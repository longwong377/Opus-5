extends CharacterBody3D
## The player. A body that stands on the station and walks around it.
##
## THIS IS THE FILE THIS PROJECT SPENT ITS FIRST THREE PHASES NOT WRITING. As of
## session 3u the string `CollisionShape` appeared nowhere in the repository:
## 118 locations had geometry, materials and measured lighting, and not one of
## them had a floor in the physics sense. Every gate measured a part in
## isolation, so nothing ever failed for the absence of a player.
##
## GRAVITY POINTS OUTWARD, NOT DOWN, AND IT IS NOT 9.81 ANYWHERE ON THE ROTOR.
## The whole station spins about +Z. "Down" for anyone standing inside it is AWAY
## from the spin axis, so the gravity vector is the radial direction at the
## player's own position and it changes as they walk around the ring; and the
## magnitude is g = omega^2 r, which on the boot deck at r = 211.5 m is
## **7.454 m/s^2 (0.760 g)**, not 9.81.
##
## THE OLD SHAPE OF THIS FILE GOT BOTH HALVES WRONG AND ONE OF THEM SHIPPED.
## `gravity_mode` was a two-way switch -- "drum" derived the direction from the
## body's position, "deck" returned the constant `Vector3(0, -1, 0)` -- with a
## separate scalar `gravity_m_s2` defaulting to 9.81 that every caller was
## expected to fill in. Measured, session 4r:
##
##   * `"deck"` mode is wrong everywhere except the bottom of the ring. The
##     shipped spawn sits at ring angle **264.8 deg**, where -Y is 5.2 deg off
##     the true radial, so it LOOKED right; at ring angle 90 deg the same
##     constant points at the ceiling and a player falls off it.
##   * `main.gd::_configure_walk` does set `"drum"`, so the shipped direction was
##     right -- and **nothing anywhere sets `gravity_m_s2`**, so the shipped
##     magnitude was Earth's: 9.81 against 7.4522, **+31.7%**. A jump was a third
##     short and every fall a third too fast, on the only build a player launches.
##
## So the derivation lives HERE, once, off the body's own world position, exactly
## as `ragdoll.gd::promote` was made to do in session 4q (INV-451) for exactly
## the same reason: a default that only the gate it was written in ever sets is
## an unset default. `omega2` is the one number the runtime cannot work out for
## itself -- the station's spin -- and `walk.gd` reads it off the same
## `cell_manifest.json` deck table `main.gd::_spin_omega2` does. INV-480.

## Which field this body is in when `omega2` is unset. "drum" derives the
## DIRECTION from position; "deck" is -Y. **Both are superseded by `omega2`**,
## which derives direction and magnitude together; this switch survives so that
## the callers which spawn their own body and state their own scalar --
## `transit.gd`, `route_test.gd`, `life.gd`, `navwalk.gd`, `arrival.gd` -- are
## bit-for-bit unchanged by that fix.
@export_enum("deck", "drum") var gravity_mode: String = "deck"
## Metres per second squared, when there is no `omega2`. See `gravity_g()`: with
## a spin stated, this is not read at all.
@export var gravity_m_s2: float = 9.81
## THE STATION'S OWN SPIN, omega^2 in rad^2/s^2. Positive means "this body is
## standing on the rotor": down is radially outward from +Z and the magnitude is
## omega^2 r at the body's own radius, which is exact at every radius including
## the ones with no deck on them.
##
## ZERO IS NOT A GUESS, IT IS "NOBODY TOLD ME". A build that does not state the
## spin keeps the pre-4r behaviour rather than silently inventing a field --
## `field_report()` says which of the two is in force, on every run, because a
## thing that can substitute one mode for another has to name the one it used.
@export var omega2: float = 0.0
## Walking speed. A person walks at 1.4 m/s; this is a game, so it is faster.
@export var speed_m_s: float = 4.2
@export var sprint_m_s: float = 8.0
## Jump take-off speed, in m/s.
@export var jump_m_s: float = 4.0
## Mouse look sensitivity, radians per pixel.
@export var look_sensitivity: float = 0.0025
## Where the eye sits above the body's origin. 1.7 m is the stature this project
## uses everywhere -- `drum_ground.stand_on_ground`, the reference m/px ladders
## in INV-071 -- so a screenshot from this camera is comparable to one from the
## render harness.
@export var eye_height_m: float = 1.7

var _yaw := 0.0
var _pitch := 0.0
var _cam: Camera3D
## Whether the body is in the air because it JUMPED. See `step`: it is the
## only thing allowed to give a walking body upward velocity.
var _jumped := false


