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
##
## AND IT IS DRESSED. Until session 3w this scene applied no materials and made
## no lights: it loaded a .glb, collided it, and stood a body on it under a flat
## grey ambient, while `tools/export_scene.py` carried 429 material rules and
## sixteen measured fittings used only for screenshots. `scripts/dress_scene.gd`
## binds the same table and lights the same fittings HERE, so the build a player
## walks in and the build the renders are taken from are one build. Dressing
## runs in the headless walk test too, on purpose: a step that only ever runs in
## the configuration nobody checks is a step that rots, and this file has that
## exact scar twice already. `--no-dress` is the control.

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
## The cast list written beside the deck mesh -- see `station/walkable.py`.
@export var actors_path: String = ""
## The corridor crowd: placements against the shared body library, and the
## library itself. Separate from `actors_path` because they are different
## things -- an actor is baked into the deck mesh, a walker is an instance.
@export var crowd_path: String = ""
@export var crowd_glb: String = ""
## The LOD ladder for the crowd: `max_m:lod` pairs nearest-first, and one glb
## per rung. A baked walker had one LOD because a static mesh has no other
## option; an instanced one is a transform, so the runtime picks per person.
@export var crowd_ladder: String = ""
@export var crowd_glbs: String = ""
var _people: Node3D
## The interactables sidecar written beside the deck mesh -- see
## `station/interact.py`. `{group, place, token, verb, pressable, label}` per
## declared interactable, derived from `directory.PLACES["interacts"]`. The verb
## table lives in Python and is NOT repeated here.
@export var interact_path: String = ""
var _interact: Node3D
## The group the headless test is to walk up to and use, and whether it has.
var _use_group := ""
var _used_ok := false
var _dress: Node
var _lights: Node3D

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
	if args.has("actors"):
		actors_path = args["actors"]
	if args.has("crowd"):
		crowd_path = args["crowd"]
	if args.has("crowd-glb"):
		crowd_glb = args["crowd-glb"]
	if args.has("crowd-ladder"):
		crowd_ladder = args["crowd-ladder"]
	if args.has("crowd-glbs"):
		crowd_glbs = args["crowd-glbs"]

	if args.has("interact"):
		interact_path = args["interact"]
	_use_group = String(args.get("use-group", ""))

	if not _load_level():
		push_error("walk: could not load %s" % glb_path)
		get_tree().quit(2)
		return
	_spawn_player()
	if _doors != null:
		_doors.watch(_player)
	if _people != null:
		_people.watch(_player)
	if _interact != null:
		_interact.watch(_player)
		_interact.doors(_doors)
		print("walk: %d interactables wired, %d pressable (%s)"
			% [_interact.count(), _interact.pressable_count(),
				_interact.verb_report()])
		var miss: Array[String] = _interact.missing()
		if not miss.is_empty():
			print("walk: %d declared interactable(s) have a span in the "
				% miss.size() + "generator and NO MESH in the glb -- their "
				+ "parts claimed every triangle: " + ", ".join(miss))

	if args.has("walk-test"):
		_run_walk_test(args)
	elif args.has("shot"):
		_run_shot(args)


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
	_dress_level(scene)

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
		_wire_people(scene)
		_wire_interact(scene)
		return c > 0

	var n := 0
	for m in _all_meshes(scene):
		m.create_trimesh_collision()
		n += 1
	print("walk: %d mesh instances given trimesh collision" % n)
	return n > 0


