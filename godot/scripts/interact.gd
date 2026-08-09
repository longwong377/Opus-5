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
## WHAT SESSION 4q ADDED, because the header above describes only half of it.
## `use()` used to do ONE thing for every verb -- count the press, move the prop
## four millimetres, print a line -- so 357 declared interactables reached a
## player as 357 identical wiggles. It now dispatches: `sit` and `rest` put the
## player's own body in the chair and take walking away until they stand,
## `store` moves things between the world and a bag that has a bottom, `serve`
## debits the purse, decrements the shelf and credits the till in
## `station/generated/economy.json`, and a `rest` on a bunk advances the station
## clock to when this person's species wakes. See `THE FOUR VERBS` below.
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
# carries `RESPONDS` and stamps `responds` on every sidecar row; this file reads
# the flag and never asks which verb it is in order to decide it.
#
# AS OF SESSION 4q THAT LIST IS EVERY PRESSABLE VERB, and getting there is what
# this session was. It read `("open", "operate", "read", "store", "serve")` with
# `sit` and `rest` excluded for an honest reason -- *"what responds to those is
# a BODY, not a prop"* -- and what "responds" MEANT for the five that were in it
# was: increment a counter, depress the prop four millimetres, print a line.
# Identically. `open` on a locker and `read` on an arrivals board did the same
# nothing. `store` had no inventory to move anything into, and `serve` ran no
# transaction while `station/economy.py` sat at 25/25 with stock, prices and
# tills nobody could reach. MASTER-PLAN A4b-1, A4b-2, A4b-3.


class Item:
	var group: String = ""
	var tag: String = ""                # which streamed cell brought it
	var place: String = ""
	var token: String = ""
	var verb: String = ""
	var label: String = ""
	var pressable: bool = false
	var responds: bool = false
	## WHAT A `read` ACTUALLY SAYS. Derived in `station/interact.py::read_text`
	## from the modules that already held the content and had no consumer --
	## `signage.arrivals_lines` for a board, `broadcast.day` for a monitor or a
	## comms channel, `economy` for a menu, `directory` for a plaque, a
	## schematic or an atmosphere lamp. Empty means nothing was derivable, and
	## the prompt falls back to the label exactly as before. NOT ONE LINE IS
	## WRITTEN HERE: a `read` that invented its text would be the unmarked
	## invention hard rule 1 forbids.
	var text: String = ""
	## True when that text is a function of the hour (a board, a monitor, a
	## menu). The sidecar is baked, so those are a snapshot at the bake hour and
	## a runtime that refreshes boards through the day refreshes only these.
	var live: bool = false
	## WHAT THE OTHER FOUR VERBS NEED, and not one of these is decided here.
	## `station/interact.py::verb_payload` bakes them from the modules that
	## already own the answer -- `rooms.PROP_KIND` for the shape, `economy` for
	## the lines and the price, `consequence.sells_to` for the reader -- for
	## exactly the reason the verb itself is baked: a second copy of any of
	## those in GDScript is free to drift the day one of them changes.
	##
	## `kind`    `rooms.PROP_KIND`: `seat` and `bed` are things you get ON, so
	##           the seat height is measured off this object; anything else is
	##           something you sit AT and the seat is the player's fitted one.
	## `holds`   the lines this place trades (`economy.stock_list`). Empty is a
	##           real answer -- an empty container is somewhere to PUT things.
	## `counter` `{sells, goods:[{good, cr}], tier:{rung: [ok, why]}}`. All
	##           seven rungs, because a player's standing changes inside a
	##           session and a counter baked at one rung would go on serving
	##           somebody the ladder has demoted.
	var kind: String = ""
	var holds: Array[String] = []
	var counter: Dictionary = {}
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
## STREAMED: `tag` names the cell these meshes arrived in, and `release(tag)`
## gives them back. The sidecar is per DECK and is NOT split -- a row whose
## meshes are not in this cell binds to nothing, which is the same rule that
## already skipped a row the glb never emitted.
## STRIP THE CLUSTER PREFIX A DECK MESH CARRIES AND A SIDECAR DOES NOT.
##
## `station/deck.py:1419` writes `pre = f"z{int(round(z))}__"` onto every mesh
## group of a multi-z deck -- added in 9db2466 so two clusters of one deck can
## both hold a `customs_north__prop_identicard_reader` without colliding. The
## SIDECARS were never given the same prefix, and neither were the three
## consumers that match against them. Measured on the shipped blue_0_0:
##
##     mesh groups 1471, of which 1375 are z-prefixed
##     interact rows 65 -- resolve EXACT: 0
##                      -- resolve after stripping the prefix: 64
##
## Zero. Every interactable on the station was unreachable, on a build whose
## own README promises the player an identicard reader. The content was never
## missing: 409 of 419 declared interactables exist as real mesh nodes.
##
## THE ENGINE'S OWN DIAGNOSTIC BLAMED THE WRONG THING and both judges quoted it
## uncritically -- `walk: N declared interactable(s) ... NO MESH in the glb --
## their parts claimed every triangle` points at triangle attribution, so a
## fixer following that message goes hunting geometry that is present.
##
## Stripping is done HERE, at the one place a mesh name meets a declared name,
## rather than at each of the three call sites -- this project's own rule that a
## fix applied to an instance and not the rule will be needed again.
static func strip_cluster(n: String) -> String:
	var i := n.find("__")
	if i <= 1 or not n.begins_with("z"):
		return n
	if not n.substr(1, i - 1).is_valid_int():
		return n
	return n.substr(i + 2)


func collect(visual: Node, rows: Array, tag: String = "") -> int:
	if tag != "":
		for it0 in _items:
			if it0.tag == tag:
				double_wires += 1
				push_error("interact: cell %s was wired twice without a "
					% tag + "release")
				return _items.size()
		wired_cells += 1
	var before := _items.size()
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
		var n := strip_cluster(String(m.name))
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
		it.tag = tag
		it.place = String(row2.get("place", ""))
		it.token = String(row2.get("token", ""))
		it.verb = String(row2.get("verb", ""))
		it.text = String(row2.get("text", ""))
		it.live = bool(row2.get("live", false))
		it.label = String(row2.get("label", it.token))
		it.pressable = bool(row2.get("pressable", false))
		it.responds = bool(row2.get("responds", false))
		it.kind = String(row2.get("kind", ""))
		for h in row2.get("holds", []):
			it.holds.append(String(h))
		var ctr = row2.get("counter")
		if typeof(ctr) == TYPE_DICTIONARY:
			it.counter = ctr
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
	#
	# NOT COMPUTABLE PER CELL, and saying so is better than a wrong number. On a
	# streamed build a row absent from THIS cell is almost always present in
	# another one, and whether it is present in ANY cell cannot be known until
	# every cell has been resident -- which never happens. So the miss list is
	# only accumulated for a monolithic load, where "not in this scene" really
	# does mean "not in the build".
	if tag == "":
		for g4 in want:
			if not found.has(g4):
				_missing.append(String(g4))
		_missing.sort()
	return _items.size() - before


## Give back everything one cell brought. Called BEFORE the cell is freed.
##
## THE PROXY BOXES ARE CHILDREN OF THIS NODE, NOT OF THE CELL, so they outlive
## the geometry unless this frees them -- and an interact box with no object in
## it is a prompt for a prop that has been unloaded, which is the streaming
## version of a door that is a picture of a door.
func release(tag: String) -> int:
	if tag == "":
		return 0
	var keep: Array[Item] = []
	var gone := 0
	for it in _items:
		if it.tag == tag:
			if it.body != null and is_instance_valid(it.body):
				it.body.queue_free()
			if _prompt == it:
				_prompt = null
				if _hud != null:
					_hud.text = ""
			gone += 1
		else:
			keep.append(it)
	_items = keep
	if gone > 0:
		released_cells += 1
		# The scan is frame-guarded, so without this the prompt computed before
		# the free would stand for the rest of this frame.
		_scanned_frame = -1
	return gone


## Counters the streaming gate reads.
var wired_cells := 0
var released_cells := 0
var double_wires := 0
## Frames on which the live prompt named an object that is no longer wired. It
## must be zero; the control that makes it fire is `--no-unwire`.
var stale_prompt_frames := 0


var _missing: Array[String] = []


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


# ===========================================================================
#  THE LEDGER -- the world's mutable half, and the engine now WRITES it
# ===========================================================================
## WHAT THIS ENDS. `station/economy.py` is a 25/25 working economy -- stock,
## derived prices, tills, wages, a fourteen-day trace in which a lurker crosses
## the passage-home line on day 4 -- and until session 4q **the only runtime
## consumer of any of it was `hud.gd` drawing a NUMBER out of the JSON file
## Python wrote.** The bar, the market, the kiosks and the black market all
## existed as geometry and not one of them would take your money.
## `MASTER-PLAN` A4b-3.
##
## THE DECISIONS ARE PYTHON'S AND THE ARITHMETIC IS HERE, and that split is
## deliberate rather than convenient. There is no call from GDScript into
## `consequence.purchase`, so what crosses is that function's OUTPUT: the price
## `economy.price` derived from one sourced anchor, and the six-rung verdict
## `consequence.sells_to` reached for every rung (INV-342 -- a licit counter
## checks the card because the identicard IS the credit card). This file looks
## up the player's rung, applies the verdict, and moves the four numbers
## `economy.buy` moves: purse down, shelf down, till up, one row appended.
##
## AND THE SPLIT IS GATED, because "one decision, two evaluations" is the shape
## this repository has paid for three times. `python3 station/interact.py
## --verify-buy BEFORE AFTER WHO PLACE GOOD` replays the same purchase through
## `consequence.purchase` from the before-ledger and fails on a one-millicredit
## disagreement with what this file wrote.
##
## IT IS NOT WRITTEN UNLESS SOMETHING HAPPENED. A launch that buys nothing
## leaves the file untouched, so a shipped run is not a mutation.
const LEDGER_REL := "../station/generated/economy.json"

