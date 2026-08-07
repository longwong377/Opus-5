extends CanvasLayer
## THE FRONT DOOR. The first thing a person who is not a developer ever sees.
##
## WHAT THIS EXISTS TO END, measured in session 4t rather than remembered:
## `godot/export_presets.cfg` did not exist, `tools/` had no packaging path, and
## there was no title screen, no new-game and no continue anywhere in 25,000
## lines of GDScript. `docs/MASTER-PLAN.md` A2's definition of done opens *"a
## stranger downloads ONE FILE, runs it at 60 fps, arrives at Babylon 5 as a
## person with papers"* -- and the honest state of that sentence was that
## **there was no way for a person to start this at all.** Launching the shipped
## scene without the generated world printed `main: no boot manifest` to a
## console a player cannot see and quit 2: a black flash and nothing.
##
## SO THE FIRST RESPONSIBILITY OF THIS FILE IS NOT A MENU, IT IS SAYING WHY.
## Every entry below reports whether it can run and, when it cannot, the exact
## command that makes it able to -- on screen, where a person is looking, not in
## `push_error`. That is CLAUDE.md's rule about tools that silently substitute a
## lesser mode, applied to the one surface a player actually meets: a front door
## that quietly does nothing is worse than one that says the room is not built.
##
## IT IS DRIVABLE WITHOUT A KEYBOARD, and that is what makes it gateable.
## `items()`, `move()` and `activate()` are the whole interface, and
## `main.gd --menu-gate` runs this headlessly, walks the list, presses NEW GAME
## and asserts the world came up. A menu that only a human can operate is a menu
## no CI step can fail on -- which is this project's signature defect wearing a
## different hat, since a title screen with no reachable NEW GAME is finished
## machinery with no caller.
##
## THE LOOK IS DRAWN, NOT ASSEMBLED, for `hud.gd`'s and `arrival.gd`'s stated
## reason: the whole house style is small capitals, hairlines and two accent
## colours, a StyleBox cannot express it without a texture, and this project has
## a standing rule against binary resources entering the repository. The colours
## here are `arrival.gd::Face`'s own CYAN, AMBER, RED and INK, taken from that
## file rather than re-picked, so the title screen and the identicard the player
## is about to be handed are the same object.

## What the player picked. `main.gd` connects to this and builds that mode.
signal chosen(id: String)

## Set by `main.gd` before this is added to the tree: whether there is a world on
## disk to boot into, and if not, the command that builds one. Passed in rather
## than looked up here, because `main.gd::_boot_manifest` is the one place that
## knows where a boot manifest lives and a second copy of that search would be a
## second description of where the world is.
var world_ok := false
var world_why := ""
## Whether `save.gd` found a slot, and its one-line description.
var save_ok := false
var save_why := ""

var index := 0
var _rows: Array = []
var _face: Control
## Set once `activate()` has fired, so a held key or a second gate call cannot
## build two worlds.
var _taken := ""


func _ready() -> void:
	layer = 20
	_rows = _build_rows()
	# START ON SOMETHING THE PLAYER CAN ACTUALLY PRESS. A cursor parked on a
	# disabled NEW GAME, on a build with no world, is a menu that looks broken
	# rather than one that explains itself.
	index = _first_enabled()
	_face = Face.new()
	_face.m = self
	_face.name = "MenuFace"
	_face.set_anchors_preset(Control.PRESET_FULL_RECT)
	_face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_face)
	# The mouse is released here and captured again by `player.gd` when the
	# world comes up. A title screen with a hidden pointer cannot be clicked.
	if DisplayServer.get_name() != "headless":
		Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	print("menu: title screen -- %d entries, %d playable%s"
		% [_rows.size(), _enabled_count(),
			("" if world_ok else "  -- NO WORLD: " + world_why)])
	for r in _rows:
		print("menu:   %-14s %-34s %s"
			% [r["id"], r["label"],
				("ready" if r["enabled"] else "unavailable -- " + r["why"])])


