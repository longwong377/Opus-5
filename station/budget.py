#!/usr/bin/env python3
"""Performance budget gates.

There is no GPU in the build container, so framerate cannot be measured here.
What can be measured is everything framerate is a function of: triangle counts,
draw calls, instance counts, vertex bandwidth and texture memory. Shipping
studios gate on exactly these numbers and treat the profiler as confirmation
rather than discovery, which is the only workable approach when the target
hardware is not present.

Budgets derive from the target in CLAUDE.md: RTX 4070 / RX 7800 XT class,
1440p60, 12 GB VRAM. Exceeding one is a build failure, not a warning.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "station/generated/hull_manifest.json")
GLB = os.path.join(ROOT, "station/generated/station.glb")

# A 4070 sustains roughly 20-30 M triangles/frame at 1440p60 with a modern
# deferred renderer. The exterior hull is always-visible background geometry
# competing with interiors, NPCs and effects, so it gets a deliberately small
# slice -- 2% of frame budget -- leaving headroom for everything in front of it.
BUDGETS = {
    "exterior_triangles": 400_000,
    "exterior_draw_calls": 64,
    "glb_size_mb": 64.0,
    "vertex_bandwidth_mb": 32.0,
}

# Interior is gated on what can be SEEN AT ONCE, not on total built geometry.
# Totalling the interior is meaningless: the concentric-ring topology gives ring
# 1 alone a circumference of 2*pi*278.3 = 1,749 m per sector, and with five
# rings across six sectors the built total runs to millions of triangles that
# are never simultaneously in frame. Occlusion culling means the cost that
# matters is the current cell plus whatever is visible through its portals.
#
# The visible-set estimate below is deliberately pessimistic: a straight run
# with a crossing at each end and both of those crossings' near arms partly in
# view. A curved ring corridor sees less than this, not more.
INTERIOR = {
    "corridor_tris_per_m": 400,      # marginal rate along a run
    "junction_tris": 2_000,          # one crossing, all arms
    "visible_set_tris": 60_000,      # structure only -- see below
    "sight_line_m": 50.0,            # how far down a corridor before it curves or a door blocks
    "junctions_in_view": 2,
}

# 60,000 is structure only. At 1440p60 on the target card the whole frame
# affords roughly 1.2 M triangles, and interior structure should not take more
# than ~5% of it: the same view has to carry props, fittings, signage, NPCs and
# whatever is through the windows. If structure alone reaches 60 k the kit has
# become too expensive to dress.
INTERIOR_FRAME_SHARE = 0.05
FRAME_TRIANGLES = 1_200_000

# The habitat drum is not a corridor and the corridor gate does not describe it.
# A corridor is budgeted on a 50 m sight line because a wall stops you seeing
# further. Standing in the Garden there is no wall: the far end cap is 2.6 km
# away, the ground overhead is 556 m up, and every triangle in the volume is in
# the frustum at once. It is the worst visibility case in the project and until
# now it had no gate at all.
#
# It also earns a bigger share than a corridor. This is the view the whole
# structure phase exists to produce, so it gets a quarter of the frame rather
# than a twentieth -- and it has to hold that with LOD, since the far half of
# the drum is over a kilometre away and cannot be drawn at full rate.
DRUM = {
    "visible_set_tris": 300_000,
    "frame_share": 0.25,
    # Everything in the drum's inner surface is potentially visible, so the
    # meaningful density is per square metre of ground, not per metre of run.
    # This is the number that decides whether the ground can be per-object
    # geometry or has to be a heightfield -- and it says heightfield.
    "surface_tris_per_m2": 0.5,
}

results = []


def check(name, value, limit, unit="", note=""):
    ok = value <= limit
    results.append(ok)
    pct = value / limit * 100
    bar = "#" * int(pct / 5) + "." * (20 - int(min(pct, 100) / 5))
    # Densities are fractions per square metre; rounding them to integers
    # printed "0 / 0" for a gate that was doing real work.
    fmt = ",.3f" if limit < 10 else ",.0f"
    print(f"{'PASS' if ok else 'FAIL'}  {name:26s} [{bar}] "
          f"{value:>10{fmt}}{unit} / {limit:{fmt}}{unit}  ({pct:.1f}%)"
          + (f"  {note}" if note else ""))
    return ok


def main():
    if not os.path.exists(MANIFEST):
        print("no manifest -- run station/generate_hull.py first")
        return 1
    man = json.load(open(MANIFEST))

    tris = man["triangles"]
    draws = len(man["groups"])
    # 24 bytes per vertex un-indexed (position + normal), 3 vertices per triangle.
    bandwidth = tris * 3 * 24 / 1e6
    size = os.path.getsize(GLB) / 1e6 if os.path.exists(GLB) else 0.0

    print("Exterior geometry against the 1440p60 / 12 GB target\n")
    check("triangles", tris, BUDGETS["exterior_triangles"],
          note=f"{man['hull_triangles']:,} hull + {man['component_triangles']:,} components"
               f" + {man.get('greeble_triangles', 0):,} greebles")
    check("draw calls", draws, BUDGETS["exterior_draw_calls"],
          note="one per feature group, before instancing")
    check("vertex bandwidth", bandwidth, BUDGETS["vertex_bandwidth_mb"], " MB",
          "flat-shaded, un-indexed")
    if size:
        check("glb on disk", size, BUDGETS["glb_size_mb"], " MB")

    greebles = man.get("greeble_triangles", 0)
    if greebles:
        print(f"\nsurface detail: {greebles:,} triangles "
              f"({greebles / BUDGETS['exterior_triangles'] * 100:.0f}% of the triangle "
              f"budget, {greebles / tris * 100:.0f}% of the model) across "
              f"{man.get('greeble_instances', 0):,} fittings in "
              f"{man.get('greeble_assemblies', 0):,} assemblies and "
              f"{man.get('greeble_conduit_runs', 0)} conduit runs")

    print(f"\nheadroom: {BUDGETS['exterior_triangles'] - tris:,} triangles, "
          f"{BUDGETS['exterior_draw_calls'] - draws} draw calls")

    # --- interior -----------------------------------------------------------
    try:
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import interior_kit as ik

        # Marginal rate, not total: a corridor's fixed end caps would otherwise
        # make a short sample look far more expensive per metre than a long run.
        t1 = len(ik.corridor_section(1.0)[1])
        t20 = len(ik.corridor_section(20.0)[1])
        per_m = (t20 - t1) / 19.0
        cross = len(ik.junction()[1])
        tee = len(ik.junction(arms=(0, 1, 3))[1])

        visible = (per_m * INTERIOR["sight_line_m"]
                   + max(cross, tee) * INTERIOR["junctions_in_view"])

        print("\nInterior, gated on what is visible at once rather than on total built\n")
        check("corridor rate", per_m, INTERIOR["corridor_tris_per_m"], " tri/m",
              "marginal along a run")
        check("junction", max(cross, tee), INTERIOR["junction_tris"], " tri",
              f"crossing {cross:,}, tee {tee:,}")
        check("visible structure set", visible, INTERIOR["visible_set_tris"], " tri",
              f"{INTERIOR['sight_line_m']:.0f} m sight line + "
              f"{INTERIOR['junctions_in_view']} crossings")
        share = visible / FRAME_TRIANGLES
        check("interior share of frame", share * 100,
              INTERIOR_FRAME_SHARE * 100, "%",
              "structure only -- props, NPCs and signage come out of the rest")
    except Exception as exc:
        check("interior kit measurable", 1, 0, "", f"could not measure: {exc}")

    # --- habitat drum -------------------------------------------------------
    try:
        import interior as it

        schema, profile = it.load()
        drum = it.drum_sector(schema, profile)
        r = it.sector_radius(schema, profile, drum)
        ex = schema["sectors"]["extents_m"][drum]
        length = ex["z1"] - ex["z0"]
        area = 2 * math.pi * r * length

        shell = len(it.drum_interior(schema, profile, drum, arc_deg=360.0,
                                     seg_deg=2.0, z_step=40.0)[1])
        caps = sum(len(it.drum_end_cap(schema, profile, drum, e)[1])
                   for e in ("fore", "aft"))
        trusses = len(it.drum_guideways(schema, profile, drum)[1])
        spokes = len(it.drum_spokes(schema, profile, drum)[1])
        total = shell + caps + trusses + spokes

        print("\nHabitat drum, where everything is visible at once\n")
        check("drum visible set", total, DRUM["visible_set_tris"], " tri",
              f"shell {shell:,} + caps {caps:,} + trusses {trusses:,}"
              f" + spokes {spokes:,}")
        check("drum share of frame", total / FRAME_TRIANGLES * 100,
              DRUM["frame_share"] * 100, "%",
              "no occlusion -- there is no wall to hide behind")
        check("ground surface density", shell / area,
              DRUM["surface_tris_per_m2"], " tri/m2",
              f"{area/1e6:.1f} million m2 of inner surface")
        print(f"\nheadroom: {DRUM['visible_set_tris'] - total:,} triangles for "
              f"ground detail, buildings, trams and vegetation across "
              f"{area/1e6:.1f} million m2 -- "
              f"{(DRUM['visible_set_tris'] - total) / area:.2f} tri/m2. "
              f"The ground is a heightfield, not objects.")
    except Exception as exc:
        check("drum measurable", 1, 0, "", f"could not measure: {exc}")
    print("Note: these gate the numbers framerate is a function of. They say nothing\n"
          "about actual framerate, which needs the target hardware.")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} within budget")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
