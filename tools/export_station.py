#!/usr/bin/env python3
"""BUILD THE WHOLE STATION — every deck, every cluster, joined, as glTF.

Not one deck. Not one cluster. **Every deck the register carries**, assembled
with its axial spine, its junction doors and its sector's transit column, and
written as `.obj` + `.glb` for `godot/scripts/stream.gd` to bake into cells.

WHY IT DID NOT EXIST. Every build path in this project takes a sector, a ring
and a deck and makes one of them: `deck.build_deck` one cluster, `walkable.py`
one deck for one walk test, `export_scene.build_deck_shot` one camera. That is
correct for a gate and it is why the station has never once been built. The
count that matters -- how many of the station's decks have ever been assembled
at the same time -- was zero until this file.

WHAT IT WRITES, per deck, into `station/generated/scene/station/`:

    <sector>_<ring>_<deck>.obj    the assembled render mesh, groups preserved
    <sector>_<ring>_<deck>.glb    the same, for Godot
    station_manifest.json         what was built, what failed, and why

and per (sector, ring), the transit column that joins its decks:

    column_<sector>_<ring>.obj / .glb

EVERY DECK GETS THE SAME THREE ARGUMENTS, and they are the session's whole
finding in one call:

    join=True          the axial spine, so a deck's clusters are one place
    must_cover=<ang>   so every cluster's corridor REACHES that spine
    column             so the deck's ring is joined to the ones above and below

`must_cover` is `routes.transit_angle` for the sector -- derived, one angle per
sector, the angle lying inside the most of its cluster arcs.

IT IS HOURS OF MACHINE TIME AND IT SAYS SO. A single cluster of `blue/0/0` takes
about a minute to assemble; the register carries 71 decks over 96 clusters. Run
it with `--sector` to do one sector, or `--dry-run` to see the work list and its
cost without paying it. Progress is printed per deck, and the manifest is
rewritten after every deck so a run that is killed half way still leaves an
accurate record of what exists.

Run: python3 tools/export_station.py --dry-run
     python3 tools/export_station.py --sector blue
     python3 tools/export_station.py
"""
import argparse
import collections
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import deck as D                                                # noqa: E402
import interior as it                                           # noqa: E402
import routes as RT                                             # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/station")


def work_list():
    """Every deck that carries a location, and every ring that needs a column.

    FROM `routes.clusters`, not from a second walk of the register -- the
    circulation gate and the build have to agree about what the station is made
    of, and two enumerations of that is one too many.
    """
    nodes = RT.clusters()
    decks = collections.defaultdict(list)
    for k in nodes:
        decks[k[:3]].append(k[3])
    rings = sorted({k[:2] for k in nodes})
    ang = {s: RT.transit_angle(s, nodes)
           for s in sorted({k[0] for k in nodes})}
    return ({k: sorted(v) for k, v in decks.items()}, rings, ang, nodes)


