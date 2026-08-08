#!/usr/bin/env python3
"""CUT THE HABITAT DRUM INTO STREAMING CELLS -- it ships as ONE cell of 1.59 M.

`tools/bake_station.py` bakes every deck with `stream.gd::bake()`'s DEFAULT
axial band, which is `cell_manifest.json`'s `deck_table[<deck>].cell_length_m`.
For the drum that row reads

    {"id": "green.open.d0", "cells": 0, "cell_deg": 360.0,
     "cell_length_m": 0.0, "sight_line_m": 0.0, "cell_triangles": 0}

-- all four zero, because `station/interior.ring_cells` derives them from a ring
corridor and the drum is an open barrel with no corridor. `bake()` reads
`cell_length_m == 0` as its ONE-DIMENSIONAL CONTROL ("Every cell runs the deck's
whole axial extent, which is the defect INV-610 records"), so the whole habitat
drum comes out as a single cell:

    green_1_0_c00   0-360 deg   z 3790.5-6473.5   1,585,762 tri   636,596 col

That is **8.81x the whole `budget.CELLS["resident_tris"]` allowance of 180,000
and 26.4x the 60,000 per-cell one**, in a unit the streamer can neither split
nor partially page: `stream.gd` loads and frees whole cells. It is the single
worst cell on the station by a factor of 5.2 over the next one, and it is the
reason the packaged build's performance dimension scores 2 -- the standard's
PERFORMANCE 3 asks for "worst case measured and inside budget", and the worst
case is measured and is 8.81x outside.

    python3 tools/bake_drum.py                  # --plan: derive the band, no engine
    python3 tools/bake_drum.py --axis           # WHICH AXIS IS SAFE, with its control
    python3 tools/bake_drum.py --seam           # can a player fall through a cut?
    python3 tools/bake_drum.py --bake           # run Godot, write the cells
    python3 tools/bake_drum.py --selftest       # every cheap check, exits nonzero

===========================================================================
1. WHICH AXIS IS SAFE, ESTABLISHED BEFORE CUTTING AND NOT AFTER
===========================================================================

`tools/bake_columns.py` records the case that makes this a real question:
`stream.gd::bake()` assigns each triangle **whole** to the cell its centroid
falls in and never cuts one -- that is the property that makes the bake
lossless. So a surface built from a few enormous triangles lands entirely in
ONE cell, and every other cell along that axis has nothing there at all. For a
lift column, six collision triangles of 172 span the shaft's whole 67.1 m rise,
so a split along the rise leaves an open shaft: no wall, no overhead, no pit
floor, and a body walks out of the side into vacuum.

**THE DRUM IS ALMOST THE OPPOSITE CASE, AND THE "ALMOST" IS MEASURED RATHER
THAN ASSUMED.** The question is not "how big is the biggest triangle" -- it is
"how big is the biggest triangle **a foot can stand on**", because a decorative
triangle that lands in the wrong cell is a pop and a floor triangle that does is
a fall. `--axis` finds the load-bearing set the way `export_drum._floor_probe`
does -- by casting radial rays and recording which group each one lands on, so
the answer is a measurement of the shipped collision mesh and not a list of
names -- and then reports the widest per-triangle span of that set along each
candidate axis. Measured on the shipped `green_1_0_collision.glb`, 720 casts,
720 of 720 finding ground, 15 groups carrying it, 619,556 triangles:

    axis      widest load-bearing tri   which group        of the drum's extent
    z                       221.94 m    drum_solid         8.3% of 2,682.9 m
    arc                      22.00 deg  townscape_solid    6.1% of 360
    radius                   40.57 m    townscape_solid    --
    z, GROUND ONLY            4.04 m    ground_*           0.15%

**The derived precondition is `widest load-bearing span <= 2 x the residency
radius`**, and it is arithmetic rather than taste: a triangle is written whole
into the cell its CENTROID falls in, so a body standing on the far end of one is
up to half its span from that cell, and past the residency radius the cell
holding the thing under the body is not loaded. At the shipped 98.9 m radius the
bound is 197.8 m.

**THE DRUM FAILS IT, BY 24.1 M, ON 8 TRIANGLES OF 619,556** -- the six faces of
one 221.94 m hedge run at r 274.40-276.87, z 5389.6-5611.6, which
`drum_dressing.ribbon_boxes` emits as a single oriented box per merged run. The
consequence is bounded and is NOT a fall: the hedge is 2.47 m of solid standing
ON the ground, and the ground under it is `ground_*`, whose widest triangle is
4.04 m and therefore always in a resident band. A body at the extreme end of
that one run steps 2.47 m down onto grass. `--seam` separates those two outcomes
explicitly and reports them separately, because "would fall" and "the hedge
under you is not loaded" are different bugs and only one of them is fatal.
Measured, 3,000 probes at the 33 m band and the shipped 98.9 m radius:
**3,000 stood on resident ground, 0 stepped down, 0 fell.** The control, at
residency radius 0, loses 100 of the same 3,000 -- 76 falls and 24 step-downs --
which is what makes the pass mean something.

Everything else is a **protrusion, not a gap**: the triangle is still written,
into the neighbour, and the union of the cells is the source exactly.
`--axis` runs the same measurement on `column_red.glb` as its control, where the
load-bearing span is 215.33 m of a 215.35 m rise -- 0.9999, one triangle IS the
axis -- so the measurement is shown able to say no.

**Z IS CHOSEN OVER ARC, AND NOT ONLY BECAUSE THE DRUM IS LONGER THAN IT IS
ROUND** (2,682.7 m against 1,748.6 m of circumference at the floor). The
deciding fact is that a barrel is walked on the INSIDE. On a ring deck the
station's own curvature occludes at `interior.sight_line`, which is why a ring
cell may be an arc; on the concave side of a drum nothing occludes and the far
wall is 556 m of clear air away, so an arc cut removes geometry the player is
looking straight at. A cut across the axis removes geometry that is 100 m or
more up a barrel whose own townscape, foliage and end cap already stand in the
way. **`bake()` cannot cut the drum on arc anyway** -- `cell_deg` comes from the
deck row and there is no override -- and that limit is what section 4 is about.

===========================================================================
2. THE BAND IS DERIVED FROM THE BUDGET, WITH NO FREE PARAMETER
===========================================================================

Three numbers decide it and all three are `station/budget.py`'s:

  `CELLS["cell_tris"]`      60,000   no cell may exceed it
  `CELLS["resident_tris"]` 180,000   nor may the set resident at once
  `DRAW["max_per_frame"]`   1,041   derived in budget.py from 4.17 ms of render
                                     thread at 4.0 us a call

and one number is read off the artefact rather than chosen: the **residency
radius the shipped manifest actually carries**, 98.9 m, which
`tools/merge_cells.py` takes as the MAX over 76 decks and which is therefore not
the drum's to set. `stream.gd::configure` keeps ONE global radius, so whatever
the drum's own manifest says, in the merged build every drum cell within 98.9 m
of the body is resident.

That radius is what makes this a two-sided optimum rather than "smaller is
better". Resident triangles fall as the band shrinks -- the resident slab
approaches 2 x 98.9 m of drum however finely it is cut -- but resident **draw
calls** rise, because every cell re-instances each of the drum's 403 groups it
holds any triangle of. Measured over the shipped mesh:

    band   cells  worst cell  worst resident  resident instances
     11 m    253      36,193         221,049       1,488  OVER DRAW
     20 m    139      45,878         230,345       1,043  OVER DRAW
     33 m     85      58,297         232,586         795
     40 m     70      58,634         240,622         751
     50 m     56      85,498         259,119         621  OVER CELL
     99 m     29     111,582         285,033         483  OVER CELL

So the rule is stated once and has nothing to tune: **the band that minimises
worst-case resident triangles, subject to no cell exceeding `cell_tris` and no
resident set exceeding `DRAW["max_per_frame"]` instances.** On the shipped drum
that is **33 m, 85 cells**. `--curve` prints the whole search so the choice is
visible, and `--band` overrides it for an experiment. -- INV-1249

===========================================================================
3. THE RESIDENCY BLOCK HAS TO BE WRITTEN, BECAUSE THE DECK ROW CANNOT
===========================================================================

`bake()` copies `radius_m` straight from `sight_line_m`, which is **0** for the
drum. `stream.gd::configure` refuses a manifest whose radius is not positive --
*"manifest carries no residency radius or budget"* -- and returns false, at
which point the game loads NOTHING. So `green_1_0_cells.json` as shipped is
**not loadable on its own**, and the only reason the packaged build works at all
is that `merge_cells.py` takes the max across decks and some other deck supplies
a positive number. That is a live latent defect, not a hypothetical: point
`boot.json` at the drum's own cell set and the build is black.

This file therefore writes the drum's residency itself, derived and with the
derivation in the artefact:

    radius_m        = the band -- one band of lead time, which at `player.gd`'s
                      8.0 m/s sprint is 4.1 s to load the next cell. There is no
                      sight line to use: curvature does not occlude on the
                      concave side of a barrel, which is exactly why
                      `interior.ring_cells` wrote 0.
    free_radius_m   = 2 x the band, so the deadband is one whole cell -- the
                      same shape as `bake()`'s `max(sight, cell_length)` rule
                      and the same reason: a body that turns round on a
                      threshold must not outrun the reload.
    cell_length_m   = the band.

`merge_cells.py` still takes the MAX, so these numbers do not lower the shipped
global radius; they make the drum's own manifest loadable and they state what
the drum would ask for. -- INV-1250

===========================================================================
4. WHAT THIS DOES NOT REACH, MEASURED RATHER THAN ROUNDED AWAY
===========================================================================

**The cut takes the drum's worst cell from 26.43x the per-cell budget to 0.97x
-- that one CLEARS -- and its worst resident set from 8.81x to 1.29x, which does
not, and no band can.** The floor is arithmetic: at the shipped 98.9 m
radius the resident set is always at least a 198 m slab of drum, and the 198 m
slab around Earhart's and Fresh Air (z 4789-4839, where two bespoke interiors
put 26,748 triangles of clutter into one 50 m band) holds ~215,000 triangles
however the boundaries fall. Every band from 15 m to 100 m was searched; the
best is 221,049 at 11 m, which then breaks the draw-call budget instead.

WHAT THE BAKE ACTUALLY PRODUCED, from the engine's own log rather than from the
plan above -- `85 cells (0 arc x 85 band), 1585762 triangles total (source had
1585762)`, so the cut is lossless, and `biggest cell green_1_0_c00z29 at 58300
tri = 0.97x cell_tris; 0 of 85 cells over cell_tris`. 129.2 MB against the one
cell's 133.5 MB, in 13 s. The predicted worst cell was 58,297 against the
engine's 58,300: three triangles, from `_split` binning float32 vertices where
this file bins their float64 centroids.

    the drum                        as shipped        cut at 33 m
    cells                                    1                 85
    worst cell                       1,585,762             58,300
                                    26.43x cell        0.97x cell
    drum-only resident, worst        1,585,762            232,586
                                     8.81x res          1.29x res
    drum-only resident, median       1,585,762            131,557
    a body in the Garden, whole      1,799,343    worst 1,355,026
      station, at the shipped                    median   173,013
      98.9 m radius                                    INSIDE budget

and on the merged 76-deck manifest the station's worst co-resident set falls
from **4,477,402 (24.87x) to 2,895,463 (16.09x)** -- see
`tools/merge_cells.py --budget`, whose docstring records why the Garden was
resident from a Grey corridor 171 m away and what is left once it is not.

**What DOES clear the drum's own 1.29x is a second axis, and it is measured
here so the next session does not have to re-derive it.** Simulating the same
bake on an arc x z grid with the same residency metric:

    cell_deg  band     cells   worst cell   worst resident
      360      33 m       85       58,297          232,586   <- what this ships
       45     100 m      224       69,148          184,432
       20     100 m      504       49,659          165,516   <- clears both
       20      50 m    1,008       44,692          146,187

`cell_deg = 20, band = 100 m` puts the drum inside **both** budgets: 0.83x per
cell and 0.92x resident. It cannot be baked from here. `bake()` reads
`cell_deg` from `cell_manifest.json`'s deck row and offers no `--cell-deg`
override, and the drum's row is written by `station/interior.ring_cells`, which
returns 360 because the drum is not a ring. Two one-line changes reach it and
both are in files this file may not touch:

  * `godot/scripts/stream.gd::bake()` -- accept `--cell-deg` beside the
    `--z-band` it already accepts, three lines below `cell_deg` is read.
  * or `station/interior.py` -- give the drum row a real `cell_deg`.

Stated here, with its numbers, because a lever that is measured and named is
worth more than a lever that is guessed at later. -- INV-1251
"""

