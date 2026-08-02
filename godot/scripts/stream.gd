extends Node3D
## CELL RESIDENCY -- the thing that makes the station bigger than one file.
##
## WHAT THIS EXISTS TO END. `walk.gd` takes ONE `--glb` and loads it whole, so
## the largest continuously walkable piece of Babylon 5 is one 40 m z-cluster of
## one deck: 773,172 triangles, 65 MB, loaded synchronously, and when you reach
## its edge there is nothing on the other side. `station/routes.py --report` puts
## the station in 85 foot-connected pieces; even once corridors join them, a
## player still cannot walk from one to the next because NOTHING IN THE ENGINE
## LOADS A SECOND FILE. `station/budget.py` says so itself, in the `when=` of its
## own resident-triangle check: *"walk.gd loads one .glb whole -- there is no
## streaming and no LOD"*.
##
## THE TWO RESIDENCY NUMBERS ARE READ, NOT PICKED, and they come from opposite
## ends of the problem:
##
##   RADIUS -- how far you must keep loaded -- is `sight_line_m` out of
##   `station/generated/cell_manifest.json`, which `station/interior.py` computes
##   as `sight_line(r_floor, corridor_width) = 2*sqrt(r_o^2 - r_i^2)`: the chord
##   tangent to the inner wall, past which the ring's OWN CURVATURE occludes.
##   For Blue ring_1 deck 0 that is **66.1 m** at r = 211.55. Inside it the
##   player can see the geometry, so inside it the geometry must exist. Outside
##   it the corridor wall is in the way and nothing can pop.
##
##   CEILING -- how much you may keep loaded -- is `CELLS["resident_tris"]` out
##   of `station/budget.py`: **180,000**, which that file annotates *"the cell
##   you are in plus both neighbours"*, i.e. 180,000 / `CELLS["cell_tris"]`
##   60,000 = **3 cells**.
##
## THEY AGREE, AND THAT IS THE CHECK. A canonical cell on this deck is 20.0 deg
## = 73.8 m of run, and 73.8 > 66.1, so "everything within a sight line" is
## exactly "the cell you are in plus both neighbours" -- the two derivations,
## from curvature and from triangles, land on the same three cells. Neither
## number is written down here; both are read at run time and the manifest
## records which file each came from.
##
## WHEN THEY DISAGREE, CORRECTNESS WINS AND IT SAYS SO. If the sight line demands
## more triangles than the budget allows, this file keeps the cells and prints
## `OVER BUDGET`, because dropping a cell the player can see is a pop and going
## over budget is a frame cost. Measured on the real deck it IS over: an
## assembled 20 deg cell is ~75,000 triangles against the 60,000 `cell_tris`
## gate, so three of them are 1.25x the resident budget. That is a true statement
## about the content, printed rather than hidden by dropping a cell.
##
## THE HYSTERESIS IS BOUNDED, NOT CHOSEN. A cell is loaded when it comes within
## the sight line and freed only past a larger `free_radius_m`, so a player
## standing on the threshold cannot make a cell load and unload on alternate
## frames. That deadband has a HARD CEILING: a cell two away is never nearer than
## one cell length, so any free radius above `cell_length_m` holds a fourth cell
## the want set never asked for and the budget still pays for. Free radius is
## therefore `max(sight_line, cell_length)` -- the largest deadband that cannot
## admit a fourth cell -- which here is 73.8 m and leaves 7.7 m of slack, 0.96 s
## at `player.gd`'s 8.0 m/s sprint against a measured 11 ms activation.
##
## The first version of this file used `sight_line + cell_length` with the
## plausible-sounding justification "one cell is the granularity of the thing
## being freed". The gate caught it in one line: `resident_max=4` on a run whose
## want set never exceeded 3. A rationalisation that sounds like a derivation is
## not one.
##
## ASYNCHRONOUS, AND VERIFIED ASYNCHRONOUS. `ResourceLoader.load_threaded_request`
## does the read and the mesh construction on a worker thread;
## `load_threaded_get_status` is polled once a frame and `load_threaded_get`
## takes the result. Only the instancing, the trimesh collider, the material bind
## and the fittings happen on the main thread, and AT MOST ONE CELL IS ACTIVATED
## PER FRAME so the hand-off cannot stack.
##
##   AND IT CANNOT BE DONE WITH A .glb. `ResourceLoader` has no runtime glTF
##   format loader -- a `.glb` outside `res://` is not a Resource to it, and one
##   inside `res://` needs the editor import step. `walk.gd`'s `_load_glb` uses
##   `GLTFDocument.append_from_file`, which is SYNCHRONOUS and is the hitch.
##   So a cell is baked to a `.scn` (`bake()` below), which `ResourceLoader`
##   loads from an absolute path off `res://` -- verified, not assumed.
##
## WHAT A BAKED CELL KEEPS, because `walk.gd` must not be able to tell the
## difference: every mesh keeps its SOURCE GROUP NAME, so `dress_scene.gd` binds
## the same material rule to `deck_panel` in a streamed cell as it does in a
## monolithic glb; and the collision cell gets `create_trimesh_collision()` on
## every mesh exactly as `_load_level` does, for the reason stated there --
## trimesh and not convex, because a room is a hole in solid.

# ---------------------------------------------------------------------------
# Where the derived numbers live. Neither is restated here.
# ---------------------------------------------------------------------------
## `station/interior.ring_cells` per deck: cell_deg, cell_length_m, sight_line_m,
## floor_r_m, cell_triangles. Written by `station/interior.py --cells`.
const CELL_MANIFEST_PY := "../station/generated/cell_manifest.json"
## `station/budget.CELLS`: cell_tris, resident_tris. Parsed out of the source for
## the same reason `dress_scene.gd` parses `export_scene.py` -- a copy is correct
## on the day it is written and silently wrong afterwards.
const BUDGET_PY := "../station/budget.py"

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
var plan: Dictionary = {}              ## the manifest, as loaded
var cells: Array = []                  ## Array[Dictionary], one per cell
var problems: PackedStringArray = PackedStringArray()

var radius_m := 0.0                    ## sight line: inside this, must be resident
var free_m := 0.0                      ## radius + one cell: outside this, may go
var resident_tris_budget := 0
var cell_tris_budget := 0
var max_inflight := 1