## The entries, and every one of them carries the reason it cannot run.
##
## THE ORDER IS THE DESIGN'S ORDER, not a habit. `docs/THE-GAME.md` §1: *"you
## are nobody ... the only thing standing between you and being put back on a
## transport is a card that says who you are"*. So the first entry is the moment
## the card is issued -- arriving at customs -- and the free-walk entry that
## every developer in this project has been using for eight sessions is
## SECOND and labelled as what it is. Shipping the developer's entry point as
## the player's would be shipping the tool as the game, which is exactly what
## `project.godot` did until session 4g.
func _build_rows() -> Array:
	var no_world := "" if world_ok else world_why
	return [
		{"id": "new_game", "mode": "arrival",
			"label": "NEW GAME",
			"blurb": "Arrive at Babylon 5. Present your card at customs.",
			"enabled": world_ok, "why": no_world},
		{"id": "continue_game", "mode": "continue",
			"label": "CONTINUE",
			"blurb": save_why if save_ok else "No saved station.",
			"enabled": world_ok and save_ok,
			"why": (no_world if not world_ok else save_why)},
		{"id": "station", "mode": "station",
			"label": "WALK THE STATION",
			"blurb": "Skip arrival. Stand in the corridor with a card already issued.",
			"enabled": world_ok, "why": no_world},
		{"id": "quit", "mode": "",
			"label": "QUIT",
			"blurb": "",
			"enabled": true, "why": ""},
	]


func items() -> Array:
	return _rows.duplicate(true)


func enabled_ids() -> Array:
	var out := []
	for r in _rows:
		if r["enabled"]:
			out.append(r["id"])
	return out


func taken() -> String:
	return _taken


func _enabled_count() -> int:
	return enabled_ids().size()


func _first_enabled() -> int:
	for i in _rows.size():
		if _rows[i]["enabled"]:
			return i
	return 0


## Move the cursor by `d`, skipping entries that cannot run. Wraps.
func move(d: int) -> void:
	if _rows.is_empty():
		return
	var i := index
	for _n in _rows.size():
		i = wrapi(i + d, 0, _rows.size())
		if _rows[i]["enabled"]:
			index = i
			return


## Move the cursor onto a named entry. Returns false if there is no such entry
## or it cannot run -- which is what makes `--menu-gate`'s negative control
## possible: with no world on disk, `select("new_game")` is FALSE.
func select(id: String) -> bool:
	for i in _rows.size():
		if _rows[i]["id"] == id:
			if not _rows[i]["enabled"]:
				return false
			index = i
			return true
	return false


## Press the current entry. Returns the id it fired, or "" if it refused.
func activate() -> String:
	if _taken != "":
		return ""
	if index < 0 or index >= _rows.size():
		return ""
	var r: Dictionary = _rows[index]
	if not r["enabled"]:
		print("menu: %s is unavailable -- %s" % [r["id"], r["why"]])
		return ""
	_taken = String(r["id"])
	print("menu: chose %s -> mode=%s" % [_taken, String(r["mode"])])
	if _taken == "quit":
		get_tree().quit(0)
		return _taken
	chosen.emit(_taken)
	return _taken


func mode_of(id: String) -> String:
	for r in _rows:
		if r["id"] == id:
			return String(r["mode"])
	return ""


## Keyboard only, and deliberately so. `player.gd` owns mouse look and captures
## the pointer; a menu that also wanted the mouse would be fighting it over who
## has the cursor at the one frame the world comes up.
func _unhandled_input(e: InputEvent) -> void:
	if _taken != "":
		return
	if not (e is InputEventKey) or not e.pressed or e.echo:
		return
	var k := (e as InputEventKey).keycode
	if k == KEY_DOWN or k == KEY_S:
		move(1)
	elif k == KEY_UP or k == KEY_W:
		move(-1)
	elif k == KEY_ENTER or k == KEY_KP_ENTER or k == KEY_SPACE:
		activate()
	elif k == KEY_ESCAPE:
		if select("quit"):
			activate()