## Bind the materials and light the fittings -- see `scripts/dress_scene.gd`.
##
## BEST EFFORT, LOUDLY. Dressing must never be able to fail a walk test: this
## scene's first job is to answer "can a player stand up in this station", and
## that answer does not depend on what colour the wall is. But a look that
## quietly stops working is this project's most-repeated defect -- the render
## path rotted for eleven sessions and every gate stayed green -- so failure
## prints `dress: FAILED` and the reason, and the summary line is printed on
## EVERY run, including the headless one CI reads.
##
## `--no-dress` is the control. With it the build is what it was before session
## 3w: grey geometry under a flat ambient, no sources. If a render with dressing
## and a render without it look the same, this file is doing nothing.
func _dress_level(scene: Node) -> void:
	if _args().has("no-dress"):
		print("walk: dressing DISABLED (control) -- no materials, no lights")
		return
	_dress = Node.new()
	_dress.name = "Dress"
	_dress.set_script(load("res://scripts/dress_scene.gd"))
	add_child(_dress)
	if not _dress.prepare():
		push_error("walk: dress FAILED -- " + ", ".join(_dress.problems))
		print("dress: FAILED -- %s" % ", ".join(_dress.problems))
	var m: Dictionary = _dress.bind(scene)
	_dress.release()
	var un: PackedStringArray = m["unmatched"]
	print("dress: %d/%d meshes MATERIALLED, %d group(s) on the glTF fallback%s"
		% [m["bound"], m["meshes"], un.size(),
			("" if un.is_empty() else ": " + ", ".join(un))])
	# A rule that resolves to null is worse than no rule: the summary above
	# reads as a success and the frame is the glTF default. It happens whenever
	# `godot/.godot/` is absent (it is gitignored), and the engine only says so
	# in a wall of [ext_resource] parse errors nobody reads.
	var nul: PackedStringArray = m["ruled_but_null"]
	if not nul.is_empty():
		push_error("walk: %d group(s) matched a material rule that resolved to "
			% nul.size() + "NULL -- the material library did not load")
		print("dress: %d group(s) MATCHED A RULE THAT IS NULL -- run "
			% nul.size() + "`station/materials.py --export` and let Godot "
			+ "import once; the frame is the glTF fallback: %s"
			% ", ".join(nul.slice(0, 6)))

	_lights = Node3D.new()
	_lights.name = "Fittings"
	add_child(_lights)
	var energy: float = _dress.consts.get("fixture_energy", 3.0)
	var lit: Dictionary = _dress.light(scene, _lights, energy, spawn)
	print("dress: %d light sources at energy %.2f from %s, %d casting shadows"
		% [lit["lights"], energy, str(lit["by_fitting"]), lit["shadows"]])
	var eo: PackedStringArray = lit["emissive_only"]
	# Only claim "measured" when the measurements actually loaded. With the
	# table empty EVERY fitting looks emissive-only, and printing the reassuring
	# sentence over a failed parse is how a broken step reads as a working one.
	if not eo.is_empty() and not _dress.spec.is_empty():
		# Not a warning. Absence from FIXTURE_LIGHTING is a MEASUREMENT -- the
		# pilaster strip is the brightest thing on the wall and lights nothing.
		print("dress: emissive-only (measured, not missing): %s" % ", ".join(eo))
	var ext: PackedStringArray = lit["extended"]
	if not ext.is_empty():
		print("dress: sampled as extended fittings: %s" % ", ".join(ext))


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


## Give the deck its inhabitants. `--no-people` leaves them inert, which is the
## negative control: with nobody reacting the turn must read ZERO. A reaction
## test that only runs the working configuration cannot tell a person who turns
## from a statue that happened to be facing the right way.
func _wire_people(scene: Node) -> void:
	if actors_path == "" or not FileAccess.file_exists(actors_path):
		return
	if _args().has("no-people"):
		print("walk: people DISABLED (negative control)")
		return
	var f := FileAccess.open(actors_path, FileAccess.READ)
	var actors = JSON.parse_string(f.get_as_text())
	if typeof(actors) != TYPE_ARRAY:
		return
	_people = Node3D.new()
	_people.name = "People"
	_people.set_script(load("res://scripts/npc.gd"))
	add_child(_people)
	var n: int = _people.collect(scene, actors)
	print("walk: %d people wired of %d in the cast list" % [n, actors.size()])
	_wire_crowd()


