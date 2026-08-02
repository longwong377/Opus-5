#!/usr/bin/env python3
"""EXPORT THE HABITAT DRUM — the one place the station build refuses.

`tools/export_station.py` builds 70 ring decks and declines the 71st with

    green_1_0: ValueError: green ring 1 is not a ring deck: the habitat drum --
               the Garden, the townscape, the tram and the spokes. An open 8 km
               barrel, no

which is a CORRECT refusal and left the drum out of the built station entirely.
The Garden, Earhart's, the zen garden, the townscape, the water reclamation, the
ground tram -- **eleven register locations, and the largest single volume on the
station** -- were absent from everything exported today.

The drum is not a ring of decks and must not be built like one. It is an open
barrel with a heightfield floor, and `station/drum_walk.py` and
`station/drum_ground.py` already know how to make it walkable: `ground_patch`
builds one tile of ground at one LOD, `collision_stride()` derives the coarsest
stride whose measured error stays under a step, and `stand_at` puts feet on it.

    r = 278.3 m, circumference 1,749 m, z extent 2,586 m
    patch 124.9 x 129.4 m  ->  14 around x 20 along = 280 patches

THE STRIDE IS DERIVED, NOT CHOSEN, and that is `drum_walk`'s own rule: the
collision ground is built at ONE stride everywhere, so every shared edge vertex
comes from the same `_vertex(ia, iz)` call on both sides and the seam is exact
rather than repaired. The render ground mixes LOD levels and clamps borders; the
collision ground does not mix, deliberately -- a heightfield with holes in it is
a heightfield you fall through, and under spin gravity you then accelerate
outward for thirty kilometres.

Run: python3 tools/export_drum.py --dry-run
     python3 tools/export_drum.py --max-patches 4
     python3 tools/export_drum.py
"""
import argparse
import json
import math
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import deck as D                                                # noqa: E402
import drum_ground as dg                                        # noqa: E402
import drum_walk as DW                                          # noqa: E402
import interior as it                                           # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/drum")


def grid(schema, profile, sector):
    """How many patches go round the drum and along it.

    From the drum's OWN patch span and its OWN extents, so a change to either
    moves this count rather than leaving it stale.
    """
    ex = schema["sectors"]["extents_m"][sector]
    r = it.sector_radius(schema, profile, sector)
    pa_m, pz_m = DW.patch_span_m()
    na = int(round(2.0 * math.pi * r / pa_m))
    nz = int(round((ex["z1"] - ex["z0"]) / pz_m))
    return na, nz, r, ex


def _write(stem, V, T, G):
    obj = os.path.join(OUT, stem + ".obj")
    glb = os.path.join(OUT, stem + ".glb")
    D.write_obj(obj, V, T, G)
    with open(obj) as f:
        nf = f.read().count("\nf ")
    if nf != len(T):
        raise AssertionError(f"{stem}: wrote {nf} faces for {len(T)} triangles")
    import export_gltf                                          # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj, "--out", glb]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    if not os.path.exists(glb) or os.path.getsize(glb) < 1024:
        raise AssertionError(f"{stem}: glb missing or empty")
    os.remove(obj)
    return os.path.getsize(glb)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-patches", type=int, default=0)
    ap.add_argument("--stride", type=int, default=0)
    a = ap.parse_args(argv)

    schema, profile, sector = DW.drum()
    na, nz, r, ex = grid(schema, profile, sector)
    # `collision_stride` RETURNS (stride, table). Taking it whole put a tuple
    # into an f-string and into `ground_patch(stride=)`; the first run printed a
    # five-level LOD table where a number should have been, which is the tell.
    stride = a.stride or DW.collision_stride()[0]
    total = na * nz

    print(f"\nTHE HABITAT DRUM\n")
    print(f"  sector {sector}: r = {r:.1f} m, circumference "
          f"{2 * math.pi * r:,.0f} m, z {ex['z0']:.0f}..{ex['z1']:.0f} "
          f"({ex['z1'] - ex['z0']:,.0f} m)")
    print(f"  {na} patches around x {nz} along = {total} patches, "
          f"collision stride {stride} (derived by drum_walk.collision_stride)")
    if a.dry_run:
        print("\n  dry run -- nothing built.")
        return 0

    os.makedirs(OUT, exist_ok=True)
    man = {"patches": [], "na": na, "nz": nz, "stride": stride,
           "sector": sector, "started": time.time()}
    mpath = os.path.join(OUT, "drum_manifest.json")
    todo = [(ia, iz) for ia in range(na) for iz in range(nz)]
    if a.max_patches:
        todo = todo[:a.max_patches]

    for n, (ia, iz) in enumerate(todo, 1):
        stem = f"drum_a{ia:02d}_z{iz:02d}"
        t0 = time.time()
        try:
            # `ground_patch` RETURNS PER-TRIANGLE GROUP NAMES; `deck.write_obj`
            # takes (name, lo, hi) SPANS. `drum_walk._spans` is the converter and
            # `render_ground` already uses it -- the third time today two group
            # formats with the same shape have cost a run.
            rv, rt, rg, _rm = dg.ground_patch(ia, iz, stride=1)
            rb = _write(stem, rv, rt, DW._spans(rg))
            cv, ct, cg, _cm = dg.ground_patch(ia, iz, stride=stride)
            cb = _write(stem + "_collision", cv, ct, DW._spans(cg))
            row = {"key": stem, "ok": True, "tris": len(rt),
                   "collision_tris": len(ct),
                   "mb": round(rb / 1e6, 2), "collision_mb": round(cb / 1e6, 2),
                   "seconds": round(time.time() - t0, 1)}
            print(f"  [{n}/{len(todo)}] {stem}: {len(rt):,} tri + "
                  f"{len(ct):,} collision, {row['mb']:.1f} MB, "
                  f"{row['seconds']:.1f} s")
        except Exception as e:                                  # noqa: BLE001
            tb = traceback.format_exc()
            where = [l.strip() for l in tb.splitlines()
                     if l.strip().startswith("File ")]
            row = {"key": stem, "ok": False, "why": f"{type(e).__name__}: {e}",
                   "at": where[-1] if where else ""}
            print(f"  [{n}/{len(todo)}] {stem}: FAILED -- {row['why'][:100]}"
                  f"\n        {row['at']}")
        man["patches"].append(row)
        man["elapsed_s"] = round(time.time() - man["started"], 1)
        with open(mpath, "w") as f:
            json.dump(man, f, indent=1)

    good = [p for p in man["patches"] if p.get("ok")]
    print(f"\n  BUILT {len(good)} of {len(todo)} patches, "
          f"{sum(p['tris'] for p in good):,} render tri + "
          f"{sum(p['collision_tris'] for p in good):,} collision tri, "
          f"{sum(p['mb'] + p['collision_mb'] for p in good):.0f} MB, in "
          f"{man['elapsed_s'] / 60:.0f} min")
    return 0 if len(good) == len(todo) else 1


if __name__ == "__main__":
    sys.exit(main())
