"""Gate 1 - same place: checks EXIF GPS/compass when present, then matches ORB features and fits a RANSAC homography.
Passes only if enough matches agree on one geometric transform; that homography is reused to align the photos."""

import cv2
import numpy as np

from . import config
from .exif import gps_distance_m


def draw_matches(before_bgr, kp_b, after_bgr, kp_a, good, mask=None, max_lines=150):
    """Side-by-side image (before | after) with match lines; green = RANSAC inlier, red = rejected."""
    def spread(idx, n):  # evenly spaced sample so lines cover the whole image
        return idx[:: max(1, len(idx) // n)][:n]

    flags = mask.ravel().astype(bool) if mask is not None else np.zeros(len(good), bool)
    inl = [i for i in range(len(good)) if flags[i]]
    rej = [i for i in range(len(good)) if not flags[i]]
    keep = spread(inl, max_lines) + spread(rej, max_lines // 3)
    h = max(before_bgr.shape[0], after_bgr.shape[0])
    canvas = np.zeros((h, before_bgr.shape[1] + after_bgr.shape[1], 3), np.uint8)
    canvas[: before_bgr.shape[0], : before_bgr.shape[1]] = before_bgr
    canvas[: after_bgr.shape[0], before_bgr.shape[1]:] = after_bgr
    for i in keep:
        m = good[i]
        p1 = tuple(int(v) for v in kp_b[m.trainIdx].pt)
        x2, y2 = kp_a[m.queryIdx].pt
        p2 = (int(x2) + before_bgr.shape[1], int(y2))
        colour = (0, 200, 0) if flags[i] else (0, 0, 230)
        cv2.line(canvas, p1, p2, colour, 1, cv2.LINE_AA)
        cv2.circle(canvas, p1, 3, colour, -1)
        cv2.circle(canvas, p2, 3, colour, -1)
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def check_same_place(before_bgr, after_bgr, before_exif, after_exif, debug=None):
    """Returns (result dict, homography mapping after -> before, or None).
    If a dict is passed as debug, a match-line image is stored in debug["gate1_matches"]."""
    result = {
        "passed": False,
        "reason": "",
        "gps_distance_m": None,
        "heading_diff_deg": None,
        "good_matches": 0,
        "inliers": 0,
        "inlier_ratio": 0.0,
    }
    notes = []

    # EXIF location: only judged when both photos carry it
    if None not in (before_exif["lat"], after_exif["lat"]):
        dist = gps_distance_m(before_exif["lat"], before_exif["lon"], after_exif["lat"], after_exif["lon"])
        result["gps_distance_m"] = round(dist, 1)
        if dist > config.GPS_MAX_M:
            result["reason"] = f"GPS says photos are {dist:.0f} m apart (limit {config.GPS_MAX_M} m)"
            return result, None
        notes.append(f"GPS {dist:.0f} m apart")
    else:
        notes.append("GPS missing in at least one photo")

    if None not in (before_exif["heading"], after_exif["heading"]):
        diff = abs(before_exif["heading"] - after_exif["heading"]) % 360
        diff = min(diff, 360 - diff)
        result["heading_diff_deg"] = round(diff, 1)
        if diff > config.HEADING_MAX_DEG:
            result["reason"] = f"compass headings differ by {diff:.0f} deg (limit {config.HEADING_MAX_DEG})"
            return result, None

    # Visual match: ORB + ratio test + RANSAC homography
    orb = cv2.ORB_create(nfeatures=config.ORB_FEATURES)
    kp_b, des_b = orb.detectAndCompute(cv2.cvtColor(before_bgr, cv2.COLOR_BGR2GRAY), None)
    kp_a, des_a = orb.detectAndCompute(cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY), None)
    if des_b is None or des_a is None or len(kp_b) < 10 or len(kp_a) < 10:
        result["reason"] = "too few visual features to compare the photos"
        return result, None

    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(des_a, des_b, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < config.LOWE_RATIO * p[1].distance]
    result["good_matches"] = len(good)
    if debug is not None:
        debug["gate1_matches"] = draw_matches(before_bgr, kp_b, after_bgr, kp_a, good)
    if len(good) < config.MIN_INLIERS:
        result["reason"] = f"only {len(good)} feature matches (need {config.MIN_INLIERS}); likely a different place"
        return result, None

    src = np.float32([kp_a[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp_b[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, config.RANSAC_PX)
    if H is None:
        result["reason"] = "could not fit a homography between the photos"
        return result, None

    if debug is not None:
        debug["gate1_matches"] = draw_matches(before_bgr, kp_b, after_bgr, kp_a, good, mask)
    inliers = int(mask.sum())
    ratio = inliers / len(good)
    result["inliers"] = inliers
    result["inlier_ratio"] = round(ratio, 3)

    # A wildly stretched or flipped transform means the "match" is not a real view of the same spot
    det = float(np.linalg.det(H[:2, :2]))
    if not 0.2 < det < 5.0:
        result["reason"] = f"geometric transform is implausible (scale factor {det:.2f})"
        return result, None

    if inliers >= config.MIN_INLIERS and ratio >= config.MIN_INLIER_RATIO:
        result["passed"] = True
        notes.append(f"{inliers} RANSAC inliers ({ratio:.0%} of matches)")
        result["reason"] = "same place: " + "; ".join(notes)
        return result, H

    result["reason"] = (
        f"weak visual match: {inliers} inliers, {ratio:.0%} ratio "
        f"(need {config.MIN_INLIERS} and {config.MIN_INLIER_RATIO:.0%})"
    )
    return result, None
