extends Node3D
## Someone talks back.
##
## WHAT THIS EXISTS TO END. `station/interact.py` names eight verbs and then
## excludes three of them from `RESPONDS`, and its comment says why: *"being
## served needs whoever is behind the counter to turn round and TALK, WHICH
## NEEDS DIALOGUE."* There was none. `npc.gd` turns 2,028 heads towards the
## player and that was the entire consequence of every name, job, home,
## schedule, costume and identicard the generator builds.
##
## NOT ONE WORD OF IT IS DECIDED HERE. `station/dialogue.py` derives the whole
## exchange -- who says what, in which register, about which of today's events
## -- from `npc/resident.py`, `npc/schedule.py`, `npc/friction.py`,
## `npc/security.py`, `traffic.py`, `broadcast.py` and `npc/costume.py`'s era
## lock, and writes it beside the deck mesh as `<deck>_dialogue.json`. This file
## reads that sidecar and holds no line, no topic rule and no register table.
## It is `interact.gd`'s relationship to `interact.py`, for the same reason:
## a second copy of a decision is the defect this repository has paid for three
## times.
##
## THE PROMPT KEY IS `T` AND NOT `E`. `interact.gd` owns `E` and scans props;
## this scans PEOPLE. Two systems on one key would make "use the console" and
## "talk to the clerk" race each other in front of a manned counter, which is
## precisely where both are true at once.
##
## THE LOOK IS HUD.GD'S, AND IT IS LOADED RATHER THAN COPIED. The palette, the
## fade and the tracked-capitals treatment are read off `scripts/hud.gd`'s own
## constants at runtime, so the interface stays one design. A second set of
## colour literals in this file would drift the first time the HUD was retuned.

## How close you have to be for a conversation to be offered. Nearer than
## `npc.gd`'s `notice_m` of 6.0 on purpose: being noticed across a room and
## being close enough to speak are different distances, and the person turning
## their head at 6 m is what tells you the nearer prompt is coming.
@export var talk_m: float = 3.0
## Half-angle of the "am I looking at them" cone, in degrees. Wider than
## `interact.gd`'s 35 deg because a person is a metre wide and a wall panel is
## not, and because you can address someone you are not staring straight at.
@export var look_half_deg: float = 45.0
## How long the panel takes to arrive and to leave, in seconds. Read off
## `hud.gd::FADE_S` so the two surfaces move together.
var fade_s: float = 0.10

const HUD_SCRIPT := "res://scripts/hud.gd"

# The palette, LOADED. See the header: these are `hud.gd`'s own constants,
# sampled from `reference/03-sector-blue/comand and contorl.webp`.
var CYAN := Color(0.494, 0.812, 0.882)
var AMBER := Color(1.0, 0.702, 0.290)
var INK := Color(0.016, 0.031, 0.047)
var _palette_from := "fallback literals"


## The three keys that take a stance. `station/dialogue.STANCES`' order, and
## the panel numbers them in the same order -- a menu whose numbering disagrees
## with the model is a menu that mispresses under the player's fingers.
const PICK_KEYS := [KEY_1, KEY_2, KEY_3]


## One version of a person: what they say at ONE hour of the station's day.
##
## `station/dialogue.py::speak` is a function of `world.hour` and the sidecar
## bakes it at `SIDECAR_HOURS`. A Person below holds every variant and switches
## between them as `life.gd`'s Clock turns, which is why this is a class and
## not four loose fields.
class Take:
	var hour: float = 13.0
	var topic: String = ""
	var band: String = ""
	var doing: String = ""         # what they return to at THIS hour
	var lines: Array = []          # [{who, kind, text}]
	var choices: Array = []        # [{stance, text, yielded, reply:[...]}]
	var choice_at: int = -1


class Person:
	var group: String = ""
	var id: String = ""
	var name: String = ""
	var species: String = ""
	var role: String = ""
	var place: String = ""
	## What they were doing when the deck was baked -- `populace`'s own
	## `who.doing` field, off the cast list rather than out of this file. It is
	## what "they go back to what they were doing" is quoting.
	var doing: String = ""
	var takes: Array = []          # [Take], one per baked hour
	var at_hour: int = 0           # which of them the clock has selected
	var pos := Vector3.ZERO
	var talked: int = 0

	func take() -> Take:
		return takes[clampi(at_hour, 0, takes.size() - 1)]

	var topic: String:
		get: return take().topic
	var band: String:
		get: return take().band
	var lines: Array:
		get: return take().lines
	var choices: Array:
		get: return take().choices
	var choice_at: int:
		get: return take().choice_at

	## Pick the take nearest `h` ON THE CLOCK RING. Nearest and not
	## interpolated: an averaged person is a person nobody is, and the 21:00
	## midpoint between a 19:00 and a 03:00 take belongs to one of them.
	func select(h: float) -> bool:
		var best := 0
		var best_d := INF
		for i in takes.size():
			var d: float = absf(fposmod(takes[i].hour - h + 12.0, 24.0) - 12.0)
			if d < best_d:
				best_d = d
				best = i
		if best == at_hour:
			return false
		at_hour = best
		return true


var _people: Array[Person] = []
var _player: Node3D
var _cam: Camera3D
var _near: Person = null           # who the prompt is offering
var _open: Person = null           # who you are actually talking to
var _at: int = -1                  # which of their lines is showing
var _panel: CanvasLayer = null
var _face = null
var _hot: float = 0.0
var _spoken: int = 0               # lines a player has actually been shown
var _opened: int = 0
var _last_report := ""


# ===========================================================================
#  Binding
# ===========================================================================

