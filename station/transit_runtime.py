#!/usr/bin/env python3
"""THE PART OF TRANSPORT THAT MOVES -- and the gate that says a body rode it.

WHY THIS FILE EXISTS. Measured, not summarised, at the start of session 4g:

    station/transit.py       computes how long every journey takes, by every
                             mode.  TIMES ONLY.
    station/npc/navigation.py  lift_ride_s, axial_ride_s, ground_tram_ride_s,
                             the Coriolis speed cap.  TIMES ONLY.
    station/core_tube.py     builds the core shuttle tube.  Its own docstring:
                             "with no motion in them at all".
    station/tram.py          `guideway_cars` advertises a `phase` that walks the
                             whole train along the run.  NOTHING CALLS IT WITH A
                             CHANGING PHASE.
    station/lift.py          a shaft, a car, a floor under it, 37 gates.
                             `lift_car(at_deck=)` PARKS the car.  It does not
                             move.

Five modules model transport. Every mode is fully costed and none of them moves.
That is this project's most-repeated shape: a number computed about a thing that
does not exist -- here, a ride time for a vehicle nobody can be inside of.

WHAT IS HERE. The offline half of a moving lift and a moving tram: the meshes
split so that the piece that moves is its own node, the collision the body
stands on, and a MOTION TABLE. And the gate -- `--ride` launches Godot headless,
walks a body into the car, rides it, walks it out, and asserts on what came
back.

NOT ONE TIMING NUMBER IS CHOSEN HERE, and that is a requirement rather than a
boast. Every duration is read from the module that owns it and cross-checked
against a second module that computed it a different way:

  lift ride       `npc/navigation.lift_ride_s(schema, rise)` -- and the rise is
                  the DIFFERENCE of two landings' own `walk_r_m`, read off the
                  geometry `lift.shaft_geometry` emitted, never DECK_PITCH_M
                  restated.  Cross-checked against `transit.climb_leg`, which
                  shares no code with it.
  lift profile    smoothstep, because that is the profile BOTH of those
                  functions document ("a smoothstep profile peaks at 1.5x its
                  mean speed, so holding the peak at the Coriolis cap gives
                  T = 1.5 * dr / v_cap").  `_ride_table` emits it sampled and
                  then ASSERTS its own peak against
                  `navigation.coriolis_speed_cap`.  A table that disagreed with
                  the cap would fail here rather than drift.
  lift dwell      `navigation.TRANSIT_DWELL_S`.
  door time       the leaf's MEASURED travel (below) divided by
                  `godot/scripts/door.gd`'s own `speed_m_s`, which the engine
                  side reads out of that script rather than copying.
  tram cycle      `transit.line_report(guideway_line)` -- `leg_s` per stop
                  spacing plus `transit.DWELL_S` -- and the within-leg profile
                  is `transit.ride_profile`'s seven-phase jerk-limited ramp,
                  integrated here and asserted against
                  `transit._integrate_profile`.

THE LEAF TRAVEL IS MEASURED, NOT PASSED IN. `walk.gd` takes `--door-travel` and
`station/walkable.py` hands it `PROVISIONAL["door_width_m"] / 2` -- a second
description of a decision `interior_kit.door_leaf` already makes. Here the car
is built TWICE, at `open_fraction=0` and at `1`, and the leaves' travel is the
per-triangle difference between the two meshes. So the runtime slides a leaf
exactly as far as the generator would have drawn it, and which leaf goes which
way is a fact about the mesh rather than an argument about left and right.
`weld` merges the two shut leaves into one another at 0.0 -- they share an
exactly coincident face, which is `lift.py`'s own documented four non-manifold
edges -- so the difference is taken per TRIANGLE and not per vertex; the vertex
lists are not comparable and the triangle lists are.

THE LOBBY IS NOT NEW GEOMETRY. A lift you can only be inside is not a lift you
can board, and `lift.py` builds a landing sill 0.44 m deep -- a ledge, not a
floor. So every landing gets one section of `interior.axial_run` /
`collision.axial_shell` at THAT LANDING'S OWN RADIUS: the station's own corridor
generator, at `floor_r_m`, so its walking surface is the same
`floor_r_m - floor_y` the car's floor lands on and a body crosses the threshold
without a step. Hard rule 4 -- one schema -- rather than a test rig.

Run: python3 station/transit_runtime.py --selftest      (no engine)
     python3 station/transit_runtime.py --ride          (the gate)
     python3 station/transit_runtime.py --tram          (the tram gate)
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import collision as C                                            # noqa: E402
import interior as it                                            # noqa: E402
import interior_kit as K                                         # noqa: E402
import lift as L                                                 # noqa: E402
import transit as T                                              # noqa: E402
import tram as TRAM                                              # noqa: E402
from npc import navigation as NAV                                # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/transit")

# WHERE THE LIFT IS. `station/lift.py`'s own self-test address, so every
# clearance and closure figure it prints is about this shaft, plus one more
# landing -- four decks rather than three, because the control this file needs
# is a body falling PAST a landing and a two-storey shaft cannot show one.
LIFT_ADDRESS = dict(sector="blue", ring=0, decks=(0, 1, 2, 3),
                    angle_deg=80.0, z_m=7500.0, landing_side=1)

# How much lobby each landing gets. `interior.AXIAL_SECTION_M` -- ONE SECTION of
# the station's own axial corridor, the unit `axial_run` subdivides into. Not a
# length chosen for the test: the body has to start far enough from the doorway
# that it is walking rather than already standing in it, and one section is the
# smallest piece of corridor this station knows how to build.
LOBBY_M = it.AXIAL_SECTION_M

def g0(schema):
    """Standard gravity, for turning a deck's own `floor_g` into the m/s^2 the
    character controller takes. READ FROM THE SCHEMA -- it is the same figure
    `interior.gravity_at` divides by, and writing 9.80665 here would be a second
    copy of a number the station is already defined against."""
    return schema["station"]["rotation"]["standard_gravity_m_s2"]["value"]

# How many samples a motion table carries. The runtime interpolates linearly
# between them, so the error is the curve's second difference over one interval:
# at 64 intervals a smoothstep is within 0.04% of itself, which on a 10.8 m rise
# is 4 mm -- under `collision.STEP_TOLERANCE_M`. Asserted in `_selftest`.
TABLE_N = 64


# ---------------------------------------------------------------------------
# Motion tables. The runtime plays these; it does not know the physics.
# ---------------------------------------------------------------------------

def _ride_table(schema, rise_m, n=TABLE_N):
    """The lift's motion, as (fraction of ride time, fraction of travel).

    SMOOTHSTEP, AND IT IS NOT A CHOICE MADE HERE. `navigation.lift_ride_s` and
    `transit.climb_leg` both derive their answer FROM this profile -- "a
    smoothstep profile peaks at 1.5x its mean speed, so holding the peak at the
    Coriolis cap gives T = 1.5 * dr / v_cap". Playing anything else in the
    engine would make the ride take the time those functions say while moving at
    a speed they forbid.

    So the table is emitted and then checked against the two things the physics
    is actually about: the total time is `lift_ride_s`, and the peak speed the
    table implies is `coriolis_speed_cap`. Both are asserted, so a table that
    drifted from the profile would fail here rather than quietly run hot.
    """
    seconds = NAV.lift_ride_s(schema, rise_m)
    tab = [(i / n, 3.0 * (i / n) ** 2 - 2.0 * (i / n) ** 3) for i in range(n + 1)]
    peak = 0.0
    if seconds > 0.0:
        peak = max((b - a) * rise_m / ((seconds) / n)
                   for (_, a), (_, b) in zip(tab, tab[1:]))
    return {"seconds": seconds, "rise_m": rise_m,
            "peak_m_s": peak, "table": [[round(u, 6), round(f, 8)]
                                        for u, f in tab]}


def _leg_table(distance_m, n=TABLE_N):
    """One stop-to-stop leg of an axial line, as (fraction of time, of distance).

    `transit.ride_profile` gives the leg's duration and peak speed in closed
    form and says nothing about WHERE the vehicle is at a given second, which is
    the one thing a runtime needs. This integrates the same seven-phase
    jerk-limited acceleration `transit._integrate_profile` builds -- jerk up,
    hold, jerk down, cruise, and the mirror image -- and is asserted against
    that function's own numbers in `_selftest`. The phase breakdown is taken
    from `transit.ride_profile` and `transit._ramp` rather than restated.
    """
    p = T.ride_profile(distance_m)
    v_pk = p["peak_speed_m_s"]
    t_ramp, _d = T._ramp(v_pk, T.CRUISE_ACCEL_M_S2, T.JERK_M_S3)
    t_j = min(T.CRUISE_ACCEL_M_S2 / T.JERK_M_S3, t_ramp / 2.0)
    t_hold = max(0.0, t_ramp - 2.0 * t_j)
    total = 2.0 * t_ramp + p["cruise_s"]
    a_pk = (T.CRUISE_ACCEL_M_S2
            if v_pk >= T.CRUISE_ACCEL_M_S2 ** 2 / T.JERK_M_S3
            else T.JERK_M_S3 * t_j)

    def a_at(t):
        if t < t_j:
            return T.JERK_M_S3 * t
        if t < t_j + t_hold:
            return a_pk
        if t < t_ramp:
            return a_pk - T.JERK_M_S3 * (t - t_j - t_hold)
        if t < t_ramp + p["cruise_s"]:
            return 0.0
        u = t - t_ramp - p["cruise_s"]
        if u < t_j:
            return -T.JERK_M_S3 * u
        if u < t_j + t_hold:
            return -a_pk
        return -a_pk + T.JERK_M_S3 * (u - t_j - t_hold)

    steps = 20000
    dt = total / steps
    v = d = 0.0
    marks = [0.0]
    want = 1
    for k in range(steps):
        v += a_at((k + 0.5) * dt) * dt
        d += v * dt
        while want <= n and (k + 1) * dt >= total * want / n - 1e-12:
            marks.append(d)
            want += 1
    while len(marks) < n + 1:
        marks.append(d)
    scale = 1.0 / marks[-1] if marks[-1] > 0 else 0.0
    return {"seconds": total, "distance_m": distance_m,
            "peak_m_s": v_pk, "integrated_m": marks[-1],
            "table": [[round(i / n, 6), round(marks[i] * scale, 8)]
                      for i in range(n + 1)]}


# ---------------------------------------------------------------------------
# The lift, split so the piece that moves is its own node
# ---------------------------------------------------------------------------

def shaft(schema, profile, **kw):
    a = dict(LIFT_ADDRESS)
    a.update(kw)
    return L.shaft_geometry(schema, profile, a["sector"], a["ring"],
                            a["decks"], a["angle_deg"], a["z_m"],
                            landing_side=a["landing_side"])


def lobby_span(g):
    """(z0, z1) of a landing lobby, in world z.

    It starts ON the bore line, which is where `lift_collision` puts the landing
    wall, so the corridor's floor and the shaft's own sill overlap rather than
    leaving a seam at the one place a body crosses.
    """
    ls = g["landing_side"]
    z0 = g["z_m"] + ls * g["shaft"]["bore_hd"]
    return z0, z0 + ls * LOBBY_M


def lobby_stand(g, lg, above_m=0.05):
    """Where a body stands in a landing's lobby -- world metres.

    `above_m` is small for `collision.stand_at`'s reason: a spawn is a claim
    that a person can stand there, and a claim that needs a metre of falling to
    resolve is being hoped for rather than checked. UP IS INWARD, so standing
    above the floor is a SMALLER radius.
    """
    ls = g["landing_side"]
    z = g["z_m"] + ls * (g["shaft"]["bore_hd"] + LOBBY_M / 2.0)
    r = lg["walk_r_m"] - above_m
    a = math.radians(g["angle_deg"])
    return (r * math.cos(a), r * math.sin(a), z)


def static_collision(schema, profile, g):
    """The shell that does not move: shaft, sills, and a lobby at every landing.

    The car is NOT in it. `lift.lift_collision(car=False)` is what the shaft
    looks like when the car is somewhere else, which is exactly what a runtime
    needs -- the floor of the car has to be a body the engine can move, and a
    floor baked into the static shell is a floor at one deck for ever.
    """
    sv, st, sm = L.lift_collision(schema, profile, g=g, car=False)
    verts, tris = list(sv), list(st)
    groups = [(f"liftshaft__{n}", a, b) for n, a, b in sm["groups"]]
    z0, z1 = lobby_span(g)
    for lg in g["landings"]:
        lv, lt, _lm = C.axial_shell(schema, profile, g["sector"],
                                    g["ring_index"], z0, z1,
                                    angle_deg=g["angle_deg"],
                                    radius_m=lg["floor_r_m"])
        o, t0 = len(verts), len(tris)
        verts.extend(lv)
        tris.extend((a + o, b + o, c + o) for a, b, c in lt)
        groups.append((f"liftlobby_{lg['index']}", t0, len(tris)))
    return verts, tris, groups


def static_render(schema, profile, g, lobbies=True):
    """What the static half looks like. Same pieces, the visible versions."""
    sv, st, sm = L.lift_shaft(schema, profile, g=g,
                              sector=g["sector"], ring_index=g["ring_index"],
                              decks=[lg["deck"] for lg in g["landings"]],
                              angle_deg=g["angle_deg"], z_m=g["z_m"],
                              landing_side=g["landing_side"])
    verts, tris = list(sv), list(st)
    groups = [(f"liftshaft__{n}", a, b) for n, a, b in sm["groups"]]
    if lobbies:
        z0, z1 = lobby_span(g)
        for lg in g["landings"]:
            lv, lt, lm = it.axial_run(schema, profile, g["sector"],
                                      g["ring_index"], z0, z1,
                                      angle_deg=g["angle_deg"],
                                      radius_m=lg["floor_r_m"])
            o, t0 = len(verts), len(tris)
            verts.extend(lv)
            tris.extend((a + o, b + o, c + o) for a, b, c in lt)
            groups.extend((f"liftlobby{lg['index']}__{n}", t0 + a, t0 + b)
                          for n, a, b in lm["groups"])
    return verts, tris, groups


def _tri_centroid(verts, tri):
    a, b, c = tri
    return tuple((verts[a][k] + verts[b][k] + verts[c][k]) / 3.0
                 for k in range(3))


def car_render(schema, profile, g):
    """The car, with its two door leaves as their own groups. -> (v, t, groups, meta)

    THE LEAVES ARE FOUND BY BUILDING THE CAR TWICE. `lift.lift_car` takes an
    `open_fraction` and merges the leaves into the body, so the only way to know
    which triangles move -- and how far, and which way -- without repeating
    `interior_kit.door_leaf`'s arithmetic is to ask the generator for both
    states and subtract. Per triangle, because `weld` fuses the two shut leaves
    to each other (their coincident face is `lift.py`'s own documented four
    non-manifold edges) and the vertex lists are therefore not comparable.

    Everything is emitted MINUS the car's parked position, so the mesh is a
    2.4 m box about its own origin instead of a box 210 m from the axis and
    7.5 km down the ship. The runtime puts it back with a node transform. That
    is not tidiness: the glb carries float32 positions, which at z = 7500 m
    resolve to 0.5 mm, and the thing this file exists to do is move it.
    """
    at = g["landings"][0]
    v0, t0, m0 = L.lift_car(schema, profile, g=g, at_deck=at,
                            open_fraction=0.0)
    v1, t1, _m1 = L.lift_car(schema, profile, g=g, at_deck=at,
                             open_fraction=1.0)
    if len(t0) != len(t1):
        raise AssertionError(
            f"lift_car changed its triangle count between open_fraction 0 and "
            f"1 ({len(t0)} -> {len(t1)}); the per-triangle difference this "
            f"function takes is not defined")
    # WHICH TRIANGLES ARE LEAF, RESOLVED THE WAY THE OBJ RESOLVES THEM.
    # `interior_kit.tagged_spans` returns one span per `_merge`, so `door_leaf`
    # arrives as seven spans and not one, and a span may be overridden by a
    # later one -- `write_obj` is last-wins and so is this. Filtering on the
    # name after resolution is the only reading that matches what gets written.
    names = [None] * len(t0)
    for n, a, b in m0["groups"]:
        for i in range(a, min(b, len(t0))):
            names[i] = n
    leaf_idx = [i for i, n in enumerate(names) if n == "door_leaf"]
    if not leaf_idx:
        raise AssertionError("the car has no door_leaf triangles")
    c0 = [_tri_centroid(v0, t0[i]) for i in leaf_idx]
    c1 = [_tri_centroid(v1, t1[i]) for i in leaf_idx]
    deltas = [tuple(b[k] - a[k] for k in range(3)) for a, b in zip(c0, c1)]
    # Two leaves, and which is which is read off the geometry: they travel in
    # opposite directions, so the sign of the projection onto the first non-zero
    # delta separates them. Nothing has to say "left" and "right".
    ref = max(deltas, key=lambda d: d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    reflen = math.sqrt(sum(c * c for c in ref))
    if reflen < 1e-6:
        raise AssertionError("no leaf moved between open_fraction 0 and 1")
    side = []
    for d in deltas:
        s = sum(d[k] * ref[k] for k in range(3)) / reflen
        side.append(0 if s > reflen * 0.5 else (1 if s < -reflen * 0.5 else -1))
    travel = {}
    for k in (0, 1):
        mine = [d for d, s in zip(deltas, side) if s == k]
        if not mine:
            raise AssertionError(f"leaf {k} has no triangles")
        travel[k] = tuple(sum(d[j] for d in mine) / len(mine) for j in range(3))

    px, py, pz = g["origin"]
    verts = [(x - px, y - py, z - pz) for x, y, z in v0]
    out = [f"liftcar__{n}" if n else "liftcar__untagged" for n in names]
    for j, i in enumerate(leaf_idx):
        s = side[j]
        out[i] = f"liftleaf_{s}" if s >= 0 else "liftcar__door_leaf_fixed"
    groups = [(out[i], i, i + 1) for i in range(len(t0))]
    meta = {"pivot": [px, py, pz],
            "leaf_travel": {str(k): list(travel[k]) for k in travel},
            "leaf_travel_m": {str(k): math.sqrt(sum(c * c for c in travel[k]))
                              for k in travel},
            "leaf_tris": {str(k): sum(1 for s in side if s == k)
                          for k in (0, 1)},
            "triangles": len(t0)}
    return verts, t0, groups, meta


def _box(verts, tris, lo, hi):
    """A closed box, wound outward, from two opposite corners."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    p = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    ctr = tuple((lo[k] + hi[k]) / 2.0 for k in range(3))
    faces = ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))
    for f in faces:
        pts = [p[i] for i in f]
        mid = [sum(q[k] for q in pts) / 4.0 for k in range(3)]
        L._quad(verts, tris, pts, [mid[k] - ctr[k] for k in range(3)])


