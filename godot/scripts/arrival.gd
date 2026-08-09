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
## Frames allowed per step before `--arrival-test` gives up on it and moves on.
## IT APPLIES TO THE TEST ONLY -- a player has no deadline; see the note at its
## use site in `_physics_process` for why that distinction cost the shipped
## arrival sequence.
##
## AND THE ARITHMETIC HERE WAS WRONG, WHICH IS HOW 600 LOOKED SUFFICIENT. The old
## comment read "at 60 Hz and 4.2 m/s a body covers 70 m in 1000 frames" -- true,
## and the value beside it is 600, which is 10 s and 42 m. The shipped spawn is
## 181 m of arc from the customs reader, so the default was short by a factor of
## four for the one sequence it exists to drive. `--arrival-budget` overrides it
## and the customs runs in CI pass one.
@export var step_budget: int = 600

# ===========================================================================
#  THE CARD IS READ AT RUNTIME, AND THE VERDICT IS NOT IN THE FILE
# ===========================================================================
## WHAT THIS CLOSES, AND IT IS THE WHOLE POINT OF AN ARRIVAL. Until session 4u
## the sidecar carried `"status": "admitted"` and `"verdict": "Cleared. Welcome
## to Babylon 5."` -- computed by `station/arrival.py::checks` BEFORE the game
## started -- and `_verdict()` printed those two strings. A player who walked to
## the reader and pressed it got the same sentence as a player who did not, and
## a card with its visa struck off got the same sentence as a valid one. That is
## not a customs post, it is a caption.
##
## SO THE TEN STATIONS ARE EVALUATED HERE, AGAINST THE CARD IN THE PLAYER'S
## HAND, at the moment the reader is operated. `interact.gd::_verb_operate`
## calls `customs_verdict()`; nothing reads `seq["status"]` or `seq["verdict"]`
## to decide anything any more. Both are still PRINTED, beside the runtime
## answer, because a disagreement between them is evidence and hiding it would
## be throwing the control away.
##
## WHICH STATIONS ARE RE-DERIVED AND WHICH ARE INHERITED, stated per row rather
## than blurred. Five of the ten stations read a field the prop actually carries
## (3 presented, 5 record, 6 visa, 7 atmosphere, 8 telepath) and those are
## computed here from `_card_fields`. The other five are not facts about the
## card at all -- 1 and 2 are the ramp and the queue, 4 is a genetic match this
## project does not model as a forgeable item, 9 is a contraband draw on
## (npc_id, day, seed) -- so they are taken from the sidecar's own `checks`
## rows, which is READING A DERIVED INPUT rather than copying a rule. Every row
## in the result says which it was, in `from`.
##
## THE RULES ARE `station/arrival.py`'S AND ARE PORTED, NOT INVENTED.
## `entry_class` below is that function line for line; the severity ladder is
## `_SEVERITY`; the three verdict sentences are the ones in `arrival.py:777`;
## `outcome_of`'s "PASS/FLAG both admit" is `_outcome_of`. A second SET of rules
## would be this repository's most-repeated defect. What makes the port checkable
## rather than trusted is `_agree`: on the UNMODIFIED card this file's
## `entry_class` must return the class Python already wrote into
## `seq["entry_class"]`, and the arrival line prints whether it did.
const PASS := "pass"
const FLAG := "flag"
const REFER := "refer"
const REFUSE := "refuse"
const SEVERITY := {"pass": 0, "flag": 1, "refer": 2, "refuse": 3}

const ADMITTED := "admitted"
const REFERRED := "referred"
const REFUSED := "refused"

## `arrival.py:777`. Not paraphrased: the same three sentences, so a player hears
## what the Python half says they hear.
const VERDICT_LINE := {
	"admitted": "Cleared. Welcome to Babylon 5.",
	"referred": "Step aside, please. Secondary inspection.",
	"refused": "You are not going anywhere. Hold him.",
}

## `arrival.py::entry_class`'s five classes and its expiry suffix.
const EA_CITIZEN := "ea_citizen"
const RESIDENT := "resident"
const TRANSIT := "transit"
const SANCTUARY := "sanctuary"
const NO_STATUS := "no_status"
const EXPIRED_SUFFIX := " -- EXPIRED"

## The item a customs reader is looking for. `station/player.py::IDENTICARD`.
const IDENTICARD_ITEM := "identicard"

