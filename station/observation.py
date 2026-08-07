#!/usr/bin/env python3
"""The observation rooms -- the two Blue domes and the Green rotundas.

Three register places, one module, three PROGRAMS, and the programs are read
off the register rather than chosen:

    obs_dome_1    blue/0/0    0 deg  z7960  26 x 44 m   PLC-002
    obs_dome_2    blue/0/0   90 deg  z7960  20 x 36 m   PLC-030
    obs_rotundas  green/0/0  96 deg  z4200  12 x 30 m   PLC-064

All three are owned by `components.py` in the register, and `components.py`
builds the EXTERIOR -- every one of its builders emits a ring of instances in
station coordinates, and standing under an `observation_dome` at its own base
plane **0 of its 192 triangles face the viewer**. `dome_mesh` says so itself:
*"the base sits inside the hull and the hole faces away from every camera"*.
These are blisters ON a hull. `bespoke.py`'s own audit block nominated exactly
these three as *"the three worth building"* and said what each needs: *"an
observation room is a FLOOR, a WINDOW RING and a DOME WITH THICKNESS"*.

Until this module existed a player walked into any of the three and found a
generic bay -- an 8.0 x 6.3 m store room where the station's windows are.

SOURCES
-------
**`reference/05-sector-green/rotunda.webp`, authority 1** -- a domed circular
chamber ringed with windows, and the richest single interior frame in
`00-INDEX`. What it establishes and what is built from it:

  * **At least eight columns across the far arc, evenly spaced. "A closed ring
    at that spacing implies roughly sixteen bays."**
  * **Column order: a plain slightly tapered cylindrical shaft carrying a group
    of THREE narrow ring collars, then a longer plain shaft, then a short
    stepped capital under the entablature.** The same order appears on the
    Garden's civic building in `garden.png`, which is a second frame.
  * **A corbel course of stepped rectangular blocks in layered tiers** above the
    columns, then a **smooth warm gold-bronze dome with broad radial ribs**.
  * **Two pale conical elements standing on the cornice**, upper left.
  * **A continuous band of narrow pale vertical slats at about waist height**
    running right around the room, lit so it reads as a bright ribbon.
  * **Four hanging banners**, long vertical cloths with the sigil in the lower
    third.
  * **Tall blue backlit lattice panels** flanking the room left and right.
  * **A flight of about ten pale steps rising to a dark portal**, flanked by
    piers whose lower ends carry **a comb of vertical slots**; handrail left.
  * **A dark plinth lectern with a sloping cyan-glowing top**, the glow divided
    by dark bars into a symmetrical chevron figure.
  * **A radiating sunburst mosaic floor** -- triangular radial wedges about a
    centre and a broad concentric band of chevrons at larger radius.

**`reference/03-sector-blue/comand and contorl.webp`, authority 1** -- the
dome glazing seen FROM INSIDE, which is what LOCATIONS.md §169 records at
authority 1: *"a large circle on radial spoke mullions with a broad concentric
ring band, set in a flat-panelled bulkhead with angled bracing"*. That is the
dome programs' window, and `command_control.py` already builds the same
element for C&C's own bulkhead -- so the two must agree, and the mullion count
is READ from `components.DOME_MULLIONS` rather than restated here.

THE ONE THING THE SPEC AND THE GAZETTEER DISAGREE ABOUT, carried visibly.
`LOCATIONS.md` §241 records the rotundas' facing as **unresolved** -- *"if the
domed rotunda above is one of these, they face inward across the drum, not
outward at space"* -- and `00-INDEX` reads the frame as drum-interior *"with
the caveat stated"*. `docs/spec/PLACES.md` PLC-064 is the content authority and
says **"facing OUT at space"**. This module follows the spec for the GLAZING
and the auth-1 frame for the ARCHITECTURE, which is the only split that uses
both sources honestly. Nothing here decides C-003.

SESSION 4m -- `obs_rotundas` IS BEING GRADED AGAINST A DIFFERENT ROOM'S FRAME,
AND THAT IS WHY ITS LIGHTING CANNOT PASS
---------------------------------------------------------------------
`tools/measure_frame.py --against reference/05-sector-green/rotunda.webp`
scores this place median x0.51, p5 x1.58 FAIL, p95 x0.23 FAIL, p5/p95 x6.79
FAIL. The p95 miss IS the whole gap and it is a WINDOW: that reference frame's
95th percentile is 0.7906 and its bright population is the band of glazing,
which reads linear Y 0.42-0.55 across three clean bays against the room's own
lit wall at 0.053 -- **the pane is 9.4x the wall it is set in**.

`docs/spec/PLACES.md` says those are not this room's windows. PLC-063
`domed_rotunda` is "stepped gold coffered dome, INWARD DRUM-FACING WINDOWS,
alien-sigil banners, blue altar table (auth 1 dressing)" and its CHECK is "the
windows show the true drum interior". PLC-064 -- this place -- is "the
4-rotunda class (canon count), **facing OUT at space**", its viewports are
"T1 -- starfield + gate bearing true", and its CHECK wants "one of them
planetward: Epsilon III below". PLC-063 states the split is deliberate:
"facing question resolved inward for this one, outward for PLC-064, splitting
the canon ambiguity visibly".

So `rotunda.webp` is PLC-063's frame. Measuring PLC-064 against it asks a
gallery looking at vacuum to match a chapel looking at a sunlit habitat, and
**no exposure, ambient or fitting change in this module can close a x0.23 p95
that is made of daylight this room does not have.** The pairing was tried:
binding `prop_viewport` to a measured drum-daylight material (emission
(1.000,0.952,0.923) at energy 0.62) took p95 x0.23 -> x0.54 and p5/p95
x6.79 -> x3.31, both to PASS, in one change -- and it is REVERTED, because
`prop_viewport` is one group shared with PLC-063 and PLC-065 and lighting it
globally decides C-003, which is OPEN and BLOCKING. See the block on
`materials.viewport_glazing`'s bind list.

WHAT IS WRONG HERE INDEPENDENTLY OF THE REFERENCE, and it is the same defect
`docking_bay` had. Summing Godot's own attenuation over every source on the
working plane -- the measurement recorded above `tools/export_scene.py`'s
BESPOKE_EXPOSURE -- gives:

    corridor (the anchor)   24 sources   3.3 x  22.1 m   mean E 4.2641
    docking_bays            39 sources  42.5 x 141.5 m   mean E 1.9026
    obs_rotundas             1 source   14.4 x  17.9 m   mean E 0.0044

**970x under the anchor, from ONE source.** This module emits four light
groups and three of them cast nothing: `light_pilaster_strip` (1,260
triangles, the largest fitting in the room), `light_portal_head` and
`light_bar_backlight` are all absent from `FIXTURE_LIGHTING` and are emissive
only. The single caster is `light_dais_key`, 12 triangles, and
`export_scene.room_reach` has stretched its 9 m measured range to 27 m -- the
REACH_CAP -- to report 100% floor coverage, which is the rig saying out loud
that it has no sources. The room is therefore lit by `ambient_energy` 1.300,
the residential corridor's full calibrated fill, because `ambient_energy`
hands every module-owned place `AMBIENT_CALIBRATED_RATIO`.

NOT FIXED HERE, deliberately: the remedy is sources, and the reference frame
names them -- "a continuous band of narrow pale vertical slats ... **lit so it
reads as a bright ribbon**" and "tall blue **backlit** lattice panels", which
is `alien_sector`'s own ruling that a diffuser is not the source. But that
overturns a measured `emissive_only` decision, and the only frame available to
verify the result against is the wrong room's. Pick the reference first.

WHAT IS EXTRAPOLATED -- INV-291 (the rotunda) and INV-292 (the domes)
---------------------------------------------------------------------
Every absolute dimension. The frames give proportions against robed figures
and against a standing officer, not metres. See the constants: each one is
derived from something already fixed in this project -- the register's own
footprint, `rooms.PROPS['viewport']`, `rooms.WALK_M`, INV-010's 3.6 m deck
pitch -- rather than picked.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior_kit as kit                                      # noqa: E402
import rooms as _rooms                                          # noqa: E402
import bespoke as _bsp                                          # noqa: E402

DECK_PITCH_M = 3.6          # INV-010. Named, not re-derived.
WALL_T_M = _rooms.WALL_T_M  # 0.18

# ---------------------------------------------------------------------------
# THE BAY MODULE -- INV-291/292, and it is derived twice over
# ---------------------------------------------------------------------------
# A window bay has to hold a viewport and leave a pier a person can pass
# between two of them, so its width is `rooms.PROPS['viewport'][0]` plus
# `rooms.WALK_M`. Both are already fixed elsewhere in this project, so the
# module changes if either does instead of drifting from them.
VIEWPORT_W_M = _rooms.PROPS["viewport"][0]          # 2.4
VIEWPORT_H_M = _rooms.PROPS["viewport"][2]          # 1.4
DOME_BAY_M = VIEWPORT_W_M + _rooms.WALK_M           # 3.30

# THE ROTUNDA'S BAY IS THE REGISTER'S OWN, AND IT AGREES WITH THE FRAME. The
# `obs_rotundas` row is a CLASS row for four rotundas over 12 degrees at radius
# 281.9 m -- 59.0 m of arc, so 14.75 m of frontage each. A chamber of that
# outside width with `WALL_T_M` walls has an interior radius of 7.0 m, whose
# circumference over the frame's counted SIXTEEN bays is 2.75 m a bay.
#
# That is two independent derivations landing on the same number: the
# register's arc share, and a bay wide enough for the frame's colonnade at a
# robed figure's scale. Neither was fitted to the other.
ROTUNDA_BAYS = 16
ROTUNDA_R_M = 7.00
ROTUNDA_BAY_M = math.tau * ROTUNDA_R_M / ROTUNDA_BAYS           # 2.749

# Heights. Both of the rotunda's two are INV-010's deck pitch, which is the
# same rule INV-020 used to make the concourse two decks tall: a window that
# occupies exactly the first deck, and a crown at exactly the second.
ROT_SILL_M = 1.20           # the solid dado under the glazing, a leaning height
ROT_HEAD_M = DECK_PITCH_M                       # 3.60
ROT_ENTAB_M = DECK_PITCH_M * 1.20               # 4.32, the entablature top
ROT_CROWN_M = DECK_PITCH_M * 2.0                # 7.20
ROT_SLAT_M = 1.05           # the pale vertical slat band -- waist on a 1.75 m
ROT_SLATS_PER_BAY = 7       # "narrow pale vertical slats", counted off the frame
ROT_COLLARS = 3             # "a group of THREE narrow ring collars"
ROT_CORBEL_TIERS = 3        # "stepped rectangular blocks in layered tiers"
ROT_BANNERS = 4             # "four hanging banners"
ROT_LATTICE = 2             # "tall blue backlit lattice panels ... left and right"
ROT_STEPS = 10              # "a flight of about ten pale steps"
ROT_CONES = 2               # "two pale conical elements stand on the cornice"

# The dome programs. Radius is the bay module times the place's OWN declared
# viewport count, which is what makes dome 1 and dome 2 different rooms rather
# than one room at two scales -- PLC-002 lists 12 viewports, PLC-030 lists 8.
DOME_WALL_M = DECK_PITCH_M          # the ring wall is one deck; the dome is above
DOME_RISE_FRAC = 0.75               # a shallow cap, not a hemisphere -- the C&C
                                    # frame's glazing is a broad shallow circle
GALLERY_WELL_FRAC = 0.55            # dome 1's central well, as a fraction of R

# THE VESTIBULE. A round room has no flat face for a corridor to arrive at, and
# `bespoke.room_shell` puts the near face on the assembler's plane and
# `near_face_opening` measures the widest way in across it. So the chamber is
# entered through a short passage, which is also how you enter a rotunda.
# Its width is `bespoke.DOOR_HALF_W_M` doubled plus a wall either side, so the
# aperture the assembler probes is the passage itself; its length is
# `bespoke.APPROACH_DEPTH_M` plus a stride, so a body is standing in the
# passage rather than in its own doorway before the chamber opens up.
VEST_HALF_W_M = _bsp.DOOR_HALF_W_M + 0.45
VEST_L_M = _bsp.APPROACH_DEPTH_M + 1.40
VEST_H_M = kit.PROVISIONAL["door_height_m"] + 0.80

# ---------------------------------------------------------------------------
# THE PALETTE -- INV-950, and it is the single largest thing that was wrong
# ---------------------------------------------------------------------------
# `reference/05-sector-green/rotunda.webp`, authority 1, read again in session
# 4t rather than from the summary above it: **the room is DARK WARM BRONZE and
# the dome is GOLD**. The wall below the window band, the columns and the
# corbel tiers are warm brown-bronze; the floor mosaic is cream and ochre; the
# two flanking lattice panels are DEEP BLUE and so is the lectern's glowing
# top. There is no grey anywhere in that frame.
#
# What this module built is grey, and not by choice -- by NAMING. Every
# `worship_*` and `transit_*` group in `materials.py` resolves to exactly three
# materials: `shell_wall_panel` 0.455, `shell_rib_painted` 0.469 and
# `shell_deck_stone` 0.400. Wall, dado, cornice, panel, skirt, rail, mullion
# and rib are EIGHT names for ONE value. So however the room is modelled it
# comes out one flat grey, which is `docs/AAA-STANDARD.md` CRAFT 3 verbatim --
# *"materials exist as groups but carry one flat value each"* -- and it is why
# round 1 read the rotunda as *"grey-on-grey at half distance"*.
#
# `materials.py` is not this session's file and `export_scene.py` is not
# either. The lever that IS inside this one is that **`materials.resolve_any`
# matches by PREFIX**: a group named `<bound_name>_<shell_suffix>` takes the
# bound name's material, and `rooms._SHELL_SUFFIXES` still classes it as SHELL,
# so it does not become a collision box a player walks into. `dress_kerb_rib`
# -- already in this file for the dome ribs, with its reason written beside it
# -- is the existing instance of the idiom; this block is the same trick
# applied to the whole surface instead of to one part.
#
# Each pick names the clause of the frame it answers and the measured value it
# resolves to. Nothing here invents a colour: every value was measured into
# `materials.py` by another session, and the choice is which measured value the
# reference asks for.
M_WALL = "zoc_rail_wall"                   # 0.290,0.145,0.084 r0.42 met0.15
#   "the wall below the window band is dark warm brown" -- the one warm brown
#   in the library, measured off the Zocalo's own handrail.
M_WALL_UP = "dress_furnace_panel"          # 0.215,0.198,0.190 r0.78
#   the darker storey above the entablature. The scorched roughness is what
#   stops the upper wall reading as the same paint as the lower one.
M_PIER = "dress_post_rib"                  # 0.300,0.255,0.242 r0.52 met0.30
#   column shafts and stair piers: bronze structure, part-metallic, so it takes
#   a highlight where the flat shell material takes none.
M_BRONZE = "prop_deck_marking_rib"         # 0.405,0.299,0.308 r0.58 met0.00
#   "a group of THREE narrow ring collars" and the capitals. In the frame the
#   collars are distinctly LIGHTER than the shaft they ring, which is the whole
#   reason the order reads at all against a bright window.
#
#   AND IT MAY NOT BE A SMOOTH METAL, which cost a render to learn and is the
#   one real constraint on this whole palette. The first pick was
#   `zoc_table_edge` -- 0.600,0.510,0.458 at metallic 0.85 and roughness 0.30 --
#   and at arm's length the three collars rendered BLACK. `interior.tscn` sets
#   `reflected_light_source = 1`, which is DISABLED, and a smooth metal with no
#   environment to reflect integrates to nothing; `station/vista.py`'s header
#   records the identical mechanism for the glazing. Rough metals survive it
#   (`furn_shop_steel` at 0.58 does not go black); smooth ones do not. **Read a
#   material's metallic AND its roughness before putting it on trim a player
#   can get close to.**
M_GOLD = "dress_kerb_rib"                  # 0.900,0.720,0.060 r0.62
#   "a smooth warm gold-bronze dome with broad radial ribs". Already this
#   file's choice; kept, and now it has a dome field to sit against.
M_STONE = "prop_level_plaque_panel"        # 0.391,0.379,0.321 r0.72
#   the cream of the sunburst floor and of the pale corbel tiers.
M_STONE_D = "zoc_deck_chevron_deck_joint"  # 0.265,0.262,0.209 r0.34
#   "a broad concentric band of chevrons at larger radius" -- the darker ochre
#   the chevrons are laid in.
M_RECESS = "prop_planter_panel"            # 0.094,0.092,0.093 r0.24
#   every shadow gap, coffer ground and reveal. A recess the same value as the
#   thing it is cut into is not a recess.
M_METAL = "zoc_stall_post_conduit"         # 0.420,0.418,0.412 r0.75 met0.00
#   service risers and cable runs -- CRAFT 4's "a fitting is where a fitting
#   would be needed".
M_GRILLE = "zoc_chair_frame_mullion"       # 0.075,0.074,0.074 r0.32
#   the dark lattice in FRONT of the backlight. See `_lattice_panel`.
M_CLOTH_B = "prop_gaming_table_panel"      # 0.138,0.276,0.483 r0.95
M_CLOTH_P = "prop_stall_panel"             # 0.380,0.345,0.312 r0.92
#   "four hanging banners". The frame shows two dark blue-violet and two pale,
#   and they are matte cloth: both of these are cloth at r 0.92-0.95.
M_SIGIL = "sign_text_panel"                # em 1.000,0.970,0.620 ee 0.9
#   the sigil in the lower third, IN RELIEF. Round 1's C1 finding was that the
#   banner was "a lit rectangle standing in for a named object"; a figure at
#   ee 0.9 is a figure, and 0.9 does not blow the way `signage_panel`'s 3.0 did.
M_GLOW_B = "prop_shrine_panel"             # em 0.240,0.320,1.000 ee 2.2
#   the backlit blue behind the lattice, and the lectern's sloping top. The
#   frame's lectern glow is BLUE; this module had it warm at ee 6.0 and it read
#   as a white hole in the middle of the room.
M_RIBBON = "alien_frost_panel"             # em 0.691,0.760,1.000 ee 0.55
#   "a continuous band of narrow pale vertical slats ... lit so it reads as a
#   bright ribbon". `light_pilaster_strip` is ee 0.23 and reads as paint.
L_COVE = "light_house_cove"                # CASTS: omni, 1.000,0.966,0.944,
#   energy_rel 0.35, range 18.0 m -- it is in `export_scene.FIXTURE_LIGHTING`,
#   which is the whole point. See `_cove_ring`.
L_BLUE = "cc_light_strip"                  # CASTS: omni, 0.243,0.546,1.000,
#   energy_rel 0.44, range 3.5 m. C&C's own measured strip, and the rotunda's
#   blue is the same blue.

# THE OVERLAP RULE -- INV-951, and it is why the non-manifold count was 489.
# Two closed solids that ABUT on an exact plane weld into edges used by four
# triangles. `_prism` is closed and correctly wound every time, so no gate
# fired: the ring wall's fifteen bays shared fourteen radial faces, the head
# reveal shared its top face with the wall above it, and every stair tread
# shared its riser with the next. Session 3x rebuilt `portal_frame` for exactly
# this and got 8,832 FEWER triangles, because coincident faces are geometry
# nobody can see. The cure is one constant used wherever two solids meet:
# solids OVERLAP by `LAP_M`, or they are separated by a reveal. They never
# abut. `_selftest` gates the count at zero and the control is in this file.
# The palette's own names, in one list, so `_selftest`'s control can withdraw
# it and count what is left. A control that names the constants somewhere else
# is a second copy of the palette.
_PALETTE = ("M_WALL", "M_WALL_UP", "M_PIER", "M_BRONZE", "M_GOLD", "M_STONE",
            "M_STONE_D", "M_RECESS", "M_METAL", "M_GRILLE", "M_CLOTH_B",
            "M_CLOTH_P", "M_SIGIL", "M_GLOW_B", "M_RIBBON", "L_COVE",
            "L_BLUE", "D_FRAME", "D_PALE", "D_TRIM", "D_DECK")

LAP_M = 0.02
# The angular half-gap between two ring segments. At the rotunda's r = 7.00 m,
# 0.010 rad is 70 mm -- a reveal a person sees, not a tolerance.
GAP_A = 0.010


def _dome_mullions():
    """The dome's radial spoke count, READ from the exterior component.

    INV-024's window and this room's window are the same piece of glass seen
    from two sides, and `components.DOME_MULLIONS` is where that count lives --
    measured off the C&C frame and corroborated by `rotunda.webp`'s *"at least
    eight columns across the far arc ... roughly sixteen bays"*. Restating it
    would be a second copy of a measurement.
    """
    try:
        import components as _c                                 # noqa: PLC0415
        n = int(getattr(_c, "DOME_MULLIONS", 16))
        return n if n >= 4 else 16
    except Exception:                                           # noqa: BLE001
        return 16


# ---------------------------------------------------------------------------
# Primitives. Closed at both ends, every time.
# ---------------------------------------------------------------------------
def _box(v, t, g, name, lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    if z1 < z0:
        z0, z1 = z1, z0
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    g.append((name, t0, len(t)))
    return v, t, g


def _prism(v, t, g, name, quad, y0, y1):
    """A closed vertical prism on a 4-point (x, z) footprint.

    The wall segments, piers, banners and lattice panels of a round room are
    all trapezia in plan -- a box cannot make one, and four boxes meeting at a
    mitre share coincident faces, which is the defect `portal_frame` shipped
    for a session (828 non-manifold edges a deck).
    """
    # Normalise the winding so the sides face outward. Signed area in (x, z):
    # positive means the fan would face DOWN -- see `interior_kit.deck_pad`.
    n = len(quad)
    a2 = sum(quad[i][0] * quad[(i + 1) % n][1] - quad[(i + 1) % n][0] * quad[i][1]
             for i in range(n))
    if a2 > 0.0:
        quad = quad[::-1]
    base = len(v)
    t0 = len(t)
    v.extend((x, y1, z) for x, z in quad)
    v.extend((x, y0, z) for x, z in quad)
    for i in range(1, n - 1):
        t.append((base, base + i, base + i + 1))                # top, up
        t.append((base + n, base + n + i + 1, base + n + i))    # bottom, down
    for i in range(n):
        j = (i + 1) % n
        t.append((base + i, base + n + i, base + n + j))
        t.append((base + i, base + n + j, base + j))
    g.append((name, t0, len(t)))
    return v, t, g


def _revolve(v, t, g, name, profile, seg, y_off=0.0):
    """A closed solid of revolution about +Y from a CLOSED meridian polygon.

    `profile` is [(r, y), ...] traversed so the material lies to its left when
    walking the meridian in the (r, y) half-plane. Points with r == 0 are the
    axis and become a single shared apex vertex rather than a ring of
    coincident ones -- a degenerate ring is a fan of zero-area triangles, which
    is geometry that renders as nothing and confuses every closure measurement
    that welds by position.
    """
    n = len(profile)
    rings = []
    for r, y in profile:
        if r <= 1e-9:
            rings.append([len(v)])
            v.append((0.0, y + y_off, 0.0))
        else:
            ring = []
            for k in range(seg):
                a = math.tau * k / seg
                ring.append(len(v))
                v.append((r * math.cos(a), y + y_off, r * math.sin(a)))
            rings.append(ring)
    t0 = len(t)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(seg):
            k2 = (k + 1) % seg
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                t.append((a[0], b[k], b[k2]))
            elif len(b) == 1:
                t.append((a[k2], a[k], b[0]))
            else:
                t.append((a[k], b[k], b[k2]))
                t.append((a[k], b[k2], a[k2]))
    g.append((name, t0, len(t)))
    return v, t, g


def _cyl(v, t, g, name, cx, cz, y0, y1, r0, r1=None, seg=12):
    """A capped cone/cylinder. Both ends closed -- see `hospitality._cyl`."""
    r1 = r0 if r1 is None else r1
    n0 = len(v)
    for k in range(seg):
        a = math.tau * k / seg
        c, s = math.cos(a), math.sin(a)
        v.append((cx + r0 * c, y0, cz + r0 * s))
        v.append((cx + r1 * c, y1, cz + r1 * s))
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
    if pt:
        _merge(v, t, g, name, [(x, y, z) for x, y, z in pv], pt)
    return v, t, g


def _ring_quad(r0, r1, a0, a1):
    """The (x, z) trapezium of one annular sector -- a wall segment in plan."""
    return [(r0 * math.cos(a0), r0 * math.sin(a0)),
            (r1 * math.cos(a0), r1 * math.sin(a0)),
            (r1 * math.cos(a1), r1 * math.sin(a1)),
            (r0 * math.cos(a1), r0 * math.sin(a1))]


# ---------------------------------------------------------------------------
# The program, read off the register
# ---------------------------------------------------------------------------
# THE PLACE, NOT THE MODULE. Session 4h: `BESPOKE_GEOMETRY` entries that threw
# `q` away drew one room for every place that reached them, and `components`
# owns NINE places of which only these three are rooms at all. So the table
# entry dispatches by place key (`bespoke.BESPOKE_PLACES`) and refuses the
# other six by name, and this function turns the place into a program.
PROGRAMS = {
    # PLC-002. The dome C&C sits inside: glazing ribs, gallery ring, service
    # crawl. NOT a second C&C -- `command_control.py` builds the console pit
    # and this builds the ring GALLERY round its light well, which is the
    # room the spec actually describes.
    "obs_dome_1": {
        "kind": "dome", "viewports": 12, "well": True, "benches": 0,
        "ladders": 2, "shutters": True, "consoles": 1,
        "note": "C&C's dome: gallery ring, service crawl, shutter gear",
    },
    # PLC-030. Function unstated in canon; LOCATIONS P-11 adopts a traffic
    # annexe plus public gallery, and PLACES.md carries it at auth 5.
    "obs_dome_2": {
        "kind": "dome", "viewports": 8, "well": False, "benches": 6,
        "ladders": 0, "shutters": False, "consoles": 2,
        "note": "the traffic annexe and public gallery (P-11)",
    },
    # PLC-064. The four-rotunda class row.
    "obs_rotundas": {
        "kind": "rotunda", "viewports": 8, "benches": 4,
        "note": "the Minbari-order ceremonial rotunda of rotunda.webp",
    },
}


def program(place=None):
    """Which of the three this is. `place=None` gives the rotunda reference."""
    key = "obs_rotundas" if place is None else place.get("key")
    if key not in PROGRAMS:
        raise KeyError(
            f"observation.py has no program for {key!r}. It builds "
            f"{sorted(PROGRAMS)}; the other six `components` places are "
            f"exterior structures -- see the audit block in bespoke.py.")
    p = dict(PROGRAMS[key])
    p["key"] = key
    p["fn"] = frozenset((place or {}).get("functions") or ())
    p["interacts"] = tuple((place or {}).get("interacts") or ("viewport",))
    if p["kind"] == "dome":
        p["r"] = DOME_BAY_M * p["viewports"] / math.tau
        p["bays"] = p["viewports"]
        p["bay"] = DOME_BAY_M
    else:
        p["r"] = ROTUNDA_R_M
        p["bays"] = ROTUNDA_BAYS
        p["bay"] = ROTUNDA_BAY_M
    return p


def room(schema=None, profile=None, place=None):
    """One observation room: x across, y up, z along, deck at y = 0.

    Authored with the way IN at MAXIMUM z. The chamber is centred on the
    origin and the vestibule runs out to +z, so `bespoke.NEAR_END`'s `max_z`
    declaration and the geometry are one decision made in one place.
    """
    prog = program(place)
    v, t, g = [], [], []
    if prog["kind"] == "dome":
        _dome_chamber(v, t, g, prog)
    else:
        _rotunda_chamber(v, t, g, prog)
    _vestibule(v, t, g, prog)
    return v, t, g


# ---------------------------------------------------------------------------
# The vestibule -- the flat face a corridor arrives at
# ---------------------------------------------------------------------------
def _entry_bay(prog):
    """Which bay of the ring the vestibule replaces, and its angular span.

    The +z direction in this module's frame is the way out to the corridor, so
    the entry bay is the one centred on +z -- angle pi/2 in the (x, z) plane
    this module revolves in.
    """
    return math.pi / 2.0, math.tau / prog["bays"]


def _vestibule(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    hw = VEST_HALF_W_M
    z0 = ro - 0.30                      # overlaps the ring wall's own thickness
    z1 = ro + VEST_L_M
    _box(v, t, g, "worship_deck" if prog["kind"] == "rotunda"
         else "transit_deck", (-hw - WALL_T_M, -0.18, z0),
         (hw + WALL_T_M, 0.0, z1))
    pre = "worship" if prog["kind"] == "rotunda" else "transit"
    for s in (-1, 1):
        _box(v, t, g, f"{pre}_wall", (s * hw, -0.02, z0),
             (s * (hw + WALL_T_M), VEST_H_M, z1))
    _box(v, t, g, f"{pre}_soffit", (-hw - WALL_T_M - 0.004, VEST_H_M - LAP_M,
                                    z0 - 0.004),
         (hw + WALL_T_M + 0.004, VEST_H_M + 0.18, z1 + 0.004))
    # THE DOORWAY, as PIECES round the aperture -- never a solid with a hole
    # punched through it. `bespoke.doorway_wall` owns the dimensions so three
    # modules cannot agree about them by hand and then stop agreeing.
    # THE PIECES ARE INFLATED BY 2 mm SO THEY OVERLAP RATHER THAN ABUT.
    # `bespoke.doorway_wall` owns the dimensions -- three modules may not agree
    # about them by hand and then stop agreeing -- and it emits a head and two
    # jambs that meet on exact planes, which welds into two non-manifold edges
    # per room (INV-951). Inflating what it hands back keeps its arithmetic and
    # separates the faces; the aperture loses 4 mm of a 2.20 m clear width,
    # against `kit.PROVISIONAL["door_width_m"]` of 1.50, and
    # `near_face_opening` is asserted against that in `_selftest`.
    _bsp.doorway_wall(
        lambda n, lo, hi: _box(v, t, g, n,
                               (lo[0] - 0.002, lo[1] - 0.002, lo[2] - 0.002),
                               (hi[0] + 0.002, hi[1] + 0.002, hi[2] + 0.002)),
        f"{pre}_wall", -hw - WALL_T_M, hw + WALL_T_M,
        0.0, VEST_H_M, z1, z1 + WALL_T_M)
    # A portal frame, AT THE CHAMBER END and not at the aperture. It belongs at
    # the aperture and it may not stand there, and the measurement is the
    # reason: `kit.door_frame` carries a sliding leaf's pocket on one side, so
    # at the three heights `deck._mouth_clear` probes it leaves **1.20 m clear,
    # centred 0.125 m off** -- narrower than the corridor's own 1.50 m leaf and
    # not symmetric about it. Put in the near face it turns a 2.20 m aperture
    # into a jamb a body walking straight at the door meets, which is exactly
    # the failure `deck_plan`'s phase sweep was fixed for in session 3z.
    # `bespoke.near_face_opening` caught it here in the module that builds the
    # thing, which is where the gate belongs.
    fv, ft = kit.door_frame()
    _merge(v, t, g, "prop_door", fv, ft, dz=z0 + 0.35)
    # And the lit head over it, which is what makes a doorway read at distance.
    _box(v, t, g, "light_portal_head",
         (-1.02, kit.PROVISIONAL["door_height_m"] + 0.06, z1 - 0.20),
         (1.02, kit.PROVISIONAL["door_height_m"] + 0.16, z1 - 0.14))
    _box(v, t, g, "light_portal_head",
         (-1.02, kit.PROVISIONAL["door_height_m"] + 0.06, z0 + 0.30),
         (1.02, kit.PROVISIONAL["door_height_m"] + 0.16, z0 + 0.36))


def _seg(v, t, g, name, r0, r1, a0, a1, y0, y1):
    """One annular-sector solid. Every ring element in this module is one."""
    return _prism(v, t, g, name, _ring_quad(r0, r1, a0, a1), y0, y1)


def _recessed_panel(v, t, g, r, ro, a0, a1, y0, y1,
                    frame=None, field=None, bead=None, depth=0.075):
    """A framed panel with its field SET BACK, not a flat rectangle.

    THE RULE, NOT THE INSTANCE. Round 1 said of the domes *"roughly 80% of the
    frame is flat panelled wall"*, and it was right: the wall was one prism per
    bay per storey. A panel that is a rectangle of the same material at the
    same depth is a rectangle; a panel is a frame, a reveal, and a field behind
    it, and the reveal is what a raking light finds. Both programs call this,
    which is session 4h's lesson about fixing a table rather than an entry.

    `depth` is how far the field sits outboard of the frame's inner face. At
    75 mm it throws a shadow the eye reads at four metres and does not eat the
    wall's 180 mm thickness.
    """
    frame = frame or M_PIER
    field = field or M_RECESS
    da = min(0.055, (a1 - a0) * 0.22)
    dy = min(0.14, (y1 - y0) * 0.16)
    # the field, set back, and OVERLAPPING the frame rather than abutting it
    _seg(v, t, g, field, r + depth, ro + 0.004, a0 + da * 0.5, a1 - da * 0.5,
         y0 + dy * 0.5, y1 - dy * 0.5)
    # the frame: two stiles and two rails, each a separate closed solid
    _seg(v, t, g, frame, r, ro, a0, a0 + da, y0, y1)
    _seg(v, t, g, frame, r, ro, a1 - da, a1, y0, y1)
    _seg(v, t, g, frame, r - 0.006, ro + 0.002,
         a0 + da - LAP_M * 0.1, a1 - da + LAP_M * 0.1, y0, y0 + dy)
    _seg(v, t, g, frame, r - 0.006, ro + 0.002,
         a0 + da - LAP_M * 0.1, a1 - da + LAP_M * 0.1, y1 - dy, y1)
    if bead:
        _seg(v, t, g, bead, r - 0.014, r + 0.018,
             a0 + da * 0.62, a1 - da * 0.62, y1 - dy - 0.024, y1 - dy + 0.006)
    return v, t, g


def _lattice_panel(v, t, g, r, a, half_a, y0, y1, bars=9, rungs=6):
    """"Tall blue backlit lattice panels" -- a GRILLE in front of a glow.

    Round 1 photographed the failure without naming it: the old panel was nine
    solid bars of `light_bar_backlight` filling the whole aperture, so it
    rendered as one clipped cyan slab with no lattice in it at all. A backlit
    lattice is three things at three depths -- a recessed emissive ground, a
    dark grille standing in front of it, and a frame round both -- and the
    frame's own panels read exactly that way: dark blue-violet, with the light
    coming through the gaps rather than off the face.
    """
    a0, a1 = a - half_a, a + half_a
    # THREE DEPTHS, AND THEY MAY NOT ENCLOSE EACH OTHER. The first version of
    # this put the glow inside a solid reveal box spanning r-0.34..r-0.14 and
    # the panel rendered as a flat dark slab, because an emissive surface
    # sealed inside an opaque solid emits into the inside of that solid. It is
    # INV-024's lesson at fitting scale -- glass in a bulkhead with no aperture
    # -- and it is why the back plate is now a PLATE.
    _seg(v, t, g, M_RECESS, r - 0.20, r - 0.15, a0, a1, y0 - 0.10, y1 + 0.10)
    # THE LIGHT COMES THROUGH THE GAPS. A full emissive field behind an open
    # grille is a light box: at `prop_shrine`'s emission energy 2.2 over a
    # 2.3 x 3.0 m face it clipped, which is the same failure as the disc on the
    # plot table one room over. Only the strips BETWEEN the grille bars glow --
    # 38% of the aperture -- and the bars are wide enough to read as a lattice.
    for k in range(bars + 1):
        fc = k / bars
        half = 0.20 / bars
        _seg(v, t, g, M_GLOW_B, r - 0.255, r - 0.215,
             a0 + (a1 - a0) * max(0.0, fc - half),
             a0 + (a1 - a0) * min(1.0, fc + half), y0, y1)
    for k in range(bars):
        f = (k + 0.5) / bars
        ac = a0 + (a1 - a0) * f
        _seg(v, t, g, M_GRILLE, r - 0.315, r - 0.265,
             ac - (a1 - a0) * 0.042, ac + (a1 - a0) * 0.042, y0 - 0.04,
             y1 + 0.04)
    for k in range(rungs):
        yy = y0 + (y1 - y0) * (k + 0.5) / rungs
        _seg(v, t, g, M_GRILLE, r - 0.300, r - 0.270, a0 + 0.004, a1 - 0.004,
             yy - 0.016, yy + 0.016)
    # the frame, and a real source at head and foot of the reveal
    for yy0, yy1 in ((y0 - 0.22, y0 - 0.08), (y1 + 0.08, y1 + 0.22)):
        _seg(v, t, g, M_PIER, r - 0.36, r - 0.12, a0 - 0.018, a1 + 0.018,
             yy0, yy1)
    for s in (-1, 1):
        _seg(v, t, g, M_PIER, r - 0.366, r - 0.114,
             a + s * half_a - 0.018, a + s * half_a + 0.018,
             y0 - 0.22, y1 + 0.22)
    for yy in (y0 + 0.05, y1 - 0.05):
        _seg(v, t, g, L_BLUE, r - 0.212, r - 0.185, a0 + 0.02, a1 - 0.02,
             yy - 0.022, yy + 0.022)
    return v, t, g


def _sigil(v, t, g, r, a, y, size=0.30, name=None):
    """The banner sigil, IN RELIEF -- the object round 1 said was missing.

    Round 1's C1 finding, verbatim: *"the two blue signage panels are the most
    eye-catching objects in the shot and are BLANK -- a lit rectangle standing
    in for a named object"*. The frame shows a figure painted in the lower
    third of each cloth. This builds one: a boss, six radial arms of two
    lengths, and a broken outer ring -- the same radial-about-a-centre idiom
    the floor mosaic and the dome ribs already use, so the room has ONE motif
    rather than a decal.

    It is geometry rather than a texture for the reason the mosaic is: at the
    grazing angles a banner is seen from, relief is the only thing that reads.
    """
    name = name or M_SIGIL
    rr = r - 0.352
    _cyl(v, t, g, name, (rr - 0.03) * math.cos(a), (rr - 0.03) * math.sin(a),
         y - size * 0.20, y + size * 0.20, size * 0.20, seg=10)
    for k in range(6):
        th = math.tau * k / 6.0
        long_arm = (k % 2 == 0)
        L = size * (0.98 if long_arm else 0.60)
        ac = a + math.cos(th) * (L * 0.5) / max(0.2, r)
        yc = y + math.sin(th) * L * 0.5
        w = size * (0.155 if long_arm else 0.115)
        _seg(v, t, g, name, rr - 0.042, rr,
             ac - w / max(0.2, r), ac + w / max(0.2, r), yc - w, yc + w)
    for k in range(8):
        if k % 4 == 3:
            continue
        th0 = math.tau * (k + 0.06) / 8.0
        th1 = math.tau * (k + 0.94) / 8.0
        for th in (th0, th1):
            ac = a + math.cos(th) * (size * 0.68) / max(0.2, r)
            yc = y + math.sin(th) * size * 0.68
            _seg(v, t, g, name, rr - 0.034, rr,
                 ac - 0.055 / max(0.2, r), ac + 0.055 / max(0.2, r),
                 yc - 0.055, yc + 0.055)
    return v, t, g


def _cove_ring(v, t, g, r, y, n, ea, name=None, inset=0.34):
    """The uplight cove -- the source the rotunda did not have.

    THE ROOM WAS LIT BY AMBIENT AND SAID SO IN ITS OWN NUMBERS. The block at
    the head of this file measured it: one caster, mean irradiance 0.0044
    against the corridor anchor's 4.2641 -- **970x under** -- because
    `light_pilaster_strip`, `light_portal_head` and `light_bar_backlight` are
    all absent from `export_scene.FIXTURE_LIGHTING` and emit without casting.
    That block ends *"NOT FIXED HERE, deliberately: the remedy is sources"*.

    This is the source. `light_house_cove` IS in that table -- omni, 6300 K,
    energy_rel 0.35, range 18.0 m, measured off the council chamber -- and a
    cove is what the frame shows lighting this dome: the corbel course is lit
    from beneath its own lip, and the dome above it is washed rather than lamped.
    One per bay behind the cornice lip, which is `FIXTURE_MERGE_M` 0.9 m apart
    at nothing under a 2.7 m bay pitch, so they stay separate lamps.
    """
    name = name or L_COVE
    for i in range(n):
        a0 = math.tau * (i + 0.12) / n + ea
        a1 = math.tau * (i + 0.88) / n + ea
        _seg(v, t, g, name, r - inset, r - inset + 0.055, a0, a1,
             y - 0.05, y + 0.05)
    return v, t, g


# ---------------------------------------------------------------------------
# The rotunda -- rotunda.webp, authority 1
# ---------------------------------------------------------------------------
# THE INTENT, WRITTEN BEFORE THE RENDER, because AAA-STANDARD's lighting
# section requires it and a review without it is a preference:
#
#   CEREMONIAL AND WARM, LOOKING OUT AT SOMETHING COLD. The bronze is the
#   room and the vacuum is the view, so nothing in here may be as bright as
#   the window; the eye rests on the lit ribbon at waist height, travels up
#   the colonnade to the gold dome, and is answered at floor level by the
#   mosaic. The two blue lattices and the blue lectern are the only cold
#   things inside, and they are the Minbari order's own colour.
def _rotunda_chamber(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    n = prog["bays"]
    ea, espan = _entry_bay(prog)
    seg = max(48, n * 4)

    # THE SUNBURST FLOOR. "Triangular radial wedges about a centre, and a broad
    # concentric band of chevrons at larger radius." Built as a deck slab with
    # the mosaic laid on it as pads, so it is geometry at grazing incidence
    # rather than a texture claim -- AND IN THE FRAME'S OWN CREAM AND OCHRE.
    # The slab under it stays `worship_deck` because `collision.py` and
    # `rooms.is_solid` both key the walkable surface off that name and a floor
    # is not the place to be clever.
    _revolve(v, t, g, "worship_deck",
             [(0.0, 0.0), (ro, 0.0), (ro, -0.18), (0.0, -0.18)], seg)
    _pad(v, t, g, M_STONE,
         [(r * 0.995 * math.cos(math.tau * k / seg),
           r * 0.995 * math.sin(math.tau * k / seg)) for k in range(seg)],
         0.0, 0.008)
    wedges = n
    for i in range(wedges):
        if i % 2:
            continue
        a0 = math.tau * i / wedges
        a1 = math.tau * (i + 0.62) / wedges
        _pad(v, t, g, M_STONE_D,
             [(0.10 * math.cos((a0 + a1) / 2), 0.10 * math.sin((a0 + a1) / 2)),
              (r * 0.46 * math.cos(a0), r * 0.46 * math.sin(a0)),
              (r * 0.46 * math.cos(a1), r * 0.46 * math.sin(a1))],
             0.008, 0.019)
    for i in range(wedges * 2):
        a0 = math.tau * i / (wedges * 2)
        a1 = math.tau * (i + 0.5) / (wedges * 2)
        am = (a0 + a1) / 2.0
        _pad(v, t, g, M_STONE_D,
             [(r * 0.58 * math.cos(a0), r * 0.58 * math.sin(a0)),
              (r * 0.70 * math.cos(am), r * 0.70 * math.sin(am)),
              (r * 0.58 * math.cos(a1), r * 0.58 * math.sin(a1)),
              (r * 0.64 * math.cos(am), r * 0.64 * math.sin(am))],
             0.008, 0.019)
    # A HUB the wedges radiate from, and a bronze ring round it. The frame's
    # mosaic has a centre; ours radiated from nothing.
    _revolve(v, t, g, M_BRONZE,
             [(0.0, 0.008), (0.46, 0.008), (0.46, 0.026), (0.38, 0.026),
              (0.38, 0.020), (0.0, 0.020)], seg)

    # THE WALL BELOW THE SILL, in segments, with the entry bay left OUT -- an
    # opening is a hole in something and the something is built with the hole
    # already in it. Every segment is inset by `GAP_A` and the gap carries a
    # recessed pier, so no two ring solids share a face (INV-951) and the bay
    # rhythm is legible instead of the ring being one continuous surface.
    for i in range(n):
        a0 = math.tau * i / n - math.tau / (2 * n) + ea
        a1 = a0 + math.tau / n
        if abs(((a0 + a1) / 2.0 - ea + math.pi) % math.tau - math.pi) < 1e-6:
            continue
        b0, b1 = a0 + GAP_A, a1 - GAP_A
        # THE WALL STOPS AT THE SILL. It used to run floor to entablature and
        # the glazing was then laid at r+0.02..r+0.09 -- INSIDE the wall's own
        # 0.18 m thickness. The room had no windows at all, and
        # `docs/engine-4k-rotunda-normal.png` is the frame that showed it.
        # INV-024 records the identical defect on C&C's own window in session 2
        # -- *"the bulkhead had no aperture; it was one solid slab with the
        # glazing laid on it"* -- and the lesson is stated there: **an opening
        # is a hole in something, and the something has to be built with the
        # hole already in it.**
        _seg(v, t, g, M_WALL, r, ro, b0, b1, 0.0, ROT_SILL_M)
        # THE SKIRTING, and it is where the wear goes. CRAFT 4 wants lighting
        # response to VARY across the surface; the bottom 160 mm of a wall in a
        # room people queue in is scuffed part-metallic bronze and the field
        # above it is matte brown, which is a difference in ROUGHNESS as well
        # as in value and therefore survives a change of lighting.
        _seg(v, t, g, M_PIER, r - 0.055, ro + 0.004, b0, b1, -0.02, 0.155)
        # THE PALE VERTICAL SLAT BAND at waist height, right around the room,
        # standing proud of a dark recess so it reads as a lit ribbon rather
        # than as a bright wall.
        _seg(v, t, g, M_RECESS, r - 0.082, r + 0.01, b0, b1,
             ROT_SLAT_M - 0.40, ROT_SLAT_M + 0.22)
        for k in range(ROT_SLATS_PER_BAY):
            f0 = (k + 0.22) / ROT_SLATS_PER_BAY
            f1 = (k + 0.62) / ROT_SLATS_PER_BAY
            _seg(v, t, g, M_RIBBON, r - 0.075, r - 0.012,
                 b0 + (b1 - b0) * f0, b0 + (b1 - b0) * f1,
                 ROT_SLAT_M - 0.34, ROT_SLAT_M + 0.16)
        _seg(v, t, g, M_BRONZE, r - 0.105, r + 0.015, b0, b1,
             ROT_SLAT_M + 0.20, ROT_SLAT_M + 0.255)
        # THE GLAZING, set INTO the bay between sill and head, spanning the
        # reveal and inset from the jambs so the columns and the reveal read
        # either side of it.
        _seg(v, t, g, "prop_viewport", r + 0.055, ro - 0.055,
             b0 + 0.035, b1 - 0.035, ROT_SILL_M, ROT_HEAD_M)
        # GLAZING BARS, and they are part of the window rather than trim. A
        # pane of glass is a flat prism with almost no visible line in it, and
        # fifteen of them dragged this room's `density.py --machinery` ratio to
        # x0.95 -- machinery LESS articulated than the shell behind it. A
        # transom and two glazing bars are what a 2.4 m window is built from.
        #
        # AND EACH BAR IS TWO PIECES. `prop_viewport` binds `viewport_glazing`
        # -- albedo 0.04, the colour of glass -- so a bar named `prop_viewport`
        # in front of black glass carries the line the DENSITY gate measures
        # and shows the eye nothing. The dark bar stays and a BRONZE cover
        # strip stands proud of it on the room side, which is what a real
        # window frame is; it used to be `worship_mullion`, which is the same
        # grey as the wall, so the division vanished into the bulkhead.
        for f in (0.30, 0.70):
            _seg(v, t, g, "prop_viewport", r + 0.02, ro - 0.02,
                 b0 + (b1 - b0) * f - 0.008, b0 + (b1 - b0) * f + 0.008,
                 ROT_SILL_M + 0.03, ROT_HEAD_M - 0.03)
            _seg(v, t, g, M_BRONZE, r - 0.05, r + 0.03,
                 b0 + (b1 - b0) * f - 0.012, b0 + (b1 - b0) * f + 0.012,
                 ROT_SILL_M + 0.02, ROT_HEAD_M - 0.02)
        for yf in (0.34, 0.68):
            yy = ROT_SILL_M + (ROT_HEAD_M - ROT_SILL_M) * yf
            _seg(v, t, g, "prop_viewport", r + 0.02, ro - 0.02,
                 b0 + 0.045, b1 - 0.045, yy - 0.022, yy + 0.022)
            _seg(v, t, g, M_BRONZE, r - 0.05, r + 0.03, b0 + 0.045, b1 - 0.045,
                 yy - 0.030, yy + 0.030)
        # The reveal round the aperture -- head, sill and two jambs, which is
        # what stops a window reading as a decal at grazing incidence. Each one
        # OVERLAPS its neighbour by `LAP_M` instead of abutting it.
        _seg(v, t, g, M_BRONZE, r - 0.06, ro, b0, b1,
             ROT_HEAD_M - 0.10, ROT_HEAD_M + LAP_M)
        _seg(v, t, g, M_BRONZE, r - 0.07, ro, b0, b1,
             ROT_SILL_M - 0.09, ROT_SILL_M + LAP_M)
        for f0, f1 in ((0.0, 0.035), (1.0 - 0.035 / (b1 - b0), 1.0)):
            _seg(v, t, g, M_PIER, r + 0.005, ro + 0.005,
                 b0 + (b1 - b0) * f0, b0 + (b1 - b0) * f1,
                 ROT_SILL_M - LAP_M, ROT_HEAD_M + LAP_M)
        # THE STOREY ABOVE THE WINDOW, as a framed and recessed panel rather
        # than a slab. This is the surface round 1 called "flat panelled wall".
        _recessed_panel(v, t, g, r, ro, b0, b1, ROT_HEAD_M - LAP_M,
                        ROT_ENTAB_M, frame=M_PIER, field=M_WALL_UP,
                        bead=M_GOLD, depth=0.070)
        # A SERVICE RISER every third bay -- the physical plant a station of
        # 250,000 needs, where it would actually be needed: in the pier between
        # two windows, running from the skirting to the entablature.
        if i % 3 == 1:
            am = (b0 + b1) / 2.0
            _seg(v, t, g, M_METAL, r - 0.115, r - 0.035,
                 am - 0.026, am + 0.026, 0.14, ROT_ENTAB_M - 0.10)
            for k in range(4):
                yy = 0.40 + k * 0.86
                _seg(v, t, g, M_PIER, r - 0.135, r - 0.020,
                     am - 0.040, am + 0.040, yy - 0.035, yy + 0.035)
        _seg(v, t, g, M_STONE_D, r - 0.055, r, b0, b1, 0.155 - LAP_M,
             ROT_SILL_M - 0.09 + LAP_M)
        # THE REVEAL BETWEEN BAYS, set back so the bay rhythm has a shadow in
        # it. This is also what makes the ring solids non-adjacent (INV-951).
        _seg(v, t, g, M_RECESS, r + 0.055, ro, a1 - GAP_A * 1.6,
             a1 + GAP_A * 1.6, 0.0, ROT_ENTAB_M)

    # THE COLUMNS. "A plain slightly tapered cylindrical shaft carrying a group
    # of THREE narrow ring collars, then a longer plain shaft, then a short
    # stepped capital under the entablature." Built in that order, and the
    # order is the identity of the room -- `garden.png` carries the same one on
    # the Garden's civic building, so it is a station order, not a one-off.
    for i in range(n):
        a = math.tau * i / n - math.tau / (2 * n) + ea
        if abs(((a - ea + math.pi) % math.tau) - math.pi) < 1e-6:
            continue
        cx, cz = (r - 0.24) * math.cos(a), (r - 0.24) * math.sin(a)
        _column(v, t, g, cx, cz)

    # THE CORBEL COURSE -- stepped rectangular blocks in layered tiers. In the
    # frame the tiers ALTERNATE in value, pale over dark over pale, with a
    # shadow gap behind each; built all one grey they read as one black band,
    # which is what round 1 saw.
    for tier in range(ROT_CORBEL_TIERS):
        y0 = ROT_ENTAB_M + tier * 0.30
        rr = r - 0.10 - tier * 0.20
        m = n * 2
        _revolve(v, t, g, M_RECESS,
                 [(rr - 0.02, y0 + 0.315), (ro, y0 + 0.315),
                  (ro, y0 - 0.015), (rr - 0.02, y0 - 0.015)], seg)
        for i in range(m):
            a0 = math.tau * (i + 0.14) / m + ea
            a1 = math.tau * (i + 0.86) / m + ea
            _seg(v, t, g, M_STONE if tier % 2 == 0 else M_WALL_UP,
                 rr, ro, a0, a1, y0, y0 + 0.30 + LAP_M)
            if tier == ROT_CORBEL_TIERS - 1:
                _seg(v, t, g, M_GOLD, rr - 0.030, rr + 0.02, a0 + 0.004,
                     a1 - 0.004, y0 + 0.245, y0 + 0.285)

    # THE COVE. One per bay, tucked behind the corbel lip -- and it is the
    # room's first real source. See `_cove_ring`.
    _cove_ring(v, t, g, r, ROT_ENTAB_M - 0.13, n, ea, inset=0.20)

    # THE DOME. Warm gold-bronze, smooth, with broad radial ribs. A CLOSED
    # SOLID with thickness -- `bespoke.py`'s own note on this work says the
    # hard part is exactly that: `components.dome_mesh` is a closed
    # half-ellipsoid every face of which points OUT, so an interior needs the
    # surface built twice with a rim between.
    y0 = ROT_ENTAB_M + ROT_CORBEL_TIERS * 0.30
    rise = ROT_CROWN_M - y0
    r_in = r - 0.10 - ROT_CORBEL_TIERS * 0.20
    _dome_solid(v, t, g, M_BRONZE, r_in, y0, rise, 0.22, seg)
    # THE RIBS ARE GOLD-BRONZE, which is the frame's own word for the dome:
    # *"a smooth warm gold-bronze dome with broad radial ribs"*. `dress_kerb`
    # (albedo 0.900 / 0.720 / 0.060, sourced from `Minbari Flyer 969 in docking
    # bay 17.webp`) is the one sourced gold in the library. The name has to end
    # in `_rib` so `rooms.is_solid` calls it shell -- a dome rib named as an
    # object becomes a collision box hanging over the floor.
    #
    # AND THEY ARE NOW BROAD. At 0.16 m on a 6.5 m dome a "broad radial rib"
    # was 1.4 degrees of arc and read as a wire; the frame's ribs are of the
    # order of a fifth of the bay they divide.
    ribs = n
    for i in range(ribs):
        a = math.tau * i / ribs + ea
        _dome_rib(v, t, g, M_GOLD, r_in, y0, rise, a, 0.52, 0.19)
    # AND THE FIELD BETWEEN THEM IS COFFERED. A dome that is a smooth shell is
    # legible only from its silhouette; CRAFT 5 asks that "the form is legible
    # from shading alone", and a coffer is the cheapest thing that delivers it.
    _dome_coffers(v, t, g, r_in, y0, rise, ribs, ea, seg=seg)
    # THE CROWN. Something has to happen where sixteen ribs meet, or the dome
    # ends in a pinch of coincident geometry the eye reads as a mistake.
    _cyl(v, t, g, M_GOLD, 0.0, 0.0, y0 + rise - 0.30, y0 + rise - 0.06,
         0.42, 0.30, seg=16)
    _cyl(v, t, g, M_RECESS, 0.0, 0.0, y0 + rise - 0.34, y0 + rise - 0.26,
         0.50, seg=16)

    # TWO PALE CONICAL ELEMENTS standing on the cornice, upper left.
    for i in range(ROT_CONES):
        a = ea + math.pi * (0.62 + 0.16 * i)
        _cyl(v, t, g, M_STONE, (r - 0.55) * math.cos(a),
             (r - 0.55) * math.sin(a), y0, y0 + 0.72, 0.26, 0.02, seg=10)

    _rotunda_fittings(v, t, g, prog, r, n, ea)


def _column(v, t, g, cx, cz):
    """One column of the frame's order: taper, THREE collars, shaft, capital.

    THE COLLARS ARE A DIFFERENT MATERIAL FROM THE SHAFT, which is what makes
    the order read. In the reference the shafts are dark bronze and the three
    collars catch the window light as bright rings; built all one grey the
    whole colonnade disappeared into the wall behind it, and
    `docs/engine-4k-rotunda-normal.png` shows exactly that -- sixteen columns
    in frame and not one of them legible.
    """
    _cyl(v, t, g, M_STONE, cx, cz, 0.0, 0.17, 0.30, 0.27, seg=12)
    _cyl(v, t, g, M_PIER, cx, cz, 0.15, 1.63, 0.26, 0.225, seg=12)
    for k in range(ROT_COLLARS):
        y = 1.62 + k * 0.135
        _cyl(v, t, g, M_BRONZE, cx, cz, y, y + 0.085, 0.285, seg=12)
    _cyl(v, t, g, M_PIER, cx, cz, 2.02, ROT_HEAD_M - 0.27, 0.215, 0.195,
         seg=12)
    _cyl(v, t, g, M_BRONZE, cx, cz, ROT_HEAD_M - 0.29, ROT_HEAD_M - 0.13,
         0.255, seg=12)
    _cyl(v, t, g, M_STONE, cx, cz, ROT_HEAD_M - 0.15, ROT_ENTAB_M + LAP_M,
         0.295, seg=12)


def _dome_coffers(v, t, g, r, y0, rise, ribs, ea, seg=48,
                  minor=None, band=None, bands=(0.26, 0.50, 0.74)):
    """Coffer the dome: a MINOR rib between each pair of majors, and concentric
    bands across them -- INV-952.

    A dome built as one smooth revolve has nothing on it for light to do, and
    both programs shipped one: the rotunda's read as a pale shell and the
    domes' as smooth plastic. CRAFT 5 asks that *"the form is legible from
    shading alone"* and a shell cannot be; a grid of ribs and bands is the
    cheapest thing that delivers it, and it is what a coffered dome of this
    order reads as from beneath -- the ribs, not the sinkings.

    IT IS BUILT WITH THE SAME TWO PRIMITIVES THE DOME ALREADY USES, deliberately.
    `_dome_rib` follows the meridian and `_revolve` follows the parallel, so
    every piece lies ON the surface the dome was revolved from and cannot poke
    through it -- which a box spanning a chord of that surface does, and which
    is how a "coffer" becomes a lump.

    The bands are at three unequal fractions of the meridian rather than at
    even thirds: an even grid is a period the eye can index, which is the
    clause CRAFT 5 fails on.
    """
    minor = minor or M_STONE
    band = band or M_GOLD
    for i in range(ribs):
        a = math.tau * (i + 0.5) / ribs + ea
        _dome_rib(v, t, g, minor, r, y0, rise, a, 0.26, 0.11)
    for f in bands:
        rr = (r - 0.03) * math.cos(f * math.pi / 2.0)
        yy = y0 + (rise - 0.03) * math.sin(f * math.pi / 2.0)
        h = 0.15 + 0.09 * f
        # the raised band, and a SHADOW GAP set deeper beneath it. A band with
        # nothing under it is a line; a band over a recess is a step, and a
        # step is what makes a dome legible from shading alone.
        _revolve(v, t, g, M_RECESS,
                 [(rr + 0.02, yy - 0.10), (rr + 0.02, yy + h + 0.06),
                  (rr - 0.20, yy + h + 0.06), (rr - 0.20, yy - 0.10)], seg)
        _revolve(v, t, g, band,
                 [(rr, yy), (rr, yy + h), (rr - 0.16, yy + h), (rr - 0.16, yy)],
                 seg)
    return v, t, g


def _dome_solid(v, t, g, name, r, y0, rise, thick, seg):
    """A dome with THICKNESS: outer surface, inner surface, and the rim.

    `bespoke.py`'s audit block names this as the only hard part of an
    observation room, and it is right. The profile is a closed meridian --
    outer from the springing to the crown, inner back down, rim across -- so
    the revolve produces one closed solid and the INSIDE face exists, which is
    the whole difference between a room and a blister on a hull.
    """
    steps = 12
    prof = []
    for i in range(steps + 1):
        f = i / steps
        prof.append((r * math.cos(f * math.pi / 2.0),
                     y0 + rise * math.sin(f * math.pi / 2.0)))
    ri, yi = r - thick, rise - thick
    for i in range(steps, -1, -1):
        f = i / steps
        prof.append((ri * math.cos(f * math.pi / 2.0),
                     y0 + yi * math.sin(f * math.pi / 2.0)))
    _revolve(v, t, g, name, prof, seg)
    return v, t, g


def _dome_rib(v, t, g, name, r, y0, rise, a, w, d, steps=9, f_max=0.92):
    """One broad radial rib on the dome's inner face, along a meridian."""
    c, s = math.cos(a), math.sin(a)
    tc, ts = -math.sin(a), math.cos(a)
    base = len(v)
    t0 = len(t)
    rings = []
    for i in range(steps + 1):
        # STOP SHORT OF THE AXIS. At f = 1 the meridian radius is zero and this
        # rib's four-point ring collapses to one point, which welds into edges
        # used by four triangles -- 32 non-manifold edges per dome, times four
        # rib families, which was two thirds of the whole count. A crown boss
        # covers the last 8% of the meridian, and a rib that runs to a pinch is
        # geometry nobody can see (session 3x, `portal_frame`).
        f = f_max * i / steps
        rr = (r - 0.02) * math.cos(f * math.pi / 2.0)
        yy = y0 + (rise - 0.02) * math.sin(f * math.pi / 2.0)
        ri = max(0.0, rr - d)
        yi = yy - d * math.sin(f * math.pi / 2.0) * 0.2
        quad = []
        for rq, yq in ((rr, yy), (ri, yi)):
            for sgn in (-1.0, 1.0):
                quad.append((rq * c + sgn * w / 2.0 * tc, yq,
                             rq * s + sgn * w / 2.0 * ts))
        rings.append([quad[0], quad[1], quad[3], quad[2]])
    for i, ring in enumerate(rings):
        v.extend(ring)
    for i in range(steps):
        a0 = base + 4 * i
        b0 = base + 4 * (i + 1)
        for k in range(4):
            j = (k + 1) % 4
            t.append((a0 + k, b0 + k, b0 + j))
            t.append((a0 + k, b0 + j, a0 + j))
    t += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    e = base + 4 * steps
    t += [(e, e + 1, e + 2), (e, e + 2, e + 3)]
    g.append((name, t0, len(t)))
    return v, t, g


