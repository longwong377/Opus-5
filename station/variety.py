"""Is this place different from that place? -- the V0 gate.

WHAT THIS EXISTS TO ANSWER, and why nothing else in the repository answers it.

Every gate in this project measures COVERAGE or CORRECTNESS.  `directory.py`
counts locations per layer, `density.py` scores one module's line density,
`budget.py` counts triangles, `walkable.py` asks whether a body can get from A
to B, `deck.py --sweep` asks how many of the 128 assemble.  **Every one of them
is perfectly satisfied by one generic thing repeated seventy-eight times.**  The
owner looked at the station and said every corridor looks the same; measured,
they are right, and no assertion in this repository could have said so.

So this module asks the missing question in a number: **for every pair of
places, how much of one is the other?**  It is modelled directly on
`npc/body.py --silhouette`, which asks the same question of four species and
carries the control that makes the answer mean something -- four bodies built
from ONE parameter block read IoU 1.000 and FAIL the ceiling the four real
species pass.  Everything below is that instrument, pointed at rooms.

`MASTER-PLAN.md` §4 milestone V0: *"the gate exists and is red"*.  It is red.


HOW A PLACE IS COMPARED, AND WHY THESE THREE CHANNELS
-----------------------------------------------------
A player walking into a room answers three questions, in this order:

  1. **What shape is this volume?**  Clear height, width, the rhythm of ribs
     and services overhead.  -> the SECTION channel.
  2. **What is standing in it, and where?**  Aisles, benches, racking, the
     pitch of the repeated thing.  -> the PLAN channel.
  3. **What ARE those things?**  A player names a room by its contents: this
     is a medlab, that is a bar.  -> the CONTENT channel.

All three are marginals of ONE computed structure -- a solid-occupancy field
sampled by a winding walk down each column (see `occupancy`).  Plan and section
are two views of the same solid, so `form` is the harsher of them, exactly as
`body.py` scores a species pair at the view they differ MOST in; content is a
different property, the way stature is not a third view of a species.  A pair's
score is `min(form, content)`, so it only reads high when two places are the
same shape AND the same layout AND the same stuff.

The gate is then a ceiling on the worst pair, and the number that matters most
is not the worst pair -- it is how many pairs are over the ceiling, and how big
the largest cluster of places nothing can tell apart is.


WHAT IS DELIBERATELY NOT IN THE MEASUREMENT
-------------------------------------------
* **People.** `npc_` groups are excluded, through `rooms.is_solid`'s own rule.
  A room's crowd is not the room's form, and including it would have broken the
  seed control below: two clones differing only in seed get different bodies,
  so the metric would have reported crowd RNG as place identity.
* **Material and light.** They are real differences and they are somebody
  else's gate (layer 3 and 4b).  This one is about FORM, which is what V1 has
  to generate and what no existing measurement touches.
* **Absolute size.** It is not excluded -- see the window rule -- but it is
  reported separately in `--drivers`, because "is the variance just size?" is
  the question that decides what V1's grammar keys on.


THE WINDOW, AND THE PIXEL SPAN IT IS MEASURED AT
------------------------------------------------
`body.py` records the most expensive lesson available here: it once rasterised
a head **5 pixels wide**, and a "regression" everyone was reading turned out to
be one pixel of a five-pixel shape.  So, stated up front rather than left to be
rediscovered:

    cell        0.08 m
    window      19.2 m x 19.2 m in plan  ->  240 x 240 columns
    section     19.2 m x  9.6 m          ->  240 x 120 cells

At that scale a 0.6 m prop is **7.5 px**, a 0.9 m walking aisle is **11 px**, a
2.4 m furnace stack is **30 px** and a 4.5 m fixture pitch is **56 px**.  The
finest structure the comparison has to resolve is an aisle between furniture,
and it is eleven pixels across.

**THE PLAN IS FITTED TO THE ROOM'S OWN FOOTPRINT AND THE SECTION'S HEIGHT IS
NOT, and that asymmetry is the one real design decision in this file.**  It was
made by measurement.  Three mappings were built and all three are still
runnable, because the difference between them is itself a finding:

    fit      each horizontal axis stretched to the room's own footprint.
             PURE LAYOUT: where things stand relative to the room.  DEFAULT.
    uniform  one scale factor, the room's longest extent.  Layout + aspect.
    metric   a fixed 19.2 m window.  Layout + aspect + absolute size.

`metric` was the first version, on the reasoning that a 4.5 m fixture pitch is
the same 4.5 m in any room.  Run, it scored `medlab_one` against `morgue` at
**0.317** and `uniform` scored the same pair at **0.184** -- two rooms out of
the same generic kit, the same archetype, the same fixture list and the same
props, called *different places* because one is 10.5 m long and the other 8.3
m.  Under both, the channel doing the work was the WALL POSITION: these rooms
are near-empty at knee height, so the wall ring is most of the occupancy, and
a room 27% longer puts its walls somewhere the other's are not.

A player cannot tell a 6 x 8 m room from a 6 x 10 m one.  A gate that can is
not measuring distinguishability, it is **manufacturing variety out of a
footprint number** -- which is precisely the flattery this milestone exists to
stop, and the same defect as a coverage count that is satisfied by one generic
thing repeated seventy-eight times.  So the default fits both axes, and size
and aspect are reported on their own axes by `--drivers` rather than smuggled
into the score.  This follows `body.py`, which divides stature out of the
silhouette and asserts it separately.

**The section's vertical axis stays in METRES from the room's own measured
floor**, and that is not an inconsistency.  A metre of height is measured
against the observer's own body -- a player reads a 7.5 m foundry and a 2.9 m
office instantly -- and a metre of plan is not.  Normalising height too would
have scored a 13.6 m foundry (7.6/13.6 = 0.56) and an 8.3 m medlab
(3.1/8.3 = 0.38) by their proportion, and proportion is not what a ceiling is.

`--mode uniform` and `--mode metric` run the whole matrix the other way, and
the difference between the three is reported in `docs/variety-V0.md`.

Nothing clips: the mapping leaves a 5% margin and `occupancy` counts any
occupied cell touching the border, because a clipped plan scores two different
rooms identical along the clip -- `body.py`'s `HEAD_BAND_SPAN` check, one
dimension up.

Occupancy is measured by **a winding walk down each column**, not by splatting
vertices and not by projecting filled triangles.  Both of those were tried in
`body.py`'s history and both are wrong here for a reason worth writing down: a
vertical wall's triangles project to a LINE in plan, so a filled projection of a
closed room draws its walls one pixel wide and its floor solid, and an IoU of
one-pixel lines moves by half its value when a wall shifts by 8 cm.  The walk
uses the horizontal faces -- which is what a solid always has -- and returns the
room's actual matter.

Run:

    python3 station/variety.py                 # the gate, with every control
    python3 station/variety.py --matrix        # all 8,128 pairs + the clusters
    python3 station/variety.py --drivers       # what the variance is made of
    python3 station/variety.py --derive        # recompute the ceiling; fails on drift
    python3 station/variety.py --pair a b      # one pair, per channel
    python3 station/variety.py --plan KEY      # an ASCII plan of the walking band
    python3 station/variety.py --verify-cache  # rebuild sampled rooms, diff the cache
    python3 station/variety.py --mode metric … # any of the above, other mapping

The findings, the derivations and what V1 should key on are in
`docs/variety-V0.md`.
"""

import argparse
import collections
import hashlib
import inspect
import json
import math
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bespoke as BSP                                          # noqa: E402
import deck as DECK                                            # noqa: E402
import directory as DIR                                        # noqa: E402
import interior as IT                                          # noqa: E402
import rooms as R                                              # noqa: E402

