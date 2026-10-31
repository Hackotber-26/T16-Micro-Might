"""Geometry Lab pictures: turns the intermediates verify(debug=True) already computed (keypoints, homography, masks)
into stage images, a before/after slider, residual bars and plain-language bullets built only from the real numbers."""

import base64
import html
import math

import cv2
import numpy as np

YELLOW_BGR, RED_BGR, GREEN_BGR, TEAL_BGR = (14, 194, 255), (47, 47, 211), (62, 142, 30), (92, 92, 15)


def _rgb(bgr):
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _label(img, text, org, scale=0.9, fg=(255, 255, 255), bg=(30, 38, 35)):
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)
    x, y = org
    cv2.rectangle(img, (x - 6, y - h - 8), (x + w + 6, y + base + 4), bg, -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, fg, 2, cv2.LINE_AA)


def _side_by_side(left, right, gap=12):
    h = max(left.shape[0], right.shape[0])
    canvas = np.full((h, left.shape[1] + gap + right.shape[1], 3), 255, np.uint8)
    canvas[: left.shape[0], : left.shape[1]] = left
    canvas[: right.shape[0], left.shape[1] + gap:] = right
    return canvas


def aligned_before(images):
    """Before photo warped into the after photo's frame (H maps after -> before, so use its inverse)."""
    after, H = images["after_bgr"], images.get("H")
    if H is None:
        return None, None
    h, w = after.shape[:2]
    H_inv = np.linalg.inv(H)
    warped = cv2.warpPerspective(images["before_bgr"], H_inv, (w, h))
    valid = cv2.warpPerspective(np.full(images["before_bgr"].shape[:2], 255, np.uint8), H_inv, (w, h)) > 0
    return warped, valid


