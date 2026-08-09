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

import aperture as aperture_mod
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
    with open(SCHEMA, encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    with open(PROFILE, encoding="utf-8") as f:
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


def _samples_with(samples, extra_z):
    """The profile's own samples plus the exact z values an aperture needs.

    Returns [(z, radius, plate_row_source)]. An inserted sample INHERITS the
    plate row of the sample it follows, so the plating pattern -- which is
    hashed on (row, column) -- does not shift by one along the whole 8 km of
    hull the moment a hole is cut in one end of it. Without that, cutting a
    docking bay would move every plate seam on the station.
    """
    out = [(s["z_m"], s["radius_m"], zi) for zi, s in enumerate(samples)]
    for z in extra_z:
        if any(abs(z - q[0]) <= 1e-9 for q in out):
            continue
        prev = None
        for k, (zz, _rr, _zi) in enumerate(out):
            if zz < z:
                prev = k
            else:
                break
        if prev is None or prev + 1 >= len(out):
            raise ValueError(f"aperture z {z} is outside the profile")
        z0, r0, zi = out[prev]
        z1, r1, _ = out[prev + 1]
        r = r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        out.insert(prev + 1, (z, r, zi))
    return out


def _plate_column(theta, radial_segments):
    """The lathe column an arbitrary angle falls in.

    `plate_offset` is indexed on the column, and a refined ring has columns the
    base ring does not. Deriving the column from the ANGLE rather than from the
    vertex index is what keeps an inserted vertex at the same radius as the
    plate it sits on -- otherwise the refined ring and the base ring disagree
    about where the hull is, and the surface tears along the stitch.
    """
    return int(math.floor(theta / (2.0 * math.pi) * radial_segments + 1e-9))


def build(radial_segments, z_stride, apertures=(), throats=True,
          cut_with=None):
    """Lathe the hull, cutting `apertures` out of it.

    `cut_with` defaults to `apertures` and exists only so `aperture._selftest`
    can build the two broken variants its negative controls need -- a cut with
    no throat, and a throat with no cut. Neither is reachable from the CLI.
    """
    schema, profile = load()
    samples = profile["profile"][::z_stride]
    features = schema["longitudinal"]["features"]

    plating = schema.get("hull_plating", {})
    plate_cfg = plating if plating.get("enabled") else None

    cut = apertures if cut_with is None else cut_with
    base_ang = [2.0 * math.pi * i / radial_segments
                for i in range(radial_segments)]
    fine_ang = aperture_mod.refined_angles(base_ang, apertures) \
        if apertures else base_ang
    band = aperture_mod.cut_band(apertures) if apertures else None
    collar = aperture_mod.collar_band(apertures) if apertures else None

    verts = []          # (x, y, z)
    rings = []          # list of (z, first_vertex_index, radius, feature)
    ring_ang = []       # the angle list each ring was built from

    for z, r, zi in _samples_with(samples, aperture_mod.extra_z(apertures)):
        base = len(verts)
        if r <= 0.05:
            # Degenerate ring: emit a single axis vertex so the surface closes
            # cleanly at the nose and tail instead of leaving a ragged hole.
            verts.append((0.0, 0.0, z))
            rings.append((z, base, 0.0, feature_at(features, z), True))
            ring_ang.append(None)
            continue
        ang = fine_ang if (band and band[0] <= z <= band[1]) else base_ang
        # See aperture.collar_band: the mouths are cut through machined
        # collar, not plate, because a plate step reverses the taper the
        # throat walls are welded to.
        plated = plate_cfg and not (
            collar and collar[0] - 1e-9 <= z <= collar[1] + 1e-9)
        for a in ang:
            rr = r
            if plated and r > plate_cfg.get("min_radius_m", 40):
                rr = r + plate_offset(
                    zi, _plate_column(a, radial_segments), plate_cfg)
            verts.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append((z, base, r, feature_at(features, z), False))
        ring_ang.append(ang)

    groups = {}
    degenerate = 0
    for k in range(len(rings) - 1):
        (z0, b0, r0, feat, pt0) = rings[k]
        (z1, b1, r1, _f1, pt1) = rings[k + 1]
        a0, a1 = ring_ang[k], ring_ang[k + 1]
        tris = groups.setdefault(feat, [])
        if pt0 and pt1:
            continue
        if pt0:                                  # fan from the axis point outward
            n = len(a1)
            for i in range(n):
                tris.append((b0, b1 + i, b1 + (i + 1) % n))
        elif pt1:
            n = len(a0)
            for i in range(n):
                tris.append((b0 + i, b1, b0 + (i + 1) % n))
        elif a0 is a1:
            n = len(a0)
            z_mid = 0.5 * (z0 + z1)
            for i in range(n):
                j = (i + 1) % n
                a, b, c, d = b0 + i, b0 + j, b1 + j, b1 + i
                if r0 <= 0.05 and r1 <= 0.05:
                    degenerate += 1
                    continue
                if cut and aperture_mod.is_cut(
                        cut, 0.5 * (a0[i] + a0[j] + (2.0 * math.pi if j == 0 else 0.0)),
                        z_mid):
                    continue
                tris.append((a, b, c))
                tris.append((a, c, d))
        else:
            # A stitch ring: one side carries the aperture columns and the
            # other does not. `cut_band`'s margin guarantees no aperture
            # reaches here, so this strip is never cut -- asserted in
            # `aperture._selftest`.
            _stitch(tris, b0, a0, b1, a1)

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
        n = len(ring_ang[idx])
        for i in range(n):
            j = (i + 1) % n
            if end == "tail":
                tris.append((centre, base + j, base + i))
            else:
                tris.append((centre, base + i, base + j))
        caps += n

    if apertures and throats:
        def ring_vertex(k, j):
            return rings[k][1] + j
        for gid, tri in aperture_mod.build_throats(
                apertures, verts, ring_vertex,
                [rr[0] for rr in rings], fine_ang).items():
            groups.setdefault(gid, []).extend(tri)

    return verts, groups, rings, degenerate, caps


def _stitch(tris, b0, a0, b1, a1):
    """Triangulate between two rings with different angle lists.

    A plain quad strip needs both rings to have the same columns. Where the
    refined band meets the base lathe they do not, so the strip is merged
    instead: walk both rings in angle, and at each step close the triangle
    against whichever side has the nearer next vertex. Winding follows the
    quad path's own convention -- ascending angle on the lower ring, then up.
    """
    two_pi = 2.0 * math.pi
    na, nb = len(a0), len(a1)
    if abs(a0[0] - a1[0]) > 1e-9:
        # The merge walks both rings forward from a common start. Two rings
        # that begin at different angles would be stitched with a half-turn
        # twist in it, and a twisted strip is still closed -- so nothing
        # downstream could catch it.
        raise ValueError(f"stitch rings start at {a0[0]} and {a1[0]}")
    i = j = 0
    while i < na or j < nb:
        nxt_a = (a0[i + 1] if i + 1 < na else a0[0] + two_pi) if i < na else None
        nxt_b = (a1[j + 1] if j + 1 < nb else a1[0] + two_pi) if j < nb else None
        take_a = nxt_b is None or (nxt_a is not None and nxt_a <= nxt_b)
        if take_a:
            tris.append((b0 + i % na, b0 + (i + 1) % na, b1 + j % nb))
            i += 1
        else:
            tris.append((b0 + i % na, b1 + (j + 1) % nb, b1 + j % nb))
            j += 1


def check_closure(verts, groups, apertures):
    """The lathe is closed except where it was deliberately opened.

    THIS GATE LIVES HERE BECAUSE THIS IS THE MODULE THAT BUILDS THE SURFACE.
    Session 3x's lesson, applied: `interior_kit`'s tag gate ran on a corridor
    with no doors and could not see the four defects in one, because the module
    that emits a piece has to be the module that measures it.

    Before any hole was cut, the lathe measured `open 0, non-manifold 0` -- so
    the assertion is not "few open edges", it is that every open edge lies on a
    bay mouth, that every bay mouth is a single closed loop, and that no two
    triangles share an edge with a third. All three can fail, and
    `aperture._selftest` fires each of them on purpose.

    Runs on the LATHE ONLY, before components and greebles are merged: those
    are unions of interpenetrating closed boxes and decal plates, and they
    carry 20,724 open and 9,708 non-manifold edges by construction. Measuring
    the cut against that noise floor would hide it.
    """
    import interior_kit as ik                                  # noqa: PLC0415
    tris = [t for g in groups.values() for t in g]
    op, nm = ik.boundary_edges(verts, tris)
    if nm:
        raise AssertionError(
            f"the lathe is non-manifold on {len(nm)} edges, e.g. {nm[0]}")
    buckets, stray = aperture_mod.classify_open_edges(apertures, verts, op)
    if stray:
        raise AssertionError(
            f"{len(stray)} of {len(op)} open edges are not on a bay mouth, "
            f"e.g. {stray[0]} -- the hull has a hole nobody cut")
    ragged = [i for i in buckets if not aperture_mod.loop_is_closed(buckets[i])]
    if apertures and ragged:
        raise AssertionError(
            f"{len(ragged)} bay mouths are not a single closed loop: {ragged}")
    empty = [i for i in buckets if not buckets[i]]
    if empty:
        raise AssertionError(f"{len(empty)} bay mouths were never opened: {empty}")
    return len(op)


def write_obj(path, verts, groups):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
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
    ap.add_argument("--no-apertures", action="store_true",
                    help="lathe a closed hull with no docking bay mouths. "
                         "The pre-3z behaviour, kept so the cut can be "
                         "diffed against it -- everything outside the "
                         "refined band is byte-identical either way")
    ap.add_argument("--greeble-detail", type=float, default=1.0,
                    help="fraction of greeble instances to keep; the LOD chain "
                         "uses this because surface detail does not decimate "
                         "the way the lathe does")
    a = ap.parse_args()

    schema, profile = load()
    apertures = () if a.no_apertures else aperture_mod.hull_apertures(
        schema, profile)
    verts, groups, rings, degenerate, caps = build(
        a.radial_segments, a.z_stride, apertures)

    # Components attach at the hull radius the profile reports for their z, so
    # they stay welded to the hull automatically when the profile changes.
    hull_tris = sum(len(t) for t in groups.values())
    throat_tris = sum(len(groups.get(g, ()))
                      for g in (aperture_mod.GROUP_THROAT,
                                aperture_mod.GROUP_LIP))
    rims = check_closure(verts, groups, apertures)

    def merge(parts, into):
        """Rebase a builder's local vertex indices onto the shared vertex list."""
        for gid, (gv, gt) in parts.items():
            base = len(verts)
            verts.extend(gv)
            groups[gid] = [(x + base, y + base, z + base) for x, y, z in gt]
            into[gid] = len(gt)

    comp_counts = {}
    if not a.no_components:
        # Component rib detail rides the SAME knob as greebles. A stiffener rib
        # is small surface decoration and `--greeble-detail` is already what a
        # coarse level turns down; giving ribs a second knob would let the two
        # disagree about what "far away" means, and `station/lod.py`'s model
        # would then describe a mesh nobody writes -- which is exactly what its
        # "the chain's triangle model matches what the generator wrote"
        # assertion caught when this was left at full detail.
        merge(components_mod.build_all(schema.get("components", []),
                                       profile["profile"],
                                       detail=a.greeble_detail), comp_counts)

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
        "apertures": len(apertures),
        "aperture_throat_triangles": throat_tris,
        "aperture_rim_open_edges": rims,
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
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    print(json.dumps(manifest, indent=1))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
