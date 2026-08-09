extends Node3D
const Interact = preload("res://scripts/interact.gd")
## Pressure doors that open when somebody comes to them, and are solid when shut.
##
## THE MESH NAME ARRIVES z-PREFIXED AND THIS FILE READ IT RAW, so it wired ZERO
## doors on every build that has ever shipped. The generator names a mesh
## `z7120__doorleaf_docking_bays_0`; `begins_with("doorleaf_")` is false for all
## 46 door meshes on blue_0_0, and for every one of the 907 streamed cells. The
## committed launch logs say so in one line -- `walk: 0 doors wired`, in both
## dist/firstrun.log and dist/sourcerun.log -- and nobody read it.
##
## `interact.gd::strip_cluster` is the fix and it already existed. Its own
## docstring says stripping belongs "at the one place a mesh name meets a
## declared name, rather than at each of the three call sites -- this project's
## own rule that a fix applied to an instance and not the rule will be needed
## again." It was applied to `interact.gd` and not to `door.gd`, one file away.
## That is the ninth instance of this project's recurring defect and the first
## one a PLAYER would have met: every named room on the station was sealed, and
## the objective the game hands you on NEW GAME is on the far side of a door.
##
## THE FIRST THING A PLAYER USES. Until this existed the station had doors that
## were pictures of doors: the collision shell cut a permanent hole at every
## doorway -- which is what let a body walk from the corridor into a room -- and
## the leaves the player could SEE were a closed slab baked into the corridor
## mesh. So you walked through a shut door. Physics and pixels disagreeing about
## whether there is a wall is the same defect this project has now hit three
## times, and this is the one a player meets first.
##
## WHAT IT NEEDS FROM THE GENERATOR, and it is all self-describing rather than a
## table that can drift:
##
##   doorleaf_<key>_0  the two moving leaves, each its OWN mesh, because they
##   doorleaf_<key>_1  travel in opposite directions
##   doorpanel_<key>   the solid the closed door is, in the collision shell,
##                     as its own group so exactly it can be switched off
##
## Which way a leaf travels is read off the geometry: away from the midpoint of
## the pair. Nothing has to say "left" and "right", so nothing can say it wrong.
##
## AND IT NOW HAS TO SURVIVE THE GEOMETRY ARRIVING AND LEAVING. `walk.gd` used to
## call `collect()` once over a monolithic glb, so a door was a thing that
## existed for the life of the process. With `scripts/stream.gd` the leaves and
## the panel arrive with their cell and are freed with it, and this file has to
## be told both times or it holds references into a scene that has been
## `queue_free`d.
##
## THE TWO HALVES OF ONE DOOR CAN ARRIVE IN DIFFERENT CELLS, and that is not a
## corner case: the bake bins each TRIANGLE by its own centroid, so a door
## sitting on a cell boundary has its leaves in one cell and its panel in the
## next. A door assembled per cell would then be a door with no panel to switch
## off -- visibly open and physically solid, the exact defect this file exists to
## end. So leaves and panels are registered per cell into per-KEY buckets and the
## door list is rebuilt from every resident cell at once.
##
## A DOOR WHOSE LEAF SET CHANGES IS RESET TO SHUT, because a re-instanced cell
## brings its leaves back at their baked closed positions and its panel back with
## the collider ENABLED. Carrying an openness across that would leave a door
## drawn half open with a solid panel in it.

## How close a body has to be for the door to notice. A pressure door opens as
## you reach it, not across the room.
@export var open_range_m: float = 2.6
## Metres per second the leaves travel. A pressure door is heavy.
@export var speed_m_s: float = 1.6

var _doors: Array = []
var _body: Node3D

# key -> Array of {tag, mesh, base, centre}. `base` and `centre` are captured at
# ADOPT time, when the leaf is still at the closed position the bake wrote, so a
# rebuild that happens while a door is open cannot mistake a travelling leaf's
# position for its home.
var _leaf_rec := {}
var _panel_rec := {}                ## key -> Array of {tag, mesh}
var _open := {}                     ## key -> openness, carried across rebuilds
var _peak := {}                     ## key -> the most open it has ever been
var _sig := {}                      ## key -> which leaves built the last Door
var _travel_m: float = 0.75

