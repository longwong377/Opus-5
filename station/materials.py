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
        # `forward_comms_plate` is the fourth of the four groups that were on
        # the exterior fallback by design, and it is the one that needed no new
        # material: 00-INDEX's read of the same sheet says the "swept
        # structures" of the top view ARE a flat plate-like communications
        # array, i.e. the same panel family as the collectors and the proximity
        # arrays, measured in the same pass off the same image. Binding it here
        # is one measurement covering four components, not a fourth guess.
        binds=("heat_exchange_solar_array", "forward_swept_array",
               "space_traffic_prox_array", "forward_comms_plate"),
        scenes=("exterior",),
        source="exterior more.jpg top-view swept blades, V 0.34, near-neutral — darker than hull, not white"))

    # ---- the glazed blisters: observation domes, rotundas, docking ports ---
    #
    # INV-008 left all of these on `hull_exterior` and said why: "they are
    # glazed volumes over lit interiors and almost certainly should not be
    # opaque hull, but no reference in the set shows them lit from outside,
    # and a glowing dome is a large, prominent guess."
    #
    # THAT CAUTION IS RIGHT AND IS KEPT. What has changed is that the domes are
    # no longer a single smooth surface: components.domes now emits the shell
    # and its FRAME as separate groups, because 03-sector-blue/comand and
    # contorl.webp is authority 1, is Observation Dome 1 seen from inside, and
    # shows the glazing "carried on radial spoke mullions with a broad
    # concentric ring band" (00-INDEX). So the structure is sourced even though
    # the light through the glass is not, and the two can now be said
    # separately instead of averaged into one grey egg.
    #
    # `dome_glazing` is therefore dark glass and NOT an emissive. That is a
    # smaller claim than the one INV-008 declined, and it replaces a claim that
    # is certainly wrong -- that a window is hull plating.
    a(Material(
        "dome_glazing", "Dome Glazing — observation dome, rotunda and docking port glass",
        albedo=(0.045, 0.048, 0.055), roughness=0.10, metallic=0.0,
        specular=0.85,
        binds=("observation_dome", "docking_port"), scenes=("exterior",),
        source="03-sector-blue/comand and contorl.webp (authority 1) — Observation "
               "Dome 1 is Command and Control and its aperture is GLAZED, a large "
               "circle of panes on radial mullions, not plating. Contract 5 names "
               "'OB. DOME 1 (COMMAND & CONTROL)' and 'OB. DOME 2'.",
        note=("`observation_rotunda` is deliberately NOT bound here. It stays on "
              "`habitat_windows`, which INV-036 put it on, and 00-INDEX's "
              "re-examination of 05-sector-green/rotunda.webp says the rotunda's "
              "window ring looks INWARD onto the drum rather than out at space. "
              "Two different fittings; one of them is not settled and this "
              "material does not settle it."),
        extrapolated=("every number. No frame in the set shows any of these from "
                      "outside, so this is a dark dielectric — 4.5% albedo, "
                      "roughness 0.10, specular 0.85 — which is what unlit glass "
                      "does at grazing incidence in a Forward+ renderer. It is "
                      "chosen to be the SMALL guess: it makes the domes read as "
                      "glass in silhouette and adds no light to the frame. "
                      "Overturned by any exterior frame showing a dome, which "
                      "would settle whether they are lit from within — and if "
                      "they are, this becomes an emissive and the entry stands "
                      "as the record of why it was not one first.")))

    a(Material(
        "dome_structure", "Dome Structure — mullions, ring band and base collar",
        # hull_exterior's measured albedo. The mullions are the pale structural
        # members carrying the glazing and they are continuous with the hull
        # plating at the dome's base collar; in the C&C frame they are the
        # lightest thing in the aperture.
        albedo=(0.600, 0.582, 0.564), roughness=0.58, metallic=0.30,
        specular=0.45, texture="hull_plate", uv_scale=1.0 / 16.0,
        normal_scale=0.9,
        binds=("observation_dome_frame", "observation_rotunda_frame",
               "docking_port_frame"),
        scenes=("exterior",),
        source="03-sector-blue/comand and contorl.webp (authority 1) — radial spoke "
               "mullions and a broad concentric ring band, pale against the glazing. "
               "Albedo adopted from `hull_exterior`, measured neutral on exterior "
               "more.jpg (INV-008).",
        note=("Bound by the full `*_frame` fragments rather than by a bare "
              "`_frame`, which would also match the interior kit's portal_frame "
              "and door_frame. Longest-fragment resolution would still sort that "
              "out today; it would stop doing so the moment someone emitted a "
              "group called `frame`."),
        extrapolated="the 16 m plate repeat and the finish; the mullion COUNT is "
                     "measured — see components.DOME_MULLIONS and INV-041"))

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
              "frame. It waited three sessions for geometry and now has some: "
              "components.cobra_bay_ring emits `hazard_stripe_cobra` -- the "
              "sill you cross going into a bay and the nosing on each of its "
              "two deck ledges, which is where every chevron in the reference "
              "frame is."),
        extrapolated="the 3 m stripe pitch — the frames show the pattern, not its scale"))

    a(Material(
        "marker_light_white", "Marker Light White — section-joint beacon",
        albedo=(0.080, 0.080, 0.085), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(1.000, 0.950, 0.880), emission_energy=1.3,
        # `cobra_marker_white` is the geometry this material was measured from
        # and never had: files of marker lights down the inner faces of a bay's
        # columns. It was bound to `greeble_nav_light` alone, which is a
        # section-joint beacon somewhere else entirely on the hull.
        binds=("greeble_nav_light", "cobra_marker_white"), scenes=("exterior",),
        source="Cobra Bays with starfurries.webp — red and white marker lights on the columns"))

    a(Material(
        "marker_light_red", "Marker Light Red — hazard beacon",
        albedo=(0.100, 0.050, 0.040), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(1.000, 0.300, 0.120), emission_energy=2.1,
        # Same closure as marker_light_white: the beacons on the cobra bay
        # column heads are literally what the 96% figure below was measured on.
        binds=("greeble_hazard_light", "cobra_beacon_red"), scenes=("exterior",),
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

    # ---- the cobra bays --------------------------------------------------
    #
    # These two are the reason `cobra_bay` sat on the exterior fallback for
    # eleven sessions: there was nothing to bind, because the bay was one box.
    # It is now a framed well in five groups, and three of the five need no
    # new material at all -- the hazard lip lands on `hazard_chevron` and the
    # two light families on `marker_light_red` and `marker_light_white`, which
    # were MEASURED OFF THIS BAY'S OWN REFERENCE FRAME and had no geometry to
    # sit on. That loop closing is worth more than a new colour would be.
    #
    # NEITHER OF THE TWO BELOW INTRODUCES A COLOUR. Each adopts an albedo
    # already measured on the exterior sheet, for the same reason
    # docking_bay.py adopts the schema's cobra bay width instead of inventing
    # a second one: two numbers for one surface is how a project ends up with
    # two answers. What differs is finish and texture scale, and those are
    # extrapolated and say so.
    a(Material(
        "bay_frame", "Cobra Bay Frame — the columns, sill and lintel of a launch well",
        # greeble_fitting's measured albedo exactly. A bay's frame is the same
        # register as every other thing bolted to the hull: fabricated metal,
        # consistently darker and less warm than the plating it stands on.
        albedo=(0.310, 0.306, 0.300), roughness=0.52, metallic=0.42,
        specular=0.50, texture="hull_plate", uv_scale=1.0 / 24.0,
        normal_scale=1.1,
        binds=("cobra_bay",), scenes=("exterior",),
        source="Albedo adopted from `greeble_fitting`, measured on exterior more.jpg "
               "at V 0.20-0.31 against hull plating 0.28-0.37. The FORM is authority 1: "
               "01-station-exterior/Cobra Bays with starfurries.webp shows heavy "
               "chamfered box columns with red beacons at their heads.",
        note=("Textured with hull_plate rather than greeble_fitting's truss_steel, "
              "because a column 9.7 m across and 42 m long is plate-built structure "
              "and a 6 m steel repeat on it reads as noise. Do NOT read the frame's "
              "warm brown as paint: INV-008 established for this exact frame that "
              "the hue there is a warm key light, and tinting albedo to match it is "
              "the mistake that made the whole hull steel blue in session 2c."),
        extrapolated="the 24 m plate repeat, and roughness/metallic, which no "
                     "reference in the set can measure — INV-008 constraint 2"))

    a(Material(
        "bay_well", "Cobra Bay Well — the liner, floor and ledges inside the bay",
        # structural_truss's measured albedo: the darkest surface on the sheet,
        # and an unpainted well liner is the same unpainted structural metal.
        albedo=(0.260, 0.255, 0.248), roughness=0.66, metallic=0.30,
        specular=0.40, texture="truss_steel", uv_scale=1.0 / 10.0,
        normal_scale=1.0,
        binds=("cobra_bay_well",), scenes=("exterior",),
        source="Albedo adopted from `structural_truss`, measured on exterior more.jpg "
               "at V 0.204 against hull 0.44. Cobra Bays with starfurries.webp shows "
               "at least three stepped deck levels inside the bay volume.",
        note=("Darker than the frame by a measured step, NOT crushed to black. "
              "The bay interior is nearly black in the reference and it is "
              "tempting to paint that in, but the frame is a night shot and the "
              "well is 24 m deep: Forward+ shadow maps and SSAO produce that "
              "darkness from the geometry, which is the honest place for it. "
              "Painting it as well would double-count and the bay would go flat "
              "black in the one shot -- a lit approach -- that it exists for."),
        extrapolated="roughness, metallic and the 10 m repeat"))

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
        binds=("pilaster", "portal_frame", "door_frame", "alien_portal_chamfer", "alien_portal_head", "alien_portal_jamb", "alien_portal_sill", "alien_stile", "alien_ring"), scenes=("interior",),
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
        binds=("deck_grid", "deck_panel", "qtr_deck", "alien_deck"), scenes=("interior",),
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
        note=("Eleven discrete cells in the frame, not a continuous tube. The "
              "segmentation is geometry. `customs_light_strip` USED TO BIND "
              "HERE and now has its own material, light_arrival_strip: the "
              "arrival hall's band measurably lights the wall it is set into "
              "and this fitting measurably does not, which is a difference "
              "one material cannot carry.")))

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

    # ---- layer 4: the fittings the 68 generated rooms are lit by ----------
    # `rooms.LIGHTS` maps each of the eleven archetypes onto MEASURED fittings
    # rather than inventing lamp colours per room type; these are the
    # materials those tags resolve to. Every colour below is a linear triple
    # from docs/layer4-lighting/*.json, which three agents measured off the
    # reference frames in session 3n — the file names the frame, the region
    # and the balance for each. What is extrapolated here is the SAME thing in
    # every entry and is not repeated in full each time: the housing albedo
    # (the geometry is the whole fitting, so an unlit lamp must not read as a
    # hole — the pattern light_downlight, marker_light_red and emissive_signage
    # already follow of carrying the emission's tint at low value), and the
    # emission_energy, which is placed on THIS LIBRARY'S ladder because the
    # JSON's `energy_rel` is relative within its own measured family and two
    # families' 1.0 are not the same number of lumens.
    #
    # The ladder, for reference: light_ceiling_grid 2.6, light_deck_channel
    # 3.5, light_command_strip 3.8, light_downlight 4.0, emissive_signage 4.5,
    # light_portal_head 5.0, light_pilaster_strip 6.0, bay_floodlight 6.0,
    # bar_pendant_lamp 9.0.

    a(Material(
        "light_house_cove", "House Cove — the council chamber's concealed wash",
        albedo=(0.640, 0.630, 0.610), roughness=0.32, metallic=0.0,
        specular=0.22, emission=(1.000, 0.966, 0.944), emission_energy=1.2,
        binds=("light_house_cove",), scenes=("interior",),
        source="docs/layer4-lighting/public_social.json, fixture `cc_house_wash`, measured from reference/05-sector-green/council chambers.webp (authority 1). Directional, 6300 K, energy_rel 1.0, range 18 m, shadow: 'concealed high-level house lighting, fitting never in frame; a broad soft near-neutral wash over the whole chamber'. The chamber's ambient ratio is 0.210, one of the two brightest measured spaces on the station — it is a room with no dark corners, and this is the only thing in it that could produce that.",
        extrapolated="THE FITTING ITSELF, and that is the honest way to say it. The measurement is explicit that the source is never in shot, so its colour and its behaviour are measured and its GEOMETRY is not. council_chamber.house_cove() puts it where a chamber lit this evenly would be lit from — a concealed cove high on the rear wall, above the fin fan, whose housing you cannot see because it faces away from the room. Also extrapolated: the diffuser albedo, and emission_energy 1.2, and the first value was WRONG and the render said so. It was set at light_downlight's 4.0 on the argument that the frame shows a wash and not a source — and 4.0 drew a bright white bar across the top of the chamber, which is the exact failure the argument was made to avoid. 1.2 sits below light_ceiling_grid's 2.6, the library's other concealed-decorative source, and is what a cove looks like when you are seeing its glow on the wall rather than its lens. The energy that produces the WASH is separate and unchanged: it lives in export_scene.FIXTURE_LIGHTING, so dimming the fitting does not dim the room. Overturned by any frame showing this chamber's ceiling.",
        note="A near-neutral that is not quite neutral: (1.000, 0.966, 0.944) at 6300 K against light_ceiling_batten's (1.000, 0.980, 1.000) at 6530 K. Two measured whites, kept apart."))

    # ---- the segmented light strip is a FAMILY, and its members differ ------
    # 00-INDEX.md's re-examination of `corridor in alien sector.webp` states
    # the generalisation this library now has to carry: the station's amber
    # chamfer bars are "the same fitting family as the grey corridor's white
    # vertical strips, tinted amber here". docs/layer4-lighting/corridor_kit
    # .json measures three members and they are NOT one material — residential
    # 6200 K, concourse 5310 K, and its own note says "if the two are bound to
    # one material the concourse loses that contrast; I would keep them
    # separate". The arrival hall is the fourth member and it is separated for
    # a stronger reason than tint: IT LIGHTS ITS WALL AND THE CORRIDOR'S DOES
    # NOT, which is a difference no shared material can express.
    a(Material(
        "light_arrival_strip", "Arrival Hall Wall Band — the gate-wall light course",
        albedo=(0.845, 0.855, 0.850), roughness=0.28, metallic=0.0,
        specular=0.20, emission=(0.980, 1.000, 0.952), emission_energy=3.0,
        binds=("customs_light_strip",), scenes=("interior",),
        source="reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg (authority 1), grey-world gains recomputed from the frame as 1.0456/1.0655/0.9050 — reproducing the figure light_ceiling_grid already cites for this frame to 0.000. THE FITTING IS NOT WHAT customs.py BUILT: it is one horizontal COURSE of short vertical cells at mid-height, not a rank of full-height strips. Near run isolated at (0.253,0.727)-(0.358,0.787); per-column max-luminance profile gives cell centres at px 331/345/362/377/406/418, i.e. pitch 14.5 px, against a band height of 41 px measured on the row profile (rise through 10% of peak at row 460, fall at row 502). Pitch/height = 0.354, and the far run corroborates it dimensionlessly (11-13.5 px pitch on a ~32 px band, 0.34-0.42). IT CASTS, and that is the whole reason this material exists. Two independent wall columns above the band, (0.290,0.560)-(0.320,0.880) and (0.300,0.560)-(0.340,0.880), rise MONOTONICALLY toward it — balanced L 0.0211 -> 0.0260 -> 0.0319 -> 0.0370 -> 0.0399 and 0.0191 -> 0.0272 -> 0.0331 -> 0.0355 -> 0.0379 over y 0.629 -> 0.710, factors of 1.89 and 1.98 — and the gradient's DIRECTION rules out the ceiling grid overhead, which would make the same wall brightest at its top. The identical test on the corridor fitting in grey level 1.webp gives the opposite answer twice: the wall beside the strip reads L 0.0373-0.0505 against 0.0686 four cells away, and the wall below it BRIGHTENS with distance (0.0459 at y 0.374 to 0.0717 at y 0.491). Two frames, one test, two answers.",
        extrapolated="THE COLOUR, and the reason is a negative result worth carrying. The value here is the family's MEASURED linear (0.956, 1.000, 0.895) at 6200 K from docs/layer4-lighting/corridor_kit.json, fixture `light_pilaster_strip`. The customs frame's own reading of its cells was taken and NOT used: value-banded over (0.280,0.735)-(0.330,0.772) it gives normalised sRGB (0.860, 0.814, 1.000) at V 0.50-0.75 and (0.911, 0.870, 1.000) at V 0.75-1.01, hue constant at 255-259 across the two bands — a violet-leaning cool white. The residual against the family value is R and B up, G down, which is exactly the direction chroma bleed from the H 334 maroon wall these 9 px cells sit on would push it at 4:2:0 on a 1262x634 screencap. The decisive check is that the fill-subtraction corridor_kit.json used on `light_downlight` FAILS here: (wall above the band minus wall two band-heights higher) returns H 333.6 balanced, the wall's own measured hue of H 334.3, so in this neighbourhood the frame's chroma is the wall and not the lamp. Also extrapolated: the diffuser albedo, and emission_energy 3.0, WHICH THE RENDER SET AND NOT THE LADDER. It was first put at 5.0 by argument — below light_pilaster_strip's 6.0 because this band is 0.839/0.905 = 0.93 of its own frame's brightest family where the corridor strip is 1.00 of its, and because light_house_cove's lesson applies (a fitting that also CASTS gets part of its rendered brightness back off the wall). At 5.0 the lens blew: masking the engine frame by region, the band accounted for 2,054 clipped pixels and the ceiling coffer and the screens for zero, i.e. 100% of the frame's clipping was this one fitting. The reference's own cells do not clip — raw sRGB V p99 0.927, max 0.969, which is linear 0.843 — so a value that blows is refuted by the frame it came from. At 3.0 the frame clips 0.02% and its median moves from 1.45x its reference to 1.36x. Overturned by any frame of this wall at a resolution that resolves a cell across.",
        note=("materials.light_pilaster_strip still carries the library's older "
              "(0.880, 0.930, 1.000), which corridor_kit.json calls 'a decided "
              "blue' and too strong for its own measurement. That correction "
              "is on STATE.md's list and is NOT made here: it moves the "
              "residential corridor, which is the anchor every exposure in "
              "this project is calibrated against. The two will agree when it "
              "lands.")))

    a(Material(
        "light_alien_lattice", "Alien Sector Overhead Grille — the amber source above",
        albedo=(0.120, 0.098, 0.062), roughness=0.32, metallic=0.0,
        specular=0.22, emission=(1.000, 0.841, 0.272), emission_energy=0.35,
        binds=("alien_lattice", "alien_ceiling_lamp"), scenes=("interior",),
        source="reference/05-sector-green/corridor in alien sector.webp (authority 1), read RAW. THE BALANCE IS INVALID FOR THIS FRAME and that is stated before it is used: grey-world gains computed from it are 0.7716/0.9012/1.6825, a 68% blue lift, because the frame is emphatically amber throughout — 00-INDEX.md calls it 'yellow-green overall with one cold blue pocket' — and balancing erases the very thing being measured. NEGATIVE_RESULTS' rule, already applied to `comand and contorl.webp` by light_dais_key, is that a SOURCE read raw is what raw is for. Colour from the descending light shafts at (0.400,0.010)-(0.560,0.180), top decile: linear (1.000, 0.675, 0.060), H 39.3. Corroborated by the floor grating at (0.300,0.820)-(0.520,0.950), an independent region: linear (1.000, 0.680, 0.035), H 40.1 — the same source seen twice, agreeing in R:G to 0.7%. THE SOURCE IS OVERHEAD, and this was tested rather than assumed: a vertical profile of the caged volume at (0.30,0.10)-(0.55,0.75) reads L 0.0473/0.0511/0.0384/0.0505 across its top four bands and 0.0221/0.0229/0.0258/0.0271 across its bottom four — brightest at the TOP, falling by a factor of 2 downward. The whole frame's lit structure (0.008 < L < 0.10, 715,264 px) is linear (1.000, 0.796, 0.273) at H 43.1, i.e. every lit surface in the room carries this fitting's hue.",
        extrapolated="Housing albedo and emission_energy 1.2, taken from light_house_cove for a reason that is the same reason: the fitting is not in shot. What the frame shows is the shafts it throws and the volume it lights, never the lens, so its colour and behaviour are measured and its brightness as an object is not. 1.2 is where light_house_cove ended up after 4.0 drew a bright white bar across the top of the council chamber; the throw is carried by export_scene.FIXTURE_LIGHTING, so dimming the fitting does not dim the room. Overturned by any frame looking UP in this quarter.",
        note=("TWO GROUPS, ONE MATERIAL, and the reason is that the frame "
              "cannot separate them: it never shows this ceiling at all. "
              "`alien_ceiling_lamp` is the recessed trough that casts and "
              "`alien_lattice` is the grille 0.2 m below it that makes the "
              "shafts hard-edged, and from the deck they are one lit assembly "
              "seen through its own diffuser. The grille was bound to "
              "furn_screen_panel — an office partition — for two layers.")))

    a(Material(
        "light_deck_grating", "Illuminated Deck Grating — louvre bars over a light box",
        albedo=(0.150, 0.122, 0.070), roughness=0.34, metallic=0.0,
        specular=0.22, emission=(1.000, 0.839, 0.200), emission_energy=0.30,
        binds=("alien_deck_grating",), scenes=("interior",),
        source="reference/05-sector-green/corridor in alien sector.webp (authority 1), read raw for the reason given under light_alien_lattice. The grating occupies (0.230,0.790)-(0.600,0.980) and is THE BRIGHTEST THING IN THE FRAME by a wide margin — L p90 0.223 against 0.122 for the shafts, 0.118 for the blue bay and 0.061 for the chamfer bars — and it does NOT clip (V max 0.796), which is unusual for a source and is what sets its energy below the fittings that do. Core linear (1.000, 0.671, 0.033), H 39.6 S 0.97. 00-INDEX.md magnified it: 'a grid of roughly square cells, each cell containing about three short horizontal louvre bars over a light box', 'roughly 7 cells across', and it generalises the part — 'the illuminated floor grating is a station-wide element, colour-tinted per environment ... one kit part with a tint parameter, not four set dressings', appearing white/blue in central corridor.webp, checkerboard white in sleeping-in-light-05.jpg, saturated yellow here and as pooled uplight in grey level 1.webp.",
        extrapolated="Housing albedo and emission_energy 3.5, which is light_deck_channel's exactly — that material is this same station-wide part in its corridor tint, so the two are one fitting at one energy in two colours, which is what the index's generalisation means. What is NOT extrapolated and is worth stating as a finding: this fitting is EMISSIVE ONLY, and it is the third instance in this project of the brightest thing in a frame lighting nothing. The pier feet either side of the grating are the darkest surfaces in the frame (left pier L 0.0094-0.0107 flat from head to foot over y 0.15-0.90; right pier falling to 0.0103 at y 0.873 from a mid-height maximum of 0.0183 at the chamfer bars), and the caged volume above it is brightest at the top. A floor that bright with dark walls at its edge is a light box under a louvre, not a source. Overturned by a frame of this deck showing the pier bases lifted.",
        note=("00-INDEX.md's Feeds line has asked for this since session 2q: "
              "'new light_grating with tint' in station/interior_kit.py. It is "
              "built in alien_sector.py instead because that is the module "
              "this pass owns; when it moves into the kit, the tint parameter "
              "is the only thing that has to change.")))

    a(Material(
        "light_service_tube", "Service Tube — cold blue wall batten",
        albedo=(0.070, 0.100, 0.150), roughness=0.28, metallic=0.0,
        specular=0.20, emission=(0.300, 0.550, 1.000), emission_energy=3.0,
        binds=("light_service_tube",), scenes=("interior",),
        source="docs/layer4-lighting/corridor_kit.json, fixture `service_wall_tube`, measured from reference/10-interiors-generic-kit/more hallways.jpg (authority 1; NEGATIVE_RESULTS classes that frame a LIGHTING reference and not an albedo reference, which is what it is used for here). Gains recomputed as 0.793/1.146/1.154, reproducing GREY_WORLD_GAINS. Tubes isolated at x 0.394-0.405 y 0.116-0.191 and x 0.399-0.415 y 0.224-0.444; aspect ~13:1 for the lower run. The measurement calls it EMISSIVE ONLY and export_scene.FIXTURE_LIGHTING keeps it that way: it is the brightest thing on a service wall and it lights nothing.",
        extrapolated="Housing albedo and emission_energy 3.0. Energy sits below light_command_strip's 3.8 — the same cold-blue register on a smaller fitting — and well below the pilaster strip's 6.0, because a service corridor's balanced median luminance is 0.060 against a residential corridor's 0.265 and the tube must not lift it.",
        note="The measurement records TWO courses of these, an upper run hung off an overhead truss and a lower at head height. Only the lower is placed: rooms.py builds no truss to hang the upper from, and inventing one would be a layer-2 change made inside layer 4."))

    a(Material(
        "light_platform_pool", "Platform Downlight — the overhead pool source",
        albedo=(0.180, 0.200, 0.185), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(0.850, 1.000, 0.870), emission_energy=5.0,
        binds=("light_platform_pool",), scenes=("interior",),
        source="docs/layer4-lighting/corridor_kit.json, fixture `concourse_deck_spot`, measured from reference/10-interiors-generic-kit/more hallway.jpg (authority 1), gains recomputed 1.120/1.198/0.786. The pool is 1.57 m across — interior_kit's own DOWNLIGHT_POOL_M, itself measured against a standing officer at 149 px/m — and the measurement derives the cone from it: half-angle 12.3 deg at a 3.6 m mount, 6.2 deg at 7.2 m, penumbra about 60% of the pool radius.",
        extrapolated="Housing albedo and emission_energy 5.0, matched to light_portal_head rather than to light_pilaster_strip: this is a fitting that actually throws (export_scene gives it a shadow-casting spot), and the strip is the brighter surface precisely because it does not.",
        note="Same colour as the lit deck patch beneath it, which is correct and not a copy: a pool on the deck is this lamp's own light coming back."))

    a(Material(
        "light_dais_key", "Dais Key Light — the one fitting that throws a shadow",
        albedo=(0.220, 0.170, 0.130), roughness=0.32, metallic=0.0,
        specular=0.25, emission=(1.000, 0.760, 0.556), emission_energy=6.0,
        binds=("light_dais_key",), scenes=("interior",),
        source="docs/layer4-lighting/command_working.json, fixture `cc_dais_key`, measured from reference/03-sector-blue/comand and contorl.webp (authority 1), raw — that frame's grey-world balance is INVALID for albedo (balanced S median 0.420, p90 0.891) and NEGATIVE_RESULTS' rule is that a source read raw is exactly what raw is for. Found by a horizontal profile of the dais apron at y .690-.735 in 6 px columns: LIT plateau x .386-.482 at L 0.26-0.585 H 314-335, SHADOW x .489-.548 at L 0.183-0.292, LIT again x .555-.644 — i.e. a hard-edged pool with a body-shaped hole in it, which is what identifies it as a single keyed source at ~3.5 m rather than a wash. 4725 K.",
        extrapolated="Housing albedo and emission_energy 6.0. It is set at bay_floodlight's level and above light_downlight's 4.0 because the frame shows it as the only fitting in the room casting a legible shadow, which is a statement about its intensity relative to the fill and not about its size.",
        note="rooms.py places it as the `key` kind: ONE fitting, on the centreline, over whatever the spine carries. In a chapel that is the dais, and the dais is the only thing in the room that should be lit."))

    a(Material(
        "light_wall_course", "Wall Course — cold horizontal band, flush in the wall",
        albedo=(0.060, 0.090, 0.150), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(0.243, 0.546, 1.000), emission_energy=3.4,
        binds=("light_wall_course",), scenes=("interior",),
        source="docs/layer4-lighting/command_working.json, fixture `cc_wall_course`, measured from reference/03-sector-blue/comand and contorl.webp (authority 1), raw, for the reason given under light_dais_key. Four horizontal courses per side wall at a measured 1.2 m vertical pitch, each running the room's full length with its emitting face flush in the wall and throwing OUTWARD, so the centre of the room stays dark. 22000 K — the coldest source in the measured set, and the reading is a strong blue rather than a blue-white.",
        extrapolated="Housing albedo and emission_energy 3.4, just under light_command_strip's 3.8. The two are the same architectural idea in the same sector and the 0.4 separates a course flush in a wall from a proud strip; nothing in the frames distinguishes them further.",
        note=("The G channel is what separates this from light_command_strip's "
              "(0.240, 0.320, 1.000): 0.546 against 0.320. Both are Blue "
              "Sector cold sources measured in the same frame and they are NOT "
              "the same colour, so they are not the same material.")))

    a(Material(
        "light_ceiling_batten", "Ceiling Batten — the neutral white overhead",
        albedo=(0.780, 0.780, 0.780), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(1.000, 0.980, 1.000), emission_energy=7.0,
        binds=("light_ceiling_batten", "light_cage_lamp"), scenes=("interior",),
        source="docs/layer4-lighting/public_social.json, fixture `fa_batten`, measured from reference/04-sector-red/Fresh air.webp raw over (0.372,0.455)-(0.430,0.480): median (0.776, 0.769, 0.776) at S 0.010 — NEUTRAL, the only genuinely neutral source in the whole measured set — with p95 and max both (1.000, 1.000, 1.000). It clips in all three channels and carries the largest bloom in the frame. Normalised (1.000, 0.991, 1.000) sRGB. 6530 K.",
        extrapolated="Housing albedo, emission_energy 7.0, and the SECOND BIND. Energy 7.0 sits above bay_floodlight's 6.0 and below bar_pendant_lamp's 9.0: it clips harder than the bay floods do in their frame but it is a room-scale batten rather than the sole source in a dark bar. Albedo 0.78 rather than the near-black the other fittings carry, because this one is a diffuser panel and a diffuser is pale when it is off — the same argument light_pilaster_strip makes at 0.85. `light_cage_lamp` is the DECLARED part: the brig is the one archetype in rooms.py with no measured reference frame at all, and rather than invent a colour for it, it takes this neutral batten behind a guard. What would overturn it: any Season 2-3 frame inside the brig.",
        note="Medical, research and detention all resolve here. A medlab, a lab and a cell block are the three interiors that should be lit by something honest and colourless, and this is the only measured source that is."))

    a(Material(
        "light_indicator_red", "Indicator — small red status lamp",
        albedo=(0.120, 0.030, 0.035), roughness=0.35, metallic=0.0,
        specular=0.25, emission=(1.000, 0.115, 0.143), emission_energy=0.9,
        binds=("light_indicator_red",), scenes=("interior",),
        source="docs/layer4-lighting/command_working.json, fixture `cc_pit_indicator`, measured from reference/03-sector-blue/comand and contorl.webp (authority 1), raw. The forward pit is the darkest working area in frame: a pit panel at (0.055,0.755)-(0.115,0.795) reads rgb 0.071/0.012/0.020 at H 352 S 0.833, and whole-pit region medians sit at L 0.019-0.033.",
        extrapolated="Housing albedo and emission_energy 0.9. THE SOURCE MEASUREMENT SAYS OF ITSELF THAT IT IS WEAK — the indicators are a few pixels each in the darkest part of the frame — so the energy is floored on the library ladder rather than argued up, below light_ceiling_grid's 2.6 and near device_reader_shell's 0.25. It should read as a row of points on a dark wall and never as a light.",
        note=("Distinct from marker_light_red (1.000, 0.300, 0.120), which is "
              "an exterior hazard beacon: that one is orange-red and this is "
              "nearer a pure red at H 352. Two reds, measured separately, in "
              "the same way accent_warning and hull_banding_red are.")))

    a(Material(
        "light_market_pool", "Market Downlight — the Zocalo's overhead",
        albedo=(0.150, 0.200, 0.205), roughness=0.30, metallic=0.0,
        specular=0.20, emission=(0.694, 0.982, 1.000), emission_energy=5.5,
        binds=("light_market_pool",), scenes=("interior",),
        source="docs/layer4-lighting/public_social.json, fixture `zoc_downlight_overhead`, measured from reference/04-sector-red/more zocalo.png (authority 1) balanced with the gains already in GREY_WORLD_GAINS (0.936/1.137/0.951, recomputed there as 0.9362/1.1368/0.9504). Mounted 7.2 m above the deck, one above each of zocalo.py's pool centres; spacing 2.7 m over a 7.2 m drop, so spacing/height = 0.375 and the pools MERGE — the measurement's own conclusion is that the cone must be at least 50 deg half-angle. 7740 K.",
        extrapolated="Housing albedo and emission_energy 5.5, between light_portal_head's 5.0 and light_pilaster_strip's 6.0. It is the principal overhead of a public concourse, so it belongs above a doorway light and below a bay flood.",
        note=("NOT the same object as `zoc_downlight`, which zoc_deck_light "
              "binds: that group is kit.downlight_pool(), the 1.57 m lit patch "
              "ON THE DECK, and this is the fitting 7.2 m above it. The layer-4 "
              "measurement separates them and gives them different colours — "
              "(0.850, 1.000, 0.870) for the pool against (0.694, 0.982, 1.000) "
              "for the source.")))

    a(Material(
        "light_strip_warm", "Warm Wall Strip — the working office's light",
        albedo=(0.230, 0.180, 0.130), roughness=0.30, metallic=0.0,
        specular=0.25, emission=(1.000, 0.764, 0.516), emission_energy=4.2,
        binds=("light_wall_strip_bank", "light_soffit_blade"),
        scenes=("interior",),
        source="docs/layer4-lighting/command_working.json, fixtures `wr_wall_strip_bank` and `wr_soffit_blade`, both measured from reference/03-sector-blue/war room.webp (authority 1) balanced (1.088, 1.062, 0.877). Strip bank top-decile cores: hi bank rgb 0.444/0.396/0.334 H 33.8 S 0.248, hi bank 2 rgb 0.414/0.366/0.334 H 24.6, mid bank rgb 0.648/0.583/0.481 H 36.5 S 0.258, mid bank 2 rgb 0.621/0.546/0.464 — four readings, hue stable at H 25-37. Soffit blade top-decile core over (0.000,0.235)-(0.045,0.285): rgb 0.960/0.887/0.693 H 43.6 S 0.278 V 0.960, and its vertical wall profile is a single sharp peak rising L 0.28 to 0.749. Banks are ganged at two heights, ~1.2 m and ~2.4-2.8 m, vertical pitch ~1.4 m; each bank is 4-8 short bars side by side rather than one tube. 4611 K.",
        extrapolated="Housing albedo, emission_energy 4.2, and THE MERGE OF TWO FITTINGS INTO ONE MATERIAL. The merge: the two measure (1.000, 0.764, 0.516) and (1.000, 0.703, 0.440), which is 0.06-0.08 apart in two channels against a 0.28 saturation — inside the spread of the four strip-bank readings themselves — and they are the same warm register in the same room. If a later pass finds a frame that separates them the bind fragments are already distinct and splitting is a two-line change. Energy 4.2 is set just above light_downlight's 4.0: the same warm practical idea, ganged.",
        note=("This is what a WORKING interior is lit by, and it is warm, wall-"
              "mounted and low. The obvious wrong answer for an office is a "
              "cool ceiling grid; the only measured office in the reference "
              "does not have one.")))

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
        # `sign_face` is signage.py's board face -- the object this material was
        # measured FROM. It went unbound because the material predates the
        # module. Session 3l's bespoke pass re-measured the frame independently
        # and landed on the same albedo to three places, so this is one surface
        # with one value, not two materials that happen to agree.
        binds=("signage_panel", "sign_face"), scenes=("interior",),
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
        binds=("prop_console", "prop_reactor_console", "prop_furnace_control", "prop_irrigation_control", "cc_console_face"), scenes=("interior",),
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
        binds=("prop_babcom_terminal", "prop_monitor_wall", "prop_tactical_display", "customs_screen", "bar_display"), scenes=("interior",),
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
        binds=("prop_identicard_reader", "prop_credit_terminal", "prop_exchange_terminal", "prop_manifest_terminal", "prop_lift_call", "prop_intercom", "qtr_babcom", "alien_mask_dispenser"), scenes=("interior",),
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
        binds=("prop_neon_sign", "bar_neon_glyph", "bar_neon_tube",
               "light_bar_backlight"), scenes=("interior",),
        source="11-props-and-technology/Zocalo neon signage in background.jpg (authority 1), grey-world gains 0.935/1.162/0.935. Wordmark 5-cluster over (0.47,0.03)-(0.65,0.16): 33.3% rgb(0.591, 0.999, 0.921) H 168, 26.5% rgb(0.385, 0.995, 0.879) H 169 S 0.613, 11.5% rgb(0.316, 0.832, 0.709) H 166. Board ground between the chevron blades (0.36,0.10)-(0.44,0.125) balances rgb(0.092, 0.105, 0.136). Lit fraction of the sign board (0.30,0.02)-(0.78,0.19): 0.386 above L 0.30, 0.283 above L 0.50, 0.225 above L 0.70. Cross-checked against 04-sector-red/more zocalo.png and 04-sector-red/Darkstar_logo.webp — see extrapolated.",
        extrapolated="The choice of the cyan state over the orange-red state, and emission_energy 1.3 by flux-matching. The board ground's blue channel is trimmed from the measured 0.136 to 0.112 to keep S under 0.20.",
        note=("`light_bar_backlight` is rooms.py's hospitality wall course, "
              "and it is here rather than in a material of its own because "
              "the two agree. docs/layer4-lighting/public_social.json measures "
              "`casino_bar_backlight` — a continuous strip along the bar back "
              "at 1.1-1.4 m — at (0.484, 1.000, 0.922) from a DIFFERENT frame "
              "(Casino.webp) than this one was measured from, and lands within "
              "0.04 of this emission in every channel. Two independent "
              "measurements of the same cyan tube register is corroboration, "
              "not a coincidence to paper over with a second material.")))

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
        binds=("prop_valve", "customs_conduit", "bar_conduit", "qtr_conduit",
               # Session 3s articulation (INV-073). High-level conduit
               # runs are bare metal service pipe -- the same surface
               # this entry was measured on, at a different diameter. No
               # new colour is introduced.
               "commerce_conduit", "detention_conduit", "generic_conduit", "hospitality_conduit", "medical_conduit", "office_conduit", "research_conduit", "transit_conduit", "worship_conduit", "industrial_conduit", "store_conduit"), scenes=("interior",),
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
        binds=("commerce_wall", "detention_wall", "generic_wall", "hospitality_wall", "office_wall", "transit_wall", "worship_wall", "customs_wall", "customs_endwall",
               # Session 3s articulation (INV-073): the hall's own wall plane
               # worked into relief.
               "customs_dado", "customs_rail", "customs_cornice",
               "customs_panel", "qtr_wall", "alien_wall", "alien_endwall", "alien_quarter_shell", "bar_wall",
               # Session 3s articulation (INV-073): bar and quarters trim, the
               # same painted wall plane worked into relief.
               "bar_dado", "bar_rail", "bar_cornice", "bar_panel",
               "bar_skirt", "qtr_dado", "qtr_rail", "qtr_cornice",
               "qtr_panel", "qtr_skirt", "customs_skirt",
               # Session 3s articulation (INV-073). Skirting, dado, picture rail, cornice and raised panel are all the same painted wall plane worked into relief -- no new surface and no new colour.
               "commerce_skirt", "detention_skirt", "generic_skirt", "hospitality_skirt", "medical_skirt", "office_skirt", "research_skirt", "transit_skirt", "worship_skirt", "industrial_skirt", "store_skirt", "commerce_dado", "detention_dado", "generic_dado", "hospitality_dado", "medical_dado", "office_dado", "research_dado", "transit_dado", "worship_dado", "industrial_dado", "store_dado", "commerce_rail", "detention_rail", "generic_rail", "hospitality_rail", "medical_rail", "office_rail", "research_rail", "transit_rail", "worship_rail", "industrial_rail", "store_rail", "commerce_cornice", "detention_cornice", "generic_cornice", "hospitality_cornice", "medical_cornice", "office_cornice", "research_cornice", "transit_cornice", "worship_cornice", "industrial_cornice", "store_cornice", "commerce_panel", "detention_panel", "generic_panel", "hospitality_panel", "medical_panel", "office_panel", "research_panel", "transit_panel", "worship_panel", "industrial_panel", "store_panel"), scenes=("interior",),
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
        binds=("industrial_wall", "store_wall", "bay_backwall", "bay_ceiling", "bay_ledge", "alien_lock_wall"), scenes=("interior",),
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
        binds=("commerce_deck", "detention_deck", "generic_deck", "hospitality_deck", "office_deck", "transit_deck", "cc_floor", "cc_pit", "customs_deck", "bar_deck", "bar_deck_joint",
               "qtr_deck_joint", "customs_deck_joint",
               # Session 3s articulation (INV-073). A bay joint is the deck's own material at its edges.
               "commerce_deck_joint", "detention_deck_joint", "generic_deck_joint", "hospitality_deck_joint", "medical_deck_joint", "office_deck_joint", "research_deck_joint", "transit_deck_joint", "worship_deck_joint", "industrial_deck_joint", "store_deck_joint"), scenes=("interior",),
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
        binds=("industrial_deck", "store_deck", "bay_deck"), scenes=("interior",),
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
        binds=("worship_deck", "cc_dais", "council_floor_1"), scenes=("interior",),
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
        binds=("commerce_rib", "detention_rib", "generic_rib", "hospitality_rib", "medical_rib", "office_rib", "research_rib", "transit_rib", "worship_rib", "council_fin", "cc_mullion", "cc_ring", "cc_hub", "customs_mullion", "bar_mullion",
               "qtr_mullion",
               # Session 3s articulation (INV-073). A mullion is a rib at bay scale -- same painted structural surface, and the entry's own measurement is a pilaster:wall ratio that applies at either size.
               "commerce_mullion", "detention_mullion", "generic_mullion", "hospitality_mullion", "medical_mullion", "office_mullion", "research_mullion", "transit_mullion", "worship_mullion", "industrial_mullion", "store_mullion"), scenes=("interior",),
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
        binds=("industrial_rib", "store_rib", "customs_bracket", "customs_hanger"), scenes=("interior",),
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
        binds=("fix_gantry_rail", "fix_racking_run", "fix_catenary_run", "crane", "prop_docking_clamp", "bay_girder", "plant_frame", "plant_frame_ring"), scenes=("interior",),
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
        binds=("fix_service_duct", "fix_service_riser", "fix_plant_column", "plant_pipe", "plant_tank"), scenes=("interior",),
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
        binds=("prop_catwalk", "cc_stair", "plant_catwalk"), scenes=("interior",),
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
        binds=("prop_viewport", "cc_glazing"), scenes=("interior",),
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
        binds=("prop_handhold", "cc_rail", "cc_console_leg", "alien_bar", "bar_footrail", "plant_rail"), scenes=("interior",),
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
        binds=("fix_platform_edge", "bay_chevron"), scenes=("interior",),
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
        binds=("prop_desk", "prop_duty_desk", "prop_counter", "prop_issue_counter", "prop_parcel_locker", "prop_lab_bench", "fix_fume_column", "council_top", "council_frame", "council_plinth", "customs_bollard", "customs_desk", "qtr_desk", "qtr_locker", "bar_servery", "bar_backbar", "bar_table"), scenes=("interior",),
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
        binds=("prop_seat", "prop_bunk", "qtr_bed", "qtr_seat", "bar_stool"), scenes=("interior",),
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
        binds=("prop_serving_counter", "prop_tray_dispenser", "prop_cold_drawer", "council_medallion"), scenes=("interior",),
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
        binds=("prop_workbench", "prop_tool_rack", "prop_grow_rack", "fix_cell_divider", "bar_table_stem", "bar_neon_clamp"), scenes=("interior",),
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
        binds=("prop_diagnostic_bed", "prop_medcabinet", "prop_cryo_pod", "fix_equipment_gantry", "qtr_shower"), scenes=("interior",),
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
        binds=("fix_stall_frame", "fix_awning_rail", "council_chair"), scenes=("interior",),
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

    # =====================================================================
    # LAYER 3 -- THE ZOCALO
    # =====================================================================
    # The station's social centre and the largest bespoke module in the
    # project: 38 emitted groups, enumerated by RUNNING zocalo.py rather than
    # by reading its strings. Proposed as structured data in
    # docs/layer3-proposals/bespoke/zocalo.json and rendered here by
    # station/apply_proposals.py.
    #
    # One correction was made before it landed, and it is the same defect
    # interior_kit had one commit earlier: `zoc_rib_cap` and `zoc_rib_lamp`
    # were both claimed and the rib ARCH they sit on was not. The proposal's
    # own coverage note asserted that every group had exactly one owner; the
    # resolver found this one had none. A claim of coverage is not coverage.
    #
    # The group was also renamed `zoc_rib` -> `zoc_rib_arch` in zocalo.py so
    # the three are siblings rather than a prefix and its extensions -- a bare
    # `zoc_rib` is a substring of both the others, a real ambiguity under
    # longest-wins even though it happens to resolve correctly today.

    # ---- zocalo (bespoke) ----------------------------------------------

        # The Zocalo's side walls are not a Zocalo surface at all —
        # zocalo_bay() calls interior_kit.wall_assembly() twice per bay and
        # mirrors one copy, so the geometry, the plate courses and the tagged
        # light spans are the corridor kit's. Giving it its own albedo would
        # let the concourse and the corridor it opens off disagree about what
        # the station is painted, which is exactly the second-source-of-truth
        # failure materials.py exists to prevent. The 4.0 m wall_plate repeat
        # is kept because it is 6 courses per repeat, i.e. the 0.667 m course
        # the corridor frame measures; a concourse wall is the same panel,
        # taller.
    a(Material(
        "zoc_wall_plate", "Zocalo Concourse Wall — the corridor kit's wall assembly at concourse height",
        albedo=(0.460, 0.460, 0.460), roughness=0.56, metallic=0.1,
        specular=0.35, texture="wall_plate", uv_scale=1.0 / 4,
        binds=("zoc_wall",), scenes=("interior",),
        source="NOT A NEW MEASUREMENT. station/zocalo.py builds both side walls by calling station/interior_kit.py's wall_assembly(l, ceil, p) directly, so zoc_wall IS kit_wall_plate's surface under a second generator; all five numbers are reproduced exactly from station/materials.py's kit_wall_plate rather than re-derived, the same discipline container_skin uses against cargo_module. Confirmed in the room's own frame: reference/04-sector-red/zocalo.webp, balanced with the gains already in materials.GREY_WORLD_GAINS (0.906/1.185/0.950, recomputed here from the frame as 0.9059/1.1854/0.9501), the Zocalo side wall at (0.855,0.110)-(0.900,0.290) reads balanced rgb 0.409/0.479/0.484 H 174 S 0.180 V 0.488, and that frame's lit structural cluster sits at V 0.458 — so the wall is 1.06x ALBEDO_ANCHOR, i.e. the same pale plated panel with square fasteners the corridor kit is calibrated on. reference/11-props-and-technology/Zocalo neon signage in background.jpg shows the same ribbed pale panelling behind the wordmark.",
        extrapolated="Nothing. Every value is kit_wall_plate's, reproduced because apply_proposals.py refuses a fragment already claimed by another material and 'zoc_wall' contains none of kit_wall_plate's fragments ('structure', 'wall_panel', 'wall_assembly', 'bulkhead'). If kit_wall_plate ever moves, this must move with it; that coupling is the cost of the reproduction and is recorded here so a later session can collapse the two if binds are ever made extensible."))

        # The deck is the surface the whole frame is exposed for and the one
        # everything else in this room is measured against, so it has to be
        # right first. It is NOT given the cyan the balanced frame shows,
        # because the same deck two metres away under the blue practical is 30
        # degrees further round the wheel with MORE saturation, not less — the
        # project's own multiplicative-tint test, and the fifth time in this
        # library that a colour in a frame has turned out to belong to the
        # light. It goes BELOW the wall it meets (0.396 against 0.460) and gets
        # its brightness back through roughness 0.32 and specular 0.58, which
        # is the ruling kit_deck and shell_deck_public already share and which
        # is also what throws the light pools the frame actually shows.
    a(Material(
        "zoc_deck_tile", "Zocalo Deck Tile — pale 0.45 m concourse tile on recessed joints",
        albedo=(0.396, 0.396, 0.396), roughness=0.32, metallic=0,
        specular=0.58, texture="deck_plate", uv_scale=1.0 / 1.8,
        binds=("zoc_deck_tile",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951, recomputed here from the frame as 0.9362/1.1368/0.9504). THE FRAME'S ESTABLISHED ANCHOR, reproduced before use: the concourse deck tile at (0.237,0.652)-(0.287,0.712) reads raw 0.596/0.573/0.690 — the exact figure station/materials.py already records against furn_pale_composite — and balanced 0.558/0.651/0.656, V 0.656; materials.py's furn_stall_frame fixes that same tile as kit_deck_plate at 0.360, so this frame's albedo scale is balanced V x 0.549. A clean tile field at (0.215,0.815)-(0.315,0.859) reads balanced V 0.694, i.e. 0.381 — within 4% of shell_deck_public's 0.396, whose source is this same frame. NEUTRALITY, by the two-light test: the same continuous deck reads H 173-183 S 0.15-0.20 on the frame's left half and H 203-209 S 0.32-0.43 on its right half under the blue deck practical, with saturation RISING as value rises (S 0.204 at V 0.344, 0.320 at V 0.547, 0.414 at V 0.704, 0.404 at V 0.876 across the k-means bands of (0.74,0.84)-(1.00,0.99)) — the additive signature. One surface, two lights, two colours, so the blue is the light. Values reproduced from station/materials.py's shell_deck_public, itself derived from this frame.",
        extrapolated="The 1.8 m texture repeat, and it is the one number here that is new. shell_deck_public carries 4.0 m and its own extrapolated note calls that 'the weakest number in this material', asking for 'one frame with a person standing on a tile joint'. station/zocalo.py has better than that: its camera solve (REF_HORIZON_PX 370.5, REF_EYE_M 1.265, REF_FOCAL_PX 2517, cross-checked on three furniture sizes it did not know) measures the deck's two joint families at 0.52 m and 0.40 m — MEASURED['deck_tile_m_range'] — and the module builds at TILE_M = 0.45. deck_plate is 4 plates across a repeat (station/materials.py, door_blast_plate: '4x3 plates per repeat, so 3.0 m gives 0.75 m plate courses'), so 1.8 m gives 0.45 m plates and the sheet's seams land on the modelled tile joints instead of 2.2x coarser than them. Overturned by: a re-solve of the camera that moves TILE_M."))

        # tiled_deck() spends 2,304 triangles a bay putting one quad under
        # every tile for exactly one reason — that tiles can differ
        # individually — and 7% of them are tagged worn. If that group takes
        # the clean tile's material the geometry is wasted. The frame cannot
        # supply the number, so the number is declared invented and the
        # measurement that bounds it is published instead of a
        # plausible-looking figure: 2.4% is what two clean tiles differ by, and
        # this has to beat it.
    a(Material(
        "zoc_deck_worn", "Zocalo Deck Tile, Traffic-Worn — polished and grimed in the walking lane",
        albedo=(0.340, 0.340, 0.340), roughness=0.26, metallic=0,
        specular=0.62, texture="deck_plate", uv_scale=1.0 / 1.8,
        binds=("zoc_deck_worn",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png, balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). A NEGATIVE MEASUREMENT, and it is the honest content of this entry: ten adjacent tile cells sampled across the clean deck field at (0.215,0.815)-(0.315,0.859) give balanced V medians 0.669 0.678 0.700 0.713 0.704 0.704 0.703 0.678 0.696 0.664 — mean 0.691, sd 0.016, i.e. 2.4% tile-to-tile. The frame does NOT resolve a worn tile population at this scale; every larger swing in the deck (sd 65% over the bottom-left field) is chairs, shoes and cast shadow, checked cell by cell. The tie to a real level is zoc_deck_tile's 0.396, itself anchored through this frame's deck tile at kit_deck_plate 0.360.",
        extrapolated="The entire delta from the clean tile — value 0.86x, roughness -0.06, specular +0.04. What constrains it: (1) the measured 2.4% tile-to-tile uniformity is the FLOOR, because a wear group that differs by less than the noise between two clean tiles is 7% of the deck's triangles doing nothing, and 14% is six times that — enough to read at 1440p, small enough not to look like spilled paint; (2) the direction is not free: foot traffic on a coated tile polishes it and loads it with grime, so it goes darker AND smoother, never lighter or rougher, which is why roughness drops to 0.26 while value drops to 0.34; (3) it must stay above the chevron band at 0.265, or wear starts reading as deliberate marking. Overturned by: any frame that shows a Zocalo traffic lane and its untrodden edge in one shot."))

        # tiled_deck() lays the band as whole tiles at both ends of every bay
        # with the stripe direction reversing about the centreline, so it reads
        # as a V pointing along the concourse — a threshold marker, not a
        # hazard. Getting it wrong in the loud direction would be worse than
        # getting it wrong in the quiet one: a hazard chevron says 'do not step
        # here' and this is the exact tile everyone steps on. The value lands
        # at 0.67x the clean tile, which is what the frame shows and what makes
        # the band read as an inlay rather than as a stain.
    a(Material(
        "zoc_deck_chevron", "Zocalo Threshold Band — ochre chevron inlay at the bay ends",
        albedo=(0.265, 0.262, 0.209), roughness=0.34, metallic=0,
        specular=0.55, texture="deck_plate", uv_scale=1.0 / 1.8,
        binds=("zoc_deck_chevron",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). The band runs diagonally across the deck at the frame's lower right and is legible at magnification as tan chevrons inlaid in a darker strip. Two chevrons measured clear of the standing figure's shadow: (0.782,0.7955)-(0.802,0.8045) balanced rgb 0.457/0.439/0.347 H 48 S 0.234 V 0.457, and (0.868,0.8345)-(0.892,0.8425) rgb 0.488/0.499/0.399 H 74 S 0.181 V 0.510. The dark ground between them, (0.806,0.7965)-(0.826,0.8055), reads 0.338/0.339/0.269 V 0.348. Through this frame's established anchor (deck tile balanced V 0.656 -> kit_deck_plate 0.360, x0.549) the chevrons are 0.251 and 0.280, mean 0.265; normalised hue (0.989, 0.980, 0.780). THE HUE IS THE PAINT, not the light: the deck tile 0.2 m away in the identical light reads H 173-183, so two adjacent surfaces under one key sit 110-130 degrees apart on the wheel.",
        extrapolated="Roughness, specular, and — declared plainly — the absence of the chevron pattern itself. hazard_chevron is the library's only diagonal-stripe sheet and it is in COLOUR_SHEETS, so it BAKES yellow and black and ignores albedo_color entirely (materials.emitted_albedo returns white for it). Applying it here would paint a shopping concourse's wayfinding threshold in docking-bay hazard yellow, when the measurement is H 48-74 at S 0.18-0.23 — a muted ochre, three times less saturated than ACCENTS['hazard_yellow']. So the band ships as a flat ochre inlay on deck_plate at the tile module, and the missing piece is named: ONE procedural ochre chevron sheet closes it, and until then this group carries the band's colour and value but not its stripe. Saturation 0.211 is over STRUCTURAL_SAT_MAX and is measured, not styled; the frame is cited above."))

        # This is the one place in the room where reuse is not a convenience
        # but a correctness requirement: kit.deck_strip and kit.downlight_pool
        # are the same functions the corridors call, so two different emission
        # colours for one function would put a warm pool in the Zocalo and a
        # cool one 20 m away through the same doorway. The albedo is nearly
        # black on purpose — these discs and strips sit 10-12 mm proud of the
        # deck and are lit surfaces in the engine, so what they are is emission
        # plus a dark substrate that catches a grazing highlight; a pale albedo
        # under an emission would double-count the light.
    a(Material(
        "zoc_deck_light", "Zocalo Deck Light — the centre strip and the 1.57 m downlight pools",
        albedo=(0.090, 0.095, 0.105), roughness=0.3, metallic=0,
        specular=0.2,
        emission=(0.860, 0.910, 1.000), emission_energy=3.5,
        binds=("zoc_deck_strip", "zoc_downlight"), scenes=("interior",),
        source="NOT A NEW MEASUREMENT. Both groups are the interior kit's own primitives called straight out of station/zocalo.py: kit.deck_strip(p['deck_strip_w_m'], l) and kit.downlight_pool(), the latter sized 1.57 m off reference/10-interiors-generic-kit/more hallway.jpg against a standing officer (station/interior_kit.py, downlight_pool docstring). Every value is reproduced exactly from station/materials.py's light_deck_channel so the concourse's deck lighting cannot disagree with the corridor's. Corroborated in more hallway.jpg, which reference/00-INDEX.md and materials.NEGATIVE_RESULTS both class as a LIGHTING reference and not an albedo reference — the right kind of frame for a source: the near pool at (0.395,0.930)-(0.500,0.985) k-means raw gives its bright core at rgb(0.635,0.718,0.966), R<G<B, i.e. cool white, matching light_deck_channel's cool emission rather than the warm register.",
        extrapolated="The merge of the two groups into one material, and the single energy. A lit strip behind a lens and a lit patch of deck under a downlight are not physically the same fitting, and if a later pass wants the pool dimmer than the channel it should split them — the fragments are already separate. They are merged now because nothing in any held frame separates them and inventing a difference would be invention. Nothing else here is new: the colour and energy are light_deck_channel's, reproduced."))

        # The elliptical rib is the signature element of every B5 interior in
        # this project, and the frame's only usable statement about it is a
        # ratio: it is four to six times its surround, which is to say it is
        # the thing that reads. 0.469 makes it the palest large surface in the
        # volume, one notch above the wall and well above the near-black
        # soffit, so the arch draws itself against the ceiling exactly as it
        # does in the reference instead of dissolving into it. The purlins get
        # the same value deliberately — zocalo_bay() adds five shallow beams
        # because 'a 233 m2 ceiling with nothing on it reads as a lid', and
        # that only works if they are pale against a dark soffit. --
        # `zoc_rib_arch` added when the resolver found it UNOWNED: the proposal
        # claimed every group had exactly one owner and this one had none. Its
        # cap and its lamp were both claimed and the arch itself was not, which
        # is the same defect interior_kit had (a tagged light strip inside an
        # untagged pilaster). The rib is structure, so it belongs here.
    a(Material(
        "zoc_structure", "Zocalo Painted Structure — the elliptical rib, gallery beam, raking struts and soffit purlins",
        albedo=(0.469, 0.469, 0.469), roughness=0.4, metallic=0,
        specular=0.46,
        binds=("zoc_gallery_beam", "zoc_gallery_strut", "zoc_purlin", "zoc_rib_arch", "zoc_rib_cap"), scenes=("interior",),
        source="Values reproduced from station/materials.py's shell_rib_painted ('painted structural pilaster, floor to soffit'), which is the same build and the same paint. Confirmed as the PALE element of the volume in reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951): scanlines across the elliptical rib give peak balanced V 0.254 at y=0.10, 0.245 at y=0.13, 0.192 at y=0.16 and 0.259 at y=0.20, against row medians of 0.067/0.055/0.045/0.040 in the same scanline — the arch is 4 to 6 times the value of everything behind it. NEUTRALITY, by the two-light test: the gallery's raking strut band at (0.52,0.125)-(0.62,0.205) clusters H 1-18 S 0.25-0.37 where the stalls' warm practicals reach it, while the identical members at the gallery slab edge (0.300,0.170)-(0.420,0.185) and the purlin run at (0.640,0.040)-(0.760,0.080) read H 331 S 0.241 and H 338 S 0.271 where they do not — one structure, two lights, 320 degrees apart, so neither hue is the paint. reference/10-interiors-generic-kit/more hallway.jpg shows the same pale ribbon ribs against a dark shell.",
        extrapolated="The absolute level, via ALBEDO_ANCHOR and shell_rib_painted — the frame gives only the 4-6x RATIO of the arch to its background, because the upper third of more zocalo.png is three to six stops under the foreground and no absolute reading survives there. Also extrapolated: that four groups share one value. What constrains that merge is that the frame shows no colour difference between them once the practicals are removed, and the project has now been wrong five times in the other direction. Overturned by: any Zocalo frame lit flat, or one showing the rib against the gallery beam under a single key."))

        # zocalo.py's own comment is the point: 'Signage and practicals ARE the
        # light in this space; there is no ambient fill anywhere in the
        # reference.' Ten of these a bay along the arch is what makes the
        # ceiling volume legible at all, and the standing blocking finding
        # against the exterior — a station that renders unlit from within reads
        # as a derelict — has the same shape indoors. The frame independently
        # landing on the existing warm register, from a lamp that register was
        # not derived from, is the reason this is a two-line entry rather than
        # a new colour.
    a(Material(
        "zoc_rib_lamp", "Rib Lamp — the warm practical set into the arch intrados",
        albedo=(0.300, 0.240, 0.190), roughness=0.35, metallic=0,
        specular=0.25,
        emission=(1.000, 0.680, 0.400), emission_energy=4,
        binds=("zoc_rib_lamp",), scenes=("interior",),
        source="Emission and albedo reproduced from station/materials.py's light_downlight ('the warm practical, low on the wall'), which is the register these lamps belong to. Independently corroborated on the fitting itself: reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951), the lamp set into the arch at (0.460,0.030)-(0.472,0.052) reads rgb 0.402/0.268/0.209 H 29 S 0.343 V 0.402; normalised to its own peak that is (1.000, 0.667, 0.520), which reproduces light_downlight's (1.0, 0.68, 0.4) in R and G to within 2%. reference/10-interiors-generic-kit/more hallway.jpg shows the same lamps repeating along the ribs at (0.230,0.100)-(0.360,0.330), which is the frame station/zocalo.py cites for placing them.",
        extrapolated="The blue channel and the energy. Measured B/R is 0.52 against light_downlight's 0.40; the excess is bloom around a source occupying about 12x22 px, so the register value is kept rather than the reading, on the argument that a clipped 200-pixel highlight cannot outvote a measurement made on a resolved surface. Energy 4.0 is light_downlight's, unchanged: these lamps are 3-6 m up on an arch rather than 1 m up on a wall, so their contribution per fitting is smaller, but zocalo_bay() places only ten a bay and they are the room's overhead practical — dropping the energy would leave the arch reading as an unlit ribbon."))

        # The gallery is the second storey of the room and its slab is the
        # single largest continuous surface in the volume after the deck
        # itself, so it cannot be a value nobody argued for. Making it the same
        # tile as the lower deck is the strongest available claim: the frame
        # shows the upper level in the same use as the lower, at the same 3.6 m
        # deck pitch INV-010 fixes everywhere else, and two decks in one shot
        # disagreeing about how big a tile is would be visible from the
        # concourse floor.
    a(Material(
        "zoc_gallery_slab", "Gallery Slab — the upper deck of the concourse and the colonnade soffit",
        albedo=(0.396, 0.396, 0.396), roughness=0.34, metallic=0,
        specular=0.52, texture="deck_plate", uv_scale=1.0 / 1.8,
        binds=("zoc_gallery_slab",), scenes=("interior",),
        source="Value, sheet and repeat reproduced from zoc_deck_tile, which is anchored on reference/04-sector-red/more zocalo.png through that frame's deck tile at (0.237,0.652)-(0.287,0.712) (raw 0.596/0.573/0.690, balanced V 0.656, kit_deck_plate 0.360, x0.549) and on station/materials.py's shell_deck_public, derived from the same frame. The slab's own faces cannot be read for level in that frame — its edge at (0.300,0.170)-(0.420,0.185) sits at balanced V 0.033, four stops under the foreground — but the frame does establish what it is: people are standing on it at (0.26,0.00)-(0.60,0.10), so it is a walking deck, and reference/04-sector-red/zocalo.webp shows the upper level trading exactly as the lower one does.",
        extrapolated="Roughness 0.34 and specular 0.52, and the decision to give the slab's underside the same material as its top. A 0.35 m slab shows three faces to the concourse — a walked-on top, a 0.35 m edge, and 4.5 m of colonnade ceiling — and one group has to serve all three. It takes the DECK's position on the ladder rather than the wall's because the top is the surface a player stands on and the group's dominant use is a floor; the underside being a shade too bright for a soffit is a lighting problem, and layer 4 owns it. Roughness is nudged from the tile's 0.32 to 0.34 because a slab edge and soffit are cast, not tiled. Overturned by: a frame of the Zocalo colonnade ceiling."))

        # This is the material that changes the room. station/zocalo.py's
        # gallery() calls it 'the kit's red-orange handrail, the dominant warm
        # accent in every Zocalo frame' — and the kit's handrail material,
        # kit_rail_band, is NEUTRAL 0.5302. Every metre of rail on the gallery
        # edge and both stair stringers would have rendered mid-grey. A
        # saturated albedo needs to survive the project's own test before it is
        # believed, and this one does so decisively: the saturation holds at
        # 0.63-0.71 from deep shadow to highlight, which additive light cannot
        # do. The value sits well below ALBEDO_ANCHOR because a saturated red
        # pigment cannot be bright — its red channel is 0.63x the wall's and
        # its blue channel 0.18x, which is what makes it read as oxide red
        # rather than as pink.
    a(Material(
        "zoc_rail", "Zocalo Handrail — oxide red, the room's warm accent",
        albedo=(0.290, 0.145, 0.084), roughness=0.42, metallic=0.15,
        specular=0.5,
        binds=("zoc_rail",), scenes=("interior",),
        source="reference/04-sector-red/zocalo.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.906/1.185/0.950, recomputed here from the frame as 0.9059/1.1854/0.9501). The three-rail run across the frame's lower right was isolated by masking R > 1.6G over (0.70,0.55)-(1.00,1.00), 5,301 pixels. THE TINT TEST, run and PASSED for once in the positive direction: banded by value, the rail reads rgb 0.082/0.028/0.030 H 358 S 0.659 at V 0.05-0.10; 0.121/0.051/0.045 H 5 S 0.630 at V 0.10-0.16; 0.181/0.098/0.067 H 16 S 0.630 at V 0.16-0.24; 0.298/0.149/0.086 H 18 S 0.713 at V 0.24-0.40. Saturation is FLAT across a 3.6x range of value — the multiplicative signature of a real tint, where materials.NEGATIVE_RESULTS' five previous cases all showed saturation collapsing as value rose. LEVEL: that frame's lit structural surfaces sit at balanced V 0.458 (whole-frame k-means, 5.3% cluster) and V 0.488 (wall panel at (0.855,0.110)-(0.900,0.290)), mean 0.473 -> ALBEDO_ANCHOR, a factor of 0.972, so the lit rail band scales to (0.290, 0.145, 0.084). This is the register materials.ACCENTS already names: 'maroon red H 351-5 S 0.22-0.59 tram soft goods, Zocalo handrail'.",
        extrapolated="Roughness 0.42, metallic 0.15, specular 0.50 — no frame separates gloss from the specular streak running along each rail's crown, and 0.42 with a 0.15 metallic blend is the library's existing treatment for painted steel (kit_wall_plate 0.10, accent_warning 0.42). Also extrapolated: which end of the measured value range is the albedo. The rail's shadowed body scales to (0.138,0.068,0.054) and its lit band to (0.290,0.145,0.084); the lit band is taken because the anchor is defined on lit surfaces, and the shadowed figure is recorded as the floor. Overturned by: a Zocalo frame with the rail under a neutral key, or any frame showing the rail and a pale wall in the same light at the same depth."))

        # ONE material for both zoc_stair and zoc_stair_tread, and the frame is
        # the reason: the tread face and the riser face measure within 2% of
        # each other, so a separate tread albedo would be inventing a
        # difference the reference does not contain — the exact mistake
        # NEGATIVE_RESULTS records five times. It is also the only reading
        # substring binding can express: 'zoc_stair' is a substring of
        # 'zoc_stair_tread', so any fragment that catches the carriage catches
        # the tread too, and two materials both claiming the tread is the
        # ambiguity defect test_materials_layer3.ambiguous() exists to catch.
        # The group stays in the geometry, so a later frame showing a chevron
        # nosing or a grating tread can split it — with a GROUP_ALIASES entry,
        # exactly as zoc_rib needs one.
    a(Material(
        "zoc_stair", "Zocalo Stair — the flight to the gallery, plate carriage and treads",
        albedo=(0.375, 0.375, 0.375), roughness=0.45, metallic=0.05,
        specular=0.48, texture="deck_plate", uv_scale=1.0 / 1.8,
        binds=("zoc_stair",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). The stepped run behind the threshold band reads balanced rgb 0.217/0.241/0.235 H 180 S 0.160 V 0.250 at (0.860,0.735)-(0.960,0.775) and 0.228/0.236/0.220 H 167 S 0.143 V 0.246 at (0.880,0.760)-(0.960,0.780) — tread and riser faces within 2% of each other, i.e. one material with the light falling differently on it, not two. Level is set from the deck it rises off: this frame's anchor is the deck tile at (0.237,0.652)-(0.287,0.712), balanced V 0.656 -> kit_deck_plate 0.360 (x0.549), and the clean deck field at (0.215,0.815)-(0.315,0.859) reads 0.694 -> 0.381.",
        extrapolated="The albedo's 0.95x offset below the deck, and roughness/specular/metallic. What constrains them: a stair is walked on, so it takes the deck's rung on the measured ladder, not the wall's; it is plate with an anti-slip finish rather than a laid tile, so it is ROUGHER than the concourse floor (0.45 against 0.32) and slightly darker; and it must stay above the worn-tile group (0.340) so a stair never reads as a stain on the floor. Overturned by: any frame of the Zocalo stair from the concourse floor."))

        # zocalo_bay() calls these 'backlit shopfront panels in the colonnade'
        # and adds, correctly, that 'every light in this space has an object
        # behind it; there is no ambient fill in any reference frame'. They are
        # the only light source at eye height in the 4.5 m colonnade a player
        # walks through, so if they render as dark boxes the whole underside of
        # the gallery goes black and the crowd walks through a tunnel. The hue
        # landing between two registers already measured off this room is
        # corroboration, not coincidence.
    a(Material(
        "zoc_screen", "Colonnade Shopfront — backlit panel behind the stalls",
        albedo=(0.055, 0.060, 0.075), roughness=0.22, metallic=0,
        specular=0.45,
        emission=(0.388, 0.723, 1.000), emission_energy=2.6,
        binds=("zoc_screen",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1). A source, so measured raw as well as balanced, per the treatment station/materials.py gives the rotunda altar. The lit shopfront at (0.462,0.278)-(0.512,0.372) k-means (balanced, gains already in materials.GREY_WORLD_GAINS 0.936/1.137/0.951) gives its bright field at rgb(0.350,0.653,0.903) H 207 S 0.613 (38.2%), a second lit band at (0.269,0.484,0.759) H 214 (18.2%), a third at (0.207,0.332,0.496) H 214 (14.5%) and its mullion grid at (0.149,0.155,0.180) (29.1%) — three lit bands at a constant H 207-214 across a 1.8x range of value, which is a source and not a lit surface. Normalised to its peak channel that is (0.388, 0.723, 1.000). The hue sits between materials.ACCENTS['cyan_neon'] and ACCENTS['cool_blue'], both Zocalo-adjacent registers. A SECOND colour is attested in the same colonnade in the same frame: the shopfront at (0.281,0.312)-(0.303,0.352) reads balanced 0.514/0.314/0.254 H 13 S 0.492 — a warm-red backlit panel. reference/10-interiors-generic-kit/more hallway.jpg shows the identical blue-lit mullioned panel at (0.680,0.530)-(0.840,0.680).",
        extrapolated="The albedo, the roughness/specular, the energy, and the choice of ONE colour for a group the frame shows in two. Albedo is set near black because what is modelled is a 0.06 m proud panel that is a light, and a pale substrate under an emission double-counts it; roughness 0.22 is a diffuser behind glazing, kept above 0.15 because it is not glass. Energy 2.6 is between signage_panel's 3.0 and sign_neon_venue's 1.3: this is a lit shop window 1.5 m from a walking crowd, brighter than a wall plaque and dimmer than a wordmark. The blue is chosen over the red because it is the larger and brighter population in the frame and because zocalo_bay() emits four of these a bay in a fixed pattern; splitting the group by variant, as vendor_stall already does, would let both colours ship and is the obvious next edit."))

        # This is the object the room is named after and the first thing a
        # viewer will check us on, so the honest move is to publish both
        # readings and say which was taken and why, rather than pick one and
        # let it look sourced. The six glyphs are a decal on this group, not
        # geometry — the module is explicit — so what this material owes is the
        # tube's colour, its clipping behaviour, and a board dark enough that
        # the glyphs read as light rather than as paint.
    a(Material(
        "zoc_neon_face", "Zocalo Wordmark — neon tube, orange-red",
        albedo=(0.090, 0.050, 0.040), roughness=0.25, metallic=0,
        specular=0.2,
        emission=(1.000, 0.520, 0.300), emission_energy=5,
        binds=("zoc_neon_face",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), measured RAW because a source is radiance and balancing it would be meaningless. Over the sign board at (0.054,0.109)-(0.203,0.190) the raw 95th percentile per channel is (0.980, 0.510, 0.294), the 99th is (1.000, 0.533, 0.322) and the maximum is (1.000, 0.655, 0.561) — the red channel CLIPS, so this is a source and not a lit surface, the same test station/materials.py applies to the rotunda altar. k-means over the board gives the tube core at rgb(0.858,0.267,0.158) H 9 S 0.816 (38.3%), its bloom at (0.952,0.465,0.263) H 18 (25.1%), and the spill on the plate at (0.673,0.161,0.148), (0.450,0.107,0.121) and (0.269,0.078,0.097), H 354-2. Emission is the p95 normalised to its peak: (1.000, 0.520, 0.300), H 18. THE CYAN VARIANT IS EQUALLY ATTESTED and is recorded rather than used: reference/04-sector-red/zocalo.webp shows the same wordmark cyan, raw clusters at H 180-181 clipping in G and B, normalised (0.411, 0.986, 1.000) — which reproduces materials.ACCENTS['cyan_neon'] (0.444,1.000,0.939), a register derived from this very glyph; and reference/11-props-and-technology/Zocalo neon signage in background.jpg shows it cyan again on a dark board.",
        extrapolated="The choice of colour, the albedo and the energy. station/zocalo.py's neon_sign() docstring says outright that both colours are attested and 'the choice is a material' — this is that choice, and the reasons are: (1) more zocalo.png is the frame this entire module is solved from, so sign and geometry then come from one camera; (2) emissive_signage and sign_neon_venue are BOTH already cyan, so a cyan wordmark would be the third identical cyan in one room and the concourse's widest shot would lose its only warm anchor; (3) materials.SECTOR_ACCENT maps Red sector to warm_practical. Two edits reverse it: emission -> ACCENTS['cyan_neon'], energy unchanged. Albedo near black is the unlit tube and its board. Energy 5.0 sits between emissive_signage's 4.5 and light_pilaster_strip's 6.0, for a 1.9 x 0.84 m sign 4.75 m up."))

        # The board is 12 triangles and it matters out of all proportion,
        # because it is what the glyphs are read against. If it took the wall's
        # 0.46 the wordmark's contrast would collapse and the sign would look
        # like a poster. Recording that the frame cannot supply the number —
        # every pixel of the plate is red because the tube is on — is more
        # useful to the next session than a plausible dark grey with a citation
        # stapled to it.
    a(Material(
        "zoc_neon_back", "Neon Board — the dark backing plate behind the wordmark",
        albedo=(0.094, 0.100, 0.112), roughness=0.34, metallic=0.1,
        specular=0.25,
        binds=("zoc_neon_back",), scenes=("interior",),
        source="Albedo reproduced exactly from station/materials.py's sign_neon_venue ('concourse sign board, cyan tube on a dark ground'), the same object class in the same sector. reference/11-props-and-technology/Zocalo neon signage in background.jpg (authority 1) shows the board plainly: a rectangular dark panel carrying the wordmark, distinctly darker than the pale ribbed wall behind it. In reference/04-sector-red/more zocalo.png the board CANNOT be measured for its own colour and this entry says so: every k-means cluster inside the board rectangle (0.056,0.106)-(0.206,0.196) comes back red — (0.229,0.084,0.088) H 358 and (0.405,0.120,0.115) H 1 are the darkest two — because the whole plate is carrying the tube's spill, so a reading there would be the neon's colour, not the board's.",
        extrapolated="Roughness 0.34 and metallic 0.10 — a painted sheet-steel board, treated like the library's other painted panel work. The albedo is not extrapolated but it is also not independently measured here: it is sign_neon_venue's, taken on the argument that the reference set contains no frame in which a Zocalo sign board is separable from its own tube. Overturned by: a frame of the sign switched off, or lit only by room light."))

        # The table is the object the camera solve was built on — its 0.475 m
        # top and the 0.093 m shaker standing on it are what confirmed the
        # solve was not a fit to noise — so it would be perverse to give it a
        # colour other than the one the library already measured from it. The
        # value is 1.04x the deck beside it, which is what the frame says and
        # what makes a café table read as furniture standing on a floor rather
        # than as a hole in it.
    a(Material(
        "zoc_cafe_table", "Zocalo Café Table — moulded pale composite: top, pedestal and foot",
        albedo=(0.402, 0.412, 0.432), roughness=0.4, metallic=0,
        specular=0.5,
        binds=("zoc_table_top", "zoc_table_col", "zoc_table_foot"), scenes=("interior",),
        source="NOT A NEW MEASUREMENT: reproduced exactly from station/materials.py's furn_pale_composite, whose first of three anchors IS this table — 'reference/04-sector-red/more zocalo.png, raw: the pedestal café table's top (0.515,0.706)-(0.580,0.731) reads 0.592/0.600/0.718'. That figure was recomputed here from the frame before reuse and reproduces to three decimals. Independently re-derived through this frame's deck anchor as a check: balanced (gains already in materials.GREY_WORLD_GAINS, 0.936/1.137/0.951) the top reads V 0.754 at (0.505,0.690)-(0.560,0.712) and V 0.803 at (0.630,0.695)-(0.680,0.715), which through the frame's scale (deck tile balanced V 0.656 -> kit_deck_plate 0.360, x0.549) is 0.414 and 0.441 — bracketing furn_pale_composite's 0.411 luminance from a direction that material did not use.",
        extrapolated="That the pedestal and foot are the same composite as the top. The frame reads them much darker — the lower pedestal at (0.450,0.880)-(0.560,0.960) is balanced V 0.473 against the top's 0.754, a ratio of 0.63 — but that is orientation, not paint: this frame's key is strongly downward (its own downlight pools are what the deck shows), and the same 0.63-0.72 vertical-to-horizontal ratio appears on the chair panel and the stall counter in the same shot. One moulded pedestal table in one colour is the reading; a pedestal genuinely 0.63x its own top would be a two-tone table, which no frame shows. Overturned by: a Zocalo frame with side light."))

        # Saturation 0.237 is over the structural ceiling and it is measured,
        # with the control in the same frame: the table top the band is bolted
        # to sits 150 degrees away in hue under one light, which is the cheap
        # test NEGATIVE_RESULTS prescribes and the only kind of evidence that
        # should ever buy a coloured interior surface. The band is the one warm
        # note on the room's most-looked-at prop, and if it were painted the
        # top's grey the tables would flatten into the floor.
    a(Material(
        "zoc_table_edge", "Table Edge Band — the warm metal rim around the top",
        albedo=(0.600, 0.510, 0.458), roughness=0.3, metallic=0.85,
        specular=0.55,
        binds=("zoc_table_edge",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). The 23 mm rim is legible at magnification as a warm brown metal ring around a cool pale disc. Measured on the front arc clear of the shaker, (0.548,0.7405)-(0.606,0.7505): rgb 0.220/0.187/0.168 H 28 S 0.210 V 0.220, normalised hue (1.000, 0.850, 0.764). The hue is the metal, not the light: the composite top 15 px above it in the same frame, under the identical key, reads H 179-184 S 0.20-0.23 — one object, one light, two surfaces 150 degrees apart on the wheel. station/zocalo.py's MEASURED table gives the band's size, 0.023 m, from the same camera solve.",
        extrapolated="The level and the metallic. A metal's albedo channel is F0, not a diffuse value, so it sits ABOVE ALBEDO_ANCHOR rather than below it — the argument station/materials.py already makes for clad_services — and the frame's 0.220 is a diffuse-style reading of a surface whose brightness is almost entirely specular, so it cannot set F0. 0.600 is chosen between the library's bare steel (grab_rail_bare and tram_saloon_post at 0.560-0.580) and copper's F0 near 0.95: a dulled brass or bronze trim, warm by the measured ratio and no brighter than a steel one. Metallic 0.85 rather than 1.0 because the rim in the frame carries a broad soft highlight rather than a mirror, so it is a lacquered or handled trim. Overturned by: a frame with a specular highlight of known colour on the rim."))

        # The '5' is a decal on this group and not geometry — the module is
        # explicit that it is 'the same glyph as the station shield patch and
        # the floor inlay in 05-sector-green/conference aerea.webp', built
        # once. Binding zoc_table_five here as well is what makes the module's
        # own note true: 'the index entry reads the 5 onto table pedestals as
        # well as chair backs... Both readings are one edit apart.' With this
        # material in place that edit stays one edit, because the
        # pedestal-with-roundel already has a home. The group is latent in the
        # default build (params()['table_pedestal_five'] is False), so the
        # fragment is insurance, not decoration.
    a(Material(
        "zoc_five_panel", "The '5' Panel — pale composite carrying the station roundel",
        albedo=(0.374, 0.383, 0.402), roughness=0.55, metallic=0,
        specular=0.45,
        binds=("zoc_chair_five", "zoc_table_five"), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). The near chair's back panel fills (0.055,0.622)-(0.200,0.762) and carries a dark outlined '5'; at magnification the panel is visibly soiled and streaked where the table top is not. Its LIT right-hand portion, (0.168,0.634)-(0.196,0.750), reads balanced rgb 0.308/0.339/0.321 V 0.339; its shadowed left, (0.062,0.645)-(0.105,0.748), reads V 0.147. The same white composite on the table pedestal below, (0.450,0.880)-(0.560,0.960), reads V 0.473. Base colour reproduced from station/materials.py's furn_pale_composite (0.402,0.412,0.432), whose three-frame derivation includes this frame's café table.",
        extrapolated="The 0.93x drop from furn_pale_composite and the roughness. The frame shows the panel at 0.72x the pedestal (0.339 against 0.473), but both are vertical composite in the same room and most of that gap is distance from the key — so only a quarter of it is taken as grime, giving 0.93x and 0.374. Roughness is raised to 0.55 from the table's 0.40 because the streaking is visible in the frame and a chair back is the one surface in the room every customer puts a hand on. Overturned by: a frame with a clean and a dirty chair in one shot."))

        # Three groups, 10,164 triangles across three bays, all of them thin
        # members read in silhouette. What they need is to be dark enough to
        # draw the market's structure against the pale deck and the lit
        # canopies, and the one number the library already has for exactly this
        # object is 0.075. The spar measurement is the useful new thing: it
        # corroborates a value derived from a chair with a reading taken off an
        # awning, which is the kind of independent agreement that makes a
        # number safe to reuse rather than merely convenient.
    a(Material(
        "zoc_armature", "Market Armature — the black tube of chair frames, awning spars and sign masts",
        albedo=(0.075, 0.074, 0.074), roughness=0.32, metallic=0,
        specular=0.5,
        binds=("zoc_chair_frame", "zoc_stall_spar", "zoc_stall_mast"), scenes=("interior",),
        source="NOT A NEW MEASUREMENT: reproduced exactly from station/materials.py's furn_stall_frame, whose source IS this object in this frame — 'reference/04-sector-red/more zocalo.png, raw: the black tubular hoop round a café pedestal (0.455,0.824)-(0.530,0.840) reads 0.094/0.063/0.090, and against that frame's deck anchor (deck tile raw V 0.690 -> kit_deck_plate 0.360, x0.522) that is 0.049', with a second-frame, second-sector cross-check at 0.109 on 05-sector-green/council chambers.webp. That raw reading was recomputed here from the frame before reuse and reproduces to three decimals. INDEPENDENT CORROBORATION on a different member: the awning spars at (0.640,0.120)-(0.700,0.130) read balanced (gains 0.936/1.137/0.951) V 0.173, which through this frame's balanced anchor (deck V 0.656 -> 0.360, x0.549) is 0.095 — landing inside furn_stall_frame's own 0.049-to-0.109 bracket, from a member it did not measure.",
        extrapolated="That the chair frame, the awning spars and the sign mast are one armature. The frame supports it — 0.049 for the chair hoop and 0.095 for the spars, both black tube of the same 25-45 mm class — and reference/00-INDEX.md reads the Zocalo canopies as 'fabric on radiating spars, parasol-fashion', which is the same slender armature the chairs are made of. What is NOT extrapolated is the value: it is furn_stall_frame's, cross-checked in two frames and two sectors. Roughness 0.32 is furn_stall_frame's and matches the hard specular streak the frame shows along the chair's top rail."))

        # Declared invention with the gap named, rather than a silent copy of
        # the frame material. The honest content of this entry is the sentence
        # that no held frame contains an unoccupied Zocalo chair seen from the
        # front, which is worth more to the next session than a fourth
        # plausible black.
    a(Material(
        "zoc_chair_seat", "Café Chair Seat — moulded dark pad",
        albedo=(0.105, 0.103, 0.102), roughness=0.62, metallic=0,
        specular=0.4,
        binds=("zoc_chair_seat",), scenes=("interior",),
        source="NO FRAME SHOWS IT. In reference/04-sector-red/more zocalo.png every chair in the shot is either occupied or seen from behind its back panel, and the seat pad — a 35 mm disc at 0.45 m, station/zocalo.py CHAIR_SEAT_H_M — is occluded in all of them; reference/04-sector-red/zocalo.webp shows the concourse at standing-crowd height with no seat visible at all. Nothing here is measured on the seat. The two sourced quantities it is tied to are the chair's own frame, station/materials.py's furn_stall_frame at 0.075 (measured on this chair's hoop in this frame), and the council chambers cross-check at 0.109 that furn_stall_frame records.",
        extrapolated="All four numbers. What constrains them: (1) the chairs read black overall in both authority-1 frames, so the seat cannot be pale or the silhouette the frames show would break; (2) it must not be the same value as the tube it is bolted to, or the group is wasted geometry — 0.105 sits at the top of the 0.049-0.109 bracket furn_stall_frame measured, so the pad is the lightest thing in a black chair and still black; (3) it is a seat, so it is matte where the tube is glossy, which is the whole of the roughness argument (0.62 against 0.32) and is the difference a player will actually see when they look down at one; (4) it stays a dielectric because a moulded pad is. Overturned by one frame of an empty Zocalo chair from the front — the cheapest reference gap in this room."))

        # Twelve of these stand on tables across three bays, 2,288 triangles,
        # and they are the only true mirror in the room. That matters more than
        # their size: a specular object is how a player reads how bright the
        # space around them is, so it is the one surface that makes the
        # Zocalo's practicals visible from a seat. Reproducing the library's
        # stainless F0 rather than inventing a chrome keeps the shaker, the
        # servery counter and the grab rails on one metal.
    a(Material(
        "zoc_service_chrome", "Drinks Service — polished steel shaker and tumblers",
        albedo=(0.560, 0.565, 0.575), roughness=0.18, metallic=1,
        specular=0.55,
        binds=("zoc_service_chrome",), scenes=("interior",),
        source="F0 reproduced exactly from station/materials.py's furn_service_steel ('Service Stainless — servery, tray stack'), the same alloy in the same use. reference/04-sector-red/more zocalo.png (authority 1) establishes what the object is and that it is a mirror: the shaker at (0.578,0.630)-(0.598,0.690) reads balanced (gains already in materials.GREY_WORLD_GAINS, 0.936/1.137/0.951) V 0.139 and the tumbler cluster at (0.560,0.690)-(0.575,0.720) V 0.158 — DARKER than the pale table they stand on at V 0.754, which is the signature of a specular surface reflecting a dark room rather than of a dark material. Its size is a load-bearing measurement in station/zocalo.py: 0.093 m across, one of the three independent cross-checks that confirmed the camera solve, because a cocktail shaker is 90 mm and nothing in the derivation knew that.",
        extrapolated="Roughness 0.18, down from furn_service_steel's 0.31. The frame shows hard, near-mirror highlights running the length of the shaker and each tumbler, which a 0.31 servery finish would not give; 0.18 is bar chrome. It is deliberately NOT taken below 0.15: that threshold is reserved for glass, still water and polished metal, and while a shaker is arguably the third, this one is a working bar's — handled and fingerprinted, not a showroom's. Nothing else is extrapolated; the F0 triple is furn_service_steel's, which is also where grab_rail_bare and tram_saloon_post sit."))

        # The canopies are the market's silhouette — closed hipped solids, not
        # shells, precisely so they have thickness against the arch behind them
        # — and they are lit from underneath by the stalls' own string lights
        # in one frame and from above by a cyan neon in the other. That is the
        # ideal case for the project's cheap test, and running it here is what
        # stops the awning shipping as tan canvas, which is what a single look
        # at more zocalo.png would have produced. Goods share the material
        # because they are the same cloth-and-crate mass at the same distance
        # and no frame separates them.
    a(Material(
        "zoc_stall_canvas", "Stall Canvas — awning fabric and the goods stacked on the counter",
        albedo=(0.380, 0.345, 0.312), roughness=0.92, metallic=0,
        specular=0.3,
        binds=("zoc_stall_awning", "zoc_stall_goods"), scenes=("interior",),
        source="Values reproduced exactly from station/materials.py's furn_stall_canvas, whose title is already 'awning fabric and stacked goods'. THE TWO-LIGHT PROOF, run here on the canopy itself and it is the strongest instance of the test in this room: in reference/04-sector-red/more zocalo.png the fabric at (0.615,0.135)-(0.720,0.165), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951), reads rgb 0.268/0.187/0.172 H 28 S 0.326; in reference/04-sector-red/zocalo.webp the same canopy at (0.205,0.180)-(0.290,0.235), balanced (0.906/1.185/0.950), reads rgb 0.526/0.985/0.920 H 173 S 0.444. One fabric, two frames, two lights, 145 degrees apart — so neither hue belongs to the cloth. The stall goods in more zocalo.png at (0.700,0.190)-(0.730,0.215) read H 24 S 0.407 under the same warm string lights that make the canopy read H 28.",
        extrapolated="Nothing new; furn_stall_canvas's mild warm bias is inherited rather than re-derived. What this entry ADDS is a ceiling on it: the 145-degree swing between the two frames caps how much of any warmth can be the cloth, so furn_stall_canvas's S 0.179 is at the top of what the evidence will carry and must not grow. Roughness 0.92 is furn_stall_canvas's — the roughest surface in the library, which is right for a slack fabric canopy and for cloth-wrapped goods."))

        # The posts are what make a stall read as temporary against permanent
        # architecture, which is the single thing both authority-1 frames agree
        # the Zocalo market IS. They fail the level test the way most objects
        # in this room do — the only frame that shows them clearly has a neon
        # tube half a metre away — so the bracket is published and the choice
        # inside it is argued from what the object is for. The neutrality, at
        # least, is not a judgement call: 275 degrees of hue swing between two
        # frames settles it.
    a(Material(
        "zoc_stall_post", "Stall Post — pale salvaged section, the market's uprights",
        albedo=(0.420, 0.418, 0.412), roughness=0.75, metallic=0,
        specular=0.35,
        binds=("zoc_stall_post",), scenes=("interior",),
        source="Two frames, and they bracket rather than fix the level. reference/04-sector-red/zocalo.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.906/1.185/0.950): the stall's square uprights are pale and legible at magnification; the post at (0.157,0.300)-(0.180,0.480), directly under the cyan neon, reads balanced rgb 0.444/0.441/0.637 H 232 S 0.328 V 0.637, and the post at (0.226,0.300)-(0.252,0.500), further from it, reads 0.188/0.223/0.291 H 210 S 0.271 V 0.294. Against that frame's lit structural anchor (whole-frame k-means 0.458, wall panel 0.488, mean 0.473 -> ALBEDO_ANCHOR, x0.972) that is 0.619 and 0.286. NEUTRALITY, by the two-light test and by the two-frame test: saturation RISES with value between those two posts (0.271 at V 0.294, 0.328 at V 0.637), which is the additive signature, and in reference/04-sector-red/more zocalo.png the same posts at (0.734,0.170)-(0.746,0.250) read H 317 balanced — 275 degrees away from H 232. The blue is the neon.",
        extrapolated="The level inside the measured 0.286-0.619 bracket, and roughness/specular. 0.420 is set just below ALBEDO_ANCHOR on three constraints: the post must be paler than the black armature it carries (0.075) and paler than the canvas it holds up (0.380), or the stall has no structure to read; it must be BELOW the finished wall behind it, because a market stall is built out of salvaged section and a station that keeps its concourse walls painted does not paint a trader's uprights; and the bracket's own geometric mean is 0.421, which is where it lands. Roughness 0.75 is sawn, unfinished stock — the roughest non-fabric surface in this family and deliberately rougher than any structural panel. Overturned by: a Zocalo frame with a stall post out of the neon's throw."))

        # One counter per stall, four stalls a bay on two levels, so this is
        # 288 triangles a run in the most-looked-at 1.0 m band of the colonnade
        # — the height a player's eye sits at while walking past a trader.
        # Reusing the station's counter material keeps a Zocalo stall and a
        # customs issue counter made of the same painted steel, which is what a
        # station that fabricates its own fittings would actually produce, and
        # avoids a third counter grey in a library that already has two.
    a(Material(
        "zoc_stall_counter", "Stall Counter — painted steel serving top",
        albedo=(0.400, 0.396, 0.388), roughness=0.45, metallic=0,
        specular=0.5,
        binds=("zoc_stall_counter",), scenes=("interior",),
        source="Values reproduced exactly from station/materials.py's furn_casework ('painted steel desk, counter and locker bodies'), which already covers prop_counter and prop_issue_counter elsewhere in the station. reference/04-sector-red/zocalo.webp (authority 1) shows the counter as a pale horizontal slab across the stall front at (0.140,0.428)-(0.270,0.448), with bottles standing on it. THAT REGION CANNOT SET A LEVEL and this entry says so: balanced with the gains already in materials.GREY_WORLD_GAINS (0.906/1.185/0.950) it reads V 0.790 against that frame's lit structural anchor of 0.473, i.e. 1.67x a lit wall — a clipped highlight on a slab lying 0.6 m under a neon tube, not an albedo.",
        extrapolated="Nothing about the numbers, which are furn_casework's. What IS a judgement is the decision to use furn_casework rather than measure: the only frame showing a Zocalo counter shows it blown out, so the choice is between a number from a clipped highlight and a number the library already measured for the same class of object. Overturned by: a Zocalo stall counter out of a practical's throw."))

        # 2,016 triangles across three bays and every one of them is a light.
        # vendor_stall() puts 6-9 bulbs on each awning and its comment is the
        # argument: 'Signage and practicals ARE the light in this space; there
        # is no ambient fill anywhere in the reference.' Unlit, the market's
        # eave line goes dark and the colonnade loses the thing that makes it
        # read as a market rather than as an arcade — and it is exactly the
        # interior form of the standing blocking finding that a station with no
        # emissive windows reads as a derelict.
    a(Material(
        "zoc_stall_light", "Stall String Lights — the warm bulbs along the awning eaves",
        albedo=(0.300, 0.240, 0.190), roughness=0.35, metallic=0,
        specular=0.25,
        emission=(1.000, 0.680, 0.400), emission_energy=2.2,
        # `light_stall_festoon` is rooms.py's commerce fitting -- the market
        # bays, the black market and N'Grath's. It is the same object: the
        # measurement this material's own extrapolated field argues with
        # (docs/layer4-lighting/public_social.json's zoc_stall_light) is the
        # one rooms.py places, and the two rooms are the same room in two
        # sectors. One fitting, one material.
        binds=("zoc_stall_light", "light_stall_festoon"), scenes=("interior",),
        source="Emission and albedo reproduced from station/materials.py's light_downlight, the library's warm practical register. reference/04-sector-red/zocalo.webp (authority 1) shows them unmistakably: a dense run of individual point sources strung along the awning eave at (0.010,0.165)-(0.200,0.250), dozens of discrete bulbs. reference/04-sector-red/more zocalo.png shows the same strings on the stall at (0.756,0.158)-(0.774,0.198), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951) reading rgb 0.162/0.125/0.116 H 21 S 0.286 — warm, and the same warm signature (H 21-30) appears on every surface those strings reach in that frame: the canopy at H 28, the goods at H 24, the spars at H 17.",
        extrapolated="The energy, 2.2, and the decision to take the warm register rather than the reading. In zocalo.webp the bulbs measure raw (0.787,0.773,0.884) — bluer than white — because the cyan Zocalo neon is 1.5 m above them and their cores are 2-3 px across; a source that small cannot outvote a resolved measurement, and more zocalo.png's H 21 on the same fitting is the resolved one. Energy is set below the rib lamp's 4.0 and below light_downlight's 4.0 because these are small decorative bulbs strung six to nine per stall, not architectural fittings: they should read as a glittering line at 20 m and not as a floodlight at 2 m. Overturned by: a Zocalo frame with the strings lit and the neon off."))

        # One disc per even-numbered stall variant, so half the market carries
        # one, and it is the only element in vendor_stall() whose whole job is
        # to be read from across the concourse. It is set above the wall rather
        # than below it because that is the one thing the frame establishes
        # clearly — it is 2.1x the structure behind it — and a sign darker than
        # its background does not work as a sign. The saturation cut is the
        # standing lesson of this library applied again: five times now a
        # colour in a frame has belonged to the light, and a board sitting
        # under a string of amber bulbs is the textbook setup for the sixth.
    a(Material(
        "zoc_stall_sign", "Stall Disc Sign — the trader's board on its braced pole",
        albedo=(0.470, 0.462, 0.436), roughness=0.6, metallic=0,
        specular=0.35,
        binds=("zoc_stall_sign",), scenes=("interior",),
        source="reference/04-sector-red/more zocalo.png (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.936/1.137/0.951). The disc sign stands clear of the stall at the frame's right edge, a pale circular board on a pole carrying dark lettering; measured at (0.958,0.075)-(0.998,0.160) it reads rgb 0.308/0.290/0.239 H 50 S 0.218 V 0.308. The load-bearing figure is a RATIO in one light, not the level: the gallery structure immediately behind it at (0.535,0.140)-(0.585,0.175) reads V 0.147, so the sign is 2.1x the painted structure it hangs in front of, and it is the palest object in the colonnade's upper band. reference/04-sector-red/zocalo.webp shows the same class of trader board at (0.138,0.285)-(0.188,0.380) as a dark banner with pale script — the opposite polarity, so the group carries both readings.",
        extrapolated="The level and the saturation. The frame's absolute readings in that band are three to four stops under the foreground and cannot be anchored; what it gives is the 2.1x ratio, and 0.470 is chosen as one notch ABOVE ALBEDO_ANCHOR because a shop sign has to read against the structure it hangs on, which is what the ratio says it does. Saturation is cut from the measured 0.218 to 0.072: the sign sits in the throw of the stall's warm string lights, and every other surface those lights reach in this frame reads H 17-30, so most of the measured warmth is the practicals and only a cream cast survives as paint. Overturned by: any Zocalo frame showing a trader's board under a neutral key."))

    # The board's POST AND FRAME, which are not the board. `welcome to babylon
    # 5.webp` shows two backlit blue panels held in a dark surround that reads
    # near-black against them; giving the whole assembly the panel's material
    # would make the mount glow, and giving it the wall's would make the panel
    # sit on a pale slab. It is the contrast that makes a lit sign read as lit.
    a(Material(
        "sign_mount_dark", "Sign Mount — dark structural post and board frame, matte painted steel",
        albedo=(0.103, 0.100, 0.099),
        roughness=0.7, metallic=0,
        specular=0.35,
        binds=("sign_frame", "sign_post"), scenes=("interior",),
        source="reference/01-station-exterior/welcome to babylon 5.webp (authority 1, 1000x750; reference/00-INDEX.md files it as 'misfiled — this is signage, not exterior' and calls it 'two backlit blue information boards in the customs hall'). MEASURED RAW, NOT BALANCED — see extrapolated. POST, clear of both boa",
        extrapolated="THE LEVEL, and the decision to measure this frame raw. Both are declared in full. (1) GREY-WORLD FAILS ON THIS FRAME, and I checked rather than assumed. Its gains are (1.262, 1.276, 0.702), and its balanced mid-tone population (0.15 < V < 0.85) has median saturation 0.299 and p90 0.469 against the a"))

    # =====================================================================
    # LAYER 3 -- THE DRUM LANDSCAPE
    # =====================================================================
    # garden.py's townscape and drum_ground.py's land-use bands: the only
    # surfaces in the project that are seen from a kilometre away and from two
    # metres in the same shot, because the drum curves overhead. Scene is
    # `drum`, not `interior`.
    #
    # Six general/specific overrides live in here and they are deliberate:
    # `garden_water` for the pool and `garden_waterfall` for the fall,
    # `garden_colonnade` and `garden_colonnade_core`, `ground_arable` and its
    # four crop variants. Substring-with-longest-wins exists for exactly that,
    # and test_materials_layer3.ambiguous() was rewritten to report containment
    # pairs rather than fail them -- it had been treating every specialisation
    # as a defect, which teaches a reader to distrust the check.

    # ---- drum landscape (bespoke) --------------------------------------

        # The single most important decision in the Garden, because this
        # material is most of the building the gazetteer ranks fifth and the
        # shot the owner's opening beat is composed around. Everything about
        # the frame says warm sandstone and the project has now found five
        # times that a colour in a frame belonged to the light; this is the
        # sixth, and it is the cleanest instance in the set, because a cylinder
        # gives a continuous lit-to-shaded ramp of ONE material under ONE light
        # and the saturation falls all the way down it. The four groups are
        # bound together because the frame measures them within 1.1% — they are
        # one poured render seen at four orientations, and splitting them would
        # be painting contrast that the reference does not have.
    a(Material(
        "garden_civic_render", "Garden Civic Render — the stacked-drum landmark's stone, shafts, colonnade fins, caps and slab terraces",
        albedo=(0.358, 0.358, 0.358), roughness=0.7, metallic=0,
        specular=0.42,
        binds=("garden_tower", "garden_colonnade", "garden_cap", "garden_slab",
               # Session 3s: the articulated block's render surfaces. Same
               # material, more of it -- plinth, pilaster, cornice, parapet,
               # expressed slab band, cill, lintel, balcony soffit and the
               # dwarf boundary walls are all the same rendered masonry this
               # entry was measured for. No new colour is introduced.
               "garden_plinth", "garden_pilaster", "garden_cornice",
               "garden_parapet", "garden_slab_band", "garden_cill",
               "garden_lintel", "garden_balcony", "garden_boundary",
               "garden_roof_plant"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1). Grey-world gains recomputed here from the frame: (0.884, 0.994, 1.159), reproducing materials.GREY_WORLD_GAINS to 0.000. Method control on the same frame: the lawn balances to H 112.0 S 0.337 V 0.651, reproducing the figure materials.PROVENANCE already records for it (H 114 S 0.330 V 0.651). LEVEL, via an in-frame anchor: the lawn's raw median is 0.522/0.655/0.373, luminance 0.606; materials.ground_parkland (0.345,0.425,0.260) has luminance 0.396; so K = 0.6534 converts this frame's raw luminance to albedo. Four render surfaces measured raw: tower shaft lit half (0.418,0.402)-(0.470,0.500) 0.580/0.525/0.537 lum 0.548; colonnade fin cluster 0.583/0.539/0.548 lum 0.549; cantilevered slab top (0.205,0.535)-(0.300,0.552) 0.586/0.545/0.552 lum 0.554; slab fascia (0.205,0.556)-(0.300,0.572) 0.587/0.537/0.548 lum 0.548. Mean lum 0.547 x K = 0.358, and the four agree within 1.1% of each other, which is why they are one material and not four. The lower second drum reads 0.475/0.420/0.420 lum 0.431 -> 0.282: same cylinder in less light, not a second stone. ORIENTATION CONTROL, which is what lets a vertical shaft be compared with a horizontal slab and with the paving at all: the horizontal slab top (lum 0.543) and the vertical lit shaft (lum 0.548) differ by 3.1% — inside a drum the bounce is nearly isotropic, so orientation is not what separates these surfaces.",
        extrapolated="The NEUTRALITY, and the roughness/specular/metallic. Neutrality is not a guess but it is a reading of a test rather than a direct measurement. The frame's architecture LOOKS warm pinkish sandstone — reference/00-INDEX.md reads it that way — and the test materials.NEGATIVE_RESULTS prescribes says the warmth is the light. Run on the tower cylinder alone (one material, one light, a continuous lit-to-shaded ramp), RAW, binned by value: V 0.30-0.40 meanS 0.220 rgb 0.353/0.293/0.277 R-B +0.076; 0.40-0.45 S 0.168 0.426/0.368/0.355 +0.071; 0.45-0.50 S 0.133 0.478/0.419/0.419 +0.059; 0.50-0.55 S 0.117 0.529/0.470/0.473 +0.055; 0.55-0.60 S 0.093 0.580/0.529/0.537 +0.043; 0.60-0.70 S 0.082 0.605/0.556/0.570 +0.036. Saturation FALLS monotonically 0.220 -> 0.082 while R rises 1.7x, and R-B holds roughly constant instead of scaling: that is an additive coloured lift, exactly the arithmetic materials.PROVENANCE uses to declare the hull neutral. Fitting R = k*B + c over those bins gives R = 0.862*B + 0.117 and G = 0.895*B + 0.046; the independent second drum gives R = 0.956*B + 0.076 and G = 0.970*B + 0.014. Both fits put the reflectance ratios AT or slightly BELOW neutral (R/B 0.86-0.96, G/B 0.89-0.97) and neither supports warm, so the render is set exactly neutral and the residual is left to the light. THE BALANCE MUST NOT BE USED FOR HUE ON THIS FRAME AND THIS IS THE SECOND FINDING: balanced with the recorded gains the same cylinder's saturation RISES with value (0.101 -> 0.187) and R-B runs -0.016 -> -0.120, i.e. the balance injects a multiplicative blue; the terrace paving, a different material on a horizontal plane, balances to H 222.6 S 0.215 — a lavender pavement, and above the 0.02-0.16 band materials.py says every large station surface occupies. The cause is in the scene: khaki farmland overhead fills 35% of this frame, so grey-world reads the subject's real warmth as a cast. Roughness 0.70: fine architectural render, matte, with the soft even falloff and no specular streak the frame shows across 20 facets of cylinder; below the 0.75 the library gives endcap_course_wall and above the 0.62 it gives drum_structure, because this is stucco, not plate. Metallic 0.0 and specular 0.42 follow from it being mineral render. Texture null and that is a gap, not a choice: none of the eight sheets in materials.TEX_SIZE is an architectural render — hull_plate and wall_plate are plate courses with rebated seams and the frame shows a seamless surface. Overturned by: any frame of this building under a cool or neutral key."))

        # garden.py built this drum specifically because without it the render
        # showed the magenta background through the top of the building — the
        # module says so, and its self-test asserts the group exists. That
        # makes it the one surface here whose job is to be DARK; give it the
        # render's albedo and the fins stop reading as fins. It is also the
        # surface most likely to be got wrong in both directions at once, so
        # the value is derived from a stated precedent rather than chosen, and
        # the frame reading it is half of is published so the next session can
        # move it with evidence.
    a(Material(
        "garden_loggia_recess", "Colonnade Loggia — the recessed drum standing behind the fins",
        albedo=(0.179, 0.179, 0.179), roughness=0.78, metallic=0,
        specular=0.38,
        binds=("garden_colonnade_core", "garden_bench"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, with the same in-frame ladder as garden_civic_render (lawn lum 0.606 -> materials.ground_parkland lum 0.396, K = 0.6534). A 2-cluster k-means across the colonnade band at (0.455,0.288)-(0.478,0.345) separates the two populations cleanly: 54.6% at rgb(0.161,0.095,0.062) lum 0.106 -> 0.070, and 45.4% at rgb(0.583,0.539,0.548) lum 0.549 -> 0.359 — the bay interior and the fin in front of it, and the fin reproduces garden_civic_render's 0.358 from an independent region. A second probe across a pure bay at (0.459,0.290)-(0.470,0.340) gives 69.3% at rgb(0.157,0.092,0.059), lum 0.103 -> 0.067. So the frame reads the loggia at 0.19x the fin standing in front of it.",
        extrapolated="The DEGREE of shadow baked in, and the neutrality. The frame's 0.19x has the full self-shadow of a 3.4 m deep loggia in it; the engine will supply that occlusion again, so baking all of it double-counts and the bays go black. materials.py has already made this call once for exactly this class of surface — endcap_course_wall, 'the riser behind each rib... in shadow behind every rib step', sits at 0.255 against endcap_plate's 0.430, i.e. 0.59x. Half of that precedent, 0.50x of garden_civic_render's 0.358, gives 0.179: dark enough that the colonnade reads as a colonnade rather than as a solid drum with stripes painted on it, and bright enough that engine shadowing has somewhere to go. Neutral for the same reason garden_civic_render is: the raw bay reads S 0.62, but the frame's built region has meanS 0.518 at V 0.10-0.20 falling to 0.082 at V 0.60-0.70, so the warmth on the darkest surfaces is the additive key, not paint — a deep recess lit only by bounce off warm ground is a LIGHTING statement and belongs to layer 4. Roughness 0.78 rather than the render's 0.70 because this surface is never cleaned. Overturned by: an engine frame of the loggia showing the bays reading either as solid or as holes."))

        # This is the Garden's contribution to the standing blocking finding —
        # 'NO EMISSIVE WINDOWS ANYWHERE... it reads as a derelict, not a city'
        # — carried inside the drum, where the same failure would make the
        # civic landmark read as an abandoned building at the centre of a
        # farmed cylinder. The interesting measurement is the one that says how
        # BRIGHT it is not: the panes do not clip, and they are two thirds of
        # the lit paving, so the honest fix is a dim source and not a lightbox.
    a(Material(
        "garden_glass", "Ground-Floor Arcade Glazing — the warmly lit glass ring behind the mullions",
        albedo=(0.060, 0.056, 0.052), roughness=0.1, metallic=0,
        specular=0.5,
        emission=(1.000, 0.836, 0.640), emission_energy=1.2,
        binds=("garden_glazing", "garden_lamp_head"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), measured RAW because a source is radiance and balancing it is meaningless. reference/00-INDEX.md calls this 'a deeply recessed arcade of tall narrow bronze-framed windows, grouped in threes and fours by mullions, warmly lit from within' (authority 1). Two pane-core regions clear of the piers, (0.6625,0.6370)-(0.6790,0.6680) and (0.7200,0.6370)-(0.7400,0.6680): medians 0.361/0.300/0.282 and 0.365/0.280/0.253; p90 0.491/0.420/0.409 and 0.535/0.480/0.463; p99 0.594/0.504/0.482 and 0.598/0.523/0.553. NOTHING CLIPS — the arcade's raw maximum is 0.628 — so by the library's own test (see zoc_neon_face, where the red channel clips and the surface is therefore declared a source) this is a DIM source, not a bright one. p90 normalised to peak is (1.000, 0.854, 0.832). Level against the same frame's terrace paving (raw lum 0.658): pane p90 lum 0.434, i.e. the windows are 0.66x the lit ground, so they must not out-shine the scene.",
        extrapolated="The emission colour, the albedo and the energy. COLOUR: taken from materials.WINDOW_TEMPS[0], the library's already-derived warm-practical window register (1.000, 0.836, 0.640), rather than from this frame's normalised p90 (1.000, 0.854, 0.832). The frame corroborates R and G to 0.018 and reads B high, which is what a 4-px pane does when the pale render pier beside it (measured 1.000/0.876/0.921 on the same row) bleeds into it; and taking the library's register keeps the Garden's windows the same temperature as the hull's, which is CLAUDE.md hard rule 4 applied to light. ALBEDO near black because what is modelled is a glass ring 0.25 m behind the mullions that IS a light; a pale substrate under an emission double-counts it — the argument materials.py already makes for zoc_screen (0.055,0.060,0.075). ROUGHNESS 0.10 is glass, which is one of the three things materials.py permits below 0.15. ENERGY 1.2, and it is deliberately the lowest emissive energy in the library: the panes measure 0.66x the lit paving, so this is a lit interior seen through glass in a daylit drum, not a sign. It sits far below zoc_screen's 2.6 and signage_panel's 3.0 because those are read at 1.5 m in a dim concourse and this is read at ~40 m in a lit one; the value is set so the glass reads as a source when the building's own shadow falls across it, which is what the frame shows, and does not blow out at drum noon. Overturned by: an engine frame at the drum's day exposure where the arcade either disappears or blooms."))

        # 0.22 m square posts in a ring of fourteen, and they are the thing
        # that makes a glazed ground floor read as architecture rather than as
        # a lit band. The value matters less than the discipline: this is the
        # darkest surface in the set and therefore the one where the frame's
        # warm additive key does the most damage, so the bracket is stated
        # rather than a single warm number presented as measured.
    a(Material(
        "garden_bronze_joinery", "Arcade Joinery — the dark bronze mullions and window surrounds",
        albedo=(0.140, 0.098, 0.082), roughness=0.45, metallic=0.25,
        specular=0.45,
        binds=("garden_mullion",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534. reference/00-INDEX.md records the material directly at authority 1: 'a deeply recessed arcade of tall narrow bronze-framed windows' and 'dark bronze joinery'. The dark reveal and head of the right-wing arcade, (0.6570,0.6230)-(0.7050,0.6370), k-means: 78.0% at rgb(0.240,0.137,0.091) H 18.3 S 0.620 lum 0.155 -> albedo 0.102; the remaining 22.0% at rgb(0.501,0.429,0.427) is the pale pier bleeding in. The pale render pier between window groups, measured separately at (0.7020,0.6250)-(0.7110,0.6700), reads 0.478/0.419/0.440 — 4.6x brighter and 0.5 in saturation apart, which is what makes the dark member a different material rather than the render in shadow.",
        extrapolated="The saturation and the metallic. Saturation is pulled back from the frame's measured 0.62 to 0.41. The reason is the additive test in garden_civic_render's entry, applied where it bites hardest: this frame's built region has mean saturation 0.518 at V 0.10-0.20 falling to 0.082 at V 0.60-0.70, and the fitted additive lift on the tower is +0.117 R / +0.046 G / +0.000 B — which on a reading of 0.240 R is half the signal. Subtracting the lift outright gives (0.123, 0.091, 0.091), a NEUTRAL dark member; taking the raw gives (1.000, 0.571, 0.379). Those are the two defensible endpoints and the value sits between them at chromaticity (1.000, 0.700, 0.586), scaled to the ladder's 0.102. Both endpoints are published so the next session can pick differently with one edit. METALLIC 0.25 rather than a real bronze's ~0.9: the frame shows no specular glint on any of the fourteen members at any orientation, so what is modelled is patinated or lacquered bronze whose visible surface is a dielectric coat, treated the same way materials.zoc_neon_back treats painted sheet steel at metallic 0.10. Roughness 0.45 is joinery: harder than render, softer than polished metal. Overturned by: a frame with a specular highlight of known colour on a mullion, which would give both the metallic and the true hue at once."))

        # Saturation 0.594 is far over the structural ceiling and it is
        # measured, twice, in two regions of an authority-1 frame, with the
        # index naming the material in words. This is the one place in the
        # Garden where colour is allowed to be colour, and it is worth being
        # exact about: the register agrees with a value the library already
        # holds, the LEVEL does not, and pretending the two are one material
        # would quietly brighten the stair 3.5x on an argument nobody wrote
        # down.
    a(Material(
        "garden_terracotta", "Terracotta Stair — the external flight, the one saturated accent in the Garden",
        albedo=(0.180, 0.089, 0.073), roughness=0.8, metallic=0,
        specular=0.35,
        binds=("garden_stair_accent",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), in-frame ladder K = 0.6534. reference/00-INDEX.md, authority 1: 'red-orange painted external stairs (the accent again, outdoors)' and 'a tall terracotta slab pylon stands proud at the right — the red-orange accent again, here as primary architecture rather than trim'. Two separate regions, at 10x magnification the stepped profile of the flight is unambiguous: (0.8880,0.5450)-(0.9280,0.5900) raw median 0.310/0.129/0.086 H 11.6 S 0.722 lum 0.165 -> 0.108, k-means 58% at (0.306,0.129,0.083) and 42% at (0.312,0.134,0.093) — one population, so the reading is the object and not an edge; and (0.8600,0.6100)-(0.9400,0.6500) raw median 0.292/0.141/0.114 H 9.2 S 0.611 lum 0.171 -> 0.112. Balanced with the recorded gains the same region reads 0.267/0.133/0.109, normalised (1.000, 0.498, 0.408) H 8.9 S 0.591 — the chromaticity used here. INDEPENDENT REGISTER CORROBORATION: materials.accent_warning is 'red-orange hazard paint' at H 12-20 S ~0.68, mean rgb (0.667, 0.306, 0.215), normalised (1.000, 0.459, 0.321) — this frame's (1.000, 0.498, 0.408) reproduces that register in a DRUM scene that accent_warning never used.",
        extrapolated="The LEVEL, and the decision not to reuse accent_warning's. The two agree on the register to within 0.04 in normalised chromaticity and disagree on level by 3.5x: accent_warning sits at luminance 0.395, this at 0.108. The disagreement is recorded rather than reconciled, and the reading taken here is the frame's, for two reasons. First, the anchor chain: accent_warning's level rides on materials.ALBEDO_ANCHOR through interior frames under interior key, and this one rides on the lawn in its own frame through ground_parkland — and that chain independently reproduces the anchor (see garden_flagstone), so it is not the chain that is wrong. Second, they are not the same material: accent_warning is hazard PAINT on plate, and reference/00-INDEX.md names this one terracotta, i.e. unglazed fired clay, which is genuinely a dark oxide red. Roughness 0.80 follows from that — fired clay is the roughest built surface in this scene, rougher than the 0.70 render. Overturned by: a frame showing the stair and a hazard-painted surface in one shot, which would settle whether the station has one red-orange or two."))

        # The paving is what the two figures walk on and what sets the scale of
        # the whole shot, and it turned out to be the most valuable measurement
        # in the set for a reason that has nothing to do with the Garden: it
        # lands on ALBEDO_ANCHOR from an entirely separate direction. That is
        # the check ALBEDO_ANCHOR_CORROBORATION says it cannot do for itself —
        # 'every reading uses the same balance method, so a systematic error in
        # the method would move all of them together' — and this one does not
        # use the balance at all.
    a(Material(
        "garden_flagstone", "Terrace Paving — large pale flagstones, the brightest surface in the Garden",
        albedo=(0.430, 0.430, 0.430), roughness=0.55, metallic=0,
        specular=0.45, texture="deck_plate", uv_scale=1.0 / 2.5,
        binds=("garden_terrace", "garden_paving", "garden_kerb",
               # Session 3s ground articulation: the bay joints, the planting
               # bed edging and the service trench lids are all the same laid
               # stone this entry was measured for.
               "garden_paving_joint", "garden_bed_edge", "garden_trench_lid"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534 (lawn raw 0.522/0.655/0.373 lum 0.606 -> materials.ground_parkland lum 0.396). reference/00-INDEX.md, authority 1: 'large pale flagstone paving' and 'pale concrete paving'. Region (0.545,0.845)-(0.790,0.925), clear of the two walking figures: raw median 0.682/0.651/0.663 lum 0.658 -> albedo 0.430; 90.8% of the region falls in one k-means cluster, so it is a single surface. Raw saturation ramp across it: V 0.50-0.60 S 0.107 R-B +0.056; 0.60-0.65 S 0.071 +0.038; 0.65-0.70 S 0.050 +0.022; 0.70-0.75 S 0.048 +0.011; 0.75-0.85 S 0.057 -0.021 — saturation falls and R-B crosses zero at the brightest, so the most directly lit paving is neutral and the warmth below it is the same additive key the tower shows. THE RESULT WORTH CARRYING: 0.430 reproduces materials.ALBEDO_ANCHOR_CORROBORATION's seven-frame mean of 0.435 to 1%, and materials.ALBEDO_ANCHOR itself (0.46) to 6.5%, through a chain that shares nothing with either — a drum scene, a ground_parkland anchor derived from reference/03-sector-blue/Babylon_5_2-22_29a.jpg, and no use of ALBEDO_ANCHOR at any step. That is an eighth corroboration of the one number the whole library hangs on, and the first from outside the interior.",
        extrapolated="Neutrality, roughness, and the texture stand-in. Neutrality is read off the ramp above rather than asserted. Roughness 0.55: laid stone, walked on, so smoother than the 0.70 render it abuts and rougher than anything polished — the same deck-smoother-than-wall logic materials.py enforces for interiors, applied here where the frame supports it (the paving is 1.20x the render's luminance, and the orientation control in garden_civic_render's entry shows only 3% of that is the horizontal/vertical difference, so it is a genuine albedo gap, not a lighting one). TEXTURE is a declared stand-in and the reason is worth recording: none of the eight sheets in materials.TEX_SIZE is a flagstone, so deck_plate — a seamed plate pattern — is bound at uv_scale 1/2.5 because 2.5 m is garden.TERRACE_SLAB_M, the module's OWN paving module. That keeps the joint spacing tied to the geometry rather than to a number picked to look right, and if garden.py ever changes its paving module the two must be changed together. Overturned by: a stucco/flagstone sheet being added to materials.TEX_SIZE, at which point this rebinds."))

        # 12 triangles, and it is the line that separates the water from the
        # terrace in the frame's strongest horizontal. If it took the paving's
        # value the pool would lose its edge and read as a hole in the
        # flagstones.
    a(Material(
        "garden_coping_stone", "Pool Coping — the dark stone rim of the reflecting pool",
        albedo=(0.191, 0.191, 0.191), roughness=0.6, metallic=0,
        specular=0.4,
        binds=("garden_pool_coping", "garden_planter"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534. reference/00-INDEX.md, authority 1: 'rectangular reflecting pool with a dark stone coping'. Region (0.042,0.754)-(0.250,0.787), the coping band running the full near edge of the pool: raw median 0.322/0.282/0.298 lum 0.292 -> albedo 0.191. Against the paving it abuts in the same frame (lum 0.658) that is 0.44x, which is what makes it read as a dark stone edge rather than as the terrace continuing.",
        extrapolated="Neutrality and the finish. Raw saturation is 0.12 and the frame's additive key accounts for most of it by the test in garden_civic_render's entry, so the coping is set neutral; at this saturation the decision is nearly cosmetic and is recorded only for consistency. Roughness 0.60: dressed stone with a sawn face, rougher than the walked flagstone (0.55) because nobody walks on a coping and it never polishes, and well short of anything wet. Overturned by: a frame of the coping under a cool key."))

        # The alternative was a second water value, which would have meant the
        # drum's lake and the Garden's pool disagreeing about what water is in
        # a scene where both can be in frame. The useful work here was
        # verification, not measurement: ground_water's stored reading was
        # recomputed from the frame before being reused, and it reproduces.
    a(Material(
        "garden_pool_water", "Reflecting Pool — still water, the surface that shows the drum overhead",
        albedo=(0.055, 0.115, 0.145), roughness=0.06, metallic=0,
        specular=0.85,
        binds=("garden_water",), scenes=("drum",),
        source="NOT A NEW MEASUREMENT: reproduced exactly from materials.ground_water, whose own source IS this pool in this frame — 'godot/scenes/drum.tscn; garden.png water balances H 195 S 0.476'. That reading was recomputed here before reuse: reference/09-garden-core-and-transit/garden.png (authority 1) at (0.042,0.813)-(0.250,0.892), balanced with the gains already in materials.GREY_WORLD_GAINS (0.884/0.994/1.159), gives median 0.184/0.292/0.341 H 198.5 S 0.461 V 0.341, with all three k-means clusters inside H 188-201 — reproducing the recorded H 195 S 0.476 on a region that entry did not specify. Raw the same region reads 0.208/0.294/0.294, lum 0.276, which through the in-frame ladder (K = 0.6534) is 0.180 — against ground_water's own luminance of 0.104, i.e. the frame reads the lit pool 1.7x its stored albedo, which is the specular sky term this material's roughness 0.06 exists to produce and not a reason to raise the diffuse value.",
        extrapolated="Nothing new. The one judgement is that the Garden's rectangular reflecting pool and the drum's lake are the same water and take the same material — which is not much of a stretch, since ground_water was measured off this pool. Roughness 0.06 is below the library's 0.15 floor and is one of the three things allowed there; materials.py's own note says why it must stay there: 'in a drum the water reflects the ground overhead, which is the single most legible statement the geometry can make about where you are standing', and a 30 x 12 m rectangle four metres from the camera is exactly where that statement gets made. Overturned by: nothing this frame can supply."))

        # The fragment matters as much as the value. 'garden_water' is a
        # SUBSTRING of 'garden_waterfall', so resolution by longest match only
        # sends the fall here as long as the full fragment stays bound; drop it
        # and the waterfall silently becomes still pool water at roughness 0.06
        # and turns into a vertical mirror. Both fragments must survive
        # together.
    a(Material(
        "garden_falling_water", "Waterfall — the aerated column down the planted bank",
        albedo=(0.205, 0.228, 0.236), roughness=0.32, metallic=0,
        specular=0.6,
        binds=("garden_waterfall",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534. reference/00-INDEX.md, authority 1: 'a tall thin waterfall on a planted bank'. Region (0.104,0.500)-(0.140,0.700), the full drop: raw median 0.314/0.349/0.361 lum 0.342 -> albedo 0.224; balanced 0.277/0.347/0.418 H 210.4 S 0.337; k-means gives the fall's two bright populations at (0.356,0.447,0.549) H 211.7 and (0.268,0.333,0.396) H 209.5, with the third cluster (0.162,0.183,0.181) the dark bank showing through. At 3x magnification the column is plainly a pale blue-white foaming sheet, not a smooth one.",
        extrapolated="The chromaticity is taken RAW and not corrected, and that is the choice worth flagging. This frame carries an additive WARM key (see garden_civic_render), so a surface that still reads COOL raw is reading cool despite the light, and correcting it further would push it to a saturation no water has. So the raw normalised (0.870, 0.967, 1.000) is used as measured, scaled to the ladder's 0.224. Roughness 0.32: this is the same water as garden_pool_water and NOT the same surface — falling aerated water is foam, which scatters, so it must sit well above the 0.15 floor while the still pool sits below it. That the fall measures 2.1x the pool's luminance (0.224 against ground_water's 0.104) is the frame agreeing: foam is brighter than a mirror pointed at a dark ceiling. Specular 0.60 between the pool's 0.85 and a mineral surface. Overturned by: a frame of the fall against a bright background, which would separate the water's own scattering from what is behind it."))

        # This is the material the whole Garden ladder stands on, so the honest
        # thing is to say plainly that its level cannot corroborate itself.
        # What it can do — and did — is corroborate its own HUE from a second
        # frame, and then hand the level onward to the paving, which lands on
        # ALBEDO_ANCHOR from outside. Adding a second, differently-valued green
        # here would have broken the chain and put a visible seam where the
        # terrace meets the parkland band.
    a(Material(
        "garden_mown_grass", "Mown Lawn — the striped grass strips on the terrace",
        albedo=(0.345, 0.425, 0.260), roughness=0.95, metallic=0,
        specular=0.35,
        binds=("garden_lawn",), scenes=("drum",),
        source="NOT A NEW MEASUREMENT: reproduced exactly from materials.ground_parkland ('Parkland — designed park at ground level', sampled from reference/03-sector-blue/Babylon_5_2-22_29a.jpg). AND IT IS THE FRAME'S OWN ANCHOR, so the agreement in LEVEL is by construction and is not evidence: this material's value is what defines K = 0.6534 for every other Garden measurement. What IS independent is the chromaticity. reference/09-garden-core-and-transit/garden.png (authority 1) at (0.820,0.790)-(0.975,0.860), raw median 0.522/0.655/0.373, normalised 0.336/0.421/0.240; materials.ground_parkland normalised is 0.334/0.412/0.252 — two different frames, two different sectors of the reference set, agreeing to within 0.012 on all three channels. Balanced, the same region gives H 112.0 S 0.337 V 0.651, reproducing the figure materials.PROVENANCE already records for this lawn (H 114 S 0.330 V 0.651) and confirming the balance is being applied the way that block applied it.",
        extrapolated="That the Garden's mown terrace lawn and the drum's parkland band are one material. reference/00-INDEX.md reads the Garden's grass as 'striped mown lawn' and the parkland band as 'a designed park, not rough grass' — the same maintained turf under the same axial light, at 40 m and at 400 m. Roughness 0.95 and specular 0.35 are ground_parkland's and are carried unchanged. Overturned by: a frame showing mown stripe and open parkland in one shot at a value ratio away from 1.0."))

        # Two hundred and forty triangles of tree per settlement band, so the
        # material is the whole read. The library already contains a measured
        # value for dense drum vegetation and it is 7% from what a second frame
        # gives for a canopy specifically — inventing a third green when two
        # independent readings already agree would be the kind of unmarked
        # invention CLAUDE.md's first hard rule is about.
    a(Material(
        "garden_foliage", "Tree Canopy — dense broadleaf massing",
        albedo=(0.225, 0.275, 0.170), roughness=0.98, metallic=0,
        specular=0.35,
        binds=("garden_canopy", "garden_foliage", "garden_hedge"), scenes=("drum",),
        source="NOT A NEW MEASUREMENT: reproduced exactly from materials.ground_hedge ('Hedge — field boundary, darkest green in frame', from Babylon_5_2-22_34b.jpg). CORROBORATED in a frame it did not use: reference/03-sector-blue/Babylon_5_2-22_29a.jpg (authority 1, and reference/00-INDEX.md places this frame in the Garden, not Blue sector). Its grey-world gains, computed here, are (0.884, 1.043, 1.099). The rounded broadleaf canopy at (0.250,0.190)-(0.400,0.260) balances to median 0.212/0.253/0.181 H 94.7 S 0.286, luminance 0.239, against ground_hedge's luminance of 0.257 — 7% apart, on a surface ground_hedge was not measured from. In reference/09-garden-core-and-transit/garden.png the deciduous masses behind and left of the building sit at albedo 0.12-0.18 through the in-frame ladder, i.e. this value seen in shadow.",
        extrapolated="That a tree canopy and a hedgerow are the same material. They are the same thing at different scales — dense leaf mass presenting a rough, self-shadowing surface — and garden.tree() builds the canopy as a 6-segment drum, which is a foliage BILLBOARD's cousin at 0.06 tri/m2 and can carry no leaf detail of its own; all the read has to come from the material. Roughness 0.98 and specular 0.35 are ground_hedge's, unchanged. NOTE ON 29a AS A COLOUR SOURCE: it is used here for corroboration only and its balanced structural surfaces come back at S 0.19-0.32, which is the same over-correction garden.png shows — the frame is dominated by dark foliage, so grey-world reads the subject as a cast. Its foliage reading is trusted precisely because foliage is what dominates it. Overturned by: a near-field tree in an unambiguously neutral frame."))

        # garden.tree() gives a trunk 0.44 m square and 3 m tall and there is
        # genuinely no reference for it, so the choice is a marked
        # extrapolation or a hole, and CLAUDE.md is explicit that the answer is
        # never a hole. What makes it reviewable is that it says exactly which
        # number is sourced (the bank's 0.132), which constraint fixes the rest
        # (darker than the canopy over it), and that one photograph would
        # overturn the whole entry.
    a(Material(
        "garden_bark", "Tree Trunk — bark, dark grey-brown",
        albedo=(0.148, 0.135, 0.121), roughness=0.92, metallic=0,
        specular=0.3,
        binds=("garden_trunk", "garden_branch"), scenes=("drum",),
        source="NO FRAME MEASURES THIS, and saying so is the point. In reference/09-garden-core-and-transit/garden.png no trunk exceeds two pixels and every one of them stands against dark canopy, so any reading is a mixture; in reference/03-sector-blue/Babylon_5_2-22_29a.jpg (authority 1) trunks are visible — reference/00-INDEX.md records 'palm trees lining streets and open ground, plus dark rounded broadleaf trees' — but at that frame's exposure they are inseparable from the shadow behind them. The only sourced quantity is the level it is tied to: reference/09-garden-core-and-transit/garden.png's planted bank at (0.010,0.590)-(0.075,0.700), raw median 0.235/0.200/0.129, luminance 0.202, which through the in-frame ladder (lawn lum 0.606 -> materials.ground_parkland lum 0.396, K = 0.6534) is 0.132.",
        extrapolated="Everything except the level it is pinned to. Value 0.135 sits at the planted bank's 0.132, on the argument that bark and shaded planted earth are the same class of dark organic surface and no frame in the set separates them; it must stay BELOW garden_foliage's 0.257 so a trunk never reads brighter than the canopy above it, which is the one relationship a viewer would notice. Saturation is held to 0.18 — under the library's 0.20 structural ceiling — because there is no frame to buy anything higher with, and because the warm reading the bank gives is the frame's additive key by the test in garden_civic_render's entry. Roughness 0.92: bark is the second-roughest surface in this set after foliage. Overturned by: any near-field frame of a tree in the drum, which would settle it in one measurement — this is the weakest entry in the family and it is 88 triangles."))

        # A 14 x 12 m box that reads as a mass in silhouette behind the
        # waterfall, so what it owes is a level dark enough to give the fall
        # something to be pale against, and a hue that does not turn into an
        # ochre hillside — which is exactly the mistake NEGATIVE_RESULTS
        # records for the corridor dado, made outdoors.
    a(Material(
        "garden_bank_planting", "Planted Bank — the dark embankment the waterfall runs down",
        albedo=(0.138, 0.140, 0.118), roughness=0.95, metallic=0,
        specular=0.32,
        binds=("garden_bank",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534. reference/00-INDEX.md, authority 1: 'a tall thin waterfall on a planted bank'. Region (0.010,0.590)-(0.075,0.700), the bank clear of the fall: raw median 0.235/0.200/0.129 luminance 0.202 -> albedo 0.132; k-means over it gives 43.3% at (0.242,0.200,0.154) lum 0.205, 30.9% at (0.171,0.141,0.078) lum 0.143 and 25.8% at (0.273,0.286,0.146) lum 0.273 — soil, shadow and planting, whose weighted level is what the single value takes. Against materials.ground_hedge (luminance 0.257) the bank reads 0.52x, i.e. planting seen in shadow with earth showing through it.",
        extrapolated="The chromaticity, which is pulled from the raw reading's saturation 0.45 down to 0.157. Raw, this bank is strongly warm (H 40); corrected by the additive lift fitted on the tower (+0.117 R, +0.046 G, +0.000 B) it goes cool-olive; the value sits between, at a dark olive-neutral, and both endpoints are published. The reason not to keep the raw warmth is materials.NEGATIVE_RESULTS' rule applied where it bites hardest — this frame's built region runs mean saturation 0.518 at V 0.10-0.20 against 0.082 at V 0.60-0.70, so the darkest surfaces are the most cast-contaminated, and 0.202 is dark. Roughness 0.95 as planting. Overturned by: a frame of this bank from the other side of the pool, where it is lit rather than shadowed."))

        # Four banners of 12 triangles each and they are the brightest thing in
        # the lower half of the frame, which is why they are worth being exact
        # about: get them wrong downward and the flagpole group disappears; get
        # them wrong upward and four small white rectangles become the
        # composition's focal point instead of the building.
    a(Material(
        "garden_pennant", "Banner — white cloth on the flagpoles",
        albedo=(0.478, 0.478, 0.478), roughness=0.85, metallic=0,
        specular=0.3,
        binds=("garden_banner",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1), raw, in-frame ladder K = 0.6534. reference/00-INDEX.md, authority 1: 'flagpoles with white banners' and 'at least four slender white flagpoles'. At 6x magnification the banners are unambiguous hanging white pennants. Region (0.8115,0.4200)-(0.8198,0.5200), the leftmost banner's flat face: raw median 0.669/0.631/0.651 luminance 0.641 -> 0.419; p90 0.747/0.722/0.741 luminance 0.728 -> 0.476; k-means 69.6% at (0.697,0.670,0.690) and 30.4% at (0.489,0.443,0.449) — the lit face and its shaded folds. Chromaticity of the lit face is 1.000/0.961/0.990, i.e. neutral to within 4%, which for a warm-cast frame is a white surface.",
        extrapolated="Taking p90 rather than the median, and the neutrality. p90 because the median includes the folds — the 30% shaded cluster — and a hanging cloth's albedo is the flat lit face, not the average of face and fold; the two differ by 1.4x and the folds are geometry the engine will produce for itself. Neutral because 1.000/0.961/0.990 is inside the frame's noise and because it is the only surface in the Garden the index calls white outright. At 0.478 it is the brightest material in the family, just above the paving's 0.430, which is what the frame shows. Roughness 0.85 as woven cloth, specular 0.30. Overturned by: a frame showing the banner carrying an emblem, which the reference does not resolve."))

        # Four 12-triangle boxes 9 m tall. The temptation was to publish the
        # probe's 0.375/0.262/0.256 as measured, and it would have passed every
        # gate in the project while being half a reading of the object behind
        # it. Saying which number is real (the banner's 0.476), what
        # relationship the frame supports (pole slightly below cloth), and what
        # would settle it is worth more than a citation stapled to a
        # contaminated pixel.
    a(Material(
        "garden_mast", "Flagpole — slender painted metal mast",
        albedo=(0.452, 0.452, 0.452), roughness=0.38, metallic=0.15,
        specular=0.5,
        binds=("garden_flagpole", "garden_rail", "garden_downpipe",
               "garden_gutter", "garden_lamp_column", "garden_track_pier",
               "garden_sleeper"), scenes=("drum",),
        source="reference/09-garden-core-and-transit/garden.png (authority 1). THE POLE CANNOT BE MEASURED AND THIS ENTRY SAYS SO. garden.FLAGPOLE_R_M is 0.11 m, which at this frame's scale is one to two pixels; a probe at (0.8770,0.5450)-(0.8820,0.5900) returns 0.375/0.262/0.256 H 8.1 S 0.35, and its two k-means clusters are (0.375,0.262,0.256) and (0.300,0.177,0.167) — both warm, because the pole at that station is standing in front of the terracotta stair and the reading is at least half background. What the frame DOES establish, at 6x magnification, is the pole's relationship to its own banner: a pale grey-silver shaft with a dark finial cap, reading marginally darker than the cloth beside it. reference/00-INDEX.md, authority 1: 'at least four slender white flagpoles'.",
        extrapolated="The whole value, and it is pinned to one measured neighbour rather than chosen. garden_pennant's lit face measures 0.476 in this frame; the index calls both the poles and the banners white; the magnified frame reads the pole a little below the cloth; so the mast sits just under it at 0.452, which is also materials.ALBEDO_ANCHOR's neighbourhood and therefore not a value that will look out of family anywhere. Neutral rather than the warm probe reading, because the probe is a mixture with the terracotta behind it — a warm number taken from that region would be the stair's colour, which is the same trap materials.zoc_neon_back records for a sign board carrying its own tube's spill. Metallic 0.15 and roughness 0.38: painted metal, so mostly dielectric, with enough sheen for a 9 m mast to catch a highlight and read as round. Overturned by: any higher-resolution frame of the flagpoles, or one where they stand against sky rather than against the stair."))

        # Twelve of these per settlement band and they are the town — the
        # difference between the Garden being a building in a field and the
        # Garden being a district. Neither available frame can be
        # colour-matched, so what is published is the bracket both give, the
        # reason the value sits where it does inside it, and the fact that
        # nothing here is a hue measurement.
    a(Material(
        "garden_town_block", "Town Block — the low flat-roofed buildings of the drum settlement",
        albedo=(0.335, 0.335, 0.335), roughness=0.72, metallic=0,
        specular=0.42,
        binds=("garden_block",), scenes=("drum",),
        source="TWO FRAMES, BRACKETING, and neither can be colour-matched. reference/09-garden-core-and-transit/The Gardens.webp (authority 1) is the frame that shows this object — reference/00-INDEX.md: 'low-rise flat-roofed blocky buildings, two to four storeys, in a dense orthogonal street grid. Pale warm stone' — and the same index says outright 'the whole frame carries a heavy pink-magenta cast (tape colour shift)... Do not colour-match this file'. Its gains, computed here, are (0.854, 1.056, 1.134). So it is used for a RATIO only: block wall raw luminance 0.341-0.361 against the distant mown hillside in the same frame at 0.516-0.523, i.e. 0.66-0.70x; anchoring that hillside to materials.ground_parkland (luminance 0.396) puts the wall at 0.269. reference/03-sector-blue/Babylon_5_2-22_29a.jpg (authority 1, and reference/00-INDEX.md places this frame in the Garden) gives the second bracket: its glazed-band building's wall at (0.560,0.060)-(0.640,0.150) balances to luminance 0.353, and its broadleaf canopy at (0.250,0.190)-(0.400,0.260) to 0.239 against materials.ground_hedge's 0.257, so K29 = 1.075 and the wall is 0.380. The bracket is 0.269-0.380.",
        extrapolated="The value inside the bracket, and the neutrality. 0.335 is set at 0.94x garden_civic_render's 0.358 rather than at the bracket's midpoint, and the reason is a statement about what the object is: reference/00-INDEX.md reads the town as 'pale warm stone' and reference/14-characters-and-uniforms/talia-winters in gorgeous office.webp — whose reading materials.py already quotes in drum_ground.py's header — as 'low wide grey settlement blocks, terraced rather than towered'. Same construction as the civic landmark, plainer and dirtier; a hair below it, and inside both frames' brackets. Neutral because both frames' balanced structural surfaces come back at H 220-265 S 0.19-0.32, which is the same grey-world over-correction garden.png shows and the index warns about for The Gardens.webp by name. Roughness 0.72, just above the civic render's 0.70, on the same argument: plainer render, less maintained. Overturned by: a clean, neutral-cast frame of the drum settlement at ground level, which the reference set does not contain."))

        # This is the standing blocking finding — 'a station housing 250,000
        # renders completely unlit from within' — as it appears INSIDE the
        # hull. Twelve blocks a band with up to three bands each is the only
        # artificial light in the drum's town, and if it ships unlit the
        # settlement reads as ruins in a farmed cylinder. The frame is unusable
        # for colour and perfectly good for the one thing that sets the energy:
        # whether the source clips. It does.
    a(Material(
        "garden_town_window", "Town Window Band — the lit horizontal banding on the settlement blocks",
        albedo=(0.070, 0.062, 0.052), roughness=0.3, metallic=0,
        specular=0.4,
        emission=(1.000, 0.836, 0.640), emission_energy=2.6,
        binds=("garden_window_band",), scenes=("drum",),
        source="reference/09-garden-core-and-transit/The Gardens.webp (authority 1), measured RAW because a source is radiance. reference/00-INDEX.md, authority 1: 'continuous horizontal window banding — rows of small bright rectangles in dark recessed bands, giving strong horizontal striping. One large building at right shows exactly three stacked glazed bands over a solid battered base', and separately 'low blockish buildings with lit window bands'. At 3x magnification the two bands on the right-hand block resolve into rows of bright rectangles in dark recesses. The lower band, measured across the block: raw p99 reaches (1.000, 0.980, 0.902) — THE RED CHANNEL CLIPS, which is the library's own test for a source (see zoc_neon_face, where the same test is what separates a source from a lit surface). Raw p90 (0.710,0.620,0.553), normalised (1.000, 0.874, 0.780); brightest k-means cluster (0.880,0.821,0.747). The upper band gives raw p90 (0.514,0.388,0.298) and p99 (0.773,0.659,0.570).",
        extrapolated="The emission colour and the energy. COLOUR is taken from materials.WINDOW_TEMPS[0] (1.000, 0.836, 0.640), the library's warm-practical window register, and NOT from this frame, because the frame cannot supply it: raw it normalises to (1.000, 0.874, 0.780), and balanced with this frame's gains (0.854, 1.056, 1.134) it normalises to (0.925, 1.000, 0.958) — a GREEN window, which is impossible. reference/00-INDEX.md declares this file uncolour-matchable for exactly this reason. The two readings bracket the library's register and reusing it keeps the drum's town, the civic arcade (garden_glass) and the hull's apertures at one colour temperature, which is CLAUDE.md hard rule 4 applied to light. ENERGY 2.6 against garden_glass's 1.2, and the difference is measured, not felt: these bands CLIP in their frame and the civic arcade does not clip in its own (maximum 0.628), so one is a source at saturation and the other is a dim one. 2.6 matches materials.zoc_screen's, a backlit panel of similar apparent brightness. ALBEDO near black because the band is a 0.06 m proud box that IS a light and a pale substrate under an emission double-counts it. Overturned by: any neutral-cast frame of the drum settlement at night."))

    # =====================================================================
    # LAYER 3 -- BLUE SECTOR PUBLIC: C&C, the Council Chamber, customs, the bay
    # =====================================================================
    # NINE materials for 55 groups, because EIGHTEEN of the surfaces turned out
    # to be ones this library already has. The proposal rebound them --
    # `bay_deck` onto shell_deck_industrial, `cc_floor` and `customs_deck` onto
    # shell_deck_public, `council_top` onto furn_casework -- instead of
    # authoring near-duplicates, which is what keeps a docking bay's deck and
    # a fabrication bay's deck the same deck.
    #
    # That is the same move `signage_panel` made: the material already existed
    # and had simply never been bound to the geometry it was measured from.

    # ---- blue sector public (bespoke) ----------------------------------

        # The disc is the only painted marking on the station whose SIZE is
        # measured rather than chosen (docking_bay.py DECK_DISC_D_M = 10.6 m
        # off the dock workers), so it deserved a measured colour too. It comes
        # out a dusty oxide red at S 0.26, not a fire red — which is what a
        # worn hangar-deck marking should be, and it is high enough above the
        # STRUCTURAL_SAT_MAX 0.20 ceiling that the gate will demand the frame
        # citation it has. The level is set by ratio to the deck rather than by
        # lit() because both surfaces sit inside the same floodlight pool,
        # where lit() (calibrated on a diffusely lit wall) would overstate
        # both.
    a(Material(
        "bay_deck_marking", "Bay Deck Marking — the red painted landing disc",
        albedo=(0.405, 0.299, 0.308), roughness=0.58, metallic=0,
        specular=0.38,
        binds=("bay_disc",), scenes=("interior",),
        source="reference/03-sector-blue/dock.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.968/1.027/1.006, recomputed here from the frame as 0.9684/1.0271/1.0063). THE TINT TEST, run and PASSED: value-banded over the disc at (0.450,0.645)-(0.590,0.715) it reads rgb 0.363/0.266/0.271 H 357.1 S 0.266 at V 0.30-0.42 (n=777); 0.480/0.359/0.372 H 353.2 S 0.252 at V 0.42-0.52 (n=1287); 0.568/0.419/0.433 H 354.2 S 0.263 at V 0.52-0.62 (n=3505); 0.652/0.541/0.558 H 351.0 S 0.170 at V 0.62-0.80 (n=1016). Saturation is FLAT at 0.25-0.27 across a 1.8x range of value, falling only in the clipping band, and hue holds at H 351-357 throughout — the multiplicative signature of a real tint, where materials.NEGATIVE_RESULTS' five recorded cases all showed saturation collapsing as value rose. LEVEL: the deck it is painted on, same frame, same flood pool. k-means over (0.22,0.50)-(0.62,0.78) puts the dominant 25.6% of the deck on balanced rgb 0.237/0.237/0.233 (H 50 S 0.017, dead neutral) -> lit() 0.370, which reproduces materials.py's shell_deck_industrial 0.365 to 1.4%. Inside the pool the disc's luminance is 0.87x the deck's (disc L 0.458 at (0.470,0.655)-(0.520,0.690) against deck L 0.526 at (0.412,0.650)-(0.442,0.685)), so 0.87 x 0.370 = 0.322 luminance, carried on the measured hue normalised to peak (1.000, 0.738, 0.762).",
        extrapolated="Roughness 0.58 and specular 0.38 — no frame separates gloss from geometry here, and both are set slightly duller than the deck's own 0.52 because deck traffic paint is a flat coating and a glossier value would flare under the pendant floods. Nothing about the colour: hue, saturation and the 0.87 ratio are all measured in one frame under one light. Overturned by any frame showing this disc away from a flood pool."))

        # Splitting bay_emblem from bay_disc is the module's decision and it is
        # right — a red disc with a white device on it is what the frame shows
        # — but the material has to admit that the frame cannot colour the
        # device. Making it a declared extrapolation bracketed by three
        # measured numbers is better than quietly copying the disc's red, which
        # is what a single material would have done.
    a(Material(
        "bay_deck_emblem", "Bay Deck Emblem — worn white line paint inside the disc",
        albedo=(0.560, 0.545, 0.530), roughness=0.6, metallic=0,
        specular=0.38,
        binds=("bay_emblem",), scenes=("interior",),
        source="reference/03-sector-blue/dock.webp (authority 1), balanced (0.968/1.027/1.006). A NEGATIVE MEASUREMENT, and it is the honest content of this entry: at 4x magnification the emblem is two pale rounded bars about 4 px tall, and the frame does not resolve them clear of the red around them. The bars at (0.4735,0.6965)-(0.4855,0.7035) read balanced rgb 0.627/0.491/0.515 (H 349.5 S 0.216 V 0.627) and at (0.5205,0.6975)-(0.5325,0.7045) rgb 0.630/0.497/0.525 (H 347.6 S 0.211), against the disc ground 15 px away at (0.4930,0.6975)-(0.5130,0.7040) rgb 0.619/0.503/0.525 (H 348.9 S 0.187 V 0.619). That is 1.3% brighter and 15% MORE saturated than its own ground — i.e. the sample is dominated by the red it sits in, not by the emblem. All the frame establishes is what docking_bay.py's docstring already records from it: a white oval emblem inside the red disc.",
        extrapolated="The whole albedo. Constrained rather than free: (1) it must be lighter than the disc it sits inside, whose luminance is measured at 0.322; (2) it must be lighter than the deck at 0.370, or it would read as a stain rather than a marking; (3) it must sit below fresh white line paint, which is 0.70-0.75, because nothing in a working docking bay is fresh. 0.547 luminance is the middle of that bracket, i.e. white line paint about half worn. Saturation 0.054 is neutral: no frame gives it a hue, and the 15% desaturation the sample shows against its red ground is the only directional evidence, which says less saturated, not warmer. Overturned by one frame that resolves the emblem at more than about 10 px."))

        # The bay's read in dock.webp is entirely lighting: red steel overhead,
        # dark everywhere except under the floods, and pools on the deck. If
        # bay_lamp is not emissive the room is a grey box with boxes hanging in
        # it. The colour is the easy part — three independent samples all land
        # inside S 0.081 of neutral, so this is a plain cool-white industrial
        # flood, not a coloured practical, and it must NOT pick up the cyan
        # register that the Blue-sector accent table would otherwise suggest.
    a(Material(
        "bay_floodlight", "Bay Floodlight — pendant cool-white flood on the overhead lattice",
        albedo=(0.620, 0.620, 0.610), roughness=0.35, metallic=0,
        specular=0.25,
        emission=(0.942, 0.929, 1.000), emission_energy=6,
        binds=("bay_lamp", "light_highbay", "light_plant_flood"),
        scenes=("interior",),
        source="reference/03-sector-blue/dock.webp (authority 1). Measured RAW, because a source keeps its own colour and balancing it would remove exactly the thing being read — the same treatment materials.py gives the Zocalo shopfront and the rotunda altar. The two unoccluded flood cores read rgb 0.408/0.400/0.435 (H 253 S 0.081) at (0.368,0.092)-(0.386,0.108) and rgb 0.539/0.524/0.565 (H 263 S 0.073) at (0.527,0.070)-(0.545,0.088); k-means over the pool at (0.360,0.085)-(0.395,0.115) puts 11.8% on rgb 0.585/0.577/0.621 (H 250 S 0.071). Near-neutral at every reading, faintly cool, S never above 0.081 — normalised to its peak channel that is (0.942, 0.929, 1.000). docking_bay.py's docstring records the fitting itself from this frame: pendant floodlights hanging at regular spacing off the lattice gantry, 'the bay's whole lighting scheme and the first thing that reads'.",
        extrapolated="emission_energy 6.0 and the housing albedo. Energy: matched to materials.py's light_pilaster_strip (6.0), which is a corridor's principal wall light, on the argument that this is the bay's principal light and the fitting is far larger — docking_bay.py builds it as a 1.5 m box against the strip's ~0.1 m tube, so at equal energy this delivers roughly fifteen times the flux, which is the right order for a 42 x 140 m hangar against a 3 m corridor. The visible beam shafts in the frame are haze, not intensity, and were not used to argue it up. Housing 0.62: the geometry is the whole fitting, so it must not read as a hole when unlit; 0.62 is a painted steel lamp body, darker than materials.py's truss_lamp tube at 0.95 because that is glass and this is not. Overturned by any frame showing a dark bay bay with the floods off.",
        note=("`light_highbay` is rooms.py's industrial and store fitting and "
              "resolves here deliberately: docs/layer4-lighting/"
              "command_working.json re-measured this same fitting in the same "
              "frame for layer 4 and got (0.850, 0.830, 1.000) against the "
              "(0.942, 0.929, 1.000) above — the same faintly cool near-"
              "neutral, differing by 0.09 in the channel a normalisation "
              "choice moves. A plant hall and a cargo bay are lit the way a "
              "docking bay is, and giving them a second flood material would "
              "be recording that difference as real. `light_plant_flood` is "
              "the same fitting again in plant.py, and it is a separate GROUP "
              "only because its range transfers unscaled: a five-deck plant "
              "bay is 5 x DECK_PITCH_M = 18.0 m, which is the depth "
              "bay_flood's 30 m range was measured at.")))

        # command_control.py's docstring calls these 'the room's ambient
        # light', and it is the truest thing in the module: every other surface
        # in that frame is a reflection of these strips. Using
        # ACCENTS['cool_blue'] rather than a new number is deliberate —
        # SECTOR_ACCENT already names cool_blue as Blue Sector's register and
        # cites this exact room, so the strip IS the register, not a thing that
        # resembles it. The saturation looks alarming for a light source until
        # you notice the whole frame reads H 215-230; that is what makes this
        # room the one place on the station where a saturated light is measured
        # rather than chosen.
    a(Material(
        "light_command_strip", "C&C Wall Course — the cool-blue backlit strip that is the whole room's ambient",
        albedo=(0.780, 0.800, 0.840), roughness=0.28, metallic=0,
        specular=0.2,
        emission=(0.240, 0.320, 1.000), emission_energy=3.8,
        binds=("cc_light_strip",), scenes=("interior",),
        source="reference/03-sector-blue/comand and contorl.webp (authority 1). Measured RAW — see the coverage note: this frame's grey-world balance is INVALID for albedo, but a source read raw is exactly what it is good for, and materials.py's ACCENTS['cool_blue'] was already derived from it. Pooling the two high courses (0.02,0.145)-(0.25,0.185) and (0.83,0.145)-(0.99,0.185) with the mid course (0.09,0.395)-(0.27,0.428) and banding by value: rgb 0.073/0.147/0.274 H 218.0 S 0.734 at V 0.20-0.35 (n=3743); 0.229/0.307/0.424 H 216.0 S 0.459 at V 0.35-0.50 (n=1055); 0.375/0.456/0.571 H 215.3 S 0.342 at V 0.50-0.65 (n=750); 0.546/0.621/0.733 H 215.9 S 0.255 at V 0.65-0.80 (n=1155); 0.758/0.847/0.935 H 209.9 S 0.189 at V 0.80-1.01 (n=2998). Hue is CONSTANT at H 210-218 across a 3.5x range of value while saturation falls monotonically 0.734 -> 0.189 — a source blowing toward white with its register intact. The un-clipped V 0.35-0.50 band normalises to (0.540, 0.724, 1.000), H 216 S 0.46. Emission is taken as materials.py's ACCENTS['cool_blue'] (0.240, 0.320, 1.000), whose own note records 'H 228, C&C brightest cluster H228 S0.880' from this frame; my independent read lands in the same register 12 deg away and less saturated only because the sample sits nearer the clipped core.",
        extrapolated="emission_energy 3.8 and the diffuser albedo. Energy: two-thirds of materials.py's light_pilaster_strip (6.0) because the emitting area is roughly ten times larger — command_control.py builds four courses 0.22 m tall running the full 12 m room against a pilaster strip's ~0.1 x 2 m — and because the frame shows a room that is dark everywhere the courses do not reach, so this is a bright source in a dark room rather than a bright room. Albedo 0.78/0.80/0.84: a pale cool diffuser, reproduced in kind from light_pilaster_strip's (0.85, 0.86, 0.88) and taken down 8% because these are recessed panels behind a grille rather than a bare tube. Overturned by an engine render at this room's real light levels that comes out too blue at a correct exposure."))

        # council_chamber.py says it plainly: 'THE LIGHT IS THE POINT. If the
        # mesh panel is not emissive this room is a grey box with chairs.' The
        # interesting part is that the docstring also calls it 'perforated gold
        # mesh', and the frame does not support gold at any value band under
        # either treatment. Carrying the warmth as H 65 at S 0.09 keeps the
        # cream the magnification shows while refusing the saturation the word
        # 'gold' implies — and it keeps the panel inside the neutral band the
        # rest of the station obeys, which matters because this surface lights
        # every delegate's face.
    a(Material(
        "council_lit_mesh", "Council Bench Panel — the perforated backlit face, the room's light source",
        albedo=(0.420, 0.410, 0.390), roughness=0.45, metallic=0,
        specular=0.35,
        emission=(1.000, 0.968, 0.910), emission_energy=2,
        binds=("council_mesh",), scenes=("interior",),
        source="reference/05-sector-green/council chambers.webp (authority 1), balanced with the gains already in materials.GREY_WORLD_GAINS (0.998/1.082/0.932, recomputed here from the frame as 0.9977/1.0818/0.9317). THE PANEL IS NOT GOLD, and that is this material's main finding. Value-banded over the mesh at (0.24,0.755)-(0.66,0.890): balanced H 61.1 S 0.102 at V 0.25-0.35, H 114.2 S 0.068 at V 0.35-0.45, H 71.6 S 0.087 at V 0.45-0.55, H 75.4 S 0.046 at V 0.55-0.65, H 92.3 S 0.029 at V 0.65-0.80. Read RAW over the same region it gives H 336.7/254.8/298.1/282.6/271.6 at S 0.081/0.072/0.058/0.090/0.118. Both readings stay under S 0.12 at every band and they disagree about which side of neutral it sits, so the panel is a WHITE source with a cream lean, not a gold one; at 7x NEAREST magnification it resolves as a fine pale-grey and cream grille. Hue is taken from the balanced read (H 65) at the middle of its measured saturation (0.09), giving (1.000, 0.968, 0.910). LEVEL evidence for the energy: the panel's brightest band is balanced V 0.667 against the room's lit fin wall at V 0.259 (k-means dominant, 28.1% of (0.00,0.00)-(0.20,0.30)) — a ratio of 2.6.",
        extrapolated="emission_energy 2.0 and the unlit albedo. Energy: derived from that 2.6 ratio. A source only 2.6x the value of the surfaces it lights is a large, soft, low-intensity emitter, not a lamp — which is why 2.0 sits below materials.py's furn_shrine_lit (2.2) and light_deck_channel (3.5) despite this being the room's only light, and why flux-matching against a corridor strip was rejected: council_chamber.py's panel is 12.0 m of arc x 0.92 m = 11.1 m2, fifty-five times a pilaster strip's area, and matching that strip's flux would put the energy at 0.11 and black the room out. Albedo 0.42: the perforated sheet's own metal when unlit, set at the frame's paint-system level (fin wall lit() 0.404) and not brighter, because a sheet that is roughly half open reads darker than the solid metal it is punched from. Overturned by a frame showing this bench with the panel off."))

        # The honest gap here is that the fan is TWO things and the geometry is
        # one group: 13 white blades with saturated blue wedges between them,
        # measured at (0.29,0.490)-(0.37,0.550) as balanced rgb
        # 0.333/0.395/0.486, H 216 S 0.316 — the only saturated element
        # anywhere on the bench. council_chamber.py tags all thirteen quads
        # council_speak_fan, so a material cannot express both and the blue
        # belongs to a decal in a later layer. I have taken the majority
        # surface, the white blade, and recorded the blue reading here so the
        # next pass does not have to re-derive it. At luminance 0.533 this is
        # also the palest non-emissive surface I am proposing anywhere, which
        # is correct: the frame says it is.
    a(Material(
        "council_speak_inlay", "Speaking-Position Inlay — the white fan laid into the bench top",
        albedo=(0.524, 0.535, 0.540), roughness=0.32, metallic=0,
        specular=0.55,
        binds=("council_speak_fan",), scenes=("interior",),
        source="reference/05-sector-green/council chambers.webp (authority 1), balanced (0.998/1.082/0.932). The fan's white blades at (0.44,0.417)-(0.59,0.483) read balanced rgb 0.618/0.641/0.669, H 213 S 0.075, V 0.669, luminance 0.638 — the brightest diffuse surface anywhere in the room, 2.6x the lit fin wall (V 0.259) and 1.4x the bench slab it lies on (luminance 0.457 at (0.44,0.583)-(0.59,0.623)). LEVEL: this frame's transform for an up-facing pale surface is already fixed by a reviewed material — materials.py's shell_deck_stone maps this frame's floor patch (0.900,0.860)-(0.990,0.990) at balanced V 0.496 onto luminance 0.419, i.e. x0.845 — so 0.638 x 0.845 = 0.539. SATURATION is cut from the measured 0.075 to 0.030 for the reason shell_deck_stone's own note gives for cutting 0.146 to 0.059: this chamber is keyed cool and its walls are cool in the same frame (fin wall H 190-206), so one frame with a single-temperature key cannot separate a cool surface from a cool light.",
        extrapolated="Roughness 0.32 and specular 0.55, and the decision to make this one material rather than two. Gloss: at 2x magnification the fan carries a specular sheen the speckled slab beside it does not, so it is smoother than the slab's casework (0.45) without going near the 0.15 mirror floor. The saturation cut is declared above. Overturned by any second frame of this bench under a warm key."))

        # shell_deck_stone was derived from THIS floor in THIS frame — its own
        # source string says so and its note says 'This is a ceremonial floor,
        # NOT a chapel floor.' So the right structure is not three new
        # materials but one reuse plus two siblings: council_floor_1 takes
        # shell_deck_stone unchanged as the pale tile, and these two carry the
        # mid and dark shades. Folding all three into one material would have
        # satisfied coverage and killed the mosaic, which council_chamber.py's
        # own self-test asserts must have more than one shade.
    a(Material(
        "council_floor_mid", "Council Mosaic — mid tile",
        albedo=(0.344, 0.346, 0.330), roughness=0.2, metallic=0,
        specular=0.66, texture="deck_plate", uv_scale=1.0 / 3.2,
        binds=("council_floor_0",), scenes=("interior",),
        source="reference/05-sector-green/council chambers.webp (authority 1), balanced (0.998/1.082/0.932). The mosaic was sampled on the only two strips of floor the ambassador does not stand on, (0.725,0.640)-(0.762,0.990) and (0.950,0.560)-(0.999,0.990), pooled and 4-clustered: 32.4% rgb 0.438/0.486/0.470 (H 159 S 0.100, luminance 0.475), 23.5% rgb 0.406/0.412/0.365 (H 67 S 0.112, luminance 0.407), 31.6% rgb 0.319/0.309/0.292 (H 38 S 0.083, luminance 0.310), 12.5% rgb 0.233/0.225/0.218 (luminance 0.226). That is a three-shade ladder, which is what council_chamber.py's mosaic_floor() emits. LEVEL through the same x0.845 transform materials.py's shell_deck_stone already establishes on this frame's floor (balanced V 0.496 -> luminance 0.419): the 23.5% cluster becomes 0.344. SATURATION cut from the measured 0.112 to 0.045, exactly as shell_deck_stone cut 0.146 to 0.059 and for the same stated reason — a single-temperature key cannot separate a tinted floor from a tinted light. Roughness, specular and the 3.2 m deck_plate repeat are reproduced from shell_deck_stone unchanged so the three tiles read as one floor.",
        extrapolated="The saturation cut (declared above) and the assignment of shade index to cluster. council_chamber.py picks a tile's shade from a blake2b hash, so which of 0/1/2 lands on which polygon is arbitrary and only the ladder as a whole is meaningful; what is asserted is that the three together reproduce the measured spread of 0.262 / 0.344 / 0.419 luminance. Overturned by a wider or better-lit shot of this floor."))

        # The dark tile is what stops the mosaic reading as one flat slab:
        # 0.262 against 0.419 is a 1.6x ladder, which is what the frame shows
        # at magnification. It sits below materials.py's shell_deck_industrial
        # (0.365) but it is a polished ceremonial floor, not a plant deck, so
        # it keeps shell_deck_stone's roughness 0.20 and specular 0.66 — dark
        # and polished, not dark and matte.
    a(Material(
        "council_floor_dark", "Council Mosaic — dark tile",
        albedo=(0.265, 0.262, 0.256), roughness=0.2, metallic=0,
        specular=0.66, texture="deck_plate", uv_scale=1.0 / 3.2,
        binds=("council_floor_2",), scenes=("interior",),
        source="reference/05-sector-green/council chambers.webp (authority 1), balanced (0.998/1.082/0.932). Same pooled k-means over the two clean floor strips as council_floor_mid: the 31.6% cluster reads rgb 0.319/0.309/0.292, H 38 S 0.083, luminance 0.310. Through the x0.845 transform materials.py's shell_deck_stone establishes for this frame's floor, that is 0.262. Saturation cut from the measured 0.083 to 0.033, on shell_deck_stone's stated single-key argument. Roughness, specular and the 3.2 m deck_plate repeat reproduced from shell_deck_stone.",
        extrapolated="The saturation cut, and the risk that this cluster is contaminated: the left-hand strip runs beside the Centauri ambassador's warm costume, which is the likeliest source of its H 38 warm lean. That is the second reason the hue is carried at 40% strength rather than as measured, and it is why the shade is separated from its siblings by VALUE, which cannot be contaminated the same way. Overturned by a frame of this floor with nobody standing on it."))

        # A CORRECTION TO THE MODULE, and it is worth carrying: customs.py's
        # docstring describes 'a backlit ceiling grid above the screens —
        # yellow-green illuminated panels in a coffered lattice.' Measured, the
        # register is H 54.6-57.0 at every value band — an amber-gold, roughly
        # 60 degrees warmer than yellow-green. Six bands agree to within 2.4
        # degrees, so this is not a marginal call. It matters because this is
        # the ceiling of the player's first room and it sets the colour of the
        # light falling on the arrival crowd.
    a(Material(
        "light_ceiling_grid", "Arrival Hall Ceiling Grid — the backlit amber coffer",
        albedo=(0.480, 0.470, 0.380), roughness=0.35, metallic=0,
        specular=0.22,
        emission=(1.000, 0.987, 0.734), emission_energy=0.8,
        binds=("customs_ceiling_lamp",), scenes=("interior",),
        source="reference/11-props-and-technology/babylon 5 welcome sign, instructions, and hub.jpg (authority 1), balanced with gains 1.046/1.065/0.905 — the same gains materials.py's device_screen_glass already cites for this frame, recomputed here from the frame as 1.0455/1.0652/0.9052 and reproducing them exactly. Value-banded over the grid at (0.310,0.010)-(0.570,0.160): H 60.1 S 0.090 at V 0.06-0.10 (n=7013, the dark lattice between cells); then the lit cells, H 55.3 S 0.356 at V 0.10-0.16 (n=2539), H 54.6 S 0.357 at V 0.16-0.24 (n=2175), H 56.7 S 0.302 at V 0.24-0.34 (n=1760), H 57.0 S 0.267 at V 0.34-0.50 (n=1284), H 56.9 S 0.247 at V 0.50-0.75 (n=212). Hue is CONSTANT at H 54.6-57.0 across an 8.5x range of value while saturation falls monotonically — a lit panel blowing toward white with its register intact. Normalised from the V 0.34-0.50 band (rgb 0.399/0.394/0.293) that is (1.000, 0.987, 0.734).",
        extrapolated="emission_energy 0.8 and the diffuser albedo. Energy: the frame ranks its own three source families and this one is last — measured balanced peaks are 0.99 for the screens, 0.82 for the vertical wall strips and 0.55 for the ceiling grid — so it is ambient decoration rather than a task light. IT WAS 2.6, ON THE ARGUMENT THAT 2.6 SITS BELOW light_deck_channel'S 3.5, AND THAT ARGUMENT WAS BLIND TO AREA. The first engine frame of this room, session 3p, came back with a solid blown-white slab where the ceiling should be: customs.hall() coffers 64% of a 34 x 17 m soffit, so this one material covers roughly 370 m2 against light_pilaster_strip's ~0.2 m2 — a factor of 1,800 the ladder says nothing about. materials.bay_floodlight already makes the same argument in the other direction ('the fitting is far larger ... so at equal energy this delivers roughly fifteen times the flux'); nobody had made it downward. The frame's own numbers say the same: 7,013 px of dark lattice at V 0.06-0.10, and only 212 px of 14,983 — 1.4% — above V 0.50, with 78% of the lit cells below V 0.34. That is a dim ceiling. At 0.8 the coffer reads as an amber lattice with dark ribs and the whole-frame median falls from 5.39x its reference to 2.48x; taking it further to 0.3 moves the median by 3.6%, so 0.8 is where the fitting stops dominating and below it the change is only to the ceiling's own look. It sits below light_indicator_red's 0.9, which is correct and is the point: PER UNIT AREA a decorative ceiling is dimmer than a status lamp. Albedo 0.48/0.47/0.38 carries a hint of the emission hue, following light_downlight's pattern of an albedo tinted toward its own output; it is otherwise unsourced because the grid is never seen unlit. Overturned by any frame of this ceiling with the panels off."))

    # =====================================================================
    # LAYER 3 -- PLANT, ALIEN SECTOR, HOSPITALITY, QUARTERS
    # =====================================================================
    # 46 groups, of which FORTY were surfaces this library already had:
    # a cabin floor is the kit's deck panel, a bunk and a bar stool are the
    # same soft goods, a grab bar and a plant handrail are one extrusion.
    # Those were rebound above rather than re-authored, which is what keeps
    # the station one station.
    #
    # SIX are genuinely new, and all six are in Doug's Dugout or an airlock.
    #
    # THE DUGOUT CANNOT BE MEASURED FOR ALBEDO -- see NEGATIVE_RESULTS. Its
    # grey-world balance returns nonsense (a wall at S 1.000) because the room
    # is lit entirely by isolated pendant cones with near-zero ambient, so its
    # mid-tone population is not neutral. Every REFLECTANCE below is therefore
    # a declared extrapolation and says so.
    #
    # EMISSION is the exception, and the reason is worth stating rather than
    # assuming: balancing recovers a reflectance by assuming the illuminant is
    # neutral. An emitter's own colour is not a reflectance and does not depend
    # on that assumption -- it is the illuminant. So the frame is unusable for
    # what the walls are and usable for what the lamps are, which is the
    # opposite of the usual case and is why it is spelled out here.

    a(Material(
        "bar_pendant_shade", "Pendant Shade -- shallow polished cone over each table",
        albedo=(0.520, 0.512, 0.498), roughness=0.22, metallic=0.55,
        specular=0.55,
        binds=("bar_pendant_shade",), scenes=("interior",),
        source="Doug's Dugout.webp establishes the FORM and the count -- shallow "
               "polished shades on slim stems, one per table, hung below "
               "standing eye height so they pool rather than light the room. "
               "It does NOT establish the reflectance: see NEGATIVE_RESULTS.",
        note="The lighting design is the room, and hospitality.py asserts the "
             "one-pendant-per-table relation rather than trusting it.",
        extrapolated="Every number. A shade read as bright in frame is bright "
                     "because it is close to a lamp, not because it is white, "
                     "so it is put at roughly the wall's value with a low "
                     "roughness and a metal component -- a spun shade, not a "
                     "painted one. Overturned by any second frame of a station "
                     "bar under ordinary lighting."))

    a(Material(
        "bar_pendant_stem", "Pendant Stem -- slim dark drop to the soffit",
        albedo=(0.075, 0.074, 0.072), roughness=0.42, metallic=0.35,
        specular=0.35,
        binds=("bar_pendant_stem",), scenes=("interior",),
        source="Doug's Dugout.webp: the stems read as near-black lines against "
               "a dark soffit even directly above a lit shade, which is a "
               "statement about their value that survives the frame's broken "
               "balance because it is a comparison inside one exposure.",
        extrapolated="The exact value, roughness and metallic. Dark enough to "
                     "disappear is the requirement; 0.075 is the darkest thing "
                     "in this library after viewport_glazing."))

    a(Material(
        "bar_pendant_lamp", "Pendant Lamp -- the source inside the shade",
        albedo=(0.090, 0.088, 0.084), roughness=0.30, metallic=0.0,
        specular=0.25,
        emission=(1.000, 0.612, 0.353), emission_energy=9.0,
        binds=("bar_pendant_lamp", "light_pendant"), scenes=("interior",),
        source="ACCENTS['warm_practical'], which is the register measured "
               "across the balanced interiors at H 12-35. Doug's Dugout.webp "
               "corroborates the HUE without being balanced: the pools beneath "
               "the shades are the warmest thing in a frame whose only light is "
               "these lamps, and an emitter's colour is the illuminant rather "
               "than a reflectance, so it does not depend on the balance the "
               "frame cannot support.",
        extrapolated="The energy. 9.0 matches light_downlight, the other "
                     "fitting in this library that is the sole source in its "
                     "room.",
        note=("`light_pendant` is rooms.py's hospitality fitting and it is "
              "this lamp, not a lookalike: docs/layer4-lighting/"
              "public_social.json measures `bar_pendant_lamp` at (1.000, "
              "0.554, 0.393) against this material's (1.000, 0.612, 0.353) "
              "from the same frame, and the mess hall, the Dark Star and the "
              "Casino are lit by the fitting Doug's Dugout was measured "
              "from.")))

    a(Material(
        "bar_cell_matrix", "Backlit Cell Matrix -- orange-red, twelve across",
        albedo=(0.110, 0.085, 0.070), roughness=0.35, metallic=0.0,
        specular=0.30,
        emission=(1.000, 0.330, 0.140), emission_energy=2.4,
        binds=("bar_cell_matrix",), scenes=("interior",),
        source="Doug's Dugout.webp, authority 1: an orange-red backlit cell "
               "matrix twelve cells across in a stepped irregular silhouette. "
               "The count is counted -- hospitality.MATRIX_CELLS_X = 12 -- and "
               "asserted there rather than chosen. Hue is an emitter's, so it "
               "survives the frame's balance failure.",
        extrapolated="The energy and the unlit cell's reflectance. Dimmer than "
                     "the pendants because it is a background fitting; if it "
                     "outshone them it would stop being a bar."))

    a(Material(
        "bar_dartboard", "Dartboard -- regulation board, dark ground",
        albedo=(0.115, 0.108, 0.098), roughness=0.72, metallic=0.0,
        specular=0.25,
        binds=("bar_dartboard",), scenes=("interior",),
        source="Doug's Dugout.webp shows a regulation 20-segment board. "
               "hospitality.py carries the real geometry -- DART_R_M 0.2255 "
               "for a 451 mm board, DART_SEQUENCE the regulation clockwise "
               "order, DART_RING_R the regulation radii -- and asserts the "
               "sequence's defining property, that high numbers neighbour low "
               "ones. A plausible ring of numbers is wrong in a way a player "
               "can catch.",
        note="One material for a board that is really four colours. The "
             "segments need their own groups before they can carry them, and "
             "that is layer 5 rather than a value to invent here.",
        extrapolated="The value. A dartboard reads dark at the scale it "
                     "occupies in this room; the cream and red segments are "
                     "geometry this module does not yet emit separately."))

    a(Material(
        "alien_status_lamp", "Airlock Status Lamp -- green, one per lock",
        albedo=(0.085, 0.095, 0.085), roughness=0.28, metallic=0.0,
        specular=0.30,
        emission=(0.220, 1.000, 0.380), emission_energy=5.0,
        binds=("alien_status_lamp",), scenes=("interior",),
        source="alien_sector.py builds one green status lamp per lock -- the "
               "state indicator on an atmosphere seal. NO FRAME SHOWS A LOCK, "
               "and that has not changed. What the layer-4 pass did find is "
               "that the register exists in this quarter: "
               "reference/05-sector-green/corridor in alien sector.webp "
               "(authority 1) carries small green points low on the right, "
               "read raw at (0.643,0.500)-(0.668,0.552) as linear (0.878, "
               "1.000, 0.739) H 88 and at (0.603,0.437)-(0.622,0.462) as "
               "(0.806, 1.000, 0.827) H 126, both dim (V max 0.267 and 0.596) "
               "and both a few pixels across. 00-INDEX.md names them "
               "'green point lights low on the right'.",
        note="Green because the lamp means the seal holds. It is the only "
             "saturated green in the interior library and it is a fitting, not "
             "a surface, so the neutrality rule does not reach it.",
        extrapolated="Every number, and the choice of green itself. What "
                     "constrains it: it must read at a glance from down a "
                     "gallery, it must not be confusable with the warm "
                     "practical register, and it must be dimmer than a "
                     "pendant, which is task lighting. THE SATURATION IS NOT "
                     "CHANGED to match the frame's H 88-126 at S 0.19-0.26, "
                     "and the reason is that those blobs are 20-40 px on an "
                     "amber field: a saturated green core blurred against "
                     "H 39 surroundings reads exactly as a desaturated "
                     "yellow-green, which is what they read as. Overturned by "
                     "a frame that resolves one of these lamps."))

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
    # The exterior components. They were absent from this list for as long as
    # they had no materials, which is backwards -- the list exists to catch a
    # group with no material, so leaving the unbound ones out of it is the one
    # case it cannot report. `forward_comms_plate` and the three `*_frame`
    # groups are here for that reason as much as for coverage.
    + ("cobra_bay", "cobra_bay_well", "hazard_stripe_cobra",
       "cobra_beacon_red", "cobra_marker_white", "forward_comms_plate",
       "observation_dome", "observation_dome_frame",
       "observation_rotunda", "observation_rotunda_frame",
       "docking_port", "docking_port_frame")
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
               "drum": os.path.join(ROOT, "godot", "scenes", "drum.tscn"),
               # The interior scene has the most materials of the three and was
               # the last to get a file. Adding it here is what makes its 265
               # rules reach the engine at all.
               "interior": os.path.join(ROOT, "godot", "scenes",
                                        "interior.tscn")}


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
# The interior figure is asserted against the WORST SINGLE VIEW, not against
# the library, because a material costs a draw call only where it is drawn.
# See the gate in `_selftest`; the distinction only started mattering when
# "interior" stopped meaning "the corridor kit" and started meaning every
# surface across 118 locations.
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
# `test_materials_layer3.py` and `apply_proposals.py` joined the list when
# BESPOKE_SCENE landed: its keys are MODULE names -- "drum_ground", "core_tube",
# "tram" -- and the scan reads them as group literals. Same reason as
# directory.py's place keys and rooms.py's prop types. A file that talks ABOUT
# the generators is not a generator.
NOT_GENERATORS = {"materials.py", "directory.py", "rooms.py",
                  "test_materials_layer3.py", "apply_proposals.py"}

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
    # EVERY COMMITTED TEXTURE MUST ACTUALLY DECODE, and one of them did not.
    # `deck_stud_orm.png` was in the repository at 196,673 bytes against the
    # 613,211 it regenerates to -- truncated, and PIL refuses to load it. It is
    # the occlusion/roughness/metallic map for `kit_deck`, which is the deck of
    # every corridor on the station and the most-seen surface in the project.
    #
    # NOTHING WOULD HAVE SAID SO. The material referencing it resolves, its
    # size is declared, its slope is declared, and the VRAM budget is computed
    # from TEX_SIZE rather than from the file, so all four gates above pass on
    # a file that is half missing. It would have reached the engine as a failed
    # import or as garbage roughness on every deck -- the kind of defect that
    # reads as "the material is wrong" three sessions later.
    #
    # Cheap to check and it belongs here rather than in CI, because this is the
    # file that writes them: `--export` regenerates every texture and the
    # output is byte-deterministic (verified by exporting twice and comparing).
    # EVERY FILE ON DISK, not every name in TEX_SIZE, and the difference is why
    # the first version of this gate was useless: TEX_SIZE is keyed by SHEET
    # (`deck_stud`) and the files are per MAP (`deck_stud_albedo.png`,
    # `deck_stud_orm.png`, `deck_stud_normal.png`). Iterating the declared
    # names looked at eight paths, none of which exists, and passed. Reading
    # the directory asks about the artefacts that actually ship.
    from PIL import Image as _PILImage                      # noqa: PLC0415
    truncated = []
    for fn in sorted(os.listdir(TEXTURE_DIR)
                     if os.path.isdir(TEXTURE_DIR) else []):
        if not fn.endswith(".png"):
            continue
        path = os.path.join(TEXTURE_DIR, fn)
        try:
            with _PILImage.open(path) as im:
                im.load()               # header alone decodes on a truncated
                sheet = fn[:-4]         # file; the pixels are the test
                for suffix in ("_albedo", "_orm", "_normal"):
                    if sheet.endswith(suffix):
                        sheet = sheet[:-len(suffix)]
                        break
                want = TEX_SIZE.get(sheet)
                if want and im.size != (want, want):
                    truncated.append(f"{fn} is {im.size}, declared {want}")
        except Exception as exc:                               # noqa: BLE001
            truncated.append(f"{fn}: {type(exc).__name__} {exc}")
    check("every exported texture decodes at its declared size",
          not truncated, str(truncated[:3]))

    # AND EVERY .tres ON DISK MUST BE WHAT THE LIBRARY WOULD WRITE. This is the
    # scene-rules defect again, one file down. Material RULES used to be
    # emitted to a .txt for a human to paste into a .tscn, and the first
    # material added after that exported cleanly, passed every assertion and
    # never reached the render; `patch_scene_rules` and its gate exist because
    # of it. The .tres files are the same shape of hole and had no gate: three
    # emission energies were re-tuned against engine frames this session, and
    # two of the .tres the ENGINE ACTUALLY READS still carried the old values
    # (light_arrival_strip at 5 against the library's 3, light_deck_grating at
    # 3.5 against 1.2) because nobody had re-run `--export`.
    #
    # Skipped rather than failed on a bare checkout: the files are generated,
    # so their absence means "not exported yet" and not "wrong".
    drifted = []
    for m in MATERIALS:
        path = os.path.join(MATERIAL_DIR, f"{m.name}.tres")
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            if fh.read() != (shader_tres(m) if m.shader else tres(m)):
                drifted.append(m.name)
    check("every exported .tres is what the library would write today",
          not drifted,
          f"{len(drifted)} stale, run --export: {drifted[:4]}")

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
    # -- DRAW CALLS ARE PAID PER MATERIAL *DRAWN*, NOT PER MATERIAL OWNED ---
    # This gate counted len(scene_materials(scene)) and failed the moment the
    # zocalo landed: 80 interior materials against a budget of 64. Raising the
    # budget would have been picking the convenient reading. Measuring showed
    # the gate was asking the wrong question.
    #
    # "interior" meant the corridor kit when the budget was written, so the
    # library and a frame were the same set. It now means every interior
    # surface across 118 locations, and no view draws them all: the worst
    # single procedural room draws NINE materials, the mean is 7.4, and a
    # corridor section draws nine. A material only costs a draw call where it
    # is on screen.
    #
    # So the budget is asserted against the worst single view, and the library
    # size is reported next to it as what it is -- an inventory.
    try:
        import rooms as _rooms                                 # noqa: PLC0415
        import interior_kit as _kit                            # noqa: PLC0415
        _s, _p = _it.load()
        views = []
        for _pl in _rooms.unbuilt(_s, _p):
            _v, _t, _g = _rooms.build(_s, _p, _pl)
            views.append((_pl["key"], len({resolve_any(n, "interior").name
                                           for n, _a, _b in _g
                                           if resolve_any(n, "interior")})))
        _kv, _kt = _kit.corridor_section(21.6)
        views.append(("corridor_section",
                      len({resolve_any(n, "interior").name
                           for n, _a, _b in _kit.tagged_spans(_kt)
                           if resolve_any(n, "interior")})))
    except Exception as exc:                                   # noqa: BLE001
        check("the per-view material count is measurable", False, str(exc))
        views = []
    if views:
        worst_key, worst_n = max(views, key=lambda x: x[1])
        check("no single interior view exceeds the draw-call budget",
              worst_n <= DRAW_CALL_BUDGET["interior"],
              f"{worst_key} draws {worst_n} > {DRAW_CALL_BUDGET['interior']}")
        # A floor as well as a ceiling: if the worst view ever drops to one or
        # two materials, something has stopped resolving and this gate would
        # go green for the wrong reason.
        check("the worst interior view draws a plausible number of materials",
              worst_n >= 5, f"{worst_key} draws only {worst_n}")
        print(f"  worst interior view: {worst_key} at {worst_n} materials "
              f"(budget {DRAW_CALL_BUDGET['interior']}); library holds "
              f"{len(scene_materials('interior'))}")
    for scene in ("exterior", "drum"):
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
