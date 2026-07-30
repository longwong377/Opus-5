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
    python3 tools/export_scene.py                      # runs the self-test
    python3 tools/export_scene.py --gate-exterior      # measures the frames

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
DRUM_EXPOSURE = 1.41

# A light 500 m across the drum should not be 20x dimmer than one 40 m
# overhead: the drum reads near-uniformly lit in `34b`, which is what a line
# source 2.6 km long inside a reflective cavity actually does. Godot's omni
# falloff is pow(1 - d/range, attenuation), so an exponent below 1 flattens it.
LAMP_ATTENUATION = 0.7


def light_energy(per_run):
    """Energy for one omni, given how many sample the run. See RUN_ENERGY."""
    return RUN_ENERGY * DRUM_EXPOSURE / max(1, per_run)


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
                   "fov": args.fov, "near": 1.0, "far": 200000.0},
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
    return parts


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
                                     eye_h=args.eye_height)
    elif args.eye:
        eye = tuple(args.eye)
        a = math.atan2(eye[1], eye[0])
        up = (-math.cos(a), -math.sin(a), 0.0)
    else:
        raise SystemExit("--shot drum needs --stand DEG,Z or --eye X,Y,Z")

    if args.look:
        ang, z = args.look
        aim, _ = dg.stand_on_ground(schema, profile, sector, ang, z,
                                    eye_h=args.eye_height)
    elif args.target:
        aim = tuple(args.target)
    else:
        raise SystemExit("--shot drum needs --look DEG,Z or --target X,Y,Z")

    parts = drum_parts(schema, profile, sector, eye, trams=args.trams)

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
    for run in runs:
        for p in run:
            lights.append({"pos": list(p), "energy": per_light,
                           "colour": list(LAMP_COLOUR),
                           "range": args.light_range,
                           "attenuation": LAMP_ATTENUATION})
    # Shadow casting is rationed, not free: an omni shadow is a cube map, so
    # each one re-renders the scene six times, and this renderer is a CPU. The
    # nearest few carry the shadows because they are the ones whose occluders
    # are on screen at a size where a shadow reads.
    order = sorted(range(len(lights)),
                   key=lambda i: sum((lights[i]["pos"][k] - eye[k]) ** 2
                                     for k in range(3)))
    for i in order[:args.shadow_lights]:
        lights[i]["shadow"] = True

    return {
        "shot": "drum",
        "scene": "res://scenes/drum.tscn",
        "glb": glbs,
        "triangles": total,
        "groups": sorted(set(all_groups)),
        "lights": lights,
        "camera": {"eye": list(eye), "target": list(aim), "up": list(up),
                   # Near plane at 0.15 m: the camera is a person's eye and
                   # things get close indoors. Far plane clears the drum's
                   # 2.6 km diagonal with room for the end cap behind it.
                   "fov": args.fov, "near": 0.15, "far": 12000.0},
        "sun_from": None,
        "sector": sector,
        "floor_radius_m": dg.FLOOR_R,
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


def fixture_lights(verts, tris, spans, energy, rng, shadow_n=2, eye=None):
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
        if name not in FIXTURE_LIGHTING:
            # Emissive only. The material still glows -- that is what makes the
            # trim read -- but it casts nothing. Measured per fitting, not
            # assumed; see FIXTURE_LIGHTING.
            continue
        spec = FIXTURE_LIGHTING[name]
        reach = spec.get("range_m") or rng
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
                      "energy": energy * spec["energy_rel"] * share,
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
                    lt["kind"] = "spot"
                    lt["angle"] = spec["angle_deg"]
                    lt["aim"] = [0.0, -1.0, 0.0]
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
# The entry points are NOT uniform and were established by reading each
# module's own _selftest, which is its canonical usage. They are recorded here
# so nobody has to rediscover them a third time -- test_materials_layer3 had
# already found them once for the coverage gate. Each takes (schema, profile,
# place) and returns whatever its module returns; `to_spans` normalises.
#
# `signage` is absent deliberately: it builds a sign board, which is a prop
# that stands in other rooms rather than a room you can stand in.
BESPOKE_GEOMETRY = {
    "alien_sector": lambda s, p, q: __import__("alien_sector").gallery(s, p),
    "command_control":
        lambda s, p, q: __import__("command_control").command_control(),
    "council_chamber":
        lambda s, p, q: __import__("council_chamber").council_chamber(),
    "customs": lambda s, p, q: __import__("customs").hall(s, p),
    "docking_bay": lambda s, p, q: __import__("docking_bay").docking_bay(
        0, s, p),
    "hospitality": lambda s, p, q: __import__("hospitality").room(),
    # The bay a place lands in is the first one; plant.bays() partitions the
    # deck by arc and every bay is the same construction.
    "plant": lambda s, p, q: __import__("plant").plant_bay(
        s, p, __import__("plant").bays(s, p)[0], 10.0),
    # THE CLASS COMES FROM THE PLACE. A lurker's berth and a command cabin are
    # different geometry, and rendering one class seven times would be seven
    # frames of one room. See QUARTERS_CLASS.
    "quarters": lambda s, p, q: __import__("quarters").run(
        s, p, __import__("quarters").class_by_key(QUARTERS_CLASS[q["key"]])),
    "zocalo": lambda s, p, q: __import__("zocalo").zocalo_run(
        3, cap_ends=True),
}


# Directory key -> quarters class key. Four of the seven differ, and they
# differ for a reason rather than by accident: the directory names a PLACE ON
# THE STATION and quarters.py names a HOUSING CLASS, and the ambassadorial
# suites and the League delegations are two places drawing on one class. A
# `key.removeprefix("qtr_")` would have produced three KeyErrors and no hint
# that the two vocabularies are different things.
#
# Asserted against both vocabularies in the self-test, so a new place or a
# renamed class fails here rather than rendering the wrong room.
QUARTERS_CLASS = {
    "qtr_command": "command",
    "qtr_personnel": "personnel",
    "qtr_civilian": "civilian",
    "qtr_transient": "transient",
    "ambassadorial_suites": "diplomatic",
    "league_delegations": "diplomatic",
    "alien_resident_qtr": "alien_resident",
}


# Modules that build in STATION coordinates rather than in a local Y-up frame,
# and therefore have to be unrolled before a person can be stood in them.
#
# Eight of the nine interior modules build a room the way you would model one:
# origin at the floor, +Y up, walk down +Z. `plant` does not, and it is right
# not to -- it builds an arc of the outer deck stack in place, at radius 447 to
# 471 m, because its whole subject is a bay that spans five decks of a spinning
# ring and it has to know where those decks are.
#
# The consequence for a RENDER is that "up" there is radially INWARD, toward
# the spin axis, and every other part of this shot -- the camera's up vector,
# `open_standpoint`'s eye height, a spot light's downward aim -- assumes +Y.
# The first plant frame is what showed it: the camera stood in a tangential
# direction and looked at two tanks side-on from outside them.
UNROLL = {"plant"}

# Group-name fragments whose triangles are THE SURFACE PEOPLE STAND ON, for
# modules where that is not the bottom of the model.
#
# `open_standpoint` finds candidate floors by histogramming near-horizontal
# triangle area, and in a plant bay that picks the tank-farm floor and the tank
# tops -- both far larger than the walkway. But plant.py's own docstring calls
# the catwalk "the walkable skeleton", and the module knows which group it is.
# Asking beats inferring, exactly as `light_` tagging beats guessing which
# material glows.
WALK_SURFACE = {"plant": ("plant_catwalk",)}


def unroll_to_local(verts):
    """Station coordinates -> a standing frame, by unrolling the cylinder.

    +X is along the arc, +Y is UP (which is radially inward, because down is
    outward under spin), +Z is along the station's axis. The mid-point of the
    geometry becomes the origin.

    Unrolling rather than projecting, because the arc is what a walker
    experiences: a plant bay spans about 20 degrees at 460 m, which is 160 m of
    catwalk and 8 m of sagitta. Flattening it makes the catwalk straight, which
    is what it feels like at 1.7 g, and costs nothing this shot can see.
    """
    import numpy as np

    a = np.asarray(verts, dtype=np.float64)
    r = np.hypot(a[:, 0], a[:, 1])
    ang = np.arctan2(a[:, 1], a[:, 0])
    # Unwrap about the mean angle so a bay straddling +/-pi does not tear.
    mid = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    d = (ang - mid + math.pi) % (2 * math.pi) - math.pi
    r_ref = float(r.max())              # the floor: the largest radius is down
    x = d * r_ref
    y = r_ref - r
    z = a[:, 2] - a[:, 2].mean()
    return [(float(x[i]), float(y[i]), float(z[i])) for i in range(len(a))]


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
        h = min(args.eye_height, ceil - 0.4)
        eye, aim = (x, h, z), (0.0, h, ln / 2.0 - 0.2)
    elif room in ("corridor", "junction"):
        # The kit has no prop to avoid, so the centreline just inside the near
        # end is right and is cheaper than searching for it.
        zs = [q[2] for q in verts]
        eye = (0.0, args.eye_height, min(zs) + 1.2)
        aim = (0.0, args.eye_height, max(zs) - 0.5)
    else:
        # A bespoke module: no declared extent and no prop naming convention,
        # so the standpoint is searched for against the geometry itself.
        walk = [sp for sp in spans
                if any(f in sp[0] for f in WALK_SURFACE.get(
                    __import__("directory").by_key(room)["module"], ()))]
        eye, aim = open_standpoint(verts, tris, args.eye_height,
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
                            shadow_n=args.shadow_lights, eye=eye)
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
        "ambient": (args.ambient if args.ambient is not None
                    else ambient_energy(room)),
        # Near plane at 60 mm: indoors the camera can stand against a wall, and
        # the drum's 0.15 m clips a prop the eye is leaning over.
        "camera": {"eye": list(eye), "target": list(aim), "up": [0.0, 1.0, 0.0],
                   "fov": args.fov, "near": 0.06, "far": 400.0},
        "sun_from": None,
    }


