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
  * FEATURE (crest, tendrils, face, hair, hands, feet). Error = how far the
    silhouette moves when the part is removed, MEASURED two ways and maxed --
    the growth of the figure's bounding box, AND `_cull_standoff`, which is how
    far the removed geometry lay outside what survives. This one produces an
    uncomfortable result and the result is the point: a Centauri crest is 0.11 m
    of silhouette, so it is not cullable until 118 m, which is beyond the
    distance a body is drawn as a mesh at all. The identifying features are
    therefore NOT an LOD knob. The face and the thumbs are.

    THE SECOND MEASUREMENT EXISTS BECAUSE THE FIRST WAS BLIND, and session 4e
    paid for finding out. A nose, an ear, a thumb and a haircut all lie strictly
    inside the figure's own extremes -- the crown, the soles, the fingertips --
    so a bounding box scores their removal at exactly zero and the schedule
    concluded they were free to cull at zero metres. Two consequences, both
    real: `lod_chain()` built a chain that never used the full feature level at
    any distance, so the face existed in the code and in no frame; and the
    entire shipped corridor crowd, which `populace.corridor_lod` bakes at a
    `no_detail` level, was BALD. Hair has moved to the `extremity` tier for that
    reason and the schedule now prices what the box could not see.

SESSION 4G: A FACE, A HAND, AND THE VIEW THE SILHOUETTE TEST COULD NOT SEE
---------------------------------------------------------------------------
Session 4f gave the head nine landmark rings, a nose, a pair of ears and a
haircut, and the owner looked at the next render and said the same thing again:
*"the npcs just being undetailed featureless blobs"*. Three things were still
true of every resident on the station and each is now closed:

  * **no eyes.** A head with a nose and no eyes is a mannequin at every
    distance a mannequin can be told from a person, and nothing else on a face
    reads below ~100 px of head height. `_f_eyes` builds two eyes and two
    brows, off the SKULL'S OWN section (`_face_point`) so a Narn's braincase
    and every cranium jitter carry them. They emit into `npc_hair` -- an
    eyebrow IS hair, and it is the library's one measured "darker than skin"
    material -- and they are emitted LAST, beside the hair, because
    `populace._by_material` merges RUNS and a dark part in the middle of the
    skin run costs two draw calls a person.
  * **no fingers.** `_hand` was one closed shell wrist to fingertip. A mitten
    and a hand have the same bounding box, the same front outline, and nothing
    else in common: what reads as a hand is the 4 mm of BACKGROUND between two
    fingers. The palm now stops at the metacarpal head and gives up exactly
    what the four fingers add, so the hand does not grow, and culling
    `fingers` brings the mitt back as the coarse level of the same object.
  * **species that were four humans in hats at the level the crowd SHIPS at.**
    `_detail_gate` rasterises a filled silhouette from the FRONT AND THE SIDE
    and scores every pair of human / Centauri / Minbari / Narn in the head
    band. It found the Minbari crest 60% shorter than its own source says
    ("wider than the skull" -- it was 1.18 half-widths), and it found the brow
    ridge culled at 22 m, which made every Narn in a corridor a bald human.
    Both fixed; the front-only view was itself the blind instrument, since a
    brow, a nose and an occiput all project fore-aft.

`_small_seg` is what paid for it: a part is built at the coarsest ring count
whose sagitta is no worse than the BODY's own at that level, so a 9 mm finger
is 6 segments and not 64. Four fingers at the body's count would be 1,024
triangles a hand.

