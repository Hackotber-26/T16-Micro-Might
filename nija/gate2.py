"""Gate 2 - real and fresh: pHash rejects an after photo that is the before photo or an earlier submission, and EXIF time must move forward.
The screen-recapture check is not built yet; the result says so instead of pretending it ran."""

from pathlib import Path

import imagehash

from .config import CONFIG
from .images import load_pil

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def check_fresh(before_path, after_path, before_exif, after_exif, history_dir=None):
    cfg = CONFIG["gate2"]
    history_dir = Path(history_dir or cfg["history_dir"])
    result = {
        "passed": False,
        "reason": "",
        "phash_distance": None,
        "history_match": None,
        "before_time": _fmt(before_exif["timestamp"]),
        "after_time": _fmt(after_exif["timestamp"]),
        "recapture_check": "not implemented yet",
    }
    notes = []

    hash_after = imagehash.phash(load_pil(after_path))
    dist = int(hash_after - imagehash.phash(load_pil(before_path)))
    result["phash_distance"] = dist
    if dist <= cfg["duplicate_max_distance"]:
        result["reason"] = f"after photo is a near-copy of the before photo (pHash distance {dist})"
        return result

    if history_dir.is_dir():
        after_resolved = Path(after_path).resolve()
        for old in sorted(history_dir.iterdir()):
            if old.suffix.lower() not in IMAGE_EXTS or old.resolve() == after_resolved:
                continue
            d = int(hash_after - imagehash.phash(load_pil(old)))
            if d <= cfg["duplicate_max_distance"]:
                result["history_match"] = old.name
                result["reason"] = f"after photo matches an earlier submission ({old.name}, pHash distance {d})"
                return result

    t_before, t_after = before_exif["timestamp"], after_exif["timestamp"]
    if t_before and t_after:
        if t_after <= t_before:
            result["reason"] = f"after photo ({_fmt(t_after)}) is not later than before photo ({_fmt(t_before)})"
            return result
        notes.append(f"taken {t_after - t_before} after the before photo")
    else:
        notes.append("EXIF timestamp missing in at least one photo, time order not checked")

    result["passed"] = True
    result["reason"] = f"not a duplicate (pHash distance {dist}); " + "; ".join(notes)
    return result


def _fmt(ts):
    return ts.isoformat(sep=" ") if ts else None
