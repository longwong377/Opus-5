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
import roomnav as RN                                            # noqa: E402
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
# How close to the middle of a room counts as being in it. A body that stops in
# the doorway is not inside; one standing anywhere in the far half is.
ARRIVED_M = 1.5
# The deck spawns a body 50 mm above its floor, so a drop of more than a step
# means it is not where the shell says the floor is.
#
# MEASURED ALONG THE BODY'S OWN UP, and it was not. This asserted on `drop`,
# which is `spawn.distance_to(rest)` -- a 3D displacement -- while its own
# failure message is a claim about the floor's radius. On a deck with 134 people
# walking down it the two are nothing like each other: session 4h measured
# `drop=0.319` against `drop_up=0.043` on the same frame, so the body fell 43 mm
# onto a shell 50 mm below it exactly as designed, and was pushed 316 mm ALONG
# the corridor by people walking past it during the 2.5 s it stood there
# settling. `drop` is still printed and still in the verdict; it is simply not
# the number this bound is about.
MAX_DECK_DROP_M = 0.30
# How close to actually facing the player the nearest inhabitant has to end up.
# Generous: they turn at a human rate and the walk ends when the player arrives,
# so a few degrees of lag is a person still turning, not a person facing wrong.
FACING_TOL_DEG = 25.0

# -- STREAMING: IS A STREAMED CELL A PLACE, OR A SHELL? ---------------------
# Every other gate in this file loads one glb whole and wires it once, so none
# of them can fail for a station whose doors are solid because the geometry
# arrived late -- which is exactly what `docs/streaming-4g.md` shipped and
# `docs/streaming-doors-4g.md` fixed. That fix has never been in CI.
STREAM_CELLS = os.path.join(
    ROOT, "station/generated/scene/deck/cells_blue_0_0/cells.json")
STREAM_DECK = os.path.join(ROOT, "station/generated/scene/deck")
# The object the monolithic `--deck --use` gate picks on this cluster, named so
# the two gates walk up to the SAME thing and a difference is the streaming.
STREAM_USE = "docking_bays__prop_bay_control_booth"
# Two cell lengths less a margin: a run that crosses one boundary and stops has
# not shown the hand-off repeats.
MIN_STREAM_FLOOR_M = 100.0
# HOW PEOPLE ARE MADE SOLID. `godot/scripts/npc.gd` can either leave them on the
# world collision layer for `move_and_slide` to resolve -- which costs the body
# its floor for as long as it is touching one, and is what shoved the player in
# `docs/streaming-doors-4g.md` 4c -- or put them on their own layer and separate
# the player from them by hand, across the floor plane only. Asserted rather than
# assumed, because a control that silently became the subject is a gate
# measuring nothing.
STREAM_COLLIDER = "separate/every_frame"


def godot_binary():
    """The Godot this project drives, or None. $GODOT wins.

    THE SEARCH ORDER STARTS AT $GODOT AND THAT IS THE WINDOWS FIX. This
    function knew exactly one path -- a Linux one, with `double` in the
    filename -- so on Windows it returned None however many working binaries
    were present, and every one of the five modules that borrow it printed
    "no double-precision Godot binary. run: bash tools/build_godot.sh" at a
    runner which had just downloaded a perfectly good engine and put it in
    $GODOT. Forty minutes of world build died on that line in run 3.

    THE MESSAGE NAMED THE WRONG CAUSE, which is why it cost three runs to see.
    Precision was the only reason this project had ever failed to find an
    engine, so the not-found branch said "precision" -- but the actual fault
    was a finder that could not look outside one directory on one OS. A
    diagnostic that can only describe one failure will describe that one
    whatever actually happened.
    """
    import shutil                                             # noqa: PLC0415
    env = os.environ.get("GODOT", "").strip()
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    cand = ("/home/user/godot-build/godot-4.4-stable/bin/"
            "godot.linuxbsd.editor.double.x86_64")
    if os.path.exists(cand) and os.access(cand, os.X_OK):
        return cand
    import glob                                               # noqa: PLC0415
    for c in glob.glob("/home/user/godot-build/*/bin/godot.linuxbsd.*.double.*"):
        if os.access(c, os.X_OK):
            return c
    return shutil.which("godot") or shutil.which("godot.exe")


