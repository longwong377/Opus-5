"""Is the +10,240 triangles STRUCTURE, or lighting and materials dressing a box?

Three measurements, all on the geometry rather than on a picture:

  1. per-group triangle and area delta, pre-fix (a3d414e) against HEAD;
  2. the biggest UNBROKEN face -- connected, coplanar triangles merged into one
     region, area and extent. A 100 m flat plane is a box whatever is painted
     on it, and this is the number that says whether one is there;
  3. what is actually inside the half-distance frustum, because a triangle
     added behind the eye is not evidence about the frame that was scored.
"""
import importlib.util
import math
import os
import sys

ROOT = "/home/user/wt-judge-db"
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

spec = importlib.util.spec_from_file_location(
    "docking_bay_old", os.path.join(ROOT, "scratchpad/judge/docking_bay_old.py"))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
import docking_bay as new                                       # noqa: E402


def area(v, tri):
    a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cx = u[1] * w[2] - u[2] * w[1]
    cy = u[2] * w[0] - u[0] * w[2]
    cz = u[0] * w[1] - u[1] * w[0]
    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def normal(v, tri):
    a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
         u[0] * w[1] - u[1] * w[0])
    m = math.sqrt(sum(q * q for q in n)) or 1.0
    return (n[0] / m, n[1] / m, n[2] / m)


def by_group(v, t, g):
    out = {}
    for i, tri in enumerate(t):
        n, a = out.get(g[i], (0, 0.0))
        out[g[i]] = (n + 1, a + area(v, tri))
    return out


def biggest_face(v, t, g, restrict=None):
    """Largest connected set of coplanar triangles: area, extent, group."""
    key = {}
    for i, p in enumerate(v):
        key.setdefault((round(p[0], 4), round(p[1], 4), round(p[2], 4)),
                       []).append(i)
    canon = {}
    for ks in key.values():
        for i in ks:
            canon[i] = ks[0]
    edges = {}
    idx = [i for i in range(len(t)) if restrict is None or g[i] in restrict]
    for i in idx:
        a, b, c = (canon[q] for q in t[i])
        for p, q in ((a, b), (b, c), (c, a)):
            edges.setdefault((min(p, q), max(p, q)), []).append(i)
    nrm = {i: normal(v, t[i]) for i in idx}
    plane = {}
    for i in idx:
        n = nrm[i]
        p = v[t[i][0]]
        plane[i] = n[0] * p[0] + n[1] * p[1] + n[2] * p[2]
    seen, best = set(), (0.0, None, None, None)
    for s in idx:
        if s in seen:
            continue
        stack, comp = [s], []
        seen.add(s)
        while stack:
            i = stack.pop()
            comp.append(i)
            a, b, c = (canon[q] for q in t[i])
            for p, q in ((a, b), (b, c), (c, a)):
                for j in edges.get((min(p, q), max(p, q)), ()):
                    if j in seen:
                        continue
                    dot = sum(nrm[i][k] * nrm[j][k] for k in range(3))
                    if dot > 0.9999 and abs(plane[i] - plane[j]) < 1e-4:
                        seen.add(j)
                        stack.append(j)
        ar = sum(area(v, t[i]) for i in comp)
        if ar > best[0]:
            pts = [v[q] for i in comp for q in t[i]]
            ext = tuple(max(p[k] for p in pts) - min(p[k] for p in pts)
                        for k in range(3))
            best = (ar, len(comp), ext, g[comp[0]])
    return best


def in_frustum(v, t, eye, target, fov_deg=46.0, aspect=16 / 9):
    fwd = [target[k] - eye[k] for k in range(3)]
    m = math.sqrt(sum(q * q for q in fwd))
    fwd = [q / m for q in fwd]
    up0 = (0.0, 1.0, 0.0)
    right = [fwd[1] * up0[2] - fwd[2] * up0[1],
             fwd[2] * up0[0] - fwd[0] * up0[2],
             fwd[0] * up0[1] - fwd[1] * up0[0]]
    m = math.sqrt(sum(q * q for q in right))
    right = [q / m for q in right]
    up = [right[1] * fwd[2] - right[2] * fwd[1],
          right[2] * fwd[0] - right[0] * fwd[2],
          right[0] * fwd[1] - right[1] * fwd[0]]
    ty = math.tan(math.radians(fov_deg / 2.0))
    tx = ty * aspect
    inside = set()
    for i, p in enumerate(v):
        d = [p[k] - eye[k] for k in range(3)]
        z = sum(d[k] * fwd[k] for k in range(3))
        if z <= 0.05:
            continue
        x = sum(d[k] * right[k] for k in range(3)) / z
        y = sum(d[k] * up[k] for k in range(3)) / z
        if abs(x) <= tx and abs(y) <= ty:
            inside.add(i)
    return [i for i, tri in enumerate(t) if any(q in inside for q in tri)]


ov, ot, og = old.docking_bay()[:3]
nv, nt, ng = new.docking_bay()[:3]
o, n = by_group(ov, ot, og), by_group(nv, nt, ng)

print("=== per-group triangles, pre-fix (a3d414e) -> HEAD (dd705ec) ===")
rows = []
for k in sorted(set(o) | set(n)):
    a, b = o.get(k, (0, 0.0)), n.get(k, (0, 0.0))
    if a[0] != b[0]:
        rows.append((b[0] - a[0], k, a[0], b[0], a[1], b[1]))
for d, k, a0, b0, aa, ba in sorted(rows, reverse=True):
    print(f"  {d:+7,}  {k:<26s} {a0:6,} -> {b0:6,} tri   "
          f"{aa:9.1f} -> {ba:9.1f} m2")
print(f"  {len(nt) - len(ot):+7,}  TOTAL{'':<21s} {len(ot):6,} -> {len(nt):6,}")

print("\n=== the biggest UNBROKEN face (connected coplanar region) ===")
for tag, (v, t, g) in (("pre-fix", (ov, ot, og)), ("HEAD", (nv, nt, ng))):
    ar, cnt, ext, grp = biggest_face(v, t, g)
    print(f"  {tag:<8s} {ar:9.1f} m2 over {cnt:4d} triangles, extent "
          f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} m, group '{grp}'")

print("\n=== the half-distance frustum: eye (0,1.70,21.085) -> (0,9.0,35.0) "
      "fov 46 deg, 16:9 ===")
for tag, (v, t, g) in (("pre-fix", (ov, ot, og)), ("HEAD", (nv, nt, ng))):
    idx = in_frustum(v, t, (0.0, 1.70, 21.085), (0.0, 9.0, 35.0))
    grp = {}
    for i in idx:
        grp[g[i]] = grp.get(g[i], 0) + 1
    print(f"  {tag:<8s} {len(idx):6,} of {len(t):,} triangles touch the "
          f"frustum ({100 * len(idx) / len(t):.1f}%), {len(grp)} groups")
    if tag == "HEAD":
        head_grp = grp
    else:
        pre_grp = grp
print("  delta by group inside the frustum:")
for k in sorted(set(pre_grp) | set(head_grp),
                key=lambda k: -(head_grp.get(k, 0) - pre_grp.get(k, 0))):
    d = head_grp.get(k, 0) - pre_grp.get(k, 0)
    if d:
        print(f"    {d:+6,}  {k:<26s} {pre_grp.get(k, 0):5,} -> "
              f"{head_grp.get(k, 0):5,}")
