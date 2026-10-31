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
    if roi and config.ROI_CHANGE_MODE:
        return _measure_roi_change(before_bgr, after_bgr, H, roi, defect_type)
    if roi and config.ROI_DISTRIBUTION_MEASURE:
        return measure_box(before_bgr, after_bgr, H, roi, defect_type)
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


def defectness(bgr, box, ring):
    """How unlike the surrounding road the box looks: texture (std of L), edge density and LAB colour histograms."""
    blur = cv2.GaussianBlur(bgr, (5, 5), 0)
    lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)

    def hist(mask):
        h = cv2.calcHist([lab], [0, 1, 2], mask.astype(np.uint8) * 255, [8, 8, 8], [0, 256] * 3)
        return cv2.normalize(h, h).flatten()

    hist_d = float(cv2.compareHist(hist(box), hist(ring), cv2.HISTCMP_BHATTACHARYYA))
    sd = _local_std(lab[:, :, 0], 15)
    tex = min(abs(sd[box].mean() - sd[ring].mean()) / (sd[ring].mean() + 1e-6), 1.5)
    edges = cv2.Canny(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    edge = min(abs(edges[box].mean() - edges[ring].mean()) / (edges[ring].mean() + 0.02), 1.5)
    d = config.BOX_W_TEXTURE * tex + config.BOX_W_EDGE * edge + config.BOX_W_HIST * hist_d
    return d, {"texture": round(float(tex), 3), "edge": round(float(edge), 3), "hist": round(hist_d, 3)}


def measure_box(before_bgr, after_bgr, H, roi, defect_type):
    """Box-based look-alike measure (only with a defect box): defect-ness of the box vs the road ring around it,
    before (aligned onto the after frame) and after. residual = d_after / d_before. Same output keys as the segmentation path."""
    h, w = after_bgr.shape[:2]
    before_al = cv2.warpPerspective(before_bgr, np.linalg.inv(H), (w, h))
    valid = cv2.warpPerspective(np.full(before_bgr.shape[:2], 255, np.uint8), np.linalg.inv(H), (w, h)) > 0
    x, y, rw, rh = int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h)
    box = np.zeros((h, w), bool)
    box[y:y + rh, x:x + rw] = True
    mx, my = int(config.BOX_RING_SCALE * rw), int(config.BOX_RING_SCALE * rh)
    ring = np.zeros((h, w), bool)
    ring[max(0, y - my):y + rh + my, max(0, x - mx):x + rw + mx] = True
    box &= valid
    ring &= valid & ~box
    method = "box-based look-alike measure (box vs surrounding road)"
    base = {"residual_area_pct": None, "before_defect_px": 0, "after_defect_px": 0, "relief_change": None,
            "defect_type": defect_type, "method": method}
    if box.sum() < 100 or ring.sum() < 100:
        base["method"] = "box is outside the aligned photos, cannot measure"
        return base, {"before_aligned": _rgb(before_al)}

    d_before, parts_b = defectness(before_al, box, ring)
    d_after, parts_a = defectness(after_bgr, box, ring)
    # Illumination-normalised change inside the box (z-score each photo's box, then mean abs difference)
    gb = cv2.cvtColor(before_al, cv2.COLOR_BGR2GRAY).astype(np.float32)[box]
    ga = cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)[box]
    change = float(np.abs((gb - gb.mean()) / (gb.std() + 1e-6) - (ga - ga.mean()) / (ga.std() + 1e-6)).mean())
    if change < config.BOX_UNCHANGED_MAX:
        residual, method = 1.0, method + "; nothing changed in the box"
    elif d_before <= 1e-6:
        base["method"] = "the box does not look different from the road in the before photo (try a tighter box)"
        return base, {"before_aligned": _rgb(before_al)}
    else:
        residual = float(np.clip(d_after / d_before, 0, config.BOX_RESIDUAL_MAX))

    box_px = int(box.sum())
    result = {
        "residual_area_pct": round(100 * residual, 1),
        "before_defect_px": box_px,  # box size, not a segmented area
        "after_defect_px": int(round(box_px * min(residual, 1.0))),  # box size x look-alike ratio
        "relief_change": None,
        "residual_adjusted": round(min(residual, 1.0), 3),
        "d_before": round(float(d_before), 3),
        "d_after": round(float(d_after), 3),
        "box_change": round(change, 3),
        "parts_before": parts_b,
        "parts_after": parts_a,
        "defect_type": defect_type,
        "method": method,
    }
    return result, _box_overlays(before_al, after_bgr, box, ring, (x, y, rw, rh), d_before, d_after)