import argparse
import glob
import json
import math
import os
import struct
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

SRC = os.path.join(ROOT, "station", "generated", "scene", "station")
CELLS = os.path.join(SRC, "cells")
STEM = "green_1_0"
SECTOR, RING, DECK = "green", 1, 0

# The drum's deck row gives the band grid its origin, exactly as it does for
# every other deck: `bake()` anchors bands at `row["z0"]` so a band index is a
# property of the deck and not of this build's extent.
Z_ORIGIN = 3839.0

# The search range for the band, in metres. The low end is where the draw-call
# budget has already been broken by a wide margin; the high end is past the
# point where one cell exceeds the whole resident allowance.
BAND_LO, BAND_HI = 15, 100


# ===========================================================================
# GLB -- positions and indices only, vectorised
# ===========================================================================
#
# `tools/glb_to_obj.py::read_glb` is the project's reader and it is per-element
# Python. This file asks a whole-mesh question of 2.2 M triangles and would
# spend minutes in `struct.unpack_from`; the accessors are contiguous typed
# arrays, so `np.frombuffer` reads them without a loop. The two agree and
# `_selftest` asserts that they do on a real file rather than trusting it.

_CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16,
       5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _accessor(j, blob, idx):
    a = j["accessors"][idx]
    bv = j["bufferViews"][a["bufferView"]]
    dt = _CT[a["componentType"]]
    n = _NC[a["type"]]
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    packed = np.dtype(dt).itemsize * n
    stride = bv.get("byteStride") or packed
    cnt = a["count"]
    if stride == packed:
        return np.frombuffer(blob, dtype=dt, count=cnt * n,
                             offset=base).reshape(cnt, n)
    raw = np.frombuffer(blob, dtype=np.uint8, count=stride * cnt, offset=base)
    raw = raw.reshape(cnt, stride)[:, :packed]
    return np.ascontiguousarray(raw).view(dt).reshape(cnt, n)


