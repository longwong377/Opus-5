#!/usr/bin/env python3
"""A REAL cutaway: the actual hull mesh, cut open, with the actual decks inside.

Not a diagram. `tools/cutaway.py` draws the schema; this cuts the shipped
geometry. Everything in the output OBJ is a triangle that exists in the build:
`station/generated/hull.obj` is what the exterior shot renders, and the deck
meshes are what `walk.gd` loads and `walkable.py` walks on.

HOW THE CUT IS MADE, and it is a real cut rather than a camera trick: every
triangle whose centroid is on the near side of a plane through the spin axis is
DELETED, so the remaining hull is genuinely open and a camera outside sees the
interior through the hole. A clip plane in a shader would look the same from one
angle and fall apart from any other; this survives being orbited.

WHAT IT CANNOT SHOW, stated because a cutaway invites the assumption that
everything absent is missing: only the decks present on disk are placed. The
full 70-deck build is 2.39 GB and this container is ephemeral, so a fresh
session has the hull and whatever `tools/export_station.py` last wrote.
`--decks` lists what was found and the header records the count.
"""
import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
HULL = os.path.join(ROOT, "station/generated/hull.obj")
DECK = os.path.join(ROOT, "station/generated/scene/deck")


def read_obj(path):
    v, f, g = [], [], []
    name, start = "default", 0
    with open(path) as fh:
        for ln in fh:
            if ln.startswith("v "):
                p = ln.split()
                v.append((float(p[1]), float(p[2]), float(p[3])))
            elif ln.startswith("f "):
                idx = [int(q.split("/")[0]) - 1 for q in ln.split()[1:]]
                for k in range(1, len(idx) - 1):
                    f.append((idx[0], idx[k], idx[k + 1]))
            elif ln[:2] in ("g ", "o "):
                if len(f) > start:
                    g.append((name, start, len(f)))
                name, start = ln[2:].strip(), len(f)
    if len(f) > start:
        g.append((name, start, len(f)))
    return v, f, g


def cut(v, f, g, keep, prefix=""):
    """Drop every triangle whose centroid fails `keep`. Re-indexes."""
    out_v, remap, out_f = [], {}, []
    for name, lo, hi in g:
        first = len(out_f)
        for tri in f[lo:hi]:
            p = [v[i] for i in tri]
            c = (sum(q[0] for q in p) / 3.0, sum(q[1] for q in p) / 3.0,
                 sum(q[2] for q in p) / 3.0)
            if not keep(c):
                continue
            nt = []
            for i in tri:
                if i not in remap:
                    remap[i] = len(out_v)
                    out_v.append(v[i])
                nt.append(remap[i])
            out_f.append((tuple(nt), prefix + name))
        del first
    return out_v, out_f


def write_obj(path, verts, faces):
    with open(path, "w") as fh:
        fh.write(f"# cutaway -- {len(verts):,} verts, {len(faces):,} tris\n")
        for x, y, z in verts:
            fh.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        cur = None
        for tri, name in faces:
            if name != cur:
                fh.write(f"g {name}\n")
                cur = name
            fh.write(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT,
                    "station/generated/cutaway.obj"))
    ap.add_argument("--angle", type=float, default=90.0,
                    help="the cut plane's angle about the spin axis, degrees")
    ap.add_argument("--z0", type=float, default=0.0)
    ap.add_argument("--z1", type=float, default=8100.0)
    a = ap.parse_args()

    if not os.path.exists(HULL):
        raise SystemExit(f"missing {HULL} -- run station/generate_hull.py")

    # The cut plane's inward normal. Keep a triangle when it is on the FAR side,
    # so the near half is removed and the camera looks into the opening.
    th = math.radians(a.angle)
    nx, ny = math.cos(th), math.sin(th)

    hv, hf, hg = read_obj(HULL)
    print(f"hull      {len(hv):,} verts {len(hf):,} tris in {len(hg)} groups")
    cv, cf = cut(hv, hf, hg,
                 lambda c: (c[0] * nx + c[1] * ny) <= 0.0
                 or not (a.z0 <= c[2] <= a.z1),
                 prefix="hull_")
    print(f"  cut     {len(cf):,} tris kept "
          f"({100.0 * len(cf) / max(len(hf), 1):.1f}%)")

    verts, faces = list(cv), list(cf)
    found = []
    for fn in sorted(os.listdir(DECK)) if os.path.isdir(DECK) else []:
        if not fn.endswith(".obj") or fn.endswith("_col.obj") \
                or fn.startswith(("crowd", "shot_")):
            continue
        p = os.path.join(DECK, fn)
        dv, df, dg = read_obj(p)
        # Decks are authored in STATION coordinates already, so they drop
        # straight in -- the same property that lets `walk.gd` load one whole.
        kv, kf = cut(dv, df, dg, lambda c: True, prefix="deck_")
        off = len(verts)
        verts.extend(kv)
        faces.extend(((t[0] + off, t[1] + off, t[2] + off), n) for t, n in kf)
        found.append((fn, len(kf)))
        print(f"  deck    {fn:<28} {len(kf):>9,} tris")

    write_obj(a.out, verts, faces)
    print(f"\nwrote {a.out}")
    print(f"  {len(verts):,} verts, {len(faces):,} tris, "
          f"{len(found)} deck(s) placed")
    if len(found) < 10:
        print(f"  NOTE: only {len(found)} deck(s) on disk. The full build is "
              f"70; run tools/export_station.py to place them all.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
