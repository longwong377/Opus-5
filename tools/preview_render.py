#!/usr/bin/env python3
"""Software-rasterise an OBJ to PNG so generated geometry can be inspected.

Independent of Godot and of any GPU. Its job is to answer "does the silhouette
look like Babylon 5" within seconds of a schema edit, which is the tightest
possible feedback loop on proportion and form.

Flat-shaded, painter's algorithm, backface culled. Not a renderer for looking
at materials -- that is what the lavapipe/Godot path is for.
"""
import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw


def load_obj(path):
    verts, tris = [], []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                _, x, y, z = line.split()
                verts.append((float(x), float(y), float(z)))
            elif line.startswith("f "):
                idx = [int(p.split("/")[0]) - 1 for p in line.split()[1:]]
                for i in range(1, len(idx) - 1):
                    tris.append((idx[0], idx[i], idx[i + 1]))
    return np.array(verts, dtype=np.float64), np.array(tris, dtype=np.int64)


def look_at(eye, target, up=(0, 0, 1)):
    f = np.array(target, dtype=np.float64) - np.array(eye, dtype=np.float64)
    f /= np.linalg.norm(f)
    u = np.array(up, dtype=np.float64)
    s = np.cross(f, u)
    if np.linalg.norm(s) < 1e-9:          # camera looking along `up`
        u = np.array([0.0, 1.0, 0.0])
        s = np.cross(f, u)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    return np.stack([s, u, -f])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--eye", nargs=3, type=float, required=True)
    ap.add_argument("--target", nargs=3, type=float, default=[0, 0, 4023])
    ap.add_argument("--fov", type=float, default=35.0)
    # The station's long axis is +Z, so the default world-up of +Z would render
    # it standing on end. -X puts the axis horizontal with fore to screen-right.
    ap.add_argument("--up", nargs=3, type=float, default=[-1, 0, 0])
    ap.add_argument("--light", nargs=3, type=float, default=[-0.4, -0.7, 0.55])
    ap.add_argument("--bg", nargs=3, type=int, default=[8, 10, 16])
    a = ap.parse_args()

    verts, tris = load_obj(a.obj)
    eye = np.array(a.eye, dtype=np.float64)
    R = look_at(eye, a.target, a.up)

    cam = (verts - eye) @ R.T
    depth = -cam[:, 2]

    fl = (a.height / 2) / math.tan(math.radians(a.fov) / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        sx = a.width / 2 + cam[:, 0] * fl / depth
        sy = a.height / 2 - cam[:, 1] * fl / depth

    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    n = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] /= ln[ok][:, None]

    centroid = (v0 + v1 + v2) / 3.0
    view = eye - centroid
    view /= np.linalg.norm(view, axis=1)[:, None]
    facing = np.einsum("ij,ij->i", n, view) > 0

    tri_depth = depth[tris].mean(axis=1)
    visible = facing & ok & (depth[tris] > 1.0).all(axis=1)

    L = np.array(a.light, dtype=np.float64)
    L /= np.linalg.norm(L)
    lam = np.clip(np.einsum("ij,j->i", n, L), 0, 1)
    # Ambient floor keeps unlit hull readable as form rather than silhouette.
    shade = 0.16 + 0.84 * lam

    order = np.argsort(-tri_depth)
    order = order[visible[order]]

    img = Image.new("RGB", (a.width, a.height), tuple(a.bg))
    d = ImageDraw.Draw(img)
    for t in order:
        i, j, k = tris[t]
        c = int(np.clip(shade[t], 0, 1) * 235)
        d.polygon([(sx[i], sy[i]), (sx[j], sy[j]), (sx[k], sy[k])],
                  fill=(c, int(c * 0.99), int(c * 0.94)))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.save(a.out)
    print(f"{a.out}  {a.width}x{a.height}  {int(visible.sum()):,}/{len(tris):,} triangles drawn")


if __name__ == "__main__":
    main()
