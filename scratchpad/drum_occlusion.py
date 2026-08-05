#!/usr/bin/env python3
"""CAN THE DRUM BE OCCLUDED? Measured, from the eye the budget gate fails at.

`station/budget.py`'s drum gate prints "no occlusion -- there is no wall to hide
behind" and `station/occluders.py` has never been pointed at the drum. This
answers whether it could be, with three independent measurements rather than an
argument:

  1. TERRAIN.   For every one of the 280 ground patches and every dressing
     feature, march the sight line from the eye and ask whether the heightfield
     ever rises above it. This is the only thing that CAN occlude in a drum:
     the inner surface of a cylinder is the boundary of a CONVEX region, so
     every point of it is visible from every point inside it unless something
     standing on it gets in the way.
  2. STANDING OBJECTS. The same targets, tested against every dressing feature
     nearer than they are, each treated as a vertical cylinder of its own
     measured extent -- the most generous possible occluder for an object that
     is mostly a tree.
  3. GRANULARITY. What Godot can actually cull is an INSTANCE, tested by its
     axis-aligned bounding box against a rasterised occluder buffer. So the
     third measurement is over the shipped .glb node list: how many instances
     the drum submits and how big their AABBs are.

Every number here is a CEILING on what occlusion could buy, because each
measurement culls a target the moment it is hidden and charges nothing for the
occluder itself.
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
    """Radius of the ground surface at a station, from the heightfield."""
    u = (angle_deg / 360.0) % 1.0
    w = min(max((z - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
    h, _k = dg.sample(u, w)
    return dg.FLOOR_R - h


def ground_point(angle_deg, z):
    r = ground_r(angle_deg, z)
    a = math.radians(angle_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def cyl(p):
    """(angle_deg, z, radius) of a world point."""
    return (math.degrees(math.atan2(p[1], p[0])) % 360.0, p[2],
            math.hypot(p[0], p[1]))


def terrain_blocks(eye, target, steps=64, clear_m=0.0):
    """Does the heightfield rise above the segment eye->target?

    `clear_m` is a tolerance in metres of radius: the sight line must be at
    least this much clear of the ground to count as unblocked. 0 is the strict
    reading; the ends are skipped because both endpoints ARE the ground.
    """
    for i in range(1, steps):
        t = i / steps
        p = tuple(eye[k] + (target[k] - eye[k]) * t for k in range(3))
        ang, z, r = cyl(p)
        # Ground is at FLOOR_R - h; "up" is toward the axis, so the sight point
        # is above the ground iff its radius is SMALLER.
        if r > ground_r(ang, z) - clear_m:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ang", type=float, default=270.0)
    ap.add_argument("--z", type=float, default=5132.0)
    ap.add_argument("--steps", type=int, default=64)
    ap.add_argument("--objects", action="store_true",
                    help="also test occlusion by standing dressing features")
    a = ap.parse_args()

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    eye, _up = dg.stand_on_ground(schema, profile, sector, a.ang, a.z)
    print(f"eye at ({a.ang}, {a.z}) = {tuple(round(x,1) for x in eye)}, "
          f"r={math.hypot(eye[0],eye[1]):.2f} of FLOOR_R {dg.FLOOR_R}")

    # ---- 0. THE CONVEXITY CONTROL ------------------------------------------
    # With the heightfield replaced by the mean cylinder, NOTHING may be
    # occluded. If this control reports a single blocked target the test is
    # measuring its own arithmetic rather than the terrain.
    real_sample = dg.sample
    dg.sample = lambda u, w: (0.0, "flat")
    dg._SAMPLE_CACHE = {} if hasattr(dg, "_SAMPLE_CACHE") else None
    flat_eye, _ = dg.stand_on_ground(schema, profile, sector, a.ang, a.z)
    blocked_flat = 0
    tgt = []
    for i in range(72):
        for j in range(20):
            ang = 360.0 * i / 72
            z = dg.Z0 + (dg.Z1 - dg.Z0) * (j + 0.5) / 20
            tgt.append((ang, z))
    for ang, z in tgt:
        if terrain_blocks(flat_eye, ground_point(ang, z), a.steps):
            blocked_flat += 1
    dg.sample = real_sample
    print(f"\nCONTROL, heightfield flattened to the mean cylinder: "
          f"{blocked_flat} of {len(tgt)} targets blocked "
          f"({'FIRES' if blocked_flat else 'ZERO -- as a convex boundary must'})")

    # ---- 1. TERRAIN OCCLUSION OF THE GROUND --------------------------------
    t0 = time.time()
    blocked, seen = 0, 0
    by_dist = {"<100 m": [0, 0], "100-300 m": [0, 0], "300-1000 m": [0, 0],
               ">1000 m": [0, 0]}
    for ang, z in tgt:
        p = ground_point(ang, z)
        d = math.dist(p, eye)
        k = ("<100 m" if d < 100 else "100-300 m" if d < 300
             else "300-1000 m" if d < 1000 else ">1000 m")
        by_dist[k][1] += 1
        seen += 1
        if terrain_blocks(eye, p, a.steps):
            blocked += 1
            by_dist[k][0] += 1
    print(f"\n1. THE GROUND, against its own heightfield "
          f"({len(tgt)} sample stations, {a.steps} steps each, "
          f"{time.time()-t0:.0f} s)")
    print(f"   blocked {blocked} of {seen} = {blocked/seen*100:.1f}%")
    for k, (b, n) in by_dist.items():
        print(f"     {k:<12} {b:4d} of {n:4d} = {b/max(n,1)*100:5.1f}%")

    # ---- 2. THE DRESSING, and what it could hide ---------------------------
    fld = dd.field()
    feats = fld["points"]
    print(f"\n2. THE DRESSING: {len(feats)} point features, "
          f"{len(fld['lines'])} lines")
    t0 = time.time()
    hidden_terrain = 0
    for f in feats:
        p = f.position()
        if terrain_blocks(eye, p, 32):
            hidden_terrain += 1
    print(f"   hidden by TERRAIN alone: {hidden_terrain} of {len(feats)} = "
          f"{hidden_terrain/len(feats)*100:.1f}%  ({time.time()-t0:.0f} s)")

    if a.objects:
        # Every feature as a vertical cylinder of its own extent -- the most
        # generous occluder shape for a thing that is mostly a tree.
        t0 = time.time()
        prep = []
        for f in feats:
            p = f.position()
            h, w = dd._proto_extent(f.kind, f.proto, 0)
            if f.radius_m > 0:
                h, w = dd.CLUMP_MASS_H_M, 2.0 * f.radius_m
            prep.append((p, math.dist(p, eye), h * f.scale, 0.5 * w * f.scale))
        prep.sort(key=lambda r: r[1])
        hidden_obj = 0
        for i, (p, d, _h, _w) in enumerate(prep):
            ep = (p[0] - eye[0], p[1] - eye[1], p[2] - eye[2])
            L = math.dist(p, eye) or 1.0
            u = (ep[0] / L, ep[1] / L, ep[2] / L)
            blocked_by = False
            for (q, dq, hq, wq) in prep[:i]:
                if dq >= d or wq <= 0:
                    continue
                eq = (q[0] - eye[0], q[1] - eye[1], q[2] - eye[2])
                t = eq[0] * u[0] + eq[1] * u[1] + eq[2] * u[2]
                if t <= 0 or t >= L:
                    continue
                perp = math.sqrt(max(0.0, dq * dq - t * t))
                if perp < wq:
                    blocked_by = True
                    break
            if blocked_by:
                hidden_obj += 1
        print(f"   hidden by ANOTHER FEATURE (axis-cylinder, generous): "
              f"{hidden_obj} of {len(feats)} = "
              f"{hidden_obj/len(feats)*100:.1f}%  ({time.time()-t0:.0f} s)")

    # ---- 3. WHAT THE ENGINE COULD CULL -------------------------------------
    print("\n3. GRANULARITY -- what Godot tests is an INSTANCE AABB")
    d = os.path.join(ROOT, "station/generated/scene/drum")
    import json
    import struct
    tot_nodes = 0
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".glb") or fn.startswith("drum_a"):
            continue
        with open(os.path.join(d, fn), "rb") as fh:
            fh.read(12)
            clen, _ctype = struct.unpack("<II", fh.read(8))
            js = json.loads(fh.read(clen).decode("utf-8"))
        n = len(js.get("nodes", []))
        tot_nodes += n
        print(f"     {fn:<20} {n:4d} instances")
    print(f"     {'TOTAL':<20} {tot_nodes:4d} instances for the whole drum")


if __name__ == "__main__":
    main()
