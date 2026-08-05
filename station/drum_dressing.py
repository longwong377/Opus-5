#!/usr/bin/env python3
"""What STANDS on the drum floor: 4.5 million square metres of world.

WHY THIS MODULE EXISTS, in the reviewer's own words
---------------------------------------------------
`docs/aaa-scorecard.json`, `garden_townscape` round 2, severity **major**,
descriptor **C1**, against `docs/judge-4e-drum-half.png`:

    "the habitat floor is two flat colour fields meeting along a straight-edged
    polygon boundary with the terrain lattice visible in the zigzag. No
    vegetation, no props, no people, no relief, nothing standing anywhere on
    4.5 million m2."

Every word of that was true when it was written, and the cause is stated in the
same finding: `station/budget.py` reported the drum ground at **0.020 tri/m2
against a 0.500 allowance (3.9%)** with **183,880 triangles of headroom
explicitly unspent**. `drum_ground.py` gave the drum a *surface*; `garden.py`
gave **one** 300 m stretch of **one** settlement band a town. Everything else --
the other 2,286 m of the drum, both arable bands, the lake, the parkland and
15/16ths of the built-up land -- carried nothing at all.

This module is the rest of it. It is a scatter, not a hand-placed set: 4.5
million square metres cannot be dressed by hand, and a generator is finished
when its output is VARIOUS rather than when it is correct (MASTER-PLAN, 4h).

WHAT THE REFERENCE ESTABLISHES, and it is the same four authority-1 frames
`drum_ground.py` and `garden.py` are already built from -- carried here with
what each one asks for that nothing was building
--------------------------------------------------------------------------
`03-sector-blue/Babylon_5_2-22_34b.jpg` (authority 1) -- down the axis over the
agricultural half. "Irregular four- and five-sided parcels ... **darker tree
masses scatter across a tan parcel** ... pale roads wind between them." The
parcels exist as *tags* in `drum_ground.sample()`; the **tree masses did not
exist at all**. -> `copse`, and the hedgerow that draws a parcel edge in three
dimensions instead of as a colour change.

`03-sector-blue/Babylon_5_2-22_33a.jpg` (authority 1) -- the built-up half.
"Rectangular built parcels carry a fine internal grid." `drum_ground` cuts the
avenue grid into the podium; **nothing stood on the blocks**. -> `town_block`,
rolled out over every settlement block on the drum rather than twelve of them.

`14-characters-and-uniforms/talia-winters in gorgeous office.webp` (authority 1)
-- the far side through a window: "low wide grey settlement blocks, **terraced
rather than towered**". That is the massing rule the L2/L3 proxies follow, and
it is why the proxy is a two-step massing rather than a box.

`03-sector-blue/Babylon_5_2-22_29a.jpg` (authority 1) -- ground level in the
park: "gravel paths, clipped hedges about head height, trees, a waterfall, an
elevated tram, **tall orange conical spires**". `garden.hard_landscape()` builds
the paths, hedges and benches for the Garden's own terrace. The **spires are
built by nothing in this project** and they are the most distinctive silhouette
in the frame. -> `spire`.

THE ONE NUMBER THAT SHAPES EVERY DECISION BELOW
-----------------------------------------------
`budget.DRUM["visible_set_tris"]` is 300,000 and the drum already spends, both
measured in this session and not quoted from anywhere:

    end caps 15,072 + guideways 11,796 + spokes 516 + core 13,340
    + trams 12,624 + garden.townscape 22,620          =  75,968   fixed
    drum_ground.worst_case_cost(12)                    =  96,320   worst eye
                                                        --------
                                                          172,288

which leaves **127,712**. `DRESSING_TRIS` below is 120,000 of that, and the
7,712 that is left over is margin rather than an oversight. So this module has
about **26 times** the triangles the ground itself spends per square metre, and
that is the headroom the reviewer said was unspent.

HOW THE LOD CHAIN IS DERIVED, AND WHY IT IS NOT THE GROUND'S CRITERION
----------------------------------------------------------------------
`drum_ground._switch_distance()` accepts a level once its geometric error is
under 1.5 pixels. Applied to a scatter that criterion is useless and it is worth
writing down why, because it looks like the obvious thing to do: substituting a
24-triangle blob for a 344-triangle tree is an error of order **1.5 m**, and
1.5 m under budget needs 1,540 m of distance -- further than any two points in
the drum are apart. A pixel-error criterion says "never switch", the whole drum
renders at full detail, and 2,500 trees alone would be 860,000 triangles.

So the chain here is **budget-driven, and this module says so rather than
dressing it up as a perceptual result**. One scale parameter sets all three
switch distances at fixed ratios; `--derive` bisects for the largest scale
(finest detail, most triangles) whose WORST standing position still fits
`DRESSING_TRIS`, and prints, at each switch, the size in pixels of the smallest
feature the coarser level throws away. Those pixel figures are the honest report
of what the budget bought: they are outputs, not inputs.

WHAT IS NOT HERE, stated because a missing thing that is not written down reads
as an oversight six sessions later
-------------------------------------------------------------------------------
  * **People.** The reviewer's finding says "no people" and this module places
    none. `station/npc/body.py` is owned by another agent this session and a
    render taken against a module mid-edit is not evidence (CLAUDE.md, 4e).
    The hooks are here -- `field()` returns world positions and ground radii --
    and the work is one function.
  * **Collision.** `station/drum_walk.py` builds the collision ground from
    `drum_ground.ground_patch`; nothing here is solid, so a player walks through
    a hedge. That is the same state props were in before session 3v and the same
    fix applies: derive boxes from the emitted mesh, do not write a second list.
    STILL TRUE IN 4r, and the near rung makes half of it CORRECT and half of it
    worse. Walking through a crop stand, a tussock or a reed bed is what a
    player should do. Walking through a **town block** is not, and the near
    gate now reports how many of its standing positions fall inside one
    (`skipped_indoors`) precisely so that the number is visible: they are only
    reachable because nothing here is solid.
  * **Streaming.** Everything here is built for one eye at one instant, exactly
    as `drum_ground.visible_set` is. Neither is a streamer.

SESSION 4r ADDED THE RUNG BELOW THE LADDER, AND THE MEASUREMENT THAT SAYS SO
----------------------------------------------------------------------------
Everything above was true and closed half the finding. STATE.md 24.4b read the
other half off the frame this module's own work produced: "the scatter is dense
enough to read at 500 m and not at 20 m, which is the opposite of where a player
stands ... nothing measures features per m2 AT WALKING DISTANCE". Measured at
that frame's own eye, the nearest thing standing anywhere was **44.3 m** away and
nothing at all was inside 35 m.

`--near` is the measurement and `near_horizon_split()` is why its floor is not a
preference: at the player's own 1.7 m and 70-degree lens, HALF of everything
below the horizon is ground within **5.39 m** of your feet. The near rung
(`near_field`) fills it, on the ground's own lattice, at a density solved against
the gate rather than chosen. See INV-490..494.

Run:
    python3 station/drum_dressing.py                 # self-test
    python3 station/drum_dressing.py --report        # what stands on the drum
    python3 station/drum_dressing.py --gate          # the emptiness gate
    python3 station/drum_dressing.py --gate --bare   # ...shown failing
    python3 station/drum_dressing.py --near          # the NEAR-FIELD gate
    python3 station/drum_dressing.py --near --bare   # ...shown failing
    python3 station/drum_dressing.py --degeneracy    # five drum rows, five hashes
    python3 station/drum_dressing.py --derive        # re-solve the LOD scale
    python3 station/drum_dressing.py --derive-near   # re-solve the near density
"""
import argparse
import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import drum_ground as dg                                        # noqa: E402
import garden as gd                                             # noqa: E402
import interior as it                                           # noqa: E402

# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
# `drum_ground._unit` rather than a second value source, for the reason
# `garden.settlement_arcs()` reads `interior.LAND_USE`: two generators keyed off
# two different noise functions drift, and the drift is invisible.
_unit = dg._unit

SEED = "b5-drum-dressing-v1"

# A golden digest over the whole placement, the same instrument
# `drum_ground.GROUND_DIGEST` is and for the same reason: this module has about
# forty constants and pinning them one at a time is forty assertions restating
# forty numbers. It is meant to be brittle -- a placement change SHOULD fail it,
# be looked at in a render, and have the digest updated deliberately.
FIELD_DIGEST = "9103bbc25c65353e"

# ---------------------------------------------------------------------------
# THE BUDGET, and it is the input rather than the output
# ---------------------------------------------------------------------------
# Derived in the module docstring from measurements taken in this session:
# 300,000 (budget.DRUM) - 75,968 fixed parts - 96,320 worst-case ground.
# Left at 120,000 rather than 127,712 so that a small growth in the ground or
# the tram does not silently push the drum over its allowance. -- INV-458
DRESSING_TRIS = 120_000

# Switch distances, as multiples of LOD_SCALE_M. The ratios are fixed and the
# scale is solved; see `--derive`. Three switches, matching the three proxy
# levels every prototype family below provides.
LOD_RATIOS = (1.0, 3.2, 9.0)
# Solved by `--derive` against DRESSING_TRIS. Recorded rather than solved at
# import because the solve sweeps 36 standing positions over the whole instance
# field, and a module that costs two seconds to import is a module every gate
# in the project pays for.
#
# LEFT AT 113 IN 4r, AND `--derive` NOW SAYS 118.4 -- WHICH IS DECLINED, ON
# EVIDENCE. The whole near rung was added this session and the solve still came
# back LONGER than the recorded value, which is only possible if the far field
# got cheaper. It did: `garden.py`'s 4q rebuild changed the level-0 tree and
# town block this module instances, and the far field's worst standing position
# fell from the **119,868** recorded in STATE.md 24.6, INV-452 and
# `docs/aaa-scorecard.json` to **104,842**. That figure was written down as
# "unchanged at 119,868 / 120,000" and was not. Measured on the COMMITTED
# module against the CURRENT garden -- i.e. with none of this session's edits
# -- it is 104,842.
#
# So the near rung is paid for out of headroom the garden rebuild had already
# freed: combined worst is 114,670 of 120,000. The extra 5.4 m of level-0 reach
# `--derive` offers is declined because the drum as a whole is already over its
# allowance (see `_selftest`'s drum budget check, which is honestly RED), and
# spending the last of a per-part allowance to buy far-field reach while the
# whole is over is the wrong trade in both directions.
#
# THE DRUM IS NO LONGER OVER, AND THE DECISION IS UNCHANGED. Later in 4r the
# ground's LOD error was charged per PATCH rather than per drum (INV-540) and
# the drum's worst standing eye went 315,604 -> 290,164 against 300,000, so
# `_selftest`'s budget check is green. That buys nothing here: this module is
# still 114,910 of its own 120,000, and the second half of the sentence above
# -- spending the last of a per-part allowance on far-field reach -- was always
# the load-bearing half. 113.0 stands, and now on one reason instead of two.
LOD_SCALE_M = 113.0

# Screen constants, taken from `drum_ground` rather than restated, so the pixel
# figures `--derive` prints are comparable with the ground's own switch table.
FOV_DEG = dg.FOV_DEG
SCREEN_H = dg.SCREEN_H


def _pixels(size_m, distance_m):
    """Screen height in pixels of a feature `size_m` across at `distance_m`."""
    if distance_m <= 0:
        return float("inf")
    return (size_m / distance_m) * SCREEN_H / (
        2.0 * math.tan(math.radians(FOV_DEG) / 2.0))


# ---------------------------------------------------------------------------
# THE HEDGEROW -- the single highest-value object on the drum floor
# ---------------------------------------------------------------------------
# 34b's parcels read as a patchwork because their edges have a tone of their
# own; `drum_ground.sample()` already tags a `hedge` kind on every arable parcel
# boundary and gives it a 0.22 m bank. What it cannot do is make the edge stand
# up: at 3.9 m cells a 1 m hedge is finer than the lattice, which is exactly why
# `drum_ground.HEDGE_H_M` is 0.22 m and its comment says "the hedge itself --
# 2 m tall, 1 m wide -- is finer than lod0's 3.9 m cell and belongs in the
# material, not the field."
#
# It belongs in neither. It belongs in an OBJECT, which is what this is. The
# geometry follows the same `_parcel()` boundary the tag follows, so the tagged
# strip and the standing hedge cannot disagree.
#
# HEIGHT. 29a is the only frame with a hedge at a known scale and it shows
# clipped hedges "about head height" in the PARK. A field boundary hedge is
# taller than a garden one and 1.9 m is a stock-proof farm hedge; the park hedge
# below is separately 1.05 m, which is `garden.HEDGE_H_M`, read from the same
# frame by `garden.hard_landscape`. Bounded ABOVE by the 2.2 m at which a hedge
# stops being a hedge and becomes a shelterbelt (which is a separate class here,
# with trees in it); bounded BELOW by 1.4 m, under which it stops occluding a
# person and reads as a kerb. Overturned by any frame showing the arable
# boundaries at a known scale. -- INV-495, authority 5
HEDGE_H_M = 1.90
HEDGE_W_M = 1.40
HEDGE_WOBBLE_M = 0.35       # amplitude of the clipped-but-not-machined top
# Sample spacing along a hedgerow at each detail level, in metres. The near
# figure is one cross-section per 6 m, which puts a crease at 6 m intervals
# along a line the player walks beside; the far figure is 64 m, which is half a
# ground patch and still draws the parcel.
HEDGE_STEP_M = (6.0, 18.0, 40.0, 80.0)
# A standard -- a full tree left uncut in the hedge line -- every 85 m. English
# hedgerow practice is one standard per chain-and-a-half of hedge; 85 m is the
# same order and is chosen so a 323 m parcel edge carries three or four rather
# than a regular two. -- INV-495
HEDGE_STANDARD_M = 85.0

# ---------------------------------------------------------------------------
# TREE MASSES
# ---------------------------------------------------------------------------
# 34b: "darker tree masses scatter across a tan parcel". A MASS, not a tree --
# which is also the only affordable reading, because 2,500 individual trees at
# the coarsest proxy this module has would be 15,000 triangles before anything
# else is built, and as a mass they are 4,200.
#
# Lattice spacing 118 m: `drum_ground.PATCH_A` is 32 cells = 124.9 m and the
# clump lattice is deliberately NOT that number, so clumps do not line up with
# patch boundaries and produce a visible grid at the LOD seams. -- INV-496
CLUMP_SPACING_M = 118.0
CLUMP_JITTER = 0.42                  # of a lattice cell, each axis
CLUMP_P_ARABLE = 0.34                # fraction of arable lattice cells
CLUMP_P_PARKLAND = 0.80              # 29a is a planted park, not a lawn
CLUMP_MIN, CLUMP_MAX = 6, 22         # trees in a mass
CLUMP_R_MIN_M, CLUMP_R_MAX_M = 13.0, 34.0
# The mass proxy at the coarsest level: one squashed dome over the clump, at
# the clump's OWN radius and at the height of the trees in it. The squash is
# therefore DERIVED per clump -- `garden.TREE_H_M` over the clump radius --
# rather than being a constant, and that matters: a fixed 0.72 ratio on a 34 m
# clump gives a 24 m dome, which is three and a half times the height of the
# trees it stands in for and reads as a hill. The first version did exactly
# that and the render showed it.
CLUMP_MASS_H_M = gd.TREE_H_M * 0.95

# ---------------------------------------------------------------------------
# THE FARM -- what makes 250,000 people eat
# ---------------------------------------------------------------------------
# CLAUDE.md's scope clause: "the physical plant that makes 250,000 people
# possible: food, water, air, power, waste". The gazetteer puts hydroponics in
# the sub-floor stack and says "the drum floor is open fields" (directory.py,
# `hydroponics`), so what stands in the fields is the equipment that works them.
#
# Nothing in the reference set shows drum farm plant at all -- 34b is too far
# away to resolve a building. All three of these are authority 5. What bounds
# them is FUNCTION and SCALE rather than a frame:
#   * a farmstead every ~3 parcels puts one within 300 m of any point in the
#     arable band, which is the distance a person walks to a tool store;
#   * a silo of 6.5 m diameter and 11 m tall holds ~350 m3, about one parcel's
#     grain, and is bounded above by the 16 m at which it would be visible in
#     34b as a distinct object and is not;
#   * an irrigation gantry spans one parcel's 87.4 m circumferential width,
#     because that is the dimension a boom is built to.
# Overturned by any frame resolving an object in the arable bands. -- INV-452
FARMSTEAD_PER_PARCELS = 3
SHED_L_M, SHED_W_M, SHED_H_M = 16.0, 9.0, 5.2
SILO_R_M, SILO_H_M = 3.25, 11.0
SILO_SEG = 10
GANTRY_PER_PARCELS = 4
GANTRY_SPAN_M = 87.4                 # one parcel circumferentially
GANTRY_H_M = 3.4
GANTRY_BAYS = 7
GANTRY_R_M = 0.16

# ---------------------------------------------------------------------------
# THE PARK -- 29a, and it is the frame with the most in it
# ---------------------------------------------------------------------------
# "tall orange conical spires". They are the one saturated accent in an
# otherwise buff-and-green frame, the same role `garden.STAIR_ACCENT` plays on
# the terrace, and they take the same material. Height is set against 29a's own
# scale anchor the way `garden.TOWER_H_M` is: the spires stand roughly twice the
# height of the tree line beside them, and `garden.TREE_H_M` is 7.0 m, so 15 m.
# Bounded above by 22 m, at which they would break the tram guideway line in the
# same frame and do not; below by 9 m, at which they stop reading as "tall".
# Overturned by a measurement off 29a at a known px/m. -- INV-455, authority 5
SPIRE_H_M = 15.0
SPIRE_R_M = 2.1
SPIRE_SEG = 12
SPIRE_BASE_H_M = 1.1
SPIRE_GROUPS = 7                     # groups of them, not a scatter
SPIRE_PER_GROUP = (2, 4)

# Park hedges and street trees take `garden.py`'s own numbers, imported rather
# than restated. The park is the band `garden.hard_landscape()` was built for.
PARK_HEDGE_H_M = gd.HEDGE_H_M        # 1.05 m, 29a, "clipped ... below eye level"
PARK_HEDGE_W_M = gd.HEDGE_W_M
PARK_HEDGE_SPACING_M = 150.0
PARK_HEDGE_LEN_M = (40.0, 130.0)

# ---------------------------------------------------------------------------
# THE LAKE
# ---------------------------------------------------------------------------
# `interior.LAND_USE` gives the water band 10% of the circumference and
# `drum_ground` floods everywhere the bowl is below WATER_LEVEL_M. What a
# shoreline needs to stop reading as a painted edge is something breaking it:
# reeds along the margin and a jetty every so often. Both authority 5, both
# bounded by the same argument as the farm plant -- 33a shows "a large dark
# blue-grey rectangle" among the built parcels at a scale where a 20 m jetty is
# one pixel. Reed height 2.4 m is a stand of phragmites; a jetty at 22 m is a
# rowing landing rather than a dock. -- INV-456
REED_H_M = 2.4
REED_W_M = 3.0
REED_RUN_M = (18.0, 60.0)
REED_SPACING_M = 95.0
JETTY_SPACING_M = 420.0
JETTY_L_M, JETTY_W_M, JETTY_H_M = 22.0, 3.2, 0.9

# ---------------------------------------------------------------------------
# THE TOWN
# ---------------------------------------------------------------------------
# `drum_ground` cuts the settlement podium into blocks of `BLOCK_CELLS` = 16
# lattice cells, 62.4 x 64.6 m, with a 10 m avenue between them. That grid is
# the town plan and it was standing empty: `garden.townscape()` places twelve
# buildings in one 300 m stretch of one band, and the drum has 1,120 blocks of
# which 290 are settlement.
#
# Buildings per block is 2-4 on a 62.4 x 64.6 m plot with a 10 m street around
# it -- so 52 x 54 m of buildable ground for blocks that `garden.BLOCK_MAX_M`
# caps at 22 x 13 m. Three of those is 40% site coverage, which is a low-rise
# terraced quarter rather than a downtown, and "terraced rather than towered" is
# what the Talia Winters frame shows. -- INV-457
TOWN_MIN, TOWN_MAX = 2, 4
TOWN_INSET_M = 9.0                   # from the block edge: the street and verge
# `garden.townscape()` already stands here. Its own blocks are placed over a
# 260 m span of z and the whole settlement arc, so this keeps out of a box
# around it rather than around one point.
TOWNSCAPE_KEEPOUT_DEG = 4.0
TOWNSCAPE_KEEPOUT_M = 190.0
# Street lamps down the avenues, near the eye only -- there are 41 km of avenue
# on this drum and a lamp every 32 m would be 1,280 objects, which is what the
# LOD chain is for. `garden.LAMP_PITCH_M` is 7.5 m on a terrace; an avenue is a
# road, and 32 m is a carriageway spacing.
LAMP_PITCH_M = 32.0
LAMP_H_M = gd.LAMP_H_M
LAMP_R_M = gd.LAMP_R_M

