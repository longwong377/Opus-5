#!/usr/bin/env python3
"""Fill every room on the station with objects, from rules.

WHY THIS IS A GENERATOR AND NOT A ROOM. The owner, session 3u: *"Can't you come
up with procedural generation systems that fill in the station in it's totality?
What I want to avoid is spending a billion sessions and tokens on one fucking
room when there's an entire goddamn space station to build."* They are right, and
this project already has the proof: the articulation pass in 3s moved all 68
procedural rooms in one commit because it was a generator rather than a room, and
`greeble.py` puts 70,778 triangles of surface detail on the hull from rules that
nobody placed by hand. The interior had no equivalent, which is why it measured
95.9% architecture, 1.7% fixtures and 2.5% props -- 311 prop instances in the
whole station, about 4.5 per room.

WHAT WAS ACTUALLY WRONG WITH THE OLD PROPS, and it was not only the count.
`rooms.PROPS` defines a prop as `(width, depth, height, mount)` -- a prop IS a
box. Placing more of them places more boxes. So this module carries parametric
BUILDERS: a chair has legs and a back, a crate has a lid and corner irons, a
locker has doors and a handle. Form first, then count.

THE THREE RULES THAT FILL A ROOM, in the order they run:

  1. FURNITURE goes against the walls and into the corners, because that is
     where furniture goes and because the middle of a room is circulation. The
     free channel is read from `rooms.lateral_stack`, the same bookkeeping the
     fixtures already use, so nothing lands inside a workbench.
  2. SURFACE SCATTER puts small objects on every horizontal face above a size
     threshold -- tabletops, shelves, crate lids, counter runs. This is where
     the density in a Starfield frame actually comes from: not big objects, but
     the clipboard, the mug, the tool roll and the stack of cases on top of the
     big objects. One rule, hundreds of instances.
  3. SERVICES hang off the walls and ceiling -- conduit drops, cable loops,
     wall boxes, signage. Cheap, and they break up the flat planes the
     articulation pass left.

Everything is deterministic from `blake2b(key)`, never `random` and never
`str.__hash__`, which is salted per process and would redress the station on
every run. Same discipline as `greeble.py`, `garden.py` and `npc/names.py`.
"""
import hashlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _u(*parts):
    """Deterministic unit float from a key."""
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def _pick(seq, *key):
    return seq[int(_u(*key) * len(seq)) % len(seq)]


def _box(v, t, g, name, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    _tag(g, name, t0, len(t))


def _tag(g, name, lo, hi):
    """Record a span, or do not, if the caller asked for no span.

    `g=None` means "this geometry belongs to whatever group already owns it".
    The MACHINERY builders below need that: a vessel's shell, its domed head and
    its flanges are all the same clad surface as the fixture they replace, so
    they are covered by the fixture's own outer span and must NOT be recorded
    again. A second span over the same triangles would be a second AABB in
    `rooms._solid_boxes` overlapping the first, and the interpenetration gate --
    correctly -- would call that two solids in one place.
    """
    if g is not None and hi > lo:
        g.append((name, lo, hi))


def _cyl(v, t, g, name, cx, cz, y0, y1, r, seg=6, phase=0.0):
    """An upright capped cylinder: conduit drops, pipe bands, bollards.

    THIS PRIMITIVE WAS INSIDE-OUT AND OPEN, and both were found by the same
    measurement in session 3x. `_box` beside it is 12/12 outward-facing and
    `interior_kit._prism` is 12/12; this was **0/24**. Every face of every
    cylinder in the station's furniture pointed into its own body, which with
    backface culling on is an object you look straight through -- the exact
    failure CLAUDE.md records `_box` having had for several sessions of exterior
    work, where it only changed the shading, repeated indoors where it does not.

    It was also capped at the top only, which is where all 102 of an assembled
    deck's remaining boundary edges lived -- six an object over seventeen
    objects. Six triangles an end is what closure costs.

    Neither defect could be seen in a render: an inward-facing surface and a
    missing one both show the background, and the background is black.
    """
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg + phase
        dx, dz = r * math.cos(a), r * math.sin(a)
        v.append((cx + dx, y0, cz + dz))
        v.append((cx + dx, y1, cz + dz))
    t0 = len(t)
    for k in range(seg):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % seg)
        t += [(a0, b0 + 1, b0), (a0, a0 + 1, b0 + 1)]
    c = len(v)
    v.append((cx, y1, cz))
    for k in range(seg):
        t.append((c, n0 + 2 * ((k + 1) % seg) + 1, n0 + 2 * k + 1))
    c0 = len(v)
    v.append((cx, y0, cz))
    for k in range(seg):
        t.append((c0, n0 + 2 * k, n0 + 2 * ((k + 1) % seg)))
    _tag(g, name, t0, len(t))


# --- the kit ---------------------------------------------------------------
# Each builder takes (v, t, g, x, y, z, w, d, h, seed) and puts one object with
# its base at y, centred on (x, z). Dimensions are the archetype's, so a builder
# can be swapped for another of the same footprint without moving anything.

# THE FURNITURE GOES THROUGH THE SAME KIT AS THE MACHINERY -- INV-132.
# Measured rather than assumed: a ray cast across the medlab's half-distance
# frame after INV-130 lands on `dress_top` 27 times of 119 -- more than any
# other group and more than the articulated gantry it was standing next to.
# The fixtures and the declared props were raised and the FURNITURE was still
# the flattest thing in the room, which is the same finding one object down.
#
# Only the five that stand up and read at a distance are routed. A chair, a bin
# and a drum can are already legs-and-a-back rather than boxes, and there are
# four chairs per ten metres of wall in a hospitality room -- spending a
# cabinet's triangle count on each would buy a silhouette nobody sees and cost
# the frame budget a rack.
def _mach(v, t, g, kind, name, x, y, z, w, d, h, seed):
    machine(v, t, g, kind, name, (x - w / 2, y, z - d / 2),
            (x + w / 2, y + h, z + d / 2), seed)


def _crate(v, t, g, x, y, z, w, d, h, seed):
    """A shipping case: body, proud lid, corner irons and banding."""
    _mach(v, t, g, "crate", "dress_crate", x, y, z, w, d, h, seed)


def _chair(v, t, g, x, y, z, w, d, h, seed):
    """Four legs, a seat and a back. Not a cube."""
    lw = 0.04
    for sx in (-1, 1):
        for sz in (-1, 1):
            _box(v, t, g, "dress_metal",
                 (x + sx * (w / 2 - lw), y, z + sz * (d / 2 - lw)),
                 (x + sx * (w / 2 - lw) + lw, y + h * 0.55,
                  z + sz * (d / 2 - lw) + lw))
    _box(v, t, g, "dress_soft", (x - w / 2, y + h * 0.55, z - d / 2),
         (x + w / 2, y + h * 0.62, z + d / 2))
    _box(v, t, g, "dress_soft", (x - w / 2, y + h * 0.62, z + d / 2 - 0.07),
         (x + w / 2, y + h, z + d / 2))


def _table(v, t, g, x, y, z, w, d, h, seed):
    """Kick recess, apron, nosed top and a front broken into panels."""
    _mach(v, t, g, "counter", "dress_top", x, y, z, w, d, h, seed)


def _locker(v, t, g, x, y, z, w, d, h, seed):
    """A cubicle line-up: plinth, doors with reveals, louvres and handles."""
    _mach(v, t, g, "cabinet", "dress_top", x, y, z, w, d, h, seed)


def _console(v, t, g, x, y, z, w, d, h, seed):
    """A raked face, a bezel, a screen, a knee recess and a vent row."""
    _mach(v, t, g, "console", "dress_top", x, y, z, w, d, h, seed)


def _shelf(v, t, g, x, y, z, w, d, h, seed):
    """Uprights, rails, shelves with edge lips -- and STOCK on the shelves."""
    _mach(v, t, g, "rack", "dress_top", x, y, z, w, d, h, seed)


def _bin(v, t, g, x, y, z, w, d, h, seed):
    _cyl(v, t, g, "dress_metal", x, z, y, y + h, min(w, d) / 2)


def _drum_can(v, t, g, x, y, z, w, d, h, seed):
    r = min(w, d) / 2
    _cyl(v, t, g, "dress_metal", x, z, y, y + h, r)
    for k in (0.3, 0.7):
        _cyl(v, t, g, "dress_band", x, z, y + h * k, y + h * k + 0.04, r * 1.04)


BUILDERS = {
    "crate": _crate, "chair": _chair, "table": _table, "locker": _locker,
    "console": _console, "shelf": _shelf, "bin": _bin, "can": _drum_can,
}

# What stands against a wall, by room archetype. Each entry is
# (builder, w, d, h, how many per 10 m of wall).
SCHEMES = {
    "commerce": [("shelf", 1.6, 0.5, 2.0, 2.2), ("crate", 0.7, 0.6, 0.6, 2.0),
                 ("locker", 1.0, 0.5, 1.9, 1.0), ("table", 1.2, 0.8, 0.74, 1.2)],
    "medical": [("locker", 1.0, 0.5, 1.9, 2.0), ("console", 0.8, 0.6, 1.1, 1.4),
                ("table", 1.4, 0.7, 0.9, 1.0), ("bin", 0.4, 0.4, 0.7, 1.2)],
    "industrial": [("crate", 0.9, 0.9, 0.8, 2.6), ("can", 0.6, 0.6, 0.9, 1.8),
                   ("shelf", 1.8, 0.6, 2.2, 1.4), ("locker", 0.9, 0.5, 1.9, 0.8)],
    "store": [("shelf", 2.0, 0.6, 2.4, 3.0), ("crate", 1.0, 0.8, 0.8, 3.0),
              ("can", 0.6, 0.6, 0.9, 1.2)],
    "office": [("table", 1.4, 0.8, 0.74, 1.8), ("chair", 0.52, 0.52, 0.95, 2.2),
               ("locker", 0.9, 0.5, 1.9, 1.2), ("console", 0.7, 0.6, 1.1, 1.0)],
    "hospitality": [("table", 1.0, 1.0, 0.74, 2.0), ("chair", 0.5, 0.5, 0.95, 4.0),
                    ("shelf", 1.4, 0.4, 2.0, 1.0), ("crate", 0.6, 0.5, 0.5, 0.8)],
    "detention": [("locker", 0.8, 0.5, 1.9, 1.0), ("bin", 0.35, 0.35, 0.6, 0.8)],
    "transit": [("bin", 0.4, 0.4, 0.8, 1.2), ("crate", 0.8, 0.6, 0.6, 1.4),
                ("shelf", 1.4, 0.45, 1.8, 1.0)],
    "research": [("console", 0.9, 0.7, 1.1, 2.0), ("locker", 1.0, 0.5, 1.9, 1.6),
                 ("table", 1.4, 0.8, 0.9, 1.4)],
    "worship": [("crate", 0.6, 0.5, 0.5, 0.6)],
    "generic": [("crate", 0.8, 0.7, 0.7, 1.8), ("locker", 0.9, 0.5, 1.9, 1.2),
                ("shelf", 1.5, 0.5, 2.0, 1.2)],
}

# Small objects scattered on horizontal surfaces, as (w, d, h). THIS is where a
# frame's density comes from -- the objects ON the furniture, not the furniture.
CLUTTER = [(0.22, 0.16, 0.06), (0.12, 0.12, 0.18), (0.30, 0.20, 0.04),
           (0.16, 0.16, 0.22), (0.26, 0.18, 0.10), (0.10, 0.10, 0.12),
           (0.34, 0.24, 0.08), (0.14, 0.10, 0.20)]
CLUTTER_PER_M2 = 9.0          # on tops, not on the deck
SURFACE_MIN_M2 = 0.10
FLOOR_CLUTTER_PER_M = 0.55
# A person is 0.5 m across the shoulders; 1.4 m lets two pass and a door swing.
LANE_M = 1.6         # anything smaller carries nothing


def wall_band_m(arch):
    """How deep a band this archetype's furniture takes off each wall.

    So a bay can be SIZED for the furniture that is going to be put in it.
    `rooms.bay_span_m` derives a bay from the props ranked along its walls and
    the fixtures it holds, and then this module adds a whole second layer of
    furniture that the sizing never allowed for -- which is why 44 of 87 rooms
    have to throw some of it away again to stay crossable. The two rules have to
    agree about how wide the room is, and the only way they can is for the
    sizing to ask the thing that does the placing.
    """
    return max((d for _b, _w, d, _h, _n in SCHEMES.get(arch, SCHEMES["generic"])),
               default=0.0)


def _surfaces_of(v, t, g, mark):
    """Upward-facing faces added since `mark`, as (y, x0, x1, z0, z1, area).

    Read back off the geometry rather than tracked alongside it: a builder that
    grows a new shelf gets clutter on it automatically, and a builder that loses
    one stops getting clutter, with nothing to keep in step. Two lists that must
    agree is the defect this project keeps finding in new costumes.
    """
    out = []
    for name, lo, hi in g:
        if lo < mark or MACHINE_MARK in name:
            # SPANS NEST since INV-132: a piece of furniture emits one outer
            # span covering all its triangles and then part spans inside it.
            # The outer span already sees every horizontal face, so counting
            # the parts as well would put two mugs on every shelf.
            continue
        for tri in t[lo:hi]:
            p = [v[i] for i in tri]
            if max(abs(p[0][1] - p[1][1]), abs(p[0][1] - p[2][1])) > 1e-6:
                continue                       # not horizontal
            xs = [q[0] for q in p]
            zs = [q[2] for q in p]
            a = 0.5 * abs((xs[1] - xs[0]) * (zs[2] - zs[0])
                          - (xs[2] - xs[0]) * (zs[1] - zs[0]))
            if a * 2 < SURFACE_MIN_M2:
                continue
            out.append((p[0][1], min(xs), max(xs), min(zs), max(zs), a * 2))
    return out


def dress(place, w_m, l_m, ceil_m, arch, inset=(0.0, 0.0), seed=None,
          density=1.0):
    """Fill one room. Returns (verts, tris, group_spans, stats).

    `w_m`/`l_m` are the room's interior span and `inset` the depth each side has
    already lost to fixtures, so furniture lands against free wall rather than
    inside the machinery `rooms.py` put there.
    """
    seed = seed or place
    v, t, g = [], [], []
    hw, hl = w_m / 2.0, l_m / 2.0
    scheme = SCHEMES.get(arch, SCHEMES["generic"])
    counts = {"furniture": 0, "clutter": 0, "service": 0, "rejected": 0}

    # THE CIRCULATION LANE, and it is the difference between a furnished room
    # and a blocked one. Dressing all four walls of a small room closes it:
    # `station/walkable.py` went from 6/8 rooms walkable to 59 UNWALKABLE the
    # moment this generator was wired in, because a body cannot squeeze past a
    # shelf run into a corner. A room has to keep a path through it, so a lane
    # of `LANE_M` is reserved down the long axis and across the short one, and
    # anything whose footprint would intrude is rejected rather than shrunk --
    # a half-size locker jammed into a doorway is still a blocked doorway.
    # `density` scales how much goes in. It exists because no single constant
    # is right for 68 rooms of different shapes: tuning LANE_M globally left 21
    # rooms unwalkable at every value tried, because the blocker is the room's
    # own proportions and its fixtures, not the lane. `rooms.build` calls this
    # at falling densities and keeps the first result a body can still walk
    # through, so the generator guarantees its own invariant per room instead
    # of me guessing a number that works everywhere and does not.
    lane_hw = min(LANE_M / 2.0, max(0.35, hw - 0.9))
    lane_hl = min(LANE_M / 2.0, max(0.35, hl - 0.9))

    def blocks_lane(cx, cz, sw, sd):
        # ONE BAND DOWN THE LONG AXIS, which is exactly the question
        # `rooms.walkable` asks: can a 0.9 m body get from one end wall to the
        # other. Two earlier versions were wrong in opposite directions -- an
        # `and` cleared only the centre POINT and left 58 rooms unwalkable, and
        # an `or` reserved a full cross and rejected every piece of mid-wall
        # furniture, emptying the rooms it was meant to fill. The corridor is
        # the thing that has to stay clear; the walls are where furniture goes.
        return abs(cx) - sw / 2.0 < lane_hw

    # 1 -- furniture against the four walls.
    mark_f = len(g)
    # ALL FOUR WALLS. The first version dressed the two long ones and a 6x9 m
    # office came out with six pieces of furniture, which is a waiting room, not
    # a working space. The end walls are wall too.
    walls = [(-hw + inset[0], 1, hl * 2, "x"), (hw - inset[1], -1, hl * 2, "x"),
             (-hl, 1, hw * 2, "z"), (hl, -1, hw * 2, "z")]
    for wall_x, facing, run, axis in walls:
        for spec in scheme:
            build, pw, pd, ph, per10 = spec
            n = max(0, int(run / 10.0 * per10 * density))
            for i in range(n):
                # ALONG the wall and PERPENDICULAR to it, named, because the
                # first version computed the offset from `pd` and then swapped
                # `pw`/`pd` for the end walls -- so an object was positioned
                # using one dimension and built with the other, and furniture
                # left the room. rooms.py's footprint assertion caught it on
                # three locations.
                s_along, s_perp = (pw, pd) if axis == "x" else (pd, pw)
                along = -run / 2 + run * (i + 0.5) / max(1, n)
                along += (_u(seed, "z", wall_x, build, i) - 0.5) * 0.4
                along = max(-run / 2 + s_along / 2,
                            min(run / 2 - s_along / 2, along))
                off = wall_x + facing * (s_perp / 2.0 + 0.04)
                if axis == "x":
                    xx, zz, bw_, bd_ = off, along, s_perp, s_along
                else:
                    xx, zz, bw_, bd_ = along, off, s_along, s_perp
                if blocks_lane(xx, zz, bw_, bd_):
                    counts["rejected"] += 1
                    continue
                BUILDERS[build](v, t, g, xx, 0.0, zz, bw_, bd_, ph,
                                f"{seed}-{build}-{i}")
                counts["furniture"] += 1

    # 2 -- clutter on every horizontal surface the furniture just made.
    for (sy, x0, x1, z0, z1, area) in _surfaces_of(v, t, g, mark_f):
        n = int(area * CLUTTER_PER_M2 * density)
        for i in range(n):
            cw, cd, ch = _pick(CLUTTER, seed, "c", sy, x0, i)
            cx = x0 + (x1 - x0) * _u(seed, "cx", sy, x0, i)
            cz = z0 + (z1 - z0) * _u(seed, "cz", sy, z0, i)
            cx = max(x0 + cw / 2, min(x1 - cw / 2, cx))
            cz = max(z0 + cd / 2, min(z1 - cd / 2, cz))
            if x1 - x0 < cw or z1 - z0 < cd:
                continue
            _box(v, t, g, "dress_clutter", (cx - cw / 2, sy, cz - cd / 2),
                 (cx + cw / 2, sy + ch, cz + cd / 2))
            counts["clutter"] += 1

    # 2b -- floor scatter along the wall line. A room with a clean deck reads
    # as a showroom; the things that make it look worked-in are on the ground
    # against the skirting, where they do not block circulation.
    for wall_x, facing, run, axis in walls:
        n = max(0, int(run * FLOOR_CLUTTER_PER_M * density))
        for i in range(n):
            cw, cd, ch = _pick(CLUTTER, seed, "f", wall_x, i)
            sc = 1.4 + 1.2 * _u(seed, "fs", wall_x, i)
            cw, cd, ch = cw * sc, cd * sc, ch * sc
            along = -run / 2 + run * (i + 0.6) / max(1, n)
            off = wall_x + facing * (0.55 + 0.5 * _u(seed, "fo", wall_x, i))
            cx, cz = (off, along) if axis == "x" else (along, off)
            if blocks_lane(cx, cz, cw, cd):
                counts["rejected"] += 1
                continue
            _box(v, t, g, "dress_clutter", (cx - cw / 2, 0.0, cz - cd / 2),
                 (cx + cw / 2, ch, cz + cd / 2))
            counts["clutter"] += 1

    # 3 -- services on the walls and under the soffit.
    # SERVICES SCALE TOO. They did not, so `density=0.0` -- the fallback that
    # exists so a room can always end up walkable -- still hung wall boxes at
    # chest height and left 23 rooms impassable. A zero that does not mean zero
    # is worse than no fallback at all, because it looks like one.
    # AND THEY SCALE ALL THE WAY DOWN. `max(2, ...)` meant two wall boxes went
    # up at EVERY density above zero, so the ladder had no rung on which the
    # furniture survived and the services did not -- and in a marginal room it
    # is the services that close the path, because `rooms.walkable` dilates
    # every obstacle by the walker's radius and a 0.14 m panel becomes a 1.04 m
    # block. `bay_elevators` was unwalkable with FOUR extra objects and
    # walkable with none, so the whole dressing was thrown away to remove two
    # shallow panels. A floor under a scale factor is a scale factor that does
    # not reach zero.
    for wall_x, facing, run, axis in walls[:2]:
        if density <= 0.0:
            break
        n = int(run / 2.2 * density)
        for i in range(n):
            zz = -hl + run * (i + 0.5) / n
            if _u(seed, "svc", wall_x, i) < 0.45:
                _box(v, t, g, "dress_wallbox",
                     (wall_x + facing * 0.02, 1.35, zz - 0.16),
                     (wall_x + facing * 0.16, 1.72, zz + 0.16))
                counts["service"] += 1
            if _u(seed, "drop", wall_x, i) < 0.35:
                _cyl(v, t, g, "dress_conduit",
                     wall_x + facing * 0.09, zz, 0.0, ceil_m - 0.25, 0.045)
                counts["service"] += 1
    return v, t, g, counts


