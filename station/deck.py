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


# Rings that are not ring-corridor decks at all, and why. Not a failure list:
# these are places the assembler is the wrong tool for, and saying so is how a
# sweep's numbers stay honest.
NOT_RING_DECKS = {
    ("green", 1): "the habitat drum -- the Garden, the townscape, the tram and "
                  "the spokes. An open 8 km barrel, not a corridor deck; its "
                  "walkable surface is drum_ground's heightfield",
}


def deck_index(schema, profile, sector, ring, deck_label):
    """The gazetteer's `deck` turned into an index into the built deck stack.

    THESE ARE NOT THE SAME NUMBER IN EVERY SECTOR, and assuming they were is
    what stopped 14 of 67 decks assembling with `IndexError`. Grey Sector's
    locations carry the deck numbers the show uses -- 40, 55, 80 -- while the
    generated stack for Grey ring 0 has 23 decks; Yellow reaches deck 30 with 7.
    A show-facing deck NUMBER is a name, and using a name as an index is the
    same mistake as placing a corridor at a z-cluster's bucket label.

    Decided per ring rather than per location, so the mapping is monotonic and
    stable: if every deck number the gazetteer uses on this ring is a valid
    index, they ARE the indices and are used unchanged (Blue, Red, Green ring 0);
    otherwise the distinct numbers are ranked in order and the rank is the index,
    which preserves which deck is above which and is the only thing the stack
    ordering has to get right.
    """
    decks = it.decks_in_ring(schema, profile, sector, ring)
    if not decks:
        raise ValueError(f"{sector} ring {ring} carries no deck stack")
    labels = sorted({q["deck"] for q in dr.PLACES
                     if q.get("sector") == sector and q.get("ring") == ring})
    if labels and max(labels) < len(decks):
        return deck_label
    if deck_label not in labels:
        raise ValueError(f"{sector} ring {ring} has no deck {deck_label}")
    return labels.index(deck_label)


def _ring_cells(schema, profile, sector, ring, deck):
    """`interior.ring_cells` with the gazetteer's deck number translated."""
    if (sector, ring) in NOT_RING_DECKS:
        raise ValueError(f"{sector} ring {ring} is not a ring deck: "
                         f"{NOT_RING_DECKS[(sector, ring)]}")
    return it.ring_cells(schema, profile, sector, ring,
                         deck_index(schema, profile, sector, ring, deck))


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


def room_interior_half_m(schema, profile, place):
    """Half a built room's INSIDE length along the station axis.

    Read off the same three lines `rooms.build` uses to size itself, rather than
    off the gazetteer footprint: a location's stored footprint is its FULL
    extent (`docking_bays` is 360 degrees by 140 m), and what gets built is one
    representative bay clamped by `bay_span_m`. Asking the footprint gives a
    number an order of magnitude too big.
    """
    _w, l_full, _r = R.room_extent_m(schema, profile, place)
    _bw, bl = R.bay_span_m(place)
    return min(l_full, bl) / 2.0


def room_axial_half_m(schema, profile, place):
    """The same, to the OUTSIDE of the wall. Which of the two is wanted matters:
    the corridor is placed clear of a room's outer face, and a vestibule joins
    its inner one."""
    return room_interior_half_m(schema, profile, place) + R.WALL_T_M


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


def room_half_w_m(schema, profile, place):
    """Half a built room's width across the ring, as `rooms.build` sizes it."""
    w_full, _l, _r = R.room_extent_m(schema, profile, place)
    bw, _bl = R.bay_span_m(place)
    return min(w_full, bw) / 2.0


