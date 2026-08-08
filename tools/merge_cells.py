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
"""

import argparse
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLS = os.path.join(ROOT, "station", "generated", "scene", "station", "cells")
OUT = os.path.join(CELLS, "station_cells.json")


def per_deck(cells_dir=CELLS):
    """-> [(stem, manifest)] for every per-deck cell set on disk."""
    out = []
    for p in sorted(glob.glob(os.path.join(cells_dir, "*_cells.json"))):
        stem = os.path.basename(p)[:-len("_cells.json")]
        if stem == "station":                     # our own output
            continue
        with open(p) as f:
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
    ab = c["aabb"]
    lo = ab["pos"]
    hi = [lo[i] + ab["size"][i] for i in range(3)]
    q = [min(max(p[i], lo[i]), hi[i]) for i in range(3)]
    return math.dist(p, q)


def worst_resident(cells, radius):
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
    """
    pts = [(c["spawn"], c) for c in cells if c.get("spawn")]
    tris = [int(c.get("tris", 0) or 0) for c in cells]
    worst, at, n_at = 0, "", 0
    for p, home in pts:
        s = n = 0
        for c, t in zip(cells, tris):
            if distance_to(c, p) <= radius:
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


def merge(cells_dir=CELLS, out_path=OUT, renumber=True):
    sets = per_deck(cells_dir)
    if not sets:
        raise SystemExit("merge_cells: no *_cells.json in %s" % cells_dir)

    cells, ids, by_deck = [], set(), {}
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
            # AND SO MUST INDICES, FOR THE SAME REASON ONE LEVEL DOWN. The id is
            # what the streamer keys residency on; the INDEX is what `cell_at`
            # returns and `cell_by_index`/`prime` look back up, so a repeated
            # index primes a cell the body is not standing in. Renumbering is the
            # whole fix: position in the merged array, which is unique because
            # the array is what the engine scans.
            if renumber:
                c["deck"] = stem
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
    free = max(_f(m, "free_radius_m", radius * 2.0) for _s, m in sets)
    cell_len = max(_f(m, "cell_length_m") for _s, m in sets)
    widest = max(sets, key=lambda sm: _f(sm[1], "radius_m"))[0]
    base = sets[0][1].get("residency", {})

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
            "radius_from": ("the widest of %d decks (%s) -- see "
                            "tools/merge_cells.py on why max and not min"
                            % (len(sets), widest)),
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
    with open(out_path, "w") as f:
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


def budget_report(man, out=print):
    """THE WORST CASE THIS MANIFEST CAN PRODUCE, measured rather than proxied.

    Printed on every merge, because `main()` calls `report()` and `report()`
    calls this: the shipped path is the only place a budget number is worth
    having. `--budget` runs it alone and exits nonzero, so it can also be a
    gate; it is NOT part of `--selftest`, which asserts loadability and must
    stay able to pass on a build whose budget is honestly red.
    """
    r = man["residency"]
    cells = man["cells"]
    cell_tris = int(r.get("cell_tris", 60000))
    res_tris = int(r.get("resident_tris", 180000))
    radius = float(r.get("radius_m", 0.0))
    worst, at, n_at = worst_resident(cells, radius)
    over = over_budget(cells, cell_tris)
    out("  budget %s tri resident, %s per cell" % (res_tris, cell_tris))
    out("  WORST CO-RESIDENT SET: %s tri in %d cells, standing at %s "
        "-- %.2fx the %s allowance%s"
        % ("{:,}".format(worst), n_at, at or "?", worst / max(res_tris, 1),
           "{:,}".format(res_tris), "" if worst <= res_tris else "   OVER"))
    out("  %d of %d cells exceed %s tri on their own%s"
        % (len(over), len(cells), "{:,}".format(cell_tris),
           ":" if over else " -- none"))
    for t, cid, deck in over[:12]:
        out("      %11s  %-28s %.2fx  %s"
            % ("{:,}".format(t), cid, t / cell_tris, deck))
    if len(over) > 12:
        out("      ... %d more" % (len(over) - 12))
    return {"worst_resident": worst, "worst_at": at, "resident_cells": n_at,
            "over_cell": len(over), "cell_tris": cell_tris,
            "resident_tris": res_tris}


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
    with open(p) as f:
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
    print("merged manifest: %d cells, radius %.1f m, %d distinct index value(s)"
          % (len(rows), float(res.get("radius_m", 0.0)),
             len({int(c.get("index", -1)) for c in rows})))
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
    a = ap.parse_args()
    if a.budget:
        p = a.out
        if not os.path.exists(p):
            print("  NO MERGED MANIFEST at %s -- run: python3 "
                  "tools/merge_cells.py" % p)
            return 1
        with open(p) as f:
            man = json.load(f)
        b = budget_report(man)
        bad = (b["worst_resident"] > b["resident_tris"]) or b["over_cell"]
        print("\n  CELL BUDGET %s" % ("RED" if bad else "GREEN"))
        return 1 if bad else 0
    if a.selftest:
        return selftest(a.cells, a.out if a.out != OUT else None)
    man = merge(a.cells, a.out, renumber=not a.legacy_index)
    report(man)
    print("\n  wrote %s" % os.path.relpath(a.out, ROOT))
    return selftest(a.cells, a.out)


if __name__ == "__main__":
    sys.exit(main())
