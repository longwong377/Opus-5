#!/usr/bin/env python3
"""Assemble a render SHOT: geometry, lights and camera, for the Godot renderer.

Why this exists as a separate step. The generators in `station/` each build one
subsystem and none of them knows about the others; the Godot scene files carry
lighting and environment and should not carry a list of which subsystems are in
frame. This is the join: it decides what geometry a named shot contains, where
the camera stands, and where the drum's light runs put their light sources, and
writes all of it as one `scene.json` the engine reads at startup.

Three things it deliberately does NOT do:

* It does not regenerate geometry. `station/generated/*.obj` is whatever the
  generators last wrote, and re-running them here would fight any other process
  mid-edit. `tools/build_and_render.sh` regenerates; this consumes.
* It does not choose materials. Those live in the `.tscn` (see
  `godot/materials/README.md`), because a material is a look and a look belongs
  with the lighting it was judged under. What it DOES do is assert that every
  group it emits has a rule, so nothing lands on the fallback by accident.
* It does not place lights by hand. The drum's illumination is the light runs
  on the guideway trusses (authority 1: `Babylon_5_2-22_34b.jpg` shows the
  tubes alongside the truss, `33a` the fixtures on its underside), so the light
  positions are derived from `interior.guideway_truss`'s own constants. A
  hand-placed light would drift the moment the truss moved.

Usage:

    python3 tools/export_scene.py --shot exterior --orbit 9200,18,214
    python3 tools/export_scene.py --shot exterior --orbit 9200,18,214 \
        --lighting night                               # the anti-sun side
    python3 tools/export_scene.py --shot drum --stand 20,4700 --look 20,6300
    python3 tools/export_scene.py --shot deck --at docking_bays
    python3 tools/export_scene.py                      # runs the self-test
    python3 tools/export_scene.py --gate-exterior      # measures the frames

FOUR SHOTS, AND ONLY ONE OF THEM IS THE BUILD. `interior` renders ONE ROOM in
its own local frame with a camera this file invents; `deck` renders what
`station/deck.py` assembles and `station/walkable.py` walks -- a ring corridor
with its rooms, doors, vestibules, furniture and inhabitants, at its real
radius seven kilometres down the station, through the camera
`godot/scripts/player.gd` ships. Use `interior` to judge a room and `deck`
to judge the game.

A WARNING ABOUT `--no-export`, learned the hard way this session. That flag on
tools/render_godot.sh reuses whatever is in station/generated/scene/<shot>/,
and that path is SHARED: another agent exporting a shot of their own replaces
it underneath you. Two renders that were supposed to differ only in an SSAO
flag came back as two entirely different framings, and the first reading of it
was "the renderer is non-deterministic". It is not -- re-exported properly, the
same shot renders byte-identical. Export every time unless nothing else is
running.
"""
import argparse
import math
import json
import math
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION = os.path.join(ROOT, "station")
GENERATED = os.path.join(STATION, "generated")
SCENE_DIR = os.path.join(GENERATED, "scene")

sys.path.insert(0, STATION)

import interior as it              # noqa: E402
import drum_ground as dg           # noqa: E402
import tram                        # noqa: E402
import garden as gd                # noqa: E402
import core_tube as ct             # noqa: E402


# ---------------------------------------------------------------------------
# Light runs
# ---------------------------------------------------------------------------

# Colour of the habitat's light runs, measured off `Babylon_5_2-22_34b.jpg`:
# the tube cores clip at (1.000, 1.000, 0.94-0.97) and their unclipped mean is
# (0.861, 0.866, 0.755). Both readings put red and green level with each other
# and blue 5-12% down, i.e. a warm white with no red cast -- a fluorescent-ish
# source rather than tungsten. Recorded as measured rather than chosen.
LAMP_COLOUR = (1.0, 0.99, 0.93)
# The interior fitting's own colour, from materials.py's light_downlight, which
# is the measured warm practical the corridor frames show. Imported would be
# better than restated; it is restated because export_scene must run without
# importing the material library, and the value is asserted against
# `materials.BY_NAME["light_downlight"].emission` in the self-test below.
# (removed -- see fixture_lights: each fitting emits its OWN measured colour)

# Total light energy contributed by ONE light run, shared out over however many
# omnis are used to sample it. A run is a 2.6 km line source and an omni is a
# point; the sampling density is a cost decision and must not be a look
# decision, so energy is normalised by count. Without this, doubling
# --lights-per-run doubles the brightness of the drum and every judgement made
# about the previous render is void.
RUN_ENERGY = 24.0

# THE DRUM'S EXPOSURE, measured the same way every interior room's is: render
# the shot, measure it and its reference frame with tools/measure_frame.py, and
# scale until it sits at the multiple of its reference the corridor sits at.
#
# It was the last lit volume in the project with no measured exposure. The drum
# rig has been rendering since session 2j and RUN_ENERGY was set by eye; at
# gain 1.00 the standard drum shot reads x1.03 of
# reference/03-sector-blue/Babylon_5_2-22_34b.jpg against the x1.40 target --
# under-exposed by a third. The response is very nearly linear (gain 1.36 gave
# x1.35), so 1.36 x 1.40/1.35 = 1.41.
#
# SEPARATE FROM RUN_ENERGY ON PURPOSE. RUN_ENERGY is the physical claim -- the
# total flux one 2.6 km light run contributes, normalised so that sampling
# density stays a cost decision. This is the exposure that claim is viewed at,
# and keeping them apart is what let the sampling density change in session 3p
# without anyone having to re-argue the flux.
#
# 1.41 -> 3.384 in session 3u, and it is a compensation rather than a new
# judgement about level. Three terms that were lighting this volume were removed
# because none of them was light: ambient dropped 0.15 -> 0.03 (drum.tscn says
# why), `glow_bloom` 0.06 -> 0.0, and glow's default wide mip levels. Together
# they were carrying most of the frame's median, so the lamps have to make it up
# and the FRAME is what is held fixed.
#
# THE MULTIPLIER IS NOT THE GARDEN FRAMING'S OWN BEST NUMBER, and that is the
# whole difficulty. x2.40 puts the garden framing at x1.38 of `garden.png`,
# dead on the x1.40 target -- and at x2.40 the other two framings of the same
# volume read x1.59 (wide) and x0.98 (tram). One rig, one exposure, three
# cameras, and the three now disagree by x1.62 where at the old rig they agreed
# to within 7% (x1.393 / x1.492 / x1.496).
#
# THE RIG DID THAT, and it is a consequence rather than a fault: with 24 of 60
# lamps occluded, how much light a framing receives depends on how much of it is
# in shadow, and these three framings are as different as that gets. The tram
# camera looks up through a Warren truss at a townscape in its own shadow; the
# wide camera looks along 2.6 km of open ground with no occluder in the picture
# at all. Unoccluded light has no such spread, which is exactly why the old rig
# agreed with itself -- and why it read as blockout.
#
# So the multiplier is chosen to fit all three inside the +/-25% band rather
# than to centre any one of them, and the band is now NEARLY EXHAUSTED by
# framing-to-framing variation: x1.75/x1.05 admits a spread of x1.667 and the
# spread is x1.62. Measured, not projected: at x2.62 the three read
DRUM_EXPOSURE = 1.41 * 2.70

# HOW MANY OF THE DRUM'S LAMPS CAST SHADOWS, and it is the layer-4b lever.
#
# It was 2, which is what an omni-shadow budget on a CPU rasteriser suggests,
# and with 58 of 60 sources passing through every wall the volume had no dark
# side to anything: the calibrated garden frame had 0.99% of its pixels below
# the measurable floor against its reference's 5.63%, and its p5 sat at x2.97 of
# the show's AT MATCHED LEVEL. Measured at 24 it is x0.94 and every distribution
# check passes.
#
# 24 RATHER THAN ALL 60, measured: 60 gives p5 x0.84 against 24's x0.94 and
# costs 76 s a frame against 60 s at 960x540 on lavapipe. 24 already clears the
# x1.29 band with 27% of margin, so the extra sixteen seconds buy nothing that
# is being asked for. NOT A TARGET-HARDWARE COST: lavapipe is a CPU rasteriser
# and these seconds say nothing about an RTX 4070, where 24 omni shadow cube
# maps in a 250k-triangle scene is an ordinary load. What the seconds bound is
# how often this project can afford to look at a frame.
DRUM_SHADOW_LIGHTS = 24
# The interior rooms keep the old ration and it has not been re-derived; the
# drum's own number is not transferable, because a room 12 m across has a
# different relationship between its lamp count and its occluders than a 556 m
# cavity does. Named rather than left as an argparse default so that the two
# cannot be changed by accident together.
INTERIOR_SHADOW_LIGHTS = 2

# A light 500 m across the drum should not be 20x dimmer than one 40 m
# overhead: the drum reads near-uniformly lit in `34b`, which is what a line
# source 2.6 km long inside a reflective cavity actually does.
#
# THIS IS A DECAY EXPONENT, NOT A SHAPING EXPONENT, and the comment that used to
# sit here said otherwise. Godot 4's omni falloff is
#     (1 - (d/range)^4)^2 * d^(-attenuation)
# (scene_forward_lights_inc.glsl, `get_omni_attenuation`), so `attenuation` is
# the exponent on DISTANCE and not on the windowing term. That is why setting it
# to 8.0 to "tighten the falloff" produced a frame byte-identical to one with
# every lamp switched off: 41.7^-8 is 4e-13. Session 3u, and it is recorded
# because the wrong reading makes every number derived from this parameter
# meaningless rather than merely off.
LAMP_ATTENUATION = 0.7


# The render shots' own camera, as distinct from the player's. 46 degrees is
# what every exterior, drum and interior frame in docs/ was composed at, and
# 1.7 m is the stature this project stands a person at everywhere. Named here
# because `--fov` and `--eye-height` now default to None -- see main().
SHOT_FOV_DEG = 46.0
SHOT_EYE_HEIGHT_M = 1.7


def _eye_h(args):
    """The standing eye height a non-deck shot uses."""
    return SHOT_EYE_HEIGHT_M if args.eye_height is None else args.eye_height


def light_energy(per_run):
    """Energy for one omni, given how many sample the run. See RUN_ENERGY."""
    return RUN_ENERGY * DRUM_EXPOSURE / max(1, per_run)


def radial_aim(p):
    """Unit vector from the spin axis out through `p`. Where "down" is.

    A GUIDEWAY FITTING THROWS LIGHT AT THE FLOOR BENEATH IT, and inside a spun
    drum "beneath" is radially OUTWARD: the lamps sit at r 236.6 m and the floor
    is at r 278.3 m, so down is AWAY from the axis and not toward it. Aiming
    these inward would light the core tube and nothing else, and a frame lit
    that way looks like a lighting bug rather than a sign error.

    A function rather than three lines inline because it is the one piece of
    `--light-kind spot` that can be wrong without the render looking obviously
    broken, and because it is then testable without building 250k triangles of
    drum. See LIGHT_DIRECTIONALITY for why the spot rig is not the default.
    """
    r = math.hypot(p[0], p[1])
    if r == 0.0:
        raise ValueError("radial_aim: a lamp on the spin axis has no radial "
                         "direction; light_runs should never place one there")
    return (p[0] / r, p[1] / r, 0.0)


def light_runs(schema, profile, sector, per_run=10, z_span=None):
    """Positions of the drum's light-run samples, in station coordinates.

    Derived from `interior.guideway_truss`'s own placement arithmetic -- chord
    radius fraction, lateral offset, truss count -- so the lights cannot drift
    away from the tubes they represent. Returns one list of points per run,
    two runs per truss (the tubes sit either side of the web).
    """
    r0 = it.sector_radius(schema, profile, sector)
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = z_span if z_span else (float(ex["z0"]), float(ex["z1"]))
    r_bot = r0 * it.TRUSS_RADIUS_FRAC
    laterals = (-(it.TRUSS_CHORD_M + 3.0), it.TRUSS_CHORD_M + 3.0)

    runs = []
    for i in range(it.TRUSS_COUNT):
        a = math.radians(360.0 * i / it.TRUSS_COUNT)
        ca, sa = math.cos(a), math.sin(a)
        for lat in laterals:
            pts = []
            for k in range(per_run):
                # Samples sit at cell centres, not at the ends: a sample ON the
                # end cap would put half its cone outside the drum and leave
                # the far end darker than the middle for no physical reason.
                t = (k + 0.5) / per_run
                z = z0 + (z1 - z0) * t
                pts.append((r_bot * ca - lat * sa, r_bot * sa + lat * ca, z))
            runs.append(pts)
    return runs


# ---------------------------------------------------------------------------
# OBJ / glTF plumbing
# ---------------------------------------------------------------------------

def write_obj(path, verts, tris, groups):
    """Grouped OBJ. Same format `interior.write_grouped_obj` emits."""
    order, seen = [], set()
    for g in groups:
        if g not in seen:
            seen.add(g)
            order.append(g)
    by_group = {g: [] for g in order}
    for i, t in enumerate(tris):
        by_group[groups[i]].append(t)
    with open(path, "w") as f:
        for x, y, z in verts:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for g in order:
            f.write(f"g {g}\no {g}\n")
            for a, b, c in by_group[g]:
                f.write(f"f {a + 1} {b + 1} {c + 1}\n")
    return len(tris)


