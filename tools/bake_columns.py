#!/usr/bin/env python3
"""BAKE THE FIVE TRANSIT COLUMNS INTO STREAMING CELLS.

`tools/export_station.py` writes seventy deck meshes AND five transit columns:

    station/generated/scene/station/column_{blue,green,grey,red,yellow}.glb

`tools/bake_station.py` bakes the seventy and **explicitly skips the five** --
`stem.startswith("column_")` is in its exclusion list. So no cell set names
them, `tools/merge_cells.py` (which globs `*_cells.json`) cannot see them, and
the streamer never loads one. Finished machinery with no caller, for the tenth
time in this project; this file is the caller.

    python3 tools/bake_columns.py                 # all five, skip what is done
    python3 tools/bake_columns.py --sector blue --force
    python3 tools/bake_columns.py --verify        # measure, bake nothing
    python3 tools/bake_columns.py --check-mesh    # seconds: is the mesh on
                                                  # disk where its manifest
                                                  # says, and still where it
                                                  # would be built today?
    python3 tools/bake_columns.py --selftest

===========================================================================
FIVE THINGS ABOUT A COLUMN THAT ARE NOT TRUE OF A DECK
===========================================================================

**1. A COLUMN RISES THROUGH RADIUS, NOT THROUGH Z.** This is the fact the whole
file is shaped by and it is easy to get backwards, because "column" and
"landings over 121.6 m of rise" both read as vertical. Measured off the shipped
GLBs, each column is a 3.42 m slab in z at a single angle, spanning tens or
hundreds of metres of RADIUS:

    blue    r 130.5-198.0 ( 67.5 m)  z 6878.4-6881.8  at 140.0 deg
    green   r 278.5-311.2 ( 32.7 m)  z 3998.4-4001.8  at 100.0 deg
    grey    r 388.7-471.8 ( 83.1 m)  z 3598.4-3601.8  at 150.0 deg
    red     r  51.7-267.0 (215.4 m)  z 6598.4-6601.8  at  90.0 deg
    yellow  r  30.5-156.0 (125.5 m)  z  158.4- 161.8  at   0.0 deg

`spoke_way.spoke_way` says so in one line -- `"rise_m": stack[0]["floor_r_m"] -
stack[-1]["floor_r_m"]` -- and `ring_stack`'s docstring says why: *"down is
outward on a spun ring, so the largest floor radius is the lowest landing"*. A
lift on a spun station climbs inward.

**2. IT MUST THEREFORE NOT BE SPLIT ALONG ITS RISE, and that is a measurement
rather than a preference.** The obvious plan -- cut the shaft into radial bands
so each is a small cell -- is wrong, because `lift.lift_collision` builds the
bore as four `_rect` quads running the WHOLE shaft:

    six collision triangles of blue's 172 span 67.1 m of radius,
    which is the column's entire 67.1 m rise

`stream.gd::bake()` assigns a triangle whole to the cell its centroid falls in
and never cuts one -- that is the property that makes the bake lossless. So any
split along the rise puts all six wall quads in ONE band and leaves every other
band an open shaft: no wall, no overhead, no pit floor. A body would walk out of
the side of the lift into vacuum. **The budget does not ask for the split
anyway** -- the heaviest column is red at 43,716 triangles against a 60,000
`cell_tris` budget, so every column fits in one cell with room to spare.

**3. IT IS NOT AN ARC CELL, SO IT CARRIES NO `arc`.** `stream.gd::distance_to`
picks its metric off the row: *"Both forms are in the manifest and this picks
whichever the cell has"* -- `arc` when present, the world AABB otherwise. An arc
record is right for a ring corridor, where the distance that decides residency
is arc length at a fixed radius; it is exactly wrong for a shaft, because the
arc form has **no radial term at all** and would call a body on Blue 4 at r=44
zero metres from a shaft that stops at r=130. A column's AABB is tight -- the
shaft is 1.5 deg wide and 3.4 m thick -- so the AABB branch is both correct and
cheap here. What `bake()` wrote is kept as `arc_deck_grid` for provenance and is
read by nothing.

Both consumers already handle this and say so: `stream.gd::distance_to` falls
through to the AABB, and `station/boot.py::start_cell` does the same
(*"and falls back to the world AABB when a cell has no arc"*). `walk.gd`'s
`--visit-cell` refuses with `"cell %d is not an arc cell"`, which is the right
answer -- you cannot walk a lift shaft round a ring.

**4. NOTHING EXPORTS ITS COLLISION.** `export_station.py` calls `spoke_way`,
receives `st["collision"] = (verts, tris, meta)` from `lift.lift_collision`
-- and writes only the render half. There is no `column_*_collision.glb` on
disk and never has been. `bake()` returns 2 without one, so this file
regenerates it from the same call the export makes and writes it to a work
directory. **The regeneration is checked against the shipped mesh, not
assumed**: if the render half we rebuild does not match the triangle count and
bounds of `column_<sector>.glb` on disk, the schema has moved since the export
and the collision we would bake describes a different shaft. That refuses
rather than bakes a mismatched pair.

===========================================================================
**5. THE PLACEMENT COMES FROM THE MANIFEST, NOT FROM A SECOND DERIVATION** --
and this is the fix for the three columns that refused to bake in Windows
build run 9.
===========================================================================

`column_site.site(rule="floor")` IS NOT A PURE FUNCTION OF THE SCHEMA. It picks
the candidate z whose landing stack meets the most **baked deck cells on disk**,
and it says so in its own header, including the chicken-and-egg: with no cells
it falls back to `routes.column_z` and records `source: "routes.column_z (no
baked deck cells on disk)"`.

`tools/build_world.py`'s STEPS put `export_station.py` at **step 1** and
`bake_station.py` -- the thing that creates those cells -- at **step 3**. On a
fresh checkout `station/generated/scene/station/cells/` does not exist, so:

    step 1  export_station  ->  no cells    ->  column_site falls back
                                                yellow z=160, blue 7120, green 4000
    step 3  bake_station    ->  126 deck cell sets appear
    step 5  bake_columns    ->  cells now exist  ->  column_site MEASURES
                                                yellow z=240, blue 7520, green 4720

Same function, same arguments, two answers, because the world changed between
them. This file then rebuilt the shaft at the *measured* z and compared it to a
GLB built at the *fallback* z. Grey and red agree under both rules and baked;
blue and green refused on triangle count; yellow's stack is congruent under a
pure shift, so it refused on bounds -- `sits 80.000 m away` -- which is what
guard 4 exists for and it was right.

**So the placement is read from `station_manifest.json`**, the row
`export_station.py` writes in the same loop iteration as the mesh. That is the
only description on disk of what the shipped GLB actually IS, and rebuilding a
shaft from anything else is a second opinion about a file that already exists.
`--site-from=derive` restores the old behaviour and is the negative control.

**The disagreement is not swallowed, it is reported.** When the manifest z and
the z `column_site` derives today differ, the shipped mesh is at a provisional
placement: the bake still runs (the collision matches the render, which is this
file's actual job) and `main()` names the sector, both z values, and exits 1.
Producing the artefact and reporting the defect are different things and run 5
of the Windows build was lost to conflating them.

Fixing it at the source is one line in a file this one does not own: either
export the columns *after* `bake_station.py`, or re-run
`tools/export_station.py` once the cells exist.

===========================================================================
THE BAKE SUCCEEDING AND THE COLUMNS CONNECTING ARE TWO DIFFERENT CLAIMS
===========================================================================

They are kept apart on purpose, because this project's signature failure is a
green number standing in for a thing that does not work. `main()` reports on
whether five cell sets exist with their `.scn` files beside them. `--verify`
reports on something else entirely: whether a column's landings are anywhere
near a deck a player can walk on.

They do not agree, and the disagreement is the finding. `export_station.py`
places a column at `(RT.transit_angle(sector), min(z_cluster))` -- an angle and
a z chosen by two independent computations, with nothing asserting that the
sector has any floor at that PAIR. Measured against the 816 baked deck cells:

    grey     0.0 m   lands on grey_0_5 / grey_0_60          CONNECTS
    red      0.0 m   lands on red_1_0 / red_1_3 / red_3_4   CONNECTS
    yellow  18.0 m   nearest deck cell yellow_0_0_c00z03    stands clear
    blue    78.2 m   nearest deck cell blue_0_0_c06z02      stands clear
    green  108.0 m   nearest deck cell green_0_2_c04z02     stands clear

Blue is the clearest case: at 140 deg the nearest blue geometry in z is 79.8 m
away at z=6960, and the only blue geometry at the column's own z=6880 is the
axial spine, at 2-358 deg. Green has NO geometry at z=4000 in any sector.

So three of five columns stream correctly and join nothing. That is a defect in
where `export_station.py` puts them, not in this bake, and it is not fixable
from here -- that file is owned elsewhere. It is measured, named and exit-coded
instead: `--verify` returns 1 while any column has no landing near a deck.
"""

