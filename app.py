"""Streamlit UI for Nija in English and Kannada. Tabs: Verify (upload before + after), Geometry lab (what changed, step by step),
Try to fool Nija (one-click attacks + free upload), Re-inspection queue (all pairs ranked). Run with: python -m streamlit run app.py"""

import tempfile
import threading
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from nija import config, ui, verify, visuals
from nija.i18n import is_kn, note_kn, reason_text, t as _t, verdict_label
from nija.narrate import build_facts, translate_kn, warm_up
from nija.reinspect import build_queue, list_pairs

SAMPLES = config.ROOT / "samples"
GATES = ("gate1", "gate2")
ATTACKS = {  # one-click attacks for the demo; all built from the SYNTHETIC sample pair
    "atk_reused": "synthetic_attack_reused.jpg",
    "atk_screen": "synthetic_attack_screen.jpg",
    "atk_place": "synthetic_after_otherplace.jpg",
}
LAB_SAMPLES = {"sample_fixed": "synthetic_after_fixed.jpg", "sample_partial": "synthetic_after_partial.jpg",
               "sample_notfixed": "synthetic_after_notfixed.jpg", "sample_otherplace": "synthetic_after_otherplace.jpg"}

st.set_page_config(page_title="Nija - Proof of Fix", page_icon="🛣️", layout="wide")
ui.inject_css()


def lang():
    return st.session_state.get("lang") or "EN"


def L(key, **fmt):
    """Text in the language picked in the header."""
    return _t(key, lang(), **fmt)


@st.cache_resource
def start_gemma_warm_up():
    # Load gemma4:e2b into memory in the background once per server, so the first note is fast
    th = threading.Thread(target=warm_up, daemon=True)
    th.start()
    return th


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


@st.cache_data(show_spinner=False, max_entries=100)
def cached_translation(text, facts_items):
    return translate_kn(text, dict(facts_items))


def save_bytes(data, name, folder):
    # Keep the original bytes so EXIF (time, GPS) survives; own subfolder in case both files share a name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(name).name
    path.write_bytes(data)
    return path


def safe_verify(pair, gemma=None):
    """Runs the cached verify with the sidebar settings; shows a friendly error instead of a stack trace."""
    with st.spinner(L("spinner")):
        try:
            return run_verify(*pair, roi, defect_type, use_gemma if gemma is None else gemma)
        except Exception as e:
            st.error(L("err_process", err=type(e).__name__))
            return None, None


def badge(verdict):
    ui.verdict_badge(verdict, verdict_label(verdict, lang()), sub=verdict if is_kn(lang()) else None)


def show_note(result, ctx):
    note = result["note"]
    st.subheader(L("note"))
    if not is_kn(lang()):
        st.write(f"**{L('officer')}:** {note['officer']}")
        st.write(f"**{L('citizen')}:** {note['citizen']}")
        st.caption(L("written_by", src=L("src_gemma") if note["source"] == "gemma" else L("src_template")))
        return
    kn = note_kn(result["verdict"], result["score"], result["checks"])
    store = st.session_state.setdefault("kn_citizen", {})
    key = f"{ctx}:{note['citizen']}"
    citizen = store.get(key) or kn["citizen"]
    st.write(f"**{L('officer')}:** {kn['officer']}")
    st.write(f"**{L('citizen')}:** {citizen}")
    st.caption(L("written_by", src=L("src_kn_gemma") if key in store else L("src_kn_template")))
    if key not in store and st.button(L("btn_translate"), key=f"tr_{ctx}"):
        facts = build_facts(result["verdict"], result["score"], result["checks"])
        with st.spinner(L("spinner")):
            kn_text = cached_translation(note["citizen"], tuple(sorted((k, str(v)) for k, v in facts.items())))
        if kn_text:
            store[key] = kn_text
            st.rerun()
        else:
            st.warning(L("translate_fail"))
    with st.expander(L("officer_en")):
        st.write(note["officer"])
        st.write(note["citizen"])