# ===========================================================================
#  WHO THIS BODY IS -- the purse, the bag and the rung
# ===========================================================================
## THE FOUR THINGS THE ENGINE CANNOT DERIVE, and they arrive together because
## they arrive through one channel. `station/player.py` is 800 lines about who
## the player is -- a `Resident` with a card, a home, a job, a purse and a
## standing -- and until session 4q **not one byte of it reached a runtime**:
## `hud.gd` parsed `economy.json` for a NUMBER to draw in the corner and that
## was the whole bridge. So this body had a stature and a walking speed and
## nothing else, which is `MASTER-PLAN` A4b-2 stated as a field list.
##
## THEY ARE SET, NEVER COMPUTED. Every one of these is `Player.state()`'s own
## output: the rung comes from `consequence.tier_of` through the nine
## identicard fields, the hip and seat heights from `npc/animation.py`'s sit
## rule scaled by this person's own stature and species leg factor, the bag
## size from `player.CARRY_CAPACITY`. A default written here would be a human's
## hip height applied to a 2.02 m Narn -- which is the same defect as the
## corridor profile written down instead of measured, one body down.
##
## `credits < 0.0` MEANS "NO LEDGER", and it is a different statement from
## zero. A build with no economy behind it must not draw `0.00 CR`, because
## that is a HUD asserting a fact nobody computed.
var npc_id := ""
var person := ""
var credits := -1.0
var carrying: Array[String] = []
var carry_cap := 0
## THE RUNG, AND IT IS A READING RATHER THAN A STORED FIELD -- see `rung_of`.
var tier := -99
var tier_name := ""
## Why the rung reads what it reads, in one line, so a gate can assert on the
## DERIVATION and not only on the answer. Printed by `interact.gd::watch`.
var rung_why := ""
## The number the DOCUMENT carried, kept beside the derived one. `st["tier"]` is
## `player.py::state()`'s report of the card at save time; when the two differ,
## the record moved and the report did not, which is exactly the case a reload
## has to get right.
var tier_stored := -99
## The last purse document `set_purse` was handed, kept whole so `load_state`
## can put the rung back through `rung_of` instead of restoring it as a number.
## It is NOT saved -- `interact.gd`'s ledger snapshot already carries it, and a
## second copy in the same file is the defect this whole section is about.
var _purse_doc: Dictionary = {}
## Standing hip height and a fitted seat height, metres, for THIS person.
var hip_m := 0.0
var seat_m := 0.0
## How far the eye sits above whatever you are lying on.
var recline_m := 0.0
## The hour this species wakes -- `npc/schedule.py::wake_hour`. A `rest` on a
## bunk advances the station clock to it; a Narn's is not a human's.
var wake_h := -1.0


## Take the mutable half of a `station/player.py::Player` onto this body.
##
## HANDED IN RATHER THAN READ HERE. `interact.gd` owns the ledger document,
## because the ledger also holds every counter's stock and till and those
## belong to the world rather than to the person standing in it. One reader,
## one writer -- the rule `hud.gd` learned when its room extents disagreed with
## `ambience.gd`'s by 31.6 m.
func set_purse(st: Dictionary) -> void:
	npc_id = String(st.get("npc_id", ""))
	person = String(st.get("name", npc_id))
	credits = float(st.get("credits", -1.0))
	carrying.clear()
	for x in st.get("carrying", []):
		carrying.append(String(x))
	carry_cap = int(st.get("carry_cap", 0))
	tier_stored = int(st.get("tier", -99))
	# THE DOCUMENT IS KEPT, and it is kept for exactly one reason: `load_state`
	# has to be able to run this derivation again without a ledger reader. See
	# the block above `save_state`.
	_purse_doc = st.duplicate(true)
	# THE RUNG IS THE ONE FIELD HERE THAT IS **NOT** TAKEN AS HANDED IN, and the
	# comment above this block used to say all four were. See `rung_of`.
	var r: Array = rung_of(st)
	tier = int(r[0])
	tier_name = String(r[1])
	rung_why = String(r[2])
	hip_m = float(st.get("hip_m", 0.0))
	seat_m = float(st.get("seat_m", 0.0))
	recline_m = float(st.get("recline_m", 0.0))
	wake_h = float(st.get("wake_h", -1.0))


# ===========================================================================
#  THE RUNG IS READ OFF THE RECORD, NOT REMEMBERED -- `consequence.tier_of`
# ===========================================================================
## WHAT WAS WRONG, STATED ONCE, because it is instance ten of this project's
## signature defect and the most refined one yet. Session 4t round 2 built the
## whole arrest chain correctly: `interact.gd::convict` writes the demotion into
## the RECORD (`visa_revoked`, `revoked_from`, `convictions`) exactly where
## `player.py` wants it, and the ledger on disk carried three convictions, a
## revoked visa and 619.89 cr gone. And then:
##
##   * `interact.gd::_sync_purse` writes back `credits` and `carrying` and NEVER
##     `tier`/`tier_name` -- correctly, because `player.py` deliberately refuses
##     to store the rung as a fact;
##   * this function read `tier = int(st.get("tier", -99))` verbatim off that
##     stale stored field and derived nothing;
##   * so a second launch on the very file the first one wrote opened it as
##     `interact: purse player:g2c (IVANOVA, AMIS, transit)`. **The money
##     persisted, the record persisted, the punishment did not.**
##
## And the gate was GREEN, because its reload check re-derived the rung in
## PYTHON (`consequence.tier_of`) -- a call the shipped Godot path never makes.
## A gate that recomputes the answer cannot notice that the shipped path never
## computes it.
##
## THE MINIMAL FIX IS THE WRONG FIX. Having `_sync_purse` also write `st["tier"]`
## works and stores the rung as a fact, which is the thing `player.py`'s own
## comment forbids: *"Restoring them would be a second copy of a derivation,
## which is how a saved tier survives a conviction."* So the fix is at the RULE,
## the way `_fine_of` and `_cell_of` were fixed one file over: the rung is
## COMPUTED here, from the record, against the baked ladder.
##
## AND IT IS `consequence.tier_of`'S RULE AND NOT A SECOND ONE. That function
## has exactly three branches over the record -- custody, revocation, otherwise
## the card's own reading -- and this is those three. The card's own reading is
## the one thing the engine genuinely cannot recompute (it needs `arrival.
## entry_class`, a five-branch visa parser), so `st["tier"]` is used for THAT
## and only that: as the report of the frozen card it is documented to be.
const LADDER_REL := "../station/generated/scene/enforcement.json"

var _ladder: Dictionary = {}
var _ladder_read := false


func _ladder_table() -> Dictionary:
	if _ladder_read:
		return _ladder
	_ladder_read = true
	var p := ProjectSettings.globalize_path("res://").path_join(
		LADDER_REL).simplify_path()
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		# LOUD, NOT SILENT. Without the ladder this body cannot derive a rung,
		# and falling back to the stored report is precisely the defect above.
		# It says so and takes the report, so the gate goes red on the reload
		# rather than passing on a number nobody computed.
		print("player: no consequence ladder at %s -- the rung on this card is "
			% p + "the STORED REPORT and a demotion will not survive a reload. "
			+ "Run `python3 station/enforcement.py --bake`")
		return _ladder
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) == TYPE_DICTIONARY:
		_ladder = d
	return _ladder


