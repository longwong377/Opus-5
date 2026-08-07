#!/usr/bin/env python3
"""What the game boots into, written down once.

`godot/scripts/main.gd` needs six things to start: a mesh, a collision shell,
the interactables, the cast, a spawn point a body can stand on, and the hour it
is. Until this file existed it read them out of
`station/generated/scene/deck/<deck>_arrival.json` -- the sidecar
`station/arrival.py --build` writes for the player's first ten minutes.

THAT WAS A BORROWED MANIFEST AND IT SHOULD NOT HAVE BEEN. The arrival sequence
is one mode of four; the other three had no reason to depend on it, and deleting
the arrival sidecar would have stopped the game booting at all. Worse, it made
the boot deck a property of a narrative artefact: change which ship the player
arrives on and you change what `godot --path godot` opens.

THE SPAWN IS DERIVED FROM THE FLOOR, NOT COPIED FROM ANYWHERE. This is the point
of the file and it is `station/collision.py`'s rule applied one level up -- that
module measures the corridor's walking profile off the kit by ray casting rather
than writing it down, "so it cannot drift from what it stands in for". A spawn
copied out of another JSON is a second description of where the floor is, and
`arrival.tscn`'s header records what that costs: its first run was handed
`--spawn=0,0,0`, which on a ring deck at radius 211 m is the SPIN AXIS, and the
body fell for two minutes.

So the spawn here is read out of the collision shell itself:

  * the shell's `collision` group is the surface a body walks on;
  * a ring deck is spun, so its floor is the OUTERMOST radius in that group --
    "down" is away from the axis;
  * a body stands just inside it, at `floor_r - STAND_IN_M`;
  * it is placed at the angular and axial MIDDLE of the shell's own extent, so
    it is as far from either end of the built corridor as the geometry allows.

Nothing about that can disagree with the mesh, because it is the mesh.

VALIDATED BY THE GATE THAT USES IT, not by an assertion here: `--check` compares
the derived spawn against the arrival sidecar's independently computed one, and
`station/coldstart.py --g1` stands a real body on it and reports `on_floor` and
the drop. A spawn inside a wall fails that in six seconds.

AND IT NAMES A CELL SET, NOT A MONOLITH -- session 4k, and it is the single most
load-bearing finding in `docs/MASTER-PLAN.md`'s P0.5:

    "`boot.py` emits one `.glb` and `main.gd` never sets `cells_path`, so the
     shipped scene loads ONE DECK and never streams. Every player-facing system
     built before that is fixed is validated on a topology the shipped world
     does not have."

Every part of the machinery already existed and none of it was on the shipped
path. `godot/scripts/stream.gd` bakes and streams cells; `godot/scripts/walk.gd`
takes `--cells=` and loads nothing else when it has one; `tools/bake_station.py`
has baked all 70 decks into 955 cells; `station/walkable.py --stream` drives a
body across them in CI. What was missing was two strings: this file never said
where the cells were, and `main.gd` never set `cells_path`. A player launching
the game got `walk.gd`'s other branch -- one 62 MB `.glb`, loaded whole, with
nothing on the other side of it.

THE CELL SET IS FOUND, NEVER DESCRIBED. This file writes no cell format and cuts
no geometry: `stream.gd::bake()` does both, and `--bake` here shells out to that
same entry point with this deck's paths. A second description of where a cell is
would be `arrival.tscn`'s `--spawn=0,0,0` one level up.

AND THE START CELL IS THE ONE THE SPAWN IS IN. A streamed build primes exactly
one cell before the first frame; a body spawned outside it has nothing under its
feet. `start_cell` reads the containing cell out of the manifest's own arc rows,
by the same predicate `stream.gd::distance_to` uses, so the two cannot disagree
about which cell a point is in.

Run:
    python3 station/boot.py                 # write station/generated/scene/boot.json
    python3 station/boot.py --check         # derive, compare, write nothing
    python3 station/boot.py --deck <stem>   # choose the deck by name
    python3 station/boot.py --bake          # bake the cell set first, if it is
                                            #   missing or no longer describes
                                            #   the deck on disk (needs Godot)
    python3 station/boot.py --gate          # CI: the shipped scene streams
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECK_DIR = os.path.join(ROOT, "station/generated/scene/deck")
# The whole-station export -- `tools/export_station.py` writes here and
# `tools/bake_station.py` cuts these decks into streaming cells.
STATION_DIR = os.path.join(ROOT, "station/generated/scene/station")


def preferred_deck_dir():
    """Where to boot from when the caller names nothing.

    THE STREAMED BUILD WINS WHENEVER IT EXISTS, and this is a DEFAULT rather
    than a flag because the flag was a footgun the moment it existed.

    `scene/deck/` is what `walkable.py` writes as a side effect of a walk test:
    one z-cluster, no corridor crowd, no cell set. `scene/station/` is the real
    export: every cluster of the deck, its actors, its crowd placements and its
    baked cells. For the whole of this project's life `boot.py` could only see
    the first one -- `decks()` enumerates `*_col.obj` and only the walk-test
    path emits that name -- so the packaged game shipped a 39 MB test fixture
    with 83 people in it while the real deck sat in the next directory.

    Adding `--deck-dir` fixed the run that passes it AND LEFT EVERY OTHER
    CALLER WRONG. `tools/bootstrap.py`'s boot step runs `python3
    station/boot.py` bare, so a container recovery would have quietly rewritten
    boot.json back to the walk-test deck and undone the fix with no error
    anywhere. That is this project's signature defect one more time: a repair
    applied to the instance instead of to the rule.

    So the rule: prefer the streamed build, fall back to the walk-test deck,
    and let `--deck-dir` override either. A caller that names nothing gets the
    deck a player should be in.
    """
    try:
        if decks(STATION_DIR):
            return STATION_DIR
    except Exception:                                           # noqa: BLE001
        pass
    return DECK_DIR
OUT = os.path.join(ROOT, "station/generated/scene/boot.json")
# `tools/bake_station.py`'s output -- 70 decks, 955 cells, one `<stem>_cells.json`
# each. Consulted last, because a deck built into `scene/deck/` is the one this
# file's spawn was measured off and a sibling bake of the same NAME is a
# different build of it.
STATION_CELLS = os.path.join(ROOT, "station/generated/scene/station/cells")
# The Godot project `stream.gd` lives in. Only `--bake` uses it.
GODOT_DIR = os.path.join(ROOT, "godot")
# What `main.gd` must set for any of this to reach a player. Asserted by
# `--gate` against the file itself: this repository has shipped finished,
# tested, gated machinery with no caller three times, and the only check that
# catches it is one that reads the caller.
MAIN_GD = os.path.join(ROOT, "godot/scripts/main.gd")

# How far inside the floor surface a body's origin sits, in metres. The deck
# build spawns 50 mm over its shell -- `walkable.py::MAX_DECK_DROP_M`'s comment
# says so in as many words -- and the same clearance is right here: enough that
# the body is unambiguously above the surface, small enough that the settle is
# one physics frame rather than a fall.
STAND_IN_M = 0.05
# The group in the collision shell that is the walkable surface. `collision.py`
# writes the smooth swept shell under this name; `doorpanel_*` are the movable
# leaves and are not floor.
FLOOR_GROUP = "collision"
# How close to the outermost radius still counts as floor, in metres. The shell
# is swept, so its floor is one radius to within the sweep's own tolerance; a
# wall rises inward from it and must not be sampled as ground.
FLOOR_BAND_M = 0.15
# The hour the station starts at when nothing says otherwise. 13:00 is
# `life.gd`'s own Clock default and the middle of the working day, which is when
# the most is happening to look at.
DEFAULT_HOUR = 13.0
# How close a member of the cast has to be for the spawn to be called their
# room rather than the corridor, in metres. A room is bigger than this; the
# point is only to stop "the nearest person on the whole deck" being read as
# "the room you are standing in".
NEAR_ROOM_M = 15.0
# How far the cells' own triangle totals may drift from the deck on disk before
# the set is called stale, as a fraction. ZERO, and that is not a strict choice
# -- `stream.gd::bake()` asserts the cells sum to the source EXACTLY, because it
# assigns whole triangles and never cuts one, and it returns 2 rather than write
# a set that does not. So any difference at all means the cells were baked from
# a different build of this deck, and there is no tolerance to pick.
CELL_DRIFT = 0.0


def _obj_floor_tris(path):
    """The collision shell's floor triangles, as ((x,y,z) x 3).

    TRIANGLES AND NOT LOOSE VERTICES, and the difference is the whole of this
    function's history. The first version averaged the floor's vertices and
    spawned at the mean -- which is a point in the AIR: a corridor is an arc, so
    the centroid of an arc is inside the circle it bends around, and on this
    deck it landed 214 m from any built floor. `coldstart.py --g1` caught it in
    six seconds (`on_floor=false, drop_m=19.456`, radius climbing as the body
    fell outward) and that is exactly why the spawn is validated by standing a
    body on it rather than by an assertion in this file.

    A point ON a triangle of the floor cannot be in the air. That is the fix.

    Parsed out of the .obj rather than the .glb because it is the same file the
    .glb is converted from, it is text, and this needs no engine.
    """
    verts, tris, group = [], [], ""
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("g "):
                group = line[2:].strip()
            elif line.startswith("f ") and group == FLOOR_GROUP:
                idx = [int(t.split("/")[0]) for t in line.split()[1:]]
                pts = [verts[i - 1 if i > 0 else len(verts) + i] for i in idx]
                # Fan-triangulate, so a quad in the shell is two triangles
                # rather than a discarded face.
                for k in range(1, len(pts) - 1):
                    tris.append((pts[0], pts[k], pts[k + 1]))
    return tris


def spawn_from_shell(col_obj):
    """Where a body can stand, read off the collision shell.

    Returns (spawn, detail). Raises if the shell carries no floor group.
    """
    tris = _obj_floor_tris(col_obj)
    if not tris:
        raise SystemExit("boot: %s has no `%s` group -- is it a collision "
                         "shell?" % (col_obj, FLOOR_GROUP))
    floor_r = max(math.hypot(p[0], p[1]) for t in tris for p in t)

    def centre(t):
        return tuple(sum(p[i] for p in t) / 3.0 for i in range(3))

    # A FLOOR TRIANGLE IS ONE WHOSE WHOLE SELF IS AT THE OUTERMOST RADIUS. The
    # shell is a closed tube: its walls and soffit are in the same group, and a
    # triangle with one vertex on the floor and two up the wall is not somewhere
    # to stand.
    floor = [t for t in tris
             if all(floor_r - math.hypot(p[0], p[1]) <= FLOOR_BAND_M
                    for p in t)]
    if not floor:
        raise SystemExit("boot: no floor triangle within %.2f m of r=%.2f in %s"
                         % (FLOOR_BAND_M, floor_r, col_obj))
    mids = [centre(t) for t in floor]
    # The middle of the built arc, circularly -- a corridor that straddles
    # +/-pi has angles at both ends of the range and a plain mean lands on the
    # far side of the ring. This is a TARGET, not the answer: the answer is the
    # real floor triangle nearest it.
    angs = [math.atan2(c[1], c[0]) for c in mids]
    mid_a = math.atan2(sum(math.sin(a) for a in angs) / len(angs),
                       sum(math.cos(a) for a in angs) / len(angs))
    mid_z = (min(c[2] for c in mids) + max(c[2] for c in mids)) / 2.0

    def cost(c):
        da = abs((math.atan2(c[1], c[0]) - mid_a + math.pi)
                 % (2 * math.pi) - math.pi) * floor_r
        return da * da + (c[2] - mid_z) ** 2

    c = min(mids, key=cost)
    # THE ASSERTION THAT WOULD HAVE FIRED ON THE OLD CODE. The first version's
    # spawn was 214 m from the nearest floor triangle -- a point in the air over
    # the middle of the arc -- and nothing here noticed; `coldstart.py` did,
    # after a build and a launch. A derivation that can put a body in space
    # should say so itself, in milliseconds, rather than leave it to the gate.
    away = min(math.dist(c, m) for m in mids)
    if away > 1e-6:
        raise SystemExit("boot: the spawn is not on a floor triangle "
                         "(%.3f m from the nearest)" % away)
    # Stand just inside the surface. Radially, because on a spun deck "down" is
    # outward and the floor's own normal is the inward radial.
    r = math.hypot(c[0], c[1])
    k = (r - STAND_IN_M) / r
    spawn = [c[0] * k, c[1] * k, c[2]]
    return spawn, {
        "floor_r_m": round(floor_r, 4),
        "stand_in_m": STAND_IN_M,
        "on_triangle_r_m": round(r, 4),
        "arc_deg": round(math.degrees(math.atan2(c[1], c[0])) % 360.0, 3),
        "z_m": round(c[2], 3),
        "floor_triangles": len(floor),
        "shell_triangles": len(tris),
    }


def decks(deck_dir=None):
    """Every deck on disk that has both a mesh and a collision shell.

    IT ACCEPTS BOTH NAMING CONVENTIONS, and the cost of not doing so was the
    whole station. `walkable.py` writes `<stem>_col.obj`/`_col.glb`;
    `tools/export_station.py` writes `<stem>_collision.glb`. This function
    looked for the first spelling ONLY, so all 71 exported decks were invisible
    to the file that decides what the game boots into, and the one deck that
    was visible was visible because somebody had hand-made its `_col.obj`.

    A deck is present when it has a render mesh AND a collision shell under
    EITHER spelling. `collision_shell` then hands back a path the caller can
    actually read, deriving the OBJ from the GLB when only the GLB exists.
    """
    dd = deck_dir or preferred_deck_dir()
    out = []
    for g in sorted(glob.glob(os.path.join(dd, "*.glb"))):
        stem = os.path.basename(g)[:-len(".glb")]
        # `crowd_lod2.glb` is a shared body library, not a deck, and the
        # collision spellings are not decks either.
        if stem.startswith("crowd_lod") or stem.endswith(("_col", "_collision")):
            continue
        if (os.path.exists(os.path.join(dd, stem + "_col.obj"))
                or os.path.exists(os.path.join(dd, stem + "_collision.glb"))
                or os.path.exists(os.path.join(dd, stem + "_col.glb"))):
            out.append(stem)
    return out


def collision_shell(stem, deck_dir=None):
    """-> (obj_path, glb_path) for `stem`'s collision shell, both readable.

    `spawn_from_shell` reads named groups out of an OBJ -- it derives the
    player's spawn from the floor triangles, *"measured off the collision
    shell's own floor, never copied"* -- and the whole-station export writes
    only a GLB. Rather than teach this file a second geometry reader or make
    every caller remember a conversion step, the OBJ is DERIVED ON DEMAND from
    the GLB that exists, once, and cached on disk.

    `tools/glb_to_obj.py --collision` does the translation, including the group
    names: the GLB calls the shell `deck_untagged`/`join<z0>_<z1>` and the OBJ
    convention `boot.FLOOR_GROUP` reads is the literal string `collision`.
    """
    dd = deck_dir or preferred_deck_dir()
    obj = os.path.join(dd, stem + "_col.obj")
    glb = os.path.join(dd, stem + "_col.glb")
    src = os.path.join(dd, stem + "_collision.glb")
    if not os.path.exists(glb) and os.path.exists(src):
        glb = src
    if not os.path.exists(obj):
        if not os.path.exists(glb):
            raise SystemExit("boot: %s has no collision shell in %s" % (stem, dd))
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import glb_to_obj as _g2o                               # noqa: PLC0415
        meshes = _g2o.read_glb(glb)
        _g2o.write_obj(obj, meshes, rename=_g2o.collision_group)
    return obj, glb


def _checks():
    """place -> {"need", "name", "why"} for every place that reads a card.

    98 of the register's 129 places. The rung comes from
    `consequence.required_tier` and the reason from `certain_check`, so the
    engine holds no copy of P-05's rule -- only its result.
    """
    try:
        import consequence as cq                                # noqa: PLC0415
        import directory as dr                                  # noqa: PLC0415
    except Exception:
        return {}
    out = {}
    for q in dr.PLACES:
        try:
            ok, why = cq.certain_check(q["key"])
            if not ok:
                continue
            need, _ = cq.required_tier(q["key"])
            out[q["key"]] = {"need": int(need),
                             "name": cq.tier_name(need),
                             "why": str(why)}
        except Exception:
            continue
    return out


def _collapses(rooms, day=1, seed="b5"):
    """One station-day of incidents on THIS deck that put a body on the deck.

    THE JOIN BETWEEN A SIMULATION AND A THING A PLAYER CAN SEE, and it is the
    piece that was missing on both sides at once. `station/incident.py` decides
    380 collapses a day and wrote them into a ledger; `godot/scripts/ragdoll.gd`
    can drop a 16-segment body with the deck's own gravity. Neither knew about
    the other, so the only way to see a ragdoll was to pass `--ragdoll-gate`.
    A capability reachable only from its own gate is this project's signature
    defect one step before it happens.

    Scoped to the rooms this deck actually has, because an incident in a place
    the player cannot walk to is a row nothing will ever read. `--no-collapses`
    on the engine side is the control.
    """
    if not rooms:
        return []
    try:
        import incident as ic                                   # noqa: PLC0415
        return ic.visible_bodies(rooms, day=day, seed=seed)
    except Exception as e:                                      # noqa: BLE001
        # NAMED, NOT SWALLOWED. A bake that silently produced an empty schedule
        # would look exactly like a quiet day on the station.
        print("boot: no collapse schedule -- %s: %s"
              % (type(e).__name__, e), file=sys.stderr)
        return []


def sidecar(stem, suffix, deck_dir=None):
    p = os.path.join(deck_dir or preferred_deck_dir(), stem + suffix)
    return p if os.path.exists(p) else ""


# ---------------------------------------------------------------------------
# THE CELL SET -- found, measured, and named. Never authored.
# ---------------------------------------------------------------------------

def _obj_tris(path):
    """Triangles in an .obj, fan-triangulated exactly as `_obj_floor_tris` is.

    The `.obj` and not the `.glb` for the same reason `_obj_floor_tris` gives:
    it is the file the .glb is converted from, it is text, and this needs no
    engine. Returns -1 when there is no .obj to count, which is a DIFFERENT
    answer from zero and is reported as one.
    """
    if not os.path.exists(path):
        return -1
    n = 0
    with open(path) as f:
        for line in f:
            if line.startswith("f "):
                n += len(line.split()) - 3
    return n


def _describes(stem, man):
    """Is this manifest a cell set for THIS deck?

    THE PREFIX ALONE IS NOT ENOUGH, and the deck on this station that proves it
    is `blue_0_0`: `blue_0_0_z7440_c01` starts with `blue_0_0`, so a plain
    prefix test hands the wrong deck's eleven cells to a boot that measured its
    spawn off a different shell -- 320 m down the axis, where this deck has no
    floor. `_c` is the separator `stream.gd::bake()` writes between the cluster
    stem and the cell index, so `stem + "_c"` cannot match a sibling cluster.
    """
    if not isinstance(man, dict):
        return False
    rows = man.get("cells") or []
    if not rows:
        return False
    src = os.path.basename(str((man.get("source") or {}).get("glb", "")))
    if src and src != stem + ".glb":
        return False
    return all(str(c.get("id", "")).startswith(stem + "_c") for c in rows)


def _cell_candidates(stem, dd):
    """Where a cell set for `stem` can be, best first.

    `<stem>_cells.json` before `cells.json` everywhere, and that ordering is a
    finding rather than a preference: `stream.gd::bake()` writes both, and
    `cells.json` is whichever cluster of a multi-deck bake ran LAST. On this
    tree `scene/deck/cells/cells.json` describes `blue_0_0_z7440` while sitting
    in a directory a reader would take for the station's. The stem-named file
    cannot be overwritten by a sibling; the bare one can, so it is only ever
    reached after `_describes` has agreed it is this deck's.
    """
    out = [os.path.join(dd, "cells_" + stem, stem + "_cells.json"),
           os.path.join(dd, "cells_" + stem, "cells.json"),
           os.path.join(dd, "cells", stem + "_cells.json"),
           os.path.join(dd, "cells", "cells.json")]
    if os.path.abspath(dd) == os.path.abspath(DECK_DIR):
        # The whole-station bake, last. Only for the real deck directory: a
        # fixture deck must not be able to reach the station's own cells and
        # pass on somebody else's geometry.
        out.append(os.path.join(STATION_CELLS, stem + "_cells.json"))
    return out


def cells_for(stem, deck_dir=None, why=None):
    """(path, manifest) of this deck's cell set, or ("", None).

    FRESH BEATS NEAR, AND IT USED TO BE THE OTHER WAY ROUND. This returned the
    first candidate that described the deck by NAME, so a cell set sitting
    beside the deck won however old it was. Measured on this tree in session 4r:
    `scene/deck/cells_blue_0_0/` held 18 cells summing to 735,732 render and
    5,270 collision triangles while the deck beside it had 1,263,904 and 15,166
    -- a set cut from a build two thirds smaller, covering **12.2 m of a 143 m
    deck** -- and `build()` named it as `cells_path` anyway, printing STALE as
    it went. The shipped scene therefore streamed a third of its own floor.

    Location still breaks ties, for the reason `_cell_candidates` gives: a
    sibling bake of the same NAME is a different build of the deck. But a set
    that provably no longer sums to the deck cannot beat one that does.

    `why` collects one line per candidate considered, so a boot that picks
    nothing can say what it looked at rather than only that it failed.
    """
    dd = deck_dir or preferred_deck_dir()
    best = ("", None)
    for p in _cell_candidates(stem, dd):
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                man = json.load(f)
        except (OSError, ValueError) as e:
            if why is not None:
                why.append("%s: unreadable (%s)" % (os.path.relpath(p, ROOT), e))
            continue
        if not _describes(stem, man):
            if why is not None:
                why.append("%s: describes a different deck"
                           % os.path.relpath(p, ROOT))
            continue
        got = cells_describe(stem, man, dd)
        if why is not None:
            why.append("%s: %d cells, %s" % (os.path.relpath(p, ROOT),
                                             got["count"],
                                             "fresh" if got["fresh"]
                                             else got["why"]))
        if got["fresh"]:
            return p, man
        if best[0] == "":
            best = (p, man)
    return best


def cells_describe(stem, man, deck_dir=None):
    """How many cells, and do they still describe the deck on disk?

    A CELL SET THAT NO LONGER SUMS TO ITS DECK IS A DIFFERENT STATION. The bake
    assigns whole triangles and asserts the cells sum to the source exactly, so
    this comparison has no tolerance to argue about -- and it is the general
    form of the lesson this repository already paid for twice: a gate that reads
    a committed artefact must be able to say whether the artefact still
    describes the code. `--bake` is how it is rebuilt.

    Measured on both halves. The COLLISION half is what a body stands on and
    the RENDER half is what it looks at, and they go stale independently: on
    this tree at the time of writing the collision totals agreed exactly (5,270
    = 5,270) while the render mesh had moved by 5,308 triangles, so a
    collision-only check would have called a stale set fresh.
    """
    dd = deck_dir or preferred_deck_dir()
    rows = man.get("cells") or []
    got = {"count": len(rows),
           "tris": sum(int(c.get("tris", 0)) for c in rows),
           "col_tris": sum(int(c.get("col_tris", 0)) for c in rows),
           # DOES THE GRID HAVE AN AXIS IN THE DIRECTION THE STATION IS LONG?
           # Until INV-610 it did not, and nothing anywhere could say so: a set
           # of 18 cells each running the deck's whole 1,253 m read exactly like
           # a set of 18 cells that tile it. `z_band_m` is written by
           # `stream.gd::bake()`; a set baked before it is absent, which is a
           # DIFFERENT answer from zero and is reported as one.
           "z_band_m": float(man.get("z_band_m", -1.0)),
           "z_bands": int(man.get("z_bands", 0)),
           # The z a cell actually spans, biggest first -- the number that made
           # the defect visible once it was printed.
           "z_span_max_m": max([float(c.get("arc", {}).get("z1", 0.0))
                                - float(c.get("arc", {}).get("z0", 0.0))
                                for c in rows] or [0.0]),
           "tris_max": max([int(c.get("tris", 0)) for c in rows] or [0])}
    got["deck_tris"] = _obj_tris(os.path.join(dd, stem + ".obj"))
    got["deck_col_tris"] = _obj_tris(os.path.join(dd, stem + "_col.obj"))
    why = []
    for half, mine, theirs in (("render", got["tris"], got["deck_tris"]),
                               ("collision", got["col_tris"],
                                got["deck_col_tris"])):
        if theirs < 0:
            why.append("%s: no .obj beside the deck to compare against" % half)
            continue
        if abs(mine - theirs) > CELL_DRIFT * max(theirs, 1):
            why.append("%s: cells sum to %d, the deck on disk has %d (%+d)"
                       % (half, mine, theirs, mine - theirs))
    got["fresh"] = not why
    got["why"] = "; ".join(why)
    return got


def start_cell(man, spawn):
    """The index of the cell that CONTAINS `spawn`, or -1.

    THE SAME PREDICATE THE ENGINE USES, read off the manifest's own rows rather
    than recomputed from the cell grid. `stream.gd::distance_to` returns zero
    for an arc cell exactly when the point's angle is in [a0, a1) and its z is
    within [z0, z1], and falls back to the world AABB when a cell has no arc;
    `cell_at` is "the cell whose distance is zero". A second rule here -- even a
    correct one -- would be a second description of where a cell is, and the
    failure mode is silent: the wrong cell primed, and a body standing on a
    floor that has not arrived.
    """
    for c in man.get("cells") or []:
        arc = c.get("arc")
        if arc:
            a = math.degrees(math.atan2(spawn[1], spawn[0])) % 360.0
            if not (float(arc["a0_deg"]) <= a < float(arc["a1_deg"])):
                continue
            if not (float(arc["z0"]) <= spawn[2] <= float(arc["z1"])):
                continue
            return int(c["index"])
        ab = c.get("aabb")
        if not ab:
            continue
        lo, size = ab["pos"], ab["size"]
        if all(lo[i] <= spawn[i] <= lo[i] + size[i] for i in range(3)):
            return int(c["index"])
    return -1


def bake_cells(stem, deck_dir=None, timeout=900):
    """Cut this deck into cells WITH THE EXISTING BAKER. Returns (ok, why).

    Nothing about the cell format, the cell grid or the cut is decided here.
    `godot/scripts/stream.gd::bake()` owns all three -- it reads `cell_deg` out
    of `station/generated/cell_manifest.json`, assigns every triangle whole to
    the cell its centroid falls in, asserts the cells sum to the source, and
    refuses to write a set that does not. This function supplies four paths and
    a deck address, which is exactly what `tools/bake_station.py` supplies for
    all 70 decks; the difference is that this one bakes the ONE cluster the
    shipped scene boots into, beside the deck it was built from.
    """
    dd = deck_dir or preferred_deck_dir()
    glb = os.path.join(dd, stem + ".glb")
    col = os.path.join(dd, stem + "_col.glb")
    for p in (glb, col):
        if not os.path.exists(p):
            return False, "no %s -- run the deck exporter" % os.path.relpath(
                p, ROOT)
    sys.path.insert(0, HERE)
    try:
        import walkable as W                                   # noqa: PLC0415
        godot = W.godot_binary()
    except Exception as e:                                     # noqa: BLE001
        return False, "could not find a Godot binary (%s)" % e
    if godot is None:
        return False, ("no double-precision Godot binary -- run "
                       "`bash tools/build_godot.sh`")
    part = stem.split("_")
    if len(part) < 3:
        return False, "cannot read a deck address out of the stem %r" % stem
    sec, ring, dk = part[0], part[1], part[2]
    # THE REGISTER'S DECK IS A NAME, NOT AN INDEX. `cell_manifest.json`'s
    # deck_table is keyed by index into the ring's stack while the gazetteer
    # carries the numbers the show uses; `tools/bake_station.py` lost 15 of 70
    # bakes to exactly this before it went through `deck.deck_index`.
    try:
        import deck as _D                                      # noqa: PLC0415
        import interior as _I                                  # noqa: PLC0415
        schema, profile = _I.load()
        dk_index = _D.deck_index(schema, profile, sec, int(ring), int(dk))
    except Exception:                                          # noqa: BLE001
        dk_index = int(dk)
    out_dir = os.path.join(dd, "cells_" + stem)
    os.makedirs(out_dir, exist_ok=True)
    cmd = [godot, "--headless", "--path", GODOT_DIR, "res://scenes/walk.tscn",
           "--", "--bake-cells", "--glb=" + glb, "--collision=" + col,
           "--sector=" + sec, "--ring-index=" + str(ring),
           "--deck-index=" + str(dk_index), "--cell-id=" + stem,
           "--cells-out=" + out_dir]
    print("boot: baking %s -> %s" % (stem, os.path.relpath(out_dir, ROOT)))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "the bake timed out after %d s" % timeout
    # THE CELLS ON DISK ARE THE VERDICT, NOT THE EXIT CODE -- `bake_station.py`'s
    # rule, and this repository's most-repeated lesson: a tool that exits 0
    # having written nothing manufactures evidence.
    path, man = cells_for(stem, dd)
    if not path:
        tail = [ln for ln in (r.stderr or r.stdout).splitlines()
                if ln.strip()][-3:]
        return False, "exit %d and no cell set for %s: %s" % (
            r.returncode, stem, " | ".join(tail))
    # THE PLACES SIDECAR, WRITTEN BY THE SECOND BAKE PATH AS WELL AS THE FIRST.
    #
    # `stream.gd`'s `--axial-gate` reads `<stem>_places.json` to know that
    # `obs_dome_2` is a thing a walk can arrive AT rather than a z coordinate
    # it can reach. `tools/bake_station.py` writes it for the whole-station
    # bake. This function is the OTHER bake -- the single cluster the shipped
    # scene boots into -- and a sidecar written by only one of them would be
    # absent on exactly the deck a gate gets pointed at.
    #
    # That is this project's ninth-instance defect in its cheapest form:
    # machinery with no caller on the path that ships. CLAUDE.md's rule from
    # the `bespoke.BESPOKE_GEOMETRY` table is the one being followed here --
    # when a defect is found in one entry, fix the RULE, not the entry. There
    # are two bake paths; both write the sidecar; `wiring.py` can see the
    # import.
    #
    # NOT FATAL IF IT FAILS, and that is deliberate rather than lax: the cells
    # are the artefact this function promises and they are on disk. A deck the
    # register places nothing on legitimately has no sidecar, and turning that
    # into a bake failure would break decks that are fine.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import bake_station as _BS                               # noqa: PLC0415
        pp, npl = _BS.write_places(stem, sec, ring, dk, out_dir)
        side = (", %d register place(s) -> %s" % (npl, os.path.basename(pp))
                if pp else ", no places sidecar (no register place on this "
                           "deck, or no deck_table row)")
    except Exception as e:                                       # noqa: BLE001
        side = ", places sidecar FAILED (%s) -- --axial-gate cannot name " \
               "where a walk arrives without it" % e
    return True, "%d cells in %s%s" % (len(man.get("cells") or []),
                                       os.path.relpath(path, ROOT), side)


def _crowd_ladder(stem, deck_dir=None):
    """-> {"crowd_ladder": "max_m:lod,...", "crowd_glbs": "path,..."}.

    Empty strings when the placement list or the libraries are absent, so a
    deck with no crowd boots exactly as it did. ONLY RUNGS THAT ACTUALLY EXIST
    ON DISK are named: `walk.gd` treats a missing glb as a hard failure of the
    whole library load, so naming a rung that was never baked is worse than
    naming none -- it turns a partial crowd into no crowd.
    """
    dd = deck_dir or preferred_deck_dir()
    if not sidecar(stem, "_crowd.json", dd):
        return {"crowd_ladder": "", "crowd_glbs": ""}
    try:
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import populace as _pop                                 # noqa: PLC0415
        lad = _pop.crowd_ladder()
    except Exception:                                           # noqa: BLE001
        return {"crowd_ladder": "", "crowd_glbs": ""}
    rungs, glbs = [], []
    for hi, lod in lad:
        p = os.path.join(dd, "crowd_lod%d.glb" % lod)
        if not os.path.exists(p):
            continue
        rungs.append("%g:%d" % (hi, lod))
        glbs.append(p)
    if not rungs:
        return {"crowd_ladder": "", "crowd_glbs": ""}
    return {"crowd_ladder": ",".join(rungs), "crowd_glbs": ",".join(glbs)}


def build(stem=None, hour=None, deck_dir=None):
    """The boot manifest for one deck, derived from what is on disk."""
    dd = deck_dir or preferred_deck_dir()
    have = decks(dd)
    if not have:
        raise SystemExit("boot: no built deck in %s -- run the deck exporter"
                         % dd)
    if stem is None:
        # THE FIRST BY NAME, and stated rather than left to a directory listing's
        # order: a boot that opens a different deck depending on the filesystem
        # is a boot nobody can reproduce a bug in.
        stem = sorted(have)[0]
    if stem not in have:
        raise SystemExit("boot: %s is not built (have: %s)"
                         % (stem, ", ".join(have)))
    # Both spellings, and the OBJ derived from the GLB if only the GLB exists.
    col_obj, col_glb = collision_shell(stem, dd)
    spawn, detail = spawn_from_shell(col_obj)
    # WHICH PLACE THE SPAWN IS IN is read off the cast standing in it -- the
    # actors carry their own place key and their own position, so the nearest
    # one names the spot without a second table of room bounds. It is a LABEL
    # for the HUD and the report; nothing depends on it being right.
    at, rooms = "corridor", []
    actors_p = sidecar(stem, "_actors.json", dd)
    if actors_p:
        with open(actors_p) as f:
            cast = json.load(f)
        rooms = sorted({a.get("place", "") for a in cast if a.get("place")})
        if cast:
            near = min(cast, key=lambda a: (a.get("x", 0) - spawn[0]) ** 2
                       + (a.get("y", 0) - spawn[1]) ** 2
                       + (a.get("z", 0) - spawn[2]) ** 2)
            d = math.dist(spawn, [near.get("x", 0), near.get("y", 0),
                                  near.get("z", 0)])
            # ONLY IF IT IS ACTUALLY NEAR. The nearest person on the deck is
            # always SOMEBODY, and calling their room the spawn's room put
            # `in arrival_concourse` on a point 160 m down the corridor from it.
            # On a ring deck the honest answer for "between rooms" is the
            # corridor, which is `ambience.place_at`'s rule and `places.gd`'s.
            if d <= NEAR_ROOM_M:
                at = near.get("place", "corridor")

    # THE CELL SET. `glb` and `collision` stay in the manifest and are NOT
    # replaced: they are what `walk.gd` loads when there is no cell set, and
    # what `arrival.gd` adopts for its own cluster. `cells_path` is the one that
    # decides -- `walk.gd::_ready` loads the monolith only when it is empty.
    looked = []
    cells_p, cman = cells_for(stem, dd, why=looked)
    cells = {"path": cells_p, "count": 0, "start": -1, "fresh": False,
             "z_band_m": -1.0, "z_bands": 0, "z_span_max_m": 0.0,
             "tris_max": 0,
             "why": "no cell set for %s -- run `python3 station/boot.py "
                    "--bake`" % stem}
    if cman is not None:
        cells = cells_describe(stem, cman, dd)
        cells["path"] = cells_p
        cells["start"] = start_cell(cman, spawn)
        if cells["start"] < 0:
            # A SPAWN IN NO CELL IS A FALL, and it must be said here rather than
            # discovered by a body. Exactly one cell is primed before the first
            # frame; if the spawn is not in it, the body drops through geometry
            # that has not arrived and the verdict blames streaming for it.
            cells["fresh"] = False
            cells["why"] = ((cells["why"] + "; ") if cells["why"] else "") + (
                "the spawn %.1f,%.1f,%.1f is in none of the %d cells"
                % (spawn[0], spawn[1], spawn[2], cells["count"]))
    return {
        "deck": stem,
        "glb": os.path.join(dd, stem + ".glb"),
        "collision": col_glb,
        "interact": sidecar(stem, "_interact.json", dd),
        # The deck's occlusion geometry, written by
        # `export_scene.write_deck_occluder`. `sidecar` returns "" when the file
        # is absent, and walk.gd treats "" as "render without it" -- a deck that
        # has never been exported must still be walkable.
        "occluder": sidecar(stem, "_occ.tscn", dd),
        # WHERE A CARD IS READ ON THE WAY IN, and what rung it wants.
        # `consequence.certain_check` is P-05's boundary as a predicate and it
        # had NO RUNTIME CALLER -- visa revocation was reachable in Python and
        # not in the game, which is MASTER-PLAN A4b's whole complaint one level
        # down. Baked rather than queried because the register lives in Python
        # and the reader lives in GDScript; the engine gets a place -> rung map
        # and compares it against the rung already on the purse.
        "checks": _checks(),
        # WHO FALLS DOWN TODAY, AND WHEN, AND WHERE. `incident.RAGDOLL_OF`'s
        # four classes over this deck's own rooms for one station-day -- each
        # row a NAMED resident with a species, not "a body". `life.gd` fires
        # them as the clock passes their hour. See `_collapses`.
        "collapses": _collapses(rooms),
        "actors": actors_p,
        "dialogue": sidecar(stem, "_dialogue.json", dd),
        "crowd": sidecar(stem, "_crowd.json", dd),
        # THE LADDER AND ITS LIBRARIES, because naming only the placement list
        # is instance ten of this project's signature defect and it shipped.
        # `walk.gd::_derived_crowd_glbs` has a fallback that scans the
        # placement list's own directory, and the fallback is not the same
        # answer: it prints
        #
        #     no crowd library was named -- found 3 beside blue_0_0_crowd.json,
        #     ladder 1e9:8 (the coarsest that shipped)
        #
        # and draws all 444 walkers at LOD 8 -- 23,016 vertices for the whole
        # species set -- at every distance including arm's length. The rungs
        # exist precisely so a body two metres away is not the one built for
        # 400 m. `populace.crowd_ladder()` derives them from
        # `schedule.NPC_BUDGET`'s allowances, so it is read rather than
        # restated here.
        **_crowd_ladder(stem, dd),
        # WHAT MAKES THE SHIPPED SCENE STREAM. Empty means it does not, and
        # `cells_why` says which of the two reasons it is -- there is no set, or
        # the set on disk no longer describes this deck.
        "cells_path": cells["path"] if cells["count"] else "",
        "cells_count": cells["count"],
        "cells_start": cells["start"],
        "cells_fresh": cells["fresh"],
        "cells_why": cells["why"],
        # THE SECOND AXIS, ON THE SHIPPED MANIFEST. A build whose cells each run
        # the deck's whole axial extent streams nothing when a player walks
        # along the station, and before this key nothing on the boot path could
        # distinguish that from a build that tiles both ways. INV-610.
        "cells_z_band_m": cells["z_band_m"],
        "cells_z_bands": cells["z_bands"],
        "cells_z_span_max_m": round(cells["z_span_max_m"], 3),
        "cells_tris_max": cells["tris_max"],
        "cells_considered": looked,
        "spawn": [round(v, 4) for v in spawn],
        "spawn_at": at,
        "rooms": rooms,
        "hour": DEFAULT_HOUR if hour is None else float(hour),
        "spawn_derivation": detail,
        # WHICH OF THE TWO BUILDS THIS MANIFEST DESCRIBES, written down rather
        # than inferred from the other paths. The packager stages a directory
        # and `check` looks for the arrival sidecar in one; both used to assume
        # `DECK_DIR`, which is how a manifest naming the streamed build could
        # still be cross-checked against the walk-test deck's arrival file --
        # two different stations, silently compared.
        "deck_dir": dd,
        "note": "Written by station/boot.py. The spawn is measured off the "
                "collision shell's own floor, never copied -- see that file.",
    }


