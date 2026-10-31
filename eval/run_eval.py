"""Evaluates Nija on data/pairs (real) + data/pairs_fake (synthetic): confusion matrix over the 4 verdicts, and precision/recall at
catching BAD closures (anything not truly fixed), against a baseline that just asks gemma4:e2b "Was this repair completed?". Writes eval/results.md + .csv."""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nija import config, verify  # noqa: E402
from nija.reinspect import list_pairs  # noqa: E402

VERDICTS = ["Verified", "Partial", "Not fixed", "Cannot verify"]
TRUTHS = ["fixed", "partial", "not_fixed", "unverifiable"]
EXPECTED = dict(zip(TRUTHS, VERDICTS))
OUT_DIR = ROOT / "eval"
CACHE = OUT_DIR / "results_cache"
BASELINE_PROMPT = "Photo 1 was taken BEFORE a civic repair, photo 2 AFTER. Was this repair completed? Answer yes or no."
ANSWER_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "enum": ["yes", "no"]}}, "required": ["answer"]}


def load_pairs(dirs):
    items = []
    for d in dirs:
        for p in list_pairs(d):
            try:
                label = json.loads((p / "label.json").read_text())
            except (OSError, ValueError):
                print(f"skip {p}: no label.json")
                continue
            if label.get("label") not in TRUTHS:
                print(f"skip {p}: label must be one of {TRUTHS}")
                continue
            items.append((p, label))
    return items


def ask_gemma_baseline(before, after):
    """Baseline: Gemma sees both photos and answers yes/no. Returns (answer, seconds). Cached by file mtime."""
    import ollama

    CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE / "baseline.json"
    cache = json.loads(cache_file.read_text()) if cache_file.exists() else {}
    key = f"{before}|{before.stat().st_mtime}|{after}|{after.stat().st_mtime}"
    if key in cache:
        return cache[key]["answer"], cache[key]["seconds"]

    small = []
    for i, p in enumerate((before, after)):  # downsize so the vision call stays quick
        img = cv2.imread(str(p))
        s = 512 / max(img.shape[:2])
        out = CACHE / f"_baseline_{i}.jpg"
        cv2.imwrite(str(out), cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else img)
        small.append(str(out))
    t = time.perf_counter()
    r = ollama.Client(timeout=120).chat(
        model=config.GEMMA_MODEL,
        messages=[{"role": "user", "content": BASELINE_PROMPT, "images": small}],
        format=ANSWER_SCHEMA, options={"temperature": 0, "num_predict": 20}, keep_alive="30m", think=False)
    seconds = round(time.perf_counter() - t, 2)
    m = re.search(r"\b(yes|no)\b", r.message.content.lower())  # reply is {"answer": "yes"|"no"}
    answer = m.group(1) if m else "unclear"
    cache[key] = {"answer": answer, "seconds": seconds, "raw": r.message.content[:200]}
    cache_file.write_text(json.dumps(cache, indent=1))
    return answer, seconds


