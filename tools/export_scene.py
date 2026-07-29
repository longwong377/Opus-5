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
    python3 tools/export_scene.py --shot drum --stand 20,4700 --look 20,6300
    python3 tools/export_scene.py                      # runs the self-test
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

# A light 500 m across the drum should not be 20x dimmer than one 40 m
# overhead: the drum reads near-uniformly lit in `34b`, which is what a line
# source 2.6 km long inside a reflective cavity actually does. Godot's omni
# falloff is pow(1 - d/range, attenuation), so an exponent below 1 flattens it.
LAMP_ATTENUATION = 0.7


def light_energy(per_run):
    """Energy for one omni, given how many sample the run. See RUN_ENERGY."""
    return RUN_ENERGY / max(1, per_run)


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

    return {
        "shot": "exterior",
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
        "sun_from": list(_spherical(20000.0, args.sun_elev, args.sun_az, target)),
        # Kicker from behind and slightly below, opposite the key: its whole
        # job is to put a bright edge on the unlit side so the silhouette
        # separates from black space.
        "rim_from": list(_spherical(20000.0, -10.0, args.sun_az + 175.0, target)),
        # Fill sits on the OPPOSITE side of the camera axis from the key --
        # mirrored through it -- which is where a fill goes and where it does
        # some good. Put on the same side as the key it merely brightens the
        # side that is already lit, which is what the first version did and
        # why the terminator kept refusing to appear.
        "fill_from": list(_spherical(20000.0, args.orbit[1] + 10.0,
                                     2 * args.orbit[2] - args.sun_az, target)),
        "sun_at": list(target),
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
    "light_plant_flood": {"kind": "spot", "colour": (0.850, 0.830, 1.000),
                          "energy_rel": 1.00, "range_m": 30.0, "shadow": True,
                          "angle_deg": 35.0},
}
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
BESPOKE_EXPOSURE = {
    "zocalo": 0.92,          # vs reference/04-sector-red/more zocalo.png
    "hospitality": 1.34,     # vs reference/04-sector-red/Doug's Dugout.webp
    "command_control": 0.93,  # vs 03-sector-blue/comand and contorl.webp
    "docking_bay": 0.90,     # vs reference/03-sector-blue/dock.webp
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
    """
    import materials as mats

    raw = []
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
        idx = {i for tri in tris[lo:hi] for i in tri}
        if not idx:
            continue
        n = float(len(idx))
        c = [sum(verts[i][k] for i in idx) / n for k in range(3)]
        spec = FIXTURE_LIGHTING[name]
        lt = {"pos": c, "energy": energy * spec["energy_rel"],
              "colour": list(spec["colour"]),
              "range": spec.get("range_m") or rng, "attenuation": 1.0,
              "group": name, "_shadow": spec["shadow"]}
        if spec["kind"] == "spot":
            # Every spot in this table is a ceiling or soffit fitting aimed
            # straight down. That is the measurement in all five cases; the
            # one that is not quite -- cc_dais_key, "aimed down and aft" --
            # is aimed down here, because the aft direction is a property of
            # the room command and control is, and rooms.py builds the same
            # bay in eleven archetypes with no aft.
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
    out = []
    for lt in raw:
        for got in out:
            if got["group"] != lt["group"]:
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
        levels = [float(edges[i]) for i in np.where(keep)[0]]
        if not levels:
            levels = [float(lo[1])]
    # Only levels with headroom for a person, and never more than a handful:
    # every extra level is another occupancy grid.
    levels = sorted({round(v, 1) for v in levels if v + eye_h < hi[1] + 0.5})[:6]
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
    for v in levels:
        for flip in axes:
            pts = swapped if flip else a
            e, m, score = _standpoint_at(pts, tri, v + eye_h, clear_m)
            if best is None or score > best[0]:
                best = (score, (e[2], e[1], e[0]) if flip else e,
                        (m[2], m[1], m[0]) if flip else m)
    return best[1], best[2]


def _standpoint_at(a, tri, y, clear_m):
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
        check(abs(total_e - RUN_ENERGY * runs) < 1e-6,
              f"exported light energy sums to one run's worth per run "
              f"({total_e:.3f} against {RUN_ENERGY * runs:.3f})")
        check(len(sc["lights"]) % runs == 0,
              f"exported light count is a whole number per run "
              f"({len(sc['lights'])} over {runs} runs)")

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
