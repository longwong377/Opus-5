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

import bespoke as BSP                                           # noqa: E402
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


def deck_arc(sector, ring, deck, z_m, max_rooms=None, must_cover=None):
    """The angular span of corridor a cluster needs, and the places on it.

    Pulled out of `build_deck` so the render mesh and the collision shell are
    laid over EXACTLY the same arc rather than each recomputing it -- two copies
    of this arithmetic is one copy too many for geometry that has to agree about
    where the floor is.

    `must_cover` IS THE FIX FOR 79 OF 96 CLUSTERS BEING UNREACHABLE. Session 4g
    built `station/routes.py`, which asks the question this project had never
    asked -- can you get from here to there -- and answered 91 separate pieces.
    The largest single cause was this function: **a corridor was run over the
    arc its own ROOMS occupy**, so two clusters on one deck could sit on
    opposite sides of the ring with no arc in common, and a deck's axial spine
    had nothing to attach to.

    A corridor is not a fitting for the rooms on it. It is the deck's
    circulation, and it has to reach the deck's spine whether or not anybody
    lives at that angle. `must_cover` is that angle -- `routes.transit_angle`,
    one per sector -- and passing it takes the network from 91 pieces to 71
    with no other change.

    Extending to the angle rather than sweeping the full ring is deliberate: a
    full 360 degrees is 1,210 m of corridor a deck at r = 192 m, and the
    connectivity that is actually missing costs the shortest arc that reaches
    the spine.
    """
    here = places_on(sector, ring, deck, z_m)
    if max_rooms is not None:
        here = here[:max_rooms]
    if not here:
        raise ValueError(f"no gazetteer location on {sector}/{ring}/{deck}")
    lo = min(q["angle_deg"] for q in here) - ARC_PAD_DEG
    hi = max(q["angle_deg"] for q in here) + ARC_PAD_DEG
    if must_cover is not None:
        a = float(must_cover)
        # Reach it the short way round. A corridor that grew the long way round
        # to meet an angle 10 degrees off its end would sweep 350 degrees of
        # ring to close a 10 degree gap.
        while a < lo - 180.0:
            a += 360.0
        while a > hi + 180.0:
            a -= 360.0
        lo = min(lo, a - ARC_PAD_DEG)
        hi = max(hi, a + ARC_PAD_DEG)
    return here, lo, min(360.0, hi - lo)


def room_half_w_m(schema, profile, place):
    """Half a built room's width across the ring, as `rooms.build` sizes it."""
    w_full, _l, _r = R.room_extent_m(schema, profile, place)
    bw, _bl = R.bay_span_m(place)
    return min(w_full, bw) / 2.0


def deck_plan(schema, profile, sector, ring, deck, z_m=None, max_rooms=None,
              extra_doors=(), must_cover=None):
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
    here, lo, span = deck_arc(sector, ring, deck, z_m, max_rooms,
                              must_cover=must_cover)
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
    def rank(rooms_):
        """More rooms opened first, then doors nearest their room's centre.

        THE SECOND TERM IS NOT A REFINEMENT, and leaving it out sealed every
        single-room z-cluster on the station. The fit test above asks only
        whether the leaf lands inside the room's WALL -- which a door 1.33 m
        off centre does in a 7 m room -- so on a one-room cluster the FIRST
        phase tried already opened it, `if not unopened: break` ended the sweep
        immediately, and the door stayed wherever the bay division happened to
        put it.

        A body steering straight at the room from the corridor then crosses the
        corridor wall 0.14 m along that line and meets the jamb.
        `walkable.py --deck` measures **0.70-0.74 m of progress** into every
        such cluster -- corridor half-width 1.0806 less the capsule radius --
        including `grey/0/24 -> thieves_guild`, which STATE.md records PASSING
        in session 3v. It was a silent regression on everything except
        `blue/0/0`, whose goto target happens to sit at dx = 0.00.

        Scoring all 24 phases costs 24 door placements a cluster and puts max
        |dx| at 0.00 m on twelve of thirteen clusters measured, 0.18 m on the
        thirteenth, and improves `blue/0/0` from 1.11 m to 0.07 m. No room is
        lost and `unopened` stays 0.

        Found by the interiors agent, session 3z, on its own new room -- and
        then reproduced on untouched geometry, which is what turned "my room is
        broken" into "the station is".
        """
        return (-len(rooms_),
                round(sum(abs(dx) for _q, _d, dx in rooms_), 6))

    best = None
    for k in range(24):
        off = 2.5 * k / 24.0
        rooms, unopened = score(lo - off, min(360.0, span + off))
        if best is None or rank(rooms) < rank(best[0]):
            best = (rooms, unopened, lo - off, min(360.0, span + off))
    rooms, unopened, lo, span = best
    return {"plan": plan, "radius": radius, "z_m": z_m, "here": here,
            "lo": lo, "span": span, "cz": cz, "rooms": rooms,
            "unopened": unopened,
            # EXTRA DOORS ARE NOT ROOM DOORS. A room's door is placed by the
            # fitting rule above and may be declined; a junction door is where
            # an axial corridor meets this ring one, and declining it would
            # leave the axial run walled off at the end -- a corridor to
            # nowhere, which is worse than no corridor. They are appended
            # after the rooms so `ring_arc`'s snapping treats them the same.
            "doors": ([(q["angle_deg"], -1) for q, _d, _x in rooms]
                      + [(float(a), int(sd)) for a, sd in extra_doors])}


def _dress_solid(name):
    """Is this span a piece of FURNITURE, as opposed to the room's own fabric?

    Used for a composed room, where the module's shell and its dressing are in
    one mesh and only the second is a thing a body walks into -- the first is
    represented by `room_shell_for`. `dress_` is what `dressing.dress` prefixes
    everything it emits, including the fixtures it forwards under `dress_mp_`,
    and `npc_` is excluded for the reason `rooms.is_solid` excludes it: static
    collision is generated once and a person baked into it is a statue.
    """
    return name.startswith("dress_")


def room_geometry(schema, profile, q, dx=None, report=None):
    """A room's geometry, and WHICH build produced it. One decision, two callers.

    ONE DESCRIPTION OF ONE ROOM, and it exists because there were two. Since
    session 3z the assembler composes 23 module-owned places from their own
    modules -- the Zocalo is the Zocalo -- while `build_collision` went on
    calling `rooms.build` for its solids. So a player **saw** the Zocalo and
    **walked through** a generic bay's furniture standing in places the drawn
    room has nothing. That is hard rule 4's failure mode exactly: two
    descriptions of one thing, drifting the moment either improves.

    Returns `(verts, tris, spans, used)` with `used` in {"bespoke", "generic"}.
    `report` collects the same diagnostics `build_deck` prints.
    """
    rep = {} if report is None else report
    mod = q.get("module")
    if mod in BSP.NEAR_END:
        try:
            brep = {}
            bv, bt, bg = BSP.compose(
                schema, profile, q, room_axial_half_m(schema, profile, q),
                report=brep)
            # A COMPOSED ROOM STILL HAS TO BE ENTERABLE, and the same test the
            # assembler applies is applied here -- so collision cannot take the
            # bespoke build for a room the render fell back on, which would
            # reintroduce the divergence in the opposite direction.
            if dx is None or _mouth_clear(bv, bt, dx):
                rep.update(brep)
                return bv, bt, bg, "bespoke"
            rep["why"] = "composed room is walled at the doorway"
        except Exception as e:                                  # noqa: BLE001
            rep["why"] = f"compose raised: {str(e)[:60]}"
    rv, rt, rg = R.build(
        schema, profile, q,
        door_at=None if dx is None else
        (dx, K.PROVISIONAL["door_width_m"], K.PROVISIONAL["door_height_m"]),
        report=rep)
    return rv, rt, rg, "generic"


