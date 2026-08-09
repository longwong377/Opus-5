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
## THE STATION'S SPIN, omega^2 in rad^2/s^2, handed to `player.gd` so the body
## falls along its own radius at its own g instead of straight down at Earth's.
##
## WHY IT IS HERE AND NOT A CONSTANT. `g = omega^2 r` on a rigid rotor, so one
## deck row of `cell_manifest.json` -- `floor_r_m` with `floor_g` -- fixes the
## field at EVERY radius, including the ones with no deck on them. Left at 0 this
## file derives it from the deck it is standing on and says so; `--omega2=` and
## `--gravity=` both override, in that order of specificity.
##
## `--gravity=` WINS OUTRIGHT and that is deliberate. `station/drum_walk.py`
## passes a measured `--gravity=` for the drum floor, and a caller that has
## stated a number must not have it quietly replaced -- so a run with `--gravity`
## is byte-identical to the pre-4r build. See `_derive_omega2`.
@export var omega2: float = 0.0
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

## The deck's occlusion geometry, written beside the deck `.glb` by
## `tools/export_scene.py::write_deck_occluder` as an `ArrayOccluder3D` in a
## `.tscn`. THESE SIX LINES ARE THE THIRD RUNG OF THREE, and without them the
## other two are inert: `station/occluders.py` builds a provably-contained
## occluder (9/9, 0 breaches of 2,880 rays) and `project.godot` turns
## `use_occlusion_culling` on, but Godot only consults occluders that are
## actually in the tree. `station/budget.py::occlusion_chain` reports rung 3
## as the failing one until this loads something.
##
## READ INV-371 BEFORE EXPECTING A SAVING. Godot culls per INSTANCE AABB, not
## per triangle, and `export_gltf` writes one primitive per OBJ group whose
## corridor groups span the whole 345 deg ring -- so their bounding box
## contains the camera and no occluder can reject them. Measured: 7.8% of the
## frame overall and 0.2% of structure. The larger win is next door and is
## the same fix: cutting the deck into the 18 cells `stream.gd` already bakes
## takes frustum submission down 39% BEFORE any occluder.
@export var occluder_path: String = ""
## WHO MAY STAND WHERE -- `place -> {need, name, why}`, baked by
## `station/boot.py::_checks` off `consequence.certain_check`. Passed straight
## through to `hud.gd`, which fires it on the place transition it already
## computes; this node does not read it and does not need to.
@export var checks: Dictionary = {}
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
	if args.has("omega2"):
		omega2 = float(args["omega2"])
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
	# WITHOUT THIS, A COMMAND-LINE RUN CAN NEVER LOAD ONE, and every
	# verification command written against `walk.tscn` was structurally
	# incapable of showing whether the occluder worked. `main.tscn` sets
	# `occluder_path` as an export var from boot.json and was the only path
	# that ever could; the reviewer's own repro could not have caught the bug.
	if args.has("occluder"):
		occluder_path = args["occluder"]
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
	# BOTH LISTS, AND THE SPLIT IS WHY DIALOGUE WENT DARK. `_load_sidecars`
	# separates the cast into `_actors` (baked into the deck mesh) and
	# `_actors_occ` (instanced, carrying a `who.day` timetable). Passing only
	# the baked half was correct while most occupants were baked; since
	# `populace.ROOM_INSTANCED` it is empty. The build printed
	# `cast of 111 -- 111 instanced occupant(s), 0 baked into the deck mesh`
	# and then `dialogue: 0 people can speak, of 0 in the cast`, with 444
	# exchanges naming a group with no body.
	#
	# THIS IS THE W5 DEFECT AGAIN, ONE SUBSYSTEM OVER: a representation changed
	# and the consumer that reads the other representation was left behind.
	# There it was the notice loop; here it is the whole conversation layer. An
	# occupant with a timetable is not less of a person to talk to -- they are
	# the ones with somewhere to be, which is what makes them worth talking to.
	_wire_dialogue(_actors + _actors_occ)

	_wire_hud()

	if args.has("gravity-gate"):
		_run_gravity_gate(args)
	elif args.has("corpse-gate"):
		_run_corpse_gate(args)
	elif args.has("stream-test"):
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


## The deck's occlusion geometry, from an absolute path outside `res://` — the
## same route the deck `.glb` already takes.
##
## CALLED FROM BOTH LEVEL PATHS, AND THE FIRST CUT WAS NOT. It went into
## `_load_level` alone, which the SHIPPED build never runs: the shipped scene is
## STREAMED, and `_load_level` is the monolithic path. The scene booted, the
## occluder never loaded, and nothing said so — which is instance NINE of this
## project's signature defect, created while closing instance eight, in the one
## file whose own header records the same trap for `stream.gd` and
## `dialogue.gd`. It was caught by launching the scene and grepping for the line
## this function prints, which is the only check that could have caught it:
## `budget.occlusion_chain` reported `applied=True` throughout, because it looks
## for a REFERENCE in the source and cannot see which branch runs.
##
## A missing file is not an error. The deck renders identically without it, only
## slower, so this must never be the reason a player cannot walk.
## AND A MISSING FILE IS NOT SILENT EITHER, which is what actually let this
## survive. Returning with no print meant `boot.json`'s `"occluder": ""` read
## exactly like a deck that had one: the file DID exist, in `scene/deck/`, and
## the shipped build boots from `scene/station/`. Two directories, one name, and
## nothing said which was loaded. Say which of the modes this run is in, always.
func _load_occluder() -> void:
	if occluder_path == "":
		print("walk: NO OCCLUDER -- occluder_path is empty; every triangle "
			+ "behind every wall is submitted. `python3 station/occluders.py "
			+ "--emit` writes one, `station/boot.py` names it.")
		return
	if not FileAccess.file_exists(occluder_path):
		print("walk: NO OCCLUDER -- looked for %s and it is not there"
			% occluder_path)
		return
	var occ := ResourceLoader.load(occluder_path)
	if occ is PackedScene:
		var node := (occ as PackedScene).instantiate()
		add_child(node)
		# THE VERTEX COUNT, so an EMPTY occluder cannot pass as a loaded one.
		# "loaded" and "occluding" are different claims and this prints both.
		var n := 0
		for c in node.get_children():
			if c is OccluderInstance3D and c.occluder != null:
				n += c.occluder.vertices.size()
		print("walk: occluder loaded from %s -- %d occluder vertices"
			% [occluder_path, n])
		if n == 0:
			push_warning("walk: the occluder scene carries no geometry")
	else:
		push_warning("walk: %s is not a PackedScene" % occluder_path)


func _load_level() -> bool:
	var scene := _load_glb(glb_path)
	if scene == null:
		return false
	add_child(scene)
	_visual = scene
	_dress_level(scene)

	_load_occluder()

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
	_load_occluder()
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


## The cast list, split by WHAT KIND OF OBJECT each person is.
##
## A row whose `who` carries a `day` is an INSTANCED ROOM OCCUPANT --
## `populace.populate` emitted a placement and a timetable instead of triangles,
## so their body comes out of the shared crowd library and their state comes out
## of the station clock. A row without one is a body baked into the deck mesh,
## which `npc.gd::collect` binds to its own geometry exactly as before.
##
## THEY MUST NOT BOTH BE WIRED. An occupant promoted to an instance has their
## baked meshes hidden; handing the same row to `collect()` as well would leave
## a `Person` turning invisible geometry to face the player, and would count that
## person twice in every report.
var _actors: Array = []
var _actors_occ: Array = []
## WHICH DECK THE SIDECARS DESCRIBE, off their own file names. A sidecar is per
## DECK -- `blue_0_0_crowd.json`, `blue_0_0_actors.json` -- while `cells_path` on
## the shipped build is the MERGED manifest: 907 cells over 76 decks. So every
## sidecar row this process holds belongs to exactly one of those decks, and a
## row must never be bound into a cell of another one. See `_cell_is_ours`.
##
## Empty when no sidecar was named, or when their names do not agree on a deck.
## Both cases disable the scoping rather than guessing, because a wrong deck name
## here would silently empty the station -- the failure mode this file exists to
## stop, not one to add.
var _sidecar_deck := ""
## Every deck we hold sidecar rows for, as a set. See `_load_sidecars`.
var _sidecar_decks := {}


## The deck a sidecar path names, or "" -- `.../blue_0_0_crowd.json` -> blue_0_0.
func _deck_of_sidecar(path: String) -> String:
	if path == "":
		return ""
	var f := path.get_file()
	for suffix in ["_crowd.json", "_actors.json", "_interact.json",
			"_dialogue.json"]:
		if f.ends_with(suffix):
			return f.substr(0, f.length() - suffix.length())
	return ""


