#!/usr/bin/env python3
"""BUILD THE WORLD. Cross-platform, no shell required.

    python tools/build_world.py

This is `tools/build_world.sh` with the bash taken out, because the bash was a
Windows blocker for no reason -- every step in it was already a plain Python
call. Run this once, wait, then open `godot/` in Godot 4.4 and press play.

WHAT IT PRODUCES, and why it is not simply committed: about 6.2 GB of meshes,
collision shells, streaming cells, crowd bodies and audio under
`station/generated/`. It is generated rather than authored, so it does not
belong in git and could not fit there anyway.

WHAT IT COSTS: roughly 45 minutes on four cores, nearly all of it in the first
three steps. It is skippable afterwards -- `--check` reports what is already
on disk without building anything.

ORDER MATTERS in exactly one place and it is not obvious, so it is spelled out
at the step: the drum must be cut AFTER the whole-station bake, which would
otherwise overwrite its 85 cells with one.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD_MARK = ROOT / "station/generated/scene/station/cells/station_cells.json"

# THE FLOOR UNDER "SHIPPABLE", and it is deliberately far below the real total.
# A complete bake is ~907 cells over 76 decks, and blue_0_0 alone is 103. This
# is not a quality bar -- `--gates-only` is where quality is judged. It is the
# line between "a station missing some content" and "the world build fell over
# and produced a shell", which is the only distinction the export step needs.
MIN_SHIPPABLE_CELLS = 400

# (label, argv-after-the-interpreter, note-or-None)
STEPS: list[tuple[str, list[str], str | None]] = [
    (
        "the deck table every later step reads",
        ["station/interior.py", "--cell-manifest"],
        # FIRST, BECAUSE EVERYTHING AFTER IT READS THE FILE IT WRITES.
        # `cell_manifest.json` is tracked and shipped, the engine reads it on the
        # player's path, and until now NOTHING IN THIS BUILD REGENERATED IT --
        # its only caller in the repository was a one-liner inside a
        # `continue-on-error: true` step of validate.yml. So the table on disk
        # described whatever the station looked like the last time a human
        # remembered to run it.
        #
        # Measured against a fresh derivation on the tree that shipped it: 164 of
        # 252 deck rows differ and 15 decks are missing entirely. `red 2/18` is
        # one of the fifteen, which is precisely why the last Windows build
        # printed `bake: no deck_table row for red ring_index=2 deck_index=18`
        # and lost eleven decks at step 3.
        #
        # It costs seconds and it is pure Python, so there is no argument for
        # leaving it out other than nobody having noticed.
        "everything downstream reads deck_table -- see the comment in this file",
    ),
    ("export the ring decks and columns", ["tools/export_station.py"], None),
    ("export the habitat drum", ["tools/export_drum.py"], None),
    ("bake every deck into streaming cells", ["tools/bake_station.py"], None),
    (
        "cut the drum into its own cells",
        ["tools/bake_drum.py", "--bake"],
        # stream.gd::bake() takes its axial band from
        # cell_manifest.json deck_table[<deck>].cell_length_m, and the drum's
        # row carries 0.0 because interior.ring_cells derives that figure from
        # a ring corridor and the drum has none. A zero band is ONE cell of
        # 1,585,762 triangles, 26x the per-cell budget. This must run after the
        # bake above, which would otherwise overwrite the 85 cells with one.
        "must follow the bake above -- see the comment in this file",
    ),
    ("bake the transit columns", ["tools/bake_columns.py", "--force"], None),
    ("merge into one manifest and renumber", ["tools/merge_cells.py"], None),
    ("dialogue and arrival sidecars", ["tools/bake_sidecars.py", "--stale"], None),
    (
        "the shared crowd library",
        ["tools/bake_crowd.py", "--out", "station/generated/scene/station", "--force"],
        None,
    ),
    ("the boot manifest", ["station/boot.py"], None),
]

GATES: list[list[str]] = [
    ["tools/reach_gate.py"],
    ["tools/cell_identity.py"],
    ["tools/cast_gate.py"],
    ["tools/crowd_material_gate.py", "--wiring"],
    ["tools/column_site.py", "--gate"],
    ["station/populace.py", "--lod-gate"],
    ["tools/bake_sidecars.py", "--check"],
    ["tools/merge_cells.py", "--selftest"],
    # SECONDS, NO GODOT, NO BAKE -- and it is the check that would have caught
    # run 9's column failure before 45 minutes of export. It asserts every
    # column mesh sits where its manifest says, which is exactly the mismatch
    # that made the yellow shaft refuse: `column_site(rule="floor")` measures
    # against baked deck cells ON DISK, and step 1 runs two steps before those
    # cells exist, so the export placed the columns provisionally and step 5
    # re-derived them 80 m away.
    ["tools/bake_columns.py", "--check-mesh"],
    # THE PAIRWISE QUESTION merge_cells asks, asked in seconds instead of after
    # a 49-minute world build. Every deck of a ring must sit at a distinct
    # radius at least MIN_HEADROOM_M apart -- which `--ladder` reads OUT of
    # merge_cells rather than restating, so this gate cannot pass a build that
    # tool would refuse. It is RED until Shell B stops claiming rungs the
    # register already holds, and that is the point of it.
    ["station/interior.py", "--ladder"],
    # DOES THE WORLD REMEMBER YOU? Three launches: a customs refusal is
    # written, a FRESH PROCESS finds it, and withholding only the write makes
    # it vanish. It lives here rather than in validate.yml because it needs a
    # BUILT WORLD and validate.yml has never had one -- `journal.py --gate`
    # says SKIP there, correctly. This step runs after the .exe is uploaded, on
    # a machine holding the whole station, which is the one place the question
    # is answerable.
    #
    # `save.gd` was complete, tested and audited with no caller that writes on
    # the shipped path, so CONTINUE was dead from the day it was built. The
    # gate that proves the fix was written in the same session and NOTHING RAN
    # IT -- the identical defect one level up. This is that caller.
    ["station/journal.py", "--persist-gate"],
    # DOES EACH DECK'S STREAMING BAND CONTAIN ITS OWN FLOOR? The band comes from
    # `cell_manifest.json`'s deck_table and the floor comes from the mesh, so the
    # two can drift apart without either being wrong on its own -- and when they
    # do, a body walks onto a deck whose cells are never resident and falls
    # through the world. Session 4s closed this at 15 decks / worst 68.40 m and
    # then a later commit moved the station under it: an audit re-ran the same
    # gate on HEAD and got 82 of 119 decks, worst 292.56 m, exit 1.
    #
    # It was never in this list, which is why nobody saw it go. The gate existed,
    # passed when written, and had no caller -- the shape this project keeps
    # producing. With `--cell-manifest` now running as step 1 the drift should be
    # zero; this is what proves it rather than assuming it.
    ["tools/bake_station.py", "--shell-audit"],
]


LOGDIR = ROOT / "logs"


def run(argv: list[str], logname: str | None = None) -> int:
    """Run one step with THIS interpreter, so a machine with both python2 and
    python3, or a venv, cannot end up running a different one than the caller.

    Output is TEED to `logs/<logname>.log` rather than left on the console,
    because the console is the thing that fails you when it matters. The first
    CI run of this driver failed in step 1 and printed the reason 43 minutes
    before the run ended -- past what GitHub's log API will hand back, which
    caps at a few thousand trailing lines. A step's own log file survives as an
    artefact, and on failure the tail of it is reprinted at the END of the
    console output, where it is reachable."""
    if logname is None:
        return subprocess.call([sys.executable, *argv], cwd=str(ROOT))
    LOGDIR.mkdir(exist_ok=True)
    path = LOGDIR / f"{logname}.log"
    with open(path, "w", encoding="utf-8", errors="replace") as fh:
        rc = subprocess.call([sys.executable, *argv], cwd=str(ROOT),
                             stdout=fh, stderr=subprocess.STDOUT)
    if rc != 0:
        print(f"    --- last 40 lines of {path.relative_to(ROOT)} ---")
        try:
            tail = path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
            for line in tail:
                print(f"    | {line}")
        except OSError as e:
            print(f"    (could not read the log: {e})")
        print("    --- end ---")
    return rc


def world_on_disk() -> int | None:
    """Streaming-cell count if the world is built, else None."""
    try:
        with open(WORLD_MARK, encoding="utf-8") as fh:
            return len(json.load(fh)["cells"])
    except (OSError, ValueError, KeyError):
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="build the station's world")
    ap.add_argument("--check", action="store_true",
                    help="report what is on disk and exit without building")
    ap.add_argument("--skip-gates", action="store_true",
                    help="build only; do not run the eight verification gates")
    ap.add_argument("--keep-going", action="store_true",
                    help="run every step even after one fails (the old behaviour; "
                         "it buries the first error under everything after it)")
    ap.add_argument("--gates-only", action="store_true",
                    help="run the eight gates against a world already on disk "
                         "and build nothing. This is how CI verifies AFTER it "
                         "has exported and uploaded a binary, so that a failing "
                         "gate reports a fault instead of destroying delivery")
    args = ap.parse_args(argv)

    print(f"python  {sys.version.split()[0]}  ({sys.executable})")
    print(f"root    {ROOT}")

    built = world_on_disk()
    if args.check:
        # THIS IS NOW THE STEP THAT DECIDES WHETHER A BUILD SHIPS, so it has to
        # be able to say no. It returned 0 unconditionally -- it printed
        # "NOT BUILT" and exited SUCCESS, which is this project's own
        # "a criterion that cannot fail is measuring the wrong thing", sitting
        # in the one place CI asks whether the world is there.
        #
        # The bar is what a PLAYER needs, not what the build intended:
        # somewhere to stand, and a crowd that can be drawn. Missing transit
        # lifts are a degraded station; missing decks are not a station.
        missing = []
        if not built:
            missing.append(f"no merged cell manifest at "
                           f"{os.path.relpath(WORLD_MARK, ROOT)} -- nothing to stand on")
        elif built < MIN_SHIPPABLE_CELLS:
            missing.append(f"only {built} streaming cells, under the "
                           f"{MIN_SHIPPABLE_CELLS} a walkable station needs")
        crowd = ROOT / "station/generated/scene/station"
        for rung in (2, 4, 8):
            if not (crowd / f"crowd_lod{rung}.glb").exists():
                missing.append(f"no crowd_lod{rung}.glb -- every walker in that "
                               f"band is undrawable")
        if missing:
            print("world   NOT SHIPPABLE:")
            for m in missing:
                print(f"          {m}")
            return 1
        print(f"world   {built} streaming cells, all three crowd rungs present")
        return 0
    if built:
        print(f"world   already built: {built} streaming cells")
        print("        delete station/generated/ to force a full rebuild")

    t0 = time.time()
    failed: list[str] = []

    steps = [] if args.gates_only else STEPS
    for i, (label, cmd, note) in enumerate(steps, 1):
        print(f"\n=== {i}/{len(steps)}  {label}")
        if note:
            print(f"    ({note})")
        rc = run(cmd, logname=f"{i:02d}-{cmd[0].split('/')[-1].removesuffix('.py')}")
        if rc != 0:
            print(f"    FAILED rc={rc}")
            failed.append(label)
            # FAIL FAST BY DEFAULT. Steps 3 onward consume step 1's output, so
            # after an early failure every later step fails for a reason that is
            # not its own -- eight failures reported, one of them real.
            if not args.keep_going:
                print("\n    stopping here; the failure above is the real one.")
                print("    (--keep-going runs the rest anyway)")
                break

    # AND NOT AFTER A BUILD FAILURE. Run 3 reported six failures of which one
    # was real: the bake died, and then five gates ran anyway and each reported
    # that a file the bake never wrote was missing. Reading that log, the real
    # cause is one line among six equally-loud ones. A gate that runs against
    # inputs it knows were not built is not measuring anything.
    if not args.skip_gates and not failed:
        print(f"\n=== gates")
        for cmd in GATES:
            name = " ".join(cmd)
            rc = run(cmd, logname="gate-" + cmd[0].split("/")[-1].removesuffix(".py"))
            print(f"    {'PASS' if rc == 0 else f'FAIL rc={rc}'}  {name}")
            if rc != 0:
                failed.append(name)

    mins = (time.time() - t0) / 60.0
    print(f"\n{'=' * 60}")
    if failed:
        print(f"INCOMPLETE after {mins:.1f} min -- {len(failed)} step(s) failed:")
        for f in failed:
            print(f"    {f}")
        return 1

    cells = world_on_disk()
    print(f"DONE in {mins:.1f} min -- {cells} streaming cells on disk.")
    print("Now open the `godot/` folder in Godot 4.4 and press play.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