def check(man):
    """Compare the derived spawn with the arrival sidecar's, if there is one.

    A CROSS-CHECK AND NOT A SOURCE. The two numbers are computed by different
    code from different inputs -- this one off the collision shell, the other by
    `arrival.py` out of the deck build -- so agreement is evidence and
    disagreement is a question, but neither file is reading the other.
    """
    p = os.path.join(man.get("deck_dir") or DECK_DIR,
                     man["deck"] + "_arrival.json")
    if not os.path.exists(p):
        print("  no arrival sidecar to cross-check against")
        return True
    with open(p) as f:
        other = json.load(f).get("build", {}).get("spawn")
    if not other:
        return True
    a, b = man["spawn"], other
    d = math.dist(a, b)
    ra, rb = math.hypot(a[0], a[1]), math.hypot(b[0], b[1])
    print("  derived  %8.3f %8.3f %8.3f   r=%.3f" % (a[0], a[1], a[2], ra))
    print("  arrival  %8.3f %8.3f %8.3f   r=%.3f" % (b[0], b[1], b[2], rb))
    print("  they differ by %.3f m along the corridor and %.3f m in radius"
          % (d, abs(ra - rb)))
    # The radius is the part that decides whether a body is standing on the
    # floor; where along the corridor it stands is a choice, not a fact, and the
    # two make it differently on purpose (this one takes the middle of the built
    # arc, arrival takes the hall its sequence starts outside).
    ok = abs(ra - rb) < 0.25
    print("  %s the two agree on where the floor is"
          % ("ok  " if ok else "FAIL"))
    return ok