def read_glb(path):
    """-> [(group_name, verts (N,3) float64, tris (M,3) int64)] in world space.

    NODE TRANSFORMS ARE REFUSED RATHER THAN IGNORED, for the reason
    `glb_to_obj.read_glb` gives: these decks are authored in world space and
    silently dropping a matrix would place the floor somewhere the player is
    not.
    """
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"glTF":
        raise SystemExit("%s is not a GLB" % path)
    jlen = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + jlen])
    p = 20 + jlen
    blen, ctype = struct.unpack("<II", d[p:p + 8])
    if ctype != 0x004E4942:
        raise SystemExit("%s: second chunk is not BIN" % path)
    blob = d[p + 8:p + 8 + blen]
    for nd in j.get("nodes", []):
        for k in ("matrix", "translation", "rotation", "scale"):
            if k in nd:
                raise SystemExit("%s: node %r carries a %s -- this reader is "
                                 "world-space only" % (path, nd.get("name"), k))
    named = {}
    for nd in j.get("nodes", []):
        if "mesh" in nd:
            named.setdefault(nd["mesh"], nd.get("name", ""))
    out = []
    for mi, m in enumerate(j["meshes"]):
        base = m.get("name") or named.get(mi) or "mesh%d" % mi
        for pi, prim in enumerate(m["primitives"]):
            v = _accessor(j, blob, prim["attributes"]["POSITION"]).astype(float)
            t = _accessor(j, blob, prim["indices"]).astype(np.int64).reshape(-1, 3)
            out.append((base if len(m["primitives"]) == 1
                        else "%s#%d" % (base, pi), v, t))
    return out


