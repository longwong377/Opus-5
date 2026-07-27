"""Tests for double precision and floating origin at station scale.

The point of these is to demonstrate, numerically, that the scale problem is
real and that the chosen mitigation actually solves it.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from floating_origin import (FloatingOrigin, f32_error_at, f32_spacing,
                             safe_radius)

STATION_LENGTH = 8047.0
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    # --- the problem is real ------------------------------------------------
    sp_nose = f32_spacing(STATION_LENGTH)
    check("float32 spacing at the station's nose exceeds 0.25 mm",
          sp_nose > 0.00025, f"{sp_nose*1000:.3f} mm at {STATION_LENGTH:.0f} m")

    sp_far = f32_spacing(50_000.0)
    check("float32 spacing at 50 km exceeds 1 mm",
          sp_far > 0.001, f"{sp_far*1000:.2f} mm")

    # Measured, not assumed: float32 holds 1 mm resolution out to 16.4 km, so
    # the station's own 8 km is marginally survivable in float32 -- 0.49 mm at
    # the nose. What is NOT survivable is Starfury range: at 20 km spacing is
    # already 1.95 mm and at 50 km it is 3.91 mm, which is visible shimmer on
    # stationary geometry. Double precision plus a floating origin is required
    # by the flight envelope, not by the station alone.
    r = safe_radius()
    check("float32 holds 1 mm only to ~16 km, well inside Starfury range",
          STATION_LENGTH < r < 20_000.0,
          f"1 mm lost beyond {r:.0f} m; station {STATION_LENGTH:.0f} m, flight range 50 km+")

    # --- double precision is enough for the simulation ----------------------
    far = 1_000_000.0
    check("float64 holds sub-micron precision at 1000 km",
          abs((far + 1e-6) - far - 1e-6) < 1e-9)

    # --- floating origin fixes rendering ------------------------------------
    fo = FloatingOrigin(threshold_m=500.0)
    nose = (0.0, 0.0, STATION_LENGTH)
    fo.update(nose)
    err = fo.render_error(nose)
    check("rebasing at the nose reduces its render error to zero",
          err == 0.0, f"{err:.3e} m")

    fo = FloatingOrigin(threshold_m=500.0)
    viewer = (0.0, 0.0, 40_000.0)          # Starfury 40 km out
    fo.update(viewer)
    err = fo.render_error((0.0, 0.0, 40_000.0 + 250.0))
    check("a point 250 m from a viewer 40 km out renders sub-micron",
          err < 1e-5, f"{err*1e6:.3f} microns")

    # Deliberately not a round number: float32 represents integers exactly up
    # to 2^24, so testing at 40250.0 would measure zero error and prove nothing.
    off_grid = 40_000.0 + 250.37
    fo2 = FloatingOrigin(threshold_m=500.0)
    fo2.update((0.0, 0.0, 40_000.0))
    naive = f32_error_at(off_grid)
    rebased = fo2.render_error((0.0, 0.0, off_grid))
    # Rebased error is not zero -- the point still sits 250 m from the new
    # origin, where float32 spacing is ~15 um. Two orders of magnitude is what
    # the arithmetic actually delivers, so that is what is asserted.
    check("floating origin beats naive float32 by two orders of magnitude",
          naive > rebased * 100,
          f"naive {naive*1000:.4f} mm vs rebased {rebased*1e6:.4f} um "
          f"({naive/rebased:.0f}x better)")

    # --- rebasing behaviour -------------------------------------------------
    fo = FloatingOrigin(threshold_m=500.0)
    moved = [fo.update((0.0, 0.0, z)) for z in range(0, 5001, 100)]
    check("rebases only when the viewer drifts past the threshold",
          fo.rebases == sum(moved) and 5 <= fo.rebases <= 12,
          f"{fo.rebases} rebases over 5 km at a 500 m threshold")

    fo = FloatingOrigin(threshold_m=500.0)
    fo.update((1234.5, -678.9, 4321.0))
    p = (1200.0, -700.0, 4400.0)
    check("to_world inverts to_render",
          all(abs(a - b) < 1e-12 for a, b in zip(fo.to_world(fo.to_render(p)), p)))

    # Worst case: viewer at one end of the station, geometry at the other.
    fo = FloatingOrigin(threshold_m=500.0)
    fo.update((0.0, 0.0, 0.0))
    err = fo.render_error((0.0, 0.0, STATION_LENGTH))
    check("worst case across the whole station stays under 1 mm",
          err < 0.001, f"{err*1000:.4f} mm end to end")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
