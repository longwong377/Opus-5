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
import populace as P                                             # noqa: E402
import routes as RT                                              # noqa: E402
import route_walk as RW                                          # noqa: E402
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
CAPSULE_R_M = 0.35
CAPSULE_H_M = 1.8

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


def room_legs(schema, profile, m, place_key, outward):
    """Getting through one room's doorway, in the direction of travel.

    `outward` is leaving the room; otherwise entering it. THE DOORWAY IS THE
    PLACE A BODY GETS STUCK and `route_walk` paid for the rule this reproduces:
    a waypoint IN an aperture is tight (`door_tol_m`, derived from the aperture
    and the capsule), and there is an aim point on the doorway's own centre line
    at both ends, because a body that turns while standing in a doorway meets
    the jamb.
    """
    place = DIR.by_key(place_key)
    door = next(r for r in m["rooms"] if r["key"] == place_key)
    fr = m["floor_r_m"]
    cz = m["z_m"]
    tol = RW.door_tol_m()
    z_inner = place["z_m"] + D.room_interior_half_m(schema, profile, place)
    target = list(W.room_target(m, place))
    in_door = RW._at(fr, door["door_deg"], z_inner - 0.5)
    at_door = RW._at(fr, door["door_deg"], cz)
    if outward:
        pts = [target, in_door, at_door]
        return RW._leg("room", f"out of {place_key} through its door at "
                               f"{door['door_deg']:.0f} deg", pts,
                       RW._tight(pts, [1, 2], tol))
    pts = [at_door, in_door, target]
    return RW._leg("room", f"through the door into {place_key} at "
                           f"{door['door_deg']:.0f} deg", pts,
                   RW._tight(pts, [0, 1], tol))


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
    if not any(r["key"] == res.job for r in m["rooms"]):
        raise ValueError(f"{res.job} is not on the same z-cluster as "
                         f"{res.home}; L1 walks one corridor")
    d0 = next(r for r in m["rooms"] if r["key"] == res.home)["door_deg"]
    d1 = next(r for r in m["rooms"] if r["key"] == res.job)["door_deg"]
    fr, cz = m["floor_r_m"], m["z_m"]

    arc = RW._arc_points(fr, d0, d1, cz)
    legs = [
        room_legs(schema, profile, m, res.home, outward=True),
        RW._leg("ring", f"the ring corridor of {sector}/{ring}/{deck} at "
                        f"r={fr:.1f} m, {d0:.0f} deg -> {d1:.0f} deg", arc,
                RW._tight(arc, [0, len(arc) - 1], RW.door_tol_m())),
        room_legs(schema, profile, m, res.job, outward=False),
    ]
    pts = []
    for l in legs:
        for q in l["points"]:
            if not pts or math.dist(pts[-1], q) > 1e-6:
                pts.append(list(q))
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    return {"legs": legs, "points": pts, "length_m": round(length, 3),
            "meta": m, "verts": v, "tris": t, "all_meta": meta,
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
    groups = [("shell", 0, len(tris))]
    base = 0
    for m in meta["clusters"]:
        for nm, lo, hi in m.get("groups", ()):
            groups.append((nm, base + lo, base + hi))
        base += m["triangles"]
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
    spawn = list(W.room_target(m, home))
    post = list(W.room_target(m, job))

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
                    help="THE GATE: three clock rates and three controls")
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