## Every deck's three sidecar files, as {stem: {actors, crowd, interact}}.
##
## THE DIRECTORY COMES FROM THE PATHS THE CALLER ALREADY PASSED, so this adds no
## new setting to the boot manifest and cannot point somewhere the caller did not
## choose. A file that is not there is "" and `_read_rows` returns nothing for it,
## which is how a deck with a cast and no interactables loads correctly.
##
## The stem is everything before the suffix -- `blue_0_0` out of
## `blue_0_0_actors.json` -- which is the same rule `_deck_of_sidecar` uses and
## the same one `boot.py` names its files by.
func _sidecar_set() -> Dictionary:
	var out := {}
	var mine := {"actors": actors_path, "crowd": crowd_path,
		"interact": interact_path}
	# THE CONTROL, AND THE FALLBACK. `--one-deck-sidecars` restores the exact
	# pre-fix behaviour for an A/B; a caller whose paths name no directory we can
	# list gets the same, because inventing a directory would be worse than the
	# defect being fixed.
	var dir := ""
	for k in mine:
		if String(mine[k]) != "":
			dir = String(mine[k]).get_base_dir()
			break
	if dir == "" or _args().has("one-deck-sidecars"):
		var stem := ""
		for k in mine:
			stem = _deck_of_sidecar(String(mine[k]))
			if stem != "":
				break
		if _args().has("one-deck-sidecars"):
			_say_once("walk: ONE DECK'S SIDECARS (control) -- every other deck "
				+ "will be empty, which is what the shipped build used to do")
		return {} if stem == "" else {stem: mine}
	var d := DirAccess.open(dir)
	if d == null:
		var stem2 := _deck_of_sidecar(String(actors_path))
		return {} if stem2 == "" else {stem2: mine}
	for f in d.get_files():
		var name := String(f)
		for suffix in [["_actors.json", "actors"], ["_crowd.json", "crowd"],
				["_interact.json", "interact"]]:
			if not name.ends_with(String(suffix[0])):
				continue
			var stem3 := name.substr(0, name.length() - String(suffix[0]).length())
			if not out.has(stem3):
				out[stem3] = {"actors": "", "crowd": "", "interact": ""}
			(out[stem3] as Dictionary)[String(suffix[1])] = dir.path_join(name)
			break
	# The caller's own three win for their deck, so an explicitly passed path is
	# never silently replaced by one this scan happened to find.
	var own := _deck_of_sidecar(String(actors_path))
	if own == "":
		own = _deck_of_sidecar(String(crowd_path))
	if own != "":
		if not out.has(own):
			out[own] = {"actors": "", "crowd": "", "interact": ""}
		for k2 in mine:
			if String(mine[k2]) != "":
				(out[own] as Dictionary)[k2] = String(mine[k2])
	return out


## EVERY DECK'S SIDECARS, NOT ONE DECK'S.
##
## THE SHIPPED BUILD LOADED ONE DECK'S PEOPLE FOR A SEVENTY-SIX-DECK STATION, and
## that is not a bug in any part -- it is the shape of the wiring. `boot.py` names
## `blue_0_0_actors.json`, `blue_0_0_crowd.json` and `blue_0_0_interact.json`;
## `main.gd` hands those three strings over; this function read exactly those
## three files; and `_cell_is_ours` then correctly refused to put blue_0_0's cast
## into any other deck's cell. Every step was right and the result was a station
## of 907 cells in which 75 decks out of 76 were EMPTY BY CONSTRUCTION -- walk off
## the spawn deck and the crowd, the cast and every usable object stop.
##
## The three named paths still decide WHICH DIRECTORY, so nothing about the boot
## manifest has to change and a caller who passes one deck's files still gets a
## sane single-deck run. What changes is that the directory is then read for every
## other deck beside them, and each row is stamped with the deck it came out of.
##
## IT IS AFFORDABLE, MEASURED RATHER THAN ASSUMED: the whole station is 3,957 cast
## rows, 1,994 crowd placements and 419 interactables across 71 sidecar sets --
## a few megabytes of JSON parsed once at load. The bodies are already shared
## MultiMesh instances out of `crowd_lod*.glb`, so holding the rows costs no
## geometry; only cells that are RESIDENT ever wire anybody, and that is unchanged.
##
## `--one-deck-sidecars` is the control: it restores the old behaviour exactly.
func _load_sidecars() -> void:
	var paths := _sidecar_set()
	var all: Array = []
	_actors = []
	_actors_occ = []
	_ix_rows = []
	_crowd_rows = []
	_sidecar_decks = {}
	for stem in paths:
		var trio: Dictionary = paths[stem]
		# THE STEM IS STAMPED ON THE ROW, because after this point a row's own
		# file is gone and the only two questions that matter -- "is this row on
		# the cell's deck" and "which decks did we load" -- both need it. The key
		# is `_deck` with an underscore so it cannot collide with anything
		# `station/populace.py` or `interact.py` writes.
		for r in _read_rows(String(trio.get("actors", ""))):
			(r as Dictionary)["_deck"] = stem
			all.append(r)
			var who = (r as Dictionary).get("who", {})
			if who is Dictionary and (who as Dictionary).has("day"):
				_actors_occ.append(r)
			else:
				_actors.append(r)
		for r in _read_rows(String(trio.get("interact", ""))):
			(r as Dictionary)["_deck"] = stem
			_ix_rows.append(r)
		for r in _read_rows(String(trio.get("crowd", ""))):
			(r as Dictionary)["_deck"] = stem
			_crowd_rows.append(r)
		_sidecar_decks[stem] = true
	# Kept for the report and for the single-deck case; empty when more than one
	# deck is loaded, which is what every message below already means by it.
	_sidecar_deck = ("" if _sidecar_decks.size() != 1
		else String(_sidecar_decks.keys()[0]))
	if _sidecar_decks.size() > 1:
		print("walk: sidecars for %d decks -- the whole station, not just the "
			% _sidecar_decks.size() + "one the boot manifest names "
			+ "(--one-deck-sidecars is the control)")
	if not _actors_occ.is_empty():
		print("walk: cast of %d -- %d instanced occupant(s) with a timetable, "
			% [all.size(), _actors_occ.size()]
			+ "%d baked into the deck mesh" % _actors.size())
	# SAY WHAT LOADED, ON EVERY RUN, INCLUDING WHEN NOTHING DID.
	#
	# THE LINE BELOW IS THE ONE THAT WAS MISSING AND IT COST A SESSION. A streamed
	# launch printed `+wired <cell> -- doors now 0, 0 person(s), 0 walker(s),
	# 0 interactable(s)` on every cell, and that zero has THREE different causes
	# which the line could not tell apart: no sidecar was passed at all, the
	# sidecars belong to another deck, or the cell is honestly empty. It was read
	# as "the streamed path wires nobody" and the streamed path was fine -- the
	# command had no `--actors/--crowd/--interact` on it, and the shipped spawn
	# sits in five cells that genuinely contain nobody. A count with no
	# denominator beside it is not a measurement.
	print("walk: sidecars%s -- %d cast row(s) (%d with a timetable), "
		% [("" if _sidecar_deck == "" else " for deck " + _sidecar_deck),
			all.size(), _actors_occ.size()]
		+ "%d crowd placement(s), %d interactable(s)"
		% [_crowd_rows.size(), _ix_rows.size()]
		+ ("" if not (all.is_empty() and _crowd_rows.is_empty()
			and _ix_rows.is_empty())
			else "  -- NOTHING IS LOADED, so no cell can ever wire anybody"))
	if interact_path != "" and _ix_rows.is_empty():
		push_error("walk: %s is not a JSON array" % interact_path)