import argparse
import collections
import glob
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

SRC = os.path.join(ROOT, "station/generated/scene/station")
CELLS = os.path.join(SRC, "cells")
CELL_MANIFEST = os.path.join(ROOT, "station/generated/cell_manifest.json")
# WHAT `export_station.py` SAYS IT BUILT. The only record on disk of the
# (angle, z) each `column_<sector>.glb` was actually generated at, written in
# the same loop iteration as the mesh. See `manifest_sites`.
STATION_MANIFEST = os.path.join(SRC, "station_manifest.json")

SECTORS = ("blue", "green", "grey", "red", "yellow")

# How near a landing has to be to a deck cell before we will call it joined.
# A doorway's worth: `interior`'s portals are ~2.2 m wide and a cell AABB is
# the bounding box of its CONTENT, so a landing that opens onto a deck is at
# most a few metres from that deck's box. Stated so a reader can move it and
# see the verdict move.
NEAR_M = 5.0

# How far the rebuilt shaft may sit from the shipped one before the bake
# refuses. Not a tuning knob: both come from the SAME `spoke_way` call with the
# same arguments, so in agreement they are bit-identical and any non-zero
# offset is a real disagreement about where the shaft is. A millimetre is
# float noise; 80 m is the defect this exists to catch.
BOUNDS_TOL_M = 0.001



# ===========================================================================
# WHAT THERE IS TO BAKE
# ===========================================================================

def _work_list():
    """(decks, rings, angles) from `routes.clusters`, as `export_station` does.

    THE SAME ENUMERATION THE EXPORT USED, not a second walk of the register --
    a column baked for a sector the export did not build is a cell set pointing
    at a mesh that is not there, and a column the export built and this missed
    is the defect this file exists to close, arriving by the back door.
    """
    import routes as RT                                          # noqa: PLC0415
    nodes = RT.clusters()
    decks = collections.defaultdict(list)
    for k in nodes:
        decks[k[:3]].append(k[3])
    rings = sorted({k[:2] for k in nodes})
    ang = {s: RT.transit_angle(s, nodes)
           for s in sorted({k[0] for k in nodes})}
    return decks, rings, ang


def manifest_sites(path=STATION_MANIFEST):
    """-> {sector: row} from `station_manifest.json`'s `columns` list.

    THE RECORD OF WHAT WAS BUILT, WHICH IS NOT THE SAME QUESTION AS WHERE IT
    SHOULD GO. `export_station.py` writes this row in the same loop iteration
    that writes `column_<sector>.glb`, carrying `angle_deg`, `z_m` and the
    `z_source` string that says whether `column_site` measured or fell back.
    Only `ok` rows are returned: a failed export wrote no mesh either.
    """
    try:
        with open(path, encoding="utf-8") as f:
            man = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for row in man.get("columns", ()):
        key = str(row.get("key", ""))
        if not key.startswith("column_") or not row.get("ok"):
            continue
        if "z_m" not in row or "angle_deg" not in row:
            continue                    # a row from before 4t recorded neither
        out[key[len("column_"):]] = row
    return out


def columns(legacy=False, site_source="manifest", cells_dir=CELLS):
    """-> [{sector, rings, angle_deg, z_m, glb}] for every exported column.

    THE PLACEMENT IS READ FROM `station_manifest.json`, NOT DERIVED A SECOND
    TIME, and header section 5 is the whole argument. `bake_one` REBUILDS the
    shaft with `spoke_way(..., angle_deg, z_m)` to recover the collision half
    the export drops, and refuses if the rebuilt render half does not match the
    shipped GLB triangle for triangle and bound for bound. So the z used here is
    not a preference about where the column belongs -- it is a claim about what
    the file on disk IS, and the only witness to that is the row the export
    wrote beside it.

    `column_site.site()` is still called, every time, on both paths: its answer
    is carried as `derived_z_m` so a stale mesh can be NAMED rather than
    silently baked. `site_source="derive"` uses that answer instead, which is
    the behaviour that refused 3 of 5 columns in Windows build run 9 and is
    kept as the negative control.

    `legacy=True` additionally asks `column_site` for the pre-4t `min(z)` rule.
    """
    import column_site as CS                                     # noqa: PLC0415
    import interior as it                                        # noqa: PLC0415
    import routes as RT                                          # noqa: PLC0415
    _decks, rings, _ang = _work_list()
    nodes = RT.clusters()
    schema, profile = it.load()
    rec = manifest_sites()
    by_sector = collections.defaultdict(set)
    for s, r in rings:
        by_sector[s].add(r)
    out = []
    for sec, rs in sorted(by_sector.items()):
        glb = os.path.join(SRC, "column_%s.glb" % sec)
        site = CS.site(schema, profile, nodes, sec, rings=sorted(rs),
                       cells_dir=cells_dir,
                       rule="legacy" if legacy else "floor")
        row = rec.get(sec)
        if site_source == "manifest" and row is not None:
            angle, z = float(row["angle_deg"]), float(row["z_m"])
            src = "station_manifest.json (%s)" % str(row.get("z_source", "?"))
        else:
            angle, z = site["angle_deg"], site["z_m"]
            src = ("column_site, re-derived now (%s)" % site["source"]
                   if row is None else
                   "column_site, re-derived now -- --site-from=derive")
        out.append({
            "sector": sec,
            "rings": sorted(rs),
            "angle_deg": angle,
            "z_m": z,
            "placement_source": src,
            "have_manifest_row": row is not None,
            # WHAT THE MESH ON DISK IS, kept separately from what we chose to
            # rebuild at, so `--site-from=derive` cannot make the staleness
            # report compare a number with itself.
            "manifest_z_m": None if row is None else float(row["z_m"]),
            # WHERE THIS COLUMN WOULD GO IF IT WERE BUILT TODAY. Kept beside
            # the placement rather than instead of it, because the gap between
            # the two IS the defect and a single number cannot express it.
            "derived_z_m": site["z_m"],
            "derived_angle_deg": site["angle_deg"],
            "derived_source": site["source"],
            "stale": (row is not None
                      and (abs(float(row["z_m"]) - site["z_m"]) > 1e-6
                           or abs(float(row["angle_deg"])
                                  - site["angle_deg"]) > 1e-6)),
            "site": site,
            "glb": glb,
            "have_glb": os.path.exists(glb),
        })
    return out


def deck_table(sector=None):
    with open(CELL_MANIFEST, encoding="utf-8") as f:
        rows = json.load(f)["deck_table"]
    return [r for r in rows if sector is None or r["sector"] == sector]


