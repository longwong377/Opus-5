#!/usr/bin/env python3
"""Export a walkable ANGULAR SLICE of a real ring deck as a self-contained web build.

WHAT THIS IS AND IS NOT. It is not the Godot build and does not pretend to be:
a true Godot web export needs export templates compiled for this project's
custom `precision=double` engine, and the shipped scene data is 2.39 GB. This
takes the SAME geometry the engine loads -- `station/generated/scene/deck/*.obj`
and its collision shell -- and puts a slice of it behind a small WebGL renderer,
so what a browser draws is the station the generators actually built rather than
a model made for the web.

THREE THINGS IT INHERITS FROM THE REST OF THE PROJECT, and each is a rule that
was learned expensively somewhere else in this repository:

  * IT WALKS ON THE COLLISION SHELL, NOT THE RENDER MESH. `station/collision.py`
    exists because a capsule dropped on the corridor's 66 mm lighting channel
    and 22 mm proud tiles wedges on an internal edge and moves 1 mm. The web
    build has the same problem and takes the same answer -- the smooth shell is
    5,270 faces against the render mesh's 741,040.
  * IT REBASES THE ORIGIN. The deck sits at radius 211 m and z 7,126 m, and
    JavaScript's Float32Array is exactly the float32 this project built a
    double-precision engine to avoid. Every vertex is emitted relative to the
    spawn point, so the numbers a browser sees are small.
  * COLOUR COMES FROM `materials.resolve_any`, the same resolver the .tres
    export uses. A second colour table would be a second description of one
    thing -- hard rule 4 -- and would drift the moment a material moved.

The slice is angular because a corridor's sight line is bounded at 66 m
(`populace.corridor_sight_m`), which on a 211 m radius is about 18 degrees.
"""
import argparse
import base64
import json
import math
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
DECK = os.path.join(ROOT, "station/generated/scene/deck")


def read_obj(path):
    """(verts, faces, groups) where groups is [(name, first_face, end_face)]."""
    v, f, g = [], [], []
    name, start = "default", 0
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("v "):
                _, x, y, z = ln.split()
                v.append((float(x), float(y), float(z)))
            elif ln.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in ln.split()[1:]]
                for k in range(1, len(idx) - 1):
                    f.append((idx[0], idx[k], idx[k + 1]))
            elif ln[0] in "go" and ln[1] == " ":
                if len(f) > start:
                    g.append((name, start, len(f)))
                name, start = ln[2:].strip(), len(f)
    if len(f) > start:
        g.append((name, start, len(f)))
    return v, f, g


def group_colour(name, cache={}):
    """(albedo_rgb, emission_rgb, energy) for a mesh group, from materials.py."""
    if name in cache:
        return cache[name]
    import materials as M
    alb, emis, en = (0.42, 0.43, 0.45), None, 0.0
    try:
        r = M.resolve_any(name, "interior") or M.resolve_any(name)
        if r is not None:
            alb = tuple(r.albedo) if r.albedo else alb
            if getattr(r, "emission", None):
                emis, en = tuple(r.emission), float(r.emission_energy or 0.0)
    except Exception:                                            # noqa: BLE001
        pass
    cache[name] = (alb, emis, en)
    return cache[name]


def slice_mesh(v, f, g, cx, cy, half_deg, cz, half_z, rebase):
    """Faces whose centroid is inside the angular window, re-indexed and rebased."""
    a0 = math.atan2(cy, cx)
    keep, out_v, remap = [], [], {}
    for name, lo, hi in g:
        first = len(keep)
        for tri in f[lo:hi]:
            p = [v[i] for i in tri]
            mx = sum(q[0] for q in p) / 3.0
            my = sum(q[1] for q in p) / 3.0
            mz = sum(q[2] for q in p) / 3.0
            if abs(mz - cz) > half_z:
                continue
            d = math.degrees(math.atan2(math.sin(math.atan2(my, mx) - a0),
                                        math.cos(math.atan2(my, mx) - a0)))
            if abs(d) > half_deg:
                continue
            nt = []
            for i in tri:
                if i not in remap:
                    remap[i] = len(out_v)
                    q = v[i]
                    out_v.append((q[0] - rebase[0], q[1] - rebase[1],
                                  q[2] - rebase[2]))
                nt.append(remap[i])
            keep.append((tuple(nt), name))
        del first
    return out_v, keep


def unroll(verts, ang0, floor_r, cz):
    """Station (x, y, z) -> a flat Y-up local frame, by UNROLLING the ring.

    UP IS INWARD on a spun ring: a standing person's head points at the spin
    axis, so local +Y is -radial. Getting that wrong "puts the ground on the
    ceiling in a frame symmetric enough to hide the mistake" -- `deck_camera`'s
    own warning, and a corridor section is very nearly symmetric top to bottom.

    Unrolling rather than rotating, because the ring CURVES: over 66 m of arc at
    a 211.55 m radius the floor sags 2.59 m, so a rigid rotation would leave a
    browser walking on a shallow bowl and needing radial gravity to cope. In arc
    coordinates the floor is flat, gravity is -Y, and the only error is a shear
    of 66 m against a 211 m radius, which is below what an eye resolves in a
    corridor. `bespoke.UNROLL` already does exactly this for `plant`, for the
    same reason: a renderer that assumes +Y is up needs a frame where it is.

        x = floor_r * (theta - theta0)     arc length along the ring
        y = floor_r - r                    height above the floor, inward = up
        z = z - cz                          along the station axis
    """
    out = []
    for x, y, z in verts:
        r = math.hypot(x, y) or 1e-9
        d = math.atan2(y, x) - ang0
        d = math.atan2(math.sin(d), math.cos(d))       # wrap to (-pi, pi]
        out.append((floor_r * d, floor_r - r, z - cz))
    return out


