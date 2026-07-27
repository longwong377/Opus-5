#!/usr/bin/env python3
"""Emit magnified, grid-calibrated segments of an orthographic schematic.

A single full-width pass over a 2000px schematic is not precise enough to read
section boundaries. This splits the drawing into overlapping windows, each
magnified with a fine calibrated grid, so transitions can be read individually.

Calibration comes from station/schema/station.yaml (OW-001).
"""
import argparse
import os

from PIL import Image, ImageDraw

SCRATCH = "/tmp/claude-0/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/scratchpad/zoom"

# Calibration for reference/02-station-cutaways-and-plans/other map 4.jpg
TAIL_PX = 71
NOSE_PX = 2048
AXIS_PY = 388
MILLER_L = 3108.0
DRAW_TOP, DRAW_BOT = 150, 600


def build(image, seg_start, seg_end, minor, major, scale, tag):
    im = Image.open(image).convert("RGB")
    pxm = (NOSE_PX - TAIL_PX) / MILLER_L
    d = ImageDraw.Draw(im)

    m = 0.0
    while m <= MILLER_L:
        x = TAIL_PX + m * pxm
        is_major = abs(m % major) < 1e-6
        d.line([(x, DRAW_TOP), (x, DRAW_BOT)],
               fill=(255, 0, 0) if is_major else (255, 170, 170),
               width=2 if is_major else 1)
        if is_major:
            d.text((x + 3, DRAW_TOP + 2), f"{int(m)}", fill=(255, 0, 0))
        m += minor

    d.line([(0, AXIS_PY), (im.size[0], AXIS_PY)], fill=(0, 160, 255), width=1)

    l = int(TAIL_PX + seg_start * pxm)
    r = int(TAIL_PX + seg_end * pxm)
    crop = im.crop((max(0, l), DRAW_TOP, min(im.size[0], r), DRAW_BOT))
    cw, ch = crop.size
    crop = crop.resize((int(cw * scale), int(ch * scale)), Image.LANCZOS)
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, f"{tag}.png")
    crop.save(path)
    print(f"{path}  {crop.size[0]}x{crop.size[1]}  "
          f"miller {seg_start:.0f}-{seg_end:.0f} m  (real {seg_start*2.5891:.0f}-{seg_end*2.5891:.0f} m)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image",
                    default="/home/user/Opus-5/reference/02-station-cutaways-and-plans/other map 4.jpg")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--minor", type=float, default=50.0)
    ap.add_argument("--major", type=float, default=200.0)
    ap.add_argument("--scale", type=float, default=3.0)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    build(a.image, a.start, a.end, a.minor, a.major, a.scale, a.tag)


if __name__ == "__main__":
    main()