# ===========================================================================
# THE GATE -- the shipped scene streams, or everything after it is built on
# one deck
# ===========================================================================
#
# IT LIVES HERE BECAUSE THIS IS THE MODULE THAT BUILDS THE THING. CLAUDE.md's
# rule, learned from a doorway that carried four defects at once: the closure
# gate lived in the module that IMPORTED the kit, so the module that built the
# pieces had no way to measure them.
#
# AND IT IS HERMETIC. Every artefact this file reads -- the deck, its shell, its
# cells -- is under `station/generated/scene/`, which is gitignored, so a gate
# that needed one could never run in CI and would join the Godot steps in being
# permanently red. The core assertions are made against a FIXTURE deck built in
# a temporary directory: a shell whose floor this file's own `spawn_from_shell`
# measures, and a cell set in `stream.gd`'s format. No engine, no build, 40 ms,
# and it fails on today's code for the reason it exists to catch.
#
# THE REAL DECK IS STILL CHECKED when it is there, and reported separately, so
# a developer's tree answers the question about the station and CI answers it
# about the contract.

def main_gd_sets_cells(text):
    """Does `main.gd` hand the manifest's `cells_path` to `walk.gd`?

    A SOURCE CHECK, AND IT IS THE HALF THAT WAS ACTUALLY MISSING. Both ends of
    this existed and were tested: `stream.gd` bakes and streams, `walk.gd`
    streams when it is given `--cells=`, `walkable.py --stream` drives a body
    across cell boundaries in CI. `main.gd::_configure_walk` set seven
    properties and none of them was this one, so the shipped scene took the
    other branch and loaded one 62 MB `.glb` whole. Nothing that measures
    geometry can see that; only something that reads the caller can.

    Takes the TEXT rather than the path so the negative control can hand it a
    copy with the line removed.
    """
    # `w.set("cells_path", ...)` with the value coming from the boot manifest.
    # Both halves matter: setting it from a constant would be this file's spawn
    # problem one level up.
    m = re.search(r'set\(\s*"cells_path"\s*,\s*([^\n]*)', text)
    if not m:
        return False, 'no `set("cells_path", ...)` in main.gd'
    if "_boot" not in m.group(1):
        return False, ('main.gd sets cells_path from %r rather than from the '
                       'boot manifest' % m.group(1).strip())
    return True, m.group(0).strip()


