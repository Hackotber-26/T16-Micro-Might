"""Design system for the Streamlit app: bundled fonts (Plus Jakarta Sans, Inter, Noto Sans Kannada; served offline from static/fonts),
colour tokens, CSS (cards, 44 px tap targets, mobile stacking) and small HTML helpers: hero(), card(), verdict_badge(), step_pills(), pill()."""

import html

import streamlit as st

# Colour tokens
SAFFRON = "#F5B700"  # Karnataka yellow (accent)
RED = "#C62828"  # Karnataka red (accent)
TEAL = "#0B4F4A"  # primary
TEAL_2 = "#127A6E"
CREAM = "#FBF6EA"  # background
SURFACE = "#FFFFFF"
INK = "#14201D"  # text
MUTED = "#5B6B66"
LINE = "#E8DFC9"
VERDICT_COLOURS = {
    "Verified": ("#1B7F3B", "#FFFFFF"),
    "Partial": ("#F5B700", INK),
    "Not fixed": (RED, "#FFFFFF"),
    "Cannot verify": ("#4E6470", "#FFFFFF"),
}
TONES = {"ok": "#1B7F3B", "warn": "#C98A00", "bad": RED, "info": TEAL, "muted": "#4E6470"}

BODY_FONT = '"Inter", "Noto Sans Kannada", "Nirmala UI", "Tunga", "Segoe UI", system-ui, sans-serif'
HEAD_FONT = '"Plus Jakarta Sans", "Noto Sans Kannada", "Nirmala UI", "Segoe UI", system-ui, sans-serif'
FONT_URL = "app/static/fonts"  # Streamlit static serving (enableStaticServing in .streamlit/config.toml)