# ===========================================================================
# GEOMETRY
# ===========================================================================

def glb_bounds(path):
    """-> (triangles, groups, [(lo,hi) x3], (r_lo,r_hi), (a_lo,a_hi)).

    Angles are UNWRAPPED about the mesh's own circular mean, so a column at
    0 deg reports [-3.2, +3.2] rather than [0, 360]. A min/max of `atan2` is
    the classic way to measure a 6-degree object as covering the whole ring,
    and yellow sits exactly on the seam.
    """
    from glb_to_obj import read_glb                              # noqa: PLC0415
    gs = read_glb(path)
    tris = sum(len(t) for _n, _v, t in gs)
    pts = [p for _n, v, _t in gs for p in v]
    if not pts:
        raise SystemExit("%s holds no vertices" % path)
    box = [(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)]
    rs = [math.hypot(p[0], p[1]) for p in pts]
    sx = sum(p[0] / max(r, 1e-9) for p, r in zip(pts, rs))
    sy = sum(p[1] / max(r, 1e-9) for p, r in zip(pts, rs))
    mean = math.degrees(math.atan2(sy, sx))
    ds = [((math.degrees(math.atan2(p[1], p[0])) - mean + 180.0) % 360.0)
          - 180.0 for p in pts]
    return (tris, len(gs), box, (min(rs), max(rs)),
            (mean + min(ds), mean + max(ds)))


def rebuild(col):
    """`spoke_way` again -- for the collision the export computes and drops.

    Returns (V, T, G, stats). Costs 12 s on blue and about a minute on red;
    that is the price of the collision half existing at all.
    """
    import interior as it                                        # noqa: PLC0415
    import spoke_way as SW                                       # noqa: PLC0415
    schema, profile = it.load()
    return SW.spoke_way(schema, profile, col["sector"], col["rings"],
                        col["angle_deg"], col["z_m"])


def write_glb(stem, verts, tris, spans, out_dir):
    """OBJ -> GLB through the same writer `export_station._write` uses.

    Deliberately the same path rather than a second one: `deck.write_obj`
    carries no normals and no UVs, and a converter of mine that DID carry them
    would give the collision half a fidelity the render half on disk does not
    have. Two descriptions of one pipeline is the thing this project keeps
    paying for.
    """
    import deck as D                                             # noqa: PLC0415
    import export_gltf                                           # noqa: PLC0415
    obj = os.path.join(out_dir, stem + ".obj")
    glb = os.path.join(out_dir, stem + ".glb")
    D.write_obj(obj, verts, tris, spans)
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj, "--out", glb]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    if not os.path.exists(glb) or os.path.getsize(glb) < 512:
        raise SystemExit("%s: glb is missing or empty" % stem)
    os.remove(obj)
    return glb


def pick_row(sector, mid_r, a_lo, a_hi, z_lo, z_hi):
    """The deck_table row to bake this column against. -> (row, whole)

    `bake()` will not run without one: it reads `cell_deg`, `floor_r_m`,
    `sight_line_m`, `cell_length_m` and `z0` off a deck, and a column is not a
    deck. Two things follow and both are chosen rather than defaulted.

    FIRST, PREFER A ROW WHOSE GRID DOES NOT CUT THE COLUMN IN HALF -- AND THE
    GRID HAS TWO AXES, WHICH COST A REBAKE TO LEARN. `_split` bins on the arc
    (from 0 deg in steps of `cell_deg`) AND on the z band (from the deck's own
    `z0` in steps of `cell_length_m`). Choosing for the arc alone got blue down
    to one arc cell and it still came out in two, because the column is a
    3.42 m slab in z and this row's band edge at z = 6794 + 85.2 = 6879.2 falls
    inside it. Both are checked here.

    A split shaft is not a hole -- the halves' AABBs differ by a couple of
    metres against a 98.9 m load radius, so they are always co-resident -- but
    one half then holds all six bore quads and the other holds sills, which is
    a worse thing to own than one cell.

    SECOND, AMONG THOSE, TAKE THE RADIUS NEAREST THE COLUMN'S MIDDLE. With the
    arc dropped, `floor_r_m` survives only in `_cell_spawn`'s "is this the deck
    floor or the outermost collision" test and in the residency block; nearest
    keeps both honest. Yellow at 0 deg cannot be saved by any step, because
    every arc grid starts at 0 -- it falls to the last tier and the caller
    says so in its own output.
    """
    rows = deck_table(sector)
    if not rows:
        raise SystemExit("no deck_table rows for sector %r" % sector)

    def one_arc(r):
        cd = float(r["cell_deg"])
        return (math.floor((a_lo % 360.0) / cd)
                == math.floor((a_hi % 360.0) / cd))

    def one_band(r):
        bl = float(r["cell_length_m"])
        z0 = float(r.get("z0", 0.0))
        if bl <= 0.0:
            return True
        return (math.floor((z_lo - z0) / bl) == math.floor((z_hi - z0) / bl))

    for pool in ([r for r in rows if one_arc(r) and one_band(r)],
                 [r for r in rows if one_arc(r)],
                 rows):
        if pool:
            best = min(pool, key=lambda r: abs(r["floor_r_m"] - mid_r))
            return best, one_arc(best) and one_band(best)
    raise SystemExit("no deck_table rows for sector %r" % sector)


# ===========================================================================
# THE BAKE
# ===========================================================================

def godot_binary():
    import walkable as W                                         # noqa: PLC0415
    return W.godot_binary()


def already_baked(sector):
    """True when the cell set AND every .scn it names are on disk.

    A manifest whose meshes have been deleted is not a baked column, and
    `--force` should not be the only way to notice.
    """
    p = os.path.join(CELLS, "column_%s_cells.json" % sector)
    if not os.path.exists(p):
        return False
    try:
        with open(p, encoding="utf-8") as f:
            man = json.load(f)
    except (ValueError, OSError):
        return False
    rows = man.get("cells") or []
    if not rows:
        return False
    for c in rows:
        for k in ("mesh", "collision"):
            v = c.get(k, "")
            if v and not os.path.exists(os.path.join(CELLS, v)):
                return False
    return True


