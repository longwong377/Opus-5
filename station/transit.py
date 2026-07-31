#!/usr/bin/env python3
"""How long it takes to get anywhere, and why the station's own shape decides it.

The owner asked how long it takes to cross the station on foot and by each
transport. On foot was answerable and by transport was not: `tram.py` and
`core_tube.py` build a vehicle and a tube with **no motion in them at all**, so
the geometry existed and the system did not.

WHAT WAS ALREADY HERE, because most of this is not new and pretending otherwise
would duplicate it. `station/physics/core_shuttle.py` models the radial climb
and the axial run; `station/npc/navigation.py` section 3 already derives the
Coriolis speed cap, the lift ride, the axial ride and the dwell. **Neither knows
the guideway tram exists.** `navigation.py`'s own docstring asserts *"the
guideway tram runs along the axis where Coriolis is exactly zero and is fast"*
and then never gives it a speed, a stop, or a headway. This module supplies the
missing line, composes all four into journeys, and cross-checks every shared
number against the module that owns it -- `_selftest` reads
`navigation.MAX_LATERAL_G` and `core_shuttle`'s own default arguments through
`inspect.signature`, so a change there fires here rather than drifting.

THE FOUR SYSTEMS, AND THE GEOMETRY IS WHAT MAKES THEM DIFFERENT
---------------------------------------------------------------
Everything below follows from one fact: the station spins, so a Coriolis term
appears on any motion that is **not parallel to the spin axis**. That single
distinction sorts the four systems into fast and slow and it is not a design
choice anyone made.

  * **The core shuttle** runs on the axis, along z. Coriolis is *identically*
    zero (omega x v = 0 when v is parallel to omega). It is fast.
  * **The guideway tram** runs along z at r = 236.6 m, slung under the trusses
    `interior.guideway_truss` puts in the spoke planes. Also axial, also zero
    Coriolis, also fast -- and it is fast *at 0.85 g in open air over the
    Garden*, which no other transit system in fiction gets to be.
  * **The ground tram** runs around the drum's circumference. Its Coriolis is
    **radial**, so it does not push you sideways -- it changes what you weigh,
    and it changes it in *opposite directions* depending on which way you ride.
  * **The spoke lifts** run radially. Their Coriolis is **tangential**: a
    sideways push with no visible cause, which is the least tolerable kind, and
    it is why a 278 m ride takes 133 seconds.

CORIOLIS IS NOT ONE NUMBER, IT IS THREE, and the difference between them is the
whole reason this station needs four transit systems instead of one. See
`coriolis_report()`.

THE SPEEDS ARE OUTPUTS, NOT INPUTS
-----------------------------------
Nothing here picks a speed. Two comfort bounds and the stop spacing are the
inputs, and peak speed falls out of the motion profile:

  * **0.12 g** on an acceleration with no visible cause. Not invented here --
    it is `physics/core_shuttle.comfortable_duration`'s default and the number
    that produces the 133 s spoke ride `LOCATIONS.md` section 9 quotes.
  * **1.2 m/s^2** longitudinal, `physics/core_shuttle.AxialShuttle`'s default.
  * **0.6 m/s^3** of jerk, which is INV-094 and the only new comfort bound: it
    is `accel / 2.0 s`, a ramp long enough for a standing passenger to complete
    a stance shift inside it.

Feed those a stop spacing and `ride_profile()` returns the ride time and the
peak speed. **The peak speed is whatever the profile reaches.** That is the
difference between deriving a speed and choosing one, and it is why the
guideway tram comes out at 26.7 m/s rather than at a number that sounded right.

WHERE THE STOPS ARE, AND THEY ARE FORCED
-----------------------------------------
The guideway tram's five stops are not spaced by taste. Three of its stops are
fixed by structure -- the two drum end caps, which is where the truss starts and
stops, and the spoke crossing at mid-drum, which is the only place in the drum
you can transfer to anything. Even spacing plus those three forces an **odd**
number of stops. Three stops would put 1,293 m between them, which is a
14-minute walk to a stop; five brings it to 646.5 m, a 3.6-minute walk, inside
the 5-minute catchment that is the standard planning figure. Five is therefore
the *fewest* stops that satisfy all four constraints, and `_selftest` asserts
that four fails and that three fails, which is what makes the rule a rule.

A TRANSIT TIME THAT IGNORES HEADWAY IS A LIE
---------------------------------------------
Every journey below carries a wait. Headway is **derived**, not stated: it is
the round trip divided by the cars on the line, and the car counts come from
`tram.drum_trams`'s own `per_guideway` default and from
`navigation.CORE_SHUTTLE_CARS`. Mean wait for a passenger who arrives without
consulting a timetable is half the headway. Where that produces an
embarrassing number -- the spoke lifts, at one car per shaft -- the number is
reported rather than tuned away, because it is a real finding about how many
cars the station needs.

Run `python3 station/transit.py` for the gate and `--table` for the journeys.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "physics"))

import interior as it

G0 = 9.80665


# ---------------------------------------------------------------------------
# Comfort bounds. Every one of these is owned by another module; the values are
# restated here so this file reads on its own, and `_selftest` asserts each one
# against its owner so the restatement cannot drift into a second opinion.
# ---------------------------------------------------------------------------

# The station's bound on an acceleration a passenger cannot see the cause of.
# `physics/core_shuttle.comfortable_duration(max_lateral_g=...)` and
# `npc/navigation.MAX_LATERAL_G`.
COMFORT_LATERAL_G = 0.12

# Longitudinal cruise acceleration. `physics/core_shuttle.AxialShuttle`'s
# `cruise_accel` default and `npc/navigation.AXIAL_ACCEL_M_S2`. Note it is
# 0.1224 g -- the same comfort bound arrived at from the other direction.
CRUISE_ACCEL_M_S2 = 1.2

# INV-094. Jerk limit, and the anchor is the RAMP TIME rather than the figure:
# 2.0 s is long enough for a standing passenger to complete a voluntary stance
# shift inside the ramp, so the acceleration arrives as a push rather than a
# jolt. 1.2 / 2.0 = 0.6, which lands inside the 0.3-1.0 m/s^3 band transit
# practice uses. What would overturn it: a Season 2-3 frame of a passenger
# standing unsupported in a moving car.
JERK_M_S3 = CRUISE_ACCEL_M_S2 / 2.0

# Station dwell. `npc/navigation.TRANSIT_DWELL_S`, an extrapolation there.
DWELL_S = 20.0

# The planning catchment for a stop: how far someone will walk to reach one.
# 5 minutes is the standard figure and it is stated as a TIME, so it converts
# to a different distance in each sector's gravity, which is the point.
CATCHMENT_WALK_S = 300.0


def omega(schema):
    return schema["station"]["rotation"]["omega_rad_s"]["value"]


def gravity_g(schema, r):
    """Spin gravity at radius r, in g. omega^2 r / g0."""
    w = omega(schema)
    return w * w * r / G0


def walk_speed(g):
    """Preferred walking speed at local gravity `g`, in m/s.

    Delegated to `npc/navigation.walk_speed` rather than restated: it derives
    from the Froude number and the project's own measured leg length, and a
    second copy of that here is the two-sources-of-truth defect. Imported
    lazily so `tram.py` importing this module does not drag in the navmesh.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "npc"))
    import navigation as nv                                   # noqa: PLC0415
    return nv.walk_speed(g)


# ---------------------------------------------------------------------------
# The motion profile
# ---------------------------------------------------------------------------

def _ramp(v, accel, jerk):
    """(time, distance) to go from rest to `v` under an accel and a jerk limit.

    Two regimes. Above v = accel^2 / jerk the acceleration has time to reach
    its limit and the ramp is jerk-up, hold, jerk-down; below it, the hold
    phase would be negative and the ramp is two jerk phases back to back.

    The distance is exactly v*t/2 in BOTH regimes, which is not an
    approximation: the acceleration profile is symmetric about the ramp's
    midpoint, so the velocity curve is point-symmetric about (t/2, v/2).
    `_selftest` checks that against a numeric integration of the real profile,
    because "it is exact" is the kind of claim that is worth being able to
    falsify.
    """
    if v <= 0.0:
        return 0.0, 0.0
    t = v / accel + accel / jerk if v >= accel * accel / jerk \
        else 2.0 * math.sqrt(v / jerk)
    return t, 0.5 * v * t