# ---------------------------------------------------------------------------
# The sampling grid.  See the module docstring for the pixel spans these give.
# ---------------------------------------------------------------------------
CELL_M = 0.08                                   # metres per cell, VERTICAL
WIN_M = 19.2                                    # the `--mode metric` window
NX = NZ = int(round(WIN_M / CELL_M))            # 240
SECT_H_M = 9.6                                  # tallest archetype is 7.5 m
NY = int(round(SECT_H_M / CELL_M))              # 120
# The normalised plan's scale: the room's longest horizontal extent plus this
# much margin, so a room's own walls never sit on the border of its raster.
PLAN_MARGIN = 1.05

# The band a body occupies, measured from the room's own measured floor.  Above
# the deck's own decoration -- `rooms.SKIRT_H_M` is 0.14, `DECK_TILE_M`'s tiles
# stand 22 mm proud and the corridor's lighting channel is 66 mm -- and below
# the head, so a soffit is not part of the comparison either.
#
# 0.30 AND NOT 0.90, AND THE FIRST VERSION HAD IT AT 0.90.  "Above the knee"
# sounds like the right description of what a player walks among and it is not:
# `dressing.SCHEMES`' own vocabulary is 8 objects and their heights are
# table 0.74, chair 0.95, crate 0.50-0.80, can 0.90, bin 0.60-0.80, console
# 1.10, locker 1.90, shelf 1.80-2.40.  A 0.90 m floor threw away the TABLES AND
# THE CRATES -- half the vocabulary, and in a bar or a mess hall most of the
# furniture -- so the plan channel was comparing rooms with their tables
# removed.  It is the same defect as a gate that measures the case without the
# defect in it, one level down: the band was chosen to exclude the floor and
# happened to exclude the furniture.
WALK_LO_M, WALK_HI_M = 0.30, 2.00
_BAND = ((1 << int(WALK_HI_M / CELL_M)) - 1) ^ ((1 << int(WALK_LO_M / CELL_M)) - 1)

# ---------------------------------------------------------------------------
# THE CEILING, AND IT IS DERIVED RATHER THAN CHOSEN
# ---------------------------------------------------------------------------
# `python3 station/variety.py --derive` recomputes it and FAILS if the recorded
# value has drifted, which is `tools/measure_frame.py --derive`'s idiom and
# exists for the same reason: a tolerance somebody typed is a tolerance somebody
# can retype when it becomes inconvenient.
#
# The derivation is one sentence.  **Two places are indistinguishable when they
# are no more different than the same room built twice.**  `clone_place` builds
# a place under a second key, which changes every random stream in `rooms.build`
# and `dressing.dress` and nothing else -- same archetype, same footprint, same
# declared fixtures, same props.  Done once per archetype, the LOWEST score any
# such pair reaches is the empirical value of "identical place", and the ceiling
# is that, rounded down to the nearest 0.01 so every clone is strictly above it.
#
# It has the property a threshold needs: it cannot be argued with.  It is not a
# number about how similar rooms ought to look, it is a number about how similar
# this generator's own output is to itself.
#
# Measured over all 11 archetypes (`--derive` prints the whole table):
#
#     industrial  fabrication      0.736     office      war_room         0.929
#     store       cargo_bays       0.880     detention   brig             0.948
#     commerce    business_center  0.912     worship     sanctuary_blue   0.951
#     hospitality mess_hall        0.913     medical     medlab_one       0.963
#     generic     obs_dome_1       0.924     transit     central_corridor 0.966
#     research    research_labs    0.928
#
# The weakest is `industrial` at 0.736 and the reason is legible: its dressing
# scheme is four kinds of small movable object at the second-highest density on
# the station, so a re-seed has the most to move.  The strongest is `transit`
# at 0.966, whose rooms have almost nothing in them to re-seed.  Every one of
# the eleven re-seeds at 1.000 in the SECTION channel, which is a channel-level
# control in its own right: the shell does not depend on the seed, and if it
# ever appears to, this file is wrong before the generator is.
#
# THE MINIMUM RATHER THAN THE MEDIAN, and the direction is worth stating
# because it is the opposite of what it sounds like.  A HIGHER ceiling flags
# FEWER pairs.  Measured over the same 8,128:
#
#     ceiling 0.963 (best re-seed)      0 pairs   0 clusters    0 places
#     ceiling 0.913                    33 pairs  11 clusters   31 places
#     ceiling 0.880                    46 pairs  17 clusters   46 places
#     ceiling 0.800                    76 pairs  24 clusters   69 places
#     ceiling 0.736 (worst re-seed)    99 pairs  27 clusters   82 places
#     ceiling 0.700                   120 pairs  26 clusters   85 places
#
# So the minimum is the SENSITIVE end.  The logical statement it supports is
# the strict one -- a pair above 0.736 is AT LEAST AS SIMILAR as two builds of
# one industrial room, which is a thing a player calls the same room -- and the
# check on it is that its output is verifiable by eye rather than on trust.
# The 35 pairs the move from 0.85 to 0.736 adds include `arrival_concourse` vs
# `customs_north`, `qtr_civilian` vs `qtr_personnel`, `cargo_bays` vs
# `spinal_cargo` and `bar_unnamed` vs `fresh_air`.  Every one of those is one
# room twice.  Nothing in the band needs a metric to adjudicate.
#
# The obvious refinement, recorded rather than built: the re-seed score is
# archetype-dependent because it depends on how much furniture there is to
# shuffle -- 0.736 to 0.966 is a wide spread -- so a pair's honest ceiling is
# `min(reseed[arch(a)], reseed[arch(b)])` rather than one number for the
# station.  That is a better instrument and it needs the table above to become
# a gate input rather than a comment.
SEED_CLONE_WORST = 0.736
PLACE_IOU_MAX = 0.73

# Group-name role prefixes stripped when canonicalising the content vocabulary.
# See `canon_group`.
_ROLE_PREFIXES = ("dress", "fix", "prop", "mp")


# ---------------------------------------------------------------------------
# Occupancy
# ---------------------------------------------------------------------------
def _spans_of(groups, ntris):
    """(name, lo, hi) spans, whichever shape the builder used. `bespoke._spans`."""
    return BSP._spans(groups, ntris)


MODES = ("fit", "uniform", "metric")


