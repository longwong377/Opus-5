#!/usr/bin/env python3
"""Merge 70 per-deck cell sets into ONE manifest, so the whole station streams.

WHY. `boot.json` names a single deck's cell set and `main.gd` hands that one
path to `stream.gd::configure`, so the shipped game loads ONE deck of seventy.
All 70 are in the package -- 2,815 MB of mesh, 816 cells, 129 rooms, 6,021
people -- and 113 of the register's 129 places are unreachable data. That is
"built but unreachable" at station scale.

AND IT NEEDS NO NEW ENGINE CODE, WHICH IS THE WHOLE POINT OF DOING IT THIS WAY.
Three facts make the merge sufficient:

  1. EVERY DECK IS ALREADY IN ONE WORLD FRAME. A cell's `aabb.pos` and `arc`
     are absolute station coordinates, not deck-local: blue_0_0 sits at
     r=211.55 m, red_0_0 at r=268.05, grey_0_0 at r=471.25, each with its own
     z. Nothing has to be transformed; they simply coexist.
  2. `configure()` READS A FLAT LIST. It takes `j["cells"]`, resolves each
     cell's `mesh`/`collision` RELATIVE TO THE MANIFEST'S OWN DIRECTORY, and
     every one of the 70 sets already writes its `.scn` files into that same
     `cells/` directory. So concatenation is the entire transform.
  3. THE STREAMER NEVER ASKS WHICH DECK A CELL BELONGS TO. It loads by distance
     from the player and frees by distance. `plan["corridor"]`, `floor_r_m` and
     `z_cluster_m` are read only by `_ax_setup`/`_ax_pick_target`, which are the
     AXIAL GATE, not the runtime.

THE ONE REAL DECISION IS RESIDENCY, AND IT IS STATED RATHER THAN DEFAULTED.
`configure()` sets ONE global load radius, and the 70 sets carry 70 DIFFERENT
residency blocks because each deck derives its cell length from its own
circumference -- 73.8 m on blue_0_0, 72.6, 71.3 and so on. A merged manifest
must choose.

It takes the MAXIMUM radius and free distance across the decks. The reason is
asymmetric cost: a radius smaller than some deck's cell length means a player
walking that deck can stand where the next cell has not been asked for yet --
no floor, a fall through the world. A radius larger than needed on a
fine-grained deck costs resident triangles, which `stream.gd`'s stated policy
already handles by printing rather than popping a cell. **Missing ground is a
bug; extra triangles are a budget number.**

That budget is already RED and this makes it redder -- `boot.py --axial-gate`
measured peak resident 359,584 tri against a 180,000 budget on blue_0_0 alone.
It is recorded here rather than hidden: see `--report`, which prints the worst
case the merged manifest can produce.

===========================================================================
AND `index` IS AN IDENTITY, SO CONCATENATING SEVENTY-SIX OF THEM BROKE IT
===========================================================================

THE DOCSTRING ABOVE ASSERTED IDS AND FORGOT INDICES, and the loop below says so
in its own comment: *"IDS MUST STAY UNIQUE ACROSS THE MERGE ... a collision
would make `stream.gd` free the wrong cell, which is a hole in the floor rather
than a wrong number."* That is exactly right about `id`, and it is word for word
the argument for `index`, which nothing ever checked. Measured on the shipped
manifest before this change: **823 cells carrying 190 distinct `index` values**,
index 7 alone shared by 33 cells, 712 of the 823 sitting on a number somebody
else also claims.

The cause is structural rather than careless. `stream.gd::bake()` computes
`cix = arc * n_band + band` PER DECK and is right to -- its own comment says
*"`index` is only an engine-local handle (`prime`, `cell_by_index`) and has to be
unique and small, so it is compacted"*. Seventy-six decks each numbering from
zero, concatenated without renumbering, is seventy-six overlapping handle spaces
in one array, and "unique" was a property of the input this merge quietly spent.

AND IT IS AN IDENTITY, WHICH IS WHY IT IS NOT COSMETIC. `stream.gd::cell_at(p)`
RETURNS `c["index"]`, and `walk.gd::_load_streamed` feeds that straight back
through `cell_by_index()` and `prime()`. Both are FIRST-MATCH scans over the same
array, so with duplicates the round trip is not the identity: `cell_at` finds the
cell the body is standing in, hands back an integer, and `cell_by_index` returns
the FIRST cell carrying that integer -- a different cell, usually on a different
deck. `prime()` then loads THAT one, synchronously, as the level's load screen,
and the body is left standing over geometry nobody asked for.

MEASURED by putting a body at each cell's own recorded spawn point and running
that exact chain -- `tools/cell_identity.py`, on the shipped manifest:

    the primed cell is the cell the body is in       170 of 787
    the primed cell is somewhere else                617 of 787
      median distance to the primed cell's geometry     2,724.8 m
      further than 50 m from anything that loaded              574

Of those 617, **248 are this defect alone** -- `cell_at` found the right cell and
`cell_by_index` handed back a different one. The other 369 are a SECOND defect
that renumbering does not touch and this file cannot reach; it is named and
measured at the bottom of `tools/cell_identity.py`. Renumbering here takes the
round trip from **170 to 418 of 787**, and the residual is stated rather than
rounded away.

AND THE SAME MEASUREMENT OVER CONTENT, WHICH IS THE ONE THAT MATTERS. Put a body
at each of the register's **129 named places**, at the `floor_xyz` the bake
recorded for it, and ask whether the cell the streamer primes has any geometry
under that body:

                                        as shipped   renumbered
    floor under the body                 23 of 129    91 of 129
    when not, distance to the primed     2,065.1 m      42.7 m   (median)
    ... worst                            7,231.5 m     166.5 m

THE GARDEN IS THE CLEANEST SINGLE CASE and it is the one the 4t panel traced.
`the_garden` sits in `green_1_0_c00`, whose per-deck index is **0**;
`blue_0_0_c00z00` is also index 0 and comes first in the merged array, so
`prime()` loaded a corridor cell **1,756.7 m away** and the body stood over
nothing. `zen_garden` and `drum_tram` share that same index 0 and the same wrong
cell; `garden_terrace` got `blue_0_2_c08z11`, 2,733.5 m away.

AND THE REASON IT SURVIVED IS WORTH MORE THAN THE FIX: **the one deck the boot
manifest names is the one deck the defect cannot touch.** `per_deck()` globs
`sorted()`, so `blue_0_0` is first, so `cell_by_index` always resolves to a
`blue_0_0` cell when `blue_0_0` claims that index -- and `boot.json`'s spawn is
on `blue_0_0`. Every launch-and-look check anyone ran started on the only deck
that works. A defect that is invisible from the spawn point is invisible from
every test that starts at the spawn point.

THE FIX IS TO NUMBER THE MERGED ARRAY, NOT TO KEEP SEVENTY-SIX NUMBERINGS.
A merged cell's `index` is its position in the merged list: unique by
construction, still "small" in the sense `bake()` wanted, and derived from the
array the engine actually scans rather than from the deck it used to live on. The
deck-local handle is kept as `index_in_deck` beside `deck`, so nothing is lost
and a merged row can still be lined up against the per-deck manifest it came
from.

WHAT WAS CHECKED BEFORE RENUMBERING, because an index anything persists or
cross-references would break silently and this project has paid for that twice:

  * `stream.gd` -- `cell_by_index`, `cell_at`, `prime`, the free guard in
    `update()` and `_entering`. Every one consumes the index WITHIN the one
    manifest it loaded. Nothing stores one anywhere.
  * `walk.gd` -- `_start_cell`, `_cell_index`, `_nearest_cell`, and the axial
    gate's `_g_idx`. All within one loaded manifest. `_g_idx` gets strictly
    BETTER: it enumerates cells by index, so on the shipped manifest it could
    only ever visit 190 of 823 cells and always the first of each collision.
  * `station/boot.py::start_cell` -> `boot.json`'s `cells_start`, which `main.gd`
    prints. Recomputed by `boot.build()` from the manifest it names, every time,
    so there is nothing stale to leave behind. (`station/generated/` is
    gitignored; no manifest is committed.)
  * `tools/reach_gate.py` -- matches cell **ids**, never indices.
  * THE PER-DECK MANIFESTS ARE NOT TOUCHED. This tool reads them and writes one
    new file. `docs/streaming-4g.md`'s `--start-cell=4` commands run against
    `cells_<deck>/cells.json`, whose numbering is unchanged and stays correct.
  * `station/boot.py::_fixture` writes its own per-deck test manifests with
    `"index": k` -- per deck, so unaffected.

`--legacy-index` is the control: it concatenates without renumbering, exactly as
before, and `--selftest` then FAILS on the file it just wrote.

===========================================================================
AND THE WORST-CASE NUMBER THIS FILE PRINTED WAS NOT THE WORST CASE
===========================================================================

`report()` used to say *"heaviest 3 cells: A, B, C = N tri against a 180,000
budget"*, with the comment *"the cheap proxy for it is the heaviest few"*. That
proxy is not a bound in either direction and it is worth being exact about why,
because it read like a measurement for four sessions.

The heaviest three cells on this station are on three different decks thousands
of metres apart and **can never be resident together**, so the number was an
overestimate of a thing that cannot happen. At the same time eleven ordinary
cells inside one residency radius comfortably beat all three, so it was an
underestimate of the thing that does. `worst_resident()` asks the question
`stream.gd::update` actually asks -- every cell within `radius_m` of where the
body is standing -- by porting `distance_to` and evaluating it at every cell's
own recorded spawn.

**MEASURED ON THE SHIPPED MANIFEST, THE ANSWER IS 24.87x AND ITS BIGGEST SINGLE
CAUSE IS NOT ON THE DECK THE BODY IS STANDING ON.** Standing at
`grey_0_22_c08z01`, r=449.4, z=3694.8:

    58 cells resident, from 20 decks, 4,477,402 tri
      green_1_0    1 cell   1,585,762 tri   floor r=278.3   95.7 m away
      grey_0_8     3 cells    293,402 tri   floor r=464.1
      grey_0_0     5 cells    210,830 tri   floor r=471.2
      ... 17 more grey decks at r 406-471

The Garden is 35% of it, and it is resident **from a Grey corridor 171 m away
radially and outside the drum entirely**, because `distance_to`'s arc branch has
**no radial term at all** -- `da` is 0 for any angle inside `[a0, a1)`, the drum
cell's arc is `[0, 360)`, so the only distance left is the z overhang and the
drum's aft end is 95.7 m up the axis. That is exactly the hazard
`tools/bake_columns.py` names for a lift shaft (*"would call a body on Blue 4 at
r=44 zero metres from a shaft that stops at r=130"*), arriving at station scale
because this file merged 76 decks into one metric space.

TWO THINGS FOLLOW AND THE SECOND IS THE SURPRISE.

  * `tools/bake_drum.py` cuts the drum into 85 cells and the worst co-resident
    set falls to **2,895,463 (16.09x)** -- the whole 1,585,762 comes out.
  * A RADIAL TERM WOULD NOW BUY ALMOST NOTHING. Re-measured with
    `sqrt(along^2 + dz^2 + dr^2)`, `dr` being the body's radius against the
    cell's floor radius less a 5 m deck slab: **before** the drum cut it takes
    4,477,402 to 2,891,640, and every one of those 1,585,762 triangles is the
    Garden; **after** the cut it takes 2,895,463 to 2,891,640, which is 0.13%.
    The residual is nineteen Grey decks genuinely stacked 3.5 m apart in radius
    at r 406-471, all inside one 98.9 m residency sphere and all at the same
    angle and z. That is a deck-spacing and residency-radius question, not a
    metric bug, and it is the next thing to look at -- named here with its
    number so the next session does not spend the session I nearly spent
    building a radial term worth 0.13%.

`--budget` is the gate. It is deliberately NOT part of `--selftest`: that
asserts the manifest is LOADABLE and has to stay able to pass on a build whose
budget is honestly red, which this one is.

===========================================================================
AND THE PARAGRAPH ABOVE WAS WRONG ABOUT WHY: A RADIAL *DISTANCE* BUYS 0.10%,
A RADIAL *BAND* BUYS 80% (session 4u)
===========================================================================

THE PREDICTION IN THIS FILE WAS RIGHT AND ITS CONCLUSION WAS WRONG. Two
sections up it says a radial term "would now buy almost nothing ... 0.13%", and
re-measured today that is exactly true: `sqrt(along^2 + dz^2 + dr^2)` takes the
worst co-resident set from 3,737,289 to 3,733,466 tri, which is **0.10%**. The
reason is arithmetic and it is the whole finding: **the decks of this station
are 3.600 m apart in radius** -- measured, every ring, 57 of 59 consecutive
gaps -- and a residency radius of 98.9 m does not notice 3.6 m. Nineteen Grey
decks stacked over 61 m of radius all sit inside one residency sphere however
the metric is written, as long as the metric is a DISTANCE.

**A DECK FLOOR IS OPAQUE, AND THAT IS A PREDICATE RATHER THAN A DISTANCE.** The
residency radius is `sight_line_m`, which `station/interior.py` derives as the
chord past which the ring's OWN CURVATURE occludes -- a statement about what a
body standing IN A CORRIDOR can see along it. A cell on the deck above is not
0.3 m away through a floor slab; it is not visible at all, at any arc distance,
because there is a floor in between. So the right question is not "how far is
that cell" but "is that cell on the deck I am standing on", and the answer is
a band test on radius:

    worst co-resident set, measured at every cell's own recorded spawn

      shipped (radius-blind, one global radius)   3,737,289 tri   20.76x   59 cells
      + radial distance term (the 4t proposal)    3,733,466       20.74x   57
      + per-deck residency radius alone           3,733,466       20.74x   57
      + DECK BAND alone                             827,521        4.60x   21
      + DECK BAND and per-deck radius               751,123        4.17x   10

      over the 868 standing positions            shipped        band
        median resident                            667,452     232,316
        mean cells resident                           20.7         6.9
        positions over the 180,000 budget            92.4%       66.5%
        positions over 1,041 mesh groups             32.6%        0.1%
        median mesh groups resident                    729         240

THE BAND IS DERIVED, NOT PICKED, AND IT IS WIDENED BY THE CELL'S OWN EVIDENCE.
A cell's `arc.r_m` is its deck's FLOOR radius, so the deck occupies inward from
there to the next deck's floor: `headroom` is that gap, taken per (sector,
ring) from the manifest's own floor radii and defaulted to their median for a
ring with one deck. Then the band is widened by the cell's own recorded spawn,
because `bake()` derives a spawn from that cell's own collision floor ("a spawn
is a CLAIM") -- which is how a mezzanine says so: eleven ring cells have a
spawn 5.2 to 14.9 m inboard of their deck floor, and their band opens to hold
it.

CHECKED AGAINST EVERY BODY THIS STATION PLACES, because a band that excludes a
place a player can stand is a fall through the world and no triangle count
would show it. Over the 1,458 crowd placements on ring decks in
`station/generated/scene/station/*_crowd.json`, **0 sit outside their own
cell's band**; over the 862 cells with a spawn, **0 fail to contain their own
spawn** (`--selftest` asserts exactly that, and it is not vacuous: it fails on
a band built without the spawn widening). The 36 placements that DO sit
outboard of their deck floor -- by up to 2.36 m -- are all in `green_1_0`,
which is exempt:

**A FULL-CIRCLE CELL IS NOT A CORRIDOR AND TAKES THE AABB BRANCH.** The drum's
85 cells carry `arc = [0, 360)`, so `da` is 0 for every angle on the station
and the arc branch reduces to "the z overhang" -- which is precisely how a Grey
corridor 171 m away radially held the whole Garden resident. The arc branch
exists because "an arc cell's world AABB is a 145 m box whose nearest corner is
nothing a player can walk to"; for a disc the box IS the volume, so the reason
does not apply and the AABB branch is both correct and radius-aware. It also
means the drum keeps no band at all, which matters because the drum's ground
has RELIEF -- a 7 m settlement podium -- and a body climbing it would leave any
3.6 m band and free the ground under its own feet.

RESIDENCY IS PER CELL NOW, AND THE GLOBAL MAX IS DEMOTED TO A BOUND. Each cell
carries `res_radius_m` and `res_free_m` from its own deck's manifest, so
`blue_0_0` is back on the 66.1 m sight line and 73.8 m free radius that
`stream.gd`'s own header derives for it instead of Grey's 98.9/164.5, and
`green_1_0` gets the 33.0 m band `tools/bake_drum.py` derived for it and
recorded as overridden ("the MERGED manifest's radius ... governs in the
packaged build whatever this row says"). With the band in place these two
readings can no longer disagree: a wanted cell is on the player's own deck, so
"the cell's deck" and "the player's deck" are the same deck and there is
nothing left to compromise. The top-level `residency` block keeps the max --
`configure()` refuses a manifest whose radius is not positive, and the max is
the true upper bound on the want set -- and its prose now says so.

    one deck's row is not positive (`column_green`, radius 0.0). That cell
    falls back to the global bound and the fallback is COUNTED AND PRINTED,
    because a silent 0.0 would make a cell that can never be resident.

`--legacy-radial` is the control: it merges with no bands and no per-cell
radii, and the numbers above come back. `--budget --legacy-radial` measures an
existing manifest as if it had neither, which is the same control without
rewriting the artefact.
"""

