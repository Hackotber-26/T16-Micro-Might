"""Streamlit UI for Nija: upload a before and an after photo, press Verify, see the verdict, score, per-check results and note.
Run with: python -m streamlit run app.py"""

import tempfile
from pathlib import Path

import streamlit as st

from nija import verify

BADGE_COLOURS = {"Verified": "#1e8e3e", "Partial": "#f9a825", "Not fixed": "#d93025", "Cannot verify": "#5f6368"}

st.set_page_config(page_title="Nija - Proof of Fix", layout="wide")
st.title("Nija - Proof of Fix")
st.caption("Checks whether a civic repair was really done from before/after photos. Gates and measurements decide the verdict.")


def save_upload(upload, folder):
    # Keep the original bytes so EXIF (time, GPS) survives; own subfolder in case both files share a name
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / upload.name
    path.write_bytes(upload.getvalue())
    return path


col_b, col_a = st.columns(2)
before_file = col_b.file_uploader("Before photo (complaint)", type=["jpg", "jpeg", "png", "webp"])
after_file = col_a.file_uploader("After photo (claimed fix)", type=["jpg", "jpeg", "png", "webp"])
if before_file:
    col_b.image(before_file, width="stretch")
if after_file:
    col_a.image(after_file, width="stretch")

with st.sidebar:
    st.header("Settings")
    defect_type = st.radio("Defect type", ["pothole", "garbage"], horizontal=True)
    use_roi = st.checkbox("Manual defect box (overrides auto-detect)")
    roi = None
    if use_roi:
        st.caption("Box position in % of the AFTER photo")
        rx = st.slider("x (left)", 0, 95, 25)
        ry = st.slider("y (top)", 0, 95, 25)
        rw = st.slider("width", 5, 100 - rx, min(50, 100 - rx))
        rh = st.slider("height", 5, 100 - ry, min(50, 100 - ry))
        roi = (rx / 100, ry / 100, rw / 100, rh / 100)

if st.button("Verify", type="primary", disabled=not (before_file and after_file)):
    with st.spinner("Checking place, freshness and repair..."):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                b = save_upload(before_file, Path(tmp) / "before")
                a = save_upload(after_file, Path(tmp) / "after")
                result, images = verify(b, a, roi=roi, defect_type=defect_type, debug=True)
        except Exception as e:  # never show a stack trace in the demo
            st.error(f"Could not process these photos: {e}")
            st.stop()

    verdict, score = result["verdict"], result["score"]
    st.markdown(
        f"<div style='display:inline-block;padding:10px 22px;border-radius:8px;color:white;font-size:28px;"
        f"font-weight:700;background:{BADGE_COLOURS[verdict]}'>{verdict}</div>",
        unsafe_allow_html=True,
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Fix score", "n/a" if score is None else f"{score:.2f}")
    residual = result["checks"]["measure"]["residual_area_pct"]
    m2.metric("Residual area", "n/a" if residual is None else f"{residual}%")
    m3.metric("Time", f"{result['timings_ms']['total'] / 1000:.1f} s")

    note = result["note"]
    st.subheader("Note")
    st.write(f"**Officer:** {note['officer']}")
    st.write(f"**Citizen:** {note['citizen']}")
    st.caption(f"Written by: {note['source']}")

    if "after_overlay" in images:
        c1, c2 = st.columns(2)
        c1.image(images["before_overlay"], width="stretch",
                 caption="Before, warped into the after frame: yellow = defect region, red = defect pixels")
        c2.image(images["after_overlay"], width="stretch", caption="After: red = defect pixels still detected")

    for name, label in (("gate1", "Gate 1 - same place"), ("gate2", "Gate 2 - real and fresh photo"), ("measure", "Measure - residual")):
        check = result["checks"][name]
        icon = "" if name == "measure" else ("✅ " if check["passed"] else "❌ ")
        with st.expander(f"{icon}{label}"):
            if "reason" in check:
                st.write(check["reason"])
            st.json(check)

    with st.expander("Gate 1 debug - feature matches"):
        if "gate1_matches" in images:
            g1 = result["checks"]["gate1"]
            st.image(images["gate1_matches"], width="stretch",
                     caption=f"Before (left) | After (right). Green = RANSAC inlier, red = rejected. "
                             f"{g1['inliers']} inliers / {g1['good_matches']} matches")
        else:
            st.write("No match image: too few features, or the GPS/compass check failed first.")

    with st.expander("Raw result (contract JSON)"):
        st.json(result)
    st.caption(
        "Honesty note: the defect is found with classical CV heuristics (darker + rough for potholes, colour/texture "
        "clutter for garbage), not a trained model. Use the manual box if auto-detect picks the wrong area. Depth is not measured yet."
    )
