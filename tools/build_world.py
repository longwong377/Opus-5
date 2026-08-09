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

# (label, argv-after-the-interpreter, note-or-None)
STEPS: list[tuple[str, list[str], str | None]] = [
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
    args = ap.parse_args(argv)

    print(f"python  {sys.version.split()[0]}  ({sys.executable})")
    print(f"root    {ROOT}")

    built = world_on_disk()
    if args.check:
        print(f"world   {built} streaming cells" if built
              else "world   NOT BUILT -- run this without --check")
        return 0
    if built:
        print(f"world   already built: {built} streaming cells")
        print("        delete station/generated/ to force a full rebuild")

    t0 = time.time()
    failed: list[str] = []

    for i, (label, cmd, note) in enumerate(STEPS, 1):
        print(f"\n=== {i}/{len(STEPS)}  {label}")
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

    if not args.skip_gates:
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
