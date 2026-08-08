extends "res://scripts/walk.gd"

# The cluster-prefix rule lives in interact.gd and is preloaded rather than
# copied, so the two files cannot drift about what a group name is. Copying it
# would be the "two sources of truth" defect this project already records for
# materials and for column placement.
const Interact = preload("res://scripts/interact.gd")
## THE PLAYER'S FIRST TEN MINUTES, PLAYED.
##
## Spawn in the corridor outside customs, walk into the hall, present your
## identicard at the reader, get a verdict off the nine-field record the show's
## own prop carries, and walk out through the arrival concourse toward the room
## the station has assigned you.
##
## IT EXTENDS walk.gd RATHER THAN COPYING IT, and that is the whole reason this
## file is 300 lines instead of 1,100. `walk.gd` already loads a deck glb, gives
## it a smooth collision shell, dresses it from `interior.tscn`'s material rules
## and measured fittings, wires the doors, instances the crowd, binds the
## interactables sidecar and stands a `player.gd` body on the floor. A second
## copy of that would be a second description of how this station becomes a
## build -- the exact defect CLAUDE.md records three times over. What is HERE is
## only what is new: a sequence, a place to be next, and a line of text.
##
## THE SEQUENCE IS NOT IN THIS FILE. `station/arrival.py --emit` writes it, and
## every fact in it comes from a Python module that can be gated without an
## engine: the ship from `traffic.arrivals`, the bay from the schema's bay
## count, the hall from `directory`'s own angles, the card from
## `npc/resident.identicard`, the verbs from `interact.verb_of`, the quarters
## from `resident.home_for`. This file reads that JSON and drives a body at it.
## A hard-coded intro script in GDScript would be the fourth vocabulary.
##
## WAYPOINTS ARE MEASURED, NEVER WRITTEN DOWN. A step names a PLACE and an
## OBJECT; where they are is read off the loaded mesh -- the object from the
## interactables sidecar's measured box, the room from the union of every mesh
## whose name begins `<place>__`. Hard rule 4 again: the same rule that makes
## `collision.py` ray-cast the corridor profile instead of restating it.
##
## OFF-BUILD STEPS ARE REPORTED, NOT SKIPPED SILENTLY. `arrival.py` records
## which z-cluster each step's place assembles into, and the bays sit at z=7120
## while the halls sit at z=7440 -- two clusters, one deck. So the first two
## steps of the sequence cannot be walked in a build that holds the halls. This
## file counts them and says so on its verdict line. A runtime that quietly
## dropped them would make an eleven-step sequence look complete at six.
##
## HEADLESS BY DESIGN, like everything else here. `--arrival-test` drives the
## body with no window, no keyboard and no GPU, and prints one `ARRIVAL ...`
## line. The negative controls are `--no-interact` (nothing to present the card
## to, so the run must NOT reach admitted) and `--no-doors` (the hall is sealed,
## so the body must not get in).

## The sequence, as written by `station/arrival.py --emit`.
@export var arrival_path: String = ""
## How close counts as "you are there", in metres. 2.4 m is `interact.gd`'s own
## reach (INV-232) and is used for an OBJECT; a room is bigger and gets its own.
const REACH_M := 2.4
const ROOM_ARRIVE_M := 3.0
## Physics frames to settle the body before the sequence starts. walk.gd's own
## shot path uses 120; a body that has not landed cannot walk.
@export var settle_frames: int = 120
## Frames allowed per step before the run gives up on it and moves on. At 60 Hz
## and 4.2 m/s a body covers 70 m in 1000 frames, which is more than the length
## of this cluster's corridor.
@export var step_budget: int = 600

