"""Biggest unbroken face PER GROUP, and what the half-distance frame is made of.

Two things the triangle total cannot say:
  - which surfaces are still single flat plates, and how big;
  - how much of the SCREEN each group covers, which is what a craft score is
    actually about. A group can be 60% of the triangles and 2% of the frame.
"""
import math
import os
import sys

ROOT = "/home/user/wt-judge-db"
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import docking_bay as new                                       # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "scratchpad/judge"))
from structure import biggest_face                              # noqa: E402

v, t, g = new.docking_bay()[:3]
groups = sorted(set(g))
print("=== biggest unbroken (connected, coplanar) face per group, HEAD ===")
tot = {}
for i, tri in enumerate(t):
    tot[g[i]] = tot.get(g[i], 0) + 1
out = []
for grp in groups:
    ar, cnt, ext, _ = biggest_face(v, t, g, restrict={grp})
    out.append((ar, grp, cnt, ext, tot[grp]))
for ar, grp, cnt, ext, n in sorted(out, reverse=True)[:14]:
    print(f"  {ar:9.1f} m2  {grp:<26s} {cnt:4d} tri of {n:6,}   "
          f"extent {ext[0]:7.1f} x {ext[1]:6.1f} x {ext[2]:7.1f} m")

# ---- screen coverage at the half-distance camera, by rasterising group ids --
W, H, FOV, ASP = 1280, 720, 46.0, 16 / 9
eye, tgt = (0.0, 1.70, 21.085), (0.0, 9.0, 35.0)
fwd = [tgt[k] - eye[k] for k in range(3)]
m = math.sqrt(sum(q * q for q in fwd))
fwd = [q / m for q in fwd]
right = [fwd[1] * 1.0 - fwd[2] * 0.0, fwd[2] * 0.0 - fwd[0] * 1.0,
         fwd[0] * 0.0 - fwd[1] * 0.0]
m = math.sqrt(sum(q * q for q in right)) or 1.0
right = [q / m for q in right]
up = [right[1] * fwd[2] - right[2] * fwd[1],
      right[2] * fwd[0] - right[0] * fwd[2],
      right[0] * fwd[1] - right[1] * fwd[0]]
ty = math.tan(math.radians(FOV / 2.0))
tx = ty * ASP

proj = []
for p in v:
    d = [p[k] - eye[k] for k in range(3)]
    z = sum(d[k] * fwd[k] for k in range(3))
    if z <= 0.02:
        proj.append(None)
        continue
    x = sum(d[k] * right[k] for k in range(3)) / z
    y = sum(d[k] * up[k] for k in range(3)) / z
    proj.append(((x / tx * 0.5 + 0.5) * W, (0.5 - y / ty * 0.5) * H, z))

zbuf = [[1e30] * W for _ in range(H)]
gbuf = [[None] * W for _ in range(H)]
for i, tri in enumerate(t):
    ps = [proj[q] for q in tri]
    if any(p is None for p in ps):
        continue
    xs = [p[0] for p in ps]
    ys = [p[1] for p in ps]
    x0, x1 = max(0, int(min(xs))), min(W - 1, int(max(xs)) + 1)
    y0, y1 = max(0, int(min(ys))), min(H - 1, int(max(ys)) + 1)
    if x1 < x0 or y1 < y0:
        continue
    ax, ay, az = ps[0]
    bx, by, bz = ps[1]
    cx, cy, cz = ps[2]
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12:
        continue
    for py in range(y0, y1 + 1):
        for px in range(x0, x1 + 1):
            l1 = ((by - cy) * (px + .5 - cx) + (cx - bx) * (py + .5 - cy)) / den
            l2 = ((cy - ay) * (px + .5 - cx) + (ax - cx) * (py + .5 - cy)) / den
            l3 = 1.0 - l1 - l2
            if l1 < 0 or l2 < 0 or l3 < 0:
                continue
            z = l1 * az + l2 * bz + l3 * cz
            if z < zbuf[py][px]:
                zbuf[py][px] = z
                gbuf[py][px] = g[i]

cov = {}
for row in gbuf:
    for q in row:
        cov[q] = cov.get(q, 0) + 1
print("\n=== screen coverage at the half distance (1280x720, z-buffered) ===")
for k, n in sorted(cov.items(), key=lambda kv: -kv[1])[:12]:
    print(f"  {100 * n / (W * H):6.2f}%  {k}")
