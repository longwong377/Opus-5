#!/usr/bin/env python3
"""The station's material library, and the single source of truth for it.

WHY THIS FILE EXISTS
--------------------
Every surface in this project was flat colour. ADR 0002 chose "modular
polygonal geometry with PBR materials -- kit-bashed modules, trim sheets, decal
layers, procedural greebling" two ADRs ago and the material half of that
decision was never built. This is that half.

It is a *generator*, not a folder of hand-written resources, for the same
reason `station.yaml` is a schema and not a pile of OBJs: the project's core
discipline is that inside and outside come from one description so they cannot
disagree. Materials were on their way to becoming a second source of truth --
twelve `.tres` files under `godot/materials/`, plus twenty-eight more
`StandardMaterial3D` sub-resources living inside `godot/scenes/drum.tscn`, with
no mechanical relationship between them. `godot/scenes/drum.tscn` says so in
its own header comment: *"These are placeholders in one specific sense: they
are StandardMaterial3D sub-resources living in this scene rather than files
under godot/materials/, because that directory was being worked on
concurrently."* Both sets are now declared here and exported from here.

WHAT A "MEASURED" COLOUR MEANS HERE
-----------------------------------
Every albedo traces to a named frame and a named pixel region. None was chosen
by eye and none came from memory. Three things had to be dealt with to make
that meaningful, and each is a method, not an opinion:

1. **Every frame in the set carries a colour cast**, and it is not the same
   cast twice. `grey level 1.webp` is magenta (its green channel wants a 1.087
   gain to sit neutral); `exterior more.jpg` is blue; `Babylon_5_2-22_33a.jpg`
   is warm. Absolute hue off an uncorrected frame is worthless, which is what
   INV-010 already found the hard way. Colours here are quoted **after a
   grey-world balance** whose per-channel gains are recorded beside them, so a
   later session can re-run the correction rather than trust the number.

2. **A screencap pixel is radiance, not albedo.** What can be read off a frame
   is the *ratio* between two surfaces under the same light, and the hue once
   the cast is removed. The absolute level cannot be: there is no reflectance
   standard anywhere in the reference set. So the ladder of relative values is
   measured and the level is set by exactly one number, `ALBEDO_ANCHOR`, which
   is declared as an extrapolation and is the only place to change if the whole
   station reads too dark or too light.

3. **Saturation that falls as brightness rises is lighting, not paint.** A
   tinted surface holds roughly constant saturation from shadow to highlight,
   because the tint is multiplicative. An additive coloured lift -- ambient,
   rim, a gel on the key -- loses saturation as the underlying signal grows.
   That test is what says the hull is neutral and the blue is the environment,
   and it is re-derived here rather than inherited (see `PROVENANCE`).

THE SINGLE MOST IMPORTANT MEASUREMENT
-------------------------------------
Balanced and clustered, **every large surface in every station interior frame
in the reference set sits at saturation 0.02-0.16**. Council chambers 0.019 to
0.062. `grey level 1.webp` 0.020 to 0.107. War room 0.029 to 0.090. Zocalo
0.068. Casino 0.100 to 0.163.

The station's surfaces are near-neutral. All of the colour in every frame comes
from the lighting and from a small, saturated accent set. So this file builds a
near-neutral value ladder and puts the colour in three accent registers, and
anything that looks like a coloured wall in the reference is checked against a
differently-lit wall in the same frame before it is believed. That check has
already killed one: see `NEGATIVE_RESULTS`.

TEXTURES ARE GENERATED, NOT SHIPPED
-----------------------------------
No show asset may be redistributed, so every texel here is original work
computed from a hash. They are also *deterministic*: keyed with
`hashlib.blake2b`, never `random` and never `str.__hash__`, which is salted per
process and would produce a different station every run -- the mistake
`greeble.py` had to be rescued from.

The generated maps are trim sheets in the ADR 0002 sense: tileable, projected
triplanar because the glTF export carries POSITION and NORMAL only and there
are no UVs to place a decal against. What they carry is the high-frequency
detail the geometry cannot afford -- plate seams, edge wear, corner grime, weld
runs, deck studs -- at 0.06 triangles per square metre of drum.

RUN
---
    python3 station/materials.py                     # self-test
    python3 station/materials.py --export            # .tres + textures + rules
    python3 station/materials.py --budget            # VRAM and draw-call report
    python3 station/materials.py --sheet OUT.png     # every material as a chip
    python3 station/materials.py --surface M OUT.png # one trim sheet, lit

After `--export`, the textures need one importer pass, and the engine has to be
asked whether the files it was handed are the files it wanted:

    godot --headless --path godot --import
    godot --headless --path godot --script res://scripts/verify_materials.gd

**Run that second command.** It is not a formality. The first export of this
library wrote a six-line `#` banner above the `[gd_resource]` tag, and all 59
materials failed to load with "Parse Error: Expected '['" -- `.tres` takes `;`
as its comment character and wants the resource tag on line one. Every check in
this file passed on that build, because a `.tres` can be correct by every rule
this module knows and still be rejected by the only parser that matters.
"""
import argparse
import hashlib
import re
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIAL_DIR = os.path.join(ROOT, "godot", "materials")
TEXTURE_DIR = os.path.join(MATERIAL_DIR, "textures")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import interior as _it                                         # noqa: E402

# Imported, not restated. The window sheet's row pitch IS the deck pitch --
# CLAUDE.md hard rule 4, inside and outside from the same schema -- and a copy
# of the number here is exactly how the two would drift apart.
DECK_PITCH_M = _it.DECK_PITCH_M


# ---------------------------------------------------------------------------
# Habitat windows -- INV-036
# ---------------------------------------------------------------------------
# THE STANDING BLOCKING FINDING. `docs/aaa-scorecard.json`, `exterior_approach`
# round 1: "NO EMISSIVE WINDOWS ANYWHERE. A station housing 250,000 people
# renders completely unlit from within. It reads as a derelict, not a city."
# It is the first thing the owner's opening beat shows -- the station coming
# into view -- so it is the first thing layer 3 fixes.
#
# WHY A SHEET AND NOT GEOMETRY. At 1:1 the habitable shell carries on the order
# of 10^5 windows. Modelling them is a triangle budget this project does not
# have and does not need: a window seen from 3 km is a lit rectangle, and a
# window seen from 20 m is a lit rectangle with a frame. So it is a trim sheet
# with an emission mask, tiled over the habitable hull.
#
# CONSISTENCY BY CONSTRUCTION -- CLAUDE.md hard rule 4. The rows are NOT at a
# pitch chosen to look right. The sheet repeats over exactly
# `WINDOW_ROWS * interior.DECK_PITCH_M` metres and puts one row per deck, so a
# schema change that moves the decks moves the windows with them and the two
# cannot drift. `_selftest` asserts the sheet's metric repeat against
# `interior.DECK_PITCH_M` rather than against a number written here.
# BANDS, NOT FULL COVERAGE. The first bake glazed every deck of the habitat
# sections and the engine frame came back reading as rust-coloured static: at
# 900 m the drum is 500 m across, so a 2.4 m window pitch puts ~650 apertures
# round the circumference and they alias into noise long before they resolve
# into windows. That is not a texture-filtering problem to tune away -- it is
# the wrong building. The reference hull is mostly PLATE with window strips in
# it, so the sheet is now eight decks tall with two of them glazed.
# The radius the cylindrical mapping closes exactly at: the green sector's
# shell, imported rather than restated for the same reason DECK_PITCH_M is.
DRUM_REF_RADIUS_M = round(_it.sector_shell_radius(*_it.load(), "green"), 1)

WINDOW_ROWS = 8                    # decks per texture repeat
WINDOW_BANDS = (3, 4)              # which of those rows carry apertures
WINDOW_COLS = 12                   # apertures across the same repeat
WINDOW_REPEAT_M = WINDOW_ROWS * DECK_PITCH_M          # 14.4 m, and SQUARE
WINDOW_PITCH_M = WINDOW_REPEAT_M / WINDOW_COLS        # 2.40 m centres
WINDOW_W_M = 1.10                  # aperture width -- 46% glazed
WINDOW_H_M = 1.35                  # aperture height, in a 3.6 m deck
WINDOW_SILL_M = 1.05               # deck to the bottom of the aperture

# The repeat is square ON PURPOSE. `tres` writes one scalar uv1_scale as
# Vector3(s, s, s), so a sheet whose metric repeat differs between u and v
# would be stretched in one axis with nothing to catch it -- the windows would
# still be windows, just the wrong size, which is the class of error that
# survives a render. Deriving the column pitch from the row repeat keeps it
# square by construction instead of by coincidence.

# What fraction of apertures are lit at any moment. NOT 1.0, and this is the
# whole difference between a city and a lightbox: a uniformly lit hull reads as
# a display model. Derived rather than picked -- station time is a 24 h cycle
# (`npc/schedule.py`), roughly a third of the population is asleep, quarters are
# unoccupied while their resident is on shift, and plant and storage volumes
# have no windows lit at all. Two thirds is the daytime figure and it is what
# the approach shot is composed for.
WINDOW_LIT_P = 0.66
# Three registers, because a station's interiors are not one colour temperature.
# Warm practical dominates residential, cool blue reads as workspace, and the
# dim register is a room lit by light spilling in from another room -- which is
# most of what a real building's windows look like at night.
WINDOW_TEMPS = (
    ((1.000, 0.836, 0.640), 1.00, 0.52),    # warm practical, most quarters
    ((0.860, 0.910, 1.000), 1.15, 0.26),    # cool working light
    ((1.000, 0.620, 0.330), 0.55, 0.22),    # dim spill from an inner room
)



# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def h64(*keys):
    """Stable 64-bit hash of the key tuple.

    blake2b rather than `hash()`. Python salts `str.__hash__` per process, so a
    texture keyed on it would differ between two runs of the same commit --
    exactly the bug `greeble.py` was rescued from, and one that only shows up
    as an unreproducible diff long after it is introduced.
    """
    h = hashlib.blake2b(digest_size=8)
    for k in keys:
        h.update(repr(k).encode("utf-8"))
        h.update(b"\x1f")
    return int.from_bytes(h.digest(), "big")


def h01(*keys):
    """Deterministic float in [0, 1)."""
    return h64(*keys) / 2.0 ** 64


def hpick(seq, *keys):
    return seq[h64(*keys) % len(seq)]


# ---------------------------------------------------------------------------
# The measurement record
# ---------------------------------------------------------------------------
#
# Each entry: (what, frame, fractional region L T R B, authority, reading).
# "balanced" means after the grey-world gains recorded in GREY_WORLD_GAINS.
# Regions are fractions of image width/height so they survive a rescale.

GREY_WORLD_GAINS = {
    # frame -> (R, G, B) gains that put its mid-tone population at neutral.
    # Computed over every pixel with 0.04 < V < 0.95: clipped highlights are
    # (1,1,1) whatever the cast and would pull the estimate toward neutral.
    "07-sector-grey/grey level 1.webp": (0.970, 1.087, 0.953),
    "04-sector-red/zocalo.webp": (0.906, 1.185, 0.950),
    "04-sector-red/Casino.webp": (1.014, 1.071, 0.926),
    "05-sector-green/council chambers.webp": (0.998, 1.082, 0.932),
    "05-sector-green/conference aerea.webp": (1.122, 1.026, 0.882),
    "03-sector-blue/war room.webp": (1.088, 1.062, 0.877),
    "03-sector-blue/Babylon_5_2-22_35a.jpg": (0.913, 1.090, 1.013),
    "03-sector-blue/Babylon_5_2-22_33a.jpg": (0.881, 1.055, 1.091),
    "09-garden-core-and-transit/garden.png": (0.884, 0.994, 1.159),
    # Added session 3k with the layer-3 interior pass. Each was recomputed
    # here, from the frame, before being written down -- and the method's own
    # control is that recomputing the three entries above reproduces them to
    # 0.000. See `_selftest`, which does that check on every run so the table
    # cannot silently drift from the frames it describes.
    "03-sector-blue/dock.webp": (0.968, 1.027, 1.006),
    "10-interiors-generic-kit/central corridor.webp": (1.045, 1.086, 0.891),
    "04-sector-red/more zocalo.png": (0.936, 1.137, 0.951),
    "10-interiors-generic-kit/more hallway.jpg": (1.120, 1.198, 0.786),
    "10-interiors-generic-kit/more hallways.jpg": (0.793, 1.146, 1.154),
}

PROVENANCE = """
HULL, EXTERIOR
  The hull is neutral and the blue is the environment. Re-derived here from a
  frame INV-010 did not use, and it is the cleanest instance of the test in the
  whole reference set. `01-station-exterior/welcome to babylon 5.webp`
  clusters at H 239-240 throughout, which looks like a decisive blue -- until
  the clusters are read as numbers:

      rgb(0.121, 0.124, 0.335)   B - R = 0.214
      rgb(0.159, 0.164, 0.440)   B - R = 0.281
      rgb(0.291, 0.291, 0.535)   B - R = 0.244
      rgb(0.412, 0.415, 0.683)   B - R = 0.271
      rgb(0.536, 0.538, 0.804)   B - R = 0.268

  R equals G to three decimals at every level, and B *minus* R is constant
  across a 4.4x range of R while B *over* R runs 2.77 -> 1.50. A blue albedo
  holds the ratio; an additive blue holds the difference. This is additive.
  (This frame is the "Welcome to Babylon 5" customs signage panel, so what is
  being measured is a backlit blue panel with neutral lettering -- the same
  arithmetic gives both the panel emission and the letter colour.)

  `01-station-exterior/exterior more.jpg`, drum region of the side view
  (0.50, 0.43)-(0.72, 0.58), gives the same signature as a saturation ramp:

      V 0.10-0.20  mean S 0.396   rgb 0.103, 0.100, 0.155
      V 0.20-0.30  mean S 0.311   rgb 0.191, 0.185, 0.243
      V 0.30-0.40  mean S 0.203   rgb 0.286, 0.286, 0.340
      V 0.40-0.55  mean S 0.150   rgb 0.390, 0.403, 0.454
      V 0.55-0.75  mean S 0.056   rgb 0.580, 0.580, 0.604
      V 0.75-1.00  mean S 0.038   rgb 0.827, 0.827, 0.852

  Saturation falls monotonically 0.396 -> 0.038 while R and G stay equal. So
  the hull albedo is neutral, and `hull_exterior`'s slight warm bias -- which
  INV-010 records as invented, not measured -- is retained only because
  `01-station-exterior/Cobra Bays with starfurries.webp` (authority 1, the hull
  under a real key rather than a production render) has *every* cluster at
  H 11-19 deg, S 0.29-0.44. That is a warm key light, and the warm bias is the
  cheap stand-in for it in scenes that do not have one.

  Plate-scale variation is measured, not invented. Along one constant latitude
  of the drum in the side view, sampled across 281 px at three heights, value
  varies with sd 0.037 to 0.095 about a mean of 0.28 to 0.37 -- i.e. roughly
  +/-13% per plate. `PLATE_VALUE_JITTER` is set from that.

INTERIOR CORRIDOR KIT -- `07-sector-grey/grey level 1.webp`, authority 1
  Balanced (gains 0.970 / 1.087 / 0.953), median over each region:

      pilaster vertical light strip  (0.183,0.214)-(0.197,0.366)  V 0.609  S 0.024
      rail band nosing, proud        (0.019,0.470)-(0.134,0.492)  V 0.340  S 0.035
      pilaster bullnose face         (0.188,0.394)-(0.206,0.731)  V 0.301  S 0.050
      wall plate course, clean       (0.019,0.236)-(0.125,0.293)  V 0.295  S 0.046
      dado panel                     (0.019,0.563)-(0.134,0.731)  V 0.247  S 0.108
      amber sign plaque              (0.084,0.309)-(0.111,0.360)  V 0.247  S 0.184
      soffit / ceiling               (0.019,0.020)-(0.300,0.090)  V 0.162  S 0.123
      rail band reveal, in shadow    (0.019,0.501)-(0.134,0.526)  V 0.160  S 0.205
      skirt                          (0.019,0.771)-(0.134,0.793)  V 0.141  S 0.257
      deck tile field                (0.300,0.750)-(0.500,0.950)  V 0.471  S 0.077

  The four *lit* elements -- plate course, pilaster, rail nosing, dado -- span
  0.247 to 0.340, a spread of +/-15% about their mean. The corridor is
  essentially ONE albedo. Everything that reads as contrast in that frame is
  geometry, shadow reveal or a light fitting. Painting the contrast in would be
  the wrong fix and would fight the lighting.

DRUM GROUND -- `03-sector-blue/Babylon_5_2-22_33a.jpg`, authority 1
  Raw medians over identified parcels:

      tilled parcel   (0.054,0.692)-(0.122,0.809)  rgb 0.498, 0.404, 0.376
      crop field      (0.203,0.622)-(0.270,0.716)  rgb 0.471, 0.396, 0.365
      woodland mass   (0.108,0.270)-(0.189,0.388)  rgb 0.353, 0.325, 0.286

  Balanced (0.881 / 1.055 / 1.091) the woodland becomes H 122 S 0.093 and the
  parcels H 36 S 0.066 -- a *desaturated* patchwork separated mostly by value,
  not by hue. `09-garden-core-and-transit/garden.png` shows the same ground
  from standing height and its lawn balances to H 114 S 0.330 V 0.651, a
  properly saturated green, while that frame's view of the drum's far side
  overhead reads H 41 S 0.295.

  So near ground is saturated and far ground is washed warm-khaki, in the same
  volume. That is aerial perspective across 500 m of pressurised air, and it
  belongs to the fog term in the scene, NOT to the albedo. Land-use albedos
  here are the *near-field* values. Desaturating them to match the distant
  frame would double-count the haze and make the Garden look dead underfoot.

TRAM SALOON -- `03-sector-blue/Babylon_5_2-22_35a.jpg`, authority 1
  Balanced (0.913 / 1.090 / 1.013), clustered over the saloon half of the frame
  (0.30, 0.35)-(1.0, 1.0), 8 clusters, share first:

      17.6%  rgb(0.349, 0.354, 0.406)  H 235  S 0.139   wall panel, mid
      15.5%  rgb(0.272, 0.119, 0.112)  H   2  S 0.588   bench cushion, shadowed
      14.6%  rgb(0.102, 0.059, 0.065)  H 351  S 0.421   cushion, deepest shadow
      12.0%  rgb(0.264, 0.257, 0.294)  H 251  S 0.126   wall panel, shadowed
      10.4%  rgb(0.375, 0.237, 0.225)  H   5  S 0.401   cushion, lit
       9.0%  rgb(0.486, 0.486, 0.546)  H 240  S 0.110   wall panel, lit
       6.3%  rgb(0.491, 0.383, 0.392)  H 355  S 0.220   cushion highlight

  Two populations and nothing between them: a near-neutral cool-grey shell
  (S 0.11-0.14) and a red soft-goods set (S 0.22-0.59 at H 351-5). The amber
  panels low on the saloon wall are a third, small population that the cluster
  pass does not separate because they are under 2% of the frame.

SIGNAGE -- `01-station-exterior/welcome to babylon 5.webp`, authority 1
  Clustered inside the sign panel (0.02, 0.32)-(0.52, 0.95):

      48.4%  rgb(0.151, 0.156, 0.434)   field
      14.4%  rgb(0.275, 0.277, 0.557)   letter edge
      16.5%  rgb(0.409, 0.410, 0.691)   letter core
      20.6%  rgb(0.532, 0.532, 0.810)   letter, blown

  B - R = 0.283 / 0.282 / 0.282 / 0.278 across the whole set. One constant blue
  emission with neutral lettering added on top -- which is exactly how a
  backlit panel is built, and how this material is built.

EXTERIOR HAZARD MARKING -- authority 1
  `01-station-exterior/Cobra Bays with starfurries.webp` shows yellow-and-black
  diagonal chevrons on the bay lip, and `03-sector-blue/dock.webp` shows the
  same marking painted on the docking-bay deck along with a large red circular
  bay number. Both are diagonal stripe patterns at roughly 45 deg, and both are
  the only high-chroma paint anywhere on the exterior. This is why
  `hazard_chevron` exists as a trim sheet rather than as a flat colour.
"""

ALBEDO_ANCHOR_CORROBORATION = """
THE ANCHOR SURVIVES SIX FRAMES IT WAS NOT DERIVED FROM.

`ALBEDO_ANCHOR = 0.46` is the single number that sets the station's absolute
interior brightness: every interior albedo in this library is a ratio against
it, so if it is wrong, all of them are wrong together and no relative check can
see it. It was derived from ONE measurement -- `grey level 1.webp`'s wall plate
course at balanced V 0.295 -- and a one-source constant carrying that much
weight is exactly the kind of thing this project is supposed to distrust.

Session 3k's layer-3 pass measured lit structural wall surfaces in six further
frames, none of which the anchor came from, using the same grey-world balance:

    central corridor.webp  wall panel (0.600,0.300)-(0.720,0.420)   lit 0.365
    central corridor.webp  walkway fascia                           lit 0.390
    dock.webp              bay wall (0.200,0.290)-(0.330,0.400)     lit 0.418
    dock.webp              stepped ledge                            lit 0.421
    war room.webp          arch face (0.040,0.020)-(0.130,0.120)    lit 0.446
    council chambers.webp  wall blade, dominant cluster             lit 0.494
    more zocalo.png        lit structure, dominant cluster          lit 0.511

Mean 0.435 against an anchor of 0.46 -- a 5% difference across seven readings
spanning six frames, four sectors and three lighting set-ups. Three of the
seven were recomputed independently when this note was written (0.365, 0.418,
0.446, reproduced exactly).

That is corroboration, not proof: every reading uses the same balance method,
so a systematic error in the method would move all of them together. What it
does rule out is the failure that mattered -- that the anchor was a fluke of
one frame's exposure.
"""

NEGATIVE_RESULTS = """
THE OCHRE DADO DOES NOT EXIST.
  In `grey level 1.webp` the lower half of the LEFT wall balances warm --
  dado H 60 S 0.108, skirt H 53 S 0.257, rail reveal H 48 S 0.205 -- against a
  plate course above it at H 204 S 0.046. Read on its own that is a two-tone
  wall: neutral plates over a warm ochre dado, and it is a good-looking scheme
  that I was one edit from encoding.

  The RIGHT wall of the same frame, at the same height, is not warm:

      right wall low band   (0.594,0.545)-(0.700,0.640)   H 159  S 0.037
      right wall low band   (0.845,0.500)-(0.930,0.620)   H 195  S 0.122
      right wall high plate (0.845,0.100)-(0.930,0.280)   H 195  S 0.120

  The warmth is on the wall that has warm downlights low on it and absent from
  the wall that does not. It is the practicals, not the paint. The corridor
  gets one neutral albedo and the warmth goes in the lights.

  This is the same shape as the mistake INV-010 records for the exterior --
  "the hull is neutral, and the blue was the lighting" -- and the same shape as
  the two red accents that were nearly conflated in session 2n. Three times now
  the answer has been that a colour in a frame belonged to the lighting. The
  cheap test is: find the same material somewhere else in the same frame under
  a different light, and see whether the colour follows the material or the
  light.

THE SAME DECK PLATE IS TWO COLOURS IN ONE FRAME.
  `more hallways.jpg`, balanced. One continuous deck plate reads

      under the warm backlit panels    H 36-37   S 0.59-0.65
      under the cool tubes             H 179-200 S 0.12-0.25

  One surface, two lights, two colours, 160 degrees apart. `more hallway.jpg`
  repeats it on a wall: H 17-27 S 0.09-0.25 on its warm side, H 198 S 0.27 on
  its cool side. Both are LIGHTING references and neither is an albedo
  reference. This is the ochre-dado test above, run twice more and failed
  twice more, which is now five times this project has found a colour in a
  frame that belonged to the light.

`04-sector-red/Doug's Dugout.webp` MUST NOT BE MEASURED FOR ALBEDO AT ALL.
  Its grey-world gains are (0.723, 1.280, 1.197) and the balanced frame is
  nonsense: over mid-tones (0.15 < V < 0.85) the balanced saturation has a
  median of 0.370 and a p90 of 0.870, and a THIRD of those pixels sit above
  S 0.5. The anchor frame `grey level 1.webp`, measured the same way, gives a
  median of 0.105, a p90 of 0.194, and nothing at all above S 0.5.

  The cause is in the room, not in the method. `hospitality.py` records the
  Dugout as lit entirely by isolated pendant cones with near-zero ambient
  between them -- the lighting design IS the room -- so its mid-tone population
  is not a neutral population and grey-world has nothing to work with. A wall
  measured there comes back at S 1.000.

  Recorded so nobody re-mines it. The frame remains authority-1 for LAYOUT and
  for the lighting design itself, which is what it was used for.

THE DRUM GROUND IS NOT DESATURATED.
  See PROVENANCE. The distant reading is haze; the albedo is the near reading.

`view.jpg` IS `Babylon_5_2-22_34b.jpg`.
  Byte-identical, md5 e2bf2216d53aa9ba89342267db3f92f6, filed in two folders.
  It is counted twice in the reference index's live-file total. No material
  cites it twice as independent corroboration; noted so that nobody does.
"""


# ---------------------------------------------------------------------------
# The one number that sets the absolute level
# ---------------------------------------------------------------------------

# EXTRAPOLATED. A screencap gives the RATIO between two surfaces under the same
# light and nothing about the level, because there is no reflectance standard
# in any held frame. This maps the balanced value of `grey level 1.webp`'s lit
# wall plate course (0.295) onto an albedo, and every other measured interior
# value scales with it.
#
# 0.46 sRGB is a light-mid architectural grey -- the top of the range painted
# panel work usually occupies, chosen because the set is plainly a light one
# and because the existing reviewed `hull_interior.tres` sits at mean 0.493.
# Overturned by: any frame containing a known-reflectance object, or an engine
# render at the scene's real light levels that comes out visibly too dark or
# too bright at a correct exposure.
ALBEDO_ANCHOR = 0.46
_ANCHOR_MEASURED = 0.295
INTERIOR_GAIN = ALBEDO_ANCHOR / _ANCHOR_MEASURED     # 1.559

# Measured on the exterior sheet: sd 0.037-0.095 of value about means of
# 0.28-0.37 along one constant latitude, i.e. roughly +/-13% per plate.
PLATE_VALUE_JITTER = 0.13


def lit(v):
    """Balanced screen value of a LIT surface -> albedo, via the one anchor."""
    return round(min(1.0, v * INTERIOR_GAIN), 4)


# ---------------------------------------------------------------------------
# Material declaration
# ---------------------------------------------------------------------------

class Material:
    """One PBR surface, its bindings, and where its colour came from.

    `binds` are OBJ/glTF group-name fragments. Resolution is substring match,
    longest fragment wins -- identical to `godot/scripts/render_shot.gd`, which
    matches by substring rather than prefix because the glTF importer decorates
    node names (`cargo_module` comes back as `BabylonStation_cargo_module`).
    Two materials must never claim the same fragment; `_selftest` asserts it.
    """

    __slots__ = ("name", "title", "albedo", "roughness", "metallic", "specular",
                 "emission", "emission_energy", "emission_texture",
                 "shader", "shader_params", "texture", "uv_scale",
                 "triplanar", "normal_scale", "binds", "scenes", "source",
                 "note", "extrapolated")

    def __init__(self, name, title, albedo, roughness, metallic=0.0,
                 specular=0.5, emission=None, emission_energy=0.0,
                 emission_texture=None, shader=None, shader_params=None,
                 texture=None, uv_scale=1.0, triplanar=True, normal_scale=1.0,
                 binds=(), scenes=(), source="", note="", extrapolated=""):
        self.name = name
        self.title = title
        self.albedo = tuple(round(c, 4) for c in albedo)
        self.roughness = roughness
        self.metallic = metallic
        self.specular = specular
        self.emission = tuple(emission) if emission else None
        self.emission_energy = emission_energy
        self.emission_texture = emission_texture
        self.shader = shader
        self.shader_params = dict(shader_params or {})
        self.texture = texture
        self.uv_scale = uv_scale
        self.triplanar = triplanar
        self.normal_scale = normal_scale
        self.binds = tuple(binds)
        self.scenes = tuple(scenes)
        self.source = source
        self.note = note
        self.extrapolated = extrapolated

    def __repr__(self):
        return f"<Material {self.name}>"

    def luminance(self):
        r, g, b = self.albedo
        return 0.2126 * r + 0.7152 * g + 0.0722 * b


# Accent registers. Measured across every balanced interior frame in the set;
# these are the only saturations above 0.20 that survive the cast correction.
#
#   warm practical  H 12-35   S 0.21-0.46   Casino, Zocalo, rotunda, conference
#   cyan / teal     H 187-199 S 0.16-0.67   conference aerea, more zocalo, Casino
#   cool blue       H 216-235 S 0.18-0.88   command and control, rotunda screens
#   maroon red      H 351-5   S 0.22-0.59   tram soft goods, Zocalo handrail
#
# Sector identity lives HERE and in the lights, not in the wall albedo: no
# sector's structural surfaces measure differently from any other sector's.
ACCENTS = {
    "warm_practical": (1.000, 0.612, 0.353),   # H 24, from Casino H21 S0.457 lifted to source level
    "cyan_neon": (0.444, 1.000, 0.939),        # measured, Zocalo neon glyph, balanced
    "cool_blue": (0.240, 0.320, 1.000),        # H 228, C&C brightest cluster H228 S0.880
    "maroon": (0.491, 0.383, 0.392),           # 35a cushion highlight, balanced
    "hazard_yellow": (0.900, 0.720, 0.060),    # dock.webp deck chevrons
}

SECTOR_ACCENT = {
    # Which register dominates each sector's reference frames. Advisory for
    # lighting and signage; no sector changes the structural albedo.
    "blue": "cool_blue",        # command and control: 31.8% + 17.2% + 2.7% of frame at H 222-228
    "red": "warm_practical",    # Casino H 21 S 0.457; Zocalo cyan is signage, not ambience
    "green": "cyan_neon",       # conference aerea H 196-199 S 0.65-0.67, 22.7% of frame
    "grey": "warm_practical",   # grey level 1: warm downlights low on the wall
    "brown": "warm_practical",  # sleeping-in-light-05: orange window light, one frame only
    "yellow": "hazard_yellow",  # NO REFERENCE. Extrapolated from the sector being engineering.
}


# ---------------------------------------------------------------------------
# The library
# ---------------------------------------------------------------------------