def godot_is_double(path):
    """Whether `path` is the precision=double build, by this project's naming.

    REPORTING ONLY -- nothing refuses a single-precision binary any more. The
    naming convention is the build's own: scons writes `precision=double` into
    the filename and nowhere else a script can reach without launching it.
    """
    return "double" in os.path.basename(path or "").lower()


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


def room_target(meta, place, verts=None, tris=None, groups=None, **kw):
    """A point on the floor of a room a body can actually STAND on.

    ON THE FLOOR, not at eye or waist height. Aiming at a room's mid-height left
    an irreducible 0.85 m in the "how close did it get" number, because a body
    standing on the deck can never close a radial offset -- which reads as a
    near miss and is nothing of the kind.

    AND NOT INSIDE THE FURNITURE, which is `roomnav.py`'s answer and not a
    second one. The register's centre point is where the ROOM is, not where a
    person can be, and the two stopped being the same thing the moment V1's
    form-follows-function pass put real fittings in these rooms. Without a mesh
    this is the register's centre point exactly as it always was, so a caller
    that has no collision to offer changes nothing.
    """
    if not verts or not tris:
        a = math.radians(place["angle_deg"])
        r = meta["floor_r_m"] - 0.05
        return (r * math.cos(a), r * math.sin(a), place["z_m"])
    return RN.standpoint(meta, place, verts, tris, groups, **kw)


# How near a path waypoint the body has to get before it aims at the next one.
# Loose on purpose: these are aim points on a corridor's centre line, not
# apertures. The waypoints that ARE in an aperture get `route_walk.door_tol_m()`
# from the module that owns that question -- see `deck_path`.
WAYPOINT_TOL_M = 0.5


def _arc_inside(meta, radius, a0, a1, z):
    """Points along the ring from a0 to a1 THAT STAY ON THE BUILT CORRIDOR.

    `route_walk._arc_points` takes the short way round unconditionally, and
    `route_walk`'s own section 2.1 is the warning: *"a ring corridor runs one
    way round, and the short way is often not it."* A corridor covers an ARC,
    not the whole ring, so the short way between two of its angles can leave the
    floor entirely. Measured before this existed: a body following a path to
    `vorlon_berth` cleared 13 of 24 waypoints and then fell -- **1,089 of 1,800
    frames in the air**, 1,677 m of "journey".

    The arc the shell actually swept is recorded by `collision.corridor_shell`
    in its own meta, so it is READ rather than recomputed -- the same rule
    `agenda.corridor_span` states: a route laid against a recomputed arc can
    describe a different corridor from the one that was written. With no arc
    recorded, this falls back to the short way, which is what every caller had
    before.
    """
    import route_walk as RW                                      # noqa: PLC0415
    lo = meta.get("start_deg")
    span = meta.get("arc_deg")
    if lo is None or span is None:
        return RW._arc_points(radius, a0, a1, z)
    lo, span = float(lo), float(span)
    u0 = (a0 - lo) % 360.0
    u1 = (a1 - lo) % 360.0
    if u0 > span + 1e-6 or u1 > span + 1e-6:
        # One of the ends is not on this corridor at all; the short way is no
        # worse than anything else and the caller's own gate will say so.
        return RW._arc_points(radius, a0, a1, z)
    n = max(1, int(math.ceil(abs(u1 - u0) / RW.RING_STEP_DEG)))
    return [RW._at(radius, lo + u0 + (u1 - u0) * i / n, z) for i in range(n + 1)]


