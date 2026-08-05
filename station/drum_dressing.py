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
  * **Streaming.** Everything here is built for one eye at one instant, exactly
    as `drum_ground.visible_set` is. Neither is a streamer.

Run:
    python3 station/drum_dressing.py                 # self-test
    python3 station/drum_dressing.py --report        # what stands on the drum
    python3 station/drum_dressing.py --gate          # the emptiness gate
    python3 station/drum_dressing.py --gate --bare   # ...shown failing
    python3 station/drum_dressing.py --degeneracy    # five drum rows, five hashes
    python3 station/drum_dressing.py --derive        # re-solve the LOD scale
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
# boundaries at a known scale. -- INV-450, authority 5
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
# than a regular two. -- INV-450
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
# patch boundaries and produce a visible grid at the LOD seams. -- INV-451
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
    global _FIELD
    if _FIELD is not None and not rebuild:
        return _FIELD
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
    return total, per


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
    return V, T, G, {
        "eye": tuple(round(x, 1) for x in eye),
        "triangles": len(T),
        "vertices": len(V),
        "features": len(fld["points"]) + len(fld["lines"]),
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
    fixed = 75_968
    ground = dg.worst_case_cost(samples=12)["triangles"]
    import budget as B                                          # noqa: PLC0415
    check("the whole drum still fits its own budget",
          fixed + ground + w["triangles"] <= B.DRUM["visible_set_tris"],
          f"{fixed + ground + w['triangles']:,} against "
          f"{B.DRUM['visible_set_tris']:,}")

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