def build_collision(schema, profile, sector, ring, deck, z_m=None,
                    max_rooms=None, props=False, extra_doors=(),
                    must_cover=None):
    """The deck's COLLISION geometry -- what a body stands on, not what it sees.

    See `station/collision.py` for why these are different meshes. In short: the
    render corridor's deck carries a 66 mm lighting channel and 22 mm grid
    tiles, and a capsule dropped on it stands still forever while reporting that
    it is on the floor.
    """
    d = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms,
                  extra_doors=extra_doors, must_cover=must_cover)

    # The shell's holes come from the SAME door decision the corridor is cut
    # with -- `deck_plan` makes it once. Recomputing it here is what gave five
    # decks a room whose collision had a doorway and whose render was a sealed
    # box.
    #
    # AND THE JUNCTION DOORS ARE PART OF THAT DECISION. `build_deck_clusters`
    # cuts a junction aperture in the RENDER through `deck_plan(extra_doors=)`;
    # this function had no such argument, so the collision shell carried a WALL
    # where the render carries a doorway -- a body walking the axial spine is
    # stopped at 1.0 m by a surface that is not there. Nothing noticed because
    # NO COLLISION HAD EVER BEEN BUILT FOR A JOINED DECK: `tools/export_station.py`
    # wrote render meshes only. Same defect class as the five decks that once had
    # "a room whose collision carried a doorway and whose render was a sealed
    # box", one level out -- made once for the rooms and twice for the junctions.
    v, t, meta = C.corridor_shell(schema, profile, sector, ring,
                                  degrees=d["span"], start_deg=d["lo"],
                                  radius_m=d["radius"], z_offset=d["cz"],
                                  doors=([x[1] for x in d["rooms"]]
                                         + [{"angle_deg": float(a),
                                             "side": float(sd)}
                                            for a, sd in extra_doors]))
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
    _dxs = {q["key"]: dx for q, _door, dx in d["rooms"]}
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
                # THE ROOM THAT IS ACTUALLY DRAWN, not a generic stand-in. See
                # `room_geometry`: this called `R.build` unconditionally, so
                # every composed place put its solids where a generic bay's
                # furniture would have been.
                rv, rt, rg, _used = room_geometry(schema, profile, q,
                                                  dx=_dxs.get(q["key"]))
                # THE FURNITURE FROM THE ROOM THAT IS DRAWN; THE SHELL FROM
                # THE SHELL. A composed room's module geometry is one welded
                # mesh, so `prop_boxes`' connected-component rule -- which is
                # right for a generic bay, where each `_box` call is its own
                # island -- collapses the Zocalo's 702,840 triangles into ONE
                # solid filling the room. Measured: 1 box against the generic
                # build's 39. Shipping that would seal the room a player is
                # supposed to walk into, which is worse than the divergence it
                # was meant to fix.
                #
                # So the predicate takes the DRESSING and nothing else. The
                # module's own walls and floor are already represented, by
                # `room_shell_for`, as the smooth shell the
                # collision-is-not-render rule requires -- and `compose` adds
                # its furniture as separate `dress_*` islands exactly as
                # `rooms.build` does, so the component rule holds for them.
                solid = (_dress_solid if _used == "bespoke"
                         else R.is_solid)
                boxes = C.prop_boxes(rv, rt, rg, solid=solid)
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


def _mouth_clear(verts, tris, dx, w=None, h=None, eps=0.12):
    """Is the doorway into this room actually open?

    A composed room is built by a module that knows nothing about the corridor,
    so the face the vestibule arrives at may be solid. Cast a short ray STRAIGHT
    IN along the axis at door height, across the door's width, and ask whether
    anything is in the way. Cheaper and more decisive than reasoning about which
    wall a module built where.

    Returns True when the aperture is clear, which is when a body can get in.
    """
    w = w or K.PROVISIONAL["door_width_m"]
    h = h or K.PROVISIONAL["door_height_m"]
    zmax = max(p[2] for p in verts)
    hits = 0
    for i in range(-2, 3):
        px = dx + i * (w * 0.4 / 2.0)
        for fy in (0.35, 0.6, 0.85):
            py = h * fy
            for a, b, c in tris:
                p0, p1, p2 = verts[a], verts[b], verts[c]
                if min(p0[2], p1[2], p2[2]) < zmax - 1.2:
                    continue
                if (min(p0[0], p1[0], p2[0]) - eps <= px
                        <= max(p0[0], p1[0], p2[0]) + eps
                        and min(p0[1], p1[1], p2[1]) - eps <= py
                        <= max(p0[1], p1[1], p2[1]) + eps):
                    hits += 1
                    break
    return hits < 8


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


# WHICH PLACES CARRY AN ARRIVALS BOARD, and it is the port's own list rather
# than a new one: `broadcast.PA_PLACES` is where a port announcement is FOR, and
# a board is the same announcement with a longer memory. Filtered to the four
# where a passenger stands and waits -- a cargo bay has traffic and nobody
# reading about it.
ARRIVALS_BOARD_PLACES = ("arrival_concourse", "customs_north", "customs_south",
                         "bay_elevators")


def arrivals_sign(radius_m, angle_deg, z_m, side, hour=10.0, day=0,
                  gap_m=0.10):
    """The arrivals board beside one door, mapped onto the ring.

    THE SAME FOUR LINES AS `door_sign` AND FOR THE SAME REASONS -- `signage`
    authors +x across, +y up, +z out of the face; `_place_local` maps that onto
    a ring; and `side` is a HALF TURN about the vertical, not a mirror, because
    a mirror would point it the right way with every face inside-out and
    neither a render nor a closure check would see it.

    What differs is only the offset: the plaque sits beside the door at
    `door_width/2 + plaque_width/2 + gap`, and this sits beyond it, so the two
    do not overlap on the same wall.
    """
    import signage as S                                        # noqa: PLC0415
    v, t, g = S.arrivals_board(hour, day, with_post=False)
    dx = (K.PROVISIONAL["door_width_m"] / 2.0 + S.PLAQUE_W_M
          + S.BOARD_W_M / 2.0 + 2.0 * gap_m)
    # NO HEIGHT OFFSET, and that is the difference from `door_sign`.
    # `signage.board()` builds with "deck at y = 0" and its own frame already
    # starting at `MOUNT_H_M`, while `door_plaque` builds centred on zero and
    # needs `PLAQUE_CENTRE_H_M` added. Adding `MOUNT_H_M` here as well hung the
    # board at 2.70 m with its top at 4.18 -- above the soffit line, over
    # everyone's head. Caught by RENDERING IT AND LOOKING, not by an assertion:
    # a board on a wall at the wrong height still looks like a board on a wall.
    local = [(x + dx, y, z) for x, y, z in v]
    if side > 0:
        local = [(-x, y, -z) for x, y, z in local]
    return _place_local(local, radius_m, angle_deg, z_m), t, g


# The standing surfaces, and the list is `broadcast.MINIPAX_PLACES` -- where
# people queue and are processed. FACTIONS.md 13 proposes public reporting
# terminals "in the Zocalo and both customs halls" and a notice belongs
# wherever the terminal does.
NOTICE_BOARD_PLACES = ("customs_north", "customs_south", "arrival_concourse",
                       "bay_elevators")


