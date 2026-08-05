extends Node3D
## SOMEBODY COMES -- what happens after a refusal, in the shipped scene.
##
## THE LIMIT THIS CLOSES IS WRITTEN IN THE FILE THAT SHIPPED IT. `hud.gd::
## _boundary` reads your identicard on the way into 98 of the register's 129
## places and its own comment says, in as many words:
##
##     "the arrest chain behind a refusal (`consequence.arrest` -> brig -> fine
##      -> release) is Python and stays there for now, so a refused player is
##      TOLD they are refused and is not yet detained. That is a real limit and
##      P2 owns closing it."
##
## A refusal a player can walk away from unharmed is a SIGN, not a rule. This is
## the thing that walks up to them.
##
## WHAT IS AND IS NOT IN THIS FILE, because the whole defect being closed is a
## rule that existed in two places. **There is no rule here.** Not the six-rung
## ladder, not the offence table, not the fine band, not where the brig is, not
## how long a hold runs, not whether a conviction costs you your visa. Every one
## of those is `station/consequence.py`'s and arrives BAKED, per place, in
## `station/generated/scene/enforcement.json` -- exactly the way `boot.py::
## _checks` bakes `certain_check`'s result rather than its rule. What is here is
## a state machine, a body walking across a floor, and four numbers of geometry
## that are measured off this build rather than written down.
##
## THE FOUR THINGS A PLAYER MEETS:
##
##   1. The reader refuses them (`hud.gd`, already shipped).
##   2. SECURITY IS NOTIFIED, and the wait is the place's own answer.
##      `security.response_from_nearest_post` routes from every fixed post on
##      the station: **0 s in `docking_bays`, which has a post standing in it,
##      227 s in `lowg_bays`, from customs north**. LAW-CRIME 2.6's headline is
##      a CONTRAST and this is that contrast as a countdown.
##   3. A PAIR ARRIVES AND THEY HAVE NAMES. One wears the Nightwatch armband and
##      one does not -- FACTIONS 5.3 -- and the body that walks in is an
##      instanced crowd walker driven by `npc.gd::drive_commuter`, the same
##      machinery a commuting resident uses, so the drawn body and the physics
##      capsule cannot disagree about where somebody is.
##   4. AND THEN SOMETHING HAPPENS TO YOU. Four times in five it is LAW-CRIME
##      2.7 rung 3 -- moved on, no arrest, no record -- and you are walked back
##      out of the room. The fifth time it is rung 4: booked, escorted to the
##      brig on the routed graph, held to the next Ombuds sitting, fined, and
##      released with a conviction on the card. The clock moves. The money goes.
##      The record is written into the purse and survives the process.
##
## WHY MOST REFUSALS COST NOTHING, stated because it looks like a bug and is the
## opposite. `consequence.DETAIN_ON_FAIL` is 0.20 and it is sourced: 2.7 calls
## rung 3 "the standard Downbelow-in-a-commercial-area outcome". A build that
## put every refusal in the brig would make the brig meaningless and would
## overflow its own sourced 24-40 cells inside a day -- `consequence.brig_check`
## fails when it does.
##
## THE GATE: `python3 station/enforcement.py --gate`. It launches the scene
## `godot/project.godot` actually ships -- no `--glb=`, no fixture -- drives the
## body across a real boundary until a refusal, and asserts that somebody came,
## covered ground getting there, and that the outcome reached the purse. Four
## controls, and the first of them (`--enforce-legacy`) is this repository
## yesterday: the refusal is reported and nothing follows it.

const DATA_REL := "../station/generated/scene/enforcement.json"

## HOW FAR AWAY THE PAIR BECOMES VISIBLE, in metres. NOT A NEW NUMBER: 12 m is
## `npc.gd::promote_walker`'s own default radius -- this project's existing
## answer to "how far away is somebody who is here with you", the distance
## inside which a collapsing body is a person who was standing there rather than
## a corpse appearing out of the air. The same question, so the same answer.
## Capped by the ray below, so an officer never appears through a wall.
const APPROACH_MAX_M := 12.0

## The reach at which the pair has ARRIVED. `interact.gd::reach_m` -- the
## distance at which a player can operate a thing -- because being close enough
## to be handed a citation is the same distance as being close enough to press
## a console, and a second constant here would be a second answer to one
## question.
const ARRIVE_M := 2.4

## How long each leg of the custody chain holds the interface, in seconds of
## wall clock. It is a READOUT, not a duration: the durations are the routed
## ones in the table and they are hours. Six lines at 1.4 s is nine seconds of
## reading, which is what a fade-to-black in this genre costs.
const LEG_DWELL_S := 1.4

## THE ONE THING A PLAYER CAN SEE THAT IS NOT DERIVED, and it is here so it can
## be argued with: the response countdown runs in REAL seconds by default, so a
## 227 s turn-out to `lowg_bays` is 227 seconds of a player standing in a room
## they were told to leave. `--arrest-rate=N` compresses it and every verdict
## line PRINTS the rate it ran at, because a tool that can substitute a lesser
## mode for the one asked for must say which one it used.
var rate: float = 1.0

