"""Everything around a result that is not the verdict: location context from EXIF, the auditor's evidence pack (ZIP),
citizen "still not fixed" feedback (data/feedback.json) and the browser-side Listen button (Web Speech API, no server)."""

import hashlib
import html
import io
import json
import zipfile
from datetime import datetime

import cv2

from . import config
from .exif import gps_distance_m, read_exif

FEEDBACK_FILE = config.DATA_DIR / "feedback.json"
CORPORATIONS = ["Central", "North", "South", "East", "West"]  # GBA city corporations


def photo_id(photo_bytes):
    """Short stable id for a photo (used to link citizen feedback to a pair)."""
    return hashlib.sha1(photo_bytes).hexdigest()[:12]


def location_context(before_bytes, after_bytes, corporation=None, ward=None):
    """GPS of both photos from EXIF plus the officer-entered corporation / ward (not verified)."""
    b, a = read_exif(io.BytesIO(before_bytes)), read_exif(io.BytesIO(after_bytes))
    gps_b = [round(b["lat"], 6), round(b["lon"], 6)] if b["lat"] is not None else None
    gps_a = [round(a["lat"], 6), round(a["lon"], 6)] if a["lat"] is not None else None
    dist = round(gps_distance_m(*gps_b, *gps_a), 1) if gps_b and gps_a else None
    return {"gps_before": gps_b, "gps_after": gps_a, "distance_m": dist,
            "corporation": corporation or None, "ward": (ward or "").strip() or None,
            "corporation_ward_source": "entered by officer, not verified"}


def evidence_zip(result, images, pair, context):
    """In-memory ZIP: before/after photos, overlays, result JSON with context, and a short README with the time."""
    before_bytes, before_name, after_bytes, after_name = pair
    buf = io.BytesIO()
    stamp = datetime.now().isoformat(timespec="seconds")
    record = {**{k: v for k, v in result.items()}, "context": context, "evidence_created": stamp}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("before" + _ext(before_name), before_bytes)
        z.writestr("after" + _ext(after_name), after_bytes)
        for key in ("before_overlay", "after_overlay", "gate1_matches"):
            if key in images:
                z.writestr(f"{key}.png", cv2.imencode(".png", cv2.cvtColor(images[key], cv2.COLOR_RGB2BGR))[1].tobytes())
        z.writestr("result.json", json.dumps(record, indent=2, ensure_ascii=False, default=str))
        z.writestr("README.txt", f"Nija evidence pack\nCreated: {stamp}\nVerdict: {result['verdict']}  score: {result['score']}\n"
                                 "Verdict comes from classical computer vision checks; notes may be written by Gemma 4.\n"
                                 "Depth is not measured. Corporation and ward are entered by an officer and not verified.\n")
    return buf.getvalue()


def _ext(name):
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name else ".jpg"


def load_feedback():
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def add_feedback(before_bytes, verdict, lang):
    items = load_feedback()
    items.append({"photo_id": photo_id(before_bytes), "verdict_shown": verdict, "lang": lang,
                  "time": datetime.now().isoformat(timespec="seconds"), "says": "still not fixed"})
    FEEDBACK_FILE.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    return len(items)


def feedback_counts():
    counts = {}
    for f in load_feedback():
        counts[f["photo_id"]] = counts.get(f["photo_id"], 0) + 1
    return counts


def listen_html(text, lang_code, fallback_text, labels):
    """Listen button: speaks the text with the browser's own voices (speechSynthesis). If no voice for lang_code
    is installed it says so and reads the English fallback instead. Fully client-side."""
    payload = json.dumps({"text": text, "lang": lang_code, "fallback": fallback_text, **labels})
    return f"""
<div style="font-family:Inter,'Noto Sans Kannada',sans-serif;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
  <button id="say" style="min-height:44px;padding:0 18px;border-radius:12px;border:0;background:#F5B700;color:#14201D;
          font-weight:700;font-size:16px;cursor:pointer">🔊 {html.escape(labels['listen'])}</button>
  <span id="msg" style="color:#5B6B66;font-size:14px"></span>
</div>
<script>
const P = {payload};
const speak = (txt, lang) => {{ const u = new SpeechSynthesisUtterance(txt); u.lang = lang;
  const v = speechSynthesis.getVoices().find(v => v.lang && v.lang.toLowerCase().startsWith(lang.slice(0, 2)));
  if (v) u.voice = v; speechSynthesis.cancel(); speechSynthesis.speak(u); }};
document.getElementById('say').onclick = () => {{
  if (!('speechSynthesis' in window)) {{ document.getElementById('msg').textContent = P.no_speech; return; }}
  const has = speechSynthesis.getVoices().some(v => v.lang && v.lang.toLowerCase().startsWith(P.lang.slice(0, 2)));
  if (has || P.lang.startsWith('en')) {{ speak(P.text, P.lang); document.getElementById('msg').textContent = ''; }}
  else {{ document.getElementById('msg').textContent = P.no_voice; speak(P.fallback, 'en-IN'); }}
}};
speechSynthesis.getVoices();
</script>"""
