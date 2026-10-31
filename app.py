"""Streamlit UI for Nija in English and Kannada, with Citizen / Officer / Auditor views. Tabs: Verify, Geometry lab,
Try to fool Nija, Re-inspection queue, Why Karnataka. Run with: python -m streamlit run app.py"""

import csv
import html
import io
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import quote

import cv2
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from nija import config, evidence, ui, verify, visuals
from nija.i18n import FACTS, is_kn, note_kn, reason_text, t as _t, verdict_label
from nija.narrate import build_facts, translate_kn, warm_up
from nija.reinspect import _read_label, build_queue, label_roi, list_pairs

SAMPLES = config.ROOT / "samples"
GATES = ("gate1", "gate2")
ATTACKS = {  # one-click attacks for the demo; all built from the SYNTHETIC sample pair
    "atk_reused": "synthetic_attack_reused.jpg",
    "atk_screen": "synthetic_attack_screen.jpg",
    "atk_place": "synthetic_after_otherplace.jpg",
}
LAB_SAMPLES = {"sample_fixed": "synthetic_after_fixed.jpg", "sample_partial": "synthetic_after_partial.jpg",
               "sample_notfixed": "synthetic_after_notfixed.jpg", "sample_otherplace": "synthetic_after_otherplace.jpg"}
ROLES = ["citizen", "officer", "auditor"]
ACCOUNTS = {"citizen@demo": "citizen", "officer@demo": "officer", "auditor@demo": "auditor"}  # demo only, no real authentication

st.set_page_config(page_title="Nija - Proof of Fix", page_icon="🛣️", layout="wide")
ui.inject_css()


def lang():
    return st.session_state.get("lang") or "EN"


def role():
    return st.session_state.get("role") or "officer"


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


def safe_verify(pair, gemma=None, box=None, kind=None):
    """Runs the cached verify with the sidebar settings (or a pair's saved defect box); friendly error, never a stack trace."""
    with st.spinner(L("spinner")):
        try:
            return run_verify(*pair, box or roi, kind or defect_type, use_gemma if gemma is None else gemma)
        except Exception as e:
            st.error(L("err_process", err=type(e).__name__))
            return None, None


def with_context(result, pair):
    """Result JSON plus the extra "context" key (GPS from EXIF, officer-entered corporation and ward). Never inside checks."""
    ctx = evidence.location_context(pair[0], pair[2], corporation, ward)
    return {**result, "context": ctx}, ctx


def badge(verdict):
    ui.verdict_badge(verdict, verdict_label(verdict, lang()), sub=verdict if is_kn(lang()) else None)


def citizen_text(result, ctx):
    """Citizen message in the chosen language. Kannada: template, or Gemma's translation once it passed the number check."""
    note = result["note"]
    if not is_kn(lang()):
        return note["citizen"], L("src_gemma") if note["source"] == "gemma" else L("src_template"), None
    store = st.session_state.setdefault("kn_citizen", {})
    key = f"{ctx}:{note['citizen']}"
    if key in store:
        return store[key], L("src_kn_gemma"), None
    return note_kn(result["verdict"], result["score"], result["checks"])["citizen"], L("src_kn_template"), key


def translate_button(result, key, ctx):
    if key and st.button(L("btn_translate"), key=f"tr_{ctx}"):
        facts = build_facts(result["verdict"], result["score"], result["checks"])
        with st.spinner(L("spinner")):
            kn_text = cached_translation(result["note"]["citizen"], tuple(sorted((k, str(v)) for k, v in facts.items())))
        if kn_text:
            st.session_state["kn_citizen"][key] = kn_text
            st.rerun()
        else:
            st.warning(L("translate_fail"))


def show_note(result, ctx):
    note = result["note"]
    st.subheader(L("note"))
    text, src, key = citizen_text(result, ctx)
    officer = note["officer"] if not is_kn(lang()) else note_kn(result["verdict"], result["score"], result["checks"])["officer"]
    st.write(f"**{L('officer')}:** {officer}")
    st.write(f"**{L('citizen')}:** {text}")
    st.caption(L("written_by", src=src))
    translate_button(result, key, ctx)
    if is_kn(lang()):
        with st.expander(L("officer_en")):
            st.write(note["officer"])
            st.write(note["citizen"])


