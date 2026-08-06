"""Irradiance on the docking bay's deck plane, summed the way Godot sums it.

THE POINT. `tools/export_scene.py`'s session-4m note says the bay reads as an
even sheet because "39 floods at 12.23 m through a 35 deg cone throw a 17.1 m
pool at a 14.0 m lateral and 11.67 m longitudinal pitch, so every point of the
deck is inside about ten of them and the sum is flat". That is an arithmetic
claim about the rig and it can be checked without a render, which is what this
does -- and unlike a render it can be swept over a parameter in seconds.

Godot's spot term, from `scene_forward_clustered`'s light shader:

    nd = (d/r)^4 ; att = max(1-nd, 0)^2 * d^-decay
    scos = max(dot(-normalise(rel), spot_dir), cos(angle))
    rim  = max(1e-4, (1 - scos) / (1 - cos(angle)))
    att *= 1 - rim^cone_attenuation

`render_shot.gd` builds `spot_attenuation = attenuation` (1.0) and
`spot_angle_attenuation = angle_attenuation` (0.6 default).

The statistic reported is the MODULATION DEPTH of E over the clear deck --
p95/p5 and the ratio of the mean under a lamp to the mean midway between two
-- because "pools versus a sheet" is a statement about variation, not level.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "station"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "tools"))

import export_scene as ex     # noqa: E402


def lights_for(room="docking_bays", fixture_energy=3.0):
    v, t, spans, _e = ex.interior_geometry(room)
    reach = ex.room_reach(room)
    return v, ex.fixture_lights(
        v, t, spans, fixture_energy * ex.room_exposure(room),
        ex.INTERIOR_LIGHT_RANGE_M, shadow_n=0, reach_of=reach)


def irradiance(lights, pts, normal=(0.0, 1.0, 0.0), cone_att=0.6):
    """Sum of Godot's attenuation x N.L over every source, at each point."""
    n = np.asarray(normal, dtype=float)
    tot = np.zeros(len(pts))
    P = np.asarray(pts, dtype=float)
    for lt in lights:
        c = np.asarray(lt["pos"], dtype=float)
        rel = P - c                                  # light -> surface
        d = np.linalg.norm(rel, axis=-1)
        d = np.maximum(d, 1e-4)
        r = float(lt["range"])
        nd = (d / r) ** 4
        att = np.maximum(1.0 - nd, 0.0) ** 2 * d ** (-float(
            lt.get("attenuation", 1.0)))
        if str(lt.get("kind", "omni")) == "spot":
            aim = np.asarray(lt.get("aim", (0.0, -1.0, 0.0)), dtype=float)
            aim = aim / np.linalg.norm(aim)
            ca = math.cos(math.radians(float(lt.get("angle", 45.0))))
            scos = np.maximum((rel / d[..., None]) @ aim, ca)
            rim = np.maximum(1e-4, (1.0 - scos) / (1.0 - ca))
            att = att * (1.0 - rim ** cone_att)
        ndotl = np.maximum((-rel / d[..., None]) @ n, 0.0)
        tot += att * ndotl * float(lt["energy"])
    return tot


def report(tag, lights, half_x, z0, z1, y=0.0, n=241):
    xs = np.linspace(-half_x, half_x, 61)
    zs = np.linspace(z0, z1, n)
    gx, gz = np.meshgrid(xs, zs, indexing="ij")
    pts = np.stack([gx.ravel(), np.full(gx.size, y), gz.ravel()], axis=-1)
    E = irradiance(lights, pts).reshape(gx.shape)
    p5, p50, p95 = np.percentile(E, [5, 50, 95])
    # THE LONGITUDINAL PROFILE is the one that shows pooling: the lamps repeat
    # along z at the girder pitch, so E averaged across x and read along z is
    # the sheet-versus-scallop question with the width integrated out.
    prof = E.mean(axis=0)
    depth = (prof.max() - prof.min()) / max(prof.max(), 1e-12)
    print(f"{tag:28s} n={len(lights):3d}  meanE {E.mean():7.4f}  "
          f"p5 {p5:7.4f}  p50 {p50:7.4f}  p95 {p95:7.4f}  "
          f"p95/p5 {p95 / max(p5, 1e-12):6.2f}  "
          f"long-modulation {100 * depth:5.1f}%")
    return dict(mean=float(E.mean()), p5=float(p5), p95=float(p95),
                depth=float(depth), profile=prof)


if __name__ == "__main__":
    import docking_bay as db
    v, lights = lights_for()
    ch = db.clear_half_m()
    r = report("shipped (35 deg cone)", lights, ch, 6.0, 134.0)
    # SINGLE VARIABLE: the cone alone, everything else held.
    for deg in (28.0, 22.0, 16.0):
        alt = []
        for lt in lights:
            q = dict(lt)
            if q.get("kind") == "spot":
                q["angle"] = deg
            alt.append(q)
        report(f"cone {deg:.0f} deg", alt, ch, 6.0, 134.0)