var disabled := false                  ## `--no-stream`: the negative control
## Hold a finished load for this many frames before activating it.
##
## A STRESS CONTROL, NOT A TUNING KNOB. "Survive the player turning round
## mid-load" is untestable on this box at its natural speed -- a 28,000 triangle
## cell finishes inside one physics frame, so the in-flight window is never open
## when the body reverses and the abandon path is never reached. With a lag the
## window is as wide as asked for and the requirement can actually fail. It is
## zero everywhere except that control.
var lag_frames := 0
var _frames := 0

var _dress: Node = null                ## dress_scene.gd, kept ALIVE across cells
var _fixture_energy := 3.0
var _player: Node3D = null
## WHO TO TELL WHEN GEOMETRY ARRIVES AND LEAVES. `walk.gd`, which owns the door,
## inhabitant and interactable nodes and holds the deck's sidecars. Without it a
## streamed cell is a dead shell: its pressure doors are solid, nobody in it
## knows a player exists, and nothing in it can be used -- which is exactly what
## a streamed build was until this hook existed. `--no-cell-wiring` leaves it
## null, and that is the control.
var _wiring: Node = null
var wired := 0
var unwired := 0

var _resident := {}                    ## id -> {node, col, tris, lights}
var _inflight := {}                    ## id -> {paths:[..], got:{path:res}}
var _ready_q: Array = []               ## ids loaded and waiting for their frame

# -- counters the gate reads -------------------------------------------------
var loads := 0                         ## cells activated
var frees := 0                         ## cells released
var double_loads := 0                  ## requests for a path already in flight
var abandoned := 0                     ## finished loading after falling out of want
var peak_resident := 0
var peak_tris := 0
var over_budget_frames := 0
var last_activate_ms := 0.0
var max_activate_ms := 0.0
## id -> distance from the player at the frame that cell became resident. This is
## THE number the gate is for: it must be positive for every cell entered.
var lead_m := {}


# ===========================================================================
# The derived numbers
# ===========================================================================

func _abs(rel: String) -> String:
	return ProjectSettings.globalize_path("res://").path_join(rel).simplify_path()


## The deck row `interior.ring_cells` produced for this deck, by sector and
## indices. Loud on a miss: a residency radius guessed from nothing is exactly
## the defect this file's docstring is about.
func deck_row(sector: String, ring_index: int, deck_index: int) -> Dictionary:
	var p := _abs(CELL_MANIFEST_PY)
	if not FileAccess.file_exists(p):
		problems.append("no cell manifest at " + p
			+ " -- run `python3 station/interior.py --cells`")
		return {}
	var j = JSON.parse_string(FileAccess.get_file_as_string(p))
	if typeof(j) != TYPE_DICTIONARY or not j.has("deck_table"):
		problems.append(p + " has no deck_table")
		return {}
	for row in j["deck_table"]:
		if (String(row.get("sector", "")) == sector
				and int(row.get("ring_index", -1)) == ring_index
				and int(row.get("deck_index", -1)) == deck_index):
			return row
	problems.append("no deck_table row for %s ring_index=%d deck_index=%d"
		% [sector, ring_index, deck_index])
	return {}


## `CELLS = { "cell_tris": 60_000, "resident_tris": 180_000, ... }` out of
## `station/budget.py`. Underscored integer literals and all.
func budget_cells() -> Dictionary:
	var p := _abs(BUDGET_PY)
	if not FileAccess.file_exists(p):
		problems.append("no such file: " + p)
		return {}
	var txt := FileAccess.get_file_as_string(p)
	var out := {}
	var re := RegEx.new()
	re.compile("(?m)^CELLS\\s*=\\s*\\{([\\s\\S]*?)^\\}")
	var m := re.search(txt)
	if m == null:
		problems.append(p + " has no module-level CELLS block")
		return {}
	var kv := RegEx.new()
	kv.compile("\"([a-z_]+)\"\\s*:\\s*([0-9_]+)")
	for r in kv.search_all(m.get_string(1)):
		out[r.get_string(1)] = int(r.get_string(2).replace("_", ""))
	for need in ["cell_tris", "resident_tris"]:
		if not out.has(need):
			problems.append("budget.CELLS has no " + need)
	return out


# ===========================================================================
# BAKE -- one built cluster into cells on the station's own cell grid
# ===========================================================================
#
# THE CELL BOUNDARY IS NOT INVENTED HERE. `interior.deck_cell` defines cell i of
# a deck as the arc [i*cell_deg, (i+1)*cell_deg] measured from 0 degrees, and
# that is the grid this cuts on -- so a cell baked out of one cluster carries the
# same id and the same arc as the cell a generator will one day emit directly.
# `cell_deg` is read from the manifest, never passed in.
#
# TRIANGLES ARE ASSIGNED, NEVER CUT. Each triangle goes whole to the cell its
# centroid falls in, so the union of the cells is the source mesh EXACTLY -- no
# gap can be introduced at a boundary by the bake itself, and a hole in the floor
# at a cell edge can only mean the neighbour is not resident. That is the
# property the gate depends on.
#
# THIS IS A BRIDGE, AND IT SAYS SO. In production a cell should be written by the
# generator that knows what is in it; the exact Python patch is in
# `docs/streaming-4g.md` under CHANGES I NEED IN FILES I DO NOT OWN. Until then
# this is how real station geometry becomes streamable cells without a second
# description of the station.

