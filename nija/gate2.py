"""Gate 2 - real and fresh: pHash catches reused photos (vs the before photo and every photo in data/pairs), EXIF time must move forward,
and a screen-recapture HEURISTIC (FFT moire peaks + colour banding) flags photos of a monitor. Calibrate with `python eval/screen_score.py photo.jpg`."""

import json
from pathlib import Path

import cv2
import imagehash
import numpy as np

from . import config
from .images import load_bgr, load_pil

IMAGE_NAMES = ("before.jpg", "after.jpg")


def check_fresh(before_path, after_path, before_exif, after_exif, H=None, after_bgr=None):
    """H = Gate 1 homography (after -> before) or None. after_bgr = already-loaded after photo (optional)."""
    result = {
        "passed": False,
        "reason": "",
        "dup_hash_distance": None,
        "time_ok": None,
        "screen_suspect": False,
        "screen_peak": None,
        "screen_banding": None,
        "reused_from": None,
        "before_time": _fmt(before_exif["timestamp"]),
        "after_time": _fmt(after_exif["timestamp"]),
    }
    notes = []

    # 1. Reused photo: same picture as the before photo?
    hash_before, hash_after = imagehash.phash(load_pil(before_path)), imagehash.phash(load_pil(after_path))
    dist = int(hash_after - hash_before)
    result["dup_hash_distance"] = dist
    shift = _corner_shift(H, after_bgr.shape if after_bgr is not None else None)
    if dist <= config.DUP_MAX and (shift is None or shift <= config.REUSE_MAX_SHIFT_PX):
        how = "" if shift is None else f", camera moved only {shift:.1f} px"
        result["reused_from"] = "before photo"
        result["reason"] = f"reused photo: after is the before photo again (pHash distance {dist}{how})"
        return result
    if dist <= config.DUP_MAX:
        notes.append(f"looks very similar to before (pHash {dist}) but camera moved {shift:.0f} px, so a real retake")

    # 2. Reused photo: same picture as any other photo in data/pairs (skipping the pair under test)?
    known = load_known_hashes()
    test_pair = _pair_of(hash_before, known)
    for rel, info in known.items():
        if Path(rel).parent.name == test_pair:
            continue
        d = int(hash_after - imagehash.hex_to_hash(info["phash"]))
        if d <= config.DUP_MAX:
            result["dup_hash_distance"] = d
            result["reused_from"] = rel
            result["reason"] = f"reused photo: after matches an earlier photo {rel} (pHash distance {d})"
            return result

    # 3. Time order from EXIF
    t_before, t_after = before_exif["timestamp"], after_exif["timestamp"]
    if t_before and t_after:
        result["time_ok"] = t_after > t_before
        if not result["time_ok"]:
            result["reason"] = f"after photo ({_fmt(t_after)}) is not later than before photo ({_fmt(t_before)})"
            return result
        notes.append(f"taken {t_after - t_before} after the before photo")
    else:
        notes.append("warning: EXIF time missing, time order not checked")

    # 4. Photo of a screen? (heuristic)
    screen = screen_scores(after_bgr if after_bgr is not None else load_bgr(after_path))
    result.update(screen)
    if screen["screen_suspect"]:
        result["reason"] = (
            f"looks like a photo of a screen (moire peak {screen['screen_peak']}, banding {screen['screen_banding']}; heuristic)"
        )
        return result

    result["passed"] = True
    result["reason"] = f"not a reused photo (pHash distance {dist}); no screen pattern found; " + "; ".join(notes)
    return result


def screen_scores(bgr):
    """HEURISTIC, not a trained detector. Moire: a photographed screen shows sharp periodic peaks in the 2D FFT,
    far above the smooth falloff of a natural photo. Banding: a re-captured or posterised image uses few grey levels."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    n = min(512, *gray.shape)
    y0, x0 = (gray.shape[0] - n) // 2, (gray.shape[1] - n) // 2
    crop = gray[y0:y0 + n, x0:x0 + n]  # native resolution, so the pixel grid is not blurred away
    crop = (crop - crop.mean()) * np.outer(np.hanning(n), np.hanning(n))
    logmag = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(crop))))

    yy, xx = np.indices((n, n))
    r = np.hypot(yy - n // 2, xx - n // 2).astype(int)
    radial_mean = np.bincount(r.ravel(), logmag.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    excess = logmag - radial_mean[r]
    band = (r > 0.08 * n) & (r < 0.48 * n)  # skip DC / scene layout, and the corners
    peak = float(excess[band].max())

    g = gray.astype(np.uint8)
    lo, hi = np.percentile(g, [1, 99]).astype(int)
    hist = np.bincount(g.ravel(), minlength=256)[lo:hi + 1]
    banding = float((hist == 0).mean()) if hi > lo else 1.0

    suspect = peak >= config.SCREEN_PEAK_MIN or banding >= config.SCREEN_BANDING_MIN
    return {"screen_suspect": bool(suspect), "screen_peak": round(peak, 2), "screen_banding": round(banding, 3)}


def load_known_hashes():
    """pHash of every data/pairs/<id>/before.jpg and after.jpg, cached in data/known_hashes.json (refreshed when files change)."""
    try:
        cache = json.loads(config.KNOWN_HASHES.read_text())
    except (OSError, ValueError):
        cache = {}
    fresh, changed = {}, False
    for path in sorted(config.PAIRS_DIR.glob("*/*.jpg")):
        if path.name.lower() not in IMAGE_NAMES:
            continue
        rel = path.relative_to(config.DATA_DIR).as_posix()
        mtime = path.stat().st_mtime
        if rel in cache and cache[rel]["mtime"] == mtime:
            fresh[rel] = cache[rel]
        else:
            fresh[rel] = {"mtime": mtime, "phash": str(imagehash.phash(load_pil(path)))}
            changed = True
    if changed or fresh.keys() != cache.keys():
        config.KNOWN_HASHES.write_text(json.dumps(fresh, indent=1))
    return fresh


def _pair_of(hash_before, known):
    """Folder name of the pair whose before.jpg is this before photo, so its own after.jpg is not called 'reused'."""
    for rel, info in known.items():
        if rel.endswith("/before.jpg") and hash_before - imagehash.hex_to_hash(info["phash"]) <= config.DUP_MAX:
            return Path(rel).parent.name
    return None


def _corner_shift(H, shape):
    """Mean distance (px) the after photo's corners move under H. Near 0 = the very same framing (same photo)."""
    if H is None or shape is None:
        return None
    h, w = shape[:2]
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    return float(np.linalg.norm(cv2.perspectiveTransform(corners, H) - corners, axis=2).mean())


def _fmt(ts):
    return ts.isoformat(sep=" ") if ts else None

