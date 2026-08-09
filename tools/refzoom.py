#!/usr/bin/env python3
"""Crop and upscale regions of a reference image so fine detail becomes legible.

Reference material is mostly low-resolution screencaps and scanned schematics.
Reading dimensions and labels off them requires magnifying specific regions.

Usage:
    refzoom.py <image> [--grid ROWS COLS] [--box L T R B] [--scale N] [--out DIR]

    --grid  split the image into a grid and emit every cell (default 2x2)
    --box   crop one region, given in fractions of width/height (0..1)
    --scale upscale factor (default: auto, targets ~1600px on the long edge)
"""
import argparse
import os
import sys

from PIL import Image, ImageEnhance

OUT_DEFAULT = "/tmp/claude-0/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/scratchpad/zoom"
TARGET_LONG_EDGE = 1600
MAX_LONG_EDGE = 2400


def enhance(img):
    """Sharpen and lift contrast a little -- schematic scans respond well."""
    img = ImageEnhance.Contrast(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.6)
    return img


def emit(img, box, path, scale=None):
    w, h = img.size
    l, t, r, b = box
    crop = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    cw, ch = crop.size
    if cw == 0 or ch == 0:
        return None
    if scale is None:
        scale = max(1.0, min(TARGET_LONG_EDGE / max(cw, ch), MAX_LONG_EDGE / max(cw, ch)))
    crop = crop.resize((int(cw * scale), int(ch * scale)), Image.LANCZOS)
    crop = enhance(crop)
    crop.save(path)
    return path, crop.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--grid", nargs=2, type=int, metavar=("ROWS", "COLS"))
    ap.add_argument("--box", nargs=4, type=float, metavar=("L", "T", "R", "B"))
    ap.add_argument("--scale", type=float)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    img = Image.open(args.image, encoding="utf-8").convert("RGB")
    stem = args.tag or os.path.splitext(os.path.basename(args.image))[0]
    stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    print(f"source: {args.image}  {img.size[0]}x{img.size[1]}")

    if args.box:
        p = emit(img, args.box, os.path.join(args.out, f"{stem}_box.png"), args.scale)
        print(f"{p[0]}  {p[1][0]}x{p[1][1]}")
        return

    rows, cols = args.grid if args.grid else (2, 2)
    # Overlap cells slightly so nothing important lands exactly on a seam.
    ov = 0.04
    for r in range(rows):
        for c in range(cols):
            box = (
                max(0.0, c / cols - ov),
                max(0.0, r / rows - ov),
                min(1.0, (c + 1) / cols + ov),
                min(1.0, (r + 1) / rows + ov),
            )
            path = os.path.join(args.out, f"{stem}_r{r}c{c}.png")
            res = emit(img, box, path, args.scale)
            if res:
                print(f"{res[0]}  {res[1][0]}x{res[1][1]}")


if __name__ == "__main__":
    sys.exit(main())
