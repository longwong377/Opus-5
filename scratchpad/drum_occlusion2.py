#!/usr/bin/env python3
"""The occlusion ceiling in TRIANGLES, at the granularity a renderer can cull.

`drum_occlusion.py` counted targets. A target is not a cost: a copse hidden at
1,200 m is 30 triangles and a farmstead hidden at 30 m is 800, so a percentage
of features says nothing about a triangle budget. This weights every hidden
thing by the triangles it would actually have contributed AT THE LEVEL THE LOD
CHAIN WOULD HAVE DRAWN IT, and it culls at the two granularities that could
exist:

  patch      the 14 x 20 ground patches -- a patch is cullable only if EVERY
             sample point on it is hidden, because half a hidden patch is a
             drawn patch.
  feature    one dressing feature, which is the finest granularity anything in
             this project could ever submit.

Both are CEILINGS. Neither charges anything for the occluder geometry, for the
depth rasterisation, or for the fact that Godot tests an axis-aligned box round
the instance rather than the instance.
"""
import argparse
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


def ground_r(angle_deg, z):
    u = (angle_deg / 360.0) % 1.0
    w = min(max((z - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
    return dg.FLOOR_R - dg.sample(u, w)[0]


def ground_point(angle_deg, z):
    r = ground_r(angle_deg, z)
    a = math.radians(angle_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def blocked(eye, target, steps=48):
    for i in range(1, steps):
        t = i / steps
        p = tuple(eye[k] + (target[k] - eye[k]) * t for k in range(3))
        ang = math.degrees(math.atan2(p[1], p[0])) % 360.0
        if math.hypot(p[0], p[1]) > ground_r(ang, p[2]):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ang", type=float, default=270.0)
    ap.add_argument("--z", type=float, default=5132.0)
    ap.add_argument("--patch-samples", type=int, default=9)
    a = ap.parse_args()

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    eye, _up = dg.stand_on_ground(schema, profile, sector, a.ang, a.z)
    table = dg.lod_table()

    # ---------------- ground, per patch, weighted by triangles --------------
    t0 = time.time()
    deg_per_patch = 360.0 / dg.PATCHES_A
    z_per_patch = (dg.Z1 - dg.Z0) / dg.PATCHES_Z
    n = int(math.sqrt(a.patch_samples))
    tot_t = hid_t = 0
    hid_p = 0
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            lvl = dg.level_for_distance(
                dg.patch_nearest_distance(pa, pz, eye), table)
            tris = table[lvl]["patch_triangles"]
            tot_t += tris
            all_hidden = True
            for i in range(n):
                for j in range(n):
                    ang = (pa + (i + 0.5) / n) * deg_per_patch
                    z = dg.Z0 + (pz + (j + 0.5) / n) * z_per_patch
                    if not blocked(eye, ground_point(ang, z)):
                        all_hidden = False
                        break
                if not all_hidden:
                    break
            if all_hidden:
                hid_p += 1
                hid_t += tris
    print(f"GROUND, {dg.PATCHES_A}x{dg.PATCHES_Z} patches, "
          f"{n*n} samples each ({time.time()-t0:.0f} s)")
    print(f"  fully hidden patches: {hid_p} of "
          f"{dg.PATCHES_A*dg.PATCHES_Z}")
    print(f"  triangles cullable  : {hid_t:,} of {tot_t:,} = "
          f"{hid_t/tot_t*100:.2f}%")

    # ---------------- dressing, per feature, weighted by triangles ----------
    t0 = time.time()
    sw = dd.switch_distances()
    fld = dd.field()
    tot_d = hid_d = 0
    hid_n = 0
    for f in fld["points"]:
        p = f.position()
        lv = dd._level(math.dist(p, eye), sw)
        if dd._culled(f.kind, f.proto, lv, sw, f.scale, f.radius_m):
            continue
        tris = dd._feature_tris(f, lv)
        tot_d += tris
        if blocked(eye, p, 32):
            hid_n += 1
            hid_d += tris
    for ln in fld["lines"]:
        c = ln.centre()
        lv = dd._level(math.dist(c, eye), sw)
        tris = dd._line_tris(ln, lv)
        tot_d += tris
        if blocked(eye, c, 32):
            hid_n += 1
            hid_d += tris
    near = dd.near_cost(eye)
    print(f"\nDRESSING, per feature ({time.time()-t0:.0f} s)")
    print(f"  hidden features     : {hid_n} of "
          f"{len(fld['points'])+len(fld['lines'])}")
    print(f"  triangles cullable  : {hid_d:,} of {tot_d:,} ladder triangles "
          f"(+{near:,} near rung, untested) = {hid_d/max(tot_d,1)*100:.2f}%")

    # ---------------- the whole frame ---------------------------------------
    total = dd.DRUM_FIXED_TRIS + tot_t + tot_d + near
    cull = hid_t + hid_d
    print(f"\nTHE CEILING, at this eye")
    print(f"  drawn today         : {total:,}")
    print(f"  perfectly occluded  : {cull:,} = {cull/total*100:.2f}%")
    print(f"  best case after     : {total-cull:,} against "
          f"{B.DRUM['visible_set_tris']:,} = "
          f"{(total-cull)/B.DRUM['visible_set_tris']*100:.1f}%")
    print(f"  the FIXED parts ({dd.DRUM_FIXED_TRIS:,}) are not in the cull "
          f"test at all -- they are one instance each and span the drum")


if __name__ == "__main__":
    main()