## Wire the derived exchanges to the bodies they belong to.
##
## TWO SIDECARS, JOINED ON `group`, AND NEITHER IS A SECOND POPULATION.
## `<deck>_actors.json` is what `populace.py` baked and where each body stands;
## `<deck>_dialogue.json` is what `station/dialogue.py` derived for those same
## rows. The join key is the mesh group, which is the only name both files and
## the .glb agree on.
## AND ONE PERSON PER GROUP, NOT ONE PER ROW. `station/dialogue.write_sidecar`
## bakes `SIDECAR_HOURS` takes of every body, so the file holds four rows for
## each of them. Keying the join on `group` alone -- which is what this did
## while the sidecar was single-hour -- would stand four copies of the same
## resident in the same square metre and offer the player whichever the scan
## reached first.
func collect(actors: Array, rows: Array) -> int:
	var where := {}
	var doing := {}
	for a in actors:
		if typeof(a) != TYPE_DICTIONARY:
			continue
		var g := String(a.get("group", ""))
		if g == "":
			continue
		where[g] = Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0)))
		var who = a.get("who", {})
		if typeof(who) == TYPE_DICTIONARY:
			doing[g] = String(who.get("doing", ""))
	var by_group := {}
	var unplaced := 0
	for r in rows:
		if typeof(r) != TYPE_DICTIONARY:
			continue
		var g2 := String(r.get("group", ""))
		if not where.has(g2):
			unplaced += 1
			continue
		var t := Take.new()
		t.hour = float(r.get("hour", 13.0))
		t.topic = String(r.get("topic", ""))
		t.band = String(r.get("band", ""))
		t.doing = String(r.get("doing", ""))
		var ls = r.get("lines", [])
		if typeof(ls) == TYPE_ARRAY:
			t.lines = ls
		# `choices` and `choice_at` are ADDITIVE: a sidecar baked before player
		# utterances existed has neither, and reads here as a conversation with
		# nothing to say back -- exactly what it was.
		var cs = r.get("choices", [])
		if typeof(cs) == TYPE_ARRAY:
			t.choices = cs
		t.choice_at = int(r.get("choice_at", -1))
		# A PERSON WITH NO LINES IS NOT A PERSON YOU CAN TALK TO, and saying so
		# here is better than offering a prompt that opens an empty panel --
		# the failure that looks like success.
		if t.lines.is_empty():
			continue
		if not by_group.has(g2):
			var p := Person.new()
			p.group = g2
			p.id = String(r.get("id", ""))
			p.name = String(r.get("name", ""))
			p.species = String(r.get("species", ""))
			p.role = String(r.get("role", ""))
			p.place = String(r.get("place", ""))
			p.doing = String(doing.get(g2, ""))
			p.pos = where[g2]
			by_group[g2] = p
			_people.append(p)
		(by_group[g2] as Person).takes.append(t)
	for g3 in by_group:
		var pp: Person = by_group[g3]
		pp.takes.sort_custom(func(a, b): return a.hour < b.hour)
	if unplaced > 0:
		print("dialogue: %d exchange(s) name a group with no body in the cast "
			% unplaced + "list -- the two sidecars were built from different "
			+ "populations")
	if not _people.is_empty():
		var hrs := []
		for t2 in (_people[0] as Person).takes:
			hrs.append("%05.2f" % t2.hour)
		print("dialogue: %d people, %d rows, baked at %s"
			% [_people.size(), rows.size(), ", ".join(hrs)])
	return _people.size()


# ===========================================================================
#  The clock
# ===========================================================================
# WHY THIS FILE LOOKS FOR THE CLOCK INSTEAD OF BEING HANDED IT. `walk.gd`
# builds this node and has no clock; `main.gd` builds the Clock and hands it to
# `life.gd`'s Director. Threading it through would mean editing both, and both
# are load-bearing files this session does not own. The Director is a named
# node in the tree with an `hour()` accessor, so one guarded search finds it
# and a build that has no Director keeps the take it booted with -- which is
# the old behaviour exactly.

var _director: Node = null
var _looked := false
var _hour: float = -1.0


func _find_director() -> Node:
	if _looked:
		return _director
	_looked = true
	var scene := get_tree().current_scene if get_tree() != null else null
	for root in [scene, get_parent()]:
		if root == null:
			continue
		var n := _search(root, 0)
		if n != null:
			_director = n
			print("dialogue: following the station clock at %s"
				% _director.get_path())
			return _director
	print("dialogue: no Life director in the tree -- the cast keeps the hour "
		+ "it was baked at")
	return null


## Depth-limited, and BY CAPABILITY rather than by name: a node that answers
## `hour()` is the clock whatever it is called, and a node called "Life" that
## does not is not.
func _search(node: Node, depth: int) -> Node:
	if depth > 4:
		return null
	if node.has_method("hour") and node != self:
		return node
	for c in node.get_children():
		var got := _search(c, depth + 1)
		if got != null:
			return got
	return null


## Move the whole cast to the hour the station is at. Returns how many people
## changed what they would say.
func set_hour(h: float) -> int:
	_hour = h
	var moved := 0
	for p in _people:
		if p != _open and p.select(h):
			moved += 1
	return moved


func hour() -> float:
	return _hour


func watch(body: Node3D) -> void:
	_player = body
	if _player != null:
		_cam = _player.get_node_or_null("Camera3D") as Camera3D
	_load_palette()
	_build_panel()


func _load_palette() -> void:
	var s = load(HUD_SCRIPT)
	if s == null:
		push_warning("dialogue: could not load %s -- the panel is drawing on "
			% HUD_SCRIPT + "its own colour literals, which can drift from the "
			+ "HUD")
		return
	CYAN = s.CYAN
	AMBER = s.AMBER
	INK = s.INK
	fade_s = float(s.FADE_S)
	_palette_from = HUD_SCRIPT


# ===========================================================================
#  Who you are looking at
# ===========================================================================

## The nearest person inside reach and inside the cone, by ANGLE then distance.
##
## THE SAME TEST `interact.gd` USES, and deliberately so: a player should not
## have to learn two aiming rules. The one difference is the line-of-sight ray,
## which is cast only when there is a physics world to cast it in -- the
## headless harness at the bottom of this file has bodies and no level, and a
## test that silently required a bulkhead to be present would be measuring the
## level rather than this file.
func scan() -> Person:
	if _player == null:
		return null
	var eye: Vector3 = _player.global_position
	var fwd := -_player.global_transform.basis.z
	if _cam != null:
		eye = _cam.global_position
		fwd = -_cam.global_transform.basis.z
	if fwd.length_squared() < 1e-9:
		return null
	fwd = fwd.normalized()
	var cos_lim := cos(deg_to_rad(look_half_deg))
	var best: Person = null
	var best_cos := -2.0
	var best_d := INF
	for p in _people:
		# AT THE HEAD, NOT AT THE FEET. `populace` records where a body STANDS,
		# and a standing eye at 1.70 m looking level passes 1.70 m over an
		# ankle: measured against the foot position, a person two metres in
		# front of you is 40 degrees below the view axis and outside any
		# sensible cone.
		var at: Vector3 = p.pos + _up_at(p.pos) * 1.55
		var to: Vector3 = at - eye
		var d: float = to.length()
		if d > talk_m or d < 1e-4:
			continue
		var c: float = to.normalized().dot(fwd)
		if c < cos_lim:
			continue
		if c < best_cos - 0.001 or (absf(c - best_cos) <= 0.001 and d >= best_d):
			continue
		best = p
		best_cos = c
		best_d = d
	return best


## Which way is up where somebody is standing. INWARD on a spun ring -- the
## floor is the outer wall -- so it is a different direction at every angle.
## `npc.gd` derives it the same way from the same position.
func _up_at(at: Vector3) -> Vector3:
	var radial := Vector3(at.x, at.y, 0.0)
	if radial.length() < 0.001:
		return Vector3.UP
	return -radial.normalized()


