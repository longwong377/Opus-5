"""Tests for core shuttle and radial transit."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from core_shuttle import G0, AxialShuttle, RadialTransit, comfortable_duration
from rotating_frame import from_schema

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    schema = yaml.safe_load(open(os.path.join(ROOT, "station/schema/station.yaml")))
    drum = from_schema(schema)
    R = drum.floor_radius

    t = RadialTransit(drum, R, 0.0, 60.0)

    # --- the gravity ramp ---------------------------------------------------
    check("starts at the rim under 1 g", abs(t.gravity_in_g(0.0) - 1.0) < 1e-6,
          f"{t.gravity_in_g(0.0):.6f} g")
    check("ends weightless on the axis", t.gravity_in_g(60.0) < 1e-9,
          f"{t.gravity_in_g(60.0):.3e} g")
    check("halfway in radius is half a g",
          abs(drum.omega ** 2 * (R / 2) / G0 - 0.5) < 1e-6)
    mid = t.gravity_in_g(30.0)
    check("gravity falls monotonically through the ride",
          all(t.gravity_in_g(60.0 * i / 20) >= t.gravity_in_g(60.0 * (i + 1) / 20) - 1e-12
              for i in range(20)),
          f"midpoint {mid:.3f} g")

    # --- Coriolis -----------------------------------------------------------
    c = t.coriolis_at(30.0)
    check("inbound motion produces Coriolis", abs(c) > 0.1,
          f"{c/G0:.4f} g lateral at mid-transit")
    check("Coriolis is spinward when inbound", c < 0,
          "negative radial speed deflects spinward")
    # The endpoint values are a central-difference artifact: radius_at clamps
    # outside [0, duration], so the stencil is one-sided there. Physically the
    # smoothstep has zero derivative at both ends, and the residual is ~1e-4 g.
    check("Coriolis is negligible at rest at both ends",
          abs(t.coriolis_at(0.0)) / G0 < 1e-3 and abs(t.coriolis_at(60.0)) / G0 < 1e-3,
          f"{abs(t.coriolis_at(0.0))/G0:.2e} g at the endpoints")

    fast = RadialTransit(drum, R, 0.0, 8.0)
    check("a rushed transit throws passengers sideways",
          fast.peak_lateral_g() > 0.2,
          f"{fast.peak_lateral_g():.3f} g lateral over 8 s")
    # Measured, not assumed. Peak lateral scales as 1/duration:
    #   8 s -> 2.00 g   60 s -> 0.27 g   120 s -> 0.13 g   300 s -> 0.05 g
    # Two full minutes still leaves 0.13 g of sideways push with no visible
    # cause, which is why the transfer is slow rather than a lift ride.
    slow = RadialTransit(drum, R, 0.0, 120.0)
    check("even a two-minute transit still has noticeable lateral load",
          0.12 < slow.peak_lateral_g() < 0.15,
          f"{slow.peak_lateral_g():.4f} g over 120 s")
    check("peak lateral scales inversely with duration",
          abs(RadialTransit(drum, R, 0.0, 240.0).peak_lateral_g()
              - slow.peak_lateral_g() / 2) < 1e-4)

    d = comfortable_duration(drum, R, 0.0, max_lateral_g=0.12)
    check("a comfort limit implies a minimum transit time of over two minutes",
          120.0 < d < 180.0, f"{d:.0f} s to hold peak lateral under 0.12 g")
    check("the comfortable duration actually meets its limit",
          abs(RadialTransit(drum, R, 0.0, d).peak_lateral_g() - 0.12) < 0.002)

    # --- tangential momentum ------------------------------------------------
    check("the car must shed the drum's tangential speed",
          abs(t.tangential_speed_at(0.0) - drum.floor_speed) < 1e-9
          and t.tangential_speed_at(60.0) < 1e-9,
          f"{drum.floor_speed:.1f} m/s at the rim, 0 on the axis")
    ta = abs(t.tangential_accel_at(30.0))
    check("shedding it takes real acceleration", ta > 0.5,
          f"{ta:.3f} m/s^2 = {ta/G0:.3f} g along the direction of rotation")

    # --- axial run ----------------------------------------------------------
    sh = AxialShuttle(drum, 3107.0, 6035.0)
    check("the axial run spans the rotating assembly",
          abs(sh.distance - 2928.0) < 1.0, f"{sh.distance:.0f} m")
    tt = sh.transit_time()
    check("axial transit takes a believable time",
          60.0 < tt < 180.0, f"{tt:.1f} s end to end at 1.2 m/s^2")
    check("peak speed is sane for an interior vehicle",
          20.0 < sh.peak_speed() < 90.0, f"{sh.peak_speed():.1f} m/s")

    prof = t.profile(10)
    check("profile is sampled end to end",
          len(prof) == 11 and prof[0]["gravity_g"] > prof[-1]["gravity_g"])

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