def bake_one(col, work, timeout=600, quiet=True):
    """Regenerate the collision, run `stream.gd::bake()`, keep the cells.

    THE BAKE RUNS INTO A SCRATCH DIRECTORY AND THE RESULTS ARE MOVED. `bake()`
    writes `<stem>_cells.json` AND an unconditional `cells.json` beside it --
    the single-cluster name every gate in `docs/streaming-4g.md` uses. Baking
    straight into `cells/` would silently replace whichever deck's `cells.json`
    is there, which is somebody else's artefact and not ours to move.
    """
    sec = col["sector"]
    rep = {"sector": sec, "ok": False}
    t0 = time.time()

    tris, groups, box, (r_lo, r_hi), (a_lo, a_hi) = glb_bounds(col["glb"])
    rep.update({"glb_tris": tris, "glb_groups": groups,
                "r_m": [r_lo, r_hi], "z_m": [box[2][0], box[2][1]],
                "angle_deg": [a_lo, a_hi], "rise_m": r_hi - r_lo})

    V, T, G, st = rebuild(col)
    # THE COLLISION MUST DESCRIBE THE MESH ON DISK. Both halves come out of one
    # `spoke_way` call, so checking the render half against the shipped GLB
    # checks the collision half too -- and it is the only check available,
    # since the collision half was never written and has nothing to compare to.
    if len(T) != tris:
        rep["why"] = ("rebuilt render is %d triangles, %s has %d -- the schema "
                      "has moved since the export and the collision this would "
                      "bake describes a different shaft"
                      % (len(T), os.path.basename(col["glb"]), tris))
        return rep
    # AND THE BOUNDS, BECAUSE A TRIANGLE COUNT CANNOT SEE A TRANSLATION.
    #
    # This guard's docstring promised "triangle count AND BOUNDS" and the code
    # compared only the count. An adversarial verifier broke it end to end on
    # yellow, whose stack is congruent under a pure shift in z:
    #
    #   yellow  shipped 21,388 tri @ z 158.4..161.8
    #           rebuild 21,388 tri @ z 238.4..241.8   -- guard refuses: FALSE
    #   green   shipped  7,624 tri  -> rebuild 6,908  -- guard refuses: True
    #
    # `ring_stack` returns a bit-identical 24-landing stack at z=160 and z=240,
    # so 21,388 == 21,388 and the shaft sails through 80 m from where the
    # shipped render mesh is. `bake_one` then hands Godot the SHIPPED render
    # and the REBUILT collision, and `finalise` writes the rebuilt z into the
    # manifest -- so `verify()` reads the moved z, reports the column as
    # connecting, and the player gets a render/collision split with a green
    # gate over it. The other columns refuse only because their landing COUNT
    # happens to change; the guard was audited where it works.
    #
    # THE CAUSE OF THAT 80 m IS NOW KNOWN AND THE GUARD IS UNCHANGED. It was
    # not a schema move: `column_site.site` measures against baked deck cells,
    # `build_world.py` exports the columns two steps BEFORE those cells exist,
    # and this file used to re-derive the placement after they did. Header
    # section 5. The placement now comes from `station_manifest.json`, so a
    # matched pair reaches this guard and a mismatch here means the manifest
    # and the mesh disagree -- which is a thing worth refusing over.
    #
    # `box` was already computed above and thrown away. This compares it.
    if V:
        reb = [(min(p[i] for p in V), max(p[i] for p in V)) for i in range(3)]
        off = max(max(abs(reb[i][0] - box[i][0]), abs(reb[i][1] - box[i][1]))
                  for i in range(3))
        if off > BOUNDS_TOL_M:
            rep["why"] = (
                "rebuilt shaft has the same %d triangles as %s but sits %.3f m "
                "away (rebuilt z %.1f..%.1f against the shipped %.1f..%.1f) -- "
                "a congruent stack at a different z. Baking this would give the "
                "shipped render mesh a collision shell from somewhere else."
                % (tris, os.path.basename(col["glb"]), off,
                   reb[2][0], reb[2][1], box[2][0], box[2][1]))
            return rep
    xv, xt, xmeta = st["collision"]
    # THE SOURCE GROUP NAMES SURVIVE -- `lift_shaft`, `lift_sill`, `lift_car`.
    # `_write_cell` names its nodes after them and `lift_car` is a separate
    # group precisely because it MOVES; collapsing all three into one
    # "collision" node would leave a runtime unable to move exactly the car,
    # which is `collision.door_panel`'s reason for existing one level down.
    xspans = list(xmeta.get("groups") or [("collision", 0, len(xt))])
    if not xt:
        rep["why"] = "lift_collision returned no triangles"
        return rep
    rep.update({"col_tris": len(xt), "landings": st["landings"],
                "rings_served": st["rings_served"], "stack_r_m":
                [round(d["floor_r_m"], 3) for d in st["stack"]]})

    cglb = write_glb("column_%s_collision" % sec, xv, xt, xspans, work)

    mid_r = 0.5 * (r_lo + r_hi)
    row, whole = pick_row(sec, mid_r, a_lo, a_hi, box[2][0], box[2][1])
    rep["deck_row"] = {"id": row["id"], "label": row["label"],
                       "floor_r_m": row["floor_r_m"],
                       "cell_deg": row["cell_deg"],
                       "sight_line_m": row["sight_line_m"],
                       "cell_length_m": row["cell_length_m"],
                       "one_arc_cell": whole}

    out = os.path.join(work, "out_" + sec)
    os.makedirs(out, exist_ok=True)
    godot = godot_binary()
    if godot is None:
        rep["why"] = "no double-precision Godot binary; run tools/build_godot.sh"
        return rep
    cmd = [godot, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--", "--bake-cells",
           "--glb=%s" % col["glb"], "--collision=%s" % cglb,
           "--sector=%s" % sec,
           "--ring-index=%d" % int(row["ring_index"]),
           "--deck-index=%d" % int(row["deck_index"]),
           "--cell-id=column_%s" % sec, "--cells-out=%s" % out]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout)
        code, log = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        code, log = -1, "timed out after %d s" % timeout

    # THE ARTEFACTS ARE THE VERDICT, NOT THE EXIT CODE -- `bake_station.py`'s
    # rule, and it is right for the same reason: a bake that exits 0 having
    # written nothing is the failure this project has paid for twice.
    man_p = os.path.join(out, "column_%s_cells.json" % sec)
    scn = sorted(glob.glob(os.path.join(out, "column_%s_c*.scn" % sec)))
    if code != 0 or not os.path.exists(man_p) or not scn:
        rep["why"] = "bake exit %d, %d .scn, manifest %s" % (
            code, len(scn), "yes" if os.path.exists(man_p) else "no")
        rep["engine"] = [ln for ln in log.splitlines()
                         if ln.strip() and "ALSA" not in ln][-6:]
        return rep

    with open(man_p, encoding="utf-8") as f:
        man = json.load(f)
    man = finalise(man, col, st, row, whole)

    os.makedirs(CELLS, exist_ok=True)
    # STALE .scn FILES ARE SWEPT, and that is not tidiness. A re-bake against a
    # different deck row produces different cell ids (`_c04z01` became `_c04z00`
    # the first time this file's grid choice was fixed), so the old meshes would
    # sit in `cells/` named by nothing -- megabytes the package carries and no
    # manifest can account for. The manifest is written last, so a crash between
    # the sweep and the write leaves a set `already_baked` correctly calls unbaked.
    for old in glob.glob(os.path.join(CELLS, "column_%s_c*.scn" % sec)):
        os.remove(old)
    for p in scn:
        shutil.move(p, os.path.join(CELLS, os.path.basename(p)))
    with open(os.path.join(CELLS, "column_%s_cells.json" % sec), "w") as f:
        json.dump(man, f, indent=1)

    rep.update({"ok": True, "cells": len(man["cells"]),
                "cell_tris": sum(int(c["tris"]) for c in man["cells"]),
                "cell_col_tris": sum(int(c["col_tris"]) for c in man["cells"]),
                "mb": round(sum(os.path.getsize(os.path.join(CELLS,
                                os.path.basename(p))) for p in scn) / 1e6, 2),
                "seconds": round(time.time() - t0, 1)})
    if not quiet:
        for ln in log.splitlines():
            if ln.startswith("bake:"):
                print("        | " + ln[:150])
    return rep


