#!/usr/bin/env python3
"""Export generated station geometry as glTF 2.0 (.glb).

OBJ carries no normals, no material bindings and no scene hierarchy, so it is
fine for the preview rasteriser and wrong for the engine. glTF is the format
Godot imports natively and losslessly, and it keeps the per-feature grouping
the generator produces, so hull sections stay individually addressable at
runtime for streaming and for damage states.

Emits a single .glb with one mesh per feature group and CREASE-ANGLE normals:
a tessellated curve is smoothed, a real corner stays hard. See `CREASE_DEG`.
"""
import argparse
import json
import math
import os
import struct
from collections import defaultdict

COMPONENT_FLOAT = 5126
COMPONENT_UINT = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963

# THE CREASE ANGLE, AND IT IS MEASURED OFF THE STATION RATHER THAN CHOSEN.
#
# Until session 4i this file shaded every triangle flat, and the docstring said
# why: "the hull is faceted deliberately -- plating steps and section
# transitions should read as hard edges". That was TRUE OF THE HULL, which was
# the only subject when it was written. It then applied to everything the
# project has built since -- the drum's 8 km barrel, 345 degrees of ring
# corridor, every lathed cylinder in `dressing`, the observation domes, and
# every human head in the crowd. `station/generated/**.obj` carries **zero**
# `vn` lines, so nothing downstream could disagree.
#
# The threshold is the minimum-density point of the station's own dihedral
# distribution, over the 971,112 shared edges of the assembled blue/0/0 deck
# (`--dihedral` recomputes it):
#
#   coplanar             0-5 deg    343,881   35.4%
#   curve tessellation   6-45 deg    38,973    4.0%
#   THE TROUGH          46-84 deg     7,073    0.7%
#   real corners        85-180 deg   581,185   59.9%
#
# It is bimodal with a trough three orders of magnitude below either peak, so
# the threshold is well determined: anywhere in 46-84 shades at most 0.73% of
# edges the wrong way, and 57 deg is the least dense degree of it (1,509 edges
# within +/-5). NOT an industry default that happens to work -- rerun
# `--dihedral` on a deck and the number comes back.
CREASE_DEG = 57.0

# Positions are quantised to this before being matched, in metres.
#
# BY POSITION, NOT BY INDEX, and that is the difference between a smooth
# cylinder and one with a seam down it. The generators emit lathed surfaces as
# runs of vertices that duplicate at the wrap, and solids that meet flush share
# no indices at all -- `interior.boundary_edges` pairs edges by position for
# exactly this reason. Index-keyed smoothing would leave a hard line down every
# barrel in the project. 0.1 mm is the precision `write_obj` commits to
# (`%.4f`), so this loses nothing that survived the round trip anyway.
WELD_M = 1e-4


def load_obj_groups(path):
    verts = []
    groups = defaultdict(list)
    current = "default"
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                _, x, y, z = line.split()
                verts.append((float(x), float(y), float(z)))
            elif line.startswith("g "):
                current = line[2:].strip()
            elif line.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in line.split()[1:]]
                for i in range(1, len(idx) - 1):
                    groups[current].append((idx[0], idx[i], idx[i + 1]))
    return verts, groups


def face_normals(verts, tris):
    """Unit normal per triangle, and the interior angle at each of its corners.

    THE WEIGHT IS THE CORNER ANGLE, NOT THE AREA, and that is not a detail.
    Area weighting was tried first and this file's own self-test caught it: a
    24-segment barrel came out with 48 distinct normals instead of 24, because
    a quad split into two triangles gives one endpoint two faces of the quad
    and the other endpoint one, so the two ends of the same lathe column got
    different answers. Angle-weighted normals are provably invariant to how a
    surface was triangulated (Thurmer & Wuthrich 1998) -- the smoothed normal
    is a property of the SURFACE, which is the whole claim being made.
    """
    unit, ang = [], []
    for a, b, c in tris:
        va, vb, vc = verts[a], verts[b], verts[c]
        u = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
        w = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
        unit.append((n[0] / ln, n[1] / ln, n[2] / ln) if ln else (0.0, 1.0, 0.0))
        ang.append(tuple(_corner(verts, x, y, z) for x, y, z in
                         ((a, b, c), (b, c, a), (c, a, b))))
    return unit, ang