def notice_sign(radius_m, angle_deg, z_m, side, kind="minipax", gap_m=0.10):
    """A Ministry of Peace or ISN board beside one door.

    On the OPPOSITE side of the door from the arrivals board, so a passenger
    reading when the next ship berths is not reading a recruitment notice at
    the same time -- and so the two boards do not intersect, which is the sort
    of thing a render shows and an assertion does not.
    """
    import signage as S                                        # noqa: PLC0415
    v, t, g = S.notice_board(kind, with_post=False)
    dx = (K.PROVISIONAL["door_width_m"] / 2.0 + S.PLAQUE_W_M
          + S.BOARD_W_M / 2.0 + 2.0 * gap_m)
    local = [(x - dx, y, z) for x, y, z in v]
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


# Whether a corridor's walkers are INSTANCED against the shared crowd library
# or baked into the deck mesh. Instanced is the shipping form -- 88% fewer
# triangles station-wide and the only form that can move -- and the flag exists
# so the two can be measured against each other rather than argued about.
CORRIDOR_INSTANCED = True


def build_deck(schema, profile, sector, ring, deck, with_rooms=True,
               bake_crowd=False,
               max_rooms=None, z_m=None, extra_doors=(),
               must_cover=None):
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
    dp = deck_plan(schema, profile, sector, ring, deck, z_m, max_rooms,
                   extra_doors=extra_doors, must_cover=must_cover)
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

        # THE PORT, ON A SURFACE. `station/traffic.py` models 55 movements a
        # day, a two-peaked EMT curve and the liner event, and until this call
        # existed NOTHING RENDERED ANY OF IT -- no ship arrives in geometry, no
        # bay fills, and its only reader was `broadcast.py`, which had no
        # importer at all. A board is the cheapest surface a simulation nobody
        # can otherwise see can reach, and the text is `traffic.arrivals`
        # itself, so the board cannot say something the port is not doing.
        if q["key"] in ARRIVALS_BOARD_PLACES:
            av, at, ag = arrivals_sign(
                radius, door["angle_deg"],
                cz + door["side"] * K.PROVISIONAL["corridor_width_m"] / 2.0,
                door["side"])
            off, t0 = len(V), len(T)
            V.extend(av)
            T.extend((a + off, b + off, c + off) for a, b, c in at)
            for nm, lo_, hi_ in _runs(ag):
                G.append((f"{q['key']}__{nm}", lo_ + t0, hi_ + t0))
            stats["arrivals_tris"] = (stats.get("arrivals_tris", 0)
                                      + len(at))

        # THE STANDING SURFACES. `broadcast.py` had zero importers; its ISN
        # bulletins and Ministry of Peace notices are era-locked to
        # `costume.ERA_EVENTS`, so this is the one surface on the station whose
        # CONTENT changes if the datum moves -- render the same deck at S2E01
        # and the Ministry of Peace is not on it, exactly as the armband is not
        # on a sleeve. FACTIONS.md 5.1's rule, applied to a wall.
        if q["key"] in NOTICE_BOARD_PLACES:
            nv, nt, ng = notice_sign(
                radius, door["angle_deg"],
                cz + door["side"] * K.PROVISIONAL["corridor_width_m"] / 2.0,
                door["side"],
                "minipax" if q["key"].startswith("customs") else "isn")
            off, t0 = len(V), len(T)
            V.extend(nv)
            T.extend((a + off, b + off, c + off) for a, b, c in nt)
            for nm, lo_, hi_ in _runs(ng):
                G.append((f"{q['key']}__{nm}", lo_ + t0, hi_ + t0))
            stats["notice_tris"] = stats.get("notice_tris", 0) + len(nt)

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
    stats["radius_m"] = radius
    stats["spawn"] = C.stand_at(cmeta, here[0]["angle_deg"])
    stats["spawn_at"] = here[0]["key"]

    # THINGS STANDING IN THE CORRIDOR. Session 4e, and the reason is measured
    # rather than aesthetic: eight new texture sheets landed on 131 materials
    # and the corridor frame stayed flat, so the look was chased through SSIL,
    # volumetric fog and shadow count -- all three byte-identical on/off. The
    # third is the one that explains it. Eighteen shadow casters change nothing
    # because a corridor is a smooth tube with 20 mm of relief and there is
    # NOTHING IN IT to cast a shadow of. `dressing.dress()` fills the 78 rooms
    # and has never been offered a corridor.
    #
    # FROM cmeta, NOT RECOMPUTED. `floor_r_m` and `half_w_m` are the collision
    # shell's own measured profile, so the clutter cannot stand at a different
    # floor from the one a body walks on -- hard rule 4.
    import corridor_dressing as CD                              # noqa: PLC0415
    _dr_doors = tuple(
        (d["angle_deg"] if isinstance(d, dict) else float(d[0])
         if isinstance(d, (tuple, list)) else float(d))
        for d in (stats.get("doors") or ()))
    dv, dt, dg, drep = CD.run(
        schema, profile, sector, ring, span, lo, radius, cz,
        cmeta["floor_r_m"], cmeta["half_w_m"], doors=_dr_doors,
        places=here, seed=f"{sector}/{ring}/{deck}")
    if dt:
        _base, _t0 = len(V), len(T)
        V.extend(dv)
        T.extend((a + _base, b + _base, c + _base) for a, b, c in dt)
        G.extend((n, a + _t0, b + _t0) for n, a, b in dg)
    stats["clutter"] = drep
    # NOT SOLID, AND SAID SO. `build_collision` sweeps the corridor shell and
    # the room shells; it does not read this mesh, so a player walks through
    # these. They sit outside the walking lane by construction, so nothing a
    # body would meet head-on -- but it IS a gap and naming it here is cheaper
    # than the next context rediscovering it from a render.
    stats["clutter_solid"] = False

    if not with_rooms:
        return V, T, G, stats

    # The door's angle in the ROOM's frame: the room's local x is arc length
    # from its own centre, so `dx` is however far the corridor's bay division
    # moved the door. Rooms with no door in `deck_plan` are built sealed, which
    # is what their collision shell also is.
    opened = {q["key"]: dx for q, _d, dx in dp["rooms"]}
    for q in here:
        why = ""
        try:
            dx = opened.get(q["key"])
            rep = {}
            # ONE DECISION, AND `build_collision` MAKES THE SAME ONE. The
            # bespoke-versus-generic choice used to live here and nowhere else,
            # so collision went on deriving its solids from `rooms.build` for
            # rooms this loop had composed -- a player saw the Zocalo and
            # walked through a generic bay's furniture. `room_geometry` is now
            # the single answer to "what is in this room"; see its docstring.
            rv, rt, rg, used = room_geometry(schema, profile, q, dx=dx,
                                             report=rep)
            if used == "bespoke":
                why = (f"{rep.get('dressed', 0)} dressed at "
                       f"{rep.get('density', 0):.2f}, "
                       f"{rep.get('people', 0)} people")
            else:
                why = rep.get("why", "")
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

        # A MODULE-OWNED PLACE ASSEMBLED GENERICALLY IS NOW SAID OUT LOUD.
        # `build_deck` has always called `rooms.build` unconditionally and
        # never looked at `place["module"]`, so 39 of the 106 ring-deck places
        # are owned by a bespoke module and assembled as generic bays -- and
        # nothing anywhere reported it, so every craft score taken on an
        # assembled deck has been scoring the generic bay without saying so.
        #
        # NOT SWAPPED, and the measurement is why. `station/bespoke.compare`
        # builds both for all 25 places that have a builder: generic 390,432
        # triangles against bespoke 210,702, **x0.54**. The bespoke modules are
        # SHELLS -- `rooms.build` runs `dressing` and `populace` inside itself,
        # so a generic bay arrives furnished and inhabited, while
        # `docking_bay.docking_bay` is 3,740 triangles of bay and nothing in
        # it against the generic 38,728. Swapping wholesale would take 46% of
        # the detail OFF the station.
        #
        # The right answer is bespoke shell PLUS generic dressing, and it is
        # the next increment. Until then this records the substitution with the
        # reason, because a defect nothing prints is a defect nobody fixes.
        if q.get("module"):
            stats.setdefault("module_places", []).append(
                (q["key"], q["module"], used, len(rt), why))
            if used == "generic":
                stats.setdefault("generic_for_module", []).append(
                    (q["key"], q["module"], len(rt),
                     why or ("has a builder"
                             if q["module"] in BSP.BESPOKE_GEOMETRY
                             else "no builder in bespoke.BESPOKE_GEOMETRY")))

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

    # -- AND PEOPLE IN THE CORRIDOR ITSELF ---------------------------------
    # Every inhabitant this file placed was inside a ROOM. A player spawned in
    # the corridor, walked its 126 m and met **nobody** -- on a station of
    # 250,000, in the one space the scope names twice.
    #
    # Placed from `cmeta`, which is the collision shell's OWN measurement of
    # where the floor is -- `floor_r_m`, `half_w_m`, `arc_deg`, `start_deg`,
    # `z_m` -- so the people stand on the surface the walk gate certifies and
    # a deck that moves takes them with it. Hard rule 4, applied to a crowd.
    #
    # `served` is what the deck opens onto, and it sets the density:
    # `populace.corridor_headcount` weights the station-wide 1.07 per 100 m2 by
    # the occupancy of those places at this hour, so the concourse outside
    # customs is busy at 1300 and an outer plant deck has four people on it at
    # any hour.
    try:
        import populace as _pop                                 # noqa: PLC0415
        pv, pt, pg, pstat = _pop.populate_corridor(
            f"{sector}/{ring}/{deck}", cmeta["floor_r_m"], cmeta["half_w_m"],
            cmeta["arc_deg"], cmeta["start_deg"], cmeta["z_m"],
            served=tuple(q["key"] for q, _d, _x in dp["rooms"]),
            # INSTANCED. The walkers' bodies live in
            # `populace.station_crowd_library` -- 112 shared meshes for the
            # whole station against 466,092 triangles of unique ones -- and
            # what comes back here is placements, not geometry. It is also the
            # only form they can MOVE in: an instance is a transform the
            # runtime rewrites, where a baked body is triangles welded to the
            # deck. Room occupants stay baked and stay individuals.
            instanced=CORRIDOR_INSTANCED)
    except Exception as e:                                      # noqa: BLE001
        pv, pt, pg, pstat = [], [], [], {"error": str(e)[:80]}
    if pt:
        off, t0 = len(V), len(T)
        # ALREADY IN THE RING'S WORLD FRAME. `populate_corridor` authors on the
        # ring rather than in a room's local box, so unlike every other block
        # in this function it takes no `_place_local`.
        V.extend(pv)
        T.extend((a + off, b + off, c + off) for a, b, c in pt)
        G.extend((n, lo_ + t0, hi_ + t0) for n, lo_, hi_ in pg)
        for act in pstat.get("actors", ()):
            stats.setdefault("actors", []).append(dict(act, place="corridor"))
    stats["corridor_people"] = pstat
    stats["crowd"] = pstat.get("instances", [])
    # THE RENDER PATH HAS NO RUNTIME TO INSTANCE THEM. A still frame needs
    # triangles, so `bake_crowd` writes the same placements out as geometry --
    # the SAME list, so a body in a render stands where the body in the build
    # stands. `tools/export_scene.py` passes it; the shipped deck does not.
    if bake_crowd and stats["crowd"]:
        bv2, bt2, bg2 = _pop.bake_instances(stats["crowd"])
        if bt2:
            off, t0 = len(V), len(T)
            V.extend(bv2)
            T.extend((a + off, b + off, c + off) for a, b, c in bt2)
            G.extend((n, lo_ + t0, hi_ + t0) for n, lo_, hi_ in bg2)
            stats["crowd_baked_tris"] = len(bt2)
    stats["crowd_lods"] = sorted({(r["species"], r["lod"])
                                  for r in stats["crowd"]})

    stats["triangles"] = len(T)
    return V, T, G, stats