def listen(text, fallback, key):
    components.html(evidence.listen_html(text, "kn-IN" if is_kn(lang()) else "en-IN", fallback,
                                         {"listen": L("cit_listen"), "no_voice": L("voice_no_voice"),
                                          "no_speech": L("voice_no_speech")}), height=64)


def show_location(result, ctx):
    g1 = result["checks"]["gate1"]
    fmt = lambda p: f"{p[0]:.5f}, {p[1]:.5f}" if p else L("loc_none")
    body = (f"<p><b>{html.escape(L('loc_before'))}:</b> {fmt(ctx['gps_before'])}<br>"
            f"<b>{html.escape(L('loc_after'))}:</b> {fmt(ctx['gps_after'])}</p>"
            f"<p>{html.escape(L('loc_dist', m=ctx['distance_m']) if ctx['distance_m'] is not None else L('loc_nodist'))}</p>"
            f"<p>{html.escape(L('loc_gate1', reason=reason_text(g1['reason'], lang())))}</p>"
            f"<p class='src'>{html.escape(L('loc_corp'))}: {html.escape(ctx['corporation'] or L('loc_pick'))} · "
            f"{html.escape(L('loc_ward'))}: {html.escape(ctx['ward'] or L('loc_pick'))} ({html.escape(L('loc_officer_note'))})</p>")
    ui.card(body, title=L("loc_title"), accent=ui.SAFFRON)
    pts = [p for p in (ctx["gps_before"], ctx["gps_after"]) if p]
    if pts:
        st.map(pd.DataFrame(pts, columns=["lat", "lon"]), zoom=16, size=8)
        st.caption(L("loc_map_note"))
        lat, lon = pts[-1]
        st.link_button(L("loc_gmaps"), f"https://www.google.com/maps?q={lat},{lon}")


def show_retake_guide(images):
    if "before_bgr" not in images:
        return
    faded = cv2.addWeighted(images["before_bgr"], 0.45, np.full_like(images["before_bgr"], 255), 0.55, 0)
    c1, c2 = st.columns(2)
    c1.image(cv2.cvtColor(faded, cv2.COLOR_BGR2RGB), caption=L("fool_before_cap"), width="stretch")
    c2.image(cv2.cvtColor(images["after_bgr"], cv2.COLOR_BGR2RGB), caption=L("up_after"), width="stretch")
    st.markdown(f"{L('off_retake_intro')}\n\n1. {L('off_tip1')}\n2. {L('off_tip2')}\n3. {L('off_tip3')}")


def show_checks(result, images):
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


def show_metrics(result):
    score = result["score"]
    m1, m2, m3 = st.columns(3)
    m1.metric(L("m_score"), L("na") if score is None else f"{score:.2f}")
    residual = result["checks"]["measure"]["residual_area_pct"]
    m2.metric(L("m_residual"), L("na") if residual is None else f"{residual}%")
    m3.metric(L("m_time"), f"{result['timings_ms']['total'] / 1000:.1f} s")