var _player: Node3D
var _interact: Node                  ## the ledger's one writer -- see `fine()`
var _hud                             ## untyped: `check_text` is on the script
var _crowd: Node                     ## npc.gd -- add_commuter / drive_commuter
var _clock: Node                     ## life.gd's Director -- hour() / apply()

var _data: Dictionary = {}
var _places: Dictionary = {}
var _looked := false

## How many times this player has been stopped at each place. The index into the
## baked fork and into the conviction ladder -- a second stop is a second draw
## and, if it detains, a second conviction.
var _stops: Dictionary = {}

enum {IDLE, CALLED, APPROACH, VERDICT, CUSTODY, DONE}
var state := IDLE
var _place := ""
var _t := 0.0
var _wait_s := 0.0
var _row: Dictionary = {}
var _officer = null                  ## npc.gd's Walker, or null
var _officer_at := Vector3.ZERO
var _officer_from := Vector3.ZERO
var _officer_m := 0.0                ## GROUND COVERED, not "did it move"
var _leg := 0
var _legs: Array = []

# -- what a gate reads back ------------------------------------------------
var refused := 0
var responded := 0
var arrived := 0
var moved_on := 0
var detained := 0
var credits_before := -1.0
var credits_after := -1.0
var hour_before := -1.0
var hour_after := -1.0
var last_line := ""
var last_why := ""


func _ready() -> void:
	var a := _args()
	if a.has("arrest-rate"):
		rate = maxf(0.01, float(a["arrest-rate"]))
	_load()


func bind(body: Node3D, interact: Node) -> void:
	_player = body
	_interact = interact


## THE TABLE, AND THE ENGINE HOLDS NOTHING ELSE. Absent, this node is inert and
## says so once -- the same statement `interact.gd` makes when there is no
## ledger, and for the same reason: a build with no consequence data must not
## invent one, it must report that nobody computed it.
func _load() -> void:
	if _args().has("enforce-legacy"):
		print("enforcement: DISABLED (control) -- a refusal is reported and "
			+ "nothing follows it. This is the build before session 4r.")
		return
	var p := ProjectSettings.globalize_path("res://").path_join(
		DATA_REL).simplify_path()
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		print("enforcement: no %s -- a refusal will be reported and nothing "
			% p + "will follow it. Run `python3 station/enforcement.py --bake`")
		return
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		push_error("enforcement: %s is not a JSON object" % p)
		return
	_data = d
	_places = d.get("places", {})
	print("enforcement: %d place(s) carry a consequence, for %s (rung %d %s), "
		% [_places.size(), String((d.get("player", {}) as Dictionary).get(
			"name", "?")), int((d.get("player", {}) as Dictionary).get(
			"tier", -99)), String((d.get("player", {}) as Dictionary).get(
			"tier_name", "?"))]
		+ "response %s" % _spread())


## The contrast, printed on every run, because one number would hide it.
func _spread() -> String:
	var lo := INF
	var hi := -INF
	var lo_k := ""
	var hi_k := ""
	for k in _places:
		var s := float((_places[k] as Dictionary).get("respond_s", 0.0))
		if s < lo:
			lo = s
			lo_k = String(k)
		if s > hi:
			hi = s
			hi_k = String(k)
	if lo_k == "":
		return "(none)"
	return "%.0f s (%s) .. %.0f s (%s)" % [lo, lo_k, hi, hi_k]


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if not s.begins_with("--"):
			continue
		var b := s.substr(2)
		var eq := b.find("=")
		if eq < 0:
			out[b] = "1"
		else:
			out[b.substr(0, eq)] = b.substr(eq + 1)
	return out


# ===========================================================================
#  FINDING THE THREE THINGS THIS NEEDS, BY CAPABILITY AND NOT BY NAME
# ===========================================================================
# `interact.gd::_find_clock` records why: a node found by name breaks the day
# somebody renames it, and a node found by ONE method finds a follower. Each
# search below names two capabilities that only the intended node has.
func _look() -> void:
	if _looked:
		return
	_looked = true
	var roots := []
	var tree := get_tree()
	if tree != null and tree.current_scene != null:
		roots.append(tree.current_scene)
	if get_parent() != null:
		roots.append(get_parent())
	for r in roots:
		if _hud == null:
			_hud = _find(r, ["check_text", "tier"], [], 6)
		if _crowd == null:
			_crowd = _find(r, [], ["add_commuter", "drive_commuter"], 6)
		if _clock == null:
			_clock = _find(r, [], ["hour", "apply"], 6)
	print("enforcement: hud=%s crowd=%s clock=%s"
		% [_hud != null, _crowd != null, _clock != null])


func _find(n: Node, props: Array, methods: Array, depth: int):
	if depth < 0 or n == null:
		return null
	if n != self:
		var good := true
		for m in methods:
			if not n.has_method(String(m)):
				good = false
		for p in props:
			var plist := n.get_property_list()
			var seen := false
			for e in plist:
				if String(e.get("name", "")) == String(p):
					seen = true
			if not seen:
				good = false
		if good and (not props.is_empty() or not methods.is_empty()):
			return n
	for c in n.get_children():
		var got = _find(c, props, methods, depth - 1)
		if got != null:
			return got
	return null