# Stage 1
def keypoints_image(images):
    b, a = images["before_bgr"].copy(), images["after_bgr"].copy()
    kb, ka = images.get("kp_before", np.zeros((0, 2))), images.get("kp_after", np.zeros((0, 2)))
    for img, pts in ((b, kb), (a, ka)):
        for x, y in pts[:: max(1, len(pts) // 600)]:
            cv2.circle(img, (int(x), int(y)), 5, YELLOW_BGR, 2, cv2.LINE_AA)
    _label(b, f"Before: {len(kb)} keypoints", (16, 40))
    _label(a, f"After: {len(ka)} keypoints", (16, 40))
    return _rgb(_side_by_side(b, a)), len(kb), len(ka)


# Stage 3
def homography_image(images):
    H = images.get("H")
    if H is None:
        return None
    after = images["after_bgr"].copy()
    hb, wb = images["before_bgr"].shape[:2]
    corners = np.float32([[0, 0], [wb, 0], [wb, hb], [0, hb]]).reshape(-1, 1, 2)
    quad = cv2.perspectiveTransform(corners, np.linalg.inv(H)).astype(np.int32)
    overlay = after.copy()
    cv2.fillPoly(overlay, [quad], YELLOW_BGR)
    after = cv2.addWeighted(overlay, 0.15, after, 0.85, 0)
    cv2.polylines(after, [quad], True, YELLOW_BGR, 6, cv2.LINE_AA)
    for (x, y), name in zip(quad.reshape(-1, 2), ("TL", "TR", "BR", "BL")):
        cv2.circle(after, (int(x), int(y)), 10, RED_BGR, -1, cv2.LINE_AA)
    _label(after, "Yellow = where the before photo's frame lands in the after photo", (16, 40), 0.8)
    return _rgb(after)


def describe_homography(H, before_shape):
    """Plain numbers for the camera change: shift of the photo centre (px), rotation (deg), scale."""
    if H is None:
        return None
    H_inv = np.linalg.inv(H)
    hb, wb = before_shape[:2]
    c = cv2.perspectiveTransform(np.float32([[[wb / 2, hb / 2]]]), H_inv)[0, 0]
    dx, dy = float(c[0] - wb / 2), float(c[1] - hb / 2)
    A = H_inv[:2, :2] / H_inv[2, 2]
    rot = math.degrees(math.atan2(A[1, 0], A[0, 0]))
    scale = math.sqrt(abs(np.linalg.det(A)))
    return {"dx": round(dx), "dy": round(dy), "rotation_deg": round(rot, 1), "scale": round(scale, 3)}


def homography_words(d):
    if d is None:
        return "No geometric transform: the photos did not match as one place."
    parts = []
    if abs(d["dx"]) >= 3:
        parts.append(f"{abs(d['dx'])} px {'right' if d['dx'] > 0 else 'left'}")
    if abs(d["dy"]) >= 3:
        parts.append(f"{abs(d['dy'])} px {'down' if d['dy'] > 0 else 'up'}")
    shift = "shifted " + " and ".join(parts) if parts else "in the same position"
    rot = abs(d["rotation_deg"])
    turn = "not turned" if rot < 0.3 else f"turned {rot} degrees {'clockwise' if d['rotation_deg'] > 0 else 'anticlockwise'}"
    size = "the same size" if abs(d["scale"] - 1) < 0.02 else f"{d['scale']:.2f}x the size"
    return f"In the after photo the scene is {shift}, {turn}, at {size}."


# Stage 4
def slider_html(images, height_px=420):
    warped, _ = aligned_before(images)
    if warped is None:
        return None
    def enc(bgr):
        h, w = bgr.shape[:2]
        s = min(1.0, 900 / w)
        small = cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        return base64.b64encode(cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 82])[1]).decode()
    h, w = images["after_bgr"].shape[:2]
    return f"""
<div style="font-family:'Noto Sans Kannada','Nirmala UI',sans-serif;max-width:100%;">
  <div id="cmp" style="position:relative;width:100%;aspect-ratio:{w}/{h};max-height:{height_px}px;margin:auto;border-radius:12px;overflow:hidden;">
    <img src="data:image/jpeg;base64,{enc(images['after_bgr'])}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;">
    <img id="top" src="data:image/jpeg;base64,{enc(warped)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;clip-path:inset(0 50% 0 0);">
    <div id="bar" style="position:absolute;top:0;bottom:0;left:50%;width:4px;background:#FFC20E;box-shadow:0 0 6px #000;"></div>
    <span style="position:absolute;left:8px;top:8px;background:#1E2623;color:#fff;padding:3px 8px;border-radius:8px;font-size:14px;">BEFORE (aligned)</span>
    <span style="position:absolute;right:8px;top:8px;background:#0F5C5C;color:#fff;padding:3px 8px;border-radius:8px;font-size:14px;">AFTER</span>
  </div>
  <input id="rng" type="range" min="0" max="100" value="50" aria-label="before after slider"
         style="width:100%;height:44px;accent-color:#0F5C5C;margin-top:6px;">
</div>
<script>
  const r = document.getElementById('rng'), t = document.getElementById('top'), b = document.getElementById('bar');
  r.addEventListener('input', () => {{ t.style.clipPath = 'inset(0 ' + (100 - r.value) + '% 0 0)'; b.style.left = r.value + '%'; }});
</script>"""


