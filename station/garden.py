"""The Garden's townscape -- the payoff view of the whole project.

`drum_ground.py` gave the drum a surface: land-use bands, block plateaux,
avenues, verges, water. What it did not give it was a *town*. Standing in the
Garden you were standing on believable terrain in an empty world.

`docs/gazetteer/LOCATIONS.md` ranks this **fifth**, and is blunt about the
constraint: the drum's inner surface is **4.5 million m2** with about 250,000
triangles of headroom, which is **0.06 tri/m2**. Fields, roads and settlement
pattern are texture and displacement. **Only what a person can walk up to gets
mesh.** This module is that mesh, and every decision in it is downstream of
that number.

SOURCE -- and it is the best single interior frame in the whole reference set
-------------------------------------------------------------------------
`reference/09-garden-core-and-transit/garden.png`, authority 1. It shows,
unambiguously:

  * **A civic landmark of stacked cylindrical drums** in warm buff concrete --
    a tall tower with a **colonnaded upper storey** (a ring of vertical fins
    over open bays), a second lower drum beside it colonnaded the same way,
    **cantilevered horizontal slab terraces** wrapping the base, and a
    **glazed ground floor** whose windows are lit warm from inside. Curved
    throughout. The idiom is streamline-moderne, not the station's industrial
    grey, and that contrast is the point: the Garden is where the station
    stops looking like a machine.
  * **A rectangular reflecting pool**, green water, dark coping.
  * **Paved terraces** in large slabs, and **mown lawn strips**.
  * **A tall thin waterfall** down a dark planted bank at the left.
  * **Flagpoles carrying white banners** at the right.
  * **A red-orange painted external stair** -- the one saturated accent in an
    otherwise buff and green scene.
  * **Two people walking**, which is the scale anchor.
  * Behind everything, **the far side of the drum arching overhead as
    patchwork fields**, crossed by the guideway trusses.

MEASURED FROM THE FRAME
-----------------------
The two figures are ~35 px tall; the landmark stands ~330 px from terrace to
tower cap. At a 1.7 m stature that is **~16 m, about five storeys** -- which
agrees with the gazetteer's "~6 storeys" read closely enough to adopt, and is
recorded as a measurement rather than a choice. Everything else is proportioned
against it and logged as **INV-030**.

PLACEMENT IS NOT FREE
---------------------
Buildings go in **settlement bands only**. `interior.LAND_USE` puts those at
0.26-0.40 and 0.72-0.84 of the circumference -- **93.6-144 deg** and
**259.2-302.4 deg** -- and everything else is arable, water or parkland. A
building on a field is a bug, and the self-test asserts against it rather than
trusting the caller.

Ground height comes from `drum_ground.terrain_sample()` on every footing, so a
building follows the heightfield instead of floating over it or sinking into
it. That is the same class of error that put the first drum camera five metres
underground in session 2u.

SESSION 4q -- THE PART A PLAYER STANDS IN
-----------------------------------------
`docs/aaa-scorecard.json` scores `garden_townscape` **craft 1**, twice, and the
owner's words behind that score are "shitty little cubes" and "a sad excuse for
a tree". Session 3z rebuilt both generators against a line-density floor
(INV-072) and **the score did not move**, which is the interesting part and the
reason this section exists.

WHAT WAS ACTUALLY WRONG, read off an engine frame at the rubric's HALF distance
rather than off a metric. `scratchpad/frames/before-tree5.png`, Forward+ on
Vulkan 1.4, eye 11 m from a tree:

  * the tree was a **five-facet green blob on a black spike**. Cause, and it is
    arithmetic rather than taste: `tree()` drew its height from a distribution
    and every canopy lobe from the CONSTANT `TREE_R_M = 2.2`, so the taller half
    of the population got a 2.2 m crown on a 10 m stem -- a lollipop by
    construction, whatever else was hung on it. -> `CROWN_FRAC`, INV-453.
  * the buildings were **grey slabs reading as retaining walls**. The 3z rebuild
    had put pilasters, cills, gutters, downpipes, balconies and roof plant on a
    single rectangular prism: twenty-one times the line and the same
    silhouette. "Cubes" is a statement about MASS. -> terracing, INV-455.
  * the ground was two flat colour fields meeting along a drawn edge with
    nothing standing on either -- the same finding STATE.md 24.4b records
    against `docs/engine-4q-drum-dressed.png`. -> ground cover, INV-456.
  * a tree's canopy stood **inside a building**, from 11 m away, because blocks
    and trees were drawn from two independent distributions and neither knew
    about the other. Nothing measured it.

THE STRUCTURAL POINT, and it is the transferable one: every gate this module
had -- triangle count, line density, closure, winding, determinism, the surface
budget -- is satisfied by a ball on a stick beside a box. **A metric that
scores a part cannot ask what the part IS.** The gates added below ask shape
questions instead: crown span over height, mass plan at two heights over the
walls alone, foliage masses off the trunk axis, a trunk section that is not a
circle. Each one is shown failing on the content it replaced.

The near field is a LEVEL BELOW `drum_dressing`'s ladder, not more detail on
it -- see `NEAR_LEVEL` and INV-452 for why the default level is deliberately
not the finest one.
"""
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402
import drum_ground as dg                                       # noqa: E402

# ---------------------------------------------------------------------------
# The civic landmark, measured against the two figures in garden.png
# ---------------------------------------------------------------------------
TOWER_H_M = 16.0           # terrace to cap: 330 px / 35 px * 1.7 m
TOWER_R_M = 5.2
TOWER_SEG = 20

# The colonnade at the top of each drum: a ring of vertical fins over open bays.
COLONNADE_H_M = 3.4
COLONNADE_FINS = 20
COLONNADE_FIN_W_M = 0.45

# The second, lower drum beside the tower.
DRUM2_H_M = 9.5
DRUM2_R_M = 4.1
DRUM2_OFFSET_M = 9.0

# Cantilevered slab terraces wrapping the base.
SLAB_T_M = 0.45
SLAB_OVERHANG_M = 2.6
SLAB_LEVELS = 3
SLAB_RISE_M = 3.2          # one storey

# The glazed ground floor.
GLAZE_H_M = 3.0
GLAZE_BAYS = 14
GLAZE_MULLION_M = 0.22

# ---------------------------------------------------------------------------
# The setting
# ---------------------------------------------------------------------------
POOL_L_M = 30.0
POOL_W_M = 12.0
POOL_DEPTH_M = 0.9
POOL_COPING_M = 0.8

TERRACE_SLAB_M = 2.5       # paving module
TERRACE_L_M = 46.0
TERRACE_W_M = 26.0

LAWN_L_M = 18.0
LAWN_W_M = 7.0

FLAGPOLE_H_M = 9.0
FLAGPOLE_R_M = 0.11
BANNER_W_M = 0.9
BANNER_H_M = 3.2
FLAGPOLES = 4
FLAGPOLE_PITCH_M = 3.2

WATERFALL_H_M = 11.0
WATERFALL_W_M = 1.6
BANK_W_M = 14.0
BANK_H_M = 12.0

STAIR_RISE_M = 0.18
STAIR_GOING_M = 0.29
STAIR_W_M = 2.2
STAIR_FLIGHT = 18          # the red-orange external stair

# The generic townscape beyond the landmark: low blockish buildings with lit
# window bands. These are what fill a settlement band, and they are cheap on
# purpose -- see the 0.06 tri/m2 note above.
BLOCK_MIN_M = (9.0, 6.0, 4.0)      # length, width, height
BLOCK_MAX_M = (22.0, 13.0, 11.0)
BLOCK_BANDS = 3                     # vestigial: see `_banded_tier` (INV-455)

# --- hard landscape, all INV-072, all from 29a's extraction -------------------
PATH_W_M = 2.4
PATH_PITCH_M = 14.0
KERB_W_M = 0.15
KERB_H_M = 0.12
HEDGE_RUNS = 24
HEDGE_MIN_M = 6.0
HEDGE_MAX_M = 18.0
HEDGE_W_M = 0.8
HEDGE_H_M = 1.05                    # clipped, so below eye level
STEP_COUNT = 4
STEP_RISE_M = 0.16
STEP_GOING_M = 0.34
STEP_RUN_M = 2.6
STEP_W_M = 9.0
PLANTER_R_M = 3.1
PLANTER_H_M = 0.62
PLANTER_COPE_M = 0.16
PLANTER_SEG = 16
BENCHES = 6
BENCH_L_M = 1.8
BENCH_H_M = 0.45
BENCH_SLATS = 4
BENCH_SLAT_W_M = 0.09
BENCH_SLAT_P_M = 0.13
SAILS = 3
SAIL_W_M = 5.2
SAIL_D_M = 3.4
MAST_H_M = 3.6
MAST_R_M = 0.07

TREE_H_M = 7.0
TREE_R_M = 2.2
TREE_SEG = 6                        # kept: `setting()` still uses it for hedging

# ---------------------------------------------------------------------------
# THE NEAR FIELD -- the level below `drum_dressing`'s ladder, INV-452..INV-456
# ---------------------------------------------------------------------------
# `station/drum_dressing.py` dressed the drum FLOOR and its own honest limit is
# recorded in STATE.md 24.4b against `docs/engine-4q-drum-dressed.png`:
#
#     "The near field is empty ... The scatter is dense enough to read at 500 m
#      and not at 20 m, which is the opposite of where a player stands. The LOD
#      ladder resolves DETAIL by distance; it does not place more things near
#      the eye ... The near tree is still a lollipop -- a dark blob on a stick,
#      at the distance where a player would see bark."
#
# Verified here before touching anything, which is the only reason the fix is
# aimed correctly. `scratchpad/frames/before-tree5.png` -- Forward+ on Vulkan
# 1.4, eye 11 m from `garden.tree()`'s canopy -- shows a FIVE-FACET dark green
# blob on a black spike, in front of a grey slab with no window on the face it
# presents, over flat ground. Three separate defects, and the tree's has a
# cause that no line-density metric could ever have caught:
#
#     `TREE_R_M` IS A CONSTANT AND `h` IS NOT. `tree()` draws its height from
#     `TREE_H_M * (0.75 + 0.5 * u)` -- 5.25 to 10.5 m -- and every canopy lobe
#     from a FIXED `TREE_R_M = 2.2`. A 10.5 m tree therefore gets a 2.2 m
#     crown: a lollipop BY CONSTRUCTION, on the tall half of the population,
#     however many lobes are hung on it. The crown lobe alone is 1.15-1.5 m and
#     sits 0.8-1.6 m from every limb lobe, so the "several overlapping lobes"
#     the docstring argues for resolve into one ball.
#
# So the ladder gains a level BELOW `drum_dressing.LOD_RATIOS`, rather than the
# existing levels gaining triangles. Numbering follows that module exactly --
# level 0 is its LOD0 and its cost, level 1/2/3 are its proxies -- and the new
# one is **level -1**, which is the only numbering that cannot be misread six
# sessions from now: a level nearer than its nearest.
#
# WHY THE DEFAULT IS NOT THE FINEST, and it is a cross-module fact rather than
# a preference: `drum_dressing._tree_proto` and `_building_proto` call
# `gd.tree(seed)` and `gd.block_building(seed)` with NO level for their own
# LOD0, and `drum_dressing.LOD_SCALE_M = 113.0` was SOLVED by bisection against
# `DRESSING_TRIS` at that cost. Making the bare call finer moves 1,945 features
# through a budget that is already spent to 119,868 of 120,000. `_selftest`
# asserts the bare call stays inside the cost it was solved against, and that
# assertion fails if a future session forgets.
NEAR_LEVEL = -1

# The near switch. IT IS A BUDGET AND NOT A PERCEPTUAL RESULT, and saying so
# is the point of this comment, because the first draft of it claimed the
# opposite and the arithmetic refuted me.
#
# The obvious derivation is the one `drum_dressing._switch_distance` uses:
# switch once the smallest feature the coarser level throws away falls under a
# pixel. Run on this level's own features, at the project's own FOV 50 deg /
# 1440 px constants (`drum_ground.FOV_DEG`, `SCREEN_H`), it says:
#
#     bark flute, 0.0286 m deep  ->  1.0 px at  44.2 m
#     order-3 twig, 0.104 m dia  ->  1.0 px at 160.6 m
#
# So a pixel criterion says "carry the near level out past 160 m", which is
# every tree in the settlement at 2,900 triangles each. That is exactly the
# refutation `drum_dressing`'s own docstring records one level up -- "a
# pixel-error criterion says never switch" -- and it applies here with more
# force, because near-field content is the expensive kind.
#
# 35 m is therefore a BUDGET, stated as one. It is under both pixel figures,
# so the level never carries a feature that has already vanished; and the real
# spending control is `HERO_TREES` below, which is a COUNT, because a radius
# silently costs whatever happens to fall inside it. `--near` prints both
# columns so the next session can see the trade rather than re-derive it.
NEAR_SWITCH_M = 35.0

# Crown radius as a fraction of tree height. THE BUG ABOVE, fixed as a rule
# rather than as a bigger constant. A mature open-grown garden broadleaf is
# about as wide as it is tall, so the radius is ~0.45 h; `garden.png`'s trees
# behind the landmark read 0.40-0.55 of their own height in radius, and 29a's
# overhanging broadleaf is wider than tall (it is pruned over a path). Bounded
# BELOW by 0.30, under which a broadleaf reads as a conifer; ABOVE by 0.60, at
# which the crown out-spans the path pitch and the canopies merge into a roof.
CROWN_FRAC = 0.45
FLUTE_D = 0.11                      # bark ridge depth, as a fraction of radius
FLUTE_N = 7                         # ridges round the trunk
TRUNK_RINGS = 5
BRANCH_ORDERS = 3                   # trunk -> limb -> bough -> twig
LIMBS_MIN, LIMBS_MAX = 4, 6
BOUGHS_MIN, BOUGHS_MAX = 2, 3
LEAF_LOBES = 3                      # small masses per bough tip
LEAF_R_FRAC = 0.40                  # lobe radius as a fraction of the crown

# The form vocabulary, and every one of the three is authority 1.
#   broadleaf  `garden.png` "deciduous trees and shrubs", dark rounded masses
#              behind the landmark; `The Gardens.webp` "dark rounded broadleaf
#              trees"; `Babylon_5_2-22_29a.jpg`'s overhanging canopy.
#   umbrella   29a, upper left: broad FLAT-TOPPED canopies on clear stems --
#              pruned street trees, the widest thing in that frame.
#   palm       `The Gardens.webp`: "Palm trees lining streets and open ground".
#              The only frame that shows the settlement's own street planting.
TREE_FORMS = ("broadleaf", "umbrella", "palm")
FROND_COUNT = (9, 14)
FROND_SEG = 4                       # a 4-gon section IS a midrib, not a saving
FROND_FLAT = 0.17                   # blade thickness as a fraction of its width
PALM_SCARS = 7                      # leaf scars up the stem, one crease each

# --- massing, INV-455 --------------------------------------------------------
# `14-characters-and-uniforms/talia-winters in gorgeous office.webp`, authority
# 1, reads the far side as "low wide grey settlement blocks, TERRACED rather
# than towered"; `The Gardens.webp` reads the same town at ground level as
# "low-rise flat-roofed blocky buildings, two to four storeys, in a dense
# orthogonal street grid ... continuous horizontal window banding -- rows of
# small bright rectangles in dark recessed bands ... one large building shows
# exactly three stacked glazed bands over a SOLID BATTERED BASE ... long low
# linear blocks with unbroken window strips."
#
# None of that was built. The old mass is ONE rectangular prism with trim on
# it, which is what `before-tree5.png` shows: a grey slab reading as a
# retaining wall. Trim does not change a silhouette and the silhouette is what
# the owner's word "cubes" is about. These are the numbers that do.
SETBACK_M = 1.35                    # each tier steps back this far all round
BATTER_M = 0.55                     # the base's outward lean, bottom over top
BATTER_H_M = 2.20                   # height the batter resolves over
TIER_MIN, TIER_MAX = 2, 3
WING_FRAC = 0.55                    # the low wing's length, as a fraction of L
WING_D_M = 5.5
WING_H_M = 3.6
BAND_RECESS_M = 0.34                # the dark band the window rows sit in
BAND_H_M = 1.30
PANE_W_M = 0.95                     # "rows of SMALL bright rectangles"
PANE_PITCH_M = 1.55
PANE_H_M = 0.90
CANOPY_D_M = 1.9                    # the slab canopy over the entrance
CANOPY_T_M = 0.26