# ===========================================================================
#  THE MACHINE
# ===========================================================================
func _physics_process(delta: float) -> void:
	if _places.is_empty() or _player == null:
		return
	_look()
	if _hud == null:
		return
	match state:
		IDLE, DONE:
			_watch()
		CALLED:
			_wait(delta)
		APPROACH:
			_walk_in(delta)
		VERDICT:
			_verdict()
		CUSTODY:
			_custody(delta)


## THE TRIGGER IS THE HUD'S OWN READING AND NOT A SECOND LOOK-UP. `hud.gd`
## resolves the place, applies the baked check and writes the sentence; this
## reacts to the sentence. A second evaluation of "does this place admit me"
## here would be exactly the duplication that made two halves of one crowd
## disagree about which way round a person is.
func _watch() -> void:
	var txt := String(_hud.get("check_text"))
	var here := String(_hud.get("_check_place"))
	if not txt.begins_with("IDENTICARD REFUSED"):
		if state == DONE and here == "":
			state = IDLE               # stepped back into the corridor: re-armed
		return
	if here == "" or not _places.has(here):
		return
	if state == DONE and here == _place:
		return
	_open(here)


func _open(key: String) -> void:
	_place = key
	_row = _places[key]
	refused += 1
	var n := int(_stops.get(key, 0))
	_stops[key] = n + 1
	_wait_s = float(_row.get("respond_s", 0.0)) / rate
	_t = 0.0
	state = CALLED
	var who := _pair()
	print("ARREST refused at %s -- %s notified, %.0f s away (%s)"
		% [key, who, float(_row.get("respond_s", 0.0)),
			String(_row.get("respond_from", "?"))])
	_say("SECURITY NOTIFIED\n%s -- %s, %s"
		% [who.to_upper(), String(_row.get("respond_from_name", "")).to_upper(),
			_mmss(float(_row.get("respond_s", 0.0)))])


func _pair() -> String:
	var names := []
	for o in (_row.get("officers", []) as Array):
		names.append(String((o as Dictionary).get("name", "?"))
			+ ("*" if bool((o as Dictionary).get("armband", false)) else ""))
	return " + ".join(names)


func _mmss(s: float) -> String:
	if s < 1.0:
		return "ALREADY HERE"
	return "ETA %d:%02d" % [int(s) / 60, int(s) % 60]


func _wait(delta: float) -> void:
	_t += delta
	if _t < _wait_s:
		return
	responded += 1
	_spawn()
	state = APPROACH


# ---------------------------------------------------------------------------
#  THE BODY THAT COMES
# ---------------------------------------------------------------------------
## WHERE THEY APPEAR IS MEASURED OFF THIS BUILD, NOT WRITTEN DOWN. A point
## chosen on paper appears inside a wall on some deck, and this repository's own
## history is a list of exactly that. So: thirteen casts from the player's chest
## across the quadrant facing the way out, the pair placed at the last clear
## metre of the longest of them, and the floor found under that by a second
## cast. They then walk a straight line that has ALREADY BEEN PROVEN CLEAR by
## the cast that placed them.
func _spawn() -> void:
	var eye: Vector3 = _player.global_position + _player.body_up() * 1.2
	var pair := _clearest(eye, _out_dir())
	var to_out: Vector3 = pair[0]
	var want: float = pair[1]
	_officer_from = _foot(eye + to_out * want)
	_officer_at = _officer_from
	_officer_m = 0.0
	if _crowd == null or _args().has("enforce-no-officer"):
		print("ARREST no body -- %s"
			% ("crowd node absent" if _crowd == null
				else "--enforce-no-officer (control)"))
		return
	var sp := "human"
	var offs: Array = _row.get("officers", [])
	if not offs.is_empty():
		sp = String((offs[0] as Dictionary).get("species", "human"))
	_officer = _crowd.call("add_commuter", {
		"species": sp, "lod": 8, "phase": 0,
		"x": _officer_at.x, "y": _officer_at.y, "z": _officer_at.z,
		"r_m": 0.36, "h_m": 1.75, "cycle_s": 1.0,
		"speed_ms": float(_data.get("walk_speed_ms", 1.30))})
	print("ARREST %s arriving %.1f m away, at %.2f m/s"
		% [_pair(), _officer_from.distance_to(_player.global_position),
			float(_data.get("walk_speed_ms", 1.30))])


