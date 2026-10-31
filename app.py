"""Streamlit UI for Nija. Tabs: Verify (upload before + after), Try to fool Nija (one-click attacks + free upload),
Re-inspection queue (all pairs in data/pairs ranked). Run with: python -m streamlit run app.py"""

import tempfile
import threading
from pathlib import Path

import streamlit as st

from nija import config, ui, verify
from nija.narrate import warm_up
from nija.reinspect import build_queue, list_pairs

SAMPLES = config.ROOT / "samples"
GATES = (("gate1", "Gate 1 - same place"), ("gate2", "Gate 2 - real and fresh photo"))
ATTACKS = {  # one-click attacks for the demo; all built from the SYNTHETIC sample pair
    "Old photo reused": ("synthetic_attack_reused.jpg", "The BEFORE photo itself, shrunk and re-saved, submitted as the 'after'."),
    "Photo of a screen": ("synthetic_attack_screen.jpg", "The real after photo re-photographed off a monitor (simulated moire)."),
    "Different place": ("synthetic_after_otherplace.jpg", "A clean-road photo taken somewhere else."),
}

st.set_page_config(page_title="Nija - Proof of Fix", page_icon="🛣️", layout="wide")
ui.inject_css()


@st.cache_resource
def start_gemma_warm_up():
    # Load gemma4:e2b into memory in the background once per server, so the first note is fast
    t = threading.Thread(target=warm_up, daemon=True)
    t.start()
    return t


@st.cache_data(show_spinner=False, max_entries=50)
def run_verify(before_bytes, before_name, after_bytes, after_name, roi, defect_type, use_gemma):
    """Cached verify(): the same photos + settings return instantly (smooth live demo)."""
    with tempfile.TemporaryDirectory() as tmp:
        b = save_bytes(before_bytes, before_name, Path(tmp) / "before")
        a = save_bytes(after_bytes, after_name, Path(tmp) / "after")
        return verify(b, a, roi=roi, defect_type=defect_type, use_gemma=use_gemma, debug=True)


@st.cache_data(show_spinner=False)
def cached_queue(signature):
    return build_queue()


def save_bytes(data, name, folder):
    # Keep the original bytes so EXIF (time, GPS) survives; own subfolder in case both files share a name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(name).name
    path.write_bytes(data)
    return path


def safe_verify(before_bytes, before_name, after_bytes, after_name):
    """Runs the cached verify with the sidebar settings; shows a friendly error instead of a stack trace."""
    with st.spinner("Checking place, freshness and repair, then writing the note..."):
        try:
            return run_verify(before_bytes, before_name, after_bytes, after_name, roi, defect_type, use_gemma)
        except Exception as e:
            st.error(f"Could not process these photos ({type(e).__name__}: {e}). Try another pair of JPG/PNG photos.")
            return None, None


def badge(verdict):
    ui.verdict_badge(verdict)


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
        else "fixed template (Gemma off, unavailable, too slow, or used a number not in the measurements)"
    st.caption(f"Written by: {source}. The verdict is never decided by Gemma.")

    if "after_overlay" in images:
        c1, c2 = st.columns(2)
        c1.image(images["before_overlay"], width="stretch",
                 caption="Before, warped into the after frame: yellow = defect region, red = defect pixels")
        c2.image(images["after_overlay"], width="stretch", caption="After: red = defect pixels still detected")

    for name, label in GATES + (("measure", "Measure - residual"),):
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


def show_caught(result):
    """For the fooling demo: which gate(s) stopped the attack, and why."""
    failed = [(label, result["checks"][g]["reason"]) for g, label in GATES if not result["checks"][g]["passed"]]
    if failed:
        for label, reason in failed:
            st.success(f"Caught by **{label}**: {reason}")
    elif result["verdict"] == "Cannot verify":
        st.success(f"Caught: {result['checks']['measure'].get('method', '')}")
    else:
        st.warning(f"Not caught by the gates. Verdict: {result['verdict']}. Nija's checks are heuristics and can be fooled.")


