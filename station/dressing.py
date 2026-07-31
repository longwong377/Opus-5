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
    g.append((name, t0, len(t)))


def _cyl(v, t, g, name, cx, cz, y0, y1, r, seg=6):
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg
        dx, dz = r * math.cos(a), r * math.sin(a)
        v.append((cx + dx, y0, cz + dz))
        v.append((cx + dx, y1, cz + dz))
    t0 = len(t)
    for k in range(seg):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % seg)
        t += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    c = len(v)
    v.append((cx, y1, cz))
    for k in range(seg):
        t.append((c, n0 + 2 * k + 1, n0 + 2 * ((k + 1) % seg) + 1))
    g.append((name, t0, len(t)))


# --- the kit ---------------------------------------------------------------
# Each builder takes (v, t, g, x, y, z, w, d, h, seed) and puts one object with
# its base at y, centred on (x, z). Dimensions are the archetype's, so a builder
# can be swapped for another of the same footprint without moving anything.

def _crate(v, t, g, x, y, z, w, d, h, seed):
    """A shipping case: body, proud lid, and corner irons."""
    _box(v, t, g, "dress_crate", (x - w / 2, y, z - d / 2),
         (x + w / 2, y + h * 0.88, z + d / 2))
    _box(v, t, g, "dress_crate_lid",
         (x - w / 2 - 0.02, y + h * 0.88, z - d / 2 - 0.02),
         (x + w / 2 + 0.02, y + h, z + d / 2 + 0.02))
    for sx in (-1, 1):
        for sz in (-1, 1):
            _box(v, t, g, "dress_metal",
                 (x + sx * w / 2 - 0.05, y, z + sz * d / 2 - 0.05),
                 (x + sx * w / 2 + 0.05, y + h * 0.88, z + sz * d / 2 + 0.05))


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
    """Top, apron and legs."""
    _box(v, t, g, "dress_top", (x - w / 2, y + h - 0.05, z - d / 2),
         (x + w / 2, y + h, z + d / 2))
    _box(v, t, g, "dress_metal", (x - w / 2 + 0.06, y + h - 0.14, z - d / 2 + 0.06),
         (x + w / 2 - 0.06, y + h - 0.05, z + d / 2 - 0.06))
    for sx in (-1, 1):
        for sz in (-1, 1):
            _box(v, t, g, "dress_metal",
                 (x + sx * (w / 2 - 0.09), y, z + sz * (d / 2 - 0.09)),
                 (x + sx * (w / 2 - 0.09) + 0.05, y + h - 0.14,
                  z + sz * (d / 2 - 0.09) + 0.05))


def _locker(v, t, g, x, y, z, w, d, h, seed):
    """A cabinet with expressed doors and handles."""
    _box(v, t, g, "dress_top", (x - w / 2, y, z - d / 2),
         (x + w / 2, y + h, z + d / 2))
    n = max(1, int(w / 0.45))
    for i in range(n):
        dx = -w / 2 + w * (i + 0.5) / n
        _box(v, t, g, "dress_door",
             (dx - w / (2 * n) + 0.02, y + 0.05, z + d / 2),
             (dx + w / (2 * n) - 0.02, y + h - 0.05, z + d / 2 + 0.02))
        _box(v, t, g, "dress_metal",
             (dx + w / (2 * n) - 0.10, y + h * 0.5, z + d / 2 + 0.02),
             (dx + w / (2 * n) - 0.05, y + h * 0.62, z + d / 2 + 0.05))


def _console(v, t, g, x, y, z, w, d, h, seed):
    """A pedestal with a raked screen and a lit face."""
    _box(v, t, g, "dress_top", (x - w / 2, y, z - d / 2),
         (x + w / 2, y + h * 0.78, z + d / 2))
    _box(v, t, g, "dress_screen", (x - w / 2 + 0.05, y + h * 0.78, z - d / 4),
         (x + w / 2 - 0.05, y + h, z + d / 4))


def _shelf(v, t, g, x, y, z, w, d, h, seed):
    """Uprights and shelves -- a surface machine, four tops for six boxes."""
    for sx in (-1, 1):
        _box(v, t, g, "dress_metal", (x + sx * w / 2 - 0.04, y, z - d / 2),
             (x + sx * w / 2, y + h, z + d / 2))
    n = max(2, int(h / 0.45))
    for i in range(1, n + 1):
        yy = y + h * i / n
        _box(v, t, g, "dress_top", (x - w / 2, yy - 0.03, z - d / 2),
             (x + w / 2, yy, z + d / 2))


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


def _surfaces_of(v, t, g, mark):
    """Upward-facing faces added since `mark`, as (y, x0, x1, z0, z1, area).

    Read back off the geometry rather than tracked alongside it: a builder that
    grows a new shelf gets clutter on it automatically, and a builder that loses
    one stops getting clutter, with nothing to keep in step. Two lists that must
    agree is the defect this project keeps finding in new costumes.
    """
    out = []
    for name, lo, hi in g:
        if lo < mark:
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
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in g) == len(t))

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