SHOTS = {"exterior": build_exterior, "drum": build_drum,
         "interior": build_interior}


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
    ap.add_argument("--eye-height", type=float, default=1.7)
    ap.add_argument("--orbit", type=_triple, default=(9200.0, 18.0, 214.0),
                    metavar="DIST,ELEV,AZ")
    ap.add_argument("--target-z", type=float, default=4023.0,
                    help="exterior: station midpoint")
    ap.add_argument("--lod", default="auto",
                    help="hull LOD: auto (by distance), or lod0..lod3 to force")
    ap.add_argument("--fov", type=float, default=46.0)
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
    ap.add_argument("--lights-per-run", type=int, default=10)
    ap.add_argument("--light-range", type=float, default=1100.0)
    ap.add_argument("--shadow-lights", type=int, default=2)
    ap.add_argument("--trams", type=int, default=2)
    ap.add_argument("--room", default="",
                    help="interior shot: a directory place key, or `corridor` "
                         "/ `junction` for the kit itself")
    ap.add_argument("--fixture-energy", type=float, default=3.0,
                    help="interior shot: energy per tagged light fitting")
    ap.add_argument("--ambient", type=float, default=None,
                    help="interior shot: override the room's ambient energy. "
                         "Exists so the anchor in AMBIENT_CALIBRATED_ENERGY "
                         "can be found by rendering and measuring rather than "
                         "by taste -- see tools/measure_frame.py")
    a = ap.parse_args()

    if a.gate_exterior is not None:
        sys.exit(0 if run_exterior_gates(*a.gate_exterior) else 1)

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