var _led: Dictionary = {}
var _led_path := ""
var _led_dirty := false
## Transactions this session, for the gate to report. `sales` counts what the
## till took; `refusals` counts what it would not.
var sales := 0
var refusals := 0


func ledger_path() -> String:
	if _led_path != "":
		return _led_path
	var a := _args()
	if a.has("ledger"):
		_led_path = String(a["ledger"])
	else:
		_led_path = ProjectSettings.globalize_path("res://").path_join(
			LEDGER_REL).simplify_path()
	return _led_path


## Read the ledger and hand the player their own purse.
##
## WHICH PURSE IS THE PLAYER'S. `economy.json` keys purses by `npc_id` and a
## played session has exactly one whose id begins `player:` -- `player.py::
## player_id` mints that namespace and `resident.pool_id` deliberately does
## not, so the two can never collide. Sorted first, so a ledger carrying more
## than one is resolved the same way twice.
func _load_ledger() -> bool:
	var path := ledger_path()
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return false
	_led = d
	return true


## THE PURSE BUG THIS FIXES, AND IT IS WORTH STATING BECAUSE IT LOOKED LIKE A
## SORT ORDER AND WAS NOT.
##
## The old body took the FIRST key beginning `player:` out of a sorted list.
## Measured on the ledger this repository actually ships, `economy.json` holds
## exactly one such key -- `player:downbelow`, ALLAN, ANNA, a lurker at rung 0 --
## and the arrival sequence's player is `player:player`, Michael Chowdhury, a
## visitor on a TRANSIT 7D visa. Run before this change, the shipped
## `--mode=arrival` printed
##
##     interact: purse player:downbelow (ALLAN, ANNA, no_status) 420.71 cr
##     arrival: Michael Chowdhury -- human aboard Transport Cousteau
##
## in nineteen lines of each other. **The card in the player's hand and the
## wallet on their HUD named different people**, and the rung the entire law
## layer turns on came off the wrong one of them: rung 0 `no_status` instead of
## rung 2 `transit`, which `enforcement.json`'s own ladder makes the difference
## between "already at the floor" and "transit withdrawn".
##
## Sorting harder would not have fixed it. There is no `player:player` row in
## the document at all, so the scan had nothing right to find.
##
## SO THE SESSION SAYS WHO IT IS PLAYING, AND THE PURSE IS MINTED IF THE LEDGER
## HAS NONE. Asked of the node that owns the card (`arrival.gd::player_npc_id`)
## by CAPABILITY, the way `_find_clock` and `enforcement._look` find theirs, so
## a `walk.gd` build that names nobody keeps exactly the old behaviour and says
## which stranger it settled for.
func _my_purse() -> Dictionary:
	var purses = _led.get("purses", {})
	if typeof(purses) != TYPE_DICTIONARY or purses.is_empty():
		return {}
	var want := _declared_npc_id()
	if want != "":
		if purses.has(want):
			return purses[want]
		# NO ROW FOR THE PERSON THIS SESSION IS PLAYING. Minted from the sidecar's
		# own derived fields rather than borrowed from a stranger -- see
		# `arrival.gd::player_identity` for why that is reading and not deriving.
		# It goes into the ledger document, so `_sync_purse`, `_record` and
		# `convict` all have somewhere to write and the outcome survives the
		# process.
		var holder = _card_owner()
		if holder != null and holder.has_method("player_identity"):
			var st: Dictionary = holder.call("player_identity")
			purses[want] = st
			_led["purses"] = purses
			_led_dirty = true
			print("interact: no purse for %s in the ledger -- MINTED one from "
				% want + "the arrival sidecar (%s, %s, rung %d %s, %.2f cr). "
				% [String(st.get("name", "?")), String(st.get("role", "?")),
					int(st.get("tier", -99)), String(st.get("tier_name", "?")),
					float(st.get("credits", 0.0))]
				+ "`economy.py` did not know this person was coming.")
			# WHAT A MINTED PURSE CANNOT SUPPLY, NAMED RATHER THAN DEFAULTED.
			# `carry_cap`, `hip_m`, `seat_m`, `recline_m` and `wake_h` are
			# `station/player.py::posture` and `npc/schedule.py::wake_hour` --
			# per species and per stature -- and none of them is on the arrival
			# sidecar or on the nine-field card. Guessing a number here would be
			# the unmarked invention hard rule 1 forbids, so they stay absent and
			# the verbs that need them SAY they have nothing: `sit`/`rest` report
			# "no posture" and `store` has a bag of size zero. The fix is a
			# `player:player` row in `economy.json`, which is `station/economy.py`
			# and `station/arrival.py`'s to write, not this file's.
			var lack := PackedStringArray()
			for k in ["carry_cap", "hip_m", "seat_m", "recline_m", "wake_h"]:
				if not st.has(k):
					lack.append(String(k))
			if lack.size() > 0:
				print("interact: the minted purse has no %s -- sit, rest and "
					% ", ".join(lack) + "store are degraded for this body until "
					+ "`station/economy.py` writes a %s row" % want)
			return purses[want]
		push_error("interact: this session is playing %s and the ledger has no "
			% want + "purse for them, and nothing can mint one -- the wallet "
			+ "below belongs to somebody else")
	var keys: Array = purses.keys()
	keys.sort()
	for k in keys:
		if String(k).begins_with("player:"):
			if want != "" and String(k) != want:
				push_error("interact: FALLING BACK to %s -- this is NOT the "
					% String(k) + "person the session named (%s)" % want)
			elif want == "":
				# NOBODY DECLARED WHO THIS SESSION IS PLAYING, AND THAT IS THE
				# SHIPPED PATH. In `--mode=arrival` the parent is `arrival.gd`,
				# which answers `player_npc_id`; on the default `--mode=station`
				# the parent is `walk.gd`, which does not -- so this loop picks
				# the alphabetically first `player:` row and calls it the player.
				#
				# It is not choosing badly among candidates. It is choosing the
				# ONLY one: `economy.py` writes exactly one player purse (it
				# asserts that, line 2615) and casts `player:downbelow`, ALLAN,
				# ANNA, a lurker -- while the arrival sequence casts
				# `player:player`, CHOWDHURY, MICHAEL. TWO SYSTEMS EACH CAST A
				# PLAYER AND THEY CAST DIFFERENT PEOPLE. The wallet in the HUD
				# and the card in the hand name two strangers, and they always
				# have.
				#
				# Reconciling them is a decision about which system is
				# authoritative, not a patch here, so this says so on every run
				# instead of pretending. The HUD now prints `person=` beside the
				# credits, so it is on the frame as well as in the log.
				push_warning("interact: NOBODY DECLARED THE PLAYER -- using %s "
					% String(k) + "(%s) because it is the only `player:` row "
					% String((purses[k] as Dictionary).get("name", "?"))
					+ "in the ledger. If the card in your hand names someone "
					+ "else, this is why: economy.py and the arrival sequence "
					+ "cast different people. walk.gd needs a player_npc_id().")
			return purses[k]
	return purses[keys[0]]


## Who this session is playing, or "" when nothing in the tree says.
func _declared_npc_id() -> String:
	var holder = _card_owner()
	if holder != null and holder.has_method("player_npc_id"):
		return String(holder.call("player_npc_id"))
	return ""


func _save_ledger() -> bool:
	if not _led_dirty or _led.is_empty():
		return false
	var f := FileAccess.open(ledger_path(), FileAccess.WRITE)
	if f == null:
		push_error("interact: cannot write %s" % ledger_path())
		return false
	f.store_string(JSON.stringify(_led, " ", true))
	f.close()
	_led_dirty = false
	return true