def _build():
    M = []
    a = M.append

    # ---- exterior hull --------------------------------------------------
    a(Material(
        "hull_exterior", "Hull Exterior — plated neutral grey, weathered",
        # Neutral by measurement (see PROVENANCE), with the warm bias INV-010
        # invented kept at 6% so scenes without a warm key still read like the
        # authority-1 frames, which are H 11-19 throughout.
        albedo=(0.600, 0.582, 0.564), roughness=0.72, metallic=0.34,
        specular=0.45, texture="hull_plate", uv_scale=1.0 / 48.0,
        normal_scale=1.3,
        binds=(), scenes=("exterior",),
        source="exterior more.jpg drum side view; Cobra Bays with starfurries.webp",
        note="Fallback for the exterior scene: most of the model is hull.",
        extrapolated="the 6% warm bias; the 48 m texture repeat"))

    a(Material(
        "habitat_windows", "Habitat Windows — lit apertures on the pressurised hull",
        # THE FIX FOR THE STANDING BLOCKING FINDING. See the INV-036 block near
        # the top of this file for why this is a sheet rather than geometry and
        # why its row pitch is `interior.DECK_PITCH_M` rather than a number.
        #
        # `albedo` is dark glass, not hull: an unlit window must read as a hole
        # in a lit hull, and it is the unlit ones that make the lit ones mean
        # something. `emission` is white because the MAP carries the colour --
        # three registers, per aperture -- and emission_operator MULTIPLY lets
        # it through unchanged.
        # ALBEDO IS THE HULL'S, NOT A DARKER ONE, and the sheet's plate value
        # is TEX_MEAN so the two multiply back to the hull's 0.60. The first
        # version set 0.18 here and 0.60 in the sheet, which rendered the plate
        # between windows at 0.15 -- FOUR TIMES DARKER than the hull it is
        # continuous with -- so the habitat sections read as a different
        # material bolted on rather than as the same hull with windows in it.
        # Logged as a minor against exterior_approach round 2 and measured
        # rather than eyeballed: 0.72 * 0.8333 = 0.60, hull_exterior exactly.
        albedo=(0.600, 0.582, 0.564), roughness=0.58, metallic=0.34,
        specular=0.45, texture="hull_window", uv_scale=1.0 / WINDOW_REPEAT_M,
        normal_scale=1.0,
        emission=(1.0, 1.0, 1.0), emission_energy=3.4,
        emission_texture="hull_window",
        # Cylindrical about the spin axis. See godot/materials/hull_window.gdshader
        # -- world triplanar blends two grids across the drum's barrel and draws
        # them as a crosshatch, which is what round 2 logged as a major.
        shader="hull_window",
        shader_params={
            "albedo_color": (0.8333, 0.8083, 0.7833),
            "emission_color": (1.0, 1.0, 1.0),
            "emission_energy": 3.4,
            "metallic": 0.34, "roughness": 0.58, "specular": 0.45,
            "normal_scale": 1.0,
            "repeat_m": WINDOW_REPEAT_M,
            "ref_radius_m": DRUM_REF_RADIUS_M,
            "dark_block_fraction": 0.28,
            "block_repeats": 5.0,
        },
        binds=("green_section", "red_section", "aft_hull_block",
               "habitat_cylinder", "observation_rotunda"),
        scenes=("exterior",),
        source="No frame in the reference set shows the hull lit from within at "
               "range; the apertures are extrapolated. What IS sourced is that "
               "these sections are the pressurised, inhabited ones -- "
               "schema/station.yaml hull sections, and directory.py's sector "
               "z-extents.",
        note="Bound to the pressurised sections only. The truss spine, the "
             "reactor and the deflector spike have nobody in them and stay "
             "dark, which is what makes the lit part read as inhabited.",
        extrapolated="every aperture dimension, the 66% lit fraction and the "
                     "three colour registers -- INV-036"))

    a(Material(
        "structural_truss", "Structural Truss — unpainted spine and framework",
        albedo=(0.260, 0.255, 0.248), roughness=0.46, metallic=0.28,
        specular=0.45, texture="truss_steel", uv_scale=1.0 / 12.0,
        normal_scale=1.0,
        binds=("main_truss_spine", "reactor_spine", "explosive_disconnect_neck",
               "comms_grid_pylon"),
        scenes=("exterior",),
        source="exterior more.jpg truss spine, V 0.204 against hull 0.44 — the darkest thing on the station",
        note="INV-010's relative reading; only differences within that sheet are trustworthy."))

    a(Material(
        "radiator", "Radiator — deep blue high-emissivity blade coating",
        albedo=(0.126, 0.188, 0.320), roughness=0.78, metallic=0.05,
        specular=0.30,
        binds=("reactor_cooling_fin",), scenes=("exterior",),
        source="exterior more.jpg blade panel, H 221, S 0.43-0.78, V 0.29 — the most saturated element on the sheet",
        note="Untextured on purpose: a radiator blade is a coated panel, not plate."))

    a(Material(
        "cargo_module", "Cargo Module — red-brown container skin",
        albedo=(0.340, 0.222, 0.205), roughness=0.68, metallic=0.15,
        specular=0.40, texture="hull_plate", uv_scale=1.0 / 12.0,
        normal_scale=0.8,
        binds=("cargo_module",), scenes=("exterior",),
        source="exterior more.jpg dorsal boxes, H 351-5, S 0.25-0.47, V 0.29"))

    a(Material(
        "swept_array", "Swept Array — collector and sensor panel faces",
        albedo=(0.360, 0.365, 0.375), roughness=0.66, metallic=0.25,
        specular=0.35,
        binds=("heat_exchange_solar_array", "forward_swept_array",
               "space_traffic_prox_array"),
        scenes=("exterior",),
        source="exterior more.jpg top-view swept blades, V 0.34, near-neutral — darker than hull, not white"))

    a(Material(
        "hull_banding_red", "Hull Banding Red — exterior structural marking",
        albedo=(0.480, 0.090, 0.100), roughness=0.50, metallic=0.10,
        specular=0.45,
        binds=(), scenes=("exterior",),
        source="exterior more.jpg forward waist, H 357, S 0.81, V 0.34-0.54",
        note=("Deliberately UNBOUND. INV-010's adversarial verification found "
              "the source shows a hairline longitudinal rail, and binding it to "
              "`cobra_bay` painted 28 saturated red blocks where the sheet has "
              "a thin line. The fix is a banding strip in components.py, which "
              "is not this file's to make. Leaving it bound would be shipping a "
              "known-wrong render.")))

    a(Material(
        "hazard_chevron", "Hazard Chevron — yellow-and-black diagonal marking",
        albedo=(0.900, 0.720, 0.060), roughness=0.62, metallic=0.05,
        specular=0.40, texture="hazard_chevron", uv_scale=1.0 / 3.0,
        normal_scale=0.5,
        binds=("hazard_stripe", "bay_lip"), scenes=("exterior", "drum"),
        source="Cobra Bays with starfurries.webp bay lip; dock.webp deck marking",
        note=("The only high-chroma paint on the exterior in any authority-1 "
              "frame. No geometry carries the `hazard_stripe` group yet; the "
              "material exists so the group has somewhere to land."),
        extrapolated="the 3 m stripe pitch — the frames show the pattern, not its scale"))

    a(Material(
        "marker_light_white", "Marker Light White — section-joint beacon",
        albedo=(0.080, 0.080, 0.085), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(1.000, 0.950, 0.880), emission_energy=1.3,
        binds=("greeble_nav_light",), scenes=("exterior",),
        source="Cobra Bays with starfurries.webp — red and white marker lights on the columns"))

    a(Material(
        "marker_light_red", "Marker Light Red — hazard beacon",
        albedo=(0.100, 0.050, 0.040), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(1.000, 0.300, 0.120), emission_energy=2.1,
        binds=("greeble_hazard_light",), scenes=("exterior",),
        source="Cobra Bays with starfurries.webp — 96% of the frame's saturated-bright pixels are H 15-20"))

    a(Material(
        "greeble_fitting", "Greeble Fitting — hatches, vents, blisters, cleats",
        # Greebles used to inherit the hull fallback, so 70,778 triangles of
        # bolted-on machinery read as the same paint as the pressure hull. On
        # the sheet the fittings are consistently darker and less warm than the
        # plating they sit on: they are unpainted or differently painted metal.
        albedo=(0.310, 0.306, 0.300), roughness=0.55, metallic=0.42,
        specular=0.50, texture="truss_steel", uv_scale=1.0 / 6.0,
        normal_scale=1.0,
        binds=("greeble_panel", "greeble_vent", "greeble_hatch",
               "greeble_blister", "greeble_antenna", "greeble_cleat",
               "greeble_conduit"),
        scenes=("exterior",),
        source="exterior more.jpg dorsal fittings, V 0.20-0.31 against hull plating 0.28-0.37"))

    # ---- interior corridor kit -----------------------------------------
    #
    # ONE albedo, four rungs. The measured spread across the lit elements of
    # `grey level 1.webp` is +/-15%; anything wider than that is invention.
    wall = lit(0.295)          # 0.4600
    a(Material(
        "kit_wall_plate", "Corridor Wall Plate — the station's base surface",
        albedo=(wall, wall, wall), roughness=0.56, metallic=0.10,
        specular=0.35, texture="wall_plate", uv_scale=1.0 / 4.0,
        normal_scale=1.0,
        binds=("structure", "wall_panel", "wall_assembly", "bulkhead"),
        scenes=("interior",),
        source="grey level 1.webp wall plate course (0.019,0.236)-(0.125,0.293), balanced V 0.295 S 0.046",
        note="Neutral. See NEGATIVE_RESULTS for why it is not warm."))

    a(Material(
        "kit_pilaster", "Corridor Pilaster — bullnose jamb column",
        albedo=(lit(0.301),) * 3, roughness=0.42, metallic=0.12,
        specular=0.40,
        binds=("pilaster", "portal_frame", "door_frame"), scenes=("interior",),
        source="grey level 1.webp pilaster face (0.188,0.394)-(0.206,0.731), balanced V 0.301 S 0.050",
        note=("Smoother than the wall, not lighter: the bullnose reads as a "
              "different object in the frame because it catches a specular "
              "roll-off along its curve, and at 1.02x the wall's value it "
              "cannot be doing it with albedo.")))

    a(Material(
        "kit_rail_band", "Corridor Rail Band — the hip-height nosing",
        albedo=(lit(0.340),) * 3, roughness=0.38, metallic=0.20,
        specular=0.45,
        binds=("rail_band", "handrail"), scenes=("interior",),
        source="grey level 1.webp rail nosing (0.019,0.470)-(0.134,0.492), balanced V 0.340 S 0.035"))

    a(Material(
        "kit_reveal", "Corridor Reveal — the shadow gap under the rail band",
        albedo=(0.140, 0.140, 0.145), roughness=0.85, metallic=0.05,
        specular=0.25,
        binds=("reveal", "wall_reveal", "soffit", "ceiling_slab"),
        scenes=("interior",),
        source="grey level 1.webp rail reveal (0.019,0.501)-(0.134,0.526), balanced V 0.160",
        note=("Painted dark, not merely shadowed. Cannot be separated from "
              "shadow in a single frame; assigned dark because a deep reveal is "
              "the strongest horizontal in the wall build-up and modelling it "
              "as pure occlusion would cost geometry to get a result paint "
              "gives for nothing."),
        extrapolated="that the reveal is painted rather than only shadowed"))

    a(Material(
        "kit_skirt", "Corridor Skirt — kick zone at the deck",
        albedo=(0.340, 0.336, 0.330), roughness=0.68, metallic=0.10,
        specular=0.35, texture="wall_plate", uv_scale=1.0 / 2.0,
        normal_scale=0.7,
        binds=("skirt",), scenes=("interior",),
        source="grey level 1.webp skirt (0.019,0.771)-(0.134,0.793), balanced V 0.141",
        note="Measured region sits in the warm downlight's falloff, so its 0.141 is part shadow.",
        extrapolated=("lifted from the measured 0.141 to 0.34 — 0.74x the wall "
                      "rather than 0.48x. A skirt in the same paint system is "
                      "not half the albedo of the wall above it; what the frame "
                      "shows at that height is the light running out.")))

    a(Material(
        "kit_deck", "Corridor Deck — studded anti-slip plate",
        albedo=(0.400, 0.398, 0.395), roughness=0.34, metallic=0.30,
        specular=0.55, texture="deck_stud", uv_scale=1.0 / 1.21,
        normal_scale=1.6,
        binds=("deck_grid", "deck_panel"), scenes=("interior",),
        source="grey level 1.webp deck field (0.300,0.750)-(0.500,0.950), balanced V 0.471 S 0.077",
        note=("The deck measures 1.6x the wall's value, and it is not 1.6x the "
              "albedo. Magnified, the floor is a regular grid of raised studs "
              "and every stud carries a specular hit; the brightness is the "
              "highlights, so the material reproduces it with roughness 0.34 "
              "and metallic 0.30 and an albedo slightly BELOW the wall's, which "
              "is what a floor normally is. `uv_scale` is the kit's own "
              "0.605 m tile pitch doubled, so one texture repeat is two tiles.")))

    a(Material(
        "kit_deck_plate", "Deck Plate — large flat plates with recessed seams",
        albedo=(0.360, 0.356, 0.348), roughness=0.62, metallic=0.20,
        specular=0.40, texture="deck_plate", uv_scale=1.0 / 6.0,
        normal_scale=1.2,
        binds=("deck_plate", "concourse_deck"), scenes=("interior",),
        source="sleeping-in-light-05.jpg — the Downbelow deck is wide flat plates with recessed seams, not studs",
        note="A second deck register. The corridor is studded; open concourse is plated."))

    a(Material(
        "light_deck_channel", "Deck Light Channel — recessed floor strip",
        albedo=(0.090, 0.095, 0.105), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(0.860, 0.910, 1.000), emission_energy=3.5,
        binds=("light_deck_channel",), scenes=("interior",),
        source="sleeping-in-light-05.jpg deck strip; central corridor.webp. Blows to white; lower half reads (0.83, 0.83, 0.87) cool-white",
        note="An emissive is not a light. Forward+ needs a real OmniLight3D beside this one."))

    a(Material(
        "light_pilaster_strip", "Pilaster Light Strip — segmented vertical tube",
        albedo=(0.850, 0.860, 0.880), roughness=0.28, metallic=0.0,
        specular=0.20, emission=(0.880, 0.930, 1.000), emission_energy=6.0,
        binds=("light_pilaster_strip",), scenes=("interior",),
        source="grey level 1.webp strip (0.183,0.214)-(0.197,0.366), balanced V 0.609 S 0.024 — the brightest large feature and still nearly neutral",
        note="Eleven discrete cells in the frame, not a continuous tube. The segmentation is geometry."))

    a(Material(
        "light_portal_head", "Portal Head Light — over the doorway",
        albedo=(0.840, 0.850, 0.870), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(0.900, 0.940, 1.000), emission_energy=5.0,
        binds=("light_portal_head",), scenes=("interior",),
        source="grey level 1.webp far portal head — the strip above the aperture blows to V 0.988"))

    a(Material(
        "light_downlight", "Wall Downlight — the warm practical, low on the wall",
        albedo=(0.300, 0.240, 0.190), roughness=0.35, metallic=0.0,
        specular=0.25, emission=(1.000, 0.680, 0.400), emission_energy=4.0,
        binds=("light_downlight",), scenes=("interior",),
        source="grey level 1.webp lens (0.440,0.505)-(0.465,0.545), balanced H 27 S 0.238; clips to V 0.988 at core",
        note=("This fitting is why the left wall of that frame balances warm and "
              "the right wall does not. It is the whole warm register of the "
              "station's interior in one object.")))

    a(Material(
        "accent_warning", "Accent Warning — red-orange hazard paint",
        albedo=(0.700, 0.321, 0.225), roughness=0.42, metallic=0.0,
        specular=0.50,
        binds=("accent_warning", "hazard_frame"), scenes=("interior",),
        source="more zocalo.png, Cobra Bays…, sleeping-in-light-05.jpg — H 12-20, S ~0.68, mean rgb (0.667, 0.306, 0.215)",
        note="Distinct register from hull_banding_red (H 357, S 0.81). Two reds, measured separately."))

    a(Material(
        "emissive_signage", "Signage Neon — cyan",
        albedo=(0.050, 0.090, 0.100), roughness=0.25, metallic=0.0,
        specular=0.20, emission=ACCENTS["cyan_neon"], emission_energy=4.5,
        binds=("signage_neon",), scenes=("interior",),
        source="zocalo.webp neon glyph, balanced (0.444, 1.000, 0.939); Zocalo neon signage in background.jpg"))

    a(Material(
        "signage_panel", "Signage Panel — backlit blue with neutral lettering",
        albedo=(0.060, 0.062, 0.140), roughness=0.30, metallic=0.0,
        specular=0.25, emission=(0.151, 0.156, 0.434), emission_energy=3.0,
        texture="signage_panel", uv_scale=1.0 / 1.6, triplanar=False,
        binds=("signage_panel",), scenes=("interior",),
        source="welcome to babylon 5.webp panel field (0.02,0.32)-(0.52,0.95): field rgb(0.151,0.156,0.434), B-R constant at 0.28 through the letters",
        note=("The one non-triplanar material. A sign has an orientation and a "
              "reading direction; projecting it three ways would mirror the "
              "lettering on half the faces. Whatever mesh carries this group "
              "must ship UVs.")))

    # ---- drum: ground ----------------------------------------------------
    # Promoted from godot/scenes/drum.tscn, whose header invites exactly this
    # ("Promoting one to a .tres is a two-line change"). The sampled values are
    # that agent's, from 34b and 33a, and are kept verbatim rather than
    # re-derived: two independent samples of the same frame that differ would
    # be worse than one, and re-measuring would silently discard their work.
    ground = [
        ("ground_arable", "Arable — sampled 34b field green",
         (0.510, 0.518, 0.367), 0.95, ("ground_arable",),
         "34b agricultural half"),
        ("ground_arable_0", "Arable crop 0 — darker green",
         (0.440, 0.490, 0.310), 0.95, ("ground_arable_0",), "34b field variant"),
        ("ground_arable_1", "Arable crop 1 — pale stubble",
         (0.575, 0.565, 0.400), 0.96, ("ground_arable_1",), "34b field variant"),
        ("ground_arable_2", "Arable crop 2 — olive",
         (0.470, 0.475, 0.375), 0.95, ("ground_arable_2",), "34b field variant"),
        ("ground_arable_3", "Arable crop 3 — yellow-green",
         (0.545, 0.520, 0.335), 0.95, ("ground_arable_3",), "34b field variant"),
        ("ground_hedge", "Hedge — field boundary, darkest green in frame",
         (0.225, 0.275, 0.170), 0.98, ("ground_hedge",), "34b hedgerow"),
        ("ground_parkland", "Parkland — designed park at ground level",
         (0.345, 0.425, 0.260), 0.95, ("ground_parkland",), "29a"),
        ("ground_settlement", "Settlement — built-up ground",
         (0.500, 0.495, 0.475), 0.85, ("ground_settlement",), "33a grey-brown blocks"),
        ("ground_shore", "Shore — dry margin",
         (0.500, 0.465, 0.375), 0.92, ("ground_shore",), "34b water margin"),
        ("ground_road", "Road and avenue — pale carriageways, not asphalt",
         (0.360, 0.355, 0.335), 0.90, ("ground_road", "ground_avenue"),
         "33a road corridor (0.311,0.341)-(0.332,0.575)"),
    ]
    for nm, title, alb, rough, binds, src in ground:
        a(Material(nm, title, albedo=alb, roughness=rough, metallic=0.0,
                   specular=0.35, binds=binds, scenes=("drum",),
                   source=f"godot/scenes/drum.tscn, sampled from {src}",
                   note="Near-field albedo. The distant wash is fog, not paint — see PROVENANCE."))

    a(Material(
        "ground_water", "Water — the only smooth surface in the drum",
        albedo=(0.055, 0.115, 0.145), roughness=0.06, metallic=0.0,
        specular=0.85,
        binds=("ground_water",), scenes=("drum",),
        source="godot/scenes/drum.tscn; garden.png water balances H 195 S 0.476",
        note=("Roughness 0.06 is the point of it. In a drum the water reflects "
              "the ground overhead, which is the single most legible statement "
              "the geometry can make about where you are standing.")))

    # ---- drum: structure -------------------------------------------------
    a(Material(
        "drum_structure", "Structural Grey — spokes, rim, drum framing",
        albedo=(0.355, 0.365, 0.375), roughness=0.62, metallic=0.25,
        specular=0.50, texture="hull_plate", uv_scale=1.0 / 24.0,
        normal_scale=0.9,
        # NOT the land-use risers. `drum_riser` was a bind fragment here until
        # the generated rules table was read back: it shadowed every
        # `drum_riser_*` alias, so the 9.5 m cliff between the water band and
        # the settlement band came out as painted structural steel. A riser is
        # a bank of ground seen from below, so it takes a ground material.
        binds=("spoke", "ground_rim"), scenes=("drum",),
        source="godot/scenes/drum.tscn; 34b structure clusters H 148-204 S 0.025-0.037 — neutral"))

    a(Material(
        "endcap_plate", "End Cap Plate — the dished bulkhead's courses",
        albedo=(0.430, 0.441, 0.458), roughness=0.68, metallic=0.20,
        specular=0.45, texture="hull_plate", uv_scale=1.0 / 32.0,
        normal_scale=1.1,
        binds=("endcap_plate",), scenes=("drum",),
        source="34b course grey, sampled 0.430/0.441/0.458"))

    a(Material(
        "endcap_checker", "End Cap Checker Course — the two plated courses",
        albedo=(0.365, 0.375, 0.395), roughness=0.55, metallic=0.30,
        specular=0.45, texture="hull_plate", uv_scale=1.0 / 16.0,
        normal_scale=1.1,
        binds=("endcap_plate_c2_checker", "endcap_plate_c5_checker"),
        scenes=("drum",),
        source="34b — two of eight courses read as a different plating pattern",
        note=("Session 2y demoted the checker from 0.35 m of relief to a "
              "material group, because 0.35 m on a 278 m radius was never going "
              "to read as relief and the step was tearing the cap open. This is "
              "where it landed: same albedo family, finer plate pitch.")))

    a(Material(
        "endcap_course_wall", "End Cap Course Wall — the riser behind each rib",
        albedo=(0.255, 0.262, 0.275), roughness=0.75, metallic=0.20,
        specular=0.40,
        binds=("endcap_course_wall",), scenes=("drum",),
        source="34b — in shadow behind every rib step"))

    a(Material(
        "endcap_rib", "End Cap Rib — the radial ribs",
        albedo=(0.321, 0.327, 0.350), roughness=0.50, metallic=0.35,
        specular=0.50,
        binds=("endcap_rib",), scenes=("drum",),
        source="34b outer grey, sampled 0.321/0.327/0.350"))

    a(Material(
        "endcap_rimlight", "End Cap Rim Light — the one cold accent in the drum",
        albedo=(0.600, 0.750, 0.950), roughness=0.30, metallic=0.0,
        specular=0.25, emission=(0.420, 0.660, 1.000), emission_energy=5.0,
        binds=("endcap_rimlight",), scenes=("drum",),
        source="godot/scenes/drum.tscn"))

    a(Material(
        "truss_steel", "Guideway Truss — lattice carrying the habitat's light",
        albedo=(0.204, 0.200, 0.181), roughness=0.55, metallic=0.40,
        specular=0.45, texture="truss_steel", uv_scale=1.0 / 8.0,
        normal_scale=1.0,
        binds=("truss_chord", "truss_tie", "truss_web"), scenes=("drum",),
        source="34b lattice, sampled 0.204/0.200/0.181"))

    a(Material(
        "truss_lamp", "Light Run Tube — the habitat's light source",
        albedo=(0.950, 0.950, 0.920), roughness=0.35, metallic=0.0,
        specular=0.25, emission=(1.000, 0.990, 0.930), emission_energy=9.0,
        binds=("truss_lamp",), scenes=("drum",),
        source="34b tube cores clip at 1.000/1.000/0.94-0.97; 33a rectangular fixtures on the truss underside",
        note="Authority 1, and it settles a question that had no answer: the habitat is lit from the trusses."))

    # ---- drum: core axis -------------------------------------------------
    a(Material(
        "core_tube", "Core Tube Barrel — the axial shuttle tube",
        albedo=(0.322, 0.329, 0.315), roughness=0.45, metallic=0.45,
        specular=0.50, texture="hull_plate", uv_scale=1.0 / 20.0,
        normal_scale=0.8,
        binds=("core_tube_barrel", "core_tube"), scenes=("drum",),
        source="34b, sampled 0.322/0.329/0.315"))

    a(Material(
        "core_collar", "Core Collar — the fine ring groups at segment joints",
        albedo=(0.450, 0.425, 0.400), roughness=0.40, metallic=0.40,
        specular=0.50,
        binds=("core_tube_collar",), scenes=("drum",),
        source="33a: lighter and warmer than the barrel (relationship, not absolute — 33a is strongly graded)"))

    a(Material(
        "core_band", "Core Band — the dark ring between collar groups",
        albedo=(0.190, 0.195, 0.200), roughness=0.40, metallic=0.50,
        specular=0.50,
        binds=("core_tube_band",), scenes=("drum",),
        source="34b"))

    a(Material(
        "core_band_warm", "Core Warm Band — the red-orange collar rings",
        albedo=(0.520, 0.280, 0.190), roughness=0.55, metallic=0.20,
        specular=0.45,
        binds=("core_tube_band_warm",), scenes=("drum",),
        source="33a red-orange collar rings"))

    a(Material(
        "core_structure", "Core Structure — cage, end rings, hub framing",
        albedo=(0.240, 0.245, 0.250), roughness=0.50, metallic=0.45,
        specular=0.50, texture="truss_steel", uv_scale=1.0 / 6.0,
        normal_scale=0.9,
        binds=("core_tube_cage", "core_tube_end", "core_hub_", "core_node_"),
        scenes=("drum",),
        source="godot/scenes/drum.tscn"))

    a(Material(
        "core_hub_lamp", "Hub Lamp", albedo=(0.900, 0.900, 0.880),
        roughness=0.35, metallic=0.0, specular=0.25,
        emission=(1.000, 0.960, 0.860), emission_energy=6.0,
        binds=("core_hub_lamp",), scenes=("drum",),
        source="godot/scenes/drum.tscn"))

    # ---- tram ------------------------------------------------------------
    a(Material(
        "tram_body", "Tram Body — white livery",
        albedo=(0.730, 0.715, 0.690), roughness=0.42, metallic=0.15,
        specular=0.50,
        binds=("tram_body", "tram_roof", "tram_cap", "tram_port", "tram_recess",
               "tram_shoe", "tram_valance"),
        scenes=("drum",),
        source="33a reads white under a warm grade"))

    a(Material(
        "tram_band", "Tram Banding — the red livery stripe",
        albedo=(0.420, 0.140, 0.130), roughness=0.45, metallic=0.10,
        specular=0.45,
        binds=("tram_band",), scenes=("drum",),
        source="33a livery stripe"))

    a(Material(
        "tram_glass", "Tram Glazing — opaque dark",
        albedo=(0.045, 0.060, 0.070), roughness=0.08, metallic=0.80,
        specular=0.90,
        binds=("tram_glass", "tram_in_window"), scenes=("drum",),
        source="godot/scenes/drum.tscn",
        note="Opaque rather than transparent: transparency costs a sort and buys nothing at 236 m."))

    a(Material(
        "tram_headlight", "Tram Headlight", albedo=(0.900, 0.900, 0.850),
        roughness=0.30, metallic=0.0, specular=0.25,
        emission=(1.000, 0.950, 0.820), emission_energy=8.0,
        binds=("tram_headlight",), scenes=("drum",),
        source="godot/scenes/drum.tscn"))

    # Saloon. `35a` is unusually good vehicle-interior reference and the saloon
    # was built for it, so it gets its own set rather than borrowing the kit's.
    a(Material(
        "tram_saloon_wall", "Tram Saloon Wall — cool grey panelling",
        albedo=(0.486, 0.486, 0.546), roughness=0.48, metallic=0.12,
        specular=0.40,
        binds=("tram_in_wall", "tram_in_ceiling", "tram_in_reveal",
               "tram_in_mullion", "tram_in_bezel"),
        scenes=("drum",),
        source="35a lit wall cluster, balanced rgb(0.486, 0.486, 0.546) H 240 S 0.110",
        note="The one place in the station where a near-neutral surface measures COOL rather than warm-neutral."))

    a(Material(
        "tram_saloon_seat", "Tram Saloon Seat — maroon soft goods",
        albedo=(0.375, 0.237, 0.225), roughness=0.88, metallic=0.0,
        specular=0.25,
        binds=("tram_in_seat",), scenes=("drum",),
        source="35a lit cushion cluster, balanced rgb(0.375, 0.237, 0.225) H 5 S 0.401, 10.4% of the saloon",
        note=("Three candidate clusters and the choice matters. The 6.3% "
              "cluster at (0.491, 0.383, 0.392) is the brightest, and chipped "
              "it renders dusty pink -- nothing like the frame. The 15.5% "
              "cluster at S 0.588 is cushion in shadow, and upholstery "
              "saturates as it darkens. The 10.4% cluster is the seat face "
              "under the same key as the wall panels, and it is the one that "
              "keeps the RELATIONSHIP the frame shows: seat 0.375 against wall "
              "0.486 is 0.77, so the seat is assigned 0.77x the wall's albedo "
              "rather than a colour picked on its own. Roughness 0.88 because "
              "it is cloth, and it is the only cloth in the drum.")))

    a(Material(
        "tram_saloon_floor", "Tram Saloon Floor",
        albedo=(0.264, 0.257, 0.294), roughness=0.70, metallic=0.10,
        specular=0.35, texture="deck_stud", uv_scale=1.0 / 0.6,
        normal_scale=1.2,
        binds=("tram_in_floor", "tram_in_plinth", "tram_in_skirt"),
        scenes=("drum",),
        source="35a shadowed panel cluster, balanced rgb(0.264, 0.257, 0.294)"))

    a(Material(
        "tram_saloon_post", "Tram Saloon Stanchion — brushed pole",
        albedo=(0.560, 0.565, 0.580), roughness=0.28, metallic=0.75,
        specular=0.60,
        binds=("tram_in_post",), scenes=("drum",),
        source="35a vertical poles read as bare metal against the painted panels",
        extrapolated="metallic 0.75 — the frame shows a specular roll-off along the pole, which fixes the kind but not the value"))

    a(Material(
        "tram_saloon_strip", "Tram Saloon Amber Panel — the lit strip below the bench",
        albedo=(0.500, 0.400, 0.120), roughness=0.35, metallic=0.0,
        specular=0.25, emission=(1.000, 0.780, 0.220), emission_energy=2.6,
        binds=("tram_in_strip", "tram_in_readout", "tram_in_device"),
        scenes=("drum",),
        source="35a — four amber panels along the saloon wall at (0.55,0.79)-(0.60,0.83) and repeats",
        note="The only warm light in the saloon, against a cool-grey shell. It is what makes the car read as inhabited."))

    # ---- fallback --------------------------------------------------------
    a(Material(
        "unbound", "UNBOUND — a colour that cannot occur in the model",
        albedo=(1.0, 0.0, 0.85), roughness=1.0, metallic=0.0, specular=0.5,
        emission=(1.0, 0.0, 0.85), emission_energy=2.0,
        binds=(), scenes=("drum", "interior"),
        source="not sampled — deliberately impossible",
        note=("Magenta on purpose. This project has twice lost sessions to a "
              "defect that was invisible because the wrong thing and the "
              "background were the same pixels. A neutral grey fallback in a "
              "station full of greys is a silent failure.")))

    # =====================================================================
    # LAYER 3 -- THE PROCEDURAL INTERIOR
    # =====================================================================
    # Every surface station/rooms.py emits for the 68 procedural locations.
    # Proposed by four agents working one surface family each, against the
    # reference set and the PROVENANCE block above; rendered into this file by
    # station/apply_proposals.py from the JSON in docs/layer3-proposals/, so
    # the numbers here are provably the ones that were reviewed rather than
    # ones retyped. Gated by station/test_materials_layer3.py.
    #
    # The prose on each material is the proposer's own reasoning, kept because
    # it is the record of WHY a value is what it is -- which is the bar
    # CLAUDE.md sets for an extrapolation, and the thing that makes the value
    # reviewable later by someone who was not here.

    # ---- electronics ---------------------------------------------------

        # A console is not a desk and must not render as one. Both authority-1
        # console frames show the same two-part object — a pale grey moulded
        # case and a much darker instrument face carrying lit keys — at a
        # consistent ratio: war room 0.290/0.529 = 0.55, and the whole assembly
        # averages 0.454 of its own case. rooms.py emits prop_console as ONE
        # box, so the material has to be the assembly's area-weighted read,
        # which is 0.21: a dark instrument mass, well below the 0.46 wall and
        # below the 0.40 deck. NEUTRAL by refusal, not by choice — the two
        # frames disagree on hue (war room balances warm H 9-40 under a warm
        # key; C&C reads H 247-251 RAW under a blue key), and both balanced
        # saturations (0.028, 0.082) bracket the corridor wall's own 0.046, so
        # there is no tint any frame supports. THE EMISSION IS THE POINT: C&C's
        # key field measures warm in BOTH the raw frame (H 346-354) and the
        # balanced one (H 18-30) inside a room whose ambient is blue, so the
        # warmth belongs to the object, not the light — this is the
        # NEGATIVE_RESULTS test run on a console and passed. It lands on
        # ACCENTS['warm_practical'] (H 24), independently re-derived at H 30.
        # Energy is flux-matched rather than picked: the lit fraction above L
        # 0.30 is 0.370 (C&C left bed), 0.285 (C&C right bed), 0.203 (war-room
        # console face), mean 0.286; the top plus front faces are 2.38 of the
        # 3.745 m2 visible on a 1.40x0.65x1.05 box with its back to a wall,
        # i.e. 0.635; 0.286 x 0.635 = 0.182 x 2.6 (tram_saloon_strip, a fully
        # lit device panel) = 0.47. metallic 0.0 because a console case is
        # moulded and painted — the metal, if any, is under the coating, so it
        # is not in the 0.2-0.8 worn-plate band hull_exterior occupies. KNOWN
        # LIMIT, declared: the box glows uniformly, including its back and
        # underside. The fix is a sub-group split in rooms.py (case / control
        # face) and it belongs to layer 5, not here. No cross-frame ratio is
        # claimed from C&C: an operator stands on the console centreline in
        # that frame and its grey-world gains (1.307/1.130/0.741) are the most
        # aggressive in the reference set.
    a(Material(
        "device_console_bed", "Console Instrument Bed — control podium, charcoal with a warm key field",
        albedo=(0.212, 0.212, 0.214), roughness=0.35, metallic=0,
        specular=0.5,
        emission=(1.000, 0.612, 0.353), emission_energy=0.5,
        binds=("prop_console", "prop_reactor_console", "prop_furnace_control", "prop_irrigation_control"), scenes=("interior",),
        source="03-sector-blue/war room.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (1.088/1.062/0.877). 6-cluster over the console assembly (0.55,0.60)-(1.00,1.00): V 0.596 at 4.0%, 0.390 at 13.1%, 0.286 at 23.8%, 0.210 at 28.2%, 0.136 at 28.0% — area-weighted mean V 0.240. Same frame, the console's own pale capping rail (0.625,0.634)-(0.719,0.662) reads V 0.529 S 0.051, and its dark control face (0.79,0.79)-(0.87,0.85) V 0.290 S 0.028. Emission colour corroborated on 03-sector-blue/comand and contorl.webp: the two lit control beds, luminance-weighted mean of everything above L 0.30, balanced, rgb(0.640, 0.478, 0.317) H 30 S 0.505, normalised (1.000, 0.747, 0.495).",
        extrapolated="The absolute level, via ALBEDO_ANCHOR. The frame gives a RATIO (assembly 0.240 / the console's own pale case 0.529 = 0.454); the case is the same painted panel work as the walls, so the anchor 0.46 x 0.454 = 0.209 sets the level. Also extrapolated: emission_energy 0.5 by flux-matching (see reasoning), and the decision to give one box a uniform emission at all."))

        # Every station screen in the reference set is the same surface: a
        # near-black glass field carrying high-chroma content, in a bezel
        # barely brighter than the field. That is true of the three concourse
        # panels, the war-room map and the war-room console readout, so babcom
        # terminal, monitor wall and tactical display are one material at three
        # sizes — the brief's steel-door / blast-door case exactly. roughness
        # 0.12 because it IS glass, which is the only thing the mirror rule in
        # test_materials_layer3.py permits below 0.15; the name carries
        # 'screen' and 'glass' so MIRROR_OK sees it. THE BLUE TRIM IS DECLARED,
        # NOT HIDDEN: the measured field is rgb(0.053, 0.054, 0.082), but at V
        # 0.08 on a black field in a chroma-subsampled JPEG a 7-code blue
        # excess is at the resolution limit, and S 0.35 would put a surface
        # over STRUCTURAL_SAT_MAX; 0.062 keeps it at S 0.161 and inside the
        # measurement's noise. The emission colour is the lit-area-weighted
        # mean of four panels — lit fractions above L 0.30 of 0.157, 0.315 and
        # 0.204 (concourse) and 0.374 (war-room map) — giving peak-normalised
        # (0.931, 1.000, 0.912). Its slight green bias is the green wireframe
        # content, and it is honest that a screen averages to near-neutral
        # because screens carry mixed content; layer 5 gives them real content
        # and can then justify a per-screen colour. Energy = 3.0
        # (signage_panel, a fully backlit panel) x mean lit fraction 0.2625 =
        # 0.79. As light_deck_channel already says of itself: an emissive is
        # not a light, and a monitor wall in Security Central will need a real
        # light beside it in layer 4.
    a(Material(
        "device_screen_glass", "Screen Glass — dark panel with lit content",
        albedo=(0.052, 0.054, 0.062), roughness=0.12, metallic=0,
        specular=0.65,
        emission=(0.930, 1.000, 0.915), emission_energy=0.8,
        binds=("prop_babcom_terminal", "prop_monitor_wall", "prop_tactical_display"), scenes=("interior",),
        source="11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg (authority 1), grey-world gains 1.046/1.065/0.905. Unlit screen field (0.32,0.19)-(0.56,0.235) balanced rgb(0.053, 0.054, 0.082); whole-panel dominant clusters 49.3% at V 0.037 (centre screen) and 45.9% at V 0.051 (right screen); bezel V 0.092. Content registers in the same frame: green wireframe H 121-141, blue title bar rgb(0.145,0.154,0.627) H 239 S 0.768, yellow caps H 60-75. Fourth panel from 03-sector-blue/war room.webp, the backlit galactic map, lit content luminance-weighted mean normalised (0.858, 0.918, 1.000).",
        extrapolated="The blue channel trimmed from the measured 0.082 to 0.062, and emission_energy 0.8 by flux-matching. The single emission colour is a real average across four measured panels rather than a colour any one screen has."))

        # These six are one object at six sizes: a small dark moulded device
        # with a slot or a button and one indicator. The reference supports the
        # black: the counter reader is 0.31 of its own counter top, i.e.
        # roughly a third of the wall's albedo, and it reads as matte black in
        # the frame. A COUNTER-READING IS RECORDED RATHER THAN SUPPRESSED — the
        # handheld scanner in 'Identicard reader.webp' balances much lighter, V
        # 0.241-0.431, which would argue for ~0.35. I did not use it: that
        # frame's grey-world gains are 0.837/1.042/1.182 on a warm-lit scene,
        # and after correction the body reads H 200-220, a blue that is plainly
        # the over-correction and not the paint. The counter reader is the
        # object my props actually are (a wall reader, a credit kiosk, a lift
        # call plate); the handheld is a different prop the directory does not
        # declare. The indicator colour is the strongest agreement in this
        # family: two independent authority-1 frames of two different devices
        # give normalised (1.000, 0.315, 0.404) and (1.000, 0.349, 0.104), mean
        # (1.000, 0.332, 0.254) — within 0.03 of marker_light_red's (1.000,
        # 0.300, 0.120), measured on the hull, which suggests one
        # indicator-lamp register across the whole station. ENERGY IS AT A
        # DECLARED FLOOR AND SAYS SO: flux-matching gives 2.1 x 0.05 = 0.105
        # (LED bar 78x42 px in a 170x290 px plinth = 0.066; lens stack 39x83 px
        # in a ~300x330 px body = 0.033), which is below the level at which
        # anything reads at all. 0.25 is the floor I apply consistently across
        # this family's prop-scale indicators, and it is chosen, not measured.
        # metallic 0.0: moulded plastic. roughness 0.30 because a moulded
        # consumer device is semi-gloss — smoother than the console's
        # instrument bed, which is why these two materials stay separate
        # despite both being dark.
    a(Material(
        "device_reader_shell", "Reader Shell — black moulded card reader and kiosk",
        albedo=(0.145, 0.143, 0.145), roughness=0.3, metallic=0,
        specular=0.5,
        emission=(1.000, 0.330, 0.250), emission_energy=0.25,
        binds=("prop_identicard_reader", "prop_credit_terminal", "prop_exchange_terminal", "prop_manifest_terminal", "prop_lift_call", "prop_intercom"), scenes=("interior",),
        source="11-props-and-technology/credit chit.jpg (authority 1), grey-world gains 0.919/1.003/1.093. The counter-mounted card reader clusters 41.4% at V 0.121 against the same frame's counter top at V 0.393; its red LED bar clusters at rgb(0.317, 0.100, 0.128) H 352 S 0.683. Second indicator measurement from 11-props-and-technology/Identicard reader.webp: the amber lens stack (0.196,0.375)-(0.245,0.56) balances rgb(0.269, 0.094, 0.028) H 16 S 0.897. Object identity from reference/00-INDEX.md, which reads the credit-chit reader as 'a small black wedge plinth with a top slot and a red LED line on its front face'.",
        extrapolated="The absolute level via ALBEDO_ANCHOR (ratio 0.121/0.393 = 0.308 x 0.46 = 0.142), and emission_energy, which is FLOORED rather than measured — see reasoning."))

        # This is the same register as the library's existing emissive_signage,
        # re-measured from a SECOND frame: my clusters bracket 0.385-0.591 in
        # red at H 166-169, and ACCENTS['cyan_neon'] = (0.444, 1.000, 0.939)
        # sits inside that bracket. That is corroboration, not a new colour,
        # and I have kept the accent value rather than replacing it with mine.
        # RECORDED, NOT PICKED — reference/00-INDEX.md's own instruction for
        # this sign: 04-sector-red/more zocalo.png (1440x1080, the best Zocalo
        # frame in the set) shows the SAME wordmark ORANGE-RED, clustering
        # rgb(0.768, 0.253, 0.146) H 10 S 0.810, rgb(0.836, 0.390, 0.171) H 20,
        # rgb(0.901, 0.550, 0.263) H 27 at V 0.77-0.90; and Darkstar_logo.webp
        # shows the Dark Star venue sign as a dark ground with warm pale
        # letterforms (V 0.347 H 36, V 0.540 H 39). Cyan wins because the
        # library already has exactly one neon register and prop_neon_sign is
        # used in only two places, so a second register bought for one prop
        # would split what the file deliberately keeps unified; the orange-red
        # numbers are recorded here so a future sub-group split can take them
        # in one edit. Albedo is the BOARD, not the tube: prop_neon_sign is a
        # 1.60x0.10x0.55 m box, i.e. sign plus backing plate, so it sits a
        # little above emissive_signage's glyph-only 0.050/0.090/0.100. Energy
        # = 4.5 (emissive_signage, a neon tube) x 0.283 (the measured fraction
        # of the board above L 0.50) = 1.27, so the box radiates the flux the
        # real board does even though it cannot show where the tube is.
    a(Material(
        "sign_neon_venue", "Venue Neon — concourse sign board, cyan tube on a dark ground",
        albedo=(0.094, 0.100, 0.112), roughness=0.3, metallic=0,
        specular=0.25,
        emission=(0.444, 1.000, 0.939), emission_energy=1.3,
        binds=("prop_neon_sign",), scenes=("interior",),
        source="11-props-and-technology/Zocalo neon signage in background.jpg (authority 1), grey-world gains 0.935/1.162/0.935. Wordmark 5-cluster over (0.47,0.03)-(0.65,0.16): 33.3% rgb(0.591, 0.999, 0.921) H 168, 26.5% rgb(0.385, 0.995, 0.879) H 169 S 0.613, 11.5% rgb(0.316, 0.832, 0.709) H 166. Board ground between the chevron blades (0.36,0.10)-(0.44,0.125) balances rgb(0.092, 0.105, 0.136). Lit fraction of the sign board (0.30,0.02)-(0.78,0.19): 0.386 above L 0.30, 0.283 above L 0.50, 0.225 above L 0.70. Cross-checked against 04-sector-red/more zocalo.png and 04-sector-red/Darkstar_logo.webp — see extrapolated.",
        extrapolated="The choice of the cyan state over the orange-red state, and emission_energy 1.3 by flux-matching. The board ground's blue channel is trimmed from the measured 0.136 to 0.112 to keep S under 0.20."))

        # This is the one prop in my family that materials.py had already
        # measured without knowing it — PROVENANCE lists 'amber sign plaque V
        # 0.247 S 0.184' in the corridor kit's own region table, and it is
        # prop_level_plaque. I re-measured it (0.251, S 0.181) rather than
        # copying the number. THE HARD PART IS THAT THIS FRAME IS THE ONE
        # NEGATIVE_RESULTS WARNS ABOUT: the plaque sits on the LEFT wall, the
        # wall whose warmth turned out to be warm downlights rather than ochre
        # paint. So I ran the test that entry prescribes — find the same light
        # on a different material — and it passes in the strongest possible
        # form: the wall 20 px ABOVE the plaque, under the same fitting,
        # balances H 202 S 0.027, dead neutral, while the plaque balances S
        # 0.181. Across a few centimetres of one wall under one light, the
        # warmth follows the object. The failed case was warmth that followed
        # the wall; this is warmth that does not. AND IT IS NOT EMISSIVE, which
        # is the finding that surprised me: a p10-to-p90 spread of 0.053 about
        # a 0.251 median is a flat matte face with no hot spot, and the plaque
        # reads DARKER than the wall it is fixed to (0.251 against 0.340). A
        # backlit plaque cannot be darker than its surround. So it gets no
        # emission and a high roughness, and it will read as a painted sign
        # catching the corridor's own light — which is what the frame shows. S
        # 0.179 keeps it under STRUCTURAL_SAT_MAX without trimming, and the
        # source cites the frame regardless. It stays separate from
        # sign_neon_venue because a matte painted plaque and a glowing tube
        # sign are not the same surface by any reading.
    a(Material(
        "sign_deck_plaque", "Deck Plaque — the amber corridor sign, matte and unlit",
        albedo=(0.391, 0.379, 0.321), roughness=0.72, metallic=0,
        specular=0.35,
        binds=("prop_level_plaque",), scenes=("interior",),
        source="07-sector-grey/grey level 1.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.970/1.087/0.953). Amber sign plaque (0.084,0.309)-(0.111,0.360): rgb(0.251, 0.243, 0.206) H 49 S 0.181 V 0.251, p10 0.228, p90 0.281. Same frame, wall plate course (0.019,0.236)-(0.125,0.293) V 0.295 — the exact region materials.ALBEDO_ANCHOR is calibrated on. Same frame, the wall immediately above the plaque (0.070,0.280)-(0.125,0.300): H 202 S 0.027 V 0.340.",
        extrapolated="The absolute level only, via ALBEDO_ANCHOR: the plaque is 0.251/0.295 = 0.851 of the anchored wall plate course, so 0.46 x 0.851 = 0.391 and the channels scale with it."))

        # A valve is the one genuinely metallic thing in my family and the
        # gate's physicality rule decides most of it: metallic 0.95 because a
        # handwheel is bare metal with no coating over it, which is why it does
        # NOT sit in the 0.2-0.8 blend band that hull_exterior (0.34) and
        # greeble_fitting (0.42) occupy — those are painted or worn plate, and
        # materials.py's test file records that the library authors that band
        # deliberately for exactly that case. At metallic 0.95 the albedo is
        # effectively F0, and mild steel's is about 0.56 neutral;
        # 0.545/0.540/0.528 is that with a 3% warm bias for grime, smaller than
        # the 6% hull_exterior declares. Roughness 0.42 is placed on the
        # library's own ladder rather than picked in the abstract: rougher than
        # tram_saloon_post at 0.28, which is a brushed rail nobody grips hard,
        # and smoother than structural_truss at 0.46, because a valve is a
        # touched object and hands polish a handwheel. Untextured for the
        # reason radiator is untextured — it is a small formed object, not
        # plate, and every sheet this project owns (hull_plate, wall_plate,
        # deck_stud, deck_plate, truss_steel) is architectural at metre scale
        # and would read as a wall wrapped round a 0.45 m wheel. WHAT WOULD
        # OVERTURN IT: any engineering-space frame. If station valves turn out
        # to be painted bodies with a coloured handwheel, this becomes two
        # surfaces and metallic drops to 0.0 for the body.
    a(Material(
        "plant_valve_metal", "Valve — bare metal handwheel and stem, worn by use",
        albedo=(0.545, 0.540, 0.528), roughness=0.42, metallic=0.95,
        specular=0.5,
        binds=("prop_valve",), scenes=("interior",),
        source="NO FRAME ESTABLISHES THIS. The reference set holds no view of the station's machine spaces at all: reference/08-sector-yellow-engineering/ and reference/06-sector-brown-downbelow/ are empty directories, and canon/INVENTIONS.md says the same thing in its own words for the plant zone — 'Overturned by: any on-screen view of the station's machine spaces, of which we hold none.' What IS sourced is the object: station/directory.py declares valve in eleven locations, all of them water storage, waste, fuel, air handling or reclamation, and station/rooms.py sizes it 0.45 m square, wall-mounted — a handwheel, not a control panel.",
        extrapolated="Every number. Declared in full rather than dressed as a reading."))

        # A breaker lever and a tank gauge are the same object at two sizes — a
        # painted enclosure on a plant-room wall with a handle or a dial face
        # and one indicator — so they share a material rather than getting one
        # each for two groups. metallic 0.0 because a painted enclosure is a
        # dielectric: the steel is under the coat, and this is precisely the
        # distinction the library's own test file documents when it explains
        # why hull_exterior sits at 0.34 (48 m of plating worn through in
        # places) while a 0.3 m instrument case has no such story. The value is
        # deliberately BELOW the wall: 0.298 against 0.460 makes plant fittings
        # read as darker machinery bolted onto lighter architecture, which is
        # the relationship greeble_fitting already encodes on the exterior at
        # 0.310 against the hull's 0.600 — I am reusing a measured relationship
        # where I have no measurement of my own. Energy sits at the same
        # declared 0.25 floor as device_reader_shell and for the same reason: a
        # dial lamp is a few square centimetres of a 0.30 m box, flux-matching
        # gives a number that renders as nothing, and a plant room where
        # nothing is powered reads as abandoned. NOT hazard_yellow, although
        # SECTOR_ACCENT maps Yellow sector to it — that mapping carries the
        # comment 'NO REFERENCE. Extrapolated from the sector being
        # engineering', and preferring a measured register to an extrapolated
        # one is the whole discipline here. WHAT WOULD OVERTURN IT: an
        # engineering frame; and specifically, if breaker handles turn out to
        # be hazard-coloured, the handle becomes a second surface and
        # ACCENTS['hazard_yellow'] finally gets a measurement behind it.
    a(Material(
        "plant_switchgear", "Switchgear and Gauge — painted plant instrument case",
        albedo=(0.298, 0.296, 0.290), roughness=0.55, metallic=0,
        specular=0.4,
        emission=(1.000, 0.612, 0.353), emission_energy=0.25,
        binds=("prop_breaker_lever", "prop_tank_gauge"), scenes=("interior",),
        source="NO FRAME ESTABLISHES THE CASE — same gap as plant_valve_metal: reference/08-sector-yellow-engineering/ is empty and canon/INVENTIONS.md records that the machine spaces have no on-screen view. Placed instead on materials.py's own measured value ladder, between kit_reveal (0.140), greeble_fitting (0.310, measured on 01-station-exterior/exterior more.jpg as bolted-on unpainted machinery) and kit_wall_plate (0.460). The INDICATOR colour is measured: the only two authority-1 readings of a small indicator in the whole set are the amber lens stack in 11-props-and-technology/Identicard reader.webp (H 16, S 0.897) and the lit key field in 03-sector-blue/comand and contorl.webp (H 30, S 0.505), and both sit in the warm_practical register at H 24.",
        extrapolated="The albedo, roughness, specular and the emission_energy floor. The emission colour is the measured accent register; everything else here is declared invention."))
    # ---- shells --------------------------------------------------------

        # This is the surface with the most screen area in the station — 44
        # office, 32 generic, 20 commerce, 16 worship, 12 each
        # detention/hospitality/transit spans out of rooms.build. It is
        # therefore the material that must not be interesting. The measured
        # finding is that the station is essentially ONE albedo and that
        # everything reading as contrast is geometry, shadow or a fitting, so
        # this is pinned to ALBEDO_ANCHOR and left pure neutral. It is NOT warm
        # and NOT cool: five of the seven corroborating frames balance cool (H
        # 168-220) and two balance warm (H 30), and the two warm ones are the
        # two with warm practicals low on the wall. That is the ochre-dado
        # asymmetry again — the hue follows the light, not the paint, so there
        # is no hue. Metallic 0.0 because a painted panel is a dielectric at
        # its surface; the existing kit_wall_plate's 0.10 is neither metal nor
        # paint and is not copied. Detention is here rather than with the
        # industrial set on purpose: two of its three locations
        # (security_central, security_posts) are staffed public-facing rooms,
        # and a brig reads hard because of its lighting, its cell dividers and
        # its cell doors, not because somebody painted the wall darker.
    a(Material(
        "shell_wall_panel", "Room Shell Wall — the station's painted panel, at room scale",
        albedo=(0.455, 0.455, 0.455), roughness=0.56, metallic=0,
        specular=0.38, texture="wall_plate", uv_scale=1.0 / 4,
        binds=("commerce_wall", "detention_wall", "generic_wall", "hospitality_wall", "office_wall", "transit_wall", "worship_wall"), scenes=("interior",),
        source="07-sector-grey/grey level 1.webp wall plate course (0.019,0.236)-(0.125,0.293), balanced V 0.295 — the anchor measurement, restated here only as the level this material is pinned to. Corroborated in six frames the anchor did not come from: 03-sector-blue/war room.webp arch face (0.040,0.020)-(0.130,0.120) balanced V 0.286; 05-sector-green/council chambers.webp wall blade dominant cluster V 0.270 (29.9% of (0.00,0.00)-(0.30,0.20)); 03-sector-blue/dock.webp bay wall (0.200,0.290)-(0.330,0.400) V 0.268; 09-garden-core-and-transit/central corridor.webp walkway fascia (0.300,0.245)-(0.600,0.275) V 0.250 and wall panel (0.600,0.300)-(0.720,0.420) V 0.234; 04-sector-red/more zocalo.png lit structure cluster V 0.317. lit() of those seven: 0.365-0.511, mean 0.435.",
        extrapolated="Nothing about the colour. The 4.0 m texture repeat is chosen, not measured — but it is chosen to PRESERVE a measurement: wall_plate lays 6 plate courses across its repeat, so 4.0 m holds the 0.667 m course pitch materials.py already read off grey level 1.webp against a 2.1 m door. Any other repeat silently changes that pitch. Roughness 0.56 and specular 0.38 are extrapolated: no frame in the set separates gloss from geometry on a wall."))

        # A medlab and a fabrication hall must not be the same surface, and the
        # only defensible way to make them differ without inventing a colour is
        # to move the finish and leave the value alone. So this is the same
        # paint system a fraction lighter and a fraction smoother, with a cool
        # cast small enough to be deniable in a single frame and just large
        # enough to separate it from the warm-lit corridor outside the door.
        # The 6.0 m repeat puts 1.0 m lining panels on the wall instead of the
        # corridor's 0.667 m plate courses — a wipe-clean room is lined in
        # large sheets with few joints, and that is a legible difference in
        # silhouette rather than in colour. Metallic 0.0: a coating over steel
        # is a dielectric. Research shares it with medical because both of
        # research's locations (research_labs, gravity_torus) are laboratory
        # volumes and the archetype's own fixture is a fume column.
    a(Material(
        "shell_wall_clinical", "Clinical Shell Wall — wipe-clean lining, medlab and laboratory",
        albedo=(0.470, 0.478, 0.488), roughness=0.48, metallic=0,
        specular=0.44, texture="wall_plate", uv_scale=1.0 / 6,
        binds=("medical_wall", "research_wall"), scenes=("interior",),
        source="NO FRAME. The reference set contains no medlab, no infirmary, no isolab, no morgue and no laboratory interior — 00-INDEX.md's folder inventory has nothing in any sector folder for these ten locations. Nothing here is measured. The only sourced quantity is the level it is tied to: ALBEDO_ANCHOR 0.46, itself derived from 07-sector-grey/grey level 1.webp's wall plate course.",
        extrapolated="All of it, and this material is the reason the coverage note exists. Constrained rather than free: (1) luminance 0.477 is 1.048x the anchor, which keeps it inside the +/-15% spread the corridor's four lit elements measured, so the clinical rooms cannot drift out of the station's one paint system; (2) the cool bias is S 0.037, an order of magnitude below the accent floor of 0.20, so it can never read as a coloured wall — it reads as a white that is not warm; (3) roughness 0.48 against the standard wall's 0.56 says satin, not gloss. Overturned by any frame of a Babylon 5 medlab wall; if one appears and shows the same matte grey as a corridor, delete this material and fold its two groups into shell_wall_panel."))

        # The albedo is not invented — the mean of four readings across two
        # authority-1 frames is 0.421 and that is what this is, which makes the
        # plant wall measurably 0.92x the finished wall rather than arbitrarily
        # darker. Albedo is deliberately left PURE NEUTRAL here even though the
        # surface should read faintly warm, because hull_plate carries its own
        # (1.000, 0.985, 0.965) tint and setting a warm albedo as well would
        # double-count it; the product lands at S 0.035, which is where I want
        # it. hull_plate rather than wall_plate is the whole point of this
        # material: that sheet exists for 'deep rebated seams and proud weld
        # beads' at TEX_SLOPE 0.35, and a fabrication bay wall is fabricated
        # plate, not a finished panel. Metallic 0.0 — I looked for bare metal
        # in dock.webp and could not find it: the deck and walls show a broad
        # soft falloff under hard pendant floods with no mirror behind them and
        # no metal-like specular streak anywhere, so every large surface in
        # that bay is coated. This is the wall behind 52 industrial spans and
        # 32 store spans, the two largest counts in the whole room set.
    a(Material(
        "shell_wall_industrial", "Plant Shell Wall — heavy plate, grubby, foundry and cargo hall",
        albedo=(0.420, 0.420, 0.420), roughness=0.7, metallic=0,
        specular=0.32, texture="hull_plate", uv_scale=1.0 / 12,
        binds=("industrial_wall", "store_wall"), scenes=("interior",),
        source="03-sector-blue/dock.webp (grey-world gains 0.968/1.027/1.007), bay wall (0.200,0.290)-(0.330,0.400) balanced V 0.268 S 0.113, and stepped ledge (0.155,0.315)-(0.285,0.440) V 0.328 S 0.096 — lit() 0.418 and 0.511. 09-garden-core-and-transit/central corridor.webp (gains 1.044/1.085/0.892), wall panel (0.600,0.300)-(0.720,0.420) V 0.234 and walkway fascia (0.300,0.245)-(0.600,0.275) V 0.250 — lit() 0.365 and 0.390. Mean of the four: 0.421.",
        extrapolated="Roughness 0.70 and specular 0.32 — no frame separates gloss from geometry, and both are pushed to the dull end because these are the volumes the station does not keep clean. The 12.0 m hull_plate repeat is chosen: 16 plates across the repeat gives 0.75 m plates, deliberately within 12% of the corridor's measured 0.667 m course so that a plant wall and a finished wall share a plate module and differ only in how the seam is cut."))

        # Three frames, three completely different floor constructions — grey
        # level 1's studded plate, the Zocalo's flat tile, council chambers'
        # polished slab — all measure 1.5 to 1.8 times the value of the wall in
        # the same frame. Three unrelated materials cannot coincidentally share
        # an albedo ratio; what they share is that a floor is the surface most
        # squarely facing a downward light and that floors are smoother than
        # walls. So the ratio is illumination and gloss, and kit_deck's
        # existing ruling ('the deck measures 1.6x the wall's value, and it is
        # not 1.6x the albedo') is correct and is extended here rather than
        # re-argued. The deck therefore goes BELOW its wall in albedo and gets
        # the brightness back through roughness 0.32 and specular 0.58, which
        # is also what makes a concourse floor throw the light pools the frames
        # actually show. Metallic 0.0: a tiled or coated public floor is a
        # dielectric, and nothing in more zocalo.png reflects like metal.
        # deck_plate rather than deck_stud because the Zocalo is plainly large
        # flat tiles with dark recessed joints and the studded pattern belongs
        # to the narrow corridor.
    a(Material(
        "shell_deck_public", "Public Shell Deck — pale tiled floor, concourse and office",
        albedo=(0.396, 0.396, 0.396), roughness=0.32, metallic=0,
        specular=0.58, texture="deck_plate", uv_scale=1.0 / 4,
        binds=("commerce_deck", "detention_deck", "generic_deck", "hospitality_deck", "office_deck", "transit_deck"), scenes=("interior",),
        source="04-sector-red/more zocalo.png (gains 0.936/1.137/0.950), tile field lit (0.200,0.620)-(0.340,0.720) balanced V 0.611, and k-means over (0.15,0.60)-(0.55,0.95) giving lit deck clusters at V 0.465 / 0.619 / 0.715 against lit structure clusters at V 0.317 / 0.436 in the same frame — a deck:wall ratio of 1.8. 05-sector-green/council chambers.webp floor (0.900,0.860)-(0.990,0.990) V 0.496 against wall clusters V 0.270-0.425, ratio ~1.5. 07-sector-grey/grey level 1.webp deck field V 0.471 against wall 0.295, ratio 1.60.",
        extrapolated="The albedo is a DERIVED value, not a measured one, and the derivation is the interesting part — see reasoning. 0.396 is 0.87x the wall it meets. The 4.0 m deck_plate repeat gives 1.0 m tiles, estimated off more zocalo.png's joint grid against the café furniture; it is the weakest number in this material and one frame with a person standing on a tile joint would close it."))

        # This is the one surface in my thirty-three that is deliberately
        # untextured, and the choice is the material. A medlab floor is welded
        # sheet or poured resin coved up the wall — it has no plate seam, no
        # stud, no tile joint, and giving it deck_plate's 0.22-slope seams
        # would put a cargo-bay joint in an operating room. What it does have
        # is gloss: at roughness 0.24 and specular 0.62 it mirrors the room's
        # own lights, which is exactly how a clinical floor reads and is the
        # single strongest cue that this room is not a corridor. That is a PBR
        # surface, not flat colour — the layer-3 bar is that every mesh carries
        # a material, and an untextured coating with real roughness and real
        # Fresnel is one. Metallic 0.0: resin over deck plate is a dielectric.
    a(Material(
        "shell_deck_clinical", "Clinical Shell Deck — seamless coved resin, medlab and laboratory",
        albedo=(0.414, 0.420, 0.428), roughness=0.24, metallic=0,
        specular=0.62,
        binds=("medical_deck", "research_deck"), scenes=("interior",),
        source="NO FRAME — there is no medlab, infirmary, isolab, morgue or laboratory interior anywhere in the reference set. Not measured. The only sourced input is the deck:wall ratio established in three other frames (more zocalo.png 1.8, council chambers 1.5, grey level 1 1.60) and interpreted as illumination, which is what puts this at 0.88x the clinical wall.",
        extrapolated="All of it. Constrained by: it must be 0.88x its wall like every other deck in this set; it must be smoother than its wall (0.24 against 0.48); its cool cast is inherited from shell_wall_clinical at S 0.033, so floor and wall cannot disagree about the room's temperature; and roughness stays at 0.24 rather than going lower because below 0.15 is glass and nothing else. Overturned by one frame of a medlab floor."))

        # This is the grubbiest floor in the station and it still has to obey
        # the two rules the set obeys everywhere: darker than its wall and
        # smoother than its wall. It is smoother than the plant wall (0.52
        # against 0.70) and rougher than the office floor (0.52 against 0.32),
        # so 'industrial is rougher' lives in the absolute level while 'a deck
        # is smoother than a wall' lives in the pairing, and both are true at
        # once. Metallic 0.0 is the call I spent the longest on and I am
        # recording why: a working bay deck is the most plausible bare-metal
        # surface in my whole family, but dock.webp shows a broad soft gradient
        # from the pendant floods with no mirror and no anisotropic streak, and
        # the frame's painted red disc and yellow chevrons imply a painted
        # field to paint them onto. The surface is coated steel, so it is a
        # dielectric, so it is 0.0 — not the 0.20-0.30 the existing kit decks
        # carry, which the physical rule forbids.
    a(Material(
        "shell_deck_industrial", "Plant Shell Deck — worn plate with recessed seams, bay and store",
        albedo=(0.365, 0.365, 0.365), roughness=0.52, metallic=0,
        specular=0.46, texture="deck_plate", uv_scale=1.0 / 6,
        binds=("industrial_deck", "store_deck"), scenes=("interior",),
        source="03-sector-blue/dock.webp (gains 0.968/1.027/1.007), lit apron (0.300,0.665)-(0.500,0.720) balanced V 0.501 S 0.080 and deck mid (0.300,0.500)-(0.500,0.545) V 0.239 S 0.067 — the same deck at a 2.1x illumination range and near-neutral at both ends. Against the bay wall in the same frame at V 0.268, the lit deck is 1.9x. 10-interiors-generic-kit/more hallways.jpg (gains 0.794/1.145/1.154) shows the plate construction: large flat plates with recessed seams and litter, and the same deck balances H 36 S 0.65 on its warm-lit half and H 179-200 S 0.12-0.25 on its cool-lit half — one surface, two lights, two colours, so it is neutral.",
        extrapolated="The albedo is derived at 0.87x its wall by the deck:wall ratio argument, not read off a frame. Roughness 0.52 and specular 0.46 are extrapolated. The 6.0 m repeat gives 1.5 m plates, which is kit_deck_plate's existing figure and is kept deliberately so that two deck materials visible in one shot cannot disagree about how big a deck plate is."))

        # Four locations — sanctuary_blue, alien_worship, sanctuaries,
        # interfaith_chapel — and the entire point of the archetype is that it
        # should not feel like the rest of the station. rooms.py already gives
        # it the height (4.2 m, the tallest non-plant ceiling) and the emptiest
        # prop density (0.18); what it does not have is a floor that sounds
        # different underfoot. At roughness 0.20 and specular 0.66 this is the
        # most reflective non-glass surface in my set: it will carry the
        # reflection of a dais and a shrine across an empty floor, which is
        # what makes a sanctuary read as a sanctuary and is something no amount
        # of wall treatment can do. It gets its own material for one group
        # rather than being merged into the public deck because roughness 0.20
        # against 0.32 and a visible slab joint against a tile joint are a
        # genuine on-screen difference, which is the stated test for not
        # over-merging. Metallic 0.0: stone is a dielectric.
    a(Material(
        "shell_deck_stone", "Sanctuary Deck — polished slab, the one hard floor in the station",
        albedo=(0.400, 0.424, 0.425), roughness=0.2, metallic=0,
        specular=0.66, texture="deck_plate", uv_scale=1.0 / 3.2,
        binds=("worship_deck",), scenes=("interior",),
        source="05-sector-green/council chambers.webp (gains 0.998/1.082/0.932, which reproduce the value already in GREY_WORLD_GAINS exactly). Floor (0.900,0.860)-(0.990,0.990) balanced rgb 0.426/0.488/0.493, H 180 S 0.146 V 0.496; k-means over (0.80,0.80)-(1.00,1.00) puts 45.0% of the band on rgb(0.421,0.490,0.493) H 183 S 0.146. Wall blades in the same frame cluster at V 0.270 / 0.425, so the floor is ~1.5x the wall. This is a ceremonial floor, NOT a chapel floor — the reference set has no worship space in it at all.",
        extrapolated="Two things. (1) The saturation is CUT from the measured 0.146 to 0.059, because council chambers is keyed cool and the wall in the same frame is also cool (H 196-211) — one frame with a single-temperature key cannot separate a cool floor from a cool light, so the measured cast is carried at less than half strength as a hint rather than as a fact. (2) The mottle is missing entirely: there is no stone sheet among the seven that exist, so deck_plate at 3.2 m stands in with 0.8 m slab joints. That is the honest gap in this material and one procedural stone sheet closes it. Value 0.419 is 0.92x the wall by the deck:wall ratio argument, not the raw 0.769 that lit() would give."))

        # 38 generic, 46 office, 34 industrial-equivalent, 32 medical spans —
        # the rib is the most repeated single element in the room set, and
        # getting it wrong would articulate the whole station wrongly. The
        # measurement is unambiguous and slightly counter-intuitive: a pilaster
        # reads as a separate object in a Babylon 5 corridor at 1.02x the
        # wall's value, which means it CANNOT be doing it with albedo. So this
        # is the same paint, smoother, and the read comes from the 0.16 m of
        # relief catching a highlight along its edge. Painting the ribs lighter
        # or darker to make them 'show' would be inventing contrast the
        # reference denies and would fight the lighting layer that comes next.
        # Untextured for the same reason kit_pilaster is: a bullnose column
        # 0.45 m wide has no room for a plate course, and triplanar-projecting
        # one across a narrow vertical would smear it. Metallic 0.0 — painted
        # steel is a dielectric; the existing kit_pilaster's 0.12 is a
        # half-value the physical rule rejects.
    a(Material(
        "shell_rib_painted", "Shell Rib — painted structural pilaster, floor to soffit",
        albedo=(0.469, 0.469, 0.469), roughness=0.4, metallic=0,
        specular=0.46,
        binds=("commerce_rib", "detention_rib", "generic_rib", "hospitality_rib", "medical_rib", "office_rib", "research_rib", "transit_rib", "worship_rib"), scenes=("interior",),
        source="07-sector-grey/grey level 1.webp pilaster bullnose face (0.188,0.394)-(0.206,0.731), balanced V 0.301 against the wall plate course at V 0.295 in the same frame — a ratio of 1.02, which is the whole measurement. Corroborated at room scale by 03-sector-blue/war room.webp, whose arch pier (0.245,0.100)-(0.300,0.550) balances V 0.235 against the arch face at V 0.286 and the console rail at V 0.233: the pier is not lighter than what it sits against, it is differently shaped. 00-INDEX.md's war room entry calls that arch 'the chamfered structural language of the corridors at room scale', which is exactly the claim this material makes.",
        extrapolated="Roughness 0.40 and specular 0.46 — the frame shows a specular roll-off along the bullnose but fixes the kind and not the value, the same caveat kit_pilaster already carries. The albedo is not extrapolated: 0.469 is 1.031x shell_wall_panel and 0.983x shell_wall_clinical, so it sits inside +/-3% of BOTH walls it meets, which is the measured pilaster:wall relationship applied twice."))

        # THIS IS THE ONE MATERIAL IN MY SET ABOVE S 0.20 AND I AM DECLARING IT
        # RATHER THAN HIDING IT. It is not a 'red sector red wall' — it is a
        # specific finish on a specific element class in two specific
        # archetypes, and it passes the exact test NEGATIVE_RESULTS demands. In
        # dock.webp the girders balance H 13-22 S 0.40-0.73 while the stepped
        # structural ledge under the SAME pendant floods balances H 220 S
        # 0.096; the colour follows the material, not the light. In central
        # corridor.webp the ring frames hold S 0.294-0.324 across a 5.4x value
        # range (V 0.086 to 0.462) while the walkway fascia beside them is H
        # 134 S 0.076; constant saturation as brightness rises is a
        # multiplicative tint, which is the same arithmetic PROVENANCE uses to
        # prove the hull is NEUTRAL, run here and coming out the other way. Two
        # frames, two different lighting designs, one register. For contrast I
        # ran the same test on more zocalo.png, where the upper structure also
        # balances warm at S 0.24-0.31 — and it FAILS, because the hue is
        # incoherent across elements (H 309, 322, 357, 16, 21) at similar
        # saturations, so the Zocalo's structure is neutral and its warmth is
        # the practicals. That is the difference between a finding and the
        # ochre dado. Metallic 0.0: red-oxide primer is paint, so the surface
        # is a dielectric even though what is under it is steel. If the
        # neutrality gate rejects S 0.301, use (0.379, 0.331, 0.303) at S 0.200
        # — do NOT fall back to neutral, which contradicts both frames and
        # would throw away the single most recognisable colour note a Babylon 5
        # cargo bay has.
    a(Material(
        "shell_rib_oxide", "Plant Rib — red-oxide primed structural steel, bay and cargo hall",
        albedo=(0.379, 0.315, 0.265), roughness=0.45, metallic=0,
        specular=0.42, texture="truss_steel", uv_scale=1.0 / 2.5,
        binds=("industrial_rib", "store_rib"), scenes=("interior",),
        source="03-sector-blue/dock.webp (gains 0.968/1.027/1.007): k-means over the overhead structure band (0.00,0.00)-(0.55,0.20) gives rgb(0.080,0.042,0.029) H 15 S 0.633 and rgb(0.129,0.068,0.052) H 13 S 0.595; over the left pier band (0.02,0.18)-(0.14,0.58) gives H 22 S 0.618, H 17 S 0.731, H 17 S 0.677 and H 16 S 0.400. 09-garden-core-and-transit/central corridor.webp (gains 1.044/1.085/0.892): the hull ring frames at (0.87,0.10)-(0.94,0.55) cluster at V 0.086 S 0.440, V 0.157 S 0.324, V 0.243 S 0.318 and V 0.462 S 0.294 — all at H 28-34. 00-INDEX.md independently describes both: 'red-orange box girders' in dock.webp and ring frames in 'dark oxide red' in central corridor.webp.",
        extrapolated="Value 0.379 = lit(0.243) from central corridor's dominant lit ring cluster. Hue 26 deg is the midpoint of the two frames' registers (dock H 13-22, central corridor H 28-34). Saturation 0.301 is set so that truss_steel's own (1.000, 0.980, 0.950) tint carries the rendered surface to S 0.336, which is the mean of the four cleanest lit clusters across the two frames (0.294, 0.318, 0.324, 0.400) — the declared albedo is pulled below the target on purpose so the sheet does not double-count. Roughness 0.45 and specular 0.42 are extrapolated from the specular roll-off visible along the ring tube (the V 0.462 cluster). The 2.5 m truss_steel repeat gives 0.5 m panels, about one per rib face."))
    # ---- steel_heavy ---------------------------------------------------

        # The two-frame differential is what makes this warm rather than
        # neutral, and it is the file's own test applied twice. Within
        # dock.webp the steel holds R/G 1.69-2.12 and R/B 2.09-3.67 across a
        # 2.5x value range while R-B runs 0.040/0.055/0.073 — the RATIO is
        # near-constant and the DIFFERENCE is not, which by the PROVENANCE test
        # is multiplicative, i.e. paint, the opposite signature to the hull's
        # additive blue. The background bay wall in the same region and the
        # same light clusters at rgb(0.034,0.040,0.036) S 0.158 near-neutral,
        # and the gantry platform at (0.240,0.520)-(0.330,0.545) reads rgb
        # 0.277,0.278,0.276 at S 0.006 — dead neutral. So the warm follows the
        # object, not the light. In central corridor.webp the rib measures S
        # 0.21-0.45 against a wall panel beside it at S 0.017 and a similar
        # value: same conclusion, independent frame. This is the one place in
        # the interior where a surface's warmth is the paint rather than the
        # practical, and NEGATIVE_RESULTS is the reason I checked before
        # believing it. One material covers gantry rail, racking run, catenary
        # run, cranes and docking clamp because they are one paint system on
        # one grade of steel at different sections — a crane and the rail it
        # rides are the same surface, and dock.webp shows exactly that assembly
        # as one continuous red-oxide. metallic 0.30 is the worn-coating case
        # and is stated as such: crane wheels rub the rail head, forks rub the
        # racking beam at pallet height, and a docking clamp is walked over —
        # bare steel under a thin coating, which is precisely the exception the
        # physical rule allows. truss_steel is the right sheet because it bakes
        # weld beads on 22% of seams and welded structural steel is what these
        # objects are.
    a(Material(
        "steel_gantry_oxide", "Gantry Steel — oxide-primed heavy structure, handling and plant",
        albedo=(0.300, 0.255, 0.242), roughness=0.52, metallic=0.3,
        specular=0.45, texture="truss_steel", uv_scale=1.0 / 4,
        binds=("fix_gantry_rail", "fix_racking_run", "fix_catenary_run", "crane", "prop_docking_clamp"), scenes=("interior",),
        source="reference/03-sector-blue/dock.webp (authority 1), grey-world gains 0.968/1.027/1.006. The overhead heavy steel — deep box girders and a lattice gantry, which is exactly this family — clusters over (0.02,0.02)-(0.50,0.30) at 27.2% rgb(0.095,0.054,0.040) H 15.0 S 0.577, 20.1% rgb(0.055,0.026,0.015) H 17.1 S 0.729, 14.9% rgb(0.140,0.083,0.067) H 13.1 S 0.520; box girder lit top face (0.300,0.020)-(0.520,0.045) rgb 0.110,0.052,0.036 H 13.5; lattice top chord (0.238,0.133)-(0.423,0.154) rgb 0.068,0.036,0.024 H 16.9. Corroborated in reference/09-garden-core-and-transit/central corridor.webp (gains 1.045/1.086/0.891): ring rib (0.036,0.330)-(0.058,0.405) rgb 0.139,0.077,0.098 H 340 S 0.450, rib clusters H 3.5 S 0.209 and H 345 S 0.110. THE FRAMES DO NOT ESTABLISH THE LEVEL — dock.webp's steel sits at V 0.055-0.140 and is not under the key, so no ratio to a co-lit neutral exists; the value here is set by argument, not measured.",
        extrapolated="The albedo LEVEL (0.300 max channel) and the SATURATION (0.193 against a measured 0.11-0.58). Level: reference/03-sector-blue/dock.webp and station/materials.py's `structural_truss` source line agree that structural steel is the darkest large thing in frame; the library's two existing structural-steel values are 0.260 and 0.204, and painted steel indoors sits just above bare steel outdoors, so 0.300 — 0.65x the corridor wall's 0.46. Saturation: the two frames bracket S 0.11-0.58 and the value sits at the bottom of that bracket because a non-accented surface in this library is capped at 0.20; the remaining chroma belongs to the warm practicals in layer 4. Also extrapolated: the 4 m texture repeat (truss_steel is 5x5 plates per repeat, so 0.80 m plate faces — a girder web's stiffener pitch). Overturned by: any frame showing this steel under a measurable key beside a co-lit neutral, which would fix both the level and the saturation at once."))

        # Three objects, one material, and the merge is the honest call rather
        # than the cheap one: a duct, a riser and a plant column are the same
        # clad-sheet service casing at three sizes, and inventing three
        # separate finishes for three grey boxes nothing in the reference set
        # distinguishes would be invention dressed as detail. Because the sheet
        # is projected triplanar in world space, one uv_scale gives all three
        # the SAME physical sheet size, which is what a real cladding system
        # does. metallic 0.90 is the physical value for bare galvanised sheet
        # and is not the worn-coating case — the roughness of 0.52 is what
        # stops it reading as a mirror overhead in 31 locations and is what
        # galvanising actually looks like. This is the largest group in my
        # family by location count, so it is also the one most likely to be
        # caught being wrong; the source string says plainly that it is
        # unsourced rather than borrowing authority from a frame that does not
        # show it.
    a(Material(
        "clad_services", "Clad Services — sheet-metal duct, riser and plant column",
        albedo=(0.520, 0.525, 0.530), roughness=0.52, metallic=0.9,
        specular=0.55, texture="wall_plate", uv_scale=1.0 / 7.2,
        binds=("fix_service_duct", "fix_service_riser", "fix_plant_column"), scenes=("interior",),
        source="NO FRAME IN THE REFERENCE SET SHOWS A STATION PLANT ROOM, A SERVICE DUCT OR A RISER. reference/08-sector-yellow-engineering/ is empty (only .gitkeep) and reference/00-INDEX.md carries no engineering-interior entry. What IS sourced is what these objects are for: station/rooms.py FIXTURES gives service_duct as an overhead run (0.90/0.60/0.55 m square) in industrial, medical, research and generic rooms, service_riser as a full-height 0.70 m flank in generic rooms, and plant_column as a full-height 1.10 m flank in industrial rooms; station/directory.py places them in air_handling, water_reclamation, waste_processing and power locations. The albedo is a bare-metal F0, not a diffuse reflectance, and is declared invented.",
        extrapolated="Everything: colour, roughness, metallic, and the 7.2 m repeat. Constrained by three things. (1) It must be the PALE element in an industrial room — station/rooms.py puts a 4.6 m furnace stack on the centreline of the same room, and if the flank and the overhead run were also dark the room would have no read at all; contrast between the machine and its services is most of what makes a plant room legible. (2) A metal's albedo is its F0, not a diffuse value, so it sits ABOVE ALBEDO_ANCHOR (0.52 against 0.46) rather than below it — bare steel and zinc F0 are around 0.52-0.58, which is also where `tram_saloon_post` (0.560/0.565/0.580, measured off Babylon_5_2-22_35a.jpg) already sits. (3) 7.2 m repeat: wall_plate is 6 courses per repeat, so 7.2 m gives 1.2 m sections — one flange line per duct length. Overturned by: any frame of a B5 plant room or service riser, which would replace all four numbers at once."))

        # metallic 0.0 is the physical answer and is deliberate: mill scale and
        # heat oxide are dielectrics, and a scorched shell is not bare metal
        # even though it is made of it, so this is NOT the worn-coating case
        # and does not get an intermediate value. roughness 0.78 follows — an
        # oxidised surface scatters. The 2.4 m repeat is derived, not picked:
        # the stack is 2.4 m square, so exactly one texture repeat covers each
        # face and the sheet's plate seams land on the object's own edges
        # instead of wandering across them. This is the object CLAUDE.md's
        # layer-2 note is about — 'Fabrication furnaces was a grey box holding
        # two control podiums and no furnace' — so it is the one fixture in the
        # family where getting the read wrong loses the whole room, which is
        # why it is the darkest thing in it rather than another grey.
    a(Material(
        "steel_furnace_scorched", "Furnace Stack — heat-scorched steel shell",
        albedo=(0.215, 0.198, 0.190), roughness=0.78, metallic=0,
        specular=0.35, texture="truss_steel", uv_scale=1.0 / 2.4,
        binds=("fix_furnace_stack",), scenes=("interior",),
        source="NO FRAME SHOWS A FURNACE OR ANY B5 industrial plant interior — reference/08-sector-yellow-engineering/ is empty. The object is sourced from station/rooms.py FIXTURES: a 2.40 x 2.40 x 4.60 m spine fixture repeated at 4.5 m centres down the centreline of every industrial room, standing in 13 locations including fabrication, waste_red, waste_green and alpha_substation per station/directory.py. The value is placed against two MEASURED library anchors rather than invented free: station/materials.py `truss_steel` at (0.204,0.200,0.181), sampled off Babylon_5_2-22_34b.jpg, and `structural_truss` at (0.260,0.255,0.248), whose source line records it as the darkest thing on the station.",
        extrapolated="The whole surface. Set at luminance 0.201, level with `truss_steel` — the darkest rung of the library's existing value ladder — because a furnace shell is heat-scorched and is the one object in the room that should be darker than the room's own steelwork. It has to be darker than `steel_gantry_oxide` (0.264) or the spine fixture and the flanking racking read as one mass, and it has to be lighter than nothing, because at layer 3 there is no light in the room yet and a value below 0.18 is indistinguishable from an unlit hole. Hue is carried at S 0.116 — half the gantry's — on the argument that a scorched shell keeps some of the warm cast of the steel it is made from but loses saturation to the oxide. Overturned by: any B5 engineering-interior frame at all; this material has the weakest evidence in the family and should be the first thing re-measured if one arrives."))

        # Both frames that show a catwalk show a SOLID deck with a fascia, not
        # open grating, so this is a walkway plate and not a mesh — modelling
        # it as grating would put an alpha-tested surface in the budget for a
        # read the reference does not support. The value is the strongest thing
        # about this material: a ratio between two surfaces under the same
        # light in the same frame is exactly what a screencap can honestly
        # give, and it says a catwalk is about 0.70 of the deck it hangs over,
        # i.e. darker than the finished floor, which is what a service walkway
        # is. metallic 0.30 is the worn-coating case and is stated: a catwalk
        # is a strip of steel that people walk down in one line, and the paint
        # on that line is gone — deck_stud's ORM already inverts roughness on
        # the crowns for exactly this reason, and roughness 0.34 lets the
        # polished tread carry the brightness as specular rather than as
        # albedo, which is the same argument `kit_deck` makes for the corridor
        # floor.
    a(Material(
        "steel_catwalk_tread", "Catwalk — painted walkway plate, tread worn to steel",
        albedo=(0.266, 0.266, 0.270), roughness=0.34, metallic=0.3,
        specular=0.5, texture="deck_stud", uv_scale=1.0 / 0.64,
        binds=("prop_catwalk",), scenes=("interior",),
        source="reference/03-sector-blue/dock.webp (authority 1), balanced 0.968/1.027/1.006: the raised walkway platform at (0.240,0.520)-(0.330,0.545) reads rgb 0.277,0.278,0.276 (S 0.006, V 0.278) against the lit deck beside it at (0.330,0.640)-(0.420,0.680) rgb 0.406,0.379,0.367 and (0.300,0.700)-(0.400,0.760) rgb 0.395,0.387,0.383 — a same-frame, same-light RATIO of 0.278/0.400 = 0.695, which is what is used here. reference/09-garden-core-and-transit/central corridor.webp shows the second catwalk in the set: a two-person-wide mezzanine with a solid fascia beam and a plain two-bar railing, walked on by figures, per reference/00-INDEX.md. Neither frame resolves the tread pattern; that is extrapolated.",
        extrapolated="The tread pattern and its 0.64 m repeat, and the metallic. Pattern: reference/10-interiors-generic-kit/more hallways.jpg shows the deck's service strip as a fine bar grid — roughly 30 bars across the strip at magnification — but that frame establishes no absolute length, so the 40 mm pitch (deck_stud's 16 studs over a 0.64 m repeat, with the sheet's transverse joint every 0.32 m) is derived from assuming a walkway-width strip and is the weak number here. What is NOT extrapolated is the value: 0.695 x the deck's albedo, applied to the mean of the library's two measured decks (`kit_deck` 0.400, `kit_deck_plate` 0.360) = 0.266, so the catwalk moves if the decks move. Overturned by: a frame showing a catwalk beside a scale reference, which would fix the tread pitch."))

        # Seven groups, one material, and the merge is the brief's own example:
        # an office door, a cell door, a lift door and a tram door are the same
        # painted panel at 0.20-0.30 m of thickness, and nothing about
        # thickness changes a surface. The public gallery front and the
        # checkpoint barrier join them because they are the same object too — a
        # flat painted panel standing 1.05 m proud in a room — and giving a
        # courtroom gallery its own material would be three numbers invented to
        # distinguish two boxes. prop_barrier is deliberately NOT
        # chevron-marked: the chevron in this reference set marks physical drop
        # and collision edges (step nosings, ramp lips, bay lips), and a
        # security checkpoint barrier is access control, not a fall hazard;
        # putting hazard stripes on it would be extending a measured rule past
        # what it measures. metallic 0.0 because paint is a dielectric and a
        # door leaf is not rubbed back — unlike the gantry rail and the blast
        # door's leading edge, there is no mechanism here that removes the
        # coating, so this material gets the clean physical zero rather than
        # the worn-coating exception.
    a(Material(
        "door_leaf_painted", "Door Leaf — painted panel: leaves, gallery front, checkpoint barrier",
        albedo=(0.385, 0.385, 0.385), roughness=0.42, metallic=0,
        specular=0.45, texture="wall_plate", uv_scale=1.0 / 4,
        binds=("prop_door", "prop_office_door", "prop_lift_door", "prop_tram_door", "prop_cell_door", "prop_public_gallery", "prop_barrier"), scenes=("interior",),
        source="NO FRAME IN THE SET SHOWS A DOOR LEAF — open, closed or moving. reference/00-INDEX.md states this explicitly against reference/07-sector-grey/grey level 1.webp and records that the leaf mechanism is therefore invented (canon/INVENTIONS.md INV-008). The colour is NOT invented free, though: it is `lit(0.247)` = 0.3852, the balanced value of that frame's DADO PANEL at (0.019,0.563)-(0.134,0.731), run through station/materials.py's single ALBEDO_ANCHOR. The dado is the corridor's set-back flat panel and is the closest measured analogue in the whole reference set to a flat panel standing in a wall build-up. Neutral because NEGATIVE_RESULTS shows that frame's warm dado reading is the downlights, not the paint.",
        extrapolated="That a door leaf takes the dado's albedo rather than the wall's or the frame's. Constrained by: it must read as a SEPARATE PLANE from the `kit_pilaster` jamb it sits inside (0.469) under one light, and 0.385 is 0.82x that — the smallest step that separates two coplanar-ish surfaces without inventing contrast the reference denies. It must not be darker than the reveal (0.140), which is the wall's deliberate shadow gap and the only thing in the build-up meant to read as a hole. The 4 m repeat is NOT extrapolated: it is `kit_wall_plate`'s own repeat, so the leaf's plate courses land on the same 0.67 m pitch as the wall around it, which is what a kit-built station does. Overturned by: any frame showing a leaf, which would replace the value outright."))

        # Kept separate from `door_leaf_painted` because these read differently
        # on screen and not merely at a different thickness: at 6 x 5 m the bay
        # door is the largest single surface any of my groups produces, and its
        # plate courses are legible where an ordinary leaf's are not — one
        # material for both would either give the 6 m door a domestic panel
        # pitch or give the 1.1 m office door a blast door's plating. metallic
        # 0.30 is the worn-coating case, stated: a pressure door's leading edge
        # and rubbing strips run against their seals and frames every cycle and
        # are the one part of a door that goes back to bare steel — the ORM's
        # wear term is keyed to plate edges, which is where that wear
        # physically is. These three sit in fusion_core, war_room, fuel_stores,
        # alpha_substation, hazard_tanks, lowg_bays, vorlon_berth, medlab_one
        # and isolab per station/directory.py — every one of them a volume you
        # are sealed out of, which is what the extra thickness is for.
    a(Material(
        "door_blast_plate", "Blast Door — heavy pressure plate, bay and isolation",
        albedo=(0.320, 0.320, 0.325), roughness=0.48, metallic=0.3,
        specular=0.5, texture="deck_plate", uv_scale=1.0 / 3,
        binds=("prop_blast_door", "prop_bay_door", "prop_isolation_door"), scenes=("interior",),
        source="No frame shows a blast, bay or isolation door leaf — the same gap reference/00-INDEX.md records for every door in the set. What the frames DO establish is the aperture these close: reference/03-sector-blue/dock.webp shows the bay mouth as a very wide, low, flat-topped opening, and reference/03-sector-blue/Minbari Flyer 969 in docking bay 17.webp shows the bay built as stepped plate ledges (both authority 1, per reference/00-INDEX.md). Sizes are from station/rooms.py PROPS: bay_door 6.00 x 0.60 x 5.00 m, blast_door 2.60 x 0.45 x 2.60 m, isolation_door 1.90 x 0.35 x 2.35 m — 0.35-0.60 m of thickness against the ordinary leaf's 0.20-0.22 m. The value is placed on the library's own ladder, not measured.",
        extrapolated="The value, the metallic, and the 3 m repeat. Value 0.320 sits between the painted leaf (0.385) and the gantry steel (0.264): a pressure door is bare or minimally coated plate rather than a finished panel, so it is darker than the leaf, but it is an internal fitting kept clean rather than plant, so it is lighter than the machinery. Repeat: deck_plate is 4x3 plates per repeat, so 3.0 m gives 0.75 m plate courses — a 2.6 m blast door reads as three and a half plates across and a 6 m bay door as eight, which is the build a plate-armoured door actually has and is why deck_plate (large flat plates with recessed seams) is the sheet rather than the finer wall_plate. Overturned by: a frame showing any of these three leaves."))

        # metallic 0.35 is the worn-coating case and is the strongest instance
        # of it in the family: a scrap plate is bare steel under patchy oxide,
        # so the surface is genuinely part metal and part dielectric, and the
        # ORM's wear term distributes that over the plate edges rather than
        # uniformly. roughness 0.82 is the highest in the family because oxide
        # scatters and this plate has no coating to hold a sheen. Merging the
        # makeshift door and the welded door is safe — one is a plate hung over
        # an opening and the other is a plate welded across it, the same
        # material at the same age — and separating them would be two
        # inventions where one will do. This is the material most likely to be
        # wrong, and the source string says so: the reference tree's
        # `06-sector-brown-downbelow/` folder contains nothing but a .gitkeep.
    a(Material(
        "door_scrap_welded", "Scrap Door — welded plate over a Downbelow opening",
        albedo=(0.250, 0.216, 0.203), roughness=0.82, metallic=0.35,
        specular=0.4, texture="truss_steel", uv_scale=1.0 / 1.6,
        binds=("prop_makeshift_door", "prop_welded_door"), scenes=("interior",),
        source="No frame shows either door. What is sourced is WHERE THEY ARE and therefore what they are: station/directory.py places makeshift_door in `thieves_guild` (functions crime, organised_crime, Grey Sector) and welded_door in `welded_shut` (function sealed_volume, Grey Sector) — the station's underclass and its abandoned volumes. reference/00-INDEX.md's Downbelow-adjacent entry for reference/09-garden-core-and-transit/central corridor.webp records exposed structure, litter and practical-only lighting for that register, and reference/10-interiors-generic-kit/more hallways.jpg (authority 1) shows litter on the deck of a service corridor of the same character. The hue is carried from the same oxide family as `steel_gantry_oxide`, whose measurement is in dock.webp; the level is invented.",
        extrapolated="The whole surface. Constrained by: it must be the one door in the family that does NOT look like the others, because that is its entire function in the simulation — a welded plate over an opening is scavenged material, not station stock, and if it renders as another painted leaf then Downbelow reads as the same building as Blue Sector. Value 0.250 puts it below the painted leaf (0.385) and beside the gantry steel (0.264): unpainted plate that has been in a corridor for years. Saturation 0.188 stays inside the library's neutrality cap while keeping the oxide direction the dock measurement establishes for bare station steel. The 1.6 m repeat is derived: truss_steel is 5x5 plates per repeat, so 1.6 m gives 0.32 m plate faces — offcuts, not stock sheet — and truss_steel is the only sheet in the set that bakes weld beads (22% of seams), which is literally what a welded door is. Overturned by: any Brown Sector / Downbelow reference at all, of which this project currently holds none."))

        # This is the one material in my family whose saturation exceeds 0.20
        # without being an ACCENT register value, and it is deliberate: S 0.397
        # is a MEASURED library value that already ships, on a MOVABLE OBJECT
        # rather than a station surface. The neutrality finding is about the
        # station's structural surfaces — walls, decks, ribs, hulls — and a
        # shipping container is livery, which is the same category as
        # `tram_band` (S 0.69) and `hull_banding_red` (S 0.81) already in the
        # file. Reproducing the number rather than softening it is the honest
        # call: dropping it to 0.20 would be discarding an authority-2
        # measurement to satisfy a rule the measurement is not about, and it
        # would leave a hold full of containers reading as more grey boxes in a
        # room whose walls, deck and racking are already grey. metallic 0.0 is
        # a deliberate divergence from `cargo_module`'s 0.15: paint is a
        # dielectric, the 0.15 predates the physical-metallic rule, and 0.15 is
        # exactly the kind of unjustified middle value that rule exists to
        # stop. Called out here rather than left as a silent inconsistency.
    a(Material(
        "container_skin", "Cargo Container — red-brown painted container skin, interior",
        albedo=(0.340, 0.222, 0.205), roughness=0.68, metallic=0,
        specular=0.4, texture="hull_plate", uv_scale=1.0 / 6,
        binds=("prop_container",), scenes=("interior",),
        source="reference/01-station-exterior/exterior more.jpg, dorsal cargo boxes: H 351-5, S 0.25-0.47, V 0.29 — the measurement already recorded in station/materials.py against `cargo_module`, whose albedo (0.340, 0.222, 0.205) is reproduced here EXACTLY rather than re-derived. The same measurement was taken beside a hull the same sheet shows to be neutral (PROVENANCE: saturation falls 0.396 -> 0.038 while R equals G at every level), so the container's colour is a same-frame differential against a neutral reference and belongs to the paint, not the light. A separate material is required only because `cargo_module` is scenes=('exterior',) and prop_container is interior geometry; the colour is not a second opinion.",
        extrapolated="The 6 m texture repeat: hull_plate is 16 plates per repeat, so 6.0 m gives 0.375 m panel pitch. `cargo_module` uses 12 m (0.75 m panels) because it is seen from a kilometre away; a 2.40 x 1.20 x 1.20 m container is seen from two metres in cargo_bays, raw_material and spinal_cargo, so the panel pitch is halved to stay legible at that range. Nothing else here is extrapolated."))

        # roughness 0.07 is below the 0.15 floor and is allowed to be, because
        # this is glass and nothing else in the family goes near it. metallic
        # 0.0 is the physical value — glass is a dielectric — and this is
        # deliberately NOT `tram_glass`'s metallic 0.80, which is a distance
        # hack for a 236 m read and would give a hand's-breadth viewport a
        # chrome sheen. No emission: a viewport does not emit, it shows what is
        # behind it, and putting emission here would be the exact failure mode
        # INV-036's note describes for the hull — a lightbox instead of a
        # window. It is the only untextured surface in the family besides the
        # grab rail, which is the brief's rule for small objects and coated
        # panels applied where it belongs: a trim sheet on a 2.4 m pane would
        # be dirt on glass at any scale.
    a(Material(
        "viewport_glazing", "Viewport — dark glazing onto the drum",
        albedo=(0.040, 0.042, 0.046), roughness=0.07, metallic=0,
        specular=0.92,
        binds=("prop_viewport",), scenes=("interior",),
        source="reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp (authority 1; reference/00-INDEX.md calls it the clearest view of the habitat drum interior the project holds), grey-world gains 0.844/1.075/1.131. It shows a drum office viewport head-on: the glazing carries NO visible tint or veiling reflection — the drum's ground, guideway trusses and lit blocks read through it unattenuated — and it is divided by near-black vertical mullions with a dark sill, measured at (0.560,0.530)-(0.780,0.560) rgb 0.043,0.038,0.067, V 0.067. station/directory.py places prop_viewport in `drum_office` (offices, green sector) and `domed_rotunda` (observation, public_social), which is the same room class as the frame.",
        extrapolated="That the aperture is rendered as one dark, near-mirror surface rather than as transparent glass in a frame. station/rooms.py builds prop_viewport as a single 2.40 x 0.20 x 1.40 m box, so there is no frame member to separate from the pane; the material has to read as 'a window' from that one box. Constrained by: it must be the darkest thing in any room it stands in (0.042 luminance, an order below the door leaf) so it reads as an opening rather than a panel, and roughness 0.07 with specular 0.92 makes it carry the room as a reflection, which is what the measured mullion-and-sill darkness plus an untinted view actually look like from inside. The precedent is `tram_glass`, opaque rather than transparent for the same reason — a sort costs more than it buys. Overturned by: layer 5 splitting the viewport into pane and frame, at which point the pane should become genuinely transmissive and this material becomes the frame's."))

        # This is the brightest and smoothest surface in the family, and it
        # should be — 0.565 luminance against a 0.46 wall, because for a metal
        # the albedo IS the F0 reflectance and not a diffuse value, so it sits
        # above the anchor rather than below it. Untextured on purpose, which
        # is the brief's rule for small objects: the object is a 100 mm tube,
        # and any trim sheet at any repeat would put plate seams on something
        # that has none. It is a one-group material and stays one because
        # nothing else in the family is polished bare tube — merging it into
        # the catwalk (painted, worn, metallic 0.30) or the clad services
        # (galvanised sheet, roughness 0.52) would lose the single read that
        # matters here, which is that in a micro-g bay the thing you can reach
        # for is the thing that catches the light.
    a(Material(
        "grab_rail_bare", "Grab Rail — polished bare tube, micro-gravity handhold",
        albedo=(0.560, 0.565, 0.580), roughness=0.22, metallic=0.9,
        specular=0.65,
        binds=("prop_handhold",), scenes=("interior",),
        source="reference/03-sector-blue/Babylon_5_2-22_35a.jpg (authority 1), balanced 0.913/1.090/1.013 — the tram saloon's vertical stanchions, the only object in the whole reference set that is a metal pole a person grips. station/materials.py already carries that reading as `tram_saloon_post` (0.560, 0.565, 0.580), whose source line records that the poles read as bare metal against the painted panels and shows a specular roll-off along their length. The value is reproduced here rather than re-derived. station/rooms.py sizes prop_handhold at 0.60 x 0.10 x 0.10 m, wall-mounted, and station/directory.py places it only in `lowg_bays`, `zerog_maint` and `micro_g_bays` — every one a microgravity_handling or repair volume.",
        extrapolated="metallic 0.90 and roughness 0.22, both raised from `tram_saloon_post`'s 0.75 and 0.28. The 0.75 is itself declared an extrapolation in station/materials.py ('the frame shows a specular roll-off along the pole, which fixes the kind but not the value'), and the physical rule is that bare metal is 0.9-1.0 and an intermediate value needs a worn-coating argument this object cannot make — it has no coating. Roughness drops to 0.22 on a specific argument: this is the only object in the station gripped by every occupant of a zero-g bay on every transit, and a handrail polished by constant use is smoother than a tram stanchion held occasionally. Overturned by: a frame showing a micro-g handhold, which the set does not contain."))

        # This is the best-evidenced thing in my family and the only place a
        # saturated accent belongs in it: an ACCENT register value, on an
        # object whose entire function is to be seen and not stepped over.
        # fix_platform_edge is a 0.45 x 0.22 m nosing flanking a transit hall —
        # station/rooms.py builds it as the drop at the guideway — and the
        # reference's rule is that the station marks step and ramp edges this
        # way. I deliberately did NOT extend it to prop_barrier: the frames
        # mark FALL and COLLISION edges, and a security checkpoint barrier is
        # access control, so binding it here would be stretching a measured
        # rule past what it measures; that group went to door_leaf_painted
        # instead. metallic 0.05 and roughness 0.62 are taken verbatim from the
        # existing `hazard_chevron` material so the interior and exterior
        # chevron differ ONLY in scene and repeat — a separate material is
        # needed at all solely because `hazard_chevron` is
        # scenes=('exterior','drum') and this geometry is interior. Note for
        # the applier: hazard_chevron is in COLOUR_SHEETS, so emitted_albedo()
        # writes albedo_color white and Material.albedo keeps the measured
        # colour — same as the exterior sibling, no special handling.
    a(Material(
        "edge_chevron_nosing", "Edge Nosing — yellow/black chevron on the platform drop",
        albedo=(0.900, 0.720, 0.060), roughness=0.62, metallic=0.05,
        specular=0.4, texture="hazard_chevron", uv_scale=1.0 / 2.4,
        binds=("fix_platform_edge",), scenes=("interior",),
        source="reference/03-sector-blue/Minbari Flyer 969 in docking bay 17.webp (authority 1): the bay wall is a stepped ziggurat of ledges and EVERY STEP NOSING CARRIES YELLOW/BLACK HAZARD CHEVRONS — reference/00-INDEX.md records this and draws the consequence explicitly, that the chevron is applied by rule to all step edges and is therefore a generator rule rather than a decal placement. Corroborated by reference/03-sector-blue/dock.webp, which shows the same marking on the ramp edges of the bay deck, and by reference/01-station-exterior/Cobra Bays with starfurries.webp on the bay lip. The albedo is ACCENTS['hazard_yellow'] (0.900, 0.720, 0.060), the value station/materials.py already measured off dock.webp's deck chevrons; this is the same register, not a second one.",
        extrapolated="The stripe pitch, and that a tram platform edge is a step edge in the sense the rule means. Pitch: a Fourier scan along dock.webp's lower ramp chevron run, source pixels (248,505) to (315,556), puts the stripe peaks at k = 6-8 over a 67 px horizontal extent; at the scale reference/00-INDEX.md measures in that frame (the red deck disc, 156 px = 9.4 m, so 16.6 px/m) that run is 4.0 m and the cycle is 0.50-0.67 m. uv_scale 1/2.4 gives 4 cycles per repeat = 0.60 m, inside that bracket, against the exterior sibling's declared-invented 0.75 m. So this measurement also CORROBORATES the exterior material's guess. Overturned by: a frame showing a station transit platform, of which the set holds none."))

    # ---- furnishing ----------------------------------------------------

        # This is the station's default furniture carcass and it takes seven of
        # my thirty-five groups, so getting it wrong is worse than getting any
        # other one wrong. Two decisions carry it. METALLIC 0.0 — it is paint
        # on steel, not steel; the specular of an enamelled panel is dielectric
        # and giving it a metal response would make every desk in the station
        # read as bare aluminium. And it sits BELOW the wall it stands against,
        # not above: a room is legible because its furniture separates from the
        # surface behind it, and the corridor wall is 0.460. Roughness 0.45 is
        # satin enamel — smoother than the wall plate's 0.56 because a painted
        # furniture panel is sprayed and a wall panel is not, which is also why
        # it takes no texture: it is a coated panel, and the same reason
        # `radiator` ships untextured. The seven groups merge because they are
        # one object at seven sizes — a desk, a duty desk, a service counter,
        # an issue counter, a locker bank, a lab bench and a fume enclosure are
        # all a sprayed steel carcass at desk-to-2.6 m scale, and nothing on
        # screen would separate them. What I deliberately did NOT merge into it
        # is the servery and the workshop bench: those are bare metal, and bare
        # metal is a different BRDF, not a different colour.
    a(Material(
        "furn_casework", "Furniture Casework — painted steel desk, counter and locker bodies",
        albedo=(0.400, 0.396, 0.388), roughness=0.45, metallic=0,
        specular=0.5,
        binds=("prop_desk", "prop_duty_desk", "prop_counter", "prop_issue_counter", "prop_parcel_locker", "prop_lab_bench", "fix_fume_column"), scenes=("interior",),
        source="05-sector-green/council chambers.webp, balanced (gains 0.998/1.082/0.932): the council bench's plain grey frame (0.160,0.560)-(0.195,0.680) rgb(0.258,0.272,0.267) S 0.063, and the same bench's lit slab top (0.460,0.420)-(0.600,0.450) rgb(0.630,0.649,0.672) S 0.065. That bench is the only piece of station casework in the whole reference set measured square-on under a mild cast, and 00-INDEX.md reads its construction directly — 'a grey slab top with a chamfered edge', 'set in a plain grey frame with a bottom kick rail', 'a recessed plinth'. NO FRAME EXISTS of an office desk, a post-office counter, a quartermaster's issue counter, a parcel locker, a lab bench or a fume column.",
        extrapolated="The level, and the extension from one ceremonial bench to seven working units. The council bench brackets rather than fixes it — 0.63 lit against 0.27 in shadow — because 00-INDEX.md records that chamber as deliberately lit asymmetrically ('the fan-and-medallion side is bright, the opposite wall ... almost no fill'), so neither end is the albedo. 0.400 is chosen as one rung below ALBEDO_ANCHOR and it is inside the corridor kit's own measured ladder: the kit's darkest lit element, the dado, is lit(0.247) = 0.385, and its wall is 0.460. Overturned by any frame of a working office or issue counter, or by a frame containing a reflectance standard."))

        # The thing that nearly went wrong here is worth recording. In more
        # zocalo.png the furniture reads plainly blue-white and the ratio test
        # appears to confirm it — the same pedestal at V 0.498 and V 0.718
        # holds B/R at 1.176 and 1.212, constant across a 1.44x range, which is
        # the signature of a tinted surface rather than a tinted light. But the
        # deck tile in the same frame holds B/R 1.158, and the library already
        # calls that deck neutral-to-warm. Everything in the frame is at B/R
        # 1.16-1.21, so the blue is the frame and the concourse's cool ambient,
        # and the furniture is neutral to within 4% of the deck. Third time
        # this project has caught that; the only reason I caught it is that
        # materials.py insists on a same-frame control. What survives is the
        # small cool bias, and it survives because garden.png shows it as a
        # DIFFERENCE between two surfaces in one light rather than as a
        # property of the whole frame. Untextured because these are moulded,
        # not plated: 00-INDEX.md reads the Zocalo pedestals and chair backs as
        # 'white drums carrying a large outlined 5', and a plate seam across a
        # moulded drum would be a lie. Roughness 0.40 — smoother than casework,
        # because the frames show a soft broad highlight rolling round the
        # drums, which is a gel-coat and not a spray. `prop_bench` belongs here
        # rather than with anything softer because the geometry is 1.80 x 0.45
        # x 0.45, a backless slab — exactly the object garden.png shows, so the
        # mesh and the reference agree without any argument.
    a(Material(
        "furn_pale_composite", "Moulded Composite Furniture — café tables, chairs and slab benches",
        albedo=(0.402, 0.412, 0.432), roughness=0.4, metallic=0,
        specular=0.5,
        binds=("prop_table", "prop_bench"), scenes=("interior",),
        source="Three frames, three independent anchors. (a) 04-sector-red/more zocalo.png, raw: the pedestal café table's top (0.515,0.706)-(0.580,0.731) reads 0.592/0.600/0.718 and the concourse deck tile beside it (0.237,0.652)-(0.287,0.712) reads 0.596/0.573/0.690 — two up-facing surfaces equal in value to within 4%, so against `kit_deck_plate`'s 0.360 the furniture is 0.375. (b) 04-sector-red/Casino.webp, balanced: a small round café table (0.524,0.547)-(0.579,0.575) rgb(0.410,0.441,0.425) S 0.092, scaled by that frame's mural-wall anchor (balanced 0.491 -> ALBEDO_ANCHOR) gives 0.413. (c) 09-garden-core-and-transit/garden.png, raw: a 'low white slab bench' (0.495,0.936)-(0.635,0.962) 0.624/0.643/0.686, scaled x0.667 by the lawn anchor gives 0.416/0.429/0.458. Mean of the three, 0.415. The cool bias is measured, not styled: in garden.png the bench slab runs B-R +0.063 while the paving two metres away under the same key runs B-R -0.041, a 0.104 swing between two surfaces in one light.",
        extrapolated="Only the reconciliation. The three anchors span 0.375 to 0.458, a 22% spread, and 0.432 sits inside it; one frame containing a reflectance standard collapses the spread. Also extrapolated: that the Zocalo's café furniture, the Casino's round tables and the Garden's slab benches are one material. They are three sets in three sectors; what ties them is that all three measure pale, near-neutral and slightly cool, and that the modelled objects are the same objects."))

        # Merging a bar counter with a garden pool coping looks like
        # over-merging until you read what the index calls them: 'dark stone
        # bar counter' and 'dark stone coping'. They are the same surface, and
        # both frames show the same tell — a hard specular streak running along
        # the top arris with the body of the stone going near-black beside it.
        # That is what roughness 0.24 and specular 0.60 reproduce, and it is
        # the whole reason this material is not just a dark colour: at 0.094
        # albedo, everything you actually see is the specular. It also gives
        # the hospitality set its one genuinely dark object, which matters
        # because the Casino, the Zocalo bar and Doug's Dugout are all dim
        # rooms where the bar is the darkest thing in frame and the light sits
        # on top of it. RED FLAG I AM RAISING RATHER THAN PAINTING OVER: the
        # Zocalo counter's pale rectangular inlays are the best-observed detail
        # on this surface and no existing trim sheet can produce them, so this
        # ships untextured and the detail is lost until a sheet exists. And
        # 0.094 is dark enough that it will look like a hole in any render that
        # is not exposed for the bar — that is correct, and it is what the
        # frames show, but a reviewer should expect it.
    a(Material(
        "furn_dark_stone", "Dark Polished Stone — bar counters, back fittings and pool copings",
        albedo=(0.094, 0.092, 0.093), roughness=0.24, metallic=0,
        specular=0.6,
        binds=("prop_bar_counter", "fix_back_shelving", "prop_pool_edge"), scenes=("interior",),
        source="Both objects are called dark stone by the index and both measure near-black. (a) 11-props-and-technology/Zocalo neon signage in background.jpg — 00-INDEX.md: 'a dark stone bar counter inlaid with small pale rectangles'. Balanced, an 8-way cluster over the counter band (0.0,0.80)-(1.0,1.0) gives 29.3% at V 0.082, 28.9% at V 0.060, 16.2% at V 0.034, with the pale inlays at V 0.127-0.389. (b) 09-garden-core-and-transit/garden.png — 00-INDEX.md: 'rectangular reflecting pool with a dark stone coping'. Raw (0.535,0.850)-(0.579,0.868) 0.129/0.078/0.086; removing that frame's measured additive warm key (the paving holds R-B at +0.041 and +0.039 across a 1.63x value range, so it is additive) leaves 0.088/0.074/0.086, and the lawn anchor x0.667 leaves 0.059/0.049/0.057. (c) Cross-check, 04-sector-red/Casino.webp balanced: the bar's front face (0.300,0.430)-(0.500,0.450) V 0.197, the brightest of the three and under green spill.",
        extrapolated="The single level for three groups. The evidence spans 0.055 (garden coping, corrected) to 0.197 (Casino bar face under spill), and 0.094 sits inside it. The coping figure is a lower bound because the measured strip includes the coping's own shadowed return face, which no albedo should carry. Also extrapolated: that a bar's back fitting is the same surface as its counter — no frame shows a back fitting clear of bottles and glassware; both frames that show one show it dark."))

        # Deliberately identical in value to `tram_saloon_seat`, because it IS
        # `tram_saloon_seat` seen from `rooms.py` instead of from the tram
        # module — if a later pass merges the two, nothing changes and nothing
        # was lost. Kept as its own entry only because the fragments differ and
        # I may not edit the existing material. This is one of the two surfaces
        # in my family allowed above saturation 0.20, and it is allowed on the
        # terms materials.py already set: S 0.400 at H 5 sits in the `maroon`
        # accent register, and the register exists precisely because the
        # reference shows exactly two populations in that car — a near-neutral
        # shell at S 0.11-0.14 and a red soft-goods set at S 0.22-0.59.
        # Upholstery is genuinely accented; it is the one thing in a grey
        # station that is allowed to be a colour. Roughness 0.90 rather than
        # the tram entry's 0.88 because this also covers bedding, which is the
        # roughest surface anywhere in the library. Specular 0.25: cloth has
        # almost no specular lobe, and giving it the default 0.5 is what makes
        # cheap renders look like vinyl.
    a(Material(
        "furn_upholstery", "Soft Goods — maroon seat and bunk upholstery",
        albedo=(0.375, 0.237, 0.225), roughness=0.9, metallic=0,
        specular=0.25,
        binds=("prop_seat", "prop_bunk"), scenes=("interior",),
        source="03-sector-blue/Babylon_5_2-22_35a.jpg, authority 1, already measured and already in this library: the lit cushion cluster, balanced (gains 0.913/1.090/1.013), rgb(0.375,0.237,0.225) H 5 S 0.401, 10.4% of the saloon. 00-INDEX.md reads that frame as 'bench and individual seating in red-maroon upholstery on moulded grey bases'. Five of the seven locations that declare `prop_seat` — ground_tram, drum_tram, core_shuttle, shuttle_car — ARE that vehicle, so for most of its uses this is not an analogy, it is the same seat. No frame shows a bunk.",
        extrapolated="That a bunk mattress and blanket take the seat's cloth. What constrains it: the station's only measured soft goods are this maroon set, quarters are fitted out by the same authority that fits out the transit cars, and a second invented colour for bedding would be unmarked invention where a sourced one exists. Overturned by any frame of crew or civilian quarters."))

        # Three objects that are all sheet stainless because of what they DO,
        # not what they look like: a hot servery, a tray stack and a mortuary
        # cold drawer are all wipe-down food-or-tissue-contact metal, and every
        # one of them would be stainless in a real installation for the same
        # reason. That is a better argument than a colour match, and it is why
        # they merge. METALLIC 1.0 is the whole point — this is the only bright
        # bare metal in the furnishing family, and at metallic 1.0 with
        # roughness 0.31 it will pick up and throw back the room's practicals,
        # which is exactly how a servery reads in a dim mess hall and is
        # something no diffuse grey can imitate. I have kept it clearly apart
        # from `furn_shop_steel`: a servery and a scarred workbench are both
        # steel and read nothing alike, so per the brief they are two
        # materials, not one. Untextured because a brushed finish is a
        # sub-millimetre anisotropy and the seven available sheets are all
        # plate patterns — tiling `truss_steel` across a servery front would
        # put structural weld seams on a food counter.
    a(Material(
        "furn_service_steel", "Service Stainless — servery, tray stack and mortuary drawers",
        albedo=(0.560, 0.565, 0.575), roughness=0.31, metallic=1,
        specular=0.5,
        binds=("prop_serving_counter", "prop_tray_dispenser", "prop_cold_drawer"), scenes=("interior",),
        source="NO FRAME SHOWS A STATION SERVERY, TRAY DISPENSER OR MORTUARY DRAWER. What is sourced is that bright chrome is the station's food-service metal: 00-INDEX.md on 04-sector-red/more zocalo.png reads the tableware as a 'chrome domed-top shaker and stacked tumblers', and the shaker is visible in frame at (0.55,0.50)-(0.64,0.72) as a hard specular cylinder with no diffuse term. The library's only measured bare-metal furniture, `tram_saloon_post` from the same authority-1 frame set, sits at 0.560/0.565/0.580 roughness 0.28.",
        extrapolated="Everything except the kind of surface. The albedo is the physical F0 of stainless steel, ~0.56 and very slightly cool, not a screen measurement — for a conductor the albedo IS the specular reflectance, so this is the one case where physics fixes the number better than a screencap could. Roughness 0.31 is a directionally brushed 2B/4 finish. Overturned by any frame of the mess hall servery or a medlab."))

        # METALLIC 0.95, and I have to justify it rather than leave it in the
        # forbidden band: this is bare metal with a thin oxide, not metal under
        # a coating, and 0.95 rather than 1.0 only acknowledges the oxide film
        # and the grime that a working shop puts on everything. If any of these
        # four turns out to be painted in a frame, the correct fix is to move
        # that group to `furn_casework`, not to slide the metallic value down —
        # a half-metallic surface is a rendering error, not a compromise. This
        # is the one furnishing material that takes a texture, and it earns it:
        # `truss_steel` at a 1.2 m repeat puts plate grain and weld runs across
        # a 2.0 m bench and a 2.4 m rack at roughly the right frequency for the
        # surfaces the sheet was authored for, and these are the only objects
        # in my family big enough and flat enough to show it.
        # `fix_cell_divider` sits here rather than with the office partition
        # because a brig divider is 0.30 m thick and full height — that is a
        # structural steel partition, and it should read as heavier than
        # anything else in the room.
    a(Material(
        "furn_shop_steel", "Utility Steel — benches, racks and cell dividers, unpainted",
        albedo=(0.470, 0.466, 0.458), roughness=0.58, metallic=0.95,
        specular=0.5, texture="truss_steel", uv_scale=1.0 / 1.2,
        binds=("prop_workbench", "prop_tool_rack", "prop_grow_rack", "fix_cell_divider"), scenes=("interior",),
        source="NO FRAME SHOWS A WORKSHOP BENCH, TOOL RACK, GROW RACK OR BRIG DIVIDER. Bracketed against the library's own measured steel registers, which come from authority-1 exterior and drum frames: `truss_steel` 0.204/0.200/0.181 (34b lattice), `greeble_fitting` 0.310/0.306/0.300 (exterior more.jpg dorsal fittings), `tram_saloon_post` 0.560/0.565/0.580 (35a poles). Those are painted or coated structure; unpainted mill and galvanised steel sits above them.",
        extrapolated="The whole surface. What constrains it: these four objects are the station's unpainted utility steelwork — a bench top scarred back to bare metal, an open tool rack, a wet galvanised grow rack, a heavy brig divider — and the painted register already exists next door in `furn_casework`, so anything that would be sprayed goes there and only what would not comes here. 0.470 is below the servery's 0.560 because scuffed and oxidised steel loses reflectance, and roughness 0.58 is twice the servery's because a workshop surface is abraded in every direction. Overturned by any frame of maintenance, hydroponics or the brig."))

        # Four groups merge because a medlab is fitted out as one system: a
        # diagnostic bed, a wall cabinet, a cryo pod and an equipment gantry
        # are the same sealed coated shell at four shapes, and the show's
        # medical spaces read as a single fit-out rather than as assembled
        # parts. The one deliberate departure from every other material I am
        # proposing is that this one is BRIGHTER than the wall. That is the
        # only lever available to make a medlab feel different from a store
        # room when both are grey boxes at layer 3, and it is what the lighting
        # layer will amplify — a clinical room reads clinical because its
        # surfaces return more light than the corridor outside it, not because
        # they are white. Roughness 0.33 and specular 0.55 give the broad soft
        # sheen of a sealed polymer; metallic 0.0 because a wipe-clean clinical
        # surface is a coating over whatever is underneath. Untextured,
        # deliberately: any plate seam is a dirt trap, and a clinical surface
        # that shows plating would be wrong in a way a viewer would feel
        # without being able to name.
    a(Material(
        "furn_clinical", "Clinical Fit-out — beds, cabinets, pods and equipment gantries",
        albedo=(0.500, 0.512, 0.535), roughness=0.33, metallic=0,
        specular=0.55,
        binds=("prop_diagnostic_bed", "prop_medcabinet", "prop_cryo_pod", "fix_equipment_gantry"), scenes=("interior",),
        source="THERE IS NO MEDICAL INTERIOR ANYWHERE IN reference/. 03-sector-blue/ holds command and control, the war room, a docking bay, a Minbari flyer and four drum CGI plates; no medlab, no infirmary, no morgue, no cryo bay, and no other folder holds one either. Nothing here is measured. The one thing borrowed from a measurement is the SHAPE of the tint: 03-sector-blue/Babylon_5_2-22_35a.jpg's saloon panelling, balanced rgb(0.486,0.486,0.546), is the library's only near-neutral surface that measures cool rather than warm-neutral (B/R 1.12), and this uses the same 1.07 ratio at a lower strength.",
        extrapolated="All four numbers, and I am marking this the weakest material in the family. What constrains it: it must sit near ALBEDO_ANCHOR to belong to the same station (0.535 is 1.16x the wall, the only surface in my family placed ABOVE the wall); it must be wipe-clean, which fixes roughness low and forbids a texture; it must not be white, because nothing in a lived-in station stays at 0.8 and a white medlab is the Star Trek reading the brief rules out; and the cool bias must be small enough to stay inside the neutral band at S 0.065. ONE MEDLAB FRAME OVERTURNS ALL OF IT, and this is the single highest-value reference gap in the furnishing family — six medlabs, a morgue and cryo storage depend on it."))

        # This is the darkest structural thing in my family and that is the
        # point of it: the market reads as lightweight goods hung on a nearly
        # invisible frame, which is what 'built as lightweight structures
        # inside a hard architectural shell' means, and a mid-grey armature
        # would turn a stall into a booth. Two frames in two sectors both put
        # the station's tube furniture at 0.05-0.11, which is a real black
        # paint and not a shadow — the council chair reading is under a bright
        # key. METALLIC 0.0: black-painted tube is paint, and the hoops in more
        # zocalo show a single hard specular line running the length of the
        # tube with no coloured metal response beneath it, which is a
        # dielectric gloss. Roughness 0.32 reproduces that line. Untextured — a
        # 40 mm tube has no room for a trim sheet, and at that albedo nothing
        # would be visible anyway. Split from `furn_stall_canvas` because the
        # frames plainly show two things: a dark armature and a pale canopy,
        # and merging them would produce a grey mush that matches neither.
    a(Material(
        "furn_stall_frame", "Market Armature — black tube stall frames and awning rails",
        albedo=(0.075, 0.074, 0.074), roughness=0.32, metallic=0,
        specular=0.5,
        binds=("fix_stall_frame", "fix_awning_rail"), scenes=("interior",),
        source="04-sector-red/more zocalo.png, raw: the black tubular hoop round a café pedestal (0.455,0.824)-(0.530,0.840) reads 0.094/0.063/0.090, and against that frame's deck anchor (deck tile raw V 0.690 -> `kit_deck_plate` 0.360, x0.522) that is 0.049. Cross-check in a second frame and a second sector: 05-sector-green/council chambers.webp balanced, the chair's black square-section lattice (0.435,0.160)-(0.455,0.250) rgb(0.106,0.102,0.117), scaled by that frame's floor-mosaic reference gives 0.109. 00-INDEX.md reads the Zocalo stall canopies as 'fabric on radiating spars, parasol-fashion' and 09-garden-core-and-transit/central corridor.webp shows a vendor front as 'backlit orange-red panels behind vertical mullions over a counter' — the market's structure is a slender armature in both.",
        extrapolated="The level within the 0.049-0.109 bracket the two frames give; 0.075 is the midpoint. Also extrapolated: that the Zocalo's black tubework, measured on café furniture, is the same finish as the stall armature beside it. What supports it is that both are the same lightweight tube in the same concourse, and that no other dark furniture finish appears anywhere in the set."))

        # `prop_stall` is the whole 1.8 x 1.2 x 2.1 m stall — canopy, frame and
        # goods in one box — and the surface that identifies it at any distance
        # is the canvas, so the canvas is what it gets. Roughness 0.92 is the
        # second-roughest material in the family after bedding, and it is doing
        # real work: the market must read as the only soft, matte,
        # light-absorbing thing in a station otherwise made of plate and paint,
        # and that contrast is most of what makes a concourse feel like a
        # market rather than a corridor with boxes in it. Specular 0.30 for the
        # same reason — woven cloth has almost no coherent lobe. The one
        # location that declares this group is `black_market` in Grey Sector,
        # which is not the Zocalo; I am extending the Zocalo's market fabric to
        # it deliberately, because a black-market stall is the same makeshift
        # construction pitched somewhere it should not be, and the difference
        # between the two is lighting and siting, not cloth.
    a(Material(
        "furn_stall_canvas", "Stall Canvas — awning fabric and stacked goods",
        albedo=(0.380, 0.345, 0.312), roughness=0.92, metallic=0,
        specular=0.3,
        binds=("prop_stall",), scenes=("interior",),
        source="04-sector-red/more zocalo.png, the stall canopy at (0.625,0.122)-(0.670,0.143) and a second panel at (0.730,0.115)-(0.775,0.136): raw 0.212/0.137/0.137 and 0.197/0.129/0.137, H 20-23. 00-INDEX.md on the same frame: 'Market stalls with fabric awnings, string lighting and hanging goods'; 'Stall canopies are fabric on radiating spars, parasol-fashion'; and on the lighting, 'warm practicals at stall level, cyan neon accents above, low ambient fill'.",
        extrapolated="The level, and most of the warmth. The measured patches sit ABOVE the stall practicals in the frame's dim ceiling zone, so their V 0.20 is a lighting floor, not an albedo — carrying it through the frame's x0.522 deck anchor would give 0.111, which is a black awning, and that is plainly not what the frame shows. 0.380 is a tan canvas raised to the level a fabric under a practical would need to read as the frames do. The hue is kept but pulled back to S 0.179, just inside the neutral band, because the index says the light at stall level is warm and an unknown share of the measured H 20-23 is that light rather than the cloth. Overturned by a frame of a stall canopy lit from the front."))

        # The second of the two surfaces in my family above saturation 0.20,
        # and it earns it the same way the tram upholstery does: it is a
        # deliberately coloured cloth, it lands at H 216-219 against the
        # `cool_blue` register's H 228, and the same-object control rules out
        # the lighting. A casino table is supposed to be the one saturated
        # object in the room. Roughness 0.95 — baize is the flattest diffuse
        # surface that exists, and a table that catches any specular reads as
        # plastic. CAVEAT THE NEXT LAYER MUST KNOW: `rooms.build` emits
        # `prop_gaming_table` as a single 1.60 x 1.10 x 0.78 box, so this blue
        # will cover the apron and the padded rail too, which the frame shows
        # as dark with a lit chase around it. I bound the identifying surface
        # rather than averaging the two, because an averaged mid-blue would
        # match neither; splitting the box is a layer-2 fix and is worth
        # making, since this is one of only two prop types in the whole station
        # that is allowed to be a colour.
    a(Material(
        "furn_gaming_baize", "Gaming Baize — the casino table cloth",
        albedo=(0.138, 0.276, 0.483), roughness=0.95, metallic=0,
        specular=0.25,
        binds=("prop_gaming_table",), scenes=("interior",),
        source="04-sector-red/Casino.webp, balanced (gains 1.014/1.071/0.926): the felt (0.264,0.583)-(0.377,0.630) rgb(0.147,0.294,0.515) H 219 S 0.686 V 0.515, scaled x0.937 by that frame's mural-wall anchor (balanced V 0.491 -> ALBEDO_ANCHOR). 00-INDEX.md calls it 'a blue-felt gaming table on a raised kerb'. The proof that the blue is the cloth and not the room: the SAME table's apron, 0.05 of frame height below the felt and under the same light, reads (0.270,0.660)-(0.400,0.700) rgb(0.099,0.084,0.102), B/R 1.02 — dead neutral — while the felt is at B/R 3.50. One object, one light, two hues.",
        extrapolated="Nothing about the colour. The level rides on the mural-wall anchor, which assumes the Casino's back wall is a wall-class surface at ALBEDO_ANCHOR; if it is not, this scales with it. The saturation may be a few points high because the Casino is lit with strong coloured practicals, but the apron control caps how much of it can be light."))

        # This is the one material in my family placed slightly above the wall
        # for a reason that is about mood rather than physics: a sanctuary is a
        # room where the furniture is the architecture — a pew and a dais are
        # cut stone, not casework — and stone that is lighter and matter than
        # the corridor is what separates a chapel from an office at the moment
        # a player walks in. Roughness 0.66 is honed, not polished; it is the
        # deliberate opposite of `furn_dark_stone`'s 0.24, and the pair of them
        # gives the station two stones that behave in opposite ways under one
        # light. Untextured because none of the seven sheets is a stone:
        # `deck_plate` would put a mechanical slab grid across a pew, which
        # reads as decking. `fix_dais` is 3.20 x 1.60 x 0.35 — a platform, not
        # a lectern — and the council bench is the station's own precedent for
        # what a raised speaking place is made of, which is why I used it for
        # the form even though it belongs to a bespoke module.
    a(Material(
        "furn_worship_stone", "Worship Stone — pews and the sanctuary dais",
        albedo=(0.468, 0.462, 0.432), roughness=0.66, metallic=0,
        specular=0.4,
        binds=("prop_pew", "fix_dais"), scenes=("interior",),
        source="05-sector-green/rotunda.webp, the only worship-class interior in the set, balanced: the floor's cream-and-grey radiating mosaic (0.550,0.900)-(0.680,0.970) rgb(0.439,0.457,0.398) S 0.140 V 0.457. 00-INDEX.md reads that room as a 'stepped, coffered dome in gold and grey' over a 'circular mosaic with a radiating sunburst in cream and grey'. Corroborating the form of a raised speaking platform, 00-INDEX.md on 05-sector-green/council chambers.webp: a faceted raised bench with 'a grey slab top with a chamfered edge', a riveted bullnose capping rail and 'a recessed plinth holding the whole bench off the floor'. NO FRAME SHOWS A PEW, A CHAPEL OR A SANCTUARY DAIS.",
        extrapolated="That a sanctuary's furniture is cut from the same pale stone as a rotunda's floor, and the small warm bias. The bias is the weakest part: rotunda.webp's grey-world gains are 0.766/1.153/1.208, extreme enough that hue from it is soft, so S is held to 0.077 — about half the measured 0.140 — on the argument that some of the cream is the room's very warm key. The level, 0.468, is the measured mosaic value taken at face value, which is legitimate here only because it lands within 2% of ALBEDO_ANCHOR from an entirely independent direction. Overturned by any frame of a chapel or sanctuary."))

        # Merged because they are the same object at two heights — a 0.16 x
        # 1.80 x 1.75 m office divider and a 0.22 x 2.60 m full-height
        # sanctuary screen are one panel system, and nothing on screen would
        # separate them; keeping them apart would have meant inventing two sets
        # of numbers from the same zero evidence, which doubles the invention
        # for no gain. Roughness 0.30 with specular 0.45 gives a
        # translucent-composite sheen rather than a matte board, which is what
        # makes a screen read as a screen when it is only a thin box. THE
        # OBVIOUS NEXT MOVE, and I am flagging rather than taking it: every
        # frame that shows a divider in this station shows it BACKLIT. I have
        # not given this emission because no frame shows either of these two
        # specific objects, and inventing an emitter is a larger claim than
        # inventing a colour. If layer 4 wants the station's screens lit — and
        # on this evidence it should — the right fix is a lit variant with its
        # own group, not raising the emission on a material that also has to
        # serve a cubicle partition in an administration office.
    a(Material(
        "furn_screen_panel", "Panel Screen — office partitions and sanctuary screens",
        albedo=(0.505, 0.508, 0.515), roughness=0.3, metallic=0,
        specular=0.45,
        binds=("fix_screen_panel", "fix_partition_screen"), scenes=("interior",),
        source="NO FRAME SHOWS AN OFFICE PARTITION OR A SANCTUARY SCREEN. What is sourced is that thin light-passing panels are the station's idiom for dividing a space without closing it: 00-INDEX.md on 05-sector-green/rotunda.webp records 'wall panels of vertical blue light slots' and hanging banners between columns; on 05-sector-green/council chambers.webp, a 'very fine square-hole perforated sheet ... evenly backlit with no visible lamp hotspots'; on 04-sector-red/Earhart's.webp, 'wood-slat screens' read through the glazed band; and on 05-sector-green/conference aerea.webp, 'arrays of tall narrow illuminated slots'.",
        extrapolated="All four numbers. What constrains them: the panel must read as thinner and lighter than the wall behind it or it is a wall (hence 0.515, just above ALBEDO_ANCHOR, and the lowest saturation in the family at 0.019); it is 0.16-0.22 m thick in the geometry, which is a panel and not a partition wall; and it must be smooth, because a translucent screen with plate texture is a contradiction. Overturned by any frame of an office interior or a chapel."))

        # The only emitter I am proposing, and it emits because the frame shows
        # it emitting — it clips to white in a room where nothing else does. It
        # is also the reason this material exists at all rather than being
        # folded into `furn_worship_stone`: a sanctuary needs one point of
        # light or it is a dark box, and this is the station's own answer to
        # what that light looks like. The near-black blue body is measured, and
        # it is built the way the library already builds emitter housings —
        # `emissive_signage` at (0.050,0.090,0.100), `marker_light_red` at
        # (0.100,0.050,0.040), `light_downlight` at (0.300,0.240,0.190) all
        # carry their emission's tint in the albedo, because a housing sits in
        # its own light. That is why its S 0.409 is not a coloured structural
        # surface. The independent arrival of the rotunda altar at the
        # cool_blue register's exact value is the strongest corroboration I
        # found anywhere in this pass, and it is worth noting that it makes the
        # register a measurement from two frames rather than one. Same
        # whole-box caveat as the gaming table: the slab is the emitter, the
        # body is not, and splitting them is a layer-2 fix.
    a(Material(
        "furn_shrine_lit", "Shrine — dark body under a lit altar slab",
        albedo=(0.068, 0.076, 0.115), roughness=0.3, metallic=0,
        specular=0.35,
        emission=(0.240, 0.320, 1.000), emission_energy=2.2,
        binds=("prop_shrine",), scenes=("interior",),
        source="05-sector-green/rotunda.webp — 00-INDEX.md: 'a blue illuminated altar table'. Balanced (gains 0.766/1.153/1.208): the lit slab (0.280,0.795)-(0.440,0.845) rgb(0.243,0.321,0.981) H 233 S 0.730 V 0.981, raw 95th percentile 0.847/0.882/1.000 — it clips, so it is a source and not a lit surface. The body below it, (0.300,0.860)-(0.420,0.900), reads rgb(0.003,0.009,0.142): near-black with only its own light on it. The measured emission is (0.243,0.321,0.981) and ACCENTS['cool_blue'] is (0.240,0.320,1.000) — the altar IS the cool_blue register, to three decimals, from a frame that register was not derived from.",
        extrapolated="The energy, 2.2, and it is a compromise I want on the record. The frame says the altar clips, which argues for much more; but `rooms.build` emits `prop_shrine` as one 1.10 x 0.60 x 1.70 m box, so whatever I set applies to the body as well as the slab, and a clipping value would turn a shrine into a lightbox. 2.2 is set against the library's own ladder — `tram_saloon_strip` 2.6, `marker_light_red` 2.1, `light_deck_channel` 3.5, `light_pilaster_strip` 6.0 — at the low end, where an object that is only partly a lamp belongs. Also extrapolated: that the alien shrines in alien_worship take the same light as the rotunda's altar."))

        # The neutrality here is the whole result, and it is the fourth time
        # this project has found a colour that belonged to the light:
        # garden.png's grey-world gains (0.884/0.994/1.159) push the paving to
        # H 224 S 0.225 because the drum's khaki farmland fills the upper half
        # of the frame and drags the estimate blue, while the raw frame reads H
        # 11 S 0.062. Neither number is the albedo; the constant R-B across
        # three light levels is, and it says neutral. At 0.437 the path lands
        # just under the corridor wall's 0.460 and just under the pale
        # furniture standing on it, which is where a ground plane belongs.
        # `deck_plate` is the only sheet in the library that is large flat
        # panels with recessed seams, and at a 1.6 m repeat it reads as
        # flagstone jointing rather than as decking — the one place in my
        # family where an existing sheet genuinely fits the observed surface.
        # Kept apart from `furn_pale_composite` despite landing within 1% of it
        # in value: the difference between paving and furniture here is
        # entirely roughness and jointing (0.70 and textured against 0.40 and
        # smooth), and that is exactly the kind of difference that reads on
        # screen even when the albedo does not.
    a(Material(
        "furn_paving", "Garden Paving — flagstone path",
        albedo=(0.437, 0.437, 0.437), roughness=0.7, metallic=0,
        specular=0.35, texture="deck_plate", uv_scale=1.0 / 1.6,
        binds=("prop_path",), scenes=("interior",),
        source="09-garden-core-and-transit/garden.png raw, three light levels on one surface: lit (0.586,0.876)-(0.640,0.900) 0.696/0.659/0.655; mid (0.660,0.800)-(0.760,0.850) 0.686/0.651/0.667; shadowed (0.360,0.960)-(0.460,0.985) 0.427/0.392/0.388. R-B holds at +0.041, +0.019 and +0.039 across a 1.63x range of value while R/B runs 1.063 to 1.100 — a constant DIFFERENCE, so the warmth is an additive key and the stone is neutral. Neutral base 0.655, scaled x0.667 by that frame's lawn anchor (raw lawn 0.522/0.655/0.376 against `ground_parkland` 0.345/0.425/0.260, per-channel scales 0.661/0.649/0.691) gives 0.437. 00-INDEX.md on the same frame: 'large pale flagstone paving'; 03-sector-blue/Babylon_5_2-22_29a.jpg independently shows 'paved winding paths in small setts'.",
        extrapolated="The 1.6 m slab repeat. The frame plainly shows large rectangular slabs with open joints, but every run of paving in it is seen at a grazing angle, so a joint pitch cannot be recovered without a ground-plane homography and I did not fake one — 00-INDEX.md's own calibration (1.75 m figures at ~40 px/m at their depth, and explicitly not transferable) is the only scale in the frame. This is the same class of number `hazard_chevron` already declares extrapolated: 'the frames show the pattern, not its scale'. One frame of a path square-on closes it."))

    return tuple(M)