def clusters_for(sector, ring, deck, keys):
    """The z-clusters that carry the named places, in axial order.

    BUSIEST-FIRST IS THE WRONG SELECTOR WHEN YOU KNOW WHAT YOU WANT. `blue/0/0`
    holds six clusters, and its two busiest are the docking bays at 7120 and
    C&C at 7960 -- so asking for "the top two" to stage the arrival sequence
    returns the bays and the command deck, and the customs halls at 7440 are
    not in the build at all. Ask for the places instead.
    """
    want = set(keys)
    out = {}
    for q in places_on(sector, ring, deck):
        if q["key"] in want:
            out[round(q.get("z_m", 0.0) / Z_CLUSTER_M) * Z_CLUSTER_M] = True
    return sorted(out)


# How much arc two clusters must share before a corridor can be run between
# them. A doorway is 1.50 m, which at the ring radii here is well under a
# degree; 2 degrees leaves room for `ring_arc` to snap the aperture to a bay
# centre at either end without it falling off the arc.
JOIN_MIN_ARC_DEG = 2.0
# How far a snapped junction door may land from where it was asked for before it
# counts as a different door. `ring_arc` snaps to the nearest bay centre and the
# bays are ~3.07 m, which at 192 m radius is 0.92 degrees.
JOIN_SNAP_TOL_DEG = 1.5