## The card as the player is carrying it: label -> value. Built once from the
## sidecar and then STRUCK by `--card-drop`, so the thing the reader reads and
## the thing the card face draws are one dictionary and cannot disagree.
var _card_fields := {}
## Which labels `--card-drop` struck, in the order given. The negative control
## for the whole loop: a run with this empty must ADMIT and a run naming the
## fields the visa hangs on must REFUSE, and both go through this same code.
var _card_dropped: Array[String] = []
## The last runtime verdict, or {} until the reader has been used.
var _customs := {}
## Does this file's `entry_class` agree with Python's, on the untouched card?
var _agree := "unchecked"

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

	# THE CARD IS BUILT BEFORE `super._ready()`, not after, and the ordering is
	# load-bearing rather than tidy. `walk.gd::_make_interact` -> `watch()` reads
	# the ledger and hands the body a purse during that call, and `_my_purse`
	# asks THIS node who is playing (`player_npc_id`). A card built afterwards
	# would be a card that arrived one function too late to name the player, and
	# the body would carry ANNA ALLAN's wallet again -- see `player_identity`.
	_build_card()

	# walk.gd does all of the loading, dressing, collision, doors, crowd and
	# HUD, and its own args still win over anything adopted above.
	super._ready()
	_load_boxes()
	_build_plan()
	# THE READER NEEDS A CARD TO READ, AND IT IS THIS NODE THAT HAS ONE.
	# `interact.gd` holds no customs rule and no identicard -- it dispatches the
	# verb and asks whoever owns the card. On a `walk.gd` build nothing answers
	# and `operate` on a reader says so rather than inventing a verdict.
	if _interact != null and _interact.has_method("bind_card"):
		_interact.call("bind_card", self)
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
	if args.has("arrival-budget"):
		# HOW FAR A STEP IS ALLOWED TO WALK, and 600 frames is not far enough on
		# the SHIPPED build. `boot.json` spawns the body in the CORRIDOR
		# (`spawn_at: "corridor"`, ring angle 89.3 deg) and the customs hall's
		# reader stands at 40.0 deg, which is 181 m of arc at r=211 m. Measured:
		# 600 frames buys 54-68 m, so every customs step timed out 174 m short
		# and the sequence could not reach its own verdict on the build a player
		# launches. That is a property of the walk, not of the reader, and the
		# right cure is a navmesh -- see `_physics_process`'s note on the
		# bug-algorithm sidestep. Until there is one, this says how long to try.
		step_budget = maxi(1, int(args["arrival-budget"]))
		print("arrival: step budget %d frames (default 600) -- the shipped spawn "
			% step_budget + "is 181 m of corridor from the customs reader")
	if args.has("arrival-from"):
		# WHERE THE PLAN STARTS, AND WHY THAT IS NOT THE SAME AS CAPPING IT.
		# `--arrival-steps` cuts from the END, which on this build keeps the two
		# steps a body cannot reach: `blue_0_0_z7440.glb` carries the z7120
		# docking bays as well as the z7440 halls, so `berth` and `disembark`
		# resolve to real mesh 364 m down the axis -- measured, closest approach
		# 419.7 m and 399.8 m against a 600-frame budget that buys 68 m. They are
		# on the build and they are not reachable inside a step, which is a
		# different thing from `offbuild` and is why they are not silently
		# dropped. This cuts from the FRONT so a run can start at the customs
		# hall the body actually spawns in, and says what it skipped.
		var from_id := String(args["arrival-from"])
		var cut := 0
		for i in plan.size():
			if String((plan[i]["step"] as Dictionary).get("id", "")) == from_id:
				cut = i
				break
		if cut > 0:
			var skipped := PackedStringArray()
			for i in cut:
				skipped.append(String((plan[i]["step"] as Dictionary).get("id", "?")))
			plan = plan.slice(cut)
			print("arrival: --arrival-from=%s skips %d step(s) BEFORE it (%s) -- "
				% [from_id, cut, ", ".join(skipped)]
				+ "they are on this build and are not walked in this run")
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