func _tier_named(nm: String) -> int:
	var tiers: Dictionary = _ladder_table().get("tiers", {})
	for k in tiers:
		if String(tiers[k]) == nm:
			return int(String(k))
	return -99


func _tier_label(t: int, fallback: String) -> String:
	var tiers: Dictionary = _ladder_table().get("tiers", {})
	return String(tiers.get(str(t), fallback))


## Is a revocation DUE on this record at this rung? `consequence._dispose`'s own
## two thresholds, read from the bake rather than written here.
##
## WHY THE THRESHOLDS ARE CONSULTED AT ALL when `visa_revoked` already answers
## it: the flag is the REPORT of a decision and the ladder is the RULE, and this
## takes either. A record carrying two grade-2 convictions on a revocable rung
## with the flag unset is a record whose writer did not apply the disposal --
## which is the same class of defect as the one this function exists for, one
## level down. It is resolved towards the rule, never away from it: nothing here
## can un-revoke a card.
func _revocation_due(rung: int, rec: Dictionary) -> Dictionary:
	var t := _ladder_table()
	var rv: Dictionary = t.get("revocable", {})
	if not rv.has(str(rung)):
		return {"due": false, "falls_to": rung,
			"why": "the ladder prices no rung %d" % rung}
	var to = rv[str(rung)]
	if to == null:
		return {"due": false, "falls_to": rung,
			"why": "rung %d holds no permission an Ombuds can withdraw" % rung}
	var grades: Dictionary = t.get("offence_grade", {})
	var ord_n := 0
	var ser_n := 0
	var ungraded := 0
	for k in (rec.get("convictions", []) as Array):
		if not grades.has(String(k)):
			ungraded += 1
			continue
		var g := int(grades[String(k)])
		if g == 2:
			ord_n += 1
		elif g >= 3:
			ser_n += 1
	var ns := int(t.get("revoke_on_serious", 1))
	var no := int(t.get("revoke_on_ordinary", 2))
	var tail := ("" if ungraded == 0
		else " (%d conviction(s) the bake does not grade)" % ungraded)
	if ns > 0 and ser_n >= ns:
		return {"due": true, "falls_to": int(to),
			"why": "%d serious conviction(s), the ladder revokes at %d%s"
				% [ser_n, ns, tail]}
	if no > 0 and ord_n >= no:
		return {"due": true, "falls_to": int(to),
			"why": "%d ordinary conviction(s), the ladder revokes at %d%s"
				% [ord_n, no, tail]}
	return {"due": false, "falls_to": rung,
		"why": "%d ordinary / %d serious, under the ladder's %d / %d%s"
			% [ord_n, ser_n, no, ns, tail]}


## `[rung, name, why]` for the purse `st`. `consequence.tier_of`, in the engine.
func rung_of(st: Dictionary) -> Array:
	var card := int(st.get("tier", -99))
	var card_nm := String(st.get("tier_name", ""))
	# THE CONTROL THAT SHOWS THIS IS LOAD-BEARING. `--player-stored-rung` is the
	# pre-fix line, one branch wide: the rung is whatever the document last
	# reported. A run with it must come back from a revocation still holding the
	# permission, and the progression gate must go RED. If it does not, this
	# whole function is decoration.
	if _stored_rung_forced():
		return [card, card_nm,
			"CONTROL --player-stored-rung: taken verbatim from the document, "
			+ "which is the defect this function exists for"]
	var rec = st.get("record")
	if typeof(rec) != TYPE_DICTIONARY:
		return [card, card_nm,
			"no record on this card -- the rung is the card's own reading"]
	# 1. CUSTODY OUTRANKS EVERYTHING. `tier_of` branch 1.
	if bool(rec.get("in_custody", false)):
		var dt := -1
		return [dt, _tier_label(dt, "detained"),
			"in custody -- the card reads nothing until the Ombuds sits"]
	# 2. WAS A PERMISSION TAKEN? The rung it was taken FROM is the record's own
	#    `revoked_from` when there is one, because `st["tier"]` is by then the
	#    stale report and testing revocability against a stale rung is how this
	#    would quietly stop working the day a second demotion lands.
	var flag := bool(rec.get("visa_revoked", false))
	var from_rung := card
	var rf := String(rec.get("revoked_from", ""))
	if rf != "":
		var f := _tier_named(rf)
		if f != -99:
			from_rung = f
	var due: Dictionary = _revocation_due(from_rung, rec)
	if flag or bool(due["due"]):
		# `tier_of` branch 2, verbatim: "the conditional permission is gone, so
		# the card reads the way a card with no permission reads". The ladder
		# supplies which rung that is; NO_STATUS is the only floor `REVOCABLE`
		# ever names, and it is read rather than written down.
		var to := (int(due["falls_to"]) if bool(due["due"]) else 0)
		var why := String(due["why"])
		var src := ""
		if flag and bool(due["due"]):
			src = "the record and the ladder agree -- " + why
		elif flag:
			src = ("the record says revoked; the ladder does not require it ("
				+ why + ")")
		else:
			src = ("THE RECORD DOES NOT SAY REVOKED AND THE LADDER SAYS IT IS "
				+ "DUE (" + why + ") -- the rule wins")
		return [to, _tier_label(to, "no_status"),
			"revoked from %s: %s" % [(rf if rf != "" else card_nm), src]]
	# 3. OTHERWISE THE CARD'S OWN READING, which is the one thing here the
	#    engine cannot recompute -- `arrival.entry_class` is the visa parser and
	#    it does not exist in GDScript. This is `st["tier"]` used AS the report
	#    `player.py::state()` documents it to be.
	return [card, card_nm,
		("the card's own reading; the record takes nothing ("
			+ String(due["why"]) + ")")]


