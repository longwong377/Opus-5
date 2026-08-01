extends Node3D
## G2 ROUTE WALKED -- a body walks from a room on one deck to a room on another.
##
## WHAT THIS ENDS. `station/routes.py` reports the station as ONE foot-connected
## component. That is a claim about a graph. Every walk test in this repository
## walks inside a single z-cluster -- `walkable.py --deck blue/0/0` covers 126 m
## and stops at the end of one 40 m slice of one deck -- and `transit.gd`'s
## `--ride` proves the lift carries a body between two landings of one shaft with
## a 9.2 m lobby either side. **Nothing had ever walked from one deck to
## another.** The corridor that runs ALONG the ship, the junction where it meets
## a ring corridor, the lobby, the car and the far deck had never been in one
## scene with a body in it.
##
## WHAT IT MEASURES, and the metric is the whole point:
##
##   floor_m   metres covered WHILE STANDING ON SOMETHING
##   air_m     metres covered while not
##   offfloor  physics frames not on a floor
##   leg/wp    which leg and which waypoint it was on when it stopped
##
## `floor_m` and not path length, because the streaming work on this codebase
## found a body reporting 11,712 m of "distance travelled" -- it was falling. A
## gate that adds up displacement without asking whether the body was standing on
## anything scores a fall as a journey, and a broken build then scores as walking
## eleven kilometres.
##
## THE CAR IS THE MECHANISM `scripts/transit.gd` ESTABLISHED and this reproduces
## it rather than reinventing it: an AnimatableBody3D with `sync_to_physics`,
## moved from a motion table, and an explicit carry applied from the displacement
## the physics server has ALREADY APPLIED -- one frame back -- because a
## CharacterBody3D is resolved against the floor's previous position. That file
## measured the alternative at 51.83 mm of stand-off at peak speed, which is
## exactly one frame of travel at the Coriolis cap. Nothing here re-derives it.
##
## NOT ONE DISTANCE, ANGLE, RADIUS OR DURATION IS DECIDED HERE. Every one arrives
## in the manifest `station/route_walk.py` writes, and that module reads each of
## them out of the generator that owns it. This file interpolates a table, reads a
## clock, and walks at the next waypoint.

@export var manifest_path: String = ""

var _man: Dictionary = {}
var _player: CharacterBody3D

# The shaft's own frame -- `lift.place` is a rigid rotation and these are its
# columns, so "is the body in the car" is asked in the car's coordinates rather
# than guessed from a radius.
var _origin := Vector3.ZERO
var _ux := Vector3.ZERO
var _uy := Vector3.ZERO
var _axis := Vector3.ZERO
var _pivot := Vector3.ZERO

var _car: Node3D
var _car_body: PhysicsBody3D
var _car_prev := Vector3.ZERO
## THE COLLIDER IS ONE FRAME BEHIND THE COMMAND. `scripts/transit.gd` measured
## it: with the carry taken from the CURRENT command the body sits 51.83 mm above
## the car floor at peak speed, and the Coriolis cap of 3.1345 m/s at 60 Hz is
## 52.2 mm a frame. Godot resolves a CharacterBody3D against the position the
## physics server is holding, which is the one commanded LAST frame -- so the
## carry uses the displacement already applied, and the stand-off is measured
## against the floor's physical height rather than its commanded one. Measuring
## against the command reports one frame of travel as an error every frame; this
## file's first run read 53.11 mm for exactly that reason.
var _car_lag := Vector3.ZERO
var _car_y := 0.0
var _car_y_phys := 0.0
var _car_moved := 0.0
var _panels: Array[CollisionShape3D] = []
var _leaves: Array = []
var _door_open := 1.0
var _door_speed := 1.6
var _door_travel := 0.75

## Every room door in the route's collision shells, as {centre, shape}. A shut
## door is a solid panel in the shell -- `collision.door_panel` -- so the room at
## the end of the route cannot be entered until it opens. `scripts/door.gd` owns
## the rule and its range is read off that script rather than copied.
var _room_doors: Array = []
var _door_range := 2.6
var _no_doors := false

