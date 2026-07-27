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
          note=f"{man['hull_triangles']:,} hull + {man['component_triangles']:,} components")
    check("draw calls", draws, BUDGETS["exterior_draw_calls"],
          note="one per feature group, before instancing")
    check("vertex bandwidth", bandwidth, BUDGETS["vertex_bandwidth_mb"], " MB",
          "flat-shaded, un-indexed")
    if size:
        check("glb on disk", size, BUDGETS["glb_size_mb"], " MB")

    print(f"\nheadroom: {BUDGETS['exterior_triangles'] - tris:,} triangles, "
          f"{BUDGETS['exterior_draw_calls'] - draws} draw calls")
    print("Note: these gate the numbers framerate is a function of. They say nothing\n"
          "about actual framerate, which needs the target hardware.")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} within budget")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
