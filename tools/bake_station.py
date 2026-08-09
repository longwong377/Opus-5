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
import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

SRC = os.path.join(ROOT, "station/generated/scene/station")
CELLS = os.path.join(SRC, "cells")


# ===========================================================================
# THE PLACES SIDECAR -- what a cell set could not say, and why that mattered
# ===========================================================================
#
# A baked cell knows its arc, its band, its triangles and its spawn. It does
# NOT know that `obs_dome_2` is inside it, because `stream.gd::bake()` bins
# TRIANGLES and the register lives in Python. So every question of the form
# "did the player get ANYWHERE" could only be answered in metres of z.
#
# That is the difference between "the streamer performed 5 loads and 3 frees"
# and "the player walked from the docking bays to Observation Dome 2". The
# first is a statement about a cache; only the second is a statement about the
# station. R5's acceptance is written in the second form on purpose.
#
# WHY IT IS A SIDECAR AND NOT A FIELD ON THE CELL ROW. A place is addressed by
# (angle, z) and has a FOOTPRINT: `docking_bays` is 97.5 deg wide and 140 m
# long and therefore overlaps many cells, while `bay_elevators` is 2.2 deg and
# 24 m and sits inside one. Writing "the place in this cell" onto a cell row
# forces a one-to-one answer to a many-to-many question, and the first thing it
# would lose is the big places -- which are the ones a walk actually crosses.
# The sidecar carries the footprint and lets the reader do the overlap.
#
# AND IT IS EMITTED BY BOTH BAKE PATHS RATHER THAN BY THIS ONE. `boot.py
# --bake` shells straight out to `stream.gd::bake()` for a single cluster and
# never comes through `main()` here. A sidecar written only by the whole-
# station path would be absent on exactly the deck a gate is pointed at, which
# is this project's ninth-instance defect -- machinery with no caller on the
# path that ships. `station/boot.py` imports `write_places` for that reason.


def place_rows(sector, ring, deck, floor_r_m):
    """Every register place on one deck, with the geometry a walk needs.

    `half_deg` and `half_z_m` are the place's own footprint resolved onto this
    deck's floor radius -- `directory._P`'s `foot` is (across_m, along_m) and
    across is an ARC, so the half-angle is `degrees((across/2) / r)`. Nothing
    here is chosen: the radius comes from `cell_manifest.json`, the footprint
    from the register, and the cluster from `deck.Z_CLUSTER_M`.
    """
    import deck as _D                                            # noqa: PLC0415
    out = []
    for q in _D.places_on(sector, ring, deck):
        across, along = q["footprint"]
        half_deg = math.degrees((across / 2.0) / max(floor_r_m, 1e-9))
        a = math.radians(q["angle_deg"])
        # ON THE FLOOR, not on the axis. `boot.STAND_IN_M` is the convention
        # for "just inside the surface a body stands on"; a point at the bare
        # floor radius is exactly on the triangle and reads as a tie.
        r = floor_r_m - 0.05
        out.append({
            "key": q["key"], "name": q["name"], "module": q.get("module") or "",
            # NOT ROUNDED, and the selftest is why. `round(half_deg, 4)` reads
            # as tidy and makes the footprint round-trip wrong by up to 0.4 mm
            # of arc -- which is nothing to a walk and is a second, lossily
            # stored copy of a number the register already holds exactly. A
            # derived geometric quantity is stored at the precision it was
            # derived at or it is not the same quantity.
            "angle_deg": q["angle_deg"], "half_deg": half_deg,
            "z_m": q["z_m"], "half_z_m": along / 2.0,
            "footprint_m": [across, along],
            "z_cluster": round(q["z_m"] / _D.Z_CLUSTER_M) * _D.Z_CLUSTER_M,
            "floor_xyz": [r * math.cos(a), r * math.sin(a), q["z_m"]],
        })
    return out


