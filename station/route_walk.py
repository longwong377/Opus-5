#!/usr/bin/env python3
"""G2 ROUTE WALKED -- one body, two decks, and the lift in between.

WHAT WAS MISSING, MEASURED RATHER THAN SUMMARISED. `station/routes.py` reports
the station as **1 foot-connected component**. That is a claim about a GRAPH.
Every walk test in this repository walks inside ONE z-cluster:

    walkable.py --deck blue/0/0     126 m of corridor, one cluster, one deck
    drum_walk.py                    the drum's ground, one place
    transit_runtime.py --ride       the lift alone -- a body boards at landing 3,
                                    rides to landing 0 and alights, and the
                                    lobby it starts in is one 9.2 m section of
                                    corridor built for the test

**No body had ever walked from one deck to another.** The graph said you could;
nothing had.

WHAT THIS DOES. It takes a route OUT OF `routes.py` -- shortest path over the
station's own circulation graph, printed as legs with their kind -- and walks
it, end to end, in Godot:

    spawn outside a named room on deck A
      -> its ring corridor          (ring)
      -> the deck's axial spine     (axial)     the corridor that runs ALONG the ship
      -> the transit column's lobby
      -> into the car, doors shut   (lift)
      -> RIDE, radially, to another deck
      -> out, and the far deck's spine and ring corridor
      -> INTO a named room on deck B

and it reports **metres covered ON THE FLOOR**, frames spent off it, and where
it stopped. `floor_m` and not path length, because the streaming work on this
same codebase found a body reporting 11,712 m of "distance travelled" while
falling. A gate that adds up displacement without asking whether the body was
standing on anything scores a fall as a journey.

NOTHING HERE AUTHORS GEOMETRY. Every piece is the station's own generator:

    the cluster shell   deck.build_collision  -- rooms, vestibules, prop boxes
    its corridor        collision.corridor_shell, from deck.deck_plan
    the spine           collision.axial_shell at the sector's transit angle
    the column          lift.shaft_geometry + transit_runtime.build_lift, the
                        SAME call station/spoke_way.py makes for
                        column_<sector>.glb, at the same angle and the same z
    the car, its doors  transit_runtime.car_collision / car_render
    the ride            the motion table transit_runtime writes, whose seconds
                        are navigation.lift_ride_s and whose peak is asserted
                        against the Coriolis cap before it is written

THE ONE PLACE IT REACHES PAST AN EXISTING FUNCTION IS THE JUNCTION APERTURE,
and it is a hole in a file this module does not own. `deck.build_deck_clusters`
cuts a junction door where an axial run meets a ring corridor -- `extra_doors`,
threaded through `deck_plan` into `interior.ring_arc`. **The collision path has
no such thread**: `deck.build_collision` calls `deck_plan` with no `extra_doors`
and no `must_cover`, so the shell a body stands on has a solid wall exactly
where the render has a doorway. Nothing had ever noticed, because no collision
had ever been built for a joined deck -- `tools/export_station.py` writes render
meshes only. `cluster_collision` below rebuilds the corridor with the aperture
in it and ASSERTS, triangle for triangle, that the rest of `build_collision`'s
output is untouched. The three-line fix that would retire it is in
docs/route-walk-4g.md.

Run: python3 station/route_walk.py --report    (the route and the legs, no engine)
     python3 station/route_walk.py --selftest  (everything answerable offline)
     python3 station/route_walk.py --walk      (THE GATE: the walk and both controls)
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
import routes as RT                                              # noqa: E402
import spoke_way as SW                                           # noqa: E402
import transit_runtime as TR                                     # noqa: E402
import walkable as W                                             # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/route")
STATION = os.path.join(ROOT, "station/generated/scene/station")

# How far apart the points of a curved leg are, in degrees of ring.
#
# A body is steered straight at its next waypoint, so a leg laid across an arc
# with two points is a body steered across the chord -- and at r = 289 m, 30
# degrees of chord bulges 9.8 m out of a corridor 2.16 m wide. The step is set
# the way `collision.corridor_shell` sets its own faceting: by sagitta.
# r(1-cos(dt/2)) at 2 degrees and 500 m is 76 mm, inside the corridor's own
# half width by an order of magnitude, at every radius this station has.
RING_STEP_DEG = 2.0

# And along a straight leg. Nothing needs subdividing on a straight run -- these
# exist so the report can say WHERE a body stopped rather than only that it did.
AXIAL_STEP_M = 40.0

# How close to a waypoint counts as reaching it. The corridor's clear half width
# is 1.08 m and the capsule's radius is 0.35, so a body walking down the middle
# is within 0.73 m of the centre line by construction; 0.8 m therefore cannot be
# passed by standing still against a wall and cannot be failed by ordinary
# contact with one.
WAYPOINT_TOL_M = 0.8

# The player's capsule radius. `godot/scripts/walk.gd`, `transit.gd` and this
# module's own runtime all build the same 0.35 m capsule, and
# `collision.floor_holes` measures floor gaps against the same figure.
CAPSULE_R_M = 0.35

# AND A DOORWAY IS NOT A CORRIDOR. A door aperture is `door_width_m` wide -- half
# the width of the corridor it is cut in -- so a body that "reached" a waypoint
# 0.8 m off its centre line then turns for the next one and meets the JAMB. That
# is the failure `deck.deck_plan`'s phase sweep was written for, measured there
# as "0.70-0.74 m of progress into every such cluster", and it is exactly what
# the first run of this gate did: the body walked the ring corridor, stopped
# 0.8 m short of the junction and stood against the wall beside a 1.5 m opening
# for 7,093 frames.
#
# So a waypoint IN a doorway is tight, and the figure is derived rather than
# tuned: the capsule has `door_w/2 - CAPSULE_R_M` of clearance either side, and
# the tolerance is half of that, leaving the same margin again.
def door_tol_m(p=None):
    import interior_kit as K                                      # noqa: PLC0415
    return ((p or K.PROVISIONAL)["door_width_m"] / 2.0 - CAPSULE_R_M) / 2.0


# How far past a doorway the body is aimed before it goes through. Standing IN
# the aperture and turning is what catches a jamb; aiming at a point beyond it,
# on the same centre line, walks a straight line through.
AIM_M = 2.0

# How long a leg may take, as a multiple of its own length at the player's
# walking speed. 2.5x absorbs the acceleration at each waypoint and the arc a
# body cuts round a corner; a body that has genuinely stopped fails it.
LEG_BUDGET = 2.5
LEG_BUDGET_FLOOR_FRAMES = 240


# ---------------------------------------------------------------------------
# WHERE THE COLUMN IS. `tools/export_station.py`'s rule, read rather than
# restated: one column per sector, at `routes.transit_angle`, at the LOWEST z
# any of that sector's clusters sits at.
# ---------------------------------------------------------------------------

def column_address(nodes, sector):
    """(angle_deg, z_m) of a sector's transit column."""
    zs = [k[3] for k in nodes if k[0] == sector]
    if not zs:
        raise ValueError(f"{sector} carries no located cluster")
    return RT.transit_angle(sector, nodes), min(zs)


def column_stack(schema, profile, nodes, sector):
    """The column's landing stack -- `spoke_way.ring_stack`, one column for
    every ring of the sector, which is what `export_station` builds."""
    rings = sorted({k[1] for k in nodes if k[0] == sector})
    _ang, z = column_address(nodes, sector)
    return SW.ring_stack(schema, profile, sector, rings, z)


