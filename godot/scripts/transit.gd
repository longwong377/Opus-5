extends Node3D
## VEHICLES THAT MOVE, AND A BODY THAT RIDES ONE.
##
## WHAT THIS ENDS. Five modules in `station/` model transport and not one of them
## moves: `transit.py` costs every journey, `npc/navigation.py` owns
## `lift_ride_s` and the Coriolis cap, `core_tube.py`'s own docstring says its
## tubes are built "with no motion in them at all", `tram.py` advertises a
## `phase` parameter that walks a whole train along the guideway and nothing has
## ever called it with a changing one, and `lift.py` builds a shaft, a car and a
## floor under it -- parked. Every mode is fully costed and none of them moves.
## That is this project's oldest shape: a number computed about a thing that does
## not exist.
##
## WHAT MOVES HERE, and it is two different problems:
##
##   the lift   the car is a body the physics engine owns, and the floor of it
##              has to take the player with it. Radial: on a spun ring UP IS
##              INWARD, toward the axis, so the whole ride is a translation along
##              `station/lift.py::_basis(angle)[1]` and a rising car has a
##              SMALLER radius at the end than at the start.
##   the tram   nothing rides it yet; the cars are placed by
##              `tram.guideway_cars(phase=)` and this reproduces that function's
##              own placement rule as a function of time. The gate is that the
##              engine and Python agree about where every car is.
##
## NOT ONE DURATION IS DECIDED IN THIS FILE. Every one arrives in the manifest
## `station/transit_runtime.py` writes, and every one of those is read out of the
## module that owns it: the ride is `navigation.lift_ride_s`, cross-checked
## against `transit.climb_leg`; the motion curve is a TABLE sampled from the
## smoothstep both of those functions derive their answer from, and its peak is
## asserted against `navigation.coriolis_speed_cap` before it is written; the
## dwell is `navigation.TRANSIT_DWELL_S`; the tram's cycle is
## `transit.line_report`. This file interpolates a table and reads a clock.
##
## THE ONE NUMBER IT DOES FETCH IT FETCHES RATHER THAN COPIES: how fast a door
## leaf travels is `scripts/door.gd`'s `speed_m_s`, read off that script by
## instancing it. A second copy of 1.6 here would be a second decision about
## pressure doors, which is exactly the class of duplication this project keeps
## paying for.
##
## HEADLESS BY DESIGN, like `scripts/walk.gd`: there is no GPU and no human in
## this container, so `--ride-test` steps the physics itself, walks the body with
## a synthetic steer vector and prints one line `station/transit_runtime.py`
## parses. And it reports ON-FLOOR distance, because a broken run in the
## streaming work on this same codebase reported a path length of 11,712 m -- the
## body was falling. A gate that adds up displacement without asking whether the
## body was standing on anything scores a fall as a journey.

@export var manifest_path: String = ""

var _man: Dictionary = {}
var _player: CharacterBody3D

# The shaft's own frame, from the manifest. `lift.place` is a rigid rotation;
# these are its columns, so "is the body in the car" can be asked in the car's
# coordinates instead of guessed from a radius.
var _origin := Vector3.ZERO
var _ux := Vector3.ZERO
var _uy := Vector3.ZERO
var _axis := Vector3.ZERO
var _pivot := Vector3.ZERO

var _car: Node3D                      # the visual car, and the leaves under it
var _car_body: PhysicsBody3D          # its collider -- the thing that moves
var _car_prev := Vector3.ZERO
## THE COLLIDER IS ONE FRAME BEHIND THE COMMAND, AND THE CARRY HAS TO BE TOO.
## Measured, not assumed: with the carry applied from the CURRENT command the
## body sat 51.83 mm above the car floor at peak speed, and 3.1345 m/s (the
## Coriolis cap) at 60 Hz is 52.2 mm a frame. That is the whole of the error and
## it identifies the cause exactly. Godot processes a node's `_physics_process`
## in tree order and an AnimatableBody3D's `sync_to_physics` sync afterwards, so
## when `move_and_slide()` runs inside this script the physics server still holds
## the position commanded LAST frame -- the body is resolved against the floor's
## previous position, which is inherent to kinematic physics and is what the
## engine's own moving-platform path does too. So the carry uses the delta the
## server has already applied, one frame back, and the body rides the floor it is
## actually standing on rather than the one it has been told about.
var _car_lag := Vector3.ZERO          # P(n-1) - P(n-2): what the server applied
var _car_y_phys := 0.0                # the y the server is holding
var _panels: Array[CollisionShape3D] = []
var _leaves: Array = []               # [{node, base, dir, travel}]