# ===========================================================================
#  THE CARD IN THE PLAYER'S HAND
# ===========================================================================
## THE ONE COPY OF THE CARD THIS SESSION IS PLAYING WITH.
##
## `--card-drop=VISAS,ORIGIN` strikes fields off it, and that flag is the
## negative control the whole consequence loop is worth nothing without: a
## refusal branch that cannot be reached on demand is a branch nobody can show
## you. It strikes by LABEL, which is the prop's own vocabulary
## (`npc/resident.py::CARD`), so a typo names a field that does not exist and is
## reported instead of silently doing nothing.
func _build_card() -> void:
	_card_fields.clear()
	_card_dropped.clear()
	var order := PackedStringArray()
	for r in seq.get("identicard", []):
		if typeof(r) != TYPE_DICTIONARY:
			continue
		var label := String((r as Dictionary).get("label", ""))
		if label == "":
			continue
		_card_fields[label] = String((r as Dictionary).get("value", ""))
		order.append(label)
	var a := _args()
	if a.has("card-drop"):
		for raw in String(a["card-drop"]).split(",", false):
			var label := String(raw).strip_edges().to_upper()
			if label == "":
				continue
			if not _card_fields.has(label):
				push_error("arrival: --card-drop=%s names no field on this card "
					% label + "-- the nine are %s" % ", ".join(order))
				continue
			if String(_card_fields[label]) == "":
				print("arrival: --card-drop=%s was ALREADY empty on this card, "
					% label + "so striking it changes nothing")
			_card_fields[label] = ""
			_card_dropped.append(label)
	# THE PORT IS CHECKED AGAINST THE THING IT IS A PORT OF, on every run, before
	# anything is decided. `seq["entry_class"]` is `station/arrival.py`'s own
	# answer for the untouched card; if this file's `entry_class` disagrees the
	# verdict below is computed by a rule that has drifted, and a silent
	# disagreement is exactly the shape of defect this repository keeps paying
	# for. Checked on the ORIGINAL fields, so a `--card-drop` run still reports
	# whether the port is sound.
	var orig := {}
	for r in seq.get("identicard", []):
		if typeof(r) == TYPE_DICTIONARY:
			orig[String((r as Dictionary).get("label", ""))] = String(
				(r as Dictionary).get("value", ""))
	var mine: Array = entry_class(orig)
	var theirs := String(seq.get("entry_class", ""))
	_agree = ("agrees:%s" % theirs if String(mine[0]) == theirs
		else "DISAGREES:gd=%s/py=%s" % [String(mine[0]), theirs])
	print("arrival: identicard %s -- %d field(s), %s; entry_class %s (%s), "
		% [String(seq.get("card_name", "?")), _card_fields.size(),
			("nothing struck" if _card_dropped.is_empty()
				else "STRUCK " + ", ".join(_card_dropped)),
			String(mine[0]), String(mine[2])]
		+ "port %s" % _agree)


## Who this session is playing, for `interact.gd::_my_purse`. THE ARRIVAL
## SIDECAR IS THE ONLY THING IN THE BUILD THAT KNOWS. `economy.json` is keyed by
## npc_id and carries `player:downbelow`; the sequence's player is
## `player:player`, and until this method existed the wallet on the HUD named a
## different person from the card in the hand.
func player_npc_id() -> String:
	return String(seq.get("npc_id", ""))


## `consequence.TIERS`' six rungs, by the labels the bake writes. Ported for one
## reason and it is a narrow one: a MINTED purse has no `tier` field, and
## `player.gd::rung_of` reads that field as the card's own frozen reading when
## the record is empty -- so a purse without it hands the body rung -99 and every
## counter, checkpoint and ladder in the build then misreads a live card. This is
## the card's READING and not a stored derivation, which is the distinction
## `interact.gd::_sync_purse`'s header draws in as many words.
const TIER_NAME := {0: "no_status", 1: "sanctuary", 2: "transit",
	3: "resident", 4: "citizen", 5: "accredited"}
## `consequence.ACCREDITED_ROLES`.
const ACCREDITED_ROLES := ["diplomat", "envoy"]


## `consequence.tier_of`, on the card as it reads NOW. No record is consulted --
## custody and revocation are the record's half and `player.gd::rung_of` already
## applies them on top of this number, which is exactly the split Python makes.
func card_rung() -> int:
	if ACCREDITED_ROLES.has(String(seq.get("role", ""))):
		return 5
	var ec: Array = entry_class(_card_fields)
	if bool(ec[1]):
		return 0                      # expired is not a lesser permission
	return {EA_CITIZEN: 4, RESIDENT: 3, TRANSIT: 2, SANCTUARY: 1,
		NO_STATUS: 0}[String(ec[0])]