def _corner(verts, at, p, q):
    """Interior angle of the triangle at vertex `at`, in radians."""
    o, u, w = verts[at], verts[p], verts[q]
    a = (u[0] - o[0], u[1] - o[1], u[2] - o[2])
    b = (w[0] - o[0], w[1] - o[1], w[2] - o[2])
    la = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    lb = math.sqrt(b[0] * b[0] + b[1] * b[1] + b[2] * b[2])
    if la == 0.0 or lb == 0.0:
        return 0.0
    d = (a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (la * lb)
    return math.acos(max(-1.0, min(1.0, d)))


def build_group(verts, tris, crease_deg=CREASE_DEG):
    """Un-index into triangles with crease-angle normals.

    A vertex normal is the area-weighted average of the faces meeting at that
    POSITION whose own normal is within `crease_deg` of the face being shaded.
    So a cylinder's barrel is smooth, its cap is not smoothed into it, and a
    box corner keeps all three of its faces.

    `crease_deg=0` is the negative control and reproduces the flat shading this
    file did until session 4i, face for face.
    """
    unit, ang = face_normals(verts, tris)
    cos_crease = math.cos(math.radians(crease_deg))
    # Half the crease, for the cheap all-smooth test below.
    cos_half = math.cos(math.radians(crease_deg) * 0.5)

    # Every (face, weight) meeting at a welded position. The weight is that
    # face's own corner angle THERE, so a face contributes differently to each
    # of its three corners.
    at = defaultdict(list)
    for i, t in enumerate(tris):
        for k, v in enumerate(t):
            p = verts[v]
            at[(round(p[0] / WELD_M), round(p[1] / WELD_M),
                round(p[2] / WELD_M))].append((i, ang[i][k]))

    # One resolved normal per (position, face). Computed per position rather
    # than per corner: a position carries three to eight faces and the same
    # answer serves every corner sitting on it.
    resolved = {}
    for key, fw in at.items():
        if len(fw) == 1:
            resolved[(key, fw[0][0])] = unit[fw[0][0]]
            continue
        sx = sy = sz = 0.0
        for i, w in fw:
            sx += unit[i][0] * w
            sy += unit[i][1] * w
            sz += unit[i][2] * w
        sl = math.sqrt(sx * sx + sy * sy + sz * sz)
        # THE CHEAP CASE FIRST, and it is most of a curved surface. If every
        # face here is within half the crease of their common mean, then every
        # PAIR is within the crease (angles obey the triangle inequality), so
        # they all smooth together and the mean is the answer. That turns the
        # O(n^2) pairwise test into an O(n) one everywhere it matters.
        if sl > 0.0:
            m = (sx / sl, sy / sl, sz / sl)
            if all(unit[i][0] * m[0] + unit[i][1] * m[1] + unit[i][2] * m[2]
                   >= cos_half for i, _w in fw):
                for i, _w in fw:
                    resolved[(key, i)] = m
                continue
        for i, _w in fw:
            ni = unit[i]
            ax = ay = az = 0.0
            for j, wj in fw:
                if (ni[0] * unit[j][0] + ni[1] * unit[j][1]
                        + ni[2] * unit[j][2]) >= cos_crease:
                    ax += unit[j][0] * wj
                    ay += unit[j][1] * wj
                    az += unit[j][2] * wj
            al = math.sqrt(ax * ax + ay * ay + az * az)
            resolved[(key, i)] = ((ax / al, ay / al, az / al) if al > 0.0
                                  else ni)

    pos, nrm = [], []
    for i, (a, b, c) in enumerate(tris):
        for v in (a, b, c):
            p = verts[v]
            pos.append(p)
            nrm.append(resolved[((round(p[0] / WELD_M), round(p[1] / WELD_M),
                                  round(p[2] / WELD_M)), i)])
    return pos, nrm


def dihedral_report(verts, groups):
    """Re-derive `CREASE_DEG` from a mesh's own dihedral distribution.

    A GATE THAT READS A CONSTANT MUST BE ABLE TO REBUILD IT -- the same rule
    `measure_frame.py --derive` exists for, and the reason `budget.py`'s cached
    collision total prints loudly when it drifts. `CREASE_DEG` is a number
    measured off blue/0/0; this is the measurement, so a later session can
    check it against a different deck rather than trusting the comment.
    """
    deg = defaultdict(int)
    total = 0
    for name, tris in groups.items():
        unit, _ang = face_normals(verts, tris)
        edge = defaultdict(list)
        for i, (a, b, c) in enumerate(tris):
            for e in ((a, b), (b, c), (c, a)):
                # By position, for the reason `WELD_M` exists.
                pa, pb = verts[e[0]], verts[e[1]]
                ka = tuple(round(x / WELD_M) for x in pa)
                kb = tuple(round(x / WELD_M) for x in pb)
                edge[(ka, kb) if ka <= kb else (kb, ka)].append(i)
        for fs in edge.values():
            if len(fs) != 2:
                continue
            n1, n2 = unit[fs[0]], unit[fs[1]]
            d = max(-1.0, min(1.0, n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2]))
            deg[int(math.degrees(math.acos(d)))] += 1
            total += 1
    if not total:
        print("no shared edges -- nothing to derive from")
        return 1
    bands = ((0, 6, "coplanar"), (6, 46, "curve tessellation"),
             (46, 85, "THE TROUGH"), (85, 181, "real corners"))
    print(f"{total:,} shared edges")
    for lo, hi, lbl in bands:
        n = sum(deg[d] for d in range(lo, hi))
        print(f"  {lbl:20s} {lo:3d}-{hi - 1:3d} deg  {n:9,}  {n / total * 100:6.2f}%")
    # A MESH WITH NO CORNERS HAS NOTHING FOR A CREASE ANGLE TO PROTECT, and the
    # crossing is meaningless on one -- the drum's ground is a heightfield, 99.95%
    # coplanar with zero edges above 85 degrees, and the argmin below picks
    # whichever degree it scans first. Reporting that as DISAGREES is a gate
    # crying wolf on the one subject where any threshold above the tessellation
    # is correct. The bar there is only that the crease clears the terrain's own
    # steepest fold.
    corners = sum(deg[d] for d in range(85, 181))
    steepest = max((d for d in deg if deg[d]), default=0)
    if not corners:
        good = CREASE_DEG > steepest
        print(f"  no edges above 85 deg -- this is a heightfield or a lathe, "
              f"not architecture. Steepest fold {steepest} deg; CREASE_DEG "
              f"{CREASE_DEG:g} {'clears' if good else 'DOES NOT CLEAR'} it, so "
              f"the whole surface smooths{'' if good else ' -- IT WILL FACET'}")
        return 0 if good else 1
    best = min(range(30, 86),
               key=lambda c: sum(deg[d] for d in range(c - 5, c + 6)))
    win = sum(deg[d] for d in range(best - 5, best + 6))
    print(f"  minimum-density crossing: {best} deg ({win:,} edges within "
          f"+/-5, {win / total * 100:.3f}%)")
    off = abs(best - CREASE_DEG)
    print(f"  CREASE_DEG is {CREASE_DEG:g} -- {'AGREES' if off <= 10 else 'DISAGREES'} "
          f"with this mesh ({off:.0f} deg away)")
    return 0 if off <= 10 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj", default="station/generated/hull.obj")
    ap.add_argument("--out", default="station/generated/station.glb")
    ap.add_argument("--crease", type=float, default=CREASE_DEG,
                    help="crease angle in degrees; 0 is the flat-shaded "
                         "negative control this file did until session 4i")
    ap.add_argument("--dihedral", action="store_true",
                    help="re-derive CREASE_DEG from this mesh's own dihedral "
                         "distribution and print it, instead of exporting")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    verts, groups = load_obj_groups(os.path.join(root, a.obj))

    if a.dihedral:
        return dihedral_report(verts, groups)

    buf = bytearray()
    accessors, buffer_views, meshes, nodes = [], [], [], []

    for name, tris in sorted(groups.items()):
        if not tris:
            continue
        pos, nrm = build_group(verts, tris, a.crease)
        n = len(pos)

        prim_accessors = []
        for data, kind in ((pos, "POSITION"), (nrm, "NORMAL")):
            offset = len(buf)
            for v in data:
                buf.extend(struct.pack("<3f", *v))
            buffer_views.append({"buffer": 0, "byteOffset": offset,
                                 "byteLength": len(buf) - offset,
                                 "target": ARRAY_BUFFER})
            acc = {"bufferView": len(buffer_views) - 1, "componentType": COMPONENT_FLOAT,
                   "count": n, "type": "VEC3"}
            if kind == "POSITION":
                xs = [v[0] for v in data]
                ys = [v[1] for v in data]
                zs = [v[2] for v in data]
                acc["min"] = [min(xs), min(ys), min(zs)]
                acc["max"] = [max(xs), max(ys), max(zs)]
            accessors.append(acc)
            prim_accessors.append(len(accessors) - 1)

        offset = len(buf)
        for i in range(n):
            buf.extend(struct.pack("<I", i))
        buffer_views.append({"buffer": 0, "byteOffset": offset,
                             "byteLength": len(buf) - offset,
                             "target": ELEMENT_ARRAY_BUFFER})
        accessors.append({"bufferView": len(buffer_views) - 1,
                          "componentType": COMPONENT_UINT, "count": n,
                          "type": "SCALAR"})

        meshes.append({"name": name, "primitives": [{
            "attributes": {"POSITION": prim_accessors[0], "NORMAL": prim_accessors[1]},
            "indices": len(accessors) - 1, "mode": 4}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})

        while len(buf) % 4:
            buf.append(0)

    gltf = {
        "asset": {"version": "2.0",
                  "generator": "babylon5-station/export_gltf.py"},
        "scene": 0,
        "scenes": [{"name": "BabylonStation", "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(buf)}],
    }

    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    while len(buf) % 4:
        buf.append(0)

    out = os.path.join(root, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        total = 12 + 8 + len(js) + 8 + len(buf)
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(buf), 0x004E4942))
        f.write(buf)

    print(json.dumps({
        "out": a.out,
        "meshes": len(meshes),
        "triangles": sum(len(t) for t in groups.values()),
        "size_mb": round(total / 1e6, 2),
        "groups": sorted(groups.keys()),
    }, indent=1))


def _cylinder(segs=24, r=1.0, h=2.0, seam_split=False, caps=True):
    """A lathed barrel, built the way the generators build one.

    `seam_split` emits the wrap as a SECOND run of vertices at the same
    positions, which is what a real lathe does and what index-keyed smoothing
    would leave a hard line down.
    """
    v, t = [], []
    ring = []
    for k in range(segs + (1 if seam_split else 0)):
        a = 2.0 * math.pi * (k % segs) / segs
        lo = len(v)
        v.append((r * math.cos(a), 0.0, r * math.sin(a)))
        v.append((r * math.cos(a), h, r * math.sin(a)))
        ring.append(lo)
    n = len(ring)
    # Wound so the normals face OUT. The first version was inside-out and the
    # radial assertion below reported exactly 180.000 degrees, which is how a
    # winding error announces itself and why the test measures a direction
    # rather than counting distinct normals.
    for k in range(segs):
        i, j = ring[k], ring[(k + 1) % n]
        t.append((i, j + 1, j))
        t.append((i, i + 1, j + 1))
    if caps:
        cl, ch = len(v), len(v) + 1
        v.append((0.0, 0.0, 0.0))
        v.append((0.0, h, 0.0))
        for k in range(segs):
            i, j = ring[k], ring[(k + 1) % n]
            t.append((cl, i, j))
            t.append((ch, j + 1, i + 1))
    return v, t


def _cube(s=1.0):
    v = [(x * s, y * s, z * s) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    f = [(0, 1, 3), (0, 3, 2), (4, 7, 5), (4, 6, 7), (0, 4, 5), (0, 5, 1),
         (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v, f


def _distinct(nrm, tol=1e-6):
    seen = []
    for n in nrm:
        if not any(abs(n[0] - s[0]) < tol and abs(n[1] - s[1]) < tol
                   and abs(n[2] - s[2]) < tol for s in seen):
            seen.append(n)
    return seen


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL  {name}  {detail}")

    # -- A TESSELLATED CURVE IS SMOOTHED --------------------------------
    #
    # NOT MEASURED BY COUNTING DISTINCT NORMALS -- a flat-shaded barrel has 24
    # of them too, one per planar quad, so the count cannot tell the two apart.
    # What can: on a smooth cylinder the vertex normal points straight out
    # through the vertex it sits on. On a flat-shaded one it points through the
    # middle of the facet, which is half a segment away.
    def radial_err_deg(pos, nrm):
        worst = 0.0
        for p, n in zip(pos, nrm):
            r = math.hypot(p[0], p[2])
            if r < 1e-9:
                continue
            d = (p[0] / r) * n[0] + (p[2] / r) * n[2]
            worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0, d)))))
        return worst

    v, t = _cylinder(segs=24, caps=False)
    p, n = build_group(v, t)
    err = radial_err_deg(p, n)
    check("a 24-segment barrel's normals point through their own vertex",
          err < 1e-6, f"worst {err:.3f} deg off radial")
    # THE CONTROL, and it is quantitative: half a segment is 360/24/2 = 7.5.
    p0, n0 = build_group(v, t, 0.0)
    err0 = radial_err_deg(p0, n0)
    check("control: crease 0 is the flat shading this file did until 4i",
          abs(err0 - 7.5) < 0.01, f"flat error {err0:.3f} deg, want 7.5")

    # -- AND THE SEAM DOES NOT SHOW -------------------------------------
    # The wrap emitted as a SECOND run of vertices at the same positions, which
    # is what a real lathe does. Index-keyed smoothing sees half the faces at
    # each seam column and leaves them 7.5 degrees out -- a hard line down every
    # barrel in the project. Position keying is what makes this pass.
    v, t = _cylinder(segs=24, seam_split=True, caps=False)
    p, n = build_group(v, t)
    err = radial_err_deg(p, n)
    check("a lathe seam smooths across duplicated vertices", err < 1e-6,
          f"worst {err:.3f} deg off radial at the seam")

    # -- A REAL CORNER SURVIVES -----------------------------------------
    v, t = _cube()
    _p, n = build_group(v, t)
    d = _distinct(n)
    axis = [x for x in d if max(abs(x[0]), abs(x[1]), abs(x[2])) > 0.999]
    check("a cube keeps its six faces", len(d) == 6 and len(axis) == 6,
          f"{len(d)} distinct normals, {len(axis)} axis-aligned; want 6 and 6")
    # THE CONTROL: smooth everything and the cube's corners average to their
    # diagonals -- eight normals, none axis-aligned, a rounded blob.
    _p, nb = build_group(v, t, 180.0)
    db = _distinct(nb)
    axb = [x for x in db if max(abs(x[0]), abs(x[1]), abs(x[2])) > 0.999]
    check("control: at crease 180 the same cube rounds over",
          len(db) == 8 and not axb,
          f"{len(db)} distinct normals, {len(axb)} axis-aligned; want 8 and 0")

    # -- AND A CAP IS NOT SMOOTHED INTO THE BARREL ----------------------
    # The barrel/cap edge is 90 degrees. If it smoothed, the rim would round
    # over and the cylinder would read as a pill.
    v, t = _cylinder(segs=24, caps=True)
    p, n = build_group(v, t)
    barrel = [(q, m) for q, m in zip(p, n) if abs(m[1]) < 0.999]
    caps_n = [m for q, m in zip(p, n) if abs(m[1]) > 0.999]
    err = radial_err_deg([q for q, _m in barrel], [m for _q, m in barrel])
    check("a capped cylinder keeps its rim: the barrel stays radial",
          err < 1e-6, f"worst {err:.3f} deg off radial")
    check("and the caps stay flat", len(_distinct(caps_n)) == 2,
          f"{len(_distinct(caps_n))} axial normals, want 2")

    # -- THE THRESHOLD IS INSIDE THE TROUGH IT WAS DERIVED FROM ---------
    # A 24-segment lathe steps 15 degrees a facet, so anything above that
    # smooths it; a box corner is 90. Both bounds are geometry, not taste.
    check("CREASE_DEG smooths a 24-segment lathe and keeps a box corner",
          15.0 < CREASE_DEG < 90.0, f"CREASE_DEG={CREASE_DEG}")

    # -- DETERMINISM ----------------------------------------------------
    v, t = _cylinder(segs=13, caps=True)
    a1 = build_group(v, t)
    a2 = build_group(v, t)
    check("the same mesh exports the same normals twice", a1 == a2)

    print(f"export_gltf: {ok}/{ok + fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    main()
