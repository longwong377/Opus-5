extends Node3D
## Pressure doors that open when somebody comes to them, and are solid when shut.
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

## How close a body has to be for the door to notice. A pressure door opens as
## you reach it, not across the room.
@export var open_range_m: float = 2.6
## Metres per second the leaves travel. A pressure door is heavy.
@export var speed_m_s: float = 1.6

var _doors: Array = []
var _body: Node3D


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
func collect(visual: Node, collision: Node, travel_m: float) -> int:
	var leaves := {}
	for m in _meshes(visual):
		var n := String(m.name)
		if n.begins_with("doorleaf_"):
			# doorleaf_<key>_<i> -- the key may itself contain underscores, so
			# take the LAST field as the index and everything between as the key.
			var body := n.substr(9)
			var cut := body.rfind("_")
			if cut < 0:
				continue
			var key := body.substr(0, cut)
			if not leaves.has(key):
				leaves[key] = []
			leaves[key].append(m)

	var panels := {}
	if collision != null:
		for m in _meshes(collision):
			var n2 := String(m.name)
			if n2.begins_with("doorpanel_"):
				panels[n2.substr(10)] = m

	for key in leaves:
		var d := Door.new()
		d.key = key
		d.leaves = leaves[key]
		d.travel_m = travel_m
		var mid := Vector3.ZERO
		for m in d.leaves:
			mid += _centre_of(m)
		mid /= float(d.leaves.size())
		d.centre = mid
		for m in d.leaves:
			d.bases.append(m.global_position)
			# AWAY FROM THE PAIR'S MIDPOINT, flattened onto the plane the door
			# stands in: the leaves part sideways, not up the radius.
			var away := _centre_of(m) - mid
			var up := mid.normalized()          # radial: this station spins
			away = away - up * away.dot(up)
			d.dirs.append(away.normalized() if away.length() > 1e-4
				else Vector3.ZERO)
		if panels.has(key):
			for c in panels[key].get_children():
				for cs in c.get_children():
					if cs is CollisionShape3D:
						d.shapes.append(cs)
		_doors.append(d)
	return _doors.size()


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
		for i in d.leaves.size():
			d.leaves[i].global_position = (
				d.bases[i] + d.dirs[i] * d.travel_m * d.open)
		# The panel is solid until the leaves have actually started moving.
		# Disabling it the instant a body is in range would let a player walk
		# through a door that is still visibly shut, which is the defect this
		# file exists to end, arriving one frame early instead of forever.
		for cs in d.shapes:
			cs.disabled = d.open > 0.15


## How far open a named door is, for the headless test to assert on.
func openness(key: String) -> float:
	for d in _doors:
		if d.key == key:
			return d.open
	return -1.0


## Drop doors whose leaves the engine has freed, and say how many went.
##
## THE ONE THING `collect()` COULD NOT DO. All three wiring modules append and
## none of them clears, so calling `collect` again on a newly streamed cell
## already accumulates correctly -- session 4o checked that before assuming it.
## Unloading is the half with no inverse: free a cell's subtree and this array
## still holds records pointing at deleted nodes, which is a crash the first
## time anything iterates them.
##
## BY VALIDITY, NOT BY BOOKKEEPING. Nothing here records which cell a door came
## from, and deliberately: a map from cell to record is a second description of
## something the engine already knows, and it goes stale exactly when a node is
## freed by any path other than the one that wrote the map. `is_instance_valid`
## asks the authority.
func forget_freed() -> int:
	var keep: Array = []
	for d in _doors:
		var live := false
		for m in d.leaves:
			if is_instance_valid(m):
				live = true
				break
		if live:
			keep.append(d)
	var gone: int = _doors.size() - keep.size()
	_doors = keep
	return gone


## How many doors are wired right now. Changes as cells stream.
func count() -> int:
	return _doors.size()
