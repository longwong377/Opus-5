#!/usr/bin/env python3
"""THE CIRCULATION GRAPH, EXPORTED INTO THE ENGINE -- and a body walking a route
the ENGINE chose.

WHAT WAS MISSING, MEASURED RATHER THAN SUMMARISED. `docs/MASTER-PLAN.md` §A0
records it in four words: **zero `Navigation*` in godot/**. Confirmed here --
`grep -rn Navigation godot/` returns 0 lines. Everything this project knows about
getting from one place to another is Python and runs offline:

    station/routes.py            96 z-cluster nodes, 249 edges, ONE component
    station/route_walk.py        the waypoints across each edge, and the
                                 `path_between` BFS that chooses a route
    station/roomnav.py           the way across a room past its furniture
    station/npc/navigation.py    20,871 nodes of cost model -- time and effort
    station/agenda.py            one resident's whole day, baked to a manifest

So an inhabitant could FOLLOW a route and could not CHOOSE one. `life.gd`'s
Commuter plays back `agenda.py`'s polyline; `route_test.gd` plays back
`route_walk.py`'s. Nothing in the engine can answer "how do I get to the Zocalo",
which is the question every other system after this one needs asked -- a job
loop, an incident, a person you follow, a map in the player's hand.

WHAT THIS DOES. It writes `station/generated/navgraph.json` -- the graph itself,
plus the waypoints that cross each edge -- and `godot/scripts/navgraph.gd` reads
it, searches it in GDScript, and hands back a polyline a body walks.

    nodes    routes.clusters()          one per z-cluster that carries a place
             + the spine of each deck   routes.edges()' own transit nodes
             + the column of each ring
    edges    routes.edges()             ring / axial / lift / spoke / trunk,
                                        with that module's own `built` and `why`
    legs     route_walk._arc_points     the ring arc, at RING_STEP_DEG's sagitta
             route_walk._line_points    the axial run, at AXIAL_STEP_M
             route_walk.door_tol_m      the doorway discipline

NOT ONE EDGE IS DECIDED HERE, AND THAT IS THE POINT. `routes.py` took a session
to make correct -- it went from 71 disconnected components to 1 -- and a second
opinion about what connects to what is the exact failure hard rule 4 exists for.
This module calls it and serialises the answer. The gate below then asserts, over
all 741 routable pairs, that the route GDScript finds is the route
`route_walk.path_between` finds, **node for node** -- so a graph that had been
quietly re-derived in the engine could not pass.

WHY A BAKED ARTEFACT AND NOT `NavigationServer3D`. The trade, stated once:

  * the station STREAMS. `stream.gd` keeps three cells resident out of 955 and
    frees the rest, so a navmesh built from what is in the tree can only path
    where the player already is. A graph that is DATA does not care what is
    loaded, and `--gate` proves that with a control rather than asserting it.
  * "up" in a ring corridor is radially inward -- a different vector at every
    angle (`npc/navigation.nav_from_ring_mesh` says so in as many words). One
    region per ring deck would classify the far side of its own arc as a wall.
  * a lift is a WAIT, not a distance. `npc/navigation.py` prices boarding at
    half a headway plus half a dwell each way; a navmesh has nowhere to put it.
  * CLAUDE.md's own architecture: *"Heavy content generation happens offline in
    Python -- schema -> meshes, collision, navmesh -- deterministic and
    unit-testable without an engine at all. The runtime consumes committed
    data."*

WHAT WOULD MAKE ME PICK THE OTHER ONE: local avoidance between moving bodies,
and pathing round furniture that moves. Neither is a station-scale question and
`roomnav.py` already answers the static case offline. When two hundred people
have to flow round each other in one concourse, `NavigationServer3D` with
`NavigationAgent3D` avoidance is the right tool for the last thirty metres --
underneath this graph, not instead of it.

Run:
    python3 station/navgraph_export.py --write     # the artefact (endpoints: ~150 s)
    python3 station/navgraph_export.py --report    # what it holds
    python3 station/navgraph_export.py --gate      # THE GATE: 741 pairs + a walk
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import collision as C                                            # noqa: E402
import deck as D                                                 # noqa: E402
import directory as DIR                                          # noqa: E402
import interior as it                                            # noqa: E402
import routes as RT                                              # noqa: E402
import route_walk as RW                                          # noqa: E402
import walkable as W                                             # noqa: E402

OUT = os.path.join(ROOT, "station/generated/navgraph.json")
WALK_OUT = os.path.join(ROOT, "station/generated/scene/navwalk")

# The artefact's own version. Bumped when the SHAPE changes, so `navgraph.gd`
# refusing an old file is a clear failure rather than a wrong route.
VERSION = 1

# How far past the ring corridor's wall a body is aimed before it turns down the
# axial spine -- `route_walk.AIM_M`, imported rather than restated, because a
# waypoint IN a junction is a waypoint whose next leg meets the jamb.
AIM_M = RW.AIM_M


# ---------------------------------------------------------------------------
# 1.  THE GRAPH
# ---------------------------------------------------------------------------

def _nid(k):
    """A node id a human can read in a log and a machine can key on.

    `routes.py`'s node is a TUPLE and JSON has no tuples, so it has to become a
    string somewhere. Doing it in one function means the engine and the gate
    agree about the spelling by construction rather than by discipline.
    """
    if k[0] == "spine":
        return f"spine:{k[1]}/{k[2]}/{k[3]}"
    if k[0] == "column":
        return f"column:{k[1]}/{k[2]}@{k[3]:.0f}"
    return f"cluster:{k[0]}/{k[1]}/{k[2]}@{k[3]:.0f}"


def _at(radius, angle_deg, z):
    return list(RW._at(radius, angle_deg, z))


def graph(schema=None, profile=None, quiet=True):
    """`routes.py`'s network, plus the geometry that crosses each edge.

    THE TOPOLOGY AND THE GEOMETRY COME FROM DIFFERENT FUNCTIONS AND THAT IS
    DELIBERATE. `routes.edges()` answers "does this connect", over all 96
    clusters. `route_walk.endpoints()` answers "can a body actually start or
    finish here", and rejects 57 of the 96 for four separate reasons -- no
    landing on the column, the landing at a different radius from the corridor,
    extending the corridor moves the room doors, the deck was never exported.
    Both go in. A node with no geometry is still a node: the graph is still
    connected through it, and the artefact carries `walkable:false` plus the
    refusal `endpoints` gave, so the engine knows the difference between "there
    is no route" and "there is a route nobody has built the floor for yet".
    """
    schema, profile = RT.station(schema, profile)
    t0 = time.time()
    nodes = RT.clusters()
    es = RT.edges(nodes, schema, profile=profile)
    ok, bad = RW.endpoints(schema, profile, nodes)
    if not quiet:
        print(f"  routes: {len(nodes)} clusters, {len(es)} edges, "
              f"{len(RT.components(nodes, es))} component(s); endpoints: "
              f"{len(ok)} walkable, {len(bad)} not  ({time.time() - t0:.0f} s)")

    prof = C.corridor_profile()
    rows = {r["key"]: r for r in ok}
    refused = {r["key"]: whynot for r, whynot in bad}

    # -- the node set: every endpoint of every edge, plus every cluster -------
    keys = list(sorted(nodes))
    allk = RT.all_nodes(nodes, es)
    order = sorted(allk, key=lambda k: (k[0] != "spine" and k[0] != "column",
                                        _nid(k)))
    index = {k: i for i, k in enumerate(order)}

    # -- the shafts, one per sector, for the column lobby --------------------
    # `route_walk.shaft` is `lift.shaft_geometry` at the sector's own transit
    # angle and the same z `tools/export_station.py` puts the column at -- so
    # the lobby a route ends at is the lobby in `column_<sector>.glb`. Cheap:
    # it reads the register and does no geometry.
    shafts = {}
    for sec in sorted({k[0] for k in keys}):
        try:
            shafts[sec] = RW.shaft(schema, profile, nodes, sec)
        except Exception as e:                                   # noqa: BLE001
            shafts[sec] = None
            if not quiet:
                print(f"  {sec}: no shaft ({e})")

    out_nodes = []
    for k in order:
        if k[0] == "spine":
            _t, sec, ring, dk = k
            out_nodes.append({"id": _nid(k), "kind": "spine", "sector": sec,
                              "ring": ring, "deck": dk,
                              "pos": [0.0, 0.0, 0.0], "places": []})
        elif k[0] == "column":
            _t, sec, ring, z = k
            g = shafts.get(sec)
            ang = RT.transit_angle(sec, nodes)
            r = 0.0
            if g is not None and g.get("landings"):
                r = float(g["landings"][0]["floor_r_m"])
            out_nodes.append({"id": _nid(k), "kind": "column", "sector": sec,
                              "ring": ring, "z": z, "angle_deg": ang,
                              "pos": _at(r, ang, z), "places": []})
        else:
            sec, ring, dk, z = k
            n = nodes[k]
            row = rows.get(k)
            rec = {"id": _nid(k), "kind": "cluster", "sector": sec,
                   "ring": ring, "deck": dk, "z": z,
                   "places": list(n["places"]),
                   "walkable": row is not None,
                   "pos": [0.0, 0.0, float(z)]}
            if row is None:
                rec["why_not"] = refused.get(k, "no endpoints row")
            else:
                fr = row["radius_m"] - prof["floor_y"]
                hw = prof["half_w"]
                cz = row["cz"]
                ang = row["spine_deg"]
                rec.update({
                    "radius_m": row["radius_m"], "floor_r_m": round(fr, 4),
                    "half_w_m": round(hw, 4), "cz": cz, "spine_deg": ang,
                    "z_col": row["z_col"], "landing": row["landing"],
                    "junction": _at(fr, ang, cz),
                    "pos": _at(fr, ang, cz),
                    "legs": {}, "axial": [], "lobby_run": [],
                })
                # THE RING LEG, per place: the arc from that place's door round
                # to the deck's transit angle. `route_walk._arc_points` at
                # `RING_STEP_DEG`'s sagitta -- 76 mm at r = 500 m, inside the
                # corridor's own half width by an order of magnitude.
                for place, door_deg in row["doors"]:
                    arc = RW._arc_points(fr, door_deg, ang, cz)
                    rec["legs"][place] = {
                        "door_deg": door_deg,
                        "ring": [list(p) for p in arc],
                        "ring_m": round(sum(math.dist(a, b)
                                            for a, b in zip(arc, arc[1:])), 3),
                    }
                # ONTO THE SPINE, TOWARD THE COLUMN. The aim point is
                # `route_walk.legs_for`'s: the junction, then a point AIM_M clear
                # of the ring corridor's own wall on the spine's centre line. A
                # body that turns while standing in a junction meets the jamb;
                # one aimed at a point beyond it walks a straight line through.
                #
                # THE SIDE DEPENDS ON WHERE IT IS GOING, WHICH IS WHY THIS IS ONE
                # RUN PER DESTINATION RATHER THAN ONE PER CLUSTER. The first
                # version stored a single `[junction, aim]` leg per cluster,
                # aimed at the column -- so a route between two clusters on ONE
                # deck stepped 3.08 m the WRONG WAY down the spine before setting
                # off, on yellow/0/0 where the column is at z=160 and the
                # destination at z=490. Simulated against the artefact before any
                # engine run, which is what caught it.
                g = shafts.get(sec)
                if g is not None:
                    lg = g["landings"][row["landing"]]
                    import transit_runtime as TR                  # noqa: PLC0415
                    stand = list(TR.lobby_stand(g, lg))
                    s_col = -1.0 if cz > row["z_col"] else 1.0
                    aim_col = _at(fr, ang, cz + s_col * (hw + AIM_M))
                    rec["lobby_run"] = ([rec["junction"]]
                                        + [list(p) for p in
                                           RW._line_points(aim_col, stand)])
                    rec["lobby"] = stand
            out_nodes.append(rec)

    # -- the edges, exactly as `routes.edges()` returns them ------------------
    out_edges = []
    for e in es:
        a, b = index[e["a"]], index[e["b"]]
        out_edges.append({"a": a, "b": b, "kind": e["kind"],
                          "built": bool(e["built"]),
                          "length_m": round(float(e["length_m"]), 3),
                          "why": e["why"]})

    # -- the axial runs between two clusters on ONE spine ---------------------
    # A SPINE IS A CORRIDOR AND NOT A POINT, which is why `routes.py` models it
    # as a SELF-LOOP: passing through the node is what traverses it. So the run
    # between two clusters on one deck depends on WHICH TWO, and it is laid here
    # per ordered pair rather than left for the engine to interpolate. Four
    # clusters is at most twelve runs a deck; the whole station is 62.
    by_spine = {}
    for k in keys:
        row = rows.get(k)
        if row is None:
            continue
        by_spine.setdefault(("spine",) + k[:3], []).append(k)
    for sp, members in by_spine.items():
        rec = out_nodes[index[sp]]
        rec["runs"] = {}
        rec["radius_m"] = out_nodes[index[members[0]]]["radius_m"]
        rec["spine_deg"] = out_nodes[index[members[0]]]["spine_deg"]
        pos = None
        for ka in members:
            na = out_nodes[index[ka]]
            pos = na["junction"] if pos is None else pos
            for kb in members:
                if ka == kb:
                    continue
                nb = out_nodes[index[kb]]
                # JUNCTION TO JUNCTION, with an aim point AIM_M past each one on
                # the side the OTHER cluster is on. Both aims are decided per
                # ordered pair for the reason recorded above.
                s = 1.0 if nb["cz"] > na["cz"] else -1.0
                aim_a = _at(na["floor_r_m"], na["spine_deg"],
                            na["cz"] + s * (na["half_w_m"] + AIM_M))
                aim_b = _at(nb["floor_r_m"], nb["spine_deg"],
                            nb["cz"] - s * (nb["half_w_m"] + AIM_M))
                run = ([na["junction"]]
                       + [list(p) for p in RW._line_points(aim_a, aim_b)]
                       + [nb["junction"]])
                rec["runs"][f"{_nid(ka)}|{_nid(kb)}"] = run
        rec["pos"] = pos or [0.0, 0.0, 0.0]

    man = {
        "kind": "navgraph",
        "version": VERSION,
        "built_from": ("station/routes.py (topology) + station/route_walk.py "
                       "(endpoints and waypoints)"),
        "authority": ("routes.clusters/edges decides what connects to what; "
                      "route_walk.endpoints decides where a body can start and "
                      "finish; route_walk._arc_points/_line_points lay every "
                      "waypoint. Nothing in this file or in navgraph.gd "
                      "re-derives any of it."),
        "ring_step_deg": RW.RING_STEP_DEG,
        "axial_step_m": RW.AXIAL_STEP_M,
        "waypoint_tol_m": RW.WAYPOINT_TOL_M,
        "door_tol_m": round(RW.door_tol_m(), 4),
        "capsule_r_m": RW.CAPSULE_R_M,
        "counts": {
            "clusters": len(keys),
            "walkable_clusters": len(ok),
            "nodes": len(out_nodes),
            "edges": len(out_edges),
            "built_edges": sum(1 for e in out_edges if e["built"]),
            "components": len(RT.components(nodes, es)),
            "places": sum(len(n["places"]) for n in out_nodes),
        },
        "nodes": out_nodes,
        "edges": out_edges,
    }
    man["digest"] = digest(man)
    return man, nodes, es, ok, bad


def digest(man):
    """blake2b over the topology alone -- ids, edge ends and kinds.

    THE TOPOLOGY AND NOT THE WAYPOINTS, deliberately. This is the number
    `--gate` compares a committed artefact against a freshly derived
    `routes.edges()`, and it has to be able to do that WITHOUT paying
    `endpoints`' 150 seconds -- otherwise the cheap check is not cheap and gets
    skipped. A waypoint that moved is caught by the walk; an edge that appeared
    or vanished is caught by this.
    """
    h = hashlib.blake2b(digest_size=16)
    for n in man["nodes"]:
        h.update(f"{n['id']}|{n['kind']}\n".encode())
    for e in man["edges"]:
        h.update(f"{man['nodes'][e['a']]['id']}>{man['nodes'][e['b']]['id']}"
                 f"|{e['kind']}|{int(e['built'])}\n".encode())
    return h.hexdigest()


def topology_digest(schema=None, profile=None):
    """The same number, from `routes.py` alone. ~11 s, no `endpoints`."""
    schema, profile = RT.station(schema, profile)
    nodes = RT.clusters()
    es = RT.edges(nodes, schema, profile=profile)
    allk = RT.all_nodes(nodes, es)
    order = sorted(allk, key=lambda k: (k[0] != "spine" and k[0] != "column",
                                        _nid(k)))
    h = hashlib.blake2b(digest_size=16)
    for k in order:
        kind = ("spine" if k[0] == "spine"
                else "column" if k[0] == "column" else "cluster")
        h.update(f"{_nid(k)}|{kind}\n".encode())
    for e in es:
        h.update(f"{_nid(e['a'])}>{_nid(e['b'])}|{e['kind']}"
                 f"|{int(bool(e['built']))}\n".encode())
    return h.hexdigest(), nodes, es


def write(path=OUT, quiet=False):
    man, _n, _e, _ok, _bad = graph(quiet=quiet)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(man, f, separators=(",", ":"))
    if not quiet:
        c = man["counts"]
        print(f"  wrote {os.path.relpath(path, ROOT)} -- {c['nodes']} nodes, "
              f"{c['edges']} edges ({c['built_edges']} built), "
              f"{c['walkable_clusters']}/{c['clusters']} clusters with "
              f"waypoints, {c['components']} component(s), "
              f"{os.path.getsize(path) / 1e6:.2f} MB, digest {man['digest']}")
    return man


# ---------------------------------------------------------------------------
# 2.  THE PAIRS -- what the engine has to agree with
# ---------------------------------------------------------------------------

def pairs(nodes=None, es=None, ok=None, schema=None, profile=None):
    """Every ordered pair of walkable clusters, and Python's own route for it.

    741 pairs over 39 walkable clusters, which is `route_walk`'s own
    denominator. Each row is (from_id, to_id, [node ids along the way]) -- the
    SHAPE of the route rather than its length, because two searches can agree
    about how many hops a journey takes and disagree about which corridor it
    goes down.
    """
    schema, profile = RT.station(schema, profile)
    if nodes is None:
        nodes = RT.clusters()
    if es is None:
        es = RT.edges(nodes, schema, profile=profile)
    if ok is None:
        ok, _bad = RW.endpoints(schema, profile, nodes)
    keys = [r["key"] for r in ok]
    out = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            legs = RW.path_between(nodes, es, a, b)
            if legs is None:
                out.append((_nid(a), _nid(b), None))
                continue
            seq = [_nid(legs[0]["a"])]
            for l in legs:
                if _nid(l["b"]) != seq[-1]:
                    seq.append(_nid(l["b"]))
            out.append((_nid(a), _nid(b), seq))
    return out


# ---------------------------------------------------------------------------
# 3.  THE WALK -- geometry for a body to cross two z-clusters on
# ---------------------------------------------------------------------------
# WHY THIS BUILDS ITS OWN SHELLS RATHER THAN USING THE COMMITTED ONES, and it is
# a finding rather than a preference.
#
# `station/generated/scene/agenda/commute.json` is the L3 cross-deck commute and
# every piece of it is on disk. Measured against today's generators it is STALE
# by 57 metres: it puts red/1/6's ring corridor at z = 6654.48 and
# `deck.deck_plan` puts it at 6711.48 today, because session 4k's tiling changed
# `deck.room_interior_half_m` from the one-bay clamp to the full footprint and
# `deck.corridor_z_m` is that number plus a wall. The shipped whole-deck
# collision `blue_0_0_col.glb` has the same problem -- its corridor is at
# z = 7120.9 and today's plan says 7186.5.
#
# So a route laid from TODAY's graph on THOSE shells is a route 57-66 m off the
# floor, and a body walking it would fall. Both shells are rebuilt here from the
# same `route_walk` calls the graph's waypoints came from, which is the only
# arrangement in which "the graph agrees with the floor" is true by construction
# rather than by luck.

def spine_clash(schema, profile, sector, ring, deck, spine_deg, radius_m,
                z0, z1):
    """Rooms an axial run at `spine_deg` would pass through, z0 to z1.

    THE SPINE IS A CORRIDOR AT ONE ANGLE AND THE ROOMS ARE AT THEIRS, so this is
    a two-axis test and doing it on z alone is what made the first run of this
    gate stop dead 8.6 m along. `routes.py` grants a `ring` edge from every
    cluster to its deck's spine and an `axial` self-loop on that spine -- both
    correct as TOPOLOGY -- and `route_walk` lays the spine at the sector's
    transit angle because its own routes run to the transit COLUMN, which sits
    beyond the last cluster. Between two clusters ON one deck the run instead
    passes the whole length of the far cluster's room, and whether that matters
    is an angle question.

    Measured, and this is the finding: on `yellow/0/0` the transit angle is 0 and
    `fusion_core`'s shell is a bay centred on 0 spanning z 310.9 to 489.1, so the
    only axial run `route_walk`'s model can lay between `reactor_hall` and
    `fusion_core` goes straight into it. The body walked its 54 m of ring arc,
    turned down the spine, and stopped at z = 310.7 against the room's own outer
    wall -- correctly, on geometry that is correct. What was wrong was the choice
    of pair.

    Room size is `deck.room_half_w_m` and `deck.room_axial_half_m`, which is what
    `deck.room_shell_for` builds the shell from -- one bay, not the register's
    full footprint. Asked of those functions rather than of the footprint,
    because `rooms.tiling` instances the RENDER along the footprint and the
    collision shell is still a bay.
    """
    hits = []
    for q in DIR.PLACES:
        if (q.get("sector"), q.get("ring"), q.get("deck")) != (sector, ring,
                                                               deck):
            continue
        h = D.room_axial_half_m(schema, profile, q)
        if not (q["z_m"] + h > z0 and q["z_m"] - h < z1):
            continue
        # The room's arc, in degrees at the corridor's own radius, plus the
        # spine's half width -- a corridor is not a line.
        half_deg = (math.degrees(D.room_half_w_m(schema, profile, q) / radius_m)
                    + math.degrees(C.corridor_profile()["half_w"] / radius_m))
        d = abs(((q["angle_deg"] - spine_deg) + 180.0) % 360.0 - 180.0)
        if d <= half_deg:
            hits.append((q["key"], round(d, 2), round(half_deg, 2)))
    return hits


def walk_pair(schema, profile, nodes, ok):
    """The two z-clusters the walk crosses, chosen FROM THE DATA.

    Two clusters on ONE deck cross a z-cluster boundary with no lift in between,
    which is what makes this walk a test of the GRAPH rather than a second test
    of `transit.gd` -- the ride already has one (`transit_runtime --ride`) and
    the cross-deck half of this gate is the 741 pairs above.

    Among every adjacent pair on every deck that carries two, the closest along
    the axis WHOSE SPINE HAS SOMEWHERE TO RUN -- `spine_clash` above, and the
    reason is recorded there. If none is clear the error names every pair and
    what blocked it, because "no route is walkable on one deck" is a fact about
    the station worth reading rather than a gate that mysteriously skipped.
    """
    per = {}
    for r in ok:
        per.setdefault((r["sector"], r["ring"], r["deck"]), []).append(r)
    cand = [(k, sorted(v, key=lambda r: r["cz"]))
            for k, v in sorted(per.items()) if len(v) > 1]
    if not cand:
        raise ValueError("no deck carries two walkable z-clusters")
    hw = C.corridor_profile()["half_w"]
    best, blocked = None, []
    for k, rows in cand:
        for a, b in zip(rows, rows[1:]):
            hits = spine_clash(schema, profile, k[0], k[1], k[2],
                               a["spine_deg"], a["radius_m"],
                               a["cz"] + hw, b["cz"] - hw)
            if hits:
                blocked.append((a["places"], b["places"], hits))
                continue
            span = abs(b["cz"] - a["cz"])
            if best is None or span < best[0]:
                best = (span, a, b)
    if best is None:
        raise ValueError("every same-deck pair's spine runs through a room: "
                         + "; ".join(f"{x[0]}->{x[1]} hits {x[2]}"
                                     for x in blocked))
    return best[1], best[2]


def build_walk(schema, profile, a_row, b_row, out_dir=WALK_OUT, quiet=False):
    """Two cluster shells and the axial spine between them, plus a manifest.

    EVERY PIECE IS `route_walk`'s OWN BUILDER. `cluster_collision` is the
    station's cluster shell with the junction aperture its deck's spine needs --
    the one `deck.build_collision` has no argument for -- and `spine` is
    `collision.axial_shell` at the sector's transit angle and the deck's own
    corridor radius. Nothing here authors geometry.
    """
    os.makedirs(out_dir, exist_ok=True)
    files = {}
    metas = {}
    for tag, row, side in (("a", a_row, +1.0), ("b", b_row, -1.0)):
        v, t, g, m = RW.cluster_collision(
            schema, profile, row["sector"], row["ring"], row["deck"],
            row["z"], row["spine_deg"], side=side)
        obj = _write_obj(out_dir, f"cluster_{tag}_col", v, t, g)
        files[f"cluster_{tag}"] = _glb(obj)
        metas[tag] = m
        if not quiet:
            print(f"  cluster_{tag}: {row['sector']}/{row['ring']}/"
                  f"{row['deck']} z={row['z']:.0f}  cz={m['z_m']:.2f}  "
                  f"r={m['floor_r_m']:.3f}  {len(t):,} tri  "
                  f"rooms={[r['key'] for r in m['rooms']]}")

    # The spine, from the near face of one cluster's corridor to the near face
    # of the other's -- the two junction apertures the shells above carry.
    ma, mb = metas["a"], metas["b"]
    z0 = ma["z_m"] + ma["half_w_m"]
    z1 = mb["z_m"] - mb["half_w_m"]
    sv, st, _sm = RW.spine(schema, profile, a_row["sector"], a_row["ring"],
                           ma["radius_m"], a_row["spine_deg"], z0, z1)
    obj = _write_obj(out_dir, "spine_col", sv, st, [("spine", 0, len(st))])
    files["spine"] = _glb(obj)
    if not quiet:
        print(f"  spine: {a_row['spine_deg']:.0f} deg, z {z0:.1f} -> {z1:.1f} "
              f"({z1 - z0:.1f} m), {len(st):,} tri")

    # WHERE THE BODY STARTS, and it is the same function `walkable.py --deck`
    # and `agenda.py` use: the free floor of the room, nudged off its furniture.
    a_place = a_row["doors"][0][0]
    b_place = b_row["doors"][0][0]
    spawn = list(C.stand_at(ma, dict(a_row["doors"])[a_place]))
    man = {
        "kind": "navwalk",
        "collision_glbs": [files["cluster_a"], files["spine"],
                           files["cluster_b"]],
        "deck": f"{a_row['sector']}/{a_row['ring']}/{a_row['deck']}",
        "from": {"place": a_place, "cluster": _nid(a_row["key"]),
                 "z": a_row["z"], "cz": ma["z_m"]},
        "to": {"place": b_place, "cluster": _nid(b_row["key"]),
               "z": b_row["z"], "cz": mb["z_m"]},
        "spawn": spawn,
        "spine_deg": a_row["spine_deg"],
        "capsule_r_m": RW.CAPSULE_R_M,
        "waypoint_tol_m": RW.WAYPOINT_TOL_M,
        "door_tol_m": round(RW.door_tol_m(), 4),
        "arrived_m": W.ARRIVED_M,
        "omega_rad_s": schema["station"]["rotation"]["omega_rad_s"]["value"],
        "doors": [{"key": r["key"], "group": f"doorpanel_{r['key']}",
                   "at": _at(m["floor_r_m"], r["door_deg"], m["z_m"])}
                  for m in (ma, mb) for r in m["rooms"]],
        "target": _at(mb["floor_r_m"], dict(b_row["doors"])[b_place],
                      mb["z_m"]),
    }
    path = os.path.join(out_dir, "navwalk.json")
    with open(path, "w") as f:
        json.dump(man, f, indent=1)
    return man, path


def _write_obj(out_dir, stem, verts, tris, groups):
    path = os.path.join(out_dir, stem + ".obj")
    with open(path, "w") as f:
        f.write(f"o {stem}\n")
        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        at = 0
        for nm, lo, hi in groups:
            if lo > at:
                f.write("g rest\n")
                for a, b, c in tris[at:lo]:
                    f.write(f"f {a + 1} {b + 1} {c + 1}\n")
            f.write(f"g {nm}\n")
            for a, b, c in tris[lo:hi]:
                f.write(f"f {a + 1} {b + 1} {c + 1}\n")
            at = hi
        if at < len(tris):
            f.write("g rest\n")
            for a, b, c in tris[at:]:
                f.write(f"f {a + 1} {b + 1} {c + 1}\n")
    return path


def _glb(obj_path):
    """OBJ -> GLB through `station/export_gltf.py`, one node per group name."""
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


# ---------------------------------------------------------------------------
# 4.  THE RESIDENT
# ---------------------------------------------------------------------------

def resident_for(place, limit=160):
    """A NAMED person the generator would have put in that room anyway.

    FROM THE POOL THE ROOM IS CAST FROM, which is `agenda.candidates`' rule:
    `populace.populate` fills a place with `resident.roster`, which draws on
    `resident.affiliates`, which scans `resident.pool_id(place, species, i)` in
    order. Walking the same stream means the person who walks this route is a
    person the station would have put there, not a probe id invented for a gate.

    AND THE ONE WHOSE JOB IT IS, PREFERRED OVER THE ONE WHO HAPPENS TO BE IN THE
    ROOM. `pool_id` affiliates an id with a place; `resident()` then derives that
    person's role, home and job independently, so the first name out of
    `fusion_core`'s pool is a Centauri financier who works in a drum office and
    is merely visiting. A gate that says "a named resident walks to their post"
    has to pick somebody whose post it is. `why` records which rule matched, so
    a fallback cannot be read as the strong case.
    """
    import npc.resident as RS                                     # noqa: PLC0415
    import npc.schedule as SC                                     # noqa: PLC0415
    best = None
    for rule in ("job", "home", "any"):
        for species in sorted(SC.STATION_MIX):
            if species in SC.SPECIES_WITHOUT_NAMES:
                continue
            for i in range(limit):
                try:
                    res = RS.resident(RS.pool_id(place, species, i, "b5"),
                                      species)
                except Exception:                                 # noqa: BLE001
                    continue
                if not getattr(res, "name", ""):
                    continue
                if rule == "job" and res.job == place:
                    return res, f"works at {place}"
                if rule == "home" and res.home == place:
                    return res, f"lives in {place}"
                if rule == "any":
                    return res, f"is in {place}'s pool"
                best = best or res
    if best is not None:
        return best, f"is in {place}'s pool"
    raise ValueError(f"no named resident in {place}'s pool")


# ---------------------------------------------------------------------------
# 5.  THE GATE
# ---------------------------------------------------------------------------

def _godot():
    return W.godot_binary()


def run_engine(args, timeout=900, verbose=False):
    godot = _godot()
    if godot is None:
        return None, "no godot binary under /home/user/godot-build"
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "--script", "res://scripts/navwalk.gd", "--"] + list(args)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout} s"
    out = (p.stdout or "") + (p.stderr or "")
    if verbose:
        print(out)
    return out, ""


def _verdict(out, tag):
    """The engine's report line for `tag`, or "".

    THE TAG HAS TO BE THE WHOLE TAG, and this is a bug the gate caught on
    itself. `NAVWALK DIRECTOR same=1 ...` was added as a second line in the walk
    run and it starts with `NAVWALK`, so a prefix match handed the walk's own
    parser the Director's line -- every field came back `None` and four checks
    failed on a run whose walk had actually arrived. So the token after the tag
    must be a `key=value`, which a second tag word is not.
    """
    for line in (out or "").splitlines():
        if not line.startswith(tag):
            continue
        rest = line[len(tag):].strip().split(" ", 1)[0]
        if "=" in rest:
            return line
    return ""


def _kv(line):
    d = {}
    for m in re.finditer(r"(\w+)=([^\s]+)", line):
        d[m.group(1)] = m.group(2)
    return d


def gate(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default=OUT)
    ap.add_argument("--no-walk", action="store_true",
                    help="the graph half only -- no engine geometry build")
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild the walk's collision shells (~2 min)")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)

    fails = []

    def check(ok, name, detail=""):
        print(f"{'PASS' if ok else 'FAIL'}  {name}"
              + (f"  -- {detail}" if detail else ""))
        if not ok:
            fails.append(name)
        return ok

    print("THE NAVIGATION GRAPH, IN THE ENGINE\n")

    # ---- 1. the artefact exists and still describes the code ---------------
    if not os.path.exists(a.graph):
        check(False, "the graph is on disk",
              f"{os.path.relpath(a.graph, ROOT)} is missing -- run --write")
        return 1
    man = json.load(open(a.graph))
    check(man.get("kind") == "navgraph" and man.get("version") == VERSION,
          "the artefact is a navgraph of this version",
          f"kind={man.get('kind')} version={man.get('version')}")

    t0 = time.time()
    dg, nodes, es = topology_digest()
    check(dg == man["digest"],
          "the committed graph is the graph routes.py builds TODAY",
          f"{man['digest']} vs {dg} ({time.time() - t0:.0f} s to re-derive)")
    check(man["counts"]["components"] == RT.TARGET_COMPONENTS,
          "the station is one foot-connected component",
          f"{man['counts']['components']} component(s)")

    # ---- 2. Python's own answer, for every pair ----------------------------
    schema, profile = RT.station()
    t0 = time.time()
    ok, bad = RW.endpoints(schema, profile, nodes)
    pr = pairs(nodes, es, ok)
    routable = [p for p in pr if p[2] is not None]
    print(f"      {len(routable)} of {len(pr)} pairs routable in Python "
          f"({time.time() - t0:.0f} s)")
    check(len(routable) == len(pr) and len(pr) > 0,
          "Python routes every pair of walkable clusters",
          f"{len(routable)}/{len(pr)}")

    ask = os.path.join(ROOT, "station/generated/scene/navwalk/pairs.json")
    os.makedirs(os.path.dirname(ask), exist_ok=True)
    with open(ask, "w") as f:
        json.dump([{"a": x[0], "b": x[1], "seq": x[2]} for x in pr], f)

    # ---- 3. the engine, on the same pairs ----------------------------------
    out, err = run_engine(["--pairs=" + ask, "--graph=" + a.graph],
                          verbose=a.verbose)
    if err:
        check(False, "the engine ran", err)
        return 1
    line = _verdict(out, "NAVGRAPH PAIRS")
    print(f"      {line}")
    kv = _kv(line)
    check(kv.get("routed") == kv.get("of") and int(kv.get("of", 0)) > 0,
          "the ENGINE routes every pair, at run time, in GDScript",
          f"{kv.get('routed')}/{kv.get('of')}")
    check(int(kv.get("mismatch", -1)) == 0,
          "every engine route is Python's route, NODE FOR NODE",
          f"{kv.get('mismatch')} disagreed")
    check(int(kv.get("crossdeck", 0)) > 0,
          "pairs that cross a deck boundary are among them",
          f"{kv.get('crossdeck')} cross a deck, {kv.get('crossring')} a ring, "
          f"{kv.get('crosssector')} a sector")

    line = _verdict(out, "NAVGRAPH WEIGHTED")
    print(f"      {line}")
    kvw = _kv(line)
    zero = sum(1 for e in man["edges"] if e["built"] and e["length_m"] <= 0.0)
    check(kvw.get("routed") == kv.get("of") and int(kvw.get("of", 0)) > 0,
          "the metre-weighted search routes them too",
          f"{kvw.get('routed')}/{kvw.get('of')}, differing from the hop search "
          f"on {kvw.get('differ')} -- AND THAT IS A STATEMENT ABOUT THE INPUT: "
          f"{zero} of {man['counts']['built_edges']} built edges carry "
          f"length_m 0.0, because routes.py answers 'does this connect' and "
          f"puts a real length only on its trunk edges. Weighting has almost "
          f"nothing to weigh until the exporter carries its own leg lengths "
          f"onto the edges")

    # ---- 4. the streaming property, and its control ------------------------
    line = _verdict(out, "NAVGRAPH STREAM")
    print(f"      {line}")
    kv = _kv(line)
    check(kv.get("resolved") == kv.get("of") and int(kv.get("of", 0)) > 0,
          "every walkable cluster resolves with NOTHING in the scene tree",
          f"{kv.get('resolved')}/{kv.get('of')}")
    check(kv.get("after") == kv.get("of"),
          "and the same after geometry is added and freed",
          f"{kv.get('after')}/{kv.get('of')}")
    check(kv.get("distinct") == kv.get("of"),
          "no two of them stand at the same point, so that question is real",
          f"{kv.get('distinct')} distinct positions over {kv.get('of')}")
    check(int(kv.get("control", 0)) < int(kv.get("of", 1)),
          "CONTROL: a residency-filtered graph loses most of the station",
          f"{kv.get('control')}/{kv.get('of')} resolve when only the "
          f"resident cell's nodes count")

    if a.no_walk:
        return _finish(fails)

    # ---- 5. a named resident walks a route the engine chose ----------------
    a_row, b_row = walk_pair(schema, profile, nodes, ok)
    wman_path = os.path.join(WALK_OUT, "navwalk.json")
    if a.rebuild or not os.path.exists(wman_path):
        print("\n  building the walk's collision (route_walk's own shells)")
        wman, wman_path = build_walk(schema, profile, a_row, b_row)
    else:
        wman = json.load(open(wman_path))
    missing = [p for p in wman["collision_glbs"] if not os.path.exists(p)]
    if missing:
        print("\n  collision shells missing -- rebuilding")
        wman, wman_path = build_walk(schema, profile, a_row, b_row)

    who, why = resident_for(wman["to"]["place"])
    print(f"\n  {who.name} -- {who.species} {who.role}, {why}, {who.origin} --"
          f" walks from {wman['from']['place']} ({wman['from']['cluster']}) "
          f"to {wman['to']['place']} ({wman['to']['cluster']})")

    out, err = run_engine(["--walk=" + wman_path, "--graph=" + a.graph,
                           "--who=" + who.name,
                           "--from=" + wman["from"]["place"],
                           "--to=" + wman["to"]["place"]],
                          timeout=1800, verbose=a.verbose)
    if err:
        check(False, "the walk ran", err)
        return _finish(fails)
    line = _verdict(out, "NAVWALK")
    print(f"      {line}")
    kv = _kv(line)
    check(kv.get("found") == "1",
          "the route was found AT RUN TIME, in GDScript, on the engine graph",
          f"hops={kv.get('hops')} kinds={kv.get('kinds')}")
    dline = _verdict(out, "NAVGRAPH DIRECTOR")
    dkv = _kv(dline)
    check(dkv.get("same") == "1" and int(dkv.get("pts", 0)) > 1,
          "and `life.gd`'s Director returns the SAME polyline, point for point",
          f"{dkv.get('via')} waypoints through Director.route_between against "
          f"{dkv.get('pts')} the body walks")
    check(kv.get("crossed") == "1",
          "it crosses a z-cluster boundary",
          f"{kv.get('from')} -> {kv.get('to')}")
    reached = float(kv.get("reached_m", 1e9))
    check(reached <= float(wman["arrived_m"]),
          "the body ARRIVED", f"{reached:.2f} m from its target, "
          f"against {wman['arrived_m']} m")
    floor_m = float(kv.get("floor_m", 0.0))
    route_m = float(kv.get("route_m", 0.0))
    check(floor_m >= 0.9 * route_m and route_m > 100.0,
          "and covered the route ON THE FLOOR",
          f"{floor_m:.1f} m of floor over a {route_m:.1f} m route, "
          f"off the floor for {kv.get('offfloor')} frames")

    # ---- 6. the controls ---------------------------------------------------
    print("\n  CONTROLS -- each of these must FAIL\n")

    # 6a. THE GRAPH IS NOT SAYING YES TO EVERYTHING. Marking every `lift` edge
    #     unbuilt is what the station was before `station/lift.py` existed:
    #     `routes.py` records that state in its own `why` -- *"no lift, stair or
    #     shaft exists anywhere in the project"* -- and the component count it
    #     produced was 71. If the pair sweep still routed 741 pairs with the
    #     lifts gone, it would be measuring something other than the graph.
    out, err = run_engine(["--pairs=" + ask, "--graph=" + a.graph,
                           "--drop-edge=lift"], verbose=a.verbose)
    line = _verdict(out, "NAVGRAPH PAIRS")
    kv = _kv(line)
    print(f"      {line}")
    check(int(kv.get("routed", 10 ** 9)) < len(pr) // 2,
          "CONTROL: with no lift edges most pairs have no route",
          f"{kv.get('routed')}/{kv.get('of')} still route")

    # 6b. The cluster reaches its deck's spine by exactly one `ring` edge, so
    #     the walk's own route cannot survive losing that kind.
    out, err = run_engine(["--walk=" + wman_path, "--graph=" + a.graph,
                           "--who=" + who.name,
                           "--from=" + wman["from"]["place"],
                           "--to=" + wman["to"]["place"],
                           "--drop-edge=ring"], timeout=1800,
                          verbose=a.verbose)
    line = _verdict(out, "NAVWALK")
    kv = _kv(line)
    print(f"      {line}")
    check(kv.get("found") == "0",
          "CONTROL: with the ring edge dropped there is NO route",
          "a cluster reaches its deck's spine by exactly one edge")

    # 6c. And the body has to be the thing that covers the ground.
    out, err = run_engine(["--walk=" + wman_path, "--graph=" + a.graph,
                           "--who=" + who.name,
                           "--from=" + wman["from"]["place"],
                           "--to=" + wman["to"]["place"],
                           "--no-steer"], timeout=1800, verbose=a.verbose)
    line = _verdict(out, "NAVWALK")
    kv = _kv(line)
    print(f"      {line}")
    check(float(kv.get("reached_m", 0.0)) > float(wman["arrived_m"]),
          "CONTROL: a body that is not steered does not arrive",
          f"{kv.get('reached_m')} m from its target, against "
          f"{wman['arrived_m']} m")

    return _finish(fails)


def _finish(fails):
    print()
    if fails:
        print(f"{len(fails)} FAILED: {', '.join(fails)}")
        return 1
    print("the engine has the graph, and it answered every question asked of it")
    return 0


# ---------------------------------------------------------------------------
# 6.  REPORT
# ---------------------------------------------------------------------------

def report(path=OUT):
    if not os.path.exists(path):
        print(f"no graph at {os.path.relpath(path, ROOT)} -- run --write")
        return 1
    man = json.load(open(path))
    c = man["counts"]
    print(f"{os.path.relpath(path, ROOT)}  v{man['version']}  "
          f"{man['digest']}\n")
    print(f"  {c['nodes']} nodes  {c['edges']} edges "
          f"({c['built_edges']} built)  {c['components']} component(s)")
    print(f"  {c['walkable_clusters']} of {c['clusters']} clusters carry "
          f"waypoints; {c['places']} places attach\n")
    kinds = {}
    for e in man["edges"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    print("  edges by kind: "
          + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    nk = {}
    for n in man["nodes"]:
        nk[n["kind"]] = nk.get(n["kind"], 0) + 1
    print("  nodes by kind: "
          + ", ".join(f"{k} {v}" for k, v in sorted(nk.items())))
    print("\n  clusters with NO waypoints, and the reason `route_walk."
          "endpoints` gave:")
    seen = {}
    for n in man["nodes"]:
        if n["kind"] == "cluster" and not n.get("walkable", False):
            w = n.get("why_not", "?")
            seen.setdefault(w.split("--")[0].strip()[:64], []).append(n["id"])
    for w, ids in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        print(f"   {len(ids):>3}  {w}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--build-walk", action="store_true")
    ap.add_argument("--out", default=OUT)
    a, rest = ap.parse_known_args(argv)
    if a.write:
        write(a.out)
        return 0
    if a.build_walk:
        schema, profile = RT.station()
        nodes = RT.clusters()
        ok, _bad = RW.endpoints(schema, profile, nodes)
        ar, br = walk_pair(schema, profile, nodes, ok)
        _m, p = build_walk(schema, profile, ar, br)
        print(f"  wrote {os.path.relpath(p, ROOT)}")
        return 0
    if a.gate:
        return gate(rest)
    return report(a.out)


if __name__ == "__main__":
    sys.exit(main())