## The way OUT of the place the player is standing in: the shortest HORIZONTAL
## axis of its own box, pointing away from the centre.
##
## HORIZONTAL IS THE WHOLE OF THIS FUNCTION AND ITS ABSENCE COST A GATE RUN.
## `main.gd::_check_gate` takes the shortest axis of the AABB with no such test,
## which is right for what it does -- it TELEPORTS a body to a standoff and the
## axis is only a direction to come from. Here the direction is walked, and on a
## ring deck at 264.8 deg the thinnest axis of a docking bay's world-aligned box
## is the RADIAL one. The pair was placed 2.9 m straight up, the floor cast
## under them fell short of the deck, and they arrived having walked
## **0.0 m** -- which the verdict caught and printed, because a walk gate that
## reports "did it move" instead of DISTANCE COVERED is this project's own
## recorded mistake from session 3v.
func _out_dir() -> Vector3:
	var up: Vector3 = _player.body_up()
	var b = (_hud.get("_boxes") as Dictionary).get(_place)
	var p: Vector3 = _player.global_position
	if typeof(b) != TYPE_ARRAY:
		# No box for this place: leave along the deck's own tangent, which is
		# the corridor, rather than guessing a compass direction.
		return up.cross(Vector3(0, 0, 1)).normalized()
	var lo: Vector3 = (b as Array)[0]
	var hi: Vector3 = (b as Array)[1]
	var size: Vector3 = hi - lo
	var c: Vector3 = (lo + hi) * 0.5
	var ax := -1
	for i in 3:
		var axis := Vector3.ZERO
		axis[i] = 1.0
		if absf(axis.dot(up)) > 0.7:          # this one is up, not out
			continue
		if ax < 0 or size[i] < size[ax]:
			ax = i
	if ax < 0:
		return up.cross(Vector3(0, 0, 1)).normalized()
	var d := Vector3.ZERO
	d[ax] = (1.0 if p[ax] >= c[ax] else -1.0)
	d -= up * d.dot(up)
	return d.normalized()


## The clearest way out within a quadrant of `want_dir`, and how far it runs.
##
## A DOORWAY IS NOT IN ANY TABLE THIS BUILD READS, so it is found by looking:
## thirteen casts at 15 deg from the player's chest, and the one with the
## longest clear run is the way out of a bay. That is measured off the collision
## the player is standing on -- the same rule `collision.py` applies to the
## corridor profile, "measured off the kit by ray casting, never written down,
## so it cannot drift from what it stands in for".
##
## Bounded to +-90 deg of the box-exit direction so the pair still comes from
## OUTSIDE: the longest clear run in an open bay is down its own length, and a
## patrol arriving from the far end of the room they are throwing you out of
## reads as a patrol that was already inside.
func _clearest(eye: Vector3, want_dir: Vector3) -> Array:
	var up: Vector3 = _player.body_up()
	var space := get_world_3d().direct_space_state
	var best := want_dir
	var best_m := 0.0
	for i in range(-6, 7):
		var d: Vector3 = want_dir.rotated(up, deg_to_rad(15.0 * float(i)))
		var q := PhysicsRayQueryParameters3D.create(eye, eye + d * APPROACH_MAX_M)
		q.collision_mask = 1
		q.exclude = [_player.get_rid()]
		var hit := space.intersect_ray(q)
		var run := (APPROACH_MAX_M if hit.is_empty()
			else eye.distance_to(hit["position"]) - 0.6)
		if run > best_m:
			best_m = run
			best = d
	return [best, clampf(best_m, ARRIVE_M + 0.5, APPROACH_MAX_M)]


## Put a point on the floor under itself. A body handed a position 1.2 m up
## walks in the air, and this deck's "down" is a radius rather than -Y.
## AND THE FALLBACK IS NOT THE PLAYER'S OWN POSITION, which is what it was and
## what made the first failure read as zero distance rather than as a missed
## cast. Falling back to where the player stands COLLAPSES the thing being
## measured: the pair arrives instantly, `walked` is 0.0, and the number that
## should say "the cast missed" says "they were already here". The honest
## fallback keeps the horizontal offset and takes the height from the body that
## is demonstrably standing on a floor.
func _foot(p: Vector3) -> Vector3:
	var up: Vector3 = _player.body_up()
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(p + up * 2.0, p - up * 4.0)
	q.collision_mask = 1
	q.exclude = [_player.get_rid()]
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		return hit["position"]
	var here: Vector3 = _player.global_position
	var off := p - here
	return here + (off - up * off.dot(up))


## NOBODY COMES, NOTHING ARRIVES, AND THE VERDICT STILL LANDS -- which is what
## `--enforce-no-officer` produces and why the gate must fail on it. A
## consequence delivered by nobody is a caption, and a caption is what this file
## exists to stop being the answer. So the control's run reaches VERDICT (the
## money and the clock still move, so the failure is isolated to the BODY) and
## `arrived` stays at zero, which is the term the verdict tests.
func _walk_in(delta: float) -> void:
	var to: Vector3 = _player.global_position - _officer_at
	var up: Vector3 = _player.body_up()
	to -= up * to.dot(up)
	var d := to.length()
	var step: float = float(_data.get("walk_speed_ms", 1.30)) * delta * rate
	if d > ARRIVE_M:
		step = minf(step, d - ARRIVE_M)
		_officer_at += to.normalized() * step
		_officer_m += step
		if _officer != null and _crowd != null:
			_crowd.call("drive_commuter", _officer, _officer_at,
				to.normalized(), step)
		return
	if _officer != null:
		arrived += 1
		print("ARREST arrived -- %.2f m from the player, %.1f m of floor "
			% [d, _officer_m] + "covered by a body in the crowd")
	else:
		print("ARREST NOBODY CAME -- %s. The verdict below is a caption."
			% ("--enforce-no-officer (control)"
				if _args().has("enforce-no-officer")
				else "this build has no crowd node"))
	state = VERDICT


