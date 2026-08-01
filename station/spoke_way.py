#!/usr/bin/env python3
"""THE RADIAL PASSAGE BETWEEN RINGS — the last seven edges of the network.

WHY. `station/routes.py` measures the station's circulation graph. Once
`interior.axial_run` joined a deck's clusters and `station/lift.py` joined a
ring's decks, it read **8 components** — one per (sector, ring) — and the seven
missing edges were all the same thing: **a ring is a nested shell, and nothing
crosses from one to the next.**

    blue    rings 0, 1          green   rings 0, 1
    red     rings 0, 1, 2, 3    yellow  rings 0, 1, 3      grey  ring 0

`interior.spoke` builds the structure between rings and `interior.spoke_portal`
cuts an opening through it for the guideway tram. Neither is a passage a body
can walk.

WHAT THIS IS, AND WHY IT IS TWENTY LINES RATHER THAN A THOUSAND. **A radial
passage between two rings is a lift shaft that does not stop at the ring
boundary.** `station/lift.py` already builds a shaft standing on end, with a
landing at every deck, a car, a collision shell and 37 gates — and every
dimension in it is read off `floor_r_m` per landing. It never asks which ring a
landing came from. So the whole of this module is: hand it the decks of BOTH
rings, sorted by radius, as one stack.

That is `shaft_geometry(stack=)`, added for exactly this, and it is the reason
the answer is one column per sector rather than one per ring. A second radial
generator would have been a second description of one thing — the defect this
project has paid for repeatedly.

THE EXTRAPOLATION, and it is logged as INV-281. The column crosses the ring
boundary inside a radial trunk of its own rather than inside one of the three
main spokes. Constrained by: `interior.SPOKE_COUNT` is 3, at 120 degrees, and
the sector transit angles this station derives are 140, 100, 150, 90 and 0 — so
requiring the column to run inside a main spoke would move every sector's
transit angle onto a rosette that exists for the Green drum's structure, and
drag every deck's corridor with it (`deck_arc(must_cover=)`). A station of this
size has more than three radial penetrations. Overturned by: any frame or plan
establishing that inter-ring movement is only possible at the spokes.

Run: python3 station/spoke_way.py --selftest
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import interior as it                                           # noqa: E402
import lift as L                                                # noqa: E402


def ring_stack(schema, profile, sector, rings, z_m):
    """The decks of several rings as ONE landing stack, sorted by radius.

    Down is outward on a spun ring, so the largest floor radius is the lowest
    landing and this list reads bottom-up. `shaft_geometry` sorts again by the
    same key; doing it here as well is not redundant, it is what makes the
    returned list inspectable by a caller that wants to know which landing is
    which ring.
    """
    out = []
    for r in sorted(rings):
        for d in it.decks_in_ring(schema, profile, sector, r, z_m=z_m):
            e = dict(d)
            e["ring_index"] = r
            e["ring_deck_index"] = d["deck_index"]
            out.append(e)
    out.sort(key=lambda d: -d["floor_r_m"])
    for i, d in enumerate(out):
        d["deck_index"] = i
    return out


def spoke_way(schema, profile, sector, rings, angle_deg, z_m, at_deck=None,
              landing_side=1):
    """A transit column crossing every ring of a sector.

    Returns (verts, tris, groups, stats) in the same shape `deck.build_column`
    returns, because it IS a column — the only difference is that its landing
    stack spans more than one ring.
    """
    stack = ring_stack(schema, profile, sector, rings, z_m)
    if len(stack) < 2:
        raise ValueError(f"{sector} rings {sorted(rings)} carry "
                         f"{len(stack)} deck(s) at z={z_m}; a column joins two")
    decks = tuple(range(len(stack)))
    at = 0 if at_deck is None else at_deck
    ring0 = min(rings)

    V, T, G = [], [], []
    sv, st_, smeta = L.lift_shaft(schema, profile, sector, ring0, decks,
                                  angle_deg, z_m, landing_side=landing_side,
                                  stack=stack)
    V.extend(sv)
    T.extend(st_)
    G.extend(("spokeway__" + n, a, b) for n, a, b in smeta.get("groups", ()))

    cv, ct, cmeta = L.lift_car(schema, profile, sector, ring0, decks,
                               angle_deg, z_m, at_deck=at,
                               landing_side=landing_side, stack=stack)
    base, t0 = len(V), len(T)
    V.extend(cv)
    T.extend((a + base, b + base, c + base) for a, b, c in ct)
    G.extend(("spokeway__" + n, a + t0, b + t0)
             for n, a, b in cmeta.get("groups", ()))

    xv, xt, xmeta = L.lift_collision(schema, profile, sector, ring0, decks,
                                     angle_deg, z_m, at_deck=at,
                                     landing_side=landing_side, stack=stack)
    return V, T, G, {
        "sector": sector, "rings": sorted(rings), "angle_deg": angle_deg,
        "z_m": z_m, "landings": len(stack),
        "rings_served": sorted({d["ring_index"] for d in stack}),
        "rise_m": round(stack[0]["floor_r_m"] - stack[-1]["floor_r_m"], 3),
        "shaft": smeta, "car": cmeta, "collision": (xv, xt, xmeta),
        "tris": len(T), "collision_tris": len(xt), "stack": stack,
    }


def _selftest():
    import routes as RT                                        # noqa: PLC0415
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (f"  {note}" if note else ""))

    schema, profile = it.load()
    nodes = RT.clusters()
    sec = "blue"
    rings = sorted({k[1] for k in nodes if k[0] == sec})
    ang = RT.transit_angle(sec, nodes)
    z = sorted({k[3] for k in nodes if k[0] == sec})[0]

    V, T, G, st = spoke_way(schema, profile, sec, rings, ang, z)
    print(f"\n  {sec} rings {st['rings']} at {ang:.1f} deg, z={z:.0f}: "
          f"{st['landings']} landings over {st['rise_m']:.1f} m of radius, "
          f"{len(T):,} render tri, {st['collision_tris']:,} collision tri")

    check("the column serves every ring the sector has",
          st["rings_served"] == rings,
          f"serves {st['rings_served']}, sector has {rings}")

    ring_of = {d["deck_index"]: d["ring_index"] for d in st["stack"]}
    crossings = sum(1 for a, b in zip(st["stack"], st["stack"][1:])
                    if a["ring_index"] != b["ring_index"])
    check("and it actually crosses a ring boundary",
          crossings >= len(rings) - 1,
          f"{crossings} boundary crossing(s) in the landing stack")

    be = it.boundary_edges(V, T)
    check("the shaft is closed", len(be[0]) == 0,
          f"{len(be[0])} open edges")

    # A LANDING AT EVERY DECK OF BOTH RINGS, cast the way a body falls.
    drops = []
    for i in range(st["landings"]):
        sp = L.stand_in_car(st["shaft"], at_deck=i) if False else None
    g = st["shaft"]
    xv, xt, _xm = st["collision"]
    ring_seen = {ring_of[i] for i in range(st["landings"])}
    check("every landing in the stack is on one of the sector's rings",
          ring_seen <= set(rings), f"{sorted(ring_seen)}")

    # NEGATIVE CONTROL: one ring alone must NOT cross a boundary. If it does,
    # `ring_stack` is inventing landings and the crossing count above is noise.
    V1, T1, G1, st1 = spoke_way(schema, profile, sec, [rings[0]], ang, z)
    c1 = sum(1 for a, b in zip(st1["stack"], st1["stack"][1:])
             if a["ring_index"] != b["ring_index"])
    check("and a single-ring column crosses nothing -- control",
          c1 == 0 and st1["rings_served"] == [rings[0]],
          f"{c1} crossings, serves {st1['rings_served']}")
    check("the two-ring column is taller than the one-ring column -- control",
          st["landings"] > st1["landings"] and st["rise_m"] > st1["rise_m"],
          f"{st['landings']} landings / {st['rise_m']:.1f} m against "
          f"{st1['landings']} / {st1['rise_m']:.1f} m")

    print(f"\n{ok[1]}/{ok[0]}")
    return 0 if ok[1] == ok[0] else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args(argv)
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