def ride_profile(distance_m, accel=CRUISE_ACCEL_M_S2, jerk=JERK_M_S3,
                 v_max=None):
    """Time and peak speed for one stop-to-stop leg.

    THE PEAK SPEED IS AN OUTPUT. Given a distance, an acceleration limit and a
    jerk limit, the fastest comfortable run is the one that accelerates until
    it has to start braking; whatever speed that reaches is the line's speed.
    `v_max` exists so a caller with an independent cap -- the Coriolis cap, for
    a line that runs across the spin -- can impose it and get a cruise phase.

    Solved in closed form. With no cruise phase the whole distance is two
    ramps, so 2 * v/2 * (v/a + a/j) = D, a quadratic in v.
    """
    if distance_m <= 0.0:
        return {"time_s": 0.0, "peak_speed_m_s": 0.0, "cruise_s": 0.0,
                "distance_m": 0.0, "accel_limited": True}
    knee = accel * accel / jerk
    disc = (knee) ** 2 + 4.0 * accel * distance_m
    v = (-knee + math.sqrt(disc)) / 2.0
    if v < knee:
        # Below the knee the ramp never reaches the accel limit: 2*v*sqrt(v/j)
        # = D, so v = (D*sqrt(j)/2)^(2/3).
        v = (distance_m * math.sqrt(jerk) / 2.0) ** (2.0 / 3.0)
    capped = v_max is not None and v > v_max
    if capped:
        v = v_max
    t_ramp, d_ramp = _ramp(v, accel, jerk)
    cruise = (distance_m - 2.0 * d_ramp) / v if capped else 0.0
    return {"time_s": 2.0 * t_ramp + cruise, "peak_speed_m_s": v,
            "cruise_s": cruise, "distance_m": distance_m,
            "accel_limited": not capped}


def _integrate_profile(distance_m, accel, jerk, v_max=None, steps=200000):
    """Numeric integration of the real seven-phase profile.

    The negative control on `ride_profile`'s closed form. Builds the jerk
    timeline explicitly and integrates it, so it shares no algebra with the
    thing it checks -- if the closed form is wrong this disagrees.
    """
    p = ride_profile(distance_m, accel, jerk, v_max)
    v_pk = p["peak_speed_m_s"]
    t_ramp, _d = _ramp(v_pk, accel, jerk)
    t_j = min(accel / jerk, t_ramp / 2.0)
    t_hold = max(0.0, t_ramp - 2.0 * t_j)
    total = 2.0 * t_ramp + p["cruise_s"]
    dt = total / steps
    # Peak acceleration actually used: below the knee it is jerk * t_j.
    a_pk = accel if v_pk >= accel * accel / jerk else jerk * t_j

    def a_at(t):
        if t < t_j:
            return jerk * t
        if t < t_j + t_hold:
            return a_pk
        if t < t_ramp:
            return a_pk - jerk * (t - t_j - t_hold)
        if t < t_ramp + p["cruise_s"]:
            return 0.0
        u = t - t_ramp - p["cruise_s"]
        if u < t_j:
            return -jerk * u
        if u < t_j + t_hold:
            return -a_pk
        return -a_pk + jerk * (u - t_j - t_hold)

    v = d = 0.0
    v_seen = 0.0
    for k in range(steps):
        v += a_at((k + 0.5) * dt) * dt
        v_seen = max(v_seen, v)
        d += v * dt
    return {"time_s": total, "distance_m": d, "peak_speed_m_s": v_seen,
            "end_speed_m_s": v}


# ---------------------------------------------------------------------------
# Coriolis -- three directions, three completely different consequences
# ---------------------------------------------------------------------------

def coriolis_speed_cap(schema, max_lateral_g=COMFORT_LATERAL_G):
    """Speed at which 2*omega*v reaches the comfort bound.

    Applies to radial AND tangential motion, because the Coriolis magnitude
    does not care which of the two it is -- only its DIRECTION differs, and
    that is what `coriolis_report` is about.
    """
    return max_lateral_g * G0 / (2.0 * omega(schema))


def apparent_weight_g(schema, r, u_spinward):
    """What a passenger weighs, in g, riding tangentially at `u_spinward`.

    Three terms, and the middle one is the interesting one:

        omega^2 r     the spin gravity that is there when you stand still
        2 omega u     Coriolis. Radially OUTWARD for spinward motion, so
                      spinward is heavier and anti-spinward is lighter
        u^2 / r       the centripetal term of the relative motion. Same sign
                      BOTH ways, so it does not cancel out of the difference

    Cross-checked against the inertial frame: total tangential speed is
    omega*r + u, so the centripetal requirement is (omega*r + u)^2 / r, which
    expands to exactly those three terms. `_selftest` asserts the identity.
    """
    w = omega(schema)
    return (w * w * r + 2.0 * w * u_spinward + u_spinward * u_spinward / r) / G0


def coriolis_report(schema, u_ring=None, v_radial=None):
    """The three motion directions, and what each one does to a passenger.

    This is the arithmetic that decides the station's transit architecture, so
    it is computed rather than described.
    """
    w = omega(schema)
    cap = coriolis_speed_cap(schema)
    u = cap if u_ring is None else u_ring
    v = cap if v_radial is None else v_radial
    # The drum is identified by GEOMETRY, not by the name C-003/C-004 argue
    # about -- `drum_sector` exists precisely so this does not wait on a label.
    sch, prof = it.load()
    r_floor = it.sector_radius(sch, prof, it.drum_sector(sch, prof))
    r_guide = r_floor * it.TRUSS_RADIUS_FRAC

    spin = apparent_weight_g(schema, r_floor, +u)
    anti = apparent_weight_g(schema, r_floor, -u)
    return {
        "omega_rad_s": w,
        "cap_m_s": cap,
        "axial": {
            # omega x v = 0 when v is parallel to omega. Not "small": zero.
            "coriolis_g": 0.0,
            "radius_m": r_guide,
            "static_weight_g": gravity_g(schema, r_guide),
            "speed_m_s": None,
            "note": "exactly zero at any speed",
        },
        "tangential": {
            "radius_m": r_floor,
            "speed_m_s": u,
            "coriolis_g": 2.0 * w * u / G0,
            "relative_centrifugal_g": u * u / r_floor / G0,
            "spinward_weight_g": spin,
            "antispinward_weight_g": anti,
            "weight_swing_g": spin - anti,
            "weight_ratio": spin / anti,
        },
        "radial": {
            "radius_m": r_floor,
            "speed_m_s": v,
            "coriolis_g": 2.0 * w * v / G0,
            "tangential_speed_to_shed_m_s": w * r_floor,
            "shed_rate_m_s2": w * v,
            "note": "a sideways push with no visible cause; half of it is the "
                    "rate the co-rotation speed changes and half is Coriolis "
                    "proper",
        },
    }


# ---------------------------------------------------------------------------
# The lines
# ---------------------------------------------------------------------------

# Cars on each line. The guideway figure is `tram.drum_trams`'s `per_guideway`
# default, so the vehicle module and this one cannot disagree about how many
# cars exist; `_selftest` reads it out of the signature. The rest are
# `navigation.CORE_SHUTTLE_CARS` / `GROUND_TRAM_CARS` / `SPOKE_LIFT_CARS`.
CARS_PER_GUIDEWAY = 2
CORE_SHUTTLE_CARS = 6
GROUND_TRAM_CARS = 4
SPOKE_LIFT_CARS = 1