def flatten(gs):
    """[(name, v, t)] -> (verts list, tris list, per-triangle group name list).

    The list-of-tuples form `station/collision._down_index` and `_ray_tri` take.
    """
    V, T, G = [], [], []
    for nm, v, t in gs:
        off = len(V)
        V.extend(map(tuple, v))
        T.extend((int(a) + off, int(b) + off, int(c) + off) for a, b, c in t)
        G.extend([nm] * len(t))
    return V, T, G


# ===========================================================================
# SPANS -- how far one triangle reaches along each candidate axis
# ===========================================================================

def spans(v, t):
    """-> dict of per-triangle extents for one group, along all three axes."""
    x, y, z = v[:, 0][t], v[:, 1][t], v[:, 2][t]
    r = np.hypot(x, y)
    a = np.degrees(np.arctan2(y, x)) % 360.0
    s = np.sort(a, axis=1)
    gaps = np.column_stack([s[:, 1] - s[:, 0], s[:, 2] - s[:, 1],
                            360.0 + s[:, 0] - s[:, 2]])
    return {"n": len(t),
            "dz": z.max(1) - z.min(1),
            "darc": 360.0 - gaps.max(1),
            "dr": r.max(1) - r.min(1),
            "z0": float(z.min()), "z1": float(z.max()),
            "r0": float(r.min()), "r1": float(r.max())}


def load_bearing(col_path, samples=720, seed_stride=0.61803398875):
    """The groups a foot actually meets, MEASURED by casting at the mesh.

    Not a name list. `export_drum._floor_probe` asks the same question of the
    same file -- "can a body stand on this shell" -- by casting radially from
    the axis outward, which is what down is on a spun barrel. This keeps the
    group each cast landed on, because the axis question is about the widest
    triangle a foot can stand on and not the widest triangle.
    """
    import collision as C                                      # noqa: PLC0415
    import drum_ground as dg                                   # noqa: PLC0415
    V, T, G = flatten(read_glb(col_path))
    bins, nbin = C._down_index(V, T)
    top = dg.FLOOR_R - 40.0
    hit, miss = {}, 0
    for i in range(samples):
        ang = (i * 360.0 / samples) % 360.0
        z = dg.Z0 + (dg.Z1 - dg.Z0) * ((i * seed_stride) % 1.0)
        a = math.radians(ang)
        b = int((math.atan2(math.sin(a), math.cos(a)) + math.pi)
                / (2 * math.pi) * nbin) % nbin
        o = (top * math.cos(a), top * math.sin(a), z)
        d = (math.cos(a), math.sin(a), 0.0)
        best, best_t = None, None
        for z0, z1, tri in bins.get(b, ()):
            if z < z0 - 1e-6 or z > z1 + 1e-6:
                continue
            h = C._ray_tri(o, d, V[tri[0]], V[tri[1]], V[tri[2]])
            if h is not None and (best is None or h < best):
                best, best_t = h, tri
        if best is None:
            miss += 1
            continue
        # which triangle index -- T is the same order the index was built from
        hit[best_t] = hit.get(best_t, 0) + 1
    names = {}
    idx = {tuple(tri): k for k, tri in enumerate(T)}
    for tri, n in hit.items():
        names[G[idx[tuple(tri)]]] = names.get(G[idx[tuple(tri)]], 0) + n
    return names, samples - miss, miss


