#!/usr/bin/env python3
"""Merge 70 per-deck cell sets into ONE manifest, so the whole station streams.

WHY. `boot.json` names a single deck's cell set and `main.gd` hands that one
path to `stream.gd::configure`, so the shipped game loads ONE deck of seventy.
All 70 are in the package -- 2,815 MB of mesh, 816 cells, 129 rooms, 6,021
people -- and 113 of the register's 129 places are unreachable data. That is
"built but unreachable" at station scale.

AND IT NEEDS NO NEW ENGINE CODE, WHICH IS THE WHOLE POINT OF DOING IT THIS WAY.
Three facts make the merge sufficient:

  1. EVERY DECK IS ALREADY IN ONE WORLD FRAME. A cell's `aabb.pos` and `arc`
     are absolute station coordinates, not deck-local: blue_0_0 sits at
     r=211.55 m, red_0_0 at r=268.05, grey_0_0 at r=471.25, each with its own
     z. Nothing has to be transformed; they simply coexist.
  2. `configure()` READS A FLAT LIST. It takes `j["cells"]`, resolves each
     cell's `mesh`/`collision` RELATIVE TO THE MANIFEST'S OWN DIRECTORY, and
     every one of the 70 sets already writes its `.scn` files into that same
     `cells/` directory. So concatenation is the entire transform.
  3. THE STREAMER NEVER ASKS WHICH DECK A CELL BELONGS TO. It loads by distance
     from the player and frees by distance. `plan["corridor"]`, `floor_r_m` and
     `z_cluster_m` are read only by `_ax_setup`/`_ax_pick_target`, which are the
     AXIAL GATE, not the runtime.

THE ONE REAL DECISION IS RESIDENCY, AND IT IS STATED RATHER THAN DEFAULTED.
`configure()` sets ONE global load radius, and the 70 sets carry 70 DIFFERENT
residency blocks because each deck derives its cell length from its own
circumference -- 73.8 m on blue_0_0, 72.6, 71.3 and so on. A merged manifest
must choose.

It takes the MAXIMUM radius and free distance across the decks. The reason is
asymmetric cost: a radius smaller than some deck's cell length means a player
walking that deck can stand where the next cell has not been asked for yet --
no floor, a fall through the world. A radius larger than needed on a
fine-grained deck costs resident triangles, which `stream.gd`'s stated policy
already handles by printing rather than popping a cell. **Missing ground is a
bug; extra triangles are a budget number.**

That budget is already RED and this makes it redder -- `boot.py --axial-gate`
measured peak resident 359,584 tri against a 180,000 budget on blue_0_0 alone.
It is recorded here rather than hidden: see `--report`, which prints the worst
case the merged manifest can produce.

===========================================================================
AND `index` IS AN IDENTITY, SO CONCATENATING SEVENTY-SIX OF THEM BROKE IT
===========================================================================

THE DOCSTRING ABOVE ASSERTED IDS AND FORGOT INDICES, and the loop below says so
in its own comment: *"IDS MUST STAY UNIQUE ACROSS THE MERGE ... a collision
would make `stream.gd` free the wrong cell, which is a hole in the floor rather
than a wrong number."* That is exactly right about `id`, and it is word for word
the argument for `index`, which nothing ever checked. Measured on the shipped
manifest before this change: **823 cells carrying 190 distinct `index` values**,
index 7 alone shared by 33 cells, 712 of the 823 sitting on a number somebody
else also claims.

The cause is structural rather than careless. `stream.gd::bake()` computes
`cix = arc * n_band + band` PER DECK and is right to -- its own comment says
*"`index` is only an engine-local handle (`prime`, `cell_by_index`) and has to be
unique and small, so it is compacted"*. Seventy-six decks each numbering from
zero, concatenated without renumbering, is seventy-six overlapping handle spaces
in one array, and "unique" was a property of the input this merge quietly spent.

AND IT IS AN IDENTITY, WHICH IS WHY IT IS NOT COSMETIC. `stream.gd::cell_at(p)`
RETURNS `c["index"]`, and `walk.gd::_load_streamed` feeds that straight back
through `cell_by_index()` and `prime()`. Both are FIRST-MATCH scans over the same
array, so with duplicates the round trip is not the identity: `cell_at` finds the
cell the body is standing in, hands back an integer, and `cell_by_index` returns
the FIRST cell carrying that integer -- a different cell, usually on a different
deck. `prime()` then loads THAT one, synchronously, as the level's load screen,
and the body is left standing over geometry nobody asked for.

MEASURED by putting a body at each cell's own recorded spawn point and running
that exact chain -- `tools/cell_identity.py`, on the shipped manifest:

    the primed cell is the cell the body is in       170 of 787
    the primed cell is somewhere else                617 of 787
      median distance to the primed cell's geometry     2,724.8 m
      further than 50 m from anything that loaded              574

Of those 617, **248 are this defect alone** -- `cell_at` found the right cell and
`cell_by_index` handed back a different one. The other 369 are a SECOND defect
that renumbering does not touch and this file cannot reach; it is named and
measured at the bottom of `tools/cell_identity.py`. Renumbering here takes the
round trip from **170 to 418 of 787**, and the residual is stated rather than
rounded away.

AND THE SAME MEASUREMENT OVER CONTENT, WHICH IS THE ONE THAT MATTERS. Put a body
at each of the register's **129 named places**, at the `floor_xyz` the bake
recorded for it, and ask whether the cell the streamer primes has any geometry
under that body:

                                        as shipped   renumbered
    floor under the body                 23 of 129    91 of 129
    when not, distance to the primed     2,065.1 m      42.7 m   (median)
    ... worst                            7,231.5 m     166.5 m

THE GARDEN IS THE CLEANEST SINGLE CASE and it is the one the 4t panel traced.
`the_garden` sits in `green_1_0_c00`, whose per-deck index is **0**;
`blue_0_0_c00z00` is also index 0 and comes first in the merged array, so
`prime()` loaded a corridor cell **1,756.7 m away** and the body stood over
nothing. `zen_garden` and `drum_tram` share that same index 0 and the same wrong
cell; `garden_terrace` got `blue_0_2_c08z11`, 2,733.5 m away.

AND THE REASON IT SURVIVED IS WORTH MORE THAN THE FIX: **the one deck the boot
manifest names is the one deck the defect cannot touch.** `per_deck()` globs
`sorted()`, so `blue_0_0` is first, so `cell_by_index` always resolves to a
`blue_0_0` cell when `blue_0_0` claims that index -- and `boot.json`'s spawn is
on `blue_0_0`. Every launch-and-look check anyone ran started on the only deck
that works. A defect that is invisible from the spawn point is invisible from
every test that starts at the spawn point.

THE FIX IS TO NUMBER THE MERGED ARRAY, NOT TO KEEP SEVENTY-SIX NUMBERINGS.
A merged cell's `index` is its position in the merged list: unique by
construction, still "small" in the sense `bake()` wanted, and derived from the
array the engine actually scans rather than from the deck it used to live on. The
deck-local handle is kept as `index_in_deck` beside `deck`, so nothing is lost
and a merged row can still be lined up against the per-deck manifest it came
from.

WHAT WAS CHECKED BEFORE RENUMBERING, because an index anything persists or
cross-references would break silently and this project has paid for that twice:

  * `stream.gd` -- `cell_by_index`, `cell_at`, `prime`, the free guard in
    `update()` and `_entering`. Every one consumes the index WITHIN the one
    manifest it loaded. Nothing stores one anywhere.
  * `walk.gd` -- `_start_cell`, `_cell_index`, `_nearest_cell`, and the axial
    gate's `_g_idx`. All within one loaded manifest. `_g_idx` gets strictly
    BETTER: it enumerates cells by index, so on the shipped manifest it could
    only ever visit 190 of 823 cells and always the first of each collision.
  * `station/boot.py::start_cell` -> `boot.json`'s `cells_start`, which `main.gd`
    prints. Recomputed by `boot.build()` from the manifest it names, every time,
    so there is nothing stale to leave behind. (`station/generated/` is
    gitignored; no manifest is committed.)
  * `tools/reach_gate.py` -- matches cell **ids**, never indices.
  * THE PER-DECK MANIFESTS ARE NOT TOUCHED. This tool reads them and writes one
    new file. `docs/streaming-4g.md`'s `--start-cell=4` commands run against
    `cells_<deck>/cells.json`, whose numbering is unchanged and stays correct.
  * `station/boot.py::_fixture` writes its own per-deck test manifests with
    `"index": k` -- per deck, so unaffected.

`--legacy-index` is the control: it concatenates without renumbering, exactly as
before, and `--selftest` then FAILS on the file it just wrote.
"""

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLS = os.path.join(ROOT, "station", "generated", "scene", "station", "cells")
OUT = os.path.join(CELLS, "station_cells.json")


