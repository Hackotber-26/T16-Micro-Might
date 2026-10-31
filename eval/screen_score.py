"""Prints Gate 2's screen-recapture scores for any photos, to calibrate SCREEN_PEAK_MIN / SCREEN_BANDING_MIN in nija/config.py.
Usage: python eval/screen_score.py normal_photo.jpg photo_of_monitor.jpg ..."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nija.gate2 import screen_scores  # noqa: E402
from nija.images import load_bgr  # noqa: E402

for p in sys.argv[1:]:
    print(p, screen_scores(load_bgr(p)))