And the gate found two defects older than this session, both the same shape:
`interior.boundary_edges` keys edges on POSITION and `edge_census` keys on
INDEX, so a coincident capped disc between two shells is invisible to one and
obvious to the other. Every humanoid's foot began on exactly the leg's last
ring (2 non-manifold edges) and Kosh's yoke on exactly the robe's (125). Both
now overlap like every other joint here. Session 3x's `portal_frame` lesson,
in a second module: coincident faces are geometry nobody can see.

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
import json
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
    # Which face the head carries: see FACE_PLANS. A row rather than a branch,
    # so the sixteenth species is still a row.
    face: str = "humanoid"
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
#
# HAIR MOVED OUT OF `detail` IN SESSION 4e, AND THE REASON IS A MEASUREMENT
# BEING THE WRONG INSTRUMENT RATHER THAN A PREFERENCE. `feature_schedule()`
# prices a cull as the growth of the figure's BOUNDING BOX, and a skull cap
# barely moves one -- 20 mm at the crown -- so the schedule said hair was free
# to drop at 4.41 m and the whole shipped crowd, which `populace.corridor_lod`
# bakes at a `no_detail` level, was **bald to a person**. That is exactly the
# defect CLAUDE.md records for layer 2: a criterion that a defective case
# passes. A bounding box cannot see that a cull changes the MATERIAL over a
# third of the head, or that it removes the only thing distinguishing one
# resident's head from another's. Hair is therefore priced with the hands and
# the feet, and the honest statement of the cost is in `report()`.
FEATURE_TIER = {
    # THE BROW RIDGE IS A NARN'S IDENTITY, NOT A DETAIL, and it was `detail`
    # until session 4g -- so it was gone past 22 m and the corridor's Narn were
    # bald humans with a slightly heavier braincase. It is the same mistake
    # hair was in `_head_profile`'s note: an attachment that lies inside the
    # figure's own bounding box, priced by a measurement that cannot see it.
    # `_f_brow` is what `G'Kar more.jpg` establishes about that face; dropping
    # it at the level the crowd is BAKED at is dropping the species.
    # 20 triangles at seg 8. `_detail_gate`'s silhouette measurement is what
    # moved it: human vs Narn read IoU 0.875 in the head band with the brow
    # culled, which is 87.5% the same picture.
    "brow":            "extremity",
    # The nose and the ears. 20-60 mm of relief, genuinely cullable, and the
    # tier says so.
    "face":            "detail",
    "thumbs":          "detail",
    # Eyes and brows, and fingers. Both are `detail` for the same reason the
    # nose is -- an eye aperture is 11 mm tall and the gap between two fingers
    # is 4 mm -- and both are here rather than absent because a head with no
    # eyes and a hand with no digits is what "featureless blob" MEANS at the
    # only distance a player ever talks to somebody. `feature_schedule` prices
    # them; nothing here asserts they are worth their triangles.
    "eyes":            "detail",
    "fingers":         "detail",
    "hair":            "extremity",
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
        ("brow", "hands", "feet"), _S_NARN, face="ridged",
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
        ("brow", "hands", "feet"), _S_GENERIC, face="ridged",
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
        face="none",
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
        ("hands", "feet"), _S_GENERIC, face="flat",
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
        ("hands", "feet"), _S_GENERIC, face="ridged",
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
    # APPENDED, with a default, and deliberately so: `animation.rig` and
    # `_selftest` both construct an Individual positionally to suppress the
    # stoop, and a field inserted anywhere but the end silently reassigns those
    # arguments. "" means no hair mesh at all, which is what every species
    # without "hair" in its feature list gets.
    hair_style: str = ""


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
    # Drawn even for a species with no hair feature, so the digest stream does
    # not shift when a species gains or loses one -- the same reason `crest` is
    # drawn for every individual and used by one species.
    hair = hair_style_for(seed, sex) if "hair" in features else ""
    return Individual(species, npc_id, stature, build, shoulder, head, cran,
                      max(0.4, crest), max(0.0, stoop), sex,
                      int(_u(seed, "tone") * len(sp.surface.tones)),
                      int(_u(seed, "pat") * (1 << 24)), features, hair)


# ---------------------------------------------------------------------------
# Primitives. Y is up, +Z is facing -- the same frame as interior_kit, whose
# decks lie in XZ with `ceiling_height_m` along Y.
# ---------------------------------------------------------------------------
def _window(theta_deg, th, half, sharp=1.0):
    """The raised-cosine weight of a bump centred on `th`, at azimuth
    `theta_deg`. Zero outside `half`, one at the centre, C1 at the edges.

    `sharp` is an exponent on the window and it is what separates a CREASE from
    a SWELL. The oral fissure is 4 mm deep over 20 degrees of azimuth and the
    supraorbital torus is 4 mm proud over 45; with one window shape the first
    is a dent in a balloon. Raising the cosine to a power narrows the support
    without narrowing `half` -- which matters because `half` also sets how many
    of a coarse ring's samples fall inside the feature at all, and a feature
    narrower than one sample is a feature that vanishes at lod2 rather than
    softening. So `half` stays wide enough to be SAMPLED and `sharp` decides
    how much of that support carries amplitude.
    """
    d = (theta_deg - th + 180.0) % 360.0 - 180.0
    if abs(d) >= half:
        return 0.0
    w = math.cos(math.pi * 0.5 * d / half) ** 2
    return w if sharp == 1.0 else w ** sharp


def _ring(cx, cy, cz, rx, rz, seg, squash_front=1.0, squash_back=1.0,
          power=2.0, lobes=(), zoff=()):
    """One closed loop of `seg` points in the XZ plane at height cy.

    `squash_front` scales +Z only, which is how a chest gets a flatter back than
    front without a second radius parameter; `squash_back` does the same for -Z.

    ANGLE CONVENTION, stated once because every lobe below depends on it: the
    parameter runs x = cos(t), z = sin(t), so **t = 0 is the figure's LEFT
    (+X), t = 90 deg is the FACE (+Z), t = 180 deg is the right, t = 270 deg is
    the back**. Everything a body needs to stop being a solid of revolution is
    a function of that angle, and that is the whole point of the arguments
    below:

    `power` is the exponent of a superellipse |x/a|^p + |z/b|^p = 1. p = 2 is
    the ellipse this function used to be and is still the default. A TORSO IS
    NOT AN ELLIPSE IN SECTION -- a chest is nearly flat across the front and
    turns hard at the flank -- and p ~ 2.6 is the difference between a barrel
    and a ribcage. It costs ZERO triangles, which is why it is the first tool
    reached for here: session 3r's lesson was that articulation is what layer 2
    was missing, and articulation that moves vertices instead of adding them
    survives every level of the LOD chain unchanged.

    `lobes` is a tuple of `(theta_deg, half_width_deg, amount[, sharp])` RADIAL
    bumps. A deltoid, a brow ridge, a chin, an occiput and a cheekbone are all
    "the radius is 12% larger over a 40 degree arc centred here", and a raised
    cosine window keeps the ring smooth and strictly convex-ish so the loft
    cannot fold. Amounts are additive so two lobes may overlap.

    `zoff` is the same tuple shape and it displaces **z alone**, by
    `amount * rz`, AFTER the squash. IT IS NOT A LOBE AT 90 DEGREES AND THE
    DIFFERENCE IS THE WHOLE OF WHY A FACE IS NOT A STACK OF DISCS. A radial
    lobe scales the distance from the ring's ONE CENTRE, so it moves x and z
    together everywhere except exactly on an axis: a 6 mm "eye socket" built as
    a negative lobe at 66 degrees pulls the temple in by 2.4 mm as well, and a
    nasal root built that way narrows the whole upper face. Every craniofacial
    landmark that is a matter of FORE-AFT relief and not of width -- the
    nasion, the orbit, the oral fissure, the lip vermilion, the submalar
    hollow -- is a `zoff`, and every one that really is a width -- the
    zygomatic arch, the gonial angle, the temporal fossa, the occiput -- is a
    lobe. Both cost nothing.

    BOTH ARE PURE FUNCTIONS OF t, WHICH IS WHAT KEEPS THE LOD CHAIN HONEST.
    `SILHOUETTE_STEPS` are powers of two so a coarse ring's vertices are a
    strict SUBSET of a fine one's; that property survives any per-angle
    shaping, and would not survive shaping that depended on `seg`.
    """
    return [_ring_point(cx, cy, cz, rx, rz, 360.0 * i / seg,
                        squash_front, squash_back, power, lobes, zoff)
            for i in range(seg)]


def _ring_point(cx, cy, cz, rx, rz, theta_deg, squash_front=1.0,
                squash_back=1.0, power=2.0, lobes=(), zoff=()):
    """ONE point of the ring `_ring` would build, at an arbitrary azimuth.

    Split out of `_ring` so that anything which needs to sit ON the surface --
    an eye in its orbit, a brow on its ridge -- reads the SAME function the
    surface is lofted from instead of a second copy of it. `_face_point` used
    to reconstruct the superellipse by hand and knew nothing about the lobes,
    so an orbit recess would have moved the skull and left the eye floating in
    front of it. Hard rule 4 at the scale of an eye socket: one authoritative
    model, evaluated twice.
    """
    e = 2.0 / max(power, 1e-6)
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    if abs(power - 2.0) > 1e-9:
        c = math.copysign(abs(c) ** e, c)
        s = math.copysign(abs(s) ** e, s)
    k = 1.0
    for lb in lobes:
        th, half, amt = lb[0], lb[1], lb[2]
        k += amt * _window(theta_deg, th, half, lb[3] if len(lb) > 3 else 1.0)
    x, z = rx * c * k, rz * s * k
    z *= squash_front if z > 0 else squash_back
    for zb in zoff:
        th, half, amt = zb[0], zb[1], zb[2]
        z += rz * amt * _window(theta_deg, th, half,
                                zb[3] if len(zb) > 3 else 1.0)
    return (cx + x, cy, cz + z)


def _mirror(theta_deg, half, amt, sharp=1.0):
    """A left/right symmetric pair of lobes. A body is bilateral; typing the
    two entries by hand is how one of them ends up 5 degrees out."""
    return ((theta_deg, half, amt, sharp), (180.0 - theta_deg, half, amt, sharp))


# ---------------------------------------------------------------------------
# Segment counts for the SMALL parts -- fingers, eyes, brows
# ---------------------------------------------------------------------------
# The reference radius a small part's sagitta is compared against: the human
# figure's own shoulder half-width, MEASURED, straight out of `FIGURE`.
#
# IT IS DELIBERATELY NOT `_max_section_radius()`, for two reasons and the
# second one is the interesting one. First, that function measures by BUILDING
# every species, so calling it from inside a builder recurses into itself.
# Second, it reads 0.4514 m -- the Vorlon's robe hem, an object no humanoid
# has -- against this 0.2056 m, so using it would let every attachment be
# built COARSER than the body it hangs on. Being the smaller of the two makes
# `_small_seg` conservative in the only direction that matters: a part can come
# out finer than the strict sagitta rule requires, never coarser.
# `_selftest` asserts that ordering rather than an agreement, and prints both.
REF_SECTION_R_M = FIGURE["shoulder_w"] * HUMAN_STATURE_M / 2.0     # 0.2056 m

# Not powers of two, and deliberately so. A small attachment is PRESENT OR
# GONE -- it is culled by `FEATURE_TIER`, never decimated -- so it takes no part
# in the strict-subset property `SILHOUETTE_STEPS` exists to guarantee, and is
# free to be sized by its own sagitta. `costume._ATT_SEGS` makes the identical
# argument for a collar and this is the same ladder.
_PART_SEGS = (4, 5, 6, 8, 10, 12, 16, 24, 32)


def _small_seg(radius_m, seg, floor=4, cap=8):
    """Ring count for an attachment of `radius_m`, matched to the BODY's error.

    THE RULE IS "AS HONEST AS THE THING IT IS ATTACHED TO", stated once so it
    needs no distance argument. The body's silhouette error at `seg` is the
    sagitta at the figure's worst section, `R(1 - cos(pi/seg))`; the coarsest
    `n` whose sagitta at `radius_m` is no worse than that is exactly as visible
    a defect as the body already carries, and anything finer is spent on an
    error the torso beside it does not honour.

    It runs the OPPOSITE way from intuition and that is the whole point: a 9 mm
    finger at the body's 64 segments would cost 4x what it needs, which is the
    mistake `costume._att_seg` records paying for a 90 mm collar. Four fingers
    at 64 segments are 1,024 triangles a hand; at 6 they are 128, and the
    sagitta is 1.2 mm.

    `cap` is a stated ceiling on quality rather than an oversight, in the same
    words `costume._att_seg` uses: past 8 segments a 9 mm cylinder is round to
    well under a tenth of a millimetre and the ring count is buying nothing any
    camera in this project can resolve.
    """
    ref = REF_SECTION_R_M * (1.0 - math.cos(math.pi / max(int(seg), 3)))
    for n in _PART_SEGS:
        if radius_m * (1.0 - math.cos(math.pi / n)) <= ref:
            return max(floor, min(n, cap, max(int(seg), floor)))
    return max(floor, min(cap, max(int(seg), floor)))


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
# The ring plan. IDENTICAL for every species, so a coarser level is a strict
# SUBSET of a finer one -- `_selftest` measures that as a set operation rather
# than trusting this comment. `stride` picks every other entry with 0 and -1
# pinned, which is why the count is odd.
TORSO_RINGS = ("hip", "pelvis", "waist", "lower_chest", "chest", "upper_chest",
               "shoulder", "trapezius")
LIMB_RINGS = 5           # root, upper mid, joint, lower mid, tip
# Nine, one per craniofacial landmark: under-chin, chin, jaw, cheek, eye, brow,
# forehead, parietal, crown. It was seven and three of those were pure
# interpolation. `_selftest` asserts this IS the length of `_head_profile`'s
# BASE tier, so the constant cannot go stale the way it did between sessions 4d
# and 4e.
HEAD_RINGS = 9

# ---------------------------------------------------------------------------
# RING TIERS -- session 4h, and it is the only thing that made a modelled skull
# affordable.
# ---------------------------------------------------------------------------
# A ring plan that is one list serves two irreconcilable jobs. `ROOM_LOD = 1` is
# the level a player stands in front of, where a mouth, an orbit and a deltoid
# roll-over have to exist; `populace.corridor_lod` resolves to lod4, where the
# whole body is 644 triangles and `_selftest` caps the level the crowd is baked
# at at 640. Session 4g's honest craft 3 was written about the FORM, and a form
# needs rings -- but every ring is 2 x seg triangles at EVERY level, so buying a
# lip at lod0 also buys it at lod4, where it cannot be paid for and cannot be
# seen (8 azimuth samples across a whole head).
#
# So a profile row carries a tier:
#
#   "base"  -- built at every feature level. Exactly the rings that existed
#              before this session, so lod3 and below do not move at all.
#   "form"  -- built only at `features == "all"`, i.e. lod0/1/2, out to 22.1 m.
#
# The base set is a subset of the full set BY CONSTRUCTION -- one list, filtered
# -- so dropping to it removes rings rather than rearranging them, which is the
# same contract `_stride` and `SILHOUETTE_STEPS` hold.
#
# AND THE DROP IS PRICED BY THE RIGHT INSTRUMENT, which is the part worth
# reading. `feature_schedule()` cannot see this cull at all: it compares PART
# NAMES, and a reshaped torso is the same part. The bounding box cannot see it
# either -- that is the exact blindness session 4e paid for with a bald crowd.
# What a dropped intermediate ring costs is the distance from its vertices to
# the chord joining the rings that remain, which is precisely `chord_error`, and
# `_detail_gate` asserts that error is honest at the distance lod3 begins.
# AND THERE ARE TWO FORM TIERS, NOT ONE, FOR THE REASON THIS MODULE ALREADY
# SPLIT ONE LOD SCHEDULE INTO THREE: two knobs stop being visible at two
# distances. A lip is 9 mm and a deltoid is 22 mm of outline, and pricing them
# together prices the lip at the deltoid's distance -- which is what the first
# version of this did, and `npc/crowd.py` caught it in one run: carrying the
# face rings out to 26.8 m made a body 25% dearer in the band that holds most
# of a Zocalo, and the crowd system answered by moving the impostor swap from
# 51.1 m to 33.4 m -- INSIDE the 36 m floor that module sets so that "fix the
# budget" can never mean "put cards on people the player is talking to".
#
#   "base"  every level. The rings that existed before session 4h.
#   "face"  the head's landmark rings -- lips, orbital rims, frontal eminences.
#   "body"  the torso's shoulder S-curve and costal arch, and the limbs' extra
#           muscle rings.
#
# Each is dropped at its own MEASURED distance -- `form_schedule()` -- and the
# base set is a subset of both by construction, so every drop removes rings
# rather than rearranging them.
RING_TIERS = ("base", "face", "body")
# The steps, coarsening left to right, exactly like SILHOUETTE_STEPS.
FORM_STEPS = ("face_and_body", "body", "none")
_FORM_KEEP = {"face_and_body": ("face", "body"), "body": ("body",),
              "none": ()}


def _tier_rows(rows, form):
    """Filter a profile by tier. `rows` are `(..., tier)`; the tier is last.

    `form` is a `FORM_STEPS` key, or a bool for the two callers that only want
    "everything" or "nothing" -- `_detail_gate`'s control and `_face_point`.
    """
    if form is True:
        keep = ("face", "body")
    elif form is False:
        keep = ()
    else:
        keep = _FORM_KEEP[form]
    return [r for r in rows if r[-1] == "base" or r[-1] in keep]


def form_flags(form):
    """(face, body) booleans for a `FORM_STEPS` key."""
    keep = _FORM_KEEP[form] if isinstance(form, str) else (
        ("face", "body") if form else ())
    return ("face" in keep, "body" in keep)


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


def _shoulder_half(ind: Individual) -> float:
    """Biacromial half-width as a fraction of stature, for one individual.

    ONE function, because two call sites need it and they must not disagree:
    `_torso_profile` sizes the shoulder ring with it and `build_humanoid` roots
    the arms with it. The sex factor was applied in the first and not the second
    for exactly as long as it took to write this note, and the symptom would
    have been a woman's arms hanging 5% outside her own shoulders.
    """
    return (FIGURE["shoulder_w"] * ind.shoulder_k * 0.5
            * (0.95 if ind.sex == "f" else 1.0))


def _torso_profile(ind: Individual, sp: SpeciesBody, form=True):
    """(name, height, half_width, half_depth, section, tier) per torso ring.

    `section` is the keyword block handed to `_ring` -- superellipse exponent,
    front/back squash and radial lobes -- and it is where a stack of rings stops
    being a stack of cylinders. NONE OF IT COSTS A TRIANGLE, which is the reason
    it is done this way round: a shape carried by vertex positions rather than
    by vertex counts is present at every level of the LOD chain, including the
    484-triangle level the corridor crowd is actually baked at, where there is
    no room to add anything.

    What each section is, and why:

      * hip / pelvis  -- squarer than an ellipse (p 2.4) with the buttock as a
        lobe at the back. A pelvis is a bucket, not a barrel.
      * waist         -- the narrowest ring, and the only one with no lobes.
      * lower_chest   -- the ribcage. p 2.5 and the deepest section after the
        hip, because ribs turn hard at the flank.
      * chest         -- pectoral lobes either side of the midline, and for
        women a breast lobe at the same place with more amplitude and a
        narrower arc. `ind.sex` HAS EXISTED SINCE THIS MODULE WAS WRITTEN AND
        DROVE NOTHING BUT THE CENTAURI CREST; half the station was built to
        one silhouette.
      * upper_chest / shoulder -- p 2.9, the squarest sections on the figure.
        A square section is what makes a shoulder read as a shelf rather than
        as the top of a bottle.
      * deltoid / supraspinous / trapezius -- the S-curve of the shoulder, and
        the long comment beside them is the argument. The note that used to
        stand here said "there is no deltoid lobe on purpose: the deltoid
        belongs to the ARM, whose own bulge already carries it". MEASURED, it
        did not: the arm's widest point is 0.99 of the biacromial half-width
        against the torso's 1.00, so the deltoid was inside the torso at every
        height and the widest point of the figure was the flat corner at the
        acromion. It is the torso's now, and the arm's bulge meets it below.

    SEXUAL DIMORPHISM IS A RATIO, NOT A SIZE. `shoulder_k` and stature are
    already jittered per individual, so what is applied here is only the part
    that is a SHAPE: shoulder-to-hip. The values (women +9% hip, -5% shoulder,
    -6% waist against the same stature) are EXTRAPOLATED, authority 5; what
    constrains them is that the reference set is 24 shoulder-framed portraits
    and establishes nothing about waists at all. What would overturn them is
    any full-figure frame of a woman in the S2-3 uniform.
    """
    b = ind.build
    f = ind.sex == "f"
    sw = _shoulder_half(ind)
    hip_y, lx, r_th, _r_an = _leg_params(ind, sp)
    # Wide enough to CONTAIN both leg roots, not merely to look about right.
    #
    # AND THE CONTAINMENT FLOOR IS WHAT BINDS, ON EVERY FIGURE THIS MODULE HAS
    # EVER BUILT. Measured while writing the dimorphism assertion below:
    # `FIGURE["hip_w"] * 0.5` is 0.0900 of stature and `(lx + r_th) * 1.12` is
    # 0.1092, so the second term wins for every species at every build, and
    # `FIGURE["hip_w"]` -- which is marked EXTRAPOLATED in the table -- has
    # never been the hip width of anything. The real pelvis is 0.38 m across at
    # human stature, set by where the legs are and how thick they are, which is
    # within a few centimetres of adult bi-iliac breadth and is why nothing ever
    # looked wrong. It is written down here because a parameter that drives
    # nothing is a parameter the next context will try to tune.
    #
    # The sex factor therefore multiplies the RESOLVED width rather than one of
    # the two candidates, or it would have been invisible for the same reason.
    # It only ever widens (women x1.09, men x1.00), so it can never take a
    # pelvis below the width its own leg roots need.
    hw0 = max(FIGURE["hip_w"] * 0.5 * b, (lx + r_th) * 1.12)
    hw = hw0 * (1.09 if f else 1.0)
    cd = FIGURE["chest_d"] * 0.5 * b
    waist_k = 0.80 if f else 0.88
    # Pectoral / breast: same place on the ring, different amplitude and arc.
    bust = _mirror(66.0, 22.0, 0.16) if f else _mirror(62.0, 30.0, 0.055)
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
    ac = FIGURE["acromion"]
    rows = [
        ("hip",          hip_y - 0.035,                   hw * 1.00, cd_hip,
         {"power": 2.1, "squash_back": 0.98,
          "lobes": ((270.0, 60.0, 0.10 if f else 0.05),)}, "base"),
        # Placed BETWEEN the hip and the waist rather than a fixed 0.030 above
        # the hip: with a fixed offset, a species with long legs (Minbari at
        # leg_k 1.03) pushes the pelvis ring ABOVE the waist ring, the stack
        # stops being monotonic in y, the loft folds back on itself and the
        # solid self-intersects. `contains()` then returns nonsense -- which is
        # how this was found, as two leg-root vertices "outside" a torso that
        # was 0.25 m wide at that height.
        ("pelvis",       hip_y + 0.55 * (FIGURE["waist"] - hip_y),
                                                          hw * 1.00, cd_hip,
         {"power": 2.1, "squash_back": 0.99,
          "lobes": ((270.0, 55.0, 0.06 if f else 0.03),)}, "base"),
        # The waist and the ribcage hang off `hw0`, the pelvis's width BEFORE
        # the sex factor, and that is not a detail. Deriving them from the
        # widened hip makes a woman's waist wider in the same proportion, so
        # the shoulder-to-waist-to-hip ratio -- the entire content of the
        # dimorphism -- comes out unchanged. The assertion in `_selftest`
        # caught exactly that and it is the reason these two read `hw0`.
        ("waist",        FIGURE["waist"],            hw0 * waist_k, cd * 0.80,
         {"power": 2.3}, "base"),
        # The costal arch: the ribcage flares out of the waist FASTER than it
        # then rises, so the lower ribs are a corner and not a ramp. A form
        # ring, because at 22 m it is 6 mm of outline.
        ("lower_ribs",   0.578,                          hw0 * 0.945, cd * 0.88,
         {"power": 2.4, "squash_front": 1.03,
          "lobes": _mirror(30.0, 34.0, 0.03)}, "body"),
        ("lower_chest",  0.615,                          hw0 * 0.98, cd * 0.94,
         {"power": 2.5, "squash_front": 1.04}, "base"),
        ("chest",        FIGURE["chest"],                 sw * 0.86, cd * 1.00,
         {"power": 2.6, "squash_back": 0.94, "lobes": bust}, "base"),
        ("upper_chest",  0.772,                           sw * 0.96, cd * 0.96,
         {"power": 2.8, "squash_back": 0.92,
          "lobes": _mirror(62.0, 26.0, 0.04)}, "base"),
        # ------------------------------------------------------------------
        # THE SHOULDER, AND IT IS THE OTHER HALF OF SESSION 4h's BRIEF.
        # ------------------------------------------------------------------
        # What the owner was looking at, stated as geometry: the torso's top
        # was `shoulder` at the acromion, `sw * 1.00` half-width, and then
        # `trapezius` 42 mm above it at `sw * 0.40`. That is 71 mm of
        # horizontal travel over 42 mm of rise, all the way round, so the top
        # of the shoulder was a PLATE and the front outline turned a hard
        # corner at the acromion. The arm did not help: rooted at 0.44 of the
        # biacromial half-width and never exceeding 0.99 of it, its deltoid
        # never reached the silhouette at all, so the widest point of the
        # figure was the flat corner rather than the muscle.
        #
        # A real shoulder is the opposite in both respects. Its widest point
        # is the DELTOID, about 25 mm BELOW the acromion; from there the
        # outline runs up and IN over the acromion, then down and in again
        # along the trapezius to the neck. That is an S, and three rings is
        # the fewest that can carry one.
        #
        #   deltoid       0.798   the widest ring on the whole figure
        #   shoulder      0.818   the acromion, now NARROWER than the deltoid
        #   supraspinous  0.831   the roll-over into the trapezius
        #   trapezius     0.842   the neck root, but reaching out at the sides
        #
        # `deltoid` and `supraspinous` are `form`, so lod3 and below keep the
        # two-ring stack they had -- but the two BASE rings' own numbers move,
        # which is free and which is why the crowd gets a shoulder too: the
        # acromion comes in to 0.94 and the trapezius goes out to 0.50 with a
        # 0.34 lobe at the sides, so even at 8 azimuth samples the top ring is
        # a RIDGE running out toward the joint instead of a small round post.
        #
        # The deltoid lobe is at 0 and 180 -- the pure sides, where the arm is
        # -- and `_selftest`'s `contains()` check is what stops it being turned
        # up further: every arm-root vertex has to stay inside this solid.
        #
        # AND THE WHOLE GROUP IS SCALED SO THE DELTOID SITS *AT* THE MEASURED
        # BIACROMIAL WIDTH RATHER THAN OUTSIDE IT, which is a fidelity point
        # and not a budget one. `FIGURE["shoulder_w"] = 0.235` was read off a
        # standing officer in `more hallway.jpg` -- across his shoulders, in a
        # uniform, deltoids and all. Building a deltoid 6.5% OUTSIDE that
        # number double-counts the muscle the number already contains. The
        # first version did exactly that and `populace.py`'s idle-sway control
        # is what said so: a dressed figure went 0.549 m across the shoulders
        # to 0.601 m, through a 0.58 m bound that exists because a body has to
        # come back inside its own shoulders. Scaled to land the widest ring at
        # 1.01 of biacromial, the S-curve is unchanged -- deltoid 1.01,
        # acromion 0.95, supraspinous 0.83, trapezius 0.64 -- and the figure is
        # the width the photograph says it is.
        ("deltoid",      0.798,                          sw * 0.940, cd * 0.90,
         {"power": 2.85, "squash_back": 0.93,
          "lobes": _mirror(0.0, 42.0, 0.075)}, "body"),
        ("shoulder",     ac,                             sw * 0.900, cd * 0.86,
         {"power": 2.9, "squash_back": 0.94,
          "lobes": _mirror(0.0, 46.0, 0.055)}, "base"),
        ("supraspinous", ac + 0.013,                     sw * 0.755, cd * 0.72,
         {"power": 2.5, "squash_back": 0.94,
          "lobes": _mirror(0.0, 50.0, 0.10)}, "body"),
        # The torso used to end on the acromion ring, and the render showed
        # exactly what that is: a flat elliptical disc across the top of the
        # shoulders, lit like a table. A body closes with the trapezius sloping
        # up to the neck, so the last ring is small and high and the shoulder
        # becomes an edge rather than a lid.
        # The lobes are the two trapezius ridges running from the neck out over
        # the clavicle. They were at 20/160 degrees -- 20 degrees off the side
        # -- and 0.10 deep, which put the ridge in the wrong place and made it
        # too shallow to see; the muscle runs to the ACROMION, so the lobe is
        # on the side itself and deep enough that the top ring is 0.67 of the
        # biacromial half-width there against 0.50 at the throat.
        ("trapezius",    ac + 0.024,                     sw * 0.480, cd * 0.52,
         {"power": 2.2, "lobes": _mirror(0.0, 52.0, 0.34)}, "base"),
    ]
    return _tier_rows(rows, form)


# How much the +Z half of every head ring is flattened. A face is a PLANE and
# the back of a skull is a dome; without this the head is a solid of revolution
# at every distance where its profile reads at all.
FACE_FLATTEN = 0.88


# WHERE A FACE'S FEATURES SIT ROUND THE RING, derived once rather than typed
# fifteen times. The angle convention is `_ring`'s: 90 degrees is the midline of
# the face and 0 is the figure's left side, so a landmark `d` degrees off the
# midline is a `_mirror` pair at `90 - d`.
#
# The three that matter are DERIVED from the width the landmark actually sits at
# rather than chosen, using the superellipse the head ring is built on: a point
# at a fraction `xf` of the half-width lies at azimuth acos(xf^(p/2)) from the
# +X axis, so with p ~ 2.1
#
#   eye     0.43 of half-width (INV-4G-001's interpupillary)   -> 24 deg off
#   zygion  0.72 of half-width (the arch is near the widest)   -> 43 deg off
#   gonion  0.86 of half-width (the jaw angle is nearly at it) -> 60 deg off
#
# so `_face_az(0.43)` and `EYE_X_F` cannot drift apart, and the cheekbone lobe
# is at the cheekbone rather than 8 degrees off it.
def _face_az(xf, power=2.1):
    """Azimuth, in degrees off the +X axis, of the point `xf` of the way out to
    a superellipse ring's half-width on the FACE side."""
    xf = max(0.0, min(1.0, abs(xf)))
    return math.degrees(math.acos(xf ** (power / 2.0)))


def _head_profile(ind: Individual, form=True):
    """(t, radius_scale, z offset in head heights, section, tier) chin to crown.

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

    NINE RINGS OF LANDMARK IS STILL A STACK OF DISCS, and session 4g scored
    itself craft 3 for it and was right. Nine rings over a 231 mm head is 26 mm
    of vertical resolution: a lip is 9 mm, an orbital rim is 6 mm and a
    mentolabial sulcus is 4 mm, so NONE OF THEM CAN EXIST, however many lobes
    the rings carry. And every landmark that had been built was built as a
    RADIAL lobe about the ring's one centre, which is a shape that can only make
    a head rounder or narrower -- there was no way to say "this part of the face
    is further back" at all.

    So the stack is now FIFTEEN rows and there are two kinds of displacement:

        t      landmark              tier   what carries it
      -0.07  submental               base   buried in the neck, tucked back
       0.06  mental protuberance     base   radial lobe at the midline
       0.115 mentolabial sulcus      form   zoff  -- the crease under the lip
       0.165 lower vermilion         form   zoff  -- the lower lip
       0.20  oral fissure / gonion   base   zoff at the midline + radial lobes
       0.255 upper vermilion         form   zoff, with a philtrum groove in it
       0.34  zygomatic arch          base   radial lobes, submalar zoff below
       0.405 infraorbital rim        form   zoff -- the lower orbital margin
       0.46  orbit / temporal fossa  base   zoff INTO the socket, radial out
       0.515 supraorbital rim        form   zoff -- the superciliary arches
       0.57  supraorbital torus      base   radial lobe + the nasion notch
       0.635 frontal eminence        form   zoff, paired
       0.70  frontal squama          base   slopes back
       0.86  parietal / occiput      base   the widest ring
       1.00  crown                   base   small, and set back

    THE SPLIT BETWEEN A LOBE AND A `zoff` IS THE ANATOMY, and `_ring`'s own
    docstring derives it: width is a lobe, relief is a zoff. The orbit is the
    case that proves it. As a negative lobe at 66 degrees a 8 mm socket also
    pulls 3 mm out of the temple, because a lobe scales the distance from the
    ring's single centre; as a `zoff` it is 8 mm straight back and the head is
    exactly as wide as it was. That is what lets the eye be RECESSED instead of
    a bead stuck on a ball, which is what the owner was looking at.

    The temple lobes being NEGATIVE is the same argument in the other currency:
    a head narrows above the cheekbone and widens again above the ear, and a
    profile that can only add is a profile that can only make heads rounder.

    `form` rows are dropped at `features != "all"`, i.e. past 22.1 m -- see
    RING_TIERS. The BASE nine are exactly the rows that existed before, so the
    corridor bake does not move, and every base row's own shaping got better for
    free: at lod4 a head is 8 azimuth samples and a `zoff` at the midline is
    still exactly one of them.

    Every number is EXTRAPOLATED (authority 5) except the widths, which inherit
    `jaw_k`'s measurement, and the azimuths, which are derived by `_face_az`
    from the width the landmark sits at. The constraint is standard adult
    craniofacial proportion -- eyes at half the head height, widest point at the
    parietal, chin ~0.6 of the parietal width, stomion ~0.19 of chin-to-crown,
    interpupillary 0.43 of the half-width -- and what would overturn any of it
    is one square-on portrait at a stated scale, which
    `reference/15-races-and-makeup/` has for G'Kar and for nobody else.
    Logged as INV-4H-001 in docs/npc-form-4g.md.
    """
    ff = FACE_FLATTEN
    # Azimuths, derived. `ey` is where the eye is, `zy` the zygomatic arch,
    # `go` the gonial angle, and the midline is 90.
    ey, zy, go = _face_az(EYE_X_F), _face_az(0.72), _face_az(0.86)
    rows = (
        # The submental triangle: BEHIND the chin and narrower than it, so the
        # underside of the jaw slopes back to the neck instead of hanging as a
        # cylinder. -0.008 rather than +0.020: the old value put this ring
        # almost level with the chin point and the jaw had no underside at all.
        (-0.07, 0.50, -0.008, {"power": 2.0, "squash_front": ff * 0.92},
         "base"),
        # The chin: narrow, forward, and with a point on it.
        (0.06, 0.63, +0.030, {"power": 2.2, "squash_front": ff * 1.06,
                              "squash_back": 0.92,
                              "lobes": ((90.0, 34.0, 0.10),)}, "base"),
        # The mentolabial sulcus -- the crease between the lower lip and the
        # chin. `sharp` 2.2 keeps it a crease: at half 26 degrees it is sampled
        # by three vertices at lod1 and still reads as a groove rather than as
        # a flattening of the whole lower face.
        (0.115, 0.735, +0.026, {"power": 2.25, "squash_front": ff * 1.03,
                                "zoff": ((90.0, 26.0, -0.075, 2.2),)}, "face"),
        # The lower lip. The vermilion stands proud of the sulcus below it and
        # of the fissure above it; that pair of sign changes over 9 mm is the
        # entire reason a mouth needs its own rings.
        (0.165, 0.790, +0.029, {"power": 2.2, "squash_front": ff * 1.05,
                                "zoff": ((90.0, 25.0, +0.070, 1.4),)}, "face"),
        # The oral fissure and the gonial angle, at one height and on a BASE
        # ring. Both survive to lod4, which is the point: at 22 m a mouth is a
        # shadow line and a jaw angle is the outline of the face, and they cost
        # nothing. The lips above and below it are `form`.
        (0.20, 0.845, +0.014, {"power": 2.3, "squash_front": ff * 1.01,
                               "lobes": _mirror(go, 30.0, 0.05),
                               "zoff": ((90.0, 23.0, -0.055, 2.0),)}, "base"),
        # The upper lip, with the philtrum cut into it: a wide positive window
        # and a narrow negative one at the same azimuth. Two windows on one
        # ring is what `zoff` being additive buys.
        (0.255, 0.880, +0.010, {"power": 2.25, "squash_front": ff * 1.04,
                                "zoff": ((90.0, 24.0, +0.060, 1.3),
                                         (90.0, 9.0, -0.035, 1.8),
                                         ) + _mirror(90.0 - 32.0, 16.0, -0.030)},
         "face"),
        # The cheekbone: a WIDTH, so a radial lobe, with the submalar hollow
        # behind it as a zoff. The arch is the widest thing on a face below the
        # parietal and the hollow under it is why a face is not a balloon.
        (0.34, 0.94, +0.002, {"power": 2.2, "squash_front": ff * 1.02,
                              "lobes": _mirror(zy, 24.0, 0.07),
                              "zoff": _mirror(90.0 - 40.0, 16.0, -0.035)}, "base"),
        # The infraorbital rim -- the lower margin of the socket. The lid sits
        # on it, so the surface comes forward here and goes back above.
        (0.405, 0.965, -0.003, {"power": 2.15, "squash_front": ff * 1.01,
                                "zoff": _mirror(ey, 17.0, +0.030)}, "face"),
        # The eye line. The temple goes IN (a width, so a lobe) and the ORBIT
        # goes BACK (a relief, so a zoff). The two used to be one lobe and the
        # head paid for the socket in width.
        (0.46, 0.99, -0.008, {"power": 2.1, "squash_front": ff,
                              "lobes": _mirror(2.0, 28.0, -0.045),
                              "zoff": _mirror(ey, 19.0, -0.105, 1.2)
                              + ((90.0, 11.0, -0.055, 1.6),)}, "base"),
        # The supraorbital rim: the superciliary arches, and the NASION notch
        # between them. The nose is a separate solid whose bridge used to sit
        # exactly level with the face plane -- 0.871 hd against 0.860 -- so it
        # had no root at all. Cutting the notch is what gives it one.
        (0.515, 1.00, -0.013, {"power": 2.1, "squash_front": ff,
                               "lobes": _mirror(2.0, 26.0, -0.030),
                               "zoff": _mirror(ey, 21.0, +0.055)
                               + ((90.0, 12.0, -0.070, 1.6),)}, "face"),
        # The supraorbital torus. A width AND a relief: the ridge is wider than
        # the frontal bone above it and stands proud of it.
        (0.57, 1.00, -0.018, {"power": 2.1, "squash_front": ff,
                              "lobes": ((90.0, 46.0, 0.045),),
                              "zoff": ((90.0, 13.0, -0.045, 1.6),)}, "base"),
        # The frontal eminences -- the pair of low domes above the brow that
        # stop a forehead being a cone.
        (0.635, 0.995, -0.025, {"power": 2.05, "squash_front": ff * 0.97,
                                "zoff": _mirror(90.0 - 30.0, 24.0, +0.022)},
         "face"),
        # The frontal squama, sloping back.
        (0.70, 0.98, -0.030, {"power": 2.0, "squash_front": ff * 0.94}, "base"),
        # The parietal and the occiput behind it.
        (0.86, 0.90, -0.042, {"power": 2.0, "squash_front": ff * 0.90,
                              "lobes": ((270.0, 55.0, 0.055),)}, "base"),
        (1.00, 0.46, -0.052, {"power": 2.0, "squash_front": ff * 0.90}, "base"),
    )
    return tuple(_tier_rows(rows, form))


def _limb_ts(bulge_at, rings=LIMB_RINGS, form=False):
    """Where a limb's rings sit along its own length, as parameter values.

    THE DOCSTRING BELOW USED TO CLAIM THE JOINT RING WAS PINNED AT `bulge_at`
    AND IT WAS NOT -- the ring plan was `k / (rings - 1)`, five evenly spaced
    values, and no `bulge_at` this module uses is one of them. The consequence
    is arithmetic and it is the whole shoulder: an arm authored with a 1.30
    deltoid at t = 0.16 was sampled at t = 0.25, where the envelope has already
    fallen to 0.33 of its peak, so the built bulge was 1.098. A leg authored
    with a 1.10 calf at 0.55 was sampled at 0.50 and built 1.034. Both muscles
    existed in the parameters and in no vertex, for as long as the function has
    existed.

    So the plan is the SAME even spacing it always was, with the one ring
    nearest the belly snapped onto it. That is the minimal repair and it is
    deliberately minimal: the elbow and the knee are where they were (0.50 on
    an arm, 0.25/0.75 on a leg), the count is unchanged, so lod4 does not move
    by a triangle -- and the muscle exists.

        arm  (belly 0.19)   0, 0.19, 0.50, 0.75, 1.0
        leg  (belly 0.62)   0, 0.25, 0.62, 0.75, 1.0

    AND A BELLY MUST NOT SIT ON A JOINT, which is a constraint this function
    creates by snapping. `FIGURE` puts the knee at 0.527-0.572 of the leg, so a
    calf authored at 0.55 pulled a ring onto the knee and `animation.
    rigid_track` -- a different module's gate -- went 10.7 mm to 30.3 mm
    against a 20 mm bar. See the note beside the leg in `build_humanoid`.

    `form` adds two rings at `features == "all"` only: one at half the belly's
    height, which is the muscle's superior slope -- the part of a deltoid that
    caps the shoulder -- and one in the middle of the widest remaining gap.
    They are a strict superset by construction.
    """
    b = max(1e-6, min(1.0 - 1e-6, bulge_at))
    ts = [k / (rings - 1) for k in range(rings)]
    near = min(range(1, rings - 1), key=lambda i: abs(ts[i] - b))
    ts[near] = b
    ts.sort()
    if not form:
        return ts
    extra = [b * 0.5]
    gaps = sorted(zip(ts, ts[1:]), key=lambda p: p[1] - p[0], reverse=True)
    extra.append((gaps[0][0] + gaps[0][1]) / 2.0)
    # 0.06, not an epsilon: a leg's belly is at 0.55 so its superior slope
    # lands on 0.275, which is 0.025 from the ring already at 0.25. Two rings
    # 2.5% of a limb apart are a near-degenerate band that costs a full ring of
    # triangles and moves the surface by nothing.
    for e in extra:
        if all(abs(e - t) > 0.06 for t in ts):
            ts.append(e)
    return sorted(ts)


def _limb(p0, p1, r0, r1, seg, bulge=1.12, bulge_at=0.5, rings=LIMB_RINGS,
          section=None, depth_k=1.0, form=False, sections=()):
    """A tapered limb from p0 to p1 as a loft of `rings` rings.

    `bulge` puts a muscle belly at `bulge_at`, which `_limb_ts` now actually
    puts a ring on -- see its note, and the 1.30 deltoid that was built as 1.098
    for as long as this function existed. That is also what makes the PROFILE
    LOD schedule interesting: dropping the joint ring on a limb with a real
    bulge is a measurable silhouette error and dropping a mid-shaft ring is not.

    `depth_k` scales the +/-Z radius against the +/-X one, and `section` is the
    shaping block from `_ring`. A limb was a solid of revolution here and a limb
    is not one: an upper arm is flattened front to back, a calf is deeper than
    it is wide and its mass sits at the BACK. Both cost nothing.

    `sections` is an optional list of `(t, extra_section)` overrides blended in
    by nearest t, so one limb can be square at the deltoid and round at the
    wrist without becoming two lofts.
    """
    out = []
    ax, ay, az = p0
    bx, by, bz = p1
    sec = dict(section or {})
    for t in _limb_ts(bulge_at, rings, form):
        r = r0 + (r1 - r0) * t
        r *= 1.0 + (bulge - 1.0) * math.sin(math.pi * min(1.0, t / max(bulge_at, 1e-6))
                                            if t <= bulge_at else
                                            math.pi * (1.0 - (t - bulge_at)
                                                       / max(1e-6, 1.0 - bulge_at)))
        s = dict(sec)
        for st, extra in sections:
            w = max(0.0, 1.0 - abs(t - st) / 0.30)
            if w <= 0.0:
                continue
            for key, val in extra.items():
                if key == "lobes":
                    s["lobes"] = tuple(s.get("lobes", ())) + tuple(
                        (lb[0], lb[1], lb[2] * w) + tuple(lb[3:]) for lb in val)
                else:
                    s[key] = 1.0 + (val - 1.0) * w
        out.append(_ring(ax + (bx - ax) * t, ay + (by - ay) * t,
                         az + (bz - az) * t, r, r * depth_k, seg, **s))
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
                   features="all", form=None):
    """The base topology: torso, head, two arms, two legs, plus attachments.

    `form` overrides the ring tier that `features` would imply. It exists for
    ONE caller and that caller is a control: `_detail_gate` part 5 has to build
    the same feature level with the form rings on and off, to show that
    `feature_schedule`'s part-list and bounding-box instruments both score the
    difference at zero. A control that cannot be constructed is a control that
    does not exist, which is this repository's most-repeated defect.
    """
    m = Mesh()
    H = ind.stature_m
    b = ind.build
    keep = _feature_filter(features)
    # THE ONE SWITCH THE FORM TIER HANGS OFF. `features == "all"` is lod0-lod2,
    # which `lod_chain()` uses out to 22.1 m; past that the profile falls back
    # to its base rings and nothing about the corridor bake moves. See
    # RING_TIERS for why this is a ring-count decision and not a feature-list
    # one, and `_detail_gate` part 5 for the chord error it is priced by.
    form = _form_for(seg, features) if form is None else form
    face_form, body_form = form_flags(form)

    # --- torso ------------------------------------------------------------
    # The section block comes from the profile; `squash_front` is the torso-wide
    # 1.08 unless the ring names its own, and the two MULTIPLY rather than one
    # replacing the other -- a ribcage is 4% deeper in front than the rest of
    # the trunk AND the whole trunk is deeper in front than behind.
    prof = _torso_profile(ind, sp, body_form)
    rings = []
    for _n, fy, w, d, sec, _tier in prof:
        sec = dict(sec)
        sec["squash_front"] = 1.08 * sec.get("squash_front", 1.0)
        rings.append(_ring(0.0, fy * H, 0.0, w * H, d * H, seg, **sec))
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
        #
        # THREE RINGS, AND THE BOTTOM ONE IS THE FIX FOR judge-4e's F-9.
        # `_torso_profile` closes on a trapezius ring at 0.40 of the shoulder
        # half-width, 0.024 of stature above the acromion -- a 42 mm rise from
        # a 118 mm half-width to a 47 mm one. That is not a slope, it is a lid,
        # and a two-ring neck standing on it gave the render a head balanced on
        # a post above a shelf. The added root ring is nearly twice the neck's
        # own radius with the same 20-degree trapezius lobes the torso's top
        # ring carries, so the two solids meet at similar widths and the
        # sterno-mastoid runs into the shoulder instead of off a cliff. One
        # ring: 2 x seg triangles, 16 of them at the level the crowd ships at.
        m.add(*_loft([_ring(0.0, sh_y - 0.042 * H, -0.004 * H,
                            neck_r * 1.90, neck_r * 1.72, seg, power=2.2,
                            lobes=_mirror(20.0, 45.0, 0.12)),
                      _ring(0.0, sh_y + 0.012 * H, -0.004 * H,
                            neck_r * 1.22, neck_r * 1.26, seg, power=2.1),
                      _ring(0.0, chin_y + 0.010 * H, -0.006 * H,
                            neck_r * 0.86, neck_r * 0.94, seg)]),
              "npc_%s_neck" % sp.surface.kind, "neck")

    cw, ch, cd = ind.cranium
    hw = head_h * 0.36 * cw          # half-width at the widest ring
    hd = head_h * 0.36 * cd
    hrings = []
    for t, k, zo, sec, _tier in _head_profile(ind, face_form):
        jk = sp.jaw_k + (1.0 - sp.jaw_k) * min(1.0, max(0.0, t) / 0.34)
        # `squash_front` < 1 flattens the +Z half only: the face is a plane and
        # the back of the skull is a dome, which is what separates a head from
        # a solid of revolution at any distance where the profile reads. The
        # per-ring landmark shaping rides on top of it -- see `_head_profile`.
        hrings.append(_ring(0.0, chin_y + head_h * ch * t, head_h * zo,
                            hw * k * jk, hd * k * jk, seg, **sec))
    m.add(*_loft(hrings), "npc_%s_head" % sp.surface.kind, "head")

    # The face. Built here rather than as a species attachment because every
    # humanoid has one and `FACE_PLANS` says what KIND -- a Narn has no external
    # ear and a pak'ma'ra has no nose at all, and both of those are a row in a
    # table rather than a branch.
    if "face" in keep:
        _face(m, ind, sp, seg, chin_y, head_h, hw, hd, ch)

    # --- arms -------------------------------------------------------------
    # +0.005 rather than -0.02: the arm's root ring now sits INSIDE the torso
    # instead of level with its side, which is what left a lit disc floating at
    # each shoulder in the first render.
    arm_top = FIGURE["acromion"] + 0.005
    arm_bot = FIGURE["fingertip"] + 0.030      # wrist; the hand carries the rest
    span = (arm_top - arm_bot) * sp.arm_k
    sw_h = _shoulder_half(ind) * H
    # The root is INBOARD and NARROW; the deltoid is the bulge just below it.
    # Rooting the arm at the shoulder's own half-width put its top cap level
    # with the torso's side, which reads as a lit disc floating at the shoulder
    # and which `contains()` reports as 9 of 8 root vertices outside the solid.
    #
    # The WRIST end moved from 0.96 to 1.02 of the biacromial half-width in
    # session 4e, and it was forced by a measurement rather than chosen. The
    # pelvis's width is pinned by its leg roots at 0.1134 of stature and the
    # hanging wrist sat at 0.1136 -- the forearm hung exactly ON the hip, which
    # is why `costume.py`'s Nightwatch armband gate (at least 40% of the band
    # clear of the coat, FACTIONS 5.4's political signal) was the first thing
    # to fail when the pelvis section stopped being an ellipse. At 1.02 the
    # band reads 50% clear against 46% before any of this session's work.
    ax_in, ax = sw_h * 0.44, sw_h * 1.02
    r_up, r_wr = 0.028 * H * b, 0.022 * H * b
    lseg = max(4, seg // 2)
    for side in (-1, 1):
        # An arm is not a cone of revolution either: the section is wider across
        # the deltoid than it is deep, and squarer at the elbow than at the
        # wrist. `_limb`'s `section` rides the same free mechanism the torso and
        # head use, and the flattening is what stops a sleeve reading as a pipe.
        #
        # THE DELTOID BELLY IS NOW BUILT AND IT WAS NOT BEFORE -- `_limb_ts`
        # puts a ring on `bulge_at`, so the authored 1.30 is 1.30 in the mesh
        # instead of the 1.098 five evenly-spaced rings sampled. `bulge_at`
        # moved 0.16 -> 0.19 with it: with the belly ACTUALLY at 0.16 of the
        # arm the mass sat above the torso's own deltoid ring and the two
        # surfaces crossed at a grazing angle over 40 mm, which is the case a
        # renderer sorts worst. At 0.19 the arm's widest point is 26 mm below
        # the torso's and it emerges through it steeply.
        #
        # The lateral lobe at 0/180 is the deltoid's own outboard mass, and it
        # is what carries the muscle out to the biacromial width: `sections`
        # blends it in around the belly and out again by the elbow, so a
        # forearm is not built with a shoulder's section.
        arm = _limb((side * ax_in, arm_top * H, 0.0),
                    (side * ax, (arm_top - span) * H, 0.0),
                    r_up, r_wr, lseg, bulge=1.30, bulge_at=0.19,
                    section={"power": 2.3, "squash_front": 0.94},
                    depth_k=0.90, form=body_form,
                    sections=((0.19, {"power": 2.7,
                                      "lobes": _mirror(0.0, 54.0, 0.14)}),))
        arm = _stride(arm, ring_stride)
        m.add(*_loft(arm), "npc_%s_arm" % sp.surface.kind, "arm")
        if "hands" in keep and "hands" in ind.features:
            _hand(m, ind, sp, side, ax, (arm_top - span) * H, r_wr, lseg, keep)

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
        # The calf lobe sits at 270 degrees, which is the BACK. A leg whose
        # mass is centred is a table leg; the gastrocnemius is the reason a
        # standing figure reads as standing rather than as propped up.
        # The calf's own 1.10 was built as 1.034 for the same reason the
        # deltoid was built as 1.098 -- see `_limb_ts`. With a ring on the
        # belly it is 1.10, and `bulge_at` 0.55 now names the gastrocnemius
        # rather than a point between two rings. The thigh gets its own lobe
        # forward (the rectus) so the leg is not symmetric front to back.
        #
        # 0.62 AND NOT 0.55, AND THE RIG IS WHAT SAID SO. `FIGURE`'s own
        # numbers put the knee at t = 0.527-0.572 of the hip-to-ankle span
        # depending on `leg_k`, so a belly at 0.55 lands a ring ON THE JOINT --
        # and `_limb_ts` now snaps a ring to the belly, so it actually did.
        # `animation.rigid_track` fires on exactly that: a piece straddling a
        # joint has to follow one bone while its vertices interpolate two, and
        # the human's worst rigid piece went 10.7 mm -> 30.3 mm against a 20 mm
        # bar. The gastrocnemius belly is BELOW the knee -- about 0.62 of the
        # span -- which is both where the muscle is and clear of the joint, and
        # it takes the fit back to 10.7 mm. A number checked by a second
        # module's gate, which is the point of having one.
        leg = _limb((side * lx, hip_y * H, 0.0), (side * lx, ank_y * H, 0.0),
                    r_th, r_an, lseg, bulge=1.10, bulge_at=0.62,
                    section={"power": 2.2, "lobes": ((270.0, 70.0, 0.10),)},
                    depth_k=1.06, form=body_form,
                    sections=((0.14, {"power": 2.4,
                                      "lobes": ((90.0, 60.0, 0.05),)}),))
        leg = _stride(leg, ring_stride)
        m.add(*_loft(leg), "npc_%s_leg" % sp.surface.kind, "leg")
        if "feet" in keep and "feet" in ind.features:
            # A foot is narrow at the heel, widest across the ball, and its
            # toe box is a wedge rather than a cone -- so the forward rings are
            # squarer AND offset forward, which is what puts the instep in.
            #
            # THE TOP RING IS INSIDE THE SHIN, and it was not until 4g. It sat
            # at exactly `ank_y * H` with exactly `r_an` and exactly `lseg`
            # segments -- the leg's own last ring, to the vertex. Two closed
            # shells with a coincident capped disc between them is 4 triangles
            # on one edge, which `edge_census` cannot see because it keys on
            # vertex INDEX and the two caps are different indices, and which
            # `interior.boundary_edges` sees immediately because it keys on
            # POSITION. It is the same defect as session 3x's `portal_frame`:
            # coincident faces are geometry nobody can see, and they z-fight.
            # The comment 20 lines up already stated the rule -- "rooted a
            # little ABOVE ... so the two solids overlap" -- and the ankle was
            # the one joint in the figure that did not follow it.
            foot = [_ring(side * lx, (ank_y + 0.020) * H, 0.0, r_an * 0.94,
                          r_an * 0.94, lseg, power=2.2),
                    _ring(side * lx, 0.012 * H, 0.020 * H, r_an * 1.05,
                          r_an * 1.9, lseg, power=2.5,
                          lobes=((90.0, 60.0, 0.06),)),
                    _ring(side * lx, 0.006 * H, 0.045 * H, r_an * 0.9,
                          r_an * 2.4, lseg, power=3.0)]
            m.add(*_loft(foot), "npc_%s_foot" % sp.surface.kind, "foot")

    # --- species attachments ----------------------------------------------
    for f in ind.features:
        if f in ("hands", "feet") or f not in keep:
            continue
        fn = _FEATURES.get(f)
        if fn is not None:
            fn(m, ind, sp, seg, chin_y, head_h, hw, hd)

    # --- the dark parts of the face, LAST ----------------------------------
    # EMITTED HERE AND NOT WITH `_face`, AND THE REASON IS THE DRAW-CALL MERGE.
    # `populace._by_material` merges a body's spans into one span per RUN of
    # the same material, and a run only ever joins spans that are already
    # ADJACENT in the triangle list. The eyes and brows are `npc_hair`; the
    # nose and the ears are skin, and so is a Narn's brow ridge. Emitted with
    # the face they would cut the skin run in three; emitted before the
    # attachments they would cut it in two on every species whose attachment is
    # skin. Emitted LAST they sit beside the hair, and a body's merged span
    # count does not move at all -- which `_detail_gate` measures per species,
    # against `budget.BUDGETS["deck_primitives"] = 600`, and which has a
    # control that reorders them and watches the count grow.
    if "eyes" in keep:
        _f_eyes(m, ind, sp, seg, chin_y, head_h, hw, hd, ch)

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


def _head_at(ind, t):
    """(radius scale, z offset) of the SKULL at head-height fraction `t`.

    Linear interpolation of `_head_profile`'s own table, clamped at both ends.
    Hair and ears are placed with it, so they follow whatever the skull does --
    including a Narn's heavier braincase and a pak'ma'ra's deeper one -- instead
    of carrying a second copy of the head's shape that goes stale the first time
    the profile is edited. Hard rule 4, at the scale of a haircut.
    """
    prof = _head_profile(ind)
    if t <= prof[0][0]:
        return prof[0][1], prof[0][2]
    for r0, r1 in zip(prof, prof[1:]):
        (t0, k0, z0), (t1, k1, z1) = r0[:3], r1[:3]
        if t <= t1:
            f = (t - t0) / max(t1 - t0, 1e-9)
            return k0 + (k1 - k0) * f, z0 + (z1 - z0) * f
    return prof[-1][1], prof[-1][2]


# ---------------------------------------------------------------------------
# Hair
# ---------------------------------------------------------------------------
# WHY THIS IS A TABLE AND NOT A CAP. The previous `_f_hair` was three rings of
# skull cap, identical on every resident who had hair at all, and `no_detail`
# -- the feature level everything past 4.4 m uses -- dropped it, so the corridor
# crowd the owner was looking at in session 4e was **bald, to a person**. Both
# halves of that are fixed here: the tier moves (see FEATURE_TIER) and the cap
# becomes eight styles chosen from the resident's own hash.
#
# Fields, all in fractions of head height / skull radius:
#   lo      where the hair's lowest ring sits on the skull, in head-height t
#   vol     radial multiplier on the skull at every ring above the first
#   crown   extra height above the crown
#   pull    how far the front of the cap is pulled BACK off the face; this is
#           the hairline, and it is negative amplitude on a lobe at 90 degrees
#   nape    length of the mass hanging behind, 0 for none
#   nape_w  its half-width as a fraction of the skull's
#   knot    radius of a gathered knot above the crown, 0 for none
#
# EXTRAPOLATED, authority 5, and the constraint is the era rather than anatomy:
# `reference/14-characters-and-uniforms/` is Season 2-3, where EarthForce
# personnel are uniformly short-cropped and civilians in the Zocalo frames carry
# everything from shaved to shoulder-length. The distribution below is weighted
# to that -- most of the station is crew -- and what would overturn it is a
# frame-by-frame count of a Zocalo crowd, which no reference here supports.
HAIR_STYLES = {
    "shaved":   dict(lo=0.52, vol=1.010, crown=0.005, pull=0.05, nape=0.0,
                     nape_w=0.0, knot=0.0),
    "crop":     dict(lo=0.50, vol=1.045, crown=0.020, pull=0.10, nape=0.0,
                     nape_w=0.0, knot=0.0),
    "short":    dict(lo=0.44, vol=1.070, crown=0.035, pull=0.14, nape=0.0,
                     nape_w=0.0, knot=0.0),
    "swept":    dict(lo=0.44, vol=1.090, crown=0.070, pull=0.20, nape=0.0,
                     nape_w=0.0, knot=0.0),
    "receding": dict(lo=0.46, vol=1.040, crown=0.010, pull=0.34, nape=0.0,
                     nape_w=0.0, knot=0.0),
    "bob":      dict(lo=0.26, vol=1.110, crown=0.030, pull=0.16, nape=0.10,
                     nape_w=0.85, knot=0.0),
    "long":     dict(lo=0.24, vol=1.120, crown=0.035, pull=0.14, nape=0.62,
                     nape_w=0.80, knot=0.0),
    "up":       dict(lo=0.46, vol=1.060, crown=0.020, pull=0.12, nape=0.0,
                     nape_w=0.0, knot=0.30),
}

# Weighted draws, by sex. Weights rather than a flat list because a flat list
# puts one resident in eight in a topknot, and the S2-3 frames do not.
HAIR_BY_SEX = {
    "m": (("crop", 34), ("short", 26), ("swept", 14), ("receding", 12),
          ("shaved", 10), ("long", 4)),
    "f": (("short", 22), ("bob", 22), ("long", 20), ("up", 16), ("swept", 12),
          ("crop", 8)),
}


def hair_style_for(seed: str, sex: str) -> str:
    """One resident's haircut. A pure function of their hash, like everything
    else about them -- `_pick` is uniform, so the weights are expanded here."""
    table = HAIR_BY_SEX.get(sex, HAIR_BY_SEX["m"])
    total = sum(w for _k, w in table)
    x = _u(seed, "hair") * total
    for k, w in table:
        x -= w
        if x <= 0.0:
            return k
    return table[0][0]


def _f_hair(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """The resident's own haircut: a cap that follows the skull, a hairline
    pulled back off the face, and optionally a mass behind or a knot above.

    The bottom ring is deliberately INSIDE the skull (`vol` is not applied to
    it) so the cap has no visible bottom rim: the same trick the head itself
    uses at t = -0.07 and the arm root uses at the shoulder. Without it a bowl
    of hair sits on the head with a lit disc of an edge all the way round, which
    is what "hat" looks like and what "hair" does not.
    """
    st = HAIR_STYLES.get(ind.hair_style)
    if st is None:
        return
    ch = ind.cranium[1]

    # HALF THE BODY'S SEGMENT COUNT, for the same reason a limb gets half:
    # sagitta scales with radius, and a skull cap's radius is a third of the
    # figure's worst section (0.088 m against 0.22 m at the Gaim mantle), so at
    # seg/2 it is still finer than the schedule the body itself is built to.
    # Checked, not asserted: at seg 16 the cap's sagitta is 1.7 mm, honest from
    # 1.7 m against lod1's 2.23 m; at seg 8 it is 6.7 mm, honest from 6.9 m
    # against lod2's 8.92 m. The floor is 8 rather than the limbs' 4 because a
    # cap is seen against the BACKGROUND at the top of the head, where a
    # four-sided outline is a lozenge. Saves 320 triangles a figure at lod0 and
    # 160 at lod1, which is what paid for the face.
    hseg = max(8, seg // 2)

    def ring_at(t, scale, lobes=(), dz=0.0):
        k, zo = _head_at(ind, t)
        return _ring(0.0, chin_y + head_h * ch * t, head_h * (zo + dz),
                     hw * k * scale, hd * k * scale, hseg,
                     squash_front=FACE_FLATTEN, power=2.0, lobes=lobes)

    lo, vol = st["lo"], st["vol"]
    pull = (90.0, 70.0, -st["pull"])
    # A five-ring stack: buried root, hairline, side, parietal, crown. Fewer
    # than five and the cap cannot both hug the skull at the temple and stand
    # proud at the crown, which is the whole shape of a haircut.
    #
    # EVERY RING ABOVE THE ROOT FOLLOWS `_head_at`'s OWN TAPER, offset outward
    # by `vol` and never crossing it. The first version scaled the top ring to
    # 0.52 of the skull, which put the cap's crown INSIDE the head while its
    # parietal ring was outside -- the two surfaces crossed somewhere over the
    # top of the skull, and a crossing between two nearly parallel surfaces is
    # the one thing a renderer cannot resolve cleanly. It showed as a comb of
    # slivers across the crown in `tools/preview_render.py`, which sorts
    # triangles by mean depth and has no z-buffer at all, so it renders that
    # case at its worst. Only the ROOT is deliberately inside, and it is 14%
    # inside over 5% of head height, which is a steep crossing and a short one.
    rings = [ring_at(lo, 0.86),
             ring_at(lo + 0.05, vol, (pull,)),
             ring_at(max(lo + 0.20, 0.70), vol * 1.02, (pull,), dz=-0.004),
             ring_at(0.88, vol * 1.02, dz=-0.006),
             ring_at(1.0 + st["crown"] / max(ch, 1e-6), vol * 1.04, dz=-0.008)]
    m.add(*_loft(rings), "npc_hair", "hair")

    if st["nape"] > 0.0:
        # The mass behind: a blade hanging off the occiput. Built with the same
        # `_blade` the crests use, so it inherits their closure and winding.
        k, zo = _head_at(ind, lo + 0.06)
        _blade(m, "npc_hair", "hair",
               0.0, chin_y + head_h * ch * (lo + 0.10),
               head_h * zo - hd * k * 0.55,
               hw * k * st["nape_w"], -head_h * st["nape"], hd * k * 0.42,
               hseg, sweep=hd * 0.06, taper=0.62, rings=3)

    if st["knot"] > 0.0:
        r = hw * st["knot"]
        y = chin_y + head_h * ch * (1.0 + st["crown"] / max(ch, 1e-6))
        m.add(*_loft([
            _ring(0.0, y - r * 0.30, -hd * 0.18, r * 0.62, r * 0.62,
                  max(4, hseg // 2)),
            _ring(0.0, y + r * 0.55, -hd * 0.26, r * 1.00, r * 0.88,
                  max(4, hseg // 2)),
            _ring(0.0, y + r * 1.20, -hd * 0.30, r * 0.40, r * 0.36,
                  max(4, hseg // 2))]), "npc_hair", "hair")


# ---------------------------------------------------------------------------
# The face
# ---------------------------------------------------------------------------
# WHICH FEATURES A SPECIES' FACE HAS. A row, not a branch -- the same shape of
# solution the rest of the module uses, so the sixteenth species is a row too.
#   "humanoid" nose and external ears
#   "ridged"   nose, no external ear (the Narn crown is a reticulated dome in
#              `G'Kar more.jpg` and carries no pinna; the brow attachment
#              already models what that face DOES have)
#   "flat"     a small nose only -- the Vree is built large-craniumed and
#              small-featured
#   "none"     no nose at all: the pak'ma'ra face is four tendrils and a maw
FACE_PLANS = ("humanoid", "ridged", "flat", "none")


def _face(m, ind, sp, seg, chin_y, head_h, hw, hd, ch):
    """A nose and a pair of ears, placed off the skull's own interpolated shape.

    THIS IS THE PART THE OWNER WAS LOOKING AT. A head with a brow, a jaw and a
    chin is still a mannequin if there is nothing on the front of it, and at
    conversation distance -- which is where `lod0`'s 64-segment ring exists at
    all -- the nose is the single feature that says the figure has a front.

    Both are small: the nose stands 20 mm proud of the face plane and an ear is
    60 mm tall. `feature_schedule` will therefore measure them as nearly free to
    cull, and they ARE -- which is why the whole face carries the `detail` tier
    and is gone past 4.4 m. What is NOT free to cull is the hair, and that is
    the correction this session makes to the tier table.
    """
    plan = sp.face
    if plan == "none":
        return
    # SIZED BY THEIR OWN SAGITTA, not by the body's. These are 20-60 mm objects
    # and building them at the body's 64 segments is the mistake
    # `costume._att_seg` records paying for a collar. A nose's section radius is
    # 0.014 m, so at 4 segments its sagitta is 4.1 mm -- honest from 4.2 m -- and
    # at 8 segments 1.1 mm, honest from 1.1 m. `seg // 4` therefore gives 8 at
    # the two levels used inside 9 m and 4 at every level beyond it, which is
    # exactly where those two distances fall. 4 divides 8, so the strict-subset
    # property survives the switch. It is 136 triangles a figure at seg 16, and
    # that is the band a crowded Zocalo spends most of its budget in.
    fseg = max(4, min(8, seg // 4))
    small = plan == "flat"

    # --- nose --------------------------------------------------------------
    # THE NOSE IS DEEPLY BURIED AND THAT IS THE WHOLE OF ITS CONSTRUCTION. Its
    # z-radius is 0.33 of the head's own depth -- 69 mm on a human -- against a
    # PROJECTION past the face plane of 20 mm, so two thirds of the solid is
    # inside the skull. A shallow blob laid on the face crosses it at a grazing
    # angle over the blob's whole footprint, which is the case no renderer sorts
    # well; a deeply buried one crosses along a short steep curve. The first and
    # last rings are entirely inside the head, so the nose EMERGES between
    # t = 0.28 and t = 0.50 and has no visible seam at either end -- the same
    # trick the head's own t = -0.07 ring and the arm root use.
    #
    # AND THE PROJECTION IS NOW MEASURED FROM THE SKULL RATHER THAN FROM THE
    # ORIGIN, which is the same hard-rule-4 correction `_face_point` got. Every
    # ring centre used to be an absolute fraction of the head's depth --
    # `hd * 0.74` -- so the nose knew nothing about the face it sits on. The
    # moment session 4h gave the maxilla a lip that stands 4.4 mm proud, the
    # face plane came out to meet the nose and the nose lost a fifth of its
    # projection without a number changing. It is now `_face_point(..., 0.0)`,
    # the midline of the skull's own surface at that height, plus a stated
    # projection: so the nasion notch cut into the brow ring gives the bridge a
    # ROOT, the philtrum below gives it a base, and a Narn's deeper skull moves
    # its nose with it.
    #
    # Projections, in fractions of head depth, EXTRAPOLATED at authority 5 from
    # standard adult nasal proportion -- nasal length (nasion to subnasale)
    # ~0.22 of head height, projection (subnasale to pronasale) ~20 mm on a
    # 231 mm head = 0.087 of head height = 0.24 of head depth.
    nw = hw * (0.17 if not small else 0.12)
    small_k = 0.62 if small else 1.0
    rings = []
    for t, rx_k, proj, rz, alae in ((0.235, 0.50, -0.100, 0.16, 0.00),
                                    (0.290, 1.00, +0.150, 0.30, 0.34),
                                    (0.330, 0.95, +0.240, 0.32, 0.16),
                                    (0.400, 0.72, +0.150, 0.28, 0.00),
                                    (0.480, 0.62, +0.045, 0.24, 0.00),
                                    (0.560, 0.55, -0.060, 0.20, 0.00)):
        _sx, _sy, sz = _face_point(ind, sp, t, 0.0, chin_y, head_h, hw, hd, ch)
        # The ring's own depth is the buried part; `proj` is how far its FRONT
        # stands past the skull, so the centre is (surface + proj) - rz.
        rzz = hd * rz * small_k
        cz = sz + hd * proj * (0.72 if small else 1.0) - rzz
        rings.append(_ring(0.0, chin_y + head_h * ch * t, cz,
                           nw * rx_k, rzz, fseg, power=2.3,
                           # The alae: the nostril wings are the widest part of
                           # a nose and they sit BEHIND the tip, so they are a
                           # radial lobe at the sides of the nose's own ring.
                           lobes=_mirror(0.0, 62.0, alae) if alae else ()))
    m.add(*_loft(rings), "npc_%s_nose" % sp.surface.kind, "nose")

    if plan != "humanoid":
        return
    # --- ears --------------------------------------------------------------
    # Behind the widest point of the head and set slightly back, which is where
    # a pinna is; thin across x, broad fore-aft, and swept out at the top.
    for side in (-1, 1):
        rings = []
        for t, xk, rxk, rzk, zk in ((0.34, 0.90, 0.05, 0.09, -0.10),
                                    (0.44, 1.00, 0.075, 0.17, -0.12),
                                    (0.55, 0.93, 0.05, 0.11, -0.15)):
            k, zo = _head_at(ind, t)
            rings.append(_ring(side * hw * k * xk,
                               chin_y + head_h * ch * t,
                               head_h * zo + hd * zk,
                               hw * rxk, hd * rzk, fseg, power=2.4))
        m.add(*_loft(rings), "npc_%s_ear" % sp.surface.kind, "ear")


# ---------------------------------------------------------------------------
# Hands
# ---------------------------------------------------------------------------
# Four fingers, as (z position across the palm, length, radius), the last two
# in fractions of the wrist radius and the first of the knuckle ring's own
# depth. The proportions are standard adult hand anthropometry -- index and
# ring within 5% of each other, middle longest, little ~0.78 of middle, and the
# four spanning about 1.25 palm depths at the knuckle -- which is the same
# class of source as `FIGURE`'s cross-check: two references that could not have
# copied each other, the photograph and the anthropometric table. EXTRAPOLATED
# at authority 5 as a set; see docs/npc-detail-4g.md, INV-4G-002.
FINGER_PLAN = ((+0.62, 0.92, 0.98),      # index
               (+0.21, 1.00, 1.00),      # middle -- longest and thickest
               (-0.21, 0.94, 0.93),      # ring
               (-0.62, 0.78, 0.80))      # little
# Where the fingers leave the palm and where they end, in stature. The old
# four-ring mitt ran 0.000 -> 0.100 of stature, which is 175 mm on a human and
# is hand length; the split keeps that total and puts the metacarpal head at
# 0.045, so the fingers are 0.055 of stature = 96 mm, against an adult middle
# finger of 85-100 mm.
FINGER_ROOT_F = 0.045
FINGER_TIP_F = 0.100


def _hand(m, ind, sp, side, ax, hy, r_wr, lseg, keep):
    """A hand: a palm, four fingers and a thumb.

    IT WAS THREE RINGS OF NOTHING AND IT WAS ORIENTED WRONG. The old mitt was
    widest across X -- palms facing forward, which is a posture nobody stands
    in. A hand hanging at rest has its palm facing the thigh, so the broad axis
    is fore-aft (Z) and the thin axis is lateral (X), and the thumb points
    FORWARD. Getting that round the right way costs nothing and is most of why
    the old arm ended in a paddle.

    AND THEN IT WAS STILL A MITTEN, which is what session 4f left and what the
    owner is looking at: one closed lofted shell from the wrist to the
    fingertips with nothing cut into it. A mitten and a hand have the same
    bounding box, the same silhouette from the front, and completely different
    ones from every other angle -- the gap between two fingers is 4 mm of
    background showing through, and background showing through is the only
    thing that reads as a hand rather than as the end of a sleeve.

    So the palm now stops at the metacarpal head and four fingers carry the
    rest. THE PALM GETS SHORTER BY EXACTLY WHAT THE FINGERS ADD, so the hand
    does not grow: `FINGER_TIP_F` is the old plan's last ring. When `fingers`
    is culled the palm runs the full length again and the mitt comes back --
    it is the coarse level of the same object, not a different hand.

    Every count here is `_small_seg`'s, not the body's: a 9 mm finger built at
    the torso's 64 segments is the `costume._att_seg` mistake with a different
    part name.
    """
    H = ind.stature_m
    x = side * ax
    fingers = "fingers" in keep
    # (dy in stature, rx, rz, power, dz in stature)
    plan = [(0.000, 0.72, 0.86, 2.0, 0.000),      # wrist
            (0.030, 0.78, 1.20, 2.6, 0.004)]      # knuckles -- the widest ring
    if fingers:
        # The palm ends at the metacarpal head, a little proud of where the
        # fingers root, so the finger roots are BURIED and neither end shows a
        # seam -- the same trick the nose, the arm root and the head's t=-0.07
        # ring use.
        plan.append((FINGER_ROOT_F + 0.006, 0.70, 1.14, 2.8, 0.005))
    else:
        plan.append((0.070, 0.66, 1.10, 2.8, 0.006))    # mid-phalanx
        plan.append((0.100, 0.40, 0.62, 2.2, 0.004))    # fingertips
    rings = [_ring(x, hy - dy * H, dz * H, r_wr * rx, r_wr * rz, lseg,
                   power=p)
             for dy, rx, rz, p, dz in plan]
    m.add(*_loft(rings), "npc_%s_hand" % sp.surface.kind, "hand")

    if fingers:
        # Knuckle-ring depth, so the four sit across the palm the palm actually
        # has rather than across a remembered one.
        knuckle_rz = r_wr * 1.20
        r0 = r_wr * 0.30
        fseg = _small_seg(r0, lseg, floor=4, cap=8)
        y_root = hy - FINGER_ROOT_F * H
        for zf, lk, rk in FINGER_PLAN:
            length = (FINGER_TIP_F - FINGER_ROOT_F) * H * lk
            r = r0 * rk
            rings = []
            for k in range(3):
                t = k / 2.0
                # A hanging hand's fingers curl slightly toward the thigh, and
                # the tips converge: both are `t*t` so the root ring stays in
                # the plane the palm hands it.
                rings.append(_ring(
                    x - side * r_wr * 0.16 * t * t,
                    y_root + 0.010 * H - length * t,
                    knuckle_rz * zf * (1.0 - 0.14 * t * t) + r_wr * 0.06 * t,
                    r * (1.0 - 0.28 * t * t), r * (1.0 - 0.22 * t * t), fseg,
                    power=2.2))
            m.add(*_loft(rings), "npc_%s_finger" % sp.surface.kind, "finger")

    if "thumbs" not in keep:
        return
    tr = r_wr * 0.36
    tseg = _small_seg(tr, lseg, floor=4, cap=8)
    rings = []
    for dy, rk, dz in ((0.020, 1.00, 0.60), (0.044, 0.90, 1.05),
                       (0.066, 0.55, 1.30)):
        rings.append(_ring(x - side * r_wr * 0.40, hy - dy * H,
                           r_wr * dz, tr * rk, tr * rk, tseg))
    m.add(*_loft(rings), "npc_%s_thumb" % sp.surface.kind, "thumb")


# ---------------------------------------------------------------------------
# Eyes and brows
# ---------------------------------------------------------------------------
# WHY THESE ARE `npc_hair` AND NOT A NEW MATERIAL, said plainly because it is
# the one decision here a reviewer should push on. A body in this project has
# no UVs and no texture: `materials.py` binds one material per GROUP, so
# anything on a face that is not skin-coloured has to be its own group, and the
# only groups a body may emit are the ones the material library already binds
# -- `npc_skin`, `npc_hair`/`npc_crest`, the wardrobe, the suits. Inventing
# `npc_eye` would put every eye on the fallback, which is the defect CLAUDE.md
# records three times this week and `check_material_coverage` now fails on.
#
# `npc_hair` is the right one anyway rather than merely the available one: an
# EYEBROW IS HAIR, and the eye's aperture is the darkest thing on a face at any
# distance a crowd is seen from. Both are "darker than skin, matte", which is
# what `npc_hair` is measured as. What would overturn it: a `npc_eye` material
# with a sclera and an iris, which needs `materials.py` and is not this
# module's to add.
#
# Sizes, in fractions of head height, from adult craniofacial anthropometry --
# the same standard-proportion source `_head_profile` cites, and the same
# authority-5 status. Palpebral fissure 28 x 11 mm on a 231 mm head gives the
# half-extents below; interpupillary 63 mm on a 145 mm head width gives 0.43 of
# the head's own half-width, which is where the eye sits ACROSS the face.
# Logged as INV-4G-001 in docs/npc-detail-4g.md.
EYE_X_F = 0.43        # of the skull's half-width at the eye ring
EYE_T = 0.46          # `_head_profile`'s own eye-line row
BROW_T = 0.550        # on its brow-ridge row, 21 mm above the eye
EYE_HALF_W_F = 0.061  # of head height
EYE_HALF_H_F = 0.024
BROW_HALF_W_F = 0.078
BROW_HALF_H_F = 0.013


def _face_point(ind, sp, t, xf, chin_y, head_h, hw, hd, ch):
    """A point on the SKULL's own surface at head-height `t`, `xf` of the way
    out to its half-width. Returns (x, y, z).

    Hard rule 4 at the scale of an eye socket: the eye and the brow are placed
    off the head's actual section rather than off a remembered one, so a Narn's
    heavier braincase, a pak'ma'ra's deeper skull and every per-individual
    cranium jitter carry them without a second table. `_head_at` gives the
    radius scale and the z drift; the section block comes from the nearest row
    of `_head_profile`, so if that table is re-shaped the eyes move with it.

    AND IT NOW READS THE SECTION'S LOBES AND `zoff` TOO, which it did not
    before and which session 4h's orbit made compulsory. The old body of this
    function reconstructed the superellipse by hand -- `e = 1 - |xf|^p`, then
    `z = rz * e^(1/p) * sq` -- so it knew the ring's exponent and its front
    squash and NOTHING about the displacements laid on top of them. Cutting an
    8 mm orbit into the skull would then have left the eye standing exactly
    where the old un-socketed surface was: a bead on a ball, one level worse
    than the bead it already was. So the azimuth `xf` corresponds to is solved
    from the same superellipse (`_face_az`) and the point comes back out of
    `_ring_point`, the one function the ring itself is built from.
    """
    prof = _head_profile(ind)
    row = min(prof, key=lambda r: abs(r[0] - t))
    sec = dict(row[3])
    p = float(sec.get("power", 2.0))
    k, zo = _head_at(ind, t)
    jk = sp.jaw_k + (1.0 - sp.jaw_k) * min(1.0, max(0.0, t) / 0.34)
    rx, rz = hw * k * jk, hd * k * jk
    # `xf` is a signed fraction of the half-width and `_face_az` gives the
    # azimuth FROM +X at which the ring reaches it, so the figure's LEFT
    # (+X, xf > 0) is at `az` itself and its right at 180 - az. xf = 0 is the
    # midline of the face at 90 degrees, which is `_ring`'s stated convention.
    az = _face_az(abs(xf), p)
    theta = az if xf >= 0.0 else (180.0 - az)
    return _ring_point(0.0, chin_y + head_h * ch * t, head_h * zo,
                       rx, rz, theta, **sec)


def _f_eyes(m, ind, sp, seg, chin_y, head_h, hw, hd, ch):
    """Two eyes and two brows. THE PART THE WORD "FEATURELESS" IS ABOUT.

    A head with a nose and a pair of ears and nothing at the eye line is a
    mannequin, and a mannequin is exactly what the corridor render shows. At
    the distances a player meets somebody -- 1 to 6 m, where a head is 40 to
    240 px -- the eye is the first thing the eye finds, and the second is the
    brow. Nothing else on a face reads at all below about 100 px.

    Both are BURIED, roughly half their depth inside the skull, for the reason
    `_face` records for the nose: a shallow blob laid on a curved surface
    crosses it at a grazing angle over its whole footprint, which is the case
    no renderer sorts well, and a deeply set one crosses along a short steep
    curve. The eye then stands 0.32 of its own half-width proud, which is 4.5
    mm on a human -- an eye that is flush z-fights and an eye that is proud is
    a bug's.

    `plan == "none"` has no eyes (the pak'ma'ra face is four tendrils and a
    maw) and neither does an encounter suit, which never reaches this function.
    """
    if sp.face == "none":
        return
    ew = head_h * EYE_HALF_W_F
    eh = head_h * EYE_HALF_H_F
    ed = ew * 0.55
    # A Vree is built large-craniumed and small-featured, and its `flat` face
    # plan already shrinks the nose; the eyes follow the same factor so the one
    # species whose face is deliberately understated stays understated.
    small = 0.74 if sp.face == "flat" else 1.0
    ew, eh, ed = ew * small, eh * small, ed * small
    eseg = _small_seg(ew, seg, floor=4, cap=8)
    bseg = _small_seg(head_h * BROW_HALF_H_F, seg, floor=4, cap=8)

    for side in (-1, 1):
        ex, ey, ez = _face_point(ind, sp, EYE_T, side * EYE_X_F,
                                 chin_y, head_h, hw, hd, ch)
        # HOW FAR IT STANDS PROUD IS THE WHOLE OF WHETHER IT READS, and the
        # first version got it wrong in the safe direction. Buried 42% of its
        # depth like the nose, a 28 x 11 mm lens on a skull that curves away
        # under it emerged as two 3 mm slivers -- present in the mesh, absent
        # in the picture. It is a LENS, not a blob: the lid assembly of a real
        # eye stands about 10 mm proud of the orbital rim, so 0.86 of its depth
        # is outside and the crossing with the skull is still steep because the
        # section is flat (power 2.4) rather than round.
        cz = ez - ed * 0.14
        m.add(*_loft([
            _ring(ex, ey - eh, cz, ew * 0.62, ed * 0.66, eseg, power=2.4),
            _ring(ex, ey, cz, ew * 1.00, ed * 1.00, eseg, power=2.5),
            _ring(ex, ey + eh * 0.92, cz, ew * 0.70, ed * 0.72, eseg,
                  power=2.4)]),
            "npc_hair", "eye")

        bw = head_h * BROW_HALF_W_F * small
        bh = head_h * BROW_HALF_H_F * small
        bx, by, bz = _face_point(ind, sp, BROW_T, side * EYE_X_F,
                                 chin_y, head_h, hw, hd, ch)
        bcz = bz - bw * 0.30
        m.add(*_loft([
            _ring(bx, by - bh, bcz, bw * 0.86, bw * 0.36, bseg, power=2.6),
            _ring(bx, by, bcz, bw * 1.00, bw * 0.42, bseg, power=2.8),
            _ring(bx, by + bh * 0.86, bcz, bw * 0.74, bw * 0.32, bseg,
                  power=2.6)]),
            "npc_hair", "eyebrow")


def _f_brow(m, ind, sp, seg, chin_y, head_h, hw, hd):
    """A brow shelf. The ridged face's one attachment, and it earns its tier.

    `G'Kar more.jpg` shows deep vertical furrows under a heavy supraorbital
    ridge and a crown that is a reticulated DOME rather than a scalp -- and the
    shelf alone was only ever the first of those. The silhouette gate is what
    said so: with the brow and nothing else, a Narn and a human overlapped at
    IoU 0.875 from the front and 0.816 from the side at the level the corridor
    crowd is baked at, which is 82-88% the same picture. A supraorbital shelf
    projects FORWARD, so a front-view outline cannot see it at all, and the
    dome is the part that changes the head's outline from every angle.

    What is NOT here, and why, is below the shelf: a crown keel was built,
    measured, and removed.
    """
    bseg = max(6, seg // 2)
    y = chin_y + head_h * 0.60
    rings = [_ring(0.0, y - head_h * 0.05, hd * 0.30, hw * 0.80, hd * 0.34, bseg),
             _ring(0.0, y + head_h * 0.05, hd * 0.34, hw * 0.86, hd * 0.30, bseg)]
    m.add(*_loft(rings), "npc_%s_brow" % sp.surface.kind, "brow")

    # A CROWN KEEL WAS BUILT HERE AND THE MEASUREMENT THREW IT OUT. Written
    # down because a negative result nobody records is a thing the next context
    # builds again. The idea was a low fore-aft ridge over the crown, riding
    # `_head_at`, to give the Narn something the front view could see. It made
    # the number WORSE: human vs Narn went 0.875 -> 0.946 in the front head
    # band and 0.816 -> 0.832 in the side one, because a ridge standing proud
    # of the crown occupies exactly the outline region a HUMAN'S HAIR CAP
    # occupies, so it made a Narn look more like a person with a haircut, not
    # less. It cost 32 triangles at the bake level to do that.
    #
    # And the reference does not ask for it: `G'Kar more.jpg` shows a
    # reticulated, spotted DOME, which is a texture and a colour on a skull
    # this module already builds wider and deeper than a human's. The Narn is
    # the one species of the four whose identity is not a silhouette, the gate
    # below reports the pair as the closest of the six, and that is the honest
    # answer rather than an invented fin.


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

    AND IT WAS TOO SMALL TO BE THE THING IT NAMES, which the silhouette gate
    found rather than an opinion: at 0.46 of head height and 1.18 of the
    skull's half-width, a Minbari's head band overlapped a human's at IoU
    0.875 -- 87.5% the same picture -- while a Centauri's crest brought that
    pair to 0.770. The source says "wider than the skull" and this was barely
    wider; it now stands 0.74 of head height above where it leaves the skull
    and 1.44 of its half-width across. Both numbers are still EXTRAPOLATED,
    authority 5, and what bounds them is not taste: `_selftest` asserts every
    species clears `interior_kit.PROVISIONAL["door_height_m"]`, and the crest
    is measured into that bounding box. Logged as INV-4G-003. It costs ZERO
    triangles -- `_blade`'s ring and segment counts are unchanged.
    """
    _blade(m, "npc_crest", "minbari_crest", 0.0,
           chin_y + head_h * 0.70, -hd * 0.34,
           hw * 1.44, head_h * 0.74, hd * 0.30, seg,
           sweep=hd * 0.58, taper=0.82, rings=4)


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
def build_encounter_suit(ind: Individual, sp: SpeciesBody, seg=16,
                         ring_stride=1, features="all", form=None):
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
                 features="all", form=None):
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
    #
    # ITS BOTTOM RING IS INSIDE THE ROBE, and it was a literal copy of the
    # robe's top ring until 4g -- same centre, same radii, same segment count,
    # both capped. `interior.boundary_edges`, which keys edges on POSITION
    # rather than on vertex index, read 125 non-manifold edges on Kosh: 250
    # triangles of robe and 250 of yoke sharing one disc and z-fighting over
    # it. `edge_census` could not see it and had scored the suit closed since
    # the module was written. Buried 0.030 of stature down and 6% narrower, so
    # the two shells overlap the way every other joint in this file does.
    yoke = [_ring(0.0, collar_y - 0.030 * H, 0.0, collar_r * 0.94,
                  collar_r * 0.83, seg),
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
                        ring_stride=lv["ring_stride"], features=lv["features"],
                        form=lv.get("ring_form"))
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
        # OVER EVERY FEATURE LEVEL, AND THAT IS NOT THOROUGHNESS -- IT IS THE
        # DIFFERENCE BETWEEN A MEASUREMENT AND A FLATTERING ONE. `lod_chain`
        # composes the three schedules independently, so a stride is applied at
        # levels whose ring plan is the BASE tier; measuring the stride only on
        # the `all` build measures decimation of a stack that has six more
        # rings in it than the stack being decimated. It showed up the moment
        # the form tier landed: the grome torso's stride-4 error fell 0.1227 ->
        # 0.0749 purely because the measured torso had eleven rings instead of
        # eight, stride 2 and stride 4 became equally honest, and the chain
        # silently DROPPED a level on the strength of geometry that level does
        # not contain. Same shape as every gate this repository has had to fix:
        # it built the case without the defect in it.
        for level in FEATURE_STEPS:
            for key, sp in SPECIES.items():
                ind = individual(key, "lod-probe")
                m = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                    features=level)
                for name, verts, _tris in m.parts:
                    nrings = _rings_of(verts, seg, name)
                    if nrings is None or len(nrings) < 3:
                        continue
                    e = chord_error(nrings, stride)
                    if e > worst:
                        worst, where = e, f"{key} {name} at {level}"
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


def _chord_error_keep(rings, kept):
    """Worst deviation of the DROPPED rings from the surface `kept` would loft.

    The general form of `chord_error`, which is this with `kept` derived from a
    stride. Split out because the form tier's drop is not a stride -- it keeps
    an arbitrary subset -- and pricing it needed the same measurement rather
    than a second one.
    """
    kept = set(kept)
    worst = 0.0
    for i in range(len(rings)):
        if i in kept:
            continue
        lo = max((k for k in kept if k < i), default=None)
        hi = min((k for k in kept if k > i), default=None)
        if lo is None or hi is None:
            continue
        for a, b, c in zip(rings[i], rings[lo], rings[hi]):
            worst = max(worst, _point_segment_m(a, b, c))
    return worst


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
    return _chord_error_keep(rings, _stride_indices(len(rings), stride))


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


def _unstooped(ind: "Individual") -> "Individual":
    """The same resident with the stoop suppressed.

    One helper because two measurements need it and a hand-rolled copy of the
    dataclass rebuild is how one of them ends up dropping a field.
    """
    return Individual(*[0.0 if f.name == "stoop_deg" else getattr(ind, f.name)
                        for f in ind.__dataclass_fields__.values()])


def _y_rings(verts):
    """A lofted part's rings, recovered by grouping runs of equal height.

    `_rings_of` needs the ring size and gets it wrong on anything not built at
    the body's own `seg` -- a limb is `seg // 2`, so `len(verts) % seg` either
    rejects it or, worse, divides evenly and hands back three "rings" of 16
    where the part has six of 8. This groups by y instead, which is exact
    because `_ring` puts every vertex of a ring at one height, and returns None
    for anything that is not a stack of equal rings. Same construction as
    `animation._ring_partition`, which has the same job on the same meshes.
    """
    runs, start = [], 0
    for i in range(1, len(verts) + 1):
        if i == len(verts) or abs(verts[i][1] - verts[start][1]) > 1e-9:
            runs.append(verts[start:i])
            start = i
    # `len(runs[0]) < 3` is the STOOP GUARD and it is not defensive coding.
    # `_bend` rotates y as a function of z, so a pak'ma'ra's rings are not
    # flat: every vertex lands in its own run and this returns a list of
    # one-vertex "rings" that a caller will happily measure. The first run of
    # `form_schedule` did exactly that and reported 0.222 m of error on a
    # pak'ma'ra head -- a whole head-height, from a partition that had nothing
    # to do with rings. The smallest ring this module builds is 4 vertices
    # (`_small_seg`'s floor), so anything under 3 is not a ring stack.
    if (len(runs) < 2 or len(runs[0]) < 3
            or any(len(r) != len(runs[0]) for r in runs)):
        return None
    return runs


def _box_of(verts):
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _dist_to_box(p, box):
    """Distance from a point to an axis-aligned box; 0 inside it."""
    dx = max(box[0] - p[0], 0.0, p[0] - box[3])
    dy = max(box[1] - p[1], 0.0, p[1] - box[4])
    dz = max(box[2] - p[2], 0.0, p[2] - box[5])
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _cull_standoff(full, culled):
    """How far the geometry a cull REMOVES stood outside what it leaves --
    counting only the geometry the figure's own bounding box cannot see.

    THE FIGURE'S OWN BOUNDING BOX CANNOT SEE MOST OF A CULL, and that is the
    finding session 4e paid for. The figure's extremes in every axis are the
    crown, the soles and the fingertips; a nose, an ear, a thumb and a haircut
    all live strictly INSIDE that box, so removing every one of them moved the
    old measurement by exactly 0.00000 m and the schedule concluded they were
    free to drop at zero metres. `lod_chain()` duly built a chain in which the
    `all` feature level was never used at any distance -- a face that existed in
    the code and appeared in no frame. Same defect as layer 2's "mesh, closed,
    correctly wound": a criterion a defective case passes perfectly.

    So the cull is priced against the geometry that SURVIVES it. For every part
    the cull deletes, this measures how far its vertices lie outside the
    bounding boxes of the parts that remain, and takes the worst. Point-to-box
    rather than point-to-surface because a box is a superset of its part, which
    makes this a LOWER bound on the true silhouette movement -- stated because a
    conservative bound in the cheap direction is a thing a reader has to know.
    It is enough to separate a 20 mm nose from a 0 mm one, which is the entire
    job.

    EACH REMOVED VERTEX IS PRICED BY EXACTLY ONE INSTRUMENT, and the choice is
    not a preference. A vertex OUTSIDE the culled figure's bounding box has
    already moved that box, so `feature_schedule`'s bbox term prices it and
    adding a stand-off on top would double-count the same movement in a
    different, larger currency. That is not hypothetical: a Grome's toe stands
    0.146 m forward of its own shin, and pricing it here instead of by the box
    moved the `identity_only` step from 81 m to 150 m and made every figure on
    the drum floor 44% dearer -- 145,546 triangles against a 144,000 budget,
    which `npc/crowd.py`'s worst-case gate caught within one run. The box is
    the right instrument for a foot and the wrong one for a nose; so each is
    measured by the one that can see it.
    """
    kept = {n for n, _v, _t in culled.parts}
    boxes = [_box_of(v) for n, v, _t in culled.parts if v]
    if not boxes:
        return 0.0
    outline = _box_of([p for _n, v, _t in culled.parts for p in v])
    worst = 0.0
    for name, verts, _t in full.parts:
        if name in kept:
            continue
        for p in verts:
            if _dist_to_box(p, outline) > 0.0:
                continue                  # the bbox term already prices this
            worst = max(worst, min(_dist_to_box(p, b) for b in boxes))
    return worst


def feature_schedule(seg=16):
    """Attachment culling. Error is how far the SILHOUETTE moves, MEASURED.

    TWO measurements, maxed, because one of them is blind to half the culls:

      * the growth of the figure's bounding box, which prices the crests, the
        tendrils and the mantle -- everything that changes the outline; and
      * `_cull_standoff`, which prices what the box cannot see because it
        happens inside the box: the nose, the ears, the thumbs, the hair.

    Quoted per species for the worst. Both are bounds on outline movement rather
    than estimates of it, and it is the same shape of measurement as `lod.py`'s
    greeble relief.

    The result is uncomfortable and is the reason to measure rather than assume:
    the identifying features -- the crest, the tendrils, the mantle -- are large
    enough that they are not cullable inside the distance a figure is drawn as a
    mesh at all. So this schedule has exactly one useful step, and the module
    says so instead of shipping five levels that buy nothing.
    """
    ref, refm = {}, {}
    for key, sp in SPECIES.items():
        ind = individual(key, "lod-probe")
        refm[key] = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                    features="all")
        ref[key] = refm[key].bbox()
    out = []
    for level in FEATURE_STEPS:
        worst, where = 0.0, None
        for key, sp in SPECIES.items():
            ind = individual(key, "lod-probe")
            mm = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                 features=level)
            e = max(max(abs(a - b) for a, b in zip(ref[key], mm.bbox())),
                    _cull_standoff(refm[key], mm))
            if e > worst:
                worst, where = e, key
        worst = round(worst, 5)
        out.append({
            "features": level,
            "error_m": worst,
            "error_baseline": "the full attachment set",
            "error_source": ("the larger of the figure's bounding-box movement "
                             "and the stand-off of the removed geometry from "
                             "the parts that survive, over every species"
                             + (f", worst on {where}" if where else "")),
            "honest_from_m": round(honest_from_m(worst), 2),
            "feature_m": worst,
            "feature_source": "the same movement, as a feature size",
            "aliases_beyond_m": round(aliases_beyond_m(worst), 1),
        })
    return out


# WHERE THE FACE RINGS STOP, AND THE 4.5 m THIS COSTS.
# ------------------------------------------------------------------------
# `form_schedule()` measures the face tier as honest to drop at 13.4 m. It is
# dropped at 8.9 m instead -- the first level whose radial count falls to 16 --
# and the reason is both a Nyquist argument and a budget one, in that order.
#
# NYQUIST: the face tier's whole content is `zoff` windows on the front of the
# head. The narrowest that has to READ is the lip vermilion at half 24 degrees,
# so 48 degrees of arc; at seg 16 the azimuth step is 22.5 degrees, which is
# two samples across a lip and ONE across the philtrum. A ring bought to carry
# a feature the ring cannot sample is a ring bought for nothing.
#
# BUDGET: and it is the harder constraint. Carrying the face rings through
# seg 16 -- the 8.9-26.8 m band, which holds most of a busy Zocalo -- makes a
# figure 1,929 triangles instead of 1,739, and `npc/crowd.py` answered by
# moving the Zocalo's impostor swap from 51.1 m to 33.4 m, INSIDE the 36 m
# floor that module sets so "fix the overrun" can never mean "put cards on the
# people the player is talking to".
#
# WHAT IT COSTS, stated rather than absorbed: between 8.9 m and 13.4 m a figure
# carries 13.0 mm of ring error against a budget of 1.5 px, so about 2.2 px of
# deviation instead of 1.5 over a 4.5 m band. That is the compromise, it is the
# same KIND of compromise `populace.crowd_ladder` records for its near band, and
# it is the number a future budget increase would buy back.
FACE_FORM_MIN_SEG = 32


def _form_for(radial_segments, features):
    """The `FORM_STEPS` key for a level with these knobs."""
    if features != "all":
        return "none"
    return "face_and_body" if radial_segments >= FACE_FORM_MIN_SEG else "body"


def form_schedule(seg=16):
    """Landmark-ring culling. Error is the CHORD the dropped rings leave.

    THE FOURTH SCHEDULE, AND IT EXISTS FOR THE REASON THE OTHER THREE DO: a
    knob that stops being visible at its own distance needs its own distance.
    Session 4h added rings to the skull and the shoulder -- a mouth, an orbital
    rim, a deltoid roll-over -- and a ring, unlike a superellipse exponent or a
    lobe, costs triangles at every level it exists at.

    NEITHER OF THE OTHER INSTRUMENTS CAN SEE THIS CULL, which is why it is here
    and not folded into `feature_schedule`:

      * `feature_schedule` compares PART NAMES and prices what is removed
        against what survives. A head with fewer rings is the same part with
        the same name, so it scores exactly zero.
      * the figure's BOUNDING BOX does not move either -- the crown, the soles
        and the fingertips are all base geometry. That is the same blindness
        session 4e paid for with a bald corridor.

    What a dropped intermediate ring actually costs is the distance from its
    vertices to the chord joining the rings that remain, which is
    `chord_error`'s question with an arbitrary kept set. Measured over every
    species, on the parts each tier touches, and quoted for the worst.

    The two tiers come out at very different distances and that is the whole
    argument for splitting them -- see RING_TIERS.
    """
    rows = []
    for step in FORM_STEPS:
        worst, where = 0.0, None
        for key, sp in SPECIES.items():
            # UNSTOOPED, for the reason `animation.rig` builds an unstooped
            # probe: `_bend` is a graded rotation, so a stooped stack has no
            # flat rings to recover and the stoop is a POSE rather than a
            # property of the ring plan. Measuring the erect figure measures
            # the thing the schedule is about.
            ind = _unstooped(individual(key, "lod-probe"))
            full = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                   features="all", form=FORM_STEPS[0])
            cut = _PLANS[sp.plan](ind, sp, seg=seg, ring_stride=1,
                                  features="all", form=step)
            # PART FOR PART, WITH THE SURVIVING RINGS FOUND BY MATCHING, not by
            # reading a tier table a second time. A limb's rings come out of
            # `_limb_ts` rather than a profile row, so a table-driven version of
            # this would need `bulge_at` copied here -- and a second copy of a
            # number is the defect `budget.py`'s cached collision total records.
            for (n0, v0, _t0), (n1, v1, _t1) in zip(full.parts, cut.parts):
                if n0 != n1 or len(v0) == len(v1):
                    continue
                r0, r1 = _y_rings(v0), _y_rings(v1)
                if r0 is None or r1 is None or len(r0) <= len(r1):
                    continue
                kept, j = [], 0
                for i, ring in enumerate(r0):
                    if j < len(r1) and abs(ring[0][1] - r1[j][0][1]) < 1e-9:
                        kept.append(i)
                        j += 1
                if len(kept) != len(r1):
                    continue                 # not a subset: measured elsewhere
                e = _chord_error_keep(r0, kept)
                if e > worst:
                    worst, where = e, f"{key} {n0}"
        worst = round(worst, 5)
        rows.append({
            "form": step,
            "error_m": worst,
            "error_baseline": "every landmark ring built",
            "error_source": ("max distance from a dropped landmark ring's "
                             "vertex to the chord of the base rings that "
                             "remain, over every species"
                             + (f", worst at {where}" if where else "")),
            "honest_from_m": round(honest_from_m(worst), 2),
            "feature_m": worst,
            "feature_source": "the same deviation, as a feature size",
            "aliases_beyond_m": round(aliases_beyond_m(worst), 1),
        })
    return rows


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
    frm = form_schedule(seg_measure)
    imp = impostor_distance()
    # THE FORM SCHEDULE IS MEASURED AND THEN NOT GIVEN ITS OWN BOUNDARY, and
    # that is a stated compromise rather than an oversight. Its two honest
    # distances (13.4 m for the face rings, 31.6 m for the body's) do not
    # coincide with any other schedule's, so putting them in `bounds` adds two
    # levels -- and a chain that grows breaks the one thing a chain index means
    # to another module: `npc/crowd.py`'s `CROWD_LOD_OFFSET = 2` is "two levels
    # coarser", so a finer-grained chain makes the same offset save less. It
    # was measured: 12 levels took the Zocalo's impostor horizon from 51.1 m to
    # 26.1 m and the crowd offset's saving from 36% to 27%, failing three of
    # that module's gates.
    #
    # So `ring_form` is derived from the knobs the level ALREADY has -- see
    # `_form_for` -- and the schedule's job is to say what that costs, which it
    # does in `report()` and in `_detail_gate` part 5.
    bounds = sorted({0.0} | {o["honest_from_m"]
                             for s in (sil, pro, fea) for o in s
                             if 0 < o["honest_from_m"] <= SUBPIXEL_FIGURE_M})
    levels, last = [], None
    for d in bounds:
        s = _coarsest(sil, "radial_segments", d)
        p = _coarsest(pro, "ring_stride", d)
        f = _coarsest(fea, "features", d)
        r = {"form": _form_for(s["radial_segments"], f["features"])}
        combo = (s["radial_segments"], p["ring_stride"], f["features"],
                 r["form"])
        if combo == last:
            continue
        last = combo
        levels.append({
            "name": f"lod{len(levels)}",
            "kind": "mesh",
            "radial_segments": s["radial_segments"],
            "ring_stride": p["ring_stride"],
            "features": f["features"],
            "ring_form": r["form"],
            "switch_distance_m": round(d, 2),
            "honest_from_m": {"silhouette": s["honest_from_m"],
                              "profile": p["honest_from_m"],
                              "feature": f["honest_from_m"]},
            "switch_reason": ("coarsest honest option in each schedule: "
                              f"silhouette {s['honest_from_m']} m, "
                              f"profile {p['honest_from_m']} m, "
                              f"feature {f['honest_from_m']} m; "
                              f"ring form {r['form']} from seg "
                              f"{s['radial_segments']}"),
        })
    levels.append({
        "name": f"lod{len(levels)}",
        "kind": "impostor",
        "radial_segments": 8, "ring_stride": 1, "features": "identity_only",
        "ring_form": FORM_STEPS[-1],
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
# NPCs get 19% of the frame. Defended rather than asserted: interior structure
# takes 5% (budget.INTERIOR_FRAME_SHARE) and the habitat drum takes 25%
# (budget.DRUM["frame_share"]), and those two are never both in view -- a
# corridor is not the drum. So the worst simultaneous structural load is 25%,
# leaving 75% for people, props, signage, effects and whatever is through the
# windows. 19% is a quarter of that residue.
#
# RAISED FROM 0.12 IN SESSION 4e, AND IT CLOSES TWO THINGS AT ONCE.
#
# First, this file said 0.12 and `schedule.NPC_BUDGET["npc_frame_share"]` said
# 0.15 -- two committed modules, two budgets, one frame. `crowd.py` recorded
# that as finding (b) and bound at the tighter of the two on the principle that
# a budget disagreeing with itself should bind at its tightest. It is now ONE
# number in both places.
#
# Second, giving the crowd hair, a face and hands cost the corridor bake
# 484 -> 608 triangles, and at 0.15 a busy Zocalo swapped to impostor cards at
# **24.3 m** against an assertion of 36 m. `CROWD_LOD_OFFSET` cannot reach it:
# offsets 2/3/4 give 24.3/26.7/30.4 m because the whole excess is inside 18 m
# where the offset does not apply. The three options were to raise this, to
# relax the factor of two, or to go back to a bald crowd -- and a bald crowd is
# the defect that was just fixed, so the frame pays for the hair.
#
# What it buys, in the terms `crowd.py` uses: the Zocalo at 20:00 needs 17.4%
# of the frame to hold meshes across the whole room, and it now has 19%.
NPC_FRAME_SHARE = 0.19

# ONE GATE IS RED BECAUSE OF THIS FILE AND THE NEXT CONTEXT SHOULD SEE IT HERE
# RATHER THAN REDISCOVER IT. `npc/crowd.py` asserts that no place swaps a mesh
# for an impostor closer than twice the full-simulation radius -- 36 m. On a
# busy Zocalo at peak that swap now happens at **24.3 m** where it happened at
# 40.0 m before session 4e, so `crowd.py` reads 66/67 instead of 67/67.
#
# It is a budget decision and not a defect, and the arithmetic is short. The
# Zocalo's cumulative crowd cost out to 35.4 m was 135,081 triangles against a
# 144,000 budget -- an 6.6% margin -- and it is now 176,955. The whole excess is
# per-figure detail in the FULL-SIMULATION tier inside 18 m, where
# `CROWD_LOD_OFFSET` does not apply and therefore cannot pay for it: measured,
# offset 2 gives 24.3 m, offset 3 gives 26.7 m and offset 4 gives 30.4 m, so the
# crowd module's own knob cannot reach 36 m either.
#
# The three ways out, none of which is this module's to choose:
#   1. `schedule.NPC_BUDGET["npc_frame_share"]` 0.15 -> ~0.19. 180,000
#      triangles restores the 36 m horizon. The share has 75% of the frame to
#      draw on and takes a fifth of it.
#   2. Accept a 24 m mesh horizon in the single busiest room on the station and
#      relax the factor of two in `crowd.py`'s assertion, with the figure size
#      at the swap stated -- 111 px, against 129 px when it first failed.
#   3. Put the crowd back to a bald one. It is the cheapest and it is what the
#      owner objected to in session 4e.
# Measured with `crowd.visible_cost('zocalo', peak_hour('zocalo'))`.

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


# ---------------------------------------------------------------------------
# THE SKINNED EXPORT -- the same body, with bones, ALONGSIDE the baked poses
# ---------------------------------------------------------------------------
# WHY THIS IS AN ADDITION AND NOT A REPLACEMENT. `populace.crowd_library` bakes
# a pose into vertex positions and instances it through a MultiMesh, and that is
# what makes the station's whole crowd **112 draw calls**. A MultiMesh instance
# is a transform into a shared mesh: it cannot own a skeleton, so it cannot
# ragdoll. Nothing here touches that path -- `build()`, `crowd_body()` and every
# baked pose behave exactly as before. This is the SECOND form of the same body,
# for the one figure at a time that has stopped standing up.
#
# THE SKELETON AND THE WEIGHTS ALREADY EXISTED AND HAD NO EXPORT. `npc/
# animation.py` has measured joints (`_skeleton`), ring-indexed weights
# (`_bind`, `MAX_INFLUENCES = 4`) and a JSON writer for the skeleton and the
# clips -- but `binding_dict` emits weights per RING, which is the right storage
# and is not something a GPU can consume. What was missing was the expansion to
# per-VERTEX arrays and the mesh to hang them on. So this function measures
# nothing new: it reads `animation.rig()` and unrolls it.
#
# THE FRAME IS body.py's OWN, AND THAT IS DELIBERATE. `animation.emit()` applies
# a 180-degree turn about +Y on its way out (`godot_note`), because a clip
# consumer would want Godot's -Z-forward convention. `populace._place_body`
# bakes these vertices into the deck WITHOUT that turn, so every person standing
# on this station is already in the body frame, in world space, and `npc.gd`'s
# own comment says so: "at yaw 0 the body's forward is the room's +z". A
# promoted ragdoll has to land exactly where the baked body it replaces was
# standing, so it is emitted in the frame the baked body uses. The two
# conventions in this project are recorded in `skinned()['frame']` rather than
# reconciled here, because reconciling them would change what `animation.emit`
# writes and nothing consumes that yet.
SKIN_INFLUENCES = 4          # animation.MAX_INFLUENCES; asserted against it
# The stand-in identity used only when `animation.rig(NOMINAL)` cannot bind --
# see `skinned()`. A fixed string so the fallback body is deterministic.
SKIN_FALLBACK_ID = "skin-reference"


def _rings_cover(rg):
    """Does every skinned vertex belong to a ring the binding has weights for?

    `animation._bind` partitions the UNSTOOPED build and applies the runs to the
    DRESSED one by index. That is valid only while the two are the same figure,
    and `rig()` does not always make them the same figure -- so this is the
    check that notices, rather than an index error two hundred lines later.
    """
    for pi, ringw, runs in rg.binding:
        if len(ringw) != len(runs):
            return False
        if sum(b - a for a, b in runs) != len(rg.parts[pi][1]):
            return False
    return True


def _vertex_normals(verts, tris):
    """Area-weighted vertex normals, WITHIN one part.

    Per part rather than per body, so the seam between skin and a boot stays a
    hard edge and a shoulder stays smooth. A body is a set of lofts, and a loft
    is smooth along itself and discontinuous where it meets the next one --
    which is the same rule `export_gltf.build_group` states in reverse for the
    hull, where every edge is hard by design.
    """
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for ia, ib, ic in tris:
        a, b, c = verts[ia], verts[ib], verts[ic]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        # NOT normalised: the cross product's length is twice the triangle's
        # area, so accumulating it raw weights each face by its area, which is
        # what stops a fan of slivers at a ring cap out-voting the body of the
        # loft.
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        for k in (ia, ib, ic):
            acc[k][0] += nx
            acc[k][1] += ny
            acc[k][2] += nz
    out = []
    for n in acc:
        ln = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
        out.append((0.0, 1.0, 0.0) if ln < 1e-12
                   else (n[0] / ln, n[1] / ln, n[2] / ln))
    return out


def _skin_family(group):
    """The material a body group binds through, via populace's OWN rule.

    Imported rather than re-implemented. `populace._material_family` reads the
    first two tokens of a part name back off THIS file's naming, and a second
    copy of that rule here is a second answer to "which material is this" --
    hard rule 4. The import is lazy because `populace` imports this module; by
    the time anybody calls `skinned()` both are loaded.
    """
    if _STATION not in sys.path:
        sys.path.insert(0, _STATION)
    import populace as _pop                                     # noqa: PLC0415
    return _pop._material_family(group)


def _skin_part(surface, vweights, name, verts, tris):
    """Append one mesh part to a surface, with its normals and weights."""
    base = len(surface["positions"]) // 3
    nrm = _vertex_normals(verts, tris)
    for i, v in enumerate(verts):
        surface["positions"].extend((round(v[0], 5), round(v[1], 5),
                                     round(v[2], 5)))
        surface["normals"].extend((round(nrm[i][0], 4), round(nrm[i][1], 4),
                                   round(nrm[i][2], 4)))
        pairs = list(vweights[i])[:SKIN_INFLUENCES]
        tot = sum(w for _b, w in pairs) or 1.0
        pairs = [(b, w / tot) for b, w in pairs]
        while len(pairs) < SKIN_INFLUENCES:
            pairs.append((pairs[0][0], 0.0))
        surface["bones"].extend(int(b) for b, _w in pairs)
        surface["weights"].extend(round(w, 5) for _b, w in pairs)
    for a, b, c in tris:
        surface["indices"].extend((a + base, b + base, c + base))
    surface["parts"].append(name)


def skinned(species: str, npc_id: str = None, lod: int = 0):
    """The rest-pose mesh with a skeleton and per-vertex bone weights.

    Returns a dict: bones (name, parent, rest head and tail), and one SURFACE
    per material -- positions, normals, four bone indices and four weights per
    vertex, and a triangle index list. That is exactly the shape of a Godot
    `ArrayMesh` with `ARRAY_BONES`/`ARRAY_WEIGHTS`, and of a glTF skin.

    ONE SURFACE PER MATERIAL, NOT ONE PER PART, and the reason is a draw call.
    `populace._by_material` records that a human at lod 4 was twelve primitives
    and merges the runs to one; this does the same merge on the same rule, so a
    promoted body costs what `_by_material` says a baked one costs and the
    ragdoll budget can be derived from a number that already exists.
    """
    if _STATION not in sys.path:
        sys.path.insert(0, _STATION)
    sys.path.insert(0, _HERE) if _HERE not in sys.path else None
    import animation as _anim                                   # noqa: PLC0415
    if _anim.MAX_INFLUENCES != SKIN_INFLUENCES:
        raise ValueError(
            f"animation.MAX_INFLUENCES is {_anim.MAX_INFLUENCES} and this "
            f"exporter writes {SKIN_INFLUENCES}; a fifth influence per vertex "
            f"is a format change, not a constant")
    # THE UN-JITTERED MEMBER OF THE SPECIES, and it has to be spelled
    # `animation.NOMINAL` rather than "nominal": `rig()` compares the id against
    # that sentinel and hands anything else to `body.individual()`, so passing
    # the word built a RANDOM person and called it the species mean. Caught by
    # this file's own vertex counts moving between two runs that should have
    # been identical.
    npc_id = _anim.NOMINAL if npc_id is None else npc_id
    rg = _anim.rig(species, npc_id, lod)
    if npc_id == _anim.NOMINAL and not _rings_cover(rg):
        # `animation.rig()` BINDS TWO DIFFERENT PEOPLE WHEN THE ID IS `NOMINAL`,
        # and this is the fallback that keeps every species shipping until it is
        # patched. The skeleton is measured off `body.nominal(species)`; the
        # mesh that gets skinned is
        #     _cos.dressed_mesh(species, npc_id, lod=lod, chain=chain)
        # which resolves its own figure through `body.individual(species,
        # npc_id)` -- so with npc_id == "__nominal__" it dresses a RANDOM draw.
        # On thirteen species the two happen to have the same vertex counts and
        # the binding is merely computed from the wrong person's ring radii; on
        # the Vree they diverge outright (stature 1.4833/build 0.7831 against
        # the nominal 1.5000/0.7200 -> a 24-vertex finger bound to an 18-vertex
        # one) and the partition stops covering the mesh.
        #
        # The one-argument fix belongs in `animation.rig` -- pass `ind=ind` to
        # `dressed_mesh`, which `_build_mesh` already accepts for exactly this
        # reason. Until then, asking for a CONCRETE id makes both builds resolve
        # the same individual, so the figure is one draw from the species rather
        # than its mean. SAID OUT LOUD on every run that uses it: a tool that
        # substitutes a lesser mode has to report which one it used.
        print(f"body.skinned: {species}: animation.rig(NOMINAL) bound two "
              f"different figures; falling back to the concrete reference id "
              f"{SKIN_FALLBACK_ID!r} (one draw, not the species mean). Patch "
              f"animation.rig to pass ind= to dressed_mesh.", file=sys.stderr)
        npc_id = SKIN_FALLBACK_ID
        rg = _anim.rig(species, npc_id, lod)
        if not _rings_cover(rg):
            raise ValueError(
                f"{species}: the ring partition does not cover the skinned "
                f"mesh even with a concrete id -- this is not the NOMINAL bug")

    # Ring weights -> vertex weights. `_bind` stores one weight list per RING
    # because the ring plan is a property of the species and not of the person;
    # unrolling it here is the only place the per-vertex form is ever built.
    per_vertex = [None] * len(rg.parts)
    for pi, ringw, runs in rg.binding:
        w = [None] * len(rg.parts[pi][1])
        for (a, b), ring in zip(runs, ringw):
            for i in range(a, b):
                w[i] = ring
        if any(x is None for x in w):
            raise ValueError(
                f"part {rg.parts[pi][0]!r} has vertices outside every ring; "
                f"`_ring_partition` and the mesh disagree")
        per_vertex[pi] = w

    # ONE SURFACE PER MATERIAL FAMILY, AND THE PARTS ARE REORDERED TO GET IT.
    # `populace._by_material` merges only ADJACENT runs, and it says why: a
    # baked body's triangles live inside a room's merged mesh, where the spans
    # of everything else are already written against those offsets, so moving a
    # triangle moves somebody else's span. Measured on this figure that rule
    # gives **twelve** surfaces at lod 0, because the parts interleave --
    # cloth arm, skin hand, cloth arm, skin hand -- and twelve draw calls for
    # one person is most of `schedule.NPC_BUDGET["max_draw_calls"]`.
    #
    # A PROMOTED BODY IS ITS OWN MESH AND HAS NO SUCH NEIGHBOURS. Nothing
    # downstream indexes into it, so the parts can be gathered by family first,
    # which gives FOUR surfaces on a dressed human -- skin, cloth, boot leather,
    # hair. That is the whole difference between the two paths and it is why
    # the merge is done here rather than by calling `_by_material`.
    order, groups = [], {}
    for pi in range(len(rg.parts)):
        fam = _skin_family(rg.groups[pi]) if rg.groups[pi] else "npc_body"
        if fam not in groups:
            groups[fam] = []
            order.append(fam)
        groups[fam].append(pi)
    surfaces = []
    for fam in order:
        surfaces.append({"group": fam, "positions": [], "normals": [],
                         "bones": [], "weights": [], "indices": [],
                         "parts": []})
        for pi in groups[fam]:
            name, verts, tris = rg.parts[pi]
            _skin_part(surfaces[-1], per_vertex[pi], name, verts, tris)
    del order, groups

    bones = [{"name": b.name, "parent": b.parent,
              "rest_head": [round(x, 6) for x in b.head],
              "rest_tail": [round(x, 6) for x in b.tail]}
             for b in rg.skel.bones]
    return {
        "generator": "station/npc/body.py::skinned",
        "species": species, "npc_id": npc_id, "lod": lod,
        "nominal": npc_id == _anim.NOMINAL,
        "plan": rg.skel.plan,
        # STATED, because two frames exist in this project and only one of them
        # is what the station is built in. See the section header.
        "frame": "body.py: +Z forward, +Y up, +X the figure's LEFT -- the frame "
                 "populace._place_body bakes into the deck, NOT the 180-degree "
                 "turn animation.emit() applies",
        "stature_m": rg.skel.stature_m,
        "ground_y": rg.skel.ground_y,
        "com_height_m": rg.skel.com_height_m,
        "leg_length_m": rg.skel.leg_length_m,
        "influences": SKIN_INFLUENCES,
        "bones": bones,
        "surfaces": surfaces,
        "vertices": sum(len(s["positions"]) // 3 for s in surfaces),
        "triangles": sum(len(s["indices"]) // 3 for s in surfaces),
    }


def write_skinned(path, doc):
    """The skinned body as JSON. Text, per ADR 0001."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(doc, f, separators=(",", ":"), sort_keys=True)
    return path, os.path.getsize(path)


def skin_selftest(species="human", out=print):
    """The skinned mesh IS the baked mesh, vertex for vertex.

    THE ASSERTION THAT MAKES THIS EXPORT WORTH ANYTHING. A skinned body and a
    baked body are two builds of one figure -- CLAUDE.md's session-4h lesson,
    one level down -- so the only thing that can show they have not drifted is
    reproducing one from the other. In the rest pose every skinning matrix is
    the identity (`animation.rest_offsets`: rest rotations are identity, so a
    bone's rest transform is a pure translation to its head), which makes the
    check exact rather than approximate: the skinned surfaces, concatenated in
    emission order, must equal `rig().parts` to the export's own rounding.

    Returns (ok, fail).
    """
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            out(f"FAIL: {label}")

    if _STATION not in sys.path:
        sys.path.insert(0, _STATION)
    import animation as _anim                                   # noqa: PLC0415
    doc = skinned(species, "nominal", 0)
    rg = _anim.rig(species, "nominal", 0)

    # THE PARTS ARE REORDERED BY MATERIAL, so the comparison is rebuilt part by
    # part rather than by concatenating both lists and hoping the order agrees.
    # Each surface names the parts it swallowed, in order; taking the next
    # unconsumed rig part of that name reproduces the emission exactly, and it
    # is the ONLY thing that would notice a part being dropped or duplicated.
    pool = {}
    for pi, (nm, vs, _t) in enumerate(rg.parts):
        pool.setdefault(nm, []).append(vs)
    flat, want = [], []
    for srf in doc["surfaces"]:
        pos = srf["positions"]
        flat.extend((pos[i], pos[i + 1], pos[i + 2])
                    for i in range(0, len(pos), 3))
        for nm in srf["parts"]:
            want.extend(pool[nm].pop(0))
    check(not any(pool.values()),
          f"{sum(len(v) for v in pool.values())} rig parts were never emitted "
          f"into any surface")
    check(len(flat) == len(want),
          f"skinned() emits {len(flat)} vertices, the rig has {len(want)}")
    worst = 0.0
    for a, b in zip(flat, want):
        worst = max(worst, max(abs(a[k] - b[k]) for k in range(3)))
    check(worst <= 1e-5 + 1e-12,
          f"the skinned mesh differs from the built body by {worst * 1000:.4f} "
          f"mm; rounding is 1e-5 m so anything above 10 microns is drift")

    ntri = sum(len(s["indices"]) // 3 for s in doc["surfaces"])
    check(ntri == sum(len(t) for _n, _v, t in rg.parts),
          f"{ntri} triangles skinned against {sum(len(t) for _n, _v, t in rg.parts)} built")

    # Weights: four per vertex, summing to one, and every index a real bone.
    nb = len(doc["bones"])
    bad_sum = bad_idx = 0
    for s in doc["surfaces"]:
        w, b = s["weights"], s["bones"]
        for i in range(0, len(w), SKIN_INFLUENCES):
            if abs(sum(w[i:i + SKIN_INFLUENCES]) - 1.0) > 2e-4:
                bad_sum += 1
        bad_idx += sum(1 for x in b if not (0 <= x < nb))
    check(bad_sum == 0, f"{bad_sum} vertices whose four weights do not sum to 1")
    check(bad_idx == 0, f"{bad_idx} bone indices outside the skeleton")

    # NEGATIVE CONTROL: a mesh skinned to the WRONG ring order must fail the
    # reproduction check above. Without this the check could be passing because
    # both sides read the same list.
    shifted = [flat[(i + 1) % len(flat)] for i in range(len(flat))]
    moved = max(max(abs(a[k] - b[k]) for k in range(3))
                for a, b in zip(shifted, want))
    check(moved > 1e-3,
          f"CONTROL: rotating the vertex list by one moves it {moved * 1000:.2f} "
          f"mm -- if this were small the reproduction check would be vacuous")

    # NORMALS point out of the body: the mean dot of a normal with the ray from
    # the part centroid must be positive, or the winding is inside out and every
    # promoted body renders as a hole.
    inward = 0
    for s in doc["surfaces"]:
        p, n = s["positions"], s["normals"]
        cnt = len(p) // 3
        cx = sum(p[0::3]) / cnt
        cy = sum(p[1::3]) / cnt
        cz = sum(p[2::3]) / cnt
        dot = 0.0
        for i in range(cnt):
            dot += ((p[3 * i] - cx) * n[3 * i] + (p[3 * i + 1] - cy) * n[3 * i + 1]
                    + (p[3 * i + 2] - cz) * n[3 * i + 2])
        if dot <= 0.0:
            inward += 1
    check(inward == 0,
          f"{inward} of {len(doc['surfaces'])} surfaces have normals pointing "
          f"into the body")
    return ok, fail


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
                      "m", 0, 0, sp.features,
                      # The commonest male cut, so the nominal figure is the
                      # modal resident rather than a draw. `_selftest` asserts
                      # this is a real key.
                      "crop" if "hair" in sp.features else "")


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
                            ("FEATURE", feature_schedule(), "features"),
                            ("RING FORM", form_schedule(), "form")):
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
        f"{'ring form':>14} {'from':>10} {'to':>10} {'tri min':>9} "
        f"{'tri max':>9} {'mix mean':>9}")
    for lv, t in zip(chain, tri):
        out(f"  {lv['name']:6} {lv['kind']:10} {lv['radial_segments']:>5} "
            f"{lv['ring_stride']:>7} {lv['features']:>14} "
            f"{lv['ring_form']:>14} "
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
# The silhouette gate: what a head, a hand and a haircut are actually worth
# ---------------------------------------------------------------------------
def silhouette_raster(verts, tris, nx=64, ny=128, axis=0, span=None):
    """A FILLED silhouette bitmap of a figure, normalised to its own height.

    Filled, not a vertex splat: a vertex cloud of two different bodies overlaps
    almost nowhere and reports a difference that is really a sampling artefact,
    which is what the first version of this measured and why it is written down.
    Scanline-filled per triangle, which is exact for the coverage question.

    Normalised by the figure's OWN height so this compares SHAPE. Stature is a
    real difference between species and it is asserted separately -- folding it
    in here would let a tall human pass as a Narn's silhouette test.

    `axis` picks the projected horizontal: 0 is x (front view), 2 is z (side).
    """
    ys = [p[1] for p in verts]
    y0, y1 = min(ys), max(ys)
    h = max(y1 - y0, 1e-9)
    cx = (min(p[axis] for p in verts) + max(p[axis] for p in verts)) / 2.0
    w = span if span is not None else 0.75          # of a stature, half-width
    grid = bytearray(nx * ny)

    def to_px(p):
        return (((p[axis] - cx) / h / (2.0 * w) + 0.5) * nx,
                (p[1] - y0) / h * ny)

    for (a, b, c) in tris:
        pa, pb, pc = to_px(verts[a]), to_px(verts[b]), to_px(verts[c])
        lo = max(0, int(math.floor(min(pa[1], pb[1], pc[1]))))
        hi = min(ny - 1, int(math.ceil(max(pa[1], pb[1], pc[1]))))
        for row in range(lo, hi + 1):
            yc = row + 0.5
            xs = []
            for (p, q) in ((pa, pb), (pb, pc), (pc, pa)):
                if (p[1] <= yc < q[1]) or (q[1] <= yc < p[1]):
                    f = (yc - p[1]) / (q[1] - p[1])
                    xs.append(p[0] + (q[0] - p[0]) * f)
            if len(xs) < 2:
                continue
            xs.sort()
            x0 = max(0, int(math.floor(xs[0] + 0.5)))
            x1 = min(nx - 1, int(math.ceil(xs[-1] - 0.5)))
            base = row * nx
            for col in range(x0, x1 + 1):
                grid[base + col] = 1
    return grid, nx, ny


def silhouette_iou(g1, g2, lo_row=0, hi_row=None):
    """Intersection over union of two rasters, optionally over a row band."""
    (a, nx, ny), (b, _nx, _ny) = g1, g2
    hi_row = ny if hi_row is None else hi_row
    inter = union = 0
    for r in range(lo_row, hi_row):
        base = r * nx
        for c in range(nx):
            x, y = a[base + c], b[base + c]
            if x or y:
                union += 1
                if x and y:
                    inter += 1
    return inter / max(1, union)


# Every pair of these four must differ by more than this in the head band --
# the top fifth of the figure, where a crest, a cranium and a haircut live --
# in the VIEW THEY DIFFER MOST IN, front or side.
#
# 0.90 is the worst measured pair with a margin, not a target: human vs Narn
# reads 0.832 and is the closest of the six, because a Narn's identity in the
# reference is a spotted, reticulated crown -- a texture -- and not a shape.
# The two controls below are what make the number mean anything: four bodies
# built from ONE parameter block read 1.000 and fail this ceiling, and taking
# the Centauri's crest away moves that pair from 0.634 to 0.848.
# 0.86, and the derivation is the point rather than the number. The comment
# here used to say "0.90 is the worst measured pair with a margin" -- and with
# the head band rasterised five pixels wide (see HEAD_BAND_SPAN) that margin was
# 0.088 of a five-pixel shape, which is to say it was nothing. A mutation sweep
# caught it: shrinking the MINBARI crest to zero leaves that pair at 0.887 and
# the ceiling passed it. The worst pair that really exists is human vs Narn at
# 0.812 -- a Narn's identity in the reference is a spotted crown, a texture, and
# the module says so -- so 0.86 leaves 4.8 points of margin AND sits below the
# 0.887 a crestless Minbari reads, which means the ceiling itself now catches an
# identity feature that has silently gone. Three controls below check the same
# thing from the other side.
SPECIES_HEAD_IOU_MAX = 0.86
GATE_SPECIES = ("human", "centauri", "minbari", "narn")
# The attachment each of these carries that IS its silhouette, for the strip
# control. The Narn is deliberately absent and that is a recorded finding, not
# an omission: stripping its brow moves the pair by 0.000 (INV-4G-004).
IDENTITY_FEATURE = {"centauri": "centauri_crest", "minbari": "minbari_crest"}

# ---------------------------------------------------------------------------
# AND THE HEAD BAND WAS BEING RASTERISED FIVE PIXELS WIDE. Session 4h, found
# while checking that a rebuilt skull had not moved these numbers.
# ---------------------------------------------------------------------------
# `silhouette_raster`'s default span is 0.75 of a stature EITHER SIDE, because
# it is sized for a whole figure with its arms out. A head is 0.048 of a
# stature to the side, so on the 64-column grid the head band came out **3 to
# 13 columns across**, and the pair scores were quantised to about a fifth of a
# head. That is enough to separate a Minbari crest from a human skull and not
# nearly enough to say anything about a jaw: rebuilding the face moved human vs
# Narn from 0.875 to 0.911 in the front view and the entire move was ONE PIXEL
# of a five-pixel shape. Measured at a span that fits a head, the same pair
# reads 0.881 before and 0.884 after -- the "regression" does not exist.
#
# `HEAD_BAND_SPAN` is DERIVED, not chosen: the widest head band on the four
# gate species is a Narn's at 0.1288 of its own height, so 0.14 clears it with
# 9% of margin and `_detail_gate` asserts no species touches the raster edge --
# a clipped silhouette would score two different heads as identical at the
# clip. 192 columns then put a head at 161 of them.
HEAD_BAND_SPAN = 0.14
HEAD_BAND_NX = 192
HEAD_BAND_NY = 384


def _detail_gate(check, quiet=False, out=print):
    """The four questions session 4g's silhouette work has to answer.

    Run from `_selftest`, and printable on its own with `--silhouette`, because
    the numbers are the deliverable and a number nobody prints is a number the
    next context re-derives. Each part carries a NEGATIVE CONTROL that
    constructs the defect and confirms the check rejects it -- AAA-STANDARD
    ROBUSTNESS 4, and the reason is in this repository's own history: three
    assertions here scored a defect as passing because the defective case was
    never built.
    """
    say = (lambda *_a, **_k: None) if quiet else out
    chain = lod_chain()

    # -- 1. triangles per body per level, and the draw-call merge ----------
    say("\nTRIANGLES PER BODY, and the merge that keeps a deck under "
        f"{600} primitives")
    try:
        sys.path.insert(0, _STATION)
        import populace as _pop                                 # noqa: PLC0415
        merge = _pop._by_material
    except Exception as exc:                                    # noqa: BLE001
        check(False, f"populace._by_material not importable: {exc}")
        merge = None
    if merge is not None:
        say(f"  {'level':6} {'segs':>5} {'features':>14} {'tri':>7} "
            f"{'spans':>6} {'merged':>7}")
        worst_merged, worst_where = 0, None
        for i, lv in enumerate(chain):
            v, t, s = build("human", "merge-probe", i, chain)
            mg = merge(s)
            say(f"  {lv['name']:6} {lv['radial_segments']:>5} "
                f"{lv['features']:>14} {len(t):>7,} {len(s):>6} {len(mg):>7}")
        # EVERY SPECIES, not the one I happened to look at. A Narn's brow and a
        # Minbari's crest are skin and bone; if the dark face parts were
        # emitted before them the run would split on exactly the species this
        # loop would otherwise never build.
        for key, sp in SPECIES.items():
            for i, lv in enumerate(chain):
                if lv["kind"] != "mesh":
                    continue
                m = _PLANS[sp.plan](individual(key, "merge-probe"), sp,
                                    seg=lv["radial_segments"],
                                    ring_stride=lv["ring_stride"],
                                    features=lv["features"])
                n = len(merge(m.spans))
                if n > worst_merged:
                    worst_merged, worst_where = n, f"{key}/{lv['name']}"
        # PINNED, NOT BOUNDED, and the difference matters this session. A "<= 3"
        # ceiling passes a change that quietly takes every human from 2 runs to
        # 3, which on a deck of 147 people is 147 draw calls against
        # `budget.BUDGETS["deck_primitives"] = 600`. Session 4h rebuilt the
        # skull and the shoulder and had to be able to say the merge did not
        # move, so the number is the number.
        BARE_MERGE_RUNS = 3          # a Minbari: skin, crest, hair
        check(worst_merged == BARE_MERGE_RUNS,
              f"a bare body merges to EXACTLY {BARE_MERGE_RUNS} material runs "
              f"at the worst level of the worst species (got {worst_merged} on "
              f"{worst_where}) -- the new parts are emitted adjacent to a part "
              f"of their own material, not in the middle of another")
        _human_runs = max(
            len(merge(_PLANS["humanoid"](individual("human", "merge-probe"),
                                         SPECIES["human"],
                                         seg=lv["radial_segments"],
                                         ring_stride=lv["ring_stride"],
                                         features=lv["features"]).spans))
            for lv in chain if lv["kind"] == "mesh")
        check(_human_runs == 2,
              f"and a bare HUMAN is exactly 2 at every level -- skin and hair "
              f"(got {_human_runs})")
        # THE CONTROL. Emit the same spans with the dark face parts moved next
        # to the nose, which is where they would naturally have gone, and the
        # merge has to grow. If it does not, this check is measuring nothing.
        _v, _t, sp_ok = build("human", "merge-probe", 0, chain)
        moved, dark = [], []
        for nm, lo, hi in sp_ok:
            (dark if nm == "npc_hair" else moved).append((nm, lo, hi))
        cut = next(i for i, (nm, _l, _h) in enumerate(moved)
                   if nm.endswith("_nose"))
        bad = moved[:cut + 1] + dark + moved[cut + 1:]
        check(len(merge(bad)) > len(merge(sp_ok)),
              f"MUTATION: emitting the eyes and brows beside the nose instead "
              f"of beside the hair splits the skin run -- "
              f"{len(merge(sp_ok))} runs becomes {len(merge(bad))}")
        # And the level the corridor is actually baked at, dressed, which is
        # the number `budget.BUDGETS['deck_primitives']` is spent in.
        try:
            import npc.costume as _cos                          # noqa: PLC0415
            bake = min(range(len(chain)),
                       key=lambda i: abs(len(build("human", "bp", i, chain)[1])
                                         - 600))
            dv, dt, ds = _cos.build_dressed("human", "merge-probe",
                                            lod=bake)[:3]
            say(f"  dressed at the corridor bake level ({chain[bake]['name']}): "
                f"{len(dt):,} tri, {len(ds)} spans, {len(merge(ds))} merged")
            check(len(merge(ds)) == 12,
                  f"a DRESSED body at the bake level is EXACTLY 12 primitives "
                  f"(got {len(merge(ds))}) -- pinned rather than bounded, so a "
                  f"change that costs a deck 147 draw calls cannot pass")
        except Exception as exc:                                # noqa: BLE001
            check(False, f"costume.build_dressed not usable here: {exc}")

    # -- 2. every part is tagged and resolves to a material that exists ----
    say("\nMATERIAL COVERAGE of every group any body can emit")
    groups = set()
    for key, sp in SPECIES.items():
        for lv in chain:
            if lv["kind"] != "mesh":
                continue
            m = _PLANS[sp.plan](individual(key, "tag-probe"), sp,
                                seg=lv["radial_segments"],
                                ring_stride=lv["ring_stride"],
                                features=lv["features"])
            check(all(g for g, _l, _h in m.spans),
                  f"{key}/{lv['name']}: every span carries a group name")
            check(len(m.spans) == len(m.parts),
                  f"{key}/{lv['name']}: every emitted part is tagged "
                  f"({len(m.spans)} spans against {len(m.parts)} parts)")
            groups.update(g for g, _l, _h in m.spans)
    groups.add("npc_impostor")
    try:
        sys.path.insert(0, _STATION)
        import materials as _mat                                # noqa: PLC0415
        unbound = sorted(g for g in groups if _mat.resolve_any(g) is None)
        say(f"  {len(groups)} distinct groups, {len(unbound)} unbound "
            f"{unbound if unbound else ''}")
        # DECLARED, WITH A REASON, WHICH IS NOT THE SAME AS IGNORED.
        # `npc_impostor` is the only group on this station a body can emit that
        # `materials.py` does not bind, and it is latent rather than shipped:
        # `lod9` is the impostor card, nothing outside this file references the
        # name, and no exporter reaches that level -- `populace.crowd_ladder()`
        # stops at lod8. It is still a real hole and it is reported rather than
        # papered over: the day the runtime starts drawing cards, every figure
        # past 272 m lands on the fallback. Fixing it needs a `npc_impostor`
        # entry in `materials.py`, which this module does not own. The
        # assertion is EXACTLY this list, so a NEW unbound group fails.
        check(unbound == ["npc_impostor"] or not unbound,
              f"every group a body emits resolves to a material, except the "
              f"declared impostor card ({unbound})")
        check(_mat.resolve_any("npc_eyeball_no_such_material") is None,
              "MUTATION: an invented group name resolves to nothing, so the "
              "check above is capable of failing")
        # And the dressed groups, which are the ones that actually ship.
        try:
            import npc.costume as _cos2                         # noqa: PLC0415
            dg = set()
            for key in SPECIES:
                for lod in (0, 2, 4):
                    dg.update(g for g, _l, _h
                              in _cos2.build_dressed(key, "tag-probe",
                                                     lod=lod)[2])
            du = sorted(g for g in dg if _mat.resolve_any(g) is None)
            say(f"  {len(dg)} distinct DRESSED groups, {len(du)} unbound")
            check(not du, f"every dressed group resolves too ({du})")
            check(_mat.resolve_any("npc_hair") is _mat.resolve_any("npc_crest"),
                  "eyes, brows, hair and crests share one measured material")
        except Exception as exc:                                # noqa: BLE001
            check(False, f"dressed material coverage not runnable: {exc}")
    except Exception as exc:                                    # noqa: BLE001
        check(False, f"materials.py not importable for the tag gate: {exc}")

    # -- 3. closure, measured by the station's own instrument ---------------
    say("\nCLOSURE, via interior.boundary_edges")
    try:
        sys.path.insert(0, _STATION)
        import interior as _int                                 # noqa: PLC0415
        # IT RETURNS TWO LISTS, NOT TWO COUNTS, and `interior`'s own docstring
        # warns that mis-reading the shape of this return is a mistake made
        # here before. Written out so the next reader sees the len().
        worst = 0
        for key, sp in SPECIES.items():
            for lv in chain:
                if lv["kind"] != "mesh":
                    continue
                v, t, _s = _PLANS[sp.plan](
                    individual(key, "closure-probe"), sp,
                    seg=lv["radial_segments"], ring_stride=lv["ring_stride"],
                    features=lv["features"]).as_tuple()
                op, nmf = _int.boundary_edges(v, t)
                worst = max(worst, len(op) + len(nmf))
                check(not op and not nmf,
                      f"{key}/{lv['name']}: interior.boundary_edges reads "
                      f"{len(op)} open / {len(nmf)} non-manifold")
        say(f"  {len(SPECIES)} species x {len(chain) - 1} mesh levels, worst "
            f"open+non-manifold edge count {worst}")
        v, t, _s = build("human", "closure-probe", 0, chain)
        holed = len(_int.boundary_edges(v, t[:-2])[0])
        check(holed > 0,
              f"MUTATION: deleting two triangles from a body makes "
              f"interior.boundary_edges report {holed} open edges")
        # AND THE MUTATION FOR THE CLASS `edge_census` CANNOT SEE, because that
        # is the whole reason this gate uses the other instrument. Two capped
        # shells sharing one ring EXACTLY -- which is what every foot and Kosh's
        # yoke were until session 4g -- give one disc four triangles per edge.
        # `edge_census` keys on vertex INDEX, so the two caps are different
        # indices and it reads (0, 0); `interior.boundary_edges` keys on
        # POSITION and sees it at once. Constructed here rather than trusted,
        # so the difference between the two instruments is a measurement.
        _r = [_ring(0, 0, 0, 0.2, 0.2, 8), _ring(0, 0.4, 0, 0.2, 0.2, 8)]
        _u = [_ring(0, 0.4, 0, 0.2, 0.2, 8), _ring(0, 0.8, 0, 0.2, 0.2, 8)]
        _sv, _st = _loft(_r)
        _uv, _ut = _loft(_u)
        _cv = list(_sv) + list(_uv)
        _ct = list(_st) + [(a + len(_sv), b + len(_sv), c + len(_sv))
                           for a, b, c in _ut]
        _idx = edge_census(_ct)
        _pos = _int.boundary_edges(_cv, _ct)
        check(_idx == (0, 0) and len(_pos[1]) > 0,
              f"MUTATION: two shells sharing a ring read {_idx} to edge_census "
              f"and {len(_pos[0])} open / {len(_pos[1])} non-manifold to "
              f"interior.boundary_edges -- the class the index-keyed check is "
              f"blind to, and the reason this gate uses the other one")
    except Exception as exc:                                    # noqa: BLE001
        check(False, f"interior.boundary_edges not usable here: {exc}")

    # -- 4. four species, four silhouettes ---------------------------------
    # AT THE LEVEL THE CROWD IS BAKED AT, not at lod0. A difference that only
    # exists on the hero mesh is a difference nobody sees.
    bake = min(range(len(chain)),
               key=lambda i: abs(len(build("human", "bp", i, chain)[1]) - 600))
    say(f"\nSPECIES SILHOUETTE at {chain[bake]['name']}, head band = the top "
        f"fifth of the figure")
    # FRONT AND SIDE, and the second view is not decoration. A front-view
    # outline cannot see a brow ridge, a nose, an occiput or a pak'ma'ra's
    # tendrils, because every one of them projects fore-aft -- which is the
    # same blindness `_cull_standoff` exists to fix in the feature schedule.
    # Measured from one view a Narn and a human are 87.5% the same picture and
    # the difference that matters is entirely in the other one. The pair's
    # score is the view they differ MOST in: two bodies differ if there is any
    # angle a player can tell them apart from.
    rast, head = {}, {}
    for key in GATE_SPECIES:
        v, t, _s = build(key, "sil-probe", bake, chain)
        rast[key] = (silhouette_raster(v, t, axis=0),
                     silhouette_raster(v, t, axis=2))
        # THE HEAD BAND GETS ITS OWN RASTER, at its own span. See
        # HEAD_BAND_SPAN: on the figure-wide grid a head was 5 columns across
        # and every pair score was quantised to a fifth of a head.
        head[key] = (silhouette_raster(v, t, nx=HEAD_BAND_NX, ny=HEAD_BAND_NY,
                                       axis=0, span=HEAD_BAND_SPAN),
                     silhouette_raster(v, t, nx=HEAD_BAND_NX, ny=HEAD_BAND_NY,
                                       axis=2, span=HEAD_BAND_SPAN))
    ny = rast["human"][0][2]
    band = int(ny * 0.80)
    hband = int(HEAD_BAND_NY * 0.80)
    # AND THE SPAN MUST NOT CLIP, or two different heads score identical at the
    # edge of the grid. Asserted per species and per view rather than assumed
    # from the one number that was measured to choose it.
    clipped = []
    for key in GATE_SPECIES:
        for k, g in enumerate(head[key]):
            grid, nx_, ny_ = g
            for r in range(hband, ny_):
                if grid[r * nx_] or grid[r * nx_ + nx_ - 1]:
                    clipped.append(f"{key}/{'front' if k == 0 else 'side'}")
                    break
    check(not clipped,
          f"no species' head band reaches the edge of its own raster at span "
          f"{HEAD_BAND_SPAN} -- a clipped silhouette scores two heads the same "
          f"({sorted(set(clipped))})")
    _hw_px = max(sum(1 for c in range(HEAD_BAND_NX)
                     if head["human"][0][0][r * HEAD_BAND_NX + c])
                 for r in range(hband, HEAD_BAND_NY))
    check(_hw_px > 100,
          f"and a head is {_hw_px} of {HEAD_BAND_NX} columns across, not the "
          f"5 the figure-wide grid gave it")
    say(f"  a head is {_hw_px} px across on the head-band raster "
        f"(it was 5 on the figure-wide one)")
    say(f"  {'pair':24} {'front':>7} {'side':>7} {'head F':>7} {'head S':>7}")
    worst_pair, worst_iou = None, 0.0
    for i, a in enumerate(GATE_SPECIES):
        for b in GATE_SPECIES[i + 1:]:
            wf = silhouette_iou(rast[a][0], rast[b][0])
            ws = silhouette_iou(rast[a][1], rast[b][1])
            hf = silhouette_iou(head[a][0], head[b][0], lo_row=hband)
            hs = silhouette_iou(head[a][1], head[b][1], lo_row=hband)
            say(f"  {a + ' vs ' + b:24} {wf:>7.3f} {ws:>7.3f} "
                f"{hf:>7.3f} {hs:>7.3f}")
            if min(hf, hs) > worst_iou:
                worst_pair, worst_iou = (a, b), min(hf, hs)
    check(worst_iou <= SPECIES_HEAD_IOU_MAX,
          f"every pair of {GATE_SPECIES} differs in the head band "
          f"(worst {worst_pair} at IoU {worst_iou:.3f} against a "
          f"{SPECIES_HEAD_IOU_MAX} ceiling)")
    # CONTROL A: the measurement must return 1.000 for a figure against itself,
    # or the numbers above are noise rather than difference.
    check(abs(silhouette_iou(head["human"][0], head["human"][0], lo_row=hband)
              - 1.0) < 1e-12,
          "a figure against itself reads IoU 1.000")
    # CONTROL B: take EVERY crest away, one species at a time, and each pair
    # has to collapse toward a human. It was the Centauri alone and a mutation
    # sweep found the hole: shrinking the MINBARI crest to nothing left the
    # gate green, because no control built that case and the ceiling was loose
    # enough to pass it. A control that covers one instance of a class is the
    # defect AAA-STANDARD's ROBUSTNESS 2 describes.
    caught_by_ceiling = set()
    for key, feat in IDENTITY_FEATURE.items():
        spc = SPECIES[key]
        ind = individual(key, "sil-probe")
        bare = Individual(*[getattr(ind, f.name) if f.name != "features"
                            else tuple(x for x in ind.features
                                       if x not in (feat, "hair"))
                            for f in ind.__dataclass_fields__.values()])
        bv, bt, _bs = _PLANS[spc.plan](
            bare, spc, seg=chain[bake]["radial_segments"],
            ring_stride=chain[bake]["ring_stride"],
            features=chain[bake]["features"],
            form=chain[bake]["ring_form"]).as_tuple()
        bare_iou = min(silhouette_iou(silhouette_raster(
                                          bv, bt, nx=HEAD_BAND_NX,
                                          ny=HEAD_BAND_NY, axis=ax,
                                          span=HEAD_BAND_SPAN),
                                      head["human"][k], lo_row=hband)
                       for k, ax in enumerate((0, 2)))
        with_iou = min(silhouette_iou(head[key][k], head["human"][k],
                                      lo_row=hband) for k in (0, 1))
        say(f"  CONTROL  {key} without its {feat} vs human: {bare_iou:.3f} "
            f"(with it: {with_iou:.3f})")
        check(bare_iou > with_iou + 0.05,
              f"MUTATION: stripping the {key} {feat} moves its head "
              f"silhouette toward a human's, {with_iou:.3f} -> "
              f"{bare_iou:.3f}")
        if bare_iou > SPECIES_HEAD_IOU_MAX:
            caught_by_ceiling.add(key)
    # WHICH OF THOSE THE CEILING CATCHES ON ITS OWN, pinned as a set rather
    # than hoped for. The ceiling cannot go below the worst pair that really
    # exists (human vs Narn, 0.812), so it can only catch a stripped species
    # whose bare skull still reads above 0.86 -- the Minbari does, at 0.887; the
    # Centauri's skull alone reads 0.822 and is covered by its own strip control
    # and by nothing else. Asserting the SET means a change that stops the
    # ceiling catching the Minbari fails here instead of passing quietly.
    check(caught_by_ceiling == {"minbari"},
          f"the {SPECIES_HEAD_IOU_MAX} ceiling alone catches a crestless "
          f"{sorted(caught_by_ceiling)}; the rest are covered by their strip "
          f"control, because the ceiling cannot sit below the worst real pair")
    # CONTROL C, AND IT IS THE ONE THE TASK NAMES: build all four species from
    # the HUMAN parameter block with no attachments at all -- four humans in
    # different hats, which is exactly the failure this gate exists to catch --
    # and every pair has to read 1.000 and FAIL the ceiling above. Without
    # this, a raster that returned a constant would pass everything.
    hsp = SPECIES["human"]
    clones = {}
    for key in GATE_SPECIES:
        ind0 = individual("human", "sil-probe")
        cl = Individual(*[getattr(ind0, f.name) if f.name != "species"
                          else key
                          for f in ind0.__dataclass_fields__.values()])
        cm = _PLANS[hsp.plan](cl, hsp, seg=chain[bake]["radial_segments"],
                              ring_stride=chain[bake]["ring_stride"],
                              features=chain[bake]["features"])
        cv, ct, _cs = cm.as_tuple()
        clones[key] = (silhouette_raster(cv, ct, nx=HEAD_BAND_NX,
                                         ny=HEAD_BAND_NY, axis=0,
                                         span=HEAD_BAND_SPAN),
                       silhouette_raster(cv, ct, nx=HEAD_BAND_NX,
                                         ny=HEAD_BAND_NY, axis=2,
                                         span=HEAD_BAND_SPAN))
    clone_worst = 0.0
    for i, a in enumerate(GATE_SPECIES):
        for b in GATE_SPECIES[i + 1:]:
            clone_worst = max(clone_worst,
                              min(silhouette_iou(clones[a][k], clones[b][k],
                                                 lo_row=hband) for k in (0, 1)))
    say(f"  CONTROL  four species built from ONE parameter block: "
        f"worst pair IoU {clone_worst:.3f}")
    check(clone_worst > SPECIES_HEAD_IOU_MAX,
          f"MUTATION: four bodies built from one parameter block read "
          f"{clone_worst:.3f} and FAIL the {SPECIES_HEAD_IOU_MAX} ceiling the "
          f"four real species pass -- the gate can tell four humans apart "
          f"from four species")
    # Stature is the other half of a species' silhouette and is asserted
    # separately, because the raster above normalises it away on purpose.
    stats = {k: nominal(k).stature_m for k in GATE_SPECIES}
    check(max(stats.values()) - min(stats.values()) > 0.08,
          f"and the four differ in stature as well as in shape ({stats})")

    # -- 5. THE FORM TIER: what it costs, what it buys, where it is honest ---
    # Session 4h added rings, and a ring is the one kind of articulation this
    # module cannot make free. So the tier is gated four ways and every one of
    # them can fail:
    #
    #   (a) it must cost NOTHING below `features == "all"`. The corridor bake
    #       and every level past 28.1 m are the same triangles they were.
    #   (b) the level a body is drawn at must carry the tier the schedule and
    #       the Nyquist rule say it should -- `_form_for`, not a table.
    #   (c) the deviation each drop accepts, in PIXELS at the distance it is
    #       actually dropped at, against the module's own budget.
    #   (d) and the control: `feature_schedule`'s two instruments must both be
    #       shown to score this cull at zero, which is why it needed a third.
    say("\nTHE FORM TIER: landmark rings, and where each one stops")
    frm = form_schedule()
    say(f"  {'step':16} {'error m':>9} {'honest from':>12} "
        f"{'dropped at':>11} {'px at the drop':>15}")
    for row in frm:
        at = [lv["switch_distance_m"] for lv in chain
              if lv.get("ring_form") == row["form"]]
        d = min(at) if at else None
        px = (row["error_m"] / d * _px_scale(1.0)) if d else 0.0
        say(f"  {row['form']:16} {row['error_m']:>9.5f} "
            f"{row['honest_from_m']:>11.2f}m "
            f"{('%.1f m' % d) if d is not None else '--':>11} "
            f"{px:>14.2f}")
    say(f"  {'level':6} {'features':>14} {'ring form':>14} {'as shipped':>11} "
        f"{'all rings':>10} {'saved':>7}")
    for i, lv in enumerate(chain):
        if lv["kind"] != "mesh":
            continue
        kw = dict(seg=lv["radial_segments"], ring_stride=lv["ring_stride"],
                  features=lv["features"])
        n_ship = len(_PLANS["humanoid"](individual("human", "form-probe"),
                                        SPECIES["human"],
                                        form=lv["ring_form"], **kw).tris)
        n_form = len(_PLANS["humanoid"](individual("human", "form-probe"),
                                        SPECIES["human"],
                                        form=FORM_STEPS[0], **kw).tris)
        say(f"  {lv['name']:6} {lv['features']:>14} {lv['ring_form']:>14} "
            f"{n_ship:>11,} {n_form:>10,} {n_form - n_ship:>7,}")
    # (a) The invariant that keeps lod3 and below at exactly the cost they had:
    # a build below `all` uses the DECLARED base plan and nothing else. Stated
    # as ring counts rather than as triangle counts, because a triangle count
    # is a number this session could have tuned and a ring plan is not.
    bad_plan = []
    for key, sp in SPECIES.items():
        if sp.plan != "humanoid":
            continue
        ind_b = individual(key, "form-probe")
        if len(_head_profile(ind_b, False)) != HEAD_RINGS:
            bad_plan.append(f"{key} head")
        if len(_torso_profile(ind_b, sp, False)) != len(TORSO_RINGS):
            bad_plan.append(f"{key} torso")
    check(not bad_plan,
          f"(a) every species' BASE ring plan is the declared one -- "
          f"{HEAD_RINGS} head, {len(TORSO_RINGS)} torso -- so no level below "
          f"`all` can have grown ({bad_plan})")
    lod_base = [i for i, lv in enumerate(chain)
                if lv["kind"] == "mesh" and lv["ring_form"] == FORM_STEPS[-1]]
    check(lod_base and all(
              len(_PLANS["humanoid"](individual("human", "form-probe"),
                                     SPECIES["human"],
                                     seg=chain[i]["radial_segments"],
                                     ring_stride=chain[i]["ring_stride"],
                                     features=chain[i]["features"],
                                     form=FORM_STEPS[0]).tris)
              > len(build("human", "form-probe", i, chain)[1])
              for i in lod_base),
          f"and forcing the tier ON at those levels WOULD cost more, so the "
          f"saving is real rather than a level that never had the rings "
          f"({[chain[i]['name'] for i in lod_base]})")
    # (b) The chain's own field agrees with the rule, level by level.
    check(all(lv["ring_form"] == _form_for(lv["radial_segments"],
                                           lv["features"])
              for lv in chain if lv["kind"] == "mesh"),
          "(b) every level's ring form is `_form_for`'s answer for its own "
          "knobs, not a table that can go stale")
    check(_form_for(64, "all") == "face_and_body"
          and _form_for(16, "all") == "body"
          and _form_for(16, "no_detail") == "none",
          "and that rule turns the face rings off with the radial count and "
          "the body rings off with the feature level")
    # (c) The pixel cost of each drop, at the distance it is really dropped at.
    # A DECLARED CEILING RATHER THAN THE BUDGET, because the face tier is
    # dropped 4.5 m early on purpose -- see FACE_FORM_MIN_SEG -- and a gate
    # that read PIXEL_BUDGET would either fail by design or have to pretend
    # that compromise was not made.
    FORM_DROP_PX_MAX = 2.5
    worst_px, worst_step = 0.0, None
    for row in frm:
        at = [lv["switch_distance_m"] for lv in chain
              if lv.get("ring_form") == row["form"]]
        if not at or row["error_m"] <= 0.0:
            continue
        px = row["error_m"] / min(at) * _px_scale(1.0)
        if px > worst_px:
            worst_px, worst_step = px, row["form"]
    check(worst_px <= FORM_DROP_PX_MAX,
          f"(c) the worst ring-form drop accepts {worst_px:.2f} px of "
          f"deviation at the distance it happens ({worst_step}), against a "
          f"declared {FORM_DROP_PX_MAX} px ceiling and the module's own "
          f"{PIXEL_BUDGET} px budget")
    check(worst_px > PIXEL_BUDGET,
          f"and it is OVER the budget rather than inside it -- {worst_px:.2f} "
          f"px against {PIXEL_BUDGET} -- which is the compromise "
          f"FACE_FORM_MIN_SEG states, recorded as a number rather than "
          f"absorbed")
    # (d) THE CONTROL, WHICH NEEDED `form` TO BE OVERRIDABLE TO EXIST AT ALL.
    # `feature_schedule`'s two instruments -- the part list and the figure's
    # bounding box -- must be SHOWN to score this cull at zero, on the very
    # pair of meshes the schedule scored at millimetres. Building the same
    # feature level with the rings on and off is the only way to construct
    # that, which is why `build_humanoid` takes `form` and not just `features`.
    _fp = _unstooped(individual("human", "form-probe"))
    _mf = _PLANS["humanoid"](_fp, SPECIES["human"], seg=16, features="all",
                             form=FORM_STEPS[0])
    _mb = _PLANS["humanoid"](_fp, SPECIES["human"], seg=16, features="all",
                             form=FORM_STEPS[-1])
    _bbox = max(abs(a - b) for a, b in zip(_mf.bbox(), _mb.bbox()))
    _pf = {n for n, _v, _t in _mf.parts}
    _pb = {n for n, _v, _t in _mb.parts}
    _stand = _cull_standoff(_mf, _mb)
    check(len(_mf.tris) > len(_mb.tris),
          f"(d) the two builds differ ({len(_mb.tris):,} -> "
          f"{len(_mf.tris):,} triangles), so the comparison below is real")
    check(_bbox < 1e-4 and _pf == _pb and _stand == 0.0
          and frm[-1]["error_m"] > 0.002,
          f"(d) dropping the form rings removes NO part, moves the bounding "
          f"box {_bbox * 1000:.3f} mm and gives `_cull_standoff` {_stand:.3f} "
          f"m -- `feature_schedule`'s two instruments BOTH score it zero -- "
          f"while the chord error is {frm[-1]['error_m'] * 1000:.1f} mm. The "
          f"cull needed a third instrument and `form_schedule` is it")


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
        # BOTH directories, and the second one is a fix. `schedule.py` reaches
        # its siblings as `npc.<module>`, so the package's PARENT has to be
        # importable too; with only `_HERE` on the path the import died with
        # "No module named 'npc'" and this check had been reporting FAIL --
        # against a real interface, for an environment reason -- since
        # `schedule.py` grew that import.
        sys.path.insert(0, _HERE)
        sys.path.insert(0, _STATION)
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
    # THE DECLARED PLAN IS THE BASE TIER, and the FULL plan must be a strict
    # superset of it -- otherwise a switch to lod3 rearranges the figure rather
    # than simplifying it, which is the exact property `SILHOUETTE_STEPS` and
    # `_stride` exist to hold and the reason the tier is a filter of one list.
    _hb = _head_profile(nominal("human"), form=False)
    _hf = _head_profile(nominal("human"), form=True)
    _tb = _torso_profile(nominal("human"), SPECIES["human"], form=False)
    _tf = _torso_profile(nominal("human"), SPECIES["human"], form=True)
    check(len(_hb) == HEAD_RINGS and len(_tb) == len(TORSO_RINGS),
          f"the declared BASE ring plan is the built one "
          f"({len(_hb)} head rings against HEAD_RINGS={HEAD_RINGS}, "
          f"{len(_tb)} torso against {len(TORSO_RINGS)})")
    check(len(_hf) > len(_hb) and len(_tf) > len(_tb),
          f"and the form tier adds rings ({len(_hb)} -> {len(_hf)} head, "
          f"{len(_tb)} -> {len(_tf)} torso)")
    check(all(r in _hf for r in _hb) and all(r in _tf for r in _tb),
          "every BASE row is present, identical, in the FORM profile -- the "
          "coarse ring plan is a strict subset of the fine one")
    check(all(r[-1] in RING_TIERS for r in _hf + tuple(_tf)),
          "every profile row declares a tier the module knows")
    # And the same for a limb: the form ring plan must contain the base one.
    for _b_at in (0.19, 0.55):
        _lb, _lf = _limb_ts(_b_at), _limb_ts(_b_at, form=True)
        check(len(_lb) == LIMB_RINGS and len(_lf) > len(_lb)
              and all(any(abs(x - y) < 1e-12 for y in _lf) for x in _lb),
              f"a limb's base ring plan is {LIMB_RINGS} rings and a strict "
              f"subset of its form plan ({_lb} in {_lf})")
        check(any(abs(x - _b_at) < 1e-12 for x in _lb),
              f"and the muscle belly at {_b_at} HAS a ring on it -- the "
              f"defect `_limb_ts` exists to fix ({_lb})")
    for key, sp in SPECIES.items():
        for _form in (False, True):
            ys = [f for _n, f, _w, _d, _s, _t
                  in _torso_profile(nominal(key), sp, _form)]
            check(all(a < b for a, b in zip(ys, ys[1:])),
                  f"{key}: torso ring heights strictly increase at "
                  f"form={_form} ({[round(y, 3) for y in ys]})")
            ts = [t for t, _k, _z, _s, _ti in _head_profile(nominal(key), _form)]
            check(all(a < b for a, b in zip(ts, ts[1:])),
                  f"{key}: head ring heights strictly increase at "
                  f"form={_form} ({ts})")

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
    # BY PART, NOT BY GROUP, and the difference is a defect this assertion
    # caught the moment eyes existed. The crest emits into `npc_hair` and so do
    # the brows, so "no npc_hair group" stopped meaning "no crest" and started
    # meaning "no crest and no eyebrows either" -- an assertion that had
    # silently changed what it was about. The parts list is the thing that
    # actually says which feature was built.
    def _parts_of(species, npc_id):
        sp = SPECIES[species]
        return {n for n, _v, _t in _PLANS[sp.plan](
            individual(species, npc_id), sp, seg=16, ring_stride=1,
            features="all").parts}

    mp = _parts_of("centauri", f"c{males[0]}")
    fp = _parts_of("centauri", f"c{females[0]}")
    check("centauri_crest" in mp and "hair" in mp,
          "a Centauri male carries the crest and the hair")
    check("centauri_crest" not in fp and "hair" not in fp,
          "a Centauri female carries no crest mesh at all, not a zero-size one")
    check("eye" in fp and "eyebrow" in fp,
          "and she still has eyes -- the shaven head is a feature-list drop, "
          "not a bald group name")
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

    # THE FEATURE SCHEDULE MUST BE ABLE TO SEE A CULL THAT HAPPENS INSIDE THE
    # BOUNDING BOX. This is the assertion session 4e's face and hair would have
    # needed and did not have: `no_detail` removes the nose, the ears, the brow
    # and the thumbs, every one of which lies strictly inside the figure's own
    # extremes, and the whole-figure bbox measurement scores that cull at
    # exactly zero -- so the chain never used the `all` level at any distance
    # and the face existed only in the source. Both halves are checked: the
    # combined measurement is non-zero, and the old bbox-only one is shown to
    # be the thing that was blind.
    _fs = individual("human", "lod-probe")
    _full = build_humanoid(_fs, SPECIES["human"], seg=16, features="all")
    _cut = build_humanoid(_fs, SPECIES["human"], seg=16, features="no_detail")
    _bbox_only = max(abs(a - b) for a, b in zip(_full.bbox(), _cut.bbox()))
    _stand = _cull_standoff(_full, _cut)
    check(_bbox_only < 1e-9,
          f"CONTROL: dropping the face and the thumbs moves the figure's "
          f"bounding box by {_bbox_only:.6f} m -- the old measurement, and the "
          f"reason the `all` level was unreachable")
    check(_stand > 0.010,
          f"but the removed geometry stood {_stand * 1000:.1f} mm outside what "
          f"remains, which is what `_cull_standoff` prices")
    check(fea[1]["error_m"] > 0.010 and fea[1]["honest_from_m"] > 5.0,
          f"so `no_detail` is honest only from {fea[1]['honest_from_m']:.1f} m "
          f"(error {fea[1]['error_m']:.5f} m), and the chain has a level that "
          f"carries a face")
    check(any(lv["features"] == "all" for lv in chain),
          "the chain USES the full feature level at some distance -- it did "
          "not, for as long as the bbox was the only instrument")
    # And the standoff measurement must return zero when nothing is removed,
    # or it is measuring the mesh rather than the cull.
    check(_cull_standoff(_full, _full) == 0.0,
          "MUTATION: a cull that removes nothing measures zero stand-off")
    # EACH REMOVED VERTEX IS PRICED ONCE. A part that pokes out of the culled
    # figure's own outline is priced by the bbox term, so it must contribute
    # NOTHING here -- pricing it twice moved `identity_only` from 81 m to 150 m
    # on the strength of a Grome's toe and put the drum floor 1.1% over the NPC
    # triangle budget, which `npc/crowd.py`'s worst-case gate caught. Both
    # directions are constructed, so this cannot rot into a tautology.
    def _twopart():
        # A host, and a second retained part further out that SETS the outline
        # -- the stand-in for the feet and hands, which is what puts a nose
        # strictly inside the figure while leaving it clear of the head.
        mm = Mesh()
        mm.add(*_loft([_ring(0, 0, 0, 1, 1, 8), _ring(0, 1, 0, 1, 1, 8)]),
               "g", "host")
        mm.add(*_loft([_ring(1.6, 0, 0, 0.1, 0.1, 6),
                       _ring(1.6, 0.4, 0, 0.1, 0.1, 6)]), "g", "outrigger")
        return mm
    _hostm = _twopart()
    _inside = _twopart()
    _inside.add(*_loft([_ring(1.2, 0.4, 0, 0.1, 0.1, 6),
                        _ring(1.2, 0.6, 0, 0.1, 0.1, 6)]), "g", "bump")
    _outside = _twopart()
    _outside.add(*_loft([_ring(0, 1.4, 0, 0.1, 0.1, 6),
                         _ring(0, 1.8, 0, 0.1, 0.1, 6)]), "g", "spike")
    check(0.10 < _cull_standoff(_inside, _hostm) < 0.40,
          f"a removed part INSIDE the outline is priced by its stand-off from "
          f"the parts that remain ({_cull_standoff(_inside, _hostm):.3f} m for "
          f"a bump whose far face is 0.30 m clear of the host)")
    check(_cull_standoff(_outside, _hostm) == 0.0,
          f"and one that pokes OUT of it is priced by the bounding box "
          f"instead, not twice "
          f"({_cull_standoff(_outside, _hostm):.3f} m)")
    check(_dist_to_box((0.0, 0.0, 0.0), (-1, -1, -1, 1, 1, 1)) == 0.0
          and abs(_dist_to_box((4.0, 0.0, 5.0), (-1, -1, -1, 1, 1, 1))
                  - 5.0) < 1e-12,
          "point-to-box is zero inside and Pythagorean outside the face "
          f"(got {_dist_to_box((4.0, 0.0, 5.0), (-1, -1, -1, 1, 1, 1)):.6f})")

    # -- the body has the parts a body has --------------------------------
    # Named, at lod0, because "undetailed featureless blobs" (owner, session 4e)
    # is a statement about which parts exist and these are the ones that did
    # not. Asserted on the DEFAULT chain level a room occupant is baked at as
    # well, because a part that exists only at lod0 is a part nobody sees.
    for lvl, want in ((0, ("head", "nose", "ear", "hair", "hand", "thumb")),
                      (1, ("head", "nose", "ear", "hair", "hand", "thumb")),
                      (4, ("head", "hair", "hand"))):
        mp = _PLANS["humanoid"](
            individual("human", "parts-probe"), SPECIES["human"],
            seg=chain[lvl]["radial_segments"],
            ring_stride=chain[lvl]["ring_stride"],
            features=chain[lvl]["features"])
        have = {n for n, _v, _t in mp.parts}
        check(all(w in have for w in want),
              f"a human at {chain[lvl]['name']} has {want} "
              f"(missing {[w for w in want if w not in have]})")
    # The corridor crowd is baked at whatever level is nearest 600 triangles --
    # `populace.corridor_lod` -- and that level MUST carry hair, because until
    # session 4e it did not and every walker on the station was bald.
    _counts = [len(build("human", "bake-probe", i, chain)[1])
               for i in range(len(chain))]
    _bake = min(range(len(_counts)), key=lambda i: abs(_counts[i] - 600))
    _bm = _PLANS["humanoid"](individual("human", "bake-probe"),
                             SPECIES["human"],
                             seg=chain[_bake]["radial_segments"],
                             ring_stride=chain[_bake]["ring_stride"],
                             features=chain[_bake]["features"])
    check("hair" in {n for n, _v, _t in _bm.parts},
          f"the level the corridor crowd is baked at ({chain[_bake]['name']}, "
          f"{_counts[_bake]} triangles) carries hair")
    check(_counts[_bake] <= 640,
          f"and it is still inside the 600-triangle allowance "
          f"schedule.NPC_BUDGET gives its distance band ({_counts[_bake]})")

    # -- residents differ from one another, visibly ------------------------
    # A crowd of one haircut is a crowd of clones. Drawn from the same hash as
    # the name and the schedule, so this is a property of the id.
    styles = {}
    for i in range(400):
        styles[hair_style_for(f"human:h{i}", "m" if i % 2 else "f")] = 1
    check(len(styles) >= 6,
          f"the wardrobe of haircuts is actually drawn from "
          f"({sorted(styles)})")
    check(all(s in HAIR_STYLES for s in styles),
          f"and every style drawn is a real one ({sorted(styles)})")
    check(nominal("human").hair_style in HAIR_STYLES,
          "the nominal figure's haircut is a real one too")
    check(individual("human", "hx-1").hair_style
          == individual("human", "hx-1").hair_style
          and individual("human", "hx-1") != individual("human", "hx-2"),
          "a resident's haircut is a pure function of their id")
    check(individual("grome", "hx-1").hair_style == "",
          "a species with no hair feature is given no style, not a hidden one")
    # Sexual dimorphism is a SHAPE, and it has to be present in the mesh rather
    # than in the parameter table. Same id, same stature, sex flipped.
    _base = individual("human", "dimorph-probe")

    def _sexed(s):
        ii = Individual(_base.species, _base.npc_id, HUMAN_STATURE_M, 1.0, 1.0,
                        1.0, SPECIES["human"].cranium, 1.0, 0.0, s, 0, 0,
                        SPECIES["human"].features, "crop")
        pr = _torso_profile(ii, SPECIES["human"])
        return {n: (w, d) for n, _f, w, d, _s, _t in pr}
    _m, _f2 = _sexed("m"), _sexed("f")
    check(_f2["hip"][0] > _m["hip"][0] and _f2["shoulder"][0] < _m["shoulder"][0]
          and _f2["waist"][0] / _f2["shoulder"][0]
          < _m["waist"][0] / _m["shoulder"][0],
          f"a woman is built to a different shoulder-to-hip ratio than a man "
          f"(hip {_f2['hip'][0]:.4f} vs {_m['hip'][0]:.4f}, shoulder "
          f"{_f2['shoulder'][0]:.4f} vs {_m['shoulder'][0]:.4f})")

    # -- the ring sections are doing work ----------------------------------
    # A superellipse and a lobe cost NOTHING, which is the whole reason they
    # are the first tool reached for -- so the assertion is that they changed
    # the geometry and not the count. Built against the same ring as an
    # ellipse with no lobes.
    _plain = _ring(0.0, 0.0, 0.0, 1.0, 1.0, 64)
    _sq = _ring(0.0, 0.0, 0.0, 1.0, 1.0, 64, power=2.6)
    _lob = _ring(0.0, 0.0, 0.0, 1.0, 1.0, 64, lobes=((90.0, 30.0, 0.20),))
    check(len(_plain) == len(_sq) == len(_lob) == 64,
          "shaping a ring does not change its vertex count")
    check(max(math.hypot(a[0], a[2]) for a in _sq) > 1.05,
          f"a superellipse section is fatter off-axis than an ellipse "
          f"({max(math.hypot(a[0], a[2]) for a in _sq):.4f} against 1.0)")
    check(abs(max(a[2] for a in _lob) - 1.20) < 1e-9
          and abs(max(a[0] for a in _lob) - 1.0) < 1e-9,
          "a lobe at 90 degrees raises the FRONT radius by its amount and "
          "leaves the sides alone")
    check(all(abs(_ring(0, 0, 0, 1, 1, 16, power=2.0)[i][j]
                  - _plain[i * 4][j]) < 1e-12
              for i in range(16) for j in range(3)),
          "power 2.0 is the ellipse this function used to be, exactly")
    # The shaping must survive decimation, or the chain pops instead of
    # simplifying: a coarse ring's vertices are still a strict subset.
    _c8 = _ring(0.0, 0.0, 0.0, 1.0, 1.0, 8, power=2.6,
                lobes=((90.0, 30.0, 0.20),))
    _f64 = {tuple(round(c, 12) for c in v) for v in
            _ring(0.0, 0.0, 0.0, 1.0, 1.0, 64, power=2.6,
                  lobes=((90.0, 30.0, 0.20),))}
    check(all(tuple(round(c, 12) for c in v) in _f64 for v in _c8),
          "a shaped ring's 8 vertices are still a strict subset of its 64")

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
    # `REF_SECTION_R_M` must stay at or below the MEASURED worst section, or
    # `_small_seg` starts handing attachments a looser error budget than the
    # body they hang on. Asserted as an ordering, because the first version of
    # this check claimed the two agreed to 10% and they do not -- the measured
    # worst is a Vorlon robe hem at 0.4514 m and this is a human shoulder at
    # 0.2056 m. The assertion fired on its first run, which is why the comment
    # above now says the true thing.
    _rref = _max_section_radius()
    check(REF_SECTION_R_M <= _rref,
          f"REF_SECTION_R_M {REF_SECTION_R_M:.4f} m is at or below the "
          f"MEASURED worst section radius {_rref:.4f} m, so _small_seg is "
          f"conservative rather than permissive")
    # And `_small_seg` must actually be doing arithmetic rather than returning
    # its cap: a finger is 30x smaller in radius than the reference section, so
    # it has to come out coarser than the body at every level.
    check(_small_seg(0.009, 64) < 64 and _small_seg(0.009, 16) <= 8
          and _small_seg(0.009, 8) <= 8,
          f"_small_seg gives a 9 mm finger {_small_seg(0.009, 64)} segments at "
          f"the body's 64 and {_small_seg(0.009, 16)} at its 16")
    check(_small_seg(REF_SECTION_R_M, 8) >= 8,
          "MUTATION: asked about a part the SIZE of the reference section it "
          "returns the body's own count, so the rule is a comparison and not "
          "a constant")
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

    _detail_gate(check, quiet=True)

    # -- the skinned export ------------------------------------------------
    # HERE RATHER THAN IN ITS OWN GATE. CLAUDE.md's session-3x rule: a gate
    # belongs in the module that builds the thing, and it must build the hard
    # case. The hard case for a skin is a DRESSED figure, because `costume.py`
    # replaces parts and appends accessories, so a human is run rather than the
    # bare plan. It costs one `animation.rig()` build, ~1 s.
    _sok, _sfail = skin_selftest("human", out=print)
    ok += _sok
    fail += _sfail

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
    ap.add_argument("--silhouette", action="store_true",
                    help="print the session-4g detail gate and its controls")
    ap.add_argument("--skin", action="store_true",
                    help="print the skinned export's gate and its control")
    ap.add_argument("--skin-out", default=None, metavar="DIR",
                    help="write <species>_skin.json for every species")
    a = ap.parse_args()
    if a.skin:
        o, f = skin_selftest(a.species or "human")
        print(f"skinned export: {o}/{o + f} passed")
        sys.exit(1 if f else 0)
    if a.skin_out:
        total = 0
        for k in ([a.species] if a.species else sorted(SPECIES)):
            doc = skinned(k, lod=a.lod)
            path, size = write_skinned(
                os.path.join(a.skin_out, f"{k}_skin.json"), doc)
            total += size
            print(f"  {k:9s} {doc['vertices']:6,} v  {doc['triangles']:6,} t  "
                  f"{len(doc['surfaces'])} surfaces  {size / 1e3:7.1f} kB")
        print(f"wrote {a.skin_out}: {total / 1e6:.2f} MB")
        sys.exit(0)
    if a.silhouette:
        bad = []
        _detail_gate(lambda c, label: None if c else bad.append(label))
        for b in bad:
            print(f"FAIL: {b}")
        sys.exit(1 if bad else 0)
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
