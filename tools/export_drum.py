#!/usr/bin/env python3
"""EXPORT THE HABITAT DRUM AS A DECK — the one place the station build refuses.

`tools/export_station.py` builds 70 ring decks and declines the 71st with

    FAILED green_1_0: ValueError: green ring 1 is not a ring deck: the habitat
    drum -- the Garden, the townscape, the tram and the spokes. An open 8 km
    barrel, no ring corridor.

which is a CORRECT refusal — the drum genuinely is not a ring of rooms off a
corridor — and it left **twelve register locations and the largest single volume
on the station** out of everything that ships. The Garden, garden_town,
garden_terrace, the zen garden, water reclamation, Earhart's, Fresh Air, the
drum tram, the ground tram, the spokes, the end caps and the radial tubes were
absent from `station/generated/scene/station/` entirely.

WHAT CHANGED, AND IT IS THE ONLY THING THAT NEEDED TO. The refusal is about
*how a deck is assembled*, not about what a deck IS on disk. Downstream —
`tools/bake_station.py`, `station/route_walk.py`, `station/agenda.py`,
`godot/scripts/stream.gd` — a deck is five files and a manifest row:

    <stem>.glb  <stem>_collision.glb  <stem>_actors.json
    <stem>_crowd.json  <stem>_interact.json   + a row in station_manifest.json

So this file writes exactly those five, under the stem `green_1_0`, from the
drum's own generators. Nothing downstream needs to know the drum was built by a
different route, which is the whole point: **the pipeline must not special-case
it.** INV-1228 records the packaging decision and the two derivations inside it;
INV-1227 the uniform LOD, INV-1229 the collision proxies, INV-1230 the crowd.

WHAT GOES IN, AND WHERE EACH PIECE COMES FROM

  ground      `drum_ground.ground_patch` over ALL 280 patches at the stride
              `drum_walk.collision_stride()` derives — 573,440 triangles. Not
              `visible_set(eye)`: a static deck has no eye, and baking one
              eye's LOD into a shipped mesh means everything on the far side of
              the barrel is a level-4 blob for a player who walks over there.
  fixed parts `tools/export_scene.py::drum_parts` — end caps, guideways,
              spokes, core, trams, townscape. IMPORTED rather than re-listed:
              that function is already "the ONE place the drum shot's contents
              are listed", and a second copy of the list is this project's
              oldest defect in a new costume.
  dressing    `drum_dressing.dressing_set` at a UNIFORM level 0 (`scale` pushed
              past the far side of the drum so `_level` cannot return anything
              else) and with the near rung excluded — see NEAR RUNG below.
  rooms       the drum places whose module `bespoke.NEAR_END` can compose, built
              through `deck.room_geometry` (the same entry point the assembler
              and the collision builder use) and placed on the drum's own
              ground radius with `deck._place_local`.

WHAT IS NOT IN, STATED RATHER THAN OMITTED QUIETLY

  the near rung  `drum_dressing.near_field(eye)` is grass, crops, setts and
                 tussocks within ~35 m of the eye. It is defined against an eye
                 and there is no eye in a static deck; baked over 4.5 million m2
                 it is tens of millions of triangles. It stays a runtime rung.
  ground_tram    the register carries it (210 deg, 20 x 200 m) and nothing in
                 this repository builds a ground-level tram. `tram.py` builds
                 the ELEVATED guideway cars, which are `drum_tram`.
  radial_tubes   no builder anywhere; `interior.drum_spokes` is the spokes.

WHAT USED TO BE IN THAT LIST AND IS NOT ANY MORE. It read *"hedge collision: a
hedgerow's world AABB is a whole field. Colliding hedges needs a box per ribbon
segment; it is not in this pass."* It is in this pass now --
`drum_dressing.ribbon_boxes()`, one oriented box per merged run, 795 boxes and
9,540 triangles for 28.5 km of solid hedge. `tools/drum_hedge_gate.py` fires
9,510 rays at the assembly BELOW and reports **9,510 of 9,510 stopped**, against
**510 of 9,510** with the ribbon part withheld. -- INV-1244

Run: python3 tools/export_drum.py --dry-run
     python3 tools/export_drum.py                     # writes green_1_0_*
     python3 tools/export_drum.py --out /some/dir
"""
import argparse
import collections
import json
import math
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bespoke as BSP                                            # noqa: E402
import collision as C                                            # noqa: E402
import deck as D                                                 # noqa: E402
import directory as dr                                           # noqa: E402
import drum_dressing as dd                                       # noqa: E402
import drum_ground as dg                                         # noqa: E402
import drum_walk as DW                                           # noqa: E402
import interior as it                                            # noqa: E402

OUT = os.path.join(ROOT, "station/generated/scene/station")

# The stem every consumer addresses this deck by. It is the register's own
# (sector, ring, deck) for the drum -- `directory.PLACES` puts all twelve drum
# locations on green/1/0 -- so a reader that asks the register where the Garden
# is and then opens the deck it names finds this file.
STEM = "green_1_0"
SECTOR, RING, DECK = "green", 1, 0

# Every kind `drum_dressing.field()` emits, minus "near". Passing an explicit
# tuple is what excludes the near rung: `dressing_set` adds it unless `kinds` is
# given and does not contain "near".
DRESSING_KINDS = ("tree", "copse", "gantry", "shed", "silo", "spire", "jetty",
                  "town_block", "lamp", "hedgerow", "park_hedge", "reeds")

