#!/usr/bin/env python3
"""LOD chain for the exterior hull: three independent schedules, each derived.

A Starfury sees the station from 50 m and from 50 km in the same flight. At
50 km the whole 8 km hull covers a few hundred pixels, so 327,000 triangles is
roughly a thousand triangles per visible pixel -- waste, and worse than waste,
because it is bandwidth stolen from whatever is near the camera. Godot has no
Nanite (ADR 0001), so LOD is ours to build.

WHY THREE SCHEDULES AND NOT ONE
-------------------------------
The previous chain stepped `radial_segments`, `z_stride` and `greeble_detail`
together in a single LEVELS table and derived every switch distance from ONE
error: the radial silhouette sagitta. Measuring the other two showed the table
was wrong by an order of magnitude in both:

    knob            old switch    honest switch (measured)   error
    radial 32       6,000 m       6,002 m                    correct
    z-stride 2      6,000 m       49,204 m                   8.2x too early
    greeble 0.45    6,000 m       73,249 m                   12.2x too early

They cannot share a table because they are not the same quantity and they do
not become acceptable at the same distance. That is the whole change.

THE ERROR EACH SCHEDULE INTRODUCES, AND HOW IT IS OBTAINED
----------------------------------------------------------
`CONTRIBUTING.md` records this project sizing LOD distances against facet
WIDTH when what causes a visible pop on a body of revolution is the SAGITTA
`r(1-cos(pi/n))`. The lesson is not about circles: it is that a switch
distance must come from the quantity that actually changes on screen, and
that quantity must be measured rather than reasoned about. Applied to all
three:

* SILHOUETTE (radial segments). Error = the sagitta, computed at the model's
  true maximum radius, which is taken from the built components rather than
  from the profile -- the widest thing on the station is the comms grid pylon
  tip at 1,210.9 m and the lathe alone never reaches it.

* LONGITUDINAL (z stride). `generate_hull.build()` decimates with
  `profile[::z_stride]`, so the surface between two kept samples is the
  straight chord and every dropped sample's true radius is the error. This is
  MEASURED sample by sample against `radius_profile.json`, not modelled. It is
  large and it is local: the profile ramps 135.4 -> 227.9 -> 321.6 -> 417.2 m
  across three samples at the drum's aft shoulder (z = 3126..3138), so stride 2
  drops z = 3138.2 and cuts 47.8 m off that corner. Uniform striding is simply
  the wrong tool on a profile with steps in it; see "WHAT WOULD FIX IT,
  AS A SPECIFICATION" below.

* GREEBLE (instance fraction). Error = the RELIEF of the largest piece the cull
  removes -- how far it stands proud of the hull, which is the greeble pass's
  own sagitta. MEASURED off the built greeble geometry: every connected piece
  is found by union-find and its relief taken as the point-to-surface distance
  in the (z, r) plane, `(r_v - R(z_v)) / sqrt(1 + slope^2)`. The plane form
  matters -- a plain radial difference reads 297 m on a section transition
  where the hull is 23:1 steep and the surface normal is nearly axial.

TWO PIXEL BUDGETS, AND THEY ANSWER DIFFERENT QUESTIONS
------------------------------------------------------
`PIXEL_BUDGET` (1.5 px) is the DEVIATION budget: how far the picture may move
when a level is swapped in. It is unchanged from the old chain and
`drum_ground.py` mirrors it deliberately.

`SHADING_SAMPLE_PX` (1.0 px) is new and is a different question: at what size
does a level's own detail stop being resolvable at all. Derived, not chosen.
`project.godot` runs 4x MSAA, which supersamples COVERAGE 2x in each axis but
still shades once per covered fragment per pixel; so the finest feature the
frame can resolve as form rather than as a coin-flip is one final pixel wide,
whatever the MSAA level. What would overturn it: supersampling, per-sample
shading, or a TAA resolve, all of which move the shading rate.

Every level therefore carries BOTH numbers: `honest_from_m` (it may be used
from here outward) and `aliases_beyond_m` (its own detail is sub-pixel past
here). Where a level is the coarsest honest option and is already past its
aliasing distance, the chain has a GAP -- it is drawing detail nobody can
resolve because nothing coarser is yet accurate enough. Gaps are reported per
level rather than hidden, because the previous chain's gap is what put white
salt-and-pepper over the whole hull in `docs/engine-exterior.png`.

WHAT THE SPECKLE ACTUALLY IS -- SIX RENDERS, ONE CAMERA
--------------------------------------------------------
The white salt-and-pepper over `docs/engine-exterior.png` was measured by
differencing each frame against its own 5x5 median and counting hull pixels more
than 60/765 of luminance away from it. Six engine frames were rendered at ONE
camera -- orbit 6,400 m, elev 15, az 208, fov 42, 1280x720, the camera in
`tools/build_and_render.sh` -- with only the mesh changing:

    level   segs/stride/greeble   triangles   greeble tris   speckled px
    lod0        64 / 1 / 1.00       327,346        70,778        5.72%
    lod1        32 / 1 / 1.00       200,754        70,778        5.89%
    lod2        16 / 1 / 1.00       137,458        70,778        6.24%
    lod3        16 / 2 / 1.00       105,810        70,778        6.06%
    lod4        16 / 4 / 1.00        90,002        70,778        6.11%
    lod5        16 / 4 / 0.00        19,224             0        1.92%

Two things fall out and they point in opposite directions from what the LOD
chain can do.

**Decimating the hull does nothing.** lod0 through lod4 span a 3.6x range of
triangles and the speckle does not move -- it rises slightly, because coarser
facets make bigger normal steps. So no choice of switch distance in this file
was ever going to remove it.

**The greebles are the speckle.** lod4 and lod5 are the SAME hull geometry with
surface detail on and off: 6.11% falls to 1.92%. The fittings carry roughly 69%
of it, and the residual 1.9% is the lathe's own section transitions and plating
bevels. Session 3a's diagnosis was right and this file now has the controlled
pair that proves it.

WHAT WOULD FIX IT, AS A SPECIFICATION
--------------------------------------
Not this file, and not a switch distance. `--greeble-detail` culls by FRACTION
over a population whose relief runs from 1.7 m panels to 72 m antenna masts, so
every fractional level drops a mast and is dishonest until 73 km. That is why
the greeble schedule below collapses to two useful entries.

What the chain wants is a cull graded by RELIEF, smallest first, with the
threshold set by the distance:

    threshold(d) = d / _px_scale(SHADING_SAMPLE_PX)

Such a cull removes only pieces already under one pixel of relief at d, and one
pixel is inside the 1.5 px deviation budget, so it is honest at exactly the
distance it was computed for and pops nothing -- which no fraction cull can
manage at any distance. `relief_cull_proposal()` derives the table; the report
prints it. It needs one flag on `generate_hull.py`, and `greeble.py` already
has the shape of it in `SATELLITE_CUTOFF`, welded to the same float as the
fraction.

The second change, smaller but real: curvature-adaptive longitudinal decimation
in `generate_hull.py`. Uniform striding drops 47.8 m off the drum's aft shoulder
at stride 2, which is why the longitudinal schedule cannot help before 49 km.
Half of all profile intervals have EXACTLY zero slope change; ~20 carry real
section transitions. Keeping the transitions and dropping the flats would bring
the chord error under a metre and make longitudinal decimation honest from a few
hundred metres.

Run `python3 station/lod.py` for the self-test, `--build` to regenerate the
chain, `--report` for the derivation without touching any file.
"""
import argparse
import json
import math
import os
import statistics
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATION = os.path.join(ROOT, "station")
GENERATED = os.path.join(STATION, "generated")
if STATION not in sys.path:
    sys.path.insert(0, STATION)


