"""Re-inspection queue: runs verify() on every pair in data/pairs/<id>/ and ranks them, most doubtful first.
Order comes from config.QUEUE_PRIORITY (Not fixed > Partial > Cannot verify > Verified); lower score first within a verdict."""

import json

from . import config
from .pipeline import verify


def list_pairs(pairs_dir=None):
    pairs_dir = pairs_dir or config.PAIRS_DIR
    return [d for d in sorted(pairs_dir.iterdir()) if (d / "before.jpg").is_file() and (d / "after.jpg").is_file()] \
        if pairs_dir.is_dir() else []


def build_queue(pairs_dir=None):
    """Returns a list of row dicts sorted by priority. Uses template notes (no Gemma) so it stays fast."""
    rows = []
    for d in list_pairs(pairs_dir):
        label = _read_label(d)
        defect_type = label.get("type") if label.get("type") in ("pothole", "garbage") else None
        r = verify(d / "before.jpg", d / "after.jpg", defect_type=defect_type, use_gemma=False)
        checks = r["checks"]
        failed = next((checks[g] for g in ("gate1", "gate2") if not checks[g]["passed"]), None)
        rows.append({
            "pair": d.name,
            "verdict": r["verdict"],
            "score": r["score"],
            "residual_%": checks["measure"]["residual_area_pct"],
            "why": failed["reason"] if failed else checks["measure"].get("method", ""),
            "type": label.get("type", ""),
            "label (ground truth)": label.get("label", ""),
            "ms": r["timings_ms"]["total"],
        })
    rank = {v: i for i, v in enumerate(config.QUEUE_PRIORITY)}
    rows.sort(key=lambda row: (rank[row["verdict"]], row["score"] if row["score"] is not None else 0))
    for i, row in enumerate(rows, 1):
        row["priority"] = i
    return rows


def _read_label(pair_dir):
    try:
        return json.loads((pair_dir / "label.json").read_text())
    except (OSError, ValueError):
        return {}