var _landings: Array = []
var _from := 0
var _to := 0
var _park := -1
## THE FOUR WAYS A FLOOR CAN TAKE A BODY WITH IT, EACH ITS OWN SWITCH.
##
## An A/B that changes two of them at once cannot say which one did the work,
## and this project has paid for exactly that reading twice. Measured on this
## shaft (see docs/transport-4g.md), THREE of these four carry a body down a
## lift on their own, because the ride is Coriolis-capped at 3.1345 m/s and
## 52 mm a frame is inside every one of their windows:
##
##   carry     this script translates the body by the floor's own displacement
##   snap      `CharacterBody3D.floor_snap_length`, 0.1 m by default -- it
##             re-attaches a body to a floor that has moved out from under it,
##             and 0.1 m is TWICE the 52 mm a frame this lift travels
##   platform  the platform velocity `move_and_slide` picks up from the body it
##             is standing on. OFF by default here, because with the explicit
##             carry on it would apply the same displacement a second time
##   collider  AnimatableBody3D + sync_to_physics, versus a StaticBody3D whose
##             transform is rewritten -- the classic wrong answer
##
## The subject is what ships: carry on, snap at the engine default, platform off,
## an AnimatableBody3D. The control has to turn off every mechanism that could
## substitute for the one under test, or it is not a control.
var _carry := true
var _snap := true
var _platform := false
var _collider := "animatable"

var _door_open := 1.0
var _door_speed := 1.6                # replaced from scripts/door.gd at load
var _door_travel := 0.75              # replaced from the manifest (measured)

## Driven by another script's clock rather than by `--ride-test`. See `_ready`.
var _embedded := false
## Whether to load the static shaft's RENDER mesh. The ride gate loads it; a
## headless commute does not need three thousand triangles nobody looks at, and
## the collision -- which is what a body stands on -- is loaded either way.
var _visuals := true

# ---------------------------------------------------------------------------

const ST_SETTLE := 0
const ST_BOARD := 1
const ST_SHUT := 2
const ST_RIDE := 3
const ST_OPEN := 4
const ST_ALIGHT := 5
const ST_DONE := 6

var _testing := false
var _state := ST_SETTLE
var _frame := 0
var _state_frame := 0
var _t_settle := 90
var _t_board := 480
var _t_alight := 480
var _trace := 0

var _car_y := 0.0
var _ride_t := 0.0
var _ride_s := 0.0
var _ride_from_y := 0.0
var _ride_to_y := 0.0
var _ride_frames := 0
var _ride_off := 0
var _car_moved := 0.0

var _boarded := false
var _alighted := false
var _doors_shut_before_move := true
var _prev_pos := Vector3.ZERO
var _r_settle := 0.0
var _r_board := 0.0
var _floor_m := 0.0
var _air_m := 0.0
var _radial_floor := 0.0
var _radial_air := 0.0
var _off := 0
var _frames := 0
var _standoff_max := 0.0
var _carry_frames := 0
## WHICH frames of the ride lost the floor, not just how many. A body that loses
## it on the first frame and one that loses it throughout are different defects
## and a count cannot tell them apart.
var _ride_off_first := -1
var _ride_off_last := -1
## How close to the shut door the body ended up standing, in the car's own
## frame. Reported because it is what two frames of lost floor turned out to be.
var _ride_door_z := 0.0


func _ready() -> void:
	# ALREADY EMBEDDED, AND `_ready` CAN ARRIVE AFTER `embed_lift`.
	#
	# `scripts/life.gd` adds this node from `_initialize`, before the tree is
	# running, so the order is embed-then-ready rather than ready-then-embed.
	# Without this guard `_ready` re-read the COMMUTE manifest off the command
	# line -- `--manifest=` is in `OS.get_cmdline_user_args()` for the whole
	# process -- and replaced the lift's own manifest with it. Everything still
	# looked right: the car moved 376 m, the body rode 21.55 m of radius with 0
	# frames off the floor. Only `_in_car` failed, because the commute manifest
	# has no `car` block, so its half widths read 0.0 and NOTHING is inside a
	# box of zero size. `boarded=false` on a body standing in the car.
	if _embedded:
		return
	var args := _args()
	if args.has("manifest"):
		manifest_path = args["manifest"]
	# EMBEDDED: SOMEBODY ELSE OWNS THE CLOCK.
	#
	# `scripts/life.gd` drives a resident's whole day, and part of that day is a
	# lift ride. It does NOT get its own copy of the car -- it instantiates this
	# script and calls `embed_lift`, so there is exactly one answer in this
	# project to "how does a moving floor take a body with it", and
	# `transit_runtime.py --ride` remains the test of it. With no manifest on
	# the command line and none set, this node builds nothing and waits.
	if manifest_path == "" and not args.has("manifest"):
		_embedded = true
		set_physics_process(false)
		return
	if not _load_manifest():
		push_error("transit: could not read %s" % manifest_path)
		get_tree().quit(2)
		return
	if String(_man.get("kind", "")) == "tram":
		_build_tram()
		if args.has("tram-test"):
			_run_tram_test(args)
		return
	_build_lift()
	_from = int(args.get("from", "0"))
	_to = int(args.get("to", str(_landings.size() - 1)))
	_park = int(args.get("park", "-1"))
	_carry = String(args.get("carry", "on")) != "off"
	_snap = String(args.get("snap", "on")) != "off"
	_platform = String(args.get("platform", "off")) != "off"
	_collider = String(args.get("collider", "animatable"))
	_spawn_player()
	if args.has("ride-test"):
		_run_ride_test(args)


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
	if path == "" or not FileAccess.file_exists(path):
		return null
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
# The lift
# ---------------------------------------------------------------------------

