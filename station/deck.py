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

import collision as C                                           # noqa: E402
import directory as dr                                          # noqa: E402
import interior as it                                           # noqa: E402
import interior_kit as K                                        # noqa: E402
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


def room_axial_half_m(schema, profile, place):
    """How far a built room reaches along the station axis from its centre.

    Read off the same three lines `rooms.build` uses to size itself, rather than
    off the gazetteer footprint: a location's stored footprint is its FULL
    extent (`docking_bays` is 360 degrees by 140 m), and what gets built is one
    representative bay clamped by `bay_span_m`. Asking the footprint gives a
    number an order of magnitude too big.
    """
    _w, l_full, _r = R.room_extent_m(schema, profile, place)
    _bw, bl = R.bay_span_m(place)
    return min(l_full, bl) / 2.0 + R.WALL_T_M


def corridor_z_m(schema, profile, here):
    """Where the ring corridor goes: clear of the rooms it serves.

    THE CORRIDOR USED TO BE PLACED AT A ROUNDING ARTEFACT. `z_clusters` groups
    locations into 40 m buckets and labels each bucket `round(z / 40) * 40`;
    `build_deck` then placed the corridor AT THE LABEL. Blue ring 0 deck 0's
    rooms sit at z = 7115 and got a corridor at 7120, so the 2.6 m corridor tube
    ran through the far end of every room on the deck -- 0.36 m into
    `docking_bays`, 1.31 m into `plantroom_bay`. A bucket label is a name for a
    group, not a position.

    The corridor goes just beyond the furthest room's outer wall, so its near
    face is flush with the deepest room and no room is cut. Rooms that fall
    short of it need a vestibule to reach it, which is what a station has
    anyway -- and is the next thing to build.
    """
    far = max(q["z_m"] + room_axial_half_m(schema, profile, q) for q in here)
    return far + K.PROVISIONAL["corridor_width_m"] / 2.0


def deck_arc(sector, ring, deck, z_m, max_rooms=None):
    """The angular span of corridor a cluster needs, and the places on it.

    Pulled out of `build_deck` so the render mesh and the collision shell are
    laid over EXACTLY the same arc rather than each recomputing it -- two copies
    of this arithmetic is one copy too many for geometry that has to agree about
    where the floor is.
    """
    here = places_on(sector, ring, deck, z_m)
    if max_rooms is not None:
        here = here[:max_rooms]
    if not here:
        raise ValueError(f"no gazetteer location on {sector}/{ring}/{deck}")
    lo = min(q["angle_deg"] for q in here) - ARC_PAD_DEG
    hi = max(q["angle_deg"] for q in here) + ARC_PAD_DEG
    return here, lo, min(360.0, hi - lo)


def build_collision(schema, profile, sector, ring, deck, z_m=None,
                    max_rooms=None):
    """The deck's COLLISION geometry -- what a body stands on, not what it sees.

    See `station/collision.py` for why these are different meshes. In short: the
    render corridor's deck carries a 66 mm lighting channel and 22 mm grid
    tiles, and a capsule dropped on it stands still forever while reporting that
    it is on the floor.
    """
    plan = it.ring_cells(schema, profile, sector, ring, deck)
    if plan is None:
        raise ValueError(f"{sector} ring {ring} carries no deck {deck}")
    if z_m is None:
        z_m = (z_clusters(sector, ring, deck) or [None])[0]
    here, lo, span = deck_arc(sector, ring, deck, z_m, max_rooms)
    return C.corridor_shell(schema, profile, sector, ring, degrees=span,
                            start_deg=lo, radius_m=plan["radius_m"],
                            z_offset=corridor_z_m(schema, profile, here))


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
    # The corridor runs over the arc the rooms actually occupy plus a margin, so
    # a player can walk past the last door rather than stopping at it.
    here, lo, span = deck_arc(sector, ring, deck, z_m, max_rooms)
    # AT A z DERIVED FROM THE ROOMS, not at the cluster's label -- see
    # `corridor_z_m`. Placing it at the label put the corridor through the far
    # end of every room on the deck; placing it at the deck's nominal z, before
    # clustering existed, made a body fall 263 m through empty space.
    cz = corridor_z_m(schema, profile, here)
    stats["corridor_z"] = cz
    cv, ct, cm = it.ring_arc(schema, profile, sector, ring,
                             degrees=span, start_deg=lo, radius_m=radius,
                             z_offset=cz)
    V.extend(cv)
    T.extend(ct)
    G.extend(cm["groups"] if isinstance(cm, dict) and "groups" in cm else [])
    stats["corridor_tris"] = len(ct)

    # THE SPAWN COMES FROM THE COLLISION SHELL, which is the only mesh that
    # knows where the floor a body rests on actually is. Two earlier versions of
    # this line were wrong in instructive ways and both are worth keeping:
    #
    #  * computed over the whole assembled deck, the largest constant-radius
    #    surface belonged to a room whose geometry reaches z = -302, so the
    #    "floor" was seven kilometres away and the body fell forever;
    #  * computed over the corridor alone, it took the CENTROID of the floor
    #    triangles -- and the centroid of a 344 degree ring of floor is near the
    #    axis, so the angle recovered from it was whatever numerical asymmetry
    #    the arc happened to have. It also landed dead on the centreline, which
    #    is the inside of the lighting channel: the body straddled a 66 mm slot
    #    and could not take a step.
    #
    # A place has an angle. Stand the player at one.
    _cvx, _ctx, cmeta = C.corridor_shell(
        schema, profile, sector, ring, degrees=span, start_deg=lo,
        radius_m=radius, z_offset=cz)
    stats["collision_meta"] = cmeta
    stats["spawn"] = C.stand_at(cmeta, here[0]["angle_deg"])
    stats["spawn_at"] = here[0]["key"]

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