def _rotunda_fittings(v, t, g, prog, r, n, ea):
    """Banners, lattice panels, the steps and portal, the lectern, the seats."""
    # FOUR HANGING BANNERS -- long vertical cloths, sigil in the lower third.
    # TWO DARK AND TWO PALE, which is what the frame shows and which is also
    # the cheapest defence against the thing CRAFT 5 forbids: four identical
    # cloths at four evenly spaced angles is a period the eye indexes in one
    # sweep. They alternate material, and the two pairs hang at different
    # heights because a cloth hung by hand does not.
    for i in range(ROT_BANNERS):
        a = ea + math.pi * (0.42 + 0.39 * i)
        a0, a1 = a - 0.105, a + 0.105
        cloth = M_CLOTH_B if i % 2 == 0 else M_CLOTH_P
        drop = 0.0 if i % 2 == 0 else 0.14
        _seg(v, t, g, cloth, r - 0.34, r - 0.30, a0, a1,
             1.48 + drop, ROT_HEAD_M + 0.10)
        # THE SIGIL, IN THE LOWER THIRD AND IN RELIEF. Round 1's C1 finding.
        _sigil(v, t, g, r, a, 1.94 + drop, size=0.50)
        # the hanging rail, and a boss at each end of it
        _seg(v, t, g, M_BRONZE, r - 0.365, r - 0.275, a0 - 0.014, a1 + 0.014,
             ROT_HEAD_M + 0.08, ROT_HEAD_M + 0.155)
        for s in (-1, 1):
            _cyl(v, t, g, M_BRONZE, (r - 0.32) * math.cos(a + s * 0.119),
                 (r - 0.32) * math.sin(a + s * 0.119),
                 ROT_HEAD_M + 0.09, ROT_HEAD_M + 0.145, 0.045, seg=8)

    # TALL BLUE BACKLIT LATTICE PANELS flanking the room, left and right.
    for i in range(ROT_LATTICE):
        a = ea + math.pi * (0.66 + 0.68 * i)
        _lattice_panel(v, t, g, r, a, 0.165, 0.42, ROT_HEAD_M - 0.14,
                       bars=7, rungs=8)

    # THE FLIGHT OF ABOUT TEN PALE STEPS rising to a dark portal, flanked by
    # piers whose lower ends carry a comb of vertical slots.
    #
    # THE STEPS ARE PALE AND THE NOSINGS ARE BRONZE. They were `worship_deck`
    # grey with `fix_platform_edge` on the nose, which is the station's HAZARD
    # CHEVRON -- albedo 0.900 / 0.720 / 0.060 -- so a ceremonial stair in a
    # Minbari-order chamber was striped like a loading dock, and it is the
    # first thing the eye goes to in `docs/engine-4k-rotunda-half.png`.
    rise = 0.165
    for i in range(ROT_STEPS):
        zz = -r * 0.42 - i * 0.30
        hw_i = 1.35 - 0.004 * i
        _box(v, t, g, M_STONE, (-hw_i, -0.006 * i, zz - 0.30 - LAP_M),
             (hw_i, rise * (i + 1), zz))
        _box(v, t, g, M_BRONZE, (-1.34, rise * (i + 1) - 0.035, zz - 0.30),
             (1.34, rise * (i + 1) + 0.014, zz - 0.235))
    top = rise * ROT_STEPS
    zt = -r * 0.42 - ROT_STEPS * 0.30
    # THE DARK PORTAL at the head of the flight, with a lit reveal round it so
    # the way out reads as a way out rather than as a stain on the wall.
    _box(v, t, g, M_RECESS, (-1.32, top, zt - 0.54), (1.32, top + 2.30,
                                                      zt - 0.30))
    _box(v, t, g, M_WALL_UP, (-1.62, top, zt - 0.58), (1.62, top + 2.62,
                                                       zt - 0.28))
    _box(v, t, g, M_BRONZE, (-1.66, top + 2.30, zt - 0.60),
         (1.66, top + 2.46, zt - 0.26))
    _box(v, t, g, M_RIBBON, (-1.24, top + 2.22, zt - 0.46),
         (1.24, top + 2.28, zt - 0.40))
    for s in (-1, 1):
        # the pier: a plinth, a shaft, and a capital -- three solids, three
        # materials. It was one grey slab 0.37 x 2.72 x 5.7 m, and at half
        # distance it is the largest object in the room.
        _box(v, t, g, M_WALL_UP, (s * 1.33, 0.0, zt - 0.34),
             (s * 1.74, 0.42, zt + 2.42))
        _box(v, t, g, M_PIER, (s * 1.35, 0.40, zt - 0.32),
             (s * 1.72, top + 2.46, zt + 2.40))
        _box(v, t, g, M_BRONZE, (s * 1.31, top + 2.44, zt - 0.36),
             (s * 1.76, top + 2.62, zt + 2.44))
        # the comb of vertical slots at the lower end, RECESSED into the pier
        for k in range(8):
            _box(v, t, g, M_RECESS,
                 (s * 1.345, 0.10, zt + 0.30 + k * 0.24),
                 (s * 1.755, 1.05, zt + 0.36 + k * 0.24))
        # a service riser up the room face of each pier
        _box(v, t, g, M_METAL, (s * 1.30, 0.44, zt + 2.24),
             (s * 1.36, top + 2.40, zt + 2.34))
    rv, rt = kit.handrail(ROT_STEPS * 0.30, height=1.02, post_spacing=0.9)
    _merge(v, t, g, "prop_gallery_rail",
           [(-z, y + top * (1.0 - x / max(1e-9, ROT_STEPS * 0.30)), x)
            for x, y, z in rv], rt, dx=-1.24, dz=zt)

    # THE LECTERN -- dark plinth, sloping BLUE-glowing top, chevron figure.
    # The reference is explicit: *"a dark plinth lectern with a sloping
    # cyan-glowing top, the glow divided by dark bars into a symmetrical
    # chevron figure"*. This module had the plinth right and the glow WARM, on
    # `light_dais_key` at emission energy 6.0 over a 1.12 x 0.64 m face -- a
    # white hole in the middle of a cold room, and the brightest thing in a
    # frame whose subject is a window. It is now `prop_shrine` blue at ee 2.2,
    # a third of the area, and the dark bars that make the chevron are built.
    zc = r * 0.30
    _box(v, t, g, M_WALL_UP, (-0.62, 0.0, zc), (0.62, 0.94, zc + 0.72))
    _box(v, t, g, M_PIER, (-0.58, 0.0, zc + 0.02), (0.58, 0.16, zc + 0.70))
    _box(v, t, g, M_BRONZE, (-0.66, 0.90, zc - 0.04), (0.66, 0.99, zc + 0.76))
    _box(v, t, g, M_RECESS, (-0.57, 0.965, zc + 0.03), (0.57, 1.005, zc + 0.69))
    # the glowing field, then the dark bars that divide it into a chevron
    _box(v, t, g, M_GLOW_B, (-0.545, 0.985, zc + 0.05), (0.545, 1.012,
                                                         zc + 0.67))
    for k in range(5):
        f = (k + 0.5) / 5.0
        xx = -0.545 + 1.09 * f
        w = 0.019
        zk = zc + 0.05 + 0.62 * abs(f - 0.5) * 0.9
        _box(v, t, g, M_GRILLE, (xx - w, 1.008, zk),
             (xx + w, 1.028, zk + 0.62 - (zk - zc - 0.05)))
    _box(v, t, g, M_GRILLE, (-0.545, 1.008, zc + 0.345),
         (0.545, 1.026, zc + 0.375))
    # AND A REAL SOURCE UNDER THE LIP. `cc_light_strip` is in
    # `export_scene.FIXTURE_LIGHTING` -- omni, 22000 K, energy_rel 0.44,
    # range 3.5 m -- so the lectern throws its own blue onto the floor and the
    # robes standing at it, which is what the frame shows and what an emissive
    # surface alone can never do.
    _box(v, t, g, L_BLUE, (-0.50, 0.955, zc + 0.06), (0.50, 0.975, zc + 0.10))

    # THE SEATS the register declares, on the ring between the columns.
    for i in range(prog["benches"]):
        a = ea + math.tau * (i + 0.5) / prog["benches"] + math.tau / (2 * n)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.95, r - 0.48, a - 0.115, a + 0.115),
               0.40, 0.46)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.92, r - 0.84, a - 0.11, a + 0.11), 0.0, 0.40)
        _prism(v, t, g, "prop_bench",
               _ring_quad(r - 0.59, r - 0.51, a - 0.11, a + 0.11), 0.0, 0.40)

    # THE SKY PLAQUE, ETIQUETTE NOTICE, LIGHTS-DOWN SWITCH and INSPECTION
    # TERMINAL that PLC-064 adds to the register's two. They are built under
    # names `materials.py` already binds; the register rows that would DECLARE
    # them are not this session's to add -- see the report.
    for i, (nm, y0, y1, wd) in enumerate((
            ("prop_info_board", 1.15, 2.05, 0.16),
            ("prop_babcom_terminal", 1.05, 1.55, 0.10))):
        a = ea + math.pi + (0.34 if i else -0.34)
        _seg(v, t, g, M_RECESS, r - 0.13, r - 0.095, a - wd - 0.022,
             a + wd + 0.022, y0 - 0.05, y1 + 0.05)
        _prism(v, t, g, nm, _ring_quad(r - 0.09, r - 0.02, a - wd, a + wd),
               y0, y1)
        _seg(v, t, g, M_BRONZE, r - 0.135, r - 0.025, a - wd - 0.030,
             a + wd + 0.030, y1 + 0.04, y1 + 0.09)