def _fixture(dirpath, stem="gate_0_0", cells=2, offset_deg=0.0, bands=1,
             z_len=1.0):
    """A deck and a cell set on disk, small enough to reason about.

    The shell is an arc of floor at a fixed radius: every vertex is at r=R, so
    `spawn_from_shell`'s floor band takes all of it and the spawn lands at the
    angular and axial middle -- which for a 0..30 degree arc is 15 degrees, in
    the first of two 30-degree cells. `offset_deg` slides the CELLS away from
    the shell without moving the shell, which is how the "the spawn is in no
    cell" control is made without authoring an unreachable spawn.

    `bands` cuts the cell set along Z as well, and `z_len` makes the deck long
    enough for that to mean something. With `bands=1` every cell spans the whole
    `z_len` however long it is, which is exactly the shape of the defect
    INV-610 records and is the control the axial checks below run against.
    """
    r, z0, span = 200.0, 100.0, 30.0
    z1 = z0 + z_len
    lines, n = [], 0
    faces = []
    for i in range(31):
        a = math.radians(span * i / 30.0)
        for z in (z0, z1):
            lines.append("v %.6f %.6f %.6f" % (r * math.cos(a),
                                               r * math.sin(a), z))
            n += 1
        if i:
            b = n - 4                      # 1-based: b+1..b+4
            faces.append("f %d %d %d" % (b + 1, b + 2, b + 3))
            faces.append("f %d %d %d" % (b + 2, b + 4, b + 3))
    body = "\n".join(lines) + "\ng %s\n" % FLOOR_GROUP + "\n".join(faces) + "\n"
    with open(os.path.join(dirpath, stem + "_col.obj"), "w") as f:
        f.write(body)
    # BOTH HALVES, because `cells_describe` checks both and the render half is
    # the one that went stale on the real deck. The `.glb` only has to EXIST for
    # `decks()` to see the deck; the `.obj` beside it is what is counted.
    with open(os.path.join(dirpath, stem + ".obj"), "w") as f:
        f.write(body)
    open(os.path.join(dirpath, stem + ".glb"), "w").close()
    rows = []
    n_cell = max(cells, 1) * max(bands, 1)
    per = len(faces) // n_cell
    band_m = z_len / max(bands, 1)
    k = 0
    for i in range(cells):
        a0 = offset_deg + span * i / cells
        for j in range(max(bands, 1)):
            share = per if k < n_cell - 1 else len(faces) - per * (n_cell - 1)
            cid = ("%s_c%02d" % (stem, i) if bands <= 1
                   else "%s_c%02dz%02d" % (stem, i, j))
            rows.append({
                "id": cid, "index": k,
                "mesh": cid + ".scn",
                "collision": cid + "_col.scn",
                "arc": {"r_m": r, "a0_deg": a0, "a1_deg": a0 + span / cells,
                        "z0": z0 + j * band_m - 0.5,
                        "z1": z0 + (j + 1) * band_m + 0.5},
                "aabb": {"pos": [-r, -r, z0], "size": [2 * r, 2 * r, z1 - z0]},
                "tris": share,
                "col_tris": share,
                "groups": 1,
                "spawn": [r * math.cos(math.radians(a0 + 1.0)),
                          r * math.sin(math.radians(a0 + 1.0)),
                          z0 + (j + 0.5) * band_m],
            })
            k += 1
    out = os.path.join(dirpath, "cells_" + stem)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, stem + "_cells.json"), "w") as f:
        json.dump({"version": 1, "kind": "ring", "cell_deg": span / cells,
                   "z_band_m": (0.0 if bands <= 1 else band_m),
                   "z_bands": max(bands, 1),
                   "written_by": "station/boot.py::_fixture (gate)",
                   "source": {"glb": os.path.join(dirpath, stem + ".glb")},
                   "cells": rows}, f)
    return stem


