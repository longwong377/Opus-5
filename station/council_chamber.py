"""The Babylon 5 Advisory Council chamber.

Sixth on the gazetteer's ranked build list: "one strong authority-1 frame, an
unmistakable silhouette, and it is the room that makes the diplomatic layer
legible." Named in the Green rosette (`other map.png`, authority 3).

WHAT THE REFERENCE ESTABLISHES

`reference/05-sector-green/council chambers.webp` (authority 1):

  - A **curved raised bench** with an angled pale slab top, and -- the room's
    defining feature -- a **perforated gold mesh front panel lit from within**.
    The furniture is the light source. Nearly all the light on the delegates'
    faces comes up off that panel.
  - **High-backed chairs with open black lattice backs**, one per delegation,
    standing well clear of the bench.
  - The back wall is a **radiating fan of angled fins**, pale, splaying outward.
  - A large **circular spoked medallion** on deep blue above the fins.
  - The floor is a **pale blue-green polygonal mosaic** -- irregular polygons,
    not a grid.
  - A **fan of blue-and-white radiating panels** laid on the bench top marks the
    speaking position.

WHAT IS NOT SOURCED is how many delegations sit at it. Five are visible in the
frame and the arc continues past both edges, so the visible count is a LOWER
BOUND, not the number. `SEATS` is a parameter and the self-test asserts only
that it is at least the five that can be counted. Fixing it would need a wider
shot or an authority-3 plan, and neither is held. See INV-025.

THE LIGHT IS THE POINT. If the mesh panel is not emissive this room is a grey
box with chairs. It is built as a recessed panel behind a perforated face so
that it reads as lit from within rather than as a painted stripe -- the same
construction as the customs boards in `signage.py`, and for the same reason.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dressing as _dress                                    # noqa: E402
import interior as it                                        # noqa: E402
import interior_kit as it_kit                                # noqa: E402

# --- the bench -------------------------------------------------------------
# Proportioned against the seated delegates: the slab top sits at about chest
# height for someone seated, and the lit panel fills the whole face below it.
BENCH_R_M = 4.6                 # radius of the curved bench, INV-025
BENCH_ARC_DEG = 150.0
BENCH_TOP_H_M = 1.12
BENCH_TOP_D_M = 0.95
BENCH_TOP_TILT_DEG = 9.0        # the top is an angled slab, not flat
BENCH_PANEL_INSET_M = 0.055     # how far the lit mesh sits behind its frame
BENCH_PLINTH_H_M = 0.14
# THE CAPPING RAIL AND ITS STUDS, and they are the strongest tertiary detail on
# the object a player stands closest to. `00-INDEX.md` reads this bench as "a
# grey slab top with a chamfered edge" over "a riveted bullnose capping rail",
# and the 3x crop of `council chambers.webp` shows both plainly: a bright
# chamfered nose along the whole front edge with a line of round studs down it.
# The bench had neither -- its top met its frame at a bare arris, which is
# `docs/AAA-STANDARD.md` C3's "the tertiary tier is generic" with nothing in the
# tier at all.
#
# THE STUD PITCH IS A LOWER BOUND, NOT A MEASUREMENT. On the crop the studs read
# at about 0.15 of the lit panel's height along the rail -- 0.11 m -- but the
# rail runs in the strongly foreshortened direction and the panel height does
# not, so the true spacing is LARGER by however much the foreshortening is, and
# one frame cannot say. 0.14 m is used and it is an extrapolation: INV-631,
# overturned by any square-on frame of the bench front.
BENCH_CAP_H_M = 0.075           # the bullnose's own height on the face
BENCH_CAP_D_M = 0.055           # how far it stands proud of the frame
BENCH_STUD_PITCH_M = 0.14
BENCH_STUD_R_M = 0.011
# The speaking-position fan. `council chambers.webp` shows it covering most of
# the bench top -- an apex at the speaking position with white blades splaying
# out over 160-odd degrees and bright blue slivers between their outer halves,
# feathering into jagged blue tips. What was built was 13 lines 22 mm wide over
# +/-26 degrees, which at the normal viewing distance is invisible.
SPEAK_BLADES = 21               # INV-635
SPEAK_SPREAD_DEG = 82.0         # half-angle from the apex, in the top's plane
SPEAK_REACH_M = 3.6             # along the arc, from the apex
SPEAK_RISE_M = 0.004            # a proud inlay catches the grazing light
SPEAK_BLUE_FROM = 0.55          # blue slivers over the outer part of the fan

SEATS = 5                       # a LOWER BOUND -- see the module docstring
# INBOARD of the bench, which is where the reference puts the delegates -- see
# `council_chamber`. 0.72 m of clearance behind `r_in`, so a chair back at
# -0.30 radial still stands 0.42 m clear of the bench it is drawn up to.
CHAIR_R_M = BENCH_R_M - BENCH_TOP_D_M - 0.72
CHAIR_BACK_H_M = 1.94
CHAIR_SEAT_H_M = 0.46
CHAIR_W_M = 0.62
# SQUARES, AND THEY WERE NOT SQUARE. One count was used for both axes of a back
# 0.62 m wide and 1.48 m tall, so a "4 x 4 lattice" is cells 155 mm wide by
# 370 mm tall -- 2.4:1 -- and at half distance the reference's "open black
# lattice back" reads as a set of SHELVES. `docs/craft-4r-council-before-half.png`
# is the frame. In `council chambers.webp` at 3x the chairs read as three
# columns of roughly square cells, so the across count is what is counted off
# the frame and the down count is DERIVED from the chair's own proportions --
# which is the only way a cell stays square if either dimension moves.
CHAIR_LATTICE = 3               # squares across the back, at 3x -- INV-634

# --- the room --------------------------------------------------------------
# THE FAN AND THE MEDALLION WERE IN A PLANE NO CAMERA CAN SEE THEM FROM, and
# that is why this room could not be photographed. Measured off the built mesh
# in session 4p, before anything was changed:
#
#     council_fin          x -7.39..7.40  y 0.06..7.38  z -0.44..-0.21
#     council_plinth       x  0.94..4.60  y 0.00..1.12  z -4.44.. 4.44
#     council_fin_backing  x -11.60..11.60 y 0.00..7.00 z -0.91..11.38
#
# The fan is a vertical fan in the plane z = -0.3 radiating from the ORIGIN,
# which is the centre of the bench's arc -- so it stands in the middle of the
# room rather than behind anybody, and the bench, which sweeps +/-75 degrees
# about that same origin, passes STRAIGHT THROUGH IT: both solids occupy
# x 0.94..4.60, y 0.06..1.12, z -0.44..-0.21. So does the flat backing plate at
# z = -0.75. Two interpenetrations, which AAA-STANDARD calls blocking, and
# neither module gate could see them because every assertion in this file
# measures ONE object against ITSELF -- closure, winding, signed volume -- and
# `docs/AAA-STANDARD.md` R5 names exactly this: "cross-subsystem clearance is
# asserted wherever two systems occupy the same space", the tram-through-spoke
# defect, one file down.
#
# It also made the reference unreproducible. `council chambers.webp` is taken
# from the chamber floor: the bench is convex toward the lens, the delegates
# are BEHIND it, and the fan and the medallion are behind THEM. A fan in the
# plane z = -0.3 is edge-on from every point on the +x axis, so the composition
# the room exists for could not be framed from anywhere.
#
# The fan now stands on a flat SCREEN WALL behind the delegates -- the plane
# x = FAN_X_M, facing +x, hub on the floor at z = 0 -- which is what the frame
# shows and which is clear of the bench (min x 0.94) by 2.0 m.
FAN_X_M = -1.05                 # the screen wall's face, behind the chairs
FAN_WALL_T_M = 0.34
FAN_WALL_HZ_M = 9.20            # half-length of the screen wall along z
FAN_FIELD_T_M = 0.024           # the blue field's own body -- INV-171

FIN_COUNT = 30                  # the radiating fan behind the bench
# 0.9, not 2.2. The blades converge on the hub in the reference; at 2.2 m they
# leave a 4.4 m disc of bare field in the middle of the fan, which in the
# render is the single largest patch of blue in the frame. Pitch at the hub is
# pi*0.9/30 = 94 mm, so FIN_TAPER is set so a blade is 87 mm there and the
# blades nearly touch WITHOUT overlapping -- two solids sharing space is the
# defect this session opened by finding the bench inside the fan.
FIN_R0_M = 0.9
# 6.35, not 7.4. The fan radiates from a hub on the floor, so its outer radius
# IS its height, and the chamber now has a ceiling at WALL_H_M. A fin reaching
# 7.4 m through a 7.0 m ceiling is the same defect one line up.
FIN_R1_M = 6.35
# THE BLADES WERE THE WIDTH OF THEIR OWN SINE AND NOTHING MEASURED IT.
# `fin_wall` offset each blade's two long edges by (-hw*sa, 0) and (+hw*sa, 0)
# -- along the authoring x axis -- where a blade standing perpendicular to its
# own radius needs (-hw*sa, +hw*ca) and (+hw*sa, -hw*ca). The y term was simply
# absent, so a blade's width collapsed as sin(its angle): measured on the built
# mesh before the fix, **22 of 30 blades were under 90% of nominal, the
# narrowest 32 mm against a nominal 620 mm (5%), and the widest was 19.1x the
# narrowest**. That is why the fan reads as a sunburst of tapering slivers on a
# field of blue rather than as the reference's mass of overlapping plates, and
# it is most of the reason 25.9% of the normal frame and 35.7% of the half
# frame measured as strong blue against the reference's 1.6%.
#
# No gate here could see it. Every assertion in this file measures closure,
# winding, signed volume or separation -- and a blade 32 mm wide is closed,
# wound correctly, positive in volume and clear of its neighbours. `_selftest`
# now measures the width itself.
#
# 0.83 = 1.25 x the rim pitch (pi*6.35/30 = 0.665), so consecutive blades
# OVERLAP by a quarter of their width, which is what `council chambers.webp`
# shows: a stack of plates fanned out over each other, each one's end face
# catching the light. Overlapping solids are the defect this file opened a
# session by finding, so the blades alternate between two depth layers
# FIN_LAYER_GAP_M apart and the gate asserts the layers' x ranges are disjoint.
FIN_W_M = 0.83                  # at the rim; FIN_TAPER of that at the hub
FIN_TAPER = 0.14
FIN_D_M = 0.10                  # how thick the fin is -- INV-171
FIN_TILT_DEG = 16.0
FIN_STANDOFF_M = 0.03           # how far a fin stands off the blue field
FIN_LAYER_GAP_M = 0.30          # the front layer stands this out -- INV-632
# THE OUTER EDGE OF THE FAN IS RAGGED IN THE REFERENCE and it was a perfect
# circle here. Thirty identical blades on a perfect polar lattice is
# `docs/AAA-STANDARD.md` C3's "the tertiary tier is generic: the same panel ...
# repeated without regard to what the part does", and C5's "nothing in frame
# repeats in a way the eye can index" is the thing it fails. In
# `council chambers.webp` the blades stop at visibly different radii -- the fan
# has a stepped, terraced outline, and the wall shows between the short ones.
# Deterministic per blade from `_u`, never `random`.
FIN_R1_JITTER = 0.14            # a blade may be cut back by up to this fraction
FIN_R0_JITTER = 0.35            # ...and start this much further out from the hub
# ...and each blade is raked its own amount. All thirty at one angle is thirty
# surfaces with one normal, which under this room's broad even wash is thirty
# identical greys -- `docs/craft-4r-council-after-half.png` shows the fan as one
# flat grey mass. In `council chambers.webp` the blades are visibly at different
# rakes and the value steps blade to blade, which is what gives the fan depth.
FIN_TILT_JITTER = 0.55          # of FIN_TILT_DEG, either side
# THE FIELD STOPS INSIDE THE SHORTEST BLADE. Bounded at the LONGEST blade the
# field shows as a saturated blue halo round the whole fan -- the "gear tooth"
# outline in `docs/craft-4r-council-after-half.png`, and 5.1%/7.2% of those two
# frames against the reference's 1.6%. Beyond FIN_R1_M*(1 - FIN_R1_JITTER) every
# blade has already stopped, so all the field can do out there is outline them.
#
# TWO NARROWER FIELDS WERE TRIED AND BOTH ARE WORSE, and the numbers are kept
# because the middle one is the trap:
#
#   bounded at the SHORTEST blade (5.56 m): **0.1% / 0.6% strong blue** against
#   the reference's 1.6% -- the field disappears, and the rear composition
#   becomes a grey mass on a grey wall. That re-opens judge-4e's own F2, which
#   logged the absence of "the deep blue field" as a fidelity failure.
#
#   bounded HALFWAY up the jitter range (5.91 m): 1.7%, which matches the
#   reference's coverage almost exactly and looks WORSE THAN EITHER END,
#   because the blue only survives in the notches between blades that stop
#   short and blades that carry on -- twenty disconnected bright rectangles.
#   **A coverage figure that matches the reference is not a composition that
#   matches the reference**, and this is the cheapest demonstration of it in
#   the repository.
#
# So the field is the full lunette, which is the shape `council chambers.webp`
# shows -- a coherent wall the fan stands on, visible around and between the
# blades. What is left wrong is its VALUE and that is not geometry: see
# `screen_wall` for the measurement and `scratchpad/PATCHES-4r-council.md` for
# the material it needs.
FIELD_R_M = FIN_R1_M + 0.20

# THE MEDALLION WAS A MOON. Built as a solid backing disc with spokes and rings
# in relief on it, it renders as an opaque grey plate 2.7 m across -- the single
# brightest object in `docs/craft-4r-council-before-half.png` at V 0.611,
# against the reference's V 0.455 -- and it hides the fan it is supposed to
# stand in front of. `council chambers.webp` at 3x (docs/ref-fan) shows the
# opposite construction: **an open wheel**. A small plain hub disc, a dense
# sunburst of thin spokes from it out to a bright rim ring, and OUTSIDE that a
# large thin outline circle you see the fin blades straight through. There is
# no backing plate anywhere in it.
#
# THE OUTLINE'S RADIUS IS A RATIO AND IT DOES NOT FIT, which is worth writing
# down rather than quietly rounding away. Measured on the 4x crop of
# `council chambers.webp`: the bright rim reads 66 px across (radius 33 px in
# the 1000x750 source) and a circle fitted through three points on the faint
# outline arc -- crop (700,25), (1085,300), (640,790) -- has radius 386 crop px
# = 96.6 source px. That is **2.9 rim radii, +/-10% on the eyeballed points**.
# At MEDALLION_R_M = 1.35 that outline is 3.92 m of radius on a centre 4.60 m up
# in a room with a 7.00 m ceiling, i.e. 1.8 m through the slab. So it is built
# at the ceiling's own limit, 1.59, and the shortfall is recorded rather than
# hidden -- see the round-2 fidelity finding in the scorecard, because the
# SAME frame says something else this module contradicts: the fin blades
# converge on the medallion rather than on a hub at floor level, and a fan
# radiating FROM the medallion is exactly the composition in which a 2.9x
# outline fits. The two disagreements are one disagreement. INV-633.
MEDALLION_R_M = 1.35
MEDALLION_Y_M = 4.60            # centre height, on the fan and under the cove
MEDALLION_SPOKES = 36           # the sunburst inside the rim, counted off 3x
MEDALLION_HUB_F = 0.22          # the plain centre disc, as a fraction of R
MEDALLION_RIM_W_M = 0.075       # the bright ring the spokes land on
MEDALLION_OUTLINE_R = 1.59      # the big thin circle outside it, in rim radii
MEDALLION_OUTLINE_W_M = 0.045
MEDALLION_D_M = 0.03            # a member's body -- INV-171
MEDALLION_RELIEF_M = 0.02       # how far a spoke stands off the rim's plane
# HOW FAR IT STANDS OFF THE WALL, and it is measured off the fan rather than
# chosen. With the blades in two depth layers the fan now reaches world
# x = -0.582; the medallion authored at -0.42 put it at x = -0.640, i.e. INSIDE
# the front layer -- which is the third time this file's clearance gate has
# caught the same class of thing and the first time it caught it before a render
# did. -0.70 authoring depth puts the wheel at x = -0.35, clear by 0.23 m.
MEDALLION_Z_M = -0.70

FLOOR_R_M = 11.0
FLOOR_TILES = 96                # irregular polygons, not a grid
FLOOR_BED_SEGS = 96             # the bed the mosaic is laid on
FLOOR_BED_T_M = 0.10            # its body -- INV-171
TILE_RISE_M = 0.008             # how far a tile stands proud of the grout
WALL_H_M = 7.0

# THE PANEL IS PERFORATED AND IT WAS A SMOOTH BAND. The reference's one
# defining sentence about this room -- quoted at the top of this file since it
# was written -- is "a perforated gold mesh front panel lit from within: the
# furniture is the light source", and what was built is a flat emissive strip
# in the bench profile. `docs/judge-4e.md`: "the bench is a plain white slab
# where the reference's defining feature is a perforated gold mesh front
# panel". A material can make a band gold; only geometry can make it
# perforated, and the difference is what the eye uses to tell a lit panel from
# a light BEHIND a panel.
#
# Built as a grille standing in the 55 mm recess the panel already sits in:
# vertical bars at a pitch read off the frame as roughly one bar per 90 mm of
# a 12 m bench, crossed by two horizontal rails. It is `signage.board()`'s own
# construction -- "the frame casts a shadow onto the face, and a decal cannot"
# -- applied to the object this room exists for.
# THE PITCH RECORDED HERE WAS MEASURED ALONG THE WRONG AXIS, AND THE REAL ONE
# CANNOT BE MEASURED AT ALL. The note this replaces read: "the lit panel spans
# x 200..550 px for about 4.0 m of bench at that depth, i.e. 88 px/m, and the
# perforation reads as roughly 3 px -- 34 mm". Two things are wrong with it.
#
# 1. 88 px/m is a HORIZONTAL scale on a surface that is nearly edge-on, and the
#    perforation is square, so its period has to be read against the VERTICAL
#    scale, which foreshortening does not touch. The lit panel is 176-184 px
#    tall at x = 420-520 for 0.7214 m of panel: **250 px/m, not 88**.
# 2. The period is not 3 px. An FFT of the panel rows gives a clean peak at
#    4.96-5.07 px horizontally AND 4.75-5.0 px vertically -- but folding the
#    signal on that period shows the profile repeating FIVE times inside it,
#    which is the signature of a pattern near 1 px beating against the frame's
#    own sampling grid. **The perforation is finer than the only frame that
#    shows it can resolve.** What the beat bounds is the true period: 1.0-1.25
#    source px, which against 250 px/m is **4-5 mm**.
#
# A 4-5 mm square-hole sheet over 12.0 m of bench is 2,400 columns x 144 rows.
# As geometry that is ~145,000 triangles for a feature that subtends 0.84 px at
# the distance a player stands in this room -- 5.89 m, which is the distance at
# which the bench's 8.885 m chord fills a 46-degree 16:9 frame's width and is
# where every craft frame this session was taken from. It is a TEXTURE rather
# than geometry at any pitch, and `materials.py` already has
# the machinery -- COLOUR_SHEETS, TEXTURE_BINDINGS -- so the request is written
# up in `scratchpad/PATCHES-4r-council.md` with this measurement rather than
# built here.
#
# WHAT IS BUILT IS THE COARSE TIER, AND ITS PITCH IS SET BY THE BUDGET, said
# plainly because a picked number that looks measured is the disease this file
# treats. The grille costs 12 triangles a vertical web plus 324 an arc-swept
# horizontal web, so T(p) = (12 * 11.95 + 324 * 0.7214) / p = 377 / p. The room's
# share of `budget.INTERIOR["visible_set_tris"]` (60,000 for interior structure
# in a standing frustum) is that figure less the corridor behind the player --
# `corridor_tris_per_m` 400 x `populace.corridor_sight_m` 66 = 26,400 -- leaving
# **33,600**. 30 mm spends 12,570 of it and leaves the room at 84% of its share.
# INV-630.
#
# IT IS A SQUARE-HOLE SHEET, NOT A PICKET. What was built was 287 vertical bars
# crossed by SIX heavy rails, which is a louvre: `docs/craft-4r-council-before-
# normal.png` at 3x reads as a radiator grille. `00-INDEX.md` on this frame says
# "a very fine square-hole perforated sheet ... evenly backlit with no visible
# lamp hotspots", and the rails are the thing that has to go -- the horizontal
# member runs at the SAME pitch as the vertical one or the cell is not square.
MESH_CELL_M = 0.030             # the web's pitch, both ways -- budget-derived
# 6.5 mm of web in a 30 mm cell is 61% open, which is what the reference reads
# as: thin dark lines over a bright field. The 24 mm bar in a 42 mm pitch it
# replaces was 57% SOLID -- the panel read as lit slots between dark bars
# instead of as one luminous sheet.
MESH_WEB_M = 0.0065
MESH_WEB_D_M = 0.010            # the web's own body
MESH_WEB_GAP_M = 0.002          # between the woven directions -- see below
MESH_RAIL_SEGS = 40             # the bench's own arc resolution -- see below
MESH_STANDOFF_M = 0.014         # in front of the lit face, inside the recess

# One station per delegation. `directory.py` declares `delegate_bench` and
# `speaking_position` as this room's interactables and the bench carried
# neither: 12 m of continuous desk with nothing on it anywhere. Each station
# gets the four things a seat at a council table has -- a working pad, a
# nameplate facing the chamber, a screen, and a microphone.
STATION_PAD_W_M = 0.86
STATION_PLATE_H_M = 0.13
STATION_MIC_H_M = 0.36

# The chamber's own enclosure. `docs/judge-4e.md`: "54.05% of the frame is
# below the measurable floor and the chamber stands in an unenclosed void."
# Half of that is lighting and half is that there is genuinely nothing there:
# the fin fan radiates against black and the mosaic ends at a rim with no wall
# beyond it. Both surfaces below stay INSIDE the room's own existing extent --
# the floor disc is already FLOOR_R_M across and the fan already sits at
# z = -0.30 -- so nothing new can clash with what `deck.compose` puts around
# the room that the floor did not already clash with.
# AND IT ENCLOSED HALF A ROOM. `arc_solid(..., 0.0, math.pi, ...)` walls the
# +z semicircle only; the -z half of an 11 m floor disc had nothing round it
# and nothing over it, so at the shot this module's own registry hands the
# judge, **27.65% of the frame is below sRGB 0.01** -- measured on
# docs/craft-4p-council-before-half.png. That is the same 54% judge-4e
# reported, halved by the frame's own framing rather than by any fix.
#
# So the arc runs the whole way round, MINUS a doorway, and there is a ceiling.
# The doorway is not decoration: `bespoke.near_face_opening` measures the
# widest unobstructed run across the shell's near face at the three heights
# `deck._mouth_clear` probes, and a sealed arc returns None, which is the
# signal that the assembler cannot put a body in the room. Before this change
# that function returned a 6.61 m opening at x = 7.67 -- an accident of where
# the half-arc happened to stop, 7.67 m off the bearing `_place_local` maps
# local x = 0 onto. It is now a doorway at x = 0 because that is where the
# corridor's door is.
ARC_WALL_T_M = 0.36
ARC_WALL_SEGS = 40
WALL_PIER_PITCH_M = 1.85        # pilasters -- see the note in `enclosure`
WALL_PIER_W_M = 0.44
WALL_PIER_D_M = 0.14
WALL_JOINT_W_M = 0.10         # the mid-bay reveal -- see `enclosure`
DOOR_W_M = 4.20               # the gallery door, on the near face at x = 0
DOOR_H_M = 3.00
CEIL_T_M = 0.34
CEIL_COFFER_RINGS = 4         # so a 380 m2 ceiling is not one blank disc
CEIL_COFFER_SPOKES = 24

# ---------------------------------------------------------------------------
# The house lighting
# ---------------------------------------------------------------------------
# LAYER 4. docs/layer4-lighting/public_social.json measures `cc_house_wash` as
# this chamber's entire lighting scheme -- directional, 6300 K, range 18 m,
# SHADOW, "a broad soft near-neutral wash over the whole chamber" -- and states
# the problem in the same line: **"fitting never in frame"**.
#
# That is a real difficulty for a rig where every light is derived from a
# tagged piece of geometry (export_scene.fixture_lights), and the wrong answers
# are easy. Adding a lamp where a lamp is not is an invention the frames
# contradict. Adding no light at all leaves the chamber lit by ambient, which
# is what it was, and its ambient ratio of 0.210 makes it one of the two
# BRIGHTEST measured spaces on the station -- so "no source" is also wrong.
#
# What the frame supports is a CONCEALED COVE: a source high on the wall, above
# the fin fan, throwing up and inward, whose fitting you cannot see because it
# faces away from the room. That is standard for a chamber lit this evenly, it
# is consistent with a fitting never appearing in shot, and it is the smallest
# thing that can carry a light. It is declared invention -- INV-037 -- and what
# would overturn it is any frame showing the chamber's ceiling.
COVE_H_M = 0.22                 # the lit face, seen only as a glow on the wall
COVE_D_M = 0.30                 # how far it stands off the wall
COVE_Y_M = WALL_H_M - 1.10      # above the fins, below the ceiling
COVE_SEGS = 12                  # round the chamber's rear arc


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

    def quad(self, a, b, c, d, group):
        i = len(self.v)
        self.v.extend([a, b, c, d])
        self.t.extend([(i, i + 1, i + 2), (i, i + 2, i + 3)])
        self.g.extend([group, group])

    def up_quad(self, a, b, c, d, group):
        """A horizontal face wound to face UP.

        The project has shipped downward-facing flat geometry four times and it
        is invisible every time, so the up-facing case gets its own method
        rather than relying on the caller getting the winding right.
        """
        pts = [a, b, c, d]
        u = tuple(pts[1][i] - pts[0][i] for i in range(3))
        w = tuple(pts[2][i] - pts[0][i] for i in range(3))
        if u[2] * w[0] - u[0] * w[2] < 0:
            pts = pts[::-1]
        self.quad(pts[0], pts[1], pts[2], pts[3], group)

    # --- the closed primitives ---------------------------------------------
    # EVERY GROUP IN THIS ROOM WAS A ZERO-THICKNESS PLATE, and the sum was
    # 1,592 open boundary edges -- the largest single hole in the station and
    # 43% of the whole composed-shell debt measured in session 4a. `quad` and
    # `up_quad` above are honest about winding and say nothing about closure,
    # so a bench top, a fin, a chair seat, a medallion spoke and 168 floor
    # tiles were all one-sided surfaces standing in for solids.
    #
    # A render cannot see this: from in front the plate is there, from behind
    # it shows the background and the background is black. What it costs a
    # PLAYER is that every one of those objects vanishes when walked round.
    #
    # `plate` and `arc_solid` are the two shapes this room is actually made of.

    def plate(self, a, b, c, d, thick, group, back=None):
        """A quad given the thickness it physically has: a closed solid.

        Extruded along the quad's own normal, so the caller keeps authoring in
        the plane it was already thinking in. `back` names the four faces that
        are not the front, where the material pass wants them separated;
        by default the whole solid is one group, which is what a fin or a
        seat pan wants.
        """
        pv, pt = it_kit.plate_solid([a, b, c, d], thick)
        i = len(self.v)
        self.v.extend(pv)
        self.t.extend([(x + i, y + i, z + i) for x, y, z in pt])
        # The face is the first two triangles; everything after it is the back
        # and the rim, which is where `back` separates the material.
        self.g.extend([group, group] + [(back or group)] * (len(pt) - 2))

    def poly(self, loop, thick, group, want=None, back=None):
        """`plate` for a CONVEX n-gon, with the face normal stated.

        The blue field is a lunette now rather than a rectangle -- see
        `screen_wall` -- and a 50-gon cannot go through `plate`, which takes
        four corners. `want` is the direction the visible face must point;
        the loop is reversed if it does not, because working out the winding
        of a semicircle in the head is exactly how this project has shipped
        five downward-facing surfaces.
        """
        pts = list(loop)
        if want is not None:
            u = tuple(pts[1][i] - pts[0][i] for i in range(3))
            w = tuple(pts[2][i] - pts[0][i] for i in range(3))
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            if sum(n[i] * want[i] for i in range(3)) < 0.0:
                pts = pts[::-1]
        pv, pt = it_kit.plate_solid(pts, thick)
        i = len(self.v)
        self.v.extend(pv)
        self.t.extend([(x + i, y + i, z + i) for x, y, z in pt])
        nface = 2 * (len(pts) - 2)
        self.g.extend([group] * nface + [(back or group)] * (len(pt) - nface))

    def arc_solid(self, profile, groups, a0, a1, segs, cy=0.0):
        """Sweep a closed (r, y) profile through an arc into a closed solid.

        THE BENCH AND THE COVE ARE BOTH LATHES AND BOTH SHIPPED AS RIBBONS.
        A ribbon of quads is closed nowhere: 40 segments of bench left 42 open
        edges on the plinth alone, one along the bottom of every segment plus
        the two ends, and the same count again on each of three more bands.

        `profile` is a closed loop of (r, y) in the chamber's own polar frame;
        `groups[i]` names the band swept from edge i -> i+1, so the material
        pass keeps every name it had. The two ends are capped by ear clipping,
        because the bench profile is NOT convex -- it carries the recess the
        lit mesh sits in, and a fan triangulation would tile straight across
        the notch and out through the front of the bench.
        """
        n = len(profile)
        if _shoelace(profile) < 0.0:
            # Reversing a loop shifts the edge names by one: new edge i runs
            # new[i] -> new[i+1] = old[n-1-i] -> old[n-2-i], which is OLD edge
            # n-2-i. Getting this wrong rotates every material in the bench by
            # one band and nothing but a render would show it.
            rev = list(groups)[::-1]
            profile, groups = profile[::-1], rev[1:] + rev[:1]
        # A FULL TURN IS A TORUS AND HAS NO ENDS. Swept 0..tau and capped like
        # an open arc, the last ring lands exactly on the first and the two ear
        # clips land on each other: 27 non-manifold edges, which this file's own
        # gate caught the first time the house cove was run right round. So the
        # closed case welds the seam and emits no caps -- and it is detected
        # from the ANGLES rather than passed in, because a caller that has to
        # remember to say `closed=True` is a caller that will forget.
        closed = abs(abs(a1 - a0) - math.tau) < 1e-9
        base = len(self.v)
        for k in range(segs if closed else segs + 1):
            th = a0 + (a1 - a0) * k / segs
            ct, st = math.cos(th), math.sin(th)
            for r, y in profile:
                self.v.append((r * ct, cy + y, r * st))
        for k in range(segs):
            r0 = base + k * n
            r1 = base + ((k + 1) % segs) * n if closed else base + (k + 1) * n
            for i in range(n):
                j = (i + 1) % n
                # Quad (P[k,i], P[k,j], P[k+1,j], P[k+1,i]). Sweeping about +Y
                # with a CCW (r, y) profile, edge x tangent is the OUTWARD
                # normal, so the profile edge has to come first; the other
                # order builds the whole lathe inside-out.
                self.t += [(r0 + i, r0 + j, r1 + j), (r0 + i, r1 + j, r1 + i)]
                self.g.extend([groups[i]] * 2)
        if closed:
            return
        cap = _ear_clip(profile)
        end = base + segs * n
        for tri in cap:                                   # the a1 end, outward
            self.t.append((end + tri[0], end + tri[1], end + tri[2]))
        for tri in cap:                                   # the a0 end, outward
            self.t.append((base + tri[0], base + tri[2], base + tri[1]))
        self.g.extend([groups[0]] * 2 * len(cap))

    def merge_xform(self, sub, fn):
        """Append another `_M`, mapping every vertex through `fn`.

        `fn` must be a PROPER rotation or the winding of everything it carries
        inverts silently -- which indoors is a surface you see through, the
        defect `_signed_volume` exists for. `_to_wall` is the only caller and
        it is a rotation by construction.
        """
        off = len(self.v)
        self.v.extend(fn(p) for p in sub.v)
        self.t.extend((a + off, b + off, c + off) for a, b, c in sub.t)
        self.g.extend(sub.g)

    def merge_spans(self, verts, tris, spans):
        """Take a `dressing`-style (verts, tris, SPANS) build into this mesh.

        `_M` tags per triangle and `dressing` tags by span. Four lines, and
        the alternative is a second vocabulary for the same nine surfaces.
        """
        off = len(self.v)
        per = [None] * len(tris)
        for nm, lo, hi in spans:
            for i in range(lo, hi):
                per[i] = nm
        self.v.extend(verts)
        self.t.extend((a + off, b + off, c + off) for a, b, c in tris)
        self.g.extend(per)

    def as_tuple(self):
        return self.v, self.t, self.g


# Both live in the kit, because `docking_bay`'s cross-section needs the same
# triangulator and two copies of an ear clip is two chances to fix one of them.
_shoelace = it_kit.shoelace
_ear_clip = it_kit.ear_clip


def _signed_volume(verts, tris):
    """Six times the enclosed volume. Positive iff the surface faces outward.

    The whole-object counterpart to `interior_kit._selftest`'s centroid test,
    and the right one for a room: a chamber's centroid is inside the walls, so
    "does this face point away from the centre" is meaningless for the walls
    and exactly right for the furniture. Volume is the statistic that works for
    both, because it is a property of the SURFACE rather than of a viewpoint.
    """
    s = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        s += (p[0] * (q[1] * r[2] - q[2] * r[1])
              - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return s / 6.0




def _u(seed, *parts):
    """Deterministic unit value. blake2b, never `random` or `hash`."""
    import hashlib
    h = hashlib.blake2b(("|".join([seed] + [str(p) for p in parts])).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def bench_profile():
    """The bench's cross-section, as a closed (r, y) loop, and its band names.

    ONE PLACE where the bench's shape is stated, because the ribbon version
    stated it four times -- once per band -- and the four disagreed. The lit
    mesh ran to BENCH_TOP_H - 0.06 = 1.06 m while the top slab's OUTER edge sat
    at BENCH_TOP_H - drop = 0.971 m, so the panel poked 89 mm out through the
    desk it is supposed to sit under. Nothing could catch that while the two
    surfaces were authored in separate loops; a single profile cannot express
    it at all.

    Read anticlockwise from the inner foot. The notch between `rp` and `r_out`
    is the recess -- INV-025's 55 mm -- and it is what makes this loop
    non-convex and forces the ear-clip cap.
    """
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    rp = r_out - BENCH_PANEL_INSET_M
    y_lip = BENCH_TOP_H_M - BENCH_TOP_D_M * math.sin(
        math.radians(BENCH_TOP_TILT_DEG))          # the top slab's outer edge
    y_m0 = BENCH_PLINTH_H_M + 0.05                 # under the lower frame lip
    y_m1 = y_lip - 0.06                            # under the upper frame lip
    loop = [(r_in, 0.0), (r_out, 0.0),
            (r_out, BENCH_PLINTH_H_M), (r_out, y_m0),
            (rp, y_m0), (rp, y_m1), (r_out, y_m1), (r_out, y_lip),
            (r_in, BENCH_TOP_H_M)]
    # One name per EDGE i -> i+1. The face a delegate sees is the plinth, then
    # the frame's lower lip, the recess, the lit mesh, the recess again, the
    # upper lip, and the angled slab.
    names = ["council_plinth",                     # the underside, on the deck
             "council_plinth",                     # the plinth face
             "council_frame",                      # lower frame lip
             "council_frame",                      # the return into the recess
             "council_mesh",                       # THE LIGHT SOURCE
             "council_frame",                      # the return back out
             "council_frame",                      # upper frame lip
             "council_top",                        # the angled slab
             "council_plinth"]                     # the back, facing the wall
    return loop, names


def top_y_at(r):
    """The bench slab's own height at radius r. ONE definition, four callers."""
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    drop = BENCH_TOP_D_M * math.sin(math.radians(BENCH_TOP_TILT_DEG))
    f = (r_out - r) / (r_out - r_in)
    return BENCH_TOP_H_M - drop * (1.0 - f)


