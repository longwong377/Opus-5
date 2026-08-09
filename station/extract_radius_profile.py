#!/usr/bin/env python3
"""Extract the station's radius profile from the Miller top view.

The hull is very nearly a surface of revolution, so a top-view half-height
profile plus the longitudinal framework fully defines it.

The drawing is polluted by ~26 label leader lines crossing the hull, which a
naive outermost-ink read would follow straight off the hull and into the label
row. Leader lines are thin and steeply diagonal; the hull outline is a strong,
near-horizontal, continuous boundary. Rejection therefore works on continuity:
take the raw outermost ink per column, median-filter it, and discard columns
whose raw value departs from the local median by more than a tolerance.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

SRC = "/home/user/Opus-5/reference/02-station-cutaways-and-plans/other map 4.jpg"
SCRATCH = "/tmp/claude-0/-home-user-Opus-5/25a39def-a001-5e33-8111-81bbb68b9aec/scratchpad/zoom"
OUT = "/home/user/Opus-5/station/schema/radius_profile.json"

TAIL_PX, NOSE_PX, AXIS_PY = 71, 2048, 388
MILLER_L = 3108.0
K = 2.5891                      # Miller -> real scale
DRAW_TOP, DRAW_BOT = 250, 520   # vertical window containing the hull, excluding label rows
INK = 100
MEDIAN_WIN = 41
TOL_PX = 14

# Regions of the sheet that are not line art and must not be read as hull:
# the EarthForce badge and the inset photograph of the reactor section, both of
# which are dark enough to threshold as ink and sit directly above the drawing.
MASKS = [
    (0, 150, 190, 330),      # "5" squadron badge, upper left
    (225, 150, 420, 330),    # inset render of the aft reactor assembly
]


MIN_RUN = 5


def strip_leader_lines(a):
    """Keep only ink belonging to a horizontal run of at least MIN_RUN pixels.

    The ~26 label leader lines are steep thin diagonals: each crosses any given
    row in 1-3 pixels. The hull outline is near-horizontal and crosses each row
    in long runs. A horizontal run-length threshold separates them cleanly,
    where per-column outlier rejection cannot -- in wide stretches of the sheet
    the leader lines outnumber the hull, so they *are* the local median.
    """
    out = np.zeros_like(a)
    for r in range(a.shape[0]):
        row = a[r]
        if not row.any():
            continue
        idx = np.flatnonzero(row)
        splits = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
        for run in splits:
            if run.size >= MIN_RUN:
                out[r, run] = True
    return out


STEP_THRESHOLD_PX = 4.0   # a radius jump this large is real geometry, not noise
SMOOTH_WIN = 9


def median_filter(v, win):
    h = win // 2
    pad = np.pad(v, h, mode="edge")
    return np.array([np.median(pad[i:i + win]) for i in range(len(v))])


def edge_preserving_smooth(v):
    """Kill oscillation without rounding off genuine section transitions.

    The raw trace flips gradient sign on ~20% of samples -- the outermost
    horizontal run in a column is sometimes an internal detail line rather than
    the hull outline, so the radius wobbles by a few metres. Lathed into a
    surface of revolution that wobble becomes visible rings.

    A plain low-pass would also round off the real steps: the reactor drum
    edge, the generator torus flare, the section transitions. So detect step
    edges first, then smooth only *between* them, leaving the steps sharp.
    """
    steps = np.flatnonzero(np.abs(np.diff(v)) > STEP_THRESHOLD_PX) + 1
    bounds = np.concatenate(([0], steps, [len(v)]))
    out = v.copy()
    h = SMOOTH_WIN // 2
    for a, b in zip(bounds, bounds[1:]):
        seg = v[a:b]
        if seg.size < 3:
            continue
        pad = np.pad(seg, h, mode="edge")
        kern = np.ones(SMOOTH_WIN) / SMOOTH_WIN
        out[a:b] = np.convolve(pad, kern, mode="valid")[:seg.size]
    return out


def main():
    a = np.asarray(Image.open(SRC).convert("L")) < INK
    for x0, y0, x1, y1 in MASKS:
        a[y0:y1, x0:x1] = False
    a = strip_leader_lines(a)
    px_per_miller_m = (NOSE_PX - TAIL_PX) / MILLER_L
    real_m_per_px = (MILLER_L * K) / (NOSE_PX - TAIL_PX)

    xs = np.arange(TAIL_PX, NOSE_PX + 1)
    raw_up, raw_dn = [], []
    for x in xs:
        col = a[DRAW_TOP:DRAW_BOT, x]
        rows = np.flatnonzero(col) + DRAW_TOP
        if rows.size == 0:
            raw_up.append(np.nan)
            raw_dn.append(np.nan)
            continue
        above = rows[rows < AXIS_PY]
        below = rows[rows > AXIS_PY]
        raw_up.append(AXIS_PY - above.min() if above.size else np.nan)
        raw_dn.append(below.max() - AXIS_PY if below.size else np.nan)

    raw_up = np.array(raw_up, dtype=float)
    raw_dn = np.array(raw_dn, dtype=float)

    def clean(raw):
        filled = np.where(np.isnan(raw), np.nanmedian(raw), raw)
        med = median_filter(filled, MEDIAN_WIN)
        keep = np.abs(filled - med) <= TOL_PX
        out = np.where(keep, filled, med)
        return median_filter(out, 11), keep

    up, keep_up = clean(raw_up)
    dn, keep_dn = clean(raw_dn)
    # The hull is symmetric about the axis; averaging the two halves suppresses
    # residual leader-line bias that survived on one side only.
    half_px = edge_preserving_smooth((up + dn) / 2.0)

    profile = [
        {
            "z_m": round((x - TAIL_PX) * real_m_per_px, 1),
            "radius_m": round(h * real_m_per_px, 1),
        }
        for x, h in zip(xs, half_px)
    ]

    rejected = int((~keep_up).sum() + (~keep_dn).sum())
    report = {
        "source": os.path.basename(SRC),
        "calibration": {
            "px_per_miller_m": round(px_per_miller_m, 4),
            "real_m_per_px": round(real_m_per_px, 4),
            "k": K,
        },
        "samples": len(profile),
        "columns_rejected_as_leader_lines": rejected,
        "smoothing": {"step_threshold_px": STEP_THRESHOLD_PX, "window": SMOOTH_WIN},
        "rejection_rate": round(rejected / (2 * len(xs)), 4),
        "max_radius_m": round(float(np.max(half_px)) * real_m_per_px, 1),
        "max_radius_at_z_m": round(float(xs[int(np.argmax(half_px))] - TAIL_PX) * real_m_per_px, 1),
        "profile": profile,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)

    # Overlay the accepted profile back onto the drawing for visual verification.
    ov = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(ov)
    for x, h in zip(xs, half_px):
        d.point((x, AXIS_PY - h), fill=(255, 0, 0))
        d.point((x, AXIS_PY + h), fill=(255, 0, 0))
    d.line([(0, AXIS_PY), (ov.size[0], AXIS_PY)], fill=(0, 160, 255), width=1)
    ov.crop((0, 150, ov.size[0], 620)).resize((2625, 587), Image.LANCZOS).save(
        os.path.join(SCRATCH, "radius_overlay.png"))

    print(json.dumps({k: v for k, v in report.items() if k != "profile"}, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
