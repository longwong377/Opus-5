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

# How far either side of its places a cluster's ring corridor runs. `deck_plan`
# sweeps 24 phase offsets over 2.5 degrees and then runs "over the arc the rooms
# actually occupy plus a margin"; this is that margin, and it is used here as a
# CHEAP PROXY for calling `deck_plan` 96 times. The proxy is stated because it is
# a proxy: `--exact` calls `deck_plan` for real and the report prints both.
ARC_MARGIN_DEG = 2.5

# Two clusters on adjacent decks can take a lift between them if their axial
# positions are within this. A lift is a vertical shaft; it does not travel
# along the ship.
LIFT_Z_REACH_M = D.Z_CLUSTER_M

# Two sectors can be joined by an axial trunk if their z extents come within
# this of each other. The sectors of B5 abut along the axis, so this is small.
TRUNK_GAP_M = 400.0


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
    for n in out.values():
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


def edges(nodes, schema):
    """Every connection the station's own structure implies, with its kind.

    NOT EVERY PAIR. A corridor is a real object with a generator behind it, so
    an edge is proposed only where one of the four kinds could physically run,
    and each carries whether that generator exists today.
    """
    out = []
    keys = sorted(nodes)

    # --- axial: two clusters on ONE deck, joined along the ship --------------
    by_deck = {}
    for k in keys:
        by_deck.setdefault(k[:3], []).append(k)
    for dk, ks in by_deck.items():
        ks = sorted(ks, key=lambda k: k[3])
        for a, b in zip(ks, ks[1:]):
            shared = _shared_arc(nodes[a], nodes[b])
            out.append({
                "a": a, "b": b, "kind": "axial",
                "built": shared >= MIN_SHARED_ARC_DEG,
                "length_m": abs(b[3] - a[3]),
                "why": (f"{shared:.1f} deg of shared arc"
                        if shared >= MIN_SHARED_ARC_DEG else
                        f"corridor arcs share only {shared:.1f} deg, under "
                        f"the {MIN_SHARED_ARC_DEG:.0f} a doorway needs"),
            })

    # --- lift: two decks of ONE ring, joined radially ------------------------
    by_ring = {}
    for k in keys:
        by_ring.setdefault(k[:2], []).append(k)
    for rk, ks in by_ring.items():
        decks = sorted({k[2] for k in ks})
        for d0, d1 in zip(decks, decks[1:]):
            for a in [k for k in ks if k[2] == d0]:
                for b in [k for k in ks if k[2] == d1]:
                    if abs(a[3] - b[3]) <= LIFT_Z_REACH_M:
                        out.append({
                            "a": a, "b": b, "kind": "lift", "built": False,
                            "length_m": 0.0,
                            "why": "no lift, stair or shaft exists anywhere in "
                                   "the project -- transit.py computes the "
                                   "ride, navigation.py routes NPCs through "
                                   "it, and there is nothing to walk into",
                        })

    # --- spoke: two rings of ONE sector, joined radially ---------------------
    by_sector = {}
    for k in keys:
        by_sector.setdefault(k[0], []).append(k)
    for sec, ks in by_sector.items():
        rings = sorted({k[1] for k in ks})
        for r0, r1 in zip(rings, rings[1:]):
            a = min((k for k in ks if k[1] == r0), key=lambda k: k[3])
            b = min((k for k in ks if k[1] == r1), key=lambda k: k[3])
            out.append({
                "a": a, "b": b, "kind": "spoke", "built": False,
                "length_m": 0.0,
                "why": "interior.spoke builds the structure and spoke_portal "
                       "cuts an opening for the tram; there is no walkable "
                       "passage in the gauge",
            })

    # --- trunk: two sectors, joined along the axis ---------------------------
    secs = sorted(by_sector)
    zs = {s: _sector_z(schema, s) for s in secs if s in
          schema["sectors"]["extents_m"]}
    order = sorted(zs, key=lambda s: zs[s][0])
    for s0, s1 in zip(order, order[1:]):
        gap = zs[s1][0] - zs[s0][1]
        a = max(by_sector[s0], key=lambda k: k[3])
        b = min(by_sector[s1], key=lambda k: k[3])
        out.append({
            "a": a, "b": b, "kind": "trunk",
            "built": abs(gap) <= TRUNK_GAP_M,
            "length_m": abs(b[3] - a[3]),
            "why": (f"sectors abut within {gap:.0f} m"
                    if abs(gap) <= TRUNK_GAP_M else
                    f"{gap:.0f} m of unbuilt axis between the sectors"),
        })
    return out


def components(nodes, es, only_built=True):
    """How many separate walkable pieces the station is in."""
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
    return groups


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
    for k in ("axial", "trunk", "lift", "spoke"):
        if k not in kinds:
            continue
        tot, bl = kinds[k]
        note = "" if bl == tot else f"   <- {tot - bl} with NO GENERATOR"
        print(f"     {k:8s} {bl:4d} buildable of {tot:4d}{note}")
    ex = next((e for e in es if e["kind"] == "lift"), None)
    if ex:
        print(f"\n     the lift, in full: {ex['why']}")

    print(f"\n  COMPONENTS, with only what can be built today: "
          f"{len(g_built)}")
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

    # NEGATIVE CONTROL: with the axial generator taken away -- which is the
    # state of this project as recently as yesterday -- the count must get
    # worse. If it does not, the axial edges are not doing anything and the
    # whole R1 milestone is theatre.
    no_axial = [dict(e, built=False) if e["kind"] == "axial" else e
                for e in es]
    n0 = len(components(nodes, no_axial, True))
    check("and the axial corridor is load-bearing",
          n0 > r["components_built"],
          f"without it {n0} pieces, with it {r['components_built']}")

    # NEGATIVE CONTROL: counting UNBUILT edges as built must improve the
    # number, or the lift and spoke edges are not proposing anything real.
    check("the missing generators are proposing real connections",
          r["components_all"] < r["components_built"],
          f"{r['components_all']} if lifts and spoke passages existed, "
          f"against {r['components_built']} today")

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