var _landings: Array = []
var _from := 0
var _to := 0
var _park := -1
var _seal := false

const ST_SETTLE := 0
const ST_WALK_OUT := 1
const ST_BOARD := 2
const ST_SHUT := 3
const ST_RIDE := 4
const ST_OPEN := 5
const ST_ALIGHT := 6
const ST_WALK_IN := 7
const ST_DONE := 8

var _state := ST_SETTLE
var _frame := 0
var _state_frame := 0
var _t_settle := 90
var _t_board := 600
var _t_alight := 600
var _trace := 0

## The route, flattened into waypoints. Each carries the leg it belongs to so the
## verdict can say WHICH leg a body stopped on and not merely that it did.
var _wps: Array = []
var _wp := 0
var _wp_base := 0                     # first waypoint of the leg being walked
var _legs: Array = []
var _leg := 0
var _leg_frames := 0
var _leg_floor := 0.0
var _leg_rows: Array = []

var _floor_m := 0.0
var _air_m := 0.0
var _off := 0
var _frames := 0
var _prev_pos := Vector3.ZERO
var _r_start := 0.0
var _board_r0 := 0.0
var _fell_m := 0.0
var _door_gap := -1.0
var _settle_off := 0
var _settle_drop := 0.0
var _boarded := false
var _alighted := false
var _completed := false
var _stopped_why := "-"
var _stopped_at := "-"
var _ride_t := 0.0
var _ride_s := 0.0
var _ride_from_y := 0.0
var _ride_to_y := 0.0
var _ride_frames := 0
var _ride_off := 0
var _standoff_max := 0.0
var _doors_shut_before_move := true


func _ready() -> void:
	var args := _args()
	if args.has("manifest"):
		manifest_path = args["manifest"]
	if not _load_manifest():
		push_error("route: could not read %s" % manifest_path)
		get_tree().quit(2)
		return
	_park = int(args.get("park", "-1"))
	_seal = String(args.get("seal", "off")) != "off"
	_no_doors = args.has("no-doors")
	_trace = int(args.get("trace", "0"))
	_from = int(_man["from_landing"])
	_to = int(_man["to_landing"])
	_landings = _man["landings"]
	_build_world(String(args.get("render", "off")) != "off")
	_build_route()
	_spawn_player()
	if args.has("route-test"):
		_run(args)


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--"):
			var body := s.substr(2)
			var eq := body.find("=")
			if eq >= 0:
				out[body.substr(0, eq)] = body.substr(eq + 1)
			else:
				out[body] = "1"
	return out


func _load_manifest() -> bool:
	if manifest_path == "":
		return false
	var f := FileAccess.open(manifest_path, FileAccess.READ)
	if f == null:
		return false
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	_man = parsed
	return true


func _v3(a) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _load_glb(path: String) -> Node:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		return null
	return doc.generate_scene(state)


func _meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		out.append_array(_meshes(c))
	return out


# ---------------------------------------------------------------------------
# The world: five collision shells and one car
# ---------------------------------------------------------------------------