def car_collision(schema, profile, g):
    """The car's own shell, plus the solid its shut door is. -> (v, t, groups)

    `lift.lift_collision` emits shaft, sills and car in one mesh and reports the
    car's triangle span; only that span is taken, because the whole point is
    that this piece moves and the rest does not.

    THE DOOR PANEL is the one piece of geometry this file authors, and it is
    `collision.door_panel` applied to a car: that function's own 0.12 m
    thickness and 0.02 m margins ("a collider that exactly matches an opening
    leaves a hairline a capsule can catch on"), filling the aperture
    `lift.shaft_geometry` already states. Without it "the doors are shut" is a
    claim about pixels only, and a player could walk out of a moving car into
    the shaft -- which is the same defect `godot/scripts/door.gd` was written to
    end, one vehicle along.
    """
    cv, ct, cm = L.lift_collision(schema, profile, g=g, at_deck=g["landings"][0],
                                  car=True)
    span = [(a, b) for n, a, b in cm["groups"] if n == "lift_car"]
    if len(span) != 1:
        raise AssertionError(f"expected one lift_car span, got {len(span)}")
    lo, hi = span[0]
    keep = ct[lo:hi]
    used = sorted({i for t in keep for i in t})
    remap = {j: i for i, j in enumerate(used)}
    px, py, pz = g["origin"]
    verts = [(cv[j][0] - px, cv[j][1] - py, cv[j][2] - pz) for j in used]
    tris = [(remap[a], remap[b], remap[c]) for a, b, c in keep]
    groups = [("liftcarbody", 0, len(tris))]

    ls = g["landing_side"]
    car, door = g["car"], g["door"]
    hw = door["w"] / 2.0 + 0.02
    zf = ls * car["clear_d"] / 2.0
    lv, lt = [], []
    _box(lv, lt, (-hw, -0.02, min(zf - 0.06, zf + 0.06)),
         (hw, door["h"] + 0.02, max(zf - 0.06, zf + 0.06)))
    pv = L.place(g, lv)
    o, t0 = len(verts), len(tris)
    verts.extend((x - px, y - py, z - pz) for x, y, z in pv)
    tris.extend((a + o, b + o, c + o) for a, b, c in lt)
    groups.append(("liftdoorpanel", t0, len(tris)))
    return verts, tris, groups