var _scanned_frame: int = -1


## Re-take the look-at test, at most once per physics frame. Frame-guarded and
## callable from outside for `interact.gd::refresh()`'s reason: this node is a
## sibling of the player's driver and whichever runs first, the other would
## otherwise read a state computed before the body moved.
func refresh() -> Person:
	var f := Engine.get_physics_frames()
	if f == _scanned_frame:
		return _near
	_scanned_frame = f
	# WHILE A CONVERSATION IS OPEN THE SCAN IS FROZEN. Turning your head
	# mid-sentence must not hand the conversation to the person behind you.
	if _open != null:
		_near = _open
		return _near
	_near = scan()
	return _near


# ===========================================================================
#  Talking
# ===========================================================================

## THE LIVE CONVERSATION. `_run` is the take's lines with the player's chosen
## utterance and its answer SPLICED IN, so the pointer below walks one array
## rather than switching between two. `Take.lines` is never mutated: the take
## is baked data and a conversation that edited it would make the second
## conversation with the same person a different one.
var _run: Array = []
var _run_max: int = 0              # how long it grew to, kept past close()
var _menu := false                 # sitting at the choice point, nothing picked
var _picked := ""                  # which stance, once one has been
var _said: int = 0                 # player utterances actually spoken
var _pressed_new: int = 0          # ...that were a press which yielded


## Open a conversation, or advance the one that is open. Returns true if
## anything happened.
##
## THE KEYPRESS AND THE HEADLESS TEST CALL THIS, not two paths that can
## diverge, which is the rule `interact.gd::use()` states and this file
## inherits.
##
## AND IT WILL NOT WALK PAST AN UNANSWERED QUESTION. At the choice point `T`
## does nothing and `say()` is the only way on. A `more` key that also meant
## "take the first option" would make the menu decorative -- the player would
## never learn that the three stances differ, because the fastest way through
## would never show them.
func talk() -> bool:
	if _open == null:
		var p := refresh()
		if p == null:
			return false
		_open = p
		_run = p.lines.duplicate()
		_run_max = _run.size()
		_at = 0
		_menu = false
		_picked = ""
		_opened += 1
		p.talked += 1
		_spoken += 1
		print("TALK open %s id=%s species=%s role=%s place=%s topic=%s band=%s "
			% [p.group, p.id, p.species, p.role, p.place, p.topic, p.band]
			+ "hour=%05.2f lines=%d choices=%d"
			% [p.take().hour, _run.size(), p.choices.size()])
		print("TALK line 1/%d %s" % [_run.size(), _line_text(0)])
		_arm_menu()
		return true
	if _menu:
		return false
	_at += 1
	if _at >= _run.size():
		close()
		return true
	_spoken += 1
	print("TALK line %d/%d %s" % [_at + 1, _run.size(), _line_text(_at)])
	_arm_menu()
	return true


## Offer the menu when the pointer reaches the line the choices answer.
func _arm_menu() -> void:
	if _open == null or _picked != "":
		return
	if _open.choices.is_empty() or _at != _open.choice_at:
		return
	_menu = true
	var opts := []
	for i in _open.choices.size():
		opts.append("%d) %s" % [i + 1, String(_open.choices[i].get("text", ""))])
	print("TALK you may say -- " + "  |  ".join(opts))


## Say one of them. This is the whole of what was missing: a 2,139-line module
## with ZERO player utterances, and the owner named it.
func say(i: int) -> bool:
	if _open == null or not _menu:
		return false
	if i < 0 or i >= _open.choices.size():
		return false
	var c: Dictionary = _open.choices[i]
	var stance := String(c.get("stance", ""))
	var mine := {"who": "you", "kind": "speech",
		"text": String(c.get("text", ""))}
	var add: Array = [mine]
	var reply = c.get("reply", [])
	if typeof(reply) == TYPE_ARRAY:
		for r in reply:
			add.append(r)
	# Splice, never append: the farewell that follows the topic is still owed,
	# and a stance that dropped it would end the conversation on the player's
	# own voice.
	for j in add.size():
		_run.insert(_at + 1 + j, add[j])
	_run_max = _run.size()
	_menu = false
	_picked = stance
	_said += 1
	if stance == "press" and bool(c.get("yielded", false)):
		_pressed_new += 1
	print("TALK stance=%s yielded=%s" % [stance,
		str(bool(c.get("yielded", false)))])
	_at += 1
	_spoken += 1
	print("TALK line %d/%d %s" % [_at + 1, _run.size(), _line_text(_at)])
	return true


func close() -> void:
	if _open != null:
		# THEY GO BACK TO WHAT THEY WERE DOING, and what that is comes off
		# `populace`'s own `who.doing` field rather than out of this file.
		print("TALK close %s after %d line(s), stance=%s -- back to %s"
			% [_open.group, _run.size(),
				(_picked if _picked != "" else "-"),
				_back_to(_open)])
	_open = null
	_at = -1
	_menu = false
	_run = []


## THE TAKE'S HOUR FIRST. `Person.doing` is `<deck>_actors.json`'s `who.doing`,
## which `populace` baked at ONE hour; the take carries the same call asked at
## the hour the player is actually standing in. Falling back to the actor row
## keeps a pre-`doing` sidecar reading exactly as it did.
func _back_to(p: Person) -> String:
	var d := p.take().doing
	if d == "":
		d = p.doing
	return (d if d != "" else "their day")


func _line_text(i: int) -> String:
	if _open == null and _near == null:
		return ""
	var src: Array = (_run if _open != null else _near.lines)
	if i < 0 or i >= src.size():
		return ""
	var ln: Dictionary = src[i]
	var kind := String(ln.get("kind", "speech"))
	var who := String(ln.get("who", "npc"))
	var txt := String(ln.get("text", ""))
	# AN ACTION IS A STAGE DIRECTION AND IT IS NOT ALWAYS THEIRS. FACTIONS.md
	# 12's rows are symmetric and written from the human side -- "a human
	# talking with aliens lowers his voice when an armband passes" describes
	# the PLAYER. `station/dialogue.py` records which side in `who`; both are
	# rendered as a description of the moment rather than as a voice, because
	# neither of them said anything.
	if kind == "action":
		return "(%s%s)" % [("" if who == "npc" else "> "), txt]
	return "%s\"%s\"" % [("> " if who == "you" else ""), txt]


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_T:
			talk()
		elif event.keycode == KEY_ESCAPE and _open != null:
			close()
		elif _menu:
			var i := PICK_KEYS.find(event.keycode)
			if i >= 0:
				say(i)