## Put the player's live purse back into the ledger document. Called after
## every move of money or goods, so the delta is one `_save_ledger` away from
## disk at all times.
##
## IT WRITES TWO KEYS AND DELIBERATELY NOT A THIRD, AND THE THIRD IS THE RUNG.
## `st["tier"]`/`st["tier_name"]` are `player.py::state()`'s REPORT of the
## frozen card, and a conviction does not edit a card -- it writes a record. So
## the demotion goes into `st["record"]` through `convict()` below, and the rung
## is re-derived from that record on the next load by `player.gd::rung_of`.
##
## THIS LOOKS LIKE THE BUG AND IS THE FIX. Session 4t round 2 shipped with the
## reload broken -- launch 2 opened a revoked card still reading `transit` --
## and the obvious repair is three characters here: also write `st["tier"]`.
## That repair works and is wrong. It stores the rung as a fact, which is what
## `player.py`'s own comment forbids ("Restoring them would be a second copy of
## a derivation, which is how a saved tier survives a conviction"), and it would
## leave every OTHER reader of that field -- a save written by Python, a purse
## minted by `enforcement.prog_ledger`, a hand-edited ledger -- still trusting a
## number nobody re-derived. The fix went to the rule instead. Do not add it.
func _sync_purse() -> void:
	if _player == null or _led.is_empty() or String(_player.npc_id) == "":
		return
	var purses = _led.get("purses", {})
	if typeof(purses) != TYPE_DICTIONARY:
		return
	var st = purses.get(_player.npc_id)
	if typeof(st) != TYPE_DICTIONARY:
		return
	st["credits"] = _player.credits
	st["carrying"] = _player.carrying.duplicate()
	_led_dirty = true


# ===========================================================================
#  WHO IS CARRYING A CARD, AND WHO KNOWS WHAT IT SAYS
# ===========================================================================
## THERE IS NO CUSTOMS RULE IN THIS FILE AND THERE MUST NEVER BE ONE. This file
## dispatches a verb; `arrival.gd` owns the identicard and the ten stations of
## TRAFFIC-AND-CUSTOMS 6.3, because it owns the sequence those came in. So
## `operate` on a reader ASKS, and a build with nobody to ask says so instead of
## deciding.
##
## FOUND TWO WAYS FOR ONE REASON OF TIMING. `bind_card` is the explicit call and
## `arrival.gd` makes it right after `super._ready()`; but `watch()` -- which
## loads the purse -- runs DURING that `super._ready()`, one function too early
## for any explicit call to have happened. So the fallback walks up to the
## parent, which `walk.gd::_make_interact` guarantees is the node that built this
## one. Both paths land on the same node; the second one just gets there before
## the first one could have been made.
var _card = null


func bind_card(node) -> void:
	_card = node


func _card_owner() -> Variant:
	if _card != null and is_instance_valid(_card):
		return _card
	var p := get_parent()
	if p != null and p.has_method("customs_verdict"):
		_card = p
		return p
	return null


func watch(body: Node3D) -> void:
	_player = body
	_cam = body.get_node_or_null("Camera3D") as Camera3D
	# THE PURSE ARRIVES BEFORE THE FIRST PROMPT DOES. Once per body: `watch()`
	# is called again on every streamed cell that brings interactables, and
	# re-reading the ledger there would throw away a purchase made in the cell
	# before this one.
	if _player != null and not _purse_done:
		_purse_done = true
		if _load_ledger():
			var st := _my_purse()
			if not st.is_empty() and _player.has_method("set_purse"):
				_player.set_purse(st)
				print("interact: purse %s (%s, %s) %.2f cr, carrying %d/%d"
					% [_player.npc_id, _player.person, _player.tier_name,
						_player.credits, _player.carrying.size(),
						_player.carry_cap])
				# AND WHERE THAT RUNG CAME FROM, because the line above is the
				# one a reload gate reads and a NAME is not evidence that
				# anything was derived. `player.gd::rung_of` computes the rung
				# off the record; this prints it beside the number the DOCUMENT
				# carried, so "the engine derived it" and "the engine echoed a
				# stored field" are two distinguishable lines rather than one.
				# Session 4t round 2 shipped with them indistinguishable and
				# the reload was false for six days -- see `player.gd`'s header.
				print("interact: rung %d %s DERIVED, document reported %d %s "
					% [int(_player.tier), String(_player.tier_name),
						int(_player.tier_stored),
						String(st.get("tier_name", "-"))]
					+ "-- %s" % String(_player.rung_why))
		else:
			print("interact: no ledger at %s -- nothing can be bought"
				% ledger_path())
	if _hud == null and not _args().has("no-hud"):
		var layer := CanvasLayer.new()
		layer.name = "UseHUD"
		add_child(layer)
		_hud = Label.new()
		_hud.name = "Prompt"
		_hud.anchors_preset = Control.PRESET_CENTER_BOTTOM
		_hud.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		layer.add_child(_hud)
	_make_enforcement()


var _purse_done := false

# ===========================================================================
#  WHAT HAPPENS AFTER A REFUSAL -- see `scripts/enforcement.gd`
# ===========================================================================
# WHY IT IS BUILT HERE. `hud.gd` reads the identicard on the way into a place
# and the arrest chain behind a refusal was still Python, so a player was TOLD
# they were refused and nothing followed. The thing that follows needs three
# joins this node already has and no other node has all of: the PURSE (a fine is
# money, and this file is the ledger's one writer), the PLAYER (they are walked
# out of the room), and a place in the shipped scene's tree that is built on
# BOTH the monolithic and the streamed path -- `walk.gd::_make_interact` runs in
# `_wire_interact`, which `stream.gd::wire_cell` calls per cell.
#
# ONCE PER SESSION, NOT ONCE PER CELL. `watch()` is called again on every
# streamed cell that brings interactables, and a second director would mean two
# patrols answering one refusal.
var _enforce: Node = null


## Harness modes this must stay out of. A refusal ESCORTS THE PLAYER OUT OF THE
## ROOM -- it moves the body -- and every gate in this list measures where a body
## got to. `walkable.py --deck` walks straight into `docking_bays`, which is a
## checked place, so a responder that fired there would move the subject of the
## measurement and the walk gate would report a distance nobody walked.
##
## IT IS INERT TODAY AND THAT IS NOT THE ARGUMENT FOR LEAVING IT OUT. Checked
## against the live tree: `hud.gd::checks` is only ever filled by
## `walk.gd::_wire_hud` from an `@export` that `main.gd` sets off `boot.json`, so
## a `--glb=` harness has an empty table and no reading fires at all. That is
## true by accident of who sets one variable, and the cost of it becoming untrue
## is a walk gate that fails for a reason nobody would look for.
const HARNESS_MODES := ["walk-test", "stream-test", "corpse-gate",
	"gravity-gate", "shot", "ragdoll-gate", "route-test"]


func _make_enforcement() -> void:
	if _enforce != null or _player == null:
		return
	if _args().has("no-enforcement"):
		print("interact: enforcement DISABLED (control) -- a refusal is "
			+ "reported and nothing follows it")
		return
	var a := _args()
	for m in HARNESS_MODES:
		if a.has(m):
			print("interact: enforcement OFF under --%s -- this harness "
				% m + "measures where a body got to, and a refusal moves it")
			return
	_enforce = Node3D.new()
	_enforce.name = "Enforcement"
	_enforce.set_script(load("res://scripts/enforcement.gd"))
	add_child(_enforce)
	_enforce.call("bind", _player, self)
	# THE GATE IS DRIVEN FROM THE NODE IT GATES, and it is started here because
	# this is the one call site both build paths pass through. `run_gate` is a
	# coroutine: it settles, drives the body across a real boundary, and quits
	# with its own verdict.
	if _enforce.call("gate_wanted"):
		_enforce.call("run_gate")


## THE FINE, AND IT MOVES IN THE LEDGER A DRINK MOVES THROUGH.
##
## `consequence._post_fine` is the Python half and this is the same four
## numbers: the purse goes down, the COURT's till goes up, a row is appended to
## `sales` naming the offence, and the document is written. Not a new wallet and
## not a new file -- `economy.Ledger.till`, `.sales` and `.purses` are the
## existing three.
##
## RETURNS WHETHER IT WAS PAID, and an unpayable fine is not an error. LAW-CRIME
## 4.3's Jinxo precedent read economically: the brig is not a debtors' prison,
## so the debt walks out with you and the card carries it.
func fine(cr: float, court: String, offence: String) -> bool:
	if _player == null or _led.is_empty() or cr <= 0.0:
		return false
	var paid := float(_player.credits) >= cr
	if paid:
		_player.credits = snappedf(float(_player.credits) - cr, 0.001)
	var till = _led.get("till", {})
	till[court] = snappedf(float(till.get(court, 0.0)) + (cr if paid else 0.0),
		0.01)
	_led["till"] = till
	var rows = _led.get("sales", [])
	rows.append({"day": int(_led.get("day", 0)), "at": court,
		"good": "(fine: %s)" % offence, "n": 1, "cr": snappedf(cr, 0.01),
		"who": String(_player.npc_id), "paid": paid})
	_led["sales"] = rows
	_sync_purse()
	_record_fine(cr, paid)
	_save_ledger()
	return paid


