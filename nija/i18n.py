"""UI text in English (EN) and Kannada (KN): t(key, lang) returns the text for the chosen language, falling back to English.
Also translates verdicts, gate reasons and the template notes. Kannada is machine drafted: have a Kannada speaker review it before real use."""

import re

EN = {
    # Shell
    "app_title": "Nija - Proof of Fix",
    "brand": "**Nija** · Proof of Fix",
    "hero_promise": "Was the pothole really fixed? Nija compares the complaint photo with the closure photo and flags fake or half-done repairs.",
    "step1": "1 Same place", "step2": "2 Real, fresh photo", "step3": "3 Measure what is left", "step4": "4 Verdict",
    "step5": "5 Note by Gemma 4",
    "tagline": "Gates and measurements decide the verdict. Gemma 4 only writes the notes. Runs fully offline on this laptop.",
    "footer": "Kannada text is machine drafted, have a Kannada speaker review before real use.",
    # Sidebar
    "settings": "Settings", "defect_type": "Defect type", "pothole": "pothole", "garbage": "garbage",
    "use_gemma": "Write notes with Gemma 4 (local)", "use_roi": "Manual defect box (overrides auto-detect)",
    "roi_caption": "Box position in % of the AFTER photo", "roi_x": "x (left)", "roi_y": "y (top)", "roi_w": "width",
    "roi_h": "height",
    # Tabs
    "tab_verify": "Verify", "tab_fool": "Try to fool Nija", "tab_queue": "Re-inspection queue",
    # Verify
    "up_before": "Before photo (complaint)", "up_after": "After photo (claimed fix)", "btn_verify": "Verify",
    "spinner": "Checking place, freshness and repair, then writing the note...",
    "err_process": "Could not process these photos ({err}). Try another pair of JPG or PNG photos.",
    "m_score": "Fix score", "m_residual": "Residual area", "m_time": "Time", "na": "n/a",
    "note": "Note", "officer": "Officer", "citizen": "Citizen",
    "src_gemma": "Gemma 4 (gemma4:e2b, local) from the measured numbers",
    "src_template": "fixed template (Gemma off, unavailable, too slow, or used a number not in the measurements)",
    "src_kn_template": "Kannada template built from the measured result",
    "src_kn_gemma": "Gemma 4 translation into Kannada, every number checked",
    "written_by": "Written by: {src}. The verdict is never decided by Gemma.",
    "officer_en": "Original English officer note",
    "btn_translate": "Translate the citizen message with Gemma",
    "translate_fail": "Gemma's translation failed or changed a number, so the Kannada template is shown.",
    "ov_before": "Before, warped into the after frame: yellow = defect region, red = defect pixels",
    "ov_after": "After: red = defect pixels still detected",
    "gate1": "Gate 1 - same place", "gate2": "Gate 2 - real and fresh photo", "measure": "Measure - residual",
    "debug_title": "Gate 1 debug - feature matches",
    "debug_caption": "Before (left) | After (right). Green = RANSAC inlier, red = rejected. {inl} inliers / {good} matches",
    "debug_none": "No match image: too few features, or the GPS or compass check failed first.",
    "raw": "Raw result (contract JSON)",
    "honesty": "Honesty note: the defect is found with classical computer vision rules (darker and rough for potholes, colour "
               "and texture clutter for garbage), not a trained model. Use the manual box if auto-detect picks the wrong area. "
               "Depth is not measured.",
    # Fool tab
    "fool_intro": "Judges: try to get a fake repair past Nija. The **before** photo is the synthetic sample pothole below. "
                  "Pick an attack, or upload your own pair at the bottom.",
    "fool_before_cap": "Before (complaint)",
    "atk_reused": "Old photo reused", "atk_reused_d": "The BEFORE photo itself, shrunk and re-saved, submitted as the 'after'.",
    "atk_screen": "Photo of a screen", "atk_screen_d": "The real after photo re-photographed off a monitor (simulated moire).",
    "atk_place": "Different place", "atk_place_d": "A clean-road photo taken somewhere else.",
    "attack": "Attack: {name}",
    "caught": "Caught by **{gate}**: {reason}", "caught_measure": "Caught: {reason}",
    "not_caught": "Not caught by the gates. Verdict: {verdict}. Nija's checks are heuristics and can be fooled.",
    "free_upload": "**Free upload:** your own before photo plus any after photo (an old photo, a photo of your screen, another street).",
    "fb_before": "Before", "fb_after": "After (your attack)", "btn_try": "Try it",
    # Queue
    "queue_intro": "Every pair in `data/pairs/<id>/` (before.jpg, after.jpg, label.json), ranked {order}, lowest score first. "
                   "Notes use the template here for speed.",
    "queue_empty": "No pairs yet. Add folders like data/pairs/p01/ with before.jpg, after.jpg and label.json.",
    "btn_refresh": "Refresh queue", "queue_spinner": "Verifying {n} pairs...", "err_queue": "Could not build the queue ({err}).",
    "col_priority": "priority", "col_pair": "pair", "col_verdict": "verdict", "col_score": "score", "col_residual": "residual %",
    "col_why": "why", "col_type": "type", "col_label": "label (ground truth)", "col_ms": "ms",
    # Verdicts
    "v_Verified": "Verified", "v_Partial": "Partial", "v_Not fixed": "Not fixed", "v_Cannot verify": "Cannot verify",
    # Geometry Lab
    "lab_tab": "Geometry lab",
    "lab_intro": "See what changed between the two photos, step by step. Every picture below is drawn from the numbers Nija measured.",
    "lab_source": "Photo pair", "lab_last": "Last pair from the Verify tab", "lab_run": "Run the geometry lab",
    "lab_running": "Measuring the geometry...", "lab_done": "Geometry lab finished",
    "lab_what": "What the numbers say",
    "lab_skip_gate1": "Skipped: the photos did not match as one place, so there is no transform to show.",
    "lab_skip_measure": "Skipped: no defect measurement for this pair.",
    "lab_compact": "Geometry at a glance", "lab_open_full": "Open the Geometry lab tab for all 7 steps.",
    "lab_img_note": "Labels inside the pictures are in English.",
    "s1_t": "1. Keypoints", "s1_c": "Corners and textures Nija can find again in both photos (yellow circles).",
    "s2_t": "2. Matches", "s2_c": "Green lines join the same point in both photos. Red lines were rejected by RANSAC.",
    "s3_t": "3. Camera change (homography)", "s3_c": "The yellow box shows where the before photo's frame lands in the after photo.",
    "s4_t": "4. Aligned overlay", "s4_c": "Drag the slider: the before photo, warped to line up, against the after photo.",
    "s5_t": "5. Difference heatmap",
    "s5_c": "How much each spot changed after alignment. Dark means no change, yellow to red means big change.",
    "s6_t": "6. Defect contours", "s6_c": "Green outline is the defect in the before photo. Red fill is what is still there now.",
    "s7_t": "7. Residual", "s7_c": "Defect area before and after, edge density change and the seam cue around the old border.",
    "sample_fixed": "Sample: fixed", "sample_partial": "Sample: half fixed", "sample_notfixed": "Sample: not fixed",
    "sample_otherplace": "Sample: different place",
    "match_caption": "{inl} inliers / {good} matches",
    # Residual bars
    "bar_before": "Defect area before", "bar_after": "Defect area after", "bar_edge": "Edge density after vs before",
    "bar_seam": "Seam edges around old border",
    # Bullets
    "b_same": "Same place: {inl} matching points agree on one camera transform ({ratio}% of matches).{gps}",
    "b_gps": " GPS says {m} m apart.",
    "b_notsame": "Not the same place: {reason}.", "b_gate2": "Photo not accepted as real and fresh: {reason}.",
    "b_area": "Defect area went from {b} px to {a} px ({pct}% {word}).", "w_smaller": "smaller", "w_larger": "larger",
    "b_edge": "Edge density inside the defect is now {r}x what it was ({word}).",
    "w_smoother": "smoother surface", "w_rough": "still rough",
    "b_measure": "Measurement: {m}.",
    # Camera change words
    "hw_none": "No geometric transform: the photos did not match as one place.",
    "hw_right": "{n} px right", "hw_left": "{n} px left", "hw_down": "{n} px down", "hw_up": "{n} px up", "hw_and": " and ",
    "hw_shift": "shifted {parts}", "hw_same_pos": "in the same position",
    "hw_noturn": "not turned", "hw_turn": "turned {deg} degrees {dir}", "hw_cw": "clockwise", "hw_acw": "anticlockwise",
    "hw_same_size": "the same size", "hw_size": "{s}x the size",
    "hw_sentence": "In the after photo the scene is {shift}, {turn}, at {size}.",
}

