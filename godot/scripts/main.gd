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
const RAGDOLL_SCRIPT := "res://scripts/ragdoll.gd"
const JOURNAL_SCRIPT := "res://scripts/journal.gd"

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
var _ragdoll: Node3D         # ragdoll.gd -- the bodies that stop standing up
var _journal: Node3D         # journal.gd -- SYS-16 knowledge items, CAST-05
var _mode := "station"
var _boot := {}
var _present_0300 := -1
var _present_1300 := -1
## `stream.gd`, when this build has one. Found by METHOD rather than by reaching
## into `walk.gd`'s private `_stream` field, for the same reason `_player()` is
## found by type: that file's internals are not this one's to depend on.
var _streamer = null
## What is outside a window, in the build a player actually launches.
##
## INSTANCE TEN, AND IT IS CLOSED HERE. `godot/scripts/vista.gd` is complete,
## tested and mounted by `render_shot.gd` -- which is the RENDER path. The
## shipped build is `main.gd` -> `walk.gd` -> `stream.gd`, and it mounted
## nothing, so a player walking to C&C's window saw the background colour while
## a render of the same room showed the station. `vista.gd`'s own header says
## so in as many words, and names this file as the fix. Ten is the count of
## times this project has shipped finished machinery with no caller.
var _vista: Node = null
## The HUD, found once. See `_vista_update` for why this is not a call.
var _hud_cache = null
## Which place `_vista` is currently built for, "" for none.
var _vista_place := ""
## LAZY, AND THE TRIANGLE BUDGET IS WHY -- this is not the one-liner the
## session report predicted. `cnc`'s vista is 96,498 triangles; the streamed
## build already runs 154,454 against `budget.CELLS["resident_tris"]` of
## 180,000, so mounting it unconditionally is 139% of budget before the player
## has looked at anything. Three places on the station have a window, so the
## cost is paid only while standing in one of them and released on the way out.
const VISTA_DIR := "res://../station/generated/scene/vista"
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

	# THE MANIFEST IS READ BEFORE THE DECISION, NOT AFTER IT. The front door has
	# to be able to say "there is no world on disk, here is the command", and it
	# cannot say that unless it has already looked. `_boot_manifest` prints and
	# returns {} on a miss; nothing here quits on it any more -- see `_start`.
	_boot = _boot_manifest(args)

	# THE FRONT DOOR. When it takes the launch it puts a title screen up and
	# returns, and `_on_menu_chosen` calls `_start` when the player presses
	# something. Every other launch -- every gate, every developer command line,
	# every headless CI step -- goes straight through, unchanged.
	if _front_door(args):
		return
	_start(args)


## Everything that used to be the body of `_ready`. Split out so that the menu
## can call it LATER, on the frame the player chooses a mode, rather than the
## frame the process starts.
func _start(args: Dictionary) -> void:
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
		# THE FOURTH THING WITH NO INSTANTIATOR. `station/incident.py` has been
		# producing 380 collapses a day, a dock fatality every ~500 accidents
		# and an arrest chain, all in text. `scripts/ragdoll.gd` is what makes
		# one of them visible, and like the three above it is created here
		# because nothing else in the tree owns the whole world plus the body.
		#
		# NO `--no-ragdoll` GUARD HERE, deliberately, and the first draft had
		# one. `ragdoll.gd::apply_controls` owns that flag and answers it by
		# REFUSING to promote -- so the incident still fires, three bodies are
		# still asked for, and the report reads `refused=3 (disabled)`. Skipping
		# the director instead would have produced "no director" and quit 2:
		# the control would have failed on its own absence rather than on the
		# thing it removes, which is a control that proves nothing.
		_start_ragdolls()
		# THE FIFTH THING WITH NO INSTANTIATOR, and it is the one that makes
		# passing time cost something. `station/journal.py` owns what a SYS-16
		# knowledge item is; `scripts/journal.gd` is where a conversation, a PA
		# call and a collapse become things the player HAS. It is created here
		# for the reason the four above are: this node owns the whole world and
		# the clock, and the journal needs both. `--no-journal` is the control
		# and `journal.gd` answers it by REFUSING to mint, so the flag removes
		# the learning rather than the node -- the distinction `_start_ragdolls`
		# already had to make.
		_start_journal()

	# NOT `_headless()`-ONLY. `--check-shot` needs a real viewport to read a
	# frame out of, and a headless run has none -- so the gate runs in both and
	# only the capture is conditional.
	if _args().has("check-gate"):
		_check_gate()
		return

	if _args().has("vista-gate"):
		_vista_gate()
		return

	if _headless() and _args().has("journal-gate"):
		if _journal == null:
			print("JOURNAL gate=FAIL no journal in this build")
			get_tree().quit(2)
			return
		_journal.run_gate(self)
	elif _headless() and _args().has("save-gate"):
		_save_gate()
	elif _headless() and _args().has("ragdoll-gate"):
		_ragdoll_gate()
	elif _headless() and _args().has("collapse-gate"):
		_collapse_gate()
	elif _headless() and not _args().has("no-coldstart") and not _in_menu_gate:
		_coldstart()


# ---------------------------------------------------------------------------
# The front door
# ---------------------------------------------------------------------------
## THE TITLE SCREEN, AND WHY IT IS HERE RATHER THAN IN A SCENE FILE.
##
## Measured at the start of session 4t: `godot/export_presets.cfg` did not
## exist, `tools/` had no packaging path, and the strings "menu", "title" and
## "new game" appeared nowhere in 25,000 lines of GDScript. `MASTER-PLAN` A2's
## definition of done opens *"a stranger downloads ONE FILE, runs it at 60 fps,
## arrives at Babylon 5 as a person with papers"* -- and there was no way for a
## person to start this at all. A stranger who launched the shipped build with
## no world on disk got `push_error` on a console they cannot see and exit 2.
##
## WHO GETS THE MENU, AND THE RULE IS DELIBERATELY NARROW. Only a launch with a
## DISPLAY and NO USER ARGUMENTS AT ALL -- which is what double-clicking the
## exported binary is, and nothing else in this repository. Every gate, every
## `tools/render_godot.sh` shot, every `--mode=` developer command line and
## every headless CI step is untouched, and `station/coldstart.py --g1` still
## launches this scene with no arguments headlessly and gets a body on a floor.
## Widening this predicate is how the front door would start eating the gates.
##
## `--menu-gate` forces it on headlessly so CI can drive it; `--no-menu` forces
## it off. Both exist because a menu only a human can operate is a menu no step
## can fail on, which is this project's signature defect in a new costume.
const MENU_SCRIPT := "res://scripts/main_menu.gd"
## The one slot the front door offers. `save.gd` supports any name; CONTINUE is
## a single button and a single button needs a single slot.
const MENU_SLOT := "auto"

var _menu = null
## True only for the duration of a `--menu-gate` run. Suppresses the cold start
## so the gate's own verdict is the one that decides the exit code -- two gates
## racing to `quit()` in one process is a result nobody can read.
var _in_menu_gate := false


func _front_door(args: Dictionary) -> bool:
	if args.has("no-menu"):
		return false
	var forced := args.has("menu-gate") or args.has("menu-shot")
	if not forced:
		if _headless():
			return false
		# ANY user argument at all means a developer or a tool is driving, and
		# a title screen would be in the way of every one of them.
		if not args.is_empty():
			return false
	_in_menu_gate = forced
	var m = load(MENU_SCRIPT)
	if m == null:
		push_error("main: no %s -- launching straight into the station" % MENU_SCRIPT)
		return false
	_menu = m.new()
	_menu.name = "MainMenu"
	# `--no-world` is the gate's negative control: it withholds the world the
	# same way an empty `station/generated/` would, so NEW GAME must refuse.
	_menu.world_ok = (not _boot.is_empty()) and not args.has("no-world")
	_menu.world_why = ("withheld by --no-world (control)" if args.has("no-world")
		else "%s. Build one: `python3 station/arrival.py --build` then "
			% (_boot_why if _boot_why != "" else "no boot manifest")
			+ "`python3 station/boot.py`")
	var snap: Dictionary = _save_lib().read(MENU_SLOT)
	_menu.save_ok = not snap.is_empty()
	_menu.save_why = (_save_lib().describe(snap) if _menu.save_ok
		else "No saved station.")
	_menu.chosen.connect(_on_menu_chosen)
	add_child(_menu)
	if args.has("menu-gate"):
		# Deferred so the menu's own `_ready` has run and its rows exist. A gate
		# that drove a half-constructed menu would be measuring nothing.
		call_deferred("_menu_gate")
	elif args.has("menu-shot"):
		call_deferred("_menu_shot")
	return true


