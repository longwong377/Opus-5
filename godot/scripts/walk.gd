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
## THE STATION IS BIGGER THAN ONE FILE. With a cell manifest the level is not
## loaded at all -- `scripts/stream.gd` keeps a derived number of cells resident
## around the body and frees the rest, and `--glb` is unused. See that file for
## where the residency radius and the triangle ceiling come from; neither is
## written down in either file.
@export var cells_path: String = ""
var _stream: Node3D = null
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
## The dialogue sidecar -- `station/dialogue.write_sidecar`'s output, one row
## per person the deck baked, carrying what they say. Empty disables talking,
## exactly as an empty `actors_path` disables people.
@export var dialogue_path: String = ""
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
## The interface -- see `scripts/hud.gd`. Built after the player, because it is
## the player's own readout, and NOT built in the headless walk test.
var _hud
var _talk: Node3D = null

var _player: CharacterBody3D
var _static: StaticBody3D


func _ready() -> void:
	var args := _args()
	# BAKE CELLS. Offline, in the engine, because the split has to produce
	# resources `ResourceLoader` can load on a worker thread and nothing outside
	# Godot writes those. See `scripts/stream.gd::bake`.
	if args.has("bake-cells"):
		var bk := Node3D.new()
		bk.set_script(load("res://scripts/stream.gd"))
		add_child(bk)
		get_tree().quit(bk.bake(args))
		return
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
	if args.has("dialogue"):
		dialogue_path = args["dialogue"]
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
	if args.has("cells"):
		cells_path = args["cells"]
	_use_group = String(args.get("use-group", ""))

	_load_sidecars()
	if cells_path != "":
		if not _load_streamed(args):
			get_tree().quit(2)
			return
	elif not _load_level():
		push_error("walk: could not load %s" % glb_path)
		get_tree().quit(2)
		return
	_spawn_player()
	if _stream != null:
		_stream.set_player(_player)
		# THE WIRING IS HANDED OVER AFTER THE PLAYER EXISTS, and it back-fills
		# whatever is already resident -- the start cell is primed before there
		# is a body, so without the back-fill the one cell a player is certain to
		# be standing in would be the one cell whose doors never worked.
		if not args.has("no-cell-wiring"):
			_stream.set_wiring(self)
		else:
			print("walk: streamed cells are NOT WIRED (control) -- this is the "
				+ "build before this session: solid doors, nobody home, "
				+ "nothing to use")
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

	# NOBODY SPOKE, AND IT WAS AN ORDERING BUG ON BOTH PATHS.
	#
	# `_wire_dialogue` has been called from `_wire_people` since it was
	# written, and `_wire_people` runs inside `_load_level()` -- which happens
	# ABOVE `_spawn_player()` in this function. Its second guard is
	# `if _player == null ... return`, so the node was never built in a
	# monolithic build either: its own header says *"the module that makes
	# them talk had no instantiator"*, and the instantiator it gained could
	# not fire. The SHIPPED build is streamed, where `_load_level` is not
	# called at all -- `wire_cell` handles doors, people, crowd and
	# interactables per cell, and dialogue was not among them.
	#
	# It is wired HERE, once, for both paths, because a conversation is not
	# per cell: `dialogue.gd::collect` joins the exchange sidecar to the CAST
	# LIST's own coordinates and never touches a mesh, so it has nothing to
	# wait for and nothing to re-wire when a cell arrives or is freed.
	#
	# INERT FOR EVERY EXISTING CALLER. `_wire_dialogue` returns immediately
	# when `_talk` is already built, so the older call from `_wire_people` is
	# a no-op wherever it still fires; `--walk-test`, `--no-talk` and an empty
	# `dialogue_path` return exactly as they did before, which is every
	# headless gate in this repository.
	_wire_dialogue(_actors)

	_wire_hud()

	if args.has("stream-test"):
		_run_stream_test(args)
	elif args.has("walk-test"):
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
## The loaded level's root, kept so anything that needs to ask the GEOMETRY a
## question -- which room is this point in -- can ask the geometry rather than
## infer it from a sidecar. See `scripts/places.gd`.
var _visual: Node = null


func _load_level() -> bool:
	var scene := _load_glb(glb_path)
	if scene == null:
		return false
	add_child(scene)
	_visual = scene
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
## Build the dresser and load the material table. Split out of `_dress_level`
## because a STREAMED build needs it alive across many cells -- one cell arrives
## every few seconds and each one has to be bound out of the same table -- while
## the monolithic path binds once and releases immediately. Returns false when
## `--no-dress` turned it off, which is the control on both paths.
func _prepare_dress() -> bool:
	if _args().has("no-dress"):
		print("walk: dressing DISABLED (control) -- no materials, no lights")
		return false
	_dress = Node.new()
	_dress.name = "Dress"
	_dress.set_script(load("res://scripts/dress_scene.gd"))
	add_child(_dress)
	if not _dress.prepare():
		push_error("walk: dress FAILED -- " + ", ".join(_dress.problems))
		print("dress: FAILED -- %s" % ", ".join(_dress.problems))
	return true


func _dress_level(scene: Node) -> void:
	if not _prepare_dress():
		return
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


## THE LEVEL IS NOT LOADED. It arrives, cell by cell, around the body.
##
## Nothing after this point in the file knows the difference: the body is spawned
## by the same `_spawn_player`, stepped by the same `player.gd`, and stands on
## trimesh colliders made by the same `create_trimesh_collision` -- they are just
## made when the cell arrives instead of at start-up. See `scripts/stream.gd`.
##
## THE FIRST CELL IS PRIMED SYNCHRONOUSLY and that is deliberate. A level's first
## cell is a load screen, not a stream; spawning a body into a cell that has not
## arrived makes it fall for a hundred frames and the verdict then blames
## streaming for a start-up ordering mistake.
func _load_streamed(args: Dictionary) -> bool:
	_prepare_dress()
	_stream = Node3D.new()
	_stream.name = "Stream"
	_stream.set_script(load("res://scripts/stream.gd"))
	add_child(_stream)
	var energy := 3.0
	if _dress != null:
		energy = _dress.consts.get("fixture_energy", 3.0)
	_stream.lag_frames = int(args.get("stream-lag", "0"))
	if not _stream.configure(cells_path, _dress, energy, args.has("no-stream")):
		push_error("walk: " + ", ".join(_stream.problems))
		return false
	# WHERE THE CORRIDOR IS, AND HOW FAR AHEAD TO AIM -- both off the manifest,
	# both measured. The corridor radius and z come from `stream.bake`'s scan of
	# the collision shell. The steering lookahead is `sqrt(r * w)`, which is the
	# length whose chord sags exactly w/8 off the arc (sag = L^2/8r): aim further
	# and a body walking a curved corridor walks the chord and grinds the inner
	# wall; aim shorter and the heading is noise.
	var corr: Dictionary = _stream.plan.get("corridor", {})
	_s_r = float(corr.get("r_floor_m", 0.0))
	_s_z = float(corr.get("z_mid", 0.0))
	_s_w = float(corr.get("width_m", 2.5))
	_s_lookahead = sqrt(maxf(_s_r * _s_w, 1.0))
	# THE VISIT IS PLANNED BEFORE THE START CELL IS CHOSEN, because it is what
	# chooses it: the body has to start far enough away that the cell it walks
	# into was STREAMED IN AFTER LAUNCH rather than primed under its feet.
	if args.has("visit") and not _plan_visit(args):
		return false
	_start_cell = int(args.get("start-cell", "-1"))
	if _start_cell < 0 and _visiting:
		_start_cell = _stream.cell_at(_corridor_point(_v_away_deg))
	# A SPAWN SET AS A PROPERTY CHOOSES THE CELL TOO. `main.gd` is the only
	# instantiator that is not a command line: it sets `spawn` from the boot
	# manifest, where it was measured off the collision shell's own floor, and
	# cannot pass `--spawn=` because `OS.get_cmdline_user_args()` is not
	# writable. Without this the shipped build primes `cells[0]` and then --
	# below -- overwrites the derived spawn with that cell's own, so a manifest
	# that says 265 degrees boots the player at 10 and `boot.py`'s whole
	# derivation is decoration. Inert for every other caller: they leave `spawn`
	# at the export default, and no cell of a ring deck contains the origin.
	if _start_cell < 0 and spawn != Vector3.ZERO:
		_start_cell = _stream.cell_at(spawn)
	if _start_cell < 0:
		_start_cell = int(_stream.cells[0]["index"])
	var c: Dictionary = _stream.cell_by_index(_start_cell)
	if c.is_empty():
		push_error("walk: no cell with index %d in %s"
			% [_start_cell, cells_path])
		return false
	# THE CELL'S OWN FLOOR POINT UNLESS THE CALLER'S IS INSIDE THE PRIMED CELL.
	# Exactly one cell exists at the first frame, so a spawn outside it is a
	# body falling through geometry that has not arrived -- and blaming the
	# streamer for a start-up ordering mistake is what `prime` exists to
	# prevent. `boot.py --gate` reports the same disagreement before launch.
	if not args.has("spawn") and _stream.cell_at(spawn) != _start_cell:
		spawn = Vector3(c["spawn"][0], c["spawn"][1], c["spawn"][2])
	_prime_ms = _stream.prime(_start_cell)
	print("walk: STREAMED level -- start cell %d, primed in %d ms, spawn "
		% [_start_cell, _prime_ms]
		+ "%.2f,%.2f,%.2f, corridor r=%.2f z=%.2f w=%.2f, lookahead %.1f m "
		% [spawn.x, spawn.y, spawn.z, _s_r, _s_z, _s_w, _s_lookahead]
		+ "(chord sag %.2f m)" % (_s_lookahead * _s_lookahead / (8.0 * _s_r)))
	return true