def deck_path(schema, profile, meta, place, verts, tris, spawn):
    """Every waypoint from a body standing in the corridor to inside a room.

    THREE PIECES AND NONE OF THEM IS AUTHORED HERE. The arc along the ring is
    `route_walk._arc_points` at that module's own faceting; the two aim points
    either side of the doorway are its discipline, because a body that turns
    while standing in an aperture meets the jamb; and the way across the room,
    past its furniture, is `roomnav.approach`. This function chooses the order.

    Returns [] when the room is not in this shell or has no door in it, and the
    caller then falls back to the straight steer -- so a deck this cannot route
    on behaves exactly as it did before.
    """
    import route_walk as RW                                      # noqa: PLC0415
    import deck as D_                                            # noqa: PLC0415
    door = next((r for r in meta.get("rooms", ())
                 if r["key"] == place["key"]), None)
    if door is None:
        return []
    fr, cz = meta["floor_r_m"], meta["z_m"]
    sx, sy, _sz = spawn
    start_deg = math.degrees(math.atan2(sy, sx))
    zh = D_.room_interior_half_m(schema, profile, place)
    # TOWARD THE CORRIDOR: a room's door is in the wall that faces it, and
    # `place.z + zh` is the FAR wall for a room on the other side. See
    # docs/room-reach-4k.md section 2.
    toward = 1.0 if cz > place["z_m"] else -1.0
    z_inner = place["z_m"] + toward * zh
    pts = list(_arc_inside(meta, fr, start_deg, door["door_deg"], cz))
    pts.append(RW._at(fr, door["door_deg"], z_inner - toward * 0.5))
    pts += [list(q) for q in room_approach(meta, place, verts, tris,
                                           meta.get("groups"),
                                           from_pt=pts[-1], z_half=zh)]
    # No two consecutive waypoints in the same place: a zero-length hop is a
    # waypoint the body is already at, and it would be skipped anyway.
    out = []
    for q in pts:
        if not out or math.dist(out[-1], q) > 1e-6:
            out.append(list(q))
    return out


def room_approach(meta, place, verts, tris, groups=None, **kw):
    """The way in from the door AND the spot, for a caller laying a route.

    `room_target` is this list's last element. Kept as two names because most
    callers want a point and one wants the whole way in -- never as two
    computations, which is how the route and the manifest came to name
    different points in the first place.
    """
    if not verts or not tris:
        return [room_target(meta, place)]
    return RN.approach(meta, place, verts, tris, groups, **kw)


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
    # THE SPANS, NOT JUST THE NAMES. `interact.resolve` breaks an alias tie on
    # how many triangles carry each name -- otherwise "operate the console"
    # points at `cc_console_leg`. Handing it the same span list the audit uses
    # is what stops the runtime and the audit resolving differently.
    rows = IX.sidecar({nm for nm, _a, _b in groups}, groups)
    out = []
    for r in rows:
        box = group_aabb(verts, tris, groups, r["group"])
        if box is None:
            continue
        lo, hi, n = box
        r["centre"] = [(lo[k] + hi[k]) / 2.0 for k in range(3)]
        r["half"] = [max((hi[k] - lo[k]) / 2.0, 0.0) for k in range(3)]
        r["tris"] = n
        out.append(r)
    return out


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