def per_deck(cells_dir=CELLS):
    """-> [(stem, manifest)] for every per-deck cell set on disk."""
    out = []
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_cells.json"))):
        stem = os.path.basename(p)[:-len("_cells.json")]
        if stem == "station":                     # our own output
            continue
        with open(p) as f:
            out.append((stem, json.load(f)))
    return out


def duplicate_indices(cells):
    """-> {index: [id, ...]} for every `index` more than one cell claims.

    THE ASSERTION THE MERGE WAS MISSING, in the form a caller can print. It is a
    property of the merged ARRAY -- no geometry, no predicate, no tolerance --
    because `cell_at` and `cell_by_index` are both first-match scans over that
    array and a repeated key makes their composition something other than the
    identity. See the module docstring.
    """
    seen = {}
    for c in cells:
        seen.setdefault(int(c.get("index", -1)), []).append(str(c.get("id", "")))
    return {i: ids for i, ids in seen.items() if len(ids) > 1}


def merge(cells_dir=CELLS, out_path=OUT, renumber=True):
    sets = per_deck(cells_dir)
    if not sets:
        raise SystemExit("merge_cells: no *_cells.json in %s" % cells_dir)

    cells, ids, by_deck = [], set(), {}
    for stem, man in sets:
        rows = man.get("cells", [])
        by_deck[stem] = len(rows)
        for c in rows:
            cid = c.get("id", "")
            # IDS MUST STAY UNIQUE ACROSS THE MERGE. They already are -- every
            # id is prefixed with its deck stem (`blue_0_0_c04z08`) -- but a
            # collision would make `stream.gd` free the wrong cell, which is a
            # hole in the floor rather than a wrong number. Asserted, not
            # assumed.
            if cid in ids:
                raise SystemExit("merge_cells: duplicate cell id %r" % cid)
            ids.add(cid)
            # AND SO MUST INDICES, FOR THE SAME REASON ONE LEVEL DOWN. The id is
            # what the streamer keys residency on; the INDEX is what `cell_at`
            # returns and `cell_by_index`/`prime` look back up, so a repeated
            # index primes a cell the body is not standing in. Renumbering is the
            # whole fix: position in the merged array, which is unique because
            # the array is what the engine scans.
            if renumber:
                c["deck"] = stem
                c["index_in_deck"] = int(c.get("index", -1))
                c["index"] = len(cells)
            cells.append(c)

    dup = duplicate_indices(cells)
    if dup and renumber:
        # Cannot happen -- the index is the array position. Asserted anyway,
        # because a guard that can only fire on a future edit is the only kind
        # worth keeping once the present edit is correct.
        raise SystemExit("merge_cells: renumbering did not make indices unique "
                         "(%d collisions) -- this is a bug in merge()" % len(dup))
    if dup:
        worst = max(dup.items(), key=lambda kv: len(kv[1]))
        print("merge_cells: --legacy-index -- %d of %d cells carry an index "
              "another cell also claims (%d distinct values for %d cells; "
              "index %d alone is shared by %d). `cell_by_index(cell_at(p))` is "
              "NOT the identity on this manifest: see the module docstring and "
              "`python3 tools/cell_identity.py`."
              % (sum(len(v) for v in dup.values()), len(cells),
                 len({int(c.get("index", -1)) for c in cells}), len(cells),
                 worst[0], len(worst[1])))

    # Residency: the widest radius wins. See the module docstring.
    def _f(man, key, default=0.0):
        return float(man.get("residency", {}).get(key, default))

    radius = max(_f(m, "radius_m") for _s, m in sets)
    free = max(_f(m, "free_radius_m", radius * 2.0) for _s, m in sets)
    cell_len = max(_f(m, "cell_length_m") for _s, m in sets)
    widest = max(sets, key=lambda sm: _f(sm[1], "radius_m"))[0]
    base = sets[0][1].get("residency", {})

    # THE CORRIDOR BLOCK, WHICH IS NOT DECORATION. `walk.gd::_configure` reads
    # `plan["corridor"]` for the steering lookahead -- `sqrt(r * w)`, the chord
    # length that sags exactly w/8 off the arc. A merged manifest without it
    # gives r=0, w defaults to 2.5, and the lookahead collapses from 23.4 m to
    # the 1.0 m floor: a body then steers on noise instead of on the arc ahead
    # of it, and `chord sag` prints `inf`. Measured on the first merged run
    # before this block existed.
    #
    # IT CAN ONLY CARRY ONE, AND WHICH ONE IS A REAL COMPROMISE. Every deck has
    # its own corridor radius -- 211.55 m on blue, 268.05 on red, 471.25 on
    # grey -- and `plan` is global. This takes the corridor of the deck with
    # the most cells, which is the deck a player spawns on, so the spawn deck
    # is exactly right and the others are approximately right: lookahead scales
    # as sqrt(r), so the worst case across this station is off by a factor of
    # 1.5, against a factor of 23 for having no block at all.
    #
    # `corridor_by_deck` carries all 70 so a future `walk.gd` can pick by the
    # player's own radius, which is the correct fix and needs an engine change
    # rather than a manifest one. Nothing reads it yet; it is recorded so the
    # next session does not have to re-derive it.
    biggest = max(sets, key=lambda sm: len(sm[1].get("cells", [])))
    by_deck_corr = {s: m.get("corridor", {}) for s, m in sets if m.get("corridor")}

    # THE SOURCE BLOCK, WITHOUT WHICH THE PLAYER IS AT EARTH GRAVITY.
    #
    # A REGRESSION THIS FILE CAUSED, caught by launching the packaged build:
    #
    #   walk: gravity -- NO SPIN STATED -- this build names no deck, so the
    #         body keeps mode=drum at 9.8100 m/s2 (the pre-4r field)
    #
    # against the 7.454 m/s2 (0.7602 g at r=211.55) the ring actually delivers.
    # `walk.gd::_derive_omega2` has two ways to learn which deck it is on, and
    # a STREAMED build can only use the first: `_stream.plan["source"]`. The
    # second parses `<sector>_<ring>_<deck>` out of the collision filename, and
    # a streamed build has no monolith path to parse. Every per-deck manifest
    # carries `source`; the first cut of this merge did not, so the branch fell
    # through to "names no deck" and the body fell at 9.81 down the wrong axis.
    #
    # ONE SOURCE FOR SEVENTY DECKS IS A REAL COMPROMISE, the same one the
    # corridor block above makes and for the same reason: `plan` is global and
    # gravity is per deck -- 0.7602 g at blue's r=211.55, different at grey's
    # r=471.25. This takes the spawn deck's, so the deck a player starts on and
    # spends most of its time on is exactly right and the others are wrong by
    # the ratio of their radii.
    #
    # THE HONEST FIX IS AN ENGINE CHANGE, NOT A MANIFEST ONE, and it already
    # has a precedent here: INV-451 made `ragdoll.gd` work its own gravity out
    # from the body's world position rather than being told, precisely because
    # a stated default that only one caller sets is an unset default.
    # `_derive_omega2` runs once at setup and would need to re-derive as the
    # player crosses rings. `source_by_deck` carries all 70 so that change needs
    # no re-derivation; nothing reads it yet.
    man = {
        "cells": cells,
        "source": biggest[1].get("source", {}),
        "source_by_deck": {s: m.get("source", {})
                           for s, m in sets if m.get("source")},
        "corridor": biggest[1].get("corridor", {}),
        "corridor_from": biggest[0],
        "corridor_by_deck": by_deck_corr,
        "floor_r_m": biggest[1].get("floor_r_m", 0.0),
        "residency": {
            **base,
            "radius_m": radius,
            "free_radius_m": free,
            "cell_length_m": cell_len,
            "radius_from": ("the widest of %d decks (%s) -- see "
                            "tools/merge_cells.py on why max and not min"
                            % (len(sets), widest)),
        },
        # Provenance, so a reader of this file can tell it is derived and from
        # what. Nothing in the engine reads these.
        "merged_from": {"decks": len(sets), "cells": len(cells),
                        "by_deck": by_deck},
        # WHOSE NUMBERING THE `index` FIELD IS, said out loud in the artefact
        # rather than only in this source. A reader holding a manifest can tell
        # whether its indices are an identity without re-deriving it.
        "index_from": ("position in the merged array -- unique by construction; "
                       "the deck-local handle is kept as index_in_deck"
                       if renumber else
                       "THE PER-DECK HANDLE, CONCATENATED AND NOT UNIQUE "
                       "(--legacy-index) -- cell_by_index(cell_at(p)) is not "
                       "the identity on this manifest"),
    }
    with open(out_path, "w") as f:
        json.dump(man, f)
    return man