# ---------------------------------------------------------------------------
# Writing it out
# ---------------------------------------------------------------------------

def _glb(obj_path):
    """OBJ -> GLB. `station/export_gltf.py` makes one node per group name, which
    is how the runtime gets a car it can move without touching the shaft."""
    import export_gltf                                          # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path,
                "--out", obj_path[:-4] + ".glb"]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    return obj_path[:-4] + ".glb"


def build_lift(schema, profile, g=None, lobby_render=True, quiet=False):
    """Write every file the runtime needs, and the manifest that indexes them."""
    os.makedirs(OUT, exist_ok=True)
    g = g or shaft(schema, profile)
    stem = os.path.join(OUT, "lift")

    sv, st, sg = static_collision(schema, profile, g)
    C.write_obj(stem + "_static_col.obj", sv, st, sg, name="liftstatic")
    rv, rt, rg = static_render(schema, profile, g, lobbies=lobby_render)
    C.write_obj(stem + "_static.obj", rv, rt, rg, name="liftstatic")
    cv, ct, cg, cmeta = car_render(schema, profile, g)
    C.write_obj(stem + "_car.obj", cv, ct, cg, name="liftcar")
    xv, xt, xg = car_collision(schema, profile, g)
    C.write_obj(stem + "_car_col.obj", xv, xt, xg, name="liftcarbody")
    for p in ("_static_col", "_static", "_car", "_car_col"):
        out = _glb(stem + p + ".obj")
        if not quiet:
            print(f"  wrote {os.path.relpath(out, ROOT)}")

    ux, uy, _uz = L._basis(g["angle_deg"])
    rides = {}
    for a in g["landings"]:
        for b in g["landings"]:
            if a["index"] == b["index"]:
                continue
            rise = abs(a["walk_r_m"] - b["walk_r_m"])
            rides[f"{a['index']}-{b['index']}"] = _ride_table(schema, rise)

    man = {
        "kind": "lift",
        "sector": g["sector"], "ring": g["ring_index"],
        "angle_deg": g["angle_deg"], "z_m": g["z_m"],
        "landing_side": g["landing_side"],
        "static_glb": stem + "_static.glb",
        "static_col_glb": stem + "_static_col.glb",
        "car_glb": stem + "_car.glb",
        "car_col_glb": stem + "_car_col.glb",
        # The shaft's local frame, so the runtime can ask "is the body in the
        # car" in the car's own coordinates instead of guessing from a radius.
        # `lift.place` is a rigid rotation; these are its columns.
        "origin": list(g["origin"]),
        "ux": list(ux), "uy": list(uy),
        "travel_axis": list(uy),
        "pivot": cmeta["pivot"],
        "leaf_travel": cmeta["leaf_travel"],
        "leaf_travel_m": cmeta["leaf_travel_m"],
        "landings": [{
            "index": lg["index"], "deck": lg["deck"],
            "y_m": lg["y_m"], "walk_r_m": lg["walk_r_m"],
            "floor_r_m": lg["floor_r_m"], "floor_g": lg["floor_g"],
            "stand": list(lobby_stand(g, lg)),
            "car_stand": list(L.stand_in_car(g, at_deck=lg)),
        } for lg in g["landings"]],
        "car": {"clear_w": g["car"]["clear_w"], "clear_d": g["car"]["clear_d"],
                "clear_h": g["car"]["clear_h"],
                "door_w": g["door"]["w"], "door_h": g["door"]["h"]},
        "bore_hd": g["shaft"]["bore_hd"], "bore_hw": g["shaft"]["bore_hw"],
        "y_pit": g["shaft"]["y_pit"],
        "rides": rides,
        "dwell_s": NAV.TRANSIT_DWELL_S,
        "v_cap_m_s": NAV.coriolis_speed_cap(schema),
        "rise_m": g["rise_m"],
        "gravity_g": g["landings"][0]["floor_g"],
        "g0_m_s2": g0(schema),
        "render_tris": len(rt), "collision_tris": len(st),
        "car_tris": len(ct), "car_collision_tris": len(xt),
    }
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    return man


