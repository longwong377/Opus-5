#!/usr/bin/env python3
"""What each lever is worth on the drum, measured one variable at a time.

Every row re-runs budget.py's own 4 x 3 lattice through the counting paths that
`drum_probe.py --verify` proved agree with `export_scene.drum_parts` exactly.
One knob moves per row.
"""
import argparse
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

BUDGET = B.DRUM["visible_set_tris"]


def sweep(fixed, stations=4, zs=3):
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    rows = []
    for ang, z, eye in B.drum_eyes(schema, profile, sector, stations, zs):
        g, _ = dg.visible_cost(eye)
        d, _ = dd.dressing_cost(eye)
        rows.append((fixed + g + d, ang, z, g, d))
    rows.sort(reverse=True)
    return rows


def reset_ground_caches():
    dg._LOD_CACHE.clear()


def row(label, fixed=None):
    fixed = dd.DRUM_FIXED_TRIS if fixed is None else fixed
    rows = sweep(fixed)
    t, ang, z, g, d = rows[0]
    print(f"{label:<46} {t:8,}  {t/BUDGET*100:6.1f}%   "
          f"fixed {fixed:7,} ground {g:7,} dress {d:7,}  @({ang:.0f},{z:.0f})")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="all")
    a = ap.parse_args()

    print(f"budget {BUDGET:,}   worst of a 4 x 3 lattice\n")
    print(f"{'lever':<46} {'total':>8}  {'of budget':>7}")
    print("-" * 110)
    base = row("BASELINE (committed)")

    if a.which in ("all", "fov"):
        # THE SCREEN MODEL. lod.py/drum_ground/drum_dressing resolve LOD for a
        # 50 deg vertical camera; player.gd line 279 sets 70.0 and budget.DECK
        # states 70.0. One knob, three values.
        for fov in (55.0, 60.0, 70.0, 75.0):
            dg.FOV_DEG = fov
            dd.FOV_DEG = fov
            reset_ground_caches()
            row(f"  screen model FOV {fov:.0f} deg (was 50)")
        dg.FOV_DEG = dd.FOV_DEG = 50.0
        reset_ground_caches()

    if a.which in ("all", "pixel"):
        base_px = dg.PIXEL_BUDGET
        for px in (2.0, 3.0):
            dg.PIXEL_BUDGET = px
            reset_ground_caches()
            row(f"  ground PIXEL_BUDGET {px} px (was {base_px})")
        dg.PIXEL_BUDGET = base_px
        reset_ground_caches()

    if a.which in ("all", "lod_scale"):
        base_scale = dd.LOD_SCALE_M
        for s in (90.0, 100.0, 113.0):
            dd.LOD_SCALE_M = s
            row(f"  dressing LOD_SCALE_M {s:.0f} (was {base_scale:.0f})")
        dd.LOD_SCALE_M = base_scale

    if a.which in ("all", "fixed"):
        # WHAT THE FIXED PARTS ARE WORTH IF THEY HAD A LADDER AT ALL. Not a
        # proposal -- a bound. Each row deletes a part outright to price it.
        _tot, per = dd.drum_fixed_cost()
        for k in sorted(per, key=lambda k_: -per[k_]):
            row(f"  fixed part '{k}' removed entirely",
                dd.DRUM_FIXED_TRIS - per[k])


if __name__ == "__main__":
    main()