def show_result(result, images, ctx, pair):
    """Same result, three views: citizen (plain), officer (geometry and checks), auditor (evidence)."""
    full, context = with_context(result, pair)
    badge(result["verdict"])
    if role() == "citizen":
        text, src, key = citizen_text(result, ctx)
        ui.card(f"<p style='font-size:1.15rem'>{html.escape(text)}</p><p class='src'>{html.escape(L('written_by', src=src))}</p>",
                title=L("citizen"), accent=ui.VERDICT_COLOURS[result["verdict"]][0])
        translate_button(result, key, ctx)
        listen(f"{verdict_label(result['verdict'], lang())}. {text}", f"{result['verdict']}. {result['note']['citizen']}", ctx)
        c1, c2 = st.columns(2)
        c1.link_button(L("cit_whatsapp"), "https://wa.me/?text=" + quote(f"Nija: {verdict_label(result['verdict'], lang())}. {text}"),
                       width="stretch")
        if c2.button(L("cit_feedback"), key=f"fb_{ctx}", width="stretch"):
            evidence.add_feedback(pair[0], result["verdict"], lang())
            st.success(L("cit_feedback_done"))
        return

    show_metrics(result)
    if role() == "auditor":
        show_location(result, context)
        st.download_button(L("aud_evidence"), evidence.evidence_zip(result, images, pair, context),
                           file_name=f"nija_evidence_{evidence.photo_id(pair[0])}.zip", mime="application/zip",
                           key=f"zip_{ctx}", type="primary")
        show_checks(result, images)
        with st.expander(L("raw"), expanded=True):
            st.json(full)
        return

    # Officer
    show_note(result, ctx)
    if result["verdict"] == "Cannot verify":
        failed = [result["checks"][g] for g in GATES if not result["checks"][g]["passed"]]
        why = reason_text(failed[0]["reason"] if failed else result["checks"]["measure"].get("method", ""), lang())
        ui.card(f"<p>{html.escape(why)}</p>", title=L("off_why"), accent=ui.RED)
        st.subheader(L("off_retake"))
        show_retake_guide(images)
    if "after_overlay" in images:
        c1, c2 = st.columns(2)
        c1.image(images["before_overlay"], width="stretch", caption=L("ov_before"))
        c2.image(images["after_overlay"], width="stretch", caption=L("ov_after"))
    show_geometry_compact(result, images)
    show_location(result, context)
    show_checks(result, images)
    if result["verdict"] != "Cannot verify":
        with st.expander(L("off_retake")):
            show_retake_guide(images)
    with st.expander(L("raw")):
        st.json(full)


def show_geometry_compact(result, images):
    """Three key geometry pictures and the plain-language bullets, inside every officer result."""
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


def show_why_karnataka():
    st.subheader(L("why_title"))
    steps = ["j_report", "j_assign", "j_repair", "j_close", "j_reopen", "j_audit"]

    def flow(hot_cls):
        nodes = [f"<span class='nija-node {hot_cls if s == 'j_close' else ''}'>{html.escape(L(s))}</span>" for s in steps]
        return "<div class='nija-flow'>" + "<span class='nija-arrow'>→</span>".join(nodes) + "</div>"

    st.markdown(f"#### {L('why_journey')}")
    ui.card(flow("hot") + f"<p>{html.escape(L('why_today_line'))}</p>", title=L("why_today"), accent=ui.RED)
    ui.card(flow("core") + f"<p>{html.escape(L('why_nija_line'))}</p>", title=L("why_nija"), accent=ui.TEAL)

    st.markdown(f"#### {L('why_facts')}")
    cards = []
    for en, kn, outlet, url in FACTS:
        src = (f"<a href='{html.escape(url)}' target='_blank' rel='noopener'>{html.escape(L('why_as_reported', outlet=outlet))}</a>"
               if url else f"{html.escape(L('why_as_reported', outlet=outlet))} · {html.escape(L('why_no_link'))}")
        cards.append(f"<div class='nija-card' style='margin:0'><p>{html.escape(kn if is_kn(lang()) else en)}</p>"
                     f"<p class='src'>{src}</p></div>")
    st.markdown("<div class='nija-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    st.markdown(f"#### {L('why_fits')}")
    node = lambda text, cls="": f"<span class='nija-node {cls}'>{html.escape(text)}</span>"
    st.markdown(
        f"<div class='nija-card'><p class='src' style='text-align:center'>{html.escape(L('why_inputs'))}</p>"
        f"<div class='nija-flow'>{node('Sahaaya')}{node('1533')}{node('Rasthe Gundi Gamana')}</div>"
        f"<div class='nija-flow'><span class='nija-arrow'>↓</span></div>"
        f"<div class='nija-flow'>{node('Nija: ' + L('step1') + ' · ' + L('step2') + ' · ' + L('step3'), 'core')}</div>"
        f"<div class='nija-flow'><span class='nija-arrow'>↓</span></div>"
        f"<div class='nija-flow'>{node(L('role_citizen'))}{node(L('role_officer'))}{node(L('role_auditor'))}</div>"
        f"<p class='src' style='text-align:center'>{html.escape(L('why_outputs'))}</p></div>",
        unsafe_allow_html=True)
    ui.card(f"<p>{html.escape(L('why_limits_body'))}</p>", title=L("why_limits"), accent=ui.SAFFRON)


def show_corporation_summary(rows):
    """Auditor table by GBA corporation (from each pair's label.json), CSV download and a claimed vs verified chart."""
    st.markdown(f"#### {L('sum_title')}")
    corps = evidence.CORPORATIONS + ["Unassigned"]
    stats = {c: {v: 0 for v in config.QUEUE_PRIORITY} for c in corps}
    for r in rows:
        corp = _read_label(config.PAIRS_DIR / r["pair"]).get("corporation") or "Unassigned"
        stats.setdefault(corp, {v: 0 for v in config.QUEUE_PRIORITY})[r["verdict"]] += 1
    table = []
    for corp, counts in stats.items():
        n = sum(counts.values())
        table.append({L("sum_corp"): L("sum_unassigned") if corp == "Unassigned" else corp, L("sum_reviewed"): n,
                      **{verdict_label(v, lang()): counts[v] for v in config.QUEUE_PRIORITY},
                      L("sum_pct"): round(100 * counts["Verified"] / n, 1) if n else None})
    st.dataframe(table, hide_index=True, width="stretch")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(table[0].keys()))
    w.writeheader()
    w.writerows(table)
    st.download_button(L("sum_csv"), buf.getvalue().encode("utf-8-sig"), file_name="nija_corporation_summary.csv",
                       mime="text/csv", key="sum_csv")
    st.markdown(f"**{L('sum_chart')}**")
    chart = pd.DataFrame({L("sum_claimed"): [row[L("sum_reviewed")] for row in table],
                          L("sum_verified"): [row[verdict_label("Verified", lang())] for row in table]},
                         index=[row[L("sum_corp")] for row in table])
    st.bar_chart(chart, stack=False, color=[ui.SAFFRON, ui.TEAL])
    st.caption(L("sum_note"))