KN = {
    # Shell
    "app_title": "ನಿಜ - ದುರಸ್ತಿಯ ಪುರಾವೆ",
    "brand": "**ನಿಜ** · ದುರಸ್ತಿಯ ಪುರಾವೆ",
    "hero_promise": "ರಸ್ತೆ ಗುಂಡಿ ನಿಜವಾಗಿಯೂ ಮುಚ್ಚಲಾಗಿದೆಯೇ? ದೂರಿನ ಫೋಟೋ ಮತ್ತು ದುರಸ್ತಿ ನಂತರದ ಫೋಟೋವನ್ನು ನಿಜ ಹೋಲಿಸಿ, "
                    "ನಕಲಿ ಅಥವಾ ಅರ್ಧ ಮಾಡಿದ ದುರಸ್ತಿಯನ್ನು ಗುರುತಿಸುತ್ತದೆ.",
    "step1": "1 ಒಂದೇ ಸ್ಥಳ", "step2": "2 ನಿಜವಾದ ಹೊಸ ಫೋಟೋ", "step3": "3 ಉಳಿದ ಸಮಸ್ಯೆಯ ಅಳತೆ", "step4": "4 ತೀರ್ಮಾನ",
    "step5": "5 Gemma 4 ಬರೆದ ಟಿಪ್ಪಣಿ",
    "tagline": "ತೀರ್ಮಾನವನ್ನು ಪರಿಶೀಲನೆಗಳು ಮತ್ತು ಅಳತೆಗಳು ನಿರ್ಧರಿಸುತ್ತವೆ. Gemma 4 ಕೇವಲ ಟಿಪ್ಪಣಿ ಬರೆಯುತ್ತದೆ. "
               "ಇಂಟರ್ನೆಟ್ ಇಲ್ಲದೆ ಈ ಲ್ಯಾಪ್‌ಟಾಪ್‌ನಲ್ಲೇ ಕೆಲಸ ಮಾಡುತ್ತದೆ.",
    "footer": "ಕನ್ನಡ ಪಠ್ಯವನ್ನು ಯಂತ್ರದಿಂದ ಕರಡು ಮಾಡಲಾಗಿದೆ. ನಿಜವಾದ ಬಳಕೆಗೆ ಮೊದಲು ಕನ್ನಡ ಭಾಷಿಕರಿಂದ ಪರಿಶೀಲಿಸಿ.",
    # Sidebar
    "settings": "ಸೆಟ್ಟಿಂಗ್‌ಗಳು", "defect_type": "ಸಮಸ್ಯೆಯ ಪ್ರಕಾರ", "pothole": "ರಸ್ತೆ ಗುಂಡಿ", "garbage": "ಕಸ",
    "use_gemma": "Gemma 4 ಮೂಲಕ ಟಿಪ್ಪಣಿ ಬರೆಯಿರಿ (ಸ್ಥಳೀಯ)", "use_roi": "ಕೈಯಾರೆ ಸಮಸ್ಯೆ ಪೆಟ್ಟಿಗೆ (ಸ್ವಯಂ ಪತ್ತೆಯ ಬದಲು)",
    "roi_caption": "ದುರಸ್ತಿ ನಂತರದ ಫೋಟೋದಲ್ಲಿ ಪೆಟ್ಟಿಗೆಯ ಸ್ಥಾನ (%)", "roi_x": "x (ಎಡ)", "roi_y": "y (ಮೇಲೆ)", "roi_w": "ಅಗಲ",
    "roi_h": "ಎತ್ತರ",
    # Tabs
    "tab_verify": "ಪರಿಶೀಲಿಸಿ", "tab_fool": "ನಿಜವನ್ನು ಮೋಸಗೊಳಿಸಿ ನೋಡಿ", "tab_queue": "ಮರುಪರಿಶೀಲನೆ ಪಟ್ಟಿ",
    # Verify
    "up_before": "ದುರಸ್ತಿಗೆ ಮೊದಲ ಫೋಟೋ (ದೂರು)", "up_after": "ದುರಸ್ತಿ ನಂತರದ ಫೋಟೋ", "btn_verify": "ಪರಿಶೀಲಿಸಿ",
    "spinner": "ಸ್ಥಳ, ಫೋಟೋ ಮತ್ತು ದುರಸ್ತಿಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    "err_process": "ಈ ಫೋಟೋಗಳನ್ನು ಓದಲು ಆಗಲಿಲ್ಲ ({err}). ಬೇರೆ JPG ಅಥವಾ PNG ಫೋಟೋಗಳನ್ನು ಪ್ರಯತ್ನಿಸಿ.",
    "m_score": "ದುರಸ್ತಿ ಅಂಕ", "m_residual": "ಉಳಿದ ಸಮಸ್ಯೆ ಪ್ರದೇಶ", "m_time": "ಸಮಯ", "na": "ಇಲ್ಲ",
    "note": "ಟಿಪ್ಪಣಿ", "officer": "ಅಧಿಕಾರಿಗೆ", "citizen": "ನಾಗರಿಕರಿಗೆ",
    "src_gemma": "ಅಳತೆ ಮಾಡಿದ ಸಂಖ್ಯೆಗಳಿಂದ Gemma 4 (ಸ್ಥಳೀಯ)",
    "src_template": "ನಿಗದಿತ ಮಾದರಿ ಪಠ್ಯ",
    "src_kn_template": "ಅಳತೆಯ ಫಲಿತಾಂಶದಿಂದ ರಚಿಸಿದ ಕನ್ನಡ ಮಾದರಿ ಪಠ್ಯ",
    "src_kn_gemma": "Gemma 4 ಕನ್ನಡ ಅನುವಾದ, ಎಲ್ಲಾ ಸಂಖ್ಯೆಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
    "written_by": "ಬರೆದದ್ದು: {src}. ತೀರ್ಮಾನವನ್ನು Gemma ಎಂದಿಗೂ ನಿರ್ಧರಿಸುವುದಿಲ್ಲ.",
    "officer_en": "ಅಧಿಕಾರಿಗೆ ಮೂಲ ಇಂಗ್ಲಿಷ್ ಟಿಪ್ಪಣಿ",
    "btn_translate": "ನಾಗರಿಕರ ಸಂದೇಶವನ್ನು Gemma ಮೂಲಕ ಅನುವಾದಿಸಿ",
    "translate_fail": "Gemma ಅನುವಾದ ವಿಫಲವಾಗಿದೆ ಅಥವಾ ಸಂಖ್ಯೆ ಬದಲಾಗಿದೆ, ಆದ್ದರಿಂದ ಕನ್ನಡ ಮಾದರಿ ಪಠ್ಯ ತೋರಿಸಲಾಗಿದೆ.",
    "ov_before": "ಮೊದಲ ಫೋಟೋ, ನಂತರದ ಫೋಟೋಗೆ ಹೊಂದಿಸಲಾಗಿದೆ: ಹಳದಿ = ಸಮಸ್ಯೆ ಪ್ರದೇಶ, ಕೆಂಪು = ಸಮಸ್ಯೆ",
    "ov_after": "ನಂತರದ ಫೋಟೋ: ಕೆಂಪು = ಇನ್ನೂ ಉಳಿದ ಸಮಸ್ಯೆ",
    "gate1": "ಹಂತ 1 - ಒಂದೇ ಸ್ಥಳ", "gate2": "ಹಂತ 2 - ನಿಜವಾದ ಹೊಸ ಫೋಟೋ", "measure": "ಅಳತೆ - ಉಳಿದ ಸಮಸ್ಯೆ",
    "debug_title": "ಹಂತ 1 ವಿವರ - ಹೊಂದುವ ಬಿಂದುಗಳು",
    "debug_caption": "ಎಡ: ಮೊದಲು | ಬಲ: ನಂತರ. ಹಸಿರು = ಒಪ್ಪಿದ ಹೊಂದಾಣಿಕೆ, ಕೆಂಪು = ತಿರಸ್ಕರಿಸಿದ್ದು. {inl} / {good} ಹೊಂದಾಣಿಕೆಗಳು",
    "debug_none": "ಹೊಂದಾಣಿಕೆ ಚಿತ್ರ ಇಲ್ಲ: ಸಾಕಷ್ಟು ಬಿಂದುಗಳು ಸಿಗಲಿಲ್ಲ, ಅಥವಾ GPS ಪರಿಶೀಲನೆ ಮೊದಲೇ ವಿಫಲವಾಯಿತು.",
    "raw": "ಮೂಲ ಫಲಿತಾಂಶ (JSON)",
    "honesty": "ಪ್ರಾಮಾಣಿಕ ಸೂಚನೆ: ಸಮಸ್ಯೆಯನ್ನು ತರಬೇತಿ ಪಡೆದ ಮಾದರಿಯಿಂದಲ್ಲ, ಸರಳ ಚಿತ್ರ ನಿಯಮಗಳಿಂದ ಪತ್ತೆ ಮಾಡಲಾಗುತ್ತದೆ "
               "(ಗುಂಡಿಗೆ ಕಪ್ಪು ಮತ್ತು ಒರಟು ಭಾಗ, ಕಸಕ್ಕೆ ಬಣ್ಣ ಮತ್ತು ಗೊಂದಲ). ಸ್ವಯಂ ಪತ್ತೆ ತಪ್ಪಾದರೆ ಕೈಯಾರೆ ಪೆಟ್ಟಿಗೆ ಬಳಸಿ. "
               "ಗುಂಡಿಯ ಆಳವನ್ನು ಅಳೆಯಲಾಗುವುದಿಲ್ಲ.",
    # Fool tab
    "fool_intro": "ತೀರ್ಪುಗಾರರೇ: ನಕಲಿ ದುರಸ್ತಿಯನ್ನು ನಿಜದ ಕಣ್ಣು ತಪ್ಪಿಸಿ ಕಳುಹಿಸಲು ಪ್ರಯತ್ನಿಸಿ. ಕೆಳಗಿನ **ಮೊದಲ** ಫೋಟೋ ಕೃತಕ ಮಾದರಿ ಗುಂಡಿ. "
                  "ಒಂದು ದಾಳಿಯನ್ನು ಆರಿಸಿ, ಅಥವಾ ಕೆಳಗೆ ನಿಮ್ಮದೇ ಫೋಟೋ ಜೋಡಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
    "fool_before_cap": "ಮೊದಲು (ದೂರು)",
    "atk_reused": "ಹಳೆಯ ಫೋಟೋ ಮರುಬಳಕೆ", "atk_reused_d": "ಮೊದಲ ಫೋಟೋವನ್ನೇ ಚಿಕ್ಕದು ಮಾಡಿ ಮತ್ತೆ ಉಳಿಸಿ 'ನಂತರ' ಎಂದು ಕಳುಹಿಸಲಾಗಿದೆ.",
    "atk_screen": "ಪರದೆಯ ಫೋಟೋ", "atk_screen_d": "ನಿಜವಾದ ನಂತರದ ಫೋಟೋವನ್ನು ಮಾನಿಟರ್‌ನಿಂದ ಮತ್ತೆ ಫೋಟೋ ತೆಗೆಯಲಾಗಿದೆ (ಕೃತಕ ಮೊಯಿರೆ).",
    "atk_place": "ಬೇರೆ ಸ್ಥಳ", "atk_place_d": "ಬೇರೆ ಕಡೆ ತೆಗೆದ ಸ್ವಚ್ಛ ರಸ್ತೆಯ ಫೋಟೋ.",
    "attack": "ದಾಳಿ: {name}",
    "caught": "**{gate}** ಇದನ್ನು ಹಿಡಿಯಿತು: {reason}", "caught_measure": "ಹಿಡಿಯಲಾಗಿದೆ: {reason}",
    "not_caught": "ಪರಿಶೀಲನೆಗಳು ಇದನ್ನು ಹಿಡಿಯಲಿಲ್ಲ. ತೀರ್ಮಾನ: {verdict}. ನಿಜದ ಪರಿಶೀಲನೆಗಳು ಅಂದಾಜು ನಿಯಮಗಳು, ಮೋಸ ಸಾಧ್ಯ.",
    "free_upload": "**ಉಚಿತ ಅಪ್‌ಲೋಡ್:** ನಿಮ್ಮ ಮೊದಲ ಫೋಟೋ ಮತ್ತು ಯಾವುದೇ ನಂತರದ ಫೋಟೋ (ಹಳೆಯ ಫೋಟೋ, ಪರದೆಯ ಫೋಟೋ, ಬೇರೆ ರಸ್ತೆ).",
    "fb_before": "ಮೊದಲು", "fb_after": "ನಂತರ (ನಿಮ್ಮ ದಾಳಿ)", "btn_try": "ಪ್ರಯತ್ನಿಸಿ",
    # Queue
    "queue_intro": "`data/pairs/<id>/` ನಲ್ಲಿರುವ ಪ್ರತಿ ಜೋಡಿ, {order} ಕ್ರಮದಲ್ಲಿ, ಕಡಿಮೆ ಅಂಕ ಮೊದಲು. ವೇಗಕ್ಕಾಗಿ ಇಲ್ಲಿ ಮಾದರಿ ಟಿಪ್ಪಣಿ ಬಳಸಲಾಗಿದೆ.",
    "queue_empty": "ಇನ್ನೂ ಜೋಡಿಗಳಿಲ್ಲ. data/pairs/p01/ ನಂತಹ ಫೋಲ್ಡರ್‌ಗಳಲ್ಲಿ before.jpg, after.jpg ಮತ್ತು label.json ಸೇರಿಸಿ.",
    "btn_refresh": "ಪಟ್ಟಿ ನವೀಕರಿಸಿ", "queue_spinner": "{n} ಜೋಡಿಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    "err_queue": "ಪಟ್ಟಿ ರಚಿಸಲು ಆಗಲಿಲ್ಲ ({err}).",
    "col_priority": "ಆದ್ಯತೆ", "col_pair": "ಜೋಡಿ", "col_verdict": "ತೀರ್ಮಾನ", "col_score": "ಅಂಕ", "col_residual": "ಉಳಿದ %",
    "col_why": "ಕಾರಣ", "col_type": "ಪ್ರಕಾರ", "col_label": "ನಿಜ ಲೇಬಲ್", "col_ms": "ms",
    # Verdicts
    "v_Verified": "ದುರಸ್ತಿ ದೃಢಪಟ್ಟಿದೆ", "v_Partial": "ಭಾಗಶಃ ದುರಸ್ತಿ", "v_Not fixed": "ದುರಸ್ತಿ ಆಗಿಲ್ಲ",
    "v_Cannot verify": "ಪರಿಶೀಲಿಸಲು ಆಗುತ್ತಿಲ್ಲ",
    # Geometry Lab
    "lab_tab": "ಜ್ಯಾಮಿತಿ ಪ್ರಯೋಗಾಲಯ",
    "lab_intro": "ಎರಡು ಫೋಟೋಗಳ ನಡುವೆ ಏನು ಬದಲಾಗಿದೆ ಎಂದು ಹಂತ ಹಂತವಾಗಿ ನೋಡಿ. ಕೆಳಗಿನ ಪ್ರತಿ ಚಿತ್ರವೂ ನಿಜ ಅಳೆದ ಸಂಖ್ಯೆಗಳಿಂದಲೇ ರಚನೆಯಾಗಿದೆ.",
    "lab_source": "ಫೋಟೋ ಜೋಡಿ", "lab_last": "ಪರಿಶೀಲಿಸಿ ಟ್ಯಾಬ್‌ನ ಕೊನೆಯ ಜೋಡಿ", "lab_run": "ಜ್ಯಾಮಿತಿ ಪ್ರಯೋಗ ನಡೆಸಿ",
    "lab_running": "ಜ್ಯಾಮಿತಿಯನ್ನು ಅಳೆಯಲಾಗುತ್ತಿದೆ...", "lab_done": "ಜ್ಯಾಮಿತಿ ಪ್ರಯೋಗ ಮುಗಿದಿದೆ",
    "lab_what": "ಸಂಖ್ಯೆಗಳು ಏನು ಹೇಳುತ್ತವೆ",
    "lab_skip_gate1": "ಬಿಡಲಾಗಿದೆ: ಫೋಟೋಗಳು ಒಂದೇ ಸ್ಥಳದವು ಎಂದು ಹೊಂದಲಿಲ್ಲ, ಆದ್ದರಿಂದ ತೋರಿಸಲು ರೂಪಾಂತರ ಇಲ್ಲ.",
    "lab_skip_measure": "ಬಿಡಲಾಗಿದೆ: ಈ ಜೋಡಿಗೆ ಸಮಸ್ಯೆಯ ಅಳತೆ ಇಲ್ಲ.",
    "lab_compact": "ಒಂದು ನೋಟದಲ್ಲಿ ಜ್ಯಾಮಿತಿ", "lab_open_full": "ಎಲ್ಲಾ 7 ಹಂತಗಳಿಗೆ ಜ್ಯಾಮಿತಿ ಪ್ರಯೋಗಾಲಯ ಟ್ಯಾಬ್ ತೆರೆಯಿರಿ.",
    "lab_img_note": "ಚಿತ್ರಗಳ ಒಳಗಿನ ಬರಹಗಳು ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿವೆ.",
    "s1_t": "1. ಮುಖ್ಯ ಬಿಂದುಗಳು", "s1_c": "ಎರಡೂ ಫೋಟೋಗಳಲ್ಲಿ ಮತ್ತೆ ಸಿಗುವ ಮೂಲೆಗಳು ಮತ್ತು ವಿನ್ಯಾಸಗಳು (ಹಳದಿ ವೃತ್ತಗಳು).",
    "s2_t": "2. ಹೊಂದಾಣಿಕೆಗಳು", "s2_c": "ಹಸಿರು ಗೆರೆಗಳು ಎರಡೂ ಫೋಟೋಗಳ ಒಂದೇ ಬಿಂದುವನ್ನು ಜೋಡಿಸುತ್ತವೆ. ಕೆಂಪು ಗೆರೆಗಳನ್ನು RANSAC ತಿರಸ್ಕರಿಸಿದೆ.",
    "s3_t": "3. ಕ್ಯಾಮೆರಾ ಬದಲಾವಣೆ (ಹೋಮೋಗ್ರಫಿ)", "s3_c": "ಹಳದಿ ಪೆಟ್ಟಿಗೆ ಮೊದಲ ಫೋಟೋದ ಚೌಕಟ್ಟು ನಂತರದ ಫೋಟೋದಲ್ಲಿ ಎಲ್ಲಿ ಬೀಳುತ್ತದೆ ಎಂದು ತೋರಿಸುತ್ತದೆ.",
    "s4_t": "4. ಹೊಂದಿಸಿದ ಹೋಲಿಕೆ", "s4_c": "ಸ್ಲೈಡರ್ ಎಳೆಯಿರಿ: ಹೊಂದಿಸಿದ ಮೊದಲ ಫೋಟೋ ಮತ್ತು ನಂತರದ ಫೋಟೋ.",
    "s5_t": "5. ವ್ಯತ್ಯಾಸದ ಶಾಖ ನಕ್ಷೆ", "s5_c": "ಹೊಂದಿಸಿದ ನಂತರ ಪ್ರತಿ ಜಾಗ ಎಷ್ಟು ಬದಲಾಗಿದೆ. ಕಪ್ಪು = ಬದಲಾವಣೆ ಇಲ್ಲ, ಹಳದಿಯಿಂದ ಕೆಂಪು = ಹೆಚ್ಚು ಬದಲಾವಣೆ.",
    "s6_t": "6. ಸಮಸ್ಯೆಯ ಗಡಿರೇಖೆ", "s6_c": "ಹಸಿರು ಗೆರೆ ಮೊದಲ ಫೋಟೋದ ಸಮಸ್ಯೆ. ಕೆಂಪು ಭಾಗ ಈಗಲೂ ಉಳಿದಿರುವುದು.",
    "s7_t": "7. ಉಳಿದ ಸಮಸ್ಯೆ", "s7_c": "ಮೊದಲು ಮತ್ತು ನಂತರದ ಸಮಸ್ಯೆ ಪ್ರದೇಶ, ಅಂಚಿನ ಸಾಂದ್ರತೆ ಬದಲಾವಣೆ ಮತ್ತು ಹಳೆಯ ಗಡಿಯ ಸುತ್ತ ಜೋಡಣೆ ಗುರುತು.",
    "sample_fixed": "ಮಾದರಿ: ದುರಸ್ತಿ ಆಗಿದೆ", "sample_partial": "ಮಾದರಿ: ಅರ್ಧ ದುರಸ್ತಿ", "sample_notfixed": "ಮಾದರಿ: ದುರಸ್ತಿ ಆಗಿಲ್ಲ",
    "sample_otherplace": "ಮಾದರಿ: ಬೇರೆ ಸ್ಥಳ",
    "match_caption": "{inl} ಒಪ್ಪಿದ / {good} ಹೊಂದಾಣಿಕೆಗಳು",
    # Residual bars
    "bar_before": "ಮೊದಲು ಸಮಸ್ಯೆ ಪ್ರದೇಶ", "bar_after": "ನಂತರ ಸಮಸ್ಯೆ ಪ್ರದೇಶ", "bar_edge": "ಅಂಚಿನ ಸಾಂದ್ರತೆ (ನಂತರ / ಮೊದಲು)",
    "bar_seam": "ಹಳೆಯ ಗಡಿಯ ಸುತ್ತ ಜೋಡಣೆ ಅಂಚುಗಳು",
    # Bullets
    "b_same": "ಒಂದೇ ಸ್ಥಳ: {inl} ಹೊಂದುವ ಬಿಂದುಗಳು ಒಂದೇ ಕ್ಯಾಮೆರಾ ರೂಪಾಂತರಕ್ಕೆ ಒಪ್ಪುತ್ತವೆ (ಹೊಂದಾಣಿಕೆಗಳ {ratio}%).{gps}",
    "b_gps": " GPS ಪ್ರಕಾರ {m} ಮೀ ದೂರ.",
    "b_notsame": "ಒಂದೇ ಸ್ಥಳ ಅಲ್ಲ: {reason}.", "b_gate2": "ಫೋಟೋವನ್ನು ನಿಜವಾದ ಹೊಸ ಫೋಟೋ ಎಂದು ಒಪ್ಪಲಿಲ್ಲ: {reason}.",
    "b_area": "ಸಮಸ್ಯೆ ಪ್ರದೇಶ {b} px ನಿಂದ {a} px ಗೆ ಬದಲಾಗಿದೆ ({pct}% {word}).", "w_smaller": "ಕಡಿಮೆ", "w_larger": "ಹೆಚ್ಚು",
    "b_edge": "ಸಮಸ್ಯೆಯ ಒಳಗಿನ ಅಂಚಿನ ಸಾಂದ್ರತೆ ಈಗ ಮೊದಲಿನ {r} ಪಟ್ಟು ({word}).",
    "w_smoother": "ಮೇಲ್ಮೈ ನಯವಾಗಿದೆ", "w_rough": "ಇನ್ನೂ ಒರಟಾಗಿದೆ",
    "b_measure": "ಅಳತೆ: {m}.",
    # Camera change words
    "hw_none": "ರೂಪಾಂತರ ಇಲ್ಲ: ಫೋಟೋಗಳು ಒಂದೇ ಸ್ಥಳದವು ಎಂದು ಹೊಂದಲಿಲ್ಲ.",
    "hw_right": "{n} px ಬಲಕ್ಕೆ", "hw_left": "{n} px ಎಡಕ್ಕೆ", "hw_down": "{n} px ಕೆಳಕ್ಕೆ", "hw_up": "{n} px ಮೇಲಕ್ಕೆ", "hw_and": " ಮತ್ತು ",
    "hw_shift": "{parts} ಸರಿದಿದೆ", "hw_same_pos": "ಅದೇ ಸ್ಥಾನದಲ್ಲಿದೆ",
    "hw_noturn": "ತಿರುಗಿಲ್ಲ", "hw_turn": "{dir} {deg} ಡಿಗ್ರಿ ತಿರುಗಿದೆ", "hw_cw": "ಗಡಿಯಾರದ ದಿಕ್ಕಿನಲ್ಲಿ",
    "hw_acw": "ಗಡಿಯಾರದ ವಿರುದ್ಧ ದಿಕ್ಕಿನಲ್ಲಿ",
    "hw_same_size": "ಅದೇ ಗಾತ್ರ", "hw_size": "{s} ಪಟ್ಟು ಗಾತ್ರ",
    "hw_sentence": "ದುರಸ್ತಿ ನಂತರದ ಫೋಟೋದಲ್ಲಿ ದೃಶ್ಯ {shift}, {turn}, {size}.",
}

