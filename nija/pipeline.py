"""The one entry point everyone codes to: verify(before_path, after_path, roi=None, defect_type=None) returns the contract dict.
It runs Gate 1, Gate 2, measure, verdict and narrate in order, and times each stage."""

import time

from .exif import read_exif
from .gate1 import check_same_place
from .gate2 import check_fresh
from .images import load_bgr
from .measure import measure_residual
from .narrate import narrate
from .verdict import decide

SKIPPED_MEASURE = {
    "residual_area_pct": None,
    "before_defect_px": 0,
    "after_defect_px": 0,
    "relief_change": None,
    "method": "skipped: a gate failed",
}


def verify(before_path, after_path, roi=None, defect_type=None, use_gemma=True, debug=False):
    """roi = (x, y, w, h) as fractions 0..1 of the after photo, or None to auto-detect the defect.
    defect_type = "pothole" | "garbage" (default from config). use_gemma=False skips Gemma (template note). Returns the contract dict, or (dict, debug_images) when debug=True."""
    timings = {}
    t0 = time.perf_counter()

    def lap(name, start):
        timings[name] = round((time.perf_counter() - start) * 1000)
        return time.perf_counter()

    t = time.perf_counter()
    before_exif, after_exif = read_exif(before_path), read_exif(after_path)
    before, after = load_bgr(before_path), load_bgr(after_path)
    t = lap("load", t)

    images = {}
    gate1, H = check_same_place(before, after, before_exif, after_exif, debug=images if debug else None)
    t = lap("gate1", t)
    gate2 = check_fresh(before_path, after_path, before_exif, after_exif, H=H, after_bgr=after)
    t = lap("gate2", t)

    measure = dict(SKIPPED_MEASURE)
    if gate1["passed"] and gate2["passed"]:
        measure, measure_images = measure_residual(before, after, H, roi, defect_type)
        images.update(measure_images)
    t = lap("measure", t)

    verdict, score = decide(gate1, gate2, measure)
    checks = {"gate1": gate1, "gate2": gate2, "measure": measure}
    note = narrate(verdict, score, checks, use_gemma)
    lap("narrate", t)
    timings["total"] = round((time.perf_counter() - t0) * 1000)

    result = {"verdict": verdict, "score": score, "checks": checks, "note": note, "timings_ms": timings}
    return (result, images) if debug else result