## Load every piece of the route and give it a floor.
##
## THE SHELLS, NOT THE RENDER MESHES, AND THAT IS `station/collision.py`'s whole
## finding: the corridor a player SEES carries a 66 mm lighting channel and 22 mm
## proud tiles, and a capsule dropped on it wedges on an internal edge while
## reporting `on_floor = true`. The render of every deck this route crosses is
## already on disk in `station/generated/scene/station/` and `--render=on` loads
## it; the body stands on the smooth shell either way.
func _build_world(render: bool) -> void:
	var n_mesh := 0
	var paths: Array = []
	for p in _man["collision_glbs"]:
		var s := String(p)
		# THE SEALED COLUMN IS A DIFFERENT FILE, NOT A SWITCH IN THIS SCRIPT.
		# `lift.lift_collision(landings=False)` walls up every landing aperture;
		# a control implemented here by disabling a shape would be a control
		# against this file rather than against the geometry that ships.
		if _seal and s.ends_with("column_col.glb"):
			s = String(_man["column_col_sealed_glb"])
		paths.append(s)
	for s in paths:
		var col := _load_glb(s)
		if col == null:
			push_error("route: could not load %s" % s)
			get_tree().quit(2)
			return
		add_child(col)
		for m in _meshes(col):
			m.create_trimesh_collision()
			m.visible = false
			n_mesh += 1
			if String(m.name).begins_with("doorpanel_"):
				_wire_room_door(m)
	# THE RENDER OF EVERY DECK ON THIS ROUTE IS ALREADY ON DISK.
	# `tools/export_station.py` wrote it -- 70 decks and 5 columns, 2.2 GB -- and
	# nothing here rebuilds it. It is not loaded by default because the body
	# stands on the SHELL and a headless walk has nothing to look at; `--render=on`
	# puts the built meshes over the same shells and reports what it got, so the
	# claim that the route runs on the station's own artefacts is a count.
	var n_vis := 0
	if render:
		for p in _man.get("station_glbs", []):
			var vis := _load_glb(String(p))
			if vis == null:
				push_error("route: could not load %s" % String(p))
				continue
			add_child(vis)
			n_vis += _meshes(vis).size()
		print("route: %d visual meshes from %d built station glb(s)"
			% [n_vis, _man.get("station_glbs", []).size()])

	_origin = _v3(_man["origin"])
	_ux = _v3(_man["ux"])
	_uy = _v3(_man["uy"])
	_axis = _v3(_man["travel_axis"])
	_pivot = _v3(_man["pivot"])
	_car = Node3D.new()
	_car.name = "Car"
	add_child(_car)
	var cv := _load_glb(String(_man["car_glb"]))
	if cv != null:
		_car.add_child(cv)
		_wire_leaves(cv)
	var cc := _load_glb(String(_man["car_col_glb"]))
	if cc != null:
		# A SIBLING OF THE VISUAL CAR, NOT A CHILD. `sync_to_physics` asks for
		# notification of a body's own LOCAL transform, and a body carried by a
		# moving parent never changes its local transform -- the server would see
		# a teleport rather than a motion, which is the exact failure this whole
		# arrangement exists to prevent. `scripts/transit.gd` established it.
		_car_body = _make_car_body(cc)
		add_child(_car_body)
	_set_car(_landing_y(_park if _park >= 0 else _from))
	_car_prev = _car.position
	print("route: %d collision meshes over %d file(s), %d room door(s), "
		% [n_mesh, paths.size(), _room_doors.size()]
		+ "car on a %s, %d panel(s), %d leaves, %d landings%s"
		% [("nothing" if _car_body == null else _car_body.get_class()),
			_panels.size(), _leaves.size(), _landings.size(),
			(" [LANDINGS SEALED]" if _seal else "")])


func _wire_room_door(m: MeshInstance3D) -> void:
	var body := m.get_child(m.get_child_count() - 1)
	for c in body.get_children():
		if c is CollisionShape3D:
			_room_doors.append({"key": String(m.name).substr(10),
				"centre": m.global_transform * m.get_aabb().get_center(),
				"shape": c})
	var ds = load("res://scripts/door.gd")
	if ds != null:
		var probe = ds.new()
		_door_range = float(probe.open_range_m)
		probe.free()


func _make_car_body(root: Node) -> PhysicsBody3D:
	var ab := AnimatableBody3D.new()
	ab.sync_to_physics = true
	ab.name = "CarBody"
	for m in _meshes(root):
		var cs := CollisionShape3D.new()
		cs.shape = m.mesh.create_trimesh_shape()
		cs.name = String(m.name)
		ab.add_child(cs)
		if String(m.name).begins_with("liftdoorpanel"):
			_panels.append(cs)
		m.visible = false
	return ab


