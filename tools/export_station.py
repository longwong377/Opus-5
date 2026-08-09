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
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import deck as D                                                # noqa: E402
import interior as it                                           # noqa: E402
import routes as RT                                             # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/station")

# The habitat drum's address, owned by `tools/export_drum.py` (STEM green_1_0).
# Kept as three names rather than a literal so the two files can be grepped
# together when the drum moves.
DRUM_SECTOR, DRUM_RING, DRUM_DECK = "green", 1, 0


def work_list():
    """Every deck that carries a location, and every ring that needs a column.

    FROM `routes.clusters`, not from a second walk of the register -- the
    circulation gate and the build have to agree about what the station is made
    of, and two enumerations of that is one too many.
    """
    nodes = RT.clusters()
    decks = collections.defaultdict(list)
    for k in nodes:
        # THE DRUM IS NOT OURS TO BUILD, AND DECLINING IT WAS COSTING A RED RUN
        # EVERY TIME. `station/deck.py` raises for green ring 1 -- "not a ring
        # deck: the habitat drum ... an open 8 km barrel, no ring corridor" --
        # and that refusal is CORRECT: the drum is not a ring of rooms off a
        # corridor. `tools/export_drum.py` builds it instead, writes the same
        # five files under the same `green_1_0` stem, and says so in its own
        # docstring, quoting this very traceback.
        #
        # But this function enumerates from `routes.clusters()`, which is every
        # deck that CARRIES A LOCATION -- and the drum carries twelve of them,
        # the Garden among them. So the drum arrived here, raised, and left the
        # run at "BUILT 70 of 71 decks" with exit 1 while every artefact it
        # needed was already on disk from export_drum. Under the old bash chain
        # that non-zero exit was recorded and stepped over, so the build went on
        # to succeed and nobody read the line. It only became visible when the
        # new driver started stopping at the first failure.
        #
        # Skipping it here is the honest version of what the pipeline already
        # did, and it keeps export_drum's rule intact: nothing downstream needs
        # to know the drum was built by a different route.
        if k[:3] == (DRUM_SECTOR, DRUM_RING, DRUM_DECK):
            continue
        decks[k[:3]].append(k[3])

    # SHELL B -- THE 180 DECKS THAT CARRY NO NAMED LOCATION AND ALL THE PEOPLE.
    # `routes.clusters()` is "every deck that carries a location", which is 71
    # of the station's 251. That enumeration is right for Shell A and it is the
    # reason 175 decks had no geometry of any kind: nobody lives in a landmark.
    # `station/shell_b.py` owns the residential belts -- 101 decks, 222,580
    # dwellings, 4.64 M m2 -- and a deck of its own has NO cluster z, which is
    # exactly how the build loop below tells the two apart.
    import shell_b as SHB                                       # noqa: PLC0415
    _schema, _profile = it.load()
    for row in SHB.station_plan(_schema, _profile):
        key = (row["sector"], row["ring"], row["deck"])
        if key == (DRUM_SECTOR, DRUM_RING, DRUM_DECK):
            continue                      # the drum is export_drum's, as above
        decks.setdefault(key, [])         # empty list == "this one is Shell B"

    rings = sorted({k[:2] for k in nodes})
    ang = {s: RT.transit_angle(s, nodes)
           for s in sorted({k[0] for k in nodes})}
    return ({k: sorted(v) for k, v in decks.items()}, rings, ang, nodes)


def _write(stem, V, T, G):
    """OBJ + GLB, and the group format is not a detail.

    `deck.write_obj` TAKES SPANS -- `(name, lo, hi)` -- and
    `interior.write_grouped_obj` takes a PER-TRIANGLE list of names. Two writers
    with near-identical names and incompatible arguments; `build_deck_clusters`
    returns spans. The first run of this file called the wrong one and threw
    away all 71 assembled decks at the write, reporting only
    "IndexError: list index out of range".

    So the write is ASSERTED, not assumed. A build that takes minutes and is
    discarded by its own output stage is the most expensive kind of silent
    failure there is.
    """
    obj = os.path.join(OUT, stem + ".obj")
    glb = os.path.join(OUT, stem + ".glb")
    D.write_obj(obj, V, T, G)
    with open(obj, encoding="utf-8") as f:
        body = f.read()
    nf = body.count("\nf ")
    ng = body.count("\ng ")
    if nf != len(T):
        raise AssertionError(f"{stem}: wrote {nf} faces for {len(T)} triangles")
    if ng < 1:
        raise AssertionError(f"{stem}: wrote no groups for {len(G)} spans")
    import export_gltf                                          # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj, "--out", glb]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    if not os.path.exists(glb) or os.path.getsize(glb) < 1024:
        raise AssertionError(f"{stem}: glb is missing or empty")
    # THE OBJ IS AN INTERMEDIATE AND THE STATION IS BIG. blue/0/0 alone is
    # 161 MB of OBJ and 309 MB of glTF; keeping both for 71 decks is a disk
    # allowance this container does not have. The glb is the artefact.
    ob = os.path.getsize(obj)
    os.remove(obj)
    return ob, os.path.getsize(glb)