## THE CONVICTION, WRITTEN WHERE IT SURVIVES THE PROCESS.
##
## `player.py::state()` already carries a `record` key and `restore` reads it
## back -- its own comment says why: "A CONSEQUENCE THAT DOES NOT SURVIVE THE
## PROCESS IS A MOOD". So the engine writes into that same key, in
## `consequence.Record.state()`'s own shape, and a session that quits after a
## detention comes back one conviction in with the rung it was left at.
func convict(offence: String, cr: float, revoked: bool, tier_after: int,
		tier_after_name: String) -> void:
	var rec := _record()
	var cv: Array = rec.get("convictions", [])
	cv.append(offence)
	rec["convictions"] = cv
	rec["custody_events"] = int(rec.get("custody_events", 0)) + 1
	if revoked:
		rec["visa_revoked"] = true
		rec["revoked_from"] = String(_player.tier_name)
		var notes: Array = rec.get("notes", [])
		notes.append("day %d: %s revoked on %s"
			% [int(_led.get("day", 0)), String(_player.tier_name), offence])
		rec["notes"] = notes
		_player.tier = tier_after
		_player.tier_name = tier_after_name
	_put_record(rec)
	_save_ledger()
	print("interact: conviction %d on the card -- %s%s"
		% [cv.size(), offence,
			(", %s WITHDRAWN" % tier_after_name if revoked else "")])


func convictions() -> int:
	return (_record().get("convictions", []) as Array).size()


func _record() -> Dictionary:
	var st := _my_purse()
	var r = st.get("record")
	if typeof(r) != TYPE_DICTIONARY:
		return {"convictions": [], "fines_paid": 0.0, "fines_outstanding": 0.0,
			"custody_events": 0, "custody_seconds": 0.0, "in_custody": false,
			"visa_revoked": false, "revoked_from": "", "notes": []}
	return r


func _put_record(rec: Dictionary) -> void:
	var st := _my_purse()
	if st.is_empty():
		return
	st["record"] = rec
	_led_dirty = true


func _record_fine(cr: float, paid: bool) -> void:
	var rec := _record()
	if paid:
		rec["fines_paid"] = snappedf(float(rec.get("fines_paid", 0.0)) + cr,
			0.001)
	else:
		rec["fines_outstanding"] = snappedf(
			float(rec.get("fines_outstanding", 0.0)) + cr, 0.001)
	_put_record(rec)


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
	#
	# EXCEPT WHEN THE THING IN FRONT OF IT CONTAINS IT, AND THAT MADE THE
	# IDENTICARD READER UNUSABLE ON THE SHIPPED BUILD. `_give_box` gives every
	# interactable a BoxShape3D of its WORLD AABB, and a long panel lying
	# tangentially across a ring deck has an enormous one: the customs desk at
	# `customs_north` measures 11.30 x 13.22 x 0.82 m, and the identicard reader
	# -- 5.76 m away down the axis -- has its centre INSIDE it. Every ray from
	# anywhere in the hall to that centre therefore entered the desk's box first,
	# `collider != it.body` was true on every frame, and the reader could never
	# become the prompt. Measured: the arrival driver walked the body to **2.4 m
	# and the prompt said `operate/baggage_scanner`**, so the one object the
	# entire arrival sequence exists to reach was unpressable -- by the test AND
	# by a player, since both come through this function.
	#
	# A BOX THAT SWALLOWS THE TARGET IS NOT AN OCCLUDER OF IT. That is the rule,
	# and it is about containment rather than about customs: any interactable
	# whose own box holds this one's centre is around it, not in front of it, so
	# it is excluded and the ray is cast again. Bounded by the item count, and in
	# practice one retry. NOT widened to "ignore anything close", which would
	# stop a bulkhead counting -- the exclusion is only for a shape the target is
	# demonstrably inside.
	var skip: Array[RID] = []
	var a := {}
	for _try in 4:
		var qa := PhysicsRayQueryParameters3D.create(eye, it.centre)
		qa.collision_mask = INTERACT_LAYER
		qa.collide_with_areas = false
		qa.exclude = skip
		a = space.intersect_ray(qa)
		if a.is_empty() or a.get("collider") == it.body:
			break
		var other = a.get("collider")
		if other == null or not _swallows(other, it.centre):
			return false
		skip.append((other as CollisionObject3D).get_rid())
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


## Does this proxy's own box contain that point? Asked of the ITEM LIST rather
## than of the physics shape, because the half-extents this file measured are
## the same numbers `_give_box` built the shape from and reading them back is
## exact -- a shape query would answer the same question with a tolerance.
func _swallows(body_node, p: Vector3) -> bool:
	for other in _items:
		if other.body != body_node:
			continue
		var d: Vector3 = p - other.centre
		return (absf(d.x) <= other.half.x and absf(d.y) <= other.half.y
			and absf(d.z) <= other.half.z)
	return false


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
	# SNAPSHOT WHAT WAS USED, as values. On a streamed build the cell holding
	# this object can be freed before the verdict is printed, and a verdict that
	# reads fields off a released Item is a verdict that reports on geometry that
	# no longer exists -- or crashes on it.
	_used_group = it.group
	_used_verb = it.verb
	_used_responds = it.responds
	_used_centre = it.centre
	_used_travel_m = it.travel_m
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
	# THE VERB DOES SOMETHING. Everything above this line is what every verb
	# used to do -- count the press, depress the prop, print a line -- and it is
	# why `read` on an arrivals board showed a player exactly what `open` on a
	# locker showed them: nothing. 4p made `read` real. 4q makes the other
	# three, and the count is the honest measure of it: `sit` is 37 declared
	# instances across 29 places, `rest` 18 across 18, `store` 27 across 27,
	# `serve` 30 across 28 of which 11 stand at a counter `economy.py` actually
	# stocks. `python3 station/interact.py --coverage` prints it.
	#
	# `open` IS NOT DISPATCHED HERE and that is not an omission. A door already
	# has a mechanism and it is `door.gd`'s -- two ways to open one leaf is the
	# failure mode this repository keeps rediscovering.
	#
	# `operate` WAS NOT DISPATCHED EITHER, AND THAT WAS ONE. The comment this
	# replaces said a control's response IS the press travel -- four millimetres
	# of mesh -- and on 19 declared interactables that was the whole of it,
	# including the identicard reader the entire arrival sequence walks to. A
	# customs post whose response is a 2 mm wiggle is the "no consequence"
	# finding in one object. See `_verb_operate`.
	_read_text = ""
	_said = ""
	match it.verb:
		"read":
			if it.text != "":
				_read_text = it.text
				_read_until = _read_hold_s
		"sit", "rest":
			_said = _verb_sit(it)
		"store":
			_said = _verb_store(it)
		"serve":
			_said = _verb_serve(it)
		"operate":
			_said = _verb_operate(it)
	_said_until = (_read_hold_s if _said != "" else 0.0)
	print("USE %s place=%s token=%s verb=%s response=%s prompt=%s%s%s"
		% [it.group, it.place, it.token, it.verb,
			("press" if it.responds else "none"), _used_prompt,
			("" if _read_text == "" else " READ=%s"
				% _read_text.replace("\n", " / ")),
			("" if _said == "" else " DID=%s" % _said)])
	return true


# ===========================================================================
#  THE FOUR VERBS
# ===========================================================================
## SIT / REST -- and the thing that responds is the player's own body.
##
## WHICH HEIGHT, and it is `rooms.PROP_KIND`'s call rather than this file's. A
## `seat` or a `bed` is something you get ON, so the surface is measured off
## the object -- the support point of its own world box along the body's up,
## which on a ring deck is radial and at every angle a different world
## direction. Anything else carrying a sit or rest verb is something you sit
## AT: a `table` (the register's own head-noun override), a `shrine`, a
## `brazier`. For those the seat is the player's fitted knee height, which
## `station/player.py::posture` derives per species and per stature.
##
## A SECOND PRESS STANDS YOU UP, on any seat. Otherwise the only way out of a
## chair is a key the prompt never mentioned.
func _verb_sit(it: Item) -> String:
	if _player == null or not _player.has_method("sit_at"):
		return ""
	if String(_player.seated) != "":
		var h0: float = float(_player.seat_used_m)
		_player.stand_up()
		return "stood up from %.2f m" % h0
	var recline: bool = (it.kind == "bed")
	var h := -1.0
	if it.kind == "seat" or it.kind == "bed":
		h = _surface_height(it)
	if not _player.sit_at(h, it.verb, recline):
		if float(_player.hip_m) <= 0.0:
			return ("no posture -- this body has no purse, so nothing knows "
				+ "how tall the person in the chair is")
		return ""
	var how := ("on its own measured top" if h > 0.0 else "on the fitted seat")
	var line := "%s at %.2f m (%s), eye %.2f m -> %.2f m" % [
		("lay down" if recline else "sat down"),
		float(_player.seat_used_m), how, float(_player.eye_height_m),
		float(_player.eye_now_m())]
	if recline:
		line += _sleep()
	return line