def shaft(schema, profile, nodes, sector):
    """The column, as `lift.shaft_geometry` -- every landing it has."""
    ang, z = column_address(nodes, sector)
    stack = column_stack(schema, profile, nodes, sector)
    rings = sorted({d["ring_index"] for d in stack})
    return L.shaft_geometry(schema, profile, sector, min(rings),
                            tuple(range(len(stack))), ang, z, stack=stack)


# ---------------------------------------------------------------------------
# WHICH CLUSTERS A ROUTE CAN ACTUALLY START AND END IN
# ---------------------------------------------------------------------------
# FOUR FILTERS, AND THREE OF THEM ARE FINDINGS RATHER THAN CONVENIENCES. Each
# one is a question `routes.py` grants without asking, and each answer is
# printed by `--report` so the size of what is being stepped over is visible.

def endpoints(schema, profile, nodes=None, quiet=True):
    """Every cluster a body could start or finish a route in, and why not.

    Returns (list of ok rows, list of (row, reason) rejected).
    """
    nodes = nodes if nodes is not None else RT.clusters()
    sectors = sorted({k[0] for k in nodes})
    ang = {s: RT.transit_angle(s, nodes) for s in sectors}
    zcol = {s: column_address(nodes, s)[1] for s in sectors}
    land = {}
    for s in sectors:
        st = column_stack(schema, profile, nodes, s)
        land[s] = {(d["ring_index"], d["ring_deck_index"]): (i, d) for i, d in
                   enumerate(st)}
    built = built_decks()

    ok, bad = [], []
    for k in sorted(nodes):
        s, r, dk, z = k
        row = {"key": k, "sector": s, "ring": r, "deck": dk, "z": z,
               "places": list(nodes[k]["places"]), "spine_deg": ang[s],
               "z_col": zcol[s]}
        # 1. THE COLUMN HAS A LANDING ON THIS DECK. `routes.py` grants a `lift`
        #    edge from EVERY deck's spine to its ring's column, unconditionally
        #    -- `built=_LIFT_EXISTS`, which asks the filesystem whether
        #    lift.py exists and nothing else. The column is built at ONE z, and
        #    `interior.decks_in_ring` returns a different number of decks at
        #    different z: blue ring 0 has 6 decks at z=6880, where the column
        #    stands, and 10 at z=7120, where the docking bays are.
        if (r, dk) not in land[s]:
            bad.append((row, f"{s}/{r}/{dk} has no landing on the column at "
                             f"z={zcol[s]:.0f}"))
            continue
        idx, lg = land[s][(r, dk)]
        row["landing"] = idx
        row["landing_r_m"] = lg["floor_r_m"]
        try:
            plan = D.deck_plan(schema, profile, s, r, dk, z)
        except ValueError as e:
            bad.append((row, str(e)))
            continue
        row["radius_m"] = plan["radius"]
        row["cz"] = plan["cz"]
        # 2. AND THE LANDING IS AT THE SAME RADIUS AS THE DECK'S CORRIDOR.
        #    `deck.deck_plan` takes its radius from `deck._ring_cells`, which
        #    does not take a z; `lift.shaft_geometry` takes its landings from
        #    `interior.decks_in_ring(z_m=)`, which does. Where they disagree
        #    the lift's doors open onto a lobby at one radius and the deck's
        #    corridor is at another, and no body can cross.
        if abs(plan["radius"] - lg["floor_r_m"]) > 0.01:
            bad.append((row, f"the deck's corridor is at r={plan['radius']:.2f} "
                             f"and its landing at r={lg['floor_r_m']:.2f} -- "
                             f"{plan['radius'] - lg['floor_r_m']:+.2f} m apart"))
            continue
        # 3. THE CORRIDOR REACHES THE SPINE WITHOUT MOVING ITS ROOM DOORS.
        #    `deck_arc(must_cover=)` extends a cluster's corridor to the transit
        #    angle, and extending it re-runs `deck_plan`'s phase sweep, which
        #    can land the room doors somewhere else. `build_collision` builds
        #    its rooms against the UNEXTENDED plan, so the two have to agree
        #    about every door or the shell and its vestibules are laid over
        #    different corridors.
        p2 = D.deck_plan(schema, profile, s, r, dk, z, must_cover=ang[s])
        a0 = [round(x[1]["angle_deg"], 6) for x in plan["rooms"]]
        a1 = [round(x[1]["angle_deg"], 6) for x in p2["rooms"]]
        if a0 != a1:
            bad.append((row, "extending the corridor to the transit angle moves "
                             "this cluster's room doors"))
            continue
        row["arc"] = (p2["lo"], p2["lo"] + p2["span"])
        row["doors"] = [(q["key"], round(d["angle_deg"], 3))
                        for q, d, _dx in plan["rooms"]]
        # 4. AND THE SPINE IS LONG ENOUGH TO BE A LEG. The lobby is one
        #    `interior.AXIAL_SECTION_M` deep; a cluster sitting on top of the
        #    column has no axial corridor between them to walk.
        row["spine_m"] = plan["cz"] - zcol[s]
        if f"{s}_{r}_{dk}" not in built:
            bad.append((row, f"{s}_{r}_{dk}.glb was never built"))
            continue
        if not row["doors"]:
            bad.append((row, "no room on this cluster got a door"))
            continue
        ok.append(row)
    if not quiet:
        for row, why in bad:
            print(f"     - {row['sector']}/{row['ring']}/{row['deck']} "
                  f"z={row['z']:.0f}: {why}")
    return ok, bad


def built_decks():
    """Which decks `tools/export_station.py` actually wrote, from its manifest.

    The route is walked on collision shells this module builds; the RENDER of
    every deck it crosses is already on disk and is not rebuilt. A route whose
    decks were never exported is a route through geometry nobody can see, so it
    is not offered.
    """
    path = os.path.join(STATION, "station_manifest.json")
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        man = json.load(f)
    return {d["key"] for d in man.get("decks", ())
            if d.get("ok") and os.path.exists(
                os.path.join(STATION, d["key"] + ".glb"))}


# ---------------------------------------------------------------------------
# THE ROUTE, OUT OF THE GRAPH
# ---------------------------------------------------------------------------

def path_between(nodes, es, a_key, b_key):
    """Shortest path over `routes.edges`, as a list of legs with their kind.

    BREADTH FIRST OVER THE EDGES THE GRAPH ACTUALLY HAS. The route is not
    written down here; `routes.py` says which connections exist and this asks it
    for one. The `axial` edge is a self-loop on a spine node -- the spine IS the
    axial corridor -- so passing through a spine node is what traverses it, and
    that leg is inserted where the path enters one.
    """
    adj = {}
    kinds = {}
    axial = {}
    for e in es:
        if not e["built"]:
            continue
        if e["a"] == e["b"]:
            if e["kind"] == "axial":
                axial[e["a"]] = e
            continue
        adj.setdefault(e["a"], []).append(e["b"])
        adj.setdefault(e["b"], []).append(e["a"])
        kinds[(e["a"], e["b"])] = e
        kinds[(e["b"], e["a"])] = e
    prev = {a_key: None}
    queue = [a_key]
    while queue:
        cur = queue.pop(0)
        if cur == b_key:
            break
        for nxt in adj.get(cur, ()):
            if nxt not in prev:
                prev[nxt] = cur
                queue.append(nxt)
    if b_key not in prev:
        return None
    seq = []
    cur = b_key
    while cur is not None:
        seq.append(cur)
        cur = prev[cur]
    seq.reverse()
    legs = []
    for a, b in zip(seq, seq[1:]):
        legs.append({"kind": kinds[(a, b)]["kind"], "a": a, "b": b,
                     "why": kinds[(a, b)]["why"]})
        if b in axial:
            legs.append({"kind": "axial", "a": b, "b": b,
                         "why": axial[b]["why"]})
    return legs


