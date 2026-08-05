#!/usr/bin/env python3
"""Measure named regions of a reference or rendered frame.

Session 4r. Written because every number the window work turns on has to be a
measurement of a frame rather than a preference, and because `measure_frame.py`
answers a whole-frame question while this one asks "how bright is THAT bit".

Linear luminance is Rec.709 on sRGB-decoded channels, which is what
`tools/measure_frame.py` uses, so the two are comparable.

    python3 scratchpad/vista_measure.py IMAGE name=l,t,r,b [name=...]
"""
import sys

from PIL import Image


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def stats(img, box):
    w, h = img.size
    l, t, r, b = box
    crop = img.crop((int(l * w), int(t * h), max(int(r * w), int(l * w) + 1),
                     max(int(b * h), int(t * h) + 1))).convert("RGB")
    px = list(crop.getdata())
    ys, rs, gs, bs = [], [], [], []
    for (R, G, B) in px:
        lr, lg, lb = srgb_to_linear(R), srgb_to_linear(G), srgb_to_linear(B)
        ys.append(0.2126 * lr + 0.7152 * lg + 0.0722 * lb)
        rs.append(lr)
        gs.append(lg)
        bs.append(lb)
    ys.sort()
    n = len(ys)
    return {"n": n, "mean_Y": sum(ys) / n, "p50_Y": ys[n // 2],
            "p05_Y": ys[int(0.05 * n)], "p95_Y": ys[int(0.95 * n)],
            "mean_rgb": (sum(rs) / n, sum(gs) / n, sum(bs) / n)}


def main(argv):
    img = Image.open(argv[0])
    print(f"{argv[0]}  {img.size[0]}x{img.size[1]}")
    for spec in argv[1:]:
        name, _, nums = spec.partition("=")
        box = tuple(float(v) for v in nums.split(","))
        s = stats(img, box)
        print(f"  {name:<22} n={s['n']:<7} meanY={s['mean_Y']:.4f} "
              f"p50={s['p50_Y']:.4f} p05={s['p05_Y']:.4f} p95={s['p95_Y']:.4f} "
              f"rgb=({s['mean_rgb'][0]:.4f},{s['mean_rgb'][1]:.4f},"
              f"{s['mean_rgb'][2]:.4f})")


if __name__ == "__main__":
    main(sys.argv[1:])