# --- ground cover, INV-456 ---------------------------------------------------
# `docs/engine-4q-drum-dressed.png` and `before-tree5.png` both show the same
# thing underfoot: two flat colour fields meeting along a hard straight edge,
# with nothing standing on either. 29a is the only authority-1 frame taken at
# eye level in the Garden and it shows the opposite -- "paved winding paths in
# small setts", "clipped hedges", "a circular raised planter with a red-brown
# coping" massed with flowering shrub, "terracing retained by horizontal
# red-brown timber-slat walls", ivy over the planted bank.
SCRUB_R_M = 0.62                    # one low shrub clump
SCRUB_H_FRAC = 0.55                 # squashed: wider than tall
SCRUB_PER_100M2 = 2.0               # near-field clumps per 100 m2 of verge
TUSSOCK_R_M = 0.26
TUSSOCK_PER_100M2 = 4.4
VERGE_W_M = 3.2                     # the planted band that kills the hard edge
COBBLE_M = 0.42                     # sett module, 29a "small setts"
COBBLE_PROUD_M = 0.018              # a sett stands this proud of its neighbour
KEEPOUT_M = 2.0                     # clearance between a tree crown and a wall

# --- articulation, all INV-072 -----------------------------------------------
# The old TREE_SEG comment read "a tree at 0.06 tri/m2 is a billboard's cousin",
# which was an accurate description of a constraint this module asserted on
# itself. That ceiling is gone (see `_selftest`) and these are the proportions
# that replace it. Every one is a declared extrapolation: `garden.png` and
# `Babylon_5_2-22_29a.jpg` establish that the Garden has broadleaf planting and
# banded multi-storey blocks, not the millimetres of either.
TRUNK_R_M = 0.26                    # at the flare top, a mature garden broadleaf
TRUNK_SEG = 10
FLARE_K = 1.45                      # root flare radius multiple at ground
FLARE_H_M = 0.55                    # height the flare resolves over
FORK_FRAC = 0.42                    # trunk height where limbs spring, as a frac of h
# Vestigial as of 4q: `tree()` now sizes its sections from `_TREE_LOD`. Kept
# because `drum_dressing._tree_proto` builds its own levels 1-3 out of this
# module's primitives and a constant it might reach for is cheaper to keep than
# to prove unused. Nothing in `garden.py` reads them.
LIMB_SEG = 6
LOBE_SEG = 8
LOBE_STACKS = 4

STOREY_M = 3.2                      # floor to floor, low-rise garden block
PLINTH_H_M = 0.75
PLINTH_PROUD_M = 0.30               # mass is inset this far behind the plinth
BAY_W_M = 4.0                       # structural bay, so a 16 m facade reads 4 bays
PILASTER_W_M = 0.55
PILASTER_PROUD_M = 0.18
SLAB_T_M = 0.32                     # expressed floor slab thickness
SLAB_PROUD_M = 0.12
SILL_M = 0.85
WIN_H_M = 1.95
REVEAL_M = 0.28                     # glazing set back this far -- the line-maker
CORNICE_H_M = 0.45
CORNICE_P_M = 0.34                  # cornice projection
PARAPET_H_M = 0.85
GUTTER_D_M = 0.16
PIPE_R_M = 0.075
DOWNPIPES_PER_FACE = 5
BALC_T_M = 0.18
BALC_D_M = 1.25
BALC_RAILS = 4
BALC_RAIL_H_M = 1.05
RAIL_T_M = 0.05
RAIL_H_M = 1.0
LAMP_PITCH_M = 7.5
LAMP_R_M = 0.075
LAMP_H_M = 4.2
LAMP_HEAD_M = 0.34
BAND_T_M = 0.14
BAND_P_M = 0.10
ROOF_PIPES = 5
ROOF_PIPE_H_M = 0.42
PERGOLA_BAY_M = 4.5
PERGOLA_R_M = 0.11
PERGOLA_H_M = 2.9
PERGOLA_B_M = 0.16
TRACK_OFFSET_M = 6.0
TRACK_GAUGE_M = 2.1
TRACK_H_M = 0.9
SLEEPER_PITCH_M = 3.2
SLEEPER_W_M = 0.24
SLEEPER_T_M = 0.16
BOUNDARIES = 16
BOUNDARY_W_M = 0.35
BOUNDARY_H_M = 0.55
JOINT_PITCH_M = 1.8
JOINT_W_M = 0.06
BEDS = 28
BED_MIN_M = 5.0
BED_MAX_M = 16.0
BED_EDGE_M = 0.10
BED_EDGE_H_M = 0.22
TRENCHES = 15
TRENCH_W_M = 0.70
TRENCH_LIP_M = 0.09

# Settlement bands, read from interior.LAND_USE rather than restated.
_SETTLEMENT = "settlement"


def settlement_arcs():
    """Angular spans of the settlement bands, in degrees.

    Read from `interior.LAND_USE`, never hard-coded: the band table is the
    single source for what the drum's surface is, and a second copy here would
    drift the moment someone retunes it.
    """
    out, acc = [], 0.0
    for frac, name, _relief in it.LAND_USE:
        if name == _SETTLEMENT:
            out.append((acc * 360.0, (acc + frac) * 360.0))
        acc += frac
    return out


def in_settlement(angle_deg):
    a = angle_deg % 360.0
    return any(lo <= a < hi for lo, hi in settlement_arcs())


def _u(*parts):
    """Deterministic unit float. blake2b, never `random`, never `str.__hash__`
    -- the latter is salted per process and would give a different town every
    run. Same discipline as `greeble.py` and `npc/names.py`."""
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


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


def _drum(v, t, g, name, cx, cz, y0, y1, r, seg=TOWER_SEG, cap=True):
    """A vertical cylinder: y is up in the local frame."""
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
    if cap:
        c = len(v)
        v.append((cx, y1, cz))
        for k in range(seg):
            a = n0 + 2 * k + 1
            b = n0 + 2 * ((k + 1) % seg) + 1
            t.append((c, a, b))
    g.append((name, t0, len(t)))
    return v, t, g


def civic_landmark():
    """The building in `garden.png`, authored in a local frame.

    x tangential, y UP, z along the station axis, origin at its own terrace.
    """
    v, t, g = [], [], []

    # Cantilevered slab terraces, widest at the bottom.
    for i in range(SLAB_LEVELS):
        y = i * SLAB_RISE_M
        over = SLAB_OVERHANG_M * (SLAB_LEVELS - i) / SLAB_LEVELS
        r = TOWER_R_M + over
        _drum(v, t, g, "garden_slab", 0.0, 0.0, y, y + SLAB_T_M, r,
              seg=TOWER_SEG, cap=True)

    # Glazed ground floor: a ring of mullions with the glass set behind.
    for k in range(GLAZE_BAYS):
        a = math.tau * k / GLAZE_BAYS
        dx, dz = TOWER_R_M * math.cos(a), TOWER_R_M * math.sin(a)
        _box(v, t, g, "garden_mullion",
             (dx - GLAZE_MULLION_M / 2, SLAB_T_M, dz - GLAZE_MULLION_M / 2),
             (dx + GLAZE_MULLION_M / 2, SLAB_T_M + GLAZE_H_M,
              dz + GLAZE_MULLION_M / 2))
    _drum(v, t, g, "garden_glazing", 0.0, 0.0, SLAB_T_M, SLAB_T_M + GLAZE_H_M,
          TOWER_R_M - 0.25, seg=TOWER_SEG, cap=False)

    # The tower shaft.
    y_shaft0 = SLAB_T_M + GLAZE_H_M
    y_shaft1 = TOWER_H_M - COLONNADE_H_M
    _drum(v, t, g, "garden_tower", 0.0, 0.0, y_shaft0, y_shaft1, TOWER_R_M,
          cap=False)

    # The colonnade: vertical fins over open bays, then a cap slab.
    #
    # An INNER drum stands behind the fins. Without it the bays are open all
    # the way through and the render showed the magenta background through the
    # top of the building -- a hole, not a colonnade. The reference shows a
    # dark recessed interior behind the columns, which is what this is.
    _drum(v, t, g, "garden_colonnade_core", 0.0, 0.0, y_shaft1, TOWER_H_M,
          TOWER_R_M - COLONNADE_FIN_W_M, cap=False)
    for k in range(COLONNADE_FINS):
        a = math.tau * k / COLONNADE_FINS
        dx, dz = TOWER_R_M * math.cos(a), TOWER_R_M * math.sin(a)
        _box(v, t, g, "garden_colonnade",
             (dx - COLONNADE_FIN_W_M / 2, y_shaft1, dz - COLONNADE_FIN_W_M / 2),
             (dx + COLONNADE_FIN_W_M / 2, TOWER_H_M, dz + COLONNADE_FIN_W_M / 2))
    _drum(v, t, g, "garden_cap", 0.0, 0.0, TOWER_H_M, TOWER_H_M + SLAB_T_M,
          TOWER_R_M + 0.6)

    # The second, lower drum.
    y2 = DRUM2_H_M - COLONNADE_H_M
    _drum(v, t, g, "garden_tower", DRUM2_OFFSET_M, 0.0, SLAB_T_M, y2, DRUM2_R_M,
          cap=False)
    _drum(v, t, g, "garden_colonnade_core", DRUM2_OFFSET_M, 0.0, y2, DRUM2_H_M,
          DRUM2_R_M - COLONNADE_FIN_W_M, cap=False)
    for k in range(COLONNADE_FINS):
        a = math.tau * k / COLONNADE_FINS
        dx = DRUM2_OFFSET_M + DRUM2_R_M * math.cos(a)
        dz = DRUM2_R_M * math.sin(a)
        _box(v, t, g, "garden_colonnade",
             (dx - COLONNADE_FIN_W_M / 2, y2, dz - COLONNADE_FIN_W_M / 2),
             (dx + COLONNADE_FIN_W_M / 2, DRUM2_H_M, dz + COLONNADE_FIN_W_M / 2))
    _drum(v, t, g, "garden_cap", DRUM2_OFFSET_M, 0.0, DRUM2_H_M,
          DRUM2_H_M + SLAB_T_M, DRUM2_R_M + 0.5)

    # The red-orange external stair -- the one saturated accent in the frame.
    for i in range(STAIR_FLIGHT):
        y = i * STAIR_RISE_M
        z = -DRUM2_R_M - 1.0 - i * STAIR_GOING_M
        _box(v, t, g, "garden_stair_accent",
             (DRUM2_OFFSET_M - STAIR_W_M / 2, y, z - STAIR_GOING_M),
             (DRUM2_OFFSET_M + STAIR_W_M / 2, y + STAIR_RISE_M, z))

    return v, t, g


def setting():
    """Pool, terrace, lawn, flagpoles and the waterfall bank."""
    v, t, g = [], [], []

    _box(v, t, g, "garden_terrace",
         (-TERRACE_L_M / 2, -0.15, -TERRACE_W_M / 2),
         (TERRACE_L_M / 2, 0.0, TERRACE_W_M / 2))

    # Reflecting pool: a coped basin with a water plane inside it.
    px, pz = -TERRACE_L_M / 2 + POOL_L_M / 2 + 3.0, TERRACE_W_M / 2 - POOL_W_M / 2 - 2.0
    _box(v, t, g, "garden_pool_coping",
         (px - POOL_L_M / 2 - POOL_COPING_M, -0.15, pz - POOL_W_M / 2 - POOL_COPING_M),
         (px + POOL_L_M / 2 + POOL_COPING_M, 0.20, pz + POOL_W_M / 2 + POOL_COPING_M))
    _box(v, t, g, "garden_water",
         (px - POOL_L_M / 2, -POOL_DEPTH_M, pz - POOL_W_M / 2),
         (px + POOL_L_M / 2, -0.10, pz + POOL_W_M / 2))

    _box(v, t, g, "garden_lawn",
         (TERRACE_L_M / 2 - LAWN_L_M - 2.0, -0.12, -LAWN_W_M / 2),
         (TERRACE_L_M / 2 - 2.0, 0.02, LAWN_W_M / 2))

    for k in range(FLAGPOLES):
        x = TERRACE_L_M / 2 - 5.0 - k * FLAGPOLE_PITCH_M
        z = -TERRACE_W_M / 2 + 2.0
        _box(v, t, g, "garden_flagpole",
             (x - FLAGPOLE_R_M, 0.0, z - FLAGPOLE_R_M),
             (x + FLAGPOLE_R_M, FLAGPOLE_H_M, z + FLAGPOLE_R_M))
        _box(v, t, g, "garden_banner",
             (x + FLAGPOLE_R_M, FLAGPOLE_H_M - BANNER_H_M - 0.4,
              z - BANNER_W_M / 2),
             (x + FLAGPOLE_R_M + 0.06, FLAGPOLE_H_M - 0.4, z + BANNER_W_M / 2))

    # The planted bank and its waterfall, at the far left of the frame.
    bx = -TERRACE_L_M / 2 - BANK_W_M / 2
    _box(v, t, g, "garden_bank",
         (bx - BANK_W_M / 2, -0.15, -TERRACE_W_M / 2),
         (bx + BANK_W_M / 2, BANK_H_M, TERRACE_W_M / 2))
    _box(v, t, g, "garden_waterfall",
         (bx + BANK_W_M / 2 - 0.15, 0.0, -WATERFALL_W_M / 2),
         (bx + BANK_W_M / 2 + 0.10, WATERFALL_H_M, WATERFALL_W_M / 2))

    return v, t, g


def _taper(v, t, g, name, cx, cz, rings, seg=8, close_top=True):
    """A tapered, ringed cylinder: `rings` is [(y, r), ...] bottom to top.

    WHY RINGS AND NOT A SINGLE r0->r1 TAPER. A straight taper draws exactly two
    visible lines along its length -- the two silhouette edges -- however many
    segments it has, because every lateral edge between adjacent facets of a
    smooth cone falls below the 3.24 deg crease threshold (`station/density.py`,
    INV-070). Breaking the profile into rings puts a real dihedral at every ring,
    which is what a trunk with a root flare and a branch collar actually has.
    """
    n0 = len(v)
    for y, r in rings:
        for k in range(seg):
            a = math.tau * k / seg
            v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
    t0 = len(t)
    for i in range(len(rings) - 1):
        lo, hi = n0 + i * seg, n0 + (i + 1) * seg
        for k in range(seg):
            k2 = (k + 1) % seg
            t += [(lo + k, lo + k2, hi + k2), (lo + k, hi + k2, hi + k)]
    if close_top:
        c = len(v)
        y, r = rings[-1]
        v.append((cx, y, cz))
        top = n0 + (len(rings) - 1) * seg
        for k in range(seg):
            t.append((c, top + k, top + (k + 1) % seg))
    g.append((name, t0, len(t)))
    return v, t, g


def _limb(v, t, g, name, p0, p1, r0, r1, seg=6):
    """A tapered prism between two ARBITRARY points.

    `_taper` builds rings that all share one axis, which is right for a trunk and
    wrong for a branch: called with one centre it produces a vertical stub at the
    trunk while the foliage sits offset, and the canopy floats with nothing
    holding it up. That is what the first version of `tree()` did, and no metric
    caught it -- the line density was fine, the triangles were real, and only the
    render showed a tree in three disconnected pieces. This sweeps a section
    along the actual limb direction so the collar creases against the trunk at
    one end and enters the foliage mass at the other.
    """
    ax = tuple(b - a for a, b in zip(p0, p1))
    ln = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = tuple(c / ln for c in ax)
    # Any vector not parallel to the axis, then Gram-Schmidt.
    tmp = (0.0, 0.0, 1.0) if abs(ax[1]) > 0.9 else (0.0, 1.0, 0.0)
    d = sum(a * b for a, b in zip(tmp, ax))
    u = tuple(a - d * b for a, b in zip(tmp, ax))
    un = math.sqrt(sum(c * c for c in u)) or 1.0
    u = tuple(c / un for c in u)
    w = (ax[1] * u[2] - ax[2] * u[1], ax[2] * u[0] - ax[0] * u[2],
         ax[0] * u[1] - ax[1] * u[0])
    n0 = len(v)
    for pt, r in ((p0, r0), (p1, r1)):
        for k in range(seg):
            a = math.tau * k / seg
            cs, sn = math.cos(a) * r, math.sin(a) * r
            v.append(tuple(pt[i] + u[i] * cs + w[i] * sn for i in range(3)))
    t0 = len(t)
    for k in range(seg):
        k2 = (k + 1) % seg
        t += [(n0 + k, n0 + k2, n0 + seg + k2),
              (n0 + k, n0 + seg + k2, n0 + seg + k)]
    g.append((name, t0, len(t)))
    return v, t, g


