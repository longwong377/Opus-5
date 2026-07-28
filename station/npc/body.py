#!/usr/bin/env python3
"""Species body geometry: one parametric humanoid, fifteen species, one LOD chain.

A quarter of a million residents cannot be fifteen hand-modelled meshes, and they
certainly cannot be 250,000 of them. What they can be is ONE base topology --
a fixed graph of lofted rings around a fixed skeleton -- driven by a parameter
block per species and jittered per individual from a hash of the NPC id. Two
species differ by numbers in a table and by which small attachment meshes they
carry, not by being different assets. That is the only shape of solution that
survives 250,000 people, and it is also the only one an agent with no modelling
tool can author and regression-test.

WHAT THE REFERENCE GIVES AND WHAT IT DOES NOT
---------------------------------------------
`reference/15-races-and-makeup/` and `reference/14-characters-and-uniforms/` are
twenty-four close portraits of named characters, mostly framed at the shoulders.
They are excellent for head shape, cranial features and the silhouette of a
crest, and they say **nothing whatever** about how tall a Drazi is. Every
dimension below is tagged with which of the two it came from:

  MEASURED   -- a ratio read off a named file, with the calibration stated
  DERIVED    -- arithmetic on a MEASURED value or on another module's constant
  EXTRAPOLATED -- our own, authority 5, with the constraint and the overturn
                  condition written beside it

The one full-body calibration in the whole reference set is
`reference/10-interiors-generic-kit/more hallway.jpg`: an EarthForce officer
standing in a circular downlight pool. INV-020 already used him as a ruler --
"at 1.75 m he is 261 px, giving 149 px/m at his depth" -- to size
`DOWNLIGHT_POOL_M`. This module re-uses the same figure for the FIGURE ratio
table below, so the interior kit and the people standing in it are calibrated
against the same photograph and cannot drift apart.

THE CONSTRAINT THAT KEEPS FIFTEEN SPECIES IN A HUMAN-SIZED BAND
----------------------------------------------------------------
It is tempting to make a Drazi 2.4 m and a Vree 1.1 m, and it would be wrong.
Two independent arguments bound every resident species to roughly human scale:

1. **Production reality.** Every species in these folders except the Vorlon and
   the Gaim is an actor in prosthetic makeup. On screen their stature
   distribution IS the human one. A simulation that spreads them over a metre
   would be less like the show, not more.
2. **The station's own furniture, and this one is measurable.** `Pak'ma'ra.webp`
   (authority 1) shows pak'ma'ra, a Hyach and other delegates seated at ONE
   continuous Council desk at ONE height. `interior_kit.PROVISIONAL` gives a
   single `door_height_m` for the whole station. A species that cannot use the
   furniture or fit the doors is not a resident species. `_selftest` asserts
   every species -- crest, helmet and all -- clears the kit's door height, and
   that assertion imports the kit rather than copying its number.

WINDING, AND WHY IT IS ASSERTED THREE WAYS
-------------------------------------------
Four separate subsystems in this project have shipped invisible geometry from
inside-out winding (`_box`, `ring_frame`, `wall_panel`, `downlight_pool`). A
body is a closed solid seen from outside, so the rule here is plain -- every
part winds outward -- but "plain" is exactly what the other four were. So:

  * `signed_volume` > 0 on EVERY emitted part, not on the two that broke;
  * zero boundary edges and zero non-manifold edges over the whole figure;
  * `facing_fraction()` replicates `tools/preview_render.py`'s backface test and
    asserts that about half the triangles survive culling from any camera, and
    that flipping the winding gives the complement. That is the "count the culled
    triangles" check, done numerically instead of by looking at a black render.

THE LOD CHAIN IS DERIVED, INCLUDING THE PART THAT SAYS LOD IS NOT ENOUGH
-------------------------------------------------------------------------
`CONTRIBUTING.md` records this project sizing LOD against facet WIDTH when the
thing that pops is the SAGITTA. `station/lod.py` fixed that for the hull and
went further: it split one schedule into three because three different knobs
stop being visible at three different distances. The same split applies here:

  * SILHOUETTE (radial segments round a limb). Error = the sagitta
    `r(1 - cos(pi/n))` at the figure's largest cross-section radius, MEASURED
    off the built rings rather than assumed.
  * PROFILE (rings along the skeleton). Error = the distance from a dropped
    ring's vertex to the segment joining its kept neighbours, MEASURED ring by
    ring on the built geometry. Dropping the elbow costs far more than dropping
    the waist, and only a measurement knows that.
  * FEATURE (crest, tendrils, hands, feet). Error = how far the silhouette moves
    when the part is removed, MEASURED as the growth of the figure's bounding
    box. This one produces an uncomfortable result and the result is the point:
    a Centauri crest is 0.11 m of silhouette, so it is not cullable until 118 m,
    which is beyond the distance a body is drawn as a mesh at all. The
    identifying features are therefore NOT an LOD knob. Hands and feet are.

And the honest limit, which no switch distance can fix: **the deviation budget
bounds the error per figure and says nothing about the number of figures.**
Beyond `SUBPIXEL_FIGURE_M` (695 m, where a 0.45 m shoulder span falls under one
shading sample) an individual is not resolvable at all and must become crowd
density rather than a draw. Inside it, cost is count x rate, and `crowd_cost()`
solves for the count the frame budget affords rather than asserting one.

Run `python3 station/npc/body.py` for the self-test, `--report` for the
derivation, `--obj PATH` to write a figure or a lineup for the preview renderer.
"""
import argparse
import hashlib
import math
import os
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATION = os.path.dirname(_HERE)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
# blake2b, matching the digest construction in `names.py` and `schedule.py` byte
# for byte so that one NPC id gives a name, a schedule and a body that were all
# drawn from the same stream. NEVER `random` (not reproducible across machines)
# and NEVER `str.__hash__` (salted per process -- session 2n shipped a hull that
# would have differed every run).
def _u(seed: str, salt: str = "") -> float:
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def _pick(seq, seed: str, salt: str = ""):
    return seq[int(_u(seed, salt) * len(seq)) % len(seq)]


def _gauss(seed: str, salt: str, sigma: float, clamp: float = 2.5) -> float:
    """Deterministic zero-mean normal-ish deviate, truncated.

    Sum of three uniforms (Irwin-Hall, n=3) scaled to unit variance. Truncation
    is not decoration: an untruncated tail on a stature distribution eventually
    emits a 0.4 m adult, and a crowd system that does that once in ten thousand
    people has a bug nobody can reproduce.
    """
    s = _u(seed, salt + "a") + _u(seed, salt + "b") + _u(seed, salt + "c")
    z = (s - 1.5) * 2.0                      # var(U1+U2+U3) = 1/4 -> scale by 2
    return max(-clamp, min(clamp, z)) * sigma


# ---------------------------------------------------------------------------
# The screen model. Mirrors station/lod.py deliberately; _selftest asserts the
# two agree, because two chains that quietly use different budgets produce two
# different-looking pops in the same frame.
# ---------------------------------------------------------------------------
FOV_DEG = 50.0
SCREEN_H = 1440
SCREEN_W = 2560           # 1440p is 16:9; used only for the horizontal FOV
PIXEL_BUDGET = 1.5          # deviation budget: how far the picture may move
SHADING_SAMPLE_PX = 1.0     # below this a feature cannot read as form at all


def _px_scale(budget_px: float) -> float:
    """Metres of viewing distance per metre of feature, at `budget_px`."""
    return SCREEN_H / (budget_px * 2.0 * math.tan(math.radians(FOV_DEG) / 2.0))


def _hfov_rad():
    """Horizontal half-FOV. Derived from the vertical one and the aspect."""
    return math.atan(math.tan(math.radians(FOV_DEG) / 2.0) * SCREEN_W / SCREEN_H)


def honest_from_m(error_m: float) -> float:
    """Distance beyond which `error_m` of geometric error is under budget."""
    return max(0.0, error_m) * _px_scale(PIXEL_BUDGET)


def aliases_beyond_m(feature_m: float) -> float:
    """Distance beyond which `feature_m` of detail is below the shading rate."""
    return max(0.0, feature_m) * _px_scale(SHADING_SAMPLE_PX)


# ---------------------------------------------------------------------------
# The human figure, measured
# ---------------------------------------------------------------------------
# INV-020's ruler. 1.75 m is the project's established standing human and is
# already load-bearing (DOWNLIGHT_POOL_M = 1.57 m was solved from it), so it is
# re-used rather than re-chosen -- a second number here would silently
# de-calibrate the interior kit.
HUMAN_STATURE_M = 1.75

# Ratios read off the standing officer in
# `reference/10-interiors-generic-kit/more hallway.jpg`, magnified 8x with
# tools/refzoom.py over the box (0.38, 0.47)-(0.52, 1.00). Working in the
# magnified crop's pixels, the figure runs crown y=205 to sole y=1810, so
# 1605 px = 1.75 m = 917 px/m; every entry below is (that pixel row)/1605
# measured from the crown, converted to a height above the deck.
#
# TWO OF THEM ARE CONTAMINATED AND ARE CORRECTED, WITH THE REASON:
#   * chin measured 0.851 -- the subject has a beard AND the S2-3 uniform has a
#     standing leather collar (`Sheridan.jpg`, authority 2), both of which fill
#     the space under the jaw. Corrected to 0.868; the correction is 1.7% of
#     stature and it is called out rather than absorbed.
#   * biacromial measured 0.249 -- that is across the epaulettes, which the same
#     authority-2 still shows standing proud of the shoulder. Corrected to 0.235.
# Everything else is clean: the hand is bare, the trouser breaks at the knee,
# and the sole is on a lit deck.
FIGURE = {
    "crown":        1.000,   # MEASURED (definition)
    "chin":         0.868,   # MEASURED 0.851, corrected for beard + standing collar
    "neck_base":    0.838,   # DERIVED: chin - 0.30 of head height
    "acromion":     0.818,   # MEASURED 0.835 at the epaulette top, corrected
    "chest":        0.720,   # MEASURED (the plastron's lower edge)
    "waist":        0.545,   # MEASURED (belt centre, y=935)
    "hip":          0.520,   # DERIVED: waist - one belt width
    "fingertip":    0.411,   # MEASURED (y=1150), uncontaminated
    "knee":         0.255,   # MEASURED (y=1400)
    "ankle":        0.045,   # EXTRAPOLATED: below the trouser break, not visible
    "sole":         0.000,   # MEASURED (definition)
    # DERIVED: crown - chin, AFTER the chin correction. The raw measurement
    # gives 0.149 and this is the cross-check working -- correcting the beard
    # and the standing collar out moves head height from 0.149 to 0.132, and
    # 0.132 is where adult head-height-over-stature actually sits. A correction
    # that lands on an independently known value is evidence the correction was
    # the right size, not just the right direction.
    "head_h":       0.132,
    "shoulder_w":   0.235,   # MEASURED 0.249 across epaulettes, corrected
    "chest_d":      0.155,   # EXTRAPOLATED: no frame gives the figure in profile
    "hip_w":        0.180,   # EXTRAPOLATED: narrower than shoulders in the frame
}

# Where the stoop ramp reaches full angle. Above this the shoulder girdle, neck
# and head rotate RIGIDLY as one unit. It has to clear the head's lowest ring,
# which sits below the acromion by construction (`_head_profile` starts at
# t = -0.07 so the chin is buried in the neck) -- ramping to full at the
# acromion put the ramp THROUGH the head and sheared it, which the
# chin-to-crown assertion caught to the tenth of a millimetre.
# 0.35 of the way, not half: the ramp has to finish BELOW every vertex that
# should rotate rigidly, and the lowest of those is the tip of a pak'ma'ra
# tendril at 0.768 of stature -- lower than the chin, because the tendrils hang
# past it. A ramp that ends above a tendril tip shears the tendril.
BEND_TOP = FIGURE["chest"] + 0.35 * (FIGURE["acromion"] - FIGURE["chest"])

# Cross-check that costs nothing and catches a transposed digit: these ratios
# were read off a 1990s television frame at 8x magnification and they land
# within a few percent of standard adult anthropometry (fingertip height ~0.42
# of stature, biacromial ~0.23-0.25, knee ~0.28). Two sources that could not
# have copied each other. Only `knee` is more than 5% out, and the trouser
# break sits above the joint, which is the expected direction of that error.


@dataclass(frozen=True)
class Surface:
    """A species' skin/carapace treatment, as material groups rather than pixels.

    Colour is recorded as a RELATIONSHIP and a named source, per AAA-STANDARD's
    materials checklist: a screencap hex carries the episode's grade and the
    codec's chroma subsampling, so an absolute value would be rigour-shaped and
    wrong. `tones` names the readings taken from the cited file(s); `pattern`
    names what the surface DOES, which is what a shader needs.
    """
    kind: str                # skin | carapace | encounter_suit
    tones: tuple
    pattern: str
    authority: int
    source: str


@dataclass(frozen=True)
class SpeciesBody:
    """One species' body, as numbers.

    Every field is a multiplier on the FIGURE table above except `stature_m`,
    `stature_sigma_m` and `stoop_deg`. A species is therefore a row, and adding
    the sixteenth is a row, not a mesh.
    """
    key: str
    stature_m: float
    stature_sigma_m: float
    build: float             # limb and torso girth multiplier
    shoulder_k: float        # x FIGURE["shoulder_w"]
    leg_k: float             # x the hip height, at constant stature
    arm_k: float             # x the arm length
    head_k: float            # x FIGURE["head_h"]
    cranium: tuple           # (width, height, depth) multipliers on the head box
    jaw_k: float             # jaw width / cranium width -- Narn's is MEASURED
    neck_k: float            # neck length multiplier; 0 sinks the head
    stoop_deg: float         # forward pitch of everything above the chest
    features: tuple          # attachment meshes, in emission order
    surface: Surface
    plan: str = "humanoid"   # humanoid | encounter_suit | column
    note: str = ""
    authority: int = 5
    source: str = ""


# --- the surfaces, each tied to a file that was opened -----------------------

_S_HUMAN = Surface("skin", ("as photographed",), "plain",
                   1, "reference/10-interiors-generic-kit/more hallway.jpg")

# G'Kar more.jpg at 6.25x: the crown is NOT spotted-on-plain. It is a
# RETICULATION -- dark rounded cells separated by a pale raised net, largest on
# the crown, shrinking and fading down the cheek, with a spotted line running
# forward of the ear. The brief's phrase "spotted cranial ridges" describes it
# from a distance; the ridges are the pale net BETWEEN the spots and they are a
# surface relief of a millimetre or two, not geometry. Built as material.
_S_NARN = Surface("skin", ("tan/ochre ground", "dark brown cells", "red iris"),
                  "reticulated: dark cells in a pale raised net, coarse on the "
                  "crown, fading on the cheek",
                  2, "reference/15-races-and-makeup/G'Kar more.jpg")

_S_CENTAURI = Surface("skin", ("as photographed", "dark crest hair"), "plain",
                      1, "reference/04-sector-red/more zocalo.png")

_S_MINBARI = Surface("skin", ("pale", "bone-white crest"), "plain, matte",
                     1, "reference/05-sector-green/rotunda.webp")

# The index is explicit that pak'ma'ra skin tone VARIES BETWEEN INDIVIDUALS --
# `more Pak'ma'ra.webp` is pale blue-grey, `Pak'ma'ra example.webp` is mottled
# tan and olive -- and asks for a tone-variation parameter rather than one skin.
# `tone_index()` below is that parameter.
_S_PAKMARA = Surface("skin", ("pale blue-grey/green", "mottled tan/ochre/olive",
                              "bone-cream at the tendrils"),
                     "wrinkled, matte, radial creasing at the eye; tone varies "
                     "per individual",
                     2, "reference/15-races-and-makeup/more Pak'ma'ra.webp + "
                        "Pak'ma'ra example.webp")

# vorlon.webp is a production photograph with a burned-in studio slate; the
# index's instruction is to build the shell WARM and let lighting do the rest,
# because `More Vorlon.jpg` shows the same shell reading cool purple under
# magenta light. Baking a purple albedo would be a lighting artefact fossilised
# into a material.
_S_VORLON = Surface("encounter_suit",
                    ("mottled tan/olive/amber", "dark veining", "wet gloss"),
                    "cellular: rounded cells in a dark net, high-gloss lacquer; "
                    "the SAME tessellation appears on the bib and on the alien-"
                    "sector wall, so it is a design language not a texture",
                    2, "reference/15-races-and-makeup/vorlon.webp")