def _write(stem, V, T, G):
    obj = os.path.join(OUT, stem + ".obj")
    glb = os.path.join(OUT, stem + ".glb")
    it.write_grouped_obj(obj, V, T, G)
    import export_gltf                                          # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj, "--out", glb]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    return os.path.getsize(obj), os.path.getsize(glb)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="", help="one sector only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-decks", type=int, default=0)
    ap.add_argument("--skip-existing", action="store_true")
    a = ap.parse_args(argv)

    decks, rings, ang, _nodes = work_list()
    if a.sector:
        decks = {k: v for k, v in decks.items() if k[0] == a.sector}
        rings = [r for r in rings if r[0] == a.sector]
    order = sorted(decks)
    if a.max_decks:
        order = order[:a.max_decks]

    print(f"\nTHE WHOLE STATION\n")
    print(f"  {len(order)} decks over {len(rings)} (sector, ring) pairs, "
          f"{sum(len(v) for v in decks.values())} clusters")
    print(f"  transit angles: "
          + ", ".join(f"{s} {v:.0f}" for s, v in sorted(ang.items())))
    if a.dry_run:
        for k in order:
            print(f"     {k[0]}/{k[1]}/{k[2]}  {len(decks[k])} cluster(s) at "
                  + ", ".join(f"{z:.0f}" for z in decks[k]))
        print(f"\n  dry run -- nothing built. A cluster is about a minute, so "
              f"this is roughly {sum(len(v) for v in decks.values())} minutes.")
        return 0

    os.makedirs(OUT, exist_ok=True)
    schema, profile = it.load()
    man = {"decks": [], "columns": [], "started": time.time()}
    mpath = os.path.join(OUT, "station_manifest.json")

    def flush():
        man["elapsed_s"] = round(time.time() - man["started"], 1)
        with open(mpath, "w") as f:
            json.dump(man, f, indent=1)

    for n, k in enumerate(order, 1):
        sec, ring, dk = k
        stem = f"{sec}_{ring}_{dk}"
        t0 = time.time()
        if a.skip_existing and os.path.exists(os.path.join(OUT, stem + ".glb")):
            print(f"  [{n}/{len(order)}] {stem} -- already built, skipped")
            continue
        try:
            V, T, G, st = D.build_deck_clusters(
                schema, profile, sec, ring, dk, join=True,
                must_cover=ang[sec])
            ob, gb = _write(stem, V, T, G)
            joins = [j for j in st.get("joins", ()) if j.get("built")]
            row = {"key": stem, "clusters": len(st["clusters"]),
                   "rooms": st.get("rooms", 0), "tris": len(T),
                   "groups": len(G), "joins": len(joins),
                   "join_m": round(sum(j.get("length_m", 0) for j in joins), 1),
                   "obj_mb": round(ob / 1e6, 2), "glb_mb": round(gb / 1e6, 2),
                   "seconds": round(time.time() - t0, 1), "ok": True}
            print(f"  [{n}/{len(order)}] {stem}: {len(st['clusters'])} cluster(s), "
                  f"{st.get('rooms', 0)} rooms, {len(T):,} tri, "
                  f"{len(joins)} join(s) {row['join_m']:.0f} m, "
                  f"{row['glb_mb']:.1f} MB, {row['seconds']:.0f} s")
        except Exception as e:                                  # noqa: BLE001
            row = {"key": stem, "ok": False, "why": f"{type(e).__name__}: {e}",
                   "seconds": round(time.time() - t0, 1)}
            print(f"  [{n}/{len(order)}] {stem}: FAILED -- {row['why'][:120]}")
        man["decks"].append(row)
        flush()

    # --- the transit columns -------------------------------------------------
    import spoke_way as SW                                      # noqa: PLC0415
    by_sector = collections.defaultdict(set)
    for s, r in rings:
        by_sector[s].add(r)
    for sec, rs in sorted(by_sector.items()):
        stem = f"column_{sec}"
        t0 = time.time()
        z = min(z for k, v in decks.items() if k[0] == sec for z in v)
        try:
            V, T, G, st = SW.spoke_way(schema, profile, sec, sorted(rs),
                                       ang[sec], z)
            ob, gb = _write(stem, V, T, G)
            row = {"key": stem, "rings": st["rings_served"],
                   "landings": st["landings"], "rise_m": st["rise_m"],
                   "tris": len(T), "collision_tris": st["collision_tris"],
                   "glb_mb": round(gb / 1e6, 2),
                   "seconds": round(time.time() - t0, 1), "ok": True}
            print(f"  column {sec}: rings {st['rings_served']}, "
                  f"{st['landings']} landings over {st['rise_m']:.1f} m, "
                  f"{len(T):,} tri, {row['seconds']:.0f} s")
        except Exception as e:                                  # noqa: BLE001
            row = {"key": stem, "ok": False, "why": f"{type(e).__name__}: {e}",
                   "seconds": round(time.time() - t0, 1)}
            print(f"  column {sec}: FAILED -- {row['why'][:120]}")
        man["columns"].append(row)
        flush()

    good = [d for d in man["decks"] if d.get("ok")]
    print(f"\n  BUILT {len(good)} of {len(order)} decks, "
          f"{sum(d['tris'] for d in good):,} triangles, "
          f"{sum(d['glb_mb'] for d in good):.0f} MB, in "
          f"{man['elapsed_s'] / 60:.0f} min")
    bad = [d for d in man["decks"] + man["columns"] if not d.get("ok")]
    for d in bad:
        print(f"     FAILED {d['key']}: {d['why'][:140]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
