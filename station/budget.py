#!/usr/bin/env python3
"""Performance budget gates.

There is no GPU in the build container, so framerate cannot be measured here.
What can be measured is everything framerate is a function of: triangle counts,
draw calls, instance counts, vertex bandwidth and texture memory. Shipping
studios gate on exactly these numbers and treat the profiler as confirmation
rather than discovery, which is the only workable approach when the target
hardware is not present.

Budgets derive from the target in CLAUDE.md: RTX 4070 / RX 7800 XT class,
1440p60, 12 GB VRAM. Exceeding one is a build failure, not a warning.

WHAT SESSION 3w FOUND, AND IT IS THE P1 DESCRIPTOR VERBATIM. This file printed
`PASS  visible structure set  30,941 tri / 60,000 tri (51.6%)` and that quantity
was never rendered by anybody. It came from `interior_kit.corridor_section()`
measured IN ISOLATION -- a marginal triangles-per-metre rate multiplied by a
sight line, plus two `junction()` crossings. The walkable station has no
junctions anywhere (`interior.ring_arc` never places one) and no player has ever
stood in a bare kit section. Measured in the frustum of a standing camera on the
assembled deck the same quantity is 97,321 triangles -- 162% of the allowance
the gate was reporting as half spent. `docs/judge-3w.md` scored PERFORMANCE 1:
"a gate exists and does not measure the thing it names. Worse than 0, because it
prints PASS."

SO THE INTERIOR IS NOW GATED ON AN ASSEMBLED DECK, built by `deck.build_deck`,
counted inside a real frustum from a standing eye, swept over every position and
heading a player can take. It costs about 40 seconds and it is the only honest
way to answer the question. Three of its bounds are RED as this is written and
they are left red: the numbers below are not tuned to fit the content, and the
content is not thinned to fit the numbers.

The three new bounds asked for in session 3x -- a frame the player actually
renders, a DRAW CALL budget, a COLLISION triangle budget -- are derived in
`DRAW` and `COLLISION` below and logged as INV-082..INV-085. Every one of them
prints how far the current content is from failing it, in units of the content,
so no bound in this file is a bound that cannot fail.
"""
import argparse
import json
import math
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "station/generated/hull_manifest.json")
# THE SHIPPED EXTERIOR, and the path matters because this gate was reading one
# nobody writes. `tools/export_scene.py` has always written the hull to
# `scene/exterior/hull.glb` -- `station.glb` is a name from before the scene
# directory existed. Combined with the `if size:` guard below, the effect was a
# budget that could only ever be silently skipped: the one shipped artefact
# whose size a player actually pays for was unmeasured for every session since.
# Same defect as the stale committed frames -- a gate reading an artefact that
# is not the artefact.
GLB = os.path.join(ROOT, "station/generated/scene/exterior/hull.glb")

# A 4070 sustains roughly 20-30 M triangles/frame at 1440p60 with a modern
# deferred renderer. The exterior hull is always-visible background geometry
# competing with interiors, NPCs and effects, so it gets a deliberately small
# slice -- 2% of frame budget -- leaving headroom for everything in front of it.
BUDGETS = {
    "exterior_triangles": 400_000,
    "exterior_draw_calls": 64,
    "glb_size_mb": 64.0,
    "vertex_bandwidth_mb": 32.0,
    # PRIMITIVES IN A SHIPPED DECK, and this one is a REGRESSION BOUND rather
    # than a hardware limit -- said plainly, because a bound that pretends to
    # be derived when it is not is the disease this file exists to treat.
    #
    # What it is not: a frame draw-call limit. A deck .glb is the whole 345
    # degree ring and `walk.gd` loads it whole, but a corridor's sight line is
    # bounded at 66 m (see `populace.corridor_sight_m`), which on a 211 m
    # radius is 18 degrees -- about 5% of the ring in frame at once, plus what
    # shows through the doors. The in-frame figure is therefore an order below
    # this and is not what is being gated.
    #
    # What it IS: the number that catches a body emitting its parts unmerged.
    # That regression was measured at 1,262 primitives on `blue/0/0` with 1,052
    # of them people -- twelve per inhabitant, because `body.py` tags twelve
    # parts and `export_gltf` writes one primitive per OBJ group. Merged by
    # material (`populace._by_material`) the same deck is 376. 600 sits above
    # the good number with room for the station to grow busier and far below
    # the bad one, and `check`'s `when=` states the distance in inhabitants.
    "deck_primitives": 600,
}

# Interior is gated on what can be SEEN AT ONCE, not on total built geometry.
# Totalling the interior is meaningless: the concentric-ring topology gives ring
# 1 alone a circumference of 2*pi*278.3 = 1,749 m per sector, and with five
# rings across six sectors the built total runs to millions of triangles that
# are never simultaneously in frame.
#
# WHAT IS LEFT HERE IS THE MARGINAL RATE AND NOTHING ELSE. `corridor_tris_per_m`
# is a property of geometry that actually ships: `interior.ring_arc` calls
# `interior_kit.corridor_section`, so every metre of walkable station is built
# at this rate and a regression in it is a regression everywhere.
#
# REMOVED IN 3x, and both removals are the point of this session:
#   * `visible_set_tris` as a SYNTHETIC ESTIMATE -- per-metre rate x sight line
#     + two junctions. The number now comes from a frustum on an assembled deck.
#     The estimate said 30,941. The frustum says 97,321 for the same class of
#     content. The estimate was not conservative, it was wrong.
#   * `junction_tris` / `junctions_in_view` -- a bound on `interior_kit.junction`,
#     which appears in NO walkable geometry. `ring_arc` sweeps a continuous arc
#     with door apertures cut in it and never places a crossing. Gating a
#     corridor's frame cost on two crossings that are not there is measuring a
#     part of the kit nobody renders, which is the defect this file had.
#     Recorded so the removal is auditable: it read 1,400 / 2,000 tri (70.0%).
INTERIOR = {
    "corridor_tris_per_m": 400,      # marginal rate along a run
    # Structure alone in the standing frustum. UNCHANGED from the value this
    # gate has always carried -- what changed is that it is now measured on the
    # assembled deck instead of on the kit in isolation, and at that it FAILS.
    # Raising it to fit would be the whole disease.
    "visible_set_tris": 60_000,
}

# 60,000 is structure only. At 1440p60 on the target card the whole frame
# affords roughly 1.2 M triangles, and interior structure should not take more
# than ~5% of it: the same view has to carry props, fittings, signage, NPCs and
# whatever is through the windows. If structure alone reaches 60 k the kit has
# become too expensive to dress.
#
# THIS FILE CONTRADICTS ITSELF ON THE FRAME FIGURE AND ALWAYS HAS. `BUDGETS`
# above says "a 4070 sustains roughly 20-30 M triangles/frame at 1440p60" and
# derives the exterior's 400,000 as "2% of frame budget", which implies a
# 20,000,000-triangle frame. `FRAME_TRIANGLES` says 1,200,000 -- 16.7x smaller,
# against which the exterior's own 400,000 is 33% of frame, not 2%.
# `docs/AAA-STANDARD.md` quotes the 2% sentence approvingly, so the
# contradiction is load-bearing in two documents.
#
# NEITHER NUMBER IS CHANGED HERE. Session 3x's brief was to measure honestly,
# and moving a frame budget is how a gate is made green without content
# improving. Everything below is gated against the SMALLER, tighter figure,
# because a budget's job is to be the binding constraint. If the 20 M reading is
# the right one then every interior bound in this file has 16x more headroom
# than it claims -- and that is a question for a frame capture on the target
# card, which is the only thing that can settle it. Recorded as INV-082.
INTERIOR_FRAME_SHARE = 0.05
FRAME_TRIANGLES = 1_200_000

# The habitat drum is not a corridor and the corridor gate does not describe it.
# A corridor is budgeted on a 50 m sight line because a wall stops you seeing
# further. Standing in the Garden there is no wall: the far end cap is 2.6 km
# away, the ground overhead is 556 m up, and every triangle in the volume is in
# the frustum at once. It is the worst visibility case in the project and until
# now it had no gate at all.
#
# It also earns a bigger share than a corridor. This is the view the whole
# structure phase exists to produce, so it gets a quarter of the frame rather
# than a twentieth -- and it has to hold that with LOD, since the far half of
# the drum is over a kilometre away and cannot be drawn at full rate.
# A ring corridor cannot be emitted whole -- one deck of the drum's sub-floor
# ring is 1,771 m around and 580,800 triangles, nine times the entire interior
# frame budget. Cells are the unit that is built and streamed, so they are what
# gets gated.
CELLS = {
    "cell_tris": 60_000,
    "resident_tris": 180_000,     # the cell you are in plus both neighbours
    # Bending costs more per metre than the straight kit, because each section
    # of the bend carries its own end caps. Gated so the overhead stays visible
    # rather than quietly growing -- welding sections is the fix if it does.
    "bent_tris_per_m": 400,
}

DRUM = {
    "visible_set_tris": 300_000,
    "frame_share": 0.25,
    # Everything in the drum's inner surface is potentially visible, so the
    # meaningful density is per square metre of ground, not per metre of run.
    # This is the number that decides whether the ground can be per-object
    # geometry or has to be a heightfield -- and it says heightfield.
    "surface_tris_per_m2": 0.5,
}

# ---------------------------------------------------------------------------
# THE STANDING FRAME. What a player actually renders, on an assembled deck.
# ---------------------------------------------------------------------------
#
# THE CAMERA IS NOT A CHOICE, IT IS READ OFF THE SHIPPED ONE where the shipped
# one states a value. `godot/scripts/player.gd` sets `near = 0.15` and
# `far = 12000.0` on the camera it creates, and puts the eye `eye_height_m = 1.7`
# above the body origin. Those three are copied here and `shipped_camera()`
# re-reads them at run time so they cannot drift.
#
# FIELD OF VIEW IS THE ONE NUMBER THIS FILE SPECIFIES RATHER THAN COPIES, and
# it is 70 degrees VERTICAL because Godot's `Camera3D.fov` is vertical when
# `keep_aspect` is its default `KEEP_HEIGHT`. At 16:9 that is 102.5 degrees
# horizontal, the top of the range PC first-person games ship. `player.gd` sets
# no `fov` at all, so the camera a player is given today is Godot 4's default
# 75 degrees -- WIDER than the budget, and therefore rendering MORE than the
# budget measures. `deck_section` checks that and fails until they agree; the
# fix is one line in `player.gd`, which this session does not own. INV-083.
#
# ASPECT COMES FROM THE TARGET, NOT FROM THE WINDOW. CLAUDE.md's target is
# 1440p, so 2560 x 1440 and 16:9. `godot/project.godot` opens a 1920 x 1080
# window, which is the same aspect and therefore the same frustum; pixel count
# changes shading cost, not the triangle set.
#
# THE SWEEP IS THE GATE. AAA-STANDARD scores a single convenient camera as
# PERFORMANCE 2 and a swept worst case as 3, so this sweeps: every station on a
# lattice around the built arc, every heading on a lattice at each station. The
# lattice is stated rather than tuned -- 48 x 24 -- and its own sampling error is
# printed, measured by re-running at half resolution.
DECK = {
    "sector": "blue", "ring": 0, "deck": 0,
    "eye_m": 1.70,                # above the COLLISION floor -- see deck_camera
    "fov_v_deg": 70.0,            # vertical, 16:9 -> 102.5 deg horizontal
    "aspect": 16.0 / 9.0,         # 2560 x 1440
    "near_m": 0.15,               # player.gd
    "far_m": 12_000.0,            # player.gd
    "stations": 48,               # sweep lattice around the arc
    "headings": 24,               # sweep lattice in yaw, 15 deg apart
    # Everything in the frame, not just structure: props, fittings, doors and
    # people are what the player is looking at. The allowance is the frame share
    # already committed in this file to the widest-open view the project has --
    # the drum's 25% -- on the argument that a corridor interior, which is a
    # closed box with a wall a metre from each shoulder, cannot be worth MORE
    # frame than standing in the Garden with 4.5 million square metres in view.
    # It is a ceiling taken from an existing number, not a new one.
    "visible_all_tris": int(FRAME_TRIANGLES * DRUM["frame_share"]),
}

# ---------------------------------------------------------------------------
# OCCLUSION. What a wall in front of you is worth, and at what granularity.
# ---------------------------------------------------------------------------
#
# `Frustum`'s docstring below has said since 3x that no occlusion is applied and
# that this is "not an approximation -- it is what ships". That was true and it
# is now measured rather than merely conceded. `station/occluders.py` builds the
# geometry; this section says what it buys.
#
# WHAT THIS PASS MODELS, STATED BEFORE ANY NUMBER, because an occlusion pass
# that assumes perfect culling is as wrong as none at all:
#
#   * Godot 4 rasterises the scene's OccluderInstance3D geometry into a small
#     depth buffer on the render thread and then tests each INSTANCE's
#     axis-aligned bounding box against it. It does not test triangles. So the
#     figure that describes the shipped renderer is the INSTANCE one, and it is
#     the one gated.
#   * `export_gltf` writes one primitive per OBJ group and `deck.build_deck`
#     names a room's groups `<key>__<name>` while the corridor keeps the kit's
#     own bare names. A corridor group therefore spans the WHOLE 345-degree
#     ring and its AABB contains the camera, so no occluder can ever cull it.
#     That is not a defect in the occluder; it is what submitting a ring as one
#     primitive costs, and the pass prints it as its own line.
#   * the TRIANGLE figure is reported beside it as the ceiling -- what occlusion
#     would be worth if the renderer culled per triangle. Nothing does. It is
#     there so the gap between the two is visible, because the gap is the
#     argument for spatial submission.
#   * the CELL figure is the third: the same AABB test with the deck cut into
#     the streaming cells `interior.ring_cells` declares. `stream.gd::bake`
#     already writes one MeshInstance3D per group PER CELL, and as of 4p
#     `tools/export_scene.py` names the deck shot's OBJ groups the same way, so
#     this is a decomposition that exists rather than one that would.
#   * the SHIP figure is the fourth and it is the one gated: the cell figure
#     restricted to the cells the streamer holds in memory. See
#     `shipped_streaming()` -- the boot manifest names a cell set, so the
#     monolithic row is the FALLBACK path and not the shipped one.
#
# Every one of the three is conservative in the same direction -- an instance or
# a triangle survives unless it is provably behind the occluder -- so all three
# understate the saving rather than flatter it.
OCCLUSION = {
    # THE DEPTH BUFFER'S RESOLUTION IS DERIVED FROM THE NARROWEST HOLE THE
    # OCCLUDER HAS, and the derivation runs the dangerous way round. A coarse
    # buffer loses a doorway between two pixel centres, the wall's depth fills
    # the pixel, and the room behind it is culled -- over-occlusion, which is a
    # hole in the world rather than a slow frame. So:
    #
    #   door_width_m       1.5      interior_kit.PROVISIONAL, read at run time
    #   sight_m           60.5      the corridor's own measured sight line,
    #                               deck.build_deck's `corridor_people`
    #   subtense          1.42 deg  = 2*atan(0.75/60.5)
    #   fov_h            102.4 deg  DECK's own camera
    #   pixels per door  >= 2       Nyquist on the aperture
    #
    # -> W >= 2 * 102.4 / 1.42 = 144. 160 x 90 is the next 16:9 step up.
    # `deck_section` recomputes that bound from the deck it is measuring and
    # FAILS if the buffer is under it, so the number cannot quietly stop being
    # derived.
    "buffer_w": 160,
    "buffer_h": 90,
    "min_door_px": 2.0,
    # A triangle wider than this on screen is never culled. The per-triangle
    # test reads the occluder depth at each of the three vertices' own pixels,
    # max-pooled over a 3x3 neighbourhood, which covers a triangle whose screen
    # extent stays inside that neighbourhood and would silently over-cull one
    # that does not. Big triangles are the corridor's own floor and walls, which
    # are INSIDE the occluder and never cullable anyway.
    "max_tri_px": 3.0,
    # Only cull what is clearly behind. Not chosen: the occluder's cylindrical
    # bands are faceted to `collision.MAX_SAG_M`, so a facet can sit that far
    # inside the surface it stands for.
    "bias_m": 0.005,
    # The occluded sweep runs on every other station and heading -- the same
    # half-resolution lattice `deck_section` already re-uses for its own
    # sampling-error figure, whose error on this deck it prints.
    "sweep_stride": 2,
}