# ---------------------------------------------------------------------------
# The domes -- the C&C frame's glazing, from inside
# ---------------------------------------------------------------------------
# THE DOMES' PALETTE IS COOL AND THE ROTUNDA'S IS WARM, and that is a decision
# rather than an oversight. `reference/03-sector-blue/comand and contorl.webp`
# is a cold blue-grey room with blue light courses and warm console glow; the
# rotunda's frame is warm bronze throughout. Two rooms in two sectors that look
# alike would be `deck.py --degeneracy`'s question answered wrongly at the level
# of material rather than of geometry. Same idiom, different register.
D_FRAME = "prop_workbench_rib"          # furn_shop_steel 0.470 r0.58 met0.95
D_PALE = "prop_diagnostic_bed_panel"    # furn_clinical   0.500,0.512,0.535
D_TRIM = "prop_catwalk_rib"             # steel_catwalk_tread 0.266 met0.30
D_DECK = "prop_deck_marking_deck_joint"  # bay_deck_marking 0.405,0.299,0.308


def _strut(v, t, g, name, p0, p1, rad, seg=6):
    """A capped strut between two arbitrary points -- the angled bracing.

    `LOCATIONS.md` §169 reads the C&C dome at authority 1 as *"a large circle
    on radial spoke mullions with a broad concentric ring band, set in a flat-
    panelled bulkhead WITH ANGLED BRACING"*. Every other clause of that
    sentence was built and the bracing was not, because every primitive in this
    module is axis-aligned or a solid of revolution and neither can make a
    diagonal. This is the missing primitive, and it is closed at both ends.
    """
    ax = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in ax)) or 1e-9
    ax = [c / L for c in ax]
    up = (0.0, 1.0, 0.0) if abs(ax[1]) < 0.92 else (1.0, 0.0, 0.0)
    e0 = [up[1] * ax[2] - up[2] * ax[1], up[2] * ax[0] - up[0] * ax[2],
          up[0] * ax[1] - up[1] * ax[0]]
    m0 = math.sqrt(sum(c * c for c in e0)) or 1e-9
    e0 = [c / m0 for c in e0]
    e1 = [ax[1] * e0[2] - ax[2] * e0[1], ax[2] * e0[0] - ax[0] * e0[2],
          ax[0] * e0[1] - ax[1] * e0[0]]
    n0 = len(v)
    for k in range(seg):
        th = math.tau * k / seg
        c, s = math.cos(th) * rad, math.sin(th) * rad
        v.append(tuple(p0[i] + c * e0[i] + s * e1[i] for i in range(3)))
        v.append(tuple(p1[i] + c * e0[i] + s * e1[i] for i in range(3)))
    t0 = len(t)
    for k in range(seg):
        a0 = n0 + 2 * k
        b0 = n0 + 2 * ((k + 1) % seg)
        t += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
    cap0 = len(v)
    v.append(tuple(p0))
    for k in range(seg):
        t.append((cap0, n0 + 2 * ((k + 1) % seg), n0 + 2 * k))
    cap1 = len(v)
    v.append(tuple(p1))
    for k in range(seg):
        t.append((cap1, n0 + 2 * k + 1, n0 + 2 * ((k + 1) % seg) + 1))
    g.append((name, t0, len(t)))
    return v, t, g