## Counters the streaming gate reads. A door that is wired twice, or that keeps a
## reference into a freed cell, is invisible in a screenshot and fatal in a walk.
var wired_cells := 0
var released_cells := 0
var double_wires := 0
var stale_leaves := 0


class Door:
	var key: String
	var leaves: Array = []          # MeshInstance3D
	var bases: Array = []           # their closed positions
	var dirs: Array = []            # unit travel direction each
	var shapes: Array = []          # CollisionShape3D of the closed panel
	var centre := Vector3.ZERO
	var travel_m: float = 0.75
	var open: float = 0.0


## Find every door in a loaded scene pair and wire it up.
##
## `tag` names the cell the pair came from, or "" for a monolithic load. It is
## what `release()` takes back, and it is the only thing that makes a streamed
## build's doors different from a monolithic build's.
func collect(visual: Node, collision: Node, travel_m: float,
		tag: String = "") -> int:
	_travel_m = travel_m
	if tag != "" and _tags().has(tag):
		double_wires += 1
		push_error("door: cell %s was wired twice without being released" % tag)
		return _doors.size()
	var added := 0
	for m in _meshes(visual):
		var n := Interact.strip_cluster(String(m.name))
		if n.begins_with("doorleaf_"):
			# doorleaf_<key>_<i> -- the key may itself contain underscores, so
			# take the LAST field as the index and everything between as the key.
			var body := n.substr(9)
			var cut := body.rfind("_")
			if cut < 0:
				continue
			var key := body.substr(0, cut)
			if not _leaf_rec.has(key):
				_leaf_rec[key] = []
			_leaf_rec[key].append({"tag": tag, "mesh": m,
				"base": m.global_position, "centre": _centre_of(m)})
			added += 1

	if collision != null:
		for m in _meshes(collision):
			var n2 := Interact.strip_cluster(String(m.name))
			if n2.begins_with("doorpanel_"):
				var k2 := n2.substr(10)
				if not _panel_rec.has(k2):
					_panel_rec[k2] = []
				_panel_rec[k2].append({"tag": tag, "mesh": m})
				added += 1
	if tag != "":
		wired_cells += 1
	# REBUILD ON A PANEL TOO, not only on a leaf. A cell can carry the panel of a
	# door whose leaves are in its neighbour -- that is the case this file was
	# rewritten for -- and skipping the rebuild there leaves the panel unattached
	# to the door it seals and the orphan list wrong.
	if added > 0 or tag == "":
		_rebuild()
	return _doors.size()


## Give back everything one cell brought. Called BEFORE the cell is freed, so
## nothing here is ever holding a reference into a `queue_free`d subtree.
func release(tag: String) -> int:
	var gone := 0
	for d in [_leaf_rec, _panel_rec]:
		for key in d.keys():
			var keep := []
			for rec in d[key]:
				if String(rec["tag"]) == tag:
					gone += 1
				else:
					keep.append(rec)
			if keep.is_empty():
				d.erase(key)
			else:
				d[key] = keep
	if gone > 0:
		released_cells += 1
		_rebuild()
	return gone


func _tags() -> Dictionary:
	var out := {}
	for d in [_leaf_rec, _panel_rec]:
		for key in d:
			for rec in d[key]:
				out[String(rec["tag"])] = true
	return out