func bake(args: Dictionary) -> int:
	var t0 := Time.get_ticks_msec()
	var sector := String(args.get("sector", ""))
	var ring_index := int(args.get("ring-index", "0"))
	var deck_index := int(args.get("deck-index", "0"))
	var stem := String(args.get("cell-id", "cell"))
	var out_dir := String(args.get("cells-out", ""))
	if sector == "" or out_dir == "":
		push_error("bake: --sector and --cells-out are required")
		return 2

	var row := deck_row(sector, ring_index, deck_index)
	var bud := budget_cells()
	if not problems.is_empty():
		push_error("bake: " + ", ".join(problems))
		return 2
	var cell_deg := float(row["cell_deg"])
	var floor_r := float(row["floor_r_m"])
	var sight := float(row["sight_line_m"])
	print("bake: %s -- cell_deg=%.3f (%d cells round the ring), floor_r=%.2f m, "
		% [row["label"], cell_deg, int(row["cells"]), floor_r]
		+ "sight_line=%.1f m, kit cell=%d tri  [%s]"
		% [sight, int(row["cell_triangles"]), CELL_MANIFEST_PY])
	print("bake: budget cell_tris=%d resident_tris=%d -> %d cells resident  [%s]"
		% [bud["cell_tris"], bud["resident_tris"],
			int(bud["resident_tris"] / bud["cell_tris"]), BUDGET_PY])

	var vis := _load_glb(String(args.get("glb", "")))
	if vis == null:
		push_error("bake: could not load --glb")
		return 2
	add_child(vis)
	var col := _load_glb(String(args.get("collision", "")))
	if col == null:
		push_error("bake: could not load --collision")
		return 2
	add_child(col)
	print("bake: loaded in %d ms -- %d visual meshes, %d collision meshes"
		% [Time.get_ticks_msec() - t0, _meshes(vis).size(), _meshes(col).size()])

	DirAccess.make_dir_recursive_absolute(out_dir)
	var corr := _corridor_z(col)
	print("bake: corridor MEASURED at r=%.2f m, z=[%.2f,%.2f] (mid %.2f), "
		% [corr["r_floor_m"], corr["z0"], corr["z1"], corr["z_mid"]]
		+ "covering %.1f deg of arc -- the only floor that runs the whole run"
		% corr["arc_deg"])
	var vis_bins := _split(vis, cell_deg)
	var col_bins := _split(col, cell_deg)
	print("bake: split in %d ms -- %d visual cell(s), %d collision cell(s)"
		% [Time.get_ticks_msec() - t0, vis_bins.size(), col_bins.size()])

	# EVERY BIN EITHER HALF PRODUCED, not just the visual ones.
	#
	# THIS IS WHERE `red_2_4` LOST 138 TRIANGLES. The old loop walked
	# `vis_bins.keys()` and `continue`d past any bin with no collision, so those
	# triangles were neither written nor counted -- and the conservation
	# assertion at the bottom then fired with a total and no location, which is
	# exactly right and exactly unhelpful. A cell with render geometry and no
	# floor is a TRUE statement about that arc: the deck has something to look at
	# there and nothing to stand on, which the source says too. It is written,
	# with `collision` empty, and `stream.gd`'s loader asks for one half. A bin
	# with collision and no visual is written the same way, and used to vanish
	# from the manifest silently -- a floor a player would have fallen through
	# because nothing ever made it resident.
	var idx: Array = []
	for i in vis_bins:
		idx.append(i)
	for i in col_bins:
		if not vis_bins.has(i):
			idx.append(i)
	idx.sort()
	var rows: Array = []
	var half_only: Array = []
	for i in idx:
		var have_v: bool = vis_bins.has(i)
		var have_c: bool = col_bins.has(i)
		var vpath := out_dir.path_join("%s_c%02d.scn" % [stem, i])
		var cpath := out_dir.path_join("%s_c%02d_col.scn" % [stem, i])
		var vinfo: Dictionary = ({} if not have_v
			else _write_cell(vis_bins[i], "cell_%02d" % i, vpath))
		var cinfo: Dictionary = ({} if not have_c
			else _write_cell(col_bins[i], "cell_%02d_col" % i, cpath))
		if (have_v and vinfo.is_empty()) or (have_c and cinfo.is_empty()):
			push_error("bake: could not write cell %d" % i)
			return 2
		if not (have_v and have_c):
			half_only.append("cell %02d %6.2f-%6.2f deg: %s (%d tri)"
				% [i, i * cell_deg, (i + 1) * cell_deg,
					("NO COLLISION -- nothing to stand on there"
						if have_v else "NO RENDER MESH -- floor with no room"),
					int((vinfo if have_v else cinfo).get("tris", 0))])
		var aabb: AABB = (vinfo["aabb"] if have_v else cinfo["aabb"])
		if have_v and have_c:
			aabb = vinfo["aabb"].merge(cinfo["aabb"])
		rows.append({
			"id": "%s_c%02d" % [stem, i],
			"index": i,
			"mesh": (vpath.get_file() if have_v else ""),
			"collision": (cpath.get_file() if have_c else ""),
			# THE ARC IS THE DISTANCE METRIC. A 20 deg cell's world AABB is a
			# 145 x 145 m box and a distance to it is nearly meaningless; the
			# distance a player actually has to walk is along the arc, and the
			# cell knows its own arc exactly.
			"arc": {"r_m": floor_r, "a0_deg": i * cell_deg,
				"a1_deg": (i + 1) * cell_deg,
				# The z span comes from the COLLISION half where there is one --
				# a cell is a place you walk, and its render mesh reaches up into
				# ducting a body never gets to. With no collision half there is
				# nothing to walk and the render span is all there is.
				"z0": snappedf(float((cinfo if have_c else vinfo)["zmin"]), 0.001),
				"z1": snappedf(float((cinfo if have_c else vinfo)["zmax"]), 0.001)},
			"aabb": {"pos": [aabb.position.x, aabb.position.y, aabb.position.z],
				"size": [aabb.size.x, aabb.size.y, aabb.size.z]},
			"tris": int(vinfo.get("tris", 0)),
			"col_tris": int(cinfo.get("tris", 0)),
			"groups": int(vinfo.get("groups", 0)),
			# A spawn is a CLAIM -- see walk.gd. It is placed 0.2 m off the
			# MEASURED corridor floor at the cell's arc centre, so the settle
			# either confirms it or does not.
			"spawn": _floor_point(corr, (i + 0.5) * cell_deg, 0.2),
		})
		print("  cell %02d  %6.2f-%6.2f deg  %7d tri  %5d col tri  %3d groups  "
			% [i, i * cell_deg, (i + 1) * cell_deg, int(vinfo.get("tris", 0)),
				int(cinfo.get("tris", 0)), int(vinfo.get("groups", 0))]
			+ "%5.1f MB%s" % [_file_mb(vpath) + _file_mb(cpath),
				("" if have_v and have_c
					else ("   NO COLLISION" if have_v else "   NO RENDER MESH"))])

	var nominal := int(bud["resident_tris"] / bud["cell_tris"])
	var man := {
		"version": 1,
		"kind": "ring",
		"written_by": "godot/scripts/stream.gd bake()",
		"source": {"glb": String(args.get("glb", "")),
			"collision": String(args.get("collision", "")),
			"sector": sector, "ring_index": ring_index,
			"deck_index": deck_index, "label": row["label"]},
		"cell_deg": cell_deg,
		"floor_r_m": floor_r,
		# The corridor's own measured position, so a caller that wants to walk
		# ALONG the run -- rather than into a room -- does not have to guess.
		"corridor": {"r_floor_m": snappedf(float(corr["r_floor_m"]), 0.001),
			"z0": corr["z0"], "z1": corr["z1"],
			"z_mid": corr["z_mid"], "arc_deg": snappedf(float(corr["arc_deg"]), 0.1),
			# Recovered from the deck row's own two numbers rather than restated:
			# sight = 2*sqrt(r^2 - (r-w)^2) inverts to w exactly.
			"width_m": snappedf(floor_r - sqrt(maxf(floor_r * floor_r
				- sight * sight / 4.0, 0.0)), 0.001)},
		"residency": {
			"radius_m": sight,
			"radius_from": "cell_manifest.json deck_table[%s].sight_line_m -- "
				% row["id"] + "interior.sight_line(%.2f, corridor_width), the "
				% floor_r + "chord past which the ring's own curvature occludes",
			# THE DEADBAND IS AS LARGE AS IT CAN BE WITHOUT ADMITTING A FOURTH
			# CELL, and that bound is exactly one cell length: a cell two away
			# is never nearer than `cell_length_m`, so any free radius above it
			# holds a cell the player has walked past and can no longer see.
			# Measured before this was derived, with the free radius set to
			# radius + one cell: `resident_max=4` on a run whose want set never
			# exceeded 3, the fourth being dead weight the budget still pays for.
			# Here it leaves 73.8 - 66.1 = 7.7 m of hysteresis, which at
			# `player.gd`'s 8.0 m/s sprint is 0.96 s -- two orders of magnitude
			# more than the measured activation, so a body that turns round on
			# the threshold cannot outrun the reload.
			"free_radius_m": maxf(sight, float(row["cell_length_m"])),
			"free_from": "cell_length_m (%.1f m) -- the largest deadband that "
				% float(row["cell_length_m"])
				+ "cannot admit a fourth cell, since a cell two away is never "
				+ "nearer than one cell length. Hysteresis %.1f m = %.2f s at "
				% [float(row["cell_length_m"]) - sight,
					(float(row["cell_length_m"]) - sight) / 8.0]
				+ "the shipped sprint speed",
			"resident_tris": bud["resident_tris"],
			"cell_tris": bud["cell_tris"],
			"cells_resident_nominal": nominal,
			"budget_from": "station/budget.py CELLS -- 'the cell you are in "
				+ "plus both neighbours'",
			"cell_length_m": row["cell_length_m"],
		},
		"cells": rows,
	}
	# ONE MANIFEST PER CLUSTER, NOT ONE PER DIRECTORY. `tools/bake_station.py`
	# bakes seventy decks into a single `--cells-out`, and every one of them used
	# to write `cells.json` -- so after a three-minute whole-station bake the
	# 940 cells on disk were described by the four cells of whichever deck ran
	# last. The stem is unique per cluster and already prefixes every cell id, so
	# `<stem>_cells.json` cannot be overwritten by a sibling deck. `cells.json`
	# is still written for a single-cluster bake, which is what every gate and
	# every command in `docs/streaming-4g.md` names.
	var mpath := out_dir.path_join(stem + "_cells.json")
	for p in [mpath, out_dir.path_join("cells.json")]:
		var f := FileAccess.open(p, FileAccess.WRITE)
		if f == null:
			push_error("bake: cannot write " + p)
			return 2
		f.store_string(JSON.stringify(man, "  "))
		f.close()
	var tot := 0
	var ctot := 0
	for r in rows:
		tot += int(r["tris"])
		ctot += int(r["col_tris"])
	print("bake: %d cells, %d triangles total (source had %d), %.1f MB, "
		% [rows.size(), tot, _mesh_tris(vis), _dir_mb(out_dir)]
		+ "%d ms -> %s" % [Time.get_ticks_msec() - t0, mpath])
	if not half_only.is_empty():
		# NAMED, NOT COUNTED. A conservation failure with a total and no location
		# is a diagnosis pass nobody can start; these are the arcs where the two
		# halves of the deck disagree about what exists.
		print("bake: %d cell(s) have only one half:" % half_only.size())
		for s in half_only:
			print("        " + s)
	# THE BAKE IS LOSSLESS OR IT IS A BUG. Triangles are assigned whole, so the
	# cells must sum to the source exactly; a mismatch means a triangle was
	# dropped and a dropped triangle is a hole in a floor.
	var src := _mesh_tris(vis)
	var csrc := _mesh_tris(col)
	if tot != src or ctot != csrc:
		push_error("bake: LOST %d render and %d collision triangles -- the "
			% [src - tot, csrc - ctot] + "cells do not sum to the source and a "
			+ "lost triangle is a hole")
		# WHERE, per cell, so the next reader does not have to reproduce the
		# arithmetic to find out which arc is short.
		for r in rows:
			print("        cell %02d: %d render, %d collision"
				% [int(r["index"]), int(r["tris"]), int(r["col_tris"])])
		return 2
	return 0