def finalise(man, col, st, row, whole):
    """Turn a deck-shaped manifest into a column-shaped one.

    THREE EDITS AND NOTHING ELSE, because everything `bake()` measured off the
    real geometry -- the AABBs, the triangle counts, the group counts, the
    spawn -- is right and is not ours to restate.

    1. `arc` -> `arc_deck_grid`. See the header: an arc metric has no radial
       term and a column is a radial thing. Dropping the key is what makes
       `distance_to` and `start_cell` use the AABB, which both already support.
    2. `corridor` -> `column`. `bake()` measures a ring corridor and on a shaft
       it measures the shaft: it reported blue's "corridor" at r=197.81 with an
       "axial spine 0.00 m wide". True, and calling it a corridor in the
       merged manifest's `corridor_by_deck` would be a lie about what it is.
    3. `kind: "ring"` -> `"column"`, plus the landing stack, which is the thing
       `--verify` needs and the only place it is written down.

    THE RESIDENCY BLOCK IS LEFT EXACTLY AS `bake()` WROTE IT, and that is safe
    for a stated reason rather than by luck. `merge_cells.merge` takes the
    MAXIMUM radius, free radius and cell length across every set on disk, so a
    column could widen the whole station's load radius -- a station-wide
    decision, in a file this one does not own. It cannot: every value here is
    copied from a `cell_manifest.json` deck row, and the merge already ranges
    over deck rows. Asserted below rather than argued.
    """
    dt = deck_table()
    ceil = {"radius_m": max(r["sight_line_m"] for r in dt),
            "free_radius_m": max(max(r["sight_line_m"], r["cell_length_m"])
                                 for r in dt),
            "cell_length_m": max(r["cell_length_m"] for r in dt)}
    res = man.get("residency", {})
    for k, cap in ceil.items():
        if float(res.get(k, 0.0)) > cap + 1e-9:
            raise SystemExit(
                "column %s residency %s=%.2f exceeds the deck maximum %.2f -- "
                "merging it would widen the station's global load radius"
                % (col["sector"], k, float(res[k]), cap))

    for c in man.get("cells", []):
        if "arc" in c:
            c["arc_deck_grid"] = c.pop("arc")
    measured = man.pop("corridor", {})
    man["kind"] = "column"
    man["written_by"] = ("godot/scripts/stream.gd bake(), post-processed by "
                         "tools/bake_columns.py")
    man["column"] = {
        "sector": col["sector"],
        "rings_served": st["rings_served"],
        "angle_deg": col["angle_deg"],
        "z_m": col["z_m"],
        "landings": st["landings"],
        "rise_m": st["rise_m"],
        "rise_axis": "radius -- down is outward on a spun ring, so the "
                     "outermost landing is the bottom one. NOT z: the whole "
                     "column is a 3.42 m slab in z.",
        "landing_r_m": [round(d["floor_r_m"], 3) for d in st["stack"]],
        "landing_ring": [int(d["ring_index"]) for d in st["stack"]],
        "landing_deck": [int(d["ring_deck_index"]) for d in st["stack"]],
        "baked_against": {
            "deck_row": row["id"], "label": row["label"],
            "floor_r_m": row["floor_r_m"], "cell_deg": row["cell_deg"],
            "why": "the deck_table row nearest this column's mid radius whose "
                   "arc grid does not cut it in half; bake() needs a deck row "
                   "and a column is not a deck",
            "one_arc_cell": whole},
        "measured_by_bake": measured,
        "no_arc_because": "distance_to's arc form has no radial term and this "
                          "object IS radial; the AABB branch is correct here "
                          "and both stream.gd and boot.start_cell take it",
    }
    return man


# ===========================================================================
# VERIFY -- do these cells sit where a deck does?
# ===========================================================================

def _box(c):
    p, s = c["aabb"]["pos"], c["aabb"]["size"]
    return [(p[i], p[i] + s[i]) for i in range(3)]


def _gap(a, b):
    """Shortest distance between two axis-aligned boxes. 0 when they meet."""
    d = 0.0
    for i in range(3):
        g = max(a[i][0] - b[i][1], b[i][0] - a[i][1], 0.0)
        d += g * g
    return math.sqrt(d)


def _point_gap(p, b):
    q = [min(max(p[i], b[i][0]), b[i][1]) for i in range(3)]
    return math.dist(p, q)


