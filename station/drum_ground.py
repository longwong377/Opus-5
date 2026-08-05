#!/usr/bin/env python3
"""The habitat drum's ground: a heightfield over (angle, z), with distance LOD.

`interior.drum_interior()` emits the drum's inner surface as four flat
circumferential land-use bands. That was enough to judge composition -- it
proves the volume reads as a drum -- and it is not enough to stand on: it is a
cylinder with four different radii and no surface at all.

**The budget settles the approach before any aesthetics do.** `budget.py` gives
the drum 300,000 triangles of simultaneously-visible geometry, of which the
shell, caps, trusses and spokes already take 42,696. The remainder spread over
4.5 million m2 of inner surface is **0.06 triangles per square metre**. A
hedgerow modelled as geometry, at one quad per 10 m of hedge, would spend that
on the hedges alone. So the ground is a heightfield with aggressive distance
LOD: displacement carries the relief, texture carries everything finer than the
mesh can resolve, and mesh is reserved for what a person can walk up to.

What the reference establishes (authority 1 throughout):

`03-sector-blue/Babylon_5_2-22_34b.jpg` -- looking down the drum axis over the
agricultural half. Irregular four- and five-sided parcels in greens, olives and
tans; one large field carries visible parallel cultivation rows; pale roads wind
between them; darker tree masses scatter across a tan parcel; a white settlement
block sits against the end cap. Parcels are large -- of order a tenth of the
visible ground across.

`03-sector-blue/Babylon_5_2-22_33a.jpg` -- the opposite view, the built-up half.
Denser, greyer, browner. A broad dark road with a **dashed white centre line**
runs longitudinally; rectangular built parcels carry a fine internal grid;
a large dark blue-grey rectangle sits among them. Zoomed on the end cap
(`--box 0.45 0.35 1.0 1.0`) there is a **ring road hugging the cap rim**, with a
second concentric road inside it, and the ground runs flat right up to the rim.

`04-sector-red/Earhart's.webp` -- the far side over the restaurant: ochre and
olive-brown strips converging toward the axial vanishing point, with a broad
mauve band near the apex. The strips are **longitudinal**.

`14-characters-and-uniforms/talia-winters in gorgeous office.webp` -- the far
side through a window. Long continuous longitudinal strips, greys and
olive-greens with one broad orange-red band, carrying rows of small blue lights.
In the near field, low wide grey settlement blocks, terraced rather than towered.

`03-sector-blue/Babylon_5_2-22_29a.jpg` -- ground level: gravel paths, clipped
hedges about head height, trees, a waterfall, an elevated tram, tall orange
conical spires. Confirms the parkland band is a designed park, not rough grass.

So: **strips along the axis, parcels within them, and the whole thing curving up
and over.** Which is also what a rotating farm would be -- you plough along the
direction of travel, because across it you are climbing a 278 m hill that never
ends.

What this delivers, measured:

    lattice          448 x 640 cells -- 3.90 m x 4.04 m
    patch            32 x 32 cells -- 125 x 129 m, 14 x 20 = 280 of them
    whole drum, lod0 573,440 triangles = 0.127 tri/m2   (twice the allowance)
    worst standing viewpoint, LOD resolved
                     105,920 triangles = 0.023 tri/m2   (39% of the allowance)
    switch distances 245 m / 550 m / 1,270 m / 4,668 m, derived from measured
                     error, not chosen

Everything dimensional here that is not in `interior.LAND_USE` is extrapolation
and is logged -- see the module constants, each of which states what constrained
it.
"""
import hashlib
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402


# ---------------------------------------------------------------------------
# Deterministic value source
# ---------------------------------------------------------------------------
# FNV-1a written out, and a splitmix64 finaliser, for the same reason
# `greeble.py` does it: Python's str.__hash__ is salted per process, so using it
# would give a different drum on every run and destroy the point of generating
# geometry from a committed schema. The terrain is a pure function of
# (seed, lattice index) and of nothing else -- no accumulating state, no
# iteration order, no `random` module anywhere.
# A digest of the heightfield's committed shape. Pins every terrain constant at
# once; see the assertion in `_selftest` for why one golden value beats twenty
# hand-written checks that each restate their own constant.
GROUND_DIGEST = "4def7c14e1b88c02"

_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3
_M64 = 0xFFFFFFFFFFFFFFFF


def _fnv1a(*parts):
    h = _FNV_OFFSET
    for part in parts:
        blob = part.encode("utf-8") if isinstance(part, str) else str(part).encode()
        for byte in blob + b"\x1f":       # separator: ("a", "bc") != ("ab", "c")
            h = ((h ^ byte) * _FNV_PRIME) & _M64
    return h


def _unit(*key):
    """Uniform in [0, 1) from a key. 53-bit mantissa, splitmix64 finalised."""
    z = (_fnv1a(*key) + 0x9E3779B97F4A7C15) & _M64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M64
    z ^= z >> 31
    return (z >> 11) / float(1 << 53)


def _smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def _value_noise(u, w, na, nz, seed):
    """Value noise on a lattice that is PERIODIC around the circumference.

    The angular index is taken modulo `na`, so noise at u = 1 is bit-identical
    to noise at u = 0. Without that the terrain has a seam at 0 degrees -- a
    metre-scale cliff running the full 2,586 m length of the drum, which is
    invisible in any render that does not happen to point at it and is a wall
    the player walks into. It is asserted rather than trusted.
    """
    fa = (u % 1.0) * na
    ia = int(math.floor(fa))
    ta = _smoothstep(fa - ia)
    fz = w * nz
    iz = int(math.floor(fz))
    tz = _smoothstep(fz - iz)
    a0, a1 = ia % na, (ia + 1) % na
    v00 = _unit(seed, a0, iz)
    v10 = _unit(seed, a1, iz)
    v01 = _unit(seed, a0, iz + 1)
    v11 = _unit(seed, a1, iz + 1)
    return ((v00 * (1 - ta) + v10 * ta) * (1 - tz)
            + (v01 * (1 - ta) + v11 * ta) * tz) * 2.0 - 1.0


# ---------------------------------------------------------------------------
# Terrain spectrum
# ---------------------------------------------------------------------------
# Amplitude halves as wavelength halves. That is not a texture-artist's habit
# here, it is what makes distance LOD affordable: the error a decimation of
# stride s introduces is bounded by the amplitude of the octaves it drops, so a
# spectrum with amplitude proportional to wavelength gives switch distances that
# grow linearly with stride instead of exploding. A flat spectrum -- equal
# amplitude at every scale, which is what "add some noise" produces -- would put
# metres of error into the coarsest level and force lod0 across the whole drum.
NOISE_OCTAVES = 6
NOISE_BASE_A = 4          # 4 cells around 1,748.6 m -> 437 m fundamental
NOISE_BASE_Z = 6          # 6 cells along 2,586 m   -> 431 m fundamental
NOISE_AMP_M = 6.0         # amplitude of the fundamental
NOISE_GAIN = 0.5          # amplitude halves per octave

# Octave 6 would have a 6.8 m wavelength, below lod0's 7.8 m Nyquist. Including
# it would put detail into the field that the finest mesh cannot represent and
# that would therefore alias differently at every level. It is deliberately
# absent: anything finer than the mesh belongs in the material, not the field.


def _fbm(u, w, seed, octaves=NOISE_OCTAVES, amp=NOISE_AMP_M, gain=NOISE_GAIN):
    total, a = 0.0, amp
    for o in range(octaves):
        total += a * _value_noise(u, w, NOISE_BASE_A << o, NOISE_BASE_Z << o,
                                  f"{seed}/o{o}")
        a *= gain
    return total


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------
# 448 x 640 cells over the drum: 3.90 m circumferentially, 4.04 m along the
# axis. Fine enough that a person walking sees a surface rather than facets;
# both counts are 32 x an odd factor, so every stride in STRIDES divides a patch
# exactly and a coarse vertex is always exactly a fine vertex.
CELLS_A = 448
CELLS_Z = 640

# A patch is the LOD and streaming unit. 32 x 32 cells is 125 x 129 m, which
# lands within 6% of the 118 m streaming cell `interior.streaming_cell_deg()`
# derives for the drum's sub-floor ring from sight lines. Two unrelated
# arguments -- corridor curvature occlusion below the floor, LOD granularity
# above it -- giving the same cell size is worth keeping: one streaming unit
# serves both.
PATCH_A = 32
PATCH_Z = 32
PATCHES_A = CELLS_A // PATCH_A            # 14 around
PATCHES_Z = CELLS_Z // PATCH_Z            # 20 along

# Decimation strides. Level k samples every 2^k-th lattice point, so every
# vertex of every level is a vertex of lod0 -- a switch drops detail rather than
# rearranging the ground under the player's feet. Same property `greeble.py`
# needed and for the same reason.
STRIDES = (1, 2, 4, 8, 16)

# Switch criterion, matching station/lod.py exactly so the two chains are
# comparable. A level may be used once its geometric error subtends less than
# PIXEL_BUDGET pixels.
FOV_DEG = 50.0
SCREEN_H = 1440
PIXEL_BUDGET = 1.5


def _switch_distance(error_m):
    """Distance beyond which `error_m` of geometric error is under budget."""
    if error_m <= 0:
        return 0.0
    return error_m * SCREEN_H / (2.0 * math.tan(math.radians(FOV_DEG) / 2.0)
                                 * PIXEL_BUDGET)


# ---------------------------------------------------------------------------
# Land use
# ---------------------------------------------------------------------------
# The band table is `interior.LAND_USE` and is NOT restated here. Restating it
# is how the interior and the ground would end up disagreeing about where the
# lake is, which is exactly the failure CLAUDE.md rule 4 exists to prevent. Only
# the within-band character is added.

# Bands meet across a transition rather than at a cliff. 60 m is chosen against
# the coarsest cell (16 x 3.90 = 62.4 m): a step narrower than one coarse cell
# is a step the coarsest LOD cannot represent, so it would alias into a
# different shape at every level. Blending over one coarse cell makes band
# boundaries LOD-invariant. It is also what a field edge looks like -- 34b shows
# land use changing across a road or a hedge line, not across a wall.
BAND_BLEND_M = 60.0

# The ground runs flat to the end cap rim. 33a's cap zoom shows the ring road
# hard against the rim with the fields starting outside it; `drum_end_cap()`
# puts the cap rim circle at exactly the 278.3 m floor radius, so fading all
# relief to zero at z0 and z1 is simultaneously what the frame shows and the
# only way the ground and the cap can be watertight.
END_FADE_M = 70.0
RIM_ROAD_INSET_M = 28.0
RIM_ROAD_W_M = 16.0

# 33a's longitudinal road is broad -- a dashed centre line, and roughly a third
# the width of the small parcels beside it. 20 m is a dual two-lane carriageway
# with verges. Trunk roads run along band boundaries, which is where the base
# elevation is already transitioning, so the road sits in the fold rather than
# cutting across a field.
TRUNK_ROAD_W_M = 20.0

# Street width between settlement blocks. SEPARATE from `_step_ramp_m()`, and
# that separation is the point: the ramp is a constraint the LOD imposes on how
# sharply the surface may step, and it was being used as the street's width as
# well. That made avenues 31.2 m wide on 62.4 m blocks -- point-sampled over the
# lod0 lattice, avenue came out 16.17% of the whole drum against settlement's
# 4.67%, so the settlement band was 62% street. The same conflation made trunk
# roads tag 51.2 m wide against the 20 m above.
#
# A carriageway now has a FLAT part at its real width and a VERGE ramped over
# one stride-8 cell either side. The geometry still ramps over 31.2 m, because
# it must; only the kind tag stops pretending the ramp is roadway. -- INV-021
AVENUE_W_M = 10.0
# The made shoulder either side of a carriageway or a street: kerb, gutter,
# the strip a verge material covers. Its own number, and deliberately NOT the
# LOD ramp -- the first attempt at this fix set the verge tag to one full ramp
# (31.2 m) and, since a settlement block is only 62.4 m across, tagged EVERY
# settlement cell as either avenue or verge. Plain settlement disappeared
# entirely. Both widths have to be real widths.
VERGE_W_M = 4.0

# ---------------------------------------------------------------------------
# The step rule, which the first version of this module got wrong
# ---------------------------------------------------------------------------
# First attempt put sharp steps in the field: 3.5 m terrace risers over 6 m, and
# 0.45 m hedge banks over 10 m. Measured, that gave a **3.28 m** worst-case lod1
# error and a switch distance of 3,379 m -- further than the drum is long. Every
# patch came out at lod0 and the visible set was the entire 573,440-triangle
# field, twice the whole drum allowance. The LOD chain existed and did nothing.
#
# The cause is arithmetic, not tuning. Linear interpolation across a step of
# height H is wrong by H/2 wherever the coarse lattice straddles it, and at the
# project's 1.5-pixel budget H/2 metres of error needs ~514*H metres of
# distance. Any step over about 2.7 m therefore forces the finest level across
# the whole drum, whatever else is done.
#
# So: **every step in the field is a ramp at least one stride-8 cell wide.**
# A feature that spans a coarse cell is reproduced by linear interpolation to
# within about a tenth of its amplitude at every level down to lod3, which puts
# the error back where it belongs -- with the small octaves. The visible
# consequence is that the ground has no cliffs in it, which is correct: the
# blocky masses in the Talia Winters frame and the built parcels in 33a are
# BUILDINGS standing on the ground, not folds in it, and buildings are objects
# for a later session. The heightfield carries the podium they stand on.
def _step_ramp_m():
    """One stride-8 cell, circumferentially. The narrowest a step may be."""
    return 8.0 * (2.0 * math.pi * FLOOR_R) / CELLS_A          # 31.2 m


# Arable parcels. Counted across the visible ground in 34b and 33a: the
# agricultural half reads as roughly ten parcels across the visible arc, the
# built-up half as twenty or more. Against the drum's 1,748.6 m circumference
# that is 100-200 m for farmland and 30-60 m for the built parcels. Parcels are
# elongated ALONG the axis, which is both what Earhart's and the Talia Winters
# frame show -- long continuous longitudinal strips -- and what spin gravity
# implies, since a furrow across the drum climbs a hill that never ends.
PARCELS_A = 20            # 87.4 m circumferentially
PARCELS_Z = 8             # 323.3 m along the axis -- 3.7:1, elongated on z
PARCEL_RELIEF_M = 0.55    # half the level difference between two neighbours

# Distinct crops per parcel. 34b carries at least four readable tones on the
# ground -- a strong row-textured green, a pale straw, an olive and a dark
# green -- and the patchwork is what makes it read as farmland rather than as a
# lawn. Four is the count the frame supports; it is a tag, not geometry.
CROPS = 4

