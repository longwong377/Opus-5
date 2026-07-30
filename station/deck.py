#!/usr/bin/env python3
"""Assemble a whole deck: the ring corridor, and the rooms that open off it.

WHAT THIS ENDS. The station was 118 ISLANDS. Every location had geometry,
materials, lighting, furniture and people, and none of them touched: a body
spawned in the brig could walk around the brig and there was nowhere to go.
`station/walkable.py` proved a room could be stood in; nothing proved the
station could be crossed, because nothing had ever been assembled.

`interior.ring_arc` has built the corridor since session 2w and `directory.py`
has carried every location's `(sector, ring, deck, angle_deg, z_m)` since layer
1. The corridor and the rooms were both there, in the same coordinate frame,
and no code had ever put them in one mesh. This is that code.

WHY A DECK IS THE RIGHT UNIT. It is what a player occupies -- you are on a deck,
you walk round its ring, you go through a door into a room off it -- and it is
also what `cell_manifest` already streams. A deck is small enough to load and
large enough to be somewhere.

Run: python3 station/deck.py --sector blue --ring 0 --deck 0 [--obj OUT]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import rooms as R                                               # noqa: E402

# How much of the ring to emit around the rooms, in degrees. A whole 360 deg
# ring of corridor at full articulation is 700k triangles and nobody can see
# more than a few degrees of it from inside; this is the streaming window.
ARC_PAD_DEG = 12.0


# How far along the axis two locations can sit and still be on one ring
# corridor. `interior.ring_arc` sweeps a 3.2 m corridor section AROUND the ring
# at a fixed z, so a ring serves the locations at ITS z and not the ones 300 m
# up the station. A "deck" in the gazetteer is not a z-slice: Blue ring 0 deck 0
# holds 16 locations spread over 1,100 m of axis, in six clusters. The cluster
# is the walkable unit, and assembling a whole deck onto one ring put rooms
# hundreds of metres from the floor that was supposed to serve them -- which the
# walk test found as a body falling 263 m.
Z_CLUSTER_M = 40.0


def places_on(sector, ring, deck, z_m=None):
    """Gazetteer locations on one deck, in angular order.

    With `z_m`, only those within `Z_CLUSTER_M` of it -- the ones a single ring
    corridor at that z can actually serve.
    """
    out = [q for q in dr.PLACES
           if q.get("sector") == sector and q.get("ring") == ring
           and q.get("deck") == deck]
    if z_m is not None:
        out = [q for q in out if abs(q.get("z_m", 0.0) - z_m) <= Z_CLUSTER_M]
    return sorted(out, key=lambda q: q.get("angle_deg", 0.0))


def z_clusters(sector, ring, deck):
    """The z positions that carry locations, busiest first."""
    import collections
    c = collections.Counter()
    for q in places_on(sector, ring, deck):
        c[round(q.get("z_m", 0.0) / Z_CLUSTER_M) * Z_CLUSTER_M] += 1
    return [z for z, _n in c.most_common()]


def _place_local(verts, radius_m, angle_deg, z_m):
    """Room-local (x across, y up, z along) -> station world.

    THE ROOM'S OWN FRAME IS TANGENTIAL. `rooms.build` emits x across the
    corridor, y up from the deck and z along it, which is exactly the frame
    `garden.place` maps onto the drum -- so the same mapping works here with the
    ring's radius in place of the drum's.

    UP IS INWARD, and the first version had it backwards. This station SPINS:
    the centrifugal floor is the outer wall of a ring, so "down" points away
    from the axis and a person's head points toward it. Written as `radius + y`
    every room hung off the outside of its own deck, and the walk test reported
    a body that never reached a floor. `garden.place` states the same rule for
    the drum in one line -- "up is inward" -- and it is the same station.
    """
    a0 = math.radians(angle_deg)
    out = []
    for x, y, z in verts:
        r = radius_m - y
        a = a0 + x / max(radius_m, 1e-9)
        out.append((r * math.cos(a), r * math.sin(a), z_m + z))
    return out


def build_deck(schema, profile, sector, ring, deck, with_rooms=True,
               max_rooms=None, z_m=None):
    """One deck as a single mesh. Returns (verts, tris, groups, stats)."""
    V, T, G = [], [], []
    stats = {"rooms": 0, "skipped": [], "corridor_tris": 0, "room_tris": 0}

    plan = it.ring_cells(schema, profile, sector, ring, deck)
    if plan is None:
        raise ValueError(f"{sector} ring {ring} carries no deck {deck}")
    radius = plan["radius_m"]

    if z_m is None:
        z_m = (z_clusters(sector, ring, deck) or [None])[0]
    here = places_on(sector, ring, deck, z_m)
    if max_rooms is not None:
        here = here[:max_rooms]
    if not here:
        raise ValueError(f"no gazetteer location on {sector}/{ring}/{deck}")

    # The corridor, over the arc the rooms actually occupy plus a margin, so a
    # player can walk past the last door rather than stopping at it.
    lo = min(q["angle_deg"] for q in here) - ARC_PAD_DEG
    hi = max(q["angle_deg"] for q in here) + ARC_PAD_DEG
    span = min(360.0, hi - lo)
    # AT THE CLUSTER'S OWN z. The corridor is a 3.2 m section swept round the
    # ring; putting it at the deck's nominal z while the rooms sit elsewhere is
    # what made a body fall 263 m through empty space.
    cv, ct, cm = it.ring_arc(schema, profile, sector, ring,
                             degrees=span, start_deg=lo, radius_m=radius,
                             z_offset=z_m)
    V.extend(cv)
    T.extend(ct)
    G.extend(cm["groups"] if isinstance(cm, dict) and "groups" in cm else [])
    stats["corridor_tris"] = len(ct)
    # THE SPAWN COMES FROM THE CORRIDOR, NOT THE ASSEMBLED DECK. Computed over
    # everything, the largest constant-radius surface in the MESH belonged to a
    # room whose geometry reaches z = -302, so the "floor" it picked was seven
    # kilometres from the corridor and the body fell forever. The corridor is
    # what a player spawns in; ask it directly.
    stats["spawn"] = spawn_m(cv, ct)

    if not with_rooms:
        return V, T, G, stats

    for q in here:
        try:
            rv, rt, rg = R.build(schema, profile, q)
        except Exception as e:                                  # noqa: BLE001
            stats["skipped"].append((q["key"], str(e)[:60]))
            continue
        # The room sits just INBOARD of the corridor's own radius, so its deck
        # is continuous with the corridor deck rather than floating at a
        # different height. A step between a corridor and a room is a trip
        # hazard the walk test would find and a player would feel.
        placed = _place_local(rv, radius, q["angle_deg"], q["z_m"])
        off, t0 = len(V), len(T)
        V.extend(placed)
        T.extend((a + off, b + off, c + off) for a, b, c in rt)
        G.extend((f"{q['key']}__{n}", lo_ + t0, hi_ + t0) for n, lo_, hi_ in rg)
        stats["rooms"] += 1
        stats["room_tris"] += len(rt)
    stats["triangles"] = len(T)
    return V, T, G, stats


def spawn_m(verts, tris, up_is_inward=True):
    """A point a body can stand on, computed from the deck's own floor.

    STOP GUESSING SPAWNS. Three hand-picked corridor points put a body through
    the deck and reported an identical 313 m fall each time, which is the
    signature of a spawn over no floor at all. `rooms.spawn_m` already learned
    this for rooms -- read the free channel rather than assume the origin is
    clear -- and a deck needs the same.

    The floor of a spun ring is the largest CONSTANT-RADIUS surface in the mesh:
    a corridor sweeps its section round the ring, so its deck is thousands of
    triangles at one radius while everything else varies. Find that radius, take
    the centroid of the triangles on it, and stand 1 m inboard -- inboard,
    because up is inward when the floor is the outer wall.
    """
    import collections
    bands = collections.defaultdict(list)
    for tri in tris:
        rs = [math.hypot(verts[j][0], verts[j][1]) for j in tri]
        if max(rs) - min(rs) < 0.05:
            key = round(sum(rs) / 3.0, 1)
            bands[key].append([sum(verts[j][k] for j in tri) / 3.0
                               for k in range(3)])
    if not bands:
        return None
    r_floor = max(bands, key=lambda k: len(bands[k]))
    pts = bands[r_floor]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    a = math.atan2(cy, cx)
    r = r_floor - 1.0 if up_is_inward else r_floor + 1.0
    return (r * math.cos(a), r * math.sin(a), cz)


def write_obj(path, verts, tris, groups):
    per = [None] * len(tris)
    for name, lo, hi in groups:
        for i in range(lo, hi):
            per[i] = name
    with open(path, "w") as f:
        for x, y, z in verts:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        cur = None
        for i, (a, b, c) in enumerate(tris):
            nm = per[i] or "deck_untagged"
            if nm != cur:
                cur = nm
                f.write(f"g {nm}\n")
            f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = it.load()

    here = places_on("blue", 0, 0)
    check("Blue ring 0 deck 0 carries locations", len(here) > 4,
          f"{len(here)}")

    v, t, g, s = build_deck(schema, profile, "blue", 0, 0, max_rooms=4)
    check("a deck assembles", len(t) > 0, str(s)[:120])
    check("it has corridor AND rooms in one mesh",
          s["corridor_tris"] > 0 and s["room_tris"] > 0, str(s)[:120])
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in g) <= len(t))

    # THE POINT: the rooms are at DIFFERENT places, not stacked on the origin.
    # A deck whose rooms all landed at (0,0,0) would look assembled and be one
    # room; that is the failure this check exists for.
    import collections
    centres = collections.defaultdict(list)
    for name, lo, hi in g:
        if "__" not in name:
            continue
        key = name.split("__")[0]
        for tri in t[lo:hi]:
            for i in tri:
                centres[key].append(v[i])
    cs = {}
    for k, pts in centres.items():
        cs[k] = (sum(p[0] for p in pts) / len(pts),
                 sum(p[1] for p in pts) / len(pts),
                 sum(p[2] for p in pts) / len(pts))
    if len(cs) >= 2:
        ks = sorted(cs)
        far = max(math.dist(cs[a], cs[b]) for a in ks for b in ks if a != b)
        check("the rooms are in different places on the ring", far > 5.0,
              f"widest separation {far:.1f} m")

    # Rooms must sit at the corridor's radius, not float at the axis.
    rad = [math.hypot(p[0], p[1]) for p in v]
    plan = it.ring_cells(schema, profile, "blue", 0, 0)
    check("everything is near the deck's own radius",
          min(rad) > plan["radius_m"] * 0.5,
          f"min radius {min(rad):.1f} m against deck {plan['radius_m']:.1f} m")

    probe = _place_local([(0.0, 0.0, 0.0), (0.0, 2.0, 0.0)], 200.0, 0.0, 0.0)
    check("up is INWARD on a ring deck -- this station spins",
          math.hypot(*probe[1][:2]) < math.hypot(*probe[0][:2]),
          f"floor r={math.hypot(*probe[0][:2]):.1f} "
          f"head r={math.hypot(*probe[1][:2]):.1f}")

    sp = spawn_m(v, t)
    check("a deck reports a spawn point", sp is not None)
    if sp:
        rr = math.hypot(sp[0], sp[1])
        check("the spawn is at the deck's own radius, off the floor",
              plan["radius_m"] * 0.9 < rr < plan["radius_m"] * 1.05,
              f"spawn r={rr:.1f} against deck {plan['radius_m']:.1f}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", default="blue")
    ap.add_argument("--ring", type=int, default=0)
    ap.add_argument("--deck", type=int, default=0)
    ap.add_argument("--max-rooms", type=int, default=None)
    ap.add_argument("--obj", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    schema, profile = it.load()
    v, t, g, s = build_deck(schema, profile, a.sector, a.ring, a.deck,
                            max_rooms=a.max_rooms)
    print(f"{a.sector} ring {a.ring} deck {a.deck}: {s['rooms']} rooms, "
          f"{len(t):,} triangles "
          f"({s['corridor_tris']:,} corridor + {s['room_tris']:,} rooms)")
    for k, why in s["skipped"]:
        print(f"  skipped {k}: {why}")
    if a.obj:
        write_obj(a.obj, v, t, g)
        print(f"  wrote {a.obj}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
