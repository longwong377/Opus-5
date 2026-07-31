extends Node3D
## The walkable build. Loads a piece of the station, gives it collision, and
## puts a player on it.
##
## WHAT THIS EXISTS TO END: as of session 3u this project had 118 locations with
## geometry, materials and measured lighting, and no way to stand in any of
## them. `CollisionShape` appeared nowhere. Every render was a photograph taken
## by a camera that flew through walls.
##
## HEADLESS BY DESIGN. There is no GPU and no human here, so this scene must be
## drivable with no window and no input device: `--headless --walk-test` steps
## the physics itself, moves the body with a synthetic wish vector, and prints
## a verdict `station/walkable.py` parses. A player controller nobody can test
## is one that silently stops working, which is how the render path rotted
## between sessions 2j and 3k.

@export var glb_path: String = ""
## A separate, simplified mesh to collide against. See `station/collision.py`:
## the render corridor carries a 66 mm lighting channel down its centreline and
## 22 mm grid tiles either side of it, and a capsule dropped on that stands
## perfectly still while reporting `on_floor=true`. A player walks on a surface
## built for walking on. Empty means collide against the visible mesh, which is
## right for a single room and wrong for a deck.
@export var collision_path: String = ""
## Where to put the body, in world metres. The spawn is a CLAIM -- "a person can
## stand here" -- and the test's first assertion is that the claim is true.
@export var spawn: Vector3 = Vector3.ZERO
@export var gravity_mode: String = "deck"
@export var gravity_m_s2: float = 9.81
## How far each pressure door leaf travels when it opens, in metres -- half the
## aperture width, since two leaves part on the centreline. From
## `interior_kit.PROVISIONAL["door_width_m"]`, passed in rather than repeated.
@export var door_travel_m: float = 0.75

var _doors: Node3D

var _player: CharacterBody3D
var _static: StaticBody3D


func _ready() -> void:
	var args := _args()
	if args.has("glb"):
		glb_path = args["glb"]
	if args.has("collision"):
		collision_path = args["collision"]
	if args.has("spawn"):
		spawn = _vec(args["spawn"])
	if args.has("gravity-mode"):
		gravity_mode = args["gravity-mode"]
	if args.has("gravity"):
		gravity_m_s2 = float(args["gravity"])
	if args.has("door-travel"):
		door_travel_m = float(args["door-travel"])

	if not _load_level():
		push_error("walk: could not load %s" % glb_path)
		get_tree().quit(2)
		return
	_spawn_player()
	if _doors != null:
		_doors.watch(_player)

	if args.has("walk-test"):
		_run_walk_test(args)


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


func _vec(s: String) -> Vector3:
	var p := s.split(",")
	if p.size() != 3:
		return Vector3.ZERO
	return Vector3(float(p[0]), float(p[1]), float(p[2]))


## Load the glb and give every mesh in it a trimesh collider.
##
## TRIMESH, NOT CONVEX. A station interior is concave -- rooms are holes in
## solid, not solids -- and a convex hull of a room is a block the player
## bounces off the outside of. `create_trimesh_collision` is the only correct
## choice here and it is also the expensive one; that is a runtime streaming
## problem, not a reason to use the wrong shape.
func _load_level() -> bool:
	var scene := _load_glb(glb_path)
	if scene == null:
		return false
	add_child(scene)

	# WHICH MESH IS THE FLOOR. With a collision mesh supplied, the visible one
	# gets no colliders at all and the proxy is invisible -- that separation is
	# the whole point, and giving both of them shapes would put the millimetre
	# detail straight back in the body's way.
	if collision_path != "":
		var col := _load_glb(collision_path)
		if col == null:
			push_error("walk: could not load collision %s" % collision_path)
			return false
		add_child(col)
		var c := 0
		for m in _all_meshes(col):
			m.create_trimesh_collision()
			m.visible = false
			c += 1
		print("walk: %d collision meshes (proxy), %d visual meshes (no collision)"
			% [c, _all_meshes(scene).size()])
		_wire_doors(scene, col)
		return c > 0

	var n := 0
	for m in _all_meshes(scene):
		m.create_trimesh_collision()
		n += 1
	print("walk: %d mesh instances given trimesh collision" % n)
	return n > 0


## Give the deck its doors. `--no-doors` leaves them out, which is the NEGATIVE
## CONTROL for the walk test: with the doors inert the closed panels stay solid
## and a body must NOT be able to reach the room. A test that only ever runs the
## working configuration cannot tell a door that opens from a hole in a wall.
func _wire_doors(scene: Node, col: Node) -> void:
	if _args().has("no-doors"):
		print("walk: doors DISABLED (negative control)")
		return
	_doors = Node3D.new()
	_doors.name = "Doors"
	_doors.set_script(load("res://scripts/door.gd"))
	add_child(_doors)
	var n: int = _doors.collect(scene, col, door_travel_m)
	print("walk: %d doors wired" % n)