func _on_menu_chosen(id: String) -> void:
	var mode := String(_menu.mode_of(id))
	var restoring := (mode == "continue")
	_mode = ("station" if restoring else mode)
	_menu.queue_free()
	_menu = null
	print("main: front door -> %s (mode=%s)" % [id, _mode])
	_start(_args())
	if restoring and _world != null:
		load_from(MENU_SLOT)


## CI: drive the title screen with no keyboard and assert what it reached.
##
## IT PRESSES THE BUTTON RATHER THAN CALLING THE FUNCTION BEHIND IT. `select()`
## and `activate()` are the same two calls `_unhandled_input` makes, so what is
## gated is the path a player's ENTER key takes. Asserting `_build_station()`
## works would prove the world builds and say nothing about whether anything
## reaches it -- the exact shape of the nine no-caller defects CLAUDE.md counts.
## A PICTURE OF THE FRONT DOOR, because `--menu-gate` proves the button works
## and says nothing about whether anybody would want to press it.
## `docs/AAA-STANDARD.md` scores craft off a frame; this is how the title screen
## gets one. Needs a real viewport, so it runs under `xvfb-run` with lavapipe --
## and, per CLAUDE.md's render-fallback rule, the line it prints names the
## rendering driver it actually got, so a frame taken through OpenGL 3
## Compatibility cannot be mistaken for a Forward+ one.
func _menu_shot() -> void:
	var path := String(_args().get("menu-shot", ""))
	for _i in 4:
		await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var err := img.save_png(path)
	print("MENUSHOT %s %dx%d driver=%s adapter=%s err=%d"
		% [path, img.get_width(), img.get_height(),
			RenderingServer.get_video_adapter_api_version(),
			RenderingServer.get_video_adapter_name(), err])
	get_tree().quit(0 if err == OK else 2)


func _menu_gate() -> void:
	var rows: Array = _menu.items()
	var listed := []
	for r in rows:
		listed.append("%s=%s" % [r["id"], ("ready" if r["enabled"] else "no")])
	var want := String(_args().get("menu-gate", "1"))
	if want == "1":
		want = "new_game"
	# TYPED EXPLICITLY. `_menu` is a Variant -- it is `load()`ed rather than
	# preloaded, so the parser cannot infer what `select()` returns and `:=`
	# fails to compile.
	var moved: bool = _menu.select(want)
	var fired: String = (String(_menu.activate()) if moved else "")
	# `_on_menu_chosen` has already run by here -- `chosen` is emitted
	# synchronously inside `activate()` -- so the world, if there is one, is up.
	var body := _player()
	# THE CARD BY NAME, not "is there a CanvasLayer". `interact.gd` carries a
	# second CanvasLayer and `hud.gd` a third, so a search by class finds one of
	# those and reports a card the player has not been given -- the same trap
	# `_hud()` documents one screen down.
	var card := (_world != null
		and _world.find_child("ArrivalCard", true, false) != null)
	var fields := 0
	var who := "-"
	if _world != null and _world.has_method("card_lines"):
		var seq_d: Dictionary = _world.get("seq")
		fields = (seq_d.get("identicard", []) as Array).size()
		who = String(seq_d.get("name", "-")).replace(" ", "_")
	var ok: bool = (moved and fired == want and _world != null and body != null
		and ((fields > 0 and card) if want == "new_game" else true))
	print("MENUGATE want=%s entries=[%s] selected=%s fired=%s world=%s "
		% [want, ", ".join(PackedStringArray(listed)), str(moved).to_lower(),
			(fired if fired != "" else "-"),
			("-" if _world == null else _world.name)]
		+ "player=%s card=%s who=%s identicard_fields=%d verdict=%s"
		% [str(body != null).to_lower(), str(card).to_lower(), who, fields,
			("PASS" if ok else "FAIL")])
	get_tree().quit(0 if ok else 2)


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
## AND THE SIDECAR IS NAMED BY THE DECK, NOT BY WHERE THE MANIFEST CAME FROM.
## This line used to read `a.set("arrival_path", _boot["_source"])`, and it was
## correct exactly until `station/boot.py` existed: before that, `_source` WAS
## `<deck>_arrival.json`, because the boot manifest was the arrival sidecar.
## `boot.py`'s own header says so -- *"that was a borrowed manifest and it
## should not have been"* -- and it stopped being true the day it was written.
## Nothing failed, because nothing on this box had a `boot.json` to fall over;
## the moment one existed, `--mode=arrival` handed `arrival.gd` the boot
## manifest as a sequence and the run died on `arrival: no sequence at
## .../boot.json`. **A fix applied to one caller and not to the assumption it
## shared is a fix that will be needed again**, and this is the second half of
## that one.
##
## So the path is passed ONLY when the manifest really is a sidecar. Otherwise
## it is left empty and `arrival.gd::_load_sequence` derives it from the deck it
## was given -- `<glb basename>_arrival.json` -- which is the one description of
## where a sidecar lives, in the file that reads it.
func _build_arrival() -> Node3D:
	var a := _instance(ARRIVAL_SCENE)
	if a == null:
		return null
	_configure_walk(a)
	var src := String(_boot.get("_source", ""))
	var sidecar := (src if src.ends_with("_arrival.json")
		else String(_boot.get("glb", "")).get_basename() + "_arrival.json")
	a.set("arrival_path", _rebased_sidecar(sidecar))
	add_child(a)
	return a


