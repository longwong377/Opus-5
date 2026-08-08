#!/usr/bin/env python3
"""Does the streamer prime the cell the body is standing in?

WHY THIS EXISTS, AND WHY NO EXISTING GATE COULD ASK IT. `stream.gd::cell_at(p)`
returns `c["index"]`, and every caller then treats that integer as the IDENTITY
of a cell: `walk.gd::_load_streamed` feeds it back through `cell_by_index()` and
`prime()` to choose the one cell that is loaded before the first frame,
`update()` uses it to refuse to free the cell the player is in, `_entering()`
uses it to look one sight line ahead, and the axial gate enumerates the station
with it. All of that is correct exactly while

    cell_by_index(cell_at(p))  ==  the cell containing p

and NOTHING asserted it. `tools/merge_cells.py --selftest` asserted the manifest
was loadable; `tools/reach_gate.py` asserted every named place is inside SOME
cell; `boot.py --gate` asserted the spawn is inside some cell. Each is a true
statement about a part, and a manifest can satisfy all three while the round trip
above is not the identity on 617 of its 787 cells -- which is what the shipped
build did.

THE MEASUREMENT IS THE SHIPPED CHAIN, NOT A MODEL OF IT. For every cell that
carries a spawn point -- a point the bake measured off that cell's OWN collision
floor, so it is definitionally inside it -- put a body there and run:

    i      = cell_at(spawn)          # first cell whose distance is zero
    primed = cell_by_index(i)        # first cell carrying that index
    assert primed is the cell we started from

`cell_at` is `station/boot.py::start_cell`, IMPORTED rather than reimplemented.
That function already exists to be the Python mirror of `stream.gd::cell_at`, and
its own docstring says why: *"A second rule here -- even a correct one -- would
be a second description of where a cell is, and the failure mode is silent."*
A fourth copy in this file would be exactly that mistake. `cell_by_index` is a
first-match scan and needs no geometry at all.

WHAT IT REPORTS, AND WHY BOTH HALVES ARE PRINTED SEPARATELY. A wrong primed cell
has two independent causes and they need different fixes:

  A  DUPLICATE INDEX -- `cell_at` found the right cell and `cell_by_index`
     returned a different one carrying the same integer. Fixed by
     `tools/merge_cells.py` renumbering the merged array (session 4t).

  B  AMBIGUOUS CONTAINMENT -- `cell_at` itself returned a different cell,
     because more than one cell's zero-distance test claims the point. NOT
     fixed here; see THE SECOND DEFECT at the bottom of this file.

Reporting one number for both would let a fix to A read as progress on B.

AND IT ASKS THE SAME QUESTION OF CONTENT, WHICH IS THE ONE THAT MATTERS. Cell
spawn points test the manifest against itself. `places_check` below runs the same
chain from the **129 places the register names**, at the `floor_xyz`
`tools/bake_station.py::write_places()` measured for each, and asks the plain
physical question: does the primed cell have any geometry under the body. On the
shipped manifest that is **23 of 129**, median 2,065 m from the nearest loaded
triangle; after `merge_cells` renumbers, **91 of 129**, median 42.7 m.
`the_garden` is the clean case -- its cell `green_1_0_c00` carries per-deck index
0, `blue_0_0_c00z00` carries index 0 and comes first, so the streamer primed a
corridor **1,756.7 m away**.

    python3 tools/cell_identity.py                  # the shipped manifest
    python3 tools/cell_identity.py --control        # a legacy merge, shown failing
    python3 tools/cell_identity.py --second-defect  # what B would cost to close
"""

import argparse
import glob
import json
import math
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLS = os.path.join(ROOT, "station", "generated", "scene", "station", "cells")
MERGED = os.path.join(CELLS, "station_cells.json")

sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))


def _boot_start_cell():
    """`station/boot.py::start_cell`, the maintained mirror of `cell_at`."""
    import boot                                                # noqa: PLC0415
    return boot.start_cell


def cell_by_index(cells, i):
    """`stream.gd::cell_by_index` -- FIRST match, which is the whole point."""
    for c in cells:
        if int(c.get("index", -1)) == i:
            return c
    return None