# ---------------------------------------------------------------------------
# Prototype variety
# ---------------------------------------------------------------------------
# Eight of each, instanced with yaw and scale, rather than one build per object.
# Eight is the number at which the eye stops indexing the repeat at the
# densities here (a copse of 22 draws from all eight, so the chance of two
# adjacent members matching is 1/8), and building 2,500 trees individually costs
# 40 seconds where instancing eight costs 0.1.
PROTOTYPES = 8

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
# Local frame, identical to `garden.py`'s so a prototype can come from either:
# x tangential, y UP (which on the drum is INWARD, decreasing radius), z along
# the station axis.


def _tag(g, name, t0, t):
    if len(t) > t0:
        g.append((name, t0, len(t)))


def _orient(v, t, t0):
    """Make the primitive just appended wind OUTWARD, by measuring it.

    Every primitive below is a CLOSED solid, and for a closed solid the sign of
    the divergence integral is exactly the orientation -- so the winding does
    not have to be got right by hand for six box faces, two cone rings, a fan
    and a cap. It has to be got right ONCE, here, and measured.

    This is not a shortcut around the winding rule; it is the rule enforced
    rather than intended. `station/interior.py`'s `_selftest` exists because
    hand-wound primitives were inside-out three times in this project (session
    2p: `_box`, `ring_frame`, `wall_panel`) and each fix covered the instance
    rather than the class. An inside-out solid inside a spun drum renders as
    NOTHING -- it is backface-culled, not black -- which is the one failure a
    render cannot show you.
    """
    s = 0.0
    for a, b, c in t[t0:]:
        p, q, r = v[a], v[b], v[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    if s < 0.0:
        for i in range(t0, len(t)):
            a, b, c = t[i]
            t[i] = (a, c, b)


def _box(v, t, g, name, lo, hi):
    t0 = len(t)
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(v)
    v.extend([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
              (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)])
    for a, b, c, d in ((0, 1, 2, 3), (7, 6, 5, 4), (4, 5, 1, 0),
                       (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)):
        t.append((n + a, n + b, n + c))
        t.append((n + a, n + c, n + d))
    _orient(v, t, t0)
    _tag(g, name, t0, t)


def _cone(v, t, g, name, cx, cz, y0, y1, r0, r1, seg, cap=True):
    """A truncated cone about a vertical axis. r1 == 0 gives a spire.

    `cap` closes the bottom. It defaults on and every caller leaves it on, for
    the reason CLAUDE.md records against `garden._cyl`: an open-bottomed solid
    is an object you look straight through from a metre lower down, and on a
    drum floor that curves up in front of you there is always somewhere lower.
    """
    t0 = len(t)
    n = len(v)
    for k in range(seg):
        a = math.tau * k / seg
        v.append((cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)))
    top_apex = r1 <= 1e-6
    if top_apex:
        apex = len(v)
        v.append((cx, y1, cz))
        for k in range(seg):
            t.append((n + k, n + (k + 1) % seg, apex))
    else:
        for k in range(seg):
            a = math.tau * k / seg
            v.append((cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)))
        for k in range(seg):
            k2 = (k + 1) % seg
            t.append((n + k, n + k2, n + seg + k2))
            t.append((n + k, n + seg + k2, n + seg + k))
        # THE TOP CAP, AND ITS ABSENCE WAS THE DEFECT. The first version capped
        # only the bottom, so every cylinder in this module -- lamp columns,
        # gantry legs, silo barrels, the level-3 tree trunk -- was an open tube
        # you could see down from above. On a drum floor that curves up in front
        # of you, "from above" is where the player is standing 300 m away. The
        # self-test now measures boundary edges on every prototype at every
        # level, which is what caught it: 8 open edges on a lamp, 72 on a
        # gantry.
        c1 = len(v)
        v.append((cx, y1, cz))
        for k in range(seg):
            t.append((n + seg + k, n + seg + (k + 1) % seg, c1))
    if cap:
        c = len(v)
        v.append((cx, y0, cz))
        for k in range(seg):
            t.append((n + (k + 1) % seg, n + k, c))
    _orient(v, t, t0)
    _tag(g, name, t0, t)


def _dome(v, t, g, name, cx, cy, cz, r, seg, stacks, squash):
    """A squashed hemisphere-ish blob. The canopy-mass proxy."""
    t0 = len(t)
    rings = []
    for s in range(stacks + 1):
        f = s / stacks
        rr = r * math.cos(f * math.pi / 2.0) if s < stacks else 0.0
        yy = cy + squash * r * math.sin(f * math.pi / 2.0)
        if s == stacks:
            rings.append(("apex", yy))
            continue
        n = len(v)
        for k in range(seg):
            a = math.tau * k / seg
            v.append((cx + rr * math.cos(a), yy, cz + rr * math.sin(a)))
        rings.append((n, yy))
    for s in range(stacks - 1):
        n0, _ = rings[s]
        n1, _ = rings[s + 1]
        for k in range(seg):
            k2 = (k + 1) % seg
            t.append((n0 + k, n0 + k2, n1 + k2))
            t.append((n0 + k, n1 + k2, n1 + k))
    n0, _ = rings[stacks - 1]
    apex = len(v)
    v.append((cx, rings[stacks][1], cz))
    for k in range(seg):
        t.append((n0 + k, n0 + (k + 1) % seg, apex))
    # Closed underneath: a dome open at the bottom is a surface you look
    # straight through from a metre lower down, which is `garden._cyl`'s defect
    # (CLAUDE.md, session 3x) and it is cheap to not repeat.
    n0, y0 = rings[0]
    c = len(v)
    v.append((cx, y0, cz))
    for k in range(seg):
        t.append((n0 + (k + 1) % seg, n0 + k, c))
    _orient(v, t, t0)
    _tag(g, name, t0, t)


def _cyl(v, t, g, name, cx, cz, y0, y1, r, seg):
    _cone(v, t, g, name, cx, cz, y0, y1, r, r, seg, cap=True)


# ---------------------------------------------------------------------------
# Prototypes
# ---------------------------------------------------------------------------
_PROTO = {}


def _tree_proto(i, level):
    """A broadleaf at one of four detail levels.

    Level 0 IS `garden.tree()`. That matters: the near view of the drum floor is
    then drawn by the generator the owner's "sad excuse for a tree" produced,
    rather than by a second tree written here that would drift from it.
    """
    seed = f"{SEED}/tree/{i}"
    if level == 0:
        return gd.tree(seed)
    h = gd.TREE_H_M * (0.75 + 0.5 * _unit(seed, "th"))
    r0 = gd.TRUNK_R_M * (0.85 + 0.3 * _unit(seed, "tk"))
    fork = h * gd.FORK_FRAC
    v, t, g = [], [], []
    # THE CANOPY IS A CLOSED ELLIPSOID, NOT A DOME, AND THE FIRST VERSION GOT
    # THAT WRONG IN A WAY ONLY A RENDER SHOWED. A dome is a hemisphere with a
    # flat disc closing its bottom, which is invisible from above and is the
    # ONLY part of it a standing player sees: the eye is 1.7 m up and the canopy
    # is 5 m up, so every tree past the near switch presented its flat unlit
    # underside and 1,600 of them read as black plates on sticks. The proxy has
    # to be a mass from BELOW, which is where it is looked at.
    #
    # `garden._lobe` is that shape and it is imported rather than rewritten --
    # same rule as level 0 being `garden.tree()` outright.
    if level == 1:
        # Trunk kept as a taper (the root flare is the tree's strongest line at
        # any distance a person can see it from); foliage as three lobes at
        # three different heights plus a crown, because equal heights read as
        # one plate however round each lobe is.
        # THE TRUNK RUNS UP INTO THE CANOPY. It used to stop at the fork and
        # the lobes sat 1-4 m above it with nothing between, so every level-1
        # tree in the render was a black post with a bush hovering over it --
        # which is precisely the failure `garden._limb`'s docstring records
        # ("the canopy floats with nothing holding it up ... only the render
        # showed a tree in three disconnected pieces") and I reproduced it one
        # level down. Level 1 has no triangles to spend on limbs, so the trunk
        # carries on through instead. Inside the foliage it is invisible and it
        # costs nothing: the same 24 triangles, made longer.
        _cone(v, t, g, "garden_trunk", 0.0, 0.0, 0.0, h * 0.72,
              r0 * gd.FLARE_K, r0 * 0.40, 6)
        for j in range(3):
            a = math.tau * (j + 0.3 * _unit(seed, "a1", j)) / 3.0
            reach = gd.TREE_R_M * (0.45 + 0.45 * _unit(seed, "lr", j))
            rise = (h - fork) * (0.30 + 0.55 * _unit(seed, "lh", j))
            gd._lobe(v, t, g, "garden_foliage", reach * 0.8 * math.cos(a),
                     fork + rise, reach * 0.8 * math.sin(a),
                     gd.TREE_R_M * (0.38 + 0.14 * _unit(seed, "lf", j)),
                     seg=6, stacks=3)
        gd._lobe(v, t, g, "garden_foliage", 0.0, h - gd.TREE_R_M * 0.5, 0.0,
                 gd.TREE_R_M * 0.60, seg=6, stacks=3)
        return v, t, g
    if level == 2:
        cy = fork + (h - fork) * 0.55
        _cyl(v, t, g, "garden_trunk", 0.0, 0.0, 0.0, cy, r0 * 0.9, 4)
        gd._lobe(v, t, g, "garden_foliage", 0.0, cy, 0.0, gd.TREE_R_M * 0.92,
                 seg=6, stacks=3)
        return v, t, g
    # Level 3: silhouette only. Three-sided trunk, one four-sided canopy.
    cy = fork + (h - fork) * 0.55
    _cyl(v, t, g, "garden_trunk", 0.0, 0.0, 0.0, cy, r0, 3)
    gd._lobe(v, t, g, "garden_foliage", 0.0, cy, 0.0,
             gd.TREE_R_M * 0.92, seg=4, stacks=3)
    return v, t, g


def _building_proto(i, level):
    """A low-rise block at one of four detail levels.

    Level 0 IS `garden.block_building()`, for the same reason level 0 of a tree
    is `garden.tree()`. Levels 1-3 are massing: the Talia Winters frame reads
    the far side as "low wide grey settlement blocks, terraced rather than
    towered", so the proxy keeps the SETBACK and loses the openings, which is
    the opposite of the usual box.
    """
    seed = f"{SEED}/block/{i}"
    bv, bt, bg, dims = gd.block_building(seed)
    if level == 0:
        return bv, bt, bg, dims
    L, W, H = dims
    v, t, g = [], [], []
    plinth = gd.PLINTH_H_M
    if level <= 1:
        # Plinth, main mass set back, an expressed top slab, a parapet, and one
        # recessed glazing band per storey. Four lines up the facade instead of
        # twenty-two.
        _box(v, t, g, "garden_plinth", (-L / 2, 0.0, -W / 2),
             (L / 2, plinth, W / 2))
        ix = L / 2 - gd.PLINTH_PROUD_M
        iz = W / 2 - gd.PLINTH_PROUD_M
        _box(v, t, g, "garden_block", (-ix, plinth, -iz), (ix, H, iz))
        storeys = max(1, int(round((H - plinth) / gd.STOREY_M)))
        for s in range(storeys):
            y = plinth + (s + 0.42) * (H - plinth) / storeys
            _box(v, t, g, "garden_glazing",
                 (-ix + gd.REVEAL_M, y, -iz - 0.02),
                 (ix - gd.REVEAL_M, y + gd.WIN_H_M, iz + 0.02))
        _box(v, t, g, "garden_cornice",
             (-L / 2, H, -W / 2), (L / 2, H + gd.CORNICE_H_M, W / 2))
        _box(v, t, g, "garden_parapet",
             (-ix, H + gd.CORNICE_H_M, -iz),
             (ix, H + gd.CORNICE_H_M + gd.PARAPET_H_M, iz))
        return v, t, g, dims
    if level == 2:
        _box(v, t, g, "garden_plinth", (-L / 2, 0.0, -W / 2),
             (L / 2, plinth, W / 2))
        ix, iz = L / 2 - gd.PLINTH_PROUD_M, W / 2 - gd.PLINTH_PROUD_M
        _box(v, t, g, "garden_block", (-ix, plinth, -iz), (ix, H, iz))
        _box(v, t, g, "garden_cornice", (-L / 2, H, -W / 2),
             (L / 2, H + gd.CORNICE_H_M, W / 2))
        return v, t, g, dims
    _box(v, t, g, "garden_block", (-L / 2, 0.0, -W / 2), (L / 2, H, W / 2))
    return v, t, g, dims


def _shed_proto(i, level):
    seed = f"{SEED}/shed/{i}"
    L = SHED_L_M * (0.8 + 0.5 * _unit(seed, "L"))
    W = SHED_W_M * (0.8 + 0.5 * _unit(seed, "W"))
    H = SHED_H_M * (0.85 + 0.4 * _unit(seed, "H"))
    v, t, g = [], [], []
    _box(v, t, g, "garden_block", (-L / 2, 0.0, -W / 2), (L / 2, H, W / 2))
    if level <= 1:
        # A monopitch roof and a door. Two lines, and they are the two that say
        # "agricultural building" rather than "box".
        _box(v, t, g, "garden_cornice", (-L / 2 - 0.5, H, -W / 2 - 0.5),
             (L / 2 + 0.5, H + 0.35, W / 2 + 0.5))
        _box(v, t, g, "garden_boundary", (-L * 0.22, 0.0, W / 2 - 0.05),
             (L * 0.22, H * 0.72, W / 2 + 0.12))
    if level == 0:
        for k in range(4):
            x = -L / 2 + (k + 0.5) * L / 4.0
            _box(v, t, g, "garden_pilaster",
                 (x - gd.PILASTER_W_M / 2, 0.0, -W / 2 - gd.PILASTER_PROUD_M),
                 (x + gd.PILASTER_W_M / 2, H, -W / 2))
    return v, t, g


def _silo_proto(i, level):
    seed = f"{SEED}/silo/{i}"
    r = SILO_R_M * (0.85 + 0.35 * _unit(seed, "r"))
    h = SILO_H_M * (0.85 + 0.4 * _unit(seed, "h"))
    seg = (SILO_SEG, 8, 6, 5)[level]
    v, t, g = [], [], []
    _cyl(v, t, g, "garden_tower", 0.0, 0.0, 0.0, h, r, seg)
    _cone(v, t, g, "garden_cap", 0.0, 0.0, h, h + r * 0.85, r, 0.0, seg)
    if level <= 1:
        _cyl(v, t, g, "garden_slab_band", 0.0, 0.0, h * 0.62, h * 0.68,
             r * 1.06, seg)
    return v, t, g


def _gantry_proto(i, level):
    """An irrigation boom: a wheeled truss spanning one parcel. -- INV-452"""
    seed = f"{SEED}/gantry/{i}"
    span = GANTRY_SPAN_M * (0.7 + 0.5 * _unit(seed, "s"))
    v, t, g = [], [], []
    bays = (GANTRY_BAYS, 4, 2, 1)[level]
    seg = (8, 6, 4, 3)[level]
    _cyl(v, t, g, "garden_track_pier", 0.0, 0.0, GANTRY_H_M,
         GANTRY_H_M + GANTRY_R_M * 2, GANTRY_R_M, seg)
    # The boom, laid along local x by rotating a vertical cylinder is more work
    # than laying a thin box, and a box is what a truss chord reads as at these
    # sizes.
    _box(v, t, g, "garden_track_pier",
         (-span / 2, GANTRY_H_M - GANTRY_R_M, -GANTRY_R_M),
         (span / 2, GANTRY_H_M + GANTRY_R_M, GANTRY_R_M))
    for k in range(bays + 1):
        x = -span / 2 + span * k / bays
        _cyl(v, t, g, "garden_track_pier", x, 0.0, 0.0, GANTRY_H_M,
             GANTRY_R_M * 0.8, seg)
    if level <= 1:
        for k in range(bays):
            x0 = -span / 2 + span * k / bays
            x1 = x0 + span / bays
            _box(v, t, g, "garden_rail",
                 (x0, GANTRY_H_M * 0.55, -GANTRY_R_M * 0.5),
                 (x1, GANTRY_H_M * 0.55 + 0.10, GANTRY_R_M * 0.5))
    return v, t, g


def _spire_proto(i, level):
    """29a's tall orange conical spire. -- INV-455"""
    seed = f"{SEED}/spire/{i}"
    h = SPIRE_H_M * (0.78 + 0.45 * _unit(seed, "h"))
    r = SPIRE_R_M * (0.85 + 0.35 * _unit(seed, "r"))
    seg = (SPIRE_SEG, 8, 6, 4)[level]
    v, t, g = [], [], []
    _cyl(v, t, g, "garden_plinth", 0.0, 0.0, 0.0, SPIRE_BASE_H_M, r * 1.22, seg)
    _cone(v, t, g, "garden_stair_accent", 0.0, 0.0, SPIRE_BASE_H_M, h, r, 0.0,
          seg)
    if level <= 1:
        _cyl(v, t, g, "garden_slab_band", 0.0, 0.0, h * 0.34, h * 0.37,
             r * 0.72, seg)
    return v, t, g


def _lamp_proto(_i, level):
    v, t, g = [], [], []
    seg = (8, 6, 4, 3)[level]
    _cyl(v, t, g, "garden_lamp_column", 0.0, 0.0, 0.0, LAMP_H_M, LAMP_R_M, seg)
    _box(v, t, g, "garden_lamp_head",
         (-gd.LAMP_HEAD_M, LAMP_H_M, -gd.LAMP_HEAD_M / 2),
         (gd.LAMP_HEAD_M, LAMP_H_M + 0.16, gd.LAMP_HEAD_M / 2))
    return v, t, g


def _jetty_proto(i, level):
    seed = f"{SEED}/jetty/{i}"
    L = JETTY_L_M * (0.8 + 0.5 * _unit(seed, "L"))
    v, t, g = [], [], []
    _box(v, t, g, "garden_sleeper", (-JETTY_W_M / 2, JETTY_H_M - 0.18, 0.0),
         (JETTY_W_M / 2, JETTY_H_M, L))
    posts = (7, 5, 3, 2)[level]
    for k in range(posts):
        z = L * (k + 0.5) / posts
        for sx in (-1, 1):
            _box(v, t, g, "garden_sleeper",
                 (sx * JETTY_W_M / 2 - 0.14, -1.6, z - 0.14),
                 (sx * JETTY_W_M / 2, JETTY_H_M - 0.18, z))
    return v, t, g


_PROTO_BUILDERS = {
    "tree": _tree_proto,
    "shed": _shed_proto,
    "silo": _silo_proto,
    "gantry": _gantry_proto,
    "spire": _spire_proto,
    "lamp": _lamp_proto,
    "jetty": _jetty_proto,
}


def prototype(kind, index, level):
    """(verts, tris, groups) for one prototype, cached."""
    key = (kind, index % PROTOTYPES, level)
    if key in _PROTO:
        return _PROTO[key]
    if kind == "town_block":
        v, t, g, _d = _building_proto(key[1], level)
    else:
        v, t, g = _PROTO_BUILDERS[kind](key[1], level)
    _PROTO[key] = (v, t, g)
    return _PROTO[key]


def prototype_dims(index):
    """(L, W, H) of a town block prototype, for plot fitting."""
    return _building_proto(index % PROTOTYPES, 0)[3]


def proto_tris(kind, index, level):
    return len(prototype(kind, index, level)[1])


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def _to_world(local, angle_deg, z_m, ground_r, yaw=0.0, scale=1.0):
    """Local (x tangential, y up/inward, z axial) -> station world coordinates.

    Same mapping as `garden.place()`, plus a yaw about the local vertical --
    which `place()` has no parameter for and which is the difference between a
    scatter and a parade.
    """
    ca, sa = math.cos(yaw), math.sin(yaw)
    out = []
    a0 = math.radians(angle_deg)
    inv = 1.0 / max(ground_r, 1e-9)
    for x, y, z in local:
        xr = (x * ca - z * sa) * scale
        zr = (x * sa + z * ca) * scale
        r = ground_r - y * scale
        a = a0 + xr * inv
        out.append((r * math.cos(a), r * math.sin(a), z_m + zr))
    return out


def _ground(u, w):
    """(height_m, kind) at lattice fractions, straight off drum_ground."""
    return dg.sample(u % 1.0, min(max(w, 0.0), 1.0))


def _uw_to_station(u, w):
    return (u % 1.0) * 360.0, dg.Z0 + w * (dg.Z1 - dg.Z0)


def _station_to_uw(angle_deg, z_m):
    return (angle_deg / 360.0) % 1.0, (z_m - dg.Z0) / (dg.Z1 - dg.Z0)


# ---------------------------------------------------------------------------
# THE PARCEL BOUNDARY, INVERTED
# ---------------------------------------------------------------------------
# `drum_ground._parcel()` maps (u, w) forward to a warped parcel coordinate
# (sa, sz). A hedgerow needs the INVERSE: given a boundary at sa = k, where is
# it in u? The warp is at most `PARCEL_WARP_M` = 34 m against an 87.4 m cell, so
# the map is a contraction and two fixed-point steps land inside 0.1 m. Solving
# it rather than approximating matters because the hedge GEOMETRY has to sit on
# the same line as the hedge TAG, and the tag comes from the forward map.