## -- THE SIDECARS ----------------------------------------------------------
##
## READ ONCE, HANDED TO EVERY CELL. A sidecar is per DECK -- one cast list, one
## interactables list, one crowd list for a whole ring deck -- while a streamed
## cell is 20 degrees of that deck's arc. Splitting the files per cell would be a
## second description of where everything is, and the geometry already knows: a
## row binds in the cell whose meshes carry its name and nowhere else. So there
## is nothing to split. See `npc.gd::collect` and `interact.gd::collect`.
var _actors: Array = []
var _ix_rows: Array = []
var _crowd_rows: Array = []
var _crowd_libs: Array = []


## A banner that is TRUE ONCE. Every `--no-*` control is now consulted per cell
## rather than per level, so an unguarded print becomes one line per streamed
## cell and the log stops being readable at exactly the moment it matters.
var _said := {}


func _say_once(msg: String) -> void:
	if _said.has(msg):
		return
	_said[msg] = true
	print(msg)


func _read_rows(path: String) -> Array:
	if path == "" or not FileAccess.file_exists(path):
		return []
	var rows = JSON.parse_string(FileAccess.get_file_as_string(path))
	return (rows if typeof(rows) == TYPE_ARRAY else [])


func _load_sidecars() -> void:
	_actors = _read_rows(actors_path)
	_ix_rows = _read_rows(interact_path)
	_crowd_rows = _read_rows(crowd_path)
	if interact_path != "" and _ix_rows.is_empty():
		push_error("walk: %s is not a JSON array" % interact_path)


## Give the deck its doors. `--no-doors` leaves them out, which is the NEGATIVE
## CONTROL for the walk test: with the doors inert the closed panels stay solid
## and a body must NOT be able to reach the room. A test that only ever runs the
## working configuration cannot tell a door that opens from a hole in a wall.
func _wire_doors(scene: Node, col: Node) -> void:
	if not _make_doors():
		return
	var n: int = _doors.collect(scene, col, door_travel_m)
	print("walk: %d doors wired" % n)


func _make_doors() -> bool:
	if _doors != null:
		return true
	if _args().has("no-doors"):
		_say_once("walk: doors DISABLED (negative control) -- the closed panels "
			+ "stay solid and a body must NOT get into the room")
		return false
	_doors = Node3D.new()
	_doors.name = "Doors"
	_doors.set_script(load("res://scripts/door.gd"))
	add_child(_doors)
	return true


## Give the deck its inhabitants. `--no-people` leaves them inert, which is the
## negative control: with nobody reacting the turn must read ZERO. A reaction
## test that only runs the working configuration cannot tell a person who turns
## from a statue that happened to be facing the right way.
func _wire_people(scene: Node) -> void:
	if not _make_people():
		return
	var n: int = _people.collect(scene, _actors)
	print("walk: %d people wired of %d in the cast list" % [n, _actors.size()])
	_wire_crowd()
	_wire_dialogue(_actors)


func _make_people() -> bool:
	if _people != null:
		return true
	if _actors.is_empty():
		return false
	if _args().has("no-people"):
		_say_once("walk: people DISABLED (negative control) -- nobody can "
			+ "notice, so the turn must read ZERO")
		return false
	_people = Node3D.new()
	_people.name = "People"
	_people.set_script(load("res://scripts/npc.gd"))
	add_child(_people)
	return true


## The corridor's walkers. They are not in the deck mesh at all -- their bodies
## come from `crowd_lod<N>.glb`, 112 shared meshes for the whole station, and
## this list says where each one is and which phase they are on.
func _wire_crowd() -> void:
	if not _load_crowd_libs():
		return
	var n2: int = _people.build_crowd_multi(_crowd_libs, _crowd_rows)
	print("walk: %d walkers instanced across %d LOD libraries"
		% [n2, _crowd_libs.size()])


## Load the shared body libraries and tell `npc.gd` the ladder. Split out of
## `_wire_crowd` because a STREAMED build sizes the MultiMeshes from the whole
## deck's placement list up front and then admits each cell's walkers as it
## arrives -- `MultiMesh.instance_count` cannot grow.
func _load_crowd_libs() -> bool:
	if not _crowd_libs.is_empty():
		return true
	if _people == null or _crowd_rows.is_empty():
		return false
	if crowd_glb == "" and crowd_glbs == "":
		return false
	if _args().has("no-crowd"):
		_say_once("walk: crowd DISABLED (negative control)")
		return false
	# One library per rung of the ladder. `crowd_glbs` is the new form and
	# `crowd_glb` the single-rung one it replaces; both are accepted so a
	# command written before the ladder existed still runs.
	var paths: Array = ([] if crowd_glbs == ""
		else Array(crowd_glbs.split(",")))
	if paths.is_empty() and crowd_glb != "":
		paths = [crowd_glb]
	for pth in paths:
		if not FileAccess.file_exists(String(pth)):
			continue
		var l := _load_glb(String(pth))
		if l != null:
			_crowd_libs.append(l)
	if _crowd_libs.is_empty():
		push_error("walk: could not load any crowd library")
		return false
	_people.set_crowd_ladder(crowd_ladder)
	return true


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
	if not _make_interact():
		return
	var n: int = _interact.collect(scene, _ix_rows)
	if n == 0:
		push_error("walk: the interact sidecar has %d rows and NONE of them "
			% _ix_rows.size() + "matched a mesh in this build")


func _make_interact() -> bool:
	if _interact != null:
		return true
	if _ix_rows.is_empty():
		return false
	if _args().has("no-interact"):
		_say_once("walk: interactables DISABLED (control) -- nothing to use")
		return false
	_interact = Node3D.new()
	_interact.name = "Interactables"
	_interact.set_script(load("res://scripts/interact.gd"))
	add_child(_interact)
	return true


# ===========================================================================
#  A CELL ARRIVES, AND EVERYTHING A MONOLITHIC LOAD WIRES IS WIRED TO IT
# ===========================================================================
#
# WHAT THIS EXISTS TO END. `scripts/stream.gd` made the station bigger than one
# file and `walk.gd` went on wiring doors, inhabitants and interactables exactly
# once, over a scene the streamed path never loads. So a streamed build was a
# shell you could walk through: `docs/streaming-4g.md` said so in its own "what
# is NOT done" -- *"the collision proxy carries the door panels, so in a streamed
# build today the pressure doors are solid"*. Every pressure door on the station
# was a wall, nobody in any room knew a player existed, and nothing could be
# used.
#
# THE HARD PART IS NOT ARRIVING, IT IS LEAVING. Each of the three subsystems owns
# nodes that stand for cell geometry and are NOT children of the cell -- an
# inhabitant's collision capsule, an interactable's proxy box -- and each holds
# references INTO the cell. Freeing a cell without telling them leaves an
# invisible person to bump into, a prompt for a console that has been unloaded,
# and a door that keeps moving leaves that no longer exist. So `stream.gd` calls
# `unwire_cell` BEFORE `queue_free`, and each subsystem gives back exactly what
# that cell brought.
var _wired_cells := {}
var _double_wires := 0