## The arrival sidecar, with its paths moved onto THIS install.
##
## WHY THIS IS NOT JUST `_rebase` ON THE MANIFEST. `arrival.gd::_adopt_build`
## deliberately REPLACES `glb_path`, `collision_path`, `interact_path` and
## `actors_path` with the sidecar's own -- and it is right to, because the
## sequence and the build it was measured against must be the same deck. But
## those are absolute paths written by `station/arrival.py` on the machine that
## generated the world, so on a stranger's box they are four files that do not
## exist. Measured: an untarred build with the generator's tree hidden came up,
## drew the card and read all nine identicard fields, and had **no player body
## at all** -- `MENUGATE ... player=false ... verdict=FAIL`. The sequence loaded
## (its own path is derived from the rebased glb) and the deck under it did not.
##
## SO THE REBASE IS DONE ON A COPY, IN `user://`, AND ONLY WHEN IT CHANGES
## SOMETHING. A run from the source tree rebases nothing, writes nothing and
## hands `arrival.gd` the original file -- so this function is inert on every
## path that worked before it existed, which is its own negative control. The
## alternative was rewriting the paths at package time, and that cannot work:
## the install directory is not known when the tarball is made.
func _rebased_sidecar(path: String) -> String:
	if path == "" or not FileAccess.file_exists(path):
		return ""
	var f := FileAccess.open(path, FileAccess.READ)
	var doc = JSON.parse_string(f.get_as_text())
	if typeof(doc) != TYPE_DICTIONARY:
		return ""
	var b = doc.get("build", {})
	if typeof(b) != TYPE_DICTIONARY:
		return path
	var moved := 0
	for k in ["glb", "collision", "interact", "actors"]:
		if b.has(k):
			var was := String(b[k])
			var now := _rebase(was)
			if now != was:
				b[k] = now
				moved += 1
	if moved == 0:
		return path
	doc["build"] = b
	var out := "user://arrival_rebased.json"
	var g := FileAccess.open(out, FileAccess.WRITE)
	if g == null:
		push_error("main: cannot write %s -- the arrival build stays on the "
			% out + "generator's own paths and will not load here")
		return path
	g.store_string(JSON.stringify(doc))
	g.close()
	print("main: the arrival sidecar names %d path(s) from the machine that "
		% moved + "generated it -- rebased onto %s, written to %s"
		% [_root(), ProjectSettings.globalize_path(out)])
	return out


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
	#
	# AND SETTING IT WAS STILL NOT ENOUGH, WHICH IS THE POINT OF THE PRINT
	# BELOW. The key existed and carried "" for six sessions, because the only
	# occluder anyone had ever generated landed in `scene/deck/` -- the
	# one-cluster walk-test fixture -- while `boot.py::preferred_deck_dir`
	# correctly boots from `scene/station/`, where `tools/export_station.py`
	# wrote no occluder at all. `walk.gd::_load_occluder` then returned in
	# silence, because "a missing file is not an error", and 24% of submitted
	# geometry went uncollected with every gate green.
	#
	# So this says WHICH MODE IT IS RUNNING IN, on every run, in the engine's
	# own output -- the rule this project already wrote down for any tool that
	# can substitute a lesser mode for the one it was asked for. It is four
	# lines and it is the only thing here that could have caught it: a static
	# scan can see a caller exists, and only running the thing shows what the
	# caller was handed. `boot.py::occluder` supplies `occluder_why`.
	var occ := String(_boot.get("occluder", ""))
	if occ == "":
		print("main: OCCLUDER NOT SET -- rendering with NO occlusion culling. "
			+ "boot.json says: %s" % String(_boot.get("occluder_why",
				"no reason recorded; run `python3 station/boot.py`")))
	elif not FileAccess.file_exists(occ):
		print("main: OCCLUDER MISSING -- boot.json names %s and it is not " % occ
			+ "on this machine; rendering with NO occlusion culling")
		occ = ""
	elif not ProjectSettings.get_setting(
			"rendering/occlusion_culling/use_occlusion_culling", false):
		# THE SECOND RUNG, CHECKED RATHER THAN ASSUMED. Godot 4.4's own default
		# for this key is FALSE, measured; an OccluderInstance3D in a project
		# without it is inert geometry that costs memory and culls nothing.
		print("main: occluder %s WILL BE IGNORED -- " % occ.get_file()
			+ "rendering/occlusion_culling/use_occlusion_culling is off")
	else:
		print("main: occluder %s (%d bytes), occlusion culling ON"
			% [occ.get_file(), FileAccess.get_file_as_bytes(occ).size()])
	w.set("occluder_path", occ)
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
	# THE LADDER AND THE LIBRARIES, not just the placement list. Setting
	# `crowd_path` alone is the exact defect `walk.gd::_derived_crowd_glbs`
	# documents as instance ten: its scan-the-directory fallback then loads
	# whatever it finds under a synthetic `1e9:8` ladder, so every walker on
	# the deck is drawn with the 400 m body at every distance. Empty strings
	# leave the fallback in charge, which is what a deck with no baked library
	# should still do.
	w.set("crowd_ladder", String(_boot.get("crowd_ladder", "")))
	w.set("crowd_glbs", String(_boot.get("crowd_glbs", "")))
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
	_fire_collapses()
	_vista_update()


## Mount or release the view through the window as the player enters and leaves
## the places that have one.
##
## THE FRAME IS THE WHOLE DIFFICULTY AND IT IS WHY THIS IS NOT ONE LINE.
## `render_shot.gd --shot interior` builds ONE room in a ROOM-LOCAL frame, so
## it mounts the vista at the scene root and the two coincide. The shipped
## build is in STATION WORLD COORDINATES, 8 km of them, so the same geometry
## has to be placed at the aperture's own pose.
##
## The manifest already carries it: `aperture.p` and `aperture.basis` are in
## station coordinates. `station/vista.py` builds the room-local geometry as
## `L = (V - p) @ B`, so `local_j = (world - p) . B[:,j]` -- which makes the
## local axes the COLUMNS of B and the inverse `world = B @ local + p`.
##
## THAT CONVENTION WAS CHECKED NUMERICALLY BEFORE THIS WAS WRITTEN, because
## session 4q found `npc.gd` drawing the entire corridor crowd mirrored from a
## `Basis(fwd.cross(up), up, fwd)` with determinant -1, and no gate here asks a
## transform whether it is a rotation. For all three apertures: det(B) = +1.000,
## `B[:,2]` equals the manifest's own station-frame `normal` to 0, and a
## local -> world -> local round trip closes to 1.8e-13 m. The first test tried
## could NOT have caught an error -- `cnc`'s basis is symmetric to 1.2e-16, so
## B and B.T give identical answers and the check passed for no reason. The
## domes are the discriminating case.
func _vista_update() -> void:
	if _mode != "station":
		return
	# CACHED, AND `_hud()` IS WHY. It is `_find_where(self, ...)`, a RECURSIVE
	# WALK OF THE WHOLE TREE -- fine for the once-per-run callers it was written
	# for and a real regression from `_process`, where the tree holds every mesh
	# instance, walker and prop in three resident cells. The shipped frame is
	# 5.48 ms with 3.0x headroom; a per-frame tree walk is exactly how that gets
	# spent without anybody noticing, because no gate here times `_process`.
	if _hud_cache == null or not is_instance_valid(_hud_cache):
		_hud_cache = _hud()
	var hud = _hud_cache
	var key := "" if hud == null else String(hud.get("place_key"))
	if not hud_inside(hud):
		key = ""
	if key == _vista_place:
		return
	if _vista != null:
		_vista.queue_free()
		_vista = null
		print("vista: released '%s'" % _vista_place)
	_vista_place = key
	if key == "" or _world == null:
		return
	var man := _vista_manifest(key)
	if man.is_empty():
		return
	_vista = load("res://scripts/vista.gd").mount(_world, key, VISTA_DIR)
	if _vista == null:
		return
	var ap: Dictionary = man.get("aperture", {})
	(_vista as Node3D).global_transform = Transform3D(
		_basis_cols(ap.get("basis", [])), _v3(ap.get("p", [])))
	print("vista: MOUNTED '%s' in the shipped build at %s -- %d triangles"
		% [key, (_vista as Node3D).global_transform.origin,
			int(man.get("triangles", 0))])


## Is the player INSIDE a place, rather than near one? Near is not in: the
## corridor outside C&C is not C&C and must not pay for its window.
func hud_inside(hud) -> bool:
	return hud != null and bool(hud.get("place_inside"))