def _lobe(v, t, g, name, cx, cy, cz, r, seg=8, stacks=4, squash=0.82):
    """One faceted foliage mass. Deliberately faceted, not smooth.

    A canopy modelled as ONE smooth ellipsoid reads as a balloon and, worse,
    draws almost no line: adjacent facets of a sphere at this segment count sit
    under the crease threshold. Several overlapping lobes give a real silhouette
    AND real creases where they intersect, which is what makes a tree read as
    foliage rather than as a solid.
    """
    n0 = len(v)
    for i in range(1, stacks):
        phi = math.pi * i / stacks
        ry, rr = math.cos(phi) * r * squash, math.sin(phi) * r
        for k in range(seg):
            a = math.tau * k / seg
            v.append((cx + rr * math.cos(a), cy + ry, cz + rr * math.sin(a)))
    top, bot = len(v), len(v) + 1
    v += [(cx, cy + r * squash, cz), (cx, cy - r * squash, cz)]
    t0 = len(t)
    for i in range(stacks - 2):
        lo, hi = n0 + i * seg, n0 + (i + 1) * seg
        for k in range(seg):
            k2 = (k + 1) % seg
            t += [(lo + k, hi + k2, lo + k2), (lo + k, hi + k, hi + k2)]
    ring_hi, ring_lo = n0, n0 + (stacks - 2) * seg
    for k in range(seg):
        k2 = (k + 1) % seg
        t.append((top, ring_hi + k2, ring_hi + k))
        t.append((bot, ring_lo + k, ring_lo + k2))
    g.append((name, t0, len(t)))
    return v, t, g


# ---------------------------------------------------------------------------
# Vector helpers. Three lines each and used by `_sweep` below; kept local so
# this module still imports nothing but `interior` and `drum_ground`.
# ---------------------------------------------------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1.0 / n)


def _rot_min(a, b, u):
    """`u` carried through the minimal rotation taking unit `a` to unit `b`.

    PARALLEL TRANSPORT, and it is the reason `_sweep` exists beside `_limb`.
    `_limb` picks its section frame from a fixed reference vector, which is
    correct for ONE straight segment and wrong for a polyline: the frame flips
    by up to 90 degrees between consecutive segments of a bending branch and
    the tube twists visibly where they meet. Rodrigues on the minimal rotation
    keeps the section continuous, so a branch that bends stays a branch.
    """
    ax = _cross(a, b)
    s = math.sqrt(_dot(ax, ax))
    c = _dot(a, b)
    if s < 1e-9:
        return u if c > 0.0 else _mul(u, -1.0)
    k = _mul(ax, 1.0 / s)
    ang = math.atan2(s, c)
    cs, sn = math.cos(ang), math.sin(ang)
    return _add(_add(_mul(u, cs), _mul(_cross(k, u), sn)),
                _mul(k, _dot(k, u) * (1.0 - cs)))


def _sweep(v, t, g, name, pts, radii, seg=8, flute=0.0, flutes=FLUTE_N,
           phase=0.0, flat=1.0):
    """Sweep a section along a polyline of arbitrary points.

    `_taper` sweeps rings that share one vertical axis; `_limb` sweeps one
    straight segment between two points. A tree is neither: a limb bends, and
    the bend is where the eye reads a branch as a branch rather than as a rod.

    THREE THINGS THIS DOES THAT NEITHER OF THOSE CAN, each answering a defect
    read off `scratchpad/frames/before-tree5.png`:

      * `flute` modulates the radius round the section, so the trunk's section
        is not a circle. A smooth cylinder draws exactly two lines at any
        segment count -- its silhouette edges -- because every lateral facet
        edge sits under `density.py`'s 3.24 deg crease threshold. Seven ridges
        at 11% of the radius put a real dihedral on every one of them, which is
        what bark is and is why a trunk stops reading as a black spike.
      * `flat` scales the section on one axis, which turns the same code into a
        palm frond: a 4-gon section flattened to 0.17 IS a blade with a midrib.
      * the frame is parallel-transported, so a bough does not twist at a bend.
    """
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            d = _sub(pts[1], pts[0])
        elif i == n - 1:
            d = _sub(pts[-1], pts[-2])
        else:
            d = _add(_norm(_sub(pts[i], pts[i - 1])),
                     _norm(_sub(pts[i + 1], pts[i])))
        tans.append(_norm(d))
    ref = (0.0, 0.0, 1.0) if abs(tans[0][1]) > 0.9 else (0.0, 1.0, 0.0)
    u = _norm(_sub(ref, _mul(tans[0], _dot(ref, tans[0]))))
    n0 = len(v)
    for i in range(n):
        if i > 0:
            u = _norm(_rot_min(tans[i - 1], tans[i], u))
        w = _cross(tans[i], u)
        r = radii[i]
        for k in range(seg):
            a = math.tau * k / seg
            rr = r * (1.0 + flute * math.cos(flutes * a + phase))
            cs, sn = math.cos(a) * rr, math.sin(a) * rr * flat
            v.append(tuple(pts[i][j] + u[j] * cs + w[j] * sn
                           for j in range(3)))
    t0 = len(t)
    for i in range(n - 1):
        lo, hi = n0 + i * seg, n0 + (i + 1) * seg
        for k in range(seg):
            k2 = (k + 1) % seg
            t += [(lo + k, lo + k2, hi + k2), (lo + k, hi + k2, hi + k)]
    g.append((name, t0, len(t)))
    return v, t, g


def _leaf_mass(v, t, g, name, centre, r, seed, lobes=LEAF_LOBES, seg=6,
               stacks=3):
    """A cluster of small lobes at a bough tip, NOT one lobe at the trunk.

    This is the whole difference between a tree and a lollipop and it is worth
    stating as a rule, because the old code already had several lobes and still
    rendered as one ball: **no foliage mass may be centred on the trunk axis,
    and no mass may be large enough to swallow its neighbours.** A crown lobe
    at 0.52-0.68 of the crown radius sitting 0.8-1.6 m from limb lobes of
    0.34-0.54 does exactly that. `_selftest` asserts both properties.
    """
    for j in range(lobes):
        a = math.tau * (j + 0.5 * _u(seed, "lm", j)) / lobes
        tilt = -0.35 + 0.9 * _u(seed, "lt", j)
        # OFFSET UNDER RADIUS, DELIBERATELY, AND IT IS THE WHOLE READ. The
        # first version of this had lobes 0.42-0.72 r out carrying radii of
        # 0.62-0.92 r, so the masses only just touched, and
        # `scratchpad/frames/after-heroA.png` shows the result: a cluster of
        # dark dice hung on the branches with sky between them. Foliage reads
        # as foliage when neighbouring masses INTERSECT -- the crease where
        # two lobes cut each other is the line, and the union is the mass.
        off = r * (0.28 + 0.26 * _u(seed, "lo", j))
        rr = r * (0.80 + 0.34 * _u(seed, "lr", j))
        _lobe(v, t, g, name,
              centre[0] + off * math.cos(a),
              centre[1] + off * tilt,
              centre[2] + off * math.sin(a),
              rr, seg=seg, stacks=stacks,
              squash=0.74 + 0.26 * _u(seed, "ls", j))
    return v, t, g


def _tips(segs):
    """Ends of the skeleton that nothing else grows from.

    Computed from the segment list rather than tracked while building it, and
    the difference is not cosmetic: with `orders=1` BOTH segments of a limb
    carry order 1, so "the segments of the outermost order" includes the
    elbow, and foliage lands halfway along the branch. A tip is a p1 that is
    no segment's p0, at every order, which is the same statement one level up.
    """
    starts = {tuple(round(c, 6) for c in s[1]) for s in segs}
    return [s[2] for s in segs
            if tuple(round(c, 6) for c in s[2]) not in starts]


def _skeleton(seed, h, r0, fork, spread, rise, orders=BRANCH_ORDERS):
    """The branch structure, as data, before any triangle is spent on it.

    Returned as (order, p0, p1, r_start, r_end) so every level of detail draws
    the SAME tree and a coarser one is a subset rather than a different plant.
    That is the "culled sets are strict subsets" clause of PERFORMANCE 4,
    applied to a generator instead of to a mesh.
    """
    segs = []
    limbs = LIMBS_MIN + int((LIMBS_MAX - LIMBS_MIN + 1) * _u(seed, "nl"))
    limbs = min(limbs, LIMBS_MAX)
    for j in range(limbs):
        a = math.tau * (j + 0.30 * _u(seed, "la", j)) / limbs
        reach = spread * (0.60 + 0.40 * _u(seed, "lr", j))
        top = fork + rise * (0.55 + 0.45 * _u(seed, "lh", j))
        br = r0 * (0.34 + 0.14 * _u(seed, "lb", j))
        ex, ez = reach * math.cos(a), reach * math.sin(a)
        # A limb leaves the trunk steeply and flattens: the elbow is the crease
        # that reads as a branch. Two segments, so it has one.
        mid = (ex * 0.42, fork + (top - fork) * 0.68, ez * 0.42)
        end = (ex, top, ez)
        segs.append((1, (0.0, fork - 0.20, 0.0), mid, br * 1.7, br * 1.15))
        segs.append((1, mid, end, br * 1.15, br * 0.72))
        if orders < 2:
            continue
        boughs = BOUGHS_MIN + int(
            (BOUGHS_MAX - BOUGHS_MIN + 1) * _u(seed, "nb", j))
        boughs = min(boughs, BOUGHS_MAX)
        for k in range(boughs):
            b = a + (-0.55 + 1.1 * _u(seed, "ba", j, k))
            rr = spread * (0.30 + 0.34 * _u(seed, "br", j, k))
            tip = (ex + rr * math.cos(b),
                   top + rise * (0.10 + 0.26 * _u(seed, "bh", j, k)),
                   ez + rr * math.sin(b))
            segs.append((2, end, tip, br * 0.72, br * 0.42))
            if orders < 3:
                continue
            for m in range(2):
                c = b + (-0.8 + 1.6 * _u(seed, "ta", j, k, m))
                t2 = (tip[0] + rr * 0.34 * math.cos(c),
                      tip[1] + rise * 0.12 * (0.3 + _u(seed, "th", j, k, m)),
                      tip[2] + rr * 0.34 * math.sin(c))
                segs.append((3, tip, t2, br * 0.42, br * 0.20))
    return segs


# The ladder, as a table with its reasons, one row per level. Read across:
# how many branch orders exist, how many of them carry foliage, the trunk and
# branch section counts, how many lobes hang at a tip and how big they are.
#
# The two columns that decide everything are `orders` and `lobes`. Everything
# else is a section count and moves the cost by tens; those two move it by
# hundreds, and they are also what the eye reads -- a tree with one order of
# branching is a coat rack however finely it is tessellated.
#
# `foliage` is deliberately NOT always the outermost order. At level -1 the
# canopy hangs on the BOUGHS and the twigs project through it, because that is
# what you see standing under a real tree: bare twig ends against sky at the
# canopy edge. Putting three lobes on each of 25 twigs instead costs 1,800
# triangles for a mass the eye reads as one surface.
_TREE_LOD = {
    #        orders foliage trunk_seg rings br_seg lobes lobe_seg lobe_r
    -1:  dict(orders=3, foliage=2, tseg=12, rings=5, bseg=7, lobes=5,
              lseg=7, lstk=4, lscale=1.00),
    0:   dict(orders=1, foliage=1, tseg=TRUNK_SEG, rings=3, bseg=6, lobes=2,
              lseg=5, lstk=3, lscale=1.45),
    1:   dict(orders=1, foliage=1, tseg=6, rings=3, bseg=4, lobes=1,
              lseg=5, lstk=3, lscale=2.10),
    2:   dict(orders=1, foliage=1, tseg=5, rings=2, bseg=3, lobes=1,
              lseg=4, lstk=3, lscale=2.60),
    3:   dict(orders=0, foliage=0, tseg=4, rings=2, bseg=3, lobes=0,
              lseg=4, lstk=3, lscale=0.00),
}


def _broadleaf(seed, level, squat=False):
    """A rounded broadleaf (`garden.png`, `The Gardens.webp`) or, with `squat`,
    29a's broad flat-topped street tree on a clear stem."""
    lod = _TREE_LOD[level]
    v, t, g = [], [], []
    h = TREE_H_M * (0.75 + 0.5 * _u(seed, "th"))
    r0 = TRUNK_R_M * (0.85 + 0.3 * _u(seed, "tk"))
    crown = h * CROWN_FRAC * (0.85 + 0.30 * _u(seed, "cw"))
    if squat:
        h *= 0.80
        crown *= 1.45
        fork = h * 0.58
        rise = (h - fork) * 0.45
    else:
        fork = h * FORK_FRAC
        rise = h - fork
    rings = [(0.0, r0 * FLARE_K), (FLARE_H_M, r0),
             (fork * 0.45, r0 * 0.80), (fork * 0.80, r0 * 0.66),
             (fork, r0 * 0.58)]
    if lod["rings"] == 3:
        rings = [rings[0], rings[1], rings[-1]]
    elif lod["rings"] == 2:
        rings = [rings[0], rings[-1]]
    _sweep(v, t, g, "garden_trunk",
           [(0.0, y, 0.0) for y, _r in rings], [r for _y, r in rings],
           seg=lod["tseg"], flute=(FLUTE_D if level < 0 else 0.0),
           phase=_u(seed, "ph") * math.tau)
    if not lod["orders"]:
        _lobe(v, t, g, "garden_foliage", 0.0, fork + rise * 0.55, 0.0,
              crown * 0.95, seg=lod["lseg"], stacks=3, squash=0.80)
        return v, t, g
    segs = _skeleton(seed, h, r0, fork, crown, rise, orders=lod["orders"])
    for order, p0, p1, ra, rb in segs:
        _sweep(v, t, g, "garden_branch", [p0, p1], [ra, rb],
               seg=max(3, lod["bseg"] - order + 1))
    carried = [s for s in segs if s[0] <= lod["foliage"]]
    lr = crown * LEAF_R_FRAC * lod["lscale"]
    for i, tip in enumerate(_tips(carried)):
        _leaf_mass(v, t, g, "garden_foliage", tip, lr, f"{seed}/{i}",
                   lobes=lod["lobes"], seg=lod["lseg"], stacks=lod["lstk"])
    return v, t, g


