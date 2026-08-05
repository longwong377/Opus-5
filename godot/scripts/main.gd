extends Node3D
## THE ENTRY POINT. Launch this project with no arguments and you are standing
## in Babylon 5, with an interface, a clock running and the station audible.
##
## WHAT THIS EXISTS TO END, stated plainly because it is the third recurrence of
## one failure. Until session 4g `project.godot` shipped
## `run/main_scene="res://scenes/exterior.tscn"`, and the only script that scene
## references is `render_shot.gd` -- a SCREENSHOT TOOL. Launching the game
## printed `render_shot: --scene-json is required` and quit 2. **Every game
## script in the project was unreachable from the scene it shipped**: 2,630
## lines of finished, tested GDScript with zero inbound references -- the
## station clock (`life.gd`), all of layer 7's audio (`ambience.gd`), the
## flyable Starfury (`starfury.gd`) -- plus everything `walk.gd` builds, which
## only a developer typing `--glb=<path>` could reach. `station/audio.py` scored
## 100/100 and no sound had ever played.
##
## It survived because **every gate in this repository is a module self-test,
## and a module self-test passes whether or not anything calls it.**
## `station/coldstart.py` is the gate that can fail for it: G3 walks the
## reference graph from `run/main_scene` and fails on any game script it cannot
## reach, and G1 launches this scene with NO ARGUMENTS and asserts a player is
## standing on a floor with a HUD and a running clock.
##
## THIS FILE DRIVES, IT DOES NOT DUPLICATE. Loading a deck, colliding it,
## dressing it out of `scenes/interior.tscn`, wiring the doors, the crowd, the
## interactables, the dialogue and the HUD, and standing a `player.gd` body on
## the floor is all `scripts/walk.gd`'s job and none of it is repeated here --
## this node instantiates `scenes/walk.tscn` and sets its exported properties,
## exactly as a developer's command line does. The three things it adds are the
## three that had no instantiator anywhere: the clock, the crowd's response to
## it, and the sound.
##
## THE WORLD IT BOOTS INTO IS NOT WRITTEN DOWN HERE EITHER. `station/arrival.py
## --build` already writes a sidecar carrying the mesh, the collision shell, the
## interactables, the cast and a spawn point a body can stand on -- see
## `_boot_manifest`. A spawn constant in this file would be a second description
## of where the floor is, and the first run of `arrival.tscn` proves what that
## costs: it was handed `--spawn=0,0,0`, which on a ring deck at radius 211 m is
## the SPIN AXIS, and the body fell for two minutes.
##
##     godot --path godot                      # play it
##     godot --path godot -- --mode=arrival    # the player's first ten minutes
##     godot --path godot -- --mode=starfury   # fly one
##     godot --path godot --headless           # G1: check itself and quit
##
## HEADLESS MEANS NOBODY IS AT THE KEYBOARD, so this scene verifies itself and
## quits rather than sitting in a black room for ever. That is not a test mode
## bolted on: it is the only way a container with no display can answer "can
## this be started", and the answer had never been asked.

const WALK_SCENE := "res://scenes/walk.tscn"
const ARRIVAL_SCENE := "res://scenes/arrival.tscn"
const STARFURY_SCENE := "res://scenes/starfury.tscn"
const TRANSIT_SCENE := "res://scenes/transit.tscn"
const LIFE_SCRIPT := "res://scripts/life.gd"
const AMBIENCE_SCRIPT := "res://scripts/ambience.gd"
const NAVGRAPH_SCRIPT := "res://scripts/navgraph.gd"

## Station hours per real second, handed to `life.gd`'s Clock. 1/60 is a station
## minute a second: `life.gd`'s own default, and the rate at which a player
## standing in a corridor sees the crowd thin out over a few minutes rather than
## over a day. `--rate=` overrides; 1.0/3600.0 is real time.
@export var clock_rate: float = 1.0 / 60.0
## Where the day starts. Overridden by the boot manifest's own hour, which is
## when the player's transport docks -- the one hour in this project tied to the
## player rather than chosen.
@export var start_hour: float = 13.0
## How long the body is given to settle onto the floor before the cold-start
## check reads it, in physics frames. 120 is `arrival.gd::settle_frames`.
@export var settle_frames: int = 120
## Frames the clock is watched over, after settling. At 1/60 h per second and
## 60 Hz this is a station minute, which is far more than a float can hide.
@export var clock_frames: int = 60
## How long the cold start will wait for the mixer to report a level, in physics
## frames. 300 is five seconds -- twice the mixer's own 2.5 s crossfade constant,
## so it covers the old fade-in-from-silence behaviour completely even though
## `ambience.gd` no longer does that. The check is "did the station become
## audible", not "was it audible at frame 180".
const AUDIO_SETTLE_FRAMES := 300

var _world: Node3D           # the walk.tscn (or arrival.tscn) instance
var _life: Node3D            # life.gd's Director
var _clock                   # life.gd's Clock
var _audio: Node3D           # ambience.gd
var _mode := "station"
var _boot := {}
var _present_0300 := -1
var _present_1300 := -1
## `stream.gd`, when this build has one. Found by METHOD rather than by reaching
## into `walk.gd`'s private `_stream` field, for the same reason `_player()` is
## found by type: that file's internals are not this one's to depend on.
var _streamer = null
## `loads + frees` at the last time the cast was bound. A streamed build's tree
## CHANGES SHAPE as the player walks, and `life.gd`'s Director binds people by
## walking the meshes that are in the tree at the moment it is called.
var _stream_epoch := -1
## The cast list, read once. `Director.bind` is called again on every cell
## transition and re-reading a JSON file per transition would be a file read
## inside a hitch.
var _cast: Array = []
## Why there is no mixer, when there is no mixer. Carried into the verdict so a
## silent build says which silence it is.
var _audio_why := "-"


