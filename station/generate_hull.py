#!/usr/bin/env python3
"""Generate the station hull mesh from the parametric schema.

Reads station/schema/station.yaml (longitudinal framework) and
station/schema/radius_profile.json (envelope radius, 1978 samples) and lathes
them into a closed surface of revolution, grouped by longitudinal feature.

Deterministic and engine-free -- this runs and is testable without Godot, a GPU
or a display. See docs/adr/0003-parametric-station-schema.md

Output: station/generated/hull.obj plus a manifest with budget numbers.
"""
import argparse
import json
import math
import os

import yaml

import components as components_mod
import greeble as greeble_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "station/schema/station.yaml")
PROFILE = os.path.join(ROOT, "station/schema/radius_profile.json")
OUTDIR = os.path.join(ROOT, "station/generated")

# The station is 8 km long and read at 4.07 m sample spacing; decimating the
# profile below that gains nothing, so longitudinal resolution is the source
# resolution. Radial segments are the real tunable.
DEFAULT_RADIAL_SEGMENTS = 64
DEFAULT_Z_STRIDE = 1


def load():
    with open(SCHEMA) as f:
        schema = yaml.safe_load(f)
    with open(PROFILE) as f:
        profile = json.load(f)
    return schema, profile


def plate_offset(zi, si, cfg):
    """Deterministic radial offset for the hull plate a vertex belongs to.

    B5's hull reads as assembled plating, not a smooth shell. Rather than model
    every plate as separate geometry -- which would quadruple vertex count for
    detail invisible at station scale -- the lathe radius is modulated per plate
    cell. Adjacent cells differ by a metre or two, which is the real order for
    spacecraft plating, and the shared vertices at cell boundaries bevel rather
    than step. That reads correctly from a Starfury alongside and costs nothing.

    Deterministic in (row, col) so regeneration is byte-identical -- required
    for the CI geometry check to mean anything.
    """
    row = zi // cfg["rows_per_plate"]
    col = si // cfg["segs_per_plate"]
    h = (row * 73856093) ^ (col * 19349663)
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h / 0xFFFFFFFF) * 2.0 - 1.0) * cfg["depth_m"]


def feature_at(features, z):
    """Which longitudinal feature contains this z, for mesh grouping."""
    for f in features:
        if f["z0"] <= z <= f["z1"]:
            return f["id"]
    return "unassigned"


def build(radial_segments, z_stride):
    schema, profile = load()
    samples = profile["profile"][::z_stride]
    features = schema["longitudinal"]["features"]

    plating = schema.get("hull_plating", {})
    plate_cfg = plating if plating.get("enabled") else None

    verts = []          # (x, y, z)
    rings = []          # list of (z, first_vertex_index, radius, feature)

    for zi, s in enumerate(samples):
        z, r = s["z_m"], s["radius_m"]
        base = len(verts)
        if r <= 0.05:
            # Degenerate ring: emit a single axis vertex so the surface closes
            # cleanly at the nose and tail instead of leaving a ragged hole.
            verts.append((0.0, 0.0, z))
            rings.append((z, base, 0.0, feature_at(features, z), True))
            continue
        for i in range(radial_segments):
            a = 2.0 * math.pi * i / radial_segments
            rr = r
            if plate_cfg and r > plate_cfg.get("min_radius_m", 40):
                rr = r + plate_offset(zi, i, plate_cfg)
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append((z, base, r, feature_at(features, z), False))

    groups = {}
    degenerate = 0
    for (z0, b0, r0, feat, pt0), (z1, b1, r1, _f1, pt1) in zip(rings, rings[1:]):
        tris = groups.setdefault(feat, [])
        n = radial_segments
        if pt0 and pt1:
            continue
        if pt0:                                  # fan from the axis point outward
            for i in range(n):
                tris.append((b0, b1 + i, b1 + (i + 1) % n))
        elif pt1:
            for i in range(n):
                tris.append((b0 + i, b1, b0 + (i + 1) % n))
        else:
            for i in range(n):
                j = (i + 1) % n
                a, b, c, d = b0 + i, b0 + j, b1 + j, b1 + i
                if r0 <= 0.05 and r1 <= 0.05:
                    degenerate += 1
                    continue
                tris.append((a, b, c))
                tris.append((a, c, d))

    # Cap any open end so the hull is a closed volume -- required for the
    # airtightness assertion and for meaningful collision.
    caps = 0
    for idx, end in ((0, "tail"), (len(rings) - 1, "nose")):
        z, base, r, feat, is_pt = rings[idx]
        if is_pt or r <= 0.05:
            continue
        centre = len(verts)
        verts.append((0.0, 0.0, z))
        tris = groups.setdefault(feat, [])
        for i in range(radial_segments):
            j = (i + 1) % radial_segments
            if end == "tail":
                tris.append((centre, base + j, base + i))
            else:
                tris.append((centre, base + i, base + j))
        caps += radial_segments

    return verts, groups, rings, degenerate, caps


