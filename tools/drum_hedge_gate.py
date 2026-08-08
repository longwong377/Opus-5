#!/usr/bin/env python3
"""DOES THE COLLISION MESH THE DRUM SHIPS STOP A BODY AT A HEDGE?

`station/drum_dressing.py --ribbon-collision` already answers "do the boxes
`ribbon_boxes()` returns stop a ray", and it answers it exhaustively -- 9,510
probes, every solid cross-section on the drum, both sides. It cannot answer the
question this file exists for, and the difference is the whole reason this file
exists:

    **A gate on the function says nothing about whether the exporter calls it.**

CLAUDE.md lists nine instances of finished, tested machinery with no caller on
the shipped path, and records that `tools/wiring.py` catches most of them by
scanning source for a reference -- and that the ninth slipped under it anyway,
because "a static scan can tell you a caller exists; only running the thing
tells you the caller runs". So this assembles the drum's COLLISION PART LIST the
way `export_drum.main` assembles it, from `export_drum`'s own functions, and
fires the probes at the merged result. Delete the `("ribbons", ...)` line from
the exporter and this goes red; `station/drum_dressing.py --ribbon-collision`
stays green.

WHAT IT ASSEMBLES, AND WHAT IT LEAVES OUT ON PURPOSE. Everything in `cparts`
except the ground: features, ribbons, the end caps and spokes, and the
townscape's masonry. The ground is 573,440 triangles and twenty minutes of the
container's four cores, and a horizontal ray fired at chest height across a
hedge cannot be stopped by the floor it is fired above -- so including it would
buy nothing and cost the session. `--with-ground` adds it for anyone who wants
to check that claim rather than take it: run both and compare the STOPPED and
`early` figures by eye. Nothing here diffs them for you, and this sentence says
so rather than promising a comparison the code does not make.

THE CONTROL IS NOT A FLAG THAT WEAKENS THE GATE. `--without-ribbons` rebuilds
the same assembly with the ribbon part dropped -- the state the exporter was in
before INV-1244 -- and the gate must FAIL. A gate whose control cannot fail is
this project's oldest defect wearing a new hat.

Run: python3 tools/drum_hedge_gate.py                 # ~1 minute
     python3 tools/drum_hedge_gate.py --without-ribbons   # the control, must FAIL
     python3 tools/drum_hedge_gate.py --lines 12      # a quick subset
     python3 tools/drum_hedge_gate.py --with-ground   # +573,440 tri, slow
"""
import argparse
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import collision as C                                             # noqa: E402
import drum_dressing as dd                                        # noqa: E402
import drum_ground as dg                                          # noqa: E402
import drum_walk as DW                                            # noqa: E402
import export_drum as ED                                          # noqa: E402


def collision_parts(with_ribbons=True, with_ground=False):
    """The drum's collision parts, composed the way `export_drum.main` does.

    IMPORTED RATHER THAN RESTATED, for the reason `tools/drum_interact.py`
    gives about the render parts: a second copy of the exporter's list is the
    copy that drifts, and the drift is invisible until a player walks into it.
    `feature_boxes`, `ribbon_boxes`, `_dressing_solid` and `prop_boxes` are all
    the exporter's own calls.
    """
    import export_scene as ES                                     # noqa: PLC0415
    schema, profile, sector = DW.drum()
    eye = (0.0, -(dg.FLOOR_R - 2.0), (dg.Z0 + dg.Z1) / 2.0)
    parts = [(n, v, t, list(g))
             for n, v, t, g in ES.drum_parts(schema, profile, sector, eye)]
    by = {n: i for i, (n, _v, _t, _g) in enumerate(parts)}

    out = []
    fv, ft, _fn = ED.feature_boxes()
    out.append(("features", fv, ft))
    if with_ribbons:
        rv, rt, _rn = dd.ribbon_boxes()
        out.append(("ribbons", rv, rt))
    for n, v, t, _g in parts:
        if n in ("endcap_fore", "endcap_aft", "spokes"):
            out.append((n, v, t))
    tsi = by["townscape"]
    tv, tt, tg = parts[tsi][1], parts[tsi][2], parts[tsi][3]
    tspans = DW._spans([x.split("__")[-1] for x in tg])
    tboxes = C.prop_boxes(tv, tt, tspans, solid=ED._dressing_solid)
    bv, bt = C.boxes_mesh(tboxes, lambda pts: pts)
    out.append(("townscape", bv, bt))
    if with_ground:
        gv, gt, _gg = ED.full_ground(DW.collision_stride()[0])
        out.append(("ground", gv, gt))
    return out