def stats(place, w_m, l_m, ceil_m, arch, inset=(0.0, 0.0)):
    v, t, g, c = dress(place, w_m, l_m, ceil_m, arch, inset)
    area = w_m * l_m
    return {"triangles": len(t), "objects": sum(c.values()),
            "per_m2": sum(c.values()) / max(area, 1e-9), **c}


# ===========================================================================
# MACHINERY -- the object a room is NAMED FOR, and it was a single box
# ===========================================================================
# `docs/aaa-scorecard.json` scores `generated_rooms` at CRAFT 1 -- the rubric's
# own words for that score are *"a box primitive standing in for a named
# object"* -- across 58% of the station's locations. The measurement behind it
# is in `rooms.FIXTURES`: every fixture instance was one call to `_box`, so a
# "fusion containment vessel" was a rectangular pier 4 m across and a
# "fabrication furnace" was a 2.4 x 2.4 x 4.6 m slab.
#
# WHY NO GATE CAUGHT IT, which is the part worth carrying forward.
# `station/density.py` measures visible line density over a WHOLE ROOM and the
# rooms PASS it -- 123 of 128 locations were at or above their derived floor
# with every machine still a box. Measured per group on the pre-change build:
#
#     room             room lambda   machinery lambda   machinery normals
#     fabrication          4.23           1.04                5.95
#     reactor_hall         4.02           0.66                5.83
#     medlab_one           5.76           1.89                5.84
#     business_center      6.20           2.19                5.07
#
# The shell's articulation -- ribs, bands, mullions, panels, deck grid -- is
# 99% of the room's surface, so it carries the room's average over the floor
# while the machinery sits at a sixth of it. `density.machinery_report()` is
# the gate that separates the two, and `normals ~ 6` is a box's signature
# whatever its tessellation (density.py's own docstring says so).
#
# WHAT A MACHINE IS MADE OF HERE
# ------------------------------
# One PRIMARY form, SECONDARY structure that carries or feeds it, and TERTIARY
# fittings that say what it does -- which is the size hierarchy
# `docs/AAA-STANDARD.md` names as the difference between CRAFT 1 and CRAFT 3.
# A vessel is a lathe with a domed head, flanges, standoff legs, a bolted
# manway, radial pipe stubs with elbows, a gauge plate, a ladder and a hazard
# band at its foot. A rack is uprights, rails, shelves and stock ON the
# shelves. A console has a raked face, a bezel, a screen and a knee recess.
#
# EVERY PART STAYS INSIDE THE BOX IT REPLACES. That is not tidiness, it is what
# makes the change safe: `rooms.walkable`, `rooms._solid_boxes` and
# `collision.prop_boxes` all read the fixture's own AABB, so a machine that
# never leaves it cannot make a walkable room unwalkable or a solid clash.
# `machine_bounds_ok` asserts it and `rooms._selftest` runs it.
#
# GROUP NAMES: THE BOUND FRAGMENT NAMES THE MATERIAL, and the `_mp_` infix
# marks a machine part. Both are load-bearing:
#
#   * `materials.resolve` matches a fragment as a SUBSTRING, longest wins, so
#     `fix_mp_plant_frame` takes `plant_frame` -> `steel_gantry_oxide` with no
#     edit to `materials.py` (which this session does not own). The convention
#     is `rooms.PLACE_FIXTURES`' own, adopted there for the same reason.
#   * `_mp_` is what `rooms._solid_boxes` skips. A machine part nests INSIDE
#     its fixture's span -- `per_triangle` resolves last-span-wins, so the part
#     takes its own material and the fixture's outer span still owns the AABB
#     every walkability and collision rule reads. Without the marker the
#     interpenetration gate would see a flange inside its own vessel and call
#     it two solids in one place, which it is not.
#   * The prefix is INHERITED from the parent (`fix_` or `prop_`), because
#     `budget.klass_of` splits its report on exactly that prefix. A machine
#     part of a fixture must be counted as a fixture.
#
# Everything here is extrapolation -- INV-130 -- constrained by: the part must
# fit inside the box the fixture already occupied, the assembly must be closed
# and manifold (a hole and an inside-out face both render as the background),
# and no dimension may be finer than the mesh can carry at the distance the
# room is composed from.
MACHINE_MARK = "_mp_"

# Proportions. Every one is a RATIO of the box the fixture declares, so a
# machine in a 3.4 m lock and the same machine in a 7.5 m reactor hall are the
# same object at two sizes rather than two objects.
SEG_BODY = 14              # facets round a vessel: 25.7 deg, 0.9 m chord at r=2
SEG_PIPE = 8
SEG_BOLT = 5
LEG_FRAC = 0.075           # standoff under a vessel, as a fraction of height
LEG_MIN_M = 0.16
LEG_MAX_M = 0.55
DOME_FRAC = 0.34           # domed head rise / body radius
FLANGE_PROUD = 0.055       # flange radius over body radius, fraction
FLANGE_T_M = 0.07
HAZARD_H_M = 0.22
RAIL_H_M = 1.05
RUNG_PITCH_M = 0.30
GAUGE_Y_M = 1.45           # instruments at the height a standing person reads
MIN_PART_M = 0.012         # below this a part is sub-pixel at any indoor range
MACH_PROUD_M = 0.045       # plan inset, so proud bands have room to be proud


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _tube(v, t, g, name, p0, p1, r, seg=SEG_PIPE, phase=0.0):
    """A capped cylinder between two arbitrary points.

    `_cyl` above is upright only, which is enough for a bollard and useless for
    a pipe stub leaving a vessel sideways, a hanger rod, a handrail or a crane
    rope. Winding is derived from `_cyl`'s rather than guessed: with the local
    basis (e1, e2, axis) satisfying e1 x e2 = -axis -- which `uy = e1 x axis`
    gives -- the same triangle order faces outward. `_selftest` measures it on
    all three axes and on a diagonal, because "I checked one case" is how this
    project shipped a 0/24 inside-out cylinder.
    """
    ax = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in ax))
    if ln < 1e-9 or r <= 0.0:
        return
    ax = [c / ln for c in ax]
    seed_up = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    ux = _cross(seed_up, ax)
    m = math.sqrt(sum(c * c for c in ux))
    ux = [c / m for c in ux]
    uy = _cross(ux, ax)
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg + phase
        ca, sa = r * math.cos(a), r * math.sin(a)
        d = [ca * ux[i] + sa * uy[i] for i in range(3)]
        v.append(tuple(p0[i] + d[i] for i in range(3)))
        v.append(tuple(p1[i] + d[i] for i in range(3)))
    t0 = len(t)
    for k in range(seg):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % seg)
        t += [(a0, b0 + 1, b0), (a0, a0 + 1, b0 + 1)]
    c = len(v)
    v.append(tuple(p1))
    for k in range(seg):
        t.append((c, n0 + 2 * ((k + 1) % seg) + 1, n0 + 2 * k + 1))
    c0 = len(v)
    v.append(tuple(p0))
    for k in range(seg):
        t.append((c0, n0 + 2 * k, n0 + 2 * ((k + 1) % seg)))
    _tag(g, name, t0, len(t))


def _band(v, t, g, name, p0, p1, r_in, r_out, seg=SEG_BODY, phase=0.0):
    """An annular band between two points -- a girth flange WITH ITS BORE OPEN.

    THE LATHE'S VERSION OF THE SLAB BAND, and the same finding one primitive
    down. `_perim_band` above records that a course band built as one box
    "carries 11 m2 of surface of which 0.4 m2 is visible -- the rest is buried
    inside the body it wraps -- and `density.py --machinery` measures line over
    TOTAL area, so a band built that way LOWERS the number it was added to
    raise." Every girth flange, hazard band and collar on this module's lathed
    machines was a `_cyl`, which is a DISC: two caps of pi*r^2 buried inside
    the barrel they ring. Measured on the reactor vessel at its declared 4.00 x
    6.20 m, before this existed:

        four girth flanges   4 x 14.5 m2 of buried cap
        one hazard band          13.2 m2
        the barrel's own caps    13.0 m2   (inside the two domed heads)
                                 ------
                                 84.2 m2 of the vessel's 218.7 m2 total

    38% of a reactor vessel's measured surface was inside itself. The band
    below is the same object with the bore taken out: 2.79 m2 against 15.2 m2
    for one flange, and not one visible line lost.

    Closed and manifold by construction -- outer wall, inner wall wound the
    other way, and an annulus at each end. Winding is DERIVED from `_tube`'s,
    which `_selftest` measures on four axes: the outer wall is `_tube`'s
    lateral verbatim, the inner wall is that reversed, and each end annulus is
    `_tube`'s end cap with the hub vertex replaced by the inner ring -- which
    preserves orientation because the inner ring is on the same side of the
    outer arc that the hub was. `_selftest` does not take that on trust: it
    asserts the SIGNED VOLUME equals the analytic prism volume of the annulus,
    which an inside-out inner wall gets wrong by 2*pi*r_in^2*L and a merely
    "positive volume" check would pass.
    """
    if _FLAT:                     # the pre-INV-136 disc, for the control
        return _tube(v, t, g, name, p0, p1, r_out, seg, phase)
    if r_out <= r_in + 1e-6:
        return
    ax = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in ax))
    if ln < 1e-9:
        return
    ax = [c / ln for c in ax]
    seed_up = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    ux = _cross(seed_up, ax)
    m = math.sqrt(sum(c * c for c in ux))
    ux = [c / m for c in ux]
    uy = _cross(ux, ax)
    n0 = len(v)
    for r in (r_out, r_in):                 # outer ring block, then inner
        for k in range(seg):
            a = math.tau * k / seg + phase
            ca, sa = r * math.cos(a), r * math.sin(a)
            d = [ca * ux[i] + sa * uy[i] for i in range(3)]
            v.append(tuple(p0[i] + d[i] for i in range(3)))
            v.append(tuple(p1[i] + d[i] for i in range(3)))
    inner = n0 + 2 * seg
    t0 = len(t)
    for k in range(seg):
        oa, ob = n0 + 2 * k, n0 + 2 * ((k + 1) % seg)
        ia, ib = inner + 2 * k, inner + 2 * ((k + 1) % seg)
        t += [(oa, ob + 1, ob), (oa, oa + 1, ob + 1)]       # outer, facing out
        t += [(ia, ib, ib + 1), (ia, ib + 1, ia + 1)]       # inner, facing in
        t += [(ia + 1, ob + 1, oa + 1)]                     # annulus at p1
        t += [(ia + 1, ib + 1, ob + 1)]
        t += [(ia, oa, ob)]                                 # annulus at p0
        t += [(ia, ob, ib)]
    _tag(g, name, t0, len(t))


def _ring(v, t, g, name, cx, cz, y0, y1, r_in, r_out, seg=SEG_BODY, phase=0.0):
    """`_band` upright, for the lathed machines that are built on `_cyl`."""
    _band(v, t, g, name, (cx, y0, cz), (cx, y1, cz), r_in, r_out, seg, phase)


# ---------------------------------------------------------------------------
# THE MACHINE IS PLATED OUT OF THE SAME KIT THE WALL BEHIND IT IS
# ---------------------------------------------------------------------------
# `density.py --machinery`'s floor is *the room's own shell*, and its docstring
# states the case in one line: "the machine may not be less articulated than
# the wall behind it". Session 4e plated the walls, the floor rose, and ten
# rooms fell out of the gate -- a player now saw a properly plated wall with a
# plain box standing in front of it.
#
# The wall's answer to a big flat surface is already in this repository and is
# already measured: `rooms.kit_plate_module()` returns the plate length, course
# height, seam and proud that `rooms.articulate` lays a wall field on, every
# one of them `interior_kit.PROVISIONAL`'s and read off `grey level 1.webp` --
# the authority-1 frame that defines 1.00 for this project. NOTHING HERE IS A
# NEW NUMBER: the module is fetched from `rooms` at call time rather than
# copied, because a copied constant is a second copy of a computed number and
# this file has the scars.
#
# WHY A FIXED FEATURE COUNT IS THE DEFECT. `_m_leaf` put three ribs on a door
# leaf whatever its size. On the 1.90 x 2.35 m `door` that is a rib every
# 0.78 m and the leaf measures 6.14 m^-1; on the 6.00 x 5.00 m `bay_door` the
# same three ribs are 104 m2 of leaf at 2.59 m^-1 -- the least articulated
# object in the station and the one a player walks through. A plate module is a
# LENGTH, so the count grows with the object and the density does not fall.
_KIT_MOD = None

# THE NEGATIVE CONTROL'S SWITCH, and it is the same device `articulate` uses.
# That function's `plates=False` "REBUILDS THE PRE-INV-210 SHELL ... so that
# `density.py --shell`'s negative control can be run on the geometry the gate
# was written against instead of on a description of it". This is that, for the
# machines: with it set, `_plate_face` and `_face_rim` build nothing, `_band`
# goes back to being a solid disc and a rack shelf back to one plate. Nothing
# ships with it on -- `_selftest` sets it, asserts the articulation gate FAILS,
# and clears it.
_FLAT = False


def kit_module(scale=1.0):
    """(plate length, course height, seam, proud) -- `rooms`', not a copy.

    Imported at call time. `rooms` imports this module inside its functions, so
    the cycle only ever runs one way at import; `density.machinery_split` takes
    the same route to `rooms._SHELL_SUFFIXES` and for the same reason.
    """
    global _KIT_MOD
    if _KIT_MOD is None:
        import rooms as _R                                  # noqa: PLC0415
        _KIT_MOD = _R.kit_plate_module
    return _KIT_MOD(scale)


def kit_tile():
    """The kit's floor tile -- `rooms.DECK_TILE_M`, fetched, never copied.

    The horizontal counterpart of `kit_module`, and the module for a machine's
    horizontal surfaces: a rack shelf, a platform, a bed deck. `rooms`' own
    comment on it reads "interior_kit.deck_grid's own tile, and the same
    relationship: proud tiles, recessed joints".
    """
    import rooms as _R                                      # noqa: PLC0415
    return _R.DECK_TILE_M


def _face_rim(v, t, g, name, box, axis, side, width, proud):
    """A bezel: four members round ONE face, IN THAT FACE'S OWN PLANE.

    `_perim_band` is the horizontal version of this and wraps a body the way a
    girth band wraps a vessel. It is the wrong primitive for a bezel and the
    cost of finding that out is recorded in `_m_wallpanel`: used round an
    upright screen its two side members came out spanning the screen's full
    height AND its full width -- 9.099 m2 each, measured -- and took the panel
    from 28.98 m2 to 40.67. A helper on the wrong axis is not a small mistake
    here; it is the slab it exists to prevent.

    Scale-free, unlike `_plate_face`: a bezel is a bezel on a 0.20 m lift-call
    button and on a 3.20 m monitor wall, because it is a proportion of the
    thing it surrounds rather than a module laid across it. The two are
    complementary and `_m_wallpanel` uses both.
    """
    if _FLAT:
        return 0
    x0, y0, z0, x1, y1, z1 = box
    if axis == "x":
        u0, u1, w0, w1, fx = z0, z1, y0, y1, (x0 if side < 0 else x1)
    elif axis == "z":
        u0, u1, w0, w1, fx = x0, x1, y0, y1, (z0 if side < 0 else z1)
    else:
        u0, u1, w0, w1, fx = x0, x1, z0, z1, (y0 if side < 0 else y1)
    # THE GUARD IS ON THE MEMBER'S WIDTH, NOT ON ITS PROUD. `MIN_PART_M` asks
    # whether a part is sub-pixel, and a bezel 0.156 m long and 0.025 m wide is
    # not, however shallow it stands -- the depth of a bezel on a 45 mm thick
    # button panel is 6 mm because the panel is 45 mm thick. Guarding on the
    # proud instead declined the rim on every small terminal on the station.
    b = min(width, (u1 - u0) * 0.30, (w1 - w0) * 0.30)
    if b < MIN_PART_M or proud <= 1e-4:
        return 0
    a, c = (fx, fx + side * proud) if side > 0 else (fx + side * proud, fx)
    q = b * 0.22                      # so the four corners do not share an edge
    # ...and the whole rim is held off the face's own edge by `e`, for the
    # reason `_plate_face` records: a member drawn flush runs corner to corner
    # of the face, so its edge IS the body's edge and that edge then has four
    # faces on it. It measured 2 a face on the smallest wallpanel.
    e = b * 0.10
    u0, u1, w0, w1 = u0 + e, u1 - e, w0 + e, w1 - e
    n = 0
    for ua, ub, wa, wb in ((u0, u1, w0, w0 + b), (u0, u1, w1 - b, w1),
                           (u0, u0 + b, w0 + q, w1 - q),
                           (u1 - b, u1, w0 + q, w1 - q)):
        if axis == "x":
            _box(v, t, g, name, (a, wa, ua), (c, wb, ub))
        elif axis == "z":
            _box(v, t, g, name, (ua, wa, a), (ub, wb, c))
        else:
            _box(v, t, g, name, (ua, a, wa), (ub, c, wb))
        n += 1
    return n


