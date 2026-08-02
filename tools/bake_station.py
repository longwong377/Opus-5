#!/usr/bin/env python3
"""BAKE THE WHOLE STATION INTO STREAMING CELLS.

`tools/export_station.py` writes 70 deck meshes and their collision. Godot's
`ResourceLoader` **cannot load a runtime `.glb`** -- there is no glTF format
loader off `res://`, verified with a probe in session 4g -- so a streamable cell
has to be a `.scn`. `godot/scripts/stream.gd::bake()` cuts one deck on
`interior.deck_cell`'s own 20-degree grid, assigns every triangle to exactly one
cell (asserted: the cells sum to the source), preserves the source group names so
`dress_scene.gd` binds identically, and gives the collision proxy the trimesh
colliders while the visual mesh gets none.

It had been run on **one deck**. This runs it on all of them, which is the
difference between a streaming loader that has been demonstrated and a station
that streams.

    python3 tools/bake_station.py --dry-run
    python3 tools/bake_station.py --sector blue
    python3 tools/bake_station.py

Each deck is one headless Godot launch. Failures are recorded per deck with the
engine's own stderr rather than an exit code, because a bake that silently wrote
nothing is the failure mode this project has already paid for twice.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

SRC = os.path.join(ROOT, "station/generated/scene/station")
CELLS = os.path.join(SRC, "cells")


def godot_binary():
    import walkable as W                                        # noqa: PLC0415
    return W.godot_binary()


def decks():
    """Every deck that has BOTH a render mesh and a collision mesh on disk.

    A deck with no collision is not bakeable and saying so here is cheaper than
    discovering it inside the engine: `bake()` returns 2 on a missing
    `--collision` and that reads as a Godot failure rather than a missing input.
    """
    out = []
    for g in sorted(glob.glob(os.path.join(SRC, "*.glb"))):
        stem = os.path.basename(g)[:-4]
        if stem.endswith("_collision") or stem.startswith("column_"):
            continue
        col = os.path.join(SRC, stem + "_collision.glb")
        if not os.path.exists(col):
            out.append((stem, g, None))
            continue
        out.append((stem, g, col))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-decks", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args(argv)

    work = decks()
    if a.sector:
        work = [w for w in work if w[0].startswith(a.sector + "_")]
    if a.max_decks:
        work = work[:a.max_decks]
    missing = [w for w in work if w[2] is None]

    print(f"\nBAKE THE WHOLE STATION\n")
    print(f"  {len(work)} decks on disk, {len(missing)} with no collision mesh")
    if a.dry_run:
        for stem, _g, col in work:
            print(f"     {stem}{'' if col else '   -- NO COLLISION'}")
        return 0

    godot = godot_binary()
    if godot is None:
        print("no double-precision Godot binary. run: bash tools/build_godot.sh")
        return 1
    os.makedirs(CELLS, exist_ok=True)

    man, t0 = {"decks": [], "started": time.time()}, time.time()
    mpath = os.path.join(CELLS, "bake_manifest.json")

    for n, (stem, g, col) in enumerate(work, 1):
        if col is None:
            man["decks"].append({"key": stem, "ok": False,
                                 "why": "no collision mesh on disk"})
            print(f"  [{n}/{len(work)}] {stem}: SKIPPED -- no collision")
            continue
        sec, ring, dk = stem.split("_")[0], stem.split("_")[1], stem.split("_")[2]
        # THE REGISTER'S DECK IS A NAME, NOT AN INDEX -- for the third time this
        # session. `cell_manifest.json`'s deck_table is keyed by INDEX into the
        # ring's stack; grey's locations carry the deck numbers the show uses,
        # 24 through 80, on a 23-deep ring. 15 of 70 bakes died on
        # "no deck_table row for grey ring_index=0 deck_index=24".
        # `deck.deck_index` has existed for exactly this since the session that
        # found 14 of 67 decks failing to assemble; `_ring_cells` goes through
        # it, `routes.py` did not until an hour ago, and this did not either.
        import deck as _D                                      # noqa: PLC0415
        import interior as _it                                 # noqa: PLC0415
        _schema, _profile = _it.load()
        try:
            dk_index = _D.deck_index(_schema, _profile, sec, int(ring), int(dk))
        except Exception:                                      # noqa: BLE001
            dk_index = int(dk)
        t1 = time.time()
        cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
               "res://scenes/walk.tscn", "--", "--bake-cells",
               f"--glb={g}",
               f"--collision={col}",
               f"--sector={sec}", f"--ring-index={ring}",
               f"--deck-index={dk_index}",
               f"--cell-id={stem}",
               f"--cells-out={CELLS}"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               cwd=ROOT, timeout=a.timeout)
            out, err, code = r.stdout, r.stderr, r.returncode
        except subprocess.TimeoutExpired:
            out, err, code = "", f"timed out after {a.timeout}s", -1
        # FRESHNESS, NOT A SET DIFFERENCE. The first version diffed the cell
        # files against a `before` snapshot, so a deck that had been baked in an
        # earlier run re-baked correctly and reported "exit 0, 0 cells" -- the
        # engine's own log in the same block said "7 cells, 782146 triangles
        # (source had 782146)". A verdict that reads as failure when the
        # artefact is already right is worse than no verdict.
        made = sorted(p2 for p2 in glob.glob(os.path.join(CELLS, stem + "_c*.scn"))
                      if os.path.getmtime(p2) >= t1 - 1.0)
        mb = sum(os.path.getsize(p) for p in made) / 1e6

        # THE CELLS ON DISK ARE THE VERDICT, NOT THE EXIT CODE. A bake that
        # exits 0 having written nothing is the failure this project has already
        # paid for twice -- a render_godot.sh that fell back to OpenGL and
        # exited 0 with a PNG, and an export that threw away 71 decks at the
        # write and reported IndexError. Count the artefacts.
        ok = code == 0 and len(made) > 0
        row = {"key": stem, "ok": ok, "cells": len(made),
               "mb": round(mb, 1), "seconds": round(time.time() - t1, 1)}
        if not ok:
            tail = [ln for ln in (err or out).splitlines()
                    if ln.strip()][-3:]
            row["why"] = f"exit {code}, {len(made)} cells"
            row["engine"] = tail
        man["decks"].append(row)
        print(f"  [{n}/{len(work)}] {stem}: "
              + (f"{len(made)} cells, {mb:.1f} MB, {row['seconds']:.0f} s"
                 if ok else f"FAILED -- {row['why']}"))
        if not ok:
            for ln in row.get("engine", ()):
                print(f"        | {ln[:150]}")
        man["elapsed_s"] = round(time.time() - t0, 1)
        with open(mpath, "w") as f:
            json.dump(man, f, indent=1)

    good = [d for d in man["decks"] if d.get("ok")]
    print(f"\n  BAKED {len(good)} of {len(work)} decks into "
          f"{sum(d['cells'] for d in good):,} cells, "
          f"{sum(d['mb'] for d in good):.0f} MB, in "
          f"{man.get('elapsed_s', 0) / 60:.0f} min")
    return 0 if len(good) == len(work) else 1


if __name__ == "__main__":
    sys.exit(main())
