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
## Where to put the body, in world metres. The spawn is a CLAIM -- "a person can
## stand here" -- and the test's first assertion is that the claim is true.
@export var spawn: Vector3 = Vector3.ZERO
@export var gravity_mode: String = "deck"
@export var gravity_m_s2: float = 9.81

var _player: CharacterBody3D
var _static: StaticBody3D


func _ready() -> void:
	var args := _args()
	if args.has("glb"):
		glb_path = args["glb"]
	if args.has("spawn"):
		spawn = _vec(args["spawn"])
	if args.has("gravity-mode"):
		gravity_mode = args["gravity-mode"]
	if args.has("gravity"):
		gravity_m_s2 = float(args["gravity"])

	if not _load_level():
		push_error("walk: could not load %s" % glb_path)
		get_tree().quit(2)
		return
	_spawn_player()

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
	if glb_path == "" or not FileAccess.file_exists(glb_path):
		return false
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(glb_path, state) != OK:
		return false
	var scene := doc.generate_scene(state)
	if scene == null:
		return false
	add_child(scene)
	var n := 0
	for m in _all_meshes(scene):
		m.create_trimesh_collision()
		n += 1
	print("walk: %d mesh instances given trimesh collision" % n)
	return n > 0


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
	_testing = true
	set_physics_process(true)


var _testing := false
var _frame := 0
var _t_settle := 150
var _t_walk := 120
var _rest := Vector3.ZERO
var _on_floor := false


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
		if _frame == _t_settle:
			_rest = _player.global_position
			_on_floor = _player.is_on_floor()
		return
	_player.step(delta, Vector2(0, 1), false, false)
	var n := _frame - _t_settle
	if n == _t_walk:
		_moved_1s = _player.global_position.distance_to(_rest)
	if n >= _t_walk * 5:
		var far := _player.global_position.distance_to(_rest)
		var fell: bool = (not _on_floor) and _rest.distance_to(spawn) > 50.0
		print("WALKTEST rest=%.3f,%.3f,%.3f on_floor=%s fell=%s moved_1s=%.3f moved_5s=%.3f drop=%.3f" % [
			_rest.x, _rest.y, _rest.z, str(_on_floor).to_lower(),
			str(fell).to_lower(), _moved_1s, far,
			spawn.distance_to(_rest)])
		get_tree().quit(0)


var _moved_1s := 0.0