def _palm(seed, level):
    """`The Gardens.webp`: palms lining the streets and the open ground.

    A palm is the one tree form whose silhouette is entirely in its crown, so
    the LOD chain cannot drop fronds the way it drops twigs -- it drops the
    SEGMENTS along each frond and the section count across it, and keeps the
    count, because five fronds is a different plant and eleven short ones is
    the same one further away.
    """
    v, t, g = [], [], []
    h = TREE_H_M * (1.05 + 0.55 * _u(seed, "ph"))
    r0 = TRUNK_R_M * (0.62 + 0.22 * _u(seed, "pk"))
    lean = -0.10 + 0.20 * _u(seed, "pl")
    scars = {-1: PALM_SCARS, 0: 4, 1: 3, 2: 2, 3: 1}[level]
    seg_t = {-1: 10, 0: 6, 1: 5, 2: 4, 3: 3}[level]
    pts, radii = [], []
    for i in range(scars + 1):
        f = i / scars
        pts.append((lean * h * f * f, h * f, 0.0))
        # Each scar is a step in the radius: a palm's stem is a stack of leaf
        # bases, and the step is the crease. A smooth taper draws nothing.
        step = 1.0 - 0.30 * f + (0.055 if i % 2 else 0.0)
        radii.append(r0 * step)
    _sweep(v, t, g, "garden_trunk", pts, radii, seg=seg_t,
           flute=(0.06 if level < 0 else 0.0), flutes=9)
    top = pts[-1]
    if level >= 3:
        _lobe(v, t, g, "garden_foliage", top[0], top[1] + 0.4, top[2],
              h * 0.20, seg=4, stacks=3, squash=0.55)
        return v, t, g
    n = FROND_COUNT[0] + int((FROND_COUNT[1] - FROND_COUNT[0] + 1)
                             * _u(seed, "pf"))
    n = min(n, FROND_COUNT[1])
    fl = h * (0.26 + 0.08 * _u(seed, "fl"))
    steps = {-1: 5, 0: 2, 1: 2, 2: 1}[level]
    fseg = {-1: 5, 0: FROND_SEG, 1: 3, 2: 3}[level]
    for j in range(n):
        a = math.tau * (j + 0.30 * _u(seed, "fa", j)) / n
        droop = 0.55 + 0.55 * _u(seed, "fd", j)
        rise = 0.55 - 0.30 * droop
        pts = [top]
        radii = [fl * 0.055]
        for s in range(1, steps + 1):
            f = s / steps
            # Out, up, then over: a frond arches and falls.
            y = top[1] + fl * (rise * f - droop * f * f * 0.85)
            pts.append((top[0] + fl * f * math.cos(a), y,
                        top[2] + fl * f * math.sin(a)))
            radii.append(fl * (0.115 * (1.0 - 0.75 * f) + 0.012))
        _sweep(v, t, g, "garden_foliage", pts, radii, seg=fseg,
               flat=FROND_FLAT, phase=a)
    _lobe(v, t, g, "garden_foliage", top[0], top[1] + fl * 0.10, top[2],
          fl * 0.20, seg=max(4, fseg + 1), stacks=3, squash=0.75)
    return v, t, g


def _frustum(v, t, g, name, lo, hi, inset):
    """A box whose TOP footprint is `inset` smaller than its bottom.

    A batter is a wall that leans, and it is the cheapest way to stop a mass
    reading as a box: twelve triangles, and every vertical arris becomes a
    slope, so the silhouette is no longer four parallel lines. `The Gardens.webp`
    reads the settlement's large building as "three stacked glazed bands over a
    SOLID BATTERED BASE" -- the batter is in the reference and nothing built it.
    """
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    for i in (2, 3, 6, 7):                       # the four top corners
        x, y, z = v[n + i]
        v[n + i] = (x + (inset if x < (x0 + x1) / 2 else -inset), y,
                    z + (inset if z < (z0 + z1) / 2 else -inset))
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    g.append((name, t0, len(t)))
    return v, t, g


def _banded_tier(v, t, g, seed, x0, x1, z0, z1, y0, y1, storeys, panes):
    """One tier of a block: a recessed core with solid courses in front of it.

    HOW A WINDOW BAND IS MADE WITHOUT CUTTING A HOLE. `The Gardens.webp` reads
    the settlement as "continuous horizontal window banding -- rows of small
    bright rectangles in DARK RECESSED BANDS, giving strong horizontal
    striping", and the old block answered that with a box standing 6 cm PROUD
    of the facade. A proud band draws two lines and reads as a stripe painted
    on a wall, which is exactly what `docs/judge-4e-drum-half.png` called
    "white boxes with window-grid textures".

    A recess is the other way round and costs the same: build the mass as an
    inset CORE plus solid spandrel courses at the full footprint, and the slot
    left between two courses IS the band -- with a real reveal at its head and
    its cill, both at 90 degrees, both far above `density.py`'s 3.24 deg crease
    threshold. The panes then sit on the core's own face, inside the slot,
    where a lit window actually is.
    """
    core = BAND_RECESS_M
    _box(v, t, g, "garden_colonnade_core",
         (x0 + core, y0, z0 + core), (x1 - core, y1, z1 - core))
    sh = (y1 - y0) / storeys
    band = min(BAND_H_M, sh * 0.52)
    spandrel = sh - band
    for s in range(storeys):
        cy0 = y0 + s * sh
        _box(v, t, g, "garden_block", (x0, cy0, z0), (x1, cy0 + spandrel, z1))
    # The rows of small bright rectangles, on the core's face inside the slot.
    for s in range(storeys):
        wy = y0 + s * sh + spandrel + (band - PANE_H_M) * 0.5
        if wy + PANE_H_M > y1:
            break
        for (px0, px1, pz, axis) in ((x0, x1, z0 + core, "x"),
                                     (x0, x1, z1 - core, "x"),
                                     (z0, z1, x0 + core, "z"),
                                     (z0, z1, x1 - core, "z")):
            span = px1 - px0 - 1.2
            if span <= PANE_W_M:
                continue
            n = max(1, int(span / PANE_PITCH_M))
            if not panes:
                # One continuous lit strip instead of n panes: same slot, same
                # two reveal lines, a twelfth of the triangles.
                a0, a1 = px0 + 0.6, px1 - 0.6
                if axis == "x":
                    _box(v, t, g, "garden_window_band",
                         (a0, wy, pz - 0.06), (a1, wy + PANE_H_M, pz + 0.06))
                else:
                    _box(v, t, g, "garden_window_band",
                         (pz - 0.06, wy, a0), (pz + 0.06, wy + PANE_H_M, a1))
                continue
            for k in range(n):
                c = px0 + 0.6 + (span) * (k + 0.5) / n
                if axis == "x":
                    _box(v, t, g, "garden_window_band",
                         (c - PANE_W_M / 2, wy, pz - 0.06),
                         (c + PANE_W_M / 2, wy + PANE_H_M, pz + 0.06))
                else:
                    _box(v, t, g, "garden_window_band",
                         (pz - 0.06, wy, c - PANE_W_M / 2),
                         (pz + 0.06, wy + PANE_H_M, c + PANE_W_M / 2))
    return v, t, g


def block_form(seed):
    """Which massing this block takes. All three are read off one frame.

    `The Gardens.webp`, authority 1, is the only frame of the drum settlement
    at ground level, and it shows three things at once: stepped low-rise blocks
    of two to four storeys, "long low linear blocks with unbroken window
    strips", and L-plan ranges enclosing yards off the street grid. Mix is
    45 / 30 / 25 by eye over the legible half of that frame; overturned by any
    frame in which the town's plots can be counted.
    """
    x = _u(seed, "massing")
    if x < 0.45:
        return "terrace"
    if x < 0.75:
        return "bar"
    return "court"


