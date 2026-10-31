# Nija - Proof of Fix

**Team Micro Might, RV University.** Nija is an offline before/after photo verifier for civic repairs (potholes, garbage).

Bengaluru residents report potholes and garbage, and complaints get marked "resolved", but nobody can check at scale that the repair is real.
Nija checks each closure from the complaint photo and the "fixed" photo. It flags incomplete or fake closures and ranks them for re-inspection.

Nija is a **verification layer, not "ask an AI if it looks fixed"**. Computer-vision gates and measurements decide the verdict.
Gemma 4 (`gemma4:e2b`, running locally through Ollama) only turns the measured numbers into an officer note and a citizen message.

## How it works
```
 before.jpg ─┐
 after.jpg  ─┴─► GATE 1  same place? ──────────── EXIF GPS distance (<= 40 m) + compass, then
                 │                                ORB features -> ratio test -> RANSAC homography (>= 25 inliers)
                 │ fail ─────────────────────────────────────────────────────────────┐
                 ▼                                                                   │
                 GATE 2  real & fresh photo? ──── pHash vs before photo (+ alignment check: copy or retake?)
                 │                                pHash vs every photo in data/pairs (reused from another case)
                 │                                EXIF time order, screen-recapture heuristic (FFT moire + banding)
                 │ fail ─────────────────────────────────────────────────────────────┤
                 ▼                                                                   │
                 MEASURE  warp before onto after (homography from Gate 1)            │
                 │        defect = largest dark+rough blob (pothole) / colour-texture  │
                 │        clutter (garbage), or a manual box                         │
                 │        residual = defect pixels left / defect pixels before        │
                 │        + edge-density change, seam cue                            │
                 ▼                                                                   ▼
                 SCORE = clip(1 - (0.8 x residual + 0.2 x edge_ratio), 0, 1)     "Cannot verify"
                 ▼                                                                (never a guess)
                 VERDICT  >= 0.80 Verified | >= 0.40 Partial | else Not fixed
                 ▼
                 NOTE  Gemma 4 e2b writes officer + citizen text from the numbers only
                       (temperature 0, JSON; any invented number -> template fallback)
                 ▼
                 RE-INSPECTION QUEUE  Not fixed > Partial > Cannot verify > Verified
```
All thresholds live in [nija/config.py](nija/config.py). Everything runs on one laptop: no cloud, no paid APIs.