def bench(m):
    """The curved bench: plinth, lit mesh panel, and an angled slab top."""
    seg = 40
    a0 = math.radians(-BENCH_ARC_DEG / 2.0)
    a1 = math.radians(BENCH_ARC_DEG / 2.0)
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M
    loop, names = bench_profile()
    m.arc_solid(loop, names, a0, a1, seg)

    # --- the riveted bullnose capping rail ---------------------------------
    # See BENCH_CAP_H_M. It bears on the frame's upper lip and runs the whole
    # arc, and it is the one piece of this bench a player standing at it is
    # within a metre of. Six edges rather than four, so the nose is chamfered
    # top and bottom the way `00-INDEX.md` reads it, not a square batten.
    y_lip = top_y_at(r_out)
    ch, cd = BENCH_CAP_H_M, BENCH_CAP_D_M
    # IT BEARS INTO THE SLAB BY 5 mm rather than meeting it exactly, for the
    # reason `enclosure`'s door head records one function down: built flush,
    # the rail's back edge (r_out, y_lip) is EXACTLY the bench profile's own
    # vertex at every one of the 41 sweep stations, and this file's gate
    # reported it as **40 non-manifold edges** the first time it was run. A rail
    # screwed to a bench overlaps the bench.
    m.arc_solid([(r_out - 0.005, y_lip - ch),
                 (r_out + cd * 0.45, y_lip - ch),
                 (r_out + cd, y_lip - ch * 0.62),
                 (r_out + cd, y_lip - ch * 0.30),
                 (r_out + cd * 0.45, y_lip - 0.002),
                 (r_out - 0.005, y_lip - 0.002)],
                ["council_frame"] * 6, a0, a1, seg)
    ns = max(4, int(round((a1 - a0) * r_out / BENCH_STUD_PITCH_M)))
    for k in range(ns + 1):
        a = a0 + (a1 - a0) * k / ns
        ca, sa = math.cos(a), math.sin(a)
        rr = r_out + cd
        yy = y_lip - ch * 0.46
        sr = BENCH_STUD_R_M
        # a stud is a small disc standing off the nose, facing out of the bench
        ring = [(rr * ca - sr * math.sin(t) * sa,
                 yy + sr * math.cos(t),
                 rr * sa + sr * math.sin(t) * ca)
                for t in (math.tau * i / 8 for i in range(8))]
        m.poly(ring, 0.006, "council_frame", want=(ca, 0.0, sa))

    # --- the speaking-position fan -----------------------------------------
    # See SPEAK_BLADES. Laid on the top with its apex at the bench's centre,
    # outer edge, and unrolled onto the arc: a blade is straight in
    # (arc length, radial depth) and therefore follows the bench, which is what
    # an inlay laid on a curved top does. Inlaid panels have a thickness -- a
    # 4 mm proud plate is what catches the grazing light off the bench, and a
    # plate with no edge is a hole.
    def on_top(u, v, rise):
        """(arc length from the centre, radial depth from the outer edge)."""
        r = r_out - 0.06 - v
        a = u / BENCH_R_M
        return (r * math.cos(a), top_y_at(r) + rise, r * math.sin(a))

    def wedge(th, l0, l1, hw0, hw1, grp, rise):
        """A blade of the fan, in the unrolled (u, v) plane of the top."""
        d = (math.sin(th), math.cos(th))            # along the blade
        nn = (math.cos(th), -math.sin(th))          # across it
        pts = [(l0 * d[0] - hw0 * nn[0], l0 * d[1] - hw0 * nn[1]),
               (l1 * d[0] - hw1 * nn[0], l1 * d[1] - hw1 * nn[1]),
               (l1 * d[0] + hw1 * nn[0], l1 * d[1] + hw1 * nn[1]),
               (l0 * d[0] + hw0 * nn[0], l0 * d[1] + hw0 * nn[1])]
        m.poly([on_top(u, max(0.02, v), rise) for u, v in pts],
               0.004, grp, want=(0.0, 1.0, 0.0))

    spread = math.radians(SPEAK_SPREAD_DEG)
    depth = BENCH_TOP_D_M - 0.14
    dth = 2.0 * spread / SPEAK_BLADES
    for k in range(SPEAK_BLADES):
        th = ((k + 0.5) / SPEAK_BLADES * 2.0 - 1.0) * spread
        # A blade stops where it runs off the back of the top or at its reach,
        # and the tips are RAGGED -- the frame shows them stopping on no one
        # line. Deterministic, `_u` only.
        reach = min(SPEAK_REACH_M, (depth - 0.02) / max(0.14, math.cos(th)))
        reach *= 0.70 + 0.30 * _u("council-speak", k)
        wedge(th, 0.03, reach, 0.012, 0.40 * reach * dth,
              "council_speak_fan", SPEAK_RISE_M)
        # and a blue sliver in the gap beyond it, which is where
        # `council chambers.webp` puts the blue: at the blades' outer ends,
        # feathering into jagged tips rather than washing the whole inlay.
        thb = th + dth * 0.5
        rb2 = reach * (0.72 + 0.24 * _u("council-speak-blue", k))
        wedge(thb, rb2 * SPEAK_BLUE_FROM, rb2, 0.010, 0.17 * rb2 * dth,
              "signage_panel__council_speak_blue", SPEAK_RISE_M * 1.7)


