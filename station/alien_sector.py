"""The Alien Sector -- where six atmospheres stop being a sign and become a lock.

`docs/gazetteer/LOCATIONS.md` ranks this **eighth** and last of the ranked
build list, and it is the one the owner's brief asks for most directly: *the
alienness*. It is also the only place in the station where an authority-1
signboard turns into a traversal mechanic.

THE MECHANIC IS CANON, NOT INVENTED
-----------------------------------
`signage.py` carries the customs board verbatim, authority 1:

    "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5. OTHERS MAY BE
     CREATED BY PRIOR ARANGEMENT [sic]. UNCOMMON ATMOSPHERIC MAKEUPS MAY BE
     SYNTHESIZED FOR ENCOUNTER SUITS."

Six simultaneous atmospheres is a **life-support architecture**, not a line of
dialogue -- `LIFE-SUPPORT-AND-INDUSTRY.md` §2.1 spells out what it forces: the
station is not one pressurised volume but at minimum six independently
conditioned ones, **with locks between them**, plus a synthesis plant and an
encounter-suit charging service. This module is those locks.

The atmosphere *classes* are read from `npc/schedule.py`, never restated here.
That module deliberately carries classes and **no numbers**, because the
identicard prop numbers exactly one of the six (`DES/ATMOS: HUMAN/02`) and
nothing numbers the others. A wrong number printed on a wall is worse than no
number, so the signage here shows a class and a hazard, not an index.

WHAT THE FRAME ESTABLISHES
--------------------------
`reference/05-sector-green/corridor in alien sector.webp`, authority 1 -- the
only interior view of this quarter we hold, and it is unambiguous about mood
and about one piece of architecture:

  * A heavy **chamfered polygonal portal** in the foreground, the station's
    standard aperture, cut deep.
  * Beyond it, a **horizontal-barred grille screen across the whole opening**.
    You do not walk into the quarter; you look *through bars* into it. That is
    the single most informative thing in the frame and it is what makes this a
    containment zone rather than a corridor.
  * **Amber light falling through an overhead lattice onto the deck**, in a
    rectangular grid of lit cells. The floor is the brightest thing in the shot.
  * A **dark circular ring fitting** on the far wall.
  * **Green point lights** low on the right.
  * Figures silhouetted behind the bars, one reading as an encounter suit.
  * Palette: dark olive-green, amber, near-black. Murky and humid.

WHAT IS EXTRAPOLATED -- INV-031
-------------------------------
Every dimension, the two-door lock geometry, the number of quarters on a
gallery, and the mask dispenser. Authority 4 (the Downbelow/Green fan sources)
supplies *that* access is "through a series of airlocks with breather-mask
dispensers" and that ~14 species live here; it supplies no sizes.

The lock geometry is constrained rather than chosen, and the constraint is the
interesting part: a lock has to hold **one person plus an encounter suit** and
its two doors must never share an open state, so the vestibule is sized from
`npc/body.py`'s tallest species rather than from taste.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "npc"))

import interior as it                                          # noqa: E402
import interior_kit as kit                                     # noqa: E402
import signage as sg                                           # noqa: E402
import schedule as sched                                       # noqa: E402

# ---------------------------------------------------------------------------
# The gallery: a corridor with quarter entrances off it
# ---------------------------------------------------------------------------
GALLERY_LEN_M = 30.0
GALLERY_W_M = 4.2          # kit `service` class -- this is not a public street
GALLERY_H_M = 3.4

# The chamfered portal. The aperture profile is the station's standard and is
# taken from the kit rather than re-derived: `interior_kit.PROVISIONAL` holds
# door width and height, and INV-008 records that the chamfered polygon RULES
# OUT an iris on geometry rather than on taste.
PORTAL_CHAMFER_M = 0.42
PORTAL_JAMB_M = 0.34
PORTAL_DEPTH_M = 0.55

# The lock vestibule between the gallery and a quarter. Two doors, never both
# open. Depth is set so a person in an encounter suit can stand clear of both
# leaves at once -- see `lock_depth_m()`, which derives it.
LOCK_CLEAR_M = 0.45        # clearance fore and aft of the occupant
SUIT_DEPTH_M = 0.75        # an encounter suit is deeper than a body

# The barred screen. This is the frame's headline feature.
BAR_H_M = 0.11             # section of a horizontal bar
BAR_PITCH_M = 0.46         # vertical spacing between bars
BAR_INSET_M = 0.14         # how far the screen sits behind the portal face
STILE_W_M = 0.13           # the vertical members
STILES = 5

# The overhead lattice that throws the amber grid onto the deck.
LATTICE_CELL_M = 0.62
LATTICE_BAR_M = 0.09
LATTICE_DROP_M = 0.20

# ---------------------------------------------------------------------------
# The illuminated deck grating -- what makes this quarter look like itself
# ---------------------------------------------------------------------------
# 00-INDEX.md's re-examination of the frame magnified its floor and found "a
# grid of roughly square cells, each cell containing about three short
# horizontal louvre bars over a light box ... roughly 7 cells across x 3-4
# deep in view", saturated yellow, and THE BRIGHTEST THING IN THE SHOT. It then
# generalises the part, which is the sentence this constant exists because of:
# "the illuminated floor grating is a station-wide element, colour-tinted per
# environment ... one kit part with a tint parameter, not four set dressings",
# appearing white/blue in `central corridor.webp`, checkerboard white in
# `sleeping-in-light-05.jpg`, saturated yellow here and as pooled uplight in
# `grey level 1.webp`.
#
# THE CELL IS NOT A NEW NUMBER. It is `LATTICE_CELL_M`, this module's existing
# 0.62 m (INV-031), and the frame corroborates it rather than the other way
# round: seven cells across a `service`-class 4.2 m gallery is 0.60 m a cell.
# The gap between cells is `LATTICE_BAR_M`, so the deck grating and the
# overhead lattice are one module at one pitch, which is what "one kit part"
# means in geometry.
#
# IT IS EMISSIVE ONLY, and that is a measurement, not an omission. See
# materials.light_deck_grating: the pier feet either side of this grating are
# the darkest surfaces in the frame (left pier flat at L 0.0094-0.0107 from
# head to foot) and the caged volume above it is brightest at its TOP. The
# third instance in this project of the brightest thing in a frame lighting
# nothing, after the pilaster strip and the portal head.
GRATING_CELL_M = LATTICE_CELL_M
GRATING_GAP_M = LATTICE_BAR_M
GRATING_PROUD_M = 0.004    # enough to beat z-fighting with the deck top
GRATING_DEPTH_M = 0.05     # the light box below the louvres

# The exact entry this module needs in tools/export_scene.FIXTURE_LIGHTING.
# Kept here because this is the module that measured it; membership of that
# table is the gate, and a group absent from it glows and casts nothing.
#
# THE SOURCE IS OVERHEAD AND IT WAS TESTED, NOT ASSUMED. A vertical profile of
# the caged volume beyond the bars, (0.30,0.10)-(0.55,0.75) on the authority-1
# frame read raw, gives L 0.0473 / 0.0511 / 0.0384 / 0.0505 across its top four
# bands against 0.0221 / 0.0229 / 0.0258 / 0.0271 across its bottom four --
# brightest at the top, falling by a factor of two downward, which is what
# 00-INDEX.md means by "hard vertical light shafts descending from a source
# high above". `overhead_lattice()` is the only geometry in this module up
# there, and its own docstring has said since it was written that it exists so
# the material pass can make it the room's light source.
#
# RANGE, derived from this module's own dimensions: the grille hangs at
# GALLERY_H_M = 3.4 m and the far corner of the deck is at
# sqrt(3.4^2 + (4.2/2)^2) = 4.00 m, so 4.0 m is the reach that gets light to
# the whole floor and no further. It lands on the same number as the two
# MEASURED omni fittings in docs/layer4-lighting/command_working.json
# (`wr_wall_strip_bank` and `wr_soffit_blade`, both range 4), which is a
# corroboration rather than the derivation.
#
# CONE: atan(2.1 / 3.4) = 31.7 deg covers wall to wall from that height. 30 is
# taken rather than 32 so the last 0.14 m of each half-width stays dark at the
# skirting -- the frame's darkest surfaces are the pier feet, and a corridor
# whose wall bases are lit is not this room.
CAST_FITTINGS = {
    "alien_lattice": {
        "kind": "spot",
        # linear (1.000, 0.675, 0.060), measured RAW off the descending shafts
        # at (0.400,0.010)-(0.560,0.180); corroborated by the floor grating at
        # (0.300,0.820)-(0.520,0.950), linear (1.000, 0.680, 0.035) -- the same
        # source seen twice, agreeing in R:G to 0.7%. The frame's whole lit
        # structure sits at linear (1.000, 0.796, 0.273), so every surface in
        # the room carries this colour. See materials.light_alien_lattice for
        # why the frame is read raw and not balanced.
        "colour": (1.000, 0.675, 0.060),
        # The only cast source in the gallery, so 1.0 by definition of a
        # within-family relative. The LEVEL is set by the module's exposure.
        "energy_rel": 1.00,
        "range_m": 4.0,
        "shadow": True,
        "angle_deg": 30.0,
    },
}

# Fittings.
RING_R_M = 0.62            # the dark circular ring on the far wall
RING_SECTION_M = 0.11
RING_SEG = 20
DISPENSER_W_M = 0.52       # breather-mask dispenser, authority 4
DISPENSER_H_M = 0.78
DISPENSER_D_M = 0.22
GREEN_LAMP_R_M = 0.055

# How many quarters open off one gallery. Authority 4 puts ~14 species in the
# sector; at four quarters to a gallery that is four galleries, which is a
# plausible quarter of a ring and is NOT asserted as canon.
QUARTERS_PER_GALLERY = 4

# Depth of the quarter volume behind a screen. The quarter INTERIORS are not
# built here -- each is a different atmosphere and a different species' home,
# and they are their own increment -- but a shell must exist, because without
# one you look through the bars into nothing and the render shows background.
# This project's own rule is that a hole shows the background through it, so
# leaving genuine void behind a grille is indistinguishable from a defect to
# the next session that renders it. The shell is a closed dim volume: the room
# is there, it is simply undressed.
QUARTER_DEPTH_M = 6.0


def atmosphere_classes():
    """The distinct atmosphere classes the NPC layer knows about.

    Read from `npc/schedule.py`, never restated. That module is the single
    place classes are defined, and it deliberately carries no numbers for five
    of the six -- see this module's docstring.
    """
    return tuple(sorted({sched.ATMOS_STANDARD, sched.ATMOS_HUMID,
                         sched.ATMOS_METHANE, sched.ATMOS_UNDISCLOSED}))


def atmospheres_available():
    """The canon count, from the authority-1 customs board."""
    return sg.ESTABLISHED["atmospheres_available"]


def lock_depth_m():
    """Depth of a lock vestibule, derived rather than chosen.

    A lock must hold one occupant clear of both leaves at once, and the
    occupant this sector is built for is wearing an encounter suit. So the
    depth is the suit's depth plus clearance fore and aft, plus the two door
    reveals. Deriving it means a change to the body model moves the
    architecture, which is the direction that dependency should run.
    """
    return SUIT_DEPTH_M + 2 * LOCK_CLEAR_M + 2 * PORTAL_DEPTH_M


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


def _torus_ring(v, t, g, name, cx, cy, z, r, section, seg=RING_SEG):
    """A flat ring standing in the XY plane -- the fitting on the far wall."""
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg
        ca, sa = math.cos(a), math.sin(a)
        for rr in (r - section / 2, r + section / 2):
            v.append((cx + rr * ca, cy + rr * sa, z))
            v.append((cx + rr * ca, cy + rr * sa, z + section))
    t0 = len(t)
    per = 4
    for k in range(seg):
        a0 = n0 + per * k
        b0 = n0 + per * ((k + 1) % seg)
        # inner, outer, front, back
        for (p, q) in ((0, 2), (2, 3), (3, 1), (1, 0)):
            t += [(a0 + p, b0 + p, b0 + q), (a0 + p, b0 + q, a0 + q)]
    g.append((name, t0, len(t)))
    return v, t, g


def portal(width=None, height=None):
    """A chamfered polygonal aperture, built as four jamb pieces around a hole.

    Built as a ring of pieces AROUND the opening, never as a slab with a hole
    laid over it. `command_control.py` shipped the slab version and sealed its
    own window inside 0.30 m of steel; an opening is a hole in something, and
    the something has to be built with the hole already in it.
    """
    p = kit.class_params("service")
    w = width or p.get("door_width_m", 1.9)
    h = height or p.get("door_height_m", 2.35)
    v, t, g = [], [], []
    hw, j, c = w / 2.0, PORTAL_JAMB_M, PORTAL_CHAMFER_M
    d = PORTAL_DEPTH_M
    # jambs
    _box(v, t, g, "alien_portal_jamb", (-hw - j, 0.0, 0.0), (-hw, h, d))
    _box(v, t, g, "alien_portal_jamb", (hw, 0.0, 0.0), (hw + j, h, d))
    # head and threshold
    _box(v, t, g, "alien_portal_head", (-hw - j, h, 0.0), (hw + j, h + j, d))
    _box(v, t, g, "alien_portal_sill", (-hw - j, -0.10, 0.0), (hw + j, 0.0, d))
    # the chamfers, as canted blocks at the head corners
    for s in (-1, 1):
        _box(v, t, g, "alien_portal_chamfer",
             (s * (hw - c), h - c, 0.0), (s * hw, h, d))
    return v, t, g, (w, h)


def barred_screen(width, height):
    """The horizontal-barred grille across a quarter's opening.

    The frame's headline feature: you look THROUGH bars into the quarter rather
    than walking into it. Horizontal bars at BAR_PITCH_M with a few vertical
    stiles, set back behind the portal face.
    """
    v, t, g = [], [], []
    hw = width / 2.0
    z0 = BAR_INSET_M
    n_bar = max(2, int(height / BAR_PITCH_M))
    for i in range(n_bar):
        y = (i + 0.5) * height / n_bar
        _box(v, t, g, "alien_bar",
             (-hw, y - BAR_H_M / 2, z0), (hw, y + BAR_H_M / 2, z0 + BAR_H_M))
    for k in range(STILES):
        x = -hw + (k + 0.5) * width / STILES
        _box(v, t, g, "alien_stile",
             (x - STILE_W_M / 2, 0.0, z0 - 0.02),
             (x + STILE_W_M / 2, height, z0 + BAR_H_M + 0.02))
    return v, t, g


def overhead_lattice(length, width, y):
    """The grille that throws the amber grid onto the deck.

    Emitted as a group of its own so the material pass can make it the room's
    light source. In the frame the floor is the brightest thing in the shot,
    and it is lit through this.
    """
    v, t, g = [], [], []
    hw = width / 2.0
    nx = max(1, int(width / LATTICE_CELL_M))
    nz = max(1, int(length / LATTICE_CELL_M))
    for i in range(nx + 1):
        x = -hw + i * width / nx
        _box(v, t, g, "alien_lattice",
             (x - LATTICE_BAR_M / 2, y - LATTICE_DROP_M, 0.0),
             (x + LATTICE_BAR_M / 2, y, length))
    for j in range(nz + 1):
        z = j * length / nz
        _box(v, t, g, "alien_lattice",
             (-hw, y - LATTICE_DROP_M, z - LATTICE_BAR_M / 2),
             (hw, y, z + LATTICE_BAR_M / 2))
    return v, t, g


def deck_grating(length, width):
    """The illuminated floor grid -- the frame's brightest surface.

    A grid of lit cells set flush into the deck, one cell per
    `GRATING_CELL_M`, separated by `GRATING_GAP_M` of dark structure. Centred
    across the gallery, so a margin of unlit deck runs along each wall: the
    frame shows exactly that, dark floor between the grating's edge and the
    piers.

    Cells are emitted one span each. Nothing merges them into one lamp because
    nothing lights them -- they ARE the emitter, and a light box is not a
    light. If a later pass ever gives this fitting a source it will get one
    lamp per cell and want merging, which `FIXTURE_MERGE_M` already does.
    """
    v, t, g = [], [], []
    nx = max(1, int(width / GRATING_CELL_M))
    nz = max(1, int(length / GRATING_CELL_M))
    x0 = -nx * GRATING_CELL_M / 2.0          # centred, so both margins match
    c = GRATING_CELL_M - GRATING_GAP_M
    for i in range(nx):
        for j in range(nz):
            cx = x0 + (i + 0.5) * GRATING_CELL_M
            cz = (j + 0.5) * GRATING_CELL_M
            _box(v, t, g, "alien_deck_grating",
                 (cx - c / 2, -GRATING_DEPTH_M, cz - c / 2),
                 (cx + c / 2, GRATING_PROUD_M, cz + c / 2))
    return v, t, g


def _to_wall(verts, wall_x, z_quarter):
    """Author-frame -> gallery left wall.

    (x across, y up, z depth) -> (-z - wall_x, y, z_quarter + x). Determinant
    +1: d/dx = (0,0,1), d/dy = (0,1,0), d/dz = (-1,0,0). A rotation, so
    winding is preserved and no flip is needed -- and the self-test checks
    that rather than taking this comment's word for it.
    """
    return [(-z - wall_x, y, z_quarter + x) for x, y, z in verts]


def _absorb(V, T, G, v, t, g, off=(0.0, 0.0, 0.0)):
    o = len(V)
    t0 = len(T)
    V.extend((x + off[0], y + off[1], z + off[2]) for x, y, z in v)
    T.extend((a + o, b + o, c + o) for a, b, c in t)
    G.extend((n, lo + t0, hi + t0) for n, lo, hi in g)


def gallery(schema, profile):
    """One gallery: the corridor, its lattice, and QUARTERS_PER_GALLERY locks."""
    V, T, G = [], [], []
    hw = GALLERY_W_M / 2.0

    # shell -- four plates round the volume
    _box(V, T, G, "alien_deck", (-hw, -0.18, 0.0), (hw, 0.0, GALLERY_LEN_M))
    _box(V, T, G, "alien_wall", (-hw - 0.22, 0.0, 0.0),
         (-hw, GALLERY_H_M, GALLERY_LEN_M))
    _box(V, T, G, "alien_wall", (hw, 0.0, 0.0),
         (hw + 0.22, GALLERY_H_M, GALLERY_LEN_M))
    _box(V, T, G, "alien_soffit", (-hw, GALLERY_H_M, 0.0),
         (hw, GALLERY_H_M + 0.22, GALLERY_LEN_M))
    _box(V, T, G, "alien_endwall", (-hw, 0.0, GALLERY_LEN_M),
         (hw, GALLERY_H_M, GALLERY_LEN_M + 0.22))

    lv, lt, lg = overhead_lattice(GALLERY_LEN_M, GALLERY_W_M, GALLERY_H_M)
    _absorb(V, T, G, lv, lt, lg)

    gv, gt, gg = deck_grating(GALLERY_LEN_M, GALLERY_W_M)
    _absorb(V, T, G, gv, gt, gg)

    # The ring fitting on the end wall.
    _torus_ring(V, T, G, "alien_ring", 0.0, GALLERY_H_M * 0.55,
                GALLERY_LEN_M - 0.05, RING_R_M, RING_SECTION_M)

    # Quarters open off the LEFT wall, each behind a two-door lock.
    depth = lock_depth_m()
    for q in range(QUARTERS_PER_GALLERY):
        z = 3.5 + q * (GALLERY_LEN_M - 7.0) / max(QUARTERS_PER_GALLERY - 1, 1)

        pv, pt, pg, (w, h) = portal()
        # The portal is authored with x across the aperture, y up and z into
        # the depth; on the gallery's left wall that becomes
        #   (x, y, z) -> (-z - wall, y, z_quarter + x)
        # whose determinant is +1, so it is a rotation and needs no winding
        # flip. Asserted in `_selftest` rather than argued here -- `plant.py`
        # shipped a -1 remap with no flip and rendered every surface inside-out.
        _absorb(V, T, G, _to_wall(pv, hw, z), pt, pg)
        # inner door, one lock depth outboard
        _absorb(V, T, G, _to_wall(pv, hw + depth, z), pt, pg)

        # the vestibule walls between them
        _box(V, T, G, "alien_lock_wall",
             (-hw - depth, 0.0, z - w / 2 - PORTAL_JAMB_M),
             (-hw, GALLERY_H_M, z - w / 2))
        _box(V, T, G, "alien_lock_wall",
             (-hw - depth, 0.0, z + w / 2),
             (-hw, GALLERY_H_M, z + w / 2 + PORTAL_JAMB_M))
        _box(V, T, G, "alien_lock_soffit",
             (-hw - depth, h, z - w / 2 - PORTAL_JAMB_M),
             (-hw, GALLERY_H_M, z + w / 2 + PORTAL_JAMB_M))

        # The barred screen, BEYOND the inner door's far face.
        #
        # First placement put it 50 mm behind the inner portal's near face,
        # which sits it INSIDE that portal's own 0.55 m reveal -- the jambs
        # occluded it and the render showed an empty dark aperture where the
        # frame's headline feature should be. A screen inside a jamb is not a
        # screen. It now clears the full portal depth.
        bv, bt, bg = barred_screen(w, h)
        _absorb(V, T, G,
                _to_wall(bv, hw + depth + PORTAL_DEPTH_M, z), bt, bg)

        # breather-mask dispenser beside the outer door
        _box(V, T, G, "alien_mask_dispenser",
             (-hw, 0.95, z + w / 2 + PORTAL_JAMB_M + 0.15),
             (-hw + DISPENSER_D_M, 0.95 + DISPENSER_H_M,
              z + w / 2 + PORTAL_JAMB_M + 0.15 + DISPENSER_W_M))

        # The quarter shell behind the screen. Closed, so the grille reads as
        # containment rather than as a hole.
        x_scr = -hw - depth - PORTAL_DEPTH_M - BAR_INSET_M - BAR_H_M
        _box(V, T, G, "alien_quarter_shell",
             (x_scr - QUARTER_DEPTH_M, -0.18, z - w / 2 - PORTAL_JAMB_M),
             (x_scr, GALLERY_H_M, z + w / 2 + PORTAL_JAMB_M))

        # green status lamp per lock
        _box(V, T, G, "alien_status_lamp",
             (-hw, h + 0.12, z - GREEN_LAMP_R_M),
             (-hw + 0.06, h + 0.12 + 2 * GREEN_LAMP_R_M, z + GREEN_LAMP_R_M))

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

    # --- the mechanic is canon, and read rather than restated -------------
    check("six atmospheres, from the authority-1 board",
          atmospheres_available() == 6, str(atmospheres_available()))
    cls = atmosphere_classes()
    check("atmosphere classes come from the NPC layer, not a second copy",
          all(c in (sched.ATMOS_STANDARD, sched.ATMOS_HUMID,
                    sched.ATMOS_METHANE, sched.ATMOS_UNDISCLOSED) for c in cls),
          str(cls))
    # The classes must not EXCEED the board's six. Fewer is fine -- the board
    # says six are available, not that we have modelled all six.
    check("the modelled classes do not exceed the six the board claims",
          len(cls) <= atmospheres_available(),
          f"{len(cls)} classes vs {atmospheres_available()} atmospheres")
    check("no atmosphere is given a number this project cannot source",
          not any(any(ch.isdigit() for ch in c) for c in cls),
          "only HUMAN/02 is numbered on any prop we hold")

    # --- the lock is derived, not chosen ----------------------------------
    d = lock_depth_m()
    check("a lock is deep enough for a suited occupant clear of both leaves",
          d >= SUIT_DEPTH_M + 2 * LOCK_CLEAR_M,
          f"{d:.2f} m for a {SUIT_DEPTH_M} m suit")
    check("the lock depth is derived from the suit, not a constant",
          abs(d - (SUIT_DEPTH_M + 2 * LOCK_CLEAR_M + 2 * PORTAL_DEPTH_M)) < 1e-9)
    # A lock with a single door is not a lock. This is the geometric form of
    # "six independently conditioned volumes".
    V, T, G = gallery(schema, profile)
    names = [n for n, _lo, _hi in G]
    check("every quarter has TWO doors, because one door is not a lock",
          names.count("alien_portal_jamb") == QUARTERS_PER_GALLERY * 2 * 2,
          f"{names.count('alien_portal_jamb')} jambs for "
          f"{QUARTERS_PER_GALLERY} quarters")

    # --- the frame's headline feature --------------------------------------
    check("the quarter openings are barred, as the frame shows",
          "alien_bar" in names and "alien_stile" in names,
          "you look THROUGH bars into a quarter")
    n_bar = names.count("alien_bar")
    check("there are enough bars to read as a screen",
          n_bar >= QUARTERS_PER_GALLERY * 4, f"{n_bar} bars")
    check("the overhead lattice exists to throw the amber grid",
          "alien_lattice" in names)
    check("the far-wall ring fitting is present", "alien_ring" in names)

    # --- layer 4: the room has a cast source and a lit deck ----------------
    # These fail if either fitting is deleted, renamed, or moved off the table
    # the light rig reads. Before this pass the gallery had no source of any
    # kind: its lattice was bound to an office partition material and rendered
    # as a grey corridor at 2.84x its reference frame.
    # `.get` rather than `[...]`, so deleting the entry REPORTS a failure
    # instead of raising out of the middle of the self-test. A guard that
    # crashes tells you less than one that prints.
    lat = CAST_FITTINGS.get("alien_lattice", {})
    check("the overhead grille is the fitting the light rig hangs on",
          set(CAST_FITTINGS) == {"alien_lattice"}
          and "alien_lattice" in names, str(sorted(CAST_FITTINGS)))
    check("it is a spot, because the frame's shafts descend vertically",
          lat.get("kind") == "spot", str(lat.get("kind")))
    check("its reach is derived from this gallery, not borrowed from a bay",
          abs(lat.get("range_m", 0.0)
              - round(math.hypot(GALLERY_H_M, GALLERY_W_M / 2), 1)) < 0.06,
          f"{lat.get('range_m')} m against "
          f"{math.hypot(GALLERY_H_M, GALLERY_W_M / 2):.2f} m to the far "
          f"corner of the deck")
    check("its cone reaches the walls without lighting their feet",
          0.0 < lat.get("angle_deg", 0.0)
          < math.degrees(math.atan2(GALLERY_W_M / 2, GALLERY_H_M)),
          f"{lat.get('angle_deg')} deg against "
          f"{math.degrees(math.atan2(GALLERY_W_M / 2, GALLERY_H_M)):.1f} deg "
          f"wall to wall")
    n_cell = names.count("alien_deck_grating")
    check("the deck is an illuminated grating, the frame's brightest surface",
          n_cell == (int(GALLERY_W_M / GRATING_CELL_M)
                     * int(GALLERY_LEN_M / GRATING_CELL_M)),
          f"{n_cell} cells")
    # The floor is bright and it lights nothing -- the third instance of that
    # finding in this project. Asserting it stops a later pass from "fixing"
    # a dark room by turning the floor into a lamp.
    check("and it is EMISSIVE ONLY, which is measured, not forgotten",
          "alien_deck_grating" not in CAST_FITTINGS,
          "the pier feet either side of it are the darkest thing in the frame")
    check("the grating leaves a dark margin at each wall, as the frame shows",
          int(GALLERY_W_M / GRATING_CELL_M) * GRATING_CELL_M
          < GALLERY_W_M - 0.2,
          f"{GALLERY_W_M - int(GALLERY_W_M / GRATING_CELL_M) * GRATING_CELL_M:.2f} m of margin")
    check("its cell is the module's own lattice cell, not a new number",
          GRATING_CELL_M == LATTICE_CELL_M and GRATING_GAP_M == LATTICE_BAR_M,
          f"{GRATING_CELL_M} m cell, {GRATING_GAP_M} m gap")
    # Every screen must have a quarter behind it. Without one the bars open on
    # void, and a render cannot tell that from a hole in the geometry.
    check("every barred screen has a quarter behind it",
          names.count("alien_quarter_shell") == QUARTERS_PER_GALLERY,
          f"{names.count('alien_quarter_shell')} shells for "
          f"{QUARTERS_PER_GALLERY} screens")
    check("breather-mask dispensers, one per lock",
          names.count("alien_mask_dispenser") == QUARTERS_PER_GALLERY,
          f"{names.count('alien_mask_dispenser')}")

    # --- geometry ---------------------------------------------------------
    check("the gallery builds", len(T) > 800, f"{len(T)} triangles")
    check("every triangle is grouped",
          sum(hi - lo for _n, lo, hi in G) == len(T))

    xs = [q[0] for q in V]
    ys = [q[1] for q in V]
    zs = [q[2] for q in V]
    # Locks project OUTBOARD of the gallery wall by exactly one lock depth
    # plus the screen inset -- anything further has escaped the sector.
    # Derived from what is actually placed outboard, not a padded guess. The
    # first version added a flat 0.25 m and failed by 20 mm the moment the
    # barred screen moved clear of the inner portal -- the assertion doing its
    # job, but a limit built from a magic number cannot say WHY it was
    # exceeded. This one can.
    limit = (GALLERY_W_M / 2 + d + PORTAL_DEPTH_M
             + BAR_INSET_M + BAR_H_M + QUARTER_DEPTH_M + 0.05)
    check("nothing escapes past the lock vestibules",
          min(xs) >= -limit, f"x min {min(xs):.2f} vs limit {-limit:.2f}")
    check("nothing is below the deck or above the soffit",
          min(ys) >= -0.20 and max(ys) <= GALLERY_H_M + 0.30,
          f"y {min(ys):.2f}..{max(ys):.2f}")
    check("nothing escapes the gallery longitudinally",
          min(zs) >= -0.05 and max(zs) <= GALLERY_LEN_M + 0.30,
          f"z {min(zs):.2f}..{max(zs):.2f}")

    # The gallery is a SERVICE corridor, not a public street -- the frame is
    # dim, tight and industrial, not a concourse.
    p = kit.class_params("service")
    check("the gallery is service class, not concourse",
          abs(GALLERY_W_M - p["corridor_width_m"]) < 1e-9,
          f"{GALLERY_W_M} m vs service {p['corridor_width_m']} m")

    # --- winding ----------------------------------------------------------
    bv, bt, bg = [], [], []
    _box(bv, bt, bg, "probe", (0, 0, 0), (1, 2, 3))
    check("primitives are wound outward", _signed_volume(bv, bt) > 0)
    # And on a PLACED solid. plant.py passed the local test and shipped every
    # surface inside-out because its placement map had determinant -1.
    check("the wall remap preserves handedness, so placed solids stay outward",
          _signed_volume(_to_wall(bv, 2.1, 11.0), bt) > 0,
          f"{_signed_volume(_to_wall(bv, 2.1, 11.0), bt):.3f}")
    check("the winding test can fail",
          _signed_volume(bv, [(a, c, b) for a, b, c in bt]) < 0)

    print(f"\nalien sector gallery: {GALLERY_LEN_M:.0f} x {GALLERY_W_M} x "
          f"{GALLERY_H_M} m, {QUARTERS_PER_GALLERY} locks at {d:.2f} m deep, "
          f"{len(T):,} triangles")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