def walk_deck(sector, ring, deck, godot, timeout=1800, traverse=None,
              goto_key=None, no_doors=False, z_m=None, bump=False,
              no_npc_collision=False, use=False, strip=None):
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
                       timeout=timeout, godot=godot)

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
    rtgt = room_target(cm, dr.by_key(goto), cv, ct, cm.get("groups"))
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
            if not os.path.exists(lib):
                cv2, ct2, cg2 = _pop.station_crowd_library(lod)
                D.write_obj(lib, cv2, ct2, cg2)
                _glb(lib, lib[:-4] + ".glb")
    _glb(os.path.join(out, f"{stem}.obj"), os.path.join(out, f"{stem}.glb"))
    _glb(os.path.join(out, f"{stem}_col.obj"),
         os.path.join(out, f"{stem}_col.glb"))

    sx, sy, sz = s["spawn"]
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--",
           f"--glb={os.path.join(out, stem + '.glb')}",
           f"--collision={os.path.join(out, stem + '_col.glb')}",
           f"--spawn={sx},{sy},{sz}", "--gravity-mode=drum", "--walk-test",
           f"--traverse={traverse if traverse is not None else TRAVERSE_FRAMES}"]
    # Walking INTO a named place is the claim W2 actually makes, and it is a
    # strictly harder question than "did the body move": it fails when the route
    # is blocked, not only when the body is wedged.
    #
    # AND IT FOLLOWS A PATH NOW, which this comment used to say it could not:
    # *"the target has to be one it can reach without navigating -- Reaching one
    # across the ring needs a path, and there is no pathfinder yet."* Measured,
    # that limitation was not a caveat but a wrong answer: steered straight at
    # `vorlon_berth`, 40 degrees round the ring, the body walked off a CURVED
    # corridor and reported 1,661 m travelled with 1,084 of 1,800 frames in the
    # air -- the falling-body-reporting-a-journey signature, scored as a walk.
    #
    # The path is nobody's new invention: the arc along the ring is
    # `route_walk._arc_points`, the doorway aim points are that module's own
    # discipline (a body that turns while standing in an aperture meets the
    # jamb), and the way across the room is `roomnav.approach`. Imported late
    # because `route_walk` imports THIS module -- one direction only.
    tx, ty, tz = rtgt
    path = deck_path(schema, profile, cm, dr.by_key(goto), cv, ct, s["spawn"])
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
    bumped = None
    if bump:
        cand = [a for a in s.get("actors", ())
                if float(a.get("r_m", 0.0)) > 0.0]
        if cand:
            px, py, pz = s["spawn"]
            bumped = min(cand, key=lambda a: (a["x"] - px) ** 2
                         + (a["y"] - py) ** 2 + (a["z"] - pz) ** 2)
            tx, ty, tz = bumped["x"], bumped["y"], bumped["z"]
    if crowd:
        import populace as _pop2                                # noqa: PLC0415
        _lad = _pop2.crowd_ladder()
        cmd += [f"--crowd={os.path.join(out, stem + '_crowd.json')}",
                # The whole ladder, as `max_m:lod` pairs and one glb each, so
                # the runtime knows both which mesh to use at which distance
                # and where to find it.
                "--crowd-ladder=" + ",".join(
                    f"{hi:g}:{lod}" for hi, lod in _lad),
                "--crowd-glbs=" + ",".join(
                    os.path.join(out, f"crowd_lod{lod}.glb")
                    for _hi, lod in _lad)]
    cmd += [f"--actors={os.path.join(out, stem + '_actors.json')}",
            f"--interact={os.path.join(out, stem + '_interact.json')}",
            f"--goto={tx},{ty},{tz}", f"--door-key={goto}",
            f"--door-travel={K.PROVISIONAL['door_width_m'] / 2.0}"]
    # THE WAY THERE, when there is one and the target is still the room. A
    # `--bump` or `--use` run is steered at a PERSON or an OBJECT rather than at
    # the room's standing point, so its path would end somewhere else; those
    # keep the straight steer they were written against.
    if path and chosen is None and bumped is None:
        cmd += ["--goto-path=" + ";".join(f"{q[0]},{q[1]},{q[2]}" for q in path),
                f"--goto-tol={WAYPOINT_TOL_M}"]
    if chosen is not None:
        cmd += [f"--use-group={chosen['group']}"]
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
    # THE LINE THE GATE JUDGED, kept so a before/after can be quoted rather
    # than re-derived. `--raw` prints it.
    d["verdict"] = m.group(0)
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