import argparse
import collections
import glob
import json
import math
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLS = os.path.join(ROOT, "station", "generated", "scene", "station", "cells")
OUT = os.path.join(CELLS, "station_cells.json")

## An arc this wide is a disc, not a corridor: `da` is 0 at every angle on the
## station, so the arc branch measures nothing but the z overhang. Mirrored in
## `stream.gd::residency_distance`.
FULL_CIRCLE_DEG = 359.9
## Slop on the radial band, for the same reason `stream.gd::AABB_SLOP_M` exists
## and with the same value: a body standing on the floor is AT the band's
## outboard edge and float noise can put it a millimetre outside. It is slop for
## FLOAT NOISE and not a knob -- the band's real width comes from the deck gap
## and the cell's own spawn.
BAND_SLOP_M = 0.25
## A deck a body stands in cannot be thinner than this. Not a tuning value: a
## derived headroom below it means the floor radii this is derived from are not
## one-per-deck any more, and a band thinner than a body is a fall through the
## world. `deck_headroom` refuses rather than emitting one.
MIN_HEADROOM_M = 2.0
## Returned instead of a distance for a cell whose deck the player is not on.
## Finite rather than `inf` so anything ranking cells by it still ranks them,
## and large enough that no residency or free radius can admit it.
OFF_DECK_M = 1e9