# A `scale` for `switch_distances` past which `_level` cannot return anything
# but 0. DERIVED from the drum rather than picked: the furthest two points on
# the drum floor are a diameter and the full axial run apart, so anything past
# that hypotenuse is further than any eye can be from any feature. The LOD
# ladder's first switch is `scale * LOD_RATIOS[0]`, so scaling by the drum's own
# diagonal over that ratio guarantees level 0 everywhere. -- INV-1227
def _lod0_scale():
    diag = math.hypot(2.0 * dg.FLOOR_R, dg.Z1 - dg.Z0)
    return diag / max(dd.LOD_RATIOS[0], 1e-9)


# WHICH DRESSING KINDS A BODY CANNOT WALK THROUGH. Structures, not planting: a
# town block, a shed, a silo, a gantry leg, a spire and a jetty are masonry, and
# a lamp column is a post you walk into. Trees are handled separately (trunk
# only -- see `_feature_boxes`).
#
# THE RIBBONS ARE NO LONGER EXCLUDED and this list is not where they live.
# `drum_dressing.RIBBON_GROUPS` decides which of them is solid, from the render
# group each one's SIDE carries, and `dd.ribbon_boxes()` builds them -- because
# a hedgerow is generated along a polyline and has no prototype for `_proto_box`
# to measure. Their solidity is deliberately NOT a second entry here: two lists
# naming the same decision is the drift this file's own docstrings keep warning
# about. -- INV-1244
SOLID_KINDS = ("town_block", "shed", "silo", "gantry", "spire", "jetty", "lamp")

# The structural parts of the drum and the register location that NAMES each.
# An explicit table, because these four are not resolved by footprint: the end
# caps are 2,588 m apart and `drum_endcaps` has one address, the guideway runs
# the whole length and `drum_tram` has one address. Attributing them by
# containment would leave the register's own names attached to nothing.
PART_PLACE = {
    "endcap_fore": "drum_endcaps",
    "endcap_aft": "drum_endcaps",
    "spokes": "drum_spokes",
    "guideways": "drum_tram",
    "trams": "drum_tram",
    # PLC-073 AND PLC-114, FIXED-ADDRESS FOR THE SAME REASON AS THE GUIDEWAY:
    # each is one named run at one address, so containment attribution would
    # scatter its triangles across whatever it happens to pass over.
    "ground_tram": "ground_tram",
    "radial_tubes": "radial_tubes",
}


def _spans_to_names(spans, n_tris, fallback="solid"):
    """[(name, tri_lo, tri_hi)] -> one group name per triangle.

    `tram.ground_stop` and `spoke_way.radial_tube` return SPANS, which is what
    `density.machinery_split` and `export_scene.per_triangle` read; the drum's
    parts list carries a name PER TRIANGLE. Both conventions already exist in
    this repository and the builders' own docstrings say so, so this converts
    rather than adding a third.

    A triangle covered by no span keeps `fallback` instead of being dropped:
    losing it would make the merged mesh disagree with its own triangle count,
    and a silent shortfall is how a part comes to be half-attributed.
    """
    out = [fallback] * n_tris
    for name, lo, hi in spans:
        for i in range(max(0, lo), min(n_tris, hi)):
            out[i] = name
    return out


# ---------------------------------------------------------------------------
# WHERE THE REGISTER'S PLACES ARE, ON THE DRUM
# ---------------------------------------------------------------------------

def place_boxes(floor_r_m):
    """Every drum place as (key, half_deg, half_z, angle, z, area_m2).

    THE SAME FOOTPRINT ARITHMETIC `tools/bake_station.py::place_rows` USES --
    `foot` is (across_m, along_m), across is an ARC, so the half-angle is
    `degrees((across/2) / r)`. Restating it differently here would put two
    descriptions of one footprint in the pipeline, and the first thing that
    diverges is which cell a place is reported in.

    Sorted SMALLEST FIRST, because the footprints nest: `the_garden` is 60 x
    600 m and `earharts` is 5 x 16 m inside the same band of the drum. A point
    inside both belongs to the smaller, which is the one that names it.
    """
    out = []
    for q in dr.PLACES:
        if q.get("sector") != SECTOR or q.get("ring") != RING:
            continue
        across, along = q["footprint"]
        out.append({
            "key": q["key"],
            "angle_deg": q["angle_deg"] % 360.0,
            "z_m": q["z_m"],
            "half_deg": math.degrees((across / 2.0) / max(floor_r_m, 1e-9)),
            "half_z_m": along / 2.0,
            "across_m": across, "along_m": along,
            "area_m2": across * along,
            "module": q.get("module") or "",
            "interacts": tuple(q.get("interacts") or ()),
        })
    return sorted(out, key=lambda r: r["area_m2"])


def _finder(boxes):
    """(angle_deg, z) -> place key or None. Closure over the sorted list.

    Bucketed by whole degree so the common case -- a triangle out in the fields,
    inside nothing -- costs a dict lookup rather than twelve interval tests over
    1.5 million triangles.
    """
    by_deg = collections.defaultdict(list)
    for b in boxes:
        lo = b["angle_deg"] - b["half_deg"]
        hi = b["angle_deg"] + b["half_deg"]
        d = int(math.floor(lo))
        while d <= math.ceil(hi):
            by_deg[int(d) % 360].append(b)
            d += 1

    def at(angle_deg, z_m):
        a = angle_deg % 360.0
        for b in by_deg.get(int(a), ()):
            if abs(z_m - b["z_m"]) > b["half_z_m"]:
                continue
            da = (a - b["angle_deg"] + 180.0) % 360.0 - 180.0
            if abs(da) <= b["half_deg"]:
                return b["key"]
        return None
    return at


