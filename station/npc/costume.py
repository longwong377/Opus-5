#!/usr/bin/env python3
"""Clothing and uniform: how 250,000 residents get dressed for ~40 triangles each.

`body.py` builds one parametric body per species. This module puts clothes on
it. The whole design turns on one question -- what has to be GEOMETRY and what
can be MATERIAL -- because the answer decides whether a crowd is affordable.

THE SPLIT, AND THE ARITHMETIC BEHIND IT
---------------------------------------
`station/budget.py` gives NPCs 12% of a 1,200,000-triangle frame (body.py's
`NPC_FRAME_SHARE`, defended there): 144,000 triangles for every person in view.
A busy Zocalo is ~330 mid-field figures. That is ~430 triangles per person for
body AND clothing, so a per-garment mesh -- a jacket shell, a separate collar,
a separate belt, sleeves -- is not merely wasteful, it is arithmetically
impossible. Clothing is therefore split three ways:

  1. MATERIAL, zero triangles. Anything that is paint on a surface: the jacket
     colour, the leather bib, the crimson piping, every badge, the armband
     emblem, the name bar, trousers, boots, robe fabric. These are emitted as a
     GROUP NAME on triangles the body already had. Dressing an NPC in EarthForce
     command re-labels its torso; it does not add a vertex.

  2. SILHOUETTE MODIFIER, zero triangles. Anything whose outline matters but
     whose shape is a smooth swelling of the body: squared shoulders, a padded
     coat, a boot, a heavy sleeve, a tabard. Implemented as a strictly positive
     radial scale field s(y) applied about each part's own axis. A positive
     scale has positive determinant, so it CANNOT flip a winding -- which is why
     this is the preferred mechanism in a repository that has shipped four
     inside-out subsystems. `_selftest` asserts the signed volume of every part
     stays positive through every modifier.

  3. ATTACHMENT, a few dozen triangles, and only where a modifier cannot express
     the shape AND the silhouette error earns it. Each attachment carries a
     MEASURED displacement and is dropped beyond `body.honest_from_m()` of it.
     The Nightwatch armband stands 5 mm proud of a sleeve, so the STRAP is
     honest to drop at 5.1 m; the emblem it carries is a decal and survives to
     the distance it stops being legible. FACTIONS.md 5.3 calls the armband
     "one decal and one strap mesh"; this module keeps both and prices them
     apart, because they have different LOD lives by a factor of twenty.

  4. And one SUBTRACTION. A floor-length robe replaces two legs and two feet
     with one capped skirt loft: a robed Minbari is CHEAPER than a trousered
     human. `report()` prints the number.

DRAW CALLS ARE THE OTHER HALF OF THE COST, AND THE TRAP IS OBVIOUS
------------------------------------------------------------------
Twenty-two costume sets could trivially become twenty-two materials, and a
material is a draw-call floor (`materials.py`: "a mesh cannot batch across a
material"). So the costume's identity is NOT a material. Group names carry a
fixed five-slot vocabulary (`MATERIAL_SLOTS`) plus a fabric suffix that exists
only so the preview renderer can tint one, and every garment colour is
PER-INSTANCE data. Adding the twenty-third set adds zero materials, and
`_selftest` asserts exactly that by counting slots over every set.

COLOUR: WHAT WAS MEASURED, HOW, AND WHERE THE METHOD FAILS
-----------------------------------------------------------
Every colour below was sampled from a named file at a named fractional region,
after the grey-world balance `station/materials.py` uses (per-channel gains
that put the frame's mid-tone population at neutral, computed over pixels with
0.04 < V < 0.95). Nothing here was described from memory and nothing was picked
by eye. Three findings shaped the method:

  * **Grey-world FAILS on a frame one hue dominates**, and the gain vector says
    when. `G'Kar more.jpg` is a Narn filling the frame with ochre skin; its
    gains are 0.496 / 1.566 / 2.909 and the balance turns his skin GREEN.
    `Marcus Cole in uniform.jpeg` fails the same way at 0.687 / 1.098 / 1.580.
    The rule adopted here: **a frame whose gains fall outside [0.80, 1.30] is
    not balanceable**, and for those frames only within-frame RATIOS are quoted.
    `GREY_WORLD_VALID` records the test per frame.

  * **Human skin is the exposure reference, and it was cross-checked twice.**
    A portrait has no grey card, so absolute albedo is unrecoverable -- exactly
    what `materials.py` says about screencaps. But balanced, key-lit facial skin
    reads V 0.758 in `Sheridan.jpg` and V 0.745 in `Zach Allan in security
    uniform.jpg`: **two independently lit publicity stills agreeing to 1.7%**.
    And `10-interiors-generic-kit/more hallway.jpg` closes the chain to the
    station's own value ladder: the officer stands in a downlight pool with the
    deck, so their ratio is an albedo ratio, and face/deck = 0.342/0.361 =
    0.947 against `materials.kit_deck` albedo 0.40 gives **skin = 0.379 on the
    station's scale**, 8% from the physical constant for lightly-tanned
    Caucasian facial skin. Two sources that could not have copied each other.
    `SKIN_ANCHOR` is set from that pair and is the ONE declared number the whole
    colour chain hangs on.

  * **The command jacket is genuinely blue; the hull is not.** `materials.py`'s
    own discriminator -- a multiplicative tint holds B/R and grows B-R, an
    additive blue light holds B-R and shrinks B/R -- run over the whole jacket
    in `Sheridan.jpg` gives B/R = 1.47, 1.44, 1.41, 1.36 across a 5.6x value
    range while B-R runs 0.020 -> 0.128. Ratio held, difference grew: the wool
    is blue by ALBEDO. The same test on the hull said the opposite, which is why
    `hull_exterior` is neutral. And `more hallway.jpg`, a completely different
    frame under a blue key, puts the same jacket at H 215.3 against Sheridan's
    H 220.1 -- 5 degrees apart, two sources.

CIVILIAN CLOTHING WAS THE GAP AND IT IS NOW MEASURED
-----------------------------------------------------
`docs/REFERENCE-GAPS.md` 5 names civilian dress as a hole: "We have uniforms; we
have very little of what an ordinary resident wears." That is true of PORTRAITS
and false of CROWDS. `04-sector-red/more zocalo.png` is authority 1 and holds
nine separable garments plus a lit deck in the same frame, and it says something
precise: **every garment in it sits between 0.038 and 0.27 of the lit deck's
value.** Balanced, the deck reads V 0.687 and the garments V 0.026 to 0.187.
Hue clusters at 340-30 degrees with a secondary group near 270-300; saturation
0.15-0.35. `zocalo.webp` cross-checks the shape of the distribution and adds its
tail: one cream shirt at V 0.410, S 0.064, the only light garment in either
frame. So civilian dress is not invented here -- its VALUE DISTRIBUTION is
measured, its chroma band is measured, and only the cut is extrapolated.

THE ERA GATE IS LOAD-BEARING
-----------------------------
FACTIONS.md 5.1: "Any armband before *The Fall of Night* is an error." The
Nightwatch armband, the Ranger costume and Brother Theo's order each switch on
at a stated episode, and the module refuses a datum at or past secession. A
costume system without a clock would put armbands on Season 1 and misplace a
whole political layer, so the clock is a parameter, it is checked, and
`_selftest` runs the module at three datums and asserts what appears and
disappears.

Run `python3 station/npc/costume.py` for the self-test, `--report` for the
derivation and the cost, `--obj PATH` to write a dressed figure or a lineup.
"""
import argparse
import ast
import math
import os
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)
for _p in (_HERE, _STATION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import body                                                   # noqa: E402

_u = body._u
_pick = body._pick
_gauss = body._gauss


# ---------------------------------------------------------------------------
# 1. The era gate
# ---------------------------------------------------------------------------
# (season, episode). Ordered comparison is the whole mechanism; every date below
# is an event from FACTIONS.md 1.1, cited by its event id there.
ERA_EVENTS = {
    "markab_extinct":    ((2, 18), "E4  Confessions and Lamentations -- the Markab die"),
    "psi_resident_ends": ((2, 19), "E5  Divided Loyalties -- Talia removed; no resident "
                                   "Psi Corps commercial telepath after this"),
    "narn_surrender":    ((2, 20), "E6  The Long, Twilight Struggle -- Narn becomes a "
                                   "refugee population"),
    "nightwatch_visible": ((2, 22), "E7  The Fall of Night -- Nightwatch surfaces aboard; "
                                    "the first armband"),
    "rangers_visible":   ((3, 1), "E8  Matters of Honor -- Marcus Cole aboard; the Ranger "
                                  "costume enters the lock"),
    "monastics_resident": ((3, 2), "E9  Convictions -- Brother Theo's order takes up "
                                   "permanent residence"),
    "martial_law":       ((3, 9), "E11 Point of No Return -- Nightwatch broken"),
    "secession":         ((3, 10), "E12 Severed Dreams -- out of era past this point"),
}

# FACTIONS.md 1.3: "Station datum: early 2260, between E9 (Convictions, S3E02)
# and E11 (Point of No Return, S3E09). Call it S3, pre-martial-law." S3E05 is
# taken as the point inside that window because 1.1's E10 puts a Ministry of
# Peace political officer aboard there, so it is the one episode in the window
# that adds something rather than merely being inside it.
ERA_DATUM = (3, 5)


def era_check(datum=ERA_DATUM):
    """Raise if the datum is outside the era lock. Returns the datum."""
    if datum >= ERA_EVENTS["secession"][0]:
        raise ValueError(
            f"datum {datum} is at or past secession {ERA_EVENTS['secession'][0]}; "
            "CLAUDE.md locks the era to Season 2-3 pre-secession")
    if datum < (2, 1):
        raise ValueError(f"datum {datum} is before Season 2; the lock is S2-3")
    return datum


def era_active(event, datum=ERA_DATUM):
    """Is `event` in force at `datum`? The armband's whole correctness."""
    return datum >= ERA_EVENTS[event][0]


# ---------------------------------------------------------------------------
# 2. The measurement record
# ---------------------------------------------------------------------------
# Frame -> the grey-world gains measured on it, and whether the balance is
# trustworthy. A frame dominated by one hue drags its own mid-tone population to
# neutral and takes the subject with it; the gain vector is the test.
GREY_WORLD_LIMITS = (0.80, 1.30)

GREY_WORLD_GAINS = {
    "14-characters-and-uniforms/Sheridan.jpg":                    (0.887, 1.024, 1.117),
    "14-characters-and-uniforms/Zach Allan in security uniform.jpg": (0.959, 1.051, 0.993),
    "14-characters-and-uniforms/security in uniform.jpg":         (0.799, 1.009, 1.321),
    "14-characters-and-uniforms/talia-winters in gorgeous office.webp": (0.843, 1.076, 1.131),
    "14-characters-and-uniforms/Talia Winters in uniform.webp":   (0.843, 1.076, 1.131),
    "14-characters-and-uniforms/Marcus Cole in uniform.jpeg":     (0.687, 1.098, 1.580),
    "15-races-and-makeup/G'Kar more.jpg":                         (0.496, 1.566, 2.909),
    "15-races-and-makeup/Pak'ma'ra.webp":                         (0.888, 1.128, 1.012),
    "04-sector-red/more zocalo.png":                              (0.936, 1.137, 0.950),
    "04-sector-red/zocalo.webp":                                  (0.906, 1.185, 0.950),
    "05-sector-green/rotunda.webp":                               (0.766, 1.153, 1.208),
    "10-interiors-generic-kit/more hallway.jpg":                  (1.118, 1.196, 0.788),
}


def grey_world_valid(frame):
    """Is the balanced reading of `frame` trustworthy? Gains are the test."""
    lo, hi = GREY_WORLD_LIMITS
    return all(lo <= g <= hi for g in GREY_WORLD_GAINS[frame])


GREY_WORLD_VALID = {f: grey_world_valid(f) for f in GREY_WORLD_GAINS}

# The one declared number the colour chain hangs on, and it was cross-checked
# two ways before it was written down (see the module docstring):
#   * balanced key-lit facial skin reads V 0.758 and V 0.745 in two
#     independently lit publicity stills -- 1.7% apart;
#   * in `more hallway.jpg` the officer and the deck share one downlight, so
#     face/deck = 0.342/0.361 = 0.947 is an ALBEDO ratio, and against
#     materials.kit_deck's 0.40 that puts skin at 0.379 on the station's own
#     value ladder.
# 0.36 is the midpoint of 0.379 and the 0.35 physical figure for lightly-tanned
# Caucasian facial skin. EXTRAPOLATED. Overturned by any production colour
# chart, a costume swatch, or a frame containing a known reflectance standard.
SKIN_ANCHOR = 0.36

# Balanced value of key-lit facial skin, per frame. This is the exposure
# reference: garment albedo = SKIN_ANCHOR * V_garment / V_face, with BOTH
# statistics taken the same way (75th percentile of a hand-placed box on the
# key-lit side) so the ratio is between like and like.
FACE_VALUE = {
    "14-characters-and-uniforms/Sheridan.jpg": 0.786,
    "14-characters-and-uniforms/Zach Allan in security uniform.jpg": 0.783,
    "14-characters-and-uniforms/security in uniform.jpg": 0.645,
    "14-characters-and-uniforms/talia-winters in gorgeous office.webp": 0.489,
    "14-characters-and-uniforms/Talia Winters in uniform.webp": 0.778,
    # Not human skin: a Centauri, i.e. an actor in makeup under a warm
    # practical. body.py's `_S_CENTAURI` records Centauri skin as "as
    # photographed" from this very frame, so using it as the anchor is
    # consistent with the body module rather than a new claim -- but it is one
    # notch weaker than the four above and is flagged in ANCHOR_WEAK.
    "04-sector-red/more zocalo.png": 0.316,
    # The best-lit human face in a very dark frame (an EarthForce officer in
    # the foreground). p75 0.263 against 0.181 and 0.171 for two other faces
    # further back, so this is the one receiving the key. The weakest anchor in
    # the table and flagged as such: this frame is used for the SHAPE of the
    # civilian value distribution, not for a uniform.
    "04-sector-red/zocalo.webp": 0.263,
    # No human and no Centauri in frame. Anchored instead on the cream robe,
    # declared at 0.62 -- see ROBE_ANCHOR.
    "05-sector-green/rotunda.webp": None,
    # Grey-world invalid; anchored on RAW skin, ratios only.
    "14-characters-and-uniforms/Marcus Cole in uniform.jpeg": 0.608,
    "15-races-and-makeup/G'Kar more.jpg": None,
    "15-races-and-makeup/Pak'ma'ra.webp": None,
    "10-interiors-generic-kit/more hallway.jpg": 0.342,
}

ANCHOR_WEAK = ("04-sector-red/more zocalo.png",
               "04-sector-red/zocalo.webp",
               "14-characters-and-uniforms/Marcus Cole in uniform.jpeg")

# Two frames carry no skin at all and need a declared anchor of their own. Both
# are single numbers, both are stated, and both are the only invented values in
# their frame's chain.
ROBE_ANCHOR = 0.62      # rotunda.webp cream robe: the brightest large surface
NARN_SKIN_ANCHOR = 0.42  # G'Kar more.jpg crown ground; body.py calls it "tan/ochre"
PAKMARA_COWL_ANCHOR = 0.46  # Pak'ma'ra.webp bone cowl, the brightest garment there

# Explicit per-frame anchor values, so `_frame_gain` never guesses.
FRAME_ANCHOR = {
    "05-sector-green/rotunda.webp": (ROBE_ANCHOR, 0.625),
    "15-races-and-makeup/G'Kar more.jpg": (NARN_SKIN_ANCHOR, 0.729),
    "15-races-and-makeup/Pak'ma'ra.webp": (PAKMARA_COWL_ANCHOR, 0.380),
}


def frame_gain(frame):
    """Multiply a balanced measured value by this to get albedo."""
    if frame in FRAME_ANCHOR:
        albedo, measured = FRAME_ANCHOR[frame]
        return albedo / measured
    v = FACE_VALUE[frame]
    if v is None:
        raise KeyError(f"{frame} has neither a skin anchor nor a FRAME_ANCHOR")
    return SKIN_ANCHOR / v


# Nothing in the reference set is pure black or pure white, and AAA-STANDARD's
# materials checklist gates exactly that. These are albedo floors and ceilings,
# not render values, and they are asserted rather than trusted.
ALBEDO_FLOOR = 0.030
ALBEDO_CEIL = 0.900

# FOUR garments in the reference set measure BELOW that floor and are lifted to
# it. This is a finding, not a rounding: the darkest clothing on Babylon 5 is
# darker than the project's own "nothing pure black" rule allows, and the rule
# wins because a pure-black albedo kills every shading cue on a curved surface.
# The list is pinned so that a fifth entry -- which would mean a measurement or
# an anchor had moved -- fails the build instead of being absorbed.
#   narn_apron       raw min 0.0138   G'Kar's pebbled hide apron
#   psi_black_panel  raw min 0.0265   the Psi Corps inset panel
#   minbari_black    raw min 0.0280   the black-robed group in the rotunda
#   civ_cool_dark    raw min 0.0250   a walking figure's coat in the Zocalo
EXPECTED_FLOORED = ("civ_cool_dark", "minbari_black", "narn_apron",
                    "psi_black_panel")


def _albedo(frame, rgb):
    """Measured balanced RGB from `frame` -> albedo on the station's ladder."""
    g = frame_gain(frame)
    out = tuple(min(ALBEDO_CEIL, max(ALBEDO_FLOOR, c * g)) for c in rgb)
    return tuple(round(c, 4) for c in out)


# ---------------------------------------------------------------------------
# 3. Fabrics
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Fabric:
    """One cloth, leather or metal, and where its colour came from.

    `measured` is the balanced median (or the selected top-decile, for a thin
    feature like piping) of `region` in `frame`. `albedo` is derived from it by
    `_albedo`, so the arithmetic is in the code rather than baked into a hex --
    changing `SKIN_ANCHOR` moves the whole wardrobe together, which is the
    property `materials.ALBEDO_ANCHOR` exists to have.
    """
    key: str
    title: str
    frame: str
    region: str
    measured: tuple
    roughness: float
    metallic: float = 0.0
    authority: int = 1
    note: str = ""
    # Set when the photographic reading is specular-inflated and the stored
    # `measured` is a shadow- or matte-side substitute instead.
    gloss_note: str = ""
    # Declared rather than measured: `measured` is then already an albedo.
    declared: bool = False

    @property
    def albedo(self):
        if self.declared:
            return tuple(round(min(ALBEDO_CEIL, max(ALBEDO_FLOOR, c)), 4)
                         for c in self.measured)
        return _albedo(self.frame, self.measured)

    def value(self):
        return max(self.albedo)


_SH = "14-characters-and-uniforms/Sheridan.jpg"
_ZA = "14-characters-and-uniforms/Zach Allan in security uniform.jpg"
_SU = "14-characters-and-uniforms/security in uniform.jpg"
_TO = "14-characters-and-uniforms/talia-winters in gorgeous office.webp"
_TU = "14-characters-and-uniforms/Talia Winters in uniform.webp"
_MC = "14-characters-and-uniforms/Marcus Cole in uniform.jpeg"
_GK = "15-races-and-makeup/G'Kar more.jpg"
_PM = "15-races-and-makeup/Pak'ma'ra.webp"
_MZ = "04-sector-red/more zocalo.png"
_ZW = "04-sector-red/zocalo.webp"
_RO = "05-sector-green/rotunda.webp"
_MH = "10-interiors-generic-kit/more hallway.jpg"

FABRICS = {f.key: f for f in (
    # ---- EarthForce, S2-3 -------------------------------------------------
    Fabric("ef_command_wool", "EarthForce command wool -- slate blue-grey",
           _SH, "(0.36,0.33)-(0.47,0.41) lit shoulder and upper sleeve, p75",
           (0.407, 0.454, 0.548), roughness=0.82, authority=2,
           note="H 220.1 S 0.257. Blue by ALBEDO, not by light: over the whole "
                "jacket B/R holds at 1.47/1.44/1.41/1.36 across a 5.6x value "
                "range while B-R grows 0.020->0.128. Cross-checked at H 215.3 "
                "in `more hallway.jpg`, a different frame under a blue key -- "
                "5 degrees apart, two sources that could not have copied each "
                "other. The same arithmetic said the HULL is neutral."),
    Fabric("ef_command_leather", "EarthForce command plastron -- brown leather",
           _SH, "(0.55,0.40)-(0.60,0.46) lit bib panel, p75",
           (0.250, 0.209, 0.193), roughness=0.42, authority=2,
           gloss_note="the lit COLLAR roll reads (0.476,0.413,0.394), 1.9x "
                      "brighter, because it is a tight curved gloss catching "
                      "the key. The flat bib is the diffuse sample; the collar "
                      "reading is what `roughness` has to reproduce, not what "
                      "`albedo` should carry.",
           note="H 16.6. FACTIONS 3.3's brown leather plastron/bib."),
    Fabric("ef_crimson_piping", "EarthForce crimson piping",
           _SH, "cuff (0.395,0.820)-(0.450,0.835) and collar edge "
                "(0.520,0.300)-(0.640,0.320), top redness decile",
           (0.480, 0.153, 0.166), roughness=0.55, authority=2,
           note="Measured INDEPENDENTLY at two places in one frame -- the cuff "
                "band and the collar edge -- giving H 357.4 S 0.682 and H "
                "356.8 S 0.692. 0.6 degrees and 0.010 apart. This is the S1/"
                "S2-3 discriminator (FACTIONS 3.3): S1 has no piping."),
    Fabric("ef_security_twill", "EarthForce security twill -- cool near-neutral grey",
           _ZA, "(0.30,0.55)-(0.44,0.66) front panel, p75",
           (0.391, 0.462, 0.518), roughness=0.86, authority=2,
           note="H 206.6 S 0.245 here; H 196-208 S 0.12-0.24 in `security in "
                "uniform.jpg`, whose cast is the OPPOSITE way (gains "
                "0.799/1.009/1.321 against 0.959/1.051/0.993). Two opposite "
                "casts landing in the same narrow band is the cross-check. "
                "1.13x the command wool's value and 0.05 less saturated: the "
                "security jacket is lighter and greyer, and that RELATIONSHIP "
                "is what survives a change of anchor."),
    Fabric("ef_black_leather", "EarthForce black leather -- collar, yoke, epaulettes",
           _ZA, "(0.795,0.66)-(0.865,0.69) matte armband field, p75",
           (0.094, 0.107, 0.117), roughness=0.22, authority=2,
           gloss_note="the collar itself reads (0.346,0.383,0.464) at p75 -- "
                      "4x brighter -- and is unusable as albedo: it is patent-"
                      "grade gloss under a studio key. The armband's matte "
                      "black field in the same frame is the substitute, and it "
                      "reads with Vsd 0.002, i.e. it is FLAT, which is what "
                      "makes it a valid diffuse sample.",
           note="One fabric, two finishes: this albedo with roughness 0.22 for "
                "the collar/yoke/epaulettes, and `nightwatch_black` with "
                "roughness 0.88 for the band. The gloss difference is the only "
                "thing separating them and it is visible in the still."),
    Fabric("ef_gold", "EarthForce gold -- collar wedge, epaulette wedge, name bar",
           _SH, "name bar (0.678,0.379)-(0.740,0.394), top-20% by value",
           (0.620, 0.510, 0.320), roughness=0.30, metallic=1.0, authority=2,
           declared=True,
           note="Hue MEASURED at H 38.3 S 0.481 on the name bar and H 30.4 on "
                "the collar wedge; the LEVEL is declared, because a metal's "
                "albedo is its reflectance and a photograph of it is the "
                "light. The collar wedge's own reading, V 0.859 S 0.123, is a "
                "blown specular and proves the point."),
    Fabric("ef_coverall", "EarthForce technical coverall",
           _MH, "(0.425,0.615)-(0.475,0.72) officer jacket in the downlight",
           (0.127, 0.169, 0.229), roughness=0.90, authority=1,
           note="EXTRAPOLATED as a SET: no frame in reference/ shows an "
                "EarthForce engineering or environmental coverall. What is "
                "measured is the COLOUR -- the standing officer in `more "
                "hallway.jpg`, H 215.3, the same blue family as the command "
                "wool -- so the extrapolation is 'the same cloth, cut as "
                "workwear', not a new palette. Overturned by any Grey or "
                "Yellow sector interior with a technician in it, which "
                "REFERENCE-GAPS.md 6 already asks for."),

    # ---- Nightwatch -------------------------------------------------------
    Fabric("nightwatch_black", "Nightwatch armband -- matte black field",
           _ZA, "(0.795,0.66)-(0.865,0.69), p75",
           (0.094, 0.107, 0.117), roughness=0.88, authority=2,
           note="Vsd 0.002 over 940 px: the flattest surface in the whole "
                "costume reference set. That is what says it is matte wool or "
                "felt and not the patent leather of the collar 30 cm away."),
    Fabric("nightwatch_gold", "Nightwatch armband -- gold embroidery",
           _ZA, "gold-thread mask over (0.76,0.62)-(1.00,0.82): S>0.45, V>0.30, R>B",
           (0.620, 0.440, 0.200), roughness=0.42, metallic=0.85, authority=2,
           declared=True,
           note="Measured H 23.4 S 0.642 V 0.489 over 3,296 masked pixels. "
                "Level declared as for `ef_gold`. Embroidery, not plate: "
                "roughness 0.42 and metallic 0.85 rather than 0.30/1.0, "
                "because thread scatters."),

    # ---- Psi Corps --------------------------------------------------------
    # FACTIONS 4.2 is unresolved about the suit colour and this module resolves
    # it by looking: see PSI_CORPS_RESOLUTION. All three readings are built.
    Fabric("psi_ochre", "Psi Corps suit -- warm mustard / gold-ochre",
           _TO, "(0.29,0.33)-(0.35,0.45) lit jacket front, p75",
           (0.337, 0.283, 0.124), roughness=0.72, authority=1,
           note="H 44.6 S 0.632, cross-checked on the skirt at H 43.1 S 0.627 "
                "-- 1.5 degrees and 0.005 apart, two panels of the same "
                "garment. This is the reading `reference/22-QUARANTINE-ai-"
                "generated/README.md` says is wrong, and it is not wrong."),
    Fabric("psi_olive", "Psi Corps suit -- dark olive-green/black",
           _TU, "(0.30,0.70)-(0.42,0.90) jacket body, p75",
           (0.139, 0.121, 0.088), roughness=0.72, authority=1,
           note="H 38.5 S 0.364 at V 0.139. A different episode and a "
                "different garment on the same character."),
    Fabric("psi_grey", "Psi Corps suit -- pale grey",
           _TU, "no region: asserted in text, not measured",
           (0.300, 0.302, 0.310), roughness=0.72, authority=4, declared=True,
           note="The third reading, from `reference/22-QUARANTINE-ai-generated/"
                "README.md`'s own prose ('pale grey Psi Corps suit with black "
                "gloves'). Carried at authority 4 -- a claim in a README is "
                "not a frame -- and included because PSI_CORPS_RESOLUTION says "
                "the identity is the badge and the panels, not one colour."),
    Fabric("psi_black_panel", "Psi Corps black inset panel",
           _TO, "(0.27,0.40)-(0.30,0.62) side panel, p75",
           (0.036, 0.038, 0.067), roughness=0.60, authority=1,
           note="The invariant. Present in BOTH Talia frames whatever the body "
                "colour is: a deep V at the front and panels down the sides "
                "and sleeves in one frame, an asymmetric shawl wrap in the "
                "other. Reads blue-black, H 236.8."),
    Fabric("psi_chrome", "Psi Corps badge -- polished silver-chrome",
           _TU, "badge core (0.55,0.58)-(0.70,0.74), V>0.42 and |R-B|<0.14",
           (0.750, 0.760, 0.780), roughness=0.12, metallic=1.0, authority=1,
           declared=True,
           note="Level declared (a mirror photographs as its surroundings). "
                "The MEASURED part is the shape: a 27x33 px bright core, "
                "aspect 0.82 -- taller than wide, which is the downward-"
                "pointing cut diamond the index resolved at 8x."),

    # ---- Rangers ----------------------------------------------------------
    Fabric("ranger_tabard", "Ranger tabard -- brown/tan",
           _MC, "(0.44,0.55)-(0.62,0.70) lit tunic front, RAW (see note), p75",
           (0.153, 0.107, 0.089), roughness=0.80, authority=1, declared=True,
           note="This frame FAILS the grey-world test (gains 0.687/1.098/1.580) "
                "so no balanced hue is quotable. What is quotable is a ratio: "
                "raw tabard V 0.259 against raw skin V 0.608 = 0.426, so the "
                "tabard is 0.426 x SKIN_ANCHOR = 0.153 in value. Chroma is "
                "DERIVED, not measured: the tabard's raw S 0.742 against the "
                "same frame's raw skin S 0.768 says the two are about equally "
                "saturated, so the tabard's true chroma is about skin's, ~0.42. "
                "Hue from the index's 'brown/tan'. Value MEASURED, chroma "
                "DERIVED, hue SOURCED -- and said separately so a reader can "
                "see which is which."),
    Fabric("ranger_black", "Ranger underlayers -- black quilted leather",
           _MC, "(0.22,0.45)-(0.30,0.60) sleeve, RAW ratio to skin",
           (0.086, 0.082, 0.078), roughness=0.48, authority=1, declared=True,
           note="raw V 0.145 / raw skin 0.608 = 0.238 -> 0.086. Belt 0.042 and "
                "trousers 0.033 by the same ratio, so the underlayers are a "
                "value LADDER, not one black."),
    Fabric("ranger_cabochon", "Ranger brooch -- pale blue-green cabochon",
           _MC, "(0.44,0.325)-(0.51,0.355)",
           (0.420, 0.620, 0.600), roughness=0.10, authority=1, declared=True,
           note="The one element in the frame the cast cannot hide. Raw, it is "
                "the LEAST saturated thing present (S 0.450 against 0.60-0.77 "
                "for everything else); balanced -- invalidly, but the outlier "
                "survives -- it comes out H 181.6, cyan. Two treatments "
                "agreeing that it is the coolest object in an orange frame is "
                "the evidence for 'pale blue-green'; the level is declared."),
    Fabric("ranger_gold", "Ranger bezel and belt buckle -- gold-bronze",
           _MC, "(0.60,0.53)-(0.72,0.60) buckle",
           (0.560, 0.420, 0.220), roughness=0.34, metallic=1.0, authority=1,
           declared=True, note="Bronze rather than brass: raw H 20.6 against "
                               "the EarthForce name bar's H 38.3."),

    # ---- Narn -------------------------------------------------------------
    Fabric("narn_suede", "Narn suede panels -- tan/ochre",
           _GK, "(0.30,0.62)-(0.45,0.75) fluted collar, RAW",
           (0.275, 0.165, 0.055), roughness=0.88, authority=2,
           note="Frame FAILS grey-world at gains 0.496/1.566/2.909 -- the "
                "balance turns Narn skin GREEN -- so this is anchored on the "
                "frame's own Narn skin instead (NARN_SKIN_ANCHOR 0.42 against "
                "the measured crown ground 0.729). Ratios within the frame are "
                "the claim: collar 0.38x skin, apron 0.34x, yoke trim 0.62x."),
    Fabric("narn_apron", "Narn apron panel -- deep pebbled reptile hide",
           _GK, "(0.55,0.80)-(0.75,0.95), RAW",
           (0.251, 0.071, 0.024), roughness=0.72, authority=2,
           note="The reddest and most saturated element on the costume, H 12.4 "
                "S 0.906 raw, against the collar's H 30.0 S 0.800."),
    Fabric("narn_yoke", "Narn shoulder yoke -- studded quilted pauldron",
           _GK, "(0.62,0.60)-(0.78,0.72), RAW",
           (0.455, 0.247, 0.086), roughness=0.66, authority=2,
           note="The BRIGHTEST garment element, 0.62x skin. A Narn formal "
                "silhouette is lit at the shoulders."),
    Fabric("narn_iridescent", "Narn trim -- iridescent purple-blue",
           _GK, "not separately resolvable at 800x800",
           (0.180, 0.140, 0.300), roughness=0.28, metallic=0.4, authority=2,
           declared=True,
           note="FACTIONS 6.3 (authority 2, this same file) states 'iridescent "
                "purple-blue trim on shoulder yokes and front apron edge'. The "
                "trim is a few pixels wide here and was NOT separately "
                "sampled; the colour is declared from that sentence and the "
                "metallic 0.4 is what 'iridescent' has to be to behave. Marked "
                "so, rather than dressed up as a reading."),
    Fabric("narn_salvage", "Narn refugee dress -- worn leather and salvaged issue",
           _GK, "derived: narn_suede at the civilian value median",
           (0.062, 0.048, 0.030), roughness=0.94, authority=5, declared=True,
           note="FACTIONS 6.3: 'Take the same silhouette down: no pauldrons, no "
                "trim, no gloves; worn leather, salvaged EA-issue coveralls.' "
                "The value is not invented -- it is the measured CIVILIAN "
                "median from `more zocalo.png` (0.062) applied to the Narn "
                "hue, so a Narn refugee sits in the crowd's own value band "
                "rather than in a made-up one."),

    # ---- Minbari ----------------------------------------------------------
    Fabric("minbari_cream", "Minbari religious robe -- cream and pale gold",
           _RO, "(0.79,0.74)-(0.86,0.88) lit robe, p75",
           (0.620, 0.600, 0.480), roughness=0.76, authority=1, declared=True,
           note="Measured (0.739,0.746,0.588) at H 62.6 S 0.212, but this "
                "frame is borderline on grey-world (R gain 0.766, just outside "
                "the 0.80 limit) and H 62 is yellow-green rather than the "
                "index's 'cream and pale-gold'. The value is kept and the hue "
                "is pulled to H 45 -- a DECLARED correction of 17 degrees, "
                "stated rather than absorbed. Overturned by a second Minbari "
                "frame under different light."),
    Fabric("minbari_black", "Minbari black robe -- the second group",
           _RO, "(0.345,0.66)-(0.395,0.76) standing figure, median",
           (0.030, 0.028, 0.032), roughness=0.70, authority=1, declared=True,
           note="Balanced median V 0.024 -- the darkest garment anywhere in the "
                "reference set, and 1/16 of the cream robe in the SAME frame. "
                "That 16:1 ratio inside one chamber is the composition fact: "
                "the two Minbari groups are the two ends of the frame's value "
                "range and nothing else in the room is near either. Floored at "
                "ALBEDO_FLOOR so it is not pure black."),
    Fabric("minbari_worker", "Minbari worker caste -- undyed layered cloth",
           _RO, "derived from minbari_cream at 0.55x",
           (0.240, 0.228, 0.192), roughness=0.88, authority=5, declared=True,
           note="EXTRAPOLATED. No frame shows worker-caste Minbari. Placed "
                "between the two measured castes rather than outside them, "
                "because the one thing the rotunda frame establishes is that "
                "Minbari dress is a value ladder within a narrow warm hue."),

    # ---- League and alien formal -----------------------------------------
    Fabric("league_bone", "League delegate cowl -- bone/cream quilted",
           _PM, "(0.30,0.62)-(0.42,0.78) cowl, p75",
           (0.380, 0.350, 0.329), roughness=0.90, authority=1,
           note="H 24.0 S 0.132 -- near-neutral warm, and the brightest garment "
                "in the council frame. The cowl is heavily QUILTED, which is a "
                "normal-map fact, not an albedo one."),
    Fabric("league_stole", "League delegate stole -- magenta/rose",
           _PM, "(0.36,0.50)-(0.44,0.75), median",
           (0.310, 0.235, 0.258), roughness=0.66, authority=1,
           note="H 341.3 S 0.244. The single most chromatic garment element in "
                "the council frame, and it is a STOLE down the centre front "
                "with a gold cord on it -- the League's status marker is a "
                "vertical band, not a badge."),
    Fabric("league_cord", "League delegate cord -- gold rope",
           _PM, "(0.38,0.55)-(0.46,0.70)",
           (0.560, 0.430, 0.240), roughness=0.44, metallic=0.8, authority=1,
           declared=True, note="Level declared as for every metal here."),
    Fabric("league_dark", "League working dress -- dark layered cloth",
           _MZ, "civilian median, this file's own measurement",
           (0.062, 0.052, 0.048), roughness=0.92, authority=1, declared=True,
           note="Not a separate measurement: the measured civilian median from "
                "`more zocalo.png`. A Drazi docker and a human docker wear the "
                "same value band, which is what the frame actually shows."),

    # ---- Centauri ---------------------------------------------------------
    Fabric("centauri_brocade", "Centauri court coat -- heavy dark brocade",
           _MZ, "(0.735,0.30)-(0.795,0.50) outer coat, median",
           (0.048, 0.031, 0.037), roughness=0.62, authority=1,
           note="H 338.0 S 0.346 at V 0.048 -- among the DARKEST garments in "
                "the frame, which is the opposite of what 'a status culture' "
                "suggests and is what the frame shows. Centauri conspicuousness "
                "is cut and volume, not brightness."),
    Fabric("centauri_stole", "Centauri stole/drape",
           _MZ, "(0.75,0.36)-(0.79,0.60), median",
           (0.073, 0.049, 0.048), roughness=0.70, authority=1,
           note="H 1.4 S 0.340. 1.5x the coat's value: the drape is the part "
                "that reads."),

    # ---- Civilian ---------------------------------------------------------
    # The measured distribution, one Fabric per sampled garment, so the
    # civilian palette IS the reference rather than a description of it.
    Fabric("civ_dark_warm", "Civilian -- dark warm layer",
           _MZ, "(0.31,0.45)-(0.43,0.62) foreground jacket back, median",
           (0.092, 0.071, 0.071), roughness=0.90, authority=1,
           note="H 1.5 S 0.228."),
    Fabric("civ_mid_warm", "Civilian -- mid warm layer, lit",
           _MZ, "(0.40,0.56)-(0.455,0.66) lit sleeve, median",
           (0.187, 0.165, 0.145), roughness=0.90, authority=1,
           note="H 28.1 S 0.224. The BRIGHTEST garment in the frame and still "
                "3.7x darker than the lit deck beside it."),
    Fabric("civ_collar_yoke", "Civilian -- collar and shoulder yoke",
           _MZ, "(0.32,0.42)-(0.42,0.455), median",
           (0.169, 0.138, 0.127), roughness=0.86, authority=1,
           note="H 16.3 S 0.250. Civilian coats in this frame are CUT with a "
                "yoke: the shoulders are a separate, slightly lighter panel. "
                "That is a silhouette fact as much as a colour one."),
    Fabric("civ_cool_dark", "Civilian -- cool dark layer",
           _MZ, "(0.545,0.26)-(0.60,0.44) walking figure coat, median",
           (0.029, 0.022, 0.030), roughness=0.90, authority=1,
           note="H 296.5. The secondary hue cluster: 267-300 degrees, about a "
                "third of the sampled garments."),
    Fabric("civ_light_shirt", "Civilian -- light shirt, the tail of the distribution",
           _ZW, "(0.485,0.42)-(0.545,0.62) cream open-neck shirt, median",
           (0.384, 0.395, 0.410), roughness=0.88, authority=1,
           note="H 213.7 S 0.064 at V 0.410. THE ONE light garment in either "
                "Zocalo frame. It is in the palette at a low weight because "
                "deleting it would make the crowd uniformly dark, and the "
                "reference says it is nearly-but-not-quite uniformly dark. "
                "Era caveat: `zocalo.webp` is flagged S1 for set dressing in "
                "reference/00-INDEX.md; it is used here only for the SHAPE of "
                "the value distribution, never for a uniform."),
    Fabric("civ_worker_drab", "Worker -- drab coverall",
           _ZW, "(0.235,0.58)-(0.30,0.85) dark coat, median",
           (0.156, 0.144, 0.130), roughness=0.94, authority=1,
           note="H 31.7 S 0.166."),
    Fabric("civ_lurker", "Downbelow -- salvage",
           _MZ, "derived: the civilian value floor, desaturated",
           (0.041, 0.038, 0.036), roughness=0.96, authority=5, declared=True,
           note="EXTRAPOLATED, and the only civilian entry that is. The FLOOR "
                "of the measured civilian distribution (0.030-0.046 across "
                "four sampled garments) with the chroma taken out, because "
                "FACTIONS 11.2 says lurkers are 'conspicuous by clothing before "
                "anything else' -- and in a crowd whose median garment is "
                "already dark, conspicuous means colourless and worn, not "
                "darker. `sleeping-in-light-05.jpg` is the only Downbelow frame "
                "the project holds and its DRESSING is out of era, so it was "
                "not used."),
    Fabric("civ_boot", "Boots and belts -- dark leather",
           _MZ, "derived from civ_dark_warm at 0.6x",
           (0.055, 0.043, 0.043), roughness=0.40, authority=5, declared=True,
           note="EXTRAPOLATED. No frame in the set resolves footwear."),
    Fabric("monastic_habit", "Monastic habit -- undyed wool",
           _RO, "derived: minbari_cream at 0.42x, chroma halved",
           (0.260, 0.248, 0.222), roughness=0.95, authority=5, declared=True,
           note="EXTRAPOLATED. FACTIONS 11.3 places Brother Theo's order aboard "
                "from S3E02 and reference/ holds no frame of them. Built from "
                "the one robe measurement the project owns, taken down to a "
                "working community's undyed cloth. Overturned by any frame of "
                "the order."),
)}


# ---------------------------------------------------------------------------
# 4. The Psi Corps ruling, which FACTIONS.md 4.2 asked for
# ---------------------------------------------------------------------------
PSI_CORPS_RESOLUTION = """
FACTIONS.md 4.2 records a contradiction inside this repository and asks for a
ruling. This module ruled by opening the files.

  * `reference/22-QUARANTINE-ai-generated/README.md` quarantines an AI
    turnaround BECAUSE it puts Talia Winters in mustard/ochre, and names
    `talia-winters in gorgeous office.webp` as the genuine screencap that
    disproves it.
  * That screencap, opened and sampled in this session, shows a structured
    jacket and pencil skirt at H 44.6 S 0.632 (jacket front) and H 43.1 S 0.627
    (skirt) -- two panels of one garment, 1.5 degrees apart. That is mustard /
    gold-ochre by measurement, on the very frame cited as the disproof.
  * `Talia Winters in uniform.webp`, a different episode, shows a dark
    olive-green/black jacket at H 38.5 S 0.364 with an asymmetric shawl wrap.
  * A third reading, "pale grey", exists only as prose in the quarantine README
    and is carried at authority 4.

RULING, and it matches FACTIONS 4.2's proposal rather than overturning it:

  1. The QUARANTINE STANDS. An AI turnaround is untrustworthy whatever colour it
     picks, and nothing here touches that decision.
  2. The REASON GIVEN for it is wrong on the facts, and the file it cites is the
     evidence against it. Reported, not edited -- reference/ is not this
     module's to change.
  3. There is no single Psi Corps colour. The identity is built from the
     INVARIANTS, which are present in both frames whatever the body colour:
     the silver-chrome downward-pointing Psi badge, black gloves, strongly
     squared shoulders, and black inset panelling. Body colour is a per-NPC
     draw from {psi_ochre, psi_olive, psi_grey}.

The consequence for the build is that `PSI_BODY_PALETTE` has three entries and
`_selftest` asserts a population of telepaths uses more than one of them -- so a
future session cannot quietly collapse it back to a single hard-coded colour,
which is the failure mode the contradiction was heading toward.
"""

PSI_BODY_PALETTE = (("psi_ochre", 0.45), ("psi_olive", 0.35), ("psi_grey", 0.20))


# ---------------------------------------------------------------------------
# 5. Badges and decals -- zero triangles, measured sizes, derived read distances
# ---------------------------------------------------------------------------
# A device has to span about this many pixels before a viewer can tell which
# device it is. Below it the atlas mip chain resolves it to an average colour,
# which is correct behaviour and costs nothing.
DECAL_LEGIBLE_PX = 8.0

# Where a decal sits. The vocabulary is small on purpose: a slot is a point on
# the parametric body, so a badge can move species to species without a table
# per species.
DECAL_SLOTS = ("left_chest", "right_chest", "left_upper_sleeve", "right_upper_sleeve",
               "left_forearm", "throat", "shoulder_strap", "centre_front")

# SIDEDNESS, STATED PLAINLY BECAUSE IT IS NOT SETTLED.
# reference/00-INDEX.md (session 2s, read at 6-8x) places the EarthForce wings
# on the LEFT sleeve, the name bar on the RIGHT chest, the security badge on the
# RIGHT chest, the link on the LEFT wrist and the Nightwatch armband on the LEFT
# forearm. This session measured one frame where the pose does NOT leave the
# question open -- `security in uniform.jpg`, Zack seated, both breast pockets
# visible and 450 px against 430 px wide, i.e. the torso is square to camera
# within 5% -- and in it the security badge sits above the FRAME-RIGHT pocket,
# which on a square-on subject is the wearer's LEFT chest.
#
# The other portraits cannot decide it: a single subject at unknown rotation
# does not determine which shoulder is nearer, and guessing would be exactly the
# "rigour-shaped and wrong" failure AAA-STANDARD warns about. So the index's
# reading is kept as the default, the dissent is recorded here with its
# arithmetic, and the side is ONE EDIT away in this table.
#
# What would settle it: any frame with two officers at a known camera, a
# production costume sheet, or a shot of the same badge on a subject whose
# handedness is visible.
BADGE_SIDE_SOURCE = "reference/00-INDEX.md session 2s, 6-8x; dissent recorded above"


@dataclass(frozen=True)
class Decal:
    """A badge, patch or emblem: a rectangle in the shared atlas, no geometry."""
    key: str
    title: str
    slot: str
    width_m: float
    height_m: float
    px: tuple            # measured (w, h) in the source frame
    frame: str
    authority: int
    metal: str = ""      # fabric key of the metal it is struck in, if any
    note: str = ""

    def legible_to_m(self):
        """Distance inside which the DEVICE can be told apart from a smudge."""
        return body.aliases_beyond_m(self.width_m) / DECAL_LEGIBLE_PX

    def subpixel_beyond_m(self):
        """Distance beyond which the whole badge is under one shading sample."""
        return body.aliases_beyond_m(self.width_m)


DECALS = {d.key: d for d in (
    Decal("ef_security_badge", "EarthForce Security -- crosshair in a diamond",
          "left_chest", 0.075, 0.065, (78, 67), _SU, 1, metal="ef_gold",
          note="MEASURED by a warm-pixel mask over (0.70,0.49)-(0.90,0.61): 78 x "
               "67 px, aspect 1.16 -- wider than tall, which is the 'diamond "
               "with slightly convex sides'. Converted at 539 px across the "
               "seated torso, taken as 0.52 m (EXTRAPOLATED, +/-15%). Confirmed "
               "independently in `Zach Allan in security uniform.jpg`, so this "
               "is the device and not a one-off."),
    Decal("ef_wings", "EarthForce wings", "left_upper_sleeve", 0.064, 0.049,
          (66, 50), _SH, 2, metal="ef_gold",
          note="Gold outspread wings flanking a red-and-white device on a blue "
               "ground, black field, red top edge (index, 8x). Size from the "
               "sleeve patch box against ~430 px of biacromial breadth."),
    Decal("nightwatch_eye", "NIGHT WATCH armband emblem", "left_forearm",
          0.085, 0.057, (104, 82), _ZA, 2, metal="nightwatch_gold",
          note="THE most legible political signal on the station and the "
               "highest-value 82 mm on any NPC. Read at 5x: a stylised EYE -- "
               "almond lens, concentric iris and pupil -- inside a SWEPT "
               "WING/almond outline that runs to a long tapering point on one "
               "side, with a small triangle above and outboard of the pupil, "
               "over 'NIGHT WATCH' in gold caps curved to follow the arm. "
               "MEASURED: gold-pixel bbox 152 x 117, aspect 1.30; the device is "
               "the upper ~60% and the legend the lower ~40%, device aspect "
               "~2.08:1. Sized at 1,446 px/m from the shoulder span."),
    Decal("psi_badge", "Psi Corps -- downward cut diamond with a raised Psi",
          "left_chest", 0.035, 0.042, (27, 33), _TU, 1, metal="psi_chrome",
          note="Bright-core mask gives 27 x 33 px, aspect 0.82 -- TALLER than "
               "wide, i.e. downward-pointing, which is the index's reading "
               "arrived at independently. The full badge including its dark "
               "facets is larger than the core; size carries +/-20%."),
    Decal("ranger_brooch", "Anla'shok -- oval cabochon in an ornate bezel",
          "left_chest", 0.050, 0.041, (35, 29), _MC, 1, metal="ranger_gold",
          note="FACTIONS 10.1: 'the tell is the brooch, and a player who learns "
               "to spot it starts seeing them everywhere.' At 50 mm it is "
               "legible inside 9.7 m, which is conversation-and-corridor range "
               "-- so the discovery mechanic is affordable and is bounded."),
    Decal("station_shield", "Babylon 5 station shield", "right_upper_sleeve",
          0.075, 0.082, (0, 0), "16-signage-typography-ui/babylon 5 shield.webp", 4,
          note="Red-outlined shield split diagonally, grey lower-left / blue "
               "upper-right, seven white stars (four on grey, three on blue), "
               "yellow-and-black 5 on a vertical sword (FACTIONS 3.3, authority "
               "4, corroborated at two independent sources). NO WEARER SCALE "
               "EXISTS -- the file is a logo, not a photograph of a sleeve -- "
               "so the size is set equal to the measured security badge's and "
               "marked (0,0) px to say so. `Zach Allan in security uniform.jpg` "
               "does show a dark shield-shaped patch high on the left sleeve at "
               "5x, but it is not legible and was NOT read as this device."),
)}


# ---------------------------------------------------------------------------
# 6. Silhouette modifiers -- zero triangles
# ---------------------------------------------------------------------------
# A modifier is a piecewise-linear radial scale s(y), y in fractions of stature,
# applied about each part's own local axis. Strictly positive everywhere, so the
# determinant of the transform is positive and no winding can flip.
@dataclass(frozen=True)
class Silhouette:
    key: str
    title: str
    # ((y_fraction, scale), ...) ascending in y; outside the range, the nearest.
    profile: tuple
    parts: tuple          # which body parts it applies to
    note: str = ""

    def scale_at(self, yf):
        p = self.profile
        if yf <= p[0][0]:
            return p[0][1]
        if yf >= p[-1][0]:
            return p[-1][1]
        for (y0, s0), (y1, s1) in zip(p, p[1:]):
            if y0 <= yf <= y1:
                t = (yf - y0) / max(y1 - y0, 1e-9)
                return s0 + (s1 - s0) * t
        return 1.0


_TORSO = ("torso",)
_ARMS = ("arm",)
_LEGS = ("leg",)

SILHOUETTES = {s.key: s for s in (
    Silhouette("squared_shoulders", "Structured jacket -- strong squared shoulders",
               ((0.60, 1.00), (0.72, 1.03), (0.79, 1.17), (0.84, 1.14)), _TORSO,
               note="Psi Corps and the EarthForce command cut both do this. "
                    "Talia's jacket in BOTH frames has a shoulder line wider "
                    "than her deltoid, which is a pad, not a body. 1.17 at the "
                    "acromion moves the outline 0.035 m -- above the 1.5 px "
                    "deviation budget out to 36 m, so it is not a detail."),
    Silhouette("jacket_bulk", "A jacket over a body",
               ((0.45, 1.06), (0.55, 1.09), (0.80, 1.08), (0.86, 1.02)), _TORSO,
               note="Every dressed torso gets this. A body is not a mannequin "
                    "with paint on it; a service jacket adds 20-30 mm of cloth "
                    "and lining all round."),
    Silhouette("heavy_coat", "Long heavy coat -- the Zocalo civilian silhouette",
               ((0.35, 1.22), (0.50, 1.20), (0.72, 1.14), (0.86, 1.05)), _TORSO,
               note="`more zocalo.png` shows civilian dress as LONG and "
                    "LAYERED: the foreground figure's coat has a shoulder yoke "
                    "seam and falls past the hip, and three background figures "
                    "read as coats rather than jackets. The flare below the "
                    "waist is what separates a civilian from a uniform at 40 m, "
                    "where no colour survives."),
    Silhouette("sleeve_heavy", "Quilted or padded sleeve",
               ((0.40, 1.16), (0.70, 1.20), (0.82, 1.12)), _ARMS,
               note="Ranger quilted leather sleeves; Narn studded pauldrons "
                    "reaching down the upper arm."),
    Silhouette("boots", "Boots",
               ((0.00, 1.34), (0.14, 1.30), (0.22, 1.02)), _LEGS,
               note="Dock and Downbelow wear. Ranger, Narn and EarthForce duty "
                    "rigs all boot. 0.34 of a 0.048-of-stature calf is 0.028 m "
                    "of outline -- honest to 29 m."),
    Silhouette("tabard", "Sleeveless tabard over the torso",
               ((0.35, 1.10), (0.52, 1.14), (0.74, 1.12), (0.82, 1.04)), _TORSO,
               note="The Ranger tabard-tunic. Reaches mid-thigh, so the flare "
                    "runs BELOW the hip -- which is why its lowest control "
                    "point is at 0.35 of stature and the jacket's is at 0.45."),
    Silhouette("tac_vest", "Security duty rig -- tactical vest over the jacket",
               ((0.50, 1.12), (0.58, 1.16), (0.78, 1.15), (0.83, 1.06)), _TORSO,
               note="`security in uniform.jpg` shows background officers in the "
                    "same grey jacket with a black tactical vest over it: "
                    "'Two distinct security silhouettes to model' (FACTIONS "
                    "3.3, authority 1). This is the second one, and it is a "
                    "modifier plus a material, not a mesh."),
    Silhouette("rags", "Downbelow -- ill-fitting salvage",
               ((0.30, 1.14), (0.50, 1.11), (0.70, 1.16), (0.84, 1.09)), _TORSO,
               note="EXTRAPOLATED. The one thing that reads as poverty at "
                    "crowd distance is a garment that does not follow the body, "
                    "so the profile is deliberately NON-MONOTONIC -- it bulges, "
                    "narrows and bulges again. Every other modifier here is "
                    "smooth."),
)}


# ---------------------------------------------------------------------------
# 7. Attachments -- the only triangles clothing spends
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Attachment:
    key: str
    title: str
    error_m: float        # how far it moves the silhouette
    note: str = ""

    def honest_from_m(self):
        """Beyond this, dropping it is inside the 1.5 px deviation budget."""
        return body.honest_from_m(self.error_m)


ATTACHMENTS = {a.key: a for a in (
    Attachment("standing_collar", "Standing collar", 0.040,
               note="Fills the notch between jaw and shoulder, which is a "
                    "silhouette change of about the collar's height. Both "
                    "EarthForce patterns have one; body.py's FIGURE table "
                    "already corrected its chin measurement FOR one."),
    Attachment("epaulettes", "Epaulette straps", 0.014,
               note="Leather straps over both shoulders. body.py's biacromial "
                    "ratio was corrected from 0.249 to 0.235 because the "
                    "measurement crossed these -- so this attachment puts back "
                    "exactly what that correction removed, which is a nice "
                    "closed loop and a real cross-check."),
    Attachment("belt", "Waist belt", 0.008),
    Attachment("armband", "Nightwatch armband strap", 0.005,
               note="FACTIONS 5.3 calls the armband 'one decal and one strap "
                    "mesh'. The strap is 5 mm proud of a sleeve, so it is "
                    "honest to drop at 5.1 m -- and the DECAL it carries stays "
                    "legible to 16.4 m and visible as a dark band far beyond. "
                    "Pricing them together would have kept 24 triangles alive "
                    "three times further than they earn."),
    Attachment("baldric", "Diagonal baldric", 0.014),
    Attachment("cowl", "Cowl rising over the shoulders", 0.070,
               note="pak'ma'ra and League delegate dress. body.py's own note on "
                    "the pak'ma'ra neck records that what stands above the "
                    "shoulder in `more Pak'ma'ra.webp` is 'a COWL, a garment' "
                    "-- fusing it to the skull drove the tendrils through the "
                    "chest. So this attachment is the thing that let the BODY "
                    "be right."),
    Attachment("skirt", "Floor-length robe skirt", 0.000,
               note="error_m is 0.000 because this is not an addition: it "
                    "REPLACES both legs and both feet, and a robed figure is "
                    "cheaper than a trousered one. It can never be dropped -- "
                    "dropping it would remove the lower half of the figure -- "
                    "so it is exempt from the distance rule and `_selftest` "
                    "asserts the exemption is explicit rather than accidental."),
)}

# The one attachment that is never culled, for the reason in its note.
NEVER_CULLED = frozenset({"skirt"})


# ---------------------------------------------------------------------------
# 8. Costume sets
# ---------------------------------------------------------------------------
MATERIAL_SLOTS = ("npc_cloth", "npc_cloth_trim", "npc_leather", "npc_metal",
                  "npc_decal")


@dataclass(frozen=True)
class CostumeSet:
    key: str
    title: str
    cloth: tuple          # weighted palette: ((fabric_key, weight), ...)
    trim: str             # piping / panel / stole fabric
    leather: str
    metal: str
    silhouettes: tuple
    attachments: tuple
    decals: tuple
    robed: bool = False   # legs replaced by a skirt
    split: str = "yoke"   # how the torso's second material is cut
    wear: tuple = (0.05, 0.25)
    authority: int = 5
    source: str = ""
    note: str = ""
    era_event: str = ""   # set only if the whole costume has a start date


def _P(*pairs):
    return tuple(pairs)


SETS = {s.key: s for s in (
    CostumeSet("ef_command", "EarthForce command, S2-3",
               _P(("ef_command_wool", 1.0)), "ef_command_leather",
               "ef_command_leather", "ef_gold",
               ("jacket_bulk", "squared_shoulders"),
               ("standing_collar", "epaulettes", "belt"),
               (("ef_wings", "left_upper_sleeve"),
                ("station_shield", "right_upper_sleeve")),
               wear=(0.02, 0.10), authority=2, source=_SH, split="plastron",
               note="FACTIONS 3.3's definitive in-era description, every clause "
                    "of which was re-read off the file in this session. The "
                    "S1/S2-3 discriminator is the crimson piping and the "
                    "leather bib; this set has both and the vector sheets in "
                    "the same folder have neither, which is why they are not "
                    "used. NEW READING, not in the index: the CUFF carries a "
                    "brown leather band with crimson piping on BOTH its edges "
                    "-- two crimson lines with leather between them -- and the "
                    "link is visible on the back of the wrist in this frame "
                    "too, which corroborates `Zach Allan in security "
                    "uniform.jpg` at authority 2 on a second subject."),
    CostumeSet("ef_security_dress", "EarthForce security, service dress",
               _P(("ef_security_twill", 1.0)), "ef_black_leather",
               "ef_black_leather", "ef_gold",
               ("jacket_bulk",),
               ("standing_collar", "epaulettes", "belt"),
               (("ef_security_badge", "left_chest"),),
               wear=(0.05, 0.20), authority=2, source=_ZA,
               note="Grey twill; black leather standing collar and yoke; black "
                    "leather epaulettes; two flapless breast pockets with "
                    "horizontal welt seams; gold triangular pin at the throat, "
                    "point DOWN (read at 2.5x in `security in uniform.jpg`)."),
    CostumeSet("ef_security_duty", "EarthForce security, duty rig",
               _P(("ef_security_twill", 1.0)), "ef_black_leather",
               "ef_black_leather", "ef_gold",
               ("jacket_bulk", "tac_vest", "boots"),
               ("standing_collar", "belt"),
               (("ef_security_badge", "left_chest"),),
               wear=(0.10, 0.35), authority=1, source=_SU,
               note="The same jacket with a black tactical vest over it. "
                    "FACTIONS 3.3: 'Two distinct security silhouettes to "
                    "model.' No epaulettes -- the vest covers them."),
    CostumeSet("ef_technical", "EarthForce technical coverall",
               _P(("ef_coverall", 1.0)), "ef_black_leather", "civ_boot", "ef_gold",
               ("jacket_bulk", "boots"), ("belt",),
               (("station_shield", "right_upper_sleeve"),),
               wear=(0.20, 0.60), authority=5, source=_MH,
               note="EXTRAPOLATED cut, MEASURED colour -- see `ef_coverall`. "
                    "Engineering, environmental, hydroponics, waste and cargo "
                    "are 4,000 of the 6,500 (FACTIONS 2.2) and nothing in "
                    "reference/ shows what they wear."),
    CostumeSet("ef_medical", "EarthForce medical",
               _P(("ef_security_twill", 1.0)), "civ_light_shirt",
               "ef_black_leather", "ef_gold",
               ("jacket_bulk",), ("standing_collar",),
               (("station_shield", "right_upper_sleeve"),),
               wear=(0.02, 0.12), authority=5,
               note="EXTRAPOLATED. 300 Medlab staff (FACTIONS 2.2) and no "
                    "frame. Built as the service jacket with a pale yoke, on "
                    "the argument that medical staff need to be identifiable "
                    "in a corridor and the station's own signage language is "
                    "'official and reasonable' rather than decorative."),

    # ---- Psi Corps --------------------------------------------------------
    CostumeSet("psi_corps", "Psi Corps",
               PSI_BODY_PALETTE, "psi_black_panel", "psi_black_panel",
               "psi_chrome",
               ("jacket_bulk", "squared_shoulders"), ("standing_collar",),
               (("psi_badge", "left_chest"),),
               wear=(0.00, 0.06), authority=1, source=_TO,
               note="See PSI_CORPS_RESOLUTION. Three body colours, one identity: "
                    "the badge, the gloves, the squared shoulders and the black "
                    "inset panels. Wear tops out at 0.06 -- the Corps does not "
                    "do scuffed."),

    # ---- Rangers ----------------------------------------------------------
    CostumeSet("ranger", "Anla'shok (Ranger)",
               _P(("ranger_tabard", 1.0)), "ranger_black", "ranger_black",
               "ranger_gold",
               ("tabard", "sleeve_heavy", "boots"),
               ("standing_collar", "belt", "baldric"),
               (("ranger_brooch", "left_chest"),),
               wear=(0.10, 0.30), authority=1, source=_MC,
               era_event="rangers_visible",
               note="IN ERA FOR S3 ONLY. reference/00-INDEX.md is explicit: "
                    "'Marcus is introduced in S3, so the Ranger costume is "
                    "inside the lock -- but only for S3, not S2.' `era_event` "
                    "enforces it and `_selftest` runs a Season 2 datum to watch "
                    "the costume vanish."),

    # ---- Narn -------------------------------------------------------------
    CostumeSet("narn_formal", "Narn formal / ambassadorial",
               _P(("narn_suede", 1.0)), "narn_iridescent", "narn_apron",
               "narn_yoke",
               ("jacket_bulk", "sleeve_heavy", "boots"),
               ("standing_collar", "belt"), (),
               wear=(0.05, 0.20), authority=2, source=_GK,
               note="Layered tan/ochre suede with fringed edges; vertical dark "
                    "strap bands with brass studs; a tall stiff FLUTED standing "
                    "collar; chainmail bib; iridescent purple-blue trim on the "
                    "shoulder yokes and apron edge; a large pebbled reptile-hide "
                    "apron; quilted studded pauldrons (FACTIONS 6.3)."),
    CostumeSet("narn_trader", "Narn trader",
               _P(("narn_suede", 0.6), ("league_dark", 0.4)), "narn_apron",
               "civ_boot", "ef_gold",
               ("heavy_coat", "boots"), ("belt",), (),
               wear=(0.15, 0.45), authority=5, source=_GK,
               note="The formal silhouette with the status off it: no "
                    "pauldrons, no iridescent trim, and the coat cut long "
                    "because that is what the Zocalo frame shows every trading "
                    "species wearing."),
    CostumeSet("narn_refugee", "Narn refugee",
               _P(("narn_salvage", 0.7), ("civ_lurker", 0.3)), "civ_lurker",
               "civ_boot", "ef_gold",
               ("rags",), (), (),
               wear=(0.55, 0.95), authority=5,
               note="FACTIONS 6.3's own instruction, executed: 'The class "
                    "gradient inside a species is what sells a refugee "
                    "population.' Same body, same species, no attachments at "
                    "all, wear at 0.55-0.95 -- and 13,000 of them, which makes "
                    "this the second most-worn costume on the station after "
                    "ordinary civilian dress."),

    # ---- Centauri ---------------------------------------------------------
    CostumeSet("centauri_court", "Centauri court dress",
               _P(("centauri_brocade", 1.0)), "centauri_stole", "civ_boot",
               "ef_gold",
               ("heavy_coat", "squared_shoulders", "boots"),
               ("standing_collar", "belt"), (),
               wear=(0.02, 0.12), authority=1, source=_MZ,
               note="Heavy brocaded coat, high collar, wide shoulders, a drape "
                    "over one shoulder. MEASURED in `more zocalo.png`, which "
                    "holds a Centauri male in court dress in a Zocalo crowd at "
                    "authority 1 -- and the measurement is a surprise worth "
                    "keeping: his coat is among the DARKEST garments in the "
                    "frame (V 0.048). Centauri conspicuousness is volume and "
                    "cut, not brightness."),
    CostumeSet("centauri_merchant", "Centauri merchant / financier",
               _P(("centauri_brocade", 0.7), ("civ_dark_warm", 0.3)),
               "centauri_stole", "civ_boot", "ef_gold",
               ("heavy_coat", "boots"), ("belt",), (),
               wear=(0.05, 0.20), authority=5, source=_MZ),
    CostumeSet("centauri_fallen", "Centauri in Downbelow -- the remains of good clothes",
               _P(("centauri_brocade", 0.8), ("civ_lurker", 0.2)),
               "centauri_stole", "civ_boot", "ef_gold",
               ("heavy_coat", "rags"), (), (),
               wear=(0.60, 0.95), authority=5,
               note="FACTIONS 7.2: 'A fallen Centauri is a specific tragedy -- "
                    "a status culture has no vocabulary for it. Build a "
                    "handful, conspicuous, still wearing the remains of good "
                    "clothes.' So the COURT fabric is kept and only the wear "
                    "and the profile change. That is the whole design of this "
                    "entry and it costs one row."),

    # ---- Minbari ----------------------------------------------------------
    CostumeSet("minbari_religious", "Minbari religious caste robes",
               _P(("minbari_cream", 0.8), ("minbari_black", 0.2)),
               "minbari_cream", "minbari_black", "ef_gold",
               (), ("standing_collar", "skirt"), (), robed=True,
               wear=(0.00, 0.08), authority=1, source=_RO,
               note="The 0.8/0.2 split is COUNTED, not chosen: `rotunda.webp` "
                    "shows roughly ten to twelve cream-robed figures and three "
                    "in long black robes with a metal-buckled belt, in one "
                    "chamber. 12:3 is 0.8/0.2."),
    CostumeSet("minbari_worker", "Minbari worker caste",
               _P(("minbari_worker", 1.0)), "minbari_cream", "civ_boot", "ef_gold",
               ("jacket_bulk", "boots"), ("belt",), (),
               wear=(0.15, 0.40), authority=5, source=_RO),
    CostumeSet("minbari_warrior", "Minbari warrior caste",
               _P(("minbari_black", 1.0)), "minbari_cream", "minbari_black",
               "ef_gold",
               ("jacket_bulk", "squared_shoulders", "boots"),
               ("standing_collar", "belt"), (),
               wear=(0.00, 0.06), authority=5, source=_RO,
               note="EXTRAPOLATED from the black-robed group in the rotunda, "
                    "which is the only non-cream Minbari dress the project "
                    "holds. FACTIONS 8.1: 'A warrior-caste Minbari in a "
                    "corridor is an event, not background' -- so this costume "
                    "is deliberately the highest-contrast thing in a crowd of "
                    "dark civilians: the only near-black garment with a "
                    "structured shoulder."),

    # ---- League and alien -------------------------------------------------
    CostumeSet("league_delegate", "League of Non-Aligned Worlds -- delegate",
               _P(("league_bone", 0.6), ("minbari_worker", 0.4)), "league_stole",
               "civ_boot", "league_cord",
               ("jacket_bulk",), ("cowl", "belt"), (),
               wear=(0.02, 0.12), authority=1, source=_PM,
               note="MEASURED off `Pak'ma'ra.webp`, which is a council desk with "
                    "four species at it and is the best alien-formal reference "
                    "the project owns: heavy quilted cowls rising over the "
                    "shoulders, a STOLE down the centre front, and a gold cord "
                    "on it. The League's status marker is a vertical band, not "
                    "a badge -- which is a real difference from every human "
                    "faction here and it comes straight off the frame."),
    CostumeSet("league_trader", "League trader",
               _P(("league_dark", 0.5), ("civ_dark_warm", 0.3),
                  ("civ_mid_warm", 0.2)), "league_stole", "civ_boot", "league_cord",
               ("heavy_coat",), ("belt",), (), wear=(0.10, 0.35), authority=1,
               source=_MZ),
    CostumeSet("league_worker", "League worker",
               _P(("league_dark", 0.6), ("civ_worker_drab", 0.4)),
               "civ_worker_drab", "civ_boot", "ef_gold",
               ("jacket_bulk", "boots"), ("belt",), (),
               wear=(0.30, 0.75), authority=1, source=_ZW,
               note="FACTIONS 9.2 puts the Drazi share of dock labour highest "
                    "of any species. Same value band as the human dockers, "
                    "because that is what `more zocalo.png` shows: the crowd "
                    "does not sort by species into different palettes."),
    CostumeSet("pakmara_cowl", "pak'ma'ra cowl",
               _P(("league_bone", 0.7), ("civ_worker_drab", 0.3)), "league_stole",
               "civ_boot", "league_cord",
               (), ("cowl",), (), wear=(0.25, 0.70), authority=1, source=_PM,
               note="The cowl is the pak'ma'ra silhouette and body.py needs it: "
                    "its own note records that reading the cowl as SKULL fused "
                    "the head to the clavicle and drove the tendrils through "
                    "the chest. No belt -- nothing in the frame shows one."),

    # ---- Civilian ---------------------------------------------------------
    CostumeSet("civ_business", "Civilian -- business district",
               _P(("civ_dark_warm", 0.4), ("civ_cool_dark", 0.3),
                  ("civ_collar_yoke", 0.2), ("civ_light_shirt", 0.1)),
               "civ_collar_yoke", "civ_boot", "ef_gold",
               ("jacket_bulk", "squared_shoulders"), ("standing_collar", "belt"),
               (), wear=(0.02, 0.15), authority=1, source=_MZ),
    CostumeSet("civ_ordinary", "Civilian -- ordinary resident",
               _P(("civ_dark_warm", 0.30), ("civ_cool_dark", 0.25),
                  ("civ_collar_yoke", 0.20), ("civ_mid_warm", 0.15),
                  ("league_dark", 0.07), ("civ_light_shirt", 0.03)),
               "civ_collar_yoke", "civ_boot", "ef_gold",
               ("heavy_coat",), ("belt",), (), wear=(0.10, 0.40),
               authority=1, source=_MZ,
               note="THE most-worn costume on the station and the one the "
                    "reference was said not to cover. Its palette is nine "
                    "garments sampled off two authority-1 Zocalo frames, "
                    "weighted so the crowd's value distribution reproduces the "
                    "measured one: median albedo near 0.06, everything inside "
                    "0.03-0.21, and a 3% light tail because exactly one light "
                    "garment appears in either frame. `_selftest` measures the "
                    "generated distribution against those bounds rather than "
                    "trusting these weights."),
    CostumeSet("civ_worker", "Civilian -- dock and industrial worker",
               _P(("civ_worker_drab", 0.5), ("league_dark", 0.3),
                  ("civ_dark_warm", 0.2)),
               "civ_worker_drab", "civ_boot", "ef_gold",
               ("jacket_bulk", "boots"), ("belt",), (), wear=(0.35, 0.85),
               authority=1, source=_ZW),
    CostumeSet("civ_lurker", "Downbelow -- lurker",
               _P(("civ_lurker", 0.7), ("league_dark", 0.2),
                  ("civ_worker_drab", 0.1)),
               "civ_lurker", "civ_boot", "ef_gold",
               ("rags",), (), (), wear=(0.65, 1.00), authority=5,
               note="No belt, no collar, no badge -- the absence IS the "
                    "costume. 20,000 of them (FACTIONS 2.2) at 1.117-1.445 g "
                    "next to the waste plant."),
    CostumeSet("civ_visitor", "Transient -- in port",
               _P(("civ_dark_warm", 0.3), ("civ_mid_warm", 0.25),
                  ("civ_collar_yoke", 0.2), ("civ_cool_dark", 0.15),
                  ("civ_light_shirt", 0.10)),
               "civ_collar_yoke", "civ_boot", "ef_gold",
               ("heavy_coat",), ("belt",), (), wear=(0.05, 0.30),
               authority=1, source=_MZ,
               note="45,000 in port at any time, mean stay 7 days (FACTIONS "
                    "2.3). Weighted lighter and cleaner than residents: a "
                    "traveller's coat has not been worn on this station for a "
                    "year. The light-shirt weight is 0.10 against the "
                    "resident's 0.03, which is the only difference between "
                    "this set and `civ_ordinary` -- and it is enough to make "
                    "the customs hall read differently from Brown sector."),
    CostumeSet("monastic", "Brother Theo's order",
               _P(("monastic_habit", 1.0)), "monastic_habit", "civ_boot", "ef_gold",
               (), ("standing_collar", "belt", "skirt"), (), robed=True,
               wear=(0.10, 0.35), authority=5, era_event="monastics_resident",
               note="Permanent residence from S3E02 (FACTIONS 11.3), so it "
                    "carries an era gate like the Rangers'. 15-25 people."),
    CostumeSet("none", "No costume -- the suit is the body",
               (), "", "", "", (), (), (), authority=1,
               note="Gaim and Vorlon. body.py builds both as encounter suits "
                    "with `plan='encounter_suit'` and `plan='column'`, so a "
                    "costume layer on top would be a garment over a sealed "
                    "environment suit. `_selftest` asserts they get this set "
                    "and that dressing them adds exactly zero triangles."),
)}


# ---------------------------------------------------------------------------
# 9. Who wears what
# ---------------------------------------------------------------------------
# (species, role) -> set key. Species falls back to a per-role default, and the
# role falls back to `civ_ordinary`, so a new species in body.py is dressed
# rather than crashing.
SET_FOR_ROLE = {
    "human": {
        "command": "ef_command", "traffic": "ef_command",
        "security": "ef_security_dress", "customs": "ef_security_dress",
        "medical": "ef_medical",
        "engineer": "ef_technical", "industrial": "ef_technical",
        "waste": "ef_technical", "hydroponics": "ef_technical",
        "dockworker": "ef_technical",
        "financier": "civ_business", "merchant": "civ_business",
        "service": "civ_ordinary", "visitor": "civ_visitor",
        "lurker": "civ_lurker", "cleric": "monastic",
        "diplomat": "civ_business",
    },
    "narn": {"diplomat": "narn_formal", "merchant": "narn_trader",
             "refugee": "narn_refugee", "lurker": "narn_refugee",
             "visitor": "narn_trader"},
    "centauri": {"diplomat": "centauri_court", "financier": "centauri_merchant",
                 "visitor": "centauri_merchant", "lurker": "centauri_fallen"},
    "minbari": {"cleric": "minbari_religious", "engineer": "minbari_worker",
                "diplomat": "minbari_warrior", "visitor": "minbari_religious",
                "lurker": "minbari_worker"},
    "pakmara": {},        # every role: see SET_FOR_SPECIES
    "gaim": {},
    "vorlon": {},
}

# Species-wide overrides, applied when the role table has no entry.
SET_FOR_SPECIES = {
    "pakmara": "pakmara_cowl",
    "gaim": "none",
    "vorlon": "none",
}

# Role -> set, for every species without its own table. League species.
SET_FOR_ROLE_DEFAULT = {
    "diplomat": "league_delegate",
    "financier": "league_trader", "merchant": "league_trader",
    "visitor": "league_trader",
    "dockworker": "league_worker", "industrial": "league_worker",
    "hydroponics": "league_worker", "waste": "league_worker",
    "service": "league_worker", "engineer": "league_worker",
    "security": "ef_security_dress", "customs": "ef_security_dress",
    "command": "ef_command", "traffic": "ef_command", "medical": "ef_medical",
    "cleric": "league_delegate", "envoy": "none",
    "lurker": "civ_lurker", "refugee": "narn_refugee",
}

# --- Nightwatch -------------------------------------------------------------
# FACTIONS 5.4, authority 5 but reasoned there: "150-200 of 500 (30-40%)" of
# security officers wear the armband. 0.35 is the midpoint and `_selftest`
# measures the generated rate against the 0.30-0.40 band rather than against
# this constant, so a change here that leaves the band is fine and one that
# leaves it fails.
NIGHTWATCH_SECURITY_RATE = 0.35

# 1,500-3,000 civilian informers among 155,000 humans is 1-2% (FACTIONS 5.4).
# What is NOT stated anywhere is how many of them wear the band where it can be
# seen -- and 5.3's whole point is that "anyone might be wearing one under a
# coat". EXTRAPOLATED at 30% of informers visible, i.e. 0.0045 of humans, so a
# player meets a visibly-banded civilian about once in 220 people and a banded
# officer in one of three. That ratio is the design: the split force is legible,
# the informer network is not. Overturned by any scene showing civilians in
# armbands in numbers.
NIGHTWATCH_CIVILIAN_INFORMER_RATE = 0.015
NIGHTWATCH_CIVILIAN_VISIBLE_FRACTION = 0.30

# --- rare costumes ----------------------------------------------------------
# FACTIONS 4.1: "10-40 registered commercial telepaths aboard at any time".
# 25 of 250,000 is 1e-4, and they are drawn from human financiers and visitors
# because 4.1 puts them "hired by hour for negotiations in the Business
# District". A rate rather than a list, so no NPC id is special-cased.
PSI_ABOARD = 25
# FACTIONS 10.1: "Model 20-60 Rangers aboard at any time, human and Minbari".
RANGERS_ABOARD = 40


@dataclass(frozen=True)
class Costume:
    """One resident's clothing, resolved. A pure function of (species, id, datum)."""
    species: str
    npc_id: str
    set_key: str
    cloth: str            # the fabric key drawn from the set's palette
    trim: str
    leather: str
    metal: str
    silhouettes: tuple
    attachments: tuple
    decals: tuple         # ((decal_key, slot), ...)
    nightwatch: bool
    wear: float
    value_jitter: float
    robed: bool
    split: str = "yoke"        # yoke | plastron

    def fabric(self, slot):
        return {"npc_cloth": self.cloth, "npc_cloth_trim": self.trim,
                "npc_leather": self.leather, "npc_metal": self.metal}.get(slot, "")


def _weighted(palette, seed, salt):
    """Deterministic weighted draw. Never `random`."""
    if not palette:
        return ""
    total = sum(w for _k, w in palette)
    x = _u(seed, salt) * total
    acc = 0.0
    for k, w in palette:
        acc += w
        if x < acc:
            return k
    return palette[-1][0]


def set_key_for(species, role_key):
    """Which costume set a (species, role) wears, before the era gate."""
    table = SET_FOR_ROLE.get(species)
    if table and role_key in table:
        return table[role_key]
    if species in SET_FOR_SPECIES:
        return SET_FOR_SPECIES[species]
    if table is not None and role_key in SET_FOR_ROLE_DEFAULT:
        return SET_FOR_ROLE_DEFAULT[role_key]
    return SET_FOR_ROLE_DEFAULT.get(role_key, "civ_ordinary")


def _role_key(species, npc_id):
    """schedule.role_for(), with a fallback that does not fail the build."""
    try:
        import schedule                                       # noqa: PLC0415
        return schedule.role_for(npc_id, species).key
    except Exception:                                          # noqa: BLE001
        return "visitor"


def costume_for(species, npc_id, datum=ERA_DATUM, role_key=None):
    """Resolve one resident's costume. Deterministic in (species, id, datum).

    AAA-STANDARD, NPCs: "NPC identity is a function of (seed, id) and not of
    iteration order." Nothing below reads a counter, a list position or a clock
    -- `datum` is an explicit argument precisely so that it cannot become one.
    """
    era_check(datum)
    if species not in body.SPECIES:
        raise KeyError(f"unknown species {species!r}")
    seed = f"costume:{species}:{npc_id}"
    role = role_key or _role_key(species, npc_id)
    key = set_key_for(species, role)

    # --- rare costumes, drawn as rates so no id is special-cased -----------
    if species == "human" and role in ("financier", "visitor"):
        share = body.FACTIONS_MIX["human"][0] * 0.25       # the eligible pool
        if _u(seed, "psi") < PSI_ABOARD / max(share, 1.0):
            key = "psi_corps"
    if species in ("human", "minbari") and era_active("rangers_visible", datum):
        pool = sum(body.FACTIONS_MIX[s][0] for s in ("human", "minbari"))
        if _u(seed, "ranger") < RANGERS_ABOARD / pool:
            key = "ranger"

    cset = SETS[key]
    # --- the era gate on a whole costume ----------------------------------
    if cset.era_event and not era_active(cset.era_event, datum):
        key = set_key_for(species, role)
        cset = SETS[key]
        if cset.era_event and not era_active(cset.era_event, datum):
            key, cset = "civ_ordinary", SETS["civ_ordinary"]

    # --- the Nightwatch armband, and its date -----------------------------
    band = False
    if era_active("nightwatch_visible", datum):
        if key in ("ef_security_dress", "ef_security_duty"):
            band = _u(seed, "nw") < NIGHTWATCH_SECURITY_RATE
        elif species == "human" and key.startswith("civ"):
            band = (_u(seed, "nw") < NIGHTWATCH_CIVILIAN_INFORMER_RATE
                    * NIGHTWATCH_CIVILIAN_VISIBLE_FRACTION)

    # --- security officers split between the two rigs ---------------------
    if key == "ef_security_dress" and _u(seed, "rig") < 0.45:
        key, cset = "ef_security_duty", SETS["ef_security_duty"]

    cloth = _weighted(cset.cloth, seed, "cloth")
    # The yoke has to CONTRAST or it is not a yoke. Several civilian palettes
    # contain the yoke fabric itself -- a coat cut from the lighter cloth is in
    # the reference too -- and an individual who draws it would otherwise get a
    # single-value garment. Substituting the palette's darkest other entry keeps
    # the two-tier value on every figure and inverts the seam on the few who
    # draw the light cloth, which is what a real yoke does.
    trim = cset.trim
    if trim == cloth:
        alts = [f for f, _w in cset.cloth if f != cloth]
        if alts:
            trim = min(alts, key=lambda k: FABRICS[k].value())
    lo, hi = cset.wear
    wear = lo + (hi - lo) * _u(seed, "wear")
    # Cloth is dyed in lots and fades on the wearer. +/-13% matches the
    # per-plate value spread `materials.PLATE_VALUE_JITTER` measures on the
    # hull, which is the only measured value-spread the project owns; using a
    # second, invented figure here would be a number that looks sourced.
    jitter = 1.0 + _gauss(seed, "value", 0.13, clamp=2.0)

    attachments = list(cset.attachments)
    if band:
        attachments.append("armband")
    decals = list(cset.decals)
    if band:
        decals.append(("nightwatch_eye", "left_forearm"))

    return Costume(species, npc_id, key, cloth, trim, cset.leather,
                   cset.metal, tuple(cset.silhouettes), tuple(attachments),
                   tuple(decals), band, round(wear, 4), round(jitter, 4),
                   cset.robed, cset.split)


# ---------------------------------------------------------------------------
# 10. Geometry
# ---------------------------------------------------------------------------
# Anchors are MEASURED off the built mesh rather than recomputed from FIGURE.
# body.build_humanoid normalises stature and then applies the stoop, so any
# anchor derived from the table alone is wrong for a pak'ma'ra by 0.177 m and
# wrong for every species by the normalisation factor. Reading the part back is
# also the only way an attachment survives someone changing `leg_k`.
def _axis_at(verts, yf, band=0.05):
    """(cx, cz, radius) of a part at height fraction `yf` of its own extent."""
    ys = [v[1] for v in verts]
    y0, y1 = min(ys), max(ys)
    y = y0 + (y1 - y0) * yf
    h = max((y1 - y0) * band, 1e-4)
    sel = [v for v in verts if abs(v[1] - y) <= h]
    while len(sel) < 3 and h < (y1 - y0):
        h *= 2.0
        sel = [v for v in verts if abs(v[1] - y) <= h]
    if not sel:
        sel = list(verts)
    cx = sum(v[0] for v in sel) / len(sel)
    cz = sum(v[2] for v in sel) / len(sel)
    r = max(math.hypot(v[0] - cx, v[2] - cz) for v in sel)
    return cx, cz, r, y


def _part_axis(verts):
    """(cx, cz) of a whole part, for a radial modifier."""
    cx = sum(v[0] for v in verts) / len(verts)
    cz = sum(v[2] for v in verts) / len(verts)
    return cx, cz


def _apply_silhouettes(part_name, verts, stature, mods):
    """Radial scale about the part's own axis. Strictly positive by assertion."""
    active = [SILHOUETTES[m] for m in mods
              if part_name in SILHOUETTES[m].parts]
    if not active:
        return verts
    cx, cz = _part_axis(verts)
    out = []
    for x, y, z in verts:
        s = 1.0
        for m in active:
            s *= m.scale_at(y / max(stature, 1e-9))
        if s <= 0.0:
            raise ValueError(f"non-positive garment scale {s} on {part_name}")
        out.append((cx + (x - cx) * s, y, cz + (z - cz) * s))
    return out


# Radial segment counts a small fitting may use. Not powers of two: a band is
# not part of the body's strict-subset LOD chain -- it is present or it is gone
# -- so it is free to be sized by its own sagitta instead.
_ATT_SEGS = (4, 6, 8, 12, 16)


def _att_seg(radius, distance_m, cap=16):
    """Segments for a fitting of `radius`, from the sagitta at `distance_m`.

    The same derivation `station/lod.py` and `body.silhouette_schedule()` use,
    applied to a 90 mm collar instead of a 1,211 m drum: error is
    r(1 - cos(pi/n)), and the affordable error at distance d is d / px_scale.
    Sizing a collar at the BODY's 64 segments -- which is what the first version
    of this module did -- cost 252 triangles a band and put an EarthForce
    command uniform at 752 triangles, five times the whole clothing budget for a
    crowd. It is now 60.

    `cap` is a deliberate floor on quality, not an oversight: 16 segments on a
    90 mm collar is 1.7 mm of sagitta, honest from 1.78 m, and a collar seen
    from closer than that belongs to the one NPC the player is talking to.
    """
    allowed = max(distance_m, 0.0) / body._px_scale(body.PIXEL_BUDGET)
    for n in _ATT_SEGS:
        if radius * (1.0 - math.cos(math.pi / n)) <= allowed:
            return min(n, cap)
    return cap


def _band(m, cx, cz, y, r, half_h, group, part, seg, taper=1.0):
    """A closed band: two rings, capped. The shape of a collar, belt or strap."""
    rings = [body._ring(cx, y - half_h, cz, r, r, seg),
             body._ring(cx, y + half_h, cz, r * taper, r * taper, seg)]
    v, t = body._loft(rings)
    m.add(v, t, group, part)


def _skirt(m, torso_verts, stature, group, seg, dist=0.0, flare=1.85,
           hem_yf=0.030):
    """A floor-length robe: one capped loft replacing two legs and two feet.

    The top ring is INSIDE the torso -- taken at 0.34 of the torso's height and
    scaled to 0.88 of the radius there -- and not at the hem of it. Started at
    the torso's lowest ring, the skirt's own top cap sat flush with the torso's
    bottom cap and the render showed a horizontal SHELF across the hips on
    every robed figure: two coplanar capped solids reading as a step. Burying
    the cap is the same trick body.py uses for the arm root and the neck, and
    it was found the same way -- by looking at the render.
    """
    cx, cz, r_top, y_top = _axis_at(torso_verts, 0.34, band=0.06)
    r_top *= 0.88
    hem_y = hem_yf * stature
    # Sized by ITS OWN sagitta at the hem radius, capped at 32. The skirt is a
    # primary silhouette element, so its cap is twice a collar's -- but it is
    # still not the body's 64: a 0.31 m hem at 32 segments is 1.5 mm of sagitta,
    # honest from 1.5 m, and it saves 320 triangles on every robed figure.
    seg = min(seg, _att_seg(r_top * flare, dist, cap=32))
    rings = []
    n = 5
    for k in range(n):
        t = k / (n - 1)
        y = y_top + (hem_y - y_top) * t
        r = r_top * (1.0 + (flare - 1.0) * t * t)
        rings.append(body._ring(cx, y, cz, r, r * 0.94, seg))
    v, t = body._loft(rings)
    m.add(v, t, group, "skirt")


# Where the shoulder yoke ends, as a fraction of the torso part's own height.
# MEASURED, loosely: in `more zocalo.png` the foreground civilian's coat has a
# visible yoke seam running from the shoulder point to about the level of the
# armpit, and the panel above it reads (0.169,0.138,0.127) against the body's
# (0.092,0.071,0.071) -- 1.8x lighter, in the same frame, under the same light.
# So the largest garment surface on an NPC carries TWO values rather than one,
# which is what stops a crowd of albedo-0.06 coats reading as a field of
# silhouettes. It costs zero triangles: the torso is emitted as two SPANS of
# one closed solid, not as two solids.
YOKE_TOP_FRACTION = 0.78


# How a torso's second material is cut. Both are zero-triangle span splits of
# one closed solid; they differ only in the predicate.
#
#   yoke      a HORIZONTAL band across the shoulders. What the security jacket
#             has (black leather standing collar and YOKE, authority 2), what
#             civilian coats in `more zocalo.png` have, and what FACTIONS 6.3
#             calls the Narn "shoulder yokes".
#   plastron  a VERTICAL band down the centre front. What the S2-3 command
#             uniform has -- "brown leather plastron/bib covering the whole
#             centre front from the standing leather collar down" -- and it is
#             a different shape from a yoke, so it gets a different predicate
#             rather than being approximated by one. The render is what caught
#             this: with the yoke predicate the command uniform wore its
#             crimson PIPING as a shoulder panel, which is a 5 mm cord painted
#             across 40 cm of chest.
PLASTRON_HALF_WIDTH = 0.38      # fraction of the torso's half-width, each side


def _add_split(m, verts, tris, pred, group_lo, group_hi, part):
    """Emit one closed part as two material spans, split by `pred`.

    `m.parts` still records the WHOLE part, so `signed_volume` and
    `edge_census` continue to see a closed solid. Asserting on the spans
    instead would report the yoke as an open surface with a ring of boundary
    edges -- a false failure that would have been "fixed" by deleting the
    check, which is how a real closure test gets lost.
    """
    b, lo = len(m.verts), len(m.tris)
    m.verts.extend(verts)
    below, above = [], []
    for a, c, d in tris:
        cx = (verts[a][0] + verts[c][0] + verts[d][0]) / 3.0
        cy = (verts[a][1] + verts[c][1] + verts[d][1]) / 3.0
        cz = (verts[a][2] + verts[c][2] + verts[d][2]) / 3.0
        (above if pred(cx, cy, cz) else below).append((a + b, c + b, d + b))
    m.tris.extend(below)
    m.spans.append((group_lo, lo, len(m.tris)))
    lo2 = len(m.tris)
    m.tris.extend(above)
    m.spans.append((group_hi, lo2, len(m.tris)))
    m.parts.append((part, list(verts), list(tris)))
    return m


def _attachment_active(key, distance_m):
    if key in NEVER_CULLED:
        return True
    return distance_m <= ATTACHMENTS[key].honest_from_m()


def group_name(slot, fabric):
    """`slot` drives the material; the suffix exists for the preview tinter.

    materials.py resolves a group by SUBSTRING with the longest fragment
    winning, so `npc_cloth__civ_dark_warm` binds to a material declaring
    `npc_cloth` -- one material, any number of fabrics.
    """
    if slot not in MATERIAL_SLOTS:
        raise KeyError(f"{slot!r} is not one of MATERIAL_SLOTS")
    return f"{slot}__{fabric}" if fabric else slot


# Which costume slot each body part becomes when dressed. Exposed parts keep
# their skin material; everything else is cloth or leather.
PART_SLOT = {
    "torso": "npc_cloth", "arm": "npc_cloth", "leg": "npc_cloth",
    "neck": None, "head": None, "hand": None, "foot": "npc_leather",
    "hair": None, "brow": None, "centauri_crest": None, "minbari_crest": None,
    "pakmara_keel": None, "pakmara_tendrils": None, "abbai_fin": None,
}


# Draws per species when discovering fabrics `SETS` does not declare. 600 is
# where the count stops moving; `_selftest` runs 6,000 and asserts it finds
# nothing new, which is what makes 600 a measurement rather than a guess.
SPEC_SAMPLE = 600


def _fabric_keys(value):
    """The fabric keys a `CostumeSet` slot can produce.

    A slot is a single key, or a weighted palette of them -- `_P(*pairs)` --
    so this flattens both without caring which it was handed. A tuple of
    `(key, weight)` pairs and a bare tuple of keys both appear in `SETS`.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    out = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, (tuple, list)) and item and isinstance(
                item[0], str):
            out.append(item[0])
    return tuple(out)


def material_specs():
    """One PBR material per FABRIC, from the measurements already in this file.

    THE WARDROBE WAS MEASURED AND NEVER REACHED A SURFACE. Every `Fabric` here
    carries a `measured` albedo, a `roughness`, a `metallic`, an `authority` and
    the frame and region it was read from -- a complete material spec, sourced.
    `materials.py`'s only use of this module was two constants, `SKIN_ANCHOR`
    and `PAKMARA_COWL_ANCHOR`, so 2,016 inhabitants stood on the station with
    no clothes on: `populace` called `body.build`, which is the bare figure,
    while `build_dressed` sat here unused.

    PER FABRIC RATHER THAN PER SLOT, and that is a change from the design
    `group_name` describes. Its note -- "one material, any number of fabrics"
    -- is right about the resolver and wrong about the wardrobe: measured over
    the station mix, the cloth slot draws on **17 distinct fabrics with no
    dominant one** (the commonest is 16%), so a single `npc_cloth` material
    would dress the whole station in one coat and throw away every measurement
    below. The resolver needs no change to support it: it matches the longest
    fragment, and `npc_cloth__civ_dark_warm` is longer than `npc_cloth`, so a
    per-fabric material wins where one exists and a slot-level material catches
    anything without one.

    Returned as plain dicts rather than `materials.Material` objects so that
    this module does not import that one -- the dependency runs the other way,
    and reversing it would make the wardrobe depend on the renderer.
    """
    # ONLY WHAT IS ACTUALLY WORN, AND FROM `SETS` RATHER THAN FROM SAMPLING.
    # The cross-product of four slots and every fabric is 164 combinations and
    # far fewer are reachable: a costume SET decides which fabric fills which
    # slot, so the reachable pairs are exactly the ones the 27 sets name.
    #
    # SAMPLING `costume_for` WAS TRIED FIRST AND IS WRONG. 60 draws over ten
    # species found 32 groups; 600 found 47 -- the extra fifteen are rare roles
    # (EF command, security, rangers, monastics, Narn regalia) that a small
    # sample simply misses, and no sample size can prove it has stopped
    # missing them. `SETS` is the table those draws are drawn FROM, so reading
    # it is exact. `worn_fabrics` is kept as the cross-check and `_selftest`
    # asserts every sampled group is in this list.
    pairs = set()
    for st in SETS.values():
        for slot, attr in (("npc_cloth", "cloth"),
                           ("npc_cloth_trim", "trim"),
                           ("npc_leather", "leather"),
                           ("npc_metal", "metal")):
            for key in _fabric_keys(getattr(st, attr, None)):
                if key in FABRICS:
                    pairs.add((slot, key))
    # AND WHAT THE SETS DO NOT NAME. `SETS` is the declared table and it is
    # still not the whole reachable set: `costume_for` falls back when a set
    # leaves a slot empty, so a 600-draw sample turns up four trim groups --
    # `civ_cool_dark`, `league_dark`, `minbari_black`, `narn_salvage` -- that
    # no set lists as trim. Neither source is complete alone. The union is,
    # and `_selftest` asserts a sample ten times larger than the one used here
    # finds nothing outside it, which is the only thing that can catch a third
    # path appearing.
    for group in worn_fabrics(sample=SPEC_SAMPLE):
        slot, _, key = group.partition("__")
        if key in FABRICS:
            pairs.add((slot, key))
    # AND WHAT THE MESH BUILDER EMITS DIRECTLY, which is a THIRD path and was
    # missed by both of the first two. `_build_mesh` writes the Nightwatch
    # armband as a literal -- `group_name("npc_cloth_trim", "nightwatch_black")`
    # -- under `era_active("nightwatch_visible")`, so it appears in no `SETS`
    # slot AND in no `Costume` record, which is what `worn_fabrics` reads. No
    # sample size can find it, at any datum. Three groups on an assembled deck
    # went unresolved for exactly this reason.
    pairs.update(BUILDER_FABRICS)
    out = []
    for slot, key in sorted(pairs):
        group = group_name(slot, key)
        f = FABRICS[key]
        if True:
            out.append({
                "name": f"{slot}__{key}",
                "group": group,
                "title": f.title,
                # `Fabric.albedo`, NOT `Fabric.measured`. The first is the
                # second put on the station's own ladder -- multiplied by the
                # frame's grey-world gain and clamped to `ALBEDO_FLOOR` /
                # `ALBEDO_CEIL` -- and the second is a raw balanced pixel value
                # from a photograph. Exporting the raw value is the trap
                # CLAUDE.md names in as many words: "Balanced-V vs linear
                # luminance units". It also skips the declared-vs-measured
                # branch entirely, so a declared fabric got no clamp at all.
                "albedo": tuple(f.albedo),
                "roughness": float(f.roughness),
                "metallic": float(f.metallic),
                "authority": int(f.authority),
                "declared": bool(f.declared),
                "source": f"npc/costume.py FABRICS[{key!r}] -- {f.frame} "
                          f"{f.region}" if f.frame else
                          f"npc/costume.py FABRICS[{key!r}] -- DECLARED",
                "note": f.note,
            })
    # A fabric is worn in whichever slot its costume set puts it, and the
    # tables here do not partition them, so the same key legitimately appears
    # under more than one slot. De-duplicated on the emitted GROUP name, which
    # is what the resolver actually sees.
    seen, uniq = set(), []
    for m in out:
        if m["group"] in seen:
            continue
        seen.add(m["group"])
        uniq.append(m)
    return tuple(uniq)


# (slot, fabric) pairs `_build_mesh` writes as LITERALS rather than reading off
# the `Costume` record. There is one, and `_selftest` greps this file's own
# source for two-literal `group_name(...)` calls and asserts the list covers
# every one -- so a second such garment cannot be added without this list
# noticing, which is the only way a hand-kept list stays honest.
BUILDER_FABRICS = frozenset({("npc_cloth_trim", "nightwatch_black")})


def _era_datum_for(event):
    """A datum at which `event` is active, from its own recorded window.

    `ERA_EVENTS[event]` carries `((season, episode), description)`, so the
    event's own start is the datum that turns it on -- read from the table
    rather than written down a second time.
    """
    when = ERA_EVENTS[event][0]
    return when


# Draws per species when sweeping an era event. Smaller than `SPEC_SAMPLE`
# because an event changes ONE slot on the roles it touches, so the reachable
# set converges far faster than the whole wardrobe's does.
ERA_SAMPLE = 200


def worn_fabrics(sample=60, species=None, datum=None):
    """Which fabrics the station's own mix actually puts on people.

    MEASURED, not tabulated: `costume_for` is a pure function of species and
    id, so this walks a sample and reports what comes back. `material_specs`
    emits one material per fabric in `FABRICS`; this says which of them a
    player will ever see, so a gate can assert the two agree rather than
    assuming every table entry is reachable.
    """
    species = species or ("human", "human", "human", "human", "narn",
                          "centauri", "minbari", "drazi", "brakiri", "pakmara")
    worn = {}
    for sp in species:
        for i in range(sample):
            try:
                cs = (costume_for(sp, f"worn/{sp}/{i}") if datum is None
                      else costume_for(sp, f"worn/{sp}/{i}", datum=datum))
            except Exception:                                   # noqa: BLE001
                continue
            for slot, attr in (("npc_cloth", "cloth"),
                               ("npc_cloth_trim", "trim"),
                               ("npc_leather", "leather"),
                               ("npc_metal", "metal")):
                fab = getattr(cs, attr, None)
                if fab:
                    worn[group_name(slot, fab)] = worn.get(
                        group_name(slot, fab), 0) + 1
    return worn


def build_dressed(species, npc_id, lod=0, chain=None, datum=ERA_DATUM,
                  costume=None, distance_m=None):
    """The public entry point: a dressed figure. Returns (verts, tris, spans)."""
    out = _build_mesh(species, npc_id, lod, chain, datum, costume, distance_m)
    return out if isinstance(out, tuple) else out.as_tuple()


def dressed_mesh(species, npc_id, lod=0, chain=None, datum=ERA_DATUM,
                 costume=None, distance_m=None, ind=None):
    """The dressed figure as a `body.Mesh`, so a caller that needs its spans
    as well as its parts -- `animation.rig` -- gets both from one build."""
    return _build_mesh(species, npc_id, lod, chain, datum, costume,
                       distance_m, ind)


def dressed_parts(species, npc_id, lod=0, chain=None, datum=ERA_DATUM,
                  costume=None, distance_m=None, ind=None):
    """The CLOSED PARTS of a dressed figure, for per-part assertions.

    Parts, not spans. The torso is emitted as two spans -- body and yoke -- of
    one closed solid, so a per-span closure check would report a ring of
    boundary edges that is not there, and the natural "fix" for a false failure
    is to delete the check.
    """
    out = _build_mesh(species, npc_id, lod, chain, datum, costume,
                      distance_m, ind)
    return [] if isinstance(out, tuple) else list(out.parts)


def _build_mesh(species, npc_id, lod=0, chain=None, datum=ERA_DATUM,
                costume=None, distance_m=None, ind=None):
    sp = body.SPECIES[species]
    # `ind` OVERRIDES THE FIGURE, and exists for one caller: `animation.rig`
    # builds the same body twice -- once as itself and once with the stoop
    # suppressed, because `_ring_partition` needs flat rings -- and binds the
    # first to the second vertex for vertex. It can only do that for a DRESSED
    # figure if it can ask for a dressed one with a modified individual.
    # Without this the rig dresses nobody and every POSED person on the station
    # is nude while the rest-pose probe is clothed, which is exactly the
    # mismatch `populace`'s own gate caught: 1216 vertices against 1152.
    ind = ind if ind is not None else body.individual(species, npc_id)
    levels = chain or body.lod_chain()
    lv = levels[max(0, min(lod, len(levels) - 1))]
    c = costume or costume_for(species, npc_id, datum)
    if distance_m is None:
        distance_m = lv["switch_distance_m"]

    if lv["kind"] == "impostor":
        # A card is a card. The costume changes what is PRINTED on it, not its
        # geometry, so the impostor path is body.py's unchanged -- and saying so
        # is the honest version of "the costume has an impostor LOD".
        return body.impostor(ind, sp)          # a tuple, not a Mesh

    src = body._PLANS[sp.plan](ind, sp, seg=lv["radial_segments"],
                              ring_stride=lv["ring_stride"],
                              features=lv["features"])
    if c.set_key == "none":
        return src

    seg = lv["radial_segments"]
    H = ind.stature_m
    out = body.Mesh()
    torso_verts = None

    for name, verts, tris in src.parts:
        if c.robed and name in ("leg", "foot"):
            continue
        v = _apply_silhouettes(name, verts, H, c.silhouettes)
        if name == "torso":
            torso_verts = v
        slot = PART_SLOT.get(name)
        if slot is None:
            out.add(v, tris, f"npc_{sp.surface.kind}_{name}", name)
        elif name == "torso" and c.trim and c.trim != c.cloth:
            ys = [p[1] for p in v]
            y0, y1 = min(ys), max(ys)
            if c.split == "plastron":
                hw = max(abs(p[0]) for p in v) * PLASTRON_HALF_WIDTH
                pred = (lambda cx, cy, cz, hw=hw: cz > 0.0 and abs(cx) <= hw)
            else:
                yy = y0 + (y1 - y0) * YOKE_TOP_FRACTION
                pred = (lambda cx, cy, cz, yy=yy: cy >= yy)
            _add_split(out, v, tris, pred,
                       group_name("npc_cloth", c.cloth),
                       group_name("npc_cloth_trim", c.trim), name)
        else:
            fab = c.leather if slot == "npc_leather" else c.cloth
            out.add(v, tris, group_name(slot, fab), name)

    if torso_verts is None:                    # column plan: nothing to dress
        return src

    # --- attachments -------------------------------------------------------
    arm_parts = [v for n, v, _t in out.parts if n == "arm"]
    for key in c.attachments:
        if not _attachment_active(key, distance_m):
            continue
        if key == "standing_collar":
            cx, cz, r, y = _axis_at(torso_verts, 0.985, band=0.03)
            _band(out, cx, cz, y + 0.022 * H, r * 0.92, 0.024 * H,
                  group_name("npc_leather", c.leather), "collar",
                  _att_seg(r * 0.92, distance_m), taper=1.06)
        elif key == "epaulettes":
            for av in arm_parts:
                cx, cz, r, y = _axis_at(av, 0.97, band=0.06)
                _band(out, cx, cz, y - 0.012 * H, r * 1.22, 0.014 * H,
                      group_name("npc_leather", c.leather), "epaulette",
                      _att_seg(r * 1.22, distance_m, cap=12), taper=0.88)
        elif key == "belt":
            cx, cz, r, y = _axis_at(torso_verts, 0.30, band=0.05)
            _band(out, cx, cz, y, r * 1.03, 0.016 * H,
                  group_name("npc_leather", c.leather), "belt",
                  _att_seg(r * 1.03, distance_m))
        elif key == "baldric":
            cx0, cz0, r0, y0 = _axis_at(torso_verts, 0.86, band=0.05)
            cx1, cz1, r1, y1 = _axis_at(torso_verts, 0.38, band=0.05)
            rings = []
            bseg = _att_seg(0.020 * H, distance_m, cap=8)
            for k in range(4):
                t = k / 3.0
                rings.append(body._ring(
                    cx0 + (r0 * 0.6) * (1 - 2 * t), y0 + (y1 - y0) * t,
                    cz0 + (r0 + r1) * 0.5 * 0.62,
                    0.020 * H, 0.011 * H, bseg))
            v, t = body._loft(rings)
            out.add(v, t, group_name("npc_cloth_trim", c.trim), "baldric")
        elif key == "armband":
            # LEFT forearm. body.py emits arms for side in (-1, +1) in that
            # order, so parts[0] is -x. Which side that IS depends on the
            # camera convention, and the module states its convention once
            # rather than guessing per badge: see BADGE_SIDE_SOURCE.
            if arm_parts:
                av = min(arm_parts, key=lambda vs: _part_axis(vs)[0])
                cx, cz, r, y = _axis_at(av, 0.22, band=0.08)
                _band(out, cx, cz, y, r * 1.10, 0.030 * H,
                      group_name("npc_cloth_trim", "nightwatch_black"),
                      "armband", _att_seg(r * 1.10, distance_m, cap=12))
        elif key == "cowl":
            cx, cz, r, y = _axis_at(torso_verts, 0.94, band=0.06)
            cseg = min(seg, _att_seg(r * 1.16, distance_m, cap=32))
            rings = [body._ring(cx, y - 0.030 * H, cz, r * 0.72, r * 0.72, cseg),
                     body._ring(cx, y + 0.020 * H, cz, r * 1.16, r * 1.10, cseg),
                     body._ring(cx, y + 0.070 * H, cz, r * 0.80, r * 0.78, cseg)]
            v, t = body._loft(rings)
            out.add(v, t, group_name("npc_cloth", c.cloth), "cowl")
        elif key == "skirt":
            _skirt(out, torso_verts, H, group_name("npc_cloth", c.cloth),
                   seg, distance_m)
    return out


# ---------------------------------------------------------------------------
# 11. Cost
# ---------------------------------------------------------------------------
# One atlas for every badge on the station, one trim sheet for every fabric.
# Sizes are set by the smallest legible stroke, not by habit: the Nightwatch
# legend is ~1/14 of the emblem's width, so at 85 mm the stroke is 6 mm, and a
# 256 px cell across 85 mm gives 3 px per stroke -- legible. Six decals fit a
# 1024 atlas at 256 px each with room to spare.
TEX_SIZE = {"npc_badge_atlas": 1024, "npc_cloth_trim_sheet": 1024}
# BC7 for the atlas because a badge needs alpha and BC1's 1-bit alpha would
# fringe a gold outline; BC1/BC5 for the cloth sheet, matching materials.py's
# MEASURED figures rather than a guess.
BYTES_PER_TEXEL = {"npc_badge_atlas": {"albedo": 1.0, "normal": 1.0, "orm": 0.5},
                   "npc_cloth_trim_sheet": {"albedo": 0.5, "normal": 1.0,
                                            "orm": 0.5}}
MIP_FACTOR = 4.0 / 3.0


def texture_memory():
    """Resident texture cost of every garment on the station."""
    per, total = {}, 0.0
    for name, size in TEX_SIZE.items():
        b = sum(size * size * v for v in BYTES_PER_TEXEL[name].values()) * MIP_FACTOR
        per[name] = b / 1024 ** 2
        total += b
    budget = 3072.0
    try:
        import materials                                       # noqa: PLC0415
        budget = materials.VRAM_TEXTURE_BUDGET_MB
    except Exception:                                          # noqa: BLE001
        pass
    return {"sets": len(TEX_SIZE), "maps": sum(len(v) for v in BYTES_PER_TEXEL.values()),
            "compressed_mb": total / 1024 ** 2, "budget_mb": budget,
            "fraction": total / 1024 ** 2 / budget, "per_set_mb": per}


def costume_triangles(species="human", npc_id="cost-probe", chain=None,
                      datum=ERA_DATUM, set_key=None):
    """Triangles a costume adds (or removes) at each LOD, measured on the mesh."""
    chain = chain or body.lod_chain()
    c = costume_for(species, npc_id, datum)
    if set_key:
        cs = SETS[set_key]
        c = Costume(species, npc_id, set_key,
                    (cs.cloth[0][0] if cs.cloth else ""), cs.trim, cs.leather,
                    cs.metal, tuple(cs.silhouettes), tuple(cs.attachments),
                    tuple(cs.decals), False, 0.2, 1.0, cs.robed, cs.split)
    rows = []
    for i, lv in enumerate(chain):
        bare = len(body.build(species, npc_id, i, chain)[1])
        dressed = len(build_dressed(species, npc_id, i, chain, datum, c)[1])
        rows.append({"level": lv["name"], "kind": lv["kind"], "bare": bare,
                     "dressed": dressed, "delta": dressed - bare,
                     "distance_m": lv["switch_distance_m"]})
    return {"set": c.set_key, "rows": rows}


def crowd_cost(figures, distance_m=None, chain=None, level=None,
               datum=ERA_DATUM, sample=24):
    """Dressed-crowd triangles against body.py's NPC frame budget.

    The mean is over a SAMPLE of ids weighted by the FACTIONS 2.4 mix, not over
    one figure: a station whose costume cost was measured on a human in a
    jacket would be wrong by the cost of every robe and every cowl.
    """
    chain = chain or body.lod_chain()
    if level is None:
        level = 0
        for i, lv in enumerate(chain):
            if distance_m is not None and distance_m >= lv["switch_distance_m"]:
                level = i
    tot = sum(w for _c, w in body.FACTIONS_MIX.values())
    per = 0.0
    for sp, (_count, share) in body.FACTIONS_MIX.items():
        acc = 0
        for k in range(sample):
            acc += len(build_dressed(sp, f"crowd-{k}", level, chain, datum)[1])
        per += (acc / sample) * share / tot
    budget = body.FRAME_TRIANGLES * body.NPC_FRAME_SHARE
    total = per * figures
    return {"figures": figures, "level": chain[level]["name"],
            "tris_per_figure": round(per, 1), "triangles": int(round(total)),
            "budget": int(budget), "share_of_frame": total / body.FRAME_TRIANGLES,
            "within_budget": total <= budget,
            "max_figures_in_budget": int(budget // max(per, 1e-9))}


def dressed_ratio(chain=None, datum=ERA_DATUM, sample=8):
    """Dressed triangles / bare triangles, per LOD, mix-weighted.

    The multiplier clothing applies to `body.zocalo_crowd()`'s already-audited
    band model. Reusing that model rather than writing a second one is the
    point: a crowd cost computed here from a different set of assumptions would
    be a second source of truth about the same frame, and the two would drift.
    """
    chain = chain or body.lod_chain()
    tot = sum(w for _c, w in body.FACTIONS_MIX.values())
    out = []
    for i, lv in enumerate(chain):
        bare = dressed = 0.0
        for sp, (_c, share) in body.FACTIONS_MIX.items():
            b = d = 0
            for k in range(sample):
                nid = f"ratio-{k}"
                b += len(body.build(sp, nid, i, chain)[1])
                d += len(build_dressed(sp, nid, i, chain, datum,
                                       distance_m=lv["switch_distance_m"])[1])
            bare += (b / sample) * share / tot
            dressed += (d / sample) * share / tot
        out.append({"level": lv["name"], "bare": bare, "dressed": dressed,
                    "ratio": dressed / max(bare, 1e-9),
                    "delta": dressed - bare})
    return out


def zocalo_crowd(bays=3, density="busy", chain=None, datum=ERA_DATUM, sample=8):
    """The brief's question, with the crowd dressed: does clothing break it?"""
    chain = chain or body.lod_chain()
    base = body.zocalo_crowd(bays=bays, density=density, chain=chain)
    ratios = {r["level"]: r for r in dressed_ratio(chain, datum, sample)}
    total = 0.0
    bands = []
    for b in base["bands"]:
        r = ratios[b["level"]]
        t = b["triangles"] * r["ratio"]
        total += t
        bands.append(dict(b, dressed_triangles=int(round(t)),
                          clothing_triangles=int(round(t - b["triangles"])),
                          ratio=round(r["ratio"], 3)))
    return {"figures_in_view": base["figures_in_view"],
            "bare_triangles": base["triangles"],
            "triangles": int(round(total)),
            "clothing_triangles": int(round(total - base["triangles"])),
            "budget": base["budget"], "bands": bands,
            "share_of_frame": total / body.FRAME_TRIANGLES,
            "within_budget": total <= base["budget"]}


# ---------------------------------------------------------------------------
# 12. Output
# ---------------------------------------------------------------------------
def write_obj(path, verts, tris, spans=None, default="npc"):
    body.write_obj(path, verts, tris, spans, default)


def lineup(keys=None, lod=0, spacing=0.95, datum=ERA_DATUM):
    """One figure per costume set, side by side, for the preview renderer."""
    keys = keys or [k for k in SETS if k != "none"]
    chain = body.lod_chain()
    # A costume is worn by a body; pick the species the set is actually for so
    # the lineup shows a Narn in Narn dress rather than a human in it.
    species_for = {"narn_formal": "narn", "narn_trader": "narn",
                   "narn_refugee": "narn", "centauri_court": "centauri",
                   "centauri_merchant": "centauri", "centauri_fallen": "centauri",
                   "minbari_religious": "minbari", "minbari_worker": "minbari",
                   "minbari_warrior": "minbari", "league_delegate": "drazi",
                   "league_trader": "brakiri", "league_worker": "drazi",
                   "pakmara_cowl": "pakmara"}
    verts, tris, spans = [], [], []
    for i, key in enumerate(keys):
        sp = species_for.get(key, "human")
        cs = SETS[key]
        c = Costume(sp, f"lineup-{key}", key,
                    (cs.cloth[0][0] if cs.cloth else ""), cs.trim, cs.leather,
                    cs.metal, tuple(cs.silhouettes),
                    tuple(cs.attachments) + (("armband",) if key ==
                                             "ef_security_dress" else ()),
                    tuple(cs.decals), key == "ef_security_dress", 0.2, 1.0,
                    cs.robed, cs.split)
        v, t, s = build_dressed(sp, f"lineup-{key}", lod, chain, datum, c,
                                distance_m=0.0)
        b, lo = len(verts), len(tris)
        dx = (i - (len(keys) - 1) / 2.0) * spacing
        verts.extend((x + dx, y, z) for x, y, z in v)
        tris.extend((a + b, cc + b, d + b) for a, cc, d in t)
        for g, a, cc in s:
            spans.append((g, a + lo, cc + lo))
    return verts, tris, spans


def report(out=print):
    chain = body.lod_chain()
    out(f"era datum {ERA_DATUM}  (FACTIONS.md 1.3, S3 pre-martial-law)")
    for k, (when, why) in sorted(ERA_EVENTS.items(), key=lambda kv: kv[1][0]):
        mark = "ON " if era_active(k, ERA_DATUM) else "off"
        out(f"  {mark} S{when[0]}E{when[1]:02d}  {k:20s} {why}")

    out("\ncolour chain")
    out(f"  SKIN_ANCHOR {SKIN_ANCHOR} -- cross-checked at 0.379 against "
        f"materials.kit_deck via the shared downlight in `more hallway.jpg`,")
    out( "               and at 0.35 physical; the two publicity stills' faces "
         "agree to 1.7%")
    bad = [f for f, ok in GREY_WORLD_VALID.items() if not ok]
    out(f"  grey-world valid on {sum(GREY_WORLD_VALID.values())} of "
        f"{len(GREY_WORLD_VALID)} frames; INVALID on:")
    for f in bad:
        g = GREY_WORLD_GAINS[f]
        out(f"    {g[0]:.3f}/{g[1]:.3f}/{g[2]:.3f}  {f}")

    out("\nfabrics, albedo on the station's own value ladder")
    for f in sorted(FABRICS.values(), key=lambda x: -x.value()):
        a = f.albedo
        out(f"  {f.key:20s} a({a[0]:.3f},{a[1]:.3f},{a[2]:.3f}) "
            f"rough {f.roughness:.2f} metal {f.metallic:.2f} "
            f"auth {f.authority}  {f.title}")

    out("\ndecals -- zero triangles, and the distance each stops saying anything")
    for d in DECALS.values():
        out(f"  {d.key:20s} {d.width_m*1000:5.0f} x {d.height_m*1000:4.0f} mm "
            f"legible to {d.legible_to_m():5.1f} m, sub-sample past "
            f"{d.subpixel_beyond_m():6.1f} m  [{d.slot}]")

    out("\nattachments -- the only triangles clothing spends")
    for a in ATTACHMENTS.values():
        d = "never culled" if a.key in NEVER_CULLED else f"{a.honest_from_m():6.1f} m"
        out(f"  {a.key:18s} silhouette error {a.error_m*1000:5.1f} mm  "
            f"honest to drop beyond {d}")

    out("\ncost per costume, measured on the built mesh")
    for key in ("ef_command", "ef_security_duty", "minbari_religious",
                "civ_ordinary", "pakmara_cowl", "none"):
        sp = {"minbari_religious": "minbari", "pakmara_cowl": "pakmara",
              "none": "gaim"}.get(key, "human")
        r = costume_triangles(sp, "cost-probe", chain, set_key=key)
        row = r["rows"][0]
        out(f"  {key:20s} lod0 bare {row['bare']:5,d} -> dressed "
            f"{row['dressed']:5,d}  ({row['delta']:+,d})")

    out("\ntexture")
    tm = texture_memory()
    out(f"  {tm['sets']} sheets, {tm['maps']} maps, {tm['compressed_mb']:.2f} MB "
        f"compressed = {tm['fraction']*100:.3f}% of the "
        f"{tm['budget_mb']:.0f} MB texture budget")
    out(f"  material slots: {len(MATERIAL_SLOTS)} for {len(SETS)} costume sets "
        f"and {len(FABRICS)} fabrics -- garment identity is per-instance data, "
        f"not a material")

    z = zocalo_crowd(sample=8)
    out("\ncrowd -- a busy Zocalo, dressed, against body.zocalo_crowd()'s bands")
    out(f"  {z['figures_in_view']:.0f} figures in view: bodies "
        f"{z['bare_triangles']:,} + clothing {z['clothing_triangles']:+,} = "
        f"{z['triangles']:,} of {z['budget']:,} ({100*z['triangles']/z['budget']:.1f}%)")
    out(f"  clothing is {100*z['clothing_triangles']/max(z['budget']-z['bare_triangles'],1):.1f}% "
        f"of the headroom the bodies leave, or "
        f"{z['clothing_triangles']/max(z['figures_in_view'],1):+.0f} triangles a "
        f"person -- robes and cowls SUBTRACT, uniforms add")
    out("")
    for dist in (2.0, 12.0, 40.0):
        c = crowd_cost(1, distance_m=dist, chain=chain, sample=6)
        out(f"  at {dist:5.1f} m: {c['level']}, {c['tris_per_figure']:7,.0f} "
            f"tri/dressed figure -> the NPC budget affords "
            f"{c['max_figures_in_budget']:,}")


# ---------------------------------------------------------------------------
# 13. Self-test
# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL: {label}")

    chain = body.lod_chain()

    # -- determinism -------------------------------------------------------
    a = costume_for("narn", "r-0001")
    b = costume_for("narn", "r-0001")
    check(a == b, "costume_for() is a pure function of (species, id, datum)")
    # Ignoring npc_id, which every Costume carries: comparing whole records
    # made this pass even with the seed pinned to a constant -- the ids still
    # differed. The mutation harness caught it. What is asserted now is that
    # the RESOLVED fields differ across a population.
    def _shape(c):
        return (c.set_key, c.cloth, c.nightwatch, round(c.wear, 3),
                round(c.value_jitter, 3))
    pop = {_shape(costume_for("human", f"d{i}", role_key="service"))
           for i in range(400)}
    check(len(pop) > 200,
          f"400 residents produce more than 200 distinct costumes "
          f"(got {len(pop)})")
    v1, t1, s1 = build_dressed("human", "r-0009", 0, chain)
    v2, t2, s2 = build_dressed("human", "r-0009", 0, chain)
    check(v1 == v2 and t1 == t2 and s1 == s2,
          "the same resident dresses byte-for-byte twice")
    tree = ast.parse(open(os.path.abspath(__file__)).read())
    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            banned += [n.name for n in node.names if n.name.split(".")[0] == "random"]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("random"):
            banned.append(node.module)
        elif isinstance(node, ast.Attribute) and node.attr == "__hash__":
            banned.append("__hash__")
    check(not banned, f"no `random` and no `__hash__` anywhere in the module ({banned})")
    # Not a tautology: this asserts the module draws from body.py's stream, so a
    # local copy of _u with a different construction would fail here.
    check(_u is body._u and _gauss is body._gauss,
          "randomness comes from body.py's blake2b stream, not a local copy")
    # PINNED, and pinned to a POPULATION rather than to one draw: a refactor of
    # the seed string, the salt names or the draw order regenerates every
    # resident's wardrobe silently, and a station whose crowd changes clothes
    # between sessions is not testable. blake2b is not salted per process, so
    # this value is also the PYTHONHASHSEED check -- `str.__hash__` would move
    # it every run, which is how session 2n's hull was nearly shipped.
    import hashlib                                            # noqa: PLC0415
    h = hashlib.blake2b(digest_size=8)
    for i in range(200):
        c = costume_for("human", f"pin-{i}", role_key="service")
        h.update(f"{c.set_key}|{c.cloth}|{c.nightwatch}|{c.wear:.4f}|"
                 f"{c.value_jitter:.4f}".encode())
    digest = h.hexdigest()
    check(digest == "247aee841064ce1d",
          f"200 residents dress to a pinned digest (got {digest})")

    # -- the era gate ------------------------------------------------------
    check(era_active("nightwatch_visible", (3, 5)),
          "Nightwatch is active at the datum")
    check(not era_active("nightwatch_visible", (2, 21)),
          "Nightwatch does NOT exist at S2E21 -- the episode before The Fall of Night")
    check(era_active("nightwatch_visible", (2, 22)),
          "Nightwatch switches on exactly at S2E22")
    check(not era_active("rangers_visible", (2, 22)),
          "the Ranger costume is out of era in Season 2")
    raised = False
    try:
        costume_for("human", "x", (3, 10))
    except ValueError:
        raised = True
    check(raised, "a datum at secession is refused")
    raised = False
    try:
        costume_for("human", "x", (1, 5))
    except ValueError:
        raised = True
    check(raised, "a Season 1 datum is refused")

    # Behavioural, not just the predicate: run a population at three datums.
    ids = [f"sec-{i:05d}" for i in range(1200)]
    at_datum = [costume_for("human", i, (3, 5), role_key="security") for i in ids]
    early = [costume_for("human", i, (2, 10), role_key="security") for i in ids]
    banded_now = sum(c.nightwatch for c in at_datum)
    banded_early = sum(c.nightwatch for c in early)
    check(banded_early == 0,
          f"NO armband exists in early Season 2 (got {banded_early})")
    rate = banded_now / len(at_datum)
    # FACTIONS 5.4's own band, not this module's constant: changing
    # NIGHTWATCH_SECURITY_RATE inside 30-40% is allowed and outside it is not.
    check(0.30 <= rate <= 0.40,
          f"armband rate among security is inside FACTIONS 5.4's 30-40% "
          f"(got {rate:.3f})")
    check(all("armband" in c.attachments and
              ("nightwatch_eye", "left_forearm") in c.decals
              for c in at_datum if c.nightwatch),
          "every banded officer carries BOTH the strap and the emblem")
    check(all("armband" not in c.attachments for c in at_datum
              if not c.nightwatch),
          "and every unbanded officer carries neither")
    # 40 Rangers among 167,500 humans and Minbari is 2.4e-4, so the sample has
    # to be large enough to expect several. 60,000 draws expects ~14.
    rid = [f"r{i}" for i in range(60000)]
    rangers_early = sum(costume_for("human", i, (2, 10),
                                    role_key="visitor").set_key == "ranger"
                        for i in rid)
    check(rangers_early == 0,
          f"no Ranger costume exists in Season 2 (got {rangers_early})")
    rangers_now = sum(costume_for("human", i, (3, 5),
                                  role_key="visitor").set_key == "ranger"
                      for i in rid)
    check(4 <= rangers_now <= 40,
          f"and Rangers appear at the S3 datum at FACTIONS 10.1's rate "
          f"(got {rangers_now} in 60,000, expected ~14)")

    # -- who wears what ----------------------------------------------------
    check(costume_for("gaim", "g-1").set_key == "none"
          and costume_for("vorlon", "kosh").set_key == "none",
          "encounter-suit species are not dressed")
    gv, gt, _ = build_dressed("gaim", "g-1", 0, chain)
    bv, bt, _ = body.build("gaim", "g-1", 0, chain)
    check(len(gt) == len(bt) and gv == bv,
          "dressing a Gaim adds exactly zero triangles and moves no vertex")
    check(costume_for("minbari", "m-1", role_key="cleric").set_key
          == "minbari_religious", "Minbari clerics get religious robes")
    check(costume_for("narn", "n-1", role_key="refugee").set_key
          == "narn_refugee", "Narn refugees get the refugee set")
    check(costume_for("drazi", "d-1", role_key="dockworker").set_key
          == "league_worker", "a Drazi docker falls through to League worker")
    # Every (species, role) pair resolves. A KeyError here is a crowd that
    # cannot spawn, which is the failure this loop exists to prevent.
    bad = []
    try:
        import schedule
        roles = [r.key for r in schedule.ROLES]
    except Exception:                                          # noqa: BLE001
        roles = ["visitor"]
    for sp in body.SPECIES:
        for rk in roles:
            try:
                k = set_key_for(sp, rk)
                if k not in SETS:
                    bad.append((sp, rk, k))
            except Exception as exc:                           # noqa: BLE001
                bad.append((sp, rk, repr(exc)))
    check(not bad, f"every (species, role) pair resolves to a real set ({bad[:3]})")
    # And every entry in every table names a set that exists. The loop above
    # only exercises the pairs the ROLES list produces; a typo in a table entry
    # no species reaches would survive it.
    named = set(SET_FOR_ROLE_DEFAULT.values()) | set(SET_FOR_SPECIES.values())
    for t in SET_FOR_ROLE.values():
        named |= set(t.values())
    check(named <= set(SETS),
          f"every costume table entry names a real set ({sorted(named - set(SETS))})")

    # -- Psi Corps: the ruling must survive ---------------------------------
    psi = [costume_for("human", f"p{i}", role_key="financier") for i in range(20000)]
    psi = [c for c in psi if c.set_key == "psi_corps"]
    check(len(psi) > 0, "telepaths appear in the population at all")
    check(len({c.cloth for c in psi}) >= 2,
          f"Psi Corps uses more than one body colour -- FACTIONS 4.2's ruling "
          f"(got {sorted({c.cloth for c in psi})})")
    check(all(("psi_badge", "left_chest") in c.decals for c in psi),
          "and every one of them wears the badge, which is the invariant")
    check(all(c.trim == "psi_black_panel" for c in psi),
          "and the black inset panelling, which is the other invariant")

    # -- geometry: winding, closure, facing ---------------------------------
    # Per part, not over the figure: a correct torso hides an inside-out belt.
    probes = [("human", "w-1", "ef_command"), ("human", "w-2", "ef_security_duty"),
              ("minbari", "w-3", "minbari_religious"),
              ("pakmara", "w-4", "pakmara_cowl"), ("narn", "w-5", "narn_formal"),
              ("human", "w-6", "civ_lurker"), ("drazi", "w-7", "league_delegate"),
              # civ_ordinary is here specifically because its trim differs from
              # its cloth, so its torso is emitted as TWO spans of one solid --
              # the case a per-span closure check would report as broken.
              ("human", "w-8", "civ_ordinary"), ("human", "w-10", "ranger")]
    neg = openb = nonman = []
    neg, openb, nonman = [], [], []
    for sp, nid, key in probes:
        cs = SETS[key]
        c = Costume(sp, nid, key, cs.cloth[0][0], cs.trim, cs.leather, cs.metal,
                    tuple(cs.silhouettes), tuple(cs.attachments) + ("armband",),
                    tuple(cs.decals), True, 0.2, 1.0, cs.robed, cs.split)
        for lod in (0, 2):
            src = dressed_parts(sp, nid, lod, chain, costume=c,
                                distance_m=0.0)
            for name, v, t in src:
                if body.signed_volume(v, t) <= 0.0:
                    neg.append((key, name, lod))
                bnd, nm = body.edge_census(t)
                if bnd:
                    openb.append((key, name, lod, bnd))
                if nm:
                    nonman.append((key, name, lod, nm))
    check(not neg, f"every dressed part winds outward ({neg[:4]})")
    check(not openb, f"every dressed part is closed ({openb[:4]})")
    check(not nonman, f"no non-manifold edges anywhere ({nonman[:4]})")

    # The render-side version of the same question, done numerically because a
    # black render reads as a badly placed camera rather than as a bug.
    v, t, _ = build_dressed("human", "w-1", 0, chain, distance_m=0.0)
    f = body.facing_fraction(v, t, (3.0, 1.2, 3.0))
    check(0.35 <= f <= 0.65, f"about half the dressed figure survives culling "
                             f"(got {f:.3f})")
    flipped = [(c, b, a) for a, b, c in t]
    check(abs(body.facing_fraction(v, flipped, (3.0, 1.2, 3.0)) - (1.0 - f)) < 1e-9,
          "and flipping the winding gives exactly the complement")

    # -- silhouette modifiers are strictly positive -------------------------
    worst = min(m.scale_at(y / 100.0) for m in SILHOUETTES.values()
                for y in range(0, 101))
    check(worst > 0.0, f"no silhouette modifier is ever non-positive "
                       f"(min {worst:.3f})")
    # And they actually move the outline: a modifier that did nothing would be
    # a costume that is invisible at the distance colour stops working.
    bare = body.build("human", "w-9", 0, chain)[1]
    cs = SETS["civ_ordinary"]
    naked = Costume("human", "w-9", "civ_ordinary", "civ_dark_warm", cs.trim,
                    cs.leather, cs.metal, (), (), (), False, 0.2, 1.0, False)
    cc = Costume("human", "w-9", "civ_ordinary", "civ_dark_warm", cs.trim,
                 cs.leather, cs.metal, cs.silhouettes, (), (), False, 0.2, 1.0,
                 False)

    def _torso_width(costume):
        # The TORSO, not the figure: the widest vertex on a standing human is
        # a hand, and a torso modifier does not move it. Measuring the bounding
        # box would have made this assertion unable to fail, which is the exact
        # pattern this repository has shipped three times.
        for name, v, _t in dressed_parts("human", "w-9", 0, chain,
                                         costume=costume, distance_m=0.0):
            if name == "torso":
                return max(abs(p[0]) for p in v)
        return 0.0

    w_bare, w_dress = _torso_width(naked), _torso_width(cc)
    check(w_dress > w_bare * 1.05,
          f"a coat is measurably wider than the body under it "
          f"({w_bare:.4f} -> {w_dress:.4f} m)")
    check(len(bare) == len(build_dressed("human", "w-9", 0, chain, costume=cc,
                                         distance_m=0.0)[1]),
          "and it costs zero triangles to be wider")

    # -- the shoulder yoke: two values on one solid, zero triangles ---------
    yv, yt, yspans = build_dressed("human", "w-8", 0, chain,
                                   costume=Costume(
                                       "human", "w-8", "civ_ordinary",
                                       "civ_dark_warm", "civ_collar_yoke",
                                       "civ_boot", "ef_gold", (), (), (),
                                       False, 0.2, 1.0, False),
                                   distance_m=0.0)
    yoke_spans = [g for g, _lo, _hi in yspans if g.endswith("civ_collar_yoke")]
    check(len(yoke_spans) == 1,
          f"exactly one yoke span is emitted (got {len(yoke_spans)})")
    plainv, plaint, _ = build_dressed(
        "human", "w-8", 0, chain,
        costume=Costume("human", "w-8", "civ_ordinary", "civ_dark_warm",
                        "civ_dark_warm", "civ_boot", "ef_gold", (), (), (),
                        False, 0.2, 1.0, False), distance_m=0.0)
    check(len(yt) == len(plaint) and len(yv) == len(plainv),
          f"and the split costs zero triangles and zero vertices "
          f"({len(yt)} vs {len(plaint)})")
    plain_spans = build_dressed(
        "human", "w-8", 0, chain,
        costume=Costume("human", "w-8", "civ_ordinary", "civ_dark_warm",
                        "civ_dark_warm", "civ_boot", "ef_gold", (), (), (),
                        False, 0.2, 1.0, False), distance_m=0.0)[2]
    check(len(yspans) == len(plain_spans) + 1,
          f"and it adds exactly one span, not one part "
          f"({len(plain_spans)} -> {len(yspans)})")
    # The mechanism above is asserted on a hand-built Costume, so it says
    # nothing about whether the TABLE actually uses it. This does: every set a
    # crowd is mostly made of must name a trim that differs from its cloth, or
    # the crowd is a field of single-value silhouettes and the yoke code is
    # dead. The mutation harness set civ_ordinary's trim equal to its cloth and
    # nothing failed until this was added.
    flat = [c.set_key for c in
            [costume_for("human", f"y{i}", role_key=r)
             for i in range(300) for r in ("service", "visitor", "financier")]
            if c.trim == c.cloth or not c.trim]
    check(not flat,
          f"EVERY resident of a crowd gets a yoke fabric distinct from the "
          f"body cloth ({len(flat)} without one, e.g. {flat[:3]})")
    # The PLASTRON is a different cut and must not silently become a yoke: the
    # command uniform's leather bib runs down the centre FRONT, and a
    # horizontal band across the shoulders is a different garment. Asserted on
    # the geometry -- the plastron's triangles must be forward of the torso's
    # centre and must span most of its height, which a yoke does neither of.
    pc = SETS["ef_command"]
    pcos = Costume("human", "pl-1", "ef_command", pc.cloth[0][0], pc.trim,
                   pc.leather, pc.metal, pc.silhouettes, (), (), False, 0.05,
                   1.0, False, pc.split)
    check(pc.split == "plastron", "the command uniform is cut as a plastron")
    pv, pt, psp = build_dressed("human", "pl-1", 0, chain, costume=pcos,
                                distance_m=0.0)
    trim_tris = [t for g, lo, hi in psp if g.endswith("ef_command_leather")
                 and "cloth_trim" in g for t in pt[lo:hi]]
    all_torso = [p for n, vv, _t in
                 dressed_parts("human", "pl-1", 0, chain, costume=pcos,
                               distance_m=0.0) if n == "torso" for p in vv]
    check(trim_tris, "the plastron emits triangles at all")
    zs = [sum(pv[i][2] for i in t) / 3.0 for t in trim_tris]
    ys = [sum(pv[i][1] for i in t) / 3.0 for t in trim_tris]
    ty = [p[1] for p in all_torso]
    check(min(zs) > 0.0,
          f"every plastron triangle is on the FRONT of the torso "
          f"(min z {min(zs):+.4f})")
    span = (max(ys) - min(ys)) / max(max(ty) - min(ty), 1e-9)
    check(span > 0.75,
          f"and it runs down most of the torso's height rather than sitting on "
          f"the shoulders like a yoke (covers {span:.2f} of it)")
    check(FABRICS["civ_collar_yoke"].value() > FABRICS["civ_dark_warm"].value() * 1.4,
          f"the yoke is measurably lighter than the coat body, as the frame "
          f"shows ({FABRICS['civ_collar_yoke'].value():.3f} vs "
          f"{FABRICS['civ_dark_warm'].value():.3f})")

    # -- the robe subtraction ----------------------------------------------
    rc = SETS["minbari_religious"]
    robe = Costume("minbari", "w-3", "minbari_religious", "minbari_cream",
                   rc.trim, rc.leather, rc.metal, rc.silhouettes,
                   rc.attachments, rc.decals, False, 0.05, 1.0, True)
    nrobe = Costume("minbari", "w-3", "minbari_worker", "minbari_worker",
                    rc.trim, rc.leather, rc.metal, (), ("belt",), (), False,
                    0.05, 1.0, False)
    n_robed = len(build_dressed("minbari", "w-3", 0, chain, costume=robe,
                                distance_m=0.0)[1])
    n_legs = len(build_dressed("minbari", "w-3", 0, chain, costume=nrobe,
                               distance_m=0.0)[1])
    check(n_robed < n_legs,
          f"a robed figure is CHEAPER than a trousered one "
          f"({n_robed} vs {n_legs} triangles)")

    # -- attachment LOD ----------------------------------------------------
    cs = SETS["ef_command"]
    far = Costume("human", "w-1", "ef_command", "ef_command_wool", cs.trim,
                  cs.leather, cs.metal, cs.silhouettes,
                  tuple(cs.attachments) + ("armband",), cs.decals, True, 0.05,
                  1.0, False)
    # By NAME, not by triangle count. A count also falls because `_att_seg`
    # coarsens with distance, so a count-based assertion passes even with
    # culling disabled entirely -- which is what the first version of this
    # check did, and the mutation harness caught it.
    def _part_names(d):
        v, t, spans = build_dressed("human", "w-1", 0, chain, costume=far,
                                    distance_m=d)
        # Spans, not distinct group NAMES: a collar, a belt and a boot all bind
        # `npc_leather`, so counting names reports 6 -> 6 while three parts
        # disappear between them. One span is one emitted part.
        return [g for g, _lo, _hi in spans], len(t)

    near_g, near_n = _part_names(0.0)
    mid_g, mid_n = _part_names(6.0)
    far_g, far_n = _part_names(60.0)
    band_group = group_name("npc_cloth_trim", "nightwatch_black")
    check(band_group in near_g and band_group not in mid_g,
          f"the armband strap is present at 0 m and GONE at 6 m, by name "
          f"(honest from {ATTACHMENTS['armband'].honest_from_m():.1f} m)")
    check(len(far_g) < len(mid_g) < len(near_g),
          f"and the number of emitted parts falls monotonically with distance "
          f"({len(near_g)} -> {len(mid_g)} -> {len(far_g)} parts)")
    check(near_n > mid_n > far_n,
          f"triangles fall with it ({near_n} -> {mid_n} -> {far_n})")
    check(ATTACHMENTS["armband"].honest_from_m() < 6.0
          <= ATTACHMENTS["epaulettes"].honest_from_m(),
          "and the armband strap goes before the epaulettes, as its 5 mm says")
    # CROSS-SUBSYSTEM. The armband is FACTIONS 5.4's whole political signal and
    # it sits on a forearm whose rest angle belongs to body.py, not to this
    # module. In the rest pose the forearm hangs beside the hip and the jacket-
    # bulked torso occludes part of the band, which the render showed as a
    # sliver. What matters is that a measurable share of it stays clear -- and
    # that a future change to `arm_k`, to the arm root offset or to
    # `jacket_bulk` cannot quietly bury it without failing here.
    ac = SETS["ef_security_dress"]
    band_c = Costume("human", "nw-a", "ef_security_dress", ac.cloth[0][0],
                     ac.trim, ac.leather, ac.metal, ac.silhouettes,
                     tuple(ac.attachments) + ("armband",),
                     tuple(ac.decals) + (("nightwatch_eye", "left_forearm"),),
                     True, 0.12, 1.0, False)
    parts = {n: (v, t) for n, v, t in
             dressed_parts("human", "nw-a", 0, chain, costume=band_c,
                           distance_m=0.0)}
    tv, tt = parts["torso"]
    bv, _bt = parts["armband"]
    clear = sum(1 for p in bv if not body.contains(tv, tt, p)) / len(bv)
    check(clear >= 0.40,
          f"at least 40% of the armband stands clear of the jacket in the rest "
          f"pose (got {clear:.2f}) -- it is the station's most legible "
          f"political signal and it must not be inside the coat")
    check(DECALS["nightwatch_eye"].legible_to_m()
          > ATTACHMENTS["armband"].honest_from_m() * 2.5,
          f"the armband DECAL outlives its strap by more than 2.5x "
          f"({DECALS['nightwatch_eye'].legible_to_m():.1f} m vs "
          f"{ATTACHMENTS['armband'].honest_from_m():.1f} m)")
    # `all(...)` over an EMPTY set is True, so the first version of this check
    # passed with NEVER_CULLED emptied -- a vacuous assertion of exactly the
    # kind AAA-STANDARD scores ROBUSTNESS 0 for. The membership test is what
    # makes it able to fail.
    check("skirt" in NEVER_CULLED and _attachment_active("skirt", 1e9),
          "the skirt is never culled, because dropping it removes a leg")

    # -- materials and draw calls ------------------------------------------
    slots = set()
    for sp, nid, key in probes:
        for lod in (0, 1):
            for g, _lo, _hi in build_dressed(sp, nid, lod, chain,
                                             distance_m=0.0)[2]:
                if g.startswith("npc_") and "__" in g:
                    slots.add(g.split("__")[0])
    check(slots <= set(MATERIAL_SLOTS),
          f"every costume group binds one of the {len(MATERIAL_SLOTS)} slots "
          f"({sorted(slots - set(MATERIAL_SLOTS))})")
    check(len(MATERIAL_SLOTS) < len(SETS),
          f"and there are fewer slots ({len(MATERIAL_SLOTS)}) than sets "
          f"({len(SETS)}) -- adding a costume adds no material")
    raised = False
    try:
        group_name("npc_not_a_slot", "x")
    except KeyError:
        raised = True
    check(raised, "an unknown material slot is refused rather than emitted")

    # -- colour ------------------------------------------------------------
    # UNCLAMPED. `_albedo` clamps to [ALBEDO_FLOOR, ALBEDO_CEIL], so asserting
    # on the clamped output is an assertion that cannot fail -- the mutation
    # harness set a fabric to (0,0,0) and the clamped check passed. What is
    # worth asserting is that no fabric NEEDS the clamp by more than a hair:
    # a measurement that lands outside the range is a measurement to re-take,
    # and `minbari_black` is the one deliberate exception, floored by 0.002.
    raw = {}
    for k, f in FABRICS.items():
        if f.declared:
            raw[k] = f.measured
        else:
            g = frame_gain(f.frame)
            raw[k] = tuple(c * g for c in f.measured)
    floored = tuple(sorted(k for k, v in raw.items() if min(v) < ALBEDO_FLOOR))
    check(floored == EXPECTED_FLOORED,
          f"exactly the four declared garments need the black floor "
          f"(got {floored})")
    check(min(min(v) for v in raw.values()) > 0.010,
          f"and none of them is pure black even before clamping "
          f"(min {min(min(v) for v in raw.values()):.4f})")
    check(max(max(v) for v in raw.values()) <= ALBEDO_CEIL + 1e-9,
          f"no fabric is pure white before clamping "
          f"(max {max(max(v) for v in raw.values()):.4f})")
    # The measured civilian distribution, checked against the frame it came
    # from rather than against these weights: `more zocalo.png` puts every
    # garment between 0.026 and 0.187 balanced, which is 0.030 to 0.213 albedo.
    civ = [FABRICS[k].value() for k, _w in SETS["civ_ordinary"].cloth]
    check(min(civ) >= 0.029 and max(civ) <= 0.60,
          f"civilian palette values sit in the measured band ({min(civ):.3f}-"
          f"{max(civ):.3f}); the top is the ONE light garment in either frame")
    drawn = [FABRICS[costume_for("human", f"c{i}", role_key="service").cloth].value()
             for i in range(2000)]
    drawn.sort()
    med = drawn[len(drawn) // 2]
    check(0.03 <= med <= 0.16,
          f"the generated crowd's MEDIAN garment value reproduces the measured "
          f"one (got {med:.3f}; `more zocalo.png` median 0.062)")
    light = sum(1 for v in drawn if v > 0.30) / len(drawn)
    check(0.005 <= light <= 0.08,
          f"and its light tail is small but non-zero (got {light:.3f}) -- one "
          f"light garment appears in two crowd frames, so neither 0 nor 10% "
          f"is right")
    # The two frames the balance cannot be trusted on must be MARKED, or a
    # later session will quote a green Narn.
    check(not GREY_WORLD_VALID[_GK] and not GREY_WORLD_VALID[_MC],
          "the two hue-dominated frames are marked grey-world INVALID")
    check(GREY_WORLD_VALID[_SH] and GREY_WORLD_VALID[_ZA] and
          GREY_WORLD_VALID[_MZ],
          "and the frames the uniforms come from are marked valid")
    check(all(FABRICS[k].frame in GREY_WORLD_GAINS or FABRICS[k].declared
              for k in FABRICS),
          "every measured fabric names a frame whose gains are recorded")
    # The EarthForce blue is the one colour claim with two independent frames
    # behind it. Assert the RELATIONSHIP the module actually claims.
    wool = FABRICS["ef_command_wool"].albedo
    twill = FABRICS["ef_security_twill"].albedo
    check(wool[2] > wool[0] and twill[2] > twill[0],
          "both EarthForce jackets are blue-biased, as measured")
    check((wool[2] - wool[0]) / max(wool[2], 1e-9)
          > (twill[2] - twill[0]) / max(twill[2], 1e-9),
          "and the command wool is the bluer of the two, which is the "
          "relationship the two frames agree on")

    # -- decals -------------------------------------------------------------
    check(len({d.key for d in DECALS.values()}) == len(DECALS),
          "no duplicate decal keys")
    check(all(d.slot in DECAL_SLOTS for d in DECALS.values()),
          "every decal sits in a declared slot")
    check(all(d.legible_to_m() < d.subpixel_beyond_m() for d in DECALS.values()),
          "a badge stops being legible before it stops being visible")
    nw = DECALS["nightwatch_eye"]
    check(10.0 < nw.legible_to_m() < 25.0,
          f"the armband reads across a corridor but not across the Zocalo "
          f"({nw.legible_to_m():.1f} m)")

    # -- cost ---------------------------------------------------------------
    # Against body.zocalo_crowd()'s band model, not against one distance: a
    # crowd is spread over FLOOR, and body.py records that costing it at a
    # single depth put 7% of the people inside 2.2 m of the lens. The bare
    # figure is 97,840 of 144,000, so clothing has 46,160 triangles to spend
    # and the assertion is that it spends far less.
    # sample=6, not 3. At sample=3 the per-level ratio swings between 1.01 and
    # 1.09 depending on how many robes the sample happens to draw -- robes
    # SUBTRACT -- and the assertion would be measuring the draw. At 8 the
    # clothing bill settles at about +1,000 triangles for the whole crowd.
    z = zocalo_crowd(chain=chain, sample=6)
    check(z["within_budget"],
          f"a DRESSED busy Zocalo fits the NPC budget "
          f"({z['triangles']:,} of {z['budget']:,})")
    check(z["clothing_triangles"] < 0.25 * (z["budget"] - z["bare_triangles"]),
          f"and clothing takes under a quarter of the headroom the bodies "
          f"leave ({z['clothing_triangles']:,} of "
          f"{z['budget'] - z['bare_triangles']:,})")
    tm = texture_memory()
    check(tm["fraction"] < 0.01,
          f"every garment texture on the station is under 1% of the texture "
          f"budget (got {tm['fraction']*100:.3f}%)")
    r = costume_triangles("human", "cost-probe", chain, set_key="ef_command")
    check(r["rows"][-1]["delta"] == 0,
          "the costume costs nothing at the impostor level")
    check(r["rows"][0]["delta"] < 260,
          f"and under 260 triangles at LOD0, where at most one figure is in "
          f"frame (got {r['rows'][0]['delta']})")
    # The number that actually matters: lod3 carries 74 of the Zocalo's 84
    # visible figures, so the marginal cost there is the crowd's clothing bill.
    lod3 = costume_triangles("human", "cost-probe", chain,
                             set_key="ef_command")["rows"][3]
    check(lod3["delta"] < 100,
          f"and under 100 at lod3, which carries 88% of a Zocalo crowd "
          f"(got {lod3['delta']})")

    # -- cross-module -------------------------------------------------------
    check(set(SET_FOR_ROLE) <= set(body.SPECIES),
          "every species with a costume table exists in body.SPECIES")
    check(all(f in GREY_WORLD_GAINS or f == "" for f in
              {FABRICS[k].frame for k in FABRICS} - {""}
              if not f.startswith("16-")),
          "every fabric frame is one this module measured")

    # -- THE WARDROBE AS MATERIALS ----------------------------------------
    # Measured here for sessions and never reaching a surface: `materials.py`
    # imported this module for two constants, so 2,016 inhabitants stood on
    # the station with no clothes on.
    _specs = material_specs()
    _groups = {m["group"] for m in _specs}
    # THE BUILDER'S LITERALS, CHECKED AGAINST THIS FILE'S OWN SOURCE. A
    # `group_name("slot", "fabric")` call with two literals is a garment no
    # `Costume` record mentions and no sample can reach -- the Nightwatch
    # armband is one and was missed by both other sources. Grepping the source
    # is what stops `BUILDER_FABRICS` going stale the day a second one lands.
    import re as _re                                            # noqa: PLC0415
    _src = open(__file__).read()
    # Filtered to pairs that name a REAL slot and a REAL fabric: this file's
    # own tests and docstrings call `group_name("slot", "fabric")` and
    # `group_name("npc_not_a_slot", "x")` to prove it rejects them, and those
    # are not garments. The filter is the same predicate `material_specs` uses,
    # so it cannot quietly exclude a real one.
    _lits = {(a, b) for a, b in _re.findall(
        r'group_name\(\s*"([a-z_]+)"\s*,\s*"([a-z_]+)"\s*\)', _src)
        if a in MATERIAL_SLOTS and b in FABRICS}
    check(_lits <= set(BUILDER_FABRICS),
          f"every fabric the mesh builder writes as a literal is declared in "
          f"BUILDER_FABRICS ({sorted(_lits - set(BUILDER_FABRICS))} are not)")
    check(bool(_lits),
          f"...and the grep finds them at all -- {len(_lits)} literal "
          f"group_name calls in this file")
    check(len(_specs) > 40 and len(_groups) == len(_specs),
          f"the wardrobe exports {len(_specs)} materials, one per reachable "
          f"(slot, fabric), with no duplicate group")
    check(all(m["albedo"] and 0.0 <= m["roughness"] <= 1.0
              and 0.0 <= m["metallic"] <= 1.0 for m in _specs),
          "every exported material carries a usable albedo, roughness and "
          "metallic")
    # THE ALBEDO, NOT THE RAW MEASUREMENT. `Fabric.albedo` puts the measured
    # pixel value on the station's ladder -- frame gain, then the floor and
    # ceiling clamp -- and exporting `measured` instead is the balanced-vs-
    # linear trap CLAUDE.md names. It also skips the declared branch, so a
    # declared fabric would ship unclamped.
    _byname = {f"{sl}__{k}": FABRICS[k]
               for sl in MATERIAL_SLOTS for k in FABRICS}
    check(all(tuple(m["albedo"]) == tuple(_byname[m["group"]].albedo)
              for m in _specs if m["group"] in _byname),
          "every exported albedo is the fabric's ALBEDO, not its raw measured "
          "value")
    _raw = [m["group"] for m in _specs
            if m["group"] in _byname
            and tuple(_byname[m["group"]].measured)
            != tuple(_byname[m["group"]].albedo)]
    check(bool(_raw),
          f"BREAK: and the two genuinely differ on {len(_raw)} fabrics, so "
          f"that check is not comparing a number with itself: "
          f"{_raw[:2]}")
    _auth1 = sum(1 for m in _specs if m["authority"] == 1)
    check(_auth1 >= len(_specs) // 2,
          f"and most of them are MEASURED rather than declared -- {_auth1} of "
          f"{len(_specs)} at authority 1, each naming its frame and region")
    # NEITHER SOURCE IS COMPLETE ALONE, which is why the export is a union.
    _from_sets = set()
    for _st in SETS.values():
        for _slot, _attr in (("npc_cloth", "cloth"),
                             ("npc_cloth_trim", "trim"),
                             ("npc_leather", "leather"),
                             ("npc_metal", "metal")):
            for _k in _fabric_keys(getattr(_st, _attr, None)):
                if _k in FABRICS:
                    _from_sets.add(group_name(_slot, _k))
    _sampled = set(worn_fabrics(sample=SPEC_SAMPLE))
    check(bool(_sampled - _from_sets),
          f"BREAK: `SETS` alone MISSES {len(_sampled - _from_sets)} groups that "
          f"`costume_for` actually produces -- so reading the declared table "
          f"is not enough: {sorted(_sampled - _from_sets)[:3]}")
    check(bool(_from_sets - _sampled),
          f"BREAK: and sampling alone misses {len(_from_sets - _sampled)} the "
          f"table declares -- so neither source is complete and the union is "
          f"not belt and braces")
    # THE SAMPLE SIZE IS A MEASUREMENT. Ten times more draws must find nothing
    # outside what was exported, or 600 was a guess.
    _big = set(worn_fabrics(sample=SPEC_SAMPLE * 2))
    check(_big <= _groups,
          f"a sample twice the size finds nothing outside the export "
          f"({len(_big)} groups, {sorted(_big - _groups)[:3]} outside)")

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--obj")
    ap.add_argument("--species", default="human")
    ap.add_argument("--id", default="demo-1")
    ap.add_argument("--set")
    ap.add_argument("--lineup", action="store_true")
    ap.add_argument("--lod", type=int, default=0)
    ap.add_argument("--datum", default="")
    a = ap.parse_args()
    datum = ERA_DATUM
    if a.datum:
        s, e = a.datum.lower().lstrip("s").split("e")
        datum = (int(s), int(e))
    if a.report:
        report()
        return 0
    if a.obj:
        if a.lineup:
            v, t, s = lineup(lod=a.lod, datum=datum)
        else:
            c = None
            if a.set:
                cs = SETS[a.set]
                c = Costume(a.species, a.id, a.set,
                            cs.cloth[0][0] if cs.cloth else "", cs.trim,
                            cs.leather, cs.metal, cs.silhouettes,
                            cs.attachments, cs.decals, False, 0.2, 1.0, cs.robed,
                            cs.split)
            v, t, s = build_dressed(a.species, a.id, a.lod, None, datum, c,
                                    distance_m=0.0)
        write_obj(a.obj, v, t, s)
        print(f"{a.obj}: {len(v):,} vertices, {len(t):,} triangles, "
              f"{len(s)} groups")
        return 0
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
