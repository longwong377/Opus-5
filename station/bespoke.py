#!/usr/bin/env python3
"""Which module builds which place, and the frame it builds it in.

MOVED HERE FROM `tools/export_scene.py`, UNCHANGED, so that two things can use
one registry instead of two drifting copies. `export_scene` needed it to render
a room; `station/deck.py` needs it to ASSEMBLE one, and until session 3y did
not have it -- `build_deck` called `rooms.build` unconditionally and never
consulted `place["module"]`, so 39 of the 106 ring-deck places were module-owned
and assembled as generic bays anyway. The docking bay a player walked into was
a generic store bay standing in for `docking_bay.py`'s 18 m and 39 measured
floods, and every craft score ever taken on an assembled deck scored the
generic bay.

`station/` may not import from `tools/` -- the tools are consumers of the
station, not the other way round -- so the registry had to come down here for
the assembler to reach it. `export_scene` now imports these names from this
module and its own behaviour is byte-identical.

WHAT THE MEASUREMENT SAID, because the first answer was wrong. Comparing each
bespoke module's extent against `rooms.bay_span_m` says NOT ONE of the 25 fits:
`plant` is 92 x 442 m against a 13.5 x 9.6 bay, `docking_bay` 42 x 141 against
11.6 x 7.8. That comparison is meaningless. `bay_span_m` is a `rooms.py` SIZING
HELPER -- it decides how big a representative generic bay should be -- and not
a constraint the ring imposes. The ring's own constraint is the arc between
consecutive doors, and on `blue/0/0` those gaps are 480 m, 185 m, 295 m, 148 m,
74 m and 148 m against a widest bespoke width of 42 m. **Zero collisions.**
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# The entry points are NOT uniform and were established by reading each
# module's own _selftest, which is its canonical usage. They are recorded here
# so nobody has to rediscover them a third time -- test_materials_layer3 had
# already found them once for the coverage gate. Each takes (schema, profile,
# place) and returns whatever its module returns; `to_spans` normalises.
#
# `signage` is absent deliberately: it builds a sign board, which is a prop
# that stands in other rooms rather than a room you can stand in.
BESPOKE_GEOMETRY = {
    "alien_sector": lambda s, p, q: __import__("alien_sector").gallery(s, p),
    "command_control":
        lambda s, p, q: __import__("command_control").command_control(),
    "council_chamber":
        lambda s, p, q: __import__("council_chamber").council_chamber(),
    "customs": lambda s, p, q: __import__("customs").hall(s, p),
    "docking_bay": lambda s, p, q: __import__("docking_bay").docking_bay(
        0, s, p),
    "hospitality": lambda s, p, q: __import__("hospitality").room(),
    # The bay a place lands in is the first one; plant.bays() partitions the
    # deck by arc and every bay is the same construction.
    "plant": lambda s, p, q: __import__("plant").plant_bay(
        s, p, __import__("plant").bays(s, p)[0], 10.0),
    # THE CLASS COMES FROM THE PLACE. A lurker's berth and a command cabin are
    # different geometry, and rendering one class seven times would be seven
    # frames of one room. See QUARTERS_CLASS.
    "quarters": lambda s, p, q: __import__("quarters").run(
        s, p, __import__("quarters").class_by_key(QUARTERS_CLASS[q["key"]])),
    "zocalo": lambda s, p, q: __import__("zocalo").zocalo_run(
        3, cap_ends=True),
}


# Directory key -> quarters class key. Four of the seven differ, and they
# differ for a reason rather than by accident: the directory names a PLACE ON
# THE STATION and quarters.py names a HOUSING CLASS, and the ambassadorial
# suites and the League delegations are two places drawing on one class. A
# `key.removeprefix("qtr_")` would have produced three KeyErrors and no hint
# that the two vocabularies are different things.
#
# Asserted against both vocabularies in the self-test, so a new place or a
# renamed class fails here rather than rendering the wrong room.
QUARTERS_CLASS = {
    "qtr_command": "command",
    "qtr_personnel": "personnel",
    "qtr_civilian": "civilian",
    "qtr_transient": "transient",
    "ambassadorial_suites": "diplomatic",
    "league_delegations": "diplomatic",
    "alien_resident_qtr": "alien_resident",
}


# Modules that build in STATION coordinates rather than in a local Y-up frame,
# and therefore have to be unrolled before a person can be stood in them.
#
# Eight of the nine interior modules build a room the way you would model one:
# origin at the floor, +Y up, walk down +Z. `plant` does not, and it is right
# not to -- it builds an arc of the outer deck stack in place, at radius 447 to
# 471 m, because its whole subject is a bay that spans five decks of a spinning
# ring and it has to know where those decks are.
#
# The consequence for a RENDER is that "up" there is radially INWARD, toward
# the spin axis, and every other part of this shot -- the camera's up vector,
# `open_standpoint`'s eye height, a spot light's downward aim -- assumes +Y.
# The first plant frame is what showed it: the camera stood in a tangential
# direction and looked at two tanks side-on from outside them.
UNROLL = {"plant"}

# Group-name fragments whose triangles are THE SURFACE PEOPLE STAND ON, for
# modules where that is not the bottom of the model.
#
# `open_standpoint` finds candidate floors by histogramming near-horizontal
# triangle area, and in a plant bay that picks the tank-farm floor and the tank
# tops -- both far larger than the walkway. But plant.py's own docstring calls
# the catwalk "the walkable skeleton", and the module knows which group it is.
# Asking beats inferring, exactly as `light_` tagging beats guessing which
# material glows.
WALK_SURFACE = {"plant": ("plant_catwalk",)}


def unroll_to_local(verts):
    """Station coordinates -> a standing frame, by unrolling the cylinder.

    +X is along the arc, +Y is UP (which is radially inward, because down is
    outward under spin), +Z is along the station's axis. The mid-point of the
    geometry becomes the origin.

    Unrolling rather than projecting, because the arc is what a walker
    experiences: a plant bay spans about 20 degrees at 460 m, which is 160 m of
    catwalk and 8 m of sagitta. Flattening it makes the catwalk straight, which
    is what it feels like at 1.7 g, and costs nothing this shot can see.
    """
    import numpy as np

    a = np.asarray(verts, dtype=np.float64)
    r = np.hypot(a[:, 0], a[:, 1])
    ang = np.arctan2(a[:, 1], a[:, 0])
    # Unwrap about the mean angle so a bay straddling +/-pi does not tear.
    mid = np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())
    d = (ang - mid + math.pi) % (2 * math.pi) - math.pi
    r_ref = float(r.max())              # the floor: the largest radius is down
    x = d * r_ref
    y = r_ref - r
    z = a[:, 2] - a[:, 2].mean()
    return [(float(x[i]), float(y[i]), float(z[i])) for i in range(len(a))]




# ---------------------------------------------------------------------------
# What a swap would actually cost, measured
# ---------------------------------------------------------------------------
def compare(schema, profile, places=None):
    """(key, module, generic_tris, bespoke_tris, bespoke_extent) per place.

    THE MEASUREMENT THAT INVERTED THE FINDING, and it is worth keeping runnable
    rather than written down once. Session 3x recorded that `deck.py` assembles
    39 module-owned places as generic `rooms.py` bays and called it the largest
    fidelity gap on the station -- "the docking bay a player walks into is a
    generic store bay standing in for `docking_bay.py`". That is right about
    SHAPE and IDENTITY and wrong about RICHNESS, and the difference decides
    what to do about it:

        across the 25 ring-deck places that have a builder,
        generic 390,432 triangles against bespoke 210,702 -- **x0.54**

    The bespoke modules are SHELLS. `rooms.build` runs `dressing` and
    `populace` inside itself, so a generic bay arrives furnished and inhabited;
    `docking_bay.docking_bay` is 3,740 triangles of bay and nothing in it,
    against the generic 38,728. Swapping wholesale would take detail OFF the
    station -- 46% of it.

    It is not uniform, which is the useful part. Bespoke is RICHER for
    `alien_sector` (x3.69), `zocalo/shops_kiosks` (x1.45), `customs` (x0.94 to
    x1.41) and `plant/air_compressors` (x1.13), and much poorer for
    `docking_bay` (x0.10), `command_control` (x0.12), `council_chamber` (x0.12)
    and `hospitality` (x0.19).

    So the answer is neither "swap" nor "leave it": it is **bespoke shell plus
    generic dressing**. The module gives a place its true shape, scale and
    identity; `dressing.dress()` and `populace` fill it, and both already take
    a room's dimensions rather than a `rooms.build` internal, so the
    composition is available. That is the next increment and it is a real one.

    Two other facts this function establishes and a reader should not have to
    rediscover:

    * **The frames differ.** `rooms.build` centres a room on its origin (x
      +/-5.96, z +/-4.06 for `docking_bays`) with the floor at y = -0.14.
      `docking_bay.docking_bay` puts its floor at y = 0 and runs z from -0.75
      to +140.75. Anything that places bespoke geometry on a ring has to
      recentre it first, or the room lands 70 m up the station's axis.
    * **The ring has room.** Comparing a bespoke extent against
      `rooms.bay_span_m` says not one of the 25 fits -- but `bay_span_m` sizes
      a representative GENERIC bay and is not a constraint the ring imposes.
      The real constraint is the arc between consecutive doors, and on
      `blue/0/0` those are 480, 185, 295, 148, 74 and 148 m against a widest
      bespoke width of 42 m. Zero collisions.
    """
    import directory as _dr                                    # noqa: PLC0415
    import rooms as _R                                         # noqa: PLC0415
    out = []
    for q in (places if places is not None else _dr.PLACES):
        mod = q.get("module")
        if mod not in BESPOKE_GEOMETRY:
            continue
        try:
            gt = len(_R.build(schema, profile, q)[1])
        except Exception:                                      # noqa: BLE001
            gt = None
        try:
            r = BESPOKE_GEOMETRY[mod](schema, profile, q)
            v = unroll_to_local(r[0]) if mod in UNROLL else r[0]
            bt = len(r[1])
            ext = (max(p[0] for p in v) - min(p[0] for p in v),
                   max(p[2] for p in v) - min(p[2] for p in v))
        except Exception:                                      # noqa: BLE001
            bt, ext = None, None
        out.append((q["key"], mod, gt, bt, ext))
    return out


def _selftest():
    import interior as _it                                     # noqa: PLC0415
    import directory as _dr                                    # noqa: PLC0415
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    schema, profile = _it.load()

    # EVERY ENTRY MUST BUILD. A registry whose lambdas have gone stale is worse
    # than no registry: `export_scene` would report a room it cannot render and
    # `deck` would silently keep the generic bay for a reason that is a bug.
    broken = []
    for mod in sorted(BESPOKE_GEOMETRY):
        q = next((p for p in _dr.PLACES if p.get("module") == mod), None)
        if q is None:
            broken.append((mod, "no place claims this module"))
            continue
        try:
            r = BESPOKE_GEOMETRY[mod](schema, profile, q)
            if not r[1]:
                broken.append((mod, "built no triangles"))
        except Exception as e:                                 # noqa: BLE001
            broken.append((mod, str(e)[:50]))
    check("every builder in the registry still builds", not broken, str(broken))

    # The registry may not claim a module no place owns, and every module that
    # owns a place and can be assembled should be in it. Both directions,
    # because each failure is silent in a different way.
    owning = {p.get("module") for p in _dr.PLACES} - {None}
    check("the registry claims no module nothing owns",
          set(BESPOKE_GEOMETRY) <= owning,
          str(sorted(set(BESPOKE_GEOMETRY) - owning)))

    # UNROLL and WALK_SURFACE may only name modules the registry has.
    check("UNROLL names only registered modules", UNROLL <= set(BESPOKE_GEOMETRY),
          str(UNROLL - set(BESPOKE_GEOMETRY)))
    check("WALK_SURFACE names only registered modules",
          set(WALK_SURFACE) <= set(BESPOKE_GEOMETRY),
          str(set(WALK_SURFACE) - set(BESPOKE_GEOMETRY)))

    # QUARTERS_CLASS covers exactly the places quarters owns.
    qp = {p["key"] for p in _dr.PLACES if p.get("module") == "quarters"}
    check("QUARTERS_CLASS covers exactly the quarters places",
          set(QUARTERS_CLASS) == qp,
          f"missing {sorted(qp - set(QUARTERS_CLASS))}, "
          f"stale {sorted(set(QUARTERS_CLASS) - qp)}")

    # `unroll_to_local` must actually flatten an arc: a plant bay is authored
    # at radius ~460 and must come back with its floor near y = 0.
    r = BESPOKE_GEOMETRY["plant"](schema, profile,
                                  next(p for p in _dr.PLACES
                                       if p.get("module") == "plant"))
    flat = unroll_to_local(r[0])
    ys = [p[1] for p in flat]
    check("unroll_to_local puts the floor at y = 0", abs(min(ys)) < 1e-6,
          f"floor at y={min(ys):.3f}")
    check("...and does not collapse the arc",
          max(p[0] for p in flat) - min(p[0] for p in flat) > 10.0)

    # THE COMPARISON IS THE POINT, and its headline is asserted so a change in
    # either direction is noticed rather than discovered later.
    rows = compare(schema, profile)
    g = sum(r[2] for r in rows if r[2] and r[3])
    b = sum(r[3] for r in rows if r[2] and r[3])
    check("every module-owned place can be measured both ways",
          all(r[2] and r[3] for r in rows), str([r[0] for r in rows if not r[3]]))
    check("the bespoke modules are still SHELLS, not richer rooms", b < g,
          f"bespoke {b:,} against generic {g:,}")
    print(f"  {len(BESPOKE_GEOMETRY)} builders over {len(rows)} places; "
          f"generic {g:,} tri, bespoke {b:,} tri (x{b / g:.2f})")
    richer = [r[0] for r in rows if r[2] and r[3] and r[3] > r[2]]
    print(f"  bespoke is RICHER for {len(richer)}: {', '.join(sorted(richer))}")

    # --- the frame adapter ------------------------------------------------
    import deck as _D                                          # noqa: PLC0415

    # Every builder is either DECLARED or explicitly UNKNOWN. A module in
    # neither would raise at assembly time with no explanation, which is the
    # one outcome worse than refusing.
    check("every builder's near end is declared or explicitly unknown",
          set(NEAR_END) | set(NEAR_END_UNKNOWN) == set(BESPOKE_GEOMETRY),
          f"unaccounted {sorted(set(BESPOKE_GEOMETRY) - set(NEAR_END) - set(NEAR_END_UNKNOWN))}")
    check("...and none is in both", not (set(NEAR_END) & set(NEAR_END_UNKNOWN)))
    check("every declared near end cites the module's own words",
          all(len(w) > 30 for _e, w in NEAR_END.values()))

    def signed_volume(vv, tt):
        cx = [sum(q[i] for q in vv) / len(vv) for i in range(3)]
        tot = 0.0
        for tri in tt:
            a, b_, c = [[vv[i][k] - cx[k] for k in range(3)] for i in tri]
            tot += (a[0] * (b_[1] * c[2] - b_[2] * c[1])
                    - a[1] * (b_[0] * c[2] - b_[2] * c[0])
                    + a[2] * (b_[0] * c[1] - b_[1] * c[0])) / 6.0
        return tot

    placed = 0
    for q in _dr.PLACES:
        mod = q.get("module")
        if mod not in NEAR_END:
            continue
        ah = _D.room_axial_half_m(schema, profile, q)
        v, t, _g = room_shell(schema, profile, q, ah)
        xs = [p[0] for p in v]
        ys = [p[1] for p in v]
        zs = [p[2] for p in v]
        placed += 1
        check(f"{q['key']}: near face lands on the assembler's plane",
              abs(max(zs) - ah) < 1e-6, f"{max(zs):.4f} against {ah:.4f}")
        check(f"{q['key']}: the room extends AWAY from the corridor",
              min(zs) < ah - 1e-6, f"z runs {min(zs):.2f}..{max(zs):.2f}")
        # THE MEASURED FLOOR at y = 0, not the bounding box. The first version
        # of this asserted `min(ys) == 0` and passed trivially, because the
        # adapter was forcing exactly that -- an assertion checking its own
        # input. It also hid a real defect: `command_control`'s walkable
        # surface sits 1.90 m above its lowest vertex, so a player placed by
        # the bounding box spawns under the deck.
        check(f"{q['key']}: the walkable floor is at y = 0",
              abs(floor_y(v, t, _g, mod)) < 1e-6,
              f"floor band at {floor_y(v, t, _g, mod):.3f}, "
              f"bbox bottom {min(ys):.3f}")
        check(f"{q['key']}: nothing floats above the shell's own ceiling",
              max(ys) > 2.0, f"{max(ys):.2f} m tall")
        check(f"{q['key']}: centred across the corridor",
              abs(min(xs) + max(xs)) < 1e-6, f"{min(xs):.3f}..{max(xs):.3f}")
        # THE FLIP MUST NOT INVERT THE ROOM. `min_z` modules are turned by a
        # half turn about the vertical AND have their winding reversed to
        # match; get either half wrong and the room renders inside-out, which
        # a triangle count, an extent and a render against black all miss.
        raw = BESPOKE_GEOMETRY[mod](schema, profile, q)
        rv = unroll_to_local(raw[0]) if mod in UNROLL else raw[0]
        before, after = signed_volume(rv, raw[1]), signed_volume(v, t)
        check(f"{q['key']}: recentring does not turn the room inside-out",
              (before > 0) == (after > 0) or abs(before) < 1e-9,
              f"signed volume {before:.1f} -> {after:.1f}")

    # AND AN UNDECLARED MODULE MUST REFUSE. The failure mode this prevents is
    # silent: a room placed the wrong way round has the same triangle count,
    # the same extent and the same materials as one placed correctly.
    refused = 0
    for mod in NEAR_END_UNKNOWN:
        q = next((p for p in _dr.PLACES if p.get("module") == mod), None)
        if q is None:
            continue
        try:
            room_shell(schema, profile, q, 4.0)
        except KeyError:
            refused += 1
    check("an undeclared module refuses rather than guessing",
          refused == len([m for m in NEAR_END_UNKNOWN
                          if any(p.get("module") == m for p in _dr.PLACES)]),
          f"{refused} refused")
    print(f"  frame adapter: {placed} places recentred, "
          f"{len(NEAR_END)} modules declared, {len(NEAR_END_UNKNOWN)} refused")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0



# ---------------------------------------------------------------------------
# Putting a bespoke room where a generic one goes
# ---------------------------------------------------------------------------
# WHICH END OF A BESPOKE ROOM MEETS THE CORRIDOR. There is no way to infer
# this: `docking_bay` and `command_control` are built the same way round in
# their own frames and want OPPOSITE ends against a corridor, because one's
# +Z runs in from a vacuum mouth and the other's runs out toward a window.
# Guessing would place a room backwards, which changes no triangle count, no
# extent, no gate -- and is the first thing a player would notice.
#
# So each entry is DECLARED, with the module's own words as the source. A
# module that is not here raises rather than defaulting: `rooms.build`'s
# convention (near face at +z) is a fine default for a room somebody authored
# knowing about it, and none of these were.
NEAR_END = {
    # "Frame: +Z runs INTO the bay from the mouth at z = 0" -- the mouth is the
    # vacuum end, so the crew end a corridor reaches is the far one.
    "docking_bay": ("max_z", "docking_bay.docking_bay: '+Z runs INTO the bay "
                             "from the mouth at z = 0'"),
    # "+X across, +Y up, +Z forward toward the window; deck at y = 0" -- the
    # window is the far wall, so the way in is the near one. OPPOSITE of the
    # bay, from an identically-worded frame.
    "command_control": ("min_z", "command_control: '+Z forward toward the "
                                 "window; deck at y = 0'"),
    # "z runs ALONG it -- from the gate line at z=0 to the board wall at
    # z=HALL_LEN_M". You arrive at the gate line.
    "customs": ("min_z", "customs.hall: 'from the gate line at z=0 to the "
                         "board wall at z=HALL_LEN_M'"),
    # "The whole bar, authored with x across, y up, z along", and it measures
    # symmetric about the origin (z -5.91..+5.91), so either end serves and the
    # generic convention applies unchanged.
    "hospitality": ("max_z", "hospitality.room: authored symmetric about the "
                             "origin, z -5.91..+5.91"),
    # "Bench centred on the origin, delegates outboard of it" -- symmetric.
    "council_chamber": ("max_z", "council_chamber: 'Bench centred on the "
                                 "origin'"),
}

# The four that are NOT declared, and why each is genuinely undecidable from
# what the module says about itself. Recorded so the next reader does not
# repeat the search rather than as an apology.
NEAR_END_UNKNOWN = {
    "quarters": "quarters.run builds 'a row of units opening off one side of "
                "a corridor' -- it contains its OWN corridor, so which face "
                "meets the ring's corridor is a layout decision nobody has "
                "made, not a fact about the module.",
    "zocalo": "zocalo_run builds 'bays end to end along +z' and its docstring "
              "says the concourse CONTINUES -- both ends are open by design, "
              "so neither is the near one until a layout says so.",
    "alien_sector": "alien_sector.gallery documents no frame at all.",
    "plant": "plant builds in STATION coordinates at radius 447-471 and is "
             "unrolled for rendering; its walkable surface is a catwalk "
             "(WALK_SURFACE), not a floor, and a corridor joining it is a "
             "different connection from a door in a wall.",
}


# WHAT THE NINE MODULES LOOK LIKE AS SURFACES, audited when the adapter's
# winding gate was written. Recorded because it is the first time anything has
# asked, and because the obvious reading of it is wrong:
#
#     module            signed vol   open edges   non-manifold   triangles
#     alien_sector           368.8            0            118      11,680
#     command_control       -202.1          342             44       1,334
#     council_chamber       -243.0        1,592              0       1,916
#     customs                513.0           48             54       7,296
#     docking_bay        -67,236.4          151             34       3,740
#     hospitality             39.2          824             58       4,796
#     plant               47,233.5          192              0       8,452
#     quarters               136.3            0             71       2,088
#     zocalo              -1,246.8          734             32      44,320
#
# Four are negative and it is TEMPTING to call them inside-out. Do not: signed
# volume is only decisive for a CLOSED surface, and only two of the nine are
# closed (`alien_sector` and `quarters`, both positive). For the other seven
# the statistic is measuring their openings as much as their winding. What can
# be said is narrower and still useful: **seven of nine bespoke modules are
# open surfaces**, up to 1,592 edges on `council_chamber`, and nothing has ever
# gated that -- the closure work in session 3x reached `interior_kit`,
# `dressing` and the assembler, and stopped at the bespoke modules' door.
#
# `room_shell` therefore asserts only that recentring PRESERVES whatever
# orientation a module had, which is the question it is entitled to ask.


def floor_y(verts, tris, groups=None, module=None):
    """The height a person actually stands at, measured off the geometry.

    NOT THE BOTTOM OF THE MODEL, and the difference is not small. `room_shell`
    first aligned each shell's minimum y to zero, which is right for
    `docking_bay` (floor band at 0.00, 5,886 m2) and wrong for
    `command_control`, whose dominant up-facing surface sits **1.90 m** above
    its lowest vertex -- a player placed by the bounding box would spawn under
    the deck. `customs` is out by 0.20 and `hospitality` by 0.14, both being
    the thickness of a deck slab the module models and `rooms.build` does not.

    Found the same way `export_scene.open_standpoint` finds it: histogram
    near-horizontal, UP-FACING triangle area by height and take the band with
    the most of it. Area rather than count, because a floor is a few large
    triangles and a stair is many small ones.

    `WALK_SURFACE` overrides where a module has already said which group is its
    walkable skeleton -- `plant`'s catwalk is 8 m of steel over a tank farm
    whose floor is far larger, so the biggest band there is the wrong answer
    and the module knows it. Asking beats inferring, the same rule `light_`
    tagging follows.
    """
    import collections                                          # noqa: PLC0415
    want = WALK_SURFACE.get(module or "")
    keep = None
    if want and groups:
        keep = set()
        for name, lo, hi in _spans(groups, len(tris)):
            if any(f in name for f in want):
                keep.update(range(lo, hi))
    by = collections.Counter()
    for i, (a, b, c) in enumerate(tris):
        if keep is not None and i not in keep:
            continue
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = [p1[k] - p0[k] for k in range(3)]
        w = [p2[k] - p0[k] for k in range(3)]
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        ln = math.sqrt(sum(x * x for x in n))
        if ln < 1e-12 or n[1] / ln < 0.85:
            continue
        by[round((p0[1] + p1[1] + p2[1]) / 3.0, 2)] += ln / 2.0
    if not by:
        return min(p[1] for p in verts)
    return by.most_common(1)[0][0]


def _spans(groups, n):
    """Normalise a module's groups to (name, lo, hi), whichever shape it used."""
    if not groups:
        return []
    if isinstance(groups[0], (tuple, list)) and len(groups[0]) == 3 \
            and isinstance(groups[0][1], int):
        return list(groups)
    out, i = [], 0
    while i < len(groups):
        j = i
        while j < len(groups) and groups[j] == groups[i]:
            j += 1
        out.append((groups[i], i, j))
        i = j
    return out