func _stored_rung_forced() -> bool:
	for a in OS.get_cmdline_user_args():
		if String(a) == "--player-stored-rung":
			return true
	return false


## THE CONTROL FOR THE **SAVEGAME** HALF, and it is a different defect from
## `--player-stored-rung`. That one puts the pre-round-3 line back into
## `rung_of` -- the rung read off the LEDGER document. This one puts the
## pre-round-4 line back into `save_state`/`load_state` -- the rung read off the
## SAVE FILE, which survived round 3 untouched because the fix was applied to
## one of this file's two purse loaders. With it set, `save_state` writes
## `tier`/`tier_name` and `load_state` restores them verbatim over whatever
## `interact.gd` derived, exactly as the shipped code did until this round. The
## save row of `enforcement.py --progression` must go RED under it, or that row
## is decoration.
##
## AND A SECOND FLAG, BECAUSE THE FIRST ONE ALONE CANNOT SHOW THE HARM. Inside
## one `--save-gate` run the capture and the restore see the same ledger, so the
## stored rung and the derived rung COINCIDE and the pre-fix build behaves
## identically to the fixed one. That is not an argument that the defect is
## harmless -- it is the reason it survived round 3 and a verifier had to force
## it. The values stop coinciding for exactly the cases `player.py`'s own
## comment anticipates: a save written by the pre-fix build, a save loaded after
## the ledger moved on, a hand-edited save. `--player-stale-save` is that case
## and it invents nothing: it writes `tier_stored`, which IS the frozen report
## the document still carries, so the save file describes the card as it read
## BEFORE the conviction landed. Under the pre-fix loader that restores
## `transit` onto a revoked card. Under this file as it now stands it cannot,
## because nothing reads it.
func _saved_rung_forced() -> bool:
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s == "--player-saved-rung" or s == "--player-stale-save":
			return true
	return false


func _stale_save_forced() -> bool:
	for a in OS.get_cmdline_user_args():
		if String(a) == "--player-stale-save":
			return true
	return false


func has_purse() -> bool:
	return credits >= 0.0


## Is there room for one more thing? `station/player.py::CARRY_CAPACITY` is the
## number and INV-410 is its derivation; a build with no purse has no bag and
## no ceiling, which is the pre-4q behaviour and is reported as such.
func bag_full() -> bool:
	return carry_cap > 0 and carrying.size() >= carry_cap


func take(item: String) -> bool:
	if item == "":
		return false
	if carrying.has(item):
		return true
	if bag_full():
		return false
	carrying.append(item)
	carrying.sort()
	return true


func put(item: String) -> bool:
	if not carrying.has(item):
		return false
	carrying.erase(item)
	return true


# ===========================================================================
#  SITTING DOWN
# ===========================================================================
## THE VERB THAT WAS PRESSABLE AND INERT. `station/interact.py` has classified
## nine tokens as `sit` and five as `rest` since the verb set was derived, and
## both were deliberately left out of `RESPONDS` with an honest reason: *"what
## responds to those is a BODY, not a prop"*. This is that body.
##
## WHAT SITTING IS, MECHANICALLY, and it is `npc/animation.py::sit_clip`'s own
## rule rather than a second one: the hip goes to the seat and everything above
## it comes with it, so the eye drops by exactly `hip_m - seat`. Nothing here
## picks a number -- the seat height is measured off the prop by `interact.gd`
## for something you sit ON, and is this person's own fitted knee height for
## something you sit AT.
##
## AND YOU CANNOT WALK. That is not decoration: a "sit" that leaves the player
## strafing around at chair height is a camera effect, and the difference
## between a camera effect and a mechanic is whether it takes something away.
## `step()` refuses every wish while `seated` is set; SPACE or a second press
## stands you up.
##
## THE BODY DOES NOT MOVE. It stays on the floor exactly where it was, still
## pinned by `step()`'s floor hold -- so `is_on_floor()` and the radial drop the
## cold-start gate measures are unchanged by sitting, and a seated player is
## still standing on the deck as far as the physics is concerned. Moving the
## capsule onto the seat would put a 1.8 m body inside 0.45 m of furniture.
var seated := ""                      # "" | "sit" | "rest"
var seat_used_m := 0.0                # the surface height that was used
var _eye_now := 0.0


## Where the eye goes when this person sits on a surface `h` above the floor.
func seated_eye(h: float) -> float:
	return h + (eye_height_m - hip_m)


## Sit or lie down. `h_m` is the surface height above this body's own feet;
## pass <= 0 to use the fitted seat. Returns false if already seated.
func sit_at(h_m: float, verb: String = "sit", recline: bool = false) -> bool:
	if seated != "":
		return false
	# NO PERSON, NO POSTURE, AND THIS REFUSES RATHER THAN GUESSING. `hip_m` and
	# `seat_m` come off the purse, which is `station/player.py::posture` for
	# THIS person's species and stature; a body with no purse has neither.
	#
	# IT WAS A GUESS AND IT WENT THE WRONG WAY, which is why the refusal is
	# here rather than a default. With `hip_m` left at 0 the drop
	# `eye_height_m - hip_m` is the whole eye height, so sitting on a 0.76 m
	# stool put the eye at 2.46 m -- it RAISED it by three quarters of a metre.
	# Measured, on the first engine run of this function, against a `--ledger=`
	# that pointed at nothing.
	if hip_m <= 0.0 or seat_m <= 0.0:
		return false
	var h := h_m
	# A SURFACE THAT IS NOT A SEAT IS NOT USED AS ONE. Above the hip you are
	# not sitting on it, you are climbing it; at or below the floor it is not a
	# surface. Either way the fitted seat is the honest answer, and `seat_m` is
	# this person's own knee height rather than a constant.
	if h <= 0.02 or h > hip_m:
		h = seat_m
	if h <= 0.0:
		return false
	seat_used_m = h
	seated = verb
	# LYING DOWN IS NOT SITTING ON A LOWER CHAIR. On a bunk the eye is a
	# chest-depth above the surface, not a hip-to-eye above it.
	_eye_now = (h + recline_m) if recline else seated_eye(h)
	velocity = Vector3.ZERO
	if _cam != null:
		_cam.position = Vector3(0.0, maxf(_eye_now, 0.05), 0.0)
	return true