EN.update({
    # Roles
    "role": "View as", "role_citizen": "Citizen", "role_officer": "Officer", "role_auditor": "Auditor",
    # Location
    "loc_title": "Location", "loc_before": "Before photo GPS", "loc_after": "After photo GPS", "loc_none": "not in photo",
    "loc_dist": "Distance between the two photos: {m} m", "loc_nodist": "Distance unknown: GPS missing in at least one photo.",
    "loc_gate1": "Gate 1 says: {reason}",
    "loc_map_note": "Map tiles need internet. Offline, use the coordinates above.",
    "loc_corp": "GBA corporation", "loc_ward": "Ward name", "loc_officer_note": "Entered by officer, not verified.",
    "loc_pick": "(not set)",
    # Citizen view
    "cit_listen": "Listen", "cit_whatsapp": "Share on WhatsApp", "cit_feedback": "Still not fixed? Tell us",
    "cit_feedback_done": "Thank you. Your report is saved on this device and shows as a flag in the auditor queue.",
    "voice_no_voice": "No voice for this language is installed, reading in English.",
    "voice_no_speech": "This browser cannot read aloud.",
    # Officer view
    "off_retake": "Retake guide", "off_retake_intro": "Hold the phone so the faded before photo lines up with what you see.",
    "off_tip1": "Same angle as the before photo.", "off_tip2": "Same distance, about 2 to 3 metres.",
    "off_tip3": "Keep road edges, kerbs or poles in the frame.",
    "off_why": "Why Nija could not verify",
    # Auditor view
    "aud_evidence": "Download evidence pack (ZIP)", "aud_csv": "Download queue as CSV",
    "aud_filter_verdict": "Show verdicts", "aud_filter_type": "Show types", "aud_flag": "Citizen flags",
    "aud_pick": "Evidence pack for pair", "aud_build": "Build evidence pack",
    # Why Karnataka tab
    "tab_why": "Why Karnataka",
    "why_title": "Why this matters in Karnataka",
    "why_journey": "A complaint's journey", "why_today": "Today", "why_nija": "With Nija",
    "j_report": "Report", "j_assign": "Assign", "j_repair": "Repair", "j_close": "Close", "j_reopen": "Reopen", "j_audit": "Audit",
    "why_today_line": "At Close, a ticket can be marked resolved with no photo, or a photo nobody checks.",
    "why_nija_line": "At Close, Nija compares the photos: verified repairs close, doubtful ones go to re-inspection.",
    "why_facts": "What has been reported", "why_as_reported": "as reported by {outlet}",
    "why_no_link": "source link to be added (we could not find the original article)",
    "why_fits": "Where Nija fits", "why_inputs": "Existing complaint channels", "why_outputs": "Who uses the result",
    "why_limits": "What Nija does not prove",
    "why_limits_body": "Nija checks that the photo shows the same place, is a fresh photo, and that the visible defect area shrank. "
                       "It does not prove repair quality, how long the repair will last, or depth (depth is not measured). "
                       "The test set is small and self-made. In the systems we looked at, we found no deployed system "
                       "that does this check at closure.",
})