def _sidecars(stem, V, T, G, st):
    """The JSON `walk.gd` reads beside a deck: interactables, cast, crowd.

    SHAPES BORROWED FROM `station/walkable.py`, which is the only thing that has
    ever written them, rather than invented here -- two descriptions of one file
    format is how this project has already lost a build today.
    """
    import walkable as W                                        # noqa: PLC0415
    out = {}
    # THE z-PREFIX HIDES EVERY INTERACTABLE. `build_deck_clusters` names a
    # cluster's spans `z7120__docking_bays__prop_bay_control_booth` so two
    # clusters' identically-named corridor spans do not merge into one material
    # group -- and `interact.sidecar` resolves declared interactables by the
    # name the generator emits, which is the tail. Handed the prefixed names it
    # returns NOTHING, and the first run of this sidecar wrote 0 interactables
    # on a deck with 5 rooms in it.
    #
    # Stripped for the interact pass only, and the ORIGINAL span order is kept
    # so `interact.resolve`'s triangle-count tie-break still sees the same
    # spans -- that tie-break is what stops "operate the console" pointing at
    # `cc_console_leg`.
    def _tail(nm):
        parts = nm.split("__")
        return "__".join(parts[1:]) if parts[0][:1] == "z" and \
            parts[0][1:].isdigit() and len(parts) > 1 else nm

    G2 = [(_tail(nm), a, b) for nm, a, b in G]
    rows = W.interact_rows(V, T, G2)
    for name, payload in (("interact", rows),
                          ("actors", st.get("actors", [])),
                          ("crowd", st.get("crowd", []))):
        p = os.path.join(OUT, f"{stem}_{name}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        out[name] = len(payload)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="", help="one sector only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-decks", type=int, default=0)
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--legacy-column-z", action="store_true",
                    help="place each column at min(z_cluster), the rule "
                         "replaced in session 4t. The negative control for "
                         "tools/column_site.py --gate; it puts blue's column "
                         "80 m from any blue floor")
    a = ap.parse_args(argv)

    decks, rings, ang, nodes = work_list()
    import shell_b as SHB                                       # noqa: PLC0415
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
        # AND WHERE THE COLUMNS WOULD GO, which is the one decision in this
        # file that used to be invisible until hours of build had been paid
        # for. It costs a schema load and no geometry.
        import column_site as CS                                # noqa: PLC0415
        schema, profile = it.load()
        by_sector = collections.defaultdict(set)
        for s, r in rings:
            by_sector[s].add(r)
        print("")
        for sec, rs in sorted(by_sector.items()):
            st = CS.site(schema, profile, nodes, sec, rings=sorted(rs),
                         rule="legacy" if a.legacy_column_z else "floor")
            print(f"     column_{sec:<7} {st['angle_deg']:7.2f} deg, "
                  f"z={st['z_m']:7.0f}, {st['joined']} of {st['landings']} "
                  f"landings on a deck  ({st['source']})")
        print(f"\n  dry run -- nothing built. A cluster is about a minute, so "
              f"this is roughly {sum(len(v) for v in decks.values())} minutes.")
        return 0

    os.makedirs(OUT, exist_ok=True)
    schema, profile = it.load()
    # THE MANIFEST ACCUMULATES. A run with `--sector` used to overwrite the
    # whole-station record with nine rows, so the file said the station was
    # nine decks. It is a record of what EXISTS, not of what this invocation
    # did; rows are keyed and replaced.
    mpath = os.path.join(OUT, "station_manifest.json")
    man = {"decks": [], "columns": [], "started": time.time()}
    if os.path.exists(mpath):
        try:
            with open(mpath, encoding="utf-8") as f:
                old = json.load(f)
            man["decks"] = list(old.get("decks", ()))
            man["columns"] = list(old.get("columns", ()))
        except (OSError, ValueError):
            pass

    def _put(bucket, row):
        keep = [r for r in man[bucket] if r.get("key") != row.get("key")]
        keep.append(row)
        man[bucket] = keep

    def flush():
        man["elapsed_s"] = round(time.time() - man["started"], 1)
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1)

    for n, k in enumerate(order, 1):
        sec, ring, dk = k
        stem = f"{sec}_{ring}_{dk}"
        t0 = time.time()
        if a.skip_existing and os.path.exists(os.path.join(OUT, stem + ".glb")):
            print(f"  [{n}/{len(order)}] {stem} -- already built, skipped")
            continue
        try:
            # WHICH SHELL IS THIS DECK? A Shell A deck came from
            # `routes.clusters()` and carries its cluster z values; a Shell B
            # deck was seeded with an empty list by `work_list` and has none.
            # One branch, decided by the data, so neither builder can be handed
            # the other's deck -- which is the mistake that cost run 2 when the
            # drum reached a ring-deck builder.
            if not decks[k]:
                V, T, G, st = SHB.build_deck(schema, profile, sec, ring, dk)
            else:
                V, T, G, st = D.build_deck_clusters(
                    schema, profile, sec, ring, dk, join=True,
                    must_cover=ang[sec])
            ob, gb = _write(stem, V, T, G)
            # AND ITS COLLISION, WHICH THE FIRST 70-DECK BUILD DID NOT WRITE.
            # 2.3 GB of render mesh with nothing to stand on is a station a body
            # walks through. The shell is ~0.5% of the render and is what makes
            # the difference between geometry and a place.
            if not decks[k]:
                cv, ct, cmeta = SHB.deck_collision(
                    schema, profile, sec, ring, dk)
            else:
                cv, ct, cmeta = D.build_collision_clusters(
                    schema, profile, sec, ring, dk, join=True,
                    must_cover=ang[sec])
            # THE SPANS, NOT ONE GROUP. Writing the shell as a single
            # `("collision", 0, len(ct))` made `build_collision`'s
            # `doorpanel_<place>` spans unaddressable and WELDED EVERY ROOM ON
            # ALL 70 SHIPPED DECKS SHUT -- a body could walk the station and
            # enter nothing. Found by the L1 agent when a resident could not
            # leave their own quarters; no gate caught it because no gate had
            # ever walked on this artefact.
            cgroups = cmeta.get("groups") or [("collision", 0, len(ct))]
            _ob, cgb = _write(stem + "_collision", cv, ct, cgroups)
            _doors = sum(1 for n, _a, _b in cgroups if "doorpanel" in n)
            # AND THE SIDECARS, WITHOUT WHICH A CELL CANNOT BE WIRED AT ALL.
            # `walk.gd` recovers the cast, the crowd and the interactables from
            # JSON beside the mesh, because a body baked into merged geometry
            # cannot tell the engine who it is or which way it faces, and an
            # interactable's box cannot be recovered from a triangle soup. This
            # file wrote none of them, so **not one of the 940 streaming cells
            # baked from it could be wired** -- the streamed station was a shell
            # by construction and the wiring work had nothing to act on.
            side = _sidecars(stem, V, T, G, st)
            joins = [j for j in st.get("joins", ()) if j.get("built")]
            # A SHELL B DECK HAS NO CLUSTERS AND THIS LINE ASSUMED IT DID.
            # `len(st["clusters"])` is an unconditional subscript, and
            # `shell_b.build_deck` returns blocks and slots rather than the
            # z-clusters a landmark deck is assembled from -- so EVERY Shell B
            # deck raised KeyError here, in the same commit that added the
            # branch six lines above. Run 9's step 1 lost 40 red decks that way,
            # exactly the 40 `work_list()` marks Shell B.
            #
            # The geometry was never at risk: render, collision and sidecars are
            # all written before this point, which is why the bake still found
            # 1,576 cells. What was lost is the manifest row and the exit code.
            #
            # Reported per shell rather than coerced: a Shell B deck says how
            # many residential blocks it carries, because pushing an empty
            # `clusters: []` into it would put a Shell A concept inside Shell B.
            row = {"key": stem, "clusters": len(st.get("clusters", ())),
                   "blocks": st.get("blocks", 0),
                   "units": st.get("units", 0),
                   "shell": "B" if not decks[k] else "A",
                   "rooms": st.get("rooms", 0), "tris": len(T),
                   "groups": len(G), "joins": len(joins),
                   "join_m": round(sum(j.get("length_m", 0) for j in joins), 1),
                   "collision_tris": len(ct),
                   "interactables": side["interact"],
                   "actors": side["actors"], "crowd": side["crowd"],
                   "collision_joins": len(cmeta["joins"]),
                   "collision_mb": round(cgb / 1e6, 2),
                   "obj_mb": round(ob / 1e6, 2), "glb_mb": round(gb / 1e6, 2),
                   "seconds": round(time.time() - t0, 1), "ok": True}
            print(f"  [{n}/{len(order)}] {stem}: {len(st['clusters'])} cluster(s), "
                  f"{st.get('rooms', 0)} rooms, {len(T):,} tri, "
                  f"{len(joins)} join(s) {row['join_m']:.0f} m, "
                  f"{row['glb_mb']:.1f} MB + {len(ct):,} collision tri "
                  f"({_doors} door panels), "
                  f"{side['actors']} actors / {side['crowd']} crowd / "
                  f"{side['interact']} interactables, {row['seconds']:.0f} s")
        except Exception as e:                                  # noqa: BLE001
            # THE WHOLE TRACEBACK, NOT THE MESSAGE. The first run of this file
            # recorded "IndexError: list index out of range" 142 times, which
            # names neither the file nor the line and cost a diagnosis pass. A
            # manifest is a record of what happened; a bare exception type is a
            # record that something did.
            tb = traceback.format_exc()
            where = [l.strip() for l in tb.splitlines()
                     if l.strip().startswith("File ")]
            row = {"key": stem, "ok": False, "why": f"{type(e).__name__}: {e}",
                   "at": where[-1] if where else "", "traceback": tb,
                   "seconds": round(time.time() - t0, 1)}
            print(f"  [{n}/{len(order)}] {stem}: FAILED -- {row['why'][:100]}"
                  f"\n        {row['at']}")
        _put("decks", row)
        flush()

    # --- the transit columns -------------------------------------------------
    # WHERE A COLUMN STANDS IS NO LONGER DECIDED HERE, and that is the whole
    # of session 4t's fix. This file used to write
    #
    #     z = min(z for k, v in decks.items() if k[0] == sec for z in v)
    #
    # and hand `(ang[sec], z)` to `spoke_way` -- an angle derived from the
    # cluster arcs and a z that is the sector's lowest cluster, TWO
    # INDEPENDENTLY COMPUTED NUMBERS with nothing asserting the sector has any
    # floor at that PAIR. Measured against the 817 baked deck cells, blue's
    # column stood 80.1 m in z from the nearest blue geometry and joined 0 of
    # its 18 landings; yellow joined 0 of 24. Both halves were right about
    # their own question and nobody owned the conjunction.
    #
    # `tools/column_site.py` owns it now: the angle is still
    # `routes.transit_angle` (canon -- every deck spine is built to reach it,
    # which is what `must_cover=` above does), and only the z moves, chosen as
    # the candidate that puts the most landings on a deck a player can stand
    # on. `--legacy-column-z` restores the old expression so the gate has a
    # control that fires.
    import spoke_way as SW                                      # noqa: PLC0415
    import column_site as CS                                    # noqa: PLC0415
    by_sector = collections.defaultdict(set)
    for s, r in rings:
        by_sector[s].add(r)
    for sec, rs in sorted(by_sector.items()):
        stem = f"column_{sec}"
        t0 = time.time()
        site = CS.site(schema, profile, nodes, sec, rings=sorted(rs),
                       rule="legacy" if a.legacy_column_z else "floor")
        z = site["z_m"]
        try:
            V, T, G, st = SW.spoke_way(schema, profile, sec, sorted(rs),
                                       ang[sec], z)
            ob, gb = _write(stem, V, T, G)
            row = {"key": stem, "rings": st["rings_served"],
                   "landings": st["landings"], "rise_m": st["rise_m"],
                   "tris": len(T), "collision_tris": st["collision_tris"],
                   "glb_mb": round(gb / 1e6, 2),
                   # THE PLACEMENT AND ITS EVIDENCE, in the manifest, because a
                   # column that joins nothing is invisible in a triangle count
                   # and this is the only record of why it stands where it does.
                   "angle_deg": site["angle_deg"], "z_m": z,
                   "z_source": site["source"], "z_why": site["why"],
                   "landings_on_a_deck": site["joined"],
                   "dead_doors_unbuilt": site["dead_unbuilt"],
                   "dead_doors_built": site["dead_built"],
                   "seconds": round(time.time() - t0, 1), "ok": True}
            print(f"  column {sec}: rings {st['rings_served']}, "
                  f"{st['landings']} landings over {st['rise_m']:.1f} m, "
                  f"{len(T):,} tri, {row['seconds']:.0f} s")
            print(f"     at {site['angle_deg']:.2f} deg, z={z:.0f} -- "
                  f"{site['joined']} of {site['landings']} landings meet a "
                  f"baked deck cell ({site['source']})")
        except Exception as e:                                  # noqa: BLE001
            tb = traceback.format_exc()
            where = [l.strip() for l in tb.splitlines()
                     if l.strip().startswith("File ")]
            row = {"key": stem, "ok": False, "why": f"{type(e).__name__}: {e}",
                   "at": where[-1] if where else "", "traceback": tb,
                   "seconds": round(time.time() - t0, 1)}
            print(f"  column {sec}: FAILED -- {row['why'][:100]}"
                  f"\n        {row['at']}")
        _put("columns", row)
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