# The core shuttle's stop count is authority 4 -- a fan source, cited in
# `LOCATIONS.md` section 9 alongside the Blue-to-Grey run. The SPACING that
# follows from it is ours.
CORE_SHUTTLE_STOPS = 13


def _even_stops(z0, z1, n):
    return [z0 + (z1 - z0) * i / (n - 1) for i in range(n)]


def guideway_line(schema, profile, sector=None):
    """The drum guideway tram: axial, r = 236.6 m, five stops. INV-095.

    Everything here is read off the structure `interior.py` already builds.
    The truss runs the sector's full extent, so the termini are the end caps;
    `drum_spokes` puts its spokes at mid-z, so the middle stop is the spoke
    crossing; and the infill count is the smallest that brings the walk to a
    stop inside the catchment. See `stop_rule()`, which is what makes that a
    derivation rather than an assertion.
    """
    schema_, profile_ = schema, profile
    sector = sector or it.drum_sector(schema_, profile_)
    ex = schema_["sectors"]["extents_m"][sector]
    r0 = it.sector_radius(schema_, profile_, sector)
    n = stop_rule(schema_, ex["z1"] - ex["z0"],
                  gravity_g(schema_, r0), must_include_mid=True)
    return {
        "key": "guideway_tram",
        "name": "The drum guideway tram",
        "kind": "axial",
        "radius_m": r0 * it.TRUSS_RADIUS_FRAC,
        "gravity_g": gravity_g(schema_, r0 * it.TRUSS_RADIUS_FRAC),
        "z0": float(ex["z0"]), "z1": float(ex["z1"]),
        "stops_z": _even_stops(float(ex["z0"]), float(ex["z1"]), n),
        "stops": n,
        "lines": it.TRUSS_COUNT,
        "cars_per_line": CARS_PER_GUIDEWAY,
        "v_cap_m_s": None,                 # axial: Coriolis imposes none
        "ring": False,
        # Reaching a stop on the guideway means climbing from the floor to the
        # bottom chord, and that climb is RADIAL, so it is Coriolis-capped even
        # though the ride is not. Every guideway journey pays this twice, and a
        # model that omits it understates the trip by more than a minute.
        "access_climb_m": r0 - r0 * it.TRUSS_RADIUS_FRAC,
    }


def ground_line(schema, profile, sector=None):
    """The ground-level ring tram: circumferential, on the floor. INV-096.

    Its stop count is forced by interchange rather than by catchment: there is
    one stop under each guideway, so the two drum systems meet. That is
    `interior.SPOKE_COUNT`, not a number chosen here.
    """
    sector = sector or it.drum_sector(schema, profile)
    r0 = it.sector_radius(schema, profile, sector)
    circ = 2.0 * math.pi * r0
    n = it.SPOKE_COUNT
    return {
        "key": "ground_tram",
        "name": "The ground-level ring tram",
        "kind": "tangential",
        "radius_m": r0,
        "gravity_g": gravity_g(schema, r0),
        "circumference_m": circ,
        "stops": n,
        "stops_theta_deg": [360.0 * i / n for i in range(n)],
        "lines": 1,
        "cars_per_line": GROUND_TRAM_CARS,
        "v_cap_m_s": coriolis_speed_cap(schema),
        "ring": True,
        "access_climb_m": 0.0,
    }


def core_shuttle_line(schema, profile):
    """The axial core shuttle. Thirteen stops, Grey to Blue. INV-097.

    The run is the two sector faces the fan source names -- Grey's aft face to
    Blue's fore face -- and the stop count is that source's. Only the spacing
    is ours. Both are recorded in `LOCATIONS.md` section 9 at authority 4.
    """
    ex = schema["sectors"]["extents_m"]
    z0, z1 = float(ex["grey"]["z0"]), float(ex["blue"]["z1"])
    return {
        "key": "core_shuttle",
        "name": "The core shuttle",
        "kind": "axial",
        "radius_m": 19.5,                  # core_tube.CORE_TUBE_R_M
        "gravity_g": gravity_g(schema, 19.5),
        "z0": z0, "z1": z1,
        "stops_z": _even_stops(z0, z1, CORE_SHUTTLE_STOPS),
        "stops": CORE_SHUTTLE_STOPS,
        "lines": 1,
        "cars_per_line": CORE_SHUTTLE_CARS,
        "v_cap_m_s": None,
        "ring": False,
        "access_climb_m": 0.0,             # the radial climb is a separate leg
    }


def spoke_line(schema, profile, sector=None):
    """The radial transport tubes. Rim to axis, and the slowest thing here."""
    sector = sector or it.drum_sector(schema, profile)
    rings = it.ring_radii(schema, profile, sector)
    sub = next(r for r in rings if r["kind"] == "deck_stack")
    core = next(r for r in rings if r["kind"] == "core")
    return {
        "key": "spoke_lift",
        "name": "The radial transport tubes",
        "kind": "radial",
        "r_outer_m": sub["r_outer"],
        "r_inner_m": core["r_mid"],
        "stops": 2,
        "lines": it.SPOKE_COUNT,
        "cars_per_line": SPOKE_LIFT_CARS,
        "v_cap_m_s": coriolis_speed_cap(schema),
        "ring": False,
        "access_climb_m": 0.0,
    }


def stop_rule(schema, length_m, g, must_include_mid=False,
              catchment_s=CATCHMENT_WALK_S):
    """Fewest evenly-spaced stops meeting the catchment, ends included.

    The catchment is stated as a WALKING TIME, so it converts to a different
    distance in each sector's gravity -- which is the honest form: a five
    minute walk in Grey's 1.69 g covers 583 m and in Yellow's 0.559 g covers
    335 m, and a station planned in metres would get one of them wrong.

    `must_include_mid` forces an odd count, because a stop has to land on the
    drum's spoke crossing for the guideway tram to interchange with anything.
    That constraint is what takes the answer from four stops to five.
    """
    reach = walk_speed(g) * catchment_s
    n = 3 if must_include_mid else 2
    while (length_m / (n - 1)) / 2.0 > reach:
        n += 2 if must_include_mid else 1
    return n


# ---------------------------------------------------------------------------
# Ride time, round trip and headway
# ---------------------------------------------------------------------------

def leg_time(schema, line, distance_m):
    """One stop-to-stop leg on `line`, in seconds."""
    return ride_profile(distance_m, v_max=line["v_cap_m_s"])["time_s"]


def line_report(schema, line):
    """Speed, ride, round trip and headway for one line. All derived."""
    n = line["stops"]
    if line["ring"]:
        spacing = line["circumference_m"] / n
        legs, dwells_out = n, n            # a lap returns to where it started
        run = line["circumference_m"]
    else:
        run = (line["z1"] - line["z0"]) if "z1" in line \
            else (line["r_outer_m"] - line["r_inner_m"])
        spacing = run / (n - 1)
        legs, dwells_out = n - 1, n - 2

    if line["kind"] == "radial":
        # A lift is one continuous move, not a chain of legs, and the project
        # already models it as a smoothstep whose peak is 1.5x its mean. Kept
        # rather than replaced so this agrees with `navigation.lift_ride_s`
        # and with `core_shuttle.comfortable_duration` to four figures.
        one_way = 1.5 * run / line["v_cap_m_s"]
        spacing = run
        legs, dwells_out = 1, 0
    else:
        one_way = legs * leg_time(schema, line, spacing) + dwells_out * DWELL_S

    pk = ride_profile(spacing, v_max=line["v_cap_m_s"])
    if line["ring"]:
        round_trip = one_way                      # a lap IS the round trip
    else:
        round_trip = 2.0 * one_way + 2.0 * DWELL_S
    cars = line["cars_per_line"]
    headway = round_trip / cars
    return {
        "key": line["key"], "name": line["name"], "kind": line["kind"],
        "stops": n, "spacing_m": spacing, "run_m": run,
        "peak_speed_m_s": pk["peak_speed_m_s"],
        "peak_speed_kmh": pk["peak_speed_m_s"] * 3.6,
        "leg_s": pk["time_s"] if line["kind"] != "radial" else one_way,
        "end_to_end_s": one_way,
        "round_trip_s": round_trip,
        "cars_per_line": cars,
        "headway_s": headway,
        "mean_wait_s": headway / 2.0,
        "accel_limited": pk["accel_limited"],
        "gravity_g": line["gravity_g"] if "gravity_g" in line else None,
    }