def deck_verdict(d):
    """Pass/fail for a deck, in the terms milestone W2 is written in."""
    if "error" in d:
        return False, d["error"]
    if d.get("on_floor") != "true":
        return False, "the body never reached a floor"
    if "drop_up" not in d:
        return False, ("the verdict carries no `drop_up` -- this build of "
                       "godot/scripts/walk.gd cannot say how far the body fell "
                       "as opposed to how far it moved")
    if float(d["drop_up"]) > MAX_DECK_DROP_M:
        return False, (f"fell {float(d['drop_up']):.2f} m from a spawn 50 mm "
                       f"above the shell -- the floor is not where it says "
                       f"(total displacement {float(d.get('drop', 0)):.2f} m)")
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
        # -- AND THE DOOR OPENED ------------------------------------------
        # This gate has printed `door_open` since W5 and asserted nothing on
        # it, because the number was a lie: `walk.gd` sampled the LIVE openness
        # at the frame the verdict printed, which for a body that walked
        # THROUGH a pressure door is several seconds after it shut again behind
        # them. Every passing run reported 0.00. It is now the door's PEAK over
        # the walk -- `door.gd::peak_openness` -- so it can be asserted.
        #
        # -1.00 is a different failure and says so: no door of that name was
        # ever assembled, which is leaves in one place and a panel in another.
        # The control is `--no-doors`, where `door.gd` is not built at all and
        # the token is absent; that is the branch below.
        door = ""
        if "door_open" in d:
            op = float(d["door_open"])
            if op < 0.0:
                return False, (f"there is no pressure door called `{d['goto']}` "
                               f"in this build -- nothing ever assembled its "
                               f"leaves and its panel into one door")
            if op <= 0.0:
                return False, (f"the body reached {d['goto']} and the pressure "
                               f"door never opened at all -- the way in is a "
                               f"hole in the wall, not a door")
            door = f", through a door that opened to {op:.2f}"
        elif int(d.get("doors", 0)) > 0:
            return False, (f"this cluster has {d['doors']} door(s) and the "
                           f"verdict carries no `door_open` -- "
                           f"godot/scripts/door.gd did not load, so every "
                           f"pressure door on it is a wall")
        return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg, "
                      f"{d['doors']} doors; a body spawns in the corridor and "
                      f"WALKS INTO {d['goto']} "
                      f"({float(d['goto_start_m']):.1f} m -> {near:.2f} m), "
                      f"never leaving the floor{door}{note}")
    got = float(d.get("traverse_m", 0))
    if got < MIN_TRAVERSE_M:
        return False, (f"covered {got:.1f} m of corridor, under the "
                       f"{MIN_TRAVERSE_M:.0f} m bar -- something is snagging")
    return True, (f"{d['rooms']} rooms over {float(d['arc_deg']):.0f} deg; a "
                  f"body spawns at {d['spawn_at']}, walks {got:.1f} m and "
                  f"never leaves the floor")


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


def _visit_run(godot, extra, crowd=False, timeout=1200):
    """One `--visit` run of the streamed build, parsed into a dict.

    `crowd` puts the corridor's walkers in it. It is a SEPARATE run rather than
    always-on, and the reason is a measurement rather than a preference: with
    people resolved by `move_and_slide` the crowd cost the body most of its
    walking speed -- 12 walkers resident and the arc leg covered 93 m of its
    130 m inside the same frame budget -- so the crowd run could not make the
    visit claims at all. Quietly raising the leg budgets until it could would
    have been picking the convenient reading.

    That is no longer true and the gate says so: since `npc.gd` stopped putting
    people in the player's way and started separating them by hand, the crowd
    run makes EVERY claim the crowd-less one makes and its own on top, and
    `stream_gate` asserts both on it. The crowd-less run is kept because it is
    the configuration the five wiring controls are controls FOR, and because a
    difference between the two is then the crowd and nothing else.
    """
    d = STREAM_DECK
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--", f"--cells={STREAM_CELLS}",
           "--stream-test", "--visit", "--gravity-mode=drum", "--settle=120",
           f"--actors={d}/blue_0_0_actors.json",
           f"--interact={d}/blue_0_0_interact.json",
           f"--door-travel={K.PROVISIONAL['door_width_m'] / 2.0}",
           f"--use-group={STREAM_USE}"]
    if crowd:
        import populace as _pop                                # noqa: PLC0415
        # The ladder and its libraries come from `populace.crowd_ladder()`, the
        # same function the bake wrote them with -- a literal here would be a
        # second description of which mesh belongs at which distance.
        lad = _pop.crowd_ladder()
        cmd += [f"--crowd={d}/blue_0_0_crowd.json",
                "--crowd-ladder=" + ",".join(f"{hi:g}:{lod}" for hi, lod in lad),
                "--crowd-glbs=" + ",".join(f"{d}/crowd_lod{lod}.glb"
                                           for _hi, lod in lad)]
    cmd += list(extra)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    m = re.search(r"STREAMTEST (.+)", out)
    if not m:
        return {"error": "no STREAMTEST verdict printed"}
    return dict(t.split("=", 1) for t in m.group(1).split() if "=" in t)


