"""Gate 2 - real and fresh: pHash rejects an after photo that is the before photo or an earlier submission, and EXIF time must move forward.
The screen-recapture check is not built yet (Step 3); the result says so instead of pretending it ran."""

from pathlib import Path

import imagehash

from . import config
from .images import load_pil

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def check_fresh(before_path, after_path, before_exif, after_exif, history_dir=None):
    history_dir = Path(history_dir or config.HISTORY_DIR)
    result = {
        "passed": False,
        "reason": "",
        "dup_hash_distance": None,
        "time_ok": None,
        "screen_suspect": False,
        "history_match": None,
        "before_time": _fmt(before_exif["timestamp"]),
        "after_time": _fmt(after_exif["timestamp"]),
    }
    notes = []

    hash_after = imagehash.phash(load_pil(after_path))
    dist = int(hash_after - imagehash.phash(load_pil(before_path)))
    result["dup_hash_distance"] = dist
    if dist <= config.DUP_MAX:
        result["reason"] = f"reused photo: after is a near-copy of before (pHash distance {dist}, limit {config.DUP_MAX})"
        return result

    if history_dir.is_dir():
        after_resolved = Path(after_path).resolve()
        for old in sorted(history_dir.iterdir()):
            if old.suffix.lower() not in IMAGE_EXTS or old.resolve() == after_resolved:
                continue
            d = int(hash_after - imagehash.phash(load_pil(old)))
            if d <= config.DUP_MAX:
                result["history_match"] = old.name
                result["dup_hash_distance"] = d
                result["reason"] = f"reused photo: matches earlier submission {old.name} (pHash distance {d})"
                return result

    t_before, t_after = before_exif["timestamp"], after_exif["timestamp"]
    if t_before and t_after:
        result["time_ok"] = t_after > t_before
        if not result["time_ok"]:
            result["reason"] = f"after photo ({_fmt(t_after)}) is not later than before photo ({_fmt(t_before)})"
            return result
        notes.append(f"taken {t_after - t_before} after the before photo")
    else:
        notes.append("warning: EXIF time missing, time order not checked")

    notes.append("screen check not implemented yet (Step 3)")
    result["passed"] = True
    result["reason"] = f"not a reused photo (pHash distance {dist}); " + "; ".join(notes)
    return result


def _fmt(ts):
    return ts.isoformat(sep=" ") if ts else None