## Load the four meshes and wire the one that moves.
##
## THE CAR IS AN AnimatableBody3D AND THE SHAFT IS A StaticBody3D, and that
## split is the whole mechanism. `AnimatableBody3D` is Godot's body for geometry
## a script moves: with `sync_to_physics` the server integrates its motion
## between frames instead of teleporting it, so a capsule resting on it is
## resolved against a floor that is going somewhere rather than one that has
## already arrived. `--collider=static` builds the other one -- a StaticBody3D
## whose `position` is rewritten every frame -- so the difference between them is
## a measurement in docs/transport-4g.md rather than a quotation from the
## documentation.
func _build_lift() -> void:
	_origin = _v3(_man["origin"])
	_ux = _v3(_man["ux"])
	_uy = _v3(_man["uy"])
	_axis = _v3(_man["travel_axis"])
	_pivot = _v3(_man["pivot"])
	_landings = _man["landings"]

	if _visuals and String(_man.get("static_glb", "")) != "":
		var vis := _load_glb(String(_man["static_glb"]))
		if vis != null:
			add_child(vis)
	var col := _load_glb(String(_man["static_col_glb"]))
	var n_static := 0
	if col != null:
		add_child(col)
		for m in _meshes(col):
			m.create_trimesh_collision()
			m.visible = false
			n_static += 1

	_car = Node3D.new()
	_car.name = "Car"
	add_child(_car)
	# THE LEAVES ARE ON THE VISUAL CAR AND THE PANEL IS ON THE COLLISION ONE, so
	# the car mesh is loaded even headless: it is what says how far a leaf
	# travels, measured off the mesh by `transit_runtime.car_render` rather than
	# passed in as a number.
	var cv := _load_glb(String(_man.get("car_glb", "")))
	if cv != null:
		_car.add_child(cv)
		cv.visible = _visuals
		_wire_leaves(cv)
	var cc := _load_glb(String(_man.get("car_col_glb", "")))
	if cc != null:
		# A SIBLING OF THE VISUAL CAR, NOT A CHILD OF IT, and that is not
		# arrangement for its own sake. `AnimatableBody3D.sync_to_physics` asks
		# for notification of its own LOCAL transform; a body carried along by a
		# moving parent never changes its local transform, so the server would
		# see a body that had teleported rather than one that had moved -- the
		# exact failure this whole file is about, hidden inside the mechanism
		# meant to prevent it. Both are moved explicitly, by `_set_car`, from
		# the same number.
		_car_body = _make_car_body(cc)
		add_child(_car_body)
	_set_car(0.0)
	_car_prev = _car.position
	print("transit: lift loaded -- %d static collision meshes, car on a %s, "
		% [n_static, ("nothing" if _car_body == null
			else _car_body.get_class())]
		+ "%d door panel shape(s), %d leaves, %d landings"
		% [_panels.size(), _leaves.size(), _landings.size()])


## The car's collider. One shape per mesh in the collision glb, and the door
## panel kept aside so exactly it can be switched off -- `scripts/door.gd`'s own
## arrangement, and its reason: the piece that moves has to be separate or the
## runtime cannot move it without touching the rest.
func _make_car_body(root: Node) -> PhysicsBody3D:
	var body: PhysicsBody3D
	if _collider == "static":
		# The other implementation, and it is a real one rather than a
		# mutilation: a StaticBody3D whose transform is rewritten every frame is
		# what a lift looks like when nobody thought about a player standing in
		# it. It is a switch so the difference can be MEASURED instead of
		# asserted from the documentation.
		body = StaticBody3D.new()
	else:
		var ab := AnimatableBody3D.new()
		ab.sync_to_physics = true
		body = ab
	body.name = "CarBody"
	for m in _meshes(root):
		var cs := CollisionShape3D.new()
		cs.shape = m.mesh.create_trimesh_shape()
		cs.name = String(m.name)
		body.add_child(cs)
		if String(m.name).begins_with("liftdoorpanel"):
			_panels.append(cs)
		m.visible = false
	return body