def occupancy(verts, tris, groups, module=None, mode="fit", nx=NX, nz=NZ,
              ny=NY, drop=("npc_",)):
    """The solid matter of one room, as three marginals of one field.

    Returns a dict with:
      ``plan``  -- ``bytearray(nx*nz)``, 1 where the column holds solid matter
                   anywhere in the walking band above the room's own floor;
      (see ``open`` below for what happens where a mesh is not closed)
      ``sect_x``-- ``nx`` ints, bit *j* set if any z at that x is solid in
                   y-bin *j*.  The room's CROSS-section: clear height, wall
                   thickness, a spine fixture's bump, overhead services;
      ``sect_z``-- ``nz`` ints, the LONGitudinal section: rib rhythm, fixture
                   pitch in elevation, how the room changes down its length;
      ``area``  -- canonical group name -> triangle area inside the window;
      plus ``floor_y``, ``open`` (columns where the mesh was not closed and a
      face had to be recovered as a one-cell slab) and the raw extents.

    The field is sampled by a WINDING WALK down each column.  For every triangle
    with non-zero projected area in plan -- which is every horizontal and
    sloping face, and no vertical one -- the plane's y is evaluated at each cell
    centre the triangle covers, and recorded with the sign of the face: a
    down-facing triangle is a solid being ENTERED as the ray rises, an up-facing
    one is a solid being LEFT.  Sorting by height and walking a depth counter
    gives the solid intervals exactly, for any closed mesh, and handles
    coincidence and nesting for free: a crate whose underside sits on the deck
    contributes an exit and an entry at the same height and the column stays
    solid through it.

    PLAIN EVEN-ODD PARITY WAS THE FIRST VERSION AND `command_control` BROKE IT.
    Its floor, dais and pit are `_disc` and `_ring` fans -- single-sided plates
    with no underside, which is the right way to model a floor plate and not a
    closed solid -- so 49,952 of its columns came back with an odd crossing
    count and parity had to throw a crossing away in every one of them.  The
    room a player sees is not a defect; the measurement was.

    So an unmatched face is not dropped and not guessed at: it becomes a slab
    ONE CELL thick at its own height, which is what a single-sided plate
    physically is, and the number of columns where that happened is returned as
    ``open`` and printed by `--matrix`.  A measurement that silently degrades is
    worse than one that fails, and this repository has the scar to prove it.
    """
    spans = _spans_of(groups, len(tris))
    skip = bytearray(len(tris))
    for name, lo, hi in spans:
        if any(name.startswith(d) for d in drop):
            for i in range(lo, hi):
                skip[i] = 1

    xs = [p[0] for p in verts]
    zs = [p[2] for p in verts]
    ext_x, ext_z = max(xs) - min(xs), max(zs) - min(zs)
    cx = (min(xs) + max(xs)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    fy = BSP.floor_y(verts, tris, groups, module)
    # The horizontal mapping.  See MODES and the module docstring.
    if mode == "metric":
        cell_x = cell_z = CELL_M
    elif mode == "uniform":
        cell_x = cell_z = max(max(ext_x, ext_z) * PLAN_MARGIN / nx, 1e-6)
    else:
        cell_x = max(ext_x * PLAN_MARGIN / nx, 1e-6)
        cell_z = max(ext_z * PLAN_MARGIN / nz, 1e-6)
    celly = CELL_M

    # Column crossing lists, flat.  57,600 empty lists is ~4 ms.
    cols = [None] * (nx * nz)
    half_x, half_z = nx * cell_x / 2.0, nz * cell_z / 2.0
    odd = 0

    for i, (a, b, c) in enumerate(tris):
        if skip[i]:
            continue
        p0, p1, p2 = verts[a], verts[b], verts[c]
        # Plane normal.  n[1] == 0 is a vertical face: no projected area, and
        # parity does not need it.
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        w = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        n1 = u[2] * w[0] - u[0] * w[2]
        if abs(n1) < 1e-12:
            continue
        n0 = u[1] * w[2] - u[2] * w[1]
        n2 = u[0] * w[1] - u[1] * w[0]
        # +1 = a down-facing face, i.e. a solid being ENTERED by a ray rising
        # through this column; -1 = an up-facing face, i.e. one being left.
        sgn = 1 if n1 < 0.0 else -1
        # Cell-space coordinates, (col, row) = (x, z).
        ax = (p0[0] - cx + half_x) / cell_x
        ay = (p0[2] - cz + half_z) / cell_z
        bx = (p1[0] - cx + half_x) / cell_x
        by = (p1[2] - cz + half_z) / cell_z
        gx = (p2[0] - cx + half_x) / cell_x
        gy = (p2[2] - cz + half_z) / cell_z
        r0 = max(0, int(math.floor(min(ay, by, gy))))
        r1 = min(nz - 1, int(math.ceil(max(ay, by, gy))))
        if r1 < r0:
            continue
        for row in range(r0, r1 + 1):
            yc = row + 0.5
            hits = []
            for (px, py), (qx, qy) in (((ax, ay), (bx, by)),
                                       ((bx, by), (gx, gy)),
                                       ((gx, gy), (ax, ay))):
                if (py <= yc < qy) or (qy <= yc < py):
                    hits.append(px + (qx - px) * (yc - py) / (qy - py))
            if len(hits) < 2:
                continue
            hits.sort()
            # WATERTIGHT, and the first version of this was not.  A cell is
            # claimed when its CENTRE lies in [x0, x1), half-open at both the
            # row rule above and the column rule here.  With the obvious
            # `floor(x+0.5) .. ceil(x-0.5)` nearest-integer fill, two triangles
            # sharing a quad's diagonal both claim the boundary cell -- so a
            # box's top face contributes two crossings there and its bottom
            # face one, and the parity comes out ODD.  Measured: 2,877 of ~4,500
            # occupied columns in `medlab_one` came back unbalanced before this
            # line, which is the mesh being reported open where it is closed.
            c0 = max(0, math.ceil(hits[0] - 0.5))
            c1 = min(nx - 1, math.ceil(hits[-1] - 0.5) - 1)
            if c1 < c0:
                continue
            wz = cz - half_z + yc * cell_z
            base = row * nx
            for col in range(c0, c1 + 1):
                wx = cx - half_x + (col + 0.5) * cell_x
                y = p0[1] - (n0 * (wx - p0[0]) + n2 * (wz - p0[2])) / n1
                k = base + col
                if cols[k] is None:
                    cols[k] = [(y, sgn)]
                else:
                    cols[k].append((y, sgn))

    plan = bytearray(nx * nz)
    sect_x = [0] * nx
    sect_z = [0] * nz
    top = ny * celly
    hit_cols = 0
    for k, ys in enumerate(cols):
        if not ys:
            continue
        hit_cols += 1
        ys.sort()
        depth, start, runs, broke = 0, None, [], False
        for y, s in ys:
            prev = depth
            depth += s
            if depth < 0:                    # left a solid never entered
                depth, broke = 0, True
                runs.append((y, y + celly))
                continue
            if prev == 0 and depth > 0:
                start = y
            elif prev > 0 and depth == 0 and start is not None:
                runs.append((start, y))
                start = None
        if start is not None:                # entered a solid never left
            broke = True
            runs.append((start, start + celly))
        if broke:
            odd += 1
        mask = 0
        for lo_w, hi_w in runs:
            lo, hi = lo_w - fy, hi_w - fy
            if hi <= 0.0 or lo >= top:
                continue
            b0 = max(0, int(lo / celly))
            b1 = min(ny, int(math.ceil(hi / celly)))
            if b1 > b0:
                mask |= ((1 << (b1 - b0)) - 1) << b0
        if not mask:
            continue
        if mask & _BAND:
            plan[k] = 1
        sect_x[k % nx] |= mask
        sect_z[k // nx] |= mask

    # NOTHING TOUCHES THE BORDER.  A clipped plan scores two different rooms as
    # identical along the clip, which is `body.py`'s five-pixel head in plan
    # view.  Counted rather than raised, so a bespoke room whose furniture runs
    # past its own shell is visible in `--matrix` instead of killing the sweep.
    clipped = 0
    for c in range(nx):
        if plan[c] or plan[(nz - 1) * nx + c]:
            clipped += 1
    for r in range(nz):
        if plan[r * nx] or plan[r * nx + nx - 1]:
            clipped += 1

    # Content: triangle area per canonical group name, window-clipped by
    # centroid.  Area rather than triangle count, because a tessellated
    # cylinder is not more of a room than a box is.
    # OBJECTS, NOT THE ROOM ITSELF, and the split is `rooms.is_solid`'s -- the
    # same definition the density trial and `collision.prop_boxes` use, so
    # there is not a second one to drift.  Measured with the shell in, a medlab
    # and a foundry read 0.951 on content, because wall and soffit area swamps
    # everything standing in the room: a 7.9 x 6.0 m box is ~120 m2 of shell
    # against ~30 m2 of furniture.  The shell is already the plan and section
    # channels' subject; asking the content channel about it too would be
    # counting one fact three times and hiding the one it was added for.
    shell_tok = _shell_token(spans)
    area = collections.Counter()
    raw = collections.Counter()
    area_all = collections.Counter()
    for name, lo, hi in spans:
        if any(name.startswith(d) for d in drop):
            continue
        s = 0.0
        for i in range(lo, hi):
            a, b, c = tris[i]
            p0, p1, p2 = verts[a], verts[b], verts[c]
            if abs(((p0[0] + p1[0] + p2[0]) / 3.0) - cx) > half_x or \
               abs(((p0[2] + p1[2] + p2[2]) / 3.0) - cz) > half_z:
                continue
            u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            w = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            n = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
                 u[0] * w[1] - u[1] * w[0])
            s += 0.5 * math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
        if s <= 0.0:
            continue
        area_all[canon_group(name, shell_tok)] += s
        if R.is_solid(name):
            area[canon_group(name, shell_tok)] += s
            raw[name] += s

    return {"plan": plan, "sect_x": sect_x, "sect_z": sect_z,
            "area": dict(area), "raw_area": dict(raw),
            "area_all": dict(area_all), "floor_y": fy,
            "open": odd, "cols": hit_cols, "clipped": clipped,
            "nx": nx, "nz": nz, "ny": ny, "mode": mode,
            "cell": (cell_x, cell_z),
            "extent": (ext_x, ext_z),
            "height": max(p[1] for p in verts) - fy}


def _shell_token(spans):
    """The token a room prefixes its own shell with -- 'medical', 'qtr', 'zoc'.

    DERIVED FROM THE MESH, not from a list somebody maintains.  Every builder
    on the station names its shell `<token>_deck` / `_wall` / `_soffit`, so the
    token is the most common first word among those groups.  A list would have
    to be extended every time a module is added, and the failure mode of
    forgetting is silent: an unstripped prefix makes two identical boxes look
    like different content.
    """
    c = collections.Counter()
    for name, _lo, _hi in spans:
        if name.endswith(("_deck", "_wall", "_soffit")):
            c[name.split("_")[0]] += 1
    return c.most_common(1)[0][0] if c else None


def canon_group(name, shell_tok=None):
    """A group name reduced to WHAT THE OBJECT IS.

    `medical_wall` and `office_wall` are the same box emitted by the same line
    of `rooms.build` with a different string in front of it.  Comparing raw
    names would score those two rooms as having different content, which is
    false and flattering -- the archetype prefix would be manufacturing
    variety out of nothing.  So the room's own shell token is stripped, and
    then the role prefixes (`dress_`, `fix_`, `prop_`, `mp_`) are stripped
    repeatedly, which collapses `fix_mp_dress_screen` and `dress_mp_dress_screen`
    onto `screen` -- they are one object placed by two code paths.

    `light_` is deliberately NOT stripped: a light fitting is a thing in the
    room, and the remainder of the name is unique anyway.

    `--matrix --raw-content` reports the same matrix without this, and the
    difference between the two is how much of the station's apparent content
    variety is only the prefix.
    """
    parts = name.split("_")
    if shell_tok and parts and parts[0] == shell_tok:
        parts = parts[1:]
    while len(parts) > 1 and parts[0] in _ROLE_PREFIXES:
        parts = parts[1:]
    return "_".join(parts) or name


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------
def plan_bits(o):
    """The plan mask as ONE integer, memoised on the occupancy dict.

    8,128 pairs x 57,600 cells is 468 million byte comparisons in a Python
    loop, and `--drivers` builds six matrices.  As a big integer the same
    comparison is `(a & b).bit_count()` in C.  Deliberately NOT computed inside
    `occupancy`: the cache key hashes that function's source, so putting a pure
    speed-up there would throw away a sixteen-minute rebuild for nothing.
    """
    b = o.get("plan_bits")
    if b is None:
        b = 0
        for i, v in enumerate(o["plan"]):
            if v:
                b |= 1 << i
        o["plan_bits"] = b
    return b


def mask_iou(a, b):
    """Intersection over union of two plan masks."""
    x, y = plan_bits(a) if isinstance(a, dict) else a, \
        plan_bits(b) if isinstance(b, dict) else b
    if isinstance(x, (bytes, bytearray)):
        inter = union = 0
        for p, q in zip(x, y):
            if p or q:
                union += 1
                if p and q:
                    inter += 1
        return inter / max(1, union)
    return (x & y).bit_count() / max(1, (x | y).bit_count())


def bits_iou(a, b):
    """IoU of two lists of bitmask ints -- a section against a section."""
    inter = union = 0
    for x, y in zip(a, b):
        inter += (x & y).bit_count()
        union += (x | y).bit_count()
    return inter / max(1, union)


def cosine(a, b):
    """Cosine of two name -> weight vectors."""
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    num = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return num / max(1e-12, na * nb)


def channels(o1, o2, content_key="area"):
    """Every channel for one pair, including the sub-scores.

    `plan` and `sect` are TWO VIEWS OF ONE THING -- the room's solid form, from
    above and from the side -- so `form` is the min of them, which is
    `body.py`'s rule exactly: a pair's score is the view they differ most in,
    because two things differ if there is any angle a player can tell them
    apart from.  `sect` is itself already the harsher of the cross-section and
    the longitudinal section for the same reason.

    `content` is a different question -- not a third view but a different
    property, the way stature is not a third view of a species.
    """
    plan = mask_iou(o1, o2)
    sx = bits_iou(o1["sect_x"], o2["sect_x"])
    sz = bits_iou(o1["sect_z"], o2["sect_z"])
    con = cosine(o1[content_key], o2[content_key])
    sect = min(sx, sz)
    return {"plan": plan, "sect": sect, "sect_x": sx, "sect_z": sz,
            "content": con, "form": min(plan, sect)}


def score(o1, o2, content_key="area"):
    """One number for a pair: the channel they differ MOST in.

    Two places are the same place only if they are the same shape AND the same
    layout AND the same stuff.  That makes the gate deliberately hard to fail
    and therefore credible when it does: a pair over the ceiling cannot be
    argued away with "but the props are different", because the props were
    checked.

    `channels(...)["form"]` is the sub-score that matters for V1 and it is
    reported alongside, because form is the half a generator has to produce and
    it is much the worse of the two.
    """
    ch = channels(o1, o2, content_key)
    return min(ch["form"], ch["content"]), ch


# ---------------------------------------------------------------------------
# Building the 128
# ---------------------------------------------------------------------------
_CACHE_VER = 3


def _source_stamp():
    """Hash of everything this measurement's stored numbers depend on.

    A cache that can go stale silently is a second copy of a computed number --
    `budget.py`'s cached collision total is this repository's own example.  So
    the key is the exact dependency set and nothing else: the source of every
    module that BUILDS a room, the source of `occupancy` itself, and the grid
    parameters.  Change any of them and every entry is invalidated.

    `occupancy`'s source rather than this whole file, deliberately.  Hashing
    `variety.py` wholesale means editing a print statement throws away a
    sixteen-minute rebuild, which is the pressure that makes people turn caches
    off.  What is stored is rasterised occupancy; the reporting code cannot
    change it, and `--verify-cache` rebuilds sampled rooms and diffs them
    against the store so the claim is checked rather than asserted.
    """
    h = hashlib.sha256()
    for f in sorted(("rooms.py", "bespoke.py", "dressing.py", "deck.py",
                     "directory.py", "interior_kit.py", "interior.py",
                     "quarters.py", "zocalo.py", "customs.py", "plant.py",
                     "hospitality.py", "alien_sector.py", "command_control.py",
                     "council_chamber.py", "docking_bay.py", "populace.py")):
        p = os.path.join(_HERE, f)
        if os.path.exists(p):
            with open(p, "rb") as fh:
                h.update(fh.read())
    h.update(inspect.getsource(occupancy).encode())
    h.update(inspect.getsource(canon_group).encode())
    h.update(f"{_CACHE_VER}:{CELL_M}:{WIN_M}:{NY}:{WALK_LO_M}:{WALK_HI_M}"
             .encode())
    return h.hexdigest()[:16]


def _cache_path():
    d = os.environ.get("VARIETY_CACHE") or os.path.join(
        os.path.dirname(_HERE), ".variety-cache")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"places-{_source_stamp()}.json")