def deck_cell_rows(cells_dir=CELLS):
    """Every baked DECK cell on disk. Not the merged file, not the columns.

    Per-deck sets rather than `station_cells.json` so this measurement works
    on a tree where the merge has not been run -- and so it cannot be fooled
    by a merged manifest that already contains our own columns.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_cells.json"))):
        stem = os.path.basename(p)[:-len("_cells.json")]
        if stem == "station" or stem.startswith("column_"):
            continue
        with open(p, encoding="utf-8") as f:
            for c in json.load(f).get("cells", []):
                if c.get("aabb"):
                    out.append((stem, c))
    return out


def verify(cells_dir=CELLS, near_m=NEAR_M, sector=None, dz=0.0):
    """Does each column's landings sit where a deck a player can walk sits?

    THE MEASUREMENT IS PER LANDING, NOT PER COLUMN, because a column is a
    stack of doors and the question "does this connect anything" is really
    "how many of these doors open onto a floor". A whole-column bounding-box
    test can be satisfied by one end of a 215 m shaft and say nothing about
    the other 57 landings, which is the shape of error this project makes.

    Returns (rows, bad) -- `bad` is the list of columns with no landing within
    `near_m` of any deck cell, and is what the exit code is taken from.

    `dz` shifts every landing along the axis before scoring and is used by
    `_selftest` and by nothing else. It is a parameter rather than a copy of
    this loop in the test because a control that runs a reimplementation of the
    measurement proves the reimplementation works; the verdict has to come out
    of the function that produces the verdict.
    """
    decks = deck_cell_rows(cells_dir)
    rows, bad = [], []
    for p in sorted(glob.glob(os.path.join(cells_dir, "column_*_cells.json"))):
        sec = os.path.basename(p)[len("column_"):-len("_cells.json")]
        if sector and sec != sector:
            continue
        with open(p, encoding="utf-8") as f:
            man = json.load(f)
        col = man.get("column", {})
        mine = man.get("cells", [])
        a = math.radians(float(col.get("angle_deg", 0.0)))
        z = float(col.get("z_m", 0.0)) + dz
        near, worst, best = 0, 0.0, (1e18, "")
        for r in col.get("landing_r_m", []):
            pt = (r * math.cos(a), r * math.sin(a), z)
            d, who = 1e18, ""
            for stem, c in decks:
                g = _point_gap(pt, _box(c))
                if g < d:
                    d, who = g, c["id"]
            if d <= near_m:
                near += 1
            worst = max(worst, d)
            if d < best[0]:
                best = (d, who)
        # And the coarse whole-column form, kept because it is the cheap one
        # and because a reader will want both numbers.
        cbox = None
        for c in mine:
            b = _box(c)
            cbox = b if cbox is None else [(min(cbox[i][0], b[i][0]),
                                            max(cbox[i][1], b[i][1]))
                                           for i in range(3)]
        box_gap, box_who = 1e18, ""
        if cbox is not None:
            for stem, c in decks:
                g = _gap(cbox, _box(c))
                if g < box_gap:
                    box_gap, box_who = g, c["id"]
        row = {"sector": sec, "cells": len(mine),
               "tris": sum(int(c.get("tris", 0)) for c in mine),
               "col_tris": sum(int(c.get("col_tris", 0)) for c in mine),
               "landings": len(col.get("landing_r_m", [])),
               "landings_near": near, "nearest_landing_m": best[0],
               "nearest_landing_to": best[1], "worst_landing_m": worst,
               "box_gap_m": box_gap, "box_gap_to": box_who,
               "rings_served": col.get("rings_served", []),
               "r_m": [min(col.get("landing_r_m") or [0.0]),
                       max(col.get("landing_r_m") or [0.0])],
               "z_m": z, "angle_deg": col.get("angle_deg", 0.0),
               "box": cbox}
        rows.append(row)
        if near == 0:
            bad.append(sec)
    return rows, bad


def print_verify(rows, bad, near_m=NEAR_M, decks=0):
    print("\n  DO THE COLUMNS TOUCH A DECK? -- %d baked deck cells to test "
          "against, a landing counts as joined within %.1f m\n" % (decks, near_m))
    print("    %-7s %5s %8s %6s  %-22s %-22s %s"
          % ("sector", "cells", "tris", "land", "landings near a deck",
             "nearest deck cell", "verdict"))
    for r in rows:
        print("    %-7s %5d %8s %6d  %-22s %-22s %s"
              % (r["sector"], r["cells"], "{:,}".format(r["tris"]),
                 r["landings"],
                 "%d of %d (best %.1f m)" % (r["landings_near"], r["landings"],
                                             r["nearest_landing_m"]),
                 r["nearest_landing_to"][:22],
                 "CONNECTS" if r["landings_near"] else "STANDS CLEAR"))
    for r in rows:
        print("      %-7s r=[%.1f, %.1f] (%.1f m of rise), z=%.1f, %.2f deg, "
              "rings %s; whole-column AABB gap %.2f m to %s"
              % (r["sector"], r["r_m"][0], r["r_m"][1],
                 r["r_m"][1] - r["r_m"][0], r["z_m"], r["angle_deg"],
                 r["rings_served"], r["box_gap_m"], r["box_gap_to"]))
    if bad:
        print("\n  %d of %d COLUMNS JOIN NOTHING: %s" % (len(bad), len(rows),
                                                         ", ".join(bad)))
        print("    Not a bake failure -- those cells are correct and they "
              "stream. It is where the column was PLACED.")
        print("    Session 4t moved that decision into tools/column_site.py "
              "and `--gate-placement` scores it without")
        print("    a bake. If that gate passes and this one does not, THE "
              "BAKED CELLS ARE STALE: they were baked from")
        print("    column_*.glb built at the old z. Re-run "
              "tools/export_station.py then this file with --force.")
    else:
        print("\n  every column has a landing on a deck")


# ===========================================================================
# SELFTEST
# ===========================================================================

def _selftest():
    """Assert the box maths, and assert it DISCRIMINATES.

    The first three are round trips. The fourth is the one that matters: a
    proximity test that returned 0 for everything would report five connected
    columns and pass any check written only on the connected ones. So it is
    asserted that this measurement separates grey and red (which land on deck
    geometry) from blue and green (which are 78 m and 108 m of vacuum away),
    using the baked deck cells actually on disk.

    TWO NEGATIVE CONTROLS, BOTH RUN, AND THEY FIRE ON DIFFERENT CHECKS -- which
    is the point of writing check 4 as two opposed halves rather than one.

      dropping the `max(..., 0.0)` clamp from `_gap`, so an overlap on one axis
      contributes its square instead of nothing:
          overlapping boxes measured 0.866, not 0
          boxes 3 m apart in x measured 3.317
          grey ... now measures 38.48 m      red ... now measures 55.39 m
      -- five failures. Note the DIRECTION: unclamping makes distances bigger,
      so it breaks the CONNECTS half. It is recorded because the first version
      of this docstring asserted it would make blue read 0.00 m, which is the
      opposite of what it does, and an unrun control is a decoration.

      measuring in the plane only -- `range(2)` and `math.dist(p[:2], q[:2])`,
      the plausible slip, since "the column is at the deck's radius and angle"
      feels like enough:
          blue must NOT touch a deck ... (measured 0.00 m)
          green must NOT touch a deck ... (measured 0.00 m)
      -- every box check still passes, and the STANDS CLEAR half fails. This is
      the control that matters here, because z is exactly the axis these three
      columns are wrong on.
    """
    bad, n = [], 0

    # 1. two boxes that meet are at zero, and a point inside a box likewise
    a = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
    b = [(0.5, 2.0), (0.5, 2.0), (0.5, 2.0)]
    n += 1
    if _gap(a, b) != 0.0:
        bad.append("overlapping boxes measured %.3f, not 0" % _gap(a, b))
    n += 1
    if _point_gap((0.5, 0.5, 0.5), a) != 0.0:
        bad.append("a point inside a box is not at zero")

    # 2. a pure separation on one axis is that separation
    c = [(4.0, 5.0), (0.0, 1.0), (0.0, 1.0)]
    n += 1
    if abs(_gap(a, c) - 3.0) > 1e-9:
        bad.append("boxes 3 m apart in x measured %.3f" % _gap(a, c))
    # 3. and a diagonal separation is the hypotenuse, NOT the larger axis --
    #    which is what a max-of-axes distance would give and is the slip the
    #    negative control above reproduces.
    d = [(4.0, 5.0), (5.0, 6.0), (0.0, 1.0)]
    n += 1
    if abs(_gap(a, d) - 5.0) > 1e-9:
        bad.append("boxes 3 m and 4 m apart measured %.3f, want 5" % _gap(a, d))
    n += 1
    if abs(_point_gap((4.0, 5.0, 0.5), a) - 5.0) > 1e-9:
        bad.append("point 3,4 off a box measured %.3f, want 5"
                   % _point_gap((4.0, 5.0, 0.5), a))

    # 4. THE PLACEMENT USED TO REBUILD A SHAFT DESCRIBES THE SHIPPED MESH.
    #    The check that would have caught Windows build run 9 without a bake,
    #    a Godot, or a GPU: for every column with a mesh on disk, the z the
    #    manifest records must be the z the GLB is actually at. It is the same
    #    comparison `bake_one`'s bounds guard makes, hoisted to where it costs
    #    a JSON read instead of a minute of `spoke_way`.
    #
    #    AND IT IS RUN BOTH WAYS. `--site-from=derive` against an empty floor
    #    table reproduces run 9 exactly -- `column_site` falls back to
    #    `routes.column_z` and hands back yellow z=160 for a mesh at z=240 --
    #    so the assertion below is asserted to FAIL on that path. A placement
    #    check that cannot fail is the defect this project keeps producing.
    for c in columns():
        if not c["have_glb"] or not c["have_manifest_row"]:
            continue
        n += 1
        z_glb = glb_bounds(c["glb"])[2][2]
        mid = 0.5 * (z_glb[0] + z_glb[1])
        if abs(mid - c["z_m"]) > 2.0:
            bad.append("column_%s.glb sits at z=%.1f and %s says it was built "
                       "at z=%.1f -- rebuilding it here would describe a "
                       "different shaft"
                       % (c["sector"], mid,
                          os.path.basename(STATION_MANIFEST), c["z_m"]))
    n += 1
    off = []
    for c in columns(site_source="derive", cells_dir=os.devnull + "_nope"):
        if not c["have_glb"]:
            continue
        mid = 0.5 * sum(glb_bounds(c["glb"])[2][2])
        if abs(mid - c["z_m"]) > 2.0:
            off.append("%s %.0f vs glb %.0f" % (c["sector"], c["z_m"], mid))
    if not off:
        bad.append("with no floor table and --site-from=derive, every column "
                   "should be rebuilt at column_site's routes.column_z "
                   "fallback and disagree with the shipped mesh -- none did, "
                   "so this check cannot fail and proves nothing")

    # 5. IT DISCRIMINATES, on the station's own baked cells.
    decks = deck_cell_rows()
    if not decks:
        print("bake_columns selftest: %d box checks passed; NO BAKED DECK "
              "CELLS on disk, so the discrimination check could not run "
              "-- that is not a pass" % n)
        return 1
    rows, _bad = verify()
    by = {r["sector"]: r for r in rows}
    if not by:
        print("bake_columns selftest: %d box checks passed; no column cell "
              "sets baked yet, so the discrimination check could not run "
              "-- run the bake first" % n)
        return 1
    # THE OLD FORM OF THIS CHECK NAMED FOUR SECTORS AND TWO DISTANCES --
    # "grey and red must measure 0.00 m, blue must be 70 m of vacuum away and
    # green 100 m" -- taken from the tree as it stood before session 4t moved
    # the placement into `column_site.py`. Those numbers were a description of
    # a DEFECT, and when the defect was fixed the assertion started failing for
    # being right: blue and green now land on floor and measure 0.00 m, so the
    # selftest read FAILED on a station that had just been improved. A check
    # written against the current content is a check that expires; this one is
    # written against the measurement instead and cannot.
    #
    # BOTH HALVES, BECAUSE EITHER ALONE IS SATISFIED BY A BROKEN MEASUREMENT.
    # A proximity test stuck at 0 passes "something touches"; one stuck at
    # infinity passes "something is far". So: at least one real column must
    # measure 0, AND the same column displaced 200 m up the axis -- the axis
    # these columns were actually wrong on -- must measure at least 190.
    n += 1
    touching = [r["sector"] for r in rows if r["box_gap_m"] <= 0.0]
    if not touching:
        bad.append("no baked column touches deck geometry at all (%s) -- a "
                   "proximity test that never returns 0 reports every column "
                   "as standing clear and cannot be trusted when it does"
                   % ", ".join("%s %.1f" % (r["sector"], r["box_gap_m"])
                               for r in rows))
    # AND THE DISPLACED FORM IS SCORED BY `verify` ITSELF, ON THE VERDICT AND
    # NOT ON A DISTANCE. Two earlier shapes of this control were both wrong in
    # ways worth keeping, because each looked right:
    #
    #   min over every deck cell, 200 m of z, expect >= 190 m
    #       -> 0.0 m on blue, green and yellow. Correct, and useless: the
    #          station is 8 km of axis with floor at hundreds of z values, so a
    #          column shoved 200 m up the spine lands on SOMEBODY ELSE'S deck.
    #   the same, against the one cell it had been touching
    #       -> 77-166 m, still under the threshold, because a deck cell is
    #          itself ~120 m long in z. A distance threshold here is a number
    #          about cell size, not about the measurement.
    #
    # The question the file actually answers is "does this landing meet floor",
    # so the control asks that: displace and the verdict must flip to STANDS
    # CLEAR on every column.
    #
    # **AND THE DISPLACEMENT HAS TO LEAVE THE STATION, WHICH IS A FINDING ABOUT
    # THE MEASUREMENT AND NOT A CHOICE OF CONSTANT.** Swept: +200 m flips 2 of
    # 5, +600 m flips 2, +1200 m flips 2, +20000 m flips 5. Yellow reads
    # `nearest_landing 0.0 m` at every one of those, because its inner landing
    # is at r=30.5 -- on the axial spine, whose cell AABB spans most of the
    # 8,047 m of axis. **A point-to-AABB test cannot resolve z near the axis**,
    # so `landings_near` is a weaker statement there than it looks, and a
    # reader of a CONNECTS verdict on an axis-hugging landing should know it.
    # 20 km is past both ends of the station, so nothing can be near anything.
    n += 1
    moved_rows, moved_bad = verify(dz=20000.0)
    still = [r["sector"] for r in moved_rows if r["landings_near"]]
    if len(moved_bad) != len(moved_rows) or still:
        bad.append("with every landing displaced 200 m along z, %s still "
                   "report landings on a deck -- the verdict does not depend "
                   "on where the column is, so CONNECTS means nothing"
                   % (", ".join(still) or "some columns"))
    if bad:
        print("bake_columns selftest FAILED on %d:" % len(bad))
        for b in bad:
            print("   " + b)
        return 1
    print("bake_columns selftest: %d checks passed over %d baked deck cells "
          "and %d column cell set(s)" % (n, len(decks), len(rows)))
    joined = [r["sector"] for r in rows if r["landings_near"]]
    print("  and it separates them: %s land on a deck, %s do not"
          % (", ".join(joined) or "(none)",
             ", ".join(r["sector"] for r in rows if not r["landings_near"])
             or "(none)"))
    return 0


# ===========================================================================

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sector", default="", help="one of %s" % (SECTORS,))
    ap.add_argument("--force", action="store_true",
                    help="re-bake a column whose cells are already on disk")
    ap.add_argument("--verify", action="store_true",
                    help="measure the baked columns against the baked decks "
                         "and bake nothing. Exits 1 if a column joins nothing")
    ap.add_argument("--check-mesh", action="store_true",
                    help="does each column_<sector>.glb sit at the z "
                         "station_manifest.json says it was built at, and is "
                         "that still the z column_site would choose? Seconds, "
                         "no Godot, no spoke_way, no bake -- this is the check "
                         "that would have caught Windows build run 9 before "
                         "45 minutes of export")
    ap.add_argument("--gate-placement", action="store_true",
                    help="score where the columns WILL be built, without a "
                         "bake or a mesh. Exits 1 if a column joins nothing")
    ap.add_argument("--legacy", action="store_true",
                    help="with --gate-placement, score the pre-4t rule "
                         "(min z-cluster). The negative control; it FAILS")
    ap.add_argument("--site-from", choices=("manifest", "derive"),
                    default="manifest",
                    help="where the (angle, z) to rebuild each shaft at comes "
                         "from. 'manifest' is what export_station RECORDED "
                         "building the shipped glb at; 'derive' re-derives it "
                         "from column_site against whatever deck cells are on "
                         "disk NOW, which is the pre-fix behaviour and the "
                         "negative control")
    ap.add_argument("--cells", default=CELLS,
                    help="deck cell directory column_site measures against. "
                         "Point it at an empty path to reproduce the state a "
                         "fresh checkout is in at build step 1")
    ap.add_argument("--near", type=float, default=NEAR_M,
                    help="how near a landing must be to a deck cell to count "
                         "as joined (default %.1f m)" % NEAR_M)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--engine-log", action="store_true",
                    help="echo bake()'s own lines")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return _selftest()

    if a.check_mesh:
        # TWO QUESTIONS, AND THEY FAIL DIFFERENTLY ON PURPOSE.
        #   mismatch  the manifest does not describe the file beside it. Nobody
        #             can rebuild that shaft's collision; the bake will refuse.
        #   stale     the manifest and the file agree, and both were decided
        #             before the deck cells existed. The bake works and the
        #             lift may open onto nothing.
        rows = columns(cells_dir=a.cells)
        if a.sector:
            rows = [c for c in rows if c["sector"] == a.sector]
        print("\n  DOES EACH COLUMN MESH SIT WHERE ITS MANIFEST SAYS?\n")
        print("    %-7s %9s %9s %9s  %s"
              % ("sector", "glb z", "manifest", "today", "verdict"))
        mismatch, stale = [], []
        for c in rows:
            if not c["have_glb"]:
                print("    %-7s %9s %9s %9s  NO MESH"
                      % (c["sector"], "-", "-", "-"))
                mismatch.append(c["sector"])
                continue
            zb = glb_bounds(c["glb"])[2][2]
            mid = 0.5 * (zb[0] + zb[1])
            if not c["have_manifest_row"]:
                verdict = "NO MANIFEST ROW"
                mismatch.append(c["sector"])
            elif abs(mid - c["manifest_z_m"]) > 2.0:
                verdict = "MANIFEST DOES NOT DESCRIBE THE MESH"
                mismatch.append(c["sector"])
            elif c["stale"]:
                verdict = ("STALE -- built %.0f m from where it would go now"
                           % abs(c["derived_z_m"] - c["manifest_z_m"]))
                stale.append(c["sector"])
            else:
                verdict = "ok"
            print("    %-7s %9.0f %9s %9.0f  %s"
                  % (c["sector"], mid,
                     "-" if c["manifest_z_m"] is None
                     else "%.0f" % c["manifest_z_m"],
                     c["derived_z_m"], verdict))
        if mismatch:
            print("\n  %d MESH(ES) NOT DESCRIBED BY THE MANIFEST: %s -- the "
                  "bake cannot rebuild their\n  collision and will refuse. Run "
                  "tools/export_station.py." % (len(mismatch),
                                                ", ".join(mismatch)))
        if stale:
            print("\n  %d MESH(ES) AT A PROVISIONAL PLACEMENT: %s. "
                  "tools/build_world.py exports the\n  columns at step 1 and "
                  "bakes the deck cells column_site measures against at step "
                  "3,\n  so a fresh checkout places them before it can know "
                  "where the floor is." % (len(stale), ", ".join(stale)))
        if not mismatch and not stale:
            print("\n  every column mesh sits where its manifest says, at the "
                  "z column_site would choose today")
        return 1 if (mismatch or stale) else 0

    if a.gate_placement:
        # THE OTHER HALF OF `--verify`, AND THEY ARE NOT THE SAME QUESTION.
        # `--verify` scores the cells that were BAKED, so it cannot answer
        # until an hours-long export and a bake have run, and it goes on
        # reporting the old placement until they do. This scores the placement
        # `export_station.py` WILL use, in seconds, off the same deck cells --
        # so a bad column is caught before the build rather than after it.
        import column_site as CS                                # noqa: PLC0415
        return CS.main(["--gate", "--report"]
                       + (["--legacy"] if a.legacy else [])
                       + (["--sector", a.sector] if a.sector else [])
                       + ["--cells", a.cells, "--near", str(a.near)])

    if a.verify:
        rows, bad = verify(near_m=a.near, sector=a.sector or None)
        if not rows:
            print("no column cell sets in %s -- run the bake first"
                  % os.path.relpath(CELLS, ROOT))
            return 1
        print_verify(rows, bad, a.near, len(deck_cell_rows()))
        return 1 if bad else 0

    work = list(columns(legacy=a.legacy, site_source=a.site_from,
                        cells_dir=a.cells))
    if a.sector:
        work = [c for c in work if c["sector"] == a.sector]
    if not work:
        print("no columns to bake")
        return 1

    print("\nBAKE THE TRANSIT COLUMNS\n")
    print("  %d column(s); %d have a mesh on disk; placement from %s"
          % (len(work), sum(1 for c in work if c["have_glb"]), a.site_from))
    print("\n    %-7s %9s %9s %9s  %s"
          % ("sector", "angle", "z (build)", "z (today)", "placement source"))
    for c in work:
        print("    %-7s %9.2f %9.0f %9.0f  %s%s"
              % (c["sector"], c["angle_deg"], c["z_m"], c["derived_z_m"],
                 c["placement_source"][:58],
                 "   <- STALE MESH" if c["stale"] else ""))
    if not any(c["have_manifest_row"] for c in work):
        print("\n    no station_manifest.json column rows -- falling back to "
              "column_site for every one of them.\n    Run "
              "tools/export_station.py; a placement derived here is a second "
              "opinion about a mesh that already exists.")
    if a.dry_run:
        for c in work:
            print("     column_%-7s rings %s at %.2f deg, z %.1f%s%s"
                  % (c["sector"], c["rings"], c["angle_deg"], c["z_m"],
                     "" if c["have_glb"] else "   -- NO MESH",
                     "" if not already_baked(c["sector"]) else "   -- baked"))
        return 0

    work_dir = tempfile.mkdtemp(prefix="bake_columns_")
    reps = []
    try:
        for i, c in enumerate(work, 1):
            sec = c["sector"]
            if not c["have_glb"]:
                reps.append({"sector": sec, "ok": False,
                             "why": "no column_%s.glb -- run "
                                    "tools/export_station.py" % sec})
                print("  [%d/%d] %-7s SKIPPED -- no mesh" % (i, len(work), sec))
                continue
            if already_baked(sec) and not a.force:
                print("  [%d/%d] %-7s already baked -- --force to redo"
                      % (i, len(work), sec))
                reps.append({"sector": sec, "ok": True, "skipped": True})
                continue
            rep = bake_one(c, work_dir, a.timeout, quiet=not a.engine_log)
            reps.append(rep)
            if rep["ok"]:
                print("  [%d/%d] %-7s %d cell(s), %s tri render / %s collision,"
                      " %d landings over %.1f m of RADIUS "
                      "(r %.1f-%.1f), z %.1f, %.2f MB, %.0f s"
                      % (i, len(work), sec, rep["cells"],
                         "{:,}".format(rep["cell_tris"]),
                         "{:,}".format(rep["cell_col_tris"]),
                         rep["landings"], rep["rise_m"],
                         rep["r_m"][0], rep["r_m"][1], rep["z_m"][0],
                         rep["mb"], rep["seconds"]))
                d = rep["deck_row"]
                print("           baked against %s (%s) r=%.2f cell_deg=%.0f%s"
                      % (d["id"], d["label"], d["floor_r_m"], d["cell_deg"],
                         "" if d["one_arc_cell"] else
                         "  -- no grid keeps this angle in one cell, so the "
                         "shaft comes out in two halves"))
            else:
                print("  [%d/%d] %-7s FAILED -- %s"
                      % (i, len(work), sec, rep.get("why", "?")))
                for ln in rep.get("engine", ()):
                    print("           | " + ln[:140])
    finally:
        if a.keep_work:
            print("\n  work directory kept: %s" % work_dir)
        else:
            shutil.rmtree(work_dir, ignore_errors=True)

    good = [r for r in reps if r.get("ok")]
    fresh = [r for r in good if not r.get("skipped")]
    print("\n  BAKED %d of %d columns (%d already on disk), %s render "
          "triangles in %d cells"
          % (len(fresh), len(work), len(good) - len(fresh),
             "{:,}".format(sum(r.get("cell_tris", 0) for r in fresh)),
             sum(r.get("cells", 0) for r in fresh)))
    print("  -> %s/column_*_cells.json, which tools/merge_cells.py globs"
          % os.path.relpath(CELLS, ROOT))

    # AND THE OTHER QUESTION, ALWAYS, because they are not the same question.
    # `--cells` moves the floor table `column_site` measures against, not the
    # place cells are written to and not the table this scores them on; the
    # baked columns are always in CELLS and are always judged against the decks
    # beside them.
    rows, bad = verify(near_m=a.near)
    if rows:
        print_verify(rows, bad, a.near, len(deck_cell_rows()))

    # AND A THIRD, WHICH THE OTHER TWO CANNOT ASK. `--verify` scores the cells
    # that exist; the placement gate scores where a column WOULD go. Neither
    # notices that the mesh on disk was built at a z nobody would choose today,
    # because both are right about their own question -- the exact shape of
    # defect `column_site.py` was written to close, arriving one level up.
    #
    # THE ARTEFACTS ARE PRODUCED AND THE DEFECT IS REPORTED. Run 5 of the
    # Windows build shipped nothing because this file refused; refusing is not
    # what protects a player, matching the collision to the render is, and that
    # is done above. This is the honest exit code over the top of it.
    stale = [c for c in work if c["stale"]]
    if stale:
        print("\n  %d COLUMN MESH(ES) ARE AT A PROVISIONAL PLACEMENT:" % len(stale))
        for c in stale:
            print("    column_%-7s mesh built at z=%.0f, per %s"
                  % (c["sector"], c["manifest_z_m"],
                     os.path.basename(STATION_MANIFEST)))
            print("    %-14s measured today: z=%.0f -- %.0f m away, %s"
                  % ("", c["derived_z_m"],
                     abs(c["derived_z_m"] - c["manifest_z_m"]),
                     c["derived_source"]))
            print("    %-14s rebuilt here at z=%.0f, from %s"
                  % ("", c["z_m"], c["placement_source"][:70]))
        print("    The collision baked above MATCHES the render mesh, which is "
              "this file's job. What is\n    wrong is upstream: "
              "tools/build_world.py runs tools/export_station.py at step 1 and\n"
              "    tools/bake_station.py at step 3, so the export places its "
              "columns before the deck\n    cells column_site measures against "
              "exist. Re-run tools/export_station.py now that\n    they do, "
              "then this file with --force.")
    return 0 if (len(good) == len(work) and not stale) else 1


if __name__ == "__main__":
    sys.exit(main())