KN.update({
    "role": "ಯಾರಾಗಿ ನೋಡುವುದು", "role_citizen": "ನಾಗರಿಕ", "role_officer": "ಅಧಿಕಾರಿ", "role_auditor": "ಲೆಕ್ಕಪರಿಶೋಧಕ",
    "loc_title": "ಸ್ಥಳ", "loc_before": "ಮೊದಲ ಫೋಟೋದ GPS", "loc_after": "ನಂತರದ ಫೋಟೋದ GPS", "loc_none": "ಫೋಟೋದಲ್ಲಿ ಇಲ್ಲ",
    "loc_dist": "ಎರಡು ಫೋಟೋಗಳ ನಡುವಿನ ದೂರ: {m} ಮೀ", "loc_nodist": "ದೂರ ತಿಳಿದಿಲ್ಲ: ಒಂದಾದರೂ ಫೋಟೋದಲ್ಲಿ GPS ಇಲ್ಲ.",
    "loc_gate1": "ಹಂತ 1 ಹೇಳುವುದು: {reason}",
    "loc_map_note": "ನಕ್ಷೆಗೆ ಇಂಟರ್ನೆಟ್ ಬೇಕು. ಇಂಟರ್ನೆಟ್ ಇಲ್ಲದಿದ್ದರೆ ಮೇಲಿನ ನಿರ್ದೇಶಾಂಕಗಳನ್ನು ಬಳಸಿ.",
    "loc_corp": "GBA ನಗರ ಪಾಲಿಕೆ", "loc_ward": "ವಾರ್ಡ್ ಹೆಸರು", "loc_officer_note": "ಅಧಿಕಾರಿ ನಮೂದಿಸಿದ್ದು, ಪರಿಶೀಲಿಸಿಲ್ಲ.",
    "loc_pick": "(ಆಯ್ಕೆ ಮಾಡಿಲ್ಲ)",
    "cit_listen": "ಕೇಳಿ", "cit_whatsapp": "WhatsApp ನಲ್ಲಿ ಹಂಚಿಕೊಳ್ಳಿ", "cit_feedback": "ಇನ್ನೂ ದುರಸ್ತಿ ಆಗಿಲ್ಲವೇ? ತಿಳಿಸಿ",
    "cit_feedback_done": "ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ವರದಿ ಈ ಸಾಧನದಲ್ಲಿ ಉಳಿಸಲಾಗಿದೆ ಮತ್ತು ಲೆಕ್ಕಪರಿಶೋಧಕರ ಪಟ್ಟಿಯಲ್ಲಿ ಗುರುತಾಗಿ ಕಾಣುತ್ತದೆ.",
    "voice_no_voice": "ಈ ಭಾಷೆಯ ಧ್ವನಿ ಸ್ಥಾಪಿಸಿಲ್ಲ, ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಓದಲಾಗುತ್ತಿದೆ.",
    "voice_no_speech": "ಈ ಬ್ರೌಸರ್ ಜೋರಾಗಿ ಓದಲು ಸಾಧ್ಯವಿಲ್ಲ.",
    "off_retake": "ಮತ್ತೆ ಫೋಟೋ ತೆಗೆಯುವ ಮಾರ್ಗದರ್ಶಿ", "off_retake_intro": "ಮಸುಕಾದ ಮೊದಲ ಫೋಟೋ ನೀವು ನೋಡುವ ದೃಶ್ಯಕ್ಕೆ ಹೊಂದುವಂತೆ ಫೋನ್ ಹಿಡಿಯಿರಿ.",
    "off_tip1": "ಮೊದಲ ಫೋಟೋದ ಅದೇ ಕೋನ.", "off_tip2": "ಅದೇ ದೂರ, ಸುಮಾರು 2 ರಿಂದ 3 ಮೀಟರ್.",
    "off_tip3": "ರಸ್ತೆ ಅಂಚು, ಕರ್ಬ್ ಅಥವಾ ಕಂಬಗಳು ಚೌಕಟ್ಟಿನಲ್ಲಿ ಇರಲಿ.",
    "off_why": "ನಿಜ ಏಕೆ ಪರಿಶೀಲಿಸಲು ಆಗಲಿಲ್ಲ",
    "aud_evidence": "ಸಾಕ್ಷ್ಯ ಪ್ಯಾಕ್ ಡೌನ್‌ಲೋಡ್ (ZIP)", "aud_csv": "ಪಟ್ಟಿಯನ್ನು CSV ಆಗಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "aud_filter_verdict": "ತೀರ್ಮಾನಗಳು", "aud_filter_type": "ಪ್ರಕಾರಗಳು", "aud_flag": "ನಾಗರಿಕರ ಗುರುತುಗಳು",
    "aud_pick": "ಸಾಕ್ಷ್ಯ ಪ್ಯಾಕ್‌ಗೆ ಜೋಡಿ", "aud_build": "ಸಾಕ್ಷ್ಯ ಪ್ಯಾಕ್ ರಚಿಸಿ",
    "tab_why": "ಕರ್ನಾಟಕಕ್ಕೆ ಏಕೆ",
    "why_title": "ಕರ್ನಾಟಕದಲ್ಲಿ ಇದು ಏಕೆ ಮುಖ್ಯ",
    "why_journey": "ಒಂದು ದೂರಿನ ಪ್ರಯಾಣ", "why_today": "ಇಂದು", "why_nija": "ನಿಜ ಜೊತೆ",
    "j_report": "ದೂರು", "j_assign": "ಹಂಚಿಕೆ", "j_repair": "ದುರಸ್ತಿ", "j_close": "ಮುಕ್ತಾಯ", "j_reopen": "ಮರು ತೆರೆಯುವಿಕೆ",
    "j_audit": "ಲೆಕ್ಕಪರಿಶೋಧನೆ",
    "why_today_line": "ಮುಕ್ತಾಯದ ಹಂತದಲ್ಲಿ, ಫೋಟೋ ಇಲ್ಲದೆ ಅಥವಾ ಯಾರೂ ಪರಿಶೀಲಿಸದ ಫೋಟೋದೊಂದಿಗೆ ದೂರನ್ನು ಪರಿಹರಿಸಲಾಗಿದೆ ಎಂದು ಗುರುತಿಸಬಹುದು.",
    "why_nija_line": "ಮುಕ್ತಾಯದ ಹಂತದಲ್ಲಿ ನಿಜ ಫೋಟೋಗಳನ್ನು ಹೋಲಿಸುತ್ತದೆ: ದೃಢಪಟ್ಟ ದುರಸ್ತಿ ಮುಕ್ತಾಯ, ಸಂಶಯಾಸ್ಪದವು ಮರುಪರಿಶೀಲನೆಗೆ.",
    "why_facts": "ವರದಿಯಾಗಿರುವುದು", "why_as_reported": "{outlet} ವರದಿ ಪ್ರಕಾರ",
    "why_no_link": "ಮೂಲ ಲಿಂಕ್ ಸೇರಿಸಬೇಕಿದೆ (ಮೂಲ ಲೇಖನ ನಮಗೆ ಸಿಗಲಿಲ್ಲ)",
    "why_fits": "ನಿಜ ಎಲ್ಲಿ ಸೇರುತ್ತದೆ", "why_inputs": "ಈಗಿರುವ ದೂರು ಮಾರ್ಗಗಳು", "why_outputs": "ಫಲಿತಾಂಶ ಬಳಸುವವರು",
    "why_limits": "ನಿಜ ಏನನ್ನು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ",
    "why_limits_body": "ಫೋಟೋ ಅದೇ ಸ್ಥಳದ್ದು, ಹೊಸ ಫೋಟೋ, ಮತ್ತು ಕಾಣುವ ಸಮಸ್ಯೆ ಪ್ರದೇಶ ಕಡಿಮೆಯಾಗಿದೆ ಎಂದು ನಿಜ ಪರಿಶೀಲಿಸುತ್ತದೆ. "
                       "ದುರಸ್ತಿಯ ಗುಣಮಟ್ಟ, ಎಷ್ಟು ಕಾಲ ಉಳಿಯುತ್ತದೆ, ಅಥವಾ ಆಳವನ್ನು (ಆಳ ಅಳೆಯುವುದಿಲ್ಲ) ಇದು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ. "
                       "ಪರೀಕ್ಷಾ ಸಂಗ್ರಹ ಚಿಕ್ಕದು ಮತ್ತು ನಾವೇ ತಯಾರಿಸಿದ್ದು. ನಾವು ನೋಡಿದ ವ್ಯವಸ್ಥೆಗಳಲ್ಲಿ, ಮುಕ್ತಾಯದ ಹಂತದಲ್ಲಿ "
                       "ಈ ಪರಿಶೀಲನೆ ಮಾಡುವ ಬಳಕೆಯಲ್ಲಿರುವ ವ್ಯವಸ್ಥೆ ನಮಗೆ ಸಿಗಲಿಲ್ಲ.",
})