def attribute(verts, tris, names, at):
    """Prefix every triangle's group with the place whose footprint holds it.

    `interact.sidecar` reads the place out of the group name -- `deck.build_deck`
    writes `<key>__<group>` and the resolver splits on `PLACE_SEP` -- so a drum
    that never prefixes anything has twelve locations and zero interactables by
    construction, whatever it actually built.

    PER TRIANGLE, BEFORE THE SPAN RUN-LENGTHING, and that ordering is the whole
    correctness of it. `dressing_set` emits feature by feature in kind order, so
    two `garden_trunk` runs that are adjacent in the list can be a tree at 10
    degrees and a tree at 200. Run-lengthing first and attributing the span's
    centroid afterwards would give that span a centroid in the middle of the
    drum and an interactable box 1,749 m across. Prefixing first splits the run
    exactly where the footprint boundary is.
    """
    out = []
    hits = collections.Counter()
    for i, (ia, ib, ic) in enumerate(tris):
        a, b, c = verts[ia], verts[ib], verts[ic]
        x = (a[0] + b[0] + c[0]) / 3.0
        y = (a[1] + b[1] + c[1]) / 3.0
        z = (a[2] + b[2] + c[2]) / 3.0
        k = at(math.degrees(math.atan2(y, x)), z)
        nm = names[i]
        if k is None:
            out.append(nm)
        else:
            hits[k] += 1
            out.append(f"{k}{'__'}{nm}")
    return out, hits


# ---------------------------------------------------------------------------
# THE GROUND
# ---------------------------------------------------------------------------

def full_ground(stride):
    """The WHOLE drum floor at one stride. (verts, tris, per-triangle names).

    UNIFORM, and `drum_walk.ground_shell` states why in the collision case:
    every shared edge vertex is computed from the same `_vertex(ia, iz)` call on
    both sides, so the seam is exact rather than repaired. Mixing levels here
    would need `ground_patch`'s `neighbours` clamping and would put T-junctions
    between a 32-cell edge and a 4-cell edge -- a sawtooth of holes, which under
    spin gravity is thirty kilometres of falling outward.
    """
    V, T, G = [], [], []
    for pa in range(dg.PATCHES_A):
        for pz in range(dg.PATCHES_Z):
            v, t, g, _m = dg.ground_patch(pa, pz, stride)
            off = len(V)
            V.extend(v)
            T.extend((a + off, b + off, c + off) for a, b, c in t)
            G.extend(g)
    return V, T, G


# ---------------------------------------------------------------------------
# WHAT STANDS ON IT, AND WHAT A BODY BUMPS INTO
# ---------------------------------------------------------------------------

def uniform_dressing():
    """Everything on the drum floor at level 0, everywhere. (v, t, names, meta)."""
    eye = (0.0, 0.0, (dg.Z0 + dg.Z1) / 2.0)
    return dd.dressing_set(eye, scale=_lod0_scale(), kinds=DRESSING_KINDS)


def _proto_box(kind, index, level, only=None):
    """The local AABB of a prototype's own mesh. MEASURED, not declared.

    `only` restricts it to named groups, which is what makes a tree's collider
    its TRUNK: a broadleaf's full box is 5 m across because of the crown, and
    shipping that gives every tree on the drum an invisible five-metre cylinder
    a player walks into. `drum_dressing.prototype` is the same call
    `dressing_set` renders from, so this cannot describe a different object than
    the one on screen -- hard rule 4.
    """
    v, t, g = dd.prototype(kind, index, level)
    if not v or not t:
        return None
    if only:
        per = [None] * len(t)
        for nm, lo, hi in g:
            for i in range(lo, hi):
                per[i] = nm
        keep = {j for i, tri in enumerate(t) if per[i] in only for j in tri}
        pts = [v[j] for j in sorted(keep)]
    else:
        pts = v
    if not pts:
        return None
    return [min(p[k] for p in pts) for k in range(3)] + \
           [max(p[k] for p in pts) for k in range(3)]


TRUNK_GROUPS = ("garden_trunk", "garden_branch")


def feature_boxes(level=0):
    """One oriented collision box per standing feature. (verts, tris, count).

    ORIENTED, NOT AXIS-ALIGNED IN WORLD SPACE, and that is the reason this goes
    through `collision.boxes_mesh` rather than emitting six quads here.
    `boxes_mesh` takes a LOCAL box and a `place_fn` -- its docstring says "so the
    same boxes work on a ring deck, on the drum, or anywhere else a room gets
    put" -- and `drum_dressing._to_world` is exactly that function for the drum,
    yaw included. A world AABB of a 22 x 13 m block standing at 45 degrees is
    25 x 25 m, and the four metres of that which is air is four metres a player
    walks into and cannot see. -- INV-1229
    """
    fld = dd.field()
    V, T = [], []
    n = 0
    cache = {}
    for f in fld["points"]:
        if f.kind in SOLID_KINDS:
            key = (f.kind, f.proto, None)
            only = None
        elif f.kind in ("tree", "copse"):
            key = ("tree", f.proto, TRUNK_GROUPS)
            only = TRUNK_GROUPS
        else:
            continue
        if f.kind == "copse":
            for (mx, mz, proto, yaw, sc) in f.members:
                mk = ("tree", proto, TRUNK_GROUPS)
                if mk not in cache:
                    cache[mk] = _proto_box("tree", proto, level, TRUNK_GROUPS)
                box = cache[mk]
                if box is None:
                    continue
                da = math.degrees(mx / dg.FLOOR_R)
                vv, tt = C.boxes_mesh(
                    [box], lambda pts, a=f.angle_deg + da, z=f.z_m + mz,
                    r=f.ground_r, y=yaw, s=sc:
                    dd._to_world(pts, a, z, r, y, s))
                off = len(V)
                V.extend(vv)
                T.extend((a + off, b + off, c + off) for a, b, c in tt)
                n += 1
            continue
        if key not in cache:
            cache[key] = _proto_box(f.kind if only is None else "tree",
                                    f.proto, level, only)
        box = cache[key]
        if box is None:
            continue
        vv, tt = C.boxes_mesh(
            [box], lambda pts, a=f.angle_deg, z=f.z_m, r=f.ground_r,
            y=f.yaw, s=f.scale: dd._to_world(pts, a, z, r, y, s))
        off = len(V)
        V.extend(vv)
        T.extend((a + off, b + off, c + off) for a, b, c in tt)
        n += 1
    return V, T, n


