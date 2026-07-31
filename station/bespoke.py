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
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