## The corridor's walkers. They are not in the deck mesh at all -- their bodies
## come from `crowd_lod<N>.glb`, 112 shared meshes for the whole station, and
## this list says where each one is and which phase they are on.
func _wire_crowd() -> void:
	if crowd_path == "" or (crowd_glb == "" and crowd_glbs == ""):
		return
	if _args().has("no-crowd"):
		print("walk: crowd DISABLED (negative control)")
		return
	if not FileAccess.file_exists(crowd_path):
		return
	var f2 := FileAccess.open(crowd_path, FileAccess.READ)
	var rows = JSON.parse_string(f2.get_as_text())
	if typeof(rows) != TYPE_ARRAY or rows.is_empty():
		return
	# One library per rung of the ladder. `crowd_glbs` is the new form and
	# `crowd_glb` the single-rung one it replaces; both are accepted so a
	# command written before the ladder existed still runs.
	var paths: Array = ([] if crowd_glbs == ""
		else Array(crowd_glbs.split(",")))
	if paths.is_empty() and crowd_glb != "":
		paths = [crowd_glb]
	var libs: Array = []
	for pth in paths:
		if not FileAccess.file_exists(String(pth)):
			continue
		var l := _load_glb(String(pth))
		if l != null:
			libs.append(l)
	if libs.is_empty():
		push_error("walk: could not load any crowd library")
		return
	_people.set_crowd_ladder(crowd_ladder)
	var n2: int = _people.build_crowd_multi(libs, rows)
	print("walk: %d walkers instanced across %d LOD libraries"
		% [n2, libs.size()])


