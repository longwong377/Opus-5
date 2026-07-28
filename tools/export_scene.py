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


SHOTS = {"exterior": build_exterior, "drum": build_drum}


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