def show_result(result, images, ctx):
    verdict, score = result["verdict"], result["score"]
    badge(verdict)
    m1, m2, m3 = st.columns(3)
    m1.metric(L("m_score"), L("na") if score is None else f"{score:.2f}")
    residual = result["checks"]["measure"]["residual_area_pct"]
    m2.metric(L("m_residual"), L("na") if residual is None else f"{residual}%")
    m3.metric(L("m_time"), f"{result['timings_ms']['total'] / 1000:.1f} s")

    show_note(result, ctx)

    if "after_overlay" in images:
        c1, c2 = st.columns(2)
        c1.image(images["before_overlay"], width="stretch", caption=L("ov_before"))
        c2.image(images["after_overlay"], width="stretch", caption=L("ov_after"))

    show_geometry_compact(result, images)

    for name in GATES + ("measure",):
        check = result["checks"][name]
        icon = "" if name == "measure" else ("✅ " if check["passed"] else "❌ ")
        with st.expander(f"{icon}{L(name)}"):
            st.write(reason_text(check.get("reason") or check.get("method", ""), lang()))
            st.json(check)

    with st.expander(L("debug_title")):
        if "gate1_matches" in images:
            g1 = result["checks"]["gate1"]
            st.image(images["gate1_matches"], width="stretch",
                     caption=L("debug_caption", inl=g1["inliers"], good=g1["good_matches"]))
        else:
            st.write(L("debug_none"))

    with st.expander(L("raw")):
        st.json(result)


def show_geometry_compact(result, images):
    """Three key geometry pictures and the plain-language bullets, inside every Verify result."""
    if "after_bgr" not in images:
        return
    st.subheader(L("lab_compact"))
    pics = [(visuals.homography_image(images), L("s3_t")), (visuals.heatmap_image(images), L("s5_t")),
            (visuals.contours_image(images, result["checks"]["measure"]), L("s6_t"))]
    pics = [(img, cap) for img, cap in pics if img is not None]
    if pics:
        for col, (img, cap) in zip(st.columns(len(pics)), pics):
            col.image(img, caption=cap, width="stretch")
    for b in visuals.plain_bullets(result, images, lang()):
        st.markdown(f"- {b}")
    st.caption(L("lab_open_full") + (" " + L("lab_img_note") if is_kn(lang()) else ""))


def show_geometry_lab(result, images, live=True):
    """The 7 stages, revealed one after another inside st.status so it feels live."""
    m = result["checks"]["measure"]
    H = images.get("H")

    def stage(title_key, caption_key):
        status.update(label=L(title_key))
        st.markdown(f"#### {L(title_key)}")
        st.caption(L(caption_key))

    def pause():
        if live:
            time.sleep(0.5)

    def show_or_skip(img, skip_key):
        if img is not None:
            st.image(img, width="stretch")
        else:
            st.info(L(skip_key))

    with st.status(L("lab_running"), expanded=True) as status:
        stage("s1_t", "s1_c")
        st.image(visuals.keypoints_image(images)[0], width="stretch")
        pause()
        stage("s2_t", "s2_c")
        if "gate1_matches" in images:
            g1 = result["checks"]["gate1"]
            st.image(images["gate1_matches"], width="stretch", caption=L("match_caption", inl=g1["inliers"], good=g1["good_matches"]))
        else:
            st.info(L("lab_skip_gate1"))
        pause()
        stage("s3_t", "s3_c")
        show_or_skip(visuals.homography_image(images), "lab_skip_gate1")
        if H is not None:
            st.markdown(f"**{visuals.homography_words(visuals.describe_homography(H, images['before_bgr'].shape), lang())}**")
        pause()
        stage("s4_t", "s4_c")
        slider = visuals.slider_html(images)
        if slider:
            components.html(slider, height=490, scrolling=False)
        else:
            st.info(L("lab_skip_gate1"))
        pause()
        stage("s5_t", "s5_c")
        show_or_skip(visuals.heatmap_image(images), "lab_skip_gate1")
        pause()
        stage("s6_t", "s6_c")
        show_or_skip(visuals.contours_image(images, m), "lab_skip_measure")
        pause()
        stage("s7_t", "s7_c")
        bars = visuals.residual_bars_html(m, lang())
        if bars:
            st.markdown(bars, unsafe_allow_html=True)
        else:
            st.info(L("lab_skip_measure"))
        status.update(label=L("lab_done"), state="complete", expanded=True)

    badge(result["verdict"])
    st.subheader(L("lab_what"))
    for b in visuals.plain_bullets(result, images, lang()):
        st.markdown(f"- {b}")
    if is_kn(lang()):
        st.caption(L("lab_img_note"))