def _face_cells(box, axis, scale=1.0, margin=0.0, u_mod=None, w_mod=None,
                inset=0.0):
    """The cells `_plate_face` would divide a face into, as boxes.

    The same lattice, handed back rather than drawn, so a caller that wants the
    PANELS as well as the seams -- a monitor wall wants both, since its cells
    are the monitors -- gets them off one division instead of two that can
    disagree. Each cell keeps the box's own extent on `axis`; the caller sets
    the depth it wants.
    """
    if _FLAT:
        return []
    plate_l, course_h, seam, _pr = kit_module(scale)
    u_mod = u_mod or plate_l
    w_mod = w_mod or course_h
    x0, y0, z0, x1, y1, z1 = box
    if axis == "y":
        u0, u1, w0, w1 = x0, x1, z0, z1
        tile = kit_tile() * scale
        u_mod, w_mod = u_mod or tile, w_mod or tile
    else:
        u0, u1 = ((z0, z1) if axis == "x" else (x0, x1))
        w0, w1 = y0, y1
    u0, u1, w0, w1 = u0 + margin, u1 - margin, w0 + margin, w1 - margin
    ncol = int(round((u1 - u0) / u_mod))
    nrow = int(round((w1 - w0) / w_mod))
    if ncol < 1 or nrow < 1 or ncol * nrow < 2:
        return []
    out = []
    for i in range(ncol):
        ua = u0 + (u1 - u0) * i / ncol + (seam if i else inset)
        ub = u0 + (u1 - u0) * (i + 1) / ncol - (seam if i < ncol - 1 else inset)
        for j in range(nrow):
            wa = w0 + (w1 - w0) * j / nrow + (seam if j else inset)
            wb = (w0 + (w1 - w0) * (j + 1) / nrow
                  - (seam if j < nrow - 1 else inset))
            if ub - ua < seam or wb - wa < seam:
                continue
            if axis == "x":
                out.append((x0, wa, ua, x1, wb, ub))
            elif axis == "z":
                out.append((ua, wa, z0, ub, wb, z1))
            else:
                out.append((ua, y0, wa, ub, y1, wb))
    return out


def _plate_face(v, t, g, name, box, axis, side, scale=1.0, proud=None,
                margin=0.0, u_mod=None, w_mod=None):
    """Divide ONE face of a body into the kit's plate field. Returns the count.

    `axis`/`side` name the face the way `_face_strip` does. The field is laid
    out at the kit's plate length across and its course height up, and the
    division is drawn with the kit's own seam width standing at the kit's own
    proud. Four numbers, all four `rooms.kit_plate_module()`'s and none new.

    THIS BUILDS THE SEAMS, NOT THE PLATES, AND THAT IS THE WHOLE POINT --
    `_perim_band`'s finding, one object larger. A wall can afford to build the
    plates: its substrate is a surface the room needs anyway, so the plates'
    buried backs are the only surface nobody sees. A MACHINE ALREADY HAS ITS
    BODY, so a plate laid on its face DOUBLES that face -- the back of every
    plate is buried in the body it sits on, and `--machinery` measures line
    over TOTAL area. Measured on the 6.00 x 5.00 m bay door, both built from
    this same module:

        plates (55 boxes a face)   area 104 -> 197 m2   lambda 2.594 -> 4.061
        seams  (16 ribs a face)    area 104 -> 127 m2   lambda 2.594 -> 7.39

    The rib field is 3.4x fewer triangles and lands 1.8x higher, because a rib
    has no buried back. It is also what the object physically IS: the leaf of a
    blast door is a stiffened plate and the stiffeners are on the outside.

    THE RIBS STAND PROUD OUTWARD, which is safe for the same reason
    `_perim_band`'s do: `machine()` insets every builder's box by up to
    `MACH_PROUD_M` before calling it, "so that the things which are SUPPOSED to
    stand proud have somewhere to be proud into". The proud is capped again
    here against the caller's own allowance, and `_selftest` measures the
    excursion at the LARGEST declared size of every kind -- which is the only
    place a field big enough to have a lattice in it ever appears.

    RETURNS 0 AND BUILDS NOTHING when the face is under two modules across. A
    0.6 m cell-door leaf is not a plated field, and one line down the middle of
    a small object is a box with a scratch on it.
    """
    if _FLAT:
        return 0
    plate_l, course_h, seam, kproud = kit_module(scale)
    x0, y0, z0, x1, y1, z1 = box
    if axis == "x":
        u0, u1, fx = z0 + margin, z1 - margin, (x0 if side < 0 else x1)
        w0, w1 = y0 + margin, y1 - margin
        u_mod, w_mod = u_mod or plate_l, w_mod or course_h
    elif axis == "z":
        u0, u1, fx = x0 + margin, x1 - margin, (z0 if side < 0 else z1)
        w0, w1 = y0 + margin, y1 - margin
        u_mod, w_mod = u_mod or plate_l, w_mod or course_h
    elif axis == "y":
        # A HORIZONTAL FACE TAKES THE FLOOR TILE ON BOTH AXES, because a course
        # height is a property of a WALL -- it is the field a wall's rail
        # divides -- and there is no up on a table top. `kit_tile()` is
        # `rooms.DECK_TILE_M`, and the same substitution `_m_rack`'s slatted
        # shelves make for the same reason.
        u0, u1, fx = x0 + margin, x1 - margin, (y0 if side < 0 else y1)
        w0, w1 = z0 + margin, z1 - margin
        tile = kit_tile() * scale
        u_mod, w_mod = u_mod or tile, w_mod or tile
    else:
        raise ValueError(f"_plate_face: {axis!r} is not a face")
    ncol = int(round((u1 - u0) / u_mod))
    nrow = int(round((w1 - w0) / w_mod))
    if ncol < 1 or nrow < 1 or ncol * nrow < 2:
        return 0
    pr = kproud if proud is None else min(kproud, proud)
    if pr < MIN_PART_M or min(u1 - u0, w1 - w0) < 4.0 * seam:
        return 0
    # THE WHOLE FIELD IS HELD OFF THE BODY'S OWN EDGES BY `q`. A border rib
    # drawn flush to the face runs from corner to corner of that face, so its
    # inner edge is the body's edge -- literally the same two endpoints -- and
    # that edge then has four faces on it. It measured 4 non-manifold edges a
    # face on the bay door and is invisible in any render.
    q = seam * 0.22
    u0, u1, w0, w1 = u0 + q, u1 - q, w0 + q, w1 - q
    if axis == "y":
        side = -side                   # inward: see the note below
    a, b = (fx, fx + side * pr) if side > 0 else (fx + side * pr, fx)
    if axis == "y":
        # A HORIZONTAL FACE IS TILED AND THE TILES GO INWARD. Two reasons and
        # both are already written down elsewhere in this repository:
        #
        #  * `machine()` insets the builder's box "in x and z ONLY: a full-height
        #    fixture has to reach the deck and the soffit". So on a top face
        #    there is NO room to stand proud into, and a field built outward
        #    leaves the AABB -- measured at 30 mm on the reactor shield and
        #    14 mm on the catwalk, and caught by `machine_bounds_ok` only once
        #    this file started building the LARGEST declared size.
        #  * `rooms._plate_deck`: "THE ROOM DECK HAD IT INVERTED ... `deck_grid`
        #    lays proud tiles over a substrate, so the tiles are the surface and
        #    the substrate shows only in the joints. [That] is what both corridor
        #    references show". A floor has proud tiles, not proud joints.
        #
        # So the caller sets its body back by `pr` and the tiles fill it: the
        # surface does not move, and the joints between them are the line.
        # held off the face's own edge by the same hair the rib field is:
        # an outer tile drawn flush runs corner to corner of the body, so
        # its edge IS the body's edge. 2 a face on the clamp skid.
        cells = _face_cells(box, "y", scale, margin + seam * 0.22,
                            u_mod, w_mod)
        for c in cells:
            _box(v, t, g, name, (c[0], min(a, b), c[2]), (c[3], max(a, b), c[5]))
        return len(cells)
    hs = seam / 2.0
    n = 0

    def rib(ua, ub, wa, wb):
        nonlocal n
        if ub - ua < 1e-6 or wb - wa < 1e-6:
            return
        if axis == "x":
            _box(v, t, g, name, (a, wa, ua), (b, wb, ub))
        elif axis == "z":
            _box(v, t, g, name, (ua, wa, a), (ub, wb, b))
        else:
            _box(v, t, g, name, (ua, a, wa), (ub, b, wb))
        n += 1

    # EVERY RIB IS A FULL RUN AND THEY CROSS RATHER THAN BUTT. The first
    # version stopped each stile at the rail above it, which leaves the stile's
    # cut face coplanar with the rail's side -- an edge with four faces on it,
    # and it measured 12 non-manifold edges on the bay door. That is the same
    # defect `_perim_band` records ("the four members OVERLAP at the corners
    # rather than abutting", 36 of them on the shield block) and the same one
    # `portal_frame` carried 828 times a deck in session 3x. Two boxes that
    # merely INTERPENETRATE share no vertex and so no edge, which is why
    # `_crate` and `_locker` have always been built out of overlapping solids
    # and measure zero of both.
    for j in range(1, nrow):                       # rails, the full width
        wc = w0 + (w1 - w0) * j / nrow
        rib(u0, u1, wc - hs, wc + hs)
    for i in range(1, ncol):                       # stiles, the full height
        uc = u0 + (u1 - u0) * i / ncol
        rib(uc - hs, uc + hs, w0, w1)
    # The field's own border, so the outermost course reads as a course rather
    # than as the edge of the body. THE UPRIGHTS ARE SHORTENED BY `q` AT BOTH
    # ENDS, and that is `_perim_band`'s "so the four corner posts do not share"
    # verbatim: two boxes meeting exactly at a corner share one whole edge,
    # which then has four faces on it. Measured at the field's four corners --
    # 4 non-manifold edges a face, 16 on a two-sided leaf -- and interpenetrating
    # by `q` instead costs nothing and shares nothing.
    if n:
        rib(u0, u1, w0, w0 + seam)
        rib(u0, u1, w1 - seam, w1)
        rib(u0, u0 + seam, w0 + q, w1 - q)
        rib(u1 - seam, u1, w0 + q, w1 - q)
    return n


def _dome(v, t, g, name, cx, cz, y_base, r, rise, seg=SEG_BODY, rings=3,
          up=True, phase=0.0):
    """A domed head: latitude rings to an apex, closed with its own base cap.

    CLOSED ON ITS OWN rather than welded to the barrel under it. Sharing the
    barrel's top ring would give every edge on that circle four faces, which is
    a non-manifold edge -- the defect `portal_frame` carried 828 times a deck in
    session 3x and which renders perfectly. Overlapping closed solids are how
    `_crate` and `_locker` already work and they measure zero of both.

    THE LAST RING STOPS SHORT OF THE POLE, and that is not cosmetic. The first
    version ran the latitude to phi = pi/2, where cos(phi) = 0 and all `seg`
    vertices of the top ring collapse onto one point -- so the band below it
    became `seg` degenerate triangles sharing the same zero-length edges, and
    `boundary_edges` measured 30 NON-MANIFOLD edges per vessel. A dome and a
    dome with a collapsed ring render identically.
    """
    n0 = len(v)
    for j in range(rings):
        phi = (math.pi / 2.0) * j / rings
        rr, yy = r * math.cos(phi), rise * math.sin(phi)
        for k in range(seg):
            a = math.tau * k / seg + phase
            v.append((cx + rr * math.cos(a),
                      y_base + (yy if up else -yy),
                      cz + rr * math.sin(a)))
    t0 = len(t)
    for j in range(rings - 1):
        for k in range(seg):
            a0 = n0 + j * seg + k
            b0 = n0 + j * seg + (k + 1) % seg
            a1, b1 = a0 + seg, b0 + seg
            if up:
                t += [(a0, b1, b0), (a0, a1, b1)]
            else:
                t += [(a0, b0, b1), (a0, b1, a1)]
    c = len(v)
    v.append((cx, y_base + (rise if up else -rise), cz))
    top = n0 + (rings - 1) * seg
    for k in range(seg):
        a0, b0 = top + k, top + (k + 1) % seg
        t.append((c, b0, a0) if up else (c, a0, b0))
    c0 = len(v)
    v.append((cx, y_base, cz))
    for k in range(seg):
        a0, b0 = n0 + k, n0 + (k + 1) % seg
        t.append((c0, a0, b0) if up else (c0, b0, a0))
    _tag(g, name, t0, len(t))


class _Parts:
    """The nine surfaces a machine is built out of, for one parent prefix.

    ONE GROUP PER PREFIX HOLDS EVERY MACHINE'S FRAME IN A ROOM, and that is
    what stops a pressed object being the whole object: `interact.gd` finds an
    object's meshes by name, and `prop_mp_plant_frame` does not begin with
    `prop_bay_door_`. Measured in 4w, a press moves **872 of 12,288 triangles
    across blue/0/0's sixteen interactables -- 7.1%**; a bay door is 12 of 536.

    THE STATED REASON FOR IT IS STALE, and session 4x measured that. This
    docstring used to say the vocabulary was fixed because "every extra
    distinct group name is another draw call in `budget.py`'s `draw calls,
    whole frame`, which is ALREADY over at 1,303 of 1,041". That gate now reads
    **423 of 1,041, 40.6%, passing** -- culling takes the interior to 191 in
    frustum -- and naming parts per object costs **+29 groups** on blue/0/0,
    taking primitives to 411 of 600. Affordable.

    WHAT BLOCKS IT IS MATERIAL RESOLUTION, NOT DRAW CALLS. `interact.gd`'s test
    requires the part to literally begin with its object's group name, so the
    part's name necessarily CONTAINS the object's -- and `materials.resolve`
    takes the longest matching substring. `dress_customs_desk_mp_plant_frame`
    resolves on `customs_desk` (12) over `plant_frame` (11): a desk's frame
    would take the desk's material. Renaming cannot fix it, because the
    containment is what `interact.gd` needs.

    The fix is to make `_mp_` load-bearing in resolution -- a machine part
    resolves on the fragment AFTER the marker -- and `resolve`'s own docstring
    says why that is its own increment: the rule is duplicated in
    `render_shot.gd::_material_for` "on purpose: if this function and the
    engine disagreed about which material a group got, every render would be
    judging something other than what ships". Three implementations, one rule.
    """

    def __init__(self, prefix):
        p = prefix + "mp_"
        self.frame = p + "plant_frame"        # steel_gantry_oxide
        self.pipe = p + "plant_pipe"          # clad_services
        self.conduit = p + "plant_conduit"    # plant_valve_metal, non-solid
        self.tread = p + "plant_catwalk"      # steel_catwalk_tread
        self.rail = p + "plant_rail"          # grab_rail_bare, non-solid
        self.gauge = p + "prop_tank_gauge"    # plant_switchgear
        self.hazard = p + "hazard_frame"      # accent_warning
        self.screen = p + "dress_screen"      # device_screen_glass
        self.panel = p + "prop_locker"        # furn_casework

    def all(self):
        return (self.frame, self.pipe, self.conduit, self.tread, self.rail,
                self.gauge, self.hazard, self.screen, self.panel)


def _gauges(v, t, g, P, x, y, z, nx, nz, w, seed):
    """A plate of instruments on a face: bezel, dials and a small screen.

    (nx, nz) is the outward face normal and is axis-aligned, so `abs(nx)` and
    `abs(nz)` select which of the two horizontal axes the plate runs along.
    """
    d = 0.05
    _box(v, t, g, P.panel,
         (x - w / 2 * abs(nz) - d * abs(nx), y - 0.16,
          z - w / 2 * abs(nx) - d * abs(nz)),
         (x + w / 2 * abs(nz) + d * abs(nx), y + 0.16,
          z + w / 2 * abs(nx) + d * abs(nz)))
    for i in (-1, 1):
        cx = x + i * w * 0.24 * abs(nz)
        cz = z + i * w * 0.24 * abs(nx)
        _tube(v, t, g, P.gauge,
              (cx + nx * d, y, cz + nz * d),
              (cx + nx * (d + 0.035), y, cz + nz * (d + 0.035)),
              0.055, SEG_PIPE)
    _box(v, t, g, P.screen,
         (x + nx * d - 0.09 * abs(nz), y - 0.09, z + nz * d - 0.09 * abs(nx)),
         (x + nx * (d + 0.02) + 0.09 * abs(nz), y + 0.09,
          z + nz * (d + 0.02) + 0.09 * abs(nx)))


def _perim_band(v, t, g, name, x0, z0, x1, z1, y0, y1, proud=0.014):
    """A band round the outside of a rectangular body, as FOUR THIN MEMBERS.

    NOT A SLAB, and the difference is most of this module's line-density
    budget. A course band built as one box spanning the body's full depth
    carries 11 m2 of surface of which 0.4 m2 is visible -- the rest is buried
    inside the body it wraps -- and `density.py --machinery` measures line over
    TOTAL area, so a band built that way LOWERS the number it was added to
    raise. Measured on the reactor hall's shield: 622.7 m2 of machinery surface
    for a mass whose outside is 82 m2, at 2.05 m^-1.

    It is also the same finding session 3x recorded on `portal_frame`: 8,832
    fewer triangles, "because coincident faces are geometry nobody can see".
    Here it is 4x the triangles and a tenth of the area, which is the trade the
    right way round.
    """
    # THE FOUR MEMBERS OVERLAP AT THE CORNERS rather than abutting. Butting
    # them left the side members' inner faces coplanar with the end members'
    # cut faces, which is an edge with four faces on it -- 36 non-manifold
    # edges on the shield block, and it renders perfectly.
    # THE PROUD IS CAPPED THE SAME WAY `machine` INSETS. A 0.06 m deep
    # platform edge cannot carry a 28 mm proud band and stay in its own
    # footprint, and `_selftest` found it by building each machine at the
    # SMALLEST declared size that uses it rather than at a probe size.
    proud = min(proud, (x1 - x0) * 0.12, (z1 - z0) * 0.12)
    b = min(proud * 3.0, (x1 - x0) * 0.30, (z1 - z0) * 0.30)
    q = proud * 0.22                    # so the four corner posts do not share
    for a, c, d, e in ((x0 - proud, z0 - proud, x1 + proud, z0 + b),
                       (x0 - proud, z1 - b, x1 + proud, z1 + proud),
                       (x0 - proud, z0 - proud + q, x0 + b, z1 + proud - q),
                       (x1 - b, z0 - proud + q, x1 + proud, z1 + proud - q)):
        if d - a <= 1e-6 or e - c <= 1e-6:
            continue
        _box(v, t, g, name, (a, y0, c), (d, y1, e))


def _face_strip(v, t, g, name, box, axis, side, u0, u1, y0, y1, proud=0.012):
    """A strip on ONE face of a body, and nothing behind it.

    A drawer line, a panel joint, a stack joint. The counter's first version
    ran its drawer lines round the whole 0.74 m depth for a 24 mm show, which
    is 5.5 m2 of surface an eye never meets -- the same defect as a slab band,
    one object smaller.
    """
    x0, y0b, z0, x1, y1b, z1 = box
    proud = min(proud, (x1 - x0) * 0.12, (z1 - z0) * 0.12)
    if axis == "x":
        fx = x0 if side < 0 else x1
        _box(v, t, g, name, (min(fx, fx - side * proud), y0, u0),
             (max(fx, fx - side * proud), y1, u1))
    else:
        fz = z0 if side < 0 else z1
        _box(v, t, g, name, (u0, y0, min(fz, fz - side * proud)),
             (u1, y1, max(fz, fz - side * proud)))


def _ladder(v, t, g, P, x, z, y0, y1, nx, nz, w=0.34):
    """Two stiles and rungs, on the face pointed at by (nx, nz)."""
    if y1 - y0 < 0.8:
        return
    for s in (-1, 1):
        sx = x + s * w / 2 * abs(nz)
        sz = z + s * w / 2 * abs(nx)
        _tube(v, t, g, P.frame, (sx + nx * 0.09, y0, sz + nz * 0.09),
              (sx + nx * 0.09, y1, sz + nz * 0.09), 0.028, SEG_BOLT)
    n = max(2, int((y1 - y0) / RUNG_PITCH_M))
    for i in range(1, n):
        yy = y0 + (y1 - y0) * i / n
        _tube(v, t, g, P.frame,
              (x - w / 2 * abs(nz) + nx * 0.09, yy, z - w / 2 * abs(nx) + nz * 0.09),
              (x + w / 2 * abs(nz) + nx * 0.09, yy, z + w / 2 * abs(nx) + nz * 0.09),
              0.018, SEG_BOLT)