def show_roadmap():
    """Intake -> Nija verification -> outputs. Green = built today, grey dashed = planned."""
    st.subheader(L("rm_title"))
    node = lambda key, built: (f"<span class='nija-node {'built' if built else 'planned'}'>{html.escape(L(key))}"
                               f"<small>{html.escape(L('rm_built') if built else L('rm_planned'))}</small></span>")
    col = lambda title, nodes: f"<div class='nija-col'><h5>{html.escape(L(title))}</h5>{''.join(nodes)}</div>"
    st.markdown(
        "<div class='nija-card'><div class='nija-flow' style='align-items:stretch'>"
        + col("rm_intake", [node("rm_web", True), node("rm_app", False), node("rm_whatsapp", False), node("rm_1533", False)])
        + "<span class='nija-arrow' style='align-self:center'>→</span>"
        + col("rm_verify", [node("rm_gates", True), node("rm_measure", True)])
        + "<span class='nija-arrow' style='align-self:center'>→</span>"
        + col("rm_outputs", [node("rm_citizen", True), node("rm_officer", True), node("rm_auditor", True)])
        + "</div></div>", unsafe_allow_html=True)
    st.info(L("rm_honest"))


def both(key):
    """English / Kannada label that never changes, so uploaded files survive a language switch."""
    return f"{_t(key, 'EN')} / {_t(key, 'KN')}"


def upload_pair(up_b, up_a):
    return (up_b.getvalue(), up_b.name, up_a.getvalue(), up_a.name)


def sample_pair(after_file):
    b, a = SAMPLES / "synthetic_before.jpg", SAMPLES / after_file
    return (b.read_bytes(), b.name, a.read_bytes(), a.name)


