#!/usr/bin/env python3
"""The Central Corridor -- Red Sector's grand circulation spine.

`docs/spec/PLACES.md` PLC-056: *"Red's grand circulation spine -- public-scheme
dressing, the crowd's main stage."* The register calls it `central_corridor`,
red/0/0 at 300 degrees, z 6600, 40 deg x 120 m, functions `transit` and
`public_social`, interacts `babcom_terminal`, `gallery_rail`, `door`.

WHY THIS PLACE AND NOT ANOTHER. It is owned by `interior_kit` in the register
and `interior_kit` has no builder for it, so `deck.build_deck` assembled it as
a generic bay -- a 6.9 x 6.0 m store room standing in for the busiest public
volume in the Red Sector. It is also the ONE place in the unbuilt set that a
player crosses on the way to everywhere else: the Zocalo, Earhart's and Waste
Management are all named off the same Red rosette.

SOURCE
------
`reference/09-garden-core-and-transit/central corridor.webp`, **authority 1**,
and `reference/00-INDEX.md` carries the full extraction. What the frame
establishes, item by item, and every one of them is built below:

  * **Two or three concentric circular ring frames crossing the view, DARK
    OXIDE RED** -- thick tubular ribs, the largest passing in front of
    everything at the frame edge. The colour is consistent and strong enough to
    be a deliberate note, not grime.
  * **A narrow catwalk, about two people wide**, with a two-bar railing on
    slender vertical posts and a **solid fascia beam carrying a light line
    along its edge**. People stand on it above people on the lower deck, which
    is what makes the volume two decks tall.
  * **A raked panelled soffit** -- long rectangular panels in canted rows with
    dark joints, running away in trapezoidal bays. Not open truss, not flat.
  * **Diagonal bracing** and **canted planar bulkhead panels** in the upper
    volume.
  * **The centre-line light is a ladder of PAIRED square cells** -- two columns
    of small square lights side by side in a raised dark kerb, running the
    corridor's length.
  * **The floor either side is large pale-blue emitting panels** in a
    running-bond grid with dark joints.
  * **Wall-mounted vertical white light blades** in chamfered dark surrounds,
    with **small red indicator lamps** above them.
  * **A vendor front** at the left -- backlit orange-red panels behind vertical
    mullions over a counter.
  * **A small wheeled trolley with a magenta-lit top.**
  * A dense, mixed, civilian crowd. `populace` supplies that through
    `bespoke.compose`; this module builds the room it stands in.

WHAT IS SOURCED AND IS NOT INVENTION -- the dimensions come from INV-020
-----------------------------------------------------------------------
This module invents **no** primary dimension, and that is deliberate. The
concourse class already exists in `interior_kit.CORRIDOR_CLASSES` and was
derived in INV-020 from THIS FRAME: `corridor_width_m` 9.0, `ceiling_height_m`
7.2 (two INV-010 deck pitches, because the frame shows people standing above
people), `rib_spacing_m` 6.0, `deck_strip_w_m` 0.9. Restating any of them here
would be a second copy of a number, which is how the door decision and the
corridor profile both went wrong in this project before.

What IS new is INV-290 -- the gallery's own dimensions, the rib section, the
paired-cell pitch and the composed run -- and every one of those is derived
from something already fixed rather than picked. See the constants.

THE RUN IS CAPPED AND THE CAP IS SAID OUT LOUD. The place is 187 m of arc by
120 m of axis and PLC-056's tiling target is 540 bays. This builds **four rib
bays, 24.0 m**, which is STATE.md section 13's own rule -- *"tile the bay along
Z to the location's real length, dress only the bays within sight, and state
the cap loudly"* -- with the tiling itself still unbuilt for every place on the
station. `--selftest` prints the ratio so it cannot be forgotten.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior_kit as kit                                      # noqa: E402
import rooms as _rooms                                          # noqa: E402
import bespoke as _bsp                                          # noqa: E402

# ---------------------------------------------------------------------------
# INV-290 -- what this module adds to INV-020, and why each value is that value
# ---------------------------------------------------------------------------
# The class parameters are READ, never restated. `_p()` is the only place any
# of them is fetched, so a change to INV-020 re-derives this whole room.
CLASS = "concourse"

# The composed run, in rib bays. Four because the frame shows three ring frames
# crossing the view with a fourth implied past the vanishing point, and because
# four bays at INV-020's 6.0 m spacing is 24.0 m -- long enough that the
# perspective read the frame depends on actually happens, short enough that the
# room plus its dressing stays inside `budget.CELLS['cell_tris']`.
RIB_BAYS = 4

# THE GALLERY. Its height is not invented: it is one INV-010 deck pitch, which
# is what makes the volume two decks tall in the first place. Its width is the
# frame's own words -- "about two people wide" -- and a person is 0.45-0.60 m
# across the shoulders (npc/body.py's measured silhouette), so two abreast plus
# a hand's clearance either side is 1.80 m.
GALLERY_Y_M = 3.60
GALLERY_W_M = 1.80
GALLERY_T_M = 0.22          # the fascia beam's depth, and the walkway's slab
FASCIA_H_M = 0.46           # the solid beam under the rail, carrying the light

# THE RIB. `interior_kit.rib_arch`'s own defaults are depth 0.55, thickness
# 0.42 -- proportioned in INV-020 against `more hallway.jpg`. This room uses
# them unchanged; only the number of segments rises, because a 9 m span read at
# 3 m rather than at 30 m needs the arc to be smooth at the crown.
RIB_SEGMENTS = 34

# THE CENTRE-LINE LADDER. The frame shows two columns of small square cells
# side by side in a raised kerb. The kerb is INV-020's `deck_strip_w_m` (0.9 m)
# and is not restated here; what is new is the cell itself. Counted off the
# frame: the ladder's rungs are about a pace apart and each cell is roughly a
# third of the kerb's width, so 0.26 m square on a 0.62 m pitch -- the pitch
# being `rooms.DECK_TILE_M`, the deck tile this station is already laid in, so
# the ladder lands on the grid instead of beating against it.
CELL_M = 0.26
CELL_PITCH_M = _rooms.DECK_TILE_M       # 0.62
KERB_H_M = 0.085                        # a lip you do not trip over

# THE EMITTING FLOOR PANELS. "Large pale-blue emitting panels in a running-bond
# grid with dark joints." Large against a person: the frame shows roughly two
# panels between a standing figure's feet and the wall, over about 3 m, so
# 1.55 m -- and that is 2.5 deck tiles, so the field is laid as a running bond
# of 2.5 x 1.5 tiles rather than on a number of its own.
PANEL_L_M = 2.5 * _rooms.DECK_TILE_M    # 1.550
PANEL_W_M = 1.5 * _rooms.DECK_TILE_M    # 0.930
PANEL_JOINT_M = 0.055                   # the dark joint between them
PANEL_RISE_M = 0.010

# THE WALL BLADES. Vertical white light blades in chamfered dark surrounds with
# a small red indicator above. Proportioned against the figures leaning on the
# wall in the frame: the blade reaches from just above a standing head to the
# gallery fascia, so 1.90 -> 3.30 m, and it is a blade rather than a strip --
# 0.14 m wide.
BLADE_W_M = 0.14
BLADE_Y0_M = 1.90
BLADE_Y1_M = 3.30
# ONE PER RIB BAY PER SIDE, so the pitch is INV-020's 6.0 m rather than a
# number of its own -- and the first engine frame is why it is not tighter.
# At 3.0 m the exporter reported *"100.0% of the working plane inside a
# source"* and the frame came back evenly lit, which is the opposite of what
# `central corridor.webp` shows: a dim volume with pools of light and dark
# between them. Counted off the reference's right-hand wall, the blades are
# roughly one to a structural bay.
BLADE_PER_BAY = 1
SURROUND_M = 0.11           # the chamfered dark surround around the blade
INDICATOR_M = 0.075         # the small red lamp above it

# THE VENDOR FRONT. One bay of shopfront on the port side, because the frame
# shows exactly one and a concourse whose every bay is a shop is a market, not
# a spine. Counter height is `rooms.PROPS['counter']`'s, read rather than
# restated; the backlit panel field above it is proportioned off the frame at
# 4 columns of 3.
VENDOR_BAYS = 1
VENDOR_PANEL_COLS = 4
VENDOR_PANEL_ROWS = 3

# THE WAYFINDING GANTRY. PLC-056 names it as this place's T4 organ -- "live
# SYS-08/09 state: next tram, section advisories". It hangs from the ribs, so
# its height is the rib's springing geometry and not a number: `_gantry_y`
# takes it off the arch itself.
GANTRY_BOARDS = 4
GANTRY_W_M = 2.20
GANTRY_H_M = 0.85

WALL_T_M = _rooms.WALL_T_M              # 0.18, the station's own


def _p():
    """INV-020's concourse class. The only place any of it is read."""
    return kit.class_params(CLASS)