def deck_plan(schema, profile, sector, ring, deck, z_m=None, max_rooms=None):
    """Everything the render and the collision assemblies both need, DECIDED
    ONCE: the arc, the corridor's z, and which rooms get a door and where.

    THE DOOR DECISION CANNOT BE MADE TWICE. It is made from the corridor's bay
    division, and a door that does not fit its room has to be left out of the
    corridor, the vestibule, the room's aperture and the collision opening
    together. Made separately in two places it went one way in the render and
    the other in the shell: five decks ended up with a room whose collision
    carried a doorway and a vestibule out in the wall next door, and whose
    render was a sealed box -- 68 sample points over nothing apiece.

    A door fits when its whole leaf lands inside the room's wall. `lifts` is
    3.0 m across and the corridor's bays are 3.07 m, so its door can miss even
    after being clamped into its bay; those rooms are reported in `unopened`
    rather than silently skipped, because a room you cannot enter is a real
    state of the build and not a rounding detail.
    """
    plan = _ring_cells(schema, profile, sector, ring, deck)
    if plan is None:
        raise ValueError(f"{sector} ring {ring} carries no deck {deck}")
    if z_m is None:
        z_m = (z_clusters(sector, ring, deck) or [None])[0]
    here, lo, span = deck_arc(sector, ring, deck, z_m, max_rooms)
    cz = corridor_z_m(schema, profile, here)
    radius = plan["radius_m"]

    door_w = K.PROVISIONAL["door_width_m"]
    want = [(q["angle_deg"], -1) for q in here]

    def score(start_deg, arc_deg):
        """How many rooms get a usable door if the arc starts here."""
        r, n, seg = it.arc_sections(schema, profile, sector, ring,
                                    degrees=arc_deg, radius_m=radius)
        _ps, placed = it.place_doors(r, n, seg, arc_deg, start_deg, cz, want)
        rooms, unopened = [], []
        for q, d in zip(here, placed):
            dx = math.radians(d["angle_deg"] - q["angle_deg"]) * radius
            hw = room_half_w_m(schema, profile, q)
            if abs(dx) + door_w / 2.0 < hw - R.WALL_T_M:
                rooms.append((q, d, dx))
            else:
                unopened.append((q["key"], round(dx, 2), round(hw, 2)))
        return rooms, unopened

    # THE CORRIDOR'S PHASE IS A FREE CHOICE, AND IT DECIDES WHO GETS A DOOR.
    # A door takes over a whole bay and must clear the portal frames at both
    # ends, so it can only sit in the middle ~1.0 m of a 3.07 m bay. Where a
    # room's angle lands on a section boundary the door is shoved to the edge of
    # that window -- systematically 1.32 m, which is further than a 3.0 m room
    # is wide, so `lifts`, `standard_corridor` and fourteen others came out
    # sealed. The offsets were IDENTICAL across unrelated decks, which is what
    # gave it away: an arc of `angle +/- 12 deg` divided into 2.5 deg sections
    # puts every room exactly on a boundary.
    #
    # The arc's start is arbitrary -- it is padding, not a measurement -- so
    # sweep it and keep the phase that opens the most rooms. Extending `span` by
    # the same amount keeps every room covered. This is what an architect does
    # with a structural grid: slide it until the doors land where the rooms are.
    best = None
    for k in range(24):
        off = 2.5 * k / 24.0
        rooms, unopened = score(lo - off, min(360.0, span + off))
        if best is None or len(rooms) > len(best[0]):
            best = (rooms, unopened, lo - off, min(360.0, span + off))
        if not unopened:
            break
    rooms, unopened, lo, span = best
    return {"plan": plan, "radius": radius, "z_m": z_m, "here": here,
            "lo": lo, "span": span, "cz": cz, "rooms": rooms,
            "unopened": unopened,
            "doors": [(q["angle_deg"], -1) for q, _d, _x in rooms]}


def build_collision(schema, profile, sector, ring, deck, z_m=None,
                    max_rooms=None, props=False):
    """The deck's COLLISION geometry -- what a body stands on, not what it sees.

    See `station/collision.py` for why these are different meshes. In short: the
    render corridor's deck carries a 66 mm lighting channel and 22 mm grid
    tiles, and a capsule dropped on it stands still forever while reporting that
    it is on the floor.
    """
    d = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms)

    # The shell's holes come from the SAME door decision the corridor is cut
    # with -- `deck_plan` makes it once. Recomputing it here is what gave five
    # decks a room whose collision had a doorway and whose render was a sealed
    # box.
    v, t, meta = C.corridor_shell(schema, profile, sector, ring,
                                  degrees=d["span"], start_deg=d["lo"],
                                  radius_m=d["radius"], z_offset=d["cz"],
                                  doors=[x[1] for x in d["rooms"]])
    # THE VESTIBULE JOINS TWO INTERIOR FACES, and getting either end wrong is a
    # hole in the floor. The first version ran from the room's OUTER face to the
    # kit's nominal half width (1.30 m) while the shell's floor edge is at its
    # MEASURED clear half width (1.0806 m) -- a 0.219 m gap in the deck at every
    # doorway, and a body that walked into one fell through and accelerated
    # outward under spin gravity for 30 km.
    near = d["cz"] - meta["half_w_m"]

    # A vestibule per room that has a door, then every room's shell -- with an
    # opening where there is a door and sealed where there is not.
    meta["rooms"] = []
    meta["unopened"] = d["unopened"]
    meta["groups"] = []
    opened = {q["key"]: door for q, door, _dx in d["rooms"]}
    for q in d["here"]:
        door = opened.get(q["key"])
        inner = q["z_m"] + room_interior_half_m(schema, profile, q)
        pieces = [room_shell_for(schema, profile, meta, q,
                                 door["angle_deg"] if door else None)]
        if door is not None:
            pieces.append(C.vestibule_shell(meta, door["angle_deg"], inner,
                                            near))
            meta["rooms"].append({"key": q["key"],
                                  "door_deg": door["angle_deg"],
                                  "vestibule_m": round(near - inner, 3)})
            # The closed door itself, as its own group so the runtime can
            # switch exactly this off when it opens.
            pv, pt = C.door_panel(meta, door["angle_deg"], door["z_m"])
            off, t0 = len(v), len(t)
            v.extend(pv)
            t.extend((a + off, b + off, c + off) for a, b, c in pt)
            meta["groups"].append((f"doorpanel_{q['key']}", t0, len(t)))
        # SOLID FURNITURE. Off by default because it costs a room build apiece
        # and `--sweep` asks a structural question of 66 decks; on wherever a
        # body is actually going to be put on this deck. A room whose tables a
        # player walks through is a backdrop, not a place.
        if props:
            try:
                rv, rt, rg = R.build(schema, profile, q)
                boxes = C.prop_boxes(rv, rt, rg)
                pieces.append(C.boxes_mesh(
                    boxes, lambda pts, qq=q: _place_local(
                        pts, d["radius"], qq["angle_deg"], qq["z_m"])))
                meta.setdefault("prop_boxes", 0)
                meta["prop_boxes"] += len(boxes)
            except Exception as e:                              # noqa: BLE001
                meta.setdefault("prop_errors", []).append(
                    (q["key"], str(e)[:60]))

        for vv, tt in pieces:
            off = len(v)
            v.extend(vv)
            t.extend((a + off, b + off, c + off) for a, b, c in tt)
    meta["triangles"] = len(t)
    return v, t, meta


