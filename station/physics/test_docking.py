"""Tests for docking against the rotating station."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from docking import (DockingBay, closing_rate, contact_is_safe,
                     relative_speed, spin_match_velocity)
from rotating_frame import from_schema
from starfury import Starfury, add, norm, scale, sub

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    schema = yaml.safe_load(open(os.path.join(ROOT, "station/schema/station.yaml")))
    drum = from_schema(schema)
    bay = DockingBay(drum, drum.floor_radius, 5400.0)

    # --- the bay is a moving target -----------------------------------------
    p0, p1 = bay.position_at(0.0), bay.position_at(drum.period / 4)
    check("the bay moves a quarter turn in a quarter period",
          abs(norm(sub(p1, p0)) - drum.floor_radius * math.sqrt(2)) < 1e-6,
          f"{norm(sub(p1, p0)):.2f} m")
    check("the bay returns to itself after one period",
          norm(sub(bay.position_at(drum.period), p0)) < 1e-6)
    check("the bay's speed is the drum floor speed",
          abs(norm(bay.velocity_at(3.7)) - drum.floor_speed) < 1e-9,
          f"{norm(bay.velocity_at(3.7)):.2f} m/s")
    check("bay velocity is perpendicular to its radius",
          abs(sum(a * b for a, b in zip(bay.velocity_at(2.0), bay.normal_at(2.0)))) < 1e-9)

    # --- station-keeping is not zero velocity -------------------------------
    v = spin_match_velocity(bay, 0.0, 200.0)
    check("holding station off the bay requires real velocity",
          norm(v) > 60.0, f"{norm(v):.1f} m/s at 200 m standoff")
    check("standoff velocity exceeds bay velocity",
          norm(v) > drum.floor_speed,
          f"{norm(v):.1f} vs bay {drum.floor_speed:.1f} m/s")

    # A craft stopped dead relative to the station centre loses the bay.
    craft = Starfury(position=bay.approach_point(0.0, 200.0), velocity=(0, 0, 0))
    for _ in range(200):
        craft.step(0.05)
    t = 10.0
    drift = norm(sub(craft.position, bay.approach_point(t, 200.0)))
    check("a craft at zero velocity loses the bay within seconds",
          drift > 400.0, f"{drift:.0f} m off in {t:.0f} s")

    # --- closing rate -------------------------------------------------------
    bp, bv = bay.position_at(0.0), bay.velocity_at(0.0)
    parked = Starfury(position=bay.approach_point(0.0, 100.0), velocity=bv)
    cr = closing_rate(parked.position, parked.velocity, bp, bv)
    check("matched velocity gives near-zero closing rate",
          abs(cr) < 1e-6, f"{cr:.3e} m/s")
    check("matched velocity still means high absolute speed",
          norm(parked.velocity) > 50.0,
          f"{norm(parked.velocity):.1f} m/s absolute, {abs(cr):.2e} closing")

    inbound = Starfury(position=bay.approach_point(0.0, 100.0),
                       velocity=add(bv, scale(bay.normal_at(0.0), -3.0)))
    cr = closing_rate(inbound.position, inbound.velocity, bp, bv)
    check("approaching along the normal gives a positive closing rate",
          cr > 2.9, f"{cr:.3f} m/s")

    # --- contact gates ------------------------------------------------------
    soft = Starfury(position=bay.approach_point(0.0, 2.0),
                    velocity=add(bv, scale(bay.normal_at(0.0), -0.8)))
    r = contact_is_safe(soft.position, soft.velocity, bay, 0.0)
    check("a slow aligned approach is a safe dock", r["safe"],
          f"closing {r['closing_rate']:.2f} lateral {r['lateral_drift']:.2f} "
          f"misalign {r['misalignment_deg']:.1f} deg")

    fast = Starfury(position=bay.approach_point(0.0, 2.0),
                    velocity=add(bv, scale(bay.normal_at(0.0), -9.0)))
    check("too fast is rejected",
          not contact_is_safe(fast.position, fast.velocity, bay, 0.0)["safe"])

    # Unmatched rotation: correct closing rate, but huge lateral drift.
    unmatched = Starfury(position=bay.approach_point(0.0, 2.0),
                         velocity=scale(bay.normal_at(0.0), -0.8))
    r = contact_is_safe(unmatched.position, unmatched.velocity, bay, 0.0)
    check("failing to spin-match is rejected on lateral drift",
          not r["safe"] and r["lateral_drift"] > 40.0,
          f"lateral {r['lateral_drift']:.1f} m/s")

    # --- axial approach -----------------------------------------------------
    axial = DockingBay(drum, 0.0, 7100.0)
    check("an axial port has no tangential velocity to match",
          norm(axial.velocity_at(12.0)) < 1e-12,
          "which is why large ships use the forward sphere")
    check("an axial port does not move at all",
          norm(sub(axial.position_at(0.0), axial.position_at(17.3))) < 1e-12)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