## The two moving leaves, and how far and which way each goes.
##
## READ OFF THE MANIFEST, WHICH READ IT OFF THE MESH. `station/transit_runtime.py`
## builds the car at `open_fraction` 0 and 1 and takes the per-triangle
## difference, so the travel vector here is what `interior_kit.door_leaf` would
## actually have drawn. `walk.gd` takes a `--door-travel` number instead, which
## is a second description of a decision the generator already made.
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
	# HOW FAST A PRESSURE DOOR IS, FETCHED FROM THE FILE THAT DECIDES IT.
	var ds = load("res://scripts/door.gd")
	if ds != null:
		var probe = ds.new()
		_door_speed = float(probe.speed_m_s)
		probe.free()


func _apply_doors() -> void:
	for l in _leaves:
		l["node"].position = l["base"] + l["dir"] * l["travel"] * _door_open
	# Solid until the leaves have actually started moving -- `door.gd`'s rule and
	# its reason: disabling the panel the instant a body is in range lets a
	# player walk through a door that is still visibly shut.
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


## Shaft-local coordinates -- x across, y radially inward (up), z along the ship.
## `lift.unplace`, which is `lift.place`'s transpose because that map is a
## rotation.
func _local(p: Vector3) -> Vector3:
	var d := p - _origin
	return Vector3(d.dot(_ux), d.dot(_uy), p.z - _origin.z)


## Is the body standing in the car? Asked in the CAR'S OWN FRAME rather than by
## radius, because a radius cannot tell the car from the landing beside it.
func _in_car(p: Vector3) -> bool:
	var l := _local(p)
	var car: Dictionary = _man["car"]
	var hw := float(car["clear_w"]) / 2.0
	var hd := float(car["clear_d"]) / 2.0
	return (absf(l.x) < hw and absf(l.z) < hd
		and l.y > _car_y - 0.35 and l.y < _car_y + float(car["clear_h"]))


func _radius(p: Vector3) -> float:
	return sqrt(p.x * p.x + p.y * p.y)


## Which landing a radius is at, and how far off it is.
func _deck_at(r: float) -> Array:
	var best := -1
	var miss := 1e30
	for i in _landings.size():
		var d: float = absf(float(_landings[i]["walk_r_m"]) - r)
		if d < miss:
			miss = d
			best = i
	return [best, miss]


func _spawn_player() -> void:
	_player = CharacterBody3D.new()
	_player.set_script(load("res://scripts/player.gd"))
	# DOWN IS OUTWARD. A ring deck is the inside of a spun barrel exactly as the
	# drum is; `player.gravity_dir()` calls that mode "drum" and it is the right
	# one for any spun floor. The magnitude is THIS DECK'S own spin gravity --
	# `interior.decks_in_ring`'s `floor_g` times the schema's standard gravity --
	# not 9.81, because a lift on Blue ring 0 falls at 0.76 g.
	_player.gravity_mode = "drum"
	var lg: Dictionary = _landings[_from]
	_player.gravity_m_s2 = float(lg["floor_g"]) * float(_man["g0_m_s2"])
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	caps.height = 1.8
	caps.radius = 0.35
	shape.shape = caps
	shape.position = Vector3(0, 0.9, 0)
	_player.add_child(shape)
	_player.position = _v3(lg["stand"])
	add_child(_player)

	# PLATFORM VELOCITY IS OFF BY DEFAULT AND SNAP IS ON, and neither is a
	# preference. `move_and_slide` adds the velocity of the body a
	# CharacterBody3D is standing on; with the explicit carry ALSO applying that
	# displacement the body would travel twice as far as the car and leave
	# through its ceiling, so exactly one of the two mechanisms may be live at a
	# time. Snap keeps the engine default because that default is what a player
	# gets -- `player.gd` never touches it -- and a subject configured
	# differently from the shipped one is a subject nobody plays.
	if not _platform:
		_player.platform_floor_layers = 0
	if not _snap:
		_player.floor_snap_length = 0.0

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.02, 0.02, 0.03)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.6, 0.6, 0.62)
	e.ambient_light_energy = 0.6
	env.environment = e
	add_child(env)


func _run_ride_test(args: Dictionary) -> void:
	_t_settle = int(args.get("settle", "90"))
	_t_board = int(args.get("board", "480"))
	_t_alight = int(args.get("alight", "480"))
	_trace = int(args.get("trace", "0"))
	var key := "%d-%d" % [_from, _to]
	var rides: Dictionary = _man["rides"]
	if not rides.has(key):
		push_error("transit: no ride %s in the manifest" % key)
		get_tree().quit(2)
		return
	_ride_s = float(rides[key]["seconds"])
	_ride_from_y = _landing_y(_from)
	_ride_to_y = _landing_y(_to)
	# The car is waiting at the landing the body boards from -- unless the run is
	# the control that parks it somewhere else.
	_set_car(_landing_y(_park) if _park >= 0 else _ride_from_y)
	_car_prev = _car.position
	_car_y_phys = _car_y
	_car_lag = Vector3.ZERO
	_door_open = 1.0
	_apply_doors()
	_testing = true
	_state = ST_SETTLE
	_prev_pos = _player.global_position
	set_physics_process(true)


