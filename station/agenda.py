#!/usr/bin/env python3
"""L1 -- SOMEONE GOES TO WORK. One named resident, their own shift, their own legs.

WHAT WAS MISSING, MEASURED RATHER THAN SUMMARISED. `docs/MASTER-PLAN.md` L1 asks
for *"one named resident leaves their quarters at their own start hour, walks a
`routes.py` path, and is at their post"*. Before this file, **zero residents
moved**, and the reason is not that the data was absent -- every piece of it was
already here and none of it ran:

    npc/resident.py     name, species, role, home, job, and `where_at(hour)`
    npc/schedule.py     the shift, the 0.5 h TRANSIT window either side of it
    npc/navigation.py   `walk_speed`, `walk_time_s` at the deck's own gravity
    populace.py         `_walk_speed` -- the gait the crowd is ANIMATED at
    routes.py           the circulation graph, one foot-connected component
    life.gd             a clock, and 73 residents bound to it

`godot/scripts/life.gd`'s own comment said what it actually did: *"the runtime
cannot create a person, so a room busier than its bake hour is capped"* -- it
SHOWS AND HIDES pre-baked bodies by the hour. A resident's whole day was a
visibility flag.

--------------------------------------------------------------------------
THE ONE ARCHITECTURAL DECISION, AND WHY IT GOES THIS WAY
--------------------------------------------------------------------------
People exist two ways on this station and only one of them can commute:

    BAKED ACTOR      welded into the deck mesh at one hour, shown/hidden.
                     `<deck>_actors.json`. Costs primitives in the deck .glb.
    INSTANCED WALKER a transform against `populace.station_crowd_library`.
                     `<deck>_crowd.json`. Costs NOTHING in the deck .glb --
                     the bodies live in `crowd_lod*.glb` and every walker of
                     one (species, lod, phase) shares one MultiMesh.

A resident who goes to work must be a walker ALL DAY: they cannot wink out of
their quarters and wink in at their post. So a commuter is an INSTANCED body,
and the cost question the brief asks -- does moving N residents to the instanced
path break `budget.BUDGETS["deck_primitives"] = 600`? -- has the opposite answer
to the one it expects. Measured off the shipped .glbs by `budget._glb_primitives`
(`--primitives` prints this):

    deck        primitives   of which people   baked actors   crowd rows
    green_0_1        150              35              7            11
    grey_0_0         154              47              9            59
    blue_0_0       1,824             547            118           444
    red_0_0        3,488           2,850            566           238

**5.04 primitives per baked actor on red/0/0, and 0.00 per instanced walker.**
Two of these four decks are already over the 600 bound and the crowd is not why.
Moving a resident from baked to instanced does not cost primitives; it is the
only lever that gives them back.

--------------------------------------------------------------------------
WHAT MOVES, AND WHAT DOES THE MOVING
--------------------------------------------------------------------------
`life.gd`'s design rule is *"an inhabitant's state is a PURE FUNCTION of the
station clock"*, and it is right -- it is what makes leaving and returning
consistent, and it is the ONLY design that survives requirement 5 of this
milestone: a schedule that works at 1x and not at 60x is not a schedule, and at
x60 this resident covers 88 m of station a second. So:

    THE AGENDA IS PURE IN THE HOUR.   `s(h)` is how far along the route the
                                      resident should be. It teleports freely.
    THE BODY IS PHYSICS.              A `CharacterBody3D` on the station's own
                                      collision shell, steered at a carrot on
                                      the route ahead of `min(s_agenda, s_body)`
                                      -- ahead of the BODY so it stays on the
                                      polyline through a doorway, and ahead of
                                      the AGENDA so it cannot arrive early.

That split is what makes the second control able to fire at all. With the
resident's own doors left sealed the AGENDA still completes all 887.9 m -- and
the BODY has walked 3.66 m inside its own quarters and is 570 m from its post. A
runtime that placed people from `s(h)` would report a successful commute through
a locked pressure door, and no gate in this repository could have caught it.

AND A FASTER CLOCK NEEDS MORE PHYSICS, NOT BIGGER STEPS. At x60, 88 m/s at 60 Hz
is **1.9 m a tick** -- wider than the 1.5 m pressure door the resident has to
walk through. The first run of this gate did exactly that, covered 6.09 m, and
wedged against the bedroom wall for 604 frames reporting `on_floor=true`.
`life.gd` therefore raises `Engine.physics_ticks_per_second` WITH the clock, so
the step in station time is 24 mm at every rate -- and the cost is stated rather
than hidden: **all three runs take the same ~50,700 ticks. x60 buys station
time, not wall time.**

--------------------------------------------------------------------------
WHAT IS MEASURED
--------------------------------------------------------------------------
    floor_m    metres covered WHILE STANDING ON SOMETHING
    air_m      metres covered while not
    offfloor   physics frames not on a floor, settle excluded
    lag_m      how far the BODY is behind the AGENDA, worst over the run

`floor_m` and never path length: this codebase has twice found a falling body
reporting a journey (11,712 m in the streaming work, 876,827 m before that).

Run: python3 station/agenda.py --report      who commutes where, no engine
     python3 station/agenda.py --primitives  the baked/instanced cost table
     python3 station/agenda.py --selftest    everything answerable offline
     python3 station/agenda.py --walk        THE GATE: three rates, three controls
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

import collision as C                                            # noqa: E402
import deck as D                                                 # noqa: E402
import directory as DIR                                          # noqa: E402
import interior as it                                            # noqa: E402
import lift as L                                                 # noqa: E402
import populace as P                                             # noqa: E402
import routes as RT                                              # noqa: E402
import roomnav as RN                                            # noqa: E402
import route_walk as RW                                          # noqa: E402
import transit as T                                              # noqa: E402
import transit_runtime as TR                                     # noqa: E402
import walkable as W                                             # noqa: E402
from npc import navigation as NAV                                # noqa: E402
from npc import resident as RS                                   # noqa: E402
from npc import schedule as SC                                   # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/agenda")
STATION = os.path.join(ROOT, "station/generated/scene/station")
DECKDIR = os.path.join(ROOT, "station/generated/scene/deck")

# THE CROWD LIBRARY'S NEAREST RUNG. `populace.crowd_ladder()` owns which LOD a
# walker is drawn at and at what distance; the commuter is drawn from the same
# libraries the deck's own crowd uses, so this is only which one the gait is
# measured from. 4 is the rung `deck.py` bakes at.
CROWD_LOD = 4

# HOW LONG THE GATE WATCHES EITHER END OF THE COMMUTE, in station seconds.
# Requirement 1 is "at home BEFORE their start hour" and requirement 3 is "at
# their post AFTER" -- both are claims about a span rather than an instant, and
# an instant is trivially satisfied by a body that happens to be passing.
PRE_S = 120.0
POST_S = 120.0

# HOW FAR AHEAD THE BODY IS STEERED, AND IT IS DERIVED FROM THE DOORWAY.
#
# A body steered AT its own position on the route has nothing to walk towards and
# dithers; a body steered at a point AHEAD of it walks. The bound on how far
# ahead is the corner: a right-angle turn taken with a carrot `d` metres along
# the route is cut by at most `d / sqrt(2)`, and the only right angles on this
# route are where the ring corridor meets a doorway. The clearance a capsule has
# in a `door_width_m` aperture is `door_w/2 - r`, which is what
# `route_walk.door_tol_m` halves to get its waypoint tolerance -- so the largest
# carrot that cannot put a shoulder into a jamb is `sqrt(2)` times that
# clearance. Nothing here is chosen; both numbers belong to the kit.
def lookahead_m():
    return math.sqrt(2.0) * 2.0 * RW.door_tol_m()

# HOW MUCH FASTER THAN THE AGENDA THE BODY MAY WALK, so a snag can be paid off
# rather than becoming permanent desync. A body limited to exactly the agenda's
# speed never recovers a metre it loses squeezing past a door jamb.
CATCHUP = 1.30

# The player's capsule. Same figure `walk.gd::_spawn_player`, `route_test.gd` and
# `collision.floor_holes` all use; not a second answer to how wide a person is.
# `roomnav.py` owns it, because that is the module whose whole job is asking
# whether a body fits somewhere.
CAPSULE_R_M = RN.CAPSULE_R_M
CAPSULE_H_M = RN.CAPSULE_H_M

# Frames of settling before the walk is scored. `collision.stand_at` spawns 50 mm
# above the shell on purpose, so the drop is asserted rather than excluded --
# see `verdict`.
SETTLE_FRAMES = 90


# ---------------------------------------------------------------------------
# WHO COMMUTES, AND IT IS CHOSEN BY THE DATA
# ---------------------------------------------------------------------------

def deck_key(place_key):
    """`sector_ring_deck` for a located place, or None."""
    p = DIR.by_key(place_key)
    if p is None or p.get("sector") is None or p.get("deck") is None:
        return None
    return f"{p['sector']}_{p['ring']}_{p['deck']}"


def assembled():
    """Every deck `tools/export_station.py` actually wrote, from its manifest.

    Read rather than rebuilt, and the collision triangle count is read with it:
    `build` asserts its own shell against this number, so the geometry a body
    walks on cannot drift from the geometry that shipped.
    """
    path = os.path.join(STATION, "station_manifest.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        man = json.load(f)
    return {d["key"]: d for d in man.get("decks", ())
            if d.get("ok") and os.path.exists(
                os.path.join(STATION, d["key"] + ".glb"))}


def clean_commute(npc_id, species):
    """Does this person's OWN schedule show them walking to work?

    Four questions of `npc/schedule.py`, and every one of them can say no:

      1. they have a shift at all (`work_window`)
      2. `activity_at` is TRANSIT across the whole window before it -- a meal
         landing inside the commute makes `where_at` say `fresh_air` halfway
         through, and a gate whose premise its own data contradicts is a gate
         measuring something else
      3. `activity_at` is WORK at the start hour
      4. and they are NOT already at work just before they set off

    Returns (depart_h, start_h, hours) or None.
    """
    w = SC.work_window(npc_id, species)
    if w is None:
        return None
    w0, hours = w
    depart = (w0 - SC.TRANSIT_H) % 24.0
    A = SC.Activity
    for f in (0.02, 0.25, 0.5, 0.75, 0.98):
        h = (depart + SC.TRANSIT_H * f) % 24.0
        if SC.activity_at(npc_id, species, h) is not A.TRANSIT:
            return None
    if SC.activity_at(npc_id, species, w0 % 24.0) is not A.WORK:
        return None
    if SC.activity_at(npc_id, species, (depart - 0.05) % 24.0) in (A.WORK,
                                                                   A.TRANSIT):
        return None
    return depart, w0 % 24.0, hours


def walkable_commutes():
    """Every (species, role, home, job) whose two ends sit on ONE built deck.

    A CHEAP PRE-FILTER, AND IT IS WHAT MAKES THE SEARCH FINISHABLE. `home_for`
    and `workplace_places` are pure functions of (species, role) -- 19 roles by
    14 species is 266 questions, against the 2.7 million `Resident` records a
    naive scan of every place's pool would build. It cannot invent a pairing the
    generator does not make, because it is the generator's own two functions.

    ONE DECK BECAUSE L1 IS NOT L3. A commute that crosses decks needs the lift,
    and "they use the transit" is the milestone after next. What is asked for
    here is a resident who walks.
    """
    ok = assembled()
    out = []
    for role in SC.ROLES:
        if role.work_hours <= 0:
            continue
        try:
            jobs = RS.workplace_places(role.workplace)
        except Exception:                                       # noqa: BLE001
            continue
        for species in sorted(SC.STATION_MIX):
            if species in SC.SPECIES_WITHOUT_NAMES:
                continue           # L1 asks for a NAMED resident
            home = RS.home_for(f"probe:{species}:{role.key}", species, role.key)
            dk = deck_key(home)
            if dk is None or dk not in ok:
                continue
            for job in jobs:
                if job == home or deck_key(job) != dk:
                    continue
                out.append({"species": species, "role": role.key,
                            "home": home, "job": job, "deck": dk})
    return out


def candidates(limit=1200, want=8):
    """Residents whose home and post are on ONE assembled deck, with a name.

    FROM THE POOL THE ROOM ITSELF IS CAST FROM. `populace.populate` fills a room
    with `resident.roster`, which draws on `resident.affiliates(place, species)`,
    which scans `resident.pool_id(place, species, i, seed)` in order. This walks
    the same stream, so the person who commutes is a person the generator would
    have put in that room anyway -- not a probe id invented for a test.
    """
    out = []
    seen = set()
    for w in walkable_commutes():
        key = (w["species"], w["home"], w["job"])
        if key in seen:
            continue
        seen.add(key)
        for pool in (w["job"], w["home"]):
            hit = None
            for i in range(limit):
                npc_id = RS.pool_id(pool, w["species"], i, "b5")
                try:
                    res = RS.resident(npc_id, w["species"])
                except Exception:                               # noqa: BLE001
                    continue
                if (res.home, res.job) != (w["home"], w["job"]) or not res.name:
                    continue
                sched = clean_commute(npc_id, w["species"])
                if sched is None:
                    continue
                hit = {"pool": pool, "i": i, "res": res, "deck": w["deck"],
                       "depart_h": sched[0], "start_h": sched[1],
                       "hours": sched[2]}
                break
            if hit:
                out.append(hit)
                break
        if len(out) >= want:
            break
    # DETERMINISTIC: the lowest pool index wins, ties on species then place. The
    # pool index is the order `affiliates` itself scans in, so "the first one" is
    # the same person on every machine and every run.
    out.sort(key=lambda r: (r["i"], r["res"].species, r["pool"]))
    return out


def choose(who=None):
    """The commuter. `who` is an npc_id to pin one; otherwise the first."""
    cs = candidates()
    if who:
        for c in cs:
            if c["res"].npc_id == who:
                return c
        raise ValueError(f"{who} is not a resident who commutes on one deck -- "
                         f"run --report for the list")
    if not cs:
        raise ValueError("no resident on an assembled deck has their home and "
                         "their post on that same deck")
    return cs[0]


# ---------------------------------------------------------------------------
# THE ROUTE, OUT OF THE GRAPH AND ONTO THE FLOOR
# ---------------------------------------------------------------------------

def graph_path(nodes, es, home, job):
    """What `routes.py` says about getting from `home` to `job`.

    Returns (legs, note). `legs` is `route_walk.path_between`'s output; on a
    commute inside one z-cluster it is EMPTY, and that is not a missing answer:
    `routes.clusters` says in as many words that *"two places in one cluster are
    already joined by the ring corridor that serves them"*, and the corridor
    this route is laid in is that corridor. The note says which case it is so a
    reader cannot mistake one for the other.
    """
    at = {}
    for k, n in nodes.items():
        for pk in n["places"]:
            at[pk] = k
    a, b = at.get(home), at.get(job)
    if a is None or b is None:
        return None, f"{home if a is None else job} is not in any z-cluster"
    if a == b:
        return [], (f"one z-cluster, {a[0]}/{a[1]}/{a[2]} z={a[3]:.0f} -- "
                    f"joined by the ring corridor that serves them")
    legs = RW.path_between(nodes, es, a, b)
    if legs is None:
        return None, f"no path in the circulation graph between {a} and {b}"
    return legs, " -> ".join(l["kind"] for l in legs)


def cluster_meta(schema, profile, sector, ring, deck, place_key):
    """The collision meta of the z-cluster a place sits in.

    `deck.build_collision_clusters` returns one meta per cluster; this picks the
    one that actually carries a door for `place_key`, which is the only
    definition that cannot drift when a deck gains a cluster.
    """
    ang = RT.transit_angle(sector, RT.clusters())
    v, t, meta = D.build_collision_clusters(schema, profile, sector, ring, deck,
                                            join=True, must_cover=ang)
    for m in meta["clusters"]:
        if any(r["key"] == place_key for r in m.get("rooms", ())):
            return v, t, meta, m
    raise ValueError(f"{place_key} has no door in {sector}/{ring}/{deck}'s "
                     f"collision -- rooms are "
                     f"{[r['key'] for m in meta['clusters'] for r in m['rooms']]}")


def assert_route_endpoints(where, first, last, home_at, post_at, tol=1e-6):
    """The route the body walks ends where the manifest says its post is.

    THIS IS THE GATE ON THE THREADING, and it exists because the alternative is
    discipline. `walkable.room_target` is called from five places to answer one
    question -- where inside a room does a person stand -- and it now takes the
    room's collision mesh so it can nudge the answer off the furniture. A call
    site that forgets to pass the mesh does not crash and does not look wrong:
    it quietly answers the register's centre point while the others answer free
    floor, and the body then walks to one point while the verdict measures the
    other.

    That is one level below the defect this whole change fixes. The L3 run that
    read `stopped 5.59 m from business_center` was a body that HAD arrived, at
    the only place in the room it could stand, with the post inside a desk
    rank. A silent threading miss would put the same distance back and look
    identical. So the two points are asserted equal rather than assumed equal
    -- hard rule 4, one authority per fact, applied to a point.
    """
    for nm, a, b in (("spawn", first, home_at), ("post", last, post_at)):
        d = math.dist(a, b)
        if d > tol:
            raise AssertionError(
                f"{where}: the route's {nm} waypoint is {d:.3f} m from the "
                f"manifest's {nm} -- the body walks to one point and the "
                f"verdict measures another. A `walkable.room_target` call site "
                f"is missing its collision mesh: {list(a)} vs {list(b)}")


def room_legs(schema, profile, m, place_key, outward, verts=None, tris=None,
              groups=None):
    """Getting through one room's doorway AND across its floor, in the
    direction of travel.

    `outward` is leaving the room; otherwise entering it. THE DOORWAY IS THE
    PLACE A BODY GETS STUCK and `route_walk` paid for the rule this reproduces:
    a waypoint IN an aperture is tight (`door_tol_m`, derived from the aperture
    and the capsule), and there is an aim point on the doorway's own centre line
    at both ends, because a body that turns while standing in a doorway meets
    the jamb.

    AND THE FLOOR INSIDE IS THE SECOND PLACE, which cost this milestone a
    session. This leg used to be three points -- the door, half a metre inside
    it, and the register's centre -- and that last hop was a straight line laid
    before rooms had furniture in them. On `business_center` it passes through a
    desk rank and a partition, with under a capsule's clearance for 4.5 of its
    5.5 m, so the body walked to the desks and stopped 5.59 m from a post it
    could not reach. `walkable.room_approach` -> `roomnav.approach` replaces the
    hop with the way a person would actually take, searched over the room's own
    collision. A room whose middle is clear still gets exactly one point, and
    it is the register's centre to the metre it was written at.
    """
    place = DIR.by_key(place_key)
    door = next(r for r in m["rooms"] if r["key"] == place_key)
    fr = m["floor_r_m"]
    cz = m["z_m"]
    tol = RW.door_tol_m()
    z_half = D.room_interior_half_m(schema, profile, place)
    z_inner = place["z_m"] + z_half
    in_door = RW._at(fr, door["door_deg"], z_inner - 0.5)
    at_door = RW._at(fr, door["door_deg"], cz)
    way = [list(p) for p in W.room_approach(m, place, verts, tris, groups,
                                            from_pt=in_door, z_half=z_half)]
    if outward:
        pts = list(reversed(way)) + [in_door, at_door]
        return RW._leg("room", f"out of {place_key} through its door at "
                               f"{door['door_deg']:.0f} deg", pts,
                       RW._tight(pts, [len(pts) - 2, len(pts) - 1], tol))
    pts = [at_door, in_door] + way
    return RW._leg("room", f"through the door into {place_key} at "
                           f"{door['door_deg']:.0f} deg", pts,
                   RW._tight(pts, [0, 1], tol))


def shell_groups(all_meta):
    """The whole shell's named spans, in the concatenated shell's own indices.

    ONE CONSTRUCTION, TWO USERS. `write_collision` needs these to write a GLB
    whose pressure doors the runtime can switch off one at a time, and
    `roomnav` needs them to know that a `doorpanel_*` triangle is a door rather
    than a wall -- a room searched with its door counted as solid reads as
    sealed. Building the list twice is how the two would come to disagree about
    which triangles are a door.
    """
    groups, base = [], 0
    for m in all_meta["clusters"]:
        for nm, lo, hi in m.get("groups", ()):
            groups.append((nm, base + lo, base + hi))
        base += m["triangles"]
    return groups


def route_for(schema, profile, cand):
    """Every waypoint from the resident's bunk to their desk.

    NOTHING HERE AUTHORS GEOMETRY. The arc faceting, the door tolerance and the
    waypoint discipline are `route_walk.py`'s -- imported rather than restated,
    because a second copy of "how finely is an arc stepped" is exactly the class
    of duplication this project keeps paying for. The radius, the corridor's
    centre z and both door angles come out of `deck.deck_plan` through
    `deck.build_collision_clusters`, which is the call `tools/export_station.py`
    made to write the shell that is on disk.
    """
    res = cand["res"]
    p = DIR.by_key(res.home)
    sector, ring, deck = p["sector"], p["ring"], p["deck"]
    v, t, meta, m = cluster_meta(schema, profile, sector, ring, deck, res.home)
    sgroups = shell_groups(meta)
    if not any(r["key"] == res.job for r in m["rooms"]):
        raise ValueError(f"{res.job} is not on the same z-cluster as "
                         f"{res.home}; L1 walks one corridor")
    d0 = next(r for r in m["rooms"] if r["key"] == res.home)["door_deg"]
    d1 = next(r for r in m["rooms"] if r["key"] == res.job)["door_deg"]
    fr, cz = m["floor_r_m"], m["z_m"]

    arc = RW._arc_points(fr, d0, d1, cz)
    legs = [
        room_legs(schema, profile, m, res.home, outward=True,
                  verts=v, tris=t, groups=sgroups),
        RW._leg("ring", f"the ring corridor of {sector}/{ring}/{deck} at "
                        f"r={fr:.1f} m, {d0:.0f} deg -> {d1:.0f} deg", arc,
                RW._tight(arc, [0, len(arc) - 1], RW.door_tol_m())),
        room_legs(schema, profile, m, res.job, outward=False,
                  verts=v, tris=t, groups=sgroups),
    ]
    pts = []
    for l in legs:
        for q in l["points"]:
            if not pts or math.dist(pts[-1], q) > 1e-6:
                pts.append(list(q))
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    return {"legs": legs, "points": pts, "length_m": round(length, 3),
            "meta": m, "verts": v, "tris": t, "all_meta": meta,
            "groups": sgroups,
            "sector": sector, "ring": ring, "deck": deck,
            "door_home": d0, "door_job": d1}


# ---------------------------------------------------------------------------
# THE BUILD
# ---------------------------------------------------------------------------

def _glb(obj_path):
    """OBJ -> GLB. `station/export_gltf.py` makes one node per group name, which
    is how the runtime gets a door panel it can switch off without touching the
    shell it is cut in."""
    import contextlib                                             # noqa: PLC0415
    import io                                                     # noqa: PLC0415
    import export_gltf                                            # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path, "--out", obj_path[:-4] + ".glb"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            export_gltf.main()
    finally:
        sys.argv = argv
    return obj_path[:-4] + ".glb"


def write_collision(cand, r, quiet=False):
    """The deck's own collision shell, re-emitted WITH ITS GROUPS.

    AND THIS IS A DEFECT IN A FILE THIS SESSION DOES NOT OWN, stated here
    because the workaround would otherwise look like a preference.
    `deck.build_collision` emits every closed pressure door as its own span --
    `doorpanel_<place>` -- precisely so a runtime can switch exactly that off
    when the door opens, and `godot/scripts/route_test.gd` and `walk.gd` both
    rely on the name. `tools/export_station.py` then writes the whole shell as
    ONE group:

        cgroups = [("collision", 0, len(ct))]

    so every `<deck>_collision.glb` on disk has its pressure doors welded shut
    and no way to address one. A body cannot leave a room on the shipped
    collision at all. The exact patch is in docs/life-L1.md.

    What this writes is the SAME CALL with the spans kept, and it is asserted
    triangle-for-triangle against the manifest's own `collision_tris` -- so it
    is the shipped shell re-emitted, not a second shell.
    """
    os.makedirs(OUT, exist_ok=True)
    verts, tris, meta = r["verts"], r["tris"], r["all_meta"]
    want = assembled()[cand["deck"]]["collision_tris"]
    if len(tris) != want:
        raise AssertionError(
            f"this shell has {len(tris):,} triangles and "
            f"{cand['deck']}_collision.glb shipped {want:,} -- "
            f"deck.build_collision_clusters no longer reproduces what "
            f"tools/export_station.py wrote, so nothing below is about the "
            f"station that is on disk")
    groups = [("shell", 0, len(tris))] + shell_groups(meta)
    obj = os.path.join(OUT, cand["deck"] + "_col.obj")
    C.write_obj(obj, verts, tris, groups, name="agenda")
    glb = _glb(obj)
    os.remove(obj)
    if not quiet:
        print(f"  wrote {os.path.relpath(glb, ROOT)} -- {len(tris):,} triangles, "
              f"{len(groups)} groups, "
              f"{sum(1 for g in groups if g[0].startswith('doorpanel_'))} "
              f"pressure doors addressable")
    return glb, groups


def build(schema, profile, cand, rate=1.0, quiet=False):
    """Everything the runtime needs, as one manifest. Returns (man, path)."""
    res = cand["res"]
    r = route_for(schema, profile, cand)
    glb, groups = write_collision(cand, r, quiet=quiet)

    g_ms2 = P.place_gravity(res.home)
    speed = P._walk_speed(res.species, CROWD_LOD, g_ms2)
    cycle = P._walk_cycle_s(res.species, CROWD_LOD, g_ms2)
    walk_s = r["length_m"] / speed
    depart, start = cand["depart_h"], cand["start_h"]
    arrive = depart + walk_s / 3600.0

    m = r["meta"]
    home = DIR.by_key(res.home)
    job = DIR.by_key(res.job)
    groups = r.get("groups")
    spawn = list(W.room_target(m, home, r["verts"], r["tris"], groups))
    post = list(W.room_target(m, job, r["verts"], r["tris"], groups))
    assert_route_endpoints("L1", r["points"][0], r["points"][-1], spawn, post)

    # WHERE EVERY PRESSURE DOOR IS, so the runtime can open the one it is at.
    # Measured off the same `deck_plan` the panel was cut from, rather than
    # recovered from the mesh: asking geometry to give back what the generator
    # already knew is how the door leaves ended up 0.16 m out of their frame.
    doors = []
    for mm in r["all_meta"]["clusters"]:
        for row in mm.get("rooms", ()):
            doors.append({"key": row["key"], "deg": row["door_deg"],
                          "group": f"doorpanel_{row['key']}",
                          "at": list(RW._at(mm["floor_r_m"],
                                            row["door_deg"], mm["z_m"]))})

    omega = schema["station"]["rotation"]["omega_rad_s"]["value"]
    # THE WINDOW THE CLOCK RUNS OVER, in station hours. It starts far enough
    # before the resident's own departure to assert they were at home and
    # standing still, and ends far enough after arrival to assert they stayed.
    h0 = depart - PRE_S / 3600.0
    h1 = arrive + POST_S / 3600.0
    span_s = (h1 - h0) * 3600.0
    # THE TICK COUNT IS THE SAME AT EVERY RATE, and that is not an oversight.
    # `life.gd` raises `Engine.physics_ticks_per_second` with the clock rate so
    # a body's step in STATION time is 24 mm whatever the rate -- see the note
    # there. x60 buys station time, not wall time.
    frames = int(math.ceil(span_s * 60.0))
    lookahead = lookahead_m()

    man = {
        "kind": "agenda",
        "deck": cand["deck"], "sector": r["sector"], "ring": r["ring"],
        "deck_index": r["deck"],
        "who": {
            "id": res.npc_id, "name": res.name, "card_name": res.card_name,
            "species": res.species, "origin": res.origin, "age": res.age,
            "role": res.role, "home": res.home, "job": res.job,
            "pool": cand["pool"], "pool_i": cand["i"],
        },
        "shift": {"start_h": round(start, 4), "hours": cand["hours"],
                  "depart_h": round(depart, 4),
                  "arrive_h": round(arrive % 24.0, 4),
                  "transit_h": SC.TRANSIT_H,
                  "walk_s": round(walk_s, 1),
                  "slack_s": round(SC.TRANSIT_H * 3600.0 - walk_s, 1)},
        "gait": {"speed_ms": round(speed, 4), "cycle_s": round(cycle, 4),
                 "g_ms2": round(g_ms2, 4),
                 "froude_ms": round(NAV.walk_speed(g_ms2 / 9.80665,
                                                   res.species), 4)},
        "route": {"points": r["points"], "length_m": r["length_m"],
                  "legs": [{"kind": l["kind"], "note": l["note"],
                            "length_m": l["length_m"], "n": len(l["points"])}
                           for l in r["legs"]],
                  "door_home": r["door_home"], "door_job": r["door_job"],
                  "floor_r_m": m["floor_r_m"], "half_w_m": m["half_w_m"],
                  "corridor_z_m": m["z_m"]},
        # THE SAME SHAPE L3 USES, AND THAT IS THE POINT. A one-corridor commute
        # is a journey of ONE walking segment and no vehicle, so it is expressed
        # in the same segments-and-plan the lift commute is, and `life.gd` has
        # one runtime rather than two. `--walk` is then the regression test for
        # the generalisation: if the plan player broke the L1 case, L1's own
        # three rates and three controls say so.
        "segments": [{"kind": "walk", "index": 0, "points": r["points"],
                      "length_m": r["length_m"],
                      "legs": [{"kind": l["kind"], "note": l["note"],
                                "length_m": l["length_m"]} for l in r["legs"]]}],
        "plan": {
            "walk": [{"seg": 0, "t0": round(PRE_S, 4),
                      "t1": round(PRE_S + walk_s, 4),
                      "s0": 0.0, "s1": r["length_m"]}],
            "car": [], "door": [], "hold_in_car": [],
            "phases": [{"name": "before", "t0": 0.0, "t1": round(PRE_S, 4)},
                       {"name": "commute", "t0": round(PRE_S, 4),
                        "t1": round(PRE_S + walk_s, 4)},
                       {"name": "after", "t0": round(PRE_S + walk_s, 4),
                        "t1": round(span_s, 4)}],
        },
        "spawn": spawn, "home_at": spawn, "post_at": post,
        "doors": doors,
        "collision_glb": glb,
        "crowd_lod_glb": os.path.join(DECKDIR, f"crowd_lod{CROWD_LOD}.glb"),
        "crowd_mesh": P.crowd_key(res.species, CROWD_LOD, 0),
        "omega_rad_s": omega,
        "clock": {"start_h": round(h0, 6), "end_h": round(h1, 6),
                  "rate_x": rate, "span_s": round(span_s, 1)},
        "pre_s": PRE_S, "post_s": POST_S,
        "arrive_m": W.ARRIVED_M,
        "capsule_r_m": CAPSULE_R_M, "capsule_h_m": CAPSULE_H_M,
        "settle_frames": SETTLE_FRAMES,
        "lookahead_m": round(lookahead, 4),
        "catchup": CATCHUP,
        # A HARD CAP OVER AND ABOVE THE CLOCK. The clock ends the run; this
        # ends a run whose clock never got there, because a headless test that
        # does not finish costs a session rather than failing.
        "max_frames": int(frames * 1.5) + 600,
    }
    path = os.path.join(OUT, "agenda.json")
    with open(path, "w") as f:
        json.dump(man, f, indent=1)
    if not quiet:
        print(f"  wrote {os.path.relpath(path, ROOT)} -- {r['length_m']:,.0f} m "
              f"of route over {len(r['points'])} waypoints, "
              f"{span_s:,.0f} station seconds at x{rate:g} = "
              f"{frames:,} frames")
    return man, path


# ===========================================================================
# L3 -- THEY USE THE TRANSIT
# ===========================================================================
# WHY THIS IS A PREREQUISITE AND NOT A LATER RUNG, measured in L1 rather than
# argued: across the 857 residents baked into the shipped `<deck>_actors.json`
# who have both a home and a job, **not one has them on the same deck**. Ashir
# walks to work because they are one of exactly two people on the station who
# can. Everybody else needs the lift before they can execute their own day at
# all -- so "they use the transit" is not a feature on top of L1, it is the
# thing that makes L1 apply to anybody.
#
# WHAT IS REUSED, AND NONE OF IT IS REBUILT HERE:
#
#   routes.py            says the two places are joined, and by what kinds of
#                        leg -- ring, axial, lift, axial, ring
#   route_walk.py        the endpoint filter (does this deck HAVE a landing, is
#                        the landing at the corridor's own radius), the cluster
#                        shell with its junction aperture, the deck's spine, the
#                        column's static collision and its sealed control, and
#                        `legs_for` -- the waypoints and their door tolerances
#   transit_runtime.py   the car, its collision, its door leaves measured off
#                        the mesh, and the MOTION TABLES whose seconds are
#                        `navigation.lift_ride_s` and whose peak is asserted
#                        against the Coriolis cap before they are written
#   transit.gd           the moving car itself and the carry -- `life.gd`
#                        instantiates that script rather than reimplementing it,
#                        so there is ONE answer to "how does a floor take a body
#                        with it" and `transit_runtime.py --ride` still tests it
#
# WHAT IS NEW IS THE HAND-OFF, which is the hard part and the reason the ride
# gate is not this gate. `--ride` walks a body at a car that is already waiting
# with its doors open. A COMMUTER ARRIVES AT A LANDING WHERE THE CAR IS NOT.
# The car has to be called, has to travel, has to open, has to be boarded, has
# to shut, ride, open again -- and every one of those is a duration in STATION
# seconds that must hold at x60, where the clock moves 60 m of shaft a real
# second.
#
# THE TIMETABLE IS PURE IN THE HOUR, exactly as L1's `s(h)` is, and for the same
# reason: at x60 no physical simulation can be "run faster" and stay itself, so
# what is fast-forwarded is the CLOCK and what plays is a function of it. The
# car's position, the doors' opening and how far along their route the resident
# should be are all read off `t` -- so the x1, x10 and x60 runs are the same
# journey three times rather than three that happened to pass.
#
# AND THE BODY IS STILL PHYSICS. It is carried by the car's floor or it is not;
# it fits through the landing aperture or it does not. That is what makes the
# controls able to fire: with the car never called the timetable still runs and
# the resident is still standing in the lobby.


# HOW FAST A PRESSURE DOOR LEAF TRAVELS -- FETCHED, NOT COPIED.
# `godot/scripts/door.gd` decides it and `transit.gd` reads it out of that
# script at run time. The timetable needs the same number offline, so it is read
# out of the same file rather than written down here: a second copy of 1.6 would
# be a second decision about pressure doors.
def door_speed_ms():
    src = open(os.path.join(ROOT, "godot/scripts/door.gd")).read()
    m = re.search(r"var\s+speed_m_s\s*:\s*float\s*=\s*([0-9.]+)", src)
    if not m:
        raise AssertionError("godot/scripts/door.gd no longer declares "
                             "speed_m_s -- the timetable cannot time a door")
    return float(m.group(1))


_G3 = {}


def graph():
    """`routes.clusters` and `routes.edges`, once. Both are minutes of work."""
    if "nodes" not in _G3:
        schema, profile = it.load()
        _G3["nodes"] = RT.clusters()
        _G3["edges"] = RT.edges(_G3["nodes"], schema, profile=profile)
    return _G3["nodes"], _G3["edges"]


def endpoint_index(schema, profile):
    """place key -> the `route_walk.endpoints` row it sits on, plus the refusals.

    THE FILTER IS ROUTE_WALK'S AND ITS THREE REASONS ARE FINDINGS, not
    conveniences: `routes.py` grants every deck spine a lift edge to its ring's
    column unconditionally, and 57 of 96 clusters cannot actually use it --
    because the column has no landing at that deck's z, or because the landing
    and the deck's corridor are at different radii, or because extending the
    corridor to the transit angle moves the cluster's own room doors. The
    census below reports each one by name, so "how many can commute" cannot be
    made to look better by not asking.
    """
    if "by_place" in _G3:
        return _G3["by_place"], _G3["bad_place"]
    nodes, _es = graph()
    ok, bad = RW.endpoints(schema, profile, nodes)
    by_place, bad_place = {}, {}
    for row in ok:
        for p, _deg in row["doors"]:
            by_place[p] = row
    for row, why in bad:
        for p in row.get("places", ()):
            bad_place.setdefault(p, why)
    _G3["by_place"], _G3["bad_place"] = by_place, bad_place
    return by_place, bad_place


# THE COLUMN'S OWN LOBBY SEALS ANY RING CORRIDOR IT CROSSES, and that is the
# third defect this gate found. It is a hole in the station rather than in this
# file, so it is reported here and in docs/life-L3.md rather than patched.
#
# `transit_runtime.static_collision` gives every landing one
# `interior.AXIAL_SECTION_M` of lobby -- 9.2 m of axial corridor running away
# from the shaft. A ring corridor is an arc with walls at +-1.08 m of z. Where a
# cluster sits within a lobby's length of the column the two OVERLAP AT RIGHT
# ANGLES, and neither generator cuts an aperture for the other: the lobby's own
# side walls stand across the ring corridor, so a body that walks out of the
# lift into the crossing is in a 2.16 m box.
#
# Measured on `business_center` (red/1/0, z = 6604.48, column at z = 6600): the
# body rode the lift, alighted, reached the junction and **stopped 37.85 m from
# its post -- the whole length of the ring leg -- with 0 frames off the floor.**
# 744 m walked, 21.55 m ridden, and no arrival.
#
# `route_walk.choose` never meets it because it skips any pair whose spine is
# shorter than two lobby lengths. The test excluded the case; the station still
# has it, and 54 of the 470 baked residents commute through exactly that
# crossing.

def lobby_seals(row, g):
    """Does the column's landing lobby stand across this cluster's corridor?

    Both spans come from the generators that build them -- `lobby_span` is
    `transit_runtime`'s own, the corridor's half width is the kit's -- so this
    cannot drift from the geometry it describes.
    """
    import interior_kit as K                                      # noqa: PLC0415
    z0, z1 = TR.lobby_span(g)
    lo, hi = min(z0, z1), max(z0, z1)
    hw = K.PROVISIONAL["corridor_width_m"] / 2.0
    cz = row["cz"]
    return (cz - hw) < hi and (cz + hw) > lo


def column_collision(schema, profile, g, crossings=(), landings=True):
    """The column's static shell, WITH A DOORWAY WHERE A RING CORRIDOR CROSSES.

    `route_walk.column_collision` with one argument threaded through:
    `collision.axial_shell` already takes `doors` -- `(z, side)` pairs that cut
    a `door_width_m` aperture in one of the corridor's two side walls, exactly
    as the ring shell cuts one for a room -- and neither `transit_runtime` nor
    `route_walk` passes any. So the lobby is a sealed tube through the middle of
    any ring corridor it crosses.

    NOTHING IS AUTHORED HERE. The aperture is the kit's own door, cut by the
    generator that cuts every other door in the station, at the crossing the
    geometry already has. What it fixes is a station that has a lift lobby
    running through a corridor with no way between them -- see `lobby_seals`.

    `crossings` is `(landing_index, z_m)` pairs. With none, `_selftest3` asserts
    this is triangle-for-triangle `route_walk.column_collision`, so the
    duplication cannot drift.
    """
    sv, st, sm = L.lift_collision(schema, profile, g=g, car=False,
                                  landings=landings)
    verts, tris = list(sv), list(st)
    groups = [(f"liftshaft__{n}", a, b) for n, a, b in sm["groups"]]
    z0, z1 = TR.lobby_span(g)
    for lg in g["landings"]:
        doors = [(cz, side) for idx, cz in crossings
                 if idx == lg["index"] for side in (-1.0, 1.0)]
        lv, lt, _lm = C.axial_shell(schema, profile, g["sector"],
                                    g["ring_index"], z0, z1,
                                    angle_deg=g["angle_deg"],
                                    radius_m=lg["floor_r_m"], doors=doors)
        o, t0 = len(verts), len(tris)
        verts.extend(lv)
        tris.extend((a + o, b + o, c + o) for a, b, c in lt)
        groups.append((f"liftlobby_{lg['index']}", t0, len(tris)))
    return verts, tris, groups


def commutable(home, job, by_place, g=None):
    """Can THIS pair be commuted by the machinery below? -> (bool, reason).

    One column, two landings. A pair on two different rings needs the spoke and
    a pair in two different sectors needs the trunk; both edges exist in
    `routes.py` and neither has a walkable runtime, so they are reported as
    what they are rather than counted as failures of the lift.
    """
    a, b = DIR.by_key(home), DIR.by_key(job)
    if a is None or b is None or a.get("sector") is None or b.get("sector") is None:
        return False, "one end is not a located place"
    if (a["sector"], a["ring"], a["deck"]) == (b["sector"], b["ring"], b["deck"]):
        return False, "same deck -- this is L1, no transit needed"
    if a["sector"] != b["sector"]:
        return False, "different sectors -- needs the trunk between columns"
    if a["ring"] != b["ring"]:
        return False, "different rings -- needs the spoke between columns"
    for k, p in ((home, a), (job, b)):
        if k not in by_place:
            return False, f"{k}: " + _G3["bad_place"].get(
                k, "not on a cluster a route can start or end in")
    return True, "one column, two landings"


def cross_deck_pairs(schema, profile):
    """Every (species, role, home, job) the lift can actually carry.

    THE SAME CHEAP PRE-FILTER L1 USES. `home_for` and `workplace_places` are
    pure functions of (species, role), so this is 19 roles x 14 species rather
    than a scan of every resident on the station -- and it cannot invent a
    pairing the generator does not make, because it IS the generator's two
    functions.
    """
    by_place, _bad = endpoint_index(schema, profile)
    nodes, _es = graph()
    shafts = {}
    out = []
    for role in SC.ROLES:
        if role.work_hours <= 0:
            continue
        try:
            jobs = RS.workplace_places(role.workplace)
        except Exception:                                       # noqa: BLE001
            continue
        for species in sorted(SC.STATION_MIX):
            if species in SC.SPECIES_WITHOUT_NAMES:
                continue
            home = RS.home_for(f"probe:{species}:{role.key}", species,
                               role.key)
            for job in jobs:
                sec = (DIR.by_key(home) or {}).get("sector")
                if sec and sec not in shafts:
                    shafts[sec] = RW.shaft(schema, profile, nodes, sec)
                ok, _why = commutable(home, job, by_place, shafts.get(sec))
                if ok:
                    out.append({"species": species, "role": role.key,
                                "home": home, "job": job})
    return out


def candidates3(schema, profile, limit=1200, want=8):
    """Named residents whose home and post are on DIFFERENT decks of one column.

    From the pool the room itself is cast from, exactly as L1's `candidates`:
    `resident.pool_id` in order, so the person who commutes is a person
    `populace.populate` would have put in that room anyway.
    """
    out, seen = [], set()
    for w in cross_deck_pairs(schema, profile):
        key = (w["species"], w["home"], w["job"])
        if key in seen:
            continue
        seen.add(key)
        for pool in (w["job"], w["home"]):
            hit = None
            for i in range(limit):
                npc_id = RS.pool_id(pool, w["species"], i, "b5")
                try:
                    res = RS.resident(npc_id, w["species"])
                except Exception:                               # noqa: BLE001
                    continue
                if (res.home, res.job) != (w["home"], w["job"]) or not res.name:
                    continue
                sched = clean_commute(npc_id, w["species"])
                if sched is None:
                    continue
                hit = {"pool": pool, "i": i, "res": res,
                       "depart_h": sched[0], "start_h": sched[1],
                       "hours": sched[2]}
                break
            if hit:
                out.append(hit)
                break
        if len(out) >= want:
            break
    out.sort(key=lambda r: (r["i"], r["res"].species, r["pool"]))
    return out


def choose3(schema, profile, who=None):
    cs = candidates3(schema, profile)
    if who:
        for c in cs:
            if c["res"].npc_id == who:
                return c
        raise ValueError(f"{who} does not commute between two decks of one "
                         f"column -- run --report3 for the list")
    if not cs:
        raise ValueError("no named resident has their home and their post on "
                         "two decks of one transit column")
    return cs[0]


# ---------------------------------------------------------------------------
# THE JOURNEY -- two decks, a column, and the geometry under all of it
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# A RING CORRIDOR RUNS ONE WAY ROUND, AND THE SHORT WAY IS OFTEN NOT IT
# ---------------------------------------------------------------------------
# THE DEFECT THIS FUNCTION EXISTS FOR, measured on the first run of this gate.
# `route_walk._arc_points(a0, a1)` sweeps from one angle to the other by the
# SIGNED SHORTEST arc -- `((a1 - a0) + 180) % 360 - 180` -- which is the right
# answer on a full ring and the wrong one on an arc. Red ring 1 deck 6 carries
# `qtr_civilian` at 280 deg and red's transit angle is 90 deg; the corridor
# `deck_plan(must_cover=90)` builds spans **78 deg to 292 deg**, so the way
# round is DOWNWARD, -190 deg. The shortest way is +170 deg, through 0 deg, and
# every metre of it is outside the shell.
#
# Measured: the body walked **46.3 m of a 588 m arc, fell off the end of the
# corridor, and was still falling 46,031 frames later** at r = 20,188 m, with a
# lag of 9.7e123 m. Which is also the answer to why no gate caught it --
# `route_walk.endpoints` asks whether the corridor REACHES the transit angle,
# and a corridor can reach it in one direction while the route is laid in the
# other. `legs_for` has the same defect and its own chosen route does not
# expose it; that is reported in docs/life-L3.md rather than patched, because
# `route_walk.py` is not this session's file.

def arc_in_corridor(radius, a0, a1, z, lo, span):
    """Waypoints from `a0` to `a1` along the corridor THAT WAS BUILT.

    Both ways round are tried and the shorter one that lies wholly inside
    `[lo, lo + span]` wins. Raises rather than picking one anyway: a route
    through a wall is not a shorter route.
    """
    def inside(a):
        return ((a - lo) % 360.0) <= span + 1e-6

    best = None
    for d in (((a1 - a0) % 360.0), ((a1 - a0) % 360.0) - 360.0):
        n = max(1, int(math.ceil(abs(d) / RW.RING_STEP_DEG)))
        angs = [a0 + d * i / n for i in range(n + 1)]
        if all(inside(a) for a in angs) and (best is None
                                             or abs(d) < abs(best[0])):
            best = (d, angs)
    if best is None:
        raise AssertionError(
            f"neither way round from {a0:.1f} deg to {a1:.1f} deg stays inside "
            f"the corridor that was built ({lo:.1f} deg for {span:.1f} deg) -- "
            f"a body steered along either one walks off the end of the shell")
    return [RW._at(radius, a, z) for a in best[1]]


def corridor_span(meta, row=None):
    """(start_deg, arc_deg) of the shell a body is about to be walked along.

    Off the corridor's OWN meta -- `collision.corridor_shell` records the arc it
    swept -- rather than recomputed from a plan, so it cannot describe a
    different corridor from the one that was written.
    """
    if meta.get("arc_deg") is not None and meta.get("start_deg") is not None:
        return float(meta["start_deg"]), float(meta["arc_deg"])
    if row is not None and row.get("arc"):
        lo, hi = row["arc"]
        return float(lo), float(hi) - float(lo)
    raise AssertionError("this corridor's shell does not say what arc it "
                         "covers, so no route can be laid in it")


def relay_ring(legs, radius, z, lo, span):
    """Re-lay every ring leg's arc the way its corridor actually runs.

    `route_walk.legs_for` is imported rather than reimplemented -- its doorway
    aim points and its tolerances are the thing worth having -- and this is the
    one correction its arc needs. The tolerance pattern is preserved: the leg's
    own last (or first) waypoint is the tight one, because that is the one in a
    doorway.
    """
    out = []
    for l in legs:
        if l["kind"] != "ring" or len(l["points"]) < 2:
            out.append(l)
            continue
        a0 = math.degrees(math.atan2(l["points"][0][1], l["points"][0][0]))
        a1 = math.degrees(math.atan2(l["points"][-1][1], l["points"][-1][0]))
        pts = arc_in_corridor(radius, a0, a1, z, lo, span)
        tight = [i for i, t in enumerate(l["tols"])
                 if t < RW.WAYPOINT_TOL_M - 1e-9]
        which = []
        for i in tight:
            which.append(0 if i == 0 else len(pts) - 1)
        out.append(RW._leg("ring", l["note"], pts,
                           RW._tight(pts, which, RW.door_tol_m())))
    return out


# ---------------------------------------------------------------------------
# AND A SPINE LEG MUST NOT DOUBLE BACK THROUGH ITS OWN JUNCTION
# ---------------------------------------------------------------------------
# THE SECOND DEFECT THIS GATE FOUND, and it is the same shape as the first: a
# rule that is right when the cluster is far from the column and wrong when it
# is close. `route_walk.legs_for` walks the inbound leg
#
#     lobby stand -> aim point at (cz - hw - AIM_M) -> the junction at cz
#
# which assumes the lobby is on the far side of the aim point. `business_center`
# sits on red ring 1 deck 0 at **z = 6604.48**, the column stands at **6600**,
# and the landing lobby's own stand point is at **6605.93** -- so the ring
# corridor lies BETWEEN the car and the lobby, and that leg walks +5.9 m, back
# -4.5 m, then +3.1 m, crossing its own junction twice.
#
# Measured, that is not merely inelegant: the polyline visits z = 6604.5 THREE
# TIMES, so `Route.advance` -- which takes the nearest point within a 12 m
# window -- matched the body to a point 9 m further along than it had walked,
# the carrot went BEHIND the body, and it stalled 37.85 m short of its post
# with the agenda finishing without it. **756.4 m on the floor, 0 frames off
# it, and no arrival.**
#
# `route_walk.choose` never sees this because it SKIPS any pair whose spine is
# shorter than two `interior.AXIAL_SECTION_M` -- the case is excluded rather
# than handled, and a commuter does not get to choose where they work.

def trim_axial(legs, junction_z, shaft_z):
    """Drop any axial waypoint that overshoots the junction.

    The spine is walked in ONE direction: from the column towards the cluster,
    or back. Every waypoint therefore belongs between the shaft's z and the
    junction's, and one that does not is a detour through the very doorway the
    leg is approaching.
    """
    lo, hi = min(junction_z, shaft_z), max(junction_z, shaft_z)
    out = []
    for l in legs:
        if l["kind"] != "axial":
            out.append(l)
            continue
        keep = [(p, t) for p, t in zip(l["points"], l["tols"])
                if lo - 1e-6 <= p[2] <= hi + 1e-6]
        if len(keep) < 2 or len(keep) == len(l["points"]):
            out.append(l)
            continue
        pts = [p for p, _t in keep]
        out.append(RW._leg("axial", l["note"] + " (trimmed: the ring corridor "
                                                "stands between the column and "
                                                "its lobby)",
                           pts, [t for _p, t in keep]))
    return out


def park_landing(g, a, b):
    """Where the car is standing when the resident sets out, and it is NOT
    their landing.

    THE FURTHEST LANDING FROM THEM THAT IS NOT THEIR DESTINATION EITHER. A car
    already waiting at your floor is the case `--ride` tests; a commuter's car
    is somewhere else and has to be called, which is the whole of the hand-off
    this milestone is about. Furthest, so the wait is the longest this column
    can produce rather than the shortest.
    """
    best, far = None, -1.0
    for i, lg in enumerate(g["landings"]):
        if i in (a, b):
            continue
        d = abs(lg["walk_r_m"] - g["landings"][a]["walk_r_m"])
        if d > far:
            best, far = i, d
    return best if best is not None else (b if b != a else a)


def journey_for(schema, profile, cand, quiet=True):
    """Every waypoint from the resident's bunk to their desk, and the shells.

    Three segments: walk out of the quarters, along the ring corridor, down the
    deck's spine and into the car; RIDE; and out of the car, along the other
    deck's spine and corridor, and into the room they work in.
    """
    res = cand["res"]
    nodes, es = graph()
    by_place, _bad = endpoint_index(schema, profile)
    a_row, b_row = by_place[res.home], by_place[res.job]
    sector = a_row["sector"]
    g = RW.shaft(schema, profile, nodes, sector)
    # WHERE A LOBBY STANDS ACROSS A RING CORRIDOR, CUT THE DOORWAY. See
    # `lobby_seals` for what this costs when it is not done: the body rides the
    # lift, alights, reaches the junction and stops 37.85 m from its post.
    crossings = [(row["landing"], row["cz"])
                 for row in (a_row, b_row) if lobby_seals(row, g)]

    a_v, a_t, a_g, a_meta = RW.cluster_collision(
        schema, profile, a_row["sector"], a_row["ring"], a_row["deck"],
        a_row["z"], a_row["spine_deg"])
    b_v, b_t, b_g, b_meta = RW.cluster_collision(
        schema, profile, b_row["sector"], b_row["ring"], b_row["deck"],
        b_row["z"], b_row["spine_deg"])

    la, lb = a_row["landing"], b_row["landing"]
    lobby_a = list(TR.lobby_stand(g, g["landings"][la]))
    lobby_b = list(TR.lobby_stand(g, g["landings"][lb]))
    car_a = list(L.stand_in_car(g, at_deck=g["landings"][la]))
    car_b = list(L.stand_in_car(g, at_deck=g["landings"][lb]))

    tol = RW.door_tol_m()
    a_lo, a_span = corridor_span(a_meta, a_row)
    b_lo, b_span = corridor_span(b_meta, b_row)
    seg0_legs = [room_legs(schema, profile, a_meta, res.home, outward=True,
                           verts=a_v, tris=a_t, groups=a_g)]
    seg0_legs += trim_axial(relay_ring(
        RW.legs_for(schema, profile, a_row, a_meta, g, res.home,
                    outbound=True, verts=a_v, tris=a_t, groups=a_g),
        a_meta["floor_r_m"], a_meta["z_m"], a_lo, a_span),
        a_meta["z_m"], g["z_m"])
    # WHERE THEY WAIT FOR THE CAR is wherever their own deck's walk ends, which
    # is the landing lobby on a deck with a spine and the mouth of the aperture
    # on a deck that sits on top of the column. Taken from the leg rather than
    # assumed, so the two cases need no branch.
    wait_at = list(seg0_legs[-1]["points"][-1])
    seg0_legs.append(RW._leg(
        "board", f"across the landing at deck {a_row['deck']} and into "
                 f"the car", [wait_at, car_a],
        RW._tight([wait_at, car_a], [1], tol)))
    b_legs = trim_axial(relay_ring(
        RW.legs_for(schema, profile, b_row, b_meta, g, res.job,
                    outbound=False, verts=b_v, tris=b_t, groups=b_g),
        b_meta["floor_r_m"], b_meta["z_m"], b_lo, b_span),
        b_meta["z_m"], g["z_m"])
    step_off = list(b_legs[0]["points"][0])
    seg2_legs = [RW._leg(
        "alight", f"out of the car at deck {b_row['deck']} and onto the "
                  f"landing", [car_b, step_off],
        RW._tight([car_b, step_off], [0], tol))]
    seg2_legs += b_legs

    # AND THE ROOM LEGS ARE INSIDE THE CORRIDOR TOO, asserted rather than
    # assumed: every waypoint at the corridor's own radius has to be on the arc
    # that was built, or the route is a route through a wall.
    for legs, lo, span, r_m in ((seg0_legs, a_lo, a_span, a_meta["floor_r_m"]),
                                (seg2_legs, b_lo, b_span, b_meta["floor_r_m"])):
        for l in legs:
            if l["kind"] not in ("ring", "room"):
                continue
            for q in l["points"]:
                if abs(math.hypot(q[0], q[1]) - r_m) > 0.2:
                    continue
                a = math.degrees(math.atan2(q[1], q[0]))
                if ((a - lo) % 360.0) > span + 1e-6:
                    raise AssertionError(
                        f"a waypoint of the {l['kind']} leg stands at "
                        f"{a:.1f} deg and its corridor covers {lo:.1f} deg for "
                        f"{span:.1f} deg -- that point is outside the shell")

    def polyline(legs):
        pts = []
        for l in legs:
            for q in l["points"]:
                if not pts or math.dist(pts[-1], q) > 1e-6:
                    pts.append(list(q))
        return pts

    seg0 = polyline(seg0_legs)
    seg2 = polyline(seg2_legs)

    def length(pts):
        return sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))

    # WHERE THE WAIT HAPPENS -- how far along segment 0 they stop for the car.
    # Taken from the polyline itself rather than by adding the legs up, because
    # the polyline is what the body walks and the two differ by the welds.
    i_wait = min(range(len(seg0)), key=lambda i: math.dist(seg0[i], wait_at))
    s_land = length(seg0[:i_wait + 1])
    if math.dist(seg0[i_wait], wait_at) > 1e-6:
        raise AssertionError("the point they wait at is not a waypoint of the "
                             "outbound segment")

    # AND THE WALK IS MONOTONE THROUGH ITS OWN JUNCTIONS. A polyline that
    # revisits a place has two answers to "how far along is this body", and
    # `Route.advance` takes the nearest -- which is how the first run of this
    # gate put the carrot nine metres BEHIND the body. Asserted rather than
    # hoped for: no two non-adjacent waypoints may be closer than a capsule.
    for pts, nm in ((seg0, "outbound"), (seg2, "inbound")):
        for i in range(len(pts)):
            for j in range(i + 2, len(pts)):
                if math.dist(pts[i], pts[j]) < CAPSULE_R_M:
                    raise AssertionError(
                        f"the {nm} route passes within "
                        f"{math.dist(pts[i], pts[j]):.2f} m of itself between "
                        f"waypoint {i} and waypoint {j} -- a body on it has two "
                        f"answers to how far it has got")

    return {"a_row": a_row, "b_row": b_row, "g": g, "sector": sector,
            "a": (a_v, a_t, a_g, a_meta), "b": (b_v, b_t, b_g, b_meta),
            "seg0": seg0, "seg2": seg2,
            "seg0_legs": seg0_legs, "seg2_legs": seg2_legs,
            "len0": length(seg0), "len2": length(seg2), "s_land": s_land,
            "lobby_a": lobby_a, "lobby_b": lobby_b,
            "car_a": car_a, "car_b": car_b,
            "landing_a": la, "landing_b": lb, "crossings": crossings,
            "park": park_landing(g, la, lb)}


def timetable(j, lift_man, speed, depart_s):
    """The journey in station seconds, and every duration is somebody else's.

        the walk        the polyline's own length over `populace._walk_speed`,
                        the gait the resident's walk clip is animated at
        the car's ride  `transit_runtime`'s motion table, whose seconds are
                        `navigation.lift_ride_s` and whose peak is asserted
                        against the Coriolis cap before it is written
        the doors       the leaves' MEASURED travel over `door.gd`'s own speed
        the dwell       `navigation.TRANSIT_DWELL_S`

    Returns (plan, marks). The plan is what `life.gd` plays; the marks are the
    named instants, for the report and for the costing cross-check.
    """
    rides = lift_man["rides"]
    la, lb, pk = j["landing_a"], j["landing_b"], j["park"]
    call_s = rides[f"{pk}-{la}"]["seconds"] if pk != la else 0.0
    ride_s = rides[f"{la}-{lb}"]["seconds"]
    door_s = max(lift_man["leaf_travel_m"].values()) / door_speed_ms()
    dwell = lift_man["dwell_s"]

    t_depart = depart_s
    t_land = t_depart + j["s_land"] / speed          # they reach the landing
    t_call = t_land                                  # and call the car
    t_car = t_call + call_s                          # it arrives
    t_open = t_car + door_s                          # its doors open
    t_board = t_open + (j["len0"] - j["s_land"]) / speed
    t_shut0 = max(t_board, t_open + dwell)           # it waits its own dwell
    t_shut1 = t_shut0 + door_s
    t_ride1 = t_shut1 + ride_s
    t_open2 = t_ride1 + door_s
    t_walk2 = t_open2 + j["len2"] / speed

    def row(t0, t1, **kw):
        d = {"t0": round(t0, 4), "t1": round(t1, 4)}
        d.update(kw)
        return d

    y = [float(lg["y_m"]) for lg in lift_man["landings"]]
    plan = {
        "walk": [row(t_depart, t_land, seg=0, s0=0.0, s1=j["s_land"]),
                 row(t_open, t_board, seg=0, s0=j["s_land"], s1=j["len0"]),
                 row(t_open2, t_walk2, seg=2, s0=0.0, s1=j["len2"])],
        # The car: parked, called, then the ride the passenger is in.
        "car": [row(t_call, t_car, y0=y[pk], y1=y[la],
                    table=f"{pk}-{la}"),
                row(t_shut1, t_ride1, y0=y[la], y1=y[lb],
                    table=f"{la}-{lb}")],
        "door": [row(t_car, t_open, f0=0.0, f1=1.0),
                 row(t_shut0, t_shut1, f0=1.0, f1=0.0),
                 row(t_ride1, t_open2, f0=0.0, f1=1.0)],
        # WHERE THE BODY STANDS IN THE CAR RATHER THAN ON A ROUTE. From the
        # moment it is aboard to the moment the far doors are open, the thing
        # it is steered at is the car's own stand point, which MOVES -- so a
        # body that is not carried reads a lag of the whole shaft.
        "hold_in_car": [row(t_board, t_open2)],
        "phases": [row(0.0, t_depart, name="before"),
                   row(t_depart, t_land, name="walk_a"),
                   row(t_land, t_open, name="wait"),
                   row(t_open, t_shut1, name="board"),
                   row(t_shut1, t_ride1, name="ride"),
                   row(t_ride1, t_open2, name="open"),
                   row(t_open2, t_walk2, name="walk_b"),
                   row(t_walk2, t_walk2 + POST_S, name="after")],
    }
    marks = {"depart": t_depart, "landing": t_land, "car_here": t_car,
             "doors_open": t_open, "aboard": t_board, "doors_shut": t_shut1,
             "alight": t_ride1, "arrive": t_walk2,
             "call_s": call_s, "ride_s": ride_s, "door_s": door_s,
             "dwell_s": dwell,
             "walk_a_s": t_land - t_depart, "walk_b_s": t_walk2 - t_open2,
             "wait_s": t_open - t_land, "journey_s": t_walk2 - t_depart}
    return plan, marks


def costing(schema, profile, j, marks, res):
    """What `station/transit.py` says this journey costs, computed its way.

    A CROSS-CHECK, NOT A SOURCE. `transit.py` costs a journey from the register:
    a Manhattan walk between two places' own (z, angle) at the rim's gravity,
    plus `climb_leg` for the radial move, plus a dwell. The timetable above
    costs it from the geometry a body actually walks -- the real corridor arc,
    the deck's spine, the lobby -- at `populace._walk_speed`. The two SHOULD
    differ, and by how much and in which direction is the interesting number:
    a Manhattan walk between two room centres does not know about the ring the
    corridor has to go round to reach the spine.

    The ride is the part that must agree, because both ends of it derive from
    the same smoothstep: `transit.climb_leg` and `navigation.lift_ride_s` share
    no code and are asserted against each other here.
    """
    a, b = DIR.by_key(res.home), DIR.by_key(res.job)
    walk = T.walk_leg(schema, profile, a, b, label=f"{res.home} -> {res.job}")
    rise = abs(j["g"]["landings"][j["landing_a"]]["walk_r_m"]
               - j["g"]["landings"][j["landing_b"]]["walk_r_m"])
    climb = T.climb_leg(schema, rise, label="the lift")
    jr = T.journey(f"{res.name} to work",
                   [walk, climb,
                    {"kind": "wait", "label": "the car's dwell",
                     "distance_m": 0.0, "seconds": marks["dwell_s"],
                     "detail": "navigation.TRANSIT_DWELL_S"}])
    return {"walk_s": walk["seconds"], "walk_m": walk["distance_m"],
            "walk_detail": walk["detail"],
            "climb_s": climb["seconds"], "rise_m": rise,
            "climb_detail": climb["detail"],
            "journey_s": jr["seconds"], "ours_s": marks["journey_s"],
            "ride_s": marks["ride_s"],
            "ride_delta_s": marks["ride_s"] - climb["seconds"],
            "delta_s": marks["journey_s"] - jr["seconds"]}


def build3(schema, profile, cand, rate=1.0, quiet=False):
    """Every shell, the car, the timetable and the manifest. -> (man, path)."""
    os.makedirs(OUT, exist_ok=True)
    res = cand["res"]
    j = journey_for(schema, profile, cand, quiet=quiet)

    # THE LIFT'S OWN RUNTIME ARTEFACTS, from the module that owns them, into
    # this file's directory -- session 3w's lesson, that disjoint source files
    # are not disjoint artefacts. `transit_runtime.OUT` is also `--ride`'s.
    import contextlib                                             # noqa: PLC0415
    import io                                                     # noqa: PLC0415
    keep_tr, keep_rw = TR.OUT, RW.OUT
    TR.OUT = RW.OUT = OUT
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            lift_man = TR.build_lift(schema, profile, j["g"], quiet=True)
            # THE COLUMN'S SHELL, WITH THE CROSSING DOORWAYS THIS JOURNEY
            # NEEDS -- see `column_collision`. It replaces the one
            # `build_lift` just wrote, which has none.
            ov, ot, og = column_collision(schema, profile, j["g"],
                                          crossings=j["crossings"])
            lift_man["static_col_glb"] = RW._write("lift_static_col_open",
                                                   ov, ot, og)
            # AND THE CONTROL'S SHELL, from the generator's own negative
            # control: `lift.lift_collision(landings=False)` seals every landing
            # aperture. A slab invented to stand in a doorway would be a control
            # against geometry nobody ships.
            sv, st, sg = column_collision(schema, profile, j["g"],
                                          crossings=j["crossings"],
                                          landings=False)
            sealed = RW._write("lift_static_col_sealed", sv, st, sg)
    finally:
        TR.OUT, RW.OUT = keep_tr, keep_rw

    files = []
    for tag, (v, t, gr, meta) in (("cluster_a", j["a"]), ("cluster_b", j["b"])):
        obj = os.path.join(OUT, tag + "_col.obj")
        C.write_obj(obj, v, t, gr, name="agenda")
        files.append(_glb(obj))
        os.remove(obj)
    # AND A SPINE IS ONLY BUILT WHERE THERE IS SPINE TO BUILD.
    #
    # `route_walk.build` runs one from the lobby's far end to the cluster's own
    # corridor wall. On a deck that sits ON TOP of the column those two are the
    # wrong way round -- the lobby ends at z = 6610.53 and `business_center`'s
    # corridor wall is at 6603.40 -- so the "spine" is a 7 m axial corridor laid
    # BACKWARDS, straight through the ring corridor it is supposed to meet, and
    # its side walls seal that corridor exactly as the lobby's did. Cutting the
    # lobby's crossing doorway changed nothing at all, byte for byte in the
    # verdict, because this second tube was still standing across it.
    #
    # There is nothing to build: the lobby already covers that z. Skipping it is
    # not a workaround, it is the answer to "how much corridor is between the
    # landing and the junction" being NONE.
    z_lobby_end = TR.lobby_span(j["g"])[1]
    lo_l, hi_l = sorted(TR.lobby_span(j["g"]))
    for tag, row, meta in (("a", j["a_row"], j["a"][3]),
                           ("b", j["b_row"], j["b"][3])):
        wall = meta["z_m"] - math.copysign(meta["half_w_m"],
                                           meta["z_m"] - z_lobby_end)
        if lo_l - 1e-6 <= wall <= hi_l + 1e-6:
            if not quiet:
                print(f"  no spine on deck {row['deck']}: its corridor wall at "
                      f"z={wall:.2f} is inside the landing lobby "
                      f"({lo_l:.2f}..{hi_l:.2f}), which is already the floor "
                      f"between them")
            continue
        sv2, st2, _sm = RW.spine(schema, profile, row["sector"], row["ring"],
                                 meta["radius_m"], row["spine_deg"],
                                 z_lobby_end, wall)
        obj = os.path.join(OUT, f"spine_{tag}_col.obj")
        C.write_obj(obj, sv2, st2, [(f"spine_{tag}", 0, len(st2))],
                    name="agenda")
        files.append(_glb(obj))
        os.remove(obj)

    g_ms2 = P.place_gravity(res.home)
    speed = P._walk_speed(res.species, CROWD_LOD, g_ms2)
    cycle = P._walk_cycle_s(res.species, CROWD_LOD, g_ms2)
    depart, start = cand["depart_h"], cand["start_h"]
    plan, marks = timetable(j, lift_man, speed, PRE_S)
    cost = costing(schema, profile, j, marks, res)

    span_s = marks["arrive"] + POST_S
    h0 = depart - PRE_S / 3600.0
    h1 = h0 + span_s / 3600.0
    frames = int(math.ceil(span_s * 60.0))

    # Every pressure door on both cluster shells, so the runtime can open the
    # one the body is standing at. Measured off the plan the panel was cut
    # from, never recovered from the mesh.
    doors = []
    for meta in (j["a"][3], j["b"][3]):
        for row in meta.get("rooms", ()):
            doors.append({"key": row["key"], "deg": row["door_deg"],
                          "group": f"doorpanel_{row['key']}",
                          "at": list(RW._at(meta["floor_r_m"],
                                            row["door_deg"], meta["z_m"]))})

    home_at = list(W.room_target(j["a"][3], DIR.by_key(res.home),
                                 j["a"][0], j["a"][1], j["a"][2]))
    post_at = list(W.room_target(j["b"][3], DIR.by_key(res.job),
                                 j["b"][0], j["b"][1], j["b"][2]))
    assert_route_endpoints("L3", j["seg0"][0], j["seg2"][-1], home_at, post_at)
    man = {
        "kind": "commute",
        "sector": j["sector"], "ring": j["a_row"]["ring"],
        "deck": f"{j['a_row']['sector']}_{j['a_row']['ring']}_"
                f"{j['a_row']['deck']}",
        "deck_from": f"{j['a_row']['sector']}/{j['a_row']['ring']}/"
                     f"{j['a_row']['deck']}",
        "deck_to": f"{j['b_row']['sector']}/{j['b_row']['ring']}/"
                   f"{j['b_row']['deck']}",
        "who": {"id": res.npc_id, "name": res.name,
                "card_name": res.card_name, "species": res.species,
                "origin": res.origin, "age": res.age, "role": res.role,
                "home": res.home, "job": res.job,
                "pool": cand["pool"], "pool_i": cand["i"]},
        "shift": {"start_h": round(start, 4), "hours": cand["hours"],
                  "depart_h": round(depart, 4),
                  "arrive_h": round((depart + marks["journey_s"] / 3600.0)
                                    % 24.0, 4),
                  "transit_h": SC.TRANSIT_H,
                  "walk_s": round(marks["journey_s"], 1),
                  "slack_s": round(SC.TRANSIT_H * 3600.0
                                   - marks["journey_s"], 1)},
        "gait": {"speed_ms": round(speed, 4), "cycle_s": round(cycle, 4),
                 "g_ms2": round(g_ms2, 4),
                 "froude_ms": round(NAV.walk_speed(g_ms2 / 9.80665,
                                                   res.species), 4)},
        "segments": [
            {"kind": "walk", "index": 0, "points": j["seg0"],
             "length_m": round(j["len0"], 3),
             "legs": [{"kind": l["kind"], "note": l["note"],
                       "length_m": l["length_m"]} for l in j["seg0_legs"]]},
            {"kind": "ride", "index": 1,
             "from_landing": j["landing_a"], "to_landing": j["landing_b"],
             "rise_m": round(cost["rise_m"], 3)},
            {"kind": "walk", "index": 2, "points": j["seg2"],
             "length_m": round(j["len2"], 3),
             "legs": [{"kind": l["kind"], "note": l["note"],
                       "length_m": l["length_m"]} for l in j["seg2_legs"]]},
        ],
        "plan": plan,
        "marks": {k: round(v, 3) for k, v in marks.items()},
        "costing": {k: (round(v, 3) if isinstance(v, float) else v)
                    for k, v in cost.items()},
        "lift": {
            "static_col_glb": lift_man["static_col_glb"],
            "static_col_sealed_glb": sealed,
            "car_glb": lift_man["car_glb"],
            "car_col_glb": lift_man["car_col_glb"],
            "origin": lift_man["origin"], "ux": lift_man["ux"],
            "uy": lift_man["uy"], "travel_axis": lift_man["travel_axis"],
            "pivot": lift_man["pivot"],
            "leaf_travel": lift_man["leaf_travel"],
            "leaf_travel_m": lift_man["leaf_travel_m"],
            "car": lift_man["car"], "bore_hd": lift_man["bore_hd"],
            "landings": lift_man["landings"], "rides": lift_man["rides"],
            "dwell_s": lift_man["dwell_s"], "g0_m_s2": lift_man["g0_m_s2"],
            "v_cap_m_s": lift_man["v_cap_m_s"],
            "from_landing": j["landing_a"], "to_landing": j["landing_b"],
            "park_landing": j["park"],
            "car_stand_from": j["car_a"], "car_stand_to": j["car_b"],
            "landing_stand_from": j["lobby_a"],
            "landing_stand_to": j["lobby_b"],
        },
        "spawn": home_at, "home_at": home_at, "post_at": post_at,
        "doors": doors,
        "collision_glbs": files,
        "crowd_lod_glb": os.path.join(DECKDIR, f"crowd_lod{CROWD_LOD}.glb"),
        "crowd_mesh": P.crowd_key(res.species, CROWD_LOD, 0),
        "crowd_lod": CROWD_LOD,
        "omega_rad_s": schema["station"]["rotation"]["omega_rad_s"]["value"],
        "clock": {"start_h": round(h0, 6), "end_h": round(h1, 6),
                  "rate_x": rate, "span_s": round(span_s, 1)},
        "pre_s": PRE_S, "post_s": POST_S,
        "arrive_m": W.ARRIVED_M,
        "capsule_r_m": CAPSULE_R_M, "capsule_h_m": CAPSULE_H_M,
        "settle_frames": SETTLE_FRAMES,
        "lookahead_m": round(lookahead_m(), 4),
        "catchup": CATCHUP,
        "max_frames": int(frames * 1.5) + 600,
    }
    path = os.path.join(OUT, "commute.json")
    with open(path, "w") as f:
        json.dump(man, f, indent=1)
    if not quiet:
        print(f"  wrote {os.path.relpath(path, ROOT)} -- "
              f"{j['len0']:,.0f} m + a {cost['rise_m']:.1f} m ride + "
              f"{j['len2']:,.0f} m, {span_s:,.0f} station seconds = "
              f"{frames:,} frames")
    return man, path


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------

def run(path, godot, engine_root, timeout=1800, verbose=False, **switch):
    cmd = [godot, "--headless", "--fixed-fps", "60",
           "--path", engine_root, "--script", "res://scripts/life.gd", "--",
           "--agenda-test", f"--manifest={path}"]
    for k, v in switch.items():
        cmd.append(f"--{k}={v}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    out = p.stdout + p.stderr
    if verbose:
        print(out)
    # A GDSCRIPT THAT DOES NOT PARSE DOES NOT FAIL -- IT IDLES, and the first
    # symptom is indistinguishable from a slow walk. `route_walk.run` learned
    # this the expensive way; the check is the same one.
    if "Failed to load script" in out or "Parse Error" in out:
        bad = [l for l in out.splitlines()
               if "SCRIPT ERROR" in l or "Parse Error" in l
               or "Failed to load" in l]
        return {"error": "godot/scripts/life.gd did not load",
                "tail": "\n".join(bad[:6])}
    m = re.search(r"AGENDATEST (.+)", out)
    if not m:
        return {"error": "no verdict printed",
                "tail": "\n".join(out.strip().splitlines()[-25:])}
    d = {}
    for tok in m.group(1).split():
        k, _, v = tok.partition("=")
        d[k] = v
    d["phases"] = [dict(t.split("=", 1) for t in mm.group(1).split())
                   for mm in re.finditer(r"AGENDAPHASE (.+)", out)]
    return d


def _f(d, k, dflt=0.0):
    try:
        return float(d.get(k, dflt))
    except (TypeError, ValueError):
        return dflt


def verdict(d, man):
    """Did a named resident walk to work. In L1's own terms.

    SEVEN CLAIMS, and no single number carries them:

      home       they were at home, standing still, before they set off
      left       they set off when their own schedule says they do
      arrived    they reached their post, not merely the end of the route
      stayed     and were still there after the shift started
      floor      the distance was covered ON THE FLOOR
      air        and essentially none of it falling
      tracked    the body kept up with the agenda rather than being placed by it
    """
    if "error" in d:
        return False, d["error"] + ("\n" + d.get("tail", "")
                                    if d.get("tail") else "")
    if d.get("home_before") != "true":
        return False, (f"was {_f(d, 'home_start_m'):.2f} m from their quarters "
                       f"at {man['clock']['start_h'] % 24.0:05.2f}, or moved "
                       f"{_f(d, 'pre_floor_m'):.2f} m before setting off")
    if d.get("left") != "true":
        return False, (f"never left: {_f(d, 'floor_m'):.2f} m covered in the "
                       f"whole run")
    if d.get("arrived") != "true":
        return False, (f"stopped {_f(d, 'arrive_m'):.2f} m from "
                       f"{man['who']['job']} on leg {d.get('leg')} "
                       f"({d.get('leg_kind')}) -- {_f(d, 'floor_m'):,.1f} m on "
                       f"the floor, agenda was {_f(d, 'lag_m'):.1f} m ahead")
    if d.get("stayed") != "true":
        return False, (f"reached their post and did not stay -- "
                       f"{_f(d, 'post_end_m'):.2f} m from it at the end")
    off = int(str(d.get("offfloor", "1/0")).split("/")[0])
    if off > 0:
        return False, (f"left the floor for {off} of "
                       f"{str(d.get('offfloor', '?/?')).split('/')[1]} frames")
    if _f(d, "air_m", 1.0) > 0.05:
        return False, f"{d.get('air_m')} m of the commute was covered in the air"
    # THE SPAWN IS A CLAIM THAT A PERSON CAN STAND THERE. The settle frames are
    # excluded from `offfloor` because `walkable.room_target` sits 50 mm above
    # the shell; excluding them without checking the drop would hide the case
    # the exclusion was made for.
    if abs(_f(d, "settle_drop_m", 9.9)) > 0.10:
        return False, (f"dropped {_f(d, 'settle_drop_m') * 1000:.0f} mm from a "
                       f"spawn 50 mm above the shell -- the floor is not where "
                       f"the shell says it is")
    # AND THE BODY IS NOT THE AGENDA. If the worst lag is the whole route, the
    # body was never following anything.
    if _f(d, "lag_m", 1e9) > max(5.0, 6.0 * float(man["lookahead_m"])):
        return False, (f"the body fell {_f(d, 'lag_m'):.1f} m behind its own "
                       f"agenda -- it is not tracking the route")
    return True, ""


def _fmt(d):
    return (f"{_f(d, 'floor_m'):,.1f} m on the floor "
            f"({_f(d, 'air_m'):.2f} m in the air), offfloor "
            f"{d.get('offfloor')}, {_f(d, 'arrive_m'):.2f} m from the post, "
            f"worst lag {_f(d, 'lag_m'):.2f} m, {d.get('frames')} ticks, "
            f"the drawn body went {_f(d, 'crowd_m'):,.1f} m")


def check_script(godot, engine_root):
    """Does `life.gd` parse? Three seconds, before anything else."""
    p = subprocess.run([godot, "--headless", "--path", engine_root,
                        "--check-only", "--script", "res://scripts/life.gd"],
                       capture_output=True, text=True, timeout=180)
    out = p.stdout + p.stderr
    if p.returncode == 0 and "Parse Error" not in out:
        return None
    return "\n".join(l for l in out.splitlines()
                     if "ERROR" in l or "Parse Error" in l)


RATES = (1.0, 10.0, 60.0)


def gate(argv):
    schema, profile = it.load()
    godot = argv.godot or W.godot_binary()
    engine_root = argv.engine_root or os.path.join(ROOT, "godot")
    if godot is None:
        print("no double-precision Godot binary. run: bash tools/build_godot.sh")
        return 2
    why = check_script(godot, engine_root)
    if why:
        print("godot/scripts/life.gd does not parse:\n" + why)
        return 2

    cand = choose(argv.who)
    print_commuter(schema, profile, cand)
    rows = []

    # ONE BUILD FOR EVERY RATE, and that is a property rather than a saving.
    # Nothing in the manifest depends on the clock rate any more: the route, the
    # shell, the lookahead and the tick budget are all rate-independent, because
    # `life.gd` raises the physics tick rate with the clock instead of taking
    # bigger steps. Three runs off ONE manifest is what makes them comparable.
    man, path = build(schema, profile, cand, rate=RATES[0], quiet=False)

    for rate in ([argv.rate] if argv.rate else RATES):
        d = run(path, godot, engine_root, rate=rate, timeout=argv.timeout,
                verbose=argv.verbose)
        ok, note = verdict(d, man)
        print(f"\n  {'PASS' if ok else 'FAIL'}  x{rate:g} CLOCK   {_fmt(d)}")
        for ph in d.get("phases", ()):
            print(f"        {ph.get('phase', '?'):9s} "
                  f"{_f(ph, 'floor_m'):8,.1f} m on the floor in "
                  f"{ph.get('frames')} frames"
                  + (f"  ({ph.get('note')})" if ph.get("note") else ""))
        if not ok:
            print(f"        {note}")
        rows.append((f"x{rate:g} clock", ok, d))

    # The controls run at the fastest clock: what they test is a MECHANISM, and
    # a mechanism that is broken at x60 is broken at x1.
    # CONTROL 1 -- THE CLOCK IS STOPPED. Same scene, same body, same route; the
    # clock does not advance, so the agenda never reaches the departure hour.
    # A resident who leaves anyway is a resident walking on something other than
    # their own schedule.
    c1 = run(path, godot, engine_root, rate=0.0, timeout=argv.timeout,
             verbose=argv.verbose)
    c1ok = ("error" not in c1 and c1.get("left") != "true"
            and c1.get("arrived") != "true" and _f(c1, "floor_m", 1e9) < 0.5)
    print(f"\n  {'FIRED' if c1ok else 'DID NOT FIRE'}  control: the clock "
          f"stopped -- they never leave")
    _say(c1, man)
    rows.append(("control: the clock stopped", c1ok, c1))

    # CONTROL 2 -- THE ROUTE IS UNAVAILABLE. Every pressure door on the deck
    # stays SOLID -- `deck.build_collision`'s own `doorpanel_*` spans, left
    # switched on. The resident is physically shut inside their quarters while
    # the AGENDA walks the whole route. If the runtime placed people from the
    # agenda they would arrive through a locked door; the body is the reason
    # they do not.
    c2 = run(path, godot, engine_root, doors="sealed", rate=RATES[-1],
             timeout=argv.timeout, verbose=argv.verbose)
    c2ok = ("error" not in c2 and c2.get("arrived") != "true"
            and _f(c2, "air_m", 1e9) < 0.5
            and _f(c2, "lag_m", 0.0) > 100.0)
    print(f"\n  {'FIRED' if c2ok else 'DID NOT FIRE'}  control: every pressure "
          f"door sealed -- the route is unavailable and they do not teleport")
    _say(c2, man)
    rows.append(("control: the route unavailable", c2ok, c2))

    # CONTROL 3 -- THE PRE-FIX BUILD. `--agenda=off` is `life.gd` as it was
    # before this session: the Director shows and hides baked bodies by the hour
    # and nothing walks anywhere. The commuter is placed where they were baked
    # and never steered.
    c3 = run(path, godot, engine_root, agenda="off", rate=RATES[-1],
             timeout=argv.timeout, verbose=argv.verbose)
    c3ok = ("error" not in c3 and c3.get("left") != "true"
            and c3.get("arrived") != "true" and _f(c3, "floor_m", 1e9) < 0.5)
    print(f"\n  {'FIRED' if c3ok else 'DID NOT FIRE'}  control: the pre-fix "
          f"build (--agenda=off) -- nobody moves at all")
    _say(c3, man)
    rows.append(("control: the pre-fix build", c3ok, c3))

    bad = [n for n, o, _ in rows if not o]
    print("\n" + ("ALL GREEN" if not bad else "FAILED: " + "; ".join(bad)))
    return 0 if not bad else 1


# ---------------------------------------------------------------------------
# THE L3 GATE
# ---------------------------------------------------------------------------

def verdict3(d, man):
    """Did a named resident ride the lift to work. In L3's own terms.

    L1's seven claims, and four more that are about the vehicle:

      boarded   they were inside the car when its doors shut
      carried   the RADIUS they covered is the shaft's rise, ON THE FLOOR
      alighted  they got out at the far landing's own walking radius
      on deck   and the landing they ended at is their post's landing
    """
    ok, note = verdict(d, man)
    if not ok:
        return ok, note
    if d.get("boarded") != "true":
        return False, ("the doors shut and they were not in the car -- "
                       f"lag {_f(d, 'lag_m'):.1f} m")
    rise = float(man["segments"][1]["rise_m"])
    got = _f(d, "ride_radial_floor_m")
    if abs(got - rise) > RIDE_TOL_M:
        return False, (f"covered {got:.3f} m of radius on the floor during the "
                       f"ride, against a {rise:.3f} m shaft")
    if _f(d, "ride_radial_air_m", 1e9) > RIDE_TOL_M:
        return False, (f"{_f(d, 'ride_radial_air_m'):.3f} m of the ride's "
                       f"radius was covered in the air -- that is falling")
    off = int(str(d.get("ride_offfloor", "1/0")).split("/")[0])
    if off > 0:
        return False, (f"left the floor for {off} frames DURING THE RIDE -- "
                       f"the car moved and the body did not go with it")
    if _f(d, "standoff_max_mm", 1e9) > 1000.0 * RIDE_TOL_M:
        return False, (f"stood {_f(d, 'standoff_max_mm'):.1f} mm off the car "
                       f"floor at worst -- it is not riding, it is bouncing")
    if d.get("alighted") != "true":
        return False, "they never got out of the car at the far landing"
    if int(d.get("end_landing", -1)) != int(man["lift"]["to_landing"]):
        return False, (f"ended at landing {d.get('end_landing')} "
                       f"(deck {d.get('end_deck')}), not their post's landing "
                       f"{man['lift']['to_landing']}")
    return True, ""


# How far the ride's radius may miss the shaft's own rise. `transit_runtime`'s
# own figure and its reason: the body starts and ends 50 mm above two floors and
# both are measured from the floor, so the error cannot exceed the stand-off.
RIDE_TOL_M = TR.RIDE_TOL_M


def _fmt3(d):
    return (f"{_f(d, 'floor_m'):,.1f} m on the floor "
            f"({_f(d, 'air_m'):.2f} m in the air), offfloor "
            f"{d.get('offfloor')}, rode {_f(d, 'ride_radial_floor_m'):.2f} m "
            f"of radius (offfloor {d.get('ride_offfloor')}), got off at deck "
            f"{d.get('end_deck')}, {_f(d, 'arrive_m'):.2f} m from the post, "
            f"worst lag {_f(d, 'lag_m'):.2f} m, {d.get('frames')} ticks")


def _say3(d, man):
    if "error" in d:
        print(f"        {d['error']}\n{d.get('tail', '')}")
        return
    print(f"        {_f(d, 'floor_m'):,.2f} m on the floor, boarded="
          f"{d.get('boarded')}, alighted={d.get('alighted')}, rode "
          f"{_f(d, 'ride_radial_floor_m'):.2f} m of radius "
          f"({_f(d, 'ride_radial_air_m'):.2f} m of it in the air), ended at "
          f"deck {d.get('end_deck')} r={_f(d, 'end_r'):.1f}, "
          f"{_f(d, 'arrive_m'):,.1f} m from {man['who']['job']}, "
          f"the car moved {_f(d, 'car_moved_m'):.1f} m "
          f"(arrived={d.get('arrived')}, offfloor {d.get('offfloor')})")


def gate3(argv):
    """THE L3 GATE: a resident rides the lift to work, at three clock rates,
    with the three controls the milestone requires."""
    schema, profile = it.load()
    godot = argv.godot or W.godot_binary()
    engine_root = argv.engine_root or os.path.join(ROOT, "godot")
    if godot is None:
        print("no double-precision Godot binary. run: bash tools/build_godot.sh")
        return 2
    why = check_script(godot, engine_root)
    if why:
        print("godot/scripts/life.gd does not parse:\n" + why)
        return 2
    for script in ("transit.gd",):
        p = subprocess.run([godot, "--headless", "--path", engine_root,
                            "--check-only", "--script", f"res://scripts/{script}"],
                           capture_output=True, text=True, timeout=180)
        if p.returncode != 0 or "Parse Error" in p.stdout + p.stderr:
            print(f"godot/scripts/{script} does not parse")
            return 2

    cand = choose3(schema, profile, argv.who)
    man, path = build3(schema, profile, cand, rate=RATES[0], quiet=False)
    print_commute(man)
    rows = []

    for rate in ([argv.rate] if argv.rate else RATES):
        d = run(path, godot, engine_root, rate=rate, timeout=argv.timeout,
                verbose=argv.verbose)
        ok, note = verdict3(d, man)
        print(f"\n  {'PASS' if ok else 'FAIL'}  x{rate:g} CLOCK   {_fmt3(d)}")
        for ph in d.get("phases", ()):
            print(f"        {ph.get('phase', '9s'):9s} "
                  f"{_f(ph, 'floor_m'):8,.1f} m on the floor in "
                  f"{ph.get('frames')} frames")
        if not ok:
            print(f"        {note}")
        rows.append((f"x{rate:g} clock", ok, d))

    # THE CONTROLS RUN AT THE FASTEST CLOCK: what they test is a MECHANISM, and
    # a mechanism that is broken at x60 is broken at x1.
    #
    # CONTROL 1 -- THE CAR IS PARKED SOMEWHERE ELSE AND NEVER CALLED. The
    # timetable for the RESIDENT is unchanged and still completes; the car stays
    # at its parking landing and its doors never open. This is L1's second
    # control one vehicle along: the agenda finishes the journey and the person
    # does not.
    c1 = run(path, godot, engine_root, lift="parked", rate=RATES[-1],
             timeout=argv.timeout, verbose=argv.verbose)
    c1ok = ("error" not in c1 and c1.get("boarded") != "true"
            and c1.get("arrived") != "true"
            and _f(c1, "ride_radial_floor_m", 1e9) < RIDE_TOL_M)
    print(f"\n  {'FIRED' if c1ok else 'DID NOT FIRE'}  control: the car is "
          f"parked at landing {man['lift']['park_landing']} and never called")
    _say3(c1, man)
    rows.append(("control: the car never comes", c1ok, c1))

    # CONTROL 2 -- EVERY LANDING APERTURE SEALED. `lift.lift_collision(
    # landings=False)` is the generator's own negative control: the shaft with
    # no way in or out of it. The car runs its timetable to the second and the
    # resident is standing in the lobby with a wall where the door was.
    c2 = run(path, godot, engine_root, landings="sealed", rate=RATES[-1],
             timeout=argv.timeout, verbose=argv.verbose)
    c2ok = ("error" not in c2 and c2.get("boarded") != "true"
            and c2.get("arrived") != "true")
    print(f"\n  {'FIRED' if c2ok else 'DID NOT FIRE'}  control: every landing "
          f"aperture sealed -- they are stopped at the door")
    _say3(c2, man)
    rows.append(("control: the landings sealed", c2ok, c2))

    # CONTROL 3 -- THE PRE-FIX BUILD. Before this session `life.gd` had no
    # vehicle in it at all: `--lift=off` loads the shaft and no car, which is
    # exactly the station this milestone started on. Nobody rides.
    c3 = run(path, godot, engine_root, lift="off", rate=RATES[-1],
             timeout=argv.timeout, verbose=argv.verbose)
    c3ok = ("error" not in c3 and c3.get("boarded") != "true"
            and c3.get("arrived") != "true"
            and _f(c3, "ride_radial_floor_m", 1e9) < RIDE_TOL_M)
    print(f"\n  {'FIRED' if c3ok else 'DID NOT FIRE'}  control: the pre-fix "
          f"build (--lift=off) -- there is no car in the shaft, nobody rides")
    _say3(c3, man)
    rows.append(("control: the pre-fix build", c3ok, c3))

    bad = [n for n, o, _ in rows if not o]
    print("\n" + ("ALL GREEN" if not bad else "FAILED: " + "; ".join(bad)))
    return 0 if not bad else 1


def print_commute(man):
    """Who commutes, by what legs, on whose numbers."""
    w = man["who"]
    m = man["marks"]
    c = man["costing"]
    lf = man["lift"]
    print(f"\nSOMEONE TAKES THE LIFT TO WORK\n")
    print(f"  {w['name']}, {w['age']}, {w['species']} from {w['origin']} -- "
          f"{w['role']}")
    print(f"     lives   {w['home']:22s} {man['deck_from']:12s} "
          f"landing {lf['from_landing']}")
    print(f"     works   {w['job']:22s} {man['deck_to']:12s} "
          f"landing {lf['to_landing']}")
    print(f"     shift   {man['shift']['start_h']:05.2f} EMT for "
          f"{man['shift']['hours']:.0f} h (npc/schedule.work_window)")
    print(f"     leaves  {man['shift']['depart_h']:05.2f} EMT -- the start of "
          f"their own {man['shift']['transit_h']:.1f} h TRANSIT window")
    print(f"     id      {w['id']}   -- affiliate {w['pool_i']} of "
          f"{w['pool']}")
    print(f"\n  THE JOURNEY, and every leg is somebody else's geometry")
    for s in man["segments"]:
        if s["kind"] == "ride":
            print(f"     ride   {s['rise_m']:8,.1f} m  of RADIUS, landing "
                  f"{s['from_landing']} -> {s['to_landing']}, in "
                  f"{m['ride_s']:.1f} s "
                  f"(navigation.lift_ride_s, peak at the Coriolis cap)")
            continue
        for l in s["legs"]:
            print(f"     {l['kind']:6s} {l['length_m']:8,.1f} m  "
                  f"{l['note'][:78]}")
    print(f"     {'total':6s} {man['segments'][0]['length_m'] + man['segments'][2]['length_m']:8,.1f} m "
          f"of walking plus a {man['segments'][1]['rise_m']:.1f} m ride")
    print(f"\n  THE TIMETABLE, in station seconds from the clock's own start")
    for k in ("depart", "landing", "car_here", "doors_open", "aboard",
              "doors_shut", "alight", "arrive"):
        print(f"     {k:12s} {m[k]:8,.1f} s")
    print(f"     the car is parked at landing {lf['park_landing']} and takes "
          f"{m['call_s']:.1f} s to answer the call; the doors take "
          f"{m['door_s']:.2f} s (door.gd's own speed on the leaves' measured "
          f"travel) and it dwells {m['dwell_s']:.0f} s "
          f"(navigation.TRANSIT_DWELL_S)")
    print(f"\n  AGAINST station/transit.py's OWN COSTING")
    print(f"     the ride    ours {m['ride_s']:.3f} s against climb_leg's "
          f"{c['climb_s']:.3f} s -- {c['ride_delta_s']:+.3f} s "
          f"({c['climb_detail']})")
    print(f"     the walk    ours {m['walk_a_s'] + m['walk_b_s']:,.0f} s over "
          f"{man['segments'][0]['length_m'] + man['segments'][2]['length_m']:,.0f} m of real corridor, "
          f"walk_leg's {c['walk_s']:,.0f} s over {c['walk_m']:,.0f} m "
          f"({c['walk_detail']})")
    print(f"     the whole   ours {c['ours_s']:,.0f} s against "
          f"{c['journey_s']:,.0f} s -- {c['delta_s']:+,.0f} s, of which "
          f"{m['wait_s']:.0f} s is waiting for a car transit.py never waits "
          f"for")


# ---------------------------------------------------------------------------
# THE CENSUS -- how many of the station's own residents can now do this
# ---------------------------------------------------------------------------

def baked_residents():
    """Every resident in the shipped `<deck>_actors.json` with a home and a job.

    THE STATION'S OWN CAST, not a pool this file scanned. These are the people
    `tools/bake_station.py` actually put in the rooms, so "how many can commute"
    is a question about the station that is on disk.
    """
    out, rows = {}, 0
    for key in sorted(assembled()):
        path = os.path.join(STATION, key + "_actors.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for a in json.load(f):
                who = a.get("who") or {}
                if who.get("home") and who.get("job") and who.get("id"):
                    out[who["id"]] = who
                    rows += 1
    return out, rows


def census(schema=None, profile=None):
    """How many of the baked residents can complete their commute, and why not.

    THE NUMBER L3 IS SCORED ON, and it is well short of all of them. Each
    failure is reported by its own reason rather than as a total, because the
    reasons are different pieces of work: a pair on two rings needs the SPOKE,
    a pair in two sectors needs the TRUNK, and a pair whose deck has no landing
    on its column is a fact about `interior.decks_in_ring` at that z.
    """
    if schema is None:
        schema, profile = it.load()
    by_place, _bad = endpoint_index(schema, profile)
    nodes, _es = graph()
    shafts = {}
    who, rows = baked_residents()
    reasons = {}
    can = []
    for wid, w in sorted(who.items()):
        sec = (DIR.by_key(w["home"]) or {}).get("sector")
        if sec and sec not in shafts:
            shafts[sec] = RW.shaft(schema, profile, nodes, sec)
        ok, why = commutable(w["home"], w["job"], by_place, shafts.get(sec))
        if ok:
            can.append(w)
            continue
        # A reason a reader can act on, rather than the raw sentence.
        if "same deck" in why:
            k = "home and post on ONE deck -- L1 already walks it"
        elif "trunk" in why:
            k = "different sectors -- needs the trunk between columns (no gate)"
        elif "spoke" in why:
            k = "different rings -- needs the spoke between columns (no gate)"
        elif "no landing" in why:
            k = "a deck with no landing on its own column"
        elif "apart" in why:
            k = "the landing and the deck's corridor are at different radii"
        elif "moves" in why:
            k = "reaching the spine moves that cluster's room doors"
        elif "landing lobby" in why:
            k = ("a cluster inside the column's own lobby, whose walls seal "
                 "its ring corridor")
        elif "never built" in why:
            k = "the deck was never exported"
        elif "not a located place" in why or "not on a cluster" in why:
            k = "an end that is not on a route-capable cluster"
        else:
            k = why
        reasons[k] = reasons.get(k, 0) + 1
    print(f"\nHOW MANY OF THE STATION'S RESIDENTS CAN COMMUTE\n")
    print(f"  {rows:,} baked bodies carry a home and a job, and they are "
          f"{len(who)} DISTINCT PEOPLE -- the same resident is baked into more "
          f"than one room.")
    print(f"  {len(can)} of them can complete it with what exists today -- "
          f"{100.0 * len(can) / max(1, len(who)):.1f}%\n")
    for k, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"     {n:5d}  {k}")
    routes_ = {}
    for w in can:
        routes_[(w["home"], w["job"])] = routes_.get((w["home"], w["job"]), 0) + 1
    if routes_:
        print(f"\n  and the commutes they make, which are all one column:")
        for (h, j), n in sorted(routes_.items(), key=lambda x: -x[1]):
            print(f"     {n:5d}  {h:22s} -> {j:22s} "
                  f"{deck_key(h)} -> {deck_key(j)}")
    return can, reasons


def _selftest3():
    """Everything about the ride that can be checked without an engine."""
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (f"  {note}" if note else ""))

    schema, profile = it.load()
    print("\nL3 -- EVERY PIECE OF THE RIDE THAT CAN BE CHECKED OFFLINE\n")
    cand = choose3(schema, profile)
    res = cand["res"]
    j = journey_for(schema, profile, cand)
    check("a NAMED resident commutes between two decks of one column",
          bool(res.name) and deck_key(res.home) != deck_key(res.job),
          f"{res.name}, {res.species} {res.role}, {res.home} "
          f"({deck_key(res.home)}) -> {res.job} ({deck_key(res.job)})")
    ids = RS.affiliates(cand["pool"], res.species, "b5")
    check("and they are in the pool populace casts that room from",
          res.npc_id in ids,
          f"affiliate {cand['i']} of {cand['pool']}, {len(ids)} in the pool")

    nodes, es = graph()
    at = {}
    for k, n in nodes.items():
        for pk in n["places"]:
            at[pk] = k
    legs = RW.path_between(nodes, es, at[res.home], at[res.job])
    kinds = [l["kind"] for l in (legs or ())]
    check("routes.py joins their quarters to their post THROUGH THE LIFT",
          legs is not None and "lift" in kinds, " -> ".join(kinds))

    # THE RIDE'S SECONDS ARE TWO MODULES' AND THEY AGREE. `navigation` and
    # `transit` share no code; the table this runtime plays is asserted against
    # the cap before it is written and against `climb_leg` here.
    rise = abs(j["g"]["landings"][j["landing_a"]]["walk_r_m"]
               - j["g"]["landings"][j["landing_b"]]["walk_r_m"])
    nav_s = NAV.lift_ride_s(schema, rise)
    climb = T.climb_leg(schema, rise, "the lift")["seconds"]
    check("the ride's duration is navigation's and transit's alike",
          abs(nav_s - climb) < 1e-6,
          f"{nav_s:.4f} s against {climb:.4f} s over {rise:.2f} m")

    # THE CAR'S STAND POINT MOVES WITH THE CAR, and the runtime computes it that
    # way. Evaluated at the far landing's height it must be that landing's own
    # stand point -- otherwise the passenger is steered at a point in the wall.
    ax = j["g"]["landings"]
    axis = L._basis(j["g"]["angle_deg"])[1]
    dy = ax[j["landing_b"]]["y_m"] - ax[j["landing_a"]]["y_m"]
    moved = [j["car_a"][k] + axis[k] * dy for k in range(3)]
    check("the car's stand point carried to the far landing IS that landing's",
          math.dist(moved, j["car_b"]) < 1e-6,
          f"{math.dist(moved, j['car_b']) * 1000:.3f} mm apart")

    # THE ROUTE IS MONOTONE and every ring waypoint is inside its own corridor.
    # Both are asserted inside `journey_for`; this says so out loud.
    check("the route never passes within a capsule of itself",
          True, f"{len(j['seg0'])} + {len(j['seg2'])} waypoints, "
                f"{j['len0']:.1f} m + {j['len2']:.1f} m")

    # THE CROSSING DOORWAY IS THE ONLY THING ADDED TO THE COLUMN, and with no
    # crossing this function is route_walk's own shell triangle for triangle.
    v0, t0, _g0 = column_collision(schema, profile, j["g"])
    rv, rt, _rg = RW.column_collision(schema, profile, j["g"])
    check("CONTROL: with no crossing, the column shell is route_walk's",
          len(t0) == len(rt) and t0 == rt and v0 == rv,
          f"{len(t0):,} triangles against {len(rt):,}")
    v1, t1, _g1 = column_collision(schema, profile, j["g"],
                                   crossings=j["crossings"])
    check("and cutting the crossing changes it",
          (len(j["crossings"]) == 0) or len(t1) != len(t0),
          f"{len(j['crossings'])} crossing(s): {len(t0):,} -> {len(t1):,} "
          f"triangles")

    # THE SEALED CONTROL REALLY IS SEALED -- the generator's own switch.
    v2, t2, _g2 = column_collision(schema, profile, j["g"],
                                   crossings=j["crossings"], landings=False)
    check("CONTROL: sealing the landings changes the shell",
          len(t2) != len(t1), f"{len(t1):,} -> {len(t2):,} triangles")

    # THE TIMETABLE FITS THE SCHEDULE'S OWN TRANSIT WINDOW.
    keep = TR.OUT
    TR.OUT = OUT
    try:
        import contextlib                                         # noqa: PLC0415
        import io                                                 # noqa: PLC0415
        with contextlib.redirect_stdout(io.StringIO()):
            lift_man = TR.build_lift(schema, profile, j["g"], quiet=True)
    finally:
        TR.OUT = keep
    g_ms2 = P.place_gravity(res.home)
    speed = P._walk_speed(res.species, CROWD_LOD, g_ms2)
    plan, marks = timetable(j, lift_man, speed, PRE_S)
    check("the whole journey fits the schedule's own transit window",
          marks["journey_s"] < SC.TRANSIT_H * 3600.0,
          f"{marks['journey_s']:,.0f} s against "
          f"{SC.TRANSIT_H * 3600:.0f} s allowed")
    check("the car is called from a landing that is neither end",
          j["park"] not in (j["landing_a"], j["landing_b"]),
          f"parked at {j['park']}, {marks['call_s']:.1f} s away")
    # AND THE PLAN IS ORDERED. A timetable whose rows overlap is a body in two
    # places, and the runtime would play whichever came last.
    seq = [marks[k] for k in ("depart", "landing", "car_here", "doors_open",
                              "aboard", "doors_shut", "alight", "arrive")]
    check("the timetable's instants are in order",
          all(a <= b + 1e-9 for a, b in zip(seq, seq[1:])),
          " -> ".join(f"{x:.0f}" for x in seq))
    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def _say(d, man):
    if "error" in d:
        print(f"        {d['error']}\n{d.get('tail', '')}")
        return
    print(f"        {_f(d, 'floor_m'):,.2f} m on the floor, "
          f"{_f(d, 'arrive_m'):,.1f} m from {man['who']['job']} at the end, "
          f"the agenda got {_f(d, 'agenda_s_m'):,.1f} m of "
          f"{man['route']['length_m']:,.0f} along the route "
          f"(left={d.get('left')}, arrived={d.get('arrived')}, "
          f"offfloor {d.get('offfloor')})")


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def print_commuter(schema, profile, cand):
    res = cand["res"]
    r = route_for(schema, profile, cand)
    g = P.place_gravity(res.home)
    v = P._walk_speed(res.species, CROWD_LOD, g)
    walk_s = r["length_m"] / v
    nodes = RT.clusters()
    es = RT.edges(nodes, schema, profile=profile)
    legs, note = graph_path(nodes, es, res.home, res.job)
    comps = RT.components(nodes, es, True)
    every = RT.all_nodes(nodes, es)
    one = None
    for _root, ks in comps.items():
        pk = {p for k in ks for p in every[k].get("places", ())}
        if res.home in pk and res.job in pk:
            one = len(ks)
    print(f"\nSOMEONE GOES TO WORK\n")
    print(f"  {res.name}, {res.age}, {res.species} from {res.origin} -- "
          f"{res.role}")
    print(f"     lives   {res.home:24s} {cand['deck'].replace('_', '/')} "
          f"at {r['door_home']:.0f} deg")
    print(f"     works   {res.job:24s} {cand['deck'].replace('_', '/')} "
          f"at {r['door_job']:.0f} deg")
    print(f"     shift   {cand['start_h']:05.2f} EMT for {cand['hours']:.0f} h "
          f"(npc/schedule.work_window)")
    print(f"     leaves  {cand['depart_h']:05.2f} EMT -- the start of their own "
          f"{SC.TRANSIT_H:.1f} h TRANSIT window (npc/schedule.activity_at)")
    print(f"     id      {res.npc_id}   -- affiliate {cand['i']} of "
          f"{cand['pool']}")
    print(f"\n  THE ROUTE, out of station/routes.py")
    print(f"     {note}")
    if one is not None:
        print(f"     both places are in one foot-connected component of "
              f"{one} cluster(s)")
    for l in r["legs"]:
        print(f"     {l['kind']:6s} {l['length_m']:8,.1f} m  {l['note']}")
    print(f"     {'total':6s} {r['length_m']:8,.1f} m over "
          f"{len(r['points'])} waypoints")
    print(f"\n  THE COMMUTE")
    print(f"     gait    {v:.3f} m/s at {g:.3f} m/s2 -- populace._walk_speed, "
          f"the clip the body is ANIMATED at "
          f"(navigation.walk_speed says "
          f"{NAV.walk_speed(g / 9.80665, res.species):.3f})")
    print(f"     takes   {walk_s:,.0f} s = {walk_s / 60.0:.1f} min, inside the "
          f"schedule's own {SC.TRANSIT_H * 60:.0f} min transit window with "
          f"{(SC.TRANSIT_H * 3600 - walk_s) / 60:.1f} min to spare")
    print(f"     arrives {(cand['depart_h'] + walk_s / 3600.0) % 24.0:05.2f} "
          f"EMT, {(cand['start_h'] - cand['depart_h'] - walk_s / 3600.0) * 60:.0f}"
          f" min before the shift starts")


def report():
    schema, profile = it.load()
    cs = candidates()
    print(f"\nWHO CAN WALK TO WORK, and it is a short list\n")
    print(f"  {len(cs)} residents on an assembled deck have their quarters and "
          f"their post on that SAME deck, with a name and a clean transit "
          f"window:")
    for c in cs:
        r = c["res"]
        print(f"     {r.name:22s} {r.species:9s} {r.role:10s} "
              f"{c['deck']:10s} {r.home:22s} -> {r.job:22s} "
              f"shift {c['start_h']:05.2f}")
    if cs:
        print_commuter(schema, profile, choose())
    return cs


def primitives():
    """The baked-vs-instanced cost, off the shipped .glbs.

    THE QUESTION THE ARCHITECTURE DECISION TURNS ON, measured rather than
    argued. `budget._glb_primitives` parses the glTF JSON chunk directly,
    because a count derived from the generator is a second copy of a number and
    this gate exists because the two disagreed by a factor of thirty.
    """
    import budget as B                                            # noqa: PLC0415
    print(f"\nWHAT A PERSON COSTS A DECK, in primitives\n")
    print(f"  budget.BUDGETS['deck_primitives'] = {B.BUDGETS['deck_primitives']}\n")
    print(f"  {'deck':12s} {'prims':>7s} {'people':>7s} {'baked':>7s} "
          f"{'crowd':>7s} {'per baked':>10s} {'per walker':>11s}")
    rows = []
    for key in sorted(assembled()):
        glb = os.path.join(STATION, key + ".glb")
        act = os.path.join(STATION, key + "_actors.json")
        crw = os.path.join(STATION, key + "_crowd.json")
        if not (os.path.exists(glb) and os.path.exists(act)):
            continue
        try:
            prims, npc = B._glb_primitives(glb)
        except Exception:                                         # noqa: BLE001
            continue
        with open(act) as f:
            n_act = len(json.load(f))
        n_crw = 0
        if os.path.exists(crw):
            with open(crw) as f:
                n_crw = len(json.load(f))
        rows.append((key, prims, npc, n_act, n_crw))
    rows.sort(key=lambda r: -r[1])
    tot = [0, 0, 0, 0]
    for key, prims, npc, n_act, n_crw in rows[:10]:
        per = npc / n_act if n_act else 0.0
        print(f"  {key:12s} {prims:7,d} {npc:7,d} {n_act:7,d} {n_crw:7,d} "
              f"{per:10.2f} {0.0:11.2f}")
    for _k, prims, npc, a, c in rows:
        tot[0] += prims
        tot[1] += npc
        tot[2] += a
        tot[3] += c
    print(f"\n  {len(rows)} decks: {tot[0]:,} primitives, {tot[1]:,} of them "
          f"people, from {tot[2]:,} baked actors and {tot[3]:,} instanced "
          f"walkers")
    if tot[2]:
        print(f"  a baked actor costs {tot[1] / tot[2]:.2f} primitives; an "
              f"instanced walker costs 0 -- their bodies are in "
              f"crowd_lod*.glb and every walker of one (species, lod, phase) "
              f"shares one MultiMesh")
    over = [r for r in rows if r[1] > B.BUDGETS["deck_primitives"]]
    print(f"  {len(over)} of {len(rows)} shipped decks are ALREADY over the "
          f"600 bound, worst {rows[0][0]} at {rows[0][1]:,} "
          f"({rows[0][2]:,} people)")
    return rows


# ---------------------------------------------------------------------------
# SELF-TEST -- everything answerable without an engine
# ---------------------------------------------------------------------------

def _selftest():
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name + (f"  {note}" if note
                                                           else ""))

    schema, profile = it.load()
    print("\nL1 -- EVERY PIECE OF THE COMMUTE THAT CAN BE CHECKED OFFLINE\n")

    cand = choose()
    res = cand["res"]
    check("a NAMED resident commutes on one assembled deck",
          bool(res.name) and res.job and res.home != res.job,
          f"{res.name}, {res.species} {res.role}, {res.home} -> {res.job} "
          f"on {cand['deck']}")

    # THE PERSON IS THE POOL'S, NOT A PROBE. `populace` casts a room from
    # `resident.affiliates`, which scans `pool_id` in order; if this id is not
    # in that stream the gate is walking somebody the station does not contain.
    ids = RS.affiliates(cand["pool"], res.species, "b5")
    check("and they are in the pool populace casts that room from",
          res.npc_id in ids,
          f"affiliate {cand['i']} of {cand['pool']}, {len(ids)} in the pool")

    # THE SCHEDULE SAYS THEY COMMUTE, and it is asked rather than assumed.
    A = SC.Activity
    d, s = cand["depart_h"], cand["start_h"]
    check("their own schedule puts them in TRANSIT before the shift and at "
          "WORK on it",
          SC.activity_at(res.npc_id, res.species, (d + 0.25) % 24.0) is A.TRANSIT
          and SC.activity_at(res.npc_id, res.species, s) is A.WORK,
          f"leaves {d:05.2f}, works {s:05.2f} for {cand['hours']:.0f} h")
    check("and where_at sends them to their post once the shift starts",
          RS.where_at(res, s) == res.job and RS.where_at(res, (s - 0.6) % 24.0)
          != res.job,
          f"{RS.where_at(res, (s - 0.6) % 24.0)} -> {RS.where_at(res, s)}")

    # THE GRAPH SAYS THE TWO PLACES ARE JOINED.
    nodes = RT.clusters()
    es = RT.edges(nodes, schema, profile=profile)
    legs, note = graph_path(nodes, es, res.home, res.job)
    check("routes.py joins their quarters to their post", legs is not None,
          note)

    r = route_for(schema, profile, cand)
    m = r["meta"]
    check("the route is laid on the corridor the generator built",
          abs(r["length_m"]) > 1.0
          and all(abs(math.hypot(p[0], p[1]) - m["floor_r_m"]) < 1e-6
                  for p in r["legs"][1]["points"]),
          f"{r['length_m']:,.1f} m, ring arc at r={m['floor_r_m']:.3f} m")

    # A BODY STEERED WAYPOINT TO WAYPOINT STAYS INSIDE THE CORRIDOR. The chord
    # between two waypoints has to sit inside the corridor's own half width or
    # the route is a route through a wall. `route_walk` makes the same check for
    # the same reason and this is that check on this arc.
    worst = 0.0
    for p0, p1 in zip(r["legs"][1]["points"], r["legs"][1]["points"][1:]):
        mid = [(p0[k] + p1[k]) / 2.0 for k in range(3)]
        worst = max(worst, m["floor_r_m"] - math.hypot(mid[0], mid[1]))
    check("a body steered waypoint to waypoint stays inside the corridor",
          worst < m["half_w_m"] - CAPSULE_R_M,
          f"worst chord sags {worst * 1000:.0f} mm against a "
          f"{m['half_w_m']:.2f} m half width less a {CAPSULE_R_M} m capsule")

    # THE COMMUTE FITS THE SCHEDULE'S OWN TRANSIT WINDOW.
    g = P.place_gravity(res.home)
    v = P._walk_speed(res.species, CROWD_LOD, g)
    walk_s = r["length_m"] / v
    check("the walk fits inside the schedule's own transit window",
          walk_s < SC.TRANSIT_H * 3600.0,
          f"{walk_s:,.0f} s of walking at {v:.3f} m/s against "
          f"{SC.TRANSIT_H * 3600:.0f} s allowed")

    # NEGATIVE CONTROL ON THE GAIT: at zero gravity there is no walking, and the
    # same arithmetic must refuse rather than return a plausible number.
    check("CONTROL: the gait model refuses zero gravity rather than guessing",
          NAV.walk_speed(0.0, res.species) == 0.0
          and math.isinf(NAV.walk_time_s(100.0, 0.0, 0.0, res.species)),
          "walk_speed(0) = 0, walk_time_s = inf")

    # THE SHELL IS THE SHIPPED ONE.
    want = assembled()[cand["deck"]]["collision_tris"]
    check("the collision shell is triangle-for-triangle the one that shipped",
          len(r["tris"]) == want,
          f"{len(r['tris']):,} triangles, {cand['deck']}_collision.glb "
          f"shipped {want:,}")

    # AND THE SHIPPED ONE CANNOT OPEN A DOOR. This is the finding, asserted so
    # it cannot be quietly forgotten: `export_station` writes ONE group, so the
    # `doorpanel_*` spans `build_collision` emitted are unaddressable and every
    # room on the shipped collision is sealed.
    panels = [nm for mm in r["all_meta"]["clusters"]
              for nm, _a, _b in mm.get("groups", ())
              if nm.startswith("doorpanel_")]
    shipped = os.path.join(STATION, cand["deck"] + "_collision.glb")
    named = _glb_mesh_names(shipped) if os.path.exists(shipped) else []
    check("build_collision emits a switchable panel per pressure door",
          len(panels) >= 2, f"{len(panels)}: {panels}")
    check("CONTROL: and the SHIPPED collision has none of them -- every room "
          "on disk is sealed",
          not any(n.startswith("doorpanel_") for n in named),
          f"{len(named)} mesh(es) in {os.path.basename(shipped)}: "
          f"{named[:3]}")

    # THE COST DECISION, ASSERTED. A commuter is an instanced walker; the claim
    # that this costs no deck primitives is checkable against the shipped files.
    import budget as B                                            # noqa: PLC0415
    rows = [r2 for r2 in
            ((k, os.path.join(STATION, k + ".glb")) for k in assembled())
            if os.path.exists(r2[1])]
    worst_k, worst_n, worst_npc = None, 0, 0
    for k, glb in rows:
        try:
            n, npc = B._glb_primitives(glb)
        except Exception:                                         # noqa: BLE001
            continue
        if n > worst_n:
            worst_k, worst_n, worst_npc = k, n, npc
    check("a baked cast is what puts a deck over the primitive budget, and the "
          "instanced crowd is not",
          worst_n > B.BUDGETS["deck_primitives"] and worst_npc > worst_n * 0.5,
          f"{worst_k} ships {worst_n:,} primitives, {worst_npc:,} of them "
          f"people, against a bound of {B.BUDGETS['deck_primitives']}")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def _glb_mesh_names(path):
    """Every mesh name in a .glb. Read off the artefact, like `_glb_primitives`."""
    import struct                                                 # noqa: PLC0415
    with open(path, "rb") as f:
        data = f.read()
    _magic, _ver, total = struct.unpack("<III", data[:12])
    off = 12
    while off < total:
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        if ctype == 0x4E4F534A:
            doc = json.loads(data[off + 8:off + 8 + clen])
            return [m.get("name", "") for m in doc.get("meshes", ())]
        off += 8 + clen
    return []


def main(argv=None):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--primitives", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--walk", action="store_true",
                    help="L1's GATE: three clock rates and three controls")
    ap.add_argument("--commute", action="store_true",
                    help="L3's GATE: they ride the lift, three rates, three "
                         "controls")
    ap.add_argument("--report3", action="store_true",
                    help="who can ride to work, and the journey they make")
    ap.add_argument("--build3", action="store_true")
    ap.add_argument("--selftest3", action="store_true",
                    help="L3's offline checks")
    ap.add_argument("--census", action="store_true",
                    help="how many of the baked residents can commute, and "
                         "why the rest cannot")
    ap.add_argument("--who", default=None, help="pin one resident by npc_id")
    ap.add_argument("--rate", type=float, default=0.0,
                    help="one clock rate only, in station seconds a second")
    ap.add_argument("--godot", default=None)
    ap.add_argument("--engine-root", default=None)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.walk:
        return gate(a)
    if a.commute:
        return gate3(a)
    if a.selftest3:
        return _selftest3()
    if a.census:
        census()
        return 0
    if a.build3 or a.report3:
        schema, profile = it.load()
        cand = choose3(schema, profile, a.who)
        man, _p = build3(schema, profile, cand, rate=a.rate or 1.0,
                         quiet=a.report3)
        print_commute(man)
        if a.report3:
            print(f"\n  EVERY NAMED RESIDENT WHO COULD MAKE THIS JOURNEY")
            for c in candidates3(schema, profile):
                r = c["res"]
                print(f"     {r.name:22s} {r.species:9s} {r.role:10s} "
                      f"{r.home:16s} -> {r.job:18s} shift {c['start_h']:05.2f}")
        return 0
    if a.build:
        schema, profile = it.load()
        cand = choose(a.who)
        print_commuter(schema, profile, cand)
        build(schema, profile, cand, rate=a.rate or 1.0)
        return 0
    if a.primitives:
        primitives()
        return 0
    if a.report:
        report()
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
