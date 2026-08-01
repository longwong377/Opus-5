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
                        with the full state recorded at checkpoints. The
                        GDScript port replays these and must land on the same
                        numbers. A port that drifts from its tested source is
                        the defect this project keeps finding.
  * `scene.json`     -- a shot `tools/render_godot.sh --shot starfury` can render

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
    with open(obj_path) as f:
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
    with open(os.path.join(out_dir, "launch.json"), "w") as f:
        json.dump(launch, f, indent=1)
    with open(os.path.join(out_dir, "vectors.json"), "w") as f:
        json.dump(vectors(schema), f, indent=1)

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
    flight = json.load(open(flight_path))
    ship = flight["final"]
    cam = flight["camera"]
    posed = pose_airframe(ship["position"], ship["orientation"], out_dir)

    ext = os.path.join(STATION, "generated", "scene", "exterior")
    cmd = [sys.executable, os.path.join(ROOT, "tools/export_scene.py"),
           "--shot", "exterior", "--res", res, "--out", out_png,
           "--eye", ",".join(f"{c:.4f}" for c in cam["eye"]),
           "--target", ",".join(f"{c:.4f}" for c in cam["target"]),
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
    dst = os.path.join(out_dir, "lookback.json")
    shot["scene_json"] = dst
    with open(dst, "w") as f:
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
    flight = json.load(open(flight_path))
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
    if not quiet:
        print("\n".join(lines))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true",
                    help="write the airframe, launch.json, vectors.json and "
                         "the flyable scene's scene.json")
    ap.add_argument("--report", action="store_true",
                    help="print the launch the engine has to reproduce")
    ap.add_argument("--check", metavar="FLIGHT_JSON",
                    help="compare an engine flight against the tested modules")
    ap.add_argument("--compose", metavar="FLIGHT_JSON",
                    help="assemble the look-back shot from an engine flight")
    ap.add_argument("--out", default="docs/engine-4e-fury-lookback.png")
    ap.add_argument("--res", default="1280x720")
    a = ap.parse_args()
    did = False

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