def _box_overlays(before_al, after_bgr, box, ring, rect, d_before, d_after):
    x, y, rw, rh = rect
    diff = cv2.absdiff(cv2.cvtColor(before_al, cv2.COLOR_BGR2GRAY), cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY))
    heat = cv2.applyColorMap(np.clip(diff.astype(np.float32) / 80 * 255, 0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    a = after_bgr.copy()
    a[box] = (0.55 * heat[box] + 0.45 * a[box]).astype(np.uint8)
    b = before_al.copy()
    for img in (a, b):
        tint = img.copy()
        tint[ring] = (60, 200, 60)
        img[:] = cv2.addWeighted(tint, 0.18, img, 0.82, 0)
        cv2.rectangle(img, (x, y), (x + rw, y + rh), (0, 255, 255), 4)
    for img, text in ((b, f"before: box vs road distance {d_before:.2f}"), (a, f"after: box vs road distance {d_after:.2f}")):
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.rectangle(img, (10, 12), (24 + tw, 22 + th + 8), (30, 38, 35), -1)
        cv2.putText(img, text, (16, 20 + th), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    return {"before_aligned": _rgb(before_al), "before_overlay": _rgb(b), "after_overlay": _rgb(a), "box_overlay": _rgb(a)}


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
    return {"before_aligned": _rgb(before_al), "before_overlay": _rgb(b), "after_overlay": _rgb(a),
            "region": region, "def_b": def_b, "def_a": def_a}  # masks for the Geometry Lab


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


# ---- ROI change mode: for photoreal pairs where texture segmentation fails -------------------------------------------
def _norm_l(bgr):
    """Lightness with slow lighting removed and local contrast normalised, so a sunnier after photo is not 'change'."""
    L = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[:, :, 0].astype(np.float32), (5, 5), 0)
    hp = L - cv2.GaussianBlur(L, (0, 0), 25)
    return hp / (np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 25)) + 4)


def _chroma(bgr):
    return cv2.cvtColor(cv2.GaussianBlur(bgr, (5, 5), 0), cv2.COLOR_BGR2LAB).astype(np.float32)[:, :, 1:]


