"""Turns gate results and the measured residual into a score and one of the 4 verdicts.
Failing a gate always gives "Cannot verify" with no score; thresholds come from config.py."""

from . import config

VERDICTS = ("Verified", "Partial", "Not fixed", "Cannot verify")


def decide(gate1, gate2, measure):
    """Returns (verdict, score or None)."""
    if not gate1["passed"] or not gate2["passed"]:
        return "Cannot verify", None
    residual = measure.get("residual_area_pct")
    if residual is None:
        return "Cannot verify", None

    # score = clip(1 - residual_area_pct / 100, 0, 1)
    score = round(min(max(1.0 - residual / 100.0, 0.0), 1.0), 3)
    if score >= config.T_VERIFIED:
        return "Verified", score
    if score >= config.T_PARTIAL:
        return "Partial", score
    return "Not fixed", score