func _file_mb(p: String) -> float:
	if not FileAccess.file_exists(p):
		return 0.0
	return FileAccess.open(p, FileAccess.READ).get_length() / 1048576.0


func _dir_mb(d: String) -> float:
	var t := 0.0
	for n in DirAccess.get_files_at(d):
		t += _file_mb(d.path_join(n))
	return t


## Assign every triangle of every mesh under `root` to a cell of the ring grid.
## Returns {cell_index: {group_name: [PackedVector3Array pos, nrm, PackedVector2Array uv]}}.
func _split(root: Node, cell_deg: float) -> Dictionary:
	var bins := {}
	for mi: MeshInstance3D in _meshes(root):
		var name := String(mi.name)
		var xf: Transform3D = mi.global_transform
		for s in mi.mesh.get_surface_count():
			if mi.mesh.surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
				continue
			var arr: Array = mi.mesh.surface_get_arrays(s)
			var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var nrm: PackedVector3Array = (arr[Mesh.ARRAY_NORMAL]
				if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array())
			var uv: PackedVector2Array = (arr[Mesh.ARRAY_TEX_UV]
				if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array())
			var ix: PackedInt32Array = (arr[Mesh.ARRAY_INDEX]
				if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array())
			var n_tri := (ix.size() if ix.size() > 0 else pos.size()) / 3
			for t in n_tri:
				var i0 := (ix[t * 3] if ix.size() > 0 else t * 3)
				var i1 := (ix[t * 3 + 1] if ix.size() > 0 else t * 3 + 1)
				var i2 := (ix[t * 3 + 2] if ix.size() > 0 else t * 3 + 2)
				var p0: Vector3 = xf * pos[i0]
				var p1: Vector3 = xf * pos[i1]
				var p2: Vector3 = xf * pos[i2]
				var cx: float = (p0.x + p1.x + p2.x) / 3.0
				var cy: float = (p0.y + p1.y + p2.y) / 3.0
				var a: float = rad_to_deg(atan2(cy, cx))
				if a < 0.0:
					a += 360.0
				var cell := int(floor(a / cell_deg))
				var g = bins.get(cell)
				if g == null:
					g = {}
					bins[cell] = g
				var slot = g.get(name)
				if slot == null:
					slot = [PackedVector3Array(), PackedVector3Array(),
						PackedVector2Array()]
					g[name] = slot
				slot[0].append(p0)
				slot[0].append(p1)
				slot[0].append(p2)
				if nrm.size() > 0:
					var b: Basis = xf.basis
					slot[1].append((b * nrm[i0]).normalized())
					slot[1].append((b * nrm[i1]).normalized())
					slot[1].append((b * nrm[i2]).normalized())
				if uv.size() > 0:
					slot[2].append(uv[i0])
					slot[2].append(uv[i1])
					slot[2].append(uv[i2])
	return bins