## Enough to MINT a purse when the ledger has none for this person, and not one
## field more. Every value is read out of the sidecar `station/arrival.py`
## already derived -- credits from `player.credits_for`, name and species and
## role from the same `resident()` that mints every other person aboard -- so
## this is reading a generated artefact rather than re-deriving anybody. The two
## exceptions are `tier`/`tier_name`, and `card_rung` above says why they cannot
## be left out.
func player_identity() -> Dictionary:
	var rung := card_rung()
	return {
		"npc_id": player_npc_id(),
		"name": String(seq.get("card_name", seq.get("name", ""))),
		"species": String(seq.get("species", "")),
		"role": String(seq.get("role", "")),
		"credits": float(seq.get("credits", 0.0)),
		"carrying": [IDENTICARD_ITEM, "kit_bag"],
		"at": "docking_bays",
		"status": "unprocessed",
		"quarters": "",
		"tier": rung,
		"tier_name": String(TIER_NAME.get(rung, "")),
		"generated": true,
	}


## The nine fields as the card reads NOW: (label, value, state). A struck field
## comes back EMPTY, which is the prop's red row with no colon -- so the drop is
## visible on the card face as well as in the verdict, and a player can see the
## reason they were refused.
func identicard_rows() -> Array:
	var out := []
	for r in seq.get("identicard", []):
		if typeof(r) != TYPE_DICTIONARY:
			continue
		var label := String((r as Dictionary).get("label", ""))
		var value := String(_card_fields.get(label, ""))
		out.append([label, value, ("filled" if value != "" else "empty")])
	return out


func card_dropped() -> Array:
	return _card_dropped.duplicate()


# ===========================================================================
#  THE TEN STATIONS, RESOLVED AGAINST THAT CARD
# ===========================================================================
## `station/arrival.py::entry_class`, ported line for line. Returns
## [class, expired, the field it was read off].
##
## ONE INPUT IT CANNOT SEE, NAMED RATHER THAN GUESSED. Python reads `card.job`
## in its last branch to tell a RESIDENT from a NO_STATUS; a job is not one of
## the nine fields on the prop and the sidecar does not carry one, so this
## cannot know it. The branch is only reached by a card with NO visa and a
## non-EARTH origin, and it says in its own `why` that the job was unknown --
## which is the honest answer and is why the returned reason is a sentence
## rather than a flag.
func entry_class(fields: Dictionary) -> Array:
	var v := String(fields.get("VISAS", ""))
	var expired := v.ends_with(EXPIRED_SUFFIX)
	var base := (v.substr(0, v.length() - EXPIRED_SUFFIX.length()) if expired
		else v)
	if base.begins_with("TRANSIT"):
		return [TRANSIT, expired, "VISAS=%s" % v]
	if base.begins_with("SANCTUARY"):
		return [SANCTUARY, expired, "VISAS=%s" % v]
	if base.begins_with("NO STATUS"):
		return [NO_STATUS, expired, "VISAS=%s" % v]
	if String(fields.get("ORIGIN", "")) == "EARTH":
		return [EA_CITIZEN, false, "ORIGIN=EARTH"]
	return [NO_STATUS, false, "ORIGIN=%s, VISAS empty, no job on the card"
		% (String(fields.get("ORIGIN", "")) if String(fields.get("ORIGIN", "")) != ""
			else "(struck)")]


## `arrival.py::outcome_of` -- PASS and FLAG both admit; REFER and REFUSE do not.
func _outcome_of(worst: int) -> String:
	if worst <= SEVERITY[FLAG]:
		return ADMITTED
	return REFERRED if worst == SEVERITY[REFER] else REFUSED


## The sidecar's own row for station `n`, or {}. Used for the five stations that
## are not facts about the card -- see the header block above.
func _baked_check(n: int) -> Dictionary:
	for r in seq.get("checks", []):
		if typeof(r) == TYPE_DICTIONARY and int((r as Dictionary).get("n", 0)) == n:
			return r
	return {}


func _inherit(n: int, station: String, auth: int) -> Dictionary:
	var b := _baked_check(n)
	return {"n": n, "station": String(b.get("station", station)),
		"auth": int(b.get("auth", auth)),
		"result": String(b.get("result", PASS)),
		"detail": String(b.get("detail", "")), "from": "sidecar"}


func _row(n: int, station: String, auth: int, result: String,
		detail: String) -> Dictionary:
	return {"n": n, "station": station, "auth": auth, "result": result,
		"detail": detail, "from": "card"}