# ---------------------------------------------------------------------------
# The screen model. Everything downstream is a ratio against these four.
# ---------------------------------------------------------------------------
FOV_DEG = 50.0
SCREEN_H = 1440

# Deviation budget: how far the picture may move when a level is swapped in.
# Unchanged from the chain this replaces; drum_ground.py mirrors the value and
# says so, so changing it here silently would desynchronise two chains.
PIXEL_BUDGET = 1.5

# Shading-rate budget. See the module docstring: 4x MSAA supersamples coverage,
# not shading, so one final pixel is the floor at which a feature can read as
# form rather than as a sub-pixel coin flip.
SHADING_SAMPLE_PX = 1.0

# The chain does not need to describe distances the camera cannot see from.
# Taken from the exterior camera's far plane in tools/export_scene.py rather
# than chosen, so the two cannot drift.
FAR_PLANE_M = 200_000.0


def _px_scale(budget_px):
    """Metres of viewing distance per metre of feature, at `budget_px`.

    A feature `s` metres across subtends `budget_px` pixels at
    `s * _px_scale(budget_px)` metres. One function, two budgets, so a change
    of FOV or resolution cannot move one criterion and not the other.
    """
    return SCREEN_H / (budget_px * 2.0 * math.tan(math.radians(FOV_DEG) / 2.0))


def honest_from_m(error_m):
    """Distance beyond which `error_m` of geometric error is under budget."""
    return max(0.0, error_m) * _px_scale(PIXEL_BUDGET)


def aliases_beyond_m(feature_m):
    """Distance beyond which `feature_m` of detail is below the shading rate."""
    return max(0.0, feature_m) * _px_scale(SHADING_SAMPLE_PX)


# ---------------------------------------------------------------------------
# The three schedules. Only the OPTIONS are authored; every distance is derived.
# ---------------------------------------------------------------------------
# Powers of two so each level's ring and segment indices are a subset of the
# finer level's -- a switch removes vertices rather than moving them, which is
# the stable-subset property `greeble.py` and `drum_ground.py` also hold.
SILHOUETTE_STEPS = (64, 32, 16, 8)
LONGITUDINAL_STEPS = (1, 2, 4, 8)

# Greeble detail is a fraction of instances kept (generate_hull --greeble-detail).
# 0.89 is included because it is the largest value below greeble.SATELLITE_CUTOFF
# and therefore the only SIZE-graded step the generator can express; the
# derivation below shows what that costs.
GREEBLE_STEPS = (1.0, 0.89, 0.45, 0.12, 0.0)

# Canon station length (canon/00-MASTER.md; the profile's own z extent is
# 8,046.9 m). Used only to say how much further away a level's FAR end is than
# the near point that selected it.
STATION_LENGTH_M = 8046.9

# A fitting cannot stand further proud than the tallest thing the generator
# builds, which is `greeble._antenna_stub`'s mast at rng.span(32.0, 72.0) m.
# Anything above this has left the hull and is a defect, not detail; letting a
# defect set an LOD switch distance would be the tail wagging the dog. Two such
# pieces exist today (greeble_panel at z = 3112.4 and z = 3125.0, both beside
# the z = 3138 section transition, standing 282 m and 267 m off the hull --
# `HullSurface.slope_at` smooths over +/-3 samples and reads 0.33 where the true
# step is nearly vertical, so the tangent frame is wrong and the row flies off).
# The count is gated so it cannot grow unnoticed.
RELIEF_SANITY_M = 72.0
OFF_HULL_PIECES_EXPECTED = 2


def _load():
    import yaml
    with open(os.path.join(STATION, "schema/station.yaml")) as f:
        schema = yaml.safe_load(f)
    with open(os.path.join(STATION, "schema/radius_profile.json")) as f:
        profile = json.load(f)
    return schema, profile


def model_max_radius(schema, profile):
    """Largest radius anywhere in the model, lathe and components together.

    Computed rather than read out of `hull_manifest.json`, so the derivation
    runs on a bare checkout and cannot be poisoned by a manifest another
    process left describing a decimated level -- the exact failure the restore
    dance in `build()` exists to prevent.
    """
    import components as components_mod
    r = max(s["radius_m"] for s in profile["profile"])
    for _gid, (verts, _tris) in components_mod.build_all(
            schema.get("components", []), profile["profile"]).items():
        for x, y, _z in verts:
            r = max(r, math.hypot(x, y))
    return r


# --- silhouette -------------------------------------------------------------

def silhouette_schedule(schema, profile):
    """Radial decimation. Error is the sagitta; feature is the facet width.

    Sagitta at the MAXIMUM radius because that is where the outline error is
    worst and a switch distance is a worst-case statement. Facet width at the
    MEAN radius because the aliasing question is about the typical quad, and
    the station is 1,211 m wide in one place and under 200 m over most of its
    length.

    Note the BASELINE. The other two schedules measure their error against the
    finest option, so their finest option has zero error and is honest from
    zero. This one measures against the true surface of revolution, because a
    64-gon is not a circle and pretending it is would hide the chain's quality
    floor: the 64-gon's own sagitta is over the deviation budget inside
    `honest_from_m(sagitta(64))`, and there is nothing finer to switch to. That
    floor is recorded in the manifest rather than assumed away.
    """
    r_max = model_max_radius(schema, profile)
    r_mean = statistics.fmean(s["radius_m"] for s in profile["profile"])
    out = []
    for n in SILHOUETTE_STEPS:
        # Rounded BEFORE the distance is derived from it, so the two numbers
        # printed in the manifest are consistent with each other and a reader
        # can check one against the other with a calculator. Deriving from the
        # unrounded value and publishing the rounded one puts a 1 m disagreement
        # in the file that looks like a bug and is not.
        sagitta = round(r_max * (1.0 - math.cos(math.pi / n)), 3)
        facet = round(2.0 * r_mean * math.sin(math.pi / n), 2)
        out.append({
            "radial_segments": n,
            "error_m": sagitta,
            "error_baseline": "true surface of revolution",
            "error_source": f"sagitta r(1-cos(pi/n)) at r={r_max:.2f} m",
            "honest_from_m": round(honest_from_m(sagitta)),
            "feature_m": facet,
            "feature_source": f"facet width 2r sin(pi/n) at mean r={r_mean:.1f} m",
            "aliases_beyond_m": round(aliases_beyond_m(facet)),
        })
    return out