def _measure_roi_change(before_bgr, after_bgr, H, roi, defect_type, grown=False):
    """Inside the user's box: (a) defect = pixels in the BEFORE photo that differ from the road just outside the box;
    (b) changed = pixels whose normalised appearance differs between aligned before and after (threshold calibrated on the
    ring around the box, so lighting/noise is not counted); repaired = changed share of the defect."""
    h, w = after_bgr.shape[:2]
    # A tight box (mostly defect) leaves no road inside it to compare against: then grow it (ROI_BOX_GROW total) and retry
    g = config.ROI_BOX_GROW / 2 if grown else 0.0
    x0, y0 = max(0.0, roi[0] - g * roi[2]), max(0.0, roi[1] - g * roi[3])
    x1, y1 = min(1.0, roi[0] + roi[2] * (1 + g)), min(1.0, roi[1] + roi[3] * (1 + g))
    roi = (x0, y0, x1 - x0, y1 - y0)
    Hi = np.linalg.inv(H)
    bal = cv2.warpPerspective(before_bgr, Hi, (w, h))
    valid = cv2.warpPerspective(np.full(before_bgr.shape[:2], 255, np.uint8), Hi, (w, h)) > 0
    valid = cv2.erode(valid.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    x, y, rw, rh = int(roi[0] * w), int(roi[1] * h), int(roi[2] * w), int(roi[3] * h)
    box = np.zeros((h, w), bool)
    box[y:y + rh, x:x + rw] = True
    ring = (cv2.dilate(box.astype(np.uint8), np.ones((int(rh * 0.5) | 1, int(rw * 0.5) | 1), np.uint8)) > 0) & ~box & valid
    empty = {"residual_area_pct": None, "before_defect_px": 0, "after_defect_px": 0, "relief_change": None,
             "defect_type": defect_type, "method": "ROI change mode: no defect found inside the box"}
    if not ring.any():
        return empty, {"before_aligned": _rgb(bal)}

    # (a) defect extent in the before photo: colour distance to the road ring (robust threshold)
    lab = cv2.cvtColor(cv2.GaussianBlur(bal, (7, 7), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    ref = np.median(lab[ring], axis=0)
    dist = np.linalg.norm(lab - ref, axis=2)
    mad = np.median(np.abs(dist[ring] - np.median(dist[ring])))
    thr_d = max(np.median(dist[ring]) + 4 * 1.48 * mad, config.ROI_DEFECT_MIN_DIST)
    defect = ((dist > thr_d) & box).astype(np.uint8)
    defect = cv2.morphologyEx(defect, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    defect = cv2.morphologyEx(defect, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8)) > 0
    method = "ROI change mode (changed share of the defect inside the box)"
    share = defect.sum() / max((box & valid).sum(), 1)
    if not grown and (share > config.ROI_TIGHT_SHARE or share < config.ROI_DEFECT_MIN_SHARE):
        return _measure_roi_change(before_bgr, after_bgr, H, roi, defect_type, grown=True)
    if grown:
        method += "; box was mostly defect, grown before measuring"
    if defect.sum() < config.ROI_DEFECT_MIN_SHARE * box.sum():
        defect, method = box & valid, "ROI change mode (defect not separable from the road, whole box used)"
        if defect.sum() == 0:
            return empty, {"before_aligned": _rgb(bal)}

    # (b) what changed between before and after
    d = (cv2.GaussianBlur(np.abs(_norm_l(bal) - _norm_l(after_bgr)), (0, 0), 3)
         + 0.08 * cv2.GaussianBlur(np.linalg.norm(_chroma(bal) - _chroma(after_bgr), axis=2), (0, 0), 3))
    rd = d[ring]
    # robust (median + MAD) so a repair that spills past the box into the ring does not inflate the threshold
    thr_c = max(np.median(rd) + config.ROI_CHANGE_K * 1.48 * np.median(np.abs(rd - np.median(rd))), config.ROI_CHANGE_MIN)
    changed = ((d > thr_c) & box).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    changed = cv2.morphologyEx(changed, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)) > 0

    # direction check: a repair makes the defect look MORE like the surrounding road (colour and roughness), not less
    lab_a = cv2.cvtColor(cv2.GaussianBlur(after_bgr, (7, 7), 0), cv2.COLOR_BGR2LAB).astype(np.float32)
    ref_a = np.median(lab_a[ring], axis=0)
    dist_b = np.linalg.norm(lab - ref, axis=2)[defect].mean()
    dist_a = np.linalg.norm(lab_a - ref_a, axis=2)[defect].mean()
    rough_b = _local_std(cv2.cvtColor(bal, cv2.COLOR_BGR2GRAY), 15)
    rough_a = _local_std(cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY), 15)
    rr_b, rr_a = rough_b[ring].mean() + 1e-3, rough_a[ring].mean() + 1e-3
    gap_b = abs(rough_b[defect].mean() - rr_b) / rr_b
    gap_a = abs(rough_a[defect].mean() - rr_a) / rr_a
    closer = (dist_a < config.ROI_DIRECTION_RATIO * dist_b) or (gap_a < config.ROI_DIRECTION_RATIO * gap_b)
    repaired = float((changed & defect).sum() / defect.sum()) if closer else 0.0
    eb = cv2.Canny(cv2.cvtColor(bal, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    ea = cv2.Canny(cv2.cvtColor(after_bgr, cv2.COLOR_BGR2GRAY), 60, 160) > 0
    ring_b = (cv2.dilate(defect.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0) & ~(
        cv2.erode(defect.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0)
    result = {
        "edge_density_ratio": round(float(ea[defect].mean() / eb[defect].mean()) if eb[defect].mean() > 0 else 1.0, 3),
        "seam_edge_density": round(float(ea[ring_b & valid].mean()) if (ring_b & valid).any() else 0.0, 3),
        "residual_area_pct": round(100 * (1 - repaired), 1),
        "before_defect_px": int(defect.sum()),
        "after_defect_px": int((defect & ~changed).sum()),
        "relief_change": None,
        "repaired_share": round(repaired, 3),
        "residual_adjusted": round(min(max(1 - repaired, 0.0), 1.0), 3),
        "defect_area_pct": round(100 * defect.sum() / valid.sum(), 2),
        "defect_type": defect_type,
        "method": method,
        "mode": "roi_change",
        "looks_like_road_after": bool(closer),
    }
    b_ov, a_ov = bal.copy(), after_bgr.copy()
    b_ov[defect] = (0.5 * b_ov[defect] + [0, 0, 127]).astype(np.uint8)
    unfixed = defect & ~changed
    a_ov[unfixed] = (0.5 * a_ov[unfixed] + [0, 0, 127]).astype(np.uint8)
    a_ov[changed & defect] = (0.5 * a_ov[changed & defect] + [0, 127, 0]).astype(np.uint8)
    contours, _ = cv2.findContours(defect.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for img in (b_ov, a_ov):
        cv2.drawContours(img, contours, -1, (255, 255, 255), 2)  # white = defect found
        cv2.rectangle(img, (x, y), (x + rw, y + rh), (0, 255, 255), 4)  # yellow = the box
    return result, {"before_aligned": _rgb(bal), "before_overlay": _rgb(b_ov), "after_overlay": _rgb(a_ov),
                    "region": defect, "def_b": defect, "def_a": unfixed}