## Quick start (Windows PowerShell)
You need Python 3.12 and [Ollama](https://ollama.com). Pull the model once (about 4.6 GB): `ollama pull gemma4:e2b`

Always run from inside the repo folder, using the venv's Python (the system Python has no OpenCV):
```powershell
cd "C:\Users\<you>\Documents\Micro_Might\T16-Micro-Might"
python -m venv .venv                                             # first time only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # first time only
.\.venv\Scripts\python.exe smoke_test.py                         # expect: => Verified  score=0.998
.\.venv\Scripts\python.exe -m streamlit run app.py               # opens http://localhost:8501
```
Without Ollama, everything still works: notes fall back to a fixed template (shown as "Written by: fixed template").

## The app
English and Kannada (toggle in the header), works on phones (390 px) and desktop. Fonts are bundled in `static/fonts`
(Plus Jakarta Sans, Inter, Noto Sans Kannada, all SIL Open Font Licence), so nothing loads from the internet.

| Tab | What it does |
|---|---|
| **Verify** | Upload a before and an after photo, then press Verify. What you see depends on the role (below). |
| **Geometry lab** | Seven live steps that show what changed: keypoints, matches, homography box, before/after slider, difference heatmap, defect contours, residual bars, plus plain-language bullets built from the real numbers. |
| **Try to fool Nija** | One-click attacks (old photo reused, photo of a screen, different place) plus free upload. Shows which gate caught the attack and why. |
| **Re-inspection queue** | Every pair in `data/pairs`, ranked most doubtful first, with verdict/type filters, citizen 🚩 flags, CSV export and (auditor) a per-pair evidence pack. |
| **Why Karnataka** | Complaint journey today vs with Nija, sourced fact cards ("as reported by ..."), where Nija fits, and what Nija does not prove. |

| Role (header) | Verify result shows |
|---|---|
| **Citizen** | Big verdict, the citizen message in the chosen language, a Listen button (browser speech, kn-IN / en-IN), Share on WhatsApp, and "Still not fixed? Tell us" (saved to `data/feedback.json`, shown as a flag in the queue). |
| **Officer** | Gemma note, geometry at a glance, location card (EXIF GPS, distance, Gate 1 reason, map when online), all checks, and a retake guide (faded before photo plus 3 tips). For Cannot verify, the reason comes first. |
| **Auditor** | Metrics, location card, evidence pack ZIP (photos, overlays, result JSON with `context`, timestamp), checks and the full JSON. |

Sidebar settings: pothole/garbage, Gemma notes on/off, a manual defect box (4 sliders), and the GBA corporation / ward
(entered by the officer, **not verified**). These go into an extra `"context"` key of the result JSON, never into `checks`.
Kannada citizen messages use a Kannada template; "Translate with Gemma" shows Gemma's Kannada only if every number in it matches the measurements.
Kannada text is machine drafted: have a Kannada speaker review it before real use.

`samples/` holds **SYNTHETIC** drawn images (road + pothole) so the demo runs before real photos exist. They are not real data.

## Contract
`nija.verify(before_path, after_path, roi=None, defect_type=None, use_gemma=True)` returns:
```
{"verdict": "Verified|Partial|Not fixed|Cannot verify", "score": 0..1 or None,
 "checks": {"gate1": {"passed", "reason", "gps_distance_m", "inliers", "inlier_ratio", ...},
            "gate2": {"passed", "reason", "dup_hash_distance", "time_ok", "screen_suspect", ...},
            "measure": {"residual_area_pct", "before_defect_px", "after_defect_px", "relief_change", ...}},
 "note": {"officer", "citizen", "source": "gemma|template"},
 "timings_ms": {"load", "gate1", "gate2", "measure", "narrate", "total"}}
```
`roi` = (x, y, w, h) as fractions 0..1 of the after photo. `relief_change` is always `None`, because depth is not measured.

## Files (2 lines each)
| File | What it does |
|---|---|
| `app.py` | Streamlit UI with Verify, Try to fool Nija and Re-inspection queue tabs. Caches results, warms up Gemma at start, and never shows a stack trace. |
| `smoke_test.py` | Runs `verify()` on one pair from the command line and prints the contract JSON. With no arguments it uses the synthetic sample pair. |
| `nija/config.py` | Every threshold lives here (GPS limit, inliers, pHash limit, segmentation, verdict cut-offs). Tune numbers here, never inside modules. |
| `nija/pipeline.py` | `verify()`, the single entry point: runs gate1, gate2, measure, verdict, narrate. Times each stage into `timings_ms`. |
| `nija/images.py` | Loads a photo, fixes phone rotation from EXIF, downsizes to 1280 px. All modules use the same pixels. |
| `nija/exif.py` | Reads capture time, GPS and compass heading from EXIF, plus haversine distance. Missing data is `None` (unknown), never a fail. |
| `nija/gate1.py` | Same place: GPS/compass when present, then ORB matching + RANSAC homography. The homography is reused to align the photos, and it draws the debug match image. |
| `nija/gate2.py` | Real and fresh: pHash catches reused photos (the before photo, resized copies, any photo in `data/pairs`), and EXIF time must move forward. A screen HEURISTIC (FFT moire + banding) flags photos of a monitor. |
| `nija/measure.py` | Warps before into the after frame, finds the defect (dark+rough blob / garbage clutter / manual box) and counts how much is still there. Also reports edge-density change and a seam cue. |
| `nija/verdict.py` | Turns checks into a score and one of 4 verdicts. A failed gate gives Cannot verify with no score. |
| `nija/narrate.py` | Gemma 4 (`gemma4:e2b`, local, text only, temperature 0) writes the officer note and citizen message from the numbers. Falls back to a template if Ollama is down or slow, or if Gemma invents a number. |
| `nija/ui.py` | Design system: bundled fonts, Karnataka palette (teal, saffron, red, cream), cards, 44 px tap targets, mobile layout. Helpers like `hero()` and `verdict_badge()`. |
| `nija/visuals.py` | Geometry Lab pictures (keypoints, homography box, slider, heatmap, contours, residual bars) and bullets, all from `verify(debug=True)` intermediates. |
| `nija/i18n.py` | English and Kannada text, verdict labels, Kannada versions of gate reasons and template notes, and the sourced fact cards. |
| `nija/evidence.py` | Location context from EXIF, the evidence pack ZIP, citizen feedback storage and the browser Listen button. |
| `nija/reinspect.py` | Runs `verify()` on every pair in `data/pairs` and ranks them Not fixed > Partial > Cannot verify > Verified. Feeds the queue tab. |
| `eval/make_fakes.py` | Builds SYNTHETIC fake closures from your real pairs (reused photo, photo of a screen, different place) into `data/pairs_fake/`. |
| `eval/run_eval.py` | Confusion matrix, precision/recall at catching bad closures, a Gemma-only yes/no baseline and seconds per pair. Writes `eval/results.md` + `.csv`. |
| `eval/screen_score.py` | Prints screen-recapture scores for any photos, to calibrate the screen thresholds in `config.py`. |
| `.streamlit/config.toml` | Turns off Streamlit usage stats so the demo is fully offline. Raises the upload limit to 50 MB for phone photos. |
| `DEMO.md` | 7-minute demo script and likely judge questions with honest answers. |

## Data shoot checklist (target: 40 pairs)
- **12 fixed, 8 partial, 8 not fixed** real pairs. Fakes are generated by `eval/make_fakes.py` and labelled synthetic.
- Layout: `data/pairs/<id>/before.jpg`, `after.jpg`, `label.json` (e.g. `data/pairs/p01/`).
- `label.json`: `{"label": "fixed|partial|not_fixed", "type": "pothole|garbage", "note": ""}`
- Shooting protocol:
  - [ ] Same spot, phone at about **1.5 m height**, **same angle**, **2-3 m** from the defect
  - [ ] Put the defect near the centre of the frame
  - [ ] Include road edges, kerbs, poles or walls in frame (Gate 1 matches on these)
  - [ ] Keep location and EXIF ON in the camera app
  - [ ] Copy photos by USB/cable or Google Drive original files. **No WhatsApp forwarding** (it strips EXIF and recompresses)
  - [ ] Staged garbage clear-ups (litter before, cleaned after, some left for partial) are fine. Write `"staged"` in `note`, honestly
- Photos in `data/pairs/` are git-ignored by default. Remove that rule in `.gitignore` if the team wants to commit them.

## Reproduce the evaluation
```powershell
.\.venv\Scripts\python.exe eval/make_fakes.py    # synthetic fakes from data/pairs -> data/pairs_fake
.\.venv\Scripts\python.exe eval/run_eval.py      # writes eval/results.md + eval/results.csv (add --no-baseline to skip Gemma)
```
The Gemma baseline takes about 4-6 s per pair the first time. Answers are cached in `eval/results_cache/`, so reruns take seconds.

## Honest limitations
- **Small, self-made test set** (about 40 pairs shot by us, plus synthetic fakes). The numbers show the method works; they are not a benchmark.
- **Heuristics, not trained models.** Defect segmentation (darker + rough for potholes, colour/texture clutter for garbage) and the screen check (FFT moire) are hand-tuned rules. Auto-detect can pick the wrong blob (use the manual box), and a very dark fresh patch can look like a remaining pothole.
- **Garbage is weaker than potholes.** Clutter detection is crude, and staged clean-ups are easier than real streets.
- **Depth is not measured.** `relief_change` is empty. If added, monocular depth would be *relative*, never metric.
- **Gate 1 needs a similar viewpoint.** Photos taken from very different angles or distances fail as "Cannot verify". That is safe, but it costs re-inspections.
- **EXIF can be missing or faked.** Missing time/GPS is a warning, not a fail, and EXIF alone proves nothing. That's why the visual gates exist.