def _pack(o):
    d = {k: o[k] for k in ("area", "raw_area", "area_all", "floor_y", "open",
                           "cols", "clipped", "nx", "nz", "ny", "mode",
                           "cell", "height")}
    n = len(o["plan"])
    bits = 0
    for i, b in enumerate(o["plan"]):
        if b:
            bits |= 1 << i
    d.update({"plan": "%x" % bits, "plan_n": n,
              "sect_x": [hex(v) for v in o["sect_x"]],
              "sect_z": [hex(v) for v in o["sect_z"]],
              "extent": list(o["extent"]),
              "used": o.get("used"), "tris": o.get("tris")})
    for m in MODES:
        if o.get(m):
            d[m] = _pack(o[m])
    return d


def _unpack(d):
    d = dict(d)
    bits = int(d["plan"], 16)
    d["plan"] = bytearray((bits >> i) & 1 for i in range(d["plan_n"]))
    d["plan_bits"] = bits
    d["sect_x"] = [int(v, 16) for v in d["sect_x"]]
    d["sect_z"] = [int(v, 16) for v in d["sect_z"]]
    d["extent"] = tuple(d["extent"])
    for m in MODES:
        if d.get(m):
            d[m] = _unpack(d[m])
    return d


def place_occupancy(schema, profile, place, modes=MODES):
    """Build one place through the SAME dispatcher the deck assembler uses.

    `deck.room_geometry` is the single decision about what a player actually
    walks into -- bespoke where a module owns the place and the doorway is
    clear, `rooms.build` otherwise.  Measuring anything else would be measuring
    a room nobody enters, which is hard rule 4's failure mode: two descriptions
    of one thing.

    All three mappings come off ONE build, so the three matrices can never be
    taken from different geometry -- the same reason `--gate-frames --rerender`
    exists.  The returned object is the `fit` mapping with the others hung off
    it under their own names.
    """
    v, t, g, used = DECK.room_geometry(schema, profile, place)
    out = {}
    for m in modes:
        o = occupancy(v, t, g, place.get("module"), mode=m)
        o["used"], o["tris"] = used, len(t)
        out[m] = o
    top = out.get("fit") or out[modes[0]]
    for m in modes:
        if out[m] is not top:
            top[m] = out[m]
    return top


