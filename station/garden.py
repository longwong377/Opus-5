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

TREE_H_M = 7.0
TREE_R_M = 2.2
TREE_SEG = 6                        # a tree at 0.06 tri/m2 is a billboard's cousin

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


def block_building(seed):
    """One low blockish building with lit window bands. Cheap by design."""
    v, t, g = [], [], []
    L = BLOCK_MIN_M[0] + _u(seed, "L") * (BLOCK_MAX_M[0] - BLOCK_MIN_M[0])
    W = BLOCK_MIN_M[1] + _u(seed, "W") * (BLOCK_MAX_M[1] - BLOCK_MIN_M[1])
    H = BLOCK_MIN_M[2] + _u(seed, "H") * (BLOCK_MAX_M[2] - BLOCK_MIN_M[2])
    _box(v, t, g, "garden_block", (-L / 2, 0.0, -W / 2), (L / 2, H, W / 2))
    n_band = max(1, min(BLOCK_BANDS, int(H / 3.2)))
    for i in range(n_band):
        y = (i + 0.55) * H / n_band
        _box(v, t, g, "garden_window_band",
             (-L / 2 - 0.06, y - 0.35, -W / 2 - 0.06),
             (L / 2 + 0.06, y + 0.35, W / 2 + 0.06))
    return v, t, g, (L, W, H)


def tree(seed):
    v, t, g = [], [], []
    h = TREE_H_M * (0.75 + 0.5 * _u(seed, "th"))
    _box(v, t, g, "garden_trunk", (-0.22, 0.0, -0.22), (0.22, h * 0.45, 0.22))
    _drum(v, t, g, "garden_canopy", 0.0, 0.0, h * 0.4, h,
          TREE_R_M * (0.8 + 0.4 * _u(seed, "tr")), seg=TREE_SEG)
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
    check("the townscape is inside the drum's 0.5 tri/m2 surface gate",
          dens < 0.5, f"{dens:.4f} tri/m2 over {area:,.0f} m2")
    check("and inside the 0.06 tri/m2 the drum budget actually leaves",
          dens < 0.06, f"{dens:.4f} tri/m2")

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
