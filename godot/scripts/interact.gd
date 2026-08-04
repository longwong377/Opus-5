extends Node3D
## The things in the room are things you can USE.
##
## WHAT THIS EXISTS TO END. `station/directory.py` has given every one of the 128
## register places an `interacts` field since layer 1 -- the column headed *what
## a player can use in this room* -- and `STATE.md`'s open findings still said
## "Nothing is interactable except the door." Both were true: `interacts` had two
## readers, `rooms.lateral_stack` (how much WALL does this room need) and
## `rooms.build` (where do I stand a box), and neither of those is a player using
## anything. 357 declarations, 0 verbs.
##
## THE VERB IS NOT DECIDED HERE. `station/interact.py` derives it from
## `rooms.PROP_KIND` and the register's own head nouns, and writes a sidecar
## beside the deck mesh: `{group, place, token, verb, pressable, label}` per
## interactable. A second copy of those tables in GDScript is the defect this
## repository has paid for three times -- the door decision made in the render
## and again in the shell, the corridor profile written down instead of
## measured. This file reads the sidecar and holds no table of its own.
##
## HOW LOOKING AT SOMETHING IS DECIDED, and why it is not one ray down the
## centre of the screen. A `docking_clamp` is 0.90 m tall and a standing eye is
## at 1.70 m, so a horizontal ray passes clean over the top of it and a player
## standing on top of the thing would be told there is nothing there. So the
## test is the one a game actually uses: every interactable within `reach_m` and
## inside `look_half_deg` of the view axis, nearest by ANGLE, then confirmed by a
## line-of-sight ray so you cannot use a console through a wall.
##
## THE COLLIDERS ARE ON THEIR OWN LAYER AND THAT IS LOad-BEARING. `station/
## collision.py` sweeps a smooth shell at 1.5% of the render mesh's triangles
## because a capsule wedges on the corridor's 66 mm lighting channel; putting
## interact colliders on the walking layer would put per-object boxes straight
## back in the body's way. These sit on `INTERACT_LAYER` with mask 0, so nothing
## in the world collides with them and the player capsule (mask 1) cannot feel
## them at all. The walk is measured either way -- see `walkable.py --use`.

## How far a player can reach. An arm plus a step: you use what you are standing
## at, not what is across the room. INV-232.
@export var reach_m: float = 2.4
## Half-angle of the "am I looking at it" cone, in degrees. INV-232.
@export var look_half_deg: float = 35.0
## How far a pressed control travels, in metres, and for how many physics
## frames. A momentary control moves millimetres; this is the acknowledgement a
## player feels rather than an animation. INV-232.
@export var press_travel_m: float = 0.004
@export var press_frames: int = 12

## The physics layer the interact proxies live on. NOT layer 1: the player's
## capsule masks 1 and must never feel these boxes.
const INTERACT_LAYER := 2

# WHICH VERBS HAVE A RESPONSE IS NOT DECIDED HERE EITHER. `station/interact.py`
# carries `RESPONDS` and stamps `responds` on every sidecar row, because `sit`,
# `rest` and `serve` need a BODY to respond -- the player's own animation, or
# whoever is behind the counter turning round -- and neither exists. A list here
# would be a second copy of that judgement, free to drift the day one of them
# gets a rig.


class Item:
	var group: String = ""
	var place: String = ""
	var token: String = ""
	var verb: String = ""
	var label: String = ""
	var pressable: bool = false
	var responds: bool = false
	var parts: Array[MeshInstance3D] = []
	var rest: Array[Vector3] = []       # each part's untouched origin
	var centre := Vector3.ZERO
	var half := Vector3.ZERO            # world AABB half-extent
	var rest_centre := Vector3.ZERO     # part 0's untouched world AABB centre
	var push := Vector3.ZERO            # unit travel of a press
	var body: StaticBody3D = null
	var used: int = 0
	var press_left: int = 0
	var travel_m: float = 0.0           # how far it has ACTUALLY moved


var _items: Array[Item] = []
var _player: Node3D
var _cam: Camera3D
var _prompt: Item = null
var _last_used: Item = null
var _prompt_frames: int = 0
var _use_count: int = 0
var _hud: Label = null
var _doors: Node = null