def per_deck(cells_dir=CELLS):
    """-> [(stem, manifest)] for every per-deck cell set on disk."""
    out = []
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_cells.json"))):
        stem = os.path.basename(p)[:-len("_cells.json")]
        if stem == "station":                     # our own output
            continue
        with open(p, encoding="utf-8") as f:
            out.append((stem, json.load(f)))
    return out


def duplicate_indices(cells):
    """-> {index: [id, ...]} for every `index` more than one cell claims.

    THE ASSERTION THE MERGE WAS MISSING, in the form a caller can print. It is a
    property of the merged ARRAY -- no geometry, no predicate, no tolerance --
    because `cell_at` and `cell_by_index` are both first-match scans over that
    array and a repeated key makes their composition something other than the
    identity. See the module docstring.
    """
    seen = {}
    for c in cells:
        seen.setdefault(int(c.get("index", -1)), []).append(str(c.get("id", "")))
    return {i: ids for i, ids in seen.items() if len(ids) > 1}


def deck_headroom(cells):
    """-> ({deck: metres inward from its floor it occupies}, n measured).

    MEASURED FROM THE MANIFEST'S OWN FLOOR RADII, never written down. A cell's
    `arc.r_m` is the radius of the deck's floor; the deck's own volume runs
    INWARD from there (on a spun ring "up" is toward the axis) to whatever is
    above it, which is the floor of the next deck in the same sector and ring.
    So the headroom of a deck is the gap to its inboard neighbour -- 3.600 m on
    every ring of this station, 57 of the 59 gaps that exist, the other two
    being 7.2 and 14.4 where a deck index is missing and the volume genuinely
    belongs to the deck below it.

    A ring with one deck (the drum, `red_0`, `yellow_3`) has no neighbour to
    measure against and takes the median of every gap that could be measured.

    IT REFUSES RATHER THAN RETURNING A THIN BAND. A headroom under
    `MIN_HEADROOM_M` would mean two "decks" 30 cm apart, which is not a deck
    ladder but a broken set of floor radii -- and the failure it would cause is
    silent and catastrophic, a body standing on a floor whose own cell is not
    resident. `station/spec_registry.py`'s rule: refuse to emit around an
    ambiguity rather than emit the convenient reading of it.
    """
    floor = {}
    for c in cells:
        arc = c.get("arc")
        if not arc:
            continue
        floor.setdefault(str(c.get("deck", "")), set()).add(round(float(arc["r_m"]), 3))
    split = {}
    for deck, rs in floor.items():
        if len(rs) > 1:
            raise SystemExit("merge_cells: deck %r has %d different floor radii "
                             "(%s) -- the radial band is derived per deck and "
                             "cannot be" % (deck, len(rs), sorted(rs)))
        m = re.match(r"([a-z]+)_(\d+)_(\d+)$", deck)
        split.setdefault((m.group(1), m.group(2)) if m else (deck, ""),
                         []).append((next(iter(rs)), deck))
    out, measured = {}, []
    for _ring, rows in split.items():
        rows.sort(key=lambda t: -t[0])
        for i, (r, deck) in enumerate(rows):
            if i + 1 < len(rows):
                out[deck] = r - rows[i + 1][0]
                measured.append(out[deck])
    if not measured:
        raise SystemExit("merge_cells: no ring has two decks -- the deck "
                         "headroom cannot be measured from this manifest")
    med = statistics.median(measured)
    thin = sorted((g, d) for d, g in out.items() if g < MIN_HEADROOM_M)
    if thin or med < MIN_HEADROOM_M:
        raise SystemExit("merge_cells: derived deck headroom below %.1f m (%s, "
                         "median %.3f) -- floor radii are not one per deck and "
                         "a band this thin is a fall through the world"
                         % (MIN_HEADROOM_M, thin[:3], med))
    n_measured = len(out)
    for deck in floor:
        out.setdefault(deck, med)
    return out, n_measured


