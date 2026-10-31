# Nija: 7-minute demo script (v2: Geometry lab, Kannada, roles)

**Before you start:**
- Open the app (`.\.venv\Scripts\python.exe -m streamlit run app.py`), role **Officer**, language **EN**.
- Press Verify once on the sample pair, so Gemma is warm.
- Have `eval/results.md` open in a second tab.
- If you want the Listen demo in Kannada, check Windows has a Kannada voice. Otherwise it says so and reads in English.

| Part | Time | What to show |
|---|---|---|
| Problem | 45 s | Hero banner, then the **Why Karnataka** journey row (Close is the weak step) |
| Live geometry | 2 min | **Geometry lab**, half-fixed sample: 7 stages, drag the slider, read the bullets |
| Fool Nija | 1 min | Three attack buttons, each caught with a reason |
| Kannada + voice | 45 s | Switch to ಕನ್ನಡ, Citizen role, Listen, Translate with Gemma, WhatsApp |
| Evaluation | 60 s | Numbers from `eval/results.md` only |
| Why Karnataka | 60 s | Fact cards with sources, where Nija fits, limits card |

**Photoreal pairs (synthetic AI images):** in **Geometry lab** pick `p02 (partial, synthetic AI photos, box)` or `p01`. The box measure compares the tapped defect box with the road around it. Say plainly: "these are AI-generated test photos; fully fixed pairs score Partial here, an honest limit."

### Problem (45 s)
- "In Bengaluru a pothole complaint gets marked *resolved*. Nobody checks the closure photo at scale."
- Open **Why Karnataka**: "Every complaint goes Report, Assign, Repair, **Close**. Close is where a ticket can be marked resolved with no photo, or a photo nobody checks."
- "We built **Nija** (Kannada for *truth*): it checks the closure photo before the complaint is closed."

### Live geometry (2 min)
- **Geometry lab**, keep "Sample: half fixed", press **Run the geometry lab**. Narrate as the stages appear:
  - "Keypoints, then matches. Green lines agree on one camera transform, which proves it is the same place."
  - "This yellow box is where the old photo's frame lands. Nija says in words how the camera moved."
  - Drag the **slider**: "Before and after, lined up."
  - "The heatmap shows what changed. The contours show the defect then (green) and what is left (red)."
- Read the bullet "Defect area went from 92,267 px to 50,784 px (45% smaller)". Then: "So the verdict is **Partial**, from a measurement, not an AI opinion."

### Fool Nija (1 min)
- **Try to fool Nija**: click the three attacks. Reused photo is caught by Gate 2, the screen photo by both gates, the different place by Gate 1.
- Invite a judge to upload anything.

### Kannada and voice (45 s)
- Switch to **ಕನ್ನಡ** and role **Citizen**, then open **Verify** with the partial pair. The verdict reads **ಭಾಗಶಃ ದುರಸ್ತಿ**.
- Press **ಕೇಳಿ (Listen)**, then **Translate with Gemma**. "Gemma's Kannada is shown only if every number matches our measurement."
- Show the WhatsApp share button and "Still not fixed? Tell us". The flag then appears in the auditor queue.

### Evaluation (60 s): see section 4 below.
### Why Karnataka (60 s)
- Read 2 or 3 fact cards and say "as reported by" plus the outlet.
- Show **Where Nija fits** (between Sahaaya / 1533 / Rasthe Gundi Gamana and the people who use the result).
- End on the **Limits** card: no claims about quality, durability or depth.

---

## Older script (v1), kept for reference

## 2. Architecture (60 s)
Show the diagram in the README.
- "Two gates first. **Gate 1, same place:** GPS when present, then feature matching with a RANSAC homography. **Gate 2, real and fresh photo:** perceptual-hash reuse checks against the before photo and every earlier case, EXIF time order, and a screen-moire check."
- "Fail either gate and the answer is **Cannot verify**. We never guess."
- "Then we align the photos, segment the defect and **measure how much is left**. The score and verdict come from that number: Verified, Partial or Not fixed."
- "**Gemma 4 runs locally** and only writes the officer note and citizen message from those numbers. If it ever writes a number we didn't measure, we throw its text away and use a template. Gemma never decides."