def write_places(stem, sector, ring, deck, out_dir):
    """`<stem>_places.json` beside the cells. Returns (path, n) or ("", 0).

    LOUD ON A DECK WITH NO PLACES rather than writing an empty file, because
    an empty sidecar and an absent one read identically to a gate and only one
    of them means "this deck carries nothing the register names".
    """
    import deck as _D                                            # noqa: PLC0415
    import interior as _it                                       # noqa: PLC0415
    schema, profile = _it.load()
    try:
        di = _D.deck_index(schema, profile, sector, int(ring), int(deck))
    except Exception:                                            # noqa: BLE001
        di = int(deck)
    man = os.path.join(ROOT, "station/generated/cell_manifest.json")
    floor_r = 0.0
    label = ""
    if os.path.exists(man):
        with open(man, encoding="utf-8") as f:
            for row in json.load(f).get("deck_table", []):
                if (row.get("sector") == sector
                        and int(row.get("ring_index", -1)) == int(ring)
                        and int(row.get("deck_index", -2)) == di):
                    floor_r = float(row.get("floor_r_m", 0.0))
                    label = str(row.get("label", ""))
                    break
    if floor_r <= 0.0:
        return "", 0
    rows = place_rows(sector, int(ring), int(deck), floor_r)
    if not rows:
        return "", 0
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, stem + "_places.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "written_by": "tools/bake_station.py write_places()",
            "source": {"sector": sector, "ring": int(ring), "deck": int(deck),
                       "deck_index": di, "label": label,
                       "register": "station/directory.py PLACES via "
                                   "deck.places_on"},
            "floor_r_m": floor_r,
            "z_cluster_m": _D.Z_CLUSTER_M,
            "places": rows,
        }, f, indent=1)
    return p, len(rows)


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
        # NOT EVERY .glb IN THIS DIRECTORY IS A DECK, and the exclusion list has
        # to name all four kinds that are not. `_collision` and `column_` were
        # here from the start; `_col` (the spelling `walkable.py` uses, and the
        # one `boot.collision_shell` now derives) and `crowd_lod*` (the shared
        # body library, which lives beside the crowd placement lists it is
        # indexed by) were not, so a bake reported
        #
        #     BAKED 70 of 74 decks ... FAILED blue_0_0_col: no collision mesh
        #     FAILED crowd_lod2/4/8: no collision mesh on disk
        #
        # -- four failures that are not decks and cannot fail. A denominator
        # that counts non-decks makes every coverage number from this tool
        # wrong, and a FAILED row nobody can act on is how a real failure gets
        # skimmed past. `boot.decks()` grew the same filter for the same reason;
        # this is that fix applied to the second site rather than only the first.
        if (stem.endswith(("_collision", "_col")) or stem.startswith("column_")
                or stem.startswith("crowd_lod")):
            continue
        col = os.path.join(SRC, stem + "_collision.glb")
        if not os.path.exists(col):
            out.append((stem, g, None))
            continue
        out.append((stem, g, col))
    return out


