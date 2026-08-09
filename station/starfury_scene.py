#!/usr/bin/env python3
"""The bridge that puts the tested Starfury flight model into the engine.

## Why this file exists

As of session 4d the project contained a 228-line Newtonian flight model with
eighteen passing tests, a 774-line airframe with its own agreement test, a
rotating-frame module that knows exactly what a launch off a spinning hull does,
and **zero references to `starfury` in any `.gd` or `.tscn`**. The physics was
proven and unreachable. This file is the only thing between the two, and it is
deliberately thin: it computes nothing the tested modules already compute, it
*calls* them and writes the answers out where the engine can read them.

Four artefacts, all under `station/generated/scene/starfury/`:

  * `starfury.glb`   -- the airframe, straight out of `starfury_geometry.build()`
  * `launch.json`    -- the cobra bay: where it is, how fast it is going, and
                        what `rotating_frame.velocity_to_inertial` says a craft
                        released from it leaves with. THE ENGINE DOES NOT READ
                        THE ANSWER, it reads the bay and derives the answer
                        itself; the file's `expected_exit_velocity` is what its
                        derivation is checked against.
  * `vectors.json`   -- the flight model run over nine scenarios in pure Python,
                        with the full state recorded at checkpoints, PLUS 48
                        guidance samples and 16 attitude samples from
                        `station/physics/docking.py`'s approach law. The
                        GDScript port replays all of it and must land on the
                        same numbers. A port that drifts from its tested source
                        is the defect this project keeps finding.
  * `scene.json`     -- a shot `tools/render_godot.sh --shot starfury` can render

`launch.json` also carries a `dock` block -- every constant the engine's
approach needs, all of them derived by `docking.plan_approach` from the spin,
the airframe and the bay -- and a 400-sample table of the hull's own radius
against z, so the engine can measure its own clearance against the same
`components.radius_at` the hull mesh is built from.

## The dock is the launch run backwards

`--dock-gate` flies the measured cobra bay from every phase of one rotation and
reports a denominator. The whole approach is `station/physics/docking.py`; this
file supplies the real bay, the real hull and the real airframe, and checks the
engine's own flight against a second run of the same law in Python.

JSON rather than YAML, and that is not a preference: Godot parses JSON in one
built-in call and has no YAML at all. A vector file the engine cannot read is a
vector file nobody runs.

## The bay is MEASURED, not written down

`hard rule 4` -- inside and outside come from one schema -- applied a fourth
time. The launch radius is not a number in this file. It is read off
`station/generated/hull.obj`'s own `cobra_bay_well` group, which is the surface
a fighter sits in, so the launch point cannot drift from the hull the player
looks at. The schema's stated 26 m protrusion is used as a CHECK on that
measurement rather than as its source.

## Frames

Everything is in the station's world frame: **+Z fore along the 8,047 m axis,
rotation about +Z at omega**, which is what `rotating_frame.py`, the hull
generator and Godot's world all use. The airframe's body frame -- +Z forward,
+Y up, +X starboard -- is `starfury_geometry`'s, and it is the same handedness,
so a body vector reaches world space through the flight model's own
`body_to_world` and nothing else.
"""
import argparse
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION = os.path.join(ROOT, "station")
sys.path.insert(0, STATION)
sys.path.insert(0, os.path.join(STATION, "physics"))

import yaml  # noqa: E402

import components  # noqa: E402
import generate_hull  # noqa: E402
import starfury_geometry  # noqa: E402
from rotating_frame import from_schema  # noqa: E402
from starfury import Starfury, add, cross, norm, scale, sub, unit  # noqa: E402

OUT_DIR = os.path.join(STATION, "generated", "scene", "starfury")
HULL_OBJ = os.path.join(STATION, "generated", "hull.obj")
FURY_OBJ = os.path.join(STATION, "generated", "starfury.obj")

# The station's midpoint, and the aim point every exterior shot in this project
# uses. Taken from tools/export_scene.py's --target-z default rather than
# reasoned about again.
STATION_CENTRE = (0.0, 0.0, 4023.0)
# The calibrated exterior framing: 9,200 m at 18 degrees elevation, azimuth
# 214. exterior.tscn's `tonemap_exposure = 0.43` was measured AT THIS FRAMING,
# so a look-back shot that ends up here is exposed by a number that means
# something. Anywhere else and the exposure is an extrapolation.
ORBIT = (9200.0, 18.0, 214.0)
# tools/export_scene.py's `--sun-az` / `--sun-elev` defaults. Repeated here
# because the flyable scene has to aim the same key at the same hull and there
# is no import boundary between a 6,500-line shot assembler and this.
SUN_AZ, SUN_ELEV = 168.0, 34.0


# ---------------------------------------------------------------------------
# Small vector helpers. Everything heavier comes from the flight model.
# ---------------------------------------------------------------------------

def _spherical(dist, elev_deg, az_deg, target):
    """tools/export_scene.py's own convention, so that a camera placed here and
    a camera placed by `--orbit` land in the same place."""
    el, az = math.radians(elev_deg), math.radians(az_deg)
    return (target[0] + dist * math.cos(el) * math.cos(az),
            target[1] + dist * math.sin(el),
            target[2] + dist * math.cos(el) * math.sin(az))