def view(o, mode="fit"):
    """One place's occupancy under a named mapping."""
    if mode == "fit" or o.get("mode") == mode:
        return o
    return o[mode]


def load_all(keys=None, rebuild=False, verbose=False, extra=()):
    """Occupancy for all 128 places, cached on a hash of the builders."""
    path = _cache_path()
    store = {}
    if os.path.exists(path) and not rebuild:
        with open(path) as fh:
            store = json.load(fh)
    schema, profile = IT.load()
    places = list(DIR.PLACES) + list(extra)
    if keys is not None:
        want = set(keys)
        places = [q for q in places if q["key"] in want]
    out, dirty = {}, False
    for q in places:
        k = q["key"]
        if k in store:
            out[k] = _unpack(store[k])
            continue
        t0 = time.time()
        try:
            o = place_occupancy(schema, profile, q)
        except Exception as exc:                                # noqa: BLE001
            if verbose:
                print(f"  {k:26} FAILED {str(exc)[:70]}")
            continue
        out[k] = o
        store[k] = _pack(o)
        dirty = True
        if verbose:
            print(f"  {k:26} {o['used']:8} {o['tris']:8,} tri  "
                  f"{time.time() - t0:6.2f}s  open={o['open']:,}")
    if dirty:
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(store, fh)
        os.replace(tmp, path)
    return out


ARCHETYPE_PROBE = ("medlab_one", "brig", "sanctuary_blue", "fabrication",
                   "research_labs", "cargo_bays", "central_corridor",
                   "mess_hall", "business_center", "war_room", "obs_dome_1")


def derive_ceiling(out=print, mode="fit"):
    """Rebuild the ceiling from the generator's own repeatability.

    One representative place per archetype, built twice under two keys that
    exist nowhere in `rooms.PLACE_FIXTURES`, `PLACE_LIGHTS` or `PLACE_CEILING`,
    so both clones miss those tables equally and differ ONLY in seed.  The
    weakest of those pairs is the empirical value of "the same room", and the
    ceiling is it rounded down to 0.01.

    Returns (recorded, derived, rows) and the caller fails on a mismatch.
    """
    schema, profile = IT.load()
    rows = []
    for key in ARCHETYPE_PROBE:
        q = DIR.by_key(key)
        a = place_occupancy(schema, profile, clone_place(q, f"probe_a_{key}"),
                            modes=(mode,))
        b = place_occupancy(schema, profile, clone_place(q, f"probe_b_{key}"),
                            modes=(mode,))
        s, ch = score(a, b)
        rows.append((R.archetype(q), key, s, ch))
    rows.sort(key=lambda r: r[2])
    out(f"\n  {'archetype':12} {'probe':18} {'score':>7} {'plan':>7} "
        f"{'sect':>7} {'content':>8}")
    for arch, key, s, ch in rows:
        out(f"  {arch:12} {key:18} {s:>7.3f} {ch['plan']:>7.3f} "
            f"{ch['sect']:>7.3f} {ch['content']:>8.3f}")
    worst = rows[0][2]
    derived = math.floor(worst * 100.0) / 100.0
    out(f"\n  the weakest re-seed pair is {rows[0][0]} at {worst:.3f}")
    out(f"  ceiling = floor(that, 0.01) = {derived:.2f}   "
        f"(recorded {PLACE_IOU_MAX:.2f}, SEED_CLONE_WORST "
        f"{SEED_CLONE_WORST:.3f})")
    return derived, worst, rows


def verify_cache(n=6, out=print, seed=0):
    """Rebuild sampled rooms and diff them against the cache.

    `--gate-frames` could measure a committed PNG and never say whether the file
    still described the code, and eleven of fourteen lighting failures turned
    out to be that.  This is the same trap one level down: the cache stores
    rasterised occupancy keyed on a hash, and a hash is a claim.  This checks
    it.
    """
    import random                                               # noqa: PLC0415
    path = _cache_path()
    if not os.path.exists(path):
        out(f"  no cache at {path}")
        return 1
    with open(path) as fh:
        store = json.load(fh)
    schema, profile = IT.load()
    keys = sorted(store)
    rng = random.Random(seed)
    pick = rng.sample(keys, min(n, len(keys)))
    bad = 0
    for k in pick:
        q = DIR.by_key(k)
        fresh = _pack(place_occupancy(schema, profile, q))
        same = all(fresh[f] == store[k][f] for f in ("plan", "sect_x",
                                                     "sect_z", "area"))
        out(f"  {k:26} {'MATCHES' if same else 'DIFFERS FROM'} the cache")
        bad += 0 if same else 1
    out(f"  {len(pick) - bad} of {len(pick)} sampled rooms rebuild identically")
    return bad


def clone_place(place, key):
    """The same place with a different key -- i.e. only the SEED changed.

    Every stochastic choice in `rooms.build` is drawn from `place["key"]`:
    `_fixture(..., seed=(place["key"], i))` and `dressing.dress(place["key"],
    ...)`.  So a place cloned under a new key is the same archetype, the same
    footprint, the same declared fixtures and a different random stream, which
    is exactly the control the V0 task specifies.

    The clone key must NOT collide with `rooms.PLACE_FIXTURES`,
    `PLACE_LIGHTS` or `PLACE_CEILING`; both clones miss those tables equally,
    so they stay identical to each other in everything but the seed.
    """
    q = dict(place)
    q["key"] = key
    return q


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------
def matrix(occ, keys=None, content_key="area"):
    """Every pair.  Returns {(a,b): (score, channels)} with a < b in `keys`."""
    keys = list(keys if keys is not None else occ)
    out = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            out[(a, b)] = score(occ[a], occ[b], content_key)
    return out


def clusters(pairs, keys, ceiling=PLACE_IOU_MAX):
    """Single-linkage groups of places nothing can tell apart.

    Single linkage rather than complete: if A is indistinguishable from B and B
    from C, a player walking A->B->C has seen one room three times even if A
    and C differ.  That is the experience the owner described.
    """
    parent = {k: k for k in keys}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), (s, _ch) in pairs.items():
        if s > ceiling:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    groups = collections.defaultdict(list)
    for k in keys:
        groups[find(k)].append(k)
    return sorted((v for v in groups.values() if len(v) > 1),
                  key=len, reverse=True)


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    i = min(len(xs) - 1, max(0, int(round(p / 100.0 * (len(xs) - 1)))))
    return xs[i]