# Fact cards for the Why Karnataka tab: (English, Kannada, outlet, url or None). Links checked on 31 Oct 2026.
FACTS = [
    ("BBMP logged 2.37 lakh complaints from Jan 2023 to Sep 2024. Many citizens say tickets are closed without the problem being fixed.",
     "ಜನವರಿ 2023 ರಿಂದ ಸೆಪ್ಟೆಂಬರ್ 2024 ರವರೆಗೆ BBMP ಗೆ 2.37 ಲಕ್ಷ ದೂರುಗಳು ಬಂದಿವೆ. ಸಮಸ್ಯೆ ಸರಿಪಡಿಸದೆ ದೂರು ಮುಚ್ಚಲಾಗುತ್ತದೆ ಎಂದು ಅನೇಕ ನಾಗರಿಕರು ಹೇಳುತ್ತಾರೆ.",
     "Deccan Herald", "https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fbengaluru%2Fbbmp-lavishes-more-funds-on-streetlights-but-complaints-surge-3180698"),
    ("A Rajajinagar resident filed 21 complaints over 83 days, then paid about Rs 10,500 to fix the road himself.",
     "ರಾಜಾಜಿನಗರದ ನಿವಾಸಿಯೊಬ್ಬರು 83 ದಿನಗಳಲ್ಲಿ 21 ದೂರು ನೀಡಿ, ನಂತರ ಸುಮಾರು 10,500 ರೂ. ಖರ್ಚು ಮಾಡಿ ತಾವೇ ರಸ್ತೆ ಸರಿಪಡಿಸಿದರು.",
     "Deccan Herald", None),
    ("The Lokayukta found Rs 118.26 crore paid for works in RR Nagar; only 2 of 114 works were executed properly.",
     "RR ನಗರದ ಕಾಮಗಾರಿಗಳಿಗೆ 118.26 ಕೋಟಿ ರೂ. ಪಾವತಿಸಲಾಗಿದೆ; 114 ಕಾಮಗಾರಿಗಳಲ್ಲಿ 2 ಮಾತ್ರ ಸರಿಯಾಗಿ ನಡೆದಿವೆ ಎಂದು ಲೋಕಾಯುಕ್ತ ಕಂಡುಕೊಂಡಿದೆ.",
     "Deccan Herald, 2022", "https://www.deccanherald.com/india/karnataka/bengaluru/lokayukta-unearths-a-rs-11826-crore-scam-in-bbmp-1079580.html"),
    ("On 14 Aug 2026 the Karnataka High Court asked the GBA for a detailed affidavit on preventing and repairing potholes.",
     "14 ಆಗಸ್ಟ್ 2026 ರಂದು ಕರ್ನಾಟಕ ಹೈಕೋರ್ಟ್ ಗುಂಡಿ ತಡೆ ಮತ್ತು ದುರಸ್ತಿ ಬಗ್ಗೆ ವಿವರವಾದ ಪ್ರಮಾಣಪತ್ರ ಸಲ್ಲಿಸಲು GBA ಗೆ ಸೂಚಿಸಿತು.",
     "LiveLaw", "https://www.livelaw.in/high-court/karnataka-high-court/karnataka-high-court-pothole-crisis-bbmp-claims-potholes-545776"),
    ("Earlier, the High Court asked NHAI to inspect pothole repair work commissioned by BBMP.",
     "ಹಿಂದೆ, BBMP ಮಾಡಿಸಿದ ಗುಂಡಿ ದುರಸ್ತಿ ಕೆಲಸವನ್ನು ಪರಿಶೀಲಿಸಲು ಹೈಕೋರ್ಟ್ NHAI ಗೆ ಸೂಚಿಸಿತ್ತು.",
     "LiveLaw", "https://livelaw.in/news-updates/karnataka-high-court-potholes-bengaluru-bbmp-nhai-213047"),
    ("9,438 people died in pothole-related crashes in India from 2020 to 2024 (MoRTH reply in the Lok Sabha, Feb 2026).",
     "2020 ರಿಂದ 2024 ರವರೆಗೆ ಭಾರತದಲ್ಲಿ ಗುಂಡಿ ಸಂಬಂಧಿತ ಅಪಘಾತಗಳಲ್ಲಿ 9,438 ಜನರು ಮೃತಪಟ್ಟಿದ್ದಾರೆ (ಲೋಕಸಭೆಯಲ್ಲಿ MoRTH ಉತ್ತರ, ಫೆಬ್ರವರಿ 2026).",
     "Siasat", "https://www.siasat.com/pothole-related-road-deaths-surge-53-in-5-yrs-9438-killed-nationwide-3348935/"),
    ("Bengaluru recorded the most deaths due to civic negligence of any Indian city for the sixth year running: 17 in 2024 (NCRB).",
     "ನಾಗರಿಕ ಸಂಸ್ಥೆಗಳ ನಿರ್ಲಕ್ಷ್ಯದಿಂದ ಸಾವುಗಳಲ್ಲಿ ಬೆಂಗಳೂರು ಸತತ ಆರನೇ ವರ್ಷ ಮೊದಲ ಸ್ಥಾನದಲ್ಲಿದೆ: 2024 ರಲ್ಲಿ 17 (NCRB).",
     "ThePrint", "https://theprint.in/india/a-pothole-death-ignites-public-anger-against-shivakumar-govt-minister-santosh-lads-remarks-fuel-bonfire/3014128/"),
    ("8,046 of 14,795 identified potholes in Bengaluru were still unrepaired in September 2025.",
     "ಸೆಪ್ಟೆಂಬರ್ 2025 ರಲ್ಲಿ ಬೆಂಗಳೂರಿನಲ್ಲಿ ಗುರುತಿಸಿದ 14,795 ಗುಂಡಿಗಳಲ್ಲಿ 8,046 ಇನ್ನೂ ದುರಸ್ತಿಯಾಗಿರಲಿಲ್ಲ.",
     "ETV Bharat", "https://www.etvbharat.com/en/!state/fix-potholes-in-bengaluru-by-oct-31-else-engineers-will-face-action-cm-siddaramaiah-enn25092101505"),
    ("The Kannada Language Comprehensive Development Act, 2022 requires Kannada in state administration; its amendment took effect on 12 March 2024. "
     "We could not confirm the exact clause on digital services, so check the Act before quoting it.",
     "ಕನ್ನಡ ಭಾಷಾ ಸಮಗ್ರ ಅಭಿವೃದ್ಧಿ ಅಧಿನಿಯಮ, 2022 ರಾಜ್ಯ ಆಡಳಿತದಲ್ಲಿ ಕನ್ನಡ ಬಳಕೆಯನ್ನು ಕಡ್ಡಾಯಗೊಳಿಸುತ್ತದೆ; ಅದರ ತಿದ್ದುಪಡಿ 12 ಮಾರ್ಚ್ 2024 ರಿಂದ ಜಾರಿಯಲ್ಲಿದೆ. "
     "ಡಿಜಿಟಲ್ ಸೇವೆಗಳ ನಿಖರ ಷರತ್ತನ್ನು ನಾವು ದೃಢಪಡಿಸಿಲ್ಲ.",
     "India Code (the Act)", "https://www.indiacode.nic.in/bitstream/123456789/19592/1/13of2023%28e%29_k_%26_c.pdf"),
]