def show_caught(result):
    """For the fooling demo: which gate(s) stopped the attack, and why."""
    failed = [(L(g), reason_text(result["checks"][g]["reason"], lang())) for g in GATES if not result["checks"][g]["passed"]]
    if failed:
        for gate, reason in failed:
            st.success(L("caught", gate=gate, reason=reason))
    elif result["verdict"] == "Cannot verify":
        st.success(L("caught_measure", reason=reason_text(result["checks"]["measure"].get("method", ""), lang())))
    else:
        st.warning(L("not_caught", verdict=verdict_label(result["verdict"], lang())))


def both(key):
    """English / Kannada label that never changes, so uploaded files survive a language switch."""
    return f"{_t(key, 'EN')} / {_t(key, 'KN')}"


def upload_pair(up_b, up_a):
    return (up_b.getvalue(), up_b.name, up_a.getvalue(), up_a.name)


def sample_pair(after_file):
    b, a = SAMPLES / "synthetic_before.jpg", SAMPLES / after_file
    return (b.read_bytes(), b.name, a.read_bytes(), a.name)


start_gemma_warm_up()
with st.container(key="nija_header"):
    h1, h2 = st.columns([3, 2], vertical_alignment="center")
    st.session_state.setdefault("lang", "EN")
    h2.segmented_control("Language", ["EN", "ಕನ್ನಡ"], key="lang", label_visibility="collapsed")
    h1.markdown(L("brand"))
ui.hero(L("app_title"), L("hero_promise"))
ui.step_pills([L(f"step{i}") for i in range(1, 6)])
st.caption(L("tagline"))

with st.sidebar:
    st.header(L("settings"))
    defect_type = st.radio(L("defect_type"), ["pothole", "garbage"], horizontal=True, format_func=L, key="defect_type")
    use_gemma = st.checkbox(L("use_gemma"), value=True, key="use_gemma")
    use_roi = st.checkbox(L("use_roi"), key="use_roi")
    roi = None
    if use_roi:
        st.caption(L("roi_caption"))
        rx = st.slider(L("roi_x"), 0, 95, 25, key="roi_x")
        ry = st.slider(L("roi_y"), 0, 95, 25, key="roi_y")
        rw = st.slider(L("roi_w"), 5, 100 - rx, min(50, 100 - rx), key="roi_w")
        rh = st.slider(L("roi_h"), 5, 100 - ry, min(50, 100 - ry), key="roi_h")
        roi = (rx / 100, ry / 100, rw / 100, rh / 100)

tab_verify, tab_lab, tab_fool, tab_queue = st.tabs([L("tab_verify"), L("lab_tab"), L("tab_fool"), L("tab_queue")])

with tab_verify:
    col_b, col_a = st.columns(2)
    before_file = col_b.file_uploader(both("up_before"), type=["jpg", "jpeg", "png", "webp"], key="up_before")
    after_file = col_a.file_uploader(both("up_after"), type=["jpg", "jpeg", "png", "webp"], key="up_after")
    if before_file:
        col_b.image(before_file, width="stretch")
    if after_file:
        col_a.image(after_file, width="stretch")
    if st.button(L("btn_verify"), type="primary", disabled=not (before_file and after_file), key="btn_verify"):
        st.session_state["verify_pair"] = upload_pair(before_file, after_file)
        st.session_state["last_pair"] = st.session_state["verify_pair"]
    if st.session_state.get("verify_pair"):
        result, images = safe_verify(st.session_state["verify_pair"])
        if result:
            show_result(result, images, "verify")
            st.caption(L("honesty"))