def report_matrix(out=print, content_key="area", rebuild=False, mode="fit"):
    occ = load_all(rebuild=rebuild, verbose=True)
    keys = sorted(occ)
    vw = {k: view(occ[k], mode) for k in keys}
    out(f"\n{len(keys)} places measured under the {mode!r} mapping, "
        f"{len(keys) * (len(keys) - 1) // 2:,} pairs")
    used = collections.Counter(occ[k]["used"] for k in keys)
    out(f"  built by: {dict(used)}")
    op = [k for k in keys if occ[k]["open"] > 0]
    if op:
        out(f"  meshes NOT CLOSED above at least one column: {len(op)} places, "
            f"worst {max(occ[k]['open'] for k in op):,} columns "
            f"({', '.join(sorted(op, key=lambda k: -occ[k]['open'])[:6])})")
    clip = [k for k in keys if vw[k]["clipped"] > 0]
    if clip:
        out(f"  occupancy touching the raster border: {len(clip)} places "
            f"-- their plans are clipped and score too similar")
    big = sorted(keys, key=lambda k: -max(occ[k]["extent"]))[:6]
    out("  largest places (the mapping normalises these; their absolute size "
        "is on its own axis):")
    for k in big:
        e = occ[k]["extent"]
        out(f"    {k:24} {e[0]:7.1f} x {e[1]:7.1f} m, {occ[k]['height']:5.1f} "
            f"m tall")

    pairs = matrix(vw, keys, content_key)
    scores = [s for s, _ in pairs.values()]
    out(f"\n  PAIRWISE SCORE = min(form, content),  form = min(plan, section)")
    hdr = f"    {'':6} {'score':>7} {'form':>7} {'plan':>7} {'sect':>7} " \
          f"{'content':>8}"
    out(hdr)
    cols = {"score": scores}
    for ch in ("form", "plan", "sect", "content"):
        cols[ch] = [c[ch] for _s, c in pairs.values()]
    for p in (5, 25, 50, 75, 95, 100):
        out(f"    p{p:<5} " + " ".join(
            f"{_pct(cols[c], p):>7.3f}" for c in
            ("score", "form", "plan", "sect")) +
            f" {_pct(cols['content'], p):>8.3f}")
    n = len(scores)
    out(f"\n  ABOVE THE {PLACE_IOU_MAX} CEILING")
    for c in ("score", "form", "plan", "sect", "content"):
        k = sum(1 for x in cols[c] if x > PLACE_IOU_MAX)
        out(f"    {c:8} {k:6,} of {n:,} pairs  ({100.0 * k / n:5.1f}%)")

    cl = clusters(pairs, keys)
    out(f"\n  {len(cl)} CLUSTERS OF MUTUALLY INDISTINGUISHABLE PLACES, "
        f"covering {sum(len(c) for c in cl)} of {len(keys)}")
    for c in cl:
        arch = collections.Counter(R.archetype(DIR.by_key(k)) for k in c)
        out(f"    {len(c):3}  "
            f"{'/'.join(f'{a}:{n_}' for a, n_ in arch.most_common())}")
        for i in range(0, len(sorted(c)), 6):
            out("           " + ", ".join(sorted(c)[i:i + 6]))

    fcl = clusters({k: (v[1]["form"], v[1]) for k, v in pairs.items()}, keys)
    out(f"\n  ...and on FORM ALONE -- the half a generator has to produce -- "
        f"{len(fcl)} clusters covering {sum(len(c) for c in fcl)} of "
        f"{len(keys)}, largest {max((len(c) for c in fcl), default=0)}")
    return occ, pairs


def report_drivers(out=print, mode="fit"):
    """What the variance that DOES exist is made of.

    The question V1 has to answer is what a form grammar should key on, and the
    honest way to choose is to measure which of the register's existing facts
    already predicts distinguishability and which does not.  A fact that
    separates nothing is a fact the generator is ignoring.
    """
    occ = load_all()
    keys = sorted(occ)
    vw = {k: view(occ[k], mode) for k in keys}
    pairs = matrix(vw, keys)
    P = {k: DIR.by_key(k) for k in keys}

    def split(name, pred, key="score"):
        def val(pr):
            return pr[0] if key == "score" else pr[1][key]
        same = [val(v) for (a, b), v in pairs.items() if pred(P[a], P[b])]
        diff = [val(v) for (a, b), v in pairs.items() if not pred(P[a], P[b])]
        if not same or not diff:
            out(f"  {name:26} (degenerate split)")
            return
        out(f"  {name:26} share it {_pct(same, 50):.3f} (n={len(same):6,})   "
            f"do not {_pct(diff, 50):.3f} (n={len(diff):6,})   "
            f"separation {_pct(same, 50) - _pct(diff, 50):+.3f}")

    out(f"\nWHAT PREDICTS A HIGH PAIR SCORE  ({mode!r} mapping; median score "
        f"when the two places share the fact, against when they do not)")
    split("same archetype", lambda a, b: R.archetype(a) == R.archetype(b))
    split("same module owner", lambda a, b: a.get("module") == b.get("module"))
    split("both built generic",
          lambda a, b: occ[a["key"]]["used"] == "generic"
          and occ[b["key"]]["used"] == "generic")
    split("same sector", lambda a, b: a["sector"] == b["sector"])
    split("shared function",
          lambda a, b: bool(set(a["functions"]) & set(b["functions"])))
    split("shared interactable",
          lambda a, b: bool(set(a["interacts"]) & set(b["interacts"])))
    split("same authority", lambda a, b: a["auth"] == b["auth"])
    split("same ring", lambda a, b: a["ring"] == b["ring"])
    # THE FACT THE BRIEF NAMES: can this tell a Narn quarter from a human one?
    # `populace._mix_for` is the station's own answer to who is in a room -- a
    # human share and a ranked list of dominant non-human species, measured in
    # `npc/schedule.PLACES` and averaged per sector where a place has no row of
    # its own.  If sharing it separates nothing, the geometry has never seen it.
    try:
        import populace as _pop                                 # noqa: PLC0415
        mix = {k: _pop._mix_for(k) for k in keys}
        split("same dominant species",
              lambda a, b: bool(set(mix[a["key"]][1][:2])
                                & set(mix[b["key"]][1][:2])))
        split("human share within 10 pts",
              lambda a, b: abs(mix[a["key"]][0] - mix[b["key"]][0]) < 0.10)
    except Exception as exc:                                    # noqa: BLE001
        out(f"  (species mix unavailable: {str(exc)[:50]})")

    out(f"\nAND THE SAME SPLITS ON FORM ALONE -- what a form grammar has to fix")
    split("same archetype", lambda a, b: R.archetype(a) == R.archetype(b),
          "form")
    split("both built generic",
          lambda a, b: occ[a["key"]]["used"] == "generic"
          and occ[b["key"]]["used"] == "generic", "form")
    split("shared function",
          lambda a, b: bool(set(a["functions"]) & set(b["functions"])), "form")

    out("\nIS IT SIZE?  pair score against the ratio of the two footprint areas")
    for tag, key in (("score", "score"), ("form", "form")):
        band = collections.defaultdict(list)
        for (a, b), (s, c) in pairs.items():
            ea, eb = occ[a]["extent"], occ[b]["extent"]
            aa, ab = ea[0] * ea[1], eb[0] * eb[1]
            r = max(aa, ab) / max(1e-6, min(aa, ab))
            band[min(4, int(math.log(r, 2)))].append(
                s if key == "score" else c["form"])
        row = "  ".join(
            f"x{2 ** k}{'+' if k == 4 else f'-x{2 ** (k + 1)}'}: "
            f"{_pct(band[k], 50):.3f} (n={len(band[k]):,})"
            for k in sorted(band))
        out(f"  {tag:6} {row}")

    out("\nHOW MUCH OF THE CONTENT CHANNEL IS ONLY THE ARCHETYPE PREFIX")
    can = [c["content"] for _s, c in pairs.values()]
    rawp = matrix(vw, keys, "raw_area")
    rawv = [c["content"] for _s, c in rawp.values()]
    allp = matrix(vw, keys, "area_all")
    allv = [c["content"] for _s, c in allp.values()]
    out(f"  canonical object names  median {_pct(can, 50):.3f}   "
        f"above ceiling {sum(1 for x in can if x > PLACE_IOU_MAX):,}")
    out(f"  raw group names         median {_pct(rawv, 50):.3f}   "
        f"above ceiling {sum(1 for x in rawv if x > PLACE_IOU_MAX):,}")
    out(f"  including the shell     median {_pct(allv, 50):.3f}   "
        f"above ceiling {sum(1 for x in allv if x > PLACE_IOU_MAX):,}"
        f"   <- how much of a room is the room and not what is in it")

    out("\nTHE SAME MATRIX UNDER EACH MAPPING (median / pairs over the "
        "ceiling)")
    for m in MODES:
        vm = {k: view(occ[k], m) for k in keys}
        pm = matrix(vm, keys)
        sc = [s for s, _ in pm.values()]
        fm = [c["form"] for _s, c in pm.values()]
        out(f"  {m:8} score {_pct(sc, 50):.3f} / "
            f"{sum(1 for x in sc if x > PLACE_IOU_MAX):5,}    "
            f"form {_pct(fm, 50):.3f} / "
            f"{sum(1 for x in fm if x > PLACE_IOU_MAX):5,}")
    return pairs