def block_building(seed, level=0):
    """One low-rise garden block, terraced rather than towered (INV-455).

    WHAT THIS REPLACES, and it is the second rewrite of this function, which is
    the interesting part. Version one was a single `_box` plus three proud
    window bands -- 48 triangles -- and the owner called it a "shitty little
    cube". Version two (INV-072) put a plinth, pilasters, expressed slabs,
    recessed openings, cills, gutters, downpipes, balconies and roof plant on
    it: 1,000 triangles, twenty-one times the line, every gate green.

    AND `scratchpad/frames/before-tree5.png` STILL SHOWS A BOX. Twelve metres
    away on Forward+, it reads as a grey retaining wall with scratch lines on
    it. Trim does not change a silhouette, and "cubes" is a statement about
    silhouette. Version two answered a line-density metric; the owner was
    describing the mass.

    So this version changes the MASS, and every piece of it is in the
    reference. `talia-winters in gorgeous office.webp` (authority 1): "low wide
    grey settlement blocks, TERRACED rather than towered" -> tiers that step
    back, each capped by a cantilevered slab. `The Gardens.webp` (authority 1):
    "two to four storeys ... continuous horizontal window banding -- rows of
    small bright rectangles in dark recessed bands ... three stacked glazed
    bands over a SOLID BATTERED BASE ... long low linear blocks" -> the batter,
    the recessed band (see `_banded_tier`), and the low wing. `garden.png`:
    "cantilevered horizontal slab canopies ... wrapping the base in layered
    tiers", and a "deeply recessed arcade" at the ground floor.

    `level` follows `tree()`: 0 is `drum_dressing`'s LOD0 and its cost, -1 is
    the near field. The massing is at BOTH, because massing is what reads at
    distance; only the per-pane glazing, the cills, the balconies and the
    entrance are near-field.
    """
    v, t, g = [], [], []
    L = BLOCK_MIN_M[0] + _u(seed, "L") * (BLOCK_MAX_M[0] - BLOCK_MIN_M[0])
    W = BLOCK_MIN_M[1] + _u(seed, "W") * (BLOCK_MAX_M[1] - BLOCK_MIN_M[1])
    H = BLOCK_MIN_M[2] + _u(seed, "H") * (BLOCK_MAX_M[2] - BLOCK_MIN_M[2])
    # THE ENVELOPE IS DRAWN EXACTLY AS BEFORE, ON PURPOSE.
    # `drum_dressing.prototype_dims()` reads (L, W, H) back out of this
    # function to fit plots onto the drum's street grid, so these three `_u`
    # draws must stay in this order with these bounds or 708 town blocks move.
    # What changes below is the SHAPE inside that envelope, which is what the
    # owner's word "cubes" was about -- trim on a prism is still a prism.
    storeys = max(1, int(round(H / STOREY_M)))
    sh = H / storeys
    hero = level < 0
    form = block_form(seed)

    # How the storeys divide between tiers. A "bar" is one tier by definition
    # ("long low linear blocks with unbroken window strips"); the other two
    # step back, which is the massing `talia-winters in gorgeous office.webp`
    # calls "terraced rather than towered".
    want = 1 if form == "bar" else min(
        TIER_MAX, max(TIER_MIN, int(round(H / (STOREY_M * 2.0)))))
    per = [storeys // want] * want
    for k in range(storeys % want):
        per[k] += 1
    per = [p for p in per if p > 0]
    tiers = len(per)

    bx, bz = L / 2.0, W / 2.0
    # The battered base. A leaning wall is twelve triangles and it takes four
    # vertical arrises off the silhouette.
    _frustum(v, t, g, "garden_plinth",
             (-bx - BATTER_M, 0.0, -bz - BATTER_M),
             (bx + BATTER_M, min(BATTER_H_M, H * 0.5), bz + BATTER_M),
             BATTER_M)

    y = 0.0
    tx, tz = bx, bz
    for k, n_st in enumerate(per):
        y1 = y + n_st * sh
        _banded_tier(v, t, g, f"{seed}/t{k}", -tx, tx, -tz, tz, y, y1,
                     n_st, panes=hero)
        # The cantilevered slab that caps every tier: `garden.png`'s
        # "cantilevered horizontal slab canopies with rounded ends wrapping the
        # base in layered tiers", and the thing that makes a setback read as a
        # setback rather than as a change of width.
        _box(v, t, g, "garden_slab",
             (-tx - CORNICE_P_M, y1 - SLAB_T_M, -tz - CORNICE_P_M),
             (tx + CORNICE_P_M, y1, tz + CORNICE_P_M))
        if k == 0:
            # Pilasters express the structural bay on the base tier only:
            # above it the setback already breaks the wall.
            bays = max(2, int(round((2 * tx) / BAY_W_M)))
            for i in range(bays + 1):
                x = -tx + 2 * tx * i / bays
                for zs in (-1, 1):
                    _box(v, t, g, "garden_pilaster",
                         (x - PILASTER_W_M / 2, PLINTH_H_M, zs * tz),
                         (x + PILASTER_W_M / 2, y1 - SLAB_T_M,
                          zs * (tz + PILASTER_PROUD_M)))
        y = y1
        tx = max(2.0, tx - SETBACK_M)
        tz = max(1.6, tz - SETBACK_M)
    top_x, top_z = tx + SETBACK_M, tz + SETBACK_M

    # THE LOW WING. A rectangle in plan is a rectangle in silhouette from
    # every angle a player walks past it, and one attached lower mass is the
    # cheapest way out of that: `The Gardens.webp` reads the settlement as
    # blocks with "long low linear blocks" against them, and 29a's building
    # behind the park has a lower glazed range in front of its main mass.
    wings = {"terrace": ((0.0, 1.0),), "bar": ((0.0, 1.0), (0.0, -1.0)),
             "court": ((0.0, 1.0), (1.0, 0.0))}[form]
    for wx, wz in wings:
        wl = L * WING_FRAC * (0.8 + 0.35 * _u(seed, "wl", wx, wz))
        wd = min(WING_D_M, W * 0.75)
        wh = min(WING_H_M, H * 0.65)
        if wz:
            lo = (-wl / 2 + L * 0.10 * (_u(seed, "wo", wz) - 0.5),
                  0.0, wz * bz)
            hi = (lo[0] + wl, wh, wz * (bz + wd))
            lo, hi = ((lo[0], lo[1], min(lo[2], hi[2])),
                      (hi[0], hi[1], max(lo[2], hi[2])))
        else:
            wl = min(wl, W * 1.05)
            lo = (wx * bx, 0.0, -wl / 2)
            hi = (wx * (bx + wd), wh, wl / 2)
            lo, hi = ((min(lo[0], hi[0]), lo[1], lo[2]),
                      (max(lo[0], hi[0]), hi[1], hi[2]))
        _banded_tier(v, t, g, f"{seed}/w{wx}{wz}", lo[0], hi[0], lo[2], hi[2],
                     0.0, wh, max(1, int(round(wh / STOREY_M))), panes=hero)
        _box(v, t, g, "garden_slab",
             (lo[0] - CANOPY_T_M, wh, lo[2] - CANOPY_T_M),
             (hi[0] + CANOPY_T_M, wh + CANOPY_T_M, hi[2] + CANOPY_T_M))

    # Cornice, parapet and handrail over the topmost tier.
    _box(v, t, g, "garden_cornice",
         (-top_x - CORNICE_P_M, H - CORNICE_H_M, -top_z - CORNICE_P_M),
         (top_x + CORNICE_P_M, H, top_z + CORNICE_P_M))
    _box(v, t, g, "garden_parapet",
         (-top_x - CORNICE_P_M, H, -top_z - CORNICE_P_M),
         (top_x + CORNICE_P_M, H + PARAPET_H_M, top_z + CORNICE_P_M))
    for zs in (-1, 1) if level < 0 else ():
        # A 50 mm handrail is 0.2 px at the level-0 switch distance of 113 m,
        # so it is near-field geometry by measurement rather than by taste.
        _box(v, t, g, "garden_rail",
             (-top_x - CORNICE_P_M, H + PARAPET_H_M,
              zs * (top_z + CORNICE_P_M) - RAIL_T_M / 2),
             (top_x + CORNICE_P_M, H + PARAPET_H_M + RAIL_T_M,
              zs * (top_z + CORNICE_P_M) + RAIL_T_M / 2))
    for j in range(2 + int(2 * _u(seed, "plant"))):
        px = -top_x * 0.6 + 1.2 * top_x * _u(seed, "px", j)
        pz = -top_z * 0.5 + 1.0 * top_z * _u(seed, "pz", j)
        pw = 0.8 + 1.4 * _u(seed, "pw", j)
        ph = 0.7 + 1.3 * _u(seed, "ph", j)
        _box(v, t, g, "garden_roof_plant",
             (px - pw / 2, H, pz - pw / 2), (px + pw / 2, H + ph, pz + pw / 2))

    # SERVICES. These are where a facade earns its line cheaply, and the
    # arithmetic is worth keeping because it decided the design: a six-sided
    # downpipe 8 m tall is 24 triangles and lays 48 m of visible line -- 2 m
    # per triangle, against 0.17 for the panel-relief grid `density.py`'s bound
    # is derived from. Long thin prisms are twelve times the yield.
    for zs in (-1, 1):
        _box(v, t, g, "garden_gutter",
             (-bx, per[0] * sh - SLAB_T_M - GUTTER_D_M,
              zs * (bz + CORNICE_P_M)),
             (bx, per[0] * sh - SLAB_T_M,
              zs * (bz + CORNICE_P_M + GUTTER_D_M)))
        n_pipe = DOWNPIPES_PER_FACE if level < 0 else 3
        for i in range(n_pipe):
            x = -bx * 0.9 + 1.8 * bx * i / max(1, n_pipe - 1)
            _taper(v, t, g, "garden_downpipe", x,
                   zs * (bz + PILASTER_PROUD_M + PIPE_R_M),
                   [(0.0, PIPE_R_M), (per[0] * sh - SLAB_T_M, PIPE_R_M)],
                   seg=6, close_top=False)
    if not hero:
        return v, t, g, (L, W, H)

    # ------------------------------------------------------------------
    # LEVEL -1 ONLY: what a player standing on the pavement can reach.
    # ------------------------------------------------------------------
    # Continuous cill and head bands at every window slot, an entrance with a
    # slab canopy over it, a shopfront, and a balcony per upper storey. All of
    # it is under 0.4 m in section and none of it survives to 113 m, which is
    # exactly why it belongs at this level and nowhere else.
    y = 0.0
    tx, tz = bx, bz
    for k, n_st in enumerate(per):
        band = min(BAND_H_M, sh * 0.52)
        for s in range(n_st):
            y0 = y + s * sh + (sh - band)
            for zs in (-1, 1):
                for yy, nm in ((y0 - BAND_T_M, "garden_cill"),
                               (y0 + band, "garden_lintel")):
                    _box(v, t, g, nm,
                         (-tx, yy - BAND_T_M / 2, zs * tz),
                         (tx, yy + BAND_T_M / 2, zs * (tz + BAND_P_M)))
            if k == 0 and s == 0:
                continue
            for zs in (-1, 1):
                yb = y + s * sh
                _box(v, t, g, "garden_balcony",
                     (-tx * 0.62, yb - BALC_T_M, zs * tz),
                     (tx * 0.62, yb, zs * (tz + BALC_D_M)))
                for rk in range(BALC_RAILS):
                    ry = yb + BALC_RAIL_H_M * (rk + 1) / BALC_RAILS
                    _box(v, t, g, "garden_rail",
                         (-tx * 0.62, ry - RAIL_T_M / 2,
                          zs * (tz + BALC_D_M - RAIL_T_M)),
                         (tx * 0.62, ry + RAIL_T_M / 2,
                          zs * (tz + BALC_D_M)))
        y += n_st * sh
        tx = max(2.0, tx - SETBACK_M)
        tz = max(1.6, tz - SETBACK_M)
    # The entrance: a recessed shopfront under a cantilevered slab, with
    # mullions. `garden.png`'s ground floor is "a deeply recessed arcade of
    # tall narrow bronze-framed windows, grouped in threes and fours".
    ex = min(4.2, L * 0.3)
    _box(v, t, g, "garden_slab",
         (-ex - 0.9, PLINTH_H_M + 2.55, bz),
         (ex + 0.9, PLINTH_H_M + 2.55 + CANOPY_T_M, bz + CANOPY_D_M))
    _box(v, t, g, "garden_glazing",
         (-ex, PLINTH_H_M * 0.35, bz - REVEAL_M),
         (ex, PLINTH_H_M + 2.45, bz - REVEAL_M + 0.06))
    n_mul = max(3, int((2 * ex) / 1.15))
    for i in range(n_mul + 1):
        mx = -ex + 2 * ex * i / n_mul
        _box(v, t, g, "garden_mullion",
             (mx - GLAZE_MULLION_M / 2, PLINTH_H_M * 0.35, bz - REVEAL_M),
             (mx + GLAZE_MULLION_M / 2, PLINTH_H_M + 2.45, bz + 0.02))
    return v, t, g, (L, W, H)


def tree(seed, level=0, form="broadleaf"):
    """One tree, at one level of the drum's LOD ladder.

    `level` NUMBERS `drum_dressing.LOD_RATIOS` AND EXTENDS IT DOWNWARD.
    0 is that module's LOD0 (inside 113 m) and 1/2/3 its proxies; **-1 is the
    near-field level this session added**, for the 35 m inside which a player
    can see bark. The default is 0 and not -1, and that is a cross-module fact
    rather than a preference: `drum_dressing._tree_proto` calls `gd.tree(seed)`
    with no level for its own LOD0, and `LOD_SCALE_M = 113.0` was solved by
    bisection against `DRESSING_TRIS` at that cost, over 1,945 features, with
    the worst standing position landing at 119,868 of 120,000. Changing what
    the bare call costs moves that solve. `_selftest` asserts it has not.

    `form` is likewise opt-in, for a reason one level down: `drum_dressing`
    builds its OWN levels 1-3 for a tree and every one of them is a rounded
    broadleaf blob. A palm at LOD0 that pops into a broadleaf at 113 m is worse
    than a broadleaf at both, so the scatter keeps asking for the default and
    `townscape()` -- which owns its own whole ladder -- asks for the mix.

    WHAT THIS REPLACES, and the second answer is the one that matters. The
    first version was a 0.44 m box on a post, 30 triangles, and the owner
    called it "a sad excuse for a tree". The version that replaced it in
    session 3z had a tapered trunk, limbs with elbows and five overlapping
    foliage lobes -- and `scratchpad/frames/before-tree5.png`, taken 11 m away
    on Forward+, shows a FIVE-FACET GREEN BLOB ON A BLACK SPIKE. It was still
    a lollipop, and no gate in the project could say so, because every one of
    them measures line density or triangle count and a lollipop passes both.

    The cause is arithmetic and is written out at `CROWN_FRAC`: the height is
    drawn from a distribution and the canopy radius was the CONSTANT
    `TREE_R_M = 2.2`, so the taller half of the population got a 2.2 m crown
    on a 10 m stem. A rule replaces the constant, and `_selftest` asserts the
    ratio over the whole population rather than on the one that broke.
    """
    if form == "palm":
        return _palm(seed, level)
    return _broadleaf(seed, level, squat=(form == "umbrella"))


def tree_form(seed):
    """Which of the three authority-1 forms this seed's tree takes.

    The mix is 55 / 25 / 20 broadleaf / palm / umbrella. It is a reading of the
    two frames that show the settlement's planting rather than a preference:
    `The Gardens.webp` puts palms along every street and dark rounded
    broadleaves in the open ground and the foreground, at roughly one palm to
    two broadleaves; 29a's flat-topped street trees are four of the fifteen or
    so canopies legible in that frame. Overturned by any frame of the drum's
    planting at a scale where the crowns can be counted.
    """
    x = _u(seed, "form")
    if x < 0.55:
        return "broadleaf"
    if x < 0.80:
        return "palm"
    return "umbrella"


def place(verts, schema, profile, sector, angle_deg, z_m, ground_r=None,
          yaw=0.0):
    """Set locally-authored geometry on the drum surface.

    Local x is tangential, y is UP, z is along the station axis. On the drum UP
    IS INWARD, so local +y maps to DECREASING radius. Getting that backwards
    buries a building in the hull, which is the same failure that put the first
    drum camera five metres underground.

    The ground radius comes from the heightfield, so a building sits on the
    terrain it is actually standing on rather than on the nominal floor.

    `yaw` turns the piece about its own up axis before it is set down, in
    radians. A street frontage needs it: a block whose long face is meant to
    address the street is the wrong way round without it, and the alternative
    -- a second block generator with L and W swapped -- would be a second
    description of the same building.
    """
    if ground_r is None:
        ground_r = dg.terrain_sample(schema, profile, sector,
                                     angle_deg, z_m)["radius_m"]
    cs, sn = math.cos(yaw), math.sin(yaw)
    out = []
    for x, y, z in verts:
        if yaw:
            x, z = x * cs - z * sn, x * sn + z * cs
        r = ground_r - y                      # up is inward
        a = math.radians(angle_deg) + x / max(ground_r, 1e-9)
        out.append((r * math.cos(a), r * math.sin(a), z_m + z))
    return out


def hard_landscape(seed="garden"):
    """Paths, kerbs, hedges, steps, planters, benches and sail canopies.

    ALL SIX ARE AUTHORITY 1 and were simply never built.
    `reference/00-INDEX.md` on `Babylon_5_2-22_29a.jpg` extracts, verbatim:
    "paved winding paths in small setts; clipped hedges; a water feature /
    cascade against a planted bank; a timber bench; a circular raised planter
    with a **red-brown coping**; **orange sail canopies** on masts". The cascade
    and the bank exist in `setting()`. The other five did not exist at all.

    WHY THIS IS ALSO THE CHEAPEST LINE ON THE STATION, which is worth writing
    down because it is not obvious. `station/density.py` measures metres of
    visible line per m2 of surface. A kerb is a 0.15 x 0.12 m section running 20
    metres: twelve triangles, and it lays down two arris lines twenty metres long
    -- about 3.3 m of line per triangle. A panel-relief grid, which is what the
    metric's own budget bound is derived from, yields e/6 -- about 0.17 m per
    triangle at a 1 m pitch, twenty times worse. Long thin objects are how a
    landscape earns its detail floor, and they are also simply what a garden has.
    """
    v, t, g = [], [], []
    hl, hw = TERRACE_L_M / 2, TERRACE_W_M / 2

    # Kerbed paths: one spine along the terrace, ribs off it at path pitch.
    def kerbed(x0, z0, x1, z1, w):
        _box(v, t, g, "garden_paving",
             (min(x0, x1) - w / 2, -0.13, min(z0, z1) - w / 2),
             (max(x0, x1) + w / 2, -0.02, max(z0, z1) + w / 2))
        along_x = abs(x1 - x0) >= abs(z1 - z0)
        for side in (-1, 1):
            if along_x:
                zc = (z0 + z1) / 2 + side * (w / 2 + KERB_W_M / 2)
                _box(v, t, g, "garden_kerb",
                     (min(x0, x1) - w / 2, -0.13, zc - KERB_W_M / 2),
                     (max(x0, x1) + w / 2, KERB_H_M, zc + KERB_W_M / 2))
            else:
                xc = (x0 + x1) / 2 + side * (w / 2 + KERB_W_M / 2)
                _box(v, t, g, "garden_kerb",
                     (xc - KERB_W_M / 2, -0.13, min(z0, z1) - w / 2),
                     (xc + KERB_W_M / 2, KERB_H_M, max(z0, z1) + w / 2))

    kerbed(-hl + 1.0, 0.0, hl - 1.0, 0.0, PATH_W_M)
    ribs = max(2, int((2 * hw) / PATH_PITCH_M))
    for i in range(ribs):
        z = -hw + PATH_PITCH_M * (i + 0.5)
        if abs(z) < PATH_W_M:
            continue
        x = -hl + 4.0 + (2 * hl - 8.0) * _u(seed, "rib", i)
        kerbed(x, 0.0, x, z, PATH_W_M * 0.7)

    # Clipped hedges, in runs along the spine.
    for i in range(HEDGE_RUNS):
        x0 = -hl + 2.0 + (2 * hl - 4.0) * _u(seed, "hx", i)
        ln = HEDGE_MIN_M + (HEDGE_MAX_M - HEDGE_MIN_M) * _u(seed, "hl", i)
        zs = 1.0 if _u(seed, "hs", i) > 0.5 else -1.0
        z = zs * (PATH_W_M + 0.9 + 2.5 * _u(seed, "hz", i))
        _box(v, t, g, "garden_hedge",
             (x0, -0.05, z - HEDGE_W_M / 2),
             (min(x0 + ln, hl - 1.0), HEDGE_H_M, z + HEDGE_W_M / 2))

    # Terrace steps down to the lawn: each tread is two long lines.
    for i in range(STEP_COUNT):
        y = -0.15 - i * STEP_RISE_M
        invade = (i + 1) * STEP_GOING_M
        _box(v, t, g, "garden_stair_accent",
             (hl - STEP_RUN_M, y - STEP_RISE_M, -STEP_W_M / 2 - invade * 0.15),
             (hl, y, STEP_W_M / 2 + invade * 0.15))

    # The circular raised planter with its red-brown coping.
    cx, cz = -hl + PLANTER_R_M + 6.0, -hw + PLANTER_R_M + 3.0
    _drum(v, t, g, "garden_planter", cx, cz, -0.10, PLANTER_H_M,
          PLANTER_R_M, seg=PLANTER_SEG, cap=False)
    _drum(v, t, g, "garden_pool_coping", cx, cz, PLANTER_H_M,
          PLANTER_H_M + PLANTER_COPE_M, PLANTER_R_M + PLANTER_COPE_M,
          seg=PLANTER_SEG, cap=True)

    # Benches: a slatted seat is a stack of long lines for very few triangles.
    for i in range(BENCHES):
        bx = -hl + 3.0 + (2 * hl - 6.0) * _u(seed, "bx", i)
        bz = (1.0 if _u(seed, "bs", i) > 0.5 else -1.0) * (PATH_W_M + 0.75)
        for k in range(BENCH_SLATS):
            zo = bz + (k - (BENCH_SLATS - 1) / 2) * BENCH_SLAT_P_M
            _box(v, t, g, "garden_bench",
                 (bx - BENCH_L_M / 2, BENCH_H_M - 0.06, zo - BENCH_SLAT_W_M / 2),
                 (bx + BENCH_L_M / 2, BENCH_H_M, zo + BENCH_SLAT_W_M / 2))
        for side in (-1, 1):
            _box(v, t, g, "garden_bench",
                 (bx + side * BENCH_L_M / 2 - 0.06, 0.0, bz - 0.22),
                 (bx + side * BENCH_L_M / 2 + 0.06, BENCH_H_M - 0.06, bz + 0.22))

    # Lamp columns along the spine. A column is a thin prism: cheap line, and a
    # garden path at 250,000-population density has to be lit anyway.
    lamps = max(2, int((2 * hl) / LAMP_PITCH_M))
    for i in range(lamps):
        lx = -hl + LAMP_PITCH_M * (i + 0.5)
        lz = (1.0 if i % 2 else -1.0) * (PATH_W_M / 2 + KERB_W_M + 0.35)
        _taper(v, t, g, "garden_lamp_column", lx, lz,
               [(0.0, LAMP_R_M * 1.6), (0.35, LAMP_R_M),
                (LAMP_H_M, LAMP_R_M * 0.8)], seg=6, close_top=False)
        _box(v, t, g, "garden_lamp_head",
             (lx - LAMP_HEAD_M / 2, LAMP_H_M, lz - LAMP_HEAD_M / 2),
             (lx + LAMP_HEAD_M / 2, LAMP_H_M + 0.16, lz + LAMP_HEAD_M / 2))

    # Handrails to the terrace steps: two long runs and their standards.
    for side in (-1, 1):
        zr = side * (STEP_W_M / 2 + 0.25)
        _box(v, t, g, "garden_rail",
             (hl - STEP_RUN_M, RAIL_H_M - RAIL_T_M, zr - RAIL_T_M / 2),
             (hl + 0.4, RAIL_H_M, zr + RAIL_T_M / 2))
        for k in range(3):
            sx = hl - STEP_RUN_M + (STEP_RUN_M + 0.4) * k / 2
            _box(v, t, g, "garden_rail",
                 (sx - RAIL_T_M / 2, 0.0, zr - RAIL_T_M / 2),
                 (sx + RAIL_T_M / 2, RAIL_H_M, zr + RAIL_T_M / 2))

    # FIELD BOUNDARIES AND TERRACE EDGING. `reference/00-INDEX.md` on
    # `Babylon_5_2-22_33a.jpg` reads the drum wall as "landscape with roads and
    # field boundaries" -- the boundaries are in the reference and were never
    # built. They are also the highest-yield geometry in this module by a wide
    # margin: a 60 m dwarf wall is twelve triangles and lays four sixty-metre
    # lines, about 20 m of line per triangle, because line scales with LENGTH and
    # triangle count does not.
    for i in range(BOUNDARIES):
        bz = -hw + 2 * hw * (i + 0.5) / BOUNDARIES
        x0 = -hl + (2 * hl) * 0.08 * _u(seed, "wx", i)
        ln = (2 * hl) * (0.45 + 0.5 * _u(seed, "wl", i))
        if abs(bz) < PATH_W_M + 1.5:
            continue
        _box(v, t, g, "garden_boundary",
             (x0, -0.05, bz - BOUNDARY_W_M / 2),
             (min(x0 + ln, hl), BOUNDARY_H_M, bz + BOUNDARY_W_M / 2))
    # Terrace and lawn edging: four continuous runs each.
    for (ex0, ez0, ex1, ez1) in ((-hl, -hw, hl, -hw), (-hl, hw, hl, hw),
                                 (-hl, -hw, -hl, hw), (hl, -hw, hl, hw)):
        _box(v, t, g, "garden_kerb",
             (min(ex0, ex1) - KERB_W_M, -0.16, min(ez0, ez1) - KERB_W_M),
             (max(ex0, ex1) + KERB_W_M, KERB_H_M, max(ez0, ez1) + KERB_W_M))

    # THE GROUND ITSELF. After the buildings and the planting were rebuilt the
    # module still sat at 80.9% of its floor, and the reason is arithmetic: the
    # townscape's 39,193 m2 is nearly all GROUND, and a flat plane carries no
    # line at any triangle count. Every object added above raises the numerator
    # and the ground raises only the denominator.
    #
    # What a real settlement floor has, and 29a shows: paths are laid in bays
    # with expansion joints, planting beds are edged, and service runs are
    # covered by trench lids. All three are grooves and upstands -- continuous,
    # thin, and the cheapest line on the station.
    # Bay joints BOTH WAYS across the whole terrace, not only the spine. A slab
    # field is laid in bays; the joints are what stops 39,000 m2 of ground being
    # a single flat plane that carries no line at any triangle count.
    for i in range(int((2 * hl) / JOINT_PITCH_M)):
        jx = -hl + JOINT_PITCH_M * (i + 0.5)
        _box(v, t, g, "garden_paving_joint",
             (jx - JOINT_W_M / 2, -0.13, -hw), (jx + JOINT_W_M / 2, -0.105, hw))
    for i in range(int((2 * hw) / JOINT_PITCH_M)):
        jz = -hw + JOINT_PITCH_M * (i + 0.5)
        _box(v, t, g, "garden_paving_joint",
             (-hl, -0.13, jz - JOINT_W_M / 2), (hl, -0.105, jz + JOINT_W_M / 2))
    for i in range(BEDS):
        bx = -hl + 3.0 + (2 * hl - 6.0) * _u(seed, "bdx", i)
        bz = (1.0 if _u(seed, "bds", i) > 0.5 else -1.0) * (
            PATH_W_M + 2.0 + 6.0 * _u(seed, "bdz", i))
        bl = BED_MIN_M + (BED_MAX_M - BED_MIN_M) * _u(seed, "bdl", i)
        bw = BED_MIN_M * 0.55 + BED_MIN_M * 0.5 * _u(seed, "bdw", i)
        for (ex0, ez0, ex1, ez1) in ((bx, bz - bw / 2, bx + bl, bz - bw / 2),
                                     (bx, bz + bw / 2, bx + bl, bz + bw / 2),
                                     (bx, bz - bw / 2, bx, bz + bw / 2),
                                     (bx + bl, bz - bw / 2, bx + bl,
                                      bz + bw / 2)):
            _box(v, t, g, "garden_bed_edge",
                 (min(ex0, ex1) - BED_EDGE_M, -0.10, min(ez0, ez1) - BED_EDGE_M),
                 (max(ex0, ex1) + BED_EDGE_M, BED_EDGE_H_M,
                  max(ez0, ez1) + BED_EDGE_M))
    for i in range(TRENCHES):
        tzz = -hw + 2 * hw * (i + 0.5) / TRENCHES
        if abs(tzz) < PATH_W_M + 1.0:
            continue
        for k in range(2):
            zo = tzz + (k - 0.5) * TRENCH_W_M
            _box(v, t, g, "garden_trench_lid",
                 (-hl + 2.0, -0.12, zo - TRENCH_LIP_M / 2),
                 (hl - 2.0, -0.06, zo + TRENCH_LIP_M / 2))

    # A PERGOLA over the spine. Long beams, and 29a's setting is a designed
    # civic landscape rather than a park -- the colonnade of `civic_landmark()`
    # is the same language. Cheap line for a real object.
    posts = max(2, int((2 * hl - 8.0) / PERGOLA_BAY_M))
    for i in range(posts + 1):
        px = -hl + 4.0 + (2 * hl - 8.0) * i / posts
        for side in (-1, 1):
            pz = side * (PATH_W_M / 2 + 1.1)
            _taper(v, t, g, "garden_colonnade", px, pz,
                   [(0.0, PERGOLA_R_M * 1.3), (0.3, PERGOLA_R_M),
                    (PERGOLA_H_M, PERGOLA_R_M)], seg=6, close_top=False)
        # Cross beam over the path at every bay.
        _box(v, t, g, "garden_colonnade_core",
             (px - PERGOLA_R_M, PERGOLA_H_M, -PATH_W_M / 2 - 1.2),
             (px + PERGOLA_R_M, PERGOLA_H_M + PERGOLA_B_M,
              PATH_W_M / 2 + 1.2))
    for side in (-1, 1):
        # The two longitudinal beams the cross beams sit on.
        _box(v, t, g, "garden_colonnade_core",
             (-hl + 4.0, PERGOLA_H_M + PERGOLA_B_M,
              side * (PATH_W_M / 2 + 1.1) - PERGOLA_R_M),
             (hl - 4.0, PERGOLA_H_M + PERGOLA_B_M * 1.8,
              side * (PATH_W_M / 2 + 1.1) + PERGOLA_R_M))

    # THE SURFACE TRANSIT TRACK. 29a: "a streamlined green-and-white transit car
    # on a track at the upper right". Built as rails ON SLEEPERS with supports
    # rather than as two long prisms: a single 250 m rail would hand the density
    # metric an enormous line length for 24 triangles, and a number obtained that
    # way says nothing about what a viewer sees. `station/density.py` would
    # discount it anyway at the composing distance -- a 5 cm rail is sub-pixel --
    # but building it honestly is cheaper than arguing about it.
    tz = hw - TRACK_OFFSET_M
    sleepers = max(2, int((2 * hl) / SLEEPER_PITCH_M))
    for i in range(sleepers):
        sx = -hl + SLEEPER_PITCH_M * (i + 0.5)
        _box(v, t, g, "garden_sleeper",
             (sx - SLEEPER_W_M / 2, TRACK_H_M - SLEEPER_T_M,
              tz - TRACK_GAUGE_M / 2 - 0.25),
             (sx + SLEEPER_W_M / 2, TRACK_H_M,
              tz + TRACK_GAUGE_M / 2 + 0.25))
        if i % 3 == 0:
            _taper(v, t, g, "garden_track_pier", sx, tz,
                   [(0.0, 0.22), (TRACK_H_M - SLEEPER_T_M, 0.16)],
                   seg=6, close_top=False)
    for side in (-1, 1):
        for i in range(sleepers):
            x0 = -hl + SLEEPER_PITCH_M * i
            _box(v, t, g, "garden_rail",
                 (x0, TRACK_H_M,
                  tz + side * TRACK_GAUGE_M / 2 - RAIL_T_M),
                 (x0 + SLEEPER_PITCH_M, TRACK_H_M + RAIL_T_M * 1.6,
                  tz + side * TRACK_GAUGE_M / 2 + RAIL_T_M))

    # Sail canopies on masts -- the orange sails of 29a.
    for i in range(SAILS):
        sx = -hl + 8.0 + (2 * hl - 16.0) * _u(seed, "sx", i)
        sz = (1.0 if _u(seed, "ss", i) > 0.5 else -1.0) * (PATH_W_M + 3.2)
        for side in (-1, 1):
            _box(v, t, g, "garden_flagpole",
                 (sx + side * SAIL_W_M / 2 - MAST_R_M, 0.0, sz - MAST_R_M),
                 (sx + side * SAIL_W_M / 2 + MAST_R_M, MAST_H_M, sz + MAST_R_M))
        _box(v, t, g, "garden_canopy",
             (sx - SAIL_W_M / 2, MAST_H_M - 0.10, sz - SAIL_D_M / 2),
             (sx + SAIL_W_M / 2, MAST_H_M, sz + SAIL_D_M / 2))
    return v, t, g


# ---------------------------------------------------------------------------
# THE GROUND A PLAYER IS STANDING ON
# ---------------------------------------------------------------------------
# The switch distances are `drum_dressing.LOD_RATIOS * LOD_SCALE_M` with the
# near level prepended. They are restated rather than imported because
# `drum_dressing` imports THIS module and the cycle would be import-time;
# `_selftest` asserts the two agree, so the copy cannot drift silently.
LOD_SWITCH_M = (NEAR_SWITCH_M, 113.0, 361.6, 1017.0)

# What the whole townscape may cost. DERIVED, and the derivation is a
# measurement rather than an allocation: the drum scene at the garden camera
# built 263,384 triangles against `budget.DRUM["visible_set_tris"]` of 300,000
# (the render log of `scratchpad/frames/before-tree5.png`), of which this
# module was 22,620. So the room is 300,000 - 263,384 + 22,620 = 59,236, and
# this sits under it with 4,236 of margin for the drum's own growth.
# `_selftest` measures the sum at the garden eye rather than trusting the
# subtraction, and it FAILS if the near field is grown past it. -- INV-457
TOWNSCAPE_TRIS = 55_000

# The near town, INV-457. `The Gardens.webp` reads the settlement as "a dense
# orthogonal STREET GRID"; the old townscape scattered twelve blocks over 218 m
# of arc and 260 m of axis, i.e. one building per 4,400 m2, which is not a town
# and is why the near field of `docs/engine-4q-drum-dressed.png` is empty.
STREET_PITCH_M = 38.0               # centre to centre, across the plots
CROSS_PITCH_M = 52.0                # centre to centre, along them
STREET_W_M = 9.0
NEAR_TOWN_M = 68.0                  # how far the grid runs from the terrace
STREET_TREE_PITCH_M = 26.0
HERO_TREES = 6                      # how many get the -1 level. See the budget.
CONE_H_M = (7.4, 4.2)               # 29a's orange cones, tallest and shortest
CONE_R_M = 0.62
CONES = 5


def _lod_for(d_m):
    """Which level a feature `d_m` from the eye is built at."""
    for i, s in enumerate(LOD_SWITCH_M):
        if d_m < s:
            return i - 1
    return len(LOD_SWITCH_M) - 1


def ground_cover(seed, eye=(0.0, 0.0), radius=NEAR_SWITCH_M, avoid=()):
    """Tussock, scrub and sett courses on the ground within reach of the eye.

    THE DEFECT THIS ANSWERS is in STATE.md 24.4b and in two frames:
    "the parcel boundary is still a hard straight edge where green meets tan in
    the foreground", and `before-tree5.png`'s flat green strip against flat
    paving. Nothing stands on either, at the one distance where a player would
    see that nothing does.

    WHY IT IS NOT SOLVED BY MORE SCATTER, which is the thing `drum_dressing`
    already does well: that module's LOD chain resolves DETAIL by distance and
    its density is uniform, so the same 1,945 features that read as a landscape
    at 500 m read as nothing at 20 m. Ground cover is the opposite shape --
    features that exist ONLY inside `NEAR_SWITCH_M`, at a density that would be
    ruinous anywhere else. 212 tussocks over the 3,848 m2 inside 35 m is 3,400
    triangles; the same density over the drum's 4.5 million m2 would be 4
    million.

    `avoid` is a list of (x0, x1, z0, z1) rectangles -- paving, pool, building
    footprints -- because grass growing through a terrace is worse than bare
    terrace.
    """
    v, t, g = [], [], []
    ex, ez = eye

    def clear(x, z):
        return not any(x0 <= x <= x1 and z0 <= z <= z1
                       for x0, x1, z0, z1 in avoid)

    # A jittered lattice, not a random scatter: an even lattice reads as
    # confetti (session 2n's greebles) and pure noise clumps into holes. The
    # cell is sized from the wanted density, and each occupant is jittered
    # inside its own cell, so the spacing has a floor and no pattern.
    for name, per100, r0, lobes, seg in (
            ("tussock", TUSSOCK_PER_100M2, TUSSOCK_R_M, 1, 4),
            ("scrub", SCRUB_PER_100M2, SCRUB_R_M, 3, 5)):
        cell = math.sqrt(100.0 / per100)
        n = int(math.ceil(2 * radius / cell))
        for i in range(n):
            for j in range(n):
                x = ex - radius + cell * (i + _u(seed, name, "x", i, j))
                z = ez - radius + cell * (j + _u(seed, name, "z", i, j))
                if math.hypot(x - ex, z - ez) > radius or not clear(x, z):
                    continue
                rr = r0 * (0.7 + 0.7 * _u(seed, name, "r", i, j))
                for k in range(lobes):
                    a = math.tau * (k + _u(seed, name, "a", i, j, k)) / lobes
                    # A CLUMP, NOT A LATTICE POINT. One lobe per cell reads as
                    # a scattering of dark dice on flat grass, which is what
                    # `after-heroA.png` shows underfoot. Overlapping lobes at
                    # 0.38 of their own radius merge into a patch of scrub with
                    # a lumpy edge, for the same triangles.
                    off = rr * 0.38 * k
                    _lobe(v, t, g, "garden_hedge",
                          x + off * math.cos(a), rr * SCRUB_H_FRAC * 0.55,
                          z + off * math.sin(a),
                          rr * (0.75 + 0.4 * _u(seed, name, "s", i, j, k)),
                          seg=seg, stacks=3,
                          squash=SCRUB_H_FRAC)
    return v, t, g


def sett_courses(seed, x0, x1, z0, z1, eye=(0.0, 0.0), radius=10.0):
    """29a's "paved winding paths in small setts", as courses rather than setts.

    THE ARITHMETIC THAT DECIDED THE FORM. A 46 x 26 m terrace at the frame's
    0.42 m sett module is 6,780 setts; twelve triangles each is 81,000, which
    is more than the whole drum's remaining allowance for one floor. A COURSE
    -- one continuous strip 0.42 m wide standing 18 mm proud of its neighbour
    -- lays the same two lines down the whole terrace for twelve triangles, at
    0.6% of the cost, and it is also what a laid pavement is: setts are laid in
    courses and the course line is the one that survives to 10 m. Cross joints
    are then added only inside `radius`, where an individual sett is bigger
    than a pixel.
    """
    v, t, g = [], [], []
    ex, ez = eye
    n = int((z1 - z0) / COBBLE_M)
    for i in range(n):
        z = z0 + COBBLE_M * (i + 0.5)
        if i % 2:
            continue                      # every other course stands proud
        _box(v, t, g, "garden_paving",
             (x0, -0.02, z - COBBLE_M * 0.46),
             (x1, -0.02 + COBBLE_PROUD_M, z + COBBLE_M * 0.46))
    # Cross joints: the setts themselves, only where one is over a pixel.
    m = int(2 * radius / COBBLE_M)
    for i in range(m):
        x = ex - radius + COBBLE_M * (i + 0.5)
        if not x0 < x < x1:
            continue
        _box(v, t, g, "garden_paving_joint",
             (x - COBBLE_M * 0.08, -0.021,
              max(z0, ez - radius)),
             (x + COBBLE_M * 0.08, -0.021 + COBBLE_PROUD_M * 0.7,
              min(z1, ez + radius)))
    return v, t, g


def park_planting(seed, hl, hw):
    """29a's near-field planting: cones, slat retaining walls, massed shrub.

    Three things in that frame, all authority 1, none of them built:

      * "Four to five tall orange-vermilion tapered CONES stand on the upper
        terrace -- slender, ground-mounted, of decreasing height. They are the
        strongest colour accent in the frame and are a REPEATING CIVIC ELEMENT,
        not a one-off canopy."  The Garden's only saturated accent besides the
        landmark's stair, and the most distinctive silhouette in the frame.
      * "Terracing is retained by horizontal RED-BROWN TIMBER-SLAT WALLS."
        A slat wall is the cheapest line in this module -- four courses of
        12 triangles laying eight lines the length of the terrace -- and it is
        what stops the paving meeting the grass along a drawn edge.
      * "A circular raised planter with a red-brown coping", MASSED with
        flowering shrub. `hard_landscape` built the planter and left it empty,
        which is a stone ring with nothing in it.
    """
    v, t, g = [], [], []
    # The cones, in a file of decreasing height, as the frame shows them.
    for i in range(CONES):
        f = i / max(1, CONES - 1)
        h = CONE_H_M[0] + (CONE_H_M[1] - CONE_H_M[0]) * f
        cx = -hl + 6.0 + i * 3.1
        cz = -hw + 2.6
        _taper(v, t, g, "garden_stair_accent", cx, cz,
               [(0.0, CONE_R_M), (h * 0.18, CONE_R_M * 0.92),
                (h * 0.62, CONE_R_M * 0.52), (h, CONE_R_M * 0.10)],
               seg=8, close_top=True)
    # Slat retaining walls along both long edges of the terrace.
    for zs in (-1, 1):
        for k in range(4):
            y = -0.16 - k * 0.20
            _box(v, t, g, "garden_stair_accent",
                 (-hl, y, zs * hw - 0.09 - k * 0.035),
                 (hl, y + 0.15, zs * hw + 0.09 + k * 0.035))
    # The planter, massed. `hard_landscape` puts it at this centre.
    cx, cz = -hl + PLANTER_R_M + 6.0, -hw + PLANTER_R_M + 3.0
    for k in range(7):
        a = math.tau * k / 7.0
        off = PLANTER_R_M * (0.30 + 0.42 * _u(seed, "pl", k))
        _lobe(v, t, g, "garden_hedge",
              cx + off * math.cos(a),
              PLANTER_H_M + 0.42 + 0.22 * _u(seed, "ph", k),
              cz + off * math.sin(a),
              PLANTER_R_M * (0.34 + 0.16 * _u(seed, "pr", k)),
              seg=5, stacks=3, squash=0.72)
    return v, t, g


def townscape(schema, profile, sector=None, angle_deg=112.0, z_m=4900.0,
              blocks=12, trees=10, seed="garden", near=True):
    """The landmark, its setting, and a patch of the town around it."""
    if sector is None:
        sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    if not in_settlement(angle_deg):
        raise ValueError(f"{angle_deg} deg is not in a settlement band; "
                         f"bands are {settlement_arcs()}")

    V, T, G = [], [], []

    def emit(lv, lt, lg, a, z, yaw=0.0):
        off, t0 = len(V), len(T)
        V.extend(place(lv, schema, profile, sector, a, z, yaw=yaw))
        T.extend((p + off, q + off, r + off) for p, q, r in lt)
        G.extend((n, lo + t0, hi + t0) for n, lo, hi in lg)

    lv, lt, lg = setting()
    emit(lv, lt, lg, angle_deg, z_m)
    lv, lt, lg = hard_landscape(seed)
    emit(lv, lt, lg, angle_deg, z_m)
    lv, lt, lg = civic_landmark()
    emit(lv, lt, lg, angle_deg, z_m)

    ground_r = dg.terrain_sample(schema, profile, sector,
                                 angle_deg, z_m)["radius_m"]

    def arc_deg(metres):
        """Metres of arc at the terrace's own radius, as degrees."""
        return math.degrees(metres / max(ground_r, 1e-9))

    def dist(a, z):
        return math.hypot(math.radians(a - angle_deg) * ground_r, z - z_m)

    # WHAT IS ALREADY ON THE GROUND, so nothing is planted through it. Two
    # rectangles in the terrace's own local frame: the terrace itself and the
    # bank the waterfall runs down. The AAA checklist calls this "clearance
    # against every other system occupying the same space"; here the two
    # systems are the same module's own two halves, which is exactly the case
    # the tram/spoke interpenetration came from.
    occupied = [(-TERRACE_L_M / 2 - 1.0, TERRACE_L_M / 2 + 1.0,
                 -TERRACE_W_M / 2 - 1.0, TERRACE_W_M / 2 + 1.0),
                (-TERRACE_L_M / 2 - BANK_W_M - 1.0, -TERRACE_L_M / 2,
                 -TERRACE_W_M / 2, TERRACE_W_M / 2)]

    if near:
        lv, lt, lg = park_planting(seed, TERRACE_L_M / 2, TERRACE_W_M / 2)
        emit(lv, lt, lg, angle_deg, z_m)
        lv, lt, lg = sett_courses(seed, -TERRACE_L_M / 2, TERRACE_L_M / 2,
                                  -TERRACE_W_M / 2, TERRACE_W_M / 2)
        emit(lv, lt, lg, angle_deg, z_m)
        lv, lt, lg = ground_cover(seed, avoid=occupied)
        emit(lv, lt, lg, angle_deg, z_m)

    # The town around it. Placed deterministically, and every one of them is
    # checked against the settlement band rather than assumed to be inside it.
    lo, hi = [b for b in settlement_arcs()
              if b[0] <= angle_deg % 360.0 < b[1]][0]
    # Footprints, so nothing is planted inside a wall. Kept in (angle, z, r)
    # form because that is what the placement loops work in.
    plots = []

    def free(a, z, r_m):
        r_deg = arc_deg(r_m + KEEPOUT_M)
        return all(abs(a - pa) > r_deg + arc_deg(pr)
                   or abs(z - pz) > r_m + pr + KEEPOUT_M
                   for pa, pz, pr in plots)

    # The waterfall bank is a 14 x 26 x 12 m solid at the terrace's west end
    # and it goes into `plots` before anything is planted. Found by reading the
    # placement rather than by a render: the hero ring's west point lands at
    # local x = -32 m and the bank runs -37 to -23, so a tree would have stood
    # inside a twelve-metre embankment. Same class as the trunk-in-a-wall the
    # gate below catches, one module over -- `setting()` and the planting were
    # two independent draws with nothing between them.
    _bank_x = -TERRACE_L_M / 2 - BANK_W_M / 2
    plots.append((angle_deg + arc_deg(_bank_x), z_m,
                  math.hypot(BANK_W_M, TERRACE_W_M) / 2.0))

    placed = 0
    for i in range(blocks * 3):
        if placed >= blocks:
            break
        a = lo + 2.0 + _u(seed, "ba", i) * (hi - lo - 4.0)
        z = z_m + (_u(seed, "bz", i) - 0.5) * 260.0
        if abs(a - angle_deg) < 1.2:
            continue                       # keep the landmark's setting clear
        lvl = _lod_for(dist(a, z))
        bv, bt, bg, dims = block_building(f"{seed}-{i}", level=lvl)
        plots.append((a, z, max(dims[0], dims[1]) / 2.0))
        emit(bv, bt, bg, a, z)
        placed += 1

    # THE STREET GRID. `The Gardens.webp` reads the settlement as "low-rise
    # flat-roofed blocky buildings, two to four storeys, in a dense orthogonal
    # street grid", with "street lighting: bright point sources on posts along
    # the streets" and "palm trees lining streets and open ground". The scatter
    # above is one building per 4,400 m2 and is not a street; this is.
    if near:
        for si in range(-2, 3):
            a_street = angle_deg + arc_deg(si * STREET_PITCH_M)
            if not (lo < a_street < hi) or si == 0:
                continue
            for zi in range(-2, 3):
                z = z_m + zi * CROSS_PITCH_M
                if abs(z - z_m) > NEAR_TOWN_M:
                    continue
                for side in (-1, 1):
                    key = f"{seed}/st/{si}/{zi}/{side}"
                    d0 = dist(a_street, z)
                    if d0 > NEAR_TOWN_M + 30.0:
                        continue
                    bv, bt, bg, dims = block_building(key, level=_lod_for(d0))
                    # The block is turned a quarter so its LONG face addresses
                    # the street, then stood off by half its own depth plus
                    # half the carriageway. Doing it by offset alone put a 22 m
                    # facade across the street it was meant to front, and the
                    # trunk-in-a-wall gate below caught it at 0.70 m.
                    off = STREET_W_M / 2.0 + dims[1] / 2.0 + 1.5
                    a = a_street + arc_deg(side * off)
                    rad = max(dims[0], dims[1]) / 2.0
                    if not free(a, z, rad):
                        continue
                    plots.append((a, z, rad))
                    emit(bv, bt, bg, a, z, yaw=math.pi / 2.0)
            # Street trees down the pavement, and only where a crown fits.
            n = int(2 * NEAR_TOWN_M / STREET_TREE_PITCH_M)
            for k in range(n):
                z = z_m - NEAR_TOWN_M + STREET_TREE_PITCH_M * (k + 0.5)
                key = f"{seed}/stt/{si}/{k}"
                a = a_street + arc_deg((STREET_W_M / 2.0 - 1.2)
                                       * (1 if k % 2 else -1))
                d = dist(a, z)
                if not free(a, z, TREE_H_M * CROWN_FRAC):
                    continue
                plots.append((a, z, TREE_H_M * CROWN_FRAC))
                emit(*tree(key, level=min(0, _lod_for(d)),
                           form=tree_form(key)), a, z)

    # The park's own trees. The six nearest are the ones that get the near
    # level: `HERO_TREES` is a BUDGET, stated here rather than implied by a
    # radius, because a radius silently costs whatever happens to fall in it.
    park = []
    for i in range(trees):
        a = lo + 1.0 + _u(seed, "ta", i) * (hi - lo - 2.0)
        z = z_m + (_u(seed, "tz", i) - 0.5) * 240.0
        park.append((dist(a, z), a, z, f"{seed}-t{i}"))
    # 29a is a GROVE, not a scatter: "mature broadleaf trees overhanging the
    # frame", clipped hedges, a planted bank -- planting massed round a path.
    # So the near trees are placed on the terrace's own edge rather than drawn
    # from the same uniform distribution that puts one every 4,400 m2.
    for k in range(HERO_TREES):
        a = math.tau * k / HERO_TREES
        rx = TERRACE_L_M / 2 + 5.0 + 8.0 * _u(seed, "hx", k)
        rz = TERRACE_W_M / 2 + 4.0 + 7.0 * _u(seed, "hz", k)
        px, pz = rx * math.cos(a), rz * math.sin(a)
        park.append((math.hypot(px, pz), angle_deg + arc_deg(px), z_m + pz,
                     f"{seed}/hero/{k}"))
    park.sort()
    heroes = 0
    for d, a, z, key in park:
        if not free(a, z, TREE_H_M * CROWN_FRAC):
            continue
        lvl = NEAR_LEVEL if heroes < HERO_TREES else _lod_for(d)
        heroes += 1
        plots.append((a, z, TREE_H_M * CROWN_FRAC))
        emit(*tree(key, level=lvl, form=tree_form(key)), a, z)

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
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)

    # --- settlement bands come from LAND_USE, not from a second copy -------
    arcs = settlement_arcs()
    check("there are two settlement bands, as LAND_USE says",
          len(arcs) == sum(1 for _f, n, _r in it.LAND_USE if n == "settlement"),
          str([(round(a, 1), round(b, 1)) for a, b in arcs]))
    check("the bands are where LAND_USE's fractions put them",
          abs(arcs[0][0] - 0.26 * 360) < 1e-6
          and abs(arcs[0][1] - 0.40 * 360) < 1e-6,
          str(arcs[0]))
    check("a field angle is not a settlement angle", not in_settlement(10.0))
    check("a settlement angle is", in_settlement(112.0))

    # --- the landmark, against the frame ----------------------------------
    lv, lt, lg = civic_landmark()
    check("the landmark builds", len(lt) > 400, f"{len(lt)} triangles")
    ys = [q[1] for q in lv]
    check("the tower is the height the two figures measure",
          abs(max(ys) - (TOWER_H_M + SLAB_T_M)) < 0.01,
          f"{max(ys):.2f} m against 330px/35px * 1.7 m = {TOWER_H_M} m")
    check("the tower is about five storeys",
          4.5 <= TOWER_H_M / SLAB_RISE_M <= 6.0,
          f"{TOWER_H_M / SLAB_RISE_M:.1f} storeys at {SLAB_RISE_M} m")
    check("the second drum is lower than the tower, as the frame shows",
          DRUM2_H_M < TOWER_H_M, f"{DRUM2_H_M} vs {TOWER_H_M}")
    check("the slab terraces cantilever OUT past the tower",
          SLAB_OVERHANG_M > 0 and TOWER_R_M + SLAB_OVERHANG_M > TOWER_R_M)
    names = {n for n, _lo, _hi in lg}
    # The colonnade must have a drum behind it. Without one the bays are open
    # through the building and the sky shows through its top -- found by
    # rendering against magenta, which is the only reason it was visible.
    check("the colonnade has a drum behind it, so it is not a hole",
          "garden_colonnade_core" in names,
          "open bays with nothing behind them are a hole, not a colonnade")
    for want in ("garden_colonnade", "garden_glazing", "garden_slab",
                 "garden_stair_accent"):
        check(f"the landmark has its {want.split('_', 1)[1]}", want in names)

    # --- placement --------------------------------------------------------
    V, T, G = townscape(schema, profile, sector)
    check("the townscape builds", len(T) > 2000, f"{len(T)} triangles")
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in G) == len(T))

    radii = [math.hypot(q[0], q[1]) for q in V]
    r_floor = it.sector_radius(schema, profile, sector)
    # Up is INWARD. If this is backwards every building is inside the hull.
    check("the town stands INWARD of the floor, because up is inward",
          min(radii) < r_floor - TOWER_H_M + 1.0,
          f"min radius {min(radii):.1f} m vs floor {r_floor:.1f} m")
    check("nothing pokes outward through the pressure hull",
          max(radii) <= dg.FLOOR_R + 12.0,
          f"max radius {max(radii):.1f} m")

    # Every footing must sit ON the terrain, not over or under it.
    worst = 0.0
    for a in (100.0, 112.0, 130.0):
        gr = dg.terrain_sample(schema, profile, sector, a, 4900.0)["radius_m"]
        pv = place([(0.0, 0.0, 0.0)], schema, profile, sector, a, 4900.0)
        worst = max(worst, abs(math.hypot(pv[0][0], pv[0][1]) - gr))
    check("a building's base lands exactly on the heightfield",
          worst < 1e-6, f"worst error {worst:.6f} m")

    # --- the budget, which is the constraint that shaped the module -------
    lo, hi = arcs[0]
    area = 2 * math.pi * r_floor * (hi - lo) / 360.0 * 260.0
    dens = len(T) / area
    # THE 0.06 tri/m2 CHECK THAT USED TO BE HERE WAS A CEILING ON DETAIL, and
    # it was the most harmful line in this repository. In session 3r the owner
    # looked at a render of this module and called the buildings "shitty little
    # cubes" and the trees a "sad excuse for a tree". Both are literally accurate
    # -- `tree()` is 30 triangles and renders as a hexagonal prism, and
    # `block_building()` is 48 -- and THIS ASSERTION WOULD HAVE FAILED ANY
    # ATTEMPT TO FIX THEM. A test suite actively defending the defect, green the
    # whole time.
    #
    # It was not written in bad faith: 0.06 tri/m2 is what the drum budget leaves
    # if the townscape is treated as a minor tenant of 4.5 million m2 of ground.
    # The error is that a budget SHARE was written down as a quality LIMIT, and
    # nothing recorded which of the two it was.
    #
    # What replaces it: the surface gate stays, because overrunning the drum's
    # allotment is a real failure. The floor now lives in `station/density.py`
    # (INV-070), which measures visible line density against a bound derived from
    # the budget, a Nyquist limit and the show's own frames. This module measures
    # 0.343 against a floor of 2.107 -- 16.3% of the bar and 0.8% of what a B5
    # set shows -- and `station/directory.py` reports it as NOT at layer 2.
    # THE 0.5 tri/m2 CHECK THAT USED TO BE HERE MEASURED THE WRONG QUANTITY,
    # and its replacement is a measurement rather than a relaxation. It read
    # `budget.DRUM["surface_tris_per_m2"] = 0.500`, which `budget.py` applies
    # to `it.drum_interior(...)` -- the GROUND HEIGHTFIELD's own mesh density
    # over 4.5 million m2 -- and applied it to OBJECTS STANDING ON the ground
    # over one 63,649 m2 band. Same units, different quantity. Near-field
    # content is by definition a concentration: 212 tussocks inside 35 m is
    # 1.4 tri/m2 locally and 0.0008 tri/m2 over the drum, and a rule that
    # forbids the first forbids ever standing anywhere.
    #
    # It is recorded rather than deleted, because the number it would have
    # given is the honest cost of this change -- 0.3554 before, 0.85 after --
    # and it is still printed on every run. What replaces it is the constraint
    # that actually binds, the FRAME, measured at the eye instead of divided
    # over an area.
    check("the townscape fits the drum's frame allowance",
          len(T) <= TOWNSCAPE_TRIS,
          f"{len(T):,} tri against {TOWNSCAPE_TRIS:,}; the drum scene "
          f"measured 263,384 of budget.DRUM's 300,000 with this module at "
          f"22,620, so the room is 59,236")

    # --- THE LOLLIPOP GATE, and it fails on this module's own last version --
    # `tree()` drew its height from a distribution and its canopy radius from
    # the CONSTANT `TREE_R_M = 2.2`, so a 10.5 m tree got a 2.2 m crown. That
    # is what `scratchpad/frames/before-tree5.png` shows and no gate in the
    # project could say it: line density, triangle count, closure and winding
    # are all satisfied by a ball on a stick. This asks the one question that
    # separates a tree from a lollipop -- how wide is the crown against how
    # tall is the tree -- over the whole population rather than over the one
    # that broke.
    worst_ratio, worst_seed = 9.9, ""
    for i in range(40):
        key = f"gate/tree/{i}"
        tv, _tt, _tg = tree(key, level=NEAR_LEVEL, form="broadleaf")
        ys = [q[1] for q in tv]
        span = max(max(abs(q[0]) for q in tv),
                   max(abs(q[2]) for q in tv)) * 2.0
        ratio = span / max(ys)
        if ratio < worst_ratio:
            worst_ratio, worst_seed = ratio, key
    check("no tree is a lollipop: the crown spans a stated fraction of its "
          "own height",
          worst_ratio >= 2 * 0.30,
          f"worst {worst_ratio:.2f} on {worst_seed}; CROWN_FRAC "
          f"{CROWN_FRAC} gives a band of {2 * 0.30:.2f}..{2 * 0.60:.2f}")
    # The negative control: the rule this replaced, on the same seeds.
    old = min((2 * TREE_R_M)
              / (TREE_H_M * (0.75 + 0.5 * _u(f"gate/tree/{i}", "th")))
              for i in range(40))
    check("...and the constant it replaced FAILS that gate",
          old < 2 * 0.30,
          f"a fixed TREE_R_M = {TREE_R_M} gives {old:.2f} on the tallest "
          f"draw, which is a ball on a stick")

    # --- foliage hangs on branches, and no mass swallows the canopy --------
    tv, tt, tg = tree("gate/canopy", level=NEAR_LEVEL, form="broadleaf")
    masses = []
    for name, g0, g1 in tg:
        if name != "garden_foliage":
            continue
        idx = {j for tri in tt[g0:g1] for j in tri}
        pts = [tv[j] for j in idx]
        cx = sum(q[0] for q in pts) / len(pts)
        cy = sum(q[1] for q in pts) / len(pts)
        cz = sum(q[2] for q in pts) / len(pts)
        rr = max(math.dist((cx, cy, cz), q) for q in pts)
        masses.append((cx, cy, cz, rr))
    crown = max(max(abs(q[0]) for q in tv), max(abs(q[2]) for q in tv))
    check("the canopy is many masses, not one",
          len(masses) >= 3 * LEAF_LOBES, f"{len(masses)} foliage masses")
    off_axis = min(math.hypot(m[0], m[2]) for m in masses)
    check("no foliage mass sits on the trunk axis",
          off_axis > 0.15 * crown,
          f"nearest mass centre {off_axis:.2f} m off the axis, crown radius "
          f"{crown:.2f} m")
    biggest = max(m[3] for m in masses)
    check("no single mass swallows the canopy",
          biggest < 0.62 * crown,
          f"largest lobe radius {biggest:.2f} m of a {crown:.2f} m crown")

    # --- bark: the near level's trunk section is not a circle --------------
    # A smooth cylinder draws exactly two lines however finely it is
    # tessellated, because every lateral facet edge sits under `density.py`'s
    # 3.24 deg crease threshold. This is the assertion that the near level
    # actually spends its sections on ridges rather than on smoothness, and it
    # is measured on the emitted ring rather than on `FLUTE_D`.
    def _ring_spread(lv):
        tv, _tt, tg = tree("gate/bark", level=lv, form="broadleaf")
        g0 = [(a, b) for n, a, b in tg if n == "garden_trunk"][0]
        seg = {-1: 12, 0: TRUNK_SEG}[lv]
        ring = tv[:seg]
        rr = [math.hypot(q[0], q[2]) for q in ring]
        return (max(rr) - min(rr)) / (sum(rr) / len(rr))

    check("the near level's trunk is fluted, not smooth",
          _ring_spread(NEAR_LEVEL) > 0.15,
          f"section radius varies {_ring_spread(NEAR_LEVEL):.3f} of its mean")
    check("...and the level above it is smooth, which is the control",
          _ring_spread(0) < 1e-9,
          f"{_ring_spread(0):.6f} -- a flute at 113 m is under a pixel")

    # --- the LOD ladder, and it must descend and must agree with the other --
    for form in TREE_FORMS:
        counts = [len(tree("gate/lod", level=lv, form=form)[1])
                  for lv in (-1, 0, 1, 2, 3)]
        check(f"the {form} LOD chain descends",
              all(a > b for a, b in zip(counts, counts[1:])), str(counts))
    import drum_dressing as _dd                          # noqa: PLC0415
    check("the near ladder EXTENDS drum_dressing's rather than replacing it",
          tuple(LOD_SWITCH_M[1:]) == tuple(round(x, 4)
                                           for x in _dd.switch_distances()),
          f"{LOD_SWITCH_M[1:]} against {_dd.switch_distances()}")
    # THE ASSERTION THAT PROTECTS THE OTHER MODULE. `drum_dressing`'s
    # LOD_SCALE_M was solved by bisection against DRESSING_TRIS with
    # `gd.tree()` and `gd.block_building()` at their bare-call cost, and its
    # worst standing position lands at 119,868 of 120,000. Making the bare
    # call finer -- which is the obvious way to answer "the near tree is a
    # lollipop" -- silently overruns a budget in a file this module does not
    # own, and no gate in that file would name this one.
    worst = _dd.worst_case_cost(6)
    check("the default level still fits the budget drum_dressing solved its "
          "LOD scale against",
          worst["triangles"] <= _dd.DRESSING_TRIS,
          f"{worst['triangles']:,} of {_dd.DRESSING_TRIS:,} at {worst['at']}")

    # --- THE MASS IS NOT AN EXTRUSION --------------------------------------
    # "Shitty little cubes" is a statement about SILHOUETTE, and the version
    # this replaced answered it with trim: pilasters, cills, gutters, twenty-one
    # times the line density, and the same rectangular prism underneath. So the
    # gate has to ask about the mass and ignore the trim, which is why it reads
    # the `garden_block` groups ONLY -- the spandrel courses that are the walls
    # -- and not the cornice, parapet, roof plant or downpipes that sit on top
    # of any shape at all.
    #
    # Measured off the emitted mesh, never off the plan, so a setback that is
    # declared and not built fails. Calibration, all on the same 24 seeds:
    # as built the worst block keeps 0.50 of its plan at 80% of its height;
    # with SETBACK_M forced to 0 the worst keeps 0.70, because the low wing is
    # still doing the job on its own; with the setback AND the wing removed the
    # worst is 1.000, an extrusion, and the gate fires.
    def _mass_plan(bv, bt, bg, y):
        idx = set()
        for name, g0, g1 in bg:
            if name == "garden_block":
                for tri in bt[g0:g1]:
                    idx.update(tri)
        pts = [bv[j] for j in idx if bv[j][1] > y]
        if not pts:
            return 0.0
        xs = [q[0] for q in pts]
        zs = [q[2] for q in pts]
        return (max(xs) - min(xs)) * (max(zs) - min(zs))

    worst_step, worst_key = 0.0, ""
    for i in range(24):
        key = f"gate/block/{i}"
        bv, bt_, bg_, dims = block_building(key)
        base = _mass_plan(bv, bt_, bg_, dims[2] * 0.02)
        top = _mass_plan(bv, bt_, bg_, dims[2] * 0.80)
        if base <= 0:
            continue
        if top / base > worst_step:
            worst_step, worst_key = top / base, key
    check("no block is an extrusion: every mass changes plan with height",
          worst_step <= 0.85,
          f"worst {worst_key} keeps {worst_step:.2f} of its mass plan at 80% "
          f"of its height; the version this replaced keeps 1.00")
    prism_v, prism_t, prism_g = [], [], []
    _box(prism_v, prism_t, prism_g, "garden_block",
         (-8.0, 0.0, -5.0), (8.0, 9.0, 5.0))
    check("...and the gate FIRES on the mass this replaced",
          _mass_plan(prism_v, prism_t, prism_g, 9.0 * 0.80)
          / _mass_plan(prism_v, prism_t, prism_g, 9.0 * 0.02) > 0.85,
          "one box for the whole mass keeps its plan at every height")

    # --- nothing is planted through a wall ---------------------------------
    # `before-tree5.png` shows a tree whose canopy is inside a building, from
    # 11 m away. Nothing measured it: the scatter drew blocks and trees from
    # two independent distributions and neither knew about the other.
    V2, T2, G2 = townscape(schema, profile, sector)
    trunks = [V2[T2[g0][0]] for name, g0, _g1 in G2
              if name == "garden_trunk" and g0 < len(T2)]
    walls = [V2[T2[g0][0]] for name, g0, _g1 in G2
             if name == "garden_block" and g0 < len(T2)]
    worst_gap = min((math.dist(p, q) for p in trunks for q in walls),
                    default=1e9)
    check("no trunk stands inside a wall",
          worst_gap > 1.0,
          f"closest trunk to block corner {worst_gap:.2f} m over "
          f"{len(trunks)} trunks and {len(walls)} blocks")

    # --- the ground a player stands on -------------------------------------
    gv, gt, _gg = ground_cover("gate", avoid=[(-TERRACE_L_M / 2,
                                               TERRACE_L_M / 2,
                                               -TERRACE_W_M / 2,
                                               TERRACE_W_M / 2)])
    inside = sum(1 for q in gv
                 if abs(q[0]) < TERRACE_L_M / 2 - 1.0
                 and abs(q[2]) < TERRACE_W_M / 2 - 1.0)
    check("ground cover does not grow through the paving",
          inside == 0, f"{inside} vertices inside the terrace")
    bare = ground_cover("gate", radius=0.0)
    check("...and the cover gate can fail: no radius, no cover",
          len(bare[1]) == 0 and len(gt) > 400,
          f"{len(gt)} triangles of cover against {len(bare[1])} bare")

    # --- the swept section is wound outward --------------------------------
    sv, sw_t, sw_g = [], [], []
    _sweep(sv, sw_t, sw_g, "probe", [(0, 0, 0), (0, 4, 0)], [1.0, 1.0], seg=8)

    def _outward(tris):
        n = 0
        for a, b, c in tris:
            p, q, r = sv[a], sv[b], sv[c]
            nrm = _cross(_sub(q, p), _sub(r, p))
            mid = tuple((p[i] + q[i] + r[i]) / 3.0 for i in range(3))
            if _dot(nrm, (mid[0], 0.0, mid[2])) > 0:
                n += 1
        return n

    check("_sweep winds outward", _outward(sw_t) == len(sw_t),
          f"{_outward(sw_t)}/{len(sw_t)}")
    check("...and the outward test can fail",
          _outward([(a, c, b) for a, b, c in sw_t]) == 0,
          "a reversed sweep must score zero")

    # --- determinism ------------------------------------------------------
    a1 = townscape(schema, profile, sector)[0]
    a2 = townscape(schema, profile, sector)[0]
    check("regeneration is byte-identical", a1 == a2)
    check("two different seeds give two different towns",
          townscape(schema, profile, sector, seed="a")[0]
          != townscape(schema, profile, sector, seed="b")[0])

    # --- placement refuses a field ----------------------------------------
    try:
        townscape(schema, profile, sector, angle_deg=10.0)
        check("building on a field is refused", False, "it was allowed")
    except ValueError:
        check("building on a field is refused", True)

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0, 0, 0), (1, 2, 3))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0)
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)

    print(f"\ngarden townscape: {len(T):,} triangles, {dens:.4f} tri/m2, "
          f"landmark {TOWER_H_M + SLAB_T_M:.1f} m over "
          f"{len(arcs)} settlement bands")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