## THE VERDICT, COMPUTED NOW, FROM THE CARD THIS BODY IS CARRYING.
##
## `has_card` is the player's INVENTORY answer -- `player.gd::carrying` holds
## `identicard` as an item because `station/player.py` makes it one and 6.4
## makes losing it an arc. It is passed in rather than read here because the
## body belongs to `interact.gd`, which is the node that dispatched the verb.
func customs_verdict(has_card: bool, place: String = "") -> Dictionary:
	var rows := []
	rows.append(_inherit(1, "Disembark", 4))
	rows.append(_inherit(2, "Queue", 5))

	if not has_card:
		rows.append(_row(3, "Identicard presented", 1, REFUSE,
			"NO IDENTICARD. 6.4: the card is passport, licence, credit and "
			+ "medical file at once -- without it there is no record to pull"))
		rows.append(_row(10, "Admit / refer / refuse", 5, REFUSE,
			"held pending identity; 6.3 station 10"))
		return _close(rows, place)
	rows.append(_row(3, "Identicard presented", 1, PASS,
		"inserted into the reader"))
	rows.append(_inherit(4, "Genetic match", 4))

	# 5. THE RECORD, REBUILT FROM WHAT IS STILL ON THE CARD. Python joins the
	# FILLED fields; a struck field simply is not in the sentence, so the record
	# a refused player is read back is visibly shorter than a clean one.
	var filled := PackedStringArray()
	for r in identicard_rows():
		if String(r[2]) == "filled":
			filled.append("%s=%s" % [String(r[0]), String(r[1])])
	rows.append(_row(5, "Record pulled", 1, PASS, " / ".join(filled)))

	# 6. VISAS.
	var ec: Array = entry_class(_card_fields)
	var cls := String(ec[0])
	var expired: bool = bool(ec[1])
	var why := String(ec[2])
	if expired:
		rows.append(_row(6, "Visa checked", 1, REFUSE,
			"%s -- FACTIONS.md 3.4 calls expired status the station's most " % why
			+ "ordinary crime"))
	elif cls == EA_CITIZEN:
		rows.append(_row(6, "Visa checked", 1, PASS,
			"%s: Earth Alliance sovereign territory, entry by right, " % why
			+ "VISAS properly empty"))
	elif cls == RESIDENT:
		rows.append(_row(6, "Visa checked", 1, PASS,
			"%s: standing is the residency record, not a visa" % why))
	elif cls == TRANSIT:
		rows.append(_row(6, "Visa checked", 1, PASS,
			"%s (FACTIONS.md 2.3)" % why))
	elif cls == SANCTUARY:
		rows.append(_row(6, "Visa checked", 1, REFER,
			"%s: stateless -- referred to immigration (FACTIONS.md 6.2's " % why
			+ "13,000)"))
	else:
		rows.append(_row(6, "Visa checked", 1, REFUSE,
			"%s -- FACTIONS.md 3.4, and the reason lurkers avoid readers" % why))

	# 7. DES/ATMOS. The prop writes it as `<DES>/<code>`; the code is what the
	# customs board's own subject is, so an unnumbered mix is a FLAG and not a
	# refusal -- the board says others "MAY BE CREATED BY PRIOR ARANGEMENT".
	var des := String(_card_fields.get("DES/ATMOS", ""))
	var code := (des.get_slice("/", 1) if des.find("/") >= 0 else "")
	if code != "":
		rows.append(_row(7, "Atmosphere declared", 1, PASS,
			"%s -- the standard mix" % des))
	else:
		rows.append(_row(7, "Atmosphere declared", 1, FLAG,
			"DES/ATMOS %s: unnumbered, the board says others \"MAY BE CREATED "
			% ("is struck" if des == "" else "reads %s" % des)
			+ "BY PRIOR ARANGEMENT\" (sic, authority 1)"))

	# 8. LICENSED PSI.
	if String(_card_fields.get("LICENSED PSI", "")) != "":
		rows.append(_row(8, "Telepath status", 1, FLAG,
			"LICENSED PSI: REGISTERED -- Psi Corps liaison notified "
			+ "(FACTIONS.md 4.1)"))
	else:
		rows.append(_row(8, "Telepath status", 1, PASS,
			"no registration on the record; an UNregistered telepath is not a "
			+ "field the prop carries and is not modelled"))

	rows.append(_inherit(9, "Scan", 4))
	return _close(rows, place)


