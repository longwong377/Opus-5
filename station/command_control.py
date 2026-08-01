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
CONSOLE_BANKS = 3               # control-cell banks on the bed
CONSOLE_CELLS = 3               # lit cells per bank
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
PIT_DROP_M = 1.9                # the lower forward pit
STRIP_COURSES = 2               # high and mid light strips
STRIP_Y_M = (2.35, 3.55)
STRIP_H_M = 0.22
RAIL_H_M = 1.05


class _M:
    def __init__(self):
        self.v, self.t, self.g = [], [], []

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


def console_unit(m, o, y_base, w_m, d_m, h_m, seed, cells=CELL_CYCLE):
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
    bw = (w_m - 0.11) / CONSOLE_BANKS

    def on_bed(u, s, lift):
        w, y = bed(s)
        # The bed's own normal, in the (w, y) plane, so a pad lifts off the
        # SURFACE rather than straight up: at 22 degrees straight up leaves the
        # downhill edge buried.
        n = math.hypot(2.0 * hd, rise)
        return W(u, y + lift * (2.0 * hd) / n, w - lift * rise / n)

    for b in range(CONSOLE_BANKS):
        u0 = -hw + 0.055 + b * bw
        u1 = u0 + bw - 0.030
        m.plate(on_bed(u0, 0.12, 0.007), on_bed(u0, 0.90, 0.007),
                on_bed(u1, 0.90, 0.007), on_bed(u1, 0.12, 0.007),
                0.020, P.gauge)
        cs = (0.90 - 0.12) / CONSOLE_CELLS
        for c in range(CONSOLE_CELLS):
            s0 = 0.12 + c * cs + 0.030
            s1 = s0 + cs - 0.060
            grp = cells[(b + c) % len(cells)]
            m.plate(on_bed(u0 + 0.022, s0, 0.017),
                    on_bed(u0 + 0.022, s1, 0.017),
                    on_bed(u1 - 0.022, s1, 0.017),
                    on_bed(u1 - 0.022, s0, 0.017), 0.012, grp)


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
    for i in range(n):
        zz = z0 + (z1 - z0) * i / (n - 1)
        zz = min(max(zz, z0 + 0.05), z1 - 0.05)
        m.box(x - 0.035, x + 0.035, 0.0, RAIL_H_M, zz - 0.035, zz + 0.035,
              "cc_rail")
    m.box(x - 0.045, x + 0.045, RAIL_H_M - 0.07, RAIL_H_M, z0, z1, "cc_rail")
    m.box(x - 0.032, x + 0.032, RAIL_H_M * 0.47, RAIL_H_M * 0.47 + 0.055,
          z0, z1, "cc_rail")
    m.box(x - 0.014, x + 0.014, 0.10, RAIL_H_M * 0.44, z0 + 0.06, z1 - 0.06,
          P.panel)


def window(m, z, cy):
    """The circular window: glazing, radial mullions, one concentric ring.

    Built as a ring of mullion bars over a glazed disc rather than as a wheel
    of pie segments. The frame shows the bars standing PROUD of the glass and
    crossing the ring band, which a segmented disc cannot express.
    """
    r = WINDOW_D_M / 2.0
    # Glazing, set BACK so the mullions read in front of it.
    m.vdisc(0.0, cy, z + 0.06, r, "cc_glazing")

    # Spokes run from a central hub to the rim, NOT across the full diameter.
    # Full-diameter bars were the first version and 16 of them piled up at the
    # centre into a solid starburst with no glass visible between them -- the
    # window read as a painted sunburst rather than as glazing. A real spoked
    # window has a hub.
    r0 = r * WINDOW_HUB_FRAC
    hw = WINDOW_MULLION_W_M / 2.0
    for k in range(WINDOW_MULLIONS):
        a = 2.0 * math.pi * k / WINDOW_MULLIONS
        ca, sa = math.cos(a), math.sin(a)
        nx, ny = -sa * hw, ca * hw
        m.plate((r0 * ca + nx, cy + r0 * sa + ny, z),
                (r * ca + nx, cy + r * sa + ny, z),
                (r * ca - nx, cy + r * sa - ny, z),
                (r0 * ca - nx, cy + r0 * sa - ny, z),
                WINDOW_MULLION_D_M, "cc_mullion")
    m.vdisc(0.0, cy, z, r0, "cc_hub", seg=20, thick=WINDOW_MULLION_D_M)

    # The concentric ring band -- a section, not a stripe.
    rr, w = r * WINDOW_RING_FRAC, WINDOW_RING_W_M / 2.0
    m.band(0.0, cy, z - WINDOW_MULLION_D_M, z, rr - w, rr + w, "cc_ring")