def all_lines(schema, profile):
    return [guideway_line(schema, profile), ground_line(schema, profile),
            core_shuttle_line(schema, profile), spoke_line(schema, profile)]


# ---------------------------------------------------------------------------
# Journeys
# ---------------------------------------------------------------------------
# Legs are explicit. A Dijkstra over an invented graph produces a number nobody
# can check, and the owner's question deserves a table anyone can add up by
# hand. Each leg says what it is, how far, and how long.

def _place(key):
    import directory as d                                     # noqa: PLC0415
    for p in d.PLACES:
        if p["key"] == key:
            return p
    raise KeyError(key)


def _rim_radius(schema, profile, sector):
    return it.sector_radius(schema, profile, sector)


def walk_leg(schema, profile, a, b, label=None):
    """Walking between two register places, on the rim.

    MANHATTAN, not great-circle, and the reason matters: corridors in a decked
    cylinder run either along the axis or around a ring, so the distance a
    person actually covers is the axial run PLUS the arc, never the hypotenuse.
    Using the hypotenuse would understate every cross-station walk.

    Gravity is taken at the mean of the two rim radii, so a walk that changes
    sector is walked at a speed between the two -- Blue's 0.760 g and Grey's
    1.693 g are different enough that picking either end would be wrong.
    """
    ra = _rim_radius(schema, profile, a["sector"])
    rb = _rim_radius(schema, profile, b["sector"])
    dz = abs(b["z_m"] - a["z_m"])
    dth = abs(b["angle_deg"] - a["angle_deg"]) % 360.0
    dth = min(dth, 360.0 - dth)
    arc = math.radians(dth) * (ra + rb) / 2.0
    g = gravity_g(schema, (ra + rb) / 2.0)
    d = dz + arc
    return {"kind": "walk", "label": label or f"{a['key']} -> {b['key']}",
            "distance_m": d, "seconds": d / walk_speed(g),
            "detail": f"{dz:,.0f} m axial + {arc:,.0f} m arc at {g:.3f} g"}


def climb_leg(schema, dr_m, label):
    """A radial move. Coriolis-capped, smoothstep, peak 1.5x mean.

    Used for lifts between decks, for reaching a guideway stop from the floor,
    and for the rim-to-axis climb. It is the same physics every time and it is
    the expensive part of nearly every journey in this station.

    Takes `schema` and USES it. An earlier version took the argument and read a
    module global instead, which works right up until somebody calls this
    without having called `journeys()` first -- a parameter that is accepted
    and ignored is worse than no parameter, because it reads as safe.
    """
    v = coriolis_speed_cap(schema)
    return {"kind": "climb", "label": label, "distance_m": abs(dr_m),
            "seconds": 1.5 * abs(dr_m) / v,
            "detail": f"{abs(dr_m):,.0f} m radial, capped at {v:.2f} m/s by "
                      f"{COMFORT_LATERAL_G:.2f} g Coriolis"}


def ride_leg(schema, line, rep, n_stops, label):
    """`n_stops` legs on a line, plus the dwells between them."""
    if line["kind"] == "radial":
        t = rep["end_to_end_s"]
        d = rep["run_m"]
    else:
        t = n_stops * rep["leg_s"] + max(0, n_stops - 1) * DWELL_S
        d = n_stops * rep["spacing_m"]
    return {"kind": "ride", "label": label, "distance_m": d, "seconds": t,
            "detail": f"{n_stops} stop(s) at {rep['spacing_m']:,.0f} m, peak "
                      f"{rep['peak_speed_m_s']:.1f} m/s "
                      f"({rep['peak_speed_kmh']:.0f} km/h)"}


def wait_leg(rep, label):
    return {"kind": "wait", "label": label, "distance_m": 0.0,
            "seconds": rep["mean_wait_s"],
            "detail": f"half of a {rep['headway_s'] / 60.0:.1f} min headway "
                      f"({rep['cars_per_line']} car(s) on the line)"}


def journey(name, legs, note=""):
    return {"name": name, "legs": legs, "note": note,
            "seconds": sum(l["seconds"] for l in legs),
            "distance_m": sum(l["distance_m"] for l in legs)}


# Deck pitch, for a journey that changes deck. Read off the kit rather than
# typed: a deck is its clear height plus the slab over it, and both are
# `interior_kit.PROVISIONAL`'s.
def deck_pitch_m():
    import interior_kit as ik                                 # noqa: PLC0415
    return ik.PROVISIONAL["ceiling_height_m"] + ik.PROVISIONAL["ceiling_slab_m"]


def _sector_walk(schema, profile, z_from, z_to):
    """Walk along the axis through however many sectors it crosses.

    Split by sector because walking speed follows the local gravity and the
    rim radius changes at every sector face -- 0.559 g in Yellow, 1.693 g in
    Grey. A single average speed over 8 km would be wrong by minutes.

    Sectors come from the schema in z order rather than from a list written
    here, so a sector added or renamed by C-003 is picked up instead of
    silently dropped out of every station-length walk.
    """
    ex = schema["sectors"]["extents_m"]
    lo, hi = min(z_from, z_to), max(z_from, z_to)
    out, total = [], 0.0
    for sec in sorted(ex, key=lambda k: ex[k]["z0"]):
        a, b = float(ex[sec]["z0"]), float(ex[sec]["z1"])
        s, e = max(lo, a), min(hi, b)
        if e <= s:
            continue
        r = _rim_radius(schema, profile, sec)
        g = gravity_g(schema, r)
        v = walk_speed(g)
        total += (e - s) / v
        out.append((sec, e - s, g, v))
    return total, out


