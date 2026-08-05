#!/usr/bin/env python3
"""Every control for the per-patch LOD work, fired one at a time.

A gate that cannot fail is a printout. Each block below breaks exactly one
thing and asserts the corresponding check goes RED.
"""
import hashlib
import io
import math
import os
import sys
import contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import interior as it          # noqa: E402
import drum_ground as dg       # noqa: E402

schema, profile = it.load()
sector = it.drum_sector(schema, profile)
dg.configure(schema, profile, sector)
table = dg.lod_table()
reach = dg.collision_reach_m()
FAILED = []


def report(name, fired, detail):
    print(f"  {'FIRES ' if fired else 'INERT '}  {name:<52} {detail}")
    if not fired:
        FAILED.append(name)


# --- 1. the digest ---------------------------------------------------------
saved = dg.PATCH_LOD_ERR_MM
dg.PATCH_LOD_ERR_MM = saved[:7] + (saved[7] + 1,) + saved[8:]
d = hashlib.blake2b(",".join(str(x) for x in dg.PATCH_LOD_ERR_MM).encode(),
                    digest_size=8).hexdigest()
report("digest: one millimetre moved", d != dg.PATCH_LOD_DIGEST,
       f"{d} != {dg.PATCH_LOD_DIGEST}")
dg.PATCH_LOD_ERR_MM = saved

# --- 2. the re-measure, against a terrain that moved -----------------------
real = dg.sample
dg.sample = lambda u, w, _r=real: (_r(u, w)[0] + 0.30 * math.sin(u * 400.0),
                                   _r(u, w)[1])
pa, pz = sorted({(a % dg.PATCHES_A, b) for a, b in
                 dg._representative_patches()})[0]
worst = max(abs(a - b) * 1000.0 for a, b in
            zip(dg.measure_patch_lod_error(pa, pz),
                dg.patch_lod_error_m(pa, pz)))
dg.sample = real
report("re-measure: terrain moved under the pin", worst > 0.5,
       f"{worst:.1f} mm drift at patch ({pa},{pz})")

# --- 3. the collision-tile floor -------------------------------------------
# Remove the floor entirely -- i.e. per-patch with nothing held for the tile --
# and count how many patch/distance samples inside the tile go COARSER than the
# drum-wide table. The shipped check asserts this is 0.
def unfloored(pa_, pz_):
    d_, out = 0.0, []
    for err in dg.patch_lod_error_m(pa_, pz_):
        d_ = max(d_, dg._switch_distance(err))
        out.append(d_)
    return out


coarser_floored = coarser_unfloored = 0
for pa_ in range(dg.PATCHES_A):
    for pz_ in range(dg.PATCHES_Z):
        sw_f = dg.patch_lod_table(pa_, pz_, table)
        sw_u = unfloored(pa_, pz_)
        for dm in range(5, int(reach), 5):
            g = dg.level_for_distance(dm, table)
            coarser_floored += max((i for i, s in enumerate(sw_f) if dm >= s),
                                   default=0) > g
            coarser_unfloored += max((i for i, s in enumerate(sw_u) if dm >= s),
                                     default=0) > g
report("collision floor: removed", coarser_unfloored > 0,
       f"{coarser_unfloored:,} samples inside {reach:.0f} m go coarser "
       f"without the floor, {coarser_floored} with it")

# --- 4. does the whole thing actually change the drawn set? ----------------
eye, _ = dg.stand_on_ground(schema, profile, sector, 270.0,
                            (dg.Z0 + dg.Z1) / 2.0)
pp = dg.visible_cost(eye, table)[0]
dw = sum(table[dg.level_for_distance(dg.patch_nearest_distance(a_, b_, eye),
                                     table)]["patch_triangles"]
         for a_ in range(dg.PATCHES_A) for b_ in range(dg.PATCHES_Z))
report("per-patch vs drum-wide at the worst eye", pp < dw,
       f"{pp:,} vs {dw:,} = {(1-pp/dw)*100:.1f}% fewer ground triangles")

# --- 5. built == counted, on the new path ----------------------------------
_v, tri, _g, _m = dg.visible_set(eye, table=table)
report("built set == counted set (must AGREE, not fire)", len(tri) == pp,
       f"built {len(tri):,} counted {pp:,}")

# --- 6. the selftest as a whole, with the floor removed --------------------
# The strongest control: break the module the way a careless change would and
# run the shipped selftest.
orig = dg.patch_lod_table
dg.patch_lod_table = lambda pa_, pz_, table_=None: tuple(unfloored(pa_, pz_))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = dg._selftest()
out = buf.getvalue()
dg.patch_lod_table = orig
line = [l for l in out.splitlines() if "passed" in l]
report("shipped _selftest with the collision floor removed", rc != 0,
       f"rc={rc}  {line[-1] if line else ''}")
for l in out.splitlines():
    if "FAIL" in l.upper() or "coarser" in l:
        print(f"        {l.strip()[:150]}")

print()
if FAILED:
    print(f"CONTROLS THAT DID NOT FIRE: {FAILED}")
    sys.exit(1)
print("every control fired")