func _ready() -> void:
	var args := _args()
	_mode = String(args.get("mode", "station"))
	if args.has("hour"):
		start_hour = float(args["hour"])
	if args.has("rate"):
		clock_rate = float(args["rate"])

	_boot = _boot_manifest(args)
	if _boot.is_empty():
		push_error("main: no boot manifest -- run `python3 station/arrival.py "
			+ "--build` to write one, or pass --boot=<json>")
		get_tree().quit(2)
		return
	print("main: Babylon 5 -- mode=%s, boot from %s"
		% [_mode, String(_boot.get("_source", "?"))])

	match _mode:
		"station":
			_world = _build_station()
		"arrival":
			_world = _build_arrival()
		"starfury":
			_world = _build_starfury()
		"transit":
			_world = _build_transit()
		_:
			push_error("main: unknown --mode=%s (station, arrival, starfury, "
				% _mode + "transit)")
			get_tree().quit(2)
			return
	if _world == null:
		get_tree().quit(2)
		return

	# THE THREE THINGS THAT HAD NO INSTANTIATOR. Only on the modes that put a
	# body in the station: a Starfury cockpit is outside the pressure hull and
	# has neither a corridor crowd nor a room bed.
	#
	# `--no-clock` and `--no-sound` are the CONTROLS, and they are the reason G1
	# is a gate rather than a printout: `station/coldstart.py --controls` runs
	# this same scene with each of them (and with `walk.gd`'s own `--no-hud`) and
	# asserts the cold start FAILS on exactly the check that flag removes. A
	# check that cannot fail is this repository's most-repeated defect.
	if _mode in ["station", "arrival"]:
		if args.has("no-clock"):
			print("life: DISABLED (control) -- no clock, nobody keeps a day")
		else:
			_start_clock()
		if args.has("no-sound"):
			print("ambience: DISABLED (control) -- the station is silent")
		else:
			_start_ambience()

	# NOT `_headless()`-ONLY. `--check-shot` needs a real viewport to read a
	# frame out of, and a headless run has none -- so the gate runs in both and
	# only the capture is conditional.
	if _args().has("check-gate"):
		_check_gate()
		return

	if _headless() and not _args().has("no-coldstart"):
		_coldstart()


# ---------------------------------------------------------------------------
# The world
# ---------------------------------------------------------------------------

## Boot into the walkable station. Every property set here is one `walk.gd`
## already exports and one a developer's command line already passes; the values
## come from the manifest rather than from this file.
##
## AND IT STREAMS. Until session 4k this function set `glb_path` and nothing
## else, so `walk.gd::_ready` took its OTHER branch -- `_load_level`, one 62 MB
## `.glb` read synchronously, with nothing on the far side of it. Every part of
## the alternative already existed and was gated: `stream.gd` bakes cells and
## keeps a derived number of them resident around the body, `walk.gd` loads
## nothing else when it has a `cells_path`, `tools/bake_station.py` has cut all
## 70 decks into 955 cells, and `station/walkable.py --stream` drives a body
## across cell boundaries with working doors and people in CI. The shipped scene
## reached none of it, because this file never said where the cells were --
## `docs/MASTER-PLAN.md` P0.5 calls that "its single most load-bearing finding",
## since every player-facing system built before it is fixed is validated on a
## topology the shipped world does not have.
##
## THE PATH IS READ, NOT BUILT. `station/boot.py` finds the cell set that
## belongs to the deck it measured the spawn off -- checking the cells' own ids
## and source, because `blue_0_0_z7440_c01` starts with `blue_0_0` and a prefix
## match hands over a cluster 320 m down the axis -- and puts it in the manifest
## under `cells_path`. An empty string means there is no set on disk and the
## monolith is the honest fallback; `cells_why` says which it is and the banner
## below prints it, because the failure this ends was silent.
func _build_station() -> Node3D:
	var w := _instance(WALK_SCENE)
	if w == null:
		return null
	_configure_walk(w)
	w.set("cells_path", String(_boot.get("cells_path", "")))
	# READ BACK FROM THE PROPERTY, NOT FROM THE MANIFEST. What is reported is
	# what the world was actually given -- the same argument `_coldstart` makes
	# about the spawn one screen down, and the reason `_resident_cells` asks
	# `stream.gd` rather than counting the manifest's rows.
	var cells := String(w.get("cells_path"))
	if cells == "":
		print("main: MONOLITHIC -- %s. Run `python3 station/boot.py --bake`."
			% String(_boot.get("cells_why", "the boot manifest names no cell set")))
	else:
		print("main: STREAMED -- %d cells from %s, starting in cell %d%s"
			% [int(_boot.get("cells_count", 0)), cells,
				int(_boot.get("cells_start", -1)),
				("" if bool(_boot.get("cells_fresh", false))
					else "  -- STALE: " + String(_boot.get("cells_why", "")))])
	add_child(w)
	return w


## Boot into the player's first ten minutes. `arrival.gd` EXTENDS `walk.gd` and
## reads the same sidecar this node found, so the build a player arrives into is
## the build they then walk in -- there is no second world here.
##
## AND IT DOES NOT STREAM, deliberately, which is a statement rather than an
## omission. `arrival.gd::_adopt_build` REPLACES `glb_path`, `collision_path`
## and `spawn` with the arrival sidecar's own, and on this station that sidecar
## belongs to a different cluster from the one `boot.py` measures its spawn off
## -- `blue_0_0_z7440` against `blue_0_0`. Setting `cells_path` here would hand
## `walk.gd` one cluster's cells and the other cluster's spawn: a body streaming
## geometry 320 m from where it is standing. When the arrival sequence and the
## boot deck are the same cluster this becomes one line; until then the honest
## build is the monolith the sidecar names.
func _build_arrival() -> Node3D:
	var a := _instance(ARRIVAL_SCENE)
	if a == null:
		return null
	_configure_walk(a)
	a.set("arrival_path", String(_boot.get("_source", "")))
	add_child(a)
	return a