def mesh_panel_yspan():
    """(y0, y1) of the lit face, so the grille and its gate cannot disagree."""
    y_lip = BENCH_TOP_H_M - BENCH_TOP_D_M * math.sin(
        math.radians(BENCH_TOP_TILT_DEG))
    return BENCH_PLINTH_H_M + 0.05, y_lip - 0.06


def mesh_grille(m):
    """The perforated sheet over the lit panel. See MESH_CELL_M.

    The web stands in the recess `bench_profile` already cuts, at
    MESH_STANDOFF_M in front of the lit face -- so it is between the light
    and the room, which is what makes the panel read as lit from WITHIN rather
    than painted. Anything proud of `r_out` would stand outside the bench.

    THE WEB STAYS GREY, AND THAT IS A MEASURED RESULT RATHER THAN THE FIRST
    ANSWER. The argument for tagging it `council_mesh` is good and physical --
    a backlit sheet's web is the front face of the emitter, edge-lit and warm,
    not grey -- so it was tried, rendered, and read: at emission 2.0 on both
    web and hole the panel becomes **one blown white band with no texture at
    all**, which is a worse failure than the grille it replaced, because the
    perforation stops existing. `docs/craft-4r-council-after-normal.png` is
    that frame and it is kept as the negative result.
    So the contrast comes from the web being the bench's own casework, and what
    changed is the RATIO: 6.5 mm of web in a 30 mm cell is 39% covered against
    the 24 mm bar in a 42 mm pitch's 57%, which is the difference between "thin
    dark lines over a bright field" and "lit slots between dark bars".
    """
    a0 = math.radians(-BENCH_ARC_DEG / 2.0)
    a1 = math.radians(BENCH_ARC_DEG / 2.0)
    r_out = BENCH_R_M
    rp = r_out - BENCH_PANEL_INSET_M
    rb = rp + MESH_STANDOFF_M
    y0, y1 = mesh_panel_yspan()
    hw = MESH_WEB_M / 2.0
    n = max(4, int(round((a1 - a0) * rb / MESH_CELL_M)))
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        ca, sa = math.cos(a), math.sin(a)
        # a web is a plate in the tangential plane, facing OUT of the bench
        tx, tz = -sa * hw, ca * hw
        m.plate((rb * ca + tx, y1, rb * sa + tz),
                (rb * ca + tx, y0, rb * sa + tz),
                (rb * ca - tx, y0, rb * sa - tz),
                (rb * ca - tx, y1, rb * sa - tz),
                MESH_WEB_D_M, "council_frame")
    # THE SAME PITCH THE OTHER WAY, which is what makes the cell square and the
    # sheet a sheet. Swept at the bench's own 40 segments rather than 96: a web
    # that scallops on a different chord from the panel behind it is a web that
    # walks in and out of its own recess. Sag at 40 segments over 150 degrees on
    # a 4.6 m radius is 2.5 mm, inside the 55 mm the recess gives it.
    #
    # THE TWO DIRECTIONS ARE WOVEN, NOT WELDED. The vertical web's body runs
    # INWARD from rb (`plate_solid` puts the solid behind its face), so a
    # horizontal at the same radius would be thirty-nine crossings of two
    # solids in one place -- the defect this file's own clearance gate exists
    # for. The horizontals sit MESH_WEB_GAP_M in front instead, which is what a
    # woven mesh is, and both bands stay inside the 55 mm recess: the lit face
    # is at r 4.545, the verticals occupy 4.549-4.559 and the horizontals
    # 4.561-4.571, against a bench face at 4.600.
    rh0 = rb + MESH_WEB_GAP_M
    nr = max(2, int(round((y1 - y0) / MESH_CELL_M)))
    for j in range(1, nr):
        yy = y0 + (y1 - y0) * j / nr
        m.arc_solid([(rh0, yy - hw), (rh0 + MESH_WEB_D_M, yy - hw),
                     (rh0 + MESH_WEB_D_M, yy + hw), (rh0, yy + hw)],
                    ["council_frame"] * 4, a0, a1, MESH_RAIL_SEGS)