def door_leaves(radius_m, angle_deg, z_m, key, open_fraction=0.0):
    """The two moving leaves of one pressure door, each as its own group.

    A DOOR THAT DOES NOT OPEN IS A PICTURE OF A DOOR, and until now the leaves
    were baked into the corridor's single mesh -- so the player walked through a
    shut door, because the collision aperture was permanently open and the thing
    they could see was not connected to anything. These come out as
    `doorleaf_<key>_0` and `_1`, which is what lets `godot/scripts/door.gd` find
    them and slide them.

    The leaf is authored across x, up y, thick in z, which is exactly the frame
    `_place_local` maps onto a ring: x becomes arc, y becomes radius, z becomes
    the station axis. The same mapping a room uses, because it is the same
    relationship to the deck.
    """
    out = []
    for i in (0, 1):
        lv, lt = K.door_leaf(open_fraction=open_fraction, which=i)
        placed = _place_local(lv, radius_m, angle_deg, z_m)
        out.append((f"doorleaf_{key}_{i}", placed, lt))
    return out


def _runs(per_tri):
    """Per-triangle group names -> (name, lo, hi) spans.

    Two conventions for "which material owns this triangle" live in this
    project and both are load-bearing: `interior_kit` records SPANS because its
    tags nest, and `signage`/`dressing` record one name PER TRIANGLE because
    theirs do not. Converting at the boundary is cheaper than making either
    side change, and doing it in one named place is what stops a third
    convention appearing.
    """
    out = []
    for i, nm in enumerate(per_tri):
        if out and out[-1][0] == nm and out[-1][2] == i:
            out[-1] = (nm, out[-1][1], i + 1)
        else:
            out.append((nm, i, i + 1))
    return out


def door_sign(radius_m, angle_deg, z_m, side, place, gap_m=0.10):
    """The plaque beside one door: what this place is, and where you are.

    118 places have carried a name, a sector, a ring, a deck and a bearing in
    `directory.py` for sessions and no player could read a word of it.
    judge-3w's finding at a doorway was "no room name, no bay number" and it
    was true of every door on the station.

    THE PLAQUE'S FRAME IS THE ROOM'S FRAME, which is why this is four lines.
    `signage.door_plaque` authors +x across, +y up, +z out of the face, and
    `_place_local` maps exactly that onto a ring -- x becomes arc, y becomes
    radius inward, z becomes the station axis. A door is in a wall of constant
    z, so a plaque on that wall faces along the axis and needs no rotation at
    all... on one side.

    `side` IS NOT DECORATION. A door on the far wall of the corridor faces the
    other way, and a plaque placed with the same numbers would read backwards
    from inside the corridor and face into the room. Turning it is a HALF TURN
    ABOUT THE VERTICAL AXIS -- (x, y, z) -> (-x, y, -z) -- which is a rotation
    and therefore preserves winding. Mirroring in z alone would point it the
    right way with every face inside-out, which is the defect this project
    found in `dressing._cyl` and would not see in a render, because an
    inside-out surface and a missing one both show the background.
    """
    import signage as S                                        # noqa: PLC0415
    v, t, g = S.door_plaque(place)
    dx = (K.PROVISIONAL["door_width_m"] + S.PLAQUE_W_M) / 2.0 + gap_m
    # Beside the door on the side the arc runs, lifted to reading height. `y`
    # is measured up from the deck because `_place_local` subtracts it from the
    # radius, so 1.55 m here is 1.55 m above the floor a body stands on.
    local = [(x + dx, y + S.PLAQUE_CENTRE_H_M, z) for x, y, z in v]
    if side > 0:
        local = [(-x, y, -z) for x, y, z in local]
    return _place_local(local, radius_m, angle_deg, z_m), t, g


