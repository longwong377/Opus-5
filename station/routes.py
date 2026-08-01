#!/usr/bin/env python3
"""THE CIRCULATION NETWORK — can you get from here to there.

WHY THIS FILE EXISTS, and it is the most expensive omission in the project.

`station/directory.py` is the register of 128 places, and every one of them
carries an `adjacent=` field. `docs/MASTER-PLAN.md` M1's exit criterion reads
"addressed, non-colliding, **adjacency-valid**", and `directory.py`'s own
docstring promises "adjacencies the sources require must hold". So routing was
nominally step one and was reported complete.

Measured, the field holds **33 edges over 128 places**. A connected graph over
128 nodes needs at least 127. Ten of the 33 join two places that were already in
the same 40 m cluster; the other 23 span clusters with no geometry between them;
and building all 33 would leave **97** components where the geometry gives 96.
Nothing reads the field -- one prose citation in `audio.py` and that is all.

"Adjacency-valid" was a check that the names were spelled correctly.

WHAT THE STATION ACTUALLY IS, measured here rather than asserted:

    128 locations  ->  96 FOOT-CONNECTED COMPONENTS
       74 components hold exactly one location
       the largest walkable piece of Babylon 5 holds six

because a component is exactly one z-cluster -- one 40 m slice of one deck of
one ring of one sector -- and until session 4g there was no corridor generator
in this project capable of joining two of them. `interior.ring_arc` sweeps at a
FIXED z; a deck spans 1,120 m of axis.

THE RULE THIS FILE APPLIES, and it is hard rule 4 turned on circulation:

    ROUTES AND ROOMS COME FROM THE SAME SCHEMA.

The network is DERIVED from the station's own structure -- which decks exist,
which clusters sit on them, which rings nest inside which sector -- and never
hand-declared, because 33 hand-written edges will never cover 251 decks. The 33
canon adjacencies then become ASSERTIONS ON the derived network: an adjacency
the geometry cannot realise is a conflict to resolve, not a line to delete.

EVERY EDGE SAYS WHETHER IT CAN BE BUILT TODAY, and that is the whole point of
the report. An edge whose generator does not exist is not a smaller number, it
is a different number, and printing them separately is what stops "the station
is connected" being said about a graph half of whose edges are wishes.

    axial    two clusters on one deck            -- interior.axial_run    BUILDABLE (4g)
    trunk    two sectors along the axis          -- interior.axial_run    BUILDABLE (4g)
    lift     two decks of one ring, radially     -- NOTHING EXISTS
    spoke    two rings of one sector, radially   -- NOTHING EXISTS as a walkable passage

Run: python3 station/routes.py --report
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import deck as D                                                # noqa: E402
import directory as DIR                                         # noqa: E402
import interior as it                                           # noqa: E402

# How much arc two clusters on one deck must share before an axial corridor can
# run between them. FROM `deck.JOIN_MIN_ARC_DEG`, not restated -- that module
# owns the number because it is the one that declines to build.
MIN_SHARED_ARC_DEG = D.JOIN_MIN_ARC_DEG

# How far either side of its places a cluster's ring corridor runs. FROM
# `deck.ARC_PAD_DEG`, and the first version of this file wrote 2.5 here as a
# "cheap proxy" -- which was five times too tight and reported 79 of 96 clusters
# unable to reach their spine when the true figure is far lower. A proxy for a
# number the owning module exports is not a proxy, it is a second copy. The arc
# itself now comes from `deck.deck_arc`, which is the function the corridor is
# actually built from and costs nothing to call: it reads the register and does
# no geometry.
ARC_MARGIN_DEG = D.ARC_PAD_DEG

# Two clusters on adjacent decks can take a lift between them if their axial
# positions are within this. A lift is a vertical shaft; it does not travel
# along the ship.
LIFT_Z_REACH_M = D.Z_CLUSTER_M

# Two sectors can be joined by an axial trunk if their z extents come within
# this of each other. The sectors of B5 abut along the axis, so this is small.
TRUNK_GAP_M = 400.0

# DOES THE LIFT EXIST? Asked of the filesystem, not written down, so this file
# cannot claim a connection whose generator is not there. The moment
# `station/lift.py` lands, 38 edges change state and the component count moves
# without anyone editing this line.
_LIFT_EXISTS = os.path.exists(os.path.join(HERE, "lift.py"))
_SPOKE_WAY_EXISTS = os.path.exists(os.path.join(HERE, "spoke_way.py"))


def clusters():
    """Every z-cluster that carries a location, with what it carries.

    THE NODE OF THE CIRCULATION GRAPH IS A CLUSTER, NOT A PLACE, and that is the
    finding stated as a data structure: two places in one cluster are already
    joined by the ring corridor that serves them, and two places in different
    clusters have nothing between them at all. Making the cluster the node is
    what stops the graph flattering itself.
    """
    out = {}
    for p in DIR.PLACES:
        sec, ring, dk = p.get("sector"), p.get("ring"), p.get("deck")
        z = p.get("z_m")
        if sec is None or ring is None or dk is None or z is None:
            continue
        key = (sec, ring, dk, round(z / D.Z_CLUSTER_M) * D.Z_CLUSTER_M)
        n = out.setdefault(key, {"key": key, "sector": sec, "ring": ring,
                                 "deck": dk, "z": key[3], "places": [],
                                 "angles": []})
        n["places"].append(p["key"])
        n["angles"].append(float(p.get("angle_deg") or 0.0))
    for k, n in out.items():
        try:
            _h, lo, span = D.deck_arc(n["sector"], n["ring"], n["deck"], n["z"])
            n["arc"] = (lo, lo + span)
        except ValueError:
            a = sorted(n["angles"])
            n["arc"] = (a[0] - ARC_MARGIN_DEG, a[-1] + ARC_MARGIN_DEG)
        n["z_true"] = None
    return out


def _shared_arc(a, b):
    """Degrees of arc two clusters' corridors have in common."""
    lo = max(a["arc"][0], b["arc"][0])
    hi = min(a["arc"][1], b["arc"][1])
    return hi - lo