# The parcel grid is warped before it is sampled, so boundaries come out as
# irregular quadrilaterals rather than a checkerboard. 34b's parcels are
# four- and five-sided with slightly curved edges; an unwarped grid reads as
# graph paper at any distance where the whole band is in frame.
PARCEL_WARP_M = 34.0

# Hedge banks. 29a shows clipped hedges at roughly head height at ground level,
# and 34b shows parcel boundaries as lines with their own tone rather than as
# bare colour changes. Only the BANK is geometry, and it is deliberately shallow
# and wide: 0.22 m over 15.6 m, which is four lod0 cells. The hedge itself --
# 2 m tall, 1 m wide -- is finer than lod0's 3.9 m cell and belongs in the
# material, not the field. A 1 m-wide ridge in a 3.9 m lattice does not render
# as a hedge at any level; it renders as a different random bump at each one.
HEDGE_W_M = 11.7
HEDGE_H_M = 0.22

# Settlement. The band datum is LAND_USE's 7 m: the built-up half stands on a
# raised podium, which is what the Talia Winters frame shows -- the town sits
# above the fields, not in them -- and is also where the services under a town
# would go. On top of that the podium carries one optional 2 m step per block
# and an avenue grid cut into it. Blocks are one coarse cell, 62.4 x 64.6 m,
# so the grid is rectilinear at every level rather than dissolving into the
# arable noise at distance.
BLOCK_CELLS = 16
PODIUM_STEP_M = 2.0
AVENUE_CUT_M = 1.5

# Water. `interior.LAND_USE` puts the water band 2.5 m below the datum; that is
# its surface. The bed is cut deeper so the surface is genuinely flat where it
# is water and the shore rises out of it, rather than the whole band being a
# uniform trough that reads as a ditch.
WATER_LEVEL_M = -2.5
WATER_DEPTH_M = 5.0

# Parkland is the softest band: long wavelengths only, no parcels, no hedges.
# 29a is a designed park -- lawn, beds, paths, tree masses -- and its ground
# plane is gentle. Tree masses are broad low mounds in the field and canopies in
# the material; individual trees are objects for a later session.
PARK_SMOOTH = 3           # octaves kept; the rest are dropped

SEED = "b5-drum-ground-v1"


def _bands():
    """LAND_USE as cumulative [lo, hi) fractions. Read from interior, never
    copied -- one table, one place."""
    out, acc = [], 0.0
    for frac, name, relief in it.LAND_USE:
        out.append((acc, acc + frac, name, relief))
        acc += frac
    return out


def _band_weights(u):
    """Which land uses apply at circumferential fraction u, and how strongly.

    Returns [(name, relief, weight)] with weights summing to 1. Away from a
    boundary exactly one band applies; within BAND_BLEND_M of one, two do.
    """
    bands = _bands()
    circ = 2.0 * math.pi * FLOOR_R
    blend = BAND_BLEND_M / circ           # in fractions of the circumference
    u = u % 1.0
    n = len(bands)
    for i, (lo, hi, name, relief) in enumerate(bands):
        if not (lo <= u < hi):
            continue
        # Distance to the nearer of this band's two boundaries.
        d_lo, d_hi = u - lo, hi - u
        if d_lo < blend / 2.0:
            j = (i - 1) % n
            t = 0.5 + d_lo / blend        # 0.5 at the boundary, 1 at full band
            return [(name, relief, _smoothstep(t)),
                    (bands[j][2], bands[j][3], 1.0 - _smoothstep(t))]
        if d_hi < blend / 2.0:
            j = (i + 1) % n
            t = 0.5 + d_hi / blend
            return [(name, relief, _smoothstep(t)),
                    (bands[j][2], bands[j][3], 1.0 - _smoothstep(t))]
        return [(name, relief, 1.0)]
    lo, hi, name, relief = bands[-1]
    return [(name, relief, 1.0)]


# Filled by `configure()`; module-level because the terrain function is called
# once per vertex and re-deriving the sector geometry there would dominate the
# cost. Defaults are the drum's, set at import.
FLOOR_R = 278.3
Z0 = 3839.0
Z1 = 6425.0


def configure(schema=None, profile=None, sector=None):
    """Bind the module to a sector's actual geometry.

    Everything below works in (u, w) -- fraction around, fraction along -- and
    needs the floor radius and z extent to convert to metres. Those come from
    the schema through `interior`, never from a constant here.
    """
    global FLOOR_R, Z0, Z1
    if schema is None:
        schema, profile = it.load()
    if sector is None:
        sector = it.drum_sector(schema, profile)
    FLOOR_R = it.sector_radius(schema, profile, sector)
    # The ground runs to the CAP SURFACE, not to the sector extent.
    #
    # It used to stop at the sector's z0/z1, which left an annular slot 0.6 m
    # wide right round the drum at both ends -- the cap's outermost course
    # stands ENDCAP_STEP_M proud, so its plate at the floor radius sits that far
    # beyond where the ground stopped. The old assertion could not see this: it
    # checked only that the ground's RELIEF faded to zero at z0/z1 and never
    # looked at drum_end_cap() at all, so a gap between two surfaces was scored
    # by measuring only one of them.
    Z0 = cap_plane_z(schema, profile, sector, "aft")
    Z1 = cap_plane_z(schema, profile, sector, "fore")
    return schema, profile, sector


def cap_plane_z(schema, profile, sector, end):
    """Axial position of the end cap's surface at the drum floor radius.

    Derived from `interior.drum_end_cap`'s own constants rather than restated,
    so a change to the cap's course depth moves the ground with it instead of
    silently reopening the slot. The cap's dish is zero at u = 1.0 by
    construction -- ENDCAP_DISH * r * (1 - u^2) -- so at the floor radius the
    only offset is the outermost course's step.
    """
    ex = schema["sectors"]["extents_m"][sector]
    z_base = float(ex["z1"] if end == "fore" else ex["z0"])
    out = 1.0 if end == "fore" else -1.0
    return z_base + out * it.ENDCAP_STEP_M


# ---------------------------------------------------------------------------
# The terrain function
# ---------------------------------------------------------------------------

def _parcel(u, w, cells_a, cells_z, warp_m, seed, ramp_m=None):
    """A warped grid of plateaux: one level per cell, ramped across the edges.

    Returns (plateau, edge_distance_m, cell). `plateau` is in [-1, 1], flat
    across the body of a cell and sloping across the last `ramp_m` at its
    boundary. `edge_distance_m` is the distance to the nearest cell edge, which
    is what a hedge bank or an avenue is raised or cut from -- both without any
    geometry of their own.

    The ramp is why this is not simply `floor()`. A hard cell step is a cliff,
    and a cliff is the thing that made the first version's LOD chain useless
    (see the step rule above). Ramping over a stride-8 cell keeps the parcels
    reading as separate levels while staying representable at every level.

    The warp is periodic in u because `_value_noise` is, and the cell count
    divides the circumference exactly, so cell indices wrap: parcel 14 and
    parcel 0 are neighbours and share an edge rather than meeting at a seam.
    """
    circ = 2.0 * math.pi * FLOOR_R
    span = Z1 - Z0
    ramp_m = _step_ramp_m() if ramp_m is None else ramp_m
    wa = warp_m * _value_noise(u, w, 5, 7, seed + "/warpA") if warp_m else 0.0
    wz = warp_m * _value_noise(u, w, 7, 5, seed + "/warpZ") if warp_m else 0.0
    size_a, size_z = circ / cells_a, span / cells_z
    sa = (u % 1.0) * cells_a + wa / size_a
    sz = w * cells_z + wz / size_z

    ia, iz = int(math.floor(sa)), int(math.floor(sz))
    fa, fz = sa - ia, sz - iz
    d_edge = min(min(fa, 1.0 - fa) * size_a, min(fz, 1.0 - fz) * size_z)

    # Plateau: bilinear between the four CELL CENTRES that straddle the point,
    # with the interpolation parameter sharpened so it saturates everywhere
    # except within ramp_m of the boundary. Sharpening a bilinear is what turns
    # a smooth blend into flat fields with banks between them.
    def sharp(f, size):
        return _smoothstep(min(max((f - 0.5) * size / ramp_m + 0.5, 0.0), 1.0))

    ga, gz = sa - 0.5, sz - 0.5
    ca, cz = int(math.floor(ga)), int(math.floor(gz))
    ea, ez = sharp(ga - ca, size_a), sharp(gz - cz, size_z)

    def level(i, j):
        # Quantised to three levels so a parcel is a parcel, not a dune.
        return round(_unit(seed, "level", i % cells_a, j) * 2.0 - 1.0)

    plateau = ((level(ca, cz) * (1 - ea) + level(ca + 1, cz) * ea) * (1 - ez)
               + (level(ca, cz + 1) * (1 - ea)
                  + level(ca + 1, cz + 1) * ea) * ez)
    return plateau, d_edge, (ia % cells_a, iz)


def _road_mask(u, w):
    """(strength, kind) for roads at (u, w). Strength 1 is full carriageway.

    Three road systems, all sourced:
      - the ring roads at each cap rim (33a, cap zoom);
      - longitudinal trunk roads on the land-use boundaries (33a's broad road
        with the dashed centre line runs the length of the drum);
      - nothing else. Field tracks and streets are handled by their own bands.
    """
    circ = 2.0 * math.pi * FLOOR_R
    z = Z0 + w * (Z1 - Z0)
    ramp = _step_ramp_m()
    best, kind = 0.0, None

    def profile(d, half_width):
        """Flat carriageway, then a verge ramped over one stride-8 cell.

        Ramping matters as much as the width does. A road that goes from full
        cut to untouched field over its own half-width is a step of whatever
        relief it removed, and the terrace or hedge it cuts through is exactly
        the relief that is largest.

        Returns (strength, zone) where zone is "road", "verge" or None.
        Strength is a GEOMETRY weight and stays ramped over the full stride-8
        cell, because the LOD requires that. The zone is what the KIND TAG
        follows, and it stops at the made width -- tagging the whole ramp as
        roadway is what made trunk roads read 51.2 m wide against a stated 20.
        """
        if d <= half_width:
            return 1.0, "road"
        if d >= half_width + ramp:
            return 0.0, None
        st = 1.0 - _smoothstep((d - half_width) / ramp)
        return st, ("verge" if d <= half_width + VERGE_W_M else None)

    for z_ring in (Z0 + RIM_ROAD_INSET_M, Z1 - RIM_ROAD_INSET_M):
        s, zone = profile(abs(z - z_ring), RIM_ROAD_W_M / 2.0)
        if s > best:
            best, kind = s, ("ring" if zone == "road" else zone)

    bands = _bands()
    for i, (lo, _hi, name, _relief) in enumerate(bands):
        # No trunk road on a boundary that touches water: that is a road
        # through a lake. It is also what produced the worst LOD error in the
        # first measured pass -- the road was flattening a 5 m bowl.
        if name == "water" or bands[i - 1][2] == "water":
            continue
        d = abs(((u - lo + 0.5) % 1.0) - 0.5) * circ
        s, zone = profile(d, TRUNK_ROAD_W_M / 2.0)
        if s > best:
            best, kind = s, ("trunk" if zone == "road" else zone)
    return best, kind


def _end_fade(w):
    """1 in the body of the drum, 0 at each end cap.

    This is the watertightness condition with `drum_end_cap()`: the cap's rim
    circle is at exactly the floor radius, so the ground has to arrive there at
    exactly the floor radius too. Any relief left at z0 or z1 is a gap between
    the ground and the bulkhead -- the same class of hole as a cell seam crack,
    and at 1 g it is a hole into the sub-floor decks.
    """
    span = Z1 - Z0
    z = w * span
    d = min(z, span - z)
    if d >= END_FADE_M:
        return 1.0
    return _smoothstep(max(0.0, d) / END_FADE_M)


