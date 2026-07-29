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

The consequence worth stating: this measures a frame, not a room. Point the
camera at a wall and it will report whatever that wall does. It is a
regression gate on a FIXED shot, which is what the render scripts produce.
"""

import argparse
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


def measure(path, clip=CLIP, floor=FLOOR):
    """Luminance statistics for one frame, as a dict."""
    img = Image.open(path).convert("RGB")
    a = np.asarray(img, dtype=np.float64) / 255.0
    lin = srgb_to_linear(a)
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
        "ratio": lo / hi if hi > 0 else 0.0,
        "dark_p5": lo,
        "bright_p95": hi,
        "median": float(np.median(lit)),
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


def report(m, against=None, offset=RENDER_OFFSET, tol=TOL):
    """Human-readable block, and whether it passes.

    `against` is another measurement -- a REFERENCE FRAME measured by this
    same function. See the module docstring for why nothing else is a valid
    comparison.
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
                     f"   {'OK' if ok else 'OUT OF RANGE'}")
    # Overexposure is a separate verdict and has to be, because a blown frame
    # can have a perfectly good ratio: clipping raises both ends together.
    # Above 4%: the lit lamp geometry itself clips 1.3-3.1% in the rooms
    # measured so far and the corridor 1.8%, so the threshold sits above the
    # fittings and below anything that means a surface has gone.
    if m["clipped"] > 0.04:
        lines.append(f"  OVEREXPOSED     {m['clipped'] * 100:.2f}% of the "
                     f"frame is at or above {CLIP}")
        ok = False
    return "\n".join(lines), ok


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
    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("png", nargs="*")
    ap.add_argument("--against", metavar="PNG",
                    help="reference frame to compare against, measured by "
                         "this same code -- the ONLY valid comparison, see "
                         "the module docstring")
    ap.add_argument("--offset", type=float, default=RENDER_OFFSET)
    ap.add_argument("--tol", type=float, default=TOL)
    a = ap.parse_args(argv)
    if not a.png:
        return _selftest()
    ref = measure(a.against) if a.against else None
    bad = 0
    for p in a.png:
        text, ok = report(measure(p), ref, a.offset, a.tol)
        print(text)
        bad += 0 if ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