# ---------------------------------------------------------------------------
# Primitives. Closed, both ends, every time -- see `hospitality._cyl` for the
# four sessions this project spent on lathes that were open at the bottom.
# ---------------------------------------------------------------------------
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


def _cyl(v, t, g, name, cx, cz, y0, y1, r, seg=10):
    """An upright cylinder, CAPPED AT BOTH ENDS."""
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
    top = len(v)
    v.append((cx, y1, cz))
    for k in range(seg):
        t.append((top, n0 + 2 * k + 1, n0 + 2 * ((k + 1) % seg) + 1))
    bot = len(v)
    v.append((cx, y0, cz))
    for k in range(seg):
        t.append((bot, n0 + 2 * ((k + 1) % seg), n0 + 2 * k))
    g.append((name, t0, len(t)))
    return v, t, g


def _merge(v, t, g, name, mv, mt, dx=0.0, dy=0.0, dz=0.0):
    base = len(v)
    t0 = len(t)
    v.extend((x + dx, y + dy, z + dz) for x, y, z in mv)
    t.extend((a + base, b + base, c + base) for a, b, c in mt)
    g.append((name, t0, len(t)))
    return v, t, g


def _pad(v, t, g, name, loop, y0, y1):
    pv, pt = kit.deck_pad(loop, y0, y1)
    if not pt:
        return v, t, g
    return _merge(v, t, g, name, [(x, y, z) for x, y, z in pv], pt)


# ---------------------------------------------------------------------------
# The rib, closed
# ---------------------------------------------------------------------------
def _rib(v, t, g, name, width, height, z, depth=0.55, thickness=0.42,
         segments=RIB_SEGMENTS):
    """One elliptical ring frame, standing proud inside the volume.

    `interior_kit.rib_arch` is the shape and it is used unchanged -- INV-020's
    section, INV-020's proportions, one authority for what a Babylon 5 rib is.

    IT IS OPEN AT ITS TWO SPRINGINGS AND THAT IS CLOSED HERE, not in the kit.
    `rib_arch` sweeps t = 0..pi and emits no end caps, so each rib arrives with
    two open rectangular loops -- 8 open boundary edges apiece, 32 across four
    bays, on a shell `deck._selftest` asserts watertight. The kit is not this
    module's to change and the caps are this module's geometry, so they are
    built here from the same ellipse the sweep used: same `a`, `b`, same
    outward normal, same thickness. Recomputing them rather than reading them
    back off the mesh is deliberate -- the sweep's first and last quads are
    identifiable by index only until somebody changes `segments`.
    """
    rv, rt = kit.rib_arch(width, height, depth=depth, thickness=thickness,
                          segments=segments)
    _merge(v, t, g, name, rv, rt, 0.0, 0.0, z)
    a, b = width / 2.0, height
    for tt in (0.0, math.pi):
        cx, cy = -a * math.cos(tt), b * math.sin(tt)
        nx, ny = math.cos(tt) / a, math.sin(tt) / b
        n = math.hypot(nx, ny) or 1.0
        ox, oy = cx + nx / n * thickness, cy + ny / n * thickness
        # The cap is a quad in the plane of the springing. Wound so its normal
        # points AWAY from the arch -- outward at t = 0 is -x, at t = pi is +x
        # -- because `plate_solid` puts the body behind the face it is given.
        s = -1.0 if tt == 0.0 else 1.0
        loop = [(cx, cy, z - depth / 2.0), (cx, cy, z + depth / 2.0),
                (ox, oy, z + depth / 2.0), (ox, oy, z - depth / 2.0)]
        if s < 0:
            loop = loop[::-1]
        pv, pt = kit.plate_solid(loop, 0.004)
        _merge(v, t, g, name, pv, pt)
    return v, t, g