func _physics_process(delta: float) -> void:
	if _tramming:
		_tram_step(delta)
		return
	if not _testing:
		return
	_frame += 1
	_state_frame += 1

	# 1. THE VEHICLE MOVES FIRST, and the body is put back on its floor before it
	#    is asked to walk. The order matters: carrying after `move_and_slide` has
	#    already resolved the body against a floor that was not there yet is how
	#    a rider ends up a frame behind the car all the way up.
	_advance(delta)
	var carried := carry_body(_player)

	# 2. Then the body walks, on whatever it is standing on now.
	var steer := _steer()
	if steer.length_squared() > 0.0:
		_player.step(delta, Vector2.ZERO, false, false, steer)
	else:
		_player.step(delta, Vector2.ZERO, false, false)

	_measure(carried)
	if _trace > 0 and _frame % _trace == 0:
		var l := _local(_player.global_position)
		print("TRACE f=%d st=%d car_y=%.3f local=%.3f,%.3f,%.3f r=%.3f floor=%s door=%.2f"
			% [_frame, _state, _car_y, l.x, l.y, l.z,
				_radius(_player.global_position),
				str(_player.is_on_floor()).to_lower(), _door_open])
	_next_state()


## THE CARRY, AND IT IS THE ONE COPY OF IT.
##
## Called once a physics frame, AFTER the car has been commanded and BEFORE the
## body walks: carrying after `move_and_slide` has resolved the body against a
## floor that was not there yet is how a rider ends up a frame behind the car
## all the way up. Returns what the body was carried by, for the tape.
##
## `scripts/life.gd` calls this for a commuter; `_physics_process` below calls
## it for the ride test. Neither has its own copy of the one-frame lag argument
## in `_car_lag`'s declaration, which is the whole reason this is a function.
func carry_body(target: Node3D) -> Vector3:
	var carried := Vector3.ZERO
	var d := _car_lag
	if d.length_squared() > 0.0:
		if _carry and target != null and _in_car(target.global_position):
			target.global_position += d
			carried = d
			_carry_frames += 1
	# What the server will have applied by the time the body is resolved NEXT
	# frame, kept for that frame. `_car_y_phys` is the floor's physical height
	# now, and is what the stand-off is measured against -- measuring against the
	# command would report one frame of travel as an error every frame.
	var cmd := _car.position
	_car_y_phys = _car_y - _axis.dot(cmd - _car_prev)
	_car_lag = cmd - _car_prev
	_car_moved += _car_lag.length()
	_car_prev = cmd
	return carried


# ---------------------------------------------------------------------------
# THE EMBEDDED LIFT -- somebody else's clock, this file's mechanism
# ---------------------------------------------------------------------------

## Build the lift from a manifest another script is holding, and hand the clock
## to it. `static_col` overrides the shaft's collision -- `station/agenda.py`
## passes the SEALED shell for the control in which every landing aperture is
## shut, which is `lift.lift_collision(landings=False)`, the generator's own
## negative control rather than a slab invented for a test.
func embed_lift(man: Dictionary, static_col: String = "",
		visuals: bool = false, with_car: bool = true) -> void:
	_man = man
	_embedded = true
	_visuals = visuals
	if static_col != "":
		_man["static_col_glb"] = static_col
	if not with_car:
		# THE PRE-FIX CONTROL. Before this session `life.gd` had no vehicle at
		# all: the commuter reaches the landing and there is nothing in the
		# shaft. Removing the car is that build, and it is a removal of one
		# node rather than a different code path.
		_man["car_glb"] = ""
		_man["car_col_glb"] = ""
	_build_lift()
	set_physics_process(false)


## Command the car and its doors, in the units the timetable is written in:
## `y` is metres along the shaft's own travel axis, `door` is 0 shut to 1 open.
func lift_command(y: float, door: float) -> void:
	_set_car(y)
	_door_open = clampf(door, 0.0, 1.0)
	_apply_doors()


## The fraction of a ride's travel completed at fraction `u` of its time, out of
## the motion table `transit_runtime._ride_table` wrote and asserted against the
## Coriolis cap. The interpolation is `_interp`'s, so a caller cannot play the
## ride to a different curve than `--ride` does.
func lift_ride_fraction(key: String, u: float) -> float:
	var rides: Dictionary = _man.get("rides", {})
	if not rides.has(key):
		return clampf(u, 0.0, 1.0)
	return _interp(rides[key]["table"], u)


func lift_car_y() -> float:
	return _car_y


func lift_landing_y(i: int) -> float:
	return _landing_y(i)


func lift_in_car(p: Vector3) -> bool:
	return _in_car(p)


## The body's position in the CAR'S OWN FRAME, for a caller that has to report
## why `lift_in_car` said what it said. x across, y radially inward, z along.
func lift_local(p: Vector3) -> Vector3:
	return _local(p)


