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


def merge(cells_dir=CELLS, out_path=OUT):
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
            cells.append(c)

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


def selftest(cells_dir=CELLS):
    """Assert the merged manifest is loadable by `stream.gd::configure`.

    IT CHECKS THE THINGS configure() ACTUALLY REFUSES ON, in its own order:
    a dictionary, a `cells` key, a positive residency radius and a positive
    resident triangle budget. `configure` returns false on each of those and
    the game then loads NOTHING -- which is a worse failure than the one this
    tool exists to fix, so it is asserted here rather than discovered on a
    launch.
    """
    p = os.path.join(cells_dir, "station_cells.json")
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
    print("merged manifest: %d cells, radius %.1f m"
          % (len(j.get("cells", [])), float(res.get("radius_m", 0.0))))
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
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.cells)
    man = merge(a.cells, a.out)
    report(man)
    print("\n  wrote %s" % os.path.relpath(a.out, ROOT))
    return selftest(a.cells)


if __name__ == "__main__":
    sys.exit(main())