def gate():
    """Assert the shipped scene streams. Returns 0 or 1.

    Four things, each with a control that must FAIL. The bar this repository
    keeps paying for is not "does the check pass" but "can it fail on the
    content in front of it" -- so every subject below is run again with one
    thing removed, and a control that passes is itself a failure.
    """
    print("\nDOES THE SHIPPED SCENE STREAM?\n")
    bad = []

    def say(ok, what, detail=""):
        print("  %s  %s%s" % ("PASS" if ok else "FAIL", what,
                              ("  -- " + detail) if detail else ""))
        if not ok:
            bad.append(what)

    # -- 1. the caller ------------------------------------------------------
    src = open(MAIN_GD).read()
    ok, why = main_gd_sets_cells(src)
    say(ok, "main.gd hands the boot manifest's cells_path to walk.gd", why)
    cut = re.sub(r'.*set\(\s*"cells_path".*\n', "", src)
    cok, _ = main_gd_sets_cells(cut)
    say(not cok, "CONTROL: with that line removed the check fails",
        "it passed -- the check is not reading what it says it reads"
        if cok else "fails, as it must")

    # -- 2. the manifest, on a fixture nobody has to build -------------------
    with tempfile.TemporaryDirectory() as d:
        stem = _fixture(d, cells=2)
        man = build(stem, deck_dir=d)
        say(bool(man.get("cells_path")),
            "boot.build() names a cells_path",
            man.get("cells_path") or man.get("cells_why", "empty"))
        say(os.path.exists(man.get("cells_path") or ""),
            "the cells_path it names exists on disk")
        say(int(man.get("cells_count", 0)) > 1,
            "it names MORE THAN ONE cell",
            "%d cells" % man.get("cells_count", 0))
        say(int(man.get("cells_start", -1)) >= 0,
            "the spawn is inside one of them",
            "cell %d" % man.get("cells_start", -1))
        say(bool(man.get("cells_fresh")),
            "the cells still sum to the deck they were cut from",
            man.get("cells_why") or "exactly")

    # -- 2b. THE SECOND AXIS. INV-610 ---------------------------------------
    #
    # A CELL THAT RUNS THE DECK'S WHOLE LENGTH STREAMS NOTHING ALONG IT, and no
    # check anywhere could tell that apart from a grid that tiles both ways --
    # both give the same cell COUNT, the same triangle total and the same
    # "boot.build() names a cells_path". Measured on this tree before the fix:
    # `blue_0_0` baked whole came back as 18 cells each spanning z
    # 6896.85..8005.41, the biggest carrying 582,792 triangles, which is 3.24x
    # the entire resident allowance in ONE cell -- and the only route between
    # its z-clusters, the 89 deg axial spine, lies inside one of them, so a
    # 340 m walk from the docking bays to customs performed zero loads and zero
    # frees. The check is on the SPAN, because that is the thing that was wrong.
    with tempfile.TemporaryDirectory() as d:
        stem = _fixture(d, cells=2, bands=3, z_len=300.0)
        man = build(stem, deck_dir=d)
        say(int(man.get("cells_z_bands", 0)) > 1,
            "the cell grid has an axis along the station, not only round it",
            "%d bands of %.1f m" % (man.get("cells_z_bands", 0),
                                    man.get("cells_z_band_m", -1.0)))
        say(0.0 < man.get("cells_z_span_max_m", 0.0) < 300.0,
            "no cell runs the deck's whole axial extent",
            "longest cell spans %.1f m of a %.1f m deck"
            % (man.get("cells_z_span_max_m", 0.0), 300.0))
        say(int(man.get("cells_start", -1)) >= 0,
            "the spawn is inside one of the banded cells",
            "cell %d" % man.get("cells_start", -1))
    with tempfile.TemporaryDirectory() as d:
        # THE SAME DECK WITH ONE BAND -- the grid as it was.
        stem = _fixture(d, cells=2, bands=1, z_len=300.0)
        m = build(stem, deck_dir=d)
        say(not (0.0 < m.get("cells_z_span_max_m", 0.0) < 300.0),
            "CONTROL: with one band the span check fails on the same deck",
            "longest cell spans %.1f m of a %.1f m deck -- the whole thing"
            % (m.get("cells_z_span_max_m", 0.0), 300.0))
        say(int(m.get("cells_z_bands", 0)) <= 1,
            "CONTROL: and it is reported as a one-dimensional grid",
            "%d band(s)" % m.get("cells_z_bands", 0))

    # -- 2c. FRESH BEATS NEAR -----------------------------------------------
    #
    # Two candidate sets for one deck, the near one stale and the far one not.
    # Before this rule the near one won and `build()` shipped it while printing
    # STALE, which is what `scene/deck/cells_blue_0_0` was doing on this tree:
    # 12.2 m of a 143 m deck.
    with tempfile.TemporaryDirectory() as d:
        stem = _fixture(d, cells=2, bands=3, z_len=300.0)
        good = os.path.join(d, "cells_" + stem, stem + "_cells.json")
        with open(good) as f:
            fresh_man = json.load(f)
        stale = json.loads(json.dumps(fresh_man))
        for c in stale["cells"]:
            c["tris"] = int(c["tris"]) // 3            # a smaller, older build
        near = os.path.join(d, "cells", stem + "_cells.json")
        os.makedirs(os.path.dirname(near), exist_ok=True)
        # `_cell_candidates` looks in `cells_<stem>/` BEFORE `cells/`, so to test
        # the tie-break the stale one has to be the one that is looked at first.
        with open(good) as f:
            keep = f.read()
        with open(good, "w") as f:
            json.dump(stale, f)
        with open(near, "w") as f:
            f.write(keep)
        m = build(stem, deck_dir=d)
        say(bool(m.get("cells_fresh")),
            "a FRESH cell set beats a nearer stale one",
            os.path.basename(os.path.dirname(m.get("cells_path", ""))) or "none")
        say(len(m.get("cells_considered", [])) >= 2,
            "and every candidate it looked at is named",
            "; ".join(m.get("cells_considered", []))[:120])

    # -- 3. the controls, each removing one thing ---------------------------
    with tempfile.TemporaryDirectory() as d:
        stem = _fixture(d, cells=2)
        import shutil                                          # noqa: PLC0415
        shutil.rmtree(os.path.join(d, "cells_" + stem))
        m = build(stem, deck_dir=d)
        say(not m.get("cells_path"),
            "CONTROL: with no cell set on disk there is no cells_path",
            m.get("cells_why", ""))
    with tempfile.TemporaryDirectory() as d:
        stem = _fixture(d, cells=1)
        m = build(stem, deck_dir=d)
        say(int(m.get("cells_count", 0)) == 1,
            "CONTROL: a one-cell set is reported as one cell, not as streaming",
            "%d" % m.get("cells_count", 0))
    with tempfile.TemporaryDirectory() as d:
        # The cells moved 180 degrees round the ring, the shell did not.
        stem = _fixture(d, cells=2, offset_deg=180.0)
        m = build(stem, deck_dir=d)
        say(int(m.get("cells_start", 0)) < 0 and not m.get("cells_fresh"),
            "CONTROL: a spawn in none of the cells is caught here, not by a "
            "falling body", m.get("cells_why", ""))

    # -- 4. the real deck, when there is one --------------------------------
    print()
    have = decks()
    if not have:
        print("  the built station is not on disk (station/generated/scene/ is "
              "gitignored), so the four checks above are the whole gate here. "
              "On a tree with a built deck this also reports that deck's own "
              "cell set -- run `python3 station/deck.py --deck blue/0/0` then "
              "`python3 station/boot.py --gate`.")
    else:
        man = build()
        n, s = man["cells_count"], man["cells_start"]
        print("  the real deck: %s -- %d cells, start cell %d, %s"
              % (man["deck"], n, s,
                 "fresh" if man["cells_fresh"] else man["cells_why"]))
        # REPORTED, NOT ASSERTED, and the line above says which. The fixture
        # half is the contract and it is hermetic; whether THIS tree's cells
        # have been re-baked since its deck was rebuilt is a property of the
        # tree, and failing CI for it would be failing for the absence of a
        # 62 MB artefact nobody commits.
        if n <= 1 or s < 0:
            print("  ...which would boot MONOLITHIC. `python3 station/boot.py "
                  "--bake` cuts it.")

    print("\n  %s\n" % ("the shipped scene streams" if not bad
                        else "%d failed: %s" % (len(bad), "; ".join(bad))))
    return 1 if bad else 0