def _sector_z(schema, sector):
    ex = schema["sectors"]["extents_m"][sector]
    return ex["z0"], ex["z1"]


# --------------------------------------------------------------------------
# THE INFRASTRUCTURE, and it is what makes the graph closable at all
# --------------------------------------------------------------------------
# THE FIRST VERSION OF THIS FILE BUILT THE GRAPH OUT OF PLACES ALONE and it could
# not close: with EVERY implied edge built it still left the station in 23
# pieces. The reason is the same mistake as the 33 declared adjacencies, one
# level up. 71 decks carry a location; the station has 251. **A route passes
# through decks nobody lives on**, so a network made only of destinations has no
# node to route through and no amount of edges between destinations will join it.
#
# So the network has TRANSIT NODES, and they are not an abstraction -- each one
# is a piece of geometry with a generator behind it:
#
#   spine    one axial corridor per deck, at the sector's transit angle, running
#            the deck's whole z extent.        interior.axial_run   BUILT (4g)
#   column   one radial transit column per sector at that same angle, serving
#            every deck of every ring.         station/lift.py      BEING BUILT
#   trunk    axial corridor joining one sector's column to the next.
#                                              interior.axial_run   BUILT (4g)
#
# ONE ANGLE PER SECTOR FOR ALL OF IT. The column has to land on each deck's
# spine, so the spine angle and the column angle are the same number, chosen
# once per sector. That is also how a real station is laid out and how B5's own
# core shuttle and lift cores read on screen: a transit spine you join, not a
# lift beside every room.
#
# A place's cluster reaches its deck's spine through the RING corridor it
# already has -- if that corridor covers the spine angle. Today a cluster's
# corridor covers only the arc its own rooms occupy plus 2.5 degrees
# (`deck_plan`), which is why this edge can fail, and closing that is milestone
# 2 of the session: **a deck's corridor should come from the RING, not from
# where its rooms happen to be.**


