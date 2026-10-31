# ROI change mode results

**AI-generated pairs, 6 used for tuning, 1 held out, not real-world accuracy.**

Source: `Downloads/nija_gen9` (img2 is a duplicate of img1 and is not used). Boxes are x, y, w, h as fractions of the after photo.
Run with `use_gemma=False` and an empty known-photo store, so only the two gates and the measure decide.
A reversed pair (after used as before) must never come out Verified.

| pair | type | box | expected | got | score | right |
|---|---|---|---|---|---|---|
| img3 -> img1 | garbage | [0.2, 0.36, 0.55, 0.4] | Verified | Verified | 0.533 | yes |
| img6 -> img8 | pothole | [0.34, 0.55, 0.38, 0.24] | Verified | Verified | 0.688 | yes |
| img6 -> img7 | pothole | [0.34, 0.55, 0.38, 0.24] | Partial | Partial | 0.337 | yes |
| img6 -> img9 | pothole | [0.34, 0.55, 0.38, 0.24] | Not fixed | Not fixed | 0.0 | yes |
| img4 -> img5 | pothole | [0.23, 0.55, 0.33, 0.22] | Not fixed | Not fixed | 0.209 | yes |
| img10 -> img11 | pothole | [0.25, 0.55, 0.5, 0.3] | Verified | Verified | 1.0 | yes |
| REVERSED img1 -> img3 | garbage | [0.2, 0.36, 0.55, 0.4] | not Verified | Not fixed | 0.0 | yes |
| REVERSED img8 -> img6 | pothole | [0.34, 0.55, 0.38, 0.24] | not Verified | Not fixed | 0.0 | yes |
| REVERSED img7 -> img6 | pothole | [0.34, 0.55, 0.38, 0.24] | not Verified | Not fixed | 0.0 | yes |
| REVERSED img9 -> img6 | pothole | [0.34, 0.55, 0.38, 0.24] | not Verified | Not fixed | 0.033 | yes |
| REVERSED img5 -> img4 | pothole | [0.23, 0.55, 0.33, 0.22] | not Verified | Not fixed | 0.197 | yes |
| REVERSED img11 -> img10 | pothole | [0.25, 0.55, 0.5, 0.3] | not Verified | Not fixed | 0.0 | yes |
| img10 -> img11 loose box | pothole | [0.2, 0.45, 0.62, 0.45] | Verified | Verified | 0.479 | yes |
| img10 -> img11 tight box | pothole | [0.3, 0.58, 0.4, 0.22] | Verified | Verified | 1.0 | yes |

Fix for the tight box: when the box is mostly defect, or the defect cannot be separated from the road, the box is grown by 20% (`ROI_BOX_GROW`) and measured again. Thresholds (`ROI_T_VERIFIED` 0.45, `ROI_T_PARTIAL` 0.30) were not changed.