EN.update({
    "bar_box_before": "Box vs road distance, before", "bar_box_after": "Box vs road distance, after",
    "bar_box_note": "Box-based look-alike measure: how unlike the surrounding road the box looks (texture, edges, colour).",
    "b_box": "Inside the defect box, the look-alike distance to the surrounding road went from {db} to {da}, so {pct}% of the defect look remains.",
})
KN.update({
    "bar_box_before": "ಪೆಟ್ಟಿಗೆ ಮತ್ತು ರಸ್ತೆ ನಡುವಿನ ಅಂತರ, ಮೊದಲು", "bar_box_after": "ಪೆಟ್ಟಿಗೆ ಮತ್ತು ರಸ್ತೆ ನಡುವಿನ ಅಂತರ, ನಂತರ",
    "bar_box_note": "ಪೆಟ್ಟಿಗೆ ಆಧಾರಿತ ಹೋಲಿಕೆ ಅಳತೆ: ಪೆಟ್ಟಿಗೆಯ ಒಳಭಾಗ ಸುತ್ತಲಿನ ರಸ್ತೆಗಿಂತ ಎಷ್ಟು ಭಿನ್ನವಾಗಿದೆ (ವಿನ್ಯಾಸ, ಅಂಚು, ಬಣ್ಣ).",
    "b_box": "ಸಮಸ್ಯೆ ಪೆಟ್ಟಿಗೆಯೊಳಗೆ ಸುತ್ತಲಿನ ರಸ್ತೆಗೆ ಹೋಲಿಕೆ ಅಂತರ {db} ನಿಂದ {da} ಗೆ ಬದಲಾಗಿದೆ, ಅಂದರೆ ಸಮಸ್ಯೆಯ ನೋಟದ {pct}% ಉಳಿದಿದೆ.",
})