## Is this cell on the deck the sidecars describe?
##
## A CELL FROM ANOTHER DECK MUST NOT BE HANDED THIS DECK'S PEOPLE, and until this
## existed it was. `stream.distance_to` is the BINNING rule and it is deliberately
## radius-blind (see its own docstring) -- it tests ANGLE and Z and never radius,
## because `bake()::_split` bins triangles that way and an identity test that
## disagreed with the bake would lose content. That is right for "which cell is
## this triangle in" and wrong on its own for "whose crowd is this", because the
## decks of this station are concentric: `blue_1_0` sits at a different radius
## behind the same arc and the same z as `blue_0_0`.
##
## MEASURED ON THE SHIPPED MANIFEST, not argued: of `blue_0_0_crowd.json`'s 444
## placements, 88 are claimed by more than one cell and every one of those extra
## claims -- 98 of them -- is a cell on one of six OTHER decks (blue_1_0 29,
## blue_1_5 24, blue_0_2 19, blue_0_1 16, blue_0_5 6, blue_1_3 4). Within
## blue_0_0 the sum over all 103 cells is exactly 444, so this filter cannot drop
## a single row of its own deck. And it is live rather than theoretical:
##
##     walk: +wired blue_1_0_c05z12 -- doors now 0, 0 person(s), 10 walker(s), ...
##
## is ten of blue_0_0's corridor crowd standing inside a blue_1_0 cell, at
## blue_0_0's radius, drawn a second time if both cells are ever resident at once.
##
## NOT A RADIAL BAND, AND THAT IS THE WHOLE POINT. `residency_distance` has one
## and it is right for residency; used here it would be the binning rule with a
## radius test bolted on, and the bake never binned by radius. Measured on this
## deck's own crowd, 36 placements sit up to 2.36 m OUTBOARD of their deck floor
## and 127 more than 3.6 m inboard, so a band would silently drop 163 of 444
## people who are exactly where the generator put them. The deck NAME is exact,
## costs a string compare, and cannot be off by a metre.
##
## DEGRADES TO THE OLD BEHAVIOUR RATHER THAN TO AN EMPTY STATION, twice over: no
## sidecar deck (nobody named one) and no `deck` key on the cell (a per-deck
## manifest such as `blue_0_0_cells.json`, where every cell is ours by
## construction) both return true. `--no-deck-scope` is the control.
func _cell_is_ours(c: Dictionary) -> bool:
	# ASKED AGAINST THE SET OF LOADED DECKS, not against one name. With every
	# deck's sidecars loaded this is true for any cell whose deck we hold rows
	# for -- which is the point -- and the per-row test in `_row_is_here` is what
	# now stops one deck's crowd landing in the deck concentric with it. The two
	# together do exactly what the single-deck check did before, and do it for 76
	# decks instead of 1.
	if _sidecar_decks.is_empty() or c.is_empty():
		return true
	var d := String(c.get("deck", ""))
	if d == "":
		return true
	if _sidecar_decks.has(d):
		return true
	if _args().has("no-deck-scope"):
		_say_once("walk: cross-deck scoping DISABLED (control) -- this deck's "
			+ "people will be bound into other decks' cells")
		return true
	return false


## Is this ROW on this CELL's deck?
##
## THE HALF OF THE OLD GUARD THAT STILL HAS WORK TO DO. `stream.distance_to` is
## radius-blind on purpose -- it tests angle and z and never radius, because that
## is how `bake()::_split` binned the triangles -- so it cannot tell `blue_0_0`
## from `blue_1_0`, which sits behind the same arc at a different radius.
## Measured on the shipped manifest: 98 of blue_0_0's 444 crowd placements are
## claimed by a cell on one of six other decks.
##
## When only one deck was loaded, refusing the whole cell was enough. Now that
## every deck is loaded, refusing the cell would refuse the deck its own people,
## so the question moves down one level: this row against this cell. A row or a
## cell that does not name a deck passes, which keeps a per-deck manifest -- where
## every cell is ours by construction -- working exactly as before.
func _row_is_here(r: Dictionary, c: Dictionary) -> bool:
	var rd := String(r.get("_deck", ""))
	var cd := String(c.get("deck", ""))
	if rd == "" or cd == "":
		return true
	if rd == cd:
		return true
	return _args().has("no-deck-scope")


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
	# THE OCCUPANTS, AND THEY NEED THE LIBRARY FIRST. An occupant is a reference
	# into `crowd_lod*.glb`; admitting one before the MultiMeshes exist gives a
	# walker in no bucket, which draws nothing and reports fine.
	_wire_occupants(scene, "")
	_wire_dialogue(_actors + _actors_occ)


func _make_people() -> bool:
	if _people != null:
		return true
	if _actors.is_empty() and _actors_occ.is_empty():
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


## Admit the room occupants of one cell (or of the whole level, tag "").
##
## THE MULTIMESH BUCKETS HAVE TO BE SIZED FOR THEM. `prepare_crowd` allocates
## from a placement list and `instance_count` cannot grow, so the occupant rows
## are handed in alongside the corridor's -- an occupant is a placement against
## the same 168 shared bodies and belongs in the same allocation.
func _wire_occupants(vis: Node, tag: String) -> int:
	if _people == null or _actors_occ.is_empty():
		return 0
	if not _load_crowd_libs():
		_say_once("walk: %d room occupant(s) have a timetable and NO shared "
			% _actors_occ.size() + "body library -- they cannot be drawn")
		return 0
	if not _crowd_ready:
		_crowd_ready = true
		_people.prepare_crowd(_crowd_libs, _crowd_rows + _actors_occ)
	var rows := _actors_occ
	if tag != "" and vis != null:
		# WHOSE CELL IS THIS? An occupant DOES have a mesh in the cell -- their
		# baked one, until the deck is rebuilt -- but the honest test is the one
		# `stream.gd` already owns, because after the rebuild there will be no
		# mesh to find. Same question as `_rows_in_cell` asks of a walker.
		rows = []
		# AND THE SAME DECK GUARD, for the same reason. `cell_at` picks ONE cell
		# out of all 907 by nearest floor radius, so an occupant is far less
		# exposed than a walker -- measured, all 363 of this deck's cast land on a
		# blue_0_0 cell today. That is a property of the current content, not of
		# the code: the winning cell is chosen station-wide and nothing in that
		# choice knows which deck's cast list is loaded.
		if not _cell_is_ours(_stream.cell_by_id(tag) if _stream != null else {}):
			return 0
		var cell_here: Dictionary = ({} if _stream == null
			else _stream.cell_by_id(tag))
		for r in _actors_occ:
			if not _row_is_here(r, cell_here):
				continue
			var p := Vector3(float((r as Dictionary).get("x", 0.0)),
				float((r as Dictionary).get("y", 0.0)),
				float((r as Dictionary).get("z", 0.0)))
			if _stream == null or _stream.cell_at(p) == _cell_index(tag):
				rows.append(r)
	var n: int = _people.add_occupants(rows, tag, vis)
	if n > 0:
		print("walk: %d room occupant(s) instanced%s -- %s"
			% [n, ("" if tag == "" else " in " + tag),
				_people.occupant_report()])
	return n


func _cell_index(id: String) -> int:
	if _stream == null:
		return -1
	for c in _stream.cells:
		if String((c as Dictionary).get("id", "")) == id:
			return int((c as Dictionary).get("index", -1))
	return -1


## Load the shared body libraries and tell `npc.gd` the ladder. Split out of
## `_wire_crowd` because a STREAMED build sizes the MultiMeshes from the whole
## deck's placement list up front and then admits each cell's walkers as it
## arrives -- `MultiMesh.instance_count` cannot grow.
## Every shared-body library beside the crowd sidecar, when the caller named
## none.
##
## INSTANCE TEN OF THIS PROJECT'S SIGNATURE DEFECT, and it is in the shipped
## build. `main.gd::_configure_walk` sets `crowd_path` and NOT `crowd_glbs` or
## `crowd_ladder`, so `_load_crowd_libs` returned false on its third line and
## every launch of `godot --path godot` printed `0 walker(s)` on every cell. The
## whole instanced-corridor argument -- 963 people, 88% fewer triangles, "the
## only form they can MOVE in" -- reached a developer's command line and never
## reached the game. Measured before this function existed:
##
##     walk: +wired blue_0_0_c13 -- doors now 1, 1 person(s), 0 walker(s), ...
##
## The libraries are not somewhere else: `deck.py` writes them into the same
## directory as the crowd placement list. So the fallback is to look there,
## which is one directory listing and cannot invent a path that does not exist.
func _derived_crowd_glbs() -> Array:
	if crowd_path == "":
		return []
	var dir := crowd_path.get_base_dir()
	var d := DirAccess.open(dir)
	if d == null:
		return []
	var out := []
	for f in d.get_files():
		if String(f).begins_with("crowd_lod") and String(f).ends_with(".glb"):
			out.append(dir.path_join(String(f)))
	out.sort()
	return out


