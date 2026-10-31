"""Gate 1 - same place: checks EXIF GPS/compass when present, then matches ORB features and fits a RANSAC homography.
Passes only if enough matches agree on one geometric transform; that homography is reused to align the photos."""

import cv2
import numpy as np

from .config import CONFIG
from .exif import gps_distance_m


def check_same_place(before_bgr, after_bgr, before_exif, after_exif):
    """Returns (result dict, homography mapping after -> before, or None)."""
    cfg = CONFIG["gate1"]
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
        if dist > cfg["max_gps_distance_m"]:
            result["reason"] = f"GPS says photos are {dist:.0f} m apart (limit {cfg['max_gps_distance_m']} m)"
            return result, None
        notes.append(f"GPS {dist:.0f} m apart")
    else:
        notes.append("GPS missing in at least one photo")

    if None not in (before_exif["heading"], after_exif["heading"]):
        diff = abs(before_exif["heading"] - after_exif["heading"]) % 360
        diff = min(diff, 360 - diff)
        result["heading_diff_deg"] = round(diff, 1)
        if diff > cfg["max_heading_diff_deg"]:
            result["reason"] = f"compass headings differ by {diff:.0f} deg (limit {cfg['max_heading_diff_deg']})"
            return result, None

    # Visual match: ORB + ratio test + RANSAC homography
    orb = cv2.ORB_create(nfeatures=cfg["orb_features"])
    kp_b, des_b = orb.detectAndCompute(cv2.cvtColor(before_bgr, cv2.COLOR_BGR2GRAY), None)
    kp_a, des_a = orb.detectAndCompute(cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY), None)
    if des_b is None or des_a is None or len(kp_b) < 10 or len(kp_a) < 10:
        result["reason"] = "too few visual features to compare the photos"
        return result, None

    pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(des_a, des_b, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < cfg["ratio_test"] * p[1].distance]
    result["good_matches"] = len(good)
    if len(good) < cfg["min_inliers"]:
        result["reason"] = f"only {len(good)} feature matches (need {cfg['min_inliers']}); likely a different place"
        return result, None

    src = np.float32([kp_a[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp_b[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, cfg["ransac_px"])
    if H is None:
        result["reason"] = "could not fit a homography between the photos"
        return result, None

    inliers = int(mask.sum())
    ratio = inliers / len(good)
    result["inliers"] = inliers
    result["inlier_ratio"] = round(ratio, 3)

    # A wildly stretched or flipped transform means the "match" is not a real view of the same spot
    det = float(np.linalg.det(H[:2, :2]))
    if not 0.2 < det < 5.0:
        result["reason"] = f"geometric transform is implausible (scale factor {det:.2f})"
        return result, None

    if inliers >= cfg["min_inliers"] and ratio >= cfg["min_inlier_ratio"]:
        result["passed"] = True
        notes.append(f"{inliers} RANSAC inliers ({ratio:.0%} of matches)")
        result["reason"] = "same place: " + "; ".join(notes)
        return result, H

    result["reason"] = (
        f"weak visual match: {inliers} inliers, {ratio:.0%} ratio "
        f"(need {cfg['min_inliers']} and {cfg['min_inlier_ratio']:.0%})"
    )
    return result, None
