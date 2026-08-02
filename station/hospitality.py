"""The bar/diner -- the station's most common workplace, and its darkest room.

`npc/schedule.py` makes **hospitality the largest single workplace on the
station**: 734 of 3,000 sampled residents work in it, ahead of the concourse
(556) and the Zocalo (488). Until now it had no geometry at all. Every one of
those NPCs was clocking on to nowhere.

It is also the best *small enclosed interior* the reference set holds, and it is
utterly unlike the Zocalo. The Zocalo is a two-storey public concourse under
arch ribs. This is a low, dark, tight room that is **lit entirely by pendant
cones over the tables**, so the space reads as a field of separate pools of
light with near-zero ambient between them. Building the station's social life
out of concourse alone would have made it one note.

SOURCE
------
`reference/04-sector-red/Doug's Dugout.webp`, authority 1. (The uploader's
caption is **not** a canon name -- `LOCATIONS.md` §218 records it as an unnamed
bar and says to treat the name as unsourced, so this module never uses it.)

It establishes:

  * **Low pendant cone lamps, one over each table** -- large shallow
    polished-metal shades on slim stems, hung LOW, bright rim, hot pool
    beneath. Ambient fill is near zero. This is the room's whole lighting
    design and the single most transferable thing in the frame.
  * **A cyan neon glyph** in the curvilinear alien script family, upper left,
    beside a **vertical cyan neon tube in four segments split by three clamp
    bands**.
  * **A large orange-red backlit matrix of small square cells**, ~12 across, in
    a stepped irregular silhouette.
  * **A correctly laid out standard 20-segment dartboard** -- the numerals were
    verified against the real sequence, and this module reproduces that
    sequence rather than a plausible-looking ring. A wrong dartboard is the
    kind of detail that breaks the room for anyone who has played.
  * **An amber alphanumeric display reading "209"**.
  * Tables with a species-mixed clientele; a bar counter at the right.
  * **Ordinary human pub fittings persist on the station**, which is a
    characterisation point: Babylon 5 has darts and burgers, not only
    diplomacy.

WHAT IS DELIBERATELY NOT REPRODUCED
-----------------------------------
The frame contains a lit **ZIMA** panel. That is real 1990s product placement
in the original broadcast, and it is recorded in the reference index **as
observed** while being excluded from everything this project builds. It is a
real-world trademark and reproducing it would be passing off a brand into a fan
reconstruction. `_selftest` asserts the string appears nowhere in this module,
because "I remembered not to" is not a guarantee and the next session will not
have seen the frame.

WHAT IS EXTRAPOLATED -- INV-033
-------------------------------
Every dimension. The frame gives proportions against seated diners, not metres.
Scale is taken from a seated head (~0.23 m chin to crown at ~120 px), which
puts the pendant shades at roughly 0.6 m across, and everything else is
proportioned from the table height a person eats at.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "npc"))

import interior as it
import rooms as _rooms                                          # noqa: E402
import interior_kit as kit                                     # noqa: E402
import bespoke as _bsp                                         # noqa: E402

# ---------------------------------------------------------------------------
# The room. Small and low -- that is the point of it.
# ---------------------------------------------------------------------------
ROOM_L_M = 11.5
ROOM_W_M = 8.0
ROOM_H_M = 2.9             # low. The Zocalo's concourse is 7.2 m.
WALL_T_M = 0.16

# Tables and seating.
TABLE_R_M = 0.62
TABLE_H_M = 0.74
TABLE_SEG = 12
TABLE_TOP_M = 0.06
STOOL_R_M = 0.19
STOOL_H_M = 0.62
STOOLS_PER_TABLE = 4
TABLES_X = 3
TABLES_Z = 3

# The pendant cones. THE defining feature: one per table, hung low, shallow
# shade, so each table is its own pool of light.
SHADE_R_M = 0.32           # ~0.64 m across
SHADE_DROP_M = 0.16        # shallow -- a cone, not a dome
SHADE_T_M = 0.012          # the shade's own material thickness -- INV-171
STEM_R_M = 0.022
PENDANT_H_M = 1.62         # underside of the shade above the deck
LAMP_R_M = 0.10            # the bright rim inside the shade

# The bar counter.
BAR_L_M = 6.0
BAR_D_M = 0.72
BAR_H_M = 1.08
BAR_FOOT_M = 0.18          # foot rail
BACKBAR_H_M = 2.15

# Wall fittings, all from the frame.
NEON_TUBE_SEGS = 4         # the vertical cyan tube...
NEON_CLAMPS = 3            # ...split by three clamp bands
NEON_TUBE_H_M = 1.45
NEON_TUBE_R_M = 0.035
NEON_GLYPH_W_M = 0.85
NEON_GLYPH_H_M = 0.70

MATRIX_CELLS_X = 12        # the orange-red backlit cell matrix
MATRIX_CELLS_Y = 7
MATRIX_CELL_M = 0.085
MATRIX_GAP_M = 0.025

# Non-manifold edges this module does NOT own. `rooms.articulate` lays the
# dado, rail, skirt and cornice bands as proud plates whose edges coincide with
# the wall behind them, and `rooms.py` is not this module's to edit -- so the
# assertion is against the measured inherited count, exactly as `zocalo._selftest`
# does for `interior_kit.wall_assembly`. It still fails the moment this file
# introduces one of its own.
#
# 58 -> 54 in session 4h, and the number was CHECKED rather than relaxed: the
# selftest failed identically before and after this module was touched (29/30,
# 5,852 triangles both ways), and `rooms.py` changed by 854 lines in c4f989b
# when the V1 pass reworked `articulate`. So four of the inherited edges went
# away because the module that owns them improved.
#
# It stays an EXACT equality. A drop means rooms.py got better and the constant
# is stale; a RISE means either rooms.py regressed or this file introduced an
# edge of its own, and that second case is the one this assertion exists for.
_INHERITED_NON_MANIFOLD = 54

# Booths -- the `rumour` fitting. A snug is a bench with a high back, which is
# what makes it a place you can talk in; the height is the one thing that has to
# be right or it is just a sofa. INV-265.
BOOTHS = 4
BOOTH_L_M = 1.65           # two people a side
BOOTH_D_M = 0.62
BOOTH_SEAT_M = 0.46
BOOTH_BACK_M = 1.42        # above a seated head, which is the whole point

# The `black_market_fringe` fitting: a closed roller shutter behind the bar.
SHUTTER_W_M = 1.30
SHUTTER_H_M = 2.05
SHUTTER_SLATS = 14

DART_R_M = 0.2255          # a regulation board is 451 mm across
DART_T_M = 0.038           # and 38 mm deep -- INV-171
DART_SEGS = 20
DART_RING_R = (0.0159, 0.0318, 0.1070, 0.1150, 0.1620, 0.1700)  # regulation
DISPLAY_W_M = 0.42         # the amber alphanumeric reading 209
DISPLAY_H_M = 0.16

# The amber display's content, carried as data for the same reason
# `signage.BOARDS` is: what a screen says is a fact about the room.
DISPLAY_TEXT = "209"

# A regulation dartboard's number sequence, clockwise from the top. This is a
# real-world fact, not Babylon 5 canon, and the frame verifies the prop uses
# the correct one -- so a plausible-looking ring of numbers would be wrong in a
# way a player can catch.
DART_SEQUENCE = (20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
                 3, 19, 7, 16, 8, 11, 14, 9, 12, 5)


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


def _cyl(v, t, g, name, cx, cz, y0, y1, r, seg=TABLE_SEG):
    """An upright cylinder, CAPPED AT BOTH ENDS.

    IT USED TO BE CAPPED AT THE TOP ONLY, and two call sites passed
    `cap=False` and got no caps at all. That is `dressing._cyl`'s defect --
    fixed there in session 3x -- alive in a second copy in this file, and it
    was the single biggest hole in the bar: 288 open boundary edges under 36
    stools, 108 round the tables, 72 under the table stems, 108 on the pendant
    stems and 48 on the neon tube. 624 of the room's 824, all of them the same
    missing six triangles an end.

    THE `cap=False` CALLERS WERE THE WORST OF IT and the reasoning that
    produced them is worth recording, because it is plausible and wrong: a
    pendant stem runs INTO the ceiling and a neon tube segment butts against
    the next one, so an end cap there is never seen. True -- and a cap you
    cannot see costs six triangles, while a hole you cannot see is still a
    hole in the deck this room is composed onto, and the deck asserts
    watertightness. Closure is not a visibility argument.
    """
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


def pendant(v, t, g, cx, cz):
    """One pendant cone over a table: stem, shallow shade, bright rim.

    The shade is emitted as its own group so the material pass can make it the
    ONLY emissive surface in the room. In the frame ambient fill is effectively
    zero and every lit thing is either a lamp or something a lamp is hitting.
    """
    y = PENDANT_H_M
    _cyl(v, t, g, "bar_pendant_stem", cx, cz, y + SHADE_DROP_M, ROOM_H_M,
         STEM_R_M, seg=6)
    # Shallow cone: a ring at the rim, apex above -- and it is a SHELL, with
    # an inner cone and a rim band, because a shade is a thing with a
    # thickness. As a single cone it was open all the way round its rim, 12
    # edges a pendant, and the underside -- the surface the lamp actually
    # bounces off and the only part of the shade a seated drinker sees -- did
    # not exist at all. Capping the rim instead would have closed it and put a
    # lid on the lamp.
    n0 = len(v)
    ri = SHADE_R_M - SHADE_T_M
    for k in range(TABLE_SEG):
        a = math.tau * k / TABLE_SEG
        ca, sa = math.cos(a), math.sin(a)
        v.append((cx + SHADE_R_M * ca, y, cz + SHADE_R_M * sa))
        v.append((cx + ri * ca, y + SHADE_DROP_M * SHADE_T_M / SHADE_R_M,
                  cz + ri * sa))
    apex_o = len(v)
    v.append((cx, y + SHADE_DROP_M, cz))
    apex_i = len(v)
    v.append((cx, y + SHADE_DROP_M - SHADE_T_M, cz))
    t0 = len(t)
    for k in range(TABLE_SEG):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % TABLE_SEG)
        t.append((apex_o, b0, a0))                       # the outside, upward
        t.append((apex_i, a0 + 1, b0 + 1))               # the underside, lit
        t.append((a0, b0, b0 + 1))                       # the rim band
        t.append((a0, b0 + 1, a0 + 1))
    g.append(("bar_pendant_shade", t0, len(t)))
    # The bright rim inside the shade -- the actual source.
    _cyl(v, t, g, "bar_pendant_lamp", cx, cz, y + 0.01, y + 0.05, LAMP_R_M,
         seg=8)
    return v, t, g


def dartboard(v, t, g, cx, cy, z):
    """A regulation 20-segment board on the back wall.

    Built with the real clockwise sequence, and the sequence is asserted rather
    than assumed -- see DART_SEQUENCE.
    """
    n0 = len(v)
    # A board is 38 mm of sisal on a backing plate, and it hangs on a wall a
    # player walks past 0.6 m from -- so it gets a rim and a back. As a bare
    # fan it was 20 open edges at exactly the distance the rubric calls half
    # distance, and you could see the wall through the edge of it.
    for zz in (z, z + DART_T_M):
        v.append((cx, cy, zz))
        for k in range(DART_SEGS):
            a = math.tau * (k - 0.5) / DART_SEGS + math.tau / 4
            v.append((cx + DART_R_M * math.cos(a),
                      cy + DART_R_M * math.sin(a), zz))
    t0 = len(t)
    back = n0 + DART_SEGS + 1
    for k in range(DART_SEGS):
        k2 = (k + 1) % DART_SEGS
        t.append((n0, n0 + 1 + k, n0 + 1 + k2))            # the playing face
        t.append((back, back + 1 + k2, back + 1 + k))      # against the wall
        t.append((n0 + 1 + k, back + 1 + k, back + 1 + k2))
        t.append((n0 + 1 + k, back + 1 + k2, n0 + 1 + k2))
    g.append(("bar_dartboard", t0, len(t)))
    return v, t, g


def bar_program(place=None):
    """What KIND of bar this is, read off the register rather than chosen.

    THE FIVE BARS WERE ONE ROOM. `room()` took no arguments, so `bespoke`'s
    entry -- `lambda s, p, q: hospitality.room()` -- drew the same geometry for
    `bar_unnamed`, `eclipse_cafe`, `earharts`, `fresh_air` and `happy_daze`.
    They rendered byte-identically and `deck.py --degeneracy` now fails on it.

    Nothing here is invented. The register already distinguishes them and
    nobody was reading it:

        bar_unnamed   18.7 x 14.3 m   hospitality food_service recreation rumour
        eclipse_cafe  18.7 x 14.3 m   hospitality food_service
        earharts      12.3 x 16.0 m   hospitality food_service recreation
        fresh_air     12.3 x 16.0 m   hospitality food_service
        happy_daze    11.8 x 14.0 m   hospitality recreation black_market_fringe

    So the footprint comes from `rooms.bay_span_m` and the fittings come from
    the declared functions -- which is the V-track's rule, form follows
    function, applied to the module that had the worst case of not doing it.
    `place=None` keeps the module's own constants so the self-test and any
    caller without a register entry still build the reference bar.
    """
    if place is None:
        return {"w": ROOM_W_M, "l": ROOM_L_M, "fn": frozenset(),
                "key": "reference"}
    w, l = _rooms.bay_span_m(place)
    return {"w": float(w), "l": float(l),
            "fn": frozenset(place.get("functions") or ()),
            "key": place.get("key", "reference")}


def room(place=None):
    """The whole bar, authored with x across, y up, z along.

    `place` is a register row. See `bar_program` for what it changes and why.
    """
    prog = bar_program(place)
    room_w, room_l = prog["w"], prog["l"]
    fn = prog["fn"]
    v, t, g = [], [], []
    hw, hl = room_w / 2.0, room_l / 2.0

    # Deck and soffit run to the OUTER wall extent, not the inner face.
    #
    # First version spanned only -hw..hw while the walls sit outboard of that,
    # which left an open corner at every wall/soffit junction. The render
    # showed a magenta speck where the ceiling met the far wall -- a hole a few
    # pixels across, and the only reason it was visible at all is that this
    # project renders interiors against a colour that cannot occur in the
    # model. Against black it would have been a shadow.
    ow = hw + WALL_T_M
    ol = hl + WALL_T_M
    _box(v, t, g, "bar_deck", (-ow, -0.14, -ol), (ow, 0.0, ol))
    _box(v, t, g, "bar_soffit", (-ow, ROOM_H_M, -ol),
         (ow, ROOM_H_M + 0.14, ol))
    for s in (-1, 1):
        _box(v, t, g, "bar_wall", (s * hw, 0.0, -hl),
             (s * (hw + WALL_T_M), ROOM_H_M, hl))
        if s > 0:
            # THE BAR HAD NO DOOR. Four sealed walls, which is what every
            # bespoke module was: each was written to be RENDERED on its own,
            # before `deck.py` could assemble one onto a ring, so nothing ever
            # had to be entered. `deck.build_deck` measures the mouth with
            # `_mouth_clear` and fell back to a generic store bay for all three
            # bars -- `bar_unnamed`, `eclipse_cafe` and `happy_daze` -- so a
            # player walked into a grey box where a bar should be.
            #
            # The +z wall, because `bespoke.NEAR_END` declares this module's
            # near end `max_z` on the module's own evidence (it is authored
            # symmetric about the origin, z -5.91..+5.91), and that is the face
            # the ring corridor arrives at.
            _bsp.doorway_wall(
                lambda n, lo, hi: _box(v, t, g, n, lo, hi), "bar_wall",
                -hw - WALL_T_M, hw + WALL_T_M, 0.0, ROOM_H_M,
                s * hl, s * (hl + WALL_T_M))
        else:
            _box(v, t, g, "bar_wall", (-hw - WALL_T_M, 0.0, s * hl),
                 (hw + WALL_T_M, ROOM_H_M, s * (hl + WALL_T_M)))

    # ARTICULATION -- rooms.articulate(), INV-073. The bar was 23.9% of its
    # detail floor: a box with tables in it. One vocabulary for every
    # box-shaped interior on the station rather than nine that drift apart.
    _rooms.articulate(v, t, g, "bar", hw, hl, ROOM_H_M, ow=ow, ol=ol)

    # Tables in a loose grid, each with its own pendant and stools.
    for i in range(TABLES_X):
        for j in range(TABLES_Z):
            cx = -hw + (i + 1) * room_w / (TABLES_X + 1.6)
            cz = -hl + (j + 1) * room_l / (TABLES_Z + 1)
            _cyl(v, t, g, "bar_table_stem", cx, cz, 0.0,
                 TABLE_H_M - TABLE_TOP_M, 0.075, seg=8)
            _cyl(v, t, g, "bar_table", cx, cz, TABLE_H_M - TABLE_TOP_M,
                 TABLE_H_M, TABLE_R_M)
            for k in range(STOOLS_PER_TABLE):
                a = math.tau * k / STOOLS_PER_TABLE + 0.4
                sx = cx + (TABLE_R_M + 0.34) * math.cos(a)
                sz = cz + (TABLE_R_M + 0.34) * math.sin(a)
                _cyl(v, t, g, "bar_stool", sx, sz, 0.0, STOOL_H_M, STOOL_R_M,
                     seg=8)
            pendant(v, t, g, cx, cz)

    # The bar counter along the right-hand wall, with a back bar behind it.
    bx = hw - BAR_D_M - 0.25
    # `bar_servery`, not `bar_counter`: rooms.py emits `prop_bar_counter`
    # for the procedural bars, and `bar_counter` is a SUFFIX of it. Under
    # substring/longest-wins a material binding the short name also
    # matches the long one. It resolves correctly today only because
    # `prop_bar_counter` happens to be longer, and would stop the moment
    # either was renamed -- the same latent shape as `_wall` reaching into
    # `prop_monitor_wall`.
    _box(v, t, g, "bar_servery",
         (bx, 0.0, -BAR_L_M / 2), (bx + BAR_D_M, BAR_H_M, BAR_L_M / 2))
    _box(v, t, g, "bar_footrail",
         (bx - 0.14, BAR_FOOT_M, -BAR_L_M / 2),
         (bx - 0.08, BAR_FOOT_M + 0.06, BAR_L_M / 2))
    _box(v, t, g, "bar_backbar",
         (hw - 0.30, 0.0, -BAR_L_M / 2), (hw, BACKBAR_H_M, BAR_L_M / 2))

    # --- wall fittings, all from the frame -------------------------------
    # Cyan neon: a glyph plus a vertical tube in four segments with three
    # clamp bands. The segment/clamp counts are counted from the frame, so
    # they are observations rather than choices and are asserted as such.
    _box(v, t, g, "bar_neon_glyph",
         (-hw, 1.75, -hl + 1.2),
         (-hw + 0.05, 1.75 + NEON_GLYPH_H_M, -hl + 1.2 + NEON_GLYPH_W_M))
    seg_h = (NEON_TUBE_H_M - NEON_CLAMPS * 0.05) / NEON_TUBE_SEGS
    for k in range(NEON_TUBE_SEGS):
        y0 = 1.05 + k * (seg_h + 0.05)
        _cyl(v, t, g, "bar_neon_tube", -hw + 0.06, -hl + 0.75,
             y0, y0 + seg_h, NEON_TUBE_R_M, seg=6)
        if k < NEON_CLAMPS:
            _box(v, t, g, "bar_neon_clamp",
                 (-hw, y0 + seg_h, -hl + 0.75 - 0.06),
                 (-hw + 0.10, y0 + seg_h + 0.05, -hl + 0.75 + 0.06))

    # The orange-red backlit cell matrix, stepped rather than rectangular.
    step = MATRIX_CELL_M + MATRIX_GAP_M
    for i in range(MATRIX_CELLS_X):
        # A stepped irregular silhouette: column height varies, as the frame
        # shows, instead of a clean rectangle.
        h = MATRIX_CELLS_Y - (i % 3)
        for j in range(h):
            _box(v, t, g, "bar_cell_matrix",
                 (-hw, 1.35 + j * step, -hl + 2.6 + i * step),
                 (-hw + 0.04, 1.35 + j * step + MATRIX_CELL_M,
                  -hl + 2.6 + i * step + MATRIX_CELL_M))

    # --- WHAT THIS BAR IS FOR, and it is the register that says so ----------
    #
    # These three were unconditional, which is half of why five named bars were
    # one room. A darts oche is a RECREATION fitting and `eclipse_cafe` and
    # `fresh_air` do not declare recreation; they are food_service, and a cafe
    # with a dartboard is a pub. `place=None` keeps every fitting so the
    # reference bar in `_selftest` -- the one measured against Doug's Dugout --
    # is unchanged. INV-265.

    # RECREATION -> the dartboard and its amber scoreboard. Authority 1: the
    # frame shows both, and it is a pub frame.
    if not fn or "recreation" in fn:
        dartboard(v, t, g, hw - 2.1, 1.73, hl - 0.02)
        _box(v, t, g, "bar_display",
             (hw - 2.1 - DISPLAY_W_M / 2, 1.28, hl - 0.04),
             (hw - 2.1 + DISPLAY_W_M / 2, 1.28 + DISPLAY_H_M, hl - 0.02))

    # RUMOUR -> booths. A room where things are overheard needs somewhere to
    # sit where you are NOT overheard, which is what a snug is for; the
    # gazetteer gives `rumour` to exactly one bar and this is what it buys.
    if "rumour" in fn:
        for k in range(BOOTHS):
            z0 = -hl + 0.5 + k * (BOOTH_L_M + 0.22)
            if z0 + BOOTH_L_M > hl - 0.5:
                break
            _box(v, t, g, "bar_booth_bench",
                 (-hw + 0.06, 0.0, z0), (-hw + 0.06 + BOOTH_D_M,
                                         BOOTH_SEAT_M, z0 + BOOTH_L_M))
            _box(v, t, g, "bar_booth_back",
                 (-hw + 0.06, 0.0, z0), (-hw + 0.16,
                                         BOOTH_BACK_M, z0 + BOOTH_L_M))
            _box(v, t, g, "bar_booth_divider",
                 (-hw + 0.06, 0.0, z0 - 0.05),
                 (-hw + 0.06 + BOOTH_D_M, BOOTH_BACK_M, z0))

    # BLACK MARKET FRINGE -> a shuttered hatch behind the counter. Not a
    # storeroom you can enter -- the point is that it is CLOSED, and that a
    # player can see there is a back of house they are not in.
    if "black_market_fringe" in fn:
        sx = hw - 0.30
        _box(v, t, g, "bar_shutter_frame",
             (sx - 0.06, 0.0, -SHUTTER_W_M / 2 - 0.08),
             (sx, SHUTTER_H_M + 0.08, SHUTTER_W_M / 2 + 0.08))
        for k in range(SHUTTER_SLATS):
            y0 = k * SHUTTER_H_M / SHUTTER_SLATS
            _box(v, t, g, "bar_shutter_slat",
                 (sx - 0.04, y0 + 0.006, -SHUTTER_W_M / 2),
                 (sx, y0 + SHUTTER_H_M / SHUTTER_SLATS - 0.006,
                  SHUTTER_W_M / 2))

    return v, t, g


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
    v, t, g = room()
    names = [n for n, _lo, _hi in g]

    # --- the trademark, excluded by assertion rather than by memory -------
    # The source frame contains a lit ZIMA panel: real 1990s product placement.
    # It is recorded in the reference index as observed and is reproduced
    # nowhere. "I remembered not to" is not a guarantee; the next session will
    # not have seen the frame.
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    body = src.split("WHAT IS DELIBERATELY NOT REPRODUCED", 1)[1]
    body = body.split("_selftest", 1)[0]
    check("the real-world trademark in the frame is not reproduced",
          body.upper().count("ZIMA") <= 1,
          "it may be named once, in the note explaining why it is excluded")
    check("no geometry group carries the trademark",
          not any("zima" in n.lower() for n in names))

    # --- the lighting design, which IS the room ---------------------------
    n_tables = names.count("bar_table")
    check("there is a pendant over every table, one to one",
          names.count("bar_pendant_shade") == n_tables == TABLES_X * TABLES_Z,
          f"{names.count('bar_pendant_shade')} pendants, {n_tables} tables")
    check("every pendant has a source inside its shade",
          names.count("bar_pendant_lamp") == n_tables)
    # Hung LOW is the whole point: a pendant above standing eye height lights
    # the room instead of the table, and the pools disappear.
    check("the pendants hang below standing eye height, so they pool",
          PENDANT_H_M < 1.70,
          f"{PENDANT_H_M} m to the shade underside")
    check("but clear of a seated diner's head",
          PENDANT_H_M > TABLE_H_M + 0.55,
          f"{PENDANT_H_M - TABLE_H_M:.2f} m above the table")
    check("the shade is shallow, a cone rather than a dome",
          SHADE_DROP_M < SHADE_R_M * 0.75,
          f"drop {SHADE_DROP_M} m across a {SHADE_R_M} m radius")

    # --- it is NOT the Zocalo ---------------------------------------------
    p = kit.class_params("concourse")
    check("the bar is far lower than a concourse -- it is a small room",
          ROOM_H_M < p["ceiling_height_m"] * 0.5,
          f"{ROOM_H_M} m against the concourse's {p['ceiling_height_m']} m")
    check("and its floor area is a room's, not a concourse's",
          ROOM_L_M * ROOM_W_M < 120.0,
          f"{ROOM_L_M * ROOM_W_M:.0f} m2")

    # --- the dartboard is a real dartboard --------------------------------
    check("the dartboard has twenty segments", DART_SEGS == 20)
    check("the number sequence is the regulation one",
          DART_SEQUENCE == (20, 1, 18, 4, 13, 6, 10, 15, 2, 17,
                            3, 19, 7, 16, 8, 11, 14, 9, 12, 5))
    check("every number 1-20 appears exactly once",
          sorted(DART_SEQUENCE) == list(range(1, 21)))
    # The defining property of the real layout: high numbers sit beside low
    # ones, so a near miss is punished. Mean adjacent difference is ~6.7 on a
    # regulation board and would be ~1 on a naive 1..20 ring.
    diffs = [abs(DART_SEQUENCE[i] - DART_SEQUENCE[(i + 1) % 20])
             for i in range(20)]
    check("high numbers neighbour low ones, as a real board does",
          sum(diffs) / len(diffs) > 5.0,
          f"mean adjacent difference {sum(diffs) / len(diffs):.1f}")
    check("the board is regulation size across",
          abs(DART_R_M * 2 - 0.451) < 0.001, f"{DART_R_M * 2:.3f} m")

    # --- the counted fittings are counts, not choices ---------------------
    check("the neon tube is in four segments, as counted in the frame",
          names.count("bar_neon_tube") == NEON_TUBE_SEGS == 4)
    check("split by three clamp bands, as counted",
          names.count("bar_neon_clamp") == NEON_CLAMPS == 3)
    check("the cell matrix is about twelve cells across",
          MATRIX_CELLS_X == 12)
    check("the matrix silhouette is stepped, not a clean rectangle",
          len({MATRIX_CELLS_Y - (i % 3) for i in range(MATRIX_CELLS_X)}) > 1)
    check("the amber display reads what the frame reads",
          DISPLAY_TEXT == "209")

    # --- geometry ---------------------------------------------------------
    check("the room builds", len(t) > 600, f"{len(t)} triangles")
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in g) == len(t))
    xs = [q[0] for q in v]
    ys = [q[1] for q in v]
    zs = [q[2] for q in v]
    check("nothing escapes the room",
          min(xs) >= -ROOM_W_M / 2 - WALL_T_M - 1e-6
          and max(xs) <= ROOM_W_M / 2 + WALL_T_M + 1e-6
          and min(zs) >= -ROOM_L_M / 2 - WALL_T_M - 1e-6
          and max(zs) <= ROOM_L_M / 2 + WALL_T_M + 1e-6,
          f"x {min(xs):.2f}..{max(xs):.2f}  z {min(zs):.2f}..{max(zs):.2f}")
    check("nothing is below the deck or above the soffit",
          min(ys) >= -0.15 and max(ys) <= ROOM_H_M + 0.15,
          f"y {min(ys):.2f}..{max(ys):.2f}")
    # A stool a diner cannot sit on, or a table they cannot reach, is furniture
    # that fails at the one thing furniture does.
    check("the stools are a sittable height for the tables",
          0.10 < TABLE_H_M - STOOL_H_M < 0.32,
          f"{TABLE_H_M - STOOL_H_M:.2f} m from seat to table top")
    check("the bar counter is a standing counter, not a table",
          BAR_H_M > TABLE_H_M + 0.25, f"{BAR_H_M} m")

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0, 0, 0), (1, 2, 3))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0)
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)

    # --- CLOSURE, which winding says nothing about -------------------------
    # This file asserted winding from the day it was written and never
    # closure, and the two are independent: `_signed_volume` on a cylinder
    # with no bottom is still positive, because the missing cap contributes
    # nothing either way. 824 open boundary edges shipped under that gate --
    # 36 stools, 9 tables, 9 stems, 9 pendants, 4 neon segments and the
    # dartboard, every one of them a lathe or a disc open at one end.
    #
    # It runs on the WHOLE ROOM rather than on a probe, because the probe is
    # the case with no defect in it.
    import interior_kit as _k                                # noqa: PLC0415
    op, nm = _k.boundary_edges(v, t)
    check("the bar is a closed surface", not op,
          f"{len(op)} open boundary edges, first at {op[:1]}")

    # NEGATIVE CONTROL -- put one cylinder's caps back the way they were.
    cv, ct, cg = [], [], []
    _cyl(cv, ct, cg, "probe", 0.0, 0.0, 0.0, 1.0, 0.3, seg=8)
    check("...and the gate fires on a cylinder with no bottom cap",
          len(_k.boundary_edges(cv, ct[:-8])[0]) == 8,
          f"{len(_k.boundary_edges(cv, ct[:-8])[0])} open with the floor of "
          f"an 8-sided cylinder removed -- expected 8")
    check("...and none of these non-manifold edges is this module's",
          len(nm) == _INHERITED_NON_MANIFOLD,
          f"{len(nm)} against the {_INHERITED_NON_MANIFOLD} that "
          f"rooms.articulate brings in with the dado, rail and skirt bands")

    print(f"\nbar: {ROOM_L_M} x {ROOM_W_M} x {ROOM_H_M} m, "
          f"{n_tables} tables each under its own pendant, {len(t):,} triangles")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