# ---------------------------------------------------------------------------
#  WHAT THEY DO WHEN THEY GET THERE
# ---------------------------------------------------------------------------
func _verdict() -> void:
	var nth := int(_stops.get(_place, 1)) - 1
	var det: Array = _row.get("detained", [])
	# THE TABLE CARRIES THREE STOPS AND A PLAYER CAN MAKE A FOURTH. It CYCLES
	# rather than going quiet: a fourth refusal that could never detain is a
	# rule that switches itself off the moment somebody tests it, which is worse
	# than either answer. Cycling reuses the same draws in the same order, so it
	# stays deterministic and keeps the one-in-five over a long session.
	var will := (not det.is_empty() and bool(det[nth % det.size()]))
	if _args().has("enforce-no-detain"):
		will = false
	if not will:
		moved_on += 1
		var mo: Dictionary = _row.get("moved_on", {})
		last_line = String(mo.get("disposal", "moved on"))
		last_why = String(mo.get("line", ""))
		print("ARREST moved on at %s -- %s (%s)" % [_place, last_line, last_why])
		_say("MOVED ON\n%s" % last_why.to_upper())
		_escort_out()
		_dismiss()
		state = DONE
		return
	detained += 1
	_legs = _chain()
	_leg = 0
	_t = 0.0
	_shot()
	credits_before = float(_player.get("credits"))
	hour_before = (float(_clock.call("hour")) if _clock != null else -1.0)
	state = CUSTODY
	_say("DETAINED\n%s" % String(_legs[0]).to_upper())


## The custody chain as lines, straight off the baked table. Every duration in
## it was routed by `consequence.arrest` on the graph a resident commutes on;
## nothing here adds anything up except the hour index, which is the one leg
## that moves with the clock.
func _chain() -> Array:
	var d: Dictionary = _row.get("detention", {})
	var legs: Dictionary = d.get("legs", {})
	var h := 13
	if _clock != null:
		h = int(floor(fposmod(float(_clock.call("hour")), 24.0)))
	var hold: Array = d.get("hold_s_h", [])
	var hold_s := (float(hold[h]) if h < hold.size() else 0.0)
	var total: Array = d.get("total_s_h", [])
	var total_s := (float(total[h]) if h < total.size() else 0.0)
	var c: Dictionary = _outcome()
	var offs: Dictionary = _data.get("offence", {})
	var row: Dictionary = offs.get(String(d.get("offence", "")), {})
	var card := "CARD ENDORSED"
	if bool(c.get("revoked", false)):
		card = "STANDING WITHDRAWN: %s -> %s" % [
			String(c.get("tier_before_name", "")).to_upper(),
			String(c.get("tier_after_name", "")).to_upper()]
	return [
		"IDENTICARD SEIZED -- %s" % String(row.get("source", "")).left(64),
		"ESCORTED TO THE BRIG -- %.1f min on the routed graph"
			% (float(legs.get("escort_s", 0.0)) / 60.0),
		"BOOKED -- %.0f min" % (float(legs.get("booking_s", 0.0)) / 60.0),
		"HELD TO THE NEXT OMBUDS SITTING -- %.1f h" % (hold_s / 3600.0),
		"OMBUDS COURT -- %s" % String(c.get("reason", "")).left(64),
		"FINE %.2f CR -- %s" % [float(c.get("fine", 0.0)),
			String(c.get("disposal", "")).to_upper()],
		"RELEASED -- %.1f h in custody, %s" % [total_s / 3600.0, card],
	]


## Which rung of the conviction ladder this is, at the rung the card ACTUALLY
## reads. The engine may be running with `--tier=N` forcing the card, and
## `consequence._dispose` answers differently at every rung: EA citizenship
## cannot be withdrawn by an Ombuds at all, and the floor rung has nothing left
## to take -- 4.3 step 6's next disposal is transfer off-station.
##
## WHAT NO NUMBER OF REFUSALS DOES IS COST YOU YOUR STANDING, and that is the
## answer rather than a gap. `Record.ordinary()` counts grade-2 convictions and
## `id_check_fail` is grade 1 -- INV-347 prices it at one day of casual labour,
## a citation. A station that withdrew a transit visa for two citations would
## have no middle to its own escalation. Revocation is a grade-2 conviction, a
## different verb, and another session's work. `enforcement.py --selftest`
## asserts this at all six rungs with a grade-2 positive control beside it, so
## "it never revokes" cannot quietly become "the machinery is absent".
func _outcome() -> Dictionary:
	var d: Dictionary = _row.get("detention", {})
	var t := int(_player.get("tier"))
	var by: Dictionary = d.get("ladder_by_tier", {})
	var seq: Array = by.get(str(t), d.get("ladder", []))
	if seq.is_empty():
		return {}
	var i := mini(_convictions(), seq.size() - 1)
	return seq[i] as Dictionary