## The LOD ladder, when the caller named none.
##
## NOT INVENTED, AND DELIBERATELY CONSERVATIVE. `populace.crowd_ladder()` derives
## the real one -- ((18 m, 2), (45 m, 4), (400 m, 8)) -- from
## `schedule.NPC_BUDGET`, and copying those distances into GDScript would be a
## second description of a budget that lives in Python. What this can know
## without repeating anything is which libraries actually shipped, so it puts
## everybody on the COARSEST of them: the rung that cannot be over budget. A
## caller with the real ladder still passes it and this is never consulted.
func _derived_ladder(paths: Array) -> String:
	var lods := []
	for p in paths:
		var n := String(p).get_file().trim_prefix("crowd_lod").trim_suffix(".glb")
		if n.is_valid_int():
			lods.append(int(n))
	if lods.is_empty():
		return ""
	lods.sort()
	return "1e9:%d" % lods[lods.size() - 1]


func _load_crowd_libs() -> bool:
	if not _crowd_libs.is_empty():
		return true
	if _people == null:
		return false
	if _crowd_rows.is_empty() and _actors_occ.is_empty():
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
	if paths.is_empty():
		paths = _derived_crowd_glbs()
		if not paths.is_empty():
			if crowd_ladder == "":
				crowd_ladder = _derived_ladder(paths)
			_say_once("walk: no crowd library was named -- found %d beside %s, "
				% [paths.size(), crowd_path.get_file()]
				+ "ladder %s (the coarsest that shipped; pass "
				% crowd_ladder + "--crowd-ladder= for the derived one)")
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
		np += _wire_occupants(vis, id)
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
	_wired_people += np
	_wired_walkers += nc
	_wired_ix += ni
	print("walk: +wired %s -- doors now %d, %d person(s), %d walker(s), "
		% [id, nd, np, nc] + "%d interactable(s)" % ni
		+ ("" if nd + np + nc + ni > 0 else "  -- " + _empty_reason(id)))


## Counters so the LEVEL can be asked the question, not only a cell. A streamed
## build has no moment at which everything is loaded, so the monolithic path's
## one-line totals have no equivalent here; these are what a log can be grepped
## for to answer "is anybody home on this station".
##
## CUMULATIVE, NOT LIVE, and the line that prints them says so. `npc.gd::release`
## returns people and walkers as one number, so a live figure would need this file
## to keep a second tally of who is in which cell -- a second description of what
## `npc.gd` already knows, which is the defect hard rule 4 exists to stop. What
## these answer is "has this build ever wired anybody", which is the question that
## was open.
var _wired_people := 0
var _wired_walkers := 0
var _wired_ix := 0


## WHY THIS CELL WIRED NOTHING -- and there are three different answers.
##
## Session 4t was spent on the wrong one. `+wired ... 0, 0, 0, 0` on every cell
## was read as "the streamed path wires nobody"; the streamed path was correct
## and the cause was that the launch had no sidecar arguments on it. The second
## launch, with them, wired 4 walkers into the same cells. A count that cannot say
## which zero it is turns a five-minute check into a session.
func _empty_reason(id: String) -> String:
	if _actors.is_empty() and _actors_occ.is_empty() and _crowd_rows.is_empty() \
			and _ix_rows.is_empty():
		return ("NOTHING IS LOADED: no cast list, no crowd list and no "
			+ "interactables list, so NO cell can ever wire anybody. Pass "
			+ "--actors= --crowd= --interact= (main.gd takes them off boot.json)")
	var c: Dictionary = ({} if _stream == null else _stream.cell_by_id(id))
	if not _cell_is_ours(c):
		return ("this cell is on deck %s and no sidecar was found for it -- "
			% String(c.get("deck", "?"))
			+ "%d deck(s) loaded, %d cells in the manifest"
			% [_sidecar_decks.size(),
				0 if _stream == null else _stream.cells.size()])
	return ("this cell is honestly EMPTY -- the deck's sidecars hold %d cast, "
		% (_actors.size() + _actors_occ.size())
		+ "%d crowd and %d interactable(s), and none of them are in this arc"
		% [_crowd_rows.size(), _ix_rows.size()]
		+ " (this level has wired %d person(s), %d walker(s), %d interactable(s) "
		% [_wired_people, _wired_walkers, _wired_ix]
		+ "so far, over %d resident cell(s))" % _wired_cells.size())


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
	# WHOSE CROWD IS THIS. The test below is radius-blind on purpose and therefore
	# cannot tell one deck from the deck concentric with it; `_cell_is_ours` is
	# what makes it a question about THIS deck. Measured: 98 of these 444 rows are
	# claimed by a cell on another deck.
	if not _cell_is_ours(c):
		return out
	for r in _crowd_rows:
		# PER ROW NOW, because every deck's crowd is loaded. `_row_is_here` is
		# the deck-name half of the old whole-cell guard; `distance_to` is still
		# the arc-and-z half, unchanged and still the bake's own rule.
		if not _row_is_here(r, c):
			continue
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
	# BEFORE `bind`, not after. `bind` calls `_wallet`, which is the first read
	# of the player's rung, and a checkpoint table that arrived a frame later
	# would miss the place the player SPAWNS in -- which on this build is a
	# checked one.
	_hud.checks = checks
	_hud.bind(_player, _interact, glb_path, interact_path, _visual)
	if not checks.is_empty():
		print("hud: %d checkpoints wired" % checks.size())


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


## The SI definition of standard gravity, used only to turn the deck table's
## `floor_g` back into m/s^2. `main.gd::_spin_omega2` uses the same constant for
## the same conversion; the schema keeps it as
## `station.rotation.standard_gravity_m_s2`.
const G0_M_S2 := 9.80665


## The deck table row for one deck, through `stream.gd`'s reader.
##
## ONE READER. `stream.gd::deck_row` already parses `cell_manifest.json` and is
## loud on a miss; a second parse here would be a second copy of where the
## station's spin is written down, which is the defect that produced `INV-451`
## one file over. On the monolithic path there is no streamer yet, so a bare
## instance is made for the read and thrown away -- `deck_row` touches no state.
func _deck_row(sector: String, ring_index: int, deck_index: int) -> Dictionary:
	if _stream != null:
		return _stream.deck_row(sector, ring_index, deck_index)
	var n := Node3D.new()
	n.name = "DeckTableRead"
	n.set_script(load("res://scripts/stream.gd"))
	add_child(n)
	var row: Dictionary = n.deck_row(sector, ring_index, deck_index)
	n.queue_free()
	return row


## Work out the station's spin, and SAY WHERE IT CAME FROM.
##
## The order is most-specific-first and every branch is reported, because the
## thing this replaces was a scalar nobody set and a mode nobody checked:
##
##   1. `--gravity=` -- the caller has stated a number. It wins outright and no
##      spin is derived, so `drum_walk.py`'s measured drum-floor value is
##      untouched and its run is byte-identical to the pre-4r build.
##   2. `--omega2=` or the export -- somebody handed us the spin.
##   3. the deck the body is standing on, off `cell_manifest.json`'s own
##      `floor_r_m`/`floor_g` pair: omega^2 = g0 * floor_g / floor_r_m.
##   4. nothing -- keep the old behaviour and print why, rather than invent one.
func _derive_omega2(args: Dictionary) -> String:
	# THE CONTROLS FOR THE GRAVITY GATE, and they belong HERE rather than after
	# the body exists, because `_spawn_player` stands the capsule up from the
	# field: a control applied after the spawn would leave the fixed pose in place
	# and only half the defect would come back.
	if args.has("legacy-field") or args.has("legacy-deck"):
		omega2 = 0.0
		gravity_mode = ("deck" if args.has("legacy-deck") else "drum")
		gravity_m_s2 = 9.81
		return ("LEGACY CONTROL -- mode=%s at %.2f m/s2 and no spin. "
			% [gravity_mode, gravity_m_s2]
			+ ("This is `player.gd`'s own export default."
				if gravity_mode == "deck"
				else "This is what the shipped build did: `main.gd` set the "
				+ "mode and nobody set the scalar."))
	if args.has("gravity"):
		omega2 = 0.0
		return ("STATED --gravity=%.4f m/s2 along %s -- no spin derived, the "
			% [gravity_m_s2, gravity_mode] + "caller's number wins")
	if omega2 > 0.0:
		return "given omega2=%.8f rad2/s2" % omega2
	var sector := ""
	var ri := -1
	var di := -1
	if _stream != null:
		var src: Dictionary = _stream.plan.get("source", {})
		sector = String(src.get("sector", ""))
		ri = int(src.get("ring_index", -1))
		di = int(src.get("deck_index", -1))
	else:
		# `<sector>_<ring>_<deck>.glb` -- the name `station/deck.py` writes and
		# `boot.json` repeats as its `deck` key. Anything else (the drum ground,
		# a single room) does not parse and falls through to branch 4.
		# THE FIRST THREE TOKENS, NOT EXACTLY THREE. `station/walkable.py` writes
		# `blue_0_0`, `blue_0_0_z7121` (a deck has up to six walkable clusters)
		# and `blue_0_0_nouse` (the stripped control) -- so an exact-length test
		# would give one form of the same deck its real gravity and the other two
		# Earth's, which is the kind of split this project keeps paying for.
		var stem := (collision_path if collision_path != "" else glb_path
			).get_file().get_basename().trim_suffix("_col")
		var p := stem.split("_")
		if p.size() >= 3 and p[1].is_valid_int() and p[2].is_valid_int():
			sector = p[0]
			ri = int(p[1])
			di = int(p[2])
	if sector == "" or ri < 0 or di < 0:
		return ("NO SPIN STATED -- this build names no deck, so the body keeps "
			+ "mode=%s at %.4f m/s2 (the pre-4r field)" % [gravity_mode,
			gravity_m_s2])
	var row: Dictionary = _deck_row(sector, ri, di)
	var r := float(row.get("floor_r_m", 0.0))
	var g := float(row.get("floor_g", 0.0))
	if r <= 1.0 or g <= 0.0:
		return ("NO SPIN STATED -- no deck_table row for %s ring %d deck %d, so "
			% [sector, ri, di] + "the body keeps mode=%s at %.4f m/s2"
			% [gravity_mode, gravity_m_s2])
	omega2 = g * G0_M_S2 / r
	return ("omega2=%.8f rad2/s2 from cell_manifest deck_table[%s]: "
		% [omega2, String(row.get("id", "?"))]
		+ "floor_g %.4f at r=%.2f m, period %.3f s"
		% [g, r, TAU / sqrt(omega2)])