def _invert_parcel_a(sa_target, w, iters=3):
    """u such that `_parcel`'s sa equals `sa_target` at this w."""
    cells_a = dg.PARCELS_A
    circ = 2.0 * math.pi * dg.FLOOR_R
    size_a = circ / cells_a
    seed = dg.SEED + "/parcel"
    u = sa_target / cells_a
    for _ in range(iters):
        wa = dg.PARCEL_WARP_M * dg._value_noise(u % 1.0, w, 5, 7, seed + "/warpA")
        u = (sa_target - wa / size_a) / cells_a
    return u % 1.0


def _invert_parcel_z(sz_target, u, iters=3):
    cells_z = dg.PARCELS_Z
    span = dg.Z1 - dg.Z0
    size_z = span / cells_z
    seed = dg.SEED + "/parcel"
    w = sz_target / cells_z
    for _ in range(iters):
        wz = dg.PARCEL_WARP_M * dg._value_noise(u, min(max(w, 0.0), 1.0), 7, 5,
                                                seed + "/warpZ")
        w = (sz_target - wz / size_z) / cells_z
    return w


_ARABLE_KINDS = {"arable"} | {f"arable{i}" for i in range(dg.CROPS)} | {"hedge"}


def _is_field(u, w):
    """Is this point open arable ground a hedge may stand on?

    A road, a verge, the rim fade and any non-arable band all say no -- which is
    what breaks a hedgerow where a trunk road crosses it, and 33a shows exactly
    that: the road runs THROUGH the field pattern, not around it.
    """
    _h, kind = _ground(u, w)
    return kind in _ARABLE_KINDS


# ---------------------------------------------------------------------------
# The instance field
# ---------------------------------------------------------------------------
# One list for point features and one for polylines, built once and cached. The
# field is eye-independent by construction: nothing below looks at a camera.
# That separation is what lets `dressing_cost()` price a viewpoint in
# microseconds and `--derive` sweep 36 of them.

_FIELD = None


class Feature:
    """A point feature. Deliberately not a dataclass -- 4,000 of these are
    built on every cold import of the field and __slots__ halves the cost."""
    __slots__ = ("kind", "proto", "angle_deg", "z_m", "ground_r", "yaw",
                 "scale", "members", "radius_m", "band")

    def __init__(self, kind, proto, angle_deg, z_m, ground_r, yaw=0.0,
                 scale=1.0, members=(), radius_m=0.0, band=""):
        self.kind = kind
        self.proto = proto
        self.angle_deg = angle_deg
        self.z_m = z_m
        self.ground_r = ground_r
        self.yaw = yaw
        self.scale = scale
        self.members = members
        self.radius_m = radius_m
        self.band = band

    def position(self):
        a = math.radians(self.angle_deg)
        return (self.ground_r * math.cos(a), self.ground_r * math.sin(a),
                self.z_m)


class Line:
    """A polyline feature -- a hedgerow, a reed margin, a park hedge."""
    __slots__ = ("kind", "points", "height_m", "width_m", "band")

    def __init__(self, kind, points, height_m, width_m, band=""):
        self.kind = kind
        self.points = points          # [(angle_deg, z_m, ground_r)]
        self.height_m = height_m
        self.width_m = width_m
        self.band = band

    def length_m(self):
        tot = 0.0
        for i in range(len(self.points) - 1):
            a0, z0, r0 = self.points[i]
            a1, z1, r1 = self.points[i + 1]
            da = math.radians(a1 - a0) * 0.5 * (r0 + r1)
            tot += math.hypot(da, z1 - z0)
        return tot

    def centre(self):
        i = len(self.points) // 2
        a, z, r = self.points[i]
        return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)


def _band_at(u):
    """Land-use name at circumferential fraction u, from LAND_USE via
    drum_ground -- never a second copy of the band table."""
    return dg._band_weights(u % 1.0)[0][0]


def _in_townscape_keepout(angle_deg, z_m):
    da = abs(((angle_deg - 112.0 + 180.0) % 360.0) - 180.0)
    return da < TOWNSCAPE_KEEPOUT_DEG and abs(z_m - 4900.0) < TOWNSCAPE_KEEPOUT_M


def _hedgerows():
    """Every arable parcel boundary, as a polyline that stops at roads."""
    lines = []
    circ = 2.0 * math.pi * dg.FLOOR_R
    span = dg.Z1 - dg.Z0
    size_a = circ / dg.PARCELS_A
    size_z = span / dg.PARCELS_Z
    step = HEDGE_STEP_M[0] * 2.6      # placement spacing; geometry resamples

    def emit(pts):
        if len(pts) >= 2:
            lines.append(Line("hedgerow", pts, HEDGE_H_M, HEDGE_W_M, "arable"))

    # Boundaries of constant sa (running along the axis).
    for ia in range(dg.PARCELS_A):
        n = max(3, int(size_z / step))
        run = []
        for k in range(n + 1):
            w = k / n
            u = _invert_parcel_a(float(ia), w)
            if not _is_field(u, w):
                emit(run)
                run = []
                continue
            h, _k = _ground(u, w)
            a, z = _uw_to_station(u, w)
            run.append((a, z, dg.FLOOR_R - h))
        emit(run)
    # Boundaries of constant sz (running around the drum).
    for iz in range(1, dg.PARCELS_Z):
        n = max(3, int(size_a / step))
        for ia in range(dg.PARCELS_A):
            run = []
            for k in range(n + 1):
                sa = ia + k / n
                u = _invert_parcel_a(sa, float(iz) / dg.PARCELS_Z)
                w = _invert_parcel_z(float(iz), u)
                if not (0.0 <= w <= 1.0) or not _is_field(u, w):
                    emit(run)
                    run = []
                    continue
                h, _k = _ground(u, w)
                a, z = _uw_to_station(u, w)
                run.append((a, z, dg.FLOOR_R - h))
            emit(run)
    return lines


def _standards(lines):
    """Trees left uncut in a hedge line, one per HEDGE_STANDARD_M."""
    out = []
    for i, ln in enumerate(lines):
        L = ln.length_m()
        n = int(L / HEDGE_STANDARD_M)
        for k in range(n):
            f = (k + 0.5 + 0.4 * (_unit(SEED, "std", i, k) - 0.5)) / max(n, 1)
            j = min(int(f * (len(ln.points) - 1)), len(ln.points) - 2)
            a, z, r = ln.points[j]
            out.append(Feature("tree", int(_unit(SEED, "sp", i, k) * PROTOTYPES),
                               a, z, r,
                               yaw=math.tau * _unit(SEED, "sy", i, k),
                               scale=0.85 + 0.45 * _unit(SEED, "ss", i, k),
                               band="arable"))
    return out


def _clumps():
    """Tree masses: 34b's "darker tree masses" in arable, a planted park in the
    parkland band."""
    out = []
    circ = 2.0 * math.pi * dg.FLOOR_R
    span = dg.Z1 - dg.Z0
    na = max(4, int(round(circ / CLUMP_SPACING_M)))
    nz = max(4, int(round(span / CLUMP_SPACING_M)))
    for ia in range(na):
        for iz in range(nz):
            ju = (ia + 0.5 + CLUMP_JITTER * (_unit(SEED, "cu", ia, iz) - 0.5) * 2) / na
            jw = (iz + 0.5 + CLUMP_JITTER * (_unit(SEED, "cw", ia, iz) - 0.5) * 2) / nz
            if not (0.02 < jw < 0.98):
                continue
            h, kind = _ground(ju, jw)
            band = _band_at(ju)
            if kind in ("road", "ring_road", "rim", "water_surface"):
                continue
            if band == "arable":
                p = CLUMP_P_ARABLE
            elif band == "parkland":
                p = CLUMP_P_PARKLAND
            else:
                continue
            if _unit(SEED, "cp", ia, iz) > p:
                continue
            a, z = _uw_to_station(ju, jw)
            if _in_townscape_keepout(a, z):
                continue
            n = CLUMP_MIN + int(_unit(SEED, "cn", ia, iz) * (CLUMP_MAX - CLUMP_MIN))
            rad = CLUMP_R_MIN_M + _unit(SEED, "cr", ia, iz) * (
                CLUMP_R_MAX_M - CLUMP_R_MIN_M)
            members = []
            for k in range(n):
                ang = math.tau * _unit(SEED, "ma", ia, iz, k)
                rr = rad * math.sqrt(_unit(SEED, "mr", ia, iz, k))
                members.append((rr * math.cos(ang), rr * math.sin(ang),
                                int(_unit(SEED, "mp", ia, iz, k) * PROTOTYPES),
                                math.tau * _unit(SEED, "my", ia, iz, k),
                                0.75 + 0.5 * _unit(SEED, "ms", ia, iz, k)))
            out.append(Feature("copse", 0, a, z, dg.FLOOR_R - h,
                               members=tuple(members), radius_m=rad, band=band))
    return out


def _farm():
    """Farmsteads and irrigation gantries on the arable parcels. -- INV-452"""
    out = []
    for ia in range(dg.PARCELS_A):
        for iz in range(dg.PARCELS_Z):
            u = _invert_parcel_a(ia + 0.5, (iz + 0.5) / dg.PARCELS_Z)
            w = _invert_parcel_z(iz + 0.5, u)
            if not (0.02 < w < 0.98) or not _is_field(u, w):
                continue
            a, z = _uw_to_station(u, w)
            if _in_townscape_keepout(a, z):
                continue
            r0 = _unit(SEED, "farm", ia, iz)
            if r0 < 1.0 / FARMSTEAD_PER_PARCELS:
                # The steading sits at a parcel corner, where a track would
                # reach it, not in the middle of the crop.
                fu = _invert_parcel_a(ia + 0.12, (iz + 0.18) / dg.PARCELS_Z)
                fw = _invert_parcel_z(iz + 0.18, fu)
                if 0.02 < fw < 0.98 and _is_field(fu, fw):
                    h, _k = _ground(fu, fw)
                    fa, fz = _uw_to_station(fu, fw)
                    yaw = math.tau * _unit(SEED, "fy", ia, iz)
                    out.append(Feature("shed", ia + iz, fa, fz,
                                       dg.FLOOR_R - h, yaw=yaw, band="arable"))
                    # The silo stands beside the shed, offset along the yard.
                    # Its OWN ground is sampled: a steading near a band edge
                    # would otherwise put the silo in the lake, which is what
                    # the "no feature is in the wrong land-use band" assertion
                    # caught on the first run.
                    d = SHED_L_M * 0.9
                    sa = fa + math.degrees(d * math.cos(yaw) / dg.FLOOR_R)
                    sz = fz + d * math.sin(yaw)
                    su, sw = _station_to_uw(sa, sz)
                    sh, skind = _ground(su, sw)
                    if _band_at(su) == "arable" and skind in _ARABLE_KINDS:
                        out.append(Feature("silo", ia * 3 + iz, sa, sz,
                                           dg.FLOOR_R - sh, band="arable"))
            if _unit(SEED, "gant", ia, iz) < 1.0 / GANTRY_PER_PARCELS:
                h, _k = _ground(u, w)
                # A boom runs ACROSS the furrows, and the furrows run along the
                # axis (drum_ground: "you plough along the direction of travel"),
                # so the boom is circumferential -- local x, yaw 0.
                out.append(Feature("gantry", ia + 2 * iz, a, z,
                                   dg.FLOOR_R - h, band="arable"))
    return out


def _park():
    """Clipped hedge runs and the orange spires. 29a."""
    lines, points = [], []
    circ = 2.0 * math.pi * dg.FLOOR_R
    spans = [(lo, hi) for lo, hi, nm, _r in dg._bands() if nm == "parkland"]
    for si, (lo, hi) in enumerate(spans):
        width_m = (hi - lo) * circ
        na = max(2, int(width_m / PARK_HEDGE_SPACING_M))
        nz = max(2, int((dg.Z1 - dg.Z0) / PARK_HEDGE_SPACING_M))
        for ia in range(na):
            for iz in range(nz):
                if _unit(SEED, "ph", si, ia, iz) > 0.55:
                    continue
                u = lo + (ia + 0.5 + 0.6 * (_unit(SEED, "phu", si, ia, iz) - 0.5)) \
                    * (hi - lo) / na
                w = (iz + 0.5 + 0.6 * (_unit(SEED, "phw", si, ia, iz) - 0.5)) / nz
                if not (0.03 < w < 0.97):
                    continue
                h, kind = _ground(u, w)
                if kind not in ("parkland",):
                    continue
                L = PARK_HEDGE_LEN_M[0] + _unit(SEED, "pl", si, ia, iz) * (
                    PARK_HEDGE_LEN_M[1] - PARK_HEDGE_LEN_M[0])
                yaw = math.tau * _unit(SEED, "py", si, ia, iz)
                pts = []
                n = max(2, int(L / 12.0))
                for k in range(n + 1):
                    d = (k / n - 0.5) * L
                    du = math.degrees(d * math.cos(yaw) / dg.FLOOR_R) / 360.0
                    dz = d * math.sin(yaw) / (dg.Z1 - dg.Z0)
                    uu, ww = u + du, w + dz
                    hh, _kk = _ground(uu, ww)
                    aa, zz = _uw_to_station(uu, ww)
                    pts.append((aa, zz, dg.FLOOR_R - hh))
                lines.append(Line("park_hedge", pts, PARK_HEDGE_H_M,
                                  PARK_HEDGE_W_M, "parkland"))
        # The spires, in groups.
        for gi in range(SPIRE_GROUPS):
            u = lo + (0.12 + 0.76 * _unit(SEED, "spu", si, gi)) * (hi - lo)
            w = 0.06 + 0.88 * _unit(SEED, "spw", si, gi)
            h, kind = _ground(u, w)
            if kind not in ("parkland",):
                continue
            a, z = _uw_to_station(u, w)
            n = SPIRE_PER_GROUP[0] + int(_unit(SEED, "spn", si, gi) * (
                SPIRE_PER_GROUP[1] - SPIRE_PER_GROUP[0] + 1))
            for k in range(n):
                ang = math.tau * _unit(SEED, "sga", si, gi, k)
                rr = 6.0 + 16.0 * _unit(SEED, "sgr", si, gi, k)
                da = math.degrees(rr * math.cos(ang) / dg.FLOOR_R)
                dz = rr * math.sin(ang)
                hh, _kk = _ground(u + da / 360.0, w + dz / (dg.Z1 - dg.Z0))
                points.append(Feature("spire", si * 5 + gi + k, a + da, z + dz,
                                      dg.FLOOR_R - hh, band="parkland"))
    return lines, points


def _water():
    """Reed margins and jetties along the lake shore."""
    lines, points = [], []
    circ = 2.0 * math.pi * dg.FLOOR_R
    spans = [(lo, hi) for lo, hi, nm, _r in dg._bands() if nm == "water"]
    nz = max(4, int((dg.Z1 - dg.Z0) / REED_SPACING_M))
    for si, (lo, hi) in enumerate(spans):
        for edge, u_scan in (("lo", lo), ("hi", hi)):
            for iz in range(nz):
                w = (iz + 0.5) / nz
                if not (0.03 < w < 0.97):
                    continue
                # Walk in from the band edge until the ground stops being shore
                # -- the shoreline is where the flooded bowl meets it, and it
                # moves with the terrain rather than sitting on the band edge.
                found = None
                for step in range(26):
                    f = step / 25.0 * 0.5
                    u = u_scan + (f if edge == "lo" else -f) * (hi - lo)
                    _h, kind = _ground(u, w)
                    if kind == "water_surface":
                        break
                    if kind == "shore":
                        found = u
                if found is None:
                    continue
                if _unit(SEED, "reed", si, edge, iz) < 0.62:
                    L = REED_RUN_M[0] + _unit(SEED, "rl", si, edge, iz) * (
                        REED_RUN_M[1] - REED_RUN_M[0])
                    n = max(2, int(L / 12.0))
                    pts = []
                    for k in range(n + 1):
                        ww = w + (k / n - 0.5) * L / (dg.Z1 - dg.Z0)
                        hh, _kk = _ground(found, ww)
                        aa, zz = _uw_to_station(found, ww)
                        pts.append((aa, zz, dg.FLOOR_R - hh))
                    lines.append(Line("reeds", pts, REED_H_M, REED_W_M, "water"))
                if _unit(SEED, "jetty", si, edge, iz) < \
                        REED_SPACING_M / JETTY_SPACING_M:
                    hh, _kk = _ground(found, w)
                    aa, zz = _uw_to_station(found, w)
                    # A jetty runs INTO the water, so its local +z points across
                    # the band toward the centreline.
                    yaw = math.pi / 2.0 if edge == "lo" else -math.pi / 2.0
                    points.append(Feature("jetty", si * 3 + iz, aa, zz,
                                          dg.FLOOR_R - hh, yaw=yaw, band="water"))
    return lines, points