def to_glb(obj_path, glb_path):
    """Run the project's glTF exporter over one OBJ.

    Shelled out rather than imported: `station/export_gltf.py` is another
    agent's file and is argparse-driven, so calling its CLI is the contract
    that will not break when its internals change.
    """
    rel_obj = os.path.relpath(obj_path, ROOT)
    rel_glb = os.path.relpath(glb_path, ROOT)
    subprocess.run(
        [sys.executable, os.path.join(STATION, "export_gltf.py"),
         "--obj", rel_obj, "--out", rel_glb],
        check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
    return glb_path


def glb_triangles(path):
    """Triangle count read back out of a .glb, by parsing its JSON chunk.

    Read back rather than trusted. A truncated or mis-offset buffer still
    produces a file Godot will load and half-draw, and half a hull is not an
    error anyone notices in a 960x540 render of a black scene.
    """
    with open(path, "rb") as f:
        magic, version, total = struct.unpack("<III", f.read(12))
        if magic != 0x46546C67 or version != 2:
            raise ValueError(f"{path}: not a glTF 2.0 binary")
        if total != os.path.getsize(path):
            raise ValueError(f"{path}: header length {total} != file size "
                             f"{os.path.getsize(path)}")
        js_len, js_kind = struct.unpack("<II", f.read(8))
        if js_kind != 0x4E4F534A:
            raise ValueError(f"{path}: first chunk is not JSON")
        doc = json.loads(f.read(js_len))
    n = 0
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            n += doc["accessors"][prim["indices"]]["count"] // 3
    return n, [m["name"] for m in doc["meshes"]]


# ---------------------------------------------------------------------------
# Shots
# ---------------------------------------------------------------------------

def _spherical(dist, elev_deg, az_deg, target):
    el, az = math.radians(elev_deg), math.radians(az_deg)
    return (target[0] + dist * math.cos(el) * math.cos(az),
            target[1] + dist * math.sin(el),
            target[2] + dist * math.cos(el) * math.sin(az))


def hull_near_distance(eye):
    """Distance from the eye to the nearest point of the hull's bounding box.

    Distance is taken to the NEAREST point of the hull, not to the aim point.
    An 8 km station seen from 9 km has its near end at about 5 km, and picking
    a level on centre distance would decimate geometry that is half as far away
    as the number used to justify it.

    The box is a conservative stand-in for the surface: it is never further from
    the eye than the hull is, so the level chosen is never coarser than the true
    nearest point would justify. Erring toward a finer level is the right way
    round -- the failure this guards against is decimating geometry the player
    is looking at from close range.
    """
    hull_man = os.path.join(GENERATED, "hull_manifest.json")
    if os.path.exists(hull_man):
        b = json.load(open(hull_man))["bounds"]
        r, length = b["max_radius_m"], b["length_m"]
    else:
        r, length = 1211.0, 8047.0

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    near = (clamp(eye[0], -r, r), clamp(eye[1], -r, r), clamp(eye[2], 0.0, length))
    return math.dist(eye, near)


def pick_hull_lod(eye, target, forced=""):
    """Which hull LOD a shot should use, and why.

    This did not exist, so every exterior shot drew lod0 however far away the
    camera was -- a 95 km shot would have drawn 327,346 triangles to cover a few
    hundred pixels. The chain was built, measured and given a manifest three
    sessions ago and was simply never connected to the thing that renders.

    Selection is on the COMBINED schedules. `station/lod.py` no longer steps
    radial segments, z stride and greeble detail together: they are three
    independent schedules with three separately derived switch distances, and a
    level is the distinct combination those three produce over a distance band.
    The chain in the manifest is already that flattened combination, so the walk
    here stays a walk -- but the reason string now names WHICH schedule moved,
    because "lod3" says nothing about whether the outline or the surface detail
    just changed and that is the first question when a render looks wrong.
    """
    man_path = os.path.join(GENERATED, "lod_manifest.json")
    if not os.path.exists(man_path):
        return os.path.join(GENERATED, "hull.obj"), "lod0", 0.0, "no lod manifest"
    man = json.load(open(man_path))
    levels = man["levels"]
    dist = hull_near_distance(eye)

    if forced and forced != "auto":
        chosen = next((lv for lv in levels if lv["name"] == forced), None)
        if chosen is None:
            # Raised rather than quietly falling back to lod0. The override is a
            # debugging tool, and silently rendering a different level than the
            # one asked for wastes the session that asked for it.
            raise SystemExit(
                f"--lod {forced}: no such level. The chain has "
                f"{', '.join(lv['name'] for lv in levels)}. Note the chain is "
                f"derived, so its length changes when a schedule changes.")
        why = f"forced {forced}"
    else:
        chosen = levels[0]
        for lv in levels:
            if dist >= lv["switch_distance_m"]:
                chosen = lv
        why = (f"nearest hull point {dist:,.0f} m; {chosen['name']} "
               f"= {chosen['radial_segments']} segments / z-stride "
               f"{chosen['z_stride']} / greeble {chosen['greeble_detail']:g}, "
               f"from {chosen['switch_distance_m']:,} m")
        honest = chosen.get("honest_from_m")
        if isinstance(honest, dict):
            # Which schedule is holding the level back. With one table this was
            # unanswerable; with three it is the useful half of the reason.
            binding = max(honest, key=lambda k: honest[k])
            why += f" (binding schedule: {binding} at {honest[binding]:,} m)"
        gap = chosen.get("aliasing_gap_at_far_end") or {}
        if gap:
            why += ("; drawing sub-pixel "
                    + "/".join(sorted(gap)) + " detail at its far end")

    path = os.path.join(GENERATED, f"hull_{chosen['name']}.obj")
    if not os.path.exists(path):
        path = os.path.join(GENERATED, "hull.obj")
        why += (f" (hull_{chosen['name']}.obj missing -- fell back to hull.obj; "
                f"run `python3 station/lod.py --build`)")
    return path, chosen["name"], dist, why


def it_length():
    """Hull length from the built manifest, for the LOD selection assertions.

    Read rather than hard-coded: the assertions below construct eye positions
    relative to the nose, and a stale constant would put them inside the hull
    where every one of them would pass for the wrong reason.
    """
    hull_man = os.path.join(GENERATED, "hull_manifest.json")
    if os.path.exists(hull_man):
        return float(json.load(open(hull_man))["bounds"]["length_m"])
    return 8047.0


def _lod_options(name):
    """The three schedule settings behind a level name, or {} if unknown."""
    man_path = os.path.join(GENERATED, "lod_manifest.json")
    if not os.path.exists(man_path):
        return {}
    for lv in json.load(open(man_path))["levels"]:
        if lv["name"] == name:
            return {k: lv[k] for k in
                    ("radial_segments", "z_stride", "greeble_detail")
                    if k in lv}
    return {}


# ---------------------------------------------------------------------------
# The exterior's two lighting conditions
# ---------------------------------------------------------------------------
# WHY THERE ARE TWO. Until session 3r the exterior rig rendered exactly one
# condition -- full sun -- and the standing blocking finding against it, open
# since session 3k, said why that is not enough: "A station 8 km long in orbit
# has a terminator, and the side facing away from the sun is where the thing
# reads as INHABITED rather than as a lit model." It is the first thing the
# owner's opening beat shows.
#
# WHERE EACH HALF LIVES. The LOOK of both conditions -- exposure, ambient,
# bloom, which lights go dark -- is in `godot/scenes/exterior.tscn`, because a
# look has to be judged as a whole. What is here is the SHOT's half: where the
# sun goes, which condition this frame is, and the calibration record.
#
# THE SUN IS PLACED RELATIVE TO THE CAMERA, not at an absolute azimuth, and
# that is the difference between a night condition and a night-looking frame.
# "Night side" is not a property of the sun; it is the angle between the sun
# and the eye. Nail the sun to a world azimuth and orbiting the camera turns
# night silently back into day -- the same failure `_aim_sun`'s docstring
# already records for the rim: "A rig nailed to world axes stops being a rig
# the moment the camera moves."
#
# THE PHASE is how far the sun is off dead-behind-the-station, and it is DERIVED
# rather than dialled. For a convex body the sunlit crescent covers
# (1 - cos(phase)) / 2 of the visible face, so the phase decides how many PIXELS
# of lit edge the frame gets, and at the arrival framing the habitat drum is
# about 90 px across a 960-wide frame:
#
#   phase 22 -> 3.6% of the face -> 3.3 px. A line at the resolution limit; it
#               aliases along the barrel and reads as a rendering artefact.
#   phase 39 -> 11.1% -> 10 px. The floor: below this the crescent is thinner
#               than the greebles standing on it.
#   phase 46 -> 15.3% -> 14 px. Taken.
#
# WHY IT MATTERS MORE THAN IT LOOKS. The terminator is what gives the unlit
# station its shape, and it is the only PHYSICAL way to do that -- the
# alternative is more planetshine, which buys the silhouette by washing out the
# windows, and the windows are the whole finding. Measured at the arrival
# framing over the station's own footprint: at phase 22 with no planetshine 38%
# of the hull is distinguishable from the starfield, and at phase 46 with the
# planetshine floor it is 66%, with the drum's window band still reading 4.9x
# over the plate between bands. Widening the crescent is nearly free; brightening
# the ambient is not.
#
# The 46 itself is DECLARED, authority 5. What is derived is the floor at 39.
NIGHT_SUN_PHASE_DEG = 46.0

# THE EXPOSURE RECORD, kept the way ROOM_EXPOSURE and DRUM_EXPOSURE are kept
# except for one thing: the VALUES are not here. They are `tonemap_exposure` on
# the two Environments in exterior.tscn, and this reads them back out of that
# file the way `scene_material_rules` reads the material rules back, for the
# same reason -- two copies of a number drift, and the copy that loses is
# always the one the renderer does not read.
#
# ------------------------------------------------------------------ THE DAY
#
# THE REFERENCE, and the first thing found was that the obvious comparison is
# not a comparison at all. `reference/01-station-exterior/` holds five files
# and THREE OF THEM ARE MISFILED INTERIORS -- `view.jpg` is byte-identical to
# `03-sector-blue/Babylon_5_2-22_34b.jpg` (the drum, and the frame the DRUM
# exposure is calibrated against), `welcome to babylon 5.webp` is customs
# signage, `sleeping-in-light-05.jpg` is Downbelow. reference/00-INDEX.md says
# so for all three. That leaves two real exteriors.
#
# `exterior more.jpg` is the only one showing the whole station in sunlight,
# and measuring it whole-frame measures A DESKTOP WALLPAPER'S BACKDROP: the
# sheet is a fan-assembled wallpaper (00-INDEX: "rounded-rectangle bevelled
# border, marbled backdrop, drop shadows... a large glassy embossed 5"), and
# the marbled plate behind the projections measures median 0.1259 -- the whole
# frame's median, to four decimal places. The station contributes nothing to
# it. So the comparison is against a CROP.
#
# `Cobra Bays with starfurries.webp` is authority 1 and is NOT the day
# reference: it is a close shot of the bay face out of sunlight. It is used
# below, for the night side, where being out of sunlight is the point.
#
# THE CALIBRATION SHOT IS NOT THE ARRIVAL SHOT. The reference's projections are
# orthographic side and top views, and comparing them to a 9.2 km three-quarter
# orbit compares lit FRACTIONS as much as levels. The calibration shot is a
# near-orthographic side-on frame -- 30 km at fov 16, lod0 forced -- so the two
# crops frame the same object the same way. Both crops come out with the same
# proportion of background (9.6% ours, 8.0% the reference's), which is the
# check that the framings really are matched.
#
# THE STATISTIC IS p95 AND NOT THE MEDIAN. See the note on `tonemap_exposure`
# in exterior.tscn: the reference hull is mostly dark blue-purple courses and
# ours is warm off-white throughout, so their medians sit at 29% and 76% of
# their own brightest plate. That is a shape difference and no exposure fixes
# it. p95 is the brightest sunlit plating, which is the same white plate in
# both frames.
#
# TWO PROJECTIONS AGREE, which is what makes the number usable at all: the
# sheet's side view and top view of the same drum measure p95 0.2378 and
# 0.2051 and mean linear rgb (0.084, 0.085, 0.110) and (0.088, 0.087, 0.112) --
# 14% apart on the statistic and 3% apart on colour, from two independent
# renders on one sheet.
#
# WHAT WOULD OVERTURN IT: any Season 2-3 broadcast frame of the station in
# sunlight at range. There is none in the reference set. `exterior more.jpg`
# is a render of the production model rather than a screencap, so the x1.40
# offset -- whose stated derivation is "a film frame carries a grade, a stock
# and chroma subsampling and our render carries none of them" -- is on weaker
# ground here than anywhere else in the project. It is kept anyway: every other
# space targets 1.40, the two projections of this one sheet already disagree by
# 14%, and changing the project's single calibration constant for one space on
# an argument that cannot be measured is picking the convenient reading.
#
# ----------------------------------------------------------------- THE NIGHT
#
# THERE IS NO REFERENCE FRAME FOR THE STATION AT RANGE ON THE ANTI-SUN SIDE,
# and INV-036 says the same thing about the windows themselves: "No frame in
# the reference set shows the hull lit from within at range." So the night
# exposure is NOT calibrated against a reference median, and saying it is would
# be the exact dishonesty CLAUDE.md's first hard rule is about. It is derived
# from three things that ARE measurable, and the gates below are those three:
#
#   1. THE WINDOW SHEET'S OWN EMISSION. `hull_window_emission.png` has mean
#      linear rgb (0.0219, 0.0191, 0.0132) over its 2048 square, 2.86% of it
#      lit above 0.2, at `emission_energy` 3.4 -- so a mean EMISSION of 0.066
#      at any range where the apertures do not resolve, which at the arrival
#      distance they do not (the drum is 500 m across over ~90 px, i.e. 5.5 m
#      a pixel against a 1.10 m aperture). MEASURED, off the shipping texture.
#   2. THE BAND MUST READ. INV-036 builds eight decks per repeat with two
#      glazed and 28% of blocks dark, so 0.25 x 0.72 = 18% of the habitat hull
#      should be above tools/measure_frame.py's 0.010 floor. The gate asks for
#      12%, two thirds of the derived figure, because at a three-quarter
#      orbit part of the band is on the far side and part is at grazing
#      incidence. DERIVED from INV-036.
#   3. IT MUST NOT BECOME A LIGHTBOX. Clipping stays under the 4% that
#      tools/measure_frame.py itself calls overexposed. INV-036's whole point
#      is that the lit fraction is below 1.0 "because a third of the population
#      is asleep"; a night side that clips has thrown that away.
#
# `Cobra Bays with starfurries.webp` is the one authority-1 broadcast frame of
# station exterior OUT of sunlight we hold, and it is quoted here as a sanity
# check rather than as a target, because it is a close shot of one bay face and
# this is the whole station at 9 km: median 0.0345, p5/p95 0.048, 43.9% of the
# frame crushed, 0.08% clipped. What it says that transfers is the SHAPE -- a
# frame of unlit station read by its own fittings is mostly below the floor and
# clips essentially nothing.
EXTERIOR_CALIBRATION = {
    "day": {
        "reference": "reference/01-station-exterior/exterior more.jpg",
        # (left, top, right, bottom) as fractions. The habitat drum in each of
        # the sheet's two orthographic projections.
        "reference_boxes": {"side": (0.49, 0.47, 0.69, 0.57),
                            "top": (0.44, 0.145, 0.66, 0.235)},
        "reference_p95": {"side": 0.2378, "top": 0.2051},
        # The mean of the two projections, which is what the exposure is set
        # against.
        "reference_value": 0.2215,
        "statistic": "bright_p95",
        # The calibration shot, exactly. Anything else measured against the
        # boxes below is measuring a different frame.
        "shot": ("--shot exterior --eye 30000,0,4023 --target 0,0,4023 "
                 "--fov 16 --lod lod0 --sun-elev 45 --sun-az 25 "
                 "--res 960x540"),
        "our_box": (0.35, 0.45, 0.54, 0.54),
        # Three points on the AgX response, from that shot: exposure 1.00 gave
        # p95 0.5117, 0.70 gave 0.4251, 0.40 gave 0.2943. Strongly sub-linear
        # -- out ~ exposure^0.62 -- so the correction is NOT the ratio, and
        # assuming it was would have landed this two thirds of a stop dark.
        "verified_p95": 0.3108,
        "verified_multiple": 1.403,
        # THE EXPOSURE THOSE TWO NUMBERS WERE TAKEN AT. Not a duplicate of the
        # .tscn's value -- it is the statement "the verification above
        # describes a scene set to this", and the self-test reads the .tscn
        # back and compares. Without it the recorded derivation can stay
        # internally consistent while describing a file nobody has measured:
        # set `Env`'s tonemap_exposure to 1.00 and every number here is still
        # self-consistent and every one of them is wrong.
        "exposure": 0.43,
    },
    "night": {
        # Deliberately no "reference". See above: there is none, and a key
        # here with a plausible frame path in it would be a lie that reads as
        # provenance.
        "sanity_frame": "reference/01-station-exterior/"
                        "Cobra Bays with starfurries.webp",
        "sanity_stats": {"median": 0.0345, "ratio": 0.048,
                         "crushed": 0.4385, "clipped": 0.0008},
        "shot": ("--shot exterior --lighting night --orbit 9200,18,214 "
                 "--res 960x540"),
        # THE THREE BOXES, at the arrival framing. All three are on the DAY
        # frame's geometry too, so every night number has a daylight number
        # beside it taken from the same pixels.
        #   habitat   the drum barrel -- the pressurised, glazed section
        #   structure the aft truss spine and terminus -- nobody lives there
        #             and INV-036 keeps it dark on purpose
        #   sky       empty space, for what "visible against the starfield"
        #             means in this frame
        "habitat_box": (0.47, 0.44, 0.59, 0.52),
        "structure_box": (0.20, 0.545, 0.36, 0.605),
        "sky_box": (0.03, 0.70, 0.30, 0.95),
        "emission_texture_mean_linear": 0.0193,
        "emission_energy": 3.4,
        # A night frame whose habitat box has not fallen by at least this much
        # against the day frame at the SAME camera is a night frame that did
        # not happen. This is the gate for "the flag did nothing", which is the
        # failure mode this pipeline has shipped twice: `--light-gain` scaling
        # no lights, and material rules pasted into a file nobody read back.
        # 4x is a floor a broken condition cannot clear -- the two exposures
        # alone differ by 8.4x -- and the frames measure 21.8x.
        "min_day_night_drop": 4.0,
        # LIT FROM WITHIN, and it took two wrong statistics to find the right
        # one. The first was "what fraction of the drum is above the measurable
        # floor", which PLANETSHINE SATISFIES WITH NO WINDOWS AT ALL. The
        # second was the drum's own p99/p50, which at 960x540 measures the
        # MARKER LIGHTS: the box is 3,680 pixels, so p99 is its brightest 37,
        # and those are navigation lamps, not window band. The band itself only
        # reaches p90, at 1.9x the plate.
        #
        # 1.9x is not a defect. At the arrival distance the drum is 500 m over
        # ~90 px, i.e. 5.5 m a pixel against INV-036's 1.10 m aperture and
        # 3.6 m deck pitch, so no window and no window ROW resolves. What
        # resolves is INV-036's long-period variation -- 28% of blocks five
        # repeats square with nothing lit, which is 144 m, which is 26 px. At
        # range the window sheet is districts, not windows.
        #
        # So the statistic that carries the finding is the one INV-036 itself
        # states: the pressurised sections are lit and the truss, the reactor
        # and the spike "have nobody in them and stay dark". The gate is the
        # ratio between them, measured against the SAME ratio in daylight,
        # where both are lit from outside by one sun. Day 12.7, night 30.4.
        # Requiring 2x the day figure says the habitat is at least a stop
        # brighter relative to the structure than any external light explains.
        "lit_from_within_over_day": 2.0,
        # THE SILHOUETTE READS. Fraction of the station's own footprint --
        # taken from the DAY frame, so it is the real outline and not a
        # threshold on the night frame -- that is brighter at night than 99% of
        # empty sky in the same frame. Half is the line: a shape more than half
        # of which is indistinguishable from space is not a station coming into
        # view, it is fragments. Measured: 37.9% with the planetshine floor
        # removed, 66.8% as it ships.
        "min_footprint_visible": 0.50,
        # NOT A LIGHTBOX. The night side must not be rescued by opening up
        # until the windows blow -- INV-036's whole point is a lit fraction
        # below 1.0 "because a third of the population is asleep", and a
        # clipped frame has thrown that away.
        #
        # MEASURED OVER THE STATION'S FOOTPRINT, NOT THE FRAME, and this had to
        # be corrected after the gate was written: measure_frame's 4%-of-frame
        # threshold was calibrated on interiors, which fill the frame. The
        # station is 4.4% of an arrival frame, so 4% of the FRAME means the
        # entire hull has blown and then some -- the gate could not fail. A
        # deliberate night render at exposure 60, sixteen times the shipping
        # value, clipped 0.098% of the frame and would have PASSED.
        #
        # 0.5% of the footprint, and the derivation is two measured frames: the
        # calibrated DAY frame clips 0.00% of the footprint with an 8 km hull
        # in direct sun, and `Cobra Bays with starfurries.webp` -- the one
        # authority-1 broadcast frame of this station's exterior out of
        # sunlight, with working lamps in shot -- clips 0.08% of itself. Half a
        # percent sits above the show's own night frame and far below anything
        # that means a hull surface has gone. At exposure 60 the footprint
        # clips 2.43% and the gate fires.
        "max_footprint_clipped": 0.005,
    },
    # WHAT WAS MEASURED AND LEFT ALONE, recorded because the next session will
    # otherwise ask the same two questions and pay for the same four renders.
    #
    # SSAO IS OFF AT NIGHT AND IT IS FREE TO BE. Rendering the night arrival
    # shot with `ssao_enabled` true in EnvNight produced a BYTE-IDENTICAL PNG
    # (max channel delta 0 over 960x540) and took 12s against 9s. It modulates
    # ambient occlusion and the night ambient is a 0.12 planetshine floor, so
    # there is nothing for it to occlude. A third of the frame time for no
    # pixels.
    #
    # THE SUN'S SHADOWS STAY ON AT NIGHT, and this one went the other way. The
    # standing suspicion was that four PSSM splits over a 12 km range are tuned
    # for a lit hull and are wasted on a dark one. Measured: turning
    # `shadow_enabled` off on the Sun changed 10.0% of the frame, 2.0% of it by
    # more than 8/255, with a peak delta of 244, and lifted the habitat box's
    # median 12% -- because the crescent is a GRAZING light and grazing light
    # is all shadow. It also saved nothing measurable (9s either way). The
    # hypothesis is refuted; the rig is unchanged.
    #
    # The .tscn's `directional_shadow_max_distance = 12000` is never the value
    # used anyway: `render_shot._aim_sun` overrides it per shot to
    # clamp(eye-to-target x 2.2, 400, 20000), which at the arrival framing is
    # the 20 km clamp.
    "measured_and_unchanged": {
        "ssao_night": "byte-identical PNG, 12s vs 9s -> disabled",
        "sun_shadows_night": "10.0% of pixels change, no time saved -> kept",
    },
}


def scene_env_exposure(tscn_path, sub_id):
    """`tonemap_exposure` off one Environment sub-resource in a .tscn.

    Read back rather than restated, for the reason `scene_material_rules`
    exists: the renderer reads the scene file, so anything a gate checks has to
    come from the scene file too. A Python constant holding "the exposure" can
    be right while the render is wrong, which is worse than not checking.
    """
    with open(tscn_path) as f:
        text = f.read()
    m = re.search(r'\[sub_resource type="Environment" id="%s"\](.*?)(?=\n\[|\Z)'
                  % re.escape(sub_id), text, re.S)
    if not m:
        raise ValueError(f"{tscn_path}: no Environment sub-resource "
                         f"'{sub_id}'")
    e = re.search(r"^tonemap_exposure = ([0-9.eE+-]+)", m.group(1), re.M)
    if not e:
        raise ValueError(f"{tscn_path}: Environment '{sub_id}' sets no "
                         f"tonemap_exposure")
    return float(e.group(1))


def _measure_frame():
    """`tools/measure_frame`, imported late.

    Late because it pulls numpy and pillow, and every OTHER path through this
    file -- assembling a shot for the renderer -- needs neither. The gates are
    the only consumer.
    """
    p = os.path.join(ROOT, "tools")
    if p not in sys.path:
        sys.path.insert(0, p)
    import measure_frame
    return measure_frame


def measure_box(png, box):
    """`tools/measure_frame.measure` over a fractional crop of one PNG.

    Cropping is not a second yardstick. The reference measurements in
    docs/layer4-lighting/*.json all name a REGION -- "the soffit above the
    gallery fascia", "the clean deck field" -- and this is the same move with
    the region written down instead of described. What must not change is the
    code doing the measuring, which is why measure_frame is imported rather
    than reimplemented.
    """
    import tempfile
    from PIL import Image
    mf = _measure_frame()

    im = Image.open(png).convert("RGB")
    w, h = im.size
    l, t, r, b = box
    c = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
    fd, p = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        c.save(p)
        return mf.measure(p)
    finally:
        os.unlink(p)


def gate_exterior_day(png, tolerance=0.25):
    """Is the day frame at x1.40 of its reference's brightest sunlit plate?

    Returns (ok, message). The frame must be the calibration shot in
    EXTERIOR_CALIBRATION["day"]["shot"]; measuring any other framing against
    this box measures whatever happens to be in it.
    """
    mf = _measure_frame()
    cal = EXTERIOR_CALIBRATION["day"]
    if not os.path.exists(png):
        return False, f"day calibration frame missing: {png}"
    m = measure_box(png, cal["our_box"])
    x = m["bright_p95"] / cal["reference_value"]
    ok = abs(x - mf.RENDER_OFFSET) <= tolerance * mf.RENDER_OFFSET
    return ok, (f"day p95 {m['bright_p95']:.4f} = x{x:.2f} of the reference's "
                f"{cal['reference_value']:.4f} (target x{mf.RENDER_OFFSET:.2f} "
                f"+/-{tolerance * 100:.0f}%)")


def frame_luma(png):
    """Linear Rec.709 luminance of a whole PNG, by measure_frame's own code.

    measure_frame.measure returns percentiles over its MEASURABLE population --
    everything between its floor and its clip -- which is exactly right for
    comparing a room to a reference frame and exactly wrong for two boxes on
    one night frame: the population changes between them, so p95 in a box that
    is 16% measurable and p95 in a box that is 54% measurable are percentiles
    of different things. That cost a wrong reading here -- adding light appeared
    to LOWER the drum's p95. Fixed populations from here on.
    """
    import numpy as np
    from PIL import Image
    mf = _measure_frame()
    a = np.asarray(Image.open(png).convert("RGB"), dtype=np.float64) / 255.0
    return mf.srgb_to_linear(a) @ np.array(mf.LUMA)


def _crop(y, box):
    h, w = y.shape
    return y[int(box[1] * h):int(box[3] * h), int(box[0] * w):int(box[2] * w)]


def gate_exterior_night(day_png, night_png):
    """The four things the night side can be held to. Returns (ok, [lines]).

    NOT ONE OF THEM IS "matches a reference", because there is no reference
    frame of this station at range on the anti-sun side and pretending there is
    would be worse than having no gate. They are, in order: the condition did
    something; the station is lit from WITHIN rather than from outside; the
    silhouette reads against the starfield; the frame is not a lightbox.

    THE MIDDLE TWO PULL AGAINST EACH OTHER, which is the property that makes
    them worth having. Planetshine buys silhouette and costs the lit-from-
    within ratio: with it removed the frame scores 5.9 million and 37.9%, with
    it at 0.55 it scores 14.4 and 94.6%. Neither extreme passes both. A pair of
    gates that a single knob can satisfy is one gate.
    """
    cal = EXTERIOR_CALIBRATION["night"]
    import numpy as np
    mf = _measure_frame()
    lines, ok = [], True
    for p in (day_png, night_png):
        if not os.path.exists(p):
            return False, [f"night gate frame missing: {p}"]

    d, n = frame_luma(day_png), frame_luma(night_png)
    if d.shape != n.shape:
        return False, [f"day and night frames differ in size: "
                       f"{d.shape} vs {n.shape} -- the boxes and the footprint "
                       f"mask only mean anything at one framing"]

    def p50(y, box):
        return float(np.percentile(_crop(y, box), 50))

    hab_d, hab_n = p50(d, cal["habitat_box"]), p50(n, cal["habitat_box"])
    str_d, str_n = p50(d, cal["structure_box"]), p50(n, cal["structure_box"])

    drop = hab_d / hab_n if hab_n else float("inf")
    good = drop >= cal["min_day_night_drop"]
    ok &= good
    lines.append(f"  {'OK  ' if good else 'FAIL'} the condition happened: "
                 f"habitat median {hab_d:.4f} -> {hab_n:.4f}, x{drop:.1f} down "
                 f"(need x{cal['min_day_night_drop']:.0f})")

    r_d = hab_d / max(str_d, 1e-9)
    r_n = hab_n / max(str_n, 1e-9)
    want = r_d * cal["lit_from_within_over_day"]
    good = r_n >= want
    ok &= good
    lines.append(f"  {'OK  ' if good else 'FAIL'} lit from within: habitat "
                 f"over unlit structure {r_n:.1f} at night against {r_d:.1f} "
                 f"in daylight (need {want:.1f} = "
                 f"x{cal['lit_from_within_over_day']:.0f} the day figure)")

    # The footprint comes from the DAY frame, so it is the station's real
    # outline. Thresholding the NIGHT frame for it would ask whether the bright
    # parts are bright.
    mask = d >= mf.FLOOR
    thr = float(np.percentile(_crop(n, cal["sky_box"]), 99))
    seen = float((n[mask] > thr).mean()) if mask.any() else 0.0
    good = seen >= cal["min_footprint_visible"]
    ok &= good
    lines.append(f"  {'OK  ' if good else 'FAIL'} the silhouette reads: "
                 f"{seen * 100:.1f}% of the station's footprint is brighter "
                 f"than 99% of empty sky "
                 f"(need {cal['min_footprint_visible'] * 100:.0f}%)")

    clipped = float((n[mask] >= mf.CLIP).mean()) if mask.any() else 0.0
    good = clipped <= cal["max_footprint_clipped"]
    ok &= good
    lines.append(f"  {'OK  ' if good else 'FAIL'} not a lightbox: "
                 f"{clipped * 100:.2f}% of the station's footprint clipped "
                 f"(max {cal['max_footprint_clipped'] * 100:.1f}%)")
    return ok, lines


# The three committed frames the gates read. They are FRAMES rather than
# numbers on purpose: a gate that checks a constant against a constant cannot
# fail, and this project has written three of those this month. These fail the
# moment the rig, the exposure, the hull material or the window sheet moves,
# and the only way to make them pass again is to re-render and look.
GATE_FRAMES = {
    "day_calibration": "docs/engine-exterior-calibration.png",
    "day_arrival": "docs/engine-exterior-day.png",
    "night_arrival": "docs/engine-exterior-night.png",
}


def run_exterior_gates(*paths):
    """Both exterior gates over committed frames. True if everything passes."""
    p = list(paths) + [os.path.join(ROOT, GATE_FRAMES[k])
                       for k in ("day_calibration", "day_arrival",
                                 "night_arrival")][len(paths):]
    cal, day, night = p[0], p[1], p[2]
    ok, msg = gate_exterior_day(cal)
    print(f"exterior day exposure  {'OK  ' if ok else 'FAIL'} {msg}")
    night_ok, lines = gate_exterior_night(day, night)
    print("exterior night side")
    for ln in lines:
        print(ln)
    return ok and night_ok


def camera_spherical(eye, target):
    """The eye as (elevation, azimuth) in `_spherical`'s own convention.

    The inverse of `_spherical`, and it exists so the night sun can be placed
    relative to the CAMERA. Returning both angles rather than just the azimuth
    was a correction: the first night frame set only the azimuth opposite and
    left the elevation at the day default, so with the eye 18 degrees up and
    the sun 34 degrees up the two were 124 degrees apart rather than 158, the
    barrel's whole upper surface stayed lit, and the frame came back looking
    like a slightly underexposed day. Half an antipode is not an antipode.
    """
    dx, dy, dz = eye[0] - target[0], eye[1] - target[1], eye[2] - target[2]
    d = math.dist(eye, target) or 1.0
    return (math.degrees(math.asin(max(-1.0, min(1.0, dy / d)))),
            math.degrees(math.atan2(dz, dx)))


def build_exterior(args, out_dir):
    """The whole station against space. One glb, straight off the hull."""
    target0 = (0.0, 0.0, args.target_z)
    if args.eye:
        eye0 = args.eye
    else:
        d0, e0, a0 = args.orbit
        eye0 = _spherical(d0, e0, a0, target0)
    obj, lod_name, lod_dist, lod_why = pick_hull_lod(
        eye0, target0, getattr(args, "lod", "auto"))
    print(f"hull LOD: {lod_name} -- {lod_why}")
    if not os.path.exists(obj):
        raise SystemExit("station/generated/hull.obj is missing -- run "
                         "station/generate_hull.py first")
    glb = to_glb(obj, os.path.join(out_dir, "hull.glb"))
    tris, groups = glb_triangles(glb)

    target = (0.0, 0.0, args.target_z)
    if args.eye:
        eye = args.eye
    else:
        dist, elev, az = args.orbit
        eye = _spherical(dist, elev, az, target)
    aim = args.target if args.target else target

    # The sun. On the day side it is where the shot says; on the night side it
    # is behind the station AS SEEN FROM THIS EYE, because that is what makes
    # the frame a night frame. Derived from the eye rather than from --orbit so
    # that --eye works too: a shot given an explicit eye position and a
    # `--lighting night` that quietly used --orbit's untouched default would
    # come back fully lit and look like a rig failure.
    #
    # `--sun-az` and `--sun-elev` DO NOT APPLY at night, and that is the point
    # rather than a limitation: the sun's job in a night shot is to be behind
    # the station from this eye, and letting a shot set it absolutely is how a
    # night frame comes back lit.
    lighting = getattr(args, "lighting", "day")
    if lighting == "night":
        cam_elev, cam_az = camera_spherical(eye, target)
        # The antipode of the eye, swung about the SPIN AXIS by the phase --
        # about the spin axis rather than about anything else so the surviving
        # crescent runs down one flank of the barrel, where it reads as a
        # cylinder 500 m across, instead of along the top where it reads as a
        # rim light.
        sun_elev = -cam_elev
        sun_az = cam_az + 180.0 + args.night_sun_phase
    else:
        sun_elev, sun_az = args.sun_elev, args.sun_az

    return {
        "shot": "exterior",
        # WHICH OF THE SCENE'S TWO LOOKS THIS FRAME IS. The look itself is in
        # exterior.tscn -- see the note there on why it is a second Environment
        # and not a second scene. All that belongs in the shot is which one,
        # because which side of the terminator the camera is on is a property
        # of the shot and not of the look.
        "lighting": lighting,
        "scene": "res://scenes/exterior.tscn",
        "glb": [glb],
        "triangles": tris,
        "groups": groups,
        "hull_lod": lod_name,
        "hull_lod_distance_m": round(lod_dist),
        "hull_lod_reason": lod_why,
        # The three schedule settings, written into the shot rather than left
        # implicit in a level name. A frame that is compared against an earlier
        # one months later needs to know whether it was drawn with the same
        # outline AND the same surface detail, and "lod1" does not say.
        "hull_lod_options": _lod_options(lod_name),
        "lights": [],
        # World +Y up. The station's long axis is +Z, so using that as up would
        # stand an 8 km station on its nose.
        "camera": {"eye": list(eye), "target": list(aim), "up": [0.0, 1.0, 0.0],
                   "fov": SHOT_FOV_DEG if args.fov is None else args.fov,
                   "near": 1.0, "far": 200000.0},
        # The three lights are given as the points they come FROM, so the
        # scene can aim a DirectionalLight without anyone having to reason
        # about which axis a hand-written 3x3 basis points down.
        #
        # All three are DERIVED from the key, and that is the fix for a real
        # defect: the rim was previously a fixed basis in the .tscn, and at
        # the framings used here it happened to point from roughly the camera's
        # own side. It was therefore a second frontal fill, and no choice of
        # sun angle produced a terminator -- the 8 km hull read as one flat
        # grey value end to end however the key was moved. A rig nailed to
        # world axes stops being a rig the moment the camera moves.
        "sun_from": list(_spherical(20000.0, sun_elev, sun_az, target)),
        # Kicker from behind and slightly below, opposite the key: its whole
        # job is to put a bright edge on the unlit side so the silhouette
        # separates from black space.
        #
        # AT NIGHT IT IS DARK, and exterior.tscn's `night_lights_off` is what
        # darkens it -- not this file. Which lights are burning is part of the
        # look. It is still AIMED here, from the resolved sun rather than from
        # --sun-az, so that if the look ever wants it back it is pointing where
        # its own docstring says it should rather than at the day sun.
        "rim_from": list(_spherical(20000.0, -10.0, sun_az + 175.0, target)),
        # Fill sits on the OPPOSITE side of the camera axis from the key --
        # mirrored through it -- which is where a fill goes and where it does
        # some good. Put on the same side as the key it merely brightens the
        # side that is already lit, which is what the first version did and
        # why the terminator kept refusing to appear.
        "fill_from": list(_spherical(20000.0, args.orbit[1] + 10.0,
                                     2 * args.orbit[2] - sun_az, target)),
        "sun_at": list(target),
        # Per-shot ambient, the same override the interior shot has and for the
        # same reason: it exists so the calibrated value in the .tscn can be
        # found by rendering and measuring rather than by taste. Absent unless
        # asked for, so the .tscn's value is what ships.
        **({"ambient": args.ambient} if args.ambient is not None else {}),
    }


def drum_parts(schema, profile, sector, eye, trams=2):
    """Every mesh the drum shot contains, as (name, verts, tris, groups).

    The ONE place the drum shot's contents are listed. An earlier version had
    the list here and a second copy in the self-test's group enumeration, which
    is the failure this project keeps repeating in new costumes: two copies of
    a mapping, one of them updated. With one list, a part added to the shot is
    automatically covered by the material and disjointness assertions.
    """
    parts = []

    # Ground. This REPLACES interior.drum_interior()'s band shell -- both
    # describe the same surface at the same radius, and emitting both would
    # z-fight across four and a half million square metres. Asserted below by
    # comparing group vocabularies, not by trusting this comment.
    gv, gt, gg, _gm = dg.visible_set(eye)
    parts.append(("ground", gv, gt, gg))

    for end in ("fore", "aft"):
        v, t, m = it.drum_end_cap(schema, profile, sector, end=end)
        parts.append((f"endcap_{end}", v, t, m["groups"]))

    v, t, m = it.drum_guideways(schema, profile, sector)
    parts.append(("guideways", v, t, m["groups"]))

    v, t, m = it.drum_spokes(schema, profile, sector)
    parts.append(("spokes", v, t, m["groups"]))

    v, t, m = ct.core_axis(schema, profile, sector)
    parts.append(("core", v, t, m["groups"]))

    v, t, m = tram.drum_trams(schema, profile, sector,
                              per_guideway=trams, glazed=True)
    parts.append(("trams", v, t, m["groups"]))

    # THE GARDEN'S TOWNSCAPE. It stands on the drum floor inside the settlement
    # arc at 93.6-144 deg (`garden.settlement_arcs`), so it is part of what the
    # eye reaches from the Garden floor in the same sense the ground is -- and
    # it was missing from this list, which is how four locations came to be
    # counted as lit off a frame their geometry is not in. 2,228 tri.
    v, t, spans = gd.townscape(schema, profile, sector)
    # `garden` reports (name, lo, hi) SPANS; every other part here reports one
    # name per triangle, which is what `write_obj` indexes. Expanded rather
    # than special-cased downstream, and asserted complete -- a span list that
    # missed a triangle would write an OBJ with an unnamed face, and an unnamed
    # face takes the fallback material silently.
    per_tri = [None] * len(t)
    for nm, lo, hi in spans:
        for i in range(lo, hi):
            per_tri[i] = nm
    if any(x is None for x in per_tri):
        raise ValueError(f"townscape: {per_tri.count(None)} triangles of "
                         f"{len(t)} are in no group span")
    parts.append(("townscape", v, t, per_tri))
    return parts


def omit_parts(parts, omit):
    """Drop named parts from a drum shot. The contribution measurement's tool.

    `DRUM_CALIBRATION[...]["contribution"]` is obtained by rendering a framing
    twice, once whole and once with one part left out, and counting the pixels
    that move. Until this existed that method was described in a comment and
    performed by hand-editing `drum_parts`, which means the numbers in the
    table could not be reproduced by running anything.

    AN UNKNOWN NAME IS A HARD ERROR, and that is the whole reason this is a
    function rather than a set difference. A typo would silently omit nothing,
    the two renders would come back identical, and the measurement would report
    0.00% -- indistinguishable from a part that genuinely contributes nothing,
    which is exactly the reading the table exists to make. A measurement whose
    failure mode is its own headline finding has to refuse to run.
    """
    if not omit:
        return parts
    want = {s.strip() for s in omit.split(",") if s.strip()}
    have = {p[0] for p in parts}
    unknown = sorted(want - have)
    if unknown:
        raise SystemExit(f"--omit: no such drum part {unknown}; the shot holds "
                         f"{sorted(have)}")
    return [p for p in parts if p[0] not in want]


def build_drum(args, out_dir):
    """Standing in the habitat drum: ground, end caps, trusses, spokes, core,
    trams. Everything the eye can reach from the Garden floor."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)

    # Camera first: the ground is LOD-resolved against the eye, so the eye has
    # to be known before the geometry is built. That is also true at runtime --
    # this is the same decision the streamer will make, made offline.
    if args.stand:
        ang, z = args.stand
        eye, up = dg.stand_on_ground(schema, profile, sector, ang, z,
                                     eye_h=_eye_h(args))
    elif args.eye:
        eye = tuple(args.eye)
        a = math.atan2(eye[1], eye[0])
        up = (-math.cos(a), -math.sin(a), 0.0)
    else:
        raise SystemExit("--shot drum needs --stand DEG,Z or --eye X,Y,Z")

    if args.look:
        ang, z = args.look
        aim, _ = dg.stand_on_ground(schema, profile, sector, ang, z,
                                    eye_h=_eye_h(args))
    elif args.target:
        aim = tuple(args.target)
    else:
        raise SystemExit("--shot drum needs --look DEG,Z or --target X,Y,Z")

    parts = drum_parts(schema, profile, sector, eye, trams=args.trams)
    built = sorted(p[0] for p in parts)
    parts = omit_parts(parts, getattr(args, "omit", ""))
    omitted = sorted(set(built) - {p[0] for p in parts})

    glbs, total, all_groups = [], 0, []
    for name, v, t, g in parts:
        obj = os.path.join(out_dir, f"{name}.obj")
        write_obj(obj, v, t, g)
        glb = to_glb(obj, os.path.join(out_dir, f"{name}.glb"))
        n, names = glb_triangles(glb)
        if n != len(t):
            raise ValueError(f"{name}: glb has {n} triangles, source has "
                             f"{len(t)}")
        total += n
        all_groups.extend(names)
        glbs.append(glb)

    runs = light_runs(schema, profile, sector, per_run=args.lights_per_run)
    lights = []
    per_light = light_energy(args.lights_per_run)
    att = (args.light_attenuation if args.light_attenuation is not None
           else LAMP_ATTENUATION)
    for run in runs:
        for p in run:
            lt = {"pos": list(p), "energy": per_light,
                  "colour": list(LAMP_COLOUR),
                  "range": args.light_range,
                  "attenuation": att}
            if args.light_kind == "spot":
                lt["kind"] = "spot"
                lt["aim"] = list(radial_aim(p))
                lt["angle"] = args.light_cone
            lights.append(lt)
    # Shadow casting is rationed, not free: an omni shadow is a cube map, so
    # each one re-renders the scene six times, and this renderer is a CPU. The
    # nearest few carry the shadows because they are the ones whose occluders
    # are on screen at a size where a shadow reads.
    order = sorted(range(len(lights)),
                   key=lambda i: sum((lights[i]["pos"][k] - eye[k]) ** 2
                                     for k in range(3)))
    n_shadow = (DRUM_SHADOW_LIGHTS if args.shadow_lights is None
                else args.shadow_lights)
    for i in order[:n_shadow]:
        lights[i]["shadow"] = True

    return {
        "shot": "drum",
        "scene": "res://scenes/drum.tscn",
        # PER-SHOT AMBIENT, and its absence here was a flag that did nothing.
        # `--ambient` is documented, is honoured by the exterior shot and by the
        # interior shot, and was silently dropped by this one: three renders at
        # 0.55, 0.30 and 0.15 came back with an IDENTICAL p5 of 0.0458. That is
        # the same defect as `--light-gain` on the exterior, found the same way
        # -- by disbelieving a number that did not move -- and it matters more
        # here, because ambient is what sets p5, and p5 is the statistic 13 of
        # the project's 17 exposures fail on.
        **({"ambient": args.ambient} if args.ambient is not None else {}),
        "glb": glbs,
        "triangles": total,
        "groups": sorted(set(all_groups)),
        "lights": lights,
        "camera": {"eye": list(eye), "target": list(aim), "up": list(up),
                   # Near plane at 0.15 m: the camera is a person's eye and
                   # things get close indoors. Far plane clears the drum's
                   # 2.6 km diagonal with room for the end cap behind it.
                   "fov": SHOT_FOV_DEG if args.fov is None else args.fov,
                   "near": 0.15, "far": 12000.0},
        "sun_from": None,
        "sector": sector,
        "floor_radius_m": dg.FLOOR_R,
        # WHAT THE SHOT COULD HAVE HELD, recorded so the self-test can check
        # DRUM_CALIBRATION's tables against the real list without paying 22
        # seconds for a geometry build on every run. `drum_parts` is the truth;
        # this is that truth written down by the code that ran it, which is not
        # a second copy in the sense that drifts -- it is regenerated by every
        # export. `omitted` is here so a measurement run's short export cannot
        # be mistaken for a part having been deleted from the shot.
        "parts": built,
        "omitted": omitted,
    }


# ---------------------------------------------------------------------------
# The interior shot
# ---------------------------------------------------------------------------
# LAYER 4 CANNOT START WITHOUT THIS. The material library declares three
# scenes; two of them had a .tscn. The interior scene has NINETY-SIX materials
# and 265 rules -- the largest of the three, 40% of the library -- and not one
# of them had ever been rendered, because there was no interior scene to render
# them in. Layer 3 was declared complete over surfaces nobody had seen.
#
# This is layer 4's equivalent of layer 0: infrastructure, not a location, and
# it has to exist before a single interior can be judged.

# Fittings the kit and the room generators already tag. Their PLACEMENT is
# sourced and built; what was missing is that they emit nothing.
LIGHT_GROUP_PREFIX = "light_"
# Two tagged spans of the same fitting closer than this are one lamp. 0.9 m
# spans a pilaster strip's seven bars (0.12 m pitch) without reaching the next
# pilaster, which the kit puts a portal bay apart.
FIXTURE_MERGE_M = 0.9

# A FITTING IS A CONNECTED BODY, AND A TAGGED SPAN IS NOT ONE. `to_spans` cuts
# a per-triangle group list into contiguous runs, so a module that emits all of
# one fitting family in one go emits ONE span however many lamps it built --
# and `fixture_lights` used to put a single source at that span's centroid.
# Measured across every lit room, that lost three quarters of the station's
# lamps and put several of the survivors in mid-air:
#
#   room             fitting            spans  bodies  what the span really is
#   council_chamber  light_house_cove       1       1  a 33.6 m continuous cove
#   cnc              cc_light_strip         1       4  four 8.6 m wall courses
#   zocalo           zoc_rib_lamp           6      30  five lamps per rib -- the
#                                                      measured number
#   zocalo           light_downlight        6      18  three per bay
#   docking_bays     bay_lamp              13      39  three per bay
#
# The single `cc_light_strip` lamp sat 6.92 m from the nearest strip with a
# measured range of 3.5 m -- twice its own reach away from the fitting it was
# supposed to be, in the middle of a room the measurement says stays dark.
#
# Welded by POSITION rather than by vertex index, because none of these
# generators shares indices between primitives: `council_chamber._M.quad`
# appends four fresh vertices per quad, so index connectivity would call one
# continuous cove twelve fittings and multiply its flux by twelve. Position
# connectivity gets both cases right -- the cove's segments meet exactly and
# are one body; two rib lamps 2 m apart are two.
FIXTURE_WELD_M = 1e-4

# A FITTING LONGER THAN ITS OWN THROW CANNOT BE A POINT: the far end of the
# fitting is beyond the near end's reach, so no single position stands for it.
# One point at the centroid of the council chamber's cove sat 3.89 m out in the
# room facing the cove and washed it point-blank -- the bright white arc across
# the top of `docs/engine-council.png`, which survived dropping the material's
# own emission_energy to 1.2 because the lamp, not the emission, was drawing it.
#
# So an extended fitting is SAMPLED, exactly as the drum's 2.6 km light runs
# are, and for the same stated reason: "the sampling density is a cost decision
# and must not be a look decision, so energy is normalised by count" (see
# RUN_ENERGY). Sampling a fitting therefore never changes how much light is in
# the room, only where it comes from.
#
# The density is the drum's own, measured off the rig that has been rendering
# since session 2j: `light_runs` samples a 2,586 m sector with ten omnis of
# range 1,100 m, i.e. one sample per 258.6 m against an 1,100 m reach --
# range / 4.25. Rounded to 4 here, which is slightly denser, and denser is the
# safe direction when the energy is normalised.
#
# WHERE THE THRESHOLD SITS, measured over every lit fitting in the library as
# body extent / its own measured range:
#
#   light_stall_festoon 0.04   light_wall_strip_bank 0.09   light_downlight 0.22
#   light_ceiling_batten 0.26  light_soffit_blade 0.31   light_wall_course 0.69
#   ---------------------------------------------------- 1.0 -------------------
#   light_house_cove 1.33      cc_light_strip 2.47
#
# Two fittings are extended and fourteen are not, with the nearest of each 31%
# and 33% clear of the line. A fitting that drifts across it is a fitting whose
# geometry has changed shape, which is worth a re-render either way.
EXTENDED_SAMPLES_PER_RANGE = 4.0
# Cost bound, not a look bound. A 200 m light strip at range/4 would emit
# hundreds of omnis and every one of them re-lights the scene; past this the
# pitch is widened instead. Nothing in the library reaches it -- the cove takes
# 8 samples and a wall course 10 -- so it is a guard against a future fitting,
# and because the energy is normalised, hitting it costs fidelity and not
# brightness.
EXTENDED_SAMPLE_CAP = 24
# Interior lights need an interior RANGE. The first render used the drum's
# 1100 m default in a 21.6 m corridor, so all 117 sources reached every surface
# with no falloff and the frame came back pure white. A corridor fitting lights
# its own bay and the two either side of it; beyond that the next fitting takes
# over, and that hand-off IS the rhythm the reference frames show.
INTERIOR_LIGHT_RANGE_M = 7.0

# WHICH FITTINGS ACTUALLY EMIT LIGHT, measured off the reference frames in
# session 3n and recorded in docs/layer4-lighting/corridor_kit.json.
#
# THE FIRST INTERIOR RENDER MADE EVERY TAGGED FITTING A REAL SOURCE and came
# back looking like a clean modern hospital. It is not a tuning error. Of the
# four fittings interior_kit builds, exactly ONE lights anything:
#
#   light_downlight       omni, 2650 K, range 1.2 m, no shadow
#   light_pilaster_strip  EMISSIVE ONLY -- it is the brightest thing on the
#                         wall and it illuminates nothing. Two independent
#                         tests in `grey level 1.webp`: the deck directly
#                         beneath it reads balanced L 0.29-0.35 against a
#                         mid-corridor deck field of 0.446, i.e. DARKER; and
#                         materials.py's own PROVENANCE has the pilaster face
#                         at V 0.301 against a wall plate three metres away at
#                         V 0.295.
#   light_portal_head     EMISSIVE ONLY, same finding.
#
# So a corridor is lit by a handful of weak warm downlights and read by a lot
# of cool emissive trim. That contrast is the room. Treating the trim as
# lighting floods the fill and destroys it.
#
# Absent means EMISSIVE ONLY, which is the default: a fitting has to be
# measured to become a source. Fields: kind ("omni" or "spot"), colour_linear,
# energy_rel, range_m, shadow, and for a spot the cone half-angle in degrees.
#
# The eleven room fittings below come from docs/layer4-lighting/*.json exactly
# as the four kit fittings above do. Two things had to be DERIVED rather than
# read, and both are stated on the entry: a range measured in an 18 m docking
# bay is wrong in a 7.5 m plant hall, and a cone angle is almost never given
# directly -- it falls out of the pool diameter or the fitting spacing over the
# mounting height.
FIXTURE_LIGHTING = {
    # --- the corridor kit -------------------------------------------------
    "light_downlight": {"kind": "omni", "colour": (1.000, 0.420, 0.133),
                        "energy_rel": 1.00, "range_m": 1.2, "shadow": False},
    # --- rooms.py, industrial and store -----------------------------------
    # bay_flood: measured range 30 m at a 13.0 m emitting height in an 18 m
    # bay. Scaled to the tallest room archetype's 7.5 m ceiling -- 30 x 7.5/18
    # -- because an unscaled 30 m range in a 12 m room is no falloff at all,
    # which is the exact defect that made the first interior render white.
    # Cone: the frame gives 28-35 deg at 18 m, and the same floor coverage from
    # 2.4x closer needs it wider; 35 deg is the top of the measured range and
    # is taken rather than opened further.
    "light_highbay": {"kind": "spot", "colour": (0.850, 0.830, 1.000),
                      "energy_rel": 1.00, "range_m": 12.5, "shadow": True,
                      "angle_deg": 35.0},
    # --- rooms.py, transit ------------------------------------------------
    # concourse_deck_spot, measured: range 4 m, and a half-angle stated
    # outright -- 12.3 deg at a 3.6 m mount for a 1.57 m pool.
    "light_platform_pool": {"kind": "spot", "colour": (0.850, 1.000, 0.870),
                            "energy_rel": 1.00, "range_m": 4.0, "shadow": True,
                            "angle_deg": 12.3},
    # --- rooms.py, hospitality --------------------------------------------
    # bar_pendant_lamp, measured: range 3.5 m, one per table at 2.2 m spacing.
    # Cone from the shade: hung below standing eye height (~1.9 m) over a
    # 1.20 m table at 0.74 m, so atan(0.60 / 1.16) = 27.4 deg.
    "light_pendant": {"kind": "spot", "colour": (1.000, 0.554, 0.393),
                      "energy_rel": 1.00, "range_m": 3.5, "shadow": True,
                      "angle_deg": 27.4},
    # --- rooms.py, worship ------------------------------------------------
    # cc_dais_key, measured: range 9 m, ~3.5 m above the dais, cone wide
    # enough to cover a 4.6 m dais plus its apron -- atan(2.3 / 3.5) = 33.3.
    "light_dais_key": {"kind": "spot", "colour": (1.000, 0.760, 0.556),
                       "energy_rel": 1.00, "range_m": 9.0, "shadow": True,
                       "angle_deg": 33.3},
    # --- rooms.py, worship and research -----------------------------------
    # cc_wall_course, measured: omni, range 3.5, energy_rel 0.44, and the
    # placement is explicit that it throws OUTWARD and the room centre stays
    # dark -- which a 3.5 m range on a 7 m half-width delivers by itself.
    "light_wall_course": {"kind": "omni", "colour": (0.243, 0.546, 1.000),
                          "energy_rel": 0.44, "range_m": 3.5, "shadow": False},
    # --- rooms.py, medical, research and detention ------------------------
    # fa_batten, measured: range 12 m, hung 4-5 m above the tables. Scaled to
    # a 3.0 m medical ceiling by the same argument as the high bay:
    # 12 x 3.0/5.0 = 7.2.
    "light_ceiling_batten": {"kind": "omni", "colour": (1.000, 0.980, 1.000),
                             "energy_rel": 0.90, "range_m": 7.2,
                             "shadow": True},
    # DECLARED, not measured: the brig has no reference frame. It takes the
    # batten's colour behind a guard, at half its energy and half its reach,
    # because a cell block is the one interior that should be lit adequately
    # and not well. See materials.light_ceiling_batten.
    "light_cage_lamp": {"kind": "omni", "colour": (1.000, 0.980, 1.000),
                        "energy_rel": 0.45, "range_m": 4.0, "shadow": False},
    # --- rooms.py, commerce -----------------------------------------------
    # zoc_downlight_overhead, measured: range 12 m from 7.2 m, and the
    # measurement states the conclusion for us -- spacing/height = 0.375, the
    # pools MERGE, so the half-angle is at least 50 deg.
    "light_market_pool": {"kind": "spot", "colour": (0.694, 0.982, 1.000),
                          "energy_rel": 1.00, "range_m": 12.0, "shadow": True,
                          "angle_deg": 50.0},
    # zoc_stall_light, measured: omni, range 2.5, energy_rel 0.19. Sixty to a
    # hundred bulbs a stall, so `FIXTURE_MERGE_M` does most of the work here --
    # the geometry keeps every bulb and the rig gets one lamp per 0.9 m.
    "light_stall_festoon": {"kind": "omni", "colour": (1.000, 0.492, 0.420),
                            "energy_rel": 0.19, "range_m": 2.5,
                            "shadow": False},
    # --- rooms.py, office -------------------------------------------------
    # wr_wall_strip_bank and wr_soffit_blade, both measured omni at range 4.
    "light_wall_strip_bank": {"kind": "omni", "colour": (1.000, 0.764, 0.516),
                              "energy_rel": 0.61, "range_m": 4.0,
                              "shadow": False},
    "light_soffit_blade": {"kind": "omni", "colour": (1.000, 0.703, 0.440),
                           "energy_rel": 0.92, "range_m": 4.0,
                           "shadow": False},

    # --- the bespoke modules ----------------------------------------------
    # These five are the fittings the bespoke generators ALREADY BUILD and that
    # the committed measurements already describe. Nothing here is new
    # geometry, no colour is invented, and -- unlike the room fittings above --
    # NO RANGE NEEDED SCALING: every one was measured in the very volume its
    # module builds, so the number transfers as read.
    #
    # bay_flood, measured in reference/03-sector-blue/dock.webp: spot, 7391 K,
    # range 30 m, spacing 11 m, SHADOW, cone half-angle 28-35 deg, emitting
    # face at BAY_H_M - GIRDER_D_M - LAMP_DROP_M = 13.0 m. The 30 m range is
    # right here and would be wrong anywhere else: docking_bay.py's BAY_H_M
    # really is 18 m. 35 deg is the top of the measured range and is taken
    # rather than opened further.
    "bay_lamp": {"kind": "spot", "colour": (0.850, 0.830, 1.000),
                 "energy_rel": 1.00, "range_m": 30.0, "shadow": True,
                 "angle_deg": 35.0},
    # zoc_rib_lamp, measured in reference/04-sector-red/zocalo.webp: omni,
    # 2990 K, energy_rel 0.30, range 6 m, no shadow. Five per rib at the
    # measured (x, y) intrados positions, ribs at 5.4 m pitch. This is the
    # concourse's warm register and the only thing in the Zocalo that is not
    # cool.
    "zoc_rib_lamp": {"kind": "omni", "colour": (1.000, 0.398, 0.233),
                     "energy_rel": 0.30, "range_m": 6.0, "shadow": False},
    # zoc_stall_light, measured in the same frame by blob analysis -- 64
    # discrete bulbs at a median spacing of 2.6 bulb diameters: omni, 3800 K,
    # energy_rel 0.19, range 2.5 m. FIXTURE_MERGE_M does the heavy lifting: the
    # geometry keeps every bulb and the rig gets one lamp per 0.9 m.
    "zoc_stall_light": {"kind": "omni", "colour": (1.000, 0.492, 0.420),
                        "energy_rel": 0.19, "range_m": 2.5, "shadow": False},
    # bar_pendant_lamp, measured in reference/04-sector-red/Doug's Dugout.webp:
    # spot, 3900 K, range 3.5 m, spacing 2.2 m, SHADOW, one per table. Cone
    # from the shade itself -- hung below standing eye height (~1.9 m) over a
    # 1.20 m table at 0.74 m, so atan(0.60/1.16) = 27.4 deg. This is the
    # module's own fitting, which hospitality.py already places and asserts.
    "bar_pendant_lamp": {"kind": "spot", "colour": (1.000, 0.554, 0.393),
                         "energy_rel": 1.00, "range_m": 3.5, "shadow": True,
                         "angle_deg": 27.4},
    # cc_wall_course, measured raw in reference/03-sector-blue/comand and
    # contorl.webp: omni, 22000 K, energy_rel 0.44, range 3.5 m, no shadow.
    # command_control.py's group is `cc_light_strip` and the measurement is of
    # that object. The placement note is the reason a 3.5 m range on a 7 m
    # half-width is correct rather than mean: the courses throw OUTWARD and the
    # centre of the room stays dark.
    "cc_light_strip": {"kind": "omni", "colour": (0.243, 0.546, 1.000),
                       "energy_rel": 0.44, "range_m": 3.5, "shadow": False},
    # plant.py's flood: bay_flood again, and the ONE range in the project that
    # transfers with no arithmetic at all. It was measured at 30 m in an 18 m
    # docking bay and a five-deck plant bay is 5 x DECK_PITCH_M = 18.0 m.
    # Its companion, light_service_tube, is measured EMISSIVE ONLY and is
    # already in the table above by that name -- the cold blue tubes are what
    # you see in a service space and they light nothing.
    # alien_sector.CAST_FITTINGS, and it lives THERE because that is the module
    # that measured it. Copied here because membership of this table is the
    # gate and a dict in another file is not membership; alien_sector's own
    # self-test asserts the two agree, so they cannot drift.
    #
    # Colour measured RAW off the descending shafts and corroborated by the
    # floor grating -- the same source seen twice, agreeing in R:G to 0.7%.
    # Range 4.0 m is derived from the module's own dimensions: the grille hangs
    # at GALLERY_H_M 3.4 m and the deck's far corner is sqrt(3.4^2 + 2.1^2) =
    # 4.00 m away, so it is the reach that lights the whole floor and no more.
    # Cone 30 deg against the 31.7 deg that covers wall to wall, so the last
    # 0.14 m at the skirting stays dark -- the frame's darkest surfaces are the
    # pier feet.
    #
    # THE LIGHT HANGS ON THE TROUGH AND NOT ON THE GRILLE, which cost a render
    # to learn: `alien_lattice` is fifty-six separate bars and `fitting_bodies`
    # correctly reads each as its own luminaire, so the frame came back with
    # 126 lamps at 7.10x its reference. A grille is a DIFFUSER; the source is
    # behind it. Eight troughs where there were fifty-six bars.
    # customs.CAST_FITTINGS -- the ARRIVAL HALL WALL BAND, and it is here for
    # the reason the coffer is not. OMNI rather than spot because the wall
    # reads brighter both ABOVE the band (measured, 1.9-2.0x over 0.09 of frame
    # height) and below it before the crowd occludes the deck, so it throws in
    # both directions off the wall face. Colour is the family's measured
    # (0.956, 1.000, 0.895) at 6200 K from corridor_kit.json's
    # `light_pilaster_strip`; the customs frame's own reading of its cells is
    # violet-leaning and was rejected, with the argument on
    # materials.light_arrival_strip. energy_rel 0.83 is 0.839/0.905, this
    # band's balanced V p99 against the screens' -- the same normalisation the
    # withdrawn coffer proposal used, applied to the family that survived.
    "customs_light_strip": {"kind": "omni", "colour": (0.956, 1.000, 0.895),
                            "energy_rel": 0.83, "range_m": 3.5,
                            "shadow": False},
    "alien_ceiling_lamp": {"kind": "spot", "colour": (1.000, 0.675, 0.060),
                           "energy_rel": 1.00, "range_m": 4.0, "shadow": True,
                           "angle_deg": 30.0},
    "light_plant_flood": {"kind": "spot", "colour": (0.850, 0.830, 1.000),
                          "energy_rel": 1.00, "range_m": 30.0, "shadow": True,
                          "angle_deg": 35.0},
    # cc_house_wash, the council chamber's whole lighting scheme: 6300 K,
    # range 18 m, shadow. Measured as DIRECTIONAL -- a broad soft wash -- and
    # emitted here as a ring of omnis, because the rig derives a light from a
    # piece of geometry and a cove is a real object at a real place while a
    # directional light is a direction with no position. Twelve omnis round the
    # rear arc at 18 m reach is the same wash by another construction.
    "light_house_cove": {"kind": "omni", "colour": (1.000, 0.966, 0.944),
                         "energy_rel": 0.35, "range_m": 18.0, "shadow": False},
}

# WHERE A ROOM IS ON THE STATION IS NOT PART OF ITS FITTING'S NAME, and the
# table above is an EXACT-NAME lookup, so until this function existed every
# fitting inside every room of an assembled deck was invisible to the light rig.
#
# `deck.build_deck` prefixes each room's own group names with the place key and
# a double underscore -- `docking_bays__light_highbay` -- so the engine can
# address one room's meshes among six rooms' worth in a single mesh, and so a
# door leaf can be found and slid. That prefix is an ADDRESS. The fitting is
# still `light_highbay` and is still the thing the measurement in the table was
# taken of.
#
# Measured on blue/0/0, the first deck `station/walkable.py` walks: 822 corridor
# spans matched (the kit's, which carry no prefix) and 28 room spans across six
# rooms matched NOTHING -- every high bay, every deck channel, every downlight
# inside a room. The deck rendered with its corridor lit and its rooms black,
# and no assertion could fire, because "a room with no tagged fitting comes back
# BLACK, which is correct and legible" is the documented behaviour of the rig
# and is indistinguishable from this.
#
# FIXED AT THE LOOKUP AND NOT IN THE TABLE, deliberately. Pre-expanding 87 rooms
# x N fittings into FIXTURE_LIGHTING would be a second copy of something
# `deck.py` computes, and it would go stale the first time a room moved decks --
# the same defect as a table of hand-placed lamp positions, which is what
# `fixture_lights`' own docstring exists to argue against.
#
# `materials.py`'s rules already work this way and always have: `render_shot.gd`
# matches a mesh name by SUBSTRING, so `docking_bays__light_highbay` takes the
# high bay's material without anything being told about docking bays. The light
# rig was the one place on the path that asked for an exact string.
def fixture_key(name):
    """The FIXTURE_LIGHTING entry a tagged span's name refers to, or None.

    An exact name wins outright; otherwise the address is stripped from the
    front. Split on the LAST `__` rather than the first, because the address is
    a prefix and the fitting name is the tail -- and `rsplit` on a name with no
    `__` returns the name unchanged, so the two cases need no branch.
    """
    if name in FIXTURE_LIGHTING:
        return name
    base = name.rsplit("__", 1)[-1]
    return base if base in FIXTURE_LIGHTING else None


# THE CUSTOMS COFFER IS DELIBERATELY ABSENT AND THE WALL BAND IS NOT. What
# follows was written when neither was in the table. It is still right about
# the COFFER, which is the fitting it is about; `customs_light_strip` was added
# later from a separate measurement and is above.
#
# THE COFFER COST A RENDER TO BE SURE. The arrival
# hall's ceiling coffer looked like the obvious next entry: materials.py's
# light_ceiling_grid measured its colour on the fitting itself, and the same
# frame ranks its three source families by balanced peak -- screens 0.99, wall
# strips 0.82, ceiling grid 0.55 -- which reads as an energy_rel of 0.56.
# Given a light, customs.hall() emits 210 separate coffers, the frame came back
# at 18.9x its reference with 14% of it clipped, and the exposure needed to
# rescue it was 0.07.
#
# The real answer was already written in that material's own source note: the
# grid is "ambient decoration rather than a task light", ranked LAST of the
# three families in its frame. It is emissive-only, for the same reason the
# pilaster strip is, and customs therefore has no measured cast source yet --
# so it is not at layer 4, which is the honest count rather than a rescued one.
#
# EVERYTHING NOT IN THAT TABLE IS EMISSIVE ONLY, and for rooms.py that is:
# light_service_tube, light_bar_backlight, light_indicator_red and
# light_deck_channel. All four are recorded `emissive_only` in the measured
# JSON. The trim glows and casts nothing; treating it as lighting is what
# flooded the first interior render and destroyed exactly the contrast the
# reference frames are made of.

# ---------------------------------------------------------------------------
# THE SOFT FILL -- the key a corridor has and its fittings do not
# ---------------------------------------------------------------------------
# docs/layer4-lighting/corridor_kit.json, `corridor_soft_fill`, and its own
# reasoning field says what it is:
#
#   "THIS IS THE MOST IMPORTANT ENTRY IN THE SET AND IT IS THE ONE THE KIT DOES
#    NOT HAVE ... The light therefore is not in the fittings ... Build the room
#    this way round and it reads as the show; build it from the fittings and it
#    will be a dark corridor with three bright dots."
#
# It sat in that file unimplemented for six sessions, because `FIXTURE_LIGHTING`
# has no `directional` kind and `fixture_lights` derives a light's position from
# a TAGGED SPAN -- and a soft fill has no fitting to hang on. The measurement
# says so itself: "Not a fitting. A broad soft source, above and slightly ahead
# of the viewer."
#
# MEASURED BEFORE IT WAS BUILT, and this is the evidence that the corridor could
# not be fixed from the fitting table. On the assembled deck, blue/0/0:
#
#   --fixture-energy 3.0 -> 0.3   frame median moves 6%, p5 not at all
#   --ambient 1.30 -> 0.40        frame median moves 70%
#
# The corridor was lit essentially entirely by a FLAT AMBIENT, and a flat
# ambient gives every surface the same irradiance whichever way it faces. That
# is exactly the shape of the defect: measured on `docs/engine-deck-corridor.png`
# the deck sat at x0.57 of the lit wall and the soffit at x0.89, where the show
# is at x2.49 and x0.23-0.32. Everything was pulled toward the wall because
# nothing in the scene knew which way was down.
#
# ---------------------------------------------------------------------------
# WHY A RING OF SPOTS AND NOT A DirectionalLight3D
# ---------------------------------------------------------------------------
# ON A SPUN RING "DOWN" IS RADIALLY OUTWARD from the spin axis -- `player.gd`'s
# `gravity_dir()` is the authority and returns `(x, y, 0)` normalised. A ring
# corridor covers up to 344 degrees, so "down" ROTATES THROUGH 344 DEGREES along
# it. A Godot DirectionalLight3D is one direction for the whole world, so a
# single one is right at one angle of the ring, grazing 90 degrees away and
# UNDER the deck 180 degrees away. Twelve of them aimed at twelve radial
# directions do not fix it either: a directional lights the whole scene, so
# twelve of them is twelve overlapping washes, which is an ambient term again --
# the very thing this replaces.
#
# The precedent is already in FIXTURE_LIGHTING and it was the right call there
# too: `light_house_cove` is "measured as DIRECTIONAL -- a broad soft wash --
# and emitted here as a ring of omnis, because the rig derives a light from a
# piece of geometry and a cove is a real object at a real place while a
# directional light is a direction with no position."
#
# So: a run of SHADOWLESS SPOTS on the corridor's own centreline, mounted
# `SOFT_FILL_HEIGHT_M` above the deck -- above the ceiling, out of shot, which is
# what "off-camera key" means -- and aimed radially outward by `radial_aim`, the
# same function every deck spot already uses. Three consequences, all wanted:
#
#   * a spot's cone can be sized to the corridor and therefore CANNOT SPILL into
#     the rooms opening off it, which have their own measured fill. An omni at
#     the same place would light all 87 of them.
#   * the ceiling's visible face points radially OUTWARD, i.e. away from a source
#     that is inward of it, so the fill does not touch the soffit. That is the
#     x0.23-0.32 rung, and it comes from the geometry rather than from a number.
#   * shadow is False, which is the measurement ("shadow": false) and is also
#     what lets the source sit outside the corridor shell at all.
#
# THE PLACEMENT IS DERIVED FROM THE COLLISION META -- the same dict the shell a
# player stands on is built from (`floor_r_m`, `half_w_m`, `z_m`, `arc_deg`,
# `start_deg`). CLAUDE.md's fourth hard rule applied to light: the key cannot
# drift off the floor it is keying, because it is computed from that floor.
#
# ---------------------------------------------------------------------------
# THE TWO NUMBERS, AND WHERE EACH COMES FROM
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# THE AMBIENT DOES NOT COME DOWN, AND THE DERIVATION THAT SAID IT SHOULD IS
# RECORDED HERE BECAUSE IT WAS OVERTURNED BY A RENDER
# ---------------------------------------------------------------------------
# Take the show's own ladder in docs/reference-values.md section 1, divide out
# the albedos materials.py already holds, and a split falls out in one line.
# Write A for the isotropic ambient irradiance and F for the fill's irradiance
# on an up-facing surface:
#
#   deck   faces the fill        E = A + F
#   wall   vertical, sees part   E = A + f*F
#   soffit faces away            E = A
#
#   soffit / wall, luminance  0.228-0.321 (rungs 2 and 3)
#   deck   / wall, luminance  2.486       (rung 16)
#   albedos: kit_wall_plate 0.460, kit_deck 0.400, kit_soffit 0.2526
#
#   E_soffit/E_wall = 0.27 / (0.2526/0.460) = 0.49
#   E_deck  /E_wall = 2.486 / (0.400/0.460) = 2.86
#
# Two equations, two unknowns (A/F and f), and they are consistent:
#
#   A / (A + f*F) = 0.49  ->  A ~= f*F
#   (A + F) / (A + f*F) = 2.86, with A = f*F  ->  (1+f)/(2f) = 2.86
#                                             ->  f = 0.212
#
# That says the ambient should come down to 0.49 of what it is, because the
# soffit sees the isotropic term AND NOTHING ELSE, so soffit-over-wall IS the
# ambient's share of the wall.
#
# IT IS WRONG HERE, AND THE FRAME SAYS SO. Its premise is that the only thing
# darkening a soffit is that it faces away from the key. Measured on our own
# corridor, with the boxes recorded in SOFT_FILL_LADDER_BOXES:
#
#   docs/engine-deck-corridor.png, BEFORE any of this   soffit x0.23 of the wall
#   the show                                            soffit x0.23-0.32
#
# The soffit rung was ALREADY IN BAND. It is dark because it is a recessed
# coffer under 2.2-intensity SSAO, not because the key misses it -- and the
# show's soffit is a recessed coffer too, so the same mechanism is probably what
# put it at 0.23-0.32 there. Halving the ambient took ours to x0.19 and then
# x0.15, i.e. it broke a rung that was right in order to satisfy a model of why
# it was right.
#
# So the fill is ADDITIVE and the ambient is untouched. Two checks that this is
# not just convenient: `--soft-fill 0` then reproduces the committed baseline
# exactly, which is what makes it a usable negative control; and the corridor's
# LEVEL was never too high to begin with -- the baseline sits at x0.91 of the
# reference against a x1.40 +/-25% window, i.e. BELOW range. The missing light
# was never a quantity of ambient, it was a direction.
#
# `SOFT_FILL_ENERGY` and `SOFT_FILL_HEIGHT_M` COULD NOT BE DERIVED and were
# measured the way ROOM_EXPOSURE was: render, measure the ladder, scale. The
# algebra above fixes the RATIO f = 0.212 that the height has to deliver, and a
# point source on the centreline at height H over a corridor of half-width 1.3 m
# gives f = 1.3*H^2 / (1.3^2 + (H-1.5)^2)^1.5 at mid-wall, which solves to
# H ~ 10 m. That model ignores the pilaster strips, the portal heads, the
# downlights, ambient occlusion and the fact that the source is a run and not a
# point, all of which the render has, so the value below is the RENDERED one and
# the derivation stands only as the reason the number is near 10 and not near 3.
# See SOFT_FILL_CALIBRATION for the frames that set it.
SOFT_FILL = {
    # Every field here is `corridor_soft_fill` verbatim except `range_m` and
    # `angle_deg`, which the record does not carry (a directional has neither)
    # and which are derived below from the corridor's own dimensions.
    "colour": (0.738, 0.955, 1.000),   # linear, from the unfitted right wall
    "energy_rel": 2.5,                 # fill / brightest fitting, on the wall
    "shadow": False,
}
# AND `energy_rel` IS RECORDED HERE AND DELIBERATELY NOT USED, which is worth
# saying because every other entry in FIXTURE_LIGHTING does use its own. 2.5 is
# a ratio of DELIVERED IRRADIANCE ON A WALL between the fill and the brightest
# fitting -- "the fill delivers L 0.27 and the brightest fitting adds at most
# +0.11 at its own peak". `light_downlight` throws that +0.11 from 0.37 m at a
# 1.2 m range; the fill throws from 10 m at an 18 m range through a different
# falloff and a cone. Multiplying a Godot energy by 2.5 would be treating two
# incomparable numbers as one, which is the mistake BESPOKE_EXPOSURE exists to
# warn about. What transfers is the measurement's SHAPE -- colour, direction,
# and that the fill dominates the fittings -- and the fittings-versus-fill test
# above confirms the last of those from our own render: dropping
# `--fixture-energy` by 10x moves the frame's median 6%.
# Above the DECK, not above the ceiling: the deck is what the collision meta
# gives and what the fill is aimed at. The corridor's ceiling is 2.81 m, so the
# source sits 7 m clear of it and is never in shot.
#
# 10 m IS THE `f = 0.212` THE LADDER ASKED FOR, and it is the same answer from
# two different falloff laws, which is why it is trusted. Godot's spot decays as
# `d^-attenuation` with attenuation 1.0, so for a source on the centreline at
# height H the wall-to-deck irradiance ratio is `hw*H / (hw^2 + (H-h)^2)`, and
# the anchor wall course sits at h = 2.20 m -- read off `grey level 1.webp`,
# whose deck images at y 0.785 and whose wall top images at y 0.075, putting the
# ALBEDO_ANCHOR box's centre at 0.732 of a 3.0 m wall. That solves to H = 10.0.
# Under inverse square it solves to H = 10 as well. Six metres, the first value
# tried, gives f = 0.48 -- and f > 1/2.86 makes the deck rung UNREACHABLE at any
# energy, because deck/wall tops out at 1/f.
SOFT_FILL_HEIGHT_M = 10.0
# Three times the mount height. Godot's range is a CULLING WINDOW, not a
# falloff -- see `_soft_fill_light` -- and at d/r = 1/3 it costs 2.4%.
SOFT_FILL_RANGE_M = 3.0 * SOFT_FILL_HEIGHT_M
# Godot's spot angular term is `1 - rim^k`, rim running 0 on the axis to 1 at
# the cone edge. render_shot.gd's 0.6 is the measured `concourse_deck_spot` --
# "these pools have edges, and they are not razors" -- and it is a curve that
# starts falling immediately: at rim 0.5 it is already down to 0.34. A fill is
# not a pool. k = 4 holds 0.99 out to rim 0.56 and then drops, which is the
# flat-topped cone a broad source needs.
SOFT_FILL_ANGLE_ATTENUATION = 4.0
# How much of the axial value the corridor's WORST-LIT corner may lose to the
# cone. The cone half-angle is then solved from it rather than chosen -- see
# `soft_fill_cone_deg` -- so a corridor of another width or a different mount
# height re-derives its own cone instead of inheriting this one's.
SOFT_FILL_CORNER_FLOOR = 0.90
# How far past the corridor wall the cone may land, in metres. A shadowless
# source cannot be stopped by a wall, so the fill reaches the floor of whatever
# room is on the other side; this is the bound on how much of it. 2.0 m is one
# door width (`interior_kit.PROVISIONAL["door_width_m"]` is 1.50) plus its
# frame, i.e. the fill may not throw further into a room than an open door
# does. It is an ASSERTED bound and not a description: the self-test fails the
# build if the solved cone exceeds it, which is what stops the cone quietly
# opening up when some other constant moves.
SOFT_FILL_MAX_SPILL_M = 2.0
# THE CONE IS SIZED TO THE WALL PLATE AND NOT TO THE WALKABLE WIDTH.
# `collision_meta["half_w_m"]` is 1.0806 m on blue/0/0 and it is the NARROWEST
# clearance a body has over its own height -- measured between pilasters, which
# project 0.17 m into the corridor. The surface the fill has to reach is the
# wall plate behind them, at `corridor_width_m / 2` = 1.30 m. Sizing the cone to
# the shell would under-reach the wall by 0.22 m at exactly the place the ladder
# is anchored.
def _corridor_half_w_m(meta):
    import interior_kit as kit                                  # noqa: PLC0415
    return max(meta["half_w_m"], kit.PROVISIONAL["corridor_width_m"] / 2.0)
# HALF a corridor bay -- `interior_kit.PROVISIONAL["portal_spacing_m"] / 2`,
# and the halving is the wall's doing. The cone has to hold the far top corner
# of a whole BAY, so its half-angle grows with the pitch, and its footprint on
# the deck grows with it: at the 3.6 m bay the cone is 22.9 degrees and spills
# 2.9 m past each wall into the rooms, at 1.8 m it is 16.5 degrees and spills
# 1.7 m. Halving the pitch buys back most of the spill for 353 more lights on a
# deck, which the clustered renderer absorbs -- measured below.
SOFT_FILL_PITCH_M = 1.8
# The one free scalar, set by rendering. See SOFT_FILL_CALIBRATION.
SOFT_FILL_ENERGY = 12.0

# WHICH SPACES HAVE ONE, and the answer is only the one that was measured.
# corridor_kit.json records `concourse_soft_fill` (energy_rel 0.35) and
# `service_soft_fill` (0.20) as well, and both are real measurements -- but the
# ambient share above is derived from the RESIDENTIAL corridor's ladder and the
# concourse and service classes sit at ambient ratios 0.12 and 0.06 against its
# 0.30. Applying one share to all three would be the mistake BESPOKE_EXPOSURE is
# written to warn about, so the other two stay unbuilt and are named here rather
# than left to be rediscovered.
SOFT_FILL_SPACES = ("corridor", "junction")

# THE LADDER'S BOXES, as data. docs/reference-values.md section 6.4 measured the
# same comparison and recorded its boxes nowhere, so the one number this whole
# module exists to move -- the deck against the lit wall -- could not be
# recomputed by anyone who came after. These are fractions of the frame, picked
# once by drawing them on `docs/engine-deck-corridor.png` and LOOKING, and they
# land on the same elements in the deck shot and in `--shot interior --room
# corridor` because the two frame the corridor the same way.
#
# One of them was wrong for two renders and the failure is instructive: the
# first "soffit" box, at (0.230,0.120)-(0.320,0.200), landed on a near-field
# PILASTER FACE rather than on the overhead, and read x0.89 -- which reproduced
# section 6.4's own "ceiling / soffit ... OURS 1.12" and so looked corroborated.
# The overhead was in band the whole time. A box picked off a number instead of
# off the picture is a measurement of nothing.
SOFT_FILL_LADDER_BOXES = {
    "lit wall plate (ANCHOR)": (0.320, 0.355, 0.400, 0.430),
    "lit wall plate, right":   (0.610, 0.355, 0.690, 0.430),
    "soffit / ceiling":        (0.400, 0.115, 0.600, 0.190),
    "deck field":              (0.430, 0.800, 0.570, 0.900),
    "deck beside the wall":    (0.330, 0.745, 0.410, 0.770),
}

SOFT_FILL_CALIBRATION = """
Set on `--shot deck --deck blue/0/0 --at docking_bays` at 1280x720 -- the
framing docs/engine-deck-corridor.png is taken at -- measured with
SOFT_FILL_LADDER_BOXES against docs/reference-values.md section 1's ladder.
Ratios are to the lit wall plate; the SHOW row is that section's rungs 2/3
and 16. Frame median is `tools/measure_frame.py --against
"reference/10-interiors-generic-kit/grey level 1.webp"`.

  fill energy   deck field   soffit      frame median   distribution gate
  ---------------------------------------------------------------------------
   0 (before)      x0.65      x0.23         x0.91        FAIL -- p5 x0.77
   4               x1.37      x0.21         x1.00        (not gated)
  10               x2.29      x0.20         x1.07        PASS, every band
  12 (SHIPPED)     x2.59      x0.20         x1.09        PASS, every band
  SHOW             x2.49      x0.23-0.32

`--shot interior --room corridor` moves the same way and does not regress: deck
x0.62 -> x2.59, and it passed the whole distribution before and after (median
x1.09 -> x1.43, against a x1.40 +/-25% window).

12.0 overshoots the deck rung by 4% and is kept there rather than shaved to
11.5, because the two frames disagree by more than that between themselves and
tuning inside the disagreement is fitting noise.

THE ONE RUNG THAT DID NOT GO THE RIGHT WAY IS THE SOFFIT, x0.23 -> x0.20
against a show band of 0.23-0.32, and it is a real cost rather than noise. The
fill does reach the wall -- that is the whole point of the cone rule -- so the
wall rises and everything measured against it falls. Recovering it needs the
wall to rise WITHOUT the soffit staying put, which an isotropic ambient cannot
do; the honest fix is a soffit that is darker in its own right, i.e. geometry
or occlusion, not a light.

THE FRAMES ARE COMMITTED, which is the point of EXPOSURE_FRAMES' complaint that
"nine of the eleven ROOM_EXPOSURE values have no committed frame at all":

  docs/engine-deck-corridor-prefill.png    BEFORE. `--soft-fill 0` reproduces
                                           it BYTE FOR BYTE, 0 pixels differing
                                           of 921,600, which is what makes the
                                           flag a usable negative control.
  docs/engine-deck-corridor-softfill.png   AFTER, the shipped defaults.
  docs/engine-corridor-softfill.png        AFTER, `--shot interior --room
                                           corridor`, the anchor frame.
  docs/engine-deck-corridor-softfill-alone.png
                                           THE FILL ON ITS OWN, rendered with
                                           `--ambient 0 --fixture-energy 0`. It
                                           is the diagnostic that found the
                                           third cone bug and it is worth
                                           re-taking after any change here: an
                                           even deck, dim walls and a black
                                           overhead is what the fill is for,
                                           and a row of pools is not.

AND THE FRAME THAT WAS ALREADY COMMITTED IS STALE, which is why there is a
`-prefill` before-frame rather than a diff against the existing one.
`docs/engine-deck-corridor.png` was last written by 8b39055 and the lens fix
c05a877 -- which changed `light_pilaster_strip`, `light_portal_head` and
interior.tscn -- did not re-take it. Measured today it reads 4.64% CLIPPED
against a 3.69% cap and p5 x1.45, i.e. the blown-lens state; the same command
run against the same code renders 0.00% clipped and p5 x0.77. A committed frame
that no longer matches the code that made it is worse than none, because it is
the thing the next reader diffs against. It should be regenerated:

  tools/render_godot.sh --shot deck --deck blue/0/0 --at docking_bays \\
      --res 1280x720 --out docs/engine-deck-corridor.png
"""


# Darkest measurable surface / brightest lit surface, balanced, per space.
# THIS TABLE WAS DEAD FOR A SESSION: it was measured, committed, and read by
# nothing, while interior.tscn carried one hand-calibrated ambient_light_energy
# for every room in the station. `ambient_energy()` below is what uses it.
#
# The corridor numbers came from three frames that do not agree, because they
# are three different kinds of corridor -- which is itself the finding.
AMBIENT_RATIO = {"residential": 0.300, "concourse": 0.120, "service": 0.060}

# The room archetypes, mapped onto measured spaces. `rooms.LIGHTS` maps the
# same eleven archetypes onto measured FITTINGS and this is the other half of
# it: how much light is in the room that no fitting accounts for.
#
# Medical, research and office take the war room's 0.23 rather than a corridor
# number, because they are the measured WORKING interiors and a working
# interior has fill. Detention takes command and control's 0.047, the darkest
# thing measured anywhere in the reference.
AMBIENT_BY_ARCHETYPE = {
    "industrial": 0.060,     # corridor_service
    "store": 0.076,          # docking_bay
    "transit": 0.120,        # corridor_concourse
    "hospitality": 0.090,    # dougs_dugout
    "worship": 0.210,        # council_chamber
    "medical": 0.230,        # war_room
    "research": 0.230,       # war_room
    "detention": 0.047,      # command_control
    "commerce": 0.094,       # zocalo_concourse
    "office": 0.230,         # war_room
    "generic": 0.300,        # corridor_residential
}
# interior.tscn's ambient_light_energy, calibrated in session 3n against the
# residential corridor -- which is the AMBIENT_RATIO 0.300 row. Every other
# space scales off that one measured point rather than off a guess.
#
# RE-DERIVED ONCE THE SOFT FILL EXISTED, because it was calibrated in 3n with
# the corridor's lenses blown -- about 40% of that frame was halo -- so it was
# stale by construction and had to be re-taken AFTER the missing key was built
# rather than before. Its own definition is the value that puts the corridor
# anchor's frame at x1.40 of `grey level 1.webp`'s median, so it was swept.
# `--shot interior --room corridor`, 1280x720, soft fill at 12.0:
#
#   ambient   median vs the reference   distribution
#   ------------------------------------------------
#     1.00            x1.16             FAIL -- p5 x1.44 against a x1.29 band
#     1.30            x1.43             PASS, every band
#     1.60            x1.72             PASS, at the top of the level window
#
# d(ln median)/d(ln ambient) = 0.84 over that range, so unlike the EXPOSURE
# derivation this file records as invalid, the median really does track the
# ambient here and the sweep can be inverted. It inverts to 1.25-1.27 -- the
# recorded 1.30 is 3% high, which is inside any tolerance this project uses and
# is left alone rather than churned.
#
# THE INTERESTING ROW IS 1.00, and it is the same pathology as the exposure
# finding rather than a different one: LOWERING the ambient makes p5 go UP, from
# x0.80 to x1.44, because the frame's crushed fraction goes 1.80% -> 5.84% and
# the pixels leaving the measurable set leave from the BOTTOM. Turning the fill
# down to make room for a lower ambient does not darken the shadows, it deletes
# them.
AMBIENT_CALIBRATED_ENERGY = 1.30
AMBIENT_CALIBRATED_RATIO = 0.300


# THE MISSING HALF OF `energy_rel`, and it is worth being precise about what
# is missing. Every fixture in docs/layer4-lighting/*.json carries an
# `energy_rel` that is RELATIVE WITHIN ITS OWN MEASURED FAMILY -- the war
# room's brightest fitting is 1.0 and so is the docking bay's, and those are
# not the same number of lumens. Nothing in the measurement could supply the
# ratio between families, because no frame contains two of them.
#
# So it is measured HERE, from our own renders, against the reference frame
# each archetype was mapped to. The procedure, and it is repeatable:
#
#   1. render one room per archetype
#   2. tools/measure_frame.py both it and its mapped reference frame
#   3. gain *= 1.40 * ref_median / our_median
#
# The 1.40 is not a fudge. It is the offset the CORRIDOR already sits at and
# has been judged good at: `grey level 1.webp` measures median linear
# luminance 0.0533 and our corridor at the calibrated ambient renders 0.0741,
# i.e. 1.40x. A film frame carries a grade, a stock and chroma subsampling and
# our render carries none of them, so matching a reference exactly would make
# every room darker than the one room in this project anyone has looked at.
# Targeting the corridor's own offset makes every archetype as faithful as the
# corridor is, which is the most that can honestly be claimed.
#
# Session 3o, first pass, at gain 1.0 everywhere (our median / ref median):
#   industrial 1.08  store 0.97  transit 1.70  hospitality 1.27  worship 0.53
#   medical 7.47  research 7.75  detention 2.39  commerce 2.42  office 7.16
#   generic 0.77
# Medical, research and office at 7x is one defect with one cause: those three
# are the archetypes whose fittings got the largest measured RANGES (the
# 7.2 m scaled batten) or the tightest measured SPACING (the strip bank at
# 1.4 m, which puts 12-23 lamps in a bay), and range and count both multiply
# flux while `energy_rel` says nothing about either.
#
# IT SCALES THE AMBIENT TOO, and the first version did not -- which is the
# finding that produced this shape. Scaling only the fittings moved medical
# from 7.5x to 3.1x and moved transit, worship and generic by nothing at all
# (1.70 -> 1.70, 0.53 -> 0.55, 0.77 -> 0.77), because in those three rooms the
# fittings contribute almost nothing to the frame: a corridor downlight
# reaches 1.2 m and a platform pool 4 m, so what fills the room is ambient and
# the emissive surfaces. An exposure that cannot move the dominant term is not
# an exposure. Scaling both preserves the fill-to-key relationship -- which is
# what AMBIENT_BY_ARCHETYPE and `energy_rel` measure -- and sets only the
# level, which is what nothing measured.
ROOM_EXPOSURE = {
    "industrial": 1.30,
    "store": 1.42,
    "transit": 0.75,
    "hospitality": 1.20,
    "worship": 2.25,
    "medical": 0.14,
    "research": 0.14,
    "detention": 0.53,
    "commerce": 0.51,
    "office": 0.14,
    "generic": 1.67,
}


# Bespoke modules get their own exposure, once each has been through a layer-4
# pass -- rendered, measured against its reference frame with
# tools/measure_frame.py, and scaled. EMPTY IS THE HONEST STATE and not an
# oversight: a bespoke module falls back to the corridor's anchor rather than
# borrowing an archetype's number.
#
# It borrowed one for exactly one render and the result is why this exists.
# `rooms.archetype()` reads a place's `functions`, so it happily classifies a
# bespoke place too -- command and control came out "office" and took office's
# 0.14, which was calibrated against a rooms.py bay with rooms.py fittings.
# The frame came back 100% below the measurable floor: not one pixel of the
# station's bridge above 0.01 linear. An exposure measured on one generator's
# geometry says nothing about another's.
#
# Four are measured. Same procedure as ROOM_EXPOSURE and the same 1.40 target:
# render the module's room, measure it and its reference frame with
# tools/measure_frame.py, scale. At the anchor they came in at 1.53, 1.04, 1.51
# and 1.55 of their references' medians, so the corrections are small -- which
# is the interesting part. It says the anchor was a reasonable default and that
# what those four modules were missing was not exposure but SOURCES: none of
# their lamps cast anything until FIXTURE_LIGHTING learned their names.
#
# The rest stay absent, which means the anchor, which means not yet measured.
#
# ONE OF THEM MOVED WHEN `fixture_lights` LEARNED WHAT A FITTING IS. Splitting
# a span into its connected bodies multiplied three modules' flux -- the Zocalo
# by 2.92, command and control by 4.00, the docking bay by 3.00 -- and only the
# Zocalo's FRAME moved with it. All three were re-rendered at 640x360 with the
# old rig and the new one at the same camera and the same exposure, and
# differenced pixel by pixel:
#
#   zocalo   52.5% of the frame changed, +3.6 mean   1.42 -> 1.54 of its ref
#   docking   7.3% changed, every one brighter       1.38 -> 1.39
#   cnc       45 PIXELS changed out of 230,400       1.18 -> 1.18
#
# Only the Zocalo is rescaled, because only the Zocalo's measurement moved. The
# docking bay's floods were already spread over the bay three to a span, so the
# one lamp a span stood among them rather than away from them, and splitting
# them apart moved the light a metre. cnc is the interesting one and it is NOT
# evidence the fix did nothing there: its shot stands in the pit below the
# strips looking away from them, so it can see neither the wall the courses
# wash nor the courses themselves.
BESPOKE_EXPOSURE = {
    "zocalo": 0.84,          # vs reference/04-sector-red/more zocalo.png
                             # 0.92 x 1.40/1.54, re-measured after the body
                             # split took it from 36 lamps to 96. Verified at
                             # 1.43 of the reference on the re-render.
    "hospitality": 1.34,     # vs reference/04-sector-red/Doug's Dugout.webp
    # 1.10, and the 0.93 it replaces was measured against a frame the pipeline
    # could not produce: the standpoint search stood this camera at y = -0.20 m,
    # in the instrument pit, until the floor test above was added. Re-measured
    # at the corrected camera and at the recovered lamp count (1 -> 36).
    "command_control": 1.10,  # vs 03-sector-blue/comand and contorl.webp
                             # UNCHANGED, and the reason is worth a line
                             # because the number looks stale and is not: this
                             # shot now measures 1.18 rather than the 1.40 it
                             # was set at, but it measures 1.18 with the OLD
                             # rig too. What moved is the CAMERA -- session
                             # 3o's rewrite of `open_standpoint` -- not the
                             # light. Correcting an exposure for a camera move
                             # would be treating an exposure as a rescue, and
                             # the shot itself is the thing to look at first:
                             # it stands the eye at y = -0.20 m, below the
                             # deck. Re-calibrate when the shot is right.
    "docking_bay": 0.90,     # vs reference/03-sector-blue/dock.webp -- 13
                             # lamps became 39 and it measured 1.38 -> 1.39.
    # 0.47, and my own 1.00 was worse-founded. I set that by eye against the
    # CORRIDOR's median, having not found a reference frame for this sector.
    # `reference/05-sector-green/corridor in alien sector.webp` exists, is
    # authority 1, and is the frame the module's own fitting was measured from.
    # Calibrated against it the correction is 0.47, not none.
    "alien_sector": 0.47,
    "customs": 0.62,         # vs 11-props-and-technology/babylon 5 welcome
                             # sign, instructions, and hub.jpg
    "quarters": 1.12,        # vs reference/07-sector-grey/grey level 1.webp,
                             # the residential corridor a unit opens off
    # 2.27, from 2.84. Two things moved it and both were corrections rather
    # than tuning: the cove became six lamps spread round the arc instead of
    # one at its centroid, and the camera moved onto the chamber floor. At the
    # old value the corrected frame reads x1.75 of its reference, the very edge
    # of the tolerance band.
    "council_chamber": 2.27,  # vs 05-sector-green/council chambers.webp
    "plant": 0.88,           # vs 10-interiors-generic-kit/more hallways.jpg,
                             # the measured SERVICE corridor -- the register
                             # whose walls are black except where a panel or
                             # the deck strip reaches them.
                             #
                             # AND IT BARELY MOVES THE NUMBER, which is worth
                             # knowing before someone iterates on it: the plant
                             # frame is mostly below the measurable floor, so
                             # dimming it pushes more pixels under 0.01 and
                             # RAISES the median of what is left. The two
                             # effects cancel and the frame sits at 1.59x its
                             # reference either way -- inside tolerance, and
                             # not reachable by exposure. In a volume that is
                             # 139.8 million cubic metres of void with seven
                             # floods in it, the median of the lit pixels is
                             # not an exposure measurement.
}


# WHICH FRAME AND WHICH REFERENCE EACH EXPOSURE ABOVE WAS SET ON, as data
# rather than as prose in a comment. It exists because the exposures could not
# be RE-verified: every reference above is named in a comment, so re-measuring
# the record meant a human reading fourteen comments and retyping paths. A
# verdict that cannot be recomputed is a verdict that gets believed.
#
# NINE OF THE ELEVEN ROOM_EXPOSURE VALUES HAVE NO COMMITTED FRAME AT ALL, and
# that is the first thing this table makes visible. industrial, store, transit,
# hospitality, worship, research, detention, office and generic were each set
# by rendering a room, measuring it, and not keeping the render. Their values
# are unfalsifiable until someone re-renders them, and `--gate-frames` says so
# per row instead of passing them in silence.
#
# `reference` is the frame the exposure was CALIBRATED against, which is not
# always the frame the framing was composed from -- DRUM_CALIBRATION['tram']
# is the standing example (composed from 33a, measured against 34b) and it is
# recorded there rather than duplicated here.
EXPOSURE_FRAMES = {
    "ROOM_EXPOSURE": {
        "industrial": (None, "reference/10-interiors-generic-kit/"
                             "more hallways.jpg"),
        "store": (None, "reference/03-sector-blue/dock.webp"),
        "transit": (None, "reference/10-interiors-generic-kit/"
                          "more hallway.jpg"),
        "hospitality": (None, "reference/04-sector-red/Doug's Dugout.webp"),
        "worship": (None, "reference/05-sector-green/council chambers.webp"),
        "medical": ("docs/engine-medlab.png",
                    "reference/03-sector-blue/war room.webp"),
        "research": (None, "reference/03-sector-blue/war room.webp"),
        "detention": (None, "reference/03-sector-blue/comand and contorl.webp"),
        "commerce": ("docs/engine-market.png",
                     "reference/04-sector-red/more zocalo.png"),
        "office": (None, "reference/03-sector-blue/war room.webp"),
        "generic": (None, "reference/07-sector-grey/grey level 1.webp"),
    },
    "BESPOKE_EXPOSURE": {
        "zocalo": ("docs/engine-zocalo.png",
                   "reference/04-sector-red/more zocalo.png"),
        "hospitality": ("docs/engine-dugout.png",
                        "reference/04-sector-red/Doug's Dugout.webp"),
        "command_control": ("docs/engine-cnc.png",
                            "reference/03-sector-blue/comand and contorl.webp"),
        "docking_bay": ("docs/engine-docking-bay.png",
                        "reference/03-sector-blue/dock.webp"),
        "alien_sector": ("docs/engine-alien-sector.png",
                         "reference/05-sector-green/"
                         "corridor in alien sector.webp"),
        "customs": ("docs/engine-customs.png",
                    "reference/11-props-and-technology/babylon 5 welcome "
                    "sign, instructions, and hub.jpg"),
        "quarters": ("docs/engine-quarters.png",
                     "reference/07-sector-grey/grey level 1.webp"),
        "council_chamber": ("docs/engine-council.png",
                            "reference/05-sector-green/council chambers.webp"),
        "plant": ("docs/engine-plant.png",
                  "reference/10-interiors-generic-kit/more hallways.jpg"),
    },
    # THE ANCHOR. `room_exposure` returns 1.0 for the corridor because 1.0 is
    # what the corridor's own frame over `grey level 1.webp` DEFINES, so it
    # belongs in this table more than anything else does.
    "ANCHOR": {
        "corridor": ("docs/engine-corridor.png",
                     "reference/07-sector-grey/grey level 1.webp"),
    },
    # THE ASSEMBLED BUILD, measured against the same reference as the anchor,
    # because it is 76% the same geometry. These two are the first frames of the
    # WALKABLE station that came out of the shipped rig -- see DECK_EXPOSURE.
    #
    # Both are committed, which is the point of them. Nine ROOM_EXPOSURE rows
    # above have no frame and cannot be checked in either direction; a shot that
    # produced its evidence and then threw it away would be the tenth.
    #
    # WHAT THEY MEASURE, run 2026-07-31 at 1280x720:
    #
    #   frame              median   p5      distribution
    #   deck corridor      x1.52    x1.45   FAIL -- p5 bright, 4.64% clipped
    #   deck door          x0.98    x1.23   PASS -- all six checks
    #   engine-corridor    x1.39    x1.64   FAIL -- p5 bright  (the anchor)
    #
    # THREE THINGS THEY SETTLE, and none of them was knowable before the shot
    # existed:
    #
    # 1. THE AD-HOC RIG WAS THE PROBLEM, NOT THE BUILD. The only previous engine
    #    frames of the walkable deck were lit by four hand-placed omnis and an
    #    ambient of 0.34 written into a scratch JSON, and they read p5 x11.09.
    #    The shipped fittings read x1.45 in the same corridor. The ad-hoc rig was
    #    7.6x hot in the shadows and essentially all of that number was the rig.
    # 2. THE DECK IS NOT WORSE-LIT THAN THE ROOM. The assembled corridor's p5
    #    (x1.45) is CLOSER to the reference than the single-room anchor's
    #    (x1.64) at the same exposure, the same fittings and the same materials.
    #    What differs is what else is in frame.
    # 3. THE DOOR FRAME PASSES THE DISTRIBUTION TEST, which 16 of the 17
    #    exposures measured in session 3r do not -- and it FAILS the level test
    #    while doing it (x0.98 against the x1.05-1.75 window). The two criteria
    #    disagree, on one frame, in opposite directions. That is worth more than
    #    either verdict: it is a case where matching the show's contrast and
    #    matching the corridor's own offset are not the same requirement.
    "DECK": {
        "deck_corridor": ("docs/engine-deck-corridor.png",
                          "reference/07-sector-grey/grey level 1.webp"),
        "deck_door": ("docs/engine-deck-door.png",
                      "reference/07-sector-grey/grey level 1.webp"),
    },
}
# The re-verification of all of it, run 2026-07-30 with the distribution
# comparison and recorded in docs/layer4-lighting/frame_distribution.json:
# 17 of 17 pass the median test, 1 of 17 passes the distribution test. NO
# EXPOSURE VALUE WAS CHANGED. `--gate-frames` reprints it from the files.
EXPOSURE_DISTRIBUTION_DEBT = True


def gate_frames(mf=None):
    """Every exposure with a committed frame, on the new comparison.

    Reports, and returns (n_pass, n_fail, n_unverifiable). It does not exit
    non-zero on a distribution failure the way `--gate-drum` does, because
    fifteen of these are known-failing debt and a command that always fails is
    a command nobody runs. It DOES count the rows that cannot be checked at
    all, which is the number that should be zero first.
    """
    mf = mf or _measure_frame()
    npass = nfail = nskip = 0
    for fam in ("ANCHOR", "DECK", "ROOM_EXPOSURE", "BESPOKE_EXPOSURE"):
        for key, (frame, ref) in sorted(EXPOSURE_FRAMES[fam].items()):
            if frame is None:
                print(f"{fam:16s} {key:16s} NO COMMITTED FRAME -- this "
                      f"exposure cannot be verified against "
                      f"{os.path.basename(ref)}")
                nskip += 1
                continue
            p, rp = os.path.join(ROOT, frame), os.path.join(ROOT, ref)
            if not os.path.exists(p) or not os.path.exists(rp):
                print(f"{fam:16s} {key:16s} MISSING FILE "
                      f"{frame if not os.path.exists(p) else ref}")
                nfail += 1
                continue
            m, r = mf.measure(p), mf.measure(rp)
            x = m["median"] / r["median"] if r["median"] else 0.0
            old = abs(x - mf.RENDER_OFFSET) <= mf.TOL * mf.RENDER_OFFSET
            rows, dok = mf.distribution(m, mf.at_offset(rp, mf.RENDER_OFFSET))
            bad = ", ".join(
                f"{lab}"
                + (f" x{xx:.2f}" if xx not in (None, float("inf")) else "")
                for lab, _a, _b, xx, good, _n in rows if good is False)
            npass += dok
            nfail += not dok
            print(f"{fam:16s} {key:16s} median x{x:.2f} "
                  f"{'OK  ' if old else 'OUT '} | distribution "
                  f"{'OK' if dok else 'FAIL: ' + bad}")
    print(f"\n{npass} pass, {nfail} fail, {nskip} have no committed frame "
          f"and cannot be verified at all")
    return npass, nfail, nskip


def room_exposure(room):
    """Exposure multiplier for one room. See ROOM_EXPOSURE."""
    if room in ("corridor", "junction"):
        return 1.0                      # the anchor: it is what 1.0 means
    import directory as dr
    import rooms as R

    place = dr.by_key(room)
    if place["module"]:
        return BESPOKE_EXPOSURE.get(place["module"], 1.0)
    return ROOM_EXPOSURE.get(R.archetype(place), 1.0)


def ambient_energy(room):
    """Ambient light energy for one interior room.

    The corridor and junction pseudo-rooms are the residential corridor the
    calibration was made in, so they get exactly the calibrated value and this
    function is a no-op for them. Everything else scales by the ratio of its
    space's measured darkest/brightest against that corridor's.
    """
    if room in ("corridor", "junction"):
        return AMBIENT_CALIBRATED_ENERGY
    import directory as dr
    import rooms as R

    place = dr.by_key(room)
    # A bespoke module takes the corridor's fill until its own layer-4 pass
    # measures one, for the reason recorded on BESPOKE_EXPOSURE: an archetype
    # inferred from a place's `functions` is a rooms.py number and rooms.py
    # did not build this room.
    ratio = (AMBIENT_CALIBRATED_RATIO if place["module"]
             else AMBIENT_BY_ARCHETYPE.get(R.archetype(place),
                                           AMBIENT_CALIBRATED_RATIO))
    return (AMBIENT_CALIBRATED_ENERGY * ratio / AMBIENT_CALIBRATED_RATIO
            * room_exposure(room))


def fitting_bodies(verts, tris, lo, hi, weld=FIXTURE_WELD_M):
    """One tagged span -> its CONNECTED BODIES, one list of triangles each.

    This is what makes a fitting a fitting rather than a run of triangles that
    happen to share a name. See FIXTURE_WELD_M for what it was measured to be
    worth and why the weld is by position rather than by vertex index.

    Union-find over welded vertex positions. Rounding coordinates to a grid of
    `weld` and unioning triangles that share a cell is the whole method: it is
    O(triangles) with no spatial structure, and the failure it can have -- two
    vertices either side of a cell boundary reading as distinct -- costs one
    extra body, which the FIXTURE_MERGE_M pass then puts back together if they
    really were 0.1 mm apart.
    """
    key, owner = {}, {}
    parent = list(range(hi - lo))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for k in range(lo, hi):
        for i in tris[k]:
            p = verts[i]
            cell = (round(p[0] / weld), round(p[1] / weld), round(p[2] / weld))
            v = key.setdefault(cell, len(key))
            if v in owner:
                a, b = find(k - lo), find(owner[v])
                if a != b:
                    parent[a] = b
            else:
                owner[v] = k - lo
    bodies = {}
    for k in range(hi - lo):
        bodies.setdefault(find(k), []).append(lo + k)
    return list(bodies.values())


def surface_points(verts, tris, body, spacing, max_split=16):
    """Points spread over a body's SURFACE, with their share of its area.

    SAMPLING BY TRIANGLE IS NOT SAMPLING BY GEOMETRY, and the first version of
    `sample_body` proved it on the first fitting it was pointed at: command and
    control's wall course is an 8.64 m box drawn with twelve triangles, so
    clustering triangle centroids could never place a sample anywhere except at
    a triangle's centroid. It produced four lamps for that course -- one on
    each end cap and TWO AT THE SAME POINT in the middle -- and left the length
    of the course, which is the part that lights the room, unsampled.

    So the candidates come from subdividing each triangle to `spacing`, not
    from counting them. A long thin box then yields points all along itself
    however few triangles it is made of, which is the property that makes the
    sampling a statement about the fitting rather than about its tessellation.

    Each triangle splits into n x n congruent sub-triangles, so every returned
    point carries the same area A/n^2 -- no quadrature weights to get wrong.
    """
    pts = []
    for k in body:
        a, b, c = (verts[i] for i in tris[k])
        ab = [b[j] - a[j] for j in range(3)]
        ac = [c[j] - a[j] for j in range(3)]
        cr = (ab[1] * ac[2] - ab[2] * ac[1],
              ab[2] * ac[0] - ab[0] * ac[2],
              ab[0] * ac[1] - ab[1] * ac[0])
        area = 0.5 * math.sqrt(sum(q * q for q in cr))
        if area <= 0.0:
            continue
        longest = max(math.dist(a, b), math.dist(b, c), math.dist(c, a))
        n = max(1, min(max_split, int(math.ceil(longest / spacing))))
        w = area / (n * n)
        for i in range(n):
            for j in range(n - i):
                for du, dv in (((3 * i + 1), (3 * j + 1)),
                               ((3 * i + 2), (3 * j + 2))):
                    if du + dv > 3 * n - 1:
                        continue        # the down-facing sub-triangle of the
                    u, v = du / (3.0 * n), dv / (3.0 * n)   # last row does not
                    pts.append(([a[q] + u * ab[q] + v * ac[q]              # exist
                                 for q in range(3)], w))
    return pts


def sample_body(verts, tris, body, pitch, cap=EXTENDED_SAMPLE_CAP):
    """One extended fitting -> the (position, share of its energy) it lights
    from.

    Greedy clustering against each cluster's SEED, not against its running
    mean, and the difference is the whole point. The FIXTURE_MERGE_M pass below
    merges against a running mean, which is right for its job -- pulling seven
    pilaster bars into one lamp -- and catastrophic here: on a line source the
    mean walks along the line as members are added, every next point is still
    within pitch of it, and a 33.6 m cove comes back as one cluster, which is
    the defect this function exists to fix. Measuring from a fixed seed bounds
    a cluster at `pitch` and cannot chain.

    Order-dependent, and that is acceptable rather than ignored: a different
    ordering gives more clusters and smaller ones, never a cluster wider than
    2 x pitch, so the property that matters -- every sample sits ON the fitting
    and none of them stands off it -- holds however the generator emits.

    THE SHARE IS BY AREA, not one over the count. The end cap of a light strip
    is a hundredth of its emitting surface and should not put out a tenth of
    its light; weighting by area also makes the result stable when the pitch
    moves, because a cluster that splits in two hands each half its own area.
    """
    while True:
        seeds = []
        p2 = pitch * pitch
        for p, w in surface_points(verts, tris, body, pitch / 3.0):
            for s in seeds:
                if sum((s[0][j] - p[j]) ** 2 for j in range(3)) <= p2:
                    s[1].append((p, w))
                    break
            else:
                seeds.append((p, [(p, w)]))
        if seeds and len(seeds) <= cap:
            break
        if not seeds:
            return []
        # Over the cost bound. Widening the pitch is the right lever because
        # the energy is normalised: a coarser sampling of the same fitting is
        # the same amount of light in fewer places.
        pitch *= 2.0
    total = sum(w for s in seeds for _p, w in s[1]) or 1.0
    out = []
    for _seed, members in seeds:
        m = sum(w for _p, w in members) or 1.0
        out.append(([sum(p[j] * w for p, w in members) / m for j in range(3)],
                    m / total))
    return out


def fixture_lights(verts, tris, spans, energy, rng, shadow_n=2, eye=None,
                   down=None, exposure=None):
    """One light per tagged light fitting, at its centroid, IN ITS OWN COLOUR.

    CONSISTENCY BY CONSTRUCTION -- CLAUDE.md's fourth hard rule, applied to
    light. The alternative is a table of hand-placed lamp positions, which is a
    second description of where the fittings are; the moment the kit moves a
    downlight the table is wrong and nothing says so. Here the light IS the
    fitting: `interior_kit` tags `light_downlight`, `light_pilaster_strip`,
    `light_portal_head` and `light_deck_channel`, and every one of those spans
    becomes a source at its own centre.

    A consequence worth stating: a room with no tagged fitting comes back
    BLACK, which is correct and legible. An interior that lights itself from
    nowhere is the failure this avoids.

    THE COLOUR COMES FROM THE MATERIAL, and that is not a detail. The four kit
    fittings are NOT one colour: `light_downlight` is warm at (1.00, 0.68,
    0.40) and the pilaster strip, portal head and deck channel are cool
    blue-white at roughly (0.88, 0.93, 1.00). Those are measured values sitting
    in materials.py. Passing one lamp colour for all four would have thrown
    away the warm/cool contrast that is most of what a Babylon 5 corridor looks
    like -- and it would have looked deliberate.

    Energy is scaled by each material's own emission_energy for the same
    reason: the library already says the portal head is the brightest fitting
    and the deck channel the dimmest, and that ranking is measured.

    A SPAN IS NOT A FITTING AND A FITTING IS NOT ALWAYS A POINT, which is the
    other half of "the light IS the fitting" and was missing. Each tagged span
    is cut into connected BODIES (`fitting_bodies`), and a body longer than its
    own measured range is SAMPLED (`sample_body`) rather than collapsed to a
    centroid that would sit off the fitting looking back at it. Those are two
    different corrections and they move the light in opposite directions: a
    body is a whole fitting and gets a fitting's energy, so more bodies is more
    light; samples are one fitting seen in several places and share its energy
    between them, so more samples is the same light better spread.

    `down` IS WHICH WAY THE FLOOR IS, and it is a function of position rather
    than a constant because on this station it is one. Every spot in the table
    is a ceiling or soffit fitting aimed at the deck beneath it; in a
    cylindrical section that deck is at -Y, and inside a spun ring it is
    radially OUTWARD from the spin axis. Default None keeps -Y, so every
    existing single-room shot renders exactly as it did. See `radial_aim` and
    `godot/scripts/player.gd`'s `gravity_dir()`, which is the authority on the
    convention and agrees with it: gravity is `(x, y, 0)` normalised, the spin
    axis being +Z.

    `exposure` is a per-span multiplier, for a shot that contains more than one
    room. A single-room shot scales `energy` on the way in and passes None here;
    an assembled deck cannot, because `ROOM_EXPOSURE` is per-archetype and a
    deck carries six archetypes at once. Passing the fitting's own room's value
    is the direct generalisation of what `build_interior` already does, and the
    alternative -- one number for all of them -- is the mistake BESPOKE_EXPOSURE
    is written to warn about: "an exposure measured on one generator's geometry
    says nothing about another's".
    """
    import materials as mats

    raw = []
    # One entry per connected body, so a sample can say which fitting it is a
    # sample OF. The merge below needs that: two bodies 0.1 m apart are one
    # lamp, but two samples of one 33.6 m cove 4.5 m apart are not, and without
    # an identity the merge cannot tell those cases apart by distance alone.
    seen_bodies = []
    for name, lo, hi in spans:
        # MEMBERSHIP OF THE TABLE IS THE GATE, not the name. It used to be the
        # `light_` prefix, and that rule locked every bespoke module out of the
        # light rig: zocalo.py's lamp is `zoc_rib_lamp`, the docking bay's is
        # `bay_lamp`, the bar's is `bar_pendant_lamp`, and no amount of
        # measurement could make any of them cast because none of them is
        # spelled right. Renaming nine modules' groups would have broken their
        # material binds, their scene rules and the layer-3 coverage count, to
        # satisfy a convention.
        #
        # Nothing is lost by the change. The prefix was never the real test --
        # a `light_` group absent from FIXTURE_LIGHTING was already skipped --
        # so this is the same rule stated once instead of twice. The convention
        # survives where it means something: interior_kit and rooms.py still
        # tag `light_*`, the self-test asserts it, and `directory._lit_keys`
        # still counts by it for the generated rooms.
        #
        # THE NAME MAY CARRY AN ADDRESS. `fixture_key` strips it; see there for
        # what it cost while the lookup was a bare `in`.
        key = fixture_key(name)
        if key is None:
            # Emissive only. The material still glows -- that is what makes the
            # trim read -- but it casts nothing. Measured per fitting, not
            # assumed; see FIXTURE_LIGHTING.
            continue
        spec = FIXTURE_LIGHTING[key]
        reach = spec.get("range_m") or rng
        gain = energy * (exposure(name) if exposure else 1.0)
        for body in fitting_bodies(verts, tris, lo, hi):
            bidx = {i for k in body for i in tris[k]}
            if not bidx:
                continue
            b0 = [min(verts[i][j] for i in bidx) for j in range(3)]
            b1 = [max(verts[i][j] for i in bidx) for j in range(3)]
            # The body's own size, against the distance the measurement says
            # it throws. See EXTENDED_SAMPLES_PER_RANGE for where the line is
            # and what sits either side of it.
            if math.dist(b0, b1) > reach:
                parts = sample_body(verts, tris, body,
                                    reach / EXTENDED_SAMPLES_PER_RANGE)
            else:
                # NOT the surface sampler with one cluster: a compact fitting
                # keeps the vertex centroid it has always had, to the last bit,
                # so the twelve lamps of `docs/engine-corridor.png` -- this
                # project's calibration anchor -- do not move by a millimetre
                # for a change that was never about them.
                n = float(len(bidx))
                parts = [([sum(verts[i][j] for i in bidx) / n
                           for j in range(3)], 1.0)]
            fitting = len(seen_bodies)
            seen_bodies.append(name)
            for c, share in parts:
                lt = {"pos": c,
                      # Shared, not repeated: samples are one fitting seen in
                      # several places and `share` sums to 1 across them.
                      # Bodies are not -- each is its own fitting and carries a
                      # fitting's energy.
                      "energy": gain * spec["energy_rel"] * share,
                      "colour": list(spec["colour"]),
                      "range": reach, "attenuation": 1.0,
                      "group": name, "_shadow": spec["shadow"],
                      "_fitting": fitting}
                if spec["kind"] == "spot":
                    # Every spot in this table is a ceiling or soffit fitting
                    # aimed straight down. That is the measurement in all five
                    # cases; the one that is not quite -- cc_dais_key, "aimed
                    # down and aft" -- is aimed down here, because the aft
                    # direction is a property of the room command and control
                    # is, and rooms.py builds the same bay in eleven archetypes
                    # with no aft.
                    #
                    # DOWN IS NOT -Y ON A RING, and `[0, -1, 0]` was hard-coded
                    # here. A spot in a ring corridor aimed at world -Y points
                    # ALONG the ring -- it grazes the deck at two angles a lap
                    # and at every other angle throws its cone down the corridor
                    # at a wall. See the `down` parameter.
                    lt["kind"] = "spot"
                    lt["angle"] = spec["angle_deg"]
                    lt["aim"] = list(down(c)) if down else [0.0, -1.0, 0.0]
                raw.append(lt)

    # ONE FITTING, ONE LIGHT. A pilaster strip is SEVEN tagged bars with gaps
    # between them -- that segmentation is what makes it read as B5 rather than
    # as a fluorescent batten, and it is asserted in interior_kit. But seven
    # bars 120 mm apart are one lamp as far as the lighting is concerned, and
    # treating them as seven put 117 sources in a 21.6 m corridor.
    #
    # Merged by proximity within a group, so the segmentation survives in the
    # GEOMETRY (where it is the point) and disappears from the LIGHT RIG (where
    # it is seven times the cost for no visible difference).
    #
    # NEVER ACROSS THE SAMPLES OF ONE FITTING. `sample_body` spreads an
    # extended fitting on purpose, and its pitch is range/4 -- 0.88 m for a
    # 3.5 m wall course, which is inside this 0.9 m radius. Merging by distance
    # alone would therefore undo the split for every fitting throwing less than
    # 3.6 m and leave the fix working only on the long-range ones, which is the
    # sort of half-applied correction that reads as a tuning problem later.
    out = []
    for lt in raw:
        for got in out:
            if (got["group"] != lt["group"]
                    or got["_fitting"] == lt["_fitting"]):
                continue
            d2 = sum((got["pos"][k] - lt["pos"][k]) ** 2 for k in range(3))
            if d2 <= FIXTURE_MERGE_M ** 2:
                w = got["_n"]
                got["pos"] = [(got["pos"][k] * w + lt["pos"][k]) / (w + 1)
                              for k in range(3)]
                got["_n"] = w + 1
                break
        else:
            lt["_n"] = 1
            out.append(lt)
    for lt in out:
        lt.pop("_n", None)
        lt.pop("_fitting", None)
    # Shadows are rationed for the same reason as in the drum: an omni shadow
    # is a cube map, so each one re-renders the scene six times, on a CPU.
    # Shadows only where the MEASUREMENT says the fitting casts one. In
    # `grey level 1.webp` a pilaster projecting 0.17 m from the wall a metre
    # from a downlight lens throws no visible shadow, so the downlight does not
    # get one here either. Rationing by distance to the eye -- the drum's rule
    # -- would have invented three.
    castable = [i for i, lt in enumerate(out) if lt.pop("_shadow", False)]
    if eye is not None and castable:
        castable.sort(key=lambda i: sum((out[i]["pos"][k] - eye[k]) ** 2
                                        for k in range(3)))
        for i in castable[:shadow_n]:
            out[i]["shadow"] = True
    return out


def soft_fill_cone_deg(half_w_m, ceil_h_m, height_m=None, pitch_m=None,
                       k=None, floor_=None):
    """The cone that holds a whole BAY of corridor in its flat top, in degrees.

    THE FOUR CONSTANTS ARE READ IN THE BODY AND NOT IN THE SIGNATURE, and that
    is not a style preference. Python binds a default argument once, at import,
    so `height_m=SOFT_FILL_HEIGHT_M` freezes a copy: editing the constant would
    move the lamps and leave the cone at the old geometry, silently. The
    negative-control harness caught exactly that -- widening the pitch fired the
    corner check not because the cone was wrong for the new pitch but because
    the cone had not noticed the new pitch at all.

    SOLVED, NOT CHOSEN, and the thing being solved for is the worst-lit point of
    the volume one source is responsible for: the top corner of its own bay --
    `half_w` sideways, `pitch/2` along the corridor, and only `H - ceiling`
    below. Godot's angular term is `1 - rim^k` with
    `rim = (1 - cos a) / (1 - cos a_max)`, so requiring that corner to keep
    `floor_` of the axial value inverts to

        1 - cos(a_max)  >=  (1 - cos(a_corner)) / (1 - floor_)^(1/k)

    THREE VERSIONS OF THIS WERE WRONG AND EACH FAILED DIFFERENTLY. They are kept
    because the shape of the mistake is the same each time -- a cone sized to
    a smaller set of points than the fill is responsible for -- and because each
    one produced a frame that looked like a different bug.

      1. `atan(half_w / H)`, the ray to the wall FOOT. Every point of a wall
         above its foot is at a LARGER angle from a source above it, so the cone
         lit the deck and none of the wall. With the ambient cut to make room
         for the fill, the frame came back 75.7% below the measurable floor.
      2. The far top corner exactly. Godot's `1 - rim^k` is ZERO at the rim, and
         at the shipped k = 0.6 a wall at rim 0.74 keeps 17%: the wall rung did
         not move between two renders 130x apart in delivered energy, which
         reads as an energy problem and is a cone problem.
      3. The far top corner with the flat top, but IN CROSS-SECTION ONLY. That
         covers a wall point from the one source directly abreast of it and
         from no other, so a wall was lit over 0.9 m in every 3.6 m and dark in
         between -- and the median over a wall box, which is what the ladder
         measures, showed the fill delivering EXACTLY nothing: probed at two
         energies 2.5x apart, six wall boxes all moved by a factor of 1.000.
         The frame that settled it is the fill rendered ALONE, `--ambient 0
         --fixture-energy 0`: a perfectly even deck and black walls.

    The cone comes out WIDER than the corridor and that is the price of a
    shadowless source: the overspill lands on a room's floor along its corridor
    wall, about 1.7 m of it either side at the 10 m mount and the 1.8 m pitch.
    Stated rather than designed out -- it is a strip barely wider than a
    doorway, and light through a doorway is not a defect. Shadows instead would
    cost 706 shadow maps a deck on a CPU rasteriser, and the measurement says
    `shadow: false`.
    """
    height_m = SOFT_FILL_HEIGHT_M if height_m is None else height_m
    pitch_m = SOFT_FILL_PITCH_M if pitch_m is None else pitch_m
    k = SOFT_FILL_ANGLE_ATTENUATION if k is None else k
    floor_ = SOFT_FILL_CORNER_FLOOR if floor_ is None else floor_
    corner = math.atan2(math.hypot(half_w_m, pitch_m / 2.0),
                        max(height_m - ceil_h_m, 1e-3))
    want = (1.0 - math.cos(corner)) / (1.0 - floor_) ** (1.0 / k)
    return math.degrees(math.acos(max(-1.0, 1.0 - want)))


def _soft_fill_light(pos, aim, half_w_m, ceil_h_m, energy):
    """One source of the run.

    `range` IS A CUTOFF AND NOT A FALLOFF, and that cost a render. Godot's
    attenuation is `max(1 - (d/r)^4, 0)^2 * d^-decay`: the first factor is a
    window that exists so the renderer can cull the light, and it is 0.0078 at
    d/r = 0.98. Sized to the far bottom corner -- 6.14 m for a deck 6.00 m below
    -- it multiplied the whole fill by 1/130, and the frame came back with the
    ladder unmoved and everything 2.5x darker, which reads exactly like an
    energy that is too low. `SOFT_FILL_RANGE_M` puts the working distance at a
    third of range, where the window costs 2.4% and the falloff over the
    corridor is the inverse-power term alone. Nothing lies beyond the deck for
    the extra reach to find: the deck is the outermost surface of the ring and
    the cone points away from the axis.
    """
    return {"pos": list(pos), "kind": "spot", "aim": list(aim),
            "angle": soft_fill_cone_deg(half_w_m, ceil_h_m),
            "angle_attenuation": SOFT_FILL_ANGLE_ATTENUATION,
            "range": SOFT_FILL_RANGE_M,
            "energy": energy, "colour": list(SOFT_FILL["colour"]),
            # From the record, not from the default. `render_shot.gd` defaults
            # this to false anyway, so writing it changes no pixel -- but a
            # measured field that the emitter does not read is a field nobody
            # can tell has stopped mattering.
            "shadow": SOFT_FILL["shadow"],
            "attenuation": 1.0, "group": "corridor_soft_fill"}


def soft_fill_ring(meta, energy=SOFT_FILL_ENERGY, pitch_m=SOFT_FILL_PITCH_M):
    """The corridor's off-camera key, on a spun ring, from the collision meta.

    `meta` is `stats["collision_meta"]` -- the description of the surface a
    player actually stands on. Deriving the key from it rather than from the
    render mesh or from a written-down radius is the fourth hard rule applied to
    light: a deck that moves takes its key with it.

    One source per `pitch_m` of ARC LENGTH, so the pitch is metric down the
    corridor rather than angular, and a ring at r 210 m and a ring at r 300 m
    get the same spacing between lamps instead of the same number of them.
    """
    r_floor, hw = meta["floor_r_m"], _corridor_half_w_m(meta)
    ceil_h = r_floor - meta["ceil_r_m"]
    if SOFT_FILL_HEIGHT_M <= ceil_h:
        raise ValueError(f"soft_fill_ring: the key must sit clear of the "
                         f"corridor it keys -- mount {SOFT_FILL_HEIGHT_M} m "
                         f"against a {ceil_h:.2f} m ceiling")
    r_light = r_floor - SOFT_FILL_HEIGHT_M
    if r_light <= 0.0:
        raise ValueError(f"soft_fill_ring: floor radius {r_floor} m is inside "
                         f"the {SOFT_FILL_HEIGHT_M} m mount height")
    a0 = math.radians(meta["start_deg"])
    arc = math.radians(meta["arc_deg"])
    n = max(1, int(round(arc * r_floor / pitch_m)))
    out = []
    for i in range(n):
        a = a0 + arc * (i + 0.5) / n
        p = (r_light * math.cos(a), r_light * math.sin(a), meta["z_m"])
        out.append(_soft_fill_light(p, radial_aim(p), hw, ceil_h, energy))
    return out


def soft_fill_run(verts, tris, spans, energy=SOFT_FILL_ENERGY,
                  pitch_m=SOFT_FILL_PITCH_M):
    """The same key in a single room's LOCAL frame, where down really is -Y.

    `--shot interior` builds one room on its own, Y up, the corridor running
    along +Z. There is no ring and no radial anything, so the run is a straight
    line over the centreline and the aim is (0, -1, 0) -- which is what
    `fixture_lights` already assumes when no `down` is passed, so the two paths
    agree about which way the floor is.

    The extent comes off the DECK PANELS' own vertices rather than off
    `interior_kit.PROVISIONAL`, for the same reason `collision.py` ray-casts its
    shell profile instead of writing it down: a corridor built to another
    profile keys itself correctly and the two cannot disagree. It is also not
    the mesh's bounding box -- that includes the wall build-up either side, and
    a cone sized to it would throw light at the walls' outer faces.
    """
    idx = {i for name, lo, hi in spans if name.startswith("deck")
           for k in range(lo, hi) for i in tris[k]}
    if not idx:
        raise ValueError("soft_fill_run: no `deck*` span in this room -- the "
                         "fill has no floor to key and would be aimed at "
                         "nothing")
    xs = [verts[i][0] for i in idx]
    ys = [verts[i][1] for i in idx]
    zs = [verts[i][2] for i in idx]
    x_mid = (min(xs) + max(xs)) / 2.0
    hw = (max(xs) - min(xs)) / 2.0
    deck_y = max(ys)
    ceil_h = max(q[1] for q in verts) - deck_y
    n = max(1, int(round((max(zs) - min(zs)) / pitch_m)))
    out = []
    for i in range(n):
        z = min(zs) + (max(zs) - min(zs)) * (i + 0.5) / n
        out.append(_soft_fill_light((x_mid, deck_y + SOFT_FILL_HEIGHT_M, z),
                                    (0.0, -1.0, 0.0), hw, ceil_h, energy))
    return out


def per_triangle(spans, n_tris, default="structure"):
    """(name, lo, hi) spans -> one name per triangle.

    `write_obj` here indexes groups per triangle; the interior generators emit
    spans. Converting at the boundary rather than changing either side, because
    both conventions are load-bearing where they are: spans are what
    `interior_kit` records as it builds, and a per-triangle list is what an OBJ
    writer needs.

    The default is NAMED rather than left empty. If it ever appears in a
    render, `structure` resolves to kit_wall_plate and the frame looks merely
    plain -- which is exactly how 80% of every corridor stayed one material for
    two years. `interior_kit` now asserts zero untagged triangles, so seeing
    this name in an interior shot means a generator has regressed.
    """
    owner = [default] * n_tris
    for name, lo, hi in spans:
        for i in range(lo, min(hi, n_tris)):
            owner[i] = name
    return owner


def to_spans(groups, n_tris):
    """Normalise a generator's third return value to (name, lo, hi) spans.

    FOUR SHAPES, because eleven generators were written independently and
    normalising them at source would mean editing every one:

      * (name, lo, hi) spans          -- rooms.py, interior_kit
      * a flat per-triangle name list -- command_control, zocalo, alien_sector
      * a metadata DICT with "groups" -- core_tube, tram
      * nothing at all

    `test_materials_layer3._names` already converts all four to a SET of names,
    which is all a coverage gate needs. The light rig needs more than the
    names: `fixture_lights` puts one source at each span's centroid, so the
    per-triangle shape has to become runs and not just a set. Runs, and not one
    span per group -- a module that emits its ten bay floods as ten contiguous
    stretches of one group gets ten lamps, which is right, and collapsing them
    to a single span would put one lamp at the centroid of all ten.
    """
    if isinstance(groups, dict):
        groups = groups.get("groups") or ()
    if not groups:
        return [("structure", 0, n_tris)]
    if isinstance(groups[0], (list, tuple)):
        return [tuple(x) for x in groups]
    out, start = [], 0
    for i in range(1, len(groups) + 1):
        if i == len(groups) or groups[i] != groups[start]:
            out.append((groups[start], start, i))
            start = i
    return out


# THE INTERIOR-SCENE BESPOKE MODULES AND HOW TO BUILD ONE ROOM OF EACH.
#
# Until this table existed the interior shot could assemble exactly two things:
# the corridor kit and a rooms.py bay. Every one of the fifty locations built
# by a bespoke module raised SystemExit -- so the Zocalo, the docking bay,
# command and control and the council chamber had materials, had lamps in some
# cases, and had NEVER BEEN RENDERED FROM THE INSIDE. Layer 4's whole method is
# to look at a frame and measure it, and there was no frame to look at.
#
# THE REGISTRY MOVED to `station/bespoke.py` so that `station/deck.py` can
# assemble a deck out of the same builders this shot renders a room from,
# instead of the two drifting apart. Imported rather than re-declared:
# `BESPOKE_GEOMETRY`, `QUARTERS_CLASS`, `UNROLL`, `WALK_SURFACE` and
# `unroll_to_local` are the same objects this file used to define, and every
# use site below is unchanged.
from bespoke import (BESPOKE_GEOMETRY, QUARTERS_CLASS,   # noqa: E402,F401
                     UNROLL, WALK_SURFACE, unroll_to_local)
def interior_geometry(room):
    """(verts, tris, spans, extent) for a room key, or the corridor kit.

    Accepts any of the 118 directory keys plus the pseudo-rooms `corridor` and
    `junction`, which are the kit itself -- the surface every location connects
    through and the one with no place entry of its own.

    `extent` is (width_x, length_z) when the generator can say what one bay of
    the room is, and None when the camera has to find its own way -- see
    `build_interior`.
    """
    import interior_kit as kit
    import rooms as R
    import directory as dr

    schema, profile = it.load()
    if room in ("corridor", "junction"):
        kit.reset_tags()
        v, t = (kit.corridor_section(21.6) if room == "corridor"
                else kit.corridor_junction_section(6.0))
        return v, t, kit.tagged_spans(t), None

    place = dr.by_key(room)
    if place["module"]:
        build = BESPOKE_GEOMETRY.get(place["module"])
        if build is None:
            raise SystemExit(
                f"--room {room} is built by {place['module']}.py, which the "
                f"interior shot cannot assemble. Modules it can: "
                f"{', '.join(sorted(BESPOKE_GEOMETRY))}. The rest are drum- or "
                f"exterior-scene and belong in those shots.")
        r = build(schema, profile, place)
        v, t = r[0], r[1]
        if place["module"] in UNROLL:
            v = unroll_to_local(v)
        return v, t, to_spans(r[2] if len(r) > 2 else None, len(t)), None
    v, t, g = R.build(schema, profile, place)
    return v, t, g, R.bay_span_m(place)


def open_standpoint(verts, tris, eye_h, clear_m=0.75, walk_spans=None):
    """Somewhere inside this geometry a person could actually stand.

    `rooms.standpoint` searches the walkable grid, but it needs a room whose
    props are named `prop_` and `fix_` and whose extent the generator will
    state. A bespoke module has neither, so this asks a cruder question that
    needs nothing: which point at eye height is FURTHEST FROM ANY SURFACE,
    preferring the near end of the volume so the shot looks down its length.

    Crude is the right trade here. Three camera bugs in this project came from
    picking a standpoint by arithmetic -- an eye outside its own end wall, an
    eye past the first rank of props, an eye 1.1 m inside a furnace stack --
    and all three were "compute a position and trust it". This computes a
    position and then checks it against the geometry, which is the property
    that matters.
    """
    import numpy as np

    a = np.asarray(verts, dtype=np.float64)
    tri = np.asarray(tris, dtype=np.int64)
    lo, hi = a.min(axis=0), a.max(axis=0)

    # WHICH SURFACE ARE YOU STANDING ON? Not necessarily the bottom of the
    # model. plant.py's walkable skeleton is a catwalk threaded near the INNER
    # face of an 18 m bay -- 15.6 m above the outer face the tanks stand on --
    # so an eye at 1.7 m absolute stands in the tank farm and looks at the
    # underside of everything. The frame showed exactly that: a dark wall of
    # frame and two lit tanks edge-on.
    #
    # So the floors are found rather than assumed: near-horizontal triangles,
    # weighted by area, histogrammed by height. A level carrying a few percent
    # of the model's horizontal area is a deck someone could be on; anything
    # less is a table top.
    p_all = a[tri]
    n = np.cross(p_all[:, 1] - p_all[:, 0], p_all[:, 2] - p_all[:, 0])
    area2 = np.linalg.norm(n, axis=1)
    ok = area2 > 1e-12
    up = np.zeros(len(tri))
    up[ok] = np.abs(n[ok, 1]) / area2[ok]
    flat = ok & (up > 0.85)
    if walk_spans:
        # The module named its walkway. Restrict the search to it and skip the
        # histogram entirely: a declared answer beats an inferred one.
        mask = np.zeros(len(tri), dtype=bool)
        for _n, _l, _h in walk_spans:
            mask[_l:_h] = True
        flat = flat & mask
    levels = [float(lo[1])]
    if flat.any():
        ys = p_all[flat][:, :, 1].mean(axis=1)
        w = area2[flat] / 2.0
        edges = np.arange(lo[1], hi[1] + 0.5, 0.5)
        hist, _ = np.histogram(ys, bins=edges, weights=w)
        keep = hist > 0.03 * w.sum()
        # THE LEVEL IS THE AREA-WEIGHTED MEAN OF THE SURFACES IN ITS BIN, not
        # the bin's edge and not its centre. `edges` starts at the model's
        # lowest vertex, so a deck at y = 0 in a room whose pit bottoms out at
        # -1.9 lands in the bin [-0.4, 0.1) -- reported at its left edge that
        # is 0.4 m INTO the deck, and at its centre 0.15 m above it. Neither is
        # the floor. The mean is, exactly, and costs one more line.
        which = np.digitize(ys, edges) - 1
        levels = []
        for i in np.where(keep)[0]:
            m = which == i
            levels.append((float((ys[m] * w[m]).sum() / w[m].sum()),
                           float(hist[i] / w.sum())))
        if not levels:
            levels = [(float(lo[1]), 1.0)]
    else:
        levels = [(v, 1.0) for v in levels]
    # Only levels with headroom for a person, and never more than a handful:
    # every extra level is another occupancy grid.
    levels = sorted({(round(v, 1), round(sh, 4)) for v, sh in levels
                     if v + eye_h < hi[1] + 0.5})[:6]
    # AND LOOK DOWN WHICHEVER AXIS YOU CAN SEE FURTHEST ALONG. The search
    # scores by the clear run in +Z, which is right for eight of the nine
    # modules because a room is modelled with its length down Z. A plant
    # catwalk is not: plant.py runs it ALONG THE ARC -- "the direction a person
    # travels in a ring" -- so it is 80 m in X and 1.8 m in Z, and aiming down
    # Z pointed the camera across a 1.8 m walkway into 139 million cubic metres
    # of unlit void. Swapping the axes and taking the better score costs one
    # more grid and needs no per-module knowledge.
    # When the module DECLARED its walkway, its long axis is the answer and no
    # search is needed. That matters because the score below is "how far can
    # you see", and empty void scores highest: at the plant catwalk's height
    # the bay is clear for 441 m down Z and the walkway is 1.8 m wide in that
    # direction, so the honest-looking metric aimed the camera off the side of
    # the walkway into the dark.
    axes = (False, True)
    if walk_spans:
        w = a[np.unique(tri[np.concatenate(
            [np.arange(l, h) for _n, l, h in walk_spans])])]
        span = w.max(axis=0) - w.min(axis=0)
        axes = (True,) if span[0] > span[2] else (False,)
    swapped = a[:, [2, 1, 0]]
    best = None
    for v, share in levels:
        for flip in axes:
            pts = swapped if flip else a
            e, m, score = _standpoint_at(pts, tri, v + eye_h, clear_m,
                                          floor_y=v)
            # WEIGHTED BY HOW MUCH FLOOR THE LEVEL IS. View length alone put
            # the command and control camera at y = -0.20 m -- standing in the
            # 1.9 m instrument pit with its eyes at deck level, looking down
            # the pit and away from the wall courses that light the room. The
            # pit is real floor and a person can be in it, so rejecting it
            # outright would be wrong; it is 17% of the room's horizontal area
            # against the main deck's 47%, and that is the thing that makes one
            # of them THE floor. Multiplying is enough to settle it and still
            # lets a small level win when it is the only one worth standing on.
            score *= share
            if best is None or score > best[0]:
                best = (score, (e[2], e[1], e[0]) if flip else e,
                        (m[2], m[1], m[0]) if flip else m)
    return best[1], best[2]


def _standpoint_at(a, tri, y, clear_m, floor_y=None):
    """The standpoint search at one height. See `open_standpoint`."""
    import numpy as np

    lo, hi = a.min(axis=0), a.max(axis=0)
    y = min(max(y, lo[1] + 0.3), hi[1] - 0.3)

    # OCCUPANCY FROM TRIANGLE FOOTPRINTS, NOT FROM VERTICES. The first version
    # scored each candidate by its distance to the nearest VERTEX in the eye's
    # y band, and put the Zocalo camera inside a bulkhead: a 30 m x 8 m end cap
    # is two triangles with four corners between them, so its middle is thirty
    # metres from the nearest vertex and reads as the most open spot in the
    # room. The frame came back a flat grey field. Coarse architecture is
    # exactly what this has to handle, so what is rasterised is each triangle's
    # xz footprint -- the same method rooms.walkable uses, which has been right
    # about a racking run standing in front of the only door.
    p = a[tri]                                                # (n, 3, 3)
    y0, y1 = p[:, :, 1].min(axis=1), p[:, :, 1].max(axis=1)
    # Knee to just overhead. A floor spans no height at all and never
    # intersects this band, which is why the deck does not block the room.
    solid = (y1 > y - 0.9) & (y0 < y + 0.9)
    cell = 0.25
    nx = max(4, int((hi[0] - lo[0]) / cell) + 1)
    nz = max(4, int((hi[2] - lo[2]) / cell) + 1)
    blocked = np.zeros((nx, nz), dtype=bool)
    q = p[solid]
    if len(q):
        i0 = np.clip(((q[:, :, 0].min(axis=1) - lo[0]) / cell).astype(int), 0, nx - 1)
        i1 = np.clip(((q[:, :, 0].max(axis=1) - lo[0]) / cell).astype(int), 0, nx - 1)
        j0 = np.clip(((q[:, :, 2].min(axis=1) - lo[2]) / cell).astype(int), 0, nz - 1)
        j1 = np.clip(((q[:, :, 2].max(axis=1) - lo[2]) / cell).astype(int), 0, nz - 1)
        for k in range(len(q)):
            blocked[i0[k]:i1[k] + 1, j0[k]:j1[k] + 1] = True

    # AND THERE HAS TO BE A FLOOR UNDER IT. "Nothing blocks the body" and
    # "something holds the body up" are different questions and only the first
    # was being asked, so the camera stood over the command and control pit's
    # open mouth, off the near end of the docking bay's deck, and outside the
    # council chamber's raised floor -- three rooms out of eight, each with a
    # perfectly good deck a few metres away. A level's histogram says the floor
    # EXISTS; it does not say it is under this particular cell.
    if floor_y is not None:
        holds = np.zeros((nx, nz), dtype=bool)
        fy = p[:, :, 1].mean(axis=1)
        near = np.abs(fy - floor_y) < 0.35
        # Near-horizontal only: a wall panel crossing the right height is not
        # something to stand on.
        nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
        mag = np.linalg.norm(nrm, axis=1)
        flat_ok = (mag > 1e-12)
        upness = np.zeros(len(p))
        upness[flat_ok] = np.abs(nrm[flat_ok, 1]) / mag[flat_ok]
        f = p[near & flat_ok & (upness > 0.85)]
        for k in range(len(f)):
            fi0 = int(np.clip((f[k, :, 0].min() - lo[0]) / cell, 0, nx - 1))
            fi1 = int(np.clip((f[k, :, 0].max() - lo[0]) / cell, 0, nx - 1))
            fj0 = int(np.clip((f[k, :, 2].min() - lo[2]) / cell, 0, nz - 1))
            fj1 = int(np.clip((f[k, :, 2].max() - lo[2]) / cell, 0, nz - 1))
            holds[fi0:fi1 + 1, fj0:fj1 + 1] = True
        if holds.any():
            blocked |= ~holds

    # Erode by the body radius: standing 0.1 m from a wall is not standing
    # somewhere, and a camera at the near plane against a surface renders it as
    # a flat field, which is the artefact this whole function exists to avoid.
    pad = max(1, int(clear_m / cell))
    free = ~blocked
    for s in range(1, pad + 1):
        free[s:, :] &= ~blocked[:-s, :]
        free[:-s, :] &= ~blocked[s:, :]
        free[:, s:] &= ~blocked[:, :-s]
        free[:, :-s] &= ~blocked[:, s:]

    def _pt(i, j):
        return (float(lo[0] + (i + 0.5) * cell), float(y),
                float(lo[2] + (j + 0.5) * cell))

    aim_x = float((lo[0] + hi[0]) / 2)
    if not free.any():
        # Nowhere clear at all. Score 0, so a level that IS clear wins.
        return ((aim_x, y, float(lo[2] + 1.0)),
                (aim_x, y, float(hi[2] - 0.5)), 0.0)

    # STAND WHERE YOU CAN SEE DOWN THE ROOM. Picking the free cell nearest the
    # near end is not the same thing and the Zocalo proved it: `zoc_bulkhead`
    # caps both ends of the run at z 0 and z 32.4, the stall awnings overhang
    # to z -1.89, and the nearest free cell was therefore OUTSIDE the concourse
    # with an end cap filling the frame. Scoring by the clear run AHEAD makes
    # that cell worth nothing and a cell inside the volume worth 130.
    ahead = np.zeros((nx, nz), dtype=np.int32)
    for j in range(nz - 2, -1, -1):
        ahead[:, j] = np.where(free[:, j + 1], ahead[:, j + 1] + 1, 0)
    ahead = np.where(free, ahead, -1)
    best = int(ahead.max())
    # Among the cells that see nearly as far, the one furthest back, so the
    # shot is from the end of the volume rather than from its middle.
    good = ahead >= max(1, int(best * 0.85))
    js = np.where(good.any(axis=0))[0]
    j = int(js[0])
    col = good[:, j]
    runs, start = [], None
    for i in range(nx + 1):
        if i < nx and col[i] and start is None:
            start = i
        elif start is not None and (i == nx or not col[i]):
            runs.append((start, i - 1))
            start = None
    s, e = max(runs, key=lambda r: r[1] - r[0])
    eye = _pt((s + e) // 2, j)
    # Aim at the end of the clear run, on the centreline of the VOLUME rather
    # than of the eye's own aisle: a shot that tracks the aisle it stands in
    # never shows the room widening. Clamped to what is actually visible, so a
    # capped run aims at its cap and not through it.
    aim_z = min(float(hi[2] - 0.5),
                eye[2] + (int(ahead[(s + e) // 2, j]) + 1) * cell)
    # The score is HOW FAR YOU CAN SEE, in metres, which is what picks between
    # standing levels: the plant bay's tank-farm floor sees a wall of frame and
    # its catwalk sees 400 m down the bay.
    return eye, (aim_x, y, aim_z), float(best) * cell


def build_interior(args, out_dir):
    """One room, lit by its own fittings, from the inside."""
    import rooms as R

    room = args.room or "corridor"
    verts, tris, spans, extent = interior_geometry(room)

    # Camera: `rooms.standpoint` searches the walkable grid, so the eye stands
    # where a person could stand. For the kit there is no prop to avoid, so the
    # centreline just inside the near end is right.
    if args.eye and args.target:
        eye, aim = tuple(args.eye), tuple(args.target)
    elif extent is not None:
        w, ln = extent
        ceil = max(q[1] for q in verts)
        x, z = R.standpoint(verts, tris, spans, w, ln)
        h = min(_eye_h(args), ceil - 0.4)
        eye, aim = (x, h, z), (0.0, h, ln / 2.0 - 0.2)
    elif room in ("corridor", "junction"):
        # The kit has no prop to avoid, so the centreline just inside the near
        # end is right and is cheaper than searching for it.
        zs = [q[2] for q in verts]
        eye = (0.0, _eye_h(args), min(zs) + 1.2)
        aim = (0.0, _eye_h(args), max(zs) - 0.5)
    else:
        # A bespoke module: no declared extent and no prop naming convention,
        # so the standpoint is searched for against the geometry itself.
        walk = [sp for sp in spans
                if any(f in sp[0] for f in WALK_SURFACE.get(
                    __import__("directory").by_key(room)["module"], ()))]
        eye, aim = open_standpoint(verts, tris, _eye_h(args),
                                   walk_spans=walk or None)

    obj = os.path.join(out_dir, f"{room}.obj")
    write_obj(obj, verts, tris, per_triangle(spans, len(tris)))
    glb = to_glb(obj, os.path.join(out_dir, f"{room}.glb"))
    n, names = glb_triangles(glb)
    if n != len(tris):
        raise ValueError(f"{room}: glb has {n} triangles, source has "
                         f"{len(tris)}")

    rng = (args.light_range if args.light_range != 1100.0
           else INTERIOR_LIGHT_RANGE_M)
    lights = fixture_lights(verts, tris, spans,
                            args.fixture_energy * room_exposure(room), rng,
                            shadow_n=(INTERIOR_SHADOW_LIGHTS
                                      if args.shadow_lights is None
                                      else args.shadow_lights), eye=eye)
    fill = (soft_fill_run(verts, tris, spans,
                          args.soft_fill * room_exposure(room))
            if args.soft_fill > 0.0 and room in SOFT_FILL_SPACES else [])
    lights = lights + fill
    print(f"interior {room}: {len(lights) - len(fill)} fitting light(s), "
          f"{len(fill)} soft fill at energy {args.soft_fill}")
    return {
        "shot": "interior",
        "scene": "res://scenes/interior.tscn",
        "glb": [glb],
        "triangles": n,
        "groups": sorted(set(names)),
        "lights": lights,
        "room": room,
        # Per-room ambient. interior.tscn carries one calibrated number and it
        # is the residential corridor's; a brig and a chapel are not lit to the
        # same fill and AMBIENT_RATIO has said so, in a table nothing read,
        # since it was measured.
        #
        # UNCHANGED BY THE SOFT FILL, which is a measurement and not an
        # oversight -- see the block above SOFT_FILL.
        "ambient": (args.ambient if args.ambient is not None
                    else ambient_energy(room)),
        # Near plane at 60 mm: indoors the camera can stand against a wall, and
        # the drum's 0.15 m clips a prop the eye is leaning over.
        "camera": {"eye": list(eye), "target": list(aim), "up": [0.0, 1.0, 0.0],
                   "fov": SHOT_FOV_DEG if args.fov is None else args.fov,
                   "near": 0.06, "far": 400.0},
        "sun_from": None,
    }


# ---------------------------------------------------------------------------
# The deck shot -- the assembled build, as a player stands in it
# ---------------------------------------------------------------------------
# THE ONE THING THIS FILE COULD NOT RENDER WAS THE BUILD. `--shot interior`
# renders ONE ROOM, on its own, in a local Y-up frame with a camera the exporter
# invents. `station/deck.py` assembles the thing a player is actually put into
# -- a ring corridor with its rooms opening off it, its doors, its vestibules,
# its furniture and its inhabitants, at its real radius seven kilometres down
# the station -- and `station/walkable.py` walks a body through it. Between
# those two there was no way to LOOK at it.
#
# What filled the gap was an ad-hoc rig hand-written into a scratch JSON: four
# omni lights and an ambient of 0.34. Measured against the corridor anchor that
# frame read p5 x11.09 against a x1.29 band with zero crushed pixels, and the
# number was worthless in both directions, because nobody could say how much of
# it was the build and how much was the four lights somebody chose. A frame from
# a rig that does not ship measures the rig.
#
# So this shot places NOTHING by hand. Every source is a fitting the deck's own
# generators tagged, found by `fixture_lights` exactly as in a room shot; the
# scene is `interior.tscn`, which has no lights in it at all; the exposure is
# stated below and inherited rather than invented; and the camera is the SHIPPED
# player camera, read out of `godot/scripts/player.gd`.

PLAYER_GD = os.path.join(ROOT, "godot", "scripts", "player.gd")


def player_camera(path=PLAYER_GD):
    """The shipped player camera, read off `player.gd` rather than restated.

    A frame that claims to show what a player sees has to be taken through the
    lens a player has. Godot's `Camera3D` defaults to 75 degrees and this
    project's render shots default to 46, and `player.gd` sets 70 for a reason
    it writes down -- `station/budget.py` counts the frustum at 70. Three
    numbers, and the only one that is the answer to "what does the player see"
    is the one in the player.

    Parsed, for the same reason `scene_material_rules` parses the .tscn instead
    of keeping a Python copy of the material rules: two copies of a number
    drift, and this one would drift silently, because a frame at the wrong fov
    looks like a frame.

    Also returns the gravity convention, which is what a ring shot's `up` and
    its spot aims are derived from. It is checked rather than read: if
    `gravity_dir()` stops being "radial about +Z", every aim and every up vector
    in this shot is wrong and the render still looks like a render.
    """
    with open(path) as f:
        text = f.read()

    def num(pattern, what):
        m = re.search(pattern, text)
        if not m:
            raise ValueError(
                f"{os.path.relpath(path, ROOT)}: cannot find {what}. The deck "
                f"shot reads the shipped player camera out of this file so "
                f"that the two cannot disagree; if it has been restructured, "
                f"fix the pattern here rather than hard-coding the number.")
        return float(m.group(1))

    radial = re.search(
        r"gravity_dir\(\).*?Vector3\(\s*global_position\.x\s*,\s*"
        r"global_position\.y\s*,\s*0\.0\s*\)", text, re.S)
    if not radial:
        raise ValueError(
            f"{os.path.relpath(path, ROOT)}: gravity_dir() no longer derives "
            f"'down' as the radial direction about +Z. The deck shot aims "
            f"every spot and orients the camera from that convention.")
    return {"fov": num(r"_cam\.fov\s*=\s*([0-9.]+)", "the camera fov"),
            "eye_height_m": num(
                r"var\s+eye_height_m\s*:\s*float\s*=\s*([0-9.]+)",
                "eye_height_m"),
            "spin_axis": "z"}


# THE DECK'S EXPOSURE IS INHERITED FROM THE CORRIDOR ANCHOR AND IS NOT DERIVED,
# and saying so is the whole of the claim.
#
# The block around ROOM_EXPOSURE records at length why it cannot be derived the
# way those eleven values were: `gain *= 1.40 * ref_median / our_median` assumes
# the median scales with exposure, and measured over the reference corpus
# d(ln median)/d(ln gain) runs from 0.97 to 0.01 and goes NEGATIVE on four
# frames. Producing a twelfth number by the same arithmetic would add a twelfth
# unfalsifiable row to a table that already carries nine.
#
# What can be said honestly is what the deck IS. Measured on blue/0/0, the first
# deck `walkable.py` walks: 450,096 of 589,216 triangles -- 76.4% -- are
# `interior.ring_arc`, which is `interior_kit`'s corridor section swept round
# the ring. That is the same geometry, the same fittings and the same materials
# as `docs/engine-corridor.png`, the frame that DEFINES 1.00 for this project
# against `reference/07-sector-grey/grey level 1.webp`. The dominant surface in
# a deck frame is the surface the anchor was measured on, so the anchor is what
# it takes, and the rooms' own fittings keep their own archetype's value through
# `deck_fixture_exposure` below.
#
# WHAT WOULD REPLACE IT: a deck frame measured against `grey level 1.webp` with
# `tools/measure_frame.py --against`, by the same code every other exposure in
# this file was set by. That is a measurement this shot now makes possible and
# did not exist before it. The first one is recorded in EXPOSURE_FRAMES below;
# it is evidence about the RIG, and changing this constant to chase its median
# would be doing the invalid thing again.
DECK_EXPOSURE = 1.0

# Which deck the shot assembles when nothing says otherwise. blue/0/0 is the one
# `station/walkable.py` walks and the one milestone W2 was closed on, so it is
# the deck with a walk verdict to put beside a frame.
DEFAULT_DECK = "blue/0/0"

# How far ahead the camera looks when it is not aimed at a named place: metres
# along the corridor arc, and metres along the station axis. 14 m is four bays
# of the kit's 3.07 m division, which is the run the reference corridor frames
# show before the perspective closes.
DECK_FACE_M = (14.0, 0.0)


def parse_deck(s):
    """`sector/ring/deck` -> (str, int, int)."""
    parts = str(s).split("/")
    if len(parts) != 3:
        raise SystemExit(f"--deck wants sector/ring/deck, got {s!r} "
                         f"(e.g. {DEFAULT_DECK})")
    return parts[0], int(parts[1]), int(parts[2])


def deck_fixture_exposure(name):
    """Exposure for one tagged span on an assembled deck, by which room it is in.

    The corridor kit's own fittings carry no address and take the anchor, which
    is what the anchor IS. A room's fittings carry `<place_key>__` and take that
    place's own `room_exposure`, which is the value the interior shot would give
    them if the room were rendered alone.

    STRICT ON PURPOSE: an address that is not a place key raises, because on a
    deck the only thing that produces one is `deck.build_deck`, and a change to
    how it names a room's groups is a change this shot has to know about.
    """
    if "__" not in name:
        return DECK_EXPOSURE
    return room_exposure(name.rsplit("__", 1)[0])


def spots_lighting_the_floor(lights, floor_r_m):
    """Which spot fittings actually put light on the floor beneath them.

    Returns (n_spots, n_lit, misses). THE REGRESSION THIS EXISTS TO CATCH is a
    spot on a ring aimed at world -Y, which is what `fixture_lights` did for
    every shot before the deck one: inside a spun ring "down" is radially
    outward, so a -Y aim points ALONG the ring and the cone lands on a wall
    forty metres away instead of on the deck under the fitting.

    IT HAS TO BE A GEOMETRIC TEST AND NOT A COMPARISON OF AIM VECTORS. At ring
    angle 270 the outward radial IS (0, -1, 0), so a -Y aim is accidentally
    correct there. THIS IS NOT HYPOTHETICAL: swept over twelve decks in four
    sectors, 44 spots, the -Y rig lights the floor beneath 14 of them -- every
    one on `grey/0/22` (rooms at 230 deg) and `grey/0/70` (260 deg). A gate
    that asked "is the aim radial", or one that ran on either of those two
    decks, would have been green with the defect live. This asks the question
    the fitting exists to answer -- is the deck directly beneath it inside this
    lamp's cone and within its reach.

    The floor point is the fitting's own position pushed out to the shell's
    floor radius, so `q - p` is exactly `radial_aim(p) * (floor_r - r)` and the
    angle between the aim and it is one dot product.
    """
    misses, lit = [], 0
    spots = [lt for lt in lights if lt.get("kind") == "spot"]
    for lt in spots:
        p = lt["pos"]
        r = math.hypot(p[0], p[1])
        drop = floor_r_m - r
        if drop <= 0.0:
            misses.append((lt["group"], "at or below the floor radius"))
            continue
        if drop > lt["range"]:
            misses.append((lt["group"],
                           f"floor {drop:.2f} m below, range {lt['range']} m"))
            continue
        out = radial_aim(p)
        aim = lt["aim"]
        n = math.dist(aim, (0.0, 0.0, 0.0)) or 1.0
        cos = sum(aim[k] * out[k] for k in range(3)) / n
        off = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        if off > lt["angle"]:
            misses.append((lt["group"],
                           f"aimed {off:.1f} deg off the floor beneath it, "
                           f"cone {lt['angle']} deg"))
            continue
        lit += 1
    return len(spots), lit, misses


def deck_camera(args, stats, cam):
    """Where the eye stands on an assembled deck, and what it looks at.

    THE DECK KNOWS WHERE THINGS ARE, so nothing here is a world coordinate typed
    in by hand. `--at` is a gazetteer place key and the eye stands at that
    place's own angle on the corridor floor; `--at-offset` moves it in metres
    along the arc and along the station axis, which are the two directions a
    person can walk. `--face` aims at another place. The alternative -- raw
    `--eye x,y,z --target x,y,z` at a radius of 211.528 and a z of 7121.305 --
    is how the ad-hoc rig was written, and it is unreadable and unre-derivable.

    UP IS INWARD. On a spun ring the floor is the inside of a barrel, so a
    standing person's head points AT the spin axis. `render_shot.gd` takes the
    up vector from the shot for exactly this reason and warns that getting it
    wrong "puts the ground on the ceiling in a frame symmetric enough to hide
    the mistake" -- which on a corridor, whose section is very nearly
    symmetrical top to bottom, it genuinely is.
    """
    import directory as dr                                       # noqa: PLC0415

    meta = stats["collision_meta"]
    floor_r, cz = meta["floor_r_m"], meta["z_m"]
    eye_h = (cam["eye_height_m"] if args.eye_height is None
             else args.eye_height)

    at = args.at or stats["spawn_at"]
    a0 = math.radians(dr.by_key(at)["angle_deg"])
    da, dz = args.at_offset if args.at_offset else (0.0, 0.0)
    # The eye's radius, not the floor's: up is inward, so a standing eye is
    # `eye_h` CLOSER to the axis than the deck it stands on.
    r_eye = floor_r - eye_h
    a_eye = a0 + da / floor_r
    eye = (r_eye * math.cos(a_eye), r_eye * math.sin(a_eye), cz + dz)

    if args.face:
        q = dr.by_key(args.face)
        a_t, z_t = math.radians(q["angle_deg"]), q["z_m"]
    else:
        fa, fz = args.face_offset if args.face_offset else DECK_FACE_M
        a_t, z_t = a_eye + fa / floor_r, eye[2] + fz
    aim = (r_eye * math.cos(a_t), r_eye * math.sin(a_t), z_t)
    up = (-math.cos(a_eye), -math.sin(a_eye), 0.0)
    return eye, aim, up


def build_deck_shot(args, out_dir):
    """One assembled deck, lit by its own fittings, from standing height."""
    import deck as D                                             # noqa: PLC0415

    sector, ring, deck = parse_deck(args.deck)
    cam = player_camera()
    schema, profile = it.load()
    verts, tris, groups, stats = D.build_deck(
        schema, profile, sector, ring, deck, z_m=args.deck_z,
        max_rooms=args.max_rooms)
    spans = to_spans(groups, len(tris))

    if args.eye and args.target:
        eye, aim = tuple(args.eye), tuple(args.target)
        r = math.hypot(eye[0], eye[1]) or 1.0
        up = (-eye[0] / r, -eye[1] / r, 0.0)
    else:
        eye, aim, up = deck_camera(args, stats, cam)

    stem = f"shot_{sector}_{ring}_{deck}"
    obj = os.path.join(out_dir, f"{stem}.obj")
    write_obj(obj, verts, tris, per_triangle(spans, len(tris)))
    glb = to_glb(obj, os.path.join(out_dir, f"{stem}.glb"))
    n, names = glb_triangles(glb)
    if n != len(tris):
        raise ValueError(f"{stem}: glb has {n} triangles, source has "
                         f"{len(tris)}")

    rng = (args.light_range if args.light_range != 1100.0
           else INTERIOR_LIGHT_RANGE_M)
    lights = fixture_lights(
        verts, tris, spans, args.fixture_energy, rng,
        shadow_n=(INTERIOR_SHADOW_LIGHTS if args.shadow_lights is None
                  else args.shadow_lights),
        eye=eye, down=radial_aim, exposure=deck_fixture_exposure)
    # The corridor's off-camera key. A deck is 76% corridor, and until this
    # existed the whole assembly was lit by a flat ambient -- see SOFT_FILL.
    fill = (soft_fill_ring(stats["collision_meta"],
                           args.soft_fill * DECK_EXPOSURE)
            if args.soft_fill > 0.0 else [])
    lights = lights + fill

    # REPORTED AT EXPORT, not only in the self-test. A deck whose fittings light
    # a wall instead of its floor still produces a plausible PNG, and the number
    # that says otherwise has to be in front of whoever runs the render.
    n_spot, n_lit, misses = spots_lighting_the_floor(lights,
                                                     stats["collision_meta"]
                                                     ["floor_r_m"])
    print(f"deck {sector}/{ring}/{deck}: {stats['rooms']} rooms, "
          f"{len(tris)} triangles, {len(lights)} lights "
          f"({n_spot} spot, {n_lit} of them on the floor beneath them), "
          f"{len(fill)} of them soft fill, "
          f"exposure {DECK_EXPOSURE} (inherited from the corridor anchor)")
    if misses:
        print(f"  {len(misses)} spot(s) light nothing beneath them: "
              f"{misses[:3]}")
    if stats["unopened"]:
        print(f"  rooms with no door: {stats['unopened']}")
    if stats["skipped"]:
        print(f"  rooms that did not build: {stats['skipped']}")

    return {
        "shot": "deck",
        # THE INTERIOR SCENE, and not one of its own. interior.tscn declares no
        # lights at all and carries the 434 material rules `materials.py
        # --export` writes; a deck is interiors, so a second scene file would be
        # a second copy of that block and would stop matching the library the
        # first time a material was added.
        "scene": "res://scenes/interior.tscn",
        "glb": [glb],
        "triangles": n,
        "groups": sorted(set(names)),
        "lights": lights,
        "deck": f"{sector}/{ring}/{deck}",
        "room": args.at or stats["spawn_at"],
        "rooms": stats["rooms"],
        "actors": len(stats.get("actors", ())),
        "exposure": DECK_EXPOSURE,
        # The residential corridor's measured fill, which is what the deck's
        # 76% corridor takes. One ambient per SCENE is a Godot property, so the
        # rooms cannot each have their own here the way a single-room shot does
        # -- recorded rather than papered over.
        #
        # UNCHANGED BY THE SOFT FILL. The fill is additive; see the block above
        # SOFT_FILL for the derivation that said it should not be and the frame
        # that overturned it. One consequence worth stating anyway: the fill's
        # cone is bounded, so it lifts the CORRIDOR's deck and reaches about
        # 1.7 m into a room past its corridor wall and no further. A deck's 87
        # rooms still have only their own tagged fittings and one scene ambient
        # between them, and a per-room fill needs a light per room.
        "ambient": (args.ambient if args.ambient is not None
                    else ambient_energy("corridor") * DECK_EXPOSURE),
        "camera": {"eye": list(eye), "target": list(aim), "up": list(up),
                   "fov": (cam["fov"] if args.fov is None else args.fov),
                   "near": 0.06, "far": 400.0},
        "sun_from": None,
    }


SHOTS = {"exterior": build_exterior, "drum": build_drum,
         "interior": build_interior, "deck": build_deck_shot}


def build(args):
    out_dir = os.path.join(SCENE_DIR, args.shot)
    os.makedirs(out_dir, exist_ok=True)
    scene = SHOTS[args.shot](args, out_dir)
    scene["out_png"] = args.out
    path = os.path.join(out_dir, "scene.json")
    with open(path, "w") as f:
        json.dump(scene, f, indent=1)
    scene["scene_json"] = path
    return scene


# ---------------------------------------------------------------------------
# Material rules, read back out of the scene file
# ---------------------------------------------------------------------------

def scene_material_rules(tscn_path):
    """Mesh-name fragments the .tscn binds a material to.

    Parsed rather than duplicated. The alternative is a copy of the rule list
    in Python, and two copies of a mapping drift -- the group renames itself in
    the generator, the Python copy is updated, the scene is not, and the mesh
    renders on the fallback material. That failure is invisible in a render
    when the fallback is grey and the intended material is also grey.
    """
    with open(tscn_path) as f:
        text = f.read()
    m = re.search(r"material_rules\s*=\s*\{(.*?)\n\}", text, re.S)
    if not m:
        return []
    return re.findall(r'"([^"]+)"\s*:', m.group(1))


def unmatched_groups(groups, rules):
    """Groups no rule matches -- i.e. everything that lands on the fallback."""
    return sorted(g for g in groups
                  if not any(frag in g for frag in rules))


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _selftest():
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL: {label}")

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    r0 = it.sector_radius(schema, profile, sector)

    # -- light runs -------------------------------------------------------
    runs = light_runs(schema, profile, sector, per_run=8)
    check(all(len(r) == 8 for r in runs), "every run sampled equally")

    # Every light must sit ON the truss that is supposed to carry it, and that
    # is checked against the BUILT TRUSS MESH rather than against the constants
    # the light positions were computed from.
    #
    # The first two versions of this were worthless and the breakage harness
    # proved it: one compared len(runs) against 2 * TRUSS_COUNT, and the other
    # compared the light radius against a `want` recomputed from
    # TRUSS_RADIUS_FRAC. Both sides moved together, so setting
    # TRUSS_RADIUS_FRAC to 0.60 -- which puts every light 111 m away from its
    # tube -- was scored as passing. Comparing against the mesh cannot do that:
    # the mesh is built by a different function from a different call path.
    #
    # Compared in the XY plane only, because a truss chord is one long beam
    # with vertices at its two ends, so a light at mid-span is a kilometre from
    # the nearest vertex in 3-D and 2.2 m from it in section.
    tv, tt, tm = it.drum_guideways(schema, profile, sector)
    truss_xy = {(round(v[0], 2), round(v[1], 2)) for v in tv}
    worst = 0.0
    for run in runs:
        p = run[0]
        d = min(math.hypot(p[0] - x, p[1] - y) for x, y in truss_xy)
        worst = max(worst, d)
    check(worst < 4.0,
          f"every light run lies on a built truss in section "
          f"(worst offset {worst:.2f} m, tolerance 4 m)")

    # And there must be exactly one run either side of each truss. Truss count
    # is taken from the mesh -- distinct azimuths of its vertices -- not from
    # TRUSS_COUNT, for the same reason.
    truss_az = {round(math.degrees(math.atan2(y, x)) / 10.0)
                for x, y in truss_xy}
    # Each truss occupies a small span of azimuths; cluster them by gap.
    ordered = sorted(truss_az)
    clusters = 1
    for a, b in zip(ordered, ordered[1:]):
        if b - a > 2:
            clusters += 1
    check(len(runs) == 2 * clusters,
          f"one light run each side of every truss: {len(runs)} runs for "
          f"{clusters} trusses measured off the mesh")

    radii = [math.hypot(p[0], p[1]) for r in runs for p in r]

    # The class of error this catches is a light that has drifted out of the
    # air: below the floor is inside the ground, above the core is inside the
    # shuttle tube. Either renders as a light that lights nothing.
    check(all(r < r0 for r in radii),
          "lights are inboard of the habitat floor, i.e. in the air")
    check(all(r > ct.CORE_TUBE_R_M for r in radii),
          "lights are outboard of the core tube")

    # Energy is normalised by sampling density, so the drum's brightness does
    # not change when the light count is tuned for cost. Called through the
    # real function `build_drum` uses, not recomputed here -- an assertion that
    # re-derives the value it is checking is an algebraic identity, and this
    # project already has two of those on record.
    check(abs(light_energy(8) * 8 - light_energy(32) * 32) < 1e-9,
          "total run energy independent of sample count")

    # Samples at cell centres, not at the span ends.
    ex = schema["sectors"]["extents_m"][sector]
    z0, z1 = float(ex["z0"]), float(ex["z1"])
    zs = [p[2] for p in runs[0]]
    check(min(zs) > z0 and max(zs) < z1,
          f"no light sample lands on an end cap ({min(zs):.0f}..{max(zs):.0f} "
          f"inside {z0:.0f}..{z1:.0f})")

    # -- the camera is not buried ----------------------------------------
    # This is the failure that has now happened twice in this project: an eye
    # hand-placed at the nominal floor radius while the ground under it stood
    # 7 m proud. Assert the standing eye is genuinely above the terrain.
    buried = 0
    for ang in range(0, 360, 17):
        for z in (z0 + 200.0, (z0 + z1) / 2, z1 - 200.0):
            eye, up = dg.stand_on_ground(schema, profile, sector, ang, z,
                                         eye_h=1.7)
            s = dg.terrain_sample(schema, profile, sector, ang, z)
            r_eye = math.hypot(eye[0], eye[1])
            if r_eye >= s["radius_m"] - 1e-6:
                buried += 1
    check(buried == 0, f"standing eye is above the terrain everywhere "
                       f"({buried} buried samples)")

    # "Up" inside the drum points at the spin axis. Getting this backwards
    # renders the sky as the floor and is not obvious in a symmetric frame.
    bad_up = 0
    for ang in range(0, 360, 23):
        eye, up = dg.stand_on_ground(schema, profile, sector, ang,
                                     (z0 + z1) / 2)
        radial = (eye[0], eye[1])
        n = math.hypot(*radial) or 1.0
        if up[0] * radial[0] / n + up[1] * radial[1] / n > -0.999:
            bad_up += 1
    check(bad_up == 0, f"interior up vector points at the spin axis "
                       f"({bad_up} wrong)")

    # -- material coverage ------------------------------------------------
    # Every group a shot emits must be bound by a rule in its scene. A group
    # that falls through to the fallback renders as a plausible grey, which is
    # exactly the kind of wrong that survives a render pass.
    shot_groups = drum_groups(schema, profile, sector)
    rules = scene_material_rules(os.path.join(ROOT, "godot/scenes/drum.tscn"))
    missing = unmatched_groups(shot_groups, rules)
    check(not missing,
          f"drum: every emitted group has a material rule "
          f"(unbound: {missing[:6]})")
    check(len(rules) > 20,
          f"drum scene's rule table actually parsed ({len(rules)} rules)")

    # -- the shell and the ground are the same surface --------------------
    # `interior.drum_interior()` and `drum_ground` both draw the drum floor at
    # the same radius, so emitting both z-fights across four and a half million
    # square metres. Checked by comparing group VOCABULARIES, taken from the
    # two generators themselves: the shell names its bands drum_*, the ground
    # names its ground_*, and an overlap means the shot has picked up both.
    # An earlier version of this assertion scanned this file's own source text
    # for the string "drum_interior" and failed on its own explanatory comment
    # -- a test that could only be satisfied by not writing the comment.
    # Full circumference at a coarse tessellation: the band vocabulary is a
    # property of the whole circle, and a 6 degree sample landed inside one
    # band and produced a one-name "vocabulary" that could not have caught
    # anything.
    _v, _t, shell = it.drum_interior(schema, profile, sector, arc_deg=360.0,
                                     seg_deg=10.0, z_step=1200.0)
    shell_groups = set(shell["groups"])
    check(len(shell_groups) >= 2,
          f"shell vocabulary is non-trivial ({len(shell_groups)} groups), so "
          "the disjointness test below can fail")
    overlap = shell_groups & set(shot_groups)
    check(not overlap,
          f"drum shot does not emit the band shell alongside the heightfield "
          f"(overlap: {sorted(overlap)[:4]})")

    # -- the interior light rig -------------------------------------------
    # THE TABLES ARE THREE FILES APART AND THEY DESCRIBE ONE THING. rooms.py
    # decides which fitting an archetype gets, materials.py gives the fitting
    # a colour, and FIXTURE_LIGHTING here decides whether it casts anything.
    # A fitting missing from any one of the three is a defect that renders as
    # "slightly dim" and nothing else notices.
    import rooms as R                                          # noqa: PLC0415
    import materials as mats                                   # noqa: PLC0415

    arches = {a for a, _keys in R.ARCHETYPES} | {"generic"}
    check(arches <= set(ROOM_EXPOSURE),
          f"every archetype has a calibrated exposure "
          f"(missing {sorted(arches - set(ROOM_EXPOSURE))})")
    check(arches <= set(AMBIENT_BY_ARCHETYPE),
          f"every archetype has an ambient ratio "
          f"(missing {sorted(arches - set(AMBIENT_BY_ARCHETYPE))})")
    fittings = {n for a in R.LIGHTS for n, *_ in R.LIGHTS[a]}
    unpainted = {n for n in fittings if not mats.resolve_any(n, "interior")}
    check(not unpainted,
          f"every room fitting resolves to a material ({sorted(unpainted)})")
    dark = {n for n in fittings
            if not mats.resolve_any(n, "interior").emission}
    check(not dark,
          f"every room fitting resolves to something that EMITS ({sorted(dark)})")
    # Absent from FIXTURE_LIGHTING means emissive-only, which is a MEASURED
    # claim per fitting and not a default anyone may fall into by forgetting.
    # These four are recorded `emissive_only` in docs/layer4-lighting/*.json.
    emissive_only = {"light_service_tube", "light_bar_backlight",
                     "light_indicator_red", "light_deck_channel"}
    unaccounted = fittings - set(FIXTURE_LIGHTING) - emissive_only
    check(not unaccounted,
          f"every room fitting is a measured source or a measured emissive "
          f"({sorted(unaccounted)})")
    check(not (emissive_only & set(FIXTURE_LIGHTING)),
          "no fitting is declared emissive-only and given a light too")
    # Now that membership rather than spelling is the gate, a TYPO in a key is
    # a fitting that silently never lights. So every key must be a group some
    # generator actually emits. rooms.py and interior_kit are asked directly;
    # the bespoke modules come from the layer-3 gate, which already builds all
    # sixteen for its coverage count.
    emitted = {n for a in R.LIGHTS for n, *_ in R.LIGHTS[a]}
    import interior_kit as _kit                                # noqa: PLC0415
    import test_materials_layer3 as l3gate                     # noqa: PLC0415
    _kit.reset_tags()
    for _v, _t in (_kit.corridor_section(21.6),
                   _kit.corridor_junction_section(6.0)):
        emitted |= {n for n, _lo, _hi in _kit.tagged_spans(_t)}
    for _m, _groups in l3gate.bespoke_groups(*it.load()).items():
        emitted |= {g for g in _groups if not g.startswith("__error__")}
    ghost = set(FIXTURE_LIGHTING) - emitted
    check(not ghost,
          f"every fitting given a light is a group something emits ({sorted(ghost)})")
    for n, spec in FIXTURE_LIGHTING.items():
        check(spec["kind"] in ("omni", "spot"), f"{n}: known light kind")
        check(spec["kind"] != "spot" or 0.0 < spec["angle_deg"] < 90.0,
              f"{n}: a spot has a cone under 90 degrees")
        check(0.0 < spec["energy_rel"] <= 1.0, f"{n}: energy_rel in (0, 1]")
        check(spec.get("range_m", 1.0) > 0.0, f"{n}: a positive range")
    # The exposure is an EXPOSURE, not a rescue: a value that has run away by
    # more than an order of magnitude either side means a fitting's own energy
    # or range is wrong and is being papered over here.
    check(all(0.1 <= g <= 10.0 for g in ROOM_EXPOSURE.values()),
          f"no archetype's exposure has run away "
          f"({[k for k, g in ROOM_EXPOSURE.items() if not 0.1 <= g <= 10.0]})")
    check(room_exposure("corridor") == 1.0,
          "the corridor is the anchor and its exposure is 1.0")

    # -- a span is not a fitting, and a fitting is not always a point -------
    # Both corrections are invisible in a still if you are not counting, and
    # both were live for a session: one span became one lamp however many
    # fittings it held, and a fitting longer than its own throw was collapsed
    # to a centroid standing off it. The measured recoveries are the gate,
    # because they are numbers the MODULES chose and this code has to
    # rediscover:
    #   docking_bay  LAMPS_PER_BAY_GIRDER=3 x 13 girders = 39
    #   zocalo       5 rib lamps per rib, measured, x 6 ribs = 30
    #   command_control  four wall courses, one per measured course
    def _lamps(room):
        v, t, g, _e = interior_geometry(room)
        return fixture_lights(v, t, g, 3.0 * room_exposure(room), 7.0)

    _bay = _lamps("docking_bays")
    check(len(_bay) == 39,
          f"the docking bay recovers its three floods a girder ({len(_bay)})")
    _zoc = [x for x in _lamps("zocalo") if x["group"] == "zoc_rib_lamp"]
    check(len(_zoc) == 30,
          f"the Zocalo recovers its five rib lamps a rib ({len(_zoc)})")
    # Stated on the bodies as well as on the lamps, because the lamp count of
    # an EXTENDED fitting is a sampling decision and can land on the right
    # number for the wrong reason -- reverting the body split and letting the
    # sampler loose on the whole span happened to give the Zocalo 30 lamps
    # again. `command_control` emits its four wall courses consecutively under
    # one group, which is the case `to_spans` cannot see, and four is a count
    # the module chose rather than one this file can arrive at by tuning.
    _cv, _ct, _cg = interior_geometry("cnc")[:3]
    _courses = [len(fitting_bodies(_cv, _ct, lo, hi))
                for n, lo, hi in _cg if n == "cc_light_strip"]
    check(_courses == [4],
          f"one span of cc_light_strip is four wall courses ({_courses})")
    # EVERY LIGHT SITS ON THE FITTING IT STANDS FOR. This is defect 1 written
    # as a property, and it is the one that fires on a revert of either half of
    # the fix -- the counts above catch the split, this catches the placement.
    #
    # MEASURED AS A SURFACE DISTANCE, and that is the whole difficulty. An
    # "inside its bounding box" version was written first and was VACUOUS: the
    # centroid of a set of points is inside their bounding box by construction,
    # so both defective lamps passed it. The council chamber is the case that
    # shows why -- a semicircular arc's bounding box is the half-disc, and a
    # lamp 3.89 m out in front of the arc sits comfortably in the middle of it.
    # Vertex distance is no better: a wall course is an 8.6 m box with eight
    # corners, so a sample correctly placed at its midpoint is 4 m from the
    # nearest vertex. `open_standpoint` has the same lesson written on it.
    #
    # `surface_points` is therefore reused as the probe. Distance to the
    # nearest sampled point OVER-estimates distance to the surface by at most
    # the sampling spacing, so a pass here implies a pass on the true distance,
    # which is the safe direction for a gate.
    #
    # The threshold is a fraction of the fitting's OWN reach, because 0.77 m
    # off a flood that throws 30 m is a point source and 0.77 m off a downlight
    # that throws 1.2 m is not. Measured over every lit fitting in these rooms,
    # with the rig before this change and after it:
    #
    #   after   0.008 .. 0.075  (worst: zoc_stall_light, a merged bulb string)
    #   before  0.008 .. 1.976  (cc_light_strip 1.976 -- a lamp twice its own
    #                            range from the strip it represents --
    #                            zoc_rib_lamp 0.288, light_house_cove 0.216)
    #
    # 0.125 is the geometric middle of that gap: 67% clear of the worst pass
    # and 42% clear of the nearest failure.
    astray = []
    for _room in ("corridor", "council_chamber", "cnc", "zocalo",
                  "docking_bays"):
        _v, _t, _g = interior_geometry(_room)[:3]
        for _name, _lo, _hi in _g:
            if _name not in FIXTURE_LIGHTING:
                continue
            _reach = FIXTURE_LIGHTING[_name].get("range_m") or 7.0
            _probe = surface_points(_v, _t, list(range(_lo, _hi)),
                                    _reach / 40.0, max_split=48)
            for _lt in fixture_lights(_v, _t, [(_name, _lo, _hi)], 1.0, 7.0):
                _d = min(math.dist(_lt["pos"], _p) for _p, _w in _probe)
                if _d > 0.125 * _reach:
                    astray.append(f"{_room}/{_name} {_d:.2f} m of {_reach} m")
                    break
    check(not astray,
          f"every light sits ON the fitting it stands for ({astray[:3]})")

    # -- the camera stands ON a floor ---------------------------------------
    # It did not. Session 3o's level search scored candidate standing heights
    # by how far you could see from them, and in command and control that put
    # the eye at y = -0.20 m: standing in the 1.9 m instrument pit with its
    # eyes at deck level, looking down the pit and away from the wall courses
    # that light the room. The exposure calibrated against that shot was
    # therefore calibrated against a frame of the underside of a floor.
    #
    # Two causes, both fixed: the level was reported at its histogram bin's
    # LEFT EDGE, which is up to 0.5 m below the surface it stands for; and the
    # search preferred a long view over a large floor, so a narrow pit beat the
    # deck above it. The pit is real floor and a person can be in it -- it is
    # 17% of the room's horizontal area against the main deck's 47%, and that
    # is what makes one of them THE floor.
    #
    # The gate is that the eye sits a standing height above SOME real surface
    # of the room, which is a property no view-length score can satisfy by
    # accident.
    floors = []
    for _room in ("cnc", "zocalo", "council_chamber", "customs_north",
                  "alien_sector", "docking_bays", "bar_unnamed", "qtr_command"):
        _v, _t, _g, _x = interior_geometry(_room)
        _walk = [sp for sp in _g if any(
            f in sp[0] for f in WALK_SURFACE.get(
                __import__("directory").by_key(_room)["module"], ()))]
        _eye, _aim = open_standpoint(_v, _t, 1.7, walk_spans=_walk or None)
        # UNDER THE EYE'S FOOTPRINT, not near a vertex. A customs deck is one
        # large quad and its corners are twenty metres from the camera; asking
        # for a nearby VERTEX failed both of the rooms with the biggest floors
        # in the project. That is the third time this session that vertex
        # distance has been the wrong question about coarse architecture --
        # `open_standpoint` and the light-placement gate had it too.
        _drop = None
        for _k in range(len(_t)):
            _q = [_v[i] for i in _t[_k]]
            _y = sum(x[1] for x in _q) / 3.0
            if not _eye[1] - 2.0 < _y < _eye[1] - 1.2:
                continue
            if (min(x[0] for x in _q) - 0.3 <= _eye[0] <= max(x[0] for x in _q) + 0.3
                    and min(x[2] for x in _q) - 0.3 <= _eye[2]
                    <= max(x[2] for x in _q) + 0.3):
                _d = _eye[1] - _y
                _drop = _d if _drop is None else min(_drop, _d)
        if _drop is None:
            floors.append(f"{_room}: nothing under the eye to stand on")
    check(not floors, f"the camera stands on a floor ({floors})")

    # THE ANCHOR MUST NOT MOVE. docs/engine-corridor.png is what every exposure
    # in this file was calibrated against, so a change to the rig that alters
    # the corridor invalidates ROOM_EXPOSURE and BESPOKE_EXPOSURE together.
    # Twelve lamps at 36.0 total energy, and both numbers are checked because
    # either could move alone.
    _cor = _lamps("corridor")
    check(len(_cor) == 12 and abs(sum(x["energy"] for x in _cor) - 36.0) < 1e-6,
          f"the corridor anchor is unmoved ({len(_cor)} lamps, "
          f"{sum(x['energy'] for x in _cor):.2f} energy)")

    # -- and the two new pieces must be able to fail -----------------------
    # A gate that cannot fail is worse than no gate. Both of these are checked
    # on constructed geometry rather than on a room, so they say something
    # about the ALGORITHM and not about whatever the generators happen to emit.
    # A quad drawn as two triangles, plus a third triangle ten metres away.
    _v = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0),
          (9.0, 0.0, 0.0), (10.0, 0.0, 0.0), (9.0, 1.0, 0.0)]
    _t = [(0, 1, 2), (1, 3, 2), (4, 5, 6)]
    check(len(fitting_bodies(_v, _t, 0, 2)) == 1,
          "two triangles sharing an edge are one fitting")
    check(len(fitting_bodies(_v, _t, 0, 3)) == 2,
          "a third triangle ten metres away is a second fitting")
    # Welding by POSITION, not by index: council_chamber._M.quad appends four
    # fresh vertices per quad, so index connectivity would call one continuous
    # cove twelve fittings and multiply its flux by twelve.
    _dv = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
           (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]
    check(len(fitting_bodies(_dv, [(0, 1, 2), (3, 4, 5)], 0, 2)) == 1,
          "triangles that share an EDGE BY POSITION are one body, even with "
          "no shared vertex index")
    # The sampler's weights are areas, so they must sum to the area. A silent
    # error here would redistribute a fitting's energy, not lose it, which is
    # the kind of defect a render cannot show.
    _tri = [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 4.0, 0.0)]
    _w = sum(w for _p, w in surface_points(_tri, [(0, 1, 2)], [0], 0.4))
    check(abs(_w - 6.0) < 1e-9, f"the sampler's weights sum to the area ({_w})")
    _parts = sample_body(_tri, [(0, 1, 2)], [0], 1.0)
    check(abs(sum(sh for _p, sh in _parts) - 1.0) < 1e-9,
          "a sampled fitting's shares sum to one, so sampling never changes "
          "how much light is in the room")
    check(len(_parts) > 1, f"an extended fitting is sampled ({len(_parts)})")
    # AND THE SHARES ARE AREAS, not one over the count. Summing to one is true
    # of both and cannot tell them apart, so this asks a shape the two answers
    # disagree about: an area-6 triangle beside an area-0.06 one, ten metres
    # off. By area the far one takes 0.99% of the light; one-over-N would give
    # it a third. The far sliver is one cluster and the big triangle is many,
    # so getting this wrong dumps most of a strip's light on its end cap.
    _uneven = [(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 4.0, 0.0),
               (20.0, 0.0, 0.0), (20.3, 0.0, 0.0), (20.0, 0.4, 0.0)]
    _far = sum(sh for p, sh in sample_body(
        _uneven, [(0, 1, 2), (3, 4, 5)], [0, 1], 1.0) if p[0] > 15.0)
    check(abs(_far - 0.06 / 6.06) < 1e-6,
          f"a sample's share of its fitting's energy is its share of the "
          f"fitting's AREA ({_far:.4f} against {0.06 / 6.06:.4f})")
    # THE MERGE MUST NOT UNDO THE SAMPLING. FIXTURE_MERGE_M is 0.9 m and a
    # sample pitch is range/4, so every fitting that throws less than 3.6 m
    # samples at a pitch INSIDE the merge radius -- `zoc_stall_light` at
    # 2.5 m samples at 0.625 m. Distance alone cannot tell "two bulbs on one
    # string" from "two samples of one strip"; identity can, and this is the
    # constructed case that proves the identity is being used, because nothing
    # in the library is currently both short-range and long enough to trip it.
    _strip = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (0.0, 0.0, 0.1),
              (5.0, 0.0, 0.1)]
    _st = [(0, 1, 2), (1, 3, 2)]
    _sl = fixture_lights(_strip, _st, [("zoc_stall_light", 0, 2)], 1.0, 7.0)
    check(len(_sl) > 4,
          f"a 5 m fitting throwing 2.5 m keeps its samples through the "
          f"0.9 m merge ({len(_sl)} lamps)")

    # -- the bespoke modules the interior shot can now assemble -------------
    import directory as dr                                     # noqa: PLC0415
    import quarters as Q                                       # noqa: PLC0415

    # to_spans, against all four shapes it exists for. Written first because
    # the shape normaliser is where a silent wrong answer would live: three of
    # the four shapes degrade into something plausible rather than raising.
    check(to_spans([("a", 0, 2), ("b", 2, 4)], 4) == [("a", 0, 2), ("b", 2, 4)],
          "to_spans passes spans through")
    check(to_spans(["a", "a", "b", "a"], 4)
          == [("a", 0, 2), ("b", 2, 3), ("a", 3, 4)],
          "to_spans turns a per-triangle list into RUNS, not one span a group")
    check(to_spans({"groups": [("a", 0, 3)]}, 3) == [("a", 0, 3)],
          "to_spans reads the metadata dict shape")
    check(to_spans(None, 7) == [("structure", 0, 7)],
          "to_spans names the default rather than leaving it empty")

    qplaces = {q["key"] for q in dr.PLACES if q["module"] == "quarters"}
    check(set(QUARTERS_CLASS) == qplaces,
          f"every quarters place maps to a class "
          f"(missing {sorted(qplaces - set(QUARTERS_CLASS))}, "
          f"stale {sorted(set(QUARTERS_CLASS) - qplaces)})")
    qclasses = {c["key"] for c in Q.CLASSES}
    check(set(QUARTERS_CLASS.values()) <= qclasses,
          f"every mapped class exists in quarters.CLASSES "
          f"({sorted(set(QUARTERS_CLASS.values()) - qclasses)})")
    # Two places share `diplomatic` and that is deliberate; a mapping that
    # collapsed to ONE class would render seven frames of one room and look
    # like coverage.
    check(len(set(QUARTERS_CLASS.values())) >= 5,
          f"the quarters mapping distinguishes classes "
          f"({len(set(QUARTERS_CLASS.values()))} distinct)")

    # Every interior-scene module that owns a place must be assemblable, or the
    # shot silently cannot look at those locations -- which is how fifty of
    # them reached layer 3 without a single interior frame ever being rendered.
    owning = {q["module"] for q in dr.PLACES if q["module"]}
    interior_mods = {m for m in owning
                     if l3gate.BESPOKE_SCENE.get(m, "interior") == "interior"}
    # `signage` builds a sign board -- a prop that stands in other rooms, not a
    # room. `interior_kit` IS the corridor, and `interior_geometry` handles it
    # by name as the two pseudo-rooms rather than through this table.
    missing = interior_mods - set(BESPOKE_GEOMETRY) - {"signage", "interior_kit"}
    check(not missing,
          f"every interior-scene bespoke module can be assembled ({sorted(missing)})")
    check(set(BESPOKE_GEOMETRY) <= owning,
          f"no entry builds a module that owns no place "
          f"({sorted(set(BESPOKE_GEOMETRY) - owning)})")

    # -- the deck shot: the assembled build ---------------------------------
    # EVERY ASSERTION HERE IS RUN AGAINST THE CASE THAT HAS THE DEFECT IN IT,
    # which is the lesson session 3x paid for: `interior_kit`'s tag-coverage gate
    # ran on a corridor with no doors, so four defects lived in the doorway for a
    # session. Both defects this section exists for are properties of an
    # ASSEMBLED deck and neither can appear in a single-room shot -- a room shot
    # has no addressed group names and no ring -- so the fixture is a real deck.
    #
    # `max_rooms=1` for cost: one room, a 24 degree arc, 66,340 triangles and a
    # few seconds, and it still carries an addressed fitting AND a spot on a
    # ring, which is everything under test. Anything cheaper would be a fixture
    # that cannot express either defect.
    import deck as _D                                            # noqa: PLC0415

    # The shipped player camera, read rather than restated.
    _cam = player_camera()
    check(_cam["fov"] > 0.0 and _cam["eye_height_m"] > 0.0
          and _cam["spin_axis"] == "z",
          f"player.gd's camera and gravity convention parse ({_cam})")
    # NEGATIVE CONTROL: it must not fall back to a default when the file it is
    # reading stops saying what it is reading. A silent default here renders
    # every deck frame at the wrong fov, which looks exactly like a frame.
    try:
        player_camera(os.path.abspath(__file__))
        check(False, "player_camera refuses a file that is not player.gd")
    except ValueError:
        check(True, "player_camera refuses a file that is not player.gd")

    # `fixture_key`, against all four cases. An exact name wins; an addressed
    # name resolves to its fitting; a name that is neither is emissive-only.
    check(fixture_key("light_downlight") == "light_downlight",
          "fixture_key passes an exact fitting name through")
    check(fixture_key("docking_bays__light_highbay") == "light_highbay",
          "fixture_key strips a room's address off its fitting")
    check(fixture_key("kit_wall_plate") is None,
          "fixture_key does not invent a fitting for a plain group")
    check(fixture_key("docking_bays__prop_deck_marking") is None,
          "fixture_key does not invent a fitting for an addressed non-fitting")

    _dv, _dt, _dg, _ds = _D.build_deck(schema, profile, "blue", 0, 0,
                                       max_rooms=1)
    _dspans = to_spans(_dg, len(_dt))
    _dmeta = _ds["collision_meta"]

    # THE FIXTURE HAS TO HAVE THE DEFECT AVAILABLE TO IT. If `deck.build_deck`
    # ever stops addressing a room's groups, the lookup gate below passes for the
    # wrong reason and this is the line that says so.
    _addressed = [n for n, _l, _h in _dspans
                  if "__" in n and fixture_key(n) is not None]
    check(_addressed,
          "the deck fixture carries an ADDRESSED fitting, so the lookup gate "
          "is measuring the case with the defect in it")

    _dl = fixture_lights(_dv, _dt, _dspans, 3.0, INTERIOR_LIGHT_RANGE_M,
                         eye=_ds["spawn"], down=radial_aim,
                         exposure=deck_fixture_exposure)
    # THE ROOMS ARE LIT. Before `fixture_key`, FIXTURE_LIGHTING was an
    # exact-name table and every fitting inside every room of a deck matched
    # nothing: measured on the full blue/0/0, 822 corridor spans became lamps and
    # 28 room spans became none. The deck rendered with a lit corridor and black
    # rooms, and no gate could fire, because a room with no tagged fitting coming
    # back black IS the documented behaviour of this rig.
    _inroom = [x for x in _dl if "__" in x["group"]]
    check(_inroom, f"the fittings inside a deck's rooms cast light "
                   f"({len(_inroom)} of {len(_dl)} lamps)")

    # SPOTS AIM AT THE FLOOR, AND ON A RING THE FLOOR IS NOT AT -Y.
    _n_spot, _lit, _miss = spots_lighting_the_floor(_dl, _dmeta["floor_r_m"])
    check(_n_spot > 0,
          f"the deck fixture contains a spot at all, so the aim gate is not "
          f"vacuously true ({_n_spot} spots)")
    check(_n_spot and _lit == _n_spot,
          f"every spot on the ring lights the floor beneath it "
          f"({_lit}/{_n_spot}, misses {_miss[:2]})")
    # NEGATIVE CONTROL, and it is the regression itself rather than a mutation
    # of the result: the same fittings, the same deck, `down` left at the -Y
    # default every other shot uses. Measured on this fixture the four high bays
    # come out 89.2 degrees off a 35 degree cone.
    _dl_y = fixture_lights(_dv, _dt, _dspans, 3.0, INTERIOR_LIGHT_RANGE_M,
                           eye=_ds["spawn"], exposure=deck_fixture_exposure)
    _ny, _lity, _missy = spots_lighting_the_floor(_dl_y, _dmeta["floor_r_m"])
    check(_ny == _n_spot and _lity == 0,
          f"a spot aimed at world -Y on a ring lights NOTHING beneath it "
          f"({_lity}/{_ny} still on the floor -- this gate cannot fail)")

    # NO LAMP IN MID-AIR. `render_shot.gd` records that a light positioned
    # before it is parented silently stays at the origin, which inside this
    # station is on the spin axis lighting nothing. A bounding-box test is weak
    # in general -- the light-placement gate above says why -- but the origin is
    # 211 m outside this box in the radial direction and 7 km along the axis, so
    # it is exactly the question worth asking here.
    _blo = [min(q[j] for q in _dv) for j in range(3)]
    _bhi = [max(q[j] for q in _dv) for j in range(3)]
    _out = [x["group"] for x in _dl
            if not all(_blo[j] - 0.5 <= x["pos"][j] <= _bhi[j] + 0.5
                       for j in range(3))]
    check(not _out, f"every deck lamp is inside the deck ({_out[:3]})")

    # EACH ROOM'S FITTINGS TAKE THEIR OWN ROOM'S EXPOSURE, and the corridor kit
    # takes the anchor. One number for a whole deck would apply an exposure
    # measured on one generator's geometry to another's, which is the mistake
    # BESPOKE_EXPOSURE is written to warn about.
    check(deck_fixture_exposure("light_downlight") == DECK_EXPOSURE,
          "the corridor kit's own fittings take the anchor")
    check(deck_fixture_exposure("docking_bays__light_highbay")
          == room_exposure("docking_bays") != DECK_EXPOSURE,
          f"a room's fittings take that room's exposure "
          f"({deck_fixture_exposure('docking_bays__light_highbay')} vs the "
          f"anchor's {DECK_EXPOSURE})")

    # -- the soft fill ----------------------------------------------------
    # THE OFF-CAMERA KEY, and every gate here is written against a defect that
    # actually happened during the build. See SOFT_FILL.
    _fill = soft_fill_ring(_dmeta, SOFT_FILL_ENERGY)
    # THE PITCH IS METRIC, NOT ANGULAR -- a ring at 211 m and a ring at 300 m
    # get the same spacing between lamps and not the same number of them, which
    # a count-based check would let drift.
    # It is measured where the light LANDS -- one deck radius out -- because
    # that is the spacing the corridor sees; the sources themselves sit 10 m
    # nearer the axis and are correspondingly closer together.
    _da = abs(math.atan2(_fill[1]["pos"][1], _fill[1]["pos"][0])
              - math.atan2(_fill[0]["pos"][1], _fill[0]["pos"][0]))
    _gap = _da * _dmeta["floor_r_m"]
    check(abs(_gap - SOFT_FILL_PITCH_M) < 0.05,
          f"consecutive fill footprints sit one bay-half apart on the deck "
          f"({_gap:.3f} m vs {SOFT_FILL_PITCH_M} m)")

    # 1. IT FOLLOWS THE RING'S OWN DOWN. This is the one a DirectionalLight3D
    #    cannot do, and the check is the same one the fittings get.
    _nf, _fl, _fm = spots_lighting_the_floor(_fill, _dmeta["floor_r_m"])
    check(_nf == len(_fill) and _fl == _nf,
          f"every soft-fill source lights the deck beneath it "
          f"({_fl}/{_nf}, misses {_fm[:2]})")
    # NEGATIVE CONTROL: the same run with the world -Y a directional light
    # would impose. On a 344 degree arc that is right at two angles and wrong
    # everywhere else, and the count says how wrong.
    _flat = [dict(x, aim=[0.0, -1.0, 0.0]) for x in _fill]
    _n2, _l2, _m2 = spots_lighting_the_floor(_flat, _dmeta["floor_r_m"])
    check(_l2 < _nf * 0.05,
          f"one world-space DOWN cannot serve a 344 degree corridor: "
          f"{_l2}/{_n2} sources would still light their own deck")

    # 2. THE CONE HOLDS THE WHOLE BAY. Three earlier versions did not, and the
    #    one that mattered most held the deck and missed the walls, which the
    #    frame reported as the fill delivering exactly nothing to a wall.
    _hw = _corridor_half_w_m(_dmeta)
    _ch = _dmeta["floor_r_m"] - _dmeta["ceil_r_m"]
    _cone = math.radians(soft_fill_cone_deg(_hw, _ch))
    _corner = math.atan2(math.hypot(_hw, SOFT_FILL_PITCH_M / 2.0),
                         SOFT_FILL_HEIGHT_M - _ch)

    def _ang(a):
        """Godot's `1 - rim^k` at an angle off the cone axis."""
        rim = (1.0 - math.cos(a)) / (1.0 - math.cos(_cone))
        return 1.0 - min(rim, 1.0) ** SOFT_FILL_ANGLE_ATTENUATION

    # THE BAR IS A LITERAL AND NOT `SOFT_FILL_CORNER_FLOOR`, deliberately.
    # Comparing the outcome against the constant the cone was SOLVED from is
    # the both-sides-move-together defect this file's own light-placement gate
    # was rewritten to remove: set the constant to 0 and the cone collapses onto
    # the corner, the corner keeps 0.000 of the axial value, and `>= 0 - 1e-9`
    # still passes. 0.85 sits below the 0.90 the design asks for and above the
    # 0.29 that the shipped 0.6 attenuation would leave.
    check(_ang(_corner) >= 0.85,
          f"the bay's far top corner keeps {_ang(_corner):.3f} of the axial "
          f"value (design floor {SOFT_FILL_CORNER_FLOOR}, gate 0.85)")
    # AND IT IS BOUNDED. A cone can always be widened until nothing fails, and
    # widening it is free in the corridor and expensive in the rooms next door,
    # so the spill is asserted rather than described.
    _spill = SOFT_FILL_HEIGHT_M * math.tan(_cone) - _hw
    check(0.0 < _spill <= SOFT_FILL_MAX_SPILL_M,
          f"the fill lands {_spill:.2f} m past the corridor wall, inside the "
          f"{SOFT_FILL_MAX_SPILL_M} m bound")
    # And version 1 of the bug: the cone sized to the wall FOOT misses the wall
    # TOP, because every point of a wall above its foot is at a larger angle.
    _foot = math.atan2(_hw, SOFT_FILL_HEIGHT_M)
    check(_corner > _foot * 1.2,
          f"the bay corner ({math.degrees(_corner):.1f} deg) is well outside "
          f"the wall foot ({math.degrees(_foot):.1f} deg), so a cone sized to "
          f"the deck cannot light a wall")

    # 3. RANGE IS A CUTOFF. Godot's window is 0.0078 at d/r = 0.98, and a range
    #    sized to the far corner cost a whole render.
    def _win(d, r):
        return max(1.0 - (d / r) ** 4, 0.0) ** 2

    check(_win(SOFT_FILL_HEIGHT_M, SOFT_FILL_RANGE_M) > 0.95,
          f"the deck sits in the flat part of the distance window "
          f"({_win(SOFT_FILL_HEIGHT_M, SOFT_FILL_RANGE_M):.3f})")
    check(_win(SOFT_FILL_HEIGHT_M,
               math.hypot(SOFT_FILL_HEIGHT_M, _hw)) < 0.05,
          "a range sized to the corridor's own far corner would multiply the "
          "whole fill by under 1/20 -- this is the control that says the "
          "window is real and not a rounding detail")

    # 4. IT DOES NOT TOUCH THE SOFFIT, which is what makes the ceiling rung a
    #    property of the geometry rather than of a number. Every source sits
    #    INWARD of the ceiling, and the ceiling's visible face points outward.
    check(all(math.hypot(x["pos"][0], x["pos"][1])
              < _dmeta["ceil_r_m"] - 1.0 for x in _fill),
          "every fill source is clear of the corridor's ceiling, so the soffit "
          "faces away from it")

    # 5. THE PLACEMENT IS THE FLOOR'S, NOT A NUMBER'S. Move the meta and the
    #    key moves with it -- hard rule 4 applied to light.
    _moved = soft_fill_ring(dict(_dmeta, floor_r_m=_dmeta["floor_r_m"] + 25.0,
                                 ceil_r_m=_dmeta["ceil_r_m"] + 25.0),
                            SOFT_FILL_ENERGY)
    check(abs(math.hypot(_moved[0]["pos"][0], _moved[0]["pos"][1])
              - math.hypot(_fill[0]["pos"][0], _fill[0]["pos"][1]) - 25.0)
          < 1e-6,
          "a deck at another radius takes its key with it")

    # THE CAMERA STANDS ON THE CORRIDOR FLOOR AND ITS HEAD POINTS AT THE AXIS.
    # Both are ring properties with no analogue in a room shot, and both are
    # invisible in a still: a corridor section is nearly symmetrical top to
    # bottom, so an inverted frame reads as a corridor.
    class _A:                                       # the shot's own defaults
        at = face = ""
        at_offset = face_offset = None
        eye_height = 1.7
    _eye, _aim, _up = deck_camera(_A(), _ds, _cam)
    _r = math.hypot(_eye[0], _eye[1])
    check(_dmeta["ceil_r_m"] < _r < _dmeta["floor_r_m"],
          f"the eye is between the deck and the soffit "
          f"({_r:.3f} in {_dmeta['ceil_r_m']:.3f}..{_dmeta['floor_r_m']:.3f})")
    check(abs(_dmeta["floor_r_m"] - _r - _cam["eye_height_m"]) < 1e-6,
          f"the eye is a shipped standing height above the deck "
          f"({_dmeta['floor_r_m'] - _r:.3f} m vs {_cam['eye_height_m']} m)")
    check(abs(_eye[2] - _dmeta["z_m"]) <= _dmeta["half_w_m"],
          f"the eye is inside the corridor's width, not in a wall "
          f"({_eye[2] - _dmeta['z_m']:.3f} m of +/-{_dmeta['half_w_m']:.3f})")
    _outward = radial_aim(_eye)
    check(sum(_up[k] * _outward[k] for k in range(3)) < -0.999,
          f"the camera's up points AT the spin axis, which is where a standing "
          f"head is on a spun ring ({_up})")
    # And it is a place key that put it there, not a coordinate.
    check(_ds["spawn_at"] in {q["key"] for q in dr.PLACES},
          f"the deck's default standpoint is a gazetteer place "
          f"({_ds['spawn_at']})")

    # THE PLAYER'S LENS IS NOT THE RENDER SHOTS' LENS, which is why `--fov`
    # defaults to None rather than to 46: with a float default, "nobody said"
    # and "the user asked for 46" are the same value, and a deck shot that
    # asked for 46 would silently have been taken at 70.
    check(SHOT_FOV_DEG != _cam["fov"],
          f"the shot camera ({SHOT_FOV_DEG} deg) and the player's "
          f"({_cam['fov']} deg) are different lenses, so which one a deck "
          f"frame was taken through is a question with an answer")

    check(parse_deck("blue/0/0") == ("blue", 0, 0), "parse_deck reads a deck")
    check("deck" in SHOTS and SHOTS["deck"] is build_deck_shot,
          "the deck shot is registered, so render_godot.sh --shot deck works")

    # -- glb integrity ----------------------------------------------------
    # Only if something has already been exported; a bare checkout has not.
    probe = os.path.join(SCENE_DIR, "drum", "ground.glb")
    if os.path.exists(probe):
        # Caught rather than raised. `glb_triangles` raises on a malformed
        # file, which is right for the export path -- a bad glb should stop the
        # pipeline -- but wrong here: an exception aborts the run and the
        # remaining assertions never execute, so a single corrupt file hides
        # every other result. The breakage harness found this by corrupting the
        # magic and getting a traceback instead of a "FAIL:" line.
        try:
            n, names = glb_triangles(probe)
            check(n > 0 and names,
                  f"exported ground.glb parses: {n} triangles")
        except (ValueError, KeyError, OSError) as exc:
            check(False, f"exported ground.glb parses: {exc}")
        with open(probe, "rb") as f:
            head = f.read(12)
        check(struct.unpack("<I", head[8:12])[0] == os.path.getsize(probe),
              "exported glb declared length matches its size")
    else:
        print("note: no exported scene to check; run --shot drum first")

    # -- exterior material coverage, reported not gated --------------------
    # The drum's coverage is asserted above. The EXTERIOR's never was, and it is
    # worse: 21 of the hull's 32 groups match no rule in exterior.tscn, so every
    # greeble group and the drum's own `green_section` render on the fallback.
    # That is why a re-render of `docs/engine-exterior.png` at its own committed
    # camera does not reproduce it (8.69% speckled pixels against 5.72%): the
    # surfaces are not the ones the frame was judged on.
    #
    # Printed rather than checked, deliberately. `godot/scenes/exterior.tscn` is
    # not this file's to edit, and a hard check here turns
    # tools/build_and_render.sh red for every other agent until someone else's
    # file changes. It should BECOME a check the moment the .tscn binds them --
    # a note that nobody promotes is how this stayed invisible for two sessions.
    hull_man = os.path.join(GENERATED, "hull_manifest.json")
    ext_tscn = os.path.join(ROOT, "godot/scenes/exterior.tscn")
    if os.path.exists(hull_man) and os.path.exists(ext_tscn):
        ext_rules = scene_material_rules(ext_tscn)
        hull_groups = sorted(json.load(open(hull_man))["groups"])
        unbound = unmatched_groups(hull_groups, ext_rules)
        if unbound:
            print(f"note: exterior.tscn binds {len(ext_rules)} rules and leaves "
                  f"{len(unbound)} of {len(hull_groups)} hull groups on the "
                  f"fallback material: {', '.join(unbound[:6])}...")

    # -- hull LOD selection ------------------------------------------------
    # The chain is derived in station/lod.py and flattened into the manifest;
    # this is the consumer. What can go wrong here and nowhere else: selecting
    # on the aim point instead of the near point, an off-by-one at a switch
    # boundary, and an override that silently renders something else.
    man_path = os.path.join(GENERATED, "lod_manifest.json")
    if os.path.exists(man_path):
        levels = json.load(open(man_path))["levels"]
        check(len(levels) >= 2, f"lod manifest has a chain ({len(levels)} levels)")

        # Selection must agree with the manifest at, just below and just above
        # every switch distance. The just-below case is the one that matters:
        # `>=` written as `>` puts every boundary in the wrong level and no
        # render would show it.
        wrong = []
        for i, lv in enumerate(levels):
            d = lv["switch_distance_m"]
            for delta, want in ((0.0, lv["name"]),
                                (+1.0, lv["name"]),
                                (-1.0, levels[max(0, i - 1)]["name"])):
                if d + delta < 0:
                    continue
                # Put the eye on the axis, `d` beyond the nose, so the nearest
                # point of the bounding box is exactly `d` away by construction.
                eye = (0.0, 0.0, it_length() + d + delta)
                _p, got, dist, _w = pick_hull_lod(eye, (0.0, 0.0, 0.0))
                if got != want or abs(dist - (d + delta)) > 1.0:
                    wrong.append((lv["name"], delta, got, round(dist)))
        check(not wrong,
              f"LOD selection matches the manifest at every switch boundary "
              f"(mismatches: {wrong[:4]})")

        # Measured to the NEAREST point, not the aim point. Constructed so the
        # two answers differ by more than a switch band: an eye abeam the
        # station's midpoint is `length/2` closer to the near end than to the
        # far end, and selecting on the aim point would say otherwise.
        half = it_length() / 2.0
        eye = (0.0, 0.0, it_length() + 1000.0)
        near = hull_near_distance(eye)
        aim = math.dist(eye, (0.0, 0.0, half))
        check(near < aim - 1000.0,
              f"selection distance is to the near end ({near:,.0f} m), not to "
              f"the aim point ({aim:,.0f} m)")

        # Every level the chain can select must have a mesh on disk, or the
        # renderer quietly falls back to hull.obj and draws the finest level at
        # 100 km. The fallback exists; it must never be the normal path.
        missing = [lv["name"] for lv in levels
                   if not os.path.exists(
                       os.path.join(GENERATED, f"hull_{lv['name']}.obj"))]
        check(not missing, f"every chain level has a built mesh: missing {missing}")

        # The override must reach the level asked for, and must refuse a name
        # the chain does not have rather than rendering lod0 and saying nothing.
        _p, got, _d, _w = pick_hull_lod((0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                                        forced=levels[-1]["name"])
        check(got == levels[-1]["name"],
              f"--lod override reaches {levels[-1]['name']} (got {got})")
        # Caught broadly and scored, not allowed to propagate. An exception here
        # aborts the run and every assertion after it silently never executes --
        # the failure mode the glb probe below already carries a note about, and
        # the breakage harness reproduced it here by making the refusal fall
        # through into a `None['name']`.
        try:
            _p, got, _d, _w = pick_hull_lod((0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                                            forced="lod99")
            check(False, f"--lod with an unknown level is refused (silently "
                         f"rendered {got})")
        except SystemExit:
            check(True, "--lod with an unknown level is refused")
        except Exception as exc:                     # noqa: BLE001
            check(False, f"--lod with an unknown level is refused clearly, "
                         f"not with {type(exc).__name__}: {exc}")

    # -- budget -----------------------------------------------------------
    # The drum gate is 300,000 triangles (station/budget.py). A shot that
    # cannot be rendered on the target machine is not a shot worth judging
    # lighting on.
    saved = os.path.join(SCENE_DIR, "drum", "scene.json")
    if os.path.exists(saved):
        with open(saved) as f:
            sc = json.load(f)
        check(sc["triangles"] <= 300000,
              f"drum shot within the drum triangle gate: {sc['triangles']}")
        # End-to-end: the energy actually written into the file, summed over
        # every light, must equal one run's worth times the number of runs.
        # The previous version of this line asserted only that the light count
        # was divisible by six, which is true of nearly any plausible mistake.
        runs = 2 * it.TRUSS_COUNT
        total_e = sum(l["energy"] for l in sc["lights"])
        check(abs(total_e - RUN_ENERGY * DRUM_EXPOSURE * runs) < 1e-6,
              f"exported light energy sums to one run's worth per run "
              f"({total_e:.3f} against {RUN_ENERGY * DRUM_EXPOSURE * runs:.3f})")
        check(len(sc["lights"]) % runs == 0,
              f"exported light count is a whole number per run "
              f"({len(sc['lights'])} over {runs} runs)")
        # THE TABLES DESCRIBE THE SHOT THAT EXISTS. `parts` is written by the
        # code that ran `drum_parts`, so a part added to the drum and exported
        # once fails here until every framing has measured it -- which is the
        # only moment anyone would think to. Free: the file is already open.
        if "parts" in sc:
            shot_parts = set(sc["parts"])
            for nm, cal in sorted(DRUM_CALIBRATION.items()):
                miss = sorted(shot_parts - set(cal["contribution"]))
                extra = sorted(set(cal["contribution"]) - shot_parts)
                check(not miss and not extra,
                      f"DRUM_CALIBRATION[{nm!r}] covers exactly the parts the "
                      f"drum shot builds (unmeasured {miss}, gone {extra})")

    # -- the drum's calibrated framings -------------------------------------
    # Structural first, because these cost nothing and fail for a different
    # reason from the frames: a table that is internally wrong describes no
    # render at all, and would keep on being self-consistent while the frames
    # rotted underneath it.
    for nm, cal in sorted(DRUM_CALIBRATION.items()):
        sub = cal["subject"]
        check(sub in cal["contribution"],
              f"{nm}: its declared subject {sub!r} is in its own table")
        check(cal["contribution"].get(sub, 0.0) >= DRUM_FRAME_MIN_PERCENT,
              f"{nm}: the framing shows its subject "
              f"({cal['contribution'].get(sub, 0.0):.2f}% against the "
              f"{DRUM_FRAME_MIN_PERCENT}% floor)")
        # ...and shows it as an OBJECT, not as a scatter of shadow changes.
        check(cal["largest_region"].get(sub, 0.0) >= DRUM_SUBJECT_MIN_PERCENT,
              f"{nm}: its subject is a contiguous body in frame "
              f"({cal['largest_region'].get(sub, 0.0):.2f}% against the "
              f"{DRUM_SUBJECT_MIN_PERCENT}% floor)")
        bad = sorted(k for k, v in cal["largest_region"].items()
                     if v > cal["contribution"].get(k, 0.0) + 1e-9)
        check(not bad,
              f"{nm}: no part's largest contiguous region exceeds the pixels "
              f"that moved at all ({bad})")
        check(set(cal["largest_region"]) == set(cal["contribution"]),
              f"{nm}: both tables cover the same parts")
        # The recorded multiple must be the two recorded medians. Without this
        # the derivation can stay readable and describe nothing.
        pred = cal["verified_median"] / cal["reference_median"]
        check(abs(pred - cal["verified_multiple"]) < 0.005,
              f"{nm}: the recorded calibration is self-consistent "
              f"({pred:.3f} against {cal['verified_multiple']})")
        # ...at the exposure it was taken at. Same guard EXTERIOR_CALIBRATION
        # carries: change DRUM_EXPOSURE and every number above is stale.
        check(abs(cal["exposure"] - DRUM_EXPOSURE) < 1e-9,
              f"{nm}: verified at the exposure the drum is currently at "
              f"({cal['exposure']} against {DRUM_EXPOSURE})")
        check(os.path.exists(os.path.join(ROOT, cal["reference"])),
              f"{nm}: its reference frame exists ({cal['reference']})")
        check(len(cal["signature"]) == 12,
              f"{nm}: carries a 3x4 framing signature "
              f"({len(cal['signature'])} cells)")
        # ...AND A RECORDED DISTRIBUTION VERDICT. Every framing here passes the
        # median band and fails the whole-distribution comparison, and the one
        # thing that must not happen is for that to stop being written down.
        check(set(cal.get("distribution", {})) >=
              {"p5", "p95", "p5/p95", "crushed", "verdict"},
              f"{nm}: records where it sits on the whole distribution, not "
              f"only on the median ({sorted(cal.get('distribution', {}))})")
    # NO TWO FRAMINGS MAY SHARE A SIGNATURE. If they did the gate could not
    # tell them apart, which is the hole `frame_signature` was added to close;
    # this is the check that the closure is still worth anything.
    _names = sorted(DRUM_CALIBRATION)
    for _i, _a in enumerate(_names):
        for _b in _names[_i + 1:]:
            _d = sum(abs(x - y) for x, y in zip(DRUM_CALIBRATION[_a]["signature"],
                                                DRUM_CALIBRATION[_b]["signature"])) / 12
            check(_d > DRUM_SIGNATURE_TOL,
                  f"{_a} and {_b} are distinguishable framings "
                  f"({_d:.4f} against a {DRUM_SIGNATURE_TOL} tolerance)")
    # The reference a drum framing is measured against has to agree with the
    # frame DRUM_EXPOSURE itself was set on, or the framing is quietly asking
    # for a different exposure of the same volume. 33a and 29a fail this and
    # that is why neither is a measurement reference here.
    anchor = DRUM_CALIBRATION["wide"]["reference_median"]
    for nm, cal in sorted(DRUM_CALIBRATION.items()):
        rel = cal["reference_median"] / anchor
        check(abs(rel - 1.0) <= 0.25,
              f"{nm}: its reference agrees with 34b, the frame DRUM_EXPOSURE "
              f"was set on (x{rel:.2f})")
    check(drum_visible_parts() >= {"townscape", "trams"},
          f"the garden and the tram are in a measured frame "
          f"({sorted(drum_visible_parts())})")

    # -- EXPOSURE_FRAMES: the record of what each exposure was measured on ---
    # This table is what makes `--gate-frames` possible at all, and its only
    # failure mode is going stale: an exposure added without a reference, or a
    # path that no longer resolves. Both are checked, and both are checked
    # AGAINST THE EXPOSURE DICTS THEMSELVES rather than against a second list.
    check(set(EXPOSURE_FRAMES["ROOM_EXPOSURE"]) == set(ROOM_EXPOSURE),
          f"every ROOM_EXPOSURE archetype records what it was measured "
          f"against ({sorted(set(ROOM_EXPOSURE) ^ set(EXPOSURE_FRAMES['ROOM_EXPOSURE']))})")
    check(set(EXPOSURE_FRAMES["BESPOKE_EXPOSURE"]) == set(BESPOKE_EXPOSURE),
          f"every BESPOKE_EXPOSURE module records what it was measured "
          f"against ({sorted(set(BESPOKE_EXPOSURE) ^ set(EXPOSURE_FRAMES['BESPOKE_EXPOSURE']))})")
    _missing = [f"{fam}/{k}: {p}"
                for fam, tab in EXPOSURE_FRAMES.items()
                for k, pair in tab.items() for p in pair
                if p is not None and not os.path.exists(os.path.join(ROOT, p))]
    check(not _missing,
          f"every frame and reference EXPOSURE_FRAMES names exists ({_missing})")
    # A NULL FRAME IS NOT A PASS. Nine ROOM_EXPOSURE values have no committed
    # render, so they cannot be verified by anything; the count is asserted so
    # it can only go DOWN, and so that quietly deleting a frame to dodge a
    # failing distribution verdict shows up here instead of nowhere.
    _unver = sorted(f"{fam}/{k}" for fam, tab in EXPOSURE_FRAMES.items()
                    for k, (f_, _r) in tab.items() if f_ is None)
    check(len(_unver) <= 9,
          f"no MORE exposures have become unverifiable ({len(_unver)}: {_unver})")
    # THE PREDICATE IS STILL DRIVEN BY THE MEASUREMENT, and this is the check
    # that keeps it so. With three framings the union of what they show is now
    # every part the drum builds, so there is no part left sitting below the
    # floor to act as a negative example -- and `station/directory.py`'s two
    # assertions that the garden and the tram were NOT lit were exactly that
    # negative example until this session inverted them. Without something in
    # its place, `drum_visible_parts` could be replaced by "return everything"
    # and nothing would notice. So: drop every measured contribution below the
    # floor and the visible set must empty.
    _saved = {k: dict(v["contribution"]) for k, v in DRUM_CALIBRATION.items()}
    try:
        for _c in DRUM_CALIBRATION.values():
            for _k in _c["contribution"]:
                _c["contribution"][_k] = DRUM_FRAME_MIN_PERCENT - 0.01
        check(drum_visible_parts() == set(),
              f"nothing is visible when no framing measures it "
              f"({sorted(drum_visible_parts())})")
    finally:
        for _k, _v in _saved.items():
            DRUM_CALIBRATION[_k]["contribution"] = _v
    check("townscape" in drum_visible_parts(),
          "the real tables are restored after the negative test")
    # `omit_parts` is the measurement's own tool and its failure mode is the
    # measurement's headline finding, so it has to refuse rather than shrug.
    _p = [("ground", [], [], []), ("trams", [], [], [])]
    # `--light-kind spot` is the rig LIGHT_DIRECTIONALITY refutes, and it is
    # kept so that table can be reproduced by running something. The one part of
    # it that can be silently wrong is which way "down" is: inside a spun drum
    # the floor is OUTSIDE the lamps, so the aim is radially outward, and an
    # inward aim lights the core tube while still producing a plausible frame.
    _a = radial_aim((236.6, 0.0, 4900.0))
    check(abs(_a[0] - 1.0) < 1e-9 and abs(_a[1]) < 1e-9 and abs(_a[2]) < 1e-9,
          f"a lamp at +x aims at +x -- away from the spin axis, at the floor "
          f"beneath it, not at the core ({_a})")
    _b = radial_aim((-100.0, -100.0, 0.0))
    check(_b[0] < 0 and _b[1] < 0 and abs(math.hypot(*_b[:2]) - 1.0) < 1e-9,
          f"...and it is a unit vector in the lamp's own quadrant ({_b})")
    try:
        radial_aim((0.0, 0.0, 4900.0))
        check(False, "radial_aim refuses a lamp on the spin axis")
    except ValueError:
        check(True, "radial_aim refuses a lamp on the spin axis")
    check(len(omit_parts(_p, "trams")) == 1, "omit_parts drops a named part")
    check(len(omit_parts(_p, "")) == 2, "omit_parts with nothing named is a "
                                        "no-op")
    try:
        omit_parts(_p, "grnud")
        check(False, "omit_parts refuses a part name that does not exist")
    except SystemExit:
        check(True, "omit_parts refuses a part name that does not exist")
    # THE ENVIRONMENT THE FRAMES WERE RENDERED UNDER. Before the frames, because
    # if the .tscn has moved then every frame verdict below is measuring a
    # picture that cannot be made again and its pass means nothing.
    _env = scene_environment()
    _drift = sorted(k for k in set(_env) | set(DRUM_ENVIRONMENT)
                    if _env.get(k) != DRUM_ENVIRONMENT.get(k))
    check(not _drift,
          "drum.tscn's environment is the one DRUM_CALIBRATION was measured "
          "under: " + ", ".join(
              f"{k} is {_env.get(k, '(absent)')}, recorded "
              f"{DRUM_ENVIRONMENT.get(k, '(absent)')}" for k in _drift))
    # And the frames themselves. SCORED ON THE DISTRIBUTION for every framing
    # not in DRUM_DISTRIBUTION_DEBT, which is new in session 3u:
    # `score_distribution` defaulted off because all three framings failed it
    # and "a self-test that is red for a known reason stops being read". One
    # passes now, so leaving the flag off for that one would leave layer 4b's
    # exit criterion computed and uncounted.
    check(DRUM_DISTRIBUTION_DEBT <= set(DRUM_CALIBRATION),
          f"the distribution debt names framings that exist "
          f"({sorted(DRUM_DISTRIBUTION_DEBT - set(DRUM_CALIBRATION))})")
    for nm in sorted(DRUM_CALIBRATION):
        indebt = nm in DRUM_DISTRIBUTION_DEBT
        good, msg = gate_drum(nm, score_distribution=not indebt)
        check(good, f"drum frame gate: {msg}")
        # THE OTHER HALF OF THE RATCHET: a framing carried as debt must still
        # be failing. Otherwise the list is somewhere to park a framing that has
        # started passing, and the count of what is done drifts downward for
        # free. Same rule directory.py applies to its deferral list.
        if indebt:
            _cal = DRUM_CALIBRATION[nm]
            _png = os.path.join(ROOT, _cal["frame"])
            _ref = os.path.join(ROOT, _cal["reference"])
            if os.path.exists(_png) and os.path.exists(_ref):
                _mf = _measure_frame()
                _rows, _dok = _mf.distribution(
                    _mf.measure(_png), _mf.at_offset(_ref, _mf.RENDER_OFFSET))
                check(not _dok,
                      f"{nm} is carried as distribution debt and still fails "
                      f"the verdict -- if it passes, take it off the list "
                      f"rather than leaving the count wrong")

    # -- the exterior's two lighting conditions ----------------------------
    # Three classes of check, and they are separated because they fail for
    # different reasons: the WIRING (a night shot that quietly renders the day
    # look), the NUMBERS (an exposure that drifted away from the frame it was
    # measured on), and the FRAMES (the rig, the hull material or the window
    # sheet moved under a committed render).
    ext_tscn = os.path.join(ROOT, "godot/scenes/exterior.tscn")
    if os.path.exists(ext_tscn):
        with open(ext_tscn) as f:
            tscn = f.read()
        day_e = scene_env_exposure(ext_tscn, "Env")
        night_e = scene_env_exposure(ext_tscn, "EnvNight")
        # A night side that is not a different exposure is not a night side.
        # This is the cheapest possible guard against the whole feature being
        # wired to nothing, and it costs no render.
        check(night_e > day_e * 2.0,
              f"the night environment is a genuinely different stop "
              f"(day {day_e}, night {night_e})")
        check("night_environment = SubResource(\"EnvNight\")" in tscn,
              "the root node mounts EnvNight as its night environment")
        # The rim is the specific light whose aim makes it a frontal fill on
        # the anti-sun side. If it is ever dropped from this list the night
        # frame gets its camera-facing edge lit again, which is the defect the
        # condition exists to remove -- and the frame would still look
        # plausible.
        m = re.search(r"night_lights_off = PackedStringArray\(([^)]*)\)", tscn)
        off = re.findall(r'"([^"]+)"', m.group(1)) if m else []
        check("Rim" in off and "Fill" in off,
              f"the night condition darkens the rim and the fill (has {off})")
        # Every name in that list has to BE a light in this scene. GDScript
        # errors on a miss at render time; this catches it without a render,
        # because a typo there leaves the light burning.
        lights = set(re.findall(
            r'\[node name="([^"]+)" type="\w*Light3D"', tscn))
        check(set(off) <= lights,
              f"every night_lights_off name is a light in the scene "
              f"({sorted(set(off) - lights)} are not)")
        # The day exposure has to be the one the calibration was verified at.
        # If someone nudges the .tscn without re-measuring, the recorded
        # derivation stops describing the file and this says so.
        cal = EXTERIOR_CALIBRATION["day"]
        pred = cal["verified_p95"] / cal["reference_value"]
        check(abs(pred - cal["verified_multiple"]) < 0.01,
              f"the recorded day calibration is self-consistent "
              f"({pred:.3f} vs {cal['verified_multiple']})")
        # ...and that it describes THIS FILE. Self-consistency is a property of
        # the dict; this is the one that fails when the scene moves under it.
        scene_exp = scene_env_exposure(
            os.path.join(ROOT, "godot/scenes/exterior.tscn"), "Env")
        check(abs(scene_exp - cal["exposure"]) < 1e-6,
              f"exterior.tscn is at the exposure the day calibration was "
              f"verified at ({scene_exp} vs {cal['exposure']})")
        # The shadow study's own internal consistency, and that it still
        # describes a monotone effect. If someone edits a number to argue a
        # point, p5 stops falling with coverage and this says so.
        st = SHADOW_COVERAGE_STUDY
        ks = sorted(st["p5"])
        check(all(st["p5"][a] > st["p5"][b] for a, b in zip(ks, ks[1:])),
              f"more shadow coverage always darkens p5: {[st['p5'][k] for k in ks]}")
        check(all(st["crushed"][a] < st["crushed"][b] for a, b in zip(ks, ks[1:])),
              f"...and always crushes more: {[st['crushed'][k] for k in ks]}")
        check(st["p5"][max(ks)] < st["p5"][min(ks)] / 2.0,
              f"the study spans a real range, not noise "
              f"({st['p5'][min(ks)]} -> {st['p5'][max(ks)]})")
        check("night" not in EXTERIOR_CALIBRATION["night"].get("reference", ""),
              "the night entry claims no reference frame, because it has none")

    # The frames. Missing is a FAILURE, not a skip: the whole point is that a
    # claim about the exterior cites an engine frame, and a gate that quietly
    # passes when the frame is absent is how the engine path rotted between
    # sessions 2j and 3k.
    frames = {k: os.path.join(ROOT, v) for k, v in GATE_FRAMES.items()}
    if all(os.path.exists(p) for p in frames.values()):
        good, msg = gate_exterior_day(frames["day_calibration"])
        check(good, f"day exposure gate: {msg}")
        good, lines = gate_exterior_night(frames["day_arrival"],
                                          frames["night_arrival"])
        check(good, "night side gates:\n" + "\n".join(lines))
    else:
        check(False, "committed exterior frames are missing: "
                     + ", ".join(k for k, p in frames.items()
                                 if not os.path.exists(p)))

    print(f"{ok}/{ok + fail} passed")
    return 0 if fail == 0 else 1


# ---------------------------------------------------------------------------
# THE DRUM'S CALIBRATED FRAMINGS
# ---------------------------------------------------------------------------
# WHAT A DRUM FRAME ACTUALLY SHOWS, measured part by part, per framing.
#
# `drum_parts` is the list of what the shot BUILDS. This is the list of what a
# named framing SHOWS, and they are not the same -- which is the whole finding.
# Layer 4 counts a location when it has been seen in a frame measured against
# its reference, so a predicate built on the first list credits geometry nobody
# has looked at. That is how `garden` came to be counted, and measuring it
# properly caught `tram` doing the same thing.
#
# THIS USED TO BE ONE TABLE FOR ONE FRAMING, and that was the second half of
# the same mistake. `drum_visible_parts` answered "what does THE drum frame
# show" as though the drum had one, so two locations that the wide shot does
# not reach were reported as unlit for ever -- not because they cannot be seen
# but because nobody had pointed a camera at them. The drum is 2.6 km long and
# 556 m across; one camera does not see it. A framing per subject, each with
# its own reference and its own measured exposure, is the honest shape.
#
# METHOD, and it is now runnable rather than described: render the framing,
# re-render it with `--omit PART`, and count pixels that move by more than
# 8/255. At 480x270 unless a framing says otherwise. `omit_parts` refuses an
# unknown name so a typo cannot report 0.00%.
#
# TWO STATISTICS, and the second one was added because the first can be
# fooled. `contribution` is the fraction of the frame that MOVES; a part with
# no pixels in frame can still move several percent of it by changing what the
# two shadow-casting omnis are occluded by, and by tipping distant
# sub-pixel geometry over the threshold. `largest_region` is the biggest
# 4-connected component of the same mask: a solid object in frame is one blob,
# a shadow spatter is thousands. The tram framing is the case that shows the
# gap -- see its entry.
#
# THE THRESHOLD IS 0.5% AND IT IS A JUDGEMENT, stated so it can be argued
# with. Below it the geometry is a handful of pixels at the far end of a 2.6 km
# drum -- `trams` in the wide framing is 13 pixels at this resolution -- and a
# frame's exposure says nothing about a fitting that small.
#
# `largest_region` LOST DISCRIMINATING POWER IN SESSION 3u AND THAT IS RECORDED
# RATHER THAN QUIETLY LIVED WITH. It exists to separate "a solid object in
# frame" from "a spatter of shadow changes", and with 24 lamps casting instead
# of 2, a part's shadow is now a large CONNECTED region rather than a spatter.
# `guideways` in the wide framing went from 34.60% moved / 34.52% largest to
# 79.50% / 65.91% -- the guideway itself did not grow, its shadow now falls
# across the drum floor and the floor is one blob. So the two statistics no
# longer disagree the way they were built to, and the check they feed
# (DRUM_SUBJECT_MIN_PERCENT: a framing's declared SUBJECT must be a contiguous
# 3% of frame) still does its job only because every declared subject is a solid
# body in shot. It would no longer catch a part that is present purely as
# shadow. Replacing it needs a mask that excludes shadow-only change, which is a
# depth or stencil readback this renderer does not currently expose.
DRUM_FRAME_MIN_PERCENT = 0.5
# A framing's DECLARED SUBJECT is held to more than the visibility threshold:
# it must be a contiguous 3% of the frame. That is the difference between "this
# part is in the picture somewhere" and "this framing exists to show it", and
# it is the check that makes a subject claim falsifiable -- move the camera off
# the subject and the blob collapses while the moved fraction may not.
DRUM_SUBJECT_MIN_PERCENT = 3.0

# WHICH REFERENCE EACH FRAMING IS MEASURED AGAINST, AND WHY IT IS NOT ALWAYS
# THE OBVIOUS ONE. Four authority-1 frames show the inside of this drum, and
# they do not agree on level, because the show lit and graded them differently:
#
#   reference                                   whole-frame median
#   03-sector-blue/Babylon_5_2-22_34b.jpg               0.1515
#   09-garden-core-and-transit/garden.png               0.1406
#   03-sector-blue/Babylon_5_2-22_33a.jpg               0.1166
#   03-sector-blue/Babylon_5_2-22_29a.jpg               0.0559
#
# ONE VOLUME, ONE RIG, ONE EXPOSURE -- so a single render reads at a different
# multiple of each of them, and picking the reference picks the answer. The
# committed wide frame `docs/engine-drum.png`, verified at x1.39 of 34b, reads
# x1.50 of garden.png, x1.81 of 33a and x3.77 of 29a from the same pixels.
#
# So the rule applied here: a drum framing may only be calibrated against a
# reference that AGREES WITH 34b, the frame DRUM_EXPOSURE itself was set on.
# garden.png does (0.1406 against 0.1515, 8% apart on the same render, which is
# inside the +/-25% the gate allows). 33a and 29a do not, and using either
# would demand a global re-exposure that breaks the frame it was measured on.
#
# 29a IS NOT A DARKER GARDEN, IT IS A DIFFERENT PICTURE, and this is worth
# writing down because the frame it produced -- `docs/engine-drum-terrace.png`
# at x3.49 of 29a -- was read as the garden being two and a half stops hot.
# Measured by region, 29a's own lit paving sits at median 0.1515, which is 34b's
# whole-frame median to four decimals. What drags its whole-frame median to
# 0.0559 is CONTENT: 60.1% of that frame is below linear Y 0.05 -- clipped hedge
# at 0.0296 (78% crushed), timber retaining walls at 0.0263, broadleaf canopy at
# 0.0569 -- and `garden.py` builds none of those things. No exposure and no
# shadow scheme puts foliage in a frame. See INV-044.
DRUM_CALIBRATION = {
    # THE WIDE SHOT. The frame DRUM_EXPOSURE was derived on in session 3q, and
    # the anchor the other two are consistent with.
    "wide": {
        "reference": "reference/03-sector-blue/Babylon_5_2-22_34b.jpg",
        "reference_median": 0.1515,
        "frame": "docs/engine-drum.png",
        "shot": "--shot drum --stand 20,4700 --look 20,6300 --res 640x360",
        "subject": "ground",
        "verified_median": 0.2626,
        "verified_multiple": 1.733,
        # 3x4 grid of cell medians -- what makes this the RIGHT
        # picture and not merely a correctly exposed one. See
        # frame_signature for how to regenerate it.
        "signature": [0.273, 0.278, 0.262, 0.228,
                      0.296, 0.245, 0.323, 0.297,
                      0.106, 0.117, 0.271, 0.274],
        # WHERE THE COMMITTED FRAME SITS ON THE WHOLE DISTRIBUTION, not just on
        # the median. Recorded, not tuned to: no exposure in this file was
        # changed to produce these. See the block above DRUM_DISTRIBUTION_DEBT.
        "distribution": {"p5": 2.92, "p95": 0.68, "p5/p95": 4.31,
                         "crushed": 0.02, "verdict": "FAIL"},
        "exposure": 3.807,
        "contribution_res": "480x270",
        "contribution": {
            "ground": 89.87, "guideways": 79.50, "endcap_fore": 5.52,
            "endcap_aft": 0.00, "spokes": 1.92, "core": 2.43, "trams": 0.01,
            "townscape": 0.00,
        },
        "largest_region": {
            "ground": 82.51, "guideways": 65.91, "endcap_fore": 5.52,
            "endcap_aft": 0.00, "spokes": 1.90, "core": 1.32, "trams": 0.01,
            "townscape": 0.00,
        },
    },
    # THE GARDEN. Composition matched to `garden.png` -- the authority-1 frame
    # `garden.townscape()` was built from and names in its own docstring -- so
    # the two frames hold the same subject: the civic landmark and its setting
    # at mid distance, the settlement around it, and the drum's far side
    # arching overhead. The camera is 8.0 m above the terrace, 56 m out along
    # the axis from the landmark, looking back at it. See INV-044 for the
    # derivation of the distance and for what does NOT match (our tower is 16 m
    # against the reference's 25-30 m, which is a layer-2 debt this framing
    # surfaced and does not fix).
    "garden": {
        "reference": "reference/09-garden-core-and-transit/garden.png",
        "reference_median": 0.1406,
        "frame": "docs/engine-drum-garden.png",
        "shot": ("--shot drum --eye \" -90.144,246.253,4956.0\" "
                 "--target \" -95.185,243.275,4900.0\" --fov 45 --res 960x540"),
        "subject": "townscape",
        "verified_median": 0.2107,
        "verified_multiple": 1.499,
        # 3x4 grid of cell medians -- what makes this the RIGHT
        # picture and not merely a correctly exposed one. See
        # frame_signature for how to regenerate it.
        "signature": [0.288, 0.222, 0.274, 0.022,
                      0.102, 0.227, 0.112, 0.237,
                      0.102, 0.231, 0.271, 0.179],
        "distribution": {"p5": 0.89, "p95": 0.89, "p5/p95": 1.00,
                         "crushed": 0.84, "verdict": "PASS"},
        "exposure": 3.807,
        "contribution_res": "480x270",
        "contribution": {
            "ground": 59.40, "guideways": 54.61, "endcap_fore": 0.00,
            "endcap_aft": 11.85, "spokes": 1.05, "core": 1.81,
            "trams": 6.16, "townscape": 33.20,
        },
        "largest_region": {
            "ground": 40.74, "guideways": 51.82, "endcap_fore": 0.00,
            "endcap_aft": 5.32, "spokes": 0.68, "core": 1.79, "trams": 5.10,
            "townscape": 32.14,
        },
    },
    # THE TRAM. `trams` is 0.01% of the wide frame -- thirteen pixels -- so the
    # wide shot says nothing about it, and that is the whole reason this entry
    # exists. Here the camera stands on the drum floor at 96 degrees and looks
    # up and across at the car on the 120-degree guideway at z 4916.5: the car
    # is broadside at 120 m, the Warren truss and its light run are above it,
    # and the drum's far side is behind. That is `Babylon_5_2-22_33a.jpg`'s
    # relationship -- camera below the truss, seeing its lit underside, car
    # slung beneath it, far surface beyond -- which is why 33a is cited as the
    # framing's source even though 34b is what it is MEASURED against. 33a
    # cannot be the measurement reference: it puts the already-calibrated wide
    # frame at x1.81. See INV-045.
    "tram": {
        "reference": "reference/03-sector-blue/Babylon_5_2-22_34b.jpg",
        "reference_median": 0.1515,
        "framing_source": "reference/03-sector-blue/Babylon_5_2-22_33a.jpg",
        "frame": "docs/engine-drum-tram.png",
        "shot": ("--shot drum --stand 96,4875 "
                 "--target \" -121.5,210.444,4916.5\" --fov 45 --res 960x540"),
        "subject": "trams",
        "verified_median": 0.1608,
        "verified_multiple": 1.061,
        # 3x4 grid of cell medians -- what makes this the RIGHT
        # picture and not merely a correctly exposed one. See
        # frame_signature for how to regenerate it.
        "signature": [0.047, 0.147, 0.183, 0.229,
                      0.187, 0.156, 0.149, 0.111,
                      0.154, 0.015, 0.003, 0.085],
        # The ONLY drum framing whose black population matches its reference
        # (x1.06). Its debt is entirely in p5: shadows at 1.48x the show's.
        "distribution": {"p5": 0.40, "p95": 0.88, "p5/p95": 0.45,
                         "crushed": 6.66, "verdict": "FAIL"},
        "exposure": 3.807,
        "contribution_res": "480x270",
        "contribution": {
            "ground": 70.19, "guideways": 77.59, "endcap_fore": 0.00,
            "endcap_aft": 0.00, "spokes": 0.00, "core": 11.19,
            "trams": 6.49, "townscape": 27.19,
        },
        "largest_region": {
            "ground": 33.34, "guideways": 75.34, "endcap_fore": 0.00,
            "endcap_aft": 0.00, "spokes": 0.00, "core": 10.94,
            "trams": 5.78, "townscape": 27.03,
        },
    },
}


# WHAT SHADOW COVERAGE BUYS, measured on the garden framing against
# `reference/09-garden-core-and-transit/garden.png`. Recorded because the
# conclusion is not the one anyone would guess and the numbers are expensive to
# reproduce (47 s a frame at 960x540 on lavapipe).
#
#   shadow lights   p5      crushed   render
#         2       0.0560     0.20%      11 s
#         6       0.0470     1.23%      14 s
#        20       0.0337     1.84%      31 s
#        32       0.0207     3.86%      47 s     <- reference is 0.0180 / 5.63%
#
# AMBIENT IS NEARLY INERT and that was the surprise: 0.15 -> 0.02 moves p5 only
# 0.0458 -> 0.0427. The hypothesis going in was that ambient sets the shadow
# floor; measurement refuted it. Shadow COUNT is the lever.
#
# AT 32 LIGHTS THE FRAME PASSES ALL SIX DISTRIBUTION CHECKS -- p5 x1.16 inside
# the x1.29 band, p95, the ratio, crushed as ratio and envelope, clipped -- and
# it is the first frame in this project to do so besides the one that already
# did. Its MEDIAN is then x0.49 of the reference instead of x1.40.
#
# AND THE LEVEL CANNOT BE RECOVERED WITH LIGHT ENERGY. Gain 2.0/3.0/4.0 give
# medians x0.98/x1.42/x1.82 and p5 0.0298/0.0467/0.0653: the same lights light
# the shadows, so every stop that fixes the level undoes the shape. Getting both
# needs light that is brighter where it lands and no brighter where it does not
# -- tighter falloff, more directional fittings -- not a global gain. That is a
# rig change, not a number, and it is the real content of layer 4b.
#
# ==========================================================================
# SESSION 3u: THAT LAST PARAGRAPH IS WRONG, AND SO IS THE ONE ABOVE IT.
# ==========================================================================
# Both are kept verbatim because the record of a refuted reading is worth more
# than a tidy file, and because the two errors are different kinds.
#
# 1. "AT 32 LIGHTS THE FRAME PASSES ALL SIX CHECKS" is CONFOUNDED BY LEVEL. The
#    distribution verdict is not level-invariant, `at_offset` notwithstanding,
#    because FLOOR censors from below and our frames have no sub-floor
#    population to lose while the show's frames do. Demonstrated on ONE
#    UNCHANGED IMAGE -- `docs/engine-drum-garden.png` as it was then -- by
#    applying a post-hoc gain and re-measuring, so the shape is fixed by
#    construction and only the exposure moves:
#
#        gain   0.25   0.50   1.00   1.40   2.00   3.00
#        x p5   1.26   1.90   3.21   4.27   5.84   7.85
#
#    A statistic that spans x1.26 to x7.85 on a picture that did not change is
#    measuring exposure at least as much as shape. Applied to the 32-shadow
#    frame: it passes at gains 0.50-1.00, which is where its median sits at
#    x0.26-x0.49 of its reference, and at the gain that puts the median in the
#    level band it reads p5 x2.02 and FAILS. The 32-light pass was bought by
#    being a stop and a half under, not by shadow coverage.
#
#    Shadow coverage is still the lever -- it is worth x2.92 -> x2.00 on p5 AT
#    MATCHED LEVEL, which is the honest way to state it -- but that is a third
#    of the distance, not the whole of it.
#
# 2. "TIGHTER FALLOFF, MORE DIRECTIONAL FITTINGS" IS THE WRONG DIRECTION, and
#    the reference frame says so before any render does. Measured in horizontal
#    thirds, every frame normalised to a matched whole-frame median:
#
#      band              reference median   ours (2 shadow)   what it holds
#      far side overhead      0.2321            0.2077        drum arching over
#      middle                 0.1758            0.1847        the landmark
#      near foreground        0.1030            0.1685        pool, planting
#
#    The show's frame gets DARKER toward the camera. The lamps are 41.7 m above
#    the floor the camera stands on and 400-500 m from the far side, so
#    concentrating the light where it lands brightens the foreground and dims
#    the overhead -- it inverts the gradient the reference has. Rendered, at
#    matched median: LIGHT_DIRECTIONALITY below.
#
# THE DEFAULT WAS 2 AND IS NOW DRUM_SHADOW_LIGHTS = 24, with all three
# DRUM_CALIBRATION framings re-derived at it. The paragraph this replaces was
# right that raising it silently would invalidate them.
SHADOW_COVERAGE_STUDY = {
    "reference": "reference/09-garden-core-and-transit/garden.png",
    "reference_p5": 0.0180, "reference_crushed": 0.0563,
    "framing": "--shot drum --eye -90.144,246.253,4956 --look 112,4900 --fov 45",
    "p5": {2: 0.0560, 6: 0.0470, 20: 0.0337, 32: 0.0207},
    "crushed": {2: 0.0020, 6: 0.0123, 20: 0.0184, 32: 0.0386},
    "seconds_960x540_lavapipe": {2: 11, 6: 14, 20: 31, 32: 47},
    "ambient_sweep_p5": {0.15: 0.0458, 0.08: 0.0442, 0.04: 0.0431,
                         0.02: 0.0427},
    "gain_sweep": {2.0: (0.1371, 0.0298), 3.0: (0.1999, 0.0467),
                   4.0: (0.2553, 0.0653)},
    # Session 3u. Same image, post-hoc gain, x p5 against the reference at our
    # offset. See the paragraph above: the verdict moves with exposure alone.
    "level_confound_xp5": {0.25: 1.26, 0.50: 1.90, 1.00: 3.21, 1.40: 4.27,
                           2.00: 5.84, 3.00: 7.85},
}


# WHY DIRECTIONAL LIGHT IS NOT THE ANSWER, RENDERED. Every row is the garden
# framing, and every row is put on a MATCHED WHOLE-FRAME MEDIAN of x1.40 of
# `garden.png` before p5 is read, because comparing p5 at different levels is
# the confound SHADOW_COVERAGE_STUDY records above.
#
#   rig                                       x p5   what the frame does
#   omni, decay 0.7, range 1100 (the rig)     2.92   the baseline
#   omni, decay 2.0, energy x2600             3.55   WORSE. Inverse-square dims
#                                                    the overhead far side,
#                                                    which the reference has
#                                                    BRIGHT, and leaves the
#                                                    foreground, which the
#                                                    reference has dark
#   omni, decay 0.7, range 300                2.64   10% better and 21% of the
#                                                    frame clips once it is
#                                                    normalised back to level
#   spot, 85 deg cone, aimed at the floor     2.85   no better than the omni,
#                                                    same 21% clipping
#   spot, 60 deg cone                          --    unusable: the townscape is
#                                                    unlit and the drum's far
#                                                    side is black
#
# THE GEOMETRY FORBIDS IT ANYWAY, and this is the argument that does not need a
# render. There are three trusses, 120 degrees apart, and their lamps sit 41.7 m
# above a floor of radius 278.3 m. To reach the floor midway between two trusses
# a lamp must throw 291 m sideways from 41.7 m up -- a half-angle of 81.9
# degrees, which is not a cone, it is a hemisphere with the top cut off. Any
# genuinely directional fitting leaves the drum floor in three lit stripes with
# three black gaps, and `Babylon_5_2-22_34b.jpg` shows the floor evenly lit from
# end to end with the truss a black silhouette against it.
#
# WHAT THE FOREGROUND'S DARKNESS ACTUALLY IS, measured on the reference: 30.9%
# of `garden.png`'s bottom third is below linear Y 0.04, against 0.4% of ours.
# Of those pixels only 2.8% are near-neutral -- 22.1% are green-dominant and
# 20.5% blue/teal-dominant, mean chromaticity r/g/b 0.433/0.293/0.266. A grey
# surface in shadow is neutral; a dark thing is not. 97% of the show's dark
# foreground is FOLIAGE, WATER AND DARK TIMBER, which is content, and INV-044
# already reached the same conclusion from `29a` two sessions earlier: "no
# exposure and no shadow scheme puts foliage in a frame". Ours is 74.7%
# near-neutral, because a light rig is all we had.
LIGHT_DIRECTIONALITY = {
    "framing": "DRUM_CALIBRATION['garden']",
    "method": "p5 read at the gain that puts the whole-frame median at x1.40",
    "xp5_at_matched_median": {
        "omni_decay_0.7_range_1100": 2.92,
        "omni_decay_2.0": 3.55,
        "omni_decay_0.7_range_300": 2.64,
        "spot_85deg": 2.85,
    },
    # Fraction of the bottom third below linear Y 0.04, and how much of that is
    # chromatic rather than neutral.
    "foreground_dark_fraction": {"reference": 0.309, "ours": 0.004},
    "foreground_dark_neutral_fraction": {"reference": 0.028, "ours": 0.747},
    # Half-angle a guideway fitting would need to reach mid-way between trusses.
    "cone_halfangle_needed_deg": 81.9,
}


def drum_visible_parts():
    """Part names SOME calibrated drum framing demonstrably shows.

    The union, not the intersection, and not one framing's table. A location is
    at layer 4 once it has appeared in one frame measured against its
    reference; requiring it in every framing would mean no location could be
    lit until every camera in the project pointed at it.
    """
    seen = set()
    for cal in DRUM_CALIBRATION.values():
        seen |= {k for k, v in cal["contribution"].items()
                 if v >= DRUM_FRAME_MIN_PERCENT}
    return seen


def frame_signature(png, rows=3, cols=4):
    """Median linear luminance of each cell of a 3x4 grid over one frame.

    WHAT IT IS FOR: telling one FRAMING from another, which no level statistic
    can do. It exists because the frame gate below was demonstrated NOT
    failing: point the tram framing's `frame` key at `engine-drum-terrace.png`
    -- a 20 m close-up of a block facade, a completely different picture -- and
    every check passed, because two frames of one volume at one exposure have
    similar medians by construction. That is the "assertion that cannot fail"
    this project most wants to avoid, found the only way it can be found, which
    is by breaking the thing the gate guards and watching.

    Deliberately coarse, and deliberately medians. Twelve cell medians are
    insensitive to a few thousand pixels of geometry changing and very
    sensitive to the camera moving, which is the discrimination wanted. A hash
    would be exact and useless -- it fails on any re-render at all.

    Regenerate a framing's recorded signature with:

        python3 -c "import sys; sys.path.insert(0,'tools'); \\
            import export_scene as X; \\
            print([round(v,3) for v in X.frame_signature('docs/FRAME.png')])"
    """
    import numpy as np                                        # noqa: PLC0415
    from PIL import Image                                     # noqa: PLC0415
    mf = _measure_frame()
    a = np.asarray(Image.open(png).convert("RGB"), dtype=np.float64) / 255.0
    y = mf.srgb_to_linear(a) @ np.array(mf.LUMA)
    h, w = y.shape
    return [float(np.median(y[int(r * h / rows):int((r + 1) * h / rows),
                              int(c * w / cols):int((c + 1) * w / cols)]))
            for r in range(rows) for c in range(cols)]


# HOW FAR APART TWO SIGNATURES HAVE TO BE TO BE TWO FRAMINGS. Measured over the
# six distinct drum frames committed in docs/, as mean absolute difference of
# the twelve cells: the CLOSEST pair is the wide shot against
# `engine-drum-landscape.png` at 0.053, which really are two similar framings of
# the same subject, and every other pair is 0.068-0.144. The threshold is 0.030,
# below the closest genuine pair by 1.8x, so a re-render that moved geometry has
# room and a different camera does not. It is not an exposure check -- the
# median band is -- and not a pixel test.
DRUM_SIGNATURE_TOL = 0.030


# ---------------------------------------------------------------------------
# THE ENVIRONMENT EVERY DRUM NUMBER ABOVE WAS MEASURED UNDER
# ---------------------------------------------------------------------------
# THE HOLE THIS CLOSES, and it is the hole session 3u fell into. Every recorded
# median, multiple, signature and distribution in DRUM_CALIBRATION is a claim
# about a rendered frame, and a rendered frame is geometry plus lights plus THE
# ENVIRONMENT BLOCK IN drum.tscn. The exposure was guarded -- `cal["exposure"]`
# must equal DRUM_EXPOSURE -- and the environment was not, so a tonemapper, a
# fog density or a glow parameter could move and every number here would go on
# describing a render nobody could reproduce, silently, exactly the way
# `verified_multiple` could before it was checked against its own frame.
#
# It is not hypothetical. `glow_bloom = 0.06` was contributing 44% of the garden
# framing's p5 -- more than the ambient term and more than the fog -- for as long
# as the drum has been rendered, and nothing in this file mentioned glow at all.
#
# WHY THE WHOLE BLOCK AND NOT THE TERMS THAT MATTER. Two of these are measured
# INERT on this framing and are locked anyway:
#
#   ssao_*        radius 2.5 -> 12.0, intensity 1.8 -> 4.0, light_affect
#                 0.2 -> 0.9 changed 0.23% of the frame by more than 8/255.
#   fog_density   halved, 0.00012 -> 0.00006: p5 0.0223 -> 0.0223, unmoved.
#
# Locking only the terms known to matter is how the next inert-looking term gets
# left out, and the whole point is that glow LOOKED inert until it was measured.
# A term that genuinely does nothing costs one line here and no render.
DRUM_ENVIRONMENT = {
    "background_mode": "1",
    "background_color": "Color(0.012, 0.016, 0.024, 1)",
    "ambient_light_source": "2",
    "ambient_light_color": "Color(0.55, 0.56, 0.52, 1)",
    "ambient_light_energy": "0.03",
    "reflected_light_source": "1",
    "tonemap_mode": "4",
    "tonemap_exposure": "1.0",
    "tonemap_white": "8.0",
    "ssao_enabled": "true",
    "ssao_radius": "2.5",
    "ssao_intensity": "1.8",
    "ssao_power": "1.5",
    "ssao_light_affect": "0.2",
    "ssao_detail": "0.6",
    "fog_enabled": "true",
    "fog_mode": "0",
    "fog_light_color": "Color(0.42, 0.45, 0.47, 1)",
    "fog_light_energy": "0.8",
    "fog_density": "0.00012",
    "fog_aerial_perspective": "0.0",
    "fog_sky_affect": "0.0",
    "glow_enabled": "true",
    "glow_levels/1": "1.0",
    "glow_levels/2": "1.0",
    "glow_levels/3": "0.0",
    "glow_levels/4": "0.0",
    "glow_levels/5": "0.0",
    "glow_levels/6": "0.0",
    "glow_levels/7": "0.0",
    "glow_normalized": "true",
    "glow_intensity": "0.7",
    "glow_strength": "1.05",
    "glow_bloom": "0.0",
    "glow_blend_mode": "1",
    "glow_hdr_threshold": "0.95",
}
DRUM_SCENE_TSCN = os.path.join(ROOT, "godot", "scenes", "drum.tscn")


def scene_environment(path=DRUM_SCENE_TSCN, sub_id="Env"):
    """Every `key = value` in one .tscn's Environment sub-resource, as strings.

    STRINGS, NOT FLOATS, and that is the point rather than laziness: the
    comparison this feeds is "is the file the one these frames were rendered
    under", and `0.03` against `0.030000001` is a difference a float compare
    would hide behind a tolerance nobody chose. A .tscn is text and the check is
    a text check.

    Stops at the next `[` header, so the node's own `material_rules` block --
    which `station/materials.py --export` rewrites and which is another agent's
    output -- is outside this and cannot make the drum's frames go stale.
    """
    want = f'[sub_resource type="Environment" id="{sub_id}"]'
    out, inside = {}, False
    with open(path) as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith("["):
                if inside:
                    break
                inside = s.strip() == want
                continue
            if not inside or not s or s.startswith(";"):
                continue
            if "=" not in s:
                continue
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    if not out:
        raise ValueError(f"{path}: no Environment sub-resource {sub_id!r}")
    return out


# EVERY DRUM FRAMING FAILS THE DISTRIBUTION COMPARISON, AND THAT IS RECORDED
# HERE RATHER THAN FIXED, because fixing it means moving exposures and the
# measurement is the point. `tools/measure_frame.py` grew a whole-distribution
# verdict -- p5, p95, p5/p95, crushed and clipped, each against a tolerance
# derived from the show's own frames -- because the median test every exposure
# in this file was set by is a test A FLAT FRAME PASSES. All three drum
# framings pass the median test and all three fail the new one:
#
#   framing   p5     p95    p5/p95  crushed        the debt
#   wide      x1.74  x0.71  x2.44   0.00% vs 2.66%  no blacks at all
#   garden    x3.21  x1.27  x2.53   0.01% vs 2.78%  shadows three stops up
#   tram      x1.48  x1.04  x1.42   2.83% vs 2.66%  shadows only
#
# The bands are x1.22 on p5 and x11.52 on crushed. `wide` and `garden` have
# essentially NO pixels below the measurable floor where their references have
# 2.7%; INV-044 already establishes that part of the garden's shortfall is
# CONTENT -- the reference's clipped hedge and broadleaf canopy are things
# garden.py does not build -- and no exposure puts foliage in a frame. The
# distribution verdict cannot separate "our shadows are too bright" from "our
# scene has nothing dark in it". Both read as blockout.
#
# `--gate-drum` now exits non-zero on this. Nothing in CI runs it (see
# .github/workflows/validate.yml, which runs the self-test and measure_frame's
# self-test only), so this states a debt rather than blocking a build.
#
# ==========================================================================
# SESSION 3u: `garden` IS OUT OF DEBT AND THE FLAG IS NOW A LIST
# ==========================================================================
# A single boolean could only ever say "some of this is broken", which is a
# statement that survives any amount of progress and any amount of regression.
# Naming the framings makes it a ratchet, and the self-test enforces BOTH
# directions:
#
#   * every framing NOT named here must pass the whole-distribution verdict.
#     That is layer 4b's exit criterion, and until this session it was computed
#     and then not counted (`score_distribution` defaulted off) because all
#     three failed it.
#   * every framing named here must actually FAIL it. Without that half the list
#     is a place to hide a framing that has started passing, which is the same
#     defect as a deferral list that can be grown until a number goes green --
#     `station/directory.py` has the identical rule for the same reason.
#
# WHY THE OTHER TWO ARE STILL IN IT, stated so the next session does not have to
# re-derive it:
#
#   wide  p5 x2.59, crushed 0.06% against 2.66%. The framing is 2.6 km of open
#         ground with NO occluder in the picture -- see `docs/engine-drum.png`
#         -- so there is nothing in it for a shadow to be cast by, and 24 shadow
#         casters change it barely at all. Its reference `34b` is dominated by a
#         black truss across the foreground. This is a COMPOSITION mismatch
#         wearing a lighting failure's clothes and no rig setting closes it.
#   tram  p5 x0.44, crushed 19.91% against 2.66%. It fails the OPPOSITE way --
#         too dark, not too bright -- which is worth more than it looks: it is
#         the first frame in this project to overshoot, and it overshoots
#         because the truss and the townscape genuinely occlude it. Its
#         foreground block reads solid black.
DRUM_DISTRIBUTION_DEBT = {"wide", "tram"}


def gate_drum(name, png="", tolerance=0.25, score_distribution=False):
    """One calibrated drum framing, measured against its reference frame.

    Returns (ok, message). The PNG must be the framing's own `shot`; measuring
    any other camera against this reference measures whatever is in it -- see
    tools/measure_frame.py's closing paragraph, which is the same warning.

    `score_distribution` decides whether the whole-distribution verdict counts
    toward `ok`. It is OFF by default and ON for `--gate-drum`; the self-test
    turns it on for every framing NOT in DRUM_DISTRIBUTION_DEBT, which since
    session 3u is `garden`. The default stays off because a caller measuring an
    arbitrary PNG is usually asking "is this the right picture at the right
    level", and because the debt list, not this flag, is where a framing's
    exemption is supposed to be visible. The verdict is in the message either
    way, the recorded `distribution` block is checked for staleness either way,
    and `--gate-drum` exits non-zero. What is NOT allowed is for the failure to
    go unstated.
    """
    mf = _measure_frame()
    cal = DRUM_CALIBRATION[name]
    png = png or os.path.join(ROOT, cal["frame"])
    ref = os.path.join(ROOT, cal["reference"])
    if not os.path.exists(png):
        return False, f"{name}: committed frame missing: {cal['frame']}"
    if not os.path.exists(ref):
        return False, f"{name}: reference missing: {cal['reference']}"
    r = mf.measure(ref)
    m = mf.measure(png)
    # The reference is measured, not trusted to the recorded number: a
    # re-encoded or replaced reference file silently moves every multiple
    # derived from it, and the recorded value is the claim that catches it.
    if abs(r["median"] - cal["reference_median"]) > 0.0006:
        return False, (f"{name}: {os.path.basename(ref)} now measures "
                       f"{r['median']:.4f}, recorded as "
                       f"{cal['reference_median']:.4f} -- the reference moved, "
                       f"so every multiple derived from it is void")
    x = m["median"] / r["median"] if r["median"] else 0.0
    ok = abs(x - mf.RENDER_OFFSET) <= tolerance * mf.RENDER_OFFSET
    over = m["clipped"] > 0.04
    # AND THE RECORD DESCRIBES THIS FILE. Without this, `verified_multiple`
    # and `verified_median` need only agree with each other -- a pair of
    # numbers can be perfectly self-consistent and describe a render nobody
    # ever made. Loose on purpose at 20%: this is here to catch a record that
    # has come adrift from its frame, not to re-litigate the exposure, which
    # the band above already does. Anything that trips it means the geometry
    # or the rig moved and the frame needs re-rendering, not re-tuning.
    drift = abs(x - cal["verified_multiple"]) > 0.20 * cal["verified_multiple"]
    # ...AND IT IS THE RIGHT PICTURE. See `frame_signature`: everything above
    # is a level test, and a level test cannot tell one camera from another.
    sig = frame_signature(png)
    d = sum(abs(a - b) for a, b in zip(sig, cal["signature"])) / len(sig)
    wrong = d > DRUM_SIGNATURE_TOL
    # ...AND THE WHOLE DISTRIBUTION, not only the level. Everything above is a
    # median test plus a framing test, and a frame can pass both while its
    # shadows sit three stops over the show's -- which is what all three of
    # these do. See DRUM_DISTRIBUTION_DEBT.
    rows, dok = mf.distribution(m, mf.at_offset(ref, mf.RENDER_OFFSET))
    dbad = [f"{lab} x{xx:.2f}" if xx not in (None, float("inf"))
            else f"{lab} {'inf' if xx else 'out'}"
            for lab, _a, _b, xx, good, _n in rows if good is False]
    # AND THE RECORDED DISTRIBUTION DESCRIBES THIS FRAME. Same reason
    # `verified_multiple` is checked: a table of numbers can be internally
    # consistent and describe a render nobody made.
    rec = cal.get("distribution", {})
    got = {lab: xx for lab, _a, _b, xx, _g, _n in rows}
    stale = [k for k, v in rec.items()
             if k in got and v is not None and got[k] is not None
             and got[k] != float("inf")
             and abs(got[k] - v) > 0.20 * max(v, 0.05)]
    if rec.get("verdict") and rec["verdict"] != ("PASS" if dok else "FAIL"):
        stale.append("verdict")
    good = (ok and not over and not drift and not wrong and not stale
            and (dok or not score_distribution))
    return good, (
        f"{name}: median {m['median']:.4f} = x{x:.2f} of "
        f"{os.path.basename(ref)}'s {r['median']:.4f} "
        f"(target x{mf.RENDER_OFFSET:.2f} +/-{tolerance * 100:.0f}%), "
        f"clipped {m['clipped'] * 100:.2f}%, signature {d:.4f}"
        + ("  OVEREXPOSED" if over else "")
        + (f"  RECORD ADRIFT: verified at x{cal['verified_multiple']:.2f}, "
           f"this frame is x{x:.2f} -- re-render it" if drift else "")
        + (f"  NOT THIS FRAMING: {os.path.basename(png)} is {d:.4f} from the "
           f"recorded signature (tol {DRUM_SIGNATURE_TOL}) -- either the "
           f"camera moved or the wrong file is committed" if wrong else "")
        # THE DIRECTION, not a fixed sentence. This line used to end "-- this
        # frame is flat against its reference", which was true of all three
        # framings when it was written and became a false statement about the
        # tram the moment the rig gained shadows: the tram fails by crushing
        # 18.4% of itself against the show's 2.7%, which is the opposite defect.
        # A gate that names the wrong cause sends the next session to the wrong
        # knob.
        + (f"\n       DISTRIBUTION FAIL: {', '.join(dbad)} -- "
           + ("shadows brighter than the show's"
              if m["dark_p5"] > mf.at_offset(ref)["dark_p5"] else
              "shadows darker than the show's")
           + f" (p5 {m['dark_p5']:.4f} against "
             f"{mf.at_offset(ref)['dark_p5']:.4f}), crushed "
             f"{m['crushed'] * 100:.2f}%"
           if not dok else "\n       distribution OK")
        + (f"\n       RECORDED DISTRIBUTION STALE: {', '.join(stale)} -- "
           f"DRUM_CALIBRATION[{name!r}]['distribution'] no longer describes "
           f"this frame" if stale else ""))


def run_drum_gates(score_distribution=True):
    """Every calibrated drum framing over its committed frame."""
    good = True
    for name in sorted(DRUM_CALIBRATION):
        ok, msg = gate_drum(name, score_distribution=score_distribution)
        print(f"drum {'OK  ' if ok else 'FAIL'} {msg}")
        good = good and ok
    return good


def drum_groups(schema, profile, sector, eye=None):
    """Every group name the drum shot emits.

    Built by actually running `drum_parts`, not by a parallel list. It costs a
    full geometry build (tens of seconds) and that is the correct trade: an
    enumeration that can disagree with the thing it enumerates asserts nothing.
    The ground's own vocabulary is added from `_KIND_GROUP` as well, because a
    single eye position resolves some patches to a LOD that happens not to
    contain, say, a water surface, and a material rule must exist for every
    kind the ground can ever produce rather than for the ones this eye saw.
    """
    if eye is None:
        eye = dg.stand_on_ground(schema, profile, sector, 205.0,
                                 (dg.Z0 + dg.Z1) / 2)[0]
    names = set(dg._KIND_GROUP.values())
    for _name, _v, _t, groups in drum_parts(schema, profile, sector, eye,
                                            trams=1):
        names |= set(groups)
    return sorted(names)


def _pair(s):
    a, b = s.split(",")
    return float(a), float(b)


def _triple(s):
    a, b, c = s.split(",")
    return float(a), float(b), float(c)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shot", choices=sorted(SHOTS))
    ap.add_argument("--out", default="", help="PNG the renderer should write")
    ap.add_argument("--eye", type=_triple)
    ap.add_argument("--target", type=_triple)
    ap.add_argument("--stand", type=_pair, metavar="DEG,Z",
                    help="drum: derive the eye from the heightfield")
    ap.add_argument("--look", type=_pair, metavar="DEG,Z",
                    help="drum: derive the aim point from the heightfield")
    # DEFAULT None SO THAT "NOBODY SAID" AND "THE USER ASKED FOR THE DEFAULT"
    # ARE DIFFERENT STATES. Every shot but the deck resolves these to the
    # literals they have always had; the deck resolves them to the SHIPPED
    # player camera, and with a plain float default `--fov 46` on a deck shot
    # would have silently given the player's 70 instead.
    ap.add_argument("--eye-height", type=float, default=None,
                    help="standing eye height (default 1.7; the deck shot "
                         "takes player.gd's)")
    ap.add_argument("--orbit", type=_triple, default=(9200.0, 18.0, 214.0),
                    metavar="DIST,ELEV,AZ")
    ap.add_argument("--target-z", type=float, default=4023.0,
                    help="exterior: station midpoint")
    ap.add_argument("--lod", default="auto",
                    help="hull LOD: auto (by distance), or lod0..lod3 to force")
    ap.add_argument("--fov", type=float, default=None,
                    help="vertical field of view (default 46; the deck shot "
                         "takes player.gd's)")
    ap.add_argument("--sun-az", type=float, default=168.0)
    ap.add_argument("--sun-elev", type=float, default=34.0)
    ap.add_argument("--lighting", choices=("day", "night"), default="day",
                    help="exterior: which of exterior.tscn's two lighting "
                         "conditions. `night` puts the sun behind the station "
                         "as seen from THIS eye and mounts the night "
                         "environment -- see EXTERIOR_CALIBRATION")
    ap.add_argument("--night-sun-phase", type=float,
                    default=NIGHT_SUN_PHASE_DEG,
                    help="exterior: degrees the night sun sits off "
                         "dead-behind-the-station. 0 eclipses it entirely and "
                         "the limb goes hard black")
    ap.add_argument("--gate-exterior", nargs="*", metavar="PNG",
                    help="measure committed exterior frames against "
                         "EXTERIOR_CALIBRATION and exit non-zero if they are "
                         "out. Defaults to the three docs/ frames")
    ap.add_argument("--gate-drum", action="store_true",
                    help="measure the committed drum frames against "
                         "DRUM_CALIBRATION and exit non-zero if they are out")
    ap.add_argument("--gate-frames", action="store_true",
                    help="re-measure every exposure in EXPOSURE_FRAMES with "
                         "tools/measure_frame.py's whole-distribution "
                         "comparison, and report which exposures have no "
                         "committed frame to verify against at all")
    ap.add_argument("--lights-per-run", type=int, default=10)
    ap.add_argument("--light-range", type=float, default=1100.0)
    # THE DIRECTIONALITY KNOBS, and they exist so that LIGHT_DIRECTIONALITY's
    # table can be reproduced by running something rather than by hand-editing
    # `build_drum` -- the same reason `--omit` exists. Defaults are None/omni,
    # so nothing changes unless a measurement asks for it.
    ap.add_argument("--light-attenuation", type=float, default=None,
                    metavar="EXP",
                    help="drum: override LAMP_ATTENUATION. Godot's omni "
                         "falloff is pow(1 - d/range, EXP), so a larger "
                         "exponent concentrates the light near the fitting")
    ap.add_argument("--light-kind", choices=("omni", "spot"), default="omni",
                    help="drum: emit the guideway light runs as spots aimed "
                         "radially outward at the floor beneath them, instead "
                         "of as point sources")
    ap.add_argument("--light-cone", type=float, default=60.0, metavar="DEG",
                    help="drum: spot half-angle when --light-kind spot")
    # DEFAULT None, AND EACH SHOT PICKS ITS OWN. One argparse default for two
    # shots meant raising the drum's ration to 24 would silently have put 24
    # shadow cube maps in every 12 m interior room as well, re-costing and
    # re-lighting eleven calibrated interiors as a side effect of a drum change.
    ap.add_argument("--shadow-lights", type=int, default=None,
                    help=f"how many lamps cast shadows (drum default "
                         f"{DRUM_SHADOW_LIGHTS}, interior "
                         f"{INTERIOR_SHADOW_LIGHTS})")
    ap.add_argument("--trams", type=int, default=2)
    ap.add_argument("--omit", default="", metavar="PART[,PART...]",
                    help="drum: leave these parts out of the shot. This is "
                         "how DRUM_CALIBRATION's per-part contribution table "
                         "is measured -- render whole, render again with one "
                         "part omitted, count the pixels that moved. An "
                         "unknown name is refused, not ignored")
    ap.add_argument("--room", default="",
                    help="interior shot: a directory place key, or `corridor` "
                         "/ `junction` for the kit itself")
    # --- the deck shot -----------------------------------------------------
    # A PLACE KEY AND AN OFFSET, not world coordinates. See `deck_camera`.
    ap.add_argument("--deck", default=DEFAULT_DECK, metavar="SECTOR/RING/DECK",
                    help=f"deck shot: which deck to assemble "
                         f"(default {DEFAULT_DECK})")
    ap.add_argument("--deck-z", type=float, default=None, metavar="Z",
                    help="deck shot: which z cluster on that deck. Default is "
                         "the busiest, which is what deck.py and walkable.py "
                         "both build")
    ap.add_argument("--max-rooms", type=int, default=None,
                    help="deck shot: assemble only the first N rooms of the "
                         "cluster, which shortens the arc. A cost lever for "
                         "iteration, not a look decision")
    ap.add_argument("--at", default="", metavar="KEY",
                    help="deck shot: stand at this place's angle on the "
                         "corridor. Default is the deck's own spawn place")
    ap.add_argument("--at-offset", type=_pair, default=None, metavar="ARC,Z",
                    help="deck shot: metres from --at along the corridor arc "
                         "and along the station axis")
    ap.add_argument("--face", default="", metavar="KEY",
                    help="deck shot: look at this place -- its door, from the "
                         "corridor")
    ap.add_argument("--face-offset", type=_pair, default=None,
                    metavar="ARC,Z",
                    help=f"deck shot: with no --face, look this far along the "
                         f"arc and the axis (default {DECK_FACE_M[0]},"
                         f"{DECK_FACE_M[1]})")
    ap.add_argument("--fixture-energy", type=float, default=3.0,
                    help="interior shot: energy per tagged light fitting")
    ap.add_argument("--ambient", type=float, default=None,
                    help="interior shot: override the room's ambient energy. "
                         "Exists so the anchor in AMBIENT_CALIBRATED_ENERGY "
                         "can be found by rendering and measuring rather than "
                         "by taste -- see tools/measure_frame.py")
    ap.add_argument("--soft-fill", type=float, default=SOFT_FILL_ENERGY,
                    help=f"energy of the corridor's off-camera key (default "
                         f"{SOFT_FILL_ENERGY}). ZERO IS THE NEGATIVE CONTROL "
                         f"and it also restores the flat ambient, so "
                         f"`--soft-fill 0` renders the pre-fill corridor "
                         f"exactly -- see SOFT_FILL")
    a = ap.parse_args()

    if a.gate_exterior is not None:
        sys.exit(0 if run_exterior_gates(*a.gate_exterior) else 1)

    if a.gate_drum:
        sys.exit(0 if run_drum_gates() else 1)

    if a.gate_frames:
        _p, _f, _s = gate_frames()
        # Non-zero only when a recorded FILE is missing, which is a broken
        # record; the distribution failures are recorded debt, not a build
        # break, and EXPOSURE_DISTRIBUTION_DEBT says so.
        sys.exit(0)

    if not a.shot:
        sys.exit(_selftest())

    sc = build(a)
    print(json.dumps({"shot": sc["shot"], "scene": sc["scene"],
                      "glb": [os.path.relpath(p, ROOT) for p in sc["glb"]],
                      "triangles": sc["triangles"],
                      "lights": len(sc["lights"]),
                      "scene_json": os.path.relpath(sc["scene_json"], ROOT)},
                     indent=1))


if __name__ == "__main__":
    main()
