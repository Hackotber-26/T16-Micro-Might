"""All tunable thresholds in one place, so the team tunes numbers here instead of inside the modules.
Change a value, rerun, and every gate / measurement / verdict picks it up."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PAIRS_DIR = DATA_DIR / "pairs"

# Images
MAX_SIDE = 1280  # long edge (px) photos are downscaled to before any CV work

# Gate 1: same place
GPS_MAX_M = 40  # only judged when both photos have GPS
HEADING_MAX_DEG = 60  # only judged when both photos have a compass heading
ORB_FEATURES = 2000
LOWE_RATIO = 0.75
RANSAC_PX = 5.0  # RANSAC reprojection error in pixels
MIN_INLIERS = 25
MIN_INLIER_RATIO = 0.25

# Gate 2: real and fresh
DUP_MAX = 6  # pHash Hamming distance at or below this = reused photo
KNOWN_HASHES = DATA_DIR / "known_hashes.json"  # cache of pHashes of every photo in data/pairs
REUSE_MAX_SHIFT_PX = 8  # near-identical hash AND corners move less than this under Gate 1's homography = same photo
SCREEN_PEAK_MIN = 4.0  # FFT moire: strongest periodic peak (log units above the radial average) to call it a screen
SCREEN_BANDING_MIN = 0.45  # fraction of empty grey levels inside the photo's range (posterised / low colour depth)

# Measure: defect segmentation (classical CV heuristics)
DEFECT_TYPE = "pothole"  # "pothole" or "garbage" (the app lets you switch)
TEXTURE_WINDOW = 21  # window (px) for local texture (std-dev of lightness)
DARK_BLOCK = 151  # adaptive threshold window: pixel must be darker than its surroundings in this window...
DARK_C = 18  # ...by at least this many lightness levels (so a slightly darker fresh patch is NOT a pothole)
ROUGH_MIN = 6.0  # pothole pixels must also be rough (local std above this); a smooth patch is not
GARBAGE_SAT_MIN = 70  # garbage: colourful pixels (HSV saturation above this)...
GARBAGE_ROUGH_MIN = 14.0  # ...or strongly textured clutter
CLOSE_PX = 15  # morphology size joining defect pixels into one blob
MIN_DEFECT_PCT = 0.3  # defect blob must cover at least this % of the photo
EDGE_WEIGHT = 0.2  # share of the score taken from edge density change (rest = residual area)

# Verdict: residual_adjusted = (1 - EDGE_WEIGHT) * residual_area + EDGE_WEIGHT * min(edge_ratio, 1)
#          score = clip(1 - residual_adjusted, 0, 1)
T_VERIFIED = 0.80
T_PARTIAL = 0.40

# Narrator
GEMMA_MODEL = "gemma4:e2b"
GEMMA_TIMEOUT_S = 20
