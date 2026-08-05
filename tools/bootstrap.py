#!/usr/bin/env python3
"""Rebuild every generated artefact the gates read, in one command.

WHY THIS EXISTS. `station/generated/` is gitignored -- correctly, it is 4.5 GB
of derived geometry -- and this project runs in a container that is reclaimed
after a period of inactivity. Session 4q was recycled THREE TIMES. Each time the
repository came back at an older commit (recoverable: everything was pushed) and
`station/generated/` came back partly empty (not recoverable: it is derived).

Each time, the same five commands were re-derived by hand from five different
places, because nothing named them together:

    python3 station/generate_hull.py
    python3 station/lod.py --build
    python3 station/dockwork.py --loop --days 14 --role lurker --seed downbelow \
        --save station/generated/economy.json
    python3 station/npc/ragdoll.py --emit station/generated/scene/npc
    python3 station/boot.py

AND THE GATES THAT NEED THEM ALREADY SAY SO, ONE AT A TIME. `coldstart.py`'s
`built_deck`, `purse_ledger` and `ragdoll_bodies` each print the exact command
that rebuilds their own input -- that work is what made this file obvious. A
precondition that names its fix is right; five preconditions naming five fixes
that nobody can run as a set is a checklist, and a checklist is a thing people
half-do.

WHAT IT DELIBERATELY DOES NOT DO. It does not build the deck geometry
(`station/rooms.py --footprint` is 23 minutes) or bake the streaming cells
(`stream.gd::bake`, and it needs Godot). Those survive a recycle here because
they are large files the snapshot keeps, and rebuilding them unasked would turn
a 4-minute recovery into a 40-minute one. `--check` says whether they are
present; if they are not, it says which command builds them and stops rather
than guessing that you wanted to wait.

IDEMPOTENT BY DESIGN. Every step tests for its own output first, so running this
on a warm container costs one `os.path.exists` per step. `--force` rebuilds
anyway. That matters because the most likely caller is a session that does not
yet know what is missing.

Run:
    python3 tools/bootstrap.py            # rebuild whatever is missing
    python3 tools/bootstrap.py --check    # report only, build nothing
    python3 tools/bootstrap.py --force    # rebuild everything
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEN = os.path.join(ROOT, "station", "generated")


def _n_glob(pat):
    return len(glob.glob(os.path.join(GEN, pat)))


def _boot_has(key):
    """Is `boot.json` present AND current enough to carry `key`?

    PRESENT IS NOT CURRENT, and that distinction cost a debugging pass in 4q:
    the restored `boot.json` predated `_checks`/`_collapses`, so it parsed, held
    a spawn, and was missing exactly the two keys the new gates read. G4 would
    have run, found `table=0`, and reported a CONTENT failure on a stale file.
    """
    p = os.path.join(GEN, "scene", "boot.json")
    if not os.path.exists(p):
        return False
    try:
        with open(p) as f:
            return bool(json.load(f).get(key))
    except Exception:                                            # noqa: BLE001
        return False


# name, "is it there" predicate, the command, why anything cares.
#
# ORDER IS DEPENDENCY ORDER, not importance: `lod.py --build` decimates the hull
# `generate_hull.py` writes, and `boot.py` reads the ragdoll directory when it
# bakes the day's collapses.
STEPS = (
    # TWO STEPS, NOT ONE, AND THE FIRST RUN OF THIS FILE IS WHY. It had a
    # single "hull" step running `generate_hull.py` and testing for
    # `station.glb` -- and `generate_hull.py` writes `hull.obj`. `station.glb`
    # comes from `export_gltf.py`, which is a SEPARATE CI step. So the step
    # exited 0, wrote its real output, and this tool reported FAILED.
    #
    # That is the design working rather than a wart: verifying the OUTPUT and
    # not the exit code is the whole point (see the note in the run loop), and
    # the first thing it caught was its own author's wrong predicate.
    ("hull",
     lambda: os.path.exists(os.path.join(GEN, "hull.obj")),
     ["python3", "station/generate_hull.py"],
     "the hull itself -- the LOD chain decimates it and every exterior shot "
     "reads its levels"),
    ("station.glb",
     lambda: os.path.exists(os.path.join(GEN, "station.glb")),
     ["python3", "station/export_gltf.py"],
     "the glTF the well-formedness gate parses"),
    ("lod chain",
     lambda: _n_glob("hull_lod*.obj") >= 8,
     ["python3", "station/lod.py", "--build"],
     "hull_lod0..7.obj. `export_scene` renders lod0, NOT hull.obj, and its "
     "self-test fails on the missing files -- which went unnoticed because the "
     "CI step ran `lod.py` bare, which is the selftest and not the builder"),
    ("economy ledger",
     lambda: os.path.exists(os.path.join(GEN, "economy.json")),
     ["python3", "station/dockwork.py", "--loop", "--days", "14",
      "--role", "lurker", "--seed", "downbelow",
      "--save", "station/generated/economy.json"],
     "the player's purse. Without it `player.gd::has_purse()` is false, `tier` "
     "stays at its -99 sentinel, and every checkpoint correctly declines to "
     "read a card that does not exist -- which reads as a dead check"),
    ("ragdoll bodies",
     lambda: _n_glob(os.path.join("scene", "npc", "*_ragdoll.json")) >= 14,
     ["python3", "station/npc/ragdoll.py", "--emit",
      "station/generated/scene/npc"],
     "14 species. `ragdoll.gd` refuses to promote without them, so nobody "
     "falls over"),
    ("boot manifest",
     lambda: _boot_has("checks") and _boot_has("collapses"),
     ["python3", "station/boot.py"],
     "what the game boots into, PLUS the 98 identicard checks and the day's 45 "
     "collapses. A boot.json without those keys is stale, not absent"),
)

def _sidecars_carry(field):
    """Do the deck interact sidecars carry `field`, or do they predate it?

    PRESENCE IS NOT FRESHNESS, AND THIS TOOL COULD NOT SEE THE DIFFERENCE UNTIL
    A BUILD AGENT SAID SO. Every check above asks "is the file there". The
    `*_interact.json` sidecars ARE there -- and every one in this container was
    written on 2026-08-02, before `interact.verb_payload` existed, so they carry
    no `counter`, `holds`, `kind`, `text` or `live` field. Four verbs' data
    missing from the only artefact `interact.gd` can read, and the shipped build
    boots into one of them.

    That is the same defect as `_boot_has` one level out, and it is the reason
    that function tests for KEYS rather than for the file. A stale artefact is
    worse than an absent one: absent fails loudly, stale answers confidently
    with last week's world.

    NOT AUTO-REBUILT, because the writer is `walkable.py`/`arrival.py` building
    a whole deck -- minutes of full CPU, and this tool's contract is that it is
    cheap. Reported instead, with the command.
    """
    d = os.path.join(GEN, "scene", "deck")
    have = glob.glob(os.path.join(d, "*_interact.json"))
    if not have:
        return None, "no deck sidecars at all"
    stale = []
    for f in have:
        try:
            with open(f) as fh:
                rows = json.load(fh)
        except Exception:                                        # noqa: BLE001
            stale.append(os.path.basename(f))
            continue
        rows = rows if isinstance(rows, list) else rows.get("items", [])
        if not any(field in r for r in rows if isinstance(r, dict)):
            stale.append(os.path.basename(f))
    return (not stale), ("%d of %d sidecars carry no `%s`: %s"
                         % (len(stale), len(have), field,
                            ", ".join(sorted(stale)[:3])
                            + (" ..." if len(stale) > 3 else "")))


def _cell_coverage():
    """How many decks have a baked cell set, out of how many exist.

    THE THIRD TIME "PRESENT" HAS MEANT "ONE OF THEM" IN THIS FILE, and the
    first two are `_boot_has` and `_sidecars_carry`, both of which exist
    because a file being on disk says nothing about whether it describes the
    world. The streaming-cells check was `len(glob("cells_*")) > 0`. After a
    container recycle exactly ONE cell set had been rebuilt -- `cells_blue_0_0`
    -- and this tool said `present`.

    What that hides is not small. Those 18 cells span **12.9 m of z** out of an
    8,047 m station, and 8 of the register's 129 located places overlap them;
    121 are unreachable from the spawn. `cell_manifest.json`'s own deck table
    lists 251 decks and STATE.md records the last full bake as 70 decks / 955
    cells / 1.7 GB. A session reading `present` here would conclude the
    streamed build was intact and spend a while wondering why the station was
    small.

    Reported rather than rebuilt, per this file's contract: the baker is
    `stream.gd::bake` and it needs Godot. But the NUMBER is printed, because a
    fraction is a thing a reader can act on and a word is not.

    DELIBERATELY NOT IN THE EXIT CODE, and the reason is that I do not know the
    denominator. `cell_manifest.json` lists 251 decks; STATE.md records the
    last full bake as 70, which is presumably the decks that have content
    worth streaming. Nothing in the repository states which of those two is the
    target, so failing the check against either would be asserting a number I
    cannot defend -- the exact move this project's own history warns about when
    a gate's bar is picked for convenience. Print the fraction, name the
    command, and let whoever settles the target put it in the exit code.
    """
    have = len(glob.glob(os.path.join(GEN, "scene", "deck", "cells_*")))
    want = 0
    p = os.path.join(GEN, "cell_manifest.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                want = len(json.load(f).get("deck_table", []))
        except Exception:                                        # noqa: BLE001
            want = 0
    return have, want


# Things this does NOT build, with the command that does. Reported by --check so
# a session knows the difference between "missing and cheap" and "missing and
# forty minutes".
HEAVY = (
    ("deck geometry", lambda: _n_glob(os.path.join("scene", "deck", "*.glb")) > 0,
     "python3 station/rooms.py --footprint    # ~23 min"),
)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="report what is missing and build nothing")
    ap.add_argument("--force", action="store_true",
                    help="rebuild every step even if its output is present")
    a = ap.parse_args()

    print("bootstrap: station/generated/ is gitignored and a recycled container "
          "loses it.\n")
    missing = [s for s in STEPS if a.force or not s[1]()]
    for name, have, cmd, why in STEPS:
        state = "present" if have() else "MISSING"
        # NOT `why.split(".")[0]` -- the first entry's reason is
        # "hull_lod0..7.obj" and a split on the full stop cut it to
        # "hull_lod0". Take the first clause instead.
        print("  %-16s %-8s %s" % (name, state, why.split(" -- ")[0]))
    print("")
    for name, have, cmd in HEAVY:
        if not have():
            print("  %-16s MISSING  not built here -- run: %s" % (name, cmd))
        else:
            print("  %-16s present  (not rebuilt by this tool)" % name)

    # COMPLETENESS, SEPARATELY FROM PRESENCE. See `_cell_coverage`. A count
    # rather than a word, because "present" was true on 1 deck of 251.
    have, want = _cell_coverage()
    if have == 0:
        print("  %-16s MISSING  no cell set at all -- run: python3 "
              "station/boot.py --bake   # needs Godot" % "streaming cells")
    elif want and have < want:
        print("  %-16s PARTIAL  %d of %d decks in cell_manifest.json have a "
              "baked cell set" % ("streaming cells", have, want))
        print("  %-16s          a recycled container loses these; the last "
              "full bake was 70 decks / 955 cells" % "")
        print("  %-16s          rebuild: python3 station/boot.py --bake  "
              "# needs Godot" % "")
    else:
        print("  %-16s present  %d cell set(s)" % ("streaming cells", have))

    # FRESHNESS, SEPARATELY FROM PRESENCE. See `_sidecars_carry`.
    ok_side, why_side = _sidecars_carry("counter")
    if ok_side is None:
        print("  %-16s MISSING  %s" % ("deck sidecars", why_side))
    elif not ok_side:
        print("  %-16s STALE    %s" % ("deck sidecars", why_side))
        print("  %-16s          rebuild: python3 station/walkable.py "
              "--deck blue/0/0" % "")
    else:
        print("  %-16s present  and current" % "deck sidecars")

    if a.check:
        print("\n%d of %d cheap artefacts missing.%s"
              % (len(missing), len(STEPS),
                 "" if ok_side else " Deck sidecars STALE."))
        return 1 if (missing or ok_side is False) else 0
    if not missing:
        print("\nnothing to do.")
        return 0

    print("\nrebuilding %d:" % len(missing))
    bad = 0
    for name, _have, cmd, _why in missing:
        t0 = time.time()
        print("  %-16s %s" % (name, " ".join(cmd)))
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        dt = time.time() - t0
        # VERIFY THE OUTPUT, NOT THE EXIT CODE. A tool that exits 0 having
        # silently produced nothing is this project's most expensive failure
        # mode -- the renderer that fell back to OpenGL and exited 0 with a PNG
        # cost a whole session of visual judgement.
        ok = _have()
        print("     %s in %.0f s%s"
              % ("ok" if ok else "FAILED", dt,
                 "" if ok else " -- exit %d, and its output is still absent"
                 % r.returncode))
        if not ok:
            bad += 1
            for line in (r.stdout + r.stderr).splitlines()[-6:]:
                print("       | " + line)
    print("\nbootstrap %s" % ("PASS" if not bad else "FAILED on %d" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