def transit_angle(sector, nodes):
    """The angle a sector's whole transit column and every deck spine stands at.

    DERIVED, not chosen: the angle that lies inside the most cluster arcs on
    that sector, so the fewest places need their corridor extended to reach it.
    Ties break to the lower angle so the answer is deterministic.
    """
    ks = [k for k in nodes if k[0] == sector]
    if not ks:
        return 0.0
    cands = sorted({round(a, 3) for k in ks for a in nodes[k]["angles"]})
    best = (None, -1)
    for a in cands:
        n = sum(1 for k in ks
                if nodes[k]["arc"][0] <= a <= nodes[k]["arc"][1])
        if n > best[1]:
            best = (a, n)
    return best[0] if best[0] is not None else 0.0


def edges(nodes, schema, full_ring=False):
    """Every connection the station's own structure implies, with its kind.

    `full_ring=True` answers the second question this file exists to ask: what
    the network becomes once a deck's corridor covers its ring instead of only
    the arc its rooms sit on. The difference between the two runs is the value
    of that one change, in components, and it is printed rather than argued.
    """
    out = []
    keys = sorted(nodes)
    sectors = sorted({k[0] for k in keys})
    ang = {s: transit_angle(s, nodes) for s in sectors}

    # --- ring: a cluster reaches its deck's spine along its own corridor -----
    # BUILDABLE MEANS THE GENERATOR CAN DO IT, NOT THAT IT HAPPENS TO TODAY.
    # `deck.deck_arc(must_cover=)` extends a cluster's corridor the short way
    # round until it reaches the deck's transit angle -- so the question this
    # edge asks is whether that extension exists, and it is asked BY CALLING IT
    # rather than by reasoning about it. `full_ring=False` reports the state
    # before that argument was threaded, which is what the 4g report compares
    # against.
    for k in keys:
        a = ang[k[0]]
        if full_ring:
            lo, hi = nodes[k]["arc"]
            reach = True
        else:
            try:
                _h, lo2, span2 = D.deck_arc(nodes[k]["sector"], nodes[k]["ring"],
                                            nodes[k]["deck"], nodes[k]["z"],
                                            must_cover=a)
                lo, hi = lo2, lo2 + span2
            except ValueError:
                lo, hi = nodes[k]["arc"]
            # A FULL RING COVERS EVERY ANGLE, and the first version of this
            # test did not know that: `deck_arc` clamps its span at 360, so a
            # cluster whose rooms already wrap the ring reported its transit
            # angle unreachable whenever that angle fell outside the raw
            # [lo, lo+360] window. 14 clusters read as unreachable for a
            # comparison that was not done modulo the ring.
            span = hi - lo
            if span >= 359.9:
                reach = True
            else:
                d = (a - lo) % 360.0
                reach = d <= span
        out.append({
            "a": k, "b": ("spine",) + k[:3], "kind": "ring",
            "built": reach, "length_m": 0.0,
            "why": (f"the cluster's corridor covers the transit angle "
                    f"{a:.1f} deg"
                    if reach else
                    f"the cluster's corridor spans {lo:.1f}..{hi:.1f} deg and "
                    f"the transit angle is {a:.1f} -- deck_plan runs a corridor "
                    f"over the arc its ROOMS occupy, not over the ring"),
        })

    # --- axial: everything on one deck is on that deck's spine --------------
    # The spine is a single corridor running the deck's whole z extent, so the
    # clusters on it are joined by construction. The edge is the spine itself.
    spines = sorted({("spine",) + k[:3] for k in keys})
    for sp in spines:
        out.append({
            "a": sp, "b": sp, "kind": "axial", "built": True, "length_m": 0.0,
            "why": "interior.axial_run, written this session",
        })

    # --- lift: every deck spine meets its RING's transit column --------------
    # ONE COLUMN PER RING, NOT PER SECTOR, and the first version of this graph
    # had it per sector -- which reported the station as ONE piece by assuming a
    # shaft that runs from ring 0 to ring 3. `station/lift.py` spans the decks
    # of ONE ring; a ring is a nested shell and crossing from one to the next is
    # a radial move through the ring boundary, which is the spoke. Blue and
    # green carry two rings, yellow three, red four. The per-sector column
    # quietly granted eight connections nothing can build.
    for sp in spines:
        out.append({
            "a": sp, "b": ("column", sp[1], sp[2]), "kind": "lift",
            "built": _LIFT_EXISTS, "length_m": 0.0,
            "why": ("station/lift.py" if _LIFT_EXISTS else
                    "no lift, stair or shaft exists anywhere in the project -- "
                    "transit.py computes the ride, navigation.py routes NPCs "
                    "through it, and there is nothing to walk into"),
        })

    # --- spoke: one ring's column to the next, radially ----------------------
    for sec in sectors:
        rings = sorted({k[1] for k in keys if k[0] == sec})
        for r0, r1 in zip(rings, rings[1:]):
            out.append({
                "a": ("column", sec, r0), "b": ("column", sec, r1),
                "kind": "spoke", "built": _SPOKE_WAY_EXISTS, "length_m": 0.0,
                "why": ("station/spoke_way.py" if _SPOKE_WAY_EXISTS else
                        "interior.spoke builds the structure and spoke_portal "
                        "cuts an opening for the tram; there is no walkable "
                        "passage in the gauge"),
            })

    # --- trunk: one sector's column to the next, along the axis --------------
    zs = {s: _sector_z(schema, s) for s in sectors
          if s in schema["sectors"]["extents_m"]}
    order = sorted(zs, key=lambda s: zs[s][0])
    for s0, s1 in zip(order, order[1:]):
        gap = zs[s1][0] - zs[s0][1]
        r0 = min(k[1] for k in keys if k[0] == s0)
        r1 = min(k[1] for k in keys if k[0] == s1)
        # THE TWO SECTORS DO NOT STAND AT THE SAME ANGLE. Blue's transit angle
        # is 140 deg and red's is 90, and an axial corridor cannot change angle
        # -- so a trunk is an axial run PLUS an arc of ring corridor to carry
        # the 50 degree jog. Both generators exist (`interior.axial_run`,
        # `interior.ring_arc`), which is why this is buildable; saying so is the
        # difference between a connection and an assumption. The first version
        # of this edge silently assumed the columns were coaxial.
        jog = abs(((ang[s1] - ang[s0]) + 180.0) % 360.0 - 180.0)
        out.append({
            "a": ("column", s0, r0), "b": ("column", s1, r1), "kind": "trunk",
            "built": abs(gap) <= TRUNK_GAP_M,
            "length_m": abs(gap),
            "why": (f"sectors abut within {gap:.0f} m; axial_run plus "
                    f"{jog:.0f} deg of ring_arc to carry the angle jog"
                    if abs(gap) <= TRUNK_GAP_M else
                    f"{gap:.0f} m of unbuilt axis between the sectors"),
        })
    return out