def axis_report(glb, col, control=None, radius=98.9, out=print):
    """The bake_columns question, asked of the drum. -> dict."""
    gs = read_glb(col)
    hit_names, nhit, nmiss = load_bearing(col)
    out("load-bearing set MEASURED by %d radial casts at %s"
        % (nhit + nmiss, os.path.basename(col)))
    out("  %d cast(s) found ground, %d found nothing; %d distinct group(s) "
        "carry it" % (nhit, nmiss, len(hit_names)))
    worst = {"z": (0.0, ""), "arc": (0.0, ""), "r": (0.0, "")}
    tot = 0
    ground = 0.0
    over = []                      # triangles wider than 2 x the radius
    for nm, v, t in gs:
        if nm not in hit_names:
            continue
        s = spans(v, t)
        tot += s["n"]
        if nm.startswith("ground_"):
            ground = max(ground, float(s["dz"].max()))
        n_over = int((s["dz"] > 2.0 * radius).sum())
        if n_over:
            k = int(np.argmax(s["dz"]))
            z = v[:, 2][t][k]
            r = np.hypot(v[:, 0][t], v[:, 1][t])[k]
            over.append((nm, n_over, s["n"], float(s["dz"][k]),
                         float(z.min()), float(z.max()),
                         float(r.min()), float(r.max())))
        for k2, key in (("z", "dz"), ("arc", "darc"), ("r", "dr")):
            m = float(s[key].max())
            if m > worst[k2][0]:
                worst[k2] = (m, nm)
    zext = max(float(spans(v, t)["z1"]) for _n, v, t in gs) - \
        min(float(spans(v, t)["z0"]) for _n, v, t in gs)
    out("  %d load-bearing triangles; widest ONE of them spans" % tot)
    out("    z      %8.2f m    (%s)  = %.4f of the drum's %.1f m"
        % (worst["z"][0], worst["z"][1], worst["z"][0] / max(zext, 1e-9), zext))
    out("    arc    %8.2f deg  (%s)  = %.4f of 360"
        % (worst["arc"][0], worst["arc"][1], worst["arc"][0] / 360.0))
    out("    radius %8.2f m    (%s)" % (worst["r"][0], worst["r"][1]))
    out("    z, GROUND ONLY %.2f m -- drum_ground's own lattice stride"
        % ground)
    # THE PRECONDITION, DERIVED. A triangle goes whole into the cell its
    # centroid falls in, so a body on the far end of one is up to half its span
    # from that cell; past the residency radius the cell holding the thing under
    # the body is not loaded.
    out("  precondition: a load-bearing span must not exceed 2 x the residency "
        "radius = %.1f m" % (2.0 * radius))
    if over:
        for nm, n_over, n_all, dz, z0, z1, r0, r1 in over:
            out("    VIOLATED by %d of %d triangles in %s -- widest %.2f m, "
                "z %.1f-%.1f, r %.2f-%.2f" % (n_over, n_all, nm, dz, z0, z1,
                                              r0, r1))
        out("    --seam reports whether that is a FALL or a step down onto "
            "whatever is under it")
    else:
        out("    HELD by every load-bearing group")
    res = {"z_m": worst["z"][0], "arc_deg": worst["arc"][0],
           "r_m": worst["r"][0], "extent_z_m": zext, "ground_z_m": ground,
           "load_bearing_tris": tot, "groups": len(hit_names),
           "over_2r": [o[0] for o in over],
           "over_2r_tris": sum(o[1] for o in over)}
    if control:
        out("")
        out("CONTROL -- the same measurement on %s, where bake_columns.py "
            "records that a split along the rise leaves an open shaft:"
            % os.path.basename(control))
        cgs = read_glb(control)
        cz = max(float(spans(v, t)["r1"]) for _n, v, t in cgs) - \
            min(float(spans(v, t)["r0"]) for _n, v, t in cgs)
        cw = max(float(spans(v, t)["dr"].max()) for _n, v, t in cgs)
        out("    radius %8.2f m of a %.2f m rise = %.4f -- %s"
            % (cw, cz, cw / max(cz, 1e-9),
               "REFUSED: one triangle IS the whole axis"
               if cw / max(cz, 1e-9) > 0.5 else "would pass"))
        res["control_ratio"] = cw / max(cz, 1e-9)
    return res


# ===========================================================================
# THE BAND -- derived from budget.py and from the shipped residency radius
# ===========================================================================

def shipped_radius(cells_dir=CELLS, default=98.9):
    """The residency radius the MERGED manifest actually carries.

    Read rather than assumed, because it is `merge_cells.py`'s max over every
    deck and therefore moves when any deck does. Falls back to the max over the
    per-deck sets, then to the recorded shipped value, and says which it used.
    """
    p = os.path.join(cells_dir, "station_cells.json")
    if os.path.exists(p):
        with open(p) as f:
            r = float(json.load(f).get("residency", {}).get("radius_m", 0.0))
        if r > 0.0:
            return r, "the merged manifest %s" % os.path.relpath(p, ROOT)
    best = 0.0
    for q in glob.glob(os.path.join(cells_dir, "*_cells.json")):
        with open(q) as f:
            best = max(best, float(json.load(f).get("residency", {})
                                   .get("radius_m", 0.0)))
    if best > 0.0:
        return best, "the max over the per-deck cell sets on disk"
    return default, ("no cell set on disk -- the value the shipped package "
                     "carries")


def band_costs(zc, groups_of, band, radius):
    """Cost one candidate band. -> (cells, worst cell, worst resident tris,
    worst resident instances, worst resident cells)."""
    b = np.floor((zc - Z_ORIGIN) / band).astype(np.int64)
    lo, hi = int(b.min()), int(b.max())
    n = hi - lo + 1
    tri = np.bincount(b - lo, minlength=n)
    inst = np.zeros(n, dtype=np.int64)
    for gb in groups_of:
        u = np.unique(np.floor((gb - Z_ORIGIN) / band).astype(np.int64)) - lo
        inst[u] += 1
    edges = Z_ORIGIN + np.arange(lo, hi + 2) * band
    wt = wi = wc = 0
    for p in np.arange(edges[0], edges[-1], 2.0):
        gap = np.maximum(0.0, np.maximum(edges[:-1] - p, p - edges[1:]))
        m = gap <= radius
        wt = max(wt, int(tri[m].sum()))
        wi = max(wi, int(inst[m].sum()))
        wc = max(wc, int(m.sum()))
    return n, int(tri.max()), wt, wi, wc


