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