start_gemma_warm_up()
st.session_state.setdefault("lang", "EN")
st.session_state.setdefault("role", "officer")
with st.container(key="nija_header"):
    h1, h2, h3 = st.columns([2, 3, 2], vertical_alignment="center")
    h3.segmented_control("Language", ["EN", "ಕನ್ನಡ"], key="lang", label_visibility="collapsed")
    h2.segmented_control(L("role"), ROLES, key="role", format_func=lambda r: L("role_" + r), label_visibility="collapsed")
    h1.markdown(L("brand"))
ui.hero(L("app_title"), L("hero_promise"))
ui.step_pills([L(f"step{i}") for i in range(1, 6)])
st.caption(L("tagline"))


# Demo sign-in: callbacks run before the next script run, so they may set the header's role widget safely
def sign_in(account):
    st.session_state["account"] = account
    st.session_state["role"] = ACCOUNTS[account]


def skip_sign_in():
    st.session_state["signin_skipped"] = True


def sign_out():
    st.session_state.pop("account", None)
    st.session_state["signin_skipped"] = False


if not st.session_state.get("account") and not st.session_state.get("signin_skipped"):
    st.subheader(L("signin_title"))
    st.info(L("signin_banner"))
    st.write(L("signin_intro"))
    for col, (account, acct_role) in zip(st.columns(3), ACCOUNTS.items()):
        with col:
            ui.card(f"<p style='font-size:1.1rem'><b>{html.escape(L('role_' + acct_role))}</b></p>"
                    f"<p class='src'>{html.escape(account)}</p>", accent=ui.SAFFRON if acct_role == "citizen" else ui.TEAL)
            st.button(L("signin_as", role=L("role_" + acct_role)), key=f"signin_{acct_role}", type="primary",
                      on_click=sign_in, args=(account,), width="stretch")
    st.button(L("signin_skip"), key="signin_skip", type="tertiary", on_click=skip_sign_in)
    st.stop()

if st.session_state.get("account"):
    b1, b2 = st.columns([5, 1], vertical_alignment="center")
    b1.info(f"{L('signin_banner')} {L('signed_as', acct=st.session_state['account'])}")
    b2.button(L("signout"), key="signout", on_click=sign_out, width="stretch")

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
    st.divider()
    st.subheader(L("loc_title"))
    corporation = st.selectbox(L("loc_corp"), [None] + evidence.CORPORATIONS, key="corporation",
                               format_func=lambda c: L("loc_pick") if c is None else c)
    ward = st.text_input(L("loc_ward"), key="ward")
    st.caption(L("loc_officer_note"))

tab_verify, tab_lab, tab_fool, tab_queue, tab_why, tab_roadmap = st.tabs(
    [L("tab_verify"), L("lab_tab"), L("tab_fool"), L("tab_queue"), L("tab_why"), L("tab_roadmap")])

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
        pair = st.session_state["verify_pair"]
        result, images = safe_verify(pair)
        if result:
            show_result(result, images, "verify", pair)
            st.caption(L("honesty"))