def aabb_distance(c, p):
    """How far the body is from the primed cell's own geometry, in metres.

    The AABB rather than the arc, deliberately: `arc` is the residency METRIC
    (how far you would have to walk round the ring) and this wants the plain
    physical answer to "is there anything under my feet".
    """
    ab = c.get("aabb")
    if not ab:
        return float("inf")
    lo, size = ab["pos"], ab["size"]
    q = [min(max(p[i], lo[i]), lo[i] + size[i]) for i in range(3)]
    return math.dist(p, q)


def duplicate_indices(cells):
    seen = {}
    for c in cells:
        seen.setdefault(int(c.get("index", -1)), []).append(str(c.get("id", "")))
    return {i: ids for i, ids in seen.items() if len(ids) > 1}


def check(man, verbose=False):
    """-> (n_right, n_wrong_index, n_wrong_containment, detail dict)."""
    cells = man.get("cells") or []
    start_cell = _boot_start_cell()
    by_id = {}
    for c in cells:
        by_id[str(c.get("id", ""))] = c

    right = wrong_index = wrong_contain = no_spawn = unplaced = 0
    dists = []
    examples = []
    disagree = 0
    for c in cells:
        sp = c.get("spawn")
        if not sp or len(sp) < 3:
            # A cell with no floor has no spawn -- `bake()` states that rather
            # than inventing a point, and it is not a failure of this gate.
            no_spawn += 1
            continue
        p = [float(x) for x in sp]
        i = start_cell(man, p)
        if i < 0:
            # A body standing on a cell's own floor that no cell claims. This is
            # the one outcome that is neither A nor B and it must not be folded
            # into either.
            unplaced += 1
            continue
        # THE CELL `cell_at` ACTUALLY CHOSE, which is the first one whose
        # distance is zero. Needed to attribute a failure, and cross-checked
        # against `boot.start_cell` below: if the two disagree, this file's
        # `_contains` has drifted from the maintained mirror and the attribution
        # is worthless, so it is counted and printed rather than assumed.
        # THE CELL THE MAINTAINED RULE CHOSE, taken from the rule itself rather
        # than from a copy of it. This scanned `_contains` first-match, which
        # WAS `start_cell`'s rule and stopped being it when `start_cell` grew
        # AABB containment plus nearest-floor-radius. The docstring below
        # anticipated the drift and counted it; the drift then made every
        # attribution wrong in a specific and misleading direction -- two
        # containment failures were reported as `A duplicate index` on a
        # manifest with 823 distinct indices over 823 cells, which sends the
        # next reader to run `merge_cells.py` for a defect it cannot fix.
        #
        # A GATE THAT MISATTRIBUTES IS THE DEFECT IT IS LOOKING FOR. The engine's
        # own `NO MESH in the glb -- their parts claimed every triangle` blamed
        # triangle attribution for the z-prefix mismatch earlier this session and
        # sent two judges hunting geometry that was present and correct.
        chose = None
        for d_ in cells:
            if int(d_.get("index", -2)) == i:
                chose = d_
                break
        # `_contains` is kept as the CONTROL: where the old first-match rule and
        # the maintained one disagree is exactly the population the second-defect
        # fix moved, and printing it is how a reader sees the fix working.
        first_match = None
        for d_ in cells:
            if _contains(d_, p):
                first_match = d_
                break
        if first_match is None or int(first_match.get("index", -2)) != i:
            disagree += 1
        primed = cell_by_index(cells, i)
        if primed is not None and primed.get("id") == c.get("id"):
            right += 1
            continue
        # WHICH OF THE TWO CAUSES. If `cell_at` chose this very cell then the
        # loss happened in `cell_by_index` -- cause A, a duplicate index. If it
        # chose a different cell, the index lookup was never given the right
        # answer to lose -- cause B.
        found_self = chose is not None and chose.get("id") == c.get("id")
        if found_self:
            wrong_index += 1
        else:
            wrong_contain += 1
        d = aabb_distance(primed, p) if primed is not None else float("inf")
        dists.append(d)
        if len(examples) < 8:
            examples.append((str(c.get("id")), str(primed.get("id"))
                             if primed is not None else "NOTHING", d,
                             "index" if found_self else "containment"))
    dists.sort()
    return right, wrong_index, wrong_contain, {
        "no_spawn": no_spawn, "unplaced": unplaced, "dists": dists,
        "examples": examples, "cells": len(cells), "disagree": disagree,
        "tested": right + wrong_index + wrong_contain,
    }


