#!/usr/bin/env python3
"""Can a player stand up in this station, and walk around in it?

THE GATE THIS PROJECT SPENT THREE PHASES WITHOUT. Every other gate here measures
a part in isolation -- `density.py` scores one module's line density,
`measure_frame.py` scores one image, `directory.py` counts locations per layer,
`budget.py` counts triangles. None of them asks the only question that matters
to a player, so nothing ever failed for the answer being "no". As of session 3u
the string `CollisionShape` appeared nowhere in the repository: 118 locations had
geometry, materials and measured lighting, and not one had a floor.

WHAT IT ASSERTS, per room, by launching Godot headless and driving a real body
over real physics frames:

  settles     the body comes to rest instead of falling through the deck
  on_floor    it is standing on geometry rather than hovering or wedged
  walks       pushing forward for one second actually moves it
  contained   five seconds of walking does not leave the room's footprint

`walks` is the one that catches an empty claim. A room whose deck is present but
whose collision is missing reports `on_floor=false` and `fell=true`; a room whose
spawn is inside a workbench reports `walks` near zero. Both happened while this
file was being written, which is why both are checks.

AND THE DECK, which is a different question and needed a different test.
`--deck` assembles a real ring corridor with its rooms, gives it the collision
shell from `station/collision.py`, and walks a body along it for as long as
asked. A room test can only ever say "not wedged"; a body that takes two
successful footsteps and stops at the third scores identically to one that
crosses the station. So the deck run reports **how far it actually got** and
**whether it was ever off the floor**, and both are asserted:

  traverse_m  distance covered walking one heading for thirty seconds
  offfloor    physics frames spent not standing on anything

That pair is what milestone W2 means by "go somewhere". Before the collision
shell existed this test reported a body that stood on the assembled deck with
`on_floor=true` and moved 1 mm in every direction, and no assertion in the
project could fail for it.

Run: python3 station/walkable.py [--rooms N] [--deck] [--verbose]
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

import collision as C                                           # noqa: E402
import deck as D                                                # noqa: E402
import directory as dr                                          # noqa: E402
import interact as IX                                           # noqa: E402
import interior as it                                           # noqa: E402
import interior_kit as K                                        # noqa: E402
import rooms as R                                               # noqa: E402

# A body that walks for a second at 4.2 m/s covers 4.2 m in the open. Rooms are
# small and full of furniture, so the bar is much lower: enough that a stuck
# body is unambiguous. 0.25 m is two footsteps.
MIN_WALK_M = 0.25
# Falling through the deck shows up as a large drop from the spawn.
MAX_DROP_M = 3.0

# How long the deck traverse runs, in physics frames, and how far it has to get.
# Thirty seconds at 4.2 m/s is 126 m of corridor; the bar is set at half that so
# a single snag fails it while ordinary contact with a wall does not. A corridor
# that only lets a body cover 60 m of a 126 m walk has something in it.
TRAVERSE_FRAMES = 1800
MIN_TRAVERSE_M = 63.0

# -- THE HEADING PROBE HAS TO OUTRUN THE CORRIDOR'S WIDTH ------------------
# `walk.gd` tries four headings before the traverse and keeps the best, and it
# scored them over `steps/2` frames -- 60, which is ONE SECOND, which at
# `PLAYER_SPEED_M_S` is 4.2 m. The probe was therefore SPEED-LIMITED rather
# than OBSTACLE-LIMITED: every heading with more than 4.2 m in front of it
# returned exactly 4.2, and `_best_yaw` fell to whichever tied leg won on float
# noise in the third decimal.
#
# It never mattered, because `_best_yaw` is used by exactly ONE code path --
# the traverse with no `--goto` and no `--arc-walk` -- and until 4z nothing had
# ever run it. Measured on blue/0/0 the moment something did:
#
#   legs=0.73/4.20/4.20/4.20  traverse_m=6.47 net_m=6.47 sweep_deg=0.00
#
# Three headings tied, the winner was an AXIAL one -- zero degrees round the
# ring -- and the body walked across the corridor into the far wall.
#
# So the leg has to be long enough that GEOMETRY decides it. A corridor's
# clearance ACROSS is bounded by the widest cross-section a heading could be
# confused by; ALONG it, a corridor runs for hundreds of metres. `walk.gd`
# spends `steps/2` frames on each of four legs, so this is 240 frames a leg --
# 4 seconds, 16.8 m -- comfortably past the 6.47 m of axial clearance measured
# above, and 16 s of probe in a run that already takes six minutes.
#
# BE PRECISE ABOUT WHICH CHANGE FIXED THIS DECK, because the control says it
# was not this one. Re-run at the old `--steps 120` with the deterministic
# tie-break in place, blue/0/0 PASSES: the legs still tie at 0.73/4.20/4.20/
# 4.20, and lowest-index-wins picks leg 1, which on a ring deck happens to be
# tangential. The TIE-BREAK is what fixed blue/0/0. The probe length is what
# makes the choice EVIDENCE rather than luck -- at 480 the same four headings
# read 0.73/16.80/6.47/16.65 and the axial one is measurably distinct from the
# corridor; at 120 three of them are indistinguishable and "best" means
# nothing. A deck whose axial hall is longer than its corridor is open would
# still be picked wrongly at 120, and no lowest-index rule can save it.
PROBE_FRAMES = 480

# What the WEAK form of the distance bar reports on this same deck: 125.93 m of
# path and this much displacement, because the body is steered at a room 6.3 m
# away and mills about once it arrives. Kept as a named constant because it is
# the negative case the no-goto run's displacement bar is controlled against --
# a measured number from a real run, not one invented to fail.
GOTO_NET_M = 0.35
# How close to the middle of a room counts as being in it. A body that stops in
# the doorway is not inside; one standing anywhere in the far half is.
ARRIVED_M = 1.5
# The deck spawns a body 50 mm above its floor, so a drop of more than a step
# means it is not where the shell says the floor is.
MAX_DECK_DROP_M = 0.30
# How close to actually facing the player the nearest inhabitant has to end up.
# Generous: they turn at a human rate and the walk ends when the player arrives,
# so a few degrees of lag is a person still turning, not a person facing wrong.
FACING_TOL_DEG = 25.0

# WHERE A PERSON STARTS. Blue Sector ring 0 deck 0 is the cluster milestone W5
# closes on -- `--deck blue/0/0 --use` is the run that reports a body spawning
# in the corridor, walking into the docking bays, seven of the room looking up,
# and a bay door opened by pressing a key. It is the densest thing on the
# station that has all four, so it is what a person is handed first.
DEFAULT_PLAY_DECK = "blue/0/0"
# The playable build's manifest, read by `walk.gd` when nothing is passed on the
# command line. It lives under `godot/` so `res://play.json` reaches it: Godot
# will not resolve a path that escapes the project directory, and the point of
# the file is that pressing Play with no arguments works.
PLAY_MANIFEST = os.path.join(ROOT, "godot", "play.json")


def godot_binary():
    for cand in (
        "/home/user/godot-build/godot-4.4-stable/bin/"
        "godot.linuxbsd.editor.double.x86_64",
    ):
        if os.path.exists(cand) and os.access(cand, os.X_OK):
            return cand
    import glob
    for c in glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*.double.*"):
        if os.access(c, os.X_OK):
            return c
    return None


def walk_room(key, godot, timeout=180):
    """Launch the walkable build in one room and parse its verdict."""
    schema, profile = it.load()
    place = dr.by_key(key)
    glb = os.path.join(ROOT, "station/generated/scene/interior", f"{key}.glb")
    if not os.path.exists(glb):
        return {"key": key, "error": "no glb -- run tools/export_scene.py"}
    sx, sy, sz = R.spawn_m(schema, profile, place)
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--",
           f"--glb={glb}", f"--spawn={sx},{sy},{sz}", "--walk-test"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"key": key, "error": f"timed out after {timeout}s"}
    m = re.search(r"WALKTEST (.+)", out)
    if not m:
        return {"key": key, "error": "no verdict printed"}
    d = {"key": key}
    for tok in m.group(1).split():
        k, _, v = tok.partition("=")
        d[k] = v
    meshes = re.search(r"walk: (\d+) mesh instances", out)
    d["meshes"] = int(meshes.group(1)) if meshes else 0
    return d


def _glb(obj_path, glb_path):
    """OBJ -> GLB, because Godot reads glTF and the generators write OBJ."""
    import export_gltf
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path, "--out", glb_path]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv


def room_target(meta, place):
    """A point on the floor in the middle of a room, for the body to walk to.

    ON THE FLOOR, not at eye or waist height. Aiming at a room's mid-height left
    an irreducible 0.85 m in the "how close did it get" number, because a body
    standing on the deck can never close a radial offset -- which reads as a
    near miss and is nothing of the kind.
    """
    a = math.radians(place["angle_deg"])
    r = meta["floor_r_m"] - 0.05
    return (r * math.cos(a), r * math.sin(a), place["z_m"])


# How close to the object the body has to end up for "you walked up to it" to
# mean anything. `interact.gd`'s reach is 2.4 m (INV-232); this is the bar on
# the WALK, and it is set at the reach so a body that stops outside arm's length
# fails even if a generous cone happened to prompt it.
USE_RANGE_M = 2.4


def group_aabb(verts, tris, groups, name):
    """The world box of one emitted group, FROM ITS TRIANGLE SPAN.

    THE SPAN, NOT THE OBJ. `dressing.machine` appends the object's outer span
    covering every triangle it built and then appends the `_mp_` part spans
    inside it, because `export_scene.per_triangle` resolves last-span-wins and
    that is how a part gets its own material. `deck.write_obj` resolves the same
    way -- so in the OBJ, and therefore in the glb, `prop_bay_door` keeps only
    the 12 faces no part claimed, and the other 1,600 are in `prop_mp_plant_*`
    groups shared with every other machine in the room. A box measured in the
    engine off the mesh that still carries the name is a box measured off the
    leftovers.

    Here the spans are still intact, so this is the object. It goes in the
    sidecar for the same reason `_actors.json` carries the yaw the generator
    used: the engine cannot recover it by looking, and asking the geometry to
    give back what the generator already knew is how the door leaves ended up
    0.16 m out of their own frame.
    """
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    n = 0
    for nm, a, b in groups:
        if nm != name:
            continue
        for i in range(a, min(b, len(tris))):
            n += 1
            for j in tris[i]:
                p = verts[j]
                for k in range(3):
                    lo[k] = min(lo[k], p[k])
                    hi[k] = max(hi[k], p[k])
    if n == 0:
        return None
    return lo, hi, n


def interact_rows(verts, tris, groups):
    """The sidecar `godot/scripts/interact.gd` reads, with a measured box each.

    `station/interact.py` says WHICH groups are declared interactables and what
    verb each carries; this adds where it is and how big, measured off the same
    mesh that is about to be written.
    """
    rows = IX.sidecar({nm for nm, _a, _b in groups})
    # WHAT LIES INSIDE EACH OBJECT'S SPAN, DERIVED FROM THE MESH.
    #
    # `dressing.machine` emits an articulated object as an outer span covering
    # everything, then its parts as spans inside it, and `write_obj` gives each
    # triangle to the LAST span covering it -- so the group still carrying the
    # object's own name owns only the leftovers no part claimed. Measured on
    # blue/0/0 in 4w: `interact.gd`'s name test grabbed **872 of 12,288 declared
    # triangles, 7.1%**; a bay door was 12 of its 536.
    #
    # **It is 12,288 of 12,288 since 4y** -- `dressing` names a part after its
    # own object and `materials.resolve` reads the material off the fragment
    # after `_mp_`. `--reach` measures it, with a control that rebuilds under
    # the old naming and gets 7.1% back.
    #
    # `span_groups` IS NOT A MEMBERSHIP LIST, and the name says so because the
    # first version of it was called `parts` and was used as one. Under the old
    # naming those group names were shared across every machine in the room --
    # `dressing` merges parts by material -- so mapping them back to their
    # enclosing interactable made each object swallow the room's machinery:
    # 209% of their own spans, a bay door grabbing 2,888 triangles of a
    # 536-triangle object. `--use` passed both before and after, which is its
    # own finding and is why `--reach` does not press anything.
    #
    # It stays because it is the cheapest description of what an object is made
    # of, it is now one-to-one with the object, and it is still read by nothing.
    owner = [None] * len(tris)
    for nm, a2, b2 in groups:
        for i in range(a2, min(b2, len(tris))):
            owner[i] = nm
    out = []
    for r in rows:
        box = group_aabb(verts, tris, groups, r["group"])
        if box is None:
            continue
        lo, hi, n = box
        r["centre"] = [(lo[k] + hi[k]) / 2.0 for k in range(3)]
        r["half"] = [max((hi[k] - lo[k]) / 2.0, 0.0) for k in range(3)]
        r["tris"] = n
        inside = set()
        for nm, a2, b2 in groups:
            if nm != r["group"]:
                continue
            for i in range(a2, min(b2, len(tris))):
                if owner[i]:
                    inside.add(owner[i])
        r["span_groups"] = sorted(inside)
        out.append(r)
    return out


def reach_report(tris, groups, rows):
    """HOW MUCH OF EACH DECLARED OBJECT THE RUNTIME'S NAME TEST ACTUALLY GRABS.

    The measurement session 4w had to make by hand and session 4w's own gate
    could not make at all. `--use` presses one object and checks the prompt
    appeared and something moved 4 mm; that passed at **7.1%** of the objects'
    triangles and passed again at **209%**, so it cannot see either failure.
    This asks the question directly, offline, over the emitted mesh.

    It models `interact.gd` exactly, including the part that bites: the runtime
    walks the declared groups in SIDECAR ORDER and takes the FIRST whose name
    the mesh's begins with, plus an underscore, then `break`s. Two declared
    objects sharing a prefix therefore collide -- 4w measured `deck_marking` at
    200% of its own span, reaching into a neighbour whose name starts the same
    way -- and modelling the loop as "any match" would hide it.

    Returns `(rows, total_span, total_grabbed, stray)`, one row per object:
    `(group, span_tris, grabbed_tris, stray_tris)`. `stray` is triangles the
    name test grabs that are NOT inside the object's own span, which is the
    209% failure; `span - grabbed` is the 7.1% one. Both directions matter and
    a single percentage would let them cancel.
    """
    # The emitted mesh for a group is the triangles it still OWNS after
    # last-span-wins, which is what the engine sees; the object's span is every
    # triangle its outer span covers, which is what the object IS.
    owner = [None] * len(tris)
    for nm, a, b in groups:
        for i in range(a, min(b, len(tris))):
            owner[i] = nm
    declared = [r["group"] for r in rows]
    span = {d: set() for d in declared}
    for nm, a, b in groups:
        if nm in span:
            span[nm].update(range(a, min(b, len(tris))))

    def key_for(mesh_name):
        if mesh_name in span:
            return mesh_name
        for d in declared:                      # sidecar order, first wins
            if mesh_name.startswith(d + "_"):
                return d
        return None

    keyed = {}
    for nm in {o for o in owner if o}:
        keyed[nm] = key_for(nm)
    grab = {d: set() for d in declared}
    for i, o in enumerate(owner):
        k = keyed.get(o) if o else None
        if k is not None:
            grab[k].add(i)
    out = []
    for d in declared:
        out.append((d, len(span[d]), len(grab[d]), len(grab[d] - span[d])))
    return (out, sum(len(span[d]) for d in declared),
            sum(len(grab[d]) for d in declared),
            sum(len(grab[d] - span[d]) for d in declared))


def _reach_main(a):
    """`--reach`: the fraction of each declared object the runtime can grab.

    Builds the deck in memory -- no engine, no Godot binary, seconds rather
    than minutes -- because the question is about names and spans, both of
    which the generator knows and the engine only inherits.
    """
    import dressing as DR                                       # noqa: PLC0415
    sector, ring, deck = (a.deck or DEFAULT_PLAY_DECK).split("/")
    schema, profile = it.load()

    def measure():
        v, t, g, _s = D.build_deck(schema, profile, sector, int(ring),
                                   int(deck), z_m=a.z)
        return reach_report(t, g, interact_rows(v, t, g))

    rows, span, grab, stray = measure()
    pct = 100.0 * grab / span if span else 0.0
    print(f"{sector}/{ring}/{deck}: {len(rows)} declared interactables, "
          f"{span:,} triangles between them")
    print(f"  the runtime's name test grabs {grab:,} -- {pct:.1f}% -- "
          f"of which {stray:,} lie outside the object they were grabbed for")
    for grp, sp, gr, st in sorted(rows, key=lambda r: r[1], reverse=True)[:8]:
        print(f"      {grp:44s} {gr:6,} of {sp:6,}  "
              f"{100.0 * gr / sp if sp else 0:5.1f}%"
              + (f"  +{st:,} stray" if st else ""))
    ok = span > 0 and grab == span and stray == 0
    print(f"  {'PASS' if ok else 'FAIL'}  a pressed object is the whole object")
    if a.control:
        # THE PRE-4y NAMING, REBUILT. One part group per class, shared by every
        # machine in the room, so `prop_bay_door_` matches none of them and an
        # object is its leftovers. If this does NOT collapse, the measurement
        # above is not measuring what it says.
        DR.PER_OBJECT_PARTS = False
        try:
            _r2, span2, grab2, stray2 = measure()
        finally:
            DR.PER_OBJECT_PARTS = True
        p2 = 100.0 * grab2 / span2 if span2 else 0.0
        print(f"  control: with the pre-4y shared part names the same test "
              f"grabs {grab2:,} of {span2:,} -- {p2:.1f}%")
        if not (p2 < 50.0 < pct):
            print("  FAIL  the control did not collapse; this gate is inert")
            ok = False
    return 0 if ok else 1


def strip_group(verts, tris, groups, name):
    """Remove one object from the mesh entirely -- THE NEGATIVE CONTROL.

    Drops the triangles of every span called `name`. That is the object AND its
    articulated parts, because `dressing.machine`'s outer span covers all of
    them; dropping only the triangles the OBJ writer would label `name` would
    leave 1,600 of the door standing and delete twelve.

    Returns `(tris, groups, dropped)` over the SAME vertex list -- an unused
    vertex costs nothing and re-indexing them would be a second thing to get
    wrong in the control rather than in the subject.
    """
    kill = set()
    for nm, a, b in groups:
        if nm == name:
            kill.update(range(a, min(b, len(tris))))
    if not kill:
        return tris, groups, 0
    keep = [i for i in range(len(tris)) if i not in kill]
    remap = {old: new for new, old in enumerate(keep)}
    out_t = [tris[i] for i in keep]
    out_g = []
    for nm, a, b in groups:
        idx = [remap[i] for i in range(a, min(b, len(tris))) if i in remap]
        if idx:
            out_g.append((nm, idx[0], idx[-1] + 1))
    return out_t, out_g, len(kill)


def pick_interactable(rows, target, place=None, responds=True):
    """Which object the use test walks up to, chosen by DATA not by hand.

    The interactable nearest the point the body was already walking to.
    Deterministic, so the gate measures the same object every run, and it keeps
    the route the same as the plain deck walk -- a use test that also changes
    where the body goes cannot tell a broken prompt from a blocked route.

    TWO FILTERS AND BOTH ARE THE MODULE'S OWN DATA. `pressable` excludes
    `tread`: a deck marking is something you walk on and giving it a keypress
    would be a lie. `responds` prefers a verb the OBJECT answers -- a lever, a
    door, a drawer -- over one that needs a body this project has not rigged, so
    the gate exercises the strongest claim the build can actually make. The
    first run of this gate chose a `bay_control_booth`, whose verb is `serve`,
    and the pass was "it was used and nothing happened".
    """
    best, bd = None, float("inf")
    for r in rows:
        if not r.get("pressable"):
            continue
        if responds and not r.get("responds"):
            continue
        if place is not None and r.get("place") != place:
            continue
        c = r["centre"]
        d = sum((c[k] - target[k]) ** 2 for k in range(3))
        if d < bd:
            best, bd = r, d
    return best


_SRC_MTIME = None


def _stale(path):
    """Is this generated file older than the code that generates it?

    THE CROWD LIBRARY WAS CACHED ON `os.path.exists` AND NOTHING ELSE, so it
    survived every change to the thing that writes it. Session 4i: the glTF
    exporter learned crease-angle normals, the deck was rebuilt, 10.7% of the
    frame changed -- and the 134 people in the corridor came back bit-identical
    and flat-shaded, because their three .glb files were hours old and still
    existed. The A/B looked like the change had done nothing.

    Same defect CLAUDE.md records for `budget.py`'s cached collision total and
    for `--gate-frames` reading a committed PNG: **a cache that can go stale
    silently is a second copy of a computed number.** Keyed on every station
    module rather than on a hand-listed few, because the list is exactly the
    thing that goes out of date -- the library's shape comes from `populace`,
    its bodies from `npc/*`, its normals from `export_gltf`, and the next one
    from a module that does not exist yet.
    """
    global _SRC_MTIME
    if not os.path.exists(path):
        return True
    if _SRC_MTIME is None:
        import glob                                             # noqa: PLC0415
        _SRC_MTIME = max(
            os.path.getmtime(p)
            for p in glob.glob(os.path.join(HERE, "*.py"))
            + glob.glob(os.path.join(HERE, "npc", "*.py")))
    return os.path.getmtime(path) < _SRC_MTIME


def engine_args(out, stem, crowd, gravity="drum", spawn=None):
    """The command line that makes the engine BE this piece of the station.

    ONE LIST, SHARED BY THE TEST AND BY A PERSON PLAYING IT. The headless gate
    and `tools/play.sh` launch the same scene with the same mesh, the same
    collision shell, the same cast, the same crowd ladder and the same
    interactables -- because a build a player walks in that is assembled
    differently from the build the gate measures is a build the gate does not
    measure. This is hard rule 4 applied to a command line: one description of
    the thing, not two.

    What is NOT here is everything test-only -- `--walk-test`, `--goto`,
    `--traverse`, `--no-doors`. A player is not steered at a target and does not
    stop after 1,800 frames.
    """
    a = [f"--glb={os.path.join(out, stem + '.glb')}",
         f"--collision={os.path.join(out, stem + '_col.glb')}",
         f"--gravity-mode={gravity}"]
    if spawn is not None:
        a.append("--spawn={:.6f},{:.6f},{:.6f}".format(*spawn))
    if crowd:
        import populace as _pop                                   # noqa: PLC0415
        lad = _pop.crowd_ladder()
        a += [f"--crowd={os.path.join(out, stem + '_crowd.json')}",
              # The whole ladder, as `max_m:lod` pairs and one glb each, so
              # the runtime knows both which mesh to use at which distance
              # and where to find it.
              "--crowd-ladder=" + ",".join(f"{hi:g}:{lod}" for hi, lod in lad),
              "--crowd-glbs=" + ",".join(
                  os.path.join(out, f"crowd_lod{lod}.glb")
                  for _hi, lod in lad)]
    # THE SIDECARS THAT WERE ACTUALLY WRITTEN. The drum has no cast list and no
    # interactables -- it is a heightfield, not a room -- and naming a file that
    # is not there makes the engine complain about a thing nobody asked for.
    # `--cells` is in this SHARED list, so the headless walk gate streams exactly
    # as a person does. walk.gd's own header gives the reason: "a step that only
    # ever runs in the configuration nobody checks is a step that rots", and
    # this file carries that scar three times over. `--no-stream` is the control
    # and loads the deck whole, which is what every session before 4p did.
    for flag, suffix in (("actors", "_actors.json"),
                         ("interact", "_interact.json"),
                         ("cells", "_cells.json")):
        p = os.path.join(out, stem + suffix)
        if os.path.exists(p):
            a.append(f"--{flag}={p}")
    a.append(f"--door-travel={K.PROVISIONAL['door_width_m'] / 2.0}")
    return a


# How far round the ring the streaming test walks, in degrees. THREE CELLS on a
# Blue deck at 20 degrees each: far enough that the window must move twice and
# free two cells behind it, near enough that the body is still following the
# corridor rather than being steered at a chord across the middle of the
# station. `deck.cell_partition` and this walk are measured on the same cells.
STREAM_WALK_DEG = 60.0
# How far the body actually has to get round the ring for the run to count. A
# cell is 20 degrees; two cell widths means it has crossed at least one boundary
# with room to spare, so a failure is a body that did not travel rather than one
# that stopped a metre short of an arbitrary line.
STREAM_MIN_DEG = 40.0


def walk_deck(sector, ring, deck, godot, timeout=1800, traverse=None,
              goto_key=None, no_doors=False, z_m=None, bump=False,
              no_npc_collision=False, use=False, strip=None,
              build_only=False, stream_deg=None, no_stream=False,
              no_goto=False, steps=None):
    """Assemble a deck, put a body on it, and walk it.

    The render mesh and the collision shell are exported separately and BOTH are
    handed to the engine -- the shell to stand on, the render mesh to be the
    place. Handing over only the render mesh is what this test used to do and
    the body could not take a step; see `station/collision.py`.
    """
    # THE DRUM IS NOT A RING DECK. `deck.build_deck` rejects green/1 by name and
    # the drum's floor is a heightfield, not a corridor: see
    # `station/drum_walk.py`, whose rule INVERTS this file's. A corridor needs a
    # smooth shell because its millimetre relief is decoration; the drum needs
    # the shape of its own ground, because there the relief IS the content.
    if (sector, ring) in D.NOT_RING_DECKS:
        import drum_walk as DW                                  # noqa: PLC0415
        return DW.walk(key=goto_key or "the_garden", traverse=traverse,
                       timeout=timeout, godot=godot, build_only=build_only)

    schema, profile = it.load()
    out = os.path.join(ROOT, "station/generated/scene/deck")
    os.makedirs(out, exist_ok=True)
    # Z IN THE FILENAME, because a deck now has up to six walkable clusters
    # and they are different places. Without it the second cluster overwrote
    # the first's mesh and the walk measured whichever ran last.
    stem = (f"{sector}_{ring}_{deck}" if z_m is None
            else f"{sector}_{ring}_{deck}_z{int(z_m)}")
    # A STRIPPED BUILD GETS ITS OWN FILES. Writing the control's mutilated mesh
    # over the deck's would leave the next `--deck` run measuring a station with
    # a docking clamp missing, and it would pass.
    if strip:
        stem += "_nouse"
    v, t, g, s = D.build_deck(schema, profile, sector, ring, deck, z_m=z_m)
    # PROPS ON. This is a body being put in the room, so the furniture has to be
    # there: a route that only exists because you can walk through a table is
    # not a route.
    cv, ct, cm = D.build_collision(schema, profile, sector, ring, deck,
                                   z_m=z_m, props=True)
    C.write_obj(os.path.join(out, f"{stem}_col.obj"), cv, ct,
                cm.get("groups"))

    # -- WHAT A PLAYER CAN USE, and where it is -----------------------------
    # Chosen BEFORE the mesh is written, because the control has to walk to the
    # same object the subject did. `strip` names it directly; otherwise it is
    # the pressable interactable nearest the point the body was already going.
    goto = goto_key or s["spawn_at"]
    rtgt = room_target(cm, dr.by_key(goto))
    rows = interact_rows(v, t, g)
    chosen, stripped = None, 0
    if strip:
        chosen = next((r for r in rows if r["group"] == strip), None)
    elif use:
        # In the room the body was already going to, with a response behind it;
        # then in that room at all; then anywhere on the deck. Each fallback is
        # a weaker claim and the verdict says which one it got.
        chosen = (pick_interactable(rows, rtgt, place=goto)
                  or pick_interactable(rows, rtgt, place=goto, responds=False)
                  or pick_interactable(rows, rtgt)
                  or pick_interactable(rows, rtgt, responds=False))
    if strip:
        # REMOVED FROM THE WORLD THE INTERACTION LAYER READS, and from nothing
        # else. The collision shell still carries the object's box, so the body
        # ends up in exactly the same place with exactly the same route; the
        # ONLY difference between the two runs is whether there is anything
        # there to look at. A control that also moves the body would confound
        # "the prompt is broken" with "it never got near".
        t, g, stripped = strip_group(v, t, g, strip)
        rows = interact_rows(v, t, g)
    D.write_obj(os.path.join(out, f"{stem}.obj"), v, t, g)
    with open(os.path.join(out, f"{stem}_interact.json"), "w") as f:
        json.dump(rows, f)

    # THE CAST LIST, beside the mesh. A body is baked into the merged geometry,
    # so the engine cannot recover who is where or which way they face by
    # looking at it. The generator knows; it writes it down.
    import json as _json
    with open(os.path.join(out, f"{stem}_actors.json"), "w") as f:
        _json.dump(s.get("actors", []), f)
    # THE CROWD, which is a different thing from the cast list and has to be.
    # An actor is a body baked into the deck mesh at a fixed pose; a crowd
    # instance is a PLACEMENT against `populace.station_crowd_library`'s 112
    # shared bodies. The library is written once per LOD rather than per deck
    # -- it is a function of the species mix, not of who is walking -- and the
    # instance list is what the runtime rewrites to make them move.
    crowd = s.get("crowd", [])
    with open(os.path.join(out, f"{stem}_crowd.json"), "w") as f:
        _json.dump(crowd, f)
    if crowd:
        # EVERY RUNG OF THE LADDER, not just the one the bake chose. A baked
        # walker had a single LOD because a static mesh has no other option;
        # an INSTANCED one is a transform, so the runtime can pick per person
        # per frame -- and `populace.crowd_ladder` says which level each
        # distance band gets, derived from `schedule.NPC_BUDGET`'s own
        # allowances. Written once per level rather than once per deck: the
        # library is a function of the species mix, not of who is walking.
        import populace as _pop                                 # noqa: PLC0415
        for _hi, lod in _pop.crowd_ladder():
            lib = os.path.join(out, f"crowd_lod{lod}.obj")
            if _stale(lib) or _stale(lib[:-4] + ".glb"):
                cv2, ct2, cg2 = _pop.station_crowd_library(lod)
                D.write_obj(lib, cv2, ct2, cg2)
                _glb(lib, lib[:-4] + ".glb")
    _glb(os.path.join(out, f"{stem}.obj"), os.path.join(out, f"{stem}.glb"))
    _glb(os.path.join(out, f"{stem}_col.obj"),
         os.path.join(out, f"{stem}_col.glb"))

    # -- THE DECK CUT INTO ITS STREAMING CELLS -----------------------------
    # `budget.py` has said `resident triangles` is 5.44x its budget since 4l,
    # for one reason it printed itself: "walk.gd loads one .glb whole -- there
    # is no streaming and no LOD". 4m measured what the alternative costs on
    # real content rather than on the corridor kit -- worst three consecutive
    # cells 147,675 triangles against a 180,000 budget -- so the target is
    # known and this writes the pieces it needs.
    #
    # THE CELLS ARE THE RING'S OWN, from `interior.ring_cells` by way of
    # `deck.cell_partition`: the same 18 x 20 degrees `npc/navigation.cell_plan`
    # builds 3,414 of. Not a second partition.
    #
    # THE COLLISION SHELL IS NOT CUT, and that is the design rather than an
    # omission. It is 5,270 triangles for the whole cluster against the render
    # mesh's 657,880, so keeping it whole costs almost nothing and buys
    # something this project cannot afford to get wrong: the floor can never
    # vanish under a player because a cell is in flight. The walk gate's
    # `offfloor` assertion stays true by construction.
    #
    # NOTHING LOADS THESE YET, and they are written anyway rather than left for
    # the session that writes the loader, because the loader's real obstacle is
    # not the loading. `walk.gd` wires doors, actors and interactables by
    # walking the whole render scene once, so a cell arriving later would carry
    # people nobody watches and objects nobody can press -- making those three
    # modules additive is the work, and it is a separate one. Measured on this
    # deck, what cannot stream until then is 49,252 triangles of actors plus
    # 872 of interactables: **50,124, 8% of the mesh**, which added to a
    # three-cell bulk window lands at about 186,547 against a 180,000 budget.
    # That is the number the next session is working against.
    # WHAT MUST NOT BE CUT IN HALF, named by the module that wires it. A door
    # is its leaves, a person is their parts, a prop is its group; `walk.gd`
    # looks all three up by name, so an object split across two cells is a door
    # with one leaf and a body with no legs. Cutting per triangle did exactly
    # that to 5 of this deck's 12 leaves and 54 of its 288 actor spans.
    #
    # STRUCTURE IS STILL CUT PER TRIANGLE, deliberately: nothing looks a wall
    # panel up by name, and keeping the corridor's continuous runs whole put
    # 418,728 triangles into one cell -- measured, not feared.
    # A DOOR IS ITS LEAVES, NOT ONE LEAF. `door.gd::collect` groups
    # `doorleaf_<key>_<i>` by `<key>` and opens the set together, so keeping
    # each LEAF whole still puts `doorleaf_docking_bays_0` in cell 0 and `_1`
    # in cell 17 -- a door that opens halfway, and nothing would report it. The
    # key is everything before the last underscore, which is the same rule
    # `door.gd` uses to parse the name.
    doors = {n.rsplit("_", 1)[0] for n, _l, _h in g
             if n.startswith("doorleaf_") and "_" in n[9:]}
    # 4o's open gap -- a machine's frame landing in the neighbouring cell --
    # is NOT closed by adding `span_groups` here, and it was tried. Those names
    # are shared across every machine in the room, so keeping one whole drags
    # the room's entire machinery into one cell: the same mistake as keeping
    # every span whole, which took the worst cell to 418,728 triangles.
    whole = (sorted(doors)
             + [a["group"] for a in s.get("actors", ()) if a.get("group")]
             + [r["group"] for r in rows if r.get("group")])
    cellmap, cmeta2 = D.cell_partition(v, t, sector, ring, deck,
                                       schema, profile, groups=g, whole=whole)
    cells = []
    for ci, idxs in enumerate(cellmap):
        if not idxs:
            continue
        cv3, ct3, cg3 = D.submesh(v, t, g, idxs)
        cobj = os.path.join(out, f"{stem}_c{ci}.obj")
        D.write_obj(cobj, cv3, ct3, cg3)
        _glb(cobj, cobj[:-4] + ".glb")
        cells.append({"cell": ci, "tris": len(ct3),
                      "deg_lo": ci * cmeta2["cell_deg"],
                      "deg_hi": (ci + 1) * cmeta2["cell_deg"],
                      "glb": cobj[:-4] + ".glb"})
    with open(os.path.join(out, f"{stem}_cells.json"), "w") as f:
        _json.dump({"cell_deg": cmeta2["cell_deg"], "cells": cells}, f)

    sx, sy, sz = s["spawn"]
    # -- STOP HERE IF SOMEBODY IS GOING TO PLAY IT ------------------------
    # `tools/play.sh` needs the deck built and the arguments that describe it;
    # it does not need a walk test run first. Returning the manifest rather
    # than writing a second assembler is the point: there is exactly one piece
    # of code that knows how a deck becomes something you can stand in, and
    # both the gate and the human launch go through it.
    if build_only:
        return {"stem": stem, "out": out, "spawn": [sx, sy, sz],
                "rooms": s["rooms"], "spawn_at": s["spawn_at"],
                "render_tris": len(t), "collision_tris": len(ct),
                "arc_deg": cm["arc_deg"], "actors": len(s.get("actors", ())),
                "crowd": len(crowd), "interact_rows": len(rows),
                "args": engine_args(out, stem, crowd, spawn=(sx, sy, sz))}
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--"]
    cmd += engine_args(out, stem, crowd, spawn=(sx, sy, sz))
    cmd += ["--walk-test",
            f"--traverse={traverse if traverse is not None else TRAVERSE_FRAMES}",
            f"--steps={steps if steps is not None else PROBE_FRAMES}"]
    # Walking INTO a named place is the claim W2 actually makes, and it is a
    # strictly harder question than "did the body move": it fails when the route
    # is blocked, not only when the body is wedged. The body steers straight at
    # the target, so the target has to be one it can reach without navigating --
    # the room the spawn is standing outside. Reaching one across the ring needs
    # a path, and there is no pathfinder yet.
    tx, ty, tz = rtgt
    # -- WALK UP TO A THING AND USE IT -------------------------------------
    # The route is the same one the plain deck walk takes -- the object is the
    # pressable interactable nearest the room target -- so a failure here is a
    # failure of the PROMPT, not of the way in. The body is steered at the
    # object's own centre rather than the room's, and `player.step` flattens the
    # direction onto the floor, so a bay door 2.5 m up is walked TO and not
    # walked AT.
    if chosen is not None:
        tx, ty, tz = chosen["centre"]
    # -- IS A PERSON SOMETHING YOU BUMP INTO? ------------------------------
    # `rooms.is_solid` keeps every `npc_` group OUT of the static collision on
    # purpose -- static collision is generated once, so an inhabitant baked
    # into it is a permanent statue. The capsule therefore lives on a runtime
    # node (`npc.gd::_give_body`), and this is the only thing that can tell
    # whether it is actually there: steer the body straight at a person
    # instead of at a room, and see how close it gets.
    # -- WALK ROUND THE RING, TO MAKE THE LOADER FREE SOMETHING ------------
    # The ordinary deck run covers 126 m of PATH and ends 0.35 m from where it
    # started -- `traverse_m=125.93 net_m=0.35` -- because the traverse sweeps
    # headings and the goto phase then pulls the body back to the room it is
    # standing outside. Distance covered was the right thing to assert in 3v
    # and it is not displacement, so the streaming window never moved and the
    # free path was exercised only by a bug.
    #
    # So this steers at a point `stream_deg` round the ring at the body's own
    # radius and z. On a ring corridor that heading is very nearly tangential,
    # which is to say: along the corridor.
    if stream_deg:
        cmd += [f"--arc-walk={stream_deg:g}"]
    bumped = None
    if bump:
        cand = [a for a in s.get("actors", ())
                if float(a.get("r_m", 0.0)) > 0.0]
        if cand:
            px, py, pz = s["spawn"]
            bumped = min(cand, key=lambda a: (a["x"] - px) ** 2
                         + (a["y"] - py) ** 2 + (a["z"] - pz) ** 2)
            tx, ty, tz = bumped["x"], bumped["y"], bumped["z"]
    # -- OR STEER AT NOTHING AT ALL, WHICH IS THE CASE NOTHING EVER RAN ----
    # `walk.gd`'s traverse has three modes and the third has never been used:
    # tangent (`--arc-walk`), toward a target (`--goto`), and -- when neither is
    # given -- `step(delta, Vector2(0, 1))`, which is the body walking FORWARD
    # on its own heading. That third one is what this file's docstring has
    # always described as the deck assertion: "distance covered walking one
    # heading for thirty seconds". `walk_deck` appended `--goto` unconditionally,
    # so it was unreachable, and `deck_verdict`'s no-goto branch was dead code
    # measuring nothing.
    #
    # It is a strictly harder question than the goto walk. Steered at a room
    # 6.3 m away the body arrives and mills about: 125.93 m of PATH, 0.35 m of
    # displacement. Walking one heading, the corridor has to actually go
    # somewhere and stay walkable the whole way.
    cmd += [f"--door-key={goto}"]
    if not no_goto:
        cmd += [f"--goto={tx},{ty},{tz}"]
    if chosen is not None:
        cmd += [f"--use-group={chosen['group']}"]
    if no_stream:
        cmd += ["--no-stream"]
    if no_doors:
        cmd += ["--no-doors"]
    if no_npc_collision:
        cmd += ["--no-npc-collision"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"key": stem, "error": f"timed out after {timeout}s"}
    m = re.search(r"WALKTEST (.+)", res)
    if not m:
        return {"key": stem, "error": "no verdict printed"}
    d = {"key": stem, "rooms": s["rooms"], "spawn_at": s["spawn_at"],
         "render_tris": len(t), "collision_tris": len(ct),
         "arc_deg": cm["arc_deg"], "goto": goto,
         "doors": len(cm.get("rooms", ()))}
    if stream_deg:
        d["stream_deg"] = stream_deg
        d["spawn_xyz"] = list(s["spawn"])
    d["actors_expected"] = bool(s.get("actors"))
    # THE PYTHON SIDE KNOWS WHAT IT ASKED FOR, and that is what makes the
    # assertions in `use_verdict` unguardable: if `interact.gd` fails to load,
    # every `use*` token vanishes from the verdict and the check fires on the
    # ABSENCE, exactly the way the NPC checks did not for six runs.
    d["interact_expected"] = bool(rows)
    d["interact_rows"] = len(rows)
    if chosen is not None:
        d["use_want"] = chosen["group"]
        d["use_want_verb"] = chosen["verb"]
        d["use_want_label"] = chosen["label"]
        d["use_want_place"] = chosen["place"]
        d["use_want_tris"] = chosen["tris"]
    if strip:
        d["stripped"] = strip
        d["stripped_tris"] = stripped
    if bumped is not None:
        d["bumped"] = bumped["group"]
        d["bump_r_m"] = float(bumped["r_m"])
        d["bump_who"] = (bumped.get("who") or {}).get("name", "") \
            if isinstance(bumped.get("who"), dict) else ""
        d["npc_collision"] = "off" if no_npc_collision else "on"
    for tok in m.group(1).split():
        k, _, val = tok.partition("=")
        d[k] = val
    return d


# How much closer the body must get with an inhabitant's capsule OFF than with
# it on, for "they are solid" to be a claim rather than noise. A person's own
# radius is 0.27-0.41 m and the player capsule adds its own, so a real block
# separates the two runs by more than half a metre; 0.25 is half of the
# smallest true separation and well outside the ~0.05 m the walker's own
# stopping distance varies by between runs.
BUMP_MARGIN_M = 0.25


# How far the corridor's crowd must travel over a walk test for "they walk" to
# be a claim rather than a hope. DERIVED: `populate_corridor` gives every
# walker their own gait's speed -- 1.4-1.5 m/s for a human at 1 g -- and the
# test runs `TRAVERSE_FRAMES` at 1/60 s, so 134 people over 1,800 frames should
# cover 134 x 1.45 x 30 = 5,800 m between them. A tenth of that is a bar only
# a crowd that has genuinely stopped can fail.
CROWD_TRAVEL_MIN_M = 500.0


# The bounds the loader exists to hold. `budget.CELLS` states them: 60,000 per
# cell and 180,000 for "the cell you are in plus both neighbours". Imported
# rather than repeated -- a second copy here is a second budget.
def _cell_budget():
    import budget as B                                           # noqa: PLC0415
    return B.CELLS["resident_tris"]


# How many streaming cells the body must sweep for "it went somewhere" to be a
# claim. ONE: a body that has crossed a whole cell has left the one it started
# in, which is the smallest statement that is not about jiggling on a boundary.
MIN_SWEEP_CELLS = 1.0


def stream_verdict(d):
    """Did the loader actually LOAD AND FREE while a body walked the ring?

    THE FREE PATH HAD NO GATE. Session 4p's only evidence that freeing worked
    was a thrash bug that happened to run it 1,734 times -- which is evidence,
    and is not a test that can fail on purpose. A standing player frees
    nothing, so the ordinary deck run reports `frees=0` honestly and proves
    nothing about it.

    What is asserted, in the order a failure would matter:

      the body travelled round the ring, in DEGREES rather than path length
      the window moved, so cells were loaded behind it
      and cells were FREED, so resident geometry does not just grow
      resident never exceeded the budget the loader exists to reach
      doors, people and interactables are still wired at the end
    """
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    off, tot = (d.get("offfloor", "0/0").split("/") + ["0"])[:2]
    if int(off) > 0:
        return False, f"left the floor for {off} of {tot} frames"
    sx, sy, _sz = d.get("spawn_xyz", (1.0, 0.0, 0.0))
    # `end`, NOT `rest`. `rest` is where the body settled before it took a
    # step; using it measured 0.0 degrees swept for a body that had walked the
    # whole run, which is a gate failing on its own arithmetic.
    rest = [float(x) for x in d.get("end", d.get("rest", "0,0,0")).split(",")]
    a0 = math.degrees(math.atan2(sy, sx))
    a1 = math.degrees(math.atan2(rest[1], rest[0]))
    swept = abs((a1 - a0 + 180.0) % 360.0 - 180.0)
    # THE BAR IS THE LOADER'S OWN BEHAVIOUR, NOT A DISTANCE. The first version
    # demanded 40 degrees of sweep and failed at 7.4, because this corridor is
    # obstructed 27 m one way and 14 m the other -- a real finding about the
    # CONTENT, and nothing to do with whether the loader works. A body that
    # never leaves its cells reports `loads=3 frees=0` and cannot pass what is
    # below, so the movement requirement is carried by the loader's own numbers
    # rather than by a threshold that has to be tuned against the geometry.
    loads, frees = int(d.get("loads", 0)), int(d.get("frees", 0))
    if swept <= 0.0:
        return False, "the body did not move at all"
    # -- AND IT WENT SOMEWHERE, WHICH IS NOT THE SAME AS WALKING ------------
    # `traverse_m=125.93` and `net_m=0.35` are printed by the same run: 126 m
    # of walking that ends where it started. Path length is satisfied by a body
    # pacing on the spot. `sweep_deg` is the FURTHEST the body got round the
    # ring from where the traverse began -- the maximum, not the end, because
    # this gate turns round at the midpoint on purpose and its net displacement
    # is small by design.
    #
    # THE BAR IS ONE CELL. `interior.ring_cells` makes them 20 degrees on a Blue
    # deck, so a body that has swept a whole cell has provably left the one it
    # started in rather than jiggling across a boundary -- which is exactly the
    # claim the loads and frees below are about.
    import interior as _it2                                       # noqa: PLC0415
    _sc, _sp = _it2.load()
    cell_deg = float(_it2.ring_cells(_sc, _sp, "blue", 0, 0)["cell_deg"])
    sweep = float(d.get("sweep_deg", 0.0))
    if sweep < MIN_SWEEP_CELLS * cell_deg:
        return False, (f"got {sweep:.1f} deg round the ring at its furthest, "
                       f"under {MIN_SWEEP_CELLS * cell_deg:.0f} -- less than a "
                       f"cell, so it never left the one it started in")
    if loads < 4:
        return False, (f"only {loads} cell load(s) after {swept:.1f} deg of "
                       f"travel -- the window never moved, so nothing here "
                       f"tests the loader")
    if frees < 1:
        return False, (f"{loads} loads and {frees} frees -- the loader only "
                       f"grows, which is not streaming")
    peak, bar = int(d.get("peak", 0)), _cell_budget()
    if peak > bar:
        return False, (f"peak resident {peak:,} triangles against a {bar:,} "
                       f"budget")
    # AND THE WIRING SURVIVED BEING UNLOADED. `forget_freed` drops records whose
    # meshes the engine has freed; if it dropped too much, the body finishes in
    # a corridor with no doors and nobody in it, and every other number here
    # still looks fine.
    # AGAINST WHAT WAS WIRED WHEN IT SET OFF, not against zero. The body walks
    # out and turns round, so it finishes among the same cells it started in --
    # and the corridor it walks THROUGH has stretches with no doors and nobody
    # in them, where a bare "> 0" test asserts something false about the
    # content instead of something true about the loader.
    wd, wp = int(d.get("wired_doors", 0)), int(d.get("wired_people", 0))
    w0 = [int(x) for x in d.get("wired0", "0/0/0").split("/")]
    if w0[0] > 0 and wd < w0[0]:
        return False, (f"set off with {w0[0]} doors wired and came back to "
                       f"{wd} after {frees} free(s) -- forget_freed took live "
                       f"records with the dead ones")
    if w0[1] > 0 and wp < w0[1]:
        return False, (f"set off with {w0[1]} people wired and came back to "
                       f"{wp} after {frees} free(s) -- forget_freed took live "
                       f"records with the dead ones")
    return True, (f"a body got {sweep:.1f} deg round the ring at its furthest "
                  f"({sweep / cell_deg:.1f} cells) and ended {swept:.1f} deg "
                  f"from where it set off; the loader "
                  f"took {loads} loads and {frees} frees, never held more than "
                  f"{peak:,} triangles (budget {bar:,}), and finished with "
                  f"{wd} doors, {wp} people and "
                  f"{int(d.get('wired_interact', 0))} interactables wired, "
                  f"against {w0[0]}/{w0[1]}/{w0[2]} when it set off")


def deck_verdict(d):
    """Pass/fail for a deck, in the terms milestone W2 is written in."""
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if float(d.get("drop", 0)) > MAX_DECK_DROP_M:
        return False, (f"dropped {float(d['drop']):.2f} m from a spawn 50 mm "
                       f"above the shell -- the floor is not where it says")
    if float(d.get("moved_1s", 0)) < MIN_WALK_M:
        return False, f"walked {float(d.get('moved_1s', 0)):.2f} m in a second"
    off, tot = (d.get("offfloor", "0/0").split("/") + ["0"])[:2]
    if int(off) > 0:
        return False, (f"left the floor for {off} of {tot} frames -- it walked "
                       f"off the deck")
    # -- AND THE CORRIDOR'S CROWD IS WALKING -------------------------------
    # They are instances against the shared crowd library, not geometry in the
    # deck, so the only thing that can tell whether they MOVE is a physics run.
    # A crowd that stands still is a crowd of statues wearing a walk pose,
    # which reads worse than statues.
    if int(d.get("walkers", 0)) > 0:
        travelled = float(d.get("crowd_travel_m", 0.0))
        if travelled < CROWD_TRAVEL_MIN_M:
            return False, (f"{d['walkers']} walkers were instanced and the "
                           f"crowd covered {travelled:.0f} m between them -- "
                           f"they are statues wearing a walk pose")
        # AND THE LOD LADDER IS USED. The crowd covers the same distance
        # whatever level it is drawn at, so `crowd_travel_m` cannot tell a
        # working ladder from a dead one -- only the histogram can. More than
        # one rung in use is the claim; a single rung means every walker is
        # being drawn at the bake's one level again, which is the state this
        # replaced.
        lods = d.get("crowd_lods", "")
        if lods:
            # `2:3/4:5/8:126,nearest=6.2` -- rungs are separated by `/` and
            # the nearest-distance field by `,`. Splitting on the comma found
            # one "rung" and failed a working ladder.
            rungs = [p for p in lods.split(",")[0].split("/") if ":" in p]
            if len(rungs) < 2:
                return False, (f"{d['walkers']} walkers are all on one LOD "
                               f"rung ({lods}) -- the ladder is not being "
                               f"used, so the near figure is as coarse as the "
                               f"far one")
    if "goto_best_m" in d:
        near = float(d["goto_best_m"])
        if near > ARRIVED_M:
            return False, (f"got within {near:.2f} m of {d['goto']} from "
                           f"{float(d['goto_start_m']):.1f} m away -- the way "
                           f"in is blocked")
        # AND SOMEBODY LOOKED UP. `facing_err_deg` is the angle between where
        # the nearest inhabitant ended up facing and the direction to the
        # player. "Did they turn" is not the question -- a body rotated by a
        # wrong yaw convention turns just as far as one rotated correctly and
        # reports the same number. This asks whether they are looking AT you.
        note = ""
        # THE ASSERTION BELOW USED TO VANISH WHEN ITS SUBJECT BROKE. Every NPC
        # check here is guarded by `if "noticed" in d`, and `noticed` is only
        # printed when `walk.gd` has a live `_people` node -- so when
        # `npc.gd` failed to parse and every call to it threw, the tokens
        # simply stopped appearing and the deck went on PASSING. A gate that
        # disappears when the thing it tests is broken is worse than no gate,
        # because it prints PASS.
        #
        # Actors were written beside the mesh, so they must be reported.
        if d.get("actors_expected") and "noticed" not in d:
            return False, ("the cast list was passed and the verdict carries "
                           "no `noticed` -- godot/scripts/npc.gd did not load, "
                           "so nobody on this deck exists at runtime")
        if "noticed" in d:
            err = float(d.get("facing_err_deg", -1.0))
            if int(d["noticed"]) < 1:
                return False, (f"reached {d['goto']} and NOBODY noticed -- "
                               f"{d.get('turned_deg')} deg turned")
            if err < 0 or err > FACING_TOL_DEG:
                return False, (f"reached {d['goto']}; {d['noticed']} noticed "
                               f"but the nearest is {err:.0f} deg off facing "
                               f"the player -- the yaw convention is wrong")
            note = (f", {d['noticed']} of the room look up "
                    f"({float(d['turned_deg']):.0f} deg turned, {err:.0f} deg "
                    f"off)")
        # THE DISTANCE BAR, WHICH HAS NEVER RUN ON A DECK TEST. It sits after
        # this branch's `return True`, and `--deck` always sets a `--goto`, so
        # every deck run since the bar was written has taken the early exit
        # past it. This file's own docstring advertises `traverse_m` and
        # `offfloor` as the pair milestone W2 is asserted with; only one of
        # them was ever checked. Moved above the return rather than deleted:
        # under a goto it is a "something is snagging" test, which is weaker
        # than what its comment claims but is not nothing.
        got0 = float(d.get("traverse_m", 0))
        if got0 < MIN_TRAVERSE_M:
            return False, (f"covered {got0:.1f} m of corridor on the way to "
                           f"{d['goto']}, under the {MIN_TRAVERSE_M:.0f} m "
                           f"bar -- something is snagging")
        return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg, "
                      f"{d['doors']} doors; a body spawns in the corridor and "
                      f"WALKS INTO {d['goto']} "
                      f"({float(d['goto_start_m']):.1f} m -> {near:.2f} m), "
                      f"never leaving the floor{note}")
    got = float(d.get("traverse_m", 0))
    if got < MIN_TRAVERSE_M:
        return False, (f"covered {got:.1f} m of corridor, under the "
                       f"{MIN_TRAVERSE_M:.0f} m bar -- something is snagging")
    # -- AND IT ENDED SOMEWHERE ELSE ---------------------------------------
    # THE STRONG FORM, and it is the whole reason this branch was made
    # reachable. Path length is not progress: the same deck steered at a room
    # 6.3 m away reports `traverse_m=125.93 net_m=0.35` -- 126 m of walking
    # that ends where it started, because the body arrives and mills. A body
    # pacing on the spot satisfies a distance-covered bar exactly as well as
    # one crossing the deck, which is 3v's lesson ("report DISTANCE COVERED,
    # not 'did it move'") one level up.
    #
    # The bar is the same 63 m, applied to DISPLACEMENT. Measured with nobody
    # steering: `traverse_m=125.87 net_m=123.95 sweep_deg=34.07` -- 98.5% of
    # the path is progress, 34 degrees of ring, 1.7 streaming cells. So 63 m
    # leaves half the measurement in hand while rejecting the 0.35 m that the
    # weak form passes.
    net = float(d.get("net_m", 0))
    if net < MIN_TRAVERSE_M:
        return False, (f"covered {got:.1f} m of corridor but ended {net:.1f} m "
                       f"from where it set off, under the {MIN_TRAVERSE_M:.0f} "
                       f"m bar -- it walked without going anywhere")
    return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg; a "
                  f"body spawns at {d['spawn_at']}, walks {got:.1f} m with "
                  f"nobody steering it, ends {net:.1f} m away "
                  f"({float(d.get('sweep_deg', 0)):.0f} deg round the ring) "
                  f"and never leaves the floor")


def use_verdict(d):
    """Did a player walk up to a declared interactable and USE it?

    THE SMALLEST COMPLETE LOOP THAT WAS STILL MISSING. W5 closed spawn -> walk
    -> a door opens -> an NPC reacts, and a door is the one thing on the station
    that works by walking at it. `directory.PLACES["interacts"]` declares 357
    other things a player can use and until now not one of them could be.

    Four claims, in the order a player meets them, and every one of them is a
    token this function requires rather than tolerates:

      interactables  the build has things to use at all
      want_present   the specific object is in the world
      prompt         the eye found it -- looking at it says what it is
      used           the key press landed on it, and it responded
    """
    if "error" in d:
        return False, d["error"]
    # THE ABSENCE OF A TOKEN IS A FAILURE, NOT A SKIP. `interact_expected` is
    # set from the sidecar this process wrote, so a verdict with no `used` in it
    # means `godot/scripts/interact.gd` did not load -- which is exactly how the
    # NPC assertions silently vanished for six runs while the deck printed PASS.
    if d.get("interact_expected") and "interactables" not in d:
        return False, (f"a sidecar of {d.get('interact_rows')} interactables "
                       f"was passed and the verdict carries no "
                       f"`interactables` -- godot/scripts/interact.gd did not "
                       f"load, so nothing on this deck can be used")
    if "use_want" not in d:
        return False, ("no pressable interactable was found to walk to -- "
                       "every declared use in this room resolves to nothing")
    for tok in ("prompt", "used", "use_count", "prompt_frames", "want_present",
                "use_travel_mm", "used_verb", "want_range_m", "used_responds",
                "used_prompt", "no_mesh"):
        if tok not in d:
            return False, f"the verdict carries no `{tok}`"
    want = d["use_want"]
    if int(d.get("interactables", 0)) < 1:
        return False, (f"{d['interact_rows']} interactables were written "
                       f"beside the mesh and the engine wired 0 -- the group "
                       f"names in the sidecar are not the names in the glb")
    if d["want_present"] != "true":
        return False, (f"{want} is not among the {d['interactables']} "
                       f"interactables the engine wired")
    if int(d["prompt_frames"]) < 1:
        return False, (f"the body ended {float(d['want_range_m']):.2f} m from "
                       f"{want} and was never prompted for anything at all "
                       f"-- the eye ray finds nothing")
    # THE PROMPT IS ASSERTED AT THE MOMENT OF USE, NOT AT THE END OF THE RUN.
    # The first version of this checked the LIVE prompt in the verdict and
    # failed a run that had worked: the body walks at 4.2 m/s, it is prompted
    # for six frames on the approach, presses the key, and keeps going -- so by
    # the last frame the eye is past the thing and the prompt is empty. That
    # tested where the body finished, not whether the player was ever told what
    # they were about to use. `used_prompt` is the sentence that was on screen
    # when the key went down.
    if d["used"] != want:
        return False, (f"a prompt appeared on {d['prompt_frames']} frames and "
                       f"{want} was never used (used={d['used']}, "
                       f"use_count={d['use_count']}) -- the eye found "
                       f"something else")
    if d["used_prompt"] in ("", "-"):
        return False, (f"{want} was used with NO prompt on screen -- a player "
                       f"would have pressed a key at nothing")
    rng = float(d["want_range_m"])
    if rng > USE_RANGE_M:
        return False, (f"used {want} from {rng:.2f} m, past the "
                       f"{USE_RANGE_M:.1f} m reach -- the prompt is firing "
                       f"across the room")
    # AND IT RESPONDED. A `use()` that returns true and moves nothing looks
    # identical to one that works, so the claim is the object's own measured
    # travel. `sit`, `rest` and `serve` have no press behind them yet and say so
    # rather than pretending -- see `station/interact.py::RESPONDS`.
    moved = float(d["use_travel_mm"])
    resp = f", and the object moved {moved:.1f} mm"
    if d["used_responds"] == "true":
        if moved <= 0.0:
            return False, (f"used {want} ({d['used_verb']}) and the object did "
                           f"not move -- `use()` returned true and nothing "
                           f"happened")
    else:
        resp = (f" (verb `{d['used_verb']}` has no response behind it yet: "
                f"what answers a `{d['used_verb']}` is a body, not a prop)")
    return True, (f"a body walks up to the {d['use_want_label']} in "
                  f"{d['use_want_place']}, is told "
                  f"\"{d['used_prompt'].replace('_', ' ')}\" and USES it: "
                  f"`{d['used_verb']}` from {rng:.2f} m after "
                  f"{d['prompt_frames']} prompted frames{resp}. "
                  f"{d['interactables']} interactables wired on this deck, "
                  f"{d.get('pressable')} pressable ({d.get('verbs')})")


def verdict(d):
    """Pass/fail for one room, with the reason a player would give."""
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if float(d.get("drop", 0)) > MAX_DROP_M:
        return False, f"fell {float(d['drop']):.1f} m -- the deck has no collision"
    if float(d.get("moved_1s", 0)) < MIN_WALK_M:
        return False, (f"walked {float(d.get('moved_1s', 0)):.2f} m in a second "
                       f"-- the body is stuck")
    return True, (f"stands and walks {float(d['moved_1s']):.2f} m/s, "
                  f"{d['meshes']} colliders")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", type=int, default=6,
                    help="how many rooms to test (they are slow)")
    ap.add_argument("--keys", default="",
                    help="comma-separated room keys, overrides --rooms")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--deck", default="",
                    help="also walk an assembled deck, as sector/ring/deck "
                         "(e.g. blue/0/0)")
    ap.add_argument("--deck-only", action="store_true")
    ap.add_argument("--no-doors", action="store_true",
                    help="negative control: leave the doors inert, so the "
                         "closed panels stay solid and the body must NOT get in")
    ap.add_argument("--z", type=float, default=None,
                    help="which z-cluster of the deck to walk. A deck is not "
                         "a z-slice: blue/0/0 has six clusters over 1,100 m "
                         "and they are six different places")
    ap.add_argument("--traverse", type=int, default=None,
                    help="physics frames of continuous walking on the deck")
    ap.add_argument("--bump", action="store_true",
                    help="steer at the nearest INHABITANT instead of a room, "
                         "and check they are something you bump into")
    ap.add_argument("--use", action="store_true",
                    help="walk up to a declared interactable, be prompted, and "
                         "use it. The control strips that object out of the "
                         "render mesh and walks the identical route again")
    ap.add_argument("--stream", action="store_true",
                    help="walk the body round the ring far enough that the "
                         "streaming window must move, and assert the loader "
                         "loads AND frees. The control turns streaming off")
    ap.add_argument("--build-only", action="store_true",
                    help="assemble the deck and write godot/play.json, then "
                         "stop. This is what tools/play.sh runs before handing "
                         "the station to a person instead of to a test")
    ap.add_argument("--steps", type=int, default=None,
                    help="frames for the four-heading probe (half each leg). "
                         "The control for --no-goto: at the old 120 the legs "
                         "are speed-limited and tie")
    ap.add_argument("--no-goto", action="store_true",
                    help="walk one heading for the whole traverse instead of "
                         "steering at a room. The strong form of the distance "
                         "bar, and the mode nothing had ever run")
    ap.add_argument("--reach", action="store_true",
                    help="how much of each declared interactable the runtime's "
                         "name test actually grabs. No engine needed")
    ap.add_argument("--control", action="store_true",
                    help="with --reach, ALSO build with the pre-4y part naming "
                         "and show the reach collapse")
    a = ap.parse_args()

    # -- HOW MUCH OF AN OBJECT IS THE OBJECT ---------------------------------
    # Offline, over the emitted mesh, because this is a question about names
    # and spans and the engine cannot answer it any better than the generator
    # can. `--use` proved a press works; this proves it presses the whole thing.
    if a.reach:
        return _reach_main(a)

    # -- BUILD IT FOR SOMEBODY TO PLAY, and do not run a test -----------------
    # No Godot binary is needed to assemble a deck, and requiring one here would
    # mean the content pipeline could not run without the engine.
    if a.build_only:
        sector, ring, deck = (a.deck or DEFAULT_PLAY_DECK).split("/")
        man = walk_deck(sector, int(ring), int(deck), None, z_m=a.z,
                        goto_key=(a.keys.split(",")[0] if a.keys else None),
                        build_only=True)
        man["deck"] = f"{sector}/{ring}/{deck}"
        with open(PLAY_MANIFEST, "w") as f:
            json.dump(man, f, indent=1)
        if a.json:
            print(json.dumps(man))
        else:
            print(f"built {man['deck']}: {man['render_tris']:,} render "
                  f"triangles, {man['collision_tris']:,} collision, "
                  f"{man['rooms']} room(s), {man['actors']} actors, "
                  f"{man['crowd']} in the crowd, {man['interact_rows']} "
                  f"interactables. Spawn {man['spawn_at']}.")
            print(f"  manifest {PLAY_MANIFEST}")
        return 0

    godot = godot_binary()
    if godot is None:
        print("no double-precision Godot binary; see docs/godot-binary.md")
        return 1

    if a.deck or a.deck_only:
        sector, ring, deck = (a.deck or "blue/0/0").split("/")
        d = walk_deck(sector, int(ring), int(deck), godot,
                      traverse=a.traverse, no_doors=a.no_doors, z_m=a.z,
                      no_goto=a.no_goto, steps=a.steps)
        drum = (sector, int(ring)) in D.NOT_RING_DECKS
        if drum:
            import drum_walk as DW                              # noqa: PLC0415
            good, why = DW.walk_verdict(d)
        else:
            good, why = deck_verdict(d)
        print(f"  {'PASS' if good else 'FAIL'}  "
              f"{'drum' if drum else 'deck'} {sector}/{ring}/{deck}  {why}")
        # A VERDICT THAT FAILS SHOULD NOT NEED A SECOND RUN TO DIAGNOSE. The
        # deck run is six minutes; printing the tokens it already has costs
        # nothing and is the difference between "something is snagging" and
        # knowing which leg, how far, and whether it left the floor.
        if True:
            print("        " + " ".join(
                f"{k}={d[k]}" for k in
                ("legs", "traverse_m", "net_m", "sweep_deg", "offfloor",
                 "drop", "moved_1s", "on_floor", "goto_best_m")
                if k in d))
        # -- THE CONTROL FOR THE DISPLACEMENT BAR ---------------------------
        # It costs NO engine time, because `deck_verdict` is a pure function of
        # the verdict dict -- so the negative case can be fed to the real
        # function rather than argued about in a comment. And the negative case
        # is not invented: 0.35 m is what the SAME deck reports under a goto,
        # walking the same 126 m of path and ending where it started. If a
        # verdict carrying that displacement still passes, the bar is inert.
        if good and a.no_goto and not drum:
            wok, wwhy = deck_verdict(dict(d, net_m=f"{GOTO_NET_M:g}"))
            if wok:
                print(f"  FAIL  the displacement bar is inert -- this run's "
                      f"verdict with the goto walk's {GOTO_NET_M} m of "
                      f"displacement substituted still passed")
                good = False
            else:
                print(f"        control: the same verdict carrying the goto "
                      f"walk's {GOTO_NET_M} m of displacement FAILS -- "
                      f"\"{wwhy}\"")

        # THE NEGATIVE CONTROL, and it is the whole reason the door claim means
        # anything. A body that reaches the room proves the route is open; it
        # does not prove the DOOR opened it, because a door-shaped hole in the
        # wall gives exactly the same number. So the same run is repeated with
        # the doors inert: the closed panels stay solid and the body must NOT
        # get in. If both runs pass, the doors are scenery.
        # The drum has no doors, so `--no-doors` is not a control there --
        # running it would compare a thing against itself and pass.
        # `--no-goto` walks one heading and never claims to reach a named room,
        # so there is no arrival for inert doors to withhold. Running the
        # control here would read `goto_best_m` off a verdict that has none,
        # default it to 0.00, and report "the body still reached it".
        if good and not a.no_doors and not drum and not a.no_goto:
            n = walk_deck(sector, int(ring), int(deck), godot,
                          traverse=a.traverse, no_doors=True)
            blocked, _w = deck_verdict(n)
            near = float(n.get("goto_best_m", 0.0))
            if blocked:
                print(f"  FAIL  the doors are scenery -- with them inert the "
                      f"body still reached {d['goto']} ({near:.2f} m)")
                good = False
            else:
                print(f"        control: with the doors inert the body is "
                      f"stopped {near:.2f} m short. The door is what opens "
                      f"the way.")
        if good and int(d.get("walkers", 0)) > 0:
            _lods = d.get("crowd_lods", "").replace(",", " ")
            print(f"        {d['walkers']} walkers instanced from the shared "
                  f"crowd library and they WALK: "
                  f"{float(d['crowd_travel_m']):,.0f} m covered between them, "
                  f"0 triangles of their own in the deck"
                  + (f"; LOD {_lods}" if _lods else ""))
        if good:
            print(f"        {d['render_tris']:,} render triangles, "
                  f"{d['collision_tris']:,} collision "
                  f"({d['collision_tris'] / d['render_tris'] * 100:.1f}%)")
        # -- AND A PERSON IS SOMETHING YOU BUMP INTO -----------------------
        # `is_solid` keeps inhabitants out of the STATIC collision on purpose,
        # so nothing in the static mesh can answer this. The capsule is built
        # at runtime by `npc.gd::_give_body`, and the only honest test is to
        # walk at somebody: with the capsule the body stops about a radius
        # short, without it the body walks through them and arrives.
        if a.bump and not drum:
            hit = walk_deck(sector, int(ring), int(deck), godot,
                            traverse=a.traverse, z_m=a.z, bump=True)
            through = walk_deck(sector, int(ring), int(deck), godot,
                                traverse=a.traverse, z_m=a.z, bump=True,
                                no_npc_collision=True)
            stop = float(hit.get("goto_best_m", -1.0))
            walk_through = float(through.get("goto_best_m", -1.0))
            r = float(hit.get("bump_r_m", 0.0))
            who = hit.get("bump_who") or hit.get("bumped", "somebody")
            # NO CANDIDATE IS NOT A FAILED COMPARISON. `_actors.json` carries
            # group, place, pose, who, x, y, z and yaw -- and no `r_m` or
            # `h_m`, so `npc.gd::_give_body` returns early on every one of the
            # 21 baked inhabitants and none of them has ever had a capsule.
            # With no candidate this test steered at the room target instead
            # and reported "0.04 m with the capsule on and 0.04 m with it off",
            # which reads as a measured refutation and is an empty sample.
            if hit.get("bumped") is None:
                print(f"  FAIL  the bump test had nothing to walk into: no "
                      f"actor in _actors.json carries `r_m`, so "
                      f"`_give_body` returns early and the baked "
                      f"inhabitants on this deck have no capsule at all. "
                      f"The crowd's walkers do; the CAST does not.")
                good = False
            elif stop < 0 or walk_through < 0:
                print(f"  FAIL  the bump test did not run  {hit.get('error')} "
                      f"/ {through.get('error')}")
                good = False
            elif stop <= walk_through + BUMP_MARGIN_M:
                print(f"  FAIL  inhabitants are not solid -- the body got "
                      f"{stop:.2f} m from {who} with their capsule on and "
                      f"{walk_through:.2f} m with it off. A person you walk "
                      f"through is a hologram.")
                good = False
            else:
                print(f"        a person is SOLID: walking straight at {who} "
                      f"(r {r:.2f} m) the body is stopped {stop:.2f} m away; "
                      f"control: with their capsule off it reaches "
                      f"{walk_through:.2f} m and walks through them.")
        # -- AND THE LOADER LOADS AND FREES WHILE SOMEBODY WALKS -----------
        if a.stream and not drum:
            # BOTH WAYS ROUND, because which direction this corridor is open
            # in is a property of the content and not of the loader. Blue 0/0
            # is blocked 27 m clockwise and 14 m anticlockwise from its spawn;
            # a gate that only walked one way would report the loader broken.
            st = walk_deck(sector, int(ring), int(deck), godot,
                           traverse=a.traverse or 3600, z_m=a.z,
                           stream_deg=STREAM_WALK_DEG)
            if int(st.get("frees", 0)) < 1:
                st = walk_deck(sector, int(ring), int(deck), godot,
                               traverse=a.traverse or 3600, z_m=a.z,
                               stream_deg=-STREAM_WALK_DEG)
            sok, swhy = stream_verdict(st)
            print(f"  {'PASS' if sok else 'FAIL'}  stream  {swhy}")
            if not sok:
                good = False
            else:
                # THE CONTROL: the same walk with `--no-stream` holds the deck
                # whole. If the subject and the control report the same
                # resident geometry, nothing is being streamed and the numbers
                # above are describing something else.
                nc = walk_deck(sector, int(ring), int(deck), godot,
                               traverse=a.traverse or 3600, z_m=a.z,
                               stream_deg=STREAM_WALK_DEG, no_stream=True)
                if "cells" in nc:
                    print(f"  FAIL  control: --no-stream still streamed "
                          f"({nc.get('cells')})")
                    good = False
                else:
                    print(f"        control: with --no-stream the same walk "
                          f"holds all {st['render_tris']:,} triangles at once "
                          f"and reports no cells at all; streaming held "
                          f"{int(st['peak']):,}.")

        # -- AND SOMETHING IN IT IS USABLE ---------------------------------
        # `directory.PLACES["interacts"]` has declared what a player can use in
        # every room since layer 1 and nothing has ever read it as a mechanic.
        # This walks a body up to one of them and presses the key.
        if a.use and not drum:
            u = walk_deck(sector, int(ring), int(deck), godot,
                          traverse=a.traverse, z_m=a.z, use=True)
            uok, uwhy = use_verdict(u)
            print(f"  {'PASS' if uok else 'FAIL'}  use  {uwhy}")
            if not uok:
                good = False
            else:
                # THE NEGATIVE CONTROL, and it is a control on the CONTENT
                # rather than on this file's own switch. `--no-interact` would
                # only prove that turning the feature off turns it off. This
                # deletes the object's triangles from the render mesh -- all of
                # them, parts included, because `dressing.machine`'s outer span
                # covers the parts -- and leaves everything else identical,
                # including the collision box, so the body walks the same route
                # to the same place and there is simply nothing there.
                n = walk_deck(sector, int(ring), int(deck), godot,
                              traverse=a.traverse, z_m=a.z,
                              strip=u["use_want"])
                nok, _nwhy = use_verdict(n)
                if nok:
                    print(f"  FAIL  the prompt is not reading the mesh -- with "
                          f"{u['use_want']} deleted from it the body was still "
                          f"prompted and still used it")
                    good = False
                else:
                    # NOT A COMPARISON OF TOTALS. It used to read "wires 4
                    # instead of 5", which was true while an object was
                    # whatever meshes happened to match its name. Now that a
                    # row carries its PARTS, deleting one object's outer span
                    # re-partitions the rest -- groups it used to own become
                    # unclaimed or fall to a neighbour -- so the total can go
                    # UP, and it did: 8 against 7. The claim was never about
                    # the count. It is that the thing is gone and cannot be
                    # used.
                    print(f"        control: with {n.get('stripped_tris')} "
                          f"triangles of {u['use_want']} deleted from the "
                          f"render mesh the prompt reads "
                          f"`{n.get('prompt', '?')}` and use_count is "
                          f"{n.get('use_count', '?')} -- the object a player "
                          f"was pressing is not there. What you look at is "
                          f"what is there.")
        if a.deck_only:
            return 0 if good else 1
        if not good:
            return 1

    if a.keys:
        keys = [k for k in a.keys.split(",") if k]
    else:
        built = {os.path.splitext(f)[0] for f in os.listdir(
            os.path.join(ROOT, "station/generated/scene/interior"))
            if f.endswith(".glb")}
        # ONLY rooms.py's own places. The bespoke modules -- alien_sector, the
        # Zocalo, C&C -- build their own geometry in their own frames and
        # `rooms.spawn_m` has nothing to say about them; asking it anyway threw
        # a KeyError on a location whose `interacts` list rooms.PROPS does not
        # carry. They need their own spawn points and get their own entry here
        # once they have them.
        gen = dr._generated_keys()
        keys = [q["key"] for q in dr.PLACES
                if q["key"] in built and q["key"] in gen][:a.rooms]

    rows, ok, fail = [], 0, 0
    for k in keys:
        d = walk_room(k, godot)
        good, why = verdict(d)
        rows.append({**d, "passes": good, "why": why})
        if good:
            ok += 1
        else:
            fail += 1
        if not a.json:
            print(f"  {'PASS' if good else 'FAIL'}  {k:22s} {why}")

    if a.json:
        print(json.dumps(rows, indent=2))
        return 0 if fail == 0 else 1

    print(f"\n{ok}/{ok + fail} rooms are walkable")
    if fail:
        print("A location nobody can stand in is not built, whatever its "
              "layer number says.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