var seq: Dictionary = {}
var plan: Array = []            ## the steps this build can actually play
var offbuild: Array = []        ## the ones it cannot, and why
var step_i := 0
var _settled := 0
var _frames_here := 0
var _in_room_frames := 0
var _done := false
var _testing_arrival := false
var _card: CanvasLayer
var _used_reader := false
var _arr_path_m := 0.0
var _arr_off_floor := 0
var _prev := Vector3.ZERO
var _reached: Array[String] = []
var _timeouts: Array[String] = []
var _trace_every := 0
var _stuck := 0
var _slide_frames := 0
var _slide_sign := 1.0
var _slides := 0
var _min_d := 1e30
var _closest: Array[String] = []


func _ready() -> void:
	# THE SIDECAR IS READ FIRST, AND IT CARRIES THE WORLD. `arrival.py --build`
	# writes the mesh, the collision shell, the interactables and the sequence
	# together and records all four paths plus a spawn point a body can stand
	# on. So `--arrival=<json>` is a complete launch and the other flags are
	# overrides. The first run of this scene was given `--spawn=0,0,0`, which on
	# a ring deck at radius 210 m is the SPIN AXIS: the body fell for two
	# minutes and the run died on a timeout that read exactly like a slow load.
	var args := _args()
	if args.has("arrival"):
		arrival_path = args["arrival"]
	if not _load_sequence():
		push_error("arrival: no sequence at %s -- run "
			% arrival_path + "`python3 station/arrival.py --build`")
		get_tree().quit(2)
		return
	_adopt_build()

	# walk.gd does all of the loading, dressing, collision, doors, crowd and
	# HUD, and its own args still win over anything adopted above.
	super._ready()
	_load_boxes()
	_build_plan()
	print("arrival: %s -- %s aboard %s, bay %s, %s area %s"
		% [seq.get("name", "?"), seq.get("species", "?"),
			seq.get("ship", "?"), seq.get("bay_label", "?"),
			seq.get("hall", "?"), str(int(seq.get("area", 0)))])
	print("arrival: %s" % seq.get("announcement", ""))
	print("arrival: %d of %d steps are on this build; %d are on another "
		% [plan.size(), _steps().size(), offbuild.size()]
		+ "cluster or have no mesh here (%s)" % _why_off())
	if not args.has("arrival-test"):
		_make_card()
	_testing_arrival = args.has("arrival-test")
	_trace_every = int(args.get("arrival-trace", "0"))
	if args.has("arrival-steps"):
		# Diagnosis is 600 frames a step at about 7 physics frames a second on
		# this box, so a six-step run is a quarter of an hour. Capping the plan
		# is what makes "why is it stuck on step 1" a two-minute question.
		plan = plan.slice(0, int(args["arrival-steps"]))
	for i in plan.size():
		var rr: Dictionary = plan[i]
		print("arrival: step %d %s -> %s in %s  room %.1f,%.1f,%.1f  "
			% [i, String(rr["step"].get("id", "?")), String(rr["group"]),
				String(rr["step"].get("place", "")),
				rr["room"].x, rr["room"].y, rr["room"].z]
			+ "obj %.1f,%.1f,%.1f" % [rr["target"].x, rr["target"].y,
				rr["target"].z])
	set_physics_process(true)