## Wire the sidecar to the meshes it describes.
##
## A SIDECAR RATHER THAN A NAME TEST, for the reason `npc.gd` takes one: the
## engine can see that a mesh is called `docking_bays__prop_bay_door`, but only
## `station/interact.py` knows that `bay_door` is a declared interactable and
## that its verb is `open`. Asking the geometry to give back what the generator
## already knew is how the door leaves ended up 0.16 m out of their own frame.
func collect(visual: Node, rows: Array) -> int:
	var want := {}
	for row in rows:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		var g: String = String(row.get("group", ""))
		if g == "":
			continue
		want[g] = row
	# A PROP IS SEVERAL MESHES. `dressing.machine` emits an articulated object
	# as a parent group plus `_mp_`-infixed parts, and the OBJ writer gives each
	# triangle to the LAST group covering it -- the same finding `npc.gd`
	# records for a person's skin and cloth. So an exact name match can find the
	# parent group empty; the parts are matched too, and merged into one object.
	var found := {}
	for m in _meshes(visual):
		var n := String(m.name)
		var key := ""
		if want.has(n):
			key = n
		else:
			for g2 in want:
				var gs: String = String(g2)
				if n.begins_with(gs + "_"):
					key = gs
					break
		if key == "":
			continue
		if not found.has(key):
			found[key] = []
		found[key].append(m)

	for g3 in found:
		var key2: String = String(g3)
		var row2: Dictionary = want[key2]
		var parts: Array = found[key2]
		if parts.is_empty():
			continue
		var it := Item.new()
		it.group = key2
		it.place = String(row2.get("place", ""))
		it.token = String(row2.get("token", ""))
		it.verb = String(row2.get("verb", ""))
		it.label = String(row2.get("label", it.token))
		it.pressable = bool(row2.get("pressable", false))
		it.responds = bool(row2.get("responds", false))
		for p in parts:
			var mi: MeshInstance3D = p
			it.parts.append(mi)
			it.rest.append(mi.global_position)
		_measure(it)
		# THE BOX COMES FROM THE GENERATOR WHERE THE GENERATOR SENT ONE, and it
		# is not a duplicate of the measurement above -- it is the measurement
		# the engine CANNOT make. `dressing.machine` appends the object's outer
		# triangle span first and its `_mp_` part spans after, and both the OBJ
		# writer and `export_scene.per_triangle` resolve last-span-wins, so by
		# the time the glb exists `prop_bay_door` keeps only the 12 faces no
		# part claimed and the other 1,600 are in `prop_mp_plant_*` groups
		# shared with every machine in the room. The mesh that still carries the
		# name is the leftovers. `walkable.py::group_aabb` reads the spans while
		# they are still intact -- the same reason `_actors.json` carries a yaw.
		var c = row2.get("centre")
		var h = row2.get("half")
		if typeof(c) == TYPE_ARRAY and c.size() == 3 \
				and typeof(h) == TYPE_ARRAY and h.size() == 3:
			it.centre = Vector3(float(c[0]), float(c[1]), float(c[2]))
			it.half = Vector3(float(h[0]), float(h[1]), float(h[2]))
			_press_axis(it)
		var box0: AABB = it.parts[0].global_transform * it.parts[0].get_aabb()
		it.rest_centre = box0.get_center()
		_give_box(it)
		_items.append(it)
	# WHICH DECLARED INTERACTABLES HAVE NO MESH OF THEIR OWN, and it is not
	# zero. `dressing.machine` appends the object's outer span and then its
	# `_mp_` part spans, and `deck.write_obj` gives each triangle to the LAST
	# span covering it -- so a machine whose parts claim every one of its
	# triangles leaves its own name with no faces, and the glb has no mesh by
	# that name at all. The count is printed by `walk.gd` rather than swallowed,
	# because a sidecar row nothing binds to is an interactable a player can
	# never see.
	# RECOMPUTED AGAINST EVERYTHING LOADED SO FAR, not appended per call. This
	# used to append the rows this one call did not find, which was right while
	# `collect` ran once over the whole deck and becomes nonsense the moment
	# cells stream it: each cell would report every interactable in every OTHER
	# cell as missing, and the list would grow past the number of rows that
	# exist. The claim is "no loaded geometry provides this row", so it is a set
	# difference over the accumulated state rather than a running log.
	for g4 in want:
		_want[g4] = true
	var have := {}
	for it3 in _items:
		have[it3.group] = true
	_missing.clear()
	for g5 in _want:
		if not have.has(g5):
			_missing.append(String(g5))
	_missing.sort()
	return _items.size()


var _missing: Array[String] = []
## Every declared row seen by any `collect` call, so `_missing` can be a set
## difference rather than a running log. See the note in `collect`.
var _want: Dictionary = {}