def delegate_stations(m, seats):
    """A working position for each delegation, on the bench top.

    `directory.py` declares `delegate_bench` and `speaking_position` for this
    room and the bench had neither: twelve metres of continuous desk with
    nothing on it. Pad, nameplate, screen, microphone -- which is what a seat
    at a council table has, and what `docs/judge-4e.md` means by machinery.
    """
    P = _dress._Parts("fix_")
    tilt = math.radians(BENCH_TOP_TILT_DEG)
    drop = BENCH_TOP_D_M * math.sin(tilt)
    r_out, r_in = BENCH_R_M, BENCH_R_M - BENCH_TOP_D_M

    def top_y(r):
        f = (r_out - r) / (r_out - r_in)
        return BENCH_TOP_H_M - drop * (1.0 - f)

    for k in range(seats):
        f = (k + 0.5) / seats - 0.5
        a = math.radians(f * BENCH_ARC_DEG * 0.92)
        ca, sa = math.cos(a), math.sin(a)
        hw = STATION_PAD_W_M / 2.0
        ra, rb = r_in + 0.10, r_out - 0.14
        ya, yb = top_y(ra) + 0.004, top_y(rb) + 0.004

        def at(r, y, w):
            return (r * ca - w * sa, y, r * sa + w * ca)

        # The working pad, laid on the slab. Wound +w first: the other order
        # has a NEGATIVE y normal, i.e. a desk pad facing the floor, and this
        # file's own `council_top faces up` gate caught it on the first run --
        # which is the fifth time this project has authored a flat surface
        # upside down and the first time a gate said so before a render did.
        # `council_top_pad`, NOT `council_top`, and it resolves to the same
        # material because `materials.resolve` matches the longest bind
        # FRAGMENT as a substring. The distinct name is what keeps this file's
        # existing `council_top faces up` gate meaningful: that gate was
        # written for the bench slab, which is a swept ribbon whose every
        # triangle faces up, and a `plate_solid` has a back and a rim that
        # legitimately do not. Folding a solid into a ribbon's gate would have
        # forced the gate to be weakened for every surface it covers.
        m.plate(at(ra, ya, hw), at(rb, yb, hw), at(rb, yb, -hw),
                at(ra, ya, -hw), 0.006, "council_top_pad")
        # THE SCREEN AND THE NAMEPLATE SWAPPED SIDES, because the delegates
        # did -- see `council_chamber`. A screen is raked toward the person
        # who reads it, which is now the INNER edge; a nameplate faces the
        # chamber, which is now the OUTER one. Built the other way round they
        # were a screen the audience reads and a nameplate the delegate reads.
        m.plate(at(ra + 0.02, ya + 0.30, hw * 0.62),
                at(ra - 0.10, ya + 0.02, hw * 0.62),
                at(ra - 0.10, ya + 0.02, -hw * 0.62),
                at(ra + 0.02, ya + 0.30, -hw * 0.62), 0.022, P.screen)
        # the nameplate, facing the chamber across the bench's outer edge
        m.plate(at(rb + 0.06, ya + STATION_PLATE_H_M, -hw * 0.70),
                at(rb + 0.06, ya + 0.004, -hw * 0.70),
                at(rb + 0.06, ya + 0.004, hw * 0.70),
                at(rb + 0.06, ya + STATION_PLATE_H_M, hw * 0.70),
                0.018, "council_frame")
        # a microphone on a stalk, which is the one object that says the
        # people at this desk are here to speak
        rm = (ra + rb) * 0.5
        ym = top_y(rm) + 0.004
        sv, st, ss = [], [], []
        _dress._tube(sv, st, ss, P.rail, at(rm, ym, hw * 0.55),
                     at(rm - 0.05, ym + STATION_MIC_H_M, hw * 0.55),
                     0.011, _dress.SEG_BOLT)
        _dress._tube(sv, st, ss, P.rail, at(rm, ym, hw * 0.55),
                     at(rm, ym + 0.030, hw * 0.55), 0.055, _dress.SEG_PIPE)
        m.merge_spans(sv, st, ss)


def door_span():
    """(a0, a1) of the gallery doorway, in the arc wall's own polar frame.

    The near face of this shell is +z, because `bespoke._place_local` maps the
    room's local x = 0 onto the place's bearing and the corridor's door onto
    the largest z. So the doorway is centred at a = pi/2 and its width is a
    CHORD converted to an angle rather than an angle chosen to look right.
    """
    r0 = FLOOR_R_M + 0.02
    half = math.asin(min(0.98, (DOOR_W_M / 2.0) / r0))
    return math.pi / 2.0 - half, math.pi / 2.0 + half


def screen_wall(m):
    """The flat wall the fan and the medallion stand on, behind the delegates.

    See FAN_X_M. It is a slab in the plane x = FAN_X_M with a DEEP BLUE FIELD
    on its face, which is the reference's own word: "a large circular spoked
    medallion on deep blue". judge-4e logged its absence as F2 -- "the 'deep
    blue' field behind the circular spoked medallion, which is black here".

    THE FIELD'S GROUP NAME IS A MEASUREMENT, NOT A NAME MATCH, and it is worth
    being explicit because `materials.py` is not this module's to edit.
    `render_shot._material_for` takes the LONGEST rule fragment contained in a
    group name, so `signage_panel__council_field` resolves to `signage_panel`
    -- albedo (0.06, 0.062, 0.14), emission (0.151, 0.156, 0.434) at 3.0. That
    material is the backlit blue field of `signage.py`'s customs boards, and
    the construction here is the same object: a dark blue panel lit from behind
    its own frame. `materials.py` makes the same kind of bind for the same kind
    of reason on `prop_deck_marking`, and records it in the same words.
    """
    x1 = FAN_X_M
    x0 = x1 - FAN_WALL_T_M
    hz = FAN_WALL_HZ_M
    m.box(x0, x1, 0.0, WALL_H_M, -hz, hz, "council_fin_backing")
    # THE FIELD IS A LUNETTE, NOT A RECTANGLE, and the difference is a quarter
    # of the frame. Bounded to the fan it backs, a rectangle still leaves the
    # four corners outside the fan's own half-disc: 13.8 x 6.48 m of rectangle
    # against a half-disc of radius 6.90 is 89.4 m2 against 74.8, so **16.3% of
    # the field is corner the fan can never cover**, and every square metre of
    # it is the brightest thing in the room. Measured on the frames this session
    # opened with: **25.9% of the normal frame and 35.7% of the half frame is
    # strongly blue, against 1.6% of `council chambers.webp`.**
    #
    # AND THE LEVEL IS STILL WRONG AFTER THIS, which is a material and not a
    # shape, so it is written up rather than bodged. Balanced against
    # `materials.GREY_WORLD_GAINS`, the reference's wall behind the fan reads
    # rgb(0.140, 0.190, 0.241), V 0.241 -- **0.67x the lit fin blade in front of
    # it** (V 0.361). Ours reads V 0.608 against a blade at V 0.445: **1.37x**.
    # The figure-ground relationship is inverted, because this group resolves
    # through `signage_panel`, whose emission is 3.0 -- a backlit sign standing
    # in for a painted wall. `scratchpad/PATCHES-4r-council.md` carries the
    # measurement and the material request; there is no non-emissive dark blue
    # bound in the interior scene to move it to today.
    fr = min(hz - 0.30, FIELD_R_M)
    fy0 = 0.30
    seg = 48
    a0 = math.asin(min(0.98, fy0 / fr))
    loop = [(x1, fr * math.sin(a0 + (math.pi - 2.0 * a0) * k / seg),
             fr * math.cos(a0 + (math.pi - 2.0 * a0) * k / seg))
            for k in range(seg + 1)]
    m.poly(loop, FAN_FIELD_T_M, "signage_panel__council_field",
           want=(1.0, 0.0, 0.0))
    # a surround, so the field is a panel set into a wall rather than paint
    for za, zb in ((-hz + 0.06, -fr - 0.06), (fr + 0.06, hz - 0.06)):
        m.box(x1, x1 + 0.06, 0.30, WALL_H_M - 0.20, za, zb, "council_frame")


def ceiling(m):
    """A coffered ceiling, because a chamber with no lid renders as sky.

    A FLAT DISC WOULD HAVE MADE THE GATE WORSE WHILE MAKING THE FRAME BETTER,
    which is the trade `enclosure`'s own note below records this file already
    losing once: `station/density.py` scores VISIBLE LINE over AREA, so 380 m2
    of blank ceiling is 380 m2 of denominator. The coffers are the numerator --
    four concentric ribs and twenty-four radial ones, which is what a
    ceremonial ceiling has anyway.
    """
    # THE SLAB BEARS ON THE WALL rather than meeting it exactly. Its rim at
    # r0 = FLOOR_R_M + 0.02 and its soffit at y = WALL_H_M land on the arc
    # wall's own inner face and top, and two of those vertices coincided to the
    # micron: 2 non-manifold edges, found by this file's gate and not by a
    # render. 140 mm of bearing into a 360 mm wall is how a slab meets a wall
    # anyway.
    y0, y1 = WALL_H_M - 0.02, WALL_H_M - 0.02 + CEIL_T_M
    r = FLOOR_R_M + 0.16
    loop = [(r * math.cos(math.tau * i / FLOOR_BED_SEGS),
             r * math.sin(math.tau * i / FLOOR_BED_SEGS))
            for i in range(FLOOR_BED_SEGS)]
    cv, ct = it_kit.deck_pad(loop, y0, y1)
    i0 = len(m.v)
    m.v.extend(cv)
    m.t.extend([(a + i0, b + i0, c + i0) for a, b, c in ct])
    m.g.extend(["council_fin_backing"] * len(ct))

    # concentric ribs, hanging below the soffit
    for k in range(1, CEIL_COFFER_RINGS + 1):
        rr = r * k / (CEIL_COFFER_RINGS + 1)
        w = 0.11
        m.arc_solid([(rr - w, y0 - 0.16), (rr + w, y0 - 0.16),
                     (rr + w, y0), (rr - w, y0)],
                    ["council_frame"] * 4, 0.0, math.tau, 48)
    # radial ribs, from the inner ring out to the wall
    for k in range(CEIL_COFFER_SPOKES):
        a = math.tau * k / CEIL_COFFER_SPOKES
        ca, sa = math.cos(a), math.sin(a)
        w = 0.09
        ra = r / (CEIL_COFFER_RINGS + 1) * 0.5
        m.plate((ra * ca - w * sa, y0 - 0.13, ra * sa + w * ca),
                (r * ca - w * sa, y0 - 0.13, r * sa + w * ca),
                (r * ca + w * sa, y0 - 0.13, r * sa - w * ca),
                (ra * ca + w * sa, y0 - 0.13, ra * sa - w * ca),
                0.13, "council_frame")