# --- longitudinal -----------------------------------------------------------

def longitudinal_schedule(profile):
    """Z decimation. Error is MEASURED against the traced profile.

    `generate_hull.build()` keeps `profile[::stride]` and lathes straight bands
    between kept samples, so the error at a dropped sample is exactly its
    distance from the chord of its kept neighbours. Nothing here is modelled;
    the loop walks every dropped sample of every stride.

    A second, smaller error is recorded too: striding drops up to stride-1
    samples off the tail, so the hull gets shorter. That is why the old
    manifest reported 8,042.9 m for lod1..3 against 8,046.9 m for lod0, and
    why `validate.py` has a note about a stale manifest failing the canon
    length check.
    """
    samples = profile["profile"]
    z = [s["z_m"] for s in samples]
    r = [s["radius_m"] for s in samples]
    spacing = (z[-1] - z[0]) / (len(z) - 1)
    out = []
    for stride in LONGITUDINAL_STEPS:
        worst, at = 0.0, None
        for i in range(0, len(r) - stride, stride):
            for k in range(1, stride):
                t = k / stride
                e = abs(r[i + k] - (r[i] * (1.0 - t) + r[i + stride] * t))
                if e > worst:
                    worst, at = e, z[i + k]
        kept = len(samples[::stride])
        lost = z[-1] - samples[::stride][-1]["z_m"]
        worst = round(worst, 3)
        feature = round(spacing * stride, 3)
        out.append({
            "z_stride": stride,
            "rings": kept,
            "error_m": worst,
            "error_baseline": "the traced profile, i.e. stride 1",
            "error_source": ("max distance from a dropped profile sample to the "
                             "chord of its kept neighbours"
                             + (f", at z={at:.1f} m" if at is not None else "")),
            "honest_from_m": round(honest_from_m(worst)),
            "length_lost_m": round(lost, 2),
            "feature_m": feature,
            "feature_source": f"ring spacing {spacing:.4f} m x stride",
            "aliases_beyond_m": round(aliases_beyond_m(feature)),
        })
    return out


# --- greeble ----------------------------------------------------------------

_PIECE_CACHE = {}


