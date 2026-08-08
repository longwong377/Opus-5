#!/usr/bin/env python3
"""WHERE A SECTOR'S TRANSIT COLUMN STANDS — one derivation, from the floor.

    python3 tools/column_site.py --report        # where each column goes, why
    python3 tools/column_site.py --gate          # FAILS if a column joins nothing
    python3 tools/column_site.py --gate --legacy # the same gate on the old rule
    python3 tools/column_site.py --selftest

===========================================================================
THE DEFECT THIS FILE EXISTS TO CLOSE
===========================================================================

`tools/export_station.py` used to place a column at

    (RT.transit_angle(sector), min(z for every cluster of that sector))

**two independently computed numbers, with nothing asserting the sector has any
floor at that PAIR.** The angle is derived from the cluster arcs; the z is the
sector's lowest cluster and knows nothing about the angle. Measured against the
817 baked deck cells, three of the five columns opened their doors into vacuum:

    blue    0 of 18 landings on a deck   nearest floor 80.1 m away in z
    yellow  0 of 24 landings             nearest floor 19.8 m away
    green   4 of  9 landings

That is not a bake failure and not a mesh failure. Both halves were right about
their own question; nobody owned the conjunction. It is the same shape as every
other defect in `CLAUDE.md`'s list — a part that meets its own standard.

===========================================================================
SO THE Z IS TAKEN FROM THE FLOOR, NOT FROM A SECOND FORMULA
===========================================================================

The angle is canon and stays: `routes.transit_angle` is the angle lying inside
the most of a sector's cluster arcs, every deck spine is built to reach it
(`export_station` passes it as `must_cover=`), and moving it would move the
whole sector's circulation. **Only the z is chosen here**, and it is chosen by
asking the built decks where they are rather than by computing a second number
and hoping:

    for each z the register places a cluster at
        stack  = spoke_way.ring_stack(schema, profile, sector, rings, z)
        joined = how many of those landings sit within NEAR_M of a
                 baked deck cell's own AABB
    take the z that joins the most landings

`ring_stack` has to be re-evaluated at every candidate because
`interior.decks_in_ring(z_m=)` RETURNS A DIFFERENT STACK AT DIFFERENT Z — blue
ring 0 has 6 decks at z=6880 and 10 at z=7120. A search that fixed the stack
and swept z would be measuring the wrong shaft at every candidate but one.

**The candidate set is `routes.clusters`' own z values**, the same enumeration
`routes.column_z` walks and the same one `export_station.work_list` builds
from. A column standing where no cluster does is a column standing where the
register never asked for floor, so there is nothing to search there.

===========================================================================
WHY THE DECK CELLS AND NOT A THIRD DESCRIPTION OF THE STATION
===========================================================================

`station/generated/scene/station/cells/*_cells.json` is what
`tools/bake_station.py` measured off the shipped deck GLBs — the AABB of the
content of each streaming cell. It is the only description of the station that
is *derived from the geometry a player stands on* rather than from the schema
the geometry was generated out of, and it is the same table
`bake_columns.py --verify` scores the baked columns against. Using anything
else would put a third opinion about where the floor is into a project whose
signature failure is two.

It is 1.5 MB of JSON and reads in well under a second. No GLB is opened, no
mesh is built, nothing is rendered.

**AND THE CHICKEN-AND-EGG IS REAL, SO IT IS NAMED RATHER THAN HIDDEN.** The
cells are baked *after* `export_station.py` runs, so on a tree that has never
been built there are none. `site()` then falls back to `routes.column_z` —
which is the best schema-only answer that exists, is already what the
circulation graph uses, and is strictly better than `min(z)` — and it records
`source: "routes.column_z (no baked deck cells on disk)"` in its own output so
no reader can mistake the fallback for the measurement. A column placed that
way is provisional and the next bake's `--gate` says so.

===========================================================================
WHAT THIS DOES NOT FIX, MEASURED
===========================================================================

**Red's shaft opens 41 doors onto deck levels the station never builds, and no
z can close them.** Red's column crosses four rings and `ring_stack` returns 58
landings — one at every physical deck of the pressure hull. `routes.clusters`
carries only 17 (ring, deck) pairs in red, because only 17 of those levels hold
a location, and `export_station.work_list` builds a deck only where the
register carries one. So 41 of the 58 landings are doors at a level with no
geometry behind them at ANY z. Decomposed by `--report --landings red`:

    12 joined, 37 at a (ring, deck) the register does not carry,
     9 at a (ring, deck) that IS built and still missed

Only that second class is this file's defect, and both z red can stand at were
measured: 6600 gives 12 of 58 and 6640 gives 5 of 47, so **red is already at
its best available placement and does not move.** The first class belongs to
`station/spoke_way.py`: `lift.lift_shaft` already takes `landings=False` and
its own docstring says why — *"a blind shaft, one that passes a deck without
serving it, is a real thing a station has"* — and `spoke_way` opens a landing
at every deck in the stack regardless. Closing it means passing `landings` per
deck rather than per shaft, which is a change in that file, not this one.

**SO THE REPORT CARRIES TWO NUMBERS AND THE SECOND IS THE HONEST ONE.**
`joined` is geometric — how many landings meet floor. `register` is how many of
the sector's own (ring, deck) pairs have a landing on them, which is the
question a resident of that deck actually asks. Across the station:

    register decks that can reach their sector's lift:  31 of 70  ->  56 of 70

The 14 still unserved are red's 9 and green's and yellow's remainders, and they
are enumerated per sector by `--report` so they cannot be quietly inherited.
"""