def is_full_circle(c):
    """A cell whose arc spans the whole ring: a disc, not a corridor."""
    arc = c.get("arc")
    return bool(arc) and (float(arc["a1_deg"]) - float(arc["a0_deg"])
                          >= FULL_CIRCLE_DEG)


def radial_band(c, headroom):
    """-> (r_lo, r_hi) the radii at which a body is ON this cell's deck.

    The deck slab first -- floor at `arc.r_m`, headroom inward -- and then
    WIDENED BY THE CELL'S OWN SPAWN, which is the only evidence in the manifest
    about where this particular cell's floors actually are. `bake()` derives a
    spawn by ray casting that cell's own collision ("a spawn is a CLAIM -- see
    walk.gd"), so a cell holding a gallery 6 m above its deck floor says so,
    and its band opens to hold a body standing there plus the same headroom
    above it. ELEVEN ring cells on this station need it -- measured, by
    rebuilding without it and running `--selftest`, which then reports eleven
    cells that do not contain their own spawn. Without it they would free the
    floor under a player who climbed to them.

    -> None for a cell with no arc (the six transit columns, whose AABB already
    spans radius) and for a full-circle cell (the drum).
    """
    if not c.get("arc") or is_full_circle(c):
        return None
    r_m = float(c["arc"]["r_m"])
    h = float(headroom.get(str(c.get("deck", "")), 0.0))
    lo, hi = r_m - h, r_m
    sp = c.get("spawn") or []
    if len(sp) >= 2:
        rs = math.hypot(float(sp[0]), float(sp[1]))
        lo, hi = min(lo, rs - h), max(hi, rs)
    return lo, hi


def residency_distance(c, p, legacy=False):
    """`stream.gd::residency_distance`, in Python. What `update()` asks.

    THE SECOND MIRROR OF A RUNTIME FUNCTION, taken for the reason the first one
    below states: the only other way to ask what the streamer would hold
    resident is to launch the engine. It is `distance_to` plus the two rules
    that make residency a question about ONE DECK -- the full-circle exemption
    and the radial band -- and it is deliberately a separate function rather
    than a flag on `distance_to`, because `distance_to` is the BINNING rule
    (`bake()::_split` bins a triangle by angle and z and never by radius) and
    everything that asks "which cell is this point in" has to keep asking it
    that way.

    NEITHER RULE IS DERIVED HERE OR IN THE ENGINE -- both are read off the cell,
    as `merge()` wrote them: `res_aabb` for a cell that is a disc rather than a
    corridor, `arc.band` for the radii at which a body is on that cell's deck.
    A threshold re-derived on each side of the mirror is a threshold that can
    drift on one side only.

    `legacy` is the control: measure this manifest as if it carried neither.
    """
    if bool(c.get("res_aabb")) and not legacy:
        return _aabb_distance(c, p)
    band = None if legacy else (c.get("arc") or {}).get("band")
    if band:
        r = math.hypot(p[0], p[1])
        if r < float(band[0]) - BAND_SLOP_M or r > float(band[1]) + BAND_SLOP_M:
            return OFF_DECK_M
    return distance_to(c, p)


def _aabb_distance(c, p):
    ab = c["aabb"]
    lo = ab["pos"]
    hi = [lo[i] + ab["size"][i] for i in range(3)]
    q = [min(max(p[i], lo[i]), hi[i]) for i in range(3)]
    return math.dist(p, q)


def distance_to(c, p):
    """`stream.gd::distance_to`, in Python. Zero inside.

    A SECOND COPY OF A RUNTIME FUNCTION IS A LIABILITY AND IT IS TAKEN
    DELIBERATELY, because the alternative is worse: the only other way to ask
    what the streamer would hold resident is to launch the engine, and a budget
    number nobody can compute without a GPU-less Godot run is a budget number
    nobody computes. It is kept to twelve lines that mirror the GDScript
    branch for branch -- `arc` when the cell has one, the world AABB otherwise,
    which is the rule `stream.gd` states in its own comment ("Both forms are in
    the manifest and this picks whichever the cell has") and which
    `station/boot.py::start_cell` already duplicates for the same reason.
    """
    if "arc" in c:
        arc = c["arc"]
        a = math.degrees(math.atan2(p[1], p[0])) % 360.0
        a0, a1 = float(arc["a0_deg"]), float(arc["a1_deg"])
        da = 0.0
        if not (a0 <= a < a1):
            d0 = math.fmod(abs(a - a0) + 360.0, 360.0)
            d0 = min(d0, 360.0 - d0)
            d1 = math.fmod(abs(a - a1) + 360.0, 360.0)
            d1 = min(d1, 360.0 - d1)
            da = min(d0, d1)
        along = math.radians(da) * float(arc["r_m"])
        dz = max(0.0, float(arc["z0"]) - p[2], p[2] - float(arc["z1"]))
        return math.hypot(along, dz)
    return _aabb_distance(c, p)


def cell_radii(cells, fallback, legacy=False):
    """-> [(want_radius, free_radius)] per cell, in the array's own order.

    Per cell, from what the merge wrote into it. `fallback` is the top-level
    maximum, which is what a cell gets when its own deck's row is not positive
    -- and `merge()` counts those and prints the count, because a cell with a
    residency radius of 0.0 can never be resident and would go missing in
    silence.
    """
    if legacy:
        return [(fallback[0], fallback[1]) for _c in cells]
    out = []
    for c in cells:
        r = float(c.get("res_radius_m", 0.0) or 0.0)
        f = float(c.get("res_free_m", 0.0) or 0.0)
        out.append((r if r > 0.0 else fallback[0], f if f > 0.0 else fallback[1]))
    return out