def stream_verdict(s):
    """Is a streamed cell a PLACE: doors that open, people who react, things
    that work -- and does it still work after the cell has been freed and
    walked back into?"""
    if "error" in s:
        return False, s["error"]
    if s.get("ok") != "true":
        return False, (f"the run did not pass its own assertions: "
                       f"{s.get('why', '?')}")
    off = int(s["offfloor"].split("/")[0])
    if off > 0:
        return False, (f"{s['offfloor']} frames off the floor -- something in "
                       f"the corridor is taking the ground away")
    if float(s["floor_m"]) < MIN_STREAM_FLOOR_M:
        return False, (f"covered {float(s['floor_m']):.1f} m ON THE FLOOR, "
                       f"under the {MIN_STREAM_FLOOR_M:.0f} m bar")
    if s.get("freed") != "true":
        return False, "the cell was never freed, so visit 2 is not a re-entry"
    for tok, want in (("double_wires", 0), ("stale_prompt_frames", 0),
                      ("stale_leaves", 0), ("stale_parts", 0)):
        if int(s.get(tok, -1)) != want:
            return False, (f"{tok}={s.get(tok)} -- something outlived the cell "
                           f"that brought it")
    for v in ("v1", "v2"):
        if float(s[f"{v}_door_open"]) <= 0.0:
            return False, (f"{v}: the pressure door never opened "
                           f"({s[f'{v}_door_open']}) -- in a streamed cell it "
                           f"is a wall")
        if int(s[f"{v}_noticed"]) < 1:
            return False, f"{v}: nobody in the cell noticed the body"
        if s[f"{v}_prompted"] != "true" or int(s[f"{v}_presses"]) < 1:
            return False, f"{v}: {s['use_group']} was never prompted or pressed"
        if float(s[f"{v}_travel_mm"]) <= 0.0:
            return False, f"{v}: {s['use_group']} was used and did not move"
    return True, (
        f"a body walks {float(s['floor_m']):.1f} m ON THE FLOOR, "
        f"{s['offfloor']} frames off it, into cell {s['visit_cell']} which was "
        f"streamed in after launch: the pressure door opens to "
        f"{float(s['v1_door_open']):.2f}, {s['v1_noticed']} people look up, "
        f"and {s['use_group']} prompts and moves "
        f"{float(s['v1_travel_mm']):.1f} mm. The cell is then FREED and "
        f"re-entered and all three still work ({float(s['v2_door_open']):.2f} "
        f"/ {s['v2_noticed']} / {float(s['v2_travel_mm']):.1f} mm)")