def _selftest():
    """Assert the sidecar's geometry, and assert it DISCRIMINATES.

    Three of these four are round trips and the fourth is the one that matters.
    A sidecar every one of whose places "contains" the walk angle would pass
    every arrival test ever written and mean nothing -- so the last check
    asserts that on the deck R5 names, the measured spine angle is inside some
    places and outside others, by the register's own footprints.

    NEGATIVE CONTROL, run and quoted in the session notes: dropping the
    `math.degrees(...)` and storing the half-angle in RADIANS -- the classic
    unit slip, and a plausible one since both are "half the footprint" -- turns
    `bay_elevators` from 1.08 deg into 0.019 and `docking_bays` from 48.75 into
    0.851, and check 4 fails with `obs_dome_2 must contain the measured spine`.

    AND CHECK 4 ALREADY EARNED ITS KEEP BY FAILING ON ITS AUTHOR. It was
    written asserting that `docking_bays` straddles the spine, because 140 m
    long and 360 m of arc reads as "spans the ring". It does not: 360 m of arc
    at r=211.55 is +-48.75 deg about 0, and the spine is at 89.16. The walk R5
    asks for therefore starts on a stretch of spine that is inside NO named
    place and arrives inside exactly one -- which is a fact about this deck
    worth having in an assertion rather than in a paragraph.
    """
    import deck as _D                                            # noqa: PLC0415
    bad, n = [], 0
    r = 211.55                                                   # Blue 1 deck 0
    rows = place_rows("blue", 0, 0, r)
    if not rows:
        return _fail(["no places on blue/0/0 -- the register is empty or "
                      "deck.places_on changed shape"])
    for q in rows:
        n += 1
        across, along = q["footprint_m"]
        # 1. the half-angle inverts back to the footprint's arc width
        back = math.radians(q["half_deg"]) * 2.0 * r
        if abs(back - across) > 1e-9:
            bad.append("%s: half_deg %.4f inverts to %.4f m of arc, footprint "
                       "says %.4f" % (q["key"], q["half_deg"], back, across))
        # 2. the world point is on the floor at the stated angle
        x, y, z = q["floor_xyz"]
        rr = math.hypot(x, y)
        if abs(rr - (r - 0.05)) > 1e-6:
            bad.append("%s: floor_xyz is at r=%.4f, floor is %.2f"
                       % (q["key"], rr, r))
        aa = math.degrees(math.atan2(y, x)) % 360.0
        if min(abs(aa - q["angle_deg"] % 360.0),
               360.0 - abs(aa - q["angle_deg"] % 360.0)) > 1e-6:
            bad.append("%s: floor_xyz is at %.4f deg, row says %.4f"
                       % (q["key"], aa, q["angle_deg"]))
        if abs(z - q["z_m"]) > 1e-9:
            bad.append("%s: floor_xyz z %.3f != z_m %.3f" % (q["key"], z, q["z_m"]))
        # 3. the cluster is the register's own rounding of z
        if abs(q["z_cluster"] - q["z_m"]) > _D.Z_CLUSTER_M / 2.0 + 1e-9:
            bad.append("%s: z_cluster %.1f is more than half a cluster from "
                       "z_m %.1f" % (q["key"], q["z_cluster"], q["z_m"]))
        if abs(q["half_z_m"] * 2.0 - along) > 1e-9:
            bad.append("%s: half_z_m %.3f is not half of %.3f"
                       % (q["key"], q["half_z_m"], along))

    # 4. IT DISCRIMINATES. The axial spine on blue/0/0 is MEASURED by
    # `stream.gd::_axial_runs` at 88.87-89.46 deg (INV-612, quoted in
    # stream.gd's header). By the register's footprints some places straddle it
    # and most do not, and a sidecar that cannot tell those apart is useless
    # for naming where a walk arrived.
    spine = 89.16
    by = {q["key"]: q for q in rows}

    def _has(k):
        q = by[k]
        d = abs(((q["angle_deg"] - spine + 180.0) % 360.0) - 180.0)
        return d <= q["half_deg"]

    checks = n * 5
    for k in ("obs_dome_2",):
        checks += 1
        if k not in by:
            bad.append("%s is not on blue/0/0 any more -- this test's premise "
                       "moved" % k)
        elif not _has(k):
            bad.append("%s must contain the measured spine at %.2f deg "
                       "(it is %.2f +-%.2f)"
                       % (k, spine, by[k]["angle_deg"], by[k]["half_deg"]))
    for k in ("docking_bays", "bay_elevators", "customs_south", "nav_beacon"):
        checks += 1
        if k in by and _has(k):
            bad.append("%s must NOT contain the spine at %.2f deg -- if every "
                       "place straddles it, 'arrived at a place' means nothing "
                       "(it is %.2f +-%.2f)"
                       % (k, spine, by[k]["angle_deg"], by[k]["half_deg"]))

    if bad:
        return _fail(bad)
    on = sorted(k for k in by if _has(k))
    print("bake_station places sidecar: %d places on blue/0/0, %d checks passed"
          % (n, checks))
    print("  the measured spine at %.2f deg lies inside %d of %d place "
          "footprints: %s" % (spine, len(on), n, ", ".join(on) or "(none)"))
    print("  -- so a walk along it arrives inside a named place at exactly "
          "those, and nowhere else on this deck")
    return 0


