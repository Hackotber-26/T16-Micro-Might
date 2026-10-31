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

# Measure (Step 1 placeholder: grey-level change, not defect segmentation)
DIFF_THRESHOLD = 30  # grey-level change (after brightness match) that counts as "changed"

# Verdict: score = clip(1 - residual_area_pct / 100, 0, 1)
T_VERIFIED = 0.80
T_PARTIAL = 0.40

# Narrator
GEMMA_MODEL = "gemma4:e2b"
GEMMA_TIMEOUT_S = 20
