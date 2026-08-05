#!/usr/bin/env python3
"""Derive the per-patch LOD error table, fast, and emit it as a source pin.

The slow form in `per_patch_error.py` re-sampled the true field once per
stride; the true heights are the same for all five, and every coarse lattice
point IS a lod0 lattice point ("every vertex of every level is a vertex of
lod0" -- drum_ground.STRIDES' own comment), so one 33 x 33 grid per patch
serves all of them. 1.9M sample() calls become 305k.

VERIFIED AGAINST THE SLOW FORM, which is the control: --check compares this
table against scratchpad/per-patch-error.json and reports the worst
disagreement. Two derivations of one number, one of them fast.
"""
import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

import interior as it          # noqa: E402
import drum_ground as dg       # noqa: E402


def patch_errors(pa, pz):
    """Max |true - strided| for every stride, on one patch, in metres."""
    ia0, iz0 = pa * dg.PATCH_A, pz * dg.PATCH_Z
    true = [[dg.sample(((ia0 + da) % dg.CELLS_A) / dg.CELLS_A,
                       (iz0 + dz) / dg.CELLS_Z)[0]
             for dz in range(dg.PATCH_Z + 1)]
            for da in range(dg.PATCH_A + 1)]
    out = []
    for stride in dg.STRIDES:
        worst = 0.0
        for da in range(dg.PATCH_A + 1):
            ka0 = (da // stride) * stride
            ka1 = min(ka0 + stride, dg.PATCH_A)
            ta = 0.0 if ka1 == ka0 else (da - ka0) / (ka1 - ka0)
            for dz in range(dg.PATCH_Z + 1):
                kz0 = (dz // stride) * stride
                kz1 = min(kz0 + stride, dg.PATCH_Z)
                tz = 0.0 if kz1 == kz0 else (dz - kz0) / (kz1 - kz0)
                approx = (true[ka0][kz0] * (1 - ta) * (1 - tz)
                          + true[ka1][kz0] * ta * (1 - tz)
                          + true[ka0][kz1] * (1 - ta) * tz
                          + true[ka1][kz1] * ta * tz)
                e = abs(true[da][dz] - approx)
                if e > worst:
                    worst = e
        dtheta = 2.0 * math.pi * stride / dg.CELLS_A
        out.append(max(worst, dg.FLOOR_R * (1.0 - math.cos(dtheta / 2.0))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--emit", default=None)
    a = ap.parse_args()
    schema, profile = it.load()
    sector = it.drum_sector(schema, profile)
    dg.configure(schema, profile, sector)

    t0 = time.time()
    tbl = {}
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            tbl[(pa, pz)] = patch_errors(pa, pz)
    dt = time.time() - t0
    print(f"derived 280 patches x 5 strides in {dt:.0f} s")

    if a.check:
        ref = json.load(open(os.path.join(ROOT, "scratchpad",
                                          "per-patch-error.json")))["per_patch"]
        worst = 0.0
        for (pa, pz), errs in tbl.items():
            for i, e in enumerate(errs):
                worst = max(worst, abs(e - ref[f"{pa},{pz}"]["err_m"][i]))
        print(f"CONTROL against the slow derivation: worst disagreement "
              f"{worst*1000:.4f} mm "
              f"({'AGREE' if worst < 5e-4 else 'DISAGREE'})")

    if a.emit:
        mm = [[int(round(e * 1000)) for e in tbl[(pa, pz)]]
              for pa in range(dg.PATCHES_A) for pz in range(dg.PATCHES_Z)]
        lines = []
        for pa in range(dg.PATCHES_A):
            lines.append(f"    # pa {pa:2d}")
            for pz in range(dg.PATCHES_Z):
                v = mm[pa * dg.PATCHES_Z + pz]
                lines.append("    " + ",".join(f"{x:5d}" for x in v) + ",")
        with open(a.emit, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"wrote {a.emit}")


if __name__ == "__main__":
    main()