def _merge(parts):
    V, T = [], []
    for _n, v, t in parts:
        off = len(V)
        V.extend(v)
        T.extend((a + off, b + off, c + off) for a, b, c in t)
    return V, T


# THE QUESTION THIS GATE ASKS IS *NOT* "IS THE COLLIDER WHERE THE HEDGE IS".
# That one belongs to `drum_dressing --ribbon-collision`, which casts at each
# ribbon against THAT RIBBON'S OWN boxes and answers it exhaustively (worst
# 0.311 m against a 0.315 m derived slack). Asked of the whole assembly it is
# ill-posed, and two rewrites of this file went into finding out why:
#
#   * a hedgerow standard -- a tree left uncut in the hedge line -- puts a
#     trunk collider in front of a probe. First version: "3.451 m gap". It was
#     a measurement of a tree.
#   * hedgerows ARE parcel boundaries, so they meet at corners, and a probe
#     fired 4 m out near a corner crosses the NEIGHBOURING run's box. Second
#     version: "2.857 m gap". Dumped, the box was 24.3 m long, 1.51 m wide,
#     with a 0.265 m chord sag against its own 0.315 m limit -- entirely
#     legal. The ray was passing through the 0.3 m of that box which stands
#     above the neighbour's own wobbled crown, over a hedge and inside its
#     collider, which is air no walking body meets and is not a defect.
#
# So the well-posed shipped-path question is directional: **a body walking at a
# hedge must be stopped at or before it, never after.** Early is the drum being
# dense; late is walking through a hedge. Each probe lands in:
#   STOPPED   something solid at or before the visible surface (+ slack).
#   THROUGH   nothing within reach, or the first solid thing is BEYOND the
#             hedge. Before INV-1244 this was every probe.
# and `blocked` is printed beside them as information: how many were decided by
# a neighbour rather than by the hedge itself.
def run(with_ribbons=True, with_ground=False, max_lines=None, verbose=True):
    t0 = time.time()
    parts = collision_parts(True, with_ground)
    others = [p for p in parts if p[0] != "ribbons"]
    OV, OT = _merge(others)
    if with_ribbons:
        V, T = _merge(parts)
    else:
        V, T = OV, OT
    build_s = time.time() - t0
    if verbose:
        print(f"\nthe drum's collision mesh, as the exporter composes it "
              f"({build_s:.1f}s)")
        for n, _v, t in parts:
            mark = "" if (with_ribbons or n != "ribbons") else "   [WITHHELD]"
            print(f"    {n:<12} {len(t):>9,} tri{mark}")
        print(f"    {'TOTAL':<12} {len(T):>9,} tri")

    # ONE INDEX OVER THE WHOLE MESH. `grid_index` at 8 m puts a probe's
    # candidate set at the handful of triangles beside it, which is what makes
    # asking every cross-section on the drum affordable at all.
    t0 = time.time()
    idx = C.grid_index(V, T)
    oidx = idx if not with_ribbons else C.grid_index(OV, OT)
    index_s = time.time() - t0

    fld = dd.field()
    reach = 2.0 * dd.RIBBON_PROBE_M
    # EVERY SOLID RIBBON'S RENDER, in one mesh, so a probe can tell "my hedge"
    # from "the hedge at the corner of the next parcel".
    AV, AT, AG = [], [], []
    for i, ln in enumerate(fld["lines"]):
        if dd.RIBBON_GROUPS[ln.kind][0] != dd.RIBBON_SOLID_SIDE:
            continue
        side, top = dd.RIBBON_GROUPS[ln.kind]
        dd._ribbon(AV, AT, AG, ln.points, ln.height_m, ln.width_m, side, top,
                   dd.HEDGE_STEP_M[0], dd.HEDGE_WOBBLE_M,
                   seed=f"{dd.SEED}/rib/{i}")
    aidx = C.grid_index(AV, AT)
    tot = {"probes": 0, "visible": 0, "blocked": 0, "stopped": 0,
           "through": 0, "late_max": -9.9, "early_max": 0.0}
    per = {}
    n_line = 0
    t0 = time.time()
    for i, ln in enumerate(fld["lines"]):
        if dd.RIBBON_GROUPS[ln.kind][0] != dd.RIBBON_SOLID_SIDE:
            continue
        if max_lines is not None and n_line >= max_lines:
            break
        n_line += 1
        seed = f"{dd.SEED}/rib/{i}"
        RV, RT, RG = [], [], []
        side, top = dd.RIBBON_GROUPS[ln.kind]
        dd._ribbon(RV, RT, RG, ln.points, ln.height_m, ln.width_m, side, top,
                   dd.HEDGE_STEP_M[0], dd.HEDGE_WOBBLE_M, seed=seed)
        ridx = C.grid_index(RV, RT)
        slack = dd._ribbon_slack(ln.width_m)
        row = per.setdefault(ln.kind, {
            "probes": 0, "visible": 0, "blocked": 0, "stopped": 0,
            "through": 0, "late_max": -9.9, "early_max": 0.0,
            "slack_m": round(slack, 3)})
        for o, d, _half in dd._ribbon_probes(ln, seed=seed):
            row["probes"] += 1
            tot["probes"] += 1
            hr = C.cast_short(o, d, RV, RT, ridx, reach)
            if hr is None:
                continue
            row["visible"] += 1
            tot["visible"] += 1
            ho = C.cast_short(o, d, OV, OT, oidx, reach)
            ha = C.cast_short(o, d, AV, AT, aidx, reach)
            if (ho is not None and ho < hr) or \
                    (ha is not None and ha < hr - 1e-6):
                row["blocked"] += 1
                tot["blocked"] += 1
            hc = C.cast_short(o, d, V, T, idx, reach)
            if hc is None or hc > hr + slack:
                row["through"] += 1
                tot["through"] += 1
                if hc is not None:
                    for r in (row, tot):
                        r["late_max"] = max(r["late_max"], hc - hr)
                continue
            row["stopped"] += 1
            tot["stopped"] += 1
            for r in (row, tot):
                r["late_max"] = max(r["late_max"], hc - hr)
                r["early_max"] = max(r["early_max"], hr - hc)
    cast_s = time.time() - t0

    vis = tot["visible"]
    frac = (tot["stopped"] / vis) if vis else 0.0
    checks = [
        ("the probes are aimed at ribbons a player can see",
         vis > 0 and vis == tot["probes"],
         f"{vis} of {tot['probes']}"),
        ("THE SHIPPED COLLISION MESH STOPS EVERY ONE OF THEM",
         frac >= 1.0,
         f"{tot['stopped']} of {vis} ({frac * 100:.1f}%), "
         f"{tot['through']} walked through"),
        ("...at or before the hedge, never after it",
         tot["late_max"] <= max(dd._ribbon_slack(w) for w in
                                (dd.HEDGE_W_M, dd.PARK_HEDGE_W_M)),
         f"worst late {tot['late_max']:+.3f} m; worst early "
         f"{tot['early_max']:.3f} m, which is a neighbour and not a defect"),
    ]
    ok = all(c[1] for c in checks)
    if verbose:
        print(f"\n  index {index_s:.1f}s, {cast_s:.1f}s of casting, "
              f"{n_line} solid ribbons"
              + ("" if with_ribbons
                 else "   [CONTROL: the ribbon part is not in the assembly]"))
        for name, good, detail in checks:
            print(f"  [{'PASS' if good else 'FAIL'}] {name}: {detail}")
        for k in sorted(per):
            r = per[k]
            print(f"    {k:<12} {r['stopped']:>6,} stopped / "
                  f"{r['through']:>6,} through, of {r['visible']:>6,} probes "
                  f"({r['blocked']:,} of them decided by a neighbour); "
                  f"late {r['late_max']:+.3f} m, early {r['early_max']:.3f} m")
    return ok, tot, per


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--without-ribbons", action="store_true",
                    help="the control: assemble without the ribbon part")
    ap.add_argument("--with-ground", action="store_true",
                    help="include the 573,440-triangle collision ground")
    ap.add_argument("--lines", type=int, default=None,
                    help="only the first N solid ribbons")
    a = ap.parse_args(argv)
    schema, profile, sector = DW.drum()
    ok, _tot, _per = run(with_ribbons=not a.without_ribbons,
                         with_ground=a.with_ground, max_lines=a.lines)
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