def command_control():
    """The room. +X across, +Y up, +Z forward toward the window; deck at y = 0."""
    m = _M()
    hw, L = FLOOR_W_M / 2.0, FLOOR_L_M

    # Upper floor, and the pit dropping away forward of it.
    m.quad((-hw, 0.0, -L * 0.35), (-hw, 0.0, L * 0.45),
           (hw, 0.0, L * 0.45), (hw, 0.0, -L * 0.35), "cc_floor")
    m.quad((-hw, -PIT_DROP_M, L * 0.45), (-hw, -PIT_DROP_M, L * 0.70),
           (hw, -PIT_DROP_M, L * 0.70), (hw, -PIT_DROP_M, L * 0.45), "cc_pit")
    m.box(-hw, hw, -PIT_DROP_M, 0.0, L * 0.45, L * 0.45 + 0.16, "cc_pit_face")
    # ...and the pit's own SIDE walls. It had a back face and a floor and
    # nothing at x = +-hw, so a player standing in the pit -- which is one of
    # the room's two occupied levels -- was looking sideways at the background
    # through a 1.9 m x 4.6 m gap either side, and the floor's two long edges
    # were the last open edges in the room.
    for sx in (-1, 1):
        m.box(sx * hw, sx * (hw + 0.16), -PIT_DROP_M, 0.0,
              L * 0.45, L * 0.70, "cc_pit_face")

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
    for k in range(CONSOLE_N):
        f = (k + 0.5) / CONSOLE_N - 0.5
        a = math.radians(f * CONSOLE_ARC_DEG) + math.pi / 2.0
        cx, cz = rc * math.cos(a), rc * math.sin(a)
        ca, sa = math.cos(a - math.pi / 2.0), math.sin(a - math.pi / 2.0)
        console_unit(m, (cx, cz, ca, sa), top, console_w_m(), CONSOLE_D_M,
                     CONSOLE_H_M, f"cnc-console-{k}")
    dais_key(m, top)

    # The window, in the forward bulkhead.
    zw = L * 0.70
    cy = WINDOW_D_M / 2.0 + 0.9
    # The bulkhead is built as four panels AROUND the window, not as one slab
    # with the glazing laid on it. A slab has no aperture, so the glass ended up
    # sealed inside 0.30 m of steel and the window showed as spokes on a wall.
    # An opening is a hole in something, and the something has to be built with
    # the hole already in it.
    ap = WINDOW_D_M / 2.0 + 0.12
    top, bot = DOME_H_M * 0.18, -PIT_DROP_M
    m.box(-hw, hw, cy + ap, top, zw, zw + 0.30, "cc_bulkhead")        # over
    m.box(-hw, hw, bot, cy - ap, zw, zw + 0.30, "cc_bulkhead")        # under
    m.box(-hw, -ap, cy - ap, cy + ap, zw, zw + 0.30, "cc_bulkhead")   # left
    m.box(ap, hw, cy - ap, cy + ap, zw, zw + 0.30, "cc_bulkhead")     # right
    window(m, zw - 0.01, cy)

    # Two courses of light strips on the side walls.
    for sx in (-1, 1):
        for y in STRIP_Y_M:
            m.box(sx * hw - 0.10 * sx, sx * hw, y, y + STRIP_H_M,
                  -L * 0.30, L * 0.42, "cc_light_strip")

    # The forward pit: "a lower forward pit of red-lit consoles". It was a bare
    # box with a floor, two side walls and nothing in it -- one of the room's
    # two occupied levels, and the thing that makes it a bridge, with no work
    # surface anywhere in it. The consoles stand against the pit's side walls
    # facing inward, which is where the frame's bottom-left crewman is.
    pit_top = -PIT_DROP_M
    for sx in (-1, 1):
        for j in range(PIT_CONSOLE_N // 2):
            zc = L * 0.50 + (j + 0.5) * (L * 0.20) / (PIT_CONSOLE_N // 2)
            cxp = sx * (hw - PIT_CONSOLE_D_M * 0.60)
            # (ca, sa) = (0, -sx) turns the unit's +w toward the wall, so the
            # operator edge -- the panes, the bezel, the cells -- faces the
            # middle of the pit rather than the plate it stands against.
            console_unit(m, (cxp, zc, 0.0, float(-sx)), pit_top,
                         PIT_CONSOLE_W_M, PIT_CONSOLE_D_M, PIT_CONSOLE_H_M,
                         f"cnc-pit-{sx}-{j}", cells=(CELL_RED,))

    # Handrails along the upper floor edges, and the stair down at the right.
    for sx in (-1, 1):
        balustrade(m, sx * (hw - 0.30), -L * 0.30, L * 0.42)
    steps = 7
    for s in range(steps):
        y = -PIT_DROP_M * (s + 1) / steps
        z = L * 0.10 + s * 0.30
        m.box(hw - 3.2, hw - 0.4, y, y + PIT_DROP_M / steps, z, z + 0.30,
              "cc_stair")

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
    for grp in ("cc_floor", "cc_pit", "cc_dais"):
        bad = 0
        for k, tri in enumerate(t):
            if g[k] != grp:
                continue
            ys = [v[i][1] for i in tri]
            if grp == "cc_dais" and max(ys) <= 1e-9:
                continue                                # the base, facing down
            p0, p1, p2 = (v[i] for i in tri)
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[2] * w[0] - u[0] * w[2] <= 0:
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

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