# Stage 5
def heatmap_image(images):
    warped, valid = aligned_before(images)
    if warped is None:
        return None
    gb = cv2.GaussianBlur(cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
    ga = cv2.GaussianBlur(cv2.cvtColor(images["after_bgr"], cv2.COLOR_BGR2GRAY), (5, 5), 0).astype(np.float32)
    ga += np.median(gb[valid]) - np.median(ga[valid])  # same global brightness match as the measurement
    diff = np.clip(np.abs(gb - ga) / 80.0 * 255, 0, 255).astype(np.uint8)  # fixed scale: 80 grey levels = full red
    heat = cv2.applyColorMap(diff, cv2.COLORMAP_TURBO)
    out = cv2.addWeighted(heat, 0.65, images["after_bgr"], 0.35, 0)
    out[~valid] = (40, 40, 40)
    _label(out, "Dark = no change, yellow to red = big change (after alignment)", (16, 40), 0.8)
    return _rgb(out)


# Stage 6
def contours_image(images, measure):
    region = images.get("region")
    if region is None:
        return None
    out = images["after_bgr"].copy()
    def_a = images["def_a"]
    tint = out.copy()
    tint[def_a] = RED_BGR
    out = cv2.addWeighted(tint, 0.45, out, 0.55, 0)
    contours, _ = cv2.findContours(region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, GREEN_BGR, 5, cv2.LINE_AA)
    total = out.shape[0] * out.shape[1]
    b_px, a_px = measure["before_defect_px"], measure["after_defect_px"]
    _label(out, f"Green: defect before {b_px:,} px ({100 * b_px / total:.1f}% of photo)", (16, 40), 0.8, bg=(30, 90, 30))
    _label(out, f"Red: still there {a_px:,} px ({100 * a_px / total:.1f}% of photo)", (16, 84), 0.8, bg=(40, 40, 160))
    return _rgb(out)


# Stage 7
def residual_bars_html(measure):
    b, a = measure.get("before_defect_px") or 0, measure.get("after_defect_px") or 0
    if not b:
        return None
    pct_a = min(100.0, 100.0 * a / b)
    edge = measure.get("edge_density_ratio")
    seam = measure.get("seam_edge_density")
    def bar(label, value, width, colour):
        return (f"<div style='margin:8px 0'><div style='display:flex;justify-content:space-between;font-weight:600'>"
                f"<span>{html.escape(label)}</span><span>{html.escape(value)}</span></div>"
                f"<div style='background:#EFE6CF;border-radius:999px;height:18px'><div style='width:{width:.1f}%;height:18px;"
                f"border-radius:999px;background:{colour}'></div></div></div>")
    rows = [bar("Defect area before", f"{b:,} px", 100, "#1E8E3E"),
            bar("Defect area after", f"{a:,} px ({pct_a:.0f}%)", pct_a, "#D32F2F")]
    if edge is not None:
        rows.append(bar("Edge density after vs before", f"{edge:.2f}x", min(100.0, 100 * edge), "#0F5C5C"))
    if seam is not None:
        rows.append(bar("Seam edges around old border", f"{seam:.3f}", min(100.0, 400 * seam), "#F2A900"))
    return "<div class='nija-card' style='border-left-color:#FFC20E'>" + "".join(rows) + "</div>"


def plain_bullets(result, images):
    """3-5 sentences built only from measured numbers."""
    g1, g2, m = result["checks"]["gate1"], result["checks"]["gate2"], result["checks"]["measure"]
    out = []
    if g1["passed"]:
        gps = f" GPS says {g1['gps_distance_m']:.0f} m apart." if g1.get("gps_distance_m") is not None else ""
        out.append(f"Same place: {g1['inliers']} matching points agree on one camera transform ({g1['inlier_ratio']:.0%} of matches).{gps}")
        out.append(homography_words(describe_homography(images.get("H"), images["before_bgr"].shape)))
    else:
        out.append(f"Not the same place: {g1['reason']}.")
    if not g2["passed"]:
        out.append(f"Photo not accepted as real and fresh: {g2['reason']}.")
    b, a = m.get("before_defect_px") or 0, m.get("after_defect_px") or 0
    if b and m.get("residual_area_pct") is not None:
        change = 100 * (1 - a / b)
        word = "smaller" if change >= 0 else "larger"
        out.append(f"Defect area went from {b:,} px to {a:,} px ({abs(change):.0f}% {word}).")
        if m.get("edge_density_ratio") is not None:
            out.append(f"Edge density inside the defect is now {m['edge_density_ratio']:.2f}x what it was "
                       f"({'smoother surface' if m['edge_density_ratio'] < 1 else 'still rough'}).")
    elif m.get("method"):
        out.append(f"Measurement: {m['method']}.")
    return out[:5]
