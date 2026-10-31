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
REUSE_MAX_PIXEL_DIFF = 4.0  # ...or, after alignment, mean grey difference below this = resized/re-saved copy of the same photo
REUSE_FRAMING_MAX_DIFF = 8.0  # same framing only counts as reuse if aligned pixels also differ by less than this
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

# Box-based look-alike measure: used ONLY when a defect box (roi) is given. roi=None keeps the segmentation above.
ROI_CHANGE_MODE = True  # with a manual box: judge by changed share of the defect (robust on photoreal pairs); False = old path
ROI_DEFECT_MIN_DIST = 10.0  # min Lab distance from the road ring to count a pixel as defect
ROI_DEFECT_MIN_SHARE = 0.03  # defect must cover at least this share of the box
ROI_CHANGE_K = 4.0  # change threshold = ring median + K x robust spread
ROI_CHANGE_MIN = 0.35
ROI_DIRECTION_RATIO = 0.8  # after must be closer to the road than before by this factor (colour or roughness)
ROI_T_VERIFIED = 0.45  # repaired share of the defect needed for Verified (calibrated on 5 AI-generated pairs only)
ROI_T_PARTIAL = 0.30  # ...and for Partial
ROI_BOX_GROW = 0.20  # if the box is mostly defect (too tight), grow it by this share (half each side) and measure again
ROI_TIGHT_SHARE = 0.60  # box counts as too tight when the defect fills more than this share of it
ROI_DISTRIBUTION_MEASURE = True
BOX_RING_SCALE = 0.21  # ring around the box grows each side by this x box size (ring area about equal to box area)
BOX_W_TEXTURE = 0.8  # defect-ness = weighted sum of: local texture (std of L) difference box vs ring...
BOX_W_EDGE = 0.1  # ...edge density difference...
BOX_W_HIST = 0.1  # ...and Bhattacharyya distance of 8x8x8 LAB histograms (low: fresh black asphalt differs in colour too)
BOX_UNCHANGED_MAX = 0.12  # mean abs diff of illumination-normalised box content below this = "nothing changed in the box"
BOX_RESIDUAL_MAX = 1.2  # residual = clip(d_after / d_before, 0, this)

# Verdict: residual_adjusted = (1 - EDGE_WEIGHT) * residual_area + EDGE_WEIGHT * min(edge_ratio, 1)
#          score = clip(1 - residual_adjusted, 0, 1)
T_VERIFIED = 0.80
T_PARTIAL = 0.40

# Narrator
GEMMA_MODEL = "gemma4:e2b"
GEMMA_TIMEOUT_S = 20
GEMMA_MAX_TOKENS = 160  # caps note length so verify() stays under 10 s

# Re-inspection queue order (most urgent first)
QUEUE_PRIORITY = ["Not fixed", "Partial", "Cannot verify", "Verified"]