CSS = f"""
<style>
@font-face {{ font-family: "Inter"; src: url("{FONT_URL}/Inter.ttf") format("truetype"); font-weight: 100 900; font-display: swap; }}
@font-face {{ font-family: "Plus Jakarta Sans"; src: url("{FONT_URL}/PlusJakartaSans.ttf") format("truetype"); font-weight: 200 800; font-display: swap; }}
@font-face {{ font-family: "Noto Sans Kannada"; src: url("{FONT_URL}/NotoSansKannada.ttf") format("truetype"); font-weight: 100 900; font-display: swap; }}

html, body, .stApp, .stMarkdown, .stMarkdown p, label, button, input, textarea, select, [data-testid="stMetricValue"],
[data-testid="stMetricLabel"], [role="tab"], .stCaption, [data-testid="stCaptionContainer"] {{
  font-family: {BODY_FONT};
}}
h1, h2, h3, h4, .nija-hero h1, .nija-verdict, [data-testid="stMetricValue"] {{ font-family: {HEAD_FONT} !important; letter-spacing: -0.01em; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: "Material Symbols Rounded" !important; }}
.stApp {{ background: radial-gradient(1200px 500px at 85% -10%, #FFF1C9 0%, rgba(255,241,201,0) 60%), {CREAM}; }}
.stMarkdown p, .stMarkdown li, label {{ font-size: 1rem; line-height: 1.65; color: {INK}; }}
.block-container {{ padding-top: 4.2rem; max-width: 1200px; }}
h3, h4 {{ color: {TEAL}; }}
[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {LINE}; }}

/* Tap targets: at least 44 px high */
.stButton button, .stDownloadButton button, .stLinkButton a, [data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"], [role="tab"], [data-testid="stSegmentedControl"] button {{
  min-height: 44px; border-radius: 12px; font-weight: 600;
}}
[data-testid="stBaseButton-primary"] {{ background: linear-gradient(135deg, {TEAL} 0%, {TEAL_2} 100%); border: 0;
  box-shadow: 0 4px 14px rgba(11, 79, 74, 0.25); }}
[role="tab"] {{ padding: 0 14px; font-size: 1rem; }}

/* Sticky header with the language / role toggles (sticky on the wrapper Streamlit puts around the keyed container) */
[data-testid="stLayoutWrapper"]:has(> .st-key-nija_header) {{ position: sticky; top: 3.75rem; z-index: 50; }}
.st-key-nija_header {{ background: rgba(251, 246, 234, 0.96); backdrop-filter: blur(6px); padding: 8px 0;
  border-bottom: 3px solid {SAFFRON}; }}
.st-key-nija_header button {{ min-height: 44px; font-size: 0.95rem; padding: 0 14px; font-weight: 600; }}
[data-testid="stHeaderActionElements"] {{ display: none; }}  /* tiny auto anchor links next to headings */

/* Hero banner */
.nija-hero {{
  background: linear-gradient(125deg, {TEAL} 0%, {TEAL_2} 60%, #1F9C7E 100%);
  color: #fff; border-radius: 22px; padding: 26px 28px; margin: 4px 0 14px 0; position: relative; overflow: hidden;
  border-bottom: 6px solid {SAFFRON}; box-shadow: 0 10px 30px rgba(11, 79, 74, 0.22);
}}
.nija-hero::after {{ content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px; border-radius: 50%;
  background: radial-gradient(circle, rgba(245,183,0,0.35) 0%, rgba(245,183,0,0) 70%); }}
.nija-hero h1 {{ color: #fff; font-size: 2.4rem; margin: 0; line-height: 1.15; padding: 0; font-weight: 800; }}
.nija-hero .nija-flag {{ display: inline-block; width: 46px; height: 8px; border-radius: 4px; margin-bottom: 12px;
  background: linear-gradient(90deg, {SAFFRON} 50%, {RED} 50%); }}
.nija-hero p {{ color: #E6F4F1; font-size: 1.1rem; margin: 8px 0 0 0; max-width: 820px; }}

/* Cards */
.nija-card {{
  background: {SURFACE}; border-radius: 18px; padding: 16px 18px; margin: 8px 0;
  box-shadow: 0 2px 12px rgba(20, 32, 29, 0.07); border: 1px solid {LINE}; border-left: 6px solid {TEAL};
}}
.nija-card h4 {{ margin: 0 0 6px 0; color: {TEAL}; font-size: 1.05rem; }}
.nija-card p {{ margin: 4px 0; }}
.nija-card .src {{ color: {MUTED}; font-size: 0.85rem; }}
.nija-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }}
.nija-flow {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; margin: 8px 0; }}
.nija-node {{ background: {SURFACE}; border: 2px solid {LINE}; border-radius: 14px; padding: 10px 14px; font-weight: 600;
  text-align: center; min-width: 110px; }}
.nija-node.hot {{ background: {SAFFRON}; border-color: {SAFFRON}; color: {INK}; }}
.nija-node.core {{ background: {TEAL}; border-color: {TEAL}; color: #fff; }}
.nija-arrow {{ color: {MUTED}; font-weight: 800; }}

/* Verdict badge */
.nija-verdict {{
  display: inline-flex; align-items: center; gap: 12px; padding: 14px 26px; border-radius: 18px;
  font-size: 2rem; font-weight: 800; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16); margin-bottom: 12px;
}}
.nija-verdict small {{ font-size: 1rem; font-weight: 600; opacity: 0.9; }}

/* Step pills and pills */
.nija-steps {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 12px 0; }}
.nija-step {{ padding: 8px 14px; border-radius: 999px; background: {SURFACE}; color: {INK}; font-weight: 600;
  border: 2px solid {LINE}; font-size: 0.95rem; }}
.nija-step.done {{ background: #E2F1EE; border-color: {TEAL}; color: {TEAL}; }}
.nija-step.active {{ background: {SAFFRON}; border-color: {SAFFRON}; color: {INK}; }}
.nija-pill {{ display: inline-block; padding: 4px 12px; border-radius: 999px; color: #fff; font-weight: 600; font-size: 0.9rem; }}

/* Metrics, expanders, images */
[data-testid="stMetric"] {{ background: {SURFACE}; border-radius: 16px; padding: 12px 16px; border: 1px solid {LINE};
  box-shadow: 0 2px 10px rgba(20,32,29,.05); }}
[data-testid="stMetricValue"] {{ color: {TEAL}; font-weight: 800; }}
[data-testid="stExpander"] details {{ border-radius: 14px; background: {SURFACE}; border-color: {LINE}; }}
img {{ border-radius: 12px; }}
[role="tab"][aria-selected="true"] {{ color: {TEAL}; }}

/* Phones: stack columns, shrink hero and badge */
@media (max-width: 640px) {{
  .block-container {{ padding-left: 0.8rem; padding-right: 0.8rem; padding-top: 3.8rem; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 0.6rem; }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 100% !important; flex: 1 1 100% !important; }}
  .nija-hero {{ padding: 18px 16px; border-radius: 18px; }}
  .nija-hero h1 {{ font-size: 1.7rem; }}
  .nija-verdict {{ font-size: 1.5rem; padding: 12px 18px; width: 100%; justify-content: center; }}
  .nija-step {{ padding: 5px 10px; font-size: 0.85rem; }}
  /* header: stacked rows (brand, role, language), not sticky, so it does not eat the small screen */
  [data-testid="stLayoutWrapper"]:has(> .st-key-nija_header) {{ position: static; }}
  .st-key-nija_header [data-testid="stHorizontalBlock"] {{ gap: 0.3rem; }}
  iframe[data-testid="stIFrame"] {{ height: 330px !important; }}
  iframe[title="nija_voice"] {{ height: 70px !important; }}
  [role="tablist"] {{ flex-wrap: wrap; row-gap: 4px; }}
  [role="tab"][aria-selected="true"] {{ background: #E2F1EE; border-radius: 10px; }}
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, promise):
    st.markdown(
        f"<div class='nija-hero'><div class='nija-flag'></div><h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(promise)}</p></div>",
        unsafe_allow_html=True,
    )


def card(body_html, title=None, accent=TEAL):
    head = f"<h4>{html.escape(title)}</h4>" if title else ""
    st.markdown(f"<div class='nija-card' style='border-left-color:{accent}'>{head}{body_html}</div>", unsafe_allow_html=True)


def verdict_badge(verdict, label=None, sub=None):
    """label = verdict text in the chosen language (defaults to the English verdict)."""
    bg, fg = VERDICT_COLOURS[verdict]
    extra = f"<small>{html.escape(sub)}</small>" if sub else ""
    st.markdown(
        f"<div class='nija-verdict' style='background:{bg};color:{fg}'>{html.escape(label or verdict)}{extra}</div>",
        unsafe_allow_html=True,
    )


def step_pills(steps, active=None, done=()):
    items = []
    for i, s in enumerate(steps):
        cls = "active" if i == active else ("done" if i in done else "")
        items.append(f"<span class='nija-step {cls}'>{html.escape(s)}</span>")
    st.markdown(f"<div class='nija-steps'>{''.join(items)}</div>", unsafe_allow_html=True)


def pill(text, tone="info"):
    return f"<span class='nija-pill' style='background:{TONES.get(tone, TEAL)}'>{html.escape(text)}</span>"
