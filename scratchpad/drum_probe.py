#!/usr/bin/env python3
"""Fast probe of the drum's per-eye triangle cost on budget.py's own lattice.

Uses the COUNTING paths (`drum_ground.visible_cost`, `drum_dressing.
dressing_cost`, `drum_dressing.drum_fixed_cost`) rather than building the
meshes, so a sweep is seconds instead of ten seconds an eye. The counting paths
are asserted against the BUILDING paths at the worst eye by `--verify`, because
a probe that disagrees with the gate it is exploring for is a probe that
manufactures evidence.

Not a gate. An instrument. `station/budget.py` is the gate.
"""
import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import interior as it          # noqa: E402
import drum_ground as dg       # noqa: E402
import drum_dressing as dd     # noqa: E402
import budget as B             # noqa: E402


def lattice(stations, zs):
    """budget.drum_eyes, restated ONLY in the sense of calling it."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    return schema, profile, sector, B.drum_eyes(schema, profile, sector,
                                                stations, zs)


def sweep(stations=4, zs=3, fixed=None, verbose=True):
    schema, profile, sector, eyes = lattice(stations, zs)
    fx = dd.DRUM_FIXED_TRIS if fixed is None else fixed
    rows = []
    t0 = time.time()
    for ang, z, eye in eyes:
        g, gper = dg.visible_cost(eye)
        d, dper = dd.dressing_cost(eye)
        rows.append({"ang": round(ang, 1), "z": round(z, 1), "eye": eye,
                     "ground": g, "dressing": d, "fixed": fx,
                     "total": fx + g + d,
                     "ground_levels": gper, "dress_levels": dper})
    rows.sort(key=lambda r: -r["total"])
    if verbose:
        for r in rows:
            print(f"  ({r['ang']:6.1f}, {r['z']:7.1f})  total {r['total']:8,}"
                  f"   fixed {r['fixed']:7,}  ground {r['ground']:7,}"
                  f"  dressing {r['dressing']:7,}")
        print(f"  swept {len(rows)} eyes in {time.time()-t0:.1f} s")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", type=int, default=4)
    ap.add_argument("--zs", type=int, default=3)
    ap.add_argument("--fixed", type=int, default=None)
    ap.add_argument("--measure-fixed", action="store_true",
                    help="rebuild the eye-independent parts (~40 s)")
    ap.add_argument("--verify", action="store_true",
                    help="rebuild the worst eye through export_scene.drum_parts "
                         "and assert the counting path agrees")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    fixed = a.fixed
    if a.measure_fixed:
        t0 = time.time()
        fixed, per = dd.drum_fixed_cost()
        print(f"fixed parts, rebuilt in {time.time()-t0:.0f} s: {fixed:,}")
        for k, v in sorted(per.items(), key=lambda kv: -kv[1]):
            print(f"    {k:<14} {v:8,}")
        print(f"  pinned DRUM_FIXED_TRIS = {dd.DRUM_FIXED_TRIS:,}"
              f"  {'AGREES' if fixed == dd.DRUM_FIXED_TRIS else 'DISAGREES'}")

    print(f"\nlattice {a.stations} x {a.zs}, LOD_SCALE_M={dd.LOD_SCALE_M}, "
          f"dg.FOV_DEG={dg.FOV_DEG}, dd.FOV_DEG={dd.FOV_DEG}")
    rows = sweep(a.stations, a.zs, fixed)
    w = rows[0]
    print(f"\nWORST EYE ({w['ang']}, {w['z']}): {w['total']:,} against "
          f"{B.DRUM['visible_set_tris']:,} = "
          f"{w['total']/B.DRUM['visible_set_tris']*100:.1f}%")
    print(f"  best eye {rows[-1]['total']:,}  spread "
          f"x{rows[0]['total']/max(rows[-1]['total'],1):.2f}")

    if a.verify:
        import export_scene as es                              # noqa: PLC0415
        schema, profile = it.load()
        sector = it.drum_sector(schema, profile)
        dg.configure(schema, profile, sector)
        t0 = time.time()
        parts = {nm: len(t) for nm, _v, t, _g in
                 es.drum_parts(schema, profile, sector, tuple(w["eye"]),
                               trams=B.DRUM["trams"])}
        built = sum(parts.values())
        print(f"\nVERIFY: export_scene.drum_parts at the worst eye, "
              f"{time.time()-t0:.0f} s")
        for k, v in sorted(parts.items(), key=lambda kv: -kv[1]):
            print(f"    {k:<14} {v:8,}")
        print(f"    {'BUILT':<14} {built:8,}   counted {w['total']:8,}   "
              f"{'AGREE' if built == w['total'] else 'DISAGREE'}")
        if built != w["total"]:
            print(f"    ground built {parts['ground']:,} counted {w['ground']:,}")
            print(f"    dressing built {parts['dressing']:,} counted "
                  f"{w['dressing']:,}")
            print(f"    fixed built "
                  f"{built-parts['ground']-parts['dressing']:,} counted "
                  f"{w['fixed']:,}")

    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"rows": rows, "lod_scale_m": dd.LOD_SCALE_M,
                       "fov_ground": dg.FOV_DEG, "fov_dress": dd.FOV_DEG},
                      fh, indent=1)
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
