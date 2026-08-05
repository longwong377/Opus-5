"""What light actually reaches a trunk, summed the way Godot sums it.

CLAUDE.md, session 4m: "RE-MEASURE A ROOM'S IRRADIANCE BEFORE TOUCHING ITS
EXPOSURE ... three sessions of knob-turning could not have found that." Same
question one object down: is the drum's tree dark because of its material or
because nothing is lighting it?

Godot's OmniLight3D attenuation is `pow(max(1 - d/range, 0), attenuation)`
scaled by `energy`, and a Lambert surface takes that times max(N.L, 0).
"""
import json, math, sys
import numpy as np

scene = json.load(open(sys.argv[1]))
L = scene["lights"]
pos = np.array([l["pos"] for l in L], dtype=float)
en = np.array([l["energy"] for l in L], dtype=float)
rng = np.array([l["range"] for l in L], dtype=float)
att = np.array([l["attenuation"] for l in L], dtype=float)
col = np.array([l["colour"] for l in L], dtype=float)
lum = col @ np.array([0.2126, 0.7152, 0.0722])


def E(p, n):
    """Irradiance at point p on a surface with unit normal n."""
    d = pos - np.asarray(p, dtype=float)
    dist = np.linalg.norm(d, axis=1)
    ldir = d / np.maximum(dist, 1e-9)[:, None]
    ndotl = np.maximum(ldir @ np.asarray(n, dtype=float), 0.0)
    a = np.power(np.clip(1.0 - dist / rng, 0.0, None), att)
    return float((en * lum * a * ndotl).sum()), int((a * ndotl > 0).sum())


eye = np.array([-117.091, 243.413, 4909.880])
tgt = np.array([-116.094, 241.341, 4918.880])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
# The trunk stands at the target. Its surface faces the camera: -fwd, with the
# vertical component removed, because a trunk is a vertical cylinder.
face = -fwd.copy()
r = math.hypot(tgt[0], tgt[1])
up = np.array([-tgt[0] / r, -tgt[1] / r, 0.0])       # drum "up" is toward the axis
face -= up * (face @ up)
face /= np.linalg.norm(face)
# The ground the trunk stands on: same place, normal along drum-up.
print(f"drum radius at the tree  r = {r:.1f} m")
print(f"trunk facing normal      {np.round(face,3)}")
print(f"ground normal (drum up)  {np.round(up,3)}")
print()
et, nt = E(tgt, face)
eg, ng = E(tgt + up * 0.05, up)
print(f"  vertical trunk surface   E = {et:.5f}   ({nt} of {len(L)} sources reach it)")
print(f"  the ground it stands on  E = {eg:.5f}   ({ng} of {len(L)} sources reach it)")
print(f"  ground / trunk           = {eg/max(et,1e-9):.2f}x")
print()
# And the same question over a whole circle of trunk facings, because one
# facing could be an unlucky sample.
best = worst = None
for k in range(36):
    a = k * math.tau / 36
    t1 = np.cross(up, [0, 0, 1.0]); t1 /= np.linalg.norm(t1)
    t2 = np.cross(up, t1)
    n = math.cos(a) * t1 + math.sin(a) * t2
    e, _ = E(tgt, n)
    best = e if best is None else max(best, e)
    worst = e if worst is None else min(worst, e)
print(f"  over 36 trunk facings: worst {worst:.5f}  best {best:.5f}")
print(f"  best trunk facing / ground = {best/max(eg,1e-9):.3f}x")