def room_shell(schema, profile, place, axial_half_m):
    """Bespoke geometry recentred into `rooms.build`'s frame.

    `rooms.build` emits a room CENTRED on its origin with the walkable floor at
    y = 0 (its deck slab reaching to -0.14) and the face that meets the
    corridor at +z. A bespoke module emits whatever frame suited authoring it,
    and the three differ in every axis: `docking_bay` runs z from -0.75 to
    +140.75 with its floor at y = 0, `command_control` from -4.20 to +8.70 with
    its floor at y = -1.90, `zocalo` from -1.89 to +32.54.

    Placing one without this adapter puts the room up to **70 m along the
    station's axis** from the door meant to serve it.

    Returns (verts, tris, groups) in the assembler's frame, or raises for a
    module whose near end is not declared -- see `NEAR_END_UNKNOWN`. Raising is
    the point: a room placed the wrong way round changes no triangle count and
    no extent, so nothing downstream can catch it.
    """
    mod = place.get("module")
    if mod not in BESPOKE_GEOMETRY:
        raise KeyError(f"{place['key']}: no builder for module {mod!r}")
    if mod not in NEAR_END:
        raise KeyError(
            f"{place['key']}: {mod} has no declared near end. "
            f"{NEAR_END_UNKNOWN.get(mod, 'undeclared')}")
    r = BESPOKE_GEOMETRY[mod](schema, profile, place)
    v, t = r[0], r[1]
    if mod in UNROLL:
        v = unroll_to_local(v)
    g = r[2] if len(r) > 2 else None

    end, _why = NEAR_END[mod]
    xs = [p[0] for p in v]
    ys = [p[1] for p in v]
    zs = [p[2] for p in v]
    # x on the room's own centreline, floor to y = 0, and the near face onto
    # the plane the assembler expects. Flipped when the module's near end is
    # its MINIMUM z, by a half turn about the vertical -- (x, y, z) ->
    # (-x, y, -z) -- which is a rotation and so preserves winding. Mirroring in
    # z alone would face it the right way with every triangle inside-out, the
    # defect `dressing._cyl` shipped for sessions because neither a render nor
    # a triangle count can see it.
    cx = (min(xs) + max(xs)) / 2.0
    # THE MEASURED FLOOR, not the bottom of the bounding box. See `floor_y`.
    y0 = floor_y(v, t, g, mod)
    if end == "max_z":
        out = [(x - cx, y - y0, z - max(zs) + axial_half_m) for x, y, z in v]
    else:
        # (x, y, z) -> (-x, y, -z) is diag(-1, 1, -1), whose determinant is
        # +1. IT IS A ROTATION AND THE WINDING MUST NOT BE TOUCHED. The first
        # version reversed the triangles as well, on the reflex that turning
        # geometry round needs it, and that inverted every customs hall --
        # signed volume +513 to -513. The gate caught it; nothing else would
        # have, because an inside-out room has the same triangle count, the
        # same extent and, against black, the same render.
        out = [(-(x - cx), y - y0, -(z - min(zs)) + axial_half_m)
               for x, y, z in v]
    return out, t, g

if __name__ == "__main__":
    raise SystemExit(_selftest())