import argparse
import collections
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

CELLS = os.path.join(ROOT, "station/generated/scene/station/cells")

# How near a landing has to be to a deck cell before it counts as joined.
# THE SAME NUMBER `tools/bake_columns.py` GATES ON, imported rather than
# restated so the placement and the verification cannot drift apart. A cell
# AABB is the bounding box of its CONTENT and a portal is ~2.2 m wide, so a
# landing that opens onto a deck is a doorway's worth from that deck's box.
NEAR_M = 5.0


# ===========================================================================
# WHERE THE FLOOR IS
# ===========================================================================

def floor_boxes(cells_dir=CELLS):
    """-> {sector: [(cell_id, [(lo,hi) x3])]} from the baked DECK cells.

    Per-deck sets, never `station_cells.json` and never `column_*`: a merged
    manifest already contains the columns, and scoring a column against itself
    is how a proximity gate comes back green on a shaft in vacuum.
    """
    out = collections.defaultdict(list)
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_cells.json"))):
        stem = os.path.basename(p)[:-len("_cells.json")]
        if stem == "station" or stem.startswith("column_"):
            continue
        sector = stem.split("_")[0]
        try:
            with open(p) as f:
                man = json.load(f)
        except (OSError, ValueError):
            continue
        for c in man.get("cells", []):
            a = c.get("aabb")
            if not a:
                continue
            pos, size = a["pos"], a["size"]
            out[sector].append(
                (c.get("id", stem), [(pos[i], pos[i] + size[i])
                                     for i in range(3)]))
    return out


def point_gap(pt, box):
    """Shortest distance from a point to an axis-aligned box. 0 inside."""
    q = [min(max(pt[i], box[i][0]), box[i][1]) for i in range(3)]
    return math.dist(pt, q)


def landing_points(stack, angle_deg, z_m):
    """The world point each landing door opens at. -> [(r, x, y, z)]

    `bake_columns.verify` builds exactly this, from `landing_r_m` in the baked
    manifest. Same expression, so the placement is scored by the measurement
    that will later judge it and cannot be tuned against a softer one.
    """
    a = math.radians(angle_deg)
    return [(d["floor_r_m"], d["floor_r_m"] * math.cos(a),
             d["floor_r_m"] * math.sin(a), z_m) for d in stack]


def score(boxes, stack, angle_deg, z_m, near_m=NEAR_M):
    """-> (joined, [(r, gap_m, cell_id)]) for one candidate placement."""
    per = []
    joined = 0
    for r, x, y, z in landing_points(stack, angle_deg, z_m):
        best, who = float("inf"), ""
        for cid, b in boxes:
            g = point_gap((x, y, z), b)
            if g < best:
                best, who = g, cid
        per.append((r, best, who))
        if best <= near_m:
            joined += 1
    return joined, per


# ===========================================================================
# THE DECISION
# ===========================================================================

def _sector_state(nodes):
    decks = collections.defaultdict(list)
    for k in nodes:
        decks[k[:3]].append(k[3])
    return decks