func _physics_process(delta: float) -> void:
	# THE CLOCK FIRST, so a body that walks up at 03:00 is offered the 03:00
	# conversation rather than the one the deck was baked with.
	var dir := _find_director()
	if dir != null:
		var h: float = float(dir.call("hour"))
		if h >= 0.0 and absf(h - _hour) > 0.001:
			set_hour(h)
	refresh()
	_hot = move_toward(_hot, (1.0 if (_near != null or _open != null) else 0.0),
		delta / maxf(fade_s, 0.001))
	if _face != null:
		_face.queue_redraw()
	var line := report()
	if line != _last_report:
		_last_report = line
		print("dialogue: %s" % line)


## One line for the log, printed on change. What a shot run says was on screen
## when the shutter opened.
func report() -> String:
	if _open != null:
		if _menu:
			return "%s is waiting for an answer (%d option(s), topic=%s)" % [
				_open.name, _open.choices.size(), _open.topic]
		return "talking to %s (%s/%s) line %d/%d topic=%s stance=%s" % [
			_open.name, _open.species, _open.role, _at + 1,
			_run.size(), _open.topic, (_picked if _picked != "" else "-")]
	if _near != null:
		return "prompt=talk/%s %.2fm topic=%s" % [_near.name,
			_player.global_position.distance_to(_near.pos), _near.topic]
	return "prompt=-"


# -- what the headless test reads -------------------------------------------

func count() -> int:
	return _people.size()


## Is a conversation on screen? Read by `hud.gd` so the `[E]` prompt stands
## down while somebody is talking to you.
func is_open() -> bool:
	return _open != null


func opened() -> int:
	return _opened


func lines_shown() -> int:
	return _spoken


func prompt_name() -> String:
	return (_near.name if _near != null else "")


func palette_source() -> String:
	return _palette_from


func nearest_m() -> float:
	if _player == null or _people.is_empty():
		return -1.0
	var best := INF
	for p in _people:
		best = minf(best, _player.global_position.distance_to(p.pos))
	return best


## Every distinct line of speech across the whole cast. THE ONE MEASUREMENT
## THIS FILE CAN MAKE THAT THE GENERATOR CANNOT: whether the deck a player
## walks in actually says many things, after the join, the placement and the
## group matching have all had their chance to collapse it.
func distinct_lines() -> int:
	var seen := {}
	for p in _people:
		for ln in p.lines:
			if String(ln.get("kind", "speech")) == "speech":
				seen[String(ln.get("text", ""))] = true
	return seen.size()


func total_lines() -> int:
	var n := 0
	for p in _people:
		n += p.lines.size()
	return n


## How many player utterances the whole deck offers, and how many DISTINCT
## ones. The DLG-05 denominator, measured after the join rather than at the
## generator -- which is the one measurement this file can make that
## `station/dialogue.py` cannot.
func offers() -> int:
	var n := 0
	for p in _people:
		if not p.choices.is_empty():
			n += 1
	return n


func distinct_says() -> int:
	var seen := {}
	for p in _people:
		for t in p.takes:
			for c in t.choices:
				seen[String(c.get("text", ""))] = true
	return seen.size()


func said() -> int:
	return _said


func pressed_yield() -> int:
	return _pressed_new


func picked() -> String:
	return _picked


## How many of the cast say something different at `a` than at `b`. The
## 03:00-against-13:00 question, asked of the RUNTIME's own take selection
## rather than of the generator that baked it.
func hour_moves(a: float, b: float) -> int:
	var n := 0
	for p in _people:
		var keep := p.at_hour
		p.select(a)
		var ta := _joined(p)
		p.select(b)
		if _joined(p) != ta:
			n += 1
		p.at_hour = keep
	return n


func _joined(p: Person) -> String:
	var out := ""
	for ln in p.lines:
		out += String(ln.get("text", "")) + "|"
	for c in p.choices:
		out += String(c.get("text", "")) + "|"
	return out


# ===========================================================================
#  THE PANEL
# ===========================================================================
# Drawn rather than assembled from Control nodes, for `hud.gd`'s stated reason:
# the whole interface is hairlines, ticks and small tracked capitals, none of
# which a StyleBox can express without a texture, and a texture is a binary
# resource this project has a standing rule against.

func _build_panel() -> void:
	if _args().has("no-dialogue-ui") or _args().has("walk-test"):
		return
	_panel = CanvasLayer.new()
	_panel.name = "DialogueUI"
	_panel.layer = 9
	add_child(_panel)
	_face = Plate.new()
	_face.d = self
	_face.name = "DialogueFace"
	_face.set_anchors_preset(Control.PRESET_FULL_RECT)
	_face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(_face)


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--"):
			var b := s.substr(2)
			var eq := b.find("=")
			if eq >= 0:
				out[b.substr(0, eq)] = b.substr(eq + 1)
			else:
				out[b] = "1"
	return out