def sample(u, w):
    """Terrain at circumferential fraction u and longitudinal fraction w.

    Returns (height_m, kind). Height is metres ABOVE the floor datum, where
    "above" means toward the spin axis: the surface radius is FLOOR_R - height.
    That sign convention is `interior.drum_interior()`'s and is kept so the two
    modules cannot disagree about which way a terrace goes.
    """
    weights = _band_weights(u)
    fade = _end_fade(w)

    h = 0.0
    kind = weights[0][0]
    kind_w = -1.0
    for name, relief, wt in weights:
        hb = relief + _band_relief(name, u, w)
        h += wt * hb
        if wt > kind_w:
            kind_w, kind = wt, name

    # Boundaries get their own kind rather than being folded into the field
    # they divide. A hedge line and an avenue are the two features the eye picks
    # a farmed or built landscape out by -- 34b's parcels are legible because
    # their edges have a tone of their own -- and at 3.9 m cells they are one or
    # two quads wide, so the tag is doing most of the work. It is also the
    # channel a material needs: this is where hedge, verge and kerb go.
    if kind == "arable":
        _p, d_edge, cell = _parcel(u, w, PARCELS_A, PARCELS_Z, PARCEL_WARP_M,
                                   SEED + "/parcel")
        if d_edge < HEDGE_W_M / 2.0:
            kind = "hedge"
        else:
            # One crop per parcel. 34b's patchwork is made of tone, not of
            # relief: a strong row-textured green beside a pale straw parcel
            # beside an olive one. Without this the arable band renders as a
            # single olive field 455 m wide and 2.6 km long, which no amount of
            # displacement rescues.
            kind = f"arable{int(_unit(SEED, 'crop', cell[0], cell[1]) * CROPS)}"
    elif kind == "settlement":
        _p, d_edge, _c = _parcel(u, w, CELLS_A // BLOCK_CELLS,
                                 CELLS_Z // BLOCK_CELLS, 0.0, SEED + "/block")
        if d_edge < AVENUE_W_M / 2.0:
            kind = "avenue"
        elif d_edge < AVENUE_W_M / 2.0 + VERGE_W_M:
            kind = "verge"

    # Water is clamped AFTER blending, so the shoreline follows the blended
    # ground rather than the band boundary. A lake whose edge is a straight line
    # at a fixed angle is the tell that the water was painted on a band instead
    # of filled into a hollow.
    if kind == "water" and h < WATER_LEVEL_M:
        h = WATER_LEVEL_M
        kind = "water_surface"
    elif kind == "water":
        kind = "shore"

    strength, road_kind = _road_mask(u, w)
    if strength > 0.0:
        # A road takes the ground it runs over and removes only what a road
        # removes -- the hedge bank it cuts through and the avenue trench it
        # replaces. It does NOT flatten the landform: an earlier version
        # substituted the bare band datum, which meant a road along the
        # arable/settlement boundary erased 2 m of podium over its verge and
        # was the largest single LOD error in the field. A road follows the
        # country; it does not delete it.
        base = sum(wt * (relief + _band_relief(name, u, w, roadbed=True))
                   for name, relief, wt in weights)
        h = h * (1.0 - strength) + base * strength
        # Only the made surface renames the ground. Beyond it the road is still
        # shaping the height -- that is what `strength` is for -- but the
        # material stays whatever band the road is cut into.
        if road_kind == "trunk":
            kind = "road"
        elif road_kind == "ring":
            kind = "ring_road"
        elif road_kind == "verge":
            kind = "verge"

    h *= fade
    if fade < 1.0 and kind not in ("road", "ring_road"):
        kind = "rim" if fade < 0.35 else kind
    return h, kind


def _band_relief(name, u, w, roadbed=False):
    """Within-band relief, in metres, relative to the band's own datum.

    `roadbed` drops the features a carriageway removes -- the hedge bank and
    the avenue trench -- and keeps the landform. See the note in `sample()`.
    """
    if name == "arable":
        # Gently undulating, subdivided by field boundaries. The undulation is
        # the full spectrum; the parcels are one level per field with a bank on
        # the boundary. 34b's fields sit at visibly different tones and levels.
        h = _fbm(u, w, SEED + "/arable") * 0.5
        plateau, d_edge, _cell = _parcel(u, w, PARCELS_A, PARCELS_Z,
                                         PARCEL_WARP_M, SEED + "/parcel")
        h += plateau * PARCEL_RELIEF_M
        if not roadbed and d_edge < HEDGE_W_M / 2.0:
            h += HEDGE_H_M * (1.0 - _smoothstep(d_edge / (HEDGE_W_M / 2.0)))
        return h

    if name == "settlement":
        # A raised podium cut by an avenue grid, on the coarse lattice. The
        # blocky masses in the Talia Winters frame are buildings standing on
        # this, not folds in it -- see the step rule. What the ground itself
        # carries is the podium level and the streets between blocks, which is
        # what makes the band read as rectilinear at distance instead of
        # dissolving into the arable noise.
        avenue_w = AVENUE_W_M
        plateau, d_edge, _cell = _parcel(u, w, CELLS_A // BLOCK_CELLS,
                                         CELLS_Z // BLOCK_CELLS, 0.0,
                                         SEED + "/block")
        h = PODIUM_STEP_M * (plateau + 1.0) / 2.0
        # Flat trench at the street's own width, then ramped out over one
        # stride-8 cell -- the same shape as a road, and for the same reason.
        if not roadbed:
            half, ramp = avenue_w / 2.0, _step_ramp_m()
            if d_edge <= half:
                h -= AVENUE_CUT_M
            elif d_edge < half + ramp:
                h -= AVENUE_CUT_M * (1.0 - _smoothstep((d_edge - half) / ramp))
        return h

    if name == "water":
        # A channel: deepest on the band's centreline, rising to the shores. The
        # cross-section is derived from the band's own width so it stays a
        # channel if LAND_USE is retuned.
        # Find the water band by NAME and clamp into it, rather than by
        # containment. `_band_weights` calls this for points on the arable side
        # of the boundary too, and a containment test returns 0 there -- which
        # put a 1.3 m cliff exactly on the shoreline, invisible in a render and
        # the largest LOD error in the field. A blend function must be defined
        # wherever it is blended.
        spans = [(a, b) for a, b, nm, _r in _bands() if nm == "water"]
        if not spans:
            return 0.0
        uu = u % 1.0
        lo, hi = min(spans, key=lambda s: abs(((uu - (s[0] + s[1]) / 2.0 + 0.5)
                                               % 1.0) - 0.5))
        t = min(max((uu - lo) / (hi - lo), 0.0), 1.0)
        # A plain sine, not a flattened one. The first version used sin^0.6 to
        # get steeper banks and a wider flat pool; sin^0.6 has infinite slope at
        # the shoreline, which put a 1.5 m drop inside a single 7.8 m cell and
        # was on its own responsible for a 1.7 m lod1 error and a switch
        # distance longer than the drum. The pool is wide enough without it:
        # the surface clamp floods everywhere sin(pi t) > 0.5, which is two
        # thirds of the band.
        bowl = -WATER_DEPTH_M * math.sin(math.pi * min(max(t, 0.0), 1.0))
        return bowl - WATER_LEVEL_M + _fbm(u, w, SEED + "/water",
                                           octaves=3) * 0.25

    if name == "parkland":
        return _fbm(u, w, SEED + "/park", octaves=PARK_SMOOTH,
                    amp=NOISE_AMP_M * 0.55) * 0.6

    return 0.0


def terrain_sample(schema, profile, sector, angle_deg, z):
    """Public sample in station coordinates. Returns a dict, not a bare float --
    the land-use kind is what a caller placing anything on the ground needs."""
    configure(schema, profile, sector)
    u = (angle_deg / 360.0) % 1.0
    w = min(max((z - Z0) / (Z1 - Z0), 0.0), 1.0)
    h, kind = sample(u, w)
    return {"angle_deg": angle_deg, "z_m": z,
            "height_m": h, "radius_m": FLOOR_R - h,
            "gravity_g": it.gravity_at(schema, FLOOR_R - h), "kind": kind}


def stand_on_ground(schema, profile, sector, angle_deg, z, eye_h=1.7):
    """Eye position and up vector for someone standing on the HEIGHTFIELD.

    `interior.stand_point()` derives the eye from LAND_USE's flat band relief,
    which was right when the ground was flat bands. With a heightfield under
    foot that is wrong by whatever the terrain does inside the band -- up to
    7 m in a settlement, which buries the camera in a terrace exactly the way
    the first drum render was buried in one. Same lesson, one level down.
    """
    configure(schema, profile, sector)
    u = (angle_deg / 360.0) % 1.0
    w = min(max((z - Z0) / (Z1 - Z0), 0.0), 1.0)
    h, _kind = sample(u, w)
    r_eye = FLOOR_R - h - eye_h
    a = math.radians(angle_deg)
    return ((r_eye * math.cos(a), r_eye * math.sin(a), z),
            (-math.cos(a), -math.sin(a), 0.0))


# ---------------------------------------------------------------------------
# Mesh
# ---------------------------------------------------------------------------

_KIND_GROUP = {
    "arable": "ground_arable",
    **{f"arable{i}": f"ground_arable_{i}" for i in range(CROPS)},
    "hedge": "ground_hedge",
    "avenue": "ground_avenue",
    # The strip either side of a carriageway or a street. It exists as its own
    # kind so that the LOD's 31.2 m geometry ramp stops being tagged as roadway:
    # it is the ground the road is cut INTO, so it takes the neighbouring band's
    # material in the engine, and here it gets a group of its own so the split
    # is visible and measurable.
    "verge": "ground_verge",
    "settlement": "ground_settlement",
    "water": "ground_shore",
    "shore": "ground_shore",
    "water_surface": "ground_water",
    "parkland": "ground_parkland",
    "road": "ground_road",
    "ring_road": "ground_road",
    "rim": "ground_rim",
}


def _vertex(ia, iz):
    """World position of lattice point (ia, iz). The lattice is the single
    source of vertex positions at every LOD, which is what makes a coarse vertex
    exactly a fine vertex rather than approximately one."""
    u = (ia % CELLS_A) / CELLS_A
    w = iz / CELLS_Z
    h, kind = sample(u, w)
    r = FLOOR_R - h
    a = 2.0 * math.pi * u
    return (r * math.cos(a), r * math.sin(a), Z0 + w * (Z1 - Z0)), kind


def _lerp3(p, q, t):
    return (p[0] + (q[0] - p[0]) * t,
            p[1] + (q[1] - p[1]) * t,
            p[2] + (q[2] - p[2]) * t)


def ground_patch(pa, pz, stride=1, neighbours=None):
    """One ground patch at one LOD. Returns (verts, tris, groups, meta).

    `neighbours` is {"a-": stride, "a+": ..., "z-": ..., "z+": ...} giving the
    stride each adjacent patch is being built at, or None where there is no
    neighbour. Where a neighbour is COARSER, this patch's border vertices are
    moved onto the coarse neighbour's edge segments. That is the whole crack
    fix: a T-junction between a 32-cell edge and a 4-cell edge leaves a
    sawtooth of holes along the seam, and a heightfield with holes in it is a
    heightfield you fall through. Clamping costs no triangles, unlike a skirt,
    and unlike a skirt it is exact rather than hidden.
    """
    neighbours = neighbours or {}
    ia0, iz0 = pa * PATCH_A, pz * PATCH_Z
    na = PATCH_A // stride
    nz = PATCH_Z // stride

    grid = {}
    kinds = {}
    for ka in range(na + 1):
        for kz in range(nz + 1):
            ia, iz = ia0 + ka * stride, iz0 + kz * stride
            grid[(ka, kz)], kinds[(ka, kz)] = _vertex(ia, iz)

    def clamp_edge(fixed_axis, at, nb_stride):
        """Snap one border row onto a coarser neighbour's lattice."""
        if not nb_stride or nb_stride <= stride:
            return
        m = nb_stride // stride                    # fine steps per coarse step
        span = na if fixed_axis == "z" else nz
        for k in range(span + 1):
            k0 = (k // m) * m
            k1 = min(k0 + m, span)
            if k0 == k1 or k == k0:
                continue
            t = (k - k0) / float(k1 - k0)
            if fixed_axis == "z":
                grid[(k, at)] = _lerp3(grid[(k0, at)], grid[(k1, at)], t)
            else:
                grid[(at, k)] = _lerp3(grid[(at, k0)], grid[(at, k1)], t)

    clamp_edge("z", 0, neighbours.get("z-"))
    clamp_edge("z", nz, neighbours.get("z+"))
    clamp_edge("a", 0, neighbours.get("a-"))
    clamp_edge("a", na, neighbours.get("a+"))

    verts, tris, groups = [], [], []
    index = {}
    for key, p in grid.items():
        index[key] = len(verts)
        verts.append(p)

    for ka in range(na):
        for kz in range(nz):
            i00 = index[(ka, kz)]
            i10 = index[(ka + 1, kz)]
            i11 = index[(ka + 1, kz + 1)]
            i01 = index[(ka, kz + 1)]
            # Wound so the normal points TOWARD the spin axis. Ascending angle
            # crossed with ascending z gives the outward radial, which is
            # backface-culled for a viewer standing inside the drum and renders
            # as nothing at all -- not as an error. Same trap that took 95% of
            # the drum shell in session 2u.
            tris.append((i00, i01, i11))
            tris.append((i00, i11, i10))
            g = _KIND_GROUP.get(kinds[(ka, kz)], "ground_arable")
            groups.extend([g, g])

    return verts, tris, groups, {
        "patch": (pa, pz), "stride": stride,
        "cells": (na, nz), "triangles": len(tris),
        "vertices": len(verts),
    }


def patch_centre(pa, pz):
    """Centre of a patch on the FLOOR datum, ignoring relief.

    Not used for LOD -- `patch_nearest_distance` is. It is here because
    anything placing content against a patch (a streaming manifest entry, a
    building, a tram stop) needs the patch's position on the datum rather than
    on the terrain: a position that moves when a hill grows on it is a position
    that cannot be a key.
    """
    u = (pa * PATCH_A + PATCH_A / 2.0) / CELLS_A
    w = (pz * PATCH_Z + PATCH_Z / 2.0) / CELLS_Z
    a = 2.0 * math.pi * u
    return (FLOOR_R * math.cos(a), FLOOR_R * math.sin(a), Z0 + w * (Z1 - Z0))


def patch_nearest_distance(pa, pz, eye):
    """Distance from `eye` to the NEAREST point of a patch, on the floor datum.

    Centre distance is the wrong measure: a patch is 125 x 129 m, so the one
    the player is standing in has its centre up to 90 m away and would be
    classified as if the ground under their feet were 90 m off. Clamping the
    eye's own (angle, z) into the patch's extents gives the near point directly
    and costs one clamp -- there is no reason to approximate it.
    """
    a0 = 2.0 * math.pi * (pa * PATCH_A) / CELLS_A
    a1 = 2.0 * math.pi * ((pa + 1) * PATCH_A) / CELLS_A
    z0 = Z0 + (pz * PATCH_Z) / CELLS_Z * (Z1 - Z0)
    z1 = Z0 + ((pz + 1) * PATCH_Z) / CELLS_Z * (Z1 - Z0)

    ae = math.atan2(eye[1], eye[0]) % (2.0 * math.pi)
    mid = (a0 + a1) / 2.0
    # Signed angular offset from the patch centre, wrapped to (-pi, pi].
    d = (ae - mid + math.pi) % (2.0 * math.pi) - math.pi
    half = (a1 - a0) / 2.0
    an = mid + max(-half, min(half, d))
    zn = max(z0, min(z1, eye[2]))
    p = (FLOOR_R * math.cos(an), FLOOR_R * math.sin(an), zn)
    return math.dist(p, eye)


# ---------------------------------------------------------------------------
# LOD: measured error, then derived switch distances
# ---------------------------------------------------------------------------

def lod_error_report(sample_patches=None):
    """Max and RMS deviation of each level from lod0, in metres.

    Two error sources and the larger wins:

      * the drum's own curvature -- a chord across an angular facet falls inside
        the true circle by the SAGITTA r(1 - cos(dtheta/2)). This is the term
        the exterior LOD chain got wrong once by sizing against facet WIDTH
        instead, and it is recorded in CONTRIBUTING.md as a mistake worth not
        repeating: at r = 1211 m an 8-gon's facets are 927 m wide and the pop is
        92 m, an order of magnitude apart.
      * the heightfield's own detail, lost when octaves fall below the coarse
        Nyquist. This one is MEASURED rather than predicted, by evaluating the
        true field at every lod0 lattice point inside a sample patch and
        comparing against the bilinear interpolation of the strided lattice.

    Sampling is at full lod0 resolution inside whole patches, one per land-use
    band, so ridge peaks are sampled rather than stepped over. A subsampled
    measurement would report an error near zero for exactly the features that
    cause the pop.
    """
    if sample_patches is None:
        sample_patches = _representative_patches()

    out = []
    for stride in STRIDES:
        worst = 0.0
        sq = n = 0
        for pa, pz in sample_patches:
            ia0, iz0 = pa * PATCH_A, pz * PATCH_Z
            coarse = {}
            for ka in range(0, PATCH_A + stride, stride):
                for kz in range(0, PATCH_Z + stride, stride):
                    u = ((ia0 + ka) % CELLS_A) / CELLS_A
                    w = (iz0 + kz) / CELLS_Z
                    coarse[(ka, kz)] = sample(u, w)[0]
            for da in range(PATCH_A + 1):
                for dz in range(PATCH_Z + 1):
                    u = ((ia0 + da) % CELLS_A) / CELLS_A
                    w = (iz0 + dz) / CELLS_Z
                    true_h = sample(u, w)[0]
                    ka0 = (da // stride) * stride
                    kz0 = (dz // stride) * stride
                    ka1 = min(ka0 + stride, PATCH_A)
                    kz1 = min(kz0 + stride, PATCH_Z)
                    ta = 0.0 if ka1 == ka0 else (da - ka0) / (ka1 - ka0)
                    tz = 0.0 if kz1 == kz0 else (dz - kz0) / (kz1 - kz0)
                    approx = (coarse[(ka0, kz0)] * (1 - ta) * (1 - tz)
                              + coarse[(ka1, kz0)] * ta * (1 - tz)
                              + coarse[(ka0, kz1)] * (1 - ta) * tz
                              + coarse[(ka1, kz1)] * ta * tz)
                    e = abs(true_h - approx)
                    worst = max(worst, e)
                    sq += e * e
                    n += 1
        dtheta = 2.0 * math.pi * stride / CELLS_A
        sagitta = FLOOR_R * (1.0 - math.cos(dtheta / 2.0))
        err = max(worst, sagitta)
        out.append({
            "level": f"lod{STRIDES.index(stride)}",
            "stride": stride,
            "cell_m": round(2 * math.pi * FLOOR_R * stride / CELLS_A, 2),
            "height_error_m": round(worst, 3),
            "height_rms_m": round(math.sqrt(sq / max(n, 1)), 3),
            "curvature_sagitta_m": round(sagitta, 4),
            "error_m": round(err, 3),
            "switch_distance_m": round(_switch_distance(err), 0),
            "patch_triangles": 2 * (PATCH_A // stride) * (PATCH_Z // stride),
        })
    return out


def _representative_patches():
    """One patch per land-use band, at mid-length, plus one at an end.

    Measuring the LOD error on farmland alone would understate it badly: the
    settlement band's terrace steps are 3.5 m and the water band's shore is
    2.5 m, both far larger than an arable undulation.
    """
    picks, seen = [], set()
    pz = PATCHES_Z // 2
    for lo, hi, name, _relief in _bands():
        u = (lo + hi) / 2.0
        pa = int(u * CELLS_A) // PATCH_A
        if (pa, name) in seen:
            continue
        seen.add((pa, name))
        picks.append((pa % PATCHES_A, pz))
    picks.append((0, 0))                    # the end fade, where relief tapers
    return picks


_LOD_CACHE = {}


def lod_table():
    """Switch distances, measured once and memoised. Monotonic by construction:
    a coarser level can never switch in closer than a finer one."""
    key = (round(FLOOR_R, 3), round(Z0, 1), round(Z1, 1))
    if key not in _LOD_CACHE:
        rows = lod_error_report()
        d = 0.0
        for r in rows:
            d = max(d, r["switch_distance_m"])
            r["switch_distance_m"] = d
        _LOD_CACHE[key] = rows
    return _LOD_CACHE[key]


def level_for_distance(distance_m, table=None):
    table = table or lod_table()
    lvl = 0
    for i, row in enumerate(table):
        if distance_m >= row["switch_distance_m"]:
            lvl = i
    return lvl


# ---------------------------------------------------------------------------
# THE ERROR IS A PROPERTY OF THE PATCH, NOT OF THE DRUM -- INV-540
# ---------------------------------------------------------------------------
# `lod_error_report()` above measures the deviation of each stride from lod0
# inside `_representative_patches()` -- one patch per land-use band -- and then
# takes the WORST and applies it to all 280 patches. So the lake pays the
# settlement podium's error and the parkland pays the arable's finest noise
# octave, and the ground draws detail at a distance where its own terrain
# cannot express it. Measured over all 280 patches at stride 4, the switch
# distance the drum-wide table imposes is 554 m and the per-patch answer ranges
# 113 to 713 m -- a factor of 6.3.
#
# THE CRITERION IS UNCHANGED. It is still `_switch_distance(err)`, still 1.5 px
# of deviation, still the same screen model. Only its DOMAIN changes: measured
# on the patch that is being drawn instead of on the worst patch on the drum.
# Nothing is removed from the ground and no allowance moves.
#
# AND IT IS NOT ONLY A SAVING -- IT IS ALSO A CORRECTION. The representative
# sample is one patch per band at mid-length, and it MISSES the worst patch:
# per-patch stride 8 runs to a 1.974 m error where the representative maximum
# is 1.048 m. Those patches now switch LATER than they do today, i.e. they are
# drawn FINER. 360 of the sampled positions inside the collision tile get more
# triangles than they have now, not fewer.
#
# PINNED, NOT DERIVED AT IMPORT, for the reason `drum_dressing.DRUM_FIXED_TRIS`
# is pinned: the derivation is 305,000 `sample()` calls and costs 51 s, and no
# gate should pay that to answer a question whose answer is a property of a
# committed terrain. `--derive-patch-lod` recomputes it and fails on drift, and
# `_selftest` re-measures a deterministic subset on every run so the pin cannot
# rot silently. Millimetres, as integers, because a float table is a diff
# nobody can read.
#
# Index is (pa * PATCHES_Z + pz) * len(STRIDES) + level.
PATCH_LOD_ERR_MM = (
    # pa  0
        7,  166,  279,  481, 1750,
        7,  161,  250,  438, 1750,
        7,  166,  278,  438, 1750,
        7,  165,  188,  580, 1750,
        7,  193,  233,  438, 1750,
        7,  193,  259,  451, 1750,
        7,  158,  249,  473, 1750,
        7,  196,  229,  471, 1750,
        7,  180,  239,  438, 1750,
        7,  205,  235,  438, 1750,
        7,  186,  296,  438, 1750,
        7,  195,  254,  438, 1750,
        7,  188,  248,  452, 1750,
        7,  173,  204,  438, 1750,
        7,  198,  306,  710, 1750,
        7,  187,  207,  517, 1750,
        7,  154,  203,  492, 1750,
        7,  182,  261,  566, 1750,
        7,  158,  260,  672, 1750,
        7,  199,  338,  746, 1883,
    # pa  1
        7,  128,  221,  438, 1750,
        7,  164,  234,  438, 1750,
        7,  180,  260,  438, 1750,
        7,   97,  295,  438, 1750,
        7,  200,  246,  438, 1750,
        7,  206,  245,  439, 1750,
        7,  190,  234,  438, 1750,
        7,  182,  239,  470, 1750,
        7,  109,  196,  438, 1750,
        7,  189,  272,  438, 1750,
        7,  147,  231,  438, 1750,
        7,  202,  268,  438, 1750,
        7,  232,  308,  438, 1750,
        7,  145,  182,  438, 1750,
        7,  144,  203,  438, 1750,
        7,  159,  231,  438, 1750,
        7,  151,  215,  438, 1750,
        7,  200,  383,  438, 1750,
        7,  149,  284,  438, 1750,
        7,  172,  258,  438, 1750,
    # pa  2
        7,  174,  277,  440, 1750,
        7,  199,  286,  447, 1750,
        7,  182,  265,  438, 1750,
        7,  182,  233,  438, 1750,
        7,  181,  249,  438, 1750,
        7,  181,  205,  438, 1750,
        7,  188,  242,  438, 1750,
        7,  193,  271,  438, 1750,
        7,  166,  237,  438, 1750,
        7,  188,  276,  438, 1750,
        7,  183,  294,  471, 1750,
        7,  186,  268,  495, 1750,
        7,  163,  309,  478, 1750,
        7,  175,  282,  438, 1750,
        7,  191,  233,  474, 1750,
        7,  175,  302,  526, 1750,
        7,  162,  251,  438, 1750,
        7,  185,  229,  438, 1750,
        7,  167,  246,  438, 1750,
        7,  108,  288,  574, 1750,
    # pa  3
        7,  192,  599, 1553, 4223,
        7,  191,  587, 1267, 3730,
        7,  191,  630, 1210, 3570,
        7,  189,  568, 1185, 3293,
        7,  201,  530, 1352, 3703,
        7,  185,  526, 1429, 3521,
        7,  160,  465,  791, 2674,
        7,  182,  544, 1373, 3586,
        7,  178,  473, 1060, 3131,
        7,  160,  396,  791, 2469,
        7,  146,  413, 1051, 3256,
        7,  148,  430,  752, 2816,
        7,  167,  478, 1184, 3401,
        7,  163,  478, 1040, 3378,
        7,  182,  538, 1041, 3479,
        7,  188,  560, 1354, 3865,
        7,  182,  559, 1326, 3673,
        7,  183,  543, 1021, 3272,
        7,  187,  561, 1236, 3692,
        7,  148,  420,  992, 2595,
    # pa  4
        7,  127,  290,  974, 1750,
        7,  185,  386,  885, 2397,
        7,  151,  290,  678, 2209,
        7,  127,  433,  967, 1750,
        7,  127,  301,  615, 1750,
        7,  127,  290,  615, 1750,
        7,  127,  290,  615, 2084,
        7,  185,  386,  881, 2459,
        7,  189,  408,  928, 2334,
        7,  151,  369,  885, 2084,
        7,  151,  369,  885, 2209,
        7,  146,  290,  615, 2147,
        7,  127,  369,  885, 1750,
        7,  154,  386,  881, 2147,
        7,  127,  290,  615, 1750,
        7,  158,  369,  885, 2209,
        7,  158,  386,  881, 2397,
        7,  150,  290,  615, 2209,
        7,  189,  408,  928, 2459,
        7,  153,  386, 1281, 1750,
    # pa  5
        7,  223,  482, 1891, 3541,
        7,  358,  537,  864, 3519,
        7,  370,  556, 1105, 3545,
        7,  417,  628, 1101, 3629,
        7,  407,  693, 1553, 3453,
        7,  197,  539, 1092, 2548,
        7,  186,  399, 1097, 2319,
        7,  202,  389, 1088, 2174,
        7,  216,  361, 1315, 2794,
        7,  215,  433, 1312, 2778,
        7,  171,  306,  993, 2097,
        7,  254,  650, 1558, 2996,
        7,  189,  666, 1190, 2995,
        7,  214,  424, 1286, 2959,
        7,  220,  543, 1346, 2904,
        7,  211,  636, 1281, 2699,
        7,  194,  530, 1113, 2652,
        7,  174,  363, 1040, 2408,
        7,  198,  533, 1175, 2833,
        7,  189,  628, 1142, 2638,
    # pa  6
        7,  254,  450, 1247, 2169,
        7,  265,  398, 1117, 2047,
        7,  211,  317, 1486, 2238,
        7,  158,  237, 1474, 2211,
        7,  301,  524, 1159, 2062,
        7,  190,  308,  438, 1750,
        7,  173,  265,  438, 1750,
        7,  114,  183,  438, 1750,
        7,  139,  283,  438, 1750,
        7,  129,  292,  510, 1750,
        7,  135,  263,  470, 1782,
        7,  199,  326,  438, 1805,
        7,  146,  243,  438, 1750,
        7,   67,  130,  438, 1750,
        7,  150,  224,  438, 1750,
        7,  146,  247,  449, 1750,
        7,   83,  147,  438, 1750,
        7,  146,  221,  438, 1750,
        7,  190,  359,  558, 1761,
        7,  101,  446, 1013, 1750,
    # pa  7
        7,  169,  228,  438, 1750,
        7,  113,  267,  438, 1750,
        7,  187,  295,  689, 1750,
        7,  189,  258,  593, 1750,
        7,  164,  206,  438, 1750,
        7,  204,  265,  438, 1750,
        7,  154,  246,  438, 1750,
        7,  201,  244,  438, 1750,
        7,  130,  307,  438, 1750,
        7,  183,  296,  487, 1750,
        7,  183,  239,  449, 1750,
        7,  119,  187,  438, 1750,
        7,  163,  270,  438, 1750,
        7,  180,  228,  438, 1750,
        7,  175,  240,  438, 1750,
        7,  174,  249,  459, 1750,
        7,  143,  221,  438, 1750,
        7,  192,  212,  438, 1750,
        7,  164,  292,  438, 1750,
        7,  150,  217,  438, 1750,
    # pa  8
        7,  121,  212,  438, 1750,
        7,  124,  211,  438, 1750,
        7,  173,  266,  438, 1750,
        7,  162,  240,  438, 1750,
        7,  179,  259,  453, 1750,
        7,  203,  272,  438, 1750,
        7,  182,  233,  438, 1750,
        7,  206,  268,  438, 1750,
        7,  176,  267,  438, 1750,
        7,  198,  293,  438, 1750,
        7,  175,  283,  438, 1750,
        7,  170,  221,  438, 1750,
        7,  176,  256,  438, 1750,
        7,  129,  184,  438, 1750,
        7,  168,  203,  438, 1750,
        7,  186,  267,  438, 1750,
        7,  183,  265,  438, 1750,
        7,  186,  298,  438, 1750,
        7,  167,  247,  438, 1750,
        7,  171,  206,  438, 1750,
    # pa  9
        7,  130,  299, 1019, 1750,
        7,  179,  332,  927, 1750,
        7,  180,  354, 1009, 1803,
        7,  169,  251,  844, 1750,
        7,  176,  312, 1330, 2289,
        7,  190,  312, 1393, 2144,
        7,  178,  288, 1403, 2322,
        7,  165,  267, 1078, 1800,
        7,  100,  355, 1231, 1817,
        7,  184,  374, 1203, 1795,
        7,  159,  470, 1376, 1927,
        7,  189,  405, 1200, 1750,
        7,  143,  387, 1031, 1750,
        7,  122,  359,  833, 1750,
        7,  173,  334,  801, 1750,
        7,  184,  261,  691, 1750,
        7,  167,  241,  570, 1750,
        7,  204,  267,  549, 1750,
        7,  201,  266,  520, 1750,
        7,  204,  247,  550, 1750,
    # pa 10
        7,  167,  461, 1220, 3544,
        7,  171,  466,  795, 3716,
        7,  171,  482, 1085, 3481,
        7,  155,  401,  826, 2209,
        7,  172,  475,  741, 3234,
        7,  170,  464,  734, 2659,
        7,  172,  469,  740, 3228,
        7,  170,  460,  885, 3404,
        7,  179,  485,  852, 3924,
        7,  192,  524,  982, 4202,
        7,  193,  538, 1048, 4459,
        7,  178,  486,  696, 3463,
        7,  170,  475,  923, 3767,
        7,  153,  420,  797, 2482,
        7,  185,  410,  885, 2909,
        7,  144,  399,  615, 2720,
        7,  155,  352,  742, 2447,
        7,  127,  332,  603, 1885,
        7,  127,  338,  787, 1968,
        7,  145,  417,  839, 2788,
    # pa 11
        7,  241,  585, 1931, 2539,
        7,  134,  344, 1342, 1858,
        7,  208,  467, 1701, 2434,
        7,  127,  321, 1089, 1816,
        7,  177,  414, 1557, 2131,
        7,  152,  290, 1019, 1941,
        7,  134,  479, 1296, 1805,
        7,  185,  321, 1009, 2316,
        7,  129,  321, 1151, 1941,
        7,  185,  479, 1401, 2378,
        7,  152,  347, 1183, 2066,
        7,  190,  490, 1690, 2361,
        7,  153,  290,  897, 2003,
        7,  176,  505, 1577, 2123,
        7,  250,  583, 1970, 2552,
        7,  248,  572, 1970, 2643,
        7,  249,  580, 1974, 2619,
        7,  149,  386, 1417, 1951,
        7,  154,  479, 1517, 2066,
        7,  154,  437, 1583, 1958,
    # pa 12
        7,   29,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   31,  109,  438, 1750,
    # pa 13
        7,   38,  129,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   39,  134,  438, 1750,
        7,   36,  132,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   33,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   27,  109,  438, 1750,
        7,   28,  109,  438, 1750,
        7,   51,  184,  474, 1750,
        7,   53,  182,  474, 1750,
        7,   51,  181,  438, 1750,
        7,   42,  153,  500, 1750,
        7,   53,  188,  585, 1750,
        7,   85,  293,  744, 1750,
)

# blake2b over the table above, the same instrument as GROUND_DIGEST and for
# the same reason: one golden value beats 1,400 hand-written checks.
PATCH_LOD_DIGEST = "3b42b398bcc5242e"

_PATCH_LOD_CACHE = {}
_COLLISION_REACH = {}


def patch_lod_error_m(pa, pz):
    """The pinned per-patch deviation of each stride from lod0, in metres."""
    i = ((pa % PATCHES_A) * PATCHES_Z + pz) * len(STRIDES)
    return tuple(PATCH_LOD_ERR_MM[i + k] / 1000.0 for k in range(len(STRIDES)))


def measure_patch_lod_error(pa, pz):
    """Derive one patch's row, the same way `lod_error_report` derives the max.

    THE TRUE HEIGHTS ARE SAMPLED ONCE FOR ALL FIVE STRIDES. Every coarse
    lattice point is a lod0 lattice point -- STRIDES' own comment says so -- so
    a 33 x 33 grid of the true field serves every level, and the derivation is
    305,000 `sample()` calls instead of 1.9 million.
    """
    ia0, iz0 = pa * PATCH_A, pz * PATCH_Z
    true = [[sample(((ia0 + da) % CELLS_A) / CELLS_A, (iz0 + dz) / CELLS_Z)[0]
             for dz in range(PATCH_Z + 1)]
            for da in range(PATCH_A + 1)]
    out = []
    for stride in STRIDES:
        worst = 0.0
        for da in range(PATCH_A + 1):
            ka0 = (da // stride) * stride
            ka1 = min(ka0 + stride, PATCH_A)
            ta = 0.0 if ka1 == ka0 else (da - ka0) / (ka1 - ka0)
            for dz in range(PATCH_Z + 1):
                kz0 = (dz // stride) * stride
                kz1 = min(kz0 + stride, PATCH_Z)
                tz = 0.0 if kz1 == kz0 else (dz - kz0) / (kz1 - kz0)
                approx = (true[ka0][kz0] * (1 - ta) * (1 - tz)
                          + true[ka1][kz0] * ta * (1 - tz)
                          + true[ka0][kz1] * (1 - ta) * tz
                          + true[ka1][kz1] * ta * tz)
                e = abs(true[da][dz] - approx)
                if e > worst:
                    worst = e
        dtheta = 2.0 * math.pi * stride / CELLS_A
        out.append(max(worst, FLOOR_R * (1.0 - math.cos(dtheta / 2.0))))
    return tuple(out)


def collision_reach_m():
    """How far from the eye `drum_walk` builds a collision surface.

    THE PER-PATCH TABLE MAY NOT COARSEN ANYTHING A PLAYER CAN STAND ON.
    `drum_walk` builds its collision tile at a uniform stride 1 and then asserts
    two things against the render ground: that a body stands on the ground it
    can see (within `STEP_M`), and that inside the render's own lod0 radius the
    two are the IDENTICAL surface. Both are statements about the mesh inside
    the tile, so inside the tile the per-patch table is held at the drum-wide
    one and the render there is exactly what it is today. Read from `drum_walk`
    rather than restated, because a second copy of a tile size is a second thing
    to get wrong -- imported inside the function because `drum_walk` imports
    this module.
    """
    if "reach" not in _COLLISION_REACH:
        import drum_walk as _dw                                # noqa: PLC0415
        a_m, z_m = _dw.patch_span_m()
        rings = _dw.rings_for(_dw.walk_distance_m())
        _COLLISION_REACH["reach"] = math.hypot((rings + 0.5) * a_m,
                                               (rings + 0.5) * z_m)
    return _COLLISION_REACH["reach"]


def patch_lod_table(pa, pz, table=None):
    """Switch distances for ONE patch: per-patch error, floored by the tile.

    Monotonic by the same running max `lod_table` uses, and for the same
    reason. `table` is the drum-wide table, which supplies both the floor
    inside the collision tile and the per-patch triangle counts.
    """
    table = table or lod_table()
    key = (pa % PATCHES_A, pz, id(table))
    if key in _PATCH_LOD_CACHE:
        return _PATCH_LOD_CACHE[key]
    reach = collision_reach_m()
    d, out = 0.0, []
    for lvl, err in enumerate(patch_lod_error_m(pa, pz)):
        floor_m = min(table[lvl]["switch_distance_m"], reach)
        d = max(d, _switch_distance(err), floor_m)
        out.append(d)
    _PATCH_LOD_CACHE[key] = tuple(out)
    return _PATCH_LOD_CACHE[key]


def patch_level(pa, pz, distance_m, table=None):
    """The level patch (pa, pz) may be drawn at, `distance_m` from the eye."""
    sw = patch_lod_table(pa, pz, table)
    lvl = 0
    for i, s in enumerate(sw):
        if distance_m >= s:
            lvl = i
    return lvl



# ---------------------------------------------------------------------------
# Visible set
# ---------------------------------------------------------------------------

def visible_set(eye, patches=None, table=None):
    """Every ground patch, each at the level its distance from `eye` allows.

    There is no occlusion culling here and there should not be: standing in the
    Garden there is no wall. The far side of the drum is 556 m overhead and both
    end caps are in frame. That is why the drum has its own budget gate and why
    this function is the thing that has to be measured against it -- the whole
    drum at lod0 is 573,440 triangles, nearly twice the entire drum allowance.

    AND IT IS NOT AN ARGUMENT, IT IS MEASURED. Session 4r cast the sight line
    from the budget gate's own worst eye to all 280 patches and to every
    dressing feature: a perfect, free, per-feature occlusion pass removes
    16,008 of 315,604 triangles -- 5.07% -- and leaves the drum at 99.9% of its
    allowance. Flatten the heightfield to the mean cylinder and the number is
    0 of 1,440 targets, which is the control and which is what the interior of
    a convex region has to report. INV-541.

    THE LEVEL IS THE PATCH'S OWN, not the drum's -- `patch_lod_table`, INV-540.
    """
    table = table or lod_table()

    chosen = {}
    for pa in range(PATCHES_A):
        for pz in range(PATCHES_Z):
            d = patch_nearest_distance(pa, pz, eye)
            chosen[(pa, pz)] = patch_level(pa, pz, d, table)

    verts, tris, groups = [], [], []
    per_level = [0] * len(STRIDES)
    todo = patches if patches is not None else sorted(chosen)
    for (pa, pz) in todo:
        lvl = chosen[(pa, pz)]
        stride = STRIDES[lvl]
        nb = {
            "a-": STRIDES[chosen[((pa - 1) % PATCHES_A, pz)]],
            "a+": STRIDES[chosen[((pa + 1) % PATCHES_A, pz)]],
            "z-": STRIDES[chosen[(pa, pz - 1)]] if pz > 0 else None,
            "z+": STRIDES[chosen[(pa, pz + 1)]] if pz < PATCHES_Z - 1 else None,
        }
        v, t, g, _m = ground_patch(pa, pz, stride, nb)
        o = len(verts)
        verts.extend(v)
        tris.extend((a + o, b + o, c + o) for a, b, c in t)
        groups.extend(g)
        per_level[lvl] += len(t)

    area = 2.0 * math.pi * FLOOR_R * (Z1 - Z0)
    return verts, tris, groups, {
        "eye": tuple(round(x, 1) for x in eye),
        "patches": len(todo),
        "triangles": len(tris),
        "triangles_per_level": per_level,
        "patches_per_level": [sum(1 for k in chosen.values() if k == i)
                              for i in range(len(STRIDES))],
        "area_m2": round(area, 0),
        "tris_per_m2": len(tris) / area,
        "levels": chosen,
    }


def visible_cost(eye, table=None):
    """Triangle count for a viewpoint WITHOUT building the geometry.

    Counting by building costs about fifteen seconds a viewpoint, which is
    enough to stop anyone sweeping for the worst case -- and the worst case is
    the only one a budget gate cares about. Level assignment is a pure function
    of patch position, so the count is a sum over 280 patches and is instant.
    """
    table = table or lod_table()
    total = 0
    per = [0] * len(STRIDES)
    for pa in range(PATCHES_A):
        for pz in range(PATCHES_Z):
            lvl = patch_level(pa, pz, patch_nearest_distance(pa, pz, eye),
                              table)
            n = table[lvl]["patch_triangles"]
            total += n
            per[lvl] += 1
    return total, per


def worst_case_cost(samples=12, table=None):
    """The most expensive place to stand, swept over the ground.

    Cost is not uniform: standing at an end cap puts half the drum beyond the
    lod3 switch, while standing at mid-length puts everything inside lod2. The
    gate has to be met from the worst spot, not from a convenient one.
    """
    table = table or lod_table()
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    worst = (0, None, None)
    for i in range(samples):
        ang = 360.0 * i / samples
        for f in (0.05, 0.5, 0.95):
            z = Z0 + f * (Z1 - Z0)
            eye, _up = stand_on_ground(schema, profile, sector, ang, z)
            n, per = visible_cost(eye, table)
            if n > worst[0]:
                worst = (n, (round(ang, 1), round(z, 1)), per)
    return {"triangles": worst[0], "at": worst[1], "patches_per_level": worst[2],
            "tris_per_m2": worst[0] / (2 * math.pi * FLOOR_R * (Z1 - Z0))}


def triangle_report():
    """Cost of the ground at each uniform level, and of the LOD-resolved set.

    The uniform-level column is what the ground would cost with no LOD at all,
    and it is the argument for having any: lod0 across the drum is 573,440
    triangles against a 300,000-triangle drum allowance that already spends
    42,696 on shell, caps, trusses and spokes.
    """
    table = lod_table()
    area = 2.0 * math.pi * FLOOR_R * (Z1 - Z0)
    rows = []
    for i, row in enumerate(table):
        n = PATCHES_A * PATCHES_Z * row["patch_triangles"]
        rows.append({
            "level": row["level"],
            "cell_m": row["cell_m"],
            "switch_distance_m": row["switch_distance_m"],
            "whole_drum_triangles": n,
            "whole_drum_tris_per_m2": round(n / area, 4),
        })
    return {"area_m2": round(area, 0), "uniform": rows}


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# WHY THE PARCEL BOUNDARY READS AS A DRAWN LINE, MEASURED
# ---------------------------------------------------------------------------
# STATE.md 24.4b, against `docs/engine-4q-drum-dressed.png`: "the parcel boundary
# is still a hard straight edge where green meets tan in the foreground", and it
# names this module's half of it as "a drawn line rather than a change in the
# ground". Measured -- 140 hedge-tagged samples across the whole drum, profiled
# over a 32 m window perpendicular to the boundary -- **that reading is wrong,
# and being wrong about it is the useful part**:
#
#     level change across a 32 m window   median 0.581 m, p10 0.232, p90 3.198
#     bank prominence (centre - ends)     median 0.068 m
#
# The ground DOES change. At `--stand 20,4700`, the frame the finding was made
# from, it changes by **1.05 m over 28 m**. What it does not do is change
# VISIBLY: 0.581 m over 32 m is **1.04 degrees**, and one degree of slope at 5 m
# displaces the horizon by 9 cm, which is nothing. Meanwhile the MATERIAL changes
# instantaneously, because `_KIND_GROUP` hands `arable2` and `arable1` two
# different groups at the cell boundary. A hard tonal step on a surface with no
# visible geometric step is exactly what "a drawn line" describes.
#
# AND THE FIX IS NOT TO SHARPEN IT. The step rule above this module's `_parcel`
# forbids anything narrower than one stride-8 cell -- 31.2 m -- and gives the
# measurement: the first version of this module put 3.5 m steps over 6 m in the
# field, which produced a 3.28 m lod1 error, a 3,379 m switch distance and the
# whole 573,440-triangle field at lod0. A field edge you can SEE as terrain is a
# field edge that costs the drum its LOD chain.
#
# So the boundary has to be an OBJECT standing on the ground, and it now is:
# `drum_dressing`'s hedgerow has always run the line, and its near rung puts
# rough grass on the bank inside the distance at which a player can tell. This
# assertion exists so that a future session reads the measurement before
# reaching for the heightfield.
BOUNDARY_WINDOW_M = 32.0
_ARABLE_TAGS = {"arable"} | {f"arable{i}" for i in range(CROPS)}


def parcel_boundary_relief(samples=140, window_m=None):
    """How much the ground changes across a tagged parcel boundary.

    DIFFERENTIAL, and the first version was not -- which its own control caught.
    Written as an absolute ("the 32 m window across a boundary changes by
    0.581 m"), the number survives `PARCEL_RELIEF_M = 0` almost intact: it drops
    only to 0.269 m, because a 32 m window anywhere on a six-octave fbm field
    changes by about that much. The measurement could not tell a parcel step
    from the terrain it sits in, so the assertion built on it could not fail for
    the thing it was named for. The control window is the same width at the same
    z, half a parcel away, in open field -- and the reported figure is the
    DIFFERENCE.
    """
    window_m = BOUNDARY_WINDOW_M if window_m is None else window_m
    circ = 2.0 * math.pi * FLOOR_R
    half_parcel = 0.5 * circ / PARCELS_A

    def span(u, w):
        prof = []
        n = 16
        for k in range(n + 1):
            uu = (u + (k / n - 0.5) * window_m / circ) % 1.0
            prof.append(sample(uu, w)[0])
        return max(prof) - min(prof), prof[n // 2] - 0.5 * (prof[0] + prof[-1])

    edge, interior, bank, paired = [], [], [], []
    for ia in range(0, CELLS_A, 7):
        for iz in range(0, CELLS_Z, 17):
            u, w = (ia + 0.5) / CELLS_A, (iz + 0.5) / CELLS_Z
            if sample(u, w)[1] != "hedge":
                continue
            uc = (u + half_parcel / circ) % 1.0
            if sample(uc, w)[1] not in _ARABLE_TAGS:
                continue
            e, b = span(u, w)
            c, _b2 = span(uc, w)
            edge.append(e)
            interior.append(c)
            paired.append(e - c)
            bank.append(b)
            if len(edge) >= samples:
                break
        if len(edge) >= samples:
            break
    if not edge:
        return None
    edge.sort()
    interior.sort()
    bank.sort()
    paired.sort()
    e_med = edge[len(edge) // 2]
    i_med = interior[len(interior) // 2]
    return {
        "samples": len(edge),
        "window_m": window_m,
        "edge_median_m": round(e_med, 3),
        "open_field_median_m": round(i_med, 3),
        # PAIRED, not a difference of two medians: each boundary is compared
        # with the open field at its own z, so terrain that happens to be
        # rougher where the boundaries fall cannot be read as a parcel step.
        "excess_m": round(paired[len(paired) // 2], 3),
        "excess_unpaired_m": round(e_med - i_med, 3),
        "excess_p75_m": round(paired[len(paired) * 3 // 4], 3),
        # THE UPPER QUARTILE IS THE ONE ASSERTED ON, AND THE REASON IS IN
        # `_parcel`: a parcel's level is quantised to three values, so two
        # neighbours agree about one time in three and the ground between them
        # is then genuinely continuous. A median over all boundaries therefore
        # sits within a few centimetres of the bank height (0.231 against 0.220)
        # and an assertion on it would flap on sampling noise while separating
        # built from control by only 5%. On p75 the same pair is 0.536 against
        # 0.199 -- built passes with 2.4x and the control fails outright.
        "edge_p90_m": round(edge[len(edge) * 9 // 10], 3),
        "bank_median_m": round(bank[len(bank) // 2], 3),
        "slope_median_deg": round(math.degrees(math.atan(e_med / window_m)), 3),
        "step_ramp_m": round(_step_ramp_m(), 1),
    }


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile, sector = configure()

    check("bound to the drum by geometry, not by name", sector == "green",
          f"{sector}")
    check("floor datum is the canon 278.3 m", abs(FLOOR_R - 278.3) < 0.05,
          f"{FLOOR_R}")

    # --- determinism -------------------------------------------------------
    # The value source, not the geometry. If this constant moves, something has
    # replaced FNV-1a with a salted hash and every later assertion about
    # byte-identical regeneration is testing the wrong thing.
    # This assertion's NAME LIED. It was
    #     _fnv1a("drum", 7, "ground") == _fnv1a("drum", 7, "ground")
    # which is x == x, computed in one process, and therefore said nothing at
    # all about stability across processes -- the one property it is named for
    # and the one the whole determinism argument rests on. Found by
    # `tools/mutation_sweep.py`: perturbing _FNV_OFFSET or _FNV_PRIME changed
    # every height in the drum and not one of 74 assertions noticed, because
    # "run it twice and compare" is satisfied by ANY pair of constants.
    #
    # Three replacements, each testing something the others cannot:
    #
    # 1. The constants are the PUBLISHED FNV-1a 64-bit values. That is an
    #    external fact, so a typo in either is caught against the standard
    #    rather than against ourselves.
    check("the FNV constants are the published FNV-1a 64-bit values",
          _FNV_OFFSET == 0xCBF29CE484222325 and _FNV_PRIME == 0x100000001B3,
          f"offset {_FNV_OFFSET:#x}, prime {_FNV_PRIME:#x}")
    # 2. The delimiter test, which was the only real clause in the original:
    #    ("a","bc") and ("ab","c") must not collide.
    check("field boundaries are not ambiguous",
          _fnv1a("a", "bc") != _fnv1a("ab", "c"))
    # 3. Actually cross a process boundary, with a DIFFERENT PYTHONHASHSEED,
    #    which is the thing the old name claimed. Python salts `str.__hash__`
    #    per process, so if anything in the chain ever falls back to it this is
    #    what fails -- and it cannot be satisfied by running in one interpreter.
    _probe = (
        "import sys, json; sys.path.insert(0, %r); import drum_ground as g;"
        "g.configure(); print(json.dumps([g._fnv1a('drum', 7, 'ground'),"
        "[round(x, 9) for x in g.ground_patch(3, 7, 2)[0][0]]]))"
        % os.path.dirname(os.path.abspath(__file__))
    )
    outs = []
    for seed in ("0", "999983"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", _probe], capture_output=True,
                           text=True, env=env,
                           cwd=os.path.dirname(os.path.abspath(__file__)))
        outs.append(r.stdout.strip().splitlines()[-1] if r.returncode == 0 else
                    f"FAILED: {r.stderr.strip()[-160:]}")
    check("the terrain is identical under two PYTHONHASHSEEDs, in two processes",
          outs[0] == outs[1] and not outs[0].startswith("FAILED"),
          f"{outs[0][:80]} vs {outs[1][:80]}")

    # And a GOLDEN DIGEST over the heightfield itself. One assertion pinning
    # every terrain constant at once -- the noise octaves and gain, the parcel
    # lattice, the water level, the road widths, the FNV constants above. The
    # sweep found ~20 of them individually unguarded; guarding each by hand
    # would be twenty assertions restating twenty constants, which is how this
    # module got here. This instead says: THE GROUND IS THIS SHAPE.
    #
    # It is meant to be brittle. A terrain change SHOULD fail it, be looked at,
    # and have the digest updated deliberately -- the same argument as the
    # committed `cell_manifest.json` diff gate in CI. A silent terrain change
    # is the failure mode; a noisy one is the fix.
    _grid = []
    for i in range(16):
        for j in range(16):
            h, kind = sample(i / 16.0, j / 16.0)
            _grid.append(f"{h:.6f}:{kind}")
    _digest = hashlib.blake2b("|".join(_grid).encode(), digest_size=8).hexdigest()
    check("the heightfield still has its committed shape",
          _digest == GROUND_DIGEST,
          f"{_digest} != {GROUND_DIGEST} -- the terrain moved. If that was "
          f"deliberate, look at a render and update GROUND_DIGEST")
    # This was
    #     "random" not in sys.modules or not hasattr(sys.modules.get("random"),
    #                                                "_inst_used_by_drum")
    # and `_inst_used_by_drum` is a name NOTHING in this repository sets --
    # `grep -r` finds it once, in the assertion itself. So `hasattr` is always
    # False, `not hasattr` is always True, and the second clause is the constant
    # True. The check could not fail for any change to any module, which is a
    # peculiarly bad outcome for a determinism guard: the golden digest and the
    # two-process seed test both catch a terrain that has ALREADY changed, and
    # this was supposed to be the one that catches the mechanism.
    #
    # So catch the mechanism. Make every public entry point of `random` raise,
    # build ground with it, and put the module back. A live call through
    # `random` -- however it got into the import graph -- now stops the suite
    # instead of being invisible until a digest mismatch nobody can explain.
    import random as _rnd
    _tripped = []

    def _forbid(name):
        def f(*_a, **_k):
            _tripped.append(name)
            raise AssertionError(f"drum_ground called random.{name}()")
        return f

    _names = [n for n in dir(_rnd)
              if not n.startswith("_") and callable(getattr(_rnd, n, None))
              and n not in ("Random", "SystemRandom")]
    _saved = {n: getattr(_rnd, n) for n in _names}
    try:
        for n in _names:
            setattr(_rnd, n, _forbid(n))
        _probe_ok, _probe_err = True, ""
        try:
            sample(0.317, 0.611)
            ground_patch(2, 4, 4)
        except Exception as exc:                      # noqa: BLE001
            _probe_ok, _probe_err = False, str(exc)
    finally:
        for n, fn in _saved.items():
            setattr(_rnd, n, fn)
    check("building ground calls nothing in `random`", _probe_ok,
          f"{_probe_err} (tripped: {sorted(set(_tripped))})")
    v1 = ground_patch(3, 7, 2)[0]
    v2 = ground_patch(3, 7, 2)[0]
    check("regeneration is byte-identical", v1 == v2,
          f"{sum(1 for a, b in zip(v1, v2) if a != b)} vertices differ")

    # --- the seam at 0 / 360 ------------------------------------------------
    # A non-periodic noise lattice puts a cliff the full 2,586 m length of the
    # drum at one angle, which no render catches unless it happens to point
    # there. Assert the field itself is periodic, not just the mesh.
    # This compared sample(0.0, w) against sample(1.0, w) and COULD NOT FAIL:
    # every consumer inside sample() applies `u % 1.0` first, so the two calls
    # are the same call and the check was a value against itself. Proven by
    # monkeypatching the angular wrap out of _value_noise, which puts a genuine
    # 3.295 m cliff at u=0 -- the old metric still reported 0.000e+00 and still
    # passed. Continuity across the seam is the property that matters, so
    # sample either SIDE of it.
    eps = 1.0 / (CELLS_A * 64.0)
    worst = 0.0
    for k in range(64):
        w = k / 64.0
        worst = max(worst, abs(sample(1.0 - eps, w)[0] - sample(eps, w)[0]))
    # A metre-scale bound, not 1e-12: two samples a real distance apart differ
    # by however much the terrain legitimately varies over that distance, and
    # demanding exact equality would be asserting the terrain is flat there.
    check("the terrain field is continuous across the 0/360 seam",
          worst < 0.05, f"max seam step {worst:.4f} m over {eps:.2e} of a turn")

    # And the mesh: patch 13 and patch 0 must share their edge vertex for
    # vertex. This is the wrap seam `range(n)` never visits.
    left = ground_patch(PATCHES_A - 1, 5, 1)[0]
    right = ground_patch(0, 5, 1)[0]
    a_wrap = 2.0 * math.pi * ((PATCHES_A) * PATCH_A % CELLS_A) / CELLS_A
    def on_angle(vs, ang):
        out = []
        for x, y, z in vs:
            r = math.hypot(x, y)
            d = (math.atan2(y, x) - ang + math.pi) % (2 * math.pi) - math.pi
            if abs(d * r) < 1e-6:
                out.append((round(r, 6), round(z, 4)))
        return sorted(out)
    check("the wrap-around patch seam closes exactly",
          on_angle(left, a_wrap) == on_angle(right, a_wrap)
          and len(on_angle(right, a_wrap)) == PATCH_Z + 1,
          f"{len(on_angle(left, a_wrap))} vs {len(on_angle(right, a_wrap))}")

    # --- tagged widths are the REAL widths ---------------------------------
    # The kind tag used to ride on the LOD's geometry ramp, so a 20 m trunk road
    # tagged 51.2 m and a street on a 62.5 m block tagged 31.2 m -- about 74% of
    # the settlement band was street. Both are asserted against their own stated
    # widths now, derived rather than compared to a remembered number.
    circ = 2.0 * math.pi * FLOOR_R
    # Walk a transect across a trunk road and measure where the tag starts and
    # stops. The boundary between the last two land-use bands carries one.
    bands = _bands()
    lo = next(b[0] for b in bands[1:] if b[2] != "water"
              and bands[bands.index(b) - 1][2] != "water")
    n = 4000
    tagged = [k for k in
              (sample((lo + (i - n // 2) / float(n) * 0.06) % 1.0, 0.5)[1]
               for i in range(n)) if k == "road"]
    got = len(tagged) / float(n) * 0.06 * circ
    check("a trunk road tags at its own width, not the LOD ramp",
          abs(got - TRUNK_ROAD_W_M) < 3.0,
          f"{got:.1f} m tagged against a stated {TRUNK_ROAD_W_M} m")

    # And the street grid. Sampled OFF the block lattice: w = 0.5 lands exactly
    # on a block boundary at the 40-cell pitch, where d_edge is 0 by
    # construction, and measuring there reports every cell as street.
    na, nz = CELLS_A // BLOCK_CELLS, CELLS_Z // BLOCK_CELLS
    block_a, block_z = circ / na, (Z1 - Z0) / nz
    predicted = 1.0 - ((block_a - AVENUE_W_M) / block_a) * \
        ((block_z - AVENUE_W_M) / block_z)
    NA = NZ = 401
    seen = [sample((i + 0.5) / NA, (j + 0.5) / NZ)[1]
            for i in range(NA) for j in range(NZ)]
    av = sum(1 for k in seen if k == "avenue")
    se = sum(1 for k in seen if k in ("settlement", "avenue"))
    share = av / float(max(se, 1))
    check("the street grid covers the fraction its own width implies",
          abs(share - predicted) < 0.12,
          f"{share*100:.1f}% of the settlement band against {predicted*100:.1f}% "
          f"predicted for a {AVENUE_W_M} m street on {block_a:.0f} x {block_z:.0f} m blocks")
    check("verge is a made shoulder, not the whole ramp",
          VERGE_W_M < _step_ramp_m() / 4.0,
          f"{VERGE_W_M} m against a {_step_ramp_m():.1f} m LOD ramp")

    # --- watertight with the drum shell and the end caps -------------------
    # `drum_end_cap()` puts its rim circle at exactly the floor radius, so the
    # ground must arrive at the caps with zero relief or there is a gap between
    # the ground and the bulkhead at 1 g.
    worst = 0.0
    for k in range(64):
        u = k / 64.0
        worst = max(worst, abs(sample(u, 0.0)[0]), abs(sample(u, 1.0)[0]))
    check("ground arrives at the caps with no relief", worst < 1e-9,
          f"max relief at the caps {worst:.3e} m")

    # And it must actually REACH them. The check above measures only the
    # ground; a surface can arrive perfectly flat and still stop short. Measure
    # the distance to the cap's own triangles.
    schema_c, profile_c = it.load()
    sec_c = it.drum_sector(schema_c, profile_c)
    for end, w_edge in (("aft", 0.0), ("fore", 1.0)):
        cv, ct, _cm = it.drum_end_cap(schema_c, profile_c, sec_c, end)
        # Cap vertices sitting on the floor-radius ring.
        ring = [q for q in cv
                if abs(math.hypot(q[0], q[1]) - FLOOR_R) < 0.05]
        gz = surface_point(0.0, w_edge)[2] if callable(
            globals().get("surface_point")) else (Z0 if w_edge == 0.0 else Z1)
        gap = min(abs(q[2] - gz) for q in ring) if ring else float("inf")
        check(f"ground reaches the {end} cap",
              gap < 0.01, f"{gap:.3f} m short of the cap plate")

    # Continuity across land-use band boundaries. `drum_interior()` steps
    # between bands with no wall between them; the heightfield must not, or the
    # seam is a hole running the whole length of the drum.
    circ = 2.0 * math.pi * FLOOR_R
    for lo, _hi, name, _relief in _bands():
        step = 0.0
        for k in range(-40, 41):
            u0 = (lo + k * 0.25 / circ) % 1.0
            u1 = (lo + (k + 1) * 0.25 / circ) % 1.0
            step = max(step, abs(sample(u0, 0.5)[0] - sample(u1, 0.5)[0]))
        # 0.25 m of horizontal travel may not produce more than a gentle slope.
        check(f"band boundary at {name} is continuous", step < 0.35,
              f"max step {step:.3f} m over 0.25 m")

    # The heightfield and LAND_USE must describe the same surface. If the mean
    # relief in a band drifts from the table, the ground and the shell disagree
    # about where the lake is -- the exact class of failure CLAUDE.md rule 4
    # exists to prevent.
    for lo, hi, name, relief in _bands():
        # Sample the band's core, away from the transitions.
        pad = (BAND_BLEND_M / circ)
        us = [lo + pad + (hi - lo - 2 * pad) * i / 24.0 for i in range(25)]
        if hi - lo <= 2 * pad:
            continue
        hs = [sample(u % 1.0, 0.5)[0] for u in us]
        mean = sum(hs) / len(hs)
        check(f"{name} band mean tracks LAND_USE relief",
              abs(mean - relief) < 2.6,
              f"mean {mean:.2f} m vs table {relief} m")

    # --- land-use character -------------------------------------------------
    def band_centre(name):
        for lo, hi, nm, _r in _bands():
            if nm == name:
                return (lo + hi) / 2.0
        raise KeyError(name)

    def band_stats(name, n=48):
        u0 = band_centre(name)
        hs = [sample((u0 + (i - n / 2) * 0.4 / circ) % 1.0, 0.35 + j * 0.012)[0]
              for i in range(n) for j in range(12)]
        return min(hs), max(hs), sum(hs) / len(hs)

    lo_ar, hi_ar, _m = band_stats("arable")
    lo_st, hi_st, mean_st = band_stats("settlement")
    lo_pk, hi_pk, _m = band_stats("parkland")
    lo_wa, hi_wa, _m = band_stats("water")

    check("water is a depression", hi_wa <= WATER_LEVEL_M + 1e-6,
          f"highest water-band point {hi_wa:.2f} m")
    check("settlement is raised above arable", mean_st > hi_ar,
          f"settlement mean {mean_st:.2f} vs arable max {hi_ar:.2f}")
    check("settlement is blockier than parkland",
          (hi_st - lo_st) > (hi_pk - lo_pk),
          f"settlement range {hi_st-lo_st:.2f} m vs parkland "
          f"{hi_pk-lo_pk:.2f} m")
    # Settlement is rectilinear where arable is organic. The test is the
    # difference between a transect ALONG the axis and one across it: an avenue
    # grid on the coarse lattice repeats at the block pitch in both directions,
    # while a warped parcel grid does not.
    u0 = band_centre("settlement")
    block_z = (Z1 - Z0) / (CELLS_Z / BLOCK_CELLS)
    at_block = [_band_relief("settlement", u0, (k * block_z) / (Z1 - Z0))
                for k in range(1, 12)]
    off_block = [_band_relief("settlement", u0,
                              ((k + 0.5) * block_z) / (Z1 - Z0))
                 for k in range(1, 12)]
    check("settlement is cut by an avenue grid on the block pitch",
          sum(at_block) / len(at_block) < sum(off_block) / len(off_block),
          f"on-grid mean {sum(at_block)/len(at_block):.2f} m vs mid-block "
          f"{sum(off_block)/len(off_block):.2f} m")

    # Arable must actually be subdivided: a band with no boundary relief is a
    # lawn, and 34b is emphatically not a lawn. Counting CROSSINGS rather than
    # samples, because the first version of this check ran its transect along
    # w = 0.5 -- which is exactly a parcel boundary in z, so every sample was
    # "in a hedge" and the count said nothing about parcel size.
    crossings, was_in = 0, False
    for i in range(400):
        u = (band_centre("arable") + (i - 200) * 1.0 / circ) % 1.0
        _p, d, _c = _parcel(u, 0.44, PARCELS_A, PARCELS_Z, PARCEL_WARP_M,
                            SEED + "/parcel")
        now = d < HEDGE_W_M / 2.0
        crossings += now and not was_in
        was_in = now
    # 400 m of transect across 116.6 m parcels is 3.4 boundaries. Anything
    # under 1 is a lawn; anything over 8 is allotments, not fields.
    check("arable is subdivided by field boundaries", 1 <= crossings <= 8,
          f"{crossings} boundary crossings in a 400 m transect")
    # Parcels wrap: the count around the circumference is an integer, so parcel
    # 14 neighbours parcel 0. Otherwise the last parcel is a runt with a hedge
    # down one side and a cliff down the other.
    #
    # This compared `_parcel(0.0, w)` against `_parcel(1.0, w)` and COULD NOT
    # FAIL -- the same defect, in the same module, as the seam assertion sixty
    # lines above, which was found and fixed in session 3e and then left here.
    # `_parcel` applies `u % 1.0` on its first line and `_value_noise` applies
    # it again, so u = 1.0 and u = 0.0 are the same call and the check compared
    # a value with itself. Proved by monkeypatching the wrap out of both: the
    # old form still returned equal and still passed.
    #
    # The property is continuity ACROSS the seam, so sample either side of it,
    # exactly as the terrain seam check now does -- and separately require the
    # cell INDEX to wrap, which is the part that makes parcel 14 a neighbour of
    # parcel 0 rather than a runt.
    _pk = (PARCELS_A, PARCELS_Z, PARCEL_WARP_M, SEED + "/parcel")
    eps_p = 1.0 / (PARCELS_A * 4096.0)
    p_lo = _parcel(1.0 - eps_p, 0.5, *_pk)
    p_hi = _parcel(eps_p, 0.5, *_pk)
    check("the parcel field is continuous across the 0/360 seam",
          abs(p_lo[0] - p_hi[0]) < 0.02 and abs(p_lo[1] - p_hi[1]) < 0.5,
          f"plateau step {abs(p_lo[0] - p_hi[0]):.4f}, edge-distance step "
          f"{abs(p_lo[1] - p_hi[1]):.4f} m across the seam")
    # The cell index has to WRAP, not restart. Adjacent-or-equal modulo the
    # count is the right form and the measurement says why: the grid is warped
    # by up to PARCEL_WARP_M, so the cell boundary is not at u = 0 and the two
    # samples either side of the seam are both in cell 19 -- one parcel
    # spanning the seam, which is exactly the property. Requiring cell 19 to
    # meet cell 0 would have been asserting the warp away.
    check("the parcel grid closes on itself",
          (p_hi[2][0] - p_lo[2][0]) % PARCELS_A <= 1,
          f"cell {p_lo[2][0]} meets cell {p_hi[2][0]} across the seam, of "
          f"{PARCELS_A}")

    # Roads. 33a shows a ring road at the cap rim; it must exist and it must be
    # flat, because a road that follows the terrain is a track.
    ring_z = Z0 + RIM_ROAD_INSET_M
    w_ring = (ring_z - Z0) / (Z1 - Z0)
    kinds = {sample(i / 32.0, w_ring)[1] for i in range(32)}
    check("a ring road runs round both cap rims",
          "ring_road" in kinds
          and "ring_road" in {sample(i / 32.0, 1.0 - w_ring)[1]
                              for i in range(32)},
          str(sorted(kinds)))

    # --- winding ------------------------------------------------------------
    # The one place the project's convention inverts. An outward-wound ground is
    # not an error, it is an empty frame.
    v, t, g, m = ground_patch(4, 9, 2)
    inward = it._inward_fraction(v, t)
    check("ground faces point toward the spin axis", inward == 1.0,
          f"{inward:.4f} -- outward faces are culled and render as nothing")
    check("every triangle carries a land-use group",
          len(g) == len(t) and all(g))
    # Every kind the field can produce must have a group. Without this a kind
    # added later renders as arable everywhere -- silently, because
    # `_KIND_GROUP.get` has a default and a missing tint is not an error.
    seen_kinds = {sample(i / 240.0, j / 60.0)[1]
                  for i in range(240) for j in range(61)}
    check("every terrain kind maps to a group",
          seen_kinds <= set(_KIND_GROUP), f"unmapped: "
          f"{sorted(seen_kinds - set(_KIND_GROUP))}")
    # And the two that make a landscape legible must actually occur.
    check("field boundaries and avenues are tagged",
          {"hedge", "avenue"} <= seen_kinds, str(sorted(seen_kinds)))

    # --- LOD ----------------------------------------------------------------
    table = lod_table()
    check("every level is a strided subset of lod0",
          all(PATCH_A % s == 0 and PATCH_Z % s == 0 for s in STRIDES))
    # A coarse vertex must be exactly a fine vertex, not nearly one, or a switch
    # slides the ground sideways under the player.
    fine = {(round(x, 6), round(y, 6), round(z, 6))
            for x, y, z in ground_patch(6, 6, 1)[0]}
    for s in STRIDES[1:]:
        coarse = ground_patch(6, 6, s)[0]
        missing = [p for p in coarse
                   if (round(p[0], 6), round(p[1], 6), round(p[2], 6))
                   not in fine]
        check(f"stride {s} vertices all exist at lod0", not missing,
              f"{len(missing)} of {len(coarse)} are new")

    # This was `table[i]["switch_distance_m"] <= table[i+1][...]` and could not
    # fail: `lod_table()` walks the rows with a running max and overwrites each
    # switch distance with it, so the list it returns is sorted by construction
    # -- its own docstring says "Monotonic by construction". The assertion
    # restated the clamp.
    #
    # What the clamp HIDES is the thing worth asserting. If a coarser level's
    # measured error came out below a finer one's, the clamp would quietly give
    # them the same switch distance and one level of the chain would become
    # unreachable. So assert on the errors, which nothing clamps, and then that
    # the clamp had nothing to do.
    check("error grows with stride, so no level is unreachable",
          all(table[i]["error_m"] < table[i + 1]["error_m"]
              for i in range(len(table) - 1)),
          str([r["error_m"] for r in table]))
    clamped = [r for r in table
               if abs(r["switch_distance_m"] - _switch_distance(r["error_m"]))
               > 1.0]
    check("the monotonic clamp in lod_table() never has to fire", not clamped,
          f"{[r['level'] for r in clamped]} had their switch distance raised, "
          "which means a coarser level measured cleaner than a finer one")
    # The sagitta, not the facet width. At the coarsest level the facets are
    # 62 m wide and the pop is 1.75 m -- a factor of 36 apart, which is the
    # mistake CONTRIBUTING.md records.
    coarsest = table[-1]
    facet_w = 2 * math.pi * FLOOR_R * coarsest["stride"] / CELLS_A
    check("LOD error is the sagitta, not the facet width",
          coarsest["curvature_sagitta_m"] < facet_w / 10.0,
          f"sagitta {coarsest['curvature_sagitta_m']:.2f} m vs facet "
          f"{facet_w:.1f} m")
    # This was `row["error_m"] >= row["curvature_sagitta_m"] - 1e-9` at every
    # level, and `lod_error_report` computes `err = max(worst, sagitta)`, so it
    # was `max(a, b) >= b`. Five assertions, none of which could fail, on the
    # number that decides how much ground is drawn.
    #
    # Its NAME is the right test: the switch distance must be set by a MEASURED
    # height error, not by the drum's curvature alone. `lod_error_report`'s own
    # docstring warns that a subsampled measurement reports near zero for
    # exactly the features that cause the pop -- and a near-zero measurement
    # would leave the sagitta winning every `max()` while every one of these
    # assertions still passed. So require the measurement to be the larger term.
    # lod0 is exempt and has to be: at stride 1 nothing is decimated, so its
    # height error is exactly 0 by definition and curvature is all there is.
    for row in table[1:]:
        check(f"{row['level']} error is dominated by a real measurement",
              row["height_error_m"] > row["curvature_sagitta_m"],
              f"measured {row['height_error_m']} m against a "
              f"{row['curvature_sagitta_m']} m sagitta -- the chain is being "
              "sized by geometry, so the heightfield sampling measured nothing")
    check("lod0 is the level with nothing decimated out of it",
          table[0]["height_error_m"] == 0.0
          and table[0]["error_m"] == round(table[0]["curvature_sagitta_m"], 3),
          f"lod0 height error {table[0]['height_error_m']} m")

    # --- the per-patch LOD error, INV-540 -----------------------------------
    _mm = ",".join(str(x) for x in PATCH_LOD_ERR_MM)
    _pd = hashlib.blake2b(_mm.encode(), digest_size=8).hexdigest()
    check("the per-patch LOD table still has its committed shape",
          _pd == PATCH_LOD_DIGEST and len(PATCH_LOD_ERR_MM)
          == PATCHES_A * PATCHES_Z * len(STRIDES),
          f"{_pd} != {PATCH_LOD_DIGEST} over {len(PATCH_LOD_ERR_MM)} values")
    # A DIGEST ONLY SAYS THE PIN IS THE PIN. It cannot say the pin still
    # describes the terrain, which is the failure `--gate-frames` had one level
    # up: a committed artefact a gate could not rebuild. So re-derive a
    # deterministic spread of patches -- one per land-use band, plus an end --
    # on every run. Four patches is 0.8 s; all 280 is 51 s and is
    # `--derive-patch-lod`.
    _subset = sorted({(pa % PATCHES_A, pz) for pa, pz in
                      _representative_patches()})[:4]
    _worst_mm, _at = 0.0, None
    for _pa, _pz in _subset:
        for _k, (_a, _b) in enumerate(zip(measure_patch_lod_error(_pa, _pz),
                                          patch_lod_error_m(_pa, _pz))):
            if abs(_a - _b) * 1000.0 > _worst_mm:
                _worst_mm, _at = abs(_a - _b) * 1000.0, (_pa, _pz, _k)
    check("the pinned per-patch error still measures what it says",
          _worst_mm <= 0.5,
          f"{_worst_mm:.3f} mm at patch/level {_at} over {len(_subset)} "
          f"patches -- the terrain moved under the pin; run "
          f"`--derive-patch-lod` and look at a render")
    # THE CONTROL. Move one pinned value and the check above must fire, or it
    # is measuring nothing. Restored immediately; the table is a tuple, so this
    # rebuilds it rather than mutating a shared object.
    _saved = PATCH_LOD_ERR_MM
    try:
        _i = (_subset[0][0] * PATCHES_Z + _subset[0][1]) * len(STRIDES) + 1
        globals()["PATCH_LOD_ERR_MM"] = (
            _saved[:_i] + (_saved[_i] + 40,) + _saved[_i + 1:])
        _ctl = abs(measure_patch_lod_error(*_subset[0])[1]
                   - patch_lod_error_m(*_subset[0])[1]) * 1000.0
    finally:
        globals()["PATCH_LOD_ERR_MM"] = _saved
    check("...and it fires when a pinned value is wrong", _ctl > 0.5,
          f"a 40 mm perturbation moved the measurement by {_ctl:.3f} mm")

    # NOTHING A PLAYER CAN STAND ON MAY BE COARSER THAN IT IS TODAY.
    # `drum_walk` builds collision at a uniform stride 1 over its tile and
    # asserts the render agrees with it. Inside the tile the per-patch table is
    # floored by the drum-wide one, so the level assigned there is exactly the
    # level assigned today -- checked over every patch at 5 m intervals rather
    # than argued from the floor's algebra.
    _reach = collision_reach_m()
    _coarser = _finer = 0
    for _pa in range(PATCHES_A):
        for _pz in range(PATCHES_Z):
            _sw = patch_lod_table(_pa, _pz, table)
            for _d in range(5, int(_reach), 5):
                _l = max((i for i, s in enumerate(_sw) if _d >= s), default=0)
                _g = level_for_distance(_d, table)
                _coarser += _l > _g
                _finer += _l < _g
    check("inside the collision tile no patch is coarser than it is today",
          _coarser == 0,
          f"{_coarser} of {PATCHES_A*PATCHES_Z*len(range(5,int(_reach),5))} "
          f"patch-distance samples inside {_reach:.0f} m went coarser, which "
          f"is a render surface `drum_walk` compares against stride-1 collision")
    check("...and the representative sample was understating some of them",
          _finer > 0,
          f"{_finer} samples are FINER than the drum-wide table -- if this is "
          f"0 the per-patch measurement found nothing the max() had hidden")
    # And the per-patch table has to be USED, or this is 1,400 numbers doing
    # nothing. Compare the two level assignments beyond the tile.
    _eye_pp, _ = stand_on_ground(schema, profile, sector, 270.0,
                                 (Z0 + Z1) / 2.0)
    _pp = visible_cost(_eye_pp, table)[0]
    _dw = sum(table[level_for_distance(patch_nearest_distance(pa_, pz_, _eye_pp),
                                       table)]["patch_triangles"]
              for pa_ in range(PATCHES_A) for pz_ in range(PATCHES_Z))
    check("the per-patch table changes what gets drawn", _pp < _dw,
          f"per-patch {_pp:,} vs drum-wide {_dw:,} at the budget gate's own "
          f"worst eye -- {(1-_pp/_dw)*100:.1f}% fewer ground triangles")

    # --- LOD seams ----------------------------------------------------------
    # A T-junction between a fine patch and a coarse one leaves a sawtooth of
    # holes. Border clamping is supposed to close it; assert the shared edge
    # matches vertex for vertex, at a level pairing the player will actually
    # see.
    # Patch 1's a+ edge is at u = 0.143, inside an arable band -- deliberately
    # not the water band, whose surface is clamped flat and where an
    # interpolated border is identical to an unclamped one, so the test would
    # pass without exercising anything.
    fine_v = ground_patch(1, 10, 1, {"a+": 4})[0]
    coarse_v = ground_patch(2, 10, 4, {"a-": 1})[0]
    seam_a = 2.0 * math.pi * (2 * PATCH_A) / CELLS_A
    lv, rv = on_angle(fine_v, seam_a), on_angle(coarse_v, seam_a)
    # Every coarse vertex must be present in the fine edge, and every fine
    # vertex must lie ON the coarse edge -- which clamping makes exact.
    check("a fine patch clamps to its coarser neighbour's edge",
          all(any(abs(a - b) < 1e-6 and abs(c - d) < 1e-6 for b, d in lv)
              for a, c in rv) and len(lv) == PATCH_Z + 1,
          f"fine {len(lv)} verts, coarse {len(rv)} verts")
    unclamped = ground_patch(1, 10, 1)[0]
    check("clamping actually moves the border",
          on_angle(unclamped, seam_a) != lv,
          "the clamp is a no-op, so the crack test proves nothing")

    # --- budget -------------------------------------------------------------
    eye, _up = stand_on_ground(schema, profile, sector, 20.0,
                               (Z0 + Z1) / 2.0)
    _v, tri, _g, vm = visible_set(eye, table=table)
    area = vm["area_m2"]
    check("the built set matches the counted set",
          visible_cost(eye, table)[0] == len(tri),
          f"counted {visible_cost(eye, table)[0]:,} vs built {len(tri):,}")
    # The drum gate: 300,000 triangles visible at once, of which the shell,
    # caps, trusses and spokes already take 42,696 and the shell's 23,040 are
    # replaced by this. 0.06 tri/m2 is what is left across 4.5 million m2.
    # Swept, because the cost depends on where you stand.
    worst = worst_case_cost(table=table)
    check("worst-case visible set is inside the drum headroom",
          worst["triangles"] <= 257_304,
          f"{worst['triangles']:,} triangles at {worst['at']}")
    check("worst-case ground density is inside 0.06 tri/m2",
          worst["tris_per_m2"] <= 0.06,
          f"{worst['tris_per_m2']:.4f} tri/m2 over {area/1e6:.1f} million m2")
    # And the number that says LOD is not optional.
    uni = triangle_report()["uniform"][0]["whole_drum_triangles"]
    check("uniform lod0 would blow the whole drum allowance", uni > 300_000,
          f"{uni:,} triangles -- if this ever fits, LOD can be dropped")

    # The patch you are standing in must be at lod0. If the near ground is
    # decimated the whole exercise is pointless.
    near = min(vm["levels"].items(),
               key=lambda kv: patch_nearest_distance(*kv[0], eye))
    check("the patch under the player is lod0", near[1] == 0,
          f"patch {near[0]} at level {near[1]}")
    # And the far half of the drum must NOT be: if the whole field comes out at
    # one level the chain is inert, which is exactly how the first version
    # failed -- it had five levels and used one.
    check("the LOD chain is actually exercised",
          sum(1 for n in vm["patches_per_level"] if n) >= 3,
          f"patches per level {vm['patches_per_level']}")

    # --- standing on it -----------------------------------------------------
    # Both of these used to be restatements of `stand_on_ground`'s own two
    # lines and neither could fail.
    #
    #   "eye stands 1.7 m above the ground" computed
    #       gh = sample((ang / 360.0) % 1.0, 0.5)[0]
    #   and compared FLOOR_R - gh - r_eye against 1.7, where the function had
    #   just set r_eye = FLOOR_R - sample(same u, same w)[0] - 1.7. The two
    #   samples are the same call, so the identity is 1.7 == 1.7. It passes
    #   with the camera buried in a terrace, which is the exact failure the
    #   function's docstring says it exists to prevent.
    #
    #   "up points toward the axis" computed up . eye, where up is
    #   (-cos a, -sin a, 0) and eye is (r cos a, r sin a, z). That dot product
    #   is -r for every angle and every terrain. It is < 0 by algebra.
    #
    # The player does not stand on `sample()`, they stand on TRIANGLES. So cast
    # the ray the camera's own `up` defines, outward from the eye, and require
    # it to hit the built mesh at exactly eye height. That crosses from the
    # field to the geometry -- border clamping, the water clamp and the LOD
    # lattice all live in between -- and it is a unit test of `up` as well,
    # because a mis-scaled or mis-signed `up` moves where the ray goes.
    def _ray_ground(origin, direction, verts, tris):
        """Nearest forward hit, Moller-Trumbore. None if the ray misses."""
        ox, oy, oz = origin
        dx, dy, dz = direction
        best = None
        for a, b, c in tris:
            p0, p1, p2 = verts[a], verts[b], verts[c]
            e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            h = (dy * e2[2] - dz * e2[1], dz * e2[0] - dx * e2[2],
                 dx * e2[1] - dy * e2[0])
            det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
            if -1e-12 < det < 1e-12:
                continue
            inv = 1.0 / det
            s = (ox - p0[0], oy - p0[1], oz - p0[2])
            u_ = inv * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
            if u_ < 0.0 or u_ > 1.0:
                continue
            q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2],
                 s[0] * e1[1] - s[1] * e1[0])
            v_ = inv * (dx * q[0] + dy * q[1] + dz * q[2])
            if v_ < 0.0 or u_ + v_ > 1.0:
                continue
            t_ = inv * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2])
            if t_ > 1e-9 and (best is None or t_ < best):
                best = t_
        return best

    # A camera placed on the CONTINUOUS field cannot sit exactly on the mesh,
    # and should not be expected to: the mesh chords the field between lattice
    # points and chords the drum's curvature as well. Both are bounded and
    # small. A lod0 facet is 3.90 m around by 4.04 m along and its curvature
    # sagitta is 6.8 mm (`lod_table`, lod0); the field's own variation across
    # one facet supplies the rest, and the worst of the six standing points is
    # 17.6 mm. So the tolerance is the mesh's own discretisation, stated here,
    # and the worst observed value is asserted separately below so that bound
    # cannot quietly grow into a datum error nobody notices.
    STAND_TOL_M = 0.05
    worst_stand = 0.0
    z_mid = (Z0 + Z1) / 2.0
    for ang in (0.0, 37.0, 95.0, 180.0, 263.0, 359.0):
        e, up = stand_on_ground(schema, profile, sector, ang, z_mid)
        r_eye = math.hypot(e[0], e[1])
        check(f"up at {ang:g} deg is the unit inward radial",
              abs(math.sqrt(sum(c * c for c in up)) - 1.0) < 1e-12
              and abs(up[0] * e[0] / r_eye + up[1] * e[1] / r_eye + 1.0) < 1e-12
              and up[2] == 0.0,
              f"up {tuple(round(c, 6) for c in up)}")
        # The patch the eye is over, at lod0 -- the level the player is served.
        u_e = (ang / 360.0) % 1.0
        w_e = (z_mid - Z0) / (Z1 - Z0)
        pa = (int(u_e * CELLS_A) // PATCH_A) % PATCHES_A
        pz = min(int(w_e * CELLS_Z) // PATCH_Z, PATCHES_Z - 1)
        pv, pt, _pg, _pm = ground_patch(pa, pz, 1)
        hit = _ray_ground(e, (-up[0], -up[1], -up[2]), pv, pt)
        detail = (f"no hit on patch {(pa, pz)}" if hit is None
                  else f"{hit:.4f} m to the mesh")
        check(f"eye at {ang:g} deg stands 1.7 m above the BUILT ground",
              hit is not None and abs(hit - 1.7) < STAND_TOL_M, detail)
        if hit is not None:
            worst_stand = max(worst_stand, abs(hit - 1.7))
        # And it must not be inside the guideway truss, which flies at 0.85 R.
        check(f"eye at {ang:g} deg is below the guideways",
              r_eye > FLOOR_R * it.TRUSS_RADIUS_FRAC)
    check("the field and the lod0 mesh agree to within a facet's chord",
          worst_stand < 0.03,
          f"worst standing discrepancy {worst_stand * 1000:.1f} mm -- above a "
          "facet's own chord error this is a datum mistake, not discretisation")

    # --- the parcel boundary, both halves of it ---------------------------
    # See the block above `parcel_boundary_relief`. Two assertions, and they
    # pull in opposite directions on purpose: the boundary must carry relief,
    # and that relief must stay gentler than the step rule allows, because a
    # boundary sharp enough to SEE as terrain is one that pins the whole drum
    # at lod0. Anybody who "fixes" the drawn-line finding by steepening the
    # field will trip the second one.
    br = parcel_boundary_relief()
    check("a parcel boundary is a change in the ground, not only in the tag",
          br and br["excess_p75_m"] > HEDGE_H_M,
          f"p75 {br['excess_p75_m'] if br else -1} m more than open field over "
          f"{BOUNDARY_WINDOW_M} m, against a {HEDGE_H_M} m bank "
          f"(median {br['excess_m'] if br else -1} m)")
    check("...and it is gentler than the step rule's own limit, which is why "
          "it reads as a drawn line and needs an OBJECT on it",
          br and br["edge_median_m"] / br["window_m"]
          <= PODIUM_STEP_M / _step_ramp_m(),
          f"{br['slope_median_deg'] if br else -1} deg against the "
          f"{math.degrees(math.atan(PODIUM_STEP_M / _step_ramp_m())):.2f} deg "
          f"a {PODIUM_STEP_M} m step over one {_step_ramp_m():.1f} m ramp makes")
    print(f"      parcel boundary: {br}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _derive_patch_lod():
    """Recompute all 280 rows of PATCH_LOD_ERR_MM and report the drift.

    THE PIN'S REBUILD PATH. `_selftest` re-measures four patches on every run;
    this measures all of them, at 51 s, and prints the replacement table when
    it disagrees. A pin with no rebuild is a committed artefact a gate cannot
    reproduce, which is the defect `--gate-frames` had one level up.
    """
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    configure(schema, profile, sector)
    t0 = time.time()
    rows, worst, at = [], 0.0, None
    for pa in range(PATCHES_A):
        for pz in range(PATCHES_Z):
            errs = measure_patch_lod_error(pa, pz)
            rows.append([int(round(e * 1000)) for e in errs])
            for k, (a_, b_) in enumerate(zip(errs, patch_lod_error_m(pa, pz))):
                if abs(a_ - b_) * 1000.0 > worst:
                    worst, at = abs(a_ - b_) * 1000.0, (pa, pz, k)
    flat = [x for r in rows for x in r]
    dig = hashlib.blake2b(",".join(str(x) for x in flat).encode(),
                          digest_size=8).hexdigest()
    print(f"derived {PATCHES_A * PATCHES_Z} patches x {len(STRIDES)} strides "
          f"in {time.time() - t0:.0f} s")
    print(f"  worst drift against the pin: {worst:.3f} mm at {at}")
    print(f"  digest {dig}  pinned {PATCH_LOD_DIGEST}  "
          f"{'AGREE' if dig == PATCH_LOD_DIGEST else 'DISAGREE'}")
    if dig != PATCH_LOD_DIGEST:
        print("\nPATCH_LOD_ERR_MM = (")
        for pa in range(PATCHES_A):
            print(f"    # pa {pa:2d}")
            for pz in range(PATCHES_Z):
                print("    " + ",".join(f"{x:5d}"
                                        for x in rows[pa * PATCHES_Z + pz])
                      + ",")
        print(")")
        print(f'PATCH_LOD_DIGEST = "{dig}"')
        return 1
    return 0


if __name__ == "__main__":
    if "--derive-patch-lod" in sys.argv:
        sys.exit(_derive_patch_lod())
    sys.exit(_selftest())