## LYING DOWN ON A BUNK ADVANCES THE STATION CLOCK TO WHEN THIS PERSON WAKES.
##
## IT FELL OUT CHEAPLY AND THAT IS THE ONLY REASON IT IS HERE. `life.gd`'s
## `Clock` has carried `set_hour()` since it was written -- its own docstring
## says *"a jump is indistinguishable from having waited, which is the whole
## point of the design"* -- and the Director that owns it is already findable
## by CAPABILITY, which is `npc.gd`'s rule and not a new one: a node that both
## REPORTS an hour and APPLIES one is the Director, and a node that only
## reports one (`dialogue.gd`) is a follower. So a sleep is: read the hour,
## set it, and let the Director put every bound body where the new hour says
## it is. Fifteen lines against a system that already existed.
##
## WHEN YOU WAKE IS NOT A CONSTANT. `wake_h` is `npc/schedule.py::wake_hour`
## for THIS person's species, carried on the purse: a human wakes at 06:30 and
## a Narn at 05:30, and a runtime that split the difference would be inventing
## a rhythm the census already states.
##
## NO CLOCK, NO JUMP, AND IT SAYS SO. `walk.gd` builds no Clock -- every
## headless walk gate in this repository runs without one -- so lying down
## there is lying down, and the sentence a player gets says which it was
## rather than silently doing nothing.
func _sleep() -> String:
	var ck := _find_clock()
	if ck == null:
		return " (no station clock in this build -- you lie down, time does not move)"
	var wake: float = float(_player.wake_h)
	if wake < 0.0:
		return " (no wake hour on this card)"
	var now: float = float(ck.call("hour"))
	if now < 0.0:
		return " (the clock has not started)"
	# A SLEEP OF NO LENGTH IS A SLEEP OF A DAY. Lying down at exactly your own
	# wake hour asks for the NEXT one, not for zero hours. `station/compress.py
	# ::hours_between` has the same rule and the same reason.
	var slept: float = fposmod(wake - now, 24.0)
	if slept < 1e-6:
		slept = 24.0
	var clock = ck.get("clock")
	if clock == null or not clock.has_method("set_hour"):
		return " (this clock cannot be set)"

	# THE WORLD IS CARRIED THROUGH THE NIGHT, NOT TELEPORTED PAST IT.
	#
	# This used to be one `set_hour(wake)` and one `apply(wake)`. Fifteen honest
	# lines against a system that already existed -- and the seven hours between
	# lying down and waking never happened. Nobody moved through them. Nothing
	# could wake you, because there was no interval to be woken during.
	# `docs/THE-STATION.md` PLY-05 is explicit that both SLEEP and WAIT advance
	# the clock "through the running simulation -- events still fire, stocks
	# still move, the world does not pause", and a jump is the opposite of that.
	#
	# ONE STATION-HOUR A STEP, which is `compress.STEP_H` and is derived there:
	# it is the finest grain at which either of this station's world-tick
	# systems has anything to say. Seven steps for a night, each one a
	# `Director.apply` that puts all 21 bound residents where that hour says
	# they are -- so a player who sleeps 22:00 -> 05:15 is stepped past the
	# 02:00 quiet hour and wakes into a corridor that filled up while they slept
	# rather than one that changed between two frames.
	#
	# WHAT IT DOES NOT DO YET, so silence is not read as completeness: nothing
	# here can INTERRUPT the sleep. `compress.advance` stops at the first
	# incident loud enough and near enough, and the runtime has no incident tick
	# to ask -- `main.gd` fires collapses from a baked list rather than
	# simulating. The step loop is the half that makes the other half possible.
	var step_h: float = 1.0
	var done: float = 0.0
	var steps: int = 0
	while done < slept - 1e-6:
		done = minf(slept, done + step_h)
		var at: float = fposmod(now + done, 24.0)
		clock.call("set_hour", at)
		ck.call("apply", at)
		steps += 1
	return " -- slept %.2f h through %d station-hours, %05.2f -> %05.2f EMT" \
		% [slept, steps, now, wake]


## The station clock, found BY CAPABILITY rather than by node name -- and the
## capability is two methods, not one, for the reason `npc.gd` records: a node
## that only reports an hour is a follower, and a depth-first search finds one
## of those before the Director on the shipped scene.
var _clock_node: Node = null
var _clock_looked := false


func _find_clock() -> Node:
	if _clock_node != null or _clock_looked:
		return _clock_node
	_clock_looked = true
	var scene := get_tree().current_scene if get_tree() != null else null
	for root in [scene, get_parent()]:
		if root == null:
			continue
		var n := _search_clock(root, 0)
		if n != null:
			_clock_node = n
			print("interact: station clock at %s" % n.get_path())
			return n
	return null


func _search_clock(node: Node, depth: int) -> Node:
	if depth > 4:
		return null
	if node.has_method("hour") and node.has_method("apply") and node != self:
		return node
	for c in node.get_children():
		var got := _search_clock(c, depth + 1)
		if got != null:
			return got
	return null


## How high this object's top surface is above the player's own feet.
##
## THE SUPPORT POINT OF THE BOX ALONG THE BODY'S UP, which is exact for an
## axis-aligned box and is not the same as `centre.y + half.y`: "up" here is
## the radial direction out of the spin axis, so on the far side of the ring
## the top of a bench is at a SMALLER world y than its centre. Taking it from
## `half.y` alone would have seated a player 0.45 m into the floor for half of
## every lap.
func _surface_height(it: Item) -> float:
	if _player == null:
		return -1.0
	var up: Vector3 = _player.body_up()
	var top := it.centre + Vector3(
		(it.half.x if up.x >= 0.0 else -it.half.x),
		(it.half.y if up.y >= 0.0 else -it.half.y),
		(it.half.z if up.z >= 0.0 else -it.half.z))
	return (top - _player.global_position).dot(up)


## STORE -- the inventory, and it moves BOTH ways.
##
## THERE WAS NO INVENTORY ANYWHERE. Zero references in 16,865 lines of
## `godot/scripts/` as of the 4p audit, while `station/player.py` had carried
## `IDENTICARD`, `KIT_BAG` and a `carrying` tuple since it was written --
## MASTER-PLAN A4b-2. This is the verb that uses it.
##
## WHICH DIRECTION IS DECIDED BY THE CONTAINER, not by a second key: a
## container with lines in it gives you one, an empty one takes one. The lines
## are `economy.stock_list(place)` -- what that place's own register functions
## trade -- so a crate in the black market holds contraband and a tray
## dispenser in the mess hall holds nothing, because `mess_hall` is
## ("catering", "crew_social") and sells no line.
##
## THE IDENTICARD IS NEVER THE THING YOU PUT DOWN, and that rule has a reason:
## TRAFFIC-AND-CUSTOMS 6.4 makes it passport, licence, credit card and medical
## file at once, `arrival.py` refuses entry without it, and losing it by
## pressing E on a locker would be a character arc nobody chose.
func _verb_store(it: Item) -> String:
	if _player == null or not _player.has_method("take"):
		return ""
	if not it.holds.is_empty():
		var want := String(it.holds[it.used % it.holds.size()])
		if _player.bag_full():
			return "no room for %s -- carrying %d/%d" % [want,
				_player.carrying.size(), int(_player.carry_cap)]
		if not _player.take(want):
			return "no room for %s" % want
		_sync_purse()
		return "took %s -- carrying %d/%d" % [want,
			_player.carrying.size(), int(_player.carry_cap)]
	var give := ""
	for x in _player.carrying:
		if String(x) != "identicard":
			give = String(x)
	if give == "":
		return "nothing to put in it"
	_player.put(give)
	_sync_purse()
	return "put %s in it -- carrying %d/%d" % [give,
		_player.carrying.size(), int(_player.carry_cap)]


## SERVE -- the counter takes your money.
##
## EVERY DECISION HERE WAS MADE IN PYTHON. The price is `economy.price`'s, from
## one sourced anchor through a class band; the verdict is
## `consequence.sells_to`'s, evaluated at all seven rungs and baked into the
## row. What this function does is the arithmetic `economy.buy` does, on the
## same four numbers, and `station/interact.py --verify-buy` replays it through
## `consequence.purchase` to prove the two agree.
##
## THE REFUSALS ARE THE POINT AS MUCH AS THE SALE. A till that cannot say no is
## not a till: an empty shelf, a purse that is short, and a card the reader
## will not take (INV-342 -- exactly one licit rung is excluded, and it is the
## rung the black market exists to serve) each come back with the sentence a
## keeper would actually give.
func _verb_serve(it: Item) -> String:
	if _player == null or not _player.has_method("set_purse"):
		return ""
	if it.counter.is_empty():
		return ""
	var tiers = it.counter.get("tier", {})
	var rung := int(_player.tier)
	var verdict = tiers.get(str(rung), null)
	if typeof(verdict) == TYPE_ARRAY and verdict.size() == 2 \
			and not bool(verdict[0]):
		refusals += 1
		return "REFUSED (%s): %s" % [String(_player.tier_name),
			String(verdict[1])]
	if not bool(it.counter.get("sells", false)):
		refusals += 1
		return "REFUSED: nothing is sold here"
	if not _player.has_purse():
		return "no ledger -- this counter cannot take money"
	# WHAT IS ON THE SHELF IS LIVE, not baked. The row carries the LINES and
	# their prices, which are deterministic; how many are left is the ledger's,
	# and it moves every time anybody -- the player or `background_sales` --
	# takes one.
	var stock = _led.get("stock", {}).get(it.place, {})
	var pick := {}
	var goods = it.counter.get("goods", [])
	for i in goods.size():
		var g = goods[(it.used + i) % goods.size()]
		if typeof(g) != TYPE_DICTIONARY:
			continue
		if int(stock.get(String(g.get("good", "")), 0)) > 0:
			pick = g
			break
	if pick.is_empty():
		refusals += 1
		return "REFUSED: the shelf is empty"
	var good := String(pick.get("good", ""))
	var cr := float(pick.get("cr", 0.0))
	if float(_player.credits) < cr:
		refusals += 1
		return "REFUSED: %s costs %.2f cr and you have %.2f" % [
			good, cr, float(_player.credits)]
	if _player.bag_full():
		refusals += 1
		return "REFUSED: nothing to carry it in -- %d/%d" % [
			_player.carrying.size(), int(_player.carry_cap)]
	# -- the four numbers `economy.buy` moves, and no fifth ------------------
	# ROUNDED THE WAY PYTHON ROUNDS THEM, and that is load-bearing rather than
	# tidy: `economy.buy` totals at 2 dp and `Player.spend` keeps a balance to
	# MILLIcredits, because LAW-CRIME:730 puts millicredits below the credit
	# and an `int()` truncation there once ate 0.20 cr of a 0.80 cr drink.
	# `--verify-buy` fails on a one-millicredit disagreement, so these two
	# snaps are what make it pass.
	_player.credits = snappedf(float(_player.credits) - cr, 0.001)
	_player.take(good)
	stock[good] = int(stock[good]) - 1
	var till = _led.get("till", {})
	till[it.place] = snappedf(float(till.get(it.place, 0.0)) + cr, 0.01)
	var rows = _led.get("sales", [])
	rows.append({"day": int(_led.get("day", 0)), "at": it.place,
		"good": good, "n": 1, "cr": snappedf(cr, 0.01),
		"who": String(_player.npc_id)})
	_led["sales"] = rows
	_sync_purse()
	_save_ledger()
	sales += 1
	return "bought %s for %.2f cr (%s) -- purse %.2f, till %.2f, %d left" % [
		good, cr, String(_player.tier_name), float(_player.credits),
		float(till[it.place]), int(stock[good])]