def build_deck_clusters(schema, profile, sector, ring, deck, n=None,
                        keys=None, join=False, join_deg=None, must_cover=None, **kw):
    """Several of a deck's z-clusters in ONE mesh. Returns (V, T, G, stats).

    THE THING THAT STOPPED THE ARRIVAL LOOP BEING ONE PLACE. `build_deck`
    assembles a single z-cluster, and that is correct -- `interior.ring_arc`
    sweeps a corridor at a FIXED z, so a ring serves the locations at its own z
    and not the ones 300 m up the station. Assembling a whole deck onto one
    ring once put rooms hundreds of metres from the floor meant to serve them,
    which the walk test found as a body falling 263 m. `Z_CLUSTER_M` and this
    module's cluster rule exist because of that.

    But "one cluster per build" is not the same statement, and it is the one
    that bit. Measured: **13 decks carry more than one z-cluster**, and
    `blue/0/0` carries SIX over 1,120 m of axis. The docking bays sit at
    z 7120 and the customs halls at 7440, one deck and two clusters -- so the
    arrival sequence's walk from ramp to queue could not exist in a single
    build, and the arrival agent reported it as 6 steps of 11 rather than
    hiding it.

    This does not join them with geometry and does not pretend to: there is no
    floor between 7120 and 7440 and inventing one would be worse than the gap.
    What it does is put both in ONE SCENE, so a transition between them is a
    transition inside a build rather than across a build boundary -- which is
    what a transport tube actually is on this station, and what
    `arrival.py` already models.

    A WRAPPER, NOT A REWRITE, and deliberately. `build_deck` is 370 lines that
    end in one `return`, with the collision meta, the spawn, the doors and the
    clutter all bound to a single cluster's `cz`. Threading a loop through it
    would put every one of those decisions in question at once. Calling it per
    cluster and merging costs a little geometry and risks nothing that is
    already tested.

    `keys=` names the PLACES that must be in the build and takes the clusters
    that carry them, which is almost always what a caller means; `n=` takes the
    busiest N; `n=None` takes every cluster the deck has. Groups are prefixed
    `zNNNN__` so
    a caller can tell which cluster a span came from -- and so two clusters'
    identically-named corridor spans do not merge into one material group.
    """
    if keys:
        zs = clusters_for(sector, ring, deck, keys)
        if not zs:
            raise ValueError(f"{sector}/{ring}/{deck} carries none of {keys}")
    else:
        zs = z_clusters(sector, ring, deck)
        if not zs:
            raise ValueError(f"{sector}/{ring}/{deck} carries no located "
                             f"cluster")
        if n is not None:
            zs = zs[:max(1, n)]
    V, T, G = [], [], []
    stats = {"clusters": [], "z": list(zs), "rooms": 0, "corridor_tris": 0,
             "room_tris": 0, "skipped": [], "joins": []}

    # THE JOINS, DECIDED BEFORE THE CLUSTERS ARE BUILT, because each end needs a
    # door in its own ring corridor and a door has to be in the plan before the
    # corridor is swept. `join_deg` is the angle the axial runs stand at; it is
    # one angle for the whole deck so the runs form a single spine rather than a
    # zigzag, and it is checked against every cluster's arc below.
    axial = sorted(zs)
    at_deg = {}
    if join and len(axial) > 1:
        # THE ANGLE IS DERIVED, NOT PASSED, and the first version passed it.
        # A cluster's corridor covers the arc its own rooms occupy: the docking
        # bays sweep -12.8 to 332.0 degrees and the customs halls 26.3 to 232.0.
        # A join at 0 degrees gets a door in the first and NOTHING in the second
        # -- `deck_plan` only cuts doors inside its own arc, so the aperture was
        # silently absent and the corridor would have arrived at a wall. Take
        # the middle of the arc EVERY cluster covers, or decline to build.
        plans = {z: deck_plan(schema, profile, sector, ring, deck, z,
                              kw.get("max_rooms"), must_cover=must_cover)
                 for z in axial}
        a_lo = max(pl["lo"] for pl in plans.values())
        a_hi = min(pl["lo"] + pl["span"] for pl in plans.values())
        if a_hi - a_lo < JOIN_MIN_ARC_DEG:
            stats["joins"].append(
                {"built": False, "from": axial[0], "to": axial[-1],
                 "why": f"the clusters' arcs share only {a_hi - a_lo:.1f} deg, "
                        f"under the {JOIN_MIN_ARC_DEG:.0f} deg a doorway needs"})
        else:
            if join_deg is None:
                join_deg = a_lo + (a_hi - a_lo) / 2.0
            stats["join_deg"] = join_deg
            stats["join_arc"] = (round(a_lo, 2), round(a_hi, 2))
            for i, z in enumerate(axial):
                hands = []
                if i:
                    hands.append(-1)        # a run arriving from lower z
                if i < len(axial) - 1:
                    hands.append(1)         # a run leaving toward higher z
                at_deg[z] = tuple((join_deg, h) for h in hands)

    for z in zs:
        v, t, g, st = build_deck(schema, profile, sector, ring, deck,
                                 z_m=z, extra_doors=at_deg.get(z, ()),
                                 must_cover=must_cover, **kw)
        base, t0 = len(V), len(T)
        V.extend(v)
        T.extend((a + base, b + base, c + base) for a, b, c in t)
        pre = f"z{int(round(z))}__"
        G.extend((pre + nm, lo + t0, hi + t0) for nm, lo, hi in g)
        cmz = st.get("collision_meta") or {}
        stats["clusters"].append({"z": z, "tris": len(t),
                                  "rooms": st.get("rooms", 0),
                                  "spawn": st.get("spawn"),
                                  "spawn_at": st.get("spawn_at"),
                                  "corridor_z": st.get("corridor_z", z),
                                  "half_w_m": cmz.get("half_w_m", 1.0806),
                                  # RADIUS OR NOTHING, AND `None` IS NOT
                                  # NOTHING. `collision_meta` is absent on a
                                  # deck whose collision assembly was skipped,
                                  # and `cmz.get("radius_m")` then handed None
                                  # to `axial_run`, which put it through
                                  # `round(gravity_at(schema, None))`. Four of
                                  # the station's 71 decks failed that way in
                                  # the first whole-station build, with a
                                  # TypeError two frames from the cause.
                                  "radius_m": (cmz.get("radius_m")
                                               or st.get("radius_m"))})
        for k in ("rooms", "corridor_tris", "room_tris"):
            stats[k] += st.get(k, 0)
        stats["skipped"] += st.get("skipped", [])

        # A JUNCTION DOOR THAT DID NOT SURVIVE IS A CORRIDOR INTO A WALL, and it
        # is silent: `ring_arc` snaps a door to the nearest bay centre and drops
        # one it cannot place, and `deck_plan` never cuts one outside its own
        # arc. So the aperture is looked for in the mesh's own `doors_at` rather
        # than assumed from what was asked.
        for want_a, want_s in at_deg.get(z, ()):
            if not any(abs(d["angle_deg"] - want_a) < JOIN_SNAP_TOL_DEG
                       and int(d["side"]) == want_s
                       for d in (st.get("doors") or ())):
                raise ValueError(
                    f"{sector}/{ring}/{deck} z={z:.0f}: the junction door at "
                    f"{want_a:.3f} deg side {want_s:+d} is not in the built "
                    f"corridor -- an axial run to it would arrive at a wall")
    # --- and now the corridor BETWEEN them ---------------------------------
    # Each run spans from one ring corridor's far wall to the next one's near
    # wall, so the two ends land exactly on the apertures cut for them above.
    # The half-width comes from the cluster's own collision meta rather than
    # being recomputed -- hard rule 4, the same reason the corridor clutter
    # reads it from there.
    # DECLINING TO BUILD HAS TO ACTUALLY DECLINE. When two clusters' arcs share
    # under JOIN_MIN_ARC_DEG the block above records a `joins` entry saying so
    # and leaves `join_deg` unset -- and this loop then ran anyway and put None
    # through `math.radians`. Four of the station's 71 decks failed that way in
    # the first whole-station build, with a TypeError two frames from the cause
    # and a manifest entry that read like a geometry problem.
    #
    # A refusal that is recorded but not obeyed is worse than no refusal: it
    # produces a report saying the right thing and a crash saying nothing.
    _joinable = (join and len(axial) > 1
                 and stats.get("join_deg") is not None)
    for a, b in zip(axial, axial[1:]) if _joinable else ():
        ca = next(c for c in stats["clusters"] if c["z"] == a)
        cb = next(c for c in stats["clusters"] if c["z"] == b)
        za = ca["corridor_z"] + ca["half_w_m"]
        zb = cb["corridor_z"] - cb["half_w_m"]
        if zb - za < 1.0:
            stats["joins"].append({"from": a, "to": b, "built": False,
                                   "why": f"only {zb - za:.2f} m between them"})
            continue
        jv, jt, jm = it.axial_run(schema, profile, sector, ring, za, zb,
                                  angle_deg=join_deg, radius_m=ca["radius_m"],
                                  door_leaves=False)
        base, t0 = len(V), len(T)
        V.extend(jv)
        T.extend((x + base, y + base, c + base) for x, y, c in jt)
        pre = f"join{int(round(a))}_{int(round(b))}__"
        G.extend((pre + nm, lo_ + t0, hi_ + t0) for nm, lo_, hi_ in jm["groups"])
        jm["built"] = True
        jm["from"] = a
        jm["to"] = b
        stats["joins"].append(jm)
        stats["corridor_tris"] += len(jt)

    stats["tris"] = len(T)
    return V, T, G, stats