## Prove the shipped build can mount a vista, and say where it cannot.
##
## WHY A GATE AND NOT A WALK TEST. This project's rule is that only running the
## thing tells you the caller runs, and the strongest form of that here would
## be to walk a body to C&C's window and grep the loader's line. IT CANNOT BE
## DONE IN THE SHIPPED BUILD TODAY, and finding out why is most of this gate's
## value: the boot deck is `blue_0_0` at the z ~7120 cluster, and all three
## places that have a window -- `cnc`, `obs_dome_1`, `obs_dome_2` -- sit at
## z 7938..7982, a DIFFERENT z-cluster of the same deck. There is no walk from
## the spawn to a window. Writing the mount and stopping there would have been
## instance eleven of exactly the defect it fixes.
##
## So this drives the mount directly for every place that has a manifest, and
## checks the thing a walk test would have checked: that the node exists, that
## it is placed at the aperture's own station coordinates, and that the hull
## geometry LANDED WHERE THE HULL IS -- an aperture-frame mesh mounted with the
## basis transposed still produces a node at the right origin and a station
## pointing the wrong way, which is the mirrored-crowd defect's exact shape.
##
## Two controls, both of which fail when the code is right:
##   * a place with no manifest must mount nothing;
##   * mounting with the TRANSPOSED basis must move the geometry, and the gate
##     reports by how much. If that comes back 0 the check is inert -- which is
##     true for `cnc` alone, whose basis is symmetric to 1.2e-16, and is why
##     the domes are the discriminating case and are checked too.
func _vista_gate() -> void:
	for _i in 4:
		await get_tree().physics_frame
	var keys := ["cnc", "obs_dome_1", "obs_dome_2"]
	var mounted := 0
	var worst_origin := 0.0
	var least_control := INF
	var control_places := 0
	var symmetric: Array = []
	var fail := ""
	for k in keys:
		var man := _vista_manifest(k)
		if man.is_empty():
			fail = "%s has no manifest" % k
			break
		var ap: Dictionary = man.get("aperture", {})
		var want := _v3(ap.get("p", []))
		var node = load("res://scripts/vista.gd").mount(self, k, VISTA_DIR)
		if node == null:
			fail = "%s did not mount" % k
			break
		var n3 := node as Node3D
		n3.global_transform = Transform3D(
			_basis_cols(ap.get("basis", [])), want)
		worst_origin = maxf(worst_origin, n3.global_transform.origin.distance_to(want))
		# WHERE DID THE GEOMETRY GO? The aperture normal is a station-frame
		# unit vector and `B[:,2]` is its local +Z, so a correctly mounted
		# vista maps local +Z onto it. Transposing the basis inverts the
		# rotation; the control measures how far that moves a point 1 km out
		# along the view axis, which is the scale a window actually shows.
		var probe := Vector3(0.0, 0.0, 1000.0)
		var good := n3.global_transform * probe
		var B := _basis_cols(ap.get("basis", []))
		var bad := Transform3D(B.transposed(), want) * probe
		var moved := good.distance_to(bad)
		# A SYMMETRIC BASIS IS ITS OWN TRANSPOSE, so for such a place this
		# control CANNOT fire and reporting it as though it had is worse than
		# not running it. `cnc` is symmetric to 1.2e-16 -- the first version of
		# this gate took the MIN across all three places, so cnc dragged the
		# control to 0.0 m and the gate PASSED with a dead check. Each place
		# now declares which case it is, and the pass condition requires the
		# asymmetric ones to move.
		var asym := maxf(maxf((B.x - Basis(B.x, B.y, B.z).transposed().x).length(),
			(B.y - B.transposed().y).length()), (B.z - B.transposed().z).length())
		if asym > 1.0e-9:
			control_places += 1
			least_control = minf(least_control, moved)
			if moved < 1.0:
				fail = "%s: basis is asymmetric (%.3g) but transposing it moves the view %.3f m -- the control is inert" % [k, asym, moved]
				node.queue_free()
				break
		else:
			symmetric.append(k)
		var nrm := _v3(ap.get("normal", []))
		var got := (good - want).normalized()
		if nrm.length() > 0.5 and got.distance_to(nrm) > 1e-3:
			fail = "%s: local +Z maps to %s, manifest normal is %s" % [k, got, nrm]
			node.queue_free()
			break
		mounted += 1
		node.queue_free()
	# CONTROL: a place with no window must mount nothing.
	var none = load("res://scripts/vista.gd").mount(self, "plantroom_bay", VISTA_DIR)
	if none != null:
		fail = "a place with no manifest mounted a vista"
		none.queue_free()
	# CAN THE PLAYER REACH ANY OF THEM IN THIS BUILD? Computed, not asserted,
	# and it is the most useful line this gate prints. The mount is correct and
	# in the shipped `_process`, and the shipped build still cannot show it: the
	# boot cell cluster and the windows are different z-clusters of one deck.
	# Reported as the axial gap from the spawn to the nearest aperture so the
	# number moves on its own when the build boots somewhere else.
	var spawn_z := 0.0
	if _world != null and _world.get("spawn") != null:
		spawn_z = (_world.get("spawn") as Vector3).z
	var nearest := INF
	for k in keys:
		var a: Dictionary = _vista_manifest(k).get("aperture", {})
		if a.has("z_m"):
			nearest = minf(nearest, absf(float(a["z_m"]) - spawn_z))
	var reach := "no -- nearest window is %.0f m along the axis from the spawn (a different z-cluster of blue/0/0)" % nearest
	# THE CONTROL HAS TO HAVE FIRED SOMEWHERE. If every basis were symmetric
	# there would be nothing distinguishing the right convention from its
	# inverse, and a PASS would mean only "it mounted".
	if control_places == 0 and fail == "":
		fail = "no place has an asymmetric basis -- the transpose control cannot discriminate"
	var ok: bool = fail == "" and mounted == keys.size()
	print("VISTA gate=%s mounted=%d/%d origin_err=%.6f m " % [
			"PASS" if ok else "FAIL", mounted, keys.size(), worst_origin]
		+ "transpose_control fired on %d place(s), worst %.1f m " % [
			control_places, 0.0 if least_control == INF else least_control]
		+ "(symmetric, cannot discriminate: %s) " % [
			"none" if symmetric.is_empty() else ", ".join(symmetric)]
		+ "no_manifest_mounts=%s reachable_from_spawn=%s%s" % [
			str(none != null), reach, "" if fail == "" else "  -- " + fail])
	get_tree().quit(0 if ok else 1)


func _vista_manifest(key: String) -> Dictionary:
	var path := VISTA_DIR.path_join(key + ".json")
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


## A Godot `Basis` from a row-major 3x3, taking COLUMNS as the basis vectors.
##
## `Basis(x, y, z)` takes the three COLUMN vectors -- the images of the local
## axes -- so column j is `(m[0][j], m[1][j], m[2][j])`. Feeding it the ROWS
## builds the transpose, which for a rotation is the inverse: geometry that
## looks plausible and faces the wrong way. That is exactly the shape of the
## mirrored-crowd defect, so it is spelled out rather than inlined.
func _basis_cols(m) -> Basis:
	var a: Array = m as Array
	if a.size() != 3:
		return Basis()
	return Basis(
		Vector3(float(a[0][0]), float(a[1][0]), float(a[2][0])),
		Vector3(float(a[0][1]), float(a[1][1]), float(a[2][1])),
		Vector3(float(a[0][2]), float(a[1][2]), float(a[2][2])))


func _v3(a) -> Vector3:
	var v: Array = a as Array
	return Vector3.ZERO if v.size() != 3 else Vector3(
		float(v[0]), float(v[1]), float(v[2]))


# ---------------------------------------------------------------------------
# When somebody stops standing up
# ---------------------------------------------------------------------------

## The day's collapses, from `boot.json` -- `incident.RAGDOLL_OF`'s four classes
## over this deck's own rooms, each a named resident with a species and an hour.
var _collapses: Array = []
## How far into the list the clock has got. The list is sorted by hour, so this
## is a cursor and not a search.
var _collapse_i := 0
## How many actually put a body on the deck, and how many had nobody standing
## near enough to be the one who fell. BOTH are reported: an incident that fires
## into an empty room is a real outcome and silently dropping it would make the
## count a claim about the schedule rather than about the station.
var _fell := 0
var _fell_nobody := 0
var _fell_last := ""
## How close the player has to be to the place for the body to be worth
## promoting. Beyond this nobody would see it fall and the promotion would spend
## one of `ragdoll.gd`'s four concurrent slots on nothing.
const COLLAPSE_SIGHT_M := 40.0


## Fire every collapse the clock has passed. Called every frame; costs one float
## compare when there is nothing due, which is almost always.
##
## THE MISSING HALF, AND BOTH HALVES WERE FINISHED. `station/incident.py` has
## decided who collapses, where and at what hour since P1-G3 -- 380 INC-SICK a
## day, with a named resident as the subject -- and wrote it into a ledger.
## `scripts/ragdoll.gd` can drop a 16-segment body at the deck's own 7.454 m/s2
## along its own radius. The only thing that had ever asked for one was
## `--ragdoll-gate`, a flag no player passes: a capability reachable only from
## its own test is this project's signature defect one step before it happens,
## and it has now produced it eleven times.
##
## `--no-collapses` is the control -- the schedule is read, the clock runs past
## every hour in it, and nobody falls over.
func _fire_collapses() -> void:
	if _clock == null or _ragdoll == null or _collapse_i >= _collapses.size():
		return
	var h: float = _clock.hour()
	while _collapse_i < _collapses.size():
		var row: Dictionary = _collapses[_collapse_i]
		if float(row.get("hour", 0.0)) > h:
			return
		_collapse_i += 1
		_collapse(row)