func stand_up() -> bool:
	if seated == "":
		return false
	seated = ""
	seat_used_m = 0.0
	_eye_now = eye_height_m
	if _cam != null:
		_cam.position = Vector3(0.0, eye_height_m, 0.0)
	return true


## Where the eye is, in metres above the body's feet. Read by `hud.gd`, and it
## is the one number that says a sit did something a player would see.
func eye_now_m() -> float:
	return _eye_now if seated != "" else eye_height_m


func _ready() -> void:
	_cam = get_node_or_null("Camera3D")
	if _cam == null:
		_cam = Camera3D.new()
		_cam.name = "Camera3D"
		add_child(_cam)
	_cam.position = Vector3(0.0, eye_height_m, 0.0)
	_eye_now = eye_height_m
	_cam.near = 0.15
	_cam.far = 12000.0
	# THE SHIPPED CAMERA MUST NOT BE WIDER THAN THE ONE THE BUDGET GATES. Godot's
	# `Camera3D` defaults to 75 degrees vertical -- verified against the engine,
	# not remembered -- and `station/budget.py` counts the frustum at 70 (INV-083),
	# so the build was rendering 5 degrees MORE than anything measured it. A
	# budget gated on a narrower view than ships understates by exactly the
	# geometry the wider view adds, which is the same defect as measuring the kit
	# in isolation and calling it a frame.
	_cam.fov = 70.0
	if not Engine.is_editor_hint():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


## The distance from the spin axis, in metres. The axis is +Z in this project's
## world frame, so the radial is the xy part of the body's own position.
func spin_radius() -> float:
	return sqrt(global_position.x * global_position.x
		+ global_position.y * global_position.y)


## The direction gravity pulls this body, as a unit vector.
##
## On a spinning ring or drum the floor is the INSIDE of a barrel, so "down" is
## the outward radial direction from the spin axis. Getting this backwards is the
## same sign error that `interior.drum_interior` guards with `_inward_fraction`:
## a body with the sign wrong falls to the axis and hangs there, which looks like
## a physics bug and is a coordinate one.
##
## WITH A SPIN STATED THERE IS NO MODE. A ring deck and the drum floor are the
## same field -- one rigid rotor -- and the old `gravity_mode` split let a body
## on the ring take the -Y branch, which is the defect this function is being
## fixed for. `omega2 == 0.0` keeps the old two-way switch so that every caller
## which has never heard of the spin behaves exactly as it did.
func gravity_dir() -> Vector3:
	if omega2 > 0.0 or gravity_mode == "drum":
		var radial := Vector3(global_position.x, global_position.y, 0.0)
		if radial.length() < 0.001:
			return Vector3(0, -1, 0)
		return radial.normalized()
	return Vector3(0, -1, 0)


## How hard, in m/s^2, at the body's OWN radius.
##
## `g = omega^2 r` is the whole of rigid-rotor kinematics and it is exact --
## there is no place on the rotor where it is an approximation, and it is the
## same expression `ragdoll.gd::promote` and `populace.place_gravity_at` use. A
## body 3.6 m up a lift shaft is in a measurably weaker field than one on the
## deck below it, and this returns that rather than a per-deck constant.
func gravity_g() -> float:
	if omega2 <= 0.0:
		return gravity_m_s2
	var r := spin_radius()
	if r < 0.001:
		# ON THE AXIS THERE IS NO SPIN GRAVITY, and that is a physical fact rather
		# than a failure: r = 0 is weightless. Returning the stated scalar here
		# would be inventing a field on the one line where there is none.
		return 0.0
	return omega2 * r


## WHICH RULE IS IN FORCE, in words, for whoever is reading a verdict. CLAUDE.md's
## rule from the renderer that silently fell back to OpenGL 3 and exited 0: a
## thing that can substitute a lesser mode for the one asked for must say which
## one it used.
func field_report() -> String:
	if omega2 > 0.0:
		return ("spin omega2=%.8f rad2/s2 -> r=%.3f m, g=%.4f m/s2 (%.4f g), "
			% [omega2, spin_radius(), gravity_g(), gravity_g() / 9.80665]
			+ "up=%.4f,%.4f,%.4f" % [body_up().x, body_up().y, body_up().z])
	return ("STATED mode=%s g=%.4f m/s2 up=%.4f,%.4f,%.4f -- no spin given"
		% [gravity_mode, gravity_m_s2, body_up().x, body_up().y, body_up().z])


## The body's own up, which is the opposite of the way it falls.
func body_up() -> Vector3:
	return -gravity_dir()


## The basis a body standing HERE has: local +Y along its own up, local -Z the
## way it faces. Split out of `step()` so a spawn can stand the capsule up before
## its first frame -- see `walk.gd::_spawn_player`.
##
## RIGHT-HANDED, AND IT IS THE PROJECT'S ONE IDIOM. `Basis(x, y, z)` takes the
## three COLUMNS and is a rotation only when x cross y = z. With
## `right = fwd cross up` and the third column `-fwd` the two negations cancel
## and the determinant is +1; `npc.gd::_walker_xform` passing `+fwd` with the
## same `right` is what drew the whole corridor crowd mirrored for six sessions.
func stand_basis(face: Vector3 = Vector3.ZERO) -> Basis:
	var up := body_up()
	var fwd := face
	if fwd.length_squared() < 1e-9:
		# THE REFERENCE AXIS IS THE SPIN AXIS. On a spun habitat `up` is radial
		# and therefore always perpendicular to +Z, so +Z can never degenerate --
		# unlike `up.cross(Vector3.RIGHT)`, which is zero at ring angles 0 and
		# 180, one of which is where a deck's own spawn can sit. See `step()`.
		fwd = Vector3(0, 0, 1)
	fwd = fwd - up * fwd.dot(up)
	if fwd.length() < 1e-4:
		fwd = Vector3(0, 0, 1) - up * up.z
	fwd = fwd.normalized()
	return Basis(fwd.cross(up).normalized(), up, -fwd).orthonormalized()