def precision_recall(rows, flag_key):
    # positive class = BAD closure (truth is not "fixed"); flagged = system did not say it is fixed
    tp = sum(r["bad"] and r[flag_key] for r in rows)
    fp = sum((not r["bad"]) and r[flag_key] for r in rows)
    fn = sum(r["bad"] and not r[flag_key] for r in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return precision, recall, tp, fp, fn


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", type=Path, default=config.PAIRS_DIR)
    ap.add_argument("--fakes", type=Path, default=config.DATA_DIR / "pairs_fake")
    ap.add_argument("--no-baseline", action="store_true", help="skip the Gemma yes/no baseline (faster)")
    args = ap.parse_args()

    items = load_pairs([args.pairs, args.fakes])
    if not items:
        sys.exit(f"No labelled pairs in {args.pairs} or {args.fakes}. See the data shoot checklist in README.md.")

    rows = []
    for i, (p, label) in enumerate(items, 1):
        defect_type = label.get("type") if label.get("type") in ("pothole", "garbage") else None
        t = time.perf_counter()
        r = verify(p / "before.jpg", p / "after.jpg", defect_type=defect_type, use_gemma=False)
        sec = time.perf_counter() - t
        row = {
            "pair": p.name, "source": "synthetic" if label.get("synthetic") else "real", "type": label.get("type", ""),
            "truth": label["label"], "verdict": r["verdict"], "score": r["score"],
            "correct": r["verdict"] == EXPECTED[label["label"]], "bad": label["label"] != "fixed",
            "nija_flagged": r["verdict"] != "Verified", "nija_seconds": round(sec, 2),
        }
        if not args.no_baseline:
            try:
                ans, bsec = ask_gemma_baseline(p / "before.jpg", p / "after.jpg")
            except Exception as e:
                ans, bsec = f"error: {e}"[:60], None
            row.update({"gemma_answer": ans, "gemma_flagged": ans != "yes", "gemma_seconds": bsec})
        rows.append(row)
        print(f"[{i}/{len(items)}] {p.name:24} truth={row['truth']:12} nija={row['verdict']:13}"
              + (f" gemma={row['gemma_answer']}" if "gemma_answer" in row else ""))

    write_results(rows, not args.no_baseline)


def write_results(rows, with_baseline):
    OUT_DIR.mkdir(exist_ok=True)
    with open(OUT_DIR / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n, n_real = len(rows), sum(r["source"] == "real" for r in rows)
    acc = sum(r["correct"] for r in rows) / n
    p, rc, tp, fp, fn = precision_recall(rows, "nija_flagged")
    nija_sec = sum(r["nija_seconds"] for r in rows) / n
    lines = [
        "# Nija evaluation results", "",
        f"{n} pairs: {n_real} real, {n - n_real} synthetic fakes (generated by eval/make_fakes.py). Small self-made test set, so read with care.",
        "", "## Confusion matrix (rows = truth, columns = Nija verdict)", "",
        "| truth \\ verdict | " + " | ".join(VERDICTS) + " |", "|---|" + "---|" * len(VERDICTS),
    ]
    for t in TRUTHS:
        lines.append(f"| {t} | " + " | ".join(str(sum(r['truth'] == t and r['verdict'] == v for r in rows)) for v in VERDICTS) + " |")
    lines += ["", f"Exact 4-way accuracy: **{acc:.0%}**", "",
              "## Catching bad closures (positive = anything not truly fixed)", "",
              "| system | precision | recall | TP | FP | FN | avg s/pair |", "|---|---|---|---|---|---|---|",
              f"| Nija (gates + measurement) | {p:.2f} | {rc:.2f} | {tp} | {fp} | {fn} | {nija_sec:.2f} |"]
    summary = f"Nija catches {rc:.0%} of bad closures at {p:.0%} precision ({n} pairs, {nija_sec:.1f} s/pair)"
    if with_baseline:
        bp, brc, btp, bfp, bfn = precision_recall(rows, "gemma_flagged")
        bs = [r["gemma_seconds"] for r in rows if r.get("gemma_seconds")]
        bsec = sum(bs) / len(bs) if bs else 0.0
        unclear = sum(r["gemma_answer"] not in ("yes", "no") for r in rows)
        yes_all = sum(r["gemma_answer"] == "yes" for r in rows)
        fixed_rows = [r for r in rows if r["truth"] == "fixed"]
        yes_fixed = sum(r["gemma_answer"] == "yes" for r in fixed_rows)
        nija_fixed = sum(r["verdict"] == "Verified" for r in fixed_rows)
        lines.append(f"| Baseline: gemma4:e2b yes/no on both photos | {bp:.2f} | {brc:.2f} | {btp} | {bfp} | {bfn} | {bsec:.2f} |")
        lines += ["", f"Baseline: anything other than a clear \"yes\" counts as flagged ({unclear} unclear answers). "
                      f"Gemma said \"yes, fixed\" on {yes_all}/{n} pairs overall and on {yes_fixed}/{len(fixed_rows)} truly fixed pairs "
                      f"(Nija verified {nija_fixed}/{len(fixed_rows)}). A model that always says \"no\" gets 100% recall "
                      f"but is useless for closing complaints, so read recall together with this line."]
        summary += (f" vs Gemma-only yes/no: {brc:.0%} recall at {bp:.0%} precision, but it confirmed only "
                    f"{yes_fixed}/{len(fixed_rows)} genuinely fixed repairs (Nija: {nija_fixed}/{len(fixed_rows)})")
    lines += ["", "## Fakes caught (synthetic attacks)", ""]
    for attack in ("reused", "screen", "otherplace"):
        fk = [r for r in rows if r["source"] == "synthetic" and r["pair"].endswith("_" + attack)]
        if fk:
            caught = sum(r["verdict"] == "Cannot verify" for r in fk)
            lines.append(f"- {attack}: Nija says Cannot verify on {caught}/{len(fk)}"
                         + (f"; Gemma baseline says 'yes, fixed' on {sum(r['gemma_answer'] == 'yes' for r in fk)}/{len(fk)}" if with_baseline else ""))
    lines += ["", f"**Slide line:** {summary}.", "", "Per-pair results: eval/results.csv"]
    (OUT_DIR / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[4:]))
    print(f"\nSLIDE: {summary}.")


if __name__ == "__main__":
    main()