## One cell's groups into a PackedScene on disk. Node names are the SOURCE GROUP
## NAMES unchanged -- that is the contract with `dress_scene.gd`, which matches
## material rules against `mi.name` and would put every streamed surface on the
## glTF fallback if this renamed anything.
func _write_cell(groups: Dictionary, root_name: String, path: String) -> Dictionary:
	var root := Node3D.new()
	root.name = root_name
	var tris := 0
	var n_groups := 0
	var box := AABB()
	var first := true
	var zmin := INF
	var zmax := -INF
	for name in groups:
		var slot: Array = groups[name]
		var pos: PackedVector3Array = slot[0]
		if pos.size() < 3:
			continue
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = pos
		if slot[1].size() == pos.size():
			arr[Mesh.ARRAY_NORMAL] = slot[1]
		if slot[2].size() == pos.size():
			arr[Mesh.ARRAY_TEX_UV] = slot[2]
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		var mi := MeshInstance3D.new()
		mi.name = name
		mi.mesh = am
		root.add_child(mi)
		mi.owner = root
		tris += pos.size() / 3
		n_groups += 1
		var b := am.get_aabb()
		box = b if first else box.merge(b)
		first = false
		zmin = minf(zmin, b.position.z)
		zmax = maxf(zmax, b.end.z)
	if first:
		root.free()
		return {}
	var ps := PackedScene.new()
	if ps.pack(root) != OK:
		root.free()
		return {}
	var rc := ResourceSaver.save(ps, path)
	root.free()
	if rc != OK:
		return {}
	return {"tris": tris, "groups": n_groups, "aabb": box,
		"zmin": zmin, "zmax": zmax}


## WHERE THE CORRIDOR IS, IN Z, MEASURED OFF THE COLLISION SHELL.
##
## A ring corridor sweeps in ANGLE at a fixed z, and its width lies along the
## station's z axis -- so on this cluster the corridor is a 2.5 m strip at
## z ~ 7465 and everything from z 7429 to 7463 is the ROOMS hanging off it.
## The mid-z of a cell's bounding box is therefore inside a docking bay, not on
## the corridor, and a body spawned there is a body spawned in the wrong place.
##
## The corridor is the only floor that runs the whole arc, so that is what this
## looks for: bucket the floor triangles by z, measure how many degrees of arc
## each bucket covers, and take the z range of the buckets that cover nearly all
## of it. Measured rather than written down, for the reason
## `station/collision.py` ray-casts its shell profile instead of asserting it.
##
## COVERAGE, NOT MIN-TO-MAX, and getting that wrong put every spawn on `blue_0_0`
## in mid-air. The first version measured a bucket's arc as `max(angle) -
## min(angle)`, which is the SPREAD of the floor in it and not how much of the
## ring it covers: this deck has six rooms at 0, 130, 180, 260, 300 and 320
## degrees, so a z bucket holding nothing but room floors spreads across 320
## degrees while covering about 24 of them. The corridor lost to the rooms, the
## measured z came out 3.8 m off, and `_floor_point` then placed all eighteen
## cell spawns where this deck has no floor at all. Counting occupied one-degree
## bins tells a ring from six rooms; a spread cannot.
func _corridor_z(col_root: Node) -> Dictionary:
	var rmax := 0.0
	var tri: Array = []
	for mi: MeshInstance3D in _meshes(col_root):
		var xf: Transform3D = mi.global_transform
		for s in mi.mesh.get_surface_count():
			if mi.mesh.surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
				continue
			var arr: Array = mi.mesh.surface_get_arrays(s)
			var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var ix: PackedInt32Array = (arr[Mesh.ARRAY_INDEX]
				if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array())
			var n_tri := (ix.size() if ix.size() > 0 else pos.size()) / 3
			for t in n_tri:
				var q: Vector3 = Vector3.ZERO
				for k in 3:
					var i := (ix[t * 3 + k] if ix.size() > 0 else t * 3 + k)
					q += xf * pos[i]
				q /= 3.0
				var r := sqrt(q.x * q.x + q.y * q.y)
				rmax = maxf(rmax, r)
				var a := rad_to_deg(atan2(q.y, q.x))
				tri.append([r, (a + 360.0 if a < 0.0 else a), q.z])
	var span := {}
	for e in tri:
		if e[0] < rmax - 0.1:
			continue                              # not floor
		var b := int(round(e[2] * 2.0))           # 0.5 m buckets
		if not span.has(b):
			span[b] = {}
		span[b][int(floor(e[1]))] = true          # one-degree bins
	var best := 0
	for b in span:
		best = maxi(best, span[b].size())
	var zlo := INF
	var zhi := -INF
	for b in span:
		if span[b].size() >= int(ceil(float(best) * 0.95)):
			zlo = minf(zlo, b / 2.0)
			zhi = maxf(zhi, b / 2.0)
	return {"r_floor_m": rmax, "z0": zlo, "z1": zhi,
		"z_mid": (zlo + zhi) * 0.5, "arc_deg": float(best)}