## Station 10 is the worst of the nine, and the sentences are `arrival.py`'s.
func _close(rows: Array, place: String) -> Dictionary:
	var worst := 0
	var worst_row := {}
	for r in rows:
		if int((r as Dictionary).get("n", 0)) == 10:
			continue
		var s := int(SEVERITY.get(String((r as Dictionary).get("result", PASS)), 0))
		if s > worst:
			worst = s
			worst_row = r
	if worst_row.is_empty():
		worst_row = rows[0]
	var res := PASS
	for k in SEVERITY:
		if int(SEVERITY[k]) == worst:
			res = String(k)
	var detail: String = {
		"pass": "through to the arrival concourse",
		"flag": "through to the arrival concourse, with a note on the record",
		"refer": "secondary inspection -- station %d, %s"
			% [int(worst_row.get("n", 0)), String(worst_row.get("station", ""))],
		"refuse": "refused and held for the next ship out -- station %d, %s"
			% [int(worst_row.get("n", 0)), String(worst_row.get("station", ""))],
	}[res]
	var has_ten := false
	for r in rows:
		if int((r as Dictionary).get("n", 0)) == 10:
			has_ten = true
	if not has_ten:
		rows.append(_row(10, "Admit / refer / refuse", 5, res, detail))
	var status := _outcome_of(worst)
	_customs = {
		"status": status,
		"verdict": String(VERDICT_LINE.get(status, "")),
		"worst": res,
		"at_station": int(worst_row.get("n", 0)),
		"station": String(worst_row.get("station", "")),
		"why": String(worst_row.get("detail", "")),
		"disposal": detail,
		"place": place,
		"rows": rows,
		"dropped": _card_dropped.duplicate(),
		"port": _agree,
		"baked_status": String(seq.get("status", "")),
		"npc_id": player_npc_id(),
		"who": String(seq.get("card_name", "")),
	}
	return _customs


## The last runtime verdict, or {}. `interact.gd` and the card face both read it
## rather than each keeping one.
func customs() -> Dictionary:
	return _customs


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


## HOW FAR ROUND THE RING TO AIM, and a straight line is the wrong answer on a
## barrel.
##
## MEASURED, ON THE BUILD A PLAYER LAUNCHES. `boot.json` spawns the body in the
## corridor at ring angle 89.3 deg and the customs reader stands at 40.0 deg --
## 49.3 deg, which at r = 211.5 m is 182 m of floor. The chord between those two
## points dips 19 m INSIDE the ring, and the corridor is a few metres wide, so
## `target - p` points the body straight into the inner wall from the first
## frame. Run that way with a 9,000-frame budget it walked **402.95 m and closed
## 0.0 m**: ring angle 89.3 -> 89.0, 136 sidesteps, a body oscillating against a
## wall while the bug-algorithm heuristic flipped its sign. `_build_plan`'s own
## header already says that heuristic "would not get round a maze"; a 49-degree
## arc turns out to be enough of one.
##
## SO THE BEARING IS THE RING'S OWN. A corridor here is an arc at constant
## radius, so the way to reach an angle is to walk TANGENTIALLY towards it --
## `Vector3(0,0,1).cross(radial)` is the spinward tangent, the same expression
## `hud.gd` derives its heading tape from, signed by the short way round. The
## axial gap rides along as a small component so the body drifts to the target's
## z as it goes.
##
## IT IS STILL NOT A NAVMESH and this is not a claim that it is. It knows one
## fact about the station -- corridors run around the ring at constant r -- and
## it is right for exactly as long as that is true. Inside `NEAR_ARC_M` of the
## target it hands back to the straight line, because a reader against a side
## wall is not on the ring and the last few metres are the part the arc cannot
## express.
const NEAR_ARC_M := 8.0
const RING_TOL_DEG := 0.6


func _bearing(p: Vector3, target: Vector3) -> Vector3:
	var pr := Vector2(p.x, p.y)
	var tr := Vector2(target.x, target.y)
	if pr.length() < 1.0 or tr.length() < 1.0:
		return target - p
	var dang: float = wrapf(tr.angle() - pr.angle(), -PI, PI)
	var arc: float = absf(dang) * pr.length()
	if arc < NEAR_ARC_M or absf(rad_to_deg(dang)) < RING_TOL_DEG:
		return target - p
	var radial := Vector3(pr.x, pr.y, 0.0).normalized()
	var tangent := Vector3(0, 0, 1).cross(radial).normalized()
	var dz: float = target.z - p.z
	return tangent * signf(dang) + Vector3(0, 0, clampf(dz / 20.0, -0.5, 0.5))