def name(k):
    if k[0] in ("spine", "column"):
        return (f"{k[0]} {k[1]}/{k[2]}"
                + (f"/{k[3]}" if len(k) > 3 else ""))
    return f"{k[0]}/{k[1]}/{k[2]} z={k[3]:.0f}"


def approach_m(row, place_key):
    """How far a place is from its deck's spine: the arc, plus the spine.

    THE ARC IS MOST OF IT AND THE FIRST VERSION OF THIS RANKING IGNORED IT.
    `deck_arc(must_cover=)` extends a cluster's corridor to the transit angle,
    and `red/1/6`'s rooms sit at 280 degrees while red's spine stands at 90 --
    657 m of ring corridor before a single metre of spine. A route ranked on
    spine length alone picks that and calls it short.
    """
    d = dict(row["doors"]).get(place_key)
    if d is None:
        return None
    arc = abs(((d - row["spine_deg"]) + 180.0) % 360.0 - 180.0)
    return (math.radians(arc) * row["radius_m"]
            + max(0.0, row["spine_m"]))


def choose(schema, profile, nodes=None, frm=None, to=None):
    """Which two places the route runs between. FROM THE DATA, not by hand.

    Among every pair of endpoint places on different decks of one sector, the
    pair whose total walk is shortest -- so the gate crosses every leg kind in
    the fewest frames it can. Deterministic: ties break on the place keys.
    """
    nodes = nodes if nodes is not None else RT.clusters()
    ok, _bad = endpoints(schema, profile, nodes)
    cand = []
    for row in ok:
        for p, _deg in row["doors"]:
            d = approach_m(row, p)
            if d is not None:
                cand.append((row, p, d))
    by_place = {p: (row, d) for row, p, d in cand}
    if frm or to:
        if frm not in by_place or to not in by_place:
            missing = [p for p in (frm, to) if p not in by_place]
            raise ValueError(f"{missing} is not a place a route can start or "
                             f"end at -- run --report for the list")
        return by_place[frm][0], frm, by_place[to][0], to
    best = None
    for i, (a, pa, da) in enumerate(cand):
        for b, pb, db in cand[i + 1:]:
            if a["sector"] != b["sector"] or a["deck"] == b["deck"]:
                continue
            # A SPINE SHORT ENOUGH TO BE THE LOBBY IS NOT AN AXIAL LEG. The
            # column's lobby is one `interior.AXIAL_SECTION_M`; a cluster
            # sitting on top of it has no corridor between them to walk, and a
            # route that skips its own axial leg proves nothing about one.
            if min(a["spine_m"], b["spine_m"]) < it.AXIAL_SECTION_M * 2:
                continue
            cost = (round(da + db, 3), pa, pb)
            if best is None or cost < best[0]:
                best = (cost, a, pa, b, pb)
    if best is None:
        raise ValueError("no two endpoint places sit on different decks of "
                         "one sector")
    _c, a, pa, b, pb = best
    return a, pa, b, pb


# ---------------------------------------------------------------------------
# THE GEOMETRY
# ---------------------------------------------------------------------------

def _prefix_matches(v, t, cv, ct):
    """Are the first triangles of `(v, t)` exactly the mesh `(cv, ct)`?

    `deck.build_collision` builds its corridor FIRST and appends every room
    after it, so its first `len(ct)` triangles are that corridor and nothing
    else. This is what makes the splice below safe rather than hopeful: if that
    module ever reorders, this fires instead of a body walking on a shell whose
    corridor has silently moved.
    """
    if len(t) < len(ct) or len(v) < len(cv):
        return False
    return t[:len(ct)] == list(ct) and v[:len(cv)] == list(cv)


def cluster_collision(schema, profile, sector, ring, deck, z_m, spine_deg,
                      side=-1, props=True):
    """A cluster's collision shell WITH the aperture its deck's spine needs.

    `deck.build_collision` is the station's own cluster shell, and this is that
    shell with its corridor rebuilt to (a) reach the transit angle and (b) carry
    the junction door where the axial spine meets it. Both are things the RENDER
    path already does -- `deck.build_deck(extra_doors=, must_cover=)` -- and the
    collision path has no argument for either.

    The rooms, their vestibules, their door panels and their prop boxes come
    through untouched, and `_prefix_matches` asserts that what is being replaced
    is exactly the corridor. `endpoints` has already checked that extending the
    arc does not move a single room door, so the rooms and the new corridor are
    laid over the same plan.
    """
    d0 = D.deck_plan(schema, profile, sector, ring, deck, z_m)
    d1 = D.deck_plan(schema, profile, sector, ring, deck, z_m,
                     must_cover=spine_deg,
                     extra_doors=((spine_deg, side),))
    a0 = [round(x[1]["angle_deg"], 6) for x in d0["rooms"]]
    a1 = [round(x[1]["angle_deg"], 6) for x in d1["rooms"]]
    if a0 != a1:
        raise ValueError(f"{sector}/{ring}/{deck} z={z_m:.0f}: extending the "
                         f"corridor to {spine_deg:.1f} deg moves its room "
                         f"doors {a0} -> {a1}")

    v, t, meta = D.build_collision(schema, profile, sector, ring, deck,
                                   z_m=z_m, props=props)
    cv, ct, _cm = C.corridor_shell(schema, profile, sector, ring,
                                   degrees=d0["span"], start_deg=d0["lo"],
                                   radius_m=d0["radius"], z_offset=d0["cz"],
                                   doors=[x[1] for x in d0["rooms"]])
    if not _prefix_matches(v, t, cv, ct):
        raise AssertionError(
            "deck.build_collision no longer starts with the corridor shell "
            "collision.corridor_shell builds from the same plan -- the splice "
            "in route_walk.cluster_collision is not valid any more")
    rooms_t = t[len(ct):]
    rooms_v = v[len(cv):]
    if any(i < len(cv) for tr in rooms_t for i in tr):
        raise AssertionError("a room triangle indexes a corridor vertex")

    jd = dict(spine_door(spine_deg, side))
    jv, jt, jm = C.corridor_shell(schema, profile, sector, ring,
                                  degrees=d1["span"], start_deg=d1["lo"],
                                  radius_m=d1["radius"], z_offset=d1["cz"],
                                  doors=[x[1] for x in d1["rooms"]] + [jd])
    verts = list(jv)
    tris = list(jt)
    base = len(verts)
    verts.extend(rooms_v)
    tris.extend((a - len(cv) + base, b - len(cv) + base, c - len(cv) + base)
                for a, b, c in rooms_t)
    groups = [("corridor", 0, len(jt))]
    for nm, lo, hi in meta.get("groups", ()):
        groups.append((nm, lo - len(ct) + len(jt), hi - len(ct) + len(jt)))
    out = dict(jm)
    out["rooms"] = meta.get("rooms", [])
    out["unopened"] = meta.get("unopened", [])
    out["prop_boxes"] = meta.get("prop_boxes", 0)
    out["room_tris"] = len(rooms_t)
    out["junction_deg"] = spine_deg
    out["junction_side"] = side
    return verts, tris, groups, out


def spine_door(spine_deg, side):
    """The junction aperture, in `collision.corridor_shell`'s own door format."""
    return {"angle_deg": float(spine_deg), "side": float(side),
            "z_m": None, "junction": True}