def journeys(schema, profile):
    """The five journeys the owner asked about, each with a transit option and
    a walk-only alternative. Transit does not always win, and where it loses
    that is the finding, not a bug."""
    reps = {r["key"]: r for r in
            (line_report(schema, l) for l in all_lines(schema, profile))}
    lines = {l["key"]: l for l in all_lines(schema, profile)}
    ex = schema["sectors"]["extents_m"]
    out = []

    # --- 1. end to end, on foot -------------------------------------------
    t, parts = _sector_walk(schema, profile, 0.0, 8047.0)
    out.append(journey(
        "End to end (z 0 -> 8,047), on foot",
        [{"kind": "walk", "label": f"{sec} {d:,.0f} m at {g:.3f} g",
          "distance_m": d, "seconds": d / v,
          "detail": f"walk {v:.2f} m/s"} for sec, d, g, v in parts],
        "Walked on the rim, sector by sector. Grey's 1.693 g is walked 1.74x "
        "faster than Yellow's 0.559 g, so a single average speed is wrong."))

    # --- 2. end to end, by core shuttle ------------------------------------
    cs, csr = lines["core_shuttle"], reps["core_shuttle"]
    r_blue = _rim_radius(schema, profile, "blue")
    r_yell = _rim_radius(schema, profile, "yellow")
    t_yellow, _p = _sector_walk(schema, profile, 0.0, cs["z0"])
    out.append(journey(
        "End to end (z 0 -> 8,047), by core shuttle",
        [{"kind": "walk", "label": "Yellow has no transit system at all",
          "distance_m": cs["z0"], "seconds": t_yellow,
          "detail": f"walk the aft {cs['z0']:,.0f} m to Grey"},
         climb_leg(schema, r_yell, "climb to the axis at Grey"),
         wait_leg(csr, "wait for a core shuttle"),
         ride_leg(schema, cs, csr, CORE_SHUTTLE_STOPS - 1,
                  "ride Grey -> Blue, all 12 legs"),
         climb_leg(schema, r_blue, "climb down to Blue's rim")],
        "THE FINDING: the shuttle does not go to the aft end. It runs Grey to "
        "Blue, so the 3,397 m of Yellow -- 42% of the station -- has no "
        "declared transit at all and has to be walked."))

    # --- 3. Blue docking bays -> the Zocalo --------------------------------
    bays, zoc = _place("docking_bays"), _place("zocalo")
    out.append(journey(
        "Blue docking bays -> the Zocalo, on foot",
        [walk_leg(schema, profile, bays, zoc, "walk Blue -> Red on the rim"),
         climb_leg(schema, _rim_radius(schema, profile, "red")
                   - _rim_radius(schema, profile, "blue"),
                   "Red's rim is 56 m further out than Blue's")],
        "Both are on the rim and 515 m apart in z."))

    # A shuttle stop is where the stop rule puts it, not under wherever you
    # happen to be standing. Both ends therefore start and finish with a walk
    # along the rim to the nearest stop's z -- and leaving those two legs out
    # is exactly how a transit model flatters itself.
    def _nearest(line, z):
        s = min(line["stops_z"], key=lambda q: abs(q - z))
        return s, abs(s - z)

    s_a, d_a = _nearest(cs, bays["z_m"])
    s_b, d_b = _nearest(cs, zoc["z_m"])
    n_hop = int(round(abs(s_b - s_a) / csr["spacing_m"]))
    g_blue = gravity_g(schema, r_blue)
    g_red = gravity_g(schema, _rim_radius(schema, profile, "red"))
    out.append(journey(
        "Blue docking bays -> the Zocalo, by core shuttle",
        [{"kind": "walk", "label": "walk to under the nearest shuttle stop",
          "distance_m": d_a, "seconds": d_a / walk_speed(g_blue),
          "detail": f"stop at z={s_a:,.0f}, {d_a:,.0f} m away"},
         climb_leg(schema, r_blue, "climb to the axis"),
         wait_leg(csr, "wait for a core shuttle"),
         ride_leg(schema, cs, csr, n_hop, f"ride {n_hop} stop(s)"),
         climb_leg(schema, _rim_radius(schema, profile, "red"),
                   "climb down to Red's rim"),
         {"kind": "walk", "label": "walk from under the stop to the Zocalo",
          "distance_m": d_b, "seconds": d_b / walk_speed(g_red),
          "detail": f"stop at z={s_b:,.0f}, {d_b:,.0f} m away"}],
        "THE FINDING: taking the shuttle is SLOWER than walking. Two radial "
        "climbs at the Coriolis cap cost 230 s between them, and the ride "
        "only saves 515 m of level walking."))

    # --- 4. C&C -> Medlab ---------------------------------------------------
    cnc, med = _place("cnc"), _place("medlab_one")
    ddeck = abs(med["deck"] - cnc["deck"]) * deck_pitch_m()
    out.append(journey(
        "C&C -> Medlab 1, on foot",
        [walk_leg(schema, profile, cnc, med, "walk within Blue"),
         climb_leg(schema, ddeck,
                   f"{abs(med['deck'] - cnc['deck'])} deck(s) down")],
        "Both in Blue, one deck and 100 degrees apart. Nothing else competes "
        "at this range -- the nearest shuttle stop is 2 climbs away."))

    # --- 5. The Garden -> Downbelow ----------------------------------------
    gar, dwn = _place("the_garden"), _place("downbelow")
    out.append(journey(
        "The Garden -> Downbelow, on foot",
        [walk_leg(schema, profile, gar, dwn, "walk the drum floor and Grey"),
         climb_leg(schema, _rim_radius(schema, profile, "grey")
                   - _rim_radius(schema, profile, "green"),
                   "Grey's rim is 193 m further out than the drum floor")],
        "Across the drum's length and out into Grey."))

    gl, glr = lines["guideway_tram"], reps["guideway_tram"]
    r_green = _rim_radius(schema, profile, "green")
    # Walk to the nearest guideway stop, ride to the aft cap, then Grey.
    stops = gl["stops_z"]
    near = min(stops, key=lambda z: abs(z - gar["z_m"]))
    n_legs = int(round(abs(near - gl["z0"]) / glr["spacing_m"]))
    dth = min(abs(gar["angle_deg"] - 0.0) % 360.0,
              360.0 - abs(gar["angle_deg"] - 0.0) % 360.0)
    out.append(journey(
        "The Garden -> Downbelow, by guideway tram",
        [{"kind": "walk", "label": "walk to the nearest guideway stop",
          "distance_m": abs(near - gar["z_m"]) + math.radians(dth) * r_green,
          "seconds": (abs(near - gar["z_m"]) + math.radians(dth) * r_green)
          / walk_speed(gravity_g(schema, r_green)),
          "detail": f"stop at z={near:,.0f}, {dth:.0f} deg round the drum"},
         climb_leg(schema, gl["access_climb_m"],
                   "climb to the guideway, 41.7 m above the fields"),
         wait_leg(glr, "wait for a guideway tram"),
         ride_leg(schema, gl, glr, n_legs, "ride to the aft end cap"),
         climb_leg(schema, gl["access_climb_m"], "climb back down"),
         {"kind": "walk", "label": "through the aft cap and out into Grey",
          "distance_m": abs(gl["z0"] - dwn["z_m"])
          + math.radians(180.0) * r_green,
          "seconds": (abs(gl["z0"] - dwn["z_m"])
                      + math.radians(180.0) * r_green)
          / walk_speed(gravity_g(schema, r_green)),
          "detail": "Downbelow is 180 deg round from the guideway"},
         climb_leg(schema, _rim_radius(schema, profile, "grey") - r_green,
                   "out to Grey's rim")],
        "THE FINDING: the guideway tram's 41.7 m access climb costs 40 s each "
        "way, which is most of what the ride saves at this distance."))

    return out, reps


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _hms(s):
    m, sec = divmod(int(round(s)), 60)
    h, m = divmod(m, 60)
    return f"{h:d}h {m:02d}m {sec:02d}s" if h else f"{m:d}m {sec:02d}s"


def print_table(schema=None, profile=None):
    if schema is None:
        schema, profile = it.load()
    js, reps = journeys(schema, profile)
    cor = coriolis_report(schema)

    print("\nTHE LINES -- every number below is derived, none is chosen")
    print("-" * 78)
    print(f"{'line':26s} {'stops':>5s} {'spacing':>9s} {'peak':>10s} "
          f"{'end-end':>9s} {'headway':>8s}")
    for k in ("core_shuttle", "guideway_tram", "ground_tram", "spoke_lift"):
        r = reps[k]
        print(f"{r['name']:26s} {r['stops']:5d} {r['spacing_m']:8,.0f}m "
              f"{r['peak_speed_m_s']:7.2f} m/s {_hms(r['end_to_end_s']):>9s} "
              f"{_hms(r['headway_s']):>8s}")
    print(f"\n  the two axial lines are ACCEL-LIMITED (Coriolis imposes no cap "
          f"on them);\n  the two that run across the spin are capped at "
          f"{cor['cap_m_s']:.2f} m/s by {COMFORT_LATERAL_G:.2f} g of Coriolis.")

    print("\nCORIOLIS -- three directions, three different consequences")
    print("-" * 78)
    a, t, rr = cor["axial"], cor["tangential"], cor["radial"]
    print(f"  ALONG THE AXIS (core shuttle, guideway tram)")
    print(f"    Coriolis                          {a['coriolis_g']:.4f} g  "
          f"-- {a['note']}")
    print(f"    static weight at r={a['radius_m']:.1f} m        "
          f"{a['static_weight_g']:.4f} g")
    print(f"  AROUND THE DRUM (ground tram) at {t['speed_m_s']:.2f} m/s, "
          f"r={t['radius_m']:.1f} m")
    print(f"    Coriolis (radial: WEIGHT)         "
          f"{t['coriolis_g']:+.4f} g")
    print(f"    riding spinward                   "
          f"{t['spinward_weight_g']:.4f} g")
    print(f"    riding anti-spinward              "
          f"{t['antispinward_weight_g']:.4f} g")
    print(f"    swing between the two             "
          f"{t['weight_swing_g']:.4f} g  "
          f"({(t['weight_ratio'] - 1) * 100:.1f}% heavier one way)")
    print(f"      -- noticeable, not unpleasant: a lift on Earth does "
          f"{COMFORT_LATERAL_G:.2f} g routinely. But it is comfortable ONLY "
          f"because\n         the line is capped at {t['speed_m_s']:.2f} m/s "
          f"to make it so; at 12 m/s it would be "
          f"{2 * cor['omega_rad_s'] * 12.0 / G0:.2f} g of Coriolis.")
    print(f"  ACROSS THE DRUM (spoke lifts) at {rr['speed_m_s']:.2f} m/s")
    print(f"    Coriolis (tangential: a PUSH)     {rr['coriolis_g']:.4f} g")
    print(f"    tangential speed to shed          "
          f"{rr['tangential_speed_to_shed_m_s']:.2f} m/s")

    print("\nJOURNEYS -- walk, wait and ride, because a time without a wait is "
          "a lie")
    print("-" * 78)
    for j in js:
        print(f"\n  {j['name']}")
        for l in j["legs"]:
            print(f"    {l['kind']:6s} {_hms(l['seconds']):>9s}  "
                  f"{l['label']}")
            print(f"           {' ':9s}  ({l['detail']})")
        print(f"    {'TOTAL':6s} {_hms(j['seconds']):>9s}  "
              f"over {j['distance_m']:,.0f} m")
        if j["note"]:
            print(f"      {j['note']}")
    print()