## The properties every walkable mode shares. `cells_path` is NOT among them and
## is set by `_build_station` alone -- see `_build_arrival` for why.
func _configure_walk(w: Node) -> void:
	w.set("glb_path", String(_boot.get("glb", "")))
	w.set("collision_path", String(_boot.get("collision", "")))
	w.set("interact_path", String(_boot.get("interact", "")))
	# THE OCCLUDER'S THIRD RUNG, and it is the line that makes the other two
	# real. `budget.occlusion_chain` reported `applied=True` the moment
	# `walk.gd` merely NAMED `occluder_path` -- a static scan finding a
	# reference, one level above whether anything ever sets it. It did not:
	# `boot.json` had no `occluder` key and this function did not pass one, so
	# the export var would have stayed "" and the occluder would never have
	# loaded. That is the same defect the chain exists to catch, hiding
	# underneath the chain.
	w.set("occluder_path", String(_boot.get("occluder", "")))
	# WHERE A CARD IS READ ON THE WAY IN -- `place -> {need, name, why}` for the
	# 98 of 129 register places that check one. `consequence.certain_check` has
	# carried the six-rung ladder since P1-G2 and had NO RUNTIME CALLER: the
	# rule that decides who may stand in C&C existed only in Python, which is
	# this project's eleventh built-but-unreachable defect and MASTER-PLAN A4b's
	# complaint one level down. `station/boot.py::_checks` bakes the RESULT, so
	# the engine never holds a copy of the rule.
	# `--no-checks` IS THE CONTROL, and it is the one that makes the other two
	# readings mean something: with the table empty the boundary must produce NO
	# reading at all. A gate that only ever sees the working case is the defect
	# this file's `--no-clock` and `--no-sound` already exist to avoid.
	if _args().has("no-checks"):
		print("checks: DISABLED (control) -- no card is read anywhere")
		w.set("checks", {})
	else:
		w.set("checks", _boot.get("checks", {}))
	w.set("actors_path", String(_boot.get("actors", "")))
	w.set("dialogue_path", String(_boot.get("dialogue", "")))
	w.set("crowd_path", String(_boot.get("crowd", "")))
	w.set("spawn", _vec3(_boot.get("spawn", [])))
	# A RING DECK IS SPUN, so "down" is away from the axis and not -Y. This is
	# the same value `station/walkable.py --deck` passes, and `player.gd`'s
	# header records what getting it wrong costs: a capsule lying sideways
	# through the floor, reporting `on_floor=true`, unable to move.
	w.set("gravity_mode", "drum")


## The flyable Starfury. Reachable from the shipped scene rather than only from
## its own, which is the whole of G3: 1,276 lines that nothing referenced.
func _build_starfury() -> Node3D:
	var f := _instance(STARFURY_SCENE)
	if f == null:
		return null
	var gen := _root().path_join("station/generated/scene")
	f.set("hull_glb", gen.path_join("exterior/hull.glb"))
	f.set("fury_glb", gen.path_join("starfury/starfury.glb"))
	f.set("launch_json", gen.path_join("starfury/launch.json"))
	f.set("vectors_json", gen.path_join("starfury/vectors.json"))
	add_child(f)
	return f


## The lift and the tram. `station/transit_runtime.py --build` writes the
## manifest; until it has, this mode reports the missing file and stops, which
## is the honest state rather than a silent empty scene.
##
## THE FILENAME HERE WAS WRONG FOR THE WHOLE OF THIS MODE'S LIFE, and it is
## worth stating rather than quietly correcting. It read
## `transit/transit_manifest.json`, a name that appeared EXACTLY ONCE in the
## repository -- on the line that read it. Nothing wrote it, nothing else
## mentioned it, and `--build` writes `transit/lift.json` (via `build_lift`)
## and `transit/tram.json`. So `--mode=transit` could never have worked, and
## its error message named a command that would not have fixed it: you would
## run `--build`, watch it succeed, and get the same error.
##
## `transit.gd` takes ONE manifest and branches on its `kind` field, so a
## combined index was never what the other end wanted either. Found by
## `tools/wiring.py --data`, which asks whether every generated path the engine
## names has a producer -- the sixth instance of built-but-unreachable in this
## project, and the first one caught by a gate instead of by a person.
const TRANSIT_MANIFEST := "station/generated/scene/transit/lift.json"


func _build_transit() -> Node3D:
	var man := _root().path_join(TRANSIT_MANIFEST)
	if not FileAccess.file_exists(man):
		push_error("main: no transit manifest at %s -- run " % man
			+ "`python3 station/transit_runtime.py --build`")
		return null
	var t := _instance(TRANSIT_SCENE)
	if t == null:
		return null
	t.set("manifest_path", man)
	add_child(t)
	return t


# ---------------------------------------------------------------------------
# The clock
# ---------------------------------------------------------------------------