RIB_DEPTH_M = 0.55          # interior_kit.rib_arch's own, INV-020
RIB_T_M = 0.42              # ditto -- the section, not restated, just named


def _rib_span(width, height):
    """The ellipse `rib_arch` must be given so the rib stands INSIDE the room.

    `rib_arch(width, height)` puts its INNER face on that ellipse and grows
    `thickness` OUTWARD from it, so handing it the room's own 9.0 x 7.2 puts
    0.42 m of steel through both walls and through the soffit -- the bounding
    box came out 0.48 m wider than the class allows and `_selftest` caught it.
    The rib a viewer sees is proud of the wall by its own thickness, so the
    outer surface is the wall face and the inner ellipse is that less the
    section.
    """
    return width - 2.0 * RIB_T_M, height - RIB_T_M


def _gantry_y(width, height, x):
    """The height of the rib's inner face over a point on the deck.

    The wayfinding boards hang from the ribs, so their height is the ribs' and
    not a number of their own. Same half-ellipse `rib_arch` sweeps: y = b *
    sqrt(1 - (x/a)^2), on the INNER ellipse -- which is the surface a board
    actually hangs off.
    """
    aw, bh = _rib_span(width, height)
    a = aw / 2.0
    q = max(0.0, 1.0 - (x / a) ** 2)
    return bh * math.sqrt(q)


# ---------------------------------------------------------------------------
# The room
# ---------------------------------------------------------------------------
def program(place=None, bay_mult=1):
    """What KIND of concourse this is, read off the register.

    `bay_mult` IS THE FOOTPRINT. `RIB_BAYS` is 4 and the spine was therefore
    24.0 m long whatever the register said; `central_corridor` declares 120 m,
    so it was building 20% of Red Sector's circulation spine. A transit spine is
    ribs, blades, soffit rakes and vendor fronts repeated down its own length --
    every one of those loops is already driven off `bays` or off `hl` -- so a
    longer spine is MORE OF THE SAME ORGANS at their authored pitch rather than
    the same organs stretched. `bespoke.axial_units` picks the multiple and
    prices it against `budget.py`.

    THE PLACE, NOT THE MODULE. `bespoke.BESPOKE_GEOMETRY` is keyed by module
    and `interior_kit` owns two places -- this one and `standard_corridor`,
    which is the kit itself and must stay generic. Session 4h's finding was
    that several registry entries threw `q` away and drew one room for every
    place that reached them; this module takes the place and the dispatch in
    `bespoke.BESPOKE_PLACES` refuses anything it has no program for, so the
    failure mode is a stated refusal rather than the wrong room.
    """
    m = max(1, int(bay_mult))
    if place is None:
        return {"key": "reference", "bays": RIB_BAYS * m, "fn": frozenset(),
                "vendor": VENDOR_BAYS * m, "mult": m}
    fn = frozenset(place.get("functions") or ())
    return {"key": place.get("key", "reference"),
            "bays": RIB_BAYS * m,
            "mult": m,
            "fn": fn,
            # A spine that is not declared `public_social` is circulation only:
            # no shopfront, no benches. Nothing on the station is that today,
            # and the branch exists so the vendor front is a consequence of the
            # register rather than a decoration this module always draws.
            "vendor": VENDOR_BAYS * m if "public_social" in fn else 0}


def central_corridor(schema=None, profile=None, place=None, bay_mult=1):
    """The whole concourse: x across, y up, z along, deck at y = 0.

    Authored with the way IN at MAXIMUM z -- `bespoke.NEAR_END` declares
    `max_z` on that basis and `doorway_wall` cuts the aperture in that face at
    local x = 0, which is where `deck._place_local` puts the corridor's door.

    `bay_mult` grows it to its declared footprint -- see `program()`.
    """
    p = _p()
    prog = program(place, bay_mult)
    w = p["corridor_width_m"]                   # 9.0, INV-020
    h = p["ceiling_height_m"]                   # 7.2, INV-020 / INV-010
    pitch = p["rib_spacing_m"]                  # 6.0, INV-020
    strip_w = p["deck_strip_w_m"]               # 0.9, INV-020
    ln = pitch * prog["bays"]
    hw, hl = w / 2.0, ln / 2.0
    ow, ol = hw + WALL_T_M, hl + WALL_T_M
    v, t, g = [], [], []

    # --- shell -----------------------------------------------------------
    # Deck and soffit run to the OUTER wall extent. Running them to the inner
    # face leaves an open corner at every wall junction -- `hospitality.room`
    # records the render that found it.
    _box(v, t, g, "transit_deck", (-ow, -0.18, -ol), (ow, 0.0, ol))
    _box(v, t, g, "transit_soffit", (-ow, h, -ol), (ow, h + 0.18, ol))
    for s in (-1, 1):
        _box(v, t, g, "transit_wall", (s * hw, 0.0, -hl),
             (s * (hw + WALL_T_M), h, hl))
    # The far end is solid; the near end carries the doorway. Three plates
    # around the aperture, never a solid with a hole punched in it -- see
    # `bespoke.doorway_wall`.
    _box(v, t, g, "transit_wall", (-ow, 0.0, -ol), (ow, h, -hl))
    _bsp.doorway_wall(lambda n, lo, hi: _box(v, t, g, n, lo, hi),
                      "transit_wall", -ow, ow, 0.0, h, hl, ol)

    # --- articulation ----------------------------------------------------
    # `rooms.articulate` is the station's one vocabulary for a box-shaped
    # interior -- bands, deck grid, mullions, wall panels, conduit. INV-073.
    # `scale` coarsens every pitch: a 7.2 m volume given a 3 m room's 0.40 m
    # soffit bay is 44,000 triangles of ceiling nobody can resolve from the
    # deck, which is the trap `articulate`'s own docstring records for the
    # quarters unit one size down.
    _rooms.articulate(v, t, g, "transit", hw, hl, h, ow=ow, ol=ol,
                      ln=ln, nrib=prog["bays"], scale=1.6)

    _ribs(v, t, g, w, h, hl, pitch, prog["bays"])
    _soffit_rake(v, t, g, hw, hl, h, pitch, prog["bays"])
    _deck_light(v, t, g, hw, hl, strip_w)
    _wall_blades(v, t, g, hw, hl)
    _gallery(v, t, g, hw, hl, w, h)
    _fittings(v, t, g, hw, hl, h, w, prog)
    return v, t, g