func _collapse(row: Dictionary) -> void:
	var body := _player()
	if body == null:
		return
	# WHERE IT HAPPENS, off the same place boxes the HUD resolves the player
	# against. No second table of where a room is.
	var hud = _hud()
	if hud == null:
		return
	var boxes: Dictionary = _check_boxes(hud)
	var key := String(row.get("place", ""))
	if not boxes.has(key):
		return
	var centre: Vector3 = (boxes[key] as AABB).get_center()
	if body.global_position.distance_to(centre) > COLLAPSE_SIGHT_M:
		# NOT COUNTED AS "NOBODY THERE". Out of sight is not the same failure as
		# an empty room, and conflating them would let a gate pass on a build
		# where the crowd never promotes anybody.
		return
	# UNTYPED, for the reason `_player` and `_hud()` are: `promote_walker` is a
	# SCRIPT member and GDScript resolves a statically typed variable's members
	# at parse time, so a `Node3D` here makes the file fail to compile.
	var crowd = _crowd()
	if crowd == null:
		return
	var spec := {
		"cause": String(row.get("cid", "?")),
		"who": String(row.get("who", "")),
		"dead": bool(row.get("dead", false)),
	}
	var imp := float(row.get("impulse_n_s", 0.0))
	if imp > 0.0:
		# ALONG THE CORRIDOR, away from the player. A shove is directional and a
		# brawl the player is standing in the middle of is a different scene.
		var away := (centre - body.global_position)
		var up_c := Vector3(centre.x, centre.y, 0.0).normalized()
		away = (away - up_c * away.dot(up_c))
		if away.length() > 0.001:
			spec["impulse"] = away.normalized() * imp
	# NO `g` AND NO `up`. `ragdoll.gd` derives both from where the body is --
	# see its `omega2`. A caller that worked them out here would be a second
	# copy of the station's spin.
	var fell := String(crowd.call("promote_walker", _ragdoll, spec, centre,
		12.0, String(row.get("species", ""))))
	if fell == "":
		_fell_nobody += 1
		# SAID, NOT COUNTED. An incident that finds nobody to knock down has
		# four possible causes and they need four different fixes; `npc.gd`
		# knows which one it was.
		print("collapse: %s at %s %05.2f -- nobody fell: %s"
			% [String(row.get("cid", "?")), key, float(row.get("hour", 0.0)),
				String(crowd.get("promote_why"))])
		return
	_fell += 1
	_fell_last = fell
	# WHO THE STATION SAID, AND WHO THE ENGINE COULD FIND. Both, always, and
	# never conflated: `incident.py` names a resident with a home and a job, and
	# the body that falls is whoever the crowd had standing there. When those
	# are not the same person the line says so rather than borrowing the name.
	print("collapse: %s at %s %05.2f -- %s goes down%s (the station's %s, %s, "
		% [String(row.get("cid", "?")), key, float(row.get("hour", 0.0)),
			fell, (" and does not get up" if spec["dead"] else ""),
			String(row.get("who", "?")), String(row.get("species", "?"))]
		+ "%s)" % String(crowd.get("promote_why")))
	# AND THE PLAYER REMEMBERS IT. PLY-07 lists "incident-log entries the
	# player witnessed" among the things the journal auto-records, and this is
	# the only place in the build where the two conditions are both known: the
	# ledger row that says what happened, and the sight test three screens up
	# that says the player was near enough to see it.
	if _journal != null:
		_journal.call("witness_collapse", row, fell,
			(_clock.day() if _clock != null else 0))


## THE STATION KNOCKS SOMEBODY DOWN AND A PLAYER SEES IT -- the gate, in the
## shipped scene, with no flag that manufactures a body.
##
## `--ragdoll-gate` proves the BODY: 16 segments, the right mass, the deck's own
## gravity. It proves nothing about whether the game ever asks for one, and
## until this existed the answer was no -- the only caller of `promote` in the
## project was that gate. So this one touches nothing the runtime would not
## touch: it stands the player where an incident is scheduled, WINDS THE CLOCK
## to just before its hour (`Clock.set_hour` -- "a jump is indistinguishable
## from having waited"), and lets `_process` do the rest. The body that falls is
## a walker out of the crowd, with that walker's species and stature.
##
##   `--no-collapses`  the schedule is emptied -> nobody falls (the build
##                     before this landed)
##   `--no-ragdoll`    the director refuses    -> the walker is put straight
##                     back, and nobody vanishes
func _collapse_gate() -> void:
	for _i in settle_frames:
		await get_tree().physics_frame
	var body := _player()
	var hud = _hud()
	var crowd = _crowd()
	if body == null or hud == null or crowd == null or _clock == null:
		print("COLLAPSE gate=FAIL -- no %s" % [
			("body" if body == null else "hud" if hud == null
				else "crowd" if crowd == null else "clock")])
		get_tree().quit(1)
		return
	var boxes: Dictionary = _check_boxes(hud)
	# The first scheduled row whose place this build actually has geometry for.
	# A row for a room on another deck is not a failure, it is a row nothing on
	# this deck can show -- so it is skipped and COUNTED.
	var pick := -1
	var offdeck := 0
	for i in _collapses.size():
		var r: Dictionary = _collapses[i]
		if boxes.has(String(r.get("place", ""))):
			pick = i
			break
		offdeck += 1
	if pick < 0:
		print("COLLAPSE gate=FAIL -- none of the %d scheduled rows names a "
			% _collapses.size() + "place this build has geometry for")
		get_tree().quit(1)
		return
	var row: Dictionary = _collapses[pick]
	var key := String(row.get("place", ""))
	var at: Vector3 = (boxes[key] as AABB).get_center()
	body.global_position = at
	body.velocity = Vector3.ZERO
	# LET THE ROOM ARRIVE BEFORE ASKING WHO IS IN IT. This build STREAMS, so
	# walking into a cell is what loads its crowd -- and the first version of
	# this gate wound the clock on the same frame as the teleport and reported
	# `nobody=1`, which reads exactly like a broken promotion path and was a
	# gate measuring an empty room. `settle_frames` is two seconds at 60 Hz;
	# `_rebind_on_stream` runs in `_process` and needs the frames as much as
	# the streamer does.
	for _i in settle_frames:
		await get_tree().physics_frame
	_collapse_i = pick
	var h: float = float(row.get("hour", 0.0))
	_clock.set_hour(h - 0.01)
	print(("COLLAPSE gate: standing in %s at %.1f,%.1f,%.1f, clock wound to "
		+ "%05.2f for %s (%s, %s) at %05.2f%s")
		% [key, at.x, at.y, at.z, _clock.hour(), String(row.get("who", "?")),
			String(row.get("species", "?")), String(row.get("cid", "?")), h,
			("" if offdeck == 0 else ", %d earlier rows off this deck"
				% offdeck)])
	# LET THE CLOCK RUN. Nothing here calls `_fire_collapses` -- `_process`
	# does, on its own, exactly as it would with a player at the keyboard.
	var t := 0.0
	while _fell == 0 and _fell_nobody == 0 and t < 20.0:
		await get_tree().process_frame
		t += 1.0 / 60.0
	var live := int(_ragdoll.call("live_count"))
	var ok := _fell > 0 and live > 0
	print(("COLLAPSE gate=%s fell=%d nobody=%d live_ragdolls=%d who=%s "
		+ "clock=%05.2f scheduled=%d cursor=%d") % [
		("PASS" if ok else "FAIL"), _fell, _fell_nobody, live,
		(_fell_last if _fell_last != "" else "-"), _clock.hour(),
		_collapses.size(), _collapse_i])
	print(String(_ragdoll.call("report")))
	get_tree().quit(0 if ok else 1)


# ===========================================================================
# SAVING, AND THE ONE THING A SAVE SYSTEM MUST NOT BE
# ===========================================================================
#
# `scripts/save.gd` writes and reads; this decides WHO is asked. That list is
# here rather than in `save.gd` because this file is the only node that owns
# the whole world -- the same reason `_start_clock`, `_start_ambience` and
# `_start_ragdolls` live here.
#
# EVERY SUBSYSTEM IS OFFERED, INCLUDING THE ONES THAT CANNOT SAVE. `_subjects`
# returns every live node a player's session mutates, and `save.gd::audit`
# splits them into those with the contract and those without. That split is
# printed on every capture, because a save system that quietly saves four of
# nine is indistinguishable in every test from one that saves all nine -- the
# four round-trip, the gate goes green, and the five nobody asked are invisible.
# This project has produced that shape eleven times under a different name.
const SAVE_SCRIPT := "res://scripts/save.gd"