## Every clause of `_in_car`, spelled out. A boolean that says no is a verdict
## nobody can act on; this says which half-width it failed.
func lift_in_car_why(p: Vector3) -> String:
	var l := _local(p)
	var car: Dictionary = _man.get("car", {})
	var hw := float(car.get("clear_w", 0.0)) / 2.0
	var hd := float(car.get("clear_d", 0.0)) / 2.0
	var ch := float(car.get("clear_h", 0.0))
	return ("x %.3f<%.3f=%s z %.3f<%.3f=%s y %.3f in (%.3f,%.3f)=%s"
		% [absf(l.x), hw, str(absf(l.x) < hw).to_lower(),
			absf(l.z), hd, str(absf(l.z) < hd).to_lower(),
			l.y, _car_y - 0.35, _car_y + ch,
			str(l.y > _car_y - 0.35 and l.y < _car_y + ch).to_lower()])


## How far the body is standing off the car's floor, in the car's own frame and
## against the height the PHYSICS SERVER is holding rather than the one just
## commanded -- see `_car_lag`.
func lift_standoff(p: Vector3) -> float:
	return absf(_local(p).y - _car_y_phys)


func lift_car_moved_m() -> float:
	return _car_moved


func lift_carry_frames() -> int:
	return _carry_frames


func lift_door_open() -> float:
	return _door_open


## Where the vehicle is this frame, and it is the only place the clock is read.
func _advance(delta: float) -> void:
	match _state:
		ST_SHUT:
			_door_open = maxf(0.0, _door_open - delta / _door_seconds())
			_apply_doors()
		ST_RIDE:
			_ride_t += delta
			var u: float = clampf(_ride_t / _ride_s, 0.0, 1.0)
			var f := _interp(_man["rides"]["%d-%d" % [_from, _to]]["table"], u)
			_set_car(_ride_from_y + (_ride_to_y - _ride_from_y) * f)
		ST_OPEN:
			_door_open = minf(1.0, _door_open + delta / _door_seconds())
			_apply_doors()


## Linear interpolation into a motion table. The samples are evenly spaced in
## time by construction (`transit_runtime._ride_table`), and the chord error that
## introduces is asserted there against `collision.STEP_TOLERANCE_M` -- so this
## is allowed to assume the spacing and does not have to search.
func _interp(tab: Array, u: float) -> float:
	if u <= 0.0:
		return 0.0
	var n := tab.size() - 1
	if u >= 1.0 or n < 1:
		return float(tab[n][1])
	var x: float = u * float(n)
	var i: int = int(floor(x))
	return lerp(float(tab[i][1]), float(tab[i + 1][1]), x - float(i))


func _steer() -> Vector3:
	match _state:
		ST_SHUT:
			# KEEP WALKING TO THE MIDDLE WHILE THE DOORS CLOSE, and this is not a
			# flourish. `_in_car` becomes true the instant the capsule crosses
			# the door plane, so the body stopped 0.670 m from the car's centre
			# -- with a 0.35 m radius that put its shell 0.6 mm from the inner
			# face of the door panel the moment the panel went solid, and the
			# depenetration between the two broke floor contact for two frames
			# of every ride. Standing clear of a closing door is also simply what
			# a passenger does; the defect and the behaviour have one fix.
			return _v3(_landings[_from]["car_stand"]) - _player.global_position
		ST_BOARD:
			# AT WHERE THE CAR SHOULD BE, not at where it is. With the car parked
			# elsewhere the body must still walk into the doorway -- that is the
			# control, and steering at the car's actual position would walk it
			# somewhere safe instead.
			return _v3(_landings[_from]["car_stand"]) - _player.global_position
		ST_ALIGHT:
			return _v3(_landings[_to]["stand"]) - _player.global_position
	return Vector3.ZERO


func _measure(carried: Vector3) -> void:
	var p := _player.global_position
	var on := _player.is_on_floor()
	# THE CARRY IS NOT TRAVEL. A body standing still in a moving car has gone
	# somewhere, so the carried displacement counts; what must NOT count is the
	# same metre being added twice, once as carry and once as the walk that
	# followed it, so the step is measured once, from the position before the
	# carry.
	var step := p.distance_to(_prev_pos)
	var dr: float = absf(_radius(p) - _radius(_prev_pos))
	if on:
		_floor_m += step
		_radial_floor += dr
	else:
		_air_m += step
		_radial_air += dr
		_off += 1
	_frames += 1
	_prev_pos = p
	if _state == ST_RIDE:
		if _ride_frames == 0:
			_ride_door_z = float(_man["car"]["clear_d"]) / 2.0 - (
				absf(_local(p).z) + 0.35)
		_ride_frames += 1
		if not on:
			_ride_off += 1
			if _ride_off_first < 0:
				_ride_off_first = _ride_frames
			_ride_off_last = _ride_frames
		if _in_car(p):
			_standoff_max = maxf(_standoff_max, absf(_local(p).y - _car_y_phys))