def occluder_path(sector, ring, deck, z_m=None, root=ROOT):
    """Where `tools/export_scene.py` writes the occluder for one deck.

    ONE NAME, TWO FILES THAT MUST AGREE, so it lives in a function rather than
    in two format strings. Keyed by z-cluster exactly as the deck artefacts
    beside it are, because a deck in the gazetteer is not a z-slice and the
    corridor arc differs between clusters.
    """
    stem = f"{sector}_{ring}_{deck}"
    if z_m is not None:
        stem += f"_z{int(round(z_m))}"
    return os.path.join(root, "station/generated/scene/deck", stem + "_occ.tscn")


def occlusion_chain(sector, ring, deck, z_m=None, root=ROOT):
    """The three things that must ALL be true before an occlusion saving is real.

    A GATE THAT APPLIES A DISCOUNT THE BUILD DOES NOT GET IS WORSE THAN NO
    GATE, so this is a ladder and each rung says what is missing in the units of
    the fix:

      1. `rendering/occlusion_culling/use_occlusion_culling` on in
         `godot/project.godot`. Godot 4's engine default is FALSE -- measured
         headless against this build with the key absent -- so without the line
         every occluder in the scene is ignored. **If this rung is missing the
         pass is not computed at all**, because a number that cannot be reached
         is not a measurement.
      2. the occluder geometry emitted beside the deck it belongs to.
      3. something in `godot/` that instantiates it. Emitting a resource nobody
         loads is exactly the failure `tools/wiring.py` exists to catch, and
         this file must not be the ninth instance of it.

    Rungs 2 and 3 do not stop the pass. They stop the SAVING being applied to
    the gated bounds, and each is a `check()` of its own so the build says which
    one is missing.
    """
    out = {"setting": False, "geometry": None, "runtime": (), "why": []}
    pg = os.path.join(root, "godot/project.godot")
    txt = ""
    if os.path.exists(pg):
        with open(pg) as f:
            txt = f.read()
    m = re.search(r"^occlusion_culling/use_occlusion_culling\s*=\s*(\w+)",
                  txt, re.M)
    out["setting"] = bool(m and m.group(1).lower() == "true")
    if not out["setting"]:
        out["why"].append(
            "godot/project.godot does not set "
            "rendering/occlusion_culling/use_occlusion_culling=true, and the "
            "engine default is false, so Godot ignores every "
            "OccluderInstance3D in the scene")

    p = occluder_path(sector, ring, deck, z_m, root)
    if os.path.exists(p):
        out["geometry"] = p
    else:
        out["why"].append(
            f"{os.path.relpath(p, root)} has not been written -- "
            f"`python3 tools/export_scene.py --shot deck --deck "
            f"{sector}/{ring}/{deck}` writes it")

    hits = []
    for base, _dirs, names in os.walk(os.path.join(root, "godot")):
        for n in names:
            if not n.endswith((".gd", ".tscn")):
                continue
            fp = os.path.join(base, n)
            try:
                with open(fp) as f:
                    s = f.read()
            except OSError:
                continue
            if "OccluderInstance3D" in s or "ArrayOccluder3D" in s \
                    or "_occ.tscn" in s:
                hits.append(os.path.relpath(fp, root))
    out["runtime"] = tuple(sorted(hits))
    if not hits:
        out["why"].append(
            "nothing under godot/ mentions OccluderInstance3D, ArrayOccluder3D "
            "or *_occ.tscn, so the emitted occluder is never added to the "
            "scene tree and the engine has nothing to rasterise")
    out["applied"] = bool(out["setting"] and out["geometry"] and out["runtime"])
    return out


# ---------------------------------------------------------------------------
# WHAT THE SHIPPED BUILD ACTUALLY LOADS. Not what `walk.gd --glb` loads.
# ---------------------------------------------------------------------------
#
# THIS FILE HAS BEEN MEASURING A PATH THE BUILD DOES NOT TAKE, and it said so in
# its own labels: the row printed as `instance (as shipped) -- WHAT GODOT DOES`
# is one primitive per OBJ group of the MONOLITHIC deck `.glb`, which is what
# `walk.gd::_load_level` loads. The shipped scene is STREAMED. That is the same
# trap as the occluder that was wired into `_load_level` in session 4o -- one
# level up, and it has been here since the deck gate was written.
#
# The evidence, all of it on disk and all of it re-readable by this function:
#
#   station/generated/scene/boot.json         names a `cells_path` and
#                                             `cells_count`; `station/boot.py`
#                                             writes it
#   godot/scripts/main.gd                     `w.set("cells_path", ...)` from
#                                             that manifest -- `station/boot.py`
#                                             gates that line's existence
#   godot/scripts/walk.gd::_load_streamed     taken when `cells_path` is set;
#                                             `_load_level` is the fallback
#   station/generated/scene/.../cells.json    the manifest `stream.gd::bake()`
#                                             wrote, one row per cell
#   tools/bake_station.py                     955 baked `.scn` cells on disk
#
# WHAT STREAMING CHANGES FOR A BUDGET, and it is two separate things:
#
#   granularity  `stream.gd::_write_cell` emits one MeshInstance3D per group
#                PER CELL, so the cull unit is (group x cell) and not (group).
#                That is the `instance x cells` row this file already prints as
#                a hypothetical.
#   residency    only cells within `radius_m` of the body are loaded at all, and
#                one outside `free_m` is freed. Fifteen of blue/0/0's eighteen
#                cells are not in memory, so they are not submitted, not culled
#                and not drawn.
#
# THE RESIDENCY NUMBERS ARE DERIVED TWICE AND CHECKED AGAINST EACH OTHER. Once
# from `interior.ring_cells` here, and once read out of the baked manifest that
# `stream.gd` wrote from the same source. A gate reading a committed artefact
# must be able to rebuild it (this project's own rule, from the stale-frame
# session); a gate that ONLY rebuilds it cannot tell whether the artefact on
# disk still matches. Both, and `check` fails on disagreement.
BOOT = os.path.join(ROOT, "station/generated/scene/boot.json")
STREAM_GD = os.path.join(ROOT, "godot/scripts/stream.gd")


def shipped_streaming(sector, ring, deck, root=ROOT):
    """Does the shipped build stream this deck, and on what residency rule?

    Returns a dict. `streamed` is False when the boot manifest names no cell
    set, in which case the monolithic figures ARE the shipped ones and this
    file's old labels were right.
    """
    out = {"streamed": False, "why": [], "cells_path": "", "n_cells": 0,
           "radius_m": 0.0, "free_m": 0.0, "manifest": None,
           "rule": {}, "boot": BOOT.replace(ROOT, "").lstrip("/")}
    bp = os.path.join(root, "station/generated/scene/boot.json")
    if not os.path.exists(bp):
        out["why"].append("no station/generated/scene/boot.json -- run "
                          "`python3 station/boot.py`; without it nothing here "
                          "can say which path the build takes")
        return out
    with open(bp) as f:
        boot = json.load(f)
    out["deck"] = boot.get("deck", "")
    cp = boot.get("cells_path", "")
    if not cp:
        out["why"].append(
            f"boot.json names no cells_path ({boot.get('cells_why', '')!r}), so "
            f"main.gd hands walk.gd an empty one and _load_streamed is skipped "
            f"-- the monolithic .glb IS what ships")
        return out
    out["cells_path"] = cp
    if not os.path.exists(cp):
        out["why"].append(f"boot.json names {os.path.basename(cp)} and it is "
                          f"not on disk")
        return out
    with open(cp) as f:
        man = json.load(f)
    res = man.get("residency", {}) or {}
    out["manifest"] = {
        "cells": len(man.get("cells", ())),
        "cell_deg": float(man.get("cell_deg", 0.0)),
        "radius_m": float(res.get("radius_m", 0.0)),
        "free_m": float(res.get("free_radius_m", 0.0)),
        "written_by": man.get("written_by", "?"),
        "tris": sum(int(c.get("tris", 0)) for c in man.get("cells", ())),
    }
    # THE RULE, READ OFF `stream.gd` ITSELF, exactly as `shipped_camera()` reads
    # `player.gd`. Two lines of that file decide how much of a deck is in memory
    # and a budget that hard-codes them is a budget that drifts silently.
    src = ""
    if os.path.exists(os.path.join(root, "godot/scripts/stream.gd")):
        with open(os.path.join(root, "godot/scripts/stream.gd")) as f:
            src = f.read()
    out["rule"]["radius_is_sight_line"] = bool(
        re.search(r'"radius_m"\s*:\s*sight\b', src))
    out["rule"]["free_is_max_sight_cell"] = bool(
        re.search(r'"free_radius_m"\s*:\s*maxf\(\s*sight\s*,\s*'
                  r'float\(row\["cell_length_m"\]\)\s*\)', src))
    out["rule"]["resident_within_radius"] = bool(
        re.search(r"if\s+d\[id\]\s*<=\s*radius_m", src))
    out["rule"]["freed_past_free_m"] = bool(
        re.search(r"if\s+want\.has\(id\)\s+or\s+d\[id\]\s*<=\s*free_m", src))
    out["streamed"] = True
    out["n_cells"] = int(boot.get("cells_count", 0)) or \
        out["manifest"]["cells"]
    out["radius_m"] = out["manifest"]["radius_m"]
    out["free_m"] = out["manifest"]["free_m"]
    return out


def cell_arc_z(fr, cell, n_cells):
    """z extent of each cell's own geometry. `stream.gd` records the same thing.

    Derived from the mesh rather than read from the manifest, because
    `distance_to` uses it and a residency radius taken from a stale artefact is
    a residency radius nobody can check.
    """
    import numpy as np                                          # noqa: PLC0415
    z = fr.cz
    lo = np.full(n_cells, np.inf)
    hi = np.full(n_cells, -np.inf)
    for k in range(n_cells):
        m = cell == k
        if m.any():
            lo[k] = z[m].min()
            hi[k] = z[m].max()
    return lo, hi


def resident_cells(eye, n_cells, cell_deg, radius_m, z_lo, z_hi, free_m):
    """Which cells are in memory with the body at `eye`. `stream.gd::update`.

    THE TEST IS `distance_to` FROM THAT FILE, transcribed: angular distance to
    the cell's own arc taken ALONG the ring at its radius, combined with the
    axial gap to the cell's z extent. Not a centre-to-centre distance -- a cell
    the body is standing in is at distance zero however long it is.

    CONSERVATIVE ON PURPOSE. `update()` loads inside `radius_m` and frees only
    past `free_m`, so a cell between the two may or may not be resident
    depending on which way the body walked in. This counts it as RESIDENT, which
    over-states what the engine holds and therefore over-states the frame. Every
    other approximation in this file leans the same way.
    """
    import numpy as np                                          # noqa: PLC0415
    r = math.hypot(eye[0], eye[1])
    a = math.degrees(math.atan2(eye[1], eye[0])) % 360.0
    k = np.arange(n_cells)
    a0 = k * cell_deg
    a1 = (k + 1) * cell_deg
    inside = (a >= a0) & (a < a1)
    d0 = np.minimum(np.abs(a - a0) % 360.0, 360.0 - np.abs(a - a0) % 360.0)
    d1 = np.minimum(np.abs(a - a1) % 360.0, 360.0 - np.abs(a - a1) % 360.0)
    da = np.where(inside, 0.0, np.minimum(d0, d1))
    along = np.radians(da) * r
    dz = np.maximum(0.0, np.maximum(z_lo - eye[2], eye[2] - z_hi))
    dz = np.where(np.isfinite(dz), dz, 0.0)
    return np.hypot(along, dz) <= free_m


def _cam_axes(eye, fwd, up):
    """Forward, up and right, orthonormal, in `_frustum`'s own convention."""
    import numpy as np                                          # noqa: PLC0415
    f = np.asarray(fwd, float)
    f = f / np.linalg.norm(f)
    u = np.asarray(up, float)
    u = u - f * float(u @ f)
    u = u / np.linalg.norm(u)
    return np.asarray(eye, float), f, u, np.cross(u, f)


def _screen(P, eye, f, u, r, tv, th, w, h):
    """Pixel coordinates and forward depth for many world points."""
    import numpy as np                                          # noqa: PLC0415
    d = np.asarray(P, float) - eye
    z = d @ f
    zz = np.where(np.abs(z) < 1e-9, 1e-9, z)
    px = ((d @ r) / (zz * th) + 1.0) * 0.5 * w
    py = (1.0 - (d @ u) / (zz * tv)) * 0.5 * h
    return px, py, z


