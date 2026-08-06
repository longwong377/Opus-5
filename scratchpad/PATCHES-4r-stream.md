# Changes needed in files I do not own — session 4r, streaming/axial agent

Owned: `godot/scripts/stream.gd`, `station/boot.py`, `godot/scenes/stream_gate.tscn`.
Everything below is measured, and each item says what the measurement was.

---

## P1 — `tools/bootstrap.py::_cells()` looks in the wrong directory, and its denominator is settleable

**It reports `PARTIAL 1 of 251`. Both numbers are wrong, and the container is actually complete.**

`_cells()` is:

```python
have = len(glob.glob(os.path.join(GEN, "scene", "deck", "cells_*")))
want = len(json.load(open(GEN + "/cell_manifest.json")).get("deck_table", []))
```

**Numerator.** The whole-station bake does not live in `scene/deck/`. `tools/bake_station.py`
writes to `scene/station/cells/`, which `station/boot.py::STATION_CELLS` already names as *"70
decks, 955 cells, one `<stem>_cells.json` each"*. Measured on this container right now:

```
cell sets bootstrap.py can see  (scene/deck/cells_*)                      : 1
cell sets on disk (scene/station/cells/*_cells.json)                      : 70
decks exported to scene/station/ with both halves                         : 70
```

So the artefact gap this session was sent to investigate **does not exist**. 70 of 70 are baked,
219.9 s of bake, 225.4 MB for `blue_0_0` alone; `bootstrap.py` was globbing a directory that holds
one developer-local set.

**Denominator, and it IS settleable from the code — `bootstrap.py`'s docstring says it did not know.**
`cell_manifest.json`'s `deck_table` is every deck SLOT of every ring stack, produced by
`interior.ring_cells` from ring geometry whether or not anything is built there. It is not a target
and never was. The target is the decks the exporter produces, and that number is derived:

```
register places (directory.PLACES)                                        : 129
distinct (sector, ring, deck) carrying at least one place                 :  71
of which not a ring deck -- deck.NOT_RING_DECKS[('green', 1)],
  "the habitat drum ... its walkable surface is drum_ground's heightfield" :   1
==> ring decks that carry content and can be baked                        :  70
```

70 is exactly what `bake_station.decks()` finds on disk and exactly what it baked. The drum is
`station/drum_walk.py`'s, not the cell streamer's.

**Patch:**

```diff
-    have = len(glob.glob(os.path.join(GEN, "scene", "deck", "cells_*")))
-    want = 0
-    p = os.path.join(GEN, "cell_manifest.json")
-    if os.path.exists(p):
-        try:
-            with open(p) as f:
-                want = len(json.load(f).get("deck_table", []))
-        except Exception:                                        # noqa: BLE001
-            want = 0
-    return have, want
+    # WHERE THE BAKE ACTUALLY IS. `tools/bake_station.py` writes one
+    # `<stem>_cells.json` per deck into `scene/station/cells/`; `scene/deck/`
+    # holds whatever a developer baked beside a single deck. Counting the
+    # latter reported `1 of 251` on a container carrying all 70.
+    have = len(glob.glob(os.path.join(GEN, "scene", "station", "cells",
+                                      "*_cells.json")))
+    # AND THE DENOMINATOR IS NOT `deck_table`. That is every deck SLOT of every
+    # ring stack, built or not. The bakeable set is the deck addresses the
+    # register's places occupy, less the habitat drum, which is not a ring deck
+    # -- `deck.NOT_RING_DECKS` -- and whose walkable surface is
+    # `drum_ground`'s heightfield. Measured: 71 addresses, 1 drum, 70 decks,
+    # which is what `bake_station.decks()` finds and what it baked.
+    want = len([g for g in glob.glob(os.path.join(GEN, "scene", "station",
+                                                  "*.glb"))
+                if not g.endswith("_collision.glb")
+                and not os.path.basename(g).startswith("column_")
+                and os.path.exists(g[:-4] + "_collision.glb")])
+    return have, want
```

With that the docstring's "I do not know the denominator" paragraph can be replaced by the
derivation above, and the fraction can go in the exit code.

---

## P2 — every cell set on disk is one-dimensional and must be re-baked

`tools/bake_station.py` needs **no code change** — `stream.gd::bake()` now defaults `z_band` to the
deck's own `cell_length_m` and it will pick that up. But its 70 existing outputs were cut before
INV-610 and every one of them is a set of arc wedges running its deck's whole axial extent.
Measured on `scene/station/cells/blue_0_0_cells.json`:

| | on disk now (1-D) | re-baked (2-D) |
|---|---|---|
| cells | 18 | **87** (18 arc × 16 band) |
| longest cell, z | **1,108.6 m** | **73.8 m** |
| biggest cell | **582,792 tri = 3.24× the whole 180,000 resident budget** | 227,247 = 1.26× |
| distinct spawn z over all cells | **1** (all at z 7562.75, in the void between clusters) | 27 |