func wire_cell(id: String, vis: Node, col: Node) -> void:
	if _wired_cells.has(id):
		_double_wires += 1
		push_error("walk: cell %s wired twice" % id)
		return
	_wired_cells[id] = true
	var nd := 0
	var np := 0
	var ni := 0
	var nc := 0
	if _make_doors():
		nd = _doors.collect(vis, col, door_travel_m, id)
	if _make_people():
		np = _people.collect(vis, _actors, id)
		if _load_crowd_libs():
			# Size the buckets from the WHOLE deck once, then admit this cell's
			# walkers. Which walkers are this cell's is decided by the same arc
			# the bake cut on -- `stream.cell_at` -- because a walker is a
			# placement and has no mesh in the cell to be found by.
			if not _crowd_ready:
				_crowd_ready = true
				_people.prepare_crowd(_crowd_libs, _crowd_rows)
			nc = _people.add_crowd(_rows_in_cell(id), id)
	if _make_interact():
		ni = _interact.collect(vis, _ix_rows, id)
	if _interact != null and _player != null:
		_interact.watch(_player)
	print("walk: +wired %s -- doors now %d, %d person(s), %d walker(s), "
		% [id, nd, np, nc] + "%d interactable(s)" % ni)


func unwire_cell(id: String) -> void:
	if not _wired_cells.has(id):
		return
	_wired_cells.erase(id)
	if _args().has("no-unwire"):
		# THE CONTROL FOR THE OTHER HALF. Everything above still runs on arrival;
		# nothing is given back. The cell's meshes are freed underneath the
		# subsystems that hold them, so the second visit double-wires and the
		# prompt goes on naming a console that has been unloaded -- which is
		# what `stale_prompt_frames` counts.
		return
	var nd := 0
	var np := 0
	var ni := 0
	if _doors != null:
		nd = _doors.release(id)
	if _people != null:
		np = _people.release(id)
	if _interact != null:
		ni = _interact.release(id)
	print("walk: -unwired %s -- %d door part(s), %d person(s), "
		% [id, nd, np] + "%d interactable(s)" % ni)


var _crowd_ready := false


## Which crowd placements belong to a cell. A walker has no mesh in the cell --
## their body comes from `crowd_lod*.glb` -- so unlike an actor they cannot be
## found by name, and position is the only thing that can say. It is the SAME
## test the bake binned triangles by, asked of `stream.gd` rather than repeated.
func _rows_in_cell(id: String) -> Array:
	var out: Array = []
	if _stream == null:
		return _crowd_rows
	var c: Dictionary = _stream.cell_by_id(id)
	if c.is_empty():
		return out
	for r in _crowd_rows:
		var p := Vector3(float(r.get("x", 0.0)), float(r.get("y", 0.0)),
			float(r.get("z", 0.0)))
		if _stream.distance_to(c, p) <= 0.0:
			out.append(r)
	return out


