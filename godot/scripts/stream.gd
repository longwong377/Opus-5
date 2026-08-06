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
##
## ===========================================================================
## THE CELL GRID HAD NO AXIAL DIMENSION, AND THAT IS WHY THE STATION WAS ONE
## Z-CLUSTER (session 4r, INV-610..613)
## ===========================================================================
##
## THE MEASUREMENT FIRST, because the conclusion is only interesting with it.
## `interior.ring_cells` cuts a deck into N ANGULAR wedges -- `cell_manifest`'s
## row for Blue 1 deck 0 says `cells: 18, cell_deg: 20.0, z0: 6794, z1: 8047` --
## and `_split` below binned every triangle by `atan2(y, x)` and nothing else.
## So a cell was a wedge running the deck's WHOLE 1,253 m of axis. Baked from
## the whole-deck build, `blue_0_0`'s eighteen cells each spanned
## z 6896.85..8005.41 and cell 4 alone carried **582,792 triangles -- 3.24x the
## entire 180,000 resident budget, in one cell.**
##
## AND THE ONLY ROUTE BETWEEN Z-CLUSTERS LIVES INSIDE ONE OF THOSE WEDGES.
## Measured off `blue_0_0_collision.glb` by merging the z intervals of every
## floor triangle per one-degree bin: exactly ONE bin of 360 carries floor
## spanning more than 300 m, and it carries 1,101.9 m of it IN A SINGLE
## UNBROKEN RUN -- an axial spine at 88.87..89.46 deg, 2.16 m wide, from
## z 6904 to z 8005, threading every ring corridor on the deck (z 6900 covering
## 164 deg of arc, 7120 covering 345, 7460 covering 206, 7960 covering 225,
## 8000 covering 360). 89 deg is inside cell 4, which is 80..100 deg.
##
## SO THE CLUSTER-TO-CLUSTER HAND-OFF WAS NOT UNTESTED. IT WAS UNREACHABLE.
## A body walking the spine from the docking bays at z 7121 to customs at
## z 7460 -- 340 m, across four z-clusters -- never leaves cell 4, so the
## streamer performs ZERO loads and ZERO frees over the whole traverse while
## holding 3.24x its budget resident the entire time. There was no boundary to
## hand off across, because the grid has no boundaries in the direction the
## station is long.
##
## THE FIX IS A SECOND AXIS ON THE GRID, AND THE RUNTIME WAS ALREADY READY FOR
## IT. `distance_to` has always computed `sqrt(along^2 + dz^2)` -- arc distance
## and the z-distance outside `[z0, z1]` -- so a cell that is bounded in z has
## always been handled correctly by residency, freeing, `cell_at` and
## `_entering`. Only `bake()` was one-dimensional. Nothing below `bake()`
## changed to make an axial hand-off work; it worked as soon as the bake stopped
## emitting 1.1 km cells.
##
## THE BAND LENGTH IS THE DECK'S OWN `cell_length_m` (73.8 m here), and that is
## a derivation rather than a pick -- see INV-610. The free-radius argument
## above says the deadband may be as large as one cell length "since a cell two
## away is never nearer than one cell length". That is a statement about the
## SPACING OF NEIGHBOURS, and it was true in the arc direction because arc
## neighbours are `cell_length_m` apart. Making the axial band exactly
## `cell_length_m` keeps one free radius valid in both directions with the same
## 7.7 m of hysteresis, and makes a cell SQUARE on the floor a player walks. A
## different band length would need a second free radius and a second
## derivation.
##
## AND ONE THING IT IS HONEST ABOUT RATHER THAN QUIET ABOUT (INV-611). The
## residency RADIUS is `sight_line_m`, derived as the chord past which the
## RING'S OWN CURVATURE occludes. An axial corridor is STRAIGHT: it has no
## curvature and therefore no such horizon, so along the axis 66.1 m is a
## BUDGET bound and not an occlusion bound, and a cell arriving 66 m ahead down
## the spine is in principle visible arriving. That is a real, stated shortfall
## with three possible answers -- a bigger budget, an axial LOD, or a door -- and
## none of them is decided here. What is NOT acceptable is the previous state,
## where the question could not arise because nothing ever popped.
##
## `--z-band=0` rebuilds the old one-dimensional grid and is the control: the
## same deck comes back as 18 cells of 1.1 km, and the axial gate below fails on
## it with `loads=0 frees=0` after walking the same 340 m.

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
	# THE AXIAL BAND. Default is the deck's own arc-cell length, so one free
	# radius stays valid in both directions -- see the header. `--z-band=0` is
	# the one-dimensional control and reproduces the old grid exactly.
	var z_band := float(row["cell_length_m"])
	if args.has("z-band"):
		z_band = float(args["z-band"])
	# The band grid is anchored at the DECK's own z0, not at whatever this build
	# happens to start at -- the same rule as the arc grid being measured from
	# 0 degrees, and for the same reason: a cell baked out of one cluster must
	# carry the same id and the same bounds as the cell a generator emits later.
	var z_origin := float(row.get("z0", 0.0))
	print("bake: %s -- cell_deg=%.3f (%d cells round the ring), floor_r=%.2f m, "
		% [row["label"], cell_deg, int(row["cells"]), floor_r]
		+ "sight_line=%.1f m, kit cell=%d tri  [%s]"
		% [sight, int(row["cell_triangles"]), CELL_MANIFEST_PY])
	print("bake: budget cell_tris=%d resident_tris=%d -> %d cells resident  [%s]"
		% [bud["cell_tris"], bud["resident_tris"],
			int(bud["resident_tris"] / bud["cell_tris"]), BUDGET_PY])
	if z_band > 0.0:
		print("bake: z_band=%.1f m from deck_table.cell_length_m, grid anchored "
			% z_band + "at deck z0=%.0f -- a cell is %.1f m of arc by %.1f m of "
			% [z_origin, float(row["cell_length_m"]), z_band]
			+ "axis, square on the floor, and one free radius covers both")
	else:
		print("bake: z_band=0 -- ONE-DIMENSIONAL CONTROL. Every cell runs the "
			+ "deck's whole axial extent, which is the defect INV-610 records.")

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
	# The corridor width the manifest records, derived here rather than after
	# the fact, because `_axial_runs` uses it as its angular window.
	var corr_w := floor_r - sqrt(maxf(floor_r * floor_r
		- sight * sight / 4.0, 0.0))
	var corr := _corridor_z(col, corr_w)
	print("bake: corridor MEASURED at r=%.2f m, z=[%.2f,%.2f] (mid %.2f), "
		% [corr["r_floor_m"], corr["z0"], corr["z1"], corr["z_mid"]]
		+ "covering %.1f deg of arc -- the busiest of %d ring corridor(s) on "
		% [corr["arc_deg"], int(corr["runs"].size())]
		+ "this build")
	if corr["runs"].size() > 1:
		# NAMED, NOT AVERAGED. The first version of `_corridor_z` returned the
		# MIN-TO-MAX of every qualifying z bucket, which on a whole-deck build is
		# a point in the void between two clusters: on `blue_0_0` it reported
		# z_mid 7562.75, where only the 0.7 m-wide axial spine has floor, and
		# every one of the eighteen cell spawns was placed there -- seventeen of
		# them in mid-air, 440 m from the nearest corridor.
		print("bake: this deck has %d separate ring corridors, not one: %s"
			% [corr["runs"].size(), ", ".join(corr["runs_desc"])])
	var spine: Dictionary = corr["spine"]
	if not spine.is_empty():
		print("bake: axial spine MEASURED at %.3f deg (%.3f-%.3f, %.2f m wide), "
			% [spine["deg"], spine["deg0"], spine["deg1"], spine["width_m"]]
			+ "z=[%.1f,%.1f] -- %.1f m of floor in %d unbroken run(s). This is "
			% [spine["z0"], spine["z1"], spine["span_m"], int(spine["runs"])]
			+ "the only thing that joins one z-cluster to the next, and it is "
			+ "what --axial-gate walks.")
	var vis_bins := _split(vis, cell_deg, z_band, z_origin)
	var col_bins := _split(col, cell_deg, z_band, z_origin)
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
	# (arc, band) order, so the listing reads round the ring band by band and the
	# compact index below is arc-major -- which for a 1-D bake is the arc index
	# unchanged, byte for byte.
	idx.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return a.x < b.x if a.x != b.x else a.y < b.y)
	var band_lo := 0
	var band_hi := 0
	var first_key := true
	for k: Vector2i in idx:
		band_lo = k.y if first_key else mini(band_lo, k.y)
		band_hi = k.y if first_key else maxi(band_hi, k.y)
		first_key = false
	var n_band := band_hi - band_lo + 1
	var banded := z_band > 0.0
	var rows: Array = []
	var half_only: Array = []
	var no_floor := 0
	for k: Vector2i in idx:
		var i: int = k.x
		var bnd: int = k.y
		# ID FROM THE ABSOLUTE BAND, INDEX FROM THE COMPACT ONE. The id is the
		# durable name and has to be a property of the DECK grid, so it carries
		# the band counted from the deck's own z0 -- a partial build and a whole
		# one then name the same arc-and-band the same thing. `index` is only an
		# engine-local handle (`prime`, `cell_by_index`) and has to be unique and
		# small, so it is compacted. For a 1-D bake it is the arc index and the
		# id is the old one, unchanged.
		var cid := ("%s_c%02dz%02d" % [stem, i, bnd] if banded
			else "%s_c%02d" % [stem, i])
		var cix := (i * n_band + (bnd - band_lo) if banded else i)
		var have_v: bool = vis_bins.has(k)
		var have_c: bool = col_bins.has(k)
		var vpath := out_dir.path_join(cid + ".scn")
		var cpath := out_dir.path_join(cid + "_col.scn")
		var vinfo: Dictionary = ({} if not have_v
			else _write_cell(vis_bins[k], "cell_%02d_%02d" % [i, bnd], vpath))
		var cinfo: Dictionary = ({} if not have_c
			else _write_cell(col_bins[k], "cell_%02d_%02d_col" % [i, bnd], cpath))
		if (have_v and vinfo.is_empty()) or (have_c and cinfo.is_empty()):
			push_error("bake: could not write cell %s" % cid)
			return 2
		if not (have_v and have_c):
			half_only.append("%s %6.2f-%6.2f deg: %s (%d tri)"
				% [cid, i * cell_deg, (i + 1) * cell_deg,
					("NO COLLISION -- nothing to stand on there"
						if have_v else "NO RENDER MESH -- floor with no room"),
					int((vinfo if have_v else cinfo).get("tris", 0))])
		var aabb: AABB = (vinfo["aabb"] if have_v else cinfo["aabb"])
		if have_v and have_c:
			aabb = vinfo["aabb"].merge(cinfo["aabb"])
		# THE BAND BOUNDS ARE THE GRID, exactly as `a0_deg`/`a1_deg` are. The old
		# row took its z from the CONTENT and its angle from the GRID, which is
		# fine while every cell spans the deck and leaves a gap the moment they
		# do not: two axially adjacent cells whose content stops short of the
		# band edge would both be at a positive distance from a point between
		# them, so `cell_at` would report -1 for a place a body is standing.
		var bz0 := z_origin + float(bnd) * z_band
		var bz1 := bz0 + z_band
		var cz0 := snappedf(float((cinfo if have_c else vinfo)["zmin"]), 0.001)
		var cz1 := snappedf(float((cinfo if have_c else vinfo)["zmax"]), 0.001)
		# A spawn is a CLAIM -- see walk.gd. Measured off THIS CELL'S OWN floor,
		# never off a deck-wide corridor scan: see `_cell_spawn`.
		var sp := (_cell_spawn(col_bins[k], floor_r, 0.2) if have_c
			else PackedFloat64Array())
		if sp.is_empty():
			no_floor += 1
		rows.append({
			"id": cid,
			"index": cix,
			"arc_index": i,
			"z_band": bnd,
			"mesh": (vpath.get_file() if have_v else ""),
			"collision": (cpath.get_file() if have_c else ""),
			# THE ARC IS THE DISTANCE METRIC. A 20 deg cell's world AABB is a
			# 145 x 145 m box and a distance to it is nearly meaningless; the
			# distance a player actually has to walk is along the arc, and the
			# cell knows its own arc exactly. `distance_to` combines it with the
			# z overhang, which is what makes the axial half of the grid work
			# without a line of runtime change.
			"arc": {"r_m": floor_r, "a0_deg": i * cell_deg,
				"a1_deg": (i + 1) * cell_deg,
				"z0": (snappedf(bz0, 0.001) if banded else cz0),
				"z1": (snappedf(bz1, 0.001) if banded else cz1)},
			# What is actually IN the cell, kept beside the grid bounds so a
			# reader can see how much of its band a cell fills without reopening
			# the .scn.
			"content_z": [cz0, cz1],
			"aabb": {"pos": [aabb.position.x, aabb.position.y, aabb.position.z],
				"size": [aabb.size.x, aabb.size.y, aabb.size.z]},
			"tris": int(vinfo.get("tris", 0)),
			"col_tris": int(cinfo.get("tris", 0)),
			"groups": int(vinfo.get("groups", 0)),
			"spawn": ([] if sp.is_empty() else [sp[0], sp[1], sp[2]]),
			"spawn_from": ("" if sp.is_empty() else
				("deck floor r=%.2f" % floor_r if sp[3] > 0.5
					else "this cell's outermost collision, r=%.2f" % sp[4])),
		})
		if rows.size() <= 64 or not banded:
			print("  %-24s %6.2f-%6.2f deg  z %8.1f-%8.1f  %7d tri  %5d col  "
				% [cid, i * cell_deg, (i + 1) * cell_deg, bz0, bz1,
					int(vinfo.get("tris", 0)), int(cinfo.get("tris", 0))]
				+ "%3d grp %5.1f MB%s"
				% [int(vinfo.get("groups", 0)),
					_file_mb(vpath) + _file_mb(cpath),
					("" if have_v and have_c
						else ("   NO COLLISION" if have_v
							else "   NO RENDER MESH"))])
		elif rows.size() == 65:
			print("  ... %d more cells, listed in the manifest" % (idx.size() - 64))

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
		# THE SECOND AXIS OF THE GRID. Zero means the one-dimensional control --
		# see the header. `z_origin_m` is the deck's own z0, so a band index is a
		# property of the deck and not of this build's extent.
		"z_band_m": z_band,
		"z_origin_m": z_origin,
		"z_bands": n_band,
		"z_band_from": ("deck_table.cell_length_m (%.1f m) -- the arc cell "
			% float(row["cell_length_m"])
			+ "length, so one free radius is valid along both axes and a cell "
			+ "is square on the floor. INV-610. Along the axis the residency "
			+ "radius is a BUDGET bound, not the ring-curvature occlusion bound "
			+ "it is around the arc: INV-611."
			if z_band > 0.0 else "0 -- the one-dimensional control, INV-610"),
		# The corridor's own measured position, so a caller that wants to walk
		# ALONG the run -- rather than into a room -- does not have to guess.
		"corridor": {"r_floor_m": snappedf(float(corr["r_floor_m"]), 0.001),
			"z0": corr["z0"], "z1": corr["z1"],
			"z_mid": corr["z_mid"], "arc_deg": snappedf(float(corr["arc_deg"]), 0.1),
			# EVERY ring corridor on this build, not just the busiest, and the
			# axial spine that threads them. A whole-deck build has several and
			# the old record could only describe one -- by taking min-to-max
			# across all of them, which lands in the void between.
			"runs": corr["runs"],
			"spine": corr["spine"],
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
	print("bake: %d cells (%d arc x %d band), %d triangles total (source had "
		% [rows.size(), int(row["cells"]), n_band, tot]
		+ "%d), %.1f MB, %d ms -> %s"
		% [_mesh_tris(vis), _dir_mb(out_dir), Time.get_ticks_msec() - t0, mpath])
	# THE NUMBER THE BUDGET IS ABOUT. A grid that has no axis in the direction
	# the station is long produces cells nothing can afford, and until this line
	# existed the bake reported a total and never a maximum -- so an 18-cell bake
	# whose biggest cell was 3.24x the WHOLE resident allowance printed as a
	# success. Reported here, where it is measured, rather than left to the
	# runtime's `over_budget_frames` to discover on a player's machine.
	var big := 0
	var big_id := ""
	var over := 0
	for r in rows:
		if int(r["tris"]) > big:
			big = int(r["tris"])
			big_id = String(r["id"])
		if int(r["tris"]) > int(bud["cell_tris"]):
			over += 1
	print("bake: biggest cell %s at %d tri = %.2fx cell_tris and %.2fx the "
		% [big_id, big, float(big) / maxf(float(bud["cell_tris"]), 1.0),
			float(big) / maxf(float(bud["resident_tris"]), 1.0)]
		+ "WHOLE resident budget; %d of %d cells over cell_tris"
		% [over, rows.size()])
	if no_floor > 0:
		print("bake: %d of %d cells have no floor and therefore no spawn -- "
			% [no_floor, rows.size()]
			+ "stated rather than given a made-up point, which is what placing "
			+ "every spawn at a deck-wide z_mid did")
	if not half_only.is_empty():
		# NAMED, NOT COUNTED. A conservation failure with a total and no location
		# is a diagnosis pass nobody can start; these are the arcs where the two
		# halves of the deck disagree about what exists.
		print("bake: %d cell(s) have only one half:" % half_only.size())
		for s in half_only.slice(0, 24):
			print("        " + s)
		if half_only.size() > 24:
			print("        ... %d more" % (half_only.size() - 24))
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
## Returns {Vector2i(arc, band): {group_name: [pos, nrm, uv]}}.
##
## TWO AXES SINCE 4r, AND THE SECOND ONE IS WHY THE STATION WAS ONE Z-CLUSTER.
## `z_band <= 0` bins everything into band 0, which is the old behaviour exactly
## and is the control. See the header.
func _split(root: Node, cell_deg: float, z_band: float = 0.0,
		z_origin: float = 0.0) -> Dictionary:
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
				var cz: float = (p0.z + p1.z + p2.z) / 3.0
				var cell := Vector2i(int(floor(a / cell_deg)),
					(0 if z_band <= 0.0
						else int(floor((cz - z_origin) / z_band))))
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
## AND A WHOLE-DECK BUILD HAS SEVERAL CORRIDORS, WHICH MIN-TO-MAX CANNOT SAY.
## The first version returned the min and max of every QUALIFYING z bucket, on
## the assumption that a build holds one ring corridor. `tools/bake_station.py`
## bakes the whole deck, and `blue_0_0` holds five -- z 6900 covering 164 deg of
## arc, 7120 covering 345, 7460 covering 206, 7960 covering 225 and 8000
## covering 360. Min-to-max over those is z [7121, 8004.5], mid **7562.75**,
## which is 440 m of vacuum: the only floor at that z is the 0.7 m-wide axial
## spine. Every one of that bake's eighteen cell spawns was placed there.
## Qualifying buckets are therefore grouped into CONTIGUOUS RUNS, the busiest
## run is the answer, and all of them are reported.
func _corridor_z(col_root: Node, win_m: float = 2.6) -> Dictionary:
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
				var zlo_t := INF
				var zhi_t := -INF
				for k in 3:
					var i := (ix[t * 3 + k] if ix.size() > 0 else t * 3 + k)
					var w: Vector3 = xf * pos[i]
					q += w
					zlo_t = minf(zlo_t, w.z)
					zhi_t = maxf(zhi_t, w.z)
				q /= 3.0
				var r := sqrt(q.x * q.x + q.y * q.y)
				rmax = maxf(rmax, r)
				var a := rad_to_deg(atan2(q.y, q.x))
				tri.append([r, (a + 360.0 if a < 0.0 else a), q.z, zlo_t, zhi_t])
	var floor_tri: Array = []
	for e in tri:
		if e[0] >= rmax - 0.1:
			floor_tri.append(e)
	var span := {}
	var mass := {}
	for e in floor_tri:
		var b := int(round(e[2] * 2.0))           # 0.5 m buckets
		if not span.has(b):
			span[b] = {}
			mass[b] = 0
		span[b][int(floor(e[1]))] = true          # one-degree bins
		mass[b] += 1
	var best := 0
	for b in span:
		best = maxi(best, span[b].size())
	var keep := {}
	for b in span:
		if span[b].size() >= int(ceil(float(best) * 0.95)):
			keep[b] = true
	# ONE CORRIDOR IS ONE RUN, AND CONTIGUITY IS THE TRIANGLES' OWN Z EXTENTS
	# rather than adjacency of centroid buckets. The first version of this used
	# adjacent 0.5 m buckets and split THIS DECK'S single corridor in two: its
	# floor is a handful of large triangles spanning z 7185.7-7188.3, whose
	# centroids land in the 7186.0 and 7187.0 buckets with nothing in 7186.5, so
	# a bucket-adjacency test reported "2 separate ring corridors" 1.0 m apart.
	# Merging the intervals themselves needs no tolerance to argue about --
	# `_axial_runs` uses the identical rule -- and gives one run.
	var iv: Array = []
	for e in floor_tri:
		if keep.has(int(round(float(e[2]) * 2.0))):
			iv.append(e)
	iv.sort_custom(func(a: Array, b: Array) -> bool: return a[3] < b[3])
	var runs: Array = []
	var desc: PackedStringArray = PackedStringArray()
	var cur: Array = []
	var hi := -INF
	for e in iv:
		if not cur.is_empty() and float(e[3]) > hi + 0.05:
			runs.append(_run_of(cur))
			cur = []
			hi = -INF
		cur.append(e)
		hi = maxf(hi, float(e[4]))
	if not cur.is_empty():
		runs.append(_run_of(cur))
	var pick := 0
	for i in runs.size():
		var r: Dictionary = runs[i]
		var p: Dictionary = runs[pick]
		if (float(r["arc_deg"]) > float(p["arc_deg"])
				or (float(r["arc_deg"]) == float(p["arc_deg"])
					and int(r["tris"]) > int(p["tris"]))):
			pick = i
	for r in runs:
		desc.append("z %.1f-%.1f (%d deg)" % [r["z0"], r["z1"], int(r["arc_deg"])])
	if runs.is_empty():
		return {"r_floor_m": rmax, "z0": INF, "z1": -INF, "z_mid": 0.0,
			"arc_deg": 0.0, "runs": [], "runs_desc": desc,
			"spine": _axial_runs(floor_tri, [], rmax, win_m)}
	var win: Dictionary = runs[pick]
	return {"r_floor_m": rmax, "z0": win["z0"], "z1": win["z1"],
		"z_mid": (float(win["z0"]) + float(win["z1"])) * 0.5,
		"arc_deg": float(win["arc_deg"]), "runs": runs, "runs_desc": desc,
		"spine": _axial_runs(floor_tri, runs, rmax, win_m)}


## One ring corridor, described from the floor triangles that make it up.
## `arc_deg` is the number of distinct one-degree bins it occupies -- COVERAGE,
## not spread, which is the distinction `_corridor_z`'s header records.
func _run_of(tri: Array) -> Dictionary:
	var bins := {}
	var lo := INF
	var hi := -INF
	for e in tri:
		bins[int(floor(float(e[1])))] = true
		lo = minf(lo, float(e[3]))
		hi = maxf(hi, float(e[4]))
	return {"z0": snappedf(lo, 0.001), "z1": snappedf(hi, 0.001),
		"arc_deg": float(bins.size()), "tris": tri.size()}


## THE TRANSPOSE OF `_corridor_z`, AND IT IS WHAT THE AXIAL GRID NEEDED.
##
## `_corridor_z` asks "which z carries the most arc" and finds a ring corridor.
## Ask the same question the other way round -- which ANGLE carries the most z --
## and you find the axial spine, the thing that joins one ring corridor to the
## next and the only reason a body can leave its own z-cluster on foot. Measured
## with the triangles' OWN z ranges merged, not their centroids, so contiguity
## needs no tolerance to argue about: triangles that touch are one run.
##
## On `blue_0_0`'s whole-deck build exactly ONE bin of 360 carries more than
## 300 m of floor, and it carries 1,101.9 m of it in a SINGLE unbroken run.
func _axial_runs(floor_tri: Array, corridors: Array, rmax: float,
		win_m: float = 2.6) -> Dictionary:
	# THE SPAN COMES FROM ALL THE FLOOR AND THE ANGLE COMES FROM THE SPINE ONLY,
	# and both halves of that were got wrong once. Measuring the span over the
	# corridor-excluded set splits the spine at every ring corridor it threads
	# and reports "1,085.9 m in 3 runs" for something continuous. Measuring the
	# ANGLE over everything, or over the winning bin and its neighbours, drags
	# in the ring corridors -- which cross every bin -- and the room floors
	# either side: the first version returned the BIN centre, 89.5 deg, for a
	# spine whose own edge is at 89.46, so the gate aimed 0.15 m outside the
	# floor it was walking on and stalled against the wall after 0.7 m.
	var by_deg := {}
	for e in floor_tri:
		var d := int(floor(float(e[1])))
		if not by_deg.has(d):
			by_deg[d] = []
		by_deg[d].append([float(e[3]), float(e[4]), float(e[1])])
	var best_deg := -1
	var best_span := 0.0
	var best_runs := 0
	var best_z0 := 0.0
	var best_z1 := 0.0
	for d in by_deg:
		var iv: Array = by_deg[d]
		iv.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
		var total := 0.0
		var n := 0
		var lo: float = iv[0][0]
		var hi: float = iv[0][1]
		var z0: float = iv[0][0]
		var z1: float = iv[iv.size() - 1][1]
		for k in range(1, iv.size()):
			if iv[k][0] <= hi + 0.05:
				hi = maxf(hi, iv[k][1])
			else:
				total += hi - lo
				n += 1
				lo = iv[k][0]
				hi = iv[k][1]
		total += hi - lo
		n += 1
		if total > best_span:
			best_span = total
			best_deg = d
			best_runs = n
			best_z0 = z0
			best_z1 = z1
	if best_deg < 0:
		return {}
	# THE ANGLE, from the winning bin's own triangles with the ring corridors cut
	# out. The MEDIAN first, because it is decided by mass and the spine is a
	# thousand metres of floor against a room's few: any stray floor at this
	# angle is outvoted rather than averaged in. Then the extent of everything
	# within ONE CORRIDOR WIDTH of it -- `win_m` is
	# `floor_r - sqrt(floor_r^2 - sight^2/4)`, the width the manifest already
	# records, so the window is a number this deck derived and not one chosen
	# here.
	var ang: Array = []
	for e in by_deg[best_deg]:
		var inside := false
		for c in corridors:
			if float(e[1]) >= float(c["z0"]) - 0.05 \
					and float(e[0]) <= float(c["z1"]) + 0.05:
				inside = true
				break
		if not inside:
			ang.append(float(e[2]))
	if ang.is_empty():
		for e in by_deg[best_deg]:      # a single-corridor build: nothing to cut
			ang.append(float(e[2]))
	ang.sort()
	var med: float = ang[ang.size() / 2]
	var win_deg := rad_to_deg(win_m / maxf(rmax, 1.0))
	# MEDIAN TO FIND IT, MEAN TO CENTRE ON IT. Measured on this deck, bin 89
	# holds 575 floor triangles: **550 of them are the spine**, in two strips of
	# 275 at 89.07 and 89.26 deg each running z 6905.7-8003.2, and the other 25
	# are singletons of room floor scattered from 89.04 to 89.93. The median is
	# decided by that mass and lands on the spine; the EXTENT of what survives
	# the window is not, because one stray triangle at 89.93 drags its midpoint
	# to 89.49 -- which is 0.03 deg past the spine's own far edge, so the gate
	# walked half off it. The mean is mass-weighted like the median and lands at
	# 89.19 against a true centre of 89.17.
	var lo_a := INF
	var hi_a := -INF
	var acc := 0.0
	var n_in := 0
	for a in ang:
		if absf(float(a) - med) <= win_deg:
			lo_a = minf(lo_a, float(a))
			hi_a = maxf(hi_a, float(a))
			acc += float(a)
			n_in += 1
	# `deg0`/`deg1`/`width_m` are the ENVELOPE of everything inside the window,
	# strays included, and are measured off triangle CENTROIDS -- so the envelope
	# is wider than the spine and the centroid extent of the spine itself is
	# narrower than its true width by about one triangle. They are here to say
	# roughly what is around, not as a dimension anything is built to. `deg` is
	# the number to walk at.
	return {"deg": snappedf(acc / maxf(float(n_in), 1.0), 0.001),
		"deg0": snappedf(lo_a, 0.001), "deg1": snappedf(hi_a, 0.001),
		"width_m": snappedf(deg_to_rad(hi_a - lo_a) * rmax, 0.01),
		"floor_tris": ang.size(),
		"z0": snappedf(best_z0, 0.01),
		"z1": snappedf(best_z1, 0.01), "span_m": snappedf(best_span, 0.01),
		"runs": best_runs}


## A SPAWN MEASURED OFF THE CELL'S OWN FLOOR. Returns
## [x, y, z, on_deck_floor, r] or empty.
##
## `boot.py::spawn_from_shell`'s rule, one level down and per cell: a point ON a
## floor triangle cannot be in the air, and the centroid of an arc is not on the
## arc. It takes this cell's collision triangles at the DECK's floor radius --
## a spun deck's floor is its outermost surface -- and returns the one nearest
## the cell's own centre, moved `up_m` inward, because on a spun ring up is
## inward. Where a cell has no floor at the deck radius (a mezzanine, a duct
## run) it falls back to that cell's own outermost triangle and SAYS SO in the
## row; where it has no collision at all it returns empty and the row carries no
## spawn, which is the honest answer and the one the old code could not give.
func _cell_spawn(groups: Dictionary, floor_r: float,
		up_m: float) -> PackedFloat64Array:
	var band := 0.15                     # `boot.FLOOR_BAND_M`, same rule
	var best := Vector3.ZERO
	var best_r := 0.0
	var on_deck := false
	var sum := Vector3.ZERO
	var n := 0
	var cands: Array = []
	for name in groups:
		var pos: PackedVector3Array = groups[name][0]
		for t in pos.size() / 3:
			var c: Vector3 = (pos[t * 3] + pos[t * 3 + 1] + pos[t * 3 + 2]) / 3.0
			var r := sqrt(c.x * c.x + c.y * c.y)
			cands.append([r, c])
			sum += c
			n += 1
			best_r = maxf(best_r, r)
	if n == 0:
		return PackedFloat64Array()
	var mid := sum / float(n)
	var want := (floor_r if best_r >= floor_r - band else best_r)
	on_deck = best_r >= floor_r - band
	var have := false
	var bd := INF
	for e in cands:
		if want - float(e[0]) > band:
			continue
		var d: float = (e[1] as Vector3).distance_squared_to(mid)
		if d < bd:
			bd = d
			best = e[1]
			have = true
	if not have:
		return PackedFloat64Array()
	var rr := sqrt(best.x * best.x + best.y * best.y)
	var k := (rr - up_m) / maxf(rr, 1e-9)
	return PackedFloat64Array([best.x * k, best.y * k, best.z,
		(1.0 if on_deck else 0.0), rr])


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


# ===========================================================================
# THE AXIAL GATE -- a body walks OUT OF ITS OWN Z-CLUSTER AND BACK
# ===========================================================================
#
# WHY THIS EXISTS AND WHY IT IS HERE. `walk.gd::--stream-test` walks a body
# round the ARC and is the gate for arc hand-off; there has never been one for
# the other axis, and `docs/MASTER-PLAN.md` P0.5 recorded the gap as
# "cluster-to-cluster hand-off untested". It was worse than untested: with a
# one-dimensional grid a cell ran the deck's whole 1,253 m of axis, so the
# traverse that was supposed to exercise the hand-off never crossed a boundary
# and could not fail. A gate that cannot fail is this project's most expensive
# recurring defect and the header records the measurement.
#
# IT WALKS THE SPINE THE BAKE MEASURED, not a route written down here. On
# `blue_0_0` that is 89.5 deg, the one bin of 360 whose floor spans more than
# 300 m -- and it is what physically joins the docking bays at z 7121 to customs
# at z 7460. Nothing in this function knows those numbers; they come out of
# `plan.corridor.spine`.
#
# AND IT REPORTS METRES ON THE FLOOR. `station/collision.py`'s rule: four nudges
# prove a body is not wedged and prove nothing about whether you can go
# anywhere. `floor_m` counts only steps taken with `is_on_floor()` true, so a
# body that walks off the end of a cell and falls 300 m scores nothing for it.
#
# THE CONTROLS, and both must fail:
#   --z-band=0 at bake time  -> one 1.1 km cell, `loads=0 frees=0` over the same
#                               traverse, and this gate fails on `crossings`.
#   --no-stream              -> the start cell is primed and nothing else is ever
#                               requested; the body walks off the end of it.

const G0_M_S2 := 9.80665           ## walk.gd's own constant, same conversion

var _ax := {}                      ## the gate's state, empty when not gating


func _ready() -> void:
	# ONLY WHEN THIS NODE IS THE SCENE. `walk.gd::_ready` adds a bare instance of
	# this script as a CHILD for `--bake-cells` and for one deck-table read, and
	# both must be untouched by anything here -- so the guard is parentage, which
	# cannot be true by accident, rather than a flag somebody has to remember not
	# to pass. `res://scenes/stream_gate.tscn` is the one scene whose root this is.
	set_physics_process(false)
	if get_parent() != get_tree().root:
		return
	var args := _cmdline()
	if not args.has("axial-gate"):
		return
	var rc := _ax_setup(args)
	if rc != 0:
		get_tree().quit(rc)
		return
	set_physics_process(true)


func _cmdline() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if not s.begins_with("--"):
			continue
		s = s.substr(2)
		var eq := s.find("=")
		if eq < 0:
			out[s] = ""
		else:
			out[s.substr(0, eq)] = s.substr(eq + 1)
	return out


func _ax_setup(args: Dictionary) -> int:
	var man_p := String(args.get("cells", ""))
	if man_p == "":
		push_error("axial-gate: --cells=<...cells.json> is required")
		return 2
	if not configure(man_p, null, 3.0, args.has("no-stream")):
		push_error("axial-gate: " + ", ".join(problems))
		return 2
	var spine: Dictionary = (plan.get("corridor", {}) as Dictionary).get(
		"spine", {})
	if spine.is_empty():
		push_error("axial-gate: this manifest carries no measured spine -- it "
			+ "was baked before INV-612. Re-bake it.")
		return 2
	var floor_r := float(plan.get("floor_r_m", 0.0))
	# GRAVITY FROM THE DECK THE BODY IS ON, never Earth's. INV-451's rule: the
	# only caller that supplied the real values used to be the gate they were
	# authored in, so they are derived here from `cell_manifest.json`'s own
	# floor_g/floor_r pair -- the same two numbers `walk.gd::_derive_omega2`
	# uses, read through the same `deck_row`.
	var src: Dictionary = plan.get("source", {})
	var row := deck_row(String(src.get("sector", "")),
		int(src.get("ring_index", 0)), int(src.get("deck_index", 0)))
	var om2 := 0.0
	if not row.is_empty() and float(row.get("floor_r_m", 0.0)) > 0.0:
		om2 = G0_M_S2 * float(row["floor_g"]) / float(row["floor_r_m"])

	var deg := float(args.get("deg", str(spine["deg"])))
	# START AND END ON THE SPINE. Default: from the busiest ring corridor's z --
	# the cluster a boot spawn lands in -- to the far end of the spine, which is
	# the last z-cluster on the deck. Both overridable so a caller can name two
	# clusters by their z.
	var corr: Dictionary = plan.get("corridor", {})
	var z_a := float(args.get("from-z", str(corr.get("z_mid", spine["z0"]))))
	# THE FAR END IS THE FURTHEST RING CORRIDOR, not `spine.z1`. A default of
	# "the high end of the spine" walked 1.1 m on this deck, because the busiest
	# corridor happens to sit AT the spine's high end -- a default that silently
	# does nothing is the same defect as a gate that cannot fail. So: the other
	# cluster's own corridor if this build has more than one, and otherwise
	# whichever end of the spine is further from where the body starts.
	var z_b: float = (float(spine["z0"]) if absf(float(spine["z0"]) - z_a)
		> absf(float(spine["z1"]) - z_a) else float(spine["z1"]))
	for r in (corr.get("runs", []) as Array):
		var mid: float = (float(r["z0"]) + float(r["z1"])) * 0.5
		if absf(mid - z_a) > absf(z_b - z_a):
			z_b = mid
	z_b = float(args.get("to-z", str(z_b)))
	var a := deg_to_rad(deg)
	var r := floor_r - 0.2
	var start := Vector3(r * cos(a), r * sin(a), z_a)
	var start_cell := cell_at(start)
	if start_cell < 0:
		push_error("axial-gate: the start point %.1f,%.1f,%.1f is in no cell"
			% [start.x, start.y, start.z])
		return 2
	var ms := prime(start_cell)

	var body := CharacterBody3D.new()
	body.name = "AxialBody"
	body.set_script(load("res://scripts/player.gd"))
	body.set("gravity_mode", "drum")
	body.set("omega2", om2)
	const Ragdoll := preload("res://scripts/ragdoll.gd")
	body.collision_layer = Ragdoll.WORLD_LAYER
	body.collision_mask = Ragdoll.WORLD_LAYER
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	# 1.8 x 0.35 -- `walk.gd::_cap_h/_cap_r`, the same person.
	caps.height = 1.8
	caps.radius = 0.35
	shape.shape = caps
	shape.position = Vector3(0, 0.9, 0)
	body.add_child(shape)
	add_child(body)
	body.drive_externally()
	body.global_position = start
	# UPRIGHT BEFORE THE FIRST STEP, THROUGH `player.gd`'s OWN CONSTRUCTOR.
	# `step` sets `global_transform.basis = stand_basis(fwd)` every frame, so the
	# body is upright from frame 1 -- but it is placed on frame 0 with an
	# IDENTITY basis, which on a ring at 89 deg points the capsule's local +Y
	# very nearly along the outward radius: 1.8 m of body buried in the deck,
	# resolved by whatever `move_and_slide` does about it on the next frame.
	# `stand_basis` is the one construction site for this expression -- see its
	# own header -- so this calls it rather than rebuilding the basis here,
	# which is CLAUDE.md's mirrored-crowd lesson applied before it can happen.
	body.global_transform.basis = body.stand_basis(Vector3(0, 0, 1))
	set_player(body)
	_ax = {
		"body": body, "deg": deg, "r": r, "z_a": z_a, "z_b": z_b,
		"dir": 1.0, "frame": 0, "floor_m": 0.0, "off": 0, "legs": 0,
		"prev": start, "start_cell": start_cell, "prime_ms": ms,
		"max_frames": int(args.get("frames", "24000")),
		"reach_m": float(args.get("reach", "3.0")),
		"seen": {}, "crossings": 0, "here": start_cell, "far_z": z_a,
		"trace": int(args.get("trace", "0")),
		# A BLOCKED BODY MUST REPORT, NOT HANG. The first run of this gate sat at
		# z 7185.75 for 6,000 frames with `on_floor=true`, which is a real and
		# interesting answer -- the route out of the ring corridor into the room
		# runs through a pressure door, and `_wiring` is null in this gate so the
		# leaf is a solid trimesh. A frame cap alone reports that as "did not get
		# there", which is true and says nothing about why. Progress is measured
		# toward the goal and stalling is named with the position and the cell.
		"stall": int(args.get("stall", "900")),
		"best": absf(z_b - z_a), "since": 0, "blocked": "",
		"landed": false, "settle_frames": 0,
	}
	print("axial-gate: spine %.2f deg (%.1f m of floor in %d run(s), z %.1f-%.1f)"
		% [deg, float(spine["span_m"]), int(spine["runs"]), float(spine["z0"]),
			float(spine["z1"])]
		+ ", walking z %.1f -> %.1f -> %.1f at r=%.2f" % [z_a, z_b, z_a, r])
	print("axial-gate: gravity omega^2=%.9f -> %.4f m/s^2 at r=%.2f (deck row "
		% [om2, om2 * floor_r, floor_r] + "%s), start cell %d primed in %d ms"
		% [String(row.get("id", "?")), start_cell, ms])
	return 0


func _physics_process(delta: float) -> void:
	if _ax.is_empty():
		return
	var body: CharacterBody3D = _ax["body"]
	var p := body.global_position
	# STEER ALONG THE SPINE AND NOWHERE ELSE. The spine is 2.16 m wide on this
	# deck, so the target is the point on it a few metres ahead: any component
	# round the ring walks the body straight off it. `player.gd::step` flattens
	# the direction onto the floor plane, which on a spun ring is the tangent
	# plane at the body's own angle, so a pure +z steer stays a pure +z walk.
	var a := deg_to_rad(float(_ax["deg"]))
	var rr: float = _ax["r"]
	var goal: float = (_ax["z_b"] if _ax["dir"] > 0.0 else _ax["z_a"])
	var ahead: float = p.z + _ax["dir"] * 5.0
	if _ax["dir"] > 0.0:
		ahead = minf(ahead, goal)
	else:
		ahead = maxf(ahead, goal)
	var target := Vector3(rr * cos(a), rr * sin(a), ahead)
	body.step(delta, Vector2.ZERO, false, false, target - p)
	update(body.global_position)

	var q := body.global_position
	var d := q.distance_to(_ax["prev"])
	# THE WALK BEGINS WHEN THE BODY IS STANDING. It is placed 0.2 m off its own
	# floor triangle -- `boot.STAND_IN_M`'s convention, so the settle either
	# confirms the spawn or does not -- and at this deck's 7.455 m/s^2 that drop
	# takes sqrt(2*0.2/7.455) = 0.23 s, which is the 12 off-floor frames the
	# first passing run reported and failed itself on. Not a derived frame count
	# (`walk.gd::--settle` uses 120 and would also have hidden a real fall):
	# nothing is measured until `is_on_floor()` is true once, so the rule needs
	# no number and a body that NEVER lands still fails, on `legs`.
	if not bool(_ax["landed"]):
		if not body.is_on_floor():
			_ax["prev"] = q
			_ax["frame"] = int(_ax["frame"]) + 1
			if int(_ax["frame"]) >= int(_ax["max_frames"]):
				_ax_finish()
			return
		_ax["landed"] = true
		_ax["settle_frames"] = int(_ax["frame"])
		_ax["prev"] = q
	if body.is_on_floor():
		_ax["floor_m"] = float(_ax["floor_m"]) + d
		if _ax["dir"] > 0.0:
			_ax["far_z"] = maxf(float(_ax["far_z"]), q.z)
	else:
		_ax["off"] = int(_ax["off"]) + 1
	_ax["prev"] = q
	_ax["frame"] = int(_ax["frame"]) + 1
	# HOW MANY CELL BOUNDARIES THE BODY ACTUALLY CROSSED, watched from OUTSIDE
	# the streamer's own counters -- `walk.gd::_note_residency`'s rule. A
	# streamer that lied about `loads` could not make this number move.
	var now := cell_at(q)
	if now >= 0:
		_ax["seen"][now] = true
		if now != int(_ax["here"]):
			_ax["crossings"] = int(_ax["crossings"]) + 1
			_ax["here"] = now
	if int(_ax["trace"]) > 0 and int(_ax["frame"]) % int(_ax["trace"]) == 0:
		print("  f%-6d z=%9.2f  cell %3d  resident %d (%d tri)  on_floor=%s"
			% [int(_ax["frame"]), q.z, now, _resident.size(), resident_tris(),
				str(body.is_on_floor())])

	var left := absf(q.z - goal)
	if left < float(_ax["best"]) - 0.5:
		_ax["best"] = left
		_ax["since"] = 0
	else:
		_ax["since"] = int(_ax["since"]) + 1
		if int(_ax["since"]) >= int(_ax["stall"]):
			_ax["blocked"] = ("stalled %d frames at z=%.2f (%.1f m short of "
				% [int(_ax["since"]), q.z, left]
				+ "z=%.1f) in cell %d, on_floor=%s -- something solid is in the "
				% [goal, now, str(body.is_on_floor())]
				+ "way, not a missing cell")
			_ax_finish()
			return
	if left <= float(_ax["reach_m"]):
		if _ax["dir"] > 0.0:
			_ax["dir"] = -1.0
			_ax["legs"] = 1
			# RESET THE PROGRESS BASELINE AT THE TURN, and the first version did
			# not. `best` is distance remaining to the CURRENT goal; at the turn
			# the goal changes from z_b to z_a, so the remaining distance jumps
			# from ~0 to the full 340 m and never beats a baseline set on the
			# outbound leg. The detector fired 900 frames later with the body
			# 62.7 m further back than the turn -- 62.7 m in 900 frames is
			# 4.18 m/s, which is `player.gd`'s own 4.2 m/s walk. A gate that
			# fails for its own bookkeeping is worse than one that cannot fail,
			# because it reads as a finding.
			_ax["best"] = absf(q.z - float(_ax["z_a"]))
			_ax["since"] = 0
			print("axial-gate: reached z=%.2f at frame %d -- turning back"
				% [q.z, int(_ax["frame"])])
			return
		_ax["legs"] = 2
		_ax_finish()
		return
	if int(_ax["frame"]) >= int(_ax["max_frames"]):
		_ax_finish()


func _ax_finish() -> void:
	var body: CharacterBody3D = _ax["body"]
	var q := body.global_position
	var reached: float = float(_ax["far_z"])
	var want: float = float(_ax["z_b"])
	var travelled: float = absf(reached - float(_ax["z_a"]))
	var line := ("AXIALWALK legs=%d floor_m=%.1f axial_m=%.1f reached_z=%.1f "
		+ "target_z=%.1f offfloor=%d/%d settle=%d cells_entered=%d "
		+ "crossings=%d %s") % [
		int(_ax["legs"]), float(_ax["floor_m"]), travelled, reached, want,
		int(_ax["off"]), int(_ax["frame"]), int(_ax["settle_frames"]),
		(_ax["seen"] as Dictionary).size(), int(_ax["crossings"]), report()]
	print(line)
	var bad: PackedStringArray = PackedStringArray()
	if String(_ax["blocked"]) != "":
		bad.append(String(_ax["blocked"]))
	if int(_ax["legs"]) < 2:
		bad.append("the body did not get there and back (legs=%d, stopped at "
			% int(_ax["legs"]) + "z=%.1f of %.1f)" % [q.z, want])
	if int(_ax["crossings"]) < 2:
		bad.append("it crossed %d cell boundaries -- a traverse inside one "
			% int(_ax["crossings"]) + "cell tests no hand-off at all")
	if loads < 1 or frees < 1:
		bad.append("loads=%d frees=%d -- nothing arrived or nothing left"
			% [loads, frees])
	if int(_ax["off"]) > 0:
		bad.append("%d frame(s) off the floor" % int(_ax["off"]))
	if peak_tris > resident_tris_budget:
		bad.append("peak resident %d tri against a %d budget (%.2fx)"
			% [peak_tris, resident_tris_budget,
				float(peak_tris) / maxf(float(resident_tris_budget), 1.0)])
	if bad.is_empty():
		print("axial-gate: PASS -- a body left its own z-cluster on foot and "
			+ "came back, with cells arriving and being released as it went")
	else:
		print("axial-gate: FAIL -- " + "; ".join(bad))
	get_tree().quit(0 if bad.is_empty() else 1)