def all_nodes(nodes, es):
    """Place clusters plus every transit node the edges introduce."""
    out = dict(nodes)
    for e in es:
        for side in ("a", "b"):
            k = e[side]
            if k not in out:
                out[k] = {"key": k, "places": [], "transit": True}
    return out


def components(nodes, es, only_built=True):
    """How many separate walkable pieces the station is in.

    RUN OVER THE TRANSIT NODES TOO, and the first version was not, which read
    96 pieces however many edges were built -- the union-find skipped every edge
    whose far end was a spine or a column because those were not in the node
    dict. A graph measured over half its own vertices always says the same
    thing, which is what made it look like a real answer.

    The count that is reported is of pieces HOLDING A PLACE. A stretch of spine
    with nothing on it is infrastructure, not a piece of the station a player is
    trying to reach.
    """
    nodes = all_nodes(nodes, es)
    par = {k: k for k in nodes}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for e in es:
        if only_built and not e["built"]:
            continue
        if e["a"] in par and e["b"] in par:
            par[find(e["a"])] = find(e["b"])
    groups = {}
    for k in nodes:
        groups.setdefault(find(k), []).append(k)
    return {r: v for r, v in groups.items()
            if any(nodes[k].get("places") for k in v)}


def declared_check(nodes, es, only_built=True):
    """The 33 canon adjacencies, against the derived network.

    THE DECLARED GRAPH IS THE ASSERTION AND THE DERIVED ONE IS THE ANSWER. An
    adjacency the sources require and the network cannot realise is a conflict
    to resolve -- not a line to delete and not a reason to widen the network.
    """
    at = {}
    for k, n in nodes.items():
        for pk in n["places"]:
            at[pk] = k
    groups = components(nodes, es, only_built)
    who = {}
    for root, ks in groups.items():
        for k in ks:
            who[k] = root
    ok = bad = orphan = 0
    fails = []
    for p in DIR.PLACES:
        for other in p.get("adjacent", ()):
            a, b = at.get(p["key"]), at.get(other)
            if a is None or b is None:
                orphan += 1
                continue
            if who.get(a) == who.get(b):
                ok += 1
            else:
                bad += 1
                fails.append((p["key"], other))
    return ok, bad, orphan, fails