def derive_band(glb, radius, lo=BAND_LO, hi=BAND_HI, curve=False, out=print):
    """The band that minimises worst-case resident triangles inside both hard
    budgets. -> (band, rows). Raises if nothing in the range is feasible."""
    import budget as B                                          # noqa: PLC0415
    gs = read_glb(glb)
    zc = np.concatenate([v[:, 2][t].mean(1) for _n, v, t in gs])
    groups_of = [v[:, 2][t].mean(1) for _n, v, t in gs]
    rows = []
    for band in range(int(lo), int(hi) + 1):
        n, mx, wt, wi, wc = band_costs(zc, groups_of, float(band), radius)
        rows.append({"band_m": band, "cells": n, "worst_cell": mx,
                     "worst_resident": wt, "worst_instances": wi,
                     "resident_cells": wc,
                     "over_cell": mx > B.CELLS["cell_tris"],
                     "over_draw": wi > B.DRAW["max_per_frame"]})
    feas = [r for r in rows if not r["over_cell"] and not r["over_draw"]]
    if not feas:
        raise SystemExit("bake_drum: no band in %d-%d m fits both budgets"
                         % (lo, hi))
    best = min(feas, key=lambda r: r["worst_resident"])
    if curve:
        out("  %5s %6s %11s %11s %10s %6s  %s"
            % ("band", "cells", "worst cell", "resident", "instances",
               "cells", "verdict"))
        for r in rows:
            if r["band_m"] % 5 and r is not best:
                continue
            why = ("OVER cell_tris" if r["over_cell"] else
                   "OVER draw calls" if r["over_draw"] else "")
            out("  %5d %6d %11s %11s %10d %6d  %s%s"
                % (r["band_m"], r["cells"], "{:,}".format(r["worst_cell"]),
                   "{:,}".format(r["worst_resident"]), r["worst_instances"],
                   r["resident_cells"], why,
                   "  <- CHOSEN" if r is best else ""))
    return best, rows


# ===========================================================================
# THE SEAM -- can a player fall through a cut?
# ===========================================================================

def seam_probe(col_path, band, radius, samples=2000, out=print):
    """For every probe: is the ground triangle under it in a RESIDENT cell?

    THE QUESTION A TRIANGLE COUNT CANNOT ANSWER. The bake is lossless -- the
    union of the cells is the source exactly -- so no cut can delete floor. What
    a cut CAN do is put the floor under your feet in a cell that is not
    resident, and that is a fall rather than a pop. The probe casts as a foot
    does, finds the triangle it lands on, computes the band that triangle's
    CENTROID falls in (which is where `stream.gd::_split` will put it) and the
    band the body is standing in, and asks whether the streamer would have the
    first one loaded while the body is in the second.

    A FALL AND A STEP DOWN ARE DIFFERENT BUGS AND ARE COUNTED SEPARATELY. The
    probe keeps EVERY surface along the ray, not just the nearest, so when the
    surface a body is standing on is in an unloaded cell it can still say what
    is underneath: if a resident surface exists further out, the body drops onto
    it -- a hedge or a roof vanishing, which is bad and bounded -- and only when
    there is nothing resident at all has the body left the world.

    THE CONTROL IS `radius=0`, which makes only the body's own cell resident.
    Every triangle whose centroid crossed a boundary is then unloaded, and the
    count is how much floor that costs. It is not zero, which is what makes this
    measurement able to fail.
    """
    import collision as C                                       # noqa: PLC0415
    import drum_ground as dg                                    # noqa: PLC0415
    V, T, _G = flatten(read_glb(col_path))
    bins, nbin = C._down_index(V, T)
    top = dg.FLOOR_R - 40.0
    ok = miss = fall = step = 0
    worst = []
    for i in range(samples):
        ang = (i * 360.0 / samples * 7.0) % 360.0
        z = dg.Z0 + (dg.Z1 - dg.Z0) * ((i * 0.61803398875) % 1.0)
        a = math.radians(ang)
        b = int((math.atan2(math.sin(a), math.cos(a)) + math.pi)
                / (2 * math.pi) * nbin) % nbin
        o = (top * math.cos(a), top * math.sin(a), z)
        d = (math.cos(a), math.sin(a), 0.0)
        hits = []
        for z0, z1, tri in bins.get(b, ()):
            if z < z0 - 1e-6 or z > z1 + 1e-6:
                continue
            h = C._ray_tri(o, d, V[tri[0]], V[tri[1]], V[tri[2]])
            if h is None:
                continue
            cz = sum(V[k][2] for k in tri) / 3.0
            tri_band = math.floor((cz - Z_ORIGIN) / band)
            bz0 = Z_ORIGIN + tri_band * band
            # the gap `stream.gd::distance_to` computes for that cell
            gap = max(0.0, bz0 - z, z - (bz0 + band))
            hits.append((h, gap <= radius, int(tri_band), gap))
        if not hits:
            miss += 1
            continue
        hits.sort()
        if hits[0][1]:
            ok += 1
            continue
        res = [h for h in hits if h[1]]
        body_band = math.floor((z - Z_ORIGIN) / band)
        if res:
            step += 1
            if len(worst) < 6:
                worst.append(("STEP %.2f m down" % (res[0][0] - hits[0][0]),
                              round(ang, 2), round(z, 1), int(body_band),
                              hits[0][2], round(hits[0][3], 2)))
        else:
            fall += 1
            if len(worst) < 6:
                worst.append(("FALL, nothing resident", round(ang, 2),
                              round(z, 1), int(body_band), hits[0][2],
                              round(hits[0][3], 2)))
    out("  %d probes: %d stood on resident ground, %d would STEP DOWN onto a "
        "resident surface below, %d would FALL out of the world, %d found no "
        "ground at all" % (samples, ok, step, fall, miss))
    for w in worst:
        out("      %-24s angle %7.2f deg z %8.1f -- body in band %d, the "
            "surface it is on is in band %d, %.2f m away" % w)
    return {"samples": samples, "ok": ok, "step": step, "fall": fall,
            "no_ground": miss}


# ===========================================================================
# THE BAKE
# ===========================================================================

def godot_binary():
    import walkable as W                                        # noqa: PLC0415
    return W.godot_binary()


