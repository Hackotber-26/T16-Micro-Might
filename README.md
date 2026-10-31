# Nija - Proof of Fix

Nija checks whether a civic repair (pothole, garbage) was actually done, using a before photo and an after photo.
It's a **verification layer**, not "ask an AI if it looks fixed". Classical computer vision gates and measurements decide the verdict, and Gemma 4 (`gemma4:e2b`, local via Ollama) only writes the human-readable notes.

```
before.jpg + after.jpg
   -> Gate 1: same place?        (EXIF GPS/compass, ORB + RANSAC homography)
   -> Gate 2: real, fresh photo? (pHash reuse vs before + all data/pairs photos, EXIF time order, screen heuristic)
   -> align + measure residual   (Step 1: grey-level change placeholder; Step 4: defect segmentation)
   -> score -> Verified / Partial / Not fixed / Cannot verify
   -> note (template now; Gemma 4 from Step 5)
```
Failing Gate 1 or Gate 2 always gives **Cannot verify**. Nija never guesses.

## Install and run (Windows PowerShell)
Always run from inside the repo folder and use the venv's Python (the system Python has no OpenCV):
```powershell
cd "C:\Users\<you>\Documents\Micro_Might\T16-Micro-Might"
python -m venv .venv                                   # first time only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe smoke_test.py               # synthetic sample pair in samples/
.\.venv\Scripts\python.exe smoke_test.py data/pairs/p01/before.jpg data/pairs/p01/after.jpg
.\.venv\Scripts\python.exe -m streamlit run app.py
```
`samples/` holds a small SYNTHETIC pair (drawn road + pothole) so the demo runs before real photos exist. It is not real data.

## Contract
`nija.verify(before_path, after_path, roi=None)` returns:
```
{"verdict": "Verified|Partial|Not fixed|Cannot verify", "score": 0..1 or None,
 "checks": {"gate1": {"passed", "reason", "gps_distance_m", "inliers", "inlier_ratio"},
            "gate2": {"passed", "reason", "dup_hash_distance", "time_ok", "screen_suspect"},
            "measure": {"residual_area_pct", "before_defect_px", "after_defect_px", "relief_change"}},
 "note": {"officer", "citizen", "source": "gemma|template"},
 "timings_ms": {...}}
```

## Files (2 lines each)
| File | What it does |
|---|---|
| `app.py` | Streamlit UI: upload before/after, press Verify, see the verdict badge, score, per-check panels and note. Never shows a stack trace. |
| `smoke_test.py` | Runs `verify()` on one pair from the command line and prints the contract JSON. Use it to test without the UI. |
| `nija/config.py` | Every threshold lives here (GPS limit, inliers, pHash limit, verdict cut-offs). Tune numbers here, never inside modules. |
| `nija/pipeline.py` | `verify()`, the single entry point: runs gate1, gate2, measure, verdict, narrate. Times each stage into `timings_ms`. |
| `nija/images.py` | Loads a photo, fixes phone rotation from EXIF, downsizes to 1280 px. All modules use the same pixels. |
| `nija/exif.py` | Reads capture time, GPS and compass heading from EXIF, plus haversine distance. Missing data is `None` (unknown), never a fail. |
| `nija/gate1.py` | Same place: GPS/compass when present, then ORB matching + RANSAC homography. The homography is reused to align the photos. |
| `nija/gate2.py` | Real and fresh: pHash catches reused photos (vs before and every photo in `data/pairs`, cached in `data/known_hashes.json`), EXIF time must move forward. A screen HEURISTIC (FFT moire peaks + banding) flags photos of a monitor. |
| `nija/measure.py` | Aligns after onto before and measures how much of the defect region remains. Step 1 is an honest grey-level placeholder. |
| `nija/verdict.py` | Turns checks into a score and one of 4 verdicts. A failed gate gives Cannot verify with no score. |
| `nija/narrate.py` | Writes the officer note and citizen message from the numbers. Template now, Gemma 4 in Step 5; it never decides the verdict. |
| `eval/screen_score.py` | Prints the screen-recapture scores for any photos. Use it to calibrate the screen thresholds in config.py. |
| `eval/` | Evaluation scripts (Step 6): fake generation and metrics on `data/pairs`. |

## Data shoot checklist (target: 40 pairs)
- **12 fixed, 8 partial, 8 not fixed** real pairs. Fakes (reused photo, screen photo, different place) are generated later by `eval/make_fakes.py` and labelled synthetic.
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

## Honest limitations (so far)
- The Step 1 residual is a grey-level change heuristic, not segmentation.
- The screen-recapture check is a heuristic (FFT moire + banding), tuned on a simulated screen photo. Calibrate it on a real monitor photo.
- Depth is not measured. When added it will be relative, not metric.