def report(schema=None, profile=None):
    if schema is None:
        schema, profile = it.load()
    nodes = clusters()
    es = edges(nodes, schema)
    built = [e for e in es if e["built"]]
    kinds = {}
    for e in es:
        k = kinds.setdefault(e["kind"], [0, 0])
        k[0] += 1
        k[1] += bool(e["built"])

    g_built = components(nodes, es, True)
    g_all = components(nodes, es, False)
    sizes = sorted((len(v) for v in g_built.values()), reverse=True)
    place_n = sum(len(n["places"]) for n in nodes.values())

    print("\nTHE CIRCULATION NETWORK — can you get from here to there\n")
    print(f"  places      {place_n} located, in {len(nodes)} z-clusters over "
          f"{len({k[:3] for k in nodes})} decks and "
          f"{len({k[0] for k in nodes})} sectors")
    print(f"\n  edges the station's own structure implies:")
    for k in ("ring", "axial", "lift", "trunk", "spoke"):
        if k not in kinds:
            continue
        tot, bl = kinds[k]
        note = "" if bl == tot else f"   <- {tot - bl} with NO GENERATOR"
        print(f"     {k:8s} {bl:4d} buildable of {tot:4d}{note}")
    ex = next((e for e in es if e["kind"] == "lift"), None)
    if ex:
        print(f"\n     the lift, in full: {ex['why']}")

    es_ring = edges(nodes, schema, full_ring=True)
    g_ring = components(nodes, es_ring, True)
    g_ring_all = components(nodes, es_ring, False)
    unreached = sum(1 for e in es if e["kind"] == "ring" and not e["built"])
    raw = sum(1 for k in nodes
              if not (nodes[k]["arc"][0] <= transit_angle(k[0], nodes)
                      <= nodes[k]["arc"][1]))
    print(f"\n  {raw} of {len(nodes)} clusters could not reach their deck's "
          f"spine on the rooms-only arc; with deck_arc(must_cover=) it is "
          f"{unreached}")
    print(f"\n  COMPONENTS, with only what can be built today: "
          f"{len(g_built)}")
    print(f"  COMPONENTS, if every deck's corridor covered its ring: "
          f"{len(g_ring)}")
    print(f"  COMPONENTS, full ring AND the lift built:       "
          f"{len(g_ring_all)}")
    print(f"  COMPONENTS, if every implied edge existed:      "
          f"{len(g_all)}")
    print(f"     largest piece holds {sizes[0]} cluster(s), "
          f"{sum(1 for s in sizes if s == 1)} pieces hold one")

    ok, bad, orphan, fails = declared_check(nodes, es, True)
    uniq = len({tuple(sorted((q["key"], o))) for q in DIR.PLACES
                for o in q.get("adjacent", ())})
    print(f"\n  the canon adjacencies in directory.py, against this network"
          f" ({ok + bad + orphan} declarations, {uniq} unique pairs):")
    print(f"     {ok} reachable, {bad} NOT reachable, {orphan} off-register")
    for a, b in fails[:6]:
        print(f"       {a} -> {b}")
    if len(fails) > 6:
        print(f"       ... and {len(fails) - 6} more")
    print()
    return {"nodes": len(nodes), "places": place_n, "edges": len(es),
            "built_edges": len(built), "components_built": len(g_built),
            "components_all": len(g_all), "declared_ok": ok,
            "declared_bad": bad}