MATERIALS = _build()
BY_NAME = {m.name: m for m in MATERIALS}

SCENES = ("exterior", "drum", "interior")


def scene_materials(scene):
    return tuple(m for m in MATERIALS if scene in m.scenes)


# ---------------------------------------------------------------------------
# Binding
# ---------------------------------------------------------------------------

def resolve(group, scene=None):
    """Material for an OBJ/glTF group name. Longest matching fragment wins.

    Identical rule to `godot/scripts/render_shot.gd::_material_for`, on purpose:
    if this function and the engine disagreed about which material a group got,
    every render would be judging something other than what ships.
    """
    best, best_len = None, -1
    for m in MATERIALS:
        if scene is not None and scene not in m.scenes:
            continue
        for frag in m.binds:
            if frag in group and len(frag) > best_len:
                best, best_len = m, len(frag)
    return best


def godot_rules(scene):
    """{group fragment: material name} for a scene's `material_rules` table.

    Aliases are folded in. They are a Python-side convenience -- "this group is
    the same surface as that one, under a different generator" -- but the
    engine has only the table, so an alias left out of it is a group that hits
    the magenta fallback in the render while `resolve_any` reports it bound.
    The first version emitted binds only, and every `drum_*` land-use band
    would have come up unbound inside the drum.
    """
    out = {}
    for m in scene_materials(scene):
        for frag in m.binds:
            out[frag] = m.name
    for group, name in GROUP_ALIASES.items():
        if scene in BY_NAME[name].scenes:
            out[group] = name
    return dict(sorted(out.items()))