def report(man):
    r = man["residency"]
    m = man["merged_from"]
    print("merged %d deck cell sets -> %d cells" % (m["decks"], m["cells"]))
    print("  radius %.1f m, free at %.1f m, longest cell %.1f m"
          % (r["radius_m"], r["free_radius_m"], r["cell_length_m"]))
    print("  index: %d distinct value(s) over %d cells -- %s"
          % (len({int(c.get("index", -1)) for c in man["cells"]}),
             len(man["cells"]), man.get("index_from", "?")))
    print("  budget %s tri resident, %s per cell"
          % (r.get("resident_tris"), r.get("cell_tris")))
    # THE WORST CASE THIS MANIFEST CAN PRODUCE, stated rather than discovered
    # by a player. Cells whose arcs overlap within the load radius all become
    # resident together; the honest bound is the heaviest cells that can be
    # co-resident, and the cheap proxy for it is the heaviest few.
    tris = sorted((int(c.get("tris", 0) or 0) for c in man["cells"]),
                  reverse=True)
    n = int(r.get("cells_resident_nominal", 3))
    if tris and tris[0]:
        print("  heaviest %d cells: %s = %s tri against a %s budget"
              % (n, ", ".join("{:,}".format(t) for t in tris[:n]),
                 "{:,}".format(sum(tris[:n])), r.get("resident_tris")))
    print("  decks, largest first:")
    for stem, k in sorted(m["by_deck"].items(), key=lambda kv: -kv[1])[:6]:
        print("    %-16s %3d cells" % (stem, k))