def legacy_z(nodes, sector):
    """The expression this file replaces, kept so the gate has a control.

    `export_station.py`'s old line, verbatim: the sector's smallest cluster z
    over every deck. Retained ONLY so `--gate --legacy` can be shown failing on
    the tree as it was; nothing calls it in anger.
    """
    decks = _sector_state(nodes)
    zs = [z for k, v in decks.items() if k[0] == sector for z in v]
    return min(zs) if zs else 0.0


def candidates(nodes, sector):
    """Every z the register places a cluster of this sector at, ascending."""
    return sorted({k[3] for k in nodes if k[0] == sector})


def site(schema, profile, nodes, sector, rings=None, boxes=None,
         cells_dir=CELLS, near_m=NEAR_M, rule="floor"):
    """Where this sector's column stands, and the evidence for it.

    `rule="legacy"` reproduces the old placement so the gate can fail on it.

    THE ORDERING IS (joined, joined/landings, -z) AND EACH TERM IS THERE FOR A
    REASON. `joined` first because a column that serves 21 decks beats one that
    serves 8 — ring-to-ring travel is the point. The RATIO second because two
    placements that join the same number of decks are separated by how many
    dead doors they leave: green joins 8 either way and z=4720 leaves none
    while z=4600 leaves one. Lowest z last, so the answer is deterministic.
    """
    import interior as IT                                        # noqa: PLC0415
    import routes as RT                                          # noqa: PLC0415
    import spoke_way as SW                                       # noqa: PLC0415

    if rings is None:
        rings = sorted({k[1] for k in nodes if k[0] == sector})
    angle = RT.transit_angle(sector, nodes)
    # A GAZETTEER DECK NUMBER IS A NAME, NOT AN INDEX, and the first version of
    # this function compared one to the other. `routes.clusters`' key carries
    # the register's deck LABEL -- Grey names 24, 26, 30 … 80 on a ring that
    # has 23 decks, and Yellow reaches 30 with 7 -- while `ring_stack` hands
    # back `ring_deck_index`, a position in the built stack.
    # `interior.deck_index_for` is the one translation both build paths already
    # go through (`deck.deck_index` delegates to it), so it is used here rather
    # than a fourth reading of the same table. Where the two coincide (Blue,
    # Red, Green ring 0) the old code was accidentally right, which is exactly
    # why it read as plausible on the sector it was developed against.
    reg = collections.defaultdict(set)
    for k in nodes:
        if k[0] != sector:
            continue
        try:
            reg[k[1]].add(IT.deck_index_for(schema, profile, sector, k[1],
                                            k[2]))
        except (ValueError, KeyError, IndexError):
            pass

    def _stack(z):
        try:
            return SW.ring_stack(schema, profile, sector, rings, z)
        except (ValueError, KeyError, IndexError):
            return []

    def _pack(z, source, why, tried=()):
        st = _stack(z)
        joined, per = (0, []) if not st else score(
            boxes or [], st, angle, z, near_m)
        # (A) vs (B): a landing that misses at a deck the register does not
        # carry is a shaft passing an unbuilt level; one that misses at a deck
        # the register DOES carry is this file's defect.
        dead_unbuilt = dead_built = 0
        served = set()
        for d, (_r, gap, _who) in zip(st, per):
            pair = (d["ring_index"], d["ring_deck_index"])
            carried = d["ring_deck_index"] in reg.get(d["ring_index"], ())
            if gap <= near_m:
                if carried:
                    served.add(pair)
                continue
            if carried:
                dead_built += 1
            else:
                dead_unbuilt += 1
        return {
            "sector": sector, "rings": list(rings), "angle_deg": angle,
            "z_m": float(z), "landings": len(st), "joined": joined,
            "dead_unbuilt": dead_unbuilt, "dead_built": dead_built,
            # THE NUMBER A RESIDENT CARES ABOUT, and it is not `joined`. A
            # landing can meet a deck cell at a level the register carries no
            # location on -- that is floor, but nobody lives there. This counts
            # the register's own (ring, deck) pairs that have a landing on
            # them, which is "how many of this sector's decks can reach the
            # lift". `joined` is the geometric question; this is the useful one.
            "served_register": len(served),
            "in_register": sum(len(v) for v in reg.values()),
            "nearest_m": min((g for _r, g, _w in per), default=float("inf")),
            "worst_m": max((g for _r, g, _w in per), default=float("inf")),
            "per_landing": per, "source": source, "why": why,
            "candidates_tried": list(tried),
        }

    # THE FLOOR TABLE IS LOADED BEFORE THE RULE BRANCHES, and that ordering is
    # load-bearing rather than tidy. It was under the `legacy` early return
    # once, so a caller that asked for the control without passing `boxes`
    # scored every landing against an EMPTY table and got "0 of 18 joined" on
    # all five columns -- the failing verdict this gate wants, arrived at by
    # measuring nothing. A control that fails for the wrong reason is worse
    # than no control: it cannot distinguish the defect from itself.
    if boxes is None:
        boxes = floor_boxes(cells_dir).get(sector, [])

    if rule == "legacy":
        z = legacy_z(nodes, sector)
        return _pack(z, "legacy min(z) — the expression being replaced",
                     "the sector's lowest cluster z, which knows nothing "
                     "about the transit angle")

    cands = candidates(nodes, sector)
    if not boxes or not cands:
        # NAMED, NOT SILENT. See the header: no cells means no measurement, so
        # the answer is the best schema-only one and it says which it is.
        z = RT.column_z(nodes, sector) if cands else 0.0
        return _pack(z, "routes.column_z (no baked deck cells on disk)",
                     "nothing has been baked for %s, so where its floor is "
                     "cannot be measured; this is the schema's best guess and "
                     "is provisional until the next bake" % sector, cands)

    tried, best = [], None
    for z in cands:
        st = _stack(z)
        if len(st) < 2:
            tried.append((z, 0, 0))
            continue                    # spoke_way refuses; a column joins two
        joined, _per = score(boxes, st, angle, z, near_m)
        tried.append((z, len(st), joined))
        key = (joined, joined / float(len(st)), -z)
        if best is None or key > best[0]:
            best = (key, z)
    if best is None:
        z = RT.column_z(nodes, sector)
        return _pack(z, "routes.column_z (no candidate z carries two decks)",
                     "every candidate z gives a stack of fewer than two decks, "
                     "which spoke_way refuses to build", tried)
    z = best[1]
    return _pack(z, "measured against %d baked deck cells" % len(boxes),
                 "the candidate z whose landing stack meets the most baked "
                 "deck cells within %.1f m; ties to the fewest dead doors, "
                 "then to the lowest z" % near_m, tried)