def worst_resident(cells, radius, legacy=False, free=False, free_radius=None):
    """The heaviest set of cells that can be resident AT ONCE. -> (tris, id, n).

    THE PROXY THIS REPLACES WAS THE HEAVIEST THREE CELLS, AND IT IS NOT AN
    UPPER OR A LOWER BOUND -- it is unrelated. The heaviest three cells on this
    station are on three different decks, thousands of metres apart, and can
    never be resident together; meanwhile eleven ordinary cells inside one
    residency radius can beat all three. The number the budget is about is what
    `stream.gd::update` will actually hold, which is every cell within
    `radius_m` of where the body is standing.

    THE SAMPLE IS THE CELLS' OWN SPAWN POINTS, so it is a measurement and not a
    grid: `bake()` derives each spawn from that cell's own collision floor
    ("A spawn is a CLAIM -- see walk.gd"), so the set of spawns is the set of
    places the build itself says a body can stand. It is therefore a LOWER
    BOUND on the true worst case -- a player standing between two spawns could
    be worse -- and that is said here rather than left to be assumed, because a
    bound quoted in the wrong direction is how a red number reads as green.

    AND IT ASKS EACH CELL ITS OWN RADIUS, because since session 4u each carries
    one. `radius` is the top-level maximum and is now only the fallback for a
    cell whose own deck row is not positive. `free=True` measures the FREE ball
    instead -- the set the streamer will still be HOLDING after the player has
    walked past, which is the honest ceiling and is bigger than the want set.
    """
    pts = [(c["spawn"], c) for c in cells if c.get("spawn")]
    tris = [int(c.get("tris", 0) or 0) for c in cells]
    fb = (radius, float(free_radius if free_radius else radius * 2.0))
    rads = [(rr[1] if free else rr[0])
            for rr in cell_radii(cells, fb, legacy)]
    worst, at, n_at = 0, "", 0
    for p, home in pts:
        s = n = 0
        for c, t, rr in zip(cells, tris, rads):
            if residency_distance(c, p, legacy) <= rr:
                s += t
                n += 1
        if s > worst:
            worst, at, n_at = s, str(home.get("id", "")), n
    return worst, at, n_at


def over_budget(cells, cell_tris):
    """Every cell that on its own exceeds the per-cell allowance."""
    out = [(int(c.get("tris", 0) or 0), str(c.get("id", "")),
            str(c.get("deck", "")))
           for c in cells if int(c.get("tris", 0) or 0) > cell_tris]
    return sorted(out, reverse=True)