## Start the station's day and hand the cast to it.
##
## `life.gd` is `extends SceneTree` -- a headless harness, launched with
## `--script`, which is why it had no importer for 917 lines. Its Director and
## its Clock are inner classes and its own header documents exactly this call
## sequence; what was missing was a node in a live build to make it. It is NOT
## recast, deliberately: `--script res://scripts/life.gd -- --life-test` is the
## purity gate (03:00 -> 08:00 -> 13:00 -> 03:00, compared transform by
## transform against an integrating control that drifts), and rewriting the file
## to be a Node would have taken that gate with it.
##
## AN INHABITANT'S STATE IS A PURE FUNCTION OF THE CLOCK -- nothing integrates,
## so 03:00 and 13:00 are two reads of the same expression rather than two
## states that have to be kept in step.
func _start_clock() -> void:
	var life := load(LIFE_SCRIPT)
	if life == null:
		push_error("main: could not load %s" % LIFE_SCRIPT)
		return
	_life = life.Director.new()
	_life.name = "Life"
	_clock = life.Clock.new(start_hour, clock_rate)
	_life.clock = _clock

	# THE STATION'S NAVIGATION GRAPH, and these four lines are the whole reason
	# it is reachable. `navgraph.gd` routes 741 of 741 walkable cluster pairs at
	# run time, node for node against `route_walk.path_between` with zero
	# disagreements -- and `Director.route_between` returns an empty array unless
	# `nav` is set, which nothing in the shipped build did. That is the SEVENTH
	# built-but-unreachable in this project, after L3's room leg, `stream.gd`,
	# the circulation graph, `dialogue.gd`, the Starfury's unbuilt data and
	# `--mode=transit`'s manifest that nothing wrote.
	#
	# It is a soft dependency on purpose: a missing or unreadable graph leaves
	# `nav` null and every caller gets an empty route, which is what every caller
	# already handled. The station still boots without it.
	var graph := _root().path_join("station/generated/navgraph.json")
	if FileAccess.file_exists(graph):
		var nav = load(NAVGRAPH_SCRIPT).new()
		if nav != null and nav.load_graph(graph):
			_life.nav = nav
			print("life: navgraph %d nodes, %d edges" % [nav.node_count(),
				nav.edge_count()])
		else:
			push_warning("main: navgraph at %s did not load" % graph)
	else:
		push_warning("main: no navgraph at %s -- run " % graph
			+ "`python3 station/navgraph_export.py --build`")

	add_child(_life)

	_cast = _read_array(String(_boot.get("actors", "")))
	_streamer = _find_where(self, "Node3D", "resident_ids")
	var actors := _cast
	var n: int = _life.bind(_world, actors)
	if _streamer != null:
		_stream_epoch = int(_streamer.loads) + int(_streamer.frees)
	print("life: clock started at %05.2f EMT, %.3f station hours per real "
		% [_clock.hour(), clock_rate] + "second; %d of %d residents bound%s"
		% [n, actors.size(),
			("" if _streamer == null else
				" (streamed: the cast in the %d resident cell(s); rebound as "
				% (_streamer.resident_ids() as Array).size()
				+ "cells arrive)")])
	if n > 0:
		# THE CLAIM, MEASURED IN THE SHIPPED BUILD RATHER THAN IN A HARNESS.
		# `docs/MASTER-PLAN.md` §0 asks that "03:00 differs visibly from 13:00";
		# this is that sentence evaluated on the cast actually standing in this
		# deck, before a viewer is attached -- `Director._may_pop` holds a
		# change back near the player's eye, which is right in front of a
		# person and wrong for a measurement.
		_life.apply(3.0)
		_present_0300 = _life.visible_count()
		_life.apply(13.0)
		_present_1300 = _life.visible_count()
		print("life: 03:00 -> %d present, 13:00 -> %d present, of %d bound "
			% [_present_0300, _present_1300, n]
			+ "(the same cast, read at two hours)")
		_life.apply(_clock.hour())
	# WHOSE EYES DECIDE WHAT MAY POP. Attached after the measurement above, and
	# never before: a body may not appear or vanish inside the player's hold
	# radius, which is what stops the crowd flickering in front of them.
	var body := _player()
	if body != null:
		_life.watch(body)


# ---------------------------------------------------------------------------
# The sound
# ---------------------------------------------------------------------------

## Make the station audible. `station/audio.py` derives seven layers per place
## per hour -- air, structure, machinery, crowd, traffic, PA, water -- each with
## a level in dBA and the reason it is that level, and writes 13 loop-exact
## WAVs. The gate reads 100/100 and **none of it had ever played**, because
## `ambience.gd` had zero inbound references.
##
## Nothing about loudness is decided here. The bank and the beds are read; the
## place the player is standing in is read off the GEOMETRY (`rooms.py` names
## room content `<place_key>__<group>`), so there is no second table of room
## bounds to drift from the meshes.
func _start_ambience() -> void:
	var dir := _root().path_join("station/generated/audio")
	var bank := dir.path_join("bank.json")
	if not FileAccess.file_exists(bank):
		_audio_why = "no bank at %s" % bank
		print("ambience: %s -- run `python3 station/audio.py --write`; the "
			% _audio_why + "station will be silent")
		return
	_audio = Node3D.new()
	_audio.name = "Ambience"
	_audio.set_script(load(AMBIENCE_SCRIPT))
	add_child(_audio)
	_audio.audio_dir = dir
	_audio.hour = start_hour
	# A HALF-BUILT MIXER MUST NOT LOOK LIKE A QUIET ONE. `load_bank` returning
	# false used to leave the node in the tree with an empty bank: `_process`
	# bailed on the first line, `_here` stayed "", and the verdict read
	# `audio_layers=0 audio_place=-` -- character for character what `--no-sound`
	# prints. Two very different failures with one signature is how a reader
	# spends an afternoon on the wrong hypothesis. It is freed, and the reason
	# is carried into the verdict.
	if not _audio.load_bank(bank, dir.path_join("beds.json")):
		_audio_why = "load_bank failed for %s" % bank
		_audio.queue_free()
		_audio = null
		return
	# The whole world node: the collision proxy carries seven groups, none of
	# them named `<place>__<group>` or matching an emitter rule, so there is
	# nothing to exclude and no dependence on `walk.gd`'s private node names.
	_audio.bind(_world, _player())


