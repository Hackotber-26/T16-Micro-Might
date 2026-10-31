"""Writes the officer note and citizen message from the measured numbers (it never decides the verdict).
Step 1 uses a fixed template only; Step 5 adds Gemma 4 (gemma4:e2b via Ollama) and keeps this as the fallback."""


def template_note(verdict, score, checks):
    g1, g2, m = checks["gate1"], checks["gate2"], checks["measure"]
    if verdict == "Cannot verify":
        failed = g1 if not g1["passed"] else g2
        why = failed["reason"] if not failed["passed"] else m["method"]
        officer = f"Cannot verify this closure: {why}. Send for physical re-inspection."
        citizen = "We could not confirm this repair from the photos, so it has been sent for a re-check."
    else:
        officer = (
            f"Verdict {verdict} (score {score:.2f}): {m['residual_area_pct']}% of the original {m['defect_type']} area "
            f"is still detected after alignment ({g1['inliers']} matching points, edge density ratio {m['edge_density_ratio']})."
        )
        citizen = {
            "Verified": "The photos show the repair was done. Thank you for reporting it.",
            "Partial": "The photos show the repair is only partly done. It has been flagged for follow-up.",
            "Not fixed": "The photos show the problem is still there. It has been sent back for repair.",
        }[verdict]
    return {"officer": officer, "citizen": citizen, "source": "template"}