## NOT CALLED `Panel`. That was the first name and it is a NATIVE GODOT CLASS,
## so the whole file failed to parse -- `Class "Panel" hides a native class` --
## and every call into it threw. It is the same defect CLAUDE.md records
## costing a session in `npc.gd`, and the headless harness at the bottom of
## this file caught it on its first run, which is the entire argument for the
## harness existing.
class Plate extends Control:
	var d                                  # the node that owns this face
	var _font: Font = ThemeDB.fallback_font

	func _draw() -> void:
		if d == null or _font == null:
			return
		var sz := size
		var s: float = maxf(sz.y / 720.0, 0.35)
		if d._backdrop != null:
			draw_texture_rect(d._backdrop, Rect2(Vector2.ZERO, sz), false)
		if d._open != null:
			_exchange(sz, s)
		elif d._near != null:
			_offer(sz, s)

	# -- primitives, the same three hud.gd draws with ----------------------

	func _hair(a: Vector2, b: Vector2, c: Color, s: float, w := 1.0) -> void:
		draw_line(a, b, c, maxf(1.0, roundf(w * s)), false)

	func _scrim(r: Rect2, a: float, fx: Vector2, fy := Vector2.ZERO) -> void:
		var xs := [r.position.x, r.position.x + r.size.x * fx.x,
			r.end.x - r.size.x * fx.y, r.end.x]
		var ys := [r.position.y, r.position.y + r.size.y * fy.x,
			r.end.y - r.size.y * fy.y, r.end.y]
		var ax := [(0.0 if fx.x > 0.0 else 1.0), 1.0, 1.0,
			(0.0 if fx.y > 0.0 else 1.0)]
		var ay := [(0.0 if fy.x > 0.0 else 1.0), 1.0, 1.0,
			(0.0 if fy.y > 0.0 else 1.0)]
		for i in 3:
			if xs[i + 1] - xs[i] < 0.5:
				continue
			for j in 3:
				if ys[j + 1] - ys[j] < 0.5:
					continue
				draw_polygon(PackedVector2Array([
						Vector2(xs[i], ys[j]), Vector2(xs[i + 1], ys[j]),
						Vector2(xs[i + 1], ys[j + 1]),
						Vector2(xs[i], ys[j + 1])]),
					PackedColorArray([
						Color(d.INK, a * ax[i] * ay[j]),
						Color(d.INK, a * ax[i + 1] * ay[j]),
						Color(d.INK, a * ax[i + 1] * ay[j + 1]),
						Color(d.INK, a * ax[i] * ay[j + 1])]))

	func _tracked(pos: Vector2, text: String, px: int, c: Color,
			track: float) -> float:
		var x := pos.x
		for i in text.length():
			var ch := text[i]
			draw_char(_font, Vector2(x, pos.y), ch, px, c)
			x += _font.get_char_size(ch.unicode_at(0), px).x + track
		return x - pos.x

	func _tracked_width(text: String, px: int, track: float) -> float:
		var w := 0.0
		for i in text.length():
			w += _font.get_char_size(text[i].unicode_at(0), px).x + track
		return maxf(w - track, 0.0)

	func _bracket(at: Vector2, dx: float, dy: float, c: Color,
			s: float) -> void:
		_hair(at, at + Vector2(dx, 0), c, s)
		_hair(at, at + Vector2(0, dy), c, s)

	## The key glyph: a square outline with a letter in it. Square, because
	## there is not a rounded corner anywhere in Command and Control.
	func _key(at: Vector2, letter: String, s: float, a: float) -> float:
		var k := 24.0 * s
		var kr := Rect2(at.x, at.y - k * 0.5, k, k)
		draw_rect(kr, Color(d.INK, 0.60 * a), true)
		draw_rect(kr, Color(d.AMBER, 0.85 * a), false, maxf(1.0, roundf(s)))
		var kpx := int(roundf(13.0 * s))
		var kw := _font.get_char_size(letter.unicode_at(0), kpx).x
		draw_char(_font, Vector2(kr.position.x + (k - kw) * 0.5,
			at.y + kpx * 0.36), letter, kpx, Color(d.AMBER, 0.95 * a))
		return k

	# -- the offer ---------------------------------------------------------

	## `[T] TALK TO ...`, in the HUD prompt's own place and idiom, one line
	## below where `interact.gd`'s prompt sits so both can be true at a manned
	## counter without overlapping.
	func _offer(sz: Vector2, s: float) -> void:
		var a: float = d._hot
		if a <= 0.01:
			return
		var p = d._near
		var cx := sz.x * 0.5
		var y: float = sz.y * 0.5 + 148.0 * s + (1.0 - a) * 8.0 * s
		var px := int(roundf(15.0 * s))
		var who: String = (p.name if p.name != "" else p.species).to_upper()
		var verb := "TALK TO"
		var vw := _tracked_width(verb, px, 2.6 * s)
		var lw := _tracked_width(who, px, 2.6 * s)
		var pad := 15.0 * s
		var key := 24.0 * s
		var total: float = key + pad + vw + pad + 1.0 + pad + lw
		var x := cx - total * 0.5
		_scrim(Rect2(x - 60.0 * s, y - 30.0 * s, total + 120.0 * s, 74.0 * s),
			0.62 * a, Vector2(0.28, 0.28), Vector2(0.28, 0.30))
		_key(Vector2(x, y), "T", s, a)
		var tx := x + key + pad
		_tracked(Vector2(tx, y + px * 0.36), verb, px,
			Color(d.AMBER, 0.95 * a), 2.6 * s)
		tx += vw + pad
		_hair(Vector2(tx, y - 8.0 * s), Vector2(tx, y + 8.0 * s),
			Color(d.CYAN, 0.35 * a), s)
		tx += pad
		_tracked(Vector2(tx, y + px * 0.36), who, px, Color(d.CYAN, 0.92 * a),
			2.6 * s)
		# Who they are, under it, small. The species and the job are what the
		# generator knows about them and the player cannot read off a face.
		var sub := "%s   %s" % [p.species.to_upper(), p.role.to_upper()]
		var spx := int(roundf(9.0 * s))
		var sw := _tracked_width(sub, spx, 1.2 * s)
		_tracked(Vector2(cx - sw * 0.5, y + 30.0 * s), sub, spx,
			Color(d.CYAN, 0.55 * a), 1.2 * s)

	# -- the conversation --------------------------------------------------

	func _exchange(sz: Vector2, s: float) -> void:
		var a: float = d._hot
		var p = d._open
		var w: float = minf(sz.x * 0.78, 980.0 * s)
		var x := (sz.x - w) * 0.5
		var h := 104.0 * s
		var y := sz.y - h - 76.0 * s
		# TWO WASHES, NOT ONE. A single soft plate at the alpha `hud.gd` uses
		# for a corner readout disappeared against a lit corridor wall -- the
		# first frame of this had amber text floating on bare geometry. The
		# wide one seats the block in the frame; the tight one under the line
		# itself is what makes the text legible against a wall with a light
		# fitting on it.
		_scrim(Rect2(x - 56.0 * s, y - 40.0 * s, w + 112.0 * s, h + 92.0 * s),
			0.66 * a, Vector2(0.16, 0.16), Vector2(0.24, 0.22))
		_scrim(Rect2(x - 22.0 * s, y - 16.0 * s, w + 44.0 * s, h + 34.0 * s),
			0.52 * a, Vector2(0.10, 0.10), Vector2(0.14, 0.14))

		# The speaker. Tracked capitals in cyan, with the L-bracket every B5
		# console panel is edged with.
		var npx := int(roundf(17.0 * s))
		var who: String = (p.name if p.name != "" else p.species).to_upper()
		_bracket(Vector2(x - 12.0 * s, y - 16.0 * s), 16.0 * s, 20.0 * s,
			Color(d.CYAN, 0.70 * a), s)
		var nw := _tracked(Vector2(x, y), who, npx, Color(d.CYAN, 0.98 * a),
			3.0 * s)
		var sub := "%s   %s   %s" % [p.species.to_upper(), p.role.to_upper(),
			p.place.replace("_", " ").to_upper()]
		var spx := int(roundf(10.0 * s))
		_tracked(Vector2(x + nw + 20.0 * s, y - 1.0 * s), sub, spx,
			Color(d.CYAN, 0.80 * a), 1.4 * s)
		_hair(Vector2(x, y + 9.0 * s), Vector2(x + w, y + 9.0 * s),
			Color(d.CYAN, 0.40 * a), s)

		# The line. Speech in the warm console amber -- it is the thing being
		# said to you -- and an ACTION in cyan and parentheses, because a
		# stage direction is not a voice. `station/dialogue.py` marks the
		# difference; nothing here decides it.
		#
		# AND THE PLAYER'S OWN VOICE IS NEITHER. It is set in cyan and marked
		# with a leading rule, because the one thing a player must never have
		# to work out is which of the two people on screen just spoke.
		var run: Array = d._run
		var ln: Dictionary = ({} if d._at < 0 or d._at >= run.size()
			else run[d._at])
		var kind := String(ln.get("kind", "speech"))
		var mine := String(ln.get("who", "npc")) == "you"
		var txt := String(ln.get("text", ""))
		var speech := kind != "action"
		if not speech:
			txt = "( " + txt + " )"
		else:
			txt = "“" + txt + "”"
		var lpx := int(roundf(16.0 * s))
		var col: Color = (Color(d.AMBER, 0.96 * a) if speech
			else Color(d.CYAN, 0.72 * a))
		if speech and mine:
			col = Color(d.CYAN, 0.96 * a)
		var ly := y + 42.0 * s
		if speech and mine:
			_hair(Vector2(x - 12.0 * s, ly - 12.0 * s),
				Vector2(x - 12.0 * s, ly + 6.0 * s), Color(d.CYAN, 0.8 * a),
				s, 2.0)
		for row in _wrap(txt, w, lpx, 1.2 * s):
			_tracked(Vector2(x, ly), row, lpx, col, 1.2 * s)
			ly += 24.0 * s

		# THE MENU. Drawn ABOVE the plate rather than inside it, because the
		# line they just said has to stay on screen while you choose what to
		# answer -- a stance is an answer to a specific sentence and replacing
		# that sentence with a list is how a player ends up picking blind.
		if d._menu:
			_menu(sz, s, a, x, w, y)

		# Where you are in the exchange, and the key that moves it on.
		var ny := y + h + 6.0 * s
		var tick := "%d / %d" % [d._at + 1, run.size()]
		_tracked(Vector2(x, ny), tick, int(roundf(9.0 * s)),
			Color(d.CYAN, 0.55 * a), 1.4 * s)
		if d._menu:
			# No `[T] MORE` while a question is open: the key does nothing
			# there, and a prompt for a key that does nothing is a lie about
			# the controls.
			var wait := "CHOOSE"
			_tracked(Vector2(x + w - _tracked_width(wait,
				int(roundf(11.0 * s)), 1.6 * s), ny), wait,
				int(roundf(11.0 * s)), Color(d.AMBER, 0.88 * a), 1.6 * s)
			return
		var last: bool = d._at >= run.size() - 1
		var word := ("END" if last else "MORE")
		var kx := x + w - 24.0 * s - 12.0 * s \
			- _tracked_width(word, int(roundf(11.0 * s)), 1.6 * s)
		_key(Vector2(kx, ny - 4.0 * s), "T", s, a)
		_tracked(Vector2(kx + 24.0 * s + 12.0 * s, ny), word,
			int(roundf(11.0 * s)), Color(d.AMBER, 0.88 * a), 1.6 * s)

	## The stances, numbered, each with its own key glyph. One row each, cyan,
	## sitting on their own scrim above the speaker's plate.
	func _menu(sz: Vector2, s: float, a: float, x: float, w: float,
			plate_y: float) -> void:
		var cs: Array = d._open.choices
		var px := int(roundf(14.0 * s))
		var rowh := 30.0 * s
		var top := plate_y - 62.0 * s - rowh * cs.size()
		_scrim(Rect2(x - 40.0 * s, top - 30.0 * s, w + 80.0 * s,
			rowh * cs.size() + 52.0 * s), 0.66 * a,
			Vector2(0.14, 0.14), Vector2(0.26, 0.20))
		_tracked(Vector2(x, top - 12.0 * s), "YOU MAY SAY",
			int(roundf(9.0 * s)), Color(d.CYAN, 0.55 * a), 1.8 * s)
		for i in cs.size():
			var ry := top + rowh * i + rowh * 0.5
			_key(Vector2(x, ry), str(i + 1), s, a)
			var t := String(cs[i].get("text", ""))
			var rows := _wrap(t, w - 46.0 * s, px, 1.2 * s)
			_tracked(Vector2(x + 24.0 * s + 14.0 * s, ry + px * 0.36),
				String(rows[0] if rows.size() > 0 else t), px,
				Color(d.CYAN, 0.94 * a), 1.2 * s)

	## Break a line at word boundaries to fit `w` pixels. Measured with the
	## same tracking it is drawn with, or the last word runs off the plate.
	func _wrap(text: String, w: float, px: int, track: float) -> Array:
		var out := []
		var cur := ""
		for word in text.split(" "):
			var t: String = (word if cur == "" else cur + " " + word)
			if _tracked_width(t, px, track) > w and cur != "":
				out.append(cur)
				cur = word
			else:
				cur = t
		if cur != "":
			out.append(cur)
		return out


