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
sys.path.insert(0, os.path.join(ROOT, "station"))
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
        # A manifest left behind by station/lod.py describes a decimated level,
        # not the mesh the engine consumes, and every assertion below would then
        # be measuring the wrong thing. Catch it explicitly rather than letting
        # it surface as a confusing canon violation.
        check("manifest describes lod0, not a decimated level",
              man.get("radial_segments") == 64 and man.get("z_stride") == 1,
              f"segs={man.get('radial_segments')} stride={man.get('z_stride')} "
              f"-- rerun station/generate_hull.py")
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
        # Once components are present the model's max radius is the
        # communications grid tip, not the hull. Check the two separately.
        comms = schema["communications_grid"]["span_m"]["value"] / 2.0
        check("model max radius reaches the comms grid tip",
              man["bounds"]["max_radius_m"] > comms,
              f"{man['bounds']['max_radius_m']} m vs half-span {comms} m")
        check("model max radius is not implausibly beyond the grid",
              man["bounds"]["max_radius_m"] < comms * 1.6,
              f"{man['bounds']['max_radius_m']} m")
        check("every schema component produced geometry",
              all(c["id"] in man["groups"] for c in schema.get("components", [])),
              str([c["id"] for c in schema.get("components", []) if c["id"] not in man["groups"]]))

    # --- procedural surface detail ------------------------------------------
    greebles = schema.get("greebles", {})
    if greebles.get("enabled"):
        import greeble

        # Bare hull is a bug, not a style. If a new longitudinal feature is added
        # without a greeble zone it silently ships as an untextured tube, and
        # nothing else in the pipeline would notice.
        zoned = {z["feature"] for z in greebles["zones"]}
        naked = [f["id"] for f in features
                 if f["id"] not in zoned
                 and not (f.get("subfeatures")
                          and all(s["id"] in zoned for s in f["subfeatures"]))]
        check("every longitudinal feature is greebled", not naked, str(naked))

        # The whole point of hashing on (feature, cell) instead of on a global
        # RNG is that regeneration is byte-identical. Assert it rather than
        # trust it: a stray dependency on dict or call order would otherwise
        # only show up as an unexplained diff in committed geometry.
        runs = [greeble.build_all(greebles, features, profile["profile"])[0]
                for _ in range(2)]
        same = all(runs[0][g] == runs[1][g] for g in runs[0]) and \
            set(runs[0]) == set(runs[1])
        check("greeble pass is deterministic across runs", same)

    # --- sector extents (C-003 resolved) ------------------------------------
    sec = schema["sectors"]
    ex = sec["extents_m"]
    order = sec["order_aft_to_fore"]
    check("sector order matches the extents table",
          set(order) == set(ex), f"{order} vs {sorted(ex)}")
    span = sum(v["z1"] - v["z0"] for v in ex.values())
    check("sector extents tile the whole station",
          abs(span - canon_len) < 1.0, f"{span} m of {canon_len} m")
    prev = None
    holes = []
    for name in order:
        v = ex[name]
        if prev is not None and abs(v["z0"] - prev) > 0.5:
            holes.append(f"{prev}->{v['z0']} before {name}")
        prev = v["z1"]
    check("sector extents are contiguous aft to fore", not holes, "; ".join(holes))
    # Brown is a radial designation, not a length -- it must not acquire extents.
    # The sector assignment is still disputed (Green/Brown transposition), so the
    # schema must keep saying so. A future session that quietly drops this flag
    # and builds interior layout against these extents is the failure this guards.
    check("sector assignment is still flagged as open",
          sec.get("assignment_status") == "OPEN_BLOCKING",
          "C-003 assignment must stay flagged until the transposition closes")
    check("Brown is not in the longitudinal extents",
          "brown" not in ex,
          "INV-009: Brown is the outermost ring, not a length of station")

    # --- derived physics ----------------------------------------------------
    rot = schema["station"]["rotation"]
    r = rot["habitat_floor_radius_m"]["value"]
    w = rot["omega_rad_s"]["value"]
    g0 = rot["standard_gravity_m_s2"]["value"]
    g = w * w * r
    # Tight: this is a derived value, so any drift means the schema's own
    # constants have stopped agreeing with each other.
    check("spin gravity at habitat floor is 1.0 g", abs(g / g0 - 1.0) < 1e-6,
          f"{g:.6f} m/s^2 = {g/g0:.9f} g")
    check("rotation period consistent with omega",
          abs(rot["period_s"]["value"] - 2 * math.pi / w) < 1e-4,
          f"{2*math.pi/w:.6f} s")
    check("rpm consistent with period",
          abs(rot["rpm"]["value"] - 60.0 / rot["period_s"]["value"]) < 1e-4,
          f"{60.0/rot['period_s']['value']:.6f}")
    check("rotation rate below 3 rpm Coriolis tolerance",
          rot["rpm"]["value"] < 3.0, f"{rot['rpm']['value']} rpm")

    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