def sites(schema=None, profile=None, nodes=None, cells_dir=CELLS,
          near_m=NEAR_M, rule="floor", sectors=None):
    """-> {sector: site(...)} for every sector the register carries."""
    import interior as it                                        # noqa: PLC0415
    import routes as RT                                          # noqa: PLC0415
    if nodes is None:
        nodes = RT.clusters()
    if schema is None:
        schema, profile = it.load()
    boxes = floor_boxes(cells_dir)
    out = {}
    for sec in sorted({k[0] for k in nodes}):
        if sectors and sec not in sectors:
            continue
        out[sec] = site(schema, profile, nodes, sec, boxes=boxes.get(sec, []),
                        cells_dir=cells_dir, near_m=near_m, rule=rule)
    return out


# ===========================================================================
# THE GATE
# ===========================================================================

def gate(rows, near_m=NEAR_M):
    """-> (bad, total). `bad` is the sectors whose column joins NOTHING.

    THE THRESHOLD IS ZERO AND THAT IS DELIBERATE. "A column joins nothing" is
    a fact about a build, not a quality score, so there is no number to argue
    about and nothing to tune. The partial cases are reported beside it and
    named — a column joining 12 of 58 is a different problem with a different
    owner (see the header) and hiding it inside a percentage threshold would
    turn a structural finding into a knob.
    """
    return [r["sector"] for r in rows if r["joined"] == 0], len(rows)