func _wire_leaves(root: Node) -> void:
	var travel: Dictionary = _man["leaf_travel"]
	for m in _meshes(root):
		var n := String(m.name)
		if not n.begins_with("liftleaf_"):
			continue
		var key := n.substr(9)
		if not travel.has(key):
			continue
		var d := _v3(travel[key])
		_leaves.append({"node": m, "base": m.position,
			"dir": d.normalized(), "travel": d.length()})
		_door_travel = maxf(_door_travel, d.length())
	var ds = load("res://scripts/door.gd")
	if ds != null:
		var probe = ds.new()
		_door_speed = float(probe.speed_m_s)
		probe.free()


func _apply_doors() -> void:
	for l in _leaves:
		l["node"].position = l["base"] + l["dir"] * l["travel"] * _door_open
	for cs in _panels:
		cs.disabled = _door_open > 0.15


func _door_seconds() -> float:
	return _door_travel / maxf(_door_speed, 0.01)


func _landing_y(i: int) -> float:
	return float(_landings[i]["y_m"])


func _set_car(y: float) -> void:
	_car_y = y
	var at := _pivot + _axis * y
	_car.position = at
	if _car_body != null:
		_car_body.position = at


func _local(p: Vector3) -> Vector3:
	var d := p - _origin
	return Vector3(d.dot(_ux), d.dot(_uy), p.z - _origin.z)


func _in_car(p: Vector3) -> bool:
	var l := _local(p)
	var car: Dictionary = _man["car"]
	var hw := float(car["clear_w"]) / 2.0
	var hd := float(car["clear_d"]) / 2.0
	return (absf(l.x) < hw and absf(l.z) < hd
		and l.y > _car_y - 0.35 and l.y < _car_y + float(car["clear_h"]))


func _radius(p: Vector3) -> float:
	return sqrt(p.x * p.x + p.y * p.y)


func _deck_at(r: float) -> int:
	var best := -1
	var miss := 1e30
	for i in _landings.size():
		var d: float = absf(float(_landings[i]["walk_r_m"]) - r)
		if d < miss:
			miss = d
			best = i
	return best


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------

## Flatten the manifest's legs into waypoints, with a frame budget each.
##
## A BUDGET PER LEG AND NOT ONE FOR THE RUN, because "it stopped" has to name
## WHERE. A single run-long budget reports a body that walked 400 m and stuck in
## the last doorway identically to one that never left the spawn.
func _build_route() -> void:
	var speed := 4.2
	for half in ["legs_out", "legs_in"]:
		for l in _man[half]:
			var pts: Array = l["points"]
			var tols: Array = l["tols"]
			var budget: int = maxi(int(_man["leg_budget_floor_frames"]),
				int(ceil(float(l["length_m"]) / speed * 60.0
					* float(_man["leg_budget"]))))
			_legs.append({"kind": String(l["kind"]), "note": String(l["note"]),
				"half": half, "length_m": float(l["length_m"]),
				"budget": budget, "first": _wps.size(), "n": pts.size()})
			for i in pts.size():
				# THE TOLERANCE IS PER WAYPOINT, AND A DOORWAY'S IS TIGHT. A body
				# that "reached" a waypoint 0.8 m off the centre line of a 1.5 m
				# aperture and then turned for the next one met the jamb and
				# stood there for 7,093 frames. `route_walk.door_tol_m` derives
				# the figure from the aperture and the capsule.
				_wps.append({"pos": _v3(pts[i]), "tol": float(tols[i]),
					"leg": _legs.size() - 1})
	# The lift's own legs sit between the two halves; `_leg` walks this list and
	# the state machine skips from the last outbound leg to the first inbound one.
	_leg = 0
	_wp = 0


func _out_legs() -> int:
	var n := 0
	for l in _legs:
		if String(l["half"]) == "legs_out":
			n += 1
	return n