EN.update({
    "signin_title": "Sign in (demo)", "signin_intro": "Pick a preset account to open its view. You can switch views later in the header.",
    "signin_as": "Sign in as {role}", "signin_skip": "Skip sign-in", "signout": "Sign out",
    "signin_banner": "Demo sign-in: no real authentication, for the hackathon only.", "signed_as": "Signed in as {acct}.",
})
KN.update({
    "signin_title": "ಸೈನ್ ಇನ್ (ಡೆಮೊ)", "signin_intro": "ಅದರ ನೋಟ ತೆರೆಯಲು ಒಂದು ಸಿದ್ಧ ಖಾತೆಯನ್ನು ಆರಿಸಿ. ನಂತರ ಮೇಲಿನ ಪಟ್ಟಿಯಲ್ಲಿ ನೋಟ ಬದಲಾಯಿಸಬಹುದು.",
    "signin_as": "{role} ಆಗಿ ಸೈನ್ ಇನ್", "signin_skip": "ಸೈನ್ ಇನ್ ಬಿಟ್ಟು ಮುಂದುವರಿಯಿರಿ", "signout": "ಸೈನ್ ಔಟ್",
    "signin_banner": "ಡೆಮೊ ಸೈನ್ ಇನ್: ನಿಜವಾದ ದೃಢೀಕರಣ ಇಲ್ಲ, ಹ್ಯಾಕಥಾನ್‌ಗೆ ಮಾತ್ರ.", "signed_as": "{acct} ಆಗಿ ಸೈನ್ ಇನ್ ಆಗಿದೆ.",
})