# ===========================================================================
#  OPERATE -- AND THE ONE CONTROL ON THIS STATION THAT DECIDES SOMETHING
# ===========================================================================
## WHICH TOKEN IS THE READER, AND WHY A NAME HERE IS NOT A TABLE. `token` is
## `station/interact.py`'s own field, written into the sidecar beside the verb;
## this file already matches on `it.verb`, which came from the same row. One
## token name is a BIND POINT between a generated name and the behaviour it
## earns, and it is the same shape as `_verb_store`'s single `"identicard"`
## exclusion two functions up. What would be a table is a dictionary of 19
## tokens to 19 behaviours, and there is not one.
const READER_TOKEN := "identicard_reader"


## OPERATE.
##
## Every other `operate` in this build is still exactly what it was -- the press
## travel applied in `use()` above -- and this function SAYS SO rather than
## returning "" and leaving a player to guess whether anything happened. The
## reader is the one that decides something, and what it decides is not in any
## file: `arrival.gd::customs_verdict` resolves the ten stations against the
## nine fields still on the card and the item in the player's hand, at the
## moment of the press.
##
## THE THREE THINGS A REFUSAL THEN DOES, because a verdict nobody feels is the
## caption this session exists to remove:
##
##   IT IS SAID.        The returned sentence is `hud.gd::did_text` and
##                      `arrival.gd::current_text`, so it is on the frame in two
##                      places without this session touching `hud.gd`.
##   SOMEBODY COMES.    `enforcement.gd::refuse_at` -- the same brig, ladder,
##                      fine and revocation `hud.gd`'s boundary check already
##                      routes into, opened by the customs verdict instead of by
##                      a rung comparison.
##   IT IS WRITTEN DOWN. Into the purse's own `record`, which
##                      `station/player.py::state()` already carries and
##                      `restore` already reads, and then to disk. A consequence
##                      that does not survive the process is a mood.
func _verb_operate(it: Item) -> String:
	if it.token != READER_TOKEN:
		# A named default rather than silence. `used_travel_mm` measures what the
		# press actually moved off the mesh's own AABB, so this is a claim about
		# the world and not a hopeful sentence.
		return "%s: the control moves under your hand" % it.label
	var holder = _card_owner()
	if holder == null or not holder.has_method("customs_verdict"):
		return ("%s: nothing in this build is carrying an identicard, so there "
			% it.label + "is no record to pull (this is a walk build, not an "
			+ "arrival)")
	var has_card := _carrying(_CARD_ITEM)
	var v: Dictionary = holder.call("customs_verdict", has_card, it.place)
	if v.is_empty():
		return "%s: the reader returned nothing" % it.label
	var status := String(v.get("status", ""))
	customs_reads += 1
	print("CUSTOMS place=%s who=%s npc=%s carrying_card=%s struck=%s "
		% [it.place, String(v.get("who", "?")), String(v.get("npc_id", "?")),
			str(has_card).to_lower(),
			("none" if (v.get("dropped", []) as Array).is_empty()
				else "+".join(PackedStringArray(v.get("dropped", []))))]
		+ "status=%s worst=%s at_station=%d(%s) baked=%s port=%s"
		% [status, String(v.get("worst", "")), int(v.get("at_station", 0)),
			String(v.get("station", "")), String(v.get("baked_status", "")),
			String(v.get("port", "?"))])
	_record_customs(v)
	if status == "admitted":
		var ok := "IDENTICARD ACCEPTED -- %s" % String(v.get("verdict", ""))
		_show_on_panel(ok)
		return ok
	# THE REFUSAL GOES SOMEWHERE. `refuse_at` returns false when this build has
	# no consequence table for the room, and the sentence says which of the two
	# happened rather than implying the first.
	# THE PLATE GOES UP BEFORE SECURITY IS CALLED, and the order is the point:
	# `refuse_at` -> `_open` -> `enforcement.gd::_say` writes SECURITY NOTIFIED
	# into the same field, so writing ours afterwards would paint over the thing
	# the refusal caused with the refusal itself.
	_show_on_panel("IDENTICARD REFUSED\n%s\nSTATION %d, %s"
		% [String(v.get("verdict", "")).to_upper(), int(v.get("at_station", 0)),
			String(v.get("station", "")).to_upper()])
	var came := false
	if _enforce != null and _enforce.has_method("refuse_at"):
		came = bool(_enforce.call("refuse_at", it.place,
			"the identicard did not read: station %d, %s"
				% [int(v.get("at_station", 0)), String(v.get("station", ""))]))
	return "IDENTICARD %s -- %s  (station %d, %s)%s" % [status.to_upper(),
		String(v.get("verdict", "")), int(v.get("at_station", 0)),
		String(v.get("station", "")),
		("  SECURITY NOTIFIED" if came else "  (nothing follows it here)")]


## The item a reader is looking for. `station/player.py::IDENTICARD`.
const _CARD_ITEM := "identicard"
## How many cards this session has put through a reader, for a gate to read.
var customs_reads := 0
## The last runtime verdict, kept as values so a save can carry it.
var _customs_last := {}


func _carrying(item: String) -> bool:
	if _player == null:
		return false
	var bag = _player.get("carrying")
	if typeof(bag) != TYPE_ARRAY and typeof(bag) != TYPE_PACKED_STRING_ARRAY:
		return false
	for x in bag:
		if String(x) == item:
			return true
	return false


## THE OUTCOME, INTO THE ONE DOCUMENT THAT OUTLIVES THE PROCESS.
##
## `record` is `station/player.py::state()`'s own key -- the same one `convict`
## and `_record_fine` write convictions and debts into, and the same one
## `Player.restore` reads back -- so a processed arrival comes back processed and
## a refused one comes back refused, with the station that refused them still on
## the record. NOT A NEW FILE and not a new key at the top of the ledger: a
## second place to look for "what happened to this person" is how a save ends up
## disagreeing with itself.
##
## `_save_ledger()` writes only when something moved, which is `interact.gd`'s
## standing rule -- a launch that reads no card leaves the document untouched.
func _record_customs(v: Dictionary) -> void:
	_customs_last = {
		"status": String(v.get("status", "")),
		"worst": String(v.get("worst", "")),
		"at_station": int(v.get("at_station", 0)),
		"station": String(v.get("station", "")),
		"place": String(v.get("place", "")),
		"why": String(v.get("why", "")),
		"struck": (v.get("dropped", []) as Array).duplicate(),
		"npc_id": String(v.get("npc_id", "")),
		"day": int(_led.get("day", 0)),
	}
	var rec := _record()
	rec["customs"] = _customs_last.duplicate(true)
	var seen: Array = rec.get("customs_history", [])
	seen.append(_customs_last.duplicate(true))
	rec["customs_history"] = seen
	# THE STATUS IS ON THE PURSE ITSELF AS WELL, because `player.py::Player.
	# status` is a field of the PERSON rather than of their record, and
	# `restore` reads it from there. Two writes, one fact, and they are the two
	# places Python already keeps it.
	var st := _my_purse()
	if not st.is_empty():
		st["status"] = String(v.get("status", ""))
	_put_record(rec)
	_save_ledger()
	print("interact: customs outcome written to %s -- record.customs.status=%s, "
		% [String(v.get("npc_id", "?")), String(v.get("status", ""))]
		+ "purse.status=%s, %d reading(s) on this card"
		% [String(st.get("status", "-")), seen.size()])