def report_pair(a, b, out=print, mode="fit"):
    occ = load_all(keys=(a, b))
    if a not in occ or b not in occ:
        raise SystemExit(f"missing: {sorted({a, b} - set(occ))}")
    oa, ob = view(occ[a], mode), view(occ[b], mode)
    s, ch = score(oa, ob)
    out(f"\n{a}  vs  {b}    ({mode!r} mapping)")
    for k in ("plan", "sect_x", "sect_z", "sect", "form", "content"):
        out(f"  {k:9} {ch[k]:.3f}")
    out(f"  SCORE     {s:.3f}   ({'ABOVE' if s > PLACE_IOU_MAX else 'under'} "
        f"the {PLACE_IOU_MAX} ceiling)")
    for k in (a, b):
        o, ov = occ[k], view(occ[k], mode)
        out(f"  {k:24} {o['used']:8} {o['extent'][0]:7.2f} x "
            f"{o['extent'][1]:7.2f} m, {o['height']:5.2f} m tall, "
            f"{o['tris']:,} tri, {sum(ov['plan']):,} occupied plan cells, "
            f"{R.archetype(DIR.by_key(k))}")
    da = {k: oa['area'].get(k, 0.0) for k in set(oa['area']) | set(ob['area'])}
    db = {k: ob['area'].get(k, 0.0) for k in da}
    diff = sorted(da, key=lambda k: -abs(da[k] - db[k]))[:10]
    out(f"  biggest object differences (m2 of surface, {a} | {b}):")
    for k in diff:
        out(f"    {k:30} {da[k]:9.1f} | {db[k]:9.1f}")
    return s, ch


def plan_art(o, rows=34, cols=68):
    """A max-pooled ASCII plan.  Subsampling lies -- a 0.18 m wall is 5 cells
    and every sixth column misses it, which made the first look at these
    rasters show rooms with one wall."""
    nx, nz = o["nx"], o["nz"]
    sx, sz = nx / cols, nz / rows
    out = []
    for r in range(rows):
        z0, z1 = int(r * sz), max(int(r * sz) + 1, int((r + 1) * sz))
        line = []
        for c in range(cols):
            x0, x1 = int(c * sx), max(int(c * sx) + 1, int((c + 1) * sx))
            hit = any(o["plan"][z * nx + x]
                      for z in range(z0, min(z1, nz))
                      for x in range(x0, min(x1, nx)))
            line.append("#" if hit else ".")
        out.append("".join(line))
    return out


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def _gate(check, out=print, rebuild=False, mode="fit"):
    """V0.  Every control constructs the case it is meant to reject.

    The order mirrors `body.py._detail_gate`: prove the instrument reads 1.000
    on an identity, prove it reads ~1.000 on a re-seeded clone and that the
    ceiling is BELOW that, prove it reads LOW on pairs a human would obviously
    separate, prove a mutation moves it in the direction the mutation implies --
    and only then report the station, so the station's number is a number about
    the station rather than about the instrument.
    """
    schema, profile = IT.load()

    # -- CONTROL 1: identity.  Without this every number below is noise. ----
    ref = DIR.by_key("medlab_one")
    o_ref = place_occupancy(schema, profile, ref, modes=(mode,))
    s_id, _ = score(o_ref, o_ref)
    out(f"\nCONTROL 1  a place against itself                       {s_id:.3f}")
    check(abs(s_id - 1.0) < 1e-12,
          "a place measured against itself reads IoU 1.000")

    # -- CONTROL 2: the seed clone.  THE ONE THE TASK NAMES. ----------------
    # Two places from one archetype with only the seed changed.  Every
    # stochastic choice in `rooms.build` is drawn from `place["key"]`, so this
    # is that and nothing else.  If it does not read ~1.000 the metric is
    # measuring dressing RNG rather than place identity, and every number below
    # is worthless.  It is `body.py`'s four-bodies-from-one-parameter-block.
    c1 = place_occupancy(schema, profile, clone_place(ref, "ctrl_seed_a"),
                         modes=(mode,))
    c2 = place_occupancy(schema, profile, clone_place(ref, "ctrl_seed_b"),
                         modes=(mode,))
    s_seed, ch_seed = score(c1, c2)
    out(f"CONTROL 2  one room, only the seed changed              {s_seed:.3f}"
        f"   plan {ch_seed['plan']:.3f}  sect {ch_seed['sect']:.3f}  "
        f"content {ch_seed['content']:.3f}")
    # THE BAR IS THE DERIVED TABLE, NOT A NUMBER TYPED HERE.  This check read
    # `> 0.95` until it was run against a corrected walking band and failed at
    # 0.924 -- which is not a defect in the generator, it is a threshold that
    # was picked before anything was measured.  `--derive` measures what a
    # re-seed is worth on every archetype, so the honest assertion is that this
    # one is no worse than the worst of those.  Note that two re-seeds of ONE
    # room do not give one number: `derive_ceiling`'s medlab pair reads 0.963
    # and this one reads 0.924, because which two seeds you draw matters by
    # about four points.  That spread is the reason the ceiling is taken from
    # the whole table rather than from one pair.
    check(s_seed >= SEED_CLONE_WORST,
          f"two builds of one place differing ONLY in seed read {s_seed:.3f}, "
          f"no worse than the worst re-seed the ceiling was derived from "
          f"({SEED_CLONE_WORST:.3f})")
    check(s_seed > PLACE_IOU_MAX,
          f"and the seed clone FAILS the {PLACE_IOU_MAX} ceiling "
          f"({s_seed:.3f}) -- the ceiling sits below a re-seed, so the gate "
          f"cannot be passed by shuffling random numbers")

    # -- CONTROL 3: pairs a human would obviously separate. -----------------
    occ = load_all(rebuild=rebuild, verbose=False)
    vw = {k: view(occ[k], mode) for k in occ}
    lo_pairs = (("zocalo", "cargo_bays"), ("zocalo", "medlab_one"),
                ("cnc", "qtr_transient"), ("fabrication", "sanctuary_blue"))
    worst_low = 0.0
    for a, b in lo_pairs:
        if a in vw and b in vw:
            s, ch = score(vw[a], vw[b])
            out(f"CONTROL 3  {a} vs {b:26} {s:.3f}"
                f"   plan {ch['plan']:.3f}  sect {ch['sect']:.3f}  "
                f"content {ch['content']:.3f}")
            worst_low = max(worst_low, s)
    check(worst_low < 0.55,
          f"places a human would obviously call different read LOW (worst of "
          f"{len(lo_pairs)} such pairs {worst_low:.3f}) -- the metric is not a "
          f"constant and the ceiling is reachable from below")

    # -- CONTROL 4: MUTATION. ----------------------------------------------
    _shell_control(check, schema, profile, out, mode)

    # -- THE STATION -------------------------------------------------------
    keys = sorted(vw)
    pairs = matrix(vw, keys)
    scores = [s for s, _ in pairs.values()]
    forms = [c["form"] for _s, c in pairs.values()]
    over = sum(1 for s in scores if s > PLACE_IOU_MAX)
    overf = sum(1 for s in forms if s > PLACE_IOU_MAX)
    cl = clusters(pairs, keys)
    biggest = max((len(c) for c in cl), default=0)
    out(f"\nTHE STATION: {len(keys)} places, {len(scores):,} pairs, "
        f"median score {_pct(scores, 50):.3f}, median form "
        f"{_pct(forms, 50):.3f}")
    out(f"  {over:,} pairs ({100.0 * over / len(scores):.1f}%) score above the "
        f"{PLACE_IOU_MAX} ceiling")
    out(f"  {overf:,} pairs ({100.0 * overf / len(forms):.1f}%) have the same "
        f"FORM -- same plan and same section, told apart only by their props")
    out(f"  {len(cl)} clusters of mutually indistinguishable places, "
        f"largest {biggest}, covering {sum(len(c) for c in cl)} of "
        f"{len(keys)} places")
    for c in cl[:4]:
        out(f"      {len(c)}  {', '.join(sorted(c))}")
    # AND WHERE THE SEED CLONE SITS IN THE STATION'S OWN DISTRIBUTION, which is
    # the strongest statement available about the instrument and needs the
    # station to have been measured first: one room built twice has to be more
    # alike than 99 out of 100 pairs of DIFFERENT rooms, or the measurement is
    # not separating "same room" from "another room".
    p99 = _pct(scores, 99)
    out(f"  the seed clone ({s_seed:.3f}) against the station's p99 "
        f"({p99:.3f})")
    check(s_seed > p99,
          f"one room built twice ({s_seed:.3f}) is more alike than 99% of "
          f"pairs of different rooms (p99 {p99:.3f})")
    check(over == 0,
          f"no two of the {len(keys)} places are indistinguishable "
          f"({over:,} of {len(scores):,} pairs score above {PLACE_IOU_MAX}; "
          f"the largest cluster nothing can tell apart is {biggest} places)")
    return occ, pairs


