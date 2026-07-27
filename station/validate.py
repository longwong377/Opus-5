#!/usr/bin/env python3
"""Canon assertions over the schema and the generated hull.

There is no human reviewing intermediate work and no GPU to look at the result,
so correctness that can be checked numerically must be checked numerically.
This runs in CI on every commit.

Exit code 0 = all assertions pass. Non-zero = a canon violation.
"""
import json
import math
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "station/schema/station.yaml")
PROFILE = os.path.join(ROOT, "station/schema/radius_profile.json")
MANIFEST = os.path.join(ROOT, "station/generated/hull_manifest.json")

# Target: RTX 4070 / RX 7800 XT class, 1440p60, 12 GB VRAM. The hull is the
# always-visible exterior shell, so it gets a small slice of the frame budget.
HULL_TRIANGLE_BUDGET = 400_000

results = []


def check(name, ok, detail=""):
    results.append((ok, name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    return ok


def main():
    schema = yaml.safe_load(open(SCHEMA))
    profile = json.load(open(PROFILE))
    features = schema["longitudinal"]["features"]

    canon_len = schema["station"]["overall_length_m"]["value"]

    # --- schema-level -------------------------------------------------------
    prev = None
    gaps = []
    for f in features:
        if prev is not None and abs(f["z0"] - prev) > 0.5:
            gaps.append((prev, f["z0"], f["id"]))
        prev = f["z1"]
    check("longitudinal features are gapless", not gaps,
          "" if not gaps else f"{len(gaps)} gap(s): " +
          ", ".join(f"{a}->{b} before {c}" for a, b, c in gaps))

    overlaps = [(features[i]["id"], features[i + 1]["id"])
                for i in range(len(features) - 1)
                if features[i]["z1"] > features[i + 1]["z0"] + 0.5]
    check("longitudinal features do not overlap", not overlaps, str(overlaps))

    check("features span the full station length",
          abs(features[0]["z0"]) < 0.5 and abs(features[-1]["z1"] - canon_len) < 1.0,
          f"{features[0]['z0']} .. {features[-1]['z1']} vs canon {canon_len}")

    # A parent's geometric extent must contain every subfeature, or the mesh
    # generator produces unassigned geometry.
    bad = []
    for f in features:
        for sub in f.get("subfeatures", []):
            if sub["z0"] < f["z0"] - 0.5 or sub["z1"] > f["z1"] + 0.5:
                bad.append(f"{sub['id']} escapes {f['id']}")
    check("subfeatures are contained by their parent", not bad, "; ".join(bad))

    # --- profile vs canon ---------------------------------------------------
    zs = [p["z_m"] for p in profile["profile"]]
    check("radius profile spans the canon length",
          abs((max(zs) - min(zs)) - canon_len) < 5.0,
          f"{max(zs) - min(zs):.1f} m vs canon {canon_len} m")

    check("no negative radii",
          all(p["radius_m"] >= 0 for p in profile["profile"]))

    # Independent cross-check that validates the calibration and the k rescale.
    xc = schema["radius_profile"]["cross_check"]
    for sec in ("red_section", "green_habitat"):
        m, t = xc[sec]["measured_d_m"], xc[sec]["table_d_m"]
        err = abs(m - t) / t
        check(f"{sec} measured vs table within 10%", err < 0.10, f"{err*100:.1f}%")

    # --- generated mesh -----------------------------------------------------
    if not os.path.exists(MANIFEST):
        check("hull mesh generated", False, "run station/generate_hull.py first")
    else:
        man = json.load(open(MANIFEST))
        check("hull length matches canon",
              abs(man["bounds"]["length_m"] - canon_len) < 1.0,
              f"{man['bounds']['length_m']} m vs canon {canon_len} m")
        check("no unassigned geometry",
              man["groups"].get("unassigned", 0) == 0,
              f"{man['groups'].get('unassigned', 0)} triangles unassigned")
        check("no degenerate quads emitted",
              man["degenerate_quads_skipped"] == 0)
        check("hull is closed at both ends", man["cap_triangles"] > 0)
        check(f"hull within triangle budget ({HULL_TRIANGLE_BUDGET:,})",
              man["triangles"] <= HULL_TRIANGLE_BUDGET,
              f"{man['triangles']:,} triangles")
        check("max radius agrees with profile",
              abs(man["bounds"]["max_radius_m"] - profile["max_radius_m"]) < 1.0,
              f"{man['bounds']['max_radius_m']} vs {profile['max_radius_m']}")

    # --- derived physics ----------------------------------------------------
    rot = schema["station"]["rotation"]
    r = rot["habitat_floor_radius_m"]["value"]
    w = rot["omega_rad_s"]["value"]
    g = w * w * r
    check("spin gravity at habitat floor is 1.0 g", abs(g - 9.81) < 0.05,
          f"{g:.3f} m/s^2 = {g/9.81:.3f} g")
    check("rotation period consistent with omega",
          abs(rot["period_s"]["value"] - 2 * math.pi / w) < 0.1,
          f"{2*math.pi/w:.2f} s")
    check("rotation rate below 3 rpm Coriolis tolerance",
          rot["rpm"]["value"] < 3.0, f"{rot['rpm']['value']} rpm")

    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