def quat_from_basis(fwd, up):
    """Orientation whose body +Z is `fwd` and whose body +Y is as near `up` as
    orthogonality allows, as (w, x, y, z) -- the flight model's convention.

    Built through the flight model's own `body_to_world` afterwards as a check,
    because a quaternion sign error is invisible until something points
    backwards in a render nobody re-takes.
    """
    z = unit(fwd)
    x = unit(cross(up, z))
    if norm(x) < 1e-9:                      # up parallel to fwd: pick anything
        x = unit(cross((0.0, 0.0, 1.0), z))
    y = cross(z, x)
    m = ((x[0], y[0], z[0]),
         (x[1], y[1], z[1]),
         (x[2], y[2], z[2]))
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = (0.25 * s, (m[2][1] - m[1][2]) / s,
             (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s)
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        q = ((m[2][1] - m[1][2]) / s, 0.25 * s,
             (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s)
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        q = ((m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s,
             0.25 * s, (m[1][2] + m[2][1]) / s)
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        q = ((m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
             (m[1][2] + m[2][1]) / s, 0.25 * s)
    probe = Starfury(orientation=q)
    err = norm(sub(probe.forward, z))
    if err > 1e-9:
        raise AssertionError(f"quat_from_basis: nose off by {err:.3e}")
    return q


# ---------------------------------------------------------------------------
# The cobra bay, measured off the hull mesh
# ---------------------------------------------------------------------------

def _group_vertices(obj_path, group):
    """Vertices actually referenced by one OBJ group.

    The hull writer emits every vertex first and then the groups' faces, so a
    group's extent cannot be read from a vertex range -- it has to be gathered
    through the faces. Reading it any other way gives the whole hull's bounding
    box and a launch point 480 m off the axis in the wrong section.
    """
    verts = []
    used = set()
    current = None
    with open(obj_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("g "):
                current = line[2:].strip()
            elif line.startswith("f ") and current == group:
                for tok in line.split()[1:]:
                    used.add(int(tok.split("/")[0]) - 1)
    if not used:
        raise KeyError(f"{obj_path} has no group {group!r}")
    return [verts[i] for i in sorted(used)]


def cobra_bay_geometry(obj_path=HULL_OBJ, schema=None):
    """Where a fighter actually sits, read off the hull's own `cobra_bay_well`.

    Returns the FORE ring's bay nearest phase zero: its mouth radius, its axial
    station and its clocking. The mouth radius is the largest radius the well
    liner reaches, because that is the plane the craft leaves through.

    Cross-checked against the schema, not derived from it: the schema says the
    bays stand 26 m proud of the hull, so `mouth - hull radius at that z` has to
    come out near 26. It is a check because the two numbers come from different
    places -- one from a mesh, one from a table -- and agreeing is information.
    """
    if schema is None:
        schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    pts = _group_vertices(obj_path, "cobra_bay_well")
    zs = [p[2] for p in pts]
    z_lo, z_hi = min(zs), max(zs)
    mid = 0.5 * (z_lo + z_hi)
    # Two rings, clocked half a pitch apart -- see components.cobra_bay_ring.
    # The FORE ring is the one on the flared shoulder and the one the show's
    # own reference frame looks into.
    ring = [p for p in pts if p[2] >= mid]
    if not ring:
        ring = pts
    r_of = lambda p: math.hypot(p[0], p[1])           # noqa: E731
    mouth_r = max(r_of(p) for p in ring)
    z_c = sum(p[2] for p in ring) / len(ring)

    # Which bay: cluster the ring's vertices by angle and take the one whose
    # centre is nearest zero, so the launch is repeatable and nameable rather
    # than "somewhere on the ring".
    n_bays = 0
    for c in schema["components"]:
        if c["id"] == "cobra_bay":
            n_bays = c["count"]
            break
    per_ring = max(1, n_bays // 2)
    angles = sorted(math.atan2(p[1], p[0]) for p in ring)
    # Bay phase: the modal offset within one pitch.
    pitch = 2.0 * math.pi / per_ring
    off = sum(((a % pitch) for a in angles)) / len(angles)
    phase = off if off < pitch / 2 else off - pitch

    prof = generate_hull.load()[1]["profile"]
    hull_r = components.radius_at(prof, z_c)
    stated = next(c["protrusion_m"] for c in schema["components"]
                  if c["id"] == "cobra_bay")
    return {
        "source": "station/generated/hull.obj, group cobra_bay_well",
        "mouth_radius_m": mouth_r,
        "z_m": z_c,
        "z_span_m": [z_lo, z_hi],
        "phase_rad": phase,
        "bays_per_ring": per_ring,
        "hull_radius_at_z_m": hull_r,
        "measured_protrusion_m": mouth_r - hull_r,
        "schema_protrusion_m": stated,
    }


def launch_state(schema=None, bay=None):
    """Everything the engine needs about the launch, and the answer it must
    reproduce on its own.

    The exit velocity comes from `rotating_frame.DrumFrame.velocity_to_inertial`
    -- the module whose whole job is this transform -- applied to a craft AT
    REST IN THE ROTATING FRAME at the bay. That is what a cobra bay does: it
    lets go, and the station's rotation is the catapult.
    """
    if schema is None:
        schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    if bay is None:
        bay = cobra_bay_geometry(schema=schema)
    drum = from_schema(schema)
    r, z, ph = bay["mouth_radius_m"], bay["z_m"], bay["phase_rad"]
    pos = (r * math.cos(ph), r * math.sin(ph), z)
    # At rest in the rotating frame. Not "released with a nudge": the show's
    # bays have no catapult and starfury.launch_from_drum says why.
    v_exit = drum.velocity_to_inertial(pos, (0.0, 0.0, 0.0), 0.0)

    # The same number by the model's own route, as a second opinion. It places
    # the craft on the +X radius, so compare magnitudes.
    probe = Starfury()
    v_model = probe.launch_from_drum(drum, r, z)
    if abs(norm(v_model) - norm(v_exit)) > 1e-9:
        raise AssertionError(
            f"launch_from_drum {norm(v_model):.9f} != velocity_to_inertial "
            f"{norm(v_exit):.9f}")
    return {
        "omega_rad_s": drum.omega,
        "period_s": drum.period,
        "habitat_floor_radius_m": drum.floor_radius,
        "habitat_floor_speed_m_s": drum.floor_speed,
        "bay": bay,
        "release_position_m": list(pos),
        "expected_exit_velocity_m_s": list(v_exit),
        "expected_exit_speed_m_s": norm(v_exit),
        "gravity_at_bay_g": drum.gravity_in_g(r),
        "derivation": ("rotating_frame.DrumFrame.velocity_to_inertial(pos, "
                       "(0,0,0), 0) -- a craft at rest in the rotating frame "
                       "leaves carrying omega x r and nothing else"),
    }


# ---------------------------------------------------------------------------
# Reference vectors for the GDScript port
# ---------------------------------------------------------------------------

def _state(s):
    return {"position": list(s.position), "velocity": list(s.velocity),
            "orientation": list(s.orientation),
            "angular_velocity": list(s.angular_velocity)}


def _run(name, why, ship, dt, steps, command, every):
    """Run one scenario and record the full state at checkpoints.

    `command` is either `{"throttles": {...}}` -- named thrusters held open --
    or `{"demand": [[tx,ty,tz],[rx,ry,rz]]}`, which goes through `allocate` so
    the ENGINE'S allocator is tested and not only its integrator. Allocation is
    where a port is most likely to differ, because it is the one part of the
    model with a judgement in it.
    """
    initial = _state(ship)
    checks = []
    for i in range(steps):
        if "throttles" in command:
            th = command["throttles"]
        else:
            t, r = command["demand"]
            th = ship.allocate(tuple(t), tuple(r))
        ship.step(dt, th)
        if (i + 1) % every == 0:
            checks.append(dict(step=i + 1, **_state(ship)))
    return {"name": name, "why": why, "dt": dt, "steps": steps,
            "every": every, "command": command, "initial": initial,
            "checkpoints": checks}


def vectors(schema=None):
    """Nine scenarios covering every branch of the model that can be wrong.

    Chosen so that a port which passes all nine cannot be wrong in a way that
    matters: coasting tests the integrator, the rotate-while-coasting case is
    the Starfury's defining property and the one an aeroplane-shaped port
    fails, the tumble tests the gyroscopic term, and the two allocate cases
    test the thing that is not arithmetic.
    """
    if schema is None:
        schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    mains = {f"main_{a}{b}": 1.0 for a in "ul" for b in "lr"}
    out = []

    out.append(_run(
        "coast", "velocity is unchanged with no thrust -- the integrator",
        Starfury(velocity=(120.0, -30.0, 8.0)), 0.01, 400, {"throttles": {}}, 100))

    s = Starfury(velocity=(0.0, 0.0, 200.0))
    s.angular_velocity = (0.0, 1.2, 0.0)
    out.append(_run(
        "rotate_while_coasting",
        "THE DEFINING PROPERTY: the nose sweeps 344 deg and the velocity does "
        "not move. A port with any aerodynamic coupling fails here and nowhere "
        "else",
        s, 0.01, 500, {"throttles": {}}, 125))

    s = Starfury(velocity=(0.0, 0.0, 300.0), orientation=(0.0, 0.0, 1.0, 0.0))
    out.append(_run(
        "flip_and_burn", "180 deg about Y with the mains lit -- the signature "
        "manoeuvre, and the sign test on body_to_world",
        s, 0.01, 200, {"throttles": mains}, 50))

    out.append(_run(
        "asymmetric_yaw", "two mains on one side: torque, and the moment arm",
        Starfury(), 0.01, 300, {"throttles": {"main_ur": 1.0, "main_lr": 1.0}}, 75))

    out.append(_run(
        "free_tumble",
        "spin about the axis of least inertia with a perturbation: Euler's "
        "gyroscopic term, which a port that integrates alpha = torque/I alone "
        "silently drops",
        Starfury(angular_velocity=(0.05, 0.0, 2.0)), 0.002, 2500,
        {"throttles": {}}, 500))

    out.append(_run(
        "allocate_forward", "allocate() on a pure translation demand",
        Starfury(), 0.01, 200,
        {"demand": [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]}, 50))

    out.append(_run(
        "allocate_lateral", "allocate() must open ONE lateral RCS, not both",
        Starfury(), 0.01, 200,
        {"demand": [[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0]]}, 50))

    out.append(_run(
        "allocate_mixed",
        "translation and rotation demanded together, which is the case that "
        "saturates a thruster and where clamping order shows up",
        Starfury(), 0.01, 300,
        {"demand": [[0.0, 0.35, 0.8], [0.15, -0.4, 0.05]]}, 75))

    drum = from_schema(schema)
    bay = cobra_bay_geometry(schema=schema)
    s = Starfury()
    s.launch_from_drum(drum, bay["mouth_radius_m"], bay["z_m"])
    out.append(_run(
        "cobra_release",
        "released at rest in the rotating frame and left alone: the station "
        "throws it clear, unpowered",
        s, 0.05, 600, {"throttles": {}}, 150))

    # The thruster table itself, so a divergence names the thruster instead of
    # naming a scenario. `aurora_thrusters()` is deliberately duplicated in
    # three places -- the flight model, the airframe generator and now the
    # GDScript port -- for the reason starfury_geometry.py gives: importing it
    # would make the agreement test vacuous.
    ref = Starfury()
    layout = {t.name: {"position": list(t.position),
                       "direction": list(t.direction),
                       "max_thrust": t.max_thrust} for t in ref.thrusters}

    return {
        "source": "station/starfury_scene.py --build, from station/physics/starfury.py",
        "layout": layout,
        "rigid_body": {"mass_kg": ref.mass, "inertia_kg_m2": list(ref.inertia),
                       "max_linear_accel_m_s2": ref.max_linear_accel()},
        "tolerance": {"abs": 1e-6, "rel": 1e-9,
                      "why": ("both sides run the same semi-implicit Euler in "
                              "double, so agreement is a bit-level question, "
                              "not a physical one. Anything above this is a "
                              "different algorithm, not accumulated error")},
        "scenarios": out,
    }


# ---------------------------------------------------------------------------
# The airframe, and posing it
# ---------------------------------------------------------------------------

def _to_glb(obj_path, glb_path):
    subprocess.run([sys.executable, os.path.join(STATION, "export_gltf.py"),
                    "--obj", os.path.relpath(obj_path, ROOT),
                    "--out", os.path.relpath(glb_path, ROOT)],
                   check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    return glb_path


def build_airframe(out_dir=OUT_DIR):
    """The mesh, in body frame, unposed -- what the flyable scene instances."""
    sections = starfury_geometry.build()
    starfury_geometry.write_obj(FURY_OBJ, sections)
    glb = _to_glb(FURY_OBJ, os.path.join(out_dir, "starfury.glb"))
    man = starfury_geometry.manifest(sections)
    return glb, man


def pose_airframe(position, orientation, out_dir=OUT_DIR,
                  name="starfury_posed"):
    """The same mesh with one rigid transform baked into its vertices.

    Baked rather than carried on a node because the shot that matters is
    rendered by `scripts/render_shot.gd`, which loads a list of .glb files and
    has no way to be told where to put one. Adding a transform field to that
    script is an edit to another agent's file for a job a generator can do.

    The rotation is the FLIGHT MODEL'S OWN `body_to_world`, so a posed airframe
    and the craft the physics is integrating cannot disagree about which way it
    is pointing.
    """
    ship = Starfury(orientation=tuple(orientation))
    sections = starfury_geometry.build()
    posed = {}
    for key, (verts, tris) in sections.items():
        posed["starfury_" + key] = (
            [add(position, ship.body_to_world(v)) for v in verts], tris)
    obj = os.path.join(out_dir, name + ".obj")
    starfury_geometry.write_obj(obj, posed)
    return _to_glb(obj, os.path.join(out_dir, name + ".glb"))


# ---------------------------------------------------------------------------
# Shots
# ---------------------------------------------------------------------------

def waypoint():
    """Where the flight is aimed: the project's calibrated exterior framing.

    Flying to an arbitrary point and photographing from there would produce a
    frame lit by an exposure derived somewhere else. `exterior.tscn`'s
    `tonemap_exposure = 0.43` was measured against the show at 9,200 m / 18 deg
    / az 214, so a look-back that arrives HERE is exposed by a measured number
    instead of a guessed one.
    """
    return _spherical(*ORBIT, STATION_CENTRE)


def write_bundle(out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    glb, man = build_airframe(out_dir)
    bay = cobra_bay_geometry(schema=schema)
    launch = launch_state(schema=schema, bay=bay)
    launch["waypoint_m"] = list(waypoint())
    launch["station_centre_m"] = list(STATION_CENTRE)
    launch["airframe_glb"] = os.path.relpath(glb, ROOT)
    launch["airframe"] = {"triangles": man["triangles"],
                          "length_m": man["bounds"]["length_m"],
                          "span_x_m": man["bounds"]["span_x_m"]}
    # THE DOCK. Every constant the engine's approach needs, plus the hull's own
    # radius profile so the engine can measure its own clearance against the
    # same function the mesh is built from.
    plan = dock_plan(schema=schema, bay=bay)
    launch["dock"] = dock_block(plan)
    launch["hull_profile"] = hull_profile(schema)
    with open(os.path.join(out_dir, "launch.json"), "w") as f:
        json.dump(launch, f, indent=1)
    vec = vectors(schema)
    vec["guidance_samples"] = guidance_samples(plan)
    vec["attitude_samples"] = attitude_samples(plan)
    with open(os.path.join(out_dir, "vectors.json"), "w") as f:
        json.dump(vec, f, indent=1)

    # The flyable scene's own shot description. `render_godot.sh --shot
    # starfury --no-export` reads this, so the flyable build renders through
    # the same guarded path as everything else -- ICD check, OpenGL-fallback
    # check, shader check, all of it.
    # ABSOLUTE PATHS. Godot resolves a bare relative path against the process
    # working directory, which for `render_godot.sh` is not the repository
    # root, and the failure mode is a scene that renders perfectly with no
    # station in it. `tools/export_scene.py` writes absolute paths into its own
    # `glb` list for the same reason.
    scene = {
        "scene": "res://scenes/starfury.tscn",
        # WHICH BEAT OF THE MISSION THE FRAME IS TAKEN AT. It lives in the shot
        # rather than on the command line because `tools/render_godot.sh`
        # forwards nothing but `--scene-json` and `--out` to a `--no-export`
        # run: anything else it is handed goes to the exporter, which is not
        # running. A flag that silently reaches nobody is worse than no flag.
        "frame": "release",
        "glb": [],                     # the flyable scene loads its own
        "hull_glb": os.path.join(STATION, "generated/scene/exterior/hull.glb"),
        "fury_glb": glb,
        "launch_json": os.path.join(out_dir, "launch.json"),
        "vectors_json": os.path.join(out_dir, "vectors.json"),
        "camera": {"fov": 46.0, "near": 0.5, "far": 200000.0,
                   "eye": list(waypoint()), "target": list(STATION_CENTRE)},
        # THE SAME RIG, AIMED BY THE SAME FORMULAS. Key at the exterior shot's
        # default sun angle; rim opposite it and slightly below, which is what
        # puts an edge on the unlit side; fill mirrored through the camera axis.
        # Copied from `tools/export_scene.build_exterior` as arithmetic rather
        # than as light nodes -- the nodes themselves, with their measured
        # energies and colours, are borrowed live from `scenes/exterior.tscn`
        # by `scripts/starfury.gd`. Only the AIM is a property of the shot.
        "sun_at": list(STATION_CENTRE),
        "sun_from": list(_spherical(20000.0, SUN_ELEV, SUN_AZ, STATION_CENTRE)),
        "rim_from": list(_spherical(20000.0, -10.0, SUN_AZ + 175.0,
                                    STATION_CENTRE)),
        "fill_from": list(_spherical(20000.0, ORBIT[1] + 10.0,
                                     2 * ORBIT[2] - SUN_AZ, STATION_CENTRE)),
    }
    with open(os.path.join(out_dir, "scene.json"), "w") as f:
        json.dump(scene, f, indent=1)
    return launch


def compose_lookback(flight_path, out_png, out_dir=OUT_DIR, res="1280x720"):
    """Assemble the money shot: the fighter's own flown pose, in front of the
    station, through the exterior rig that was calibrated for this framing.

    Everything about the LOOK comes from `scenes/exterior.tscn` and
    `tools/export_scene.py --shot exterior`; the only thing this adds is one
    extra .glb in the list and a camera that came out of a flight rather than
    out of an argument.
    """
    flight = json.load(open(flight_path, encoding="utf-8"))
    # THE LOOK-BACK BEAT, NOT THE LAST ONE. Since the mission grew a dock phase
    # `final` is the craft parked 3 m off the hull with its nose 85 degrees off
    # the station -- a perfectly valid state and the wrong photograph. The
    # fallback keeps an older flight.json composable.
    ship = flight.get("lookback", flight["final"])
    cam = flight["camera"]
    posed = pose_airframe(ship["position"], ship["orientation"], out_dir)

    ext = os.path.join(STATION, "generated", "scene", "exterior")
    # A LEADING SPACE ON A NEGATIVE TRIPLE. argparse reads `-7200,...` as an
    # option flag and dies; every worked example in `tools/export_scene.py`'s
    # own docstring quotes such arguments with a space in front, so that is
    # what is emitted here rather than rediscovered.
    def _trip(v):
        s = ",".join(f"{c:.4f}" for c in v)
        return " " + s if s.startswith("-") else s

    cmd = [sys.executable, os.path.join(ROOT, "tools/export_scene.py"),
           "--shot", "exterior", "--out", out_png,
           "--eye", _trip(cam["eye"]), "--target", _trip(cam["target"]),
           "--fov", str(cam.get("fov", 46.0))]
    subprocess.run(cmd, check=True, cwd=ROOT)
    shot = json.load(open(os.path.join(ext, "scene.json")))
    shot["glb"] = list(shot["glb"]) + [posed]
    shot["out_png"] = out_png
    # A shot whose camera is 60 m from a 10 m object cannot keep the exterior's
    # 1 m near plane: the fighter's nearest boom is inside it. Pulled in to
    # 0.5 m, which is still 18,400x the far plane's 200 km and well inside what
    # a 24-bit depth buffer carries.
    shot["camera"]["near"] = 0.5
    # ITS OWN SHOT DIRECTORY, because `tools/render_godot.sh --shot NAME`
    # resolves `station/generated/scene/NAME/scene.json` and nothing else.
    # Writing it beside the exterior's would overwrite a shot other work is
    # using -- and generated scene directories are exactly the shared artefact
    # CLAUDE.md's "disjoint source files are not disjoint artefacts" is about.
    ldir = os.path.join(STATION, "generated", "scene", "starfury_lookback")
    os.makedirs(ldir, exist_ok=True)
    dst = os.path.join(ldir, "scene.json")
    shot["scene_json"] = dst
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(shot, f, indent=1)
    return dst, posed


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_flight(flight_path, perturb=0.0, quiet=False):
    """Compare what the engine flew against what the tested modules predict.

    THREE INDEPENDENT PREDICTIONS OF ONE NUMBER, and that is the point. The
    engine derives its release velocity by finite-differencing the trajectory
    of a craft riding the rotating bay; `rotating_frame` derives it analytically
    from omega x r; `starfury.launch_from_drum` derives it a third way. If a
    port has the rotation backwards, or the radius wrong, or applies the drum's
    speed at the floor radius instead of the bay's, exactly one of these three
    moves and the disagreement names the fault.

    `perturb` is the negative control: it multiplies the engine's reported exit
    speed before comparing, so a caller can prove the check FAILS on a wrong
    number. A check nobody has seen fail is a check nobody has tested.
    """
    flight = json.load(open(flight_path, encoding="utf-8"))
    predicted = launch_state()
    ok = True
    lines = []

    def row(label, got, want, tol):
        nonlocal ok
        good = abs(got - want) <= tol
        ok = ok and good
        lines.append(f"  {'PASS' if good else 'FAIL'}  {label:<44} "
                     f"engine {got:14.6f}   model {want:14.6f}   "
                     f"d {got - want:+.3e} (tol {tol:g})")

    got = float(flight["release"]["exit_speed_m_s"]) * (1.0 + perturb)
    row("exit speed, engine vs rotating_frame",
        got, predicted["expected_exit_speed_m_s"], 1e-4)
    row("exit speed by finite difference of the ride",
        float(flight["release"]["exit_speed_finite_difference_m_s"]) * (1.0 + perturb),
        predicted["expected_exit_speed_m_s"], 5e-2)
    row("release radius", float(flight["release"]["radius_m"]),
        predicted["bay"]["mouth_radius_m"], 1e-3)
    row("omega used by the engine", float(flight["release"]["omega_rad_s"]),
        predicted["omega_rad_s"], 1e-12)

    # The exit velocity must be TANGENTIAL: a craft at rest in the rotating
    # frame has no radial component at all, and a port that adds one has
    # confused "flung out" with "pushed out".
    v = flight["release"]["exit_velocity_m_s"]
    p = flight["release"]["position_m"]
    radial = (v[0] * p[0] + v[1] * p[1]) / max(1e-9, math.hypot(p[0], p[1]))
    row("radial component of the exit velocity", radial, 0.0, 1e-6)

    lines.append(f"  ..  {'flew':<44} "
                 f"{flight['summary']['range_m']:.0f} m from the station centre "
                 f"in {flight['summary']['elapsed_s']:.1f} s, "
                 f"peak {flight['summary']['peak_speed_m_s']:.1f} m/s")

    # --- THE DOCK -------------------------------------------------------------
    # TWO INDEPENDENT IMPLEMENTATIONS FROM ONE START STATE. The engine flew the
    # approach in GDScript; `docking.fly` flies it again in Python from the
    # look-back state the engine recorded, and the two must land on the same
    # contact. Anything else means the port drifted somewhere the open-loop
    # samples do not reach -- the stage machine, the commit gate, the ramp.
    dock = flight.get("dock")
    if dock is None:
        lines.append("  FAIL  the flight has no dock phase")
        ok = False
    else:
        docking = _docking()
        plan = dock_plan()
        look = flight.get("lookback", flight["final"])
        ship = Starfury()
        ship.position = tuple(look["position"])
        ship.velocity = tuple(look["velocity"])
        q = look["orientation"]
        ship.orientation = (q[0], q[1], q[2], q[3])
        mine = docking.fly(plan, ship, t0=float(look["t_s"]), max_s=300.0)
        got = bool(dock["docked"]) and not perturb
        lines.append(f"  {'PASS' if got else 'FAIL'}  "
                     f"{'the engine docked':<44} "
                     f"{dock['reason'] or 'contact'}")
        ok = ok and got
        lines.append(f"  {'PASS' if mine.docked else 'FAIL'}  "
                     f"{'and station/physics/docking.py agrees':<44} "
                     f"python {mine.elapsed_s:.2f} s, engine "
                     f"{float(dock['elapsed_s']):.2f} s")
        ok = ok and mine.docked
        # THE TOLERANCE HERE IS NOT THE VECTOR TOLERANCE, AND THE DIFFERENCE IS
        # WORTH THE PARAGRAPH. `--selftest` and `--dock-selftest` compare the
        # two implementations OPEN LOOP at 1e-9 and measure 5e-14, which is the
        # bit-level agreement that says "same algorithm". These rows compare the
        # end of an 18,751-step CLOSED LOOP, and doubles do not survive that
        # untouched: written at 1e-9 these rows failed at 3.8e-9 (closing rate),
        # 2.9e-9 (slip) and 4.6e-8 (peak accel, which is a max over the run, so
        # a one-ulp difference changes WHICH step wins). None of that is drift.
        #
        # 1e-5 is four orders below the 1% perturbation the control applies
        # (0.0146 on the closing rate) and three orders above the observed
        # round-off, so it can still fail for a real difference and cannot fail
        # for arithmetic. The measured worst is printed below either way, so the
        # number is visible rather than swallowed by the band.
        loop_tol = 1e-5
        for label, a, b, tol in (
                ("dock time, engine vs docking.py",
                 float(dock["elapsed_s"]) * (1.0 + perturb), mine.elapsed_s,
                 loop_tol),
                ("closing rate at contact",
                 float(dock["closing_rate_m_s"]) * (1.0 + perturb),
                 mine.closing_rate_m_s, loop_tol),
                ("lateral slip at contact",
                 float(dock["lateral_slip_m_s"]) * (1.0 + perturb),
                 mine.lateral_slip_m_s, loop_tol),
                ("lateral offset at contact",
                 float(dock["lateral_offset_m"]) * (1.0 + perturb),
                 mine.lateral_offset_m, loop_tol),
                ("phase error at contact, deg",
                 float(dock["phase_error_deg"]) * (1.0 + perturb),
                 mine.phase_error_deg, loop_tol),
                ("peak dock accel as a fraction of max",
                 float(dock["dock_peak_accel_fraction"]) * (1.0 + perturb),
                 mine.dock_peak_accel_fraction, loop_tol),
                # THE A/B AGAINST THE LAUNCH: same bay, same omega, backwards.
                # A docked craft co-rotates, so its tangential speed AT THE
                # BAY'S OWN RADIUS is the speed the launch releases at.
                ("dock contact speed == launch release speed",
                 float(dock["tangential_at_bay_radius_m_s"]) * (1.0 + perturb),
                 predicted["expected_exit_speed_m_s"], 1e-2)):
            row(label, a, b, tol)
        safe = bool(dock["contact_safe"]) and not perturb
        lines.append(f"  {'PASS' if safe else 'FAIL'}  "
                     f"{'contact is inside the safety envelope':<44} "
                     f"closing {float(dock['closing_rate_m_s']):.3f} m/s, slip "
                     f"{float(dock['lateral_slip_m_s']):.4f} m/s, misalign "
                     f"{float(dock['misalignment_deg']):.2f} deg")
        ok = ok and safe
        clear = float(dock["hull_clearance_m"]) > 0.0 and not perturb
        lines.append(f"  {'PASS' if clear else 'FAIL'}  "
                     f"{'the approach never touched the hull':<44} "
                     f"tightest clearance "
                     f"{float(dock['hull_clearance_m']):.1f} m")
        ok = ok and clear
        lines.append(
            f"  ..  {'stages':<44} "
            + ", ".join(f"{k} {v:.1f} s" for k, v in dock["stage_s"].items()))
        drift = max(
            abs(float(dock["closing_rate_m_s"]) - mine.closing_rate_m_s),
            abs(float(dock["lateral_slip_m_s"]) - mine.lateral_slip_m_s),
            abs(float(dock["dock_peak_accel_fraction"])
                - mine.dock_peak_accel_fraction))
        lines.append(
            f"  ..  {'closed-loop round-off over ' + str(dock['steps']) + ' steps':<44} "
            f"worst |engine - python| = {drift:.3e} "
            f"(open loop the same law agrees to 5e-14)")
    if not quiet:
        print("\n".join(lines))
    return ok


def docking_envelope(schema=None, bay=None):
    """What it costs a Starfury to hold formation off a rotating cobra bay.

    THIS IS A NEGATIVE RESULT AND IT IS THE USEFUL KIND. Two guidance laws were
    written against `station/physics/docking.py`'s own `DockingBay` and neither
    converged: velocity matching onto the moving approach point settled into a
    stable limit cycle 690 m out at 129 m/s relative, with the throttle pinned
    at 1.00 the whole time. Pinned at 1.00 is the tell. The craft was not being
    flown badly; it was out of thrust.

    A body holding station at radius R off a hub turning at omega is being
    accelerated inward at omega^2 R for as long as it stays there. It is not a
    manoeuvre with a delta-v -- it is a CONTINUOUS acceleration, and the numbers
    below say what fraction of the airframe's total it eats. Beyond
    `amax / omega^2` there is no fraction: the craft cannot follow the circle at
    all, whatever it does.

    Everything here comes out of the tested modules -- `rotating_frame` for the
    frame, `docking.DockingBay` and `docking.spin_match_velocity` for the bay,
    `starfury.max_linear_accel` for the airframe. `docking.py` had no importer
    outside its own tests before this.
    """
    sys.path.insert(0, os.path.join(STATION, "physics"))
    import docking  # noqa: E402  -- its first importer outside its own test

    if schema is None:
        schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    if bay is None:
        bay = cobra_bay_geometry(schema=schema)
    drum = from_schema(schema)
    ship = Starfury()
    amax = ship.max_linear_accel()
    w2 = drum.omega * drum.omega
    r = bay["mouth_radius_m"]

    d = docking.DockingBay(drum, r, bay["z_m"], bay["phase_rad"])
    rows = []
    for standoff in (0.0, 25.0, 50.0, 100.0, 200.0, 227.0, 300.0):
        R = r + standoff
        need = w2 * R
        v = docking.spin_match_velocity(d, 0.0, standoff)
        rows.append({
            "standoff_m": standoff,
            "radius_m": R,
            "station_keeping_speed_m_s": norm(v),
            "centripetal_accel_m_s2": need,
            "fraction_of_max_thrust": need / amax,
            "feasible": need < amax,
        })
    return {
        "max_linear_accel_m_s2": amax,
        "omega_rad_s": drum.omega,
        "bay_radius_m": r,
        # amax = omega^2 R at the limit. Beyond it the craft cannot hold the
        # circle even with every thruster open and nothing left over to steer.
        "max_formation_radius_m": amax / w2,
        "max_standoff_m": amax / w2 - r,
        "habitat_floor_cost_m_s2": w2 * drum.floor_radius,
        "rows": rows,
        "axial_alternative_m_s": docking.axial_approach_is_trivial(drum, 0.0),
    }


# ---------------------------------------------------------------------------
# The dock -- the launch run backwards
# ---------------------------------------------------------------------------

# How finely the hull's own radius profile is written into launch.json so the
# engine can measure its own clearance. 8,047 m over 400 samples is 20.1 m a
# sample, which is finer than the profile's own control points. INV-402.
HULL_SAMPLES = 400


def _docking():
    sys.path.insert(0, os.path.join(STATION, "physics"))
    import docking  # noqa: E402
    return docking


def hull_profile(schema=None):
    """The station's radius against z, sampled, so the engine can carry it.

    THE SAME `components.radius_at` THE HULL MESH IS BUILT FROM. Hard rule 4:
    a craft that measures its clearance against a second description of the
    hull is a craft that can fly through the first one.
    """
    # THE PROFILE'S OWN EXTENT, not the schema's stated 8,047 m. They agree, and
    # taking it from the profile means the sampled table cannot end before the
    # mesh does if the two ever stop agreeing.
    prof = generate_hull.load()[1]["profile"]
    z0 = min(p["z_m"] for p in prof)
    z1 = max(p["z_m"] for p in prof)
    step = (z1 - z0) / (HULL_SAMPLES - 1)
    return {"z0": z0, "step": step,
            "radii": [components.radius_at(prof, z0 + i * step)
                      for i in range(HULL_SAMPLES)],
            "source": "station/components.radius_at(generate_hull.load() "
                      "profile) -- the function the hull mesh is built from"}


def dock_plan(schema=None, bay=None):
    """The approach plan for the measured cobra bay, with the real hull.

    Everything the plan needs comes from somewhere that already exists: the bay
    off `hull.obj`, the spin off `rotating_frame`, the thrust off the flight
    model, the craft's half-length off `starfury_geometry`'s own manifest, and
    the hull radius off the function `generate_hull` builds the mesh with.
    Nothing in the plan is written down here.
    """
    docking = _docking()
    if schema is None:
        schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    if bay is None:
        bay = cobra_bay_geometry(schema=schema)
    drum = from_schema(schema)
    amax = Starfury().max_linear_accel()
    half = 0.5 * starfury_geometry.manifest(starfury_geometry.build())[
        "bounds"]["length_m"]
    d = docking.DockingBay(drum, bay["mouth_radius_m"], bay["z_m"],
                           bay["phase_rad"])
    plan = docking.plan_approach(d, amax, craft_half_length_m=half)
    prof = generate_hull.load()[1]["profile"]
    plan.hull_radius_at = lambda z: components.radius_at(prof, z)
    return plan


def dock_block(plan):
    """Every number the engine needs to fly the same approach.

    Written into `launch.json` rather than restated in GDScript for the reason
    the launch block is: a constant duplicated across a language boundary is a
    constant that drifts. What IS duplicated on purpose is the law itself, and
    `vectors.json`'s guidance samples are what catch that.
    """
    docking = _docking()
    return {
        # The bay again, inside the dock block, so the port reads ONE dictionary
        # and cannot pick up the bay from one place and omega from another.
        "omega": plan.omega,
        "bay_radius": plan.bay.radius,
        "bay_z": plan.bay.z,
        "bay_phase": plan.bay.phase,
        "period_s": plan.bay.drum.period,
        "max_accel_m_s2": plan.max_accel,
        "ceiling_radius_m": plan.ceiling_radius_m,
        "max_standoff_m": plan.ceiling_radius_m - plan.bay.radius,
        "standoff_m": plan.standoff_m,
        "hold_radius_m": plan.hold_radius_m,
        "hold_cost_m_s2": plan.hold_cost_m_s2,
        "control_reserve": plan.control_reserve,
        "authority_m_s2": plan.authority_m_s2,
        "closing_rate_m_s": plan.closing_rate_m_s,
        "capture_range_m": plan.capture_range_m,
        "capture_speed_m_s": plan.capture_speed_m_s,
        "vel_gain": plan.vel_gain,
        "cruise_vmax_m_s": plan.cruise_vmax_m_s,
        "brachistochrone_derate": plan.brachistochrone_derate,
        "terminal_taper": plan.terminal_taper,
        "contact_standoff_m": plan.contact_standoff_m,
        "commit_lead_rad": docking.commit_lead_angle(plan),
        "att_kp": docking.ATT_KP, "att_kd": docking.ATT_KD,
        "thrust_gate_deg": docking.THRUST_GATE_DEG,
        "derivation": ("station/physics/docking.plan_approach -- the standoff "
                       "from the control reserve, the closing rate from "
                       "contact_is_safe's own buffer limit, the one gain from "
                       "the authority budget, the commit lead from the "
                       "spin-up time"),
    }


def guidance_samples(plan, n=24):
    """The law evaluated at fixed states, for the GDScript port to reproduce.

    OPEN LOOP, AND THAT IS THE POINT. The engine flies the same approach in a
    feedback loop, and a feedback loop hides a mis-ported gain by correcting for
    it -- the trajectory comes out nearly the same and the law is wrong. These
    samples pin the law itself: one state in, one acceleration out, compared
    component by component at 1e-9. The states are spread over every stage, both
    sides of the capture, and both settings of `phase_match`, so a port that
    drops the Coriolis term or the target-velocity feedforward cannot pass.
    """
    docking = _docking()
    out = []
    rng_t = [0.0, 4.7, 11.3, 22.9, 31.4, 47.0]
    for i in range(n):
        t = rng_t[i % len(rng_t)] + 7.0 * (i // len(rng_t))
        stage = ["return", "loiter", "run_in", "terminal"][i % 4]
        standoff = [plan.standoff_m, plan.standoff_m, plan.standoff_m,
                    plan.contact_standoff_m + 9.0][i % 4]
        ang = plan.bay.angle_at(t) + 0.37 * (i - n / 2.0) / n
        rad = plan.hold_radius_m + 40.0 * math.sin(0.9 * i) + 3.0 * i
        pos = (rad * math.cos(ang), rad * math.sin(ang),
               plan.bay.z + 30.0 * math.cos(1.7 * i))
        vel = (12.0 * math.sin(0.5 * i), plan.omega * rad * 0.8,
               2.0 * math.cos(0.3 * i))
        loiter = docking.loiter_point(plan, pos)
        for pm in (True, False):
            tgt = docking.stage_target(plan, t, stage, standoff, loiter)
            cmd, d, dv = docking.dock_command(plan, t, pos, vel, standoff, 0.0,
                                              pm, tgt)
            out.append({"t": t, "stage": stage, "standoff_m": standoff,
                        "phase_match": pm, "position": list(pos),
                        "velocity": list(vel), "loiter": list(loiter),
                        "accel": list(cmd), "range_m": d,
                        "velocity_error_m_s": dv})
    return out


def attitude_samples(plan, n=16):
    """`docking.attitude_command` at fixed states, throttle by throttle.

    The attitude loop is the other half of the port and it is where the one
    number that makes docking work lives -- the demand's own rotation rate, fed
    forward. A port that drops it still flies, badly, with a 26 degree standing
    error, and no trajectory comparison at engine tolerances would name the
    cause. This does.
    """
    docking = _docking()
    out = []
    for i in range(n):
        ship = Starfury()
        a = 0.41 * i
        ship.orientation = quat_from_basis(
            (math.cos(a), math.sin(a), 0.3 * math.sin(0.7 * i)),
            (0.0, 0.0, 1.0))
        ship.angular_velocity = (0.05 * math.sin(i), 0.12 * math.cos(0.6 * i),
                                 0.03 * i / n)
        aim = unit((math.cos(a + 0.25), math.sin(a + 0.25), 0.2))
        ff = (0.0, 0.0, plan.omega) if i % 2 else (0.01 * i, 0.0, 0.0)
        thr = 0.15 + 0.05 * (i % 8)
        th, ang = docking.attitude_command(ship, aim, ff, thr)
        out.append({"orientation": list(ship.orientation),
                    "angular_velocity": list(ship.angular_velocity),
                    "aim": list(aim), "omega_ff": list(ff), "throttle": thr,
                    "throttles": th, "pointing_error_deg": ang})
    return out


def dock_gate(phases=12, quiet=False):
    """The whole dock, at the real bay, over a full rotation, with its controls.

    Reports a DENOMINATOR. One dock against a rotating target is an existence
    proof and this project does not accept those: the bay's phase when the
    approach starts is the variable the problem turns on, and a law can dock
    from the phase it was written against and fly into the hull from the one 90
    degrees away -- which is exactly what the first version of the commit gate
    did, on 1 of 12.
    """
    docking = _docking()
    schema = yaml.safe_load(open(os.path.join(STATION, "schema/station.yaml")))
    bay = cobra_bay_geometry(schema=schema)
    plan = dock_plan(schema=schema, bay=bay)
    launch = launch_state(schema=schema, bay=bay)
    ok = True
    out = []

    def row(name, good, detail=""):
        nonlocal ok
        ok = ok and good
        out.append(f"  {'PASS' if good else 'FAIL'}  {name:<52}"
                   + (f"  {detail}" if detail else ""))

    out.append("--- the Starfury docks in the measured cobra bay ---")
    out.append(f"  bay r {plan.bay.radius:.2f} m at z {plan.bay.z:.1f} m; "
               f"omega {plan.omega:.9f} rad/s; airframe {plan.max_accel:.2f} "
               f"m/s^2 max")
    out.append(f"  ceiling {plan.ceiling_radius_m:.1f} m of radius = "
               f"{plan.ceiling_radius_m - plan.bay.radius:.1f} m of standoff; "
               f"plan holds at {plan.standoff_m:.1f} m "
               f"({plan.hold_cost_m_s2:.2f} m/s^2, "
               f"{plan.control_reserve:.1%} in hand)")
    out.append(f"  commit lead {math.degrees(docking.commit_lead_angle(plan)):.1f} "
               f"deg; closing {plan.closing_rate_m_s:.2f} m/s; contact standoff "
               f"{plan.contact_standoff_m:.2f} m (the airframe's half-length)")

    # THE START STATE IS THE MISSION'S OWN LOOK-BACK POINT, so this gate flies
    # the leg the engine flies rather than a convenient one.
    start = {"t0": 0.0, "position": waypoint(), "velocity": (0.0, 0.0, 0.0),
             "orientation": (1.0, 0.0, 0.0, 0.0)}
    rows = docking.sweep(plan, Starfury, start, phases=phases)
    docked = [r for _t, _a, r in rows if r.docked]
    for _t, ang, r in rows:
        out.append(
            f"    bay at {ang:6.1f} deg: "
            + (f"DOCK {r.elapsed_s:6.1f} s (return {r.return_s:5.1f} loiter "
               f"{r.loiter_s:5.1f} run-in {r.run_in_s:5.1f} close "
               f"{r.terminal_s:5.1f} settle {r.settle_s:4.2f})  closing "
               f"{r.closing_rate_m_s:5.3f} m/s  slip {r.lateral_slip_m_s:6.4f} "
               f"m/s  lateral {r.lateral_offset_m:5.2f} m  phase "
               f"{r.phase_error_deg:+6.3f} deg  peak "
               f"{r.dock_peak_accel_fraction:5.1%}  hull +"
               f"{r.hull_clearance_m:.0f} m"
               if r.docked else f"NO DOCK -- {r.reason}"))
    row("every start phase over one rotation docks", len(docked) == len(rows),
        f"{len(docked)} of {len(rows)}")
    if not docked:
        print("\n".join(out))
        return False, rows, plan
    worst = max(r.dock_peak_accel_fraction for r in docked)
    row("no dock asks the airframe for more than it has", worst <= 1.0,
        f"peak {worst:.1%} of {plan.max_accel:.2f} m/s^2")
    row("no dock touches the hull",
        all(r.hull_clearance_m > 0.0 for r in docked),
        f"tightest clearance {min(r.hull_clearance_m for r in docked):.1f} m")
    row("every contact is inside the safety envelope",
        all(r.contact_safe for r in docked),
        f"worst closing {max(r.closing_rate_m_s for r in docked):.3f} m/s, "
        f"slip {max(r.lateral_slip_m_s for r in docked):.4f} m/s, misalign "
        f"{max(r.misalignment_deg for r in docked):.2f} deg")

    # --- THE A/B AGAINST THE LAUNCH -- the same bay, the same omega, backwards
    # A docked craft is co-rotating with the station, so its tangential speed at
    # the BAY'S OWN RADIUS must be the speed the launch releases at. Same bay,
    # same omega, opposite direction of travel.
    ref = docking.contact_report
    worst_ab = 0.0
    for _t, _a, r in rows:
        if not r.docked:
            continue
        tang = math.sqrt(max(0.0, r.contact_speed_m_s ** 2
                             - r.radial_velocity_m_s ** 2))
        at_bay = tang * plan.bay.radius / r.contact_radius_m
        worst_ab = max(worst_ab, abs(at_bay - launch["expected_exit_speed_m_s"]))
    row("the dock's contact velocity IS the launch's release velocity",
        worst_ab < 1e-2,
        f"worst |dock - launch| = {worst_ab:.2e} m/s against "
        f"{launch['expected_exit_speed_m_s']:.4f} m/s")

    # --- NEGATIVE CONTROL 1: the phase-matching term nulled ------------------
    bad = docking.sweep(plan, Starfury, start, phases=4, phase_match=False)
    misses = sorted(r.miss_m for _t, _a, r in bad)
    row("CONTROL: null the phase match and nothing docks",
        not any(r.docked for _t, _a, r in bad),
        f"misses {', '.join(f'{m:.0f}' for m in misses)} m against "
        f"{sum(r.miss_m for r in docked) / len(docked):.2f} m when matched")

    # --- NEGATIVE CONTROL 2: a standoff past the ceiling ---------------------
    for demand, why in ((300.0, "past the 227.8 m ceiling"),
                        (227.0, "inside it, with no authority left")):
        try:
            docking.plan_approach(plan.bay, plan.max_accel, standoff=demand)
            row(f"CONTROL: {demand:.0f} m of standoff is refused", False,
                "IT WAS ACCEPTED -- the envelope is not enforced")
        except docking.InfeasibleApproach as e:
            row(f"CONTROL: {demand:.0f} m of standoff ({why}) is refused", True,
                str(e)[:110])

    # --- THE FINDING ABOUT contact_is_safe -----------------------------------
    r0 = docked[0]
    out.append(
        f"  ..    `contact_is_safe` says {'SAFE' if r0.naive_safe else 'UNSAFE'}"
        f" on the same contact: its lateral term reads "
        f"{r0.naive_lateral_m_s:.4f} m/s against its own 0.5 limit, because it "
        f"measures against")
    out.append(
        f"        the BAY's velocity and the craft's centre stands off by its "
        f"half-length. Referenced to the rotating structure the slip is "
        f"{r0.lateral_slip_m_s:.4f} m/s. See docking.contact_report.")

    if not quiet:
        print("\n".join(out))
        print("DOCK GATE: " + ("PASS" if ok else "FAIL"))
    return ok, rows, plan


def godot_binary():
    """The same search `station/walkable.py` does, and the same message."""
    for c in [os.environ.get("GODOT", ""),
              "/home/user/godot-build/godot-4.4-stable/bin/"
              "godot.linuxbsd.editor.double.x86_64"]:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    import glob
    for c in glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*.double.*"):
        if os.access(c, os.X_OK):
            return c
    return None


def gate(out_dir=OUT_DIR):
    """Everything that can be checked without a render, in one command.

    The port against its source, both negative controls, the flight, and the
    launch against `rotating_frame`. Not wired into CI: session 4d's ruling says
    keep the existing gates green and do not GROW them, and this is a test of
    one port rather than a new scored dimension. It is here so that the claim
    "the Starfury flies and its physics is the tested physics" is one command
    away from being re-checked rather than a paragraph in a commit message.
    """
    godot = godot_binary()
    if godot is None:
        raise SystemExit("no double-precision Godot -- bash tools/build_godot.sh")
    scene = os.path.join(out_dir, "scene.json")
    base = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
            "res://scenes/starfury.tscn", "--", f"--scene-json={scene}"]

    def run(extra, label):
        r = subprocess.run(base + extra, capture_output=True, text=True,
                           timeout=600)
        keep = [ln for ln in r.stdout.splitlines()
                if ln.startswith(("  ", "---", "CONTROL", "NEGATIVE",
                                  "PILOT", "starfury:")) or " of " in ln]
        print(f"--- {label} (exit {r.returncode}) ---")
        print("\n".join(keep))
        return r.returncode

    ok = run(["--selftest"], "the port against station/physics/starfury.py") == 0
    for d in ("aero", "nogyro"):
        # INVERTED: the drifted port MUST fail. `_selftest` already inverts its
        # own verdict, so a zero here means the control fired.
        ok = ok and run([f"--selftest", f"--drift={d}"],
                        f"negative control drift={d}") == 0
    ok = ok and run(["--dock-selftest"],
                    "the docking law against station/physics/docking.py") == 0
    for d in ("nocoriolis", "nophase", "noattff"):
        ok = ok and run(["--dock-selftest", f"--drift={d}"],
                        f"negative control drift={d}") == 0
    ok = ok and run(["--pilot-test"],
                    "the pilot's controls, from a scripted key sequence") == 0
    ok = ok and run(["--mission"], "the mission, launch to dock") == 0
    print("--- the launch against rotating_frame.py ---")
    ok = check_flight(os.path.join(out_dir, "flight.json")) and ok
    bad = check_flight(os.path.join(out_dir, "flight.json"), perturb=0.01,
                       quiet=True)
    print("  control " + ("FIRES (good)" if not bad else "DID NOT FIRE"))
    ok = ok and not bad
    print("\nSTARFURY GATE: " + ("PASS" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="build, replay the vectors in the engine, fire both "
                         "negative controls, fly the mission and check the "
                         "launch against rotating_frame.py")
    ap.add_argument("--build", action="store_true",
                    help="write the airframe, launch.json, vectors.json and "
                         "the flyable scene's scene.json")
    ap.add_argument("--report", action="store_true",
                    help="print the launch the engine has to reproduce")
    ap.add_argument("--dock-gate", action="store_true",
                    help="fly the dock at the measured cobra bay from every "
                         "phase of one rotation, with both negative controls "
                         "and the A/B against the launch")
    ap.add_argument("--phases", type=int, default=12,
                    help="start phases the dock gate sweeps over one rotation")
    ap.add_argument("--docking-envelope", action="store_true",
                    help="what holding formation off a rotating cobra bay "
                         "costs a Starfury, and where it stops being possible")
    ap.add_argument("--check", metavar="FLIGHT_JSON",
                    help="compare an engine flight against the tested modules")
    ap.add_argument("--compose", metavar="FLIGHT_JSON",
                    help="assemble the look-back shot from an engine flight")
    ap.add_argument("--out", default="docs/engine-4e-fury-lookback.png")
    ap.add_argument("--res", default="1280x720")
    a = ap.parse_args()
    did = False

    if a.gate:
        did = True
        a.build = True

    if a.build:
        did = True
        launch = write_bundle()
        b = launch["bay"]
        print(f"cobra bay measured off the hull mesh: r {b['mouth_radius_m']:.2f} m "
              f"at z {b['z_m']:.1f} m, phase {math.degrees(b['phase_rad']):+.2f} deg")
        print(f"  protrusion: measured {b['measured_protrusion_m']:.1f} m vs "
              f"schema {b['schema_protrusion_m']} m")
        if abs(b["measured_protrusion_m"] - b["schema_protrusion_m"]) > 8.0:
            raise SystemExit(
                "the well liner's mouth is not where the schema says the bay "
                "stands proud -- one of the two is wrong and the launch point "
                "is not trustworthy until it is known which")
        print(f"exit velocity per rotating_frame: "
              f"{launch['expected_exit_speed_m_s']:.4f} m/s "
              f"({launch['expected_exit_velocity_m_s']})")
        # THE BAY IS NOT THE FLOOR, and this line exists because reaching for
        # `drum.floor_speed` is the obvious mistake: it is the one tangential
        # speed this project has written down (52.2 m/s, STATE.md) and it is
        # the speed of a DIFFERENT radius. The bays stand outboard of the
        # habitat floor, so they are going faster.
        d = launch["expected_exit_speed_m_s"] - launch["habitat_floor_speed_m_s"]
        print(f"  the habitat FLOOR does {launch['habitat_floor_speed_m_s']:.2f} m/s "
              f"at r {launch['habitat_floor_radius_m']} m -- the bay is "
              f"{b['mouth_radius_m'] - launch['habitat_floor_radius_m']:.1f} m further "
              f"OUT, so it is faster, and using the floor's number would be wrong "
              f"by {-d:+.2f} m/s")
        print(f"airframe: {launch['airframe']['triangles']} triangles, "
              f"{launch['airframe']['length_m']} m long")
        print(f"wrote {os.path.relpath(OUT_DIR, ROOT)}/"
              "{starfury.glb,launch.json,vectors.json,scene.json}")

    if a.gate:
        raise SystemExit(0 if gate() else 1)

    if a.dock_gate:
        did = True
        ok, _rows, _plan = dock_gate(phases=a.phases)
        raise SystemExit(0 if ok else 1)

    if a.docking_envelope:
        did = True
        e = docking_envelope()
        print(f"Starfury max linear accel      {e['max_linear_accel_m_s2']:8.2f} m/s^2")
        print(f"cobra bay radius               {e['bay_radius_m']:8.2f} m")
        print(f"holding station at the habitat FLOOR costs "
              f"{e['habitat_floor_cost_m_s2']:.2f} m/s^2 -- which is 1.000 g, "
              f"by construction, because that is what the spin is set to make")
        print()
        print(" standoff   radius   station-keeping   centripetal   "
              "fraction of   can a")
        print("      (m)      (m)       speed (m/s)      (m/s^2)     "
              "max thrust   Starfury?")
        for r in e["rows"]:
            print(f" {r['standoff_m']:8.0f} {r['radius_m']:8.1f} "
                  f"{r['station_keeping_speed_m_s']:17.2f} "
                  f"{r['centripetal_accel_m_s2']:13.2f} "
                  f"{r['fraction_of_max_thrust']:14.1%}   "
                  f"{'yes' if r['feasible'] else 'NO'}")
        print()
        print(f"THE CEILING: {e['max_formation_radius_m']:.1f} m of radius, i.e. "
              f"{e['max_standoff_m']:.1f} m of standoff. Beyond it omega^2 R "
              f"exceeds the airframe's")
        print("maximum and no guidance law helps -- the craft cannot follow the "
              "circle at all.")
        print(f"On the spin axis the tangential speed to match is "
              f"{e['axial_alternative_m_s']:.1f} m/s, which is why "
              f"docking.py says")
        print("the forward docking sphere exists.")

    if a.report:
        did = True
        print(json.dumps(launch_state(), indent=1))

    if a.check:
        did = True
        print("--- the engine's launch against the tested modules ---")
        ok = check_flight(a.check)
        print("--- negative control: the same check on a 1% wrong exit speed ---")
        bad = check_flight(a.check, perturb=0.01, quiet=True)
        print("  control " + ("FIRES (good)" if not bad else
                              "DID NOT FIRE -- the check cannot fail"))
        if bad:
            raise SystemExit("the launch check passed a number known to be wrong")
        if not ok:
            raise SystemExit("engine flight does not match the flight model")
        print("launch verified")

    if a.compose:
        did = True
        dst, posed = compose_lookback(a.compose, a.out, res=a.res)
        print(f"shot: {os.path.relpath(dst, ROOT)}")
        print(f"posed airframe: {os.path.relpath(posed, ROOT)}")

    if not did:
        ap.print_help()


if __name__ == "__main__":
    main()
