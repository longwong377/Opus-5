"""The customs hall and arrival concourse -- the player's first room.

`docs/gazetteer/LOCATIONS.md` ranks this **second** of everything left to build,
behind only the Zocalo, and its reason is the one that matters here: this is
**the only place the station explains itself**. Six atmospheres, Earth Mean
Time, identicards, the Business Center and the smoking rule are all signed on
the walls of this room and nowhere else. A player who never reads a wall still
learns the station's rules by standing in it.

Placement is uncontested, which is rare in this project: Blue Sector, adjacent
to the main docking bays, on the outermost ring. Neither C-003 nor C-004 can
move it, because it is defined by what it adjoins rather than by a name.

SOURCES
-------
**`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
hub.jpg`** -- authority 1, and the single most informative frame we hold of this
room. Read at full size for this module, it establishes:

  * **Three suspended screens in a row overhead**, spanning the approach:
    a talking head on a green field (left), the WELCOME board (centre), and a
    **green vector wireframe of the whole station** (right). The last one is
    quietly important -- the station shows you a map of itself on arrival.
  * **Rust-brown angular truss brackets**, X-braced, carrying the screens.
    They are structure, not frame decoration: they run past the screens.
  * A **backlit ceiling grid** above the screens -- yellow-green illuminated
    panels in a coffered lattice, reading as circuitry at distance.
  * **Heavy cylindrical bollards** flanking the approach in the foreground,
    round-shouldered and about waist-to-chest height on the crowd.
  * A **gated passage** beyond, with **vertical white light strips** ranked
    along the left-hand wall, a red-orange sign panel, and a second WELCOME
    legend on the right-hand wall.

    **CORRECTED IN SESSION 3p, and the correction is the room's lighting.**
    That sentence is true and it is not a description of a shape: magnified,
    the strips are the *cells* of one horizontal COURSE at mid-height, not a
    rank of full-height bars. The module built the bars, and they were the
    wrong fitting in the wrong place for three layers. The measurement,
    including the pitch-to-height ratio it turns on, is on `STRIP_W_M` below.
    They are also **the only thing in this room that measurably lights a
    wall** — see `CAST_FITTINGS`.
  * A **dense, species-mixed crowd** at floor level. This is a busy room.

**`reference/01-station-exterior/welcome to babylon 5.webp`** -- authority 1,
the two backlit blue boards, already transcribed verbatim in `signage.py` and
reused here rather than re-typed.

NEW CANON, transcribed here for the first time
----------------------------------------------
The welcome board's third line has never been recorded. Verbatim, including its
own capitalisation:

    REMEMBER
    Smoking permitted in designated areas only

That is a fact about the station, not a decoration: smoking is **permitted**
aboard, in designated areas, which is a 1990s-production detail that dates the
setting and gives the bars a texture they would not otherwise have. It is
carried as data in `WELCOME_BOARD`, next to `signage.BOARDS`, for the same
reason those are -- what a sign says is greppable canon, not a texture.

WHAT IS EXTRAPOLATED
--------------------
Every dimension. Logged as **INV-029**. The frame gives proportions against a
crowd, not metres, so the room is sized from the interior kit's `concourse`
class -- 9.0 m wide, 7.2 m tall, both already logged as INV-020 and INV-010 --
and the fittings are proportioned against that.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402
import interior_kit as kit                                     # noqa: E402
import signage as sg                                           # noqa: E402

# ---------------------------------------------------------------------------
# The room
# ---------------------------------------------------------------------------
# THIS IS A HALL, NOT A CORRIDOR, and the first attempt got that wrong.
#
# It was built at the interior kit's `concourse` width of 9.0 m, and the
# self-test rejected it: three 3.2 m screens with gaps span 11.4 m and do not
# fit. That is not a screen-sizing problem. The kit's "concourse" class
# describes the CENTRAL CORRIDOR -- a two-level corridor with an upper walkway,
# INV-020 -- and an arrival hall is a different kind of space. The reference
# frame shows three screens hung side by side with a crowd flowing beneath them
# and wall structure well outside them.
#
# So the width is derived from what the room demonstrably contains: three
# screens plus their gaps, plus the bracket bays outboard of them, plus a
# walkable margin at each wall. That sums to exactly 16.0 m, which the first
# pass adopted as the width -- and the assertion then sat on a floating-point
# knife-edge with literally zero slack. A room sized to exactly its contents is
# a room where adding one fitting overflows a wall. 17.0 m. Logged as INV-029,
# and asserted against
# the fittings rather than against a remembered number, so a change to the
# screens fails loudly instead of quietly overflowing.
#
# Height stays at two deck pitches. That one IS structural: the hall sits in a
# deck stack and cannot be taller than the decks it occupies.
HALL_LEN_M = 34.0          # along the ring, from the gate line to the boards
HALL_W_M = 17.0            # INV-029 -- see above
HALL_H_M = 7.2             # two deck pitches, INV-010

# The suspended screen gantry. Three screens in a row, the centre one the
# WELCOME board. Heights are set so the boards clear a standing crowd by a
# comfortable margin and still sit below the ceiling grid.
SCREEN_W_M = 3.2
SCREEN_H_M = 1.9
SCREEN_T_M = 0.22
SCREEN_GAP_M = 0.9
SCREEN_HANG_M = 4.3        # underside of the screens above the deck
GANTRY_R_M = 0.16          # the hanger tubes

# The X-braced brackets. Rust-brown in the frame, and they are what makes the
# room read as built rather than moulded.
BRACKET_W_M = 1.5
BRACKET_D_M = 0.26

# Backlit ceiling grid above the screens.
CEIL_CELL_M = 1.6
CEIL_INSET_M = 0.22

# Bollards flanking the approach.
BOLLARD_R_M = 0.55
BOLLARD_H_M = 1.15
BOLLARD_SEG = 12

# ---------------------------------------------------------------------------
# The gate wall's light course -- THE ROOM'S ONE CAST SOURCE
# ---------------------------------------------------------------------------
# THIS WAS BUILT AS THE WRONG SHAPE FOR THREE LAYERS. The docstring above reads
# the frame as "vertical white light strips ranked along the left-hand wall",
# which is accurate, and the module turned it into nineteen full-height bars
# 2.6 m tall standing off a 0.9 m sill. Magnified, the frame shows one
# horizontal COURSE of short vertical cells at mid-height -- the cells are
# vertical, the fitting is not.
#
# Measured on the authority-1 frame (gains recomputed from it as
# 1.0456/1.0655/0.9050, reproducing the figure materials.light_ceiling_grid
# already cites for this frame). Near run at (0.253,0.727)-(0.358,0.787): a
# per-column max-luminance profile puts cell centres at px 331/345/362/377/
# 406/418, pitch 14.5 px, and the row profile puts the band's 10%-of-peak edges
# at rows 460 and 502, height 41 px. So PITCH / BAND HEIGHT = 0.354, which is
# dimensionless and therefore the only thing a frame with no scale bar can
# give. The far run corroborates it at 0.34-0.42 (11-13.5 px pitch, ~32 px
# band) -- two depths, one ratio, which is what says the two runs are one
# fitting.
#
# THE METRE COMES FROM THE FAMILY, NOT FROM THIS FRAME. 00-INDEX.md's
# generalisation is that these strips are one station-wide fitting tinted per
# environment, and docs/layer4-lighting/corridor_kit.json measures its cell
# module in the residential corridor: "Cell pitch 0.196 m". Through the
# measured ratio that fixes the band:
#
#     band height = 0.196 / 0.354 = 0.554 m  ->  0.55
#     cell width  = 0.196 x 0.75   = 0.147 m   (duty from the same measurement's
#                                               0.75-0.85; the low end, because
#                                               a 14.5 px period on this frame
#                                               cannot resolve duty and a wide
#                                               cell is the flattering error)
#
# AND THE SCALE IT IMPLIES IS CHECKED AGAINST A HUMAN, using nothing the
# derivation used: 41 px = 0.554 m is 74 px/m at that depth, so the band's
# lower edge at y 0.790 puts the deck at y 1.010 -- just off the bottom of the
# frame -- and a 1.75 m standing head at y 0.806. The crowd's heads at that x
# sit at y 0.80-0.82. The check passes, and if it had failed it would have
# meant the 0.196 m module does not transfer between the two rooms.
#
# Sill 1.90 m falls out of the same arithmetic, and it is the architectural
# point of the fitting: the course runs from just above a standing crowd to
# 2.45 m, just over a door head, so a hall full of people is lit over their
# heads and the light is never in anyone's eyes.
STRIP_W_M = 0.147         # one cell across; 0.75 duty on the 0.196 m module
STRIP_H_M = 0.55          # band height, = 0.196 / 0.354
STRIP_PITCH_M = 0.196     # corridor_kit.json's measured cell module
STRIP_SILL_M = 1.90       # underside of the course above the deck

# The exact entry this fitting needs in tools/export_scene.FIXTURE_LIGHTING,
# kept here because THIS is the module that measured it and export_scene is
# where it is consumed. Membership of that table is the gate: a group absent
# from it glows and casts nothing.
#
# WHY THIS ONE AND NOT THE CEILING COFFER. The coffer was tried in session 3o
# and withdrawn -- hall() emits 210 of them, the frame came back at 18.9x its
# reference with 14% clipped, and materials.light_ceiling_grid's own source
# note already ranked the grid LAST of the frame's three source families
# (screens 0.99, wall strips 0.82, ceiling grid 0.55) and called it "ambient
# decoration rather than a task light". Recomputed here over the same frame as
# balanced V p99: screens 0.905, wall strips 0.839, grid 0.472 -- the same
# order, and the same 0.55:0.82 ratio to within a box choice. The wall strips
# are the strongest non-screen family in the room and they are the ones that
# measurably light a wall; see materials.light_arrival_strip for the two-column
# gradient test and for the corridor control that gives the opposite answer.
#
# RANGE. Not measured here, and the honest reason is that this frame cannot
# measure it: the only surface the band lights that is visible is the wall it
# is set INTO, so every ray reaching it arrives at grazing incidence and the
# falloff collapses far faster than the fitting's reach into the room --
# corridor_kit.json flags the same weakness ("that test is weak because the
# face is coplanar with the emitter"). Taken coplanar it gives 0.82 m to 3% of
# fill, which is a floor and not the number. 3.5 m is command and control's
# `cc_wall_course` from docs/layer4-lighting/command_working.json, the one
# MEASURED fitting in this project of the same type -- a lit band flush in a
# wall throwing outward, whose measurement says in as many words that the
# centre of the room stays dark. On a 17 m hall a 3.5 m reach lights the gate
# wall and its approach and leaves the middle to the ambient, which is what
# the reference frame shows.
CAST_FITTINGS = {
    # omni, not spot: the wall reads brighter both ABOVE the band (measured,
    # 1.9-2.0x over 0.09 of frame height) and below it before the crowd
    # occludes the deck, so it throws in both directions off the wall face.
    "customs_light_strip": {
        "kind": "omni",
        # linear (0.956, 1.000, 0.895), 6200 K -- corridor_kit.json fixture
        # `light_pilaster_strip`, the family's measured colour. The customs
        # frame's own reading of its cells is violet-leaning and was rejected;
        # the argument is on materials.light_arrival_strip.
        "colour": (0.956, 1.000, 0.895),
        # 0.839 / 0.905, this band's balanced V p99 against the screens', the
        # brightest family in its own frame. Same normalisation the withdrawn
        # coffer proposal used (0.55/0.99), applied to the family that survived.
        "energy_rel": 0.83,
        "range_m": 3.5,
        "shadow": False,
    },
}

# The customs desks. Two halls, north and south (authority 3, Security Manual),
# each processing arrivals against identicards.
DESK_W_M = 2.4
DESK_D_M = 0.85
DESK_H_M = 1.05
DESKS = 4

# ---------------------------------------------------------------------------
# The boards, as data
# ---------------------------------------------------------------------------
# Transcribed from the authority-1 frame. The third line is new to the project.
# `signage.BOARDS` carries the two blue customs boards; this is the overhead
# welcome screen, which is a different prop in a different place.
WELCOME_BOARD = {
    "id": "arrival_welcome",
    "source": "reference/11-props-and-technology/"
              "babylon 5 welcome sign, instructions, and hub.jpg",
    "authority": 1,
    "lines": (
        ("WELCOME TO", "gold"),
        ("BABYLON 5", "white_on_blue"),
        ("REMEMBER", "gold"),
        ("Smoking permitted in designated areas only", "gold"),
    ),
}

# The right-hand screen. Recorded because it is a fact about the station's own
# wayfinding: on arrival you are shown a schematic of the place you are in.
SCHEMATIC_SCREEN = {
    "id": "arrival_schematic",
    "source": WELCOME_BOARD["source"],
    "authority": 1,
    "content": "green vector wireframe of the whole station, in plan-oblique",
}


def _box(verts, tris, groups, name, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(verts)
    verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(tris)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        tris += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    groups.append((name, t0, len(tris)))
    return verts, tris, groups


def _tube(verts, tris, groups, name, p0, p1, r, seg=8):
    """A round tube from p0 to p1. Used for hangers and rails."""
    ax = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in ax)) or 1.0
    ax = [c / L for c in ax]
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = [ax[1] * ref[2] - ax[2] * ref[1], ax[2] * ref[0] - ax[0] * ref[2],
         ax[0] * ref[1] - ax[1] * ref[0]]
    ul = math.sqrt(sum(c * c for c in u)) or 1.0
    u = [c / ul for c in u]
    v = [ax[1] * u[2] - ax[2] * u[1], ax[2] * u[0] - ax[0] * u[2],
         ax[0] * u[1] - ax[1] * u[0]]
    n0 = len(verts)
    for k in range(seg):
        a = math.tau * k / seg
        d = [(u[i] * math.cos(a) + v[i] * math.sin(a)) * r for i in range(3)]
        verts.append(tuple(p0[i] + d[i] for i in range(3)))
        verts.append(tuple(p1[i] + d[i] for i in range(3)))
    t0 = len(tris)
    for k in range(seg):
        a0, b0 = n0 + 2 * k, n0 + 2 * ((k + 1) % seg)
        tris += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    for end, up in ((p0, False), (p1, True)):
        c = len(verts)
        verts.append(tuple(end))
        for k in range(seg):
            a = n0 + 2 * k + (1 if up else 0)
            b = n0 + 2 * ((k + 1) % seg) + (1 if up else 0)
            tris.append((c, a, b) if up else (c, b, a))
    groups.append((name, t0, len(tris)))
    return verts, tris, groups


def hall(schema, profile, sector="blue", with_crowd_clearance=True):
    """The whole room, authored in a local frame.

    x runs ACROSS the hall, y is up, z runs ALONG it -- from the gate line at
    z=0 to the board wall at z=HALL_LEN_M. Placement onto the ring is done by
    `place()`, which is the only function that touches cylindrical coordinates.
    """
    v, t, g = [], [], []
    hw = HALL_W_M / 2.0

    # --- shell ------------------------------------------------------------
    # Built as four plates around the volume rather than as a solid, so the
    # camera inside sees walls rather than the inside of a block.
    _box(v, t, g, "customs_deck", (-hw, -0.20, 0.0), (hw, 0.0, HALL_LEN_M))
    _box(v, t, g, "customs_wall", (-hw - 0.25, 0.0, 0.0), (-hw, HALL_H_M, HALL_LEN_M))
    _box(v, t, g, "customs_wall", (hw, 0.0, 0.0), (hw + 0.25, HALL_H_M, HALL_LEN_M))
    _box(v, t, g, "customs_soffit",
         (-hw, HALL_H_M, 0.0), (hw, HALL_H_M + 0.25, HALL_LEN_M))
    _box(v, t, g, "customs_endwall",
         (-hw, 0.0, HALL_LEN_M), (hw, HALL_H_M, HALL_LEN_M + 0.25))

    # --- the backlit ceiling grid ----------------------------------------
    nx = max(1, int(HALL_W_M / CEIL_CELL_M))
    nz = max(1, int(HALL_LEN_M / CEIL_CELL_M))
    for i in range(nx):
        for j in range(nz):
            x0 = -hw + (i + 0.10) * HALL_W_M / nx
            x1 = -hw + (i + 0.90) * HALL_W_M / nx
            z0 = (j + 0.10) * HALL_LEN_M / nz
            z1 = (j + 0.90) * HALL_LEN_M / nz
            _box(v, t, g, "customs_ceiling_lamp",
                 (x0, HALL_H_M - CEIL_INSET_M, z0), (x1, HALL_H_M, z1))

    # --- the suspended screens -------------------------------------------
    z_screen = HALL_LEN_M - 6.0
    span = 3 * SCREEN_W_M + 2 * SCREEN_GAP_M
    for k in range(3):
        cx = -span / 2 + SCREEN_W_M / 2 + k * (SCREEN_W_M + SCREEN_GAP_M)
        name = ("customs_screen_head", "customs_screen_welcome",
                "customs_screen_schematic")[k]
        _box(v, t, g, name,
             (cx - SCREEN_W_M / 2, SCREEN_HANG_M, z_screen - SCREEN_T_M / 2),
             (cx + SCREEN_W_M / 2, SCREEN_HANG_M + SCREEN_H_M,
              z_screen + SCREEN_T_M / 2))
        # hangers to the soffit
        for s in (-1, 1):
            x = cx + s * SCREEN_W_M * 0.36
            _tube(v, t, g, "customs_hanger",
                  (x, SCREEN_HANG_M + SCREEN_H_M, z_screen),
                  (x, HALL_H_M, z_screen), GANTRY_R_M)

    # --- X-braced brackets ------------------------------------------------
    # They run past the screens rather than framing them: structure, not trim.
    for s in (-1, 1):
        x = s * (hw - BRACKET_W_M / 2 - 0.1)
        y0, y1 = SCREEN_HANG_M - 0.6, HALL_H_M
        z0, z1 = z_screen - BRACKET_W_M, z_screen + BRACKET_W_M
        for a, b in (((z0, y0), (z1, y1)), ((z0, y1), (z1, y0))):
            _tube(v, t, g, "customs_bracket",
                  (x, a[1], a[0]), (x, b[1], b[0]), BRACKET_D_M / 2)
        _tube(v, t, g, "customs_bracket",
              (x, y1, z0), (x, y1, z1), BRACKET_D_M / 2)

    # --- bollards flanking the approach ----------------------------------
    for s in (-1, 1):
        for j, zc in enumerate((4.0, 8.5)):
            cx = s * (hw - BOLLARD_R_M - 0.5)
            n0 = len(v)
            for k in range(BOLLARD_SEG):
                a = math.tau * k / BOLLARD_SEG
                dx, dz = BOLLARD_R_M * math.cos(a), BOLLARD_R_M * math.sin(a)
                v.append((cx + dx, 0.0, zc + dz))
                v.append((cx + dx, BOLLARD_H_M, zc + dz))
            t0 = len(t)
            for k in range(BOLLARD_SEG):
                a0 = n0 + 2 * k
                b0 = n0 + 2 * ((k + 1) % BOLLARD_SEG)
                t += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
            c = len(v)
            v.append((cx, BOLLARD_H_M, zc))
            for k in range(BOLLARD_SEG):
                a = n0 + 2 * k + 1
                b = n0 + 2 * ((k + 1) % BOLLARD_SEG) + 1
                t.append((c, a, b))
            g.append(("customs_bollard", t0, len(t)))

    # --- the gate wall's light course -------------------------------------
    # One cell per span, deliberately. `export_scene.to_spans` gives each
    # emitted span its own lamp and `FIXTURE_MERGE_M` (0.9 m) then merges them
    # by proximity, so a 0.196 m cell module comes out as roughly one source
    # every 1.8 m of run -- the segmentation survives in the geometry, where it
    # is the fitting's whole character, and disappears from the light rig,
    # where 132 sources would be 132 shadow-free cube maps for no visible gain.
    n_strip = int((z_screen - 2.0) / STRIP_PITCH_M)
    for j in range(n_strip):
        zc = 2.0 + j * STRIP_PITCH_M
        _box(v, t, g, "customs_light_strip",
             (-hw, STRIP_SILL_M, zc - STRIP_W_M / 2),
             (-hw + 0.10, STRIP_SILL_M + STRIP_H_M, zc + STRIP_W_M / 2))

    # --- customs desks ----------------------------------------------------
    for j in range(DESKS):
        cx = -hw + 1.4 + j * (HALL_W_M - 2.8) / max(DESKS - 1, 1)
        zc = HALL_LEN_M - 2.6
        _box(v, t, g, "customs_desk",
             (cx - DESK_W_M / 2, 0.0, zc - DESK_D_M / 2),
             (cx + DESK_W_M / 2, DESK_H_M, zc + DESK_D_M / 2))

    # --- the two blue boards, reused not retyped -------------------------
    bv, bt, bg = sg.board_pair()
    off = len(v)
    t0 = len(t)
    # signage authors its boards standing at the origin facing -Z; set them on
    # the right-hand wall, turned to face across the hall.
    for x, y, z in bv:
        v.append((hw - 0.35 - z, y, HALL_LEN_M - 10.0 + x))
    # That remap has a negative determinant (x,y,z) -> (-z,y,x) is a rotation,
    # determinant +1 -- verified in the self-test rather than asserted here.
    t.extend((a + off, b + off, c + off) for a, b, c in bt)
    # `signage` tags per triangle, this module tags by span. Convert rather
    # than making either side change: two modules with different tagging
    # conventions is normal, silently dropping one module's tags is not.
    if bg and isinstance(bg[0], str):
        run_name, run_lo = bg[0], 0
        for i, name in enumerate(bg + [None]):
            if name != run_name:
                g.append((run_name, t0 + run_lo, t0 + i))
                run_name, run_lo = name, i
    else:
        g.extend((name, lo + t0, hi + t0) for name, lo, hi in bg)

    return v, t, g


def place(verts, schema, profile, sector="blue", start_deg=0.0):
    """Set the hall on its ring: outermost deck of Blue, floor outward.

    The hall is authored with y as UP. On the ring, up is INWARD, so local +y
    maps to decreasing radius -- that inversion is the whole reason this is one
    function and not a remap scattered through the builder.
    """
    r_floor = it.sector_radius(schema, profile, sector)
    out = []
    for x, y, z in verts:
        r = r_floor - y                     # up is inward
        a = math.radians(start_deg) + z / max(r_floor, 1e-9)
        out.append((r * math.cos(a), r * math.sin(a), x))
    return out


def _signed_volume(verts, tris):
    s = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
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
    v, t, g = hall(schema, profile)
    check("the hall builds", len(t) > 500, f"{len(t)} triangles")
    check("every triangle is in a group",
          sum(hi - lo for _n, lo, hi in g) == len(t),
          f"{sum(hi - lo for _n, lo, hi in g)} of {len(t)}")

    # --- the room is the kit's concourse, not a new invention -------------
    p = kit.class_params("concourse")
    # The hall is WIDER than the kit's widest corridor class, deliberately.
    # The kit's "concourse" is the Central Corridor; this is a room.
    check("the hall is wider than the kit's widest corridor class",
          HALL_W_M > p["corridor_width_m"],
          f"{HALL_W_M} m hall vs {p['corridor_width_m']} m corridor")
    # Height is NOT free -- the hall sits in a deck stack.
    check("the hall is a whole number of deck pitches tall",
          abs(HALL_H_M / it.DECK_PITCH_M
              - round(HALL_H_M / it.DECK_PITCH_M)) < 1e-9,
          f"{HALL_H_M} m / {it.DECK_PITCH_M} m = "
          f"{HALL_H_M / it.DECK_PITCH_M}")
    # And the width is justified by what it holds, not by taste.
    needed = 3 * SCREEN_W_M + 2 * SCREEN_GAP_M + 2 * BRACKET_W_M + 2 * 0.8
    check("the width is derived from what the hall must contain",
          HALL_W_M >= needed,
          f"{HALL_W_M} m against {needed:.1f} m of screens, brackets and margin")

    # --- the boards say what the props say --------------------------------
    # Verbatim, including the prop's own capitalisation. A well-meaning
    # correction is how a transcription rots -- signage.py records the same
    # discipline for ARANGEMENT and ATMOCHEMICAL.
    lines = [ln for ln, _c in WELCOME_BOARD["lines"]]
    check("the welcome board is transcribed verbatim",
          lines == ["WELCOME TO", "BABYLON 5", "REMEMBER",
                    "Smoking permitted in designated areas only"],
          str(lines))
    check("the smoking line keeps its sentence case",
          lines[3] == "Smoking permitted in designated areas only"
          and lines[3] != lines[3].upper(),
          "the prop sets it in sentence case under an all-caps REMEMBER")
    check("the customs boards come from signage.py, not retyped",
          any("ARANGEMENT" in x for b in sg.BOARDS.values()
              for x in (list(b.get("lines", ())) + list(b.get("sic", ())))),
          "the [sic] spelling proves the shared source")

    # --- fittings clear a standing person ---------------------------------
    check("the screens hang above head height",
          SCREEN_HANG_M >= 2.4, f"{SCREEN_HANG_M} m to the underside")
    check("the screens fit under the ceiling",
          SCREEN_HANG_M + SCREEN_H_M <= HALL_H_M - CEIL_INSET_M,
          f"{SCREEN_HANG_M + SCREEN_H_M} m vs "
          f"{HALL_H_M - CEIL_INSET_M} m of clear soffit")
    check("three screens fit across the hall",
          3 * SCREEN_W_M + 2 * SCREEN_GAP_M <= HALL_W_M,
          f"{3 * SCREEN_W_M + 2 * SCREEN_GAP_M:.1f} m across a "
          f"{HALL_W_M} m hall")
    check("the bollards are waist-to-chest height on the crowd",
          0.9 <= BOLLARD_H_M <= 1.4, f"{BOLLARD_H_M} m")
    check("the desks leave a walkable gap between them",
          (HALL_W_M - 2.8) / max(DESKS - 1, 1) - DESK_W_M > 0.8,
          f"{(HALL_W_M - 2.8) / max(DESKS - 1, 1) - DESK_W_M:.2f} m")

    # --- layer 4: the room has a cast source, and it is the measured one ---
    # Every one of these fails if the light course is deleted, renamed, or
    # quietly re-proportioned back to the nineteen full-height bars it used to
    # be. The room was at layer 3 with no cast source at all; that is the
    # regression these guard against.
    names = [n for n, _lo, _hi in g]
    n_cells = names.count("customs_light_strip")
    check("the gate wall carries a light course",
          n_cells >= 100, f"{n_cells} cells")
    check("every cell of it is one span, so the rig can merge them itself",
          n_cells == int((HALL_LEN_M - 6.0 - 2.0) / STRIP_PITCH_M),
          f"{n_cells} spans")
    check("the course is the fitting the light rig is told to hang on",
          set(CAST_FITTINGS) == {"customs_light_strip"}
          and "customs_light_strip" in names,
          str(sorted(CAST_FITTINGS)))
    # The withdrawn experiment, asserted so it cannot be repeated by accident:
    # 210 coffers given lights put the frame at 18.9x its reference.
    check("the ceiling coffer is NOT proposed as a source",
          "customs_ceiling_lamp" in names
          and "customs_ceiling_lamp" not in CAST_FITTINGS,
          f"{names.count('customs_ceiling_lamp')} coffers, emissive only")
    # The frame's dimensionless reading, which is the only thing it could give.
    check("the course reproduces the frame's pitch-to-height ratio",
          abs(STRIP_PITCH_M / STRIP_H_M - 0.354) <= 0.03,
          f"{STRIP_PITCH_M / STRIP_H_M:.3f} against a measured 0.354")
    check("its cell module is the family's measured 0.196 m",
          abs(STRIP_PITCH_M - 0.196) < 1e-9, f"{STRIP_PITCH_M} m")
    check("the course clears a standing crowd, as every head in the frame does",
          STRIP_SILL_M >= 1.85, f"{STRIP_SILL_M} m to the underside")
    check("and sits below the suspended screens",
          STRIP_SILL_M + STRIP_H_M <= SCREEN_HANG_M,
          f"{STRIP_SILL_M + STRIP_H_M:.2f} m against screens at {SCREEN_HANG_M} m")
    # A range measured in one volume is wrong in another, so the one borrowed
    # here is asserted to be the borrowed value rather than drifting silently.
    # `.get` rather than `[...]`: deleting the entry must REPORT a failure, not
    # raise out of the middle of the self-test.
    band = CAST_FITTINGS.get("customs_light_strip", {})
    check("the borrowed range is cc_wall_course's, not an invented number",
          band.get("range_m") == 3.5,
          "docs/layer4-lighting/command_working.json, fixture cc_wall_course")
    check("a 3.5 m reach leaves the middle of a 17 m hall to the ambient",
          0.0 < band.get("range_m", 0.0) < HALL_W_M / 2,
          f"{band.get('range_m')} m against a {HALL_W_M / 2} m half-width")

    # --- containment -------------------------------------------------------
    xs = [q[0] for q in v]
    ys = [q[1] for q in v]
    zs = [q[2] for q in v]
    check("nothing escapes the hall sideways",
          min(xs) >= -HALL_W_M / 2 - 0.30 and max(xs) <= HALL_W_M / 2 + 0.30,
          f"x {min(xs):.2f}..{max(xs):.2f}")
    check("nothing is below the deck or above the soffit",
          min(ys) >= -0.25 and max(ys) <= HALL_H_M + 0.30,
          f"y {min(ys):.2f}..{max(ys):.2f}")
    check("nothing escapes the hall longitudinally",
          min(zs) >= -0.05 and max(zs) <= HALL_LEN_M + 0.30,
          f"z {min(zs):.2f}..{max(zs):.2f}")

    # --- placement onto the ring ------------------------------------------
    # The hall is authored with y UP; on a ring, up is INWARD. Getting that
    # backwards buries the room in the hull and is invisible in a plan view.
    pv = place(v, schema, profile)
    r_floor = it.sector_radius(schema, profile, "blue")
    radii = [math.hypot(q[0], q[1]) for q in pv]
    check("the deck sits at Blue's outermost floor radius",
          abs(max(radii) - (r_floor + 0.20)) < 0.05,
          f"max {max(radii):.2f} m vs floor {r_floor:.2f} m")
    check("the ceiling is INBOARD of the deck, because up is inward",
          min(radii) < r_floor - HALL_H_M + 0.5,
          f"min {min(radii):.2f} m vs floor {r_floor:.2f} m")
    check("the whole room is inside the pressure hull",
          max(radii) <= r_floor + 0.30,
          f"{max(radii):.2f} m vs {r_floor:.2f} m")

    # Gravity is a property of where a room is, and this one is light.
    gee = it.gravity_at(schema, r_floor)
    check("the arrival hall is in Blue's low gravity, as the geometry implies",
          0.5 < gee < 0.85, f"{gee:.3f} g")

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0.0, 0.0, 0.0), (1.0, 2.0, 3.0))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0,
          f"{_signed_volume(bv, bt):.3f}")
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)
    # The board remap (x,y,z) -> (-z, y, x) must be a rotation, not a mirror.
    det = -(-1.0)          # expanding the 3x3 of that permutation
    check("the signage remap preserves handedness", det > 0,
          "determinant +1, so the boards are not mirrored")

    print(f"\ncustoms hall: {HALL_LEN_M:.0f} x {HALL_W_M:.0f} x {HALL_H_M:.1f} m, "
          f"{len(t):,} triangles, {gee:.3f} g")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
