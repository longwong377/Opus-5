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
    """Return vertices, triangles, and the OBJ group each triangle belongs to.

    Groups are how the renderer learns that a deck channel is a light source
    rather than grey plastic. Without them the interior kit rendered as a dark
    tube and its entire lighting premise went untested.
    """
    verts, tris, groups = [], [], []
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
                    tris.append((idx[0], idx[i], idx[i + 1]))
                    groups.append(current)
    return (np.array(verts, dtype=np.float64),
            np.array(tris, dtype=np.int64), groups)


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
    # Emissive groups are given as SUBSTRING=R,G,B[,energy]. Any OBJ group whose
    # name contains the substring is drawn at that colour regardless of the
    # light direction, because a light fitting is not lit -- it emits.
    ap.add_argument("--emissive", action="append", default=[],
                    metavar="SUBSTR=R,G,B[,E]")
    # A directional light is right for the hull, seen from outside against
    # empty space. It is wrong inside the habitat drum: whichever way it points,
    # one wall lights and the rest of the cylinder -- including the ground
    # overhead, the whole reason for looking -- goes to the ambient floor.
    # An O'Neill drum is lit from its axis, not from infinity. A point light on
    # the axis also falls off along the length, which is most of what makes a
    # kilometre of cylinder read as a kilometre rather than as a texture.
    ap.add_argument("--pointlight", nargs=3, type=float, default=None,
                    metavar=("X", "Y", "Z"),
                    help="light from a position rather than a direction")
    ap.add_argument("--pointlight-range", type=float, default=400.0,
                    help="distance at which --pointlight falls to half")
    # Preview annotation, NOT a material assertion: it colours OBJ groups so
    # composition can be judged. Real materials come from the Godot path.
    ap.add_argument("--tint", action="append", default=[],
                    metavar="SUBSTR=R,G,B",
                    help="diffuse tint for groups whose name contains SUBSTR")
    ap.add_argument("--headlamp", action="store_true",
                    help="light from the eye instead of a fixed direction; "
                         "for interiors, where a directional light leaves most "
                         "of a concave surface unlit")
    ap.add_argument("--fog", type=float, default=0.0,
                    help="e-folding distance in metres; fades geometry toward "
                         "--bg with range. 0 disables. Depth cue for long "
                         "interior sight lines, where flat shading alone gives "
                         "no sense of a kilometre of drum receding")
    ap.add_argument("--bloom", type=float, default=1.0,
                    help="glow radius multiplier; 0 disables")
    a = ap.parse_args()

    verts, tris, groups = load_obj(a.obj)
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

    # A triangle straddling the near plane used to be dropped whole. Outside the
    # hull nothing is ever that close and it never showed; standing on the drum
    # floor, the quad you are standing on straddles it, and so does every quad
    # nearer than one tessellation step. The near field rendered as a black band
    # and read as missing geometry. Clip properly instead of rejecting.
    NEAR = 1.0
    din = depth[tris] > NEAR
    visible = facing & ok & din.any(axis=1)
    fully_in = din.all(axis=1)
    # Sort on clamped depth so a clipped triangle sorts by the part that
    # survives, not by a vertex behind the eye with a meaningless depth.
    tri_depth = np.maximum(depth, NEAR)[tris].mean(axis=1)

    def screen_poly(t):
        """Screen-space polygon for triangle `t`, near-plane clipped."""
        idx = tris[t]
        if fully_in[t]:
            return [(sx[i], sy[i]) for i in idx]
        pts, P = [], [cam[i] for i in idx]
        for i in range(3):
            p, q = P[i], P[(i + 1) % 3]
            dp, dq = -p[2] - NEAR, -q[2] - NEAR
            if dp >= 0:
                pts.append(p)
            if (dp >= 0) != (dq >= 0):
                pts.append(p + (q - p) * (dp / (dp - dq)))
        if len(pts) < 3:
            return None
        return [(a.width / 2 + p[0] * fl / -p[2],
                 a.height / 2 - p[1] * fl / -p[2]) for p in pts]

    # Parse the emissive table and resolve each triangle's group to a colour.
    emis_rules = []
    for spec in a.emissive:
        key, _, vals = spec.partition("=")
        parts = [float(x) for x in vals.split(",")]
        rgb = np.array(parts[:3], dtype=np.float64)
        energy = parts[3] if len(parts) > 3 else 1.0
        emis_rules.append((key, rgb * energy))
    emissive = np.zeros((len(tris), 3), dtype=np.float64)
    is_emis = np.zeros(len(tris), dtype=bool)
    if emis_rules:
        for i, g in enumerate(groups):
            for key, rgb in emis_rules:
                if key in g:
                    emissive[i] = rgb
                    is_emis[i] = True
                    break

    if a.pointlight is not None:
        P = np.array(a.pointlight, dtype=np.float64)
        d = P - centroid
        dist = np.linalg.norm(d, axis=1)
        lam = np.clip(np.einsum("ij,ij->i", n, d / dist[:, None]), 0, 1)
        lam *= 1.0 / (1.0 + (dist / a.pointlight_range) ** 2)
    elif a.headlamp:
        lam = np.clip(np.einsum("ij,ij->i", n, view), 0, 1)
    else:
        L = np.array(a.light, dtype=np.float64)
        L /= np.linalg.norm(L)
        lam = np.clip(np.einsum("ij,j->i", n, L), 0, 1)

    # Default albedo is the faintly warm grey the hull renders have always used.
    albedo = np.tile(np.array([1.0, 0.99, 0.94]), (len(tris), 1))
    for spec in a.tint:
        key, _, vals = spec.partition("=")
        rgb = np.array([float(x) for x in vals.split(",")], dtype=np.float64)
        for i, g in enumerate(groups):
            if key in g:
                albedo[i] = rgb
    # Ambient floor keeps unlit hull readable as form rather than silhouette.
    shade = 0.16 + 0.84 * lam

    # Range attenuation, applied to the lit term only: the ambient floor is
    # what keeps distant geometry from crushing to a silhouette, so fogging it
    # too would undo the reason it exists.
    if a.fog > 0:
        cdist = np.linalg.norm(centroid - eye, axis=1)
        shade = 0.16 + (shade - 0.16) * np.exp(-cdist / a.fog)

    order = np.argsort(-tri_depth)
    order = order[visible[order]]

    img = Image.new("RGB", (a.width, a.height), tuple(a.bg))
    d = ImageDraw.Draw(img)
    # Emissive triangles are also drawn into a separate mask so the glow can be
    # blurred and added back. Without the glow a light fitting reads as a bright
    # sticker; the spill onto nearby surfaces is what makes it read as a source.
    glow = Image.new("RGB", (a.width, a.height), (0, 0, 0))
    dg = ImageDraw.Draw(glow)
    for t in order:
        poly = screen_poly(t)
        if poly is None:
            continue
        if is_emis[t]:
            col = tuple(int(np.clip(v, 0, 1) * 255) for v in emissive[t])
            d.polygon(poly, fill=col)
            dg.polygon(poly, fill=col)
        else:
            s = np.clip(shade[t], 0, 1) * 235
            col = albedo[t] * s
            d.polygon(poly, fill=tuple(int(np.clip(v, 0, 255)) for v in col))

    if a.bloom > 0 and is_emis.any():
        from PIL import ImageChops, ImageFilter
        base = np.asarray(img).astype(np.float64)
        acc = np.zeros_like(base)
        # Three octaves: a tight core, a mid halo and a wide wash. One radius
        # gives either a hard edge or a fog, never the falloff a real fitting has.
        for radius, weight in ((3.0, 0.55), (9.0, 0.30), (26.0, 0.22)):
            b = glow.filter(ImageFilter.GaussianBlur(radius * a.bloom))
            acc += np.asarray(b).astype(np.float64) * weight
        img = Image.fromarray(np.clip(base + acc, 0, 255).astype(np.uint8))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.save(a.out)
    print(f"{a.out}  {a.width}x{a.height}  {int(visible.sum()):,}/{len(tris):,} triangles drawn")


if __name__ == "__main__":
    main()