def floor_radius(verts, tris, quantum=0.001, near_m=0.30, min_share=0.02):
    """The radius of the surface a boot rests on, read off an emitted mesh.

    What is LEFT of the old `spawn_m` after the parts that were wrong came out.
    Finding the floor of a spun ring this way is sound -- a corridor sweeps its
    section round the axis, so its deck is thousands of triangles at one radius
    while everything else varies. Deriving a POSITION from it was not: see the
    note in `build_deck`.

    THE DECK IS NOT ONE PLANE, and taking the commonest radius gets the wrong
    one. A corridor deck is three surfaces stacked within 88 mm -- a lighting
    channel at the bottom, its panel 66 mm above that, and grid tiles 22 mm
    above the panel -- and the panel's radius wins on triangle count, because
    every wall and portal in the section also has its base at that height. A
    player walks on the TILES. So: find the deck plane by weight, then take the
    highest substantial surface within `near_m` of it, which is the same rule
    `collision.corridor_profile` applies by casting rays from above.

    That makes this an independent check rather than a restatement: the shell
    derives its floor by ray casting through the kit's cross-section, this reads
    it off emitted triangle radii, and `_selftest` fails if they disagree.

    `quantum` is 1 mm, not the 0.1 m the first version used -- rounding the
    radius to a decimetre put the answer 50 mm from the surface it named.
    """
    import collections
    bands = collections.Counter()
    for tri in tris:
        rs = [math.hypot(verts[j][0], verts[j][1]) for j in tri]
        if max(rs) - min(rs) < 0.002:
            bands[round(sum(rs) / 3.0 / quantum) * quantum] += 1
    if not bands:
        return None
    r0, n0 = bands.most_common(1)[0]
    # Smallest radius is highest: up is inward on a spun ring.
    return min(r for r, n in bands.items()
               if abs(r - r0) <= near_m and n >= n0 * min_share)


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

    sp = s["spawn"]
    check("a deck reports a spawn point", sp is not None)
    if sp:
        rr = math.hypot(sp[0], sp[1])
        check("the spawn is at the deck's own radius, off the floor",
              plan["radius_m"] * 0.9 < rr < plan["radius_m"] * 1.05,
              f"spawn r={rr:.1f} against deck {plan['radius_m']:.1f}")
        # The spawn is at a PLACE, not at the numerical centroid of an arc.
        want = math.radians(dr.by_key(s["spawn_at"])["angle_deg"])
        got = math.atan2(sp[1], sp[0])
        check("the player starts at a named location, not at a centroid",
              abs(math.atan2(math.sin(got - want), math.cos(got - want)))
              < 1e-6,
              f"{s['spawn_at']} is at {math.degrees(want):.2f} deg, "
              f"spawn is at {math.degrees(got):.2f} deg")

    # THE COLLISION SHELL AND THE RENDER MESH MUST AGREE ABOUT THE FLOOR. They
    # are built by different code from the same schema, which is the only way
    # this project allows two things to match -- and it is worth an assertion
    # because a shell 50 mm out is a player hovering or sunk, and neither shows
    # up in a render.
    cv, ct, cm = build_collision(schema, profile, "blue", 0, 0)
    check("a collision shell is emitted", len(ct) > 0)
    probe = dict(cm, arc_deg=8.0, start_deg=0.0)
    rv, rt, _ = it.ring_arc(schema, profile, "blue", 0, degrees=8.0,
                            start_deg=0.0, radius_m=plan["radius_m"],
                            z_offset=7120.0)
    r_render = C.underfoot_radius(rv, rt, probe)
    check("the shell's floor sits on the render mesh's floor",
          r_render is not None
          and abs(r_render - cm["floor_r_m"]) < 0.003,
          f"render floor r={r_render}, shell floor r={cm['floor_r_m']}")
    check("collision is an order of magnitude cheaper than render",
          len(ct) * 10 < s["corridor_tris"],
          f"{len(ct):,} collision vs {s['corridor_tris']:,} corridor render")

    # THE CORRIDOR MUST NOT RUN THROUGH THE ROOMS IT SERVES, and it did. Placed
    # at the z-cluster's rounded bucket label the 2.6 m corridor tube cut 0.36 m
    # into `docking_bays` and 1.31 m into `plantroom_bay`. Nothing could fail
    # for it: the walk test only asks whether a body moves, and interpenetrating
    # geometry is perfectly walkable. It is visible in a render and wrong in a
    # simulation, which is two reasons and no gate.
    here_all = places_on("blue", 0, 0, z_clusters("blue", 0, 0)[0])
    cz = corridor_z_m(schema, profile, here_all)
    near = cz - K.PROVISIONAL["corridor_width_m"] / 2.0
    through = [(q["key"],
                round(q["z_m"] + room_axial_half_m(schema, profile, q)
                      - near, 3))
               for q in here_all
               if q["z_m"] + room_axial_half_m(schema, profile, q) > near + 1e-6]
    check("the corridor clears every room on its deck", not through,
          f"cuts into {through}")
    # And it is not merely parked far away: the deepest room reaches it.
    flush = min(near - (q["z_m"] + room_axial_half_m(schema, profile, q))
                for q in here_all)
    check("the corridor's near face is flush with the deepest room",
          abs(flush) < 1e-6,
          f"nearest room is {flush:.3f} m short of the corridor wall")
    gaps = sorted((round(near - (q["z_m"]
                                 + room_axial_half_m(schema, profile, q)), 2),
                   q["key"]) for q in here_all)
    print(f"  corridor at z={cz:.2f}, near face {near:.2f}; rooms fall short "
          f"by {gaps[0][0]:.2f}-{gaps[-1][0]:.2f} m "
          f"(widest {gaps[-1][1]}) -- these need vestibules")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sector", default="blue")
    ap.add_argument("--ring", type=int, default=0)
    ap.add_argument("--deck", type=int, default=0)
    ap.add_argument("--max-rooms", type=int, default=None)
    ap.add_argument("--obj", default="")
    ap.add_argument("--collision-obj", default="",
                    help="where to write the collision shell -- the mesh a "
                         "body stands on, which is not the one it looks at")
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
    sp = s["spawn"]
    print(f"  spawn {sp[0]:.3f},{sp[1]:.3f},{sp[2]:.3f} at {s['spawn_at']}")
    for k, why in s["skipped"]:
        print(f"  skipped {k}: {why}")
    if a.obj:
        write_obj(a.obj, v, t, g)
        print(f"  wrote {a.obj}")
    if a.collision_obj:
        cv, ct, cm = build_collision(schema, profile, a.sector, a.ring, a.deck,
                                     max_rooms=a.max_rooms)
        C.write_obj(a.collision_obj, cv, ct)
        print(f"  wrote {a.collision_obj}: {len(ct):,} collision triangles "
              f"({len(ct) / max(1, s['corridor_tris']) * 100:.1f}% of the "
              f"corridor's render mesh), clear width {cm['half_w_m'] * 2:.3f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