## Drawn in one function, for the reason in this file's header.
class Face extends Control:
	var m                                       ## the menu that owns it

	# Declared here rather than on the outer script for `arrival.gd::Face`'s
	# reason: an inner class is its own scope, and these are exactly that file's
	# values so the title screen and the identicard read as one object.
	const CYAN := Color(0.494, 0.812, 0.882)
	const AMBER := Color(1.0, 0.702, 0.290)
	const RED := Color(0.86, 0.24, 0.18)
	const DIM := Color(0.42, 0.47, 0.52)
	const INK := Color(0.016, 0.031, 0.047)
	## Era lock, from CLAUDE.md's opening section. Stated on the title so a
	## player knows which Babylon 5 this is before being asked to care about a
	## card.
	const ERA := "SEASON 2-3"
	## The station's own length, from `canon/00-MASTER.md`. On the title because
	## it is the one number this project is actually about.
	const LENGTH_M := 8047

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		var fnt := ThemeDB.fallback_font
		var w := size.x
		var h := size.y
		draw_rect(Rect2(0, 0, w, h), INK)

		# THE TITLE BLOCK. Two hairlines and small capitals: the station's own
		# signage vocabulary, which `interior_kit` and `hud.gd` already use.
		var top := h * 0.20
		draw_line(Vector2(w * 0.10, top - 30), Vector2(w * 0.90, top - 30),
			CYAN, 1.0)
		draw_string(fnt, Vector2(w * 0.10, top + 22), "BABYLON 5",
			HORIZONTAL_ALIGNMENT_LEFT, w, 54, Color(0.90, 0.93, 0.96))
		draw_string(fnt, Vector2(w * 0.10, top + 50),
			"EARTH ALLIANCE DIPLOMATIC STATION  ·  %d M  ·  %s"
				% [LENGTH_M, ERA],
			HORIZONTAL_ALIGNMENT_LEFT, w, 15, CYAN)
		draw_line(Vector2(w * 0.10, top + 66), Vector2(w * 0.90, top + 66),
			Color(CYAN.r, CYAN.g, CYAN.b, 0.35), 1.0)

		# THE ENTRIES.
		var y := h * 0.44
		for i in m._rows.size():
			var r: Dictionary = m._rows[i]
			var on: bool = r["enabled"]
			var here: bool = (i == m.index)
			var col: Color = (AMBER if here else Color(0.80, 0.84, 0.88))
			if not on:
				col = DIM
			if here:
				draw_rect(Rect2(w * 0.085, y - 20, w * 0.83, 30),
					Color(AMBER.r, AMBER.g, AMBER.b, 0.10))
				draw_string(fnt, Vector2(w * 0.10 - 22, y), ">",
					HORIZONTAL_ALIGNMENT_LEFT, 40, 22, AMBER)
			draw_string(fnt, Vector2(w * 0.10, y), String(r["label"]),
				HORIZONTAL_ALIGNMENT_LEFT, w * 0.4, 24, col)
			var note: String = (String(r["blurb"]) if on
				else "UNAVAILABLE -- " + String(r["why"]))
			draw_string(fnt, Vector2(w * 0.10 + 300, y), note,
				HORIZONTAL_ALIGNMENT_LEFT, w * 0.5, 14,
				(Color(0.62, 0.66, 0.70) if on else RED))
			y += 44

		# THE FOOTER. What the keys are, and -- when there is no world -- the one
		# command that builds one, spelled out where a person can read it.
		draw_line(Vector2(w * 0.10, h - 78), Vector2(w * 0.90, h - 78),
			Color(CYAN.r, CYAN.g, CYAN.b, 0.35), 1.0)
		draw_string(fnt, Vector2(w * 0.10, h - 54),
			"UP / DOWN  select      ENTER  confirm      ESC  quit",
			HORIZONTAL_ALIGNMENT_LEFT, w, 14, CYAN)
		if not m.world_ok:
			draw_string(fnt, Vector2(w * 0.10, h - 30),
				"NO WORLD ON DISK: " + m.world_why,
				HORIZONTAL_ALIGNMENT_LEFT, w * 0.85, 14, RED)
