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
BLOCK_BANDS = 3                     # lit window bands up a facade

# --- hard landscape, all INV-072, all from 29a's extraction -------------------
PATH_W_M = 2.4
PATH_PITCH_M = 14.0
KERB_W_M = 0.15
KERB_H_M = 0.12
HEDGE_RUNS = 18
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
BOUNDARIES = 9
BOUNDARY_W_M = 0.35
BOUNDARY_H_M = 0.55

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


def block_building(seed):
    """One low-rise garden block, articulated to its detail floor (INV-072).

    WHAT THIS REPLACES, and why it is worth the comment. The old version was a
    single `_box` plus `BLOCK_BANDS` slightly-larger boxes for the window bands:
    48 triangles, and the owner looked at a render of it and called these
    "shitty little cubes". The description was exact. Its docstring said "Cheap
    by design" and the module asserted `dens < 0.06 tri/m2`, so the cheapness was
    not an oversight -- it was enforced.

    A PROUD BAND IS THE WORST WAY TO SPEND A TRIANGLE HERE. A band standing 6 cm
    off the facade draws two lines, its top and bottom arris. The same triangles
    spent on a RECESSED opening draw the frame edge, the reveal, the sill and the
    head -- and the reveal's own dihedral is 90 deg, far above the 3.24 deg crease
    threshold, so every one of them survives to the frame (`station/density.py`,
    INV-070). This builds openings, not bands.

    Composition follows `garden.png` and `Babylon_5_2-22_29a.jpg`, both authority
    1: multi-storey, banded horizontally by expressed floor slabs, vertically by
    structural bays, glazed between, with a parapet and rooftop plant. Every
    proportion is logged in INV-072.
    """
    v, t, g = [], [], []
    L = BLOCK_MIN_M[0] + _u(seed, "L") * (BLOCK_MAX_M[0] - BLOCK_MIN_M[0])
    W = BLOCK_MIN_M[1] + _u(seed, "W") * (BLOCK_MAX_M[1] - BLOCK_MIN_M[1])
    H = BLOCK_MIN_M[2] + _u(seed, "H") * (BLOCK_MAX_M[2] - BLOCK_MIN_M[2])
    storeys = max(1, int(round(H / STOREY_M)))
    sh = H / storeys

    # The mass, inset behind its own plinth so the plinth reads as a line.
    _box(v, t, g, "garden_plinth", (-L / 2, 0.0, -W / 2),
         (L / 2, PLINTH_H_M, W / 2))
    _box(v, t, g, "garden_block",
         (-L / 2 + PLINTH_PROUD_M, 0.0, -W / 2 + PLINTH_PROUD_M),
         (L / 2 - PLINTH_PROUD_M, H, W / 2 - PLINTH_PROUD_M))

    xin, zin = L / 2 - PLINTH_PROUD_M, W / 2 - PLINTH_PROUD_M
    # Structural bays: pilasters standing proud on the two long elevations.
    bays = max(2, int(round((2 * xin) / BAY_W_M)))
    for i in range(bays + 1):
        x = -xin + 2 * xin * i / bays
        for zs in (-1, 1):
            _box(v, t, g, "garden_pilaster",
                 (x - PILASTER_W_M / 2, PLINTH_H_M, zs * zin),
                 (x + PILASTER_W_M / 2, H - CORNICE_H_M,
                  zs * (zin + PILASTER_PROUD_M)))
    # Expressed floor slabs, one line per storey all the way round.
    for i in range(1, storeys):
        y = i * sh
        _box(v, t, g, "garden_slab_band",
             (-xin - SLAB_PROUD_M, y - SLAB_T_M / 2, -zin - SLAB_PROUD_M),
             (xin + SLAB_PROUD_M, y + SLAB_T_M / 2, zin + SLAB_PROUD_M))
    # Recessed glazing, one opening per bay per storey, on both long faces.
    for i in range(bays):
        xc = -xin + 2 * xin * (i + 0.5) / bays
        for st in range(storeys):
            yb = st * sh + SILL_M
            yt = min(st * sh + sh - SLAB_T_M, yb + WIN_H_M)
            if yt - yb < 0.4:
                continue
            hw = min(BAY_W_M * 0.34, (2 * xin / bays) * 0.34)
            for zs in (-1, 1):
                zo = zs * zin
                zi = zs * (zin - REVEAL_M)
                _box(v, t, g, "garden_glazing",
                     (xc - hw, yb, min(zo, zi)), (xc + hw, yt, max(zo, zi)))
    # Cornice, parapet, and the plant no real roof is without.
    _box(v, t, g, "garden_cornice",
         (-xin - CORNICE_P_M, H - CORNICE_H_M, -zin - CORNICE_P_M),
         (xin + CORNICE_P_M, H, zin + CORNICE_P_M))
    _box(v, t, g, "garden_parapet",
         (-xin - CORNICE_P_M, H, -zin - CORNICE_P_M),
         (xin + CORNICE_P_M, H + PARAPET_H_M, zin + CORNICE_P_M))
    # SERVICES AND BALCONIES. These are where a facade earns its line cheaply,
    # and the arithmetic is worth recording because it decided the design. A
    # six-sided downpipe 8 m tall is 24 triangles and every one of its six
    # lateral arrises has a 60 deg dihedral, far above the 3.24 deg crease
    # threshold -- 48 m of visible line for 24 triangles, 2 m per triangle. A
    # panel-relief grid at 1 m pitch yields 0.17. Long thin prisms are twelve
    # times better line per triangle than the construction the budget bound is
    # derived from, which is why a real building's pipes, gutters, rails and
    # cills carry so much of what the eye reads as detail.
    for zs in (-1, 1):
        # Eaves gutter, one continuous run per long elevation.
        _box(v, t, g, "garden_gutter",
             (-xin - CORNICE_P_M, H - CORNICE_H_M - GUTTER_D_M,
              zs * (zin + CORNICE_P_M)),
             (xin + CORNICE_P_M, H - CORNICE_H_M,
              zs * (zin + CORNICE_P_M + GUTTER_D_M)))
        # Downpipes at the bay divisions.
        for i in range(0, bays + 1, max(1, bays // DOWNPIPES_PER_FACE)):
            x = -xin + 2 * xin * i / bays
            _taper(v, t, g, "garden_downpipe", x,
                   zs * (zin + PILASTER_PROUD_M + PIPE_R_M),
                   [(0.0, PIPE_R_M), (H - CORNICE_H_M, PIPE_R_M)],
                   seg=6, close_top=False)
        # A balcony per storey above the ground floor: slab, and a rail above
        # it. The rail is the line; the slab is the shadow line under it.
        for st in range(1, storeys):
            yb = st * sh
            _box(v, t, g, "garden_balcony",
                 (-xin * 0.72, yb - BALC_T_M, zs * zin),
                 (xin * 0.72, yb, zs * (zin + BALC_D_M)))
            for rk in range(BALC_RAILS):
                ry = yb + BALC_RAIL_H_M * (rk + 1) / BALC_RAILS
                _box(v, t, g, "garden_rail",
                     (-xin * 0.72, ry - RAIL_T_M / 2,
                      zs * (zin + BALC_D_M - RAIL_T_M)),
                     (xin * 0.72, ry + RAIL_T_M / 2,
                      zs * (zin + BALC_D_M)))
    # CONTINUOUS CILL AND HEAD BANDS. One box per storey per elevation, running
    # the whole facade: twelve triangles laying four lines the full length of the
    # building. Measured at 5.3 m of line per triangle, the best yield in this
    # module, and it is also just what a banded facade is -- 29a's building is
    # read as "banded" precisely because its openings share continuous cills.
    for st in range(storeys):
        for zs in (-1, 1):
            for y, nm in ((st * sh + SILL_M, "garden_cill"),
                          (min(st * sh + sh - SLAB_T_M,
                               st * sh + SILL_M + WIN_H_M), "garden_lintel")):
                _box(v, t, g, nm,
                     (-xin, y - BAND_T_M / 2, zs * zin),
                     (xin, y + BAND_T_M / 2, zs * (zin + BAND_P_M)))
    # Gutters and downpipes on the short elevations too -- a building does not
    # drain three sides.
    for xs in (-1, 1):
        _box(v, t, g, "garden_gutter",
             (xs * (zin * 0 + xin + CORNICE_P_M),
              H - CORNICE_H_M - GUTTER_D_M, -zin - CORNICE_P_M),
             (xs * (xin + CORNICE_P_M + GUTTER_D_M), H - CORNICE_H_M,
              zin + CORNICE_P_M))
        for k in range(2):
            z = -zin + 2 * zin * (k + 0.5) / 2
            _taper(v, t, g, "garden_downpipe",
                   xs * (xin + PIPE_R_M), z,
                   [(0.0, PIPE_R_M), (H - CORNICE_H_M, PIPE_R_M)],
                   seg=6, close_top=False)
    # Parapet handrail, four runs round the roof.
    for zs in (-1, 1):
        _box(v, t, g, "garden_rail",
             (-xin - CORNICE_P_M, H + PARAPET_H_M,
              zs * (zin + CORNICE_P_M) - RAIL_T_M / 2),
             (xin + CORNICE_P_M, H + PARAPET_H_M + RAIL_T_M,
              zs * (zin + CORNICE_P_M) + RAIL_T_M / 2))
    for xs in (-1, 1):
        _box(v, t, g, "garden_rail",
             (xs * (xin + CORNICE_P_M) - RAIL_T_M / 2, H + PARAPET_H_M,
              -zin - CORNICE_P_M),
             (xs * (xin + CORNICE_P_M) + RAIL_T_M / 2,
              H + PARAPET_H_M + RAIL_T_M, zin + CORNICE_P_M))
    # Roof service runs between the plant boxes.
    for k in range(ROOF_PIPES):
        pz = -zin * 0.6 + 1.2 * zin * (k + 0.5) / ROOF_PIPES
        _taper(v, t, g, "garden_downpipe", 0.0, 0.0,
               [(0.0, PIPE_R_M * 1.3), (1.0, PIPE_R_M * 1.3)],
               seg=6, close_top=False)
        # laid horizontally by hand: a run along x at roof level
        n0 = len(v)
        for xx in (-xin * 0.8, xin * 0.8):
            for kk in range(6):
                a = math.tau * kk / 6
                _r = PIPE_R_M * 1.3
                v.append((xx, H + ROOF_PIPE_H_M + _r * math.cos(a),
                          pz + _r * math.sin(a)))
        t0 = len(t)
        for kk in range(6):
            k2 = (kk + 1) % 6
            t += [(n0 + kk, n0 + k2, n0 + 6 + k2),
                  (n0 + kk, n0 + 6 + k2, n0 + 6 + kk)]
        g.append(("garden_downpipe", t0, len(t)))
    for j in range(2 + int(2 * _u(seed, "plant"))):
        px = -xin * 0.6 + 1.2 * xin * _u(seed, "px", j)
        pz = -zin * 0.5 + 1.0 * zin * _u(seed, "pz", j)
        pw = 0.8 + 1.4 * _u(seed, "pw", j)
        ph = 0.7 + 1.3 * _u(seed, "ph", j)
        _box(v, t, g, "garden_roof_plant",
             (px - pw / 2, H, pz - pw / 2), (px + pw / 2, H + ph, pz + pw / 2))
    return v, t, g, (L, W, H)


def tree(seed):
    """One broadleaf, articulated to its detail floor (INV-072).

    WHAT THIS REPLACES: a 0.44 m SQUARE BOX for a trunk and one 6-segment
    cylinder for the whole canopy. Thirty triangles, and it rendered as exactly
    what it was -- a hexagonal prism on a post. The owner called it a "sad excuse
    for a tree" and measured against its own floor it was at 2.2%: one visible
    line every 113 cm on a 7 m tree.

    A tree is a hard case for the line-density metric and it is worth saying why.
    Smooth tessellation buys NOTHING -- a 720-segment trunk draws only its two
    silhouette edges, because adjacent facets of a smooth cylinder sit under the
    3.24 deg crease threshold. Line comes from real changes in direction: the
    root flare, the branch collars, the taper breaks, and the intersections
    between overlapping foliage lobes. So the triangles go there.
    """
    v, t, g = [], [], []
    h = TREE_H_M * (0.75 + 0.5 * _u(seed, "th"))
    r0 = TRUNK_R_M * (0.85 + 0.3 * _u(seed, "tk"))
    fork = h * FORK_FRAC
    # Root flare, then two taper breaks to the fork. Each ring is a line.
    _taper(v, t, g, "garden_trunk", 0.0, 0.0,
           [(0.0, r0 * FLARE_K), (FLARE_H_M, r0),
            (fork * 0.45, r0 * 0.80), (fork * 0.8, r0 * 0.66),
            (fork, r0 * 0.58)], seg=TRUNK_SEG, close_top=False)
    # Limbs. Each is its own taper, so each collar creases against the trunk.
    limbs = 3 + int(3 * _u(seed, "nl"))
    for j in range(limbs):
        a = math.tau * (j + 0.35 * _u(seed, "la", j)) / limbs
        reach = TREE_R_M * (0.45 + 0.45 * _u(seed, "lr", j))
        rise = (h - fork) * (0.35 + 0.45 * _u(seed, "lh", j))
        ex, ez = reach * math.cos(a), reach * math.sin(a)
        br = r0 * (0.30 + 0.14 * _u(seed, "lb", j))
        # Trunk collar -> the foliage mass it carries. Two segments so the limb
        # has a bend in it, which is both what a branch does and another crease.
        mx, mz = ex * 0.45, ez * 0.45
        my = fork + rise * 0.62
        _limb(v, t, g, "garden_branch", (0.0, fork - 0.15, 0.0), (mx, my, mz),
              br * 1.6, br, seg=LIMB_SEG)
        _limb(v, t, g, "garden_branch", (mx, my, mz),
              (ex * 0.8, fork + rise, ez * 0.8), br, br * 0.62, seg=LIMB_SEG)
        # The limb's own foliage mass, at the end of the limb that reaches it.
        _lobe(v, t, g, "garden_foliage", ex * 0.8, fork + rise, ez * 0.8,
              TREE_R_M * (0.34 + 0.20 * _u(seed, "lf", j)),
              seg=LOBE_SEG, stacks=LOBE_STACKS)
    # A crown lobe over the fork ties the limb masses together.
    _lobe(v, t, g, "garden_foliage", 0.0, h - TREE_R_M * 0.35, 0.0,
          TREE_R_M * (0.52 + 0.16 * _u(seed, "cf")),
          seg=LOBE_SEG, stacks=LOBE_STACKS)
    return v, t, g


def place(verts, schema, profile, sector, angle_deg, z_m, ground_r=None):
    """Set locally-authored geometry on the drum surface.

    Local x is tangential, y is UP, z is along the station axis. On the drum UP
    IS INWARD, so local +y maps to DECREASING radius. Getting that backwards
    buries a building in the hull, which is the same failure that put the first
    drum camera five metres underground.

    The ground radius comes from the heightfield, so a building sits on the
    terrain it is actually standing on rather than on the nominal floor.
    """
    if ground_r is None:
        ground_r = dg.terrain_sample(schema, profile, sector,
                                     angle_deg, z_m)["radius_m"]
    out = []
    for x, y, z in verts:
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


def townscape(schema, profile, sector=None, angle_deg=112.0, z_m=4900.0,
              blocks=12, trees=10, seed="garden"):
    """The landmark, its setting, and a patch of the town around it."""
    if sector is None:
        sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)
    if not in_settlement(angle_deg):
        raise ValueError(f"{angle_deg} deg is not in a settlement band; "
                         f"bands are {settlement_arcs()}")

    V, T, G = [], [], []

    def emit(lv, lt, lg, a, z):
        off, t0 = len(V), len(T)
        V.extend(place(lv, schema, profile, sector, a, z))
        T.extend((p + off, q + off, r + off) for p, q, r in lt)
        G.extend((n, lo + t0, hi + t0) for n, lo, hi in lg)

    lv, lt, lg = setting()
    emit(lv, lt, lg, angle_deg, z_m)
    lv, lt, lg = hard_landscape(seed)
    emit(lv, lt, lg, angle_deg, z_m)
    lv, lt, lg = civic_landmark()
    emit(lv, lt, lg, angle_deg, z_m)

    # The town around it. Placed deterministically, and every one of them is
    # checked against the settlement band rather than assumed to be inside it.
    lo, hi = [b for b in settlement_arcs()
              if b[0] <= angle_deg % 360.0 < b[1]][0]
    placed = 0
    for i in range(blocks * 3):
        if placed >= blocks:
            break
        a = lo + 2.0 + _u(seed, "ba", i) * (hi - lo - 4.0)
        z = z_m + (_u(seed, "bz", i) - 0.5) * 260.0
        if abs(a - angle_deg) < 1.2:
            continue                       # keep the landmark's setting clear
        bv, bt, bg, _dims = block_building(f"{seed}-{i}")
        emit(bv, bt, bg, a, z)
        placed += 1
    for i in range(trees):
        a = lo + 1.0 + _u(seed, "ta", i) * (hi - lo - 2.0)
        z = z_m + (_u(seed, "tz", i) - 0.5) * 240.0
        tv, tt, tg = tree(f"{seed}-t{i}")
        emit(tv, tt, tg, a, z)

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
    check("the townscape is inside the drum's 0.5 tri/m2 surface gate",
          dens < 0.5, f"{dens:.4f} tri/m2 over {area:,.0f} m2")
    # No assertion stands in for the paragraph above. `"0.06" not in <a string
    # that never contains it>` was my first attempt and it was a third vacuous
    # check in one session -- a comment wearing an assertion's clothes. The real
    # gate is `station/density.py`, it fails on this module today, and CI runs it.

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


if __name__ == "__main__":
    sys.exit(_selftest())