with tab_lab:
    st.write(L("lab_intro"))
    options = list(LAB_SAMPLES) + (["lab_last"] if "last_pair" in st.session_state else [])
    pick = st.selectbox(L("lab_source"), options, index=1, format_func=L, key="lab_pick")
    clicked = st.button(L("lab_run"), type="primary", key="lab_run")
    if clicked:
        if pick == "lab_last":
            st.session_state["lab_pair"] = st.session_state["last_pair"]
        else:
            st.session_state["lab_pair"] = sample_pair(LAB_SAMPLES[pick])
    if st.session_state.get("lab_pair"):
        result, images = safe_verify(st.session_state["lab_pair"], gemma=False)
        if result:
            show_geometry_lab(result, images, live=clicked)

with tab_fool:
    st.write(L("fool_intro"))
    cols = st.columns(len(ATTACKS) + 1)
    cols[0].image(str(SAMPLES / "synthetic_before.jpg"), caption=L("fool_before_cap"), width="stretch")
    for col, (key, file) in zip(cols[1:], ATTACKS.items()):
        col.image(str(SAMPLES / file), caption=L(key + "_d"), width="stretch")
        if col.button(L("attack", name=L(key)), key=f"attack_{key}", width="stretch"):
            st.session_state["attack"] = key
    attack = st.session_state.get("attack")
    if attack in ATTACKS:
        st.subheader(L("attack", name=L(attack)))
        result, images = safe_verify(sample_pair(ATTACKS[attack]))
        if result:
            show_caught(result)
            show_result(result, images, "attack")

    st.divider()
    st.write(L("free_upload"))
    fb, fa = st.columns(2)
    fool_before = fb.file_uploader(both("fb_before"), type=["jpg", "jpeg", "png", "webp"], key="fool_before")
    fool_after = fa.file_uploader(both("fb_after"), type=["jpg", "jpeg", "png", "webp"], key="fool_after")
    if st.button(L("btn_try"), disabled=not (fool_before and fool_after), key="btn_try"):
        st.session_state["fool_pair"] = upload_pair(fool_before, fool_after)
    if st.session_state.get("fool_pair"):
        result, images = safe_verify(st.session_state["fool_pair"])
        if result:
            show_caught(result)
            show_result(result, images, "free")

with tab_queue:
    pairs = list_pairs()
    st.write(L("queue_intro", order=" > ".join(verdict_label(v, lang()) for v in config.QUEUE_PRIORITY)))
    if not pairs:
        st.info(L("queue_empty"))
    else:
        signature = tuple((p.name, (p / "before.jpg").stat().st_mtime, (p / "after.jpg").stat().st_mtime) for p in pairs)
        if st.button(L("btn_refresh"), key="btn_refresh"):
            cached_queue.clear()
        with st.spinner(L("queue_spinner", n=len(pairs))):
            try:
                rows = cached_queue(signature)
            except Exception as e:
                st.error(L("err_queue", err=type(e).__name__))
                rows = []
        if rows:
            counts = {v: sum(r["verdict"] == v for r in rows) for v in config.QUEUE_PRIORITY}
            for col, (v, n) in zip(st.columns(len(counts)), counts.items()):
                col.metric(verdict_label(v, lang()), n)
            table = [{L("col_priority"): r["priority"], L("col_pair"): r["pair"],
                      L("col_verdict"): verdict_label(r["verdict"], lang()), L("col_score"): r["score"],
                      L("col_residual"): r["residual_%"], L("col_why"): reason_text(r["why"], lang()),
                      L("col_type"): L(r["type"]) if r["type"] else "", L("col_label"): r["label (ground truth)"],
                      L("col_ms"): r["ms"]} for r in rows]
            st.dataframe(table, hide_index=True, width="stretch")

st.divider()
st.caption(f"{_t('footer', 'EN')}  \n{_t('footer', 'KN')}")
