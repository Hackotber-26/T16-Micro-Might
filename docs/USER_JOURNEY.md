# Nija: users, journey and honest limits

## Personas

| Persona | Needs | What Nija gives them |
|---|---|---|
| **Citizen** (Kannada first; some Tamil, Telugu, Urdu speakers; many on phones and WhatsApp; some elderly or low-literacy) | Know if the reported problem was really fixed, in their language, without reading technical detail | Citizen view: a big verdict, a short message in Kannada or English, a Listen button, Share on WhatsApp, and "Still not fixed? Tell us" |
| **Ward engineer (AE / AEE)** | Close genuine work fast, and know why a closure was rejected and how to fix it | Officer view: Geometry at a glance, the reason for Cannot verify, the location card and a retake guide |
| **Commissioner / auditor** | Find doubtful closures across wards, with evidence | Auditor view: a ranked queue with filters, citizen flags, CSV export, and a per-pair evidence pack (photos, overlays, result JSON, timestamp) |
| **Court / journalist** | Independent, explainable evidence | The evidence pack ZIP, plain-language bullets and the Geometry lab steps, built only from measured numbers |

## Journey

| Step | Today | With Nija |
|---|---|---|
| Report | Citizen complains via Sahaaya, 1533 or another channel | Unchanged |
| Assign | Ticket goes to the ward engineer | Unchanged |
| Repair | Contractor works (or says they did) | Unchanged |
| **Close** | Ticket marked resolved; a closure photo may be optional and is rarely checked | **Nija compares before and after photos**: same place, fresh photo, how much defect is left. Verified closes; Partial, Not fixed and Cannot verify go to re-inspection |
| Reopen | Citizen has to complain again | "Still not fixed? Tell us" adds a flag to the queue |
| Audit | Manual, after the fact | Ranked queue and an evidence pack per pair |

## Honest limits
- **Heuristics, not trained models.** Gates and defect segmentation are classical computer vision rules. Auto-detect can pick the wrong area; the manual box exists for that.
- **Depth is not measured.** Nija says nothing about how deep a pothole was or is.
- **No proof of quality or durability.** A neat patch that fails next monsoon would still look fixed in the photo.
- **Small, self-made test set.** Evaluation uses pairs we shot plus synthetic fakes. That shows the method works; it is not a benchmark.
- **Viewpoint matters.** Very different angles give Cannot verify. That's safe, but it means more re-inspections.
- **EXIF and officer inputs can be wrong.** Missing GPS or time is a warning, not a fail. Corporation and ward are entered by the officer and not verified.
- **Kannada is machine drafted.** A Kannada speaker must review it before real use. Gemma's Kannada is shown only when every number matches the measurements.
- **Wording:** we say "no deployed system we found", never "first ever".