start_gemma_warm_up()
with st.container(key="nija_header"):
    h1, h2 = st.columns([3, 2], vertical_alignment="center")
    h1.markdown("**Nija** · Proof of Fix")
    st.session_state.setdefault("lang", "EN")
    h2.segmented_control("Language", ["EN", "ಕನ್ನಡ"], key="lang", label_visibility="collapsed")
ui.hero("Nija - Proof of Fix",
        "Was the pothole really fixed? Nija compares the complaint photo with the closure photo and flags fake or half-done repairs.")
ui.step_pills(["1 Same place", "2 Real, fresh photo", "3 Measure what is left", "4 Verdict", "5 Note by Gemma 4"])
st.caption("Gates and measurements decide the verdict. Gemma 4 only writes the notes. Runs fully offline on this laptop.")

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

tab_verify, tab_fool, tab_queue = st.tabs(["Verify", "Try to fool Nija", "Re-inspection queue"])

with tab_verify:
    col_b, col_a = st.columns(2)
    before_file = col_b.file_uploader("Before photo (complaint)", type=["jpg", "jpeg", "png", "webp"])
    after_file = col_a.file_uploader("After photo (claimed fix)", type=["jpg", "jpeg", "png", "webp"])
    if before_file:
        col_b.image(before_file, width="stretch")
    if after_file:
        col_a.image(after_file, width="stretch")

    if st.button("Verify", type="primary", disabled=not (before_file and after_file)):
        result, images = safe_verify(before_file.getvalue(), before_file.name, after_file.getvalue(), after_file.name)
        if result:
            show_result(result, images)
            st.caption(
                "Honesty note: the defect is found with classical CV heuristics (darker + rough for potholes, colour/texture "
                "clutter for garbage), not a trained model. Use the manual box if auto-detect picks the wrong area. Depth is not measured."
            )

with tab_fool:
    st.write("Judges: try to get a fake repair past Nija. The **before** photo is the synthetic sample pothole below. "
             "Pick an attack, or upload your own pair at the bottom.")
    before_path = SAMPLES / "synthetic_before.jpg"
    cols = st.columns(len(ATTACKS) + 1)
    cols[0].image(str(before_path), caption="Before (complaint)", width="stretch")
    for col, (name, (file, desc)) in zip(cols[1:], ATTACKS.items()):
        col.image(str(SAMPLES / file), caption=desc, width="stretch")
        if col.button(f"Attack: {name}", key=f"attack_{name}", width="stretch"):
            st.session_state["attack"] = name

    attack = st.session_state.get("attack")
    if attack:
        st.subheader(f"Attack: {attack}")
        file = SAMPLES / ATTACKS[attack][0]
        result, images = safe_verify(before_path.read_bytes(), before_path.name, file.read_bytes(), file.name)
        if result:
            show_caught(result)
            show_result(result, images)

    st.divider()
    st.write("**Free upload:** your own before photo plus any after photo (an old photo, a photo of your screen, another street...).")
    fb, fa = st.columns(2)
    fool_before = fb.file_uploader("Before", type=["jpg", "jpeg", "png", "webp"], key="fool_before")
    fool_after = fa.file_uploader("After (your attack)", type=["jpg", "jpeg", "png", "webp"], key="fool_after")
    if st.button("Try it", disabled=not (fool_before and fool_after)):
        result, images = safe_verify(fool_before.getvalue(), fool_before.name, fool_after.getvalue(), fool_after.name)
        if result:
            show_caught(result)
            show_result(result, images)

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
                st.error(f"Could not build the queue ({type(e).__name__}: {e}).")
                rows = []
        if rows:
            counts = {v: sum(r["verdict"] == v for r in rows) for v in config.QUEUE_PRIORITY}
            for col, (v, n) in zip(st.columns(len(counts)), counts.items()):
                col.metric(v, n)
            cols_order = ["priority", "pair", "verdict", "score", "residual_%", "why", "type", "label (ground truth)", "ms"]
            st.dataframe([{k: r[k] for k in cols_order} for r in rows], hide_index=True, width="stretch")