Re-run: `python3 tools/bake_station.py`. Expect roughly the same wall time (blue_0_0 went 17.2 s →
15.4 s) and the same total size (225.4 → 215.5 MB). **Do not run it while other agents are
working** — it is minutes of full CPU.

---

## P3 — the shipped build boots a 143 m single-cluster deck while the whole 1,108 m deck exists beside it

`station/boot.py` boots `sorted(decks())[0]` out of `scene/deck/`, which on this tree is
`blue_0_0` — the z≈7120 cluster build, spanning z 7044.8–7188.1 (143 m). The whole-deck build of
the same name is in `scene/station/` and spans z 6896.9–8005.4 (1,108 m), carries all six of the
deck's z-clusters and all 36 of its interactables against the deck build's own subset.

They cannot be merged by `boot.py` alone, because the two directories disagree about naming and
about which artefacts exist:

| | `scene/deck/` | `scene/station/` |
|---|---|---|
| collision mesh | `<stem>_col.glb` **and `_col.obj`** | `<stem>_collision.glb`, no `.obj` |
| render `.obj` | present | absent |
| sidecars | `_interact/_actors/_crowd/_dialogue/_arrival` | `_interact/_actors/_crowd` |

`boot.py::decks()` needs a `*_col.obj` because `spawn_from_shell` measures the spawn off the text
`.obj` — deliberately, so it needs no engine. So `scene/station/` is unbootable today for want of
two things: the `_col` / `_collision` suffix, and an `.obj` beside the `.glb`.

**Whoever owns `station/deck.py`'s exporter:** emitting `<stem>_col.obj` alongside
`<stem>_collision.glb` in `scene/station/`, or simply using the `_col` suffix in both places, makes
the whole-deck build bootable and is what would put the other five z-clusters of blue/0/0 in front
of a player. I did not do it because both the naming and which build is canonical are decisions
that belong to the exporter, not to the boot manifest — and guessing would put the spawn a deck
build measured onto cells another build cut, which is exactly the failure `_describes` exists to
prevent.

---

## P4 — `walk.gd::--stream-test` steers along the arc only

`_run_stream_test` steers toward `Vector3(_s_r*cos(a), _s_r*sin(a), _s_z)` with `_s_z` fixed at the
manifest's `corridor.z_mid`, so it can only ever exercise arc hand-off. That is why the axial gate
had to be built as its own scene (`res://scenes/stream_gate.tscn`, script `stream.gd`,
`--axial-gate`) rather than as a flag on the existing one.

The change that would fold it back in is small — the spine is in the manifest the streamer already
loaded:

```diff
+	# --axis walks the manifest's own measured spine instead of the ring. See
+	# `stream.gd::_axial_runs`: on a whole-deck bake this is the only floor that
+	# joins one z-cluster to the next.
+	_s_axis = args.has("axis")
 	var a := atan2(p.y, p.x) + _s_dir * (_s_lookahead / maxf(_s_r, 1.0))
-	steer = Vector3(_s_r * cos(a), _s_r * sin(a), _s_z) - p
+	if _s_axis:
+		var sp: Dictionary = _stream.plan.get("corridor", {}).get("spine", {})
+		var sa := deg_to_rad(float(sp.get("deg", 0.0)))
+		steer = Vector3(_s_r * cos(sa), _s_r * sin(sa),
+			p.z + _s_dir * _s_lookahead) - p
+	else:
+		steer = Vector3(_s_r * cos(a), _s_r * sin(a), _s_z) - p
```

Two things it must keep that the standalone gate learned the hard way:

1. **The steer must have no angular component.** The spine is 2.16 m wide; anything that walks the
   body round the ring walks it off. `--axis` must hold the spine's angle exactly, not lookahead
   round it.
2. **The spine's angle is the MASS-weighted centre, not the bin centre.** Bin 89 of `blue_0_0`
   holds 575 floor triangles of which 550 are the spine in two strips at 89.07° and 89.26°; the
   other 25 are singletons of room floor out to 89.93°. Taking the extent's midpoint gives 89.49°,
   which is 0.03° past the spine's own far edge — the gate walked half off the floor and stalled
   after 0.7 m. `plan.corridor.spine.deg` is already the right number; use it and do not re-derive.

---

## P5 — a note for whoever owns `station/budget.py`

`CELLS["resident_tris"]` is annotated *"the cell you are in plus both neighbours"* — three cells,
which is the right count on a ONE-dimensional grid. On a two-dimensional one a body standing at a
cell corner has four cells at distance zero, and the measured peak on the real deck is **five**
(four plus one in flight ahead). The axial run peaked at **169,582 of 180,000 with 0 over-budget
frames**, so the number still holds on this deck — but the *reason* written beside it no longer
describes the geometry, and `stream.gd::configure` derives `max_inflight` from
`resident_tris / cell_tris - 1` on the same assumption. Worth restating; I have not changed it,
because a budget number changed by the agent that wants it to pass is not evidence.
