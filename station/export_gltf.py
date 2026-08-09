#!/usr/bin/env python3
"""Export generated station geometry as glTF 2.0 (.glb).

OBJ carries no normals, no material bindings and no scene hierarchy, so it is
fine for the preview rasteriser and wrong for the engine. glTF is the format
Godot imports natively and losslessly, and it keeps the per-feature grouping
the generator produces, so hull sections stay individually addressable at
runtime for streaming and for damage states.

Emits a single .glb with one mesh per feature group and flat-shaded normals
computed per face, since the hull is faceted by design.
"""
import argparse
import json
import os
import struct
from collections import defaultdict

COMPONENT_FLOAT = 5126
COMPONENT_UINT = 5125
ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963


def load_obj_groups(path):
    verts = []
    groups = defaultdict(list)
    current = "default"
    with open(path, encoding="utf-8") as f:
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


def build_group(verts, tris):
    """Un-index into flat-shaded triangles with per-face normals.

    The hull is faceted deliberately -- plating steps and section transitions
    should read as hard edges, not be smoothed away by shared vertex normals.
    """
    pos, nrm = [], []
    for a, b, c in tris:
        va, vb, vc = verts[a], verts[b], verts[c]
        ux, uy, uz = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
        wx, wy, wz = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
        nx, ny, nz = (uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx)
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        n = (nx / ln, ny / ln, nz / ln)
        for v in (va, vb, vc):
            pos.append(v)
            nrm.extend([n])
    return pos, nrm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obj", default="station/generated/hull.obj")
    ap.add_argument("--out", default="station/generated/station.glb")
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    verts, groups = load_obj_groups(os.path.join(root, a.obj))

    buf = bytearray()
    accessors, buffer_views, meshes, nodes = [], [], [], []

    for name, tris in sorted(groups.items()):
        if not tris:
            continue
        pos, nrm = build_group(verts, tris)
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


if __name__ == "__main__":
    main()