var _save = null


func _save_lib():
	if _save == null:
		_save = load(SAVE_SCRIPT)
	return _save


## Everything a session mutates, by the name it takes in a save file.
##
## FOUND BY METHOD OR BY CLASS, NEVER BY REACHING INTO `walk.gd`'s private
## fields -- the rule `_player()`, `_crowd()` and `_streamer` already follow. A
## save that binds to `walk.gd::_interact` breaks the moment that field is
## renamed, and breaks SILENTLY, into "this subsystem has no save_state".
func _subjects() -> Dictionary:
	var out := {}
	var body := _player()
	if body != null:
		out["player"] = body
	if _clock != null:
		out["clock"] = _clock
	if _world != null:
		for n in _world.find_children("*", "Node3D", true, false):
			# TWO METHODS EACH, because one is not distinctive enough in this
			# tree: `dialogue.gd` and `stream.gd` both define `report()`, and
			# `count()` is on `interact.gd` and `dialogue.gd` alike. The pairs
			# below are unique -- checked by name against both files rather
			# than assumed.
			if n.has_method("verb_report") and n.has_method("pressable_count"):
				out["interact"] = n
			elif n.has_method("offers") and n.has_method("lines_shown"):
				out["dialogue"] = n
	if _streamer != null:
		out["stream"] = _streamer
	if _life != null:
		out["life"] = _life
	var crowd = _crowd()
	if crowd != null:
		out["crowd"] = crowd
	if _audio != null:
		out["ambience"] = _audio
	if _ragdoll != null:
		out["ragdoll"] = _ragdoll
	# WHAT THE PLAYER KNOWS. R7's own sentence for why this had to be a save
	# subject rather than a runtime nicety: *"a journal with no save is a
	# notebook that forgets"*. It carries both halves of `save.gd`'s contract.
	if _journal != null:
		out["journal"] = _journal
	return out


func save_to(slot: String) -> Dictionary:
	var lib = _save_lib()
	var subs := _subjects()
	var snap: Dictionary = lib.capture(subs, {"mode": _mode, "hour": _hour_now()})
	var why: String = lib.write(slot, snap)
	if why != "":
		push_error("save: " + why)
	print("SAVE %s -- %s" % [slot, lib.describe(snap)])
	return snap


func load_from(slot: String) -> Dictionary:
	var lib = _save_lib()
	var snap: Dictionary = lib.read(slot)
	if snap.is_empty():
		print("SAVE load %s -- nothing there" % slot)
		return {}
	var r: Dictionary = lib.restore(_subjects(), snap)
	print("SAVE load %s -- applied %s%s%s" % [slot,
		", ".join(PackedStringArray(r["applied"])),
		("; file had no section for " + ", ".join(PackedStringArray(r["absent"]))
			if (r["absent"] as Array).size() > 0 else ""),
		("; file had unknown sections " + ", ".join(PackedStringArray(r["unknown"]))
			if (r["unknown"] as Array).size() > 0 else "")])
	return snap


func _hour_now() -> float:
	return (_clock.hour() if _clock != null else -1.0)


## G8 -- SAVE, WALK AWAY, LOAD, AND CHECK YOU CAME BACK.
##
## THE PERTURBATION IS THE GATE. Capturing a snapshot and restoring it into a
## world nobody touched proves nothing at all: every field already holds the
## value the snapshot carries, so a `load_state` that does nothing passes. So
## this MOVES the player, MOVES the clock, SPENDS money and COUNTS a
## conversation between the save and the load, and asserts the restore undid
## every one of them.
##
## `--no-restore` is the control and it skips only the load. It must FAIL, and
## on exactly the fields the perturbation moved -- if it passes, the
## perturbation is not reaching anything the check reads, which is the vacuous
## A/B this project has recorded twice.
func _save_gate() -> void:
	for _i in settle_frames:
		await get_tree().physics_frame
	var lib = _save_lib()
	var subs := _subjects()
	var au: Dictionary = lib.audit(subs)
	print("SAVE subjects: %d live, %d can save (%s)%s%s" % [
		subs.size(), (au["can"] as Array).size(),
		", ".join(PackedStringArray(au["can"])),
		("; NO save_state: " + ", ".join(PackedStringArray(au["missing"]))
			if (au["missing"] as Array).size() > 0 else ""),
		("; HALF the contract: " + ", ".join(PackedStringArray(au["partial"]))
			if (au["partial"] as Array).size() > 0 else "")])

	var body := _player()
	if body == null:
		print("SAVE gate=FAIL no player")
		get_tree().quit(2)
		return

	var before := {
		"pos": body.global_position,
		"hour": _hour_now(),
		"credits": float(body.credits),
		"bag": (body.carrying as Array).size(),
	}
	save_to("gate")

	# --- walk away ---------------------------------------------------------
	# Along the corridor rather than across it: +Z is the station's AXIS and a
	# ring corridor is 2.60 m wide in that direction, so an offset along +Z
	# walks the body off its own floor. Same derivation as `_ragdoll_gate`.
	var p: Vector3 = body.global_position
	var radial := Vector3(p.x, p.y, 0.0)
	var up: Vector3 = (-radial.normalized() if radial.length() > 0.001
		else Vector3.UP)
	var along: Vector3 = up.cross(Vector3(0, 0, 1)).normalized()
	body.global_position = p + along * 12.0
	# FIVE HOURS, AND THE FIVE IS NOT ARBITRARY. `hour()` wraps at 24, and the
	# first version of this line advanced the clock by 3,600 station hours --
	# exactly 150 days, exactly zero hours -- so the perturbation moved the
	# clock by 0.0029 h, which was the real time the frames themselves took.
	# The gate reported the clock as failing and it was the CONTROL that was
	# broken. Any advance that is not a multiple of 24 works; 5 is one.
	if _clock != null:
		_clock.tick(5.0 / max(_clock.rate, 1e-9))
	var moved_credits := false
	if body.credits >= 0.0:
		body.credits = body.credits + 137.0
		moved_credits = true
	body.carrying.append("save-gate-token")
	for _i in 10:
		await get_tree().physics_frame
	var perturbed := {
		"pos": body.global_position,
		"hour": _hour_now(),
		"credits": float(body.credits),
		"bag": (body.carrying as Array).size(),
	}

	# --- and come back -----------------------------------------------------
	if _args().has("no-restore"):
		print("SAVE: RESTORE SKIPPED (control)")
	else:
		load_from("gate")
	# THE CLOCK IS READ IN THE RESTORE'S OWN FRAME, and the settle frames come
	# after. `main._process` ticks the clock every frame, so ten frames of
	# settling move it by the real time they take -- 0.0028 h at the default
	# rate, which is small and is not zero. Reading it here needs no tolerance;
	# reading it after the settle would need one that grew with
	# `settle_frames`, and a tolerance that tracks the harness is one that will
	# eventually swallow the thing it was written to catch.
	var hour_back: float = _hour_now()
	for _i in 10:
		await get_tree().physics_frame

	var after := {
		"pos": body.global_position,
		"hour": hour_back,
		"credits": float(body.credits),
		"bag": (body.carrying as Array).size(),
	}
	var d_pos: float = (after["pos"] as Vector3).distance_to(before["pos"])
	var d_hour: float = absf(float(after["hour"]) - float(before["hour"]))
	var d_cred: float = absf(float(after["credits"]) - float(before["credits"]))
	var d_bag: int = int(after["bag"]) - int(before["bag"])
	# The body is a physics object and ten frames of gravity move it, so the
	# position tolerance is a stride rather than zero. Everything else is exact.
	var ok_pos: bool = d_pos < 0.75
	var ok_hour: bool = d_hour < 1e-4
	var ok_cred: bool = d_cred < 1e-4
	var ok_bag: bool = d_bag == 0
	var moved: float = (perturbed["pos"] as Vector3).distance_to(before["pos"])
	print("SAVE perturbation: moved %.2f m, clock +%.4f h, credits %s, bag +1"
		% [moved, absf(float(perturbed["hour"]) - float(before["hour"])),
			("+137.00" if moved_credits else "no purse in this build")])
	print("SAVE restored: pos %.3f m off, clock %.5f h off, credits %.2f off, bag %+d"
		% [d_pos, d_hour, d_cred, d_bag])
	var ok: bool = ok_pos and ok_hour and ok_cred and ok_bag
	print("SAVE gate=%s pos=%s clock=%s credits=%s bag=%s"
		% ["PASS" if ok else "FAIL", str(ok_pos), str(ok_hour), str(ok_cred),
			str(ok_bag)])
	get_tree().quit(0 if ok else 1)