# Every group name the generators emit, so a group added without a material is
# caught here rather than as a magenta patch in a render nobody looks at.
# `_selftest` also scans the sibling modules' source for group literals, which
# is what makes this list stay honest.
_LAND_USE_NAMES = ("arable", "settlement", "water", "parkland")
KNOWN_GROUPS = tuple(sorted(set(
    # exterior
    ("main_truss_spine", "reactor_spine", "explosive_disconnect_neck",
     "comms_grid_pylon", "reactor_cooling_fin", "cargo_module",
     "heat_exchange_solar_array", "forward_swept_array",
     "space_traffic_prox_array", "greeble_nav_light", "greeble_hazard_light",
     "greeble_panel", "greeble_vent", "greeble_hatch", "greeble_blister",
     "greeble_antenna", "greeble_cleat", "greeble_conduit")
    # drum shell and caps
    + tuple(f"drum_{n}" for n in _LAND_USE_NAMES)
    + tuple(f"drum_riser_{n}" for n in _LAND_USE_NAMES)
    + tuple(f"endcap_plate_c{i}" for i in range(8))
    + ("endcap_plate_c2_checker", "endcap_plate_c5_checker",
       "endcap_rib", "endcap_rimlight", "endcap_course_wall", "spoke")
    # ground
    + tuple(f"ground_arable_{i}" for i in range(4))
    + ("ground_arable", "ground_avenue", "ground_hedge", "ground_parkland",
       "ground_rim", "ground_road", "ground_settlement", "ground_shore",
       "ground_water")
    # truss, tram, core
    + ("truss_chord", "truss_tie", "truss_web", "truss_lamp")
    + ("tram_body", "tram_roof", "tram_cap", "tram_band", "tram_glass",
       "tram_headlight", "tram_port", "tram_recess", "tram_shoe",
       "tram_valance")
    + ("tram_in_wall", "tram_in_ceiling", "tram_in_floor", "tram_in_seat",
       "tram_in_post", "tram_in_strip", "tram_in_window", "tram_in_mullion",
       "tram_in_bezel", "tram_in_readout", "tram_in_device", "tram_in_plinth",
       "tram_in_reveal", "tram_in_skirt")
    + ("core_tube_barrel", "core_tube_collar", "core_tube_band",
       "core_tube_band_warm", "core_tube_cage", "core_tube_end",
       "core_hub_bell", "core_hub_bore", "core_hub_brace", "core_hub_fin",
       "core_hub_lamp", "core_hub_port", "core_hub_saddle",
       "core_node_bell", "core_node_bore", "core_node_port", "core_node_spar")
    # interior kit
    + ("structure", "wall_panel", "wall_assembly", "pilaster", "portal_frame",
       "door_frame", "door_leaf", "bulkhead", "deck_grid", "deck_panel",
       "light_deck_channel", "light_pilaster_strip", "light_portal_head",
       "light_downlight")
)))