## The player's capsule, kept because two gates need to know how big the body is
## and a second copy of 1.8 x 0.35 is a second description of a person.
var _cap_h := 1.8
var _cap_r := 0.35


func _spawn_player() -> void:
	_player = CharacterBody3D.new()
	_player.set_script(load("res://scripts/player.gd"))
	# DOWN IS OUTWARD ALONG A RADIUS AND IT IS NOT 9.81. See `player.gd`'s header:
	# `main.gd` has always set `gravity_mode = "drum"` so the shipped DIRECTION was
	# right, and nothing anywhere set `gravity_m_s2`, so the shipped MAGNITUDE was
	# Earth's -- 9.81 against this deck's 7.4522, +31.7%, on the only build a
	# player launches. DERIVED FIRST: it can rewrite the mode and the scalar.
	var why := _derive_omega2(_args())
	_player.gravity_mode = gravity_mode
	_player.gravity_m_s2 = gravity_m_s2
	_player.omega2 = omega2
	print("walk: gravity -- " + why)
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	# 1.8 m tall, 0.35 m radius: a person, and the same stature the render
	# harness stands its cameras at.
	caps.height = _cap_h
	caps.radius = _cap_r
	shape.shape = caps
	shape.position = Vector3(0, _cap_h * 0.5, 0)
	_player.add_child(shape)
	# WHAT THE PLAYER COLLIDES WITH, SAID OUT LOUD. Until session 4q nothing
	# here set either field, so the shipped player carried Godot's defaults --
	# layer 1, mask 1 -- and that happened to be right. A default nobody chose
	# is not the same as a decision, and this one was load-bearing in a way
	# nobody had noticed: it is the reason `--ragdoll-solid` was inert. Bones
	# sit on `RAGDOLL_LAYER` (16) and Godot 4.4's `move_and_collide` consults
	# THE MOVER'S MASK ONLY -- measured, see `ragdoll.gd` -- so the player could
	# never collide with a bone whatever the RID exceptions said.
	#
	# The crowd is deliberately absent from this mask and always has been:
	# `npc.gd::_layer` puts people on `PEOPLE_LAYER` with mask 0 precisely so
	# `move_and_slide` never resolves against them, because a capsule touching
	# anything refuses the floor snap. Ragdolls are excluded for the same
	# reason and separated by `push_off` instead. `--ragdoll-solid` is the
	# control that puts them back, and it is `ragdoll.gd`'s to decide.
	const Ragdoll := preload("res://scripts/ragdoll.gd")
	_player.collision_layer = Ragdoll.WORLD_LAYER
	_player.collision_mask = Ragdoll.WORLD_LAYER | Ragdoll.player_extra_mask()
	if Ragdoll.player_extra_mask() != 0:
		print("walk: player collision_mask = %d -- CONTROL, the player is "
			% _player.collision_mask
			+ "solid to ragdoll bones and will lose the floor on contact")
	_player.position = spawn
	# STAND THE CAPSULE UP BEFORE ITS FIRST FRAME. `shape.position` is
	# `(0, 0.9, 0)` in the BODY's frame, so it follows the body's own up -- but
	# only once something has set the body's basis, and until session 4r nothing
	# did until `player.step()` ran. The body therefore entered the tree with an
	# IDENTITY basis, i.e. a 1.8 m capsule lying along world +Y, which on a ring
	# deck at 264.8 degrees is 5.2 degrees off and at 90 degrees is upside down.
	# `player.gd`'s own header records what that costs when it persists: a capsule
	# through the floor and the wall, reporting `on_floor = true`, unable to move.
	#
	# It is the same class as the field defect above -- an orientation left to a
	# default nobody chose -- and it is one line, because `stand_basis()` is the
	# expression `step()` itself uses.
	#
	# AFTER `add_child`, NOT BEFORE. `Node3D::get_global_transform` fails outright
	# outside the tree, and `stand_basis()` reads the body's own world position to
	# know which way the radius points.
	add_child(_player)
	_player.global_transform = Transform3D(_player.stand_basis(), spawn)
	# ONE THING STEPS THE BODY. Every headless mode in this file drives
	# `player.step()` from `_physics_process` below, and `player.gd` has its own
	# `_physics_process` that steps it again from a keyboard that is not there --
	# a zero wish, which is harmless to the walk and rebuilds the basis from
	# `_yaw`, which is not harmless to the eye. See `player.gd::drive_externally`
	# and `docs/runtime-4h.md`. A build with a window and a player at the
	# keyboard is untouched: none of these three flags is present.
	var a2 := _args()
	if ((a2.has("walk-test") or a2.has("stream-test") or a2.has("shot")
			or a2.has("gravity-gate") or a2.has("corpse-gate"))
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
			+ " push_m=0.00 push_max_mm=0.0 occupants=0 occ_changes=0")
	# `occ_changes` IS THE CLAIM. `occupants` counts bodies, which a diorama has
	# too; the number of times one of them changed what they were doing is the
	# only figure in this line a station full of statues cannot produce.
	return s + (" walkers=%d crowd_travel_m=%.1f crowd_collider=%s %s "
		+ "occupants=%d occ_changes=%d occ_travel_m=%.1f "
		+ "people_draws=%d people_buckets=%d") % [
		_people.crowd_count(), _people.crowd_travel_m(),
		_people.walker_collider_report(), _people.push_report(),
		_people.occupant_count(), _people.occupant_changes(),
		_people.occupant_travel_m(), _people.crowd_draw_calls(),
		_people.crowd_buckets()]


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
	# THE TWO SESSION-4r GATES. Both drive the body themselves and quit when they
	# have their answer; neither runs unless its flag is on the command line.
	if _g_gate:
		_gravity_frame(delta)
		return
	if _c_gate:
		_corpse_frame(delta)
		return
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
	if _people == null:
		return
	# THE RAGDOLL DIRECTOR IS A SIBLING OF THIS NODE. `main.gd::_start_ragdolls`
	# builds it as its own child AFTER `_build_station` has added this one, so it
	# cannot be found in `_ready` and is offered here instead: one hashed child
	# lookup on the frames before a body exists, nothing after.
	if _people.ragdoll_director() == null:
		var par := get_parent()
		if par != null:
			var d := par.get_node_or_null("Ragdolls")
			if d != null:
				_people.watch_ragdolls(d)
	_people.push_off(delta)