## How many convictions this player already carries. From the PURSE, because
## that is what survives the process -- `player.py::state()` writes `record` and
## `restore` reads it back, so a session that quits after one detention comes
## back one conviction in.
func _convictions() -> int:
	if _interact != null and _interact.has_method("convictions"):
		return int(_interact.call("convictions"))
	return 0


func _custody(delta: float) -> void:
	_t += delta * rate
	if _t < LEG_DWELL_S:
		return
	_t = 0.0
	_leg += 1
	if _leg < _legs.size():
		print("ARREST   %s" % String(_legs[_leg]))
		_say("IN CUSTODY\n%s" % String(_legs[_leg]).to_upper())
		return
	_settle()
	state = DONE


## WHERE THE MONEY, THE TIME AND THE RECORD ACTUALLY GO.
##
## THE LEDGER HAS ONE WRITER. `interact.gd` owns `economy.json` -- it reads the
## purse, hands it to the body, and writes it back -- so the fine is posted
## THROUGH it rather than beside it. That is the same rule `hud.gd` learned when
## its room extents disagreed with `ambience.gd`'s by 31.6 m, and it is the rule
## `consequence._post_fine` already follows on the Python side: a fine is a
## transfer to the court in the ledger a drink moves through, not a new wallet.
func _settle() -> void:
	var c: Dictionary = _outcome()
	var d: Dictionary = _row.get("detention", {})
	var legs: Dictionary = d.get("legs", {})
	var h := 13
	if _clock != null:
		h = int(floor(fposmod(float(_clock.call("hour")), 24.0)))
	var total: Array = d.get("total_s_h", [])
	var total_s := (float(total[h]) if h < total.size() else 0.0)

	# 1. THE CLOCK. A hold that does not move the station clock is a caption.
	if _clock != null:
		var now := float(_clock.call("hour"))
		var then := fposmod(now + total_s / 3600.0, 24.0)
		var ck = _clock.get("clock")
		if ck != null and ck.has_method("set_hour"):
			ck.call("set_hour", then)
		_clock.call("apply", then)
		hour_after = float(_clock.call("hour"))
		print("ARREST clock %05.2f -> %05.2f EMT (%.1f h in custody)"
			% [now, hour_after, total_s / 3600.0])

	# 2. THE MONEY, and it is the same purse a drink comes out of.
	var fine := float(c.get("fine", 0.0))
	if _interact != null and _interact.has_method("fine") and fine > 0.0:
		var paid: bool = _interact.call("fine", fine,
			String(_data.get("court", "law_courts")),
			String(d.get("offence", "")))
		print("ARREST fine %.2f cr %s -- %.2f cr left"
			% [fine, ("paid" if paid else "OUTSTANDING"),
				float(_player.get("credits"))])
	credits_after = float(_player.get("credits"))

	# 3. THE RECORD AND THE RUNG. Written into the purse, so it survives.
	if _interact != null and _interact.has_method("convict"):
		_interact.call("convict", String(d.get("offence", "")), fine,
			bool(c.get("revoked", false)), int(c.get("tier_after", -99)),
			String(c.get("tier_after_name", "")))
	last_line = String(c.get("disposal", ""))
	last_why = String(c.get("reason", ""))

	# 4. AND YOU ARE NOT WHERE YOU WERE. Released into the corridor, because the
	#    brig is a real place in the register and it is 6 km and four decks from
	#    this one -- teleporting a body into a cell that has not streamed drops
	#    it through the world. The escort is reported in minutes and not walked,
	#    which is a real limit and is printed rather than hidden.
	_escort_out()
	_dismiss()
	var seen := "%.2f CR PAID, CONVICTION ON THE CARD" % fine
	if bool(c.get("revoked", false)):
		seen = "%s -- STANDING WITHDRAWN" % String(
			c.get("tier_after_name", "")).to_upper()
	_say("RELEASED\n%s" % seen)


## Walked back out of the room, which is the whole of rung 3 and the end of
## rung 4. The point is the one the ray that placed the officer already proved
## clear, so a player is never pushed into a wall.
func _escort_out() -> void:
	if _player == null:
		return
	_player.global_position = _outside()
	_player.set("velocity", Vector3.ZERO)


## A point demonstrably OUTSIDE the place's own box, on the floor, with a clear
## line to it. Derived from the box `hud.gd` will test the player against next
## frame, so "you are out" is the same statement the reader makes -- otherwise a
## player escorted to 12 m that happened to still be inside would be refused
## again on the next frame, for ever.
func _outside() -> Vector3:
	var b = (_hud.get("_boxes") as Dictionary).get(_place)
	var dir := _out_dir()
	var p: Vector3 = _player.global_position
	var want := APPROACH_MAX_M
	if typeof(b) == TYPE_ARRAY:
		var lo: Vector3 = (b as Array)[0]
		var hi: Vector3 = (b as Array)[1]
		var ax := 0
		for i in 3:
			if absf(dir[i]) > absf(dir[ax]):
				ax = i
		# The wall plus `hud.gd::_resolve`'s own 1.5 m of slack, plus a metre so
		# a body standing on the line is not a coin toss.
		var wall: float = (hi[ax] if dir[ax] > 0.0 else lo[ax])
		want = absf(wall - p[ax]) + 2.5
	var eye: Vector3 = p + _player.body_up() * 1.2
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(eye, eye + dir * want)
	q.collision_mask = 1
	q.exclude = [_player.get_rid()]
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		want = maxf(0.5, eye.distance_to(hit["position"]) - 0.6)
	return _foot(eye + dir * want)