def _fail(bad):
    print("bake_station selftest FAILED on %d:" % len(bad))
    for b in bad:
        print("   " + b)
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-decks", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--places-only", action="store_true",
                    help="write the register sidecars and bake nothing. "
                         "Seconds, no Godot -- for a tree whose cells are "
                         "already baked but predate the sidecar")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return _selftest()

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

    if a.places_only:
        # THE DECK LIST COMES FROM THE REGISTER HERE, not from the meshes on
        # disk. `decks()` above enumerates what has been EXPORTED, and the
        # point of this mode is to be usable on a tree where the export is
        # partial -- otherwise the sidecar is missing on exactly the decks a
        # coverage question is about.
        import deck as _D                                        # noqa: PLC0415
        import directory as _dr                                  # noqa: PLC0415
        keys = sorted({(q["sector"], q["ring"], q["deck"]) for q in _dr.PLACES})
        if a.sector:
            keys = [k for k in keys if k[0] == a.sector]
        os.makedirs(CELLS, exist_ok=True)
        wrote = 0
        for sec, ring, dk in keys:
            stem = f"{sec}_{ring}_{dk}"
            p, npl = write_places(stem, sec, ring, dk, CELLS)
            if p:
                wrote += 1
                print(f"  {stem:<16} {npl:3d} places -> {os.path.basename(p)}")
            else:
                print(f"  {stem:<16} no sidecar -- no deck_table row or no "
                      f"place on this deck")
        print(f"\n  {wrote} of {len(keys)} register decks have a places "
              f"sidecar in {os.path.relpath(CELLS, ROOT)}")
        return 0 if wrote == len(keys) else 1

    godot = godot_binary()
    if godot is None:
        print("no Godot binary at all. set $GODOT, or run: bash tools/build_godot.sh")
        return 1
    # SAY WHICH ENGINE THIS RAN ON, EVERY RUN. The old not-found branch said
    # "no double-precision Godot binary", which named the only failure this
    # project had ever had rather than the one in front of it -- on Windows the
    # binary was present in $GODOT and the finder simply could not see it, and
    # that message cost three CI runs. Single precision is measured, not
    # assumed: the same deck baked both ways differs by 4.3 mm at the spawn
    # point and 1 mm in content_z, on a station 8 km long.
    import walkable as _W                                      # noqa: PLC0415
    print(f"  engine: {os.path.basename(godot)} "
          f"({'double' if _W.godot_is_double(godot) else 'single'} precision)")
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
        # THE SIDECAR IS WRITTEN WHETHER OR NOT THE BAKE SUCCEEDED, and that is
        # deliberate: it describes the REGISTER, not the mesh, so it is correct
        # even for a deck whose geometry failed -- and a gate pointed at a
        # half-baked deck can then say "the far cluster holds Observation Dome
        # 2 and no cell covers it", which is a much better failure than "z 7960
        # is in no cell".
        pp, pn = write_places(stem, sec, ring, dk, CELLS)
        row["places"] = pn
        man["decks"].append(row)
        print(f"  [{n}/{len(work)}] {stem}: "
              + (f"{len(made)} cells, {mb:.1f} MB, {row['seconds']:.0f} s"
                 if ok else f"FAILED -- {row['why']}"))
        if not ok:
            for ln in row.get("engine", ()):
                print(f"        | {ln[:150]}")
        man["elapsed_s"] = round(time.time() - t0, 1)
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1)

    good = [d for d in man["decks"] if d.get("ok")]
    print(f"\n  BAKED {len(good)} of {len(work)} decks into "
          f"{sum(d['cells'] for d in good):,} cells, "
          f"{sum(d['mb'] for d in good):.0f} MB, in "
          f"{man.get('elapsed_s', 0) / 60:.0f} min")
    return 0 if len(good) == len(work) else 1


if __name__ == "__main__":
    sys.exit(main())