# `drum_*` bands are the ground seen from inside the shell before the
# heightfield replaces it, so they take the ground materials. Declared as an
# alias table rather than as more `binds` entries because they are the same
# surface under two different generators, and two fragments claiming one
# surface is exactly the collision `_selftest` forbids.
GROUP_ALIASES = {
    "drum_arable": "ground_arable", "drum_settlement": "ground_settlement",
    "drum_water": "ground_water", "drum_parkland": "ground_parkland",
    "drum_riser_arable": "ground_shore", "drum_riser_settlement": "ground_settlement",
    "drum_riser_water": "ground_shore", "drum_riser_parkland": "ground_shore",
    "door_leaf": "kit_pilaster",
    # The verge is the ground a road is cut INTO -- drum_ground.py splits it out
    # as its own group precisely so the LOD's 31.2 m geometry ramp stops being
    # counted as roadway. It is not a surface of its own, so it takes the band
    # it borders rather than getting a material nobody measured.
    "ground_verge": "ground_parkland",
}


def resolve_any(group, scene=None):
    """`resolve`, then the alias table. What the exporter should call."""
    m = resolve(group, scene)
    if m is not None:
        return m
    alias = GROUP_ALIASES.get(group)
    if alias:
        return BY_NAME[alias]
    # endcap_plate_cN and endcap_plate_cN_checker fall out of `resolve` because
    # "endcap_plate" is a substring of both; this branch only catches a group
    # that matched nothing at all.
    return None