## A point on the measured corridor floor. On a spun ring UP IS INWARD, so the
## floor is the LARGEST radius the collision shell reaches and "up" is `-radial`.
func _floor_point(corr: Dictionary, angle_deg: float, up_m: float) -> Array:
	var r: float = float(corr["r_floor_m"]) - up_m
	var a := deg_to_rad(angle_deg)
	return [r * cos(a), r * sin(a), float(corr["z_mid"])]


func _mesh_tris(root: Node) -> int:
	var n := 0
	for mi: MeshInstance3D in _meshes(root):
		for s in mi.mesh.get_surface_count():
			if mi.mesh.surface_get_primitive_type(s) != Mesh.PRIMITIVE_TRIANGLES:
				continue
			var arr: Array = mi.mesh.surface_get_arrays(s)
			var ix: PackedInt32Array = (arr[Mesh.ARRAY_INDEX]
				if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array())
			var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			n += (ix.size() if ix.size() > 0 else pos.size()) / 3
	return n


func _load_glb(path: String) -> Node:
	if path == "" or not FileAccess.file_exists(path):
		return null
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		return null
	return doc.generate_scene(state)


func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		_meshes(c, out)
	return out


# ===========================================================================
# RUNTIME -- residency
# ===========================================================================

## Load the manifest and adopt its residency numbers. `dress` is
## `dress_scene.gd`, already prepared, and is kept ALIVE for the session: it
## holds the instantiated `interior.tscn` that owns the material table, and a
## streamed cell needs it every time one arrives. `walk.gd` releases it after a
## single bind; this one must not.
func configure(manifest_path: String, dress: Node, fixture_energy: float,
		off: bool) -> bool:
	disabled = off
	_dress = dress
	_fixture_energy = fixture_energy
	if not FileAccess.file_exists(manifest_path):
		problems.append("no cell manifest at " + manifest_path)
		return false
	var j = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if typeof(j) != TYPE_DICTIONARY or not j.has("cells"):
		problems.append(manifest_path + " is not a cell manifest")
		return false
	plan = j
	var dir := manifest_path.get_base_dir()
	cells = []
	for c in j["cells"]:
		var d: Dictionary = c.duplicate(true)
		# EITHER HALF MAY BE ABSENT, and the manifest says which. A cell with
		# render geometry and no floor is a real thing on this station -- see
		# `bake()` -- and dropping it was how 138 triangles of `red_2_4` went
		# missing. An empty string here means "there is no such half", not "the
		# path is the directory".
		d["mesh_path"] = ("" if String(d.get("mesh", "")) == ""
			else dir.path_join(String(d["mesh"])))
		d["collision_path"] = ("" if String(d.get("collision", "")) == ""
			else dir.path_join(String(d["collision"])))
		cells.append(d)
	var res: Dictionary = j.get("residency", {})
	radius_m = float(res.get("radius_m", 0.0))
	free_m = float(res.get("free_radius_m", radius_m * 2.0))
	resident_tris_budget = int(res.get("resident_tris", 0))
	cell_tris_budget = int(res.get("cell_tris", 1))
	# AT MOST (nominal - 1) CELLS CAN NEED LOADING AT ONCE while the player walks
	# forward a cell at a time, so that is the queue depth. Not a tuning knob:
	# more in flight would not make the third cell arrive sooner, it would make
	# the second arrive later.
	max_inflight = maxi(1, int(res.get("cells_resident_nominal", 3)) - 1)
	if radius_m <= 0.0 or resident_tris_budget <= 0:
		problems.append("manifest carries no residency radius or budget")
		return false
	print("stream: %d cells, radius %.1f m (%s), free at %.1f m, "
		% [cells.size(), radius_m,
			String(res.get("radius_from", "?")).substr(0, 48), free_m]
		+ "budget %d tri = %d cells, %d in flight%s%s"
		% [resident_tris_budget,
			int(resident_tris_budget / maxi(cell_tris_budget, 1)), max_inflight,
			("  -- DISABLED (negative control)" if disabled else ""),
			("" if lag_frames == 0 else
				"  -- LAGGED %d frames (stress control)" % lag_frames)])
	return true


func set_player(body: Node3D) -> void:
	_player = body


## The node whose `wire_cell(id, visual, collision)` and `unwire_cell(id)` are
## called as cells arrive and leave.
func set_wiring(node: Node) -> void:
	_wiring = node
	# ANYTHING ALREADY RESIDENT GETS WIRED NOW. The start cell is primed
	# synchronously, before the player exists and therefore before `walk.gd` can
	# hand this over -- so without this the one cell a player is guaranteed to be
	# standing in would be the one cell whose doors never worked.
	for id in resident_ids():
		var r: Dictionary = _resident[id]
		if not bool(r.get("wired", false)):
			r["wired"] = true
			wired += 1
			node.wire_cell(id, r["vis"], r["col"])


func cell_by_index(i: int) -> Dictionary:
	for c in cells:
		if int(c["index"]) == i:
			return c
	return {}


func cell_by_id(id: String) -> Dictionary:
	return _by_id(id)


## Distance from a world point to a cell, ALONG THE CORRIDOR. Zero inside.
##
## An arc cell's world AABB is a 145 m box whose nearest corner is nothing a
## player can walk to; the number that decides residency is how far they would
## have to WALK, which for a ring is arc length and for anything else is the
## AABB. Both forms are in the manifest and this picks whichever the cell has.
func distance_to(c: Dictionary, p: Vector3) -> float:
	if c.has("arc"):
		var arc: Dictionary = c["arc"]
		var a := rad_to_deg(atan2(p.y, p.x))
		if a < 0.0:
			a += 360.0
		var a0 := float(arc["a0_deg"])
		var a1 := float(arc["a1_deg"])
		var da := 0.0
		if not (a >= a0 and a < a1):
			var d0: float = fmod(absf(a - a0) + 360.0, 360.0)
			d0 = minf(d0, 360.0 - d0)
			var d1: float = fmod(absf(a - a1) + 360.0, 360.0)
			d1 = minf(d1, 360.0 - d1)
			da = minf(d0, d1)
		var along := deg_to_rad(da) * float(arc["r_m"])
		var dz := maxf(0.0, maxf(float(arc["z0"]) - p.z, p.z - float(arc["z1"])))
		return sqrt(along * along + dz * dz)
	var ab: Dictionary = c["aabb"]
	var box := AABB(Vector3(ab["pos"][0], ab["pos"][1], ab["pos"][2]),
		Vector3(ab["size"][0], ab["size"][1], ab["size"][2]))
	if box.has_point(p):
		return 0.0
	var q := Vector3(clampf(p.x, box.position.x, box.end.x),
		clampf(p.y, box.position.y, box.end.y),
		clampf(p.z, box.position.z, box.end.z))
	return p.distance_to(q)


