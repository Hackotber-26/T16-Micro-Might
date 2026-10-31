"""Turns gate results and the measured residual into a score and one of the 4 verdicts.
Failing a gate always gives "Cannot verify" with no score; thresholds and the score formula are in config.py."""

from . import config

VERDICTS = ("Verified", "Partial", "Not fixed", "Cannot verify")


def decide(gate1, gate2, measure):
    """Returns (verdict, score or None)."""
    if not gate1["passed"] or not gate2["passed"]:
        return "Cannot verify", None
    adjusted = measure.get("residual_adjusted")
    if adjusted is None:
        return "Cannot verify", None

    score = round(min(max(1.0 - adjusted, 0.0), 1.0), 3)  # score = clip(1 - residual_adjusted, 0, 1)
    if score >= config.T_VERIFIED:
        return "Verified", score
    if score >= config.T_PARTIAL:
        return "Partial", score
    return "Not fixed", score
