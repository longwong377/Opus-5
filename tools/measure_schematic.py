#!/usr/bin/env python3
"""Measure a scaled orthographic schematic in real-world units.

Given a schematic with a known scale bar, calibrate pixels-per-metre and then
report the station silhouette: per-column vertical extent, section boundaries,
and radii. Emits an annotated overlay so the calibration can be eyeballed.

The Contract 5 sheet is line art on white, so "ink" is simply dark pixels.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw

SCRATCH = "/tmp/claude-0/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/scratchpad/zoom"
INK_THRESHOLD = 128


def ink_mask(img, box=None):
    a = np.asarray(img.convert("L"), dtype=np.uint8)
    if box:
        l, t, r, b = box
        a = a[t:b, l:r]
    return a < INK_THRESHOLD


def column_extents(mask, min_ink=1):
    """For each column, the topmost and bottommost ink row (None if empty)."""
    out = []
    for c in range(mask.shape[1]):
        rows = np.flatnonzero(mask[:, c])
        if rows.size >= min_ink:
            out.append((c, int(rows[0]), int(rows[-1])))
        else:
            out.append((c, None, None))
    return out


def find_scalebar_ticks(mask, row_band):
    """Locate vertical tick marks in a horizontal band (the scale bar)."""
    t0, t1 = row_band
    band = mask[t0:t1, :]
    density = band.sum(axis=0)
    thresh = max(2, int(band.shape[0] * 0.45))
    cols = np.flatnonzero(density >= thresh)
    # Cluster adjacent columns into single ticks.
    ticks, run = [], []
    for c in cols:
        if run and c - run[-1] > 3:
            ticks.append(int(np.mean(run)))
            run = []
        run.append(int(c))
    if run:
        ticks.append(int(np.mean(run)))
    return ticks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--scalebar-band", nargs=2, type=int, required=True,
                    metavar=("TOP", "BOT"), help="pixel rows containing the scale bar")
    ap.add_argument("--scalebar-km", type=float, required=True,
                    help="total km spanned from first tick to last tick")
    ap.add_argument("--profile-box", nargs=4, type=int, required=True,
                    metavar=("L", "T", "R", "B"), help="pixel box of the profile view")
    ap.add_argument("--axis-row", type=int, help="pixel row of the station centreline")
    ap.add_argument("--tag", default="measured")
    args = ap.parse_args()

    img = Image.open(args.image, encoding="utf-8").convert("RGB")
    W, H = img.size
    full = ink_mask(img)

    ticks = find_scalebar_ticks(full, args.scalebar_band)
    if len(ticks) < 2:
        raise SystemExit(f"scale bar: found {len(ticks)} ticks, need >= 2")
    px_per_km = (ticks[-1] - ticks[0]) / args.scalebar_km
    px_per_m = px_per_km / 1000.0
    origin_px = ticks[0]

    def to_m(px):
        return (px - origin_px) / px_per_m

    l, t, r, b = args.profile_box
    prof = ink_mask(img, (l, t, r, b))
    ext = column_extents(prof, min_ink=2)
    cols = [(c, hi, lo) for c, hi, lo in ext if hi is not None]
    if not cols:
        raise SystemExit("no ink found in profile box")

    nose_px = l + cols[-1][0]
    tail_px = l + cols[0][0]
    axis_row = args.axis_row if args.axis_row else t + int(np.mean([(hi + lo) / 2 for _, hi, lo in cols]))

    # Half-height (radius) profile along the station's long axis.
    radii = []
    for c, hi, lo in cols:
        top_abs, bot_abs = t + hi, t + lo
        rad_px = max(abs(axis_row - top_abs), abs(bot_abs - axis_row))
        radii.append({
            "x_m": round(to_m(l + c), 1),
            "radius_m": round(rad_px / px_per_m, 1),
        })

    report = {
        "image": os.path.basename(args.image),
        "image_size": [W, H],
        "scalebar": {
            "ticks_px": ticks,
            "n_ticks": len(ticks),
            "px_per_km": round(px_per_km, 3),
            "km_per_tick": round(args.scalebar_km / (len(ticks) - 1), 3),
        },
        "axis_row_px": axis_row,
        "station": {
            "tail_m": round(to_m(tail_px), 1),
            "nose_m": round(to_m(nose_px), 1),
            "overall_length_m": round(to_m(nose_px) - to_m(tail_px), 1),
            "max_radius_m": round(max(x["radius_m"] for x in radii), 1),
        },
        "radius_profile": radii,
    }

    os.makedirs(SCRATCH, exist_ok=True)
    jpath = os.path.join(SCRATCH, f"{args.tag}.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # Annotated overlay: km grid + centreline + measured extents.
    ov = img.copy()
    d = ImageDraw.Draw(ov)
    for km in range(0, int(args.scalebar_km) + 1):
        x = origin_px + km * px_per_km
        d.line([(x, 0), (x, H)], fill=(255, 0, 0), width=1)
        d.text((x + 2, 2), f"{km}", fill=(255, 0, 0))
    d.line([(0, axis_row), (W, axis_row)], fill=(0, 160, 255), width=1)
    d.rectangle([l, t, r, b], outline=(0, 200, 0), width=2)
    d.line([(tail_px, t), (tail_px, b)], fill=(255, 0, 255), width=2)
    d.line([(nose_px, t), (nose_px, b)], fill=(255, 0, 255), width=2)
    opath = os.path.join(SCRATCH, f"{args.tag}_overlay.png")
    ov.resize((W * 2, H * 2), Image.LANCZOS).save(opath)

    print(json.dumps({k: v for k, v in report.items() if k != "radius_profile"}, indent=1))
    print(f"\noverlay: {opath}\njson:    {jpath}")


if __name__ == "__main__":
    main()
