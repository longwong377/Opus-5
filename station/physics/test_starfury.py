"""Tests for the Starfury flight model.

The point is to prove the Newtonian claims -- attitude independent of velocity,
no aerodynamic coupling, momentum conserved -- rather than to check that the
numbers look plausible.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from rotating_frame import from_schema
from starfury import Starfury, add, cross, dot, norm, scale, sub, unit

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    # --- coasting -----------------------------------------------------------
    s = Starfury(velocity=(120.0, 0.0, 0.0))
    for _ in range(1000):
        s.step(0.01)
    check("velocity is unchanged when coasting",
          abs(s.speed - 120.0) < 1e-9, f"{s.speed:.9f} m/s")
    check("position integrates to v*t",
          abs(s.position[0] - 120.0 * 10.0) < 0.5, f"{s.position[0]:.2f} m")

    # --- the defining property ---------------------------------------------
    # Rotate hard while coasting. In an aeroplane the velocity would follow the
    # nose. Here it must not move at all.
    s = Starfury(velocity=(0.0, 0.0, 200.0))
    s.angular_velocity = (0.0, 1.2, 0.0)
    v0 = s.velocity
    # Accumulate the swept angle rather than comparing start to end: at
    # 1.2 rad/s over 5 s the nose turns 344 deg, and acos of the dot product
    # wraps that to 16 deg, which would look like the craft barely moved.
    swept = 0.0
    prev = s.forward
    for _ in range(500):
        s.step(0.01)
        swept += math.degrees(math.acos(max(-1.0, min(1.0, dot(unit(prev), unit(s.forward))))))
        prev = s.forward
    check("rotating does not change velocity",
          norm(sub(s.velocity, v0)) < 1e-9,
          f"drift {norm(sub(s.velocity, v0)):.3e} m/s")
    check("the craft really did rotate while velocity held",
          swept > 300.0, f"nose swept {swept:.0f} deg with velocity unchanged")

    # --- retro burn ---------------------------------------------------------
    s = Starfury(velocity=(0.0, 0.0, 300.0))
    a = s.max_linear_accel()
    check("main thrust gives a usable acceleration",
          8.0 < a < 30.0, f"{a:.2f} m/s^2 = {a/9.80665:.2f} g")
    # Face backwards, then burn the mains to decelerate: the Starfury's
    # signature manoeuvre.
    s.orientation = (0.0, 0.0, 1.0, 0.0)      # 180 deg about Y
    full = {t.name: 1.0 for t in s.thrusters if t.name.startswith("main_")}
    for _ in range(200):
        s.step(0.01, full)
    check("flipping and burning decelerates",
          s.velocity[2] < 300.0, f"{s.velocity[2]:.1f} m/s from 300")
    check("deceleration matches thrust/mass",
          abs((300.0 - s.velocity[2]) - a * 2.0) < 1.0,
          f"lost {300.0 - s.velocity[2]:.2f} m/s, expected {a*2.0:.2f}")

    # --- torque -------------------------------------------------------------
    s = Starfury()
    f, t = s.net({t.name: 1.0 for t in s.thrusters if t.name.startswith("main_")})
    check("four symmetric mains produce no net torque",
          norm(t) < 1e-9, f"|torque| = {norm(t):.3e}")
    check("four mains produce pure forward thrust",
          f[2] > 0 and abs(f[0]) < 1e-9 and abs(f[1]) < 1e-9)

    s = Starfury()
    f, t = s.net({"main_ur": 1.0, "main_lr": 1.0})
    check("asymmetric main throttle produces yaw",
          abs(t[1]) > 1.0, f"yaw torque {t[1]:.0f} N m")

    # --- allocation ---------------------------------------------------------
    s = Starfury()
    th = s.allocate((0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
    check("forward demand opens the mains",
          all(th[n] > 0.9 for n in th if n.startswith("main_")))
    check("forward demand leaves the retro shut", th["rcs_retro"] == 0.0)
    th = s.allocate((-1.0, 0.0, 0.0), (0.0, 0.0, 0.0))
    check("lateral demand opens the correct RCS only",
          th["rcs_lat_r"] > 0.9 and th["rcs_lat_l"] == 0.0)

    # --- gyroscopic ---------------------------------------------------------
    # Spin about the axis of least inertia with a small perturbation: energy
    # must stay bounded rather than diverge.
    s = Starfury(angular_velocity=(0.05, 0.0, 2.0))
    e0 = sum(i * w * w for i, w in zip(s.inertia, s.angular_velocity))
    for _ in range(5000):
        s.step(0.002)
    e1 = sum(i * w * w for i, w in zip(s.inertia, s.angular_velocity))
    check("free rotation conserves energy",
          abs(e1 - e0) / e0 < 0.02, f"{(e1-e0)/e0*100:+.3f}%")
    check("quaternion stays normalised",
          abs(norm(s.orientation[1:]) ** 2 + s.orientation[0] ** 2 - 1.0) < 1e-9)

    # --- cobra bay launch ---------------------------------------------------
    schema = yaml.safe_load(open(os.path.join(ROOT, "station/schema/station.yaml")))
    drum = from_schema(schema)
    s = Starfury()
    v = s.launch_from_drum(drum, drum.floor_radius, 5400.0)
    check("launch inherits the drum's tangential velocity",
          abs(norm(v) - drum.floor_speed) < 1e-9,
          f"{norm(v):.2f} m/s = drum floor speed")
    # Coast clear of the station and confirm it recedes.
    r0 = math.hypot(s.position[0], s.position[1])
    for _ in range(600):
        s.step(0.05)
    r1 = math.hypot(s.position[0], s.position[1])
    check("released craft coasts away from the axis",
          r1 > r0 * 3, f"{r0:.0f} m -> {r1:.0f} m in 30 s")
    check("the station throws it clear without thrust",
          r1 - r0 > 1000.0, f"gained {r1-r0:.0f} m unpowered")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