## The cell the player is inside, or -1.
func cell_at(p: Vector3) -> int:
	for c in cells:
		if distance_to(c, p) <= 0.0:
			return int(c["index"])
	return -1


func is_resident(id: String) -> bool:
	return _resident.has(id)


func resident_ids() -> Array:
	var k: Array = _resident.keys()
	k.sort()
	return k


func inflight_count() -> int:
	return _inflight.size()


func resident_tris() -> int:
	var n := 0
	for id in _resident:
		n += int(_resident[id]["tris"])
	return n


## Load the cell the player starts in, synchronously, before the first frame.
##
## A LEVEL'S FIRST CELL IS A LOAD SCREEN, NOT A STREAM, and pretending otherwise
## would make the gate measure the wrong thing: a body spawned into a cell that
## has not arrived falls for a hundred frames and the verdict blames streaming
## for a start-up ordering mistake. Returns milliseconds spent.
func prime(index: int) -> int:
	var t0 := Time.get_ticks_msec()
	var c := cell_by_index(index)
	if c.is_empty():
		problems.append("no cell with index %d" % index)
		return 0
	var save := lag_frames
	lag_frames = 0                     # the load screen is never lagged
	_request(c)
	# THE EYE IS THE CELL'S OWN SPAWN, not the world origin. `dress.light` picks
	# which fittings cast shadows by distance from the eye, and the origin is
	# 7.4 km away down the station's axis -- so the start cell, the one the
	# player is standing in, would be the only cell in the build whose shadow
	# casters were chosen by an arbitrary tiebreak.
	var sp: Array = c["spawn"]
	var eye := Vector3(sp[0], sp[1], sp[2])
	while _inflight.has(String(c["id"])):
		_poll()
		if _ready_q.size() > 0:
			_activate(_ready_q.pop_front(), eye, true)
		else:
			OS.delay_msec(2)
	lag_frames = save
	return Time.get_ticks_msec() - t0


## One frame of residency. Call from `_physics_process` with the body's position.
func update(p: Vector3) -> void:
	_frames += 1
	_poll()
	var want := {}
	var d := {}
	for c in cells:
		var id := String(c["id"])
		d[id] = distance_to(c, p)
		if d[id] <= radius_m:
			want[id] = true

	# -- FREE. Never the cell the player is in, never one the player is entering,
	# never anything inside the sight line, and only past the deadband. `want`
	# already covers the first three -- a cell containing the player is at
	# distance 0 and a cell being entered is nearer than the sight line by
	# definition -- and they are ALSO asserted separately, because a rule that is
	# only implied by another rule stops being checked the moment that other rule
	# changes.
	var here := cell_at(p)
	var entering := _entering(p)
	for id in _resident.keys():
		if want.has(id) or d[id] <= free_m:
			continue
		var c := _by_id(id)
		if int(c["index"]) == here or int(c["index"]) == entering:
			push_error("stream: refused to free the cell the player is in "
				+ "or entering (%s at %.1f m)" % [id, d[id]])
			continue
		_free_cell(id)

	# -- ACTIVATE. AT MOST ONE PER FRAME. Instancing, the trimesh collider, the
	# material bind and the fittings are all main-thread work; doing two cells on
	# one frame is how a streamer produces the hitch it exists to remove.
	if not disabled and _ready_q.size() > 0:
		var id: String = _ready_q.pop_front()
		if want.has(id) or d.get(id, 1e30) <= free_m:
			_activate(id, p)
		else:
			# The player turned round while this was in flight. It finished
			# anyway -- ResourceLoader has no cancel -- so the resource is
			# dropped rather than instanced. Counted, because a streamer that
			# silently does work nobody asked for is a streamer whose cost
			# nobody can see.
			abandoned += 1
			_inflight.erase(id)

	# -- REQUEST, nearest first. Nearest first is what makes the lead positive:
	# the cell you are about to walk into is the nearest one that is not
	# resident.
	if not disabled:
		var need: Array = []
		for id in want:
			if not _resident.has(id) and not _inflight.has(id):
				need.append([d[id], id])
		need.sort()
		for pair in need:
			if _inflight.size() >= max_inflight:
				break
			_request(_by_id(pair[1]))

	# COUNTED IN BOTH MODES, and the control is why. With the accounting behind
	# the `disabled` early return the negative control reported
	# `resident_max=0` while one cell was demonstrably resident and holding the
	# body up -- a statistic that only exists in the configuration that passes
	# is a statistic nobody can compare against.
	peak_resident = maxi(peak_resident, _resident.size())
	var tris := resident_tris()
	peak_tris = maxi(peak_tris, tris)
	if tris > resident_tris_budget:
		over_budget_frames += 1


## The cell the player is about to be in: the one containing the point a
## `sight_line` ahead along their own velocity. Kept separate from the radius
## rule on purpose -- see the comment in `update`.
func _entering(p: Vector3) -> int:
	if _player == null:
		return -1
	var v: Vector3 = _player.velocity
	if v.length_squared() < 1e-4:
		return -1
	return cell_at(p + v.normalized() * radius_m)


func _by_id(id: String) -> Dictionary:
	for c in cells:
		if String(c["id"]) == id:
			return c
	return {}


## Ask for both halves of a cell. Guarded against double-loading in the only
## place a double-load can be issued.
func _request(c: Dictionary) -> void:
	var id := String(c["id"])
	if _resident.has(id) or _inflight.has(id):
		double_loads += 1
		return
	var paths := []
	for key in ["mesh_path", "collision_path"]:
		if String(c.get(key, "")) != "":
			paths.append(String(c[key]))
	for p in paths:
		if not FileAccess.file_exists(p):
			push_error("stream: cell %s has no %s" % [id, p])
			return
		if ResourceLoader.load_threaded_request(p) != OK:
			push_error("stream: load_threaded_request failed for " + p)
			return
	_inflight[id] = {"paths": paths, "got": {}, "t0": Time.get_ticks_msec(),
		"f0": _frames}