## The last runtime customs verdict, for a gate that would rather not parse a log.
func customs_status() -> String:
	return String(_customs_last.get("status", ""))


## THE PLATE ABOVE THE RETICLE, AND WHY THIS IS NOT A CHANGE TO `hud.gd`.
##
## `hud.gd::_check` already draws `check_text` -- above the reticle, AMBER unless
## the line begins `IDENTICARD ACCEPTED`, and its own comment says that plate is
## "the one message on this HUD that is about the player rather than about the
## world". A customs verdict is exactly that message. `enforcement.gd::_say`
## already writes into the same field from outside, so this is an established
## channel with an established owner and not a new one; what it needs is a
## SECOND writer, not a second plate, and a second plate is what an edit to
## `hud.gd` would most likely have produced.
##
## THE SENTENCE IS SHAPED SO THE COLOUR RULE ALREADY WORKS. `_verb_operate`
## returns `IDENTICARD ACCEPTED -- ...` on an admit and `IDENTICARD REFUSED --
## ...` otherwise, which is the two prefixes `hud.gd:466` and `hud.gd:468` write
## themselves. Nothing in `hud.gd` has to learn a third word.
##
## FOUND BY CAPABILITY, two properties deep, which is `_find_clock`'s rule one
## file up: `check_text` alone is not distinctive (this node has a `_hud` Label
## and `enforcement.gd` holds a reference), `check_text` + `tier` is.
var _panel = null
var _panel_looked := false


func _card_panel():
	if _panel != null or _panel_looked:
		return _panel
	_panel_looked = true
	var scene := get_tree().current_scene if get_tree() != null else null
	for root in [scene, get_parent()]:
		if root == null:
			continue
		var n := _search_panel(root, 0)
		if n != null:
			_panel = n
			print("interact: card panel at %s" % n.get_path())
			return n
	print("interact: no card panel in this build -- a customs verdict will be "
		+ "said under the prompt and not on the plate above the reticle")
	return null


func _search_panel(node: Node, depth: int) -> Node:
	if depth > 6:
		return null
	if node != self:
		var props := {"check_text": false, "tier": false}
		for e in node.get_property_list():
			var nm := String(e.get("name", ""))
			if props.has(nm):
				props[nm] = true
		if bool(props["check_text"]) and bool(props["tier"]):
			return node
	for c in node.get_children():
		var got := _search_panel(c, depth + 1)
		if got != null:
			return got
	return null


## How long the verdict stays up. Longer than `hud.gd::_CHECK_HOLD_S`'s 5 s on
## purpose: a boundary reading is a fact in passing and a customs verdict is the
## outcome of the last ten minutes.
const CUSTOMS_HOLD_S := 12.0


func _show_on_panel(line: String) -> void:
	var p = _card_panel()
	if p == null:
		return
	p.set("check_text", line)
	p.set("_check_until", CUSTOMS_HOLD_S)


## What the arrest chain did about it, in the words `enforcement.gd` counts in.
## Asked THROUGH this node rather than found again, because this node is the one
## that built the director and is the only one holding a reference to it.
func enforcement_report() -> String:
	if _enforce == null:
		return "enforcement is not in this build"
	if not _enforce.has_method("report"):
		return "enforcement is present and reports nothing"
	return String(_enforce.call("report"))


## What the last verb DID, in one sentence, held for a few seconds. `hud.gd`
## draws it under the prompt; the log line carries it as `DID=`.
var _said := ""
var _said_until := 0.0


func said() -> String:
	return _said


## What this person has been PAID, out of the same ledger the purse came from.
## `hud.gd` draws it under the balance; `economy.pay` is what puts it there and
## `dockwork.py`'s shift loop is what calls that.
func wages() -> float:
	if _player == null or _led.is_empty():
		return 0.0
	var w = _led.get("wages", {})
	if typeof(w) != TYPE_DICTIONARY:
		return 0.0
	return float(w.get(String(_player.npc_id), 0.0))


## The till at one place, for a gate to read back without parsing the file.
func till_at(place_key: String) -> float:
	var t = _led.get("till", {})
	if typeof(t) != TYPE_DICTIONARY:
		return -1.0
	return float(t.get(place_key, -1.0))


## What the last `read` said, and how long it stays up. Held rather than latched
## so a player who walks away is not still reading a board from ten metres.
var _read_text := ""
var _read_until := 0.0
const _read_hold_s := 6.0


## The text the last `read` produced, "" once it has timed out. `hud.gd` draws
## this under the prompt line.
func read_text() -> String:
	return _read_text


func _tick_read(delta: float) -> void:
	if _read_until > 0.0:
		_read_until -= delta
		if _read_until <= 0.0:
			_read_text = ""
	if _said_until > 0.0:
		_said_until -= delta
		if _said_until <= 0.0:
			_said = ""


var _used_prompt := ""
var _used_group := ""
var _used_verb := ""
var _used_responds := false
var _used_centre := Vector3.ZERO
var _used_travel_m := 0.0


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


# ===========================================================================
#  THE VERB CHECK -- run in the SHIPPED scene, on the SHIPPED streamed cells
# ===========================================================================
## WHY THIS IS HERE AND NOT IN A HARNESS. This project has produced TEN
## instances of finished machinery with no caller on the shipped path, and
## number ten was `main.gd` never setting `crowd_glbs` while a Python harness
## reported 963 walkers. The lesson `CLAUDE.md` draws from it is exact: *"a
## static scan can tell you a caller exists; only running the thing tells you
## the caller runs."*
##
## So the dispatch reports on itself, from inside the shipped scene, through
## `use()` -- the same function the `E` key calls and the same one
## `walk.gd::_try_use` calls after walking a body up to something. It picks its
## subjects out of `_items`, which are the interactables the STREAMED CELLS
## brought: nothing here loads a file, names a place, or builds an Item.
##
## `--verbcheck` GATES THE REPORT, NOT THE CODE. Without the flag this function
## never runs and the build behaves exactly as it did; with it, the dispatch
## that a keypress reaches is the dispatch that prints. The flag cannot make a
## verb work that would not work for a player -- it can only make one say so.
##
## WHAT IT DOES NOT PROVE, stated because the distinction is the whole reason
## the shipped launch is not sufficient on its own: it bypasses `scan()`, so it
## says nothing about whether the player could get close enough or was looking
## the right way. That is `walkable.py --deck ... --use`'s question and it is
## answered separately, by walking a body at a seat and letting the prompt fire.
func _verbcheck() -> void:
	if _vc_done or _player == null:
		return
	_vc_done = true
	# ONE OF EVERY (VERB, KIND), not one of every verb. `sit` reaches the
	# player's body down two different routes -- a `seat` is measured off its
	# own top and a `table` uses the fitted knee height -- and a check that
	# stopped at the first `sit` row would exercise whichever the deck happened
	# to list first and call the verb covered. Same argument as the one that
	# split layer 2: a criterion that cannot fail on the case you have is not
	# measuring the case you have.
	var seen := {}
	var n := 0
	for pass_i in 2:
		for it in _items:
			var want := "%s/%s" % [it.verb, it.kind]
			if seen.has(want) or not it.pressable:
				continue
			if it.verb == "open" or it.verb == "operate":
				continue                  # door.gd's, and the press travel's
			# THROUGH `use()`, NOT ROUND IT. `_prompt` is what `use()` acts on,
			# so setting it and calling the real function is the shortest path
			# that still runs every line a keypress runs -- the press travel,
			# the snapshot, the dispatch and the log line.
			_prompt = it
			_used_prompt = "[E]  %s the %s" % [it.verb, it.label]
			seen[want] = true
			n += 1
			use()
			# Stand up again, so a check does not leave the shipped build with
			# a seated player: `main.gd` reads `is_on_floor()` and the radial
			# drop at frame 120 and neither should learn about this.
			if String(_player.seated) != "":
				_prompt = it
				use()
	print("VERBCHECK items=%d verbs=%s exercised=%d sales=%d refusals=%d "
		% [_items.size(), verb_report(), n, sales, refusals]
		+ "carrying=%s credits=%s seated=%s" % [
			("-" if _player.carrying.is_empty()
				else ",".join(_player.carrying)),
			("-" if not _player.has_purse() else "%.3f" % _player.credits),
			("-" if String(_player.seated) == "" else String(_player.seated))])


var _vc_done := false
var _vc_frames := 0


func _physics_process(_delta: float) -> void:
	refresh()
	_tick_read(_delta)
	# AFTER THE CELLS HAVE LANDED, not on the first frame. A streamed build
	# wires its neighbours over the following seconds, so a check that fired at
	# frame 0 would report on the start cell alone and call the rest missing.
	if not _vc_done and _args().has("verbcheck"):
		_vc_frames += 1
		if _vc_frames >= 90:
			_verbcheck()
	# A PROMPT FOR SOMETHING THAT IS NO LONGER LOADED. `release()` clears it, so
	# on a correct build this is zero; with `--no-unwire` the Item survives its
	# cell and the eye happily offers to operate a console that has been
	# `queue_free`d. Counted here because the prompt is the one part of this file
	# a player actually reads.
	if _prompt != null and (_prompt.parts.is_empty()
			or not is_instance_valid(_prompt.parts[0])):
		stale_prompt_frames += 1
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
			if it == _last_used:
				_used_travel_m = it.travel_m


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