func _spawn_player() -> void:
	_player = CharacterBody3D.new()
	_player.set_script(load("res://scripts/player.gd"))
	# DOWN IS OUTWARD. A ring deck is the inside of a spun barrel, so gravity is
	# the radial direction at the body's own position -- `player.gravity_dir()`
	# calls that mode "drum" and it is right for any spun floor. The MAGNITUDE
	# changes along this route: the two decks are at different radii and the ride
	# crosses everything in between, so it is set every frame from the body's own
	# radius and the schema's own spin rate, w^2 r, rather than once at spawn.
	_player.gravity_mode = "drum"
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	caps.height = 1.8
	caps.radius = 0.35
	shape.shape = caps
	shape.position = Vector3(0, 0.9, 0)
	_player.add_child(shape)
	_player.position = _v3(_man["spawn"])
	add_child(_player)
	_player.platform_floor_layers = 0
	_apply_gravity()

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.02, 0.02, 0.03)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.6, 0.6, 0.62)
	e.ambient_light_energy = 0.6
	env.environment = e
	add_child(env)


func _apply_gravity() -> void:
	var w := float(_man["omega_rad_s"])
	_player.gravity_m_s2 = w * w * _radius(_player.global_position)


func _run(args: Dictionary) -> void:
	_t_settle = int(args.get("settle", "90"))
	_t_board = int(args.get("board", "600"))
	_t_alight = int(args.get("alight", "600"))
	_ride_s = float(_man["ride"]["seconds"])
	_ride_from_y = _landing_y(_from)
	_ride_to_y = _landing_y(_to)
	_door_open = 1.0
	_apply_doors()
	_prev_pos = _player.global_position
	_r_start = _radius(_prev_pos)
	print("route: %s (%s) -> %s (%s), %d waypoints over %d legs, "
		% [String(_man["from"]["place"]), String(_man["from"]["deck"]),
			String(_man["to"]["place"]), String(_man["to"]["deck"]),
			_wps.size(), _legs.size()]
		+ "%.0f m of walking and a %.3f m ride, landing %d -> %d%s"
		% [float(_man["walk_m"]), float(_man["rise_m"]), _from, _to,
			("  [CAR PARKED AT %d]" % _park if _park >= 0 else "")])
	set_physics_process(true)


func _physics_process(delta: float) -> void:
	if _state == ST_DONE:
		return
	_frame += 1
	_state_frame += 1
	# A HARD CAP ON THE WHOLE RUN, over and above the per-leg budgets. Every
	# state here has its own timeout and the arithmetic says they cannot add up
	# past this -- which is exactly why a run that passes it is a run whose state
	# machine has a hole in it, and a headless test that does not end is a test
	# that costs a session rather than failing.
	if _frame > int(_man.get("max_frames", 60000)):
		_stopped_why = "the run's own %d frame cap -- a state never ended" % [
			int(_man.get("max_frames", 60000))]
		_finish()
		return

	# 1. THE VEHICLE MOVES FIRST, and the body is put back on its floor before it
	#    is asked to walk. Carrying after `move_and_slide` has resolved the body
	#    against a floor that was not there yet leaves the rider a frame behind
	#    the car for the whole ride.
	_advance(delta)
	var d := _car_lag
	if d.length_squared() > 0.0 and _in_car(_player.global_position):
		_player.global_position += d
	var cmd := _car.position
	_car_y_phys = _car_y - _axis.dot(cmd - _car_prev)
	_car_lag = cmd - _car_prev
	_car_moved += _car_lag.length()
	_car_prev = cmd

	# 2. Then the body walks, on whatever it is standing on now.
	_apply_gravity()
	_open_near_doors()
	var steer := _steer()
	if steer.length_squared() > 1e-9:
		_player.step(delta, Vector2.ZERO, false, false, steer)
	else:
		_player.step(delta, Vector2.ZERO, false, false)

	_measure()
	if _trace > 0 and _frame % _trace == 0:
		var p := _player.global_position
		print("TRACE f=%d st=%d leg=%d wp=%d d=%.2f r=%.2f z=%.1f floor=%s"
			% [_frame, _state, _leg, _wp, _wp_dist(), _radius(p), p.z,
				str(_player.is_on_floor()).to_lower()])
	_next_state()