func _dismiss() -> void:
	if _officer != null and _crowd != null and _crowd.has_method("release_crowd"):
		# A commuter admitted with no tag cannot be released by tag, so the pair
		# is hidden instead: `_place_crowd` skips a hidden walker entirely, which
		# is `npc.gd`'s own "away" state and costs nothing.
		_officer.set("hidden", true)
		if _crowd.has_method("_place_crowd"):
			_crowd.call("_place_crowd")
	_officer = null


## A FRAME WITH THE WORDS ON IT, at the detention and nowhere else.
##
## `get_root().get_texture()` and not `get_viewport()`, for `main.gd::
## _check_gate`'s reason: a CanvasLayer is not in the 3D viewport's texture, and
## a shot that missed the interface would be a picture proving the opposite of
## what it was taken for. One per run -- six copies of one argument is not six
## arguments. Needs a real renderer; under `--headless` it says so rather than
## writing a black PNG, because a tool that silently degrades manufactures
## evidence.
var _shot_done := false


func _shot() -> void:
	var a := _args()
	if _shot_done or not a.has("arrest-shot"):
		return
	_shot_done = true
	_say("DETAINED\n%s" % String(_legs[0]).to_upper())
	if DisplayServer.get_name() == "headless":
		print("ARREST shot=SKIPPED -- this run is --headless and has no "
			+ "renderer; a black PNG would be evidence of nothing")
		return
	await RenderingServer.frame_post_draw
	var img := get_tree().get_root().get_texture().get_image()
	var png := String(a["arrest-shot"])
	if img.save_png(png) == OK:
		print("ARREST shot=%s %dx%d -- %s"
			% [png, img.get_width(), img.get_height(),
				String(_legs[0]).left(60)])
	else:
		print("ARREST shot=FAILED to write %s" % png)


func _say(s: String) -> void:
	if _hud == null:
		return
	_hud.set("check_text", s)
	_hud.set("_check_until", LEG_DWELL_S / maxf(rate, 0.01) + 0.5)


func report() -> String:
	return ("refused=%d responded=%d arrived=%d moved_on=%d detained=%d "
		% [refused, responded, arrived, moved_on, detained]
		+ "walked=%.1f rate=%.1f" % [_officer_m, rate])


# ===========================================================================
#  THE GATE -- driven from here, because this node is the thing being tested
# ===========================================================================
# WHY NOT IN `main.gd`. Its `_check_gate` is the right shape and the wrong owner:
# the flag that turns this on has to be readable by whatever this session added,
# and `main.gd` is not this session's file. `OS.get_cmdline_user_args()` is
# global, so a gate can live in the node it gates -- which also means the gate
# cannot pass on a build where this node was never instantiated, and that is the
# whole class of defect being closed.
var _gate_ran := false
var _gate_t := 0.0
var _gate_k := ""
var _gate_out := Vector3.ZERO
var _gate_step := 0
var _gate_walked := 0.0
var _gate_visits := 0
var _gate_cr0 := -1.0
var _gate_h0 := -1.0
var _gate_where0 := Vector3.ZERO

const GATE_SETTLE := 30
const GATE_VISITS := 3          ## enough stops for the fork to show both faces
const GATE_TIMEOUT_S := 240.0


func gate_wanted() -> bool:
	return _args().has("arrest-gate")


func run_gate() -> void:
	if _gate_ran:
		return
	_gate_ran = true
	rate = maxf(rate, float(_args().get("arrest-rate", "40")))
	for _i in GATE_SETTLE:
		await get_tree().physics_frame
	_look()
	if _player == null or _hud == null:
		print("ARREST gate=FAIL -- no %s in the shipped scene"
			% ("player" if _player == null else "hud"))
		get_tree().quit(1)
		return
	if _args().has("tier"):
		var t := int(_args()["tier"])
		_player.set("tier", t)
		_player.set("tier_name", "forced_%d" % t)
		print("ARREST control: the card now reads tier %d" % t)
	# THE TABLE'S ABSENCE GETS ITS OWN SENTENCE. Without it the run falls into
	# "nothing on this deck refuses this card", which is a statement about the
	# CARD and would send the next reader to the wrong half of the system.
	if _places.is_empty():
		print("ARREST gate=FAIL -- this build carries no consequence table, so "
			+ "a refusal is reported and nothing follows it")
		get_tree().quit(1)
		return

	# WHICH PLACE. The one on this deck that the card is refused from and whose
	# baked fork contains BOTH answers, so one run shows rung 3 and rung 4 --
	# a gate that only ever saw a detention could not tell a fork from a
	# constant. Chosen from the table rather than named here.
	_gate_k = _pick()
	if _gate_k == "":
		print("ARREST gate=FAIL -- nothing on this deck refuses a tier-%d card"
			% int(_player.get("tier")))
		get_tree().quit(1)
		return
	_gate_cr0 = float(_player.get("credits"))
	_gate_h0 = (float(_clock.call("hour")) if _clock != null else -1.0)
	print("ARREST gate: %s, rung %d(%s) against need %d, response %.0f s at "
		% [_gate_k, int(_player.get("tier")), String(_player.get("tier_name")),
			int((_places[_gate_k] as Dictionary).get("need", 0)),
			float((_places[_gate_k] as Dictionary).get("respond_s", 0.0))]
		+ "x%.0f" % rate)

	var t0 := Time.get_ticks_msec()
	for v in GATE_VISITS:
		await _visit()
		if (Time.get_ticks_msec() - t0) / 1000.0 > GATE_TIMEOUT_S:
			break
	_finish(true)