## ONE CLOCK, AND THE SOUND IS ON IT. `ambience.gd` reads its own `hour`
## property and nothing advanced it: the mixer would have held the boot hour for
## ever while the crowd around the player thinned out, so a corridor at 03:00
## sounded exactly like the same corridor at 13:00. `station/audio.py` derives
## the Zocalo swinging 62.1 -> 67.6 dBA across that span and the reactor hall
## swinging +0.05, and neither could be heard until this line existed.
##
## Pushed from here rather than given to `ambience.gd` as a clock reference,
## because that file mixes and does not choose -- the same argument its own
## header makes about levels. There is one clock in this build and this node
## owns it.
func _process(_delta: float) -> void:
	if _audio != null and _clock != null:
		_audio.hour = _clock.hour()
	_rebind_on_stream()


## THE CAST CHANGES WHEN THE GEOMETRY DOES, and until this existed it did not.
##
## `life.gd`'s Director binds a person by finding the MESHES in the tree whose
## names match their group -- so `bind` describes the tree at the instant it was
## called, and in a streamed build that instant is the load screen. Measured on
## the shipped scene the moment it started streaming: `21 of 21 residents bound`
## became `1 of 21`, and the twenty who arrive with later cells would have stood
## at their bake pose for ever while the clock ran past them. That is the same
## defect `docs/streaming-doors-4g.md` fixed for doors, people and interactables
## inside `walk.gd`, recurring one level up at the node that owns the clock --
## and it is exactly what P0.5 means by "every player-facing system built before
## this is validated on a topology the shipped world does not have".
##
## ON THE TRANSITION, NOT PER FRAME. `loads + frees` only moves when a cell
## arrives or leaves, so this is two integer reads a frame and a rebuild at a
## cell boundary -- where `stream.gd` is already doing its ~30 ms of main-thread
## instancing, collider building and material binding. `Director.bind` clears
## and rebuilds from scratch, keeps its viewer, and `_process` re-applies the
## hour on the next frame, so there is nothing to reconcile.
func _rebind_on_stream() -> void:
	if _streamer == null or _life == null:
		return
	var epoch: int = int(_streamer.loads) + int(_streamer.frees)
	if epoch == _stream_epoch:
		return
	_stream_epoch = epoch
	var n: int = _life.bind(_world, _cast)
	# The viewer survives `bind`, but it is set here anyway: a body that did not
	# exist at the first bind -- which is every launch, since the cast is bound
	# before `_player()` can be found -- would otherwise never become the eyes
	# that hold a pop back.
	var body := _player()
	if body != null:
		_life.watch(body)
	print("life: %d cells resident -- %d of %d residents bound"
		% [(_streamer.resident_ids() as Array).size(), n, _cast.size()])


# ---------------------------------------------------------------------------
# Cold start -- G1
# ---------------------------------------------------------------------------

## Verify the shipped build and print one line `station/coldstart.py` parses.
##
## IT ASSERTS WHAT A PLAYER WOULD NOTICE, not what is easy to measure: a body
## exists, it is standing on something, there is an interface, and the day is
## moving. Every one of those was false in the shipped scene the day this was
## written, and no gate in this repository could say so.
func _coldstart() -> void:
	# A COCKPIT HAS NO FLOOR AND NO ROOM BED, so the station's checks do not
	# apply to it and are not printed as if they did. An earlier version ran the
	# whole check on every mode and reported the Starfury as having fallen
	# 211.478 m -- which is the deck spawn's radius measured against a fighter
	# parked somewhere else entirely. A number that means nothing is worse than
	# no number: it reads as a measurement.
	if not (_mode in ["station", "arrival"]):
		for _i in 30:
			await get_tree().physics_frame
		print("COLDSTART scene=%s mode=%s booted=1 boot_s=%.1f" % [
			String(get_tree().current_scene.scene_file_path), _mode,
			float(Time.get_ticks_msec()) / 1000.0])
		get_tree().quit(0)
		return
	# WHERE THE BODY WAS ACTUALLY PUT, not where the manifest asked for it.
	#
	# The two are the same in a monolithic build and can differ in a streamed
	# one: `walk.gd::_load_streamed` falls back to the start cell's own measured
	# floor point when the manifest's spawn is not inside the cell it primed.
	# That fallback is correct -- a body spawned into a cell that has not arrived
	# falls -- but measuring `drop_m` against the number that was NOT used turns
	# a working build into a verdict claiming it fell, which is the same class of
	# mistake as scoring a frame the renderer never produced. `boot.py --gate`
	# reports the disagreement itself; this line just measures the right thing.
	var spawn: Vector3 = _vec3(_boot.get("spawn", []))
	if _world != null and _world.get("spawn") != null:
		spawn = _world.get("spawn")
	for _i in settle_frames:
		await get_tree().physics_frame
	var body := _player()
	var pos: Vector3 = body.global_position if body != null else Vector3.ZERO
	var on_floor := body != null and body.is_on_floor()
	# Radially, because on a spun deck "down" is outward: a body that fell
	# through the shell has a LARGER radius, and its z and angle barely move.
	var drop := absf(Vector2(spawn.x, spawn.y).length()
		- Vector2(pos.x, pos.y).length())

	var h0 := float(_clock.hour()) if _clock != null else -1.0
	for _i in clock_frames:
		await get_tree().physics_frame
	var h1 := float(_clock.hour()) if _clock != null else -1.0

	var hud = _hud()
	var hud_place := ""
	if hud != null:
		print("hud: %s" % hud.report())
		hud_place = String(hud.place_name).to_lower().replace(" ", "_")
		hud_place = hud_place.replace(",", "")
	# THE MIXER IS POLLED UNTIL IT SETTLES, NOT SAMPLED ONCE.
	#
	# This used to read `describe()` at exactly `settle_frames + clock_frames`
	# and believe whatever it said. That makes the verdict a race: a fader on a
	# 2.5 s time constant is below `silence_db` for the first two seconds of a
	# build, so "the station is audible" answered a question about WHEN it was
	# asked. `ambience.gd` no longer fades in from silence at boot, which is the
	# real cure -- but a gate that is correct only because of a property of the
	# thing it is gating is one refactor from lying again, so it also waits for
	# a settled answer here and REPORTS HOW LONG IT WAITED. `audio_ready_s` is
	# the number that would have caught this on the day it was written.
	var layers := 0
	var ready_s := -1.0
	if _audio != null:
		var t0 := Time.get_ticks_msec()
		for _i in AUDIO_SETTLE_FRAMES:
			if _clock != null:
				_audio.hour = _clock.hour()
			layers = _layers(_audio.describe())
			if layers > 0:
				ready_s = float(Time.get_ticks_msec() - t0) / 1000.0
				break
			await get_tree().physics_frame
		var said: String = _audio.describe()
		print(said)
		layers = _layers(said)

	# `cells=` IS IN THE VERDICT because the topology a player-facing system was
	# validated on is a property of the run, not of the repository. `cells=0`
	# says this build loaded one deck whole; `station/coldstart.py::parse_verdict`
	# reads `k=v` tokens and ignores the ones it has no check for, so this is
	# additive.
	print(("COLDSTART scene=%s mode=%s player=%d on_floor=%s drop_m=%.3f "
		+ "hud=%d hud_place=%s h0=%05.2f h1=%05.2f clock_advanced=%s "
		+ "day=%d "
		+ "bodies=%d present_0300=%d present_1300=%d audio_layers=%d "
		+ "audio_place=%s audio_ready_s=%.2f audio_why=%s cells=%d "
		+ "cell_resident=%d boot_s=%.1f") % [
		String(get_tree().current_scene.scene_file_path), _mode,
		1 if body != null else 0, str(on_floor).to_lower(), drop,
		1 if hud != null else 0, (hud_place if hud_place != "" else "-"),
		h0, h1, str(h1 > h0).to_lower(),
		(_clock.day() if _clock != null else -1),
		_life.count() if _life != null else 0,
		_present_0300, _present_1300, layers,
		(_audio._here if _audio != null and _audio._here != "" else "-"),
		ready_s, _audio_why.replace(" ", "_"),
		int(_boot.get("cells_count", 0)), _resident_cells(),
		float(Time.get_ticks_msec()) / 1000.0])
	get_tree().quit(0)


