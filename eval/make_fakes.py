"""Builds SYNTHETIC fake closures from the real pairs in data/pairs, saved to data/pairs_fake/<id>_<attack>/ with label "unverifiable".
Attacks: reused (before photo re-sent as after), screen (after photo shown on a simulated monitor), otherplace (after photo of another pair)."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import cv2
import imagehash
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nija import config  # noqa: E402
from nija.images import load_pil  # noqa: E402
from nija.reinspect import list_pairs  # noqa: E402


def save_like(src_path, bgr, out_path, quality=88):
    """Save a BGR image as JPEG, keeping the source photo's EXIF (as a fraudster's file would)."""
    with Image.open(src_path) as src:
        exif = src.info.get("exif", b"")
    Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(out_path, quality=quality, exif=exif)


def simulate_screen(bgr):
    """Show the image on an RGB sub-pixel grid, photograph it at a slight angle -> moire. Synthetic, not a real screen shot."""
    big = cv2.resize(bgr, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST).astype(np.float32)
    grid = np.zeros_like(big)
    for c in range(3):
        grid[:, (2 - c)::3, c] = 1.0
    grid[2::3, :, :] *= 0.35
    shot = big * grid * 1.6
    M = cv2.getRotationMatrix2D((shot.shape[1] / 2, shot.shape[0] / 2), 2.5, 1.0)
    shot = cv2.warpAffine(shot, M, (shot.shape[1], shot.shape[0]))
    shot = cv2.resize(shot, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(shot, 0, 255).astype(np.uint8)


def write_pair(out_dir, before_src, after_bgr, after_src, attack, src_label):
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(before_src, out_dir / "before.jpg")
    save_like(after_src, after_bgr, out_dir / "after.jpg")
    label = {"label": "unverifiable", "type": src_label.get("type", ""), "synthetic": True,
             "note": f"synthetic fake: {attack}, built from {before_src.parent.name}"}
    (out_dir / "label.json").write_text(json.dumps(label, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pairs", type=Path, default=config.PAIRS_DIR)
    ap.add_argument("--out", type=Path, default=config.DATA_DIR / "pairs_fake")
    args = ap.parse_args()

    pairs = list_pairs(args.pairs)
    if not pairs:
        sys.exit(f"No pairs in {args.pairs}. Add data/pairs/<id>/before.jpg + after.jpg first.")
    if args.out.exists():
        shutil.rmtree(args.out)

    hashes = {p.name: imagehash.phash(load_pil(p / "before.jpg")) for p in pairs}
    made = 0
    for d in pairs:
        try:
            label = json.loads((d / "label.json").read_text())
        except (OSError, ValueError):
            label = {}
        before, after = d / "before.jpg", d / "after.jpg"
        # 1. reused: the old before photo, re-encoded and slightly resized, sent as the "after"
        b = cv2.imread(str(before))
        b = cv2.resize(b, None, fx=0.9, fy=0.9, interpolation=cv2.INTER_AREA)
        write_pair(args.out / f"{d.name}_reused", before, b, before, "reused old photo", label)
        # 2. screen: the real after photo, photographed off a (simulated) monitor
        write_pair(args.out / f"{d.name}_screen", before, simulate_screen(cv2.imread(str(after))), after, "photo of a screen", label)
        made += 2
        # 3. otherplace: the after photo from the pair that looks most different (pHash of before photos)
        if len(pairs) > 1:
            h = hashes[d.name]
            other = max((p for p in pairs if p != d), key=lambda p: h - hashes[p.name]) / "after.jpg"
            write_pair(args.out / f"{d.name}_otherplace", before, cv2.imread(str(other)), other, "different place", label)
            made += 1
    print(f"Made {made} SYNTHETIC fakes from {len(pairs)} pairs in {args.out}")


if __name__ == "__main__":
    main()