# ===========================================================================
#  THE HEADLESS HARNESS
# ===========================================================================
# WHY THERE IS ONE AT ALL. Every other runtime file in this project is driven
# by `walk.gd`, and `walk.gd` is not this session's to edit -- so without this,
# the only thing that could be said about this file is that it parses. The
# parse is worth checking (CLAUDE.md records a session lost to a GDScript parse
# error that took every call from `walk.gd` down with it), and it is nowhere
# near enough: a scan cone, a join on `group` and a line pointer are all things
# that can be wrong while the file compiles perfectly.
#
# So `--dialogue-test` builds the smallest world the feature needs -- the real
# actor positions, the real derived exchanges, a body and a camera -- walks the
# body in, and prints a verdict `station/dialogue.py --runtime-test` parses.
# There is no level in it and that is stated rather than hidden: this measures
# the conversation, not the corridor.

func _ready() -> void:
	var args := _args()
	if args.has("dialogue-shot"):
		_run_shot(args)
		return
	if not args.has("dialogue-test"):
		return
	_run_test(args)


# -- the frame ---------------------------------------------------------------
# WHAT THIS IS AND WHAT IT IS NOT, stated before the code because a frame that
# is described loosely is a frame that gets over-claimed -- this repository has
# a whole section in CLAUDE.md about a renderer that quietly substituted a
# lesser mode and manufactured a session of evidence.
#
# The panel below is drawn BY GODOT, by this file, through the same
# `CanvasItem` calls a player would see, at the shipped resolution, over a
# backdrop that is a real engine frame of the deck. It is a COMPOSITE: nothing
# in the shipped scene tree builds this node, because `godot/scripts/walk.gd`
# is not this session's file to edit, so the panel could not be in the deck
# render itself. It is evidence about the interface and about nothing else.
var _shot_out := ""
var _shot_frames := 0
var _backdrop: Texture2D = null