def column_collision(schema, profile, g, landings=True):
    """The column's static shell -- shaft, sills and a lobby at every landing.

    `transit_runtime.static_collision` with ONE argument threaded through:
    `lift.lift_collision(landings=False)`, that module's own negative control,
    which seals every landing aperture. transit_runtime does not expose it and
    this file needs it, because "the landing doors are sealed" is a control the
    milestone requires and inventing a slab to stand in the doorway would be a
    control against geometry nobody ships. `_selftest` asserts this function
    is triangle-for-triangle `transit_runtime.static_collision` when
    `landings=True`, so the duplication cannot drift.
    """
    sv, st, sm = L.lift_collision(schema, profile, g=g, car=False,
                                  landings=landings)
    verts, tris = list(sv), list(st)
    groups = [(f"liftshaft__{n}", a, b) for n, a, b in sm["groups"]]
    z0, z1 = TR.lobby_span(g)
    for lg in g["landings"]:
        lv, lt, _lm = C.axial_shell(schema, profile, g["sector"],
                                    g["ring_index"], z0, z1,
                                    angle_deg=g["angle_deg"],
                                    radius_m=lg["floor_r_m"])
        o, t0 = len(verts), len(tris)
        verts.extend(lv)
        tris.extend((a + o, b + o, c + o) for a, b, c in lt)
        groups.append((f"liftlobby_{lg['index']}", t0, len(tris)))
    return verts, tris, groups


def spine(schema, profile, sector, ring, radius_m, angle_deg, z_from, z_to):
    """One deck's axial spine, from the column's lobby to a cluster's corridor.

    `collision.axial_shell`, at the sector's transit angle and the deck's own
    corridor radius -- the same call `deck.build_deck_clusters` makes to join
    two clusters, and the same radius the lobby at that landing stands on.
    """
    return C.axial_shell(schema, profile, sector, ring, z_from, z_to,
                         angle_deg=angle_deg, radius_m=radius_m)


# ---------------------------------------------------------------------------
# THE WAYPOINTS -- where the body is steered, leg by leg
# ---------------------------------------------------------------------------

def _at(radius, angle_deg, z):
    a = math.radians(angle_deg)
    return [radius * math.cos(a), radius * math.sin(a), z]


def _arc_points(radius, a0, a1, z):
    """Points along a ring corridor between two angles, at its faceting."""
    d = ((a1 - a0) + 180.0) % 360.0 - 180.0
    n = max(1, int(math.ceil(abs(d) / RING_STEP_DEG)))
    return [_at(radius, a0 + d * i / n, z) for i in range(n + 1)]


def _line_points(p0, p1, step=AXIAL_STEP_M):
    d = math.dist(p0, p1)
    n = max(1, int(math.ceil(d / step)))
    return [[p0[k] + (p1[k] - p0[k]) * i / n for k in range(3)]
            for i in range(n + 1)]


def _leg(kind, note, points, tols=None):
    pts = [p for p in points]
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    if tols is None:
        tols = [WAYPOINT_TOL_M] * len(pts)
    return {"kind": kind, "note": note, "points": pts,
            "tols": [round(t, 4) for t in tols],
            "length_m": round(length, 2)}


def _tight(points, which, tol):
    t = [WAYPOINT_TOL_M] * len(points)
    for i in which:
        t[i] = tol
    return t


def legs_for(schema, profile, row, meta, g, place_key, outbound):
    """The walking legs on one deck, in the direction of travel.

    `outbound` is the deck the body starts on -- corridor, then spine, then the
    lobby. Inbound is the mirror: lobby, spine, corridor, and finally the room.

    EVERY DOORWAY GETS AN AIM POINT ON ITS CENTRE LINE AT BOTH ENDS, and the
    waypoint inside it is tight. A body is steered straight at its next
    waypoint, so a doorway crossed by turning inside it is a doorway whose jamb
    the capsule meets -- see `door_tol_m`.
    """
    floor_r = meta["floor_r_m"]
    hw = meta["half_w_m"]
    cz = meta["z_m"]
    ang = row["spine_deg"]
    door = next((d for d in meta["rooms"] if d["key"] == place_key), None)
    if door is None:
        raise ValueError(f"{place_key} has no door in the built shell "
                         f"({[d['key'] for d in meta['rooms']]})")
    place = DIR.by_key(place_key)
    lg = g["landings"][row["landing"]]
    lobby = list(TR.lobby_stand(g, lg))
    z_lobby_end = TR.lobby_span(g)[1]
    tol = door_tol_m()
    where = f"{row['sector']}/{row['ring']}/{row['deck']}"
    junction = _at(floor_r, ang, cz)
    # On the spine's centre line, clear of the ring corridor's wall.
    aim_spine = _at(floor_r, ang, cz - hw - AIM_M)
    at_door = _at(floor_r, door["door_deg"], cz)
    # 0.5 m inside the room, past the vestibule the shell puts between the
    # corridor and the room's own wall -- `deck.build_collision`'s `inner`.
    z_inner = place["z_m"] + D.room_interior_half_m(schema, profile, place)
    in_door = _at(floor_r, door["door_deg"], z_inner - 0.5)
    # ON THE FLOOR IN THE MIDDLE OF THE ROOM -- `walkable.room_target`, the same
    # point `walkable.py --deck` walks to, so "reached a named location" means
    # here what it means there.
    target = list(W.room_target(meta, place))

    out = []
    if outbound:
        arc = _arc_points(floor_r, door["door_deg"], ang, cz)
        out.append(_leg("ring", f"the ring corridor of {where}, "
                                f"{place_key}'s door to the spine at "
                                f"{ang:.0f} deg", arc,
                        _tight(arc, [len(arc) - 1], tol)))
        pts = [junction, aim_spine] + _line_points(aim_spine, lobby)[1:]
        out.append(_leg("axial", f"the deck's axial spine at {ang:.0f} deg, "
                                 f"{cz:.0f} m -> the column's lobby at "
                                 f"{z_lobby_end:.0f} m", pts,
                        _tight(pts, [1], tol)))
    else:
        pts = _line_points(lobby, aim_spine)[:-1] + [aim_spine, junction]
        out.append(_leg("axial", f"the deck's axial spine at {ang:.0f} deg, "
                                 f"the column's lobby -> {cz:.0f} m", pts,
                        _tight(pts, [len(pts) - 2], tol)))
        arc = _arc_points(floor_r, ang, door["door_deg"], cz)
        out.append(_leg("ring", f"the ring corridor of {where}, the spine to "
                                f"{place_key}'s door", arc,
                        _tight(arc, [len(arc) - 1], tol)))
        pts = [at_door, in_door, target]
        out.append(_leg("room", f"through the door into {place_key}", pts,
                        _tight(pts, [0, 1], tol)))
    return out


# ---------------------------------------------------------------------------
# BUILD
# ---------------------------------------------------------------------------

def _glb(obj_path):
    """OBJ -> GLB. `station/export_gltf.py` makes one node per group name, which
    is how the runtime gets a door panel it can switch off without touching the
    shell it is cut in. Its report goes to stdout; this gate has its own."""
    import contextlib                                             # noqa: PLC0415
    import io                                                     # noqa: PLC0415
    import export_gltf                                            # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path,
                "--out", obj_path[:-4] + ".glb"]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            export_gltf.main()
    finally:
        sys.argv = argv
    return obj_path[:-4] + ".glb"


def _write(stem, verts, tris, groups, name_="route"):
    obj = os.path.join(OUT, stem + ".obj")
    C.write_obj(obj, verts, tris, groups, name=name_)
    glb = _glb(obj)
    os.remove(obj)
    return glb