def greeble_pieces(schema, profile, detail):
    """Every connected piece of surface machinery, keyed by centroid.

    Keyed by (group, centroid) rather than by index so two builds at different
    detail levels can be compared as SETS -- which is how the strict-subset
    property is measured rather than asserted from a comment. Returns
    {key: (relief_m, triangles)}.

    Relief is the point-to-surface distance in the (z, r) plane,
    `(r_v - R(z_v)) / sqrt(1 + slope^2)`. The divisor is not decoration: on the
    23:1 section transitions the surface normal is nearly axial, and a plain
    radial difference reports a 5 m fitting as 297 m of relief.
    """
    key = round(detail, 6)
    if key in _PIECE_CACHE:
        return _PIECE_CACHE[key]
    import greeble
    surf = greeble.HullSurface(profile["profile"])
    parts, _stats = greeble.build_all(schema.get("greebles", {}),
                                      schema["longitudinal"]["features"],
                                      profile["profile"], detail)
    out = {}
    for gid, (verts, tris) in parts.items():
        if not tris:
            continue
        parent = list(range(len(verts)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for a, b, c in tris:
            ra = find(a)
            for other in (b, c):
                rb = find(other)
                if rb != ra:
                    parent[rb] = ra
        members, ntri = {}, {}
        for i in range(len(verts)):
            members.setdefault(find(i), []).append(i)
        for a, _b, _c in tris:
            root = find(a)
            ntri[root] = ntri.get(root, 0) + 1
        for root, idx in members.items():
            relief = -1e18
            cx = cy = cz = 0.0
            for i in idx:
                x, y, z = verts[i]
                slope = surf.slope_at(z)
                d = ((math.hypot(x, y) - surf.radius(z))
                     / math.sqrt(1.0 + slope * slope))
                relief = max(relief, d)
                cx += x
                cy += y
                cz += z
            n = len(idx)
            out[(gid, round(cx / n, 2), round(cy / n, 2), round(cz / n, 2))] = (
                relief, ntri.get(root, 0))
    _PIECE_CACHE[key] = out
    return out


def greeble_schedule(schema, profile):
    """Instance culling. Error is the relief of the largest piece removed.

    The result is uncomfortable and is the point of measuring: because the cull
    is by FRACTION and the population runs from 1.7 m panels to 72 m antenna
    masts, every non-trivial level drops a mast, so every non-trivial level has
    the same error and the same honest distance. The intermediate detail values
    are therefore DOMINATED -- they cost triangles and buy no honesty over
    dropping the greebles entirely. See the docstring for the one flag that
    would change this.
    """
    base = greeble_pieces(schema, profile, 1.0)
    off_hull = sorted(k for k, v in base.items() if v[0] > RELIEF_SANITY_M)
    out = []
    for detail in GREEBLE_STEPS:
        kept = greeble_pieces(schema, profile, detail)
        dropped = [base[k][0] for k in base.keys() - kept.keys()
                   if base[k][0] <= RELIEF_SANITY_M]
        alive = [v[0] for v in kept.values() if v[0] <= RELIEF_SANITY_M]
        worst = round(max(dropped) if dropped else 0.0, 3)
        median = round(statistics.median(alive) if alive else 0.0, 3)
        out.append({
            "greeble_detail": detail,
            "pieces": len(kept),
            "greeble_triangles": sum(v[1] for v in kept.values()),
            "error_m": worst,
            "error_baseline": "the full greeble set, i.e. detail 1.0",
            "error_source": ("relief of the tallest piece this cull removes, "
                             "measured as point-to-surface distance"),
            "honest_from_m": round(honest_from_m(worst)),
            "feature_m": median,
            "feature_source": "median relief of the pieces this level keeps",
            "aliases_beyond_m": round(aliases_beyond_m(median)),
            "strict_subset_of_full": kept.keys() <= base.keys(),
        })
    return out, off_hull


def relief_cull_proposal(schema, profile, distances=None):
    """What a RELIEF-graded greeble cull would buy, as a specification.

    Derived here rather than argued for in prose, because "greeble.py should
    cull by size" is a preference and a table of pieces and triangles against
    distance is a change request. The generator cannot do this today -- it is
    recorded so that whoever adds the flag has the numbers it should produce
    and an independent measurement to check the result against.

    The threshold is the shading-sample size at the distance, so the cull only
    ever removes pieces that are already under one pixel of relief there. One
    pixel is inside the 1.5 px deviation budget, so a relief cull is honest at
    exactly the distance it was computed for. That is the property a fraction
    cull cannot have at any distance: it draws its keep-test before it knows
    how big the fitting is.
    """
    base = greeble_pieces(schema, profile, 1.0)
    total_tris = sum(v[1] for v in base.values())
    if distances is None:
        # The distances the chain and the committed shots actually use, not a
        # round-number sweep: lod0's floor, the two orbits in
        # tools/build_and_render.sh and tools/export_scene.py's default, and
        # the first two silhouette switches.
        distances = (2_000.0, 4_271.0, 6_320.0, 12_000.0, 23_950.0, 49_204.0)
    out = []
    for d in distances:
        t = d / _px_scale(SHADING_SAMPLE_PX)
        dropped = [v for v in base.values() if v[0] < t]
        worst = max((v[0] for v in dropped), default=0.0)
        out.append({
            "distance_m": round(d),
            "relief_threshold_m": round(t, 3),
            "pieces_dropped": len(dropped),
            "pieces_kept": len(base) - len(dropped),
            "triangles_dropped": sum(v[1] for v in dropped),
            "triangles_kept": total_tris - sum(v[1] for v in dropped),
            "largest_piece_dropped_m": round(worst, 3),
            # By construction this is <= the distance it was derived for. Stated
            # so the property is checkable rather than claimed.
            "honest_from_m": round(honest_from_m(worst)),
        })
    return out


# ---------------------------------------------------------------------------
# Combining the three into one chain
# ---------------------------------------------------------------------------

def _coarsest_honest(schedule, distance):
    """The coarsest option whose introduced error is under budget at `distance`.

    Options are authored fine-to-coarse and `honest_from_m` is monotonic in
    that order (asserted), so the last one that qualifies is the coarsest.
    """
    chosen = schedule[0]
    for opt in schedule:
        if opt["honest_from_m"] <= distance:
            chosen = opt
    return chosen


def combine(sil, lon, gre, length_m=None):
    """The chain, as the distinct combinations the three schedules produce.

    Not a table. The boundaries are the union of every schedule's honest
    distances inside the camera's far plane, and the levels are whatever
    combinations survive de-duplication. Adding an option to any schedule
    changes the chain automatically; there is no second place to update, which
    is what the single LEVELS table got wrong.
    """
    if length_m is None:
        length_m = STATION_LENGTH_M
    bounds = sorted({0.0} | {opt["honest_from_m"]
                             for sched in (sil, lon, gre)
                             for opt in sched
                             if 0 < opt["honest_from_m"] <= FAR_PLANE_M})
    levels, last = [], None
    for d in bounds:
        s = _coarsest_honest(sil, d)
        l = _coarsest_honest(lon, d)
        g = _coarsest_honest(gre, d)
        combo = (s["radial_segments"], l["z_stride"], g["greeble_detail"])
        if combo == last:
            continue
        last = combo
        binding = max((s, l, g), key=lambda o: o["honest_from_m"])
        why = []
        for name, opt in (("silhouette", s), ("longitudinal", l), ("greeble", g)):
            why.append(f"{name} {opt['honest_from_m']:,} m")
        levels.append({
            "name": f"lod{len(levels)}",
            "radial_segments": s["radial_segments"],
            "z_stride": l["z_stride"],
            "greeble_detail": g["greeble_detail"],
            "switch_distance_m": round(d),
            # Every level records the three distances it is standing on, so a
            # reader can see WHICH schedule moved without re-deriving anything.
            "honest_from_m": {"silhouette": s["honest_from_m"],
                              "longitudinal": l["honest_from_m"],
                              "greeble": g["honest_from_m"]},
            "binding_schedule_honest_from_m": binding["honest_from_m"],
            # The level's own finest detail. Where this is below the switch
            # distance the chain has a gap: it is drawing detail the frame
            # cannot resolve because nothing coarser is honest yet.
            "aliases_beyond_m": {"silhouette": s["aliases_beyond_m"],
                                 "longitudinal": l["aliases_beyond_m"],
                                 "greeble": g["aliases_beyond_m"]},
            "switch_reason": "coarsest honest option in each schedule: " + ", ".join(why),
        })
    # The station is 8 km long, and `pick_hull_lod` measures to the NEAREST
    # point of it -- correctly, because decimating geometry that is close is
    # the worse error. The consequence is arithmetic and unavoidable: a level
    # selected at distance d is drawn over a depth range of at least d to
    # d + length, so its far end is always at least `length` further away than
    # the number that chose it. Recorded per level because it is the derivation
    # of "per-section LOD is required" -- previously a hunch in this file's
    # closing note, now a measured statement about every level in the chain.
    span = length_m
    for i, lv in enumerate(levels):
        nxt = levels[i + 1]["switch_distance_m"] if i + 1 < len(levels) else FAR_PLANE_M
        lv["used_to_m"] = round(nxt)
        lv["aliasing_gap"] = {k: v for k, v in lv["aliases_beyond_m"].items()
                              if v and v < nxt}
        lv["far_end_m"] = round(lv["switch_distance_m"] + span)
        lv["aliasing_gap_at_far_end"] = {
            k: v for k, v in lv["aliases_beyond_m"].items()
            if v and v < lv["far_end_m"]}
    return levels


def predicted_triangles(schema, profile, level):
    """Triangle count from the chain's own model of the generator.

    Kept separate from the number the generator reports so the two can be
    compared. If they diverge, either the generator changed shape or the chain
    is reasoning about a mesh that is not the one being shipped -- and a chain
    that models the wrong mesh will happily derive switch distances for it.
    """
    samples = profile["profile"][::level["z_stride"]]
    n = level["radial_segments"]
    lathe = 0
    for a, b in zip(samples, samples[1:]):
        ra, rb = a["radius_m"], b["radius_m"]
        pa, pb = ra <= 0.05, rb <= 0.05
        if pa and pb:
            continue
        lathe += n if (pa or pb) else 2 * n
    caps = sum(n for s in (samples[0], samples[-1]) if s["radius_m"] > 0.05)
    greeb = sum(v[1] for v in greeble_pieces(
        schema, profile, level["greeble_detail"]).values())
    # COMPONENTS NOW DECIMATE, in the one respect that matters at range: their
    # stiffener ribs. The shells themselves are hand-authored primitives welded
    # to the hull and no lathe schedule touches those -- that part of the old
    # comment here stands, and their cost is still a floor under every level.
    # What changed is that session 3s put chordwise ribs on the radiator blades,
    # the comms plate and the cooling fins, taking components from 19,800 to
    # 53,568 triangles and from 46% of lod7 to 93% of it. A 1.5 m stiffener is
    # invisible at the distance lod7 is drawn from, so it is dropped there.
    return (lathe + caps + greeb
            + component_triangles(schema, profile,
                                  component_detail(level)))


def component_detail(level):
    """Rib detail for a level, from the same greeble schedule the hull uses.

    Not a second schedule: `greeble_detail` already encodes how much small
    surface decoration a level carries, and a stiffener rib is small surface
    decoration. One knob, so the two cannot disagree about what "far away"
    means.
    """
    return max(0.0, min(1.0, float(level["greeble_detail"])))


_COMPONENT_TRIS = {}


def component_triangles(schema, profile, detail=1.0):
    key = round(detail, 4)
    if key not in _COMPONENT_TRIS:
        import components as components_mod
        parts = components_mod.build_all(schema.get("components", []),
                                         profile["profile"], detail=detail)
        _COMPONENT_TRIS[key] = sum(len(t) for _v, t in parts.values())
    return _COMPONENT_TRIS[key]


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------

def build(levels, quiet=True):
    """Generate one OBJ per level and collect what the generator reports.

    generate_hull.py writes its manifest next to its --out path, so running it
    here for a decimated level leaves `hull_manifest.json` describing that
    level. `validate.py` reads that manifest and duly failed with "hull length
    8042.9 m vs canon 8047" -- a real failure against a file that was simply
    stale. lod0's manifest is saved and restored around the whole run.
    """
    main_manifest = os.path.join(GENERATED, "hull_manifest.json")
    saved = open(main_manifest).read() if os.path.exists(main_manifest) else None
    try:
        for lv in levels:
            path = os.path.join(GENERATED, f"hull_{lv['name']}.obj")
            subprocess.run(
                [sys.executable, "generate_hull.py",
                 "--radial-segments", str(lv["radial_segments"]),
                 "--z-stride", str(lv["z_stride"]),
                 "--greeble-detail", str(lv["greeble_detail"]),
                 "--out", path],
                cwd=STATION, check=True, capture_output=True)
            man = json.load(open(main_manifest))
            lv["triangles"] = man["triangles"]
            lv["hull_triangles"] = man["hull_triangles"]
            lv["greeble_triangles"] = man["greeble_triangles"]
            lv["rings"] = man["rings"]
            lv["vertices"] = man["vertices"]
            lv["max_radius_m"] = man["bounds"]["max_radius_m"]
            lv["length_m"] = man["bounds"]["length_m"]
            lv["obj"] = os.path.relpath(path, ROOT)
            if not quiet:
                print(f"  built {lv['name']}: {lv['triangles']:,} triangles")
    finally:
        # Restore in a finally block: a generator failure halfway through used
        # to leave the shared manifest describing a decimated level, and the
        # next agent's validate.py run failed for a reason that had nothing to
        # do with what they had changed.
        if saved is not None:
            with open(main_manifest, "w") as f:
                f.write(saved)
        elif os.path.exists(os.path.join(GENERATED, "hull.obj")):
            subprocess.run([sys.executable, "generate_hull.py"],
                           cwd=STATION, check=True, capture_output=True)
    base = levels[0]["triangles"]
    for lv in levels:
        lv["reduction"] = round(1.0 - lv["triangles"] / base, 3)
    return levels


def manifest(schema, profile, levels=None, sil=None, lon=None, gre=None,
             off_hull=None):
    if sil is None:
        sil = silhouette_schedule(schema, profile)
    if lon is None:
        lon = longitudinal_schedule(profile)
    if gre is None:
        gre, off_hull = greeble_schedule(schema, profile)
    if levels is None:
        levels = combine(sil, lon, gre)
    return {
        "screen": {
            "fov_deg": FOV_DEG,
            "screen_h": SCREEN_H,
            "deviation_budget_px": PIXEL_BUDGET,
            "shading_sample_px": SHADING_SAMPLE_PX,
            "far_plane_m": FAR_PLANE_M,
            "m_per_m_deviation": round(_px_scale(PIXEL_BUDGET), 3),
            "m_per_m_shading": round(_px_scale(SHADING_SAMPLE_PX), 3),
        },
        "schedules": {"silhouette": sil, "longitudinal": lon, "greeble": gre},
        # The chain's quality floor. lod0 is the finest mesh that exists, and
        # inside this distance its own 64-gon faceting is already over the
        # deviation budget with nothing finer to switch to. Recorded because a
        # chain that only ever reports what it can fix hides its own ceiling.
        "quality_floor_m": sil[0]["honest_from_m"],
        "greeble_off_hull_pieces": [{"group": k[0], "z_m": k[3]}
                                    for k in (off_hull or [])],
        # Not part of the chain. A costed specification for the one generator
        # flag that would let the chain remove the speckle rather than only
        # measure it. See relief_cull_proposal().
        "relief_cull_proposal": relief_cull_proposal(schema, profile),
        "levels": levels,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def report(man):
    s = man["screen"]
    print(f"screen model: {s['screen_h']}p, {s['fov_deg']:.0f} deg vertical FOV")
    print(f"  deviation budget {s['deviation_budget_px']} px "
          f"-> {s['m_per_m_deviation']:,.1f} m of distance per metre of error")
    print(f"  shading sample   {s['shading_sample_px']} px "
          f"-> {s['m_per_m_shading']:,.1f} m of distance per metre of feature")
    for name, rows in man["schedules"].items():
        keyname = {"silhouette": "radial_segments", "longitudinal": "z_stride",
                   "greeble": "greeble_detail"}[name]
        print(f"\n{name.upper()} schedule")
        print(f"  {'option':>8} {'error m':>9} {'honest from':>13} "
              f"{'feature m':>10} {'aliases beyond':>15}")
        for r in rows:
            print(f"  {r[keyname]:>8} {r['error_m']:>9.3f} "
                  f"{r['honest_from_m']:>12,}m {r['feature_m']:>10.2f} "
                  f"{r['aliases_beyond_m']:>14,}m")
        print(f"    error: {rows[-1]['error_source']}")
    if man["greeble_off_hull_pieces"]:
        print(f"\n  NOTE {len(man['greeble_off_hull_pieces'])} greeble pieces stand "
              f"more than {RELIEF_SANITY_M:.0f} m off the hull and are excluded from "
              f"the derivation as defects:")
        for p in man["greeble_off_hull_pieces"]:
            print(f"    {p['group']} at z={p['z_m']:.1f} m")

    print("\nWHAT A RELIEF-GRADED GREEBLE CULL WOULD BUY (not buildable today;")
    print("needs one flag on generate_hull.py -- see relief_cull_proposal)")
    print(f"  {'at':>9} {'cull below':>11} {'pieces cut':>11} {'tris cut':>10} "
          f"{'tris kept':>10} {'honest from':>12}")
    for r in man.get("relief_cull_proposal", []):
        print(f"  {r['distance_m']:>8,}m {r['relief_threshold_m']:>10.2f}m "
              f"{r['pieces_dropped']:>11,} {r['triangles_dropped']:>10,} "
              f"{r['triangles_kept']:>10,} {r['honest_from_m']:>11,}m")

    print(f"\nCHAIN ({len(man['levels'])} levels)")
    have = "triangles" in man["levels"][0]
    head = (f"  {'level':6} {'segs':>5} {'stride':>7} {'greeb':>6} {'switch':>11} "
            f"{'used to':>11}")
    if have:
        head += f" {'triangles':>11} {'reduce':>8}"
    print(head)
    for lv in man["levels"]:
        line = (f"  {lv['name']:6} {lv['radial_segments']:>5} {lv['z_stride']:>7} "
                f"{lv['greeble_detail']:>6.2f} {lv['switch_distance_m']:>10,}m "
                f"{lv['used_to_m']:>10,}m")
        if have:
            line += f" {lv['triangles']:>11,} {lv['reduction']*100:>7.1f}%"
        print(line)
        if lv["aliasing_gap"]:
            g = ", ".join(f"{k} sub-pixel beyond {v:,} m"
                          for k, v in sorted(lv["aliasing_gap"].items()))
            print(f"         gap at the near point: {g}")
        extra = sorted(set(lv["aliasing_gap_at_far_end"]) - set(lv["aliasing_gap"]))
        if extra:
            print(f"         gap at its far end ({lv['far_end_m']:,} m): "
                  + ", ".join(f"{k} sub-pixel beyond "
                              f"{lv['aliasing_gap_at_far_end'][k]:,} m"
                              for k in extra))
    print(f"\n  A level chosen on the NEAREST hull point is drawn over at least "
          f"{STATION_LENGTH_M:,.0f} m of depth,\n  so its far end is always that much "
          f"further out than the number that selected it.\n  Every level in this chain "
          f"is past at least one aliasing distance somewhere along\n  its own length. "
          f"That is not a tuning failure -- it is what a single whole-hull\n  LOD means "
          f"on an 8 km object, and it is the derivation of per-section LOD.")
    if have:
        print(f"\n  chain total {sum(l['triangles'] for l in man['levels']):,} triangles "
              f"across {len(man['levels'])} levels")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _rasteriser_px(size_m, distance_m):
    """Pixel height of a `size_m` quad at `distance_m`, from an outside renderer.

    The pixel arithmetic every switch distance rests on must be checked against
    something that is not this file. `tools/preview_render.py` builds its own
    camera basis and does its own perspective divide, so measuring a known quad
    through it exercises an independent implementation. Comparing `_px_scale`
    against a rearrangement of `_px_scale` would be an algebraic identity, and
    this project has three of those on record (AAA-STANDARD, ROBUSTNESS 0).
    """
    import tempfile
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        obj = os.path.join(tmp, "probe.obj")
        png = os.path.join(tmp, "probe.png")
        h = size_m / 2.0
        with open(obj, "w") as f:
            for y in (-h, h):
                for x in (-h, h):
                    f.write(f"v {x:.6f} {y:.6f} 0.0\n")
            f.write("g probe\no probe\nf 1 2 4\nf 1 4 3\n")
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools/preview_render.py"), obj,
             "--out", png, "--width", "512", "--height", str(SCREEN_H),
             "--eye", "0", "0", str(distance_m), "--target", "0", "0", "0",
             "--up", "0", "1", "0", "--fov", str(FOV_DEG),
             "--bg", "255", "0", "255"],
            check=True, capture_output=True)
        import numpy as np
        a = np.asarray(Image.open(png).convert("RGB")).astype(int)
        bg = (a[:, :, 0] > 200) & (a[:, :, 1] < 60) & (a[:, :, 2] > 200)
        rows = np.where(~bg.all(axis=1))[0]
        return float(rows.max() - rows.min() + 1) if len(rows) else 0.0


def _selftest():
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL: {label}")

    schema, profile = _load()
    sil = silhouette_schedule(schema, profile)
    lon = longitudinal_schedule(profile)
    gre, off_hull = greeble_schedule(schema, profile)
    levels = combine(sil, lon, gre)

    # -- the pixel arithmetic itself --------------------------------------
    # Everything below is a ratio against _px_scale. If it is wrong by a factor
    # of two, every switch distance in the chain is wrong by a factor of two and
    # nothing else in this file would notice.
    for size, dist in ((100.0, 4000.0), (37.0, 1200.0)):
        try:
            got = _rasteriser_px(size, dist)
            want = size * _px_scale(SHADING_SAMPLE_PX) / dist
            check(abs(got - want) <= max(2.0, 0.02 * want),
                  f"pixel model agrees with tools/preview_render.py: "
                  f"{size:.0f} m at {dist:,.0f} m measured {got:.1f} px, "
                  f"model {want:.1f} px")
        except Exception as exc:                     # noqa: BLE001
            check(False, f"pixel model cross-check against the rasteriser: {exc}")

    # The two budgets must not be the same number by accident: the whole reason
    # `aliases_beyond_m` says anything the old chain did not is that it uses a
    # different budget from `honest_from_m`.
    check(_px_scale(SHADING_SAMPLE_PX) > _px_scale(PIXEL_BUDGET),
          "the shading budget is stricter than the deviation budget")

    # -- schedules are monotonic ------------------------------------------
    # Authored fine-to-coarse. If an option's error is not monotonic in that
    # order then `_coarsest_honest` picking "the last one that qualifies" is
    # wrong and the chain silently selects a level it is not entitled to.
    KEYS = {"silhouette": "radial_segments", "longitudinal": "z_stride",
            "greeble": "greeble_detail"}
    SCHEDULES = {"silhouette": sil, "longitudinal": lon, "greeble": gre}
    for name, rows, coarser in (
            ("silhouette", sil, lambda a, b: b < a),
            ("longitudinal", lon, lambda a, b: b > a),
            ("greeble", gre, lambda a, b: b < a)):
        key = KEYS[name]
        opts = [r[key] for r in rows]
        check(all(coarser(a, b) for a, b in zip(opts, opts[1:])),
              f"{name} options are authored fine to coarse: {opts}")
        d = [r["honest_from_m"] for r in rows]
        check(all(a <= b for a, b in zip(d, d[1:])),
              f"{name} honest-from distances are monotonic: {d}")
        # Aliasing distance is a property of the detail a level KEEPS, so a
        # level that keeps nothing (greeble 0.0) has none. Checked over the
        # levels that keep something, which is the set where the number means
        # anything -- not skipped for the whole schedule, which would make the
        # greeble case unfailable.
        a = [r["aliases_beyond_m"] for r in rows if r["aliases_beyond_m"] > 0]
        check(len(a) >= 2 and all(x <= y for x, y in zip(a, a[1:])),
              f"{name} aliasing distances are monotonic over the levels that "
              f"keep detail: {a}")

    # Two of the three measure error against their own finest option, so their
    # finest option has zero error by construction. The silhouette schedule
    # measures against the true surface instead, and its finest option's error
    # is the chain's quality floor rather than zero -- asserted as such, not
    # exempted.
    for name in ("longitudinal", "greeble"):
        rows = SCHEDULES[name]
        check(rows[0]["honest_from_m"] == 0 and rows[0]["error_m"] == 0.0,
              f"{name}'s finest option is its own baseline and is honest from 0 "
              f"(got {rows[0]['honest_from_m']:,} m, error "
              f"{rows[0]['error_m']:.3f} m)")
    floor = sil[0]["honest_from_m"]
    check(floor == round(honest_from_m(sil[0]["error_m"])) and floor > 0,
          f"the silhouette schedule reports a quality floor rather than zero "
          f"({floor:,} m from a {sil[0]['error_m']:.3f} m sagitta)")
    check(manifest(schema, profile, levels, sil, lon, gre,
                   off_hull)["quality_floor_m"] == floor,
          "the manifest carries the quality floor where a reader will find it")

    # -- no level claims to be honest closer than the criterion allows ----
    # This is the assertion that stops a hand-typed distance coming back. Each
    # component's honest distance is RE-DERIVED here from the recorded error and
    # compared against the switch distance the chain published.
    #
    # The finest option in each schedule is exempt from the switch-distance half
    # and ONLY that half: there is nothing finer to fall back to, so lod0 has to
    # be used inside its floor. The recorded-equals-derived half still applies to
    # it, so the exemption cannot hide a wrong number.
    for lv in levels:
        for name, rows in SCHEDULES.items():
            key = KEYS[name]
            opt = next(r for r in rows if r[key] == lv[key])
            want = honest_from_m(opt["error_m"])
            if opt is not rows[0]:
                check(lv["switch_distance_m"] >= math.floor(want),
                      f"{lv['name']} uses {name} option {opt[key]} from "
                      f"{lv['switch_distance_m']:,} m, but its {opt['error_m']:.3f} m "
                      f"error is only under {PIXEL_BUDGET} px from {want:,.0f} m")
            check(opt["honest_from_m"] == round(want),
                  f"{name} option {opt[key]}: recorded honest distance "
                  f"{opt['honest_from_m']:,} m equals the derived {want:,.0f} m")

    check(levels[0]["switch_distance_m"] == 0,
          "the chain starts at zero distance")
    d = [lv["switch_distance_m"] for lv in levels]
    check(all(a < b for a, b in zip(d, d[1:])),
          f"chain switch distances strictly increase: {d}")

    # Coverage, in both directions. An option belongs in the chain exactly when
    # it is the coarsest honest one over some band -- which is NOT the same as
    # "every option is used". Three of the five greeble steps share a switch
    # distance with the one below them, so they can never be selected: they cost
    # triangles and buy no honesty, and the chain says so by not containing
    # them. An earlier version of this assertion compared the chain's last
    # switch against FAR_PLANE_M, which `combine` filters on, so it could not
    # fail -- the exact category AAA-STANDARD scores ROBUSTNESS 0.
    for name, rows in SCHEDULES.items():
        key = KEYS[name]
        expect = {rows[i][key] for i in range(len(rows))
                  if rows[i]["honest_from_m"] <= FAR_PLANE_M
                  and (i == len(rows) - 1
                       or rows[i + 1]["honest_from_m"] > rows[i]["honest_from_m"])}
        used = {lv[key] for lv in levels}
        check(used == expect,
              f"{name}: the chain uses exactly the options that are the coarsest "
              f"honest choice somewhere inside the far plane "
              f"(used {sorted(used)}, expected {sorted(expect)})")
    check(all(levels[-1][KEYS[n]] == SCHEDULES[n][-1][KEYS[n]] for n in SCHEDULES),
          f"the chain reaches every schedule's coarsest option inside the far "
          f"plane ({FAR_PLANE_M:,.0f} m); last level is "
          f"{[levels[-1][KEYS[n]] for n in SCHEDULES]}")

    # -- the chain actually reduces triangles ------------------------------
    # Predicted from the chain's own model of the generator, so this runs on a
    # bare checkout. If the prediction is flat or rising, the chain is a list of
    # different meshes rather than a decimation.
    pred = [predicted_triangles(schema, profile, lv) for lv in levels]
    check(all(a > b for a, b in zip(pred, pred[1:])),
          f"predicted triangle counts strictly decrease along the chain: {pred}")
    check(pred[-1] < pred[0] * 0.1,
          f"the chain's coarsest level is under a tenth of its finest "
          f"({pred[-1]:,} against {pred[0]:,})")

    # Against what the generator actually wrote, if it has been run. The
    # prediction is a model and a model that has never been compared with the
    # artefact is a guess.
    man_path = os.path.join(GENERATED, "lod_manifest.json")
    if os.path.exists(man_path):
        built = json.load(open(man_path)).get("levels", [])
        by_name = {lv["name"]: lv for lv in built if "triangles" in lv}
        if by_name:
            got = [by_name[lv["name"]]["triangles"] for lv in levels
                   if lv["name"] in by_name]
            check(len(got) == len(levels),
                  f"every chain level has a built mesh in the manifest "
                  f"({len(got)} of {len(levels)})")
            check(all(a > b for a, b in zip(got, got[1:])),
                  f"BUILT triangle counts strictly decrease: {got}")
            worst = 0.0
            for lv, p in zip(levels, pred):
                b = by_name.get(lv["name"])
                if b:
                    worst = max(worst, abs(b["triangles"] - p) / max(1, p))
            check(worst < 0.005,
                  f"the chain's triangle model matches what the generator wrote "
                  f"(worst disagreement {worst*100:.3f}%)")
            # "Cost scales the way the design claims it does, and the claim is
            # measured" (AAA-STANDARD, PERFORMANCE 4). The claim here is that
            # the lathe is a grid: hull triangles = 2 x segments x (rings - 1)
            # plus caps. Checked against what the generator wrote, over every
            # level, so a change that makes cost scale some other way shows up
            # as a failure rather than as a surprise in the budget report.
            rates = []
            for lv in levels:
                b = by_name.get(lv["name"])
                if b:
                    rates.append(b["hull_triangles"]
                                 / (b["radial_segments"] * (b["rings"] - 1)))
            check(rates and max(rates) - min(rates) < 0.05,
                  f"hull cost is 2 triangles per segment per ring gap at every "
                  f"level (ratios {[round(r, 4) for r in rates]})")

            for lv in levels:
                b = by_name.get(lv["name"])
                if not b:
                    continue
                check(b["radial_segments"] == lv["radial_segments"]
                      and b["z_stride"] == lv["z_stride"]
                      and abs(b["greeble_detail"] - lv["greeble_detail"]) < 1e-9,
                      f"{lv['name']} was built with the options the chain "
                      f"derived, not another set")
    else:
        print("note: no lod_manifest.json; run --build to check built counts")

    # -- greeble measurement -----------------------------------------------
    # A cull must remove instances rather than reshuffle them, or a switch
    # rearranges the hull instead of simplifying it. Measured on piece keys, so
    # this is a property of the geometry and not of a comment in greeble.py.
    for row in gre:
        check(row["strict_subset_of_full"],
              f"greeble detail {row['greeble_detail']} is a strict subset of the "
              f"full set")
    counts = [r["pieces"] for r in gre]
    check(all(a >= b for a, b in zip(counts, counts[1:])),
          f"greeble piece counts fall monotonically with detail: {counts}")

    # The relief measurement must recover a dimension the generator states
    # independently: `greeble._antenna_stub` builds masts of rng.span(32, 72) m
    # and nothing taller exists, so the tallest sane piece has to land inside
    # that span. If the measurement were wrong -- wrong axis, missing the slope
    # divisor, clamped at zero -- this lands outside it.
    base = greeble_pieces(schema, profile, 1.0)
    sane = [(v[0], k) for k, v in base.items() if v[0] <= RELIEF_SANITY_M]
    tallest, tallest_key = max(sane)
    # The GROUP matters as much as the number. An earlier version checked only
    # that the tallest sane relief fell in 32-72 m, and scaling every measured
    # relief by 0.2 still passed it -- the off-hull panel defect shrank INTO the
    # mast span and satisfied the assertion in the antenna's place.
    check(tallest_key[0] == "greeble_antenna" and 32.0 <= tallest <= RELIEF_SANITY_M,
          f"the tallest fitting the measurement finds is an antenna mast at "
          f"{tallest:.2f} m, inside greeble._antenna_stub's 32-72 m span "
          f"(found {tallest_key[0]})")
    shortest = min(v[0] for v in base.values())
    check(shortest < 0.0,
          f"the relief measure is signed and finds buried geometry "
          f"(shallowest piece {shortest:.2f} m)")

    # A regression gate on a real defect: two greeble pieces sit hundreds of
    # metres off the hull at the z=3138 transition. They are excluded from the
    # derivation, so nothing else in this file would ever notice more appearing.
    check(len(off_hull) == OFF_HULL_PIECES_EXPECTED,
          f"greeble pieces standing off the hull: {len(off_hull)}, expected "
          f"{OFF_HULL_PIECES_EXPECTED} ({[k[0] + '@' + str(k[3]) for k in off_hull]})")

    # -- the longitudinal error is measured, not assumed -------------------
    # The whole correction in this file rests on stride 2 costing tens of metres
    # rather than the ~4 m of ring spacing that intuition suggests. Assert the
    # measurement is doing real work: the chord error must be far larger than
    # the sample spacing, which is what a profile with steps in it means.
    spacing = lon[0]["feature_m"]
    check(lon[1]["error_m"] > 10 * spacing,
          f"stride 2's measured chord error ({lon[1]['error_m']:.1f} m) is much "
          f"larger than the ring spacing ({spacing:.2f} m) -- the profile steps")
    check(all(a["error_m"] <= b["error_m"] for a, b in zip(lon, lon[1:])),
          "longitudinal chord error grows with stride")
    check(lon[0]["error_m"] == 0.0 and lon[0]["length_lost_m"] == 0.0,
          "stride 1 is the source data and introduces no error at all")

    # -- the relief-cull specification -------------------------------------
    # The proposal's whole claim is that a relief-graded cull is honest at the
    # distance it was derived for. That is a consequence of SHADING_SAMPLE_PX
    # being stricter than PIXEL_BUDGET, and it stops being true the moment
    # someone loosens one of them -- so it is asserted rather than asserted in
    # prose.
    prop = relief_cull_proposal(schema, profile)
    check(all(r["honest_from_m"] <= r["distance_m"] for r in prop),
          f"a relief cull is honest at the distance it was derived for "
          f"(worst: {max((r['honest_from_m'] - r['distance_m'] for r in prop)):,} m over)")
    cut = [r["pieces_dropped"] for r in prop]
    check(all(a <= b for a, b in zip(cut, cut[1:])) and cut[0] > 0 and cut[-1] > cut[0],
          f"the relief cull removes more as distance grows: {cut}")
    total_pieces = len(greeble_pieces(schema, profile, 1.0))
    check(all(r["pieces_dropped"] + r["pieces_kept"] == total_pieces for r in prop),
          "the relief cull accounts for every piece")
    # And it must beat the fraction cull on the thing that matters: at the
    # distance the docs frame was rendered from, the fraction knob is honest
    # nowhere and the relief cull is honest here.
    at_docs = next(r for r in prop if r["distance_m"] == 4271)
    check(at_docs["triangles_dropped"] > 0.2 * (
              at_docs["triangles_dropped"] + at_docs["triangles_kept"]),
          f"at the docs camera a relief cull removes a fifth of the greeble "
          f"triangles ({at_docs['triangles_dropped']:,} of "
          f"{at_docs['triangles_dropped'] + at_docs['triangles_kept']:,})")

    # -- the far-end consequence ------------------------------------------
    # The constant the far-end arithmetic uses must be the station's real
    # length, or the statement it supports is about a different object.
    zs = [s["z_m"] for s in profile["profile"]]
    check(abs((zs[-1] - zs[0]) - STATION_LENGTH_M) < 1.0,
          f"STATION_LENGTH_M matches the profile's z extent "
          f"({zs[-1] - zs[0]:.1f} m against {STATION_LENGTH_M:.1f} m)")
    check(all(lv["far_end_m"] > lv["switch_distance_m"] for lv in levels),
          "every level records a far end beyond the point that selected it")
    check(all(lv["aliasing_gap_at_far_end"] for lv in levels),
          "every level is past an aliasing distance somewhere along its own "
          "length -- the fact that makes per-section LOD necessary, recorded "
          "rather than assumed")

    print(f"{ok}/{ok + fail} passed")
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true",
                    help="regenerate hull_lod*.obj and lod_manifest.json")
    ap.add_argument("--report", action="store_true",
                    help="print the derivation without writing anything")
    a = ap.parse_args()
    if not (a.build or a.report):
        sys.exit(_selftest())

    schema, profile = _load()
    sil = silhouette_schedule(schema, profile)
    lon = longitudinal_schedule(profile)
    gre, off_hull = greeble_schedule(schema, profile)
    levels = combine(sil, lon, gre)
    if a.build:
        print(f"building {len(levels)} levels ...")
        build(levels, quiet=False)
    man = manifest(schema, profile, levels, sil, lon, gre, off_hull)
    if a.build:
        with open(os.path.join(GENERATED, "lod_manifest.json"), "w") as f:
            json.dump(man, f, indent=1)
    report(man)


if __name__ == "__main__":
    main()