# ---------------------------------------------------------------------------
# THE FRAMES A CRAFT CLAIM ABOUT THIS MODULE HAS TO CITE
# ---------------------------------------------------------------------------
# `CLAUDE.md`: "Every craft claim cites a frame at the rubric's HALF distance,
# not the normal one. A wide shot is not evidence about craft." That rule is
# the reason this module sat at craft 1 through a whole rebuild -- the only
# committed frames of the Garden were the wide `docs/engine-drum-garden.png`
# and a 3z terrace shot, and at 56 m a lollipop reads as a tree.
#
# So the cameras are recorded here, next to the geometry, in the same shape
# `export_scene.EXPOSURE_FRAMES` records its own. Each one is a `--shot drum`
# argument string; the eye stands at 1.70 m on the heightfield and the target
# is the subject's own mid height, both computed from `drum_ground` rather than
# written down, by the snippet in `_shots_report`.
HERO_SHOTS = {
    # 9 m from a level -1 broadleaf, standing under the canopy edge. This is
    # THE frame for the tree, and its before-image is
    # `docs/garden-4q-before-tree.png` at the identical camera.
    "hero_tree": ('--shot drum --eye " -117.091,243.413,4909.880" '
                  '--target " -116.094,241.341,4918.880" --fov 50'),
    # 14 m off the near corner of a street block, three-quarter, so the tiers,
    # the batter and the wing are all in silhouette at once. A face-on shot of
    # a terraced building looks exactly like a face-on shot of a box.
    "hero_block": ('--shot drum --eye " -113.898,245.347,4885.000" '
                   '--target " -124.912,236.429,4900.000" --fov 50'),
}