def bake(glb, col, band, radius, cells_out, timeout=1800, out=print):
    g = godot_binary()
    if g is None:
        out("no double-precision Godot binary. run: bash tools/build_godot.sh")
        return None
    os.makedirs(cells_out, exist_ok=True)
    # STALE CELLS ARE REMOVED FIRST, not left beside the new ones. The one-cell
    # bake writes `green_1_0_c00.scn`; a banded bake writes `..._c00z07.scn`, a
    # different name, so the 133 MB monolith would survive in the package as a
    # file nothing references -- and `merge_cells.py` globs manifests, not
    # meshes, so nothing would ever say so.
    stale = [p for p in glob.glob(os.path.join(cells_out, STEM + "_c*"))]
    for p in stale:
        os.remove(p)
    if stale:
        out("  removed %d stale cell file(s) from the previous bake"
            % len(stale))
    cmd = [g, "--headless", "--path", os.path.join(ROOT, "godot"),
           "res://scenes/walk.tscn", "--", "--bake-cells",
           "--glb=%s" % glb, "--collision=%s" % col,
           "--sector=%s" % SECTOR, "--ring-index=%d" % RING,
           "--deck-index=%d" % DECK, "--cell-id=%s" % STEM,
           "--z-band=%g" % band, "--cells-out=%s" % cells_out]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                       timeout=timeout)
    made = sorted(glob.glob(os.path.join(cells_out, STEM + "_c*.scn")))
    out("  godot exit %d in %.0f s, %d .scn written"
        % (r.returncode, time.time() - t0, len(made)))
    # THE CELLS ON DISK ARE THE VERDICT, NOT THE EXIT CODE -- bake_station.py's
    # rule, and it has already caught a bake that exited 0 having written
    # nothing.
    if r.returncode != 0 or not made:
        for ln in (r.stderr or r.stdout).splitlines()[-8:]:
            out("      " + ln)
        return None
    for ln in r.stdout.splitlines():
        if ln.startswith("bake: biggest cell") or "cells (" in ln:
            out("      " + ln)
    return patch_residency(os.path.join(cells_out, STEM + "_cells.json"),
                           band, radius, out=out)


def patch_residency(man_path, band, radius, out=print):
    """Write the residency the deck row could not supply. See section 3."""
    with open(man_path) as f:
        man = json.load(f)
    res = man.get("residency", {})
    before = float(res.get("radius_m", 0.0))
    res["radius_m"] = float(band)
    res["free_radius_m"] = float(2 * band)
    res["cell_length_m"] = float(band)
    res["radius_from"] = (
        "tools/bake_drum.py -- the band (%.0f m). The deck row's sight_line_m "
        "is 0 because curvature does not occlude on the concave side of a "
        "barrel, and configure() REFUSES a manifest whose radius is not "
        "positive. INV-1250" % band)
    res["free_from"] = (
        "2 x the band -- one whole cell of deadband, so a body that turns "
        "round on a threshold cannot outrun the reload. %.1f m = %.2f s at "
        "the shipped 8.0 m/s sprint" % (band, band / 8.0))
    res["shipped_radius_m"] = radius
    res["shipped_radius_note"] = (
        "the MERGED manifest's radius, which merge_cells.py takes as the max "
        "over every deck and which therefore governs in the packaged build "
        "whatever this row says. The band above was derived against it.")
    man["residency"] = res
    man["band_from"] = (
        "tools/bake_drum.py -- the band minimising worst-case resident "
        "triangles inside budget.CELLS['cell_tris'] and budget.DRAW"
        "['max_per_frame']. INV-1249")
    with open(man_path, "w") as f:
        json.dump(man, f, indent=2)
    out("  residency radius %.1f -> %.1f m (free %.1f m) in %s"
        % (before, float(band), float(2 * band),
           os.path.relpath(man_path, ROOT)))
    return man


def manifest_report(man, radius, out=print):
    """What the cells on disk actually are. Reads the artefact, not the plan."""
    import budget as B                                          # noqa: PLC0415
    cells = man.get("cells", [])
    if not cells:
        out("  NO CELLS")
        return {"cells": 0}
    tris = [int(c.get("tris", 0)) for c in cells]
    z0 = [float(c["arc"]["z0"]) for c in cells]
    z1 = [float(c["arc"]["z1"]) for c in cells]
    worst = 0
    for p in np.arange(min(z0), max(z1), 2.0):
        s = sum(t for t, a, b in zip(tris, z0, z1)
                if max(0.0, a - p, p - b) <= radius)
        worst = max(worst, int(s))
    out("  %d cells, worst %s tri (%.2fx cell_tris), worst co-resident %s tri "
        "(%.2fx resident_tris) at the shipped %.1f m radius"
        % (len(cells), "{:,}".format(max(tris)),
           max(tris) / B.CELLS["cell_tris"], "{:,}".format(worst),
           worst / B.CELLS["resident_tris"], radius))
    return {"cells": len(cells), "worst_cell": max(tris),
            "worst_resident": worst, "total": sum(tris)}


# ===========================================================================