# ---------------------------------------------------------------------------
# Procedural textures
# ---------------------------------------------------------------------------
#
# Trim sheets, in ADR 0002's sense. Tileable, because they are projected
# triplanar in world space -- the glTF export carries POSITION and NORMAL only,
# so there are no UVs to place a decal against and every map has to survive
# being tiled in three directions at once.
#
# Everything is computed from `h01`, so the same commit produces the same
# texels on any machine, and a texture diff means a rule changed rather than a
# seed drifted.

TEX_SIZE = {
    "hull_plate": 2048,      # seen from 20 m by a Starfury and from 20 km
    "wall_plate": 2048,      # seen from 0.5 m by a person
    "deck_stud": 2048,       # the highest-frequency pattern in the set
    "deck_plate": 1024,
    "truss_steel": 1024,     # never the subject of a shot
    "hazard_chevron": 512,   # two colours and a diagonal
    "signage_panel": 512,
    "hull_window": 2048,     # read at 3 km as a lit band and at 20 m as glass
}

TEXTURE_MAPS = ("albedo", "normal", "orm")

# Sheets that also export an emission map. Kept as a separate list rather than
# a fourth entry in TEXTURE_MAPS because every other sheet would then export a
# black map -- 21 wasted textures, and `tres` would bind an emission texture to
# materials that do not emit.
EMISSIVE_SHEETS = ("hull_window",)

# Steepest 0.5% of each sheet, as a dimensionless rise over run. Declared per
# sheet because it is a statement about the SURFACE -- how deep a hull seam is
# against how wide a plate is -- and not about the texture's resolution.
TEX_SLOPE = {
    "hull_plate": 0.35,       # deep rebated seams and proud weld beads
    "wall_plate": 0.25,       # recessed seams between plate courses
    "deck_stud": 0.18,        # a few mm of dome; enough to catch a specular
    "deck_plate": 0.22,
    "truss_steel": 0.30,
    "hazard_chevron": 0.06,   # paint on plate; the pattern is not relief
    "signage_panel": 0.20,    # the bezel, and nothing else
    "hull_window": 0.16,      # a shallow rebate; relief must die with distance
}

# An albedo map multiplies `albedo_color`, so it has to average to a known
# constant or the measured colour stops being the colour that renders. The
# first version left the multiplier averaging ~0.98, which put the whole
# variation against the 1.0 ceiling: every wear highlight clipped, and the
# maps came out as near-white sheets with the plate pattern barely surviving.
# Centring at 0.72 leaves 39% of headroom above the mean for wear and rivet
# highlights, and `tres` divides the measured albedo by it so the product is
# still the measured value.
TEX_MEAN = 0.72


def _np():
    import numpy as np
    return np


def _rows(n, size, seed, spread=0.45):
    """Partition `size` into ~n bands of unequal width, deterministically.

    A perfectly regular grid reads as graph paper; that is what killed the
    first greeble pass ("confetti, not machinery"). Real plating is regular in
    *pitch* and irregular in *run*, so band widths jitter about the mean and
    the cumulative sum is renormalised to land exactly on `size` -- which is
    what keeps the sheet tileable.
    """
    w = [1.0 + spread * (h01(seed, "band", i) * 2.0 - 1.0) for i in range(n)]
    total = sum(w)
    edges, acc = [0], 0.0
    for i in range(n):
        acc += w[i] / total * size
        edges.append(int(round(acc)))
    edges[-1] = size
    # A zero-width band would make a seam of infinite frequency; nudge instead.
    for i in range(1, len(edges)):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + 1
    edges[-1] = size
    return edges


def _plate_maps(size, nx, ny, seed, merge_p=0.24):
    """Per-texel (plate id, distance to the nearest ACTIVE seam, in texels).

    Cells are laid out on an irregular grid and then MERGED: a boundary
    selected with probability `merge_p` is deleted, so its two cells become one
    larger plate with no seam between them.

    That merge step is the difference between plating and bathroom tile. The
    first version emitted one plate per cell on a near-uniform grid, and tiled
    it looked exactly like tile: one size, one rhythm, a rim on every element.
    `exterior more.jpg` shows nothing of the kind -- pale plate groups several
    plates across sit inside fields of smaller ones, and a run of plates shares
    a value. Session 2n learned the same thing about greebles the same way
    ("confetti, not machinery"): what makes procedural detail read is a size
    hierarchy, not more elements.

    Merges wrap. A boundary that is never merged at u = 0 would put a column of
    single-width plates down the repeat, which is a seam you can see from
    across the room even though every pixel matches.
    """
    np = _np()
    xe = _rows(nx, size, (seed, "x"))
    ye = _rows(ny, size, (seed, "y"))

    # mx[j][i]: the boundary between cell (i-1, j) and (i, j) is DELETED.
    mx = [[h01(seed, "mx", i, j) < merge_p for i in range(nx)]
          for j in range(ny)]
    my = [[h01(seed, "my", i, j) < merge_p for i in range(nx)]
          for j in range(ny)]

    parent = list(range(nx * ny))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for j in range(ny):
        for i in range(nx):
            if mx[j][i]:
                union((i - 1) % nx + j * nx, i + j * nx)
            if my[j][i]:
                union(i + ((j - 1) % ny) * nx, i + j * nx)

    PID = np.zeros((size, size), dtype=np.int32)
    BIG = np.float32(1e6)
    D = np.full((size, size), BIG, dtype=np.float32)
    ax = np.arange(size, dtype=np.float32)
    for j in range(ny):
        ys, ye_ = ye[j], ye[j + 1]
        for i in range(nx):
            xs, xe_ = xe[i], xe[i + 1]
            PID[ys:ye_, xs:xe_] = find(i + j * nx)
            # A boundary contributes a distance only if it survived the merge.
            dl = (ax[xs:xe_] - xs) if not mx[j][i] else None
            dr = (xe_ - 1 - ax[xs:xe_]) if not mx[j][(i + 1) % nx] else None
            dt = (ax[ys:ye_] - ys) if not my[j][i] else None
            db = (ye_ - 1 - ax[ys:ye_]) if not my[(j + 1) % ny][i] else None
            blk = np.full((ye_ - ys, xe_ - xs), BIG, dtype=np.float32)
            for arr, axis in ((dl, 1), (dr, 1), (dt, 0), (db, 0)):
                if arr is None:
                    continue
                blk = np.minimum(blk, arr[None, :] if axis == 1 else arr[:, None])
            D[ys:ye_, xs:xe_] = blk
    return PID, D


def _plate_value(PID, seed, jitter, key="plate"):
    """Per-PLATE multiplicative jitter, as a full-resolution field.

    Keyed on plate id rather than on cell, so a merged plate is one value all
    the way across instead of two values with an invisible join between them.
    """
    np = _np()
    n = int(PID.max()) + 1
    tbl = np.array([1.0 + jitter * (h01(seed, key, i) * 2.0 - 1.0)
                    for i in range(n)], dtype=np.float32)
    return tbl[PID]


def _plate_gate(PID, seed, p, key="gate"):
    """Per-plate boolean field: which plates get a treatment and which do not."""
    np = _np()
    n = int(PID.max()) + 1
    tbl = np.array([1.0 if h01(seed, key, i) < p else 0.0 for i in range(n)],
                   dtype=np.float32)
    return tbl[PID]


def _fbm(size, seed, octaves=5, base=4):
    """Value-noise fBm, tileable, deterministic.

    Written out rather than imported: `numpy.random` is a global generator and
    seeding it would make this texture depend on whatever ran before it in the
    process.
    """
    np = _np()
    out = np.zeros((size, size), dtype=np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        if n > size:
            break
        g = np.array([[h01(seed, "fbm", o, i, j) for i in range(n)]
                      for j in range(n)], dtype=np.float32)
        # Wrap by one so the bilinear interpolation is periodic.
        g = np.concatenate([g, g[:1, :]], axis=0)
        g = np.concatenate([g, g[:, :1]], axis=1)
        t = np.linspace(0, n, size, endpoint=False, dtype=np.float32)
        i0 = np.floor(t).astype(np.int32)
        f = (t - i0)[:, None]
        f = f * f * (3 - 2 * f)                      # smoothstep, C1
        a = g[np.ix_(i0, i0)]
        b = g[np.ix_(i0, (i0 + 1) % n)]
        c = g[np.ix_((i0 + 1) % n, i0)]
        d = g[np.ix_((i0 + 1) % n, (i0 + 1) % n)]
        top = a + (b - a) * f.T
        bot = c + (d - c) * f.T
        out += amp * (top + (bot - top) * f)
        tot += amp
        amp *= 0.5
    return out / max(tot, 1e-6)


def _normal_from_height(height, target_slope):
    """Tangent-space normal map from a tileable height field.

    `np.roll` rather than a gradient with edge handling, because the sheet has
    to tile: a Sobel that clamps at the border puts a visible ridge along every
    repeat, which is the classic way a procedural trim sheet betrays itself.

    `target_slope` is the 99.5th-percentile gradient the finished map should
    have -- a dimensionless rise over run, so 0.35 means the steepest 0.5% of
    the surface leans about 19 degrees. The first version took a raw multiplier
    of `size / 8`, which is a *resolution*, not a slope: at 2048 it drove the
    deck's studs to normals with |xy| near 1.0, i.e. sheer vertical walls
    around every 7 cm stud. That renders as a floor of chrome ball bearings,
    and the only assertion covering it was "normals deviate from flat", which
    a 90-degree wall passes emphatically.
    """
    np = _np()
    gx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    gy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    mag = np.sqrt(gx * gx + gy * gy)
    p = float(np.percentile(mag, 99.5))
    k = target_slope / max(p, 1e-9)
    nx, ny = -gx * k, -gy * k
    nz = np.ones_like(height)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=2)


def _streaks(size, seed, count, width, length, strength):
    """Downward grime streaks below seams. Runs along +v in texture space."""
    np = _np()
    out = np.zeros((size, size), dtype=np.float32)
    v = np.arange(size, dtype=np.float32)
    for k in range(count):
        x = int(h01(seed, "streak_x", k) * size)
        y = int(h01(seed, "streak_y", k) * size)
        w = max(1, int(width * (0.4 + h01(seed, "streak_w", k))))
        ln = int(length * (0.3 + h01(seed, "streak_l", k)))
        fall = np.clip(1.0 - (v[:ln] / max(ln, 1)), 0.0, 1.0) ** 1.6
        s = strength * (0.4 + 0.6 * h01(seed, "streak_s", k))
        for dx in range(w):
            xx = (x + dx) % size
            edge = 1.0 - abs((dx + 0.5) / w * 2.0 - 1.0)
            for i, f in enumerate(fall):
                out[(y + i) % size, xx] += s * f * edge
    return np.clip(out, 0.0, 1.0)


def _write_png(path, arr):
    """arr: HxWx3 float 0..1 -> 8-bit RGB PNG."""
    from PIL import Image
    np = _np()
    img = np.clip(arr, 0.0, 1.0)
    Image.fromarray((img * 255.0 + 0.5).astype("uint8"), mode="RGB").save(
        path, optimize=True)


def _pack(ao, rough, metal):
    np = _np()
    return np.stack([ao, rough, metal], axis=2)


def gen_plate_sheet(size, seed, nx, ny, base_rough, base_metal,
                    seam_px, wear_px, jitter, streaks, weld=False,
                    seam_darken=0.35):
    """The workhorse: an irregular rectangular plate lattice.

    This is the shape the reference actually shows and the shape the existing
    `hull_exterior.tres` does not. That material mottles the hull with
    FastNoiseLite -- smooth organic blobs. Magnified, `exterior more.jpg`'s
    drum is *rectangular*: discrete plate patches at differing values with thin
    dark seams between them, and measured along one constant latitude the value
    steps rather than drifts (sd 0.037-0.095 in bands, not a gradient). Organic
    noise cannot produce a step, so it reads as dirt on a smooth hull instead of
    as a hull made of plates.
    """
    np = _np()
    PID, D = _plate_maps(size, nx, ny, seed)
    val = _plate_value(PID, seed, jitter)

    seam = np.clip(1.0 - D / max(seam_px, 1e-3), 0.0, 1.0) ** 2
    # Only some plates have rubbed edges. Rimming every plate is what made the
    # first bake read as grouted tile: a bright edge all the way round every
    # element is a pattern nothing physical produces.
    wear = np.clip(1.0 - D / max(wear_px, 1e-3), 0.0, 1.0)
    wear = wear * _plate_gate(PID, seed, 0.35, "wear")

    grain = _fbm(size, (seed, "grain"), octaves=6, base=8)
    blotch = _fbm(size, (seed, "blotch"), octaves=3, base=2)
    # A field two or three plates across, so that runs of plates share a tone.
    # The measured hull varies at plate scale (sd 0.037-0.095 along a latitude)
    # AND at a much larger one -- the pale patches on the drum in the side view
    # span several plates. One frequency cannot produce both.
    cluster = _fbm(size, (seed, "cluster"), octaves=2, base=2)
    dirt = _streaks(size, (seed, "dirt"), streaks, size / 90.0, size / 6.0, 0.5)

    # Height: plates stand proud, seams cut in, welds bead up along some seams.
    height = val * 0.5 + grain * 0.06 - seam * 1.0
    if weld:
        wmask = _plate_gate(PID, seed, 0.22, "weld")
        bead = np.clip(1.0 - D / max(seam_px * 1.6, 1e-3), 0.0, 1.0)
        height = height + wmask * bead * 0.55

    value = (val * (0.90 + 0.20 * blotch) * (0.88 + 0.24 * cluster)
             - seam * seam_darken
             + wear * 0.22
             - dirt * 0.28)
    value = np.clip(value, 0.05, 1.6)

    rough = np.clip(base_rough + seam * 0.18 + dirt * 0.22 - wear * 0.20
                    + (grain - 0.5) * 0.08, 0.04, 1.0)
    metal = np.clip(base_metal + wear * 0.35 - dirt * 0.15, 0.0, 1.0)
    ao = np.clip(1.0 - seam * 0.65 - dirt * 0.15, 0.0, 1.0)
    return value, rough, metal, ao, height