def build(sector, ring, deck, at, half_deg, half_z, out):
    import directory as DR                                       # noqa: PLC0415

    stem = f"{sector}_{ring}_{deck}"
    obj = os.path.join(DECK, stem + ".obj")
    col = os.path.join(DECK, stem + "_col.obj")
    for p in (obj, col):
        if not os.path.exists(p):
            raise SystemExit(f"missing {p} -- run tools/export_station.py")

    place = DR.by_key(at)
    ang = math.radians(place["angle_deg"])

    v, f, g = read_obj(obj)
    cv, cf, cg = read_obj(col)
    # The floor radius, measured off the collision shell rather than written
    # down: it is the largest radius the shell reaches near the spawn angle.
    rs = [math.hypot(q[0], q[1]) for q in cv]
    floor_r = max(rs)
    # THE CORRIDOR'S OWN CENTRELINE, not the mean of every collision vertex.
    # The shell spans 96 m of arc and includes the room boxes off either side,
    # so the mean z lands between the corridor and the rooms -- and a slice
    # centred there has floor at the spawn and NO FLOOR 10 m along it, which is
    # exactly what the browser walk test reported (`groundAt(10,3,0) === null`).
    # Take the z of the vertices that are actually AT the floor radius.
    on_floor = [q[2] for q, r in zip(cv, rs) if floor_r - r < 0.25]
    on_floor.sort()
    cz = (on_floor[len(on_floor) // 2] if on_floor
          else sum(q[2] for q in cv) / max(len(cv), 1))
    origin = (floor_r * math.cos(ang), floor_r * math.sin(ang), cz)

    zero = (0.0, 0.0, 0.0)
    rv, rf = slice_mesh(v, f, g, origin[0], origin[1], half_deg, cz, half_z,
                        zero)
    kv, kf = slice_mesh(cv, cf, cg, origin[0], origin[1], half_deg + 4.0, cz,
                        half_z + 6.0, zero)
    rv = unroll(rv, ang, floor_r, cz)
    kv = unroll(kv, ang, floor_r, cz)
    # UNROLLING FLIPS HANDEDNESS AND THE WINDING HAS TO FOLLOW. `y = floor_r - r`
    # negates the radial axis, so the map has determinant -1: it is a reflection,
    # not a rotation, and every triangle comes out wound the wrong way. Back-face
    # culling then hides the inside of the corridor and shows its outside, which
    # is exactly what the first browser screenshots were -- the deck seen from
    # above with the walls invisible. `plant.py` shipped a -1 remap with no flip
    # and rendered every surface inside-out; `alien_sector`'s mirrored grid was
    # controlled for the same thing this morning. Third time this defect.
    rf = [((a, c, b), n) for (a, b, c), n in rf]
    kf = [((a, c, b), n) for (a, b, c), n in kf]
    if not rf or not kf:
        raise SystemExit("the slice is empty -- widen --half-deg / --half-z")

    # Pack by material so the renderer draws a handful of batches, not a
    # thousand. Group name -> colour is materials.resolve_any, one resolver.
    batches = {}
    for tri, name in rf:
        alb, emis, en = group_colour(name)
        key = (alb, emis, en)
        batches.setdefault(key, []).append(tri)

    pos = struct.pack(f"<{len(rv) * 3}f",
                      *[c for q in rv for c in q])
    mats, idx_all, off = [], [], 0
    for (alb, emis, en), tris in sorted(batches.items(),
                                        key=lambda kv: -len(kv[1])):
        flat = [i for tri in tris for i in tri]
        idx_all.extend(flat)
        mats.append({"albedo": [round(c, 4) for c in alb],
                     "emission": [round(c, 4) for c in emis] if emis else None,
                     "energy": round(en, 3),
                     "start": off, "count": len(flat)})
        off += len(flat)
    idx = struct.pack(f"<{len(idx_all)}I", *idx_all)

    cpos = struct.pack(f"<{len(kv) * 3}f", *[c for q in kv for c in q])
    cidx = struct.pack(f"<{len(kf) * 3}I",
                       *[i for tri, _n in kf for i in tri])

    data = {
        "place": at,
        "name": place.get("name", at),
        "deck": stem,
        "floor_r_m": round(floor_r, 3),
        "angle_deg": place["angle_deg"],
        "z_m": round(cz, 2),
        "half_deg": half_deg,
        "arc_m": round(2 * math.radians(half_deg) * floor_r, 1),
        "verts": len(rv), "tris": len(rf),
        "col_verts": len(kv), "col_tris": len(kf),
        "materials": mats,
        "pos": base64.b64encode(pos).decode(),
        "idx": base64.b64encode(idx).decode(),
        "cpos": base64.b64encode(cpos).decode(),
        "cidx": base64.b64encode(cidx).decode(),
    }
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    mb = os.path.getsize(out) / 1e6
    print(f"{at}: {len(rf):,} render tris in {len(mats)} materials, "
          f"{len(kf):,} collision tris, {data['arc_m']:.0f} m of arc")
    print(f"  floor radius {floor_r:.2f} m, z {cz:.1f} m, rebased to the spawn")
    print(f"  wrote {out} -- {mb:.2f} MB of JSON")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="blue/0/0")
    ap.add_argument("--at", default="docking_bays")
    ap.add_argument("--half-deg", type=float, default=9.0,
                    help="angular half-window; a corridor sight line is ~18 deg "
                         "at this radius (populace.corridor_sight_m)")
    ap.add_argument("--half-z", type=float, default=26.0)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs/web/slice.json"))
    a = ap.parse_args()
    sec, ring, dk = a.deck.split("/")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    build(sec, int(ring), int(dk), a.at, a.half_deg, a.half_z, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