# ---------------------------------------------------------------------------
# The tram -- the phase parameter nothing ever changed
# ---------------------------------------------------------------------------

def build_tram(schema, profile, sector=None, count=None, angle_deg=0.0,
               quiet=False):
    """One guideway's cars, each as its own node, plus the line's timetable.

    `tram.guideway_cars` places `count` cars evenly along the sector and moves
    the whole train by `phase` alone. It is called here ONCE, at phase 0, and
    the cars are sliced apart by its own reported `car_triangles` -- so the mesh
    the runtime moves is the mesh that function emits, and the runtime's job is
    only to reproduce its placement rule as a function of time.

    THE GATE IS THAT REPRODUCTION. `--tram` asks the engine where its cars are
    at a series of times, recomputes `guideway_cars(phase=)` at the matching
    phases in Python, and compares. A runtime with its own idea of where a car
    goes fails.
    """
    os.makedirs(OUT, exist_ok=True)
    sector = sector or it.drum_sector(schema, profile)
    count = count or TRAM.CARS_ON_A_GUIDEWAY
    v, t, m = TRAM.guideway_cars(schema, profile, sector, angle_deg,
                                 count=count, phase=0.0)
    per = m["car_triangles"]
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = float(ex["z0"]), float(ex["z1"])
    spacing = (z1 - z0) / count

    line = T.guideway_line(schema, profile, sector)
    rep = T.line_report(schema, line)
    legs = spacing / rep["spacing_m"]
    cycle_s = legs * (rep["leg_s"] + T.DWELL_S)

    verts, tris, groups = [], [], []
    for i in range(count):
        lo, hi = i * per, (i + 1) * per
        keep = t[lo:hi]
        used = sorted({j for tr in keep for j in tr})
        remap = {j: k for k, j in enumerate(used)}
        zc = m["placements"][i]["z_m"]
        o, t_lo = len(verts), len(tris)
        verts.extend((v[j][0], v[j][1], v[j][2] - zc) for j in used)
        tris.extend((remap[a] + o, remap[b] + o, remap[c] + o)
                    for a, b, c in keep)
        groups.append((f"tramcar_{i}", t_lo, len(tris)))
    stem = os.path.join(OUT, "tram")
    C.write_obj(stem + "_cars.obj", verts, tris, groups, name="tramcar")
    out = _glb(stem + "_cars.obj")
    if not quiet:
        print(f"  wrote {os.path.relpath(out, ROOT)}")

    man = {
        "kind": "tram",
        "sector": sector, "angle_deg": angle_deg, "count": count,
        "cars_glb": stem + "_cars.glb",
        "z0": z0, "z1": z1, "spacing_m": spacing,
        "car_length_m": TRAM.car_length(),
        "car_z0": [p["z_m"] for p in m["placements"]],
        "cycle_s": cycle_s, "legs_per_spacing": legs,
        "leg_s": rep["leg_s"], "dwell_s": T.DWELL_S,
        "stop_spacing_m": rep["spacing_m"],
        "peak_speed_m_s": rep["peak_speed_m_s"],
        "leg_table": _leg_table(rep["spacing_m"])["table"],
        "triangles": len(tris),
    }
    with open(stem + ".json", "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    return man


def tram_z(man, i, phase):
    """Where car `i` is at `phase`. `tram.guideway_cars`'s own rule, restated
    ONCE in Python so the gate has something to compare the engine against --
    and `_selftest` checks this restatement against `guideway_cars` itself."""
    z = man["z0"] + man["spacing_m"] * ((i + 0.5 + phase) % man["count"])
    half = man["car_length_m"] / 2.0
    return min(max(z, man["z0"] + half), man["z1"] - half)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def godot_binary():
    """`station/walkable.py`'s own search, because there is one engine here."""
    import walkable as W                                        # noqa: PLC0415
    return W.godot_binary()


def _run(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout}s"
    return p.stdout + p.stderr, None


def ride(man, godot, engine_root, frm, to, park=None, timeout=900, extra=(),
         verbose=False, **switch):
    """Launch the runtime headless and parse its verdict.

    `switch` is passed straight through as `--<name>=<value>`: `carry`, `snap`,
    `platform` and `collider` are four independent ways a floor can take a body
    with it and the runtime keeps them independent so an A/B can move one.
    """
    cmd = [godot, "--headless", "--path", engine_root,
           "res://scenes/transit.tscn", "--",
           f"--manifest={man}", "--ride-test",
           f"--from={frm}", f"--to={to}"]
    for k, v in switch.items():
        cmd.append(f"--{k}={v}")
    if park is not None:
        cmd.append(f"--park={park}")
    cmd += list(extra)
    out, err = _run(cmd, timeout)
    if err:
        return {"error": err}
    if verbose:
        print(out)
    mm = re.search(r"RIDETEST (.+)", out)
    if not mm:
        tail = "\n".join(out.strip().splitlines()[-25:])
        return {"error": "no verdict printed", "tail": tail}
    d = {}
    for tok in mm.group(1).split():
        k, _, v = tok.partition("=")
        d[k] = v
    return d


def tram_run(man, godot, engine_root, timeout=600, verbose=False):
    cmd = [godot, "--headless", "--path", engine_root,
           "res://scenes/transit.tscn", "--",
           f"--manifest={man}", "--tram-test"]
    out, err = _run(cmd, timeout)
    if err:
        return {"error": err}
    if verbose:
        print(out)
    rows = []
    for mm in re.finditer(r"TRAMSAMPLE (.+)", out):
        d = {}
        for tok in mm.group(1).split():
            k, _, v = tok.partition("=")
            d[k] = v
        rows.append(d)
    fin = re.search(r"TRAMTEST (.+)", out)
    d = {}
    if fin:
        for tok in fin.group(1).split():
            k, _, v = tok.partition("=")
            d[k] = v
    if not rows:
        d["error"] = "no samples printed"
        d["tail"] = "\n".join(out.strip().splitlines()[-25:])
    d["samples"] = rows
    return d


# How far the body's radial travel may miss the shaft's own rise before the ride
# is not the ride. `collision.STEP_TOLERANCE_M` is 5 mm and is about a foot
# crossing a threshold; this is about a 10.8 m journey, so it is set at the
# spawn stand-off (50 mm) -- the body starts and ends that far above two floors
# and both are measured from the floor, so the error cannot exceed it.
RIDE_TOL_M = 0.05


def ride_verdict(d, man):
    """Pass/fail in the terms the milestone is written in, with the reason."""
    if "error" in d:
        return False, d["error"] + ("\n" + d.get("tail", "") if d.get("tail")
                                    else "")
    if d.get("boarded") != "true":
        return False, "the body never got into the car"
    if d.get("alighted") != "true":
        return False, "the body never got out of the car at the far landing"
    if d.get("start_deck") == d.get("end_deck"):
        return False, (f"started and ended on deck {d.get('start_deck')} -- "
                       f"a ride that goes nowhere")
    if int(d.get("ride_offfloor", "1/0").split("/")[0]) > 0:
        off, tot = d["ride_offfloor"].split("/")
        return False, (f"left the floor for {off} of {tot} frames DURING THE "
                       f"RIDE -- the car moved and the body did not go with it")
    want = float(d.get("want_rise_m", 0.0))
    # THREE SEPARATE CLAIMS, because one number cannot carry them.
    #   net   -- the body ENDED a shaft's height away from where it started
    #   floor -- and covered that distance while standing on something
    #   air   -- and essentially none of it falling
    # `radial_floor_m` is a total variation and so can only grow: a body that
    # wobbles 30 mm crossing a sill adds 30 mm to it. Asserting it alone would
    # be an assertion about noise as much as about the ride.
    net = abs(float(d.get("r_end", 0.0)) - float(d.get("r_start", 0.0)))
    if abs(net - want) > RIDE_TOL_M:
        return False, (f"ended {net:.3f} m of radius from where it started, "
                       f"against a {want:.3f} m shaft")
    got = float(d.get("radial_floor_m", 0.0))
    if got < want - RIDE_TOL_M:
        return False, (f"only {got:.3f} m of the {want:.3f} m was covered on "
                       f"the floor")
    if float(d.get("radial_air_m", 0.0)) > RIDE_TOL_M:
        return False, (f"{float(d['radial_air_m']):.3f} m of radius was covered "
                       f"in the air -- that is falling, not riding")
    if float(d.get("standoff_max_mm", 1e9)) > 1000.0 * RIDE_TOL_M:
        return False, (f"stood {d['standoff_max_mm']} mm off the car floor at "
                       f"worst -- it is not riding, it is bouncing")
    return True, ""


def _fmt(d):
    return (f"start deck {d.get('start_deck')} -> end deck {d.get('end_deck')}, "
            f"radial {float(d.get('radial_floor_m', 0)):.3f} m on the floor "
            f"({float(d.get('radial_air_m', 0)):.3f} m in the air), "
            f"offfloor {d.get('offfloor')} overall / {d.get('ride_offfloor')} "
            f"during the ride")


def gate(argv):
    """The deliverable: a body boards, rides, and alights, with two controls."""
    schema, profile = it.load()
    godot = argv.godot or godot_binary()
    engine_root = argv.engine_root or os.path.join(ROOT, "godot")
    if godot is None:
        print("no Godot binary found")
        return 2
    g = shaft(schema, profile)
    man = build_lift(schema, profile, g, lobby_render=not argv.no_lobby_render)
    path = os.path.join(OUT, "lift.json")

    top = g["landings"][-1]
    bot = g["landings"][0]
    frm = argv.frm if argv.frm is not None else top["index"]
    to = argv.to if argv.to is not None else bot["index"]
    rise = abs(g["landings"][frm]["walk_r_m"] - g["landings"][to]["walk_r_m"])

    print(f"\nTHE LIFT RUNS. {g['sector']} ring {g['ring_index']} at "
          f"{g['angle_deg']:.0f} deg, z={g['z_m']:.0f}: "
          f"{len(g['landings'])} landings over {g['rise_m']:.1f} m of radius, "
          f"{man['render_tris']:,} render tri, "
          f"{man['collision_tris']:,} static collision tri, "
          f"{man['car_collision_tris']} on the car\n")
    print(f"  ride {frm} -> {to}: {rise:.3f} m of radius in "
          f"{NAV.lift_ride_s(schema, rise):.3f} s "
          f"(navigation.lift_ride_s), peak "
          f"{NAV.coriolis_speed_cap(schema):.4f} m/s (the Coriolis cap)")
    print(f"  door leaf travel {man['leaf_travel_m']['0'] * 1000:.0f} mm, "
          f"measured off two builds of interior_kit.door_leaf\n")

    rows = []
    d = ride(path, godot, engine_root, frm, to,
             timeout=argv.timeout, verbose=argv.verbose)
    okay, why = ride_verdict(d, man)
    print(f"  {'PASS' if okay else 'FAIL'}  the ride     {_fmt(d)}")
    if d.get("boarded"):
        print(f"        {' ' * 12}standoff {d.get('standoff_max_mm')} mm, "
              f"car moved {d.get('car_moved_m')} m, "
              f"doors shut before it moved: {d.get('doors_shut_before_move')}, "
              f"ride {d.get('ride_s')} s over {d.get('ride_frames')} frames, "
              f"standing {d.get('door_z_m')} m clear of the shut door")
    if not okay:
        print(f"        {' ' * 12}{why}")
    rows.append(("the ride", okay, d))

    # CONTROL 1 -- the car is somewhere else. `station/lift.py`'s own self-test
    # measures this as a 2,315 mm fall on a three-landing shaft; here it is the
    # full shaft and a body that walks into a doorway with nothing behind it.
    c1 = ride(path, godot, engine_root, frm, to,
              park=to, timeout=argv.timeout, verbose=argv.verbose)
    fell = float(c1.get("fell_m", 0.0)) if "error" not in c1 else 0.0
    air = float(c1.get("radial_air_m", 0.0)) if "error" not in c1 else 0.0
    c1ok = ("error" not in c1 and c1.get("boarded") != "true" and air > 1.0)
    print(f"\n  {'FIRED' if c1ok else 'DID NOT FIRE'}  control: the car parked "
          f"at landing {to}")
    print(f"        the body walked into the doorway and fell {fell:.3f} m "
          f"down the shaft, {air:.3f} m of it off the floor "
          f"(boarded={c1.get('boarded')}, offfloor={c1.get('offfloor')}, "
          f"ended at r={c1.get('r_end')} m against landing "
          f"{to} at {g['landings'][to]['walk_r_m']:.3f} m)")
    rows.append(("control: car parked away", c1ok, c1))

    # CONTROL 2 -- NOTHING CARRIES THE BODY. Same car, same collider, same shut
    # doors. Four different things in Godot can take a body along with the floor
    # it is standing on and the control has to turn off every one of them, or it
    # is not a control -- see the decomposition below, which measures what each
    # of them does on its own. That is why this run also turns off floor snap:
    # snap alone carries a body down this shaft, because the ride is capped at
    # 3.13 m/s, which is 52 mm a frame, and `floor_snap_length` defaults to
    # 100 mm.
    c2 = ride(path, godot, engine_root, frm, to, carry="off", snap="off",
              timeout=argv.timeout, verbose=argv.verbose)
    c2off = int(c2.get("ride_offfloor", "0/0").split("/")[0]) \
        if "error" not in c2 else -1
    c2ok = ("error" not in c2 and c2off > 0)
    print(f"\n  {'FIRED' if c2ok else 'DID NOT FIRE'}  control: nothing carries "
          f"the body (carry off, snap off, platform off)")
    print(f"        {_fmt(c2)}")
    print(f"        the body lost the floor from ride frame "
          f"{c2.get('ride_off_first')} to {c2.get('ride_off_last')} of "
          f"{c2.get('ride_offfloor')}, standing "
          f"{c2.get('standoff_max_mm')} mm off the car floor at worst")
    rows.append(("control: nothing carries the body", c2ok, c2))

    # THE DECOMPOSITION. Which of the four mechanisms carries a body on its own,
    # measured rather than reasoned about. It is not pass/fail -- it is the
    # answer to "what is the explicit carry actually buying", and without it the
    # control above changes two switches at once and cannot say which one did
    # the work.
    if not argv.quick:
        print("\n  what each mechanism does ALONE (carry off in all four):")
        for label, kw in (
                ("floor snap only          ", dict(carry="off")),
                ("platform velocity only   ",
                 dict(carry="off", snap="off", platform="on")),
                ("a teleported static body ",
                 dict(carry="off", snap="off", collider="static")),
                ("the shipped carry        ", dict()),
        ):
            r = ride(path, godot, engine_root, frm, to, timeout=argv.timeout,
                     **kw)
            if "error" in r:
                print(f"    {label}  ERROR {r['error']}")
                continue
            print(f"    {label}  ride_offfloor={r.get('ride_offfloor'):>8}  "
                  f"standoff={float(r.get('standoff_max_mm', 0)):7.2f} mm  "
                  f"radial_floor={float(r.get('radial_floor_m', 0)):7.3f} m  "
                  f"end deck {r.get('end_deck')}")

    bad = [n for n, o, _ in rows if not o]
    print("\n" + ("ALL GREEN" if not bad else "FAILED: " + "; ".join(bad)))
    return 0 if not bad else 1


def tram_gate(argv):
    schema, profile = it.load()
    godot = argv.godot or godot_binary()
    engine_root = argv.engine_root or os.path.join(ROOT, "godot")
    if godot is None:
        print("no Godot binary found")
        return 2
    man = build_tram(schema, profile)
    path = os.path.join(OUT, "tram.json")
    print(f"\nTHE TRAM RUNS. {man['count']} cars of "
          f"{man['car_length_m']:.0f} m on one guideway of "
          f"{man['sector']}, {man['spacing_m']:,.0f} m apart; a car covers that "
          f"spacing in {man['cycle_s']:.1f} s "
          f"({man['legs_per_spacing']:.0f} legs of {man['leg_s']:.1f} s plus "
          f"{man['dwell_s']:.0f} s dwell each, transit.line_report), peak "
          f"{man['peak_speed_m_s']:.1f} m/s\n")
    d = tram_run(path, godot, engine_root, timeout=argv.timeout,
                 verbose=argv.verbose)
    if "error" in d:
        print("  FAIL " + d["error"])
        print(d.get("tail", ""))
        return 1
    worst, moved = 0.0, 0.0
    sector, ang = man["sector"], man["angle_deg"]
    for s in d["samples"]:
        ph = float(s["phase"])
        _v, _t, mm = TRAM.guideway_cars(schema, profile, sector, ang,
                                        count=man["count"], phase=ph)
        for i, pl in enumerate(mm["placements"]):
            got = float(s[f"car{i}_z"])
            worst = max(worst, abs(got - pl["z_m"]))
            moved = max(moved, abs(got - man["car_z0"][i]))
        print(f"    t={float(s['t']):7.1f} s  phase={ph:7.4f}  " + "  ".join(
            f"car{i} {float(s[f'car{i}_z']):9.2f} m "
            f"(python {pl['z_m']:9.2f})"
            for i, pl in enumerate(mm["placements"])))
    # 10 mm, and it is not a tolerance for the runtime's arithmetic: it is
    # `guideway_cars`'s own, which rounds the `z_m` it reports in `placements`
    # to two decimals. The engine can therefore never agree with it more closely
    # than 5 mm however exact it is, and a tighter bar would be a bar on the
    # report rather than on the placement.
    ok1 = worst < 0.01
    ok2 = moved > 1.0
    print(f"\n  {'PASS' if ok1 else 'FAIL'}  every car is where "
          f"tram.guideway_cars(phase=) puts it -- worst disagreement "
          f"{worst * 1000:.3f} mm over {len(d['samples'])} samples, against "
          f"the 5 mm that function's own 2-decimal placement report allows")
    print(f"  {'PASS' if ok2 else 'FAIL'}  and they actually moved -- "
          f"{moved:,.1f} m from where they were baked")
    return 0 if (ok1 and ok2) else 1


# ---------------------------------------------------------------------------
# Self-test. Everything that can be answered without an engine.
# ---------------------------------------------------------------------------

def _selftest():
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (f"  {note}" if note else ""))

    schema, profile = it.load()
    g = shaft(schema, profile)

    print("\nTHE RUNTIME'S NUMBERS AND WHERE THEY CAME FROM\n")

    # --- the timings are not ours ----------------------------------------
    rise = g["rise_m"]
    tab = _ride_table(schema, rise)
    check("the ride time is navigation.lift_ride_s and nothing else",
          abs(tab["seconds"] - NAV.lift_ride_s(schema, rise)) < 1e-12,
          f"{tab['seconds']:.4f} s for {rise:.3f} m")
    check("and transit.climb_leg agrees, through code that shares nothing",
          abs(tab["seconds"] - T.climb_leg(schema, rise, "lift")["seconds"])
          < 1e-9,
          f"climb_leg {T.climb_leg(schema, rise, 'lift')['seconds']:.4f} s")
    cap = NAV.coriolis_speed_cap(schema)
    check("the table's own peak speed IS the Coriolis cap",
          abs(tab["peak_m_s"] - cap) / cap < 0.01,
          f"table peaks at {tab['peak_m_s']:.4f} m/s against a "
          f"{cap:.4f} m/s cap")
    # NEGATIVE CONTROL: a linear table would run the same distance in the same
    # time at 2/3 the peak. If the check above cannot tell those apart it is
    # measuring the mean and calling it the peak.
    lin_peak = rise / tab["seconds"]
    check("and a constant-speed table would NOT pass that check -- control",
          abs(lin_peak - cap) / cap > 0.3,
          f"a linear ride peaks at {lin_peak:.4f} m/s, {lin_peak / cap:.2f}x "
          f"the cap")
    check("the sampled table is within the step tolerance of the curve",
          _table_error(tab["table"]) * rise < C.STEP_TOLERANCE_M,
          f"{_table_error(tab['table']) * rise * 1000:.2f} mm of chord error "
          f"on a {rise:.1f} m rise, against "
          f"{C.STEP_TOLERANCE_M * 1000:.0f} mm")
    lg0_ = g["landings"][0]
    # `decks_in_ring` rounds `floor_r_m` to 2 dp and `floor_g` to 4, so the
    # agreement is to those roundings and not to machine precision. Saying 1e-6
    # here would be asserting a tidiness the source does not claim.
    dg = abs(it.gravity_at(schema, lg0_["floor_r_m"]) - lg0_["floor_g"])
    check("the deck's own gravity is interior.gravity_at, read not restated",
          dg < 2e-4 and abs(g0(schema) - 9.80665) < 1e-9,
          f"deck 0 sits at {lg0_['floor_g']:.4f} g at "
          f"{lg0_['floor_r_m']:.2f} m ({dg:.2e} off gravity_at, which is its "
          f"own rounding), standard gravity {g0(schema)} m/s^2 from the "
          f"schema -> {lg0_['floor_g'] * g0(schema):.3f} m/s^2 for the "
          f"character controller")

    # --- the lobby is the station's own corridor --------------------------
    z0, z1 = lobby_span(g)
    lg = g["landings"][0]
    lv, lt, lm = C.axial_shell(schema, profile, g["sector"], g["ring_index"],
                               z0, z1, angle_deg=g["angle_deg"],
                               radius_m=lg["floor_r_m"])
    check("the lobby floor is on the car's own walking radius",
          abs(lm["floor_r_m"] - lg["walk_r_m"]) < 1e-4,
          f"lobby {lm['floor_r_m']:.4f} m, car floor {lg['walk_r_m']:.4f} m")
    check("and it is one section of interior.axial_run, not a length we chose",
          abs(LOBBY_M - it.AXIAL_SECTION_M) < 1e-12,
          f"{LOBBY_M:.3f} m")

    # --- the pieces that move are their own meshes ------------------------
    cv, ct, cg, cmeta = car_render(schema, profile, g)
    names = {n for n, _a, _b in cg}
    check("the car's two door leaves are their own groups",
          "liftleaf_0" in names and "liftleaf_1" in names,
          f"leaf triangles {cmeta['leaf_tris']}")
    t0 = cmeta["leaf_travel"]["0"]
    t1 = cmeta["leaf_travel"]["1"]
    dot = sum(a * b for a, b in zip(t0, t1))
    check("and they travel in opposite directions, read off the mesh",
          dot < 0.0,
          f"{cmeta['leaf_travel_m']['0'] * 1000:.0f} mm and "
          f"{cmeta['leaf_travel_m']['1'] * 1000:.0f} mm apart, dot {dot:+.4f}")
    check("the measured leaf travel is half the kit's door width",
          abs(cmeta["leaf_travel_m"]["0"]
              - K.PROVISIONAL["door_width_m"] / 2.0) < 0.02,
          f"{cmeta['leaf_travel_m']['0']:.4f} m against "
          f"{K.PROVISIONAL['door_width_m'] / 2.0:.4f} m -- MEASURED, and this "
          f"check is the only place the two are compared")
    # EVERY TRIANGLE IN A GROUP A MATERIAL RULE CAN SEE, and 144 of them are
    # not. This is session 3x's finding (`door_assembly` merged 1,248 triangles
    # a deck with no `tag()` block, so the surface a player looks straight at
    # took no light) and session 4f's (45 groups named by interpolation that no
    # scan over source could see), arriving through a third door: `lift.lift_car`
    # merges `interior_kit.handrail` three times with no `tag()` around it, so
    # the car's handrails -- the dominant warm accent in every interior frame in
    # the reference set -- export as `liftcar__untagged` and take the glTF
    # fallback. `materials.py` already binds the name (`rail_band`/`handrail`,
    # line 974); nothing has to be authored. The patch is in
    # docs/transport-4g.md and it is three lines in a file this module does not
    # own. Asserted as a CEILING rather than an equality so it fails when the
    # number grows and goes green when the patch lands -- the opposite of
    # `materials._selftest`'s `hull_exterior.binds == ()`, which could only fail
    # if somebody fixed it.
    n_untagged = sum(1 for n, _a, _b in cg if n == "liftcar__untagged")
    rails = 3 * len(K.handrail(2.0)[1])
    check("no more of the car is unmaterialled than the kit's untagged rails",
          n_untagged <= rails,
          f"{n_untagged} of {len(ct)} car triangles carry no group -- exactly "
          f"the {rails} of three interior_kit.handrail merges that "
          f"lift.lift_car makes outside a tag() block")
    check("the car mesh is about its own origin, not 7.5 km down the ship",
          max(abs(c) for p in cv for c in p) < 10.0,
          f"largest coordinate {max(abs(c) for p in cv for c in p):.3f} m")

    xv, xt, xg = car_collision(schema, profile, g)
    check("the car's collision is the car alone",
          [n for n, _a, _b in xg] == ["liftcarbody", "liftdoorpanel"]
          and len(xt) < 60,
          f"{len(xt)} triangles in {[n for n, _a, _b in xg]}")
    # The door panel has to fill the aperture the shell leaves open, or "shut"
    # is a claim about pixels. Cast the way a body walks out.
    lo, hi = [(a, b) for n, a, b in xg if n == "liftdoorpanel"][0]
    px, py, pz = g["origin"]
    world = [(x + px, y + py, z + pz) for x, y, z in xv]
    ls = g["landing_side"]
    out_dir = (0.0, 0.0, float(ls))
    o = L.place(g, [(0.0, 0.9, 0.0)])[0]
    hit_panel = C.cast(o, out_dir, world, xt[lo:hi])
    hit_body = C.cast(o, out_dir, world, xt[:lo])
    check("the shut door is solid -- a body cannot walk out of a moving car",
          hit_panel is not None and hit_body is None,
          f"panel stops it at {hit_panel and round(hit_panel, 3)} m; the car "
          f"body alone lets it through ({hit_body}) -- which is the control")

    sv, st, sg = static_collision(schema, profile, g)
    check("the static shell has a lobby at every landing",
          sum(1 for n, _a, _b in sg if n.startswith("liftlobby"))
          == len(g["landings"]),
          f"{sum(1 for n, _a, _b in sg if n.startswith('liftlobby'))} lobbies, "
          f"{len(st):,} triangles")

    # A BODY WALKS FROM THE LOBBY INTO THE CAR. `lift.py` gates the threshold
    # over the sill; this gates the whole approach, from where the body is
    # actually spawned, over the shell this file assembles. Cast outward at
    # 0.35 m -- the capsule diameter `collision.floor_holes` uses.
    world_car = [(x + px, y + py, z + pz) for x, y, z in xv]
    allv = list(sv) + world_car
    allt = list(st) + [(a + len(sv), b + len(sv), c + len(sv)) for a, b, c in xt]
    _ux, uy, _uz = L._basis(g["angle_deg"])
    down = tuple(-c for c in uy)
    lg0 = g["landings"][0]
    z_start = ls * (g["shaft"]["bore_hd"] + LOBBY_M / 2.0)
    worst = run = 0.0
    n_ = 200
    step = abs(z_start) / (n_ - 1)
    for i in range(n_):
        zz = z_start * (1.0 - i / (n_ - 1))
        p = L.place(g, [(0.0, lg0["y_m"] + 1.0, zz)])[0]
        h = C.cast(p, down, allv, allt)
        if h is None or abs(h - 1.0) > 0.05:
            run += step
            worst = max(worst, run)
        else:
            run = 0.0
    check("a body walks the whole lobby into the car with a floor throughout",
          worst < 0.35,
          f"widest unsupported run {worst * 1000:.0f} mm over "
          f"{abs(z_start):.2f} m of approach, against a 350 mm capsule")
    # NEGATIVE CONTROL: with the car at the top the same walk has to fall in.
    xv2, xt2, _xg2 = car_collision(schema, profile, g)
    y_top = g["landings"][-1]["y_m"]
    shift = [uy[k] * y_top for k in range(3)]
    world2 = [(x + px + shift[0], y + py + shift[1], z + pz + shift[2])
              for x, y, z in xv2]
    allv2 = list(sv) + world2
    allt2 = list(st) + [(a + len(sv), b + len(sv), c + len(sv))
                        for a, b, c in xt2]
    worst2 = run = 0.0
    for i in range(n_):
        zz = z_start * (1.0 - i / (n_ - 1))
        p = L.place(g, [(0.0, lg0["y_m"] + 1.0, zz)])[0]
        h = C.cast(p, down, allv2, allt2)
        if h is None or abs(h - 1.0) > 0.05:
            run += step
            worst = max(worst, run)
            worst2 = max(worst2, run)
        else:
            run = 0.0
    check("and with the car at the top landing that walk falls into the shaft",
          worst2 > 0.35,
          f"{worst2 * 1000:.0f} mm unsupported with the car {y_top:.1f} m up")

    # --- the tram's placement rule ----------------------------------------
    sec = it.drum_sector(schema, profile)
    cnt = TRAM.CARS_ON_A_GUIDEWAY
    ex = schema["sectors"]["extents_m"][sec]
    fake = {"z0": float(ex["z0"]), "z1": float(ex["z1"]), "count": cnt,
            "spacing_m": (float(ex["z1"]) - float(ex["z0"])) / cnt,
            "car_length_m": TRAM.car_length()}
    worst_z = 0.0
    for ph in (0.0, 0.13, 0.5, 0.97, 1.4, 2.6):
        _v, _t, mm = TRAM.guideway_cars(schema, profile, sec, 0.0,
                                        count=cnt, phase=ph)
        for i, pl in enumerate(mm["placements"]):
            worst_z = max(worst_z, abs(tram_z(fake, i, ph) - pl["z_m"]))
    check("the phase rule this file gates against IS guideway_cars's own",
          worst_z < 0.006,
          f"worst {worst_z * 1000:.2f} mm over six phases and {cnt} cars "
          f"(guideway_cars rounds its placement to 2 dp)")

    line = T.guideway_line(schema, profile, sec)
    rep = T.line_report(schema, line)
    leg = _leg_table(rep["spacing_m"])
    check("the tram's leg table is transit.ride_profile's own leg",
          abs(leg["seconds"] - rep["leg_s"]) < 1e-9
          and abs(leg["peak_m_s"] - rep["peak_speed_m_s"]) < 1e-9,
          f"{leg['seconds']:.3f} s, peak {leg['peak_m_s']:.3f} m/s")
    ig = T._integrate_profile(rep["spacing_m"], T.CRUISE_ACCEL_M_S2,
                              T.JERK_M_S3)
    check("and integrating it lands on the distance transit says it does",
          abs(leg["integrated_m"] - rep["spacing_m"]) / rep["spacing_m"] < 1e-3,
          f"{leg['integrated_m']:.2f} m against {rep['spacing_m']:.2f} m "
          f"(transit._integrate_profile gets {ig['distance_m']:.2f} m)")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def _table_error(tab):
    """Worst gap between the sampled table and the curve it samples.

    Midpoint of every interval, because linear interpolation is exact at the
    samples and worst halfway between them.
    """
    worst = 0.0
    for (u0, f0), (u1, f1) in zip(tab, tab[1:]):
        u = (u0 + u1) / 2.0
        worst = max(worst, abs((f0 + f1) / 2.0 - (3 * u * u - 2 * u ** 3)))
    return worst


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true",
                    help="everything answerable without an engine")
    ap.add_argument("--build", action="store_true", help="write the meshes only")
    ap.add_argument("--ride", action="store_true",
                    help="THE GATE: a body boards, rides and alights")
    ap.add_argument("--tram", action="store_true",
                    help="the guideway train, moved by phase")
    ap.add_argument("--from", dest="frm", type=int, default=None)
    ap.add_argument("--to", dest="to", type=int, default=None)
    ap.add_argument("--godot", default=None)
    ap.add_argument("--engine-root", default=None,
                    help="the godot/ directory to run from; defaults to this "
                         "checkout's")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--no-lobby-render", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--quick", action="store_true",
                    help="skip the four-way decomposition of the carry")
    a = ap.parse_args(argv)
    if a.build:
        schema, profile = it.load()
        m = build_lift(schema, profile,
                       lobby_render=not a.no_lobby_render)
        print(json.dumps({k: v for k, v in m.items()
                          if k not in ("rides", "landings")}, indent=1))
        return 0
    if a.ride:
        return gate(a)
    if a.tram:
        return tram_gate(a)
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