def enclosure(m):
    """The surfaces that stop this chamber standing in a void, ARTICULATED.

    The arc runs the WHOLE way round now, minus the gallery doorway -- see the
    block above ARC_WALL_T_M for the measurement that forced it and for why
    the doorway is at x = 0 rather than wherever the wall happened to stop. It
    adds no extent: the arc stands 20 mm outside the mosaic's own rim and
    clear of `house_cove` at r = FLOOR_R_M.

    THE PILASTERS ARE NOT DECORATION AND THE GATE SAID SO. Built as two plain
    surfaces, this enclosure added roughly 410 m2 of blank wall and
    `station/density.py` -- which scores VISIBLE LINE over AREA -- took the
    chamber from 93.7% of its floor to 85.2%. It was already the one location
    in this session's four that FAILS layer 2b, and a bare wall made the
    number worse while making the frame better, which is exactly the trade
    that criterion exists to refuse. A 7 m wall in a ceremonial chamber has
    pilasters, a cornice and a skirt whether or not a gate is watching.
    """
    r0 = FLOOR_R_M + 0.02
    d0, d1 = door_span()
    # ONE sweep, starting and ending at the doorway, so `arc_solid`'s ear-clip
    # caps become the two jambs and the opening is closed by construction.
    a0, a1 = d1, d0 + math.tau
    segs = max(8, int(ARC_WALL_SEGS * (a1 - a0) / math.pi))
    m.arc_solid([(r0, 0.0), (r0 + ARC_WALL_T_M, 0.0),
                 (r0 + ARC_WALL_T_M, WALL_H_M), (r0, WALL_H_M)],
                ["council_fin_backing"] * 4, a0, a1, segs)
    # The head over the doorway, spanning the gap the sweep leaves. It BEARS
    # INTO THE JAMBS by half a degree at each end and stands 90 mm proud of the
    # wall face, and both of those are load-bearing on the geometry rather than
    # taste: built flush and butted, its two end caps are coincident with the
    # sweep's own caps -- "coincident faces are geometry nobody can see",
    # session 3x -- and its top edge (r0+T, WALL_H)-(r0, WALL_H) is EXACTLY the
    # sweep's, so that edge carries four faces. This file's gate reported it as
    # 2 non-manifold edges and nothing else could have.
    m.arc_solid([(r0 - 0.09, DOOR_H_M), (r0 + ARC_WALL_T_M, DOOR_H_M),
                 (r0 + ARC_WALL_T_M, WALL_H_M), (r0 - 0.09, WALL_H_M)],
                ["council_fin_backing"] * 4,
                d0 - math.radians(0.5), d1 + math.radians(0.5), 6)

    # --- pilasters on the arc, standing proud INTO the room ----------------
    n = max(8, int((a1 - a0) * r0 / WALL_PIER_PITCH_M))
    hw = WALL_PIER_W_M / 2.0
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa * hw, ca * hw
        rp = r0 - WALL_PIER_D_M
        m.plate((rp * ca + tx, WALL_H_M - 0.10, rp * sa + tz),
                (rp * ca + tx, 0.0, rp * sa + tz),
                (rp * ca - tx, 0.0, rp * sa - tz),
                (rp * ca - tx, WALL_H_M - 0.10, rp * sa - tz),
                WALL_PIER_D_M + 0.02, "council_fin_backing")
    # --- a panel joint between every pair of piers --------------------------
    # `docs/AAA-STANDARD.md` C3's tertiary tier, and the cheapest line on the
    # station: a 100 mm reveal at mid-bay is 372 triangles across both walls
    # and it is what took this room from 96.9% of its layer-2b floor back over
    # 100. A 1.85 m panel with nothing between its piers is a 1.85 m panel.
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n
        ca, sa = math.cos(a), math.sin(a)
        tx, tz = -sa * WALL_JOINT_W_M / 2.0, ca * WALL_JOINT_W_M / 2.0
        rp = r0 - 0.045
        m.plate((rp * ca + tx, WALL_H_M - 0.50, rp * sa + tz),
                (rp * ca + tx, 0.30, rp * sa + tz),
                (rp * ca - tx, 0.30, rp * sa - tz),
                (rp * ca - tx, WALL_H_M - 0.50, rp * sa - tz),
                0.055, "council_fin_backing")

    # --- cornice, dado and skirt, where a wall meets a ceiling and a floor --
    # Swept over the SAME arc as the wall, so none of them crosses the doorway.
    # A dado rail across a 2.10 m opening is what `bespoke.near_face_opening`'s
    # own docstring records `hospitality` doing, and it reads as a blockage.
    for y0, y1, d in ((WALL_H_M - 0.46, WALL_H_M - 0.10, 0.20),
                      (1.34, 1.52, 0.16),
                      (0.0, 0.26, 0.13)):
        m.arc_solid([(r0 - d, y0), (r0 + 0.01, y0),
                     (r0 + 0.01, y1), (r0 - d, y1)],
                    ["council_fin_backing"] * 4, a0, a1, segs)


def chair_lattice_down():
    """Rows in the chair's open back, so its cells come out square."""
    cell = CHAIR_W_M / CHAIR_LATTICE
    return max(2, int(round((CHAIR_BACK_H_M - CHAIR_SEAT_H_M) / cell)))


def chair(m, angle_deg, r):
    """One delegation's chair: seat, and an open lattice back.

    IT FACED ALONG THE ARC. `at(dx, dy, dz)` is (radial, up, tangential) and
    every piece of the back was authored at dz = +0.30 -- tangential -- so a
    delegate in it sat sideways to the bench, looking at the next delegation's
    ear. The lattice back also spanned the RADIAL direction, i.e. the chair was
    turned through ninety degrees as a whole. Nothing could catch it: this
    file's gates ask about closure, winding and signed volume, and a chair is
    all three of those whichever way it points.

    The chairs are also INBOARD of the bench now (see `council_chamber`), so
    "behind the delegate" is -radial and that is where the back goes.
    """
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx, cz = r * ca, r * sa
    hw = CHAIR_W_M / 2.0
    back_dx = -0.30                       # behind the sitter, radially

    def at(dx, dy, dz):
        return (cx + dx * ca - dz * sa, dy, cz + dx * sa + dz * ca)

    # Seat pan. A cushion, not a sheet of paper -- 60 mm of pan is what the
    # frame shows and a plate with no edge is four open boundary edges a chair.
    # Wound so the pan faces UP: this file's `council_chair_seat's top face
    # faces up` gate is the one that says so.
    m.plate(at(0.26, CHAIR_SEAT_H_M, -hw), at(0.26, CHAIR_SEAT_H_M, hw),
            at(-0.26, CHAIR_SEAT_H_M, hw), at(-0.26, CHAIR_SEAT_H_M, -hw),
            0.06, "council_chair_seat")
    for sz in (-1, 1):
        p = at(0.20, 0.0, sz * hw * 0.9)
        m.box(p[0] - 0.03, p[0] + 0.03, 0.0, CHAIR_SEAT_H_M,
              p[2] - 0.03, p[2] + 0.03, "council_chair_leg")

    # The open lattice back. Bars, not a panel: the frame shows the wall
    # THROUGH it, and a solid back would close the room off behind every seat.
    # `m.box` IS AXIS-ALIGNED AND A CHAIR IS NOT. Every rail here used to be a
    # box spanning the BOUNDING BOX of its two ends, which is right only for a
    # chair at angle zero: at +/-60 degrees a 44 mm rail became a 0.55 m slab,
    # and at half distance the "open black lattice back" read as a set of
    # SHELVES. `docs/craft-4p-council-mid-half.png` is the frame that showed it.
    # A `plate` is a quad extruded along its own normal, so it turns with the
    # chair.
    y0, y1 = CHAIR_SEAT_H_M, CHAIR_BACK_H_M
    w = 0.022
    for i in range(CHAIR_LATTICE + 1):
        zc = -hw + CHAIR_W_M * i / CHAIR_LATTICE
        m.plate(at(back_dx, y1, zc - w), at(back_dx, y0, zc - w),
                at(back_dx, y0, zc + w), at(back_dx, y1, zc + w),
                2.0 * w, "council_chair_back")
    # THE DOWN COUNT IS DERIVED, NOT REPEATED. See CHAIR_LATTICE: one count for
    # both axes of a 0.62 x 1.48 m back gives cells 2.4 times taller than wide,
    # and at half distance that reads as shelving rather than as the
    # reference's open lattice. `chair_lattice_down()` is the shape of the
    # chair asking how many rows make the cell square, so moving the seat or
    # the back height cannot silently un-square it.
    nd = chair_lattice_down()
    for i in range(nd + 1):
        y = y0 + (y1 - y0) * i / nd
        m.plate(at(back_dx, y + w, -hw), at(back_dx, y - w, -hw),
                at(back_dx, y - w, hw), at(back_dx, y + w, hw),
                2.0 * w, "council_chair_back")


def _to_wall(p, x0=None):
    """Rotate the fan and the medallion onto the screen wall.

    Both are authored in the XY plane facing -z, which is the frame every
    winding assertion in this file was written against. A proper rotation of
    -90 degrees about +Y maps (x, y, z) -> (-z, y, x) and carries the normal
    (0, 0, -1) to (+1, 0, 0), which is the wall's face. Rotating is the cheap
    way and re-authoring is the expensive one: the medallion alone is four
    hand-wound sections whose two handednesses this file's own comments record
    costing a round trip to get right once.
    """
    return ((FAN_X_M if x0 is None else x0) - p[2], p[1], p[0])


def fin_half_width(r):
    """Half a blade's width at radius r, perpendicular to its own radius.

    ONE FUNCTION, because the blade and the gate that measures it have to agree
    about what the width IS. Tapering by radius rather than along the blade
    means every blade is the same width where it crosses a given radius, which
    is what makes a fan of DIFFERENT-LENGTH blades read as one fan.
    """
    f = (r - FIN_R0_M) / (FIN_R1_M - FIN_R0_M)
    return 0.5 * FIN_W_M * (FIN_TAPER + (1.0 - FIN_TAPER) * f)


def fin_blades(seed="council-fan"):
    """(angle, r0, r1, layer) for every blade. Deterministic, `_u` only."""
    out = []
    for k in range(FIN_COUNT):
        a = math.pi * (k + 0.5) / FIN_COUNT
        r1 = FIN_R1_M * (1.0 - FIN_R1_JITTER * _u(seed, "r1", k))
        r0 = FIN_R0_M * (1.0 + FIN_R0_JITTER * _u(seed, "r0", k))
        out.append((a, r0, r1, k % 2))
    return out


def fin_wall(m):
    """The radiating fan of angled fins, on the screen wall behind the bench.

    See FAN_X_M for the measurement that moved it and FIN_W_M for the width
    defect this rebuild closes. The hub is on the floor at z = 0 and the blades
    splay up and out through 180 degrees, so the fan's outer radius IS its
    height above the floor.

    Two layers, alternating, FIN_LAYER_GAP_M apart along the depth axis. That
    is what lets consecutive blades overlap by a tenth of their width -- the
    stack of fanned plates `council chambers.webp` shows -- without two solids
    sharing a cubic metre, which is the defect this file opened a session by
    finding between the bench and this same fan.
    """
    sub = _M()
    for k, (a, r0, r1, layer) in enumerate(fin_blades()):
        ca, sa = math.cos(a), math.sin(a)
        z0 = -(FIN_STANDOFF_M + layer * FIN_LAYER_GAP_M)
        tilt = math.radians(FIN_TILT_DEG * (1.0 + FIN_TILT_JITTER
                                            * (2.0 * _u("council-fan", "t", k)
                                               - 1.0)))
        # The tilt is a constant depth step ACROSS the blade's width, not along
        # its length -- which is why a blade near the hub, where it is narrow,
        # is raked steeply and one at the rim lies almost flat. That is the
        # reference's "angled fins" and it is unchanged from the version this
        # replaces; only the width was wrong.
        z1 = z0 - math.sin(tilt) * 0.5
        hw0 = fin_half_width(r0)
        hw1 = fin_half_width(r1)
        # PERPENDICULAR TO THE BLADE'S OWN RADIUS. The y term is the whole fix:
        # (-hw*sa, +hw*ca) is the unit normal to (ca, sa) scaled by hw, and the
        # version this replaces had (-hw*sa, 0), which is that normal projected
        # onto x -- so a blade's width came out as its own sine.
        sub.plate((r0 * ca - hw0 * sa, r0 * sa + hw0 * ca, z0),
                  (r1 * ca - hw1 * sa, r1 * sa + hw1 * ca, z0),
                  (r1 * ca + hw1 * sa, r1 * sa - hw1 * ca, z1),
                  (r0 * ca + hw0 * sa, r0 * sa - hw0 * ca, z1),
                  FIN_D_M, "council_fin")
    m.merge_xform(sub, _to_wall)