## Face a given yaw. The headless walk test uses this to try more than one
## direction, because a body's "forward" is derived from a world axis and a
## corridor runs whichever way it runs.
func set_yaw(y: float) -> void:
	_yaw = y


## A HARNESS THAT DRIVES `step()` MUST BE THE ONLY THING THAT DOES.
##
## With no window there is no input, so `_physics_process` below steps the body
## a SECOND time every frame with a zero wish -- and a zero wish still rebuilds
## the body's basis from `_yaw`. Nothing about walking notices, because a wish
## vector needs no facing. What needs one is the EYE: the camera rides the body,
## `interact.gd` scans a 35-degree cone about the camera axis, and on a ring deck
## yaw 0 points straight along the station's spine. Measured in session 4g while
## the body walked directly at a console from 3.6 m:
##
##     USELEG f=10 short=3.62 eye_range=3.65 off_axis=162 in_sight=false
##            camfwd=-0.00,-0.00,1.00 steer=-0.32,-0.26,-0.91
##
## 160 degrees off the view axis, so it could never be prompted, and the failure
## read as "the interactable is not wired". `--walk-test` masked it by calling
## `set_yaw` after its own heading sweep -- which is the only reason the
## monolithic use gate could ever see what it walked up to -- and the stream test
## worked around it in `walk.gd::_face`. Both are the wrong place: any future
## headless driver would have to remember. One line here ends the class.
func drive_externally() -> void:
	set_physics_process(false)


## ESC WAS A ONE-WAY DOOR, AND NOTHING IN THE PROJECT COULD SHUT IT AGAIN.
##
## The old body released the mouse on ESC and there was exactly ONE assignment of
## `MOUSE_MODE_CAPTURED` in the whole repository -- `_ready`, above, which runs
## once. So a player who pressed ESC looking for a pause menu got a cursor, no
## menu, and a head that never turned again for the rest of the session. The only
## recovery was to quit. Grep proves the shape of it rather than my memory of it:
## `mouse_mode` appears four times in `godot/scripts/`, and only `_ready` and
## `main_menu.gd` ever capture.
##
## TWO WAYS BACK, because a player who has lost the camera will try both. ESC
## toggles -- press it again and the mouse is recaptured -- and any mouse button
## pressed while the cursor is free recaptures too, which is the convention every
## first-person build on Windows uses and the one a hand reaches for without
## being told. No other script in this project reads `InputEventMouseButton`
## (checked, not assumed), so claiming the click costs nothing today; when an
## interaction verb wants it, it will be handled before this and never reach
## `_unhandled_input`, which is precisely what that method is for.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= event.relative.x * look_sensitivity
		_pitch = clamp(_pitch - event.relative.y * look_sensitivity,
			-1.4, 1.4)
	elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
			print("player: mouse released -- ESC or click to look again")
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif event is InputEventMouseButton and event.pressed \
			and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


