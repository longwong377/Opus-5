#!/usr/bin/env python3
"""Is the ground's LOD error a property of the DRUM or of the PATCH?

`drum_ground.lod_error_report` measures the deviation of each stride from lod0
inside `_representative_patches()` -- one patch per land-use band -- takes the
WORST, and applies it to all 280 patches. So the lake pays the settlement
podium's error and the parkland pays the arable's finest noise octave.

The switch criterion (1.5 px of deviation) is unchanged here. Only its DOMAIN
changes: per drum, or per patch. If the drum's terrain is dominated by a noise
field that is present everywhere, per-patch buys nothing and this is a negative
result. If the flat land -- lake, roads, parkland -- is genuinely flatter, it
buys triangles at exactly zero cost in deviation.

Writes the table to scratchpad/per-patch-error.json so the sweep can re-run
without paying for the measurement again.
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

import interior as it          # noqa: E402
import drum_ground as dg       # noqa: E402

OUT = os.path.join(ROOT, "scratchpad", "per-patch-error.json")


def patch_error(pa, pz, stride):
    """Max |true - strided| over the patch's own lod0 lattice, in metres."""
    ia0, iz0 = pa * dg.PATCH_A, pz * dg.PATCH_Z
    coarse = {}
    for ka in range(0, dg.PATCH_A + stride, stride):
        for kz in range(0, dg.PATCH_Z + stride, stride):
            u = ((ia0 + ka) % dg.CELLS_A) / dg.CELLS_A
            w = (iz0 + kz) / dg.CELLS_Z
            coarse[(ka, kz)] = dg.sample(u, w)[0]
    worst = 0.0
    for da in range(dg.PATCH_A + 1):
        for dz in range(dg.PATCH_Z + 1):
            u = ((ia0 + da) % dg.CELLS_A) / dg.CELLS_A
            w = (iz0 + dz) / dg.CELLS_Z
            true_h = dg.sample(u, w)[0]
            ka0 = (da // stride) * stride
            kz0 = (dz // stride) * stride
            ka1 = min(ka0 + stride, dg.PATCH_A)
            kz1 = min(kz0 + stride, dg.PATCH_Z)
            ta = 0.0 if ka1 == ka0 else (da - ka0) / (ka1 - ka0)
            tz = 0.0 if kz1 == kz0 else (dz - kz0) / (kz1 - kz0)
            approx = (coarse[(ka0, kz0)] * (1 - ta) * (1 - tz)
                      + coarse[(ka1, kz0)] * ta * (1 - tz)
                      + coarse[(ka0, kz1)] * (1 - ta) * tz
                      + coarse[(ka1, kz1)] * ta * tz)
            worst = max(worst, abs(true_h - approx))
    # The curvature floor is a property of the drum, not the patch: a chord
    # across an angular facet falls inside the true circle by the sagitta.
    dtheta = 2.0 * math.pi * stride / dg.CELLS_A
    sag = dg.FLOOR_R * (1.0 - math.cos(dtheta / 2.0))
    return max(worst, sag)


def main():
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    tab = dg.lod_table()
    print("drum-wide table (what ships):")
    for i, r in enumerate(tab):
        print(f"  stride {dg.STRIDES[i]:2d}  switch {r['switch_distance_m']:8.1f} m"
              f"  {r['patch_triangles']:6,} tri/patch")

    t0 = time.time()
    per = {}
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            errs = [patch_error(pa, pz, s) for s in dg.STRIDES]
            # Monotonic by construction, exactly as lod_table does it.
            d, sw = 0.0, []
            for e in errs:
                d = max(d, dg._switch_distance(e))
                sw.append(d)
            per[f"{pa},{pz}"] = {"err_m": [round(e, 4) for e in errs],
                                 "switch_m": [round(x, 1) for x in sw],
                                 "kind": dg.sample((pa + 0.5) / dg.PATCHES_A,
                                                   (pz + 0.5) / dg.PATCHES_Z)[1]}
        print(f"  ...pa {pa+1}/{dg.PATCHES_A}  {time.time()-t0:.0f} s",
              file=sys.stderr)
    with open(OUT, "w") as fh:
        json.dump({"per_patch": per,
                   "drum_wide_switch_m": [r["switch_distance_m"] for r in tab],
                   "patch_triangles": [r["patch_triangles"] for r in tab],
                   "strides": list(dg.STRIDES),
                   "fov_deg": dg.FOV_DEG, "pixel_budget": dg.PIXEL_BUDGET},
                  fh, indent=1)
    print(f"\nmeasured 280 patches x 5 strides in {time.time()-t0:.0f} s "
          f"-> {OUT}")

    # How much looser is per-patch than drum-wide?
    for i, s in enumerate(dg.STRIDES):
        vals = sorted(v["switch_m"][i] for v in per.values())
        print(f"  stride {s:2d}: drum-wide {tab[i]['switch_distance_m']:8.1f} m"
              f"   per-patch min {vals[0]:8.1f}  median "
              f"{vals[len(vals)//2]:8.1f}  max {vals[-1]:8.1f}")


if __name__ == "__main__":
    main()