## How many streamed cells are actually in the tree, asked of `stream.gd` rather
## than of the manifest. THE TWO ANSWER DIFFERENT QUESTIONS and only this one is
## about the run: a manifest naming 18 cells with none resident is a build that
## configured streaming and never loaded anything, which is a shape this
## repository has shipped before under the name "the gate was green".
## Untyped for the reason `_hud()` is: a value typed `Node3D` resolves its calls
## against that class at compile time, and `resident_ids` is on the script.
func _resident_cells() -> int:
	var s = _find_where(self, "Node3D", "resident_ids")
	if s == null:
		return 0
	return (s.resident_ids() as Array).size()


## The layer count out of an `AMBIENCE ...` line, or 0.
func _layers(said: String) -> int:
	var cut := said.split("layers=")
	return cut[1].split(" ")[0].to_int() if cut.size() > 1 else 0


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------

## The deck this build boots into, and everything that stands on it.
##
## READ FROM A GENERATED MANIFEST, NEVER WRITTEN HERE. A spawn constant in this
## file could only ever be a copy that goes stale against regenerated geometry,
## and `arrival.tscn`'s header records what that costs: its first run was handed
## `--spawn=0,0,0`, which on a ring deck at radius 211 m is the SPIN AXIS, and
## the body fell for two minutes.
##
## Three places are tried, in this order:
##
##   --boot=<json>   whatever you say
##   boot.json       `station/boot.py`'s output. THE RIGHT SOURCE: it derives
##                   the spawn from the collision shell's own floor rather than
##                   copying it, so it cannot disagree with the surface the body
##                   stands on
##   *_arrival.json  the fallback, and it is a BORROWED manifest. It is the
##                   sidecar `arrival.py --build` writes for the player's first
##                   ten minutes; booting the other three modes out of it made
##                   the game's entry point a property of a narrative artefact,
##                   and deleting an arrival sequence stopped the game starting
##
## The two shapes differ only in nesting -- `arrival.json` keeps its build block
## under `build` -- so both are read here rather than one being converted.
func _boot_manifest(args: Dictionary) -> Dictionary:
	var path := String(args.get("boot", ""))
	if path == "":
		var derived := _root().path_join("station/generated/scene/boot.json")
		if FileAccess.file_exists(derived):
			path = derived
	if path == "":
		var deck := _root().path_join("station/generated/scene/deck")
		var d := DirAccess.open(deck)
		if d == null:
			return {}
		var found: Array = []
		for f in d.get_files():
			if f.ends_with("_arrival.json"):
				found.append(deck.path_join(f))
		if found.is_empty():
			return {}
		found.sort()
		path = found[0]
		print("main: no boot.json -- falling back to the arrival sidecar; "
			+ "run `python3 station/boot.py` to write one")
	if not FileAccess.file_exists(path):
		return {}
	var f2 := FileAccess.open(path, FileAccess.READ)
	var doc = JSON.parse_string(f2.get_as_text())
	if typeof(doc) != TYPE_DICTIONARY:
		return {}
	var b: Dictionary = doc.get("build", doc)
	if b.is_empty() or not b.has("glb"):
		return {}
	var out := b.duplicate()
	out["_source"] = path
	# The sidecars the build block does not name are named by the mesh, which is
	# how `station/walkable.py` and `arrival.gd` both find them.
	var stem := String(out["glb"]).get_basename()
	for k in [["dialogue", "_dialogue.json"], ["crowd", "_crowd.json"]]:
		if not out.has(k[0]):
			var p: String = stem + k[1]
			out[k[0]] = p if FileAccess.file_exists(p) else ""
	# The hour the player's transport docks -- the one hour in this project tied
	# to the player rather than chosen. `--hour=` wins over it, and checking that
	# here rather than at the assignment above is the whole of the fix: written
	# the other way round the manifest silently overrode the flag, so `--hour=3`
	# and `--hour=13` produced identical runs and the clock looked inert.
	if doc.has("hour") and not args.has("hour"):
		start_hour = float(doc["hour"])
	print("main: deck %s, spawn %.2f,%.2f,%.2f in %s, %d rooms" % [
		stem.get_file(), _vec3(out.get("spawn", [])).x,
		_vec3(out.get("spawn", [])).y, _vec3(out.get("spawn", [])).z,
		String(out.get("spawn_at", "?")), (out.get("rooms", []) as Array).size()])
	return out