## One step of walking. Split out from `_physics_process` so the headless test in
## `station/walkable.py` can drive the body directly with a synthetic input
## vector and no window, keyboard or mouse. A player controller that can only be
## tested by a human is a player controller that never gets tested here -- there
## is no human and no GPU in this container.
## `world_dir`, when non-zero, steers the body toward a direction in WORLD space
## instead of deriving one from the look yaw. The headless test uses it to walk
## somewhere specific -- "can this body get from the corridor into medlab" is a
## different question from "can it move", and only the first is what milestone
## W2 claims. The direction is flattened onto the floor plane, because on a
## spun ring the target is usually a little above or below you and walking at it
## directly would mean walking into the deck.
func step(delta: float, wish: Vector2, jump: bool, sprint: bool,
		world_dir: Vector3 = Vector3.ZERO) -> void:
	var up := body_up()
	# BOTH HALVES FROM THE SAME PLACE. Before session 4r the direction came from
	# `gravity_mode` and the magnitude from a scalar nobody set, so the shipped
	# build fell along a radius at Earth's 9.81 instead of this deck's 7.4522.
	var g := gravity_dir() * gravity_g()

	# -- SEATED: THE WISH IS REFUSED, THE FLOOR HOLD IS NOT ------------------
	# A sit that can be walked out of is a camera effect. The body keeps its
	# basis, keeps its floor pin and keeps answering `is_on_floor()` -- the
	# cold-start gate reads that at frame 120 and a seated player must not read
	# as a fallen one -- and loses exactly one thing: the ability to go
	# anywhere. Jump stands up, because a player who wants to leave presses the
	# key that means "up".
	if seated != "":
		if jump:
			stand_up()
		else:
			velocity = up * -0.1
			up_direction = up
			move_and_slide()
			if _cam != null:
				_cam.transform.basis = Basis(Vector3.RIGHT, -_pitch)
			return

	# Basis from the body's own up, so "forward" stays tangential to the drum
	# floor rather than to the world.
	#
	# THE REFERENCE AXIS IS THE SPIN AXIS, and picking it by hand matters. The
	# first version took `up.cross(Vector3.RIGHT)`, which DEGENERATES TO ZERO
	# wherever `up` is parallel to world X -- ring angles 0 and 180 degrees, one
	# of which is where the deck's own spawn happens to sit. It fell back to a
	# different world axis there, so a player walking round the ring had their
	# heading frame flip discontinuously twice a lap. On a spun habitat `up` is
	# radial and therefore ALWAYS perpendicular to the spin axis, so +Z is a
	# reference that can never degenerate. Choose the one the geometry
	# guarantees rather than the one that usually works.
	var fwd := (Vector3(0, 0, 1) if (omega2 > 0.0 or gravity_mode == "drum")
		else Vector3.FORWARD)
	if world_dir.length_squared() > 1e-9:
		var flat := world_dir - up * world_dir.dot(up)
		if flat.length() > 1e-4:
			fwd = flat.normalized()
		wish = Vector2(0, 1)
	else:
		fwd = (fwd - up * fwd.dot(up)).normalized().rotated(up, _yaw)
	var right := fwd.cross(up).normalized()

	# THE BODY ITSELF IS ORIENTED, not just the camera, and this was the bug
	# that stopped a body walking on a ring deck. A CapsuleShape3D stands along
	# its owner's LOCAL Y. Leaving the body unrotated while calling its up
	# "radial" put a 1.8 m capsule lying sideways through the floor and the wall
	# -- the body reported `on_floor = true`, because it was, and could not move
	# in any of four directions, because it was embedded. It is not enough for
	# gravity to know which way is up; the shape has to.
	#
	# ONE CONSTRUCTION SITE. `stand_basis` builds exactly this expression and is
	# what `walk.gd::_spawn_player` stands the capsule up with before the body's
	# first frame, so a spawn pose and a walking pose cannot drift apart.
	global_transform.basis = stand_basis(fwd)

	var speed := sprint_m_s if sprint else speed_m_s
	var horiz := (fwd * wish.y + right * wish.x)
	if horiz.length() > 1.0:
		horiz = horiz.normalized()
	horiz *= speed

	# Split velocity into along-gravity and across-gravity so a change of field
	# direction does not turn forward motion into falling.
	var v_along := velocity.project(up)
	if is_on_floor():
		_jumped = false
		if jump:
			v_along = up * jump_m_s
			_jumped = true
		else:
			v_along = up * -0.1        # keep the body pinned to the floor
	else:
		# A WALKING BODY HAS NO UPWARD VELOCITY IT DID NOT ASK FOR. Only a jump
		# sends a person up; `move_and_slide` writes back the motion it actually
		# achieved, so anything that shoves the body arrives here as velocity
		# nobody asked for, and Godot skips `floor_snap_length` entirely while
		# `velocity.dot(up_direction) > 0`. A body that has been nudged upward by
		# a millimetre would otherwise coast, unsnapped, until gravity turned it
		# round.
		#
		# A MEASURED NEGATIVE, and it is kept because it is right rather than
		# because it fixed anything. It was session 4h's third hypothesis for the
		# crowd shove and it moved the count from 2,523 off-floor frames to
		# 2,520 -- see `docs/runtime-4h.md` 1b. The cause was elsewhere and this
		# is still the correct rule for a walking body.
		if not _jumped and v_along.dot(up) > 0.0:
			v_along = Vector3.ZERO
		v_along += g * delta

	velocity = horiz + v_along
	up_direction = up
	move_and_slide()

	# The camera rides the body now, so it only needs the look pitch.
	if _cam != null:
		_cam.transform.basis = Basis(Vector3.RIGHT, -_pitch)


func _physics_process(delta: float) -> void:
	var wish := Vector2(
		Input.get_action_strength("ui_right") - Input.get_action_strength("ui_left"),
		Input.get_action_strength("ui_up") - Input.get_action_strength("ui_down"))
	step(delta, wish,
		Input.is_key_pressed(KEY_SPACE),
		Input.is_key_pressed(KEY_SHIFT))


# ===========================================================================
# WHAT A RELOAD HAS TO PUT BACK
#
# The body's own state and nothing else. Every number here is one a player
# would notice missing: where they are standing, which way they are looking,
# what is in their purse and their bag, and whether they are sitting down.
#
# THE POSTURE FIELDS ARE SAVED EVEN THOUGH THEY ARE DERIVED, and that is
# deliberate rather than sloppy. `hip_m`, `seat_m`, `recline_m` and `wake_h`
# come from `station/player.py::posture` for this person's species and stature,
# so they ARE rebuildable -- but only by `set_purse`, and only if the ledger the
# reload finds still holds this npc_id. Saving them means a body whose ledger
# entry has gone can still sit down at its own hip height instead of refusing.
# They are re-derived and overwritten the moment a real purse arrives.
#
# NOT SAVED: `gravity_mode`, `omega2`, `gravity_m_s2`, `eye_height_m` and the
# speeds. Those are the WORLD's statement about the deck this body is standing
# on -- `main.gd` computes `omega2` from the station's own spin period at boot
# -- and a save file that carried them would let a stale snapshot quietly
# override a corrected field. That is the exact shape of the 4q defect where
# nothing set `gravity_m_s2` and a 9.81 export default stood on a 7.454 m/s^2
# deck; the cure there was to derive it at the point of use, and a save file is
# not a point of use.
#
# AND NOT SAVED, AS OF ROUND 4: `tier` AND `tier_name`. THE FIX ABOVE WAS
# APPLIED TO ONE OF THIS FILE'S TWO PURSE LOADERS AND NOT TO THE OTHER, which is
# this project's "fix the entry, not the table" defect committed inside the very
# commit that quotes it. Round 3 taught `set_purse` to derive the rung -- and
# forty lines below its own docstring saying *"the minimal fix is the wrong fix
# ... it stores the rung as a fact. Do not add it."*, `save_state` wrote
# `"tier": tier` into the savegame and `load_state` read it back verbatim with
# `tier = int(d.get("tier", tier))`. Two loaders, one fixed.
#
# AND THE ORDER MADE IT WIN. `save.gd::audit` SORTS the subject names, `capture`
# inserts in that order and `restore` walks `state.keys()` -- so "interact"
# restores before "player". `interact.gd::load_state` calls `set_purse` and
# derives the rung correctly; `player.gd::load_state` then overwrote it from the
# stored copy, forty lines later, and the derivation was computed and thrown
# away. A hostile verifier reproduced it with prints and forced a `transit` rung
# back onto a revoked card with `SAVE gate=PASS` beside it.
#
# THE CURE IS NOT "SAVE IT LAST" AND IT IS NOT "DO NOT OVERWRITE". Both are
# statements about ordering, and ordering is what made the defect invisible. The
# cure is that there is exactly ONE writer of `tier` in this file --
# `set_purse`, via `rung_of` -- and `load_state` reaches the rung by calling it,
# never by assigning. The rung is then order-independent: whichever of the two
# loaders runs last, the last thing that touched the rung derived it.
# ===========================================================================