# ---------------------------------------------------------------------------
# Driving it
# ---------------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	# walk.gd's SHOT phase settles the body itself and takes the picture from
	# where it lands. Stepping it a second time here would move the camera
	# between the settle and the grab, which is the sort of thing that produces
	# a frame nobody can reproduce.
	if _done and _hold_left > 0 and _player != null:
		_hold_tick(delta)
		return
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
		var dir := _bearing(p, target)
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

	# THE BUDGET IS A TEST DEVICE AND IT WAS BEING APPLIED TO PEOPLE.
	#
	# Everything else in this function already knows the difference -- the
	# autopilot forty lines up is gated on `_testing_arrival`, because a human at
	# a keyboard drives their own body. The TIMEOUT was not, so the sequence
	# advanced past a step after `step_budget` frames whether or not anybody had
	# asked it to. At 60 Hz that is ten seconds, and the walk from the shipped
	# spawn to the customs reader is 181 m of arc -- about forty-five seconds at
	# 4.2 m/s, and longer for a person who stops to look at anything. So a player
	# who paused to read the arrival announcement had their arrival skipped out
	# from under them, one step every ten seconds, and reached customs to find the
	# sequence finished without them.
	#
	# A test needs a bound because a stuck body must not hang CI forever. A PLAYER
	# HAS NO DEADLINE: the step ends when they get there, and if they never go,
	# the sequence waits. That is not a lenient budget, it is the absence of one,
	# which is the only correct answer for a thing a person is doing by hand.
	if arrived or (_testing_arrival and _frames_here > step_budget):
		_closest.append("%s:%.1fm" % [String(st.get("id", "?")), _min_d])
		if arrived:
			_reached.append(String(st.get("id", "?")))
		else:
			_timeouts.append(String(st.get("id", "?")))
		_advance()


## THE SEQUENCE IS NOT OVER WHILE SOMEBODY IS WALKING TOWARDS YOU.
##
## `--arrival-test` used to `quit(0)` on the frame the last step finished, which
## was correct while the last step was the end of everything that could happen.
## It is not any more: a refusal at the reader NOTIFIES SECURITY, and the pair
## then has to turn out, cross the floor and do something. Quitting on the press
## would kill the process between the cause and the effect and report the run as
## complete -- a consequence that is only ever measured before it happens.
##
## COSTS NOTHING ON THE ADMIT PATH, which is why it is a default rather than a
## flag: it is armed only when the runtime verdict was not `admitted`. A clean
## card quits exactly as fast as it did before.
@export var arrest_hold_frames: int = 1500
var _hold_left := 0


func _advance() -> void:
	step_i += 1
	_frames_here = 0
	_in_room_frames = 0
	_min_d = 1e30
	if step_i < plan.size():
		return
	_done = true
	_verdict()
	if not _testing_arrival:
		return
	var a := _args()
	if a.has("arrival-hold"):
		arrest_hold_frames = maxi(0, int(a["arrival-hold"]))
	var refused := (not _customs.is_empty()
		and String(_customs.get("status", "")) != ADMITTED)
	if refused and arrest_hold_frames > 0:
		_hold_left = arrest_hold_frames
		print("arrival: HOLDING %d frames after a %s verdict -- security has "
			% [arrest_hold_frames, String(_customs.get("status", ""))]
			+ "been notified and the run does not end before they arrive")
		return
	get_tree().quit(0)


## Stand still while the consequence plays, then say what came of it.
func _hold_tick(delta: float) -> void:
	_hold_left -= 1
	if _player != null:
		_player.step(delta, Vector2.ZERO, false, false)
	if _hold_left > 0:
		return
	var said := ""
	if _interact != null and _interact.has_method("enforcement_report"):
		said = String(_interact.call("enforcement_report"))
	print("arrival: AFTER THE REFUSAL -- %s"
		% (said if said != "" else "nothing in this build answered it"))
	get_tree().quit(0)