## `npc.gd`'s crowd node, found by METHOD rather than by name or by reaching
## into `walk.gd`'s private field -- the same rule `_player()` and `_streamer`
## follow, and for the same reason.
func _crowd():
	if _world == null:
		return null
	for n in _world.find_children("*", "Node3D", true, false):
		if n.has_method("promote_walker"):
			return n
	return null


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
# Bodies that stop standing up
# ---------------------------------------------------------------------------
## The player's notebook. PLY-07, SYS-16, CAST-05, and PLY-05's compression.
##
## THE NODE IS ADDED HERE AND THE RULES ARE NOT DECIDED HERE. Everything the
## journal knows about what a fact IS comes from `station/generated/journal.json`
## -- `python3 station/journal.py --emit` -- for the reason `interact.gd` reads
## `interact.py`'s sidecar and `dialogue.gd` reads `dialogue.py`'s: a second
## copy of a decision is the defect this repository has paid for three times.
##
## A MISSING MANIFEST IS SOFT. `install` warns and the journal simply cannot
## mint, exactly as a missing navgraph leaves `Director.nav` null. The station
## still boots.
func _start_journal() -> void:
	var s := load(JOURNAL_SCRIPT)
	if s == null:
		push_error("main: could not load %s" % JOURNAL_SCRIPT)
		return
	_journal = Node3D.new()
	_journal.name = "Journal"
	_journal.set_script(s)
	add_child(_journal)
	_journal.call("install", self)


func _start_ragdolls() -> void:
	_ragdoll = Node3D.new()
	_ragdoll.name = "Ragdolls"
	_ragdoll.set_script(load(RAGDOLL_SCRIPT))
	add_child(_ragdoll)
	_ragdoll.set("data_dir",
		_root().path_join("station/generated/scene/npc"))
	# THE SPIN, ONCE, SO NO CALLER HAS TO WORK IT OUT. Without it a promotion
	# that does not state its own gravity falls at Earth's, which is wrong
	# everywhere on this station -- see `ragdoll.gd::omega2`.
	_ragdoll.set("omega2", _spin_omega2())
	# THE DAY'S COLLAPSES. `--no-collapses` is the control: the schedule is
	# still read and reported, the clock still runs past every hour in it, and
	# nobody falls over -- which is the build before this line existed.
	_collapses = _boot.get("collapses", [])
	if _args().has("no-collapses"):
		print("collapse: DISABLED (control) -- %d scheduled, none will fire"
			% _collapses.size())
		_collapses = []
	else:
		# THE DAY DOES NOT START OVER WHEN THE BUILD DOES. The schedule is a
		# whole station-day and the player boots in at 13:00, so the twenty-four
		# rows before that already happened -- firing them all on frame one
		# would drop the entire morning's casualties in the player's lap at
		# once. The cursor starts at the first row the clock has NOT passed.
		var h0: float = (_clock.hour() if _clock != null else start_hour)
		while (_collapse_i < _collapses.size()
			and float((_collapses[_collapse_i] as Dictionary).get("hour", 0.0))
				<= h0):
			_collapse_i += 1
		print("collapse: %d bodies scheduled today on this deck, %d still to "
			% [_collapses.size(), _collapses.size() - _collapse_i]
			+ "come after %05.2f" % h0)
	var b := _player()
	if b != null:
		_ragdoll.call("watch", b)
	if _world != null:
		_ragdoll.call("set_material_donor", _world)
	print("ragdoll: director ready, bodies from %s, controls %s"
		% [_ragdoll.get("data_dir"), _ragdoll.call("apply_controls")])