def axial_gate(stem=None, extra=(), timeout=1500):
    """Run `stream.gd --axial-gate` on a deck that HAS a cell set. (rc, why).

    WHY THE DRIVER IS HERE. The gate itself is 400 lines of GDScript inside
    `stream.gd` and it needs four things a caller must not have to know: a
    Godot binary, the `res://scenes/stream_gate.tscn` entry point, an absolute
    path to a cells manifest, and a places sidecar beside it. `bake_cells`
    above already assembles the first three for the bake, off the same two
    helpers. A gate whose invocation lives only in a session's shell history
    is a gate nobody runs -- which is the failure this whole file's `--gate`
    exists to prevent, one level out.

    IT FINDS THE CELLS IN BOTH LOCATIONS, through `cells_for`, which is the
    function that already knows there are two: `scene/deck/cells_<stem>/` for
    the single-cluster bake the shipped scene boots into, and
    `scene/station/cells/` for the whole-station one. `tools/bootstrap.py` was
    blind to the second until this session and reported a 70-deck bake as "no
    cell set at all"; a driver that could only see one of them would be the
    same defect wearing a different hat.

    THE SIDECAR IS WRITTEN IF ABSENT, and that is not the gate marking its own
    homework: `write_places` reads the REGISTER, not the mesh, so it cannot
    make a failing walk pass -- it can only make the difference between the
    gate naming `obs_dome_2` and the gate refusing to run. A cell set baked
    before this session has no sidecar and there is no reason to make a human
    re-bake 266 MB of geometry to get a 4 KB JSON file.
    """
    dd = DECK_DIR
    cands = []
    if stem:
        cands = [stem]
    else:
        # Every deck with a cell set in either location, the boot deck first.
        seen = set()
        # THE BOOT DECK FIRST, BUT ONLY IF THERE IS ONE. `build()` exits the
        # process when `scene/deck/` holds no deck -- correct for its own
        # callers and fatal here, where a cell set in the OTHER location is a
        # perfectly good subject. Caught as BaseException on purpose: the exit
        # is a `SystemExit`, which `except Exception` does not see, and the
        # first run of this driver died on exactly that with the deck sitting
        # baked on disk two directories away.
        if glob.glob(os.path.join(dd, "*.glb")):
            try:
                seen.add(build()["deck"])
            except BaseException:                                # noqa: BLE001
                pass
        for p in sorted(glob.glob(os.path.join(dd, "cells_*"))):
            seen.add(os.path.basename(p)[len("cells_"):])
        for p in sorted(glob.glob(os.path.join(STATION_CELLS,
                                               "*_cells.json"))):
            seen.add(os.path.basename(p)[:-len("_cells.json")])
        cands = sorted(seen)
    # EVERY DECK WITH A CELL SET, NOT THE FIRST ONE. The version before this
    # `break`-ed on the first candidate and the review named the consequence
    # exactly: the gate tested one deck of the 71 the register addresses, and
    # said so nowhere. On this container that is the same run either way --
    # ONE deck is baked -- and the difference matters the moment a full bake
    # lands, which is precisely when a gate that quietly tests 1/71 would be
    # read as testing the station. The denominator is printed whether it is 1
    # or 71, because R5's own open question is which denominator is intended
    # and this driver must not answer it by omission.
    runs = []
    for s in cands:
        p, _m = cells_for(s, dd)
        if p:
            runs.append((s, p))
    if not runs:
        return 2, _cannot_run(
            "no deck on disk has a cell set. Bake one:\n"
            "    python3 tools/export_station.py --max-decks 1\n"
            "    python3 tools/bake_station.py --max-decks 1")
    print("boot: axial gate over %d deck(s) with a cell set, of %d candidate "
          "deck stem(s) on disk: %s"
          % (len(runs), len(cands), ", ".join(s for s, _ in runs)))
    sys.path.insert(0, HERE)
    try:
        import walkable as W                                      # noqa: PLC0415
        godot = W.godot_binary()
    except Exception as e:                                        # noqa: BLE001
        return 2, _cannot_run("could not find a Godot binary (%s)" % e)
    if godot is None:
        return 2, _cannot_run("no double-precision Godot binary -- "
                              "`bash tools/build_godot.sh`")
    bad, good = [], []
    for picked, man_p in runs:
        rc, why = _axial_run_one(picked, man_p, godot, extra, timeout)
        (good if rc == 0 else bad).append("%s (%s)" % (picked, why))
    if bad:
        return 1, ("%d of %d deck(s) FAILED: %s%s"
                   % (len(bad), len(runs), "; ".join(bad),
                      ("; passed: " + ", ".join(good)) if good else ""))
    return 0, "PASS on %d of %d deck(s) with a cell set: %s" % (
        len(good), len(runs), ", ".join(s for s, _ in runs))