# ===========================================================================
#  THE GRAVITY GATE -- is the field right ALL THE WAY ROUND the ring?
# ===========================================================================
#
# WHAT IT IS FOR. `player.gd::gravity_dir()` returned `Vector3(0, -1, 0)` at
# 9.81 m/s^2 in `"deck"` mode and nothing anywhere set the scalar in `"drum"`
# mode either. Both survived because THE SPAWN SITS AT RING ANGLE 264.8 DEGREES,
# where -Y is 5.2 degrees off the true radial and a body stands up perfectly
# well. Every gate in this repository measured the body at that one angle.
#
# So this one puts the body at EVERY angle the deck has -- the eighteen cells of
# blue/0/0, twenty degrees apart -- and asks two questions per angle:
#
#   1. WHAT THE BODY THINKS. `body_up()` against the true inward radial at its
#      own position, and `gravity_g()` against omega^2 r.
#   2. WHAT THE BODY DOES. Lift it into the corridor's own measured headroom,
#      let it fall, and measure the acceleration off its velocity: a constant
#      cannot fake `g = omega^2 r` and a -Y field cannot fake a radius. This is
#      the half that a variable read-back could never be.
#
# THE TARGET POINTS ARE THE BUILD'S OWN. Each cell carries the floor point
# `stream.bake::_floor_point` measured off that cell's collision shell; nothing
# here writes down where the corridor is.
#
# TWO CONTROLS, BOTH OF WHICH MUST FAIL:
#   --legacy-deck   `player.gd`'s export default: -Y at 9.81.
#   --legacy-field  what the shipped build actually had: radial at 9.81.
var _g_gate := false
var _g_idx: Array = []
var _g_at := -1
var _g_phase := 0
var _g_f := 0
var _g_rows: Array = []
var _g_true_w2 := 0.0
var _g_r_floor := 0.0
var _g_up_tol_deg := 0.0
var _g_g_tol := 0.005
var _g_a_tol := 0.010
var _g_drop_tol := 0.0
var _g_settle_f := 40
var _g_fall_f := 16
var _g_lift := 0.0
var _g_rest := Vector3.ZERO
var _g_v0 := Vector3.ZERO
var _g_air := 0
var _g_dt := 0.0
var _g_row: Dictionary = {}


func _run_gravity_gate(args: Dictionary) -> void:
	if _stream == null or _player == null:
		print("GRAVITY gate=FAIL -- this mode needs the streamed build, which "
			+ "is what carries a floor point per ring angle. Launch it as "
			+ "`godot --headless --path godot -- --no-coldstart --gravity-gate`.")
		get_tree().quit(2)
		return
	# THE TRUTH IS READ INDEPENDENTLY OF THE THING UNDER TEST. `_derive_omega2`
	# may have been overruled by a control, so the reference comes straight off
	# the deck table here. Both use the same reader, and that is the point: the
	# number has ALWAYS been available to the runtime -- the defect was that the
	# body never used it.
	var src: Dictionary = _stream.plan.get("source", {})
	var row: Dictionary = _deck_row(String(src.get("sector", "")),
		int(src.get("ring_index", -1)), int(src.get("deck_index", -1)))
	var fr := float(row.get("floor_r_m", 0.0))
	var fg := float(row.get("floor_g", 0.0))
	if fr <= 1.0 or fg <= 0.0:
		print("GRAVITY gate=FAIL -- no deck_table row for this build, so there "
			+ "is nothing to check the field against")
		get_tree().quit(2)
		return
	_g_true_w2 = fg * G0_M_S2 / fr
	_g_r_floor = float((_stream.plan.get("corridor", {}) as Dictionary
		).get("r_floor_m", fr))
	# THE TOLERANCES ARE DERIVED, NOT PICKED. INV-481.
	#   up   -- the angle the player's OWN capsule radius subtends at the deck
	#           radius. Inside that, "the field points at a different part of the
	#           same body" and no gameplay can tell.
	#   g    -- 0.5%, about ten times the 0.051% spread between the 251 deck rows'
	#           own implied omega^2 (`floor_g` is stored to four places). The
	#           defect being caught is 31.7%.
	#   a    -- 1.0%, twice the above, because a measured acceleration also
	#           carries whatever one frame of contact does to it.
	#   drop -- the spawn's own height above the floor plus Godot's default
	#           `floor_snap_length`, both read rather than assumed.
	_g_up_tol_deg = rad_to_deg(atan2(_cap_r, _g_r_floor))
	_g_idx = []
	for c in _stream.cells:
		_g_idx.append(int(c["index"]))
	_g_idx.sort()
	if args.has("angles"):
		var keep: Array = []
		var step: int = maxi(1, int(_g_idx.size() / maxi(1, int(args["angles"]))))
		for i in range(0, _g_idx.size(), step):
			keep.append(_g_idx[i])
		_g_idx = keep
	_g_settle_f = int(args.get("settle", "40"))
	# HOW FAR A BODY IS EXPECTED TO FALL when it is put down: the cell's own spawn
	# point stands `r_floor - r_spawn` off the shell (0.200 m here, written by
	# `stream.bake::_floor_point` and never by this file), plus Godot's default
	# `floor_snap_length` of 0.10 m.
	var c0: Dictionary = _stream.cell_by_index(int(_g_idx[0]))
	var s0 := Vector3(c0["spawn"][0], c0["spawn"][1], c0["spawn"][2])
	_g_drop_tol = (_g_r_floor - sqrt(s0.x * s0.x + s0.y * s0.y)) + 0.10
	_g_gate = true
	_g_at = -1
	_g_phase = 0
	print(("GRAVITY gate: %d ring angles on %s, omega2=%.8f rad2/s2 "
		+ "(period %.3f s) from deck_table[%s] floor_g=%.4f at r=%.2f m; "
		+ "corridor floor r=%.3f m; player %s")
		% [_g_idx.size(), String(src.get("sector", "?")), _g_true_w2,
		TAU / sqrt(_g_true_w2), String(row.get("id", "?")), fg, fr, _g_r_floor,
		_player.field_report()])
	print(("GRAVITY tol: up %.4f deg (capsule r=%.2f m at r=%.1f m), g %.2f%%, "
		+ "a %.2f%%, settle %d frames, fall window derived per angle")
		% [_g_up_tol_deg, _cap_r, _g_r_floor, _g_g_tol * 100.0,
		_g_a_tol * 100.0, _g_settle_f])


## The true down at a point: radially OUTWARD from the +Z spin axis.
func _true_down(p: Vector3) -> Vector3:
	var radial := Vector3(p.x, p.y, 0.0)
	return (radial.normalized() if radial.length() > 0.001 else Vector3(0, -1, 0))


func _ang_deg(a: Vector3, b: Vector3) -> float:
	return rad_to_deg(acos(clampf(a.normalized().dot(b.normalized()),
		-1.0, 1.0)))


