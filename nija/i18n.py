"""UI text in English (EN) and Kannada (KN). t(key, lang) returns the text for the chosen language, falling back to English.
Kannada strings are machine drafted and must be reviewed by a Kannada speaker before real use."""

EN = {
    # Geometry Lab
    "lab_tab": "Geometry lab",
    "lab_intro": "See what changed between the two photos, step by step. Every picture below is drawn from the numbers Nija measured.",
    "lab_source": "Photo pair",
    "lab_last": "Last pair from the Verify tab",
    "lab_run": "Run the geometry lab",
    "lab_running": "Measuring the geometry...",
    "lab_done": "Geometry lab finished",
    "lab_no_last": "Verify a pair in the Verify tab first, or pick a sample pair.",
    "lab_what": "What the numbers say",
    "lab_skip_gate1": "Skipped: the photos did not match as one place, so there is no transform to show.",
    "lab_skip_measure": "Skipped: no defect measurement for this pair.",
    "lab_compact": "Geometry at a glance",
    "lab_open_full": "Open the Geometry lab tab for all 7 steps.",
    "s1_t": "1. Keypoints",
    "s1_c": "Corners and textures Nija can find again in both photos (yellow circles).",
    "s2_t": "2. Matches",
    "s2_c": "Green lines join the same point in both photos. Red lines were rejected by RANSAC.",
    "s3_t": "3. Camera change (homography)",
    "s3_c": "The yellow box shows where the before photo's frame lands in the after photo.",
    "s4_t": "4. Aligned overlay",
    "s4_c": "Drag the slider: the before photo, warped to line up, against the after photo.",
    "s5_t": "5. Difference heatmap",
    "s5_c": "How much each spot changed after alignment. Dark means no change, yellow to red means big change.",
    "s6_t": "6. Defect contours",
    "s6_c": "Green outline is the defect in the before photo. Red fill is what is still there now.",
    "s7_t": "7. Residual",
    "s7_c": "Defect area before and after, edge density change and the seam cue around the old border.",
    "sample_fixed": "Sample: fixed",
    "sample_partial": "Sample: half fixed",
    "sample_notfixed": "Sample: not fixed",
    "sample_otherplace": "Sample: different place",
}

KN = {}  # filled in Step 3

LANGS = {"EN": EN, "ಕನ್ನಡ": KN, "KN": KN}


def t(key, lang="EN", **fmt):
    text = LANGS.get(lang or "EN", EN).get(key) or EN.get(key, key)
    return text.format(**fmt) if fmt else text