def _dressing_solid(name):
    """Which townscape groups a body cannot pass through.

    `collision.prop_boxes` defaults to `rooms.is_solid`, which knows the ROOM
    vocabulary (`prop_`, `fix_`, `dress_`) and nothing about `garden_*`. Handed
    the townscape it keeps nothing, and the twelve buildings the owner's own
    reference frames are of would have no collision at all.

    Foliage and water are deliberately absent: a crown is not a wall, and the
    pool is a thing you fall into rather than a thing you stand on.
    """
    return name in (
        "garden_block", "garden_plinth", "garden_tower", "garden_slab",
        "garden_colonnade", "garden_colonnade_core", "garden_pilaster",
        "garden_bank", "garden_terrace", "garden_planter", "garden_bench",
        "garden_boundary", "garden_track_pier", "garden_parapet",
        "garden_pool_coping", "garden_flagpole", "garden_trunk",
        "garden_canopy", "garden_balcony", "garden_cap", "garden_sleeper",
        "garden_lamp_column", "garden_stair_accent",
    )


# ---------------------------------------------------------------------------
# THE ROOMS ON THE DRUM
# ---------------------------------------------------------------------------

def drum_rooms(schema, profile, boxes):
    """Composed interiors for the drum places that have a builder.

    ONLY `bespoke.NEAR_END`, and the omission is deliberate rather than lazy.
    `deck.room_geometry` falls back to `rooms.build` -- a corridor-fed enclosed
    bay -- for anything else, and `the_garden` is 60 x 600 m of open parkland.
    Dropping a sealed grey bay onto the Garden's lawn is worse than leaving the
    lawn, and it is exactly the failure `garden.block_building`'s docstring
    records the owner rejecting by name.

    Placed with `deck._place_local` at the DRUM'S OWN GROUND RADIUS under the
    place, not at `FLOOR_R`: the heightfield runs -3.9 to +8.9 m about the
    datum, so a room seated on the datum at a settlement podium is eight metres
    underground.
    """
    parts, actors, used = [], [], []
    for b in boxes:
        if b["module"] not in BSP.NEAR_END:
            continue
        q = dr.by_key(b["key"])
        rep = {}
        try:
            rv, rt, rg, how = D.room_geometry(schema, profile, q, report=rep)
        except Exception as e:                                   # noqa: BLE001
            used.append((b["key"], b["module"], f"raised: {str(e)[:60]}"))
            continue
        u = (b["angle_deg"] / 360.0) % 1.0
        w = min(max((b["z_m"] - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
        ground_r = dg.FLOOR_R - dg.sample(u, w)[0]
        wv = D._place_local(rv, ground_r, b["angle_deg"], b["z_m"])
        per = [None] * len(rt)
        for nm, lo, hi in rg:
            for i in range(lo, min(hi, len(rt))):
                per[i] = nm
        if any(x is None for x in per):
            used.append((b["key"], b["module"], "untagged triangles"))
            continue
        # PREFIXED HERE, NOT BY `attribute`. A room's own mesh is the place by
        # construction and its footprint is 5 x 16 m -- attributing it by
        # centroid would work and would also silently drop any part of it that
        # overhangs its own declared footprint, which is how a bar's canopy
        # loses its material.
        parts.append((b["key"], wv, rt, [f"{b['key']}__{n}" for n in per]))
        for act in rep.get("actors", ()):
            wx, wy, wz = D._place_local(
                [(act["x"], act["y"], act["z"])], ground_r,
                b["angle_deg"], b["z_m"])[0]
            actors.append({
                "group": f"{b['key']}__{act['group']}",
                "place": b["key"], "who": act["who"], "pose": act["pose"],
                "x": wx, "y": wy, "z": wz, "yaw": act["yaw"],
                **{k: act[k] for k in ("r_m", "h_m", "species", "lod")
                   if k in act},
            })
        used.append((b["key"], b["module"], how))
    return parts, actors, used


# ---------------------------------------------------------------------------
# THE PEOPLE ON THE DRUM
# ---------------------------------------------------------------------------

def crowd_lod_for(area_m2):
    """The crowd LOD for an OPEN place of this area, off the baked ladder.

    NOT `populace.corridor_lod`, and the reason is that its premise is a
    corridor: it takes `corridor_sight_m(radius, width)` -- a chord problem,
    "how far can a body see down a corridor that curves away from it" -- and
    halves it. Handed the Garden's 600 m width that formula returns a 1,140 m
    sight line, which is not a sight line, it is the formula outside its domain.

    An open place is a patch of ground, so the honest distance is the mean
    separation of two uniformly-random points in a disc of the same area:
    `128 R / (45 pi)`, R = sqrt(A/pi). A standard result, not a number chosen
    here. The Garden's 35,734 m2 gives R = 106.6 m and a mean of 96.5 m; a
    78 m2 bar gives 4.5 m.

    AND IT IS SNAPPED TO `populace.crowd_ladder()`, WHICH IS THE BAKED SET.
    `tools/bake_crowd.py` writes `crowd_lod<N>.glb` for the ladder's rungs --
    2, 4 and 8 -- and `walk.gd::_load_crowd_libs` resolves the mesh by that
    name. `corridor_lod` returns an index into `body.lod_chain()`, which is ten
    levels long, so seven of its ten possible answers name a library file that
    was never baked. Ring decks happen to land on 4 and the drum happened to
    land on 8; nothing was making that true. -- INV-1230
    """
    import populace as _pop                                       # noqa: PLC0415
    R = math.sqrt(max(area_m2, 1e-9) / math.pi)
    mean_m = 128.0 * R / (45.0 * math.pi)
    ladder = _pop.crowd_ladder()
    for hi, lod in ladder:
        if mean_m < hi:
            return lod, mean_m
    return ladder[-1][1], mean_m


def drum_crowd(boxes, hour=None):
    """Walkers on the drum ground, per register place. Returns (rows, stats).

    `populace.populate_corridor` IS THE GENERATOR, called once per place over
    that place's own footprint rather than once over the drum. Two reasons, and
    the second is the load-bearing one:

      1. its headcount comes from `corridor_headcount(served, area, hour)`,
         which weights the station-wide 1.07 per 100 m2 by the OCCUPANCY of the
         places served -- so the Garden fills at 1300 and empties at 0300 by
         the same clock every other deck uses. Called once with all twelve
         places and the whole barrel's 4.5 million m2 it returns ~48,000 people
         and spreads them evenly over open farmland.
      2. it is the only crowd generator anything on this station ships, and a
         second one would be a second description of who is walking.

    THEN EVERY BODY IS RE-SEATED ONTO THE TERRAIN. `populate_corridor` stands
    people at a constant radius, which is right on a ring deck and wrong here by
    up to 8.9 m -- the heightfield's own range. The correction reads
    `drum_ground.sample`, the function the ground mesh is built from, so a
    person cannot end up on a different surface than the one that ships.
    """
    import populace as _pop                                       # noqa: PLC0415
    rows, stats = [], []
    for b in boxes:
        arc_deg = 2.0 * b["half_deg"]
        u = (b["angle_deg"] / 360.0) % 1.0
        w = min(max((b["z_m"] - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
        ground_r = dg.FLOOR_R - dg.sample(u, w)[0]
        lod, mean_m = crowd_lod_for(b["across_m"] * b["along_m"])
        _v, _t, _g, st = _pop.populate_corridor(
            f"{SECTOR}/{RING}/{DECK}/{b['key']}", ground_r, b["half_z_m"],
            arc_deg, b["angle_deg"] - b["half_deg"], b["z_m"],
            served=(b["key"],), hour=hour, instanced=True, lod=lod)
        moved = 0.0
        for r in st.get("instances", ()):
            a = math.atan2(r["y"], r["x"])
            uu = (math.degrees(a) / 360.0) % 1.0
            ww = min(max((r["z"] - dg.Z0) / (dg.Z1 - dg.Z0), 0.0), 1.0)
            rr = dg.FLOOR_R - dg.sample(uu, ww)[0]
            was = math.hypot(r["x"], r["y"])
            moved = max(moved, abs(rr - was))
            r["x"], r["y"] = rr * math.cos(a), rr * math.sin(a)
            r["group"] = f"{b['key']}_{r.get('group', '')}"
            rows.append(r)
        stats.append({"key": b["key"], "wanted": st.get("wanted", 0),
                      "placed": len(st.get("instances", ())),
                      "area_m2": round(st.get("area_m2", 0.0), 1),
                      "lod": st.get("lod"),
                      "mean_sight_m": round(mean_m, 1),
                      "reseated_max_m": round(moved, 3)})
    return rows, stats


# ---------------------------------------------------------------------------
# WRITING
# ---------------------------------------------------------------------------

def _write(out_dir, stem, V, T, G):
    """OBJ -> GLB, asserted, OBJ removed. `export_station._write`'s contract.

    The face-count assertion is not ceremony: `deck.write_obj` takes SPANS and
    `interior.write_grouped_obj` takes per-triangle names, and the first run of
    `export_station.py` called the wrong one and threw away all 71 assembled
    decks at the write while reporting `IndexError`.
    """
    obj = os.path.join(out_dir, stem + ".obj")
    glb = os.path.join(out_dir, stem + ".glb")
    D.write_obj(obj, V, T, G)
    with open(obj, encoding="utf-8") as f:
        body = f.read()
    nf = body.count("\nf ")
    ng = body.count("\ng ")
    if nf != len(T):
        raise AssertionError(f"{stem}: wrote {nf} faces for {len(T)} triangles")
    if ng < 1:
        raise AssertionError(f"{stem}: wrote no groups for {len(G)} spans")
    import export_gltf                                            # noqa: PLC0415
    argv = sys.argv
    sys.argv = ["export_gltf", "--obj", obj, "--out", glb]
    try:
        export_gltf.main()
    finally:
        sys.argv = argv
    if not os.path.exists(glb) or os.path.getsize(glb) < 1024:
        raise AssertionError(f"{stem}: glb is missing or empty")
    ob = os.path.getsize(obj)
    os.remove(obj)
    return ob, os.path.getsize(glb)


def _merge(parts):
    """[(name, verts, tris, per-tri names)] -> (V, T, per-tri names)."""
    V, T, G = [], [], []
    for _n, v, t, g in parts:
        off = len(V)
        V.extend(v)
        T.extend((a + off, b + off, c + off) for a, b, c in t)
        G.extend(g)
    return V, T, G


def _floor_probe(verts, tris, samples=200):
    """Can a body stand on this shell? A radial cast per sample, as a foot does.

    NOT a triangle count. `station/walkable.py`'s own lesson is that a walk gate
    reports distance covered rather than "did it move"; the cheap static form of
    the same question is whether a downhill ray from the axis hits ground at a
    plausible radius, at points spread over the whole drum. A collision file
    that is 573,440 triangles of something a foot never meets passes every count
    there is.
    """
    cast = DW._Caster(verts, tris)
    hit, miss, lo, hi = 0, 0, None, None
    for i in range(samples):
        a = (i * 360.0 / samples) % 360.0
        z = dg.Z0 + (dg.Z1 - dg.Z0) * ((i * 0.61803398875) % 1.0)
        r = cast.radius_at(a, z)
        if r is None:
            miss += 1
            continue
        hit += 1
        lo = r if lo is None else min(lo, r)
        hi = r if hi is None else max(hi, r)
    return {"samples": samples, "hit": hit, "miss": miss,
            "radius_min_m": None if lo is None else round(lo, 3),
            "radius_max_m": None if hi is None else round(hi, 3)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=OUT, help="scene/station directory")
    ap.add_argument("--stride", type=int, default=0,
                    help="override the derived collision stride")
    ap.add_argument("--hour", type=float, default=None,
                    help="station hour for the crowd (default: now)")
    ap.add_argument("--no-dressing", action="store_true",
                    help="control: the drum with nothing standing on it")
    a = ap.parse_args(argv)

    t_all = time.time()
    schema, profile, sector = DW.drum()
    stride = a.stride or DW.collision_stride()[0]
    boxes = place_boxes(dg.FLOOR_R)
    at = _finder(boxes)

    print("\nTHE HABITAT DRUM, AS A DECK\n")
    print(f"  stem {STEM}  ({SECTOR}/{RING}/{DECK}), sector {sector}")
    print(f"  r = {dg.FLOOR_R:.1f} m, circumference "
          f"{2 * math.pi * dg.FLOOR_R:,.0f} m, z {dg.Z0:,.0f}..{dg.Z1:,.0f} "
          f"({dg.Z1 - dg.Z0:,.0f} m)")
    print(f"  {dg.PATCHES_A} x {dg.PATCHES_Z} = "
          f"{dg.PATCHES_A * dg.PATCHES_Z} ground patches at stride {stride} "
          f"-> {dg.PATCHES_A * dg.PATCHES_Z * 2 * (dg.PATCH_A // stride) * (dg.PATCH_Z // stride):,} tri")
    print(f"  {len(boxes)} register locations:")
    for b in boxes:
        print(f"     {b['key']:<16} {b['angle_deg']:6.1f} deg "
              f"z {b['z_m']:.0f}  {b['across_m']:.0f} x {b['along_m']:.0f} m "
              f"({b['half_deg']:.2f} deg half-arc)  module {b['module'] or '-'}")
    if a.dry_run:
        print("\n  dry run -- nothing built.")
        return 0

    os.makedirs(a.out, exist_ok=True)
    row = {"key": STEM, "ok": False}
    try:
        # -- THE RENDER MESH ------------------------------------------------
        t0 = time.time()
        import export_scene as ES                                # noqa: PLC0415
        eye = (0.0, -(dg.FLOOR_R - 2.0), (dg.Z0 + dg.Z1) / 2.0)
        parts = [(n, v, t, list(g))
                 for n, v, t, g in ES.drum_parts(schema, profile, sector, eye)]
        fixed_s = time.time() - t0

        # The two the eye decides, replaced by the two a static deck needs.
        by_name = {n: i for i, (n, _v, _t, _g) in enumerate(parts)}

        # AND THE TRAMS GET THEIR SALOONS, which the drum SHOT correctly does
        # not build. `tram.tram_car`'s docstring states the reason for the
        # default: "three guideways of cars are always in frame in the drum and
        # only the one you are riding needs a saloon" -- right for a still, and
        # wrong for a deck, because `drum_tram` DECLARES `seat`, `tram_door` and
        # `handhold` and a shell has none of them. Measured before deciding:
        # 12,624 tri -> 30,060 over six cars, +1.1% of this deck, every one of
        # the fifteen new groups already bound in `materials`' drum scene, and
        # `seat` resolves to `tram_in_seat`.
        import tram as _tram                                     # noqa: PLC0415
        tv, tt, tm = _tram.drum_trams(schema, profile, sector, per_guideway=2,
                                      interior=True, glazed=True)
        parts[by_name["trams"]] = ("trams", tv, tt, tm["groups"])

        # -- THE TWO PLACES THAT HAD A BUILDER AND NO CALLER ------------------
        # INSTANCE TWELVE OF THIS PROJECT'S SIGNATURE DEFECT, caught by an
        # adversarial verifier rather than by a gate. `ground_tram` (PLC-073)
        # and `radial_tubes` (PLC-114) were built this session -- real geometry,
        # their own gates, reasoned extrapolations -- and NOTHING CALLED EITHER,
        # so in the shipped build those two places still had a crowd standing in
        # an empty field. The verifier's words: "the claim under verification is
        # that two register places have a builder, and in the shipped build they
        # still have nothing."
        #
        # A builder with no caller is not a built place. This is the caller.
        import spoke_way as _sw                                   # noqa: PLC0415
        for nm, fn in (("ground_tram",
                        lambda: _tram.ground_stop(schema, profile, sector)),
                       ("radial_tubes",
                        lambda: _sw.radial_tube(schema, profile, sector))):
            try:
                bv, bt, bspans, _bm = fn()
            except Exception as exc:                              # noqa: BLE001
                # NAMED, NOT SWALLOWED. A place that fails to build must say so
                # on the build's own output; `reach_gate` counts cells and would
                # still pass, because the ground under it is attributed either
                # way. Silence here is how the crowd-in-a-field state persisted.
                print(f"  {nm}: BUILD FAILED -- {exc}")
                continue
            if not bt:
                print(f"  {nm}: builder returned no triangles")
                continue
            parts.append((nm, bv, bt, _spans_to_names(bspans, len(bt))))
            print(f"  {nm}: {len(bt):,} tri from its own builder")

        t0 = time.time()
        gv, gt, gg = full_ground(stride)
        parts[by_name["ground"]] = ("ground", gv, gt, gg)
        ground_s = time.time() - t0
        t0 = time.time()
        if a.no_dressing:
            parts[by_name["dressing"]] = ("dressing", [], [], [])
            dmeta = {"triangles": 0, "features": 0}
        else:
            dv, dt, dgn, dmeta = uniform_dressing()
            parts[by_name["dressing"]] = ("dressing", dv, dt, dgn)
        dress_s = time.time() - t0

        # -- THE ROOMS ------------------------------------------------------
        t0 = time.time()
        rparts, actors, used = drum_rooms(schema, profile, boxes)
        parts.extend((f"room_{k}", v, t, g) for k, v, t, g in rparts)
        rooms_s = time.time() - t0

        # -- PLACE ATTRIBUTION, THEN THE SPANS ------------------------------
        t0 = time.time()
        named = []
        hits = collections.Counter()
        for n, v, t, g in parts:
            if n.startswith("room_"):
                named.append((n, v, t, g))
                if t:
                    hits[g[0].split("__")[0]] += len(t)
                continue
            fixed = PART_PLACE.get(n)
            if fixed:
                named.append((n, v, t, [f"{fixed}__{x}" for x in g]))
                hits[fixed] += len(t)
                continue
            g2, h = attribute(v, t, g, at)
            hits.update(h)
            named.append((n, v, t, g2))
        V, T, per = _merge(named)
        G = DW._spans(per)
        attr_s = time.time() - t0

        t0 = time.time()
        ob, gb = _write(a.out, STEM, V, T, G)
        write_s = time.time() - t0

        # -- COLLISION ------------------------------------------------------
        t0 = time.time()
        cparts = []
        # THE SAME GROUND OBJECT, NOT A SECOND BUILD OF IT. The render ground is
        # already at `collision_stride()` -- the derived answer is stride 1, and
        # `lod_error_report` says stride 2 is 0.193 m off against a 0.100 m step
        # -- so rebuilding it here would be a second copy of a surface that must
        # not differ from the one the player sees by so much as a vertex.
        cparts.append(("ground", gv, gt, gg))
        if not a.no_dressing:
            fv, ft, fn = feature_boxes()
            cparts.append(("features", fv, ft, ["drum_solid"] * len(ft)))
            # AND THE RIBBONS, which `feature_boxes` cannot do because a
            # hedgerow has no prototype to take a box from -- it is generated
            # in place along a polyline, so the box has to be fitted to the
            # cross-sections `_ribbon` emits, which is where it is fitted.
            # Same two calls underneath (`boxes_mesh` + `_to_world`), same
            # `drum_solid` group. Gated by `station/drum_dressing.py
            # --ribbon-collision` and by `tools/drum_hedge_gate.py`, which
            # asks this assembly rather than that function. -- INV-1244
            rv, rt, rn = dd.ribbon_boxes()
            cparts.append(("ribbons", rv, rt, ["drum_solid"] * len(rt)))
        else:
            fn = rn = 0
        # The end caps and the spokes: what stops a body walking off the drum.
        for n, v, t, g in parts:
            if n in ("endcap_fore", "endcap_aft", "spokes"):
                cparts.append((n, v, t, [f"drum_{n}"] * len(t)))
        # The townscape's masonry, derived from its own emitted mesh.
        tsi = by_name["townscape"]
        tv, tt, tg = parts[tsi][1], parts[tsi][2], parts[tsi][3]
        tspans = DW._spans([x.split("__")[-1] for x in tg])
        tboxes = C.prop_boxes(tv, tt, tspans, solid=_dressing_solid)
        bv, bt = C.boxes_mesh(tboxes, lambda pts: pts)
        cparts.append(("townscape", bv, bt, ["townscape_solid"] * len(bt)))
        # The rooms' own furniture, the same way `deck.build_collision` does it.
        rboxes = 0
        for k, v, t, g in rparts:
            import rooms as _R                                    # noqa: PLC0415
            spans = DW._spans([x.split("__")[-1] for x in g])
            bx = C.prop_boxes(v, t, spans, solid=_R.is_solid)
            rboxes += len(bx)
            rv2, rt2 = C.boxes_mesh(bx, lambda pts: pts)
            cparts.append((f"room_{k}", rv2, rt2,
                           [f"{k}__solid"] * len(rt2)))
        CV, CT, CN = _merge(cparts)
        CG = DW._spans(CN)
        _ob2, cgb = _write(a.out, STEM + "_collision", CV, CT, CG)
        col_s = time.time() - t0

        # -- THE SIDECARS ---------------------------------------------------
        t0 = time.time()
        import walkable as W                                      # noqa: PLC0415
        irows = W.interact_rows(V, T, G)
        crowd, cstats = drum_crowd(boxes, hour=a.hour)
        side = {}
        for nm, payload in (("interact", irows), ("actors", actors),
                            ("crowd", crowd)):
            p = os.path.join(a.out, f"{STEM}_{nm}.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            side[nm] = len(payload)
        side_s = time.time() - t0

        probe = _floor_probe(CV, CT)
        # AND THE DRUM'S OWN GATE, WHICH IS SLOPE AND NOT LIP.
        # `collision.floor_steps` asks for the largest step between neighbouring
        # samples, which is exactly right on a corridor -- flat by design, so any
        # lip is a defect -- and fails a perfectly good hill: this ground rises
        # 0.24 m between adjacent lattice points, which is 3.5 degrees, which is
        # a field. `drum_walk.slope_report` asks what a CharacterBody3D actually
        # decides, rise over run against `floor_max_angle`, per emitted triangle
        # against the local radial. Run on the SHIPPED ground rather than on the
        # function that made it.
        slope = DW.slope_report(gv, gt)
        slope.pop("histogram", None)

        row = {
            "key": STEM, "ok": True,
            "clusters": 1, "rooms": len(rparts),
            "tris": len(T), "groups": len(G),
            "joins": 0, "join_m": 0.0,
            "collision_tris": len(CT),
            "interactables": side["interact"],
            "actors": side["actors"], "crowd": side["crowd"],
            "collision_joins": 0,
            "collision_mb": round(cgb / 1e6, 2),
            "obj_mb": round(ob / 1e6, 2), "glb_mb": round(gb / 1e6, 2),
            "seconds": round(time.time() - t_all, 1),
            # THE DRUM'S OWN RECORD, beside the ring-deck fields rather than
            # instead of them. A reader that only knows about ring decks gets
            # every field it expects; one that asks about the drum gets what it
            # actually is.
            "drum": {
                "stride": stride, "floor_r_m": dg.FLOOR_R,
                "patches": dg.PATCHES_A * dg.PATCHES_Z,
                "ground_tris": len(gt),
                "dressing_tris": dmeta.get("triangles", 0),
                "dressing_features": dmeta.get("features", 0),
                "feature_boxes": fn, "ribbon_boxes": rn,
                "townscape_boxes": len(tboxes),
                "room_boxes": rboxes,
                "places": len(boxes),
                "places_with_geometry": sorted(hits),
                "tris_by_place": {k: v for k, v in sorted(hits.items())},
                "rooms_built": used,
                "crowd_by_place": cstats,
                "floor_probe": probe,
                "ground_slope": slope,
                "floor_max_deg": DW.FLOOR_MAX_DEG,
                "gravity_m_s2": round(DW.gravity_m_s2(schema), 4),
                "seconds": {"fixed": round(fixed_s, 1),
                            "ground": round(ground_s, 1),
                            "dressing": round(dress_s, 1),
                            "rooms": round(rooms_s, 1),
                            "attribute": round(attr_s, 1),
                            "write": round(write_s, 1),
                            "collision": round(col_s, 1),
                            "sidecars": round(side_s, 1)},
            },
        }
        print(f"\n  {STEM}: {len(T):,} tri in {len(G):,} groups, "
              f"{row['glb_mb']:.1f} MB")
        print(f"    ground {len(gt):,} + dressing "
              f"{dmeta.get('triangles', 0):,} over "
              f"{dmeta.get('features', 0)} features + fixed "
              f"{len(T) - len(gt) - dmeta.get('triangles', 0):,}")
        print(f"    collision {len(CT):,} tri, {row['collision_mb']:.2f} MB "
              f"({fn} feature boxes, {rn} ribbon, {len(tboxes)} townscape, "
              f"{rboxes} room)")
        print(f"    floor probe: {probe['hit']}/{probe['samples']} radial "
              f"casts land, r {probe['radius_min_m']}..{probe['radius_max_m']} m")
        print(f"    ground slope: worst {slope['max_deg']:.2f} deg, "
              f"{slope['over_floor_angle']} of {slope['triangles']:,} triangles "
              f"over Godot's {DW.FLOOR_MAX_DEG:.0f} deg floor_max_angle "
              f"(gravity {DW.gravity_m_s2(schema):.4f} m/s2, radial)")
        print(f"    {side['actors']} actors / {side['crowd']} crowd / "
              f"{side['interact']} interactables")
        for k in sorted(hits):
            print(f"       {k:<16} {hits[k]:>9,} tri")
        for c in cstats:
            print(f"       crowd {c['key']:<14} {c['placed']:>4} people over "
                  f"{c['area_m2']:>10,.0f} m2, lod {c['lod']} "
                  f"(mean {c['mean_sight_m']:.0f} m), "
                  f"re-seated <= {c['reseated_max_m']} m")
    except Exception as e:                                        # noqa: BLE001
        tb = traceback.format_exc()
        where = [l.strip() for l in tb.splitlines()
                 if l.strip().startswith("File ")]
        row = {"key": STEM, "ok": False, "why": f"{type(e).__name__}: {e}",
               "at": where[-1] if where else "", "traceback": tb,
               "seconds": round(time.time() - t_all, 1)}
        print(f"\n  {STEM}: FAILED -- {row['why'][:160]}\n"
              f"        {row['at']}")

    # -- THE MANIFEST ROW ---------------------------------------------------
    # ACCUMULATED, never overwritten. `export_station.py` learned this the hard
    # way: a `--sector` run that rewrote the whole record left a manifest saying
    # the station was nine decks. This file writes ONE row and must not disturb
    # the seventy that are already there.
    mpath = os.path.join(a.out, "station_manifest.json")
    man = {"decks": [], "columns": []}
    if os.path.exists(mpath):
        try:
            with open(mpath, encoding="utf-8") as f:
                man = json.load(f)
        except (OSError, ValueError):
            man = {"decks": [], "columns": []}
    man["decks"] = [r for r in man.get("decks", ())
                    if r.get("key") != STEM] + [row]
    man.setdefault("columns", [])
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1)
    good = [d for d in man["decks"] if d.get("ok")]
    print(f"\n  manifest: {len(good)} of {len(man['decks'])} decks ok "
          f"({mpath})")
    return 0 if row.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
