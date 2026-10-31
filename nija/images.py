"""Loads a photo once, fixes phone rotation from EXIF, and downsizes it for fast OpenCV work.
Every module gets the same BGR numpy image from here, so they all see identical pixels."""

import cv2
import numpy as np
from PIL import Image, ImageOps

from . import config


def load_bgr(path, max_side=None):
    max_side = max_side or config.MAX_SIDE
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((max_side, max_side))
        rgb = np.asarray(im)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def load_pil(path):
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")