_S_GAIM = Surface("encounter_suit", ("EXTRAPOLATED",), "rigid plate, matte",
                  5, "no Gaim frame exists in reference/; see EXTRAPOLATIONS")

_S_GENERIC = Surface("skin", ("EXTRAPOLATED",), "plain",
                     5, "no frame in reference/ shows this species")


# --- feature keys ------------------------------------------------------------
# Ordered so a cull removes the cheapest silhouette first. `FEATURE_TIER` is
# what the LOD feature schedule actually keys on.
FEATURE_TIER = {
    "hair":            "detail",
    "brow":            "detail",
    "hands":           "extremity",
    "feet":            "extremity",
    "centauri_crest":  "identity",
    "minbari_crest":   "identity",
    "pakmara_tendrils": "identity",
    "pakmara_keel":    "identity",
    "abbai_fin":       "identity",
    "gaim_helmet":     "identity",
    "gaim_mantle":     "identity",
    "vorlon_shells":   "identity",
    "vorlon_hood":     "identity",
    "vorlon_tubes":    "identity",
}


# ---------------------------------------------------------------------------
# The fifteen. Counts and shares are FACTIONS.md section 2.4 (authority 5,
# labelled so there); every body number here is ours and is tagged in `note`.
# ---------------------------------------------------------------------------
SPECIES = {
    "human": SpeciesBody(
        "human", HUMAN_STATURE_M, 0.070, 1.00, 1.00, 1.00, 1.00, 1.00,
        (1.00, 1.00, 1.25), 0.78, 1.00, 0.0,
        ("hair", "hands", "feet"), _S_HUMAN,
        note="The reference figure. Stature MEASURED via INV-020's ruler; "
             "sigma 0.070 m EXTRAPOLATED from the spread of adult stature.",
        authority=1,
        source="reference/10-interiors-generic-kit/more hallway.jpg"),

    "narn": SpeciesBody(
        "narn", 1.88, 0.075, 1.14, 1.08, 0.98, 1.00, 1.06,
        # cranium width 1.12: MEASURED. In `G'Kar more.jpg` at 6.25x the head is
        # 1330 crop px tall and 860 px wide at the temples, and only 600 px wide
        # at the jaw -- so jaw/cranium = 0.70 against the human 0.78, and the
        # braincase carries visibly more mass above the eye than a human's.
        (1.12, 1.02, 1.22), 0.70, 0.90, 0.0,
        ("brow", "hands", "feet"), _S_NARN,
        note="Head proportions MEASURED off G'Kar more.jpg (authority 2). "
             "Stature and build EXTRAPOLATED: depicted as physically imposing "
             "and the actor is tall; bounded by the door-height assertion.",
        authority=2, source="reference/15-races-and-makeup/G'Kar more.jpg"),

    "centauri": SpeciesBody(
        "centauri", 1.78, 0.070, 1.03, 1.00, 1.00, 1.00, 1.00,
        (1.00, 1.00, 1.25), 0.78, 1.00, 0.0,
        ("hair", "centauri_crest", "hands", "feet"), _S_CENTAURI,
        note="Crest fan MEASURED off more zocalo.png (authority 1): 1.7x head "
             "width, rising 0.55x face length above the crown, laterally flat. "
             "Male only -- females are shaven (FACTIONS 7.3). Crest breadth "
             "signals rank, so it is the per-individual parameter with the "
             "widest spread.",
        authority=1, source="reference/04-sector-red/more zocalo.png"),

    "minbari": SpeciesBody(
        "minbari", 1.82, 0.065, 0.93, 0.97, 1.03, 1.01, 0.99,
        (1.00, 0.98, 1.22), 0.76, 1.05, 0.0,
        ("minbari_crest", "hands", "feet"), _S_MINBARI,
        note="Crest read off rotunda.webp (authority 1, but the figures are "
             "~60 px tall and the frame is soft): a broad upright bone fin "
             "rising behind and above the crown, WIDER than the skull. Shape "
             "sourced, dimensions EXTRAPOLATED. Slender build from the robed "
             "silhouette.",
        authority=1, source="reference/05-sector-green/rotunda.webp"),

    "drazi": SpeciesBody(
        "drazi", 1.72, 0.060, 1.26, 1.12, 0.94, 0.98, 1.04,
        (1.06, 0.96, 1.18), 0.86, 0.55, 2.0,
        ("brow", "hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2 (authority 4): 'physically robust, "
             "blunt', the League species most often doing the physical work. "
             "Built as the heaviest humanoid: short neck, wide shoulders, "
             "heavy limbs. No Drazi frame exists in reference/.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "brakiri": SpeciesBody(
        "brakiri", 1.76, 0.065, 0.98, 0.98, 1.02, 1.00, 1.00,
        (1.04, 1.04, 1.24), 0.80, 1.00, 0.0,
        ("hair", "hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2: traders and financiers, night "
             "dwellers. Built as an unremarkable humanoid so that the crowd's "
             "night shift reads by dress and behaviour rather than by shape.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "pakmara": SpeciesBody(
        # Stature 1.80 is the ERECT crown height. The 26 degree stoop then
        # carries the crown 0.177 m FORWARD and 0.032 m down (measured in
        # _selftest), which is the pak'ma'ra silhouette: the head is over the
        # toes, not over the hips. Note what it does NOT do -- the overall
        # standing height falls only 0.010 m, because pitching a head forward
        # raises the occiput as much as it lowers the crown. An earlier version
        # of this comment claimed 0.16 m off the standing height; the
        # measurement disproved it and the comment was wrong, not the geometry.
        "pakmara", 1.80, 0.070, 1.18, 1.05, 0.96, 0.98, 1.16,
        (1.10, 1.14, 1.42), 0.62, 0.35, 26.0,
        ("pakmara_keel", "pakmara_tendrils", "hands", "feet"), _S_PAKMARA,
        note="MEASURED off more Pak'ma'ra.webp (authority 2): only 165 px of "
             "a 465 px head stands above the shoulder line, so the head is "
             "carried very low -- the SHORTEST neck of any species here at "
             "0.35. It was 0.0 until the render showed why that reading is "
             "wrong: what the frame shows above the shoulder is a COWL, a "
             "garment, and fusing the skull to the clavicle drove the tendrils "
             "through the chest. Head deep front-to-back and pitched down. "
             "Four tendrils, outer pair longest, reaching 0.5x head height "
             "(authority 3, Pak'ma'ra even more.jpg).",
        authority=2, source="reference/15-races-and-makeup/more Pak'ma'ra.webp"),

    "vree": SpeciesBody(
        "vree", 1.50, 0.050, 0.72, 0.84, 0.92, 1.06, 1.22,
        (1.20, 1.10, 1.10), 0.58, 0.80, 0.0,
        ("hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED and WEAK. FACTIONS 9.2 gives only 'traders; saucer "
             "craft'. Built small and large-headed so the tail of the crowd "
             "has a small silhouette in it; nothing constrains this but the "
             "furniture argument, and a Vree at 1.50 m still uses a 2.10 m "
             "door. Overturned by any frame showing a Vree beside a human.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "abbai": SpeciesBody(
        "abbai", 1.70, 0.060, 1.04, 0.99, 0.98, 0.99, 1.05,
        (1.06, 1.08, 1.20), 0.74, 0.85, 0.0,
        ("abbai_fin", "hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2: League founders, mediators, "
             "amphibian. The amphibian note is the only shape information "
             "anywhere, so it gets one attachment -- a low swept head fin -- "
             "and nothing else.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "gaim": SpeciesBody(
        "gaim", 1.84, 0.045, 1.30, 1.14, 0.94, 0.96, 1.10,
        (1.10, 1.05, 1.15), 0.90, 0.30, 4.0,
        ("gaim_mantle", "gaim_helmet"), _S_GAIM, plan="encounter_suit",
        note="A SUIT, not a body -- see build_encounter_suit(). Rigid plates "
             "with hard edges and gaps, no soft taper, no exposed skin, no "
             "hands or feet (gauntlets and boots are part of the shell). "
             "Sigma is small because a suit is manufactured in sizes rather "
             "than grown. Everything about the Gaim shell is EXTRAPOLATED: "
             "FACTIONS 9.2 gives 'methane breathers in encounter suits, "
             "hive-caste insectoids' (authority 4) and reference/ holds no "
             "Gaim frame at all. Constrained by the only encounter suit we DO "
             "hold -- Kosh's -- which establishes what a B5 encounter suit is: "
             "opaque, floor-reaching, no visible skin, one lens.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "hyach": SpeciesBody(
        "hyach", 1.80, 0.055, 0.94, 0.96, 1.02, 1.00, 1.02,
        (1.02, 1.06, 1.20), 0.72, 1.10, 3.0,
        ("hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2: 'long-lived, formal'. Built tall, "
             "thin and slightly stooped -- age reads as posture at crowd "
             "distance far better than as a texture. Pak'ma'ra.webp shows a "
             "Hyach delegation desk plate but not the delegate.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "llort": SpeciesBody(
        "llort", 1.64, 0.060, 1.10, 1.04, 0.92, 1.08, 1.02,
        (1.02, 0.96, 1.20), 0.84, 0.75, 6.0,
        ("hair", "hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2: 'reputation as scavengers and "
             "thieves'. Short, long-armed and habitually stooped, so a Llort "
             "reads differently in a corridor without a single new mesh.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "grome": SpeciesBody(
        "grome", 1.93, 0.070, 1.34, 1.16, 1.00, 0.96, 1.00,
        (1.04, 0.94, 1.20), 0.88, 0.60, 3.0,
        ("hands", "feet"), _S_GENERIC,
        note="EXTRAPOLATED. FACTIONS 9.2 gives no character at all beyond "
             "'League members', and 9.2's placement is Hydroponics and labour. "
             "Built as the largest humanoid; the door assertion is what stops "
             "this growing.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 9.2"),

    "other": SpeciesBody(
        "other", 1.74, 0.140, 1.00, 1.00, 1.00, 1.00, 1.05,
        (1.05, 1.02, 1.20), 0.78, 0.90, 0.0,
        ("hands", "feet"), _S_GENERIC,
        note="The tail: rare League species, unidentified traders, one-off "
             "visitors. FACTIONS 2.4 asks for a ROTATING model set 'so the "
             "tail never looks like the same six aliens', so this row's "
             "per-individual spread is deliberately ~2x every other row's and "
             "`individual()` widens its build and cranium jitter as well as "
             "its stature. It is a distribution, not a species.",
        authority=5, source="docs/gazetteer/FACTIONS.md section 2.4"),

    "vorlon": SpeciesBody(
        # 2.05 m: the ONE hard constraint available is that the suit uses the
        # station's doors, and interior_kit.PROVISIONAL["door_height_m"] is
        # 2.10 m. _selftest asserts this against the kit's own constant rather
        # than a copy of it, so raising the door raises the ceiling on Kosh and
        # lowering it fails the build.
        "vorlon", 2.05, 0.000, 1.00, 1.00, 0.00, 0.00, 1.00,
        (1.00, 1.00, 1.00), 1.00, 0.00, 0.0,
        ("vorlon_shells", "vorlon_hood", "vorlon_tubes"), _S_VORLON,
        plan="column",
        note="A SINGLETON. FACTIONS 2.4: 'Kosh. A singleton, and it must not be "
             "a share' -- int(250000 x share) for one person rounds to zero or "
             "three. sigma is 0.0 and `individual()` refuses to jitter it: "
             "there is exactly one of these and it is the same every session. "
             "Kosh's suit, NOT more vorlon.png, which reference/00-INDEX.md "
             "session 2s established is a structurally different second suit "
             "(red lamp, hexagonal scaling, horn blades) and out of era.",
        authority=2, source="reference/15-races-and-makeup/vorlon.webp + "
                            "Vorlon moree.jpg"),
}

# FACTIONS.md section 2.4, verbatim. Held here so `crowd_cost()` can weight a
# crowd by the real mix and so `_selftest` can assert the two properties INV-005
# says the previous mix failed: shares summing to exactly 1.0 and counts to
# exactly 250,000. This is a COPY of another file's table and is asserted
# against its own totals rather than trusted.
FACTIONS_MIX = {
    "human": (155_000, 0.620), "narn": (22_500, 0.090),
    "centauri": (17_500, 0.070), "minbari": (12_500, 0.050),
    "drazi": (12_500, 0.050), "brakiri": (7_500, 0.030),
    "pakmara": (6_250, 0.025), "vree": (5_000, 0.020),
    "abbai": (3_750, 0.015), "gaim": (2_500, 0.010),
    "hyach": (1_750, 0.007), "llort": (1_250, 0.005),
    "grome": (750, 0.003), "other": (1_250, 0.005),
}
VORLON_SINGLETON = 1        # hard-coded, never a share
STATION_POPULATION = 250_000


# ---------------------------------------------------------------------------
# Per-individual variation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Individual:
    """One resident's body, resolved. A pure function of (species, npc_id)."""
    species: str
    npc_id: str
    stature_m: float
    build: float
    shoulder_k: float
    head_k: float
    cranium: tuple
    crest_k: float
    stoop_deg: float
    sex: str
    tone_index: int
    pattern_seed: int
    features: tuple


def individual(species: str, npc_id: str) -> Individual:
    """Resolve one resident's body parameters. Deterministic in (species, id).

    AAA-STANDARD, NPCs: "NPC identity is a function of (seed, id) and not of
    iteration order." Nothing in here reads a counter, a list position or a
    clock.
    """
    sp = SPECIES.get(species)
    if sp is None:
        raise KeyError(f"unknown species {species!r}; have {sorted(SPECIES)}")
    seed = f"{species}:{npc_id}"

    if sp.key == "vorlon":
        # There is one Vorlon. Jittering a singleton is how a singleton becomes
        # three slightly different singletons.
        return Individual(species, npc_id, sp.stature_m, sp.build, sp.shoulder_k,
                          sp.head_k, sp.cranium, 1.0, sp.stoop_deg, "none", 0,
                          0, sp.features)

    # The "other" bucket is a distribution, not a species: FACTIONS 2.4 asks for
    # a rotating set, so its shape jitter is widened here rather than by adding
    # fourteen more rows.
    wide = 2.2 if sp.key == "other" else 1.0

    stature = sp.stature_m + _gauss(seed, "stature", sp.stature_sigma_m)
    build = sp.build * (1.0 + _gauss(seed, "build", 0.085 * wide))
    shoulder = sp.shoulder_k * (1.0 + _gauss(seed, "shldr", 0.045 * wide))
    head = sp.head_k * (1.0 + _gauss(seed, "head", 0.030 * wide))
    cran = tuple(c * (1.0 + _gauss(seed, f"cran{i}", 0.040 * wide))
                 for i, c in enumerate(sp.cranium))

    sex = "f" if _u(seed, "sex") < 0.5 else "m"

    # Centauri crest breadth signals rank (FACTIONS 7.3), so its spread is the
    # widest per-individual parameter in the module -- and Centauri females are
    # shaven, so the crest is dropped from the feature list rather than scaled
    # to zero, which would leave a degenerate mesh in the buffer.
    crest = 1.0 + _gauss(seed, "crest", 0.22)
    features = sp.features
    if sp.key == "centauri" and sex == "f":
        # Shaven, not merely crestless (FACTIONS 7.3): the hair cap goes too,
        # or a Centauri woman is a Centauri man with a haircut.
        features = tuple(f for f in features
                         if f not in ("centauri_crest", "hair"))

    stoop = sp.stoop_deg + _gauss(seed, "stoop", 2.5)
    return Individual(species, npc_id, stature, build, shoulder, head, cran,
                      max(0.4, crest), max(0.0, stoop), sex,
                      int(_u(seed, "tone") * len(sp.surface.tones)),
                      int(_u(seed, "pat") * (1 << 24)), features)


# ---------------------------------------------------------------------------
# Primitives. Y is up, +Z is facing -- the same frame as interior_kit, whose
# decks lie in XZ with `ceiling_height_m` along Y.
# ---------------------------------------------------------------------------
def _ring(cx, cy, cz, rx, rz, seg, squash_front=1.0):
    """One closed loop of `seg` points in the XZ plane at height cy.

    `squash_front` scales +Z only, which is how a chest gets a flatter back than
    front without a second radius parameter.
    """
    out = []
    for i in range(seg):
        t = math.tau * i / seg
        z = rz * math.sin(t)
        if z > 0:
            z *= squash_front
        out.append((cx + rx * math.cos(t), cy, cz + z))
    return out


def _loft(rings, cap_lo=True, cap_hi=True):
    """Skin a stack of equal-length rings. Winding is OUTWARD.

    Derivation of the winding, because "it looked right" is how four subsystems
    in this repository shipped inside-out. For a ring wound x=cos(t), z=sin(t)
    stacked in ASCENDING y, the quad (a_i, b_i, b_i+1) has normal (h*r, 0, h*r)
    at the +x+z corner -- radially outward. The order (a_i, a_i+1, b_i+1) gives
    the negative of that. Top cap fans (hi_0, hi_i+1, hi_i) to face +Y; bottom
    cap fans (lo_0, lo_i, lo_i+1) to face -Y.

    THE STACK DIRECTION IS NORMALISED HERE AND THAT IS NOT COSMETIC. Arms and
    legs are naturally authored root-to-tip, which for a standing figure means
    DESCENDING y, and a descending stack lofts every one of them inside-out.
    The first run of `_selftest` caught exactly that: 60 failures reading
    "arm is inside-out (signed volume -0.004546)" across every humanoid species,
    on geometry that renders perfectly and is shaded from the inside. Rather
    than ask every caller to remember, the stack is reversed here and the caps
    swap with it. A horizontal stack has no answer and raises instead of
    guessing, because a silent guess is the failure mode this whole paragraph
    exists to prevent.
    """
    lo_y = sum(v[1] for v in rings[0]) / len(rings[0])
    hi_y = sum(v[1] for v in rings[-1]) / len(rings[-1])
    if abs(hi_y - lo_y) < 1e-9:
        raise ValueError("_loft cannot orient a stack with no vertical extent")
    if hi_y < lo_y:
        rings = list(reversed(rings))
        cap_lo, cap_hi = cap_hi, cap_lo
    verts, tris = [], []
    n = len(rings[0])
    for r in rings:
        if len(r) != n:
            raise ValueError("loft rings must all have the same length")
        verts.extend(r)
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            tris.append((a + i, b + i, b + j))
            tris.append((a + i, b + j, a + j))
    if cap_lo:
        for i in range(1, n - 1):
            tris.append((0, i, i + 1))
    if cap_hi:
        b = (len(rings) - 1) * n
        for i in range(1, n - 1):
            tris.append((b, b + i + 1, b + i))
    return verts, tris


def signed_volume(verts, tris):
    """Six-times signed volume. Positive means outward winding.

    Same formula as `station/components.signed_volume`; `_selftest` asserts the
    two agree on a unit cube when components is importable, so this copy cannot
    drift from the one the rest of the station is gated on.
    """
    v6 = 0.0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        v6 += (p[0] * (q[1] * r[2] - q[2] * r[1])
               - p[1] * (q[0] * r[2] - q[2] * r[0])
               + p[2] * (q[0] * r[1] - q[1] * r[0]))
    return v6 / 6.0


def edge_census(tris):
    """(boundary, non_manifold) edge counts.

    A closed solid has zero of both. A face shared by three triangles renders
    perfectly and is a modelling error, which is why it is counted separately
    rather than folded into "not closed".
    """
    use = {}
    for a, b, c in tris:
        for p, q in ((a, b), (b, c), (c, a)):
            use[(min(p, q), max(p, q))] = use.get((min(p, q), max(p, q)), 0) + 1
    return (sum(1 for v in use.values() if v == 1),
            sum(1 for v in use.values() if v > 2))


# A deliberately generic ray direction. An axis-aligned ray is the classic
# ray-casting trap and this module walked straight into it: the torso's own
# rings put vertices at exactly z = 0, the leg's root ring does too, and a +X
# ray from such a point grazes the shared edge, counts the crossing once or
# twice depending on floating-point luck, and reports the point as outside. The
# only vertices `contains()` ever rejected were the ones at z = 0 exactly.
_RAY = (1.0, 0.0037411, 0.0091733)


def contains(verts, tris, p, eps=1e-9):
    """Is point `p` inside the closed mesh? Ray parity along `_RAY`.

    Exists because the hip gap was found by LOOKING -- the first lineup render
    had magenta showing through the pelvis of every short-legged species -- and
    a defect found by looking comes back the moment nobody looks. A render can
    only say a hole is visible FROM THIS CAMERA; this says the leg root is
    inside the torso, from every camera and at every LOD.
    """
    dx, dy, dz = _RAY
    hits = 0
    for ia, ib, ic in tris:
        a, b, c = verts[ia], verts[ib], verts[ic]
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        h = (dy * e2[2] - dz * e2[1], dz * e2[0] - dx * e2[2],
             dx * e2[1] - dy * e2[0])
        det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
        if abs(det) < eps:
            continue
        inv = 1.0 / det
        sv = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
        u = (sv[0] * h[0] + sv[1] * h[1] + sv[2] * h[2]) * inv
        if u < 0.0 or u > 1.0:
            continue
        q = (sv[1] * e1[2] - sv[2] * e1[1], sv[2] * e1[0] - sv[0] * e1[2],
             sv[0] * e1[1] - sv[1] * e1[0])
        v = (dx * q[0] + dy * q[1] + dz * q[2]) * inv
        if v < 0.0 or u + v > 1.0:
            continue
        if (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv > eps:
            hits += 1
    return hits % 2 == 1


def facing_fraction(verts, tris, eye):
    """Fraction of triangles that survive backface culling from `eye`.

    Replicates the test in `tools/preview_render.py`: a triangle is drawn when
    its geometric normal points into the half-space containing the eye. On a
    closed solid this is about half; on an inside-out one it is the complement,
    and the render still shows a figure -- shaded from the inside. That is
    exactly the failure a render cannot report, so it is measured here.
    """
    n = 0
    for a, b, c in tris:
        p, q, r = verts[a], verts[b], verts[c]
        u = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
        w = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
        nx = u[1] * w[2] - u[2] * w[1]
        ny = u[2] * w[0] - u[0] * w[2]
        nz = u[0] * w[1] - u[1] * w[0]
        cx = (p[0] + q[0] + r[0]) / 3.0
        cy = (p[1] + q[1] + r[1]) / 3.0
        cz = (p[2] + q[2] + r[2]) / 3.0
        if (nx * (eye[0] - cx) + ny * (eye[1] - cy) + nz * (eye[2] - cz)) > 0.0:
            n += 1
    return n / max(1, len(tris))


class Mesh:
    """Vertex/triangle accumulator with OBJ group spans, per part.

    Parts are kept as separate CLOSED shells that interpenetrate rather than
    being welded: an arm root sits inside the torso. That is the standard way a
    game character is built and it keeps every part individually testable for
    closure -- welding would make `signed_volume` per part meaningless and hide
    an inside-out limb inside a correct torso.
    """

    def __init__(self):
        self.verts, self.tris, self.spans, self.parts = [], [], [], []

    def add(self, verts, tris, group, part=None):
        b, lo = len(self.verts), len(self.tris)
        self.verts.extend(verts)
        self.tris.extend((a + b, c + b, d + b) for a, c, d in tris)
        self.spans.append((group, lo, len(self.tris)))
        self.parts.append((part or group, list(verts), list(tris)))
        return self

    def bbox(self):
        xs = [v[0] for v in self.verts]
        ys = [v[1] for v in self.verts]
        zs = [v[2] for v in self.verts]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def as_tuple(self):
        return self.verts, self.tris, self.spans

    def __len__(self):
        return len(self.tris)


def _normalise_stature(m: "Mesh", part: str, stature_m: float):
    """Scale the whole figure uniformly so `part`'s top lands at `stature_m`.

    `stature_m` has to BE the standing height or nothing downstream can use it:
    the door-clearance assertion, the impostor card and the crowd density all
    read it. Before this existed the head was placed at acromion + neck + head
    and the three ratios did not close, so a Narn built to a stated 1.88 m
    actually stood 2.116 m and failed the 2.10 m door -- which is how this
    function came to exist rather than by design.

    Uniform, so no proportion changes and no winding can flip. Measured on the
    head (or helmet, or head assembly) rather than on the bounding box, because
    a Minbari crest legitimately rises above the crown and stature is measured
    to the crown -- the crest is then correctly ABOVE the stated stature, and
    the door check uses the bounding box, which is what a door cares about.
    """
    if part is None:                       # the whole silhouette IS the height
        tops = [m.bbox()[4]]
    else:
        tops = [max(v[1] for v in verts)
                for name, verts, _t in m.parts if name == part]
    if not tops:
        raise KeyError(f"no part named {part!r} to normalise against")
    k = stature_m / max(tops)
    m.verts = [(x * k, y * k, z * k) for x, y, z in m.verts]
    m.parts = [(n, [(x * k, y * k, z * k) for x, y, z in v], t)
               for n, v, t in m.parts]
    return m


def _bend(m: "Mesh", deg: float, pivot_y: float, full_y: float):
    """Stoop, as a graded forward rotation about +X, applied to vertices.

    A stoop is a rotation and not a shorter stature: the pak'ma'ra reference
    shows a long skeleton carried low, so the bone lengths must survive and only
    the pose changes -- otherwise the same character cannot straighten in an
    animation without becoming a different size.

    Graded: nothing below `pivot_y` moves, the rotation ramps to full at
    `full_y` (the shoulder) and everything above -- neck, head, crest, tendrils
    -- is carried rigidly at the full angle. A single rigid rotation of the
    whole upper body would swing the hips; a linear ramp from the ankles would
    bend the legs.
    """
    if abs(deg) < 1e-9:
        return m
    span = max(full_y - pivot_y, 1e-6)

    def bend(v):
        x, y, z = v
        f = min(1.0, max(0.0, (y - pivot_y) / span))
        if f <= 0.0:
            return v
        a = math.radians(deg) * f
        c, s = math.cos(a), math.sin(a)
        dy = y - pivot_y
        return (x, pivot_y + dy * c - z * s, z * c + dy * s)

    m.verts = [bend(v) for v in m.verts]
    m.parts = [(n, [bend(v) for v in vs], t) for n, vs, t in m.parts]
    return m


# ---------------------------------------------------------------------------
# The base topology
# ---------------------------------------------------------------------------
# The ring plan. IDENTICAL for every species and every LOD, so a coarser level
# is a strict SUBSET of a finer one -- `_selftest` measures that as a set
# operation rather than trusting this comment. `stride` picks every other entry
# with 0 and -1 pinned, which is why the count is odd.
TORSO_RINGS = ("hip", "pelvis", "waist", "lower_chest", "chest", "upper_chest",
               "shoulder", "trapezius")
LIMB_RINGS = 5           # root, upper mid, joint, lower mid, tip
HEAD_RINGS = 7


def _leg_params(ind: Individual, sp: SpeciesBody):
    """(hip height, lateral offset, thigh radius, ankle radius), all as
    fractions of stature.

    Pulled out of `build_humanoid` because the torso's lowest ring is DERIVED
    from these rather than authored beside them. It was authored beside them,
    and the render showed the consequence at once: `leg_k` moved the leg root
    without moving the torso's hip ring, so every species with shorter legs --
    Drazi at 0.94 -- had a 5.6 cm band of open pelvis with the magenta
    background showing straight through it. Consistency by construction, which
    is rule 4 of CLAUDE.md applied to a body instead of to a hull.
    """
    b = ind.build
    return (FIGURE["hip"] * sp.leg_k,
            FIGURE["hip_w"] * 0.5 * 0.55,
            0.048 * b,
            0.026 * b)


def _torso_profile(ind: Individual, sp: SpeciesBody):
    """(name, height_fraction, half_width, half_depth) per torso ring."""
    b = ind.build
    sw = FIGURE["shoulder_w"] * ind.shoulder_k * 0.5
    hip_y, lx, r_th, _r_an = _leg_params(ind, sp)
    # Wide enough to CONTAIN both leg roots, not merely to look about right.
    hw = max(FIGURE["hip_w"] * 0.5 * b, (lx + r_th) * 1.12)
    cd = FIGURE["chest_d"] * 0.5 * b
    # The hip's DEPTH has to cover the leg circle too, not only its width. The
    # heaviest builds (Grome at 1.34) failed on exactly two vertices per leg --
    # the ones at 90 degrees, where the ellipse is shallowest relative to a
    # circle -- which is the kind of two-vertex leak a render never shows.
    cd_hip = max(cd * 0.92, r_th * 1.30)
    # TWO rings straddle the hip joint rather than one sitting on it. With a
    # single ring at `hip_y` the torso has already begun narrowing toward the
    # waist by the time the leg root arrives, and `contains()` found 7 of a
    # Grome's 8 leg-root vertices outside the solid -- the same defect the first
    # lineup render showed as magenta across the pelvis, but measured, per
    # species, and at every LOD.
    return [
        ("hip",          hip_y - 0.035,                   hw * 1.00, cd_hip),
        # Placed BETWEEN the hip and the waist rather than a fixed 0.030 above
        # the hip: with a fixed offset, a species with long legs (Minbari at
        # leg_k 1.03) pushes the pelvis ring ABOVE the waist ring, the stack
        # stops being monotonic in y, the loft folds back on itself and the
        # solid self-intersects. `contains()` then returns nonsense -- which is
        # how this was found, as two leg-root vertices "outside" a torso that
        # was 0.25 m wide at that height.
        ("pelvis",       hip_y + 0.55 * (FIGURE["waist"] - hip_y),
                                                          hw * 1.00, cd_hip),
        ("waist",        FIGURE["waist"],                 hw * 0.88, cd * 0.80),
        ("lower_chest",  0.615,                           hw * 0.98, cd * 0.94),
        ("chest",        FIGURE["chest"],                 sw * 0.86, cd * 1.00),
        ("upper_chest",  0.772,                           sw * 0.96, cd * 0.96),
        ("shoulder",     FIGURE["acromion"],              sw * 1.00, cd * 0.86),
        # The torso used to end on the acromion ring, and the render showed
        # exactly what that is: a flat elliptical disc across the top of the
        # shoulders, lit like a table. A body closes with the trapezius sloping
        # up to the neck, so the last ring is small and high and the shoulder
        # becomes an edge rather than a lid.
        ("trapezius",    FIGURE["acromion"] + 0.024,      sw * 0.40, cd * 0.52),
    ]


def _head_profile(ind: Individual):
    """(t, radius_scale, z offset in head heights) from below the chin to crown.

    A head is not an ellipsoid, and the first version of this table was one --
    the render showed an egg with no jaw and no face plane. Three things make it
    a head: the jaw end is narrow and set slightly FORWARD, the widest ring is
    at the parietal a little more than half way up, and the whole stack drifts
    BACKWARD as it rises so the occiput overhangs the neck while the face stays
    near vertical. The jaw end is additionally scaled by `jaw_k`, the one number
    in this table MEASURED off an alien rather than assumed: 0.70 for the Narn
    against 0.78 for a human, from the 600 px jaw and 860 px temple width in
    `G'Kar more.jpg`.

    t = -0.07 rather than 0.0 at the bottom: the lowest ring is buried inside
    the neck. Coplanar caps read as a step, and at conversation distance a step
    under the chin is the first thing the eye finds.
    """
    return ((-0.07, 0.50, +0.020), (0.06, 0.66, +0.018), (0.20, 0.86, +0.008),
            (0.40, 0.99, -0.012), (0.58, 1.00, -0.028), (0.80, 0.88, -0.044),
            (1.00, 0.44, -0.052))


def _limb(p0, p1, r0, r1, seg, bulge=1.12, bulge_at=0.5, rings=LIMB_RINGS):
    """A tapered limb from p0 to p1 as a loft of `rings` rings.

    `bulge` puts a muscle belly at `bulge_at` so an arm is not a cone. The
    joint ring is pinned at bulge_at, which is what makes the PROFILE LOD
    schedule interesting: dropping the joint ring on a limb with a 12% bulge is
    a measurable silhouette error and dropping a mid-shaft ring is not.
    """
    out = []
    ax, ay, az = p0
    bx, by, bz = p1
    for k in range(rings):
        t = k / (rings - 1)
        r = r0 + (r1 - r0) * t
        r *= 1.0 + (bulge - 1.0) * math.sin(math.pi * min(1.0, t / max(bulge_at, 1e-6))
                                            if t <= bulge_at else
                                            math.pi * (1.0 - (t - bulge_at)
                                                       / max(1e-6, 1.0 - bulge_at)))
        out.append(_ring(ax + (bx - ax) * t, ay + (by - ay) * t,
                         az + (bz - az) * t, r, r, seg))
    return out


def _stride(seq, stride):
    """Every `stride`-th entry with the first and last pinned.

    Pinning matters: dropping the shoulder ring or the sole ring shortens the
    figure, which is a different error from smoothing it, and the PROFILE
    schedule measures deviation rather than length.
    """
    if stride <= 1:
        return list(seq)
    keep = list(range(0, len(seq), stride))
    if keep[-1] != len(seq) - 1:
        keep.append(len(seq) - 1)
    return [seq[i] for i in keep]


def build_humanoid(ind: Individual, sp: SpeciesBody, seg=16, ring_stride=1,
                   features="all"):
    """The base topology: torso, head, two arms, two legs, plus attachments."""
    m = Mesh()
    H = ind.stature_m
    b = ind.build
    keep = _feature_filter(features)

    # --- torso ------------------------------------------------------------
    prof = _torso_profile(ind, sp)
    rings = [_ring(0.0, f * H, 0.0, w * H, d * H, seg, squash_front=1.08)
             for _n, f, w, d in prof]
    rings = _stride(rings, ring_stride)
    m.add(*_loft(rings), "npc_%s_torso" % sp.surface.kind, "torso")

    # --- neck and head ----------------------------------------------------
    head_h = FIGURE["head_h"] * ind.head_k * H
    # The neck is the MEASURED chin-to-acromion gap, scaled by the species.
    # It was an independent 0.055 constant until the stature normalisation
    # showed the three ratios did not close.
    neck_len = (FIGURE["chin"] - FIGURE["acromion"]) * H * sp.neck_k
    sh_y = FIGURE["acromion"] * H
    chin_y = sh_y + neck_len
    neck_r = 0.030 * H * b * (0.6 + 0.6 * sp.neck_k)
    if sp.neck_k > 0.05:
        # Ends ABOVE the chin plane and narrower than the head's lowest ring, so
        # the head swallows the joint. Ending at the chin left the neck's top
        # cap visible as a disc with the head balanced on it.
        m.add(*_loft([_ring(0.0, sh_y - 0.02 * H, -0.004 * H,
                            neck_r * 1.30, neck_r * 1.30, seg),
                      _ring(0.0, chin_y + 0.010 * H, -0.006 * H,
                            neck_r * 0.86, neck_r * 0.94, seg)]),
              "npc_%s_neck" % sp.surface.kind, "neck")

    cw, ch, cd = ind.cranium
    hw = head_h * 0.36 * cw          # half-width at the widest ring
    hd = head_h * 0.36 * cd
    hrings = []
    for t, k, zo in _head_profile(ind):
        jk = sp.jaw_k + (1.0 - sp.jaw_k) * min(1.0, max(0.0, t) / 0.34)
        # squash_front < 1 flattens the +Z half only: the face is a plane and
        # the back of the skull is a dome, which is what separates a head from
        # a solid of revolution at any distance where the profile reads.
        hrings.append(_ring(0.0, chin_y + head_h * ch * t, head_h * zo,
                            hw * k * jk, hd * k * jk, seg, squash_front=0.88))
    m.add(*_loft(hrings), "npc_%s_head" % sp.surface.kind, "head")

    # --- arms -------------------------------------------------------------
    # +0.005 rather than -0.02: the arm's root ring now sits INSIDE the torso
    # instead of level with its side, which is what left a lit disc floating at
    # each shoulder in the first render.
    arm_top = FIGURE["acromion"] + 0.005
    arm_bot = FIGURE["fingertip"] + 0.030      # wrist; the hand carries the rest
    span = (arm_top - arm_bot) * sp.arm_k
    sw_h = FIGURE["shoulder_w"] * ind.shoulder_k * 0.5 * H
    # The root is INBOARD and NARROW; the deltoid is the bulge just below it.
    # Rooting the arm at the shoulder's own half-width put its top cap level
    # with the torso's side, which reads as a lit disc floating at the shoulder
    # and which `contains()` reports as 9 of 8 root vertices outside the solid.
    ax_in, ax = sw_h * 0.44, sw_h * 0.96
    r_up, r_wr = 0.028 * H * b, 0.022 * H * b
    lseg = max(4, seg // 2)
    for side in (-1, 1):
        arm = _limb((side * ax_in, arm_top * H, 0.0),
                    (side * ax, (arm_top - span) * H, 0.0),
                    r_up, r_wr, lseg, bulge=1.30, bulge_at=0.16)
        arm = _stride(arm, ring_stride)
        m.add(*_loft(arm), "npc_%s_arm" % sp.surface.kind, "arm")
        if "hands" in keep and "hands" in ind.features:
            hy = (arm_top - span) * H
            m.add(*_loft([
                _ring(side * ax, hy, 0.0, r_wr, r_wr * 0.8, lseg),
                _ring(side * ax * 1.01, hy - 0.055 * H, 0.02 * H,
                      r_wr * 1.35, r_wr * 0.85, lseg),
                _ring(side * ax * 1.01, hy - 0.098 * H, 0.015 * H,
                      r_wr * 0.55, r_wr * 0.45, lseg)]),
                "npc_%s_hand" % sp.surface.kind, "hand")

    # --- legs -------------------------------------------------------------
    # Rooted a little ABOVE the torso's lowest ring so the two solids overlap.
    # Coplanar caps leave a hairline the renderer shows as background, and
    # background is the colour a hole is.
    hip_f, lx_f, rth_f, ran_f = _leg_params(ind, sp)
    hip_y = hip_f
    ank_y = FIGURE["ankle"]
    lx = lx_f * H
    r_th, r_an = rth_f * H, ran_f * H
    for side in (-1, 1):
        leg = _limb((side * lx, hip_y * H, 0.0), (side * lx, ank_y * H, 0.0),
                    r_th, r_an, lseg, bulge=1.10, bulge_at=0.55)
        leg = _stride(leg, ring_stride)
        m.add(*_loft(leg), "npc_%s_leg" % sp.surface.kind, "leg")
        if "feet" in keep and "feet" in ind.features:
            foot = [_ring(side * lx, ank_y * H, 0.0, r_an, r_an, lseg),
                    _ring(side * lx, 0.012 * H, 0.020 * H, r_an * 1.05,
                          r_an * 1.9, lseg),
                    _ring(side * lx, 0.006 * H, 0.045 * H, r_an * 0.9,
                          r_an * 2.4, lseg)]
            m.add(*_loft(foot), "npc_%s_foot" % sp.surface.kind, "foot")

    # --- species attachments ----------------------------------------------
    for f in ind.features:
        if f in ("hands", "feet") or f not in keep:
            continue
        fn = _FEATURES.get(f)
        if fn is not None:
            fn(m, ind, sp, seg, chin_y, head_h, hw, hd)

    # Stature last, pose after it: `stature_m` is the ERECT crown height, so it
    # is fixed before the stoop is applied and the stoop then genuinely lowers
    # the standing figure. Doing it the other way round would normalise the
    # stoop away and make `stoop_deg` a parameter with no visible effect.
    _normalise_stature(m, "head", ind.stature_m)
    return _bend(m, ind.stoop_deg, FIGURE["chest"] * ind.stature_m,
                 BEND_TOP * ind.stature_m)


# ---------------------------------------------------------------------------
# Species attachments
# ---------------------------------------------------------------------------
def _blade(m, group, part, cx, cy, cz, half_w, height, thick, seg,
           sweep=0.0, taper=0.35, rings=4):
    """A laterally-flattened fan/fin: the shape a crest is.

    Built as a loft of flattened rings rather than as a box, so it shares the
    `_loft` winding derivation and the same closure guarantee. `sweep` leans the
    top backward in -Z, which is what both the Centauri hair fan and the Minbari
    bone crest do.
    """
    out = []
    for k in range(rings):
        t = k / (rings - 1)
        w = half_w * (1.0 - (1.0 - taper) * t * t) if taper < 1.0 else half_w * (
            1.0 + (taper - 1.0) * t)
        out.append(_ring(cx, cy + height * t, cz - sweep * t,
                         max(w, 1e-4), max(thick * (1.0 - 0.45 * t), 1e-4),
                         max(4, seg // 2)))
    m.add(*_loft(out), group, part)


def _f_hair(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """A skull cap. Cheap, and the difference between a person and a mannequin."""
    top = chin_y + head_h * ind.cranium[1]
    rings = [_ring(0.0, chin_y + head_h * 0.60, 0.0, hw * 1.02, hd * 1.02, seg),
             _ring(0.0, chin_y + head_h * 0.86, -hd * 0.04, hw * 0.90, hd * 0.94, seg),
             _ring(0.0, top + head_h * 0.02, -hd * 0.05, hw * 0.42, hd * 0.44, seg)]
    m.add(*_loft(rings), "npc_hair", "hair")


def _f_brow(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """A brow shelf. G'Kar more.jpg shows deep vertical furrows under a heavy
    supraorbital ridge; at crowd distance the ridge is the part that reads."""
    y = chin_y + head_h * 0.60
    rings = [_ring(0.0, y - head_h * 0.05, hd * 0.30, hw * 0.80, hd * 0.34, max(6, seg // 2)),
             _ring(0.0, y + head_h * 0.05, hd * 0.34, hw * 0.86, hd * 0.30, max(6, seg // 2))]
    m.add(*_loft(rings), "npc_%s_brow" % sp.surface.kind, "brow")


def _f_centauri_crest(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """The male hair fan, MEASURED off `more zocalo.png` at 5.9x.

    In that crop the face is 500 px across the cheekbones and the fan is 920 px
    across the top -- 1.84x -- and the fan stands 310 px above where the hair
    leaves the skull against a 560 px face length, so 0.55x. Taken as 1.7x and
    0.55x here because the subject is leaning and the fan is therefore seen
    slightly wider than broadside. It is a FAN: wide across, thin front to back,
    and it FLARES at the top rather than tapering, which is the opposite of
    every other crest in the module and is why `taper` can exceed 1.
    """
    half_w = hw * 1.70 * ind.crest_k * 0.5
    _blade(m, "npc_hair", "centauri_crest", 0.0,
           chin_y + head_h * 0.80, -hd * 0.10,
           hw * 0.55, head_h * 0.55 * ind.crest_k, hd * 0.30, seg,
           sweep=hd * 0.22, taper=max(1.05, half_w / max(hw * 0.55, 1e-6)),
           rings=4)


def _f_minbari_crest(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """The bone crest.

    `rotunda.webp` is authority 1 and is the only Minbari reference in the repo,
    but the figures are ~60 px tall: what it establishes is the SHAPE -- a broad
    upright fin rising behind and above the crown, wider than the skull -- and
    not its size. Sizes are EXTRAPOLATED. Swept back rather than upright because
    every figure in that frame shows the crest behind the ear line.
    """
    _blade(m, "npc_crest", "minbari_crest", 0.0,
           chin_y + head_h * 0.72, -hd * 0.35,
           hw * 1.18, head_h * 0.46, hd * 0.26, seg,
           sweep=hd * 0.45, taper=0.72, rings=4)


def _f_pakmara_keel(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """The fore-aft crown keel, authority 3 (`Pak'ma'ra even more.jpg`)."""
    y = chin_y + head_h * 0.86
    rings = [_ring(0.0, y - head_h * 0.06, hd * 0.55, hw * 0.10, hd * 0.30, 6),
             _ring(0.0, y + head_h * 0.06, hd * 0.05, hw * 0.13, hd * 0.62, 6),
             _ring(0.0, y + head_h * 0.02, -hd * 0.55, hw * 0.09, hd * 0.30, 6)]
    m.add(*_loft(rings), "npc_skin_keel", "pakmara_keel")


def _f_pakmara_tendrils(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """Four tendrils, outer pair longest. NOT a two-lobed trunk.

    FACTIONS 9.2 flags the two-lobed-trunk reading as an error and cites
    `Pak'ma'ra even more.jpg` (authority 3) for four thick tapering tendrils
    hanging from below eye level past the chin, the outer two longest, fleshy
    and ringed with fine transverse creases. Length 0.5x head height is MEASURED
    off `more Pak'ma'ra.webp`: 240 px of tendril against 465 px of head.
    """
    lengths = (0.58, 0.40, 0.40, 0.58)
    xs = (-0.58, -0.20, 0.20, 0.58)
    for x, L in zip(xs, lengths):
        n = 3
        rings = []
        for k in range(n):
            t = k / (n - 1)
            # Hung off the FACE (+Z) and reaching below the chin, not off the
            # jaw line: the first version started at the ear plane and the
            # render put four small spikes inside the cowl, where the reference
            # shows them falling clear of the chin toward the chest.
            rings.append(_ring(hw * x * (1.0 - 0.30 * t),
                               chin_y + head_h * 0.22 - head_h * L * t,
                               hd * (1.30 + 0.25 * t),
                               head_h * (0.088 - 0.052 * t),
                               head_h * (0.088 - 0.052 * t), 6))
        m.add(*_loft(rings), "npc_skin_tendril", "pakmara_tendrils")


def _f_abbai_fin(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """A low swept head fin. EXTRAPOLATED from one word: 'amphibian'."""
    _blade(m, "npc_crest", "abbai_fin", 0.0,
           chin_y + head_h * 0.80, -hd * 0.20,
           hw * 0.62, head_h * 0.22, hd * 0.20, seg,
           sweep=hd * 0.55, taper=0.55, rings=3)


_FEATURES = {
    "hair": _f_hair,
    "brow": _f_brow,
    "centauri_crest": _f_centauri_crest,
    "minbari_crest": _f_minbari_crest,
    "pakmara_keel": _f_pakmara_keel,
    "pakmara_tendrils": _f_pakmara_tendrils,
    "abbai_fin": _f_abbai_fin,
}


# ---------------------------------------------------------------------------
# Encounter suits. A SUIT IS NOT A BODY.
# ---------------------------------------------------------------------------
# A body tapers continuously and every ring is a smooth interpolation of its
# neighbours. A suit does not: it is a set of rigid shells with hard edges,
# constant-section barrels, an overhanging mantle and a gap between plates. The
# difference shows in the LOD chain as well as in the silhouette -- a suit's
# PROFILE error is dominated by the plate edges, so its ring schedule is
# stricter than a body's, and `profile_schedule()` measures that rather than
# assuming one number for both.
def build_encounter_suit(ind: Individual, sp: SpeciesBody, seg=16, ring_stride=1,
                         features="all"):
    """The Gaim suit: helmet, mantle, barrel torso, plated limbs, boots.

    EXTRAPOLATED throughout -- reference/ holds no Gaim frame. What constrains
    it is the only encounter suit the repository does hold, Kosh's: opaque,
    reaching the floor, no visible skin, no visible legs at the hem, and one
    lens. The Gaim suit departs from that in exactly one respect -- it has legs,
    because FACTIONS 9.2 puts Gaim in cargo and labour, and a labourer in a
    floor-length robe cannot work a dock.
    """
    m = Mesh()
    H = ind.stature_m
    b = ind.build
    keep = _feature_filter(features)
    g = "npc_suit"

    # Barrel torso: constant section between hard shoulders, unlike a body.
    prof = [(FIGURE["hip"] - 0.02, 0.108, 0.088),
            (FIGURE["waist"], 0.112, 0.092),
            (FIGURE["chest"], 0.124, 0.100),
            (FIGURE["acromion"] - 0.015, 0.128, 0.102),
            (FIGURE["acromion"], 0.128, 0.102)]
    rings = [_ring(0.0, f * H, 0.0, w * b * H, d * b * H, seg) for f, w, d in prof]
    rings = _stride(rings, ring_stride)
    m.add(*_loft(rings), g, "suit_torso")

    if "gaim_mantle" in keep:
        # The overhanging shoulder mantle: the one silhouette cue that says
        # "suit" at 40 m, where the helmet is four pixels.
        mr = [_ring(0.0, (FIGURE["acromion"] - 0.055) * H, 0.0,
                    0.130 * b * H, 0.106 * b * H, seg),
              _ring(0.0, (FIGURE["acromion"] + 0.010) * H, 0.0,
                    0.176 * b * H, 0.142 * b * H, seg),
              _ring(0.0, (FIGURE["acromion"] + 0.030) * H, 0.0,
                    0.150 * b * H, 0.122 * b * H, seg)]
        m.add(*_loft(mr), g, "gaim_mantle")

    if "gaim_helmet" in keep:
        y0 = (FIGURE["acromion"] + 0.028) * H
        hh = FIGURE["head_h"] * ind.head_k * H * 1.05
        hr = [_ring(0.0, y0, 0.0, hh * 0.30, hh * 0.30, seg),
              _ring(0.0, y0 + hh * 0.30, hh * 0.04, hh * 0.44, hh * 0.46, seg),
              _ring(0.0, y0 + hh * 0.66, hh * 0.02, hh * 0.42, hh * 0.44, seg),
              _ring(0.0, y0 + hh * 1.00, -hh * 0.06, hh * 0.20, hh * 0.22, seg)]
        m.add(*_loft(hr), g, "gaim_helmet")

    lseg = max(4, seg // 2)
    arm_top, arm_bot = FIGURE["acromion"] - 0.03, FIGURE["fingertip"]
    ax = 0.132 * b * H
    for side in (-1, 1):
        arm = _limb((side * ax, arm_top * H, 0.0),
                    (side * ax * 1.04, arm_bot * H, 0.0),
                    0.040 * H * b, 0.032 * H * b, lseg, bulge=1.02, bulge_at=0.5)
        arm = _stride(arm, ring_stride)
        m.add(*_loft(arm), g, "suit_arm")
    lx = FIGURE["hip_w"] * 0.5 * H * 0.60
    for side in (-1, 1):
        leg = _limb((side * lx, (FIGURE["hip"] - 0.02) * H, 0.0),
                    (side * lx, 0.010 * H, 0.010 * H),
                    0.052 * H * b, 0.040 * H * b, lseg, bulge=1.02, bulge_at=0.5)
        leg = _stride(leg, ring_stride)
        m.add(*_loft(leg), g, "suit_leg")
    # A suit has no crown to measure to: the helmet top IS the height, and the
    # mantle is inside it, so the whole silhouette normalises.
    _normalise_stature(m, None, ind.stature_m)
    return _bend(m, ind.stoop_deg, FIGURE["chest"] * ind.stature_m,
                 BEND_TOP * ind.stature_m)


def build_column(ind: Individual, sp: SpeciesBody, seg=16, ring_stride=1,
                 features="all"):
    """Kosh. A singleton, and unlike anything else on the station.

    `Vorlon moree.jpg` (authority 2) is the only full-height view we hold: a
    tall tapering column, widest at the shoulders, FLOOR-LENGTH WITH NO VISIBLE
    LEGS, standing like a monolith, the robe hanging in a slight A-line. So the
    base topology does not apply -- there is no hip, no knee, no arm.

    `vorlon.webp` (authority 2, studio slate BAB5-06) gives the head assembly:
    two lateral shells sweeping forward and inward like curved mandibles, a
    central hood rising between them, a collar/yoke ring under both. MEASURED in
    that frame: the assembly is 770 px wide and 565 px tall, W/H = 1.36, and the
    robe at the collar is 680 px -- so THE HEAD IS WIDER THAN THE SHOULDERS,
    1.13x. That single ratio is most of what makes the silhouette read as Kosh
    and not as a robed man.
    """
    m = Mesh()
    H = ind.stature_m
    hem_r = 0.175 * H
    collar_y = 0.735 * H
    collar_r = 0.128 * H

    robe = [_ring(0.0, 0.0, 0.0, hem_r, hem_r * 0.90, seg),
            _ring(0.0, 0.30 * H, 0.0, hem_r * 0.94, hem_r * 0.86, seg),
            _ring(0.0, 0.55 * H, 0.0, hem_r * 0.84, hem_r * 0.78, seg),
            _ring(0.0, collar_y, 0.0, collar_r, collar_r * 0.88, seg)]
    robe = _stride(robe, ring_stride)
    m.add(*_loft(robe), "npc_suit_robe", "vorlon_robe")

    # The collar/yoke: a short flared ring the shells and hood sit on.
    yoke = [_ring(0.0, collar_y, 0.0, collar_r, collar_r * 0.88, seg),
            _ring(0.0, collar_y + 0.055 * H, 0.0, collar_r * 1.22,
                  collar_r * 1.02, seg),
            _ring(0.0, collar_y + 0.090 * H, 0.0, collar_r * 1.02,
                  collar_r * 0.86, seg)]
    m.add(*_loft(yoke), "npc_suit_shell", "vorlon_yoke")

    head_w = collar_r * 1.13 * 2.0          # MEASURED 1.13x the collar width
    head_h = head_w / 1.36                  # MEASURED W/H = 1.36
    base_y = collar_y + 0.070 * H

    if "vorlon_shells" in _feature_filter(features):
        # SWEPT ARCS, not tapered cones. The first version lofted each shell as
        # a straight tapering stack and the render returned three cones stuck in
        # a collar, which is not what `vorlon.webp` shows: the lateral shells
        # "sweep forward and inward like curved mandibles" and their tops close
        # toward the midline over the face. So the ring CENTRES follow an arc --
        # rising while travelling inward in x and forward in z -- and the ring
        # section flattens as it rises, because a shell is a blade and a cone is
        # a hat.
        for side in (-1, 1):
            shell = []
            for k in range(5):
                t = k / 4.0
                ang = math.radians(6.0 + 66.0 * t)
                shell.append(_ring(
                    side * head_w * 0.50 * math.cos(ang) * 1.02,
                    base_y + head_h * (0.02 + 0.94 * math.sin(ang)),
                    head_h * (0.02 + 0.52 * t),
                    head_w * (0.215 - 0.115 * t),
                    head_h * (0.40 - 0.20 * t), seg))
            m.add(*_loft(shell), "npc_suit_shell", "vorlon_shells")
    if "vorlon_hood" in _feature_filter(features):
        # The central hood: a blade, wide across and thin front-to-back, rising
        # BETWEEN the shells and leaning back. It is the tallest part of the
        # assembly and the reason the silhouette reads as a chevron.
        hood = []
        for k in range(4):
            t = k / 3.0
            hood.append(_ring(0.0, base_y + head_h * (0.10 + 1.02 * t),
                              head_h * (0.10 - 0.30 * t),
                              head_w * (0.20 - 0.055 * t),
                              head_h * (0.20 - 0.10 * t), max(6, seg // 2)))
        m.add(*_loft(hood), "npc_suit_shell", "vorlon_hood")
    if "vorlon_tubes" in _feature_filter(features):
        # The green segmented chitinous tubes, one on each shoulder --
        # `More Vorlon.jpg` proves they are a symmetric pair by staying teal
        # under magenta light while the shell goes purple.
        for side in (-1, 1):
            tube = []
            for k in range(3):
                t = k / 2.0
                tube.append(_ring(side * head_w * 0.42,
                                  base_y + head_h * (0.34 + 0.34 * t),
                                  head_h * (0.10 + 0.16 * t),
                                  head_h * (0.10 - 0.03 * t),
                                  head_h * (0.10 - 0.03 * t), 6))
            m.add(*_loft(tube), "npc_suit_tube", "vorlon_tubes")
    # The head assembly rises above the nominal column, so the silhouette is
    # normalised as a whole. This is the assertion that keeps Kosh under the
    # kit's door: the suit was 2.112 m against a 2.10 m door before it existed.
    return _normalise_stature(m, None, ind.stature_m)


_PLANS = {"humanoid": build_humanoid, "encounter_suit": build_encounter_suit,
          "column": build_column}


# ---------------------------------------------------------------------------
# LOD
# ---------------------------------------------------------------------------
# Radial options are powers of two so a coarser ring's vertices are a strict
# SUBSET of a finer ring's -- a switch removes vertices rather than moving them,
# which is the property lod.py, greeble.py and drum_ground.py also hold and the
# reason a switch reads as "less detail" rather than as "the model twitched".
# 64 is here because lod0's quality floor is otherwise 2.23 m and the player
# converses at about 1 m. It costs ~4,200 triangles on the two or three figures
# that are ever inside 2 m and it is the difference between a face and a
# faceted face at the one distance the player actually looks at one.
SILHOUETTE_STEPS = (64, 32, 16, 8, 4)
PROFILE_STEPS = (1, 2, 4)
FEATURE_STEPS = ("all", "no_detail", "identity_only")

# The figure's own dimensions, used for the two whole-figure criteria below.
# Both come from FIGURE and are therefore MEASURED, not chosen.
FIGURE_WIDTH_M = FIGURE["shoulder_w"] * HUMAN_STATURE_M       # 0.411 m
FIGURE_DEPTH_M = FIGURE["chest_d"] * HUMAN_STATURE_M          # 0.271 m

# Beyond this, a whole standing figure is under one shading sample across and
# cannot read as a person however many triangles it has. It is the distance at
# which individuals must stop being drawn individually and become crowd density.
SUBPIXEL_FIGURE_M = aliases_beyond_m(FIGURE_WIDTH_M)

# Impostor azimuth count. 8 gives +/-22.5 degrees of unrepresented rotation.
IMPOSTOR_VIEWS = 8


def _feature_filter(level):
    if level == "all":
        return set(FEATURE_TIER) | {"hands", "feet"}
    if level == "no_detail":
        return {k for k, t in FEATURE_TIER.items() if t != "detail"}
    if level == "identity_only":
        return {k for k, t in FEATURE_TIER.items() if t == "identity"}
    raise KeyError(f"unknown feature level {level!r}")


def build(species: str, npc_id: str, lod=0, chain=None):
    """The public entry point. Returns (verts, tris, spans).

    `spans` is [(group, lo, hi)] over the triangle list, the same shape
    `interior_kit.tagged_spans()` produces, so the preview renderer can tint a
    crest differently from skin without a second code path.
    """
    sp = SPECIES[species]
    ind = individual(species, npc_id)
    levels = chain or lod_chain()
    lv = levels[max(0, min(lod, len(levels) - 1))]
    if lv["kind"] == "impostor":
        return impostor(ind, sp)
    m = _PLANS[sp.plan](ind, sp, seg=lv["radial_segments"],
                        ring_stride=lv["ring_stride"], features=lv["features"])
    return m.as_tuple()


def impostor(ind: Individual, sp: SpeciesBody):
    """A view-aligned card. Two triangles, and the end of the mesh chain.

    Sized to the individual's own bounding box so a Grome's card is not a
    human's. Emitted facing +Z with an outward normal; the runtime billboards
    it, which is why closure is not asserted for this level -- a card is not a
    solid and pretending it is would be the assertion-that-cannot-fail pattern.
    """
    m = _PLANS[sp.plan](ind, sp, seg=8, ring_stride=1, features="identity_only")
    x0, y0, _z0, x1, y1, _z1 = m.bbox()
    hw = max(x1 - x0, 1e-3) / 2.0
    cx = (x0 + x1) / 2.0
    verts = [(cx - hw, y0, 0.0), (cx + hw, y0, 0.0),
             (cx + hw, y1, 0.0), (cx - hw, y1, 0.0)]
    tris = [(0, 1, 2), (0, 2, 3)]
    return verts, tris, [("npc_impostor", 0, 2)]


_RADIUS_CACHE = {}


def _max_section_radius(species="human", npc_id="lod-probe", seg=64):
    """Largest cross-section radius anywhere on the figure, MEASURED.

    The sagitta must be evaluated where the outline error is worst, and that is
    a property of the built rings, not of a constant. Taken over every species
    so the chain is honest for the widest one rather than for a human.
    """
    if (npc_id, seg) in _RADIUS_CACHE:
        return _RADIUS_CACHE[(npc_id, seg)]
    worst = 0.0
    for key, sp in SPECIES.items():
        ind = individual(key, npc_id)
        m = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1, features="all")
        for _name, verts, _tris in m.parts:
            # Radius about the part's own vertical axis, which is what a ring
            # actually is. Using the figure's centreline instead would report an
            # arm's OFFSET as its radius and inflate the sagitta ~5x.
            cx = sum(v[0] for v in verts) / len(verts)
            cz = sum(v[2] for v in verts) / len(verts)
            for x, _y, z in verts:
                worst = max(worst, math.hypot(x - cx, z - cz))
    _RADIUS_CACHE[(npc_id, seg)] = worst
    return worst


def silhouette_schedule():
    """Radial decimation. Error is the sagitta at the MEASURED worst radius."""
    r = _max_section_radius()
    out = []
    for n in SILHOUETTE_STEPS:
        sag = round(r * (1.0 - math.cos(math.pi / n)), 5)
        facet = round(2.0 * r * math.sin(math.pi / n), 4)
        out.append({
            "radial_segments": n,
            "error_m": sag,
            "error_baseline": "the true surface of revolution",
            "error_source": f"sagitta r(1-cos(pi/n)) at the measured worst "
                            f"section radius r={r:.4f} m",
            "honest_from_m": round(honest_from_m(sag), 2),
            "feature_m": facet,
            "feature_source": "facet width 2r sin(pi/n) at the same radius",
            "aliases_beyond_m": round(aliases_beyond_m(facet), 1),
        })
    return out


def profile_schedule(seg=16):
    """Ring decimation along the skeleton. Error is MEASURED, ring by ring.

    `_stride` keeps every stride-th ring and lofts a straight band between kept
    rings, so a dropped ring's error is exactly its distance from the segment
    joining its kept neighbours -- the same measurement `station/lod.py` makes
    for the hull's longitudinal stride, applied to a limb. Swept over EVERY
    species and every part, and quoted for the worst, because the elbow of the
    longest-armed species is where this is largest and a mean would hide it.
    """
    out = []
    for stride in PROFILE_STEPS:
        worst, where = 0.0, None
        for key, sp in SPECIES.items():
            ind = individual(key, "lod-probe")
            m = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1, features="all")
            for name, verts, _tris in m.parts:
                nrings = _rings_of(verts, seg, name)
                if nrings is None or len(nrings) < 3:
                    continue
                e = chord_error(nrings, stride)
                if e > worst:
                    worst, where = e, f"{key} {name}"
        worst = round(worst, 5)
        out.append({
            "ring_stride": stride,
            "error_m": worst,
            "error_baseline": "stride 1, the authored ring plan",
            "error_source": ("max distance from a dropped ring vertex to the "
                             "chord of its kept neighbours"
                             + (f", worst at {where}" if where else "")),
            "honest_from_m": round(honest_from_m(worst), 2),
            "feature_m": worst,
            "feature_source": "the same deviation, as a feature size",
            "aliases_beyond_m": round(aliases_beyond_m(worst), 1),
        })
    return out


def chord_error(rings, stride):
    """Worst deviation of a dropped ring from the surface `_stride` would loft.

    Public and separate so it can be tested against a surface whose answer is
    KNOWN: on a genuinely ruled stack -- rings whose centres and radii are
    linear in the index -- dropping intermediate rings introduces exactly zero
    error, and any measurement that reports otherwise is measuring something
    else. That test is what distinguishes this from the first version, which
    interpolated by ring index on a non-uniformly spaced stack and reported
    0.123 m of "error" on a torso that changes radius by 20 mm end to end.
    """
    kept = set(_stride_indices(len(rings), stride))
    worst = 0.0
    for i in range(len(rings)):
        if i in kept:
            continue
        lo = max(k for k in kept if k < i)
        hi = min(k for k in kept if k > i)
        for a, b, c in zip(rings[i], rings[lo], rings[hi]):
            worst = max(worst, _point_segment_m(a, b, c))
    return worst


def _point_segment_m(p, a, b):
    """Perpendicular distance from p to the segment ab.

    NOT the distance to the point at parameter t = index/stride. That was the
    first implementation and it was wrong by a factor of ~50: the ring plan is
    NOT uniformly spaced in y -- the Gaim torso has rings at 0.50, 0.545, 0.72,
    0.803 and 0.818 of stature -- so interpolating by ring INDEX compares a
    dropped ring against a point on the chord nowhere near its own height and
    reports 0.123 m of "error" for a torso whose radius changes by 20 mm over
    its whole length. `station/lod.py` can use index interpolation because its
    profile samples ARE uniform in z; this one cannot, and the perpendicular
    distance is parameterisation-free, which is why it is the right instrument
    for both.
    """
    ax, ay, az = a
    ux, uy, uz = b[0] - ax, b[1] - ay, b[2] - az
    L2 = ux * ux + uy * uy + uz * uz
    if L2 < 1e-18:
        return math.dist(p, a)
    t = ((p[0] - ax) * ux + (p[1] - ay) * uy + (p[2] - az) * uz) / L2
    t = max(0.0, min(1.0, t))
    return math.dist(p, (ax + ux * t, ay + uy * t, az + uz * t))


def _stride_indices(n, stride):
    if stride <= 1:
        return list(range(n))
    keep = list(range(0, n, stride))
    if keep[-1] != n - 1:
        keep.append(n - 1)
    return keep


def _rings_of(verts, seg, name):
    """Recover a part's ring stack from its vertex list, or None if not a loft.

    `_loft` writes rings back to back, so this is exact for every part in the
    module. It is a recovery rather than a record on purpose: if a future part
    stops being a loft, this returns None and that part is excluded from the
    schedule instead of contributing a meaningless number.
    """
    if seg <= 0 or len(verts) % seg:
        return None
    return [verts[i * seg:(i + 1) * seg] for i in range(len(verts) // seg)]


def feature_schedule(seg=16):
    """Attachment culling. Error is how far the SILHOUETTE moves, MEASURED.

    Measured as the growth of the figure's bounding box between the culled and
    the full build, per species, quoted for the worst. That is a bound on the
    outline movement rather than an estimate of it, and it is the same shape of
    measurement as `lod.py`'s greeble relief.

    The result is uncomfortable and is the reason to measure rather than assume:
    the identifying features -- the crest, the tendrils, the mantle -- are large
    enough that they are not cullable inside the distance a figure is drawn as a
    mesh at all. So this schedule has exactly one useful step, and the module
    says so instead of shipping five levels that buy nothing.
    """
    ref = {}
    for key, sp in SPECIES.items():
        ind = individual(key, "lod-probe")
        ref[key] = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                   features="all").bbox()
    out = []
    for level in FEATURE_STEPS:
        worst, where = 0.0, None
        for key, sp in SPECIES.items():
            ind = individual(key, "lod-probe")
            bb = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                 features=level).bbox()
            e = max(abs(a - b) for a, b in zip(ref[key], bb))
            if e > worst:
                worst, where = e, key
        worst = round(worst, 5)
        out.append({
            "features": level,
            "error_m": worst,
            "error_baseline": "the full attachment set",
            "error_source": ("largest bounding-box movement this cull causes, "
                             "over every species"
                             + (f", worst on {where}" if where else "")),
            "honest_from_m": round(honest_from_m(worst), 2),
            "feature_m": worst,
            "feature_source": "the same movement, as a feature size",
            "aliases_beyond_m": round(aliases_beyond_m(worst), 1),
        })
    return out


def impostor_distance():
    """Distance from which an 8-azimuth impostor is inside the deviation budget.

    DERIVED, not chosen. A card captured at azimuth 0 is used over +/-22.5
    degrees, so its error is the change in silhouette half-width over that arc.
    Modelling the torso section as an ellipse with the MEASURED semi-axes -- a =
    half the shoulder width, b = half the chest depth -- the silhouette
    half-width at azimuth theta is sqrt(a^2 cos^2 + b^2 sin^2), and the worst
    error over the arc is the difference at the arc's end.

    What this does NOT cover, stated because a number that looks complete and is
    not is worse than no number: an impostor also freezes the animation phase and
    the lighting response. AAA-STANDARD lists motion under "what this rubric
    cannot judge" -- there is no way to measure the cost of a frozen gait in this
    container, so the mesh levels are kept out to the distance the triangle
    budget affords rather than switching at the geometric minimum.
    """
    a, b = FIGURE_WIDTH_M / 2.0, FIGURE_DEPTH_M / 2.0
    th = math.pi / IMPOSTOR_VIEWS
    w = math.sqrt((a * math.cos(th)) ** 2 + (b * math.sin(th)) ** 2)
    err = abs(a - w)
    return {"views": IMPOSTOR_VIEWS, "arc_deg": round(math.degrees(th), 2),
            "error_m": round(err, 5), "honest_from_m": round(honest_from_m(err), 2),
            "error_source": "silhouette half-width change of the measured "
                            "shoulder/chest ellipse over half the azimuth step"}


def _coarsest(schedule, key, distance):
    chosen = schedule[0]
    for opt in schedule:
        if opt["honest_from_m"] <= distance:
            chosen = opt
    return chosen


_CHAIN_CACHE = {}


def lod_chain(seg_measure=16):
    """The chain, as the distinct combinations the three schedules produce.

    Boundaries are the union of every schedule's honest distance, not a table.
    Adding an option to any schedule changes the chain and there is no second
    place to update -- the mistake `station/lod.py` records having made with a
    single LEVELS table.
    """
    if seg_measure in _CHAIN_CACHE:
        return _CHAIN_CACHE[seg_measure]
    sil = silhouette_schedule()
    pro = profile_schedule(seg_measure)
    fea = feature_schedule(seg_measure)
    imp = impostor_distance()
    bounds = sorted({0.0} | {o["honest_from_m"]
                             for s in (sil, pro, fea) for o in s
                             if 0 < o["honest_from_m"] <= SUBPIXEL_FIGURE_M})
    levels, last = [], None
    for d in bounds:
        s = _coarsest(sil, "radial_segments", d)
        p = _coarsest(pro, "ring_stride", d)
        f = _coarsest(fea, "features", d)
        combo = (s["radial_segments"], p["ring_stride"], f["features"])
        if combo == last:
            continue
        last = combo
        levels.append({
            "name": f"lod{len(levels)}",
            "kind": "mesh",
            "radial_segments": s["radial_segments"],
            "ring_stride": p["ring_stride"],
            "features": f["features"],
            "switch_distance_m": round(d, 2),
            "honest_from_m": {"silhouette": s["honest_from_m"],
                              "profile": p["honest_from_m"],
                              "feature": f["honest_from_m"]},
            "switch_reason": ("coarsest honest option in each schedule: "
                              f"silhouette {s['honest_from_m']} m, "
                              f"profile {p['honest_from_m']} m, "
                              f"feature {f['honest_from_m']} m"),
        })
    levels.append({
        "name": f"lod{len(levels)}",
        "kind": "impostor",
        "radial_segments": 8, "ring_stride": 1, "features": "identity_only",
        "switch_distance_m": round(max(imp["honest_from_m"],
                                       levels[-1]["switch_distance_m"] * 2.0), 2),
        "honest_from_m": {"impostor": imp["honest_from_m"]},
        "switch_reason": ("an 8-view impostor is geometrically honest from "
                          f"{imp['honest_from_m']} m; it is not USED until the "
                          "mesh chain has run out, because a card freezes the "
                          "gait and motion cannot be judged in this container"),
    })
    for i, lv in enumerate(levels):
        lv["used_to_m"] = (round(levels[i + 1]["switch_distance_m"], 2)
                           if i + 1 < len(levels) else round(SUBPIXEL_FIGURE_M, 1))
    _CHAIN_CACHE[seg_measure] = levels
    return levels


_TRI_CACHE = {}


def level_triangles(chain=None, species=None):
    """Triangles per figure at each level, per species, from the BUILT mesh."""
    chain = chain or lod_chain()
    keys = tuple(species or list(SPECIES))
    ck = (tuple((lv["name"], lv["kind"], lv["radial_segments"], lv["ring_stride"],
                 lv["features"]) for lv in chain), keys)
    if ck in _TRI_CACHE:
        return _TRI_CACHE[ck]
    out = []
    for lv in chain:
        row = {"name": lv["name"], "kind": lv["kind"], "per_species": {}}
        for k in keys:
            _v, t, _s = build(k, "cost-probe", chain.index(lv), chain)
            row["per_species"][k] = len(t)
        vals = list(row["per_species"].values())
        row["min"], row["max"] = min(vals), max(vals)
        row["mean_mix"] = _mix_mean(row["per_species"])
        out.append(row)
    _TRI_CACHE[ck] = out
    return out


def _mix_mean(per_species):
    """Population-weighted mean, using the FACTIONS 2.4 mix.

    A plain mean over fifteen species would weight the 750 Grome the same as the
    155,000 humans and overstate the crowd by the cost of the expensive tail.
    """
    tot = sum(share for _c, share in FACTIONS_MIX.values())
    return sum(per_species[k] * share / tot
               for k, (_c, share) in FACTIONS_MIX.items() if k in per_species)


# ---------------------------------------------------------------------------
# Cost at crowd scale
# ---------------------------------------------------------------------------
# The frame budget and the interior share come from station/budget.py; they are
# re-derived from it at runtime when it is importable so the two cannot drift,
# and these are the fallbacks.
FRAME_TRIANGLES = 1_200_000
# NPCs get 12% of the frame. Defended rather than asserted: interior structure
# takes 5% (budget.INTERIOR_FRAME_SHARE) and the habitat drum takes 25%
# (budget.DRUM["frame_share"]), and those two are never both in view -- a
# corridor is not the drum. So the worst simultaneous structural load is 25%,
# leaving 75% for people, props, signage, effects and whatever is through the
# windows. 12% is under a sixth of that residue and it is what the brief's
# "crowdedness" costs: it buys ~330 mid-field figures, which is a full Zocalo.
NPC_FRAME_SHARE = 0.12

# Standing crowd density on a busy commercial floor, in people per square metre.
# EXTRAPOLATED, and the constraint is a count off an authority-1 frame:
# `reference/04-sector-red/more zocalo.png` resolves ~18-20 figures, and
# `station/zocalo.py` solves that exact frame's camera (REF_FOCAL_PX = 2517,
# REF_HORIZON_PX = 370.5, REF_EYE_M = 1.265), which puts the visible floor
# between 4.5 m and ~40 m of depth over a ~110-150 m2 trapezoid. 18/140 = 0.13.
# Rounded to 0.15 for "busy" because the frame's near corners are occluded by
# tables and the count is therefore a floor, not a total.
DENSITY_PER_M2 = {"dead": 0.02, "normal": 0.08, "busy": 0.15, "crush": 0.45}


def crowd_cost(figures, distance_m=None, chain=None, level=None):
    """Triangles for `figures` standing figures, and the budget verdict."""
    chain = chain or lod_chain()
    tri = level_triangles(chain)
    if level is None:
        level = 0
        for i, lv in enumerate(chain):
            if distance_m is not None and distance_m >= lv["switch_distance_m"]:
                level = i
    per = tri[level]["mean_mix"]
    total = per * figures
    budget = FRAME_TRIANGLES * NPC_FRAME_SHARE
    return {"figures": figures, "level": chain[level]["name"],
            "distance_m": distance_m, "tris_per_figure": round(per, 1),
            "triangles": int(round(total)), "budget": int(budget),
            "share_of_frame": total / FRAME_TRIANGLES,
            "within_budget": total <= budget,
            "max_figures_in_budget": int(budget // max(per, 1e-9))}


def zocalo_crowd(bays=3, density="busy", chain=None):
    """The brief's question: a Zocalo with N standing figures, at what cost.

    Floor area comes from `station/zocalo.py`'s own bay dimensions when it is
    importable (BAY_WIDTH_M x BAY_LENGTH_M, both DERIVED there from the INV-010
    3.6 m deck pitch) rather than from a number typed here, so a change to the
    Zocalo's plan moves this figure automatically.
    """
    w, l, src = 21.6, 10.8, "fallback (zocalo.py not importable)"
    try:
        sys.path.insert(0, _STATION)
        import zocalo                                    # noqa: PLC0415
        w, l = zocalo.BAY_WIDTH_M, zocalo.BAY_LENGTH_M
        src = "station/zocalo.py BAY_WIDTH_M x BAY_LENGTH_M"
    except Exception:                                     # noqa: BLE001
        pass
    area = w * l * bays
    n = int(area * DENSITY_PER_M2[density])
    chain = chain or lod_chain()
    tri = level_triangles(chain)

    # A room is not one distance, and a crowd is not spread along depth -- it is
    # spread over FLOOR, and the floor a camera sees in a depth band grows with
    # the band's distance. Splitting the count linearly in depth was the first
    # model here and it put 7% of the crowd inside 2.2 m of the lens, which is
    # both false and expensive: it made a busy Zocalo miss the NPC budget by
    # 0.8% on the strength of six imaginary people standing on the camera.
    #
    # The visible floor at distance d is min(room_width, 2 d tan(hfov/2)) wide,
    # so the area of the band [d0, d1] is the integral of that, and the figures
    # in it are that area times the density. Everything else is unchanged; only
    # the weighting is now the right shape. AAA-STANDARD scores a total divided
    # by a length as PERFORMANCE 2, and this is the same error in a room.
    t = math.tan(_hfov_rad())
    depth = l * bays
    sat = w / (2.0 * t)                       # where the view stops widening

    def visible_area(d0, d1):
        d0, d1 = max(0.0, min(d0, depth)), max(0.0, min(d1, depth))
        if d1 <= d0:
            return 0.0
        a = 0.0
        lo, hi = d0, min(d1, sat)             # widening part: integral of 2 t d
        if hi > lo:
            a += t * (hi * hi - lo * lo)
        lo, hi = max(d0, sat), d1             # saturated part: full room width
        if hi > lo:
            a += w * (hi - lo)
        return a

    seen = visible_area(0.0, depth)
    bands, total, shown = [], 0.0, 0.0
    for i, lv in enumerate(chain):
        ba = visible_area(lv["switch_distance_m"], lv["used_to_m"])
        if ba <= 0.0:
            continue
        k = ba * DENSITY_PER_M2[density]
        tt = k * tri[i]["mean_mix"]
        total += tt
        shown += k
        bands.append({"level": lv["name"],
                      "from_m": round(max(0.0, min(lv["switch_distance_m"], depth)), 1),
                      "to_m": round(max(0.0, min(lv["used_to_m"], depth)), 1),
                      "area_m2": round(ba, 1), "figures": round(k, 1),
                      "tris_per_figure": round(tri[i]["mean_mix"], 1),
                      "triangles": int(round(tt))})
    return {"bays": bays, "area_m2": round(area, 1), "area_source": src,
            "density": density, "density_per_m2": DENSITY_PER_M2[density],
            "figures": n, "visible_area_m2": round(seen, 1),
            "figures_in_view": round(shown, 1), "bands": bands,
            "triangles": int(round(total)),
            "budget": int(FRAME_TRIANGLES * NPC_FRAME_SHARE),
            "share_of_frame": total / FRAME_TRIANGLES,
            "within_budget": total <= FRAME_TRIANGLES * NPC_FRAME_SHARE}


def write_obj(path, verts, tris, spans=None, default="npc"):
    owner = [default] * len(tris)
    for name, lo, hi in (spans or []):
        for i in range(lo, min(hi, len(tris))):
            owner[i] = name
    with open(path, "w") as f:
        f.write("# station/npc/body.py -- parametric species bodies\n")
        for x, y, z in verts:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        order, seen = [], set()
        for g in owner:
            if g not in seen:
                seen.add(g)
                order.append(g)
        for g in order:
            f.write(f"g {g}\no {g}\n")
            for i, (a, b, c) in enumerate(tris):
                if owner[i] == g:
                    f.write(f"f {a + 1} {b + 1} {c + 1}\n")


def nominal(species: str) -> Individual:
    """The species' parameter block with NO per-individual jitter.

    For the lineup render and for any comparison of species against species: a
    lineup of random individuals is a lineup of draws, and the first one drawn
    here was a Narn 2.4 sigma short, which read as "the Narn parameters are
    wrong" when it meant "this Narn is short".
    """
    sp = SPECIES[species]
    return Individual(species, "nominal", sp.stature_m, sp.build, sp.shoulder_k,
                      sp.head_k, sp.cranium, 1.0, sp.stoop_deg,
                      "m", 0, 0, sp.features)


def lineup(species=None, lod=0, spacing=0.95, npc_id="lineup", nominal_bodies=False):
    """Every species side by side, for the preview renderer. Scale is the point.

    Emitted along +X in the order of the FACTIONS 2.4 mix so the frame reads
    left to right as most populous to least, with the Vorlon last because it is
    not part of the mix at all.
    """
    keys = species or (list(FACTIONS_MIX) + ["vorlon"])
    verts, tris, spans = [], [], []
    chain = lod_chain()
    for i, k in enumerate(keys):
        if nominal_bodies:
            sp = SPECIES[k]
            lv = chain[max(0, min(lod, len(chain) - 1))]
            v, t, s = _PLANS[sp.plan](nominal(k), sp, seg=lv["radial_segments"],
                                      ring_stride=lv["ring_stride"],
                                      features=lv["features"]).as_tuple()
        else:
            v, t, s = build(k, f"{npc_id}-{k}", lod, chain)
        b, lo = len(verts), len(tris)
        dx = (i - (len(keys) - 1) / 2.0) * spacing
        verts.extend((x + dx, y, z) for x, y, z in v)
        tris.extend((a + b, c + b, d + b) for a, c, d in t)
        for g, a, c in s:
            spans.append((g, a + lo, c + lo))
    return verts, tris, spans


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(out=print):
    out(f"screen model: {SCREEN_H}p, {FOV_DEG:.0f} deg vertical FOV")
    out(f"  deviation budget {PIXEL_BUDGET} px -> "
        f"{_px_scale(PIXEL_BUDGET):,.1f} m of distance per metre of error")
    out(f"  shading sample   {SHADING_SAMPLE_PX} px -> "
        f"{_px_scale(SHADING_SAMPLE_PX):,.1f} m per metre of feature")
    out(f"  a {FIGURE_WIDTH_M:.3f} m figure is one shading sample wide at "
        f"{SUBPIXEL_FIGURE_M:,.0f} m -- beyond that, crowd density, not people")

    r = _max_section_radius()
    out(f"\nworst measured section radius on any species: {r:.4f} m")
    for name, rows, key in (("SILHOUETTE", silhouette_schedule(), "radial_segments"),
                            ("PROFILE", profile_schedule(), "ring_stride"),
                            ("FEATURE", feature_schedule(), "features")):
        out(f"\n{name} schedule")
        out(f"  {'option':>14} {'error m':>10} {'honest from':>13} "
            f"{'aliases beyond':>15}")
        for row in rows:
            out(f"  {str(row[key]):>14} {row['error_m']:>10.5f} "
                f"{row['honest_from_m']:>12,.2f}m {row['aliases_beyond_m']:>14,.1f}m")
        out(f"    error: {rows[-1]['error_source']}")

    imp = impostor_distance()
    out(f"\nIMPOSTOR ({imp['views']} views, +/-{imp['arc_deg']} deg unrepresented)")
    out(f"  error {imp['error_m']:.5f} m -> honest from {imp['honest_from_m']:.2f} m")
    out(f"  {imp['error_source']}")

    chain = lod_chain()
    tri = level_triangles(chain)
    out(f"\nCHAIN ({len(chain)} levels)")
    out(f"  {'level':6} {'kind':10} {'segs':>5} {'stride':>7} {'features':>14} "
        f"{'from':>10} {'to':>10} {'tri min':>9} {'tri max':>9} {'mix mean':>9}")
    for lv, t in zip(chain, tri):
        out(f"  {lv['name']:6} {lv['kind']:10} {lv['radial_segments']:>5} "
            f"{lv['ring_stride']:>7} {lv['features']:>14} "
            f"{lv['switch_distance_m']:>9,.1f}m {lv['used_to_m']:>9,.1f}m "
            f"{t['min']:>9,} {t['max']:>9,} {t['mean_mix']:>9,.0f}")
    out(f"\n  lod0's own quality floor is {chain[0]['honest_from_m']['silhouette']:.2f} m: "
        f"inside it the {SILHOUETTE_STEPS[0]}-gon section is itself over the\n"
        f"  deviation budget and there is nothing finer to switch to. Recorded "
        f"rather than\n  assumed away -- a hero mesh for a named character is a "
        f"different asset and is not\n  in this chain.")

    out("\nPER-SPECIES COST AT lod0 / lod1 / last mesh level")
    out(f"  {'species':10} {'stature m':>10} {'plan':>15} "
        + " ".join(f"{lv['name']:>8}" for lv in chain))
    for k, sp in SPECIES.items():
        ind = individual(k, "cost-probe")
        out(f"  {k:10} {ind.stature_m:>10.3f} {sp.plan:>15} "
            + " ".join(f"{t['per_species'][k]:>8,}" for t in tri))

    z = zocalo_crowd()
    out(f"\nA ZOCALO AT THE BUSY DENSITY -- the brief's question")
    out(f"  {z['bays']} bays, {z['area_m2']:,.0f} m2 ({z['area_source']})")
    out(f"  {z['density_per_m2']} figures/m2 -> {z['figures']} standing figures "
        f"in the room, {z['figures_in_view']} on the "
        f"{z['visible_area_m2']:,.0f} m2 the camera sees")
    for b in z["bands"]:
        out(f"    {b['level']:6} {b['from_m']:>6.1f}-{b['to_m']:<6.1f}m "
            f"{b['area_m2']:>7,.1f} m2 {b['figures']:>6.1f} figures x "
            f"{b['tris_per_figure']:>7,.0f} tri = {b['triangles']:>8,}")
    out(f"  TOTAL {z['triangles']:,} triangles = {z['share_of_frame']*100:.2f}% "
        f"of a {FRAME_TRIANGLES:,} triangle frame "
        f"({'within' if z['within_budget'] else 'OVER'} the "
        f"{NPC_FRAME_SHARE*100:.0f}% NPC budget of {z['budget']:,})")
    for d in ("dead", "normal", "busy", "crush"):
        zz = zocalo_crowd(density=d)
        out(f"    {d:7} {zz['figures']:>4} figures {zz['triangles']:>9,} tri "
            f"{'OK' if zz['within_budget'] else 'OVER BUDGET'}")

    out("\nWHAT BOUNDS THE CROWD IS COUNT, NOT DISTANCE")
    for dist in (5.0, 20.0, 60.0, 200.0):
        c = crowd_cost(1, distance_m=dist)
        out(f"  at {dist:>5,.0f} m the chain gives {c['level']}, "
            f"{c['tris_per_figure']:>7,.0f} tri/figure -> the NPC budget affords "
            f"{c['max_figures_in_budget']:,} figures")
    out(f"  and past {SUBPIXEL_FIGURE_M:,.0f} m no count is affordable, because a "
        f"figure is sub-pixel:\n  it must become density, not geometry.")


# ---------------------------------------------------------------------------
# Self-test
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

    chain = lod_chain()

    # -- determinism -------------------------------------------------------
    a = individual("narn", "r-0001")
    b = individual("narn", "r-0001")
    check(a == b, "individual() is a pure function of (species, id)")
    check(individual("narn", "r-0002") != a,
          "two ids give two different residents")
    v1, t1, _ = build("centauri", "r-0009", 0, chain)
    v2, t2, _ = build("centauri", "r-0009", 0, chain)
    check(v1 == v2 and t1 == t2, "the same resident builds byte-for-byte twice")
    # The digest, not just the result: a change of hash construction would
    # regenerate the whole population silently, and PYTHONHASHSEED must not
    # touch it. Values are pinned so a refactor of _u fails here.
    check(abs(_u("narn:r-0001", "stature") - 0.996393490481693) < 1e-12,
          f"_u is pinned to its blake2b construction "
          f"(got {_u('narn:r-0001', 'stature')!r})")
    # By AST, not by substring. The substring version failed on its own source
    # -- the assertion text contains the very names it forbids -- which is the
    # comic version of a test that cannot pass; a test that cannot FAIL is the
    # one this repository has shipped three of.
    import ast                                          # noqa: PLC0415
    tree = ast.parse(open(os.path.abspath(__file__)).read())
    banned = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            banned += [a.name for a in node.names if a.name.split(".")[0] == "random"]
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("random"):
            banned.append(node.module)
        elif isinstance(node, ast.Attribute) and node.attr == "__hash__":
            banned.append("__hash__")
    check(not banned,
          f"no `random` import and no `__hash__` access anywhere in the module "
          f"({banned})")
    check(any(isinstance(n, ast.Attribute) and n.attr == "blake2b"
              for n in ast.walk(tree)),
          "and the thing it uses instead is blake2b")

    # Cross-module: the body must be drawn from the SAME stream as the name and
    # the schedule, or one NPC id gives three unrelated people.
    try:
        sys.path.insert(0, _HERE)
        import schedule as sched                        # noqa: PLC0415
        check(abs(sched._u("x", "y") - _u("x", "y")) < 1e-15,
              "body._u matches schedule._u byte for byte")
        missing = [k for k in sched.STATION_MIX if k not in SPECIES]
        check(not missing,
              f"every species schedule.py can emit has a body ({missing})")
    except ImportError as exc:                          # noqa: BLE001
        check(False, f"schedule.py not importable for the interface check: {exc}")

    # -- the mix -----------------------------------------------------------
    # INV-005: the previous mix summed to 0.94 and silently dropped 120 of every
    # 2,000 residents. Asserted in a test, never checked by eye.
    share = sum(s for _c, s in FACTIONS_MIX.values())
    count = sum(c for c, _s in FACTIONS_MIX.values())
    check(abs(share - 1.0) < 1e-12, f"FACTIONS mix shares sum to 1.0 (got {share})")
    check(count == STATION_POPULATION,
          f"FACTIONS mix counts sum to {STATION_POPULATION:,} (got {count:,})")
    check("vorlon" not in FACTIONS_MIX and VORLON_SINGLETON == 1,
          "the Vorlon is a hard-coded singleton, never a share")
    check(all(k in SPECIES for k in FACTIONS_MIX),
          "every species in the mix has a body parameter block")
    check(len(SPECIES) == 15,
          f"fifteen species are modelled (got {len(SPECIES)})")

    # -- geometry: closure, winding, manifoldness --------------------------
    # Per species AND per part. AAA-STANDARD ROBUSTNESS 3: "signed volume on
    # EVERY primitive, not on the two that broke".
    worst_lo = 1e18
    for key, sp in SPECIES.items():
        ind = individual(key, "geom-probe")
        m = _PLANS[sp.plan](ind, sp, seg=16, ring_stride=1, features="all")
        bnd, nm = edge_census(m.tris)
        check(bnd == 0, f"{key}: {bnd} boundary edges -- the figure is not closed")
        check(nm == 0, f"{key}: {nm} non-manifold edges")
        for name, verts, tris in m.parts:
            vol = signed_volume(verts, tris)
            check(vol > 0.0, f"{key}/{name} is inside-out (signed volume {vol:+.6f})")
            worst_lo = min(worst_lo, vol)
            pb, pn = edge_census(tris)
            check(pb == 0 and pn == 0,
                  f"{key}/{name} is not a closed shell ({pb} boundary, {pn} "
                  f"non-manifold)")
    check(worst_lo > 0.0, "every part of every species winds outward")

    # The ring stack must be monotonic in y or the loft folds and the solid
    # self-intersects -- which renders perfectly and breaks every containment
    # and volume test downstream.
    for key, sp in SPECIES.items():
        ys = [f for _n, f, _w, _d in _torso_profile(nominal(key), sp)]
        check(all(a < b for a, b in zip(ys, ys[1:])),
              f"{key}: torso ring heights strictly increase "
              f"({[round(y, 3) for y in ys]})")

    # `contains()` must be able to say NO, or every containment assertion below
    # is vacuous -- the exact shape of the three assertions AAA-STANDARD scores
    # ROBUSTNESS 0. Checked on the same solid the assertions use, at a point
    # inside it, a point a metre to the side, and a point a metre above.
    _hv, _ht = next((v, t) for n, v, t in
                    build_humanoid(nominal("human"), SPECIES["human"], seg=16).parts
                    if n == "torso")
    _cy = sum(v[1] for v in _hv) / len(_hv)
    check(contains(_hv, _ht, (0.0, _cy, 0.0)),
          "contains() finds the centre of the torso to be inside it")
    check(not contains(_hv, _ht, (1.0, _cy, 0.0))
          and not contains(_hv, _ht, (0.0, _cy + 1.0, 0.0))
          and not contains(_hv, _ht, (0.0, _cy, 1.0)),
          "contains() rejects points a metre outside in each axis")

    # LIMB ROOTS ARE INSIDE THE TORSO. Two separate defects motivate this and
    # both were found by reading a render rather than by measuring: a magenta
    # band across the pelvis of every species whose `leg_k` is below 1, and a
    # lit disc floating at each shoulder where the arm's root cap sat level with
    # the torso's side. Measured with `contains()`, so a camera is not involved.
    for key, sp in SPECIES.items():
        if sp.plan != "humanoid":
            continue
        m0 = build_humanoid(nominal(key), sp, seg=16)
        tv, tt = next((v, t) for n, v, t in m0.parts if n == "torso")
        for part in ("leg", "arm"):
            roots = [_rings_of(v, 8, part) for n, v, _t in m0.parts if n == part]
            outside = 0
            for r in roots:
                if r is None:
                    continue
                top = max(r, key=lambda ring: sum(p[1] for p in ring))
                outside += sum(0 if contains(tv, tt, p) else 1 for p in top)
            check(outside == 0,
                  f"{key}: {outside} {part}-root vertices are outside the torso "
                  f"-- that is the hip gap / floating shoulder, measured")

    # The culling test, done as arithmetic rather than by looking at a render.
    # A closed solid shows about half its triangles from any camera; an
    # inside-out one shows the complement and still renders a figure.
    ind = individual("human", "cull-probe")
    m = build_humanoid(ind, SPECIES["human"], seg=16)
    for eye in ((0.0, 1.6, 4.0), (3.0, 1.0, -2.0), (0.0, 6.0, 0.2)):
        f = facing_fraction(m.verts, m.tris, eye)
        check(0.35 <= f <= 0.65,
              f"about half the triangles survive backface culling from {eye} "
              f"(got {f:.3f})")
        flipped = [(a, c, b) for a, b, c in m.tris]
        g = facing_fraction(m.verts, flipped, eye)
        check(abs((f + g) - 1.0) < 1e-9,
              f"flipping the winding gives exactly the complementary set "
              f"({f:.4f} + {g:.4f})")
    check(signed_volume(m.parts[0][1],
                        [(a, c, b) for a, b, c in m.parts[0][2]]) < 0,
          "MUTATION: a deliberately flipped part reports a NEGATIVE signed "
          "volume -- the winding assertion above can fail")

    # And the same formula the rest of the station is gated on.
    try:
        sys.path.insert(0, _STATION)
        import components as comp                        # noqa: PLC0415
        cv, ct = [], []
        comp._box(cv, ct, [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                           (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)])
        check(abs(signed_volume(cv, ct) - comp.signed_volume(cv, ct)) < 1e-12
              and abs(signed_volume(cv, ct) - 1.0) < 1e-9,
              "body.signed_volume agrees with components.signed_volume on a "
              "unit cube")
    except Exception as exc:                             # noqa: BLE001
        check(False, f"components.py not importable for the cross-check: {exc}")

    # -- the species differ, and differ in the right direction -------------
    st = {k: individual(k, "shape-probe").stature_m for k in SPECIES}
    check(st["grome"] > st["human"] > st["llort"] > st["vree"],
          f"the stature ordering is the one the parameter table states: {st}")
    humanoids = {k: sp for k, sp in SPECIES.items() if sp.plan == "humanoid"}
    check(min(humanoids.values(), key=lambda x: x.neck_k).key == "pakmara",
          "the pak'ma'ra carries the shortest neck of any species -- MEASURED "
          "off more Pak'ma'ra.webp, not styled")
    # ...and the tendrils must hang CLEAR of the chest, not through it, which
    # is the defect that corrected the neck length. Measured as a point-in-solid
    # test against the torso's own rings rather than by looking at a render.
    pmm = build_humanoid(nominal("pakmara"), SPECIES["pakmara"], seg=16)
    tor = [v for n, vs, _t in pmm.parts if n == "torso" for v in vs]
    tips = [v for n, vs, _t in pmm.parts if n == "pakmara_tendrils" for v in vs]
    ymin, ymax = min(v[1] for v in tor), max(v[1] for v in tor)
    buried = 0
    for tv in tips:
        if not (ymin <= tv[1] <= ymax):
            continue
        near = [v for v in tor if abs(v[1] - tv[1]) < 0.05]
        if near and tv[2] < max(v[2] for v in near):
            buried += 1
    check(buried == 0,
          f"no tendril vertex is inside the chest ({buried} of {len(tips)} were "
          f"before the neck length was corrected)")
    # Stoop must SHORTEN the standing figure without shortening the skeleton.
    pk = individual("pakmara", "stoop-probe")
    mp = build_humanoid(pk, SPECIES["pakmara"], seg=16)
    erect = SPECIES["pakmara"]
    straight = build_humanoid(
        Individual(pk.species, pk.npc_id, pk.stature_m, pk.build, pk.shoulder_k,
                   pk.head_k, pk.cranium, pk.crest_k, 0.0, pk.sex,
                   pk.tone_index, pk.pattern_seed, pk.features), erect, seg=16)
    hs = next(vs for n, vs, _t in mp.parts if n == "head")
    hr = next(vs for n, vs, _t in straight.parts if n == "head")
    # Track the crown as a VERTEX, by index. The bounding box is the wrong
    # instrument here and measuring it taught the module something: pitching a
    # head forward about a pivot at the chest lowers the crown and RAISES the
    # occiput, so the bbox top barely moves (1.795 -> 1.784 m) while the crown
    # itself drops 0.032 m and travels 0.177 m forward. The forward travel is
    # the whole silhouette signature of a pak'ma'ra and the bbox cannot see it.
    ci = max(range(len(hr)), key=lambda k: hr[k][1])
    fwd = hs[ci][2] - hr[ci][2]
    down = hr[ci][1] - hs[ci][1]
    check(fwd > 0.10 and down > 0.02,
          f"the stoop carries the crown {fwd:.3f} m forward and {down:.3f} m "
          f"down -- head over the toes, which is what the reference shows")
    # No bone shortened: ring-centroid separation is rotation-invariant where a
    # bounding box is not, so this is the measurement that actually tests the
    # claim.
    def _span(vs):
        rings = _rings_of(vs, 16, "head")
        a = [sum(c[i] for c in rings[0]) / len(rings[0]) for i in range(3)]
        b = [sum(c[i] for c in rings[-1]) / len(rings[-1]) for i in range(3)]
        return math.dist(a, b)
    check(abs(_span(hs) - _span(hr)) < 1e-9,
          f"the head is rotated, not scaled: chin-to-crown is {_span(hs):.6f} m "
          f"both ways")
    check(abs(straight.bbox()[4] - pk.stature_m) < 1e-9,
          f"stature_m IS the erect standing height, by construction "
          f"({straight.bbox()[4]:.6f} against {pk.stature_m:.6f})")
    # A Centauri female has no crest and a male does; the crest is dropped from
    # the feature list rather than scaled to zero, so it must not be in the mesh.
    males = [i for i in range(400)
             if individual("centauri", f"c{i}").sex == "m"]
    females = [i for i in range(400)
               if individual("centauri", f"c{i}").sex == "f"]
    check(150 < len(males) < 250 and len(males) + len(females) == 400,
          f"sex splits about evenly ({len(males)} m / {len(females)} f of 400)")
    mm = build("centauri", f"c{males[0]}", 0, chain)
    ff = build("centauri", f"c{females[0]}", 0, chain)
    check(any(g == "npc_hair" for g, _l, _h in mm[2]),
          "a Centauri male carries the crest")
    check(not any(g == "npc_hair" for g, _l, _h in ff[2]),
          "a Centauri female carries no crest mesh at all, not a zero-size one")
    # Four tendrils, not two lobes. FACTIONS 9.2 flags the two-lobe reading as
    # a known error, so the count is asserted rather than trusted to the code.
    pm = build("pakmara", "tendril-probe", 0, chain)
    check(sum(1 for g, _l, _h in pm[2] if g == "npc_skin_tendril") == 4,
          "the pak'ma'ra has FOUR tendrils (authority 3), not a two-lobed trunk")

    # -- clearance against the interior kit --------------------------------
    # AAA-STANDARD ROBUSTNESS 5: "cross-subsystem clearance is asserted wherever
    # two systems occupy the same space". The tram passing 6.43 m through a spoke
    # is what its absence looks like. Every species must fit the station's door.
    try:
        sys.path.insert(0, _STATION)
        import interior_kit as ik                        # noqa: PLC0415
        door_h = ik.PROVISIONAL["door_height_m"]
        for key, sp in SPECIES.items():
            tall = max(
                _PLANS[sp.plan](individual(key, f"door-{i}"), sp, seg=8).bbox()[4]
                for i in range(60))
            check(tall < door_h,
                  f"{key} stands {tall:.3f} m and must clear the kit's "
                  f"{door_h:.2f} m door (worst of 60 individuals)")
        check(door_h > 1.9, f"the door height being tested is real ({door_h})")
    except Exception as exc:                             # noqa: BLE001
        check(False, f"interior_kit not importable for the clearance check: {exc}")

    # -- LOD: the criterion, the monotonicity, the subset property ---------
    try:
        sys.path.insert(0, _STATION)
        import lod as hull_lod                           # noqa: PLC0415
        check(hull_lod.PIXEL_BUDGET == PIXEL_BUDGET
              and hull_lod.SCREEN_H == SCREEN_H
              and hull_lod.FOV_DEG == FOV_DEG
              and hull_lod.SHADING_SAMPLE_PX == SHADING_SAMPLE_PX,
              "the screen model matches station/lod.py -- two chains with two "
              "budgets pop differently in one frame")
        check(abs(hull_lod.honest_from_m(0.37) - honest_from_m(0.37)) < 1e-9,
              "honest_from_m agrees with station/lod.py's")
    except Exception as exc:                             # noqa: BLE001
        check(False, f"station/lod.py not importable for the mirror check: {exc}")

    sil = silhouette_schedule()
    pro = profile_schedule()
    fea = feature_schedule()
    for name, rows in (("silhouette", sil), ("profile", pro), ("feature", fea)):
        d = [r["honest_from_m"] for r in rows]
        check(all(x <= y for x, y in zip(d, d[1:])),
              f"{name} honest-from distances are monotonic: {d}")
        e = [r["error_m"] for r in rows]
        check(all(x <= y for x, y in zip(e, e[1:])),
              f"{name} error grows as the option coarsens: {e}")
        check(all(abs(r["honest_from_m"] - round(honest_from_m(r["error_m"]), 2))
                  < 1e-6 for r in rows),
              f"{name}: every published distance is the derived one, not typed")
    check(pro[0]["error_m"] == 0.0 and pro[0]["honest_from_m"] == 0.0,
          "ring stride 1 is the source data and introduces no error")
    # The chord measurement, against a surface whose answer is known. A ruled
    # stack loses NOTHING when its intermediate rings are dropped, so anything
    # but zero here means the measurement is measuring the wrong quantity --
    # which is exactly what the first version did.
    ruled = [_ring(0.0, 0.4 * k, 0.0, 0.30 - 0.05 * k, 0.30 - 0.05 * k, 12)
             for k in range(5)]
    check(chord_error(ruled, 2) < 1e-12,
          f"a ruled stack has zero chord error at stride 2 "
          f"(got {chord_error(ruled, 2):.3e} m)")
    # Non-uniform SPACING alone must still give zero: the ring plan is not
    # evenly spaced in y and an index-interpolating measurement fails here while
    # passing the test above.
    uneven = [_ring(0.0, y, 0.0, 0.30 - 0.25 * y, 0.30 - 0.25 * y, 12)
              for y in (0.0, 0.08, 0.5, 0.92, 1.0)]
    check(chord_error(uneven, 2) < 1e-12,
          f"a ruled stack with UNEVEN ring spacing also has zero chord error "
          f"(got {chord_error(uneven, 2):.3e} m) -- the index-interpolating "
          f"version of this measurement reports the ring spacing instead")
    # k == 1, which stride 2 DROPS. Putting it on k == 2 measures half the
    # bulge, because a kept ring moves the chord instead of deviating from it.
    bulged = [_ring(0.0, 0.4 * k, 0.0, 0.30 + (0.10 if k == 1 else 0.0),
                    0.30 + (0.10 if k == 1 else 0.0), 12) for k in range(5)]
    check(abs(chord_error(bulged, 2) - 0.10) < 1e-9,
          f"and a 0.10 m bulge on the dropped ring measures 0.10 m "
          f"(got {chord_error(bulged, 2):.6f})")
    check(fea[0]["error_m"] == 0.0,
          "the full feature set is its own baseline")

    # The measurement must be doing work: the sagitta at 4 segments has to be
    # hundreds of times the sagitta at 32, or the schedule is a constant with
    # decoration. And it must be computed at a radius that is really on the body.
    # The published errors must BE the sagitta, not merely increase with n.
    # Checked against the closed form rather than against each other, which is
    # the difference between a measurement and an algebraic identity.
    want = ((1 - math.cos(math.pi / SILHOUETTE_STEPS[-1]))
            / (1 - math.cos(math.pi / SILHOUETTE_STEPS[0])))
    got = sil[-1]["error_m"] / sil[0]["error_m"]
    check(abs(got - want) / want < 0.01,
          f"the errors are the sagitta r(1-cos(pi/n)): the {SILHOUETTE_STEPS[0]}"
          f"-to-{SILHOUETTE_STEPS[-1]} ratio is {got:.2f} against the closed "
          f"form's {want:.2f}")
    r = _max_section_radius()
    check(0.05 < r < 0.60,
          f"the worst section radius is a body radius, not a whole-figure one "
          f"({r:.4f} m -- it is the Gaim mantle / Vorlon robe hem, the two "
          f"widest single sections on any species)")
    hum = 0.0
    hm = build_humanoid(individual("human", "lod-probe"), SPECIES["human"], seg=64)
    for _n, vs, _t in hm.parts:
        cx = sum(v[0] for v in vs) / len(vs)
        cz = sum(v[2] for v in vs) / len(vs)
        hum = max(hum, max(math.hypot(v[0] - cx, v[2] - cz) for v in vs))
    check(0.12 < hum < 0.30,
          f"a human's worst section is a torso half-width ({hum:.4f} m against "
          f"the measured {FIGURE['shoulder_w'] * HUMAN_STATURE_M / 2:.4f} m)")

    # Strict subset: a coarser radial level's vertices must be a subset of the
    # finer one's, or a switch rearranges the figure instead of simplifying it.
    for key in ("human", "gaim", "vorlon"):
        sp = SPECIES[key]
        ind = individual(key, "subset-probe")
        fine = _PLANS[sp.plan](ind, sp, seg=32, ring_stride=1, features="all")
        coarse = _PLANS[sp.plan](ind, sp, seg=8, ring_stride=1, features="all")
        fv = {tuple(round(c, 9) for c in v) for v in fine.verts}
        cv = {tuple(round(c, 9) for c in v) for v in coarse.verts}
        # Attachments built at seg//2 and features with hard-coded small segment
        # counts are exempted by construction: only rings whose count divides
        # both levels can be a subset. Measured over the parts that do.
        shared = {v for v in cv if v in fv}
        check(len(shared) / max(1, len(cv)) > 0.5,
              f"{key}: most of the 8-segment vertices exist in the 32-segment "
              f"build ({len(shared)}/{len(cv)}) -- a switch removes vertices")

    # The chain itself.
    d = [lv["switch_distance_m"] for lv in chain]
    check(all(x < y for x, y in zip(d, d[1:])),
          f"chain switch distances strictly increase: {d}")
    check(chain[0]["switch_distance_m"] == 0.0, "the chain starts at zero")
    check(chain[-1]["kind"] == "impostor", "the chain ends in an impostor")
    tri = level_triangles(chain)
    means = [t["mean_mix"] for t in tri]
    check(all(x > y for x, y in zip(means, means[1:])),
          f"cost falls strictly along the chain: {[round(x) for x in means]}")
    check(means[-1] <= 2, f"the impostor is 2 triangles (got {means[-1]})")
    check(means[0] / means[-2] > 3.0,
          f"the mesh chain spans more than 3x in cost "
          f"({means[0]:.0f} -> {means[-2]:.0f})")

    # -- cost, and the claim that the design scales the way it says --------
    z = zocalo_crowd()
    check(z["figures"] > 50, f"a busy Zocalo is a crowd ({z['figures']} figures)")
    check(z["within_budget"],
          f"a busy Zocalo fits the NPC budget ({z['triangles']:,} of "
          f"{z['budget']:,})")
    check(not zocalo_crowd(density="crush")["within_budget"]
          or zocalo_crowd(density="crush")["triangles"] > z["triangles"],
          "a crush costs more than a busy floor -- the model is not flat in "
          "density")
    lin = crowd_cost(100, distance_m=5.0)
    lin2 = crowd_cost(200, distance_m=5.0)
    check(abs(lin2["triangles"] - 2 * lin["triangles"]) <= 1,
          "crowd cost is linear in the number of figures, as claimed")
    check(crowd_cost(100, distance_m=60.0)["triangles"]
          < crowd_cost(100, distance_m=5.0)["triangles"],
          "the same crowd is cheaper further away -- the chain is doing work")
    check(SUBPIXEL_FIGURE_M > 500.0 and SUBPIXEL_FIGURE_M < 900.0,
          f"the sub-pixel figure distance is derived from the measured shoulder "
          f"width ({SUBPIXEL_FIGURE_M:,.0f} m)")

    # -- the assertions above must be able to fail -------------------------
    # Every one of these constructs the defect and confirms the checker rejects
    # it. AAA-STANDARD ROBUSTNESS 0 lists three assertions in this repository
    # that could not fail, including one that scored 768 of 768 triangles as
    # passing from an `else` branch. These run every time so they cannot rot.
    mv, mt = _loft([_ring(0, 0, 0, 1, 1, 8), _ring(0, 1, 0, 1, 1, 8)])
    check(signed_volume(mv, mt) > 0, "a clean cylinder passes the volume check")
    check(signed_volume(mv, [(a, c, b) for a, b, c in mt]) < 0,
          "MUTATION: reversing every triangle makes signed_volume negative")
    check(edge_census(mt) == (0, 0), "a clean cylinder is closed and manifold")
    check(edge_census(mt[:-1])[0] > 0,
          "MUTATION: deleting one triangle opens boundary edges "
          f"({edge_census(mt[:-1])[0]} of them)")
    check(edge_census(mt + [mt[0]])[1] > 0,
          "MUTATION: duplicating a triangle creates non-manifold edges")
    check(_max_section_radius() > 0.05,
          "the section-radius measurement returns a real number")
    # If _max_section_radius measured about the FIGURE's centreline instead of
    # each part's own axis it would report an arm's offset as its radius. Build
    # that error and confirm the number moves by more than the tolerance the
    # radius assertion above allows.
    # The measurement takes each part's radius about ITS OWN axis. Doing it
    # about the figure's centreline instead would report an arm's lateral
    # OFFSET as its radius, and the whole silhouette schedule would be derived
    # from a number five times too large. Built here on the part where the two
    # differ most -- an arm -- so the distinction is demonstrated rather than
    # asserted. Quoted for the human, whose arm offset is the measured
    # biacromial half-width.
    # Measured on the HAND, not the arm: the arm is authored on a slant from an
    # inboard root to an outboard wrist, so its own centroid-relative radius
    # already carries some of that offset and understates the contrast. A hand
    # is a short vertical stack at a constant offset, which is the clean case.
    arm = next((vs for n, vs, _t in hm.parts if n == "hand"), None)
    cx = sum(v[0] for v in arm) / len(arm)
    cz = sum(v[2] for v in arm) / len(arm)
    own = max(math.hypot(v[0] - cx, v[2] - cz) for v in arm)
    centre = max(math.hypot(v[0], v[2]) for v in arm)
    check(centre > 3.0 * own,
          f"MUTATION: measuring an arm about the figure centreline reads "
          f"{centre:.4f} m against its true {own:.4f} m section radius "
          f"({centre / own:.1f}x) -- the distinction the schedule rests on")
    # And the profile schedule must be measuring geometry, not returning zeros:
    # flatten every limb bulge and its error has to collapse.
    check(pro[1]["error_m"] > 0.002,
          f"the profile schedule finds real deviation at stride 2 "
          f"({pro[1]['error_m']:.5f} m)")

    print(f"{ok}/{ok + fail} passed")
    # 0 on success. This read `0 if fail else 1` -- inverted -- until the
    # deliberate-break pass ran twelve mutants and every one of them exited 0
    # while printing its failures. A self-test that prints FAIL and returns
    # success is the exact category AAA-STANDARD scores ROBUSTNESS 0, and it was
    # invisible from every green run.
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--obj", help="write an OBJ here")
    ap.add_argument("--species", default=None)
    ap.add_argument("--id", default="lineup")
    ap.add_argument("--lod", type=int, default=0)
    ap.add_argument("--lineup", action="store_true")
    ap.add_argument("--nominal", action="store_true",
                    help="lineup of unjittered species means")
    a = ap.parse_args()
    if not (a.report or a.obj):
        sys.exit(_selftest())
    if a.report:
        report()
    if a.obj:
        if a.lineup or not a.species:
            v, t, s = lineup(lod=a.lod, npc_id=a.id, nominal_bodies=a.nominal)
        elif a.nominal:
            sp = SPECIES[a.species]
            ch = lod_chain()[max(0, min(a.lod, len(lod_chain()) - 1))]
            v, t, s = _PLANS[sp.plan](nominal(a.species), sp,
                                      seg=ch["radial_segments"],
                                      ring_stride=ch["ring_stride"],
                                      features=ch["features"]).as_tuple()
        else:
            v, t, s = build(a.species, a.id, a.lod)
        write_obj(a.obj, v, t, s)
        print(f"wrote {a.obj}: {len(v):,} vertices, {len(t):,} triangles")


if __name__ == "__main__":
    main()