def occluder_depth(occ_v, occ_t, cam, w, h, near):
    """Nearest occluder depth per pixel, or inf. The engine's buffer, in numpy.

    CONSERVATIVE IN BOTH OF THE TWO WAYS IT CAN BE, and neither is an accident:

      coverage  a pixel is filled only when its CENTRE is inside the triangle,
                so the buffer never claims coverage the occluder does not have.
                Over-claiming coverage culls things that are visible.
      depth     the whole covered area takes the triangle's FARTHEST vertex
                depth rather than an interpolated one, so the occluder is
                recorded as further away than it is and culls less.

    A triangle with any vertex at or behind the near plane is skipped entirely
    and counted, because clipping it correctly is work that would only ever
    increase the saving.
    """
    import numpy as np                                          # noqa: PLC0415
    eye, f, u, r, tv, th = cam
    V = np.asarray(occ_v, float)
    px, py, z = _screen(V, eye, f, u, r, tv, th, w, h)
    Z = np.full((h, w), np.inf)
    xs = np.arange(w) + 0.5
    ys = np.arange(h) + 0.5
    skipped = 0
    for i0, i1, i2 in occ_t:
        z0, z1, z2 = z[i0], z[i1], z[i2]
        if min(z0, z1, z2) <= near:
            skipped += 1
            continue
        ax, ay, bx, by, cx, cy = px[i0], py[i0], px[i1], py[i1], px[i2], py[i2]
        x0 = max(0, int(math.floor(min(ax, bx, cx))))
        x1 = min(w - 1, int(math.ceil(max(ax, bx, cx))))
        y0 = max(0, int(math.floor(min(ay, by, cy))))
        y1 = min(h - 1, int(math.ceil(max(ay, by, cy))))
        if x1 < x0 or y1 < y0:
            continue
        X = xs[x0:x1 + 1][None, :]
        Y = ys[y0:y1 + 1][:, None]
        e0 = (bx - ax) * (Y - ay) - (by - ay) * (X - ax)
        e1 = (cx - bx) * (Y - by) - (cy - by) * (X - bx)
        e2 = (ax - cx) * (Y - cy) - (ay - cy) * (X - cx)
        inside = (((e0 >= 0) & (e1 >= 0) & (e2 >= 0))
                  | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0)))
        if not inside.any():
            continue
        sub = Z[y0:y1 + 1, x0:x1 + 1]
        np.minimum(sub, max(z0, z1, z2), out=sub, where=inside)
    return Z, skipped


def _pool3(Z):
    """3x3 maximum of a depth buffer, padded with inf so a border never culls."""
    import numpy as np                                          # noqa: PLC0415
    h, w = Z.shape
    P = np.full((h + 2, w + 2), np.inf)
    P[1:-1, 1:-1] = Z
    return np.maximum.reduce([P[dy:dy + h, dx:dx + w]
                              for dy in range(3) for dx in range(3)])


def group_boxes(V, T, key, n):
    """World AABB per instance, as `(lo, hi)` arrays of shape (n, 3).

    `key` is the instance every triangle belongs to. What an instance IS is not
    this function's choice: `export_gltf` writes one primitive per OBJ group and
    merges by name, so a group name is a draw and therefore a cull unit.
    """
    import numpy as np                                          # noqa: PLC0415
    P = V[T]
    tmin, tmax = P.min(axis=1), P.max(axis=1)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    tmin, tmax = tmin[order], tmax[order]
    edge = np.searchsorted(ks, np.arange(n + 1))
    lo = np.full((n, 3), np.inf)
    hi = np.full((n, 3), -np.inf)
    for b in range(n):
        a, z = edge[b], (edge[b + 1] if b + 1 < len(edge) else len(ks))
        if z > a:
            lo[b] = tmin[a:z].min(axis=0)
            hi[b] = tmax[a:z].max(axis=0)
    return lo, hi


def _corners(lo, hi):
    import numpy as np                                          # noqa: PLC0415
    n = len(lo)
    out = np.empty((n, 8, 3))
    for i in range(8):
        for ax in range(3):
            out[:, i, ax] = hi[:, ax] if (i >> ax) & 1 else lo[:, ax]
    return out


def boxes_in_frustum(corners, planes):
    """An AABB survives a plane if ANY corner is inside it. Standard, and loose
    in the safe direction -- it keeps boxes a tighter test would reject."""
    import numpy as np                                          # noqa: PLC0415
    keep = np.ones(len(corners), bool)
    for n, d in planes:
        keep &= ((corners @ n + d) >= 0.0).any(axis=1)
    return keep


def boxes_occluded(corners, Z, cam, w, h, near, bias):
    """Which AABBs are entirely behind the occluder buffer. Godot's own test.

    An instance is culled when its NEAREST point is further than the FURTHEST
    occluder depth anywhere in its screen rect. A pixel the occluder does not
    cover holds inf, so one uncovered pixel in the rect keeps the instance --
    which is the correct and conservative answer.
    """
    import numpy as np                                          # noqa: PLC0415
    eye, f, u, r, tv, th = cam
    n = len(corners)
    px, py, z = _screen(corners.reshape(-1, 3), eye, f, u, r, tv, th, w, h)
    px, py, z = px.reshape(n, 8), py.reshape(n, 8), z.reshape(n, 8)
    ok = z.min(axis=1) > near
    zmin = z.min(axis=1)
    x0 = np.clip(np.floor(px.min(axis=1)), 0, w - 1).astype(int)
    x1 = np.clip(np.ceil(px.max(axis=1)), 0, w - 1).astype(int)
    y0 = np.clip(np.floor(py.min(axis=1)), 0, h - 1).astype(int)
    y1 = np.clip(np.ceil(py.max(axis=1)), 0, h - 1).astype(int)
    out = np.zeros(n, bool)
    for i in np.nonzero(ok)[0]:
        if Z[y0[i]:y1[i] + 1, x0[i]:x1[i] + 1].max() + bias < zmin[i]:
            out[i] = True
    return out


def tris_occluded(px, py, z, T, Zp, w, h, near, bias, max_px):
    """Which triangles are behind the occluder. THE CEILING, NOT THE BEHAVIOUR.

    No renderer this project ships to culls per triangle. This exists so the
    distance between it and `boxes_occluded` is on the page, because that
    distance is the whole argument for submitting a deck in spatial pieces.
    """
    import numpy as np                                          # noqa: PLC0415
    zt, pxt, pyt = z[T], px[T], py[T]
    ok = (zt > near).all(axis=1)
    ok &= (pxt.max(axis=1) - pxt.min(axis=1)) <= max_px
    ok &= (pyt.max(axis=1) - pyt.min(axis=1)) <= max_px
    ok &= ((pxt >= 0) & (pxt < w) & (pyt >= 0) & (pyt < h)).all(axis=1)
    ix = np.clip(pxt, 0, w - 1).astype(int)
    iy = np.clip(pyt, 0, h - 1).astype(int)
    ok &= (zt > Zp[iy, ix] + bias).all(axis=1)
    return ok