def build(schema, profile, a_row, a_key, b_row, b_key, quiet=False):
    """Write every collision mesh the route needs, and the manifest.

    THE COLUMN IS NOT A TEST RIG. `shaft()` builds it at the sector's own
    transit angle and the same z `tools/export_station.py` puts it at, from the
    same `spoke_way.ring_stack` -- so the shaft this body rides is the shaft in
    `column_<sector>.glb`, and its landings are that column's landings.
    """
    os.makedirs(OUT, exist_ok=True)
    nodes = RT.clusters()
    sector = a_row["sector"]
    g = shaft(schema, profile, nodes, sector)

    # THE LIFT'S OWN RUNTIME ARTEFACTS, from the module that owns them, into a
    # directory of this file's own. `transit_runtime.build_lift` writes the
    # shaft, its lobbies, the car split so the piece that moves is its own node,
    # and the motion tables -- and it writes them to a module-level path that
    # `--ride` also uses. Pointing it here keeps the two gates' artefacts
    # disjoint, which is session 3w's lesson: disjoint source files are not
    # disjoint artefacts.
    import contextlib                                             # noqa: PLC0415
    import io                                                     # noqa: PLC0415
    keep = TR.OUT
    TR.OUT = OUT
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            lift_man = TR.build_lift(schema, profile, g, quiet=True)
    finally:
        TR.OUT = keep

    files = []
    a_v, a_t, a_g, a_meta = cluster_collision(
        schema, profile, a_row["sector"], a_row["ring"], a_row["deck"],
        a_row["z"], a_row["spine_deg"])
    files.append(("cluster_a", _write("cluster_a_col", a_v, a_t, a_g)))
    b_v, b_t, b_g, b_meta = cluster_collision(
        schema, profile, b_row["sector"], b_row["ring"], b_row["deck"],
        b_row["z"], b_row["spine_deg"])
    files.append(("cluster_b", _write("cluster_b_col", b_v, b_t, b_g)))

    z_lobby_end = TR.lobby_span(g)[1]
    spines = {}
    for tag, row, meta in (("a", a_row, a_meta), ("b", b_row, b_meta)):
        sv, st, sm = spine(schema, profile, row["sector"], row["ring"],
                           meta["radius_m"], row["spine_deg"],
                           z_lobby_end, meta["z_m"] - meta["half_w_m"])
        files.append((f"spine_{tag}",
                      _write(f"spine_{tag}_col", sv, st,
                             [(f"spine_{tag}", 0, len(st))])))
        spines[tag] = sm

    # The column, twice: as it ships, and with every landing aperture sealed --
    # `lift.lift_collision(landings=False)`, the generator's own control.
    cv, ct, cg = column_collision(schema, profile, g, landings=True)
    files.append(("column", _write("column_col", cv, ct, cg)))
    sv, st, sg = column_collision(schema, profile, g, landings=False)
    sealed = _write("column_col_sealed", sv, st, sg)

    a_legs = legs_for(schema, profile, a_row, a_meta, g, a_key,
                      outbound=True)
    b_legs = legs_for(schema, profile, b_row, b_meta, g, b_key,
                      outbound=False)
    a_door = next(d for d in a_meta["rooms"] if d["key"] == a_key)
    spawn = C.stand_at(a_meta, a_door["door_deg"])

    man = {
        "kind": "route",
        "sector": sector,
        "spine_deg": a_row["spine_deg"],
        "z_col": a_row["z_col"],
        "omega_rad_s": schema["station"]["rotation"]["omega_rad_s"]["value"],
        "from": {"place": a_key, "deck": f"{a_row['sector']}/{a_row['ring']}/"
                                         f"{a_row['deck']}",
                 "landing": a_row["landing"], "z": a_meta["z_m"],
                 "radius_m": a_meta["radius_m"],
                 "door_deg": a_door["door_deg"]},
        "to": {"place": b_key, "deck": f"{b_row['sector']}/{b_row['ring']}/"
                                       f"{b_row['deck']}",
               "landing": b_row["landing"], "z": b_meta["z_m"],
               "radius_m": b_meta["radius_m"],
               "door_deg": next(d for d in b_meta["rooms"]
                                if d["key"] == b_key)["door_deg"]},
        "collision_glbs": [p for _n, p in files],
        "column_col_sealed_glb": sealed,
        "car_glb": lift_man["car_glb"],
        "car_col_glb": lift_man["car_col_glb"],
        "origin": lift_man["origin"], "ux": lift_man["ux"],
        "uy": lift_man["uy"], "travel_axis": lift_man["travel_axis"],
        "pivot": lift_man["pivot"],
        "leaf_travel": lift_man["leaf_travel"],
        "leaf_travel_m": lift_man["leaf_travel_m"],
        "car": lift_man["car"], "bore_hd": lift_man["bore_hd"],
        "landings": lift_man["landings"],
        "from_landing": a_row["landing"], "to_landing": b_row["landing"],
        "ride": lift_man["rides"][f"{a_row['landing']}-{b_row['landing']}"],
        "dwell_s": lift_man["dwell_s"],
        "g0_m_s2": lift_man["g0_m_s2"],
        "spawn": list(spawn),
        "target": {"key": b_key, "at": b_legs[-1]["points"][-1],
                   "arrive_m": W.ARRIVED_M},
        "legs_out": a_legs, "legs_in": b_legs,
        "waypoint_tol_m": WAYPOINT_TOL_M,
        "door_tol_m": round(door_tol_m(), 4),
        "capsule_r_m": CAPSULE_R_M,
        "leg_budget": LEG_BUDGET,
        "leg_budget_floor_frames": LEG_BUDGET_FLOOR_FRAMES,
        "walk_m": round(sum(l["length_m"] for l in a_legs + b_legs), 1),
        # EVERY STATE'S TIMEOUT, ADDED UP, PLUS A HALF. The per-leg budgets and
        # the settle, board and alight windows already bound the run; this is
        # the cap that fires when one of them does not, because a headless test
        # that never ends costs a session rather than failing -- see
        # docs/route-walk-4g.md. Derived from the legs and the ride the manifest
        # already carries; the half absorbs the two door cycles, which are the
        # only thing in the machine this figure does not name.
        "max_frames": int(1.5 * (
            sum(max(LEG_BUDGET_FLOOR_FRAMES,
                    math.ceil(l["length_m"] / 4.2 * 60.0 * LEG_BUDGET))
                for l in a_legs + b_legs)
            + 90 + 600 + 600
            + 60.0 * lift_man["rides"][
                f"{a_row['landing']}-{b_row['landing']}"]["seconds"])),
        "rise_m": round(abs(g["landings"][a_row["landing"]]["walk_r_m"]
                            - g["landings"][b_row["landing"]]["walk_r_m"]), 3),
        "tris": {"cluster_a": len(a_t), "cluster_b": len(b_t),
                 "spine_a": spines["a"]["triangles"],
                 "spine_b": spines["b"]["triangles"],
                 "column": len(ct)},
        "station_glbs": [os.path.join(STATION, f"{a_row['sector']}_"
                                      f"{a_row['ring']}_{a_row['deck']}.glb"),
                         os.path.join(STATION, f"{b_row['sector']}_"
                                      f"{b_row['ring']}_{b_row['deck']}.glb"),
                         os.path.join(STATION, f"column_{sector}.glb")],
    }
    path = os.path.join(OUT, "route.json")
    with open(path, "w") as f:
        json.dump(man, f, indent=1)
    if not quiet:
        print(f"  wrote {os.path.relpath(path, ROOT)} -- "
              f"{man['walk_m']:,.0f} m of walking, "
              f"{sum(man['tris'].values()):,} collision triangles")
    return man, path