def _dome_chamber(v, t, g, prog):
    r = prog["r"]
    ro = r + WALL_T_M
    n = prog["bays"]
    ea, _ = _entry_bay(prog)
    seg = max(48, n * 4)
    mull = _dome_mullions()

    _revolve(v, t, g, "transit_deck",
             [(0.0, 0.0), (ro, 0.0), (ro, -0.18), (0.0, -0.18)], seg)

    # THE GALLERY WELL. PLC-002's dome holds C&C `within` it, and the room this
    # row describes is the ring GALLERY round it -- so dome 1 gets a recessed
    # centre with a rail on its edge, and dome 2, which is a flat public
    # gallery, does not. A RECESS, NOT A HOLE: a void in the floor is a void a
    # body falls through and the collision shell has no way to say so.
    if prog.get("well"):
        wr = r * GALLERY_WELL_FRAC
        _revolve(v, t, g, D_DECK,
                 [(0.0, -0.25), (wr, -0.25), (wr, -0.43), (0.0, -0.43)], seg)
        _revolve(v, t, g, D_TRIM,
                 [(wr - 0.01, 0.0), (wr + 0.12, 0.0), (wr + 0.12, -0.28),
                  (wr - 0.01, -0.28)], seg)
        for i in range(n * 2):
            a = math.tau * i / (n * 2)
            _cyl(v, t, g, "prop_gallery_rail",
                 (wr + 0.06) * math.cos(a), (wr + 0.06) * math.sin(a),
                 0.0, 1.05, 0.035, seg=6)
        _revolve(v, t, g, "prop_gallery_rail",
                 [(wr + 0.02, 1.05), (wr + 0.10, 1.05), (wr + 0.10, 0.99),
                  (wr + 0.02, 0.99)], seg)

    # THE RING WALL, one deck high, in segments with the entry bay left out.
    for i in range(n):
        a0 = math.tau * i / n - math.tau / (2 * n) + ea
        a1 = a0 + math.tau / n
        if abs(((a0 + a1) / 2.0 - ea + math.pi) % math.tau - math.pi) < 1e-6:
            continue
        b0, b1 = a0 + GAP_A, a1 - GAP_A
        # THE WALL STOPS AT THE SILL -- see the rotunda's own note above and
        # INV-024. A dome whose viewports are buried in its wall is a dome
        # with no view, which is the whole of what this room is for.
        #
        # AND BOTH STOREYS ARE FRAMED PANELS RATHER THAN SLABS. Round 1's
        # finding on this program was *"roughly 80% of the frame is flat
        # panelled wall"*, and it was one prism per storey per bay. See
        # `_recessed_panel`, which both programs now call.
        _recessed_panel(v, t, g, r, ro, b0, b1, 0.155 - LAP_M, 0.95,
                        frame=D_FRAME, field="transit_wall", depth=0.065)
        _recessed_panel(v, t, g, r, ro, b0, b1, 0.95 + VIEWPORT_H_M,
                        DOME_WALL_M, frame=D_FRAME, field="transit_wall",
                        depth=0.065)
        # THE SKIRTING, where the wear is. A cool dark tread metal against the
        # grey panel: a difference in metallic as well as in value, so it
        # survives a change of lighting rather than vanishing under one.
        _seg(v, t, g, D_TRIM, r - 0.055, ro + 0.004, b0, b1, -0.02, 0.155)
        _seg(v, t, g, "transit_dado", r - 0.05, r, b0, b1, 0.155 - LAP_M,
             0.86 + LAP_M)
        # THE VIEWPORT, set into the bay -- `rooms.PROPS['viewport']`'s own
        # 2.4 x 1.4 m, converted to an angle at this radius rather than to a
        # second number.
        half = VIEWPORT_W_M / 2.0 / r
        am = (a0 + a1) / 2.0
        _seg(v, t, g, "prop_viewport", r + 0.055, ro - 0.055,
             am - half, am + half, 0.95, 0.95 + VIEWPORT_H_M)
        # THE SAME DIVISION THE ROTUNDA'S WINDOWS CARRY, and for both of its
        # reasons -- see the note there. A dark bar in the glass plane so the
        # window has lines for `density.py --machinery` to find, and a pale
        # cover strip proud of it so a viewer sees them. **This is the fix
        # applied to the rule and not to the instance** -- it was found on the
        # rotunda and both programs carry it, which is session 4h's own lesson
        # about the registry table.
        for f in (0.34, 0.66):
            ba = am - half + 2.0 * half * f
            _seg(v, t, g, "prop_viewport", r + 0.02, ro - 0.02,
                 ba - 0.010, ba + 0.010, 0.98, 0.92 + VIEWPORT_H_M)
            _seg(v, t, g, D_PALE, r - 0.05, r + 0.03, ba - 0.014, ba + 0.014,
                 0.97, 0.93 + VIEWPORT_H_M)
        ym = 0.95 + VIEWPORT_H_M * 0.46
        _seg(v, t, g, "prop_viewport", r + 0.02, ro - 0.02,
             am - half + 0.01, am + half - 0.01, ym - 0.020, ym + 0.020)
        _seg(v, t, g, D_PALE, r - 0.05, r + 0.03, am - half + 0.01,
             am + half - 0.01, ym - 0.028, ym + 0.028)
        # The jambs either side of the glass, and the head and sill reveals.
        for aa, bb in ((b0, am - half), (am + half, b1)):
            if bb - aa > 1e-4:
                _seg(v, t, g, D_FRAME, r + 0.006, ro + 0.006, aa, bb,
                     0.95 - LAP_M, 0.95 + VIEWPORT_H_M + LAP_M)
        _seg(v, t, g, D_PALE, r - 0.05, ro, b0, b1, 0.95 + VIEWPORT_H_M - LAP_M,
             0.95 + VIEWPORT_H_M + 0.09)
        _seg(v, t, g, D_PALE, r - 0.05, ro, b0, b1, 0.86, 0.95 + LAP_M)
        _seg(v, t, g, D_TRIM, r - 0.06, r + 0.02, am - half - 0.03,
             am - half + 0.01, 0.95, 0.95 + VIEWPORT_H_M)
        _seg(v, t, g, D_TRIM, r - 0.06, r + 0.02, am + half - 0.01,
             am + half + 0.03, 0.95, 0.95 + VIEWPORT_H_M)
        # THE BLUE WALL COURSE. `light_wall_course` is in
        # `export_scene.FIXTURE_LIGHTING` -- omni, 22000 K, energy_rel 0.44,
        # range 3.5 m, measured off the C&C frame -- so this one throws.
        # Recessed behind its own dark reveal so it reads as a course in the
        # wall and not as a painted stripe.
        _seg(v, t, g, M_RECESS, r - 0.10, r - 0.062, b0 + 0.02, b1 - 0.02,
             DOME_WALL_M - 0.50, DOME_WALL_M - 0.24)
        _seg(v, t, g, "light_wall_course", r - 0.062, r - 0.02, b0 + 0.03,
             b1 - 0.03, DOME_WALL_M - 0.44, DOME_WALL_M - 0.30)
        # A SERVICE RISER every third bay, and a cable tray behind the dado --
        # CRAFT 4's "a fitting is where a fitting would be needed". A watch
        # room's consoles are fed from somewhere.
        if i % 3 == 1:
            _seg(v, t, g, M_METAL, r - 0.115, r - 0.035, am - 0.030,
                 am + 0.030, 0.14, DOME_WALL_M - 0.52)
            for k in range(3):
                yy = 0.42 + k * 1.05
                _seg(v, t, g, D_TRIM, r - 0.135, r - 0.020, am - 0.046,
                     am + 0.046, yy - 0.036, yy + 0.036)
        # THE REVEAL BETWEEN BAYS -- the bay rhythm gets a shadow in it, and no
        # two ring solids share a face (INV-951).
        _seg(v, t, g, M_RECESS, r + 0.055, ro, a1 - GAP_A * 1.6,
             a1 + GAP_A * 1.6, 0.0, DOME_WALL_M)
        _seg(v, t, g, D_FRAME, r - 0.075, r + 0.03, a1 - GAP_A * 1.1,
             a1 + GAP_A * 1.1, 0.0, DOME_WALL_M)

    # THE CORNICE the dome springs from.
    _revolve(v, t, g, D_PALE,
             [(r - 0.30, DOME_WALL_M), (ro, DOME_WALL_M),
              (ro, DOME_WALL_M - 0.22), (r - 0.30, DOME_WALL_M - 0.10)], seg)

    # THE ANGLED BRACING. LOCATIONS.md §169, authority 1, and the one clause of
    # it that had never been built -- see `_strut`. A pair of struts per bay
    # from the head of each pier out to the dome's springing ring, which is
    # where a brace is structurally FOR something as well as visible.
    yb = DOME_WALL_M - 0.30
    for i in range(n):
        ab = math.tau * i / n - math.tau / (2 * n) + ea
        for s in (-1, 1):
            a2 = ab + s * math.tau / (2.6 * n)
            _strut(v, t, g, D_TRIM,
                   ((r - 0.06) * math.cos(ab), yb, (r - 0.06) * math.sin(ab)),
                   ((r - 0.34) * math.cos(a2), DOME_WALL_M + 0.42,
                    (r - 0.34) * math.sin(a2)), 0.045)

    # THE DOME, WITH THICKNESS, and the glazing under it.
    rise = r * DOME_RISE_FRAC
    _dome_solid(v, t, g, "transit_panel", r - 0.20, DOME_WALL_M, rise, 0.20,
                seg)
    # RADIAL SPOKE MULLIONS AND A BROAD CONCENTRIC RING BAND. LOCATIONS.md
    # §169 at authority 1, and the count comes from `components.DOME_MULLIONS`
    # because this is the same glass C&C looks through.
    for i in range(mull):
        a = math.tau * i / mull + ea
        _dome_rib(v, t, g, D_FRAME, r - 0.20, DOME_WALL_M, rise, a, 0.42, 0.17)
    # AND THE BULKHEAD IS PANELLED, which is the other half of the same
    # sentence and the reason the dome read as smooth plastic. Same call the
    # rotunda's dome makes, in this room's own materials.
    _dome_coffers(v, t, g, r - 0.20, DOME_WALL_M, rise, mull, ea, seg=seg,
                  minor=D_TRIM, band=D_PALE,
                  bands=(0.12, 0.26, 0.42, 0.62, 0.82))
    band = 0.55
    _revolve(v, t, g, D_PALE,
             [((r - 0.20) * math.cos(band * math.pi / 2) - 0.02,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.02,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)
               + 0.42),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.24,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2)
               + 0.42),
              ((r - 0.20) * math.cos(band * math.pi / 2) - 0.24,
               DOME_WALL_M + (rise - 0.02) * math.sin(band * math.pi / 2))],
             seg)
    # THE GLAZED PANEL between the spokes -- the thing you look through.
    _dome_solid(v, t, g, "prop_viewport", r - 0.34, DOME_WALL_M + 0.02,
                rise - 0.06, 0.05, seg)

    _dome_fittings(v, t, g, prog, r, n, ea)