func _next_state() -> void:
	match _state:
		ST_SETTLE:
			if _state_frame >= _t_settle:
				_r_settle = _radius(_player.global_position)
				var dk := _deck_at(_r_settle)
				print("transit: settled at deck %d (r=%.3f m, %.0f mm off the "
					% [int(_landings[dk[0]]["deck"]), _r_settle,
						float(dk[1]) * 1000.0]
					+ "landing), on_floor=%s, %.2f m from the car"
					% [str(_player.is_on_floor()).to_lower(),
						_player.global_position.distance_to(
							_v3(_landings[_from]["car_stand"]))])
				_go(ST_BOARD)
		ST_BOARD:
			# YOU CANNOT BOARD A CAR THAT IS NOT THERE, and the first version of
			# this said otherwise. With the car parked at another landing the
			# body walks into the doorway and falls 10.8 m down the shaft --
			# straight through the car's own ceiling, which faces outward and is
			# therefore a back face to something coming from above -- and lands
			# on the car's floor. `_in_car` was then true and the run reported
			# `boarded=true` with a fall of -3 mm, so the control did not fire on
			# a run that had done exactly what the control claims. Being inside
			# the car is not boarding; boarding is the car being at YOUR landing
			# and you walking into it.
			if _park >= 0:
				pass
			elif _in_car(_player.global_position) and _player.is_on_floor():
				_boarded = true
				_r_board = _radius(_player.global_position)
				print("transit: boarded at deck %d after %d frames"
					% [int(_landings[_from]["deck"]), _state_frame])
				_go(ST_SHUT)
			if _state_frame >= _t_board:
				# WITH THE CAR PARKED SOMEWHERE ELSE THERE IS NOTHING TO RIDE.
				# The control's whole claim is what happens to a body that walks
				# at a doorway with no car behind it, so it runs the board window
				# out and reports where the body ended up.
				_r_board = _radius(_player.global_position)
				if _park >= 0:
					_finish()
				else:
					_go(ST_SHUT)
		ST_SHUT:
			if _door_open <= 0.0:
				_go(ST_RIDE)
		ST_RIDE:
			if _ride_t >= _ride_s:
				_set_car(_ride_to_y)
				print("transit: rode %.3f m of radius in %d frames (%.3f s)"
					% [absf(_ride_to_y - _ride_from_y), _ride_frames, _ride_t])
				_go(ST_OPEN)
		ST_OPEN:
			if _door_open >= 1.0:
				_go(ST_ALIGHT)
		ST_ALIGHT:
			var l := _local(_player.global_position)
			# Out of the shaft: past the bore line, in the lobby, on the floor.
			if (absf(l.z) > float(_man["bore_hd"]) + 0.6
					and _player.is_on_floor()):
				_alighted = true
				_finish()
			elif _state_frame >= _t_alight:
				_finish()


func _go(s: int) -> void:
	if s == ST_RIDE:
		# The claim "shut before it moves", asserted rather than assumed.
		_doors_shut_before_move = _door_open <= 0.0
		_ride_t = 0.0
	_state = s
	_state_frame = 0


func _finish() -> void:
	_state = ST_DONE
	set_physics_process(false)
	var p := _player.global_position
	var r_end := _radius(p)
	var dk0 := _deck_at(_r_board if _boarded else _r_settle)
	var dk1 := _deck_at(r_end)
	var want: float = absf(float(_landings[_from]["walk_r_m"])
		- float(_landings[_to]["walk_r_m"]))
	print(("RIDETEST from_landing=%d from_deck=%d to_landing=%d to_deck=%d "
		+ "start_deck=%d end_deck=%d start_miss_mm=%.0f end_miss_mm=%.0f "
		+ "boarded=%s alighted=%s r_start=%.4f r_end=%.4f fell_m=%.4f "
		+ "want_rise_m=%.4f radial_floor_m=%.4f radial_air_m=%.4f "
		+ "floor_m=%.3f air_m=%.3f offfloor=%d/%d ride_offfloor=%d/%d "
		+ "standoff_max_mm=%.2f carry_frames=%d car_moved_m=%.4f "
		+ "ride_frames=%d door_z_m=%.4f "
		+ "ride_off_first=%d ride_off_last=%d "
		+ "doors_shut_before_move=%s door_open_end=%.2f ride_s=%.4f "
		+ "ride_t=%.4f carry=%s snap=%s platform=%s collider=%s "
		+ "snap_m=%.3f park=%d") % [
		_from, int(_landings[_from]["deck"]), _to, int(_landings[_to]["deck"]),
		int(_landings[dk0[0]]["deck"]), int(_landings[dk1[0]]["deck"]),
		float(dk0[1]) * 1000.0, float(dk1[1]) * 1000.0,
		str(_boarded).to_lower(), str(_alighted).to_lower(),
		(_r_board if _boarded else _r_settle), r_end,
		r_end - _r_settle,
		want, _radial_floor, _radial_air, _floor_m, _air_m,
		_off, _frames, _ride_off, _ride_frames,
		_standoff_max * 1000.0, _carry_frames, _car_moved,
		_ride_frames, _ride_door_z,
		_ride_off_first, _ride_off_last,
		str(_doors_shut_before_move).to_lower(), _door_open,
		_ride_s, _ride_t,
		("on" if _carry else "off"), ("on" if _snap else "off"),
		("on" if _platform else "off"), _collider,
		_player.floor_snap_length, _park])
	get_tree().quit(0)