func save_state() -> Dictionary:
	var d := {
		"pos": [global_position.x, global_position.y, global_position.z],
		"yaw": _yaw,
		"pitch": _pitch,
		"npc_id": npc_id,
		"person": person,
		"credits": credits,
		"carrying": carrying.duplicate(),
		"carry_cap": carry_cap,
		"hip_m": hip_m,
		"seat_m": seat_m,
		"recline_m": recline_m,
		"wake_h": wake_h,
		"seated": seated,
		"seat_used_m": seat_used_m,
	}
	if _saved_rung_forced():
		# CONTROL --player-saved-rung: the pre-round-4 pair of lines, restored.
		# With --player-stale-save the number written is the DOCUMENT's frozen
		# report instead of the derived rung -- a save file written before the
		# conviction landed, which is the case that does the damage.
		d["tier"] = (tier_stored if _stale_save_forced() else tier)
		d["tier_name"] = ((_tier_label(tier_stored, "?")
			if _stale_save_forced() else tier_name))
	return d


func load_state(d: Dictionary) -> void:
	var p = d.get("pos", null)
	if typeof(p) == TYPE_ARRAY and p.size() == 3:
		global_position = Vector3(float(p[0]), float(p[1]), float(p[2]))
		# A LOADED BODY IS NOT FALLING. Without this it inherits whatever
		# velocity the boot spawn had built up over the frames before the
		# restore, and lands somewhere other than where it was saved.
		velocity = Vector3.ZERO
	_yaw = float(d.get("yaw", _yaw))
	_pitch = float(d.get("pitch", _pitch))
	# The look is applied to the body and camera immediately rather than waiting
	# for the next `step`, so a restore with no input still faces the right way.
	transform.basis = Basis(Vector3.UP, _yaw) if gravity_mode == "deck" \
		else transform.basis
	if _cam != null:
		_cam.transform.basis = Basis(Vector3.RIGHT, -_pitch)

	npc_id = String(d.get("npc_id", npc_id))
	person = String(d.get("person", person))
	credits = float(d.get("credits", credits))
	var bag = d.get("carrying", null)
	if typeof(bag) == TYPE_ARRAY:
		carrying.clear()
		for x in bag:
			carrying.append(String(x))
	carry_cap = int(d.get("carry_cap", carry_cap))
	hip_m = float(d.get("hip_m", hip_m))
	seat_m = float(d.get("seat_m", seat_m))
	recline_m = float(d.get("recline_m", recline_m))
	wake_h = float(d.get("wake_h", wake_h))
	seated = String(d.get("seated", seated))
	seat_used_m = float(d.get("seat_used_m", seat_used_m))

	# THE RUNG IS RE-DERIVED HERE, NOT RESTORED -- and it is re-derived rather
	# than merely left alone, because "left alone" is a claim about which loader
	# ran first and that claim is what was wrong. `_purse_doc` is the last purse
	# `set_purse` was handed, and `interact.gd::load_state` has by now pushed the
	# RESTORED ledger's purse through `set_purse`, so this is the restored record
	# going through `rung_of` a second time with the same answer. If some future
	# ordering runs this file first instead, `interact.gd` derives it afterwards
	# and the answer is the same. There is no ordering in which a stored number
	# is the last word.
	var had_stored := d.has("tier")
	if _saved_rung_forced():
		# CONTROL --player-saved-rung: the pre-round-4 lines, verbatim. The rung
		# is whatever the SAVE FILE said, over the top of the derivation
		# `interact.gd::load_state` made three calls ago.
		tier = int(d.get("tier", tier))
		tier_name = String(d.get("tier_name", tier_name))
		rung_why = ("CONTROL %s: restored from the save file, "
			% ("--player-stale-save" if _stale_save_forced()
				else "--player-saved-rung")
			+ "which is the defect round 4 exists for")
		print("player: rung %d %s RESTORED FROM THE SAVE FILE -- %s"
			% [tier, tier_name, rung_why])
		return
	var note := ""
	if had_stored:
		note = (" (the save file carried tier=%s %s, which is a REPORT and was "
			% [d.get("tier"), d.get("tier_name", "-")] + "discarded)")
	if not _purse_doc.is_empty():
		set_purse(_purse_doc)
		print("player: rung %d %s RE-DERIVED after load%s -- %s"
			% [tier, tier_name, note, rung_why])
	elif had_stored:
		# A SAVE FROM A BUILD THAT STORED THE RUNG, LOADED WITH NO LEDGER BEHIND
		# IT. The honest answer is that this body has no card reading, not the
		# number the old file happens to carry -- restoring it is the defect.
		print("player: the save file reports tier=%s %s and there is no purse "
			% [d.get("tier"), d.get("tier_name", "-")]
			+ "to derive from -- the rung stays UNREAD (%d %s). The ledger this "
			% [tier, tier_name]
			+ "save belongs to is missing.")
	_eye_now = seated_eye(seat_used_m) if seated != "" else eye_height_m