def _dome_fittings(v, t, g, prog, r, n, ea):
    """Shutters, ladders, consoles, benches, boards -- per PLC-002 / PLC-030."""
    # BLAST SHUTTER LEAVES, stowed round the springing. PLC-001 lists blast
    # shutters for the dome and PLC-002 makes the shutter master this room's
    # control, so the leaves have to exist somewhere for it to close. Each leaf
    # is a plate on a carrier with a stow rail, because a shutter that is one
    # slab is a slab.
    if prog.get("shutters"):
        for i in range(n):
            a0 = math.tau * (i + 0.10) / n + ea
            a1 = math.tau * (i + 0.90) / n + ea
            _seg(v, t, g, "prop_blast_door", r - 0.62, r - 0.28, a0, a1,
                 DOME_WALL_M - 0.06, DOME_WALL_M + 0.60)
            _seg(v, t, g, D_TRIM, r - 0.66, r - 0.60, a0 - 0.01, a1 + 0.01,
                 DOME_WALL_M - 0.10, DOME_WALL_M + 0.64)
            for f in (0.22, 0.78):
                ac = a0 + (a1 - a0) * f
                _seg(v, t, g, M_METAL, r - 0.70, r - 0.63, ac - 0.014,
                     ac + 0.014, DOME_WALL_M - 0.02, DOME_WALL_M + 0.56)
        _console(v, t, g, (r - 0.62) * math.cos(ea + math.pi),
                 (r - 0.62) * math.sin(ea + math.pi), ea + math.pi)

    # THE SERVICE CRAWL's ladders. PLC-002 lists `service_ladder`.
    for i in range(prog.get("ladders", 0)):
        a = ea + math.pi * (0.55 + 0.90 * i)
        _seg(v, t, g, M_RECESS, r - 0.20, r - 0.13, a - 0.075, a + 0.075,
             0.18, DOME_WALL_M - 0.16)
        for k in range(9):
            _seg(v, t, g, "prop_service_ladder", r - 0.34, r - 0.16,
                 a - 0.038, a + 0.038, 0.30 + k * 0.30, 0.36 + k * 0.30)
        for s in (-1, 1):
            _seg(v, t, g, "prop_service_ladder", r - 0.34, r - 0.16,
                 a + s * 0.042, a + s * 0.056, 0.24, DOME_WALL_M - 0.20)

    # THE CONSOLES: PLC-002's dome-status console, PLC-030's two traffic
    # repeaters. Both stand on the deck facing the glazing.
    for i in range(prog.get("consoles", 0)):
        a = ea + math.pi + (0.0 if prog["consoles"] == 1
                            else (-0.42 + 0.84 * i))
        _console(v, t, g, (r * 0.52) * math.cos(a), (r * 0.52) * math.sin(a),
                 a)

    # THE BENCHES PLC-030 lists, on a ring facing out at the windows.
    for i in range(prog.get("benches", 0)):
        a = ea + math.tau * (i + 0.5) / prog["benches"]
        _seg(v, t, g, "prop_bench", r - 1.35, r - 0.90, a - 0.12, a + 0.12,
             0.40, 0.46)
        for rr in (r - 1.31, r - 0.94):
            _seg(v, t, g, "prop_bench", rr - 0.04, rr + 0.04, a - 0.11,
                 a + 0.11, 0.0, 0.40)

    # THE INSPECTION TERMINAL, and A PLAQUE AT EVERY WINDOW, not at four of
    # them. PLC-002 and PLC-030 both make the same demand of this room -- *"the
    # dome's 12 viewports each answer LOOK with the true bearing they face"*,
    # *"the gallery's 8 viewports name 8 true bearings"* -- so the plaque count
    # is the viewport count by definition, and building four of them would be
    # a room that fails its own acceptance check by construction.
    a = ea + math.pi * 0.72
    _seg(v, t, g, M_RECESS, r - 0.13, r - 0.095, a - 0.13, a + 0.13, 1.00,
         1.60)
    _seg(v, t, g, "prop_babcom_terminal", r - 0.10, r - 0.02, a - 0.10,
         a + 0.10, 1.05, 1.55)
    _seg(v, t, g, D_TRIM, r - 0.135, r - 0.025, a - 0.14, a + 0.14, 1.58, 1.63)
    for i in range(n):
        a2 = ea + math.tau * (i + 0.5) / n
        _seg(v, t, g, "prop_info_board", r - 0.07, r - 0.02, a2 - 0.055,
             a2 + 0.055, 0.52, 0.86)
        _seg(v, t, g, "sign_frame", r - 0.085, r - 0.062, a2 - 0.066,
             a2 + 0.066, 0.49, 0.89)

    # THE LEANING RAIL at the window ring. Nobody stands at a viewport with
    # their nose against the glass; every observation gallery ever built has a
    # rail set back far enough to lean on, and it is also what stops a body's
    # collision capsule from resting inside the glazing.
    for i in range(n * 2):
        a2 = ea + math.tau * (i + 0.5) / (n * 2)
        _cyl(v, t, g, "prop_gallery_rail", (r - 0.62) * math.cos(a2),
             (r - 0.62) * math.sin(a2), 0.0, 1.02, 0.032, seg=6)
    _revolve(v, t, g, "prop_gallery_rail",
             [(r - 0.66, 1.02), (r - 0.58, 1.02), (r - 0.58, 0.96),
              (r - 0.66, 0.96)], max(48, n * 4))
    _revolve(v, t, g, "prop_gallery_rail",
             [(r - 0.645, 0.58), (r - 0.595, 0.58), (r - 0.595, 0.53),
              (r - 0.645, 0.53)], max(48, n * 4))

    # THE COVE at the springing. A room whose whole point is looking OUT is lit
    # from behind the eye, not from overhead: the fittings wash the wall and
    # the glazing stays the brightest thing in the frame.
    #
    # AND THE RING OF EMISSIVE DECK POOLS IS GONE. `light_deck_channel_pool` is
    # emission energy 3.5 over a 0.42 m disc, twelve of them lying face-up on
    # the floor, and `docs/engine-4k-dome*.png` shows what that is: white
    # ellipses on the deck with a planter standing in the middle of each. A
    # floor does not emit. The light those pools were standing in for now comes
    # from the cove and the blue wall course, both of which are in
    # `export_scene.FIXTURE_LIGHTING` and therefore actually cast; what is left
    # on the deck is a bearing rose, which is what the deck is for.
    _revolve(v, t, g, "light_house_cove",
             [(r - 0.34, DOME_WALL_M - 0.14), (r - 0.28, DOME_WALL_M - 0.14),
              (r - 0.28, DOME_WALL_M - 0.24), (r - 0.34, DOME_WALL_M - 0.24)],
             max(48, n * 4))

    # THE BEARING ROSE inlaid in the deck. The room's content is which way it
    # faces, so the floor says so: a radial wedge per window bay about a hub.
    _pad(v, t, g, D_DECK,
         [(0.62 * math.cos(math.tau * k / 24), 0.62 * math.sin(math.tau * k / 24))
          for k in range(24)], 0.0, 0.012)
    for i in range(n):
        a2 = ea + math.tau * i / n
        _pad(v, t, g, D_DECK,
             [(0.70 * math.cos(a2), 0.70 * math.sin(a2)),
              ((r * 0.44) * math.cos(a2 - 0.045),
               (r * 0.44) * math.sin(a2 - 0.045)),
              ((r * 0.44) * math.cos(a2 + 0.045),
               (r * 0.44) * math.sin(a2 + 0.045))],
             0.0, 0.011)

    # A LEDGE UNDER EVERY WINDOW. What a person actually does at a viewport is
    # put something down and lean; `rooms.PROPS['counter']` is the station's
    # own ledge and one per bay is what makes the ring read as somewhere people
    # stay rather than a corridor with glass in it.
    for i in range(n):
        a2 = ea + math.tau * (i + 0.5) / n
        half = VIEWPORT_W_M / 2.4 / r
        _seg(v, t, g, "prop_counter", r - 0.30, r - 0.01, a2 - half, a2 + half,
             0.86, 0.95)
        _seg(v, t, g, D_TRIM, r - 0.31, r - 0.26, a2 - half - 0.004,
             a2 + half + 0.004, 0.905, 0.945)
        _seg(v, t, g, "prop_counter", r - 0.26, r - 0.20, a2 - half * 0.85,
             a2 - half * 0.70, 0.0, 0.86)
        _seg(v, t, g, "prop_counter", r - 0.26, r - 0.20, a2 + half * 0.70,
             a2 + half * 0.85, 0.0, 0.86)

    # THE PLOT TABLE. PLC-030 makes this dome the traffic annexe -- *"the
    # repeater shows the same berth map C&C shows, delayed 0 s"* -- so the room
    # has a table to spread a berth plot on, with stools round it. PLC-002's
    # dome has a well in the middle instead and gets none of this.
    #
    # ITS GLOW WAS A DISC AND IS NOW A RING. `light_dais_key` is emission
    # energy 6.0, and a 0.96 m radius disc of it lying flat in the middle of
    # the room is the white blob in `docs/engine-4k-dome2-*.png` -- the
    # brightest object in a frame whose subject is the window. A plot table is
    # lit at its edge and reads its chart off the surface; the ring is 90 mm
    # wide, which is 6% of the area it was.
    if not prog.get("well"):
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.0, 0.10, 0.62, seg=12)
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.10, 0.68, 0.24, seg=12)
        _cyl(v, t, g, "prop_table", 0.0, 0.0, 0.68, 0.78, 1.05, seg=20)
        _revolve(v, t, g, D_PALE,
                 [(0.0, 0.800), (1.02, 0.800), (1.02, 0.774), (0.0, 0.774)],
                 20)
        _revolve(v, t, g, "prop_tactical_display",
                 [(0.0, 0.792), (0.56, 0.792), (0.56, 0.782), (0.0, 0.782)],
                 20)
        _revolve(v, t, g, "light_dais_key",
                 [(1.005, 0.796), (1.045, 0.796), (1.045, 0.762),
                  (1.005, 0.762)], 20)
        for i in range(4):
            a2 = ea + math.tau * (i + 0.25) / 4
            _cyl(v, t, g, "prop_seat", 1.62 * math.cos(a2),
                 1.62 * math.sin(a2), 0.0, 0.44, 0.20, seg=8)
            _cyl(v, t, g, "prop_seat", 1.62 * math.cos(a2),
                 1.62 * math.sin(a2), 0.44, 0.49, 0.24, seg=10)

    # THE LOCKER BANK. A watch room stores its slates, its lamps and its
    # emergency kit somewhere, and a room whose fittings all hang on the wall
    # is a set rather than a place people work in.
    for i in range(2):
        a2 = ea + math.pi + (-0.62 + 1.24 * i)
        for k in range(3):
            _seg(v, t, g, "prop_locker", r - 0.52, r - 0.08,
                 a2 - 0.13 + k * 0.09, a2 - 0.05 + k * 0.09, 0.0, 1.92)
            _seg(v, t, g, D_TRIM, r - 0.10, r - 0.06,
                 a2 - 0.125 + k * 0.09, a2 - 0.055 + k * 0.09, 1.06, 1.10)
        _seg(v, t, g, "prop_locker", r - 0.56, r - 0.04, a2 - 0.15, a2 + 0.24,
             1.90, 2.02)

    # PLANTERS AND A WASTE BIN -- a gallery the public sits in is kept, and
    # `rooms.PROPS` already carries both.
    for i in range(max(2, n // 3)):
        a2 = ea + math.tau * (i + 0.28) / max(2, n // 3)
        _cyl(v, t, g, "prop_planter", (r * 0.72) * math.cos(a2),
             (r * 0.72) * math.sin(a2), 0.0, 0.62, 0.34, seg=10)
        _cyl(v, t, g, D_TRIM, (r * 0.72) * math.cos(a2),
             (r * 0.72) * math.sin(a2), 0.60, 0.68, 0.36, seg=10)


def _console(v, t, g, cx, cz, facing):
    """One watch console: a dark plinth, a sloping fascia, a screen, a lit lip.

    IT WAS TWO BOXES OF `prop_console`, and `prop_console` binds
    `device_console_bed` -- albedo 0.212 with a warm emission at energy 0.5.
    Over a 1.40 x 0.66 x 1.02 m pair of slabs that is a saturated orange block,
    which is what round 1 called out on this program (*"the ledges read as
    saturated orange blocks"* -- the same material, the same failure). A
    console is a machine: the body is casework, the emission belongs to the
    FASCIA and the screen, and the lit lip is 40 mm of it rather than a face.
    """
    c, s = math.cos(facing), math.sin(facing)

    def at(dx, dz):
        return (cx + dx * s + dz * c, cz - dx * c + dz * s)
    for (x0, y0, z0, x1, y1, z1, nm) in (
            (-0.70, 0.00, -0.33, 0.70, 0.10, 0.33, D_TRIM),
            (-0.66, 0.10, -0.30, 0.66, 0.80, 0.30, "prop_desk_panel"),
            (-0.70, 0.80, -0.33, 0.70, 0.86, 0.33, D_FRAME)):
        p0 = at(x0, z0)
        p1 = at(x1, z1)
        _box(v, t, g, nm, (min(p0[0], p1[0]), y0, min(p0[1], p1[1])),
             (max(p0[0], p1[0]), y1, max(p0[1], p1[1])))
    # the sloping fascia and its screen, tipped toward the operator
    for (x0, y0, z0, x1, y1, z1, nm) in (
            (-0.64, 0.84, -0.30, 0.64, 1.02, 0.02, D_FRAME),
            (-0.57, 0.885, -0.25, 0.57, 1.005, -0.03, "prop_monitor_wall"),
            (-0.60, 0.858, -0.285, 0.60, 0.878, -0.255, "prop_console"),
            (-0.26, 0.846, -0.312, 0.26, 0.872, -0.288, "light_wall_course")):
        p0 = at(x0, z0)
        p1 = at(x1, z1)
        _box(v, t, g, nm, (min(p0[0], p1[0]), y0, min(p0[1], p1[1])),
             (max(p0[0], p1[0]), y1, max(p0[1], p1[1])))
    # two cable runs down the back, because a console is fed from somewhere
    for dx in (-0.42, 0.38):
        p0 = at(dx, 0.30)
        _cyl(v, t, g, M_METAL, p0[0], p0[1], 0.06, 0.82, 0.035, seg=6)
    return v, t, g


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

    import collections
    import directory as dr
    import interact as ia
    import interior as it
    schema, profile = it.load()

    built = {}
    for key in sorted(PROGRAMS):
        q = dr.by_key(key)
        v, t, g = room(schema, profile, q)
        built[key] = (v, t, g)

        op, non = kit.boundary_edges(v, t)
        check(f"{key}: closed surface", not op, f"{len(op)} open edges")

        opening = _bsp.near_face_opening(v, t)
        check(f"{key}: a body can walk in at local x = 0",
              opening is not None and abs(opening[0]) < 0.35
              and opening[1] >= kit.PROVISIONAL["door_width_m"],
              f"{opening}")

        want = tuple(q.get("interacts") or ())
        got = ia.resolve(want, {n for n, _a, _b in g}, g)
        check(f"{key}: every declared interactable is built",
              set(got) == set(want), f"missing {sorted(set(want) - set(got))}")

        # THE DOME MUST HAVE AN INSIDE. `bespoke.py`'s audit measured the
        # exterior component and found **0 of its 192 triangles face a viewer
        # standing under it** -- every surface points out, so a player sees the
        # background, and the background is black. This is that measurement,
        # applied to the room, and it is the reason the dome is a solid with
        # thickness rather than a shell.
        eye = (0.0, 1.65, 0.0)
        inward = 0
        for a, b, c in t:
            p0, p1, p2 = v[a], v[b], v[c]
            u = [p1[i] - p0[i] for i in range(3)]
            w = [p2[i] - p0[i] for i in range(3)]
            nv = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                  u[0] * w[1] - u[1] * w[0])
            d = [eye[i] - p0[i] for i in range(3)]
            if sum(nv[i] * d[i] for i in range(3)) > 0.0:
                inward += 1
        check(f"{key}: the room has an inside", inward > len(t) * 0.25,
              f"only {inward} of {len(t)} triangles face an eye at the centre")

        print(f"  {key:14s} r={program(q)['r']:5.2f} m  {len(t):7,d} tri  "
              f"{len(g):4d} groups  open={len(op)} nonmanifold={len(non)}  "
              f"{inward * 100.0 / max(1, len(t)):.0f}% facing in")

    # THE THREE MUST BE THREE ROOMS, NOT ONE. Session 4h: `deck.py
    # --degeneracy` asks IDENTITY, not similarity, because two places whose
    # geometry hashes the same ARE one place -- and the defect it found was
    # exactly this module's shape, a registry entry that dropped `q`.
    import hashlib
    hashes = {}
    for key, (v, t, _g) in built.items():
        h = hashlib.sha256()
        for p in v:
            h.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        hashes[key] = h.hexdigest()[:12]
    dupes = [k for k, c in collections.Counter(hashes.values()).items() if c > 1]
    check("the three places are three distinct geometries", not dupes,
          f"{hashes}")

    # NEGATIVE CONTROL -- drop the place and they collapse. Without this the
    # gate above cannot fail: it would pass on a module that reads the place
    # and on one that ignores it, if the three happened to differ for some
    # other reason.
    ctl = set()
    for key in sorted(PROGRAMS):
        v, _t, _g = room(schema, profile, dr.by_key("obs_rotundas"))
        h = hashlib.sha256()
        for p in v:
            h.update(f"{p[0]:.4f},{p[1]:.4f},{p[2]:.4f};".encode())
        ctl.add(h.hexdigest()[:12])
    check("...and with the place ignored they collapse to one", len(ctl) == 1)

    # THE COUNTS ARE THE SPEC'S. PLC-002 lists 12 viewports, PLC-030 lists 8,
    # PLC-064 lists 8. A viewport count is content, so it is asserted rather
    # than left to the reader of a constant.
    for key, want_n in (("obs_dome_1", 12), ("obs_dome_2", 8),
                        ("obs_rotundas", 8)):
        g = built[key][2]
        n = sum(1 for nm, _a, _b in g if nm == "prop_viewport")
        lo = want_n if PROGRAMS[key]["kind"] == "dome" else ROTUNDA_BAYS - 1
        check(f"{key}: {lo} glazed bays, as the spec lists", n >= lo,
              f"{n} viewport spans against {lo}")

    # ---------------------------------------------------------------------
    # SESSION 4t's THREE GATES. Each one fails on the content this session
    # started from, and the control that makes it fail is in this file.
    # ---------------------------------------------------------------------
    import materials as mats

    # (1) NO COINCIDENT FACES. `boundary_edges` already returned the count and
    # nothing had ever asserted on it: 489 on the rotunda, 360 and 209 on the
    # domes, all of them invisible because a face used by four triangles
    # renders perfectly. AAA-STANDARD's geometry checklist is explicit --
    # "Non-manifold edges: zero. A face used by three triangles is a modelling
    # error that renders perfectly."
    for key, (v, t, _g) in built.items():
        _op, non = kit.boundary_edges(v, t)
        check(f"{key}: no non-manifold edge", not non, f"{len(non)} edges")

    # ...AND THE CONTROL. `LAP_M` is what makes solids overlap instead of
    # abut and `_dome_rib`'s `f_max` is what stops a rib pinching on the axis;
    # withdraw both and the defect comes back, which is the evidence that the
    # assertion above is measuring the fix rather than an accident.
    _lap, _mod = LAP_M, sys.modules[__name__]
    _rib = _dome_rib
    try:
        _mod.LAP_M = 0.0
        _mod._dome_rib = lambda *a, **k: _rib(*a, **{**k, "f_max": 1.0})
        ctl_non = {}
        for key in sorted(PROGRAMS):
            v2, t2, _ = room(schema, profile, dr.by_key(key))
            ctl_non[key] = len(kit.boundary_edges(v2, t2)[1])
    finally:
        _mod.LAP_M = _lap
        _mod._dome_rib = _rib
    check("...and with the overlap rule withdrawn they come back",
          all(c > 0 for c in ctl_non.values()), f"{ctl_non}")

    # (2) EVERY GROUP CARRIES A MATERIAL SOMEBODY CHOSE. Session 4f's lesson
    # is that a name built by interpolation is invisible to the source scan in
    # `materials._scan_generator_groups`, so 45 groups sat on the fallback and
    # nothing could see it. This module now composes `<bound>_<shell-suffix>`
    # names deliberately (INV-950), which is exactly the shape that goes
    # unnoticed, so it asserts resolution HERE, in the module that builds them.
    for key, (_v, _t, gg) in built.items():
        unbound = sorted({nm for nm, _a, _b in gg
                          if mats.resolve_any(nm, "interior") is None})
        check(f"{key}: every group resolves to a material", not unbound,
              f"{unbound}")

    # (3) THE SURFACE IS NOT ONE VALUE. Round 1 scored both programs CRAFT 2 --
    # "each material carries one flat value", "grey-on-grey at half distance"
    # -- and the cause was that every `worship_*` and `transit_*` group in
    # `materials.py` resolves to one of three greys. A count of DISTINCT
    # resolved materials is the cheap universal form of that question, in the
    # spirit of `deck.py --degeneracy`: it asks identity, not similarity, so
    # there is no threshold to argue with beyond the floor itself.
    used = {}
    for key, (_v, _t, gg) in built.items():
        used[key] = {mats.resolve_any(nm, "interior").name
                     for nm, _a, _b in gg
                     if mats.resolve_any(nm, "interior")}
        check(f"{key}: at least 14 distinct materials on the surface",
              len(used[key]) >= 14, f"{len(used[key])}: {sorted(used[key])}")

    # ...AND THE CONTROL, which is the room this session started from: put the
    # palette back to the shell names and count again.
    _saved = {k: getattr(_mod, k) for k in _PALETTE}
    try:
        for k in _PALETTE:
            setattr(_mod, k, "worship_wall" if not k.startswith("L_")
                    else "light_pilaster_strip")
        ctl = {}
        for key in sorted(PROGRAMS):
            _v2, _t2, g2 = room(schema, profile, dr.by_key(key))
            ctl[key] = len({mats.resolve_any(nm, "interior").name
                            for nm, _a, _b in g2
                            if mats.resolve_any(nm, "interior")})
    finally:
        for k, val in _saved.items():
            setattr(_mod, k, val)
    # A FIFTH, not a fixed number: the domes keep more of their materials
    # under the control than the rotunda does, because a watch room's consoles,
    # lockers, seats, doors and rails are already varied and it is the SHELL
    # that was one value. Measured: 21 -> 16, 23 -> 18, 27 -> 11.
    check("...and with the palette collapsed to the shell names it falls",
          all(ctl[k] <= len(used[k]) * 0.8 for k in ctl),
          f"control {ctl} against {({k: len(u) for k, u in used.items()})}")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
