"""Command-line check of the whole pipeline on one photo pair; prints the contract JSON.
Usage: python smoke_test.py [before.jpg after.jpg]  (no arguments = the synthetic sample pair in samples/)"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # works even when started from another folder

from nija import verify  # noqa: E402

if len(sys.argv) == 3:
    before, after = Path(sys.argv[1]), Path(sys.argv[2])
elif len(sys.argv) == 1:
    before, after = ROOT / "samples/synthetic_before.jpg", ROOT / "samples/synthetic_after_fixed.jpg"
    print("No photos given: using the SYNTHETIC sample pair in samples/\n")
else:
    sys.exit("usage: python smoke_test.py [before.jpg after.jpg]")

missing = [str(p) for p in (before, after) if not p.is_file()]
if missing:
    sys.exit(f"Photo not found: {', '.join(missing)}\nPut your pair in data/pairs/<id>/before.jpg and after.jpg, or run with no arguments.")

result = verify(before, after)
print(json.dumps(result, indent=2))
print(f"\n=> {result['verdict']}  score={result['score']}  in {result['timings_ms']['total']} ms")