def stud_field(size, n):
    """(stud dome height 0..1, grout line mask 0..1) for the deck sheet.

    Split out of the generator so the self-test can ask which texels are stud
    CROWNS. The first version of that assertion masked on "normal z close to
    1", which is flat -- and the flat ground between the studs is flat too, so
    it selected both populations, averaged them, and reported the inversion
    backwards. It could not have caught the thing it was written to catch.
    """
    np = _np()
    t = (np.arange(size, dtype=np.float32) + 0.5) / size * n
    fx = np.abs((t % 1.0) - 0.5) * 2.0
    FX = np.broadcast_to(fx[None, :], (size, size))
    FY = np.broadcast_to(fx[:, None], (size, size))
    r = np.sqrt(FX * FX + FY * FY)
    stud = np.clip(1.0 - r / 0.72, 0.0, 1.0)
    stud = stud * stud * (3 - 2 * stud)              # smoothstep dome

    # Grout lines between tiles: one every `n // tiles` studs.
    tiles = max(2, n // 8)
    g = (np.arange(size, dtype=np.float32) + 0.5) / size * tiles
    gd = np.minimum(g % 1.0, 1.0 - (g % 1.0))
    GD = np.minimum(np.broadcast_to(gd[None, :], (size, size)),
                    np.broadcast_to(gd[:, None], (size, size)))
    grout = np.clip(1.0 - GD / 0.035, 0.0, 1.0)
    return stud, grout


def gen_stud_sheet(size, seed, n, base_rough, base_metal):
    """The corridor deck: a regular grid of raised studs.

    Magnified, `grey level 1.webp`'s floor is a grid of bright ovals on a
    darker ground, and the ovals are what makes the deck measure 1.6x the
    wall's value while being darker paint. Modelling that as albedo would give
    a floor that stays bright when the lights go out.
    """
    np = _np()
    stud, grout = stud_field(size, n)

    grain = _fbm(size, (seed, "deckgrain"), octaves=5, base=6)
    traffic = _fbm(size, (seed, "traffic"), octaves=2, base=2)

    height = stud * 0.8 - grout * 0.6 + grain * 0.05
    # The stud crowns get only a small albedo lift. They read bright in the
    # reference because they are polished by traffic and catch a specular, and
    # that is carried by `rough` below. A large albedo lift here clipped 3.4%
    # of the sheet against the ceiling once the map was centred on TEX_MEAN,
    # and a crown that is bright in ALBEDO stays bright with the lights off.
    value = np.clip(0.80 + stud * 0.16 - grout * 0.30
                    + (grain - 0.5) * 0.18 - traffic * 0.10, 0.1, 1.6)
    # Stud crowns are walked on, so they are polished; the ground between them
    # holds dirt. That inversion is the whole reason the floor sparkles.
    rough = np.clip(base_rough - stud * 0.22 + grout * 0.25
                    + traffic * 0.15, 0.05, 1.0)
    metal = np.clip(base_metal + stud * 0.25 - grout * 0.1, 0.0, 1.0)
    ao = np.clip(1.0 - grout * 0.7 - (1.0 - stud) * 0.12, 0.0, 1.0)
    return value, rough, metal, ao, height


def gen_window_sheet(size, seed):
    """Habitat window apertures: (albedo, rough, metal, ao, height, emission).

    Returns emission as a separate RGB field -- the mask IS the deliverable and
    the rest of the sheet is the frame around it.
    """
    np = _np()
    rep_u = rep_v = WINDOW_REPEAT_M
    cols = WINDOW_COLS
    px_u, px_v = size / rep_u, size / rep_v

    u = (np.arange(size, dtype=np.float32) + 0.5) / px_u        # metres across
    v = (np.arange(size, dtype=np.float32) + 0.5) / px_v        # metres down
    U = np.broadcast_to(u[None, :], (size, size))
    V = np.broadcast_to(v[:, None], (size, size))

    col_i = np.floor(U / WINDOW_PITCH_M).astype(np.int32)
    row_i = np.floor(V / DECK_PITCH_M).astype(np.int32)
    lu = U - col_i * WINDOW_PITCH_M - (WINDOW_PITCH_M - WINDOW_W_M) / 2.0
    lv = V - row_i * DECK_PITCH_M - WINDOW_SILL_M

    band = np.isin(row_i, np.array(WINDOW_BANDS, dtype=np.int32))
    inside = (band & (lu >= 0) & (lu <= WINDOW_W_M)
              & (lv >= 0) & (lv <= WINDOW_H_M))
    # The frame is the 90 mm rebate around the glass; it is what stops a window
    # reading as a decal painted on the hull.
    fr = 0.09
    frame = ((band & (lu >= -fr) & (lu <= WINDOW_W_M + fr)
              & (lv >= -fr) & (lv <= WINDOW_H_M + fr)) & ~inside)

    # Per-aperture state, deterministic in (row, col) so the pattern is stable
    # across processes and across a rebuild. `h01` is the project's blake2b
    # helper -- never `random`, never `str.__hash__`.
    lit = np.zeros((size, size), dtype=np.float32)
    emis = np.zeros((size, size, 3), dtype=np.float32)
    for r in WINDOW_BANDS:
        for c in range(cols):
            if h01(seed, "lit", r, c) > WINDOW_LIT_P:
                continue
            p = h01(seed, "temp", r, c)
            acc = 0.0
            for rgb, gain, share in WINDOW_TEMPS:
                acc += share
                if p <= acc:
                    break
            # Vary within the register too, or a hundred windows of one exact
            # colour read as a repeated tile -- which is what they are.
            g = gain * (0.72 + 0.55 * h01(seed, "gain", r, c))
            cell = inside & (row_i == r) & (col_i == c)
            lit = np.maximum(lit, cell.astype(np.float32))
            emis[cell] = np.array(rgb, dtype=np.float32) * g

    # THE FRAME IS A DARK REBATE, NOT A BRIGHT RIDGE, and this is the other
    # half of the static. In the first bake the frame was metallic 0.55 and
    # stood 0.25 proud, so every aperture threw a sunlit specular highlight and
    # the white speckle in the render was the FRAMES rather than the emission.
    # A window surround is a shadowed recess; it should darken the hull, not
    # sparkle on it.
    # Plate sits at TEX_MEAN so that albedo_color (the hull's, divided by
    # TEX_MEAN) multiplies back to exactly hull_exterior. Asserted below.
    val = np.where(inside, 0.14, np.where(frame, 0.26, TEX_MEAN)
                   ).astype(np.float32)
    val = val * (0.92 + 0.16 * _fbm(size, (seed, "grime"), octaves=5, base=6))
    rough = np.where(inside, 0.12, np.where(frame, 0.62, 0.58)).astype(np.float32)
    metal = np.where(inside, 0.0, np.where(frame, 0.10, 0.34)).astype(np.float32)
    h = np.where(inside, -0.75, np.where(frame, -0.30, 0.0)).astype(np.float32)
    ao = np.where(inside, 0.45, np.where(frame, 0.62, 1.0)).astype(np.float32)
    return val, rough, metal, ao, h, emis


def gen_chevron_sheet(size, seed, pitch, base_rough):
    """Diagonal yellow/black hazard stripes, worn.

    Returns a full RGB albedo rather than a value field, because it is the one
    two-colour pattern in the set.
    """
    np = _np()
    u = (np.arange(size, dtype=np.float32) + 0.5) / size
    U = np.broadcast_to(u[None, :], (size, size))
    V = np.broadcast_to(u[:, None], (size, size))
    # (u + v) so the stripe is 45 deg and the pattern tiles in both directions.
    s = ((U + V) * pitch) % 1.0
    band = (s < 0.5).astype(np.float32)
    edge = np.clip(np.minimum(np.abs(s - 0.5), np.abs(((s + 0.5) % 1.0) - 0.5))
                   / 0.02, 0.0, 1.0)
    band = band * edge + (1 - edge) * 0.5

    grain = _fbm(size, (seed, "chevgrain"), octaves=5, base=8)
    # base=3, octaves=3 put the whole wear field at one very low frequency: the
    # first bake came out with a single soft blob covering the middle third of
    # the sheet, which reads as a stain rather than as paint rubbed off by
    # traffic. Wear on a bay lip is patchy at the scale of a boot.
    scuff = _fbm(size, (seed, "scuff"), octaves=5, base=10)
    worn = np.clip((scuff - 0.56) * 4.0, 0.0, 1.0)

    yellow = np.array(ACCENTS["hazard_yellow"], dtype=np.float32)
    black = np.array([0.055, 0.052, 0.050], dtype=np.float32)
    substrate = np.array([0.32, 0.315, 0.305], dtype=np.float32)

    col = band[:, :, None] * yellow + (1 - band)[:, :, None] * black
    col = col * (0.85 + 0.30 * grain)[:, :, None]
    col = col * (1 - worn)[:, :, None] + substrate * worn[:, :, None]

    height = grain * 0.1 - worn * 0.15
    rough = np.clip(base_rough + worn * 0.2 + (grain - 0.5) * 0.1, 0.05, 1.0)
    metal = np.clip(worn * 0.5, 0.0, 1.0)
    ao = np.clip(1.0 - worn * 0.1, 0.0, 1.0)
    return col, rough, metal, ao, height


def gen_signage_sheet(size, seed):
    """A backlit panel's substrate: bezel, field, and a fine scan structure.

    No lettering. Lettering is language, and inventing Earth Alliance signage
    text is a canon decision that belongs in a signage pass with the four
    `16-signage-typography-ui/` files open, not in a material.
    """
    np = _np()
    u = (np.arange(size, dtype=np.float32) + 0.5) / size
    U = np.broadcast_to(u[None, :], (size, size))
    V = np.broadcast_to(u[:, None], (size, size))
    d = np.minimum(np.minimum(U, 1 - U), np.minimum(V, 1 - V))
    bezel = np.clip(1.0 - d / 0.045, 0.0, 1.0)
    scan = 0.5 + 0.5 * np.cos(V * size * 0.25 * 2 * math.pi)
    field = np.array([0.151, 0.156, 0.434], dtype=np.float32)
    frame = np.array([0.120, 0.122, 0.130], dtype=np.float32)
    col = field * (0.92 + 0.16 * scan)[:, :, None]
    col = col * (1 - bezel)[:, :, None] + frame * bezel[:, :, None]
    height = -bezel * 0.5
    rough = np.clip(0.30 + bezel * 0.35, 0.05, 1.0)
    metal = bezel * 0.4
    ao = np.clip(1.0 - bezel * 0.5, 0.0, 1.0)
    return col, rough, metal, ao, height


def build_texture(name):
    """(albedo HxWx3, orm HxWx3, normal HxWx3) for one trim sheet."""
    np = _np()
    size = TEX_SIZE[name]
    if name == "hull_plate":
        # 48 m repeat over 2048 texels = 43 texels/m; 16 plates across the
        # repeat = 3.0 m plates. Session 2e tuned the LATHE's plate modulation
        # to 37-65 m, which is the structural bay; this is the sheet metal
        # inside one bay, an order of magnitude finer, and the two are meant to
        # be seen together.
        v, r, m, ao, h = gen_plate_sheet(size, "hull", 16, 12, 0.72, 0.34,
                                         seam_px=size / 340.0,
                                         wear_px=size / 110.0,
                                         jitter=PLATE_VALUE_JITTER,
                                         streaks=140, weld=True)
        base = np.array([1.0, 0.985, 0.965], dtype=np.float32)
    elif name == "wall_plate":
        # 4 m repeat, 6 plates across = 0.67 m courses, which is the pitch of
        # the plate courses in `grey level 1.webp` read against a 2.1 m door.
        #
        # Jitter stays low -- 0.055 -- because that frame's plates genuinely do
        # not differ much from one another, and inventing a mottled interior
        # would contradict the measurement. What the frame DOES show clearly is
        # the seam: a thin, hard, dark line between courses, which is most of
        # the wall's read. So the seam is widened and darkened here rather than
        # the plates being made noisier.
        v, r, m, ao, h = gen_plate_sheet(size, "wall", 6, 4, 0.56, 0.10,
                                         seam_px=size / 150.0,
                                         wear_px=size / 150.0,
                                         jitter=0.055, streaks=40,
                                         seam_darken=0.62)
        base = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    elif name == "deck_plate":
        v, r, m, ao, h = gen_plate_sheet(size, "deckplate", 4, 3, 0.62, 0.20,
                                         seam_px=size / 180.0,
                                         wear_px=size / 90.0,
                                         jitter=0.07, streaks=25)
        base = np.array([1.0, 0.995, 0.985], dtype=np.float32)
    elif name == "truss_steel":
        v, r, m, ao, h = gen_plate_sheet(size, "truss", 5, 5, 0.55, 0.40,
                                         seam_px=size / 200.0,
                                         wear_px=size / 70.0,
                                         jitter=0.16, streaks=60, weld=True)
        base = np.array([1.0, 0.98, 0.95], dtype=np.float32)
    elif name == "deck_stud":
        v, r, m, ao, h = gen_stud_sheet(size, "deck", 16, 0.34, 0.30)
        base = np.array([1.0, 0.997, 0.99], dtype=np.float32)
    elif name == "hazard_chevron":
        col, r, m, ao, h = gen_chevron_sheet(size, "hazard", 4.0, 0.62)
        return col, _pack(ao, r, m), _normal_from_height(h, TEX_SLOPE[name])
    elif name == "signage_panel":
        col, r, m, ao, h = gen_signage_sheet(size, "sign")
        return col, _pack(ao, r, m), _normal_from_height(h, TEX_SLOPE[name])
    elif name == "hull_window":
        v, r, m, ao, h, _e = gen_window_sheet(size, "window")
        base = np.array([1.0, 0.99, 0.975], dtype=np.float32)
    else:
        raise KeyError(name)

    # Renormalise the multiplier onto TEX_MEAN, then clip. Order matters: mean
    # first means the clip removes only the genuine extremes instead of the top
    # third of the distribution.
    #
    # The window sheet is EXEMPT. Its albedo is not a wear multiplier over one
    # measured colour -- it is dark glass against a lighter hull, and forcing
    # its mean to 0.72 would lift the glass until unlit windows read as pale
    # panels, which is the derelict-hull failure with extra steps.
    if name != "hull_window":
        v = v / max(float(v.mean()), 1e-6) * TEX_MEAN
    albedo = np.clip(v[:, :, None] * base[None, None, :], 0.0, 1.0)
    nrm = _normal_from_height(h, TEX_SLOPE[name])
    return albedo, _pack(ao, r, m), nrm


def _patch_import(path, kind):
    """Force VRAM compression on a texture Godot has already imported.

    Godot's default for a PNG is `compress/mode=0` -- Lossless, which means
    UNCOMPRESSED in VRAM. It flips to VRAM-compressed on its own only when a
    texture is first detected in a 3D material at editor runtime, so whether
    the station's textures cost 58 MB or 174 MB depends on the order somebody
    happened to open things in. Measured on this build: 58.0 MB compressed
    against 174.0 MB not, for the same 21 maps.

    Patching rather than authoring: a `.import` carries a `uid` and a hashed
    path into `.godot/imported/`, both of which only the importer can produce.
    If the file is not there yet, this says so and the caller runs
    `godot --headless --path godot --import` once.
    """
    if not os.path.exists(path):
        return False
    with open(path) as f:
        text = f.read()
    out = text.replace("compress/mode=0", "compress/mode=2")
    # MIPMAPS ARE NOT OPTIONAL HERE and Godot's PNG default is off. The hull
    # sheet repeats every 48 m on a body 8 km long: without mips the far end of
    # the station samples one texel per several pixels and the plating boils.
    # The deck sheet repeats every 1.21 m and would shimmer as the player
    # walks. Measured cost of turning them on: 29.0 MB -> 38.6 MB, which is
    # 0.3% of the VRAM target.
    out = out.replace("mipmaps/generate=false", "mipmaps/generate=true")
    if kind in ("normal", "orm"):
        # "Optimized" rather than "sRGB Friendly". These two are DATA, not
        # colour: a roughness value and a surface direction. Letting the
        # compressor pick endpoints as though the channels were a colour ramp
        # is a small, uniform error over every surface in the station.
        out = out.replace("compress/channel_pack=0", "compress/channel_pack=1")
    if kind == "normal":
        # BC5 two-channel, and it tells Godot to reconstruct z rather than
        # storing it. A normal map compressed as ordinary colour blocks gets
        # visible banding in the shading, which reads as a modelling fault.
        out = out.replace("compress/normal_map=0", "compress/normal_map=1")
    if out != text:
        with open(path, "w") as f:
            f.write(out)
    return True


def build_emission(name):
    """The emission map for a sheet that has one. HxWx3, 0..1."""
    if name != "hull_window":
        raise KeyError(name)
    _v, _r, _m, _ao, _h, emis = gen_window_sheet(TEX_SIZE[name], "window")
    return _np().clip(emis, 0.0, 1.0)


def export_textures(outdir=TEXTURE_DIR, only=None):
    os.makedirs(outdir, exist_ok=True)
    written = []
    missing_import = []
    for name in TEX_SIZE:
        if only and name not in only:
            continue
        albedo, orm, nrm = build_texture(name)
        _write_png(os.path.join(outdir, f"{name}_albedo.png"), albedo)
        _write_png(os.path.join(outdir, f"{name}_orm.png"), orm)
        _write_png(os.path.join(outdir, f"{name}_normal.png"), nrm * 0.5 + 0.5)
        maps = TEXTURE_MAPS
        if name in EMISSIVE_SHEETS:
            emis = build_emission(name)
            _write_png(os.path.join(outdir, f"{name}_emission.png"), emis)
            maps = maps + ("emission",)
        for kind in maps:
            fn = f"{name}_{kind}.png"
            written.append(fn)
            if not _patch_import(os.path.join(outdir, fn + ".import"), kind):
                missing_import.append(fn)
    if missing_import:
        written.append(f"({len(missing_import)} textures have no .import yet -- "
                       "run: godot --headless --path godot --import)")
    return written


# ---------------------------------------------------------------------------
# Godot export
# ---------------------------------------------------------------------------

# Two sheets carry a finished two-tone COLOUR rather than a grey multiplier: a
# hazard chevron is yellow and black, and a backlit sign is navy with a dark
# bezel. Neither can be produced by tinting one map with one albedo_color, so
# the colour is baked and the material's tint is left at white. `Material.albedo`
# still records the measured colour, because that is what the palette table and
# the neutrality gate are about.
COLOUR_SHEETS = ("hazard_chevron", "signage_panel")


def emitted_albedo(m):
    """`albedo_color` as written to the .tres.

    An albedo TEXTURE multiplies albedo_color, so a material carrying a
    multiplier centred on TEX_MEAN has to pre-divide or the surface renders at
    0.72x the colour that was measured. Keeping `Material.albedo` as the
    measured value and doing the division here means the provenance table and
    the assertions stay in measured units, and only the file Godot reads
    carries the compensation.
    """
    if not m.texture:
        return m.albedo
    if m.texture in COLOUR_SHEETS:
        return (1.0, 1.0, 1.0)
    return tuple(min(1.0, round(c / TEX_MEAN, 4)) for c in m.albedo)


def _c(t, alpha=1):
    return f"Color({', '.join(_num(v) for v in t)}, {alpha})"


def _num(v):
    s = f"{float(v):.6g}"
    return s


SHADER_DIR = MATERIAL_DIR

# Uniforms a shader may declare and the library may leave alone. Kept explicit
# so that adding one is a decision someone made, not a gate quietly widening.
SHADER_DEFAULTS_OK = {"albedo_tex", "orm_tex", "normal_tex", "emission_tex"}


def shader_uniforms(name):
    """Uniform names a .gdshader declares.

    Read back out of the shader source for the same reason `tres` checks its
    keys against `STANDARD_MATERIAL_KEYS`: Godot silently DROPS a
    `shader_parameter/` it does not recognise and renders the shader at its
    declared defaults. That looks like a plausible surface rather than an
    error, which is exactly how `emission_energy` would sit at 3.4 forever
    while the library thinks it set 6.0.
    """
    path = os.path.join(SHADER_DIR, f"{name}.gdshader")
    with open(path) as f:
        src = f.read()
    return set(re.findall(r"^uniform\s+\S+\s+([A-Za-z_][A-Za-z0-9_]*)",
                          src, re.M))


def shader_tres(m):
    """One ShaderMaterial as Godot 4 text.

    A separate function rather than a branch inside `tres` because the two
    resources share almost nothing: a ShaderMaterial has no albedo_color, no
    roughness and no uv1_scale -- it has a shader and a bag of parameters, and
    every property name is the shader's rather than the engine's.
    """
    ext = [f'[ext_resource type="Shader" '
           f'path="res://materials/{m.shader}.gdshader" id="1_shader"]']
    body = [f'resource_name = "{m.title}"', 'shader = ExtResource("1_shader")']
    ids = {}
    if m.texture:
        for i, kind in enumerate(TEXTURE_MAPS):
            ids[kind] = f"{i + 2}_{kind}"
            ext.append(f'[ext_resource type="Texture2D" '
                       f'path="res://materials/textures/{m.texture}_{kind}.png" '
                       f'id="{ids[kind]}"]')
    if m.emission_texture:
        ids["emission"] = f"{len(ext) + 1}_emission"
        ext.append(f'[ext_resource type="Texture2D" '
                   f'path="res://materials/textures/'
                   f'{m.emission_texture}_emission.png" '
                   f'id="{ids["emission"]}"]')
    for kind, rid in sorted(ids.items()):
        body.append(f'shader_parameter/{kind}_tex = ExtResource("{rid}")')
    for k, v in sorted(m.shader_params.items()):
        if isinstance(v, tuple) and len(v) == 3:
            body.append(f"shader_parameter/{k} = {_c(v)}")
        else:
            body.append(f"shader_parameter/{k} = {_num(v)}")
    head = (f'[gd_resource type="ShaderMaterial" load_steps={len(ext) + 1} '
            "format=3]")
    # Same shape rules as `tres`: the [gd_resource] tag on line one and ';'
    # comments, not '#'. Getting either wrong fails the load with a parse error
    # and no amount of Python-side checking sees it.
    banner = [";" + ln[1:] if ln.startswith("#") else ln
              for ln in HEADER.strip().splitlines()]
    return "\n".join([head, ""] + banner + [""] + ext + ["", "[resource]"]
                      + body) + "\n"


def tres(m):
    """One StandardMaterial3D as Godot 4 text.

    Every key written here is a real property of StandardMaterial3D. Godot
    silently DROPS keys it does not recognise and hands back a material sitting
    at its defaults, which reads as a plausible surface rather than as an
    error, so `godot/scripts/verify_materials.gd` checks each key against the
    class's property list. `_selftest` checks the same list here, without an
    engine, so a typo fails in CI rather than in a render.
    """
    ext, body = [], []
    # ids are looked up BY MAP NAME, never by position. The first version wrote
    # them positionally and then referenced "2_orm" and "3_normal" by hand,
    # while TEXTURE_MAPS orders them albedo, normal, orm -- so id 2 was the
    # normal map and every textured material in the library loaded its normal
    # map as roughness and its ORM as normals. It exported clean, it parsed
    # clean, and the two assertions covering .tres textures (one ext_resource
    # per map; load_steps counts them) both passed, because both counted
    # references without checking what they pointed at.
    ids = {}
    if m.emission_texture:
        ids["emission"] = "0_emission"
        ext.append(f'[ext_resource type="Texture2D" '
                   f'path="res://materials/textures/'
                   f'{m.emission_texture}_emission.png" id="0_emission"]')
    if m.texture:
        for i, kind in enumerate(TEXTURE_MAPS):
            ids[kind] = f"{i + 1}_{kind}"
            ext.append(f'[ext_resource type="Texture2D" '
                       f'path="res://materials/textures/{m.texture}_{kind}.png" '
                       f'id="{ids[kind]}"]')
    body.append(f'resource_name = "{m.title}"')
    body.append(f"albedo_color = {_c(emitted_albedo(m))}")
    if m.texture:
        body.append(f'albedo_texture = ExtResource("{ids["albedo"]}")')
    body.append(f"metallic = {_num(m.metallic)}")
    body.append(f"metallic_specular = {_num(m.specular)}")
    if m.texture:
        body.append(f'metallic_texture = ExtResource("{ids["orm"]}")')
        body.append("metallic_texture_channel = 2")
    body.append(f"roughness = {_num(m.roughness)}")
    if m.texture:
        body.append(f'roughness_texture = ExtResource("{ids["orm"]}")')
        body.append("roughness_texture_channel = 1")
        body.append("normal_enabled = true")
        body.append(f'normal_texture = ExtResource("{ids["normal"]}")')
        body.append(f"normal_scale = {_num(m.normal_scale)}")
        body.append("ao_enabled = true")
        body.append(f'ao_texture = ExtResource("{ids["orm"]}")')
        body.append("ao_texture_channel = 0")
        body.append("ao_light_affect = 0.35")
    if m.emission:
        body.append("emission_enabled = true")
        body.append(f"emission = {_c(m.emission)}")
        body.append(f"emission_energy_multiplier = {_num(m.emission_energy)}")
    if m.emission_texture:
        # `emission_enabled` is set by the block above when the material also
        # carries a flat emission colour, and writing it twice is how a .tres
        # gets a duplicate key -- harmless here because both say true, and
        # exactly the kind of thing that stops being harmless.
        if not m.emission:
            body.append("emission_enabled = true")
        # emission_operator 1 is MULTIPLY: the map decides WHICH texels emit and
        # in what colour, and `emission` tints the lot. Godot's default is 0,
        # ADD, which would make the whole hull glow at `emission` and the
        # windows glow slightly more -- the derelict reads as a lightbox
        # instead, which is the same finding from the other side.
        body.append(f'emission_texture = ExtResource("{ids["emission"]}")')
        body.append("emission_operator = 1")
    if m.texture:
        s = m.uv_scale
        body.append(f"uv1_scale = Vector3({_num(s)}, {_num(s)}, {_num(s)})")
        if m.triplanar:
            body.append("uv1_triplanar = true")
            body.append("uv1_world_triplanar = true")
        body.append("texture_filter = 3")

    load_steps = len(ext) + 1
    head = ('[gd_resource type="StandardMaterial3D" '
            + (f"load_steps={load_steps} " if ext else "")
            + "format=3]")
    # The [gd_resource] tag has to be the FIRST line of the file and comments
    # are ';', not '#'. Both were got wrong on the first export: a six-line '#'
    # banner above the tag made every one of the 59 materials fail to load with
    # "Parse Error: Expected '['" and "Invalid color code: #", and nothing in
    # this module could have caught it -- the .tres was well-formed by every
    # rule this file knows and malformed by the only rule that matters. It took
    # running the engine. Hence `_selftest`'s two shape assertions below, and
    # hence the note in the module docstring about running verify_materials.gd.
    parts = [head, ""] + [";" + ln[1:] if ln.startswith("#") else ln
                          for ln in HEADER.strip().splitlines()] + [""]
    if ext:
        parts += ext + [""]
    parts += ["[resource]"] + body
    return "\n".join(parts) + "\n"


HEADER = """# GENERATED by station/materials.py. Do not hand-edit.
#
# Materials are generated for the same reason geometry is: inside and outside
# come from one description so they cannot disagree. Editing this file changes
# what renders until the next export overwrites it, and the change is then
# lost with no diff to show for it. Edit station/materials.py.
"""


# Hand-written materials this library replaces, and what replaced them. Named
# one by one rather than "delete anything not generated", because other agents
# are working in this repository at the same time and a generator that removes
# whatever it does not recognise will eventually eat someone's new file the
# hour after they add it.
SUPERSEDED = {
    # Measured warm (0.52, 0.492, 0.468) from `grey level 1.webp`. The warmth
    # is the left wall's downlights: the right wall of the same frame, at the
    # same height, balances to H 159-195 with S 0.037-0.122. See
    # NEGATIVE_RESULTS.
    "hull_interior.tres": "kit_wall_plate",
    "emissive_floor.tres": "light_deck_channel",
}


def export_tres(outdir=MATERIAL_DIR):
    os.makedirs(outdir, exist_ok=True)
    written = []
    for m in MATERIALS:
        path = os.path.join(outdir, f"{m.name}.tres")
        with open(path, "w") as f:
            f.write(shader_tres(m) if m.shader else tres(m))
        if m.shader:
            written.append(f"  ({m.shader}.gdshader)")
        written.append(f"{m.name}.tres")
    for old, new in SUPERSEDED.items():
        p = os.path.join(outdir, old)
        if os.path.exists(p):
            os.remove(p)
            written.append(f"(removed {old}, superseded by {new})")
    return written


SCENE_FILES = {"exterior": os.path.join(ROOT, "godot", "scenes",
                                        "exterior.tscn"),
               "drum": os.path.join(ROOT, "godot", "scenes", "drum.tscn")}


def patch_scene_rules(path, scene):
    """Rewrite one `.tscn`'s material_rules block and the resources it needs.

    THIS USED TO BE A PASTE STEP, AND THE PASTE STEP IS WHY LAYER 3 STARTED
    WITH A SILENT FAILURE. `export_rules_gd` wrote the tables to a .txt for a
    human to copy in, on the reasoning that "godot/scenes/** belongs to another
    agent and a generator that rewrites someone else's file is how two sources
    of truth start". The reasoning is inverted: the .txt and the .tscn WERE the
    two sources, and nobody is doing the paste. The first material added after
    that -- `habitat_windows`, the fix for the standing blocking finding --
    exported cleanly, passed every assertion, and did not reach the render.
    Godot printed `fallback material used by 21 group(s)` and nothing was
    gating on it.

    CLAUDE.md hard rule 4: consistency is by construction, not by discipline.

    Only the `material_rules` block and the `[ext_resource]` lines it needs are
    touched. The lights, the environment and the tonemapper are judgements and
    stay owned by whoever wrote them.
    """
    with open(path) as f:
        text = f.read()

    # Existing resources, so `fallback_material = ExtResource("m_hull")` and
    # every other short id keeps working. Map by PATH, because the same
    # material may already be declared under a hand-chosen id.
    by_path = {}
    for line in text.splitlines():
        if line.startswith('[ext_resource') and 'type="Material"' in line:
            by_path[line.split('path="')[1].split('"')[0]] = \
                line.split('id="')[1].split('"')[0]

    rules, added = godot_rules(scene), []
    for name in sorted(set(rules.values())):
        p = f"res://materials/{name}.tres"
        if p not in by_path:
            by_path[p] = f"m_{name}"
            added.append(f'[ext_resource type="Material" path="{p}" '
                         f'id="m_{name}"]')

    block = ["material_rules = {"]
    body = [f'"{frag}": ExtResource("{by_path[f"res://materials/{n}.tres"]}"),'
            for frag, n in rules.items()]
    if body:
        body[-1] = body[-1].rstrip(",")       # Godot rejects a trailing comma
    block += body + ["}"]

    start = text.index("material_rules = {")
    end = text.index("\n}", start) + len("\n}")
    text = text[:start] + "\n".join(block) + text[end:]

    if added:
        # After the last existing ext_resource, so the header stays grouped.
        lines = text.splitlines()
        last = max(i for i, l in enumerate(lines)
                   if l.startswith("[ext_resource"))
        lines[last + 1:last + 1] = added
        text = "\n".join(lines) + "\n"

    # load_steps is ext_resources + sub_resources + 1. Godot does not fail on a
    # wrong count -- it just stops preloading -- so this is silent if left
    # stale, which is the same class of defect as the paste step.
    n = (text.count("[ext_resource") + text.count("[sub_resource") + 1)
    text = re.sub(r"load_steps=\d+", f"load_steps={n}", text, count=1)
    with open(path, "w") as f:
        f.write(text)
    return path, len(rules), len(added)


def export_rules_gd(outdir=MATERIAL_DIR):
    """The scenes' `material_rules` tables, kept as a readable artefact.

    `patch_scene_rules` is what actually reaches the engine; this stays because
    the table is worth being able to read and diff on its own.
    """
    lines = ["; GENERATED by station/materials.py -- paste into the scene's",
             "; material_rules block. Regenerate rather than hand-editing.", ""]
    for scene in SCENES:
        rules = godot_rules(scene)
        if not rules:
            continue
        lines.append(f"; --- {scene} ---")
        lines.append("material_rules = {")
        for frag, name in rules.items():
            lines.append(f'"{frag}": ExtResource("m_{name}"),')
        lines.append("}")
        lines.append("")
    path = os.path.join(outdir, "material_rules.gen.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


# ---------------------------------------------------------------------------
# Texture memory budget
# ---------------------------------------------------------------------------
#
# CLAUDE.md's target is RTX 4070 / RX 7800 XT class, 1440p60, 12 GB VRAM.
# `station/budget.py` gates triangles, draw calls, bandwidth and file size and
# has no texture gate at all, because until now there were no textures.

VRAM_TOTAL_MB = 12 * 1024
# A 1440p Forward+ frame's own attachments -- colour, depth, normal/roughness,
# two glow chains, SSAO, shadow atlases -- run to roughly 1.2 GB on this class
# of card before any content. Content therefore gets a share of what is left,
# and textures conventionally take about a third of that: the rest is meshes,
# instance buffers, GI, and the driver.
VRAM_TEXTURE_BUDGET_MB = 3072.0
# Materials are the floor on draw calls: a mesh cannot batch across a material.
# The exterior's 64 is `budget.py`'s existing gate, so its material count has to
# sit well inside that or the gate is unreachable by construction.
#
# EXTRAPOLATED: 96 for the drum and 64 for interiors. `budget.py` gates neither.
# The drum gets more because it is the only view in the project that has the
# ground, both end caps, three trusses, the core tube and a tram in frame at
# once, and every one of those is a different fabrication. Overturned by a real
# frame-time measurement on target hardware, which nothing here can produce.
DRAW_CALL_BUDGET = {"exterior": 64, "drum": 96, "interior": 64}

# MEASURED, not assumed. The first version of this table guessed BC7 at 8 bpp
# for every map and reported 58.0 MB. Running the actual importer and weighing
# the output shows Godot picks BC1 for the two three-channel maps and BC5 for
# the normals, and the real figure is 38.67 MB:
#
#   godot --headless --path godot --import
#   ls -l godot/.godot/imported/*.s3tc.ctex | awk '{s+=$5} END {print s/1048576}'
#
# A budget gate that reports 50% more than the truth is not conservative, it is
# wrong, and it would eventually be used to refuse a texture the card had room
# for. `_selftest` holds the formula against the measurement.
BYTES_PER_TEXEL = {
    "albedo": 0.5,    # BC1  RGB  4 bpp -- no alpha anywhere in the set
    "orm": 0.5,       # BC1  RGB  4 bpp
    "normal": 1.0,    # BC5  RG   8 bpp, z reconstructed
    "emission": 0.5,  # BC1  RGB  4 bpp
}
MIP_FACTOR = 4.0 / 3.0
# Sum of godot/.godot/imported/*.s3tc.ctex after `--import`, with
# mipmaps/generate=true and compress/mode=2 on all 21 maps.
MEASURED_VRAM_MB = 38.67
# ...WHICH IS A MEASUREMENT OF THESE SEVEN SHEETS, and of nothing else. Adding
# an eighth pushed the formula to 49.33 MB and failed the agreement gate --
# correctly, because the gate asks "does the formula predict the importer" and
# the honest answer needs both sides over the same set. The tempting fix is to
# edit the number above to whatever the formula now says, which would turn a
# measurement into a restatement of the model it is supposed to check.
#
# So the gate is restricted to the measured set, and re-measuring is what moves
# MEASURED_VRAM_MB. Total cost against budget is a different question and is
# asserted separately, over everything.
MEASURED_VRAM_SHEETS = ("hull_plate", "wall_plate", "deck_stud", "deck_plate",
                        "truss_steel", "hazard_chevron", "signage_panel")


def texture_memory():
    """Resident texture cost, compressed and uncompressed."""
    comp = 0.0
    raw = 0.0
    per = {}
    n_maps = 0
    for name, size in TEX_SIZE.items():
        maps = TEXTURE_MAPS + (("emission",) if name in EMISSIVE_SHEETS else ())
        c = sum(size * size * BYTES_PER_TEXEL[k] for k in maps) * MIP_FACTOR
        r = size * size * 3 * len(maps) * MIP_FACTOR
        per[name] = c / 1024 ** 2
        comp += c
        raw += r
        n_maps += len(maps)
    return {
        "sets": len(TEX_SIZE),
        "maps": n_maps,
        "compressed_mb": comp / 1024 ** 2,
        "uncompressed_mb": raw / 1024 ** 2,
        "budget_mb": VRAM_TEXTURE_BUDGET_MB,
        "fraction": comp / 1024 ** 2 / VRAM_TEXTURE_BUDGET_MB,
        "per_set_mb": per,
    }


def budget_report():
    tm = texture_memory()
    lines = ["texture memory",
             f"  {tm['sets']} trim sheets, {tm['maps']} maps",
             f"  BC1/BC5 + mips   {tm['compressed_mb']:8.1f} MB   "
             f"{tm['fraction'] * 100:5.2f}% of the {tm['budget_mb']:.0f} MB texture budget",
             f"  measured import  {MEASURED_VRAM_MB:8.2f} MB   "
             "(sum of .godot/imported/*.s3tc.ctex)",
             f"  uncompressed     {tm['uncompressed_mb']:8.1f} MB   "
             f"(what Godot's DEFAULT import setting costs -- compress/mode=0)",
             f"  of 12 GB VRAM    {tm['compressed_mb'] / VRAM_TOTAL_MB * 100:8.2f}%",
             "",
             "materials per scene (a material is a draw-call floor)"]
    for scene in SCENES:
        n = len(scene_materials(scene))
        b = DRAW_CALL_BUDGET[scene]
        lines.append(f"  {scene:9s} {n:3d} materials   budget {b:3d} draw calls   "
                     f"{n / b * 100:5.1f}%")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Looking at it without a GPU
# ---------------------------------------------------------------------------

def preview_sheet(path, size=96):
    """A contact sheet: every material as a lit chip, in library order.

    `tools/preview_render.py` is flat-shaded and per-group tinted, so it can
    say nothing at all about a material -- which is the whole thing this file
    produces. A GGX chip under one key and one fill is not the engine, but it
    does answer the questions a swatch cannot: whether the value ladder reads
    as a ladder, whether two materials that should differ actually do, and
    whether an emissive is doing anything.
    """
    np = _np()
    from PIL import Image, ImageDraw

    cols = 8
    rows = (len(MATERIALS) + cols - 1) // cols
    pad, label_h = 8, 14
    W = cols * (size + pad) + pad
    H = rows * (size + pad + label_h) + pad
    canvas = np.zeros((H, W, 3), dtype=np.float32)
    canvas[:] = 0.06

    # Sphere normals, one key, one fill, GGX. Deliberately the same light
    # directions as `godot/scenes/station_view.tscn`'s Sun and Fill.
    t = (np.arange(size, dtype=np.float32) + 0.5) / size * 2 - 1
    X = np.broadcast_to(t[None, :], (size, size))
    Y = np.broadcast_to(-t[:, None], (size, size))
    r2 = X * X + Y * Y
    mask = r2 <= 1.0
    Z = np.sqrt(np.clip(1 - r2, 0, 1))
    N = np.stack([X, Y, Z], axis=2)
    Vv = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    key = np.array([-0.40, 0.55, 0.73], dtype=np.float32)
    key /= np.linalg.norm(key)
    fill = np.array([0.68, 0.25, 0.69], dtype=np.float32)
    fill /= np.linalg.norm(fill)

    def shade(mat):
        alb = np.array(mat.albedo, dtype=np.float32)
        rough = max(mat.roughness, 0.045)
        f0 = 0.04 + (np.array(mat.albedo) - 0.04) * mat.metallic
        out = np.zeros((size, size, 3), dtype=np.float32)
        for L, col, energy in ((key, np.array([1.0, 0.94, 0.86]), 2.2),
                               (fill, np.array([0.55, 0.68, 1.0]), 0.35)):
            ndl = np.clip((N * L).sum(axis=2), 0, 1)
            Hv = (L + Vv)
            Hv = Hv / np.linalg.norm(Hv)
            ndh = np.clip((N * Hv).sum(axis=2), 0, 1)
            a = rough * rough
            d = a * a / (math.pi * ((ndh ** 2) * (a * a - 1) + 1) ** 2)
            spec = d * 0.25
            diff = alb[None, None, :] * (1 - mat.metallic) / math.pi
            out += (diff + f0[None, None, :] * spec[:, :, None]) * ndl[:, :, None] \
                * col[None, None, :] * energy
        out += np.array(mat.albedo)[None, None, :] * 0.05
        if mat.emission:
            out += np.array(mat.emission)[None, None, :] * \
                min(mat.emission_energy, 6.0) * 0.16
        return out

    for i, mat in enumerate(MATERIALS):
        r, c = divmod(i, cols)
        x = pad + c * (size + pad)
        y = pad + r * (size + pad + label_h)
        chip = shade(mat)
        chip = np.clip(chip, 0, 1) ** (1 / 2.2)
        tile = canvas[y:y + size, x:x + size]
        canvas[y:y + size, x:x + size] = np.where(mask[:, :, None], chip, tile)

    img = Image.fromarray((np.clip(canvas, 0, 1) * 255 + 0.5).astype("uint8"))
    d = ImageDraw.Draw(img)
    for i, mat in enumerate(MATERIALS):
        r, c = divmod(i, cols)
        x = pad + c * (size + pad)
        y = pad + r * (size + pad + label_h) + size + 2
        # A chip shows the FLAT term only. Textured materials additionally
        # carry a trim sheet that changes what they look like, so they are
        # marked rather than quietly presented as the finished surface.
        tag = " +tex" if mat.texture else ""
        d.text((x, y), mat.name[:15] + tag, fill=(190, 195, 200))
    img.save(path)
    return path


def preview_surface(path, mat_name, px=520, tiles=2, light_deg=22.0):
    """One material's trim sheet, lit, as it would actually be seen.

    The chip sheet shows a material's flat term and the map sheet shows its
    maps; neither answers the question that matters, which is whether the
    normal map reads as relief when light crosses it. A grazing key is what
    exposes both failure modes: a map that is too flat shows nothing, and a map
    that is too steep -- the first deck bake, with 90-degree walls around every
    stud -- turns into chrome.

    Flat plane, orthographic, GGX, one key at `light_deg` above the surface
    plus a fill and an ambient term. Not the engine. Enough to judge relief,
    tiling and whether the wear reads as wear.
    """
    np = _np()
    from PIL import Image
    m = BY_NAME[mat_name]
    if not m.texture:
        raise ValueError(f"{mat_name} has no trim sheet")
    albedo, orm, nrm = build_texture(m.texture)
    n = albedo.shape[0]

    def tile(a):
        a = np.concatenate([a] * tiles, axis=0)
        a = np.concatenate([a] * tiles, axis=1)
        idx = (np.arange(px) * (n * tiles) // px)
        return a[np.ix_(idx, idx)]

    A = tile(albedo) * np.array(emitted_albedo(m), dtype=np.float32)
    O = tile(orm)
    N = tile(nrm)
    N = N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-6)

    rough = np.clip(O[:, :, 1] * (m.roughness / 0.5), 0.03, 1.0)
    metal = np.clip(O[:, :, 2] * (0.5 + m.metallic), 0.0, 1.0)
    ao = O[:, :, 0]

    th = math.radians(light_deg)
    L = np.array([math.cos(th) * 0.7, math.cos(th) * 0.7, math.sin(th)],
                 dtype=np.float32)
    L /= np.linalg.norm(L)
    V = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    H = (L + V) / np.linalg.norm(L + V)

    ndl = np.clip((N * L).sum(axis=2), 0, 1)
    ndh = np.clip((N * H).sum(axis=2), 0, 1)
    ndv = np.clip(N[:, :, 2], 1e-3, 1)
    a2 = (rough * rough) ** 2
    d = a2 / (math.pi * ((ndh ** 2) * (a2 - 1) + 1) ** 2)
    k = (rough + 1) ** 2 / 8
    g = (ndl / (ndl * (1 - k) + k)) * (ndv / (ndv * (1 - k) + k))
    f0 = 0.04 * (1 - metal) + metal
    spec = (d * g * f0 / (4 * np.maximum(ndl * ndv, 1e-4)))[:, :, None]
    diff = A * (1 - metal)[:, :, None] / math.pi

    key = np.array([1.0, 0.94, 0.86], dtype=np.float32) * 2.6
    out = (diff + spec) * ndl[:, :, None] * key
    fill = np.array([0.55, 0.68, 1.0], dtype=np.float32) * 0.22
    out += A * np.clip(N[:, :, 2], 0, 1)[:, :, None] * fill
    out += A * (ao * 0.10)[:, :, None]
    if m.emission:
        out += np.array(m.emission, dtype=np.float32) * \
            min(m.emission_energy, 6.0) * 0.12

    img = np.clip(out, 0, 1) ** (1 / 2.2)
    Image.fromarray((img * 255 + 0.5).astype("uint8")).save(path)
    return path


def texture_sheet(path, name, size=320):
    """Albedo | ORM | normal for one trim sheet, side by side, downsampled."""
    np = _np()
    from PIL import Image
    albedo, orm, nrm = build_texture(name)
    out = []
    for arr in (albedo, orm, nrm * 0.5 + 0.5):
        im = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype("uint8"))
        out.append(np.asarray(im.resize((size, size), Image.LANCZOS)))
    Image.fromarray(np.concatenate(out, axis=1)).save(path)
    return path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

# Real StandardMaterial3D property names, Godot 4.x. Checked against the class
# reference rather than remembered. verify_materials.gd checks the same thing
# with an engine present; this checks it without one, which is what CI has.
STANDARD_MATERIAL_KEYS = {
    "resource_name", "albedo_color", "albedo_texture", "metallic",
    "metallic_specular", "metallic_texture", "metallic_texture_channel",
    "roughness", "roughness_texture", "roughness_texture_channel",
    "normal_enabled", "normal_texture", "normal_scale",
    "ao_enabled", "ao_texture", "ao_texture_channel", "ao_light_affect",
    "emission_enabled", "emission", "emission_energy_multiplier",
    "emission_texture", "emission_operator",
    "uv1_scale", "uv1_triplanar", "uv1_world_triplanar", "uv1_offset",
    "texture_filter", "cull_mode", "shading_mode", "transparency",
}

_PASS = 0
_FAIL = 0


def check(label, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
    else:
        _FAIL += 1
        print(f"FAIL  {label}" + (f"  [{detail}]" if detail else ""))


def _scan_generator_groups():
    """Group-name literals in the sibling generators.

    A coverage list that is hand-maintained rots the moment another agent adds
    a group, and the symptom is a magenta patch in a render nobody is looking
    at that week. This reads the literals back out of the source so the gate
    fails when the geometry changes, not when someone remembers to update a
    list. Restricted to the established prefixes so an unrelated string cannot
    fail the build.
    """
    import re
    pat = re.compile(
        r'"((?:drum|endcap|truss|tram|core|ground|greeble|light)_[a-z0-9_]*)"')
    found = set()
    d = os.path.dirname(os.path.abspath(__file__))
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".py") or fn in NOT_GENERATORS:
            continue
        try:
            with open(os.path.join(d, fn)) as f:
                src = f.read()
        except OSError:
            continue
        for g in pat.findall(src):
            # Schema keys and dimension constants share the prefixes; a group
            # never ends in a unit suffix.
            if g.endswith(("_m", "_deg", "_frac", "_mm")):
                continue
            if g in NOT_GROUPS:
                continue
            found.add(g)
    return found


# Modules whose string literals are NOT geometry group names, so scanning them
# produces false failures rather than coverage. `directory.py` is the location
# register -- its literals are place keys like "core_shuttle" and "drum_office"
# -- and `rooms.py` is the room generator, whose literals are prop types like
# "tram_door". Both were added after this scanner was written, and between them
# they contributed 6 of the 8 names in its first failure; not one was a group.
#
# The distinction is real and worth keeping sharp: a SPECIFICATION names places
# and props, a GENERATOR names surfaces. Only the second kind needs a material.
NOT_GENERATORS = {"materials.py", "directory.py", "rooms.py"}

# Literals that match the group prefixes but are not group names: manifest
# statistics, and prefixes used in a `startswith` test. Kept explicit rather
# than pattern-excluded so that adding one is a decision someone made rather
# than a regex that quietly widened. If one of these ever becomes a real group,
# deleting the line is what makes the coverage gate start caring about it.
NOT_GROUPS = {
    "greeble_assemblies", "greeble_detail", "greeble_instances",
    "greeble_instances_by_kind", "greeble_triangles",
    # interior.py's riser assertion: `g.startswith("drum_riser")`. The groups
    # actually emitted are drum_riser_arable, _settlement, _water, _parkland,
    # and all four are in KNOWN_GROUPS and resolve through GROUP_ALIASES.
    "drum_riser",
    # lod.py manifest statistic: the count of greeble pieces standing off the
    # hull. A number in a report, never a surface.
    "greeble_off_hull_pieces",
}


def _selftest():
    np = _np()

    # -- library integrity ------------------------------------------------
    check("every material has a unique name",
          len(BY_NAME) == len(MATERIALS),
          f"{len(BY_NAME)} of {len(MATERIALS)}")
    check("every material declares a source",
          all(m.source for m in MATERIALS))
    check("every material belongs to at least one scene",
          all(m.scenes for m in MATERIALS))
    check("every scene name used is a declared scene",
          all(s in SCENES for m in MATERIALS for s in m.scenes))

    # Two materials claiming one fragment is not a warning: whichever is
    # iterated last silently wins, and it wins differently once the library is
    # reordered. This is the assertion that would have caught it.
    claims = {}
    dup = []
    for m in MATERIALS:
        for frag in m.binds:
            if frag in claims:
                dup.append((frag, claims[frag], m.name))
            claims[frag] = m.name
    check("no two materials claim the same bind fragment", not dup, str(dup))

    # -- resolution matches the engine's rule -----------------------------
    def rname(group, scene=None):
        m = resolve(group, scene)
        return m.name if m else "<none>"

    check("resolve picks the LONGEST matching fragment",
          rname("core_tube_band_warm") == "core_band_warm",
          rname("core_tube_band_warm"))
    check("resolve tolerates the glTF importer's name decoration",
          rname("BabylonStation_cargo_module_001") == "cargo_module",
          rname("BabylonStation_cargo_module_001"))
    check("a checker course beats the plain plate rule",
          rname("endcap_plate_c2_checker") == "endcap_checker",
          rname("endcap_plate_c2_checker"))
    check("a plain course still lands on the plate rule",
          rname("endcap_plate_c3") == "endcap_plate",
          rname("endcap_plate_c3"))
    check("scene filtering excludes other scenes' materials",
          resolve("truss_lamp", scene="exterior") is None)

    unresolved = [g for g in KNOWN_GROUPS if resolve_any(g) is None]
    check("every known generator group resolves to a material",
          not unresolved, str(unresolved[:8]))

    # An alias only fires when `resolve` finds nothing, so an alias whose key is
    # also matched by some material's bind fragment is dead code that reads as
    # a decision. `drum_riser` was such a fragment on `drum_structure`, and it
    # shadowed all four `drum_riser_*` aliases: the 9.5 m cliff between the
    # water band and the settlement band was being painted as structural steel
    # while the table next to it said "shore".
    shadowed = [g for g in GROUP_ALIASES if resolve(g) is not None]
    check("no alias is shadowed by a bind fragment", not shadowed,
          str(shadowed))

    # THE TABLE IS WHAT THE ENGINE READS. `resolve_any` reporting a group bound
    # means nothing if the fragment is absent from the exported rules, and the
    # symptom is a magenta patch in a render rather than an error anywhere.
    # This resolves every known group the way render_shot.gd does -- substring,
    # longest fragment wins -- against the exported table itself.
    all_rules = {}
    for s in SCENES:
        all_rules.update(godot_rules(s))

    def table_hit(group):
        best, bl = None, -1
        for frag, name in all_rules.items():
            if frag in group and len(frag) > bl:
                best, bl = name, len(frag)
        return best

    uncovered = [g for g in KNOWN_GROUPS if table_hit(g) is None]
    check("the EXPORTED rules table covers every known group",
          not uncovered, str(uncovered[:8]))
    disagree = [(g, table_hit(g), resolve_any(g).name)
                for g in KNOWN_GROUPS
                if resolve_any(g) and table_hit(g) != resolve_any(g).name]
    check("the exported table and resolve_any agree on every group",
          not disagree, str(disagree[:5]))

    scanned = _scan_generator_groups()
    check("the group scan found the generators at all",
          len(scanned) >= 30, f"{len(scanned)} literals")
    missed = sorted(g for g in scanned if resolve_any(g) is None)
    check("every group literal found in the generators resolves",
          not missed, str(missed[:10]))
    # AND THIS CHECK SEES LESS THAN ITS NAME SUGGESTS. The scan is restricted
    # to the prefixes drum|endcap|truss|tram|core|ground|greeble|light, so
    # every group that does not start with one is invisible to it -- all 124
    # of rooms.py's, and all 42 emitted by command_control, council_chamber,
    # docking_bay and signage. It passed over a list containing none of them.
    #
    # Widening the regex is the obvious fix and the wrong one: that is exactly
    # what made it start matching directory.py place keys and rooms.py prop
    # names, six false failures in one run. The real coverage question is
    # answered by station/test_materials_layer3.py, which RUNS the generators
    # and reads the groups they actually emit. This assertion records the
    # limitation so the name cannot be read as a guarantee.
    check("the literal scan does not claim to cover the whole station",
          not any(g.startswith(("prop_", "fix_", "cc_", "council_", "bay_",
                                "sign_")) for g in scanned),
          "the prefix scan has started matching room groups -- widen "
          "test_materials_layer3.py's BESPOKE_BUILDERS instead")

    check("the exterior hull material is deliberately unbound (it is the fallback)",
          BY_NAME["hull_exterior"].binds == ())
    check("hull_banding_red stays unbound until components.py grows a strip",
          BY_NAME["hull_banding_red"].binds == ())

    # -- the measured palette ---------------------------------------------
    # The headline finding, asserted so a later edit cannot quietly reverse it.
    # Light fittings are excluded: the finding is about SURFACES. The rim
    # light is a blue-white lamp at S 0.368 and is meant to be.
    interior = [m for m in MATERIALS
                if (m.name.startswith("kit_") or m.name.startswith("endcap")
                    or m.name in ("drum_structure", "core_tube",
                                  "tram_saloon_wall"))
                and m.emission is None]
    check("the neutrality gate covers the surfaces it is about",
          {m.name for m in interior} >= {"kit_wall_plate", "kit_pilaster",
                                         "endcap_plate", "drum_structure",
                                         "core_tube", "tram_saloon_wall"})
    for m in interior:
        r, g, b = m.albedo
        mx, mn = max(r, g, b), min(r, g, b)
        sat = 0.0 if mx == 0 else (mx - mn) / mx
        check(f"{m.name} is near-neutral (measured S 0.02-0.16 across every frame)",
              sat <= 0.16, f"S {sat:.3f}")

    # The lit corridor elements measured within +/-15% of each other. If a
    # later edit spreads them, the corridor has stopped being one paint system
    # and the reference no longer supports it.
    ladder = [BY_NAME[n].luminance() for n in
              ("kit_wall_plate", "kit_pilaster", "kit_rail_band")]
    check("the lit corridor elements stay inside the measured +/-15% spread",
          max(ladder) / min(ladder) <= 1.30,
          f"{max(ladder) / min(ladder):.3f}")

    # The anchor is the only absolute, so it has to actually be the thing that
    # sets the level: change it and the wall must move.
    check("ALBEDO_ANCHOR is what sets the interior level",
          abs(lit(_ANCHOR_MEASURED) - ALBEDO_ANCHOR) < 1e-6)
    check("the deck is darker than the wall it meets",
          BY_NAME["kit_deck"].luminance() < BY_NAME["kit_wall_plate"].luminance())
    check("the deck is smoother than the wall (its brightness is specular)",
          BY_NAME["kit_deck"].roughness < BY_NAME["kit_wall_plate"].roughness)

    # Emissives. An emissive that is not enabled renders as a dark object
    # rather than as an error -- the failure shape verify_materials.gd exists
    # for, checked here too because CI has no engine.
    for m in MATERIALS:
        if m.name.startswith(("light_", "marker_light", "emissive_")) or \
                m.name in ("truss_lamp", "core_hub_lamp", "tram_headlight",
                           "endcap_rimlight", "signage_panel",
                           "tram_saloon_strip"):
            check(f"{m.name} is named as a light source and emits",
                  m.emission is not None and m.emission_energy > 0)

    check("the fallback is a colour the model cannot produce",
          BY_NAME["unbound"].albedo == (1.0, 0.0, 0.85))

    check("every superseded material names a live replacement",
          all(v in BY_NAME for v in SUPERSEDED.values()),
          str([v for v in SUPERSEDED.values() if v not in BY_NAME]))
    check("nothing superseded shares a name with something generated",
          not (set(SUPERSEDED) & {f"{m.name}.tres" for m in MATERIALS}))

    # -- .tres validity, without an engine --------------------------------
    # `exported_tres` and not `tres`, because habitat_windows exports as a
    # ShaderMaterial and testing the StandardMaterial3D text that `tres` would
    # have written is testing a file that is never on disk. Nine assertions
    # below would have gone on passing about it.
    def exported_tres(m):
        return shader_tres(m) if m.shader else tres(m)

    for m in MATERIALS:
        text = exported_tres(m)
        if m.shader:
            # A ShaderMaterial shares only the two shape rules with a
            # StandardMaterial3D; every other property name is the shader's.
            check(f"{m.name}.tres opens with the resource tag on line 1",
                  text.splitlines()[0].startswith("[gd_resource "))
            check(f"{m.name}.tres uses ';' comments, not '#'",
                  not any(l.lstrip().startswith("#")
                          for l in text.splitlines()))
            check(f"{m.name}.tres declares it is a ShaderMaterial",
                  'type="ShaderMaterial"' in text.splitlines()[0])
            n_ext = text.count("[ext_resource")
            check(f"{m.name}.tres load_steps counts the ext_resources",
                  f"load_steps={n_ext + 1}" in text)
            # THE GATE THAT MATTERS. Godot silently DROPS a shader_parameter it
            # does not recognise and runs the shader at its declared default,
            # which reads as a plausible surface rather than as an error --
            # identical in kind to the StandardMaterial3D key check, and
            # identical in consequence: the library would believe it set a
            # value the render never saw.
            declared = shader_uniforms(m.shader)
            set_here = set(re.findall(r"shader_parameter/(\w+) = ", text))
            check(f"{m.name}: every shader_parameter is a real uniform",
                  set_here <= declared, str(sorted(set_here - declared)))
            check(f"{m.name}: every texture map reaches the shader",
                  {f"{k}_tex" for k in TEXTURE_MAPS} | (
                      {"emission_tex"} if m.emission_texture else set())
                  <= set_here,
                  str(sorted(set_here)))
            # A uniform the shader declares and nobody sets runs at its default.
            # That is legitimate, but it must be a decision, not an oversight.
            check(f"{m.name}: no shader uniform is left at a silent default",
                  declared - set_here <= SHADER_DEFAULTS_OK,
                  str(sorted(declared - set_here - SHADER_DEFAULTS_OK)))
            continue
        # Godot's text-resource parser wants the [gd_resource] tag on line one
        # and takes ';' as its comment character, not '#'. Getting either wrong
        # fails EVERY material in the directory with "Parse Error: Expected
        # '['", which is a total failure that no amount of Python-side property
        # checking sees. It happened; these two lines are why it cannot again.
        check(f"{m.name}.tres opens with the resource tag on line 1",
              text.splitlines()[0].startswith("[gd_resource "),
              text.splitlines()[0][:40])
        check(f"{m.name}.tres uses ';' comments, not '#'",
              not any(ln.lstrip().startswith("#") for ln in text.splitlines()))
        # A duplicate key is legal .tres and silently keeps the last value, so
        # nothing downstream can see it. The emissive path wrote
        # `emission_enabled` twice on its first export.
        _ks = [ln.split(" = ")[0] for ln in text.splitlines()
               if " = " in ln and not ln.startswith("[")
               and not ln.lstrip().startswith(";")]
        check(f"{m.name}.tres sets no property twice",
              len(_ks) == len(set(_ks)),
              str(sorted({k for k in _ks if _ks.count(k) > 1})))
        keys = [ln.split(" = ")[0] for ln in text.splitlines()
                if " = " in ln and not ln.startswith("[")
                and not ln.lstrip().startswith(";")]
        bad = [k for k in keys if k not in STANDARD_MATERIAL_KEYS]
        check(f"{m.name}.tres sets only real StandardMaterial3D properties",
              not bad, str(bad))
        check(f"{m.name}.tres declares load_steps iff it has ext_resources",
              ("load_steps=" in text.splitlines()[0]) ==
              ("[ext_resource" in text))
        if m.texture:
            n_ext = text.count("[ext_resource")
            want = len(TEXTURE_MAPS) + (1 if m.emission_texture else 0)
            check(f"{m.name}.tres declares one ext_resource per map",
                  n_ext == want, f"{n_ext} != {want}")
            check(f"{m.name}.tres load_steps counts the ext_resources",
                  f"load_steps={n_ext + 1}" in text)

            # THE ASSERTION THE FIRST TWO COULD NOT MAKE. Counting references
            # says nothing about what they point at, and the first version of
            # `tres` wired every textured material's normal map into its
            # roughness slot and its ORM into its normal slot. It exported
            # clean and both counting checks passed. This resolves each id back
            # to its path and asserts the texture in each slot is the map that
            # slot is for.
            paths = {}
            for ln in text.splitlines():
                if ln.startswith("[ext_resource"):
                    pid = ln.split('id="')[1].split('"')[0]
                    paths[pid] = ln.split('path="')[1].split('"')[0]
            slot_map = {"albedo_texture": "albedo",
                        "normal_texture": "normal",
                        "roughness_texture": "orm",
                        "metallic_texture": "orm",
                        "ao_texture": "orm"}
            if m.emission_texture:
                slot_map["emission_texture"] = "emission"
            wrong = []
            for ln in text.splitlines():
                if " = ExtResource(" not in ln:
                    continue
                slot = ln.split(" = ")[0]
                pid = ln.split('ExtResource("')[1].split('"')[0]
                want = slot_map.get(slot)
                if want and not paths[pid].endswith(f"_{want}.png"):
                    wrong.append((slot, paths[pid]))
            check(f"{m.name}.tres points each texture slot at the right map",
                  not wrong, str(wrong))
            check(f"{m.name}.tres fills every texture slot",
                  all(s in text for s in slot_map))
    check("every texture named by a material is a texture that exists",
          all(m.texture in TEX_SIZE for m in MATERIALS if m.texture),
          str([m.texture for m in MATERIALS
               if m.texture and m.texture not in TEX_SIZE]))
    check("every texture has a declared slope",
          set(TEX_SLOPE) == set(TEX_SIZE))

    # The measured colour has to survive the trip through the file. A material
    # with an albedo MAP renders albedo_color * map, so if the emitted
    # albedo_color were the measured value the surface would come out 0.72x too
    # dark -- across the whole station, uniformly, which is exactly the kind of
    # error that gets "fixed" later by raising every light.
    for m in MATERIALS:
        e = emitted_albedo(m)
        if not m.texture:
            check(f"{m.name} emits its measured albedo unchanged",
                  e == m.albedo)
        elif m.texture in COLOUR_SHEETS:
            check(f"{m.name} leaves the tint white (its sheet carries colour)",
                  e == (1.0, 1.0, 1.0))
        else:
            back = tuple(round(c * TEX_MEAN, 3) for c in e)
            want = tuple(round(c, 3) for c in m.albedo)
            check(f"{m.name}'s emitted tint times TEX_MEAN is the measured albedo",
                  back == want, f"{back} vs {want}")
    check("the signage panel is the only non-triplanar textured material",
          [m.name for m in MATERIALS if m.texture and not m.triplanar]
          == ["signage_panel"])

    # -- determinism ------------------------------------------------------
    # Pinned golden digests. Exact integers, not floats with a tolerance: the
    # first version pinned h01's float and allowed 1e-15, and a deliberate
    # 16-bit perturbation of h64 moved it by 7.8e-16 -- under the tolerance, so
    # the check passed on a changed hash. A float64 cannot hold 64 bits of
    # mantissa, so ANY float comparison here has a blind spot near the low
    # bits. The integer has none.
    #
    # This is a regression pin, not a proof of anything: changing the hashing
    # rule silently regenerates every texel in the project, and that is a diff
    # nobody would recognise as a decision unless something said so.
    check("h64's rule has not changed under it",
          (h64("drum", 3, "x"), h64("plate", 0), h64())
          == (5736871609237333484, 10151262523770139489, 16476032584258269876),
          str((h64("drum", 3, "x"), h64("plate", 0), h64())))
    check("h01 is h64 scaled into the unit interval",
          h01("drum", 3, "x") == h64("drum", 3, "x") / 2.0 ** 64)
    # And the actual property: a different interpreter with a different hash
    # salt must agree. `str.__hash__` is salted per process, so a generator
    # that reached for it would pass every in-process test and produce a
    # different station on every run. greeble.py had to be rescued from exactly
    # this, and an in-process check would not have found it.
    import subprocess
    env = dict(os.environ, PYTHONHASHSEED="99999")
    probe = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, %r); import materials as m; "
         "print(repr(m.h01('drum', 3, 'x')))"
         % os.path.dirname(os.path.abspath(__file__))],
        capture_output=True, text=True, env=env)
    check("h01 agrees across an interpreter with a different hash salt",
          probe.returncode == 0 and
          abs(float(probe.stdout.strip()) - h01("drum", 3, "x")) < 1e-15,
          probe.stdout.strip() or probe.stderr.strip()[-120:])

    a1, _, n1 = build_texture("hazard_chevron")
    a2, _, n2 = build_texture("hazard_chevron")
    check("a texture rebuilds byte-identically",
          bool(np.array_equal(a1, a2) and np.array_equal(n1, n2)))

    # -- texture properties a render cannot show --------------------------
    for name in ("hull_plate", "wall_plate", "deck_stud", "truss_steel"):
        albedo, orm, nrm = build_texture(name)
        size = TEX_SIZE[name]
        check(f"{name} albedo is the declared size",
              albedo.shape == (size, size, 3), str(albedo.shape))

        # TILEABILITY. A trim sheet is projected triplanar and tiled dozens of
        # times across one surface; a seam at the repeat is the single most
        # visible way procedural texturing betrays itself, and it is invisible
        # on a single chip.
        #
        # The first version of this compared the wrap difference against the
        # difference between two rows in the middle of the sheet, and failed on
        # a sheet that tiles perfectly. It was measuring the wrong thing: the
        # wrap of a PLATE sheet falls on a plate boundary, so it is supposed to
        # be a large step, and two rows in the middle of a plate are supposed
        # to be nearly identical. Comparing a boundary against an interior is a
        # test that a correct texture cannot pass.
        #
        # Two criteria, because neither is sufficient alone:
        #
        # SIGNED. A non-periodic term -- an fBm lattice that does not wrap, a
        # streak that runs off the bottom without coming back -- is a global
        # offset: every column steps the same way at the repeat. A legitimate
        # plate boundary at the wrap steps a different way in every column and
        # averages to nothing. So the mean SIGNED difference separates them
        # even when the magnitudes are similar.
        #
        # OUTLIER. A high-frequency non-periodicity can average to zero and
        # still be a visible seam, so the magnitude is also compared against
        # the worst gap the sheet already contains internally.
        #
        # The first version used the outlier criterion alone at a 1.02 bound,
        # and it failed on sheets that tile perfectly: once plate merging left
        # `deck_plate` with only two active row boundaries, the one at the
        # wrap was legitimately the strongest gap in the sheet. Being the
        # largest boundary is not the same as being a seam.
        #
        # Normals carry a systematically non-zero signed difference at a seam
        # -- a seam is a valley, so the gradient points one way on one side and
        # the other way on the other -- which is why the bound is 0.15 and not
        # 0.02. Measured, correct sheets run to 0.107; a ramp in the height
        # field runs to 0.24.
        for arr, tag in ((albedo, "albedo"), (nrm, "normal"), (orm, "orm")):
            gv = np.abs(np.diff(arr, axis=0)).mean(axis=(1, 2))
            gu = np.abs(np.diff(arr, axis=1)).mean(axis=(0, 2))
            sv = float((arr[0] - arr[-1]).mean())
            su = float((arr[:, 0] - arr[:, -1]).mean())
            check(f"{name} {tag} has no net step across the v wrap",
                  abs(sv) <= 0.15, f"signed {sv:+.4f}")
            check(f"{name} {tag} has no net step across the u wrap",
                  abs(su) <= 0.15, f"signed {su:+.4f}")
            wv = float(np.abs(arr[0] - arr[-1]).mean())
            wu = float(np.abs(arr[:, 0] - arr[:, -1]).mean())
            check(f"{name} {tag} v wrap is not an outlier row gap",
                  wv <= float(gv.max()) * 2.5 + 1e-6,
                  f"wrap {wv:.4f} vs worst interior {gv.max():.4f}")
            check(f"{name} {tag} u wrap is not an outlier column gap",
                  wu <= float(gu.max()) * 2.5 + 1e-6,
                  f"wrap {wu:.4f} vs worst interior {gu.max():.4f}")

        # A normal map whose z is not dominant is a normal map pointing into
        # the surface -- it renders as a black crawling mess rather than as an
        # error, which is the same failure class as an inside-out wall.
        check(f"{name} normals point out of the surface",
              float(nrm[:, :, 2].min()) > 0.0, f"min z {nrm[:, :, 2].min():.4f}")
        check(f"{name} normals are unit length",
              float(np.abs(np.linalg.norm(nrm, axis=2) - 1.0).max()) < 1e-4)
        # "Deviates from flat" is not enough on its own: a map of sheer
        # vertical walls passes it. The first bake drove the deck's 7 cm studs
        # to |xy| = 0.999 -- a floor of chrome ball bearings -- and that check
        # applauded. The SLOPE is the property, so the slope is what is
        # asserted, at both ends.
        slope = np.abs(nrm[:, :, :2]).sum(axis=2) / np.maximum(nrm[:, :, 2], 1e-6)
        p = float(np.percentile(slope, 99.5))
        check(f"{name} bakes to its declared slope, not to a resolution",
              0.5 * TEX_SLOPE[name] <= p <= 2.2 * TEX_SLOPE[name],
              f"p99.5 slope {p:.3f} vs declared {TEX_SLOPE[name]}")
        check(f"{name} normals actually deviate from flat",
              float(np.abs(nrm[:, :, :2]).max()) > 0.03,
              f"max xy {np.abs(nrm[:, :, :2]).max():.4f}")

        # Albedo maps multiply a tint, so they have to average to TEX_MEAN and
        # must not be sitting against the ceiling. The first bake averaged 0.98
        # and clipped 8% of its texels: the sheets came out near-white with the
        # plate pattern all but gone, and no assertion noticed because none was
        # about the histogram.
        if name not in COLOUR_SHEETS:
            check(f"{name} albedo is centred on TEX_MEAN",
                  abs(float(albedo.mean()) - TEX_MEAN) < 0.02,
                  f"mean {albedo.mean():.3f}")
            clipped = float((albedo >= 0.999).mean())
            check(f"{name} albedo is not clipping against the ceiling",
                  clipped < 0.005, f"{clipped * 100:.2f}% at 1.0")
            check(f"{name} albedo uses its range",
                  float(albedo.max() - albedo.min()) > 0.20,
                  f"range {albedo.max() - albedo.min():.3f}")

        # The plate lattice has to produce STEPS, not a gradient. That is the
        # whole argument against the FastNoiseLite mottling it replaces: the
        # reference's hull steps in value between plates (sd 0.037-0.095 along
        # one latitude) and organic noise cannot make a step. Measured as the
        # 99th percentile of the row-to-row difference against the median: a
        # smooth field has no tail, a plated one does.
        if name != "deck_stud":
            g = np.abs(np.diff(albedo[:, :, 0], axis=0))
            check(f"{name} albedo steps between plates rather than drifting",
                  float(np.percentile(g, 99.5)) > 8.0 * float(np.median(g) + 1e-6),
                  f"p99.5 {np.percentile(g, 99.5):.4f} med {np.median(g):.5f}")

        # ORM channels must be in the channel the .tres reads them from.
        check(f"{name} ORM has AO in red, roughness in green, metallic in blue",
              orm.shape[2] == 3 and float(orm[:, :, 0].mean()) > 0.5)
        check(f"{name} roughness stays inside (0, 1]",
              0.0 < float(orm[:, :, 1].min()) and float(orm[:, :, 1].max()) <= 1.0)

    # The deck's studs are the reason the floor measures 1.6x the wall. If the
    # stud crowns are not smoother than the ground between them, the specular
    # inversion is gone and the floor will need fake albedo again.
    _, orm_d, _ = build_texture("deck_stud")
    stud, grout = stud_field(TEX_SIZE["deck_stud"], 16)
    crown = stud > 0.85
    ground = (stud < 0.05) & (grout < 0.05)
    check("the deck sheet has stud crowns at all",
          int(crown.sum()) > TEX_SIZE["deck_stud"] ** 2 // 200,
          str(int(crown.sum())))
    check("the deck sheet has flat ground between the studs",
          int(ground.sum()) > TEX_SIZE["deck_stud"] ** 2 // 200,
          str(int(ground.sum())))
    check("stud crowns are smoother than the ground between them",
          float(orm_d[:, :, 1][crown].mean()) < float(orm_d[:, :, 1][ground].mean()),
          f"{orm_d[:, :, 1][crown].mean():.3f} vs {orm_d[:, :, 1][ground].mean():.3f}")

    # -- budget -----------------------------------------------------------
    tm = texture_memory()
    # The formula must agree with the one real measurement. A budget model that
    # has drifted from what the importer produces is worse than no model: the
    # first version assumed BC7 everywhere and over-reported by 50%.
    measured_side = sum(tm["per_set_mb"][n] for n in MEASURED_VRAM_SHEETS)
    check("the VRAM formula agrees with the measured import",
          abs(measured_side - MEASURED_VRAM_MB) / MEASURED_VRAM_MB < 0.10,
          f"formula {measured_side:.2f} MB vs measured {MEASURED_VRAM_MB} MB "
          f"over the {len(MEASURED_VRAM_SHEETS)} sheets that were measured")
    # And the measured set must still BE a subset of the live set, or the gate
    # above is comparing the model against sheets that no longer exist.
    check("every measured sheet is still in the library",
          set(MEASURED_VRAM_SHEETS) <= set(TEX_SIZE),
          str(sorted(set(MEASURED_VRAM_SHEETS) - set(TEX_SIZE))))
    check("sheets added since the measurement are named, not hidden",
          set(TEX_SIZE) - set(MEASURED_VRAM_SHEETS) == {"hull_window"},
          str(sorted(set(TEX_SIZE) - set(MEASURED_VRAM_SHEETS))))
    check("resident texture memory is inside the texture budget",
          tm["compressed_mb"] <= tm["budget_mb"],
          f"{tm['compressed_mb']:.1f} MB")
    check("even uncompressed the texture set fits VRAM",
          tm["uncompressed_mb"] <= VRAM_TEXTURE_BUDGET_MB,
          f"{tm['uncompressed_mb']:.1f} MB")
    for scene in SCENES:
        n = len(scene_materials(scene))
        check(f"{scene}'s material count is inside its draw-call budget",
              n <= DRAW_CALL_BUDGET[scene], f"{n} > {DRAW_CALL_BUDGET[scene]}")

    # -- the shader gates must be able to fail ----------------------------
    _w = BY_NAME["habitat_windows"]
    _fake = Material("probe", "probe", albedo=(0.5, 0.5, 0.5), roughness=0.5,
                     shader="hull_window", texture="hull_window",
                     shader_params={"not_a_uniform": 1.0})
    check("the shader-uniform gate rejects an invented parameter",
          not set(re.findall(r"shader_parameter/(\w+) = ", shader_tres(_fake)))
          <= shader_uniforms("hull_window"))
    check("the shader-uniform gate accepts the real material",
          set(re.findall(r"shader_parameter/(\w+) = ", shader_tres(_w)))
          <= shader_uniforms("hull_window"))

    # -- THE PLATE BETWEEN WINDOWS IS THE HULL ----------------------------
    # Measured, not asserted in prose. The first bake rendered it at 0.15
    # against the hull's 0.60 and the habitat sections read as a different
    # material. Both sides are computed here from the values that ship.
    _h = BY_NAME["hull_exterior"]
    _hull_v = TEX_MEAN * emitted_albedo(_h)[0]
    _plate_v = TEX_MEAN * _w.shader_params["albedo_color"][0]
    check("the hull between windows renders at the hull's own value",
          abs(_hull_v - _plate_v) < 0.01,
          f"windows {_plate_v:.3f} against hull {_hull_v:.3f}")
    # And the sheet must actually put TEX_MEAN there, or the arithmetic above
    # is about a number the texture does not contain.
    _v, _r, _m, _ao, _hh, _e = gen_window_sheet(256, "window")
    check("the window sheet's plate value is TEX_MEAN",
          abs(float(_v.max()) - TEX_MEAN) < 0.14,
          f"sheet max {float(_v.max()):.3f} against TEX_MEAN {TEX_MEAN}")

    # -- THE GAINS TABLE MUST STILL DESCRIBE THE FRAMES -------------------
    # GREY_WORLD_GAINS was nine numbers nobody re-derived: every interior
    # albedo in this library is a ratio against a balance computed with them,
    # and nothing checked that the balance still matched the frames it names.
    # A re-sorted, re-encoded or replaced frame would move every measurement
    # downstream of it and no gate would notice.
    #
    # So it is recomputed here, from the images, on every run. It is also the
    # method's own control: the five entries added in session 3k were accepted
    # because recomputing the four that predate them reproduces them exactly.
    try:
        import numpy as _numpy                                 # noqa: PLC0415
        from PIL import Image as _PILImage                     # noqa: PLC0415
    # NOT `_np`: this module already has a module-level `_np()` helper, and
    # binding that name locally makes every later call to it raise
    # UnboundLocalError -- Python decides scope per function, not per line.
    except ImportError:
        check("numpy and pillow are available to check the gains", False)
    else:
        drift, missing = [], []
        for frame, want in GREY_WORLD_GAINS.items():
            path = os.path.join(ROOT, "reference", frame)
            if not os.path.exists(path):
                missing.append(frame)
                continue
            a = _numpy.asarray(_PILImage.open(path).convert("RGB"),
                            dtype=_numpy.float32) / 255.0
            v = a.max(axis=2)
            sel = (v > 0.04) & (v < 0.95)
            mean = a[sel].mean(axis=0)
            got = mean.mean() / mean
            d = max(abs(float(g) - w) for g, w in zip(got, want))
            if d > 0.003:
                drift.append((frame, tuple(round(float(g), 3) for g in got),
                              want, round(d, 4)))
        check("every frame the gains table names still exists",
              not missing, str(missing[:3]))
        check("the gains table still describes the frames it names",
              not drift, f"{len(drift)}: {drift[:2]}")
        # And the check must be able to fire, or it is nine numbers again.
        _f = "07-sector-grey/grey level 1.webp"
        _p = os.path.join(ROOT, "reference", _f)
        if os.path.exists(_p):
            a = _numpy.asarray(_PILImage.open(_p).convert("RGB"),
                            dtype=_numpy.float32) / 255.0
            v = a.max(axis=2)
            sel = (v > 0.04) & (v < 0.95)
            mean = a[sel].mean(axis=0)
            got = mean.mean() / mean
            bent = tuple(w + 0.02 for w in GREY_WORLD_GAINS[_f])
            check("the gains check fires on a perturbed value",
                  max(abs(float(g) - w) for g, w in zip(got, bent)) > 0.003)

    # -- THE SCENE FILES MUST AGREE WITH THE LIBRARY ----------------------
    # The gate that would have caught this session's silent failure. The rules
    # tables used to be emitted to a .txt for a human to paste into the .tscn,
    # and `habitat_windows` -- the fix for the standing blocking finding --
    # exported cleanly, passed every assertion here, and never reached the
    # render. Godot said `fallback material used by 21 group(s)` and nothing
    # was reading it. Two other materials, `greeble_fitting` and
    # `hazard_chevron`, had been missing from the exterior scene for longer.
    #
    # `patch_scene_rules` now writes the block, so this asserts the file on
    # disk matches what the library would write -- which fails when someone
    # edits a scene by hand OR forgets to re-export.
    for scene, spath in SCENE_FILES.items():
        if not os.path.exists(spath):
            check(f"{scene} scene file exists", False, spath)
            continue
        text = open(spath).read()
        want = godot_rules(scene)
        got = dict(re.findall(r'"([a-z0-9_]+)": ExtResource\("([a-zA-Z0-9_]+)"\)',
                              text[text.index("material_rules = {"):]))
        ids = dict(re.findall(
            r'\[ext_resource type="Material" path="res://materials/'
            r'([a-z0-9_]+)\.tres" id="([a-zA-Z0-9_]+)"\]', text))
        id_to_mat = {v: k for k, v in ids.items()}
        resolved = {frag: id_to_mat.get(rid, rid) for frag, rid in got.items()}
        check(f"{scene}.tscn's material_rules match the library",
              resolved == want,
              f"missing {sorted(set(want) - set(resolved))[:4]} "
              f"extra {sorted(set(resolved) - set(want))[:4]} "
              f"differing {sorted(k for k in set(want) & set(resolved) if want[k] != resolved[k])[:4]}")
        check(f"{scene}.tscn declares every material its rules name",
              set(resolved.values()) <= set(ids),
              str(sorted(set(resolved.values()) - set(ids))))
        n = text.count("[ext_resource") + text.count("[sub_resource") + 1
        m = re.search(r"load_steps=(\d+)", text)
        check(f"{scene}.tscn's load_steps counts its resources",
              m and int(m.group(1)) == n,
              f"{m.group(1) if m else None} declared, {n} present")

    print(f"{_PASS}/{_PASS + _FAIL} passed")
    return _FAIL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="store_true",
                    help="write .tres, textures and the rules table")
    ap.add_argument("--textures-only", action="store_true")
    ap.add_argument("--sheet", metavar="PNG", help="material chip sheet")
    ap.add_argument("--texture-sheet", nargs=2, metavar=("NAME", "PNG"))
    ap.add_argument("--surface", nargs=2, metavar=("MATERIAL", "PNG"),
                    help="one material's trim sheet under a grazing key")
    ap.add_argument("--budget", action="store_true")
    ap.add_argument("--rules", metavar="SCENE")
    args = ap.parse_args()

    if args.budget:
        print(budget_report())
        return 0
    if args.rules:
        for frag, name in godot_rules(args.rules).items():
            print(f'"{frag}": {name}')
        return 0
    if args.sheet:
        print(preview_sheet(args.sheet))
        return 0
    if args.texture_sheet:
        print(texture_sheet(args.texture_sheet[1], args.texture_sheet[0]))
        return 0
    if args.surface:
        print(preview_surface(args.surface[1], args.surface[0]))
        return 0
    if args.textures_only:
        for f in export_textures():
            print("  textures/" + f)
        return 0
    if args.export:
        for f in export_tres():
            print("  " + f)
        for f in export_textures():
            print("  textures/" + f)
        print("  " + os.path.basename(export_rules_gd()))
        for scene, spath in SCENE_FILES.items():
            _p, n_rules, n_add = patch_scene_rules(spath, scene)
            print(f"  {os.path.basename(spath)}  {n_rules} rules"
                  + (f", {n_add} resource(s) added" if n_add else ""))
        print()
        print(budget_report())
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
