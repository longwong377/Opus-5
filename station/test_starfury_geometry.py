"""Tests for the Aurora-class Starfury mesh.

The headline assertion is that `station/starfury_geometry.py` and
`station/physics/starfury.py` describe the *same craft*: every thruster the
flight model pushes on has a nozzle at that exact point in the mesh. The two
modules hold their own copies of the layout on purpose, so this is a real gate
rather than a tautology -- edit one side and it fails.

The rest checks properties that a render cannot show. An inside-out section is
invisible, not wrong-looking, so it survives visual inspection; a plate quietly
rotated into a lift surface reads fine from one angle; a cockpit too small for
a pilot only becomes obvious when someone tries to sit in it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "physics"))

import starfury_geometry as geo
from starfury import aurora_thrusters

# A Starfury is a hero asset -- flown in first person, seen from a metre away in
# a cobra bay, and fielded 24 at a time. The station's whole exterior gets
# 400,000 triangles; a squadron pair at this budget costs under half that, which
# is the trade the number is chosen to make.
TRIANGLE_BUDGET = 8_000

# A reclined pilot in a flight suit, with helmet clearance and seat structure.
COCKPIT_MIN_M = {"length": 1.85, "width": 0.90, "height": 0.95}

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    return ok


def tri_normal_area(verts, tri):
    a, b, c = (verts[i] for i in tri)
    n = geo._cross(geo._sub(b, a), geo._sub(c, a))
    mag = math.sqrt(geo._dot(n, n))
    return (geo._mul(n, 1.0 / mag) if mag > 0 else (0.0, 0.0, 0.0)), mag / 2.0


def main():
    sections = geo.build()
    all_verts = [v for s in sections.values() for v in s[0]]

    # --- the point of the whole file ----------------------------------------
    mounts = geo.thruster_mounts()
    physics = {t.name: t.position for t in aurora_thrusters()}
    check("geometry and flight model name the same thrusters",
          set(mounts) == set(physics),
          f"geometry only: {sorted(set(mounts) - set(physics))}, "
          f"physics only: {sorted(set(physics) - set(mounts))}")
    worst = max((max(abs(a - b) for a, b in zip(mounts[n], physics[n])), n)
                for n in sorted(set(mounts) & set(physics)))
    check("every thruster mount matches the flight model exactly",
          worst[0] == 0.0, f"largest disagreement {worst[0]:.6f} m on {worst[1]}")

    # --- nozzles point the way the flight model pushes -----------------------
    # The convention is that a mount point is the nozzle *exit plane* centre, so
    # a main engine's geometry must lie entirely forward of its own mount and
    # touch it. Anything else means the bell is buried, reversed, or floating.
    bells = sections["engine_bell"][0]
    for sx in (1, -1):
        for sy in (1, -1):
            cx, cy = sx * geo.BOOM_HALF_SPAN_M, sy * geo.BOOM_HALF_SPAN_M
            own = [v for v in bells
                   if math.hypot(v[0] - cx, v[1] - cy) < 1.2]
            zmin = min(v[2] for v in own)
            check(f"main_{'u' if sy > 0 else 'l'}{'r' if sx > 0 else 'l'} bell "
                  f"opens aft onto its mount plane",
                  abs(zmin - geo.ENGINE_STATION_M) < 1e-9 and len(own) > 20,
                  f"{len(own)} vertices, aftmost z = {zmin:.4f}")

    retro_z = max(v[2] for v in sections["retro_nozzle"][0])
    check("retro nozzle opens forward onto its mount plane",
          abs(retro_z - geo.RETRO_STATION_M) < 1e-9, f"forwardmost z = {retro_z:.4f}")

    # Measured along each nozzle's own axis, not as a cylindrical radius: the +x
    # nozzle's rim spreads in y, which would read as overshoot in hypot(x, y).
    for radial in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        reach = max(geo._dot(v, radial) for v in sections["rcs_nozzle"][0])
        check(f"RCS nozzle at {radial} opens outward onto its mount radius",
              abs(reach - geo.RCS_RING_RADIUS_M) < 1e-9, f"reach = {reach:.4f} m")

    # A bell that fires into its own airframe would be a mesh the flight model
    # cannot be describing, since the flight model gets full thrust from it.
    fouled = []
    for sx in (1, -1):
        for sy in (1, -1):
            cx, cy = sx * geo.BOOM_HALF_SPAN_M, sy * geo.BOOM_HALF_SPAN_M
            for v in all_verts:
                if v[2] < geo.ENGINE_STATION_M - 1e-6 and \
                        math.hypot(v[0] - cx, v[1] - cy) < 0.8:
                    fouled.append(v)
    check("nothing sits in a main engine's exhaust", not fouled,
          f"{len(fouled)} vertices aft of an exit plane and inside its plume")

    # --- winding -------------------------------------------------------------
    inverted = [n for n, (v, t) in sections.items() if geo.signed_volume(v, t) <= 0.0]
    check("every section winds outward", not inverted, str(inverted))

    degenerate = sum(1 for _n, (v, t) in sections.items()
                     for tri in t if tri_normal_area(v, tri)[1] < 1e-12)
    check("no degenerate triangles", degenerate == 0, f"{degenerate} zero-area")

    # --- symmetry ------------------------------------------------------------
    # Port/starboard only. The craft is deliberately *not* symmetric top to
    # bottom: the canopy rakes down and the gun pod hangs under the keel.
    pts = {(round(x, 6), round(y, 6), round(z, 6)) for x, y, z in all_verts}
    mirrored = {(round(-x, 6), round(y, 6), round(z, 6)) for x, y, z in all_verts}
    check("mesh is symmetric about the x = 0 plane", pts == mirrored,
          f"{len(pts ^ mirrored)} unmatched vertices")

    ventral = {(round(x, 6), round(-y, 6), round(z, 6)) for x, y, z in all_verts}
    check("mesh is NOT symmetric top to bottom", pts != ventral,
          "canopy rake and ventral gun pod break it, as they should")

    # The four boom assemblies, though, must be interchangeable: a 90 deg roll
    # has to leave the propulsion looking identical or the craft has a preferred
    # roll attitude, which is exactly what the design does not have.
    boom_pts = {(round(x, 5), round(y, 5), round(z, 5))
                for name in ("boom", "engine_pod", "engine_bell",
                             "boom_tip", "tip_vane", "root_fairing")
                for x, y, z in sections[name][0]}
    rolled = {(round(-y, 5), round(x, 5), round(z, 5)) for x, y, z in boom_pts}
    check("propulsion assembly is invariant under a 90 deg roll",
          boom_pts == rolled, f"{len(boom_pts ^ rolled)} unmatched vertices")

    # --- no lift surfaces ----------------------------------------------------
    # The structural claim is that every plate lies in the meridional plane of
    # its own boom -- the plane containing that boom's radial direction and the
    # roll axis. Its normal is then tangential: perpendicular to both. A wing
    # would fail the second half, since a horizontal plate on the upper-right
    # boom has a normal with a large radial component.
    # Measured as the fraction of surface area whose normal is tangential, not
    # as a mean over all faces: a thin plate's own edges and end caps never face
    # tangentially, and on a narrow finger they are a fifth of its area. A
    # horizontal wing on the upper-right boom would score near zero here, since
    # its broad faces point along y and |y . t| is only 0.71.
    for name, floor in (("root_fairing", 0.70), ("tip_vane", 0.60)):
        v, t = sections[name]
        area = flat = 0.0
        for tri in t:
            n, a = tri_normal_area(v, tri)
            cen = [sum(v[i][k] for i in tri) / 3.0 for k in range(3)]
            tangential = geo._unit(geo._cross(geo._unit((cen[0], cen[1], 0.0)),
                                              (0.0, 0.0, 1.0)))
            area += a
            if abs(geo._dot(n, tangential)) >= 0.9:
                flat += a
        check(f"{name} plates lie in their boom's meridional plane",
              flat / area >= floor,
              f"{flat/area*100:.0f}% of area faces tangentially (need {floor*100:.0f}%)")

    # --- bounds --------------------------------------------------------------
    # These three are consequences of INV-009, not sourced proportions --
    # reference/12-starfury/ holds no orthographic view and no scale bar, so the
    # aspect ratio follows from the flight model's thruster stations (mains and
    # retro only 4.5 m apart along z, the X spanning 6.8 m) and nothing else. If
    # a production sheet ever gives real dimensions, expect these to fail, and
    # change them rather than arguing with the sheet.
    xs, ys, zs = ([v[i] for v in all_verts] for i in range(3))
    length, span = max(zs) - min(zs), max(xs) - min(xs)
    check("craft is wider than it is long", span > length * 1.2,
          f"span {span:.2f} m, length {length:.2f} m")
    check("span and height agree (the X is square on)",
          abs(span - (max(ys) - min(ys))) < 1e-6,
          f"{span:.3f} m across, {max(ys) - min(ys):.3f} m tall")
    check("overall size is fighter-scale", 4.0 < length < 9.0 and 7.0 < span < 13.0,
          f"{length:.2f} x {span:.2f} x {max(ys) - min(ys):.2f} m")
    check("thruster mounts all lie inside the airframe envelope",
          all(min(xs) <= p[0] <= max(xs) and min(ys) <= p[1] <= max(ys)
              and min(zs) <= p[2] <= max(zs) for p in mounts.values()))

    # --- cockpit -------------------------------------------------------------
    cockpit = geo.cockpit_volume()
    for axis, floor in COCKPIT_MIN_M.items():
        check(f"cockpit {axis} fits a reclined pilot ({floor} m)",
              cockpit[f"{axis}_m"] >= floor, f"{cockpit[f'{axis}_m']:.3f} m")
    check("cockpit is reclined rather than upright",
          5.0 < cockpit["rake_deg"] < 35.0, f"{cockpit['rake_deg']:.1f} deg nose-down")

    # The volume is only useful if it is genuinely inside the shell -- otherwise
    # a seat built against it would clip through the canopy.
    escapes = []
    for i in range(21):
        f = i / 20.0
        z = cockpit["aft"][2] + f * (cockpit["forward"][2] - cockpit["aft"][2])
        y = cockpit["aft"][1] + f * (cockpit["forward"][1] - cockpit["aft"][1])
        half_w, half_h, yc = geo.canopy_section(z)
        if (cockpit["width_m"] / 2.0 > half_w
                or abs(y - yc) + cockpit["height_m"] / 2.0 > half_h):
            escapes.append(round(z, 2))
    check("cockpit volume stays inside the canopy shell", not escapes,
          f"escapes at z = {escapes}")

    # --- budget and determinism ---------------------------------------------
    tris = sum(len(t) for _v, t in sections.values())
    check(f"within the triangle budget ({TRIANGLE_BUDGET:,})", tris <= TRIANGLE_BUDGET,
          f"{tris:,} triangles in {len(sections)} sections")

    again = geo.build()
    check("generation is deterministic",
          all(again[k] == sections[k] for k in sections) and set(again) == set(sections))

    check("the cockpit is an addressable section",
          {"cockpit_canopy", "cockpit_glazing", "canopy_frame"} <= set(sections))

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
