"""Tests for the rotating-frame physics.

Pure Python, no engine, no GPU. The maths is proven here before any of it
reaches Godot, because a sign error in Coriolis is nearly impossible to spot by
looking at a render and trivial to catch with an assertion.

Run: python3 station/physics/test_rotating_frame.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from rotating_frame import G0, DrumFrame, from_schema

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA = os.path.join(ROOT, "station/schema/station.yaml")

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def close(a, b, tol=1e-6):
    return abs(a - b) <= tol * max(1.0, abs(b))


def main():
    schema = yaml.safe_load(open(SCHEMA, encoding="utf-8"))
    drum = from_schema(schema)

    # --- canon agreement ----------------------------------------------------
    g = drum.gravity_in_g(drum.floor_radius)
    check("floor gravity is 1.0 g", close(g, 1.0, 1e-3), f"{g:.6f} g")

    rot = schema["station"]["rotation"]
    check("period matches the schema",
          close(drum.period, rot["period_s"]["value"], 1e-3),
          f"{drum.period:.3f} s vs {rot['period_s']['value']}")
    check("rpm matches the schema",
          close(drum.rpm, rot["rpm"]["value"], 2e-3),
          f"{drum.rpm:.4f} vs {rot['rpm']['value']}")

    # --- gravity gradient ---------------------------------------------------
    check("gravity is zero on the axis", close(drum.gravity_at(0.0), 0.0))
    check("gravity is linear in radius",
          close(drum.gravity_at(2 * 100.0), 2 * drum.gravity_at(100.0)))
    half = drum.radius_for_gravity(0.5)
    check("half gravity is at half the floor radius",
          close(half, drum.floor_radius / 2.0, 1e-9),
          f"{half:.2f} m of {drum.floor_radius} m")
    check("radius_for_gravity inverts gravity_in_g",
          close(drum.gravity_in_g(drum.radius_for_gravity(0.37)), 0.37))

    # --- centrifugal --------------------------------------------------------
    cf = drum.centrifugal((drum.floor_radius, 0.0, 0.0))
    check("centrifugal points radially outward", cf[0] > 0 and close(cf[1], 0.0))
    check("centrifugal has no axial component", close(cf[2], 0.0))
    check("centrifugal magnitude equals omega^2 r",
          close(math.hypot(cf[0], cf[1]), drum.gravity_at(drum.floor_radius)))
    cf_axial = drum.centrifugal((0.0, 0.0, 5000.0))
    check("a body on the axis feels no centrifugal force",
          close(math.hypot(cf_axial[0], cf_axial[1]), 0.0))

    # --- Coriolis -----------------------------------------------------------
    co = drum.coriolis((0.0, 0.0, 12.0))
    check("axial motion produces no Coriolis",
          close(co[0], 0.0) and close(co[1], 0.0) and close(co[2], 0.0))

    v = 5.0
    co = drum.coriolis((v, 0.0, 0.0))
    check("Coriolis is perpendicular to velocity",
          close(co[0] * v + co[1] * 0.0, 0.0),
          f"dot = {co[0]*v:.3e}")
    check("Coriolis magnitude is 2*omega*v",
          close(math.hypot(co[0], co[1]), 2 * drum.omega * v))

    # Climbing toward the axis (inward = -radial) must deflect spinward.
    # At +X, inward is -X; deflection should be +Y (the direction of rotation).
    co_in = drum.coriolis((-3.0, 0.0, 0.0))
    check("climbing toward the axis deflects spinward", co_in[1] > 0,
          f"lateral = {co_in[1]:+.4f} m/s^2")

    # --- apparent weight ----------------------------------------------------
    r = drum.floor_radius
    check("standing still gives exactly 1x weight",
          close(drum.apparent_weight_factor(r, 0.0), 1.0))
    w_spin = drum.apparent_weight_factor(r, 1.4)     # brisk walk, spinward
    w_anti = drum.apparent_weight_factor(r, -1.4)
    check("walking spinward increases weight", w_spin > 1.0, f"{w_spin:.4f}x")
    check("walking anti-spinward decreases weight", w_anti < 1.0, f"{w_anti:.4f}x")
    check("the effect is noticeable but not absurd at walking pace",
          0.90 < w_anti < 1.0 < w_spin < 1.12,
          f"{w_anti:.3f}x .. {w_spin:.3f}x")

    # --- frame transforms ---------------------------------------------------
    p = (120.0, -45.0, 3300.0)
    check("to_rotating inverts to_inertial",
          all(close(a, b, 1e-9) for a, b in
              zip(drum.to_rotating(drum.to_inertial(p, 7.3), 7.3), p)))
    check("transforms preserve radius",
          close(math.hypot(*drum.to_inertial(p, 11.0)[:2]), math.hypot(p[0], p[1])))
    check("transforms preserve the axial coordinate",
          close(drum.to_inertial(p, 11.0)[2], p[2]))
    check("a full period is the identity",
          all(close(a, b, 1e-6) for a, b in
              zip(drum.to_inertial(p, drum.period), p)))

    # --- launch velocity ----------------------------------------------------
    # A craft released at rest in the drum still carries the floor's tangential
    # speed in the inertial frame. That is what makes a cobra bay launch a
    # fling rather than a drop.
    vi = drum.velocity_to_inertial((r, 0.0, 4000.0), (0.0, 0.0, 0.0), 0.0)
    speed = math.hypot(vi[0], vi[1])
    check("a body at rest in the drum still moves in the inertial frame",
          close(speed, drum.floor_speed, 1e-9),
          f"{speed:.2f} m/s = floor speed")
    check("floor speed is substantial at 1 g",
          drum.floor_speed > 40.0, f"{drum.floor_speed:.1f} m/s")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
