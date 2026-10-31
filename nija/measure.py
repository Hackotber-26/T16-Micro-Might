"""Measure: warps the before photo into the after photo's frame, finds the defect (largest dark+rough blob for potholes,
colour/texture clutter for garbage, or a manual ROI box), then counts how much of it is still there in the after photo."""

import cv2
import numpy as np

from . import config


def segment(bgr, defect_type):
    """Per-pixel defect mask. Pothole = darker than its surroundings AND rough (broken surface).
    Garbage = colourful OR strongly textured clutter. Same rule is used on before and after."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    L = cv2.GaussianBlur(lab[:, :, 0], (7, 7), 0)
    rough = _local_std(L, config.TEXTURE_WINDOW)
    if defect_type == "garbage":
        sat = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[:, :, 1]
        mask = (sat > config.GARBAGE_SAT_MIN) | (rough > config.GARBAGE_ROUGH_MIN)
    else:
        dark = cv2.adaptiveThreshold(L, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
                                     config.DARK_BLOCK, config.DARK_C) > 0
        mask = dark & (rough > config.ROUGH_MIN)
    mask = mask.astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((config.CLOSE_PX, config.CLOSE_PX), np.uint8))
    return mask > 0


def measure_residual(before_bgr, after_bgr, H, roi=None, defect_type=None):
    """H maps after -> before. roi = (x, y, w, h) as FRACTIONS 0..1 of the after photo, or None for auto-detect.
    Returns (contract dict, debug images dict)."""
    defect_type = defect_type or config.DEFECT_TYPE
    h, w = after_bgr.shape[:2]
    H_inv = np.linalg.inv(H)
    before_al = cv2.warpPerspective(before_bgr, H_inv, (w, h))
    valid = cv2.warpPerspective(np.full(before_bgr.shape[:2], 255, np.uint8), H_inv, (w, h))
    valid = cv2.erode(valid, np.ones((15, 15), np.uint8)) > 0

    seg_before = segment(before_al, defect_type) & valid
    seg_after = segment(after_bgr, defect_type) & valid

    # Defect region: largest blob in the before photo (inside the ROI box if one is given)
    box = np.ones((h, w), bool)
    if roi:
        x, y, rw, rh = (int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h))
        box = np.zeros((h, w), bool)
        box[y:y + rh, x:x + rw] = True
    region, method = _largest_blob(seg_before & box), "auto: largest blob"
    if roi:
        method = "manual ROI box"
        if region is None:
            region, method = box & valid, "manual ROI box (no blob found, whole box used)"
    empty = {"residual_area_pct": None, "before_defect_px": 0, "after_defect_px": 0, "relief_change": None,
             "defect_type": defect_type, "method": method}
    if region is None or region.sum() < config.MIN_DEFECT_PCT / 100 * valid.sum():
        empty["method"] = ("no defect found inside the manual box in the before photo" if roi
                           else "no defect found in the before photo (try the manual ROI box)")
        return empty, {"before_aligned": _rgb(before_al)}

    region_d = cv2.dilate(region.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    surround = (cv2.dilate(region.astype(np.uint8), np.ones((61, 61), np.uint8)) > 0) & ~region_d & valid
    if defect_type == "garbage":
        def_b, def_a = seg_before & region_d, seg_after & region_d
    else:  # pothole pixels inside the region, judged against the road just outside it (same rule both photos)
        def_b = _darker_than_surroundings(before_al, region_d, surround)
        def_a = _darker_than_surroundings(after_bgr, region_d, surround)
    before_px = int(def_b.sum())
    after_px = int(def_a.sum())
    residual = after_px / before_px if before_px else 1.0

    # Edge/texture density inside the region (a smooth patch has few edges; rubble/garbage has many)
    edges_b = cv2.Canny(cv2.cvtColor(before_al, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    edges_a = cv2.Canny(cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    dens_b = edges_b[region_d].mean()
    dens_a = edges_a[region_d].mean()
    edge_ratio = float(dens_a / dens_b) if dens_b > 0 else 1.0

    # Seam/crack cue: edges on a ring around the old defect border in the after photo (a patch leaves a seam)
    ring = (cv2.dilate(region.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0) & ~(
        cv2.erode(region.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0)
    seam = float(edges_a[ring & valid].mean()) if (ring & valid).any() else 0.0

    # score basis: residual_adjusted = (1 - EDGE_WEIGHT) * residual + EDGE_WEIGHT * min(edge_ratio, 1)
    adjusted = (1 - config.EDGE_WEIGHT) * residual + config.EDGE_WEIGHT * min(edge_ratio, 1.0)
    result = {
        "residual_area_pct": round(100 * residual, 1),
        "before_defect_px": before_px,
        "after_defect_px": after_px,
        "relief_change": None,  # depth comes later (stretch), and will be relative, not metric
        "edge_density_ratio": round(edge_ratio, 3),
        "seam_edge_density": round(seam, 3),
        "residual_adjusted": round(min(max(adjusted, 0.0), 1.0), 3),
        "defect_area_pct": round(100 * region.sum() / valid.sum(), 2),
        "defect_type": defect_type,
        "method": method,
    }
    return result, _overlays(before_al, after_bgr, region, def_b, def_a, roi)


def _darker_than_surroundings(bgr, region, surround):
    """Inside region: darker than the surrounding road's median by DARK_C and rough, or very dark (2 x DARK_C, e.g. water)."""
    L = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[:, :, 0], (7, 7), 0).astype(np.float32)
    ref = np.median(L[surround]) if surround.any() else np.median(L)
    drop = ref - L
    rough = _local_std(L, config.TEXTURE_WINDOW) > config.ROUGH_MIN
    mask = ((drop > config.DARK_C) & rough) | (drop > 2 * config.DARK_C)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
    return mask & region


def _overlays(before_al, after_bgr, region, def_b, def_a, roi):
    contours, _ = cv2.findContours(region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    b, a = before_al.copy(), after_bgr.copy()
    b[def_b] = (0.5 * b[def_b] + [0, 0, 127]).astype(np.uint8)
    a[def_a] = (0.5 * a[def_a] + [0, 0, 127]).astype(np.uint8)
    for img in (b, a):
        cv2.drawContours(img, contours, -1, (0, 255, 255), 3)
        if roi:
            hh, ww = img.shape[:2]
            cv2.rectangle(img, (int(roi[0] * ww), int(roi[1] * hh)),
                          (int((roi[0] + roi[2]) * ww), int((roi[1] + roi[3]) * hh)), (255, 255, 0), 2)
    return {"before_aligned": _rgb(before_al), "before_overlay": _rgb(b), "after_overlay": _rgb(a)}


def _largest_blob(mask):
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    filled = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(filled, [max(contours, key=cv2.contourArea)], -1, 1, -1)
    return filled > 0


def _local_std(gray, k):
    g = gray.astype(np.float32)
    mean = cv2.blur(g, (k, k))
    return np.sqrt(np.maximum(cv2.blur(g * g, (k, k)) - mean * mean, 0))


def _rgb(bgr):
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
