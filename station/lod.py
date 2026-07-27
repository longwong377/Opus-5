#!/usr/bin/env python3
"""Generate LOD chains for the station's exterior geometry.

A Starfury will see the station from 50 m and from 50 km in the same flight.
At 50 km the whole 8 km hull covers a few hundred pixels, so 256,000 triangles
is roughly a thousand triangles per visible pixel -- pure waste, and worse than
waste, because it is bandwidth stolen from whatever is actually near the camera.

Godot has no Nanite (ADR 0001), so LOD is ours to build. The lathe makes this
easy in a way a hand-modelled hull would not: reducing radial segments and
longitudinal stride is a principled decimation that preserves silhouette
exactly, because the silhouette is a function of the radius profile rather than
of the triangles.
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (name, radial_segments, z_stride, switch distance in metres)
#
# Switch distances are derived from SILHOUETTE DEVIATION, not facet width.
# What causes a visible LOD pop on a body of revolution is the sagitta -- how
# far the flat chord of an n-gon falls inside the true circle:
#
#     deviation = r * (1 - cos(pi / n))
#
# At r = 1211 m that is 1.5 m for a 64-gon, 5.8 m for 32, 23.3 m for 16 and
# 92.2 m for 8. Each level may be used once that deviation subtends under
# ~1.5 px at 1440p with a 50 degree vertical FOV.
#
# The consequence is worth stating: this object is so large that radial
# decimation stays visible much further out than intuition suggests. lod3 is
# only honest beyond 95 km, which is past any expected viewing range, so it
# exists for the far-approach case rather than for normal flight.
# Set to the honest distances -- where deviation actually falls under 1.5 px --
# rather than to the 4x-closer values that felt reasonable before measuring.
# lod0 therefore carries all normal viewing, which the budget affords: 256k
# triangles is 64% of the exterior allowance with 144k spare.
LEVELS = [
    ("lod0", 64, 1, 0),
    ("lod1", 32, 2, 6_000),
    ("lod2", 16, 4, 24_000),
    ("lod3", 8, 8, 95_000),
]
FOV_DEG = 50.0
SCREEN_H = 1440
PIXEL_BUDGET = 1.5


def main():
    out = []
    for name, segs, stride, dist in LEVELS:
        path = os.path.join(ROOT, f"station/generated/hull_{name}.obj")
        subprocess.run(
            [sys.executable, "generate_hull.py",
             "--radial-segments", str(segs), "--z-stride", str(stride),
             "--out", path],
            cwd=os.path.join(ROOT, "station"),
            check=True, capture_output=True)
        man = json.load(open(os.path.join(ROOT, "station/generated/hull_manifest.json")))
        out.append({
            "name": name,
            "radial_segments": segs,
            "z_stride": stride,
            "switch_distance_m": dist,
            "triangles": man["triangles"],
            "max_radius_m": man["bounds"]["max_radius_m"],
            "length_m": man["bounds"]["length_m"],
        })

    base = out[0]["triangles"]
    for lv in out:
        lv["reduction"] = round(1.0 - lv["triangles"] / base, 3)
        r = base_radius(out)
        dev = r * (1.0 - math.cos(math.pi / lv["radial_segments"]))
        lv["silhouette_deviation_m"] = round(dev, 2)
        if lv["switch_distance_m"] > 0:
            px = (dev / lv["switch_distance_m"]
                  / (2 * math.tan(math.radians(FOV_DEG / 2))) * SCREEN_H)
            lv["deviation_px_at_switch"] = round(px, 2)
            lv["honest_from_m"] = round(
                dev * SCREEN_H / (PIXEL_BUDGET * 2 * math.tan(math.radians(FOV_DEG / 2))))

    path = os.path.join(ROOT, "station/generated/lod_manifest.json")
    with open(path, "w") as f:
        json.dump({"levels": out}, f, indent=1)

    print(f"{'level':6} {'segs':>5} {'stride':>7} {'triangles':>11} {'reduce':>8} "
          f"{'deviation':>10} {'switch':>10} {'dev px':>7} {'honest':>9}")
    for lv in out:
        print(f"{lv['name']:6} {lv['radial_segments']:>5} {lv['z_stride']:>7} "
              f"{lv['triangles']:>11,} {lv['reduction']*100:>7.1f}% "
              f"{lv['silhouette_deviation_m']:>9.2f}m "
              f"{lv['switch_distance_m']:>9,}m "
              f"{lv.get('deviation_px_at_switch', '-'):>7} "
              f"{lv.get('honest_from_m', 0)/1000 if lv.get('honest_from_m') else 0:>8.1f}km")
    total = sum(lv["triangles"] for lv in out)
    print(f"\nchain total {total:,} triangles across {len(out)} levels")
    print(f"at lod3 the whole 8 km station costs {out[-1]['triangles']:,} triangles")
    print("\nNote: deviation is computed against the model's MAX radius (the comms grid\n"
          "tip at 1,211 m). Most of the hull is far thinner -- under 480 m, much of it\n"
          "under 200 m -- so a single global LOD is dominated by the widest structure and\n"
          "decimates the thin sections far less aggressively than they could take.\n"
          "Per-section LOD would be substantially more effective. Recorded as future work.")


def base_radius(levels):
    return max(lv["max_radius_m"] for lv in levels)


if __name__ == "__main__":
    main()