def selftest(cells_dir=CELLS, manifest=None):
    """Assert the merged manifest is loadable by `stream.gd::configure`.

    `manifest` defaults to `<cells_dir>/station_cells.json`, and `main()` passes
    the path it JUST WROTE. It used to read the default no matter where `--out`
    pointed, so a run with a non-default `--out` reported on a stale file it had
    not produced -- the "gate reads an artefact it cannot rebuild" defect in
    miniature.

    IT CHECKS THE THINGS configure() ACTUALLY REFUSES ON, in its own order:
    a dictionary, a `cells` key, a positive residency radius and a positive
    resident triangle budget. `configure` returns false on each of those and
    the game then loads NOTHING -- which is a worse failure than the one this
    tool exists to fix, so it is asserted here rather than discovered on a
    launch.
    """
    p = manifest or os.path.join(cells_dir, "station_cells.json")
    if not os.path.exists(p):
        print("  NO MERGED MANIFEST -- run: python3 tools/merge_cells.py")
        return 1
    with open(p) as f:
        j = json.load(f)
    bad = []
    if not isinstance(j, dict):
        bad.append("not a dictionary")
    if "cells" not in j:
        bad.append("no `cells` key -- configure() calls this 'not a cell manifest'")
    res = j.get("residency", {})
    if float(res.get("radius_m", 0.0)) <= 0.0:
        bad.append("residency radius is not positive")
    if int(res.get("resident_tris", 0)) <= 0:
        bad.append("resident triangle budget is not positive")
    # Every referenced .scn must exist, or the streamer loads a cell into
    # nothing and the player walks into a hole.
    missing = 0
    for c in j.get("cells", []):
        for k in ("mesh", "collision"):
            v = c.get(k, "")
            if v and not os.path.exists(os.path.join(cells_dir, v)):
                missing += 1
    if missing:
        bad.append("%d referenced .scn file(s) are absent" % missing)
    # `index` MUST BE AN IDENTITY. `stream.gd::cell_at` returns it and
    # `cell_by_index`/`prime` look it back up, both by first match over this same
    # array, so a repeated value primes a cell the body is not standing in. This
    # is the cheap half of `tools/cell_identity.py` -- no geometry needed.
    rows = j.get("cells", [])
    dup = duplicate_indices(rows)
    if dup:
        worst = max(dup.items(), key=lambda kv: len(kv[1]))
        bad.append("%d of %d cells share an `index` with another cell "
                   "(%d distinct values; index %d is claimed by %d cells, "
                   "including %s). `cell_by_index(cell_at(p))` therefore primes "
                   "the wrong cell -- run `python3 tools/merge_cells.py` to "
                   "renumber, and `python3 tools/cell_identity.py` for the "
                   "consequence."
                   % (sum(len(v) for v in dup.values()), len(rows),
                      len({int(c.get("index", -1)) for c in rows}),
                      worst[0], len(worst[1]), ", ".join(worst[1][:3])))
    print("merged manifest: %d cells, radius %.1f m, %d distinct index value(s)"
          % (len(rows), float(res.get("radius_m", 0.0)),
             len({int(c.get("index", -1)) for c in rows})))
    if bad:
        for b in bad:
            print("  BAD: %s" % b)
        return 1
    print("\n  MERGED CELL MANIFEST OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", default=CELLS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--legacy-index", action="store_true",
                    help="THE CONTROL: concatenate the per-deck numbering "
                         "without renumbering, as this tool did before session "
                         "4t. --selftest then FAILS on the manifest it wrote.")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.cells, a.out if a.out != OUT else None)
    man = merge(a.cells, a.out, renumber=not a.legacy_index)
    report(man)
    print("\n  wrote %s" % os.path.relpath(a.out, ROOT))
    return selftest(a.cells, a.out)


if __name__ == "__main__":
    sys.exit(main())