def _cannot_run(why):
    """`--axial-gate` could not be attempted at all. Says so in one grep-able
    line, and the line exists because the alternative is worse than either
    outcome it sits between.

    THE GATE NEEDS TWO THINGS CI DOES NOT HAVE: a Godot binary and a baked cell
    set, and `station/generated/` is gitignored precisely so that a hosted run
    never carries 266 MB of geometry. So a CI step running this can only ever
    report "could not run" -- and the review's own recommendation was to add
    that step. Following it literally, with no state of its own, gives a choice
    between two lies: exit 0, and a green tick means "the walk was never
    attempted"; exit 1, and the job is permanently red for an environment fact
    while `tools/bootstrap.py --check` already reports that fact honestly and
    cheaply.

    The third answer is a NAMED THIRD STATE. `AXIALGATE state=CANNOT-RUN` is
    printed whichever exit code the caller asked for, so no reader of a log can
    mistake it for a walk that happened, and `--allow-unbaked` maps ONLY this
    state to 0 -- a walk that ran and failed still exits 1 under it. That is
    the distinction CLAUDE.md's session-4e lesson is about: the honest red stays
    red and stops blinding the answers behind it.
    """
    print("AXIALGATE state=CANNOT-RUN reason=%s" % why.splitlines()[0])
    return "CANNOT RUN -- " + why


