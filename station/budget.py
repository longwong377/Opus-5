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

results = []


def check(name, value, limit, unit="", note=""):
    ok = value <= limit
    results.append(ok)
    pct = value / limit * 100
    bar = "#" * int(pct / 5) + "." * (20 - int(min(pct, 100) / 5))
    print(f"{'PASS' if ok else 'FAIL'}  {name:26s} [{bar}] "
          f"{value:>10,.0f}{unit} / {limit:,.0f}{unit}  ({pct:.0f}%)"
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
    print("Note: these gate the numbers framerate is a function of. They say nothing\n"
          "about actual framerate, which needs the target hardware.")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} within budget")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
