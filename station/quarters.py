"""Residential quarters, by class -- and the class gradient IS gravity.

The most-repeated interior on the station. 250,000 people live somewhere, and
until now `npc/crowd.py` had nowhere to send any of them home to.

`docs/gazetteer/LOCATIONS.md` §11 sorts residence into seven classes and states
the design spine in one line:

    "The class gradient is the point. **Gravity does the work for free**:
     command quarters in Blue, Downbelow in Grey or the drum sub-floor. The
     people with the least power live where they weigh the most."

That is not decoration. It is a **checkable property of the station's geometry**,
and this module asserts it rather than restating it in prose.

**Be precise about what is true, though.** Rank and gravity are NOT monotonic
across every adjacent pair -- Green's 1.000 g sits above Red's 0.963 g while
ranking higher -- and claiming they were would be a docstring lying about its
own code, which is a failure class this project has already shipped once (a
comment reading "wound inward" over code winding outward). What holds, and what
is asserted, is the claim the gazetteer actually makes:

  * the LOWEST class lives at the HIGHEST gravity (lurkers, 1.693 g);
  * the highest class does not;
  * the spread is felt rather than marginal -- **2.23x body weight** between
    the top and the bottom of the housing ladder.

Rank orders floor area **within a sector**, which is what a housing allocation
would actually produce, and that is asserted per sector.

THE SEVEN CLASSES, AND WHERE THEY COME FROM
-------------------------------------------
Sectors are sourced; areas and fittings are not, and the difference is marked
per row in `CLASSES`.

| class            | sector | authority for the placement                       |
|------------------|--------|---------------------------------------------------|
| command          | Blue   | 4 -- fandom Blue Sector                            |
| personnel        | Blue   | **3** -- "Dock Workers' Quarters" in the Blue rosette |
| diplomatic       | Green  | 3 (Security Manual callout) + 4 ("Green 2")        |
| alien_resident   | Green  | 4                                                  |
| civilian         | Red    | 4                                                  |
| transient        | Red    | 4 -- "the layer between a hotel and Downbelow"     |
| lurker           | Grey   | 3 (the Brown rosette's outer band) + 4             |

**`lurker` has no unit geometry and that is deliberate.** The gazetteer is
explicit that Downbelow is "corridors and chambers, **not rooms**", and
`plant.py` already builds that architecture -- the plant zone at 1.26-1.69 g is
where `interior.py` tags decks `plant`, meaning *unassigned*, which is exactly
what a lurker is: someone with no billet. So the class exists in the table, is
ranked lowest, participates in the gravity assertion, and emits no room. A
class that emits nothing is still a class; pretending Downbelow is a room would
be worse than leaving it out.

ONE CANON FIGURE HAS GONE STALE, AND IT IS RECORDED RATHER THAN COPIED
----------------------------------------------------------------------
§11 quotes **"command quarters in Blue at 0.603 g"**. That figure predates
INV-026: when `HULL_ALLOWANCE` was a fraction, Blue's outermost floor sat at
167.7 m. With the metric hull skin it sits at **211.6 m and 0.760 g**. This
module reads gravity live from `interior.py` and never restates it, so the
gradient stays true while the numbers move. The gazetteer's figure should be
refreshed; it is flagged here rather than silently contradicted.

WHAT IS EXTRAPOLATED -- INV-032
-------------------------------
Every area, every dimension, the fittings list and the door pitch. What
constrains them: a unit must hold a bed, a person standing beside it and a
door that opens; the areas must descend with class or the gradient is a lie;
and a run of units must tile a corridor exactly, because a residual gap is a
hole a player walks into.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402
import interior_kit as kit                                     # noqa: E402

# ---------------------------------------------------------------------------
# The classes
# ---------------------------------------------------------------------------
# rank: 0 is the top of the social order. `area_m2` and `fittings` are INV-032;
# `sector` and `auth` are sourced -- see the module docstring's table.
#
# `shower` is authority 4 and it is the single most characterful line in §11:
# showers are for command quarters and the executive suites ONLY, because water
# is rationed (LIFE-SUPPORT-AND-INDUSTRY.md L-03/L-04 gives the reason -- the
# loop must be >98% closed). Everyone else gets a sonic cleaner. A utility
# becomes a visible class marker.
CLASSES = (
    dict(key="command", rank=0, sector="blue", area_m2=34.0, shower=True,
         auth=4, fittings=("bed", "desk", "seat", "locker", "screen",
                           "shower")),
    dict(key="personnel", rank=1, sector="blue", area_m2=18.0, shower=False,
         auth=3, fittings=("bed", "desk", "locker", "screen")),
    dict(key="diplomatic", rank=2, sector="green", area_m2=46.0, shower=True,
         auth=3, fittings=("bed", "desk", "seat", "locker", "screen",
                           "shower")),
    dict(key="alien_resident", rank=3, sector="green", area_m2=22.0,
         shower=False, auth=4, fittings=("bed", "locker", "screen")),
    dict(key="civilian", rank=4, sector="red", area_m2=16.0, shower=False,
         auth=4, fittings=("bed", "desk", "locker", "screen")),
    dict(key="transient", rank=5, sector="red", area_m2=9.0, shower=False,
         auth=4, fittings=("bed", "locker")),
    # No room. See the module docstring.
    dict(key="lurker", rank=6, sector="grey", area_m2=0.0, shower=False,
         auth=3, fittings=()),
)

# Unit proportions. A quarters unit is deeper than it is wide -- it opens off a
# corridor, so the door wall is the short one. 1:1.6 is the ratio used
# throughout; the area then fixes both dimensions, which is why area is the
# only free number per class.
UNIT_ASPECT = 1.6
UNIT_H_M = 2.8             # floor to ceiling; below DECK_PITCH_M's 3.6 m
WALL_T_M = 0.16

# Fittings. Sized to a 1.7 m occupant and asserted to leave a walkable path.
BED_L_M, BED_W_M, BED_H_M = 2.05, 0.95, 0.55
DESK_L_M, DESK_D_M, DESK_H_M = 1.30, 0.60, 0.74
SEAT_M = 0.55
LOCKER_W_M, LOCKER_D_M, LOCKER_H_M = 0.90, 0.55, 2.05
SCREEN_W_M, SCREEN_H_M, SCREEN_T_M = 0.75, 0.45, 0.06
SHOWER_M = 1.00
WALK_MIN_M = 0.75          # the clear path a person needs past the fittings


def class_by_key(key):
    for c in CLASSES:
        if c["key"] == key:
            return c
    raise KeyError(f"unknown quarters class {key!r}")


def unit_dims(cls):
    """Width (door wall) and depth, from the class area and the fixed aspect.

    Returns (0, 0) for a class that emits no room -- `lurker`. Callers must
    handle that rather than being handed a fake 1 m x 1 m cell, because a fake
    room is how Downbelow would quietly become an apartment block.
    """
    a = cls["area_m2"]
    if a <= 0:
        return 0.0, 0.0
    w = math.sqrt(a / UNIT_ASPECT)
    return w, w * UNIT_ASPECT


def floor_gravity(schema, profile, cls):
    """The gravity a resident of this class actually feels.

    Read live from `interior.py`. The gazetteer's own figures predate INV-026
    and are stale; this never restates them.
    """
    r = it.sector_radius(schema, profile, cls["sector"])
    return it.gravity_at(schema, r)


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
    return v, t, g


def unit(cls):
    """One quarters unit, authored with the door wall at z = 0.

    x across the unit, y up, z into it from the corridor.
    """
    if isinstance(cls, str):
        cls = class_by_key(cls)
    w, d = unit_dims(cls)
    if w <= 0:
        return [], [], []
    v, t, g = [], [], []
    hw = w / 2.0

    # Shell: four walls, deck and soffit, with the door wall left open. Built
    # as plates around the volume, never as a solid with a hole -- the mistake
    # command_control.py shipped when it sealed its own window inside the wall.
    _box(v, t, g, "qtr_deck", (-hw, -0.12, 0.0), (hw, 0.0, d))
    _box(v, t, g, "qtr_soffit", (-hw, UNIT_H_M, 0.0), (hw, UNIT_H_M + 0.12, d))
    _box(v, t, g, "qtr_wall", (-hw - WALL_T_M, 0.0, 0.0), (-hw, UNIT_H_M, d))
    _box(v, t, g, "qtr_wall", (hw, 0.0, 0.0), (hw + WALL_T_M, UNIT_H_M, d))
    _box(v, t, g, "qtr_wall", (-hw - WALL_T_M, 0.0, d),
         (hw + WALL_T_M, UNIT_H_M, d + WALL_T_M))

    f = set(cls["fittings"])
    # Bed along the far wall, long axis across the unit.
    if "bed" in f:
        _box(v, t, g, "qtr_bed",
             (-hw + 0.05, 0.0, d - BED_W_M - 0.05),
             (-hw + 0.05 + BED_L_M, BED_H_M, d - 0.05))
    if "desk" in f:
        _box(v, t, g, "qtr_desk",
             (hw - DESK_L_M - 0.05, 0.0, 0.6),
             (hw - 0.05, DESK_H_M, 0.6 + DESK_D_M))
    if "seat" in f:
        _box(v, t, g, "qtr_seat",
             (hw - SEAT_M - 0.35, 0.0, 0.6 + DESK_D_M + 0.15),
             (hw - 0.35, 0.42, 0.6 + DESK_D_M + 0.15 + SEAT_M))
    if "locker" in f:
        _box(v, t, g, "qtr_locker",
             (-hw + 0.05, 0.0, 0.05),
             (-hw + 0.05 + LOCKER_W_M, LOCKER_H_M, 0.05 + LOCKER_D_M))
    if "screen" in f:
        # A Babcom terminal in every quarters -- LOCATIONS.md line 371: "how
        # news and propaganda physically reach people".
        _box(v, t, g, "qtr_babcom",
             (-SCREEN_W_M / 2, 1.25, d - SCREEN_T_M),
             (SCREEN_W_M / 2, 1.25 + SCREEN_H_M, d))
    if "shower" in f:
        # The class marker. Water is rationed; this is a privilege of rank.
        _box(v, t, g, "qtr_shower",
             (hw - SHOWER_M - 0.05, 0.0, d - SHOWER_M - 0.05),
             (hw - 0.05, UNIT_H_M, d - 0.05))

    return v, t, g


def walkable_width_m(cls):
    """Clear path left between the fittings and the opposite wall.

    A unit that cannot be walked through is not a room, and area alone does not
    catch that -- a 9 m2 transient cell with a 2.05 m bed across it would pass
    any area check and be unusable. Measured against the bed, which is the
    widest fitting in every class that has one.
    """
    if isinstance(cls, str):
        cls = class_by_key(cls)
    w, d = unit_dims(cls)
    if w <= 0:
        return 0.0
    used = BED_W_M if "bed" in cls["fittings"] else 0.0
    if "locker" in cls["fittings"]:
        used += LOCKER_D_M
    return d - used - 0.2


def run(schema, profile, cls, count=6, corridor_w_m=None):
    """A row of units opening off one side of a corridor.

    Units tile exactly along the run: a residual gap between two quarters is a
    void a player can walk into, and it is invisible in any elevation.
    """
    if isinstance(cls, str):
        cls = class_by_key(cls)
    w, d = unit_dims(cls)
    if w <= 0:
        return [], [], []
    p = kit.class_params("residential")
    cw = corridor_w_m or p["corridor_width_m"]
    V, T, G = [], [], []
    uv, ut, ug = unit(cls)
    pitch = w + 2 * WALL_T_M
    for i in range(count):
        x0 = i * pitch
        off = len(V)
        t0 = len(T)
        V.extend((x + x0, y, z + cw / 2.0) for x, y, z in uv)
        T.extend((a + off, b + off, c + off) for a, b, c in ut)
        G.extend((n, lo + t0, hi + t0) for n, lo, hi in ug)
    return V, T, G


def _signed_volume(v, t):
    s = 0.0
    for a, b, c in t:
        p, q, r = v[a], v[b], v[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = it.load()

    # --- THE CLASS GRADIENT, which is the whole point ---------------------
    # "The people with the least power live where they weigh the most."
    # Asserted as monotonicity over the classes that have a sector, not as
    # prose. Ranks ascend as gravity ascends.
    rows = [(c["rank"], c["key"], floor_gravity(schema, profile, c))
            for c in CLASSES]
    rows.sort()
    gs = [g for _r, _k, g in rows]
    # Diplomatic (Green, 1.000 g) outranks personnel (Blue, 0.760 g), so the
    # gradient is not strictly monotonic across every adjacent pair -- and
    # saying it is would be a false claim. What IS true, and what the gazetteer
    # actually asserts, is that the BOTTOM of the order is the heaviest place
    # and the TOP is not.
    check("the lowest class lives at the highest gravity",
          gs[-1] == max(gs),
          f"{rows[-1][1]} at {gs[-1]:.3f} g vs max {max(gs):.3f} g")
    check("the highest class does not live at the highest gravity",
          gs[0] < max(gs), f"{rows[0][1]} at {gs[0]:.3f} g")
    check("the spread across classes is felt, not marginal",
          max(gs) - min(gs) > 0.5,
          f"{min(gs):.3f} g to {max(gs):.3f} g = "
          f"{max(gs) / min(gs):.2f}x body weight")
    # And the specific claim the gazetteer makes about Downbelow.
    lurker = class_by_key("lurker")
    check("the lurker class is the heaviest place anyone lives",
          floor_gravity(schema, profile, lurker) == max(gs),
          f"{floor_gravity(schema, profile, lurker):.3f} g")

    # --- the stale gazetteer figure ---------------------------------------
    # §11 quotes Blue at 0.603 g. That predates INV-026. Assert the divergence
    # so nobody re-copies the old number believing it still holds.
    blue = floor_gravity(schema, profile, class_by_key("command"))
    check("Blue's gravity has moved since the gazetteer was written",
          abs(blue - 0.603) > 0.05,
          f"live {blue:.3f} g vs the gazetteer's stale 0.603 g -- "
          f"§11 needs refreshing")

    # --- areas, and the honest shape of the ordering -----------------------
    # RANK IS SOCIAL ORDER, NOT FLOOR AREA, and asserting they march together
    # would be a false claim: diplomatic is rank 2 and has the LARGEST quarters
    # on the station, because ambassadorial suites outrank command quarters
    # here. The first version of this check tried to paper over that with a
    # compound `or` and failed, which was the assertion being right and the
    # claim being wrong.
    #
    # What is actually true is that rank orders area WITHIN a sector. That is a
    # real property, it is what a housing allocation would produce, and it can
    # fail.
    with_rooms = [c for c in CLASSES if c["area_m2"] > 0]
    by_sector = {}
    for c in with_rooms:
        by_sector.setdefault(c["sector"], []).append(c)
    for sec, cs in sorted(by_sector.items()):
        cs = sorted(cs, key=lambda c: c["rank"])
        check(f"{sec}: rank orders floor area within the sector",
              all(cs[i]["area_m2"] > cs[i + 1]["area_m2"]
                  for i in range(len(cs) - 1)),
              str([(c["key"], c["area_m2"]) for c in cs]))
    check("the transients have the smallest quarters",
          class_by_key("transient")["area_m2"]
          == min(c["area_m2"] for c in with_rooms))
    check("the ambassadors have the largest, as §6 implies",
          class_by_key("diplomatic")["area_m2"]
          == max(c["area_m2"] for c in with_rooms))
    # The gap between the top and the bottom of the housing ladder, which is
    # the number that makes the class layer legible at a glance.
    check("the housing gap is stark enough to read as class",
          max(c["area_m2"] for c in with_rooms)
          / min(c["area_m2"] for c in with_rooms) > 4.0,
          f"{max(c['area_m2'] for c in with_rooms) / min(c['area_m2'] for c in with_rooms):.1f}x "
          f"between an ambassador and a transient")

    # --- showers are a class marker, and only that -------------------------
    show = {c["key"] for c in CLASSES if c["shower"]}
    check("showers are for command and the suites only, as §11 says",
          show == {"command", "diplomatic"}, str(sorted(show)))
    check("a shower implies the fitting is actually built",
          all("shower" in c["fittings"] for c in CLASSES if c["shower"]))

    # --- Downbelow emits no room ------------------------------------------
    check("the lurker class has no unit geometry, because it is not rooms",
          unit("lurker") == ([], [], []),
          "Downbelow is corridors and chambers -- plant.py builds it")
    check("and no fake dimensions are handed back for it",
          unit_dims(lurker) == (0.0, 0.0))

    # --- the rooms are usable ---------------------------------------------
    for c in with_rooms:
        w, d = unit_dims(c)
        check(f"{c['key']}: the unit is deeper than it is wide",
              d > w, f"{w:.2f} x {d:.2f} m")
        check(f"{c['key']}: a bed fits across the unit",
              "bed" not in c["fittings"] or w >= BED_L_M + 0.2,
              f"{w:.2f} m wide for a {BED_L_M} m bed")
        check(f"{c['key']}: there is a walkable path past the fittings",
              walkable_width_m(c) >= WALK_MIN_M,
              f"{walkable_width_m(c):.2f} m clear, need {WALK_MIN_M} m")
        check(f"{c['key']}: the ceiling fits inside a deck",
              UNIT_H_M < it.DECK_PITCH_M,
              f"{UNIT_H_M} m in a {it.DECK_PITCH_M} m pitch")

    # --- a Babcom terminal in every quarters ------------------------------
    # LOCATIONS.md line 371: a terminal in every quarters is how news and
    # propaganda physically reach people. If a class has a screen listed, it
    # must actually be built.
    for c in with_rooms:
        if "screen" in c["fittings"]:
            names = {n for n, _lo, _hi in unit(c)[2]}
            check(f"{c['key']}: the Babcom terminal is built",
                  "qtr_babcom" in names)

    # --- runs tile exactly -------------------------------------------------
    V, T, G = run(schema, profile, "personnel", count=6)
    check("a run of quarters builds", len(T) > 300, f"{len(T)} triangles")
    w, _d = unit_dims(class_by_key("personnel"))
    pitch = w + 2 * WALL_T_M
    xs = sorted({round(q[0], 6) for q in V})
    check("units tile the run without a residual gap",
          abs((max(xs) - min(xs)) - (5 * pitch + w + 2 * WALL_T_M)) < 1e-6,
          f"span {max(xs) - min(xs):.4f} vs "
          f"{5 * pitch + w + 2 * WALL_T_M:.4f}")

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0, 0, 0), (1, 2, 3))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0)
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)

    print("\nresidential class gradient, gravity read live:")
    for r, k, gg in rows:
        c = class_by_key(k)
        w, d = unit_dims(c)
        size = f"{w:.1f} x {d:.1f} m, {c['area_m2']:.0f} m2" if w else "no rooms"
        print(f"  {r}  {k:15s} {c['sector']:6s} {gg:.3f} g   {size}")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