def _axial_run_one(picked, man_p, godot, extra, timeout):
    """One deck's axial walk. (rc, why). Split out of `axial_gate` so that
    driver can loop; everything here was already in it."""
    part = picked.split("_")
    if len(part) >= 3:
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        try:
            import bake_station as _BS                           # noqa: PLC0415
            side = os.path.join(os.path.dirname(man_p),
                                picked + "_places.json")
            if not os.path.exists(side):
                pp, npl = _BS.write_places(picked, part[0], part[1], part[2],
                                           os.path.dirname(man_p))
                print("boot: wrote the missing places sidecar -- %d place(s)"
                      % npl if pp else "boot: no places sidecar could be "
                      "written for %s" % picked)
        except Exception as e:                                   # noqa: BLE001
            print("boot: could not write a places sidecar (%s)" % e)
    cmd = [godot, "--headless", "--path", GODOT_DIR,
           "res://scenes/stream_gate.tscn", "--", "--axial-gate",
           "--cells=" + os.path.abspath(man_p)] + list(extra)
    print("boot: axial gate on %s -- %s\n     %s"
          % (picked, os.path.relpath(man_p, ROOT), " ".join(cmd[-3:])))
    env = dict(os.environ)
    # THE RENDERER MUST SAY WHICH ONE IT IS. CLAUDE.md's most expensive
    # environment lesson: a tool that silently substitutes a lesser mode and
    # exits 0 manufactures evidence. This gate is headless and never rasters,
    # so the ICD only has to exist for the engine to start -- but it is named
    # here rather than left to the caller's shell, so a run from CI and a run
    # from a session are the same run.
    env.setdefault("VK_ICD_FILENAMES", "/usr/share/vulkan/icd.d/lvp_icd.json")
    try:
        r = subprocess.run(cmd, cwd=ROOT, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return 2, "the axial gate timed out after %d s" % timeout
    return r.returncode, ("PASS" if r.returncode == 0 else
                          "FAIL -- see the axial-gate line above")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=None, help="deck stem to boot into")
    ap.add_argument("--hour", type=float, default=None)
    ap.add_argument("--check", action="store_true",
                    help="derive and cross-check, write nothing")
    ap.add_argument("--bake", action="store_true",
                    help="cut the deck into streaming cells first, if the set "
                         "is missing or no longer describes it (needs Godot)")
    ap.add_argument("--gate", action="store_true",
                    help="CI: does the shipped scene stream?")
    ap.add_argument("--axial-gate", action="store_true",
                    help="CI: can a body walk out of its own z-cluster into "
                         "another and back, arriving at a NAMED place, with "
                         "cells loading and freeing (needs Godot)")
    ap.add_argument("--strict-budget", action="store_true",
                    help="--axial-gate: also fail on the resident triangle "
                         "overage, which stream.gd's own policy prints rather "
                         "than pops a cell for")
    ap.add_argument("--allow-unbaked", action="store_true",
                    help="--axial-gate: exit 0 when the gate CANNOT RUN (no "
                         "cell set, no Godot) -- for CI, where "
                         "station/generated/ is gitignored. A walk that runs "
                         "and FAILS still exits 1. See `_cannot_run`")
    ap.add_argument("--out", default=OUT)
    # WHICH OF THE TWO BUILD DIRECTORIES TO BOOT FROM, and the default is not
    # the right one any more. `DECK_DIR` (`scene/deck/`) holds what
    # `walkable.py` writes: ONE z-cluster, built for a walk test -- 83 room
    # occupants, no corridor crowd, no cell set. `scene/station/` holds what
    # `tools/export_station.py` writes and `tools/bake_station.py` cuts into
    # cells: the whole deck, 6 clusters, 23 rooms, 408 actors, 444 crowd
    # instances, 206 streaming cells.
    #
    # Nothing chose the small one. `decks()` enumerates `*_col.obj` and only
    # the walk-test path emitted that name, so the real build was INVISIBLE to
    # this file and the packaged game shipped a test fixture. The flag exists
    # so the choice is stated in the command that writes the manifest, rather
    # than falling out of a filename convention.
    ap.add_argument("--deck-dir", default=None,
                    help="directory to boot from (default: scene/deck). "
                         "Use scene/station for the streamed build")
    a = ap.parse_args()
    if a.gate:
        return gate()
    if a.axial_gate:
        rc, why = axial_gate(a.deck,
                             ("--strict-budget",) if a.strict_budget else ())
        print("boot: axial gate %s" % why)
        # ONLY rc 2 -- the CANNOT-RUN state -- is forgiven, and only when the
        # caller asked. rc 1 is a walk that happened and failed and stays a
        # failure under every flag this file has.
        if rc == 2 and a.allow_unbaked:
            print("boot: --allow-unbaked -- exiting 0 on a gate that never "
                  "ran. This is NOT a pass and the line above says so")
            return 0
        return rc
    man = build(a.deck, a.hour, a.deck_dir)
    if a.bake and not (man["cells_count"] > 1 and man["cells_fresh"]
                       and man["cells_start"] >= 0):
        ok, why = bake_cells(man["deck"], a.deck_dir)
        print("boot: bake %s -- %s" % ("ok" if ok else "FAILED", why))
        man = build(a.deck, a.hour, a.deck_dir)
    d = man["spawn_derivation"]
    print("boot: %s -- spawn %.3f,%.3f,%.3f in %s, %d rooms; standing on 1 of "
          "%d floor triangles (of %d in the shell) at r=%.3f, %.0f deg"
          % (man["deck"], man["spawn"][0], man["spawn"][1], man["spawn"][2],
             man["spawn_at"] or "?", len(man["rooms"]),
             d["floor_triangles"], d["shell_triangles"], d["floor_r_m"],
             d["arc_deg"]))
    # WHICH BUILD A PLAYER WILL GET, in one line, every run. A manifest that
    # names no cell set boots the monolith, and the failure this whole section
    # exists to end was silent precisely because nothing said so.
    if man["cells_path"]:
        print("boot: STREAMED -- %d cells from %s, starting in cell %d%s"
              % (man["cells_count"],
                 os.path.relpath(man["cells_path"], ROOT), man["cells_start"],
                 "" if man["cells_fresh"] else "  -- STALE: " + man["cells_why"]))
        # AND ALONG WHICH AXES. A count of cells says nothing about the shape of
        # the grid, and a grid with no axis along the station streams nothing
        # when a player walks the length of it. INV-610.
        if man["cells_z_bands"] > 1:
            print("boot: the grid is %d band(s) of %.1f m along the axis; the "
                  "longest cell spans %.1f m of z and the biggest carries "
                  "%d triangles"
                  % (man["cells_z_bands"], man["cells_z_band_m"],
                     man["cells_z_span_max_m"], man["cells_tris_max"]))
        else:
            print("boot: ONE-DIMENSIONAL GRID -- every cell runs %.1f m of z, "
                  "so walking along the station loads and frees nothing and "
                  "the biggest cell is %d triangles. Re-bake: INV-610."
                  % (man["cells_z_span_max_m"], man["cells_tris_max"]))
    else:
        print("boot: MONOLITHIC -- %s. The shipped scene will load one deck "
              "whole and nothing will be on the other side of it."
              % man["cells_why"])
    ok = check(man)
    if a.check:
        return 0 if ok else 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(man, f, indent=1)
    print("boot: wrote %s" % os.path.relpath(a.out, ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