func _run_shot(args: Dictionary) -> void:
	var actors: Array = _read_array(String(args.get("actors", "")))
	var rows: Array = _read_array(String(args.get("dialogue", "")))
	collect(actors, rows)
	var body := Node3D.new()
	add_child(body)
	watch(body)
	var bd := String(args.get("backdrop", ""))
	if bd != "" and FileAccess.file_exists(bd):
		var img := Image.new()
		if img.load(bd) == OK:
			_backdrop = ImageTexture.create_from_image(img)
	# WHICH EXCHANGE. `--topic=` picks the first person whose derived topic is
	# that one, so the frame can show the officer's beat rather than whoever
	# happens to be first -- and if nothing matches, it says so instead of
	# quietly showing something else.
	var want := String(args.get("topic", ""))
	var who: Person = null
	for p in _people:
		if want == "" or p.topic == want:
			who = p
			break
	if who == null:
		print("dialogue: no exchange with topic=%s" % want)
		get_tree().quit(1)
		return
	_hot = 1.0
	if args.has("offer"):
		_near = who
	else:
		_open = who
		_run = who.lines.duplicate()
		_at = int(args.get("line", "1"))
		_at = clampi(_at, 0, _run.size() - 1)
		# `--menu` poses the choice point, which is the state a frame of the
		# OLD panel could not have been taken in because it did not exist.
		if args.has("menu"):
			_at = maxi(who.choice_at, 0)
			_menu = not who.choices.is_empty()
	print("dialogue: shot of %s (%s/%s) topic=%s line %d/%d%s"
		% [who.name, who.species, who.role, who.topic, _at + 1,
			_run.size(), (" at the menu" if _menu else "")])
	_shot_out = String(args.get("dialogue-shot", ""))
	# THE SHUTTER IS NOT THE SIMULATION. `_physics_process` re-runs the scan
	# every frame, and with no level and no body near anybody it correctly
	# returns nothing -- so an `--offer` shot came out as the backdrop with no
	# prompt on it, byte-identical to the file it was drawn over. The frame
	# poses the interface; the scan is proved by the harness above.
	set_physics_process(false)
	set_process(true)


func _process(_delta: float) -> void:
	if _shot_out == "":
		return
	if _face != null:
		_face.queue_redraw()
	_shot_frames += 1
	# A FEW FRAMES BEFORE THE SHUTTER. The first frame of a Godot window has no
	# drawn CanvasItems in it yet, and a blank PNG is exactly the artefact that
	# looks like a working tool.
	if _shot_frames < 6:
		return
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(_shot_out)
	print("dialogue: wrote %s (%dx%d)" % [_shot_out, img.get_width(),
		img.get_height()])
	_shot_out = ""
	get_tree().quit(0)


func _run_test(args: Dictionary) -> void:
	var actors: Array = _read_array(String(args.get("actors", "")))
	var rows: Array = _read_array(String(args.get("dialogue", "")))
	# THE CONTROL, and it is the same shape as `walk.gd`'s `--no-people`: with
	# the exchanges withheld, everything downstream must report zero. A test
	# that only ever runs the working configuration cannot tell a working scan
	# from one that offers a prompt for anybody who happens to be nearby.
	if args.has("no-dialogue"):
		rows = []
		print("dialogue: exchanges WITHHELD (negative control)")
	var n := collect(actors, rows)

	var body := Node3D.new()
	body.name = "TestBody"
	add_child(body)
	var cam := Camera3D.new()
	cam.name = "Camera3D"
	body.add_child(cam)
	# THE EYE IS 1.70 m UP THE BODY'S OWN UP, which on a spun ring points at
	# the axis. `player.gd` puts the camera there and `interact.gd` measures
	# its reach from it; a harness that measured from the feet would report
	# distances no player ever stands at.
	watch(body)

	if n == 0:
		print("DIALOGUETEST people=0 opened=0 lines=0 shown=0 distinct=0 "
			+ "prompt_m=-1.00 offers=0 says=0 said=0 hour_moves=0 takes=0 "
			+ "palette=%s" % palette_source())
		get_tree().quit(0)
		return

	# WALK IN ON THE MOST ISOLATED PERSON ON THE DECK, and the first version of
	# this took `_people[0]` instead. That looked like two failures of this
	# file -- a prompt at 12 m and a prompt with the body facing away -- and
	# was neither: the customs halls hold 73 people over a few metres, so the
	# approach path passed inside `talk_m` of somebody else the whole way. The
	# scan was right and the harness was measuring the crowd.
	#
	# So: pick the person furthest from their nearest neighbour, and measure
	# the range and cone tests against THAT PERSON while separately asserting
	# the invariant on whoever is offered -- which is the property that
	# actually matters and holds in a crowd.
	var target: Person = _most_isolated()
	var up := _up_at(target.pos)
	var toward := Vector3(0, 0, 1)
	if absf(toward.dot(up)) > 0.9:
		toward = Vector3(1, 0, 0)
	toward = (toward - up * toward.dot(up)).normalized()
	var head: Vector3 = target.pos + up * 1.55

	var first_m := -1.0
	var far_prompt := false
	var bad_range := 0
	var bad_cone := 0
	var d := 12.0
	while d > 0.4:
		body.global_position = target.pos + toward * d
		_aim(body, cam, up, head)
		_scanned_frame = -1
		var p := refresh()
		if p != null:
			# THE INVARIANT, on whoever was offered: inside the range and
			# inside the cone. This is what the scan promises, and it has to
			# hold in a crowd where the person offered is often not `target`.
			if not _within(p):
				bad_range += 1
			if not _in_cone(p):
				bad_cone += 1
		if p == target and first_m < 0.0:
			first_m = d
		if p == target and d > talk_m + 0.6:
			far_prompt = true
		d -= 0.25

	# And with the body facing the other way at touching distance, which is
	# the control on the CONE rather than on the range.
	# AWAY IS `+toward` AND NOT `-toward`. The body stands at `+1.2 * toward`
	# from them, so aiming at `target.pos - toward * 40` looks straight THROUGH
	# the person -- the first version of this control reported a prompt with
	# the body "facing away" and was aiming at them.
	body.global_position = target.pos + toward * 1.2
	_aim(body, cam, up, target.pos + toward * 40.0)
	_scanned_frame = -1
	var behind: bool = refresh() == target

	# THE CLOCK MOVES THE CAST, and it is asked before any conversation is
	# opened so the measurement is of the take selection and not of a
	# conversation that happens to be frozen open. `hour_moves` restores
	# everybody's take, so this is a read and not a state change.
	var moved := hour_moves(3.0, 13.0)
	var takes: int = (_people[0] as Person).takes.size()

	# Now stand in front of them and hold the conversation.
	_aim(body, cam, up, head)
	_scanned_frame = -1
	refresh()
	# ONE CONVERSATION, ALL THE WAY THROUGH. The loop exits when `talk()` has
	# run off the end and closed it -- not on a call count, because a bound
	# that happens to equal the line count cannot tell a working line pointer
	# from one that never advances.
	#
	# AND IT STOPS AT THE QUESTION, WHICH IS THE POINT OF THE QUESTION. `talk()`
	# returns false at the menu and this loop would spin there for ever, so the
	# STANCE is what moves it on. `--stance=` picks which one; the default is
	# `press`, because it is the only one that can be REFUSED and therefore the
	# only one whose outcome is not knowable from the sidecar alone.
	var want_stance := String(args.get("stance", "press"))
	var picked_i := -1
	var guard := 0
	var stalled := 0
	talk()
	while _open != null and guard < 96:
		_scanned_frame = -1
		if _menu:
			var opts: Array = _open.choices
			var k := 0
			for i in opts.size():
				if String(opts[i].get("stance", "")) == want_stance:
					k = i
			picked_i = k
			if not say(k):
				stalled += 1
				break
		elif not talk():
			stalled += 1
			break
		guard += 1
	# WHAT THE PLAYER ACTUALLY SAID, carried into the verdict verbatim. A count
	# of utterances can be right while the text is empty, and an empty string in
	# a panel is the failure that reads as success.
	var mine := ""
	if picked_i >= 0 and picked_i < target.choices.size():
		mine = String(target.choices[picked_i].get("text", ""))
	print("DIALOGUETEST people=%d opened=%d deck_lines=%d open_lines=%d "
		% [count(), opened(), total_lines(), target.lines.size()]
		+ "shown=%d distinct=%d prompt_m=%.2f far_prompt=%s behind=%s "
		% [lines_shown(), distinct_lines(), first_m, str(far_prompt),
			str(behind)]
		+ "bad_range=%d bad_cone=%d palette=%s topic=%s name=%s "
		% [bad_range, bad_cone, palette_source(), target.topic,
			target.name.replace(" ", "_")]
		+ "offers=%d says=%d said=%d stance=%s stalled=%d takes=%d "
		% [offers(), distinct_says(), said(), picked(), stalled, takes]
		+ "hour_moves=%d run_lines=%d you_said=%s"
		% [moved, _run_max, mine.replace(" ", "_")])
	get_tree().quit(0)


