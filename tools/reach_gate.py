#!/usr/bin/env python3
"""Is every place in the register inside a cell the shipped build can load?

THE GATE THIS PROJECT NEVER HAD, and its absence is why a 5 GB download
contained 129 rooms and let a player into 16 of them.

Every existing whole-station number answers a DIFFERENT question and all of
them were green while that was true:

    deck.py --sweep        "128 of 128 locations on an assembled cluster"
                           -- the generator assembling IN MEMORY during a sweep
    directory.py           per-layer completion over the register
    boot.py --axial-gate   a body walks between cells ON ONE DECK
    bake_station.py        "70 of 74 decks baked" -- how much was CUT
    package.sh             every engine read is staged

Not one of them asks whether a place a player can name is inside a cell the
shipped manifest can stream. `bake_station.decks()` returned 1 against a
register of 71 for the whole of this project's life and nothing anywhere
failed, because the question was never posed.

WHY IT ASKS ABOUT CELLS AND NOT ABOUT GEOMETRY. A place with a mesh on disk is
not reachable; a place inside a cell in the manifest `boot.json` names is at
least LOADABLE. This gate draws that line deliberately and stops there, and the
distinction is the whole finding of session 4t: 70 decks shipped inside the
package and one of them loaded.

AND IT IS HONEST ABOUT WHAT IT STILL CANNOT SEE. Loadable is not walkable. A
cell that streams can still be an island with no floor joining it to the
player's -- that is the transit columns' job, and this gate does not test it.
It reports COVERAGE, and `boot.py --axial-gate` reports TRAVEL. Two claims,
kept apart on purpose, because collapsing them is how "128 of 128" came to mean
nothing.
"""

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
CELLS = os.path.join(ROOT, "station", "generated", "scene", "station", "cells")
MERGED = os.path.join(CELLS, "station_cells.json")


def register():
    """key -> the register row, for every place the gazetteer addresses."""
    import directory as dr                                      # noqa: PLC0415
    return {q["key"]: q for q in dr.PLACES}


def places_in_cells(cells_dir=CELLS):
    """key -> [deck stems whose places sidecar carries it]."""
    out = {}
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_places.json"))):
        stem = os.path.basename(p)[:-len("_places.json")]
        try:
            with open(p) as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        rows = d.get("places", d) if isinstance(d, dict) else d
        for r in rows if isinstance(rows, list) else []:
            k = r.get("key") or r.get("place")
            if k:
                out.setdefault(k, []).append(stem)
    return out


def manifest_decks(path=MERGED):
    """Which deck stems the shipped manifest actually carries cells for.

    A places sidecar existing is not the same as its deck being IN the manifest
    -- that gap is exactly how 113 places came to be shipped and unreachable --
    so coverage is intersected against this.
    """
    if not os.path.exists(path):
        return None
    with open(path) as f:
        j = json.load(f)
    stems = set()
    for c in j.get("cells", ()):
        cid = str(c.get("id", ""))
        # `blue_0_0_c04z08` -> `blue_0_0`; the cell suffix is always `_c<..>`
        i = cid.rfind("_c")
        if i > 0:
            stems.add(cid[:i])
    return stems


def run(cells_dir=CELLS, manifest=MERGED, verbose=False):
    reg = register()
    cover = places_in_cells(cells_dir)
    stems = manifest_decks(manifest)

    if stems is None:
        print("reach: NO MERGED MANIFEST at %s"
              % os.path.relpath(manifest, ROOT))
        print("       run: python3 tools/merge_cells.py")
        return 1

    loadable, sidecar_only, absent = [], [], []
    for k in sorted(reg):
        on = cover.get(k, [])
        if not on:
            absent.append(k)
        elif any(s in stems for s in on):
            loadable.append(k)
        else:
            sidecar_only.append(k)

    n = len(reg)
    print("reach gate -- %d places in the register, manifest carries %d deck(s)"
          % (n, len(stems)))
    print("  LOADABLE            %3d  in a cell the shipped manifest streams"
          % len(loadable))
    print("  cell set not merged %3d  a sidecar names them, the manifest has "
          "no cell" % len(sidecar_only))
    print("  no cell at all      %3d  nothing has been baked for them"
          % len(absent))

    if sidecar_only:
        print("\n  NOT MERGED (%d):" % len(sidecar_only))
        for k in sidecar_only[:20]:
            print("    %-22s on %s" % (k, ", ".join(cover[k])[:48]))
    if absent:
        print("\n  NO CELL (%d):" % len(absent))
        for k in absent[:20]:
            q = reg[k]
            print("    %-22s %s/%s/%s" % (k, q.get("sector"), q.get("ring"),
                                          q.get("deck")))
    if verbose:
        print("\n  decks in the manifest: %s" % ", ".join(sorted(stems)))

    bad = len(sidecar_only) + len(absent)
    if bad:
        print("\n  %d of %d PLACES ARE NOT LOADABLE." % (bad, n))
        print("  A place the register names and the build cannot stream is a")
        print("  room the player is told about and cannot reach.")
        return 1
    print("\n  EVERY PLACE IN THE REGISTER IS IN A LOADABLE CELL (%d/%d)"
          % (len(loadable), n))
    print("  NOTE: loadable is not walkable. Whether a floor joins them is")
    print("  `station/boot.py --axial-gate`, which this gate does not answer.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", default=CELLS)
    ap.add_argument("--manifest", default=MERGED)
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    return run(a.cells, a.manifest, a.verbose)


if __name__ == "__main__":
    sys.exit(main())
