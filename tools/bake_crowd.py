#!/usr/bin/env python3
"""Write the shared crowd body library the runtime instances walkers against.

WHY THIS EXISTS AS ITS OWN TOOL, AND IT IS INSTANCE TEN OF THIS PROJECT'S
SIGNATURE DEFECT REACHING THE ONE PATH THAT SHIPS.

`walk.gd::_load_crowd_libs` resolves `crowd_lod<N>.glb` beside the crowd
placement list and draws every walker as an instance into it. Those files were
written in exactly one place -- inside `walkable.py::_bake`, under `if crowd:`,
as a side effect of running a WALK TEST -- and `deck.py`'s own build path never
called it. So the dev checkout had 0 of them, the package therefore shipped 0
of them, and the launcher printed:

    walk: 83 room occupant(s) have a timetable and NO shared body library
          -- they cannot be drawn
    ERROR: walk: could not load any crowd library

A station simulation with nobody in it. Every craft judgement in session 4t
scored a frame rendered from the DEV TREE, where `render_shot.gd` builds bodies
directly and never consults this library at all, so nine rounds of review
looked at populated rooms and the shipped artefact was empty. That is this
file's own rule -- *a thing is built more than once in this project, and a gate
on one build path says nothing about the other* -- landing on the build the
player actually runs.

THE LIBRARY IS A FUNCTION OF THE SPECIES MIX AND NOT OF WHO IS WALKING, which
is what makes this cheap and what makes it a separate tool rather than a flag
on a deck build. `populace.station_crowd_library(lod)` takes the station's
occupancy-weighted species distribution and emits one body per (species, lod,
phase); it does not need a deck, a route or a cast. Measured: 2.0 s and 87,816
vertices at lod 4. Rebuilding a deck to obtain it -- which is what the old
`walkable.py` path did -- costs minutes and couples a shipped asset to a test.

EVERY RUNG, NOT THE ONE SOME BAKE HAPPENED TO CHOOSE. `populace.crowd_ladder()`
returns ((18.0, 2), (45.0, 4), (400.0, 8)): the runtime picks per person per
frame by distance, so shipping one rung leaves every walker outside that band
undrawable. The ladder is derived from `schedule.NPC_BUDGET`'s allowances, so
it is read here rather than restated.

AND THE CONVERSE, WHICH THIS TOOL DID NOT ASK UNTIL INV-1232. "Is every rung on
disk" and "does every walker name a rung" are different questions, and a build
can pass the first while failing the second: `populace.corridor_lod` derived the
level a placement NAMES by its own copy of `crowd_ladder`'s rule, without
`crowd_ladder`'s near-band cap, so it could answer with a level this file was
never going to write. Nothing in the runtime errors on that -- `npc.gd`'s
`_place_crowd` finds no bucket for the key and the walker is quietly not drawn.
`--selftest` now reads the `*_crowd.json` beside the libraries and asserts the
two sets agree in BOTH directions.
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

DECKDIR = os.path.join(ROOT, "station", "generated", "scene", "deck")


def _glb(obj_path, glb_path):
    """OBJ -> GLB. Same converter `walkable.py` uses, for the same reason."""
    import export_gltf
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj_path, "--out", glb_path]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv


def bake(out_dir=DECKDIR, force=False, keep_obj=False):
    """Emit `crowd_lod<N>.obj/.glb` for every rung of the ladder.

    Returns the list of (lod, glb_path, n_verts, n_groups) actually written.
    """
    import deck as D
    import populace as P

    os.makedirs(out_dir, exist_ok=True)
    written = []
    for _hi, lod in P.crowd_ladder():
        glb = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        if os.path.exists(glb) and not force:
            print("  lod %d: present, skipped (use --force to rebuild)" % lod)
            continue
        obj = os.path.join(out_dir, "crowd_lod%d.obj" % lod)
        v, t, g = P.station_crowd_library(lod)
        D.write_obj(obj, v, t, g)
        _glb(obj, glb)
        # The OBJ is an intermediate: Godot reads the glb and nothing else
        # reads the obj, so it is 3-8 MB of package weight for nothing.
        if not keep_obj:
            os.remove(obj)
        written.append((lod, glb, len(v), len(g)))
        print("  lod %d: %d verts, %d groups -> %s (%.1f MB)"
              % (lod, len(v), len(g), os.path.basename(glb),
                 os.path.getsize(glb) / 1e6))
    return written


def selftest(out_dir=DECKDIR):
    """Assert the ladder is fully covered and every rung is loadable.

    THE ASSERTION IS PER RUNG AND NOT A COUNT, because the defect this tool
    exists to close was not "too few libraries" -- it was zero, and a count
    gate that reads `>= 1` would have passed on a one-rung bake that leaves
    every walker beyond 18 m invisible.

    AND IT CHECKS THE DIRECTORY THAT WAS BAKED, not a default. The first cut
    of this function read `DECKDIR` unconditionally, so `--out scene/station`
    baked three libraries into the streamed build and then reported OK by
    looking at three OTHER files left in `scene/deck` from a previous run --
    a gate passing on evidence from somewhere other than the thing it just
    did. `walk.gd` resolves the library beside the CROWD PLACEMENT LIST, so
    which directory holds it is the entire question.
    """
    import glob
    import json
    import populace as P
    lad = P.crowd_ladder()
    missing = []
    for _hi, lod in lad:
        p = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        if not os.path.exists(p) or os.path.getsize(p) < 1024:
            missing.append(lod)
    print("crowd library in %s -- ladder %s"
          % (os.path.relpath(out_dir, ROOT), tuple(l for _h, l in lad)))
    for _hi, lod in lad:
        p = os.path.join(out_dir, "crowd_lod%d.glb" % lod)
        ok = os.path.exists(p) and os.path.getsize(p) >= 1024
        print("  lod %-2d %-8s %s" % (
            lod, "OK" if ok else "MISSING",
            ("%.1f MB" % (os.path.getsize(p) / 1e6)) if ok else "--"))

    # -- THE OTHER DIRECTION: does every walker name a library that is here? --
    # `walk.gd::_load_crowd_libs` loads these files and `npc.gd::_place_crowd`
    # buckets each walker on `crowd_<species>_<lod>_<phase>`. A record whose
    # `lod` has no glb finds no bucket and is drawn nowhere -- no error, no
    # warning, an empty corridor. So the placement lists are read here, beside
    # the libraries, which is the only place both halves exist at once.
    have = {int(os.path.basename(p)[len("crowd_lod"):-len(".glb")])
            for p in glob.glob(os.path.join(out_dir, "crowd_lod*.glb"))}
    rows = sorted(glob.glob(os.path.join(out_dir, "*_crowd.json")))
    named, orphan, examples = {}, 0, []
    for p in rows:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:                                # noqa: BLE001
            print("  (unreadable %s: %s)" % (os.path.basename(p), exc))
            continue
        for rec in data:
            lv = int(rec.get("lod", -1))
            named[lv] = named.get(lv, 0) + 1
            if lv not in have:
                orphan += 1
                if len(examples) < 3:
                    examples.append("%s: %s" % (os.path.basename(p),
                                                rec.get("mesh", "?")))
    if rows:
        print("\n  %d placement file(s), %d walker(s), naming lods %s"
              % (len(rows), sum(named.values()),
                 {k: v for k, v in sorted(named.items())}))
    else:
        # A GATE MUST SAY WHEN IT DID NOT RUN. Reporting OK here on the
        # strength of three files and no placements is the shape of every
        # manufactured pass in this repository.
        print("\n  NO PLACEMENT LISTS beside the libraries -- the "
              "'does every walker name a rung' half did NOT run.")

    if missing:
        print("\n  CROWD LIBRARY INCOMPLETE -- rungs %s missing." % missing)
        print("  Every walker in those distance bands is undrawable.")
        print("  Run: python3 tools/bake_crowd.py")
        return 1
    if orphan:
        print("\n  %d WALKER(S) NAME A LIBRARY THAT IS NOT HERE -- lods %s."
              % (orphan, sorted(k for k in named if k not in have)))
        for e in examples:
            print("    e.g. %s" % e)
        print("  They are drawn nowhere and the runtime logs nothing.")
        print("  The generator picked a level off the ladder: see "
              "populace.lod_for_distance and INV-1232.")
        return 1
    print("\n  CROWD LIBRARY OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DECKDIR)
    ap.add_argument("--force", action="store_true",
                    help="rebuild rungs that already exist")
    ap.add_argument("--keep-obj", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="assert every ladder rung is present; exit 1 if not")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.out)
    print("baking the shared crowd library into %s"
          % os.path.relpath(a.out, ROOT))
    bake(a.out, force=a.force, keep_obj=a.keep_obj)
    return selftest(a.out)


if __name__ == "__main__":
    sys.exit(main())