## The object's world box, measured off its own meshes.
##
## NOT A SECOND LIST, and for the same reason `collision.prop_boxes` derives its
## boxes from the emitted mesh rather than having every prop builder record what
## it placed. `rooms.PROPS` carries a declared (w, d, h) for all 99 tokens and it
## is the size the generator ASKED for; what got built is what a player walks up
## to. Two descriptions of one thing drift the moment either improves.
func _measure(it: Item) -> void:
	var lo := Vector3(INF, INF, INF)
	var hi := Vector3(-INF, -INF, -INF)
	for m in it.parts:
		var box: AABB = m.global_transform * m.get_aabb()
		var p0: Vector3 = box.position
		var p1: Vector3 = box.end
		for i in 3:
			lo[i] = minf(lo[i], p0[i])
			hi[i] = maxf(hi[i], p1[i])
	it.centre = (lo + hi) * 0.5
	it.half = (hi - lo) * 0.5
	_press_axis(it)


## WHICH WAY A PRESS TRAVELS, read off the geometry: into the object along its
## own thinnest axis. A wall panel is thin through the wall, a lever is thin
## across its throw. Nothing has to say "inward", so nothing can say it wrong --
## the same rule `door.gd` uses to find which way a leaf parts. The SIGN is
## settled at press time, because which face you are at depends on where you
## stand.
func _press_axis(it: Item) -> void:
	var axis := 0
	for i in 3:
		if it.half[i] < it.half[axis]:
			axis = i
	var n := Vector3.ZERO
	n[axis] = 1.0
	it.push = n


## A box on its own physics layer, so the eye ray has something to hit.
##
## The visible mesh carries NO collision when a collision proxy is supplied --
## `walk.gd::_load_level` -- so there is nothing here to raycast against unless
## this file makes it. A box rather than a trimesh: an interactable is a thing
## you point at, and pointing does not need the 66 mm channel.
func _give_box(it: Item) -> void:
	if it.half.x <= 0.0 or it.half.y <= 0.0 or it.half.z <= 0.0:
		return
	var sb := StaticBody3D.new()
	sb.name = "use_" + it.group
	sb.collision_layer = INTERACT_LAYER
	sb.collision_mask = 0
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = it.half * 2.0
	cs.shape = bs
	sb.add_child(cs)
	add_child(sb)
	sb.global_position = it.centre
	it.body = sb


func watch(body: Node3D) -> void:
	_player = body
	_cam = body.get_node_or_null("Camera3D") as Camera3D
	if _hud == null and not _args().has("no-hud"):
		var layer := CanvasLayer.new()
		layer.name = "UseHUD"
		add_child(layer)
		_hud = Label.new()
		_hud.name = "Prompt"
		_hud.anchors_preset = Control.PRESET_CENTER_BOTTOM
		_hud.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		layer.add_child(_hud)


func doors(d: Node) -> void:
	_doors = d


func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	if node is MeshInstance3D and (node as MeshInstance3D).mesh != null:
		out.append(node as MeshInstance3D)
	for c in node.get_children():
		_meshes(c, out)
	return out


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if not s.begins_with("--"):
			continue
		var body := s.substr(2)
		var eq := body.find("=")
		if eq < 0:
			out[body] = "1"
		else:
			out[body.substr(0, eq)] = body.substr(eq + 1)
	return out


## What the player is looking at, or null.
##
## NEAREST BY ANGLE, NOT BY DISTANCE. A player standing between a console and
## the counter behind it is looking at whichever one is in front of their face,
## and that is an angular question. Distance breaks ties.
func scan() -> Item:
	if _player == null:
		return null
	var eye: Vector3 = _player.global_position
	var fwd := Vector3.ZERO
	if _cam != null:
		eye = _cam.global_position
		fwd = -_cam.global_transform.basis.z
	else:
		fwd = -_player.global_transform.basis.z
	if fwd.length_squared() < 1e-9:
		return null
	fwd = fwd.normalized()
	var cos_lim := cos(deg_to_rad(look_half_deg))
	var best: Item = null
	var best_cos := -2.0
	var best_d := INF
	for it in _items:
		if not it.pressable:
			continue
		var to: Vector3 = it.centre - eye
		var d: float = to.length()
		if d > reach_m or d < 1e-4:
			continue
		var c: float = to.normalized().dot(fwd)
		if c < cos_lim:
			continue
		if c < best_cos - 0.001 or (absf(c - best_cos) <= 0.001 and d >= best_d):
			continue
		if not _in_sight(eye, it, d):
			continue
		best = it
		best_cos = c
		best_d = d
	return best


