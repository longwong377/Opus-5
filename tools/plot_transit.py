#!/usr/bin/env python3
"""Plot the rim-to-axis transit profile: gravity, Coriolis, tangential speed.

The core shuttle transfer is the station's most distinctive interior journey
and none of it is visible in a still. Plotting it is how the ride gets designed.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station/physics"))

import yaml
from core_shuttle import RadialTransit, comfortable_duration
from rotating_frame import from_schema

W, H, PAD = 1400, 620, 70


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=133.0)
    a = ap.parse_args()

    schema = yaml.safe_load(open(os.path.join(ROOT, "station/schema/station.yaml")))
    drum = from_schema(schema)
    R = drum.floor_radius
    tr = RadialTransit(drum, R, 0.0, a.duration)
    prof = tr.profile(240)

    img = Image.new("RGB", (W, H), (12, 14, 20))
    d = ImageDraw.Draw(img)
    x0, x1 = PAD, W - PAD
    y0, y1 = PAD, H - PAD - 30

    for i in range(6):
        y = y0 + (y1 - y0) * i / 5
        d.line([(x0, y), (x1, y)], fill=(34, 38, 48))
        d.text((10, y - 6), f"{1.0 - i*0.2:.1f}", fill=(110, 120, 138))

    def px(p, key, lo, hi):
        return [(x0 + (x1 - x0) * s["t"] / a.duration,
                 y1 - (y1 - y0) * (s[key] - lo) / (hi - lo)) for s in p]

    # Coriolis is signed (negative = spinward). Magnitude is what a rider feels
    # and what the comfort limit is set against, so plot |a| and say so.
    for s in prof:
        s["coriolis_mag"] = abs(s["coriolis_g"])
    # Gravity and tangential speed are both linear in radius, so normalised to
    # full scale they trace exactly the same curve. Drawn dashed underneath
    # rather than hidden -- the coincidence is the point.
    d.line(px(prof, "tangential_m_s", 0, drum.floor_speed), fill=(70, 130, 90), width=7)
    d.line(px(prof, "gravity_g", 0, 1), fill=(120, 200, 255), width=3)
    d.line(px(prof, "coriolis_mag", 0, 1), fill=(255, 168, 72), width=3)

    d.text((PAD, 20), f"Rim to axis in {a.duration:.0f} s   "
                      f"({R:.0f} m radial, {drum.floor_speed:.1f} m/s tangential to shed)",
           fill=(226, 232, 244))
    d.text((PAD, 40), "gravity (1 g full scale)", fill=(120, 200, 255))
    d.text((PAD + 210, 40), f"|Coriolis| (peak {tr.peak_lateral_g():.3f} g)",
           fill=(255, 168, 72))
    d.text((PAD + 470, 40),
           "tangential speed, same scale -- identical to gravity, both linear in radius",
           fill=(70, 150, 100))
    d.text((x0, H - 46), "t = 0  (rim, 1 g)", fill=(140, 150, 170))
    d.text((x1 - 150, H - 46), "t = end  (axis, 0 g)", fill=(140, 150, 170))
    img.save(a.out)
    print(f"{a.out}  peak lateral {tr.peak_lateral_g():.4f} g over {a.duration:.0f} s")


if __name__ == "__main__":
    main()