def _ribs(v, t, g, w, h, hl, pitch, bays):
    """The exposed ring frames, and the diagonal bracing between them."""
    for i in range(bays + 1):
        z = -hl + pitch * i
        # THE GROUP NAME IS LOAD-BEARING TWICE OVER and neither reason is
        # cosmetic. It ends `_rib`, so `rooms.is_solid` calls it SHELL -- a rib
        # arch named as an object becomes a collision box spanning the whole
        # section, which walls the concourse a player is meant to walk down.
        # And it contains `dress_gantry`, which `materials.py` binds to
        # `steel_gantry_oxide` (albedo 0.300/0.255/0.242) -- the dark warm
        # oxide the reference calls out as "a deliberate note, not grime". The
        # archetype's own `transit_rib` is `shell_rib_painted`, a flat 0.469
        # grey, and would lose the one colour the frame insists on.
        aw, bh = _rib_span(w, h)
        _rib(v, t, g, "dress_gantry_rib", aw, bh, z,
             depth=RIB_DEPTH_M, thickness=RIB_T_M)
    # DIAGONAL BRACING in the upper volume, between consecutive ribs, port and
    # starboard alternately -- the frame shows them crossing the canted panels
    # rather than forming a regular X. Springing height is the rib's own, taken
    # off the ellipse, so a brace cannot float off its frame.
    bx = w / 2.0 * 0.72
    for i in range(bays):
        z0, z1 = -hl + pitch * i, -hl + pitch * (i + 1)
        s = 1.0 if i % 2 == 0 else -1.0
        y0 = _gantry_y(w, h, s * bx) - 0.30
        y1 = _gantry_y(w, h, -s * bx * 0.45) - 0.30
        _brace(v, t, g, "transit_rib", (s * bx, y0, z0),
               (-s * bx * 0.45, y1, z1), 0.11)


