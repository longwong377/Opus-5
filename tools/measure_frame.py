#!/usr/bin/env python3
"""Measure a rendered frame the way the reference frames were measured.

WHY THIS EXISTS. Three agents measured every light source in the reference in
session 3n and recorded, per space, a single number that describes the whole
lighting scheme: `ambient.ratio`, the darkest measurable structural surface
over the brightest lit surface. A residential corridor is 0.300; command and
control is 0.047. That is the difference between a place that reads as lived
in and a place that reads as a dark room with instruments in it, and it is one
number.

Nothing compared OUR frames to it. The corridor's ambient was hand-tuned until
the render looked right, and the first lit render of a rooms.py medlab came
back a white box -- correctly lit in the sense that every fitting was where the
measurement put it, and wrong in the only sense that matters.

So this measures a PNG -- ours or the show's, with the same code, which is the
only way the two can be compared at all.

    python3 tools/measure_frame.py docs/engine-medlab.png \
        --against "reference/03-sector-blue/war room.webp"
    python3 tools/measure_frame.py                        # self-test

THE NUMBER IN THE JSON IS NOT THE NUMBER THIS PRINTS, and finding that out the
hard way is why the warning is this loud. The reference measurement picked two
regions BY EYE -- "the soffit above the gallery fascia", "the clean deck
field" -- on a grey-world-balanced image. This takes percentiles over a whole
raw frame. Run it on `grey level 1.webp`, the frame whose JSON entry says
0.300, and it reports 0.086. Across the eleven measured spaces the two
statistics correlate at Pearson 0.65 and rank-correlate at 0.58: related, and
nowhere near interchangeable.

    space                json   this   median
    fresh_air            0.041  0.024  0.0300
    command_control      0.047  0.032  0.0331
    corridor_service     0.060  0.025  0.0379
    casino               0.074  0.029  0.0631
    docking_bay          0.076  0.055  0.0373
    dougs_dugout         0.090  0.025  0.0516
    zocalo_concourse     0.094  0.031  0.0597
    corridor_concourse   0.120  0.035  0.0245
    council_chamber      0.210  0.035  0.0767
    war_room             0.230  0.031  0.0451
    corridor_residential 0.300  0.086  0.0533

So THE ONLY VALID COMPARISON IS BETWEEN TWO FRAMES MEASURED BY THIS TOOL --
ours against the reference frame of the same space, which is what `--against`
does. Tuning a render until this prints the JSON's number is tuning against a
statistic the reference never had; it lands the corridor at ambient 5.6 and a
frame two and a half stops hotter than the show. That happened, in the session
that wrote this file, before the reference frame was measured with the same
code.

WHAT IT EXCLUDES, and the reference excluded the same two populations by hand:

  * EMITTERS. A lamp is not a lit surface. Anything at or above `clip` is
    dropped, which removes light fittings, their bloom, and any surface that
    has blown -- and the dropped fraction is REPORTED, because a frame that
    clips 8% of its pixels is overexposed no matter what the ratio says.
  * CRUSHED BLACK. "Darkest MEASURABLE surface" is the reference's own wording,
    and it says so explicitly in one entry: "the gallery slab edge at Y 0.028
    is nearly crushed and is not used". Below `floor` a surface has no
    measurable value, so it is not one.

    DO NOT READ A HIGH CRUSHED FRACTION AS A DEFECT. The show's interiors
    crush hard, and far harder than our renders do: `more hallways.jpg` 61.5%,
    the Zocalo 54.9%, command and control 49.8%, Doug's Dugout 63.3%, against
    19-54% for the rooms calibrated against them. `grey level 1.webp` at 2.25%
    is the outlier -- it is the one BRIGHT residential corridor in the set --
    and generalising from it produced a written-down finding that the other ten
    frames refuted the same afternoon.

The consequence worth stating: this measures a frame, not a room. Point the
camera at a wall and it will report whatever that wall does. It is a
regression gate on a FIXED shot, which is what the render scripts produce.

===========================================================================
THE MEDIAN IS NOT ENOUGH, AND THIS IS THE HALF THAT WAS MISSING
===========================================================================

Every exposure in this project was set by one test: our frame's median over
its reference's median must land at x1.40 +/-25%. The owner looked at the
renders and said they read as blockout. Every gate was green. Both are true,
because A MEDIAN IS A STATISTIC A FLAT FRAME MATCHES PERFECTLY -- it says
where the middle of the picture sits and nothing whatever about how far the
picture reaches in either direction. Measured on two frames committed the day
before this was written:

    docs/engine-drum-garden.png  median 0.2098  p5 0.0573  crushed  0.01%
    reference .../garden.png     median 0.1406  p5 0.0180  crushed  5.63%

x1.49 of its reference on the median -- inside the band, green -- while its
shadows sit at 3.2x the reference's and it has essentially NO black pixels at
all. A frame with no blacks reads washed out whatever its median is.

So `distribution()` compares the WHOLE distribution: p5, p95, the p5/p95
ratio, the crushed fraction and the clipped fraction, each against the
reference frame RE-EXPOSED TO OUR OFFSET (`measure(ref, gain=RENDER_OFFSET)`),
so that a level difference the median gate already allows is not counted twice
as a shape difference. The median check is unchanged and still reported: it is
not wrong, it is insufficient.

WHERE THE TOLERANCES COME FROM, because a tolerance with no derivation is a
guess with a decimal point. They are measured off the show's own frames --
`docs/layer4-lighting/frame_distribution.json` holds the corpus, the pairs and
the numbers, and `--derive` recomputes the whole thing and fails if the
constants below no longer match it. The chain, in full:

  1. THE CORPUS is 33 deduplicated authority-1 on-screen frames that depict a
     lit set or a lit exterior -- the thing our renders are. Props on a studio
     backdrop, schematics, costume stills, authority-2 production art and both
     QUARANTINE folders are out. Eight of the tree's files are byte-identical
     duplicates of another and are counted once; two of those eight are NOT
     recorded as duplicates in 00-INDEX --
     `10-interiors-generic-kit/garden more.jpg` is `Babylon_5_2-22_29a.jpg` and
     `10-interiors-generic-kit/more hallways.jpg`, which is `plant`'s
     calibration reference, is `01-station-exterior/sleeping-in-light-05.jpg`,
     an S5 frame and so outside the S2-3 era lock.
  2. WHICH PAIRS COUNT AS "THE SAME REGISTER" is not a new judgement. It is
     this file's existing rule, applied to the show instead of to us: two
     frames whose medians agree within TOL are calibratable against each other
     -- the rule DRUM_CALIBRATION already uses when it accepts `garden.png`
     against `Babylon_5_2-22_34b.jpg` ("8% apart, inside the +/-25% the gate
     allows") and rejects `29a`. 124 of the corpus's 528 pairs qualify.
  3. THE BAND IS THE p95 OF |ln(a/b)| OVER THOSE 124 PAIRS. Each band therefore
     admits 95% of the disagreement the show has with ITSELF at matched level.
     The 5% excluded is the tail where the median test calls two frames
     equivalent and they are different pictures -- `29a` against `34b` is
     exactly that case and INV-044 already says so. Using the observed MAXIMUM
     instead would fit the tolerance to the single worst pair in a 124-pair
     sample, which is an envelope, not a tolerance.
  4. AND IT IS VALIDATED BY RUNNING THE GATE ON THE SHOW AGAINST ITSELF, both
     orders, 248 trials, in exactly the form it is applied to us. Per check it
     admits 85.5%-100%; the COMBINED verdict admits 77.4%. Six checks at
     85-100% cannot combine to 95%, and part of the missing 23% is real -- the
     124 pairs include a war room against a residential corridor, which agree
     on median by coincidence and are not the same picture. The full table is
     in the JSON under `show_vs_show_admission`.

  THE ESTIMATE IS NOT STABLE TO ONE FRAME, and that is stated rather than
  buried: `gardens or greenery.jpg` was missed on the first pass and adding it
  -- one frame in 33, 26 new pairs -- moved the p5 band from x1.224 to x1.290.
  p95 of a 124-pair sample is its 6th-largest value. Treat these as bands good
  to about 5%, not to three figures.

WHAT THE CORPUS SAYS, and two of the five results are negative:

    statistic   p95 band   what it is worth
    p5          x1.290     THE DISCRIMINATOR. Tight because the show's frames
                           crush: their 5th measurable percentile sits close to
                           the 0.010 floor in almost every frame. Ours sit at
                           1.5-3.2x their references'.
    crushed     x11.42     Wide, and still fires: our garden frame is x0.004.
    p95         x3.266     Nearly inert. p95 is whatever practical light is in
                           shot, and the show disagrees with itself by 3x.
    p5/p95      x3.378     Nearly inert, and it inherits that from p95. The
                           ratio is the statistic that sounds like the right
                           one and measures the least.
    clipped     absolute   No usable pairwise structure at all (x53 dispersion
                           at p90). Gated as an absolute cap instead, at the
                           p95 of the corpus's own clipped fraction re-exposed
                           to our offset: 3.69%. That INDEPENDENTLY corroborates
                           the 4% overexposure threshold this file already
                           carried, which was set from our own lamp geometry.

TWO STATISTICS PROPOSED IN SESSION 4a AND REFUTED BY THE CORPUS, recorded so
they are not re-derived. `docs/engine-zocalo-inside.png` was committed with the
honest craft read "the stall vitrines and the floor pools are clipping to pure
white". Measured, that frame is 0.00% CLIPPED at this file's threshold -- its
maximum luminance is 0.921 -- so whatever the eye is seeing, `clipped` cannot
see it. Two candidate statistics were built to catch it and BOTH FAIL AGAINST
THE SHOW:

  * `bright_tail`, the fraction of the frame above x8 its own median. Ours is
    3.39% against `more zocalo.png`'s 0.54%, x6.3, which looked decisive
    against ONE reference. Over the whole 33-frame corpus the show spans
    0.00%-7.50% with a median of 2.31%, so 3.39% is an utterly ordinary show
    value, and the pairwise band at matched median comes out at x15.47 -- wider
    than `crushed`'s x11.42 and therefore even more inert. `conference
    aerea.webp` is 7.50% and `zocalo.webp` 7.02%.
  * `hi_sat`, the mean saturation of the top 1% by luminance -- "are our
    highlights colourless?". Ours is 0.105 against 0.406 for `more zocalo.png`.
    The corpus spans 0.025 to 0.891 with a p5 of 0.078, and `Doug's
    Dugout.webp` -- one of OUR OWN calibration references -- is 0.088, LOWER
    than the frame the statistic was invented to fail. A gate at the corpus's
    p5 would admit us and reject the show.

THIS IS THE THIRD TIME THIS PROJECT HAS MADE THE SAME MISTAKE and the third
time the corpus has caught it: the crushed-fraction finding in session 3n and
the `grey level 1.webp` p5 outlier in docs/reference-values.md 7.3 are the
other two. RUN A NEW STATISTIC AGAINST ALL 33 FRAMES BEFORE BELIEVING IT
AGAINST ONE.

What IS measurable about that frame is LOCAL and this tool cannot express it:
its floor pool has 42.2% of its pixels within 2% of its own maximum and a
saturation of 0.046 -- a flat white plateau where a lit floor should have a
falloff. A gate for that needs REGIONS, and picking regions by eye is the
practice the head of this docstring exists to warn against.

AND A WARNING THAT BELONGS WITH THE MEDIAN, not with any of the above. The
median of the MEASURABLE pixels is not proportional to exposure and on some
frames is not even monotonic in it, because raising exposure recruits
sub-floor pixels into the measured set and they come in at the bottom.
Measured over the 33-frame corpus by scaling each frame's linear luminance:
the exponent d(ln median)/d(ln gain) between x1.0 and x1.4 ranges from 0.97
(`Babylon_5_2-22_34b.jpg`) to 0.01 (`more zocalo.png`), and SEVEN of the 33 go
DOWN somewhere in x0.5..x2.0 -- including `babylon 5 welcome sign...jpg`
(-0.16), the customs reference, and `rotunda.webp` (-0.46). Every room in
`export_scene.ROOM_EXPOSURE` and `BESPOKE_EXPOSURE` was set by
`gain *= 1.40 * ref_median / our_median`, which assumes that exponent is 1.
STATE.md already records the symptom for one room -- the plant "sits at 1.59x
either way" -- and it is a property of the statistic, not of the plant.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

# Rec. 709 luminance on LINEAR values. The reference measurements say "Y" and
# "balanced L" and are computed on linear light; doing it on the sRGB-encoded
# bytes would compress the shadows by roughly a factor of two and every ratio
# would come out too high.
LUMA = (0.2126, 0.7152, 0.0722)

# A surface at or above this is an emitter or has blown. 0.95 rather than 1.0
# because Godot's tonemapper rolls off: a light fitting reads 0.96-0.99 across
# its lens rather than a flat 1.0, and a threshold at 1.0 would count the lens
# as the brightest LIT surface in the frame and halve every ratio.
CLIP = 0.95
# Below this a surface has no measurable value. Matches the reference's own
# "nearly crushed and is not used" at Y 0.028.
FLOOR = 0.010
LO_PCT, HI_PCT = 5.0, 95.0


def srgb_to_linear(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def measure(path, clip=CLIP, floor=FLOOR, gain=1.0, box=None):
    """Luminance statistics for one frame, as a dict.

    `gain` multiplies LINEAR luminance before anything is measured. It is not
    a convenience: it is how a reference frame is put on our exposure so that
    its shape can be compared to ours without the x1.40 offset masquerading as
    a shape difference. See `distribution`.

    `box` is (left, top, right, bottom) as fractions of the frame. It exists
    because EXTERIOR_CALIBRATION's day reference is a fan-assembled wallpaper
    sheet whose backdrop is 90% of the pixels -- measuring it whole measures
    the backdrop, and export_scene says so at length. Anything measured
    box-to-box must use boxes that frame the same object the same way.
    """
    img = Image.open(path).convert("RGB")
    a = np.asarray(img, dtype=np.float64) / 255.0
    if box is not None:
        l, t, r, b = box
        h, w = a.shape[0], a.shape[1]
        a = a[int(t * h):int(b * h), int(l * w):int(r * w)]
        if a.size == 0:
            raise SystemExit(f"{path}: box {box} selects no pixels")
    lin = srgb_to_linear(a) * gain
    y = lin @ np.array(LUMA)
    n = float(y.size)
    lit = y[(y >= floor) & (y < clip)]
    if lit.size == 0:
        raise SystemExit(f"{path}: no measurable surface between "
                         f"{floor} and {clip}")
    lo = float(np.percentile(lit, LO_PCT))
    hi = float(np.percentile(lit, HI_PCT))
    return {
        "path": path,
        "size": f"{img.width}x{img.height}",
        "gain": gain,
        "box": tuple(box) if box is not None else None,
        "ratio": lo / hi if hi > 0 else 0.0,
        "dark_p5": lo,
        "bright_p95": hi,
        # THE TOP OF THE LADDER, which p95 cannot see. `bright_p95` is this
        # file's own admitted weak statistic -- its band is x3.27 and the
        # docstring calls it "nearly inert" -- because p95 lands on ordinary
        # practical light and every interior has some. What distinguishes a
        # show frame from ours is the SMALL BRIGHT POPULATION above that: a lit
        # hatch at 11x the wall, a ceiling strip at 7.7x, a fitting at 4.7x.
        # Measured on our own corridor against the anchor, p95 is 0.48x the
        # show's -- which the x3.27 band happily admits -- while p99 is 0.16x,
        # and nothing was looking at p99 at all.
        "bright_p99": float(np.percentile(lit, 99.0)),
        "median": float(np.median(lit)),
        # THE UNCENSORED LEVEL, and it exists because `median` CANNOT BE
        # INVERTED and every exposure in this project was set by inverting it.
        #
        # `median` is taken over `lit`, i.e. over the pixels between `floor`
        # and `clip`, and that population CHANGES WITH EXPOSURE. Raise the gain
        # and sub-floor pixels are recruited into the set; they arrive at the
        # bottom and drag the median down against the gain that lifted them.
        # That is why the module docstring can report d(ln median)/d(ln gain)
        # anywhere from 0.97 to 0.01 and NEGATIVE on seven of the corpus's 33
        # frames, and it is why `gain *= 1.40 * ref/ours` -- which assumes that
        # exponent is exactly 1 -- is not a derivation.
        #
        # This is the 25th percentile of the WHOLE frame, censored by nothing.
        # Its population is every pixel, always, so it can only move because the
        # light moved. Measured on the corridor anchor over a x6 sweep of the
        # ambient (0.4333 -> 0.65 -> 1.30 -> 2.60), the exponents are:
        #
        #   statistic            0.433    0.650    1.300    2.600   exponents
        #   median (censored)   0.0296   0.0421   0.0755   0.1421   +0.86 +0.84 +0.91
        #   dark_p5 (censored)  0.0126   0.0192   0.0160   0.0377   +1.04 -0.26 +1.23
        #   level_p25           0.0157   0.0251   0.0554   0.1158   +1.15 +1.14 +1.06
        #   p50 uncensored      0.0279   0.0394   0.0746   0.1415   +0.85 +0.92 +0.92
        #   p90 uncensored      0.1272   0.1352   0.1594   0.2077   +0.15 +0.24 +0.38
        #
        # p5 GOES DOWN between 0.65 and 1.30 -- the discriminator the whole
        # distribution verdict rests on is not monotonic in exposure, so it
        # cannot be solved for either. p25 is monotonic, and its exponent sits
        # within 15% of proportional over the whole range.
        #
        # WHY p25 AND NOT p50: p50 is monotonic too (+0.85..+0.92) but it sits
        # further up the tone curve, where AgX's shoulder is already bending;
        # p90 is ON the shoulder and is nearly inert (+0.15). p25 sits in the
        # shadow-to-midtone region where the transfer is still close to linear,
        # which is why its exponent is the flattest of the five. It is a
        # DERIVATION INSTRUMENT, not a verdict: nothing is scored against it.
        "level_p25": float(np.percentile(y, 25.0)),
        "clipped": float((y >= clip).sum() / n),
        "crushed": float((y < floor).sum() / n),
        "measurable": float(lit.size / n),
        # Mean linear RGB over the measurable pixels, so a frame that has gone
        # colourless -- the failure mode of an overexposed interior -- is
        # visible as a number rather than only by looking.
        "rgb": [float(lin[..., k][(y >= floor) & (y < clip)].mean())
                for k in range(3)],
    }


# What our renders sit at against the reference frames, and it is deliberately
# not 1.0. `grey level 1.webp` measures median linear luminance 0.0533 and our
# corridor at the calibrated ambient renders 0.0741 -- 1.40x. A film frame
# carries a grade, a stock and chroma subsampling; a render carries none of
# them. Matching a reference exactly would make every room darker than the one
# room in this project that has been looked at and judged, so the corridor's
# own offset is the target every other room is calibrated to.
RENDER_OFFSET = 1.40
# Wide, on purpose. The reference frames of one kind of space disagree with
# each other by more than this, and a gate tighter than the measurement it
# checks against is a gate that fails for being precise about noise.
TOL = 0.25


# ---------------------------------------------------------------------------
# THE DISTRIBUTION COMPARISON
# ---------------------------------------------------------------------------
# EVERY NUMBER BELOW IS MEASURED, and `--derive` recomputes all of them from
# CORPUS_JSON and refuses to agree if they have drifted. Do not hand-edit one.
# The derivation is in the module docstring and in the JSON's own `method`.
CORPUS_JSON = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "docs", "layer4-lighting",
    "frame_distribution.json")

# The quantile of the show-against-itself disagreement each band admits. 0.95
# rather than 1.0 because the maximum of 121 samples is one pair, not a
# tolerance; rather than 0.90 because at 0.90 the combined verdict rejects 27%
# of pairs the show itself produces, and a gate that fails a quarter of the
# reference material is measuring the material.
DIST_QUANTILE = 0.95
# |ln(ours / reference-at-our-offset)| may not exceed these. Keys are the keys
# `measure` returns.
DIST_BAND = {
    "dark_p5": 0.2548,      # x1.290
    "bright_p95": 1.1837,   # x3.266
    # p99 IS THE TIGHTER STATISTIC AND NOTHING WAS MEASURING IT. Derived from
    # the same 124 pairs by the same rule, it comes out at x2.581 -- the show
    # agrees with ITSELF more closely at p99 than at p95, which is the opposite
    # of what "further into the tail is noisier" would predict, and it is the
    # reason p95 is inert. p95 lands on ordinary practical light and every
    # interior has some; the small bright population above it is what a set
    # dresser put there, and it is consistent across the corpus.
    #
    # WHAT IT DOES NOT DO, stated because the first version of this comment
    # claimed it and the claim was false. `docs/reference-values.md` finds our
    # corridor's p99 at 0.16x the show's NORMALISED TO THE LIT WALL, which
    # would be |ln| = 1.83 against this band. That is a different measurement
    # from the one here: this file compares absolute p99 against the reference
    # re-exposed to our offset, exactly as it does p95, and on that convention
    # our two committed corridor frames come out at x2.17 (ad-hoc rig) and
    # x1.83 (shipped fittings) -- both INSIDE the band. So this row does not
    # currently fire on anything we have shipped.
    #
    # It earns its place anyway: same corpus, same pairs, same rule, and a
    # band 21% tighter than p95's, so it is strictly the more discriminating of
    # the two on the convention this file uses. A wall-normalised comparison is
    # a real gap and belongs here eventually, but it needs a wall to normalise
    # to, which means a region this tool does not currently take.
    "bright_p99": 0.9481,   # x2.581
    "ratio": 1.2172,        # x3.378
    "crushed": 2.4350,      # x11.42
}
# ...AND THE CRUSHED FRACTION MUST ALSO LIE INSIDE THE RANGE THE SHOW'S OWN
# FRAMES OCCUPY at our exposure, because the ratio test alone has a blind spot
# at both ends: against a reference that barely crushes, x11.52 of nearly
# nothing is still nearly nothing, and against one that crushes half the frame
# it permits a render that is 90% black. min and max of the corpus measured at
# gain RENDER_OFFSET: `corridor in alien sector.webp` 0.22% and
# `Minbari Flyer 969 in docking bay 17.webp` 63.92%.
CRUSHED_ENVELOPE = (0.0022, 0.6392)   # 0.22% .. 63.92%
# An absolute cap, because the corpus gives clipping no usable pairwise
# structure to derive a band from -- two show frames the median test calls
# equivalent disagree on clipped fraction by x53 at p90. This is the p95 of the
# corpus's own clipped fraction, measured at gain RENDER_OFFSET. It lands
# within 8% of the 4% threshold `report` already used, which was derived from
# our own lamp geometry -- two independent routes to the same number.
CLIPPED_CAP = 0.0369      # 3.69%

DIST_LABEL = {"dark_p5": "p5", "bright_p95": "p95", "bright_p99": "p99",
              "ratio": "p5/p95", "crushed": "crushed"}


def at_offset(ref_path, offset=RENDER_OFFSET, box=None):
    """The reference frame as it would measure at OUR exposure.

    The comparison the distribution verdict wants is about SHAPE, and our
    frames deliberately sit at `RENDER_OFFSET` of the show's level. Comparing
    raw p5 to raw p5 would charge us for that offset a second time, having
    already allowed it in the median check. So the reference is re-measured
    with its linear luminance scaled, by the same code, and everything is
    compared at x1.

    THIS IS NOT THE SAME AS MULTIPLYING THE REFERENCE'S STATISTICS BY 1.40,
    and the difference is the point: scaling the IMAGE lifts sub-floor pixels
    into the measurable set, where they arrive at the bottom and hold p5 down.
    `garden.png` p5 goes 0.0180 -> 0.0178 under a x1.40 gain, not to 0.0252.
    A frame with a black population keeps it when you brighten it, and that is
    exactly the property our renders do not have.
    """
    return measure(ref_path, gain=offset, box=box)


def distribution(m, ref):
    """Whole-distribution comparison. Returns (rows, ok).

    `ref` must be the reference measured at OUR offset -- see `at_offset`.
    Each row is (label, ours, theirs, x, ok, note); `x` and `ok` are None when
    the statistic has no population to compare and the row is reported rather
    than scored.
    """
    rows = []
    ok = True
    for k in ("dark_p5", "bright_p95", "bright_p99", "ratio", "crushed"):
        a, b = m[k], ref[k]
        if b <= 0.0:
            # The REFERENCE has no population, so there is no ratio to take
            # and nothing to compare against. Reported, not scored. Only
            # `crushed` can reach this: p5, p95 and their ratio are censored
            # at FLOOR and cannot be zero.
            rows.append((DIST_LABEL[k], a, b, None, None,
                         "reference has no population -- not scored"))
            continue
        if a <= 0.0:
            # OURS has none and the reference does. That is the defect this
            # comparison was built for, at its limit, and calling it
            # "unscored" would be the assertion that cannot fail.
            ok = False
            rows.append((DIST_LABEL[k], a, b, float("inf"), False,
                         "OURS IS EMPTY and the reference is not"))
            continue
        x = a / b
        good = abs(math.log(x)) <= DIST_BAND[k]
        ok = ok and good
        rows.append((DIST_LABEL[k], a, b, x, good,
                     f"band x{math.exp(DIST_BAND[k]):.2f}"))
    lo, hi = CRUSHED_ENVELOPE
    inside = lo <= m["crushed"] <= hi
    ok = ok and inside
    rows.append(("crushed in show range", m["crushed"], None, None, inside,
                 f"{lo * 100:.2f}%..{hi * 100:.2f}%"))
    under = m["clipped"] <= CLIPPED_CAP
    ok = ok and under
    rows.append(("clipped under cap", m["clipped"], None, None, under,
                 f"max {CLIPPED_CAP * 100:.2f}%"))
    return rows, ok


def report(m, against=None, offset=RENDER_OFFSET, tol=TOL, ref_at_offset=None):
    """Human-readable block, and whether it passes.

    `against` is another measurement -- a REFERENCE FRAME measured by this
    same function. See the module docstring for why nothing else is a valid
    comparison.

    `ref_at_offset` is the same reference frame put on our exposure, i.e.
    `at_offset(reference_path)`. Supply it and the whole-distribution verdict
    runs as well; omit it and only the median verdict does. It is a separate
    argument rather than something this function derives from `against`
    because a caller may be comparing crops, or a synthetic frame with no file
    behind it, and re-opening a path here would be guessing at both.
    """
    lines = [
        f"{m['path']}  {m['size']}",
        f"  ratio p5/p95    {m['ratio']:.3f}   (dark p5 {m['dark_p5']:.4f} / "
        f"bright p95 {m['bright_p95']:.4f})",
        f"  median          {m['median']:.4f}",
        f"  clipped         {m['clipped'] * 100:5.2f}%   "
        f"crushed {m['crushed'] * 100:5.2f}%   "
        f"measurable {m['measurable'] * 100:5.1f}%",
        f"  mean linear rgb {m['rgb'][0]:.3f} {m['rgb'][1]:.3f} "
        f"{m['rgb'][2]:.3f}",
    ]
    ok = True
    if against is not None:
        # MEDIAN, not the ratio. The ratio describes contrast and the median
        # describes level, and the defect this was built to catch -- a medlab
        # rendering as a white box -- is a level defect that leaves the ratio
        # looking respectable.
        x = m["median"] / against["median"] if against["median"] else 0.0
        ok = abs(x - offset) <= tol * offset
        lines.append(f"  vs {os.path.basename(against['path'])[:34]:34s} "
                     f"x{x:.2f} of its {against['median']:.4f}")
        lines.append(f"  target          x{offset:.2f} +/-{tol * 100:.0f}%"
                     f"   {'OK' if ok else 'OUT OF RANGE'}   "
                     f"[LEVEL ONLY -- a flat frame passes this]")
    # Overexposure is a separate verdict and has to be, because a blown frame
    # can have a perfectly good ratio: clipping raises both ends together.
    # Above 4%: the lit lamp geometry itself clips 1.3-3.1% in the rooms
    # measured so far and the corridor 1.8%, so the threshold sits above the
    # fittings and below anything that means a surface has gone.
    if m["clipped"] > 0.04:
        lines.append(f"  OVEREXPOSED     {m['clipped'] * 100:.2f}% of the "
                     f"frame is at or above {CLIP}")
        ok = False
    if ref_at_offset is not None:
        rows, dok = distribution(m, ref_at_offset)
        lines.append(f"  -- distribution vs "
                     f"{os.path.basename(ref_at_offset['path'])[:28]} at "
                     f"x{ref_at_offset['gain']:.2f} "
                     f"{'PASS' if dok else 'FAIL'} --")
        for label, a, b, x, good, note in rows:
            mark = "    " if good is None else (" OK " if good else "FAIL")
            if b is None:
                lines.append(f"  {mark} {label:22s} "
                             f"{a * 100:8.2f}%{'':10s} {note}")
            elif x is None:
                lines.append(f"  {mark} {label:22s} {a:9.4f} vs {b:9.4f}"
                             f"        {note}")
            else:
                lines.append(f"  {mark} {label:22s} {a:9.4f} vs {b:9.4f}"
                             f"  x{x:6.2f}  {note}")
        ok = ok and dok
    return "\n".join(lines), ok


def _quantile(sorted_vals, q):
    return sorted_vals[min(len(sorted_vals) - 1,
                           int(q * (len(sorted_vals) - 1)))]


def derive(corpus_json=CORPUS_JSON, root=None):
    """Recompute every constant above from the show's own frames.

    Returns a dict with the corpus measurements, the pair selection, the
    dispersion quantiles and the resulting bands. `--derive` runs this and
    exits non-zero if the module constants no longer match, so the numbers
    cannot quietly stop describing the corpus they claim to come from.
    """
    import itertools                                          # noqa: PLC0415
    # The repo root: the corpus's paths are `reference/...`, relative to it.
    root = root or os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(corpus_json))))
    doc = json.load(open(corpus_json))
    offset = doc.get("render_offset", RENDER_OFFSET)
    q = doc.get("quantile", DIST_QUANTILE)
    ms, gs = [], {}
    for e in doc["corpus"]:
        p = os.path.join(root, e["file"])
        m = measure(p)
        m["file"] = e["file"]
        m["class"] = e["class"]
        ms.append(m)
        gs[e["file"]] = measure(p, gain=offset)
    # THE PAIR RULE, and it is not a new judgement -- see the module docstring.
    # Two show frames whose medians agree within TOL are, by this project's
    # own existing standard, the same lighting register measured twice.
    # "Within TOL" read symmetrically: the brighter over the darker is at most
    # 1 + TOL. The median gate's own band is +/-TOL of its target multiple.
    pairs = [(a, b) for a, b in itertools.combinations(ms, 2)
             if max(a["median"], b["median"])
             / min(a["median"], b["median"]) <= 1.0 + TOL]
    disp, bands = {}, {}
    for k in ("dark_p5", "bright_p95", "bright_p99", "ratio", "crushed"):
        d = sorted(abs(math.log(max(a[k], 1e-5) / max(b[k], 1e-5)))
                   for a, b in pairs)
        disp[k] = {"n": len(d), "p50": _quantile(d, 0.50),
                   "p68": _quantile(d, 0.68), "p90": _quantile(d, 0.90),
                   "p95": _quantile(d, 0.95), "max": d[-1]}
        bands[k] = _quantile(d, q)
    cr = sorted(gs[e["file"]]["crushed"] for e in doc["corpus"])
    cl = sorted(gs[e["file"]]["clipped"] for e in doc["corpus"])
    return {
        "n_corpus": len(ms), "n_pairs": len(pairs),
        "n_possible": len(ms) * (len(ms) - 1) // 2,
        "quantile": q, "render_offset": offset,
        "dispersion": disp, "bands": bands,
        "crushed_envelope": [cr[0], cr[-1]],
        "clipped_cap": _quantile(cl, 0.95),
        "measurements": {m["file"]: {
            "class": m["class"], "size": m["size"],
            "median": m["median"], "dark_p5": m["dark_p5"],
            "bright_p95": m["bright_p95"], "bright_p99": m["bright_p99"],
            "ratio": m["ratio"],
            "crushed": m["crushed"], "clipped": m["clipped"],
            "at_offset": {k: gs[m["file"]][k] for k in
                          ("median", "dark_p5", "bright_p95", "bright_p99",
                           "ratio", "crushed", "clipped")}} for m in ms},
    }


def _check_derivation(verbose=True):
    """The bands still describe the corpus. Returns (ok, lines)."""
    d = derive()
    lines, ok = [], True
    def cmp(name, got, want, tol=5e-4):
        nonlocal ok
        good = abs(got - want) <= tol
        ok = ok and good
        lines.append(f"  {' OK ' if good else 'FAIL'} {name:26s} "
                     f"derived {got:.4f}  recorded {want:.4f}")
    for k in DIST_BAND:
        cmp(f"band {DIST_LABEL[k]}", d["bands"][k], DIST_BAND[k])
    cmp("crushed envelope lo", d["crushed_envelope"][0], CRUSHED_ENVELOPE[0])
    cmp("crushed envelope hi", d["crushed_envelope"][1], CRUSHED_ENVELOPE[1])
    cmp("clipped cap", d["clipped_cap"], CLIPPED_CAP)
    lines.insert(0, f"  corpus {d['n_corpus']} frames, {d['n_pairs']} of "
                    f"{d['n_possible']} pairs agree on median within "
                    f"+/-{TOL * 100:.0f}%, band = p{d['quantile'] * 100:.0f}")
    if verbose:
        print("\n".join(lines))
    return ok, lines


def _selftest():
    """Two synthetic frames, because the statistic has to be able to fail."""
    import tempfile
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    d = tempfile.mkdtemp()
    # A frame that is half mid-grey and half near-black: known ratio.
    a = np.zeros((100, 100, 3), dtype=np.uint8)
    a[:50] = 188                      # sRGB 0.737 -> linear ~0.5
    a[50:] = 89                       # sRGB 0.349 -> linear ~0.1
    p = os.path.join(d, "half.png")
    Image.fromarray(a).save(p)
    m = measure(p)
    check("p5 lands on the dark half", abs(m["dark_p5"] - 0.1) < 0.02,
          f"{m['dark_p5']:.4f}")
    check("p95 lands on the light half", abs(m["bright_p95"] - 0.5) < 0.03,
          f"{m['bright_p95']:.4f}")
    check("the ratio is the two levels", abs(m["ratio"] - 0.2) < 0.03,
          f"{m['ratio']:.4f}")
    check("nothing clips or crushes in a mid-grey frame",
          m["clipped"] == 0.0 and m["crushed"] == 0.0)
    # A blown frame: the overexposure verdict must fire, and it must fire
    # while the RATIO still looks fine, which is the whole reason it is a
    # separate verdict.
    b = np.full((100, 100, 3), 255, dtype=np.uint8)
    b[:50] = 188
    q = os.path.join(d, "blown.png")
    Image.fromarray(b).save(q)
    mb = measure(q)
    check("a blown half is counted as clipped",
          abs(mb["clipped"] - 0.5) < 0.01, f"{mb['clipped']:.3f}")
    _txt, okb = report(mb)
    check("the overexposure verdict fires", not okb)
    _txt, oka = report(m)
    check("and it does not fire on a clean frame", oka)
    # The comparison must fail when the level is wrong and pass when it is not.
    _t, far = report(m, against={"path": "x", "median": m["median"]})
    check("a frame at 1.0x its reference is OUT OF RANGE", not far)
    _t, near = report(m, against={"path": "x",
                                  "median": m["median"] / RENDER_OFFSET})
    check("a frame at the render offset passes", near)

    # -- the distribution verdict, and every band demonstrated FAILING ------
    # A gate that cannot fail is worse than no gate, so each of these breaks
    # the thing the band guards and watches. The base frame is built to look
    # like a show frame does: a large black population under the measurable
    # floor, a lit body, and a small bright population.
    def save(lin, name):
        """A synthetic frame from LINEAR luminance, written as sRGB."""
        s = np.where(lin <= 0.0031308, lin * 12.92,
                     1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055)
        b = np.clip(np.round(s * 255.0), 0, 255).astype(np.uint8)
        p = os.path.join(d, name)
        Image.fromarray(np.dstack([b, b, b])).save(p)
        return p

    n = 200
    base = np.full((n, n), 0.10)
    base[:60] = 0.002          # 30% under the floor: a show-like black field
    base[60:80] = 0.030        # the shadow shelf p5 lands on
    base[190:] = 0.62          # the bright end p95 lands on
    ref_p = save(base, "showlike.png")
    r0 = measure(ref_p)
    check("the synthetic reference is show-like",
          0.25 < r0["crushed"] < 0.35 and r0["clipped"] == 0.0,
          f"crushed {r0['crushed']:.3f} clipped {r0['clipped']:.3f}")
    # AT x1.0 A FRAME MATCHES ITSELF. Offset 1.0 makes `at_offset` the
    # identity, so every statistic is exactly x1 and the verdict must pass.
    self_ref = at_offset(ref_p, 1.0)
    _t, okself = report(r0, r0, 1.0, TOL, self_ref)
    check("a frame compared with itself passes every band", okself)

    # 1. LIFTED BLACKS -- the defect this whole comparison exists for. The
    #    black field is raised to just above the floor and nothing else moves.
    #    The frame is now flat, and the MEDIAN CHECK STILL PASSES.
    flat = base.copy()
    flat[:60] = 0.0125
    fp = save(flat, "flat.png")
    mflat = measure(fp)
    ratio_ref = at_offset(ref_p, 1.0)
    xm = mflat["median"] / r0["median"]
    check("lifting the blacks leaves the median inside its band",
          abs(xm - 1.0) <= TOL, f"x{xm:.3f}")
    rows, dok = distribution(mflat, ratio_ref)
    check("...and the distribution verdict fails it", not dok)
    got = {r[0]: r[4] for r in rows}
    check("p5 is the band that catches it", got["p5"] is False,
          f"p5 {mflat['dark_p5']:.4f} vs {ratio_ref['dark_p5']:.4f}")
    check("crushed catches it too", got["crushed"] is False,
          f"{mflat['crushed']:.4f} vs {ratio_ref['crushed']:.4f}")
    # 2. THE p5 BAND ALONE. Raise only the shadow shelf, leaving the black
    #    field intact, so crushed is unchanged and only p5 moves.
    shelf = base.copy()
    shelf[60:80] = 0.030 * math.exp(DIST_BAND["dark_p5"]) * 1.15
    ms = measure(save(shelf, "shelf.png"))
    rows, dok = distribution(ms, ratio_ref)
    got = {r[0]: r[4] for r in rows}
    check("the p5 band fires on a lifted shadow shelf alone",
          got["p5"] is False and got["crushed"] is True, str(got))
    shelf[60:80] = 0.030 * 1.10           # inside the band
    rows, _ = distribution(measure(save(shelf, "shelf_ok.png")), ratio_ref)
    check("...and not on a shelf inside the band",
          {r[0]: r[4] for r in rows}["p5"] is True)
    # 3. THE p95 BAND. Crush the bright end by more than x3.285 and nothing
    #    else. It is the loosest band in the set and it must still fire.
    dull = base.copy()
    dull[190:] = 0.62 / (math.exp(DIST_BAND["bright_p95"]) * 1.15)
    rows, _ = distribution(measure(save(dull, "dull.png")), ratio_ref)
    got = {r[0]: r[4] for r in rows}
    check("the p95 band fires when the highlights are gone",
          got["p95"] is False, str(got))
    # 4. THE p5/p95 BAND, and it needs its own case because it is the one
    #    statistic that can fail while BOTH of its own terms pass: the bands
    #    are x1.224 and x3.285, whose product 4.02 exceeds the ratio's x3.415.
    both = base.copy()
    both[60:80] = 0.030 * 1.20                          # p5 up, inside band
    both[190:] = 0.62 / 3.20                            # p95 down, in band
    rows, _ = distribution(measure(save(both, "both.png")), ratio_ref)
    got = {r[0]: r[4] for r in rows}
    check("p5/p95 fails while p5 and p95 each pass -- the band is not "
          "redundant", got["p5/p95"] is False and got["p5"] is True
          and got["p95"] is True, str(got))
    # 5. THE CRUSHED ENVELOPE, both ends. The ratio band cannot see either:
    #    against a reference that crushes 30%, x11.52 permits 2.6% to 100%.
    allblack = base.copy()
    allblack[60:190] = 0.002
    rows, _ = distribution(measure(save(allblack, "allblack.png")), ratio_ref)
    got = {r[0]: r[4] for r in rows}
    check("a 95%-black frame is outside the show's crushed range",
          got["crushed in show range"] is False, str(got))
    check("...and its crushed RATIO is inside the band, which is why the "
          "envelope exists", got["crushed"] is True)
    # 6. THE CLIPPED CAP.
    blownf = base.copy()
    blownf[180:] = 3.0
    rows, _ = distribution(measure(save(blownf, "blownf.png")), ratio_ref)
    got = {r[0]: r[4] for r in rows}
    check("the clipped cap fires at 10% blown",
          got["clipped under cap"] is False, str(got))
    # 7. THE BANDS STILL DESCRIBE THE CORPUS. `--derive` recomputes them from
    #    the show's frames; if it stops agreeing, the tolerances have come
    #    adrift from their derivation and nothing above means anything.
    if os.path.exists(CORPUS_JSON):
        good, _lines = _check_derivation(verbose=False)
        check("DIST_BAND, CRUSHED_ENVELOPE and CLIPPED_CAP still match the "
              "corpus they were derived from", good)
        saved = DIST_BAND["dark_p5"]
        try:
            DIST_BAND["dark_p5"] = saved * 1.5
            bad, _l = _check_derivation(verbose=False)
            check("...and that check FAILS when a band is moved", not bad)
        finally:
            DIST_BAND["dark_p5"] = saved
    # 8. `level_p25` IS MONOTONE IN GAIN WHERE THE MEDIAN IS NOT, and this is
    #    the assertion INV-150 rests on, built as the case with the defect IN
    #    it rather than the case without. The frame is show-like: a large black
    #    field under the measurable floor, a lit body, a bright end. Raising
    #    the exposure RECRUITS that black field into the measurable set from
    #    the bottom, which is what drags the censored median down against the
    #    light that lifted it.
    #
    #    Built to fire: the black field sits just under FLOOR, so a modest gain
    #    lifts a large population across it all at once.
    recruit = np.full((n, n), 0.30)
    recruit[:150] = 0.0085          # 75% of the frame, just under the 0.010 floor
    recruit[150:180] = 0.40
    rp_ = save(recruit, "recruit.png")
    m10 = measure(rp_, gain=1.0)
    m14 = measure(rp_, gain=1.4)
    check("the censored median goes DOWN when the gain goes UP",
          m14["median"] < m10["median"],
          f"{m10['median']:.4f} -> {m14['median']:.4f}")
    check("...and level_p25 goes up, which is why it is what an exposure is "
          "solved from", m14["level_p25"] > m10["level_p25"],
          f"{m10['level_p25']:.4f} -> {m14['level_p25']:.4f}")
    # ...AND THE CONTROL FOR THE CONTROL. On a frame with no sub-floor
    # population to recruit there is nothing for the censoring to do, and BOTH
    # statistics track the gain. If this case also showed the median falling,
    # the one above would be measuring the synthesis rather than the effect.
    plain = np.full((n, n), 0.30)
    plain[:60] = 0.10
    pp_ = save(plain, "plain.png")
    q10, q14 = measure(pp_, gain=1.0), measure(pp_, gain=1.4)
    check("with nothing under the floor the median tracks the gain too",
          q14["median"] > q10["median"] and q14["level_p25"] > q10["level_p25"],
          f"median {q10['median']:.4f} -> {q14['median']:.4f}")
    # 9. THE BOX. It has to actually select, or every crop comparison in
    #    export_scene is measuring the whole sheet and saying it is a crop.
    top = measure(ref_p, box=(0.0, 0.0, 1.0, 0.35))
    check("a box measures only its box",
          abs(top["crushed"] - 60 / 70) < 0.02
          and abs(measure(ref_p)["crushed"] - 0.30) < 0.02,
          f"{top['crushed']:.3f} vs whole-frame "
          f"{measure(ref_p)['crushed']:.3f}")
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def _box(s):
    v = tuple(float(x) for x in s.split(","))
    if len(v) != 4:
        raise argparse.ArgumentTypeError("box is LEFT,TOP,RIGHT,BOTTOM "
                                         "as fractions")
    return v


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("png", nargs="*")
    ap.add_argument("--against", metavar="PNG",
                    help="reference frame to compare against, measured by "
                         "this same code -- the ONLY valid comparison, see "
                         "the module docstring")
    ap.add_argument("--offset", type=float, default=RENDER_OFFSET)
    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--box", type=_box, metavar="L,T,R,B",
                    help="measure only this fraction of OUR frame")
    ap.add_argument("--against-box", type=_box, metavar="L,T,R,B",
                    help="measure only this fraction of the reference")
    ap.add_argument("--median-only", action="store_true",
                    help="the old comparison alone: level, no distribution. "
                         "It is not wrong, it is insufficient -- a flat frame "
                         "passes it. Here so the two can be seen apart")
    ap.add_argument("--derive", action="store_true",
                    help="recompute DIST_BAND, CRUSHED_ENVELOPE and "
                         "CLIPPED_CAP from the show frames in "
                         "docs/layer4-lighting/frame_distribution.json and "
                         "exit non-zero if the module's constants no longer "
                         "match. A tolerance that has come adrift from its "
                         "corpus is a guess with a decimal point")
    a = ap.parse_args(argv)
    if a.derive:
        good, _ = _check_derivation()
        return 0 if good else 1
    if not a.png:
        return _selftest()
    ref = measure(a.against, box=a.against_box) if a.against else None
    rat = (None if (ref is None or a.median_only)
           else at_offset(a.against, a.offset, box=a.against_box))
    bad = 0
    for p in a.png:
        text, ok = report(measure(p, box=a.box), ref, a.offset, a.tol, rat)
        print(text)
        bad += 0 if ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