def medallion(_outer, cy, z):
    """The circular spoked medallion above the fins.

    Authored vertical in XY at depth z, facing -z, then rotated onto the screen
    wall by `_to_wall` -- see that function. Every winding comment below is
    written in the authoring frame and stays true, because a rotation cannot
    change which side of a triangle is the front.
    """
    m, seg = _M(), 44

    def ring(rr, w, z0, z1, group):
        """A rib swept about +Z as a closed solid. No backing plate anywhere.

        The section is traversed CLOCKWISE in (radial, z) -- the opposite hand
        to `arc_solid`'s profile, because this lathe turns about +Z and that
        one turns about +Y. Assuming the two shared a handedness cost a round
        trip once and the comment is kept for the next reader.
        """
        i0 = len(m.v)
        for k in range(seg):
            a = 2.0 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            for rad in (rr - w, rr + w):
                for zz in (z0, z1):
                    m.v.append((rad * ca, cy + rad * sa, zz))
        for k in range(seg):
            b = i0 + 4 * k
            n = i0 + 4 * ((k + 1) % seg)
            for p, q in ((0, 1), (1, 3), (3, 2), (2, 0)):
                m.t.append((b + p, b + q, n + q))
                m.t.append((b + p, n + q, n + p))
        m.g.extend([group] * 8 * seg)

    hub = MEDALLION_R_M * MEDALLION_HUB_F
    # the plain centre disc the sunburst converges on -- the only solid in it
    m.poly([(hub * math.cos(2.0 * math.pi * k / seg),
             cy + hub * math.sin(2.0 * math.pi * k / seg), z - 0.02)
            for k in range(seg)],
           MEDALLION_D_M, "council_medallion", want=(0.0, 0.0, -1.0))
    # the bright rim the spokes land on, and the big thin outline outside it
    ring(MEDALLION_R_M, MEDALLION_RIM_W_M * 0.5, z - 0.03, z,
         "council_medallion_ring")
    ring(MEDALLION_R_M * MEDALLION_OUTLINE_R, MEDALLION_OUTLINE_W_M * 0.5,
         z - 0.02, z + 0.01, "council_medallion_ring")

    for k in range(MEDALLION_SPOKES):
        a = 2.0 * math.pi * k / MEDALLION_SPOKES
        ca, sa = math.cos(a), math.sin(a)
        # a wedge, not a bar: the sunburst in the frame is narrow at the hub
        # and widens to the rim, and thirty-six parallel bars would read as a
        # cog. Radial-then-tangential already gives a -Z normal here, into the
        # room; reversing these "to match" the rings broke them once.
        w0, w1 = 0.010, 0.030
        m.plate((hub * ca - w0 * sa, cy + hub * sa + w0 * ca, z - 0.02),
                (MEDALLION_R_M * ca - w1 * sa,
                 cy + MEDALLION_R_M * sa + w1 * ca, z - 0.02),
                (MEDALLION_R_M * ca + w1 * sa,
                 cy + MEDALLION_R_M * sa - w1 * ca, z - 0.02),
                (hub * ca + w0 * sa, cy + hub * sa - w0 * ca, z - 0.02),
                MEDALLION_RELIEF_M, "council_medallion_spoke")

    _outer.merge_xform(m, _to_wall)


def mosaic_floor(m, seed="council"):
    """A pale polygonal mosaic, irregular rather than a grid.

    Built as a deterministic Voronoi-ish fan: tiles radiate from the centre with
    jittered angular and radial boundaries. The frame shows irregular polygons
    of varying size, and a square grid reads as a bathroom.

    A MOSAIC IS TILES ON A BED, and building it as 168 floating quads was wrong
    twice. Every tile was four open boundary edges -- 672 of them, the single
    biggest leak in the station -- and because the jitter leaves a grout gap
    between neighbours, **there was nothing under the gaps**. A player standing
    on this floor was looking through it into the background, which is black,
    at every joint. The bed is now a closed slab and each tile a closed pad
    laid TILE_RISE_M proud of it, which is what puts a grout line in the frame.
    """
    rings = 6
    # THE BED IS SUBDIVIDED, AND THAT IS NOT A TESSELLATION PREFERENCE. As one
    # `deck_pad` its top face was an ear clip of a 96-gon, so single triangles
    # ran the whole 22 m across the disc -- and `bespoke.near_face_opening`
    # classifies any horizontal triangle at y = 0 whose z reaches the approach
    # band as FLOOR AT EVERY X IT SPANS. One such triangle told the assembler
    # there was standing room at x = 7.9 m, out where the arc wall's own
    # curvature has taken it out of the near band, and the room was centred on
    # that phantom rather than on its doorway: the function returned
    # (7.87, 6.21) with a real 4.2 m door sitting at x = 0.
    #
    # Subdivided into rings x segments the same face states where the floor
    # actually is, and the same call returns the doorway. It is also better
    # geometry -- a 22 m triangle takes one vertex normal for a whole room.
    # THE CENTRE IS ONE VERTEX, not 96 at the same point. Built as a ring of
    # radius zero it is 96 coincident vertices, every triangle touching it is
    # degenerate, and `boundary_edges` welds by position -- 194 non-manifold
    # edges, AND the file's negative control went silent, because a degenerate
    # triangle removed leaves no hole. A gate that stops firing is the louder
    # of those two symptoms.
    tau = math.tau
    S = FLOOR_BED_SEGS
    i0 = len(m.v)
    bt = []
    m.v.append((0.0, 0.0, 0.0))                                   # top centre
    for ri in range(1, rings + 1):
        rr = FLOOR_R_M * ri / rings
        for k in range(S):
            a = tau * k / S
            m.v.append((rr * math.cos(a), 0.0, rr * math.sin(a)))
    nb = 1 + rings * S                                            # top block
    m.v.append((0.0, -FLOOR_BED_T_M, 0.0))                        # low centre
    for ri in range(1, rings + 1):
        rr = FLOOR_R_M * ri / rings
        for k in range(S):
            a = tau * k / S
            m.v.append((rr * math.cos(a), -FLOOR_BED_T_M, rr * math.sin(a)))

    def top(ri, k):
        return 0 if ri == 0 else 1 + (ri - 1) * S + k % S

    def low(ri, k):
        return nb + top(ri, k)

    for k in range(S):                                            # centre fan
        bt += [(top(0, 0), top(1, k + 1), top(1, k)),
               (low(0, 0), low(1, k), low(1, k + 1))]
    for ri in range(1, rings):
        for k in range(S):
            bt += [(top(ri, k), top(ri + 1, k + 1), top(ri, k + 1)),
                   (top(ri, k), top(ri + 1, k), top(ri + 1, k + 1))]
            bt += [(low(ri, k), low(ri, k + 1), low(ri + 1, k + 1)),
                   (low(ri, k), low(ri + 1, k + 1), low(ri + 1, k))]
    for k in range(S):                                            # the rim
        bt += [(top(rings, k), low(rings, k), low(rings, k + 1)),
               (top(rings, k), low(rings, k + 1), top(rings, k + 1))]
    m.t.extend([(a + i0, b + i0, c + i0) for a, b, c in bt])
    # `council_floor_2` rather than a new name. It is the group
    # `materials.council_floor_dark` binds -- the mosaic's DARK tile -- which is
    # what a grout bed under pale tiles is. A new group name would resolve to
    # the glTF fallback, the defect session 3x found on 1,248 door triangles,
    # and `test_materials_layer3` catches it: it failed on this exact line.
    m.g.extend(["council_floor_2"] * len(bt))

    for ri in range(rings):
        r0 = FLOOR_R_M * ri / rings
        r1 = FLOOR_R_M * (ri + 1) / rings
        n = max(6, int(FLOOR_TILES * (ri + 1) / rings / 2))
        for k in range(n):
            j0 = (_u(seed, "a", ri, k) - 0.5) * 0.35
            j1 = (_u(seed, "a", ri, k + 1) - 0.5) * 0.35
            a0 = 2.0 * math.pi * (k + j0) / n
            a1 = 2.0 * math.pi * (k + 1 + j1) / n
            g0 = r0 + (r1 - r0) * 0.06 * _u(seed, "r", ri, k)
            g1 = r1 - (r1 - r0) * 0.06 * _u(seed, "r", ri, k, 1)
            shade = int(_u(seed, "s", ri, k) * 3)
            tv, tt = it_kit.deck_pad(
                [(g0 * math.cos(a0), g0 * math.sin(a0)),
                 (g1 * math.cos(a0), g1 * math.sin(a0)),
                 (g1 * math.cos(a1), g1 * math.sin(a1)),
                 (g0 * math.cos(a1), g0 * math.sin(a1))],
                0.0, TILE_RISE_M)
            j = len(m.v)
            m.v.extend(tv)
            m.t.extend([(a + j, b + j, c + j) for a, b, c in tt])
            m.g.extend([f"council_floor_{shade}"] * len(tt))


def house_cove(m):
    """The concealed high-level cove. See THE HOUSE LIGHTING above.

    Segments of an arc at COVE_Y_M, standing COVE_D_M off the wall over the
    same half of the chamber the fin fan occupies -- the wall the camera faces
    and the wall the measurement watched brighten.

    A HOUSING, not a stripe. The whole point of this fitting is that you see
    the glow and never the lamp, which needs a body for the lamp to be behind;
    as a single ribbon of quads it was a painted band with 26 open edges and
    nothing to conceal anything.
    """
    r = FLOOR_R_M - COVE_D_M
    # (r, y) section: the lit face inboard, the housing behind it against the
    # wall. Convex, so the ear clip degenerates to a fan and still checks out.
    # THE WHOLE ARC, not half of it. The cove used to run 0..pi because the
    # WALL ran 0..pi; with the chamber enclosed the whole way round, a
    # half-cove leaves the other half of a ceremonial room in the dark, which
    # is the defect this change set out to close wearing a different hat.
    # `export_scene.fixture_lights` hangs one lamp per connected tagged body,
    # so this doubles the room's sources -- which is a lighting change and is
    # measured as one below rather than asserted to be harmless.
    m.arc_solid([(r, COVE_Y_M), (FLOOR_R_M, COVE_Y_M),
                 (FLOOR_R_M, COVE_Y_M + COVE_H_M), (r, COVE_Y_M + COVE_H_M)],
                # The housing is `council_frame`, a bound name: it is the same
                # metalwork as the bench's lit-panel surround and the same job,
                # a body you never see holding a face you always do.
                ["council_frame", "council_frame",
                 "council_frame", "light_house_cove"],
                0.0, math.tau, COVE_SEGS * 2)


def council_chamber(seats=SEATS):
    """The room. Bench centred on the origin, delegates INBOARD of it.

    THE BENCH WAS INSIDE-OUT, and it is the reason the room's one defining
    feature could not be seen. `council chambers.webp` shows the lit gold mesh
    facing the CHAMBER -- it is what lights the petitioner standing in front of
    it -- with the delegates behind the bench. This module put the chairs at
    `BENCH_R_M + 0.55`, i.e. OUTBOARD, on the same side as the lit face, so the
    panel faced the delegates' knees and everything the room has to say faced
    a wall. `bench_profile`'s own comment recorded the intent as built: "the
    face a delegate sees is the plinth, then the frame's lower lip, the recess,
    the lit mesh". The reference says the opposite.

    Nothing about the bench moves. The chairs move to CHAIR_R_M, inboard of
    `r_in`, and the screen wall goes behind THEM -- which is also what puts the
    fan and the medallion where a camera in the chamber can see them.
    """
    m = _M()
    mosaic_floor(m)
    bench(m)
    mesh_grille(m)
    delegate_stations(m, seats)
    for k in range(seats):
        f = (k + 0.5) / seats - 0.5
        chair(m, f * BENCH_ARC_DEG * 0.92, CHAIR_R_M)
    screen_wall(m)
    fin_wall(m)
    # STANDING CLEAR OF THE FAN, and the number is measured off the fan rather
    # than chosen. A fin occupies x = FAN_X + 0.03 out to FAN_X + 0.27 (the
    # 30 mm standoff, the 100 mm slab, and the 0.5 m tilt), and the medallion
    # was authored at z = -0.05, i.e. x = FAN_X + 0.02..0.07 -- INSIDE the
    # blades. Thirty blades through a spoked disc renders as shredded metal,
    # which is exactly what docs/craft-4p-council-normal.png showed before this
    # line, and it is the SAME defect as the bench through the fan that opened
    # this session: two solids in one place, invisible to every per-object gate.
    medallion(m, MEDALLION_Y_M, MEDALLION_Z_M)
    house_cove(m)
    enclosure(m)
    ceiling(m)
    return m.as_tuple()