## 3. Live demo (3 min)
1. **Verify tab, genuine repair** (40 s): upload `synthetic_before.jpg` and `synthetic_after_fixed.jpg`. Show the green **Verified** badge, the overlays, ✅ on both gates, the Gate 1 match lines, and the Gemma note. Say: "the photos are drawn test images; our real photo pairs are in the evaluation."
2. **Half-done repair** (30 s): switch the after photo to `synthetic_after_partial.jpg`. You get yellow **Partial**, with red showing the part still broken. "This is the closure that usually slips through."
3. **Try to fool Nija tab** (80 s): click the three attacks one by one.
   - *Old photo reused*: caught by Gate 2 ("reused photo... aligned pixel difference ~0").
   - *Photo of a screen*: caught (moire peak far above a normal photo).
   - *Different place*: caught by Gate 1 (too few matching features).
   - Invite a judge: "Upload anything you like and try to get a fake past it."
4. **Re-inspection queue** (30 s): "Every closure gets ranked. Officers start at the top: Not fixed, then Partial, then Cannot verify."

## 4. Evaluation (60 s)
Read the numbers from `eval/results.md`. Never quote numbers you didn't produce.
- "On **N** pairs (our own photos plus synthetic fakes), Nija catches **X%** of bad closures at **Y%** precision, in about 0.3 s per pair."
- "Baseline: we asked Gemma 4 alone, with both photos, 'was this repair completed?' *Quote its precision/recall and how many genuinely fixed repairs it confirmed.*"
- "Nija gives a reason and a measurement for every verdict, and it says *Cannot verify* instead of guessing."

## 5. Impact and next steps (45 s)
- "Runs offline on a laptop, so it can run inside a ward office with no cloud cost and no citizen photos leaving the building."
- "It plugs into existing complaint apps: every 'resolved' click gets a Nija check, and doubtful ones go to the queue."
- "Next: a trained defect segmenter, relative depth to measure pothole relief, and a larger labelled dataset from real complaints."

---

## Likely judge questions (honest answers)

**1. Why not just ask a vision model if it's fixed?**
We measured that baseline in `eval/results.md`. A VLM gives one opinion with no reason you can audit, and it can't tell "same photo re-sent" from "real retake". Our gates check provenance and our measurement gives a number an officer can contest. In our test run, Gemma alone said "no" to almost everything, including genuinely fixed repairs.

**2. What do you actually use Gemma 4 for?**
It writes the officer note and the citizen message from our measured numbers, locally, at temperature 0, as JSON. We check that every number it writes appears in our measurements. Otherwise we use a template. It never decides the verdict.

**3. How accurate is it?**
The numbers in `eval/results.md` come from about 40 pairs we shot ourselves plus synthetic fakes. That's enough to show the method works, but it's not a benchmark. We'd need a few hundred real complaint pairs to claim an accuracy figure.

**4. Can it be fooled?**
Yes. Every check is a heuristic. Someone could shoot a different pothole that looks similar from the same angle, or use a high-quality screen without moire. Gate 1 plus GPS plus time order makes it much harder, and anything doubtful becomes "Cannot verify" for a human to check.

**5. What if the after photo is taken from a different angle?**
Gate 1 handles moderate changes (the homography absorbs perspective). Very different viewpoints fail as "Cannot verify". That's a safe failure, but it means more re-inspections. In practice the app would guide the worker to match the original framing.

**6. Do you measure pothole depth?**
No. We only measure the remaining defect area plus edge/seam cues. Depth from one photo would be *relative*, not metric, and we left it as a stretch goal rather than show numbers we can't stand behind.

**7. Does it work on garbage?**
Partly. Garbage uses colour/texture clutter, which is weaker than pothole detection, and our garbage pairs include staged clean-ups that are labelled as staged. We say so in the limitations.

**8. How would a city deploy this?**
It needs no GPU or internet: Python + OpenCV + a 4.6 GB local model, under 10 s per check. It sits behind the "mark resolved" button of the existing complaint system. Fixed verdicts close automatically, and everything else goes to the ranked re-inspection queue.