## A shut pressure door is a solid panel in the collision shell, so the room at
## the end of the route cannot be entered until one opens. `--no-doors` leaves
## every panel solid, which is `walkable.py`'s own control one route longer.
func _open_near_doors() -> void:
	if _no_doors:
		return
	var p := _player.global_position
	for d in _room_doors:
		d["shape"].disabled = p.distance_to(d["centre"]) < _door_range


func _advance(delta: float) -> void:
	match _state:
		ST_SHUT:
			_door_open = maxf(0.0, _door_open - delta / _door_seconds())
			_apply_doors()
		ST_RIDE:
			_ride_t += delta
			var u: float = clampf(_ride_t / _ride_s, 0.0, 1.0)
			var f := _interp(_man["ride"]["table"], u)
			_set_car(_ride_from_y + (_ride_to_y - _ride_from_y) * f)
		ST_OPEN:
			_door_open = minf(1.0, _door_open + delta / _door_seconds())
			_apply_doors()


func _interp(tab: Array, u: float) -> float:
	if u <= 0.0:
		return 0.0
	var n := tab.size() - 1
	if u >= 1.0 or n < 1:
		return float(tab[n][1])
	var x: float = u * float(n)
	var i: int = int(floor(x))
	return lerp(float(tab[i][1]), float(tab[i + 1][1]), x - float(i))


func _wp_pos() -> Vector3:
	return _wps[mini(_wp, _wps.size() - 1)]["pos"]


func _wp_dist() -> float:
	return _player.global_position.distance_to(_wp_pos())


func _steer() -> Vector3:
	match _state:
		ST_WALK_OUT, ST_WALK_IN:
			return _wp_pos() - _player.global_position
		ST_BOARD, ST_SHUT:
			# AT WHERE THE CAR SHOULD BE, not at where it is. With the car parked
			# elsewhere the body must still walk into the doorway -- that is the
			# control -- and steering at the car's actual position would walk it
			# somewhere safe instead.
			return _v3(_landings[_from]["car_stand"]) - _player.global_position
		ST_ALIGHT:
			return _v3(_landings[_to]["stand"]) - _player.global_position
	return Vector3.ZERO


func _measure() -> void:
	var p := _player.global_position
	var on := _player.is_on_floor()
	var step := p.distance_to(_prev_pos)
	if on:
		_floor_m += step
		_leg_floor += step
	else:
		_air_m += step
		_off += 1
	_frames += 1
	_prev_pos = p
	# HOW FAR IT FELL, AND ONLY IN THE DOORWAY. The first version took the whole
	# run's largest radius against the spawn's, which on a completed route is the
	# RIDE -- 7.2 m of radius, reported as a fall. A fall is what happens to a
	# body that walks at a doorway with nothing behind it, so it is measured
	# where that can happen and nowhere else.
	if _state == ST_BOARD:
		_fell_m = maxf(_fell_m, _radius(p) - _board_r0)
		# THE CLOSEST IT EVER GOT TO WHERE THE CAR'S FLOOR IS. With the landing
		# apertures sealed this is the whole verdict on the control: the body is
		# stopped AT THE THRESHOLD, a capsule's radius outside a wall, rather
		# than arriving or falling.
		var gap := p.distance_to(_v3(_landings[_from]["car_stand"]))
		_door_gap = gap if _door_gap < 0.0 else minf(_door_gap, gap)
	if _state == ST_RIDE:
		_ride_frames += 1
		if not on:
			_ride_off += 1
		if _in_car(p):
			_standoff_max = maxf(_standoff_max, absf(_local(p).y - _car_y_phys))
	if _state == ST_WALK_OUT or _state == ST_WALK_IN:
		_leg_frames += 1