def vestibule_render(radius_m, angle_deg, z_from, z_to, width_m, height_m,
                     floor_y=0.022, wall_t=0.12):
    """The vestibule a player can SEE, as distinct from the one they stand on.

    The first version of this passage existed only in the collision shell, so a
    body walked from the corridor into a room across two metres of nothing --
    the doorway framed a black hole in the deck. Physics and pixels disagreeing
    about whether there is a floor is the same defect as them disagreeing about
    a wall, which is what `rooms.build(door_at=)` had just fixed at the other
    end of this passage. Both directions are the same bug.

    Its groups are the corridor kit's own tag names -- `deck_panel`, `deck_grid`,
    `wall_panel`, `soffit` -- so it is made of the same materials as the corridor
    it opens off, by construction rather than by a second table that can drift.

    `floor_y` is the corridor's tile top, not the room's deck: the collision
    shell is flat at that radius the whole way, so matching it here is what puts
    a boot on the surface it appears to be on.
    """
    hw = width_m / 2.0
    lo, hi = min(z_from, z_to), max(z_from, z_to)
    v, t, g = [], [], []

    def box(name, x0, y0, z0, x1, y1, z1):
        lo_t = len(t)
        base = len(v)
        for xx, yy, zz in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0),
                           (x0, y1, z0), (x0, y0, z1), (x1, y0, z1),
                           (x1, y1, z1), (x0, y1, z1)):
            a = math.radians(angle_deg) + xx / max(radius_m, 1e-9)
            r = radius_m - yy
            v.append((r * math.cos(a), r * math.sin(a), zz))
        for q in ((0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6),
                  (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
                  (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)):
            t.append(tuple(base + i for i in q))
        g.append((name, lo_t, len(t)))

    if hi - lo < 1e-6:
        return v, t, g
    box("deck_panel", -hw, -0.14, lo, hw, 0.0, hi)
    box("deck_grid", -hw + 0.04, 0.0, lo, hw - 0.04, floor_y, hi)
    for s in (-1.0, 1.0):
        x = s * hw
        box("wall_panel", min(x, x + s * wall_t), floor_y, lo,
            max(x, x + s * wall_t), height_m, hi)
    box("soffit", -hw - wall_t, height_m, lo, hw + wall_t,
        height_m + 0.14, hi)
    return v, t, g


def room_shell_for(schema, profile, meta, place, door_angle_deg):
    """A room's collision shell, sized the way `rooms.build` sizes the room."""
    w_full, _l, _r = R.room_extent_m(schema, profile, place)
    bw, _bl = R.bay_span_m(place)
    return C.room_shell(meta, place["angle_deg"], min(w_full, bw) / 2.0,
                        room_interior_half_m(schema, profile, place),
                        R.ceiling_m(place), place["z_m"],
                        door_angle_deg=door_angle_deg)


def build_deck(schema, profile, sector, ring, deck, with_rooms=True,
               max_rooms=None, z_m=None):
    """One deck as a single mesh. Returns (verts, tris, groups, stats)."""
    V, T, G = [], [], []
    stats = {"rooms": 0, "skipped": [], "corridor_tris": 0, "room_tris": 0}

    plan = _ring_cells(schema, profile, sector, ring, deck)
    if plan is None:
        raise ValueError(f"{sector} ring {ring} carries no deck {deck}")
    radius = plan["radius_m"]

    if z_m is None:
        z_m = (z_clusters(sector, ring, deck) or [None])[0]
    # The corridor runs over the arc the rooms actually occupy plus a margin, so
    # a player can walk past the last door rather than stopping at it.
    # ONE DOOR DECISION, shared with the collision assembly -- see `deck_plan`.
    # AT A z DERIVED FROM THE ROOMS, not at the cluster's label: placing the
    # corridor at the label put it through the far end of every room on the
    # deck; placing it at the deck's nominal z, before clustering existed, made
    # a body fall 263 m through empty space.
    dp = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms)
    here, lo, span, cz = dp["here"], dp["lo"], dp["span"], dp["cz"]
    stats["corridor_z"] = cz
    stats["unopened"] = dp["unopened"]
    # WITHOUT THE MOVING LEAVES -- `door_leaves` places them per door, as their
    # own meshes, so they can open. See that function.
    cv, ct, cm = it.ring_arc(schema, profile, sector, ring,
                             degrees=span, start_deg=lo, radius_m=radius,
                             z_offset=cz, doors=dp["doors"],
                             door_leaves=False)
    V.extend(cv)
    T.extend(ct)
    # NAMED WITH THE NAMES THE KIT ALREADY GAVE IT. The first version of this
    # line labelled all 458,400 corridor triangles `corridor` -- one group --
    # which fixed "untagged" by replacing fourteen real names with one fake one.
    # `materials.py`'s substring rules matched it zero times, so 77% of the deck
    # rendered with the glTF fallback material; and `FIXTURE_LIGHTING` is an
    # exact-name table, so the corridor's `light_downlight`, `light_pilaster_strip`
    # and `light_portal_head` fittings were invisible to it and the deck emitted
    # NO LIGHT SOURCES AT ALL. `ring_arc` had the spans the whole time.
    G.extend(cm["groups"])
    stats["corridor_tris"] = len(ct)
    stats["doors"] = cm["doors_at"]

    # One group per leaf, so the engine can move each independently.
    for q, door, _dx in dp["rooms"]:
        for name, lv, lt in door_leaves(radius, door["angle_deg"],
                                        door["z_m"], q["key"]):
            off, t0 = len(V), len(T)
            V.extend(lv)
            T.extend((a + off, b + off, c + off) for a, b, c in lt)
            G.append((name, t0, len(T)))
            stats["leaf_tris"] = stats.get("leaf_tris", 0) + len(lt)

        # ...and a plaque saying what is behind it. The wall the sign hangs on
        # is the RENDER wall, not the collision plane -- the same distinction
        # the vestibule below gets wrong-way-round if you take the measured
        # `half_w` for it, which put every passage 0.219 m inside the corridor.
        # `side` IS THE SIGN OF THE OFFSET, not its opposite, and getting that
        # backwards put every plaque on the FAR wall of the corridor -- 2.6 m
        # from the door it labels, facing away from it. The doors report
        # `side=-1` with `z_m` BELOW `cz`, so the wall is `cz + side*half`.
        # Caught by measuring where the geometry landed rather than by reading
        # the render, because at 2.6 m a plaque on the wrong wall still looks
        # like a plaque on a wall.
        sv, st, sg = door_sign(
            radius, door["angle_deg"],
            cz + door["side"] * K.PROVISIONAL["corridor_width_m"] / 2.0,
            door["side"], q)
        off, t0 = len(V), len(T)
        V.extend(sv)
        T.extend((a + off, b + off, c + off) for a, b, c in st)
        # Prefixed with the place, exactly as its props and people are, so a
        # room's whole contribution to the deck is addressable by one string.
        for nm, lo_, hi_ in _runs(sg):
            G.append((f"{q['key']}__{nm}", lo_ + t0, hi_ + t0))
        stats["sign_tris"] = stats.get("sign_tris", 0) + len(st)

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

    # The door's angle in the ROOM's frame: the room's local x is arc length
    # from its own centre, so `dx` is however far the corridor's bay division
    # moved the door. Rooms with no door in `deck_plan` are built sealed, which
    # is what their collision shell also is.
    opened = {q["key"]: dx for q, _d, dx in dp["rooms"]}
    for q in here:
        try:
            dx = opened.get(q["key"])
            rep = {}
            rv, rt, rg = R.build(
                schema, profile, q,
                door_at=None if dx is None else
                (dx, K.PROVISIONAL["door_width_m"],
                 K.PROVISIONAL["door_height_m"]),
                report=rep)
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

        # THE PEOPLE, IN THE RING'S FRAME AND UNDER THE NAME THE ENGINE SEES.
        # `build_deck` prefixes a room's groups with its key, so the mesh the
        # runtime finds is `<key>__npc_standing_3`; the actor record has to
        # carry that same name or the two cannot be matched. And the yaw needs
        # the room's own angular position added, because the room is rotated
        # onto the ring and the person is rotated with it.
        for act in rep.get("actors", ()):
            wx, wy, wz = _place_local(
                [(act["x"], act["y"], act["z"])], radius,
                q["angle_deg"], q["z_m"])[0]
            stats.setdefault("actors", []).append({
                "group": f"{q['key']}__{act['group']}",
                "place": q["key"], "who": act["who"], "pose": act["pose"],
                "x": wx, "y": wy, "z": wz,
                # THE YAW IS UNCHANGED BY THE WRAP, and adding the room's angle
                # to it -- which is what this line did first -- turned every
                # inhabitant by however far round the ring their room sits.
                # `_place_local` is not a rotation in the room's (x, z) plane:
                # it wraps room x onto an arc and leaves room z as the station
                # axis. So a body's heading relative to (axial, tangential) is
                # preserved, and `npc.gd` derives those two directions from the
                # body's OWN position, which is where the ring angle enters.
                "yaw": act["yaw"],
            })

        # And the passage joining it to the corridor, so the doorway frames a
        # floor rather than the black the preview renders empty space as. Only
        # where there IS a doorway: a sealed room gets no passage to nowhere.
        if dx is None:
            continue
        inner = q["z_m"] + room_interior_half_m(schema, profile, q)
        # THE RENDER PASSAGE STOPS AT THE RENDER WALL. THE COLLISION ONE STOPS
        # AT THE COLLISION WALL. They are different planes and using one number
        # for both is wrong in whichever direction you pick it.
        #
        # This ended at `cz - corridor_profile()["half_w"]`, the MEASURED
        # collision plane at 1.0806 m, and the corridor's render wall is at
        # `corridor_width_m / 2` = 1.30 m. So every vestibule on the station
        # projected 0.219 m into the corridor -- a 2.1 m box standing proud
        # inside a 3.0 m space, showing its top face and both flanks through the
        # wall. judge-3w photographed it at 2.5 m from a door and described "the
        # dark jamb pieces are the neighbouring room's wall panelling standing
        # proud through the corridor's white wall"; docs/judge3x-door-4m.png is
        # the same defect after the apertures were closed.
        #
        # It is the same 0.219 m as the collision bug earlier in this session,
        # inherited: the shell was correctly moved onto the measured plane and
        # this expression was copied along with it. The corridor's own
        # `deck_panel` spans the full width, so the render floor already covers
        # from this plane inward and the two abut with nothing between them.
        vv, vt, vg = vestibule_render(
            radius, q["angle_deg"] + math.degrees(dx / radius), inner,
            cz - K.PROVISIONAL["corridor_width_m"] / 2.0,
            K.PROVISIONAL["door_width_m"], K.PROVISIONAL["door_height_m"])
        off, t0 = len(V), len(T)
        V.extend(vv)
        T.extend((a + off, b + off, c + off) for a, b, c in vt)
        G.extend((n, lo_ + t0, hi_ + t0) for n, lo_, hi_ in vg)
        stats["vestibule_tris"] = stats.get("vestibule_tris", 0) + len(vt)
        # WHERE they went, so a gate can find them. Their group names are the
        # corridor kit's own, deliberately -- that is what makes them take the
        # same materials -- which means a name cannot tell a vestibule from the
        # corridor it opens off. Nothing could ask "does any vestibule poke
        # through the wall" until the answer was recorded here.
        stats.setdefault("vestibule_spans", []).append((t0, len(T)))
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
    # EVERY GROUP POINTS AT REAL TRIANGLES. Not "the spans sum to the triangle
    # count": the corridor's spans come from `interior_kit`'s tag stack and
    # NEST -- `wall_assembly` contains `skirt`, `rail_band` and the rest -- so
    # they legitimately sum to more than the mesh. Summing them was a proxy that
    # happened to hold while the corridor was one flat group, and it failed the
    # moment the real fourteen names came back.
    check("every group points at triangles that exist",
          all(0 <= lo <= hi <= len(t) for _n, lo, hi in g),
          f"{sum(1 for _n, lo, hi in g if not 0 <= lo <= hi <= len(t))} "
          f"of {len(g)} out of range")
    covered = set()
    for _n, lo, hi in g:
        covered.update(range(lo, hi))
    check("almost every triangle is named", len(covered) > 0.99 * len(t),
          f"{len(covered):,} of {len(t):,} triangles carry a group")

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
          f"(widest {gaps[-1][1]}) -- these are bridged by vestibules")

    # EVERY DOORWAY MUST HAVE A FLOOR ACROSS IT. Three separately-generated
    # meshes hand a walking body to one another here, and the first assembly
    # left a 0.219 m hole at all six -- a body that found one fell through and
    # accelerated outward for 30 km under spin gravity.
    holes = C.floor_holes(cv, ct, cm)
    check("there is a floor all the way from the corridor into every room",
          not holes,
          f"{len(holes)} sample points over nothing, first at {holes[:3]}")
    print(f"  {len(cm['rooms'])} doors, vestibules "
          f"{min(r['vestibule_m'] for r in cm['rooms']):.2f}-"
          f"{max(r['vestibule_m'] for r in cm['rooms']):.2f} m")

    # AND NO VESTIBULE POKES INTO THE CORRIDOR. The opposite failure to the one
    # above and it was shipped: the render passage ended on the MEASURED
    # collision plane (1.0806 m) while the corridor's render wall is at
    # `corridor_width_m / 2` (1.30 m), so a 2.1 m box stood 0.219 m proud inside
    # a 3.0 m space at all six doors, showing its top face and both flanks
    # through the wall. Measured on the built mesh rather than on the argument,
    # because the argument is exactly what was wrong.
    #
    # ON THE SHIPPED MESH, not on a probe. `build_deck` records where it put
    # each vestibule's triangles (`stats["vestibule_spans"]`) precisely so this
    # can address them: they carry the corridor kit's own group names on
    # purpose, so a name is no way to find them, and a probe built by passing
    # the right plane in is an assertion that cannot fail.
    wall_z = cz - K.PROVISIONAL["corridor_width_m"] / 2.0
    fv, ft, fg, fs = build_deck(schema, profile, "blue", 0, 0)

    # --- SIGNAGE IS A DECAL, AND THAT IS DECLARED RATHER THAN ASSUMED -------
    # Session 3x closed every open boundary edge on this deck, and then hung a
    # readable plaque beside all six doors. Lettering is FLUSH single-sided
    # quads -- which is what the reference shows, an emissive display panel
    # whose glyphs have no thickness -- so it reintroduces 3,984 edges used by
    # one triangle. A later session re-measuring closure would find that and
    # reasonably conclude something regressed.
    #
    # It did not, and the difference is checkable rather than a matter of
    # opinion. A decal cannot be a hole you see the background through if the
    # thing behind it is closed and it does not stick out past it. Both halves
    # are asserted: the deck LESS the lettering is still watertight, and every
    # letter lies inside its own plaque (`signage._selftest`). Exempting a
    # group by name without those two would be an exemption that rots.
    solid = [ft[i] for nm, lo, hi in fg if "sign_text" not in nm
             for i in range(lo, hi)]
    s_open, _s_non = K.boundary_edges(fv, solid)
    check("the deck is watertight once the lettering is set aside",
          not s_open, f"{len(s_open)} open edges in the solid geometry")
    all_open, _ = K.boundary_edges(fv, ft)
    lettering = [nm for nm, _l, _h in fg if "sign_text" in nm]
    check("...and every open edge that remains belongs to lettering",
          len(all_open) > 0 and lettering,
          f"{len(all_open)} open edges over {len(lettering)} lettering spans")
    print(f"  signage: {fs.get('sign_tris', 0):,} triangles over "
          f"{len(lettering)} lettering spans; {len(all_open)} flush-decal "
          f"edges, {len(s_open)} in the solid")
    deepest = max((fv[i][2] for lo_, hi_ in fs.get("vestibule_spans", ())
                   for tri in ft[lo_:hi_] for i in tri), default=wall_z)
    check("no vestibule stands proud of the corridor wall",
          deepest <= wall_z + 1e-6,
          f"a vestibule reaches z={deepest:.3f}, {deepest - wall_z:.3f} m past "
          f"the render wall face at {wall_z:.3f} -- it will show its top face "
          f"and both flanks through the corridor wall")

    # THE FURNITURE IS SOLID, and it has to stay solid AND stay out of the way.
    # Both directions can fail: no boxes at all is a player walking through
    # tables, and boxes that merge across a room's circulation lane is a room
    # nobody can cross. `dressing.blocks_lane` guarantees the second for
    # individual pieces; merging is what could break it, so it is asserted here
    # rather than assumed.
    pv, pt, pm = build_collision(schema, profile, "blue", 0, 0, props=True)
    check("the furniture in a room is solid",
          pm.get("prop_boxes", 0) > 0 and len(pt) > len(ct),
          f"{pm.get('prop_boxes', 0)} boxes, {len(pt) - len(ct)} triangles")
    check("no prop collision errors", not pm.get("prop_errors"),
          str(pm.get("prop_errors"))[:120])
    holes2 = C.floor_holes(pv, pt, pm)
    check("solid furniture does not take the floor away",
          not holes2, f"{len(holes2)} points, first {holes2[:3]}")

    # PEOPLE ARE NOT BAKED INTO THE WALLS. `is_solid` briefly counted `npc_`
    # groups, which put all 134 inhabitants into the station's static collision
    # as immovable obstacles -- a statue where a resident should be, and
    # permanent, because static collision is generated once. A gate, because
    # the failure is invisible: everything still assembles, walks and renders.
    check("no NPC is part of the station's static collision",
          not R.is_solid("npc_standing") and not R.is_solid("npc_seated")
          and R.is_solid("store_shelf") and R.is_solid("dress_crate"),
          "is_solid disagrees about what a body walks into")
    print(f"  {pm.get('prop_boxes', 0)} furniture boxes, "
          f"{len(pt) - len(ct):,} collision triangles for them")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _sweep():
    """Assemble every deck on the station, and say what does not.

    THE NUMBER THIS PROJECT KEPT NOT HAVING. Every gate here measured one thing
    at a time -- one room's density, one frame's exposure, one deck's walk --
    and the question the owner actually asks is "how much of the station can I
    walk in". This answers it, over the whole gazetteer, in about a minute, and
    it fails if any deck stops assembling or grows a hole in its floor.
    """
    schema, profile = it.load()
    decks = sorted({(q["sector"], q["ring"], q["deck"]) for q in dr.PLACES})
    ok, failed, deferred, holes, unopened, served = [], [], [], [], [], 0
    drum, dw_lod0 = [], 0
    for s, r, dk in decks:
        if (s, r) in NOT_RING_DECKS:
            # NOT DEFERRED ANY MORE, COUNTED. The drum is a different KIND of
            # walkable surface -- a heightfield rather than a corridor -- not an
            # absent one, and leaving it out of the whole-station number made
            # the number quietly smaller than the station. `drum_walk` builds
            # collision ground from `drum_ground.ground_patch` itself.
            import drum_walk as DW                              # noqa: PLC0415
            rows = DW.places()
            dv, dt, _dg, dm = DW.build(key=rows[0]["key"])
            if DW.holes(dv, dt, dm, n_a=8, n_z=8):
                holes.append((s, r, dk))
            served += len(rows)
            drum.append((s, r, dk, len(rows), len(dt)))
            dw_lod0 = max(dw_lod0, int(dm["drum_lod0_triangles"]))
            continue
        try:
            v, t, m = build_collision(schema, profile, s, r, dk)
        except Exception as e:                                  # noqa: BLE001
            failed.append((s, r, dk, str(e)[:70]))
            continue
        if C.floor_holes(v, t, m):
            holes.append((s, r, dk))
        unopened += [(s, r, dk) + u for u in m["unopened"]]
        served += len(m["rooms"]) + len(m["unopened"])
        ok.append((s, r, dk, len(m["rooms"]), len(t)))

    print(f"{len(decks)} decks in the gazetteer")
    print(f"  {len(ok)} assemble, {len(failed)} fail, "
          f"{len(deferred)} deferred, {len(drum)} on heightfield ground")
    for s, r, dk in deferred:
        print(f"     deferred {s}/{r}/{dk}: {NOT_RING_DECKS[(s, r)]}")
    for s, r, dk, n_loc, n_tri in drum:
        print(f"     drum {s}/{r}/{dk}: {n_loc} locations on collision ground, "
              f"{n_tri:,} triangles a tile -- {NOT_RING_DECKS[(s, r)][:44]}...")
    for f in failed:
        print(f"     FAIL {f[0]}/{f[1]}/{f[2]}: {f[3]}")
    print(f"  {served} locations on an assembled cluster, "
          f"{sum(x[3] for x in ok)} with a door, {len(unopened)} without")
    for u in unopened[:10]:
        print(f"     no door: {u}")
    print(f"  {len(holes)} decks with a hole in the floor  {holes[:5]}")
    # THE HEADLINE USED TO SUM `ok` ALONE AND CALL THAT THE STATION. It is the
    # ring decks only -- the drum takes the `continue` above and never reaches
    # this sum -- so the number printed 75,642 when the walkable station is
    # 649,082, wrong by 8.6x, and it was the drum's own ground that was missing:
    # 88% of the real total (station/budget.py, session 3w). A whole-station
    # figure that quietly excludes the largest walkable surface on the station
    # is the same defect as a gate that measures a part in isolation, one level
    # up. Per tile is what actually resides; lod0 is what exists.
    print(f"  {sum(x[4] for x in ok):,} collision triangles across the ring "
          f"decks, {sum(x[4] for x in drum):,} more in the drum's ground per "
          f"tile ({dw_lod0:,} for the whole drum at lod0) -- the walkable "
          f"station is {sum(x[4] for x in ok) + dw_lod0:,}")
    bad = len(failed) + len(holes) + len(unopened)
    if bad:
        print("A deck that does not assemble is a deck nobody can be on.")
    return 1 if bad else 0


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
    ap.add_argument("--sweep", action="store_true",
                    help="assemble every deck on the station and report")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if a.sweep:
        return _sweep()

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
                                     max_rooms=a.max_rooms, props=True)
        C.write_obj(a.collision_obj, cv, ct, cm.get("groups"))
        print(f"  wrote {a.collision_obj}: {len(ct):,} collision triangles "
              f"({len(ct) / max(1, s['corridor_tris']) * 100:.1f}% of the "
              f"corridor's render mesh), clear width {cm['half_w_m'] * 2:.3f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