## WHAT WAS USED, FROM THE SNAPSHOT rather than from the Item. On a streamed
## build the object's cell may have been freed since -- see `use()`.
func used_group() -> String:
	return _used_group


func used_verb() -> String:
	return _used_verb


## Did the object the player used have a response behind it? Read off the
## sidecar row, so this cannot disagree with `station/interact.py::RESPONDS`.
func used_responds() -> bool:
	return _used_responds


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
	return _used_travel_m * 1000.0


## Distance from the player to the used object, for the gate to report.
func used_range_m() -> float:
	if _used_group == "" or _player == null:
		return -1.0
	return _player.global_position.distance_to(_used_centre)


## Is a named group among the interactables at all? The negative control strips
## one from the mesh, and this is what says so.
func has_group(g: String) -> bool:
	for it in _items:
		if it.group == g:
			return true
	return false


## WHY A NAMED GROUP IS NOT THE PROMPT, in the four terms `scan()` decides on.
##
## "Never prompted" is three different failures wearing one word -- it is not
## wired, you are not close enough, you are not looking at it, or something is in
## the way -- and a gate that cannot tell them apart sends the next reader to
## re-derive the scan by hand. Costs nothing: it is only called when a claim has
## already failed.
## The three numbers `scan()` decides on, for one group: eye range, degrees off
## the view axis, and whether the line of sight is clear. Sampled every frame by
## the streaming gate on a use leg, so a prompt that never fires reports the
## CLOSEST it ever came to firing rather than the state it happened to end in.
func probe_terms(g: String) -> Array:
	for it in _items:
		if it.group != g:
			continue
		if _player == null:
			return [-1.0, -1.0, false]
		var eye: Vector3 = _player.global_position
		var fwd := -_player.global_transform.basis.z
		if _cam != null:
			eye = _cam.global_position
			fwd = -_cam.global_transform.basis.z
		var to: Vector3 = it.centre - eye
		var d: float = to.length()
		if d < 1e-4:
			return [d, 180.0, false]
		var c: float = to.normalized().dot(fwd.normalized())
		return [d, rad_to_deg(acos(clampf(c, -1.0, 1.0))),
			_in_sight(eye, it, d)]
	return [-1.0, -1.0, false]


func probe(g: String) -> String:
	var it: Item = null
	for x in _items:
		if x.group == g:
			it = x
			break
	if it == null:
		return "not wired (%d interactable(s) present)" % _items.size()
	if _player == null:
		return "no player"
	var eye: Vector3 = _player.global_position
	var fwd := -_player.global_transform.basis.z
	if _cam != null:
		eye = _cam.global_position
		fwd = -_cam.global_transform.basis.z
	var to: Vector3 = it.centre - eye
	var d: float = to.length()
	var c: float = (to.normalized().dot(fwd.normalized()) if d > 1e-4 else -2.0)
	var bits := PackedStringArray()
	bits.append("pressable=%s" % str(it.pressable).to_lower())
	bits.append("eye_range=%.2fm/%.2f" % [d, reach_m])
	bits.append("off_axis=%.0fdeg/%.0f" % [rad_to_deg(acos(clampf(c, -1.0, 1.0))),
		look_half_deg])
	bits.append("in_sight=%s" % str(_in_sight(eye, it, d)).to_lower())
	# WHICH RAY, AND WHAT IT HIT. "in_sight=false" is two failures in one word:
	# something else on the interact layer is in front of it, or the walking
	# shell is.
	var space := get_world_3d().direct_space_state
	if space != null and it.body != null:
		var qa := PhysicsRayQueryParameters3D.create(eye, it.centre)
		qa.collision_mask = INTERACT_LAYER
		var a := space.intersect_ray(qa)
		bits.append("rayA=%s" % ("nothing" if a.is_empty()
			else String((a["collider"] as Node).name)))
		var qb := PhysicsRayQueryParameters3D.create(eye, it.centre)
		qb.collision_mask = 1
		var b := space.intersect_ray(qb)
		bits.append("rayB=%s" % ("nothing" if b.is_empty()
			else "%s@%.2fm" % [String((b["collider"] as Node).name),
				eye.distance_to(b["position"])]))
	if _prompt != null and _prompt != it:
		bits.append("prompt_is=%s" % _prompt.group)
	return ", ".join(bits)


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


# ===========================================================================
# WHAT A RELOAD HAS TO PUT BACK
#
# The LEDGER, and the counters that describe what the player did to it. The
# ledger is the station's money and stock -- every till's take, every counter's
# shelf -- and it is the one document here that a session genuinely mutates.
#
# THE LEDGER IS SAVED WHOLE, and that is a deliberate exception to this file's
# own rule against copying computed data into a snapshot. `station/economy.py`
# derives the OPENING ledger from the station's shops, wages and prices, so it
# is rebuildable -- but only its opening state. Once a player has bought
# something the document is no longer derivable from anything, because the
# purchase is not written down anywhere else. A save that carried only the
# purse would restore a player's money and refill every shop they emptied.
#
# `_led_dirty` is NOT saved. It is a question about this process's relationship
# to a file on disk, and a freshly loaded ledger's relationship to disk is
# "identical", whatever it was when the snapshot was taken.
# ===========================================================================

## AND THE CUSTOMS OUTCOME, WHICH NEEDS NO CHANGE TO `save.gd` AND GETS NONE.
## `save.gd` is duck-typed -- `capture()` calls `save_state()` on every subject
## `main.gd::_subjects` found, and this node is one of them (by `verb_report` +
## `pressable_count`). So a key added here is a key in the snapshot. It is also
## already inside `ledger` above, because `_record_customs` writes into the
## purse's record; it is repeated at the top level so a reload can report the
## verdict WITHOUT reconstructing a person from a wallet, and the two cannot
## drift because `load_state` re-reads the ledger's copy on the way back in.
func save_state() -> Dictionary:
	return {
		"ledger": _led.duplicate(true),
		"sales": sales,
		"refusals": refusals,
		"use_count": _use_count,
		"customs": _customs_last.duplicate(true),
		"customs_reads": customs_reads,
	}


func load_state(d: Dictionary) -> void:
	var led = d.get("ledger", null)
	if typeof(led) == TYPE_DICTIONARY and not led.is_empty():
		_led = led.duplicate(true)
		# THE PLAYER'S PURSE IS PUSHED BACK ONTO THE BODY, because `player.gd`
		# holds its own copy and `set_purse` is the only writer. Without this
		# the ledger says one thing and the HUD says another, which is the
		# disagreement `hud.gd` and `ambience.gd` already had over room extents.
		#
		# AND THIS COMMENT USED TO STATE THE LOAD ORDER AND STATE IT BACKWARDS.
		# It said *"`player.gd::load_state` runs first in `save.gd`'s ordering,
		# so ... this only re-asserts them from the authority"*. `save.gd::audit`
		# SORTS the subject names and `restore` walks the snapshot in that order,
		# so "interact" runs BEFORE "player" -- this file is first and
		# `player.gd` is last. A hostile verifier proved it with prints, and the
		# consequence was not cosmetic: `player.gd::load_state` overwrote the
		# rung this call had just derived with the number in the save file.
		#
		# THE FIX IS NOT AN ORDERING. `player.gd::load_state` now re-derives
		# through `set_purse` and stores no rung at all, so neither file depends
		# on going first. This call is still made, and still for the reason
		# above: the ledger is the authority on the MONEY, and a restored body
		# whose credits came from its own snapshot is a second copy of it.
		if _player != null and String(_player.npc_id) != "":
			var purse := _my_purse()
			if not purse.is_empty():
				_player.set_purse(purse)
		_led_dirty = false
	sales = int(d.get("sales", sales))
	refusals = int(d.get("refusals", refusals))
	_use_count = int(d.get("use_count", _use_count))
	customs_reads = int(d.get("customs_reads", customs_reads))
	# THE LEDGER'S COPY WINS, and the top-level one is the fallback. The record
	# inside the restored ledger is the same object `_record_customs` wrote and
	# the same one Python's `Player.restore` would read; taking that in
	# preference is what stops the snapshot's two copies becoming two answers.
	var from_led: Dictionary = _record().get("customs", {})
	if typeof(from_led) == TYPE_DICTIONARY and not from_led.is_empty():
		_customs_last = from_led.duplicate(true)
	else:
		var c = d.get("customs", null)
		if typeof(c) == TYPE_DICTIONARY:
			_customs_last = (c as Dictionary).duplicate(true)
	if not _customs_last.is_empty():
		print("interact: restored a customs outcome -- %s at %s (station %d, %s)"
			% [String(_customs_last.get("status", "?")),
				String(_customs_last.get("place", "?")),
				int(_customs_last.get("at_station", 0)),
				String(_customs_last.get("station", "?"))])