func _finish_leg(reached: bool) -> void:
	_leg_rows.append({"kind": String(_legs[_leg]["kind"]),
		"floor_m": _leg_floor, "frames": _leg_frames,
		"reached": reached, "note": String(_legs[_leg]["note"])})
	_leg_floor = 0.0
	_leg_frames = 0


## Advance along the waypoints of the current half of the route.
## Returns true when the last waypoint of the last leg has been reached.
func _walk_waypoints(last_wp: int) -> bool:
	if _wp_dist() < float(_wps[mini(_wp, _wps.size() - 1)]["tol"]):
		_wp += 1
		if _wp > last_wp:
			_finish_leg(true)
			return true
		if int(_wps[_wp]["leg"]) != _leg:
			_finish_leg(true)
			_leg = int(_wps[_wp]["leg"])
		return false
	if _leg_frames > int(_legs[_leg]["budget"]):
		_stopped_why = ("the leg's %d frame budget ran out %.2f m from waypoint "
			+ "%d of %d") % [int(_legs[_leg]["budget"]), _wp_dist(),
				_wp - int(_legs[_leg]["first"]) + 1, int(_legs[_leg]["n"])]
		_finish_leg(false)
		_finish()
	return false


func _next_state() -> void:
	match _state:
		ST_SETTLE:
			if _state_frame >= _t_settle:
				var dk := _deck_at(_radius(_player.global_position))
				# THE SETTLE IS NOT THE WALK, AND ITS FRAMES ARE NOT COUNTED IN
				# IT. `collision.stand_at` spawns a body 50 mm above the floor on
				# purpose -- "a claim that needs a metre of falling to resolve is
				# being hoped for rather than checked" -- so the first three
				# frames of every run are a 50 mm drop. Counting them made
				# `offfloor` read 3/7238 on a route that never left the floor.
				# The drop is reported and asserted instead, which is the claim
				# actually worth making about a spawn.
				_settle_off = _off
				_settle_drop = _radius(_player.global_position) - _r_start
				print("route: settled at landing %d (r=%.3f m), on_floor=%s, "
					% [dk, _radius(_player.global_position),
						str(_player.is_on_floor()).to_lower()]
					+ "dropped %.0f mm in %d frames"
					% [_settle_drop * 1000.0, _off])
				_floor_m = 0.0
				_air_m = 0.0
				_off = 0
				_frames = 0
				_prev_pos = _player.global_position
				_go(ST_WALK_OUT)
		ST_WALK_OUT:
			var last: int = int(_legs[_out_legs() - 1]["first"]) \
				+ int(_legs[_out_legs() - 1]["n"]) - 1
			if _walk_waypoints(last):
				print("route: reached the column's lobby at landing %d after "
					% _from + "%d frames, %.1f m on the floor"
					% [_frame, _floor_m])
				_go(ST_BOARD)
		ST_BOARD:
			# YOU CANNOT BOARD A CAR THAT IS NOT THERE, and `scripts/transit.gd`
			# had to learn it: with the car parked elsewhere the body falls
			# through its ceiling -- an outward-facing face, therefore a back face
			# to something coming from above -- lands on the car's floor, and
			# `_in_car` reads true. Being inside the car is not boarding.
			if _park >= 0:
				if _state_frame >= _t_board:
					_stopped_why = ("the car was parked at landing %d, so there "
						+ "was nothing behind the doorway") % _park
					_finish()
			elif _in_car(_player.global_position) and _player.is_on_floor():
				_boarded = true
				print("route: boarded at landing %d after %d frames"
					% [_from, _state_frame])
				_go(ST_SHUT)
			elif _state_frame >= _t_board:
				var away := _player.global_position.distance_to(
					_v3(_landings[_from]["car_stand"]))
				_stopped_why = ("%d frames at the landing and the body never "
					+ "got into the car -- %.2f m from where it stands") % [
					_t_board, away]
				_finish()
		ST_SHUT:
			if _door_open <= 0.0:
				_go(ST_RIDE)
		ST_RIDE:
			if _ride_t >= _ride_s:
				_set_car(_ride_to_y)
				print("route: rode %.3f m of radius in %d frames (%.3f s)"
					% [absf(_ride_to_y - _ride_from_y), _ride_frames, _ride_t])
				_go(ST_OPEN)
		ST_OPEN:
			if _door_open >= 1.0:
				_go(ST_ALIGHT)
		ST_ALIGHT:
			var l := _local(_player.global_position)
			if (absf(l.z) > float(_man["bore_hd"]) + 0.6
					and _player.is_on_floor()):
				_alighted = true
				print("route: alighted at landing %d after %d frames"
					% [_to, _state_frame])
				_leg = _out_legs()
				_wp = int(_legs[_leg]["first"])
				_leg_floor = 0.0
				_leg_frames = 0
				_go(ST_WALK_IN)
			elif _state_frame >= _t_alight:
				_stopped_why = "the body never got out of the car"
				_finish()
		ST_WALK_IN:
			if _walk_waypoints(_wps.size() - 1):
				_completed = true
				_finish()


