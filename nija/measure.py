"""Measure (Step 1 PLACEHOLDER): aligns the after photo onto the before photo and counts how much of the defect region did NOT change.
It's a grey-level change heuristic, not defect segmentation. Step 4 replaces it with a real defect mask."""

import cv2
import numpy as np

from . import config


def measure_residual(before_bgr, after_bgr, H, roi=None):
    """H maps after -> before. roi = (x, y, w, h) in before-photo pixels; default = central half of the frame.
    Returns (contract dict, debug images dict)."""
    h, w = before_bgr.shape[:2]
    aligned = cv2.warpPerspective(after_bgr, H, (w, h))
    valid = cv2.warpPerspective(np.full(after_bgr.shape[:2], 255, np.uint8), H, (w, h))
    valid = cv2.erode(valid, np.ones((15, 15), np.uint8)) > 0  # drop warped borders

    region = np.zeros((h, w), bool)
    x, y, rw, rh = roi if roi else (w // 4, h // 4, w // 2, h // 2)
    region[y:y + rh, x:x + rw] = True
    region &= valid

    gb = cv2.GaussianBlur(cv2.cvtColor(before_bgr, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
    ga = cv2.GaussianBlur(cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
    # Global lighting match: shift after brightness by the median difference (local CLAHE would hide the repair)
    ga += np.median(gb[valid]) - np.median(ga[valid])
    changed = (np.abs(gb - ga) > config.DIFF_THRESHOLD).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0

    before_px = int(region.sum())
    unchanged = region & ~changed
    after_px = int(unchanged.sum())
    result = {
        "residual_area_pct": round(100.0 * after_px / before_px, 1) if before_px else None,
        "before_defect_px": before_px,
        "after_defect_px": after_px,
        "relief_change": None,  # depth comes later (stretch), and will be relative, not metric
        "method": "placeholder: grey-level change inside region, not defect segmentation",
    }

    overlay = before_bgr.copy()
    overlay[region & changed] = (0.5 * overlay[region & changed] + [0, 127, 0]).astype(np.uint8)
    overlay[unchanged] = (0.5 * overlay[unchanged] + [0, 0, 127]).astype(np.uint8)
    cv2.rectangle(overlay, (x, y), (x + rw, y + rh), (255, 255, 0), 2)
    debug = {
        "aligned_after": cv2.cvtColor(aligned, cv2.COLOR_BGR2RGB),
        "overlay": cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB),
    }
    return result, debug