# ---------------------------------------------------------------------------
# Self-test. Every assertion has a negative control that is actually run.
# ---------------------------------------------------------------------------

def _selftest():
    ok = fail = 0
    neg_ok = neg_fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    def negative(name, fn):
        """Run a case that MUST fail, and fail if it does not.

        An assertion that cannot fail is worse than none, and the only way to
        know one can is to feed it something wrong and watch it fire.
        """
        nonlocal neg_ok, neg_fail
        try:
            fn()
        except AssertionError:
            neg_ok += 1
            return
        neg_fail += 1
        print(f"NEGATIVE CONTROL DID NOT FIRE  {name}")

    schema, profile = it.load()
    w = omega(schema)

    # --- the constants are not a second opinion ----------------------------
    # Every bound here is owned by another module. Read the owner's value out
    # of its signature and compare, so a change there breaks this rather than
    # leaving two numbers quietly disagreeing.
    import inspect                                            # noqa: PLC0415
    import core_shuttle as cs_mod                              # noqa: PLC0415
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "npc"))
    import navigation as nv                                    # noqa: PLC0415
    import tram as tram_mod                                    # noqa: PLC0415

    owner_lat = inspect.signature(
        cs_mod.comfortable_duration).parameters["max_lateral_g"].default
    owner_ax = inspect.signature(
        cs_mod.AxialShuttle.__init__).parameters["cruise_accel"].default
    owner_cars = inspect.signature(
        tram_mod.drum_trams).parameters["per_guideway"].default
    check("comfort bound agrees with physics/core_shuttle",
          COMFORT_LATERAL_G == owner_lat, f"{COMFORT_LATERAL_G} vs {owner_lat}")
    check("comfort bound agrees with npc/navigation",
          COMFORT_LATERAL_G == nv.MAX_LATERAL_G)
    check("cruise accel agrees with physics/core_shuttle.AxialShuttle",
          CRUISE_ACCEL_M_S2 == owner_ax, f"{CRUISE_ACCEL_M_S2} vs {owner_ax}")
    check("cruise accel agrees with npc/navigation",
          CRUISE_ACCEL_M_S2 == nv.AXIAL_ACCEL_M_S2)
    check("dwell agrees with npc/navigation", DWELL_S == nv.TRANSIT_DWELL_S)
    check("cars per guideway agrees with tram.drum_trams",
          CARS_PER_GUIDEWAY == owner_cars,
          f"{CARS_PER_GUIDEWAY} vs {owner_cars}")
    check("core shuttle stop count agrees with npc/navigation",
          CORE_SHUTTLE_STOPS == nv.CORE_SHUTTLE_STOPS)
    check("the Coriolis cap agrees with npc/navigation to 1e-9",
          abs(coriolis_speed_cap(schema) - nv.coriolis_speed_cap(schema))
          < 1e-9,
          f"{coriolis_speed_cap(schema)} vs {nv.coriolis_speed_cap(schema)}")
    # The negative control on the cross-check. Perturb the constant by the
    # smallest amount anyone would plausibly change it by and confirm the same
    # comparison the real check uses now rejects it. Written from
    # COMFORT_LATERAL_G rather than from a literal, so it cannot go stale if
    # the bound legitimately moves.
    def _perturbed_bound():
        bad = COMFORT_LATERAL_G + 0.01
        assert bad == owner_lat, \
            f"{bad} g must not pass a cross-check against {owner_lat} g"
    negative("a perturbed comfort bound is rejected", _perturbed_bound)

    # --- the motion profile ------------------------------------------------
    # Closed form against a numeric integration of the seven-phase profile.
    # They share no algebra, so agreement is evidence rather than tautology.
    for d in (50.0, 387.5, 646.5, 1293.0, 4650.0):
        p = ride_profile(d)
        n = _integrate_profile(d, CRUISE_ACCEL_M_S2, JERK_M_S3)
        check(f"profile closed form matches integration at {d:g} m",
              abs(n["distance_m"] - d) / d < 2e-3
              and abs(n["peak_speed_m_s"] - p["peak_speed_m_s"])
              / p["peak_speed_m_s"] < 2e-3
              and abs(n["end_speed_m_s"]) < 1e-3 * p["peak_speed_m_s"],
              f"integrated {n['distance_m']:.2f} m vs {d} m, peak "
              f"{n['peak_speed_m_s']:.4f} vs {p['peak_speed_m_s']:.4f}, "
              f"ends at {n['end_speed_m_s']:.2e} m/s")
    # Below the knee the profile takes its other branch, so exercise it.
    knee_v = CRUISE_ACCEL_M_S2 ** 2 / JERK_M_S3
    small = 0.5 * knee_v * (2.0 * math.sqrt(knee_v / JERK_M_S3)) * 0.5
    p = ride_profile(small)
    check("the sub-knee branch is exercised and never reaches the accel limit",
          p["peak_speed_m_s"] < knee_v,
          f"{p['peak_speed_m_s']:.3f} m/s against a knee at {knee_v:.3f}")
    n = _integrate_profile(small, CRUISE_ACCEL_M_S2, JERK_M_S3)
    check("sub-knee closed form matches integration",
          abs(n["distance_m"] - small) / small < 3e-3,
          f"{n['distance_m']:.4f} vs {small:.4f}")

    def _wrong_profile():
        # A profile that ignored jerk would give 2*sqrt(D/a); assert the real
        # one is slower, so the jerk term is doing work rather than decorating.
        d = 646.5
        assert ride_profile(d)["time_s"] <= 2.0 * math.sqrt(d / CRUISE_ACCEL_M_S2), \
            "jerk must make the ride longer, not shorter"
    negative("a jerk-free profile is rejected as too fast", _wrong_profile)
    check("jerk lengthens the ride rather than decorating it",
          ride_profile(646.5)["time_s"]
          > 2.0 * math.sqrt(646.5 / CRUISE_ACCEL_M_S2),
          f"{ride_profile(646.5)['time_s']:.2f} s against a jerk-free "
          f"{2.0 * math.sqrt(646.5 / CRUISE_ACCEL_M_S2):.2f} s")
    check("the profile is monotone in distance",
          all(ride_profile(d)["time_s"] < ride_profile(d * 1.5)["time_s"]
              for d in (10.0, 100.0, 1000.0)))

    # --- Coriolis ----------------------------------------------------------
    r_floor = it.sector_radius(schema, profile, "green")
    cap = coriolis_speed_cap(schema)
    cor = coriolis_report(schema)

    # The apparent-weight expansion, checked against the inertial frame it came
    # from rather than against itself.
    for u in (-cap, -1.0, 0.0, 1.0, cap, 10.0):
        inertial = ((w * r_floor + u) ** 2 / r_floor) / G0
        check(f"apparent weight matches the inertial frame at u={u:+.2f}",
              abs(apparent_weight_g(schema, r_floor, u) - inertial) < 1e-12,
              f"{apparent_weight_g(schema, r_floor, u):.9f} vs "
              f"{inertial:.9f}")

    check("axial motion produces exactly zero Coriolis",
          cor["axial"]["coriolis_g"] == 0.0)
    check("the guideway tram rides at 0.85 g, not 1.0",
          abs(cor["axial"]["static_weight_g"] - it.TRUSS_RADIUS_FRAC) < 1e-6,
          f"{cor['axial']['static_weight_g']:.6f} g")
    t = cor["tangential"]
    check("the ring tram is heavier spinward than anti-spinward",
          t["spinward_weight_g"] > t["antispinward_weight_g"])
    # THE COMFORT ASSERTION, and it is stated as a tolerance so it can fail.
    # The bound is the project's own 0.12 g on the Coriolis term. The FULL
    # swing is larger than 2x that, because the u^2/r term does not cancel --
    # it adds the same amount to both directions. Assert the Coriolis part is
    # at the bound and the swing is what the arithmetic makes it.
    check("the ring tram's Coriolis sits exactly at the comfort bound",
          abs(t["coriolis_g"] - COMFORT_LATERAL_G) < 1e-9,
          f"{t['coriolis_g']:.9f} g")
    check("the spinward/anti-spinward weight swing is 2x the bound",
          abs(t["weight_swing_g"] - 2.0 * COMFORT_LATERAL_G) < 1e-9,
          f"{t['weight_swing_g']:.9f} g")
    check("the relative-motion term is small but not zero",
          0.0 < t["relative_centrifugal_g"] < 0.01,
          f"{t['relative_centrifugal_g']:.6f} g")
    check("a passenger weighs 20-30% more riding one way than the other",
          1.20 < t["weight_ratio"] < 1.30,
          f"{t['weight_ratio']:.4f}")

    def _uncomfortable_ring_tram():
        """The comfort gate must fire on a tram run at a speed nobody could
        stand. 12 m/s round the drum is 0.46 g of Coriolis."""
        c = coriolis_report(schema, u_ring=12.0)
        assert c["tangential"]["coriolis_g"] <= COMFORT_LATERAL_G, \
            "12 m/s round the drum must breach the comfort bound"
    negative("the ring tram comfort gate fires at 12 m/s",
             _uncomfortable_ring_tram)

    def _uncomfortable_lift():
        c = coriolis_report(schema, v_radial=8.0)
        assert c["radial"]["coriolis_g"] <= COMFORT_LATERAL_G, \
            "an 8 m/s lift must breach the comfort bound"
    negative("the lift comfort gate fires at 8 m/s", _uncomfortable_lift)

    check("the tangential speed to shed matches the drum floor speed",
          abs(cor["radial"]["tangential_speed_to_shed_m_s"] - 52.24) < 0.02,
          f"{cor['radial']['tangential_speed_to_shed_m_s']:.3f} m/s")

    # --- the stop rule -----------------------------------------------------
    # The rule that produces five guideway stops has to REJECT four and three,
    # or it is not a rule. Both cases are run.
    ex = schema["sectors"]["extents_m"][it.drum_sector(schema, profile)]
    drum_len = float(ex["z1"] - ex["z0"])
    g_floor = gravity_g(schema, r_floor)
    reach = walk_speed(g_floor) * CATCHMENT_WALK_S
    n = stop_rule(schema, drum_len, g_floor, must_include_mid=True)
    check("the guideway stop rule returns five", n == 5, str(n))
    check("five stops are inside the catchment",
          (drum_len / 4) / 2.0 <= reach,
          f"{(drum_len / 4) / 2.0:.0f} m walk against a {reach:.0f} m reach")
    check("THREE stops are outside the catchment, which is why it is not three",
          (drum_len / 2) / 2.0 > reach,
          f"{(drum_len / 2) / 2.0:.0f} m walk against a {reach:.0f} m reach")
    check("FOUR stops would miss the spoke crossing, which is why it is odd",
          not any(abs(z - (float(ex["z0"]) + drum_len / 2.0)) < 1.0
                  for z in _even_stops(float(ex["z0"]), float(ex["z1"]), 4)),
          str(_even_stops(float(ex["z0"]), float(ex["z1"]), 4)))
    check("five stops DO land on the spoke crossing",
          any(abs(z - (float(ex["z0"]) + drum_len / 2.0)) < 1e-9
              for z in _even_stops(float(ex["z0"]), float(ex["z1"]), 5)))

    def _catchment_gate():
        """Feed the rule a catchment so tight that five stops cannot satisfy
        it, and assert it does not return five anyway."""
        assert stop_rule(schema, drum_len, g_floor, must_include_mid=True,
                         catchment_s=60.0) == 5, \
            "a 1-minute catchment must need more than five stops"
    negative("the catchment gate fires on a 1-minute catchment", _catchment_gate)

    # --- the lines ---------------------------------------------------------
    lines = all_lines(schema, profile)
    reps = {r["key"]: r for r in (line_report(schema, l) for l in lines)}

    gl = guideway_line(schema, profile)
    check("the guideway line sits on the truss interior.py builds",
          abs(gl["radius_m"]
              - it.sector_radius(schema, profile, "green")
              * it.TRUSS_RADIUS_FRAC) < 1e-9,
          f"{gl['radius_m']:.3f} m")
    check("the guideway line runs the truss's full span",
          gl["z0"] == float(ex["z0"]) and gl["z1"] == float(ex["z1"]))
    check("there is one guideway line per truss",
          gl["lines"] == it.TRUSS_COUNT)
    check("the guideway's access climb is floor to bottom chord",
          abs(gl["access_climb_m"] - (r_floor - gl["radius_m"])) < 1e-9,
          f"{gl['access_climb_m']:.2f} m")

    # A 96 m car must fit between two stops with room to stand at each.
    car = tram_mod.car_length()
    check("a car fits between two guideway stops",
          reps["guideway_tram"]["spacing_m"] > 3.0 * car,
          f"{reps['guideway_tram']['spacing_m']:.0f} m spacing for a "
          f"{car:.0f} m car")

    # Bounds on the journeys, stated so they can fail.
    for k, lo, hi in (("core_shuttle", 15.0, 40.0),
                      ("guideway_tram", 15.0, 40.0),
                      ("ground_tram", 0.0, 4.0),
                      ("spoke_lift", 0.0, 4.0)):
        v = reps[k]["peak_speed_m_s"]
        check(f"{k} peak speed is within [{lo}, {hi}] m/s", lo < v <= hi,
              f"{v:.3f} m/s")
    check("the axial lines are accel-limited, not Coriolis-limited",
          reps["core_shuttle"]["accel_limited"]
          and reps["guideway_tram"]["accel_limited"])
    check("the cross-spin lines ARE Coriolis-limited",
          not reps["ground_tram"]["accel_limited"]
          and abs(reps["ground_tram"]["peak_speed_m_s"] - cap) < 1e-9,
          f"{reps['ground_tram']['peak_speed_m_s']:.4f} vs cap {cap:.4f}")
    check("the axial lines are at least 5x the cross-spin ones",
          reps["core_shuttle"]["peak_speed_m_s"] > 5.0
          * reps["ground_tram"]["peak_speed_m_s"],
          f"{reps['core_shuttle']['peak_speed_m_s']:.2f} vs "
          f"{reps['ground_tram']['peak_speed_m_s']:.2f} m/s")

    # The spoke lift must reproduce the project's own 133 s figure, from a
    # different route: this file's smoothstep closed form against
    # `core_shuttle.comfortable_duration`'s bisection.
    bis = cs_mod.comfortable_duration(
        cs_mod.RadialTransit(
            type("D", (), {"omega": w})(), r_floor, 0.0, 1.0).drum,
        r_floor, 0.0)
    closed = 1.5 * r_floor / cap
    check("the rim-to-axis ride agrees with core_shuttle's bisection",
          abs(closed - bis) / bis < 2e-3,
          f"closed form {closed:.3f} s vs bisection {bis:.3f} s")
    check("the rim-to-axis ride is the 133 s LOCATIONS.md quotes",
          132.0 < closed < 134.0, f"{closed:.2f} s")

    # Headways. Every one is round trip over cars; assert the relation holds
    # rather than the number, and bound the number separately.
    for k, r in reps.items():
        check(f"{k}: headway is the round trip over its cars",
              abs(r["headway_s"] - r["round_trip_s"] / r["cars_per_line"])
              < 1e-9)
        check(f"{k}: mean wait is under 10 minutes", r["mean_wait_s"] < 600.0,
              f"{r['mean_wait_s'] / 60.0:.1f} min")
    check("the spoke lifts have the worst wait on the station, and it is bad",
          reps["spoke_lift"]["mean_wait_s"]
          == max(r["mean_wait_s"] for r in reps.values())
          and reps["spoke_lift"]["mean_wait_s"] > 120.0,
          f"{reps['spoke_lift']['mean_wait_s']:.0f} s")

    def _headway_gate():
        """One car on a line whose round trip is 20 minutes must not produce a
        wait anybody would call acceptable."""
        fake = dict(gl)
        fake["cars_per_line"] = 1
        r = line_report(schema, fake)
        assert r["mean_wait_s"] < 120.0, \
            "a one-car guideway must blow the 2-minute wait"
    negative("the headway gate fires on a one-car line", _headway_gate)

    # --- stop spacing covers the register ----------------------------------
    # The task the register sets: a stop has to be near the places that exist,
    # not at a tidy interval. Measured against `directory.PLACES`.
    import directory as d                                      # noqa: PLC0415
    cs_line = core_shuttle_line(schema, profile)
    half_cs = reps["core_shuttle"]["spacing_m"] / 2.0
    half_gl = reps["guideway_tram"]["spacing_m"] / 2.0
    worst_cs = worst_gl = 0.0
    n_cs = n_gl = 0
    for p in d.PLACES:
        z = p["z_m"]
        if cs_line["z0"] <= z <= cs_line["z1"]:
            n_cs += 1
            worst_cs = max(worst_cs, min(abs(z - s)
                                         for s in cs_line["stops_z"]))
        if gl["z0"] <= z <= gl["z1"] and p["sector"] == "green":
            n_gl += 1
            worst_gl = max(worst_gl, min(abs(z - s) for s in gl["stops_z"]))
    check("every register place in the shuttle's run is within half a spacing "
          "of a stop", worst_cs <= half_cs + 1e-6,
          f"worst {worst_cs:.0f} m over {n_cs} places, half-spacing "
          f"{half_cs:.0f} m")
    check("the shuttle's run actually contains places to serve", n_cs >= 40,
          f"{n_cs} places")
    check("every drum place is within half a guideway spacing of a stop",
          worst_gl <= half_gl + 1e-6,
          f"worst {worst_gl:.0f} m over {n_gl} places, half-spacing "
          f"{half_gl:.0f} m")
    check("the drum actually contains places to serve", n_gl >= 8,
          f"{n_gl} places")

    def _coverage_gate():
        """The coverage check must fire when a stop is deleted. Rebuild the
        shuttle with its stops halved and confirm the worst gap breaks."""
        thin = [cs_line["stops_z"][i]
                for i in range(0, len(cs_line["stops_z"]), 4)]
        worst = max(min(abs(p["z_m"] - s) for s in thin) for p in d.PLACES
                    if cs_line["z0"] <= p["z_m"] <= cs_line["z1"])
        assert worst <= half_cs, "a thinned stop list must break coverage"
    negative("the coverage gate fires on a thinned stop list", _coverage_gate)

    # --- the leg builders stand alone --------------------------------------
    # REGRESSION GUARD. `climb_leg` took a `schema` argument and read a module
    # global instead, so it worked only after `journeys()` had run and set it.
    # Called first, in a fresh process, it raised NameError -- and nothing
    # would have caught that, because the self-test happened to call
    # `journeys()` before anything else. Exercised here BEFORE `journeys()`.
    solo = climb_leg(schema, 100.0, "a hundred metres of climb")
    check("climb_leg works without journeys() having primed anything",
          abs(solo["seconds"] - 1.5 * 100.0 / cap) < 1e-9,
          f"{solo['seconds']:.3f} s")
    check("a climb leg scales with its distance",
          abs(climb_leg(schema, 200.0, "x")["seconds"]
              - 2.0 * solo["seconds"]) < 1e-9)
    pitch = deck_pitch_m()
    check("deck pitch is read off the kit, not typed", 2.5 < pitch < 5.0,
          f"{pitch:.2f} m")

    # --- journeys ----------------------------------------------------------
    js, _reps = journeys(schema, profile)
    by_name = {j["name"]: j for j in js}
    for j in js:
        check(f"journey '{j['name'][:40]}' is bounded",
              0.0 < j["seconds"] < 4.0 * 3600.0,
              f"{j['seconds']:.0f} s")
        check(f"journey '{j['name'][:40]}' legs sum to its total",
              abs(sum(l["seconds"] for l in j["legs"]) - j["seconds"]) < 1e-9)

    walkall = by_name["End to end (z 0 -> 8,047), on foot"]
    check("walking end to end is between 90 and 120 minutes",
          90 * 60 < walkall["seconds"] < 120 * 60,
          f"{walkall['seconds'] / 60.0:.1f} min")
    shuttle = by_name["End to end (z 0 -> 8,047), by core shuttle"]
    check("the core shuttle beats walking end to end",
          shuttle["seconds"] < walkall["seconds"],
          f"{shuttle['seconds'] / 60:.1f} vs {walkall['seconds'] / 60:.1f} min")
    check("but only by less than 3x, because Yellow has to be walked",
          shuttle["seconds"] > walkall["seconds"] / 3.0,
          f"{walkall['seconds'] / shuttle['seconds']:.2f}x")

    bays_walk = by_name["Blue docking bays -> the Zocalo, on foot"]
    bays_ride = by_name["Blue docking bays -> the Zocalo, by core shuttle"]
    check("over 515 m, walking beats the shuttle -- the climbs cost more than "
          "the ride saves", bays_walk["seconds"] < bays_ride["seconds"],
          f"walk {bays_walk['seconds'] / 60:.1f} min vs ride "
          f"{bays_ride['seconds'] / 60:.1f} min")

    def _transit_always_wins():
        assert bays_ride["seconds"] <= bays_walk["seconds"], \
            "the model must be able to say 'walk'"
    negative("the model can say transit LOSES", _transit_always_wins)

    # The one number the owner already had: 8,047 m at 1.4 m/s = 95.8 min.
    # This project's own gravity-varying walk speed should be near it but not
    # equal to it, and the difference is the station's shape.
    naive = 8047.0 / 1.4
    check("the gravity-varying walk differs from a flat 1.4 m/s by 5-20%",
          0.05 < abs(walkall["seconds"] - naive) / naive < 0.20,
          f"{walkall['seconds'] / 60:.1f} min vs a naive "
          f"{naive / 60:.1f} min")

    print(f"{ok}/{ok + fail} passed, "
          f"{neg_ok}/{neg_ok + neg_fail} negative controls fired")
    return 1 if (fail or neg_fail) else 0


if __name__ == "__main__":
    if "--table" in sys.argv:
        print_table()
        sys.exit(0)
    sys.exit(_selftest())