func _go(s: int) -> void:
	if s == ST_RIDE:
		_doors_shut_before_move = _door_open <= 0.0
		_ride_t = 0.0
	if s == ST_BOARD:
		_board_r0 = _radius(_player.global_position)
	_state = s
	_state_frame = 0


## Which state the run ended in, by name. "Where did it stop" is the headline
## this gate reports and the LEG cannot answer it: a body that finishes its last
## walking leg and is then stopped at the lift threshold still carries that leg's
## index, so both controls read "stopped on leg 1 axial" when neither had stopped
## on a leg at all.
const ST_NAMES := ["settle", "walk_out", "board", "shut", "ride", "open",
	"alight", "walk_in", "done"]


func _finish() -> void:
	if _state == ST_DONE:
		return
	_stopped_at = ST_NAMES[_state]
	_state = ST_DONE
	set_physics_process(false)
	for r in _leg_rows:
		print("ROUTELEG kind=%s floor_m=%.3f frames=%d reached=%s note=%s"
			% [r["kind"], r["floor_m"], r["frames"],
				str(r["reached"]).to_lower(), String(r["note"]).replace(" ", "_")])
	var p := _player.global_position
	var tgt := _v3(_man["target"]["at"])
	print(("ROUTETEST completed=%s boarded=%s alighted=%s "
		+ "floor_m=%.3f air_m=%.3f offfloor=%d/%d "
		+ "arrive_m=%.3f leg=%d leg_kind=%s wp=%d leg_left_m=%.3f "
		+ "start_deck=%d end_deck=%d r_start=%.3f r_end=%.3f fell_m=%.3f "
		+ "settle_drop_m=%.4f settle_offfloor=%d "
		+ "car_moved_m=%.4f ride_offfloor=%d/%d standoff_max_mm=%.2f "
		+ "doors_shut_before_move=%s door_gap_m=%.3f ride_s=%.3f "
		+ "frames=%d park=%d seal=%s stopped_at=%s stopped_why=%s") % [
		str(_completed).to_lower(), str(_boarded).to_lower(),
		str(_alighted).to_lower(),
		_floor_m, _air_m, _off, _frames,
		p.distance_to(tgt), _leg, String(_legs[_leg]["kind"]), _wp,
		_wp_dist(),
		_deck_at(_r_start), _deck_at(_radius(p)), _r_start, _radius(p),
		_fell_m, _settle_drop, _settle_off,
		_car_moved, _ride_off, _ride_frames, _standoff_max * 1000.0,
		str(_doors_shut_before_move).to_lower(),
		_door_gap, _ride_s,
		_frame, _park, ("on" if _seal else "off"), _stopped_at,
		_stopped_why.replace(" ", "_")])
	get_tree().quit(0)