## Can the eye actually see it, or is there a bulkhead in the way?
##
## The ray is cast against the WALKING layer -- the collision shell the body
## stands on, which carries the prop boxes too (`build_collision(props=True)`).
## Three ways to be clear, and all three are needed: nothing was hit at all; the
## first thing hit is at or beyond the object's own near face; or the hit landed
## inside the object's own box, which is the object itself. Testing only the
## last would call every interactable too small to survive
## `prop_boxes(min_m=0.18)` occluded by the wall behind it.
func _in_sight(eye: Vector3, it: Item, _d: float) -> bool:
	var space := get_world_3d().direct_space_state
	if space == null or it.body == null:
		return true
	# RAY A -- at the object itself, on the interact layer. Nothing else in the
	# world is on it, so the only thing this can hit is an interactable, and if
	# the first one is not this one then something else is in front of it.
	var qa := PhysicsRayQueryParameters3D.create(eye, it.centre)
	qa.collision_mask = INTERACT_LAYER
	qa.collide_with_areas = false
	var a := space.intersect_ray(qa)
	if a.is_empty() or a.get("collider") != it.body:
		return false
	var da: float = eye.distance_to(a["position"])
	# RAY B -- at the same point on the WALKING layer, which is the collision
	# shell the body stands on plus the prop boxes. A bulkhead in the way stops
	# it measurably short of the object's own front face.
	var qb := PhysicsRayQueryParameters3D.create(eye, it.centre)
	qb.collision_mask = 1
	qb.collide_with_areas = false
	var b := space.intersect_ray(qb)
	if b.is_empty():
		return true
	# 0.10 m of skin, because the shell is DELIBERATELY not the render mesh:
	# `station/collision.py` sweeps a smooth profile past the corridor's 66 mm
	# lighting channel and its 22 mm proud tiles, so the surface a ray meets and
	# the surface a player sees differ by up to that much by design.
	return eye.distance_to(b["position"]) + 0.10 >= da


## USE WHAT YOU ARE LOOKING AT. The keypress and the headless test call THIS --
## not two paths that can diverge -- so the thing a gate proves is the thing a
## player does.
func use() -> bool:
	if _prompt == null:
		return false
	var it: Item = _prompt
	it.used += 1
	_use_count += 1
	_last_used = it
	# A DOOR ALREADY HAS A MECHANISM AND IT IS `door.gd`'S. Pressing one records
	# the use and does not grow a second way to open it: two descriptions of one
	# decision is the failure mode this project keeps rediscovering, and a door
	# that opens both on approach and on a keypress would drift the moment
	# either changed.
	_used_prompt = _hud.text if _hud != null else ""
	if it.responds:
		it.press_left = press_frames
		# AWAY FROM THE PLAYER: a control is pressed from the side you stand on,
		# and which side that is depends on where you are -- so the sign is
		# resolved here rather than baked at collect time.
		var from: Vector3 = it.centre
		if _player != null:
			from = _player.global_position
		var away: Vector3 = it.centre - from
		var n: Vector3 = it.push
		if n.dot(away) < 0.0:
			n = -n
		it.push = n
	print("USE %s place=%s token=%s verb=%s response=%s prompt=%s"
		% [it.group, it.place, it.token, it.verb,
			("press" if it.responds else "none"), _used_prompt])
	return true


var _used_prompt := ""


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo \
			and event.keycode == KEY_E:
		use()


## Re-take the look-at test, at most once per physics frame.
##
## ONCE PER FRAME AND CALLABLE FROM OUTSIDE, because Godot runs `_physics_process`
## in tree order and this node is a SIBLING of the player's driver: whichever
## runs first, the other reads a prompt computed before the body moved. The
## headless test walks the body and then asks what it is looking at, in the same
## frame, so it has to be able to force the scan -- and the frame guard is what
## stops that double-counting `prompt_frames`.
func refresh() -> Item:
	var f := Engine.get_physics_frames()
	if f == _scanned_frame:
		return _prompt
	_scanned_frame = f
	_prompt = scan()
	if _prompt != null:
		_prompt_frames += 1
	if _hud != null:
		_hud.text = ("" if _prompt == null
			else "[E]  %s the %s" % [_prompt.verb, _prompt.label])
	return _prompt


var _scanned_frame: int = -1