def _railing(v, t, g, P, x0, z0, x1, z1, y, h=RAIL_H_M):
    """A top rail, a knee rail and posts along a straight run."""
    ln = math.dist((x0, z0), (x1, z1))
    if ln < 0.4:
        return
    n = max(2, int(ln / 1.3) + 1)
    for i in range(n):
        f = i / (n - 1)
        px, pz = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
        _tube(v, t, g, P.rail, (px, y, pz), (px, y + h, pz), 0.026, SEG_BOLT)
    for k in (0.52, 1.0):
        _tube(v, t, g, P.rail, (x0, y + h * k, z0), (x1, y + h * k, z1),
              0.024, SEG_BOLT)


# --- the twelve machines ---------------------------------------------------
# Each takes (v, t, g, box, P, seed) where `box` is (x0, y0, z0, x1, y1, z1) --
# exactly the box `rooms.build` used to emit -- and puts an articulated machine
# inside it. Geometry that carries the FIXTURE'S OWN material passes `None` for
# the group and is covered by the fixture's outer span; anything that is a
# genuinely different surface takes one of `_Parts`' nine names.

def _m_vessel(v, t, g, box, P, seed, furnace=False, horizontal=False):
    """A clad pressure vessel: the thing a "containment drum" actually is.

    Primary: a lathe barrel with a domed head. Secondary: a standoff skirt on
    legs, girth flanges, and a ladder. Tertiary: a bolted manway, radial pipe
    stubs turning down to the deck through elbows, a valve on the top stub, a
    gauge plate at reading height and a hazard band round the foot.

    `horizontal` lays the barrel on its side on saddles, which is what the
    generator hall's machine "in section" is; `furnace` swaps the manway for a
    charge door and adds a flue rising out of the top.
    """
    x0, y0, z0, x1, y1, z1 = box
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    h = y1 - y0
    if horizontal:
        return _m_drum(v, t, g, box, P, seed)
    hx, hz = (x1 - x0) / 2.0, (z1 - z0) / 2.0
    # THE BARREL IS 72% OF THE BOX, NOT 93%, and the remaining quarter is the
    # plumbing. A vessel drawn to the edge of its own declared footprint has
    # nowhere to put a stub, a ladder or an access platform, and the first
    # version pushed all three 0.75 m outside the box the walkability rules
    # read. The declared 4.00 m footprint is the machine PLUS its pipework,
    # which is what the footprint of a real one is.
    r = min(hx, hz) * 0.72
    if r < 0.12 or h < 0.5:
        _box(v, t, g, P.frame, (x0, y0, z0), (x1, y1, z1))
        return
    leg = min(LEG_MAX_M, max(LEG_MIN_M, h * LEG_FRAC))
    rise = min(r * DOME_FRAC, h * 0.16)
    body0, body1 = y0 + leg, y1 - rise
    ph = _u(seed, "phase") * math.tau / SEG_BODY

    # --- standoff: four legs, a base ring and the skirt they carry ---------
    for k in range(4):
        a = math.tau * (k + 0.5) / 4.0 + ph
        lx, lz = cx + r * 0.72 * math.cos(a), cz + r * 0.72 * math.sin(a)
        _tube(v, t, g, P.frame, (lx, y0, lz), (lx, body0 + 0.06, lz),
              max(MIN_PART_M, r * 0.085), SEG_PIPE)
        _box(v, t, g, P.frame, (lx - r * 0.13, y0, lz - r * 0.13),
             (lx + r * 0.13, y0 + 0.05, lz + r * 0.13))
    # THE SKIRT IS A RING, NOT A DISC. See `_band`: a `_cyl` used as a band
    # buries two pi*r^2 caps inside the body it wraps, and `--machinery`
    # measures line over TOTAL area.
    _ring(v, t, g, P.frame, cx, cz, body0 - 0.09, body0 + 0.02,
          r * 0.80, r * 0.99, SEG_BODY, ph)

    # --- primary: barrel, domed head, dished bottom ------------------------
    _cyl(v, t, None, "", cx, cz, body0, body1, r, SEG_BODY, ph)
    _dome(v, t, None, "", cx, cz, body1 - 0.02, r, rise + 0.02, SEG_BODY,
          3, True, ph)
    _dome(v, t, None, "", cx, cz, body0 + 0.02, r, min(rise, leg * 0.8),
          SEG_BODY, 2, False, ph)

    # --- girth flanges: the lines that say this was built in courses -------
    # AND THE PITCH IS THE KIT'S COURSE, NOT 1.25 m. A tank is welded up out of
    # plate courses and the flange is the seam between two of them, so the
    # spacing is the same course height `rooms.articulate` lays the wall behind
    # it on -- see `kit_module`. At 1.25 m a 5.5 m barrel got four flanges
    # whatever it was made of; at the kit's 0.446 m it gets twelve, and the
    # count grows with the vessel instead of the spacing.
    _course = kit_module()[1]
    n_f = max(1, int((body1 - body0) / _course))
    for i in range(n_f):
        fy = body0 + (body1 - body0) * (i + 1) / (n_f + 1)
        _ring(v, t, None, "", cx, cz, fy - FLANGE_T_M / 2, fy + FLANGE_T_M / 2,
              r * 0.97, r * (1.0 + FLANGE_PROUD), SEG_BODY, ph)
    # --- lagging strakes: the cheapest line on the station -----------------
    # A 40 mm proud x 30 mm strake adds four silhouette edges per metre of run
    # and about 0.11 m2 of surface, so it lifts line density by an order more
    # than it costs. It is also what a clad vessel HAS -- the strap that holds
    # the insulation on. Without them the barrel is 3.2 m^-1 against a 4.4 m^-1
    # shell, which is `density.py --machinery`'s way of saying the machine is
    # smoother than the wall behind it.
    n_s = max(6, SEG_BODY)
    for k in range(n_s):
        a = math.tau * k / n_s + ph
        sx, sz = cx + r * 0.995 * math.cos(a), cz + r * 0.995 * math.sin(a)
        _tube(v, t, None, "", (sx, body0 + 0.10, sz), (sx, body1 - 0.08, sz),
              max(MIN_PART_M * 2, r * 0.028), SEG_BOLT)

    # --- hazard band at the foot, where a person's shin is -----------------
    _ring(v, t, g, P.hazard, cx, cz, body0 + 0.04,
          min(body0 + 0.04 + HAZARD_H_M, body1), r * 0.97, r * 1.008,
          SEG_BODY, ph)

    # --- manway or charge door, on the -z face -----------------------------
    face_z = cz - r
    if furnace:
        dw, dh = min(r * 1.1, (x1 - x0) * 0.45), min(1.5, (body1 - body0) * 0.5)
        dy = body0 + 0.35
        _box(v, t, g, P.frame, (cx - dw, dy, face_z - 0.10),
             (cx + dw, dy + dh, face_z + 0.06))
        _box(v, t, g, P.hazard, (cx - dw * 0.86, dy + dh * 0.12,
                                 face_z - 0.15),
             (cx + dw * 0.86, dy + dh * 0.86, face_z - 0.07))
        for s in (-1, 1):                      # lifting gear either side
            _tube(v, t, g, P.frame, (cx + s * dw, dy, face_z - 0.05),
                  (cx + s * dw, dy + dh + 0.55, face_z - 0.05), 0.05, SEG_BOLT)
        _tube(v, t, g, P.frame, (cx - dw, dy + dh + 0.5, face_z - 0.05),
              (cx + dw, dy + dh + 0.5, face_z - 0.05), 0.04, SEG_BOLT)
        # the flue: what a furnace has and a slab does not
        fr = max(0.12, r * 0.26)
        _tube(v, t, g, P.pipe, (cx, y1 - rise * 0.4, cz),
              (cx, y1 - 0.01, cz), fr, SEG_PIPE)
        _cyl(v, t, g, P.frame, cx, cz, y1 - rise * 0.4 - 0.05,
             y1 - rise * 0.4 + 0.05, fr * 1.35, SEG_PIPE)
    else:
        # THE MANWAY PROTRUDES INTO WHAT IS LEFT, and not a fixed 0.25 m. A
        # 0.70 m service riser has 0.086 m between its barrel and its own
        # footprint, and a nozzle sized off the barrel put the bolt circle
        # 0.12 m outside it -- found by `rooms.machine_escapes` on the real
        # content, not by the probe box this builder was written against.
        room = max(0.0, min(hx, hz) - r)
        mp = min(0.16, room * 0.62)
        mr = min(r * 0.42, 0.42)
        my = body0 + max(0.9, (body1 - body0) * 0.28)
        _tube(v, t, None, "", (cx, my, face_z + 0.05),
              (cx, my, face_z - mp), mr, SEG_PIPE)
        _tube(v, t, g, P.frame, (cx, my, face_z - mp),
              (cx, my, face_z - mp - room * 0.14), mr * 1.22, SEG_PIPE)
        nb = 8
        for k in range(nb):
            a = math.tau * k / nb
            bx, by = cx + mr * 1.08 * math.cos(a), my + mr * 1.08 * math.sin(a)
            _tube(v, t, g, P.frame, (bx, by, face_z - mp * 0.7),
                  (bx, by, face_z - min(mp + room * 0.34, room * 0.95)),
                  0.028, SEG_BOLT)

    # --- pipe stubs: a vessel is a thing that is PLUMBED --------------------
    nst = 3 if (body1 - body0) > 1.6 else 2
    for i in range(nst):
        a = math.tau * (i + 0.35) / nst + ph
        sy = body0 + (body1 - body0) * (0.30 + 0.52 * i / max(1, nst - 1))
        sy = min(sy, body1 - 0.15)
        pr = max(MIN_PART_M * 3, r * (0.16 if i == 0 else 0.11))
        ex = min(r + min(0.65, r * 0.55), min(hx, hz) - pr * 1.5)
        px0 = (cx + r * 0.86 * math.cos(a), sy, cz + r * 0.86 * math.sin(a))
        px1 = (cx + ex * math.cos(a), sy, cz + ex * math.sin(a))
        _tube(v, t, g, P.pipe, px0, px1, pr, SEG_PIPE)
        _tube(v, t, g, P.frame, px1,
              (px1[0] + 0.05 * math.cos(a), sy, px1[2] + 0.05 * math.sin(a)),
              pr * 1.4, SEG_PIPE)
        drop = y0 + 0.08 if i % 2 == 0 else y1 - 0.05
        _tube(v, t, g, P.pipe, (px1[0], sy, px1[2]), (px1[0], drop, px1[2]),
              pr, SEG_PIPE)
        if i == 0:                              # a valve you could turn
            _cyl(v, t, g, P.conduit, px1[0], px1[2], sy + pr,
                 sy + pr + 0.10, pr * 0.7, SEG_PIPE)
            _cyl(v, t, g, P.conduit, px1[0], px1[2], sy + pr + 0.10,
                 sy + pr + 0.14, pr * 1.9, SEG_PIPE)

    # --- instruments and access -------------------------------------------
    gy = min(max(GAUGE_Y_M, body0 + 0.4), body1 - 0.3)
    _gauges(v, t, g, P, cx + r * 0.55, gy, cz - r * 0.80, 0.0, -1.0,
            min(0.8, r * 0.8), seed)
    lz = min(cz + r, cz + hz - 0.14)
    _ladder(v, t, g, P, cx, lz, body0, min(body1, y1 - 0.05), 0.0, 1.0)
    if (body1 - body0) > 2.6 and hz - r > 0.35:
        py = body0 + (body1 - body0) * 0.62
        pf = min(hx, r * 1.15)
        pz = cz + hz - 0.02
        _box(v, t, g, P.tread, (cx - pf, py - 0.05, cz + r * 0.5),
             (cx + pf, py, pz))
        _railing(v, t, g, P, cx - pf, pz - 0.04, cx + pf, pz - 0.04, py)