def merge(cells_dir=CELLS, out_path=OUT, renumber=True, radial=True):
    sets = per_deck(cells_dir)
    if not sets:
        raise SystemExit("merge_cells: no *_cells.json in %s" % cells_dir)

    cells, ids, by_deck = [], set(), {}
    sets_by_stem = {s: m.get("residency", {}) for s, m in sets}
    for stem, man in sets:
        rows = man.get("cells", [])
        by_deck[stem] = len(rows)
        for c in rows:
            cid = c.get("id", "")
            # IDS MUST STAY UNIQUE ACROSS THE MERGE. They already are -- every
            # id is prefixed with its deck stem (`blue_0_0_c04z08`) -- but a
            # collision would make `stream.gd` free the wrong cell, which is a
            # hole in the floor rather than a wrong number. Asserted, not
            # assumed.
            if cid in ids:
                raise SystemExit("merge_cells: duplicate cell id %r" % cid)
            ids.add(cid)
            # WHICH DECK IT CAME FROM, unconditionally: the radial band and the
            # per-cell residency radius are both properties of the deck, so this
            # is no longer only provenance for a reader. `--legacy-index` still
            # leaves `index` alone, which is what that control is about.
            c["deck"] = stem
            # AND SO MUST INDICES, FOR THE SAME REASON ONE LEVEL DOWN. The id is
            # what the streamer keys residency on; the INDEX is what `cell_at`
            # returns and `cell_by_index`/`prime` look back up, so a repeated
            # index primes a cell the body is not standing in. Renumbering is the
            # whole fix: position in the merged array, which is unique because
            # the array is what the engine scans.
            if renumber:
                c["index_in_deck"] = int(c.get("index", -1))
                c["index"] = len(cells)
            cells.append(c)

    dup = duplicate_indices(cells)
    if dup and renumber:
        # Cannot happen -- the index is the array position. Asserted anyway,
        # because a guard that can only fire on a future edit is the only kind
        # worth keeping once the present edit is correct.
        raise SystemExit("merge_cells: renumbering did not make indices unique "
                         "(%d collisions) -- this is a bug in merge()" % len(dup))
    if dup:
        worst = max(dup.items(), key=lambda kv: len(kv[1]))
        print("merge_cells: --legacy-index -- %d of %d cells carry an index "
              "another cell also claims (%d distinct values for %d cells; "
              "index %d alone is shared by %d). `cell_by_index(cell_at(p))` is "
              "NOT the identity on this manifest: see the module docstring and "
              "`python3 tools/cell_identity.py`."
              % (sum(len(v) for v in dup.values()), len(cells),
                 len({int(c.get("index", -1)) for c in cells}), len(cells),
                 worst[0], len(worst[1])))

    # Residency: the widest radius wins. See the module docstring.
    def _f(man, key, default=0.0):
        return float(man.get("residency", {}).get(key, default))

    radius = max(_f(m, "radius_m") for _s, m in sets)
    free_max = max(_f(m, "free_radius_m", _f(m, "radius_m") * 2.0)
                   for _s, m in sets)

    # ------------------------------------------------------------------
    # THE RADIAL BAND AND THE PER-CELL RESIDENCY (session 4u). See the
    # module docstring: this is what takes the worst co-resident set from
    # 20.76x the budget to 4.17x, and a radial DISTANCE term is worth 0.10%.
    # ------------------------------------------------------------------
    band_n = full_n = fallback_n = 0
    headroom, measured_n = deck_headroom(cells) if radial else ({}, 0)
    for c in cells:
        c.pop("res_radius_m", None)
        c.pop("res_free_m", None)
        c.pop("res_aabb", None)
        if c.get("arc"):
            c["arc"].pop("band", None)
        if not radial:
            continue
        b = radial_band(c, headroom)
        if b:
            c["arc"]["band"] = [round(b[0], 4), round(b[1], 4)]
            band_n += 1
        elif is_full_circle(c):
            # A DISC, NOT A CORRIDOR: the arc branch would measure only the z
            # overhang for it. Written into the cell rather than re-derived on
            # each side of the mirror.
            c["res_aabb"] = True
            full_n += 1
        row = dict(sets_by_stem.get(str(c.get("deck", "")), {}))
        r = float(row.get("radius_m", 0.0) or 0.0)
        f = float(row.get("free_radius_m", 0.0) or 0.0)
        if r <= 0.0 or f <= 0.0:
            fallback_n += 1
            r, f = radius, free_max
        c["res_radius_m"] = r
        c["res_free_m"] = f
    if radial:
        print("merge_cells: radial band on %d of %d cells (deck headroom "
              "%.3f m median, MEASURED on %d of %d decks and defaulted to that "
              "median on the rest), %d full-circle cell(s) exempt and on the "
              "AABB rule, %d cell(s) fell back to the global radius because "
              "their own deck row is not positive"
              % (band_n, len(cells), statistics.median(sorted(headroom.values())),
                 measured_n, len(headroom), full_n, fallback_n))
    else:
        print("merge_cells: --legacy-radial -- NO radial band and NO per-cell "
              "residency. Every deck at the same angle and z is co-resident, "
              "which is the state measured at 20.76x the resident budget; see "
              "the module docstring.")
    free = free_max
    cell_len = max(_f(m, "cell_length_m") for _s, m in sets)
    widest = max(sets, key=lambda sm: _f(sm[1], "radius_m"))[0]
    longest = max(sets, key=lambda sm: _f(sm[1], "cell_length_m"))[0]
    # THE PROSE IS REGENERATED, NOT INHERITED. `base` is deck 0's residency
    # block and it carries deck 0's SENTENCES beside the merge's numbers: the
    # shipped manifest said "cell_length_m (73.8 m) ... hysteresis 7.7 m" next
    # to a free radius of 164.5 and a cell length of 164.5, because `free_from`
    # came from `blue_0_0` and the figures came from `max()`. A string copied
    # out of one input and printed beside a number computed from all of them is
    # a lie with a citation on it. Everything derived is written here.
    base = {k: v for k, v in sets[0][1].get("residency", {}).items()
            if k not in ("radius_from", "free_from", "shipped_radius_m",
                         "shipped_radius_note")}

    # THE CORRIDOR BLOCK, WHICH IS NOT DECORATION. `walk.gd::_configure` reads
    # `plan["corridor"]` for the steering lookahead -- `sqrt(r * w)`, the chord
    # length that sags exactly w/8 off the arc. A merged manifest without it
    # gives r=0, w defaults to 2.5, and the lookahead collapses from 23.4 m to
    # the 1.0 m floor: a body then steers on noise instead of on the arc ahead
    # of it, and `chord sag` prints `inf`. Measured on the first merged run
    # before this block existed.
    #
    # IT CAN ONLY CARRY ONE, AND WHICH ONE IS A REAL COMPROMISE. Every deck has
    # its own corridor radius -- 211.55 m on blue, 268.05 on red, 471.25 on
    # grey -- and `plan` is global. This takes the corridor of the deck with
    # the most cells, which is the deck a player spawns on, so the spawn deck
    # is exactly right and the others are approximately right: lookahead scales
    # as sqrt(r), so the worst case across this station is off by a factor of
    # 1.5, against a factor of 23 for having no block at all.
    #
    # `corridor_by_deck` carries all 70 so a future `walk.gd` can pick by the
    # player's own radius, which is the correct fix and needs an engine change
    # rather than a manifest one. Nothing reads it yet; it is recorded so the
    # next session does not have to re-derive it.
    biggest = max(sets, key=lambda sm: len(sm[1].get("cells", [])))
    by_deck_corr = {s: m.get("corridor", {}) for s, m in sets if m.get("corridor")}

    # THE SOURCE BLOCK, WITHOUT WHICH THE PLAYER IS AT EARTH GRAVITY.
    #
    # A REGRESSION THIS FILE CAUSED, caught by launching the packaged build:
    #
    #   walk: gravity -- NO SPIN STATED -- this build names no deck, so the
    #         body keeps mode=drum at 9.8100 m/s2 (the pre-4r field)
    #
    # against the 7.454 m/s2 (0.7602 g at r=211.55) the ring actually delivers.
    # `walk.gd::_derive_omega2` has two ways to learn which deck it is on, and
    # a STREAMED build can only use the first: `_stream.plan["source"]`. The
    # second parses `<sector>_<ring>_<deck>` out of the collision filename, and
    # a streamed build has no monolith path to parse. Every per-deck manifest
    # carries `source`; the first cut of this merge did not, so the branch fell
    # through to "names no deck" and the body fell at 9.81 down the wrong axis.
    #
    # ONE SOURCE FOR SEVENTY DECKS IS A REAL COMPROMISE, the same one the
    # corridor block above makes and for the same reason: `plan` is global and
    # gravity is per deck -- 0.7602 g at blue's r=211.55, different at grey's
    # r=471.25. This takes the spawn deck's, so the deck a player starts on and
    # spends most of its time on is exactly right and the others are wrong by
    # the ratio of their radii.
    #
    # THE HONEST FIX IS AN ENGINE CHANGE, NOT A MANIFEST ONE, and it already
    # has a precedent here: INV-451 made `ragdoll.gd` work its own gravity out
    # from the body's world position rather than being told, precisely because
    # a stated default that only one caller sets is an unset default.
    # `_derive_omega2` runs once at setup and would need to re-derive as the
    # player crosses rings. `source_by_deck` carries all 70 so that change needs
    # no re-derivation; nothing reads it yet.
    man = {
        "cells": cells,
        "source": biggest[1].get("source", {}),
        "source_by_deck": {s: m.get("source", {})
                           for s, m in sets if m.get("source")},
        "corridor": biggest[1].get("corridor", {}),
        "corridor_from": biggest[0],
        "corridor_by_deck": by_deck_corr,
        "floor_r_m": biggest[1].get("floor_r_m", 0.0),
        "residency": {
            **base,
            "radius_m": radius,
            "free_radius_m": free,
            "cell_length_m": cell_len,
            "radius_from":
                (("AN UPPER BOUND, not the radius any cell uses: the widest of "
                  "%d decks (%s, %.1f m). Since session 4u every cell carries "
                  "its own deck's sight line as res_radius_m -- 66.1 m on "
                  "blue_0_0, 33.0 m on the drum -- and update() reads that. "
                  "This value is kept because configure() refuses a manifest "
                  "whose radius is not positive and because it bounds the want "
                  "set." % (len(sets), widest, radius))
                 if radial else
                 ("the widest of %d decks (%s) -- --legacy-radial, so this ONE "
                  "value governs every deck, which is the state measured at "
                  "20.76x the resident budget" % (len(sets), widest))),
            "free_from":
                (("AN UPPER BOUND: the widest of %d decks (%s, %.1f m = its own "
                  "cell length). Each cell carries its own deck's free radius "
                  "as res_free_m -- 73.8 m on blue_0_0, 7.7 m of hysteresis "
                  "against its 66.1 m sight line, which is 0.96 s at the "
                  "shipped 8.0 m/s sprint." % (len(sets), longest, free))
                 if radial else
                 ("the widest of %d decks (%s) -- --legacy-radial"
                  % (len(sets), longest))),
            "cell_length_from":
                ("the longest cell on any deck (%s). Per deck it is in that "
                 "deck's own manifest; nothing in the engine reads this one."
                 % longest),
            "band_from":
                ("arc.band = the radii at which a body is ON that cell's deck: "
                 "floor at arc.r_m, inward by the gap to the next deck in the "
                 "same ring, widened by the cell's own recorded spawn. %d of "
                 "%d cells carry one; %d full-circle cells are exempt and use "
                 "the AABB rule. residency_distance() returns %g m for a cell "
                 "outside it, because a deck floor is opaque."
                 % (band_n, len(cells), full_n, OFF_DECK_M)
                 if radial else
                 "NONE -- --legacy-radial. Residency is radius-blind: every "
                 "deck at the same angle and z is co-resident."),
        },
        # Provenance, so a reader of this file can tell it is derived and from
        # what. Nothing in the engine reads these.
        "merged_from": {"decks": len(sets), "cells": len(cells),
                        "by_deck": by_deck},
        # WHOSE NUMBERING THE `index` FIELD IS, said out loud in the artefact
        # rather than only in this source. A reader holding a manifest can tell
        # whether its indices are an identity without re-deriving it.
        "index_from": ("position in the merged array -- unique by construction; "
                       "the deck-local handle is kept as index_in_deck"
                       if renumber else
                       "THE PER-DECK HANDLE, CONCATENATED AND NOT UNIQUE "
                       "(--legacy-index) -- cell_by_index(cell_at(p)) is not "
                       "the identity on this manifest"),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(man, f)
    return man


def report(man):
    r = man["residency"]
    m = man["merged_from"]
    print("merged %d deck cell sets -> %d cells" % (m["decks"], m["cells"]))
    print("  radius %.1f m, free at %.1f m, longest cell %.1f m"
          % (r["radius_m"], r["free_radius_m"], r["cell_length_m"]))
    print("  index: %d distinct value(s) over %d cells -- %s"
          % (len({int(c.get("index", -1)) for c in man["cells"]}),
             len(man["cells"]), man.get("index_from", "?")))
    budget_report(man)
    print("  decks, largest first:")
    for stem, k in sorted(m["by_deck"].items(), key=lambda kv: -kv[1])[:6]:
        print("    %-16s %3d cells" % (stem, k))


def budget_report(man, out=print, legacy=False):
    """THE WORST CASE THIS MANIFEST CAN PRODUCE, measured rather than proxied.

    Printed on every merge, because `main()` calls `report()` and `report()`
    calls this: the shipped path is the only place a budget number is worth
    having. `--budget` runs it alone and exits nonzero, so it can also be a
    gate; it is NOT part of `--selftest`, which asserts loadability and must
    stay able to pass on a build whose budget is honestly red.

    IT SAYS WHICH RULE IT MEASURED WITH, on every run, because since session 4u
    there are two and a manifest merged by an older copy of this tool carries
    neither band nor per-cell radius -- it would report the old number and look
    like a regression in the content. `legacy=True` measures a banded manifest
    as if it had none, which is the control.
    """
    r = man["residency"]
    cells = man["cells"]
    cell_tris = int(r.get("cell_tris", 60000))
    res_tris = int(r.get("resident_tris", 180000))
    radius = float(r.get("radius_m", 0.0))
    free_r = float(r.get("free_radius_m", radius * 2.0))
    banded = sum(1 for c in cells if (c.get("arc") or {}).get("band"))
    percell = sum(1 for c in cells if float(c.get("res_radius_m", 0.0) or 0.0) > 0.0)
    if legacy:
        out("  RULE: --legacy-radial -- radius-blind, one global radius %.1f m "
            "(this manifest carries %d band(s) and %d per-cell radius(es); "
            "they are being IGNORED, which is the control)"
            % (radius, banded, percell))
    elif banded == 0 and percell == 0:
        out("  RULE: radius-blind, one global radius %.1f m. THIS MANIFEST "
            "CARRIES NO RADIAL BAND -- it was merged before session 4u or with "
            "--legacy-radial. Re-run `python3 tools/merge_cells.py`." % radius)
    else:
        out("  RULE: deck band on %d of %d cells, per-cell residency on %d "
            "(global %.1f m is the bound only)"
            % (banded, len(cells), percell, radius))
    worst, at, n_at = worst_resident(cells, radius, legacy, free_radius=free_r)
    hold, hat, hn = worst_resident(cells, radius, legacy, free=True,
                                   free_radius=free_r)
    over = over_budget(cells, cell_tris)
    out("  budget %s tri resident, %s per cell" % (res_tris, cell_tris))
    out("  WORST CO-RESIDENT SET: %s tri in %d cells, standing at %s "
        "-- %.2fx the %s allowance%s"
        % ("{:,}".format(worst), n_at, at or "?", worst / max(res_tris, 1),
           "{:,}".format(res_tris), "" if worst <= res_tris else "   OVER"))
    # THE WANT SET IS NOT THE HELD SET, and only the want set was ever printed.
    # `update()` frees a cell at `free_radius_m`, not at `radius_m`, so what the
    # streamer is HOLDING after a player has walked past is the free ball. It is
    # the honest ceiling and it is bigger; it is printed beside the gate number
    # rather than instead of it, because the gate is about what must be loaded.
    out("  ... still HELD at the free radius: %s tri in %d cells at %s (%.2fx)"
        % ("{:,}".format(hold), hn, hat or "?", hold / max(res_tris, 1)))
    out("  %d of %d cells exceed %s tri on their own%s"
        % (len(over), len(cells), "{:,}".format(cell_tris),
           ":" if over else " -- none"))
    for t, cid, deck in over[:12]:
        out("      %11s  %-28s %.2fx  %s"
            % ("{:,}".format(t), cid, t / cell_tris, deck))
    if len(over) > 12:
        out("      ... %d more" % (len(over) - 12))
    # A DECK THAT IS ONE CELL AND OVER BUDGET WAS NEVER CUT AT ALL, and that is
    # a different bug from a cell that is merely heavy: no residency radius can
    # help, because the streamer's unit of work is the whole thing. It is
    # detected by SHAPE -- one cell, over the per-cell allowance -- rather than
    # by name, so a second deck that arrives in that state is caught too. It
    # is printed here because `report()` is on the shipped path and a tool
    # nothing calls is this project's signature defect.
    uncut = uncut_decks(cells, cell_tris)
    for stem, t in uncut:
        out("  %s IS ONE CELL of %s tri (%.2fx cell_tris) -- it was never cut. "
            "No residency radius can make that affordable; the streamer loads "
            "and frees whole cells.%s"
            % (stem, "{:,}".format(t), t / cell_tris,
               "  Run: python3 tools/bake_drum.py --bake"
               if stem == "green_1_0" else ""))
    return {"worst_resident": worst, "worst_at": at, "resident_cells": n_at,
            "over_cell": len(over), "cell_tris": cell_tris,
            "resident_tris": res_tris, "uncut": [s for s, _t in uncut]}


def uncut_decks(cells, cell_tris):
    """Decks contributing exactly one cell, and that cell over the allowance."""
    by = {}
    for c in cells:
        stem = c.get("deck") or str(c.get("id", "")).rsplit("_c", 1)[0]
        by.setdefault(stem, []).append(int(c.get("tris", 0) or 0))
    return sorted(((s, t[0]) for s, t in by.items()
                   if len(t) == 1 and t[0] > cell_tris),
                  key=lambda st: -st[1])


def selftest(cells_dir=CELLS, manifest=None):
    """Assert the merged manifest is loadable by `stream.gd::configure`.

    `manifest` defaults to `<cells_dir>/station_cells.json`, and `main()` passes
    the path it JUST WROTE. It used to read the default no matter where `--out`
    pointed, so a run with a non-default `--out` reported on a stale file it had
    not produced -- the "gate reads an artefact it cannot rebuild" defect in
    miniature.

    IT CHECKS THE THINGS configure() ACTUALLY REFUSES ON, in its own order:
    a dictionary, a `cells` key, a positive residency radius and a positive
    resident triangle budget. `configure` returns false on each of those and
    the game then loads NOTHING -- which is a worse failure than the one this
    tool exists to fix, so it is asserted here rather than discovered on a
    launch.
    """
    p = manifest or os.path.join(cells_dir, "station_cells.json")
    if not os.path.exists(p):
        print("  NO MERGED MANIFEST -- run: python3 tools/merge_cells.py")
        return 1
    with open(p, encoding="utf-8") as f:
        j = json.load(f)
    bad = []
    if not isinstance(j, dict):
        bad.append("not a dictionary")
    if "cells" not in j:
        bad.append("no `cells` key -- configure() calls this 'not a cell manifest'")
    res = j.get("residency", {})
    if float(res.get("radius_m", 0.0)) <= 0.0:
        bad.append("residency radius is not positive")
    if int(res.get("resident_tris", 0)) <= 0:
        bad.append("resident triangle budget is not positive")
    # Every referenced .scn must exist, or the streamer loads a cell into
    # nothing and the player walks into a hole.
    missing = 0
    for c in j.get("cells", []):
        for k in ("mesh", "collision"):
            v = c.get(k, "")
            if v and not os.path.exists(os.path.join(cells_dir, v)):
                missing += 1
    if missing:
        bad.append("%d referenced .scn file(s) are absent" % missing)
    # `index` MUST BE AN IDENTITY. `stream.gd::cell_at` returns it and
    # `cell_by_index`/`prime` look it back up, both by first match over this same
    # array, so a repeated value primes a cell the body is not standing in. This
    # is the cheap half of `tools/cell_identity.py` -- no geometry needed.
    rows = j.get("cells", [])
    dup = duplicate_indices(rows)
    if dup:
        worst = max(dup.items(), key=lambda kv: len(kv[1]))
        bad.append("%d of %d cells share an `index` with another cell "
                   "(%d distinct values; index %d is claimed by %d cells, "
                   "including %s). `cell_by_index(cell_at(p))` therefore primes "
                   "the wrong cell -- run `python3 tools/merge_cells.py` to "
                   "renumber, and `python3 tools/cell_identity.py` for the "
                   "consequence."
                   % (sum(len(v) for v in dup.values()), len(rows),
                      len({int(c.get("index", -1)) for c in rows}),
                      worst[0], len(worst[1]), ", ".join(worst[1][:3])))
    # A CELL MUST CONTAIN ITS OWN SPAWN UNDER THE RULE RESIDENCY USES, and this
    # is the assertion the radial band has to survive. A band that excludes a
    # place the build itself says a body can stand is a floor freed under the
    # player's feet, and no triangle count anywhere would show it -- the
    # co-resident number would only look BETTER. It is not vacuous: rebuilt with
    # the spawn widening removed from `radial_band`, it fails on 9 cells
    # (blue_0_0_c17z03, grey_0_20_c09z00 and seven more whose floor is a gallery
    # 5.2 to 14.9 m above their deck's).
    homeless = [str(c.get("id", "")) for c in rows
                if c.get("spawn") and residency_distance(c, c["spawn"]) > 0.0]
    if homeless:
        bad.append("%d cell(s) do not contain their OWN recorded spawn under "
                   "residency_distance -- the radial band excludes a place the "
                   "bake says a body stands (%s). A player there would have the "
                   "floor freed under them."
                   % (len(homeless), ", ".join(homeless[:4])))
    banded = sum(1 for c in rows if (c.get("arc") or {}).get("band"))
    percell = sum(1 for c in rows if float(c.get("res_radius_m", 0.0) or 0.0) > 0.0)
    print("merged manifest: %d cells, radius %.1f m (bound), %d distinct index "
          "value(s), %d radial band(s), %d per-cell residency radius(es)%s"
          % (len(rows), float(res.get("radius_m", 0.0)),
             len({int(c.get("index", -1)) for c in rows}), banded, percell,
             "" if banded else "  -- RADIUS-BLIND (pre-4u or --legacy-radial)"))
    if bad:
        for b in bad:
            print("  BAD: %s" % b)
        return 1
    print("\n  MERGED CELL MANIFEST OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", default=CELLS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--budget", action="store_true",
                    help="THE GATE: measure the worst set of cells that can be "
                         "resident at once and exit nonzero if it is over "
                         "budget.CELLS. Merges nothing; reads the manifest on "
                         "disk.")
    ap.add_argument("--legacy-index", action="store_true",
                    help="THE CONTROL: concatenate the per-deck numbering "
                         "without renumbering, as this tool did before session "
                         "4t. --selftest then FAILS on the manifest it wrote.")
    ap.add_argument("--legacy-radial", action="store_true",
                    help="THE OTHER CONTROL: no radial band and no per-cell "
                         "residency, as this tool did before session 4u. With "
                         "--budget it measures an existing manifest as if it "
                         "had neither, without rewriting it; on a merge it "
                         "writes a manifest the engine then streams "
                         "radius-blind.")
    a = ap.parse_args()
    if a.budget:
        p = a.out
        if not os.path.exists(p):
            print("  NO MERGED MANIFEST at %s -- run: python3 "
                  "tools/merge_cells.py" % p)
            return 1
        with open(p, encoding="utf-8") as f:
            man = json.load(f)
        b = budget_report(man, legacy=a.legacy_radial)
        bad = (b["worst_resident"] > b["resident_tris"]) or b["over_cell"]
        print("\n  CELL BUDGET %s" % ("RED" if bad else "GREEN"))
        return 1 if bad else 0
    if a.selftest:
        return selftest(a.cells, a.out if a.out != OUT else None)
    man = merge(a.cells, a.out, renumber=not a.legacy_index,
                radial=not a.legacy_radial)
    report(man)
    print("\n  wrote %s" % os.path.relpath(a.out, ROOT))
    return selftest(a.cells, a.out)


if __name__ == "__main__":
    sys.exit(main())