def _town():
    """Buildings on every settlement block on the drum. -- INV-457"""
    out = []
    circ = 2.0 * math.pi * dg.FLOOR_R
    na = dg.CELLS_A // dg.BLOCK_CELLS
    nz = dg.CELLS_Z // dg.BLOCK_CELLS
    block_a_m = circ / na
    block_z_m = (dg.Z1 - dg.Z0) / nz
    for ia in range(na):
        for iz in range(nz):
            u = (ia + 0.5) / na
            w = (iz + 0.5) / nz
            if _band_at(u) != "settlement":
                continue
            h, kind = _ground(u, w)
            if kind not in ("settlement", "verge"):
                continue
            a0, z0 = _uw_to_station(u, w)
            if _in_townscape_keepout(a0, z0):
                continue
            n = TOWN_MIN + int(_unit(SEED, "tn", ia, iz) * (TOWN_MAX - TOWN_MIN + 1))
            usable_a = block_a_m - 2 * TOWN_INSET_M
            usable_z = block_z_m - 2 * TOWN_INSET_M
            cols = 2 if n > 2 else 1
            rows = int(math.ceil(n / cols))
            for k in range(n):
                cx = (k % cols + 0.5) / cols - 0.5
                cz = (k // cols + 0.5) / rows - 0.5
                jx = 0.30 * (_unit(SEED, "tx", ia, iz, k) - 0.5)
                jz = 0.30 * (_unit(SEED, "tz", ia, iz, k) - 0.5)
                da = (cx + jx) * usable_a
                dz = (cz + jz) * usable_z
                uu = u + math.degrees(da / dg.FLOOR_R) / 360.0
                ww = w + dz / (dg.Z1 - dg.Z0)
                hh, kk = _ground(uu, ww)
                if kk not in ("settlement", "verge"):
                    continue
                aa, zz = _uw_to_station(uu, ww)
                # A block faces its street: yaw is quantised to the grid with a
                # few degrees of slop, because a town whose buildings are all
                # exactly square to the plan reads as a tile pattern.
                yaw = (math.pi / 2.0) * int(4 * _unit(SEED, "ty", ia, iz, k)) \
                    + math.radians(6.0 * (_unit(SEED, "ts", ia, iz, k) - 0.5))
                out.append(Feature("town_block",
                                   int(_unit(SEED, "tp", ia, iz, k) * PROTOTYPES),
                                   aa, zz, dg.FLOOR_R - hh, yaw=yaw,
                                   band="settlement"))
            # Street lamps down the avenue on two sides of the block.
            for side in (0, 1):
                lamps = max(1, int((block_z_m if side else block_a_m) / LAMP_PITCH_M))
                for k in range(lamps):
                    f = (k + 0.5) / lamps - 0.5
                    if side:
                        da = -block_a_m * 0.5 + 2.0
                        dz = f * block_z_m
                    else:
                        da = f * block_a_m
                        dz = -block_z_m * 0.5 + 2.0
                    uu = u + math.degrees(da / dg.FLOOR_R) / 360.0
                    ww = w + dz / (dg.Z1 - dg.Z0)
                    if _band_at(uu) != "settlement":
                        continue      # a block on the band edge; the street
                    hh, _kk = _ground(uu, ww)   # outside it is a field track
                    aa, zz = _uw_to_station(uu, ww)
                    out.append(Feature("lamp", 0, aa, zz, dg.FLOOR_R - hh,
                                       band="settlement"))
    return out


def field(rebuild=False):
    """The whole drum's dressing, eye-independent. Cached.

    Returns {"points": [Feature], "lines": [Line]}.
    """
    global _FIELD, _STATIC_ITEMS
    if _FIELD is not None and not rebuild:
        return _FIELD
    # The near rung's caches key on the ground lattice, so a rebuild has to
    # clear them too. THIS CALL WAS MISSING and `_lattice_sample`'s docstring
    # claimed it existed -- a caller asserted in prose and absent from the code,
    # which is this project's oldest defect written down in my own comment.
    # Found by re-reading, not by a gate; a stale lattice memo across a
    # `configure()` would put near cover on the previous drum's heights.
    reset_near_cache()
    _STATIC_ITEMS = None
    hedges = _hedgerows()
    park_lines, spires = _park()
    water_lines, water_points = _water()
    points = []
    points += _standards(hedges)
    points += _clumps()
    points += _farm()
    points += spires
    points += water_points
    points += _town()
    _FIELD = {"points": points, "lines": hedges + park_lines + water_lines}
    return _FIELD


# ---------------------------------------------------------------------------
# LOD
# ---------------------------------------------------------------------------

def switch_distances(scale=None):
    s = LOD_SCALE_M if scale is None else scale
    return tuple(s * r for r in LOD_RATIOS)


def _level(distance_m, sw):
    for i, d in enumerate(sw):
        if distance_m < d:
            return i
    return len(sw)


# ---------------------------------------------------------------------------
# CULLING, and why it is by AREA rather than by height
# ---------------------------------------------------------------------------
# A street lamp is 4.4 m tall and 0.30 m wide. At the level-2 switch it is 24
# pixels HIGH -- which by a height criterion is comfortably visible -- and 1.6
# pixels WIDE, which is a hairline the renderer resolves into a faint smear and
# which costs 24 triangles each over 780 of them. Height alone is the wrong
# measure for anything thin, and thin street furniture is most of what a town
# scatter contains.
#
# So the criterion is projected AREA: the prototype's own bounding height times
# its own bounding width, in square pixels at the distance the level begins.
# Both numbers are measured off the prototype mesh rather than declared, so an
# object that grows stops being culled without anybody editing a table.
#
# 60 px2 is a little under 8x8 pixels. Bounded BELOW by ~16 px2, at which
# objects visibly wink out at the switch; bounded ABOVE by ~250 px2, at which
# copses start disappearing off the far side of the drum -- which is the
# content the reviewer's finding is about. -- INV-458
CULL_PX2 = 60.0


def _proto_extent(kind, index, level):
    """(height_m, width_m) of a prototype's bounding box. Measured, not stated."""
    v, _t, _g = prototype(kind, index, level)
    if not v:
        return 0.0, 0.0
    ys = [p[1] for p in v]
    xs = [p[0] for p in v]
    zs = [p[2] for p in v]
    return max(ys) - min(ys), max(max(xs) - min(xs), max(zs) - min(zs))


def _culled(kind, index, level, sw, scale=1.0, radius_m=0.0):
    """Is this feature below the visible-area floor at this level?

    Level 0 is never culled -- something within the first switch distance is
    close enough to walk up to, and CLAUDE.md's rule is that the near view is
    where craft is judged.
    """
    if level <= 0:
        return False
    d = sw[min(level, len(sw)) - 1]
    if radius_m > 0.0:
        h, _w = _proto_extent("tree", index, level)
        w = 2.0 * radius_m
        h *= scale
    else:
        h, w = _proto_extent(kind, index, level)
        h *= scale
        w *= scale
    return _pixels(h, d) * _pixels(w, d) < CULL_PX2


# A TREE INSIDE A MASS RENDERS ONE LEVEL COARSER THAN A TREE ON ITS OWN, and
# that is not a saving dressed up as a principle. 34b shows tree MASSES: what
# reads at any distance past arm's length is the outline of the group and the
# gaps between groups, and every member but the front rank is occluded by the
# ones in front of it. Measured, it is the difference between a copse costing
# 1,600 triangles and 400, over a hundred copses -- which is most of the reason
# the LOD scale below could be pushed out from 91 m to 113 m, i.e. the reason
# the trees a player walks up to are full-detail at all.
def _member_level(level):
    return min(3, level + 1)


def _feature_tris(f, level):
    if f.kind == "copse":
        if level >= 3:
            return _clump_mass_tris()
        ml = _member_level(level)
        return sum(proto_tris("tree", m[2], ml) for m in f.members)
    return proto_tris(f.kind, f.proto, level)


_CLUMP_MASS_TRIS = None


def _clump_mass_tris():
    global _CLUMP_MASS_TRIS
    if _CLUMP_MASS_TRIS is None:
        v, t, g = [], [], []
        _dome(v, t, g, "garden_foliage", 0.0, 0.0, 0.0, 1.0, 8, 3, 0.5)
        _CLUMP_MASS_TRIS = len(t)
    return _CLUMP_MASS_TRIS


def _line_tris(ln, level):
    step = HEDGE_STEP_M[level]
    n = max(1, int(round(ln.length_m() / step)))
    # Four quads round the section, two triangles each, plus two end caps.
    return n * 8 + 4


def dressing_cost(eye, scale=None):
    """Triangles this eye would build, without building anything.

    Same instrument as `drum_ground.visible_cost` and for the same reason: the
    worst case is the only one a budget gate cares about, and a sweep that costs
    fifteen seconds a viewpoint is a sweep nobody runs.
    """
    sw = switch_distances(scale)
    fld = field()
    total = 0
    per = [0, 0, 0, 0]
    for f in fld["points"]:
        d = math.dist(f.position(), eye)
        lv = _level(d, sw)
        if _culled(f.kind, f.proto, lv, sw, f.scale, f.radius_m):
            continue
        total += _feature_tris(f, lv)
        per[lv] += 1
    for ln in fld["lines"]:
        d = math.dist(ln.centre(), eye)
        lv = _level(d, sw)
        total += _line_tris(ln, lv)
        per[lv] += 1
    # THE NEAR RUNG IS PART OF THE COST, not an extra on top of it. Its price is
    # independent of `scale` -- it has its own radius ladder -- so `--derive`
    # solves the far chain against whatever is left after the near field is
    # paid for, which is the trade CLAUDE.md's rule 1 asks for: the near view
    # is where craft is judged, so it is bought first.
    total += near_cost(eye)
    return total, per


# WHAT THE REST OF THE DRUM COSTS, MEASURED FROM THE SAME PARTS THE SHOT EMITS.
# `export_scene.drum_parts` is the one list of what a drum frame contains; this
# prices the parts of it that do not depend on the eye. Recorded as a pin
# because building them costs 40 s and no gate should pay that at import.
DRUM_FIXED_TRIS = 104_374


def drum_fixed_cost():
    """(total, per part) for everything in the drum shot that is eye-independent."""
    import core_tube as ct                                      # noqa: PLC0415
    import tram as _tram                                        # noqa: PLC0415
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    per = {}
    for end in ("fore", "aft"):
        per[f"endcap_{end}"] = len(it.drum_end_cap(schema, profile, sector,
                                                   end=end)[1])
    per["guideways"] = len(it.drum_guideways(schema, profile, sector)[1])
    per["spokes"] = len(it.drum_spokes(schema, profile, sector)[1])
    per["core"] = len(ct.core_axis(schema, profile, sector)[1])
    # `budget.DRUM["trams"]` is what `export_scene --shot drum` ships. Read,
    # not restated.
    import budget as B                                          # noqa: PLC0415
    per["trams"] = len(_tram.drum_trams(schema, profile, sector,
                                        per_guideway=B.DRUM["trams"],
                                        glazed=True)[1])
    per["townscape"] = len(gd.townscape(schema, profile, sector)[1])
    return sum(per.values()), per


def drum_worst_eye(samples=12, fixed=None):
    """The most expensive DRUM FRAME, priced at one eye at a time.

    Ground and dressing are both LOD-resolved against the eye and they peak in
    different places, so the sum of their separate worst cases is a bound no
    frame ever draws. This asks the question a renderer answers.
    """
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    fx = DRUM_FIXED_TRIS if fixed is None else fixed
    worst = {"triangles": 0}
    for i in range(samples):
        ang = 360.0 * i / samples
        for f in (0.05, 0.5, 0.95):
            z = dg.Z0 + f * (dg.Z1 - dg.Z0)
            eye, _up = dg.stand_on_ground(schema, profile, sector, ang, z)
            g, _pg = dg.visible_cost(eye)
            d, _pd = dressing_cost(eye)
            if fx + g + d > worst["triangles"]:
                worst = {"triangles": fx + g + d, "fixed": fx, "ground": g,
                         "dressing": d, "at": (round(ang, 1), round(z, 1))}
    return worst


def worst_case_cost(samples=12, scale=None):
    """The most expensive place to stand. Swept, not sampled once."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    worst = (0, None, None)
    for i in range(samples):
        ang = 360.0 * i / samples
        for f in (0.05, 0.5, 0.95):
            z = dg.Z0 + f * (dg.Z1 - dg.Z0)
            eye, _up = dg.stand_on_ground(schema, profile, sector, ang, z)
            n, per = dressing_cost(eye, scale)
            if n > worst[0]:
                worst = (n, (round(ang, 1), round(z, 1)), per)
    return {"triangles": worst[0], "at": worst[1], "per_level": worst[2]}


def derive_lod_scale(budget=None, samples=12, lo=20.0, hi=600.0, iters=22):
    """The largest LOD scale whose worst standing position fits the budget.

    This is the honest form of the argument in the module docstring: the chain
    is bought with triangles, so it is solved against triangles. Bisection
    because cost is monotone in the scale -- a longer switch distance can only
    move a feature to a finer level, never a coarser one.
    """
    budget = DRESSING_TRIS if budget is None else budget
    if worst_case_cost(samples, lo)["triangles"] > budget:
        return 0.0, worst_case_cost(samples, lo)["triangles"]
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if worst_case_cost(samples, mid)["triangles"] <= budget:
            lo = mid
        else:
            hi = mid
    return lo, worst_case_cost(samples, lo)["triangles"]


def lod_report(scale=None):
    """What each switch throws away, in pixels at the distance it happens.

    The pixel column is an OUTPUT of the budget solve, not an input to it. Read
    it as "this is what the 120,000-triangle allowance bought", which is the
    only honest reading.
    """
    sw = switch_distances(scale)
    # The finest feature each level still carries, measured off the prototypes
    # rather than asserted: the median edge length of the level's own mesh.
    rows = []
    for lv in range(4):
        v, t, _g = prototype("tree", 0, lv)
        edges = []
        for a, b, c in t:
            for p, q in ((a, b), (b, c), (c, a)):
                edges.append(math.dist(v[p], v[q]))
        edges.sort()
        med = edges[len(edges) // 2] if edges else 0.0
        d = sw[lv - 1] if 0 < lv <= len(sw) else None
        rows.append({
            "level": lv,
            "tree_triangles": len(t),
            "median_edge_m": round(med, 3),
            "used_from_m": round(d, 1) if d is not None else 0.0,
            "omitted_feature_px": (round(_pixels(rows[lv - 1]["median_edge_m"], d), 2)
                                   if d else None),
        })
    return {"switch_m": [round(x, 1) for x in sw], "levels": rows}


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _emit(V, T, G, local, groups, angle_deg, z_m, ground_r, yaw, scale):
    off = len(V)
    V.extend(_to_world(local, angle_deg, z_m, ground_r, yaw, scale))
    t0 = len(T)
    return off, t0


def _append(V, T, G, local_v, local_t, local_g, angle_deg, z_m, ground_r,
            yaw=0.0, scale=1.0):
    off = len(V)
    V.extend(_to_world(local_v, angle_deg, z_m, ground_r, yaw, scale))
    t0 = len(T)
    T.extend((a + off, b + off, c + off) for a, b, c in local_t)
    per = [None] * len(local_t)
    for nm, lo, hi in local_g:
        for i in range(lo, hi):
            per[i] = nm
    if any(x is None for x in per):
        raise ValueError("a prototype emitted a triangle in no group span")
    G.extend(per)


def _ribbon(V, T, G, points, height_m, width_m, name_side, name_top, step_m,
            wobble_m=0.0, seed="r"):
    """A hedge/reed run: resample the polyline, then extrude a cross-section.

    A CLOSED TUBE, not a folded sheet -- four quads round a four-point section
    plus two end caps. The first version of this emitted three quads and left
    the underside open, on the argument that a hedge sits on the ground and
    nobody sees under it; the self-test caught 18 open edges on a six-point run
    and the argument is wrong anyway, because the ground under a hedgerow is
    the parcel bank, which the hedge stands proud of by 0.22 m.

    DETAIL COMES FROM `step_m`, NOT FROM DROPPING FACES. Resampling by arc
    length means the level chooses how many cross-sections a run gets, which
    moves the cost by 13x between the finest and coarsest levels without ever
    making the object non-manifold.
    """
    # Resample by arc length so the segment count follows the level rather than
    # the placement spacing.
    pts = points
    if len(pts) < 2:
        return
    seg = []
    total = 0.0
    for i in range(len(pts) - 1):
        a0, z0, r0 = pts[i]
        a1, z1, r1 = pts[i + 1]
        d = math.hypot(math.radians(a1 - a0) * 0.5 * (r0 + r1), z1 - z0)
        seg.append(d)
        total += d
    n = max(1, int(round(total / step_m)))
    out = []
    for k in range(n + 1):
        target = total * k / n
        acc = 0.0
        for i, d in enumerate(seg):
            if acc + d >= target or i == len(seg) - 1:
                f = (target - acc) / d if d > 1e-9 else 0.0
                a0, z0, r0 = pts[i]
                a1, z1, r1 = pts[i + 1]
                out.append((a0 + (a1 - a0) * f, z0 + (z1 - z0) * f,
                            r0 + (r1 - r0) * f))
                break
            acc += d
    rings = []
    for k, (a, z, r) in enumerate(out):
        # Local tangent, for the cross-section's normal direction.
        if k == 0:
            a2, z2, _r2 = out[1]
            a1, z1 = a, z
        else:
            a1, z1 = out[k - 1][0], out[k - 1][1]
            a2, z2 = a, z
        tx = math.radians(a2 - a1) * r
        tz = z2 - z1
        tl = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / tl, tx / tl        # normal in (tangential, axial)
        h = height_m * (1.0 + wobble_m / max(height_m, 1e-6)
                        * (_unit(seed, "hw", k) - 0.5) * 2.0)
        base = math.radians(a)
        ring = []
        for (ox, oy, oz) in ((-width_m / 2, 0.0, 0.0),
                             (-width_m / 2 * 0.55, h, 0.0),
                             (width_m / 2 * 0.55, h, 0.0),
                             (width_m / 2, 0.0, 0.0)):
            # ox is across the run in the (nx, nz) direction.
            dx = ox * nx
            dz = ox * nz + oz
            rr = r - oy
            aa = base + dx / max(r, 1e-9)
            ring.append((rr * math.cos(aa), rr * math.sin(aa), z + dz))
        rings.append(ring)
    off = len(V)
    for ring in rings:
        V.extend(ring)
    t0 = len(T)
    for k in range(len(rings) - 1):
        b0 = off + 4 * k
        b1 = off + 4 * (k + 1)
        for (p, q) in ((0, 1), (1, 2), (2, 3), (3, 0)):
            T.append((b0 + p, b1 + p, b1 + q))
            T.append((b0 + p, b1 + q, b0 + q))
    G.extend([name_side] * (len(T) - t0))
    # End caps, so a hedge is a solid rather than a folded sheet you can see
    # into from the end of the row.
    tc = len(T)
    for b in (off, off + 4 * (len(rings) - 1)):
        T.append((b, b + 1, b + 2))
        T.append((b, b + 2, b + 3))
    G.extend([name_top] * (len(T) - tc))
    _orient(V, T, t0)


def dressing_set(eye, scale=None, kinds=None):
    """Everything standing on the drum floor, at the level `eye` allows.

    The shape of the return is `drum_ground.visible_set`'s -- (verts, tris,
    per-triangle groups, meta) -- because `export_scene.drum_parts` consumes
    both the same way and a second convention is a second thing to get wrong.
    """
    sw = switch_distances(scale)
    fld = field()
    V, T, G = [], [], []
    counts = {}
    per_level = [0, 0, 0, 0]
    for f in fld["points"]:
        if kinds and f.kind not in kinds:
            continue
        d = math.dist(f.position(), eye)
        lv = _level(d, sw)
        if _culled(f.kind, f.proto, lv, sw, f.scale, f.radius_m):
            continue
        per_level[lv] += 1
        counts[f.kind] = counts.get(f.kind, 0) + 1
        if f.kind == "copse":
            if lv >= 3:
                lv_v, lv_t, lv_g = [], [], []
                _dome(lv_v, lv_t, lv_g, "garden_foliage", 0.0, 0.0, 0.0,
                      f.radius_m, 8, 3,
                      CLUMP_MASS_H_M / max(f.radius_m, 1e-6))
                _append(V, T, G, lv_v, lv_t, lv_g, f.angle_deg, f.z_m,
                        f.ground_r)
                continue
            ml = _member_level(lv)
            for (mx, mz, proto, yaw, sc) in f.members:
                da = math.degrees(mx / dg.FLOOR_R)
                pv, pt, pg = prototype("tree", proto, ml)
                _append(V, T, G, pv, pt, pg, f.angle_deg + da, f.z_m + mz,
                        f.ground_r, yaw, sc)
            continue
        pv, pt, pg = prototype(f.kind, f.proto, lv)
        _append(V, T, G, pv, pt, pg, f.angle_deg, f.z_m, f.ground_r,
                f.yaw, f.scale)
    for i, ln in enumerate(fld["lines"]):
        if kinds and ln.kind not in kinds:
            continue
        d = math.dist(ln.centre(), eye)
        lv = _level(d, sw)
        per_level[lv] += 1
        counts[ln.kind] = counts.get(ln.kind, 0) + 1
        if ln.kind == "reeds":
            side, top = "garden_foliage", "garden_foliage"
        elif ln.kind == "park_hedge":
            side, top = "garden_hedge", "garden_hedge"
        else:
            side, top = "garden_hedge", "garden_foliage"
        _ribbon(V, T, G, ln.points, ln.height_m, ln.width_m, side, top,
                HEDGE_STEP_M[lv], HEDGE_WOBBLE_M if lv <= 1 else 0.0,
                seed=f"{SEED}/rib/{i}")
    # THE NEAR RUNG. Emitted through the same call so it reaches the engine by
    # the one path everything else on the drum floor takes -- `export_scene.
    # drum_parts` asks for `dressing_set(eye)` and gets all four rungs. A
    # separate part would be a tenth instance of this project's oldest defect:
    # finished machinery with no caller on the shipped path.
    near_n = 0
    if not kinds or "near" in kinds:
        for x in near_field(eye):
            pv, pt, pg = _near_proto(x.item, x.group, x.index, x.lod)
            _append(V, T, G, pv, pt, pg, x.angle_deg, x.z_m, x.ground_r,
                    x.yaw, 1.0 if x.item == "crop" else x.scale)
            near_n += 1
            counts["near_" + x.item] = counts.get("near_" + x.item, 0) + 1
    return V, T, G, {
        "eye": tuple(round(x, 1) for x in eye),
        "triangles": len(T),
        "vertices": len(V),
        "features": len(fld["points"]) + len(fld["lines"]),
        "near_stands": near_n,
        "per_level": per_level,
        "by_kind": dict(sorted(counts.items())),
        "switch_m": [round(x, 1) for x in sw],
    }


# ---------------------------------------------------------------------------
# THE GATE -- "nothing stands anywhere on 4.5 million m2"
# ---------------------------------------------------------------------------
# The reviewer's finding is a statement about EMPTINESS, so the gate has to
# measure emptiness rather than count objects. A count goes green on 4,000
# objects piled in one corner, which is very nearly what the drum had: 22 of
# them, all inside one 300 m stretch of one settlement band.
#
# Two questions, both of which the pre-existing content fails:
#
#   1. From a swept lattice of standing positions, how far is the NEAREST thing
#      standing on the ground? A landscape you can walk 800 m across without
#      passing anything is the frame the reviewer was looking at.
#   2. What fraction of the drum's 280 ground patches carry something? This is
#      the "piled in one corner" control, and it is the one `garden.townscape`
#      alone fails hardest -- 1 patch of 280.
#
# The floors are stated below and derived rather than picked.

# A person walking sees something within 90 m of them. That figure is not a
# preference: `drum_ground.PATCH_A` x `PATCH_Z` is 124.9 x 129.4 m, so 90 m is
# a little over half a patch diagonal's worth -- the distance at which "there is
# always something in the patch you are standing in" becomes true rather than
# average. -- INV-459
NEAREST_FLOOR_M = 90.0
# Every patch that is not rim fade or open water. Stated as a fraction because
# the water band genuinely should be empty in the middle.
OCCUPANCY_FLOOR = 0.90


def standing_report(samples=24, z_samples=9):
    """Where the drum is empty. The gate's measurement."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    fld = field()
    pts = [f.position() for f in fld["points"]]
    pts += [p for ln in fld["lines"] for p in
            [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)
             for a, z, r in ln.points]]

    worst = (0.0, None)
    dists = []
    for i in range(samples):
        ang = 360.0 * i / samples
        for j in range(z_samples):
            w = (j + 0.5) / z_samples
            z = dg.Z0 + w * (dg.Z1 - dg.Z0)
            h, kind = _ground(ang / 360.0, w)
            if kind in ("water_surface",):
                continue
            r = dg.FLOOR_R - h
            eye = (r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)), z)
            d = min((math.dist(p, eye) for p in pts), default=float("inf"))
            dists.append(d)
            if d > worst[0]:
                worst = (d, (round(ang, 1), round(z, 1)))

    # Patch occupancy.
    occupied = set()
    for (x, y, z) in pts:
        a = math.degrees(math.atan2(y, x)) % 360.0
        w = (z - dg.Z0) / (dg.Z1 - dg.Z0)
        pa = int(a / 360.0 * dg.CELLS_A) // dg.PATCH_A
        pz = min(max(int(w * dg.CELLS_Z) // dg.PATCH_Z, 0), dg.PATCHES_Z - 1)
        occupied.add((pa % dg.PATCHES_A, pz))
    # The denominator excludes patches that are open water or rim: nothing
    # should stand there and counting them would make the floor unreachable.
    eligible = 0
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            u = (pa * dg.PATCH_A + dg.PATCH_A / 2) / dg.CELLS_A
            w = (pz * dg.PATCH_Z + dg.PATCH_Z / 2) / dg.CELLS_Z
            _h, kind = _ground(u, w)
            if kind in ("water_surface", "rim"):
                continue
            eligible += 1
    occ_eligible = 0
    for (pa, pz) in occupied:
        u = (pa * dg.PATCH_A + dg.PATCH_A / 2) / dg.CELLS_A
        w = (pz * dg.PATCH_Z + dg.PATCH_Z / 2) / dg.CELLS_Z
        _h, kind = _ground(u, w)
        if kind in ("water_surface", "rim"):
            continue
        occ_eligible += 1

    dists.sort()
    return {
        "standing_positions": len(dists),
        "objects": len(pts),
        "nearest_median_m": round(dists[len(dists) // 2], 1) if dists else None,
        "nearest_p95_m": round(dists[int(len(dists) * 0.95)], 1) if dists else None,
        "worst_m": round(worst[0], 1),
        "worst_at": worst[1],
        "patches_occupied": occ_eligible,
        "patches_eligible": eligible,
        "occupancy": round(occ_eligible / max(eligible, 1), 4),
    }


def gate(bare=False, verbose=True):
    """The emptiness gate. `bare` runs it on what the drum had before this
    module existed -- `garden.townscape()` alone -- which is the control that
    shows the gate can fail."""
    global _FIELD
    saved = _FIELD
    try:
        if bare:
            schema, profile = it.load()
            sector = it.drum_sector(schema, profile)
            dg.configure(schema, profile, sector)
            # `garden.townscape()`'s own 22 objects, at the position the shot
            # places them. Reconstructed from its parameters rather than from
            # its mesh so the control is about PLACEMENT.
            pts = []
            lo, hi = [b for b in gd.settlement_arcs()
                      if b[0] <= 112.0 < b[1]][0]
            for i in range(12):
                a = lo + 2.0 + gd._u("garden", "ba", i) * (hi - lo - 4.0)
                z = 4900.0 + (gd._u("garden", "bz", i) - 0.5) * 260.0
                h, _k = _ground(a / 360.0, (z - dg.Z0) / (dg.Z1 - dg.Z0))
                pts.append(Feature("town_block", i, a, z, dg.FLOOR_R - h))
            for i in range(10):
                a = lo + 1.0 + gd._u("garden", "ta", i) * (hi - lo - 2.0)
                z = 4900.0 + (gd._u("garden", "tz", i) - 0.5) * 240.0
                h, _k = _ground(a / 360.0, (z - dg.Z0) / (dg.Z1 - dg.Z0))
                pts.append(Feature("tree", i, a, z, dg.FLOOR_R - h))
            _FIELD = {"points": pts, "lines": []}
        else:
            field()
        rep = standing_report()
    finally:
        _FIELD = saved
    ok = (rep["worst_m"] <= NEAREST_FLOOR_M
          and rep["occupancy"] >= OCCUPANCY_FLOOR)
    if verbose:
        label = ("the drum floor BEFORE this module (garden.townscape alone)"
                 if bare else "the drum floor")
        print(f"\n{label}\n")
        print(f"  objects standing                  {rep['objects']:,}")
        print(f"  standing positions swept          {rep['standing_positions']}")
        print(f"  nearest object, median            {rep['nearest_median_m']:,} m")
        print(f"  nearest object, 95th percentile   {rep['nearest_p95_m']:,} m")
        print(f"  nearest object, WORST             {rep['worst_m']:,} m "
              f"at {rep['worst_at']} "
              f"(floor {NEAREST_FLOOR_M:.0f} m) "
              f"{'PASS' if rep['worst_m'] <= NEAREST_FLOOR_M else 'FAIL'}")
        print(f"  ground patches with something on  "
              f"{rep['patches_occupied']} of {rep['patches_eligible']} "
              f"({rep['occupancy']:.1%}, floor {OCCUPANCY_FLOOR:.0%}) "
              f"{'PASS' if rep['occupancy'] >= OCCUPANCY_FLOOR else 'FAIL'}")
        print(f"\n  {'PASS' if ok else 'FAIL'}\n")
    return ok, rep


# ---------------------------------------------------------------------------
# THE NEAR FIELD -- level -1, and the arithmetic that says where it ends
# ---------------------------------------------------------------------------
# STATE.md 24.4b, against `docs/engine-4q-drum-dressed.png`:
#
#   "The near field is empty. The bottom two-thirds of the frame is bare green
#    and tan with one tree in it. The scatter is dense enough to read at 500 m
#    and not at 20 m, which is the opposite of where a player stands. The LOD
#    ladder resolves DETAIL by distance; it does not place more things near the
#    eye, and nothing measures features per m2 AT WALKING DISTANCE."
#
# Measured at that frame's own eye (`--stand 20,4700`) before this section
# existed: the nearest thing standing anywhere is a tree at **44.3 m**, and
# **nothing at all** is inside 35 m. The ladder above is not at fault -- it does
# exactly what it says -- and neither is the density: 1,945 features over 4.5
# million m2 is one per 2,300 m2, which is a landscape at 500 m and an empty
# plain at 5 m. Uniform density cannot be both.
#
# WHY THIS IS A SEPARATE RUNG AND NOT A DENSER SCATTER. The same arithmetic
# `garden.ground_cover` records: the density the near field needs, applied
# everywhere, is ruinous. 212 tussocks inside 35 m is 3,848 m2 at one per 18 m2;
# the same density over the drum is 250,000 objects. A rung that exists ONLY
# near the eye costs its area, not the drum's.
#
# WHERE IT ENDS, AND IT IS NOT A CHOSEN NUMBER. `NEAREST_FLOOR_M` = 90 m is
# already derived (INV-459) as the distance inside which the far field
# guarantees something to look at. So the near rung's job is exactly the ground
# INSIDE that guarantee, and the two rungs meet with no gap and no overlap:
# NEAR_R_M = NEAREST_FLOOR_M. Its own full/coarse switch reuses LOD_RATIOS[1],
# the same 3.2 the far ladder steps by, rather than inventing a fourth ratio.
# -- INV-490
NEAR_R_M = NEAREST_FLOOR_M
NEAR_FULL_M = NEAR_R_M / LOD_RATIOS[1]        # 28.1 m
NEAR_FINE_M = NEAR_FULL_M / LOD_RATIOS[1]     # 8.8 m -- the third rung

# THE PLAYER'S OWN LENS, read from the engine rather than restated: `player.gd`
# line 279 sets `_cam.fov = 70.0`, and Godot's Camera3D defaults to KEEP_HEIGHT,
# so 70 degrees is VERTICAL. Every number below follows from it and from the
# 1.7 m `drum_ground.stand_on_ground` stands a person at.
#
# NOTE THE THREE FOVs THIS PROJECT HAS, because using the wrong one here would
# make the floor look derived and be wrong: the player's 70, the render shot's
# `export_scene.SHOT_FOV_DEG` = 46, and this module's own screen constant
# `drum_ground.FOV_DEG` = 50 (used for LOD pixel arithmetic only). 70 is the
# strictest of the three for this question -- a wider lens puts MORE very-near
# ground in the frame -- and it is the one a player actually looks through.
NEAR_FOV_DEG = 70.0
NEAR_EYE_H_M = 1.7


def near_horizon_split(eye_h=None, fov_deg=None):
    """Where the below-horizon half of the frame actually is, in metres.

    Standing at `eye_h` on flat ground and looking at the horizon, ground at
    distance d appears at depression `atan(eye_h/d)`. The frame runs from the
    horizon (depression 0, infinitely far) to depression `fov/2` at its bottom
    edge, and the screen is a rectangle, so SCREEN AREA IS LINEAR IN DEPRESSION.
    That makes the following exact rather than approximate:

      bottom of frame  d = eye_h / tan(fov/2)
      MEDIAN           d = eye_h / tan(fov/4)   -- half the below-horizon frame
                                                   is nearer than this
      quarter          d = eye_h / tan(fov/8)

    At the player's 70 degrees and 1.7 m that is 2.43 m, **5.39 m** and 11.0 m.
    HALF OF EVERYTHING BELOW THE HORIZON IS GROUND WITHIN 5.4 m OF YOUR FEET,
    and on the drum floor before this section the nearest object was 44.3 m
    away. The lower half of that frame could not have been anything but bare.
    """
    h = NEAR_EYE_H_M if eye_h is None else eye_h
    f = math.radians(NEAR_FOV_DEG if fov_deg is None else fov_deg)
    return {
        "bottom_m": h / math.tan(f / 2.0),
        "median_m": h / math.tan(f / 4.0),
        "quarter_m": h / math.tan(f / 8.0),
        "band_deg": math.degrees(f / 2.0),
    }


# THE FLOORS, and both are the same fact stated twice -- once as a distance and
# once as an area -- so that a content fix has to move both.
#
#   1. NEAREST: from any standing position on ground that is not a road, a
#      pavement or open water, something must stand within `median_m`. Anything
#      further and the nearer half of the below-horizon frame is bare BY
#      CONSTRUCTION, whatever else is on the drum.
#   2. BARE VIEW: at most half of the below-horizon panorama may be bare ground.
#      0.50 is not a taste parameter; it is what "median" means. The near half
#      of the frame is the half inside `median_m`, and a landscape with
#      something standing in it covers that half.
#
# Neither number was chosen and neither can be moved without moving `eye_h` or
# the player's fov. -- INV-491
NEAR_BARE_VIEW_MAX = 0.50

# HOW DENSE THE NEAR RUNG IS, AND IT IS SOLVED RATHER THAN SET. A multiple of
# the garden-derived densities in `NEAR_COVER`, bisected by `--derive-near` for
# the SMALLEST value at which every land-use band passes both floors above.
# That is the same shape of argument as `LOD_SCALE_M` -- a content parameter
# solved against a stated criterion and recorded, not tuned until a frame looked
# better -- except that this one is solved against the MEASUREMENT and the LOD
# scale is solved against the budget.
#
# Recorded rather than solved at import: the solve renders nothing but it does
# sweep the gate, which is 40 s.
#
# The garden's own density is 1.0 by construction and it is NOT enough here.
# The solve, printed by `--derive-near` and reproduced in full:
#
#     gain 1.0  worst nearest 3.80 m   worst band water      60.5%  FAIL
#     gain 2.0  worst nearest 3.80 m   worst band water      55.6%  FAIL
#     gain 3.0  worst nearest 3.13 m   worst band settlement 50.7%  FAIL
#     gain 4.0  worst nearest 3.11 m   worst band settlement 48.6%  PASS
#     gain 8.0  worst nearest 3.11 m   worst band settlement 41.9%  PASS
#
# Two things are worth reading off it rather than just the answer. The DISTANCE
# floor passes at every gain, including 1.0 -- proximity was bought by the
# guaranteed primary and density buys nothing more of it. And the binding band
# is never arable: it is the town and the lake shore, which is the opposite of
# where a scatter-density parameter is any use, and is what sent the settlement
# to a plot wall instead of more grass.
#
# 4.0 x 4.4 = 17.6 tussocks per 100 m2, one clump every 2.4 m. That is a meadow
# rather than a lawn, and the Garden's 1.0 is a MOWN CIVIC TERRACE which also
# carries paving, a pool, benches, lamps and a colonnade inside the same 35 m.
# The two numbers describe two different kinds of ground and the ratio between
# them is the finding, not a fudge. -- INV-493
NEAR_DENSITY_GAIN = 4.0

# Azimuth wedges the panorama is cut into. 24 is the smallest count at which one
# wedge (15 deg) is narrower than the player's own lens is tall, so a wedge
# cannot average a bare quadrant against a dressed one.
NEAR_AZIMUTHS = 24

# Ground kinds that SHOULD be bare at eye level. A carriageway with tussocks
# growing out of it is worse than a bare one, and open water is water.
NEAR_BARE_KINDS = ("road", "ring_road", "avenue", "water_surface", "rim")


# ---------------------------------------------------------------------------
# The near lattice, and why it is the GROUND's lattice
# ---------------------------------------------------------------------------
# `drum_ground` states its own limit plainly, above `HEDGE_W_M`: "the hedge
# itself -- 2 m tall, 1 m wide -- is finer than lod0's 3.9 m cell and belongs in
# the material, not the field. A 1 m-wide ridge in a 3.9 m lattice does not
# render as a hedge at any level." That is correct and it is a DELEGATION: the
# heightfield cannot carry anything under a cell, so something else has to.
# Nothing took delivery, which is why the near field is flat.
#
# So the near rung places one stand of cover per GROUND LATTICE CELL -- 3.903 x
# 4.044 m, 15.79 m2 -- which is exactly the resolution the heightfield admits it
# cannot represent. It is not a new lattice and it cannot drift from the ground,
# because the cell's land use, height and material all come from the same
# `dg.sample` call the ground vertex comes from.
#
# Worst distance from a standing position to the nearest cell centre is half a
# cell diagonal, 2.81 m, against the 5.39 m the floor above asks for. The margin
# is deliberate: a cell whose kind is a road carries nothing, so a player
# standing beside a carriageway is two cells from cover, not one.
_NEAR_SAMPLE = {}


def _lattice_sample(ia, iz):
    """`dg.sample` at a lattice cell centre, memoised on the INTEGER cell.

    `dg.sample` costs 256 us -- six-octave fbm, two warped parcel maps and three
    road profiles -- and the near rung asks for it 500-1,600 times per eye. The
    key is the integer cell, so this is an exact memo and not the session-4c
    defect (`interior.load()` returning a fresh dict, so an id()-keyed memo
    missed every time): (ia, iz) hashes to the same bucket forever.
    Invalidated by `reset_near_cache()`, which `field(rebuild=True)` calls.
    """
    key = (ia % dg.CELLS_A, iz)
    got = _NEAR_SAMPLE.get(key)
    if got is None:
        got = dg.sample((key[0] + 0.5) / dg.CELLS_A,
                        min(max((iz + 0.5) / dg.CELLS_Z, 0.0), 1.0))
        _NEAR_SAMPLE[key] = got
    return got


def reset_near_cache():
    _NEAR_SAMPLE.clear()
    _NEAR_PROTO.clear()


# ---------------------------------------------------------------------------
# What grows where -- one recipe per ground kind, keyed off the SAME tag the
# ground's own material comes from
# ---------------------------------------------------------------------------
# THE CROP TAKES ITS PARCEL'S OWN MATERIAL. `drum_ground._KIND_GROUP` maps the
# cell's kind to the group the ground under it is drawn with, and a crop stand
# in an `arable2` parcel emits `ground_arable_2` -- the same group, so the same
# albedo, by construction. That is hard rule 4 (inside and outside from one
# schema) applied to a third thing: a crop whose colour is authored separately
# would drift from the parcel it stands in, and the drift would be invisible
# until somebody looked at a frame.
#
# Heights: 29a is the only ground-level authority-1 frame of the drum and it
# shows "clipped hedges about head height" in the PARK. `garden.HEDGE_H_M` is
# 1.05 m and is already derived from it. Crop is taken at 0.95 m -- below a
# standing eye, so a player sees over the field rather than into a wall of it,
# which is what 34b's readable parcel patchwork requires from above. Tussock and
# scrub follow `garden.TUSSOCK_R_M`/`SCRUB_R_M`, which the garden's own
# near-field work derived in this session. -- INV-492
CROP_H_M = 0.95
CROP_ROW_PITCH_M = 0.92      # 34b: "a strong row-textured green"
CROP_ROWS = 3                # per cell at full detail; 3 x 0.92 = 2.8 of 3.9 m
CROP_W_FRAC = 0.62           # ridge width as a fraction of the row pitch
TUSSOCK_H_M = 0.42
SCRUB_H_M = 0.85
REED_TUFT_H_M = 1.35
MARGIN_H_M = 0.55            # rough grass on a hedge bank
BOXHEDGE_H_M = 0.82          # clipped, below the 1.05 m of 29a's park hedges
BOXHEDGE_L_M = 3.60
BOXHEDGE_W_M = 1.15
# THE PLOT WALL, and it is here because the MEASUREMENT said so rather than
# because a town ought to have one. Solved against the near gate, the settlement
# band needed EIGHT times the garden's ground-cover density to get its
# below-horizon view under 50% bare, and eight times the grass in a town centre
# is an absurd answer to a real number. The arithmetic says why: a 3.6 m clipped
# hedge at 5 m covers about 3% of the panorama and you would need seventeen of
# them, while ONE continuous 1.25 m wall along a street frontage at 8 m covers
# a third of the band over half the azimuths. A town's near view is bounded by
# walls, not filled with objects.
#
# It is also what the reference asks for and nothing was building:
# `2-22_33a` -- "rectangular built parcels carry a fine internal grid".
# `drum_ground` cuts that grid into the podium as avenues; the plot boundary
# standing on it did not exist. 1.25 m is below a 1.7 m eye, so a player sees
# over the wall down the street, which is what the frame shows. -- INV-494
WALL_H_M = 1.25
WALL_W_M = 0.34
STONE_H_M = 0.34             # a field stone the plough turned up

# How far the cell's stand is sunk into the ground so that a ramp does not leave
# it floating. DERIVED, not chosen: the steepest ground in the drum is a road or
# podium ramp, `PODIUM_STEP_M` (2.0 m) over `_step_ramp_m()` (31.2 m) = 6.4%,
# and a stand spans at most one cell diagonal (5.62 m), so the worst end-to-end
# drop under one stand is 0.36 m. Half of that is under its centre.
NEAR_SINK_M = 0.18

# HOW MANY, AND IT IS NOT A NUMBER THIS MODULE CHOSE. `garden.ground_cover` --
# built this same session, standing in `docs/garden-4q-after-tree.png`, and the
# only near-field content in this project that has been judged craft 3 at half
# distance -- carries `TUSSOCK_PER_100M2 = 4.4` and `SCRUB_PER_100M2 = 2.0`.
# Those are read from it rather than restated, so the drum's near field and the
# Garden's cannot end up two different densities on one drum floor.
#
# THE FIRST ENTRY OF EACH RECIPE IS THE PRIMARY AND IT IS GUARANTEED ONE PER
# CELL, and that is the one number here that is derived from the gate rather
# than from the garden. The floor says something must stand within
# `median_m` = 5.39 m of any standing position; a lattice of one stand per cell
# puts the worst case at half a cell diagonal, 2.81 m. Density buys COVER, the
# guaranteed primary buys PROXIMITY, and they are different questions -- which
# is why garden's 4.4 per 100 m2 (0.69 per cell) cannot be the whole rule:
# on its own it leaves a seventh of the cells empty and the worst standing
# position walks past them. -- INV-493
#
# (item, extra stands per 100 m2, height, group source)
#   group source "ground" = the cell's own ground group, "hedge"/"foliage" =
#   a garden material, so that scrub reads darker than the lawn it stands on.
NEAR_COVER = {
    "arable":  (("crop", 0.0, CROP_H_M, "ground"),
                ("stone", 0.6, STONE_H_M, "rim")),
    "hedge":   (("margin", gd.TUSSOCK_PER_100M2, MARGIN_H_M, "hedge"),),
    "parkland": (("tussock", gd.TUSSOCK_PER_100M2, TUSSOCK_H_M, "ground"),
                 ("scrub", gd.SCRUB_PER_100M2, SCRUB_H_M, "hedge")),
    "verge":   (("tussock", gd.TUSSOCK_PER_100M2, TUSSOCK_H_M, "ground"),
                ("scrub", gd.SCRUB_PER_100M2, SCRUB_H_M, "hedge")),
    # A TOWN'S NEAR FIELD IS ORTHOGONAL, NOT TUFTED. `2-22_33a` reads the built
    # half as "rectangular built parcels [carrying] a fine internal grid", and a
    # scatter of grass tufts between the blocks reads as a field with buildings
    # in it. `boxhedge` is a clipped hedge or a planter kerb -- a low box, the
    # same family of shape as the blocks it stands among.
    "settlement": (("boxhedge", 0.0, BOXHEDGE_H_M, "hedge"),
                   ("tussock", gd.TUSSOCK_PER_100M2, TUSSOCK_H_M, "ground")),
    "shore":   (("reedtuft", gd.TUSSOCK_PER_100M2, REED_TUFT_H_M, "foliage"),),
    "water":   (("reedtuft", gd.TUSSOCK_PER_100M2, REED_TUFT_H_M, "foliage"),),
}
for _i in range(dg.CROPS):
    NEAR_COVER[f"arable{_i}"] = NEAR_COVER["arable"]

_NEAR_GROUP = {"hedge": "garden_hedge", "foliage": "garden_foliage",
               "rim": "ground_rim", "masonry": "garden_boundary"}

# A settlement cell that fronts a street gets the wall instead of the hedge.
NEAR_FRONTAGE = (("wall", 0.0, WALL_H_M, "masonry"),
                 ("tussock", gd.TUSSOCK_PER_100M2, TUSSOCK_H_M, "ground"))
_STREET_KINDS = ("avenue", "verge", "road", "ring_road")

_NEAR_PROTO = {}


def _near_proto(item, group, index, lod):
    """One stand of near cover, in the local (x tangential, y up, z axial) frame.

    THREE RUNGS, NOT TWO, and the third one is there because the half-distance
    frame asked for it. `docs/near-4r-after-half.png`'s first take shows the
    tufts as five-sided flat-topped frusta at 2-3 m -- which is `AAA-STANDARD`'s
    C1 "a box primitive standing in for a named object" at small scale. Rung 0
    is the stands inside `NEAR_FINE_M`, which is `NEAR_FULL_M / LOD_RATIOS[1]`
    -- the module's own ratio again -- and there are about fifteen cells of them,
    so rounding those costs under a thousand triangles.

    Closed solids, every one, and the self-test proves it: an open tuft is
    `dressing._cyl`'s session-3x defect (open at the bottom and wound inside
    out) at 500 times the instance count.
    """
    key = (item, group, index % PROTOTYPES, lod)
    got = _NEAR_PROTO.get(key)
    if got is not None:
        return got
    v, t, g = [], [], []
    seed = f"{SEED}/near/{item}/{index}"
    if item == "crop":
        # RIDGES ALONG THE AXIS, because that is the direction the furrows run:
        # `drum_ground` -- "you plough along the direction of travel", since a
        # furrow across the drum climbs a hill that never ends. Looking down the
        # axis, which is how the drum is framed, they converge on the vanishing
        # point and the parcel stops being a colour field.
        rows = 1 if lod >= 2 else CROP_ROWS
        pitch = CROP_ROW_PITCH_M * (CROP_ROWS if lod >= 2 else 1)
        halfw = pitch * CROP_W_FRAC * 0.5
        cz = (dg.Z1 - dg.Z0) / dg.CELLS_Z
        segs = (1, 2, 1)[min(lod, 2)] if lod >= 1 else 4
        for r in range(rows):
            x0 = (r - (rows - 1) / 2.0) * pitch
            hh = CROP_H_M * (0.82 + 0.36 * _unit(seed, "h", r))
            _ridge(v, t, g, group, x0, halfw, -cz / 2.0, cz / 2.0,
                   hh, segs, seed=f"{seed}/{r}")
    elif item in ("boxhedge", "wall"):
        wall = item == "wall"
        h = (WALL_H_M if wall else BOXHEDGE_H_M) * (0.9 + 0.2 * _unit(seed, "h"))
        # A wall RUN is one lattice cell long plus an overlap, so consecutive
        # cells join into a continuous frontage instead of a dashed line.
        L = (1.06 * (dg.Z1 - dg.Z0) / dg.CELLS_Z if wall
             else BOXHEDGE_L_M * (0.7 + 0.6 * _unit(seed, "l")))
        w = WALL_W_M if wall else BOXHEDGE_W_M * (0.8 + 0.4 * _unit(seed, "w"))
        t0 = len(t)
        _box(v, t, g, group, (-w / 2, -NEAR_SINK_M, -L / 2), (w / 2, h, L / 2))
        if wall and lod <= 1:
            # A coping course. Twelve triangles, and it is the line that says
            # "wall" rather than "slab standing on edge".
            _box(v, t, g, group, (-w * 0.72, h, -L / 2),
                 (w * 0.72, h + 0.09, L / 2))
        elif not wall and lod <= 1:
            # A clipped hedge has a cap that is not the same width as its foot;
            # a single prism is the "cube" the owner's session-3r finding is
            # about, at 1/50th the size. One setback course costs 12 triangles.
            _box(v, t, g, group, (-w * 0.36, h, -L * 0.46),
                 (w * 0.36, h + 0.12, L * 0.46))
        _orient(v, t, t0)
    elif item in ("tussock", "scrub", "margin", "reedtuft", "stone"):
        h = {"tussock": TUSSOCK_H_M, "scrub": SCRUB_H_M,
             "margin": MARGIN_H_M, "reedtuft": REED_TUFT_H_M,
             "stone": STONE_H_M}[item]
        h *= 0.75 + 0.5 * _unit(seed, "h")
        # WIDER THAN TALL, AND THE FIRST VERSION WAS NOT -- which a frame said
        # and no assertion could. At radius = 0.62 x height a tussock is as tall
        # as it is wide, and 98 of them inside 30 m of `--stand 20,4700` render
        # as a field of pitched tents (`docs/near-4r-after-axis.png`, first
        # take). `garden.SCRUB_H_FRAC` = 0.55 is the proportion that module
        # derived for the same object and it is read from there rather than
        # guessed again. Reeds invert it -- they are the one ground cover that
        # is taller than it is wide -- and a stone is nearly round.
        prop = {"tussock": gd.SCRUB_H_FRAC, "scrub": gd.SCRUB_H_FRAC,
                "margin": gd.SCRUB_H_FRAC, "reedtuft": 1.90,
                "stone": 0.62}[item]
        r = h / (2.0 * prop)
        # SEGMENT COUNT IS PAID FOR, NOT PREFERRED. A 0.42 m tussock at the
        # full/coarse switch (28.1 m) is 23 px tall by this module's own
        # `_pixels`, so a five-sided silhouette is 4.6 px a facet there and
        # rounder than the ground it stands on. Six was the first value and it
        # cost 36 triangles an object over 1,120 objects at the worst eye.
        seg = (6, 5, 4)[min(lod, 2)]
        stacks = 3 if lod == 0 else 2
        _dome(v, t, g, group, 0.0, 0.0, 0.0, r, seg, stacks, h / max(r, 1e-6))
    else:
        raise ValueError(f"no near prototype for {item!r}")
    _NEAR_PROTO[key] = (v, t, g)
    return _NEAR_PROTO[key]


def _ridge(v, t, g, name, x0, halfw, z0, z1, h, segs, seed="r"):
    """A closed crop ridge: a triangular section swept along z.

    Three verts a ring, `segs+1` rings, so it is a solid with two caps -- and it
    is wound the same way `_orient` expects, which is asserted rather than
    argued: `_orient` re-orients against the centroid at the end.
    """
    off = len(v)
    t0 = len(t)
    n = segs
    for k in range(n + 1):
        f = k / n
        z = z0 + (z1 - z0) * f
        hh = h * (0.88 + 0.24 * _unit(seed, "k", k))
        v.append((x0 - halfw, -NEAR_SINK_M, z))
        v.append((x0 + halfw, -NEAR_SINK_M, z))
        v.append((x0 + halfw * 0.12 * (_unit(seed, "l", k) - 0.5), hh, z))
    for k in range(n):
        a, b = off + 3 * k, off + 3 * (k + 1)
        for p, q in ((0, 1), (1, 2), (2, 0)):
            t.append((a + p, b + p, b + q))
            t.append((a + p, b + q, a + q))
    t.append((off, off + 1, off + 2))
    e = off + 3 * n
    t.append((e, e + 2, e + 1))
    g.append((name, t0, len(t)))
    _orient(v, t, t0)


class NearItem:
    """One stand of near cover. Not a `Feature`: it carries its own group (the
    parcel's) and its own level, and it is never in the eye-independent field."""
    __slots__ = ("item", "group", "index", "angle_deg", "z_m", "ground_r",
                 "yaw", "scale", "height_m", "width_m", "lod", "kind")

    def __init__(self, item, group, index, angle_deg, z_m, ground_r, yaw,
                 scale, height_m, width_m, lod, kind):
        self.item = item
        self.group = group
        self.index = index
        self.angle_deg = angle_deg
        self.z_m = z_m
        self.ground_r = ground_r
        self.yaw = yaw
        self.scale = scale
        self.height_m = height_m
        self.width_m = width_m
        self.lod = lod
        self.kind = kind

    def position(self):
        a = math.radians(self.angle_deg)
        return (self.ground_r * math.cos(a), self.ground_r * math.sin(a),
                self.z_m)


# WHAT THE NEAR RUNG MUST NOT GROW INSIDE, and this guard exists because the
# equivalent one FIRED FOR REAL in `garden.py` this same session: a tree's
# canopy stood inside a building 11 m from the eye, "because blocks and trees
# were drawn from two independent distributions with nothing between them".
# The near rung is a third independent distribution over the same ground and
# would have put a clipped hedge inside a house 708 times. Footprints are
# measured off the prototypes, never declared.
#
# ONLY THINGS WITH A SOLID FOOTPRINT ARE IN THIS LIST, and the first version
# got that wrong in a way the gate caught within one run: it included `gantry`,
# whose boom is `GANTRY_SPAN_M` = 87.4 m of pipe on two legs, so its bounding
# width cleared a 44 m disc of crop and the worst nearest-object distance went
# from 3.30 m to 24.01 m in the arable band. An irrigation boom is a frame you
# stand a crop UNDER. A house is not.
_NEAR_KEEPOUT_PAD_M = 1.2
_KEEPOUT_KINDS = ("town_block", "shed", "silo")


def _near_keepout(eye, radius):
    """Footprints near this eye, as ORIENTED rectangles.

    A circumscribed disc is the lazy version and it was measurably wrong: a
    22 x 13 m block's circumscribed radius is 12.8 m, so a disc clears 515 m2
    where the building covers 286, and the corner a player actually stands in
    comes back bare. The rectangle is the block's own (L, W) from
    `prototype_dims` turned through its own placed yaw.
    """
    out = []
    for f in field()["points"]:
        if f.kind not in _KEEPOUT_KINDS:
            continue
        p = f.position()
        if math.dist(p, eye) > radius + 80.0:
            continue
        if f.kind == "town_block":
            L, W, _H = prototype_dims(f.proto)
            hx = 0.5 * L * f.scale + _NEAR_KEEPOUT_PAD_M
            hz = 0.5 * W * f.scale + _NEAR_KEEPOUT_PAD_M
        else:
            _h, w = _proto_extent(f.kind, f.proto, 0)
            hx = hz = 0.5 * w * f.scale + _NEAR_KEEPOUT_PAD_M
        out.append((f.angle_deg, f.z_m, f.ground_r, f.yaw, hx, hz,
                    math.hypot(hx, hz)))
    return out


def _in_keepout(keep, ang, z, gr):
    for (fa, fz, fr, yaw, hx, hz, rmax) in keep:
        dx = math.radians(ang - fa) * fr
        dz = z - fz
        if dx * dx + dz * dz > rmax * rmax:
            continue
        ca, sa = math.cos(yaw), math.sin(yaw)
        if abs(dx * ca + dz * sa) < hx and abs(-dx * sa + dz * ca) < hz:
            return True
    return False


def _frontage(ia, iz):
    """(yaw, tangential offset, axial offset) if this cell fronts a street.

    Read off the GROUND's own kinds -- a cell whose neighbour is an avenue, a
    verge or a carriageway is a frontage cell -- so the wall follows whatever
    street grid `drum_ground` cut, and cannot drift from it.
    """
    cell_a = 2.0 * math.pi * dg.FLOOR_R / dg.CELLS_A
    cell_z = (dg.Z1 - dg.Z0) / dg.CELLS_Z
    for (dia, diz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        jz = iz + diz
        if not (0 <= jz < dg.CELLS_Z):
            continue
        if _lattice_sample(ia + dia, jz)[1] not in _STREET_KINDS:
            continue
        if dia:
            # The street runs along the axis; the wall runs with it.
            return 0.0, dia * cell_a * 0.42, 0.0
        return math.pi / 2.0, 0.0, diz * cell_z * 0.42
    return None


def near_field(eye, radius=None, full_m=None, gain=None):
    """Every stand of near cover within `radius` of `eye`. Eye-relative.

    Deterministic in WORLD space, not in eye space: everything is keyed on the
    ground lattice cell (ia, iz), so walking toward a tussock does not
    regenerate it somewhere else. That is the property a scatter authored
    relative to the camera does not have, and it is the reason this is written
    against the lattice rather than as a disc of jittered points.
    """
    radius = NEAR_R_M if radius is None else radius
    full_m = NEAR_FULL_M if full_m is None else full_m
    gain = NEAR_DENSITY_GAIN if gain is None else gain
    if radius <= 0.0:
        return []
    cell_a = 2.0 * math.pi * dg.FLOOR_R / dg.CELLS_A
    cell_z = (dg.Z1 - dg.Z0) / dg.CELLS_Z
    a_eye = math.degrees(math.atan2(eye[1], eye[0])) % 360.0
    z_eye = eye[2]
    ia0 = int(round(a_eye / 360.0 * dg.CELLS_A))
    iz0 = int(round((z_eye - dg.Z0) / (dg.Z1 - dg.Z0) * dg.CELLS_Z))
    na = int(math.ceil(radius / cell_a)) + 1
    nz = int(math.ceil(radius / cell_z)) + 1
    keep = _near_keepout(eye, radius)
    out = []
    for dia in range(-na, na + 1):
        for diz in range(-nz, nz + 1):
            ia, iz = ia0 + dia, iz0 + diz
            if not (0 <= iz < dg.CELLS_Z):
                continue
            h, kind = _lattice_sample(ia, iz)
            recipe = NEAR_COVER.get(kind)
            if recipe is None:
                continue
            front = _frontage(ia, iz) if kind == "settlement" else None
            if front is not None:
                recipe = NEAR_FRONTAGE
            u = ((ia % dg.CELLS_A) + 0.5) / dg.CELLS_A
            w = (iz + 0.5) / dg.CELLS_Z
            ang, z = _uw_to_station(u, w)
            gr = dg.FLOOR_R - h
            p = (gr * math.cos(math.radians(ang)), gr * math.sin(math.radians(ang)), z)
            d = math.dist(p, eye)
            if d > radius:
                continue
            lod = 2 if d >= full_m else (0 if d < NEAR_FINE_M else 1)
            coarse = lod >= 2
            # STRIDE 2 BEYOND THE FULL SWITCH. Not a fade: a fade leaves a bowl
            # and a ring, and the coarse rung's job is relief that catches
            # light, not a countable object. Every other cell, at one stand of
            # its own, is 3.9 tri/100 m2 against the full rung's 27.
            if coarse and ((ia + iz) % 2 or (ia % 2)):
                continue
            base_group = dg._KIND_GROUP.get(kind, "ground_arable")
            cell_area = cell_a * cell_z
            for ri, (item, per100, hgt, gsrc) in enumerate(recipe):
                if coarse and item in ("stone",):
                    continue
                grp = base_group if gsrc == "ground" else _NEAR_GROUP[gsrc]
                if item == "crop":
                    if _in_keepout(keep, ang, z, gr):
                        continue
                    out.append(NearItem(
                        "crop", grp, ia * 7 + iz, ang, z, gr, 0.0, 1.0,
                        CROP_H_M, cell_a * 0.72, lod, kind))
                    continue
                if item == "wall":
                    yaw, dxm, dzm = front
                    aa = ang + math.degrees(dxm / gr)
                    zz = z + dzm
                    if _in_keepout(keep, aa, zz, gr):
                        continue
                    out.append(NearItem(
                        "wall", grp, ia * 11 + iz, aa, zz, gr, yaw, 1.0,
                        WALL_H_M, cell_z * 1.06, lod, kind))
                    continue
                # The primary is guaranteed one per cell; the rest is the
                # garden's own density, taken deterministically rather than as
                # an average -- an integer part plus a threshold on the
                # fractional one, so 4.4 per 100 m2 really is 4.4 per 100 m2
                # over any patch and not 0 per cell because it rounds down.
                want = per100 * gain * cell_area / 100.0
                cnt = int(want) + (1 if _unit(SEED, "nn", ia, iz, item)
                                   < (want - int(want)) else 0)
                if ri == 0:
                    cnt = max(1, cnt)
                if coarse:
                    cnt = 1 if ri == 0 else 0
                for k in range(cnt):
                    jx = (_unit(SEED, "nx", ia, iz, item, k) - 0.5) * cell_a * 0.86
                    jz = (_unit(SEED, "nz", ia, iz, item, k) - 0.5) * cell_z * 0.86
                    sc = 0.75 + 0.55 * _unit(SEED, "ns", ia, iz, item, k)
                    if coarse:
                        sc *= 1.5      # one stand standing in for n
                    aa = ang + math.degrees(jx / gr)
                    if _in_keepout(keep, aa, z + jz, gr):
                        continue
                    out.append(NearItem(
                        item, grp, ia * 5 + iz * 3 + k, aa, z + jz, gr,
                        math.tau * _unit(SEED, "ny", ia, iz, item, k), sc,
                        hgt * sc, hgt * sc * 1.24, lod, kind))
    return out


def near_cost(eye, radius=None, full_m=None, gain=None):
    """Triangles the near rung would build at this eye, without building it."""
    n = 0
    for x in near_field(eye, radius, full_m, gain):
        n += len(_near_proto(x.item, x.group, x.index, x.lod)[1])
    return n


def near_worst_cost(samples=8, radius=None, full_m=None, gain=None):
    """The most expensive place to stand, for the near rung alone."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    worst = (0, None)
    for i in range(samples):
        ang = 360.0 * i / samples
        for f in (0.2, 0.5, 0.8):
            z = dg.Z0 + f * (dg.Z1 - dg.Z0)
            eye, _up = dg.stand_on_ground(schema, profile, sector, ang, z)
            n = near_cost(eye, radius, full_m, gain)
            if n > worst[0]:
                worst = (n, (round(ang, 1), round(z, 1)))
    return {"triangles": worst[0], "at": worst[1]}


# ---------------------------------------------------------------------------
# THE MEASUREMENT: how much of what a standing player can see is bare ground
# ---------------------------------------------------------------------------
# Every gate in this module before this one counts objects or measures the
# distance to one. Neither can fail for "there is nothing to look at where I am
# standing", because a count is satisfied by objects anywhere and a nearest
# distance is satisfied by ONE object in ONE direction.
#
# So this measures SCREEN. The below-horizon band is depression 0 to fov/2; each
# feature standing on the ground covers, in its own azimuth, the depression
# interval from its top to its base; the union of those intervals over every
# feature is what is not bare. It is done per azimuth wedge and averaged, so
# one tree cannot cover a panorama.
#
# THE DRUM'S CURVATURE IS IN IT, and it has to be: 90 m around the barrel is
# 18.5 degrees of arc and the floor there stands 14.4 m ABOVE the tangent plane
# at your feet, which is above the horizon. A flat-ground approximation would
# put that ground in the below-horizon band and score it as bare. Everything
# below is computed from world positions against the local vertical instead.


def _eye_frame(eye):
    """(up, tangential, axial) at a standing eye. Up is radially INWARD."""
    r = math.hypot(eye[0], eye[1]) or 1.0
    up = (-eye[0] / r, -eye[1] / r, 0.0)
    tg = (-eye[1] / r, eye[0] / r, 0.0)
    return up, tg, (0.0, 0.0, 1.0)


def _cover_intervals(eye, items, band):
    """[(azimuth_index, lo_depression, hi_depression)] for each feature.

    `items` is a sequence of (position, height_m, width_m). Depression is
    positive downward from the eye's own tangent plane, so an object whose top
    is above the horizon has a negative `lo` and is clipped at 0.
    """
    up, tg, ax = _eye_frame(eye)
    out = []
    for (p, h_m, w_m) in items:
        vx, vy, vz = p[0] - eye[0], p[1] - eye[1], p[2] - eye[2]
        d3 = math.sqrt(vx * vx + vy * vy + vz * vz)
        if d3 < 1e-6:
            continue
        # The feature's own local vertical, which is not the eye's.
        pr = math.hypot(p[0], p[1]) or 1.0
        pux, puy = -p[0] / pr, -p[1] / pr
        tx, ty, tz = vx + pux * h_m, vy + puy * h_m, vz
        dt = math.sqrt(tx * tx + ty * ty + tz * tz) or 1e-6
        hi = -math.asin(max(-1.0, min(1.0, (vx * up[0] + vy * up[1] + vz * up[2]) / d3)))
        lo = -math.asin(max(-1.0, min(1.0, (tx * up[0] + ty * up[1] + tz * up[2]) / dt)))
        if hi <= 0.0 or lo >= band:
            continue
        lo = max(lo, 0.0)
        hi = min(hi, band)
        if hi <= lo:
            continue
        az = math.atan2(vx * tg[0] + vy * tg[1] + vz * tg[2],
                        vx * ax[0] + vy * ax[1] + vz * ax[2])
        half = math.atan2(max(w_m, 0.05) * 0.5, max(d3, 0.05))
        i0 = int(math.floor((az - half) / math.tau * NEAR_AZIMUTHS))
        i1 = int(math.floor((az + half) / math.tau * NEAR_AZIMUTHS))
        for i in range(i0, i1 + 1):
            out.append((i % NEAR_AZIMUTHS, lo, hi))
    return out


def _bare_fraction(eye, items):
    """Fraction of the below-horizon panorama showing bare ground."""
    band = math.radians(NEAR_FOV_DEG / 2.0)
    per = [[] for _ in range(NEAR_AZIMUTHS)]
    for i, lo, hi in _cover_intervals(eye, items, band):
        per[i].append((lo, hi))
    total = 0.0
    for spans in per:
        if not spans:
            continue
        spans.sort()
        cov = 0.0
        clo, chi = spans[0]
        for lo, hi in spans[1:]:
            if lo > chi:
                cov += chi - clo
                clo, chi = lo, hi
            else:
                chi = max(chi, hi)
        cov += chi - clo
        total += min(cov, band)
    return 1.0 - total / (band * NEAR_AZIMUTHS)


_STATIC_ITEMS = None


def _static_items():
    """(position, height, width) for every eye-independent feature. Measured off
    the prototypes, never declared -- an object that grows counts for more."""
    global _STATIC_ITEMS
    if _STATIC_ITEMS is not None:
        return _STATIC_ITEMS
    fld = field()
    out = []
    for f in fld["points"]:
        if f.kind == "copse":
            h, _w = _proto_extent("tree", 0, 0)
            out.append((f.position(), h * 0.95, 2.0 * f.radius_m))
            continue
        h, w = _proto_extent(f.kind, f.proto, 0)
        out.append((f.position(), h * f.scale, w * f.scale))
    for ln in fld["lines"]:
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z)
               for a, z, r in ln.points]
        for i in range(len(pts) - 1):
            mid = tuple((pts[i][k] + pts[i + 1][k]) / 2.0 for k in range(3))
            seg = math.dist(pts[i], pts[i + 1])
            out.append((mid, ln.height_m, max(seg, ln.width_m)))
    _STATIC_ITEMS = out
    return out


def near_report(samples=16, z_samples=8, near=True, gain=None):
    """What a standing player can see within walking distance. The gate's
    measurement. `near=False` runs it with the near rung switched OFF, which is
    the control and is the state of the drum before this section existed."""
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    stat = _static_items()
    split = near_horizon_split()
    # WHERE THE EYE IS PUT, AND WHY IT IS NOT A UNIFORM SWEEP ALONE. A uniform
    # 16-angle sweep of this drum lands NO position in the water band -- it is
    # 36 degrees wide and the shore inside it is narrower still -- so the band
    # whose near field is hardest to fill was invisible to the first version of
    # this gate, which reported PASS with the shore unmeasured. Every band gets
    # its own positions, whatever its angular width, and the uniform sweep is
    # kept on top so the drum-wide mean is still area-weighted.
    angles = [360.0 * i / samples for i in range(samples)]
    for (lo, hi, _nm, _r) in dg._bands():
        for k in range(3):
            angles.append(360.0 * (lo + (k + 0.5) / 3.0 * (hi - lo)))
    rows = []
    skipped_kind = skipped_indoors = 0
    for ang in sorted(set(round(a, 4) for a in angles)):
        for j in range(z_samples):
            w = (j + 0.5) / z_samples
            z = dg.Z0 + w * (dg.Z1 - dg.Z0)
            h, kind = _ground(ang / 360.0, w)
            if kind in NEAR_BARE_KINDS:
                skipped_kind += 1
                continue
            eye, _up = dg.stand_on_ground(schema, profile, sector, ang, z)
            # A POSITION INSIDE A BUILDING IS NOT A STANDING POSITION, and the
            # exclusion is COUNTED rather than silent so it cannot be grown to
            # make a number go green. It matters because the near rung
            # deliberately does not grow cover inside a footprint, so measuring
            # from in there measures the inside of somebody's front room and
            # reports it as a bare landscape -- which is what put the worst
            # nearest-object distance at 6.37 m on the first run.
            #
            # THEY ARE REACHABLE, and that is a real open defect rather than a
            # modelling convenience: nothing this module emits is solid (see
            # the module docstring), so a player CAN walk into a town block.
            # That is `drum_walk.py`'s to close and it is recorded, not hidden.
            if _in_keepout(_near_keepout(eye, 0.0), ang, z, dg.FLOOR_R - h):
                skipped_indoors += 1
                continue
            items = [s for s in stat if math.dist(s[0], eye) < 600.0]
            n_near = 0
            if near:
                for x in near_field(eye, gain=gain):
                    items.append((x.position(), x.height_m, x.width_m))
                    n_near += 1
            nearest = min((math.dist(s[0], eye) for s in items),
                          default=float("inf"))
            rows.append({
                "at": (round(ang, 1), round(z, 1)),
                "kind": kind,
                "band": _band_at(ang / 360.0),
                "nearest_m": nearest,
                "bare": _bare_fraction(eye, items),
                "near_items": n_near,
                "per_ha": len([s for s in items
                               if math.dist(s[0], eye) <= split["quarter_m"]])
                / (math.pi * split["quarter_m"] ** 2) * 10000.0,
            })
    rows.sort(key=lambda r: r["nearest_m"])
    nd = [r["nearest_m"] for r in rows]
    bare = sorted(r["bare"] for r in rows)
    by_band = {}
    for r in rows:
        b = by_band.setdefault(r["band"], {"n": 0, "bare": 0.0, "worst": 0.0})
        b["n"] += 1
        b["bare"] += r["bare"]
        b["worst"] = max(b["worst"], r["nearest_m"])
    for b in by_band.values():
        b["bare"] = round(b["bare"] / b["n"], 4)
        b["worst"] = round(b["worst"], 1)
    return {
        "positions": len(rows),
        "skipped_road_or_water": skipped_kind,
        "skipped_indoors": skipped_indoors,
        "split": {k: round(v, 2) for k, v in split.items()},
        "nearest_median_m": round(nd[len(nd) // 2], 2),
        "nearest_p95_m": round(nd[int(len(nd) * 0.95)], 2),
        "nearest_worst_m": round(nd[-1], 2),
        "nearest_worst_at": rows[-1]["at"],
        "nearest_worst_band": rows[-1]["band"],
        "bare_mean": round(sum(bare) / len(bare), 4),
        "bare_median": round(bare[len(bare) // 2], 4),
        "bare_worst": round(bare[-1], 4),
        "per_ha_median": round(sorted(r["per_ha"] for r in rows)[len(rows) // 2], 1),
        "near_items_median": sorted(r["near_items"] for r in rows)[len(rows) // 2],
        "by_band": dict(sorted(by_band.items())),
    }


def near_gate(bare=False, verbose=True, samples=16, z_samples=8, gain=None):
    """The near-field gate. `bare` runs it with the near rung OFF -- the drum as
    it stood at the end of session 4q -- which is the control."""
    rep = near_report(samples=samples, z_samples=z_samples, near=not bare,
                      gain=gain)
    med = rep["split"]["median_m"]
    ok_near = rep["nearest_worst_m"] <= med
    # PER BAND, NOT OVER THE DRUM. A mean over the whole floor is exactly the
    # statistic this project has been caught by before -- a whole-location gate
    # hiding a flat surface inside its own average (CLAUDE.md, layer 2b). The
    # drum is 45% arable by circumference, so an arable band at 27% bare pulls
    # a parkland band at 59% under a 50% mean and the gate goes green on a
    # landscape a third of which is empty.
    worst_band = max(rep["by_band"].items(), key=lambda kv: kv[1]["bare"])
    ok_bare = worst_band[1]["bare"] <= NEAR_BARE_VIEW_MAX
    ok = ok_near and ok_bare
    if verbose:
        label = ("the drum floor WITHOUT the near rung (the control)" if bare
                 else "the drum floor at eye level")
        print(f"\n{label}\n")
        print(f"  standing eye                      "
              f"{NEAR_EYE_H_M:.2f} m, fov {NEAR_FOV_DEG:.0f} deg (player.gd)")
        print(f"  the below-horizon frame           bottom edge "
              f"{rep['split']['bottom_m']:.2f} m, MEDIAN "
              f"{med:.2f} m, upper quarter {rep['split']['quarter_m']:.2f} m")
        print(f"  standing positions swept          {rep['positions']} "
              f"({rep['skipped_road_or_water']} skipped as road or water, "
              f"{rep['skipped_indoors']} as inside a building)")
        print(f"  near-field stands, median         {rep['near_items_median']}")
        print(f"  features within {rep['split']['quarter_m']:5.2f} m, median  "
              f"{rep['per_ha_median']:,.0f} per hectare")
        print(f"  nearest thing standing, median    "
              f"{rep['nearest_median_m']:,.2f} m")
        print(f"  nearest thing standing, WORST     "
              f"{rep['nearest_worst_m']:,.2f} m at {rep['nearest_worst_at']} "
              f"({rep['nearest_worst_band']}) "
              f"against the {med:.2f} m median  "
              f"{'PASS' if ok_near else 'FAIL'}")
        print(f"  below-horizon view that is BARE   "
              f"{rep['bare_mean']:.1%} over the drum; WORST BAND "
              f"{worst_band[0]} at {worst_band[1]['bare']:.1%} "
              f"(floor {NEAR_BARE_VIEW_MAX:.0%})  "
              f"{'PASS' if ok_bare else 'FAIL'}")
        print("\n  by land-use band")
        for b, v in rep["by_band"].items():
            print(f"    {b:<12} {v['n']:>4} positions, bare {v['bare']:.1%}, "
                  f"worst nearest {v['worst']:,.1f} m")
        print(f"\n  {'PASS' if ok else 'FAIL'}\n")
    return ok, rep


def derive_near_density(ladder=(1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0),
                        samples=12, z_samples=6, verbose=True):
    """The SMALLEST density multiple at which every band passes both floors.

    Ascending rather than bisecting, and that is deliberate: neither statistic
    is guaranteed monotone in the density -- adding a stand can move the worst
    standing position somewhere else entirely -- so a bisection would be
    assuming a property nobody has checked. Eight evaluations of a 25 s sweep
    is cheap enough to do the honest thing.
    """
    rows = []
    best = None
    for gnum in ladder:
        ok, rep = near_gate(verbose=False, samples=samples,
                            z_samples=z_samples, gain=gnum)
        wb = max(rep["by_band"].items(), key=lambda kv: kv[1]["bare"])
        cost = near_worst_cost(samples=8, gain=gnum)["triangles"]
        rows.append({"gain": gnum, "pass": ok,
                     "worst_nearest_m": rep["nearest_worst_m"],
                     "worst_band": wb[0], "worst_band_bare": wb[1]["bare"],
                     "near_worst_tris": cost})
        if ok and best is None:
            best = gnum
        if verbose:
            print(f"  gain {gnum:>4.1f}  worst nearest "
                  f"{rep['nearest_worst_m']:>6.2f} m  worst band "
                  f"{wb[0]:<11} {wb[1]['bare']:.1%}  "
                  f"near worst {cost:>7,} tri  "
                  f"{'PASS' if ok else 'FAIL'}")
    return best, rows


# ---------------------------------------------------------------------------
# DEGENERACY -- five gazetteer rows, one measurement
# ---------------------------------------------------------------------------
# `docs/aaa-scorecard.json`, `garden_townscape` round 2, severity major, R3:
#
#   "Five distinct gazetteer rows -- the drum end caps, the three radial spokes,
#   the sub-floor deck stack under the Garden, the Garden itself and the radial
#   transport tubes -- report the IDENTICAL measurement: 121,976 tri,
#   5,764,561 m2, lam 0.112, 85.2% of floor, FAIL. They all resolve to one
#   shared drum mesh."
#
# That is `deck.py --degeneracy`'s question at drum scale, and the cause is one
# line: `directory.PLACES` gives all five `module="interior"`, and
# `density.MODULE_MESH["interior"]` returns the WHOLE DRUM. Five places, one
# mesh, one number -- so the gate has five rows it cannot fail individually.
#
# The fix has two halves and only the second is a content problem:
#
#   1. MEASURE EACH PLACE ON ITS OWN FOOTPRINT. Every one of the five carries
#      (angle_deg, z_m) and a footprint in `directory.PLACES`; the drum geometry
#      inside that footprint is a different mesh for each. `place_mesh()` below
#      does exactly that, and `--degeneracy` hashes the five.
#   2. GIVE THEM SOMETHING TO DIFFER BY. Before this module the Garden's own
#      footprint held 22 objects and the other four held nothing, so half the
#      fix would have produced five hashes over the same empty ground.
#
# `density.py` is not this module's file. `--degeneracy` proves the fix and the
# patch that routes `_m_interior` through it is printed by `--patch`.


def _drum_places():
    """The register's drum rows, read from `directory.PLACES` rather than
    listed here -- a second copy of a five-row list is a second copy."""
    import directory as D                                       # noqa: PLC0415
    out = []
    for p in D.PLACES:
        if p.get("module") == "interior" or p["key"] in (
                "the_garden", "garden_town"):
            out.append(p)
    return out


def place_mesh(place, pad_m=0.0):
    """Drum geometry inside one register place's footprint.

    Ground, dressing and townscape, clipped to the place's own (angle, z)
    footprint. What makes five rows five measurements instead of one.
    """
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    a0 = place["angle_deg"]
    z0 = place["z_m"]
    fa, fz = place["footprint"]
    half_a_deg = math.degrees((fa / 2.0 + pad_m) / dg.FLOOR_R)
    half_z = fz / 2.0 + pad_m

    def inside(p):
        x, y, z = p
        if not (z0 - half_z <= z <= z0 + half_z):
            return False
        a = math.degrees(math.atan2(y, x)) % 360.0
        d = abs(((a - a0 + 180.0) % 360.0) - 180.0)
        return d <= half_a_deg

    eye, _up = dg.stand_on_ground(schema, profile, sector, a0, z0)
    parts = []
    gv, gt, _gg, _gm = dg.visible_set(eye)
    parts.append((gv, gt))
    dv, dt, _dg2, _dm = dressing_set(eye)
    parts.append((dv, dt))
    tv, tt, _tg = gd.townscape(schema, profile, sector)
    parts.append((tv, tt))
    parts.append(it.drum_spokes(schema, profile, sector)[:2])
    parts.append(it.drum_guideways(schema, profile, sector)[:2])
    for e in ("fore", "aft"):
        parts.append(it.drum_end_cap(schema, profile, sector, e)[:2])

    V, T = [], []
    for v, t in parts:
        off = len(V)
        V.extend(v)
        for a, b, c in t:
            if inside(v[a]) or inside(v[b]) or inside(v[c]):
                T.append((a + off, b + off, c + off))
    return V, T


def place_signature(place):
    """A geometry hash of one place's own footprint. Identity, not similarity --
    the same instrument `deck.py --degeneracy` uses, at drum scale."""
    V, T = place_mesh(place)
    h = hashlib.blake2b(digest_size=8)
    h.update(f"{len(T)}|".encode())
    for a, b, c in T:
        for i in (a, b, c):
            x, y, z = V[i]
            h.update(f"{x:.3f},{y:.3f},{z:.3f};".encode())
    return h.hexdigest(), len(T)


def degeneracy_report():
    rows = []
    for p in _drum_places():
        sig, n = place_signature(p)
        rows.append({"key": p["key"], "title": p.get("name", ""),
                     "triangles": n, "hash": sig})
    return rows


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def population_report():
    fld = field()
    by_kind = {}
    for f in fld["points"]:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
    trees = sum(len(f.members) for f in fld["points"] if f.kind == "copse")
    trees += by_kind.get("tree", 0)
    by_band = {}
    for f in fld["points"]:
        by_band[f.band] = by_band.get(f.band, 0) + 1
    line_len = {}
    for ln in fld["lines"]:
        line_len[ln.kind] = line_len.get(ln.kind, 0.0) + ln.length_m()
    area = 2.0 * math.pi * dg.FLOOR_R * (dg.Z1 - dg.Z0)
    return {
        "area_m2": round(area),
        "point_features": len(fld["points"]),
        "line_features": len(fld["lines"]),
        "by_kind": dict(sorted(by_kind.items())),
        "by_band": dict(sorted(by_band.items())),
        "individual_trees": trees,
        "line_length_m": {k: round(v) for k, v in sorted(line_len.items())},
    }


def _field_digest():
    fld = field()
    h = hashlib.blake2b(digest_size=8)
    for f in fld["points"]:
        h.update(f"{f.kind}:{f.proto}:{f.angle_deg:.4f}:{f.z_m:.3f}:"
                 f"{f.ground_r:.3f}:{f.yaw:.4f}:{f.scale:.4f}:"
                 f"{len(f.members)}:{f.radius_m:.3f}|".encode())
    for ln in fld["lines"]:
        h.update(f"{ln.kind}:{len(ln.points)}:{ln.length_m():.3f}:"
                 f"{ln.height_m:.3f}|".encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _signed_volume(v, t):
    s = 0.0
    for a, b, c in t:
        p, q, r = v[a], v[b], v[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0


def _boundary_edges(t):
    seen = {}
    for a, b, c in t:
        for p, q in ((a, b), (b, c), (c, a)):
            k = (min(p, q), max(p, q))
            seen[k] = seen.get(k, 0) + 1
    return sum(1 for n in seen.values() if n == 1), \
        sum(1 for n in seen.values() if n > 2)


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

    # --- prototypes are closed solids, correctly wound -------------------
    # LEVEL 0 OF A TREE AND A BLOCK IS `garden.py`'s, NOT THIS MODULE'S, AND IT
    # IS NOT A CLOSED SOLID. Measured here rather than assumed either way:
    # `garden.tree()` has 1,048 boundary edges over the eight prototypes used
    # here -- 131 a tree, because the trunk is an open tube at both ends
    # (`_taper` caps neither by default) and every `_limb` is open at both ends
    # -- and `garden.block_building()` has 2,304, i.e. 288 each. None shows the
    # background: the limb ends are inside their own foliage lobes, the trunk
    # top is inside the crown lobe and the trunk bottom is under the ground.
    # So this is a ROBUSTNESS finding rather than a visible one, and closing it
    # would cost ~116 triangles on the most-instanced object on the drum for no
    # change to any frame. It is PINNED rather than accepted: if either count
    # moves, something changed in the object 1,597 copies of which stand on the
    # drum floor, and this says so.
    # SESSION 4q MOVED BOTH, AND THE PIN DID ITS JOB by going red. `garden.py`
    # was rebuilt off craft 1: the tree's open edges are now the open ends of
    # `garden._sweep`'s parallel-transported tubes rather than `_taper`/`_limb`'s
    # caps, and the TOWN BLOCK'S COUNT FELL BY 1,728 -- the terraced mass, with
    # its setback tiers and slab caps, closes far more than it opens. A pin that
    # moves in the direction nobody predicted is worth more than one that holds.
    #
    # BOTH NUMBERS ARE MEASURED HERE, NOT TAKEN FROM A REPORT. The builder's
    # handover gave `town_block: 960`; re-measured on the delivered file it is
    # **576**, and pinning 960 turned the gate red on correct content. A pin is
    # a record of what the code does, so it is read off the code -- taking one
    # from prose is how a gate ends up asserting a number nobody computed.
    GARDEN_OPEN_EDGES = {"tree": 1240, "town_block": 576}
    for kind, want in GARDEN_OPEN_EDGES.items():
        got = nonman = 0
        for i in range(PROTOTYPES):
            o, n = _boundary_edges(prototype(kind, i, 0)[1])
            got += o
            nonman += n
        check(f"garden's {kind} still has its recorded {want} open edges "
              f"over the eight prototypes",
              got == want, f"{got} -- garden.py's level-0 generator changed")
        check(f"garden's {kind} is manifold", nonman == 0, str(nonman))

    for kind in list(_PROTO_BUILDERS) + ["town_block"]:
        for lv in range(4):
            v, t, g = prototype(kind, 0, lv)
            check(f"{kind} L{lv} builds", len(t) > 0, f"{len(t)} tri")
            if not (lv == 0 and kind in GARDEN_OPEN_EDGES):
                check(f"{kind} L{lv} has positive signed volume",
                      _signed_volume(v, t) > 0.0,
                      f"{_signed_volume(v, t):.3f}")
                open_e, nonman = _boundary_edges(t)
                check(f"{kind} L{lv} is a closed solid",
                      open_e == 0 and nonman == 0,
                      f"{open_e} open, {nonman} non-manifold")
            nm = [n for n, _a, _b in g]
            check(f"{kind} L{lv} tags every triangle",
                  sum(b - a for _n, a, b in g) == len(t),
                  f"{sum(b - a for _n, a, b in g)} of {len(t)}")
            check(f"{kind} L{lv} names only garden groups",
                  all(n.startswith("garden_") for n in nm), str(nm[:3]))
    # ...and a coarser level is genuinely cheaper. A LOD chain whose levels do
    # not descend is a chain that costs triangles and buys nothing, which is
    # the defect `drum_ground` records in its own first attempt.
    for kind in list(_PROTO_BUILDERS) + ["town_block"]:
        counts = [proto_tris(kind, 0, lv) for lv in range(4)]
        check(f"{kind} LOD levels descend", all(
            counts[i] >= counts[i + 1] for i in range(3)), str(counts))

    # --- the ribbon is a solid, not a folded sheet -----------------------
    V, T, G = [], [], []
    pts = [(10.0 + i * 0.4, 5000.0 + i * 12.0, dg.FLOOR_R - 1.0)
           for i in range(6)]
    _ribbon(V, T, G, pts, HEDGE_H_M, HEDGE_W_M, "garden_hedge",
            "garden_foliage", 8.0, 0.0)
    open_e, nonman = _boundary_edges(T)
    check("a hedgerow run is closed", open_e == 0, f"{open_e} open edges")
    check("a hedgerow run is manifold", nonman == 0, f"{nonman} shared >2")
    check("a hedgerow tags every triangle", len(G) == len(T),
          f"{len(G)} of {len(T)}")

    # --- placement is on the ground it says it is on ---------------------
    fld = field()
    check("the field has point features", len(fld["points"]) > 500,
          str(len(fld["points"])))
    check("the field has line features", len(fld["lines"]) > 50,
          str(len(fld["lines"])))
    worst = 0.0
    for f in fld["points"][::37]:
        h, _k = _ground(*_station_to_uw(f.angle_deg, f.z_m))
        worst = max(worst, abs((dg.FLOOR_R - h) - f.ground_r))
    check("every feature stands on the heightfield, not on the datum",
          worst < 0.05, f"worst {worst:.3f} m off the sampled ground")

    # --- nothing is placed in a band it does not belong in ---------------
    bad = []
    for f in fld["points"]:
        u, _w = _station_to_uw(f.angle_deg, f.z_m)
        band = _band_at(u)
        if f.band and band != f.band:
            bad.append((f.kind, f.band, band))
    check("no feature is in the wrong land-use band", not bad, str(bad[:4]))
    # ...and the strongest form of it: a building on a field is the error
    # `garden._selftest` already guards for its twelve blocks, and this is the
    # same guard over 800.
    onfield = [f.kind for f in fld["points"]
               if f.kind in ("town_block", "lamp")
               and _band_at(_station_to_uw(f.angle_deg, f.z_m)[0]) != "settlement"]
    check("no building stands in a field", not onfield, str(onfield[:4]))
    # ...and the converse, which nothing checked: a hedgerow in the town.
    inbad = [ln.kind for ln in fld["lines"] if ln.kind == "hedgerow"
             and _band_at(_station_to_uw(ln.points[0][0], ln.points[0][1])[0])
             != "arable"]
    check("no hedgerow runs through the town", not inbad, str(inbad[:4]))

    # --- the hedgerow geometry sits on the hedgerow TAG -------------------
    # The tag comes from the forward parcel map and the geometry from the
    # inverse; if the inverse were wrong the hedge would stand beside its own
    # tagged strip, which no render would show and no other assertion here
    # would catch.
    off = []
    for ln in fld["lines"][:40]:
        if ln.kind != "hedgerow":
            continue
        for (a, z, _r) in ln.points[::5]:
            u, w = _station_to_uw(a, z)
            _p, d_edge, _c = dg._parcel(u, w, dg.PARCELS_A, dg.PARCELS_Z,
                                        dg.PARCEL_WARP_M, dg.SEED + "/parcel")
            off.append(d_edge)
    check("hedgerow geometry lands on the tagged parcel boundary",
          off and max(off) < dg.HEDGE_W_M,
          f"worst {max(off) if off else -1:.2f} m from the edge against a "
          f"{dg.HEDGE_W_M:.1f} m tagged strip")

    # --- the LOD chain fits the budget it was solved against -------------
    w = worst_case_cost(samples=12)
    check("the worst standing position fits the dressing allowance",
          w["triangles"] <= DRESSING_TRIS,
          f"{w['triangles']:,} against {DRESSING_TRIS:,} at {w['at']}")
    # ...and it SPENDS it. A LOD chain tuned so far down that it is always
    # cheap is the same failure as an unspent budget, which is the finding this
    # module exists to close.
    check("...and spends at least half of it",
          w["triangles"] >= DRESSING_TRIS * 0.5,
          f"{w['triangles']:,} of {DRESSING_TRIS:,}")
    # The whole drum plus the dressing stays inside budget.py's drum allowance.
    #
    # THIS CHECK WAS ASSERTING A HARD-CODED COPY OF ANOTHER MODULE'S COST AND
    # THE COPY HAD GONE STALE. It read `fixed = 75_968`, a number this module's
    # own docstring derives as "end caps 15,072 + guideways 11,796 + spokes 516
    # + core 13,340 + trams 12,624 + garden.townscape 22,620". `garden.townscape`
    # is **51,026** as of session 4q -- it was rebuilt off craft 1 in the same
    # session -- so the true fixed total is **104,374**, and the assertion was
    # passing with 28,406 triangles it could not see. That is this project's
    # oldest defect in a new costume: two copies of a number, one updated.
    #
    # It is now MEASURED from the same parts `export_scene.drum_parts` emits,
    # and the recorded figure below is a pin so that the next change to any of
    # them fails here and names itself instead of being absorbed.
    fixed, per_part = drum_fixed_cost()
    check("the drum's fixed parts still cost what is recorded",
          fixed == DRUM_FIXED_TRIS,
          f"{fixed:,} against a recorded {DRUM_FIXED_TRIS:,}: {per_part}")
    # AND THE BUDGET IS ASKED AT ONE EYE, which is the only question a renderer
    # answers. The old form summed three worst cases taken at three different
    # standing positions, which is not a frame anybody draws.
    import budget as B                                          # noqa: PLC0415
    tot = drum_worst_eye(samples=12)
    check("the whole drum still fits its own budget",
          tot["triangles"] <= B.DRUM["visible_set_tris"],
          f"{tot['triangles']:,} against {B.DRUM['visible_set_tris']:,} at "
          f"{tot['at']} -- fixed {tot['fixed']:,} (townscape {per_part.get('townscape', 0):,}) "
          f"+ ground {tot['ground']:,} + dressing {tot['dressing']:,}. "
          f"THIS IS AN HONEST RED AND IT PREDATES THE NEAR RUNG: the drum went "
          f"over when garden.townscape grew 22,620 -> 51,026 and nothing "
          f"recomputed DRESSING_TRIS. budget.DRUM is not this module's file")

    # --- determinism -----------------------------------------------------
    d1 = _field_digest()
    global _FIELD
    _FIELD = None
    d2 = _field_digest()
    check("the field is identical when rebuilt", d1 == d2, f"{d1} vs {d2}")
    check("the field still has its committed placement", d1 == FIELD_DIGEST,
          f"{d1} != {FIELD_DIGEST} -- the dressing moved. If that was "
          f"deliberate, look at a render and update FIELD_DIGEST")
    # `random` is forbidden, the same guard `drum_ground` carries, and for the
    # same reason: a live call through it would give a different drum per run.
    import random as _rnd                                       # noqa: PLC0415
    _names = [n for n in dir(_rnd) if not n.startswith("_")
              and callable(getattr(_rnd, n, None))
              and n not in ("Random", "SystemRandom")]
    _saved = {n: getattr(_rnd, n) for n in _names}
    _tripped = []

    def _forbid(name):
        def f(*_a, **_k):
            _tripped.append(name)
            raise AssertionError(f"drum_dressing called random.{name}()")
        return f
    try:
        for n in _names:
            setattr(_rnd, n, _forbid(n))
        _FIELD = None
        field()
        dressing_set(dg.stand_on_ground(schema, profile, sector, 20.0, 4700.0)[0])
    finally:
        for n, fn in _saved.items():
            setattr(_rnd, n, fn)
    check("nothing here reaches the random module", not _tripped, str(_tripped))

    # --- the emptiness gate, and its negative control --------------------
    passed, rep = gate(verbose=False)
    check("the drum floor is not empty", passed,
          f"worst {rep['worst_m']} m, occupancy {rep['occupancy']:.1%}")
    bare_ok, bare = gate(bare=True, verbose=False)
    check("...and the gate FAILS on what the drum had before this module",
          not bare_ok,
          f"garden.townscape alone: worst {bare['worst_m']} m, "
          f"occupancy {bare['occupancy']:.1%}")

    # --- the near rung ---------------------------------------------------
    # Every prototype is a closed solid. `dressing._cyl` shipped open at the
    # bottom and wound inside out for four sessions (CLAUDE.md, 3x) at a
    # fraction of this instance count; a near stand is the object a player's
    # eye is 3 m from.
    for item in ("crop", "tussock", "scrub", "margin", "reedtuft", "stone",
                 "boxhedge", "wall"):
        for lod in (0, 1, 2):
            v, t, g = _near_proto(item, "garden_hedge", 0, lod)
            open_e, nonman = _boundary_edges(t)
            check(f"near {item} rung {lod} is a closed solid",
                  open_e == 0 and nonman == 0,
                  f"{open_e} open, {nonman} non-manifold")
            check(f"near {item} rung {lod} winds outward",
                  _signed_volume(v, t) > 0.0, f"{_signed_volume(v, t):.4f}")
            check(f"near {item} rung {lod} tags every triangle",
                  sum(b - a for _n, a, b in g) == len(t),
                  f"{sum(b - a for _n, a, b in g)} of {len(t)}")
        counts = [len(_near_proto(item, "garden_hedge", 0, lv)[1])
                  for lv in (0, 1, 2)]
        check(f"near {item}'s three rungs descend in cost",
              counts[0] >= counts[1] >= counts[2], str(counts))

    # The near rung is deterministic in WORLD space, which is the property that
    # makes it a scatter and not a swarm following the camera. Two eyes 12 m
    # apart must agree about every stand they can both see.
    e1, _u1 = dg.stand_on_ground(schema, profile, sector, 20.0, 4700.0)
    e2, _u2 = dg.stand_on_ground(schema, profile, sector, 20.0, 4712.0)
    def _keyset(eye):
        return {(x.item, round(x.angle_deg, 6), round(x.z_m, 3),
                 round(x.scale, 4)) for x in near_field(eye)
                if math.dist(x.position(), eye) < NEAR_FULL_M - 12.0
                and math.dist(x.position(), e1) < NEAR_FULL_M - 12.0
                and math.dist(x.position(), e2) < NEAR_FULL_M - 12.0}
    k1, k2 = _keyset(e1), _keyset(e2)
    check("the near rung is the same field from two different eyes",
          k1 and k1 == k2,
          f"{len(k1)} vs {len(k2)}, {len(k1 ^ k2)} disagree")

    # Nothing grows inside a building. `garden`'s equivalent guard FIRED during
    # its own build this session at 0.70 m, which is why this one exists.
    inside = 0
    for (ang, z) in ((112.0, 4900.0), (100.0, 4700.0), (300.0, 5100.0)):
        eye, _up2 = dg.stand_on_ground(schema, profile, sector, ang, z)
        keep = _near_keepout(eye, NEAR_R_M)
        for x in near_field(eye):
            if _in_keepout(keep, x.angle_deg, x.z_m, x.ground_r):
                inside += 1
    check("no near stand grows inside a building footprint", inside == 0,
          f"{inside} stands inside a footprint")

    # The gate, and the control that shows it can fail. The control is not a
    # stub: it is the drum EXACTLY as session 4q left it, with the far field's
    # 1,945 features all present and only the near rung withheld.
    n_ok, n_rep = near_gate(verbose=False)
    check("the drum floor is not bare at eye level", n_ok,
          f"worst nearest {n_rep['nearest_worst_m']} m, "
          f"bare {n_rep['bare_mean']:.1%}")
    nb_ok, nb = near_gate(bare=True, verbose=False)
    check("...and the near gate FAILS on the drum without the near rung",
          not nb_ok,
          f"worst nearest {nb['nearest_worst_m']} m, bare {nb['bare_mean']:.1%}")
    check("...and it fails for the right reason -- nothing near, not nothing at all",
          nb["nearest_worst_m"] > 10.0 * n_rep["nearest_worst_m"],
          f"{nb['nearest_worst_m']} vs {n_rep['nearest_worst_m']}")
    # Every band, not the drum-wide mean: a whole-drum average hides a band.
    check("every land-use band is measured by the near gate",
          set(n_rep["by_band"]) >= {"arable", "settlement", "parkland", "water"},
          str(sorted(n_rep["by_band"])))
    # A stand must sit ON the ground it was sampled from, like every other
    # feature here. The tolerance is the sink depth, not zero.
    off = 0.0
    for x in near_field(e1)[::17]:
        h, _k = _ground(*_station_to_uw(x.angle_deg, x.z_m))
        off = max(off, abs((dg.FLOOR_R - h) - x.ground_r))
    check("every near stand is on the heightfield", off < 4.1,
          f"worst {off:.3f} m -- one cell of ground relief is allowed")

    # --- degeneracy ------------------------------------------------------
    rows = degeneracy_report()
    sigs = [r["hash"] for r in rows]
    check("every drum register row has its own geometry",
          len(set(sigs)) == len(sigs),
          f"{len(set(sigs))} distinct of {len(sigs)}")
    check("...and there are at least the five the reviewer named",
          len(rows) >= 5, f"{len(rows)} rows")

    # --- every group resolves to a material ------------------------------
    import materials as M                                       # noqa: PLC0415
    names = set()
    for kind in list(_PROTO_BUILDERS) + ["town_block"]:
        for lv in range(4):
            names |= {n for n, _a, _b in prototype(kind, 0, lv)[2]}
    names |= {"garden_hedge", "garden_foliage"}
    # ...and the near rung's, which are mostly the GROUND's own groups: a crop
    # stand in an `arable2` parcel emits `ground_arable_2`, so it takes the
    # albedo of the parcel it stands in by construction rather than by an
    # authored colour that would drift. Every kind a recipe can fire on is
    # enumerated from `NEAR_COVER` rather than listed here.
    names |= set(_NEAR_GROUP.values())
    names |= {dg._KIND_GROUP[k] for k in NEAR_COVER if k in dg._KIND_GROUP}
    unbound = sorted(n for n in names if M.resolve_any(n, "drum") is None)
    check("every group this module emits has a material in the drum scene",
          not unbound, str(unbound))

    print(f"\n{ok}/{ok + fail} passed")
    return fail == 0


PATCH = '''\
--- a/station/density.py
+++ b/station/density.py
@@ MODULE_MESH / _m_interior
 def _m_interior(s, p):
+    """...and it is ONE mesh for FIVE register rows, which is the R3 finding
+    in docs/aaa-scorecard.json: drum_endcaps, drum_spokes, subfloor_stack,
+    the_garden and radial_tubes all carry module="interior", so all five score
+    121,976 tri / 5,764,561 m2 / lam 0.112 and the gate cannot fail any of them
+    on its own. `drum_dressing.place_mesh(place)` clips the drum to the row's
+    OWN footprint, which is what makes five rows five measurements."""
     ...

@@ module_mesh(schema, profile, module)   -- add a per-PLACE branch
+def place_drum_mesh(schema, profile, place):
+    import drum_dressing as dd
+    return dd.place_mesh(place)
+
 # and in report(): for a place whose module is "interior" and whose sector is
 # the drum, call place_drum_mesh(schema, profile, place) instead of
 # module_mesh(schema, profile, "interior").
'''


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true",
                    help="what stands on the drum floor")
    ap.add_argument("--gate", action="store_true",
                    help="the emptiness gate")
    ap.add_argument("--bare", action="store_true",
                    help="run the gate on the pre-existing content (the control)")
    ap.add_argument("--near", action="store_true",
                    help="the near-field gate: what a standing player sees")
    ap.add_argument("--derive-near", action="store_true",
                    help="re-solve NEAR_DENSITY_GAIN against the near gate")
    ap.add_argument("--degeneracy", action="store_true",
                    help="one geometry hash per drum register row")
    ap.add_argument("--derive", action="store_true",
                    help="re-solve LOD_SCALE_M against DRESSING_TRIS")
    ap.add_argument("--cost", metavar="DEG,Z",
                    help="triangles from one standing position")
    ap.add_argument("--patch", action="store_true",
                    help="print the density.py patch this module needs")
    args = ap.parse_args(argv)

    if args.patch:
        print(PATCH)
        return 0

    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)

    if args.report:
        rep = population_report()
        print("\nWHAT STANDS ON THE DRUM FLOOR\n")
        print(f"  ground area                {rep['area_m2']:,} m2")
        print(f"  point features             {rep['point_features']:,}")
        print(f"  line features              {rep['line_features']:,}")
        print(f"  individual trees           {rep['individual_trees']:,}")
        print("\n  by kind")
        for k, n in rep["by_kind"].items():
            print(f"    {k:<14} {n:>7,}")
        print("\n  by land-use band")
        for k, n in rep["by_band"].items():
            print(f"    {k:<14} {n:>7,}")
        print("\n  line length")
        for k, n in rep["line_length_m"].items():
            print(f"    {k:<14} {n:>7,} m")
        lr = lod_report()
        print(f"\n  LOD switch distances       {lr['switch_m']} m")
        for row in lr["levels"]:
            px = row["omitted_feature_px"]
            print(f"    L{row['level']}  tree {row['tree_triangles']:>4} tri, "
                  f"median edge {row['median_edge_m']:.2f} m, "
                  f"used from {row['used_from_m']:>7.1f} m"
                  + (f", the detail it drops subtends {px:.2f} px there"
                     if px is not None else ""))
        sp = near_horizon_split()
        print(f"\n  THE NEAR RUNG (level -1)")
        print(f"    reaches                  {NEAR_R_M:.0f} m "
              f"(full to {NEAR_FULL_M:.1f} m, fine to {NEAR_FINE_M:.1f} m)")
        print(f"    on the ground's lattice  "
              f"{2 * math.pi * dg.FLOOR_R / dg.CELLS_A:.2f} x "
              f"{(dg.Z1 - dg.Z0) / dg.CELLS_Z:.2f} m cells, "
              f"density x{NEAR_DENSITY_GAIN:g} of the garden's")
        print(f"    the frame it is for      bottom edge {sp['bottom_m']:.2f} m,"
              f" MEDIAN {sp['median_m']:.2f} m at "
              f"{NEAR_EYE_H_M:.2f} m / {NEAR_FOV_DEG:.0f} deg")
        nw = near_worst_cost(samples=8)
        print(f"    worst standing position  {nw['triangles']:,} tri at "
              f"{nw['at']}")
        w = worst_case_cost()
        print(f"\n  worst standing position    {w['triangles']:,} tri at "
              f"{w['at']}, allowance {DRESSING_TRIS:,}")
        print(f"  per level at that eye      {w['per_level']}")
        area = rep["area_m2"]
        print(f"  dressing density           {w['triangles'] / area:.4f} tri/m2")
        return 0

    if args.gate:
        okc, _ = gate(bare=args.bare)
        return 0 if okc else 1

    if args.near:
        okc, _ = near_gate(bare=args.bare)
        return 0 if okc else 1

    if args.derive_near:
        print("\nNEAR_DENSITY_GAIN, solved against the near-field gate\n")
        best, _rows = derive_near_density()
        print(f"\n  smallest passing gain {best}   recorded "
              f"{NEAR_DENSITY_GAIN}\n")
        return 0

    if args.degeneracy:
        rows = degeneracy_report()
        print("\nTHE DRUM'S REGISTER ROWS, ONE HASH EACH\n")
        for r in rows:
            print(f"  {r['key']:<18} {r['triangles']:>8,} tri  {r['hash']}  "
                  f"{r['title']}")
        sigs = [r["hash"] for r in rows]
        print(f"\n  {len(set(sigs))} distinct geometries of {len(sigs)} rows  "
              f"{'PASS' if len(set(sigs)) == len(sigs) else 'FAIL'}\n")
        return 0 if len(set(sigs)) == len(sigs) else 1

    if args.derive:
        s, n = derive_lod_scale()
        print(f"\nLOD_SCALE_M = {s:.1f}   (worst case {n:,} of "
              f"{DRESSING_TRIS:,})")
        print(f"recorded    = {LOD_SCALE_M}")
        lr = lod_report(s)
        print(f"switch distances {lr['switch_m']} m")
        for row in lr["levels"]:
            px = row["omitted_feature_px"]
            if px is not None:
                print(f"  L{row['level']} from {row['used_from_m']:.0f} m: "
                      f"drops {row['median_edge_m']:.2f} m detail = "
                      f"{px:.2f} px")
        return 0

    if args.cost:
        a, z = (float(x) for x in args.cost.split(","))
        eye, _up = dg.stand_on_ground(schema, profile, sector, a, z)
        n, per = dressing_cost(eye)
        print(f"{n:,} triangles, features per level {per}")
        return 0

    return 0 if _selftest() else 1


if __name__ == "__main__":
    sys.exit(main())