## The place with the most informative fork: both a moved-on and a detention
## inside the first `GATE_VISITS` stops, and refused by the card we hold.
func _pick() -> String:
	var tier := int(_player.get("tier"))
	var boxes: Dictionary = _hud.get("_boxes")
	var best := ""
	for k in _places:
		var r: Dictionary = _places[k]
		if tier >= int(r.get("need", 0)):
			continue
		if not boxes.has(k):
			continue
		if best == "":
			best = String(k)
		var det: Array = r.get("detained", [])
		var yes := 0
		var no := 0
		for i in mini(det.size(), GATE_VISITS):
			if bool(det[i]):
				yes += 1
			else:
				no += 1
		if yes > 0 and no > 0:
			return String(k)
	return best


## One crossing: stand outside the box, walk in until the reader speaks, then
## let the machine run to DONE. TWELVE STEPS, like `main.gd::_check_gate`, so
## the body is genuinely outside on step 0 and genuinely inside at the end -- a
## teleport onto the centre would prove the table can be looked up and would say
## nothing about a transition.
func _visit() -> void:
	var b: Array = (_hud.get("_boxes") as Dictionary)[_gate_k]
	var lo: Vector3 = b[0]
	var hi: Vector3 = b[1]
	var c: Vector3 = (lo + hi) * 0.5
	var size: Vector3 = hi - lo
	var ax := 0
	if size.y < size[ax]:
		ax = 1
	if size.z < size[ax]:
		ax = 2
	var dir := Vector3.ZERO
	dir[ax] = 1.0
	_gate_out = c + dir * (size[ax] * 0.5 + 4.0)
	_player.global_position = _gate_out
	_player.set("velocity", Vector3.ZERO)
	await get_tree().physics_frame
	await get_tree().process_frame
	_gate_where0 = _player.global_position
	for i in range(1, 13):
		_player.global_position = _gate_out.lerp(c, float(i) / 12.0)
		_player.set("velocity", Vector3.ZERO)
		await get_tree().physics_frame
		await get_tree().process_frame
		if state != IDLE and state != DONE:
			break
	if state == IDLE or state == DONE:
		return
	_gate_visits += 1
	# A BOUND THAT SAYS WHAT IT GAVE UP ON. A gate that hangs looks exactly like
	# a gate that is being thorough, and this repository has lost a session to
	# that reading twice. 2,400 physics frames is 40 s of station time at 60 Hz,
	# against a compressed response of a few seconds.
	var guard := 0
	while state != DONE and guard < 2400:
		guard += 1
		await get_tree().physics_frame
		await get_tree().process_frame
	if state != DONE:
		print("ARREST STALLED in state %d at %s after %d frames -- the machine "
			% [state, _gate_k, guard] + "did not reach a verdict")
	_gate_walked = maxf(_gate_walked, _officer_m)


## THE VERDICT, AND EVERY WAY THIS CAN GO WRONG FAILS IT: nobody was refused, or
## nobody came, or somebody came and covered no ground, or a detention happened
## and the purse never noticed.
func _finish(_ok: bool) -> void:
	var moved := (_gate_where0.distance_to(_player.global_position)
		if _gate_where0 != Vector3.ZERO else 0.0)
	var dcr := (_gate_cr0 - float(_player.get("credits")) if _gate_cr0 >= 0.0
		else 0.0)
	var dh := 0.0
	if _clock != null and _gate_h0 >= 0.0:
		dh = fposmod(float(_clock.call("hour")) - _gate_h0, 24.0)
	var body := (_crowd != null and not _args().has("enforce-no-officer"))
	var ok := (refused > 0 and responded > 0 and arrived > 0
		and (moved_on + detained) > 0 and detained > 0
		and dcr > 0.0 and dh > 0.0
		and (not body or _gate_walked > 1.0))
	print(("ARREST gate=%s refused=%d responded=%d arrived=%d moved_on=%d "
		+ "detained=%d walked=%.1fm cr=-%.2f clock=+%.1fh out=%.1fm rate=x%.0f "
		+ "place=%s") % [
		("PASS" if ok else "FAIL"), refused, responded, arrived, moved_on,
		detained, _gate_walked, dcr, dh, moved, rate, _gate_k])
	get_tree().quit(0 if ok else 1)