func _instance(scene: String) -> Node3D:
	var ps = load(scene)
	if ps == null:
		push_error("main: could not load %s" % scene)
		return null
	return ps.instantiate()


## The body, found by TYPE rather than by reaching into `walk.gd`'s private
## fields -- that file is not this one's to depend on the internals of.
func _player() -> CharacterBody3D:
	return _find(self, "CharacterBody3D") as CharacterBody3D


## The interface: a CanvasLayer that can report what is on it. BOTH halves are
## load-bearing and neither alone is enough. `interact.gd` carries a second
## CanvasLayer -- the bare debug label from the session that introduced the verb
## table, which `hud.gd::bind` hides rather than deletes because `walk.gd` still
## reads its text back for the WALKTEST verdict -- and it is in the tree before
## the HUD is, so a search by class finds the wrong one. `dialogue.gd` and
## `stream.gd` both define `report()`, so a search by method finds those.
##
## Returned UNTYPED on purpose: a value typed `CanvasLayer` resolves its calls
## against that class at compile time, and `report()` is on the script rather
## than on the class -- which fails with "Nonexistent function 'report' in base
## 'CanvasLayer'" at the one moment the gate is trying to read the HUD.
func _hud():
	return _find_where(self, "CanvasLayer", "report")


func _find_where(n: Node, cls: String, method: String):
	for c in n.get_children():
		if c.is_class(cls) and c.has_method(method):
			return c
		var got = _find_where(c, cls, method)
		if got != null:
			return got
	return null


func _find(n: Node, cls: String) -> Node:
	for c in n.get_children():
		if c.is_class(cls):
			return c
		var got := _find(c, cls)
		if got != null:
			return got
	return null


func _root() -> String:
	return ProjectSettings.globalize_path("res://").path_join("..").simplify_path()


func _headless() -> bool:
	return DisplayServer.get_name() == "headless"


## HOW MANY STEPS A CROSSING IS BROKEN INTO. Twelve, so the body is genuinely
## outside the box on step 0 and genuinely inside by the last one -- a single
## teleport onto the centre would prove the HUD can look a place up and would
## say nothing about a TRANSITION, which is the thing being gated.
const CHECK_GATE_STEPS := 12
## How far outside a place's own box the approach starts.
const CHECK_GATE_STANDOFF_M := 4.0
## One frame per run, taken at the first refusal -- a refusal is the interesting
## picture and taking one per boundary would be six copies of the same argument.
var _check_shot_done := false


