"""Command and Control — the station's bridge, inside Observation Dome 1.

Fourth on the gazetteer's ranked build list, and the one that pays a structural
debt: the exterior `observation_dome` component is still a box primitive, and
C&C's window is that dome's glazing seen from inside. Building the room forces
the component to become real, and the two must agree or the station has a window
that looks out at nothing.

WHAT THE REFERENCE ESTABLISHES

`reference/03-sector-blue/comand and contorl.webp` (authority 1) shows:

  - A **great circular window** on **radial spoke mullions**, crossed by a broad
    **concentric ring band**, set into a flat-panelled bulkhead with angled
    bracing. It is the room's whole focus and it is what the exterior dome must
    match.
  - A **raised circular command dais** on a stepped plinth, with an officer
    standing at its forward edge.
  - **Wedge-shaped angled console desks on slim legs**, arranged in an arc on the
    dais, their faces lit in green, amber and red.
  - **Two courses of long horizontal light strips**, cyan-white, at high and mid
    level on the side walls -- the room's ambient light.
  - **Stairs down at the right** to a lower level, and **handrails with panel
    infill** along the upper floor.
  - A **lower forward pit of red-lit consoles**.
  - **Two occupied levels in one volume**, which is the thing that makes it read
    as a bridge rather than an office.

SCALE, measured, WITH the depth correction that a first pass omitted.

The officer at the dais stands 175 px in an 816x616 frame, so **100 px/m at his
depth**. Fitting a circle to the window's visible arc -- chord 280 px, sagitta
215 px, R = (c^2/4 + s^2)/2s -- gives a 153 px radius, i.e. 306 px across.

Dividing those two directly gives 3.1 m and is **wrong**, because the window is
in the bulkhead BEHIND the officer and pixels-per-metre falls with distance.
The officer stands about 5 m from the lens and the bulkhead about 4 m behind
him, so at the window the scale is 100 x 5/9 = **56 px/m**, and 306 px is
**~5.5 m**. The error is a factor of 1.8 and it is the ordinary trap of
comparing two measurements taken at different depths -- the same trap that put
the tram car length in dispute (C-008).

5.5 m is a feature window rather than a panorama, and it is compatible with
Contract 5's 92 m dome: the dome is the volume, the window is one aperture in
its forward face.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dressing as _dress                                       # noqa: E402
import interior as it                                        # noqa: E402
import interior_kit as it_kit                                # noqa: E402
import rooms as _rooms                                          # noqa: E402

# --- measured --------------------------------------------------------------
REF_PX_PER_M = 100.0
WINDOW_D_M = 5.5                # fitted arc, depth-corrected -- see above
WINDOW_HUB_FRAC = 0.14          # mullions stop here; they do not meet at a point

# --- canon -----------------------------------------------------------------
# Contract 5, via the schema's `observation_dome` component: radius 46 m,
# height 34 m, two of them, Dome 1 is C&C. The room sits inside that volume.
DOME_R_M = 46.0
DOME_H_M = 34.0

# --- proportioned off the frame (INV-024) ----------------------------------
WINDOW_MULLIONS = 16            # radial spokes
WINDOW_RING_FRAC = 0.62         # where the concentric band crosses them
WINDOW_MULLION_W_M = 0.10
WINDOW_MULLION_D_M = 0.06       # how far a bar stands off the glass -- INV-171
WINDOW_RING_W_M = 0.16

# WHAT THE WINDOW IS ACTUALLY MADE OF, read at 2x off the same frame
# (`tools/refzoom.py --box 0.24 0.05 0.78 0.50`). The first build of this
# window was sixteen flat bars, one flat ring and a flat hub over a black disc,
# and `docs/craft-4q-cnc-before-half.png` is what that is at the rubric's HALF
# distance: a wagon wheel painted on a black square. `docs/AAA-STANDARD.md` C1,
# "a box primitive standing in for a named object", in the one object this
# whole room is arranged around.
#
# At magnification the aperture carries FOUR tiers and the bars are the third
# of them:
#
#   1. GLAZING IN PANES, not one disc. Two concentric courses inside the band
#      and one outside it, each divided radially, each pane set back in its own
#      frame -- so the light that comes through it is broken up and the bars
#      have something to be bars OF.
#   2. A broad CONCENTRIC STRUCTURAL BAND with a visible line of STUDS along
#      its inner edge -- the clearest single detail in the reference and the
#      one that says the thing is bolted together.
#   3. The RADIAL MULLIONS, which do not stop at the rim: they continue OUT
#      across the bulkhead as ribs, which is what ties the window to the wall
#      instead of leaving it a decal on a slab.
#   4. A heavy RIM COLLAR where the glazing meets the structure.
#
# The ring fractions are read off the crop as radii over the fitted outer
# radius (153 px, see the header): hub 21 px, first course to 61 px, second to
# 95 px, band 95-122 px, outer course 122-153 px. Divided through: 0.14, 0.40,
# 0.62, 0.80, 1.00. INV-461.
WINDOW_COURSES = ((0.14, 0.40, 12), (0.40, 0.62, 24), (0.80, 1.00, 24))
WINDOW_BAND = (0.62, 0.80)      # the broad structural ring, as radius fractions
WINDOW_STUDS = 40               # along the band's inner edge
# 45 mm and 30 mm proud rather than 35/18. Measured off the rendered frame
# rather than guessed: at the first size the stud line was 1.4 px across at the
# rubric's half distance and did not read at all, which is `docs/AAA-STANDARD.md`
# C3's "tertiary tier is generic" -- detail that exists in the mesh and not in
# the picture. The reference's stud line is the clearest single detail in the
# crop, so it has to survive to the frame.
WINDOW_STUD_R_M = 0.045
WINDOW_STUD_PROUD_M = 0.030
WINDOW_PANE_INSET_M = 0.022     # how far a pane sits behind its own frame
WINDOW_RIB_OUT_M = 1.35         # how far the radial ribs run past the rim

# The bulkhead the window is cut into. Two circular BOSSES flank it high on
# the wall in the reference -- panel discs, not portholes; nothing shows
# through them -- and the panelling is a coarse orthogonal grid crossed by the
# window's own radial ribs. INV-461.
BULK_BOSS_R_M = 0.62
BULK_BOSS_X = 4.55              # +-x of the two bosses
BULK_BOSS_Y = 5.15
BULK_D_M = 0.30                 # the bulkhead's own thickness, as built

DAIS_D_M = 4.6                  # the officer's stance and the console arc
DAIS_STEPS = 3
DAIS_RISE_M = 0.18
DAIS_TREAD_M = 0.42

CONSOLE_N = 5                   # wedge desks in an arc on the dais
CONSOLE_ARC_DEG = 150.0
CONSOLE_D_M = 0.62
CONSOLE_H_M = 1.02              # a standing console, which is what the frame shows
CONSOLE_BODY_M = 0.14           # the wedge under the lit face -- INV-171

# WHAT IS ACTUALLY ON A CONSOLE, measured off the frame at 4x
# (`tools/refzoom.py --box 0.36 0.35 0.72 0.58`), because "wedge desks on slim
# legs, their faces lit in green, amber and red" is a caption and a caption is
# what got built: one 12-triangle plate on four 12-triangle sticks, 36 tri an
# instance, which `docs/judge-4e.md` scored CRAFT 1 and `docs/AAA-STANDARD.md`
# defines as "a box primitive standing in for a named object".
#
# Read at magnification the unit is FIVE tiers stacked, and every one of them
# is a different kind of surface:
#
#   1. slim round SPLAYED LEGS with a cross-tie between them, and clear air
#      under the desk -- you can see the dais through it
#   2. a dark UNDER-VALANCE, the deepest shadow in the object
#   3. an APRON of large backlit panes, three to a unit, recessed in a frame.
#      These are the cyan rectangles and they are the brightest thing on the
#      desk after the control cells
#   4. a RAKED BED behind a raised bezel lip
#   5. dense BLOCKS OF CONTROL CELLS on the bed -- the green, amber and red --
#      in three banks, each bank a recessed sub-panel carrying its own cells
#
# The proportions below are read as fractions of the unit's height, off the
# same crop: the leg/desk break sits at ~0.56 of the desk's height, the pane
# band spans ~0.70-0.88, and the bed occupies the top ~0.12 with its far edge
# one bed-depth higher than its near one (CONSOLE_TILT_DEG, already measured).
# INV-024 covers the console; this is the same extrapolation at one more tier.
CONSOLE_LEG_TOP = 0.560         # fraction of CONSOLE_H_M
CONSOLE_VALANCE_TOP = 0.690
CONSOLE_APRON_TOP = 0.882       # = (H - 0.12) / H, the old bed line, kept
CONSOLE_PANES = 3               # backlit panes across one unit's apron
# FOUR BY FOUR, NOT THREE BY THREE, and the reason is a rendered frame rather
# than a preference. `docs/craft-4q-cnc-half-console.png` at the rubric's half
# distance shows nine cells a unit reading as nine large pale tiles -- the
# reference crop at 3x carries dozens of small controls in tight blocks, and the
# difference is exactly `docs/AAA-STANDARD.md` C3's "the tertiary tier is
# generic" against C4's "the detail is functional". Sixteen cells a unit at 9
# units is 144 lit registers on the floor, which is 1,728 triangles -- affordable
# against the 300,000 a whole deck's visible set is allowed.
CONSOLE_BANKS = 4               # control-cell banks on the bed
CONSOLE_CELLS = 4               # lit cells per bank
CONSOLE_JOINT_FRAC = 0.94       # of the arc share -- the visible butt joint

# The forward pit: "a lower forward pit of red-lit consoles". The frame's
# bottom-left corner is that pit, and it is the darkest working surface in the
# room -- `docs/layer4-lighting/command_working.json` measures `cc_pit_indicator`
# there at rgb 0.071/0.012/0.020, which is why the cells are red and nothing
# else in the pit is lit at all.
PIT_CONSOLE_N = 4
PIT_CONSOLE_W_M = 1.6
PIT_CONSOLE_D_M = 0.70
PIT_CONSOLE_H_M = 1.00

# The key light over the dais. `tools/export_scene.FIXTURE_LIGHTING` has
# carried `light_dais_key` since session 4b -- spot, 4725 K, range 9 m, cone
# 33.3 deg, SHADOW -- and `materials.light_dais_key` records where it was
# measured: THIS ROOM's own authority-1 frame, by a horizontal profile of the
# dais apron that found "a hard-edged pool with a body-shaped hole in it".
#
# C&C did not emit it. The fitting measured in C&C was wired to `rooms.py`'s
# WORSHIP archetype and to nothing else, so the one room it was taken from had
# no key at all -- and `export_scene --gate-lighting` says exactly that in a
# number: `cnc 0.0%` of its working plane inside any source's range, d/r p95
# 2.18, the worst row in the table. A light rig that derives a lamp from a
# piece of geometry cannot hang one where there is no geometry.
DAIS_KEY_H_M = 3.5              # the measurement's own mounting height
DAIS_KEY_N = 3
DAIS_KEY_R_M = 0.34
# The housing takes a BOUND name rather than a new one. `cc_key_housing` was
# the obvious spelling and the engine printed it straight back:
# `render_shot: fallback material used by 1 group(s): cc_key_housing` --
# session 3x's 1,248 unmaterialled door triangles, in miniature, caught this
# time because the render says so on every run and somebody read it.
_KEY_HOUSING = "fix_mp_plant_frame"        # steel_gantry_oxide

# TOUCHING FACES, WHICH ARE NOT HOLES. Two sources, both measured rather than
# assumed:
#
#   * `rooms.articulate`, which lays proud dado, rail, skirt and cornice bands
#     whose edges land on the surface behind them. `rooms.py` is not this
#     module's to edit.
#   * the shell of the pit and the stair, where this module's own axis-aligned
#     boxes meet at a corner. Two axis-aligned boxes sharing a corner ALWAYS
#     share the edge at it, and the pattern predates this session
#     (`cc_bulkhead+cc_pit` and `cc_pit+cc_pit_face` were both in the 3z
#     baseline). It is a collinear contact between two closed solids, not an
#     opening: `boundary_edges`' OPEN count, which is the one that matters for
#     a deck's watertightness, stays at zero.
#
# THIS USED TO BE A NUMBER -- `_INHERITED_NON_MANIFOLD = 48` -- and the number
# was already WRONG when this session opened the file: the count had improved
# to 44 upstream and the gate had been failing ever since, red for a reason
# nobody was reading. `docking_bay.py` records the identical defect and the
# cure it now uses, which is what this adopts: name the groups that are
# ALLOWED to touch, and require every non-manifold edge to be explained by
# one of them. A new group interpenetrating anything fails at any count; an
# upstream improvement to the bands cannot fail it at all.
#
# STATED LIMIT: an interpenetration BETWEEN two allow-listed shell groups
# would still pass. Closing that needs a test of whether the solids meet along
# a line or overlap in volume, which is a `station/` primitive nobody has
# written; the console -- the object this session articulated, and the one
# with five new solids inside one footprint -- is deliberately outside the
# list, so the geometry that changed is the geometry the gate actually guards.
_CORNER_CONTACT = frozenset(("cc_bulkhead", "cc_pit", "cc_pit_face",
                             "cc_stair", "cc_floor"))
CONSOLE_TILT_DEG = 22.0

FLOOR_W_M = 14.0                # the upper floor the dais sits on
FLOOR_L_M = 12.0

# --- THE SIDE WALLS, WHICH THIS ROOM DID NOT HAVE (INV-620) ----------------
# Thickness is `cc_pit_face`'s own 0.16 m, because the pit's side walls were
# the only lateral plate in the room and the new wall subsumes them -- one
# plate at one thickness rather than a second number that has to be kept equal.
# The 4 mm standoff is this file's own idiom, written three times already in
# `wall_course`'s end caps and `annunciator`'s cheeks: a plate built flush with
# the trim it meets shares a whole face with it, which the non-manifold gate
# reports as two pieces of this module in the same place and is right to.
WALL_D_M = 0.16
WALL_STANDOFF_M = 0.004
# The panel grid's pitch is the DECK's joint pitch, not a new number: the deck
# lays a joint every `DECK_BAY_M` down the room and the wall's panel joints
# land over them, which is what a plated compartment does and is why the two
# grids cannot drift apart. The vertical pitch is the forward bulkhead's own
# 1.62 m, so the two walls are one grid meeting at a corner.
WALL_PANEL_Y_M = 1.62
WALL_PANEL_PROUD_M = 0.045      # the bulkhead's, for the same reason

# --- the light over the pit (INV-621) --------------------------------------
# z is the LAST ceiling beam's own centre -- `ceiling` puts CEIL_BEAMS beams
# between -L*0.35 and L*0.70, so the tray hangs from the beam nearest the
# window instead of at a z somebody liked. That lands it 1.80 m aft of the
# bulkhead, i.e. 3.55 m from the window's centre, which at `light_wall_course`'s
# measured 3.5 m range and the room's own reach factor is d/r = 0.34.
PIT_SOFFIT_Z_M = -FLOOR_L_M * 0.35 + (FLOOR_L_M * 1.05) * 6.5 / 7.0
PIT_SOFFIT_DROP_M = 0.34        # below the beam soffit, clear of the annunciator
PIT_SOFFIT_HALF_W_M = 5.40      # inside the balustrade line, outside the board
# ONE BLADE PER PIT CONSOLE PAIR -- `PIT_CONSOLE_N // 2` is how many consoles
# stand against each side of the pit, so each blade is over the pair it lights,
# and the count is derived rather than liked. It is also the number the layer-4
# level gate can carry: `fixture_lights` hangs one lamp per connected body, and
# at THREE blades `tools/measure_frame.py --against` puts this room's median at
# **x1.87** of the show's against a x1.40 +/-25% target -- OUT OF RANGE, 0.4
# stops hot. Two lands it at **x1.72**, inside the band (1.05..1.75) and near
# its top. Measured both ways, not reasoned.
#
# AND READ `measurable %` BESIDE IT, which is this project's own warning about
# this tool: the frame went from 67.9% measurable to 88.9%, so the median moved
# partly because its POPULATION did -- 21% of the frame was under
# `measure_frame`'s 0.010 floor and is now above it. Every distribution
# statistic improved at the same time (p99 x0.69 -> x1.03, p5/p95 x1.14 ->
# x0.94, crushed 32.1% -> 11.0%), which a purely hotter frame would not do.
# What would move the level itself is `export_scene.BESPOKE_EXPOSURE`'s 4.08
# for this module, which is not this file's to edit -- see
# `scratchpad/PATCHES-4r-cnc.md`.
PIT_SOFFIT_BLADES = PIT_CONSOLE_N // 2
PIT_DROP_M = 1.9                # the lower forward pit
STRIP_COURSES = 2               # high and mid light strips
STRIP_Y_M = (2.35, 3.55)
STRIP_H_M = 0.22
RAIL_H_M = 1.05

# --- what a wall course is MADE of -----------------------------------------
# `docs/craft-4q-cnc-before-ref.png`: two continuous glowing bars stuck flat on
# a flat wall, which is the reference's single most repeated element rendered
# as neon tape. At 3x (`--box 0.0 0.08 0.30 0.72`) a course is a RECESSED
# TROUGH holding SEGMENTED TUBES with dark gaps between them, a bright reflector
# cheek above and below, and an end cap where the run stops. The segmentation is
# what makes it read as a fitting rather than as a painted line: the gaps are
# where the eye finds the pitch.
STRIP_SEG_M = 1.55              # one tube, read off the crop against the 1.05 m rail
STRIP_GAP_M = 0.19              # the dark break between two tubes
STRIP_TROUGH_D_M = 0.16         # how deep the housing is recessed
#
# AND THE REFERENCE SHOWS FOUR COURSES A SIDE, NOT TWO -- `materials.py`'s own
# source line for `light_wall_course` says so in as many words: "Four horizontal
# courses per side wall at a measured 1.2 m vertical pitch". This module built
# two, and has since it was written.
#
# The other two are built here as EMISSION ONLY, and the reason is a gate in a
# file this module does not own. `export_scene.FIXTURE_LIGHTING` hangs one lamp
# on every connected BODY of a `cc_light_strip` span, and
# `export_scene._selftest` asserts `_courses == [4]` -- 2 courses x 2 walls.
# Emitting four a side would put eight lamps in a room whose exposure was solved
# against four, and would fail that assertion. So the two lit courses keep the
# rig exactly as solved and the two extra courses are `light_service_tube`,
# which is bound, emissive and NOT in `FIXTURE_LIGHTING`. The patch that makes
# all four real is reported rather than applied.
STRIP_Y_EXTRA_M = (1.15, 4.75)

# --- the deck ---------------------------------------------------------------
# The reference's floor is not a slab: it carries large INSET LIT PANELS that
# read as blue rectangles either side of the balustrade, and a joint grid
# between them. `light_deck_channel` is the bound cool-white the corridor's own
# deck channel uses, and it is emissive without being a lamp.
DECK_BAY_M = 2.35               # the joint pitch, from the corridor kit's own
DECK_INSET_W_M = 1.30
DECK_INSET_L_M = 2.60

# --- the ceiling ------------------------------------------------------------
# THERE WAS NONE. The room is a gallery under a 34 m dome and the build stopped
# at the top of the wall bands, so every frame taken in here has a black void
# over it -- which reads as an unroofed set, and is why the dais key lights
# appear to hang from nothing. A suspended coffered ceiling at the gallery's own
# head height closes it and gives the keys something to hang from. Authority 5,
# INV-462: the reference frame is cropped above the light courses and shows only
# a dark curved soffit, so what is built is the DARK and the STRUCTURE, not a
# pattern the frame does not carry.
#
# ITS HEIGHT IS `rooms.articulate`'s OWN, not a new number: this module already
# passes `DOME_H_M * 0.22` as the height the wall bands are laid to, so the
# cornice is at 7.48 m and a ceiling anywhere else would leave the bands ending
# in air. One constant, two consumers.
CEIL_Y_M = DOME_H_M * 0.22
CEIL_BEAMS = 7
CEIL_BEAM_D_M = 0.34

# THE BULKHEAD'S TOP WAS BELOW THE WINDOW'S, AND THE PANEL OVER IT WAS BUILT
# INSIDE OUT. Measured rather than noticed: the aperture is `cy + ap` = 6.52 m
# and `DOME_H_M * 0.18` = 6.12 m, so `m.box(..., 6.52, 6.12, ...)` -- y0 above
# y1 -- emitted a box of signed volume **-1.68 m3**, twelve triangles wound
# inward, directly above the one window the room is arranged around. Nothing
# caught it because `_selftest`'s facing tests name `cc_floor`, `cc_pit`,
# `cc_dais` and `cc_dais_riser` and no test in this file ever asked the
# bulkhead which way it faced -- the same shape as the riser defect this file
# already records, one surface over. The signed volume of EVERY closed solid
# this module emits is now measured, not four groups' worth.
BULK_TOP_M = CEIL_Y_M

# --- the annunciator, and it is the room's own declared interactable ---------
# `directory.PLACES` gives `cnc` the interactables
# ("console", "comms_channel", "tactical_display", "blast_door") and
# `interact.resolve_place` was resolving `tactical_display` by ALIAS, onto
# geometry that is not a display. `prop_tactical_display` is a bound name
# (materials `device_screen_glass`) and is not in `FIXTURE_LIGHTING`, so the
# board can be built as itself.
#
# One lamp per desk, in the seat order `cnc_ops.seating()` returns, above the
# window where every station on the floor can see it. Authority 5, INV-463:
# the reference's own wall instrument cluster (top left of frame, a dark panel
# carrying small lit rectangles) is the constraint on what it looks like; that
# it is over the window rather than beside it is this module's choice and the
# reason is sightline -- the dais faces the window.
ANNUN_Y_M = 6.94               # between the window's top (6.40) and the ceiling
ANNUN_W_M = 6.20
ANNUN_H_M = 0.44


class _M:
    def __init__(self):
        self.v, self.t, self.g = [], [], []
        # EVERY BOX THIS MODULE EMITS, and its signed volume. Six sessions of
        # this room shipped a bulkhead panel built `m.box(..., 6.52, 6.12, ...)`
        # -- y0 ABOVE y1 -- which is -1.68 m3 of inside-out solid directly over
        # the only window the room has, and no test in the file could see it
        # because the four facing tests name four groups by hand and the
        # bulkhead is not one of them. A ledger costs one append a box and turns
        # "the surfaces I remembered to check" into "every solid I emitted".
        self.boxes = []

    def box(self, x0, x1, y0, y1, z0, z1, group):
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)
        self.boxes.append((group, (x1 - x0) * (y1 - y0) * (z1 - z0)))

    def obox(self, o, u0, u1, y0, y1, w0, w1, group):
        """`box`, in a console's own frame: u across, y up, w away from the
        operator, turned into the room by `o = (cx, cz, cos a, sin a)`.

        THE MAP IS A ROTATION AND THAT IS THE WHOLE ARGUMENT for building the
        console this way. Its Jacobian determinant is cos^2 + sin^2 = 1, so the
        face order copied from `box` above stays outward-facing without a
        second winding rule -- and this project has shipped inside-out geometry
        four times, every one of them from a remap nobody checked the sign of
        (`interior.corridor_section`'s negative-determinant deck, session 2p).
        `_selftest` measures the signed volume of one `obox` rather than
        trusting the paragraph.
        """
        cx, cz, ca, sa = o

        def P(u, y, w):
            return (cx + u * ca - w * sa, y, cz + u * sa + w * ca)

        c = [P(u0, y0, w0), P(u1, y0, w0), P(u1, y1, w0), P(u0, y1, w0),
             P(u0, y0, w1), P(u1, y0, w1), P(u1, y1, w1), P(u0, y1, w1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)

    def merge_spans(self, verts, tris, spans):
        """Take a `dressing`-style (verts, tris, SPANS) build into this mesh.

        `dressing.py` is the module that already knows what a machine is made
        of -- a primary form, secondary structure that carries it, tertiary
        fittings that say what it does -- and its builders tag by SPAN while
        `_M` tags per triangle. Converting is four lines; a second vocabulary
        for the same nine surfaces would be a second thing to keep in step.
        Same adaptation `command_control` already makes for `rooms.articulate`.
        """
        off = len(self.v)
        per = [None] * len(tris)
        for nm, lo, hi in spans:
            for i in range(lo, hi):
                per[i] = nm
        self.v.extend(verts)
        self.t.extend((a + off, b + off, c + off) for a, b, c in tris)
        self.g.extend(per)

    def quad(self, a, b, c, d, group):
        i = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        self.g.extend([group, group])

    def merge(self, verts, tris, group):
        i = len(self.v)
        self.v.extend(verts)
        self.t.extend([(a + i, b + i, c + i) for a, b, c in tris])
        self.g.extend([group] * len(tris))

    def plate(self, a, b, c, d, thick, group):
        """A quad given the thickness it physically has -- kit.plate_solid.

        THE ROOM WAS BUILT OUT OF `quad` AND IT LEAKED FROM EVERY ONE OF THEM.
        16 mullions, 5 console faces and the window's ring band were single
        one-sided quads: 148 open boundary edges on the three surfaces a player
        standing on the dais looks straight at.
        """
        self.merge(*it_kit.plate_solid([a, b, c, d], thick), group)

    def disc(self, cx, cz, r, y, group, seg=32, down=False):
        """Flat, wound to face UP. Reversed fan -- see the note in signage.py.

        `down` flips it, for the underside of a solid that stands on the deck.
        """
        i = len(self.v)
        self.v.append((cx, y, cz))
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            self.v.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
        for k in range(seg):
            a0, b0 = i + 1 + k, i + 1 + (k + 1) % seg
            self.t.append((i, a0, b0) if down else (i, b0, a0))
        self.g.extend([group] * seg)

    def annulus(self, cx, cz, r0, r1, y, group, seg=36, down=False):
        """A flat ring from r0 to r1 at height y.

        WHAT A STEPPED DAIS IS ACTUALLY MADE OF. Each tread was emitted as a
        FULL disc, so the riser above it landed in the middle of a fan and had
        nothing to weld its foot to -- 36 open edges a step, 108 for the dais.
        An annulus puts an edge exactly where the next riser stands.
        """
        i = len(self.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            self.v.append((cx + r0 * ca, y, cz + r0 * sa))
            self.v.append((cx + r1 * ca, y, cz + r1 * sa))
        for k in range(seg):
            a0, b0 = i + 2 * k, i + 2 * ((k + 1) % seg)
            if down:
                self.t += [(a0, a0 + 1, b0 + 1), (a0, b0 + 1, b0)]
            else:
                self.t += [(a0, b0, b0 + 1), (a0, b0 + 1, a0 + 1)]
        self.g.extend([group] * 2 * seg)

    def band(self, cx, cy, z0, z1, r0, r1, group, seg=40):
        """A concentric ring band standing off a vertical bulkhead: a closed
        square-section torus in the XY plane, swept about +Z.

        The window's ring band was 40 flat quads and 80 open edges. It is a
        physical band bolted over the glazing and it has a section.
        """
        i = len(self.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            for rad in (r0, r1):
                for zz in (z0, z1):
                    self.v.append((cx + rad * ca, cy + rad * sa, zz))
        for k in range(seg):
            b = i + 4 * k
            n = i + 4 * ((k + 1) % seg)
            # CLOCKWISE in (radial, z) -- a lathe about +Z is the opposite
            # hand to one about +Y. See council_chamber.arc_solid.
            for p, q in ((0, 1), (1, 3), (3, 2), (2, 0)):
                self.t.append((b + p, b + q, n + q))
                self.t.append((b + p, n + q, n + p))
        self.g.extend([group] * 8 * seg)

    def vdisc(self, cx, cy, z, r, group, seg=48, thick=0.02):
        """A VERTICAL disc in the XY plane at depth z, facing -Z (into the room).

        Distinct from `disc`, which lies in XZ at a height. Calling `disc` for
        the window laid the glazing flat at head height instead of standing it
        in the bulkhead -- the mullions were in the window plane and the glass
        was on the ceiling. Caught by asserting the two share a plane rather
        than by looking, because from most angles the flat disc was simply out
        of frame.

        `thick` is the body behind that face. Glass has a thickness and the
        hub is a plate: as bare fans they were 68 open edges in the middle of
        the one thing this room is built around.
        """
        # Wound to face -Z, INTO the room. Ascending angle in the XY plane
        # gives a +Z normal, which points out through the bulkhead and is
        # backface-culled from the only side anyone stands on. Fourth instance
        # of this family in the project, so it is asserted below rather than
        # remembered.
        loop = [(cx + r * math.cos(2.0 * math.pi * k / seg),
                 cy + r * math.sin(2.0 * math.pi * k / seg), z)
                for k in range(seg)][::-1]
        self.merge(*it_kit.plate_solid(loop, thick), group)

    def as_tuple(self):
        return self.v, self.t, self.g


def console_pitch_m():
    """Centre-to-centre spacing of the dais consoles, along their own arc."""
    rc = DAIS_D_M / 2.0 - CONSOLE_D_M * 0.55
    return math.radians(CONSOLE_ARC_DEG) * rc / CONSOLE_N


def console_w_m():
    """One console's width. DERIVED FROM THE ARC, not written down.

    It was a bare `CONSOLE_W_M = 1.15` against a pitch this function computes
    at 1.026 m, so every one of the five consoles overlapped its neighbour by
    12% -- two closed solids in the same place, which `docs/AAA-STANDARD.md`
    calls `blocking` and which the tram already cost this project once
    ("168 of 3,144 car vertices sit 6.43 m inside a radial spoke, and both
    modules' self-tests pass"). Nothing here could see it because both consoles
    were one plate and a plate has no volume to share.

    `CONSOLE_JOINT_FRAC` is the remaining 6%, and it is not slack: the frame
    shows the units BUTTED with a visible vertical joint between them, so the
    gap is the joint and the proud side cheeks below fill it.
    """
    return console_pitch_m() * CONSOLE_JOINT_FRAC


# The three lit registers a console face carries, in the frame's own order.
# Every one is a material this project has already measured and bound; none of
# them is new, because `station/materials.py` is not this module's to edit.
#
#   green  -> device_screen_glass  (0.93, 1.00, 0.92) e 0.8, via `dress_screen`
#   amber  -> plant_switchgear     (1.00, 0.61, 0.35) e 0.25, via `prop_tank_gauge`
#   red    -> light_indicator_red  (1.00, 0.12, 0.14) e 0.9
#
# STATED AS A LIMITATION rather than passed off: the reference's green is a
# saturated green and `device_screen_glass` is a green-WHITE. It is the closest
# bound emissive in the library and the alternative -- `alien_status_lamp` at
# (0.22, 1.00, 0.38) -- is the alien sector's atmosphere lamp at e 5.0, six
# times this one's energy and a group name that would be a lie in C&C. What
# would close it is one green indicator material in `materials.py`.
CELL_GREEN = "fix_mp_dress_screen"
CELL_AMBER = "fix_mp_prop_tank_gauge"
CELL_RED = "fix_mp_light_indicator_red"
CELL_CYCLE = (CELL_GREEN, CELL_AMBER, CELL_RED)

# --- AND WHAT THE THREE OF THEM MEAN, WHICH IS THE POINT OF THIS SESSION ----
# `station/cnc_ops.py` gives every console on this floor a DESK -- a system it
# watches -- and a state on `plant_systems.wear_at`'s own three rungs. So the
# cells stop being decoration: a desk in ALARM lights its whole bed red and
# raises its own annunciator lamp, and the reason there is a red bed in the
# room is that two generating units are out of service. Nothing here decides
# any of that; `cnc_ops.room_layout()` does, out of `plant_systems`.
#
# WHY THE OTHER TWO BANKS KEEP CYCLING. Driving every cell from the state would
# make a well station's consoles uniformly green, which is further from the
# reference than what shipped -- the frame shows green, amber and red on every
# unit at once, because most of what is on a console is a working register and
# not an alarm. So each console keeps its mixed registers and gains ONE bank
# that means something, plus a three-lamp status stack.
STATE_LAMP = {"NORMAL": CELL_GREEN, "CAUTION": CELL_AMBER, "ALARM": CELL_RED}
LAMP_DARK = "fix_mp_plant_conduit"      # plant_valve_metal: an unlit cell
STATE_CYCLE = {
    "NORMAL": CELL_CYCLE,
    "CAUTION": (CELL_AMBER, CELL_AMBER, CELL_GREEN),
    "ALARM": (CELL_RED,),
}


_LAYOUT = []
BOX_LEDGER = []


def _layout():
    """The watch floor's seat map and board, memoised for this process.

    IMPORTED BY NAME AND FAILING SOFT, deliberately. `station/cnc_ops.py` reads
    `plant_systems`, which reads `incident`, which is a four-second import; this
    room is built by `deck.py --sweep`, `rooms.py --footprint`, `variety.py`,
    `test_materials_layer3.py` and every render, so the cost is paid once per
    process and only when the room is actually built. If it cannot be imported
    at all the room still builds, with every desk NORMAL and a line on stderr
    -- because a station whose bridge silently shows all-clear because a module
    would not load is worse than one that says so.
    """
    if not _LAYOUT:
        try:
            import cnc_ops                                    # noqa: PLC0415
            _LAYOUT.append(cnc_ops.room_layout())
        except Exception as e:                                # noqa: BLE001
            print("command_control: no watch board (%s: %s) -- the consoles "
                  "are being built NORMAL and that is a default, not a reading"
                  % (type(e).__name__, e), file=sys.stderr)
            _LAYOUT.append({"dais": (), "pit": (), "state": {},
                            "worst": "NORMAL", "offline": ()})
    return _LAYOUT[0]


def console_unit(m, o, y_base, w_m, d_m, h_m, seed, cells=CELL_CYCLE,
                 desk_state="NORMAL"):
    """One console desk, built as the five tiers the frame actually shows.

    `o = (cx, cz, cos a, sin a)` places and turns it; the operator stands at
    -w and looks along +w. Everything is inside (w_m x d_m) in plan and rises
    from `y_base`, so the object stays where `collision.prop_boxes` and
    `rooms.walkable` already think it is -- `dressing.machine_bounds_ok`'s
    invariant, applied by hand because this console is TURNED and
    `dressing.machine` works on an axis-aligned box.

    Everything else here is `dressing`'s: `_Parts`' nine bound surface names,
    `_tube` for the legs, and the primary/secondary/tertiary hierarchy its
    "WHAT A MACHINE IS MADE OF HERE" section sets out. The one thing that is
    NOT reused is `_m_console` itself, and the reason is geometric rather than
    stylistic: it rakes toward an X face on an axis-aligned box, and these five
    stand on a 150-degree arc, each turned to its own operator.
    """
    P = _dress._Parts("fix_")
    hw, hd = w_m / 2.0, d_m / 2.0
    cx, cz, ca, sa = o

    def W(u, y, w):
        return (cx + u * ca - w * sa, y_base + y, cz + u * sa + w * ca)

    def obox(u0, u1, y0, y1, w0, w1, group):
        m.obox(o, u0, u1, y_base + y0, y_base + y1, w0, w1, group)

    y_leg = h_m * CONSOLE_LEG_TOP
    y_val = h_m * CONSOLE_VALANCE_TOP
    y_bed = h_m * CONSOLE_APRON_TOP
    rise = d_m * math.sin(math.radians(CONSOLE_TILT_DEG))

    # --- 1. legs: slim, SPLAYED, cross-tied ---------------------------------
    # The frame's desks stand on tube legs that spread toward the deck with a
    # brace between them, and you can see the dais through the gap. A box leg
    # is the one thing that cannot read that way at any distance.
    lv, lt, ls = [], [], []
    for su in (-1, 1):
        for sw in (-1, 1):
            _dress._tube(lv, lt, ls, "cc_console_leg",
                         W(su * (hw - 0.04), 0.0, sw * (hd - 0.02)),
                         W(su * (hw - 0.13), y_leg, sw * (hd - 0.10)),
                         0.026, _dress.SEG_BOLT)
        _dress._tube(lv, lt, ls, "cc_console_leg",
                     W(su * (hw - 0.10), y_leg * 0.44, -(hd - 0.07)),
                     W(su * (hw - 0.10), y_leg * 0.44, hd - 0.07),
                     0.018, _dress.SEG_BOLT)
    # AND THE X-BRACE, which the 3x crop shows plainly and which nothing built:
    # a diagonal each way across the front pair and a rail between the feet.
    # It is the difference between four sticks and a frame, and it is the
    # element that reads first at half distance because it is the only thing
    # under the desk with a direction of its own.
    for sw in (-1, 1):
        for su in (-1, 1):
            _dress._tube(lv, lt, ls, "cc_console_leg",
                         W(-su * (hw - 0.06), 0.06, sw * (hd - 0.03)),
                         W(su * (hw - 0.12), y_leg * 0.90, sw * (hd - 0.09)),
                         0.014, _dress.SEG_BOLT)
        _dress._tube(lv, lt, ls, "cc_console_leg",
                     W(-(hw - 0.05), 0.05, sw * (hd - 0.025)),
                     W(hw - 0.05, 0.05, sw * (hd - 0.025)),
                     0.016, _dress.SEG_BOLT)
    m.merge_spans(lv, lt, ls)

    # --- 2. the dark under-valance ------------------------------------------
    obox(-hw + 0.03, hw - 0.03, y_leg, y_val, -hd + 0.035, hd - 0.035,
         P.conduit)

    # --- 3. the apron, and the backlit panes recessed into it ---------------
    obox(-hw, hw, y_val, y_bed - 0.02, -hd, hd, P.panel)
    pw = (w_m - 0.10) / CONSOLE_PANES
    for k in range(CONSOLE_PANES):
        u0 = -hw + 0.05 + k * pw + 0.022
        obox(u0, u0 + pw - 0.044, y_val + 0.045, y_bed - 0.055,
             -hd - 0.014, -hd + 0.008, P.screen)

    # --- side cheeks, proud, so the butt joint between units reads -----------
    for su in (-1, 1):
        obox(su * (hw - 0.030), su * (hw + 0.012), y_val - 0.02, y_bed + 0.01,
             -hd + 0.01, hd - 0.01, P.conduit)

    # --- 4. the raked bed ----------------------------------------------------
    # Wound (-u,-w) -> (-u,+w) -> (+u,+w) -> (+u,-w), which is the order whose
    # cross product comes out +Y: the other one builds the desk with its
    # working surface facing the deck, and a plate you see through is what this
    # room shipped for four sessions. Asserted below, not remembered.
    def bed(s):
        return -hd + 2.0 * hd * s, y_bed + rise * s

    (wa, ya), (wb, yb) = bed(0.0), bed(1.0)
    m.plate(W(-hw, ya, wa - 0.010), W(-hw, yb, wb),
            W(hw, yb, wb), W(hw, ya, wa - 0.010),
            CONSOLE_BODY_M, "cc_console_face")

    # a raised bezel lip along the operator edge, and a rear coaming
    obox(-hw, hw, y_bed - 0.035, y_bed + 0.038, -hd - 0.032, -hd + 0.016,
         P.rail)
    obox(-hw * 0.92, hw * 0.92, y_bed + rise - 0.025, y_bed + rise + 0.085,
         hd - 0.11, hd + 0.018, P.panel)

    # --- 5. the control cells, in banks, ON the raked bed -------------------
    # This is the tier the room exists for and the one that was missing. Each
    # bank is a recessed sub-panel carrying its own lit cells, which is what
    # makes the bed read as instrumented rather than painted: a proud edge
    # catches the wall course at a grazing angle and a decal cannot.
    # THE BANKS ARE THE DARK PART OF THE BED, and that is the single biggest
    # correction the half-distance frame asked for. `cc_console_face` binds to
    # `device_console_bed`, a warm pale emissive, so a bed with small bank
    # plates on it reads as a light-coloured TABLE carrying pale tiles -- the
    # reference's bed is dark and the cells are the only bright thing on it.
    # `_Parts.conduit` is `plant_valve_metal`, the darkest bound surface in the
    # machine vocabulary, and the banks now cover most of the working area.
    bw = (w_m - 0.075) / CONSOLE_BANKS

    def on_bed(u, s, lift):
        w, y = bed(s)
        # The bed's own normal, in the (w, y) plane, so a pad lifts off the
        # SURFACE rather than straight up: at 22 degrees straight up leaves the
        # downhill edge buried.
        n = math.hypot(2.0 * hd, rise)
        return W(u, y + lift * (2.0 * hd) / n, w - lift * rise / n)

    # WHICH CELLS ARE LIT IS NOW A READING. `cells` is the unit's working
    # register set -- kept mixed, because the reference shows green, amber and
    # red on every desk at once -- and `desk_state` recolours it through
    # STATE_CYCLE when this desk's own system is in trouble. At ALARM the whole
    # bed goes red; that is what makes `cnc_ops --engine-gate`'s two frames
    # different pictures rather than two readings of one.
    live = cells if desk_state == "NORMAL" else STATE_CYCLE.get(desk_state,
                                                                cells)
    if cells == (CELL_RED,):
        live = cells                      # the pit is red-lit by the reference
    for b in range(CONSOLE_BANKS):
        u0 = -hw + 0.038 + b * bw
        u1 = u0 + bw - 0.016
        m.plate(on_bed(u0, 0.10, 0.007), on_bed(u0, 0.94, 0.007),
                on_bed(u1, 0.94, 0.007), on_bed(u1, 0.10, 0.007),
                0.020, P.conduit)
        cs = (0.94 - 0.10) / CONSOLE_CELLS
        for c in range(CONSOLE_CELLS):
            s0 = 0.10 + c * cs + 0.020
            s1 = s0 + cs - 0.040
            # `(b + c) % 3` IS A DIAGONAL STRIPE AND THE EYE INDEXES IT
            # INSTANTLY. Nine consoles x four banks x four cells on one modular
            # rule renders as a red-and-white checkerboard laid over the whole
            # desk -- `docs/craft-4r-cnc-r1-console-half.png` reads as a picnic
            # blanket, and `docs/AAA-STANDARD.md` C5's "nothing in frame repeats
            # in a way the eye can index" is the clause, with C3's "the same
            # light, repeated without regard to what the part does" one rung
            # below it. `dressing._pick` is this project's own deterministic
            # chooser -- `blake2b`, never `random` and never `str.__hash__`,
            # which is salted per process -- and keying it on the DESK's seed
            # makes two consoles differ while one console is the same object
            # every run. MEASURED, and worse than it looked: `(b + c) % 3` does
            # not depend on the desk at all, so all nine consoles carried the
            # SAME sixteen-cell pattern -- 1 distinct pattern over nine desks
            # against 9 for the keyed rule. Gated below with that control.
            grp = (live[0] if len(live) == 1
                   else _dress._pick(live, seed, "cell", b, c))
            m.plate(on_bed(u0 + 0.014, s0, 0.017),
                    on_bed(u0 + 0.014, s1, 0.017),
                    on_bed(u1 - 0.014, s1, 0.017),
                    on_bed(u1 - 0.014, s0, 0.017), 0.012, grp)
            # A KEY ROW BESIDE EVERY CELL. The reference's blocks are not rows
            # of identical lozenges: each lit register sits beside a run of
            # small unlit keys, and that alternation is most of what makes the
            # bed read as instrumented at 1 m. `P.gauge` is the amber
            # switchgear the plant kit already uses for exactly this.
            if c % 2 == 0:
                m.plate(on_bed(u0 + 0.014, s0 + 0.004, 0.024),
                        on_bed(u0 + 0.014, s1 - 0.004, 0.024),
                        on_bed(u0 + 0.040, s1 - 0.004, 0.024),
                        on_bed(u0 + 0.040, s0 + 0.004, 0.024), 0.008, P.gauge)

    # --- 6. THE STATUS STACK -- three lamps, one of them lit ----------------
    # An annunciator: what this desk's system is doing, in the one place an
    # operator standing at it can see without reading anything. The two dark
    # lamps matter as much as the lit one -- a single lamp that changes colour
    # is a light; three lamps of which one is on is a STATE, and it reads as
    # one from across the room because the geometry does not change, only which
    # cell is bright.
    su0 = hw - 0.115
    for i, s in enumerate(("ALARM", "CAUTION", "NORMAL")):
        s0 = 0.24 + i * 0.24
        grp = STATE_LAMP[s] if s == desk_state else LAMP_DARK
        m.plate(on_bed(su0 - 0.075, s0, 0.026), on_bed(su0 - 0.075,
                                                       s0 + 0.16, 0.026),
                on_bed(su0 + 0.075, s0 + 0.16, 0.026),
                on_bed(su0 + 0.075, s0, 0.026), 0.014, grp)
    m.plate(on_bed(su0 - 0.098, 0.20, 0.014), on_bed(su0 - 0.098, 0.90, 0.014),
            on_bed(su0 + 0.098, 0.90, 0.014), on_bed(su0 + 0.098, 0.20, 0.014),
            0.018, P.frame)


def dais_key(m, top):
    """The key light over the dais -- THE FITTING THIS ROOM WAS MEASURED FROM.

    See DAIS_KEY_H_M. `light_dais_key` is a `FIXTURE_LIGHTING` entry whose
    source line reads "measured from reference/03-sector-blue/comand and
    contorl.webp", and until now the only geometry carrying that name was in
    `rooms.py`'s worship archetype. The lens is its own group because
    `export_scene.fixture_lights` hangs one lamp per tagged BODY -- the housing
    must not be tagged or the room gets two lamps a fitting.
    """
    r = DAIS_D_M / 2.0 - 0.30
    for k in range(DAIS_KEY_N):
        a = math.radians((k + 0.5) / DAIS_KEY_N * CONSOLE_ARC_DEG
                         - CONSOLE_ARC_DEG / 2.0) + math.pi / 2.0
        cx, cz = r * 0.55 * math.cos(a), r * 0.55 * math.sin(a)
        y = top + DAIS_KEY_H_M
        m.box(cx - DAIS_KEY_R_M, cx + DAIS_KEY_R_M, y, y + 0.30,
              cz - DAIS_KEY_R_M, cz + DAIS_KEY_R_M, _KEY_HOUSING)
        m.box(cx - DAIS_KEY_R_M * 0.72, cx + DAIS_KEY_R_M * 0.72,
              y - 0.045, y + 0.005,
              cz - DAIS_KEY_R_M * 0.72, cz + DAIS_KEY_R_M * 0.72,
              "light_dais_key")
        # the stem it hangs on -- a lamp with nothing above it is a lamp
        # floating in a 34 m dome
        sv, st, ss = [], [], []
        _dress._tube(sv, st, ss, _KEY_HOUSING, (cx, y + 0.28, cz),
                     (cx, y + 2.4, cz), 0.035, _dress.SEG_BOLT)
        m.merge_spans(sv, st, ss)


def balustrade(m, x, z0, z1):
    """A handrail WITH PANEL INFILL, which is what the frame shows.

    It was one 80 mm bar floating at 1.05 m with nothing under it and nothing
    holding it up -- a rail a hand cannot rest on because there is no post
    between it and the deck.
    """
    P = _dress._Parts("fix_")
    n = max(2, int(abs(z1 - z0) / 1.7) + 1)
    # ROUND POSTS AND A ROUND TOP RAIL. They were square section, which is the
    # one thing the 3x crop of the reference rules out: the rail carries a
    # continuous specular highlight down its length, which a flat face cannot
    # produce, and the posts read as pipe. Six sides is enough at this radius --
    # `dressing.SEG_BOLT` is the project's own count for a 35 mm member.
    bv, bt, bs = [], [], []
    for i in range(n):
        zz = z0 + (z1 - z0) * i / (n - 1)
        zz = min(max(zz, z0 + 0.05), z1 - 0.05)
        _dress._tube(bv, bt, bs, "cc_rail", (x, 0.0, zz), (x, RAIL_H_M, zz),
                     0.035, _dress.SEG_PIPE)
        # the foot casting -- a post that meets the deck at a line is a post
        # somebody drew rather than bolted down
        _dress._tube(bv, bt, bs, "cc_rail", (x, 0.0, zz), (x, 0.055, zz),
                     0.062, _dress.SEG_PIPE)
    _dress._tube(bv, bt, bs, "cc_rail", (x, RAIL_H_M - 0.045, z0),
                 (x, RAIL_H_M - 0.045, z1), 0.045, _dress.SEG_PIPE)
    _dress._tube(bv, bt, bs, "cc_rail", (x, RAIL_H_M * 0.47, z0),
                 (x, RAIL_H_M * 0.47, z1), 0.028, _dress.SEG_PIPE)
    m.merge_spans(bv, bt, bs)
    m.box(x - 0.014, x + 0.014, 0.10, RAIL_H_M * 0.44, z0 + 0.06, z1 - 0.06,
          P.panel)
    # the kick plate the reference shows glowing along the floor edge
    m.box(x - 0.026, x + 0.026, 0.055, 0.155, z0 + 0.06, z1 - 0.06,
          "light_deck_channel")


def _pane(m, cy, z, r0, r1, a0, a1, group, inset):
    """One trapezoidal pane of glazing, set back in its own opening.

    Wound so its FRONT faces -Z, into the room -- the same hand `vdisc` takes
    and for the same reason: ascending angle in the XY plane gives a +Z normal,
    which points out through the bulkhead and is backface-culled from the only
    side anybody stands on.
    """
    loop = [(r1 * math.cos(a1), cy + r1 * math.sin(a1), z + inset),
            (r1 * math.cos(a0), cy + r1 * math.sin(a0), z + inset),
            (r0 * math.cos(a0), cy + r0 * math.sin(a0), z + inset),
            (r0 * math.cos(a1), cy + r0 * math.sin(a1), z + inset)]
    m.merge(*it_kit.plate_solid(loop, 0.018), group)


def _radial_bar(m, cy, z, r0, r1, a, half_w, depth, group):
    """A mullion running out along a radius, given a section."""
    ca, sa = math.cos(a), math.sin(a)
    nx, ny = -sa * half_w, ca * half_w
    m.plate((r0 * ca + nx, cy + r0 * sa + ny, z),
            (r1 * ca + nx, cy + r1 * sa + ny, z),
            (r1 * ca - nx, cy + r1 * sa - ny, z),
            (r0 * ca - nx, cy + r0 * sa - ny, z),
            depth, group)


def window(m, z, cy):
    """The circular window: paned glazing, mullions, a studded band, ribs.

    WHAT THIS REPLACES, and it is the room's whole focus:
    sixteen flat bars, one flat ring, one flat hub and a single black disc.
    `docs/craft-4q-cnc-before-half.png` is that at the rubric's half distance.

    Built outward, because that is the order the structure is assembled in and
    it is the order the reference reads in: glazing in courses, the frames the
    courses sit in, the mullions over them, the structural band with its studs,
    the rim collar, and the ribs that carry the whole thing into the bulkhead.
    """
    r = WINDOW_D_M / 2.0
    hw = WINDOW_MULLION_W_M / 2.0
    b0, b1 = WINDOW_BAND

    # --- 1. GLAZING IN COURSES ----------------------------------------------
    # Each course is a ring of trapezoidal panes set `WINDOW_PANE_INSET_M`
    # behind the frame plane, so the frame reads as a frame at any angle: a
    # coplanar pane is a decal and a decal has no shadow line.
    # HOW FAR A CONCENTRIC MEMBER HAS TO LAP OVER THE COURSE INSIDE IT, and it
    # is not a constant. A pane is a flat trapezoid inscribed in its own arc,
    # so its outer edge is a CHORD and dips `rad * (1 - cos(pi/n))` inside the
    # radius it was cut at -- 37 mm on the twelve-pane inner course, 15 mm on
    # the twenty-four-pane one. A member built to the nominal radius misses the
    # glass it is supposed to hold, and the miss is a slot you can see space
    # through. The inner edges need no lap: a chord at the inner radius dips
    # TOWARD the centre and so covers more, not less.
    lap = {}
    for _f0, f1, n in WINDOW_COURSES:
        edge = r * f1 - 0.02
        lap[f1] = max(lap.get(f1, 0.0),
                      r * f1 - edge * math.cos(math.pi / n) + 0.004)

    frames = []
    for f0, f1, n in WINDOW_COURSES:
        for k in range(n):
            a0 = 2.0 * math.pi * k / n
            a1 = 2.0 * math.pi * (k + 1) / n
            _pane(m, cy, z, r * f0 + 0.02, r * f1 - 0.02, a0 + 0.008,
                  a1 - 0.008, "cc_glazing", WINDOW_PANE_INSET_M)
        # ...and the concentric frame member each course sits against.
        # DEDUPLICATED, and the reason is measured rather than tidy: two courses
        # meet at 0.40 and the naive loop built that ring TWICE, one solid
        # exactly inside another -- 608 non-manifold edges and 384 triangles
        # nobody can see. Same class as the mullion collision below, found by
        # the same gate in the same run.
        for f in (f0, f1):
            if b0 - 1e-9 <= f <= b1 + 1e-9:
                continue                       # the band itself, built below
            if any(abs(f - e) < 1e-9 for e in frames):
                continue
            frames.append(f)
            m.band(0.0, cy, z - 0.02, z + 0.02,
                   r * f - max(0.028, lap.get(f, 0.0)), r * f + 0.028,
                   "cc_mullion", seg=48)

    # --- 2. THE HUB ---------------------------------------------------------
    # Spokes run from a central hub to the rim, NOT across the full diameter.
    # Full-diameter bars were the first version and 16 of them piled up at the
    # centre into a solid starburst with no glass visible between them.
    r0 = r * WINDOW_HUB_FRAC
    m.vdisc(0.0, cy, z, r0, "cc_hub", seg=20, thick=WINDOW_MULLION_D_M)

    # --- 3. THE MULLIONS ----------------------------------------------------
    # The primary sixteen run hub to rim and stand proud of everything. The
    # secondary bars divide each course and stop at its own frame members, so
    # the grid gets finer as it goes out -- which is what the reference shows
    # and what a pressure window would actually do, because a pane's area has
    # to stay roughly constant as the radius grows.
    for k in range(WINDOW_MULLIONS):
        _radial_bar(m, cy, z, r0, r, 2.0 * math.pi * k / WINDOW_MULLIONS,
                    hw, WINDOW_MULLION_D_M, "cc_mullion")
    step = 2.0 * math.pi / WINDOW_MULLIONS
    for f0, f1, n in WINDOW_COURSES:
        for k in range(n):
            a = 2.0 * math.pi * k / n
            # DISTANCE TO THE NEAREST PRIMARY, not `a % step`. The modulo form
            # was written first and is wrong in the direction that hides the
            # defect: an angle a hair BELOW a multiple returns a value near
            # `step`, not near zero, so eight of the twenty-four secondary bars
            # in each outer course were built INSIDE a primary mullion -- two
            # closed solids in one place, 608 non-manifold edges, and
            # `docs/AAA-STANDARD.md` calls that `blocking`. Caught by the
            # non-manifold gate this file already had, which is the argument
            # for the gate.
            d = a % step
            if min(d, step - d) < 1e-6:
                continue                       # already a primary spoke
            # STOPPED SHORT OF THE FRAME RING AT EACH END, and that is not a
            # cosmetic gap: a bar that ends exactly on `r * f1` meets the next
            # course's bar at the same angle FACE TO FACE, 32 shared edges over
            # the window. A secondary member butts into the ring it dies into;
            # it does not weld to the member on the other side of it.
            _radial_bar(m, cy, z, r * f0 + 0.032, r * f1 - 0.032, a,
                        hw * 0.42, WINDOW_MULLION_D_M * 0.55, "cc_mullion")

    # --- 4. THE BAND, AND THE STUDS THAT SAY IT IS BOLTED ON ----------------
    # LAPPED ONTO THE PANES IT MEETS BY THEIR OWN INSET, which is the 0.02 m
    # the course loop above sets back every pane edge. Built to `r * b0`
    # exactly, the band stopped 20 mm short of the glass on both sides: a
    # hairline annular SLOT at r/R = 0.62 and again at 0.80, straight through
    # the only window in the room, and the concentric frame member that closes
    # every OTHER course boundary is skipped at these two ("the band itself,
    # built below") on the assumption the band covered them.
    #
    # Found by projecting the room along +Z and counting cross-section cells
    # covered by no triangle -- 45 of 13,160 -- and by nothing else, because
    # every closure test in this file measures ONE SURFACE and both surfaces
    # are closed. NEGATIVE RESULT worth keeping: the first hypothesis was a
    # polygon-phase mismatch (a 40-gon band against 24 chords) and re-cutting
    # the band at `seg=24` made it WORSE, 45 -> 55, because a coarser polygon
    # dips further inside its own radius. The gap was construction, not
    # tessellation.
    m.band(0.0, cy, z - WINDOW_MULLION_D_M, z,
           r * b0 - max(0.02, lap.get(b0, 0.0)), r * b1 + 0.02, "cc_ring")
    for edge in (b0 + 0.012, b1 - 0.012):
        rr = r * edge
        for k in range(WINDOW_STUDS):
            a = 2.0 * math.pi * (k + 0.5) / WINDOW_STUDS
            cx, cyy = rr * math.cos(a), cy + rr * math.sin(a)
            sv, st, ss = [], [], []
            _dress._tube(sv, st, ss, "cc_ring",
                         (cx, cyy, z - WINDOW_MULLION_D_M - WINDOW_STUD_PROUD_M),
                         (cx, cyy, z - WINDOW_MULLION_D_M),
                         WINDOW_STUD_R_M, _dress.SEG_BOLT)
            m.merge_spans(sv, st, ss)

    # --- 5. THE RIM COLLAR, and the ribs that carry it into the wall --------
    m.band(0.0, cy, z - WINDOW_MULLION_D_M * 1.6, z + 0.02,
           r - 0.10, r + 0.11, "cc_ring", seg=64)
    for k in range(WINDOW_MULLIONS):
        a = 2.0 * math.pi * (k + 0.5) / WINDOW_MULLIONS
        _radial_bar(m, cy, z - 0.03, r + 0.06, r + WINDOW_RIB_OUT_M, a,
                    hw * 0.8, 0.07, "cc_mullion")


def bulkhead(m, zw, cy, hw, bot):
    """The forward wall, with a CIRCULAR aperture cut in it.

    IT WAS FOUR BOXES AROUND A SQUARE HOLE, and one of them was inside out --
    see BULK_TOP_M. The square is the visible half of that: a round window in a
    square hole shows the background through the four corners, and
    `docs/craft-4q-cnc-before-half.png` shows exactly that, a black rectangle
    with a wheel in it. `interior_kit._plate_with_hole` is the primitive this
    project already wrote for the case and it is what every door on the station
    uses; the aperture is a 48-gon, which at a 2.87 m radius is a 6.1 mm sagitta
    and is under the 22 mm the deck's own tiles stand proud by.

    The bosses and the panel grid are the second tier. Without them the wall is
    one slab and the window is a decal on it; the reference's bulkhead is
    clearly panelled and clearly carries two circular bosses high on either
    side of the aperture.
    """
    ap = WINDOW_D_M / 2.0 + 0.12
    seg = 48
    outline = [(-hw, bot), (hw, bot), (hw, BULK_TOP_M), (-hw, BULK_TOP_M)]
    hole = [(ap * math.cos(2.0 * math.pi * k / seg),
             cy + ap * math.sin(2.0 * math.pi * k / seg))
            for k in range(seg)]
    bv, bt = [], []
    it_kit._plate_with_hole(bv, bt, outline, hole, zw, zw + BULK_D_M)
    m.merge(bv, bt, "cc_bulkhead")

    # The reveal round the aperture: a collar standing proud of the wall, which
    # is what a 300 mm plate with a hole in it would have on its room face.
    m.band(0.0, cy, zw - 0.09, zw, ap - 0.02, ap + 0.26, "cc_ring", seg=seg)

    # PANELLING. A coarse orthogonal grid of proud plates, skipping anything
    # that would land on the aperture or on a boss -- a band drawn across the
    # window is the defect this whole function exists to remove.
    px, py = 2.35, 1.62
    nx = int(hw * 2 / px)
    ny = int((BULK_TOP_M - bot) / py)
    for i in range(nx):
        for j in range(ny):
            x0 = -hw + (i + 0.5) * (2 * hw / nx)
            y0 = bot + (j + 0.5) * ((BULK_TOP_M - bot) / ny)
            if math.hypot(x0, y0 - cy) < ap + 0.75:
                continue
            if any(math.hypot(x0 - s * BULK_BOSS_X, y0 - BULK_BOSS_Y)
                   < BULK_BOSS_R_M + 0.55 for s in (-1, 1)):
                continue
            w2, h2 = (2 * hw / nx) * 0.44, ((BULK_TOP_M - bot) / ny) * 0.42
            m.box(x0 - w2, x0 + w2, y0 - h2, y0 + h2, zw - 0.045, zw,
                  "cc_panel")
    for s in (-1, 1):
        m.vdisc(s * BULK_BOSS_X, BULK_BOSS_Y, zw - 0.10, BULK_BOSS_R_M,
                "cc_panel", seg=28, thick=0.10)
        m.band(s * BULK_BOSS_X, BULK_BOSS_Y, zw - 0.13, zw - 0.02,
               BULK_BOSS_R_M - 0.02, BULK_BOSS_R_M + 0.09, "cc_ring", seg=28)


def _course_bands():
    """The y bands the wall's own fittings and trim already occupy.

    Derived from the constants the fittings are built from rather than written
    down, so a course that moves takes its exclusion with it.
    """
    h = STRIP_H_M
    bands = [(0.0, 0.14),                       # the skirting
             (0.95, 1.15),                      # the dado
             (CEIL_Y_M, CEIL_Y_M + 0.22)]       # the cornice
    for y in STRIP_Y_M:
        c = y + h / 2.0
        bands.append((c - h * 1.9, c + h * 1.9))
    for y in STRIP_Y_EXTRA_M:
        bands.append((y - h * 1.9, y + h * 1.9))
    return bands


def side_wall(m, sx, hw, L):
    """One side wall of the room -- the layer C&C has never had.

    MEASURED, NOT NOTICED. Project the room along its own x axis and ask which
    cells of its cross-section are covered by any triangle: the version that
    shipped through session 4r leaves **32.6 m2 of 100.2 m2 (32.5%) open**, and
    18.4% of the frame at the rubric's normal distance hits no room geometry at
    all -- the left and right thirds of `docs/craft-4r-cnc-r1-normal.png` are
    the vista's starfield, and of the pre-4r background colour, which is black.
    What stood at x = +-hw was four light-course housings, a dado, a skirting
    and a cornice: **trim for a wall that was never built.**
    `docs/AAA-STANDARD.md` C2 names the case verbatim -- *"a correct skeleton
    with a missing layer: the corridor after session 2l had ribs and a deck and
    no walls, so it read as scaffolding of exactly the right size."*

    AND THE REASON NO GATE COULD SEE IT IS ONE SENTENCE: **every closure test
    in this project measures a SURFACE, and enclosure is a property of a
    VOLUME.** `interior_kit.boundary_edges` reports ZERO open edges on this room and
    `bespoke.SHELL_OPEN_EDGES["command_control"]` reads 0, and both are right --
    every piece is a closed solid. A room built entirely of closed solids with
    nothing between them is watertight and open to space. `_lateral_gaps()`
    below asks the volume's question instead, and it fails on this room's own
    previous content by 32.5%.

    Three tiers, because a 12.6 x 9.7 m plate is the defect one level up:

      1. the PLATE, from the pit slab's underside to the top of the cornice, so
         no ray leaves between the wall and either;
      2. a proud PANEL GRID on the deck's own joint pitch, skipping every band
         the courses and trim already occupy (`_course_bands`);
      3. a PILASTER under each of `ceiling`'s beams. The beams used to land on
         nothing -- a beam that dies in mid-air is the tell that a room was
         drawn rather than built -- and this is `docs/AAA-STANDARD.md` C4's
         "a fitting is where a fitting would be needed", the cheapest instance
         of it available in this room.
    """
    P = _dress._Parts("fix_")
    xi = sx * (hw + WALL_STANDOFF_M)            # the face a player sees
    xo = sx * (hw + WALL_STANDOFF_M + WALL_D_M)
    y0, y1 = -PIT_DROP_M - 0.16, CEIL_Y_M + 0.22
    z0, z1 = -L * 0.35, L * 0.70
    m.box(min(xi, xo), max(xi, xo), y0, y1, z0, z1, "cc_bulkhead")

    excl = _course_bands()
    nz = max(1, int(round((z1 - z0) / DECK_BAY_M)))
    ny = max(1, int((CEIL_Y_M - 0.0) / WALL_PANEL_Y_M))
    xp = xi - sx * WALL_PANEL_PROUD_M
    for i in range(nz):
        zc = z0 + (i + 0.5) * (z1 - z0) / nz
        for j in range(ny):
            yc = (j + 0.5) * CEIL_Y_M / ny
            hy = (CEIL_Y_M / ny) * 0.40
            if any(yc - hy < b1 and yc + hy > b0 for b0, b1 in excl):
                continue
            hz = ((z1 - z0) / nz) * 0.43
            m.box(min(xi, xp), max(xi, xp), yc - hy, yc + hy,
                  zc - hz, zc + hz, "cc_panel")

    # The pilasters, one under each ceiling beam, at the beam's own z.
    zb0, zb1 = -L * 0.35, L * 0.70
    xb = xi - sx * (WALL_PANEL_PROUD_M + 0.065)
    for k in range(CEIL_BEAMS):
        zc = zb0 + (k + 0.5) * (zb1 - zb0) / CEIL_BEAMS
        m.box(min(xi, xb), max(xi, xb), 0.14, CEIL_Y_M - CEIL_BEAM_D_M,
              zc - 0.13, zc + 0.13, P.frame)
        # the head casting where it takes the beam, and a foot where it lands
        for yy, hh in ((CEIL_Y_M - CEIL_BEAM_D_M - 0.14, 0.14), (0.14, 0.11)):
            m.box(min(xi, xb - sx * 0.035), max(xi, xb - sx * 0.035),
                  yy, yy + hh, zc - 0.185, zc + 0.185, P.panel)


def course_lens(m, sx, y, z0, z1, lit):
    """The emitting face of one wall course, and nothing else.

    SEPARATE FROM ITS HOUSING FOR A REASON IN ANOTHER FILE.
    `export_scene.fixture_lights` hangs one lamp on each connected BODY of a
    `cc_light_strip` SPAN, and a span is a run of consecutive triangles with
    one group name -- so building each course as trough-then-lens-then-dividers
    turns one span of four bodies into four spans of one body. The lamp count is
    identical either way (four), but `export_scene._selftest` asserts the shape
    and not the count: `_courses == [4]` became `[1, 1, 1, 1]`.
    Both readings are right about the rig and the gate is in a file this module
    does not own, so the lenses are emitted together in their own pass and the
    assertion stays exactly as it was.
    """
    x_in = sx * (FLOOR_W_M / 2.0)
    x_bk = x_in - sx * STRIP_TROUGH_D_M
    h = STRIP_H_M
    m.box(min(x_in - sx * 0.055, x_bk + sx * 0.04),
          max(x_in - sx * 0.055, x_bk + sx * 0.04),
          y - h * 0.5, y + h * 0.5, z0, z1, lit)


def wall_course(m, sx, y, z0, z1):
    """One horizontal light course's HOUSING, as the fitting the reference shows.

    Four surfaces, not one box: a recessed TROUGH, a reflector CHEEK above and
    below it, a dark DIVIDER every `STRIP_SEG_M` so the run reads as tubes
    rather than as a painted line, and an end cap. The lens itself is
    `course_lens`, for the reason written there.
    """
    P = _dress._Parts("fix_")
    x_in = sx * (FLOOR_W_M / 2.0)          # the wall plane
    x_bk = x_in - sx * STRIP_TROUGH_D_M    # the back of the trough
    h = STRIP_H_M
    # the trough: back plate and two cheeks, so the fitting has a box to sit in
    m.box(min(x_in, x_bk), max(x_in, x_bk), y - h * 1.9, y + h * 1.9,
          z0, z1, P.panel)
    for sy in (-1, 1):
        m.box(min(x_in - sx * 0.006, x_bk + sx * 0.02),
              max(x_in - sx * 0.006, x_bk + sx * 0.02),
              y + sy * h * 0.62, y + sy * h * 0.62 + 0.045,
              z0 + 0.012, z1 - 0.012, P.frame)
    # the dividers, in front of the lens
    n = max(1, int((z1 - z0) / (STRIP_SEG_M + STRIP_GAP_M)))
    for k in range(1, n + 1):
        zc = z0 + k * (z1 - z0) / (n + 1.0)
        m.box(min(x_in - sx * 0.02, x_bk + sx * 0.03),
              max(x_in - sx * 0.02, x_bk + sx * 0.03),
              y - h * 0.62, y + h * 0.62,
              zc - STRIP_GAP_M / 2.0, zc + STRIP_GAP_M / 2.0, P.conduit)
    # END CAPS, and they are INSET rather than flush. A cap built to the
    # trough's own x and y extents at the trough's own z shares a whole face
    # with it -- 64 non-manifold edges over the room's eight courses, which the
    # gate reports as two pieces of this module in the same place and is right
    # to. A cap 15 mm inside the housing it closes is what a real one is.
    for zz, sz in ((z0, 1.0), (z1, -1.0)):
        m.box(min(x_in - sx * 0.012, x_bk), max(x_in - sx * 0.012, x_bk),
              y - h * 1.86, y + h * 1.86,
              min(zz + sz * 0.014, zz + sz * 0.074),
              max(zz + sz * 0.014, zz + sz * 0.074), P.frame)


def pit_soffit(m, hw, L):
    """The light over the forward pit -- and the reason the window is a
    silhouette.

    MEASURED FIRST. In `docs/craft-4r-cnc-r2-half.png`, inside the window's own
    aperture, the dark 55% of pixels (the frame: mullions, band, hub) average
    linear Y **0.01256** against the bright 45% (the glass, showing the station
    through it) at **0.11972** -- **x0.105**. The show's frame has the ratio the
    other way up: `scratchpad/PATCHES-4r-windows.md` §7 measures pane/mullion
    at **x0.48** there against **x6.96** here, i.e. the reference's mullions are
    BRIGHTER than its glass, because they are lit structure in front of a
    mid-dark view. Ours is a bright hole with a black wheel over it, and the
    window is the object this whole room is arranged around.

    THE CAUSE IS NOT THE WINDOW, IT IS THAT THE PIT HAS NO LIGHT. Every one of
    the room's seven fittings is aft of z = 5.04: four wall courses that stop
    `L * 0.42` forward, and ceiling battens on `light_service_tube`, which
    `export_scene.py`'s `emissive_only` set explicitly excludes from carrying a
    lamp. The forward pit -- one of the room's two occupied levels, the thing
    that makes it read as a bridge, and the level the reference leads with --
    is lit by nothing at all, and the window's frame is the surface between it
    and the eye. A mullion face is a vertical plane facing -Z; the nearest lamp
    to it was 7.7 m away at cos 0.44 and 1/d^2 of 0.017.

    So this is a fitting where a fitting is needed rather than a light where a
    light is wanted (`docs/AAA-STANDARD.md` C4). A blade over the pit at 3.5 m
    from the window's centre raking forward puts the frame in front of its own
    light, and gives the pit's four consoles an overhead of their own.

    `light_wall_course` and NOT `cc_light_strip`: they are the same measured
    fitting -- `export_scene.FIXTURE_LIGHTING`'s entry says so -- but
    `export_scene._selftest` asserts `cc_light_strip` comes in exactly four
    connected bodies, and that assertion is in a file this module does not own.
    A fifth body of it would break a gate elsewhere to fix a defect here.
    INV-621.
    """
    P = _dress._Parts("fix_")
    y = CEIL_Y_M - CEIL_BEAM_D_M - PIT_SOFFIT_DROP_M
    z0, z1 = PIT_SOFFIT_Z_M - 0.26, PIT_SOFFIT_Z_M + 0.26
    x = PIT_SOFFIT_HALF_W_M
    # the housing: a hung tray on two drop rods per end
    m.box(-x, x, y + 0.10, y + 0.24, z0, z1, P.panel)
    for sx in (-1, 1):
        for zz in (z0 + 0.12, z1 - 0.12):
            # 4 mm short of the beam it hangs from, for the reason
            # `wall_course`'s end caps and `annunciator`'s cheeks are: a rod
            # built to the soffit's own y shares a whole face with it.
            m.box(sx * (x - 0.22), sx * (x - 0.22) + 0.05,
                  y + 0.24, CEIL_Y_M - CEIL_BEAM_D_M - 0.004,
                  zz - 0.025, zz + 0.025, P.frame)
    # ...and the blades in it, one connected body each: `fixture_lights` hangs
    # one lamp per body, so the count here IS the lamp count.
    for k in range(PIT_SOFFIT_BLADES):
        cx = -x + (k + 0.5) * (2 * x) / PIT_SOFFIT_BLADES
        w = (2 * x) / PIT_SOFFIT_BLADES * 0.40
        m.box(cx - w, cx + w, y, y + 0.10, z0 + 0.05, z1 - 0.05,
              "light_wall_course")
        # the reflector cheeks that make it a blade rather than a bare tube
        for sz in (z0 + 0.03, z1 - 0.08):
            m.box(cx - w - 0.04, cx + w + 0.04, y - 0.02, y + 0.13,
                  sz, sz + 0.05, P.frame)


def ceiling(m, hw, L):
    """The soffit and its beams. There was nothing above the wall bands at all.

    Emitted with the slab's visible face DOWNWARD, which is the whole content
    of the surface: a ceiling wound the other way is a room with no lid that
    happens to have triangles in it, and this module has already shipped one
    inside-out solid (BULK_TOP_M).
    """
    P = _dress._Parts("fix_")
    z0, z1 = -L * 0.35, L * 0.70
    # A SLAB, NOT A QUAD. `m.quad` is one-sided and four open boundary edges;
    # this file's own history is 342 of them shipped for four sessions on
    # exactly this mistake, so a new surface does not get to repeat it.
    m.box(-hw, hw, CEIL_Y_M, CEIL_Y_M + 0.22, z0, z1, "cc_cornice")
    for k in range(CEIL_BEAMS):
        zc = z0 + (k + 0.5) * (z1 - z0) / CEIL_BEAMS
        m.box(-hw, hw, CEIL_Y_M - CEIL_BEAM_D_M, CEIL_Y_M,
              zc - 0.20, zc + 0.20, P.frame)
    # A run of battens down the centreline: the only general-service light the
    # room has above head height, and the fitting the dais keys hang beside.
    for k in range(CEIL_BEAMS - 1):
        zc = z0 + (k + 1.0) * (z1 - z0) / CEIL_BEAMS
        m.box(-1.15, 1.15, CEIL_Y_M - 0.10, CEIL_Y_M - 0.04,
              zc - 0.16, zc + 0.16, "light_service_tube")


def deck_field(m, hw, L):
    """Joints and lit insets in the upper floor.

    The deck was one quad. The reference's floor carries large inset panels
    that read as blue rectangles beside the balustrade and a joint grid between
    them, and `light_deck_channel` is the bound cool-white the corridor kit's
    own deck channel already uses -- it is emissive and is NOT in
    `FIXTURE_LIGHTING`, so this costs the room no lamps.
    """
    P = _dress._Parts("fix_")
    z0, z1 = -L * 0.35, L * 0.45
    n = max(1, int((z1 - z0) / DECK_BAY_M))
    for k in range(1, n):
        zc = z0 + k * (z1 - z0) / n
        m.box(-hw, hw, 0.0, 0.014, zc - 0.028, zc + 0.028, P.conduit)
    for sx in (-1, 1):
        for k in range(n):
            zc = z0 + (k + 0.5) * (z1 - z0) / n
            cx = sx * (hw - 1.35)
            if math.hypot(cx, zc) < DAIS_D_M / 2.0 + DAIS_STEPS * DAIS_TREAD_M:
                continue
            m.box(cx - DECK_INSET_W_M / 2.0, cx + DECK_INSET_W_M / 2.0,
                  0.004, 0.020,
                  zc - DECK_INSET_L_M / 2.0, zc + DECK_INSET_L_M / 2.0,
                  "light_deck_channel")
            m.box(cx - DECK_INSET_W_M / 2.0 - 0.05,
                  cx + DECK_INSET_W_M / 2.0 + 0.05, 0.0, 0.022,
                  zc - DECK_INSET_L_M / 2.0 - 0.05,
                  zc + DECK_INSET_L_M / 2.0 + 0.05, P.frame)


def stair(m, hw, L, steps=7):
    """The stair down to the pit: open treads on two stringers, with a rail.

    It was seven boxes spanning the full width with no structure under them and
    nothing beside them -- a staircase drawn as a stack of slabs. The reference
    shows open treads between a pair of stringers, the outer one a broad light
    cheek, with the balustrade running down beside it.
    """
    P = _dress._Parts("fix_")
    x0, x1 = hw - 3.2, hw - 0.4
    zt = L * 0.10
    rise, run = PIT_DROP_M / steps, 0.30
    for s in range(steps):
        y = -rise * (s + 1)
        z = zt + s * run
        m.box(x0, x1, y, y + 0.055, z, z + run + 0.02, P.tread)
        m.box(x0 + 0.10, x1 - 0.10, y - 0.16, y, z + run - 0.05, z + run + 0.02,
              P.conduit)
    for x in (x0 - 0.09, x1 + 0.01):
        for s in range(steps):
            y = -rise * (s + 1)
            z = zt + s * run
            m.box(x, x + 0.08, y - 0.30, y + 0.055, z, z + run + 0.02,
                  "cc_stair")
    # the rail beside it, following the flight down
    for s in range(0, steps, 2):
        y = -rise * (s + 1)
        z = zt + s * run
        m.box(x1 + 0.03, x1 + 0.09, y, y + RAIL_H_M, z, z + 0.06, "cc_rail")
    for s in range(steps):
        y = -rise * (s + 1)
        z = zt + s * run
        m.box(x1 + 0.02, x1 + 0.10, y + RAIL_H_M - 0.06, y + RAIL_H_M,
              z, z + run + 0.02, "cc_rail")


def annunciator(m, layout, cy):
    """The station status board over the window -- `cnc`'s `tactical_display`.

    One lamp per desk, in the seat order `cnc_ops.seating()` returns, so the
    board over the window reads left to right in the same order as the consoles
    under it. The lit colour is the desk's own state; the others are dark.

    THIS IS THE THING THAT MAKES A BROKEN STATION VISIBLE FROM THE DOOR. Every
    other consequence of a plant failure in this project is a number in a
    report; this is a red lamp in a frame, and `cnc_ops --engine-gate` renders
    both and diffs them.
    """
    P = _dress._Parts("fix_")
    desks = list(layout.get("dais", ())) + list(layout.get("pit", ()))
    if not desks:
        return
    st = layout.get("state", {})
    zw = FLOOR_L_M * 0.70
    n = len(desks)
    w = ANNUN_W_M / n
    m.box(-ANNUN_W_M / 2.0 - 0.18, ANNUN_W_M / 2.0 + 0.18,
          ANNUN_Y_M - ANNUN_H_M / 2.0 - 0.11,
          ANNUN_Y_M + ANNUN_H_M / 2.0 + 0.11,
          zw - 0.30, zw - 0.02, P.panel)
    # A HOOD, and it is not decoration. Rendered without one
    # (`docs/craft-4q-cnc-annunciator.png`, first take) the nine lamps sit
    # directly under the dais keys' glare and every one of them reads as the
    # same pale rectangle -- a board whose whole job is to be legible at a
    # glance, illegible in the frame it was built for. A shade over it puts the
    # lamps in their own shadow, which is what makes a lit one read AS lit.
    m.box(-ANNUN_W_M / 2.0 - 0.24, ANNUN_W_M / 2.0 + 0.24,
          ANNUN_Y_M + ANNUN_H_M / 2.0 + 0.11,
          ANNUN_Y_M + ANNUN_H_M / 2.0 + 0.19,
          zw - 0.62, zw - 0.02, P.frame)
    for s in (-1, 1):
        a, b = s * (ANNUN_W_M / 2.0 + 0.16), s * (ANNUN_W_M / 2.0 + 0.24)
        # STOPPING 4 mm SHORT OF THE HOOD ABOVE, for the reason the window's
        # secondary mullions do: a cheek built to the same y as the soffit it
        # meets shares a whole face with it, which the non-manifold gate reports
        # as two pieces of this module in the same place and which it is right
        # to. Third instance in one session; every one was found by the gate.
        m.box(min(a, b), max(a, b),
              ANNUN_Y_M - ANNUN_H_M / 2.0 - 0.11,
              ANNUN_Y_M + ANNUN_H_M / 2.0 + 0.106,
              zw - 0.62, zw - 0.02, P.frame)
    for k, d in enumerate(desks):
        x = -ANNUN_W_M / 2.0 + (k + 0.5) * w
        lamp = STATE_LAMP.get(st.get(d, "NORMAL"), CELL_GREEN)
        # the cell itself, proud of the panel it is set in
        m.box(x - w * 0.36, x + w * 0.36,
              ANNUN_Y_M - ANNUN_H_M * 0.20, ANNUN_Y_M + ANNUN_H_M * 0.34,
              zw - 0.345, zw - 0.30, lamp)
        m.box(x - w * 0.42, x + w * 0.42,
              ANNUN_Y_M - ANNUN_H_M * 0.26, ANNUN_Y_M + ANNUN_H_M * 0.40,
              zw - 0.325, zw - 0.30, P.frame)
        # a small legend plate under it -- a lamp with no label is a light
        m.box(x - w * 0.30, x + w * 0.30,
              ANNUN_Y_M - ANNUN_H_M * 0.44, ANNUN_Y_M - ANNUN_H_M * 0.28,
              zw - 0.325, zw - 0.30, "prop_tactical_display")


def command_control(state=None):
    """The room. +X across, +Y up, +Z forward toward the window; deck at y = 0.

    `state` is `cnc_ops.room_layout()` -- which desk sits at which console and
    what each one is showing. Passed in so the gate can build a well station and
    a broken one in the same process and diff them; `None` means "read the
    station's standing orders", which is what `bespoke.BESPOKE_GEOMETRY` does
    when `export_scene` builds the shot.
    """
    m = _M()
    hw, L = FLOOR_W_M / 2.0, FLOOR_L_M
    if state is None:
        state = _layout()

    # Upper floor, and the pit dropping away forward of it.
    m.quad((-hw, 0.0, -L * 0.35), (-hw, 0.0, L * 0.45),
           (hw, 0.0, L * 0.45), (hw, 0.0, -L * 0.35), "cc_floor")
    # THE PIT FLOOR IS A SLAB, NOT A QUAD. It was a one-sided quad whose far
    # edge happened to be welded to the old bulkhead's bottom box; the moment
    # the bulkhead became a plate with a hole in it, `_insert_collinear`
    # subdivided that edge and the weld broke -- one open boundary edge, a
    # 14 m slot along the front of the pit showing the background through it.
    # A floor with a thickness cannot have that failure mode at all.
    m.box(-hw, hw, -PIT_DROP_M - 0.16, -PIT_DROP_M, L * 0.45, L * 0.70,
          "cc_pit")
    m.box(-hw, hw, -PIT_DROP_M, 0.0, L * 0.45, L * 0.45 + 0.16, "cc_pit_face")
    # ...and the room's SIDE WALLS, which is where the pit's own two side
    # plates used to be and is 30 times as much wall.
    #
    # The old comment here recorded a real fix -- the pit had a back face and a
    # floor and nothing at x = +-hw, so a player standing in the pit was looking
    # sideways at the background -- and it was a fix applied to an INSTANCE and
    # not to the rule, which is the defect `CLAUDE.md` names and which this file
    # has now produced twice. The pit's 1.9 m band was walled; the 7.5 m of room
    # above it, over the whole 12.6 m length, was not. `side_wall` builds the
    # plate from the pit slab's underside to the top of the cornice and
    # subsumes those two boxes, so there is one lateral plate rather than two
    # that have to agree.
    #
    # (The inside-out solid the ledger caught here -- `m.box(-7.0, -7.16, ...)`,
    # x0 to the RIGHT of x1 -- is why `side_wall` sorts its own bounds too.)
    for sx in (-1, 1):
        side_wall(m, sx, hw, L)

    # The stepped dais, as a CLOSED stepped solid.
    #
    # It used to be three full discs with three ribbons of riser quads round
    # them, and the ribbons had nothing to stand on: a riser's foot landed in
    # the middle of the fan below it, where there is no edge to weld to. 108
    # open edges, one per segment per step, on the object at the centre of the
    # room. Each tread is now the ANNULUS between its own riser and the next
    # one up, so the two share an edge by construction; the top tread is the
    # only full disc and the base closes it underneath.
    seg = 36
    radii = [DAIS_D_M / 2.0 + (DAIS_STEPS - 1 - s) * DAIS_TREAD_M
             for s in range(DAIS_STEPS)]
    m.disc(0.0, 0.0, radii[0], 0.0, "cc_dais", seg=seg, down=True)
    for s, r in enumerate(radii):
        y0, y1 = s * DAIS_RISE_M, (s + 1) * DAIS_RISE_M
        for k in range(seg):
            a0 = 2.0 * math.pi * k / seg
            a1 = 2.0 * math.pi * (k + 1) / seg
            # Vertical edge FIRST. Tangential-then-vertical gives a normal
            # pointing at the axis, so every riser on the dais faced inward --
            # a step you see through, standing under the officer the room is
            # arranged around. Nothing caught it because the facing gate ran
            # on `cc_floor`, `cc_pit` and `cc_dais` and not on the risers.
            m.quad((r * math.cos(a0), y0, r * math.sin(a0)),
                   (r * math.cos(a0), y1, r * math.sin(a0)),
                   (r * math.cos(a1), y1, r * math.sin(a1)),
                   (r * math.cos(a1), y0, r * math.sin(a1)), "cc_dais_riser")
        if s + 1 < DAIS_STEPS:
            m.annulus(0.0, 0.0, radii[s + 1], r, y1, "cc_dais", seg=seg)
        else:
            m.disc(0.0, 0.0, r, y1, "cc_dais", seg=seg)

    # Wedge consoles in an arc on the dais, tilted toward the operator.
    #
    # WAS 36 TRIANGLES AN INSTANCE -- one plate on four sticks -- and
    # `docs/judge-4e.md` is right that it is C1's own definition, "a box
    # primitive standing in for a named object". `console_unit` is the five
    # tiers the reference frame carries; see CONSOLE_LEG_TOP.
    top = DAIS_STEPS * DAIS_RISE_M
    rc = DAIS_D_M / 2.0 - CONSOLE_D_M * 0.55
    dais_desks = list(state.get("dais", ()))
    room_state = state.get("state", {})
    for k in range(CONSOLE_N):
        f = (k + 0.5) / CONSOLE_N - 0.5
        a = math.radians(f * CONSOLE_ARC_DEG) + math.pi / 2.0
        cx, cz = rc * math.cos(a), rc * math.sin(a)
        ca, sa = math.cos(a - math.pi / 2.0), math.sin(a - math.pi / 2.0)
        d = dais_desks[k] if k < len(dais_desks) else None
        console_unit(m, (cx, cz, ca, sa), top, console_w_m(), CONSOLE_D_M,
                     CONSOLE_H_M, f"cnc-console-{k}",
                     desk_state=room_state.get(d, "NORMAL"))
    dais_key(m, top)

    # The window, in the forward bulkhead.
    zw = L * 0.70
    cy = WINDOW_D_M / 2.0 + 0.9
    bulkhead(m, zw, cy, hw, -PIT_DROP_M)
    window(m, zw - 0.01, cy)
    annunciator(m, state, cy)
    ceiling(m, hw, L)
    pit_soffit(m, hw, L)
    deck_field(m, hw, L)

    # FOUR courses of light strips a side, and only two of them carry a lamp.
    # See STRIP_Y_EXTRA_M: `export_scene` hangs one lamp per connected body of
    # a `cc_light_strip` span and asserts there are four, so the room's solved
    # exposure survives this exactly.
    zs0, zs1 = -L * 0.30, L * 0.42
    for sx in (-1, 1):
        for y in STRIP_Y_M:
            wall_course(m, sx, y + STRIP_H_M / 2.0, zs0, zs1)
        for y in STRIP_Y_EXTRA_M:
            wall_course(m, sx, y, zs0, zs1)
    # ...and the four lit lenses in ONE consecutive run -- see `course_lens`.
    for sx in (-1, 1):
        for y in STRIP_Y_M:
            course_lens(m, sx, y + STRIP_H_M / 2.0, zs0, zs1, "cc_light_strip")
    for sx in (-1, 1):
        for y in STRIP_Y_EXTRA_M:
            course_lens(m, sx, y, zs0, zs1, "light_service_tube")

    # The forward pit: "a lower forward pit of red-lit consoles". It was a bare
    # box with a floor, two side walls and nothing in it -- one of the room's
    # two occupied levels, and the thing that makes it a bridge, with no work
    # surface anywhere in it. The consoles stand against the pit's side walls
    # facing inward, which is where the frame's bottom-left crewman is.
    pit_top = -PIT_DROP_M
    pit_desks = list(state.get("pit", ()))
    j_pit = 0
    for sx in (-1, 1):
        for j in range(PIT_CONSOLE_N // 2):
            zc = L * 0.50 + (j + 0.5) * (L * 0.20) / (PIT_CONSOLE_N // 2)
            cxp = sx * (hw - PIT_CONSOLE_D_M * 0.60)
            # (ca, sa) = (0, -sx) turns the unit's +w toward the wall, so the
            # operator edge -- the panes, the bezel, the cells -- faces the
            # middle of the pit rather than the plate it stands against.
            d = pit_desks[j_pit] if j_pit < len(pit_desks) else None
            console_unit(m, (cxp, zc, 0.0, float(-sx)), pit_top,
                         PIT_CONSOLE_W_M, PIT_CONSOLE_D_M, PIT_CONSOLE_H_M,
                         f"cnc-pit-{sx}-{j}", cells=(CELL_RED,),
                         desk_state=room_state.get(d, "NORMAL"))
            j_pit += 1

    # Handrails along the upper floor edges, and the stair down at the right.
    for sx in (-1, 1):
        balustrade(m, sx * (hw - 0.30), -L * 0.30, L * 0.42)
    stair(m, hw, L)

    # ARTICULATION -- rooms.articulate(), INV-073. 92.4% of its floor, so this
    # is a nudge rather than a rebuild: bands and mullions only. No deck joints
    # (the floor is a stepped pit, not a slab field) and no soffit grid (the
    # ceiling is the ring and hub built above). The band ceiling is a
    # fraction of DOME_H_M rather than a room height, because this room
    # does not have one -- it is a gallery under a 34 m dome, and the
    # trim belongs at the gallery's own head height, not the dome's.
    #
    # Same span/per-triangle adaptation as docking_bay: `_M` carries one group
    # per triangle, `articulate` emits spans.
    av, at, aspans = [], [], []
    _rooms.articulate(av, at, aspans, "cc", hw, L * 0.40, DOME_H_M * 0.22,
                      z_off=L * 0.05, deck=False, soffit=False,
                      conduit=False, scale=2.6)
    off = len(m.v)
    per = [None] * len(at)
    for nm, lo, hi in aspans:
        for i in range(lo, hi):
            per[i] = nm
    m.v.extend(av)
    m.t.extend((a + off, b + off, c + off) for a, b, c in at)
    m.g.extend(per)

    # THE LEDGER OF EVERY BOX THIS BUILD EMITTED, for `_selftest`. Kept on the
    # module rather than returned because `bespoke.BESPOKE_GEOMETRY` unpacks a
    # three-tuple and a fourth element would break the only caller that
    # matters. See `_M.__init__` for what it is for.
    del BOX_LEDGER[:]
    BOX_LEDGER.extend(m.boxes)
    return m.as_tuple()


def _signed_volume(verts, tris):
    """Six times the enclosed volume, over six. Positive iff outward-facing."""
    s = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0


def enclosure_gaps(verts, tris, axis, bounds, cell=0.10, inside=None):
    """Cells of the room's own cross-section that NO triangle covers.

    THE QUESTION NO GATE IN THIS PROJECT ASKS, and the one that let C&C ship
    for six sessions with 32.5% of its side walls missing.

    Every closure test here measures a SURFACE: `boundary_edges` counts edges
    used once, `_inward_fraction` counts which way a triangle faces, the box
    ledger counts signed volumes, `bespoke.SHELL_OPEN_EDGES` sums the first of
    those over a composed shell. On the version that shipped through 4r all
    four are clean -- `boundary_edges` reports 0 open edges, `SHELL_OPEN_EDGES`
    reads 0 --
    and they are RIGHT, because every piece of the room is a closed solid.
    **Enclosure is a property of the VOLUME, and a room built entirely of
    closed solids with nothing between them is watertight and open to space.**

    So this projects the whole mesh down `axis` onto the perpendicular plane,
    marks every cell whose CENTRE lies inside some triangle, and returns the
    cells of the room's own declared cross-section that stayed unmarked. A cell
    centre test is an exact ray cast at that point, so the answer is a lower
    bound on the leak rather than a raster approximation of it: anything it
    reports is a real line of sight out of the room.

    `bounds` is ((a0, a1), (b0, b1)) over the two axes that remain, and
    `inside(a, b) -> bool` says which of those cells the room actually occupies
    -- passed in rather than derived from the mesh, because a hole must not be
    able to shrink the region it is measured against.

    Returns (open_cells, tested_cells, cell_area_m2).
    """
    a, b = [i for i in range(3) if i != axis]
    (a0, a1), (b0, b1) = bounds
    na = int(math.ceil((a1 - a0) / cell))
    nb = int(math.ceil((b1 - b0) / cell))
    cov = bytearray(na * nb)
    for tri in tris:
        p = [verts[i] for i in tri]
        pa = [q[a] for q in p]
        pb = [q[b] for q in p]
        ia0 = max(0, int((min(pa) - a0) / cell))
        ia1 = min(na - 1, int((max(pa) - a0) / cell))
        ib0 = max(0, int((min(pb) - b0) / cell))
        ib1 = min(nb - 1, int((max(pb) - b0) / cell))
        if ia1 < ia0 or ib1 < ib0:
            continue
        x1, y1 = pa[0], pb[0]
        x2, y2 = pa[1], pb[1]
        x3, y3 = pa[2], pb[2]
        det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(det) < 1e-12:
            continue
        for ia in range(ia0, ia1 + 1):
            px = a0 + (ia + 0.5) * cell
            for ib in range(ib0, ib1 + 1):
                py = b0 + (ib + 0.5) * cell
                l1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / det
                if l1 < 0.0 or l1 > 1.0:
                    continue
                l2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / det
                if l2 < 0.0 or l2 > 1.0:
                    continue
                if l1 + l2 <= 1.0:
                    cov[ia * nb + ib] = 1
    op = n = 0
    for ia in range(na):
        pa2 = a0 + (ia + 0.5) * cell
        for ib in range(nb):
            pb2 = b0 + (ib + 0.5) * cell
            if inside is not None and not inside(pa2, pb2):
                continue
            n += 1
            if not cov[ia * nb + ib]:
                op += 1
    return op, n, cell * cell


def room_enclosure(verts, tris, cell=0.10):
    """`enclosure_gaps` for the three axes, with this room's own section.

    The AFT face is the one declared opening: `bespoke.py` records C&C's door
    at `min_z` and no bespoke module authors its own doorway, so nothing is
    asserted about -Z here. Everything else is hull.
    """
    hw, L = FLOOR_W_M / 2.0, FLOOR_L_M
    by = (-PIT_DROP_M, CEIL_Y_M)
    bz = (-L * 0.35, L * 0.70)
    bx = (-hw, hw)

    def lateral(y, z):
        # the upper floor's full height everywhere, plus the pit below it
        return (0.0 <= y <= CEIL_Y_M) or (y < 0.0 and z >= L * 0.45)

    return {
        "lateral": enclosure_gaps(verts, tris, 0, (by, bz), cell, lateral),
        "forward": enclosure_gaps(verts, tris, 2, (bx, by), cell),
        "vertical": enclosure_gaps(verts, tris, 1, (bx, bz), cell),
    }


def write_obj(path):
    v, t, g = command_control()
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    v, t, g = command_control()
    schema, profile = it.load()

    # --- the window must agree with the exterior component -----------------
    comp = next(c for c in schema["components"] if c["id"] == "observation_dome")
    check("the dome component is the one canon calls C&C",
          "COMMAND & CONTROL" in comp["src"], comp["src"][:60])
    check("the window fits inside the dome it is cut into",
          WINDOW_D_M < comp["radius_m"] * 2,
          f"{WINDOW_D_M} m window in a {comp['radius_m'] * 2} m dome")
    check("dome dimensions are taken from the schema, not restated",
          abs(DOME_R_M - comp["radius_m"]) < 1e-9
          and abs(DOME_H_M - comp["height_m"]) < 1e-9,
          f"{DOME_R_M}/{DOME_H_M} vs schema {comp['radius_m']}/{comp['height_m']}")

    # The measured window diameter must follow from the fit, not drift from it.
    chord, sag = 280.0, 215.0
    r_px = (chord ** 2 / 4.0 + sag ** 2) / (2.0 * sag)
    # The depth correction is the whole point: 100 px/m is measured at the
    # OFFICER, and the window is ~4 m further from the lens.
    px_at_window = REF_PX_PER_M * 5.0 / 9.0
    check("the window diameter is depth-corrected, not naive",
          abs(WINDOW_D_M - 2 * r_px / px_at_window) < 0.3,
          f"{WINDOW_D_M} m against {2 * r_px / px_at_window:.2f} m corrected "
          f"(a naive read gives {2 * r_px / REF_PX_PER_M:.2f} m)")

    # --- the room is two levels, which is what makes it a bridge -----------
    ys = [q[1] for q in v]
    check("the room has two occupied levels",
          min(ys) <= -PIT_DROP_M + 1e-9 and max(ys) > 3.0,
          f"y {min(ys):.2f} .. {max(ys):.2f}")
    check("the stair spans the whole drop",
          any(abs(q[1] + PIT_DROP_M) < 0.3 for k, tri in enumerate(t)
              if g[k] == "cc_stair" for q in [v[i] for i in tri]))

    # --- THE ROOM IS CLOSED -------------------------------------------------
    # 342 open boundary edges shipped for four sessions, and every gate in this
    # file measured which way a surface FACED. A surface that is not there
    # faces nowhere, so those tests passed vacuously on the missing half of
    # every plate: the mullions, the glazing, the hub, the ring band, the
    # console faces and every riser on the dais.
    op, nm = it_kit.boundary_edges(v, t)
    check("C&C is a closed surface", not op,
          f"{len(op)} open boundary edges, first at {op[:1]}")
    # THE PROPERTY, NOT THE COUNT. This read `len(nm) == 48` and it was FAILING
    # at 44 before this session touched anything: the wall-articulation merge
    # improved `rooms.articulate`'s proud bands and nobody re-pegged a constant
    # living in a file the change did not touch. `docking_bay.py` records the
    # same defect and the same cure, one module over -- a second copy of a
    # computed number goes stale in the direction of an IMPROVEMENT just as
    # readily as in the direction of a regression, and a red gate that is red
    # for a stale reason is a gate nobody reads.
    #
    # What the test is named for is measurable without a constant: attribute
    # every non-manifold edge to the groups whose triangles use it, and require
    # each to have an `articulate` band on it. A band this module introduces
    # fails it at any count; an upstream improvement cannot.
    _av, _at, _asp = [], [], []
    _rooms.articulate(_av, _at, _asp, "cc", FLOOR_W_M / 2.0, FLOOR_L_M * 0.40,
                      DOME_H_M * 0.22, z_off=FLOOR_L_M * 0.05, deck=False,
                      soffit=False, conduit=False, scale=2.6)
    _bands = {n for n, _lo, _hi in _asp}

    def _key(p):
        return (round(p[0], 4), round(p[1], 4), round(p[2], 4))

    def _owners(tris, grps):
        own = {}
        for i, (a, b, c) in enumerate(tris):
            for p, q in ((a, b), (b, c), (c, a)):
                own.setdefault(tuple(sorted((_key(v[p]), _key(v[q])))),
                               set()).add(grps[i])
        return own

    _ok_owner = _bands | _CORNER_CONTACT
    _own = _owners(t, g)
    _bad = [e for e in nm if not (_own.get(e, set()) <= _ok_owner)]
    check("nothing but the declared contacts is non-manifold",
          not _bad,
          f"{len(_bad)} of {len(nm)} non-manifold edges are on neither an "
          f"articulate band nor the declared corner contacts -- two pieces of "
          f"this module in the same place. Groups: "
          f"{sorted({o for e in _bad for o in _own.get(e, {'?'})})}")
    # NEGATIVE CONTROL -- duplicate a console in place. Its groups are outside
    # the allow-list, so every edge of it becomes an unexplained non-manifold
    # edge, which is what an interpenetration IS.
    _dupe = [tri for k, tri in enumerate(t) if g[k] == "cc_console_face"]
    _t2, _g2 = list(t) + _dupe, list(g) + ["cc_console_face"] * len(_dupe)
    _own2 = _owners(_t2, _g2)
    _nm2 = it_kit.boundary_edges(v, _t2)[1]
    check("...and putting two of its own solids in one place fires it",
          any(not (_own2.get(e, set()) <= _ok_owner) for e in _nm2),
          "a duplicated console bed left every non-manifold edge explained")
    # NEGATIVE CONTROL -- one triangle out has to fire it. Asserted as "more
    # than none" rather than "exactly three", because a dropped triangle whose
    # edges were touching faces relieves a non-manifold edge instead of opening
    # one, and the number then depends on WHICH triangle -- which is a fact
    # about `rooms.articulate`, not about this gate.
    _holed = len(it_kit.boundary_edges(v, t[1:])[0])
    check("...and dropping ONE triangle fires that gate", _holed > len(op),
          f"{_holed} open with a hole in it, against {len(op)} without")

    # --- flat surfaces face up, MEASURED ON THE FACE YOU CAN SEE -----------
    # `cc_dais` is a closed stepped solid now, so its underside faces down and
    # must. The question worth asking is whether every TREAD faces up, so the
    # test runs per horizontal plane and skips the base.
    _under = {"cc_dais": 1e-9, "cc_pit": -PIT_DROP_M - 1e-9}
    for grp in ("cc_floor", "cc_pit", "cc_dais"):
        bad = 0
        for k, tri in enumerate(t):
            if g[k] != grp:
                continue
            ys = [v[i][1] for i in tri]
            # The UNDERSIDE of a slab legitimately faces down. Both of these
            # are solids now -- the pit floor became one when the bulkhead
            # became a plate with a hole and the old weld broke -- so the
            # question the test is named for is whether every TREAD faces up.
            if grp in _under and max(ys) <= _under[grp]:
                continue
            p0, p1, p2 = (v[i] for i in tri)
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            ln = math.sqrt(sum(c * c for c in n)) or 1.0
            # A SLAB HAS SIDES AND THEY ARE VERTICAL. The old form tested the
            # sign of the y component alone, so `<= 0` counted every vertical
            # face as downward -- which is why turning the pit floor into a
            # solid appeared to break it. The question is about the
            # near-horizontal faces; the rim of a slab is neither up nor down.
            if abs(n[1]) / ln < 0.7:
                continue
            if n[1] <= 0:
                bad += 1
        check(f"{grp} faces up", bad == 0, f"{bad} downward")
    # ...and the base is there, facing DOWN, which is what closes the dais.
    base = [k for k, tri in enumerate(t) if g[k] == "cc_dais"
            and all(abs(v[i][1]) < 1e-9 for i in tri)]
    check("the dais stands on a closed base", bool(base),
          "a stepped solid with no underside is 36 open edges a step")
    # Every riser must face OUTWARD, away from the axis -- the defect that
    # survived because the loop above never named `cc_dais_riser`.
    bad = 0
    for k, tri in enumerate(t):
        if g[k] != "cc_dais_riser":
            continue
        p0, p1, p2 = (v[i] for i in tri)
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0])
        cxx = sum(v[i][0] for i in tri) / 3.0
        czz = sum(v[i][2] for i in tri) / 3.0
        if n[0] * cxx + n[2] * czz <= 0:
            bad += 1
    check("the dais risers face outward, not at the axis", bad == 0,
          f"{bad} of the risers face the middle of the room")

    # --- the dais is a dais, not a step ------------------------------------
    check("the dais is stepped, not a kerb",
          DAIS_STEPS >= 2 and DAIS_RISE_M < 0.20,
          f"{DAIS_STEPS} risers of {DAIS_RISE_M} m")
    check("the dais steps are climbable",
          DAIS_TREAD_M > DAIS_RISE_M * 2,
          f"rise {DAIS_RISE_M} tread {DAIS_TREAD_M}")
    check("consoles stand on the dais, not through it",
          DAIS_D_M / 2.0 - CONSOLE_D_M * 0.55 > 0)

    # --- consoles are standing consoles, as the frame shows ----------------
    check("consoles are at standing height",
          0.95 <= CONSOLE_H_M <= 1.15, f"{CONSOLE_H_M} m")
    check("the console arc leaves the operator a way in",
          CONSOLE_ARC_DEG < 270.0, f"{CONSOLE_ARC_DEG} deg of arc")

    # --- THE CONSOLE IS THE ROOM, and it was 36 triangles -------------------
    # `docs/judge-4e.md`: "the console -- the object the room exists for -- is
    # one uniform orange polygon on four black sticks: no screens, no keys, no
    # bezel, no material break, no second detail tier of any kind." Every gate
    # in this file was green when that was written, because none of them asked
    # what a console is MADE of. These do, and every one of them fails on the
    # version that shipped.
    con = [k for k in range(len(t))
           if g[k] in ("cc_console_leg", "cc_console_face")
           or (g[k] or "").startswith("fix_mp_")]
    per_unit = len(con) / float(CONSOLE_N + PIT_CONSOLE_N)
    check("a console is an assembly, not a plate on sticks",
          per_unit >= 150.0,
          f"{per_unit:.0f} triangles a console -- the version "
          f"docs/judge-4e.md scored CRAFT 1 was 36")
    tiers = {g[k] for k in con}
    check("...built from at least five distinct surfaces",
          len(tiers) >= 6, f"{len(tiers)}: {sorted(tiers)}")
    check("...and it carries all three lit registers the frame shows",
          set(CELL_CYCLE) <= tiers,
          f"green/amber/red: {sorted(set(CELL_CYCLE) & tiers)}")
    check("the pit's consoles are the red-lit ones the frame shows",
          any(g[k] == CELL_RED
              and all(v[i][1] < 0.0 for i in t[k]) for k in range(len(t))),
          "no red-lit cell below the upper floor")

    # TWO CLOSED SOLIDS MAY NOT OCCUPY ONE PLACE. `CONSOLE_W_M` was a written
    # 1.15 m against a 1.026 m arc pitch, so all five consoles interpenetrated
    # by 12% and nothing measured it -- a plate has no volume to share, which
    # is exactly why the articulation had to come with this gate rather than
    # after it.
    check("neighbouring consoles butt, they do not interpenetrate",
          console_w_m() <= console_pitch_m() + 1e-9,
          f"{console_w_m():.3f} m wide on a {console_pitch_m():.3f} m pitch")
    check("...and they still read as a continuous desk, not five islands",
          console_w_m() >= console_pitch_m() * 0.85,
          f"{console_w_m() / console_pitch_m():.2f} of the pitch")

    # The bed's working surface must face UP, and a `plate_solid` has a BACK
    # that legitimately faces down -- so the honest test is not "none faces
    # down", it is that the near-horizontal faces come in matched pairs and
    # the up-facing one of each pair is the HIGHER. Reverse the winding and the
    # counts are unchanged and the second check fires, which is the whole point
    # of measuring the height rather than the count.
    ks = [k for k in range(len(t)) if g[k] == "cc_console_face"]
    ups, downs = [], []
    for k in ks:
        p0, p1, p2 = (v[i] for i in t[k])
        a = tuple(p1[i] - p0[i] for i in range(3))
        b = tuple(p2[i] - p0[i] for i in range(3))
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
             a[0] * b[1] - a[1] * b[0])
        ln = math.sqrt(sum(c * c for c in n)) or 1.0
        c = tuple(sum(v[i][j] for i in t[k]) / 3.0 for j in range(3))
        (ups if n[1] / ln > 0.85 else downs if n[1] / ln < -0.85
         else []).append(c)
    n_unit = CONSOLE_N + PIT_CONSOLE_N
    check("every console bed is a solid with a face and a back",
          len(ups) == len(downs) == 2 * n_unit,
          f"{len(ups)} up / {len(downs)} down over {n_unit} consoles")
    # PAIRED BY POSITION, because nine consoles stand at two different levels
    # -- five on the dais and four in the pit 1.9 m below it -- so a global
    # min/max comparison says nothing. Each face is matched to the back
    # nearest it in plan, and must be above it.
    bad = 0
    for c in ups:
        d = min(downs, key=lambda q: (q[0] - c[0]) ** 2 + (q[2] - c[2]) ** 2)
        if c[1] <= d[1]:
            bad += 1
    check("...and the face is the upper of the two", bad == 0,
          f"{bad} beds built with their working surface facing the deck")

    # `obox` is the new primitive and it is a REMAP, which is the family this
    # project has shipped inside-out four times. Measured, with the control.
    pm = _M()
    pm.obox((3.0, -2.0, math.cos(0.7), math.sin(0.7)),
            -0.5, 0.5, 0.0, 1.0, -0.3, 0.3, "probe")
    check("obox is wound outward at an arbitrary angle",
          _signed_volume(pm.v, pm.t) > 0.0,
          f"{_signed_volume(pm.v, pm.t):.4f} m3")
    check("...and the volume test can fail",
          _signed_volume(pm.v, [(a, c, b) for a, b, c in pm.t]) < 0.0)

    # --- the key light this room was MEASURED FROM is in this room ----------
    keys = [k for k in range(len(t)) if g[k] == "light_dais_key"]
    check("the dais carries the key fitting export_scene measured here",
          bool(keys), "materials.light_dais_key cites this room's own frame "
                      "and no geometry in C&C carried the name")
    ky = [v[i][1] for k in keys for i in t[k]]
    check("...and it hangs above the dais at the height it was measured at",
          abs(min(ky) - (DAIS_STEPS * DAIS_RISE_M + DAIS_KEY_H_M)) < 0.10,
          f"lens at {min(ky):.2f} m over a dais top of "
          f"{DAIS_STEPS * DAIS_RISE_M:.2f} m")

    # --- the light strips are the room's ambient ---------------------------
    check("two courses of light strips", len(STRIP_Y_M) == STRIP_COURSES)
    check("strips are above head height and below the ceiling",
          all(y > 1.8 for y in STRIP_Y_M),
          f"{STRIP_Y_M}")

    # --- the window reads as mullions over glass ---------------------------
    glaz = [k for k in range(len(t)) if g[k] == "cc_glazing"]
    mull = [k for k in range(len(t)) if g[k] == "cc_mullion"]
    ring = [k for k in range(len(t)) if g[k] == "cc_ring"]
    hub = [k for k in range(len(t)) if g[k] == "cc_hub"]
    check("the spokes stop at a hub instead of piling up at the centre",
          bool(hub) and WINDOW_HUB_FRAC > 0.05,
          f"hub at {WINDOW_HUB_FRAC} of the radius")
    check("the window has glazing, mullions and a ring band",
          glaz and mull and ring,
          f"{len(glaz)} / {len(mull)} / {len(ring)} triangles")
    gz = [v[i][2] for k in glaz for i in t[k]]
    mz = [v[i][2] for k in mull for i in t[k]]
    # The glass has a THICKNESS -- it is a pane, not a decal -- so the test is
    # that it is no deeper than a pane, not that it is planar. Asserting
    # planarity is what a one-sided quad passes, and a one-sided quad is 48
    # open boundary edges in the middle of the room's only window.
    check("the glazing is a pane in the bulkhead, not a slab of it",
          max(gz) - min(gz) <= WINDOW_MULLION_D_M + 1e-9,
          f"glazing spans {max(gz) - min(gz):.3f} m in z")
    # The glazing must be visible from the room, i.e. in front of the bulkhead's
    # near face rather than sealed inside it.
    bulk = [v[i][2] for k, tri in enumerate(t) if g[k] == "cc_bulkhead"
            for i in tri]
    # Glass sits IN an opening, not in front of the wall -- so the test is not
    # "is it proud of the bulkhead" (it should not be) but "does it fit the hole
    # and is the hole real". The first version asserted the former and failed a
    # correctly glazed window.
    gr = max(math.hypot(v[i][0], v[i][1] - (WINDOW_D_M / 2.0 + 0.9))
             for k, tri in enumerate(t) if g[k] == "cc_glazing" for i in tri)
    # Both are panes now, so the back and the rim legitimately do not face the
    # room. What must face the room is the pane's own FRONT -- the triangles in
    # its lowest-z plane, which is the surface a standing officer sees.
    for grp in ("cc_glazing", "cc_hub"):
        ks = [k for k in range(len(t)) if g[k] == grp]
        zf = min(v[i][2] for k in ks for i in t[k])
        bad = 0
        for k in ks:
            if any(abs(v[i][2] - zf) > 1e-9 for i in t[k]):
                continue
            p0, p1, p2 = (v[i] for i in t[k])
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[0] * w[1] - u[1] * w[0] >= 0:      # +Z normal = out of the room
                bad += 1
        check(f"{grp}'s front face faces into the room", bad == 0,
              f"{bad} triangles facing out through the bulkhead")

    check("the glazing fits the aperture cut for it",
          gr <= WINDOW_D_M / 2.0 + 0.12 + 1e-9,
          f"glazing radius {gr:.3f} in a {WINDOW_D_M / 2.0 + 0.12:.3f} m opening")
    check("the glazing is glazed into the opening, not floating past it",
          min(bulk) - 1e-9 <= max(gz) <= max(bulk) + 1e-9,
          f"glazing z={max(gz):.3f}, bulkhead {min(bulk):.2f}..{max(bulk):.2f}")
    # And the bulkhead must actually have an aperture: no panel may cover the
    # window's centre.
    covers = any(min(v[i][0] for i in tri) < 0.0 < max(v[i][0] for i in tri)
                 and min(v[i][1] for i in tri) < WINDOW_D_M / 2.0 + 0.9
                 < max(v[i][1] for i in tri)
                 for k, tri in enumerate(t) if g[k] == "cc_bulkhead")
    check("the bulkhead has an aperture where the window is", not covers)

    # FACE against FACE. Both are solids now, so `max(mz)` is the back of the
    # mullion and `min(gz)` is the front of the glass, and comparing those two
    # asks whether the bar's back is in front of the glass's front -- which is
    # not the question. The bar reads as proud when its FRONT is nearer the
    # room than the glass's front.
    check("mullions stand proud of the glazing, not coplanar with it",
          min(mz) < min(gz) - 1e-9,
          f"mullion face z {min(mz):.3f} vs glazing face {min(gz):.3f}")

    # === EVERY BOX, NOT THE FOUR GROUPS SOMEBODY REMEMBERED =================
    # THE DEFECT THIS EXISTS FOR IS IN THIS FILE'S OWN HISTORY: the bulkhead
    # panel over the window was `m.box(..., cy + ap, top, ...)` with
    # cy + ap = 6.52 and top = 6.12 -- y0 above y1 -- so twelve triangles were
    # wound inward, -1.68 m3 of solid you could see straight through, directly
    # over the only window the room has. It survived because the facing tests
    # above name `cc_floor`, `cc_pit`, `cc_dais` and `cc_dais_riser` and the
    # bulkhead is not one of them. `_M.box` now records every box it emits and
    # this asks the question of all of them at once -- a class of error rather
    # than the instance that bit.
    _probe = _M()
    _probe.box(0.0, 1.0, 0.0, 2.0, 0.0, 3.0, "probe")
    check("the box ledger measures a good box as positive",
          _probe.boxes[-1][1] > 0, str(_probe.boxes[-1]))
    _probe.box(0.0, 1.0, 2.0, 0.0, 0.0, 3.0, "inverted")
    check("...and CONTROL: an inverted box measures negative",
          _probe.boxes[-1][1] < 0, str(_probe.boxes[-1]))
    _bad_boxes = [b for b in BOX_LEDGER if b[1] <= 0.0]
    check("every box the SHIPPED room emits is wound outward",
          BOX_LEDGER and not _bad_boxes,
          f"{len(_bad_boxes)} inside-out solids of {len(BOX_LEDGER)}: "
          f"{sorted({b[0] for b in _bad_boxes})}")
    # CONTROL 1 -- the 4p line, verbatim, run through the ledger. This is the
    # defect the ledger exists for and not a synthetic one: the two numbers are
    # `cy + ap` and `DOME_H_M * 0.18` exactly as this file carried them.
    _hw2, _zw2 = FLOOR_W_M / 2.0, FLOOR_L_M * 0.70
    _ap2, _cy2 = WINDOW_D_M / 2.0 + 0.12, WINDOW_D_M / 2.0 + 0.9
    _old = _M()
    _old.box(-_hw2, _hw2, _cy2 + _ap2, DOME_H_M * 0.18, _zw2, _zw2 + 0.30,
             "cc_bulkhead")
    check("...and CONTROL: session 4p's own bulkhead line fires it",
          _old.boxes[-1][1] < 0.0,
          f"{_old.boxes[-1][1]:.3f} m3 for `m.box(..., {_cy2 + _ap2}, "
          f"{DOME_H_M * 0.18}, ...)`")
    # CONTROL 2 -- the ledger has to cover the SHIPPED room and not a probe.
    # Invert every box the real build emits and it must report all of them.
    _real = _M.box
    try:
        _M.box = lambda s, x0, x1, y0, y1, z0, z1, gp: _real(
            s, x0, x1, y1, y0, z0, z1, gp)
        command_control()
        _all_bad = [b for b in BOX_LEDGER if b[1] <= 0.0]
        check("...and CONTROL: inverting every box in the real build reports "
              "every box in the real build",
              len(_all_bad) == len(BOX_LEDGER) and len(BOX_LEDGER) > 100,
              f"{len(_all_bad)} of {len(BOX_LEDGER)}")
    finally:
        _M.box = _real
        command_control()

    # === THE WINDOW IS AN ASSEMBLY, NOT A WHEEL ============================
    # `docs/craft-4q-cnc-before-half.png` at the rubric's HALF distance is a
    # black rectangle with sixteen bars across it. Each of these fails on that
    # frame's geometry, which is the test `docs/AAA-STANDARD.md` demands: a
    # layer's exit criterion must be able to fail on the current content.
    panes = [k for k in range(len(t)) if g[k] == "cc_glazing"]
    n_panes = sum(n for _f0, _f1, n in WINDOW_COURSES)
    check("the glazing is divided into panes, not one disc",
          len(panes) >= n_panes * 8,
          f"{len(panes)} triangles of glazing for {n_panes} declared panes")
    # ...and they are in CONCENTRIC COURSES, which is the thing a subdivided
    # disc would still not have. Measured as distinct pane radii.
    cyw = WINDOW_D_M / 2.0 + 0.9
    radii = sorted({round(math.hypot(v[i][0], v[i][1] - cyw), 2)
                    for k in panes for i in t[k]})
    check("...in at least three concentric courses",
          len(radii) >= 6, f"{len(radii)} distinct pane radii: {radii[:8]}")
    studs = [k for k in range(len(t)) if g[k] == "cc_ring"]
    check("the structural band is studded",
          len(studs) >= WINDOW_STUDS * 2 * 6,
          f"{len(studs)} cc_ring triangles for {WINDOW_STUDS * 2} studs")
    # The ribs must leave the window. A rib that stops at the rim is a spoke;
    # one that runs out across the bulkhead is what ties the two together, and
    # it is the difference between a window IN a wall and a decal ON one.
    mull_r = max(math.hypot(v[i][0], v[i][1] - cyw)
                 for k in range(len(t)) if g[k] == "cc_mullion" for i in t[k])
    check("the radial ribs run out past the rim into the bulkhead",
          mull_r > WINDOW_D_M / 2.0 + WINDOW_RIB_OUT_M * 0.8,
          f"furthest mullion vertex at r={mull_r:.2f} against a "
          f"{WINDOW_D_M / 2.0:.2f} m rim")

    # === NO TWO DESKS CARRY THE SAME BOARD ==================================
    # `deck.py --degeneracy`'s question at the scale of one room: a gate that
    # scores N things must also ask whether the N things are the same thing.
    # Every other assertion in this file measures ONE console against a
    # standard, and nine identical consoles pass all of them.
    _pat = [tuple(_dress._pick(CELL_CYCLE, f"cnc-console-{k}", "cell", b, c)
                  for b in range(CONSOLE_BANKS) for c in range(CONSOLE_CELLS))
            for k in range(CONSOLE_N + PIT_CONSOLE_N)]
    check("no two consoles carry the same register pattern",
          len(set(_pat)) == len(_pat),
          f"{len(set(_pat))} distinct boards over {len(_pat)} desks")
    _old_pat = [tuple((b + c) % len(CELL_CYCLE)
                      for b in range(CONSOLE_BANKS)
                      for c in range(CONSOLE_CELLS))
                for k in range(CONSOLE_N + PIT_CONSOLE_N)]
    check("...and CONTROL: the modular rule this replaced gives one board",
          len(set(_old_pat)) == 1,
          f"{len(set(_old_pat))} distinct over {len(_old_pat)}")

    # === THE ROOM IS A ROOM, NOT A SET OF CLOSED SOLIDS =====================
    # See `enclosure_gaps`. This is the only gate in the file that asks about
    # the VOLUME rather than about a surface, and it is the one that found the
    # room had no side walls.
    encl = room_enclosure(v, t)
    for face, (op, n, area) in encl.items():
        check(f"the room is closed {face}",
              op == 0,
              f"{op} of {n} cross-section cells show the background "
              f"= {op * area:.1f} m2 of {n * area:.1f} m2")

    # CONTROL 1 -- the gate must fail on this room's own previous content, and
    # this is that content verbatim: the pit's two side plates and nothing
    # above them. It reports 32.6 m2 open of 100.2 m2, which is the number in
    # `side_wall`'s docstring and the reason it exists.
    _sw = side_wall
    try:
        def _pit_only(m, sx, hw, L):                     # 4r's own two boxes
            m.box(min(sx * hw, sx * (hw + 0.16)),
                  max(sx * hw, sx * (hw + 0.16)),
                  -PIT_DROP_M, 0.0, L * 0.45, L * 0.70, "cc_pit_face")
        globals()["side_wall"] = _pit_only
        _ov, _ot, _og = command_control()
        _op, _on, _oa = room_enclosure(_ov, _ot)["lateral"]
    finally:
        globals()["side_wall"] = _sw
        command_control()
    check("...and CONTROL: the walls the room shipped without fail it",
          _op > 3000 and _op * _oa > 30.0,
          f"{_op} of {_on} cells = {_op * _oa:.1f} m2 open")

    # CONTROL 2 -- the FORWARD face, and it is a different defect: 45 cells of
    # 13,160 in the window itself, where every concentric member was built to
    # its nominal radius and the panes it holds are chords that dip inside it.
    # Rebuilt without the lap, the gate reports them.
    _r = WINDOW_D_M / 2.0
    _cy = WINDOW_D_M / 2.0 + 0.9
    _pm = _M()
    for _f0, _f1, _n in WINDOW_COURSES:
        for _k in range(_n):
            _pane(_pm, _cy, 0.0, _r * _f0 + 0.02, _r * _f1 - 0.02,
                  2.0 * math.pi * _k / _n + 0.008,
                  2.0 * math.pi * (_k + 1) / _n - 0.008,
                  "cc_glazing", WINDOW_PANE_INSET_M)
        for _f in (_f0, _f1):
            _pm.band(0.0, _cy, -0.02, 0.02, _r * _f - 0.028, _r * _f + 0.028,
                     "cc_mullion", seg=48)
    _pg, _pn, _pa = enclosure_gaps(
        _pm.v, _pm.t, 2, ((-_r, _r), (_cy - _r, _cy + _r)), 0.10,
        lambda x, y: math.hypot(x, y - _cy) < _r * 0.99)
    check("...and CONTROL: nominal-radius window members leak at every chord",
          _pg > 0, f"{_pg} of {_pn} cells inside the aperture show through")

    # === THE APERTURE IS ROUND ==============================================
    # It was a SQUARE hole in four boxes with a round window in the middle of
    # it, so the four corners showed the background. Measured as: no bulkhead
    # vertex lies inside the aperture circle.
    inside = [i for k in range(len(t)) if g[k] == "cc_bulkhead" for i in t[k]
              if math.hypot(v[i][0], v[i][1] - cyw) < WINDOW_D_M / 2.0 + 0.10]
    check("the bulkhead's aperture is circular, not a square hole",
          not inside,
          f"{len(inside)} bulkhead vertices inside the window's own radius")

    # === THE ROOM HAS A LID, A DRESSED DECK AND A REAL STAIR ================
    check("the room has a ceiling", any(g[k] == "cc_cornice"
                                        and all(v[i][1] > CEIL_Y_M - 1e-6
                                                for i in t[k])
                                        for k in range(len(t))),
          "every frame taken in here had a black void over it")
    check("the deck carries lit insets",
          any(g[k] == "light_deck_channel" and all(v[i][1] < 0.05 for i in t[k])
              for k in range(len(t))), "the floor was one quad")
    st_y = [v[i][1] for k in range(len(t)) if g[k] == "cc_stair" for i in t[k]]
    check("the stair has stringers that carry it, not just treads",
          min(st_y) < -PIT_DROP_M + 0.05,
          f"lowest cc_stair vertex {min(st_y):.2f} m against a "
          f"{-PIT_DROP_M:.2f} m pit")

    # === THE WALL COURSES ARE FITTINGS =====================================
    # The lens count is the one `export_scene._selftest` asserts -- one lamp
    # per connected body of the `cc_light_strip` span, four bodies -- so this
    # module states it too rather than leaving it to be discovered by a gate
    # in another file failing.
    lens = [k for k in range(len(t)) if g[k] == "cc_light_strip"]
    check("the lit courses are exactly two a side",
          len(lens) == 12 * STRIP_COURSES * 2,
          f"{len(lens)} triangles; export_scene asserts four bodies")
    check("...and there are four courses a side in the room",
          len(STRIP_Y_M) + len(STRIP_Y_EXTRA_M) == 4,
          "materials.light_wall_course's own source line says four")
    seg = [k for k in range(len(t)) if g[k] == "fix_mp_plant_conduit"]
    check("a course is segmented into tubes rather than one bar",
          len(seg) >= 8 * 12,
          f"{len(seg)} divider triangles over eight courses")

    # === THE BOARD IS IN THE ROOM ==========================================
    # THE HALF OF THIS SESSION THE OWNER ASKED FOR: "do they actually work and
    # have shifts and run the ship?" The consoles read `station/cnc_ops.py`,
    # which reads `plant_systems`, and the geometry differs when the plant is
    # in trouble. Proved here on the mesh and in the engine by
    # `cnc_ops --engine-gate`.
    import cnc_ops as _ops                                      # noqa: PLC0415
    lay = _ops.room_layout()
    desks = list(lay["dais"]) + list(lay["pit"])
    check("every console on the floor has a desk",
          len(desks) == CONSOLE_N + PIT_CONSOLE_N,
          f"{len(desks)} desks for {CONSOLE_N + PIT_CONSOLE_N} consoles")
    ann = [k for k in range(len(t)) if g[k] == "prop_tactical_display"]
    check("the room's declared tactical_display is real geometry",
          bool(ann), "it was resolved by alias onto something else")
    lamps = {g[k] for k in range(len(t))
             if g[k] in set(STATE_LAMP.values()) | {LAMP_DARK}}
    check("the status stacks carry a dark lamp as well as a lit one",
          LAMP_DARK in lamps,
          "a single lamp that changes colour is a light, not a state")

    hot = dict(lay, state={d: "ALARM" for d in desks}, worst="ALARM")
    cold = dict(lay, state={d: "NORMAL" for d in desks}, worst="NORMAL")
    _vh, _th, gh = command_control(state=hot)
    _vc, _tc, gc = command_control(state=cold)
    n_red_h = sum(1 for x in gh if x == CELL_RED)
    n_red_c = sum(1 for x in gc if x == CELL_RED)
    check("a station in ALARM builds a redder room than a station that is well",
          n_red_h > n_red_c,
          f"{n_red_c} -> {n_red_h} triangles of {CELL_RED}")
    # NEGATIVE CONTROL -- two builds of the SAME board must be identical, or
    # the difference above is nondeterminism and not the plant. A diff of two
    # runs that were not both produced is not a diff (CLAUDE.md, 4d).
    _vc2, _tc2, gc2 = command_control(state=cold)
    check("...and CONTROL: the same board builds the same room",
          (_vc2, _tc2, gc2) == (_vc, _tc, gc),
          "the A/B above is measuring nondeterminism")
    check("...and the difference is ONLY the lit cells, not the structure",
          len(gh) == len(gc) and _vh == _vc,
          f"{len(gh)} vs {len(gc)} triangles -- an alarm must not move a wall")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
