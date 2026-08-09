#!/usr/bin/env python3
"""GLB -> OBJ, for the one direction this project never needed until now.

WHY IT EXISTS. Two build paths write this station's decks and they disagree
about file names, which is how the shipped build came to hold a dev test deck:

    station/generated/scene/deck/     blue_0_0_z7440.glb  + _col.obj + _col.glb
    station/generated/scene/station/  blue_0_0.glb        + _collision.glb

`station/boot.py::decks()` enumerates `*_col.obj`, so it can only ever see the
first directory -- and the first directory holds ONE z-cluster of six, with 83
room occupants, no corridor crowd and no cell set. The second holds the real
deck: 6 clusters, 23 rooms, 4.38 M triangles, 408 actors, 444 crowd instances
and 206 baked streaming cells. `boot.json` named the small one, so the packaged
game loaded a 39 MB test fixture and printed `MONOLITHIC -- no cell set`.

`boot.py` needs an OBJ rather than a GLB for one specific reason and it is a
good one: `spawn_from_shell` derives the player's spawn by finding the floor
triangles of the collision shell -- *"measured off the collision shell's own
floor, never copied"* -- and it reads them out of a named OBJ group. So the
cheapest correct bridge is to give it the OBJ it expects, generated from the
collision GLB that already exists, rather than to teach it a second geometry
reader or to re-run a 222-second deck export.

THE GROUP NAMES ARE TRANSLATED, NOT COPIED. The z-cluster OBJ that works today
carries four groups literally named `collision` (the shell) beside per-door
`doorpanel_<place>` groups, and `boot.FLOOR_GROUP` is the string `"collision"`.
The GLB names the same things `deck_untagged`, `join<z0>_<z1>` and
`z<z>__doorpanel_<place>`. A converter that copied those names verbatim would
produce an OBJ with no `collision` group at all, and `spawn_from_shell` would
raise `has no collision group -- is it a collision shell?` on a file that is
one. So: anything that is not a door panel becomes `collision`, and a door
panel keeps its name with the `z<z>__` address prefix stripped, which is the
convention the working file uses.

NO NODE TRANSFORMS ARE APPLIED, AND THAT IS CHECKED RATHER THAN ASSUMED. These
decks are authored in world space and their glTF nodes carry no matrix,
translation, rotation or scale. A GLB that did would need the node hierarchy
composed onto every vertex, and silently ignoring it would place the floor
somewhere the player is not -- so `read_glb` raises instead of guessing.
"""

import argparse
import json
import os
import struct
import sys

# glTF component types -> (struct code, byte size)
_CT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
       5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
_NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
          "MAT4": 16}


def _accessor(j, blob, idx):
    """Read accessor `idx` as a flat list of numbers."""
    acc = j["accessors"][idx]
    bv = j["bufferViews"][acc["bufferView"]]
    code, size = _CT[acc["componentType"]]
    n = _NCOMP[acc["type"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or (size * n)
    out = []
    for i in range(acc["count"]):
        off = base + i * stride
        out.append(struct.unpack_from("<" + code * n, blob, off))
    return out


def read_glb(path):
    """-> [(name, [(x,y,z), ...], [(a,b,c), ...])] in world space."""
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"glTF":
        raise SystemExit("%s is not a GLB" % path)
    jlen = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + jlen])
    # chunk 2 is the BIN blob: 12-byte header + 8-byte JSON chunk header
    p = 20 + jlen
    blob = b""
    while p < len(d):
        clen, ctype = struct.unpack_from("<II", d, p)
        if ctype == 0x004E4942:                       # 'BIN\0'
            blob = d[p + 8:p + 8 + clen]
            break
        p += 8 + clen
    if not blob:
        raise SystemExit("%s has no BIN chunk" % path)

    moved = [n for n in j.get("nodes", ())
             if any(k in n for k in ("matrix", "translation",
                                     "rotation", "scale"))]
    if moved:
        raise SystemExit(
            "%s has %d node(s) with a transform. This converter writes world "
            "space and would place them wrong; compose the node hierarchy "
            "first." % (path, len(moved)))

    out = []
    for m in j.get("meshes", ()):
        name = m.get("name", "mesh")
        verts, tris = [], []
        for prim in m.get("primitives", ()):
            if prim.get("mode", 4) != 4:              # TRIANGLES only
                continue
            base = len(verts)
            verts.extend(_accessor(j, blob, prim["attributes"]["POSITION"]))
            if "indices" in prim:
                idx = [v[0] for v in _accessor(j, blob, prim["indices"])]
            else:
                idx = list(range(len(verts) - base))
            for i in range(0, len(idx) - 2, 3):
                tris.append((base + idx[i], base + idx[i + 1],
                             base + idx[i + 2]))
        if tris:
            out.append((name, verts, tris))
    return out


def collision_group(name):
    """GLB mesh name -> the group name the OBJ convention uses.

    See the module docstring: `boot.FLOOR_GROUP` is `"collision"`, and a door
    panel is not somewhere to stand.
    """
    if "doorpanel" in name:
        # `z7120__doorpanel_docking_bays` -> `doorpanel_docking_bays`
        i = name.find("doorpanel")
        return name[i:]
    return "collision"


def write_obj(path, meshes, rename=None):
    """Write an OBJ, merging meshes that map to the same group name."""
    n_v = 0
    order, buckets = [], {}
    for name, verts, tris in meshes:
        g = rename(name) if rename else name
        if g not in buckets:
            order.append(g)
            buckets[g] = []
        buckets[g].append((verts, tris))
    with open(path, "w", encoding="utf-8") as f:
        f.write("# written by tools/glb_to_obj.py\n")
        for g in order:
            for verts, tris in buckets[g]:
                f.write("g %s\n" % g)
                for x, y, z in verts:
                    f.write("v %.6f %.6f %.6f\n" % (x, y, z))
                for a, b, c in tris:
                    f.write("f %d %d %d\n"
                            % (a + 1 + n_v, b + 1 + n_v, c + 1 + n_v))
                n_v += len(verts)
    return n_v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glb", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--collision", action="store_true",
                    help="translate mesh names to the collision-shell group "
                         "convention boot.py reads (see collision_group)")
    a = ap.parse_args(argv)

    meshes = read_glb(a.glb)
    n_tri = sum(len(t) for _n, _v, t in meshes)
    n_v = write_obj(a.out, meshes,
                    rename=collision_group if a.collision else None)
    groups = sorted({(collision_group(n) if a.collision else n)
                     for n, _v, _t in meshes})
    print("%s -> %s" % (os.path.basename(a.glb), os.path.basename(a.out)))
    print("  %d meshes, %d triangles, %d vertices, %d group(s)"
          % (len(meshes), n_tri, n_v, len(groups)))
    print("  groups: %s%s" % (", ".join(groups[:4]),
                              " ..." if len(groups) > 4 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