func _physics_process(_delta: float) -> void:
	refresh()
	for it in _items:
		if it.press_left <= 0:
			continue
		it.press_left -= 1
		var d: float = (press_travel_m if it.press_left > 0 else 0.0)
		for i in it.parts.size():
			it.parts[i].global_position = it.rest[i] + it.push * d
		# WHAT `use_travel_mm` DOES AND DOES NOT PROVE. It is read back off the
		# mesh's own world AABB rather than off the number that was just
		# written, so it goes through the scene graph and would report zero for
		# an object whose parts were never bound, for a `use()` that returned
		# true without reaching the press, and for a group the sidecar named and
		# the glb does not carry. It does NOT prove a player would see anything:
		# 4 mm is the acknowledgement a control gives, and judging that needs a
		# frame, not a physics run.
		if it.press_left == press_frames - 1:
			var box: AABB = (it.parts[0].global_transform
				* it.parts[0].get_aabb())
			it.travel_m = maxf(it.travel_m,
				box.get_center().distance_to(it.rest_centre))


# -- what the headless gate reads ------------------------------------------
# EVERY ONE OF THESE IS PRINTED UNCONDITIONALLY by `walk.gd` once this node
# exists, and `station/walkable.py` fails when a token it asked for is ABSENT.
# The alternative -- printing them only when there is something to say -- is the
# defect that let the NPC assertions vanish for six runs when `npc.gd` stopped
# parsing: a gate that disappears with its subject prints PASS.
func count() -> int:
	return _items.size()


func pressable_count() -> int:
	var n := 0
	for it in _items:
		if it.pressable:
			n += 1
	return n


func prompt_group() -> String:
	return "" if _prompt == null else _prompt.group


func prompt_verb() -> String:
	return "" if _prompt == null else _prompt.verb


func prompt_text() -> String:
	return "" if _hud == null else _hud.text


func prompt_frames() -> int:
	return _prompt_frames


func used_group() -> String:
	return "" if _last_used == null else _last_used.group


func used_verb() -> String:
	return "" if _last_used == null else _last_used.verb


## Did the object the player used have a response behind it? Read off the
## sidecar row, so this cannot disagree with `station/interact.py::RESPONDS`.
func used_responds() -> bool:
	return false if _last_used == null else _last_used.responds


## THE PROMPT AS IT READ AT THE MOMENT THE KEY WENT DOWN. The live prompt is
## gone by the end of a walk -- the body keeps moving -- so asserting on it at
## the end tests where the eye finished, not whether the player was ever told
## what they were about to use. This is the sentence that was on screen.
func used_prompt() -> String:
	return _used_prompt


## Sidecar rows that matched no mesh in this build.
func missing() -> Array[String]:
	return _missing


func use_count() -> int:
	return _use_count


## How far the used object's own mesh actually moved, in millimetres. The claim
## "it responded" is otherwise unfalsifiable: a use that returns true and moves
## nothing looks identical to one that works.
func used_travel_mm() -> float:
	return 0.0 if _last_used == null else _last_used.travel_m * 1000.0


## Distance from the player to the used object, for the gate to report.
func used_range_m() -> float:
	if _last_used == null or _player == null:
		return -1.0
	return _player.global_position.distance_to(_last_used.centre)


## Is a named group among the interactables at all? The negative control strips
## one from the mesh, and this is what says so.
func has_group(g: String) -> bool:
	for it in _items:
		if it.group == g:
			return true
	return false


## Distance from the eye to a named group, or -1. Reported so a failed prompt
## can be told from a body that never got near the thing.
func range_to(g: String) -> float:
	if _player == null:
		return -1.0
	var eye: Vector3 = _player.global_position
	if _cam != null:
		eye = _cam.global_position
	for it in _items:
		if it.group == g:
			return eye.distance_to(it.centre)
	return -1.0


## Every verb actually present in this build, `verb:count` joined by `/`.
func verb_report() -> String:
	var by := {}
	for it in _items:
		by[it.verb] = int(by.get(it.verb, 0)) + 1
	var parts: Array[String] = []
	for k in by:
		parts.append("%s:%d" % [String(k), int(by[k])])
	parts.sort()
	return "/".join(parts)


## Drop items whose meshes the engine has freed. See `door.gd::forget_freed`.
func forget_freed() -> int:
	var keep: Array[Item] = []
	for it2 in _items:
		var live := false
		for m in it2.parts:
			if is_instance_valid(m):
				live = true
				break
		if live:
			keep.append(it2)
		elif is_instance_valid(it2.body):
			it2.body.queue_free()
	var gone: int = _items.size() - keep.size()
	_items = keep
	# The live prompt may point at something that has just gone.
	if _prompt != null and not keep.has(_prompt):
		_prompt = null
	return gone
