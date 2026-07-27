#!/usr/bin/env python3
"""Render a flight trajectory over the station silhouette.

Numbers prove the flight model is correct; a picture shows whether it is
plausible. This plots a simulated path against the real hull profile so a
launch or docking approach can be judged by eye.
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station/physics"))

import yaml
from rotating_frame import from_schema
from starfury import Starfury

W, H = 1500, 760
MARGIN = 60


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--dt", type=float, default=0.05)
    a = ap.parse_args()

    schema = yaml.safe_load(open(os.path.join(ROOT, "station/schema/station.yaml")))
    profile = json.load(open(os.path.join(ROOT, "station/schema/radius_profile.json")))["profile"]
    drum = from_schema(schema)

    craft = Starfury()
    launch_z = 5400.0
    craft.launch_from_drum(drum, drum.floor_radius, launch_z)
    path = []
    for i in range(int(a.seconds / a.dt)):
        craft.step(a.dt)
        path.append((craft.position[2], math.hypot(craft.position[0], craft.position[1])))

    max_r = max(max(p[1] for p in path), 1200.0)
    span_z = 8047.0
    sx = (W - 2 * MARGIN) / span_z
    sy = (H / 2 - MARGIN) / max_r

    img = Image.new("RGB", (W, H), (10, 12, 18))
    d = ImageDraw.Draw(img)
    cy = H / 2

    # Hull silhouette, both halves.
    pts_u, pts_l = [], []
    for p in profile[::4]:
        x = MARGIN + p["z_m"] * sx
        r = p["radius_m"] * sy
        pts_u.append((x, cy - r))
        pts_l.append((x, cy + r))
    d.polygon(pts_u + pts_l[::-1], fill=(52, 58, 70), outline=(96, 104, 120))
    d.line([(MARGIN, cy), (W - MARGIN, cy)], fill=(60, 66, 80))

    # Trajectory.
    tp = [(MARGIN + z * sx, cy - r * sy) for z, r in path]
    d.line(tp, fill=(255, 176, 64), width=3)
    d.ellipse([tp[0][0] - 6, tp[0][1] - 6, tp[0][0] + 6, tp[0][1] + 6],
              fill=(120, 255, 140))
    d.ellipse([tp[-1][0] - 6, tp[-1][1] - 6, tp[-1][0] + 6, tp[-1][1] + 6],
              fill=(255, 96, 96))

    d.text((MARGIN, 16),
           f"Cobra bay launch at z={launch_z:.0f} m, unpowered, {a.seconds:.0f} s",
           fill=(220, 226, 240))
    d.text((MARGIN, 34),
           f"inherited {drum.floor_speed:.1f} m/s from the drum   "
           f"final radius {path[-1][1]:.0f} m   "
           f"scale: station {span_z:.0f} m long",
           fill=(150, 160, 180))
    img.save(a.out)
    print(f"{a.out}  final radius {path[-1][1]:.0f} m after {a.seconds:.0f} s")


if __name__ == "__main__":
    main()