## The spin gravity at a world point, DERIVED from the deck table rather than
## from a spin rate written down twice. `cell_manifest.json` records
## `floor_r_m` and `floor_g` for all 251 decks, and on a rigid rotor
## g = omega^2 r -- so any one row gives omega^2 and it is exact at every
## radius, including the ones with no deck on them.
func _spin_omega2() -> float:
	var man := _root().path_join("station/generated/cell_manifest.json")
	if not FileAccess.file_exists(man):
		return 0.0
	var f := FileAccess.open(man, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return 0.0
	for row in ((d as Dictionary).get("deck_table", []) as Array):
		var r := float((row as Dictionary).get("floor_r_m", 0.0))
		var g := float((row as Dictionary).get("floor_g", 0.0))
		if r > 1.0 and g > 0.0:
			return g * 9.80665 / r
	return 0.0


## Drop bodies where the player is standing, on the streamed build, and print
## what they did. `station/npc/ragdoll.py --gate` proves the BODY; this proves
## it is reachable -- which in this project is the half that keeps failing.
func _ragdoll_gate() -> void:
	for _i in settle_frames:
		await get_tree().physics_frame
	var body := _player()
	if body == null or _ragdoll == null:
		print("RAGDOLL gate=FAIL no player or no director")
		get_tree().quit(2)
		return
	var p: Vector3 = body.global_position
	# UP IS INWARD ON A SPUN RING -- the floor is the outer wall, so a head
	# points at the axis, and the axis is +Z. Same derivation as
	# `npc.gd::collect`, and it is why this is not Vector3.UP.
	var radial := Vector3(p.x, p.y, 0.0)
	var up: Vector3 = -radial.normalized() if radial.length() > 0.001 else Vector3.UP
	var g: float = _spin_omega2() * radial.length()
	var zero := _args().has("zero-g")
	# ALONG THE CORRIDOR, AND THE CORRIDOR IS NOT THE AXIS. A ring corridor
	# runs round the circumference; +Z is the station's axis and is the
	# corridor's WIDTH -- 2.60 m of it, which `walk.gd` prints as `w=2.60`.
	# Offsetting the drops along +Z put two of the three bodies off the edge of
	# their own floor, where they fell at terminal velocity for the whole gate
	# and reported "settle=NEVER" as if the physics were wrong.
	var axis := Vector3(0, 0, 1)
	var along: Vector3 = up.cross(axis).normalized()
	# RIGHT-HANDED, and it is checked rather than eyeballed: `Basis(x, y, z)`
	# takes the three COLUMNS, and `along.cross(up)` gives an x whose
	# x cross y is MINUS z on a ring corridor. `ragdoll.gd::promote` refuses a
	# transform with a non-positive determinant for exactly this reason.
	var basis := Basis(along, up, axis).orthonormalized()
	print(("RAGDOLL gate: at %.2f,%.2f,%.2f r=%.1f m, up=%.3f,%.3f,%.3f, "
		+ "g=%.3f m/s2 (%.3f g)%s")
		% [p.x, p.y, p.z, radial.length(), up.x, up.y, up.z, g,
		g / 9.80665, (" -- ZERO-G CONTROL" if zero else "")])
	var drops := [
		["INC-SICK", {"cause": "INC-SICK", "dead": false,
			"velocity": Vector3.ZERO, "offset": -3.0}],
		["INC-ACCIDENT", {"cause": "INC-ACCIDENT", "dead": true,
			"velocity": along * 1.4, "offset": 3.0}],
		["INC-BRAWL", {"cause": "INC-BRAWL", "dead": true,
			"velocity": Vector3.ZERO, "offset": 1.5,
			"impulse": along * 60.0}],
	]
	for row in drops:
		var spec: Dictionary = (row[1] as Dictionary).duplicate()
		var off: float = float(spec["offset"])
		spec.erase("offset")
		spec["species"] = "human"
		spec["h_m"] = 1.75
		# AT THE PLAYER'S FEET, WHICH IS THE PLAYER'S OWN ORIGIN.
		# `walk.gd::_spawn_player` puts the capsule at `Vector3(0, 0.9, 0)`
		# INSIDE the body, so the CharacterBody3D's origin is the sole -- and a
		# ragdoll dropped at `p - up * 0.9` starts 0.9 m inside the deck, which
		# a solver answers with a push-out of several hundred metres a second.
		#
		# EACH BODY STANDS ON ITS OWN LOCAL VERTICAL, and this cost two runs to
		# get right. Sharing the player's vertical across three drops 3 m apart
		# at r=211.5 m is a ~0.8 deg mismatch, which sounds like nothing: a body
		# laid down on one vertical and pulled along another lands on its hip
		# and keeps pressing, and INC-ACCIDENT came to rest **123-127 mm INTO
		# the deck** against the 10 mm the solver allows -- reproducibly, two
		# runs byte-identical. Whichever of placement and gravity was the
		# odd one out, that body sank; with both taken from where it actually
		# is, all three rest at 10.3-11.9 mm.
		var at: Vector3 = p + along * off
		var rad_at := Vector3(at.x, at.y, 0.0)
		var r_at := rad_at.length()
		var up_at: Vector3 = -rad_at / r_at if r_at > 0.001 else up
		var along_at: Vector3 = up_at.cross(axis).normalized()
		# `--derive-g` IS THE CONTROL FOR THE DERIVATION, and it is the one
		# control here that tests a CALLER rather than the body. Every real
		# promotion path -- `npc.gd::promote_walker` -- states neither `g` nor
		# `up`, so the numbers a gate hands in are exactly the numbers nobody
		# supplies in the game. Withholding them makes `ragdoll.gd` work both
		# out from the body's own world position, and the two halves must agree:
		# the subject states the SAME quantities this loop just computed, so the
		# only difference between the two runs is WHO computed them.
		if not _args().has("derive-g"):
			spec["up"] = up_at
			spec["g"] = 0.0 if zero else _spin_omega2() * r_at
		spec["xform"] = Transform3D(
			Basis(along_at, up_at, axis).orthonormalized(), at)
		_ragdoll.call("gate_drop", String(row[0]), spec)
	var t := 0.0
	while not bool(_ragdoll.call("gate_done")) and t < 12.0:
		await get_tree().physics_frame
		t += 1.0 / 60.0
	print(String(_ragdoll.call("gate_verdict")))
	print("RAGDOLL gate=%s %s controls=%s"
		% [("PASS" if not zero else "CONTROL"),
		String(_ragdoll.call("report")), String(_ragdoll.call("apply_controls"))])
	get_tree().quit(0)


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
	_boot_why = ""
	var path := String(args.get("boot", ""))
	if path == "":
		var derived := _root().path_join("station/generated/scene/boot.json")
		if FileAccess.file_exists(derived):
			path = derived
	if path == "":
		var deck := _root().path_join("station/generated/scene/deck")
		var d := DirAccess.open(deck)
		if d == null:
			return _no_world("no %s" % deck)
		var found: Array = []
		for f in d.get_files():
			if f.ends_with("_arrival.json"):
				found.append(deck.path_join(f))
		if found.is_empty():
			return _no_world("no boot.json and no *_arrival.json in %s" % deck)
		found.sort()
		path = found[0]
		print("main: no boot.json -- falling back to the arrival sidecar; "
			+ "run `python3 station/boot.py` to write one")
	if not FileAccess.file_exists(path):
		return _no_world("nothing at %s" % path)
	var f2 := FileAccess.open(path, FileAccess.READ)
	var doc = JSON.parse_string(f2.get_as_text())
	if typeof(doc) != TYPE_DICTIONARY:
		return {}
	var b: Dictionary = doc.get("build", doc)
	if b.is_empty() or not b.has("glb"):
		return {}
	var out := b.duplicate()
	out["_source"] = path
	# EVERY PATH IN THE MANIFEST IS REBASED ONTO THIS INSTALL. See `_rebase`.
	for k in ["glb", "collision", "interact", "actors", "crowd", "dialogue",
			"occluder", "cells_path"]:
		if out.has(k):
			out[k] = _rebase(String(out[k]))
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


## Why there is no world, in one line, WITH THE DIRECTORY IT LOOKED IN.
##
## AN EXPORTED BUILD READS ITS WORLD FROM `res://..`, and where that lands is a
## property of the SHIPPED LAYOUT rather than of the source tree. So "no boot
## manifest" with no path beside it is a message a player cannot act on and a
## packager cannot debug -- which is exactly what it cost when `tools/package.sh`
## first staged a build: the artefact came up, refused, and said nothing about
## where it had been looking. Carried into `main_menu.gd` so the sentence a
## player reads on the title screen is this one.
var _boot_why := ""


## A PATH FROM THE MANIFEST, MOVED ONTO THIS INSTALL.
##
## `station/boot.py` writes ABSOLUTE paths -- `/home/user/Opus-5/station/
## generated/scene/deck/blue_0_0_z7440.glb` -- because on the machine that
## generates the world that is the correct, unambiguous answer. It is the wrong
## answer everywhere else, and "everywhere else" is the entire point of
## `tools/package.sh`: a stranger who unpacks the tarball into `~/games/` has no
## `/home/user/Opus-5`, and every one of those paths is a file that does not
## exist.
##
## THIS WAS ALMOST MISSED, AND THE WAY IT WAS ALMOST MISSED IS THE LESSON. The
## first packaged build launched, reached customs and issued a card -- on the
## build machine, where the generator's own directory still existed. The
## evidence was real and it was true for the wrong reason. What settles it is
## the control `package.sh` now runs: the staged tree is MOVED before it is
## launched, so a build that only works in the place it was made fails.
##
## The rewrite is anchored on `station/generated/`, which is the one path
## fragment every generated artefact in this project shares, and it FALLS BACK
## to the original if the rebased file is not there -- so a developer running
## from source with a hand-passed `--boot=` outside the tree is unaffected.
func _rebase(p: String) -> String:
	if p == "":
		return p
	var i := p.find("station/generated/")
	if i < 0:
		return p
	var here := _root().path_join(p.substr(i)).simplify_path()
	if here == p:
		return p
	if FileAccess.file_exists(here) or DirAccess.dir_exists_absolute(here):
		return here
	return p


func _no_world(why: String) -> Dictionary:
	_boot_why = why
	print("main: NO WORLD -- %s (res:// is %s, so the world is expected under %s)"
		% [why, ProjectSettings.globalize_path("res://"), _root()])
	return {}


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


## WHERE THE WORLD IS. Everything under `station/generated/` -- the deck mesh,
## the collision shell, the interactables, the arrival sequence, the cell set,
## the audio bank -- lives OUTSIDE `res://` and is read from disk at runtime,
## so this one function decides whether the shipped build can find any of it.
##
## AND IT WAS EDITOR-ONLY, WHICH NOBODY COULD HAVE SEEN UNTIL SOMETHING WAS
## EXPORTED. It used to be exactly `globalize_path("res://").path_join("..")`,
## which is right in a source run and **returns `".."` in an exported one**:
## measured in session 4t, `ProjectSettings.globalize_path("res://")` is the
## EMPTY STRING in a packed build, because `res://` is inside a .pck and has no
## filesystem path at all. `".."` is then resolved against the process working
## directory -- so the packaged game looked for its world one level above
## wherever the player happened to be standing in a shell, found nothing, and
## said "no boot manifest".
##
## It is the same shape as every no-caller defect in CLAUDE.md's list, one layer
## down: the function was correct, tested, and had never been run on the path
## that ships. Nothing could have caught it before `tools/package.sh` existed,
## and `package.sh` caught it on its first run by LAUNCHING the artefact.
##
## `--data=<dir>` overrides, for a build whose world sits somewhere else.
var _root_cache := ""


func _root() -> String:
	if _root_cache != "":
		return _root_cache
	var args := _args()
	if args.has("data"):
		_root_cache = String(args["data"])
		return _root_cache
	var base := ProjectSettings.globalize_path("res://")
	if base == "":
		# EXPORTED. The pack sits beside the executable, so the executable's own
		# directory is the anchor -- and it is an anchor that does not care what
		# the working directory is, which `".."` did.
		base = OS.get_executable_path().get_base_dir()
	_root_cache = base.path_join("..").simplify_path()
	return _root_cache


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
