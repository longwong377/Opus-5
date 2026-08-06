"""Run HEAD's NEW docking-bay assertions against the PRE-FIX module.

The claim under review is that six objects were rebuilt and that the assertions
added with them can fail. `docs/AAA-STANDARD.md` R4 is exactly "every assertion
has been deliberately broken and observed to fail", and the cheapest honest
version of that here is not to break HEAD's geometry -- it is to point the same
predicate at the geometry that shipped before the change.

The pre-fix module is `git show a3d414e:station/docking_bay.py`, the parent of
e6b0ec8. It is imported alongside HEAD's `station/` because docking_bay's own
imports (directory, dressing, interior, interior_kit, rooms, bespoke) did not
change between those two commits.
"""
import importlib.util
import os
import sys

ROOT = "/home/user/wt-judge-db"
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

spec = importlib.util.spec_from_file_location(
    "docking_bay_old", os.path.join(ROOT, "scratchpad/judge/docking_bay_old.py"))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

import docking_bay as new                                       # noqa: E402

FAILS = []
PASSES = []


def verdict(name, cond, detail=""):
    (PASSES if cond else FAILS).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}"
          + (f"   [{detail}]" if detail else ""))


def built(mod, fn, *a, **kw):
    q = mod._M()
    fn(q, *a, **kw)
    return q.v, q.t, q.g


print("=== HEAD's new assertions, run on the PRE-FIX geometry (a3d414e) ===")

# ---------------------------------------------------------------- 1. pendant
lv, lt, lg = built(old, old.floodlight, 0.0, old.BAY_H_M - old.GIRDER_D_M, 0.0)
lens = {round(lv[i][1], 5) for k, tri in enumerate(lt)
        if lg[k] == "bay_lamp" for i in tri}
verdict("the pendant's lens is a revolved solid, not a slab",
        len(lens) > 2, f"{len(lens)} distinct y in the old lens")

crown = [lv[i] for k, tri in enumerate(lt)
         if lg[k] == "_probe_crown" for i in tri]
verdict("the crown aperture is above the lens it shares a fitting with",
        bool(crown) and min(q[1] for q in crown) > max(lens),
        f"{len(crown)} crown vertices in the old fitting")

# --------------------------------------------------------- 3. ceiling ribs
if not hasattr(old, "ceiling_ribs"):
    verdict("every ceiling stringer stands on a girder panel point", False,
            "docking_bay_old has no ceiling_ribs: the object did not exist")
    verdict("...and the stringers hang BELOW the shell they stiffen", False,
            "same")

# ---------------------------------------------------------- 4. deck device
def covers(vs, ts, px, pz):
    for tri in ts:
        a, b, c2 = (vs[i] for i in tri)
        d1 = (px - b[0]) * (a[2] - b[2]) - (a[0] - b[0]) * (pz - b[2])
        d2 = (px - c2[0]) * (b[2] - c2[2]) - (b[0] - c2[0]) * (pz - c2[2])
        d3 = (px - a[0]) * (c2[2] - a[2]) - (c2[0] - a[0]) * (pz - a[2])
        if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
            return True
    return False


bars = new.DECK_DISC_D_M * new.EMBLEM_W_F * new.EMBLEM_H_F / (new.EMBLEM_BARS + 1)
if not hasattr(old, "deck_device"):
    # The old build's device is the inner filled disc `deck_marks` laid down.
    od = old._M()
    old._disc(od, 0.0, 0.0, old.DECK_DISC_D_M * 0.22, 0.03, "bay_emblem")
    verdict("the deck device is an outline, not a second filled disc",
            not covers(od.v, od.t, 0.0, bars * 0.5),
            "deck_device did not exist; the shipped device was "
            "_disc(r = 0.22 * DECK_DISC_D_M)")

# ---------------------------------------------------------------- 5. pylon
if not hasattr(old, "signage_pylon"):
    verdict("the pylon's plaques face the lane", False,
            "docking_bay_old has no signage_pylon: the object did not exist")

# -------------------------------------------------------------- 6. railing
if not hasattr(old, "ledge_railing"):
    verdict("the ledge railing stands on the first tread, at the lane edge",
            False,
            "docking_bay_old has no ledge_railing: the object did not exist")

# ------------------------------------------------------------- 7. budget
import budget as bud                                            # noqa: E402
ov, ot, og = old.docking_bay()[:3]
allow = bud.INTERIOR["visible_set_tris"]
verdict(f"one bay fits the interior structure frustum ({len(ot):,} tri)",
        len(ot) <= allow, f"{len(ot):,} of {allow:,}")
verdict("...and the bound can fail",
        not (2 * len(ot) <= allow),
        f"twice the OLD bay ({2 * len(ot):,}) is still inside {allow:,}")

nv, nt, ng = new.docking_bay()[:3]
print(f"\n  pre-fix bay: {len(ot):,} tri over {len(ov):,} verts, "
      f"{len(set(og))} groups")
print(f"  HEAD    bay: {len(nt):,} tri over {len(nv):,} verts, "
      f"{len(set(ng))} groups")
print(f"\n  {len(FAILS)} of {len(FAILS) + len(PASSES)} of HEAD's new "
      f"assertions FAIL on the pre-fix geometry")