def crowd_verdict(s):
    """Can a body do all of that with people in the corridor, and still never
    lose the floor?

    EVERY VISIT CLAIM AND THEN THE CROWD'S OWN. The crowd is what
    `docs/streaming-doors-4g.md` had to switch OFF to get its headline run, so
    a crowd run that only asserted the crowd would leave the harder half of the
    build unguarded in the configuration a player actually meets.
    """
    ok, why = stream_verdict(s)
    if not ok:
        return False, why
    off = int(s["offfloor"].split("/")[0])
    # THE CROWD HAS TO BE THERE, or `offfloor=0` is a measurement of an empty
    # corridor. `walkers`, `crowd_collider` and `push_m` are printed
    # unconditionally by `walk.gd::_crowd_report` for exactly this: a run whose
    # `--crowd-glbs` pointed at nothing would otherwise report a flawless zero.
    if int(s.get("walkers", 0)) < 1:
        return False, ("no walkers were resident -- this measured an empty "
                       "corridor, not a crowd that keeps off the player")
    if float(s.get("crowd_travel_m", 0.0)) <= 0.0:
        return False, (f"{s['walkers']} walkers covered "
                       f"{s.get('crowd_travel_m')} m -- statues wearing a "
                       f"walk pose")
    # `stream_verdict` has already failed anything that left the floor, which is
    # where `--npc-solid=mask` dies -- 821 frames in 705 episodes. That is the
    # substantive claim and it is checked BEFORE the identity check below, which
    # a control would fail whatever it did: a control that fails for declaring
    # itself a control has measured nothing.
    if float(s.get("push_m", 0.0)) <= 0.0:
        return False, ("the body walked the whole corridor and was never "
                       "separated from anybody -- people are holograms")
    if s.get("crowd_collider") != STREAM_COLLIDER:
        return False, (f"people were `{s.get('crowd_collider')}` and not "
                       f"`{STREAM_COLLIDER}` -- a lesser mechanism was "
                       f"substituted for the one asked for")
    return True, (
        f"a body walks {float(s['floor_m']):.1f} m ON THE FLOOR through a "
        f"corridor with people in it, {s['offfloor']} frames off it. "
        f"{s['walkers']} walkers resident cover "
        f"{float(s['crowd_travel_m']):,.0f} m around it and push it "
        f"{float(s['push_m']):.0f} m out of their way "
        f"({float(s['push_max_mm']):.0f} mm in the worst frame) -- so they are "
        f"solid, and not one of those metres is vertical")


# EVERY ONE OF THESE MUST FAIL, and between them they turn off every claim the
# two subject runs make. `--no-cell-wiring` is the build `docs/streaming-4g.md`
# shipped -- cells stream and nothing is told about them -- and stands for all
# three wiring claims at once; the next four turn off exactly one each. The
# last is judged against the CROWD run instead, and it is the build before
# session 4h: people back on the world collision layer, resolved by
# `move_and_slide`, which cost the body its floor for 3,090 of 16,200 frames.
STREAM_CONTROLS = (
    (("--no-cell-wiring",), False, "the build before the cells were wired"),
    (("--no-doors",), False, "the door claim"),
    (("--no-people",), False, "the reaction claim"),
    (("--no-interact",), False, "the use claim"),
    (("--no-unwire",), False, "the free-and-re-enter claim"),
    (("--npc-solid=mask",), True,
     "people back on the world layer, as they were before session 4h"),
)


def stream_gate(godot):
    """A streamed cell is a PLACE and its corridor has people in it.

    TWO SUBJECT RUNS AND SIX CONTROLS. The visit claims and the crowd claim
    cannot honestly be made by the same run -- see `_visit_run` -- so each is
    made by the run that can make it, and every control is judged against the
    subject it is a control for.
    """
    sub = _visit_run(godot, [])
    good, why = stream_verdict(sub)
    print(f"  {'PASS' if good else 'FAIL'}  stream  {why}")

    crowd = _visit_run(godot, [], crowd=True)
    cgood, cwhy = crowd_verdict(crowd)
    print(f"  {'PASS' if cgood else 'FAIL'}  crowd   {cwhy}")
    good = good and cgood

    for flags, on_crowd, what in STREAM_CONTROLS:
        c = _visit_run(godot, list(flags), crowd=on_crowd)
        cok, _cw = (crowd_verdict(c) if on_crowd else stream_verdict(c))
        if cok:
            print(f"  FAIL  with {' '.join(flags)} the gate still passed -- it "
                  f"is measuring nothing ({what})")
            good = False
        else:
            print(f"        control {' '.join(flags):20s} FAILS as it must: "
                  f"{_control_note(c)}  [{what}]")
    return 0 if good else 1