# --------------------------------------------------------------------------
# THE GATE
# --------------------------------------------------------------------------
# ONE NUMBER, AND IT MUST REACH ONE. Every other coverage number in this project
# counts things that exist; this one counts whether they are joined, which is
# the question `deck.py --sweep`'s 128/128 cannot ask. It is RED and it should
# be: the station is in 96 pieces.
TARGET_COMPONENTS = 1


def _selftest():
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (f"  {note}" if note else ""))

    schema, profile = it.load()
    nodes = clusters()
    es = edges(nodes, schema)
    r = report(schema, profile)

    check("every located place lands in a cluster",
          r["places"] == len([p for p in DIR.PLACES
                              if p.get("sector") is not None]),
          f"{r['places']} placed")

    # THE GATE. It fails, and the number it prints is the project's headline.
    check(f"the station is ONE walkable piece",
          r["components_built"] <= TARGET_COMPONENTS,
          f"{r['components_built']} components — the station is in "
          f"{r['components_built']} pieces")

    # NEGATIVE CONTROL: take the deck spine away -- which is the state this
    # project was in yesterday, before `interior.axial_run` existed -- and every
    # cluster must fall back to being its own piece. If it does not, the spine
    # is not doing anything and milestone R1 is theatre.
    #
    # THE FIRST VERSION OF THIS CONTROL DISABLED THE `axial` EDGE AND READ 71
    # BOTH WAYS. That edge is a self-loop on the spine node -- the spine IS the
    # axial corridor -- so disabling it changes nothing, and a control that
    # cannot move is not a control. What carries the connection is the `ring`
    # edge, cluster to spine, and that is what has to be removed.
    no_spine = [e for e in es if e["kind"] not in ("ring", "axial")]
    n0 = len(components(nodes, no_spine, True))
    check("and the deck spine is load-bearing",
          n0 > r["components_built"],
          f"without it {n0} pieces, with it {r['components_built']}")

    # NEGATIVE CONTROL: counting UNBUILT edges as built must improve the
    # number, or the lift and spoke edges are not proposing anything real.
    # NEGATIVE CONTROL on the lift, and it replaces one that went degenerate
    # the moment `station/lift.py` landed: "components_all < components_built"
    # is unsatisfiable once every edge is buildable, so it began failing for
    # being TRUE. The question worth asking is whether the lift carries the
    # connection, and that is asked by taking it away.
    no_lift = [e for e in es if e["kind"] != "lift"]
    n1 = len(components(nodes, no_lift, True))
    check("and the lift is load-bearing",
          n1 > r["components_built"],
          f"without it {n1} pieces, with it {r['components_built']}")

    # The declared graph is 33 edges over 128 places and cannot connect them.
    dg = {}
    for p in DIR.PLACES:
        dg.setdefault(p["key"], set()).update(p.get("adjacent", ()))
    n_edges = len({tuple(sorted((a, b))) for a, bs in dg.items() for b in bs})
    check("the declared adjacency is too sparse to be a network, stated",
          n_edges < len(DIR.PLACES) - 1,
          f"{n_edges} declared edges over {len(DIR.PLACES)} places; a "
          f"connected graph needs at least {len(DIR.PLACES) - 1}")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.report and not a.selftest:
        report()
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
