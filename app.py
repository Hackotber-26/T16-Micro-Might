"""Streamlit UI for Nija: "Verify" tab (upload before + after, see verdict, score, checks and Gemma note) and
"Re-inspection queue" tab (all pairs in data/pairs ranked most doubtful first). Run with: python -m streamlit run app.py"""

import tempfile
import threading
from pathlib import Path

import streamlit as st

from nija import config, verify
from nija.narrate import warm_up
from nija.reinspect import build_queue, list_pairs

BADGE_COLOURS = {"Verified": "#1e8e3e", "Partial": "#f9a825", "Not fixed": "#d93025", "Cannot verify": "#5f6368"}

st.set_page_config(page_title="Nija - Proof of Fix", layout="wide")


@st.cache_resource
def start_gemma_warm_up():
    # Load gemma4:e2b into memory in the background once per server, so the first note is fast
    t = threading.Thread(target=warm_up, daemon=True)
    t.start()
    return t


@st.cache_data(show_spinner=False)
def cached_queue(signature):
    return build_queue()


def save_upload(upload, folder):
    # Keep the original bytes so EXIF (time, GPS) survives; own subfolder in case both files share a name
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / upload.name
    path.write_bytes(upload.getvalue())
    return path


def badge(verdict):
    st.markdown(
        f"<div style='display:inline-block;padding:10px 22px;border-radius:8px;color:white;font-size:28px;"
        f"font-weight:700;background:{BADGE_COLOURS[verdict]}'>{verdict}</div>",
        unsafe_allow_html=True,
    )


def show_result(result, images):
    verdict, score = result["verdict"], result["score"]
    badge(verdict)
    m1, m2, m3 = st.columns(3)
    m1.metric("Fix score", "n/a" if score is None else f"{score:.2f}")
    residual = result["checks"]["measure"]["residual_area_pct"]
    m2.metric("Residual area", "n/a" if residual is None else f"{residual}%")
    m3.metric("Time", f"{result['timings_ms']['total'] / 1000:.1f} s")

    note = result["note"]
    st.subheader("Note")
    st.write(f"**Officer:** {note['officer']}")
    st.write(f"**Citizen:** {note['citizen']}")
    source = "Gemma 4 (gemma4:e2b, local) from the measured numbers" if note["source"] == "gemma" \
        else "fixed template (Gemma unavailable, too slow, or used a number not in the measurements)"
    st.caption(f"Written by: {source}. The verdict is never decided by Gemma.")

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


start_gemma_warm_up()
st.title("Nija - Proof of Fix")
st.caption("Checks whether a civic repair was really done from before/after photos. Gates and measurements decide the verdict; "
           "Gemma 4 only writes the notes.")

with st.sidebar:
    st.header("Settings")
    defect_type = st.radio("Defect type", ["pothole", "garbage"], horizontal=True)
    use_gemma = st.checkbox("Write notes with Gemma 4 (local)", value=True)
    use_roi = st.checkbox("Manual defect box (overrides auto-detect)")
    roi = None
    if use_roi:
        st.caption("Box position in % of the AFTER photo")
        rx = st.slider("x (left)", 0, 95, 25)
        ry = st.slider("y (top)", 0, 95, 25)
        rw = st.slider("width", 5, 100 - rx, min(50, 100 - rx))
        rh = st.slider("height", 5, 100 - ry, min(50, 100 - ry))
        roi = (rx / 100, ry / 100, rw / 100, rh / 100)

tab_verify, tab_queue = st.tabs(["Verify", "Re-inspection queue"])

with tab_verify:
    col_b, col_a = st.columns(2)
    before_file = col_b.file_uploader("Before photo (complaint)", type=["jpg", "jpeg", "png", "webp"])
    after_file = col_a.file_uploader("After photo (claimed fix)", type=["jpg", "jpeg", "png", "webp"])
    if before_file:
        col_b.image(before_file, width="stretch")
    if after_file:
        col_a.image(after_file, width="stretch")

    if st.button("Verify", type="primary", disabled=not (before_file and after_file)):
        with st.spinner("Checking place, freshness and repair, then writing the note..."):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    b = save_upload(before_file, Path(tmp) / "before")
                    a = save_upload(after_file, Path(tmp) / "after")
                    result, images = verify(b, a, roi=roi, defect_type=defect_type, use_gemma=use_gemma, debug=True)
            except Exception as e:  # never show a stack trace in the demo
                st.error(f"Could not process these photos: {e}")
                st.stop()
        show_result(result, images)
        st.caption(
            "Honesty note: the defect is found with classical CV heuristics (darker + rough for potholes, colour/texture "
            "clutter for garbage), not a trained model. Use the manual box if auto-detect picks the wrong area. Depth is not measured yet."
        )

with tab_queue:
    pairs = list_pairs()
    st.write(f"Every pair in `data/pairs/<id>/` (before.jpg, after.jpg, label.json), ranked "
             f"{' > '.join(config.QUEUE_PRIORITY)}, lowest score first. Notes use the template here for speed.")
    if not pairs:
        st.info("No pairs yet. Add folders like data/pairs/p01/ with before.jpg, after.jpg and label.json.")
    else:
        signature = tuple((p.name, (p / "before.jpg").stat().st_mtime, (p / "after.jpg").stat().st_mtime) for p in pairs)
        if st.button("Refresh queue"):
            cached_queue.clear()
        with st.spinner(f"Verifying {len(pairs)} pairs..."):
            try:
                rows = cached_queue(signature)
            except Exception as e:
                st.error(f"Could not build the queue: {e}")
                rows = []
        if rows:
            counts = {v: sum(r["verdict"] == v for r in rows) for v in config.QUEUE_PRIORITY}
            cols = st.columns(len(counts))
            for col, (v, n) in zip(cols, counts.items()):
                col.metric(v, n)
            cols_order = ["priority", "pair", "verdict", "score", "residual_%", "why", "type", "label (ground truth)", "ms"]
            st.dataframe([{k: r[k] for k in cols_order} for r in rows], hide_index=True, width="stretch")