func _load_glb(path: String) -> Node:
	if path == "" or not FileAccess.file_exists(path):
		return null
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		return null
	return doc.generate_scene(state)


func _all_meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		out.append_array(_all_meshes(c))
	return out


func _spawn_player() -> void:
	_player = CharacterBody3D.new()
	_player.set_script(load("res://scripts/player.gd"))
	_player.gravity_mode = gravity_mode
	_player.gravity_m_s2 = gravity_m_s2
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	# 1.8 m tall, 0.35 m radius: a person, and the same stature the render
	# harness stands its cameras at.
	caps.height = 1.8
	caps.radius = 0.35
	shape.shape = caps
	shape.position = Vector3(0, 0.9, 0)
	_player.add_child(shape)
	_player.position = spawn
	add_child(_player)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.02, 0.02, 0.03)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.6, 0.6, 0.62)
	e.ambient_light_energy = 0.6
	env.environment = e
	add_child(env)


## Drive the body with no input device and print a verdict.
##
## Every number here is a CLAIM A PLAYER WOULD NOTICE, not a proxy:
##   settled   -- the body came to rest on something instead of falling forever
##   walked    -- pushing forward for a second actually moved it
##   on_floor  -- it is standing on geometry, not hovering or wedged
##   blocked   -- walking into a wall stops it, so the level is solid both ways
func _run_walk_test(args: Dictionary) -> void:
	_t_settle = int(args.get("settle", "150"))
	_t_walk = int(args.get("steps", "120"))
	_t_traverse = int(args.get("traverse", "0"))
	if args.has("goto"):
		_goto = _vec(args["goto"])
		_have_goto = true
	_door_key = String(args.get("door-key", ""))
	_trace = int(args.get("trace", "0"))
	_testing = true
	set_physics_process(true)


var _testing := false
var _frame := 0
var _t_settle := 150
var _t_walk := 120
var _trace := 0
var _rest := Vector3.ZERO
var _on_floor := false


## Why a body is not moving, in the only terms that can answer it: what it was
## told to do, what it did, and what stopped it. A walk test that only prints
## `moved=0.001` says a body is stuck and nothing about why -- three sessions of
## this project were spent guessing at exactly that class of question from a
## single summary number.
func _trace_line(tag: String) -> void:
	var p := _player.global_position
	var cols := ""
	for i in _player.get_slide_collision_count():
		var c := _player.get_slide_collision(i)
		var who := "?"
		var o = c.get_collider()
		if o != null:
			who = str(o.name)
		cols += " hit[n=%.2f,%.2f,%.2f d=%.3f %s]" % [
			c.get_normal().x, c.get_normal().y, c.get_normal().z,
			c.get_depth(), who]
	print("TRACE %s f=%d p=%.3f,%.3f,%.3f r=%.3f v=%.3f,%.3f,%.3f |v|=%.3f floor=%s wall=%s fn=%.2f,%.2f,%.2f%s" % [
		tag, _frame, p.x, p.y, p.z, sqrt(p.x * p.x + p.y * p.y),
		_player.velocity.x, _player.velocity.y, _player.velocity.z,
		_player.velocity.length(),
		str(_player.is_on_floor()).to_lower(),
		str(_player.is_on_wall()).to_lower(),
		_player.get_floor_normal().x, _player.get_floor_normal().y,
		_player.get_floor_normal().z, cols])


