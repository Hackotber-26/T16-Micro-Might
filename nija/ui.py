"""Design system for the Streamlit app: colour tokens, CSS (fonts, cards, 44 px tap targets, mobile stacking) and small HTML helpers.
Call inject_css() once per page run, then use hero(), card(), verdict_badge(), step_pills() and pill() to build the screen."""

import html

import streamlit as st

# Colour tokens
YELLOW = "#FFC20E"  # Karnataka yellow (accent)
RED = "#D32F2F"  # Karnataka red (accent)
TEAL = "#0F5C5C"  # primary
CREAM = "#FFF8E7"  # background
INK = "#1E2623"  # text
VERDICT_COLOURS = {
    "Verified": ("#1E8E3E", "#FFFFFF"),
    "Partial": ("#F2A900", INK),
    "Not fixed": (RED, "#FFFFFF"),
    "Cannot verify": ("#546E7A", "#FFFFFF"),
}
TONES = {"ok": "#1E8E3E", "warn": "#F2A900", "bad": RED, "info": TEAL, "muted": "#546E7A"}

FONT_STACK = '"Noto Sans Kannada", "Nirmala UI", "Tunga", "Noto Sans", "Segoe UI", system-ui, sans-serif'

CSS = f"""
<style>
:root {{
  --nija-yellow: {YELLOW}; --nija-red: {RED}; --nija-teal: {TEAL}; --nija-cream: {CREAM}; --nija-ink: {INK};
}}
html, body, .stApp, .stMarkdown, .stMarkdown p, label, button, input, textarea, select, [data-testid="stMetricValue"] {{
  font-family: {FONT_STACK};
}}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: "Material Symbols Rounded" !important; }}
.stMarkdown p, .stMarkdown li, label, .stCaption {{ font-size: 1rem; line-height: 1.6; }}
.block-container {{ padding-top: 4.2rem; max-width: 1200px; }}

/* Tap targets: at least 44 px high */
.stButton button, .stDownloadButton button, .stLinkButton a, [data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-primary"], button[role="tab"], [data-testid="stSegmentedControl"] button {{
  min-height: 44px; border-radius: 12px; font-weight: 600;
}}
button[role="tab"] {{ padding: 0 14px; font-size: 1rem; }}

/* Sticky header with the language / role toggles */
[data-testid="stLayoutWrapper"]:has(> .st-key-nija_header) {{
  position: sticky; top: 3.75rem; z-index: 50;
}}
.st-key-nija_header {{ background: {CREAM}; padding: 8px 0; border-bottom: 3px solid {YELLOW}; }}
.st-key-nija_header [data-testid="stSegmentedControl"] button {{ font-size: 1rem; padding: 0 16px; }}
.st-key-nija_header [aria-checked="true"], .st-key-nija_header button[kind="segmented_controlActive"] {{
  background: {TEAL} !important; color: #fff !important;
}}

/* Hero banner */
.nija-hero {{
  background: linear-gradient(120deg, {TEAL} 0%, #137272 55%, #1b8a7a 100%);
  color: #fff; border-radius: 20px; padding: 22px 26px; margin: 4px 0 14px 0;
  border-bottom: 6px solid {YELLOW}; box-shadow: 0 6px 20px rgba(15, 92, 92, 0.18);
}}
.nija-hero h1 {{ color: #fff; font-size: 2.2rem; margin: 0; line-height: 1.2; padding: 0; }}
.nija-hero .nija-flag {{ display: inline-block; width: 42px; height: 8px; border-radius: 4px; margin-bottom: 10px;
  background: linear-gradient(90deg, {YELLOW} 50%, {RED} 50%); }}
.nija-hero p {{ color: #E9F5F3; font-size: 1.08rem; margin: 6px 0 0 0; }}

/* Cards */
.nija-card {{
  background: #fff; border-radius: 16px; padding: 16px 18px; margin: 8px 0;
  box-shadow: 0 2px 10px rgba(30, 38, 35, 0.08); border-left: 6px solid {TEAL};
}}
.nija-card h4 {{ margin: 0 0 6px 0; color: {TEAL}; }}

/* Verdict badge */
.nija-verdict {{
  display: inline-flex; align-items: center; gap: 12px; padding: 14px 26px; border-radius: 16px;
  font-size: 2rem; font-weight: 800; letter-spacing: 0.2px; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  margin-bottom: 12px;
}}
.nija-verdict small {{ font-size: 1rem; font-weight: 600; opacity: 0.9; }}

/* Step pills and pills */
.nija-steps {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 12px 0; }}
.nija-step {{ padding: 8px 14px; border-radius: 999px; background: #fff; color: {INK}; font-weight: 600;
  border: 2px solid #E6DCC3; font-size: 0.95rem; }}
.nija-step.done {{ background: #E3F1EF; border-color: {TEAL}; color: {TEAL}; }}
.nija-step.active {{ background: {YELLOW}; border-color: {YELLOW}; color: {INK}; }}
.nija-pill {{ display: inline-block; padding: 4px 12px; border-radius: 999px; color: #fff; font-weight: 600; font-size: 0.9rem; }}

/* Metrics look like cards */
[data-testid="stMetric"] {{ background: #fff; border-radius: 14px; padding: 10px 14px; box-shadow: 0 2px 8px rgba(30,38,35,.06); }}
[data-testid="stExpander"] details {{ border-radius: 14px; background: #fff; }}
img {{ border-radius: 10px; }}

/* Phones: stack columns, shrink hero and badge */
@media (max-width: 640px) {{
  .block-container {{ padding-left: 0.8rem; padding-right: 0.8rem; }}
  [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 0.6rem; }}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 100% !important; flex: 1 1 100% !important; }}
  .nija-hero {{ padding: 16px 16px; border-radius: 16px; }}
  .nija-hero h1 {{ font-size: 1.6rem; }}
  .nija-verdict {{ font-size: 1.5rem; padding: 12px 18px; width: 100%; justify-content: center; }}
  .nija-step {{ padding: 5px 10px; font-size: 0.85rem; }}
  iframe[data-testid="stIFrame"] {{ height: 330px !important; }}  /* before/after slider: no blank space on phones */
  /* keep the sticky header on one row */
  .st-key-nija_header [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap; }}
  .st-key-nija_header [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 auto !important; }}
  .block-container {{ padding-top: 3.8rem; }}
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