## THE CARD IS READ ON THE WAY IN -- the gate, in the shipped scene.
##
## `consequence.certain_check` decides who may stand in C&C and had NO RUNTIME
## CALLER: the whole six-rung ladder lived in Python and a player could walk
## into the command deck of a military station unchallenged. That is this
## project's eleventh built-but-unreachable defect, and the pattern every one of
## them shares is that a static scan finds the reference. So this does not scan.
## It walks a body across a real boundary in the streamed build and asserts a
## reading came out, with three controls that must change the answer:
##
##   `--no-checks`   the table is empty      -> readings must be 0
##   `--tier=N`      the player's own rung   -> admits must become refusals
##   (and `--no-hud`, which `walk.gd` already owns, removes the reader entirely)
##
## What it does NOT claim: the arrest chain behind a refusal (`consequence.arrest`
## -> brig -> fine -> release) is still Python. A refused player is TOLD they are
## refused and is not yet detained. P2 owns closing that; reporting the reading is
## still the difference between a rule that exists and a rule a player meets.
func _check_gate() -> void:
	for _i in settle_frames:
		await get_tree().physics_frame
	var body := _player()
	var hud = _hud()
	if body == null or hud == null:
		print("CHECK gate=FAIL -- no %s in the shipped scene"
			% ("body" if body == null else "hud"))
		get_tree().quit(1)
		return

	# FORCE THE CARD, NOT THE HUD. `hud.gd::_purse` re-reads the rung from the
	# player every frame, so a tier written onto the HUD would be overwritten
	# before the first boundary. Writing it onto `player.gd` is also the more
	# honest control: it is the identicard that changed, not the reader.
	var args := _args()
	if args.has("tier"):
		var forced := int(args["tier"])
		body.set("tier", forced)
		body.set("tier_name", "forced_%d" % forced)
		print("CHECK control: the card now reads tier %d" % forced)

	# WHICHEVER SOURCE THIS BUILD ACTUALLY HAS. `hud.gd` resolves a place from
	# the level's own mesh names when the deck is loaded whole and from the
	# interact sidecar's boxes when it is STREAMED -- and the shipped build
	# streams, so reading `_place_boxes` alone made this gate report FAIL on a
	# working build for the wrong reason. A gate that only understands one of
	# the two paths is the same defect as a fix that only patches one of them.
	var boxes: Dictionary = _check_boxes(hud)
	var tbl: Dictionary = hud.get("checks")
	if boxes.is_empty():
		print("CHECK gate=FAIL -- this build named no place boxes, so there is "
			+ "no boundary to cross")
		get_tree().quit(1)
		return

	# ONLY THE PLACES THIS DECK ACTUALLY HAS. The table covers 98 of the 129
	# register places and one deck holds a handful of them; crossing into a room
	# that is not in this build would be crossing into nothing.
	var here: Array = []
	for k in boxes:
		here.append(String(k))
	here.sort()

	var admits := 0
	var refusals := 0
	var silent := 0
	var wrong := 0
	var crossed := 0
	for k in here:
		var aabb: AABB = boxes[k]
		var c: Vector3 = aabb.get_center()
		# Approach along the box's OWN shortest axis, because that is the wall a
		# body meets soonest and the standoff is most likely to clear it.
		var ax := 0
		if aabb.size.y < aabb.size[ax]:
			ax = 1
		if aabb.size.z < aabb.size[ax]:
			ax = 2
		var dir := Vector3.ZERO
		dir[ax] = 1.0
		var out: Vector3 = c + dir * (aabb.size[ax] * 0.5 + CHECK_GATE_STANDOFF_M)

		# DISARM FIRST. The reading fires on a CHANGE of place, so the body has
		# to be demonstrably outside before the approach means anything.
		body.global_position = out
		body.velocity = Vector3.ZERO
		await get_tree().physics_frame
		await get_tree().process_frame
		if String(hud.get("place_name")) != "CORRIDOR":
			continue

		hud.set("check_text", "")
		var read := ""
		for i in range(1, CHECK_GATE_STEPS + 1):
			var t := float(i) / float(CHECK_GATE_STEPS)
			body.global_position = out.lerp(c, t)
			body.velocity = Vector3.ZERO
			await get_tree().physics_frame
			await get_tree().process_frame
			var got := String(hud.get("check_text"))
			if got != "":
				read = got
				break
		crossed += 1

		if not tbl.has(k):
			if read != "":
				print("CHECK WRONG %s -- no row in the table and it read anyway"
					% k)
				wrong += 1
			continue
		var need := int((tbl[k] as Dictionary).get("need", 0))
		var tier := int(hud.get("tier"))
		if read == "":
			silent += 1
			continue
		var refused := read.begins_with("IDENTICARD REFUSED")
		if refused == (tier >= need):
			print("CHECK WRONG %s -- need %d, holding %d, and it said %s"
				% [k, need, tier, ("refuse" if refused else "admit")])
			wrong += 1
		elif refused:
			refusals += 1
			# A FRAME WITH THE WORDS ON IT. `_check` draws into the HUD's
			# `Face`, and a grep finding the call in `_draw` is exactly the
			# evidence that failed this project ten times over -- the read panel
			# shipped with its call site in place and drew nothing, because the
			# sidecars it read from had no `text` field. `get_root()` is used
			# rather than `get_viewport()` because a CanvasLayer is not in the
			# 3D viewport's texture, and a shot that missed the interface would
			# be a picture proving the opposite of what it was taken for.
			if args.has("check-shot") and not _check_shot_done:
				_check_shot_done = true
				await RenderingServer.frame_post_draw
				var img := get_tree().get_root().get_texture().get_image()
				var png := String(args["check-shot"])
				if img.save_png(png) == OK:
					print("CHECK shot=%s %dx%d -- %s"
						% [png, img.get_width(), img.get_height(),
							read.replace("\n", " / ")])
				else:
					print("CHECK shot=FAILED to write %s" % png)
		else:
			admits += 1

	# THE VERDICT, AND IT FAILS ON EVERY WAY THIS CAN GO WRONG: a boundary that
	# read nothing, a reading that disagreed with the arithmetic, or -- the case
	# `--no-checks` produces on purpose -- no reading anywhere.
	var ok := (wrong == 0 and silent == 0 and (admits + refusals) > 0)
	print(("CHECK gate=%s crossed=%d checked=%d readings=%d admit=%d refuse=%d "
		+ "silent=%d wrong=%d tier=%d(%s) table=%d") % [
		("PASS" if ok else "FAIL"), crossed,
		_check_rows(here, tbl), admits + refusals, admits, refusals,
		silent, wrong, int(hud.get("tier")), String(hud.get("tier_name")),
		tbl.size()])
	get_tree().quit(0 if ok else 1)


## `place -> AABB` for whichever of the HUD's two box sources this build filled.
## The sidecar's are stored as `[lo, hi]` and grown by the same 1.5 m of slack
## `hud.gd::_resolve` uses, so an approach that starts outside the box this
## returns starts outside the box the HUD will test against.
func _check_boxes(hud) -> Dictionary:
	var pb: Dictionary = hud.get("_place_boxes")
	if not pb.is_empty():
		return pb
	var out := {}
	var raw: Dictionary = hud.get("_boxes")
	for k in raw:
		var b: Array = raw[k]
		var lo: Vector3 = (b[0] as Vector3) - Vector3.ONE * 1.5
		var hi: Vector3 = (b[1] as Vector3) + Vector3.ONE * 1.5
		out[String(k)] = AABB(lo, hi - lo)
	return out


## How many of the places on THIS deck have a row in the table -- the denominator
## the verdict is read against, so `readings=` can be compared to something.
func _check_rows(here: Array, tbl: Dictionary) -> int:
	var n := 0
	for k in here:
		if tbl.has(k):
			n += 1
	return n


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


func _vec3(a) -> Vector3:
	if typeof(a) == TYPE_ARRAY and (a as Array).size() == 3:
		return Vector3(float(a[0]), float(a[1]), float(a[2]))
	return Vector3.ZERO


func _read_array(path: String) -> Array:
	if path == "" or not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	return d if typeof(d) == TYPE_ARRAY else []