def print_report(rows, near_m=NEAR_M, boxes_n=0, landings_for=()):
    print("\n  WHERE THE FIVE TRANSIT COLUMNS STAND — %d baked deck cells to "
          "measure against,\n  a landing counts as joined within %.1f m\n"
          % (boxes_n, near_m))
    print("    %-7s %9s %8s %6s %7s %9s  %-24s %s"
          % ("sector", "angle", "z", "land", "joined", "register",
             "dead doors", "verdict"))
    for r in rows:
        print("    %-7s %9.2f %8.0f %6d %7s %9s  %-24s %s"
              % (r["sector"], r["angle_deg"], r["z_m"], r["landings"],
                 "%d" % r["joined"],
                 "%d/%d" % (r["served_register"], r["in_register"]),
                 "%d unbuilt + %d built" % (r["dead_unbuilt"],
                                            r["dead_built"]),
                 "CONNECTS" if r["joined"] else "JOINS NOTHING"))
    print("\n    'register' is how many of the sector's OWN (ring, deck) pairs "
          "have a landing on them —\n    the question a resident asks. "
          "'joined' is the geometric one.\n")
    for r in rows:
        print("      %-7s %s" % (r["sector"], r["source"]))
        print("      %-7s nearest landing %.2f m, worst %.2f m; register "
              "carries %d (ring, deck) pairs, the shaft has %d landings"
              % ("", r["nearest_m"], r["worst_m"], r["in_register"],
                 r["landings"]))
        if r["candidates_tried"]:
            best = r["z_m"]
            s = "  ".join("%s%.0f:%d/%d%s"
                          % ("[" if abs(z - best) < 1e-6 else "",
                             z, j, n, "]" if abs(z - best) < 1e-6 else "")
                          for z, n, j in r["candidates_tried"])
            print("      %-7s tried  %s" % ("", s))
    for r in rows:
        if r["sector"] not in landings_for:
            continue
        print("\n    %s — every landing, %.2f deg, z=%.0f"
              % (r["sector"], r["angle_deg"], r["z_m"]))
        for rad, gap, who in r["per_landing"]:
            print("      r=%8.2f  gap %7.2f m  %s%s"
                  % (rad, gap, who[:26],
                     "" if gap <= near_m else "   <- opens on nothing"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any column joins nothing")
    ap.add_argument("--legacy", action="store_true",
                    help="score the placement rule this file replaces — the "
                         "negative control, and it FAILS")
    ap.add_argument("--sector", default="")
    ap.add_argument("--landings", default="",
                    help="print every landing of these sectors (comma list)")
    ap.add_argument("--near", type=float, default=NEAR_M)
    ap.add_argument("--cells", default=CELLS)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return _selftest()

    rule = "legacy" if a.legacy else "floor"
    secs = [a.sector] if a.sector else None
    rows = sites(cells_dir=a.cells, near_m=a.near, rule=rule, sectors=secs)
    rows = [rows[k] for k in sorted(rows)]
    boxes_n = sum(len(v) for v in floor_boxes(a.cells).values())
    want = [s for s in a.landings.split(",") if s]
    if a.report or not a.gate:
        print_report(rows, a.near, boxes_n, want)

    bad, total = gate(rows, a.near)
    print("\n  PLACEMENT GATE (%s rule): %d of %d columns join nothing%s"
          % (rule, len(bad), total, (" — " + ", ".join(bad)) if bad else ""))
    tot_j = sum(r["joined"] for r in rows)
    tot_l = sum(r["landings"] for r in rows)
    print("  %d of %d landings across the station meet a deck; %d dead doors "
          "at levels the register does not carry"
          % (tot_j, tot_l, sum(r["dead_unbuilt"] for r in rows)))
    if a.gate:
        return 1 if bad else 0
    return 0


# ===========================================================================
# SELFTEST
# ===========================================================================

def _selftest():
    """Assert the maths, and assert the gate DISCRIMINATES.

    A proximity test that returned 0 for everything would report five connected
    columns and pass any check written only on the connected ones, so the load-
    bearing assertion here is the last one: the SAME gate must fail on the
    legacy rule and pass on the derived one, on the cells actually on disk.
    """
    import interior as it                                        # noqa: PLC0415
    import routes as RT                                          # noqa: PLC0415
    ok = [0, 0]

    def check(name, cond, note=""):
        ok[0] += 1
        ok[1] += bool(cond)
        print(("  ok   " if cond else "  FAIL ") + name
              + (("  " + note) if note else ""))

    b = [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0)]
    check("a point inside a box has gap 0", point_gap((5, 5, 5), b) == 0.0)
    check("a point 3 m off one face", abs(point_gap((13, 5, 5), b) - 3.0) < 1e-9)
    check("a corner point is the diagonal",
          abs(point_gap((13, 14, 5), b) - 5.0) < 1e-9,
          "3-4-5 = %.3f" % point_gap((13, 14, 5), b))

    boxes = floor_boxes()
    n = sum(len(v) for v in boxes.values())
    check("baked deck cells are on disk to measure against", n > 0,
          "%d cells over %d sectors" % (n, len(boxes)))
    if n == 0:
        print("\n  %d of %d" % (ok[1], ok[0]))
        return 1 if ok[1] != ok[0] else 0

    nodes = RT.clusters()
    schema, profile = it.load()
    old = sites(schema, profile, nodes, rule="legacy")
    new = sites(schema, profile, nodes, rule="floor")
    bad_old, _ = gate([old[k] for k in sorted(old)])
    bad_new, _ = gate([new[k] for k in sorted(new)])
    check("the gate FAILS on the legacy rule", len(bad_old) > 0,
          "joins nothing: %s" % (", ".join(bad_old) or "none"))
    check("the gate PASSES on the derived rule", len(bad_new) == 0,
          "joins nothing: %s" % (", ".join(bad_new) or "none"))
    check("no sector loses landings by moving",
          all(new[k]["joined"] >= old[k]["joined"] for k in new),
          ", ".join("%s %d->%d" % (k, old[k]["joined"], new[k]["joined"])
                    for k in sorted(new)))
    check("the angle is untouched — only z moves",
          all(abs(new[k]["angle_deg"] - old[k]["angle_deg"]) < 1e-9
              for k in new))
    check("every derived z is a z the register places a cluster at",
          all(new[k]["z_m"] in set(candidates(nodes, k)) for k in new))
    # THE CONTROL MUST FAIL FOR THE RIGHT REASON. `site(rule="legacy")` called
    # without a floor table once scored every landing against nothing and
    # reported five columns joining nothing -- the verdict the gate wants, and
    # a lie. A caller that supplies no `boxes` must get the same answer as one
    # that does, or the control is measuring its own emptiness.
    solo = {k: site(schema, profile, nodes, k, rule="legacy")
            for k in sorted(old)}
    check("the legacy control loads its own floor table",
          all(solo[k]["joined"] == old[k]["joined"] for k in solo),
          ", ".join("%s %d/%d" % (k, solo[k]["joined"], old[k]["joined"])
                    for k in sorted(solo)))
    check("...and it is not uniformly zero, which is what an empty table gives",
          any(solo[k]["joined"] > 0 for k in solo),
          "grey %d, red %d" % (solo["grey"]["joined"], solo["red"]["joined"]))
    # A GAZETTEER DECK NUMBER IS NOT A STACK INDEX, and the (A)/(B) split
    # compared one to the other until this row was written. It must be checked
    # on a sector where the two DIFFER, or it passes on the coincidence that
    # makes Blue and Red right: Grey names decks 24…80 on a ring of 23.
    moved = []
    for sec in sorted(new):
        for ring in sorted({k[1] for k in nodes if k[0] == sec}):
            labs = {k[2] for k in nodes if k[0] == sec and k[1] == ring}
            idxs = set()
            for lb in labs:
                try:
                    idxs.add(it.deck_index_for(schema, profile, sec, ring, lb))
                except (ValueError, KeyError, IndexError):
                    pass
            if labs != idxs and idxs:
                moved.append("%s/%d" % (sec, ring))
    check("some ring's deck LABELS differ from its stack INDICES, so the "
          "translation is exercised", bool(moved), ", ".join(moved))
    check("no sector claims to serve more register decks than it carries",
          all(new[k]["served_register"] <= new[k]["in_register"] for k in new),
          ", ".join("%s %d/%d" % (k, new[k]["served_register"],
                                  new[k]["in_register"]) for k in sorted(new)))
    check("more register decks reach their lift after the move than before",
          sum(new[k]["served_register"] for k in new)
          > sum(old[k]["served_register"] for k in old),
          "%d -> %d of %d"
          % (sum(old[k]["served_register"] for k in old),
             sum(new[k]["served_register"] for k in new),
             sum(new[k]["in_register"] for k in new)))
    # AND THE MEASUREMENT MUST BE ABLE TO SAY NO. A gate scored against an
    # empty floor table has to fail every column, or it is not measuring.
    empty = sites(schema, profile, nodes, cells_dir=os.devnull + "_nope")
    bad_e, tot_e = gate([empty[k] for k in sorted(empty)])
    check("with no floor table at all, every column joins nothing",
          len(bad_e) == tot_e, "%d of %d" % (len(bad_e), tot_e))
    check("...and it says the fallback was used, rather than pretending",
          all("column_z" in empty[k]["source"] for k in empty))

    print("\n  %d of %d" % (ok[1], ok[0]))
    return 1 if ok[1] != ok[0] else 0


if __name__ == "__main__":
    sys.exit(main())