## Give the deck the things a player can USE. `--no-interact` leaves them out,
## which is a control on this file; the control on the CONTENT is stronger and
## lives in `station/walkable.py --use`, which strips the target object's
## triangles out of the render mesh and re-runs the identical walk.
##
## THE VERB TABLE IS NOT HERE. `station/interact.py` derives it from
## `directory.PLACES["interacts"]` and `rooms.PROP_KIND` and writes the sidecar;
## this reads it. A copy of those tables in GDScript would be a second
## description of one decision, which is hard rule 4's failure mode.
func _wire_interact(scene: Node) -> void:
	if interact_path == "" or not FileAccess.file_exists(interact_path):
		return
	if _args().has("no-interact"):
		print("walk: interactables DISABLED (control) -- nothing to use")
		return
	var f := FileAccess.open(interact_path, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	if typeof(rows) != TYPE_ARRAY:
		push_error("walk: %s is not a JSON array" % interact_path)
		return
	_interact = Node3D.new()
	_interact.name = "Interactables"
	_interact.set_script(load("res://scripts/interact.gd"))
	add_child(_interact)
	var n: int = _interact.collect(scene, rows)
	if n == 0:
		push_error("walk: the interact sidecar has %d rows and NONE of them "
			% rows.size() + "matched a mesh in this build")


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

	# THE LOOK COMES FROM interior.tscn, not from here. What used to be in this
	# spot was a hand-written Environment with ambient 0.6 and no tonemapping --
	# a fill three stops off the measured one, applied to geometry that had no
	# materials, so nothing about it could be judged. `interior.tscn`'s `Env` is
	# the calibrated interior look: ACES, exposure 1.0, white point 4.0, ambient
	# 1.30 (`AMBIENT_CALIBRATED_ENERGY`, measured in session 3n against the
	# residential corridor), SSAO at 0.6 m, low glow. A second set of numbers
	# here would be a second look, judged against nothing.
	var env := WorldEnvironment.new()
	env.name = "WorldEnvironment"
	if _dress != null and _dress.environment() != null:
		env.environment = _dress.environment()
	else:
		# Only reachable with `--no-dress` or a broken interior.tscn. Kept as
		# the pre-3w flat fill so the control renders something.
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


## THE PLAYABLE BUILD, PHOTOGRAPHED THROUGH THE PLAYER'S OWN EYE.
##
## Not a second camera rig, and that is the point. `player.gd` already carries a
## Camera3D at `eye_height_m` -- 1.7 m, the stature `drum_ground.stand_on_ground`
## and INV-071's reference ladders use -- parented to the body and oriented by
## the body's own basis. A frame taken through it is what a standing person
## sees, from where the physics actually put them, and it cannot disagree with
## where a player would be. Every other camera in this project flies through
## walls.
##
## THE BODY IS SETTLED FIRST, for the reason the walk test settles it: a spawn
## is a CLAIM ("a person can stand here"), and a camera placed at the claim
## instead of at the result photographs a point in mid-air. The eye is reported
## with the drop from the spawn, so the frame says where it was taken.
##
## Yaw defaults to 90 degrees because a RING deck runs tangentially: at the
## spawn's ring angle the body's zero yaw faces along the station's +Z spine,
## i.e. straight into the end wall 1.5 m away, and the corridor is +/-90 off it.
## Same finding the walk test's heading sweep exists for.
func _run_shot(args: Dictionary) -> void:
	_shot_png = String(args["shot"])
	_shot_settle = int(args.get("settle", "120"))
	_shot_warmup = int(args.get("warmup", "8"))
	_shot_yaw = float(args.get("yaw", "90"))
	_shot_fov = float(args.get("fov", "55"))
	_shooting = true
	set_physics_process(true)


func _grab() -> void:
	_player.set_yaw(deg_to_rad(_shot_yaw))
	_player.step(1.0 / 60.0, Vector2.ZERO, false, false)
	var cam := _player.get_node_or_null("Camera3D") as Camera3D
	if cam == null:
		push_error("walk: the player has no camera")
		get_tree().quit(2)
		return
	cam.fov = _shot_fov
	# interior.tscn's near plane, not the player's 0.15: indoors the eye stands
	# against a wall and 0.15 clips the thing it is looking at.
	cam.near = 0.06
	cam.current = true
	var p := _player.global_position
	print("shot: eye %.3f,%.3f,%.3f (r=%.3f, %.3f m below spawn), yaw %.0f deg, "
		% [cam.global_position.x, cam.global_position.y, cam.global_position.z,
			sqrt(p.x * p.x + p.y * p.y), spawn.distance_to(p), _shot_yaw]
		+ "fov %.0f, on_floor=%s" % [_shot_fov,
			str(_player.is_on_floor()).to_lower()])
	# NoiseTexture2D generates on a worker thread, so a capture taken on the
	# first frame gets flat placeholder albedo instead of the weathering --
	# render_shot.gd's own scar, and this scene loads the same materials.
	for i in _shot_warmup:
		await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(_shot_png.get_base_dir())
	if img.save_png(_shot_png) != OK:
		push_error("walk: save_png failed for %s" % _shot_png)
		get_tree().quit(2)
		return
	print("captured %s  %dx%d" % [_shot_png, img.get_width(), img.get_height()])
	get_tree().quit(0)


var _shooting := false
var _shot_png := ""
var _shot_settle := 120
var _shot_warmup := 8
var _shot_yaw := 90.0
var _shot_fov := 55.0

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
	# THE CROWD WALKS WHETHER OR NOT THE TEST IS RUNNING, and before the early
	# returns below, because a corridor whose people only move during a walk
	# test is a corridor whose people do not move. It is also what makes the
	# shot phase worth taking: a photograph of a station with somebody
	# mid-stride in it is the whole point of the exercise.
	if _people != null:
		_people.advance_crowd(delta)
	# The shot phase: settle the body on the floor, then take the picture from
	# where it ended up. No wish vector -- a photograph is of somebody standing.
	if _shooting:
		_frame += 1
		_player.step(delta, Vector2.ZERO, false, false)
		if _frame >= _shot_settle:
			_shooting = false
			set_physics_process(false)
			_grab()
		return
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
	_try_use()
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
			if _people != null:
				goto_s += " turned_deg=%.1f noticed=%d facing_err_deg=%.1f" % [
					_people.turned_deg(), _people.noticed_count(),
					_people.facing_error_deg(p)]
		if _people != null and _people.crowd_count() > 0:
			goto_s += " walkers=%d crowd_travel_m=%.1f crowd_lods=%s" % [
				_people.crowd_count(), _people.crowd_travel_m(),
				_people.crowd_lod_report().replace(" ", ",")]
		# -- WHAT A PLAYER CAN USE ------------------------------------------
		# Printed UNCONDITIONALLY once this node exists, and every field on one
		# line, because the alternative is the defect that let the NPC
		# assertions vanish for six runs: `walkable.py` guarded them on the
		# presence of the very token they asserted, so when `npc.gd` stopped
		# parsing the tokens disappeared and the deck went on printing PASS. A
		# gate that vanishes with its subject is worse than no gate.
		if _interact != null:
			goto_s += (" interactables=%d pressable=%d verbs=%s"
				+ " prompt_frames=%d prompt=%s used=%s used_verb=%s"
				+ " use_count=%d use_travel_mm=%.2f use_range_m=%.2f"
				+ " want_use=%s want_present=%s want_range_m=%.2f") % [
				_interact.count(), _interact.pressable_count(),
				("-" if _interact.verb_report() == ""
					else _interact.verb_report()),
				_interact.prompt_frames(),
				("-" if String(_interact.prompt_group()) == ""
					else _interact.prompt_group()),
				("-" if String(_interact.used_group()) == ""
					else _interact.used_group()),
				("-" if String(_interact.used_verb()) == ""
					else _interact.used_verb()),
				_interact.use_count(), _interact.used_travel_mm(),
				_interact.used_range_m(),
				("-" if _use_group == "" else _use_group),
				str(_use_group != "" and _interact.has_group(_use_group)
					).to_lower(),
				(-1.0 if _use_group == "" else _interact.range_to(_use_group))]
			goto_s += " used_responds=%s no_mesh=%d used_prompt=%s" % [
				str(_interact.used_responds()).to_lower(),
				_interact.missing().size(),
				(("-" if String(_interact.used_prompt()) == ""
					else String(_interact.used_prompt()))
					.replace(" ", "_"))]
		print(("WALKTEST rest=%.3f,%.3f,%.3f on_floor=%s fell=%s moved_1s=%.3f "
			+ "drop=%.3f legs=%.2f/%.2f/%.2f/%.2f traverse_m=%.2f net_m=%.2f "
			+ "offfloor=%d/%d%s") % [
			_rest.x, _rest.y, _rest.z, str(_on_floor).to_lower(),
			str(fell).to_lower(), _moved_1s, spawn.distance_to(_rest),
			_leg_m[0], _leg_m[1], _leg_m[2], _leg_m[3],
			_path_m, _traverse_from.distance_to(p), _off_floor, _t_traverse,
			goto_s])
		get_tree().quit(0)


## PRESS THE KEY. There is no keyboard here, so the test calls the SAME `use()`
## an `InputEventKey` calls -- not a second path that can diverge from the one a
## player takes. It fires once, on the first frame the prompt names the object
## the run was told to go and use: that is exactly the moment a player would
## press E, and firing every frame would turn "can you use it" into "did you
## ever stand near it".
##
## THE PROMPT IS RE-TAKEN FIRST. `_interact` is a sibling node, so its own
## `_physics_process` may not have run since the body moved; `refresh()` is
## frame-guarded and idempotent.
func _try_use() -> void:
	if _interact == null or _use_group == "" or _used_ok:
		return
	_interact.refresh()
	if String(_interact.prompt_group()) != _use_group:
		return
	_used_ok = _interact.use()


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