def deck_occlusion(schema, profile, sector, ring, deck, stats, meta, fr, KL,
                   cam_at, worst_all, worst_struct):
    """What the corridor's own walls are worth, on the deck already measured.

    Returns a dict, or raises. Everything it prints is measured here; nothing is
    read from an artefact this function could not rebuild.
    """
    import numpy as np                                          # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import occluders as OC                                      # noqa: PLC0415
    import interior as it                                       # noqa: PLC0415
    import interior_kit as ik                                   # noqa: PLC0415

    w, h = OCCLUSION["buffer_w"], OCCLUSION["buffer_h"]
    near, far = DECK["near_m"], DECK["far_m"]
    fov, asp = DECK["fov_v_deg"], DECK["aspect"]
    tv = math.tan(math.radians(fov) / 2.0)
    th = tv * asp
    fov_h = 2 * math.degrees(math.atan(th))
    bias = OCCLUSION["bias_m"]

    t0 = time.time()
    # THE DOORS COME FROM `stats`, NOT FROM `collision_meta`, and the difference
    # is a sealed occluder. `deck.build_deck` builds its `collision_meta` shell
    # with no `doors=` at all -- it exists only to locate the spawn -- so
    # `meta["doors"]` is empty on every deck. An occluder cut from that would be
    # a tube with no doorways in it, which `occluders.py`'s own control shows
    # hiding 34 rays' worth of room.
    doors = stats.get("doors", ()) or meta.get("doors", ())
    ov, ot, om = OC.occluder_shell(
        schema, profile, sector, ring, degrees=meta["arc_deg"],
        start_deg=meta["start_deg"], radius_m=meta["radius_m"],
        z_offset=meta["z_m"], doors=doors)
    build_s = time.time() - t0

    # --- the buffer has to resolve the narrowest hole, derived from THIS deck
    sight = (stats.get("corridor_people") or {}).get("sight_m", 60.0)
    door_w = ik.PROVISIONAL["door_width_m"]
    subtense = 2.0 * math.degrees(math.atan(door_w / 2.0 / max(sight, 1e-6)))
    w_needed = OCCLUSION["min_door_px"] * fov_h / subtense

    # --- containment, on a slice of the deck that actually has rooms in it ----
    # NOT ON THE WHOLE DECK, and the reason is cost rather than convenience:
    # `containment` is O(rays x triangles) and this deck is 1.54 M triangles.
    # The window is the corridor's OWN measured sight line either side of the
    # worst-structure pose, so nothing a body at its centre can see is outside
    # it, and it carries the rooms and doorways that make the test hard.
    half_win = math.degrees(sight / max(meta["radius_m"], 1e-6))
    centre = worst_struct[1]
    ang = np.degrees(np.arctan2(fr.cy, fr.cx))
    dd = (ang - centre + 180.0) % 360.0 - 180.0
    sel = np.abs(dd) <= half_win
    kt = fr.T[sel]
    om["profile"] = OC.deep_profile(None)
    win = dict(om, start_deg=centre - half_win * 0.5,
               arc_deg=half_win, profile=om["profile"])
    # 12 EYES AND 64 DIRECTIONS, AND THE SPLIT IS NOT ARBITRARY. `containment`
    # is O(rays x triangles) with no acceleration structure and this window is
    # ~150,000 triangles, so the ray budget is real money -- 1,728 rays cost
    # 112 s. Directions are what got cut LAST: `occluders.py` records a control
    # that reads 0 breaches at 64 directions and 2 at 256, because the case it
    # exists to catch is a sliver seen at a slant. Eye positions are the
    # cheaper axis to thin, and 3 angles x 2 lateral x 2 heights still puts an
    # eye against each wall, which is where the worst slant through a doorway
    # is taken from.
    eyes = OC._eye_lattice(win, 3, 2, 2)
    t1 = time.time()
    rays, breach, worst_m, escaped = OC.containment(
        fr.V, kt, ov, ot, om, n_dirs=64, eyes=eyes)
    contain_s = time.time() - t1
    blocked = OC.blocked_fraction(ov, ot, om, n_dirs=256,
                                  eyes=OC._eye_lattice(win, 2, 2, 2))

    # NEGATIVE CONTROL, ON THIS DECK AND NOT ONLY IN occluders.py's SELFTEST.
    # A containment test that reads 0 is worth nothing until the same test on
    # the same geometry is shown reading more than 0, and the case that does it
    # is the one this project already made once: collision geometry, which
    # takes the NEAREST surface, used as an occluder. Deliberately few rays --
    # a control has to fire, not to be exhaustive.
    import collision as _C                                      # noqa: PLC0415
    cv, ctr, cm = _C.corridor_shell(
        schema, profile, sector, ring, degrees=meta["arc_deg"],
        start_deg=meta["start_deg"], radius_m=meta["radius_m"],
        z_offset=meta["z_m"], doors=doors)
    cm["profile"] = om["profile"]
    ctrl = OC.containment(fr.V, kt, cv, ctr, cm, n_dirs=32,
                          eyes=OC._eye_lattice(win, 2, 2, 1))

    # --- three cull units, and only one of them is what Godot does -----------
    # AN EMPTY BUCKET IS NOT A BOX. `group_boxes` returns +/-inf for a bucket
    # nothing landed in, and an inf corner projects to NaN, which compares
    # false against every plane and silently culls itself. Dropping them is not
    # cosmetic: the untagged bucket is empty on this deck and every cell bucket
    # for a group that does not reach that cell is too.
    n_g = len(fr.names)
    key = np.where(fr.gid >= 0, fr.gid, n_g).astype(np.int64)
    kls_all = np.array([klass_of(n) for n in fr.names] + ["structure"])
    lo_g, hi_g = group_boxes(fr.V, fr.T, key, n_g + 1)
    live_g = np.isfinite(lo_g[:, 0])
    corn_g = _corners(lo_g[live_g], hi_g[live_g])
    tri_of_g = np.bincount(key, minlength=n_g + 1)[live_g]
    kls_g = kls_all[live_g]

    # THE CELL GRID IS THE EXPORTER'S, NOT A SECOND ONE INVENTED HERE.
    # `tools/export_scene.cell_of` is the rule `godot/scripts/stream.gd::_split`
    # bakes on and the rule the deck shot now writes its group names with, so
    # all three describe one cut. What this replaced bucketed from the
    # CORRIDOR's `start_deg` -- the right number of cells on a grid rotated off
    # the engine's, which gave a plausible saving for a decomposition nothing
    # ships. It also went through `interior.ring_cells` with the gazetteer's
    # deck NUMBER in the deck INDEX slot; `deck._ring_cells` translates.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_scene as ES                                   # noqa: PLC0415
    plan = ES.deck_cell_plan(sector, ring, deck, schema, profile)
    n_c = max(1, int(plan["cells"]))
    cell = ES.cell_of(fr.V, fr.T, plan["cell_deg"], n_c)
    ckey = key * n_c + cell
    lo_c, hi_c = group_boxes(fr.V, fr.T, ckey, (n_g + 1) * n_c)
    live = np.isfinite(lo_c[:, 0])
    corn_c = _corners(lo_c[live], hi_c[live])
    tri_of_c = np.bincount(ckey, minlength=(n_g + 1) * n_c)[live]
    kls_c = kls_all[np.nonzero(live)[0] // n_c]
    cell_of_bucket = np.nonzero(live)[0] % n_c
    z_lo, z_hi = cell_arc_z(fr, cell, n_c)

    # --- and what of it is in memory at all, which is the bigger half --------
    ship = shipped_streaming(sector, ring, deck)
    radius_m = ship["radius_m"] or plan["sight_line_m"]
    free_m = ship["free_m"] or max(plan["sight_line_m"], plan["cell_length_m"])

    def at(a, hd, pitch=0.0):
        eye, fwd, up = cam_at(a, hd, pitch)
        e, f, u, r = _cam_axes(eye, fwd, up)
        return (e, f, u, r, tv, th)

    def one(a, hd, pitch=0.0, tri=False):
        cam = at(a, hd, pitch)
        Z, skipped = occluder_depth(ov, ot, cam, w, h, near)
        eye0, fwd0, up0 = cam_at(a, hd, pitch)
        planes = _frustum(eye0, fwd0, up0, fov, asp, near, far)
        res = resident_cells(eye0, n_c, plan["cell_deg"], radius_m,
                             z_lo, z_hi, free_m)
        in_mem = res[cell_of_bucket]
        out = {"skipped": skipped, "resident_cells": int(res.sum()),
               "resident_tris": int(tri_of_c[in_mem].sum()),
               "resident_draws": int(in_mem.sum())}
        for tag, corn, ntri, kls, keep in (
                ("inst", corn_g, tri_of_g, kls_g, None),
                ("cell", corn_c, tri_of_c, kls_c, None),
                # THE SHIPPED ROW. Same cull unit as `cell`, restricted to the
                # cells `stream.gd` has actually loaded. Computed off `cell`'s
                # own occlusion result rather than re-running it, so the two
                # rows cannot disagree about which box the occluder hid.
                ("ship", corn_c, tri_of_c, kls_c, in_mem)):
            if tag == "ship":
                vis, occl = out["_cell_vis"] & keep, out["_cell_occ"] & keep
            else:
                vis = boxes_in_frustum(corn, planes)
                occl = boxes_occluded(corn, Z, cam, w, h, near, bias) & vis
                if tag == "cell":
                    out["_cell_vis"], out["_cell_occ"] = vis, occl
            out[tag] = int(ntri[vis].sum())
            out[tag + "_after"] = int(ntri[vis & ~occl].sum())
            out[tag + "_s"] = int(ntri[vis & (kls == "structure")].sum())
            out[tag + "_s_after"] = int(
                ntri[vis & ~occl & (kls == "structure")].sum())
            out[tag + "_draws"] = int(vis.sum())
            out[tag + "_draws_after"] = int((vis & ~occl).sum())
        out.pop("_cell_vis", None)
        out.pop("_cell_occ", None)
        if tri:
            eye, f, u, r, _tv, _th = cam
            px, py, z = _screen(fr.V, eye, f, u, r, tv, th, w, h)
            k = fr.sphere(planes)
            hid = tris_occluded(px, py, z, fr.T, _pool3(Z), w, h, near, bias,
                                OCCLUSION["max_tri_px"])
            out["tri"] = int(k.sum())
            out["tri_after"] = int((k & ~hid).sum())
            out["tri_s"] = int((k & (KL == "structure")).sum())
            out["tri_s_after"] = int(
                (k & ~hid & (KL == "structure")).sum())
        return out

    t2 = time.time()
    here = one(worst_struct[1], worst_struct[2], tri=True)
    there = one(worst_all[1], worst_all[2], tri=True)

    # --- and swept, because one convenient camera is AAA-STANDARD's P2 -------
    lo_deg, arc = meta["start_deg"], meta["arc_deg"]
    st, hd = DECK["stations"], DECK["headings"]
    step = OCCLUSION["sweep_stride"]
    sweep = sweep_ship = res_worst = None
    for i in range(0, st, step):
        a = lo_deg + arc * i / st
        for j in range(0, hd, step):
            m = one(a, 360.0 * j / hd)
            if sweep is None or m["inst_after"] > sweep[0]["inst_after"]:
                sweep = (m, a, 360.0 * j / hd)
            # THE WORST POSE IS NOT THE SAME POSE FOR THE TWO PATHS, and taking
            # the shipped figure at the monolithic path's worst camera would
            # flatter it. Swept separately.
            if sweep_ship is None or m["ship_after"] > sweep_ship[0]["ship_after"]:
                sweep_ship = (m, a, 360.0 * j / hd)
            if res_worst is None or m["resident_tris"] > res_worst[0]:
                res_worst = (m["resident_tris"], m["resident_draws"],
                             m["resident_cells"], a)
    sweep_s = time.time() - t2

    return {"ov": ov, "ot": ot, "meta": om, "build_s": build_s,
            "contain": (rays, breach, worst_m, escaped), "contain_s": contain_s,
            "control": ctrl, "control_tris": len(ctr),
            "blocked": blocked, "here": here, "there": there,
            "sweep": sweep, "sweep_ship": sweep_ship,
            "sweep_s": sweep_s, "poses": len(range(0, st, step))
            * len(range(0, hd, step)),
            "w_needed": w_needed, "subtense": subtense, "sight": sight,
            "cells": n_c, "instances": n_g, "cell_instances": int(live.sum()),
            "half_win": half_win, "eyes": len(eyes), "door_w": door_w,
            "ship": ship, "plan": plan, "radius_m": radius_m, "free_m": free_m,
            "res_worst": res_worst}


# ---------------------------------------------------------------------------
# DRAW CALLS. There was no interior draw-call budget in existence before 3x --
# `exterior_draw_calls: 64` was the only one on the station, and it gates a
# manifest, not a frame.
# ---------------------------------------------------------------------------
#
# DERIVED FROM CPU TIME, WHICH IS WHAT A DRAW CALL COSTS. A draw call is not
# GPU work, it is a submission: state validation, descriptor binding and a
# command-buffer write on the render thread. So the bound is
#
#     draws <= frame_ms * render_thread_share / per_draw_ms
#
# and all three inputs are stated:
#
#   frame_ms            16.667   1440p60 is the target in CLAUDE.md. Not a
#                                choice.
#   render_thread_share 0.25     the render thread also culls, clusters lights,
#                                builds shadow lists and drives the RHI. A
#                                quarter of it for submission is the planning
#                                split; it is an extrapolation (INV-084).
#   per_draw_us         4.0      Vulkan, one uniform set per surface, no
#                                GPU-driven pipeline. Godot 4's Forward+ renderer
#                                is not bindless. 4 us is an extrapolation
#                                (INV-084) and it is the weakest number here.
#
# CROSS-CHECKED AGAINST THIS FILE'S OWN EXTERIOR BUDGET, which was set years of
# sessions ago on a completely different argument: 400,000 triangles in 64 draws
# is 6,250 triangles a draw. The break-even batch implied by the numbers above --
# the batch at which the GPU work of a draw exceeds the CPU cost of submitting
# it, at the 1.2 G tri/s the `BUDGETS` comment's own "20-30 M tri/frame" figure
# implies -- is 4,800 triangles. Two independent derivations, 30% apart. That
# agreement is the reason to trust 4 us at all, and it is printed every run.
#
# THE CAP IS PER FRAME, NOT PER SUBSYSTEM. Exterior, interior, NPCs and effects
# all submit into the same 4.17 ms, so `deck_section` prints the combined figure
# as well as the interior's own.
DRAW = {
    "frame_ms": 1000.0 / 60.0,
    "render_thread_share": 0.25,
    "per_draw_us": 4.0,
    "gpu_tri_per_s": 1.2e9,       # from BUDGETS' own "20-30 M tri/frame @ 60"
}
DRAW["max_per_frame"] = int(DRAW["frame_ms"] * DRAW["render_thread_share"]
                            * 1000.0 / DRAW["per_draw_us"])
DRAW["break_even_batch"] = int(DRAW["gpu_tri_per_s"] * DRAW["per_draw_us"] / 1e6)

# ---------------------------------------------------------------------------
# COLLISION. There was no collision budget at all, on any deck, before 3x.
# ---------------------------------------------------------------------------
#
# TWO BOUNDS, BECAUSE TWO DIFFERENT THINGS CONSTRAIN IT.
#
# (1) TESSELLATION AGAINST TOLERANCE. A collision surface exists to be walked
#     on, and the only correctness requirement on it is that it represent the
#     surface to within the tolerance the walk gate certifies. Triangles spent
#     finer than that buy nothing a player can feel and cost memory, BVH build
#     time and streaming latency. Both collision generators in this project
#     already claim to derive their density this way, so the bound is theirs:
#
#       corridor  `collision.corridor_shell` sizes its angular step from
#                 `MAX_SAG_M`, the sag of a facet inside the true cylinder.
#                 The tolerance a floor is CERTIFIED against is
#                 `collision.STEP_TOLERANCE_M`. Sag scales as the square of the
#                 step, so the allowance is the step count at STEP_TOLERANCE_M.
#       drum      `drum_walk.collision_stride` already picks the coarsest LOD
#                 stride whose height error stays under `drum_walk.STEP_M`.
#                 The bound is that the tile was BUILT at that stride.
#
#     Nothing here is invented: STEP_TOLERANCE_M and STEP_M are the repository's
#     own constants and the ratio is arithmetic.
#
# (2) RESIDENT MEMORY. Godot's `ConcavePolygonShape3D` keeps its faces and BVH
#     in system RAM, and this engine is built `precision=double`, so a Vector3
#     is 24 bytes. Per triangle: 3 vertices x 24 B = 72 B of face array, plus a
#     BVH of about 2N nodes each holding an AABB (2 x Vector3 = 48 B) and three
#     ints, ~64 B a node = ~128 B. About 200 B a triangle. An extrapolation
#     (INV-085); one RSS measurement on target settles it.
#
#     The share is 1% of a 16 GB machine -- 160 MB. 16 GB is the companion
#     figure to CLAUDE.md's stated 12 GB VRAM card and is itself declared.
#     WHAT THIS BOUND IS ACTUALLY FOR is the regression this project has already
#     made once: handing the render mesh to the physics engine. One deck's
#     render mesh is 597,418 triangles -- 119 MB, three quarters of the whole
#     station's allowance, for one deck.
COLLISION = {
    "bytes_per_tri": 200,
    "ram_bytes": 16_000_000_000,
    "ram_share": 0.01,
    "tessellation_ratio": 1.0,
}
COLLISION["max_resident_tris"] = int(COLLISION["ram_bytes"]
                                     * COLLISION["ram_share"]
                                     / COLLISION["bytes_per_tri"])

results = []
FAILED = []


def _glb_primitives(path):
    """`(primitives, of which people)` in a shipped .glb.

    Parses the JSON chunk directly rather than through a library, for the same
    reason every other measurement here is taken off the artefact: a count
    derived from the generator is a second copy of a number, and this gate
    exists precisely because the generator-side count (41 feature groups) and
    the shipped count (1,262 primitives) disagreed by a factor of thirty.
    """
    import struct                                             # noqa: PLC0415
    import json as _json                                      # noqa: PLC0415
    with open(path, "rb") as f:
        data = f.read()
    _magic, _ver, total = struct.unpack("<III", data[:12])
    off = 12
    doc = None
    while off < total:
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        if ctype == 0x4E4F534A:                               # 'JSON'
            doc = _json.loads(data[off + 8:off + 8 + clen])
            break
        off += 8 + clen
    if doc is None:
        raise ValueError("no JSON chunk")
    meshes = doc.get("meshes", [])
    prims = sum(len(m.get("primitives", [])) for m in meshes)
    npc = sum(len(m.get("primitives", [])) for m in meshes
              if "npc_" in m.get("name", "")
              or m.get("name", "").startswith("corridor_"))
    # AND THE SAME COUNT WITH THE CELL SUFFIX STRIPPED, which is what the 600
    # bound has always been about. That bound exists to catch a body emitting
    # its parts unmerged -- twelve primitives an inhabitant instead of one --
    # and spatial submission multiplies the primitive count for a completely
    # different and deliberate reason. Counting distinct BASE names keeps the
    # bound measuring exactly what it measured before the cut; the raw count is
    # printed beside it, because that is the number a draw-call budget cares
    # about and it is gated in the deck frame, per resident cell.
    base = {re.sub(r"_c\d\d$", "", m.get("name", "")) for m in meshes}
    return prims, npc, len(base)


def check(name, value, limit, unit="", note="", when=""):
    """One bound. `when` says what it takes to fail, in units of the content.

    EVERY BOUND HAS TO BE ABLE TO FAIL, and a bound sitting at 12% of its
    allowance looks decorative unless the distance to failure is stated in
    something a person can picture -- "4.4x today's prop density", not "88%
    headroom". CLAUDE.md's rule 2 for layer exits is the same rule at gate
    scale: a criterion that cannot fail on the current content is measuring the
    wrong thing.
    """
    ok = value <= limit
    results.append(ok)
    if not ok:
        FAILED.append(name)
    # A limit of zero is a legitimate bound -- "this must not drift at all" --
    # and it used to divide by zero here, which made the one gate that can only
    # ever be exact the one gate that could not print.
    pct = (value / limit * 100) if limit else (0.0 if value <= 0 else 1000.0)
    bar = "#" * min(66, int(pct / 5)) + "." * (20 - int(min(pct, 100) / 5))
    # Densities are fractions per square metre; rounding them to integers
    # printed "0 / 0" for a gate that was doing real work.
    fmt = ",.3f" if (limit < 10 and unit != "%") else ",.0f"
    print(f"{'PASS' if ok else 'FAIL'}  {name:26s} [{bar}] "
          f"{value:>10{fmt}}{unit} / {limit:{fmt}}{unit}  ({pct:.1f}%)"
          + (f"  {note}" if note else ""))
    if when:
        print(f"{'':32s}{'goes red at' if ok else 'over by'}: {when}")
    return ok


# ---------------------------------------------------------------------------
# The standing frame, measured
# ---------------------------------------------------------------------------

def shipped_camera():
    """The camera `godot/scripts/player.gd` actually creates, read off the file.

    NOT COPIED INTO A CONSTANT. A budget measured at one field of view while the
    build ships another understates by whatever the difference is, and the only
    way that cannot drift is to read the shipped value. `player.gd` sets `near`
    and `far` explicitly and sets no `fov`, so the fov is Godot 4's Camera3D
    default. VERIFIED AGAINST THE ENGINE rather than remembered -- Godot 4.4
    double, headless, `Camera3D.new()` prints `fov=75.0 keep_aspect=1`, and
    keep_aspect 1 is KEEP_HEIGHT, so 75 degrees is VERTICAL. That is wider than
    this file budgets for and the difference is gated, not just reported.
    """
    path = os.path.join(ROOT, "godot/scripts/player.gd")
    out = {"fov_deg": 75.0, "fov_src": "Godot 4 Camera3D default (player.gd "
                                       "sets no fov)",
           "near_m": None, "far_m": None, "eye_m": None, "file": path}
    try:
        src = open(path).read()
    except OSError as exc:                                    # noqa: BLE001
        out["fov_src"] = f"could not read player.gd: {exc}"
        return out
    for key, pat in (("fov_deg", r"_cam\.fov\s*=\s*([0-9.]+)"),
                     ("near_m", r"_cam\.near\s*=\s*([0-9.]+)"),
                     ("far_m", r"_cam\.far\s*=\s*([0-9.]+)"),
                     ("eye_m", r"eye_height_m\s*:\s*float\s*=\s*([0-9.]+)")):
        m = re.search(pat, src)
        if m:
            out[key] = float(m.group(1))
            if key == "fov_deg":
                out["fov_src"] = "player.gd"
    return out


def _frustum(eye, fwd, up, fov_v_deg, aspect, near, far):
    """The six inward-facing planes of a perspective frustum.

    Camera space is x right, y up, z forward. A point is inside when
    |x| <= th*z, |y| <= tv*z and near <= z <= far, which is six half-spaces.
    """
    import numpy as np                                        # noqa: PLC0415
    f = np.asarray(fwd, float); f = f / np.linalg.norm(f)
    u = np.asarray(up, float); u = u - f * float(u @ f); u = u / np.linalg.norm(u)
    r = np.cross(u, f)
    tv = math.tan(math.radians(fov_v_deg) / 2.0)
    th = tv * aspect
    e = np.asarray(eye, float)
    out = []
    for n, off in ((f, -near), (-f, far), (r + th * f, 0.0), (-r + th * f, 0.0),
                   (u + tv * f, 0.0), (-u + tv * f, 0.0)):
        n = np.asarray(n, float)
        n = n / np.linalg.norm(n)
        out.append((n, -float(n @ e) + off))
    return out


class Frustum:
    """Counts triangles of one mesh inside a frustum, over many cameras.

    TWO TESTS, AND THE DIFFERENCE BETWEEN THEM IS REPORTED rather than assumed:

      sphere   conservative -- a triangle survives if its bounding sphere is
               inside every plane. Never rejects a visible triangle, may keep an
               invisible one. Cheap enough to sweep a thousand cameras.
      exact    a triangle survives if, for every plane, at least one of its
               three vertices is inside. This is the standard conservative
               triangle-frustum test and it is what the renderer effectively
               submits.

    The sweep runs `sphere` and the winner is re-counted `exact`. Measured on
    the assembled deck the two differ by 0.2%, which is printed.

    NO OCCLUSION IS APPLIED IN THIS CLASS. That was true of the whole file
    until 4o and both sentences that used to be here are now stale: `godot/`
    does contain an `OccluderInstance3D` and `use_occlusion_culling` is on, and
    `walk.gd` loads a CELL SET rather than one `.glb`, whenever the boot
    manifest names one. What survives is the caveat: everything this class
    counts is submitted whether a wall is in front of it or not, so its figures
    are the pre-occlusion ones. `deck_occlusion` applies the occluder and
    `shipped_streaming` applies residency; the difference between the three is
    printed rather than assumed. On a ring corridor it is large: the far side of
    the ring is inside the frustum from most standing positions.
    """

    def __init__(self, verts, tris, groups):
        import numpy as np                                    # noqa: PLC0415
        self.np = np
        V = np.asarray(verts, float)
        T = np.asarray(tris, np.int32)
        self.V, self.T = V, T
        P = V[T]
        C = P.mean(axis=1)
        self.cx = np.ascontiguousarray(C[:, 0])
        self.cy = np.ascontiguousarray(C[:, 1])
        self.cz = np.ascontiguousarray(C[:, 2])
        self.rad = np.linalg.norm(P - C[:, None, :], axis=2).max(axis=1)
        self._buf = np.empty(len(T))
        self._m = np.empty(len(T), bool)
        # Group ownership, LAST SPAN WINS -- `deck.write_obj` resolves
        # overlapping spans the same way, and `export_gltf.load_obj_groups`
        # then merges by name, so distinct owning names IS the draw-call count.
        # The spans are not a partition: on blue/0/0 they cover 882,134
        # triangle-slots over 597,418 triangles (`wall_assembly` wraps
        # `wall_panel`, `wall_reveal` and the mullions) and leave 1,248
        # uncovered, which the exporter emits as `deck_untagged`.
        self.names = []
        idx = {}
        gid = np.full(len(T), -1, np.int32)
        for n, a, b in groups:
            if n not in idx:
                idx[n] = len(self.names)
                self.names.append(n)
            gid[a:b] = idx[n]
        self.gid = gid
        self.untagged = int((gid < 0).sum())

    def sphere(self, planes):
        np = self.np
        keep = None
        for n, d in planes:
            np.multiply(self.cx, n[0], out=self._buf)
            self._buf += self.cy * n[1]
            self._buf += self.cz * n[2]
            self._buf += d + 0.0
            self._buf += self.rad
            np.greater_equal(self._buf, 0.0, out=self._m)
            keep = self._m.copy() if keep is None else (keep & self._m)
        return keep

    def exact(self, planes):
        np = self.np
        keep = np.ones(len(self.T), bool)
        for n, d in planes:
            keep &= ((self.V @ n + d)[self.T] >= 0.0).any(axis=1)
        return keep

    def draws(self, mask):
        """Draw calls for a selection: distinct group names owning a triangle."""
        return len(set(self.gid[mask].tolist()))


def deck_camera(meta, angle_deg, heading_deg, pitch_deg=0.0, eye_m=1.70):
    """A standing eye on a ring deck, and where it is looking.

    UP IS INWARD. On a spun ring the floor is the inside of a barrel, so a
    body's up is the direction of the axis -- the same sign `player.gd`'s
    `gravity_dir()` uses and the same one `interior.drum_interior` guards. Eye
    height is measured from the COLLISION floor radius, because that is the
    surface a body actually rests on. The shipped spawn is 50 mm proud of it
    (`collision.stand_at`), so a shipped eye is 1.75 m rather than 1.70 m above
    the floor; at these distances that is under a tenth of a percent of the
    count and it is not worth a second lattice.
    """
    import numpy as np                                        # noqa: PLC0415
    a = math.radians(angle_deg)
    rad = meta["floor_r_m"] - eye_m
    eye = np.array([rad * math.cos(a), rad * math.sin(a), meta["z_m"]])
    up = np.array([-math.cos(a), -math.sin(a), 0.0])
    tang = np.array([-math.sin(a), math.cos(a), 0.0])
    axial = np.array([0.0, 0.0, 1.0])
    h, p = math.radians(heading_deg), math.radians(pitch_deg)
    fwd = ((tang * math.cos(h) + axial * math.sin(h)) * math.cos(p)
           + up * math.sin(p))
    return eye, fwd, up


def klass_of(name):
    """structure / fixtures / props / people, from the group name.

    The 60,000 bound has always said "structure only -- props, NPCs and signage
    come out of the rest", and nothing ever measured either half. These are the
    prefixes the generators emit: `dressing.py` writes `dress_*`, `rooms.py`
    writes `prop_*` and `fix_*`, `populace.py` writes `npc_*`. `deck.build_deck`
    prefixes a room's groups with `<key>__`, so the tail is what identifies it.
    Light fittings count as structure because `corridor_section` builds them and
    the 60,000 figure was derived from that same section.
    """
    tail = (name or "untagged").split("__", 1)[-1]
    if tail.startswith(("dress_", "prop_")):
        return "props"
    if tail.startswith("npc_"):
        return "people"
    if tail.startswith("fix_"):
        return "fixtures"
    return "structure"


def deck_section(args):
    """The interior gate: an assembled deck, from a standing eye.

    Returns a dict of the measurements, so `--prove` can re-run the bounds
    against a regression without rebuilding.
    """
    import numpy as np                                        # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import collision as C                                     # noqa: PLC0415
    import deck as D                                          # noqa: PLC0415
    import interior as it                                     # noqa: PLC0415

    sec, ring, dk = DECK["sector"], DECK["ring"], DECK["deck"]
    t0 = time.time()
    schema, profile = it.load()
    verts, tris, groups, stats = D.build_deck(schema, profile, sec, ring, dk)
    meta = stats["collision_meta"]
    build_s = time.time() - t0

    fr = Frustum(verts, tris, groups)
    kls = np.array([klass_of(n) for n in fr.names] + ["structure"])
    KL = kls[np.where(fr.gid >= 0, fr.gid, len(fr.names))]
    resident = {k: int((KL == k).sum())
                for k in ("structure", "fixtures", "props", "people")}

    lo, arc = meta["start_deg"], meta["arc_deg"]
    fov, asp = DECK["fov_v_deg"], DECK["aspect"]
    near, far, eye_m = DECK["near_m"], DECK["far_m"], DECK["eye_m"]

    def planes_at(a, h, p=0.0, f=None):
        return _frustum(*deck_camera(meta, a, h, p, eye_m), f or fov,
                        asp, near, far)

    # ONE PASS, THREE ANSWERS. The worst pose for everything and the worst pose
    # for structure alone are not the same pose -- a view down the arc into two
    # dressed rooms beats one along bare corridor -- so both are tracked. The
    # half-resolution lattice is the SAME sweep sampled every other station and
    # heading, which makes the sampling-error figure free and exact rather than
    # a second run.
    n_st, n_hd = DECK["stations"], DECK["headings"]
    is_struct = (KL == "structure")
    t1 = time.time()
    all_best = st_best = half = None
    for i in range(n_st):
        a = lo + arc * i / n_st
        for j in range(n_hd):
            h = 360.0 * j / n_hd
            k = fr.sphere(planes_at(a, h))
            v = int(k.sum())
            vs = int((k & is_struct).sum())
            if all_best is None or v > all_best[0]:
                all_best = (v, a, h)
            if st_best is None or vs > st_best[0]:
                st_best = (vs, a, h)
            if not (i % 2 or j % 2) and (half is None or v > half[0]):
                half = (v, a, h)
    sweep_s = time.time() - t1

    k_all = fr.exact(planes_at(all_best[1], all_best[2]))
    k_st = fr.exact(planes_at(st_best[1], st_best[2]))
    n_all = int(k_all.sum())
    n_struct = int((KL[k_st] == "structure").sum())
    seen = {k: int((KL[k_all] == k).sum())
            for k in ("structure", "fixtures", "props", "people")}
    draws_frustum = fr.draws(k_all)
    draws_resident = len(set(fr.gid.tolist()))

    cam = shipped_camera()

    print("\nThe standing frame -- one ASSEMBLED deck, not the kit in isolation\n")
    print(f"  subject   {sec}/{ring}/{dk}: {stats['rooms']} rooms over "
          f"{arc:.0f} deg at r = {meta['radius_m']:.2f} m, "
          f"{len(tris):,} triangles, {draws_resident} groups, built in "
          f"{build_s:.0f} s")
    print(f"  camera    eye {eye_m:.2f} m above the collision floor, "
          f"{fov:.0f} deg vertical / "
          f"{2*math.degrees(math.atan(math.tan(math.radians(fov)/2)*asp)):.1f}"
          f" deg horizontal at {asp:.3f}, near {near}, far {far:.0f}")
    print(f"  sweep     {DECK['stations']} stations x {DECK['headings']} "
          f"headings = {DECK['stations']*DECK['headings']:,} poses in "
          f"{sweep_s:.0f} s; worst total at {all_best[1]:.1f} deg heading "
          f"{all_best[2]:.0f}, worst structure at {st_best[1]:.1f} deg "
          f"heading {st_best[2]:.0f}")
    print(f"  sampling  half-resolution lattice finds {half[0]:,} against "
          f"{all_best[0]:,} -- {abs(half[0]-all_best[0])/all_best[0]*100:.1f}% "
          f"lattice error; sphere test over-accepts "
          f"{(all_best[0]-n_all)/max(n_all,1)*100:.2f}% against exact")
    print(f"  resident  structure {resident['structure']:,}  props "
          f"{resident['props']:,}  people {resident['people']:,}  fixtures "
          f"{resident['fixtures']:,}  ({fr.untagged:,} triangles carry no "
          f"group and export as `deck_untagged`)\n")

    # --- occlusion, and whether the build actually gets it -------------------
    chain = occlusion_chain(sec, ring, dk)
    occ = None
    print("\nOcclusion -- an occluder on the corridor's own walls\n")
    if not chain["setting"]:
        print("  NOT MEASURED. The first rung of the ladder is missing, and a "
              "saving the\n  engine cannot reach is not a measurement:")
        for why in chain["why"]:
            print(f"    - {why}")
    else:
        try:
            occ = deck_occlusion(schema, profile, sec, ring, dk, stats, meta,
                                 fr, KL,
                                 lambda a, hh, p=0.0: deck_camera(meta, a, hh,
                                                                  p, eye_m),
                                 all_best, st_best)
        except Exception as exc:                                # noqa: BLE001
            import traceback
            traceback.print_exc()
            check("occlusion measurable", 1, 0, "", f"could not measure: {exc}")
    if occ is not None:
        occ["chain"] = chain

    if occ:
        rays, breach, worst_m, escaped = occ["contain"]
        hh, tt, sw = occ["here"], occ["there"], occ["sweep"]
        print(f"  occluder  {len(occ['ot']):,} triangles for {arc:.0f} deg of "
              f"corridor -- {len(occ['ot'])/max(len(tris),1)*100:.3f}% of the "
              f"deck, built in {occ['build_s']:.0f} s. Apertures cut "
              f"{occ['meta']['aperture_scale']:.3f}x wide at the occluder plane")
        print(f"  buffer    {OCCLUSION['buffer_w']}x{OCCLUSION['buffer_h']}; a "
              f"{occ['door_w']:.2f} m doorway at this corridor's own "
              f"{occ['sight']:.1f} m sight line subtends {occ['subtense']:.2f} "
              f"deg, so {OCCLUSION['min_door_px']:.0f} pixels across it needs "
              f"w >= {occ['w_needed']:.0f}")
        print(f"  contain   {rays:,} rays from {occ['eyes']} standing eyes over "
              f"+/-{occ['half_win']:.1f} deg of the worst-structure pose: "
              f"{breach} breaches, worst {worst_m*1000:.1f} mm, {escaped:,} "
              f"escaped ({occ['contain_s']:.0f} s). Blocks "
              f"{occ['blocked']*100:.1f}% of the sphere")
        cn, cb, cw, _ce = occ["control"]
        print(f"  control   the COLLISION shell ({occ['control_tris']:,} tri, "
              f"nearest surface instead of farthest) used as this deck's "
              f"occluder:\n            {cb:,} of {cn:,} rays hidden, worst "
              f"{cw*1000:.0f} mm of visible surface culled -- so the 0 above is "
              f"a measurement and not a tautology")
        # AND THE FIRST RUNG, SHOWN FAILING, on a copy of the real file with
        # one line taken out. `occlusion_chain` is what decides whether any of
        # this is applied, and a precondition nobody has watched fail is a
        # precondition that does not exist.
        import shutil                                           # noqa: PLC0415
        import tempfile                                         # noqa: PLC0415
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(os.path.join(ROOT, "godot"),
                            os.path.join(td, "godot"),
                            ignore=shutil.ignore_patterns(".godot"))
            gp = os.path.join(td, "godot/project.godot")
            with open(gp) as f:
                src = f.read()
            with open(gp, "w") as f:
                f.write(re.sub(r"^occlusion_culling/use_occlusion_culling.*\n",
                               "", src, flags=re.M))
            off = occlusion_chain(sec, ring, dk, root=td)
        print(f"  control   with `use_occlusion_culling` removed from a copy of "
              f"project.godot,\n            occlusion_chain reports "
              f"setting={off['setting']} applied={off['applied']} and the pass "
              f"is not computed")
        print(f"  swept     {occ['poses']} poses in {occ['sweep_s']:.0f} s; "
              f"worst survivor at {sw[1]:.1f} deg heading {sw[2]:.0f}\n")
        sh = occ["ship"]
        if sh["streamed"]:
            print(f"  SHIPPED   {os.path.basename(sh['cells_path'])}: "
                  f"{sh['n_cells']} cells, resident inside "
                  f"{occ['radius_m']:.1f} m, freed past {occ['free_m']:.1f} m. "
                  f"boot.json names it,\n            main.gd hands it to "
                  f"walk.gd and `_load_streamed` is taken -- so `_load_level`, "
                  f"which loads\n            the monolithic .glb this file used "
                  f"to call 'as shipped', is the FALLBACK path.")
            bad = [k for k, v in sh["rule"].items() if not v]
            print(f"            residency rule read off stream.gd: "
                  + ("all four clauses found"
                     if not bad else f"MISSING {', '.join(bad)}"))
            # THE ARTEFACT AND THE REBUILD, CHECKED AGAINST EACH OTHER. The
            # manifest on disk was written by the engine; the plan beside it is
            # `interior.ring_cells` run now. A gate that reads a committed
            # artefact must be able to rebuild it, and one that only rebuilds it
            # cannot notice the artefact has gone stale.
            pl, mf = occ["plan"], sh["manifest"]
            drift = (abs(mf["cell_deg"] - pl["cell_deg"]) > 1e-6
                     or mf["cells"] != pl["cells"]
                     or abs(mf["radius_m"] - pl["sight_line_m"]) > 0.05
                     or abs(mf["free_m"] - max(pl["sight_line_m"],
                                               pl["cell_length_m"])) > 0.05)
            check("baked cells match the generator", 1 if drift else 0, 0, "",
                  f"manifest {mf['cells']} x {mf['cell_deg']:.1f} deg, radius "
                  f"{mf['radius_m']:.1f} m, free {mf['free_m']:.1f} m; "
                  f"interior.ring_cells says {pl['cells']} x "
                  f"{pl['cell_deg']:.1f} deg, sight {pl['sight_line_m']:.1f} m, "
                  f"cell {pl['cell_length_m']:.1f} m",
                  when="any change to ring_cells without a re-bake -- the "
                       "residency radius the engine uses would then describe a "
                       "grid the generator no longer emits")
            check("stream.gd still says what this file measures",
                  len(bad), 0, " clause(s)",
                  "radius_m = sight_line_m; free_radius_m = max(sight, cell); "
                  "resident within radius_m; freed past free_m",
                  when="any edit to stream.gd's residency rule -- this file "
                       "transcribes it into resident_cells() and a silent "
                       "divergence is a budget measuring a policy nobody runs")
            # AND THE FIRST RUNG SHOWN FAILING, on a copy of the real manifest
            # with `cells_path` emptied -- the state `station/boot.py` writes
            # when no cell set is on disk. Without this the streamed reading is
            # a claim about a file nobody has watched go the other way.
            import shutil                                        # noqa: PLC0415
            import tempfile                                      # noqa: PLC0415
            with tempfile.TemporaryDirectory() as td:
                d = os.path.join(td, "station/generated/scene")
                os.makedirs(d)
                with open(os.path.join(ROOT,
                                       "station/generated/scene/boot.json")) as f:
                    b2 = json.load(f)
                b2["cells_path"] = ""
                b2["cells_why"] = "no cell set on disk"
                with open(os.path.join(d, "boot.json"), "w") as f:
                    json.dump(b2, f)
                off2 = shipped_streaming(sec, ring, dk, root=td)
            print(f"  control   with boot.json's cells_path emptied, "
                  f"shipped_streaming reports streamed={off2['streamed']} and "
                  f"the\n            gated unit falls back to the monolithic "
                  f"row -- so the saving disappears with the build")
        else:
            print("  SHIPPED   the boot manifest names no cell set, so the "
                  "monolithic .glb IS what ships:")
            for whyy in sh["why"]:
                print(f"            - {whyy}")
        print(f"\n  {'cull unit':26s} {'submitted':>12s} {'after occl':>12s} "
              f"{'draws':>7s}   what it is")
        for tag, name, why in (
                ("tri", "triangle", "THE CEILING -- no renderer here culls per "
                                    "triangle"),
                ("inst", "instance, whole ring", "one primitive per OBJ group "
                                                 "-- walk.gd --glb"),
                ("cell", f"instance x {occ['cells']} cells", "the cut, all "
                                                             "cells in memory"),
                ("ship", f"...x {hh['resident_cells']} resident",
                 "WHAT THE SHIPPED BUILD SUBMITS")):
            a0, a1 = hh.get(tag), hh.get(tag + "_after")
            if a0 is None:
                continue
            dr = hh.get(tag + "_draws_after")
            print(f"  {name:26s} {a0:>12,} {a1:>12,} "
                  f"{('' if dr is None else f'{dr:>7,}')}   {why}")
        print(f"\n  structure alone, at the worst-structure pose "
              f"({st_best[1]:.1f} deg / {st_best[2]:.0f}):")
        for tag, name in (("tri", "triangle"), ("inst", "instance, whole ring"),
                          ("cell", f"instance x {occ['cells']} cells"),
                          ("ship", f"...x {hh['resident_cells']} resident")):
            a0, a1 = hh.get(tag + "_s"), hh.get(tag + "_s_after")
            if a0 is None:
                continue
            print(f"  {name:26s} {a0:>12,} {a1:>12,} "
                  f"{a1/INTERIOR['visible_set_tris']:>7.2f}x   of the 60,000 "
                  f"allowance")
        # WHAT THIS PARAGRAPH USED TO SAY, AND WHY IT WAS WRONG. It said "THE
        # INSTANCE ROW IS THE ONE THAT SHIPS AND IT SAVES ALMOST NOTHING",
        # naming the monolithic .glb as the shipped artefact. It is not: the
        # boot manifest names a cell set, `main.gd` hands it to `walk.gd`, and
        # 955 baked `.scn` cells are on disk. So the cut the paragraph asked for
        # was already half built -- in the ENGINE, by `stream.gd::bake`, where
        # no Python gate could see it -- and this file went on pricing the
        # fallback path for four sessions.
        print(f"\n  Instance granularity on the whole ring submits "
              f"{hh['inst']:,} triangles where the\n  per-triangle count is "
              f"{hh['tri']:,} -- {hh['inst']/max(hh['tri'],1):.2f}x, and no "
              f"occluder can touch it, because a\n  corridor group spans "
              f"{arc:.0f} deg and its AABB contains the camera. Cut on the "
              f"{occ['cells']} cells\n  `interior.ring_cells` declares it is "
              f"{hh['cell']:,} ({1-hh['cell']/max(hh['inst'],1):.0%} less); "
              f"with only the {hh['resident_cells']} cells the streamer\n  "
              f"holds in memory it is {hh['ship']:,} "
              f"({1-hh['ship']/max(hh['inst'],1):.0%} less). The draws column "
              f"is the price: {hh['inst_draws_after']:,} -> "
              f"{hh['ship_draws_after']:,}.")
        print(f"  Residency is what makes the cut free. All {occ['cells']} "
              f"cells resident is {hh['cell_draws_after']:,} draws in\n  frame "
              f"and {occ['here']['cell']:,} triangles; the {hh['resident_cells']}"
              f" the streamer keeps is {hh['ship_draws_after']:,} draws. "
              f"Spatial submission\n  without streaming trades triangles for "
              f"draw calls; with it, it costs neither.")
        check("occlusion buffer resolves a doorway",
              OCCLUSION["min_door_px"], OCCLUSION["buffer_w"]
              * occ["subtense"] / (2 * math.degrees(math.atan(
                  math.tan(math.radians(fov) / 2) * asp))), " px",
              f"{OCCLUSION['buffer_w']}x{OCCLUSION['buffer_h']} gives "
              f"{OCCLUSION['buffer_w']*occ['subtense']/(2*math.degrees(math.atan(math.tan(math.radians(fov)/2)*asp))):.2f}"
              f" px across a {occ['door_w']:.2f} m door at {occ['sight']:.1f} m",
              when=f"a sight line past "
                   f"{occ['sight']*OCCLUSION['buffer_w']/occ['w_needed']:.0f} m, "
                   f"or a narrower aperture -- a doorway lost between two pixel "
                   f"centres culls the room behind it, which is a hole in the "
                   f"world rather than a slow frame")
        check("occluder hides nothing visible", breach, 0, " rays",
              f"{rays:,} rays from {occ['eyes']} standing eyes, {escaped:,} "
              f"escaped the modelled slice; worst {worst_m*1000:.1f} mm",
              when="any ray at all -- occluders.py's own controls put the "
                   "collision shell at 1,974 breaches and the ray-measured "
                   "profile this module shipped with at 209")
    if chain["setting"] and not chain["applied"]:
        print("\n  the saving is NOT applied to the bounds below:")
        for why in chain["why"]:
            print(f"    - {why}")

    check("occluder reaches the engine", 0 if chain["applied"] else 1, 0, "",
          ("loaded by " + ", ".join(chain["runtime"])) if chain["applied"]
          else "; ".join(chain["why"])[:180],
          when=("anything that removes the project setting, the emitted "
                "geometry or the script that loads it"
                if chain["applied"] else
                "each rung of occlusion_chain() is a separate fix; the pass "
                "above says what the missing ones are worth"))

    # THE GATED NUMBER IS THE ONE THE SHIPPED PATH SUBMITS, and until 4p it was
    # not. `inst` is the monolithic `.glb` -- `walk.gd::_load_level`, which the
    # shipped scene does not take. `ship` is the same cull unit the engine uses,
    # cut on the cell grid `stream.gd` bakes, restricted to the cells it holds
    # in memory. Both are printed above; the smaller one is not chosen because
    # it is smaller, it is chosen because it is the one that runs.
    #
    # WHEN THE BOOT MANIFEST NAMES NO CELL SET this falls back to `inst`, and
    # the bound goes back to being 4.34x red. The saving is a property of the
    # build, so it has to disappear when the build loses it -- the same ladder
    # `occlusion_chain` applies to the occluder.
    unit, unit_why = "inst", "the monolithic .glb"
    if occ and occ["ship"]["streamed"]:
        unit, unit_why = "ship", (f"{occ['here']['resident_cells']} resident "
                                  f"cells of {occ['cells']}")
    if occ and chain["applied"]:
        n_struct = occ["here"][unit + "_s_after"]
        n_all = (occ["sweep_ship"] if unit == "ship" else
                 occ["sweep"])[0][unit + "_after"]
        draws_frustum = occ["here"][unit + "_draws_after"]
        if unit == "ship":
            draws_resident = occ["res_worst"][1]

    over = n_struct - INTERIOR["visible_set_tris"]
    check("frustum structure", n_struct, INTERIOR["visible_set_tris"], " tri",
          f"was 30,941 from the kit in isolation; {unit_why}"
          + (", occlusion applied" if occ and chain["applied"]
             else ", NO occlusion (see the ladder above)"),
          when=(f"{over:,} tri, {n_struct/INTERIOR['visible_set_tris']:.2f}x. "
                f"The synthetic estimate this replaces read 51.6% of the same "
                f"allowance" if over > 0 else
                f"{-over:,} more triangles of structure in one standing view"))
    check("structure share of frame", n_struct / FRAME_TRIANGLES * 100,
          INTERIOR_FRAME_SHARE * 100, "%",
          "structure only, on the assembled deck",
          when=f"{abs(n_struct/FRAME_TRIANGLES*100 - INTERIOR_FRAME_SHARE*100):.1f}"
               f" points of a 1.2 M frame")
    hdr = DECK["visible_all_tris"] / max(n_all, 1)
    prop_x = ((DECK["visible_all_tris"] - n_all + seen["props"])
              / max(seen["props"], 1))
    # THE COMPOSITION IS OF A DIFFERENT NUMBER FROM THE ONE GATED, and saying
    # so is the point. `seen` is the per-class split of the UNOCCLUDED,
    # WHOLE-RING, per-triangle frustum -- it is what is geometrically in front
    # of the camera. The gated figure is what the engine submits, which is a
    # different cull unit, a different pose and a different residency. Printing
    # the split beside the total without that sentence invited the reading that
    # the four numbers add to the gated one; at the shipped granularity they add
    # to nearly twice it.
    check("frustum, everything", n_all, DECK["visible_all_tris"], " tri",
          f"{unit_why}; the unoccluded whole-ring frustum at the worst-total "
          f"pose is structure {seen['structure']:,} + props {seen['props']:,} "
          f"+ people {seen['people']:,} + fixtures {seen['fixtures']:,} = "
          f"{sum(seen.values()):,}",
          when=f"{hdr:.2f}x today's content in view; props are "
               f"{seen['props']/max(n_all,1)*100:.0f}% of the frame, so at "
               f"today's structure it goes red at {prop_x:.1f}x the prop "
               f"density -- 19.1 primitives/m2 today (docs/judge-3w.md)"
               if n_all <= DECK["visible_all_tris"] else
               f"{n_all - DECK['visible_all_tris']:,} tri")
    check("frustum draw calls", draws_frustum, DRAW["max_per_frame"], "",
          f"{n_all/max(draws_frustum,1):,.0f} tri a draw against a "
          f"{DRAW['break_even_batch']:,} break-even batch",
          when=f"{DRAW['max_per_frame']/max(draws_frustum,1):.1f}x today's "
               f"group count in view"
               if draws_frustum <= DRAW["max_per_frame"] else
               f"{draws_frustum - DRAW['max_per_frame']} draws")
    ext_draws = args.get("exterior_draws", 0)
    check("draw calls, whole frame", draws_resident + ext_draws,
          DRAW["max_per_frame"], "",
          f"{draws_resident} interior resident ({unit_why}) + {ext_draws} "
          f"exterior; culling takes the interior to {draws_frustum}",
          when=f"{DRAW['max_per_frame']/(draws_resident+ext_draws):.1f}x, ie "
               f"{DRAW['max_per_frame']//max(draws_resident,1)} decks resident "
               f"at once"
               if draws_resident + ext_draws <= DRAW["max_per_frame"] else
               f"{draws_resident + ext_draws - DRAW['max_per_frame']} draws")
    # THE RESIDENT SET IS WHAT IS IN MEMORY, NOT WHAT WAS BUILT. This gated
    # `len(tris)` -- the whole assembled deck -- with the note "walk.gd loads
    # one .glb whole, there is no streaming". Both halves of that sentence were
    # out of date: `stream.gd` loads cells, `main.gd` hands it a cell set, and
    # `tools/bake_station.py` has cut all 70 decks. The whole-deck figure is
    # still printed, because it is exactly what the FALLBACK path loads and it
    # is 8.57x this budget.
    res_tris = len(tris)
    res_note = "walk.gd::_load_level loads one .glb whole -- no streaming, no LOD"
    if occ and occ["ship"]["streamed"] and occ["res_worst"]:
        res_tris = occ["res_worst"][0]
        res_note = (f"worst standing position: {occ['res_worst'][2]} of "
                    f"{occ['cells']} cells in memory, {occ['res_worst'][1]:,} "
                    f"instances; the whole deck is {len(tris):,} tri and that "
                    f"is what _load_level would hold")
    check("resident triangles", res_tris, CELLS["resident_tris"], " tri",
          res_note,
          when=f"{abs(res_tris - CELLS['resident_tris']):,} tri, "
               f"{res_tris/CELLS['resident_tris']:.2f}x this file's own "
               f"three-cell resident budget")

    # PITCH IS NOT GATED AND THE REASON IS WORTH STATING. The sweep is at level
    # gaze, which is the pose eye height is defined for and the pose
    # `docs/judge-3w.md` measured, so the two numbers are comparable. But a ring
    # corridor with no occlusion culling puts THE FAR SIDE OF THE RING in the
    # frustum the moment a player tilts their head up, and the cost of that is a
    # property of the missing culling rather than of the content. Gating on it
    # would make a content budget fail for a systems reason. It is printed
    # instead, in full, because the worst of these is what actually has to hold
    # 60 fps.
    worst_pitch = (0, n_all)
    print("\n  what looking up costs, from the worst standing position "
          "(no occlusion applied -- see\n  the ladder above for which rung is "
          "missing):")
    for p in (-30, -15, 0, 15, 30, 45, 60, 90):
        n = int(fr.exact(planes_at(all_best[1], all_best[2], p)).sum())
        if n > worst_pitch[1]:
            worst_pitch = (p, n)
        print(f"     pitch {p:+3d} deg  {n:>9,} tri"
              + ("   <- the gated pose" if p == 0 else "")
              + ("   OVER the allowance" if n > DECK["visible_all_tris"] else ""))
    print(f"     worst {worst_pitch[0]:+d} deg at {worst_pitch[1]:,} tri -- "
          f"{worst_pitch[1]/max(n_all,1):.2f}x the gated pose, "
          f"{worst_pitch[1]/DECK['visible_all_tris']*100:.0f}% of the "
          f"allowance.")
    # THIS LINE USED TO SAY "what closes this is an occluder on the corridor's
    # own walls, not fewer props", and it was a hypothesis with nothing behind
    # it. The section below measures it. The short answer is that an occluder
    # closes it at TRIANGLE granularity and not at the granularity Godot
    # actually culls, so the sentence was half right and named the wrong half.
    print("     These are per-TRIANGLE counts with no occlusion and the whole "
          "deck resident, so they\n     are the ceiling rather than the frame: "
          "the table above prices the same views at the\n     cull unit the "
          "engine uses. What closes the pitched views is the same thing that "
          "closed\n     the level one -- residency, then the cell cut, then the "
          "occluder, in that order of size.")
    n_ship = int(fr.exact(planes_at(all_best[1], all_best[2], 0.0,
                                    cam["fov_deg"])).sum())
    check("shipped camera not wider", cam["fov_deg"], DECK["fov_v_deg"], " deg",
          f"{cam['fov_src']}; at that fov the same pose renders {n_ship:,} tri, "
          f"{n_ship - n_all:+,} against the budgeted camera",
          when=f"any fov above {DECK['fov_v_deg']:.0f} deg vertical"
               if cam["fov_deg"] <= DECK["fov_v_deg"] else
               f"{cam['fov_deg'] - DECK['fov_v_deg']:.0f} deg -- set "
               f"`_cam.fov = {DECK['fov_v_deg']:.1f}` in player.gd, or move "
               f"DECK['fov_v_deg'] to {cam['fov_deg']:.0f} and re-measure")

    # --- collision -----------------------------------------------------------
    t2 = time.time()
    _cv, ct, _cm = D.build_collision(schema, profile, sec, ring, dk, props=True)
    _sv, st, sm = C.corridor_shell(schema, profile, sec, ring, degrees=arc,
                                   start_deg=lo, radius_m=meta["radius_m"],
                                   z_offset=meta["z_m"],
                                   doors=meta.get("doors", ()))
    r = meta["radius_m"]

    def steps_for(tol):
        dt = 2.0 * math.acos(max(-1.0, 1.0 - tol / max(r, 1e-9)))
        return max(4, int(math.ceil(math.radians(arc) / dt)))

    steps_now = sm["steps"]
    steps_allowed = steps_for(C.STEP_TOLERANCE_M)
    ratio = steps_now / steps_allowed
    arc_len = math.radians(arc) * r
    area = arc_len * meta["half_w_m"] * 2.0

    print("\nCollision -- the mesh a body stands on, which is not the one it "
          "looks at\n")
    print(f"  deck      {len(ct):,} triangles ({len(st):,} corridor shell + "
          f"{len(ct)-len(st):,} rooms, vestibules, door panels and prop boxes) "
          f"for {arc_len:,.0f} m of walkable arc, {area:,.0f} m2 of floor, in "
          f"{time.time()-t2:.0f} s")
    print(f"  tolerance MAX_SAG_M = {C.MAX_SAG_M*1000:.0f} mm sizes the shell's "
          f"angular step; STEP_TOLERANCE_M = {C.STEP_TOLERANCE_M*1000:.0f} mm "
          f"is what `floor_steps` certifies a floor against")
    check("corridor shell tessellation", ratio,
          COLLISION["tessellation_ratio"], "x",
          f"{steps_now} steps built, {steps_allowed} needed at "
          f"{C.STEP_TOLERANCE_M*1000:.0f} mm -- sag scales as the square of the "
          f"step",
          when=f"{len(st) - int(len(st)*steps_allowed/steps_now):,} triangles a "
               f"deck bought at a tolerance 5x finer than the one the walk gate "
               f"asserts. Fix: collision.MAX_SAG_M = "
               f"{C.STEP_TOLERANCE_M}" if ratio > 1.0 else
               "any step finer than the certified floor tolerance")

    drum = drum_collision()
    if drum:
        check("drum tile stride", drum["stride_built"], drum["stride_needed"],
              "x", f"tile of {drum['patches']} patches, {drum['tile_tris']:,} "
                   f"tri, {drum['tile_tris']/drum['area']:.4f} tri/m2 -- the "
                   f"next stride up errs {drum['next_err']:.3f} m against a "
                   f"{drum['step_m']:.2f} m step, so stride "
                   f"{drum['stride_needed']} is the coarsest that fits",
              when=f"any tile built finer than the stride "
                   f"`collision_stride()` derives")
        station = drum["drum_lod0"] + drum["ring_decks"]
        check("station collision resident", station,
              COLLISION["max_resident_tris"], " tri",
              f"{drum['ring_decks']:,} ring decks + {drum['drum_lod0']:,} drum "
              f"ground at lod0 = {station*COLLISION['bytes_per_tri']/1e6:.0f} MB "
              f"at {COLLISION['bytes_per_tri']} B/tri",
              when=f"{COLLISION['max_resident_tris']/max(station,1):.2f}x -- one "
                   f"deck's RENDER mesh handed to the physics engine is "
                   f"{len(tris):,} tri, "
                   f"{len(tris)/COLLISION['max_resident_tris']*100:.0f}% of this "
                   f"allowance on its own")
        print(f"  the drum is {drum['drum_lod0']/max(station,1)*100:.0f}% of "
              f"that total and `deck.py --sweep`'s headline omitted it until "
              f"this file measured it -- the sweep called {drum['ring_decks']:,} "
              f"'the whole walkable station' and summed ring decks only. It "
              f"now prints all three numbers.")

    return {
        "occ": occ,
        "frustum_all": n_all, "frustum_structure": n_struct,
        "draws_frustum": draws_frustum, "draws_resident": draws_resident,
        "resident": len(tris), "collision_deck": len(ct),
        "shell_ratio": ratio, "drum": drum, "shell": len(st),
        "corridor_render_tris": stats["corridor_tris"],
    }


def drum_collision():
    """The drum's collision ground, which the ring-deck sweep does not count."""
    try:
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import drum_walk as DW                                # noqa: PLC0415
        stride, ladder = DW.collision_stride()
        rows = DW.places()
        _v, t, _g, m = DW.build(key=rows[0]["key"])
        pa, pz = DW.patch_span_m()
        nxt = next((r for r in ladder if r["stride"] == stride * 2), None)
        # `deck.py --sweep` prints this and it is ring decks only.
        return {
            "stride_built": m["stride"], "stride_needed": stride,
            "patches": len(m["patches"]), "tile_tris": len(t),
            "area": len(m["patches"]) * pa * pz,
            "drum_lod0": m["drum_lod0_triangles"],
            "next_err": nxt["error_m"] if nxt else float("nan"),
            "step_m": DW.STEP_M,
            "ring_decks": RING_DECK_COLLISION_TRIS,
        }
    except Exception as exc:                                  # noqa: BLE001
        check("drum collision measurable", 1, 0, "", f"could not measure: {exc}")
        return None


# `python3 station/deck.py --sweep`. Sixty-six ring decks, and building them all
# takes ~60 s, which is why it is not rebuilt on every budget run -- `--station`
# does rebuild it and fails if this number has drifted.
#
# IT DRIFTED ON PURPOSE AND THE GATE CAUGHT IT, which is what a cached number is
# for. Was 75,642 at 9f13dbf, when `collision.MAX_SAG_M` was 1 mm; tying the sag
# to `STEP_TOLERANCE_M` (5 mm, the tolerance `floor_steps` actually certifies a
# floor against -- INV-085) took every corridor shell to a coarser angular step
# and the station to 35,746, a 53% cut for no change a foot can feel. The shell
# lip rose 0.72 mm -> 1.85 mm against a 5 mm bar, and the deck still walks.
# DRIFTED AGAIN, ON PURPOSE, AND THE GATE CAUGHT IT AGAIN. 35,746 was the
# sweep building ONE z-cluster a deck -- the busiest -- which is 66 corridors.
# Session 3y builds every cluster, 80 of them, because a deck in the gazetteer
# is not a z-slice and the clusters the sweep skipped held C&C, both customs
# halls, the arrival concourse, the cobra bays, Medlab Green, hydroponics and
# both observation domes. 14 more corridors is 19,336 more collision triangles
# and 19 more locations a player can reach.
# AND AGAIN IN 3z, for the third time, which is the gate doing exactly its job.
# The interiors agent added ten locations -- reactor hall, fuel bunkerage,
# coolant gallery, generator hall, heat exchanger hall, comms operations, cargo
# transfer deck, mooring gallery, EVA lock, gunnery control -- and the register
# went 118 -> 128 places over 80 -> 90 z-clusters. Ten more corridors is 3,578
# more collision triangles. NOT a regression: every one of them is floor a
# player can stand on, and the sweep reports 128 of 128 locations reachable.
RING_DECK_COLLISION_TRIS = 58_660


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-deck", action="store_true",
                    help="skip the assembled-deck frame (~40 s). It is the "
                         "only gate here that measures what a player renders, "
                         "so skipping it is a debugging convenience and not a "
                         "shorter way to be green.")
    ap.add_argument("--station", action="store_true",
                    help="rebuild every ring deck's collision (~60 s) and fail "
                         "if RING_DECK_COLLISION_TRIS has drifted")
    ap.add_argument("--prove", action="store_true",
                    help="feed each new bound the regression it exists to "
                         "catch and require it to go red")
    a = ap.parse_args(argv)

    if not os.path.exists(MANIFEST):
        print("no manifest -- run station/generate_hull.py first")
        return 1
    man = json.load(open(MANIFEST))

    tris = man["triangles"]
    draws = len(man["groups"])
    # 24 bytes per vertex un-indexed (position + normal), 3 vertices per triangle.
    bandwidth = tris * 3 * 24 / 1e6
    size = os.path.getsize(GLB) / 1e6 if os.path.exists(GLB) else 0.0

    print("Exterior geometry against the 1440p60 / 12 GB target\n")
    check("triangles", tris, BUDGETS["exterior_triangles"],
          note=f"{man['hull_triangles']:,} hull + {man['component_triangles']:,} components"
               f" + {man.get('greeble_triangles', 0):,} greebles")
    check("draw calls", draws, BUDGETS["exterior_draw_calls"],
          note="one per feature group, before instancing")
    check("vertex bandwidth", bandwidth, BUDGETS["vertex_bandwidth_mb"], " MB",
          "flat-shaded, un-indexed")
    # NOT `if size:`. A missing artefact is the failure this bound exists to
    # catch -- an exterior that did not export is not an exterior under budget --
    # and the old guard turned every such case into a pass. It skipped for
    # sessions because GLB named a file nothing writes.
    if size:
        check("glb on disk", size, BUDGETS["glb_size_mb"], " MB",
              note=os.path.relpath(GLB, ROOT),
              when=f"{BUDGETS['glb_size_mb'] / size:.1f}x today's hull")
    else:
        # 1 against a limit of 0, which is this file's idiom for "the thing
        # being bounded is not there to bound" -- and it FAILS, because a
        # zero-byte exterior passing a size budget is the whole defect.
        check("glb on disk", 1, 0, "",
              f"NOT EXPORTED -- {os.path.relpath(GLB, ROOT)} is missing; "
              f"run tools/export_scene.py --shot exterior")

    greebles = man.get("greeble_triangles", 0)
    if greebles:
        print(f"\nsurface detail: {greebles:,} triangles "
              f"({greebles / BUDGETS['exterior_triangles'] * 100:.0f}% of the triangle "
              f"budget, {greebles / tris * 100:.0f}% of the model) across "
              f"{man.get('greeble_instances', 0):,} fittings in "
              f"{man.get('greeble_assemblies', 0):,} assemblies and "
              f"{man.get('greeble_conduit_runs', 0)} conduit runs")

    print(f"\nheadroom: {BUDGETS['exterior_triangles'] - tris:,} triangles, "
          f"{BUDGETS['exterior_draw_calls'] - draws} draw calls")

    # --- interior: the marginal rate, and then a real frame ------------------
    per_m_straight = None
    try:
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import interior_kit as ik

        # Marginal rate, not total: a corridor's fixed end caps would otherwise
        # make a short sample look far more expensive per metre than a long run.
        # THE ONE KIT MEASUREMENT LEFT IN THIS FILE, and it survives because
        # `interior.ring_arc` builds every walkable metre of the station from
        # this exact call, so it is a property of shipped geometry rather than a
        # proxy for one. The visible-set estimate that used to sit beside it is
        # gone; see the frame measured on an assembled deck below.
        t1 = len(ik.corridor_section(1.0)[1])
        t20 = len(ik.corridor_section(20.0)[1])
        per_m = (t20 - t1) / 19.0
        per_m_straight = per_m

        print("\nInterior kit -- the marginal rate every walkable metre is "
              "built at\n")
        check("corridor rate", per_m, INTERIOR["corridor_tris_per_m"], " tri/m",
              "marginal along a run, interior_kit.corridor_section",
              when=f"{INTERIOR['corridor_tris_per_m']/per_m:.2f}x today's "
                   f"section: 1,270 m of arc x {per_m:.0f} tri/m is "
                   f"{per_m*1270:,.0f} triangles of corridor a deck")
    except Exception as exc:                                  # noqa: BLE001
        check("interior kit measurable", 1, 0, "", f"could not measure: {exc}")

    # --- the standing frame on an assembled deck -----------------------------
    deck_m = None
    if a.no_deck:
        print("\n--no-deck: the assembled-deck frame was NOT measured. Every "
              "interior number\nbelow this line is about a part in isolation, "
              "which is the defect this file had.")
    else:
        try:
            deck_m = deck_section({"exterior_draws": draws})
        except Exception as exc:                              # noqa: BLE001
            import traceback
            traceback.print_exc()
            check("assembled deck measurable", 1, 0, "",
                  f"could not measure: {exc}")

    # --- streaming cells ----------------------------------------------------
    try:
        import interior as it

        schema, profile = it.load()
        # The gate used to price deck 0 of the first deck-stack ring, which is
        # the OUTERMOST deck -- and in Grey that deck is at 471 m and 1.693 g,
        # so it is plant rather than habitat. Charging tankage and machinery at
        # the corridor kit's 285 tri/m put the worst cell at 94.8% of its
        # budget and left the impression that habitat corridors had 5% of
        # headroom for props, signage and NPCs. They have 32%.
        #
        # So the scan runs over every deck and splits on `use`. Both are still
        # gated -- a plant deck is not free, and exempting it is how a subsystem
        # grows without anything noticing -- but they are reported apart, and
        # the plant figure is explicitly a placeholder priced with the wrong
        # kit until plant space has its own.
        worst = {"habitat": None, "plant": None}
        for sec in schema["sectors"]["extents_m"]:
            rings = it.ring_radii(schema, profile, sec)
            for ri, ring in enumerate(rings):
                if ring["kind"] != "deck_stack":
                    continue
                for deck in it.decks_in_ring(schema, profile, sec, ri):
                    di = deck["deck_index"]
                    plan = it.ring_cells(schema, profile, sec, ri, di)
                    cur = worst[deck["use"]]
                    if cur is None or plan["cell_length_m"] > cur[1]["cell_length_m"]:
                        worst[deck["use"]] = (sec, plan, di)

        # THE 3x LABEL HERE SAID "the unit the runtime does not yet load" AND IT
        # STOPPED BEING TRUE IN 4g. `godot/scripts/stream.gd::bake()` cuts a
        # built cluster on this exact grid, `tools/bake_station.py` has run it
        # over all 70 decks -- 955 `.scn` cells on disk -- `station/boot.py`
        # writes the resulting `cells_path` into the boot manifest and
        # `main.gd` hands it to `walk.gd`, which then takes `_load_streamed`.
        # The label survived four sessions because nothing in this file ever
        # asked which path the build takes; `shipped_streaming()` now does, and
        # the standing-frame section above prices what the runtime submits
        # rather than what the fallback would.
        print("\nStreaming cells -- the unit the runtime loads (stream.gd, "
              "955 baked cells)\n")
        for use in ("habitat", "plant"):
            if worst[use] is None:
                continue
            sec, plan, di = worst[use]
            tris = len(it.deck_cell(schema, profile, sec, plan["ring_index"],
                                    di, 0)[1])
            print(f"  worst {use} cell: {sec} {plan['ring']} deck {di} at "
                  f"{plan['gravity_g']:.3f} g -- {plan['cells']} cells of "
                  f"{plan['cell_deg']:.1f} deg, {plan['cell_length_m']:.0f} m, "
                  f"{tris:,} tri")
            note = (f"{plan['circumference_m']:,.0f} m ring would be "
                    f"{tris * plan['cells']:,} whole")
            if use == "plant":
                note += " -- priced with the corridor kit as a placeholder"
            check(f"{use} cell triangles", tris, CELLS["cell_tris"], " tri", note)
            if use == "habitat":
                per_m = tris / plan["cell_length_m"]
                # Resident set: the cell you are in plus both neighbours,
                # because you can see a sight line past a boundary either way.
                check("resident set (3 cells)", tris * 3,
                      CELLS["resident_tris"], " tri",
                      "the cell you are in plus both neighbours")
        against = (f"{per_m / per_m_straight - 1:+.0%} against the straight "
                   f"kit's {per_m_straight:.0f} tri/m" if per_m_straight
                   else "the straight kit did not measure, so there is nothing "
                        "to compare against")
        check("bent corridor rate", per_m, CELLS["bent_tris_per_m"], " tri/m",
              f"{against} -- each bent section carries its own end caps")
    except Exception as exc:
        check("streaming cells measurable", 1, 0, "", f"could not measure: {exc}")

    # --- habitat drum -------------------------------------------------------
    try:
        import interior as it

        schema, profile = it.load()
        drum = it.drum_sector(schema, profile)
        r = it.sector_radius(schema, profile, drum)
        ex = schema["sectors"]["extents_m"][drum]
        length = ex["z1"] - ex["z0"]
        area = 2 * math.pi * r * length

        shell = len(it.drum_interior(schema, profile, drum, arc_deg=360.0,
                                     seg_deg=2.0, z_step=40.0)[1])
        caps = sum(len(it.drum_end_cap(schema, profile, drum, e)[1])
                   for e in ("fore", "aft"))
        trusses = len(it.drum_guideways(schema, profile, drum)[1])
        spokes = len(it.drum_spokes(schema, profile, drum)[1])
        total = shell + caps + trusses + spokes

        print("\nHabitat drum, where everything is visible at once\n")
        check("drum visible set", total, DRUM["visible_set_tris"], " tri",
              f"shell {shell:,} + caps {caps:,} + trusses {trusses:,}"
              f" + spokes {spokes:,}")
        check("drum share of frame", total / FRAME_TRIANGLES * 100,
              DRUM["frame_share"] * 100, "%",
              "no occlusion -- there is no wall to hide behind")
        check("ground surface density", shell / area,
              DRUM["surface_tris_per_m2"], " tri/m2",
              f"{area/1e6:.1f} million m2 of inner surface")
        print(f"\nheadroom: {DRUM['visible_set_tris'] - total:,} triangles for "
              f"ground detail, buildings, trams and vegetation across "
              f"{area/1e6:.1f} million m2 -- "
              f"{(DRUM['visible_set_tris'] - total) / area:.2f} tri/m2. "
              f"The ground is a heightfield, not objects.")
    except Exception as exc:
        check("drum measurable", 1, 0, "", f"could not measure: {exc}")

    # --- WHAT THE ENGINE IS ACTUALLY HANDED -------------------------------
    # THE DRAW-CALL GATE ABOVE MEASURES THE WRONG ARTEFACT and had done since
    # it was written. It counts FEATURE GROUPS in the hull manifest -- 41 of 64
    # -- which is a fine number for the exterior, where a feature group is a
    # lathe or a component. It is not what the exporter writes: `export_gltf`
    # emits one mesh, one node and **one primitive per OBJ group**, so the
    # number a renderer sees is the group count of the shipped file.
    #
    # Measured on an assembled deck the first time anybody looked: **1,262
    # primitives, 1,052 of them people**, against `schedule.NPC_BUDGET`'s
    # `max_draw_calls` of 32. Every inhabitant was twelve primitives because
    # `body.py` tags twelve parts -- which exists so each part binds its own
    # material, and the materials are only ever two or three.
    # `populace._by_material` merges the runs: 376 primitives, 166 of them
    # people, with every material distinction intact.
    #
    # This reads the .glb rather than any Python-side count, because the whole
    # point is that the two disagreed.
    _glb = os.path.join(ROOT, "station/generated/scene/deck/blue_0_0.glb")
    if os.path.exists(_glb):
        try:
            _prims, _npc, _base = _glb_primitives(_glb)
            check("deck primitives shipped", _base,
                  BUDGETS["deck_primitives"], "",
                  f"{_prims:,} primitives over {_base:,} distinct group names "
                  f"({_npc:,} of them people). The bound is on NAMES: a cell "
                  f"cut multiplies primitives on purpose, an unmerged body "
                  f"multiplies names by twelve",
                  when="about 250 more inhabitants on one deck, or a body "
                       "emitting its parts unmerged again (that alone was "
                       "1,262)")
        except Exception as exc:                              # noqa: BLE001
            check("deck primitives measurable", 1, 0, "",
                  f"could not read {os.path.basename(_glb)}: {exc}")

    # --- whole-station collision, opt-in because it costs a minute -----------
    if a.station:
        print("\nWhole-station collision, rebuilt\n")
        import subprocess                                     # noqa: PLC0415
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "station/deck.py"), "--sweep"],
            capture_output=True, text=True, check=False).stdout
        # THIS READS ANOTHER PROGRAM'S PROSE, so it breaks when the prose
        # changes -- and it did, the moment `_sweep`'s headline was corrected to
        # name the drum. It went RED rather than quietly green, which is the
        # only failure direction that is acceptable for a cache check, but a
        # missing match and a real drift must not print the same way: `got = -1`
        # against 35,746 reads as an off-by-one drift and is a parse failure.
        m = re.search(r"([\d,]+) collision triangles across the ring", out)
        if m is None:
            check("ring-deck collision total", 1, 0, "",
                  "deck.py --sweep printed no ring-deck figure this file can "
                  "read -- its headline wording changed and this regex did not",
                  when="any change to `_sweep`'s headline line")
        else:
            got = int(m.group(1).replace(",", ""))
            check("ring-deck collision total",
                  abs(got - RING_DECK_COLLISION_TRIS), 0, " tri",
                  f"deck.py --sweep says {got:,}, this file records "
                  f"{RING_DECK_COLLISION_TRIS:,}",
                  when="any drift at all -- the recorded figure is a cache of a "
                       "60 s sweep and a cache that can go stale silently is a "
                       "second copy of a computed number")

    print("Note: these gate the numbers framerate is a function of. They say nothing\n"
          "about actual framerate, which needs the target hardware.")

    if a.prove:
        prove(deck_m)

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} within budget")
    if failed:
        print("over: " + ", ".join(FAILED))
    return 1 if failed else 0


