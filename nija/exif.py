"""Reads capture time, GPS position and compass heading from a photo's EXIF, if the phone saved them.
Missing fields come back as None; the gates treat "no data" as unknown, never as a pass or a fail."""

import math
from datetime import datetime

from PIL import Image

EXIF_IFD = 0x8769
GPS_IFD = 0x8825
DATETIME_ORIGINAL = 0x9003
DATETIME = 0x0132


def _to_degrees(dms, ref):
    d, m, s = (float(x) for x in dms)
    deg = d + m / 60 + s / 3600
    return -deg if ref in ("S", "W") else deg


def read_exif(path):
    info = {"timestamp": None, "lat": None, "lon": None, "heading": None}
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            sub = exif.get_ifd(EXIF_IFD)
            gps = exif.get_ifd(GPS_IFD)
    except Exception:
        return info

    raw = sub.get(DATETIME_ORIGINAL) or exif.get(DATETIME)
    if raw:
        try:
            info["timestamp"] = datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

    try:
        if gps.get(2) and gps.get(4):
            info["lat"] = _to_degrees(gps[2], gps.get(1, "N"))
            info["lon"] = _to_degrees(gps[4], gps.get(3, "E"))
        if gps.get(17) is not None:
            info["heading"] = float(gps[17])
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    return info


def gps_distance_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