def build_collision_clusters(schema, profile, sector, ring, deck, n=None,
                             keys=None, join=False, join_deg=None,
                             must_cover=None, **kw):
    """The COLLISION for a joined deck -- every cluster's shell plus the axial
    spine that connects them. Returns (V, T, meta).

    THE MIRROR OF `build_deck_clusters`, AND IT DID NOT EXIST. That function
    assembles the render mesh for a deck's clusters and runs an axial corridor
    between them; `tools/export_station.py` wrote 70 decks and 2.3 GB of it. No
    collision was ever built for any of them, so the whole exported station was
    geometry a body could walk through -- and the defect that hid inside that
    absence was `build_collision` having no `extra_doors`, which put a WALL in
    the shell where the render has a junction doorway.

    Every decision here is READ FROM THE SAME `deck_plan` CALL the render used,
    not recomputed: the arc, the phase, the room doors and the junction doors.
    Two copies of that arithmetic is what once gave five decks a room whose
    collision carried a doorway and whose render was a sealed box.
    """
    zs = (clusters_for(sector, ring, deck, keys) if keys
          else z_clusters(sector, ring, deck))
    if not zs:
        raise ValueError(f"{sector}/{ring}/{deck} carries no located cluster")
    if n is not None and not keys:
        zs = zs[:max(1, n)]
    axial = sorted(zs)
    at_deg = {}
    if join and len(axial) > 1:
        plans = {z: deck_plan(schema, profile, sector, ring, deck, z,
                              kw.get("max_rooms"), must_cover=must_cover)
                 for z in axial}
        a_lo = max(pl["lo"] for pl in plans.values())
        a_hi = min(pl["lo"] + pl["span"] for pl in plans.values())
        if a_hi - a_lo >= JOIN_MIN_ARC_DEG:
            if join_deg is None:
                join_deg = a_lo + (a_hi - a_lo) / 2.0
            for i, z in enumerate(axial):
                hands = ([-1] if i else []) + ([1] if i < len(axial) - 1 else [])
                at_deg[z] = tuple((join_deg, h) for h in hands)

    V, T = [], []
    metas, cz = [], {}
    for z in zs:
        v, t, m = build_collision(schema, profile, sector, ring, deck, z_m=z,
                                  extra_doors=at_deg.get(z, ()),
                                  must_cover=must_cover, **kw)
        base = len(V)
        V.extend(v)
        T.extend((a + base, b + base, c + base) for a, b, c in t)
        metas.append(m)
        cz[z] = m

    joins = []
    for a, b in zip(axial, axial[1:]) if at_deg else ():
        ma, mb = cz[a], cz[b]
        za = ma["z_m"] + ma["half_w_m"]
        zb = mb["z_m"] - mb["half_w_m"]
        if zb - za < 1.0:
            continue
        jv, jt, jm = C.axial_shell(schema, profile, sector, ring, za, zb,
                                   angle_deg=join_deg,
                                   radius_m=ma["radius_m"])
        base = len(V)
        V.extend(jv)
        T.extend((x + base, y + base, c + base) for x, y, c in jt)
        joins.append(jm)

    return V, T, {"clusters": metas, "joins": joins, "join_deg": join_deg,
                  "triangles": len(T), "z": list(zs),
                  "spawn_meta": metas[0]}


