"""The one entry point everyone codes to: verify(before_path, after_path, roi=None) returns the contract dict.
It runs Gate 1, Gate 2, measure, verdict and narrate in order, and times each stage."""

import time

from .exif import read_exif
from .gate1 import check_same_place
from .gate2 import check_fresh
from .images import load_bgr
from .measure import measure_residual
from .narrate import template_note
from .verdict import decide

SKIPPED_MEASURE = {
    "residual_area_pct": None,
    "before_defect_px": 0,
    "after_defect_px": 0,
    "relief_change": None,
    "method": "skipped: a gate failed",
}


def verify(before_path, after_path, roi=None, debug=False):
    """Returns the contract dict, or (dict, debug_images) when debug=True."""
    timings = {}
    t0 = time.perf_counter()

    def lap(name, start):
        timings[name] = round((time.perf_counter() - start) * 1000)
        return time.perf_counter()

    t = time.perf_counter()
    before_exif, after_exif = read_exif(before_path), read_exif(after_path)
    before, after = load_bgr(before_path), load_bgr(after_path)
    t = lap("load", t)

    gate1, H = check_same_place(before, after, before_exif, after_exif)
    t = lap("gate1", t)
    gate2 = check_fresh(before_path, after_path, before_exif, after_exif)
    t = lap("gate2", t)

    images = {}
    measure = dict(SKIPPED_MEASURE)
    if gate1["passed"] and gate2["passed"]:
        measure, images = measure_residual(before, after, H, roi)
    t = lap("measure", t)

    verdict, score = decide(gate1, gate2, measure)
    checks = {"gate1": gate1, "gate2": gate2, "measure": measure}
    note = template_note(verdict, score, checks)
    lap("narrate", t)
    timings["total"] = round((time.perf_counter() - t0) * 1000)

    result = {"verdict": verdict, "score": score, "checks": checks, "note": note, "timings_ms": timings}
    return (result, images) if debug else result