def _control_note(c):
    """One line saying what the control actually did, so a control that fails
    for the wrong reason is visible rather than merely absent."""
    if "error" in c:
        return c["error"]
    return (f"floor_m={float(c.get('floor_m', 0)):.1f} "
            f"offfloor={c.get('offfloor')} "
            f"v1_door={c.get('v1_door_open')} v1_noticed={c.get('v1_noticed')} "
            f"v1_presses={c.get('v1_presses')} "
            f"people={c.get('crowd_collider')} push_m={c.get('push_m')}")


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
                    help="is a streamed cell a PLACE? Walks into one that "
                         "arrived after launch, through a pressure door in it, "
                         "up to something usable, then frees it and comes back "
                         "-- with the corridor crowd walking past throughout")
    ap.add_argument("--raw", action="store_true",
                    help="also print the engine's own verdict line for the "
                         "deck walk, which is what the gate judged")
    a = ap.parse_args()

    godot = godot_binary()
    if godot is None:
        # NAME THE COMMAND, not the document. Since session 4d the binary is
        # vendored in the repository and this is a seconds-long unpack, not the
        # hour it used to imply -- a reader who has to go and find that out is
        # the reader who assumes the gate is unrunnable and skips it.
        print("no double-precision Godot binary.\n"
              "  run:  bash tools/build_godot.sh\n"
              "  (unpacks vendor/godot/ in seconds; builds from source only if\n"
              "   this container has neither a vendored copy nor a URL)\n"
              "  see docs/godot-binary.md")
        return 1

    if a.stream:
        return stream_gate(godot)

    if a.deck or a.deck_only:
        sector, ring, deck = (a.deck or "blue/0/0").split("/")
        d = walk_deck(sector, int(ring), int(deck), godot,
                      traverse=a.traverse, no_doors=a.no_doors, z_m=a.z)
        drum = (sector, int(ring)) in D.NOT_RING_DECKS
        if drum:
            import drum_walk as DW                              # noqa: PLC0415
            good, why = DW.walk_verdict(d)
        else:
            good, why = deck_verdict(d)
        print(f"  {'PASS' if good else 'FAIL'}  "
              f"{'drum' if drum else 'deck'} {sector}/{ring}/{deck}  {why}")
        if a.raw and "verdict" in d:
            print(f"        measured: {d['verdict']}")

        # THE NEGATIVE CONTROL, and it is the whole reason the door claim means
        # anything. A body that reaches the room proves the route is open; it
        # does not prove the DOOR opened it, because a door-shaped hole in the
        # wall gives exactly the same number. So the same run is repeated with
        # the doors inert: the closed panels stay solid and the body must NOT
        # get in. If both runs pass, the doors are scenery.
        # The drum has no doors, so `--no-doors` is not a control there --
        # running it would compare a thing against itself and pass.
        if good and not a.no_doors and not drum:
            # `z_m=a.z` OR THE CONTROL WALKS A DIFFERENT PLACE. A deck is not a
            # z-slice -- blue/0/0 has six clusters over 1,100 m -- so a control
            # that drops it compares the subject's cluster against the default
            # one and the comparison means nothing. Every other call here
            # passes it; this one did not.
            n = walk_deck(sector, int(ring), int(deck), godot,
                          traverse=a.traverse, z_m=a.z, no_doors=True)
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
            if stop < 0 or walk_through < 0:
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
                    print(f"        control: with {n.get('stripped_tris')} "
                          f"triangles of {u['use_want']} deleted from the "
                          f"render mesh the engine wires "
                          f"{n.get('interactables', '?')} interactables "
                          f"instead of {u['interactables']}, the prompt reads "
                          f"`{n.get('prompt', '?')}` and use_count is "
                          f"{n.get('use_count', '?')}. What you look at is "
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