func _gravity_frame(delta: float) -> void:
	_g_dt = delta
	match _g_phase:
		0:      # -- PLACE. Teleport to the next cell's own measured floor point.
			_g_at += 1
			if _g_at >= _g_idx.size():
				_gravity_verdict()
				return
			var ci: int = _g_idx[_g_at]
			var c: Dictionary = _stream.cell_by_index(ci)
			var sp := Vector3(c["spawn"][0], c["spawn"][1], c["spawn"][2])
			_player.velocity = Vector3.ZERO
			_player.global_position = sp
			# THE POSE IS SET FROM THE FIELD, exactly as `_spawn_player` does, so
			# a control that breaks the field breaks the pose too and the gate
			# sees both.
			_player.global_transform = Transform3D(_player.stand_basis(), sp)
			# SYNCHRONOUS. A body dropped into a cell that has not arrived falls
			# through the deck and the verdict blames gravity for streaming.
			_stream.prime(ci)
			var arc: Dictionary = c.get("arc", {})
			_g_row = {
				"cell": ci,
				"ang": (float(arc.get("a0_deg", 0.0))
					+ float(arc.get("a1_deg", 0.0))) * 0.5,
				"place": sp,
			}
			_g_f = 0
			_g_phase = 1
		1:      # -- SETTLE. Stand still and let the body find the floor.
			_player.step(delta, Vector2.ZERO, false, false)
			_push_off(delta)
			_g_f += 1
			if _g_f < _g_settle_f:
				return
			_g_rest = _player.global_position
			var dn: Vector3 = _true_down(_g_rest)
			var place: Vector3 = _g_row["place"]
			_g_row["on_floor"] = _player.is_on_floor()
			_g_row["r"] = sqrt(_g_rest.x * _g_rest.x + _g_rest.y * _g_rest.y)
			_g_row["drop"] = (_g_rest - place).dot(dn)
			_g_row["up_err"] = _ang_deg(_player.body_up(), -dn)
			# THE CAPSULE'S OWN AXIS, not the field's. `shape.position` rides the
			# body's basis, so a body whose basis is identity is a person lying
			# down -- which is what every spawn on this station was until 4r.
			_g_row["pose_err"] = _ang_deg(_player.global_transform.basis.y, -dn)
			_g_row["det"] = _player.global_transform.basis.determinant()
			_g_row["g_read"] = _player.gravity_g()
			_g_row["g_want"] = _g_true_w2 * float(_g_row["r"])
			_g_phase = 2
		2:      # -- LIFT, into headroom this corridor is MEASURED to have.
			var up: Vector3 = -_true_down(_g_rest)
			var space := get_world_3d().direct_space_state
			var from: Vector3 = _g_rest + up * 0.05
			var q := PhysicsRayQueryParameters3D.create(from, from + up * 8.0)
			q.exclude = [_player.get_rid()]
			var hit: Dictionary = space.intersect_ray(q)
			var head: float = (from.distance_to(hit["position"])
				if hit.has("position") else 8.0)
			_g_row["headroom"] = head
			# Clear of the ceiling by the same 50 mm a spawn stands off a floor.
			_g_lift = maxf(0.0, head - _cap_h - 0.05)
			# THE FALL WINDOW IS DERIVED FROM THE LIFT AND THE NUMBER BEING
			# DISPROVED: the largest whole frames for which even a 9.81 m/s^2
			# field leaves the body clear of the deck. Semi-implicit Euler puts
			# the body at 0.5*a*t^2*(1 + 1/n), so the check uses that and not the
			# continuous form.
			var budget: float = _g_lift - 0.05
			_g_fall_f = 0
			for n in range(1, 60):
				var t: float = float(n) * delta
				if 0.5 * 9.81 * t * t * (1.0 + 1.0 / float(n)) > budget:
					break
				_g_fall_f = n
			_g_row["lift"] = _g_lift
			_g_row["fall_f"] = _g_fall_f
			if _g_fall_f < 8:
				# Not enough room to measure anything. Say so rather than
				# reporting a number taken over four frames.
				_g_row["a_meas"] = -1.0
				_g_row["a_err_deg"] = -1.0
				_g_rows.append(_g_row)
				_g_phase = 0
				return
			_player.global_position = _g_rest + up * _g_lift
			_player.velocity = Vector3.ZERO
			_g_air = -1
			_g_f = 0
			_g_phase = 3
		3:      # -- FALL. Measure the field the body actually integrates.
			_player.step(delta, Vector2.ZERO, false, false)
			_g_f += 1
			if _g_air < 0:
				if _player.is_on_floor():
					if _g_f > 6:
						# It never left the floor: the lift failed, which is a
						# result and not a reason to keep waiting.
						_g_row["a_meas"] = -2.0
						_g_row["a_err_deg"] = -1.0
						_g_rows.append(_g_row)
						_g_phase = 0
					return
				_g_air = 0
				_g_v0 = _player.velocity
				var pa: Vector3 = _player.global_position
				_g_row["r_air0"] = sqrt(pa.x * pa.x + pa.y * pa.y)
				return
			_g_air += 1
			if _g_air < _g_fall_f:
				return
			var dv: Vector3 = _player.velocity - _g_v0
			var pb: Vector3 = _player.global_position
			var dn2: Vector3 = _true_down(pb)
			var t2: float = float(_g_air) * delta
			_g_row["a_meas"] = dv.dot(dn2) / t2
			_g_row["a_err_deg"] = _ang_deg(dv, dn2)
			_g_row["slides"] = _player.get_slide_collision_count()
			# THE FIELD IS WEAKER HIGHER UP, AND THE MEASUREMENT HAS TO SAY SO.
			# `g = omega^2 r` and a body 1.1 m above the deck is 1.1 m NEARER the
			# axis, so it falls measurably more slowly than the floor value: over
			# this window the difference is ~0.4%, which is larger than the whole
			# tolerance. Comparing the measured acceleration against the floor's g
			# would therefore report a real physical effect as gate error. The
			# reference is omega^2 at the mean radius of the fall itself.
			_g_row["r_air1"] = sqrt(pb.x * pb.x + pb.y * pb.y)
			_g_row["g_air"] = _g_true_w2 * 0.5 * (float(_g_row["r_air0"])
				+ float(_g_row["r_air1"]))
			_g_rows.append(_g_row)
			_g_phase = 0


func _gravity_verdict() -> void:
	_g_gate = false
	set_physics_process(false)
	var ok := true
	var n_floor := 0
	var up_max := 0.0
	var pose_max := 0.0
	var g_max := 0.0
	var a_max := 0.0
	var adir_max := 0.0
	var drop_max := -1e30
	var det_min := 1e30
	var measured := 0
	if _g_rows.is_empty():
		print("GRAVITY gate=FAIL -- no angle was ever measured")
		get_tree().quit(1)
		return
	for r in _g_rows:
		var g_err: float = absf(float(r["g_read"]) / maxf(1e-9,
			float(r["g_want"])) - 1.0)
		var a: float = float(r.get("a_meas", -1.0))
		# Against the field over the FALL's own radii, not the floor's -- see the
		# note where `g_air` is taken.
		var g_air: float = float(r.get("g_air", r["g_want"]))
		var a_err: float = (absf(a / maxf(1e-9, g_air) - 1.0)
			if a > 0.0 else 1e9)
		var bad: Array[String] = []
		if not bool(r["on_floor"]):
			bad.append("OFF-FLOOR")
		if float(r["up_err"]) > _g_up_tol_deg:
			bad.append("up")
		if float(r["pose_err"]) > _g_up_tol_deg:
			bad.append("pose")
		if float(r["det"]) < 0.999:
			bad.append("mirrored")
		if g_err > _g_g_tol:
			bad.append("g")
		if float(r["drop"]) > _g_drop_tol or float(r["drop"]) < -0.02:
			bad.append("drop")
		if a <= 0.0:
			bad.append("NOT-MEASURED")
		else:
			measured += 1
			if a_err > _g_a_tol:
				bad.append("a")
			if float(r["a_err_deg"]) > _g_up_tol_deg:
				bad.append("a-dir")
			a_max = maxf(a_max, a_err)
			adir_max = maxf(adir_max, float(r["a_err_deg"]))
		if bool(r["on_floor"]):
			n_floor += 1
		up_max = maxf(up_max, float(r["up_err"]))
		pose_max = maxf(pose_max, float(r["pose_err"]))
		g_max = maxf(g_max, g_err)
		drop_max = maxf(drop_max, float(r["drop"]))
		det_min = minf(det_min, float(r["det"]))
		if not bad.is_empty():
			ok = false
		print(("  ang %5.1f deg cell %2d r=%8.3f  on_floor=%s drop=%+.3f m  "
			+ "up_err=%7.3f deg pose_err=%7.3f det=%+.4f  g_read=%7.4f "
			+ "want=%7.4f (%+6.2f%%)  head=%.2f lift=%.2f n=%d  a_meas=%s "
			+ "vs g(fall)=%7.4f  a_dir=%6.2f deg  %s")
			% [float(r["ang"]), int(r["cell"]), float(r["r"]),
			("yes" if bool(r["on_floor"]) else "NO "), float(r["drop"]),
			float(r["up_err"]), float(r["pose_err"]), float(r["det"]),
			float(r["g_read"]), float(r["g_want"]),
			(float(r["g_read"]) / maxf(1e-9, float(r["g_want"])) - 1.0) * 100.0,
			float(r.get("headroom", 0.0)), float(r.get("lift", 0.0)),
			int(r.get("fall_f", 0)),
			("%7.4f (%+6.2f%%)" % [a, (a / maxf(1e-9, g_air) - 1.0)
				* 100.0] if a > 0.0 else "  none          "), g_air,
			float(r.get("a_err_deg", -1.0)),
			("ok" if bad.is_empty() else "FAIL " + ", ".join(bad))])
	print(("GRAVITY gate=%s angles=%d on_floor=%d/%d measured=%d "
		+ "up_err_max=%.4f deg (tol %.4f) pose_err_max=%.4f det_min=%+.4f "
		+ "g_err_max=%.3f%% (tol %.2f%%) a_err_max=%s a_dir_max=%.3f deg "
		+ "drop_max=%.3f m (tol %.3f)")
		% [("PASS" if ok else "FAIL"), _g_rows.size(), n_floor, _g_rows.size(),
		measured, up_max, _g_up_tol_deg, pose_max, det_min, g_max * 100.0,
		_g_g_tol * 100.0,
		("%.3f%%" % (a_max * 100.0) if measured > 0 else "n/a"),
		adir_max, drop_max, _g_drop_tol])
	get_tree().quit(0 if ok else 1)