def _near_report():
    """What the near level costs and what the pixel criterion would say.

    Both columns, side by side, because the honest answer is that they
    disagree and the budget wins. See `NEAR_SWITCH_M`.
    """
    k = dg.SCREEN_H / (2.0 * math.tan(math.radians(dg.FOV_DEG) / 2.0))
    print(f"screen {dg.SCREEN_H} px at {dg.FOV_DEG} deg -> {k:.1f} px.m\n")
    print("feature                       size      1 px at")
    for name, size in (("bark flute", TRUNK_R_M * FLUTE_D),
                       ("order-3 twig diameter", TRUNK_R_M * 0.20 * 2),
                       ("balcony rail", RAIL_T_M),
                       ("sett course upstand", COBBLE_PROUD_M),
                       ("window pane", PANE_H_M)):
        print(f"  {name:26s} {size:6.3f} m  {size * k:8.1f} m")
    print(f"\nnear switch                            {NEAR_SWITCH_M:8.1f} m"
          f"   <- budget, not pixels")
    print(f"then drum_dressing's ladder            "
          f"{LOD_SWITCH_M[1]:8.1f} / {LOD_SWITCH_M[2]:.1f} / "
          f"{LOD_SWITCH_M[3]:.1f} m\n")
    print("level   broadleaf   umbrella   palm   block")
    for lv in (-1, 0, 1, 2, 3):
        row = [len(tree("report", level=lv, form=f)[1]) for f in TREE_FORMS]
        blk = len(block_building("report", level=lv)[1]) if lv <= 0 else 0
        print(f"{lv:>5}   {row[0]:9,}   {row[1]:8,}   {row[2]:4,}   "
              f"{blk:5,}")
    print(f"\nHERO_TREES = {HERO_TREES} -- a count, so the near level's cost "
          f"is stated rather than\n  discovered. A radius costs whatever "
          f"happens to fall inside it.")
    return 0


def _cost_report():
    """Where the townscape's triangles go, by material group."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    _V, T, G = townscape(schema, profile, sector)
    per = {}
    for name, lo, hi in G:
        per[name] = per.get(name, 0) + (hi - lo)
    for name, n in sorted(per.items(), key=lambda kv: -kv[1]):
        print(f"  {name:26s} {n:7,}  {100.0 * n / len(T):5.1f}%")
    print(f"  {'TOTAL':26s} {len(T):7,}  against TOWNSCAPE_TRIS "
          f"{TOWNSCAPE_TRIS:,}")
    _bare = townscape(schema, profile, sector, near=False)[1]
    print(f"\n  --no-near (the state this session started from, plus the new "
          f"massing): {len(_bare):,}")
    return 0


if __name__ == "__main__":
    if "--near" in sys.argv:
        sys.exit(_near_report())
    if "--cost" in sys.argv:
        sys.exit(_cost_report())
    if "--shots" in sys.argv:
        for name, cmd in HERO_SHOTS.items():
            print(f"tools/render_godot.sh {cmd} --res 960x540 \\\n"
                  f"    --out docs/garden-4q-{name}.png")
        sys.exit(0)
    sys.exit(_selftest())