def build_column(schema, profile, sector, ring, angle_deg, z_m, decks=None,
                 at_deck=None):
    """A sector's TRANSIT COLUMN at one angle: the lift shaft, its car and its
    collision, serving every deck of a ring. Returns (V, T, G, stats).

    THE PIECE THAT TURNS 71 WALKABLE ISLANDS INTO ONE STATION. `routes.py`
    measures the station's circulation graph and, before this existed, read
    **71 components -- exactly one per deck**, because every deck was internally
    connected by its axial spine and nothing joined one deck to the next. There
    was no lift, stair or shaft anywhere in the project, while `transit.py`
    costed the ride and `npc/navigation.py` routed NPCs through it.

    `angle_deg` is NOT chosen here. It is the sector's transit angle --
    `routes.transit_angle`, the angle lying inside the most cluster arcs -- and
    it is passed in rather than computed because `routes` imports this module
    and the dependency cannot run both ways. The same angle goes to
    `deck_plan(must_cover=)`, which is what guarantees every cluster's corridor
    reaches the column instead of stopping wherever its own rooms end.
    """
    import lift as L                                           # noqa: PLC0415
    if decks is None:
        decks = [d["deck_index"] for d in it.decks_in_ring(schema, profile,
                                                           sector, ring)]
    decks = sorted(decks)
    at = decks[0] if at_deck is None else at_deck

    V, T, G = [], [], []
    sv, st_, smeta = L.lift_shaft(schema, profile, sector, ring, decks,
                                  angle_deg, z_m)
    V.extend(sv)
    T.extend(st_)
    G.extend(("column__" + n, a, b) for n, a, b in smeta.get("groups", ()))

    cv, ct, cmeta = L.lift_car(schema, profile, sector, ring, decks,
                               angle_deg, z_m, at_deck=at)
    base, t0 = len(V), len(T)
    V.extend(cv)
    T.extend((a + base, b + base, c + base) for a, b, c in ct)
    G.extend(("column__" + n, a + t0, b + t0)
             for n, a, b in cmeta.get("groups", ()))

    xv, xt, xmeta = L.lift_collision(schema, profile, sector, ring, decks,
                                     angle_deg, z_m, at_deck=at)
    return V, T, G, {"shaft": smeta, "car": cmeta,
                     "collision": (xv, xt, xmeta),
                     "decks": decks, "at_deck": at,
                     "angle_deg": angle_deg, "z_m": z_m,
                     "tris": len(T), "collision_tris": len(xt)}


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

    # --- THE PORT IS ON A SURFACE ----------------------------------------
    # `station/traffic.py` models 55 movements a day and until the arrivals
    # board existed NOTHING RENDERED ANY OF IT. This asserts the board is in
    # the deck and, more importantly, that its TEXT TRACKS THE PORT -- a board
    # showing a fixed list would look identical in a render and be worthless.
    import signage as _S                                        # noqa: PLC0415
    n_board = fs.get("arrivals_tris", 0)
    check("the arrivals board is in the assembled deck",
          n_board > 0, f"{n_board} triangles")
    early = _S.arrivals_lines(4.0, 0)
    late = _S.arrivals_lines(10.0, 0)
    check("...and it says different things at different hours, because the "
          "text comes from traffic.arrivals and not from a table",
          early != late,
          f"04h {early[2][:24]!r} against 10h {late[2][:24]!r}")
    check("...and a different day is different again",
          _S.arrivals_lines(10.0, 1) != late)
    # The one row a player would actually notice, and it is the manifest's
    # own event: a liner day puts a liner on the board.
    import traffic as _tf                                       # noqa: PLC0415
    lday = next((d for d in range(8) if _tf.liner_today(d)), None)
    la = (next((a for a in _tf.arrivals(lday) if a["type"] == "liner"), None)
          if lday is not None else None)
    if la is not None:
        board = _S.arrivals_lines(la["hour"] - 0.5, lday)
        check("...and a liner day puts the liner on the board",
              any("LINER" in ln for ln in board),
              f"day {lday} at {la['hour']:.1f} h: "
              f"{[ln for ln in board if 'LINER' in ln]}")
    print(f"  arrivals board: {n_board:,} triangles, "
          f"{len(late) - 2} movements listed at 10h; "
          f"04h lists {early[2].split()[0] if len(early) > 2 else '--'}, "
          f"10h lists {late[2].split()[0] if len(late) > 2 else '--'}")

    # --- THE ERA IS ON THE WALL ------------------------------------------
    # The sharpest assertion available on this deck, because it is about
    # CONTENT and not geometry: render the same corridor at S2E01 and the
    # Ministry of Peace is not on it, exactly as the armband is not on a
    # sleeve. FACTIONS.md 5.1 -- "any armband before The Fall of Night is an
    # error" -- applied to a board.
    n_notice = fs.get("notice_tris", 0)
    check("the standing notice board is in the assembled deck",
          n_notice > 0, f"{n_notice} triangles")
    now = _S.notice_lines("minipax", (3, 5))
    before = _S.notice_lines("minipax", (2, 1))
    check("...and at the S3E05 datum it carries the Ministry of Peace",
          any("NIGHTWATCH" in ln or "REPORT" in ln for ln in now),
          f"{now[2:4]}")
    check("...and BEFORE The Fall of Night it does not -- the board's content "
          "is era-locked at source, so the same deck renders differently at "
          "S2E01",
          not any("NIGHTWATCH" in ln for ln in before)
          and before != now,
          f"S2E01 {before[2:]!r}")
    check("...and it is not BLANK either -- a dark lit panel in a customs "
          "hall reads as a broken prop, so it falls back to the "
          "authority-1 civic text",
          len(before) > 2 and before[2],
          f"{before[2] if len(before) > 2 else '(empty)'!r}")
    print(f"  notice board: {n_notice:,} triangles; at S3E05 "
          f"{now[2][:30]!r}, at S2E01 {before[2][:30]!r}")

    # --- WHOSE GEOMETRY IS A PLAYER STANDING IN --------------------------
    # `build_deck` calls `rooms.build` for every room and has never consulted
    # `place["module"]`. That is a real substitution and it was SILENT, which
    # is the part that mattered: every craft score taken on an assembled deck
    # has been scoring a generic bay wherever a bespoke module owns the place,
    # and no output anywhere said so.
    #
    # This does not assert that the substitution is absent -- it is present, on
    # purpose, because `bespoke.compare` measures the swap as x0.54 and a
    # wholesale swap would take 46% of the station's detail off. It asserts the
    # substitution is REPORTED, with a module name and a reason, so it cannot
    # go quiet again. A defect nothing prints is a defect nobody fixes.
    gen = fs.get("generic_for_module", [])
    owned = [q for q in here_all if q.get("module")]
    # COUNTED AGAINST `module_places`, NOT `generic_for_module`, and the change
    # is the point. This asserted that EVERY module-owned place came back
    # generic -- which was true while the assembler composed nothing, and which
    # would fail the moment one was fixed. It passed today only because the
    # cluster it tests has no composed place left on it, so it was an assertion
    # that could only ever punish progress.
    #
    # `module_places` carries every module-owned place with `used` in
    # {bespoke, generic}, so counting it preserves exactly what this gate was
    # written for -- the substitution cannot go quiet -- and survives the
    # substitution being fixed, which is the outcome it exists to encourage.
    # Found by the composition agent while closing 23 of them.
    check("every module-owned place on this deck is accounted for",
          len(fs.get("module_places", [])) == len(owned),
          f"{len(fs.get('module_places', []))} reported against {len(owned)} "
          f"module-owned places")
    check("...each with a module name and a stated reason",
          all(m and w for _k, m, _n, w in gen), str(gen[:2]))
    # THREE REASONS NOW, NOT TWO. This asserted that the reason is exactly
    # "has a builder" or "has none", which was true while the assembler never
    # tried. It tries now, and a third outcome appeared immediately: a composed
    # room that is WALLED AT ITS DOORWAY. `docking_bay`'s crew end is a
    # bulkhead -- correct for a bay whose other end is vacuum -- and no bespoke
    # builder takes `door_at`, so the aperture is whatever the module put
    # there. The gate has to admit the reason the build actually gives.
    ok_reasons = ("has a builder", "no builder in bespoke.BESPOKE_GEOMETRY",
                  "composed room is walled at the doorway")
    check("...and every reason is one the assembler can actually give",
          all(w in ok_reasons for _k, _m, _n, w in gen),
          str([(m, w) for _k, m, _n, w in gen]))
    check("...and 'no builder' is said only of modules that have none",
          all((w != "no builder in bespoke.BESPOKE_GEOMETRY")
              == (m in BSP.BESPOKE_GEOMETRY) for _k, m, _n, w in gen),
          str([(m, w) for _k, m, _n, w in gen]))
    withb = [r for r in gen if r[3] == "has a builder"]
    print(f"  module-owned: {len(gen)} assembled generically, "
          f"{len(withb)} of them have an unused builder "
          f"({', '.join(sorted({r[1] for r in withb})) or 'none'})")
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

    # -- COLLISION FOLLOWS THE COMPOSITION ---------------------------------
    # A player SAW the Zocalo and WALKED THROUGH a generic bay's furniture:
    # `build_deck` composed 23 module-owned places from their own modules while
    # `build_collision` went on calling `rooms.build` for its solids. Two
    # descriptions of one room, which is hard rule 4's failure mode.
    zq = next((x for x in dr.PLACES if x["key"] == "zocalo"), None)
    if zq is not None:
        zv, zt, zg, zused = room_geometry(schema, profile, zq, dx=0.0)
        check("the Zocalo's collision comes from the Zocalo", zused == "bespoke",
              f"room_geometry returned {zused}")
        dressed = C.prop_boxes(zv, zt, zg, solid=_dress_solid)
        check("...and its furniture is a room full of separate objects",
              20 < len(dressed) < 400, f"{len(dressed)} solids")
        # THE NEGATIVE CONTROL, and it is the trap this nearly walked into. A
        # composed room's module geometry is ONE WELDED MESH, so `is_solid` --
        # right for a generic bay, where every `_box` call is its own island --
        # collapses the whole room into a single solid. Shipping that would
        # SEAL a room the player is meant to walk into.
        whole = C.prop_boxes(zv, zt, zg)
        check("BREAK: taking the whole composed mesh instead collapses it to "
              "ONE solid filling the room -- which would seal it",
              len(whole) <= 2 and len(whole) < len(dressed) / 10,
              f"{len(whole)} solids against {len(dressed)} dressing-only")
        # AND BOTH CALLERS AGREE, which is the property that was missing.
        gv2, gt2, gg2, gused = room_geometry(schema, profile, zq, dx=0.0)
        check("...and the two callers get the same room, by construction",
              gused == zused and len(gt2) == len(zt),
              f"{gused}/{len(gt2)} against {zused}/{len(zt)}")

    # -- MULTI-CLUSTER ASSEMBLY: the arrival route in one build --------------
    # `blue/0/0` carries six z-clusters over 1,120 m and `build_deck` assembles
    # ONE, so the walk from the docking ramp to the customs queue could not
    # exist in a single build. These three places are the arrival sequence's
    # first half and they must come back in one mesh.
    _route = ("docking_bays", "customs_north", "arrival_concourse")
    _zc = clusters_for("blue", 0, 0, _route)
    check("the arrival route spans more than one z-cluster, which is the "
          "reason build_deck_clusters exists",
          len(_zc) > 1, f"clusters {_zc}")
    _rv, _rt, _rg, _rst = build_deck_clusters(
        schema, profile, "blue", 0, 0, keys=_route, with_rooms=True)
    _missing = [k for k in _route
                if not any(k in n for n, _a, _b in _rg)]
    check("...and one build holds every place on it",
          not _missing, f"missing {_missing}")
    check("...each cluster keeping its own group namespace",
          len({n.split("__")[0] for n, _a, _b in _rg}) == len(_zc),
          str(sorted({n.split("__")[0] for n, _a, _b in _rg})))
    # THE CONTROL: the busiest-first selector does NOT contain the route, which
    # is what makes `keys=` load-bearing rather than a convenience. blue/0/0's
    # two busiest are the bays at 7120 and C&C at 7960; customs is at 7440.
    _busy = z_clusters("blue", 0, 0)[:2]
    check("...and busiest-first would have MISSED customs, which is why "
          "`keys=` exists",
          _zc != sorted(_busy), f"busiest {sorted(_busy)} vs route {_zc}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _modcount(rows):
    out = {}
    for _k, mod, _n, _why in rows:
        out[mod] = out.get(mod, 0) + 1
    return out


def _pop_per_100m2():
    import populace as _pop                                     # noqa: PLC0415
    return _pop.CORRIDOR_PER_100M2


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
    ok, failed, deferred, holes, unopened = [], [], [], [], []
    # A SET OF KEYS, not a running total. Clusters are 40 m apart and a
    # place within `Z_CLUSTER_M` of two corridors is legitimately served by
    # both, so summing per-cluster room counts reported 130 locations on a
    # station that has 118. A coverage number that can exceed its own
    # denominator is not a coverage number.
    served, withdoor = set(), set()
    walkers = room_people = 0
    walk_area = 0.0
    drum, dw_lod0, generic, clusters = [], 0, [], 0
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
            served.update(x["key"] for x in rows)
            withdoor.update(x["key"] for x in rows)
            drum.append((s, r, dk, len(rows), len(dt)))
            dw_lod0 = max(dw_lod0, int(dm["drum_lod0_triangles"]))
            continue
        # EVERY Z-CLUSTER, NOT JUST THE BUSIEST, and that one word was the
        # difference between 99 and 118 locations. A "deck" in the gazetteer is
        # not a z-slice -- Blue ring 0 deck 0 holds sixteen locations spread
        # over 1,100 m of the station's axis in six clusters -- and a ring
        # corridor serves the cluster at ITS z, so a deck needs one corridor
        # per cluster. The sweep built `z_clusters(...)[0]` alone and reported
        # the rest as simply absent, which quietly wrote off **C&C, both
        # customs halls, the arrival concourse, the cobra bays, Medlab Green,
        # hydroponics and both observation domes** -- nineteen locations, and
        # not the unimportant nineteen.
        for zi, zc in enumerate(z_clusters(s, r, dk) or [None]):
            try:
                v, t, m = build_collision(schema, profile, s, r, dk, z_m=zc)
            except Exception as e:                              # noqa: BLE001
                failed.append((s, r, dk, f"z={zc}: {str(e)[:60]}"))
                continue
            if C.floor_holes(v, t, m):
                holes.append((s, r, dk, zc))
            try:
                _v2, _t2, _g2, st2 = build_deck(schema, profile, s, r, dk,
                                                z_m=zc)
                generic += st2.get("generic_for_module", [])
                # HOW MANY PEOPLE ARE IN THE CORRIDORS. The only place the
                # whole-station total can be checked against the derivation it
                # comes from -- 250,000 residents x 50.8 min a day of walking
                # over 825,066 m2 of corridor is 8,812 at any instant, and
                # `populace.corridor_headcount` distributes exactly that by
                # what each deck serves. A per-deck number cannot show whether
                # the distribution conserves the total; this can.
                cp = st2.get("corridor_people") or {}
                walkers += int(cp.get("placed", 0))
                walk_area += float(cp.get("area_m2", 0.0))
                # COUNTED BY PLACE, NOT BY SUBTRACTION. This was
                # `len(actors) - placed`, which assumed the corridor's walkers
                # are in the cast list. They are not, and must not be: an
                # instanced walker has no baked mesh, so `npc.gd::collect`
                # would search for parts that do not exist. The subtraction
                # therefore removed the walker count from a list that never
                # held them and reported 90 people in the station's rooms
                # where there are 1,053 -- exactly 1,053 - 963.
                room_people += sum(1 for a in st2.get("actors", ())
                                   if a.get("place") != "corridor")
            except Exception:                                   # noqa: BLE001
                pass
            unopened += [(s, r, dk) + u for u in m["unopened"]]
            served.update(x["key"] for x in m["rooms"])
            withdoor.update(x["key"] for x in m["rooms"])
            served.update(u[0] for u in m["unopened"])
            ok.append((s, r, dk, len(m["rooms"]), len(t)))
            clusters += 1

    print(f"{len(decks)} decks in the gazetteer, {clusters} z-clusters "
          f"assembled across them")
    print(f"  {len(ok)} assemble, {len(failed)} fail, "
          f"{len(deferred)} deferred, {len(drum)} on heightfield ground")
    for s, r, dk in deferred:
        print(f"     deferred {s}/{r}/{dk}: {NOT_RING_DECKS[(s, r)]}")
    for s, r, dk, n_loc, n_tri in drum:
        print(f"     drum {s}/{r}/{dk}: {n_loc} locations on collision ground, "
              f"{n_tri:,} triangles a tile -- {NOT_RING_DECKS[(s, r)][:44]}...")
    for f in failed:
        print(f"     FAIL {f[0]}/{f[1]}/{f[2]}: {f[3]}")
    print(f"  {len(served)} of {len(dr.PLACES)} locations on an assembled "
          f"cluster, "
          f"{len(withdoor)} with a door or on ground, "
          f"{len(served - withdoor)} without")
    for u in unopened[:10]:
        print(f"     no door: {u}")
    print(f"  {len(holes)} decks with a hole in the floor  {holes[:5]}")
    if walk_area > 0.0:
        # THE ASSEMBLED CORRIDORS ARE BUSIER THAN THE STATION AVERAGE AND THAT
        # IS THE DISTRIBUTION WORKING. The 1.07 per 100 m2 is 8,812 walkers
        # over all 825,066 m2 of ring corridor, most of it in the 105 Grey
        # plant decks nobody lives on. What assembles here is the 90 clusters
        # that HAVE places on them, so a factor of about two is expected --
        # read a figure BELOW the derivation as the defect, not one above it.
        print(f"  {walkers:,} people walking in the corridors and "
              f"{room_people:,} in the rooms, over {walk_area:,.0f} m2 of "
              f"assembled corridor: {walkers / walk_area * 100.0:.2f} per "
              f"100 m2 against the station-wide {_pop_per_100m2():.2f} the "
              f"250,000-resident derivation gives. Assembled clusters are the "
              f"ones with rooms on them, so above the average is right")
    # WHOSE GEOMETRY A PLAYER IS ACTUALLY STANDING IN. `build_deck` calls
    # `rooms.build` for every room and never consults `place["module"]`, so a
    # module-owned place is assembled as a generic bay -- and nothing said so
    # until now, which meant every craft score taken on an assembled deck was
    # scoring the generic bay silently. Printed here because this is the only
    # gate that asks a whole-station question.
    if generic:
        withb = sum(1 for r in generic if r[3] == "has a builder")
        print(f"  {len(generic)} module-owned places assembled as GENERIC bays "
              f"({withb} of them have a bespoke builder that was not used)")
        for m, n in sorted(_modcount(generic).items(), key=lambda kv: -kv[1]):
            print(f"     {n:3d}x {m}")
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
    # COVERAGE IS A GATE NOW, not a line of prose. The sweep is the only thing
    # here that asks a whole-station question, and it spent sessions reporting
    # 99 of 118 as though the other nineteen were a known limitation rather
    # than one unasked-for `[0]`. A number that only ever gets read by a human
    # is a number that drifts.
    if len(served) < len(dr.PLACES):
        miss = sorted({q["key"] for q in dr.PLACES} - served)
        print(f"  {len(miss)} locations on NO assembled cluster: {miss[:8]}")
    bad = (len(failed) + len(holes) + len(unopened)
           + (len(dr.PLACES) - len(served)))
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