def _brace(v, t, g, name, a, b, r):
    """A square-section strut between two points. Closed, and it is a SWEEP."""
    d = [b[i] - a[i] for i in range(3)]
    ln = math.sqrt(sum(x * x for x in d)) or 1.0
    d = [x / ln for x in d]
    up = (0.0, 1.0, 0.0) if abs(d[1]) < 0.95 else (1.0, 0.0, 0.0)
    n1 = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2],
          d[0] * up[1] - d[1] * up[0])
    m = math.sqrt(sum(x * x for x in n1)) or 1.0
    n1 = [x / m for x in n1]
    n2 = (d[1] * n1[2] - d[2] * n1[1], d[2] * n1[0] - d[0] * n1[2],
          d[0] * n1[1] - d[1] * n1[0])
    ring = []
    for p in (a, b):
        ring.append([tuple(p[i] + sx * r * n1[i] + sy * r * n2[i]
                           for i in range(3))
                     for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    base = len(v)
    t0 = len(t)
    v.extend(ring[0])
    v.extend(ring[1])
    for k in range(4):
        j = (k + 1) % 4
        t += [(base + k, base + 4 + k, base + 4 + j),
              (base + k, base + 4 + j, base + j)]
    t += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    t += [(base + 4, base + 5, base + 6), (base + 4, base + 6, base + 7)]
    g.append((name, t0, len(t)))
    return v, t, g


def _soffit_rake(v, t, g, hw, hl, h, pitch, bays):
    """The raked panelled soffit: canted rows of long panels, dark joints.

    "Not open truss, and not flat" -- the frame's own words. Each rib bay
    carries a run of panels that step DOWN toward the rib on both sides, so the
    ceiling reads as trapezoidal bays running away from the eye. The step is
    what makes the dark joint visible at all; a flat field of panels at one
    height is the ceiling this room already had from `articulate`.
    """
    rows = 5
    for i in range(bays):
        z0 = -hl + pitch * i + 0.30
        z1 = -hl + pitch * (i + 1) - 0.30
        for r in range(rows):
            # Canted: the row nearest the middle of the bay hangs lowest.
            f = abs(r - (rows - 1) / 2.0) / max(1.0, (rows - 1) / 2.0)
            drop = 0.34 * (1.0 - f) + 0.06
            za = z0 + (z1 - z0) * r / rows + 0.035
            zb = z0 + (z1 - z0) * (r + 1) / rows - 0.035
            _box(v, t, g, "transit_panel",
                 (-hw + 0.22, h - drop, za), (hw - 0.22, h - drop + 0.10, zb))


def _deck_light(v, t, g, hw, hl, strip_w):
    """The centre-line ladder of paired cells, and the emitting floor field."""
    # The raised dark kerb the cells sit in. INV-020's `deck_strip_w_m`.
    _box(v, t, g, "transit_deck_joint",
         (-strip_w / 2.0, 0.0, -hl + 0.2), (strip_w / 2.0, KERB_H_M, hl - 0.2))
    n = int((2 * hl - 0.8) / CELL_PITCH_M)
    off = CELL_M * 0.62
    for i in range(n):
        z = -hl + 0.5 + (i + 0.5) * CELL_PITCH_M
        for s in (-1, 1):
            _box(v, t, g, "light_deck_channel_cell",
                 (s * off - CELL_M / 2.0, KERB_H_M, z - CELL_M / 2.0),
                 (s * off + CELL_M / 2.0, KERB_H_M + 0.014, z + CELL_M / 2.0))
    # The pale-blue emitting floor either side, in a RUNNING BOND -- alternate
    # rows offset by half a panel, which is what the frame shows and what stops
    # the field reading as graph paper.
    # A LIT LANE EITHER SIDE OF THE KERB, NOT A LIT FLOOR, and the first
    # engine frame is the reason. Laid wall to wall the field is 71% of the
    # deck and `light_deck_channel` is EMISSIVE -- which `export_scene`'s own
    # note records as the thing `room_exposure` cannot scale, because emission
    # is a material property and the room's gain touches fittings and ambient
    # only. `docs/engine-4k-concourse-normal.png` at the full width came back
    # with the deck blown to pure white and a concourse the reference frame
    # describes as *"dim, structural"* reading as a lightbox.
    #
    # The frame supports the narrower reading anyway: the pale panels run
    # either side of the centre kerb and the deck DARKENS toward the walls,
    # where the trolley and the vendor's counter stand on plain plate.
    lane0 = strip_w / 2.0 + 0.22
    # ONE COLUMN, MEASURED DOWN FROM TWO. At two columns the lit band is
    # 44% of the deck and `docs/engine-4k-concourse-half.png` came back
    # with it clipped to flat white -- no bond pattern, no joint, no
    # detail at the distance the rubric says to judge craft at. This is
    # the honest limit of what geometry can do about it: the emission is
    # a MATERIAL property and `room_exposure` scales fittings and ambient
    # only, so the lit area is the only lever this module holds. Recorded
    # as a finding rather than solved -- see the report.
    lane1 = min(hw - 0.30, lane0 + 1.0 * (PANEL_W_M + PANEL_JOINT_M))
    cols = max(1, int((lane1 - lane0) / (PANEL_W_M + PANEL_JOINT_M)))
    rows = max(1, int((2 * hl - 1.0) / (PANEL_L_M + PANEL_JOINT_M)))
    for s in (-1, 1):
        for r in range(rows):
            zc = -hl + 0.5 + (r + 0.5) * (PANEL_L_M + PANEL_JOINT_M)
            bond = 0.5 * (PANEL_W_M + PANEL_JOINT_M) if r % 2 else 0.0
            for c in range(cols):
                x0 = lane0 + bond + c * (PANEL_W_M + PANEL_JOINT_M)
                x1 = x0 + PANEL_W_M
                if x1 > lane1:
                    continue
                _pad(v, t, g, "light_deck_channel_field",
                     [(s * x0, zc - PANEL_L_M / 2.0),
                      (s * x1, zc - PANEL_L_M / 2.0),
                      (s * x1, zc + PANEL_L_M / 2.0),
                      (s * x0, zc + PANEL_L_M / 2.0)],
                     0.0, PANEL_RISE_M)


def _wall_blades(v, t, g, hw, hl):
    """Vertical white light blades in chamfered dark surrounds, red lamp above.

    `light_wall_strip_bank` is in `export_scene.FIXTURE_LIGHTING`, so these are
    the fittings that actually CAST in this room -- which is right: the frame's
    key light is on the walls, and the deck panels and the centre ladder glow
    without lighting anything. `light_deck_channel` and `light_indicator_red`
    are deliberately absent from that table and stay emissive-only, so a 260-cell
    ladder does not become 260 lights.
    """
    n = max(2, int(round(2 * hl / _p()["rib_spacing_m"])) * BLADE_PER_BAY)
    for s in (-1, 1):
        for i in range(n):
            z = -hl + 0.8 + (i + 0.5) * (2 * hl - 1.6) / n
            xf = s * hw
            _box(v, t, g, "transit_panel",
                 (min(xf, xf - s * 0.05), BLADE_Y0_M - SURROUND_M,
                  z - BLADE_W_M / 2.0 - SURROUND_M),
                 (max(xf, xf - s * 0.05), BLADE_Y1_M + SURROUND_M,
                  z + BLADE_W_M / 2.0 + SURROUND_M))
            _box(v, t, g, "light_wall_strip_bank",
                 (min(xf - s * 0.05, xf - s * 0.10), BLADE_Y0_M,
                  z - BLADE_W_M / 2.0),
                 (max(xf - s * 0.05, xf - s * 0.10), BLADE_Y1_M,
                  z + BLADE_W_M / 2.0))
            _box(v, t, g, "light_indicator_red",
                 (min(xf - s * 0.02, xf - s * 0.07),
                  BLADE_Y1_M + SURROUND_M + 0.10, z - INDICATOR_M / 2.0),
                 (max(xf - s * 0.02, xf - s * 0.07),
                  BLADE_Y1_M + SURROUND_M + 0.10 + INDICATOR_M,
                  z + INDICATOR_M / 2.0))


def _gallery(v, t, g, hw, hl, w, h):
    """The upper walkway: slab, fascia beam with its light line, and the rail.

    ONE SIDE ONLY. The frame shows a catwalk crossing above the lower deck with
    open volume beyond it, not a pair of balconies; and a gallery down both
    walls of a 9 m spine would leave a 5.4 m slot, which is a light well rather
    than a concourse. The declared `gallery_rail` interactable lives on it.
    """
    x0 = -hw + 0.02
    x1 = x0 + GALLERY_W_M
    z0, z1 = -hl + 0.6, hl - 0.6
    _box(v, t, g, "transit_deck", (x0, GALLERY_Y_M - GALLERY_T_M, z0),
         (x1, GALLERY_Y_M, z1))
    # The solid fascia beam under the outer edge, and the light line along it.
    _box(v, t, g, "transit_panel",
         (x1 - 0.12, GALLERY_Y_M - GALLERY_T_M - FASCIA_H_M, z0),
         (x1, GALLERY_Y_M - GALLERY_T_M, z1))
    _box(v, t, g, "light_deck_channel_fascia",
         (x1 - 0.135, GALLERY_Y_M - GALLERY_T_M - 0.12, z0 + 0.05),
         (x1 - 0.115, GALLERY_Y_M - GALLERY_T_M - 0.04, z1 - 0.05))
    # THE DECLARED INTERACTABLE. `directory.py` lists `gallery_rail` for this
    # place; `interact.resolve` reads emitted span names, so the rail is built
    # under the name the register uses and `bespoke.compose` does not stand a
    # second one next to it.
    rv, rt = kit.handrail(z1 - z0, height=1.05, post_spacing=1.6)
    # `handrail` runs along +x; this rail runs along +z, so it is turned a
    # quarter turn about the vertical -- (x, y, z) -> (-z, y, x), determinant
    # +1, winding untouched. Mirroring one axis would face every triangle
    # inward, which no render against black and no triangle count can see.
    _merge(v, t, g, "prop_gallery_rail",
           [(-z, y, x) for x, y, z in rv], rt,
           dx=x1 - 0.06, dy=GALLERY_Y_M, dz=z0)
    # The stair up, at the far end, treads on a stringer.
    steps = 10
    rise = GALLERY_Y_M / steps
    for i in range(steps):
        zc = -hl + 0.9 + i * 0.30
        _box(v, t, g, "transit_deck",
             (x0, rise * i, zc), (x1, rise * (i + 1), zc + 0.30))
        _box(v, t, g, "fix_platform_edge",
             (x0, rise * (i + 1) - 0.03, zc + 0.24),
             (x1, rise * (i + 1) + 0.012, zc + 0.30))


def _fittings(v, t, g, hw, hl, h, w, prog):
    """What the register says a player can use here, and what the frame shows.

    The register declares `babcom_terminal`, `gallery_rail` and `door`;
    PLC-056 adds the wayfinding gantry boards as this place's T4 organ. The
    rail is built in `_gallery`; the rest is here.
    """
    # BABCOM x4 PER 24 m OF SPINE (PLC-056's count is 4 over the authored four
    # rib bays), on the starboard wall between the blades. Scaled with the
    # length rather than spread over it: four terminals down 120 m of concourse
    # is one every 30 m, which is not a public comms wall, it is decoration.
    mult = max(1, int(prog.get("mult", 1)))
    n_bab = 4 * mult
    for i in range(n_bab):
        z = -hl + 1.6 + i * (2 * hl - 3.2) / max(1, n_bab - 1)
        _box(v, t, g, "prop_babcom_terminal",
             (hw - 0.26, 0.95, z - 0.34), (hw - 0.04, 1.78, z + 0.34))
        _box(v, t, g, "signage_panel",
             (hw - 0.28, 1.06, z - 0.28), (hw - 0.26, 1.66, z + 0.28))

    # THE DOORS a side wall opens into. The register declares `door`; the frame
    # shows the concourse's flanks pierced at intervals.
    # A QUARTER TURN, NOT A MIRROR, and a different one per side. `door_frame`
    # is authored across +x with its reveal running -0.27..+0.22 in z; both
    # walls want the deep side of that reveal against the wall face, so the
    # starboard door turns (x, y, z) -> (-z, y, x) and the port door turns it
    # the other way, (x, y, z) -> (z, y, -x). Both matrices have determinant +1
    # and neither touches the winding. Mirroring one axis instead would face
    # every triangle into the wall -- invisible in a triangle count, in an
    # extent, and in a render against black.
    reveal = 0.27
    n_door = 2 * mult
    for s in (-1, 1):
        for i in range(n_door):
            z = -hl + 4.0 + i * (2 * hl - 8.0) / max(1, n_door - 1)
            fv, ft = kit.door_frame()
            turned = ([(-z2, y, x2) for x2, y, z2 in fv] if s > 0
                      else [(z2, y, -x2) for x2, y, z2 in fv])
            _merge(v, t, g, "prop_door", turned,
                   ft, dx=s * (hw - reveal), dz=z)

    # THE WAYFINDING GANTRY BOARDS, hung from the ribs. Height off the arch.
    n_board = GANTRY_BOARDS * mult
    for i in range(n_board):
        z = -hl + 2.2 + i * (2 * hl - 4.4) / max(1, n_board - 1)
        y = _gantry_y(w, h, GANTRY_W_M / 2.0) - 0.42
        # A SURROUND, NOT A SLAB BEHIND THE FACE. The first frame showed the
        # boards as pale blank panels: the frame box was 0.14 m deep and
        # 0.10 m bigger than the face on every edge, so at 12 m it read as the
        # sign and the dark blue face read as a hole in it. Four bars.
        for lo, hi in (((-GANTRY_W_M / 2.0 - 0.05, y - 0.05),
                        (GANTRY_W_M / 2.0 + 0.05, y + 0.05)),
                       ((-GANTRY_W_M / 2.0 - 0.05, y - GANTRY_H_M - 0.05),
                        (GANTRY_W_M / 2.0 + 0.05, y - GANTRY_H_M + 0.05)),
                       ((-GANTRY_W_M / 2.0 - 0.05, y - GANTRY_H_M - 0.05),
                        (-GANTRY_W_M / 2.0 + 0.03, y + 0.05)),
                       ((GANTRY_W_M / 2.0 - 0.03, y - GANTRY_H_M - 0.05),
                        (GANTRY_W_M / 2.0 + 0.05, y + 0.05))):
            _box(v, t, g, "sign_frame", (lo[0], lo[1], z - 0.07),
                 (hi[0], hi[1], z + 0.07))
        _box(v, t, g, "sign_face",
             (-GANTRY_W_M / 2.0, y - GANTRY_H_M, z - 0.075),
             (GANTRY_W_M / 2.0, y, z - 0.055))
        _box(v, t, g, "sign_face",
             (-GANTRY_W_M / 2.0, y - GANTRY_H_M, z + 0.055),
             (GANTRY_W_M / 2.0, y, z + 0.075))
        # THE LIVE LINES. PLC-056 makes these boards its T4 organ -- *"live
        # SYS-08/09 state: next tram, section advisories"* -- so the face
        # carries rows of legible bars rather than being a lit rectangle.
        for r in range(3):
            for c in range(4):
                for zf in (z - 0.078, z + 0.076):
                    _box(v, t, g, "sign_text",
                         (-GANTRY_W_M / 2.0 + 0.14 + c * 0.46,
                          y - GANTRY_H_M + 0.12 + r * 0.24, zf - 0.004),
                         (-GANTRY_W_M / 2.0 + 0.14 + c * 0.46
                          + (0.30 if c % 2 else 0.20),
                          y - GANTRY_H_M + 0.26 + r * 0.24, zf + 0.004))
        for s in (-1, 1):
            _cyl(v, t, g, "transit_rib", s * (GANTRY_W_M / 2.0 - 0.15), z,
                 y + 0.05, _gantry_y(w, h, s * (GANTRY_W_M / 2.0 - 0.15)),
                 0.035, seg=6)

    # BENCHES and PLANTERS -- a public spine, not a service way. PLC-056 calls
    # it "the crowd's main stage".
    for i in range(3):
        z = -hl + 3.2 + i * (2 * hl - 6.4) / 2.0
        _box(v, t, g, "prop_bench",
             (hw - 1.10, 0.40, z - 0.85), (hw - 0.62, 0.46, z + 0.85))
        for s2 in (-1, 1):
            _box(v, t, g, "prop_bench",
                 (hw - 1.06, 0.0, z + s2 * 0.70), (hw - 0.66, 0.40,
                                                   z + s2 * 0.78))
        _cyl(v, t, g, "prop_planter", hw - 1.55, z + 1.6, 0.0, 0.52, 0.40,
             seg=10)

    # THE VENDOR FRONT. Backlit orange-red panels behind vertical mullions over
    # a counter, port side, one bay.
    if prog["vendor"]:
        z0 = -hl + 1.4
        z1 = z0 + 5.0
        _box(v, t, g, "prop_counter",
             (-hw + GALLERY_W_M + 0.10, 0.0, z0),
             (-hw + GALLERY_W_M + 0.80, 1.02, z1))
        _box(v, t, g, "prop_shopfront",
             (-hw + 0.02, 1.02, z0 - 0.12), (-hw + 0.16, 3.10, z1 + 0.12))
        cw = (z1 - z0) / VENDOR_PANEL_COLS
        ch = (3.10 - 1.30) / VENDOR_PANEL_ROWS
        for c in range(VENDOR_PANEL_COLS):
            for r in range(VENDOR_PANEL_ROWS):
                _box(v, t, g, "light_bar_backlight",
                     (-hw + 0.16, 1.30 + r * ch + 0.05,
                      z0 + c * cw + 0.07),
                     (-hw + 0.19, 1.30 + (r + 1) * ch - 0.05,
                      z0 + (c + 1) * cw - 0.07))
            _box(v, t, g, "transit_mullion",
                 (-hw + 0.16, 1.10, z0 + c * cw - 0.03),
                 (-hw + 0.24, 3.10, z0 + c * cw + 0.03))

    # THE TROLLEY. "A small wheeled trolley with a magenta-lit top... a good
    # prop for street-level life" -- 00-INDEX's own note about this frame.
    tz = hl - 5.0
    _box(v, t, g, "prop_container", (-0.95, 0.24, tz - 0.62),
         (-0.28, 0.86, tz + 0.62))
    _box(v, t, g, "light_bar_backlight", (-0.92, 0.86, tz - 0.58),
         (-0.31, 0.90, tz + 0.58))
    for sx in (-0.88, -0.35):
        for sz in (tz - 0.52, tz + 0.52):
            _cyl(v, t, g, "prop_container", sx, sz, 0.0, 0.24, 0.085, seg=8)

    # THE CIRCULAR DOWNLIGHT POOLS. INV-020 names them as part of the concourse
    # class -- *"a lit strip down the deck centre, circular downlight pools,
    # wall screens"* -- and they carry the ONE absolute length these frames
    # yield: an EarthForce officer standing in one in `more hallway.jpg` puts
    # them at `interior_kit.DOWNLIGHT_POOL_M` = 1.57 m across. Read, not
    # restated, and `interior_kit._selftest` asserts the built geometry still
    # matches it.
    pools = max(2, int((2 * hl - 2.0) / 4.2))
    for i in range(pools):
        z = -hl + 1.4 + (i + 0.5) * (2 * hl - 2.8) / pools
        for s in (-1, 1):
            pv, pt = kit.downlight_pool()
            _merge(v, t, g, "light_deck_channel_pool",
                   [(x, y, z2) for x, y, z2 in pv], pt,
                   dx=s * (hw - 1.95), dz=z)

    # THE SERVICE RUN under the gallery, which is what an unclad outer-ring
    # deck looks like from below: pipe runs on saddles between the ribs. The
    # Central Corridor is outermost-ring construction by LOCATIONS' own
    # reasoning -- *"only the outermost deck sits against the hull ribs"* --
    # so its services are visible rather than boxed in.
    gx = -hw + 0.02 + GALLERY_W_M
    for k in range(3):
        y = GALLERY_Y_M - GALLERY_T_M - FASCIA_H_M - 0.22 - k * 0.19
        _brace(v, t, g, "transit_conduit",
               (gx - 0.30 - k * 0.16, y, -hl + 0.5),
               (gx - 0.30 - k * 0.16, y, hl - 0.5), 0.055)
    for i in range(int((2 * hl - 1.0) / 2.4)):
        z = -hl + 1.0 + i * 2.4
        _box(v, t, g, "transit_rib", (gx - 0.72, GALLERY_Y_M - GALLERY_T_M
                                      - FASCIA_H_M - 0.34, z - 0.05),
             (gx - 0.20, GALLERY_Y_M - GALLERY_T_M - FASCIA_H_M - 0.14,
              z + 0.05))

    # PARCEL LOCKERS AND BINS -- the fabric of a public spine. `prop_parcel_locker`
    # and `prop_container` are names `materials.py` already binds, and a bank of
    # lockers is how a station gives 250,000 residents somewhere to collect a
    # package without a shopfront.
    for i in range(2):
        z0 = -hl + 6.2 + i * 8.4
        for c in range(5):
            for r in range(3):
                _box(v, t, g, "prop_parcel_locker",
                     (hw - 0.62, 0.34 + r * 0.52, z0 + c * 0.46),
                     (hw - 0.06, 0.34 + (r + 1) * 0.52 - 0.035,
                      z0 + (c + 1) * 0.46 - 0.035))
        _box(v, t, g, "prop_parcel_locker", (hw - 0.66, 0.0, z0 - 0.04),
             (hw - 0.02, 0.34, z0 + 5 * 0.46))
    for i in range(3):
        z = -hl + 4.4 + i * 6.6
        _cyl(v, t, g, "prop_container", -hw + GALLERY_W_M + 0.55, z,
             0.0, 0.88, 0.29, seg=10)
        _cyl(v, t, g, "transit_rib", -hw + GALLERY_W_M + 0.55, z,
             0.88, 0.94, 0.31, seg=10)

    # THE QUEUE STANCHIONS at the babcom bank. A public terminal on a station
    # of a quarter of a million people has a line at it, and the line has to be
    # somewhere before anybody stands in it.
    for i in range(6):
        z = -hl + 1.9 + i * 1.35
        _cyl(v, t, g, "prop_bollard", hw - 1.55, z, 0.0, 0.98, 0.055, seg=8)
        _cyl(v, t, g, "prop_bollard", hw - 1.55, z, 0.0, 0.06, 0.16, seg=10)
        if i:
            _brace(v, t, g, "prop_bollard",
                   (hw - 1.55, 0.90, z - 1.35), (hw - 1.55, 0.90, z), 0.016)

    # FREIGHT ON THE DECK. The frame's trolley is not alone: a spine is how
    # cargo crosses a sector, and STATE's own scope note calls for the physical
    # plant to be visible rather than implied.
    for i, (px, pz, n) in enumerate(((-2.35, -hl + 9.1, 3),
                                     (2.55, hl - 9.6, 2))):
        for k in range(n):
            _box(v, t, g, "prop_container",
                 (px - 0.58, 0.10 + k * 0.62, pz - 0.44),
                 (px + 0.58, 0.10 + (k + 1) * 0.62 - 0.06, pz + 0.44))
        _box(v, t, g, "fix_platform_edge", (px - 0.62, 0.0, pz - 0.48),
             (px + 0.62, 0.10, pz + 0.48))

    # DIRECTIONAL SIGNS on the ribs' inner faces, between the gantry boards.
    for i in range(3):
        z = -hl + 6.0 + i * 6.0
        for s in (-1, 1):
            x = s * (w / 2.0 * 0.60)
            y = _gantry_y(w, h, x) - 0.34
            _box(v, t, g, "sign_post", (x - 0.045, y - 0.30, z - 0.045),
                 (x + 0.045, y, z + 0.045))
            # A DARK FACE CARRYING PALE BARS, not a blank pale slab. The first
            # frame showed these as featureless light rectangles at 12 m --
            # `docs/AAA-STANDARD.md`'s own C1, *"a box primitive standing in
            # for a named object"*, and the object here is a legible sign.
            _box(v, t, g, "sign_face", (x - 0.62, y - 0.72, z - 0.035),
                 (x + 0.62, y - 0.30, z + 0.035))
            for k in range(3):
                _box(v, t, g, "sign_text",
                     (x - 0.54 + k * 0.36, y - 0.64, z - 0.045),
                     (x - 0.28 + k * 0.36, y - 0.38, z - 0.036))
                _box(v, t, g, "sign_text",
                     (x - 0.54 + k * 0.36, y - 0.64, z + 0.036),
                     (x - 0.28 + k * 0.36, y - 0.38, z + 0.045))


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}  -- {detail}")

    import directory as dr
    import interior as it
    schema, profile = it.load()
    q = dr.by_key("central_corridor")
    v, t, g = central_corridor(schema, profile, q)
    p = _p()

    check("nothing is restated from INV-020",
          abs(max(x for x, _y, _z in v) - min(x for x, _y, _z in v)
              - (p["corridor_width_m"] + 2 * WALL_T_M)) < 1e-9,
          "the built width is not the class's")
    check("the volume is a whole number of INV-010 deck pitches",
          abs(p["ceiling_height_m"] / 3.6
              - round(p["ceiling_height_m"] / 3.6)) < 1e-9)
    check("the gallery is exactly one deck pitch up",
          abs(GALLERY_Y_M - 3.6) < 1e-9)

    # CLOSURE. A composed shell's open edges become the DECK's open edges and
    # `deck._selftest` asserts watertightness. `interior_kit.rib_arch` arrives
    # open at both springings; `_rib` closes it, and the control below is the
    # measurement that proves the caps are what does it.
    op, non = kit.boundary_edges(v, t)
    check("the concourse is a closed surface", not op,
          f"{len(op)} open boundary edges")
    print(f"  closure: {len(op)} open, {len(non)} non-manifold edges")

    # NEGATIVE CONTROL -- take the springing caps away and the shell must leak.
    # Without it this gate is measuring a case with no defect in it, which is
    # the failure mode `interior_kit`'s tag-coverage assertion had for four
    # sessions (it ran on a corridor with no doors).
    real_plate = kit.plate_solid
    try:
        kit.plate_solid = lambda loop, thick: ([], [])
        cv, ct, _cg = central_corridor(schema, profile, q)
        cop, _ = kit.boundary_edges(cv, ct)
        check("...and with the rib caps removed it does NOT",
              len(cop) > 0,
              "a concourse with uncapped ribs still measures watertight -- "
              "the caps are not what is closing it")
        print(f"  control: uncapped ribs leak {len(cop)} edges")
    finally:
        kit.plate_solid = real_plate

    # THE WAY IN. `bespoke.near_face_opening` is the same measurement
    # `deck._mouth_clear` applies, so this asks the assembler's own question in
    # the module that builds the thing.
    op2 = _bsp.near_face_opening(v, t)
    check("a body can walk in at local x = 0",
          op2 is not None and abs(op2[0]) < 0.35
          and op2[1] >= kit.PROVISIONAL["door_width_m"],
          f"{op2}")

    # THE DECLARED INTERACTABLES, asked of the emitted mesh.
    import interact as ia
    want = tuple(q.get("interacts") or ())
    got = ia.resolve(want, {n for n, _a, _b in g}, g)
    check("every interactable the register declares is built here",
          set(got) == set(want), f"missing {sorted(set(want) - set(got))}")

    # NOTHING MAY BE SOLID THAT SPANS THE ROOM. A rib named as an object
    # becomes a collision box across the whole section and walls the spine --
    # the reason the ribs end in `_rib`.
    import collision as col
    boxes = col.prop_boxes(v, t, g)
    wide = [b for b in boxes
            if (b[3] - b[0]) > p["corridor_width_m"] * 0.8]
    check("no collision box spans the concourse", not wide,
          f"{len(wide)} boxes wider than 80% of the section")

    # THE CAP, SAID OUT LOUD. PLC-056's tiling target is 540 bays; this builds
    # four rib bays. The ratio is printed so nobody reads the room as the place.
    ln = p["rib_spacing_m"] * RIB_BAYS
    print(f"  built {ln:.1f} m of a 120 m location -- {ln / 120.0 * 100:.1f}% "
          f"of its axial extent, 4 rib bays against PLC-056's 540")
    print(f"  {len(t):,} triangles, {len(g)} groups")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
