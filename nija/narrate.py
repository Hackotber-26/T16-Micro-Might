"""Writes the officer note and citizen message from the measured numbers with Gemma 4 (gemma4:e2b via Ollama, text only).
Gemma never decides the verdict; if it is slow, down, or writes a number that is not in the input, a fixed template is used instead."""

import json
import re

from . import config

SYSTEM_PROMPT = (
    "You write civic repair review notes. Use ONLY the numbers given. Do not change or question the verdict. "
    "Return JSON {officer, citizen}. Officer: 2 sentences, factual. Citizen: 2 simple sentences. "
    "The officer note states the verdict, the key measurement and the recommended action. "
    "The citizen message is written TO the resident who reported the problem: what the photos showed and what happens "
    "next, friendly plain English, no technical terms, no numbers."
)
ACTIONS = {
    "Verified": "close the complaint",
    "Partial": "send back to the contractor to finish the repair",
    "Not fixed": "reopen the complaint and send back for repair",
    "Cannot verify": "send an inspector for a physical re-check",
}
NUMBER = re.compile(r"\d+(?:\.\d+)?")


def narrate(verdict, score, checks, use_gemma=True):
    """Returns {"officer", "citizen", "source": "gemma" | "template"}."""
    if not use_gemma:
        return template_note(verdict, score, checks)
    facts = build_facts(verdict, score, checks)
    try:
        import ollama

        client = ollama.Client(timeout=config.GEMMA_TIMEOUT_S)
        r = client.chat(
            model=config.GEMMA_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(facts)}],
            format="json",
            options={"temperature": 0, "num_predict": config.GEMMA_MAX_TOKENS},
            keep_alive="30m",
            think=False,
        )
        data = json.loads(r.message.content)
        officer, citizen = str(data.get("officer", "")).strip(), str(data.get("citizen", "")).strip()
        if officer and citizen and numbers_ok(officer + " " + citizen, facts):
            return {"officer": officer, "citizen": citizen, "source": "gemma"}
    except Exception:  # Ollama down, timeout, bad JSON -> template
        pass
    return template_note(verdict, score, checks)


def warm_up():
    """Loads the model into memory so the first real note is fast (about 20 s cold, about 3 s warm)."""
    try:
        import ollama

        ollama.Client(timeout=120).chat(model=config.GEMMA_MODEL, messages=[{"role": "user", "content": "ok"}],
                                        options={"num_predict": 1}, keep_alive="30m", think=False)
        return True
    except Exception:
        return False


def build_facts(verdict, score, checks):
    """Plain-language facts for Gemma: only measured values plus the fixed action for this verdict."""
    g1, g2, m = checks["gate1"], checks["gate2"], checks["measure"]
    facts = {
        "verdict": verdict,
        "recommended_action": ACTIONS[verdict],
        "same_place_check": ("passed" if g1["passed"] else "failed") + f": {g1['reason']}",
        "real_fresh_photo_check": ("passed" if g2["passed"] else "failed") + f": {g2['reason']}",
    }
    if score is not None:
        facts["fix_score_0_to_1"] = score
        facts["defect_type"] = m.get("defect_type")
        facts["defect_area_still_present_pct"] = m.get("residual_area_pct")
    elif m.get("method", "").startswith("no defect"):
        facts["measurement"] = m["method"]
    return facts


def numbers_ok(text, facts):
    """Every number Gemma writes must come from the input (allowing rounding, and 0.45 written as 45%)."""
    allowed = set()
    for n in NUMBER.findall(json.dumps(facts)):
        v = float(n)
        for x in (v, v * 100):
            allowed.update({f"{x:g}", f"{round(x)}", f"{x:.1f}", f"{x:.2f}"})
    return all(f"{float(n):g}" in allowed or n in allowed for n in NUMBER.findall(text))


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