## Give the player an INTERFACE. See `scripts/hud.gd`.
##
## NOT IN THE WALK TEST, and that is the constraint this whole node is built
## around. `station/walkable.py` matches `WALKTEST (.+)` and reads nothing else;
## the headless run has a null rendering driver, so a Control tree there draws
## nothing and can only add ways for the gate to fail. It is built for a shot
## and for a person at a keyboard, which is the configuration it is for.
##
## `--no-hud` is the control, and it is deliberately the SAME flag `interact.gd`
## reads: with it a frame carries no interface at all, not merely a different
## one, so the A/B says whether this file does anything.
##
## Wired AFTER the player and the interactables because it reads both -- the
## body for where it is and which way it faces, `interact.gd` for what is in
## reach. It holds no second look-at test and no second verb table.
## NOBODY TALKED, AND THE MODULE THAT MAKES THEM TALK HAD NO INSTANTIATOR.
## `station/dialogue.py` derives what a named resident says from the hour, their
## species rhythm, their role, their beat and what the port is doing -- and
## nothing in the shipped scene tree built the node, so a player met 73 people
## in a customs hall and none of them had a voice.
##
## Shaped like `_wire_people` deliberately, including the control: `--no-talk`
## leaves the people standing there silent, which is the frame that shows the
## dialogue is what put the words on screen.
func _wire_dialogue(actors: Array) -> void:
	# IDEMPOTENT, so the older call site above `_spawn_player` stays legal.
	if _talk != null:
		return
	var args := _args()
	if args.has("walk-test"):
		return
	if args.has("no-talk"):
		print("dialogue: DISABLED (control) -- nobody speaks on this frame")
		return
	if _player == null or dialogue_path == "":
		return
	if not FileAccess.file_exists(dialogue_path):
		print("dialogue: no sidecar at %s" % dialogue_path)
		return
	var f := FileAccess.open(dialogue_path, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	if typeof(rows) != TYPE_ARRAY:
		print("dialogue: sidecar is not an array")
		return
	_talk = Node3D.new()
	_talk.name = "Dialogue"
	_talk.set_script(load("res://scripts/dialogue.gd"))
	add_child(_talk)
	var n: int = _talk.collect(actors, rows)
	_talk.watch(_player)
	print("dialogue: %d people can speak, of %d in the cast" % [n, actors.size()])


func _wire_hud() -> void:
	var args := _args()
	if args.has("walk-test") or args.has("stream-test"):
		return
	if args.has("no-hud"):
		print("hud: DISABLED (control) -- no interface on this frame")
		return
	if _player == null:
		return
	_hud = CanvasLayer.new()
	_hud.name = "HUD"
	_hud.layer = 8
	_hud.set_script(load("res://scripts/hud.gd"))
	add_child(_hud)
	_hud.bind(_player, _interact, glb_path, interact_path, _visual)


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
	# ONE THING STEPS THE BODY. Every headless mode in this file drives
	# `player.step()` from `_physics_process` below, and `player.gd` has its own
	# `_physics_process` that steps it again from a keyboard that is not there --
	# a zero wish, which is harmless to the walk and rebuilds the basis from
	# `_yaw`, which is not harmless to the eye. See `player.gd::drive_externally`
	# and `docs/runtime-4h.md`. A build with a window and a player at the
	# keyboard is untouched: none of these three flags is present.
	var a2 := _args()
	if ((a2.has("walk-test") or a2.has("stream-test") or a2.has("shot"))
			and not a2.has("self-step")):
		_player.drive_externally()
	elif a2.has("self-step"):
		_self_step = true
		print("walk: player.gd is STEPPING ITSELF as well (control) -- the "
			+ "body is stepped twice a frame and the second step rebuilds its "
			+ "basis from a yaw nobody set, so the eye stops following the "
			+ "walk. See eye_err_deg in the verdict.")

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
	if args.has("goto-path"):
		for piece in String(args["goto-path"]).split(";", false):
			_wp.append(_vec(piece))
		if not _wp.is_empty():
			# The last waypoint IS the place, so `goto_best_m` keeps measuring
			# against the same point with or without a path.
			_goto = _wp[_wp.size() - 1]
			_have_goto = true
	if args.has("goto-tol"):
		_wp_tol = float(args["goto-tol"])
	_door_key = String(args.get("door-key", ""))
	_trace = int(args.get("trace", "0"))
	_testing = true
	set_physics_process(true)


## THE STREAMING GATE. A body walks from one cell into the next, the next cell is
## resident BEFORE the body reaches it, and the body never leaves the floor.
##
## WHY THE THIRD CLAUSE IS THE WHOLE TEST. Everything else in this project can be
## satisfied by a cell that arrives eventually: a coverage count says the cell
## exists, a triangle budget says it is affordable, a render says it looks right.
## None of them can fail for "it turned up after the player walked into the hole
## where it should have been". So the number this prints is a LEAD -- how far
## away the body still was at the frame the cell became resident -- and it is
## measured from OUTSIDE `stream.gd`, by watching its resident set change, so a
## streamer that lied about its own state could not make it pass.
##
## AND IT REPORTS METRES, NOT "DID IT MOVE", for the reason `station/collision.py`
## learned the hard way: four one-second nudges prove a body is not wedged and
## prove nothing about whether you can go anywhere. `floor_m` -- distance covered
## WHILE ON THE FLOOR -- is the honest one, because a body that walks off the end
## of a cell keeps travelling and a plain path length would score falling as
## progress.
##
## THE CONTROL IS `--no-stream`, and it must fail. With it the start cell is
## primed and nothing else is ever requested: the body walks to the cell boundary
## and off the end of the world. If both runs pass, this test is measuring
## nothing. `--turnaround=N` is the second control, for the other requirement --
## reverse the walk mid-load and no cell may be requested twice.
func _run_stream_test(args: Dictionary) -> void:
	if _stream == null:
		push_error("walk: --stream-test needs --cells=<cells.json>")
		get_tree().quit(2)
		return
	_t_settle = int(args.get("settle", "120"))
	_t_traverse = int(args.get("traverse", "2400"))
	_s_dir = (-1.0 if String(args.get("dir", "+1")).begins_with("-") else 1.0)
	_s_turnaround = int(args.get("turnaround", "0"))
	_trace = int(args.get("trace", "0"))
	if _visiting:
		_build_plan()
		# The traverse cap is a backstop for the whole itinerary, not a leg
		# budget -- the legs carry their own and report what they could not
		# reach.
		var total := 0
		for leg in _plan:
			total += int(leg["budget"])
		_t_traverse = int(args.get("traverse", str(total)))
	_streaming = true
	set_physics_process(true)


# ===========================================================================
#  THE VISIT GATE -- a streamed cell is a PLACE, not a shell
# ===========================================================================
#
## `--visit` walks a body into a cell that was loaded after launch, THROUGH a
## pressure door in it, up to a declared interactable in it, uses that, and is
## noticed by the people in it. Then it walks far enough away that the cell is
## freed, comes back, and does the whole thing again.
##
## WHY THE SECOND VISIT IS HALF THE TEST. Wiring on arrival is the easy half; a
## build that wires and never unwires passes every first-visit assertion and
## leaves an invisible person to bump into, a prompt for an unloaded console and
## a door that double-wires the moment its cell returns. `--no-unwire` is the
## control for exactly that and it fires on `double_wires` and
## `stale_prompt_frames`.
##
## IT PICKS ITS OWN TARGET, from the interactables sidecar it was given: the
## first pressable interactable with a response behind it. The door is its
## PLACE -- `doorpanel_<place>` is the generator's own naming and `door.gd` reads
## the same key -- so nothing here holds a table of what is where.
##
## AND EVERY NUMBER IS METRES ON THE FLOOR. `floor_m`, not path length: the
## `--no-stream` control walks 11,712 m by falling.
func _plan_visit(args: Dictionary) -> bool:
	if _ix_rows.is_empty():
		push_error("walk: --visit needs --interact=<sidecar>")
		return false
	var want := String(args.get("use-group", ""))
	var row := {}
	for r in _ix_rows:
		if want != "":
			if String(r.get("group", "")) == want:
				row = r
				break
			continue
		if bool(r.get("pressable", false)) and bool(r.get("responds", false)) \
				and String(r.get("place", "")) != "":
			row = r
			break
	if row.is_empty():
		push_error("walk: no pressable interactable with a response in %s"
			% interact_path)
		return false
	_v_group = String(row["group"])
	_use_group = _v_group
	_v_door = String(args.get("door-key", String(row.get("place", ""))))
	var c3 = row.get("centre")
	if typeof(c3) != TYPE_ARRAY or c3.size() != 3:
		push_error("walk: %s has no centre in the sidecar" % _v_group)
		return false
	_v_at = Vector3(float(c3[0]), float(c3[1]), float(c3[2]))
	_v_deg = _deg_of(_v_at)

	# WHERE THE CELL IS, and how far away is far enough to make it go away.
	# `free_radius_m` is the streamer's own deadband, so the away angle is
	# derived from the thing that decides the freeing rather than guessed: one
	# free radius past the cell's far edge, plus half a cell of margin.
	var cell: int = _stream.cell_at(_v_at)
	if cell < 0:
		cell = _nearest_cell(_v_at)
	_v_cell = int(args.get("visit-cell", str(cell)))
	var cd: Dictionary = _stream.cell_by_index(_v_cell)
	if cd.is_empty() or not cd.has("arc"):
		push_error("walk: cell %d is not an arc cell" % _v_cell)
		return false
	_v_id = String(cd["id"])
	var arc: Dictionary = cd["arc"]
	var r: float = float(arc["r_m"])
	var margin := rad_to_deg(float(_stream.free_m) / maxf(r, 1.0)) \
		+ 0.5 * float(_stream.plan.get("cell_deg", 20.0))
	# Away on the side the body can actually reach: the corridor is 205 deg of a
	# ring, not a closed loop, so walking off its end is not walking away.
	_v_away_deg = float(arc["a1_deg"]) + margin
	if _stream.cell_at(_corridor_point(_v_away_deg)) < 0:
		_v_away_deg = float(arc["a0_deg"]) - margin
	if _stream.cell_at(_corridor_point(_v_away_deg)) < 0:
		push_error("walk: no corridor %0.1f deg either side of cell %d -- "
			% [margin, _v_cell] + "this bake is too short to free it")
		return false
	_visiting = true
	print("walk: VISIT cell %d (%s), door '%s', use '%s' at %.2f deg; "
		% [_v_cell, _v_id, _v_door, _v_group, _v_deg]
		+ "away is %.2f deg (%.1f m of arc, free radius %.1f m)"
		% [_v_away_deg, absf(deg_to_rad(_v_away_deg - _v_deg)) * r,
			float(_stream.free_m)])
	return true


## A point on the corridor floor at a given ring angle -- the same floor the
## cell spawns are placed on, so it is somewhere a body can stand.
func _corridor_point(deg: float) -> Vector3:
	var a := deg_to_rad(deg)
	var r: float = maxf(_s_r - 0.2, 1.0)
	return Vector3(r * cos(a), r * sin(a), _s_z)


func _deg_of(p: Vector3) -> float:
	var a := rad_to_deg(atan2(p.y, p.x))
	return (a + 360.0 if a < 0.0 else a)


func _nearest_cell(p: Vector3) -> int:
	var best := -1
	var bd := INF
	for c in _stream.cells:
		var d: float = _stream.distance_to(c, p)
		if d < bd:
			bd = d
			best = int(c["index"])
	return best


## The legs, built once the target is known. Two visits with a free in between.
##
## THE DOORWAY IS ITS OWN WAYPOINT, IN BOTH DIRECTIONS, and the first version of
## this plan left it out. There is no pathfinder here -- a leg is a straight
## steer -- so a body that walks out of a room aimed at a point in the corridor
## approaches the aperture DIAGONALLY and catches the jamb: measured, it wedged
## 0.4 m off the door's centreline with `velocity = 0` and stayed there for
## 20,000 frames. Lining up on the door's own centre first is what a person does
## and it costs one waypoint. It is also why the door centre is read from
## `door.gd` rather than from the sidecar: only the engine knows where the leaves
## actually are, and only once that cell is resident.
func _build_plan() -> void:
	_plan = [
		{"kind": "arc", "deg": _v_deg, "budget": 3000, "what": "walk to the door"},
		{"kind": "at", "to": "door_out", "near": 0.7, "budget": 900,
			"what": "stand at the door"},
		{"kind": "at", "to": "door_mid", "near": 1.0, "budget": 900,
			"what": "line up on the doorway"},
		{"kind": "at", "to": "use", "near": 1.2, "budget": 900, "use": true,
			"record": 1, "what": "through the door and use it"},
		{"kind": "at", "to": "door_mid", "near": 1.0, "budget": 900,
			"what": "line up on the doorway from inside"},
		# ALL THE WAY OUT. At `near = 1.6` this leg finished with the body still
		# standing IN the aperture, and the arc leg after it then walked
		# tangentially straight into the jamb: velocity 0 for 14,000 frames and
		# the cell never freed. A doorway is somewhere you pass through, not
		# somewhere you turn round in.
		{"kind": "at", "to": "door_out", "near": 0.7, "budget": 900,
			"what": "back out into the corridor"},
		{"kind": "arc", "deg": _v_away_deg, "budget": 3000, "until": "freed",
			"what": "walk away until the cell is freed"},
		{"kind": "arc", "deg": _v_deg, "budget": 3000, "what": "walk back"},
		{"kind": "at", "to": "door_out", "near": 0.7, "budget": 900,
			"what": "stand at the door again"},
		{"kind": "at", "to": "door_mid", "near": 1.0, "budget": 900,
			"what": "line up on the doorway again"},
		{"kind": "at", "to": "use", "near": 1.2, "budget": 900, "use": true,
			"record": 2, "what": "through the door and use it again"},
	]


## Where a leg is aiming, resolved every frame because the door's position is
## only knowable once its cell is resident -- which is the point of the test.
func _leg_target(leg: Dictionary) -> Vector3:
	var to := String(leg.get("to", ""))
	if to == "use":
		return _v_at
	var c := Vector3.ZERO
	if _doors != null and _doors.has(_v_door):
		c = _doors.centre_of(_v_door)
	if to == "door_mid":
		# The aperture itself. With no door wired there is nothing to line up on
		# and the corridor point is the honest fallback -- the run then fails on
		# the door claim, which is the truth.
		return (c if c != Vector3.ZERO else _corridor_point(_v_deg))
	if c == Vector3.ZERO:
		return _corridor_point(_v_deg)
	return _corridor_point(_deg_of(c))


var _visiting := false
var _plan: Array = []
var _leg := 0
var _leg_f := 0
var _v_cell := -1
var _v_id := ""
var _v_door := ""
var _v_group := ""
var _v_at := Vector3.ZERO
var _v_deg := 0.0
var _v_away_deg := 0.0
var _v_freed := false
var _v_stalls: Array = []
## Per visit, filled at the end of a `record` leg: door openness, who noticed,
## how far off they were facing, what the prompt said, what was used and how far
## it moved.
var _v_res: Array = [{}, {}]
var _v_deepest := 0.0


func _stream_frame(delta: float) -> void:
	_frame += 1
	if _frame <= _t_settle:
		_player.step(delta, Vector2.ZERO, false, false)
		_stream.update(_player.global_position)
		_note_residency()
		if _frame == _t_settle:
			_rest = _player.global_position
			_on_floor = _player.is_on_floor()
			_traverse_from = _rest
			_traverse_prev = _rest
			_s_here = _stream.cell_at(_rest)
			_s_entered.append(_s_here)
			print("walk: settled at %.2f,%.2f,%.2f (drop %.3f m), on_floor=%s, "
				% [_rest.x, _rest.y, _rest.z, spawn.distance_to(_rest),
					str(_on_floor).to_lower()]
				+ "in cell %d, walking %s" % [_s_here,
					("+angle" if _s_dir > 0.0 else "-angle")])
		return

	# THE PLAYER TURNS ROUND MID-LOAD. Not a flourish: `ResourceLoader` has no
	# cancel, so a request issued for a cell the body then walks away from WILL
	# complete, and the only two wrong answers are to instance it anyway or to
	# re-request it when the body turns back. Both are counted in the verdict.
	if _s_turnaround > 0 and _frame == _t_settle + _s_turnaround:
		_s_dir = -_s_dir
		print("walk: TURNED ROUND at frame %d, %d cell(s) in flight"
			% [_frame, _stream.inflight_count()])

	var p := _player.global_position
	var steer := Vector3.ZERO
	if _visiting:
		steer = _visit_steer(p)
	else:
		var a := atan2(p.y, p.x) + _s_dir * (_s_lookahead / maxf(_s_r, 1.0))
		steer = Vector3(_s_r * cos(a), _s_r * sin(a), _s_z) - p
	# SAMPLED BEFORE THE STEP, and the first version was not. `player.gd`'s own
	# `_physics_process` runs AFTER this node's, so a reading taken straight
	# after `player.step` sees the basis this file just set and reports 0.0
	# however wrong the eye is by the time anything looks through it. What the
	# player sees is what the LAST thing to touch the basis left, which is what
	# is here at the top of the next frame.
	_note_eye(steer)
	_face(steer)
	_player.step(delta, Vector2.ZERO, false, false, steer)
	# AND THEN NOBODY IS INSIDE ANYBODY. `npc.gd::push_off` separates the body
	# from any person it overlaps, across the floor plane only, before the next
	# frame's `move_and_slide` can see the overlap. It is not `move_and_slide`'s
	# job because it cannot do it without costing the floor -- see that file.
	_push_off(delta)
	_stream.update(_player.global_position)
	_note_residency()
	if _visiting:
		_visit_sample()
	if _trace > 0 and _frame % _trace == 0:
		_trace_line("leg%d@%.2fdeg" % [_leg, _deg_of(_player.global_position)])

	var q := _player.global_position
	var d := q.distance_to(_traverse_prev)
	_path_m += d
	# WHAT KIND OF OFF-FLOOR IS IT? A count alone cannot tell a body thrown a
	# metre into the air from one whose contact flickers for a frame while
	# something pushes past it, and the two want completely different fixes.
	# So: how many separate EPISODES, the longest one, and how far above its own
	# last floor position the body ever got. Measured along the body's own up,
	# which on a ring is radial and different at every angle -- a world axis
	# would read the corridor's curvature as lift.
	if _player.is_on_floor():
		_s_floor_m += d
		_floor_p = q
		_have_floor_p = true
		_offf_run = 0
	else:
		_off_floor += 1
		if _offf_run == 0:
			_offf_episodes += 1
		_offf_run += 1
		_offf_run_max = maxi(_offf_run_max, _offf_run)
		if _have_floor_p:
			var lift: float = (q - _floor_p).dot(_player.body_up())
			_lift_m = maxf(_lift_m, lift)
			_drop_m = minf(_drop_m, lift)
			# WHAT IS IT TOUCHING? A count of off-floor frames cannot name the
			# thing that took the floor away, and three wrong hypotheses were
			# tested against that count before this existed. The first few
			# episodes, in full, with the colliders `move_and_slide` actually
			# resolved against.
			if _offf_run == 1 and _offf_episodes <= 8:
				var hits := PackedStringArray()
				for i in _player.get_slide_collision_count():
					var kc := _player.get_slide_collision(i)
					var nd := kc.get_collider()
					hits.append("%s@n=%.2f,%.2f,%.2f" % [
						("?" if nd == null else String((nd as Node).name)),
						kc.get_normal().x, kc.get_normal().y,
						kc.get_normal().z])
				print("walk: OFF FLOOR f=%d lift=%.1fmm v_up=%.3f wall=%s "
					% [_frame, lift * 1000.0,
						_player.velocity.dot(_player.body_up()),
						str(_player.is_on_wall()).to_lower()]
					+ "slides=%d [%s]" % [_player.get_slide_collision_count(),
						", ".join(hits)])
	_traverse_prev = q

	var here: int = _stream.cell_at(q)
	if here >= 0 and here != _s_here:
		_s_here = here
		_s_entered.append(here)
		var id := String(_stream.cell_by_index(here)["id"])
		if not _stream.is_resident(id):
			_s_late += 1
			print("walk: ENTERED %s AND IT WAS NOT RESIDENT -- the body is "
				% id + "standing where the floor has not arrived")
		else:
			_s_min_lead_m = minf(_s_min_lead_m,
				float(_stream.lead_m.get(id, INF)))
			_s_min_lead_f = mini(_s_min_lead_f,
				_frame - int(_s_ready_frame.get(id, _frame)))
	if _frame >= _t_settle + _t_traverse or (_visiting and _leg >= _plan.size()):
		_print_stream_verdict()
		get_tree().quit(0)


## POINT THE BODY THE WAY IT IS WALKING.
##
## THE DEFECT THIS WORKED AROUND IS FIXED, and the history is worth keeping
## because the workaround being in this file was the mistake. `player.gd` used to
## step the body a SECOND time every frame from its own `_physics_process` --
## from a keyboard that is not there, so a zero wish, which still rebuilt the
## basis from `_yaw`. The body walked wherever it was steered and FACED WHEREVER
## YAW 0 POINTS, which on a ring deck is straight along the station's spine: the
## eye ended up 160 degrees off a console the body was walking directly at. Since
## session 4h `_spawn_player` calls `player.gd::drive_externally()`, so nothing
## steps the body but this file.
##
## This stays, and it is no longer a workaround. `player.step` derives its
## forward from `_yaw` on any frame it is given no steer -- the settle frames are
## exactly that -- so keeping `_yaw` equal to the direction the body was last
## sent is what makes the eye continuous across a leg boundary rather than
## snapping back to the spine. It inverts `player.step`'s own
## `fwd0.rotated(up, yaw)` rather than assuming a convention.
func _face(dir: Vector3) -> void:
	# THE CONTROL IS THE WHOLE PRE-4h ARRANGEMENT, not half of it. With
	# `player.gd` stepping itself AND this keeping `_yaw` equal to the steer,
	# the two agree and the defect is invisible -- measured, `eye_err_deg=0.0`
	# either way. `--self-step` therefore turns off both: the body is stepped
	# twice a frame and nothing tells it which way it is walking, which is
	# exactly what the stream test met before session 4g worked around it here.
	if _self_step:
		return
	if _player == null or dir.length_squared() < 1e-9:
		return
	var up: Vector3 = _player.body_up()
	var fwd0: Vector3 = (Vector3(0, 0, 1) if gravity_mode == "drum" else Vector3.FORWARD)
	fwd0 = (fwd0 - up * fwd0.dot(up))
	if fwd0.length() < 1e-4:
		return
	fwd0 = fwd0.normalized()
	var flat: Vector3 = dir - up * dir.dot(up)
	if flat.length() < 1e-4:
		return
	flat = flat.normalized()
	# `player.step` builds its forward as `fwd0.rotated(up, yaw)`, which is
	# `fwd0*cos(yaw) + (up x fwd0)*sin(yaw)` -- so this inverts exactly that
	# rather than assuming a convention.
	_player.set_yaw(atan2(flat.dot(up.cross(fwd0)), flat.dot(fwd0)))


## HOW FAR THE EYE IS FROM WHERE THE BODY IS WALKING, in degrees, every frame.
##
## THE ONLY NUMBER THAT COULD HAVE CAUGHT THE DOUBLE STEP. A body stepped twice
## a frame walks exactly as well as one stepped once -- a wish vector needs no
## facing -- so every distance in this verdict was unaffected while the camera
## sat at yaw 0, which on a ring deck is straight along the station's spine.
## `interact.gd` scans a 35-degree cone about that camera, so the failure
## surfaced as "the interactable is not wired".
##
## The control is `--self-step`, which puts `player.gd`'s own `_physics_process`
## back. Flattened onto the floor plane before comparing, because `player.step`
## flattens the steer too and a target a little up or down the radius is not a
## heading error.
func _note_eye(steer: Vector3) -> void:
	if _player == null:
		return
	var cam := _player.get_node_or_null("Camera3D") as Camera3D
	if cam == null:
		return
	var up: Vector3 = _player.body_up()
	var flat: Vector3 = steer - up * steer.dot(up)
	if flat.length() < 1e-4:
		return
	var fwd: Vector3 = -cam.global_transform.basis.z
	fwd = fwd - up * fwd.dot(up)
	if fwd.length() < 1e-4:
		return
	var e: float = rad_to_deg(fwd.angle_to(flat))
	_eye_err_sum += e
	_eye_err_n += 1
	_eye_err_max = maxf(_eye_err_max, e)


# -- the visit legs ---------------------------------------------------------

## Steer for the current leg, advance when it is done or out of budget.
##
## A LEG THAT RUNS OUT OF BUDGET IS RECORDED AND MOVED ON FROM, not retried. A
## body that cannot reach a waypoint has told you something -- what, and how far
## short, is in `stalls=` in the verdict -- and a gate that sat there until the
## traverse cap would report "no cell boundary was crossed" and hide it.
func _visit_steer(p: Vector3) -> Vector3:
	var leg: Dictionary = _plan[_leg]
	if _leg_f == 0:
		_leg_started(leg)
	_leg_f += 1
	var dir := Vector3.ZERO
	var done := false
	var short := 0.0
	if String(leg["kind"]) == "arc":
		var cur := _deg_of(p)
		var d := wrapf(float(leg["deg"]) - cur, -180.0, 180.0)
		short = absf(deg_to_rad(d)) * _s_r
		_s_dir = (1.0 if d >= 0.0 else -1.0)
		var reach := short <= 2.5
		if not reach:
			var a := atan2(p.y, p.x) + _s_dir * (_s_lookahead / maxf(_s_r, 1.0))
			dir = Vector3(_s_r * cos(a), _s_r * sin(a), _s_z) - p
		if String(leg.get("until", "")) == "freed":
			# ARRIVING IS THE MEANS, THE FREE IS THE END. The body walks out to
			# an angle one free radius past the cell and then STANDS THERE until
			# the streamer lets go -- so the leg measures the residency rule and
			# not the walk.
			if not _stream.is_resident(_v_id):
				_v_freed = true
				done = true
		else:
			done = reach
	else:
		var t := _leg_target(leg)
		dir = t - p
		# ACROSS THE FLOOR, NOT THROUGH IT. A console's centre is 1.2 m up the
		# wall and a door's is 1.15 m up the aperture, so a 3D distance to either
		# can never fall below that however close the body stands -- the first
		# version burned three whole leg budgets standing DIRECTLY UNDER things,
		# 0.50 m from the console and 88 deg off the view axis, reporting "1.2 m
		# short". A player stands in front of an object; the distance that
		# matters is the one they walk.
		var up: Vector3 = -Vector3(p.x, p.y, 0.0).normalized()
		var flat: Vector3 = (t - p) - up * (t - p).dot(up)
		short = flat.length()
		_leg_best = minf(_leg_best, short)
		done = short <= float(leg["near"])
	if bool(leg.get("use", false)):
		_try_use()
		if _interact != null and String(_interact.prompt_group()) == _v_group:
			_v_prompted = true
		# THE CLOSEST IT EVER CAME TO PROMPTING, sampled every frame. A prompt
		# that never fires otherwise reports whatever the body happened to be
		# doing when the leg ended, which is the least informative frame of the
		# whole approach.
		if _interact != null:
			var pr: Array = _interact.probe_terms(_v_group)
			if float(pr[0]) >= 0.0:
				_v_best_eye = minf(_v_best_eye, float(pr[0]))
				_v_best_axis = minf(_v_best_axis, float(pr[1]))
				if bool(pr[2]):
					_v_sight_f += 1
			if _trace > 0 and _leg_f % _trace == 0:
				var cam := _player.get_node_or_null("Camera3D") as Camera3D
				var cf := (Vector3.ZERO if cam == null
					else -cam.global_transform.basis.z)
				var t2 := _leg_target(leg)
				print("USELEG f=%d short=%.2f eye_range=%.2f off_axis=%.0f "
					% [_leg_f, short, float(pr[0]), float(pr[1])]
					+ "in_sight=%s prompt=%s p=%.2f,%.2f,%.2f "
					% [str(pr[2]).to_lower(), _interact.prompt_group(),
						p.x, p.y, p.z]
					+ "camfwd=%.2f,%.2f,%.2f steer=%.2f,%.2f,%.2f v=%.2f"
					% [cf.x, cf.y, cf.z, (t2 - p).normalized().x,
						(t2 - p).normalized().y, (t2 - p).normalized().z,
						_player.velocity.length()])
		# A USE LEG ENDS A LITTLE AFTER THE KEY GOES DOWN, not when the body is
		# close. `near` is only the fallback for an object that cannot be
		# reached: it stops the leg burning its whole budget standing on top of
		# something that will never prompt, and the stall line then says how far
		# short it was.
		#
		# THE DELAY IS THE PRESS ITSELF. `interact.gd` runs a control in for
		# `press_frames` and reads the travel back off the mesh's own world AABB
		# on the frame AFTER it starts, so a leg that ended on the keypress
		# reported `travel_mm = 0.00` for a press that worked -- the object had
		# not moved yet. Measured: 4.00 mm one frame later.
		if _interact != null and _interact.use_count() > _v_use_before:
			if _v_press_f < 0:
				_v_press_f = _leg_f
			elif _leg_f >= _v_press_f + 24:
				done = true
	if not done and _leg_f >= int(leg["budget"]):
		_v_stalls.append("leg%d(%s)_%.1fm_short"
			% [_leg, String(leg["what"]).replace(" ", "_"),
				(short if _leg_best > 1e29 else _leg_best)])
		done = true
	if done:
		if leg.has("record"):
			_record_visit(int(leg["record"]), p)
		_leg += 1
		_leg_f = 0
		_leg_best = 1e30
	return dir


func _leg_started(leg: Dictionary) -> void:
	_leg_best = 1e30
	if bool(leg.get("use", false)):
		# EACH VISIT PRESSES ITS OWN KEY. `_used_ok` is the one-shot that stops
		# the headless test mashing E every frame; without resetting it the
		# second visit would inherit the first visit's press and report a use
		# that never happened.
		_used_ok = false
		_v_prompted = false
		_v_best_eye = 1e30
		_v_best_axis = 1e30
		_v_sight_f = 0
		_v_press_f = -1
		_v_use_before = (_interact.use_count() if _interact != null else 0)
	if String(leg.get("to", "")) == "door_out" and _doors != null:
		# The door claim is per visit: how open it got on the way in LAST time is
		# not evidence about this time.
		_doors.reset_peak(_v_door)


## Once a frame, whatever leg is running: the things that are only true while
## the body is where it is.
func _visit_sample() -> void:
	if _interact != null and String(_interact.prompt_group()) == _v_group:
		_v_prompted = true


func _record_visit(n: int, p: Vector3) -> void:
	var res := {}
	res["door"] = (_doors.peak_openness(_v_door) if _doors != null else -1.0)
	res["near_m"] = (p.distance_to(_v_at) if _leg_best > 1e29 else _leg_best)
	res["noticed"] = (_people.noticed_count() if _people != null else 0)
	res["turned"] = (_people.turned_deg() if _people != null else 0.0)
	res["face"] = (_people.facing_error_deg(p) if _people != null else -1.0)
	res["prompted"] = _v_prompted
	res["used"] = (_interact.used_group() if _interact != null else "")
	res["presses"] = ((_interact.use_count() - _v_use_before)
		if _interact != null else 0)
	res["travel_mm"] = (_interact.used_travel_mm() if _interact != null else 0.0)
	res["prompt_text"] = (_interact.used_prompt() if _interact != null else "")
	res["wired"] = _stream.is_resident(_v_id)
	# WHY, NOT JUST WHETHER. Only computed when the claim already failed.
	res["why"] = ("" if bool(res["prompted"]) or _interact == null
		# A LEG THAT NEVER SAW THE OBJECT HAS NO BEST. Printing the sentinel
		# gives `eye_range=1000000000000000019884624838656.00`, which is a
		# number nobody can read and a claim nobody made.
		else (("never in range; " if _v_best_eye > 1e29
			else "best over the leg: eye_range=%.2f off_axis=%.0fdeg "
				% [_v_best_eye, _v_best_axis])
			+ "in_sight_frames=%d; at the end: " % _v_sight_f
			+ _interact.probe(_v_group)))
	_v_res[n - 1] = res
	print("walk: VISIT %d of %s -- door '%s' opened to %.2f, got within %.2f m "
		% [n, _v_id, _v_door, float(res["door"]), float(res["near_m"])]
		+ "of %s, %d person(s) noticed (%.0f deg turned, %.0f deg off), "
		% [_v_group, int(res["noticed"]), float(res["turned"]),
			float(res["face"])]
		+ "prompted=%s pressed=%d moved %.2f mm%s"
		% [str(res["prompted"]).to_lower(), int(res["presses"]),
			float(res["travel_mm"]),
			("" if String(res["why"]) == "" else "  [%s]" % String(res["why"]))])


var _leg_best := 1e30
var _v_prompted := false
var _v_use_before := 0
var _v_press_f := -1
var _v_best_eye := 1e30
var _v_best_axis := 1e30
var _v_sight_f := 0


## Watch the streamer's resident set from outside and note the frame each cell
## first appeared in it. Deliberately not a callback: a gate that asks the thing
## under test to report its own timing is a gate that cannot catch it lying.
func _note_residency() -> void:
	for id in _stream.resident_ids():
		if not _s_ready_frame.has(id):
			_s_ready_frame[id] = _frame


func _print_stream_verdict() -> void:
	var crossings: int = maxi(_s_entered.size() - 1, 0)
	var ent := PackedStringArray()
	for i in _s_entered:
		ent.append(str(i))
	var mode := ("nostream" if _stream.disabled else "stream")
	# WHAT MAKES IT A PASS, stated as the conjunction it is. `late` and
	# `double_loads` are the two requirements; `crossings` is the reason to
	# believe the run exercised them at all -- a test that never left its start
	# cell would otherwise report a flawless zero on both.
	var ok: bool = (crossings >= 1 and _s_late == 0 and _off_floor == 0
		and int(_stream.double_loads) == 0 and not bool(_stream.disabled))
	var why := PackedStringArray()
	if crossings < 1:
		why.append("no cell boundary was crossed")
	if _s_late > 0:
		why.append("%d cell(s) entered before resident" % _s_late)
	if _off_floor > 0:
		why.append("%d frame(s) off the floor" % _off_floor)
	if _stream.double_loads > 0:
		why.append("%d double load(s)" % _stream.double_loads)
	if _stream.disabled:
		why.append("streaming disabled (this is the control and MUST fail)")
	var visit := ""
	if _visiting:
		visit = _visit_verdict(why)
		ok = ok and why.is_empty()
	# `inf` rather than a sentinel when nothing streamed in during the run: every
	# cell entered was resident before the walk began, which is an infinite lead
	# and not a missing measurement. A negative number here would read as the
	# failure this gate exists to catch. `-1` is reserved for the control, where
	# a cell really was entered with no lead at all.
	var lead := ("inf" if _s_min_lead_m > 1e29 and _s_late == 0
		else ("-1" if _s_min_lead_m > 1e29 else "%.2f" % _s_min_lead_m))
	print(("STREAMTEST mode=%s ok=%s start=%d dir=%s prime_ms=%d "
		+ "traverse_m=%.2f floor_m=%.2f net_m=%.2f offfloor=%d/%d "
		+ "crossings=%d entered=%s late=%d min_lead_m=%s min_lead_frames=%d "
		+ "%s%s%s why=%s") % [
		mode, str(ok).to_lower(), _start_cell,
		("+1" if _s_dir > 0.0 else "-1"), _prime_ms,
		_path_m, _s_floor_m, _traverse_from.distance_to(_traverse_prev),
		_off_floor, _t_traverse, crossings, ",".join(ent), _s_late, lead,
		(-1 if _s_min_lead_f > 1 << 29 else _s_min_lead_f),
		_stream.report(), visit, _crowd_report(),
		("-" if why.is_empty() else ";".join(why).replace(" ", "_"))])


## WAS THERE A CROWD IN THE CORRIDOR AT ALL, and what were they made of?
##
## PRINTED UNCONDITIONALLY, because the alternative is the defect that let the
## NPC assertions vanish for six runs: a gate that reads `offfloor=0` from a run
## where `--crowd-glbs` pointed at nothing has measured a corridor with nobody in
## it and called the crowd fixed. `walkers` is what makes the claim falsifiable;
## `crowd_collider` is which of the two mechanisms actually ran, so a control
## cannot silently be the subject.
func _crowd_report() -> String:
	var s := (" offfloor_runs=%d offfloor_longest=%d lift_mm=%.1f drop_mm=%.1f"
		+ " eye_err_deg=%.1f/%.1f") % [
		_offf_episodes, _offf_run_max, _lift_m * 1000.0, _drop_m * 1000.0,
		(0.0 if _eye_err_n == 0 else _eye_err_sum / float(_eye_err_n)),
		_eye_err_max]
	if _people == null:
		# THE SAME TOKENS EITHER WAY. A verdict whose field set changes with the
		# thing it describes is the defect that let the NPC assertions vanish
		# for six runs -- `walkable.py` guarded them on the presence of the very
		# token they asserted.
		return s + (" walkers=0 crowd_travel_m=0.0 crowd_collider=-"
			+ " push_m=0.00 push_max_mm=0.0")
	return s + " walkers=%d crowd_travel_m=%.1f crowd_collider=%s %s" % [
		_people.crowd_count(), _people.crowd_travel_m(),
		_people.walker_collider_report(), _people.push_report()]


## THE THREE CLAIMS, TWICE, AND THE FREE IN BETWEEN.
##
## Every one is a thing a player would notice and every one has a control that
## turns it off: `--no-cell-wiring` (the build before this session),
## `--no-doors`, `--no-people`, `--no-interact`, `--no-unwire`. A run in which
## all five pass is a run measuring nothing.
func _visit_verdict(why: PackedStringArray) -> String:
	var out := " visit_cell=%d visit_id=%s door_key=%s use_group=%s" % [
		_v_cell, _v_id, _v_door, _v_group]
	for n in 2:
		var r: Dictionary = _v_res[n]
		if r.is_empty():
			why.append("visit %d never happened" % (n + 1))
			out += " v%d=none" % (n + 1)
			continue
		out += (" v%d_door_open=%.2f v%d_near_m=%.2f v%d_noticed=%d "
			+ "v%d_turned_deg=%.1f v%d_face_err_deg=%.1f v%d_prompted=%s "
			+ "v%d_used=%s v%d_presses=%d v%d_travel_mm=%.2f") % [
			n + 1, float(r["door"]), n + 1, float(r["near_m"]),
			n + 1, int(r["noticed"]), n + 1, float(r["turned"]),
			n + 1, float(r["face"]), n + 1,
			str(bool(r["prompted"])).to_lower(),
			n + 1, ("-" if String(r["used"]) == "" else String(r["used"])),
			n + 1, int(r["presses"]), n + 1, float(r["travel_mm"])]
		var tag := "visit%d" % (n + 1)
		# 1 -- THE DOOR OPENED. `peak_openness`, not the live value: the body
		# walked THROUGH it and it shut again behind them.
		if float(r["door"]) <= 0.0:
			why.append("%s: the pressure door '%s' never opened (%.2f) -- in a "
				% [tag, _v_door, float(r["door"])]
				+ "streamed cell it is a wall")
		# 2 -- SOMEBODY REACTED. Not "there are people in the cell": a body that
		# turned is a body that was told a player exists.
		if int(r["noticed"]) < 1 or float(r["turned"]) <= 0.0:
			why.append("%s: %d person(s) noticed and the nearest turned %.1f deg"
				% [tag, int(r["noticed"]), float(r["turned"])])
		# 3 -- AND SOMETHING IN IT WORKED. Prompted, pressed, and the object's
		# own mesh moved: `travel_mm` is read back off the scene graph, so a use
		# that returned true and moved nothing reports zero.
		if not bool(r["prompted"]):
			why.append("%s: never prompted by %s (got within %.2f m: %s)"
				% [tag, _v_group, float(r["near_m"]), String(r.get("why", "?"))])
		if int(r["presses"]) < 1:
			why.append("%s: %s was never used" % [tag, _v_group])
		elif float(r["travel_mm"]) <= 0.0:
			why.append("%s: %s was used and did not move" % [tag, _v_group])
	# 4 -- AND IT SURVIVED THE CELL GOING AWAY AND COMING BACK.
	out += " freed=%s wired_cells=%d unwired_cells=%d double_wires=%d" % [
		str(_v_freed).to_lower(), int(_stream.wired), int(_stream.unwired),
		_double_wires + (_doors.double_wires if _doors != null else 0)
			+ (_people.double_wires if _people != null else 0)
			+ (_interact.double_wires if _interact != null else 0)]
	out += " stale_prompt_frames=%d stale_leaves=%d stale_parts=%d" % [
		(_interact.stale_prompt_frames if _interact != null else 0),
		(_doors.stale_leaves if _doors != null else 0),
		(_people.stale_parts if _people != null else 0)]
	if not _v_stalls.is_empty():
		out += " stalls=" + ",".join(PackedStringArray(_v_stalls))
	if not _v_freed:
		why.append("cell %s was never freed -- the second visit is not a "
			% _v_id + "re-entry")
	var dbl: int = (_double_wires + (_doors.double_wires if _doors != null else 0)
		+ (_people.double_wires if _people != null else 0)
		+ (_interact.double_wires if _interact != null else 0))
	if dbl > 0:
		why.append("%d cell(s) were wired twice without being released" % dbl)
	if _interact != null and _interact.stale_prompt_frames > 0:
		why.append("%d frame(s) prompted for an object whose cell had been "
			% _interact.stale_prompt_frames + "freed")
	if _doors != null and _doors.stale_leaves > 0:
		why.append("%d door leaf reference(s) outlived their cell"
			% _doors.stale_leaves)
	if _people != null and _people.stale_parts > 0:
		why.append("%d inhabitant mesh reference(s) outlived their cell"
			% _people.stale_parts)
	if _doors != null and not _doors.orphan_panels().is_empty():
		why.append("door panel(s) resident with no leaves: %s"
			% ",".join(PackedStringArray(_doors.orphan_panels())))
	return out


var _streaming := false
var _start_cell := 0
var _prime_ms := 0
var _s_dir := 1.0
var _s_r := 0.0
var _s_z := 0.0
var _s_w := 0.0
var _s_lookahead := 20.0
var _s_turnaround := 0
var _s_here := -1
var _s_entered: Array[int] = []
var _s_late := 0
var _s_floor_m := 0.0
var _s_min_lead_m := 1e30
var _s_min_lead_f := 1 << 30
var _s_ready_frame := {}
var _floor_p := Vector3.ZERO
var _have_floor_p := false
var _offf_run := 0
var _offf_run_max := 0
var _offf_episodes := 0
var _lift_m := 0.0
var _drop_m := 0.0
var _self_step := false
var _eye_err_sum := 0.0
var _eye_err_n := 0
var _eye_err_max := 0.0


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
	# THE STREAMING GATE runs its own frame: residency has to be updated from the
	# body's position every physics step, not from a timer, because the claim
	# being tested is about where the body IS when a cell arrives.
	if _streaming:
		_stream_frame(delta)
		return
	# AND THE SHIPPED BUILD STREAMS TOO, which it did not until session 4k.
	#
	# `_streaming` is set by `_run_stream_test` alone, so `_stream.update` --
	# the whole of residency: free, activate, request -- ran ONLY inside the
	# gate that measures it. A player launched by `main.gd` got the primed
	# start cell and never a second one: walk to its edge and the floor stops,
	# because nothing ever asked for the neighbour. The manifest was loaded, the
	# radius was derived, the budget was read, and the streamer was inert.
	#
	# It is the same shape as the finding this session exists to fix, one level
	# down, and it is this repository's most-repeated defect: FINISHED, TESTED
	# MACHINERY WITH NO CALLER ON THE SHIPPED PATH. `stream.gd` scored a gate
	# and moved nobody.
	#
	# AFTER the `_streaming` return and not before it, because `_stream_frame`
	# calls `update` itself: two calls a frame would activate two cells a frame
	# -- against that function's own "AT MOST ONE PER FRAME, because instancing,
	# the trimesh collider, the material bind and the fittings are all
	# main-thread work" -- and would double `_frames`, which is what the lag
	# stress control counts in.
	if _stream != null and _player != null:
		_stream.update(_player.global_position)
	# The shot phase: settle the body on the floor, then take the picture from
	# where it ended up. No wish vector -- a photograph is of somebody standing.
	if _shooting:
		_frame += 1
		_player.step(delta, Vector2.ZERO, false, false)
		_push_off(delta)
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
		_push_off(delta)
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
		_push_off(delta)
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
		# ON THE FLOOR PLANE, and that is not a detail. A waypoint sits 50 mm
		# above the shell on purpose so its settle drop can be asserted, and a
		# body standing on the deck can never close a RADIAL offset -- measure
		# the gap in 3D and the last waypoint is never reached, the body dithers
		# at it for ever, and the run scores as "walked" while going nowhere.
		# `walkable.room_target`'s docstring records the same defect one level up.
		var aim := _goto
		if not _wp.is_empty():
			var up: Vector3 = _player.body_up()
			while _wp_i < _wp.size() - 1:
				var d: Vector3 = _wp[_wp_i] - _player.global_position
				if (d - up * d.dot(up)).length() >= _wp_tol:
					break
				_wp_i += 1
			aim = _wp[_wp_i]
		_player.step(delta, Vector2.ZERO, false, false,
			aim - _player.global_position)
	else:
		_player.step(delta, Vector2(0, 1), false, false)
	_push_off(delta)
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
			if not _wp.is_empty():
				goto_s += " wp_done=%d/%d" % [_wp_i + 1, _wp.size()]
			if _doors != null:
				# THE MOST OPEN IT EVER GOT, not how open it is now. This read
				# the LIVE openness at the frame the verdict prints, which for a
				# body that walked THROUGH a door is several seconds after it
				# shut again behind them -- so a run that worked perfectly
				# reported `door_open=0.00` and read as the failure. The visit
				# gate has used `peak_openness` since it was written; the deck
				# walk was still sampling too late. See docs/runtime-4h.md.
				goto_s += " door_open=%.2f door_open_now=%.2f" % [
					_doors.peak_openness(_door_key),
					_doors.openness(_door_key)]
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
		# DROP IS A HEIGHT AND WAS MEASURED AS A DISTANCE. `MAX_DECK_DROP_M`'s
		# own words are "a drop of more than a step means it is not where the
		# shell says the floor is" -- a claim about the floor's RADIUS -- and
		# `spawn.distance_to(_rest)` is the 3D displacement, which on a deck
		# with people on it also counts every millimetre a passing walker
		# pushed the body sideways while it settled. Both are printed:
		# `drop` unchanged, `drop_up` along the body's own up, which on a ring
		# is radial and different at every angle.
		print(("WALKTEST rest=%.3f,%.3f,%.3f on_floor=%s fell=%s moved_1s=%.3f "
			+ "drop=%.3f drop_up=%.3f legs=%.2f/%.2f/%.2f/%.2f "
			+ "traverse_m=%.2f net_m=%.2f offfloor=%d/%d%s") % [
			_rest.x, _rest.y, _rest.z, str(_on_floor).to_lower(),
			str(fell).to_lower(), _moved_1s, spawn.distance_to(_rest),
			(spawn - _rest).dot(_player.body_up()),
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
## NOBODY IS INSIDE ANYBODY. One call, after every place this file steps the
## body, so the walk test and the stream test separate identically. See
## `npc.gd::push_off`: it is a horizontal correction and never a vertical one,
## because `move_and_slide` cannot resolve a person without costing the floor.
func _push_off(delta: float) -> void:
	if _people != null:
		_people.push_off(delta)


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
## THE WAY THERE, not just the place. `--goto` alone steers STRAIGHT at a point,
## which measures straight-line reachability and calls it walkability: driven at
## a room 40 degrees round the ring it walked the body off a curved corridor --
## 1,661 m travelled with 1,084 of 1,800 frames in the air. `station/roomnav.py`
## and `station/route_walk.py` already compute the way a person would take; this
## follows it. Empty means the old straight steer, so every existing caller is
## unchanged.
var _wp: Array[Vector3] = []
var _wp_i := 0
var _wp_tol := 0.5
var _door_key := ""