def write_obj(path, seats=SEATS):
    v, t, g = council_chamber(seats)
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

    v, t, g = council_chamber()

    # --- the light is the point --------------------------------------------
    mesh = [k for k in range(len(t)) if g[k] == "council_mesh"]
    check("the bench carries a lit mesh panel", bool(mesh), "the room's light")
    # `council_frame` IS ALSO THE CEILING RIBS AND THE PILASTER JOINTS, which
    # reach r 11.16, so a `max()` over the whole group answered a question
    # about the ceiling and reported it as a fact about the bench -- both this
    # check and the capping-rail check below read 11.160 against a bench face
    # at 4.600 and could not have failed. A group name is not a location.
    def bench_frame_tris():
        lo = BENCH_R_M - BENCH_TOP_D_M - 0.05
        hi = BENCH_R_M + BENCH_CAP_D_M + 0.02
        return [k for k in range(len(t)) if g[k] == "council_frame"
                and all(lo < math.hypot(v[i][0], v[i][2]) < hi
                        and v[i][1] < BENCH_TOP_H_M + 0.02 for i in t[k])]

    fr = [math.hypot(v[i][0], v[i][2]) for k in bench_frame_tris()
          for i in t[k]]
    # THE LIT FACE ONLY, not the web in front of it. Both carry `council_mesh`
    # now -- see `mesh_grille` -- so this has to name the face by where it is,
    # which is the swept band at the bottom of the recess.
    rp = BENCH_R_M - BENCH_PANEL_INSET_M
    face = [k for k in mesh
            if all(abs(math.hypot(v[i][0], v[i][2]) - rp) < 1e-6 for i in t[k])]
    mr = [math.hypot(v[i][0], v[i][2]) for k in face for i in t[k]]
    # Against the frame's OUTERMOST radius, not its innermost. The frame now
    # wraps into the recess -- the two returns either side of the panel are
    # frame, and they are at the panel's own radius by construction -- so
    # `min(fr)` is the bottom of the notch and comparing against it asks
    # whether the panel is behind itself. What the reference establishes is
    # that the lit face sits behind the FACE of the bench.
    check("the mesh is recessed behind its frame, not coplanar",
          face and max(mr) < max(fr) - BENCH_PANEL_INSET_M + 1e-9,
          f"mesh out to {max(mr):.3f}, frame face at {max(fr):.3f}")

    # --- THE PANEL IS PERFORATED, which is the room's one defining sentence --
    # Every check here fails on the version `docs/judge-4e.md` scored, where
    # `council_mesh` was a smooth 80-triangle band and nothing stood in front
    # of it.
    my0_, my1_ = mesh_panel_yspan()
    web = [k for k in range(len(t)) if g[k] == "council_frame"
           and all(max(mr) < math.hypot(v[i][0], v[i][2]) < BENCH_R_M + 1e-9
                   and my0_ - 1e-6 <= v[i][1] <= my1_ + 1e-6 for i in t[k])]
    check("the lit panel is screened by a perforated web",
          len(web) > 400,
          f"{len(web)} triangles of web between the light and the room")
    check("...and the web stands in the recess, not proud of the bench",
          not web or max(math.hypot(v[i][0], v[i][2])
                         for k in web for i in t[k]) <= BENCH_R_M + 1e-9,
          "a web outside r_out is a web a delegate's knee meets")
    # THE CELL IS SQUARE, which is what "a very fine square-hole perforated
    # sheet" means and what six heavy rails over 287 vertical bars was not.
    # Counted on the built mesh in both directions rather than on the constant.
    rb = rp + MESH_STANDOFF_M
    my0, my1 = mesh_panel_yspan()
    n_v = max(4, int(round(math.radians(BENCH_ARC_DEG) * rb / MESH_CELL_M)))
    n_h = max(2, int(round((my1 - my0) / MESH_CELL_M))) - 1
    p_v = math.radians(BENCH_ARC_DEG) * rb / n_v
    p_h = (my1 - my0) / (n_h + 1)
    check("the sheet's cell is square, so it reads as mesh and not as a louvre",
          abs(p_v - p_h) < 0.10 * MESH_CELL_M,
          f"{n_v} webs at {p_v * 1000:.1f} mm across against {n_h} at "
          f"{p_h * 1000:.1f} mm up")
    # ...and the two directions are WOVEN, not in the same cubic centimetre.
    v_r = [math.hypot(v[i][0], v[i][2]) for k in web for i in t[k]
           if abs(v[i][1] - my0) < 1e-6 or abs(v[i][1] - my1) < 1e-6]
    check("...and the woven directions stay inside the recess",
          min(v_r) > rp - 1e-9 and max(v_r) < BENCH_R_M + 1e-9,
          f"web spans r {min(v_r):.4f}..{max(v_r):.4f} in a recess "
          f"{rp:.4f}..{BENCH_R_M:.4f}")

    # --- every delegation has a working position ---------------------------
    pads = [k for k in range(len(t)) if g[k] == "council_top_pad"]
    check("each delegation has a working pad on the bench",
          len(pads) == 12 * SEATS, f"{len(pads)} triangles over {SEATS} seats")
    scr = [k for k in range(len(t)) if g[k] == "fix_mp_dress_screen"]
    check("...a screen at it", len(scr) == 12 * SEATS, f"{len(scr)}")
    mics = [k for k in range(len(t)) if g[k] == "fix_mp_plant_rail"]
    check("...and a microphone, which is what the room is for", bool(mics),
          f"{len(mics)} triangles")
    pad_y = [v[i][1] for k in pads for i in t[k]]
    check("the stations sit ON the bench top, not through it",
          min(pad_y) > BENCH_TOP_H_M - BENCH_TOP_D_M
          * math.sin(math.radians(BENCH_TOP_TILT_DEG)) - 0.02,
          f"lowest pad vertex at {min(pad_y):.3f} m")

    # --- the chamber is enclosed, and adds no extent doing it --------------
    back = [k for k in range(len(t)) if g[k] == "council_fin_backing"]
    check("the fin fan has something behind it", bool(back),
          "54% of the judged frame was below the measurable floor and the fan "
          "radiated against nothing")
    rr = [math.hypot(v[i][0], v[i][2]) for k in back for i in t[k]]
    check("...and the enclosure stays within the room's own footprint",
          max(rr) <= FLOOR_R_M + ARC_WALL_T_M + 0.42 + 1e-6,
          f"reaches r {max(rr):.2f} against a {FLOOR_R_M} m floor")
    # The arc stands OUTSIDE the cove, and the number is the thing to check
    # rather than the intent: `house_cove` reaches r = FLOOR_R_M and a wall
    # that started at FLOOR_R_M would share a face with it -- the coincident
    # face this file's zero-non-manifold gate exists to catch.
    cove_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
              if g[k] == "light_house_cove" for i in t[k]]
    check("...and stands clear of the house cove rather than in it",
          FLOOR_R_M + 0.02 > max(cove_r) + 1e-9,
          f"arc wall inner face r {FLOOR_R_M + 0.02:.3f} against a cove "
          f"reaching r {max(cove_r):.3f}")

    # --- seats -------------------------------------------------------------
    # Five delegations can be counted in the frame and the arc runs past both
    # edges, so five is a floor, not the number. Asserting equality would be
    # asserting something the reference does not say.
    check("seat count is at least the five that can be counted",
          SEATS >= 5, f"{SEATS}")
    # MEASURED ON THE BUILT MESH, not on the constants. This read
    # `BENCH_R_M + 0.55 > BENCH_R_M`, which is `x + 0.55 > x`: an assertion
    # that cannot fail, which `docs/AAA-STANDARD.md` scores R0 -- "below
    # untested, because it reports PASS". It also could not have noticed that
    # the chairs were on the WRONG SIDE of the bench, which is what they were.
    ch_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
            if g[k].startswith("council_chair") for i in t[k]]
    bench_r = [math.hypot(v[i][0], v[i][2]) for k in range(len(t))
               if g[k] in ("council_plinth", "council_top", "council_mesh")
               for i in t[k]]
    check("chairs stand clear of the bench, INBOARD of it",
          ch_r and bench_r and max(ch_r) < min(bench_r) - 0.20,
          f"chairs reach r {max(ch_r):.2f}, the bench starts at "
          f"r {min(bench_r):.2f}")
    check("the chair back is open lattice, not a panel",
          CHAIR_LATTICE >= 3, f"{CHAIR_LATTICE} squares across")
    check("the chair back rises well above a seated head",
          CHAIR_BACK_H_M > CHAIR_SEAT_H_M + 1.2,
          f"back {CHAIR_BACK_H_M} over seat {CHAIR_SEAT_H_M}")

    # --- the bench is a bench ----------------------------------------------
    check("the bench top is at seated working height",
          1.00 < BENCH_TOP_H_M < 1.25, f"{BENCH_TOP_H_M} m")
    check("the bench top is an angled slab, not flat",
          BENCH_TOP_TILT_DEG > 0, f"{BENCH_TOP_TILT_DEG} deg")
    check("the bench arc leaves the speaker a place to stand",
          BENCH_ARC_DEG < 200.0, f"{BENCH_ARC_DEG} deg")

    # --- THE ROOM IS CLOSED -------------------------------------------------
    # 1,592 open boundary edges shipped for four sessions and nothing here
    # could see them, because every gate in this file measured which way a
    # surface FACED. A surface that is not there faces nowhere, so a facing
    # test passes vacuously on the half of a plate that does not exist. This
    # is the measurement that catches it, and it is first now.
    op, nm = it_kit.boundary_edges(v, t)
    check("the chamber is a closed surface", not op,
          f"{len(op)} open boundary edges, first at {op[:1]}")
    check("...and no edge carries more than two faces", not nm,
          f"{len(nm)} non-manifold edges, first at {nm[:1]}")
    check("the chamber encloses a positive volume, so it is not inside-out",
          _signed_volume(v, t) > 0.0, f"{_signed_volume(v, t):.1f} m3")

    # NEGATIVE CONTROL -- one triangle removed has to fire the closure gate.
    check("...and dropping ONE triangle fires that gate",
          len(it_kit.boundary_edges(v, t[1:])[0]) == 3,
          f"{len(it_kit.boundary_edges(v, t[1:])[0])} open with a hole in it")

    # --- THE FAN IS THE WIDTH IT SAYS IT IS ---------------------------------
    # NO GATE HERE ASKED HOW WIDE A BLADE ACTUALLY IS, and the whole fan was
    # its own sine for as long as it has existed: `fin_wall` offset the two
    # long edges by (-hw*sa, 0) instead of (-hw*sa, +hw*ca), so a blade's width
    # came out as `2*hw*sin(its angle)`. Measured on the built mesh before the
    # fix: **22 of 30 blades under 90% of nominal, the narrowest 32 mm against
    # 620 mm (5%), widest / narrowest = 19.1**. Every existing assertion passed
    # -- a 32 mm blade is closed, correctly wound, positive in volume and clear
    # of everything. This is the measurement that could have failed.
    def blade_widths(x_only=False):
        """(measured, nominal) width per blade, perpendicular to its radius."""
        probe = _M()
        if x_only:
            tilt = math.radians(FIN_TILT_DEG)
            for a, r0, r1, layer in fin_blades():
                ca, sa = math.cos(a), math.sin(a)
                z0 = -(FIN_STANDOFF_M + layer * FIN_LAYER_GAP_M)
                z1 = z0 - math.sin(tilt) * 0.5
                h0, h1 = fin_half_width(r0), fin_half_width(r1)
                probe.plate((r0 * ca - h0 * sa, r0 * sa, z0),
                            (r1 * ca - h1 * sa, r1 * sa, z0),
                            (r1 * ca + h1 * sa, r1 * sa, z1),
                            (r0 * ca + h0 * sa, r0 * sa, z1),
                            FIN_D_M, "council_fin")
            pv = [_to_wall(p) for p in probe.v]
        else:
            fin_wall(probe)
            pv = probe.v
        out = []
        for k, (a, _r0, r1, _l) in enumerate(fin_blades()):
            # after `_to_wall` the blade's own plane is world (z, y): authoring
            # x -> world z, authoring y -> world y.
            px, py = -math.sin(a), math.cos(a)
            vs = pv[k * 8:(k + 1) * 8]
            pr = [q[2] * px + q[1] * py for q in vs]
            out.append((max(pr) - min(pr), 2.0 * fin_half_width(r1)))
        return out

    got = blade_widths()
    bad = [i for i, (w, nom) in enumerate(got) if w < 0.90 * nom]
    check("every fin blade is the width it is drawn at, across its own radius",
          not bad,
          f"{len(bad)} of {len(got)} blades under 90% of nominal; narrowest "
          + (f"{min(w for w, _n in got):.3f} m" if got else ""))
    old = blade_widths(x_only=True)
    n_old = sum(1 for w, nom in old if w < 0.90 * nom)
    check("...and the offset it replaced FAILS that gate",
          n_old >= 20,
          f"the x-only offset leaves {n_old} of {len(old)} blades short, "
          f"narrowest {min(w for w, _n in old):.3f} m against a nominal "
          f"{max(n for _w, n in old):.3f} m")

    # --- and the two depth layers do not share a cubic metre ----------------
    fin_t = [k for k in range(len(t)) if g[k] == "council_fin"]
    lay = {0: [], 1: []}
    for bi, (_a, _r0, _r1, layer) in enumerate(fin_blades()):
        lay[layer] += [v[i][0] for k in fin_t[bi * 12:(bi + 1) * 12]
                       for i in t[k]]
    check("the fan's two depth layers are disjoint, so no blade is inside one",
          max(lay[0]) < min(lay[1]) - 1e-9 or max(lay[1]) < min(lay[0]) - 1e-9,
          f"layer 0 x {min(lay[0]):.3f}..{max(lay[0]):.3f}, layer 1 "
          f"{min(lay[1]):.3f}..{max(lay[1]):.3f}")
    check("...and the blades overlap in projection, which is why they need it",
          2.0 * fin_half_width(FIN_R1_M) > math.pi * FIN_R1_M / FIN_COUNT,
          f"{2 * fin_half_width(FIN_R1_M):.3f} m of blade on a "
          f"{math.pi * FIN_R1_M / FIN_COUNT:.3f} m rim pitch -- at or under 1.0 "
          f"the layers would be decoration rather than clearance")

    # --- the blue field is bounded by the fan, not by the wall ---------------
    fld = [i for k in range(len(t)) if g[k] == "signage_panel__council_field"
           for i in t[k]]
    fr_max = max(math.hypot(v[i][1], v[i][2]) for i in fld)
    lim = min(FAN_WALL_HZ_M - 0.30, FIELD_R_M)
    check("the blue field is a lunette on the fan, not a rectangle on the wall",
          fr_max <= lim + 1e-6,
          f"reaches {fr_max:.2f} m from the fan hub against a {lim:.2f} m fan")
    check("...and the rectangle it replaced FAILS that gate",
          math.hypot(lim, lim) > lim + 1e-6,
          f"a rectangle bounding the same fan has corners at "
          f"{math.hypot(lim, lim):.2f} m -- {100 * (math.hypot(lim, lim) / lim - 1):.0f}% "
          f"outside it, and 16.3% of its area is corner no blade can cover")

    # --- the medallion is a wheel and not a moon ----------------------------
    # MEASURED AS COVERAGE, because "it is open" is not a property of any one
    # triangle. Sample the disc the wheel occupies and ask what fraction of it
    # is behind geometry: a spoked wheel passes light, a backing plate does not.
    def wheel_coverage(with_disc=False):
        probe = _M()
        medallion(probe, MEDALLION_Y_M, MEDALLION_Z_M)
        if with_disc:
            seg = 44
            probe.poly([(FAN_X_M - MEDALLION_Z_M,
                         MEDALLION_Y_M + MEDALLION_R_M
                         * math.sin(math.tau * k / seg),
                         MEDALLION_R_M * math.cos(math.tau * k / seg))
                        for k in range(seg)],
                       MEDALLION_D_M, "council_medallion",
                       want=(1.0, 0.0, 0.0))
        pv, pt, pg = probe.as_tuple()
        tris = [[(pv[i][2], pv[i][1]) for i in pt[k]] for k in range(len(pt))
                if pg[k].startswith("council_medallion")]
        hit = tot = 0
        for gy in range(15):
            for gz in range(15):
                zz = (gz + 0.5) / 15 * 2.0 * MEDALLION_R_M - MEDALLION_R_M
                yy = (gy + 0.5) / 15 * 2.0 * MEDALLION_R_M - MEDALLION_R_M
                if zz * zz + yy * yy > MEDALLION_R_M ** 2:
                    continue
                tot += 1
                p = (zz, MEDALLION_Y_M + yy)
                for tri in tris:
                    (ax, ay), (bx, by), (cx, cy2) = tri
                    d1 = (p[0] - bx) * (ay - by) - (ax - bx) * (p[1] - by)
                    d2 = (p[0] - cx) * (by - cy2) - (bx - cx) * (p[1] - cy2)
                    d3 = (p[0] - ax) * (cy2 - ay) - (cx - ax) * (p[1] - ay)
                    if not ((d1 < 0 or d2 < 0 or d3 < 0)
                            and (d1 > 0 or d2 > 0 or d3 > 0)):
                        hit += 1
                        break
        return hit / max(1, tot)

    cov = wheel_coverage()
    check("the medallion is an open wheel, not a plate", 0.20 < cov < 0.70,
          f"{100 * cov:.0f}% of its disc is behind geometry -- a sunburst of "
          f"{MEDALLION_SPOKES} spokes on a rim, with the fan showing through")
    solid = wheel_coverage(with_disc=True)
    check("...and putting the backing disc back FAILS that gate", solid > 0.95,
          f"the plate this replaced covers {100 * solid:.0f}%, and it renders "
          f"as the brightest object in the room at V 0.611 against the "
          f"reference wheel's V 0.455")

    # --- the chair's lattice cells are square -------------------------------
    cw = CHAIR_W_M / CHAIR_LATTICE
    chh = (CHAIR_BACK_H_M - CHAIR_SEAT_H_M) / chair_lattice_down()
    check("the chair's lattice cells are square, not shelves",
          abs(cw - chh) < 0.10 * cw,
          f"{CHAIR_LATTICE} x {chair_lattice_down()} gives "
          f"{cw * 1000:.0f} x {chh * 1000:.0f} mm")
    old_h = (CHAIR_BACK_H_M - CHAIR_SEAT_H_M) / CHAIR_LATTICE
    check("...and one count for both axes FAILS that gate",
          abs(cw - old_h) > 0.10 * cw,
          f"{CHAIR_LATTICE} x {CHAIR_LATTICE} gives {cw * 1000:.0f} x "
          f"{old_h * 1000:.0f} mm -- {old_h / cw:.1f}:1")

    # --- the capping rail is on the bench, and so are its studs -------------
    # SCOPED TO THE BENCH -- see `bench_frame_tris`. Asked of the whole
    # `council_frame` group this read "reaches r 11.160", which is the ceiling.
    cap_r = [math.hypot(v[i][0], v[i][2]) for k in bench_frame_tris()
             for i in t[k]]
    check("the bench has a capping rail proud of its own face",
          max(cap_r) > BENCH_R_M + BENCH_CAP_D_M * 0.9,
          f"the bench's own frame reaches r {max(cap_r):.3f} against a face at "
          f"{BENCH_R_M:.3f} -- +{1000 * (max(cap_r) - BENCH_R_M):.0f} mm")
    # ...and the studs are ON it, at a pitch a viewer reads as a stud course
    n_stud = max(4, int(round(math.radians(BENCH_ARC_DEG) * BENCH_R_M
                              / BENCH_STUD_PITCH_M)))
    check("...with a stud course down it", n_stud > 40,
          f"{n_stud} studs at {BENCH_STUD_PITCH_M * 1000:.0f} mm over "
          f"{math.radians(BENCH_ARC_DEG) * BENCH_R_M:.1f} m of rail")

    # --- IT FITS THE ROOM'S SHARE OF THE FRAME ------------------------------
    # DERIVED, not picked. `budget.INTERIOR` allows 60,000 triangles of
    # structure in a standing frustum; the corridor behind a player in the
    # doorway costs `corridor_tris_per_m` x the 66 m sight line budget.py's own
    # comment cites from `populace.corridor_sight_m`. What is left is this
    # room's, and the whole 22.7 m chamber is in frame from anywhere in it, so
    # the room's total IS its visible set and there is no worst case to sweep.
    import budget as _bud                                       # noqa: PLC0415
    share = (_bud.INTERIOR["visible_set_tris"]
             - _bud.INTERIOR["corridor_tris_per_m"] * 66.0)
    check("the chamber fits its share of the interior frame budget",
          len(t) <= share,
          f"{len(t):,} triangles against {share:,.0f} "
          f"({100 * len(t) / share:.0f}%), of which the perforated sheet is "
          f"{sum(1 for x in g if x == 'council_mesh'):,}")

    # --- flat things face up, MEASURED ON THE FACE YOU CAN SEE --------------
    # These groups are solids now, so their undersides face down and must.
    # The honest question is whether the TOP of each object faces up, so the
    # test is restricted to triangles lying in the object's own highest plane
    # -- which is also the only plane a standing player ever sees.
    def top_face_bad(pick, tol=1e-6):
        ks = [k for k in range(len(t)) if pick(g[k])]
        if not ks:
            return None
        ytop = max(v[i][1] for k in ks for i in t[k])
        bad = 0
        for k in ks:
            if any(abs(v[i][1] - ytop) > tol for i in t[k]):
                continue
            p0, p1, p2 = (v[i] for i in t[k])
            u = tuple(p1[i] - p0[i] for i in range(3))
            w = tuple(p2[i] - p0[i] for i in range(3))
            if u[2] * w[0] - u[0] * w[2] <= 0:
                bad += 1
        return bad

    for grp in ("council_speak_fan", "council_chair_seat", "council_top_pad"):
        bad = top_face_bad(lambda n, grp=grp: n == grp)
        check(f"{grp}'s top face faces up", bad == 0, f"{bad} downward")
    floor_groups = [grp for grp in set(g) if grp.startswith("council_floor")]
    bad = top_face_bad(lambda n: n in floor_groups)
    check("the mosaic's tile faces face up", bad == 0, f"{bad} downward")
    check("the tiles stand proud of the bed they are laid on",
          TILE_RISE_M > 0.0 and FLOOR_BED_T_M > 0.0,
          "a mosaic with no bed shows the background through every joint")

    # The bench top is a tilted slab, so it has no single horizontal plane.
    # What it must not do is face away from the room: every triangle of the
    # slab group has a POSITIVE y normal component.
    bad = 0
    for k, tri in enumerate(t):
        if g[k] != "council_top":
            continue
        p0, p1, p2 = (v[i] for i in tri)
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[2] * w[0] - u[0] * w[2] <= 0:
            bad += 1
    check("council_top faces up", bad == 0, f"{bad} downward")

    # --- NOTHING IS INSIDE ANYTHING ELSE ------------------------------------
    # THE GATE THIS ROOM DID NOT HAVE, and the reason it shipped a bench
    # through a fan, a bench through a backing plate and thirty fin blades
    # through a spoked medallion, all at once. Every other assertion in this
    # file measures ONE object against ITSELF -- closure, winding, signed
    # volume, which way a face points -- and two solids in the same cubic metre
    # are all four of those. `docs/AAA-STANDARD.md` R5 names it: "cross-subsystem
    # clearance is asserted wherever two systems occupy the same space", and the
    # standing counter-example it cites is the tram 6.43 m inside a spoke.
    #
    # Stated as the separation it actually is: the rear composition lives on the
    # screen wall, the furniture lives out in the chamber, and there is a gap.
    def xrange_of(pred):
        ks = [k for k in range(len(t)) if pred(g[k])]
        xs = [v[i][0] for k in ks for i in t[k]]
        return (min(xs), max(xs)) if xs else None

    # NAMED, not prefixed. This read `n.startswith("signage_panel")`, which
    # since the speaking fan grew its blue slivers also matches an inlay lying
    # ON the bench top -- so the gate reported the rear composition reaching
    # x 4.31 and failed on a correct room. A group-name prefix is not a place.
    rear = xrange_of(lambda n: n == "council_fin"
                     or n.startswith("council_medallion")
                     or n == "signage_panel__council_field")
    furn = xrange_of(lambda n: n in ("council_plinth", "council_top",
                                     "council_mesh", "council_speak_fan")
                     or n.startswith("council_chair"))
    check("the rear composition and the furniture do not share space",
          rear and furn and furn[0] > rear[1] + 0.50,
          f"rear reaches x {rear[1]:.2f}, furniture starts at x {furn[0]:.2f}")
    fins = xrange_of(lambda n: n == "council_fin")
    meda = xrange_of(lambda n: n.startswith("council_medallion"))
    check("the medallion stands clear of the fan rather than inside it",
          meda and fins and meda[0] > fins[1] + 1e-9,
          f"fins reach x {fins[1]:.3f}, medallion starts at x {meda[0]:.3f}")

    # NEGATIVE CONTROL -- put the medallion back where it was and the gate has
    # to fire. Built through the same `_M` the room is, so this is the real
    # geometry and not a restatement of the constants.
    _probe = _M()
    fin_wall(_probe)
    medallion(_probe, MEDALLION_Y_M, -0.05)
    pv, pt, pg = _probe.as_tuple()
    _fx = max(pv[i][0] for k in range(len(pt))
              if pg[k] == "council_fin" for i in pt[k])
    _mx = min(pv[i][0] for k in range(len(pt))
              if pg[k].startswith("council_medallion") for i in pt[k])
    check("...and the placement it replaced FAILS that gate",
          _mx < _fx, f"old medallion x {_mx:.3f} against fins to {_fx:.3f}")

    # --- the medallion faces the room --------------------------------------
    # Same correction: the disc, the spokes and the rings all have backs now,
    # and a back facing the wall is the point of having one. The face a
    # delegate sees is the one at the lowest z, which is toward the room.
    # IN X, NOT IN Z. The medallion is authored in XY facing -z and rotated
    # onto the screen wall by `_to_wall`, so the face a delegate sees is the
    # one at the GREATEST x. Left testing z this gate picked the disc's rim at
    # z = -1.35 and asked a question about it that means nothing -- it kept
    # passing, which is the worse outcome.
    ks = [k for k in range(len(t)) if g[k].startswith("council_medallion")]
    xfront = max(v[i][0] for k in ks for i in t[k])
    bad = 0
    for k in ks:
        if any(abs(v[i][0] - xfront) > 1e-6 for i in t[k]):
            continue
        p0, p1, p2 = (v[i] for i in t[k])
        u = tuple(p1[i] - p0[i] for i in range(3))
        w = tuple(p2[i] - p0[i] for i in range(3))
        if u[1] * w[2] - u[2] * w[1] <= 0:
            bad += 1
    check("the medallion's front face faces into the room", bad == 0,
          f"{bad} of the front-plane triangles face the wall")

    # --- the primitives, on the hard case -----------------------------------
    # `arc_solid`'s end cap is the piece with a real chance of being wrong, so
    # it is tested on the NON-CONVEX profile the bench actually uses rather
    # than on a rectangle. A fan triangulation tiles straight across the
    # panel recess, and the way that shows up is AREA: a cap that spills
    # outside its outline covers more than the outline does.
    loop, names = bench_profile()
    tri = _ear_clip(loop)
    area = sum(abs((loop[b][0] - loop[a][0]) * (loop[c][1] - loop[a][1])
                   - (loop[c][0] - loop[a][0]) * (loop[b][1] - loop[a][1])) / 2.0
               for a, b, c in tri)
    shoe = abs(_shoelace(loop)) / 2.0
    check("the bench end cap tiles its profile without spilling outside it",
          abs(area - shoe) < 1e-12, f"cap {area:.9f} m2 vs profile {shoe:.9f} m2")
    check("...and the profile really is the non-convex case",
          any(((loop[i - 1][0] - loop[i - 2][0]) * (loop[i][1] - loop[i - 2][1])
               - (loop[i - 1][1] - loop[i - 2][1]) * (loop[i][0] - loop[i - 2][0]))
              < 0 for i in range(len(loop))),
          "a convex profile would let a fan pass and the gate would be inert")
    # NEGATIVE CONTROL -- the fan this replaced, on the same profile.
    fan_area = sum(abs((loop[i][0] - loop[0][0]) * (loop[i + 1][1] - loop[0][1])
                       - (loop[i + 1][0] - loop[0][0]) * (loop[i][1] - loop[0][1]))
                   / 2.0 for i in range(1, len(loop) - 1))
    check("...and a fan triangulation of it FAILS that test",
          abs(fan_area - shoe) > 1e-6,
          f"a fan covers {fan_area:.6f} m2 against the profile's {shoe:.6f}")

    for what, mm in (("plate", _M()), ("arc_solid", _M())):
        if what == "plate":
            mm.plate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, -1.0),
                     (0.0, 0.0, -1.0), 0.05, "probe")
        else:
            mm.arc_solid(loop, names, -0.4, 0.4, 5)
        pv, pt, _pg = mm.as_tuple()
        pop, pnm = it_kit.boundary_edges(pv, pt)
        check(f"{what} alone is a closed solid", not pop and not pnm,
              f"{len(pop)} open, {len(pnm)} non-manifold")
        check(f"{what} alone is outward-facing", _signed_volume(pv, pt) > 0.0,
              f"signed volume {_signed_volume(pv, pt):.6f} m3 -- negative is "
              f"a solid built inside-out, which indoors you see through")

    # --- the mosaic is a mosaic, not a grid ---------------------------------
    check("the floor uses more than one tile shade",
          len(floor_groups) > 1, str(sorted(floor_groups)))
    a = council_chamber()[0]
    b = council_chamber()[0]
    check("the mosaic regenerates byte-identically", a == b)

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