## Build the door list from every cell that is resident right now.
##
## A DOOR IS ITS KEY, not its cell: this is where the leaves in one cell meet the
## panel in another. Openness is carried over for any door whose leaves are
## unchanged and reset for any door whose are not -- see the header.
func _rebuild() -> void:
	_doors = []
	for key in _leaf_rec:
		var recs: Array = _leaf_rec[key]
		var live := []
		for rec in recs:
			if is_instance_valid(rec["mesh"]):
				live.append(rec)
			else:
				stale_leaves += 1
		if live.is_empty():
			continue
		var d := Door.new()
		d.key = key
		d.travel_m = _travel_m
		# THE MIDPOINT COMES FROM THE CAPTURED CENTRES, not from where the leaves
		# are now. Rebuilding while a door is open and reading the live positions
		# would move the pair's midpoint out with the leaves and reverse one of
		# the travel directions on the next frame.
		var mid := Vector3.ZERO
		for rec in live:
			mid += rec["centre"]
		mid /= float(live.size())
		d.centre = mid
		var sig := PackedStringArray()
		for rec in live:
			d.leaves.append(rec["mesh"])
			d.bases.append(rec["base"])
			sig.append("%s:%d" % [rec["tag"], (rec["mesh"] as Node).get_instance_id()])
			# AWAY FROM THE PAIR'S MIDPOINT, flattened onto the plane the door
			# stands in: the leaves part sideways, not up the radius.
			var away: Vector3 = rec["centre"] - mid
			var up := mid.normalized()          # radial: this station spins
			away = away - up * away.dot(up)
			d.dirs.append(away.normalized() if away.length() > 1e-4
				else Vector3.ZERO)
		if _panel_rec.has(key):
			for prec in _panel_rec[key]:
				if not is_instance_valid(prec["mesh"]):
					continue
				for c in (prec["mesh"] as Node).get_children():
					for cs in c.get_children():
						if cs is CollisionShape3D:
							d.shapes.append(cs)
		sig.sort()
		var s := ",".join(sig)
		if String(_sig.get(key, "")) != s:
			_open[key] = 0.0                    # new leaves are shut leaves
			_sig[key] = s
		d.open = float(_open.get(key, 0.0))
		_doors.append(d)
	# A key with panels and no leaves is a hole in the world with a solid slab in
	# it that nothing can open. It happens legitimately for one frame while a
	# cell pair is arriving; it must not persist.
	for key in _panel_rec:
		if not _leaf_rec.has(key):
			_orphan_panels[key] = true
		else:
			_orphan_panels.erase(key)


var _orphan_panels := {}


## Doors whose panel is resident and whose leaves are not: solid, and nothing can
## open them. Reported rather than hidden.
func orphan_panels() -> Array:
	var k: Array = _orphan_panels.keys()
	k.sort()
	return k


func watch(body: Node3D) -> void:
	_body = body


func _meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		out.append_array(_meshes(c))
	return out


func _centre_of(m: MeshInstance3D) -> Vector3:
	return m.global_transform * m.get_aabb().get_center()


func _physics_process(delta: float) -> void:
	if _body == null:
		return
	var here := _body.global_position
	for d in _doors:
		var want := 1.0 if here.distance_to(d.centre) <= open_range_m else 0.0
		var step := speed_m_s * delta / maxf(d.travel_m, 0.01)
		d.open = clampf(d.open + clampf(want - d.open, -step, step), 0.0, 1.0)
		_open[d.key] = d.open
		_peak[d.key] = maxf(float(_peak.get(d.key, 0.0)), d.open)
		for i in d.leaves.size():
			if not is_instance_valid(d.leaves[i]):
				stale_leaves += 1
				continue
			d.leaves[i].global_position = (
				d.bases[i] + d.dirs[i] * d.travel_m * d.open)
		# The panel is solid until the leaves have actually started moving.
		# Disabling it the instant a body is in range would let a player walk
		# through a door that is still visibly shut, which is the defect this
		# file exists to end, arriving one frame early instead of forever.
		for cs in d.shapes:
			if is_instance_valid(cs):
				cs.disabled = d.open > 0.15


## How far open a named door is, for the headless test to assert on.
func openness(key: String) -> float:
	for d in _doors:
		if d.key == key:
			return d.open
	return -1.0


## THE MOST OPEN IT HAS EVER BEEN. `openness()` samples the door at the moment
## the verdict is printed, which for a body that walked THROUGH a door is several
## seconds after it shut again behind them -- so a run that worked reports 0.00
## and reads as the failure. This is the number that says the door opened.
func peak_openness(key: String) -> float:
	return float(_peak.get(key, -1.0))


func reset_peak(key: String) -> void:
	_peak.erase(key)


## Where a door is, so a caller can walk to one without being told where it is.
func centre_of(key: String) -> Vector3:
	for d in _doors:
		if d.key == key:
			return d.centre
	return Vector3.ZERO


func has(key: String) -> bool:
	for d in _doors:
		if d.key == key:
			return true
	return false


func count() -> int:
	return _doors.size()


## Which doors exist right now, sorted. On a streamed build this changes as cells
## come and go, which is the whole point.
func keys() -> Array:
	var out := []
	for d in _doors:
		out.append(d.key)
	out.sort()
	return out