def _selftest(src=SRC, cells_dir=CELLS, out=print):
    bad = []
    glb = os.path.join(src, STEM + ".glb")
    col = os.path.join(src, STEM + "_collision.glb")
    if not os.path.exists(glb):
        out("  NO DRUM MESH at %s -- run: python3 tools/export_drum.py" % glb)
        return 1

    # 1. the vectorised reader agrees with the project's own
    import glb_to_obj as G                                      # noqa: PLC0415
    small = min(glob.glob(os.path.join(src, "column_*.glb")) or [col],
                key=os.path.getsize)
    mine = read_glb(small)
    theirs = G.read_glb(small)
    if sum(len(t) for _n, _v, t in mine) != sum(len(t) for _n, _v, t in theirs):
        bad.append("read_glb disagrees with glb_to_obj.read_glb on %s"
                   % os.path.basename(small))
    else:
        out("  reader agrees with glb_to_obj on %s (%d tri)"
            % (os.path.basename(small), sum(len(t) for _n, _v, t in mine)))

    # 2. the band search is feasible and the objective is what it claims
    radius, why = shipped_radius(cells_dir)
    out("  residency radius %.1f m, from %s" % (radius, why))
    best, rows = derive_band(glb, radius)
    feas = [r for r in rows if not r["over_cell"] and not r["over_draw"]]
    if any(r["worst_resident"] < best["worst_resident"] for r in feas):
        bad.append("derive_band did not return the minimum")
    if not any(r["over_cell"] for r in rows):
        bad.append("no band in the range breaks cell_tris -- the search cannot "
                   "discriminate")
    if not any(r["over_draw"] for r in rows):
        bad.append("no band in the range breaks the draw budget -- the search "
                   "cannot discriminate")
    out("  band search: %d of %d candidates feasible, best %d m"
        % (len(feas), len(rows), best["band_m"]))

    # 3. THE AXIS MEASUREMENT MUST BE ABLE TO SAY NO. Run it on the case
    #    bake_columns.py documents as unsafe and require a refusal.
    ctrl = os.path.join(src, "column_red.glb")
    if os.path.exists(ctrl):
        cgs = read_glb(ctrl)
        ext = max(spans(v, t)["r1"] for _n, v, t in cgs) - \
            min(spans(v, t)["r0"] for _n, v, t in cgs)
        wid = max(float(spans(v, t)["dr"].max()) for _n, v, t in cgs)
        if wid / max(ext, 1e-9) < 0.5:
            bad.append("the axis control does not fire: column_red's widest "
                       "triangle is %.2f m of a %.2f m rise" % (wid, ext))
        else:
            out("  axis control fires: column_red spans %.2f m of its own "
                "%.2f m rise in ONE triangle" % (wid, ext))
    else:
        out("  axis control SKIPPED -- no column_red.glb on disk")

    for b in bad:
        out("  BAD: %s" % b)
    if bad:
        return 1
    out("\n  BAKE_DRUM SELFTEST OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=SRC, help="scene/station directory")
    ap.add_argument("--cells-out", default=CELLS)
    ap.add_argument("--band", type=float, default=0.0,
                    help="override the derived band, in metres")
    ap.add_argument("--radius", type=float, default=0.0,
                    help="override the residency radius the band is derived "
                         "against (default: read off the shipped manifest)")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--curve", action="store_true",
                    help="print the whole band search, not just its answer")
    ap.add_argument("--axis", action="store_true")
    ap.add_argument("--seam", action="store_true")
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--samples", type=int, default=2000)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args(argv)

    glb = os.path.join(a.src, STEM + ".glb")
    col = os.path.join(a.src, STEM + "_collision.glb")
    if a.selftest:
        return _selftest(a.src, a.cells_out)
    if not os.path.exists(glb) or not os.path.exists(col):
        print("bake_drum: no drum mesh at %s -- run tools/export_drum.py" % a.src)
        return 2

    radius = a.radius
    why = "given on the command line"
    if radius <= 0.0:
        radius, why = shipped_radius(a.cells_out)
    print("residency radius %.1f m, from %s" % (radius, why))

    if a.axis:
        ctrl = os.path.join(a.src, "column_red.glb")
        axis_report(glb, col, ctrl if os.path.exists(ctrl) else None,
                    radius=radius)
        if not (a.plan or a.seam or a.bake):
            return 0

    band = a.band
    if band <= 0.0:
        best, _rows = derive_band(glb, radius, curve=a.curve or a.plan)
        band = float(best["band_m"])
        print("derived band %.0f m: %d cells, worst %s tri, worst resident %s "
              "tri, %d instances"
              % (band, best["cells"], "{:,}".format(best["worst_cell"]),
                 "{:,}".format(best["worst_resident"]),
                 best["worst_instances"]))
    else:
        print("band %.0f m (given)" % band)

    if a.seam:
        print("seam probe at %.0f m bands, %.1f m residency radius:"
              % (band, radius))
        r = seam_probe(col, band, radius, samples=a.samples)
        print("CONTROL -- residency radius 0, so only the body's own cell is "
              "resident:")
        c = seam_probe(col, band, 0.0, samples=a.samples)
        lost_r, lost_c = r["step"] + r["fall"], c["step"] + c["fall"]
        if lost_c <= lost_r:
            print("  THE PROBE DOES NOT DISCRIMINATE: the control lost no more "
                  "floor than the real configuration (%d vs %d). Do not trust "
                  "the pass above." % (lost_c, lost_r))
            return 1
        print("  the control loses %d of %d probes against %d -- the probe "
              "discriminates" % (lost_c, c["samples"], lost_r))
        if r["fall"]:
            print("  %d probe(s) would fall out of the world at the shipped "
                  "radius -- the cut is NOT safe" % r["fall"])
            return 1

    if a.bake:
        man = bake(glb, col, band, radius, a.cells_out, timeout=a.timeout)
        if man is None:
            return 2
        manifest_report(man, radius)
    return 0


if __name__ == "__main__":
    sys.exit(main())