EN.update({
    "sum_title": "Auditor summary by GBA corporation", "sum_corp": "Corporation", "sum_reviewed": "Reviewed",
    "sum_pct": "% Verified", "sum_unassigned": "Unassigned", "sum_claimed": "Claimed fixed", "sum_verified": "Verified by Nija",
    "sum_chart": "Claimed vs verified", "sum_csv": "Download summary as CSV",
    "sum_note": "Corporation comes from each pair's label.json (\"corporation\"); pairs without one are Unassigned.",
    "loc_gmaps": "Open in Google Maps",
    "tab_roadmap": "Platform roadmap", "rm_title": "From complaint to verified closure",
    "rm_intake": "Intake channels", "rm_verify": "Nija verification", "rm_outputs": "Outputs",
    "rm_app": "Mobile app upload", "rm_whatsapp": "WhatsApp", "rm_1533": "1533 call-centre agent upload",
    "rm_web": "Web upload (this demo)", "rm_gates": "Gate 1 same place + Gate 2 real, fresh photo", "rm_measure": "Measure what is left",
    "rm_citizen": "Citizen message in Kannada / English with voice", "rm_officer": "Officer re-inspection list",
    "rm_auditor": "Auditor ward dashboard", "rm_built": "Built", "rm_planned": "Planned",
    "rm_honest": "Calls and WhatsApp intake are planned integrations, not built.",
})
KN.update({
    "sum_title": "GBA ನಗರ ಪಾಲಿಕೆವಾರು ಲೆಕ್ಕಪರಿಶೋಧಕರ ಸಾರಾಂಶ", "sum_corp": "ನಗರ ಪಾಲಿಕೆ", "sum_reviewed": "ಪರಿಶೀಲಿಸಿದವು",
    "sum_pct": "% ದೃಢಪಟ್ಟಿದೆ", "sum_unassigned": "ನಿಗದಿಪಡಿಸಿಲ್ಲ", "sum_claimed": "ದುರಸ್ತಿ ಎಂದು ಹೇಳಿದ್ದು", "sum_verified": "ನಿಜ ದೃಢಪಡಿಸಿದ್ದು",
    "sum_chart": "ಹೇಳಿದ್ದು ಮತ್ತು ದೃಢಪಟ್ಟದ್ದು", "sum_csv": "ಸಾರಾಂಶವನ್ನು CSV ಆಗಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "sum_note": "ನಗರ ಪಾಲಿಕೆ ಪ್ರತಿ ಜೋಡಿಯ label.json (\"corporation\") ನಿಂದ ಬರುತ್ತದೆ; ಇಲ್ಲದಿದ್ದರೆ ನಿಗದಿಪಡಿಸಿಲ್ಲ.",
    "loc_gmaps": "Google Maps ನಲ್ಲಿ ತೆರೆಯಿರಿ",
    "tab_roadmap": "ವೇದಿಕೆಯ ಮುಂದಿನ ಯೋಜನೆ", "rm_title": "ದೂರಿನಿಂದ ದೃಢಪಟ್ಟ ಮುಕ್ತಾಯದವರೆಗೆ",
    "rm_intake": "ದೂರು ಬರುವ ಮಾರ್ಗಗಳು", "rm_verify": "ನಿಜ ಪರಿಶೀಲನೆ", "rm_outputs": "ಫಲಿತಾಂಶಗಳು",
    "rm_app": "ಮೊಬೈಲ್ ಆ್ಯಪ್ ಅಪ್‌ಲೋಡ್", "rm_whatsapp": "WhatsApp", "rm_1533": "1533 ಕರೆ ಕೇಂದ್ರ ಸಿಬ್ಬಂದಿ ಅಪ್‌ಲೋಡ್",
    "rm_web": "ವೆಬ್ ಅಪ್‌ಲೋಡ್ (ಈ ಡೆಮೊ)", "rm_gates": "ಹಂತ 1 ಒಂದೇ ಸ್ಥಳ + ಹಂತ 2 ನಿಜವಾದ ಹೊಸ ಫೋಟೋ", "rm_measure": "ಉಳಿದ ಸಮಸ್ಯೆಯ ಅಳತೆ",
    "rm_citizen": "ಧ್ವನಿಯೊಂದಿಗೆ ಕನ್ನಡ / ಇಂಗ್ಲಿಷ್ ನಾಗರಿಕ ಸಂದೇಶ", "rm_officer": "ಅಧಿಕಾರಿಯ ಮರುಪರಿಶೀಲನೆ ಪಟ್ಟಿ",
    "rm_auditor": "ಲೆಕ್ಕಪರಿಶೋಧಕರ ವಾರ್ಡ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "rm_built": "ನಿರ್ಮಿಸಲಾಗಿದೆ", "rm_planned": "ಯೋಜಿತ",
    "rm_honest": "ಕರೆ ಮತ್ತು WhatsApp ಮೂಲಕ ದೂರು ಸ್ವೀಕಾರ ಯೋಜಿತ ಸಂಯೋಜನೆಗಳು, ಇನ್ನೂ ನಿರ್ಮಿಸಿಲ್ಲ.",
})

LANGS = {"EN": EN, "ಕನ್ನಡ": KN, "KN": KN}


def is_kn(lang):
    return lang in ("ಕನ್ನಡ", "KN")


def t(key, lang="EN", **fmt):
    text = LANGS.get(lang or "EN", EN).get(key) or EN.get(key, key)
    return text.format(**fmt) if fmt else text


def verdict_label(verdict, lang="EN"):
    return t(f"v_{verdict}", lang)


# Gate / measure reasons: Kannada pattern for each English reason the pipeline writes (numbers kept); unknown text stays English
REASON_KN = [
    (r"GPS says photos are (\d+) m apart \(limit (\d+) m\)", "GPS ಪ್ರಕಾರ ಫೋಟೋಗಳು {0} ಮೀ ದೂರದಲ್ಲಿವೆ (ಮಿತಿ {1} ಮೀ)"),
    (r"compass headings differ by (\d+) deg", "ದಿಕ್ಸೂಚಿ ದಿಕ್ಕು {0} ಡಿಗ್ರಿ ಬೇರೆಯಾಗಿದೆ"),
    (r"too few visual features", "ಹೋಲಿಸಲು ಸಾಕಷ್ಟು ಚಿತ್ರ ಬಿಂದುಗಳಿಲ್ಲ"),
    (r"only (\d+) feature matches \(need (\d+)\)", "ಕೇವಲ {0} ಬಿಂದುಗಳು ಹೊಂದಿವೆ ({1} ಬೇಕು); ಬೇರೆ ಸ್ಥಳ ಇರಬಹುದು"),
    (r"could not fit a homography", "ಎರಡು ಫೋಟೋಗಳನ್ನು ಹೊಂದಿಸಲು ಆಗಲಿಲ್ಲ"),
    (r"geometric transform is implausible \(scale factor ([\d.]+)\)", "ಫೋಟೋಗಳ ಹೊಂದಾಣಿಕೆ ಅಸಹಜವಾಗಿದೆ (ಗಾತ್ರ ಅನುಪಾತ {0})"),
    (r"weak visual match: (\d+) inliers, (\d+)% ratio", "ಹೊಂದಾಣಿಕೆ ದುರ್ಬಲವಾಗಿದೆ: {0} ಬಿಂದುಗಳು, {1}%"),
    (r"reused photo: after is the before photo again \(pHash distance (\d+)",
     "ಹಳೆಯ ಫೋಟೋ ಮರುಬಳಕೆ: ನಂತರದ ಫೋಟೋ ಮೊದಲ ಫೋಟೋವೇ ಆಗಿದೆ (pHash ಅಂತರ {0})"),
    (r"reused photo: after matches an earlier photo (\S+) \(pHash distance (\d+)\)",
     "ಹಳೆಯ ಫೋಟೋ ಮರುಬಳಕೆ: ಹಿಂದಿನ ಫೋಟೋ {0} ಗೆ ಹೊಂದುತ್ತದೆ (pHash ಅಂತರ {1})"),
    (r"after photo \((.+?)\) is not later than before photo \((.+?)\)", "ನಂತರದ ಫೋಟೋ ({0}) ಮೊದಲ ಫೋಟೋಕ್ಕಿಂತ ({1}) ನಂತರ ತೆಗೆದಿಲ್ಲ"),
    (r"looks like a photo of a screen \(moire peak ([\d.]+)", "ಇದು ಪರದೆಯ ಫೋಟೋದಂತೆ ಕಾಣುತ್ತದೆ (ಮೊಯಿರೆ ಗುರುತು {0}; ಅಂದಾಜು ನಿಯಮ)"),
    (r"not a reused photo \(pHash distance (\d+)\)", "ಮರುಬಳಕೆ ಫೋಟೋ ಅಲ್ಲ (pHash ಅಂತರ {0}); ಪರದೆಯ ಗುರುತು ಇಲ್ಲ"),
    (r"same place: .*?(\d+) RANSAC inliers \((\d+)% of matches\)", "ಒಂದೇ ಸ್ಥಳ: {0} ಹೊಂದುವ ಬಿಂದುಗಳು (ಹೊಂದಾಣಿಕೆಗಳ {1}%)"),
    (r"no defect found inside the manual box", "ಕೈಯಾರೆ ಪೆಟ್ಟಿಗೆಯೊಳಗೆ ಸಮಸ್ಯೆ ಪತ್ತೆಯಾಗಲಿಲ್ಲ"),
    (r"no defect found in the before photo", "ಮೊದಲ ಫೋಟೋದಲ್ಲಿ ಸಮಸ್ಯೆ ಪತ್ತೆಯಾಗಲಿಲ್ಲ (ಕೈಯಾರೆ ಪೆಟ್ಟಿಗೆ ಪ್ರಯತ್ನಿಸಿ)"),
    (r"skipped: a gate failed", "ಬಿಡಲಾಗಿದೆ: ಒಂದು ಪರಿಶೀಲನೆ ವಿಫಲವಾಯಿತು"),
    (r"auto: largest blob", "ಸ್ವಯಂ ಪತ್ತೆ: ದೊಡ್ಡ ಸಮಸ್ಯೆ ಭಾಗ"),
    (r"manual ROI box", "ಕೈಯಾರೆ ಪೆಟ್ಟಿಗೆ"),
]
REASON_KN.append((r"box-based look-alike measure", "ಪೆಟ್ಟಿಗೆ ಆಧಾರಿತ ಹೋಲಿಕೆ ಅಳತೆ (ಪೆಟ್ಟಿಗೆ ಮತ್ತು ಸುತ್ತಲಿನ ರಸ್ತೆ)"))
GPS_KN = (r"GPS (\d+) m apart", "GPS ಪ್ರಕಾರ {0} ಮೀ ದೂರ")
TIME_MISSING_KN = "EXIF ಸಮಯ ಇಲ್ಲ, ಸಮಯ ಕ್ರಮ ಪರಿಶೀಲಿಸಿಲ್ಲ"


def reason_text(reason, lang="EN"):
    """The pipeline's English reason, or its Kannada version when one of the known patterns matches."""
    if not reason or not is_kn(lang):
        return reason
    for pattern, kn in REASON_KN:
        m = re.search(pattern, reason)
        if m:
            text = kn.format(*m.groups())
            g = re.search(GPS_KN[0], reason)
            if g and "GPS ಪ್ರಕಾರ" not in text:
                text += "; " + GPS_KN[1].format(*g.groups())
            if "EXIF time missing" in reason:
                text += "; " + TIME_MISSING_KN
            return text
    return reason


def note_kn(verdict, score, checks):
    """Kannada version of the fixed template note (same facts as narrate.template_note)."""
    g1, g2, m = checks["gate1"], checks["gate2"], checks["measure"]
    if verdict == "Cannot verify":
        failed = g1 if not g1["passed"] else g2
        why = reason_text(failed["reason"] if not failed["passed"] else m.get("method", ""), "KN")
        return {"officer": f"ಈ ದುರಸ್ತಿಯನ್ನು ಪರಿಶೀಲಿಸಲು ಆಗಲಿಲ್ಲ: {why}. ಸ್ಥಳಕ್ಕೆ ಹೋಗಿ ಮರುಪರಿಶೀಲನೆ ಮಾಡಿ.",
                "citizen": "ಫೋಟೋಗಳಿಂದ ಈ ದುರಸ್ತಿಯನ್ನು ದೃಢಪಡಿಸಲು ಆಗಲಿಲ್ಲ. ಇದನ್ನು ಮರುಪರಿಶೀಲನೆಗೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
                "source": "template"}
    kind = t(m.get("defect_type") or "pothole", "KN")
    officer = (f"ತೀರ್ಮಾನ: {verdict_label(verdict, 'KN')} (ಅಂಕ {score:.2f}). ಮೂಲ {kind} ಪ್ರದೇಶದ "
               f"{m['residual_area_pct']}% ಇನ್ನೂ ಉಳಿದಿದೆ ({g1['inliers']} ಹೊಂದುವ ಬಿಂದುಗಳು).")
    citizen = {
        "Verified": "ಫೋಟೋಗಳ ಪ್ರಕಾರ ದುರಸ್ತಿ ಆಗಿದೆ. ದೂರು ನೀಡಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು.",
        "Partial": "ಫೋಟೋಗಳ ಪ್ರಕಾರ ದುರಸ್ತಿ ಅರ್ಧ ಮಾತ್ರ ಆಗಿದೆ. ಉಳಿದ ಕೆಲಸಕ್ಕಾಗಿ ಮತ್ತೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
        "Not fixed": "ಫೋಟೋಗಳ ಪ್ರಕಾರ ಸಮಸ್ಯೆ ಇನ್ನೂ ಹಾಗೇ ಇದೆ. ದುರಸ್ತಿಗಾಗಿ ಮತ್ತೆ ಕಳುಹಿಸಲಾಗಿದೆ.",
    }[verdict]
    return {"officer": officer, "citizen": citizen, "source": "template"}