# ===========================================================================
#  THE CORPSE GATE -- a player walks AROUND a body, not through it
# ===========================================================================
#
# `STATE.md` §24.5: *"a settled ragdoll does not push the player aside the way a
# standing person does"*. `ragdoll.gd` excepts the player's RID from all sixteen
# bones on purpose -- see `npc.gd`'s header for the floor-loss diagnosis that
# forced it -- so the only thing that can separate them is `npc.gd::push_off`,
# and until session 4r that loop knew about walkers and baked people and not
# about anybody lying down.
#
# WHAT THIS DRIVES: settle, drop a real body out of the corridor crowd where a
# collapse would put one, let it settle at the deck's own 7.45 m/s^2, then walk
# the player straight at it and measure the closest the two ever come.
#
# THE MEASUREMENT IS `npc.gd`'s OWN. `nearest_ragdoll_clearance()` is the same
# capsule maths `push_off` separates with, so this cannot pass by measuring
# something the separation does not use -- and it is negative exactly when the
# player is inside the body.
#
# CONTROL: `--no-ragdoll-push` puts the corpse back to being a hologram and the
# clearance collapses to about -(segment radius + capsule radius).
var _c_gate := false
var _c_phase := 0
var _c_f := 0
var _c_settle := 60
var _c_wait := 0
var _c_walk := 0
var _c_who := ""
var _c_min := 1e30
var _c_min_at := 0
var _c_off := 0
var _c_from := Vector3.ZERO
var _c_path := 0.0
var _c_prev := Vector3.ZERO
var _c_seen := 0
var _c_start_clear := 0.0
## Frames in which `move_and_slide` resolved the player against a ragdoll bone.
var _c_solid := 0
## Read from `ragdoll.gd` rather than written again -- see `_spawn_player`.
const RAGDOLL_LAYER := preload("res://scripts/ragdoll.gd").RAGDOLL_LAYER


func _run_corpse_gate(args: Dictionary) -> void:
	if _player == null or _people == null:
		print("CORPSE gate=FAIL -- no player or no crowd node")
		get_tree().quit(2)
		return
	_c_gate = true
	_c_phase = 0
	_c_f = 0
	_c_settle = int(args.get("settle", "60"))
	# HOW LONG A BODY TAKES TO STOP MOVING IS MEASURED, NOT GUESSED. `ragdoll.gd`
	# prints a settle time on every drop and INV-446 records the range across the
	# fifteen species: 2.02-3.55 s. Four seconds is the top of that plus a frame
	# budget's worth of margin; the gate also prints whether SETTLED was reached.
	_c_wait = int(args.get("settle-body", str(int(4.0
		* Engine.physics_ticks_per_second))))
	# Far enough to cross the whole body and out the other side if nothing stops
	# it: the approach starts ~3 m out and a human is ~1.8 m long on the deck.
	_c_walk = int(args.get("approach", str(int(2.5
		* Engine.physics_ticks_per_second))))
	print(("CORPSE gate: settle %d frames, body settle window %d frames "
		+ "(%.1f s), approach %d frames")
		% [_c_settle, _c_wait, float(_c_wait)
		/ float(Engine.physics_ticks_per_second), _c_walk])


func _corpse_frame(delta: float) -> void:
	match _c_phase:
		0:      # -- SETTLE THE PLAYER.
			_player.step(delta, Vector2.ZERO, false, false)
			_push_off(delta)
			_c_f += 1
			if _c_f < _c_settle:
				return
			_c_phase = 1
		1:      # -- DROP SOMEBODY, out of the crowd, along the corridor.
			var d: Node = _people.ragdoll_director()
			if d == null:
				print("CORPSE gate=FAIL -- no ragdoll director in the tree. "
					+ "`main.gd::_start_ragdolls` builds it on modes station "
					+ "and arrival; this build has none.")
				get_tree().quit(2)
				return
			var p: Vector3 = _player.global_position
			var up: Vector3 = _player.body_up()
			# ALONG THE CORRIDOR, WHICH IS NOT THE AXIS. A ring corridor runs
			# round the circumference; +Z is the station's axis and is the
			# corridor's 2.6 m WIDTH. Same derivation as `main.gd::_ragdoll_gate`,
			# which learned it by dropping two bodies off the edge of the floor.
			var along: Vector3 = up.cross(Vector3(0, 0, 1)).normalized()
			_c_who = _people.promote_walker(d, {
				"cause": "INC-ACCIDENT", "dead": true,
			}, p + along * 3.0, 12.0)
			if _c_who == "":
				print("CORPSE gate=FAIL -- nobody fell: %s"
					% String(_people.get("promote_why")))
				get_tree().quit(1)
				return
			print("CORPSE gate: %s went down 3.0 m along the corridor" % _c_who)
			_c_f = 0
			_c_phase = 2
		2:      # -- LET IT SETTLE. The player stands still while it does.
			_player.step(delta, Vector2.ZERO, false, false)
			_push_off(delta)
			_c_f += 1
			if _c_f < _c_wait:
				return
			_c_seen = int(_people.get("_rag_seen"))
			_c_start_clear = _people.nearest_ragdoll_clearance()
			_c_from = _player.global_position
			_c_prev = _c_from
			_c_f = 0
			_c_phase = 3
			print(("CORPSE gate: body settled, %d segments, clearance %.3f m "
				+ "before the approach") % [_c_seen, _c_start_clear])
		3:      # -- WALK AT IT.
			var aim: Vector3 = _people.ragdoll_centre()
			if aim == Vector3.ZERO:
				print("CORPSE gate=FAIL -- the body stopped existing mid-walk")
				get_tree().quit(1)
				return
			_player.step(delta, Vector2.ZERO, false, false,
				aim - _player.global_position)
			_push_off(delta)
			# DID THE SOLVER ITSELF TOUCH A BONE? Counted rather than inferred,
			# because `--ragdoll-solid` is the control for exactly this and for
			# four sessions it could not be told from the subject: with
			# `push_off` separating them the two runs agree to four decimals on
			# every statistic this gate printed, so an inert flag and a working
			# one looked the same. This is the one number they cannot agree on.
			for i in range(_player.get_slide_collision_count()):
				var k := _player.get_slide_collision(i)
				var co := k.get_collider()
				if co is CollisionObject3D and \
						((co as CollisionObject3D).collision_layer
						& RAGDOLL_LAYER) != 0:
					_c_solid += 1
					break
			var c: float = _people.nearest_ragdoll_clearance()
			if c < _c_min:
				_c_min = c
				_c_min_at = _c_f
			if not _player.is_on_floor():
				_c_off += 1
			_c_path += _player.global_position.distance_to(_c_prev)
			_c_prev = _player.global_position
			_c_f += 1
			if _c_f < _c_walk:
				return
			_corpse_verdict()


func _corpse_verdict() -> void:
	_c_gate = false
	set_physics_process(false)
	# THE TOLERANCE IS ONE FRAME OF WALKING. `push_off` deliberately pays a deep
	# overlap off over several frames at the player's own speed rather than
	# teleporting them out of it, so a body arriving at walking pace is inside by
	# up to one frame's travel before the separation catches up. 1.5x that for the
	# diagonal case. Nothing else here is allowed a tolerance: a corpse you can
	# stand in the middle of is -(r_segment + 0.35) deep, two orders bigger.
	var step_m: float = float(_player.get("speed_m_s")) \
		/ float(Engine.physics_ticks_per_second)
	var tol: float = 1.5 * step_m
	var ok := true
	var bad: Array[String] = []
	if _c_seen <= 0:
		bad.append("no segments were ever seen")
	if _c_min < -tol:
		bad.append("the player was %.3f m INSIDE the body" % -_c_min)
	if _c_off > 0:
		bad.append("%d frames off the floor" % _c_off)
	if _c_path < 0.5:
		bad.append("the player never approached (%.2f m walked)" % _c_path)
	ok = bad.is_empty()
	print(("CORPSE gate=%s who=%s segments=%d clearance_start=%.3f m "
		+ "clearance_min=%.4f m (tol -%.4f, one frame of walking is %.4f) "
		+ "at frame %d, walked=%.2f m, offfloor=%d/%d, solidhits=%d/%d, %s%s")
		% [("PASS" if ok else "FAIL"), _c_who, _c_seen, _c_start_clear, _c_min,
		tol, step_m, _c_min_at, _c_path, _c_off, _c_walk, _c_solid, _c_walk,
		String(_people.push_report()),
		("" if ok else " -- " + "; ".join(bad))])
	get_tree().quit(0 if ok else 1)


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