# ---------------------------------------------------------------------------
# THE GATE
# ---------------------------------------------------------------------------

def run(path, godot, engine_root, timeout=1800, verbose=False, **switch):
    cmd = [godot, "--headless", "--path", engine_root,
           "res://scenes/route_test.tscn", "--",
           f"--manifest={path}", "--route-test"]
    for k, v in switch.items():
        cmd.append(f"--{k}={v}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    out = p.stdout + p.stderr
    if verbose:
        print(out)
    # A GDSCRIPT THAT DOES NOT PARSE DOES NOT FAIL -- IT IDLES. Godot loads the
    # scene, finds no script on it, and runs the main loop at 60 fps forever
    # with nothing in it, at about 1% of a core. This gate lost fifteen minutes
    # to `_r_max` surviving one edit and its declaration not, and the first
    # symptom was indistinguishable from a slow walk. It is the same shape as
    # session 4e's renderer falling back to OpenGL and exiting 0: the tool did
    # something other than what was asked and said so only in passing.
    if "Failed to load script" in out or "Parse Error" in out:
        bad = [l for l in out.splitlines()
               if "SCRIPT ERROR" in l or "Parse Error" in l
               or "Failed to load" in l]
        return {"error": "the runtime script did not load",
                "tail": "\n".join(bad[:6])}
    m = re.search(r"ROUTETEST (.+)", out)
    if not m:
        return {"error": "no verdict printed",
                "tail": "\n".join(out.strip().splitlines()[-25:])}
    d = {}
    for tok in m.group(1).split():
        k, _, v = tok.partition("=")
        d[k] = v
    d["legs"] = [dict(t.split("=", 1) for t in mm.group(1).split())
                 for mm in re.finditer(r"ROUTELEG (.+)", out)]
    return d


def verdict(d, man):
    """Did a body walk from one deck to another. In the terms G2 is written in.

    FIVE CLAIMS, and no single number carries them:

      completed   it got to the far room, rather than stopping somewhere
      rode        it was in the car while the car moved
      decks       it ended on a different deck from the one it started on
      floor       the distance was covered ON THE FLOOR
      air         and essentially none of it falling
    """
    if "error" in d:
        return False, d["error"] + ("\n" + d.get("tail", "")
                                    if d.get("tail") else "")
    if d.get("completed") != "true":
        return False, (f"stopped in `{d.get('stopped_at')}` on leg "
                       f"{d.get('leg')} ({d.get('leg_kind')}) -- "
                       f"{str(d.get('stopped_why')).replace('_', ' ')} -- "
                       f"{float(d.get('leg_left_m', 0)):.2f} m short of "
                       f"waypoint {d.get('wp')}, after "
                       f"{float(d.get('floor_m', 0)):.1f} m on the floor")
    if d.get("boarded") != "true" or d.get("alighted") != "true":
        return False, (f"never rode the car (boarded={d.get('boarded')}, "
                       f"alighted={d.get('alighted')})")
    if d.get("start_deck") == d.get("end_deck"):
        return False, (f"started and ended on deck {d.get('start_deck')} -- a "
                       f"route that changes no deck")
    if float(d.get("car_moved_m", 0.0)) < 1.0:
        return False, f"the car moved {d.get('car_moved_m')} m"
    off = int(d.get("offfloor", "1/0").split("/")[0])
    if off > 0:
        return False, (f"left the floor for {off} of "
                       f"{d.get('offfloor', '?/?').split('/')[1]} frames")
    if float(d.get("air_m", 1.0)) > 0.05:
        return False, f"{d.get('air_m')} m of the route was covered in the air"
    if int(d.get("ride_offfloor", "1/0").split("/")[0]) > 0:
        return False, (f"left the floor for {d['ride_offfloor']} frames DURING "
                       f"THE RIDE -- the car moved and the body did not go "
                       f"with it")
    # THE SPAWN IS A CLAIM THAT A PERSON CAN STAND THERE, and the settle frames
    # are excluded from `offfloor` because `collision.stand_at` deliberately
    # spawns 50 mm up. Excluding them without checking the drop would be hiding
    # the case the exclusion was made for.
    if abs(float(d.get("settle_drop_m", 9.9))) > 2.0 * 0.05:
        return False, (f"dropped {float(d['settle_drop_m']) * 1000:.0f} mm from "
                       f"a spawn 50 mm above the shell -- the floor is not "
                       f"where the shell says it is")
    if float(d.get("standoff_max_mm", 1e9)) > 50.0:
        return False, (f"stood {d['standoff_max_mm']} mm off the car floor at "
                       f"worst -- it is not riding, it is bouncing")
    near = float(d.get("arrive_m", 1e9))
    if near > float(man["target"]["arrive_m"]):
        return False, (f"ended {near:.2f} m from {man['target']['key']}")
    return True, ""


def _fmt(d, man):
    return (f"{float(d.get('floor_m', 0)):,.1f} m on the floor "
            f"({float(d.get('air_m', 0)):.2f} m in the air), "
            f"offfloor {d.get('offfloor')}, deck {d.get('start_deck')} -> "
            f"{d.get('end_deck')}, {float(d.get('arrive_m', -1)):.2f} m from "
            f"{man['target']['key']}")


def check_script(godot, engine_root):
    """Does the runtime script parse? Three seconds, before anything else.

    See `run` for why: a GDScript that does not parse costs a whole run's
    timeout and looks like a slow walk while it does it.
    """
    p = subprocess.run([godot, "--headless", "--path", engine_root,
                        "--check-only", "--script",
                        "res://scripts/route_test.gd"],
                       capture_output=True, text=True, timeout=180)
    out = p.stdout + p.stderr
    if p.returncode == 0 and "Parse Error" not in out:
        return None
    return "\n".join(l for l in out.splitlines()
                      if "ERROR" in l or "Parse Error" in l)


def gate(argv):
    schema, profile = it.load()
    godot = argv.godot or W.godot_binary()
    engine_root = argv.engine_root or os.path.join(ROOT, "godot")
    if godot is None:
        print("no double-precision Godot binary. run: bash tools/build_godot.sh")
        return 2
    why = check_script(godot, engine_root)
    if why:
        print("godot/scripts/route_test.gd does not parse:\n" + why)
        return 2
    nodes = RT.clusters()
    a_row, a_key, b_row, b_key = choose(schema, profile, nodes,
                                        argv.frm, argv.to)
    es = RT.edges(nodes, schema)
    legs = path_between(nodes, es, a_row["key"], b_row["key"])
    print_route(a_row, a_key, b_row, b_key, legs)

    man, path = build(schema, profile, a_row, a_key, b_row, b_key)
    print(f"\n  the walk, leg by leg:")
    for l in man["legs_out"]:
        print(f"     {l['kind']:6s} {l['length_m']:8,.1f} m  {l['note']}")
    print(f"     {'lift':6s} {man['rise_m']:8,.1f} m  landing "
          f"{man['from_landing']} -> {man['to_landing']}, "
          f"{man['ride']['seconds']:.1f} s at up to "
          f"{man['ride']['peak_m_s']:.2f} m/s (navigation.lift_ride_s, "
          f"capped by the Coriolis limit)")
    for l in man["legs_in"]:
        print(f"     {l['kind']:6s} {l['length_m']:8,.1f} m  {l['note']}")

    rows = []
    d = run(path, godot, engine_root, timeout=argv.timeout,
            verbose=argv.verbose)
    ok, why = verdict(d, man)
    print(f"\n  {'PASS' if ok else 'FAIL'}  THE ROUTE   {_fmt(d, man)}")
    for l in d.get("legs", ()):
        print(f"        {l.get('kind', '?'):6s} "
              f"{float(l.get('floor_m', 0)):8,.1f} m on the floor in "
              f"{l.get('frames')} frames"
              + (f"  ({l.get('note')})" if l.get("note") else ""))
    if not ok:
        print(f"        {why}")
    rows.append(("the route", ok, d))

    # CONTROL 1 -- THE CAR IS AT ANOTHER LANDING. The lobby, the spine and the
    # landing aperture are all exactly as they are in the subject; the only
    # difference is that there is no car floor behind the doorway. A route that
    # completes anyway is a route that was never using the lift.
    #
    # THE FURTHEST LANDING, and not the destination. `transit.gd` parks its car
    # at the far end of the ride, and a body that falls into a car standing at
    # its own destination has arrived by falling -- an outcome the control was
    # meant to exclude and cannot distinguish. Furthest in RADIUS from where the
    # body boards, excluding both ends of the ride: the car is somewhere else
    # entirely and the shaft below the doorway is empty.
    frm_r = float(man["landings"][man["from_landing"]]["walk_r_m"])
    park = max((i for i in range(len(man["landings"]))
                if i not in (man["from_landing"], man["to_landing"])),
               key=lambda i: abs(float(man["landings"][i]["walk_r_m"]) - frm_r))
    c1 = run(path, godot, engine_root, park=park, timeout=argv.timeout,
             verbose=argv.verbose)
    c1ok = ("error" not in c1 and c1.get("completed") != "true"
            and c1.get("boarded") != "true")
    print(f"\n  {'FIRED' if c1ok else 'DID NOT FIRE'}  control: the car parked "
          f"at landing {park} instead of {man['from_landing']}")
    if "error" in c1:
        print(f"        {c1['error']}\n{c1.get('tail', '')}")
    else:
        print(f"        the body walked the spine, reached the doorway and "
              f"fell {float(c1.get('fell_m', 0)):.2f} m into the shaft "
              f"(boarded={c1.get('boarded')}, completed={c1.get('completed')}, "
              f"stopped in `{c1.get('stopped_at')}`, "
              f"{float(c1.get('floor_m', 0)):,.1f} m on the floor, "
              f"{float(c1.get('air_m', 0)):.2f} m in the air, offfloor "
              f"{c1.get('offfloor')})")
    rows.append(("control: the car parked away", c1ok, c1))

    # CONTROL 2 -- THE LANDING DOORS ARE SEALED. `lift.lift_collision(
    # landings=False)`, the generator's own control: every aperture in the
    # landing wall is walled up. The body must be stopped at the threshold, on
    # the floor, in the lobby -- not fall, not arrive.
    c2 = run(path, godot, engine_root, seal="on", timeout=argv.timeout,
             verbose=argv.verbose)
    c2ok = ("error" not in c2 and c2.get("completed") != "true"
            and c2.get("boarded") != "true"
            and float(c2.get("air_m", 1.0)) < 0.5)
    print(f"\n  {'FIRED' if c2ok else 'DID NOT FIRE'}  control: every landing "
          f"aperture on the column sealed")
    if "error" in c2:
        print(f"        {c2['error']}\n{c2.get('tail', '')}")
    else:
        print(f"        the body walked {float(c2.get('floor_m', 0)):,.1f} m "
              f"and was stopped at the landing wall "
              f"{float(c2.get('door_gap_m', -1)):.2f} m from the car's own "
              f"floor, still on the floor "
              f"({float(c2.get('air_m', 0)):.2f} m in the air, offfloor "
              f"{c2.get('offfloor')}, completed={c2.get('completed')}, "
              f"stopped in `{c2.get('stopped_at')}`: "
              f"{str(c2.get('stopped_why')).replace('_', ' ')})")
    rows.append(("control: landing apertures sealed", c2ok, c2))

    bad = [n for n, o, _ in rows if not o]
    print("\n" + ("ALL GREEN" if not bad else "FAILED: " + "; ".join(bad)))
    return 0 if not bad else 1


def print_route(a_row, a_key, b_row, b_key, legs):
    print(f"\nTHE ROUTE, out of station/routes.py\n")
    print(f"  from  {a_key:24s} {a_row['sector']}/{a_row['ring']}/"
          f"{a_row['deck']} z={a_row['cz']:.0f} r={a_row['radius_m']:.2f} "
          f"landing {a_row['landing']}")
    print(f"  to    {b_key:24s} {b_row['sector']}/{b_row['ring']}/"
          f"{b_row['deck']} z={b_row['cz']:.0f} r={b_row['radius_m']:.2f} "
          f"landing {b_row['landing']}")
    if legs is None:
        print("  NO PATH between them in the circulation graph")
        return
    print()
    for i, l in enumerate(legs, 1):
        arrow = "" if l["a"] == l["b"] else f" -> {name(l['b'])}"
        print(f"     {i}. {l['kind']:6s} {name(l['a'])}{arrow}")
        print(f"        {l['why']}")


# ---------------------------------------------------------------------------
# REPORT AND SELF-TEST
# ---------------------------------------------------------------------------

def report(schema=None, profile=None):
    if schema is None:
        schema, profile = it.load()
    nodes = RT.clusters()
    ok, bad = endpoints(schema, profile, nodes)
    print(f"\nWHICH CLUSTERS A ROUTE CAN START OR END IN\n")
    print(f"  {len(ok)} of {len(nodes)} clusters; {len(bad)} cannot, and the "
          f"reasons are the finding:")
    why = {}
    for row, w in bad:
        k = ("no landing on the column" if "no landing" in w else
             "corridor and landing at different radii" if "apart" in w else
             "extending the corridor moves its room doors" if "moves" in w else
             "the deck was never exported" if "never built" in w else
             "no room on it got a door" if "got a door" in w else "other")
        why[k] = why.get(k, 0) + 1
    for k, n in sorted(why.items(), key=lambda x: -x[1]):
        print(f"     {n:3d}  {k}")
    print(f"\n  and `routes.py` grants every one of them a lift edge to its "
          f"ring's column.\n")
    a_row, a_key, b_row, b_key = choose(schema, profile, nodes)
    es = RT.edges(nodes, schema)
    print_route(a_row, a_key, b_row, b_key,
                path_between(nodes, es, a_row["key"], b_row["key"]))
    return ok, bad


def _selftest():
    ok = [0, 0]

    def check(nm, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + nm + (f"  {note}" if note
                                                         else ""))

    schema, profile = it.load()
    nodes = RT.clusters()
    print("\nTHE ROUTE, AND EVERY PIECE OF IT THAT CAN BE CHECKED OFFLINE\n")

    a_row, a_key, b_row, b_key = choose(schema, profile, nodes)
    es = RT.edges(nodes, schema)
    legs = path_between(nodes, es, a_row["key"], b_row["key"])
    kinds = [l["kind"] for l in (legs or ())]
    check("the route comes out of routes.py and crosses a lift",
          legs is not None and "lift" in kinds and "axial" in kinds
          and "ring" in kinds,
          f"{a_key} -> {b_key}: {' '.join(kinds)}")
    check("and it changes deck", a_row["deck"] != b_row["deck"],
          f"{a_row['sector']}/{a_row['ring']}/{a_row['deck']} -> "
          f"{b_row['sector']}/{b_row['ring']}/{b_row['deck']}")

    g = shaft(schema, profile, nodes, a_row["sector"])
    ang, z = column_address(nodes, a_row["sector"])
    check("the column is the one export_station builds",
          abs(g["angle_deg"] - ang) < 1e-9 and abs(g["z_m"] - z) < 1e-9
          and len(g["landings"]) == len(column_stack(schema, profile, nodes,
                                                     a_row["sector"])),
          f"{a_row['sector']} at {ang:.0f} deg, z={z:.0f}, "
          f"{len(g['landings'])} landings over {g['rise_m']:.1f} m of radius")

    # THE SEALED COLUMN IS THE SHIPPED ONE WITH ONE ARGUMENT CHANGED. Asserted
    # against `transit_runtime.static_collision` so this file's copy cannot
    # drift from the one the lift gate runs on.
    mv, mt, mg = column_collision(schema, profile, g, landings=True)
    tv, tt, tg = TR.static_collision(schema, profile, g)
    check("the column shell IS transit_runtime.static_collision",
          mt == tt and mv == tv and [n for n, _a, _b in mg]
          == [n for n, _a, _b in tg],
          f"{len(mt):,} triangles, {len(mg)} groups")
    sv, st, _sg = column_collision(schema, profile, g, landings=False)
    check("and sealing every landing takes triangles OUT of the aperture -- "
          "the control is the generator's own",
          len(st) != len(tt),
          f"{len(tt):,} triangles open, {len(st):,} sealed")

    # A BODY CROSSES THE LANDING THRESHOLD, AND WITH THE APERTURES SEALED IT
    # CANNOT. Cast along the way a body walks out of the lobby into the car, at
    # the height of its own chest.
    lg = g["landings"][a_row["landing"]]
    ls = g["landing_side"]
    p = L.place(g, [(0.0, lg["y_m"] + 1.0,
                     ls * (g["shaft"]["bore_hd"] + 0.5))])[0]
    into = tuple(-ls * c for c in (0.0, 0.0, 1.0))
    hit_open = C.cast(p, into, tv, tt)
    hit_seal = C.cast(p, into, sv, st)
    check("the landing aperture is a hole a body can walk through",
          hit_open is None or hit_open > 1.0,
          f"nothing within {hit_open if hit_open is None else round(hit_open, 3)} m")
    check("and sealed it is a wall -- the control fires in the geometry",
          hit_seal is not None and hit_seal < 1.0,
          f"stopped at {hit_seal and round(hit_seal, 3)} m")

    # THE JUNCTION APERTURE, AND THE CONTROL THAT SAYS IT IS THE THING DOING
    # THE WORK. Cast along the spine, into the ring corridor's wall.
    v, t, _gp, meta = cluster_collision(
        schema, profile, a_row["sector"], a_row["ring"], a_row["deck"],
        a_row["z"], a_row["spine_deg"], props=False)
    # THE CONTROL IS THE SAME CORRIDOR WITHOUT THE ONE DOOR. Not the corridor
    # `build_collision` happens to build: on this cluster the rooms-only arc
    # does not reach the transit angle at all, so a cast there would miss
    # everything and the control would "fire" on empty space. Same arc, same
    # phase, same room doors; the junction aperture alone removed.
    d1 = D.deck_plan(schema, profile, a_row["sector"], a_row["ring"],
                     a_row["deck"], a_row["z"], must_cover=a_row["spine_deg"])
    wv, wt, _wm = C.corridor_shell(schema, profile, a_row["sector"],
                                   a_row["ring"], degrees=d1["span"],
                                   start_deg=d1["lo"], radius_m=d1["radius"],
                                   z_offset=d1["cz"],
                                   doors=[x[1] for x in d1["rooms"]])
    eye = _at(meta["floor_r_m"] - 1.0, a_row["spine_deg"],
              meta["z_m"] - meta["half_w_m"] - 1.0)
    fwd = (0.0, 0.0, 1.0)
    hit_j = C.cast(tuple(eye), fwd, v, t)
    hit_w = C.cast(tuple(eye), fwd, wv, wt)
    check("the spine's junction door is a hole in the ring corridor's wall",
          hit_j is None or hit_j > 2.0,
          f"nothing within {hit_j if hit_j is None else round(hit_j, 3)} m of "
          f"the wall at {a_row['spine_deg']:.0f} deg")
    check("and without it the same wall is SOLID there -- the control",
          hit_w is not None and hit_w < 2.0,
          f"stopped at {hit_w and round(hit_w, 3)} m; that wall is what "
          f"deck.build_collision builds, and it is why no collision has ever "
          f"been built for a joined deck")

    # THE SPINE AND THE LOBBY ARE ONE FLOOR. Different generators, different
    # calls; the radius has to be the same number or a body crossing takes a
    # step no gate would see.
    z_end = TR.lobby_span(g)[1]
    _sv2, _st2, sm2 = spine(schema, profile, a_row["sector"], a_row["ring"],
                            meta["radius_m"], a_row["spine_deg"], z_end,
                            meta["z_m"] - meta["half_w_m"])
    _lv, _lt, lm = C.axial_shell(schema, profile, g["sector"], g["ring_index"],
                                 *TR.lobby_span(g), angle_deg=g["angle_deg"],
                                 radius_m=lg["floor_r_m"])
    check("the spine, the lobby and the ring corridor share one floor radius",
          abs(sm2["floor_r_m"] - lm["floor_r_m"]) < 1e-6
          and abs(sm2["floor_r_m"] - meta["floor_r_m"]) < 1e-6,
          f"corridor {meta['floor_r_m']:.4f} m, spine "
          f"{sm2['floor_r_m']:.4f} m, lobby {lm['floor_r_m']:.4f} m")
    check("and the spine actually spans the gap between them",
          sm2["length_m"] > it.AXIAL_SECTION_M,
          f"{sm2['length_m']:,.1f} m of axial corridor from the lobby at "
          f"z={z_end:.0f} to the ring corridor at z={meta['z_m']:.0f}")

    # THE WAYPOINTS STAY INSIDE THE CORRIDOR THEY ARE LAID IN. A body is steered
    # straight at the next one, so the chord between two of them has to sit
    # inside the corridor's own half width, or the route is a route through a
    # wall.
    lgs = legs_for(schema, profile, a_row, meta, g, a_key, outbound=True)
    worst = 0.0
    for l in lgs:
        if l["kind"] != "ring":
            continue
        for p0, p1 in zip(l["points"], l["points"][1:]):
            mid = [(p0[k] + p1[k]) / 2.0 for k in range(3)]
            worst = max(worst, meta["floor_r_m"]
                        - math.hypot(mid[0], mid[1]))
    check("a body steered waypoint to waypoint stays inside the corridor",
          worst < meta["half_w_m"] - 0.35,
          f"worst chord sags {worst * 1000:.0f} mm off the floor radius, "
          f"against a {meta['half_w_m']:.2f} m half width less a 0.35 m capsule")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def main(argv=None):
    # LINE BUFFERED. Each run in this gate is minutes long and its output is
    # normally redirected to a file, where Python's 4 KB block buffering hides
    # everything until the process exits -- which is what a hung run looks like
    # from outside.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--walk", action="store_true",
                    help="THE GATE: the route, walked, with both controls")
    ap.add_argument("--from", dest="frm", default=None)
    ap.add_argument("--to", dest="to", default=None)
    ap.add_argument("--godot", default=None)
    ap.add_argument("--engine-root", default=None)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    if a.walk:
        return gate(a)
    if a.build:
        schema, profile = it.load()
        nodes = RT.clusters()
        rows = choose(schema, profile, nodes, a.frm, a.to)
        build(schema, profile, *rows)
        return 0
    if a.report:
        report()
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