## One line, and every number on it is a claim a player would notice.
##
## `steps` is how much of the sequence this build could play at all, `reached`
## how much the body actually walked to, `reader` whether the identicard went
## into the reader that decides the outcome, and `offfloor` whether it stayed on
## the deck getting there. `outcome` is what the station decided about this
## person -- the thing the whole first ten minutes is for.
func _verdict() -> void:
	# `outcome` IS THE RUNTIME ANSWER AND NOTHING ELSE. It used to be
	# `seq["status"]`, a string `station/arrival.py` wrote before the process
	# started, printed identically whether or not the body ever reached the
	# reader. It is now whatever the ten stations decided when the card went in,
	# and `outcome_source` says which -- `runtime` when a reader was operated,
	# `NOT-COMPUTED` when it was not. The baked answer is still printed, as
	# `baked=`, because the two agreeing is worth seeing and the two disagreeing
	# is worth seeing more.
	var runtime := not _customs.is_empty()
	print(("ARRIVAL who=%s species=%s ship=%s bay=%s hall=%s area=%s "
		+ "entry=%s outcome=%s outcome_source=%s baked=%s worst=%s "
		+ "at_station=%s card_struck=%s port=%s quarters=%s unit=%s "
		+ "steps=%d/%d reached=%d timeout=%d offbuild=%d "
		+ "reader_used=%s path_m=%.2f offfloor=%d sidesteps=%d "
		+ "interactables=%d") % [
		String(seq.get("name", "-")).replace(" ", "_"),
		seq.get("species", "-"), String(seq.get("ship", "-")).replace(" ", "_"),
		seq.get("bay_label", "-"), seq.get("hall", "-"),
		str(int(seq.get("area", 0))), seq.get("entry_class", "-"),
		(String(_customs.get("status", "-")) if runtime else "NOT-COMPUTED"),
		("runtime" if runtime else "none-the-reader-was-not-used"),
		String(seq.get("status", "-")),
		(String(_customs.get("worst", "-")) if runtime else "-"),
		(str(int(_customs.get("at_station", 0))) if runtime else "-"),
		("none" if _card_dropped.is_empty() else "+".join(_card_dropped)),
		_agree,
		seq.get("destination", {}).get("place", "-"),
		String(seq.get("unit", "-")) if String(seq.get("unit", "")) != "" else "-",
		plan.size(), _steps().size(), _reached.size(), _timeouts.size(),
		offbuild.size(), str(_used_reader).to_lower(), _arr_path_m,
		_arr_off_floor, _slides,
		(0 if _interact == null else _interact.count())])
	if runtime:
		print("arrival: VERDICT %s -- \"%s\" (%s)"
			% [String(_customs.get("status", "")).to_upper(),
				String(_customs.get("verdict", "")),
				String(_customs.get("disposal", ""))])
		for r in _customs.get("rows", []):
			print("arrival:   station %2d %-24s auth %d  %-6s [%s] %s"
				% [int((r as Dictionary).get("n", 0)),
					String((r as Dictionary).get("station", "")),
					int((r as Dictionary).get("auth", 0)),
					String((r as Dictionary).get("result", "")).to_upper(),
					String((r as Dictionary).get("from", "?")),
					String((r as Dictionary).get("detail", "")).left(96)])
	else:
		print("arrival: NO VERDICT -- the identicard reader was never operated, "
			+ "so nothing decided anything. The sidecar's baked \"%s\" is NOT "
				% String(seq.get("status", "-"))
			+ "used as a substitute.")
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


## THE LINE ACROSS THE TOP OF THE FRAME, AND IT IS THE RUNTIME VERDICT.
##
## It used to return `seq["verdict"]` -- the baked sentence -- the moment the
## last step finished, whether or not the reader had been touched. So a player
## who walked past the reader and out of the hall was told "Cleared. Welcome to
## Babylon 5." by a station that had never read their card. Now the sentence
## exists only once something decided it, and a refusal says so on the frame the
## reader says it: this is the surface `hud.gd` does not own, so the answer
## reaches the player with no change to any file this session does not hold.
func current_text() -> String:
	if not _customs.is_empty():
		var s := String(_customs.get("status", ""))
		var line := String(_customs.get("verdict", ""))
		if s != ADMITTED:
			return "%s -- %s  (station %d, %s)" % [s.to_upper(), line,
				int(_customs.get("at_station", 0)),
				String(_customs.get("station", ""))]
		return line
	if _done:
		return ""
	if step_i < plan.size():
		return String(plan[step_i]["step"].get("text", ""))
	return ""


func card_lines() -> Array:
	## The nine fields, in the prop's order, with the prop's two states -- as the
	## card READS NOW rather than as it was baked. A field `--card-drop` struck
	## comes back EMPTY and the face draws it red with no colon, which is the
	## whole point: the player can see the reason the reader refused them on the
	## same panel as the refusal.
	if not _used_reader:
		return []
	return identicard_rows()


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