def write_obj(path, verts, groups):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("# Babylon 5 station hull -- generated from station/schema/station.yaml\n")
        f.write("# Do not edit by hand. Regenerate with station/generate_hull.py\n")
        for x, y, z in verts:
            f.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
        for name, tris in groups.items():
            f.write(f"g {name}\no {name}\n")
            for a, b, c in tris:
                f.write(f"f {a+1} {b+1} {c+1}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radial-segments", type=int, default=DEFAULT_RADIAL_SEGMENTS)
    ap.add_argument("--z-stride", type=int, default=DEFAULT_Z_STRIDE)
    ap.add_argument("--out", default=os.path.join(OUTDIR, "hull.obj"))
    ap.add_argument("--no-components", action="store_true",
                    help="core hull only, for isolating lathe issues")
    ap.add_argument("--no-greebles", action="store_true",
                    help="skip surface detail, for isolating silhouette issues")
    ap.add_argument("--greeble-detail", type=float, default=1.0,
                    help="fraction of greeble instances to keep; the LOD chain "
                         "uses this because surface detail does not decimate "
                         "the way the lathe does")
    a = ap.parse_args()

    verts, groups, rings, degenerate, caps = build(a.radial_segments, a.z_stride)

    # Components attach at the hull radius the profile reports for their z, so
    # they stay welded to the hull automatically when the profile changes.
    schema, profile = load()
    hull_tris = sum(len(t) for t in groups.values())

    def merge(parts, into):
        """Rebase a builder's local vertex indices onto the shared vertex list."""
        for gid, (gv, gt) in parts.items():
            base = len(verts)
            verts.extend(gv)
            groups[gid] = [(x + base, y + base, z + base) for x, y, z in gt]
            into[gid] = len(gt)

    comp_counts = {}
    if not a.no_components:
        merge(components_mod.build_all(schema.get("components", []),
                                       profile["profile"]), comp_counts)

    # Surface detail last, so it inherits the finished profile rather than a
    # provisional one. Greebles carry no canon dimensions of their own -- they
    # read the same radius profile the lathe does. See station/greeble.py.
    greeble_counts, greeble_stats = {}, {}
    if not a.no_greebles:
        parts, greeble_stats = greeble_mod.build_all(
            schema.get("greebles", {}), schema["longitudinal"]["features"],
            profile["profile"], a.greeble_detail)
        merge(parts, greeble_counts)

    write_obj(a.out, verts, groups)

    tris = sum(len(t) for t in groups.values())
    zs = [v[2] for v in verts]
    radii = [math.hypot(v[0], v[1]) for v in verts]
    manifest = {
        "source_schema": "station/schema/station.yaml",
        "radial_segments": a.radial_segments,
        "z_stride": a.z_stride,
        "rings": len(rings),
        "vertices": len(verts),
        "triangles": tris,
        "groups": {k: len(v) for k, v in sorted(groups.items())},
        "hull_triangles": hull_tris,
        "component_triangles": sum(comp_counts.values()),
        "component_instances": sum(c["count"] for c in schema.get("components", [])) if not a.no_components else 0,
        "greeble_detail": a.greeble_detail,
        "greeble_triangles": sum(greeble_counts.values()),
        # Assemblies and conduit runs are containers, not fittings -- counting
        # them alongside their own contents would inflate the instance figure the
        # budget report quotes.
        "greeble_assemblies": greeble_stats.get("assembly", 0),
        "greeble_conduit_runs": greeble_stats.get("conduit_run", 0),
        "greeble_instances": sum(v for k, v in greeble_stats.items()
                                 if k not in ("assembly", "conduit_run")),
        "greeble_instances_by_kind": {k: v for k, v in sorted(greeble_stats.items())
                                      if k not in ("assembly", "conduit_run")},
        "degenerate_quads_skipped": degenerate,
        "cap_triangles": caps,
        "bounds": {
            "z_min_m": round(min(zs), 2),
            "z_max_m": round(max(zs), 2),
            "length_m": round(max(zs) - min(zs), 2),
            "max_radius_m": round(max(radii), 2),
        },
    }
    mpath = os.path.join(os.path.dirname(a.out), "hull_manifest.json")
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1)

    print(json.dumps(manifest, indent=1))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