## Whoever is offered must be inside `talk_m` of the eye.
func _within(p: Person) -> bool:
	var eye: Vector3 = (_cam.global_position if _cam != null
		else _player.global_position)
	return eye.distance_to(p.pos + _up_at(p.pos) * 1.55) <= talk_m + 0.01


## ...and inside the cone.
func _in_cone(p: Person) -> bool:
	var eye: Vector3 = (_cam.global_position if _cam != null
		else _player.global_position)
	var fwd: Vector3 = (-_cam.global_transform.basis.z if _cam != null
		else -_player.global_transform.basis.z).normalized()
	var to: Vector3 = (p.pos + _up_at(p.pos) * 1.55) - eye
	if to.length() < 1e-4:
		return true
	return to.normalized().dot(fwd) >= cos(deg_to_rad(look_half_deg)) - 0.001


## The person furthest from their nearest neighbour. A walk-in test needs
## somebody you can approach without passing through a queue.
func _most_isolated() -> Person:
	var best: Person = _people[0]
	var best_gap := -1.0
	for p in _people:
		var gap := INF
		for q in _people:
			if q == p:
				continue
			gap = minf(gap, p.pos.distance_to(q.pos))
		if gap > best_gap:
			best_gap = gap
			best = p
	return best


## Point the body and its camera at `at`, upright in the ring's own frame.
func _aim(body: Node3D, cam: Camera3D, up: Vector3, at: Vector3) -> void:
	var fwd: Vector3 = at - body.global_position
	fwd = fwd - up * fwd.dot(up)
	if fwd.length() < 0.001:
		fwd = Vector3(0, 0, 1)
	fwd = fwd.normalized()
	var right: Vector3 = fwd.cross(up).normalized()
	body.global_transform = Transform3D(Basis(right, up, -fwd),
		body.global_position)
	cam.transform = Transform3D(Basis(), Vector3(0, 1.70, 0))


func _read_array(path: String) -> Array:
	if path == "" or not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open(path, FileAccess.READ)
	var v = JSON.parse_string(f.get_as_text())
	return (v if typeof(v) == TYPE_ARRAY else [])


# ===========================================================================
# WHAT A RELOAD HAS TO PUT BACK
#
# WHAT THE PLAYER HAS ALREADY BEEN TOLD, and that is the whole point of saving
# this subsystem rather than letting it reset. A station where every resident
# greets you as a stranger every session is a station with no memory of you,
# which is exactly the failure `docs/MASTER-PLAN.md` R7 names for the journal.
#
# THE OPEN CONVERSATION IS DELIBERATELY NOT SAVED. `_open`, `_near`, `_at`,
# `_run` and `_menu` are a live exchange with a person who is standing in front
# of you, and the body they belong to is respawned from the crowd library at
# load with no guarantee of being the same instance -- so restoring a pointer
# into a conversation would resume a dialogue with whoever now occupies that
# slot. A reload closes the conversation. That is a design decision and it is
# the honest one; resuming it needs the speaker to be addressable across a
# reload, which nothing here is yet.
#
# WHAT IS STILL MISSING, said out loud so silence is not read as completeness:
# these are COUNTERS. They restore how much has been said, not WHICH LINES to
# whom -- so a resident whose one-off line a player already heard can offer it
# again. Per-person line state needs a stable id for a crowd body, the same
# thing the open conversation needs, and it is the same piece of work.
# ===========================================================================

func save_state() -> Dictionary:
	return {
		"spoken": _spoken,
		"opened": _opened,
		"said": _said,
		"pressed_new": _pressed_new,
		"run_max": _run_max,
	}


func load_state(d: Dictionary) -> void:
	_spoken = int(d.get("spoken", _spoken))
	_opened = int(d.get("opened", _opened))
	_said = int(d.get("said", _said))
	_pressed_new = int(d.get("pressed_new", _pressed_new))
	_run_max = int(d.get("run_max", _run_max))
	# The live exchange is closed rather than restored -- see the note
	# above. `close()` already exists and prints who was dropped.
	close()
	_near = null
	_picked = ""
	if _panel != null:
		_panel.visible = false