## THE TEST RUNS ON REAL PHYSICS FRAMES, and the first version did not. It
## called `_player.step()` in a plain `for` loop, which invokes
## `move_and_slide()` while the physics server has not advanced -- so the body
## never actually moves and the test reported `moved_1s=0.000` for a body
## standing on open floor. That is a false NEGATIVE, which is the safer
## direction to fail but still a lie about what the build does. Godot integrates
## motion between physics frames; a controller test has to let them happen.
func _physics_process(delta: float) -> void:
	if not _testing:
		return
	_frame += 1
	if _frame <= _t_settle:
		_player.step(delta, Vector2.ZERO, false, false)
		if _trace > 0 and _frame % _trace == 0:
			_trace_line("settle")
		if _frame == _t_settle:
			_rest = _player.global_position
			_on_floor = _player.is_on_floor()
		return
	# SWEEP THE HEADING. The first version walked one direction -- the body's
	# own "forward", which is derived from a world axis and has nothing to do
	# with which way the corridor runs. On a ring deck that pointed along the
	# station's spine, into a wall 1.5 m away, and the test reported a body that
	# could not move on a floor it was standing on perfectly well. The question
	# is "can this body walk", not "can it walk north", so it tries four
	# headings and keeps the best.
	#
	# EACH LEG STARTS FROM THE REST POSE. It did not, and the legs were
	# therefore not independent: leg 0 walked the body into the axial wall and
	# left it there, so leg 1 measured a body already jammed against something
	# and scored the corridor's own length as zero. A heading test whose result
	# depends on the previous heading is not a heading test.
	var leg := int(_t_walk / 2)
	var n := _frame - _t_settle
	if _phase == 0:
		var which := int((n - 1) / leg)
		if which >= 4:
			_phase = 1
			_best_yaw = _yaw_of_leg
			_player.global_position = _rest
			_player.velocity = Vector3.ZERO
			_player.set_yaw(_best_yaw)
			_traverse_from = _rest
			_traverse_prev = _rest
			return
		if which != _heading:
			_heading = which
			_player.global_position = _rest
			_player.velocity = Vector3.ZERO
			_player.set_yaw(float(which) * PI * 0.5)
			_leg_from = _rest
		_player.step(delta, Vector2(0, 1), false, false)
		if _trace > 0 and n % _trace == 0:
			_trace_line("walk%d" % which)
		var d := _player.global_position.distance_to(_leg_from)
		_leg_m[which] = maxf(_leg_m[which], d)
		if d > _moved_1s:
			_moved_1s = d
			_yaw_of_leg = float(which) * PI * 0.5
		return

	# TRAVERSE. Four one-second nudges prove a body is not wedged; they do not
	# prove you can GO ANYWHERE, which is the milestone this is for. Walk the
	# best heading for as long as asked and report the distance covered, the
	# straight-line displacement, and whether the floor was ever lost -- a body
	# that walks 80 m and falls off at 60 has not crossed the deck.
	#
	# With `--goto`, steer at a named place instead of holding a heading. That
	# is the actual W2 claim -- "two named locations joined by real walkable
	# geometry" -- and it is a strictly harder question than "did it move",
	# because it fails when the route is blocked rather than when the body is.
	if _have_goto:
		_player.step(delta, Vector2.ZERO, false, false,
			_goto - _player.global_position)
	else:
		_player.step(delta, Vector2(0, 1), false, false)
	var p := _player.global_position
	var gd := p.distance_to(_goto)
	if gd < _goto_best:
		_goto_best = gd
	_path_m += p.distance_to(_traverse_prev)
	_traverse_prev = p
	if not _player.is_on_floor():
		_off_floor += 1
	if _trace > 0 and n % _trace == 0:
		_trace_line("traverse")
	if n >= leg * 4 + _t_traverse:
		var fell: bool = (not _on_floor) and _rest.distance_to(spawn) > 50.0
		var goto_s := ""
		if _have_goto:
			goto_s = " goto_start_m=%.2f goto_best_m=%.2f goto_end_m=%.2f" % [
				_traverse_from.distance_to(_goto), _goto_best, gd]
			if _doors != null:
				goto_s += " door_open=%.2f" % _doors.openness(_door_key)
		print(("WALKTEST rest=%.3f,%.3f,%.3f on_floor=%s fell=%s moved_1s=%.3f "
			+ "drop=%.3f legs=%.2f/%.2f/%.2f/%.2f traverse_m=%.2f net_m=%.2f "
			+ "offfloor=%d/%d%s") % [
			_rest.x, _rest.y, _rest.z, str(_on_floor).to_lower(),
			str(fell).to_lower(), _moved_1s, spawn.distance_to(_rest),
			_leg_m[0], _leg_m[1], _leg_m[2], _leg_m[3],
			_path_m, _traverse_from.distance_to(p), _off_floor, _t_traverse,
			goto_s])
		get_tree().quit(0)


var _moved_1s := 0.0
var _heading := -1
var _leg_from := Vector3.ZERO
var _leg_m := [0.0, 0.0, 0.0, 0.0]
var _phase := 0
var _yaw_of_leg := 0.0
var _best_yaw := 0.0
var _t_traverse := 0
var _traverse_from := Vector3.ZERO
var _traverse_prev := Vector3.ZERO
var _path_m := 0.0
var _off_floor := 0
var _goto := Vector3.ZERO
var _have_goto := false
var _goto_best := 1e30
var _door_key := ""