def prove(m):
    """Feed each new bound the regression it exists to catch. AAA-STANDARD P5.

    "5 -- as 4, plus the gate has been proven to fail. Someone introduced the
    regression and watched the build go red."

    Three of the new bounds are red on the content as it stands, which is the
    strongest form of this proof and needs no help. The rest are green, and a
    green bound is worth exactly as much as the evidence that it can go red. So
    each is re-evaluated against a NAMED regression drawn from real numbers in
    this repository rather than an arbitrary multiplier, and this function fails
    if any of them survives it.
    """
    if not m:
        print("\n--prove needs the deck measurement; do not pass --no-deck")
        return
    print("\nProving the bounds can fail -- each fed the regression it exists "
          "to catch\n")
    drum = m["drum"] or {"drum_lod0": 0}
    cases = [
        ("frustum, everything", m["resident"], DECK["visible_all_tris"],
         "frustum culling switched off: the resident set, which is what "
         "walk.gd hands the renderer before culling"),
        ("frustum draw calls", m["draws_frustum"] * 12, DRAW["max_per_frame"],
         "the corridor's 14 material spans split per bay instead of merged -- "
         "414 identical 3.07 m bays (docs/judge-3w.md), nothing instanced"),
        ("draw calls, whole frame", m["draws_resident"] * 66,
         DRAW["max_per_frame"],
         "all 66 ring decks resident at once, which is what no streaming means"),
        ("station collision resident",
         m["resident"] * 66 + drum["drum_lod0"],
         COLLISION["max_resident_tris"],
         "render meshes handed to the physics engine station-wide -- the "
         "policy behind the regression session 3v made"),
        ("corridor shell tessellation", m["corridor_render_tris"] / m["shell"],
         COLLISION["tessellation_ratio"],
         "the corridor's RENDER mesh used as its collision shell -- session "
         "3v's regression on one deck, which is the case the resident-memory "
         "bound is too loose to catch"),
        ("corridor shell tessellation", 5.0, COLLISION["tessellation_ratio"],
         "MAX_SAG_M dropped to 0.04 mm, a 5x finer shell"),
    ]
    occ = m.get("occ")
    if occ:
        # THE OCCLUSION BOUND, FED THE ONLY REGRESSION THAT MATTERS FOR IT:
        # the geometry emitted and the setting on, but nothing in the engine
        # loading it. That is the state this file is in as it is written, so
        # this row is RED for real rather than by construction -- and it is the
        # row that flips the gated numbers from unoccluded to occluded the
        # moment a script instantiates the resource.
        cn, cb, _cw, _ce = occ["control"]
        cases.append(("occluder hides nothing visible", cb, 0,
                      f"the COLLISION shell used as the occluder, {cn:,} rays "
                      f"-- nearest surface instead of farthest"))
        cases.append(("occluder reaches the engine",
                      0 if occ["chain"]["applied"] else 1, 0,
                      "; ".join(occ["chain"]["why"])[:120] or "all three rungs"))
        # THE TWO BOUNDS THAT MOVED IN 4p, FED THE LOSS OF THE THING THAT MOVED
        # THEM. Both are the same regression -- the boot manifest losing its
        # cells_path, which is one deleted bake away -- and both have to go red
        # for the streamed reading to be worth anything.
        cases.append(("resident triangles", m["resident"],
                      CELLS["resident_tris"],
                      "streaming off: the whole assembled deck, which is what "
                      "walk.gd::_load_level holds"))
        cases.append(("frustum structure", occ["here"]["inst_s_after"],
                      INTERIOR["visible_set_tris"],
                      "streaming off: the monolithic .glb at whole-ring "
                      "instance granularity, occluder applied"))
        mf, pl = occ["ship"].get("manifest"), occ["plan"]
        if mf:
            cases.append(("baked cells match the generator",
                          abs(mf["cells"] - (pl["cells"] + 1)), 0,
                          "one more cell from interior.ring_cells than the "
                          "bake on disk was cut with"))
    bad = 0
    for name, value, limit, why in cases:
        red = value > limit
        bad += 0 if red else 1
        print(f"  {'RED ' if red else 'GREEN'}  {name:26s} "
              f"{value:>10,.0f} / {limit:,.0f}   {why}")
    if bad:
        print(f"  {bad} bound(s) survived their own regression -- that is a "
              f"bound that cannot fail")
    results.append(bad == 0)
    if bad:
        FAILED.append("prove")


if __name__ == "__main__":
    sys.exit(main())
