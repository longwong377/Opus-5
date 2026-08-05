#!/usr/bin/env python3
"""What per-patch LOD error is worth, on budget.py's own 4 x 3 lattice.

Reads the table `per_patch_error.py` measured. Changes nothing about the
criterion -- still 1.5 px of deviation at the screen model -- only its domain.
"""
import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import interior as it          # noqa: E402
import drum_ground as dg       # noqa: E402
import drum_dressing as dd     # noqa: E402
import budget as B             # noqa: E402

TBL = json.load(open(os.path.join(ROOT, "scratchpad", "per-patch-error.json")))
PER = TBL["per_patch"]
PT = TBL["patch_triangles"]


def scale_switch(sw, fov_from, fov_to):
    k = (math.tan(math.radians(fov_from) / 2.0)
         / math.tan(math.radians(fov_to) / 2.0))
    return [x * k for x in sw]


def level_for(sw, d):
    lvl = 0
    for i, s in enumerate(sw):
        if d >= s:
            lvl = i
    return lvl


def cost(eye, mode, fov, cap=None):
    tot = 0
    per_level = [0] * 5
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            d = dg.patch_nearest_distance(pa, pz, eye)
            if mode == "drum":
                sw = scale_switch(TBL["drum_wide_switch_m"], TBL["fov_deg"], fov)
            else:
                sw = scale_switch(PER[f"{pa},{pz}"]["switch_m"],
                                  TBL["fov_deg"], fov)
            lvl = level_for(sw, d)
            if cap is not None:
                lvl = min(lvl, cap)
            tot += PT[lvl]
            per_level[lvl] += 1
    return tot, per_level


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fov", type=float, nargs="*",
                    default=[50.0, 70.0])
    a = ap.parse_args()
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    eyes = B.drum_eyes(schema, profile, sector, B.DRUM["stations"],
                       B.DRUM["z_stations"])
    print(f"{'variant':<44} {'worst ground':>12} {'worst frame':>12} "
          f"{'of budget':>10}")
    print("-" * 84)
    for fov in a.fov:
        for mode in ("drum", "patch"):
            worst = (0, None, None)
            for ang, z, eye in eyes:
                g, per = cost(eye, mode, fov)
                d, _ = dd.dressing_cost(eye)
                t = dd.DRUM_FIXED_TRIS + g + d
                if t > worst[0]:
                    worst = (t, g, (ang, z), per)
            label = (f"error per {'DRUM (ships)' if mode=='drum' else 'PATCH'}"
                     f", screen model {fov:.0f} deg")
            print(f"{label:<44} {worst[1]:12,} {worst[0]:12,} "
                  f"{worst[0]/B.DRUM['visible_set_tris']*100:9.1f}%"
                  f"   patches/level {worst[3]}")


if __name__ == "__main__":
    main()