def _shell_control(check, schema, profile, out, mode="fit"):
    """CONTROL 4: strip the furniture and watch two rooms converge.

    A metric that scored only the shell would be blind to the thing V1 has to
    generate, and one that scored only the furniture would be blind to the
    thing the owner complained about.  So the mutation is built rather than
    argued: take the dressing, props and fixtures out of two rooms and the pair
    has to move, and the DIRECTION is the finding -- toward 1.000, because what
    two rooms out of one kit already have in common is the shell.

    An empty room is a real configuration of this generator and not a synthetic
    one: `rooms.DRESS_DENSITIES` ends at 0.0 and `rooms.build` already takes
    that path when a room cannot afford its furniture.
    """
    a, b = DIR.by_key("medlab_one"), DIR.by_key("fabrication")
    fa = place_occupancy(schema, profile, a, modes=(mode,))
    fb = place_occupancy(schema, profile, b, modes=(mode,))
    s_full, c_full = score(fa, fb)
    ea = occupancy(*_bare(schema, profile, a), a.get("module"), mode=mode)
    eb = occupancy(*_bare(schema, profile, b), b.get("module"), mode=mode)
    s_bare, c_bare = score(ea, eb)
    out(f"CONTROL 4  medlab_one vs fabrication, furnished         {s_full:.3f}"
        f"   -> stripped to bare shell {s_bare:.3f}"
        f"   (form {c_full['form']:.3f} -> {c_bare['form']:.3f})")
    check(c_bare["form"] > c_full["form"] + 0.05,
          f"MUTATION: taking the furniture out of two rooms moves their FORM "
          f"toward each other ({c_full['form']:.3f} -> {c_bare['form']:.3f}) "
          f"-- the metric responds to contents, and what these two already "
          f"share is the shell")


def _bare(schema, profile, place):
    """The same room with `dressing`, the props and the fixtures turned off."""
    v, t, g = R.build(schema, profile, place)
    keep = [(n, lo, hi) for n, lo, hi in _spans_of(g, len(t))
            if not n.startswith(("dress_", "prop_", "fix_", "npc_"))]
    vt, tt, gt, remap = [], [], [], {}
    for n, lo, hi in keep:
        s0 = len(tt)
        for i in range(lo, hi):
            tri = []
            for idx in t[i]:
                if idx not in remap:
                    remap[idx] = len(vt)
                    vt.append(v[idx])
                tri.append(remap[idx])
            tt.append(tuple(tri))
        gt.append((n, s0, len(tt)))
    return vt, tt, gt


def _selftest(rebuild=False, mode="fit"):
    fails = []

    def check(ok, msg):
        print(("  ok   " if ok else "  FAIL ") + msg)
        if not ok:
            fails.append(msg)

    _gate(check, rebuild=rebuild, mode=mode)
    print(f"\n{len(fails)} failing")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--matrix", action="store_true",
                    help="every pair over all 128, summarised, with clusters")
    ap.add_argument("--drivers", action="store_true",
                    help="what the variance that exists is made of")
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"))
    ap.add_argument("--plan", metavar="KEY",
                    help="ASCII plan of one place's walking-band occupancy")
    ap.add_argument("--mode", choices=MODES, default="fit",
                    help="horizontal mapping; see the module docstring")
    ap.add_argument("--rebuild", action="store_true",
                    help="ignore the cache and rebuild every room")
    ap.add_argument("--derive", action="store_true",
                    help="recompute the ceiling from the generator's own "
                         "repeatability and fail if the recorded value drifted")
    ap.add_argument("--verify-cache", type=int, nargs="?", const=6,
                    metavar="N", help="rebuild N sampled rooms and diff them "
                                      "against the cache")
    ap.add_argument("--raw-content", action="store_true",
                    help="score content on raw group names, prefix included")
    a = ap.parse_args(argv)
    ck = "raw_area" if a.raw_content else "area"
    if a.derive:
        derived, worst, _rows = derive_ceiling(mode=a.mode)
        ok = (abs(derived - PLACE_IOU_MAX) < 1e-9
              and abs(worst - SEED_CLONE_WORST) < 0.005)
        print(f"\n  {'ok' if ok else 'DRIFTED'}: recorded {PLACE_IOU_MAX:.2f} / "
              f"{SEED_CLONE_WORST:.3f}, derived {derived:.2f} / {worst:.3f}")
        return 0 if ok else 1
    if a.verify_cache:
        return 1 if verify_cache(a.verify_cache) else 0
    if a.plan:
        o = view(load_all(keys=(a.plan,))[a.plan], a.mode)
        print(f"{a.plan}  {o['extent'][0]:.2f} x {o['extent'][1]:.2f} m, "
              f"{o['height']:.2f} m tall, {sum(o['plan']):,} occupied cells "
              f"({a.mode!r} mapping, walking band "
              f"{WALK_LO_M}-{WALK_HI_M} m)")
        for ln in plan_art(o):
            print("  " + ln)
        return 0
    if a.pair:
        report_pair(*a.pair, mode=a.mode)
        return 0
    if a.drivers:
        report_drivers(mode=a.mode)
        return 0
    if a.matrix:
        report_matrix(content_key=ck, rebuild=a.rebuild, mode=a.mode)
        return 0
    fails = _selftest(rebuild=a.rebuild, mode=a.mode)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
