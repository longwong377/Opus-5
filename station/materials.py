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