## Poll every in-flight request. Nothing here blocks.
func _poll() -> void:
	for id in _inflight.keys():
		var rec: Dictionary = _inflight[id]
		for p in rec["paths"]:
			if rec["got"].has(p):
				continue
			var prog := []
			var st := ResourceLoader.load_threaded_get_status(p, prog)
			if st == ResourceLoader.THREAD_LOAD_LOADED:
				rec["got"][p] = ResourceLoader.load_threaded_get(p)
			elif st == ResourceLoader.THREAD_LOAD_FAILED:
				push_error("stream: threaded load FAILED for " + p)
				_inflight.erase(id)
				break
		if _inflight.has(id) and rec["got"].size() == rec["paths"].size():
			if _frames - int(rec["f0"]) < lag_frames:
				continue
			if not _ready_q.has(id):
				_ready_q.append(id)


## Put a loaded cell into the world: instance, collide, dress, light.
##
## EVERY STEP `walk.gd::_load_level` TAKES, IN THE SAME ORDER. The visual meshes
## get NO colliders and the collision proxy gets trimesh ones and is hidden --
## that separation is `station/collision.py`'s whole finding, and a streamed cell
## that collided its render mesh would put the corridor's 66 mm lighting channel
## straight back under the player's feet.
func _activate(id: String, p: Vector3, primed: bool = false) -> void:
	var t0 := Time.get_ticks_usec()
	var rec: Dictionary = _inflight.get(id, {})
	if rec.is_empty():
		return
	_inflight.erase(id)
	var c := _by_id(id)
	var vis: Node = null
	var col: Node = null
	if String(c.get("mesh_path", "")) != "":
		vis = (rec["got"][String(c["mesh_path"])] as PackedScene).instantiate()
		vis.name = "vis_" + id
		add_child(vis)
	if String(c.get("collision_path", "")) != "":
		col = (rec["got"][String(c["collision_path"])] as PackedScene).instantiate()
		col.name = "col_" + id
		add_child(col)
	if vis == null:
		# A cell with a floor and nothing to look at. Legal, and the visual root
		# has to exist anyway because the fittings hang off it.
		vis = Node3D.new()
		vis.name = "vis_" + id
		add_child(vis)
	var ncol := 0
	if col != null:
		for m in _meshes(col):
			m.create_trimesh_collision()
			m.visible = false
			ncol += 1

	var lights := Node3D.new()
	lights.name = "fit_" + id
	vis.add_child(lights)
	var bound := 0
	if _dress != null:
		var mm: Dictionary = _dress.bind(vis)
		bound = int(mm["bound"])
		var un: PackedStringArray = mm["unmatched"]
		if not un.is_empty():
			print("stream: cell %s -- %d group(s) on the glTF fallback: %s"
				% [id, un.size(), ", ".join(un.slice(0, 6))])
		_dress.light(vis, lights, _fixture_energy, p)

	_resident[id] = {"vis": vis, "col": col, "tris": int(c["tris"]),
		"lights": lights, "wired": false}
	# WIRE IT. Everything `walk.gd::_load_level` does to a monolithic scene after
	# it has colliders and materials -- doors, inhabitants, crowd, interactables
	# -- happens here for a cell, in the same order, because a streamed cell that
	# is not wired is a shell: solid doors, nobody home, nothing to use.
	if _wiring != null:
		_resident[id]["wired"] = true
		wired += 1
		_wiring.wire_cell(id, vis, col)
	loads += 1
	# INF FOR THE PRIMED CELL, NOT ZERO. There is no body yet when the load
	# screen runs, so its lead is not "the body was standing on it as it
	# arrived" -- it is "it was there before the body existed". Recording zero
	# made a run that turned round and re-entered its start cell report
	# `min_lead_m=0.00`, which reads as the exact failure this gate is for.
	lead_m[id] = (INF if primed else distance_to(c, p))
	last_activate_ms = (Time.get_ticks_usec() - t0) / 1000.0
	max_activate_ms = maxf(max_activate_ms, last_activate_ms)
	print("stream: +%s  %d tri, %d col mesh, %d materialled, %.1f ms, "
		% [id, int(c["tris"]), ncol, bound, last_activate_ms]
		+ "lead %s, resident %d (%d tri)"
		% [("primed" if is_inf(lead_m[id]) else "%.1f m" % lead_m[id]),
			_resident.size(), resident_tris()])


func _free_cell(id: String) -> void:
	var r: Dictionary = _resident[id]
	# UNWIRE BEFORE FREEING, NOT AFTER. `door.gd`, `npc.gd` and `interact.gd`
	# hold references INTO this subtree -- leaves, body parts, prompt targets --
	# and they own nodes of their own that stand for them: an inhabitant's
	# capsule and an interactable's proxy box are children of THOSE nodes, not of
	# the cell, so freeing the cell alone leaves an invisible person to bump into
	# and a prompt for a console that is not there.
	if _wiring != null and bool(r.get("wired", false)):
		unwired += 1
		_wiring.unwire_cell(id)
	# The lights are children of the visual root and the colliders are children
	# of the collision meshes, so both go with their cell. Nothing here keeps a
	# second list that could drift from what is actually in the tree.
	if r["vis"] != null:
		r["vis"].queue_free()
	if r["col"] != null:
		r["col"].queue_free()
	_resident.erase(id)
	frees += 1
	print("stream: -%s  resident %d (%d tri)"
		% [id, _resident.size(), resident_tris()])


func report() -> String:
	return ("cells=%d resident_max=%d resident_tris_max=%d budget_tris=%d "
		+ "radius_m=%.1f free_m=%.1f loads=%d frees=%d double_loads=%d "
		+ "abandoned=%d over_budget_frames=%d max_activate_ms=%.1f "
		+ "lag_frames=%d wired=%d unwired=%d") % [
		cells.size(), peak_resident, peak_tris, resident_tris_budget,
		radius_m, free_m, loads, frees, double_loads, abandoned,
		over_budget_frames, max_activate_ms, lag_frames, wired, unwired]