with tab_lab:
    st.write(L("lab_intro"))
    boxed = {p.name: _read_label(p) for p in list_pairs() if label_roi(_read_label(p))}  # pairs with a saved defect box
    options = list(LAB_SAMPLES) + [f"pair:{n}" for n in boxed] + (["lab_last"] if "last_pair" in st.session_state else [])
    pick = st.selectbox(L("lab_source"), options, index=1, key="lab_pick",
                        format_func=lambda o: f"{o[5:]} ({boxed[o[5:]].get('label', '')}, synthetic AI photos, box)" if o.startswith("pair:") else L(o))
    clicked = st.button(L("lab_run"), type="primary", key="lab_run")
    if clicked:
        if pick.startswith("pair:"):
            d, lab = config.PAIRS_DIR / pick[5:], boxed[pick[5:]]
            st.session_state["lab_pair"] = (((d / "before.jpg").read_bytes(), "before.jpg", (d / "after.jpg").read_bytes(), "after.jpg"),
                                            label_roi(lab), lab.get("type"))
        else:
            st.session_state["lab_pair"] = (st.session_state["last_pair"] if pick == "lab_last"
                                            else sample_pair(LAB_SAMPLES[pick]), None, None)
    if st.session_state.get("lab_pair"):
        lab_pair, lab_box, lab_kind = st.session_state["lab_pair"]
        result, images = safe_verify(lab_pair, gemma=False, box=lab_box, kind=lab_kind)
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
        pair = sample_pair(ATTACKS[attack])
        result, images = safe_verify(pair)
        if result:
            show_caught(result)
            show_result(result, images, "attack", pair)

    st.divider()
    st.write(L("free_upload"))
    fb, fa = st.columns(2)
    fool_before = fb.file_uploader(both("fb_before"), type=["jpg", "jpeg", "png", "webp"], key="fool_before")
    fool_after = fa.file_uploader(both("fb_after"), type=["jpg", "jpeg", "png", "webp"], key="fool_after")
    if st.button(L("btn_try"), disabled=not (fool_before and fool_after), key="btn_try"):
        st.session_state["fool_pair"] = upload_pair(fool_before, fool_after)
    if st.session_state.get("fool_pair"):
        pair = st.session_state["fool_pair"]
        result, images = safe_verify(pair)
        if result:
            show_caught(result)
            show_result(result, images, "free", pair)

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
            flags = evidence.feedback_counts()
            ids = {p.name: evidence.photo_id((p / "before.jpg").read_bytes()) for p in pairs}
            counts = {v: sum(r["verdict"] == v for r in rows) for v in config.QUEUE_PRIORITY}
            for col, (v, n) in zip(st.columns(len(counts)), counts.items()):
                col.metric(verdict_label(v, lang()), n)
            f1, f2 = st.columns(2)
            show_v = f1.multiselect(L("aud_filter_verdict"), config.QUEUE_PRIORITY, default=config.QUEUE_PRIORITY,
                                    format_func=lambda v: verdict_label(v, lang()), key="q_verdicts")
            types = sorted({r["type"] for r in rows})
            show_t = f2.multiselect(L("aud_filter_type"), types, default=types, format_func=lambda x: L(x) if x else "-",
                                    key="q_types")
            rows = [r for r in rows if r["verdict"] in show_v and r["type"] in show_t]
            table = [{L("col_priority"): r["priority"], L("col_pair"): r["pair"],
                      L("col_verdict"): verdict_label(r["verdict"], lang()), L("col_score"): r["score"],
                      L("col_residual"): r["residual_%"], L("aud_flag"): ("🚩 " + str(flags[ids[r["pair"]]])) if flags.get(ids[r["pair"]]) else "",
                      L("col_why"): reason_text(r["why"], lang()), L("col_type"): L(r["type"]) if r["type"] else "",
                      L("col_label"): r["label (ground truth)"], L("col_ms"): r["ms"]} for r in rows]
            st.dataframe(table, hide_index=True, width="stretch")
            if table:
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=list(table[0].keys()))
                w.writeheader()
                w.writerows(table)
                st.download_button(L("aud_csv"), buf.getvalue().encode("utf-8-sig"), file_name="nija_queue.csv",
                                   mime="text/csv", key="q_csv")
            if role() == "auditor":
                show_corporation_summary(cached_queue(signature))
            if role() == "auditor" and rows:
                st.markdown(f"#### {L('aud_evidence')}")
                p_name = st.selectbox(L("aud_pick"), [r["pair"] for r in rows], key="aud_pair")
                if st.button(L("aud_build"), key="aud_build"):
                    d = config.PAIRS_DIR / p_name
                    pair = ((d / "before.jpg").read_bytes(), "before.jpg", (d / "after.jpg").read_bytes(), "after.jpg")
                    result, images = safe_verify(pair, gemma=False)
                    if result:
                        _, context = with_context(result, pair)
                        st.download_button(L("aud_evidence"), evidence.evidence_zip(result, images, pair, context),
                                           file_name=f"nija_evidence_{p_name}.zip", mime="application/zip", key="aud_zip")

with tab_roadmap:
    show_roadmap()

with tab_why:
    show_why_karnataka()

st.divider()
st.caption(f"{_t('footer', 'EN')}  \n{_t('footer', 'KN')}")