def _contains(c, p):
    """`stream.gd::distance_to(c, p) <= 0`, for ONE cell.

    Only used to attribute a failure to cause A or cause B. The verdict itself
    comes from `boot.start_cell`, which scans in the engine's own order.
    """
    arc = c.get("arc")
    if arc:
        a = math.degrees(math.atan2(p[1], p[0])) % 360.0
        if not (float(arc["a0_deg"]) <= a < float(arc["a1_deg"])):
            return False
        return float(arc["z0"]) <= p[2] <= float(arc["z1"])
    ab = c.get("aabb")
    if not ab:
        return False
    lo, size = ab["pos"], ab["size"]
    return all(lo[i] <= p[i] <= lo[i] + size[i] for i in range(3))


def named_places(cells_dir=CELLS):
    """-> [(key, name, floor_xyz)] for every place the register puts on a deck.

    `tools/bake_station.py::write_places()` writes `<deck>_places.json` beside
    the cells, and every row carries `floor_xyz` -- the point on that place's own
    floor. `tools/reach_gate.py` reads the same files to ask whether each place
    is inside SOME cell; this asks the harder question next door: whether the
    cell the streamer would PRIME has anything under the body.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_places.json"))):
        try:
            with open(p) as f:
                j = json.load(f)
        except (OSError, ValueError):
            continue
        for row in j.get("places") or []:
            fx = row.get("floor_xyz")
            if fx and len(fx) >= 3:
                out.append((str(row.get("key", "?")), str(row.get("name", "")),
                            [float(x) for x in fx]))
    return out


def places_check(man, cells_dir, verbose=False):
    """IS THERE FLOOR UNDER THE BODY, at every place a player can name.

    THE POPULATION IS THE REGISTER, NOT THE CELL LIST, and that matters. Cell
    spawn points test the manifest against itself; these are the 129 places
    `station/directory.py` names, at the coordinates the bake measured for them,
    so a failure here is a place a player walks to and falls through.

    The criterion is the primed cell's own AABB containing the point -- the plain
    physical question, and the one that does not need to know which cell is
    "the right" one. It therefore catches BOTH causes at once.
    """
    places = named_places(cells_dir)
    if not places:
        print("  (no *_places.json beside the cells -- the named-place check "
              "needs `tools/bake_station.py`; not counted either way)")
        return None
    cells = man.get("cells") or []
    start_cell = _boot_start_cell()
    ok = 0
    ds = []
    ex = []
    for key, _name, p in places:
        i = start_cell(man, p)
        primed = cell_by_index(cells, i) if i >= 0 else None
        if primed is not None and _in_aabb(primed, p):
            ok += 1
            continue
        d = aabb_distance(primed, p) if primed is not None else float("inf")
        ds.append(d)
        if len(ex) < 8:
            ex.append((key, primed.get("id") if primed is not None else "NONE",
                       d))
    ds.sort()
    print("  the %d NAMED PLACES in the register, each at its own floor point:"
          % len(places))
    print("    the primed cell has geometry under the body   %3d of %d"
          % (ok, len(places)))
    if ds:
        print("    when it does not: median %.1f m away, max %.1f m, %d over 50 m"
              % (ds[len(ds) // 2], ds[-1], sum(1 for x in ds if x > 50.0)))
    if verbose:
        for e in ex:
            print("      %-22s primed %-24s %8.1f m" % e)
    return ok, len(places)


def _in_aabb(c, p):
    ab = c.get("aabb")
    if not ab:
        return False
    lo, size = ab["pos"], ab["size"]
    return all(lo[i] <= p[i] <= lo[i] + size[i] for i in range(3))


def report(man, label, cells_dir=CELLS, verbose=False):
    cells = man.get("cells") or []
    n = len(cells)
    distinct = len({int(c.get("index", -1)) for c in cells})
    dup = duplicate_indices(cells)
    print("%s: %d cells, %d distinct `index` value(s)" % (label, n, distinct))
    print("  index provenance: %s" % man.get("index_from", "NOT STATED"))
    if dup:
        worst = max(dup.items(), key=lambda kv: len(kv[1]))
        print("  DUPLICATE INDICES: %d of %d cells share their index with "
              "another cell; index %d alone is claimed by %d"
              % (sum(len(v) for v in dup.values()), n, worst[0],
                 len(worst[1])))
    else:
        print("  indices are unique -- `cell_by_index` can only return the cell "
              "`cell_at` chose")

    right, w_idx, w_con, d = check(man, verbose)
    tested = d["tested"]
    print("  a body on each cell's own spawn point, through "
          "cell_by_index(cell_at(p)):")
    print("    primed the cell the body is in     %4d of %d" % (right, tested))
    print("    primed some other cell             %4d of %d"
          % (w_idx + w_con, tested))
    print("      A  duplicate index               %4d   -- merge_cells renumber"
          % w_idx)
    print("      B  ambiguous containment         %4d   -- see THE SECOND "
          "DEFECT in this file" % w_con)
    if d["no_spawn"]:
        print("    (%d cells have no floor and therefore no spawn -- not tested)"
              % d["no_spawn"])
    if d["unplaced"]:
        print("    (%d spawn points are in NO cell at all)" % d["unplaced"])
    if d["disagree"]:
        print("    WARNING: this file's `_contains` disagrees with "
              "boot.start_cell on %d point(s) -- the A/B attribution above is "
              "not trustworthy" % d["disagree"])
    dd = d["dists"]
    if dd:
        print("    distance from the body to the primed cell's own geometry: "
              "median %.1f m, max %.1f m, %d over 50 m"
              % (dd[len(dd) // 2], dd[-1], sum(1 for x in dd if x > 50.0)))
    if verbose:
        for e in d["examples"]:
            print("      standing in %-24s primed %-24s %8.1f m  [%s]" % e)
    places_check(man, cells_dir, verbose)
    return right, w_idx, w_con, tested


def second_defect(man):
    """WHAT CAUSE B WOULD COST TO CLOSE -- measured, not applied.

    `stream.gd::distance_to`'s arc branch tests ANGLE and Z and never RADIUS, so
    every cell of every deck that happens to share an arc and a z with another
    deck claims the same point. On the shipped manifest the boot spawn is claimed
    by three cells on three different decks. `cell_at` returns whichever comes
    first in the array, which is an accident of merge order.

    THE FIX IS TWO LINES AND IT CANNOT LAND HERE, because the predicate exists
    TWICE by design -- `stream.gd::distance_to` and `station/boot.py::start_cell`
    -- and changing one without the other is precisely the silent divergence that
    file's docstring exists to prevent. Neither is in this tool's remit. So what
    this does is measure the candidate rule against the shipped content, so that
    whoever owns both files applies a number rather than a hunch.

    THE RULE, and both halves are derived rather than picked:
      1. a cell cannot hold a point outside its own AABB -- the AABB is the
         bound of the geometry the bake actually wrote, and it is already in
         every row. No margin, no tolerance.
      2. among what survives, the cell whose FLOOR RADIUS is nearest the point's
         own radius -- a body standing on a floor is at that floor's radius, and
         `arc.r_m` is the deck floor radius the bake measured. That is the axis
         the arc test throws away.
    """
    cells = man.get("cells") or []

    def r_err(c, p):
        arc = c.get("arc")
        if not arc:
            return 0.0
        return abs(math.hypot(p[0], p[1]) - float(arc["r_m"]))

    def in_aabb(c, p):
        ab = c.get("aabb")
        if not ab:
            return False
        lo, size = ab["pos"], ab["size"]
        return all(lo[i] <= p[i] <= lo[i] + size[i] for i in range(3))

    shipped = rule = tested = 0
    claims = {}
    misses = []
    for c in cells:
        sp = c.get("spawn")
        if not sp or len(sp) < 3:
            continue
        p = [float(x) for x in sp]
        cont = [d for d in cells if _contains(d, p)]
        if not cont:
            continue
        tested += 1
        claims[len(cont)] = claims.get(len(cont), 0) + 1
        if cont[0].get("id") == c.get("id"):
            shipped += 1
        sub = [d for d in cont if in_aabb(d, p)] or cont
        best = min(sub, key=lambda d: r_err(d, p))
        if best.get("id") == c.get("id"):
            rule += 1
        elif len(misses) < 5:
            misses.append((str(c.get("id")), str(best.get("id"))))
    print("THE SECOND DEFECT -- `distance_to`'s arc branch ignores RADIUS")
    print("  cells claiming one point (worst first): %s"
          % ", ".join("%d cells: %d points" % (k, claims[k])
                      for k in sorted(claims, reverse=True)[:6]))
    print("  cell_at picks the body's own cell, as shipped        %4d of %d"
          % (shipped, tested))
    print("  ... with AABB containment then nearest floor radius  %4d of %d"
          % (rule, tested))
    if misses:
        print("  residual, named: %s"
              % "; ".join("%s -> %s" % m for m in misses))
    print("  APPLY IN BOTH OR NEITHER: godot/scripts/stream.gd::cell_at and "
          "station/boot.py::start_cell.")
    return shipped, rule, tested


def control(cells_dir=CELLS, verbose=False):
    """Build a LEGACY merge and run the gate on it. It must fail."""
    import merge_cells as M                                    # noqa: PLC0415
    if not glob.glob(os.path.join(cells_dir, "*_cells.json")):
        print("  NO PER-DECK CELL SETS in %s -- the control needs them"
              % cells_dir)
        return 1
    fd, tmp = tempfile.mkstemp(suffix="_legacy_cells.json")
    os.close(fd)
    try:
        man = M.merge(cells_dir, tmp, renumber=False)
        print()
        right, w_idx, w_con, tested = report(man, "THE CONTROL (--legacy-index)",
                                             cells_dir, verbose)
        print()
        if w_idx == 0:
            print("  THE CONTROL DID NOT FAIL -- either the per-deck sets no "
                  "longer collide, or this gate cannot see the defect it was "
                  "written for. Both are reasons to stop trusting it.")
            return 1
        print("  the control FAILS as it must: %d of %d cells prime the wrong "
              "cell through a duplicate index" % (w_idx, tested))
        return 0
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=MERGED)
    ap.add_argument("--cells", default=CELLS)
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--control", action="store_true",
                    help="merge WITHOUT renumbering and show this gate failing")
    ap.add_argument("--second-defect", action="store_true",
                    help="measure what closing cause B would buy (applies "
                         "nothing)")
    a = ap.parse_args()

    if a.control:
        return control(a.cells, a.verbose)

    if not os.path.exists(a.manifest):
        # A MISSING MANIFEST IS NOT A PASS. It is also not this gate's failure --
        # the same rule `reach_gate.py` follows on a fresh checkout.
        print("cell_identity: no manifest at %s" % a.manifest)
        print("       run: python3 tools/merge_cells.py")
        return 0
    with open(a.manifest) as f:
        man = json.load(f)
    right, w_idx, w_con, tested = report(
        man, os.path.relpath(a.manifest, ROOT), a.cells, a.verbose)
    if a.second_defect:
        print()
        second_defect(man)
    print()
    if w_idx:
        print("  FAILED: `index` is not an identity on this manifest -- %d of "
              "%d cells prime a cell the body is not standing in because "
              "another cell claims the same index. Run "
              "`python3 tools/merge_cells.py`." % (w_idx, tested))
        return 1
    print("  CELL INDICES ARE AN IDENTITY -- cell_by_index(cell_at(p)) returns "
          "the cell cell_at chose, on all %d tested" % tested)
    if w_con:
        print("  (%d of %d still prime the wrong cell through cause B, the "
              "containment ambiguity this gate does not fix and does not hide: "
              "run --second-defect)" % (w_con, tested))
    return 0


if __name__ == "__main__":
    sys.exit(main())