func _load_sequence() -> bool:
	if arrival_path == "":
		# Beside the deck mesh, which is where `arrival.py --build` puts it.
		var stem := glb_path.get_basename()
		if stem != "":
			arrival_path = stem + "_arrival.json"
	if arrival_path == "" or not FileAccess.file_exists(arrival_path):
		return false
	var f := FileAccess.open(arrival_path, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return false
	seq = d
	return seq.has("steps")


## Take the build the sidecar names, unless the command line named one.
func _adopt_build() -> void:
	var b = seq.get("build", {})
	if typeof(b) != TYPE_DICTIONARY:
		return
	var args := _args()
	if not args.has("glb"):
		glb_path = String(b.get("glb", glb_path))
	if not args.has("collision"):
		collision_path = String(b.get("collision", collision_path))
	if not args.has("interact"):
		interact_path = String(b.get("interact", interact_path))
	if not args.has("actors"):
		actors_path = String(b.get("actors", actors_path))
	if not args.has("gravity-mode"):
		# A ring deck spins, so "down" is radial. Getting this wrong is the
		# sign error player.gd's `gravity_dir` documents: the body falls to
		# the axis and hangs there.
		gravity_mode = "drum"
	if not args.has("spawn"):
		var sp = b.get("spawn")
		if typeof(sp) == TYPE_ARRAY and sp.size() == 3:
			spawn = Vector3(float(sp[0]), float(sp[1]), float(sp[2]))


func _steps() -> Array:
	var s = seq.get("steps", [])
	return s if typeof(s) == TYPE_ARRAY else []


## Which steps this build can play, and where each one IS.
##
## A step is playable when the world can answer "where do I stand for it". Two
## answers are accepted and they are not equivalent: the OBJECT'S own measured
## box (from the interactables sidecar, which `interact.gd` has already turned
## into `Item`s), or failing that the ROOM's mesh extent. The object is the
## better target -- it is what the player walks up to and presses -- so it is
## tried first, and the plan records which one it got.
## A STEP IS TWO LEGS, NOT ONE, and the first version had only the second.
##
## It steered straight at the object from wherever the body was, which from the
## corridor means straight at the customs hall's WALL: the run walked 13.2 m,
## jammed, and reached none of its six steps in 5,400 frames. `walkable.py`'s
## `--goto` gets away with a single leg because it aims at a room CENTRE, which
## on this deck is on the far side of the room's own door and therefore on a
## line the door is on. An identicard reader standing against a side wall is
## not.
##
## So a step has a room leg and an object leg. The body walks to the room's own
## measured centre first -- through the door, because that is where the door is
## -- and only then at the thing it has come to use. A step whose object is
## already in the room the body is standing in skips the first leg.
func _build_plan() -> void:
	for st in _steps():
		var place := String(st.get("place", ""))
		var room := _place_centre(place)
		if is_inf(room.y):
			offbuild.append({"step": st, "why": "no mesh in this build"})
			continue
		var row := {"step": st, "room": room, "target": room, "kind": "room",
			"group": ""}
		var g := _group_of(st)
		if g != "":
			row["group"] = g
			row["target"] = _group_point(g)
			row["kind"] = "object"
		plan.append(row)


func _why_off() -> String:
	var out := PackedStringArray()
	for o in offbuild:
		out.append("%s:%s" % [String(o["step"].get("id", "?")),
			String(o["why"])])
	return ", ".join(out)


## The world point of an interactable, FROM THE BOX THE GENERATOR MEASURED.
##
## Read out of the same sidecar `interact.gd` binds, not re-measured here.
## `walkable.group_aabb` measured the object off its triangle SPAN while the
## spans were still intact; by the time the glb exists a machine's `_mp_` parts
## have claimed its triangles and the mesh still carrying the name is the
## leftovers -- `prop_bay_door` keeps twelve faces of sixteen hundred. Taking an
## AABB again in this file would walk the player to the leftovers.
var _boxes := {}                ## group -> measured centre
var _by_token := {}             ## "place|token" -> group


## THE STEP NAMES A PLACE AND A TOKEN; THE SIDECAR SAYS WHICH MESH THAT IS.
##
## The first version composed the group name -- `<place>__prop_<token>` -- and
## it found the reader and MISSED the desk, because `interact.resolve`'s alias
## rule had bound `customs_desk` to `customs_north__customs_desk`: the module
## that builds the hall names its own furniture and does not prefix it `prop_`.
## That is the same 26-of-98 misnaming `interact.py`'s own audit decomposed, and
## the fix is the same one: ask the resolution layer, do not re-derive it. The
## composed name is kept only as a fallback so a sidecar-less build still runs.
func _load_boxes() -> void:
	if interact_path == "" or not FileAccess.file_exists(interact_path):
		return
	var f := FileAccess.open(interact_path, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	if typeof(rows) != TYPE_ARRAY:
		return
	for r in rows:
		var g := String(r.get("group", ""))
		var c = r.get("centre")
		if typeof(c) == TYPE_ARRAY and c.size() == 3:
			_boxes[g] = Vector3(float(c[0]), float(c[1]), float(c[2]))
		_by_token["%s|%s" % [String(r.get("place", "")),
			String(r.get("token", ""))]] = g


## Which mesh group serves this step, or "" if this build does not have it.
func _group_of(st: Dictionary) -> String:
	var k := "%s|%s" % [String(st.get("place", "")), String(st.get("token", ""))]
	if _by_token.has(k):
		return String(_by_token[k])
	var g := String(st.get("group", ""))
	if _interact != null and g != "" and _interact.has_group(g):
		return g
	return ""


func _group_point(g: String) -> Vector3:
	if _boxes.has(g):
		return _boxes[g]
	return _place_centre(g.get_slice("__", 0))


## The centre of every mesh a place emitted, in world metres.
##
## `deck.build_deck` prefixes a room's groups with `<place>__`, which is the same
## convention `interact.gd` and `hud.gd` read. So a place's extent is derivable
## from the build with no table of coordinates anywhere.
func _place_centre(place: String) -> Vector3:
	if place == "":
		return Vector3(0, INF, 0)
	var lo := Vector3(INF, INF, INF)
	var hi := Vector3(-INF, -INF, -INF)
	var n := 0
	for m in _all_meshes(self):
		# THE CLUSTER PREFIX, WHICH THIS TEST DID NOT KNOW ABOUT. A multi-z deck
		# names its groups `z7440__customs_north__prop_...` (station/deck.py:1419,
		# added in 9db2466); `place + "__"` is false for every node on such a
		# deck, so this returned 0 meshes for all eleven steps and the build
		# printed `arrival: 0 of 11 steps are on this build`. Berth, disembark,
		# queue, present, scan, desk, welcome, orient, transit, door, bunk --
		# the entire authored opening, skipped silently, on a station whose
		# geometry contained every one of them.
		if not Interact.strip_cluster(String(m.name)).begins_with(place + "__"):
			continue
		var box: AABB = m.global_transform * m.get_aabb()
		lo = Vector3(minf(lo.x, box.position.x), minf(lo.y, box.position.y),
			minf(lo.z, box.position.z))
		hi = Vector3(maxf(hi.x, box.end.x), maxf(hi.y, box.end.y),
			maxf(hi.z, box.end.z))
		n += 1
	if n == 0:
		return Vector3(0, INF, 0)
	return (lo + hi) * 0.5


## A TARGET ON THE FLOOR, AND ON A SPUN RING THAT IS A RADIUS, NOT A HEIGHT.
##
## `walkable.room_target` records why this matters and it cost that gate a
## number: aiming at a room's mid-height leaves an irreducible offset in "how
## close did it get", because a body standing on the deck can never close a
## radial one -- it reads as a near miss and is nothing of the kind. Here it was
## worse than a near miss. The customs hall's AABB centre is 3.6 m above its own
## floor, i.e. 3.6 m INBOARD of the deck on a barrel whose down is radial, so a
## 3.0 m arrival radius could never be satisfied and every step timed out while
## the body stood in the right place.
##
## The floor radius is the BODY'S OWN, measured after it settles, not a number
## from the schema. It is standing on the floor; that is what its radius is for.
func _floor_project(v: Vector3, r: float) -> Vector3:
	var xy := Vector2(v.x, v.y)
	if xy.length() < 0.001:
		return v
	xy = xy.normalized() * r
	return Vector3(xy.x, xy.y, v.z)


func _floor_r() -> float:
	var p: Vector3 = _player.global_position
	return sqrt(p.x * p.x + p.y * p.y)


# ---------------------------------------------------------------------------
# Driving it
# ---------------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	# walk.gd's SHOT phase settles the body itself and takes the picture from
	# where it lands. Stepping it a second time here would move the camera
	# between the settle and the grab, which is the sort of thing that produces
	# a frame nobody can reproduce.
	if _shooting or _done or plan.is_empty() or _player == null:
		return
	if _settled < settle_frames:
		_settled += 1
		_player.step(delta, Vector2.ZERO, false, false)
		if _settled == settle_frames:
			_prev = _player.global_position
		return

	var row: Dictionary = plan[step_i]
	var st: Dictionary = row["step"]
	var p: Vector3 = _player.global_position
	var r := _floor_r()

	# LEG 1: get into the room. LEG 2: get to the thing. See `_build_plan`.
	var room: Vector3 = _floor_project(row["room"], r)
	var obj: Vector3 = _floor_project(row["target"], r)
	var in_room: bool = p.distance_to(room) <= ROOM_ARRIVE_M
	if in_room:
		_in_room_frames += 1
	var target: Vector3 = obj if (in_room or _in_room_frames > 0) else room

	# A HUMAN AT A KEYBOARD DRIVES THE BODY; THE TEST DRIVES IT ITSELF. Both go
	# through the same `step()` and the same `use()`, so there is no second path
	# that can diverge from the one a player takes -- walk.gd's own rule for its
	# `_try_use`.
	#
	# AND IT SIDESTEPS, BECAUSE A STRAIGHT LINE IS NOT A ROUTE. The trace that
	# made this necessary is worth keeping: the body walked 7.1 m into the
	# customs hall, met `is_on_wall=true` with `|v|=0.00` at z=7457.35, and
	# stood there for the remaining 480 frames -- it was not lost and it was not
	# outside, it had walked into the hall's own bollards. `walkable.py --goto`
	# never meets this because it aims at a room's CENTRE down the line its door
	# is on; the moment the target is a reader against a side wall, furniture is
	# in the way. This is a bug-algorithm heuristic and NOT a navmesh: when the
	# body stops making ground it strafes 70 degrees off the bearing for three
	# quarters of a second, alternating side. It gets round a bollard. It would
	# not get round a maze, and when the player track needs one the answer is a
	# navmesh rather than a bigger angle here.
	if _testing_arrival:
		var dir := target - p
		if _slide_frames > 0:
			dir = dir.rotated(_player.body_up(), deg_to_rad(70.0 * _slide_sign))
			_slide_frames -= 1
		_player.step(delta, Vector2.ZERO, false, false, dir)
		var moved := _player.global_position.distance_to(_prev)
		_arr_path_m += moved
		_prev = _player.global_position
		if not _player.is_on_floor():
			_arr_off_floor += 1
		if moved < 0.01 and _slide_frames <= 0:
			_stuck += 1
			if _stuck > 20:
				_slide_sign = -_slide_sign
				_slide_frames = 45
				_stuck = 0
				_slides += 1
		else:
			_stuck = 0
	_frames_here += 1

	# HOW FAR THE OBJECT IS, AS `interact.gd` MEASURES IT. Its `range_to` is
	# eye-to-object-centre against the box it bound, which is the same number
	# that decides whether the prompt appears; a second distance computed here
	# could say "in reach" while the prompt said otherwise.
	var near: float = p.distance_to(obj)
	if _interact != null and String(row["group"]) != "":
		var d: float = _interact.range_to(String(row["group"]))
		if d >= 0.0:
			near = d
	var want: float = REACH_M if String(row["kind"]) == "object" else ROOM_ARRIVE_M
	var arrived := near <= want
	# CLOSEST APPROACH, PER STEP. A step that fails has to say HOW it failed, and
	# "never got there" and "got to 0.3 m and the prompt did not fire" are
	# different defects with different owners. This is the number that told the
	# difference: every step of this sequence stops between 28 and 34 m out,
	# which is not a prompt problem, it is a floor problem.
	if near < _min_d:
		_min_d = near

	# THE STEP THAT IS THE POINT OF THE WHOLE SEQUENCE. When the prompt names
	# the reader, press it -- the same `use()` an `InputEventKey` calls.
	if arrived and bool(st.get("pressable", false)) and _interact != null:
		var g := String(row["group"])
		_interact.refresh()
		if String(_interact.prompt_group()) == g:
			if _interact.use() and String(st.get("id", "")) == "present":
				_used_reader = true

	# WHY A BODY IS NOT MOVING, IN THE TERMS THAT CAN ANSWER IT. walk.gd's own
	# `_trace_line` records the reason this exists: a run that only prints
	# `moved=0.001` says a body is stuck and nothing about what stopped it, and
	# three sessions of this project were spent guessing at exactly that.
	if _trace_every > 0 and _frames_here % _trace_every == 0:
		var hit := ""
		for i in _player.get_slide_collision_count():
			var c := _player.get_slide_collision(i)
			var o = c.get_collider()
			hit += " hit[%s d=%.3f]" % [("?" if o == null else str(o.name)),
				c.get_depth()]
		print("ATRACE step=%d(%s) f=%d leg=%s p=%.2f,%.2f,%.2f r=%.2f "
			% [step_i, String(st.get("id", "?")), _frames_here,
				("obj" if target == obj else "room"), p.x, p.y, p.z, r]
			+ "d_room=%.2f d_obj=%.2f |v|=%.2f floor=%s wall=%s slides=%d%s"
			% [p.distance_to(room), near, _player.velocity.length(),
				str(_player.is_on_floor()).to_lower(),
				str(_player.is_on_wall()).to_lower(), _slides, hit])

	if arrived or _frames_here > step_budget:
		_closest.append("%s:%.1fm" % [String(st.get("id", "?")), _min_d])
		if arrived:
			_reached.append(String(st.get("id", "?")))
		else:
			_timeouts.append(String(st.get("id", "?")))
		_advance()


func _advance() -> void:
	step_i += 1
	_frames_here = 0
	_in_room_frames = 0
	_min_d = 1e30
	if step_i < plan.size():
		return
	_done = true
	_verdict()
	if _testing_arrival:
		get_tree().quit(0)


## One line, and every number on it is a claim a player would notice.
##
## `steps` is how much of the sequence this build could play at all, `reached`
## how much the body actually walked to, `reader` whether the identicard went
## into the reader that decides the outcome, and `offfloor` whether it stayed on
## the deck getting there. `outcome` is what the station decided about this
## person -- the thing the whole first ten minutes is for.
func _verdict() -> void:
	print(("ARRIVAL who=%s species=%s ship=%s bay=%s hall=%s area=%s "
		+ "entry=%s outcome=%s quarters=%s unit=%s "
		+ "steps=%d/%d reached=%d timeout=%d offbuild=%d "
		+ "reader_used=%s path_m=%.2f offfloor=%d sidesteps=%d "
		+ "interactables=%d") % [
		String(seq.get("name", "-")).replace(" ", "_"),
		seq.get("species", "-"), String(seq.get("ship", "-")).replace(" ", "_"),
		seq.get("bay_label", "-"), seq.get("hall", "-"),
		str(int(seq.get("area", 0))), seq.get("entry_class", "-"),
		seq.get("status", "-"),
		seq.get("destination", {}).get("place", "-"),
		String(seq.get("unit", "-")) if String(seq.get("unit", "")) != "" else "-",
		plan.size(), _steps().size(), _reached.size(), _timeouts.size(),
		offbuild.size(), str(_used_reader).to_lower(), _arr_path_m,
		_arr_off_floor, _slides,
		(0 if _interact == null else _interact.count())])
	print("arrival: closest approach per step -- %s" % ", ".join(_closest))
	if not _timeouts.is_empty():
		print("arrival: never reached %s" % ", ".join(_timeouts))


# ---------------------------------------------------------------------------
# What the player sees
# ---------------------------------------------------------------------------
## THE INTERFACE IS THE HUD'S PROMPT PLUS ONE LINE OF TEXT, and that is a
## deliberate floor rather than a stub. `hud.gd` already draws the prompt --
## "OPERATE identicard reader" -- when the object is in reach, and walk.gd wires
## it. What is missing is only WHY you are walking there, so this adds the step's
## own sentence at the top of the frame and the nine-field record underneath it
## once the reader has been used. No dialogue system, no menus: the sequence is
## a walk, and the words are the announcement the station makes over it.
func _make_card() -> void:
	_card = CanvasLayer.new()
	_card.name = "ArrivalCard"
	_card.layer = 9
	var f := Face.new()
	f.a = self
	f.name = "ArrivalFace"
	f.set_anchors_preset(Control.PRESET_FULL_RECT)
	f.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.add_child(f)
	add_child(_card)


func current_text() -> String:
	if _done:
		return String(seq.get("verdict", ""))
	if step_i < plan.size():
		return String(plan[step_i]["step"].get("text", ""))
	return ""


func card_lines() -> Array:
	## The nine fields, in the prop's order, with the prop's two states. Emitted
	## by `resident.identicard()`; not re-ordered here.
	if not _used_reader:
		return []
	var out := []
	for r in seq.get("identicard", []):
		out.append([String(r.get("label", "")), String(r.get("value", "")),
			String(r.get("state", ""))])
	return out


## Drawn rather than assembled from Control nodes, for `hud.gd`'s stated reason:
## the whole look is small capitals and hairlines, a StyleBox cannot express it
## without a texture, and this project has a standing rule against binary
## resources. It also keeps the entire appearance in one reviewable function.
class Face extends Control:
	var a                                       ## the arrival node that owns it
	const CYAN := Color(0.494, 0.812, 0.882)
	const AMBER := Color(1.0, 0.702, 0.290)
	const RED := Color(0.86, 0.24, 0.18)
	const INK := Color(0.016, 0.031, 0.047)

	func _process(_d: float) -> void:
		queue_redraw()

	func _draw() -> void:
		var fnt := ThemeDB.fallback_font
		var w := size.x
		var txt: String = a.current_text()
		if txt != "":
			var bar := Rect2(0, 24, w, 34)
			draw_rect(bar, Color(INK.r, INK.g, INK.b, 0.62))
			draw_line(Vector2(0, 24), Vector2(w, 24), CYAN, 1.0)
			draw_string(fnt, Vector2(28, 48), txt,
				HORIZONTAL_ALIGNMENT_LEFT, w - 56, 17, AMBER)
		# The record, once the card has gone through the reader. The prop
		# renders a field with no entry in RED with no colon, and a filled one
		# as a label, a colon and a value -- `resident.identicard` emits that
		# state per field and it is honoured here rather than approximated.
		var rows: Array = a.card_lines()
		if rows.is_empty():
			return
		var x := 28.0
		var y := 96.0
		draw_rect(Rect2(x - 12, y - 22, 340, rows.size() * 20 + 34),
			Color(INK.r, INK.g, INK.b, 0.74))
		draw_string(fnt, Vector2(x, y - 6), "IDENTICARD",
			HORIZONTAL_ALIGNMENT_LEFT, 320, 13, CYAN)
		y += 18
		for r in rows:
			var label: String = r[0]
			var value: String = r[1]
			var empty: bool = r[2] == "empty"
			draw_string(fnt, Vector2(x, y), label + ("" if empty else ":"),
				HORIZONTAL_ALIGNMENT_LEFT, 150, 13,
				RED if empty else Color(0.85, 0.87, 0.9))
			if not empty:
				draw_string(fnt, Vector2(x + 130, y), value,
					HORIZONTAL_ALIGNMENT_LEFT, 200, 13, CYAN)
			y += 20