# ---------------------------------------------------------------------------
# The tram -- the phase parameter nothing ever changed
# ---------------------------------------------------------------------------

var _tramming := false
var _tram_cars: Array = []
var _tram_t := 0.0
var _tram_dt := 0.0
var _tram_frames := 0
var _tram_frame := 0
var _tram_samples := 12
var _tram_taken := 0


func _build_tram() -> void:
	var cars := _load_glb(String(_man["cars_glb"]))
	if cars == null:
		push_error("transit: could not load %s" % _man["cars_glb"])
		get_tree().quit(2)
		return
	add_child(cars)
	var z0: Array = _man["car_z0"]
	for m in _meshes(cars):
		var n := String(m.name)
		if not n.begins_with("tramcar_"):
			continue
		var i := int(n.substr(8))
		while _tram_cars.size() <= i:
			_tram_cars.append(null)
		m.position = Vector3(0, 0, float(z0[i]))
		_tram_cars[i] = m
	print("transit: tram loaded -- %d cars of %.0f m on %s, %.0f m apart"
		% [_tram_cars.size(), float(_man["car_length_m"]),
			String(_man["sector"]), float(_man["spacing_m"])])


func _run_tram_test(args: Dictionary) -> void:
	# A TIME LAPSE, AND IT SAYS SO. One cycle of this line is 137 s and the test
	# runs two of them; waiting that long in real time would buy nothing, because
	# a car's position is a function of the clock and no physics body is involved.
	# The motion law still executes once per physics frame -- what is compressed
	# is the clock, not the number of steps.
	_tram_frames = int(args.get("frames", "600"))
	var span := float(args.get("span", str(2.0 * float(_man["cycle_s"]))))
	_tram_dt = span / float(_tram_frames)
	_tram_samples = int(args.get("samples", "12"))
	_tramming = true
	print("transit: tram test -- %.1f s of service in %d physics frames "
		% [span, _tram_frames]
		+ "(x%.0f time lapse), %d samples" % [_tram_dt * 60.0, _tram_samples])
	set_physics_process(true)


## Where the train is at time t, as a phase. `tram.guideway_cars` takes a phase
## and places the whole train; this turns the line's TIMETABLE into one. A car
## covers its own spacing in `cycle_s`, which the manifest derives from
## `transit.line_report` -- so many legs of `leg_s` plus a `DWELL_S` at each
## stop -- and within a leg it follows `transit.ride_profile`'s jerk-limited
## ramp, tabulated offline.
func _tram_phase(t: float) -> float:
	var cyc := float(_man["cycle_s"])
	var legs := float(_man["legs_per_spacing"])
	var whole: float = floor(t / cyc)
	var u: float = t - whole * cyc
	var per: float = cyc / legs
	var k: float = floor(u / per)
	var v: float = u - k * per
	var leg_s := float(_man["leg_s"])
	var f := 1.0 if v >= leg_s else _interp(_man["leg_table"], v / leg_s)
	return whole + (k + f) / legs


func _tram_z(i: int, phase: float) -> float:
	var count := float(_man["count"])
	var z: float = float(_man["z0"]) + float(_man["spacing_m"]) * fposmod(
		float(i) + 0.5 + phase, count)
	var half: float = float(_man["car_length_m"]) / 2.0
	return clampf(z, float(_man["z0"]) + half, float(_man["z1"]) - half)


func _tram_step(_delta: float) -> void:
	_tram_frame += 1
	_tram_t += _tram_dt
	var ph := _tram_phase(_tram_t)
	for i in _tram_cars.size():
		if _tram_cars[i] != null:
			_tram_cars[i].position = Vector3(0, 0, _tram_z(i, ph))
	var want: int = int(float(_tram_frame) * float(_tram_samples)
		/ float(_tram_frames))
	if want > _tram_taken:
		_tram_taken = want
		var s := "TRAMSAMPLE t=%.4f phase=%.6f" % [_tram_t, ph]
		for i in _tram_cars.size():
			s += " car%d_z=%.4f" % [i, _tram_cars[i].position.z]
		print(s)
	if _tram_frame >= _tram_frames:
		set_physics_process(false)
		print("TRAMTEST cars=%d frames=%d span_s=%.2f end_phase=%.6f"
			% [_tram_cars.size(), _tram_frame, _tram_t, ph])
		get_tree().quit(0)