def _m_drum(v, t, g, box, P, seed):
    """A vessel lying on its side on saddles -- a heat drum, a generator case."""
    x0, y0, z0, x1, y1, z1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    r = min(x1 - x0, y1 - y0) / 2.0 * 0.90
    sad = min(0.35, (y1 - y0) * 0.16)
    cy = y0 + sad + r
    if r < 0.15:
        _box(v, t, g, P.frame, (x0, y0, z0), (x1, y1, z1))
        return
    for s in (-1, 1):                           # saddles
        sz = (z0 + z1) / 2.0 + s * (z1 - z0) * 0.30
        _box(v, t, g, P.frame, (cx - r * 0.95, y0, sz - 0.12),
             (cx + r * 0.95, y0 + sad + r * 0.35, sz + 0.12))
    _tube(v, t, None, "", (cx, cy, z0 + 0.10), (cx, cy, z1 - 0.10), r,
          SEG_BODY)
    # `_dome` is upright-only, so a horizontal drum gets BOLTED HEADS instead:
    # a flanged collar at each end, which is what a drum you can open has and
    # what the flat cap `_tube` already closes it with reads as.
    for zz in (z0 + 0.12, z1 - 0.12):
        _band(v, t, g, P.frame, (cx, cy, zz - 0.04), (cx, cy, zz + 0.04),
              r * 0.97, r * (1.0 + FLANGE_PROUD * 1.6), SEG_BODY)
    # Rings and the kit's course, for the reasons `_band` and `_m_vessel` give.
    nf = max(1, int((z1 - z0) / kit_module()[1]))
    for i in range(nf):
        fz = z0 + (z1 - z0) * (i + 1) / (nf + 1)
        _band(v, t, None, "", (cx, cy, fz - FLANGE_T_M / 2),
              (cx, cy, fz + FLANGE_T_M / 2), r * 0.97,
              r * (1.0 + FLANGE_PROUD), SEG_BODY)
    for k in range(SEG_BODY // 2):               # lagging strakes along the run
        a = math.tau * k / (SEG_BODY // 2)
        sy, sx = cy + r * 0.995 * math.sin(a), cx + r * 0.995 * math.cos(a)
        _tube(v, t, None, "", (sx, sy, z0 + 0.18), (sx, sy, z1 - 0.18),
              max(MIN_PART_M * 2, r * 0.028), SEG_BOLT)
    # a top-mounted terminal box and the conduit that leaves it
    _box(v, t, g, P.panel, (cx - r * 0.35, cy + r * 0.86, (z0 + z1) / 2 - 0.35),
         (cx + r * 0.35, cy + r * 1.05, (z0 + z1) / 2 + 0.35))
    _tube(v, t, g, P.conduit, (cx, cy + r * 1.05, (z0 + z1) / 2),
          (cx, y1 - 0.03, (z0 + z1) / 2), 0.06, SEG_PIPE)
    _gauges(v, t, g, P, cx, min(GAUGE_Y_M, cy), z0 + 0.05, 0.0, -1.0, 0.7, seed)
    # an access platform down one side, which is how a drum is maintained and
    # what tells the eye how big it is
    pw = min(0.55, (x1 - x0) * 0.5 - r * 0.92)
    if pw > 0.20:
        py = min(cy, y1 - 0.5)
        _box(v, t, g, P.tread, (x1 - pw, py - 0.05, z0 + 0.25),
             (x1, py, z1 - 0.25))
        _railing(v, t, g, P, x1 - 0.05, z0 + 0.25, x1 - 0.05, z1 - 0.25, py,
                 min(RAIL_H_M, y1 - py - 0.05))
    for s in (-1, 1):                           # coolant nozzles
        nz_ = (z0 + z1) / 2.0 + s * (z1 - z0) * 0.18
        _tube(v, t, g, P.pipe, (cx, cy - r * 0.9, nz_),
              (cx, y0 + 0.06, nz_), max(MIN_PART_M * 3, r * 0.14), SEG_PIPE)


def _m_rack(v, t, g, box, P, seed):
    """Uprights, rails, shelves -- and STOCK on the shelves.

    The stock is the point. A rack with nothing in it is a frame, and the thing
    that makes a store read as a store is what is stacked in it.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    up = min(0.09, min(w, d) * 0.22)
    n_bay = max(1, int((z1 - z0) / 2.4))
    n_lev = max(2, int(h / 1.15))
    for i in range(n_bay + 1):
        zz = z0 + (z1 - z0) * i / n_bay
        zz = min(max(zz, z0 + up), z1 - up)
        for xx in (x0 + up, x1 - up):
            _box(v, t, g, P.frame, (xx - up, y0, zz - up), (xx + up, y1, zz + up))
        # diagonal bracing on the back plane
        if i < n_bay:
            zn = z0 + (z1 - z0) * (i + 1) / n_bay
            _tube(v, t, g, P.frame, (x0 + up, y0 + 0.1, zz),
                  (x0 + up, y1 - 0.1, zn), 0.028, SEG_BOLT)
    # THE SHELVES ARE SLATTED, and that is not decoration -- it is 41% of this
    # object. Built as one plate a shelf is 2 x (w x d) of surface of which the
    # underside is never seen and the top is under the stock, and on the 2.60 x
    # 4.20 m `racking_run` the four shelves are 21.6 m2 of the rack's 52.6 --
    # `_perim_band`'s "a band built as one box LOWERS the number it was added
    # to raise", laid flat. Slatted, the same shelf costs the same area and
    # carries 3.1x the line, because a slat's sides are surface the eye meets.
    # It is also what rack decking IS. The pitch is `kit_tile()`, the kit's own
    # floor tile: a shelf is a small deck, and this file invents no module.
    slat = kit_tile()
    for j in range(n_lev + 1):
        yy = min(max(y0 + h * j / n_lev, y0 + 0.08), y1 - 0.05)
        n_sl = 1 if _FLAT else max(1, int(round((z1 - z0) / slat)))
        gap = min(0.035, (z1 - z0) / n_sl * 0.22)
        for s in range(n_sl):
            sa = z0 + (z1 - z0) * s / n_sl
            sb = z0 + (z1 - z0) * (s + 1) / n_sl - (gap if s < n_sl - 1 else 0.0)
            _box(v, t, g, P.tread, (x0, yy, sa), (x1, yy + 0.045, sb))
        for s_ in (-1, 1):                      # front and back edge lips
            _face_strip(v, t, g, P.frame, box, "x", s_, z0 + 0.02, z1 - 0.02,
                        yy - 0.055, min(yy + 0.052, y1), 0.016)
        for xx in (x0 + up, x1 - up):           # the rail the shelf sits on
            # Overlapping, and inset in z: flush against the shelf plate gave
            # 8 non-manifold edges a rack, which renders perfectly.
            _box(v, t, g, P.frame,
                 (max(xx - up * 1.3, x0), yy - 0.07, z0 + 0.006),
                 (min(xx + up * 1.3, x1), yy + 0.018, z1 - 0.006))
    for j in range(n_lev):                      # stock
        yy = y0 + h * j / n_lev + 0.045
        lvl = h / n_lev - 0.12
        for i in range(max(1, int((z1 - z0) / 0.85))):
            if _u(seed, "stock", j, i) < 0.28:
                continue
            cw = (z1 - z0) / max(1, int((z1 - z0) / 0.85))
            zc = z0 + cw * (i + 0.5)
            bw = cw * (0.55 + 0.35 * _u(seed, "sw", j, i))
            bh = lvl * (0.5 + 0.45 * _u(seed, "sh", j, i))
            _box(v, t, g, P.panel, (x0 + 0.05, yy, zc - bw / 2),
                 (x1 - 0.05, yy + bh, zc + bw / 2))
            _perim_band(v, t, g, P.conduit, x0 + 0.05, zc - bw / 2,
                        x1 - 0.05, zc + bw / 2, yy + bh * 0.62,
                        yy + bh * 0.72, 0.008)
            _box(v, t, g, P.hazard, (x0 + 0.036, yy + bh * 0.24, zc - bw * 0.30),
                 (x0 + 0.052, yy + bh * 0.44, zc + bw * 0.30))


def _m_cabinet(v, t, g, box, P, seed, louvre=True):
    """A cubicle line-up: plinth, doors, louvres, handles and a cable way.

    Switchgear, signal racks, patch panels and suit lockers are all this
    object. It is the one machine in the kit whose FRONT is the whole read, so
    everything spent goes on the door face.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    front_x = x1 if _u(seed, "face") < 0.5 else x0
    sgn = 1.0 if front_x == x1 else -1.0
    # NO TWO SOLIDS HERE SHARE A PLANE. The first version gave the plinth, the
    # body and the capping the same x0/x1/z0/z1, so three pairs of coincident
    # faces met along the same edges and `boundary_edges` measured 5
    # non-manifold edges a cabinet -- an edge with four faces on it, which is a
    # modelling error that renders perfectly (AAA-STANDARD, Geometry).
    pl = min(0.12, h * 0.06)
    _box(v, t, g, P.frame, (x0, y0, z0), (x1, y0 + pl, z1))
    _box(v, t, None, "", (x0 + 0.018, y0 + pl * 0.4, z0 + 0.018),
         (x1 - 0.018, y1 - 0.06, z1 - 0.018))
    _perim_band(v, t, g, P.frame, x0, z0, x1, z1, y1 - 0.09, y1, 0.012)
    _perim_band(v, t, g, P.frame, x0, z0, x1, z1, y0 + pl * 0.55, y0 + pl,
                0.010)
    # CORNER POSTS AND A MID BAND, ON ALL FOUR FACES. The doors are on one
    # face, chosen per instance, and a cabinet articulated on one face only is
    # a slab from the other three -- which is what the medlab's half-distance
    # frame showed: a locker with its back to the camera reading as one pale
    # rectangle 40% of frame width. The carcass has to read from any angle.
    cp = min(0.045, w * 0.18, d * 0.18)
    for ax_ in (x0, x1 - cp):
        for az in (z0, z1 - cp):
            _box(v, t, g, P.frame, (ax_ - 0.010, y0 + pl, az - 0.010),
                 (ax_ + cp + 0.010, y1 - 0.085, az + cp + 0.010))
    _perim_band(v, t, g, P.conduit, x0, z0, x1, z1, y0 + h * 0.56,
                y0 + h * 0.585, 0.008)
    n = max(1, int((z1 - z0) / 0.85))
    # THE DOOR FACE IS THE BOX FACE and everything proud is measured INWARD
    # from it. Building the door proud of `front_x` put the handle 35 mm
    # outside the fixture's own AABB -- into the aisle, which is exactly the
    # direction that matters.
    fo = front_x
    for i in range(n):
        zc = z0 + (z1 - z0) * (i + 0.5) / n
        cw = (z1 - z0) / n
        door = (min(fo, fo - sgn * 0.030), y0 + 0.14, zc - cw / 2 + 0.02,
                max(fo, fo - sgn * 0.030), y1 - 0.13, zc + cw / 2 - 0.02)
        _box(v, t, g, P.panel, door[:3], door[3:])
        # "everything spent goes on the door face", and the doors were the
        # flattest thing on the object: three of them, 10.42 m2, at 2.89 m^-1
        # against the carcass's 10.37. A switchgear door is a panelled door.
        _plate_face(v, t, g, P.frame, door, "x", 1 if sgn > 0 else -1,
                    proud=min(0.014, w * 0.02))
        if louvre:
            for k in range(3):
                yy = y0 + h * (0.60 + 0.09 * k)
                if yy > y1 - 0.20:
                    break
                _box(v, t, g, P.conduit,
                     (min(fo, fo - sgn * 0.055), yy, zc - cw * 0.32),
                     (max(fo, fo - sgn * 0.055), yy + 0.035, zc + cw * 0.32))
        _tube(v, t, g, P.frame, (fo - sgn * 0.026, y0 + h * 0.46, zc + cw * 0.34),
              (fo - sgn * 0.026, y0 + h * 0.54, zc + cw * 0.34), 0.022, SEG_BOLT)
        # the door's own reveal, as strips on the face and nothing behind it
        for yy in (y0 + 0.141, y1 - 0.1455):
            _face_strip(v, t, g, P.frame, box, "x", 1 if sgn > 0 else -1,
                        zc - cw / 2 + 0.021, zc + cw / 2 - 0.021, yy,
                        yy + 0.016, 0.038)
        for zz in (zc - cw / 2 + 0.022, zc + cw / 2 - 0.038):
            _face_strip(v, t, g, P.frame, box, "x", 1 if sgn > 0 else -1,
                        zz, zz + 0.016, y0 + 0.142, y1 - 0.132, 0.036)
        if _u(seed, "inst", i) < 0.55:
            _gauges(v, t, g, P, fo - sgn * 0.10, min(GAUGE_Y_M, y1 - 0.35), zc,
                    sgn, 0.0, min(0.55, cw * 0.7), seed)
    # `w` and NOT `d`: the cable way runs back over the cabinet's DEPTH, and
    # `d` in this builder is the line-up's LENGTH along z. With `d` a 2.00 m
    # patch-panel run put its trunking 0.29 m outside its own footprint and
    # through the console standing in front of it -- caught by the
    # interpenetration gate three rooms away from the cause.
    _tube(v, t, g, P.conduit, (front_x - sgn * w * 0.3, y1 - 0.075, z0),
          (front_x - sgn * w * 0.3, y1 - 0.075, z1), 0.045, SEG_PIPE)


def _m_pipe_bank(v, t, g, box, P, seed):
    """A bank of large pipes on brackets, with flanged joints and valves."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    vertical = h > (z1 - z0)
    n = max(2, min(4, int(max(w, d) / 0.55)))
    span = (z1 - z0) if vertical else (y1 - y0)
    for i in range(n):
        f = (i + 0.5) / n
        pr = min(w, 0.9) * (0.16 + 0.07 * ((i * 7) % 3)) / 1.0
        # 0.33 and not 0.42: a joint collar is 1.35x the pipe, so the collar is
        # what has to fit the box, not the pipe.
        pr = max(MIN_PART_M * 4, min(pr, min(w, d) * 0.33))
        if vertical:
            pz = z0 + (z1 - z0) * f
            px = (x0 + x1) / 2.0
            _tube(v, t, g, P.pipe, (px, y0 + 0.05, pz), (px, y1 - 0.05, pz),
                  pr, SEG_PIPE)
            nj = max(1, int(h / 2.0))
            for j in range(nj):
                jy = y0 + h * (j + 1) / (nj + 1)
                _cyl(v, t, g, P.frame, px, pz, jy - 0.05, jy + 0.05, pr * 1.35,
                     SEG_PIPE)
            for j in range(max(1, int(h / 1.8))):     # wall brackets
                by = y0 + h * (j + 0.5) / max(1, int(h / 1.8))
                _box(v, t, g, P.frame, (x0, by - 0.06, pz - pr * 1.2),
                     (px, by + 0.06, pz + pr * 1.2))
            if i == 0:
                vy = min(max(GAUGE_Y_M, y0 + 0.5), y1 - 0.5)
                _cyl(v, t, g, P.conduit, px, pz, vy - 0.12, vy + 0.12,
                     pr * 1.5, SEG_PIPE)
                hx_ = min(px + w * 0.42, x1 - pr * 1.1)
                _tube(v, t, g, P.conduit, (px, vy, pz), (hx_, vy, pz),
                      0.035, SEG_BOLT)
                _cyl(v, t, g, P.conduit, hx_, pz, vy - 0.02, vy + 0.02,
                     pr * 1.1, SEG_PIPE)
        else:
            py = y0 + (y1 - y0) * f * 0.86 + 0.10
            px = (x0 + x1) / 2.0
            _tube(v, t, g, P.pipe, (px, py, z0 + 0.05), (px, py, z1 - 0.05),
                  pr, SEG_PIPE)
            nj = max(1, int((z1 - z0) / 2.4))
            for j in range(nj):
                jz = z0 + (z1 - z0) * (j + 1) / (nj + 1)
                _tube(v, t, g, P.frame, (px, py, jz - 0.05), (px, py, jz + 0.05),
                      pr * 1.35, SEG_PIPE)
    ns = max(2, int((z1 - z0) / 2.6)) if not vertical else 0
    for j in range(ns):                          # saddle stands
        sz = z0 + (z1 - z0) * (j + 0.5) / ns
        _box(v, t, g, P.frame, ((x0 + x1) / 2 - 0.07, y0, sz - 0.07),
             ((x0 + x1) / 2 + 0.07, y1 - 0.08, sz + 0.07))
        _box(v, t, g, P.frame, (x0 + 0.02, y1 - 0.10, sz - 0.09),
             (x1 - 0.02, y1 - 0.02, sz + 0.09))


def _m_duct(v, t, g, box, P, seed):
    """An overhead run: a trunk in flanged sections, hangers, and a cable tray.

    The `over` fixtures are the geometry a player looks at while walking, and
    every one of them was a single extruded box.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, y1 - y0, z1 - z0
    ty = y1 - max(0.06, d * 0.22)
    _box(v, t, None, "", (x0, y0 + d * 0.10, z0), (x1, ty, z1))
    nj = max(1, int((z1 - z0) / 1.3))
    for j in range(nj + 1):
        jz = z0 + (z1 - z0) * j / max(1, nj)
        jz = min(max(jz, z0 + 0.03), z1 - 0.03)
        _box(v, t, g, P.frame, (x0 - 0.035, y0 + d * 0.05, jz - 0.030),
             (x1 + 0.035, ty + 0.035, jz + 0.030))
    nh = max(2, int((z1 - z0) / 1.9))
    for j in range(nh):                          # hanger rods to the soffit
        hz = z0 + (z1 - z0) * (j + 0.5) / nh
        for s in (-1, 1):
            hx = (x0 + x1) / 2.0 + s * w * 0.40
            _tube(v, t, g, P.frame, (hx, ty, hz), (hx, y1, hz), 0.022, SEG_BOLT)
        _box(v, t, g, P.frame, ((x0 + x1) / 2 - w * 0.46, y1 - 0.05, hz - 0.03),
             ((x0 + x1) / 2 + w * 0.46, y1, hz + 0.03))
    # a cable tray running alongside, and the conduit dropping off it
    _box(v, t, g, P.conduit, (x1 - w * 0.20, y0 + d * 0.02, z0),
         (x1 + 0.02, y0 + d * 0.14, z1))
    for j in range(max(1, int((z1 - z0) / 2.6))):
        cz = z0 + (z1 - z0) * (j + 0.6) / max(1, int((z1 - z0) / 2.6))
        _tube(v, t, g, P.conduit, (x1 - w * 0.10, y0 + d * 0.30, cz),
              (x1 - w * 0.10, y0, cz), 0.030, SEG_BOLT)


def _m_crane(v, t, g, box, P, seed):
    """A bridge crane: girder, end trucks, a crab, a hoist block and a hook."""
    x0, y0, z0, x1, y1, z1 = box
    w, d = x1 - x0, y1 - y0
    gy = y1 - max(0.05, d * 0.28)
    _box(v, t, None, "", (x0, gy, z0), (x1, y1, z1))
    # WEB STIFFENERS. A bridge girder is a plate girder and the stiffeners are
    # what stop its web buckling -- so the count is set by the SPAN, which is
    # what `_plate_face` at the kit's module gives. Undivided the girder is the
    # whole of the crane's silhouette at 4.079 m^-1.
    for s_ in (-1, 1):
        _plate_face(v, t, g, P.frame, (x0, gy, z0, x1, y1, z1), "x", s_,
                    proud=min(0.03, w * 0.05))
    for s, zz in ((-1, z0), (1, z1)):            # end trucks on the rail
        _box(v, t, g, P.frame, (x0 - 0.04, gy - 0.10, zz - 0.16 if s > 0 else zz),
             (x1 + 0.04, y1, zz if s > 0 else zz + 0.16))
    _box(v, t, g, P.frame, (x0 + 0.02, gy - 0.06, z0), (x1 - 0.02, gy, z1))
    cz = (z0 + z1) / 2.0 + (z1 - z0) * 0.12
    _box(v, t, g, P.frame, (x0 + w * 0.18, gy - min(0.30, d), cz - 0.18),
         (x1 - w * 0.18, gy, cz + 0.18))
    hy = gy - min(0.30, d)
    # THE WHOLE HOIST STAYS IN THE BOX, block and hook included. A block
    # hanging below the rail is what a crane does and it is also outside the
    # AABB every walkability and collision rule reads. The first version
    # clamped only the ROPE, and on a 0.70 m `over` fixture -- which is what
    # `transfer_crane` and `hoist_crane` actually are, against the 0.90 m the
    # probe used -- the block and hook still hung 56 mm below the box and the
    # interpenetration gate caught it against the cargo crane below. A probe
    # box is not the content.
    avail = max(0.0, hy - y0)
    bl = min(0.12, avail * 0.42)
    hk = min(0.14, avail * 0.34)
    drop = max(0.0, min(0.55, avail - bl - hk - 0.02))
    for s in (-1, 1):                            # the two falls of rope
        rx = (x0 + x1) / 2.0 + s * w * 0.12
        _tube(v, t, g, P.rail, (rx, hy, cz), (rx, hy - drop, cz), 0.012,
              SEG_BOLT)
    _box(v, t, g, P.frame, ((x0 + x1) / 2 - w * 0.20, hy - drop - bl, cz - 0.13),
         ((x0 + x1) / 2 + w * 0.20, hy - drop, cz + 0.13))
    _tube(v, t, g, P.hazard, ((x0 + x1) / 2, hy - drop - bl, cz),
          ((x0 + x1) / 2, hy - drop - bl - hk, cz), 0.035, SEG_BOLT)
    _tube(v, t, g, P.conduit, (x0 + w * 0.5, gy - 0.02, z0 + 0.05),
          (x0 + w * 0.5, gy - 0.02, z1 - 0.05), 0.020, SEG_BOLT)


def _m_screen(v, t, g, box, P, seed):
    """Posts, head and foot rails, and infill -- a partition, not a slab."""
    x0, y0, z0, x1, y1, z1 = box
    w, h = x1 - x0, y1 - y0
    post = min(0.06, w * 0.45)
    n = max(2, int((z1 - z0) / 1.6) + 1)
    for i in range(n):
        zz = z0 + (z1 - z0) * i / (n - 1)
        zz = min(max(zz, z0 + post), z1 - post)
        _box(v, t, g, P.frame, ((x0 + x1) / 2 - post, y0, zz - post),
             ((x0 + x1) / 2 + post, y1, zz + post))
        _box(v, t, g, P.frame,
             (max((x0 + x1) / 2 - post * 2.2, x0), y0,
              max(zz - post * 2.2, z0)),
             (min((x0 + x1) / 2 + post * 2.2, x1), y0 + 0.035,
              min(zz + post * 2.2, z1)))
    for k in (0.0, 0.52, 1.0):
        yy = min(y0 + h * k, y1 - 0.05)
        _box(v, t, g, P.frame, ((x0 + x1) / 2 - post * 0.8, yy, z0),
             ((x0 + x1) / 2 + post * 0.8, yy + 0.05, z1))
    for i in range(n - 1):                       # infill panels between posts
        za = z0 + (z1 - z0) * i / (n - 1) + post * 1.4
        zb = z0 + (z1 - z0) * (i + 1) / (n - 1) - post * 1.4
        if zb - za < 0.15:
            continue
        lo = (x0 + w * 0.28, y0 + 0.06, za, x1 - w * 0.28, y0 + h * 0.50, zb)
        _box(v, t, None, "", lo[:3], lo[3:])
        hi = (x0 + w * 0.34, y0 + h * 0.56, za,
              x1 - w * 0.34, min(y0 + h * 0.96, y1 - 0.06), zb)
        _box(v, t, g, P.screen, hi[:3], hi[3:])
        # Both infills divided at the kit's module, on the face a shopper is
        # standing at. The panels are what a market stall IS, and undivided
        # they are the whole of this machine's area at 4.145 m^-1.
        for s_ in (-1, 1):
            _plate_face(v, t, g, P.conduit, lo, "x", s_, proud=w * 0.05)
            _plate_face(v, t, g, P.frame, hi, "x", s_, proud=w * 0.05)


def _m_gantry(v, t, g, box, P, seed):
    """A column, a swung arm, a head with a lens, and a control pad.

    The medical and research flank fixture. A "diagnostic gantry" that is a
    2.3 m slab is the medlab's version of the reactor's rectangular pier.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    # THE COLUMN IS ROUND, so its radius comes off the SMALLER plan dimension.
    # Sizing it off `w` alone put a 0.36 m column in a 0.46 m deep footprint --
    # 0.18 m outside it, in the eight medlabs.
    s = min(w, d)
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    _box(v, t, g, P.frame, (cx - w * 0.34, y0, cz - min(0.24, d * 0.34)),
         (cx + w * 0.34, y0 + 0.07, cz + min(0.24, d * 0.34)))
    _tube(v, t, None, "", (cx, y0 + 0.05, cz), (cx, y1 - 0.22, cz),
          max(0.04, s * 0.24), SEG_PIPE)
    # Collars are RINGS -- the column runs through them (see `_band`) -- and
    # they sit at the kit's course, so the count follows the column's height
    # instead of a fixed 1.5 m.
    col_r = max(0.04, s * 0.24)
    n = max(1, int(h / kit_module()[1]))
    for i in range(n):
        jy = y0 + h * (i + 1) / (n + 1)
        _ring(v, t, g, P.frame, cx, cz, jy - 0.035, jy + 0.035,
              col_r * 0.92, min(max(0.055, s * 0.30), s * 0.46), SEG_PIPE)
    ay = y1 - 0.25
    reach = max(0.0, min(1.0, d * 0.5 - s * 0.34))
    _tube(v, t, g, P.frame, (cx, ay, cz), (cx, ay, cz - reach),
          max(0.030, s * 0.15), SEG_PIPE)
    _box(v, t, None, "", (cx - w * 0.30, ay - 0.24,
                          max(z0, cz - reach - s * 0.30)),
         (cx + w * 0.30, ay + 0.10, min(z1, cz - reach + s * 0.20)))
    _tube(v, t, g, P.screen, (cx, ay - 0.24, cz - reach),
          (cx, ay - 0.34, cz - reach), max(0.04, s * 0.22), SEG_PIPE)
    py = min(GAUGE_Y_M, y1 - 0.5)
    _box(v, t, g, P.panel, (cx - w * 0.30, py - 0.02, z0),
         (cx + w * 0.30, py + 0.30, z0 + d * 0.28))
    _box(v, t, g, P.screen, (cx - w * 0.22, py + 0.04, z0 - 0.0),
         (cx + w * 0.22, py + 0.24, z0 + 0.02))
    _tube(v, t, g, P.conduit, (cx + w * 0.20, y1 - 0.30, cz),
          (cx + w * 0.20, y1, cz), 0.028, SEG_BOLT)


def _m_console(v, t, g, box, P, seed):
    """Raked face, bezel, screen, knee recess -- and side cheeks under it."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    face = x0 if _u(seed, "cf") < 0.5 else x1
    sgn = -1.0 if face == x0 else 1.0
    # the knee recess IS the articulation: the body is set back off the floor
    ch = min(0.07, d * 0.3)
    _box(v, t, g, P.frame, (x0, y0, z0), (x1, y0 + 0.09, z1))
    low = (x0 + (w * 0.22 if sgn > 0 else 0.008), y0 + 0.06, z0 + ch * 0.5,
           x1 - (w * 0.22 if sgn < 0 else 0.008), y0 + h * 0.44, z1 - ch * 0.5)
    _box(v, t, None, "", low[:3], low[3:])
    # THE RACK BAYS. This carcass is the console's largest piece and the only
    # joints the builder had were on the operator face at a fixed 0.70 m, so a
    # 2.40 m plot table presented two 2.2 m long sides with nothing on them.
    for zz in (z0, z1 - ch):                     # cheeks reaching the floor
        _box(v, t, None, "", (x0 + 0.004, y0 + 0.085, zz),
             (x1 - 0.004, y0 + h * 0.66, zz + ch))
    for side in (-1, 1):
        _plate_face(v, t, g, P.conduit, low, "x", side,
                    proud=min(0.014, min(w, d) * 0.02))
    bod = (x0, y0 + h * 0.40, z0 + ch * 0.25, x1, y0 + h * 0.665, z1 - ch * 0.25)
    _box(v, t, None, "", bod[:3], bod[3:])
    # THE BACK AND SIDES OF A CONSOLE ARE RACK PANELS. `_face_strip` below puts
    # joints on the OPERATOR face only, at a fixed 0.70 m, so a 2.40 m
    # `plot_plant_frame` presents 46.6 m2 at 4.522 m^-1 with 4.51 normals -- and
    # the face a player walks PAST is the one that was left plain.
    for side in (-1, 1):
        _plate_face(v, t, g, P.conduit, bod, "z", side, proud=min(w, d) * 0.04)
    # raked top: a shallow wedge, expressed as two steps rather than a bevel
    _top_pr = min(0.012, h * 0.02)
    top = (x0, y0 + h * 0.66, z0, x1, y0 + h * 0.76, z1)
    _box(v, t, g, P.panel, top[:3], (top[3], top[4] - _top_pr, top[5]))
    # AND THE TOP IS THE BIGGEST FACE ON THE OBJECT. On the 2.40 m
    # `plot_plant_frame` the raked top alone is 6.05 m2 of the console's 46.6 --
    # more than any wall of it -- and every joint this builder had ran on a
    # VERTICAL face, so the surface a player looks DOWN on was the plain one. A
    # console top is made of modules; at `kit_tile()` it is divided into them.
    _plate_face(v, t, g, P.conduit, top, "y", 1, proud=_top_pr)
    b = w * 0.16
    _box(v, t, g, P.frame,
         (x0 + (b if sgn > 0 else 0.0), y0 + h * 0.74,
          z0 + min(0.05, d * 0.2)),
         (x1 - (b if sgn < 0 else 0.0), y0 + h * 0.88,
          z1 - min(0.05, d * 0.2)))
    scr = (x0 + (b * 1.5 if sgn > 0 else 0.03), y0 + h * 0.78,
           z0 + min(0.10, d * 0.28),
           x1 - (b * 1.5 if sgn < 0 else 0.03), y0 + h * 0.86,
           z1 - min(0.10, d * 0.28))
    _box(v, t, g, P.screen, scr[:3], scr[3:])
    # A bezel, for the reason `_m_wallpanel` gives: a screen has one at every
    # size, and this one is 4.59 m2 at 2.75 m^-1 on the largest console.
    _face_rim(v, t, g, P.frame, scr, "y", 1,
              min(scr[3] - scr[0], scr[5] - scr[2]) * 0.10, h * 0.02)
    # a rail along the operator edge, and a lit strip under the nose
    ex = face - sgn * 0.02
    _tube(v, t, g, P.rail, (ex, y0 + h * 0.70, z0 + 0.06),
          (ex, y0 + h * 0.70, z1 - 0.06), 0.022, SEG_BOLT)
    _box(v, t, g, P.conduit, (min(ex, ex - sgn * 0.04),
                              y0 + h * 0.62, z0 + 0.10),
         (max(ex, ex - sgn * 0.04), y0 + h * 0.66, z1 - 0.10))
    # Panel joints down the operator face and the back, which is what turns a
    # cabinet-shaped body into a console built out of modules.
    nz = max(2, int(d / 0.70))
    for j in range(1, nz):
        jz = z0 + d * j / nz
        for s_ in (-1, 1):
            _face_strip(v, t, g, P.conduit, box, "x", s_, jz - 0.014,
                        jz + 0.014, y0 + 0.12, y0 + h * 0.62, 0.012)
    _perim_band(v, t, g, P.frame, x0, z0, x1, z1, y0 + h * 0.36,
                y0 + h * 0.42, 0.012)
    _perim_band(v, t, g, P.conduit, x0, z0, x1, z1, y0 + h * 0.665,
                y0 + h * 0.695, 0.010)
    # a vent grille row under the working face -- a console is a machine that
    # has to breathe, and three slats is three lines
    for k in range(3):
        yy = y0 + h * (0.20 + 0.07 * k)
        _face_strip(v, t, g, P.conduit, box, "x", -1 if sgn > 0 else 1,
                    z0 + d * 0.18, z1 - d * 0.18, yy, yy + h * 0.030, 0.010)


def _m_skid(v, t, g, box, P, seed, reel=False):
    """A pump skid, or a hose reel: a baseplate carrying a rotating machine.

    Both are "a frame with a cylinder on it and pipework leaving it", which is
    a silhouette no other machine in the kit has.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    _base_pr = min(0.012, h * 0.02)
    base = (x0, y0, z0, x1, y0 + min(0.14, h * 0.14), z1)
    _box(v, t, g, P.frame, base[:3], (base[3], base[4] - _base_pr, base[5]))
    # A skid baseplate is a CHEQUER DECK, and it is the largest single face on
    # the machine -- on the `umbilical_plant_pipe` reel the three `plant_frame`
    # pieces are 7.62 m2 of the object's 12.76 at 5.58 m^-1, and most of that is
    # this plate. `kit_tile()`, as everywhere else horizontal.
    _plate_face(v, t, g, P.tread, base, "y", 1, proud=_base_pr)
    by = y0 + min(0.14, h * 0.14)
    r = min(min(w, d) * 0.34, (y1 - by) * 0.36)
    ax_y = by + r + min(0.18, h * 0.10)
    if reel:
        rr = min(r * 1.5, (y1 - by) * 0.42, d * 0.42)
        ax_y = by + rr * 1.35
        _tube(v, t, None, "", (x0 + w * 0.18, ax_y, cz), (x1 - w * 0.18, ax_y, cz),
              rr, SEG_PIPE)
        # CHEEKS ARE RINGS: the reel drum runs THROUGH them, so a `_tube`'s two
        # end caps are pi*r^2 of surface buried in the drum. See `_band`.
        for s in (-1, 1):                        # cheek plates
            ck = min(rr * 1.32, ax_y - by, d * 0.48)
            _band(v, t, g, P.frame,
                  (cx + s * w * 0.20, ax_y, cz), (cx + s * w * 0.26, ax_y, cz),
                  min(rr * 0.90, ck * 0.85), ck, SEG_BODY)
        _tube(v, t, g, P.conduit, (cx, ax_y - rr, cz),
              (cx, by + 0.02, cz), rr * 0.30, SEG_PIPE)
    else:
        vx = x1 - max(w * 0.16, r * 1.25)
        _tube(v, t, None, "", (x0 + w * 0.10, ax_y, cz), (cx + w * 0.06, ax_y, cz),
              r, SEG_PIPE)                                     # motor
        for i in range(4):                                     # cooling fins
            fx = x0 + w * (0.16 + 0.14 * i)
            _band(v, t, g, P.frame, (fx, ax_y, cz), (fx + 0.02, ax_y, cz),
                  r * 0.95, r * 1.16, SEG_PIPE)
        _tube(v, t, g, P.conduit, (cx + w * 0.06, ax_y, cz),
              (cx + w * 0.16, ax_y, cz), r * 0.55, SEG_PIPE)   # coupling guard
        _cyl(v, t, None, "", vx, cz, by, min(ax_y + r * 0.9, y1 - 0.05),
             r * 1.15, SEG_PIPE)                               # volute
        _tube(v, t, g, P.pipe, (vx, ax_y, cz), (vx, ax_y, z0 + 0.02),
              r * 0.5, SEG_PIPE)
        _tube(v, t, g, P.pipe, (vx, min(ax_y + r * 0.9, y1 - 0.05), cz),
              (vx, y1 - 0.03, cz), r * 0.45, SEG_PIPE)
    gy = min(GAUGE_Y_M, y1 - 0.35)
    gw = min(0.5, d * 0.7, w * 0.6)
    gx = min(max(x0 + w * 0.18, x0 + gw / 2 + 0.06), x1 - gw / 2 - 0.06)
    _box(v, t, g, P.panel, (gx - gw * 0.7, gy, z1 - min(0.10, d * 0.24)),
         (gx + gw * 0.7, gy + 0.34, z1))
    _gauges(v, t, g, P, gx, gy + 0.17, z1 - 0.06, 0.0, 1.0, gw, seed)


def _m_block(v, t, g, box, P, seed):
    """A massive block in expressed courses: a shield wall, a bund, a plinth.

    Not everything in a plant room is a machine. What makes a solid mass read
    as built rather than as a primitive is the joint pattern, a chamfered top
    course, corner armour and the one thing set INTO it -- here a plug hatch.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    # COURSES AND A PANEL FIELD. Courses alone left the block at 1.52 m^-1 of
    # line -- one line every 0.66 m over a 7.5 m wall, which is a wall with
    # stripes on it. What makes a mass read as BUILT is the block joint: a
    # course band horizontally AND a stack joint vertically, so the eye reads a
    # unit size rather than a stripe pitch.
    # ONE BODY, then bands and joints ON its faces. The first version stacked
    # `n` full-depth boxes and wrapped each in a full-depth band: 622.7 m2 of
    # surface for a mass whose outside is 82, and 2.05 m^-1 of line on it.
    _cap_pr = min(0.03, w * 0.04)
    _box(v, t, None, "", (x0, y0, z0), (x1, y1 - _cap_pr, z1))
    n = max(2, int(h / 0.78))
    nz = max(2, int((z1 - z0) / 0.95))
    for i in range(n):
        ya = y0 + h * i / n
        yb = y0 + h * (i + 1) / n
        if i < n - 1:
            _perim_band(v, t, g, P.frame, x0, z0, x1, z1, yb - 0.045, yb)
        # stack joints, staggered course by course like real blockwork, and on
        # the two long faces only -- the ends are 1.6 m of nothing
        for j in range(nz):
            jz = z0 + (z1 - z0) * (j + (0.5 if i % 2 else 0.0)) / nz
            if jz <= z0 + 0.06 or jz >= z1 - 0.06:
                continue
            for side in (-1, 1):
                _face_strip(v, t, g, P.frame, box, "x", side,
                            jz - 0.025, jz + 0.025, ya + 0.03, yb - 0.06)
    # THE ENDS AND THE TOP. The comment above says the stack joints are "on the
    # two long faces only -- the ends are 1.6 m of nothing", which was true and
    # left 24 m2 of end and 5 m2 of top undivided on the reactor shield: the
    # body alone is 78.69 m2 of the block's 107.67 and carries no line at all.
    # Same module, on the faces the joints skipped.
    for side in (-1, 1):
        _plate_face(v, t, g, P.frame, (x0, y0, z0, x1, y1, z1), "z", side,
                    proud=min(0.03, w * 0.04))
    _plate_face(v, t, g, P.frame, (x0, y0, z0, x1, y1, z1), "y", 1,
                proud=_cap_pr)
    ca = min(0.07, w * 0.2, d * 0.2)             # corner armour
    for ax_ in (x0, x1 - ca):
        for az in (z0, z1 - ca):
            _box(v, t, g, P.frame, (ax_ - 0.01, y0, az - 0.01),
                 (ax_ + ca + 0.01, y0 + min(0.9, h * 0.5), az + ca + 0.01))
    px, pz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    pr = min(0.55, min(w, d) * 0.6, h * 0.22)
    py = min(max(1.3, y0 + h * 0.35), y1 - pr - 0.2)
    face = z0 if _u(seed, "bf") < 0.5 else z1
    sg = -1.0 if face == z0 else 1.0
    _tube(v, t, g, P.frame, (px, py, face - sg * 0.10),
          (px, py, face + sg * 0.035), pr, SEG_PIPE)
    for k in range(6):
        a = math.tau * k / 6
        bx = px + pr * 1.15 * math.cos(a)
        by_ = py + pr * 1.15 * math.sin(a)
        _tube(v, t, g, P.frame, (bx, by_, face - sg * 0.02),
              (bx, by_, face + sg * 0.03), 0.026, SEG_BOLT)
    _perim_band(v, t, g, P.hazard, x0, z0, x1, z1, y0 + 0.05,
                y0 + 0.05 + min(HAZARD_H_M, h * 0.12), 0.008)
    # PENETRATIONS AND LIFTING LUGS. A shield is a thing services pass through
    # and a thing that was craned into place; both are lines, and both are the
    # reason it reads as built rather than poured.
    nsl = max(2, int((z1 - z0) / 1.1))
    for j in range(nsl):
        pz2 = z0 + (z1 - z0) * (j + 0.5) / nsl
        _tube(v, t, g, P.conduit,
              (x0 + 0.02, min(2.35, y0 + h * 0.62), pz2),
              (x1 - 0.02, min(2.35, y0 + h * 0.62), pz2), 0.045, SEG_BOLT)
    for j in range(max(2, int((z1 - z0) / 1.6))):
        lz = z0 + (z1 - z0) * (j + 0.5) / max(2, int((z1 - z0) / 1.6))
        _box(v, t, g, P.frame, ((x0 + x1) / 2 - 0.06, y1 - 0.22, lz - 0.14),
             ((x0 + x1) / 2 + 0.06, y1, lz + 0.14))


def _m_kerb(v, t, g, box, P, seed):
    """A low platform: nosing, a riser course and a tread lip.

    `platform_edge` and `dais` are 0.22 and 0.35 m tall and no articulation
    finer than the step itself will read on them, so this is deliberately the
    cheapest machine in the kit. Spending a vessel's triangle count on a kerb
    would be detail nobody can see, which the standard calls waste rather than
    craft.
    """
    x0, y0, z0, x1, y1, z1 = box
    h = max(y1 - y0, 0.06)
    _tread_pr = min(0.014, h * 0.10)
    _box(v, t, None, "", (x0, y0, z0), (x1, y1 - _tread_pr, z1))
    # THE TREAD IS 69% OF THE OBJECT and it was the one surface with nothing on
    # it: the 1.80 x 8.00 m `catwalk`'s body is 29.75 m2 of its 43.11, all of it
    # top and underside, against 13.36 m2 of nosing and hazard band carrying
    # every line. A catwalk is laid in PLATES, so it gets `kit_tile()` -- the
    # same substitution `_m_rack`'s slatted shelves and `_m_console`'s top make,
    # and for the same reason: there is no course height on a floor.
    _plate_face(v, t, g, P.tread, (x0, y0, z0, x1, y1, z1), "y", 1,
                proud=_tread_pr)
    _perim_band(v, t, g, P.frame, x0, z0, x1, z1, y1 - h * 0.30, y1, 0.022)
    _perim_band(v, t, g, P.hazard, x0, z0, x1, z1, y1 - h * 0.62,
                y1 - h * 0.36, 0.028)
    n = max(2, int(max(x1 - x0, z1 - z0) / 1.4))
    long_z = (z1 - z0) >= (x1 - x0)
    for i in range(n):                            # stringers under the tread
        if long_z:
            zz = z0 + (z1 - z0) * (i + 0.5) / n
            _box(v, t, g, P.frame, (x0 - 0.005, y0, zz - 0.05),
                 (x1 + 0.005, y0 + h * 0.30, zz + 0.05))
        else:
            xx = x0 + (x1 - x0) * (i + 0.5) / n
            _box(v, t, g, P.frame, (xx - 0.05, y0, z0 - 0.005),
                 (xx + 0.05, y0 + h * 0.30, z1 + 0.005))


def _m_counter(v, t, g, box, P, seed):
    """A counter, desk, bench or table: kick recess, apron, nosed top, front.

    The declared props are as boxy as the fixtures were -- `prop_counter` is a
    2.40 x 0.60 x 1.05 m slab and `rooms.PROPS`' comment says so outright: "a
    prop IS a box". The three lines that make a counter read are the KICK
    RECESS at the floor, the NOSING proud of the top, and a front broken into
    panels; all three are what the eye uses to tell a counter from a plinth.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    kick = min(0.11, h * 0.14)
    top = min(0.05, h * 0.09)
    _box(v, t, g, P.frame, (x0 + w * 0.10, y0, z0 + d * 0.10),
         (x1 - w * 0.10, y0 + kick, z1 - d * 0.10))
    long_z = d >= w
    carc = (x0 + 0.006, y0 + kick, z0 + 0.006,
            x1 - 0.006, y1 - top * 0.5, z1 - 0.006)
    _box(v, t, None, "", carc[:3], carc[3:])
    # THE CARCASS IS PANELLED ON ITS LONG FACES. The `public_gallery` bench is
    # 4.00 m long and its carcass is one 4 m plate: 45.9 m2 at 4.147 m^-1, the
    # largest single object in the Law Courts. The front panels below are a
    # fixed 0.85 m run and stop at the front; this is the same division carried
    # round, at the kit's module, on both long sides.
    for side in (-1, 1):
        _plate_face(v, t, g, P.conduit, carc, "x" if long_z else "z", side,
                    proud=min(w, d) * 0.05)
    _box(v, t, g, P.panel, (x0, y1 - top, z0), (x1, y1, z1))
    _perim_band(v, t, g, P.panel, x0, z0, x1, z1, y1 - top * 0.55, y1 - 0.004,
                0.014)
    n = max(1, int(max(w, d) / 0.85))
    for i in range(n):                            # front panels
        f0 = (z0 if long_z else x0) + (d if long_z else w) * (i + 0.10) / n
        f1 = (z0 if long_z else x0) + (d if long_z else w) * (i + 0.90) / n
        if long_z:
            _box(v, t, g, P.panel, (x0 - 0.010, y0 + kick + 0.05, f0),
                 (x0 + 0.004, y1 - top - 0.06, f1))
        else:
            _box(v, t, g, P.panel, (f0, y0 + kick + 0.05, z0 - 0.010),
                 (f1, y1 - top - 0.06, z0 + 0.004))
    # an under-shelf, which is where the things behind a counter live
    _box(v, t, g, P.tread, (x0 + w * 0.14, y0 + h * 0.46, z0 + d * 0.14),
         (x1 - w * 0.14, y0 + h * 0.50, z1 - d * 0.14))
    # drawer lines under the top and a foot rail at the kick: the two features
    # that separate a counter from a plinth at half distance
    for k in (0.72, 0.86):
        if y0 + h * k > y1 - top - 0.02:
            continue
        if long_z:
            _face_strip(v, t, g, P.conduit, box, "x", -1,
                        z0 + d * 0.05, z1 - d * 0.05,
                        y0 + h * k, y0 + h * (k + 0.022))
        else:
            _face_strip(v, t, g, P.conduit, box, "z", -1,
                        x0 + w * 0.05, x1 - w * 0.05,
                        y0 + h * k, y0 + h * (k + 0.022))
    if long_z:
        _tube(v, t, g, P.rail, (x0 - 0.02, y0 + kick * 1.6, z0 + d * 0.06),
              (x0 - 0.02, y0 + kick * 1.6, z1 - d * 0.06),
              min(0.020, w * 0.06), SEG_BOLT)
    else:
        _tube(v, t, g, P.rail, (x0 + w * 0.06, y0 + kick * 1.6, z0 - 0.02),
              (x1 - w * 0.06, y0 + kick * 1.6, z0 - 0.02),
              min(0.020, d * 0.06), SEG_BOLT)
    if h > 0.85 and min(w, d) > 0.30:             # a till face in the counter
        cx, cz = (x0 + x1) / 2.0, z0 + d * 0.30
        _box(v, t, g, P.screen,
             (x0 - 0.014, y1 - top - 0.30, cz - min(0.16, d * 0.24)),
             (x0 + 0.002, y1 - top - 0.06, cz + min(0.16, d * 0.24)))


def _m_bed(v, t, g, box, P, seed):
    """A bed, bunk, pod or drawer: base, deck, side rails and a head unit."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    long_z = d >= w
    ln = max(w, d)
    base = min(0.16, h * 0.30)
    # THE DECK IS 72% OF THE BOX so the head unit and the side rails have
    # somewhere to be. The first version put both ABOVE the declared height and
    # the bed left its own AABB by 0.22 m.
    deck = y0 + (y1 - y0) * 0.70
    _box(v, t, g, P.frame, (x0 + w * 0.12, y0, z0 + d * 0.12),
         (x1 - w * 0.12, y0 + base, z1 - d * 0.12))
    carc = (x0 + 0.004, y0 + base * 0.5, z0 + 0.004,
            x1 - 0.004, deck - 0.03, z1 - 0.004)
    _box(v, t, None, "", carc[:3], carc[3:])
    # The carcass is drawered on its long sides. A `cryo_pod` is 2.20 m long
    # and its carcass is one plate that long -- 18.4 m2 at 4.550 m^-1 -- and a
    # pod, a bunk or a cold drawer is a stack of units, which is what the
    # division at the kit's module says.
    for side in (-1, 1):
        _plate_face(v, t, g, P.conduit, carc, "x" if long_z else "z", side,
                    proud=min(w, d) * 0.05)
    _box(v, t, g, P.panel, (x0 + w * 0.03, deck - 0.04, z0 + d * 0.03),
         (x1 - w * 0.03, deck, z1 - d * 0.03))
    # the mattress deck is SECTIONED -- a bed articulates, and the sections are
    # the only lines a flat pallet has
    for k in (0.34, 0.62):
        if long_z:
            _perim_band(v, t, g, P.conduit, x0 + w * 0.03, z0 + d * k,
                        x1 - w * 0.03, z0 + d * (k + 0.03), deck - 0.045,
                        deck + 0.004, 0.008)
        else:
            _perim_band(v, t, g, P.conduit, x0 + w * k, z0 + d * 0.03,
                        x0 + w * (k + 0.03), z1 - d * 0.03, deck - 0.045,
                        deck + 0.004, 0.008)
    _box(v, t, g, P.tread, (x0 + w * 0.14, y0 + base, z0 + d * 0.16),
         (x1 - w * 0.14, y0 + base + 0.035, z1 - d * 0.16))
    for s in (-1, 1):                              # side rails
        if long_z:
            xx = (x0 + x1) / 2.0 + s * (w / 2 - 0.03)
            _tube(v, t, g, P.rail, (xx, deck + 0.02, z0 + ln * 0.20),
                  (xx, deck + 0.02, z1 - ln * 0.20), 0.020, SEG_BOLT)
        else:
            zz = (z0 + z1) / 2.0 + s * (d / 2 - 0.03)
            _tube(v, t, g, P.rail, (x0 + ln * 0.20, deck + 0.02, zz),
                  (x1 - ln * 0.20, deck + 0.02, zz), 0.020, SEG_BOLT)
    # head unit: the thing that makes a bed a DIAGNOSTIC bed
    if long_z:
        _box(v, t, g, P.panel, (x0 + w * 0.10, y0 + base, z0),
             (x1 - w * 0.10, y1, z0 + d * 0.14))
        _box(v, t, g, P.screen, (x0 + w * 0.20, deck + 0.05, z0 - 0.004),
             (x1 - w * 0.20, y1 - 0.02, z0 + 0.004))
    else:
        _box(v, t, g, P.panel, (x0, y0 + base, z0 + d * 0.10),
             (x0 + w * 0.14, y1, z1 - d * 0.10))
        _box(v, t, g, P.screen, (x0 - 0.004, deck + 0.05, z0 + d * 0.20),
             (x0 + 0.004, y1 - 0.02, z1 - d * 0.20))


def _m_seat(v, t, g, box, P, seed):
    """Legs, a seat pan and a back. `dressing._chair`'s form at prop scale."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    lw = min(0.045, min(w, d) * 0.16)
    sy = y0 + h * (0.62 if h > 0.6 else 0.80)
    for sx in (-1, 1):
        for sz in (-1, 1):
            px = (x0 + x1) / 2.0 + sx * (w / 2 - lw)
            pz = (z0 + z1) / 2.0 + sz * (d / 2 - lw)
            _tube(v, t, g, P.frame, (px, y0, pz), (px, sy, pz), lw, SEG_BOLT)
    pan = min(0.09, h * 0.16)
    _box(v, t, None, "", (x0, sy, z0), (x1, sy + pan, z1))
    if h > 0.6:
        # overlapping the pan, not sitting on it: flush left one non-manifold
        # edge along the seat's back lip on a 0.38 m stool
        _box(v, t, g, P.panel, (x0 + 0.004, sy + pan * 0.55, z1 - d * 0.18),
             (x1 - 0.004, y1, z1 - 0.003))
    _tube(v, t, g, P.rail, (x0 + lw, sy - 0.03, z0 + lw),
          (x1 - lw, sy - 0.03, z0 + lw), lw * 0.55, SEG_BOLT)


def _m_leaf(v, t, g, box, P, seed):
    """A door leaf in its frame: reveal, leaf, kick plate, vision slot, handle.

    Fifteen of `rooms.PROPS`' entries are doors and every one was a slab. A
    door is the object a player stands closest to (`CLAUDE.md`, session 3x).
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    thin_x = w <= d
    tt = min(w, d)
    # THE REVEAL IS FOUR MEMBERS, NOT A SLAB. Built as a full box it buried
    # both leaf faces -- 21 to 36 m2 of surface on a door at 1.9 to 2.4 m^-1,
    # the least articulated object in three of the six rooms measured.
    jamb = min(0.10, max(w, d) * 0.10)
    if thin_x:
        for zz in (z0, z1 - jamb):
            _box(v, t, g, P.frame, (x0, y0, zz), (x1, y1, zz + jamb))
        _box(v, t, g, P.frame, (x0 + 0.003, y1 - jamb, z0 + 0.003),
             (x1 - 0.003, y1, z1 - 0.003))
    else:
        for xx in (x0, x1 - jamb):
            _box(v, t, g, P.frame, (xx, y0, z0), (xx + jamb, y1, z1))
        _box(v, t, g, P.frame, (x0 + 0.003, y1 - jamb, z0 + 0.003),
             (x1 - 0.003, y1, z1 - 0.003))
    if thin_x:
        leaf = (x0 + tt * 0.18, y0, z0 + d * 0.06,
                x1 - tt * 0.18, y1 - h * 0.04, z1 - d * 0.06)
        _box(v, t, None, "", leaf[:3], leaf[3:])
        _box(v, t, g, P.frame, (x0 + tt * 0.10, y0, z0 + d * 0.08),
             (x1 - tt * 0.10, y0 + min(0.22, h * 0.12), z1 - d * 0.08))
        _box(v, t, g, P.screen, (x0 + tt * 0.06, y0 + h * 0.62, z0 + d * 0.22),
             (x1 - tt * 0.06, y0 + h * 0.82, z1 - d * 0.22))
        _tube(v, t, g, P.rail, (x0, y0 + h * 0.47, z1 - d * 0.22),
              (x1, y0 + h * 0.47, z1 - d * 0.22), min(0.028, tt * 0.4),
              SEG_BOLT)
        _box(v, t, g, P.panel, (x0 - 0.006, y0 + h * 0.42, z0 - 0.006),
             (x1 + 0.006, y0 + h * 0.56, z0 + d * 0.10))
    else:
        leaf = (x0 + w * 0.06, y0, z0 + tt * 0.18,
                x1 - w * 0.06, y1 - h * 0.04, z1 - tt * 0.18)
        _box(v, t, None, "", leaf[:3], leaf[3:])
        _box(v, t, g, P.frame, (x0 + w * 0.08, y0, z0 + tt * 0.10),
             (x1 - w * 0.08, y0 + min(0.22, h * 0.12), z1 - tt * 0.10))
        _box(v, t, g, P.screen, (x0 + w * 0.22, y0 + h * 0.62, z0 + tt * 0.06),
             (x1 - w * 0.22, y0 + h * 0.82, z1 - tt * 0.06))
        _tube(v, t, g, P.rail, (x1 - w * 0.22, y0 + h * 0.47, z0),
              (x1 - w * 0.22, y0 + h * 0.47, z1), min(0.028, tt * 0.4),
              SEG_BOLT)
        _box(v, t, g, P.panel, (x0 - 0.006, y0 + h * 0.42, z0 - 0.006),
             (x0 + w * 0.10, y0 + h * 0.56, z1 + 0.006))
    # THE LEAF IS A PLATED FIELD, AT THE KIT'S OWN MODULE.
    #
    # This was three ribs at fixed fractions of the height -- 0.24, 0.36, 0.90 --
    # and the note beside them said they existed because "without them the leaf
    # is the flattest object in three of the six rooms measured (2.4 m^-1)".
    # They were right about the disease and a fixed COUNT is not the cure: on
    # the 1.90 x 2.35 m `door` three ribs is one every 0.78 m and the leaf
    # measures 6.14 m^-1, while on the 6.00 x 5.00 m `bay_door` the same three
    # are 104 m2 at 2.594 m^-1 -- the least articulated object in the station,
    # and the one a player walks through. A PITCH IS A LENGTH: `kit_module()`
    # gives the plate length and course height `rooms.articulate` lays the wall
    # behind this door on, so the leaf gets 5 x 11 plates where the wall would
    # get 5 x 11, and a small door still gets its own handful.
    #
    # `_plate_face` returns 0 on a face smaller than one module, so a 0.6 m
    # cell-door leaf is left alone rather than given one plate and a rim.
    lp = min(abs(leaf[0] - x0), abs(leaf[2] - z0)) * 0.9
    for side in (-1, 1):
        _plate_face(v, t, g, P.conduit, leaf, "x" if thin_x else "z", side,
                    proud=lp, margin=0.0)


def _m_wallpanel(v, t, g, box, P, seed):
    """A wall terminal: mounting plate, a bezel of four members, screen, keypad.

    THE BEZEL WAS A THIRD FULL-FACE SLAB AND THE MOUNTING PLATE WAS ENTIRELY
    INSIDE IT. Measured, before this was rewritten: the `monitor_wall` at
    3.20 x 1.80 m read 27.9 m2 at **2.161 m^-1 with 2.49 effective normals** --
    the flattest and by some way the boxiest object the kit builds, on a bounding
    box whose whole surface is 12.7 m2. Three near-identical plates were stacked
    on one another, and the first of them, the one the docstring calls the
    mounting plate, spanned x0+0.55t..x1 inside a housing spanning x0+0.20t..x1
    and inset 6% in both other axes -- so it was **100% buried**, 9.5 m2 of
    surface with no visible face at all, on every one of the twenty-five props
    that use this builder.

    Rebuilt as TWO plates instead of three -- the housing, which the object has
    to have to be a solid, and the screen -- with the third replaced by
    `_plate_face` dividing the screen at the kit's own module, so a monitor
    wall is a wall OF MONITORS and the count grows with the wall.

    A `_perim_band` bezel was tried here and REMOVED, and the negative result is
    worth the line: that helper wraps a body in the HORIZONTAL plane, which is
    what a girth band on a vessel is. Round an upright screen its two side
    members came out spanning the screen's full height AND full width --
    9.099 m2 EACH, measured -- and it took the panel from 28.98 m2 to 40.67.
    A helper applied on the wrong axis is not a cheap mistake here: it is
    exactly the slab it exists to prevent.
    """
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    thin_x = w <= d
    tt = min(w, d)
    ax = "x" if thin_x else "z"
    if thin_x:
        _box(v, t, None, "", (x0 + tt * 0.26, y0, z0), (x1, y1, z1))
        scr = (x0, y0 + h * 0.12, z0 + d * 0.08,
               x0 + tt * 0.34, y1 - h * 0.12, z1 - d * 0.08)
        kp = (x0 + tt * 0.10, y0 + h * 0.02, z0 + d * 0.22,
              x0 + tt * 0.30, y0 + h * 0.10, z1 - d * 0.22)
    else:
        _box(v, t, None, "", (x0, y0, z0 + tt * 0.26), (x1, y1, z1))
        scr = (x0 + w * 0.08, y0 + h * 0.12, z0,
               x1 - w * 0.08, y1 - h * 0.12, z0 + tt * 0.34)
        kp = (x0 + w * 0.22, y0 + h * 0.02, z0 + tt * 0.10,
              x1 - w * 0.22, y0 + h * 0.10, z0 + tt * 0.30)
    # ONE SCREEN PER CELL, not one screen with lines drawn on it. Both come off
    # the SAME division -- `_face_cells` is the lattice `_plate_face` draws,
    # handed back instead of drawn -- so the bezels cannot land anywhere but
    # between the monitors. On the 3.20 x 1.80 m wall it is six panels for
    # +0.4 m2 of surface and +27 m of line against the single plate, because a
    # plate's front and back are the same area however many pieces it is in
    # while its edges are not.
    cells = _face_cells(scr, ax, margin=0.0)
    if cells:
        for c in cells:
            _box(v, t, g, P.screen, c[:3], c[3:])
    else:
        _box(v, t, g, P.screen, scr[:3], scr[3:])
    # 0.14 AND NOT 0.16: `machine()` insets by min(MACH_PROUD_M, 12% of each
    # plan dimension), so on a 0.12 m panel there is 14.4 mm to be proud into
    # and 16% of the inset thickness is 14.6. It measured 0.2 mm outside the
    # AABB -- caught by `machine_bounds_ok` at the LARGEST declared size,
    # which is a case this file did not build until now.
    _plate_face(v, t, g, P.conduit, scr, ax, -1, proud=tt * 0.14)
    # The bezel is SCALE-FREE where the field is not: `_plate_face` correctly
    # declines a 0.20 m `lift_call`, whose whole face is under two of the kit's
    # plates, and that left the smallest wallpanel at 36 triangles -- which the
    # selftest's "is not a box" gate caught. A terminal has a bezel at every
    # size, so this runs at every size.
    # The width comes off the FACE and the proud off the panel's thickness,
    # which is the only pair that is right at both ends of the range: a bezel
    # sized off the thickness is 7 mm wide on a lift-call button and vanishes,
    # and one sized off the face stands 0.3 m proud of a monitor wall.
    _face_rim(v, t, g, P.frame, scr, ax, -1,
              min(scr[4] - scr[1], scr[5] - scr[2]) * 0.08, tt * 0.14)
    _box(v, t, g, P.panel, kp[:3], kp[3:])


def _m_crate(v, t, g, box, P, seed):
    """A shipping container: proud lid, corner castings and a banding line."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    _box(v, t, None, "", (x0, y0, z0), (x1, y1, z1))
    _perim_band(v, t, g, P.frame, x0, z0, x1, z1, y1 - h * 0.10, y1, 0.014)
    c = min(0.09, min(w, d) * 0.16)
    for sx in (x0, x1 - c):
        for sz in (z0, z1 - c):
            _box(v, t, g, P.frame, (sx - 0.008, y0, sz - 0.008),
                 (sx + c + 0.008, y1 - h * 0.10, sz + c + 0.008))
    for k in (0.30, 0.52, 0.74):                  # corrugation, and a placard
        _perim_band(v, t, g, P.conduit, x0, z0, x1, z1, y0 + h * k,
                    y0 + h * (k + 0.035), 0.010)
    _box(v, t, g, P.hazard, (x0 - 0.012, y0 + h * 0.42, z0 + d * 0.30),
         (x0 + 0.002, y0 + h * 0.62, z0 + d * 0.70))


def _m_post(v, t, g, box, P, seed):
    """A bollard, standpipe or handhold: base, shaft, collar and a cap."""
    x0, y0, z0, x1, y1, z1 = box
    w, d, h = x1 - x0, z1 - z0, y1 - y0
    if h < max(w, d) * 0.9:                        # lying down: a grab rail
        long_z = d >= w
        r = max(MIN_PART_M, min(h, min(w, d)) * 0.36)
        if long_z:
            a = ((x0 + x1) / 2, (y0 + y1) / 2, z0 + r)
            b = ((x0 + x1) / 2, (y0 + y1) / 2, z1 - r)
        else:
            a = (x0 + r, (y0 + y1) / 2, (z0 + z1) / 2)
            b = (x1 - r, (y0 + y1) / 2, (z0 + z1) / 2)
        _tube(v, t, g, P.rail, a, b, r, SEG_PIPE)
        for p in (a, b):                           # the feet it is bolted on
            _box(v, t, g, P.frame, (p[0] - r * 1.4, p[1] - r * 1.4, p[2] - r * 1.4),
                 (p[0] + r * 1.4, p[1] + r * 1.4, p[2] + r * 1.4))
        return
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    r = min(w, d) / 2.0 * 0.80
    _cyl(v, t, g, P.frame, cx, cz, y0, y0 + min(0.05, h * 0.08), r * 1.22,
         SEG_PIPE)
    _cyl(v, t, None, "", cx, cz, y0 + min(0.04, h * 0.06), y1 - h * 0.06, r,
         SEG_PIPE)
    _cyl(v, t, g, P.hazard, cx, cz, y0 + h * 0.62, y0 + h * 0.74, r * 1.06,
         SEG_PIPE)
    _dome(v, t, g, P.frame, cx, cz, y1 - h * 0.08, r, h * 0.08, SEG_PIPE, 2)


MACHINES = {
    "vessel": _m_vessel,
    "counter": _m_counter,
    "bed": _m_bed,
    "seat": _m_seat,
    "leaf": _m_leaf,
    "wallpanel": _m_wallpanel,
    "crate": _m_crate,
    "post": _m_post,
    "furnace": lambda *a, **k: _m_vessel(*a, furnace=True, **k),
    "drum": _m_drum,
    "rack": _m_rack,
    "cabinet": _m_cabinet,
    "pipe_bank": _m_pipe_bank,
    "duct": _m_duct,
    "crane": _m_crane,
    "screen": _m_screen,
    "gantry": _m_gantry,
    "console": _m_console,
    "skid": _m_skid,
    "reel": lambda *a, **k: _m_skid(*a, reel=True, **k),
    "block": _m_block,
    "kerb": _m_kerb,
}


def machine(v, t, g, kind, name, lo, hi, seed):
    """Build `kind` into the box (lo, hi) that `name` used to be.

    The outer span is appended FIRST and covers every triangle, so the fixture
    still owns one AABB for `rooms._solid_boxes`, `rooms.walkable` and
    `collision.prop_boxes`. The part spans follow and override the material,
    because `export_scene.per_triangle` resolves last-span-wins -- the same
    nesting `populace.py` already uses for a body's eight skin parts inside its
    `npc_standing_3` span.

    Returns the number of triangles the machine cost.
    """
    build = MACHINES.get(kind)
    if build is None:
        raise ValueError(f"{name}: no machine kind {kind!r}; have "
                         f"{sorted(MACHINES)}")
    prefix = ("prop_" if name.startswith("prop_")
              else "dress_" if name.startswith("dress_") else "fix_")
    P = _Parts(prefix)
    t0 = len(t)
    parts = []
    # THE BUILDERS WORK IN A BOX INSET IN PLAN, so that the things which are
    # SUPPOSED to stand proud -- a girth flange, a course band, a step nosing,
    # corner armour -- have somewhere to be proud into. Without it every one of
    # them left the fixture's AABB by 15 to 45 mm and `machine_bounds_ok` was a
    # gate that fired on correct geometry. The inset is in x and z only: a
    # full-height fixture has to reach the deck and the soffit, and taking it
    # off y would leave a visible gap at both.
    m = min(MACH_PROUD_M, (hi[0] - lo[0]) * 0.12, (hi[2] - lo[2]) * 0.12)
    build(v, t, parts, (lo[0] + m, lo[1], lo[2] + m,
                        hi[0] - m, hi[1], hi[2] - m), P, seed)
    if len(t) == t0:                     # a machine that built nothing is a bug
        raise ValueError(f"{name}: {kind} emitted no geometry in "
                         f"{tuple(round(hi[i] - lo[i], 3) for i in range(3))}")
    g.append((name, t0, len(t)))
    g.extend(parts)
    return len(t) - t0


def declared_boxes():
    """(smallest, largest) declared box per machine kind, as {kind: (box, src)}.

    Taken FROM `rooms.FIXTURES`, `rooms.PLACE_FIXTURES` and `rooms.PROPS`
    rather than chosen here, because a probe box is not the content: two
    closure defects fired on real content after passing on probe boxes.

    BOTH ENDS, because they are different hard cases -- see `_selftest`. The
    smallest instance is where a part runs out of room to be proud into; the
    largest is where a fixed feature count spreads thin, and no gate in this
    repository looked there until the machinery gate went 74/78 -> 68/78.
    """
    import rooms as _R                                          # noqa: PLC0415
    lo, hi = {}, {}
    def offer(k, box, nm):
        if k not in lo or _vol(box) < _vol(lo[k][0]):
            lo[k] = (box, nm)
        if k not in hi or _vol(box) > _vol(hi[k][0]):
            hi[k] = (box, nm)
    for fx in list(_R.FIXTURES.values()) + list(_R.PLACE_FIXTURES.values()):
        for nm, fw, fd, fh, _kind in fx:
            k = _R.MACHINE_KIND.get(nm)
            if k is None:
                continue
            # a 0.0 height is "to the ceiling"; 7.5 m is the tallest room the
            # register carries, so it is the largest that fixture ever gets
            h = fh if fh > 0.0 else 7.5
            offer(k, (0.0, 0.0, 0.0, max(fd, 0.06), h, max(fw, 0.06)), nm)
    for nm, (pw, pd, phh, _m) in _R.PROPS.items():
        k = _R.PROP_KIND.get(nm)
        if k is None:
            continue
        offer(k, (0.0, 0.0, 0.0, max(pd, 0.06), max(phh, 0.06), max(pw, 0.06)),
              nm)
    return lo, hi


def _vol(box):
    return box[3] * box[4] * box[5]


def machine_bounds_ok(v, t, t0, lo, hi, tol=0.0):
    """Did the machine stay inside the box it replaced?

    THE INVARIANT THE WHOLE CHANGE RESTS ON. Every walkability, collision and
    interpenetration rule in `rooms.py` reads the fixture's AABB, so as long as
    a machine never leaves the box the box already occupied, none of them can
    be made wrong by it -- and if one does leave, a room can silently become
    impassable in a way only a walk test would find. Returns the worst
    excursion in metres, which is 0.0 when it is inside.
    """
    worst = 0.0
    idx = {i for tri in t[t0:] for i in tri}
    for i in idx:
        p = v[i]
        for j in range(3):
            worst = max(worst, lo[j] - p[j] - tol, p[j] - hi[j] - tol)
    return max(0.0, worst)


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    v, t, g, c = dress("test", 6.0, 9.0, 2.9, "office")
    check("an office gets furniture", c["furniture"] > 4, str(c))
    check("...and clutter on it", c["clutter"] > 10, str(c))
    check("...and services", c["service"] > 2, str(c))
    # COVERAGE, NOT A SUM -- the same correction `rooms._selftest` records.
    # Spans NEST since INV-132: a locker's outer `dress_top` span contains its
    # door, louvre and handle parts, exactly as a body's `npc_standing_3` span
    # contains its eight skin parts. The sum was a proxy that held only while
    # nothing nested and it fires on correct data the moment something does.
    covered = set()
    for _n, lo, hi in g:
        covered.update(range(lo, hi))
    check("every triangle is grouped",
          len(covered) == len(t) and all(0 <= lo <= hi <= len(t)
                                         for _n, lo, hi in g),
          f"{len(covered)} of {len(t)}")

    # --- CLOSED, AND FACING THE RIGHT WAY -----------------------------------
    # Neither of these could be seen in a render, and both were shipped: `_cyl`
    # capped its top only (102 open edges on an assembled deck, the last ones
    # anywhere on it) and wound every one of its 24 faces INWARD, which with
    # backface culling on is an object you look straight through. A hole and an
    # inside-out surface both show the background, and the background is black.
    # `_box` beside it has always been 12/12; that is why this is a gate on the
    # primitives rather than a note about one of them.
    import interior_kit as _K                                  # noqa: PLC0415

    def _outward(pv, pt, ctr):
        good = 0
        for tri in pt:
            p0, p1, p2 = (pv[i] for i in tri)
            u = [p1[k] - p0[k] for k in range(3)]
            w = [p2[k] - p0[k] for k in range(3)]
            nn = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                  u[0] * w[1] - u[1] * w[0])
            cc = [sum(pv[i][k] for i in tri) / 3.0 - ctr[k] for k in range(3)]
            if sum(nn[k] * cc[k] for k in range(3)) > 0:
                good += 1
        return good

    for nm, build, ctr in (
            ("_box", lambda pv, pt, pg: _box(pv, pt, pg, "b", (-1, -1, -1),
                                             (1, 1, 1)), (0.0, 0.0, 0.0)),
            ("_cyl", lambda pv, pt, pg: _cyl(pv, pt, pg, "c", 0, 0, 0.0, 1.0,
                                             0.2), (0.0, 0.5, 0.0))):
        pv, pt, pg = [], [], []
        build(pv, pt, pg)
        opn, non = _K.boundary_edges(pv, pt)
        check(f"{nm} is a closed solid", not opn, f"{len(opn)} open edges")
        check(f"{nm} is manifold", not non, f"{len(non)} non-manifold edges")
        check(f"{nm} faces outward",
              _outward(pv, pt, ctr) == len(pt),
              f"{_outward(pv, pt, ctr)}/{len(pt)} outward")
    # And over a whole dressed room, because a primitive can be closed and an
    # assembly of them still leak.
    ropn, rnon = _K.boundary_edges(v, t)
    check("a dressed room has no open edges", not ropn,
          f"{len(ropn)} open edges over {len(t):,} triangles")
    # THE SECOND HALF OF THE RETURN VALUE WAS BEING THROWN AWAY. This line read
    # `ropn, _rn = ...` and asserted only the open count, so the number below
    # has never been looked at. It is 2,234 on a dressed office of 4,428
    # triangles -- and EVERY ONE OF THEM IS CROSS-OBJECT: measured span by
    # span, the sum of the per-object counts is exactly ZERO. So no builder in
    # this file is wrong; what is wrong is that objects are being placed
    # touching each other on coincident faces, which is an edge with four faces
    # on it and renders perfectly (the `portal_frame` defect, session 3x, 828 a
    # deck). It is pre-existing and it is not this session's to fix -- the fix
    # is in the PLACEMENT rules in `dress`, not in the machines.
    #
    # A RATCHET, NOT A ZERO, and deliberately so. Asserting zero would fail on
    # content that shipped four sessions ago and tell the next reader nothing;
    # asserting nothing at all is how it got to 2,234 unseen. Whoever drives it
    # to zero should delete this and assert `not rnon`.
    #
    # THE FIRST VERSION OF THIS BOUND WAS A RATE AND COULD NOT FAIL. Edges per
    # triangle looked like the scale-free choice and is nearly inert: emitting
    # every face of the room TWICE -- the worst coincident-face defect there is
    # -- moves it from 0.505 to 0.498, DOWN, because the denominator doubles
    # while `boundary_edges` counts each edge once. An absolute count on a
    # deterministic build is the statistic that moves, and the control below
    # shows the measurement resolving the exact defect it is for.
    check("a dressed room's coincident faces do not get worse",
          len(rnon) <= 2400,
          f"{len(rnon):,} non-manifold edges over {len(t):,} triangles")
    _fv, _ft, _fg = [], [], []
    _box(_fv, _ft, _fg, "a", (0, 0, 0), (1, 1, 1))
    _box(_fv, _ft, _fg, "b", (0, 1, 0), (1, 2, 1))          # FLUSH: shares a face
    _ov, _ot, _og = [], [], []
    _box(_ov, _ot, _og, "a", (0, 0, 0), (1, 1, 1))
    _box(_ov, _ot, _og, "b", (0, 0.99, 0), (1, 2, 1))       # OVERLAPPING
    check("the coincident-face measurement fires on flush and not on overlap",
          len(_K.boundary_edges(_fv, _ft)[1]) > 0
          and not _K.boundary_edges(_ov, _ot)[1],
          f"flush {len(_K.boundary_edges(_fv, _ft)[1])}, "
          f"overlap {len(_K.boundary_edges(_ov, _ot)[1])}")
    print(f"    cross-object non-manifold: {len(rnon):,} edges over "
          f"{len(t):,} triangles, 0 of them inside any one object -- "
          f"pre-existing, ungated until now")

    # Determinism, which is what `_u` is for.
    v2, t2, _g2, _c2 = dress("test", 6.0, 9.0, 2.9, "office")
    check("the same room dresses identically twice", v == v2 and t == t2)
    v3, _t3, _g3, _c3 = dress("other", 6.0, 9.0, 2.9, "office")
    check("a different room dresses differently", v != v3)

    # THE POINT OF THE EXERCISE. A room must come out denser than the 4.5
    # objects the whole station averaged before this module existed.
    s = stats("test", 6.0, 9.0, 2.9, "office")
    check("a dressed room holds far more than the old 4.5 objects",
          s["objects"] > 60, str(s))

    # Clutter must be ON surfaces, never floating and never in the deck.
    lows = [q[1] for q in v]
    check("nothing is below the deck", min(lows) > -1e-6, f"{min(lows):.3f}")
    check("nothing is above the soffit", max(lows) < 2.9, f"{max(lows):.3f}")

    # --- THE MACHINERY KIT, INV-130 ---------------------------------------
    # A gate belongs in the module that builds the thing, and it must build the
    # HARD case (CLAUDE.md, session 3x). Every one of the fifteen machines is
    # built at a real fixture's declared size and measured for the four
    # properties a render cannot see: closure, manifoldness, winding, and
    # staying inside the box it replaced. Two of these fired on real content
    # after passing on probe boxes -- an `over` crane at 0.70 m rather than the
    # probe's 0.90, and a cabinet 0.35 m deep rather than 1.10 -- so the sizes
    # below are taken FROM `rooms.FIXTURES` and `rooms.PROPS` rather than
    # chosen here.
    import rooms as _R                                          # noqa: PLC0415
    import materials as _M                                      # noqa: PLC0415

    small, big = declared_boxes()
    check("every machine kind has a real fixture or prop that uses it",
          set(small) == set(MACHINES),
          f"unused: {sorted(set(MACHINES) - set(small))}")

    def _probe(kind, box):
        mv, mt, mg = [], [], []
        n = machine(mv, mt, mg, kind, "fix_probe", box[:3], box[3:], "s")
        return mv, mt, mg, n

    part_names = set()
    # BOTH ENDS OF EVERY KIND'S DECLARED RANGE, and they are different hard
    # cases. The SMALLEST instance is the hard case for closure and for staying
    # inside the box -- two of these fired on real content after passing on
    # probe boxes, an `over` crane at 0.70 m rather than the probe's 0.90 and a
    # cabinet 0.35 m deep rather than 1.10. The LARGEST is the hard case for
    # everything the plate field exists for, because that is the only place a
    # field big enough to have a lattice in it appears at all: the 0.20 m
    # `lift_call` and the 3.20 m `monitor_wall` are the same builder, and the
    # non-manifold defects this session found live at opposite ends of it.
    for kind in sorted(MACHINES):
        for box, src, end in ((small[kind][0], small[kind][1], "smallest"),
                              (big[kind][0], big[kind][1], "largest")):
            mv, mt, mg, n = _probe(kind, box)
            part_names.update(nm for nm, _l, _h in mg if MACHINE_MARK in nm)
            opn, non = _K.boundary_edges(mv, mt)
            sv = 0.0
            for a, b, c in mt:
                p0, p1, p2 = mv[a], mv[b], mv[c]
                sv += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
                       - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0])
                       + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0]))
            tag = f"machine {kind} ({end}, {src})"
            check(f"{tag} is closed", not opn,
                  f"{len(opn)} open edges over {n} triangles")
            check(f"{tag} is manifold", not non,
                  f"{len(non)} non-manifold edges")
            check(f"{tag} encloses positive volume", sv / 6.0 > 0,
                  f"{sv / 6.0:.4f} m3")
            check(f"{tag} stays inside the box it replaced",
                  machine_bounds_ok(mv, mt, 0, box[:3], box[3:]) <= 1e-9,
                  f"{machine_bounds_ok(mv, mt, 0, box[:3], box[3:]):.4f} m out")
            check(f"{tag} is not a box", n > 40, f"{n} triangles")
    # ...and the negative control on the closure test, run rather than claimed.
    hv, ht, hg = [], [], []
    machine(hv, ht, hg, "vessel", "fix_probe", (-2, 0, -2), (2, 6.2, 2), "s")
    check("the closure test fires on a machine with a hole in it",
          len(_K.boundary_edges(hv, [q for i, q in enumerate(ht)
                                     if i % 37])[0]) > 0)

    # --- IS THE MACHINE AS BUILT AS THE WALL BEHIND IT --------------------
    # `density.py --machinery` asks this of every location and read 68/78; this
    # asks it of every BUILDER, at the top of its declared range, and it is the
    # gate that was missing. Ten of the twenty-two kinds were under their floor
    # there and every single one of them passed at the bottom, so a gate built
    # only on the smallest instance -- which is what this file had -- could not
    # see any of it. Same defect as `interior_kit`'s tag-coverage assertion
    # running on a corridor with no doors, one module along.
    #
    # THE FLOOR IS NOT WRITTEN DOWN HERE. It is the product gate's own floor,
    # computed live: real locations built through `rooms.build`, split by the
    # same `machinery_split` and measured by the same `analyse`. A captured
    # constant would be a second copy of a computed number and this one MOVES --
    # session 4e took the gate from 74/78 to 68/78 without touching a machine,
    # because the WALLS got better and the floor is the wall.
    import interior as _it                                      # noqa: PLC0415
    import density as _D                                        # noqa: PLC0415
    _schema, _prof = _it.load()
    _seen, _probes = set(), []
    for _p in _R.unbuilt(_schema, _prof):
        _a = _R.archetype(_p)
        if _a in ("office", "store", "industrial") and _a not in _seen:
            _seen.add(_a)
            _probes.append(_p)
    floor, floor_src = 0.0, ""
    for _p in _probes:
        _pv, _pt, _pg = _R.build(_schema, _prof, _p)
        _lam = _D.analyse(_pv, _D.machinery_split(_pv, _pt, _pg)[1],
                          min_facet_m=0.0)["lam"]
        if _lam > floor:
            floor, floor_src = _lam, _p["key"]
    check("a shell floor was measured off real rooms", floor > 0.0,
          f"{len(_probes)} probes")

    def _lam_of(kind, box):
        mv, mt, _mg, _n = _probe(kind, box)
        return _D.analyse(mv, mt, min_facet_m=0.0)["lam"]

    for kind in sorted(MACHINES):
        box, src = big[kind]
        check(f"machine {kind} ({src}) is as articulated as the wall behind it",
              _lam_of(kind, box) >= floor,
              f"{_lam_of(kind, box):.3f} against {floor:.3f} "
              f"({floor_src})")
    print(f"    machinery floor {floor:.3f} /m, off {floor_src}'s own shell")

    # THE NEGATIVE CONTROL, and it is run rather than described. `_FLAT` rebuilds
    # the geometry this gate was written against -- discs instead of rings, no
    # plate field, no bezel, one-plate shelves -- exactly as `articulate`'s
    # `plates=False` does for `density.py --shell`. An articulation gate that
    # cannot fail is the defect this whole layer exists because of.
    global _FLAT
    _FLAT = True
    try:
        flat_bad = [k for k in sorted(MACHINES)
                    if _lam_of(k, big[k][0]) < floor]
    finally:
        _FLAT = False
    check("the articulation gate FAILS on the unarticulated machines",
          len(flat_bad) >= 8,
          f"only {len(flat_bad)} of {len(MACHINES)} fall below the floor")
    print(f"    negative control: {len(flat_bad)}/{len(MACHINES)} kinds fall "
          f"below {floor:.3f} with the plate field and the rings off "
          f"({', '.join(flat_bad[:6])}...)")

    # EVERY PART NAME MUST RESOLVE TO A MATERIAL, and to ONE material. The
    # bound fragment names the material and `materials.resolve` matches it as a
    # substring with longest-wins, so a part name that happened to contain two
    # unrelated fragments would take whichever is longer -- a decision made by
    # spelling rather than by anyone's intent. `test_materials_layer3.py`
    # checks this for the groups `rooms.py` emits; it is here as well because
    # this is the module that invents the names.
    # AGAINST REAL OBJECT NAMES, not the two prefixes. Parts are named after
    # the object they belong to now, so the string a material is resolved from
    # contains that object's name -- and `materials.resolve` takes the LONGEST
    # matching fragment. A long object name is exactly how the part's own
    # fragment would lose, so the check has to see the names the station
    # actually emits rather than `fix_`/`prop_`.
    for pre in ("fix_", "prop_", "dress_"):
        part_names.update(_Parts(pre).all())
    unres = sorted(g_ for g_ in part_names
                   if _M.resolve_any(g_, "interior") is None)
    check("every machine part name resolves to an interior material",
          not unres, str(unres))
    # THE INVARIANT IS THAT THE PART'S OWN FRAGMENT WINS, not that nothing
    # else matches. This asked for the second, which was the same question
    # while a part was called `prop_mp_plant_frame` and stopped being one when
    # parts took their object's name: `dress_cargo_crane_mp_dress_screen`
    # legitimately contains `crane` as well as `dress_screen`, and
    # `materials.resolve` takes the LONGEST match, so the screen still resolves
    # to a screen. An incidental substring is now unavoidable and harmless; a
    # part resolving to its OBJECT'S material is neither.
    ambiguous = []
    for g_ in sorted(part_names):
        hits = set()
        for m in _M.MATERIALS:
            if "interior" not in m.scenes:
                continue
            for f in m.binds:
                if f in g_:
                    hits.add(f)
        if not hits:
            continue
        mine = g_.split(MACHINE_MARK, 1)[1] if MACHINE_MARK in g_ else g_
        won = max(hits, key=len)
        if won not in mine and mine not in won:
            ambiguous.append((g_, f"resolves on {won!r}", f"not {mine!r}"))
    check("every machine part resolves on its OWN fragment",
          not ambiguous, str(ambiguous[:3]))

    # Surfaces are read back off geometry, so a builder with no top gets none.
    # A 0.4 m bin lid is 0.13 m2 and is CORRECTLY below SURFACE_MIN_M2 -- you
    # do not leave your mug on a bin. The read is tested on something that
    # should carry things, and on something that should not, so the threshold
    # is exercised in both directions rather than asserted in one.
    vv, tt, gg = [], [], []
    _table(vv, tt, gg, 0, 0, 0, 1.4, 0.8, 0.74, "s")
    check("a surface read finds a table top",
          len(_surfaces_of(vv, tt, gg, 0)) >= 1,
          f"{len(_surfaces_of(vv, tt, gg, 0))} surfaces")
    vv, tt, gg = [], [], []
    _bin(vv, tt, gg, 0, 0, 0, 0.4, 0.4, 0.7, "s")
    check("...and does not put clutter on a bin lid",
          len(_surfaces_of(vv, tt, gg, 0)) == 0)

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
