extends Node3D
##
## THE PLAYER'S NOTEBOOK, AND THE THING THAT MAKES TIME PASSING COST SOMETHING.
##
## `docs/MASTER-PLAN.md` R7 counted the journal ten times in the spec and zero
## times in the plan; `station/spec_harness/ply.py` searched the whole tree and
## reported *"a journal exists nowhere in station/, godot/ or tools/"*. What it
## is FOR is not a list widget. The scope document asks for *"an information
## layer the player can use"* and for a simulation that *"exists around you
## rather than in text"* -- and until this file existed, everything the station
## says was said into a void. A PA call at 03:11 that nobody can carry out of
## the room is set dressing; the same call written into a notebook with the
## hour and the source is a thing the player HAS.
##
## NOT ONE RULE IS DECIDED HERE. `station/journal.py` owns what a knowledge item
## is -- SYS-16's eight kinds, which of them go stale and after how long,
## CAST-05's eight standing ledgers, FAC-28's tells, and one real route time
## derived through `transit.py` -- and writes it to
## `station/generated/journal.json`. This file reads that manifest and carries
## no kind list, no staleness horizon and no ledger name. It is `interact.gd`'s
## relationship to `interact.py` and `dialogue.gd`'s to `dialogue.py`, for the
## reason both of those give: a second copy of a decision is the defect this
## repository has paid for three times.
##
## THE ID IS FNV-1a AND IT MUST AGREE WITH PYTHON'S, DIGIT FOR DIGIT. A fact
## minted in the engine under a different id from the one the offline station
## computes is a DIFFERENT fact, and nothing anywhere would notice: both halves
## would hold a plausible entry and neither could match the other's. So the
## manifest carries a five-string hash vector, `_check_hash()` runs it at load,
## and a mismatch REFUSES TO MINT rather than minting quietly -- because a
## notebook full of unmatchable ids is worse than an empty one. The vector's
## last two strings are non-ASCII on purpose: a port that hashes CODE POINTS
## instead of UTF-8 BYTES agrees on everything else and diverges on the first
## accented name in the cast.
##
## TIME COMPRESSION IS WITNESSING, AND THAT IS THE WHOLE MECHANIC. PLY-05 asks
## for SLEEP and WAIT to *"advance the station clock at compressed rate through
## the running simulation -- events still fire, stocks still move, the world
## does not pause"*. The hard part is not moving a clock; it is being able to
## SHOW that the world ran rather than skipped, and this project's own rule is
## that a gate which cannot fail passes on content that is wrong.
##
## `life.gd`'s Director is deliberately PURE in the hour -- its own header says
## *"nothing integrates, so 03:00 and 13:00 are two reads of the same
## expression"* -- so the crowd CANNOT tell a jump from a compression. It looks
## identical either way, which is exactly the trap. What can tell them apart is
## a thing that accumulates, and the journal is that thing: living from 22:00
## to 05:15 means hearing the 23:14 transport call, the 01:22 freighter and the
## 04:56 shuttle, each written down with its hour; jumping to 05:15 means
## hearing none of them, because you were not there.
##
## So `_process` advances a CURSOR through absolute station hours and mints
## from `broadcast.py`'s own day of timed calls as it passes each one -- and it
## refuses to witness a step the clock could not have taken continuously.
## `_continuous()` derives that bound from the clock's own rate and the frame's
## own delta rather than from a constant, so it holds at any compression.
##
## PERSISTENCE IS `save.gd`'s CONTRACT, both halves. `save_state`/`load_state`,
## and `main.gd::_subjects` offers this node by name. A journal with no save is
## R7's own phrase for it: *"a notebook that forgets"*.

## Where the station writes what a fact is. Relative to the repo root.
const MANIFEST_REL := "station/generated/journal.json"

## How much more than one frame's worth of station-time a step may be and still
## count as the clock RUNNING rather than JUMPING.
##
## DERIVED, NOT CHOSEN. One frame advances the clock by `rate * delta` exactly
## -- `life.gd::Director._process` is `clock.tick(delta)` and nothing else -- so
## the honest bound is that number with slack for a frame that hitched. Four is
## a frame taking four times its budget, which is a stutter; a jump is 7.25
## hours, which is 109x at the compression this gate runs. The two are not
## close, and nothing here needs them to be. INV-763.
const JUMP_TOL := 4.0

## The floor under that bound, in station hours, so the first frames after a
## scene load cannot be read as a jump.
const STEP_FLOOR_H := 0.02

## PLY-05's own scenario: sleep at 22:00 with a 05:15 intent. 7.25 station
## hours, taken from the row rather than picked. INV-764.
const SLEEP_H := 7.25

## Station hours per real second the compression gate multiplies the boot rate
## by when nothing says otherwise.
const DEFAULT_COMPRESS := 240.0

## How many timed calls the player must have been present for before a
## compressed run counts as having gone THROUGH the simulation. Derived: the
## boot deck's rooms hear 62 of `broadcast.day(0)`'s timed calls, which is one
## every 23 station-minutes, so 7.25 hours contains ~18 and any run that
## witnessed fewer than a quarter of them was not there for most of the night.
## INV-765.
const WITNESS_FLOOR := 4

# --- what the station decided ---------------------------------------------
var kinds: Array = []
var mutable_kinds: Array = []
var stale_after_days: int = 7
var standing_blocks: Dictionary = {}
var routes: Array = []
var marks: Dictionary = {}
var calls: Array = []                  # broadcast.py's timed day
var deck_rooms: Array = []             # which of them are audible here

# --- what the player knows -------------------------------------------------
var facts: Dictionary = {}             # fid -> fact dictionary
var people: Dictionary = {}            # npc_id -> CAST-05 memory slot
var standing: Dictionary = {}          # ledger -> scalar

# --- wiring ----------------------------------------------------------------
var _clock = null
var _dialogue = null
var _life = null
var _host = null
var _manifest_from := "nothing -- the journal cannot mint"
var _hash_ok := false
var _hash_why := "not checked"
var _refusals: Array[String] = []

# --- the witness cursor ----------------------------------------------------
var _cursor: float = -999.0
var _witnessed: int = 0
var _jumps: int = 0
var _jumped_h: float = 0.0
var _lived_h: float = 0.0
var _minting := true


func _init() -> void:
	# AFTER `life.gd`'s Director, which is 100. The Director ticks the clock;
	# this reads what the clock did. Reading it first would witness the
	# previous frame's hour every frame, which is a one-frame lie that nothing
	# would ever show.
	process_priority = 200


# ===========================================================================
#  The hash, and its twin in Python
# ===========================================================================
const FNV_OFFSET := -3750763034362895579      # 0xCBF29CE484222325 as int64
const FNV_PRIME := 1099511628211              # 0x100000001B3


## FNV-1a, 64-bit, over UTF-8 BYTES. `station/journal.py::fnv1a` is the twin.
##
## GDScript's `int` is a signed 64-bit two's-complement integer and its `*`
## wraps, so the BIT PATTERN this produces is identical to Python's masked
## unsigned arithmetic even though the printed decimal is not. `_hex64` is what
## makes that visible, and it is why the ids are compared as hex rather than as
## numbers.
static func fnv1a(s: String) -> int:
	var h := FNV_OFFSET
	for b in s.to_utf8_buffer():
		h = (h ^ int(b)) * FNV_PRIME
	return h


## Sixteen hex nibbles of a signed 64-bit value, low nibble last.
##
## `String.num_int64(h, 16)` is NOT this: it prints a signed value, so every
## hash with the top bit set comes out as `-3a1f...`, and half of all fact ids
## have the top bit set. The nibble walk has no sign to lose.
static func hex64(v: int) -> String:
	const D := "0123456789abcdef"
	var out := ""
	for i in range(15, -1, -1):
		out += D[(v >> (4 * i)) & 0xF]
	return out


static func fact_id(kind: String, subject: String, source_kind: String,
		source_key: String) -> String:
	return hex64(fnv1a("|".join(PackedStringArray(
		[kind, subject, source_kind, source_key]))))


# ===========================================================================
#  Install
# ===========================================================================
## Read the manifest, find the clock and the cast, and take the compression
## flag. Returns the number of knowledge kinds the station declared, or -1.
##
## FOUND BY CAPABILITY, NEVER BY NAME. `dialogue.gd::_find_director` makes the
## same argument in the same tree: a node that answers `hour()` is the clock
## whatever it is called, and a node called "Life" that does not is not. The
## host is passed because only `main.gd` owns the whole world, and it is asked
## for things by method rather than reached into.
func install(host) -> int:
	_host = host
	_minting = not _args().has("no-journal")
	if not _minting:
		print("journal: MINTING DISABLED (control) -- nothing will be learned")
	var root := _repo_root()
	var path := root.path_join(MANIFEST_REL)
	if not _read_manifest(path):
		push_warning("journal: no manifest at %s -- run "
			% path + "`python3 station/journal.py --emit`")
	_check_hash()
	_clock = _find_by_method(host, "hours_abs")
	_life = _find_by_method(host, "visible_count")
	# THE DIALOGUE NODE IS NOT LOOKED FOR HERE, AND THAT IS THE POINT.
	# `walk.gd::_wire_dialogue` builds it when the level -- or, in a streamed
	# build, a CELL -- arrives, which is after `main.gd::_ready` has finished.
	# Binding it at install would capture the tree at the load screen and hold
	# a null for ever, which is exactly the defect `main.gd::_rebind_on_stream`
	# was written for one node up: *"`bind` describes the tree at the instant it
	# was called, and in a streamed build that instant is the load screen"*.
	# `_dlg()` asks each time and caches only a hit.
	_load_calls(root)
	_apply_compression()
	print("journal: %d kinds, %d ledgers, %d timed calls audible on this deck "
		% [kinds.size(), standing_blocks.size(), calls.size()]
		+ "(%s); hash %s; clock=%s life=%s"
		% [_manifest_from, ("ok" if _hash_ok else "MISMATCH -- " + _hash_why),
			str(_clock != null), str(_life != null)])
	return kinds.size() if not kinds.is_empty() else -1


func _repo_root() -> String:
	# `res://` is `<repo>/godot`, so the repo root is one level up.
	#
	# THE TRAILING SLASH IS THE WHOLE OF THIS FUNCTION. `globalize_path("res://")`
	# returns `<repo>/godot/` WITH it, and `get_base_dir()` on a path that ends
	# in a separator returns the same directory again -- so the first version of
	# this returned `<repo>/godot` and every manifest read missed by one level.
	# It failed silently, because a missing manifest is a soft condition here:
	# the journal printed `0 kinds` and carried on. Found by launching the scene
	# and reading the line it prints, which is the only thing that finds this
	# class of defect -- a static scan sees a caller and not a wrong path.
	return ProjectSettings.globalize_path("res://").rstrip("/").get_base_dir()


func _read_manifest(path: String) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(d) != TYPE_DICTIONARY:
		return false
	kinds = d.get("kinds", [])
	mutable_kinds = d.get("mutable_kinds", [])
	stale_after_days = int(d.get("stale_after_days", 7))
	standing_blocks = d.get("standing_blocks", {})
	routes = d.get("routes", [])
	marks = d.get("marks", {})
	for k in standing_blocks.keys():
		standing[k] = 0.0
	_hash_why = "vector not in the manifest"
	_hash_vector = d.get("hash_vector", [])
	_manifest_from = path.get_file()
	return true


var _hash_vector: Array = []


## THE CROSS-LANGUAGE ASSERTION, and it is the one thing here that can make
## this file refuse to work. A fact id that differs between the station and the
## engine is a fact the two halves can never match, and neither would report an
## error: both would hold a plausible-looking entry. So a mismatch stops the
## minting instead of degrading it -- "a tool that silently degrades and exits 0
## manufactures evidence".
func _check_hash() -> void:
	if _hash_vector.is_empty():
		_hash_ok = false
		return
	for row in _hash_vector:
		if typeof(row) != TYPE_DICTIONARY:
			continue
		var s := String(row.get("s", ""))
		var want := String(row.get("h", ""))
		var got := hex64(fnv1a(s))
		if got != want:
			_hash_ok = false
			_hash_why = "fnv1a(%s) is %s here and %s in station/journal.py" % [
				JSON.stringify(s), got, want]
			return
	_hash_ok = true
	_hash_why = "%d vectors agree with station/journal.py" % _hash_vector.size()


## The day's timed broadcast calls, scoped to the rooms of the deck that booted.
##
## SCOPED, BECAUSE A CALL YOU CANNOT HEAR IS NOT AN EVENT YOU WITNESSED.
## `broadcast.py` carries each call's own `places` tuple and `boot.json` carries
## the rooms this deck has; the intersection is what a player standing here can
## actually hear, and it is 62 of the day's 174 on the boot deck.
func _load_calls(root: String) -> void:
	var boot := root.path_join("station/generated/scene/boot.json")
	deck_rooms = []
	if FileAccess.file_exists(boot):
		var bf := FileAccess.open(boot, FileAccess.READ)
		if bf != null:
			var bd = JSON.parse_string(bf.get_as_text())
			bf.close()
			if typeof(bd) == TYPE_DICTIONARY:
				deck_rooms = bd.get("rooms", [])
	var man := root.path_join(MANIFEST_REL)
	if not FileAccess.file_exists(man):
		return
	var f := FileAccess.open(man, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(d) != TYPE_DICTIONARY:
		return
	var all: Array = d.get("calls", [])
	calls = []
	for c in all:
		if typeof(c) != TYPE_DICTIONARY:
			continue
		var places: Array = c.get("places", [])
		for r in deck_rooms:
			if places.has(r):
				calls.append(c)
				break
	calls.sort_custom(func(a, b): return float(a["hour"]) < float(b["hour"]))


func _apply_compression() -> void:
	var a := _args()
	if not a.has("compress") or _clock == null:
		return
	var mult := float(a["compress"])
	if mult <= 0.0:
		return
	# THE BOOT RATE IS MULTIPLIED, NOT REPLACED. `main.gd` exports `clock_rate`
	# and `--rate=` already overrides it; a compression that SET the rate would
	# silently discard whichever of those the player was running at.
	_clock.rate = float(_clock.rate) * mult
	print("journal: TIME COMPRESSION x%.0f -- the clock now runs at %.4f "
		% [mult, float(_clock.rate)]
		+ "station hours a second, THROUGH the simulation")


# ===========================================================================
#  The witness -- what makes a compressed hour different from a skipped one
# ===========================================================================
func _process(delta: float) -> void:
	if _clock == null:
		return
	var now: float = float(_clock.hours_abs())
	if _cursor < -998.0:
		_cursor = now
		return
	var step := now - _cursor
	if step <= 0.0:
		return
	if not _continuous(step, delta):
		# A DISCONTINUITY IS A JUMP AND YOU CANNOT WITNESS WHAT YOU SKIPPED.
		# This is the entire difference between PLY-05's compressed sleep and
		# a fade to black, and it is the only place in this build where the two
		# are distinguishable at all -- `life.gd`'s crowd is pure in the hour
		# and looks identical after either.
		_jumps += 1
		_jumped_h += step
		_cursor = now
		return
	_witness_span(_cursor, now)
	_lived_h += step
	_cursor = now


## Could the clock have got here by ticking? `rate * delta` is exactly one
## frame's advance -- `life.gd::Director._process` ticks and does nothing else.
func _continuous(step: float, delta: float) -> bool:
	var one_frame: float = float(_clock.rate) * maxf(delta, 0.0)
	return step <= maxf(one_frame * JUMP_TOL, STEP_FLOOR_H)


## Mint one fact per timed call whose hour lies in (a, b].
func _witness_span(a: float, b: float) -> void:
	if calls.is_empty():
		return
	var d0 := int(floor(a / 24.0))
	var d1 := int(floor(b / 24.0))
	for d in range(d0, d1 + 1):
		for c in calls:
			var abs_h := float(d) * 24.0 + float(c["hour"])
			if abs_h <= a or abs_h > b:
				continue
			var place := _first_room_of(c)
			var fid := learn("rumour", place,
				String(c.get("text", "")),
				"you were standing in %s when it came over at day %d, %05.2f "
					% [place, d, float(c["hour"])]
					+ "(%s)" % String(c.get("source", "broadcast.py")),
				"overheard",
				"%s@%d:%s" % [String(c.get("kind", "pa")), d,
					("%.4f" % float(c["hour"]))],
				d, float(c["hour"]))
			if fid != "":
				_witnessed += 1


func _first_room_of(c: Dictionary) -> String:
	var places: Array = c.get("places", [])
	for r in deck_rooms:
		if places.has(r):
			return String(r)
	return "this deck"


# ===========================================================================
#  Minting
# ===========================================================================
## Write a knowledge item down. Returns its id, or "" if it was refused.
##
## EVERY REFUSAL IS NAMED AND KEPT. A journal that silently declined a fact
## would look exactly like a journal that was never offered one, and the
## difference is the whole of SYS-16's "minted ONLY by real events".
func learn(kind: String, subject: String, value: String, source: String,
		source_kind: String, source_key: String, day: int,
		hour: float) -> String:
	if not _minting:
		return ""
	if not _hash_ok:
		_refuse("the fact id does not agree with station/journal.py (%s)"
			% _hash_why)
		return ""
	if not kinds.is_empty() and not kinds.has(kind):
		_refuse("%s is not one of SYS-16's %d kinds" % [kind, kinds.size()])
		return ""
	if subject.strip_edges() == "":
		_refuse("a fact about nobody")
		return ""
	if source.strip_edges() == "":
		_refuse("a %s fact with no source event" % kind)
		return ""
	var fid := fact_id(kind, subject, source_kind, source_key)
	# RE-LEARNING SUPERSEDES. The same PA call heard again on day 3 is the same
	# fact re-dated, not a second entry -- `station/journal.py::learn` says the
	# same thing and for the same reason.
	facts[fid] = {
		"fid": fid, "kind": kind, "subject": subject, "value": value,
		"source": source, "source_kind": source_kind,
		"source_key": source_key, "day": day, "hour": hour,
		"state": "verified" if not mutable_kinds.has(kind) else "unverified",
	}
	return fid


func _refuse(why: String) -> void:
	_refusals.append(why)
	push_warning("journal refused: " + why)


## CAST-05 stage one: a face you would know again.
func see(npc_id: String) -> Dictionary:
	if not people.has(npc_id):
		people[npc_id] = {"face": false, "name_given": false, "name": "",
			"last_topic": "", "last_outcome": "", "favour": 0.0,
			"causes": [], "talks": 0}
	people[npc_id]["face"] = true
	return people[npc_id]


## CAST-05 stage two, and it is GIVEN. The row is explicit that a name is given
## in dialogue and *"not scraped from the card"*, so `see()` cannot set this and
## nothing here reads an identicard.
func given_name(npc_id: String, name: String, place: String, day: int,
		hour: float) -> String:
	var s := see(npc_id)
	s["name_given"] = true
	s["name"] = name
	return learn("name_given", npc_id, name,
		"%s gave you their name at %s, day %d, %05.2f"
			% [name, place, day, hour],
		"dialogue", npc_id, day, hour)


func name_given(npc_id: String) -> bool:
	return bool(people.get(npc_id, {}).get("name_given", false))


func note_talk(npc_id: String, topic: String, outcome: String,
		favour: float = 0.0, cause: String = "") -> void:
	var s := see(npc_id)
	s["talks"] = int(s["talks"]) + 1
	s["last_topic"] = topic
	s["last_outcome"] = outcome
	if favour != 0.0:
		if cause.strip_edges() == "":
			_refuse("a favour of %+.2f with no cause" % favour)
			return
		s["favour"] = float(s["favour"]) + favour
		(s["causes"] as Array).append("%+.2f %s" % [favour, cause])


func move_standing(block: String, delta: float, cause: String) -> float:
	if not standing.has(block):
		_refuse("%s is not one of CAST-05's ledgers" % block)
		return 0.0
	if cause.strip_edges() == "":
		_refuse("standing moved with no cause recorded")
		return float(standing[block])
	standing[block] = clampf(float(standing[block]) + delta, -100.0, 100.0)
	return float(standing[block])


## An incident the player was standing in the room for. `main.gd::_collapse`
## is the caller, and it passes `incident.py`'s own row -- so a journal entry
## for a collapse cites the ledger's `cid` and cannot be invented here.
func witness_collapse(row: Dictionary, who_fell: String, day: int) -> String:
	var cid := String(row.get("cid", ""))
	if cid == "":
		_refuse("an incident with no cid -- the ledger did not produce it")
		return ""
	var place := String(row.get("place", "?"))
	var hour := float(row.get("hour", 13.0))
	var who := String(row.get("who", ""))
	if who == "":
		who = who_fell
	return learn("incident_seen", cid, "%s, at %s" % [who, place],
		"you were standing in %s when it happened, day %d, %05.2f"
			% [place, day, hour],
		"incident", cid, day, hour)


## The porter's craft: a leg time the station derived, not one a line asserted.
## `station/journal.py::derived_routes` computed it through `transit.py`.
func learn_route(i: int, day: int, hour: float) -> String:
	if i < 0 or i >= routes.size():
		_refuse("no route %d in the manifest (%d there)" % [i, routes.size()])
		return ""
	var r: Dictionary = routes[i]
	return learn("route_time", "%s>%s" % [r["a"], r["b"]],
		"%.2f min" % float(r["minutes"]),
		"you walked %s -> %s and timed it, day %d, %05.2f "
			% [r["a"], r["b"], day, hour]
			+ "(transit.py derives %.2f min over %.1f m: %s)"
			% [float(r["minutes"]), float(r["metres"]),
				String(r.get("detail", ""))],
		"transit", "%s>%s" % [r["a"], r["b"]], day, hour)


## FAC-28's brooch and its siblings, off `npc/faction.py`'s own mark table.
func learn_tell(faction: String, place: String, day: int,
		hour: float) -> String:
	if not marks.has(faction):
		_refuse("%s has no mark in npc/faction.py" % faction)
		return ""
	return learn("tell_learned", faction, String(marks[faction]),
		"you saw the %s at %s and now read it, day %d, %05.2f"
			% [String(marks[faction]), place, day, hour],
		"costume", faction, day, hour)


# ===========================================================================
#  What is in the notebook
# ===========================================================================
func has_fact(fid: String) -> bool:
	return facts.has(fid)


func fact_count() -> int:
	return facts.size()


func witnessed() -> int:
	return _witnessed


func jumped_h() -> float:
	return _jumped_h


func lived_h() -> float:
	return _lived_h


func refusals() -> Array:
	return _refusals


## The journal page. Each line NAMES ITS SOURCE EVENT, which is PLY-07's own
## acceptance check rather than a nicety.
func entries() -> Array:
	var keys: Array = facts.keys()
	keys.sort_custom(func(a, b):
		var x: Dictionary = facts[a]
		var y: Dictionary = facts[b]
		if int(x["day"]) != int(y["day"]):
			return int(x["day"]) < int(y["day"])
		if float(x["hour"]) != float(y["hour"]):
			return float(x["hour"]) < float(y["hour"])
		return String(a) < String(b))
	var out: Array = []
	for k in keys:
		var f: Dictionary = facts[k]
		out.append("%s [%s] %s: %s -- %s (day %d, %05.2f, %s)" % [
			String(k).substr(0, 8), f["kind"], f["subject"], f["value"],
			f["source"], int(f["day"]), float(f["hour"]), f["state"]])
	return out


## The one line `main.gd` prints and the one `save.gd::audit` finds this node by.
func journal_report() -> String:
	return ("journal: %d facts, %d people met (%d by name), %d witnessed over "
		% [facts.size(), people.size(), _named_count(), _witnessed]
		+ "%.2f lived station-hours, %d jump(s) skipping %.2f h, %d refusal(s)"
		% [_lived_h, _jumps, _jumped_h, _refusals.size()])


func _named_count() -> int:
	var n := 0
	for k in people:
		if bool(people[k].get("name_given", false)):
			n += 1
	return n


# ===========================================================================
#  save.gd's contract -- BOTH halves, never one
# ===========================================================================
func save_state() -> Dictionary:
	return {"facts": facts, "people": people, "standing": standing,
			"cursor": _cursor, "witnessed": _witnessed,
			"lived_h": _lived_h}


func load_state(d: Dictionary) -> void:
	facts = d.get("facts", {})
	people = d.get("people", {})
	var st = d.get("standing", {})
	if typeof(st) == TYPE_DICTIONARY:
		for k in st:
			standing[k] = float(st[k])
	# THE CURSOR IS RESTORED WITH THE FACTS, so a reload does not re-witness
	# every call between the save hour and now. A journal that re-learned its
	# own night on every load would grow a duplicate of itself -- except that
	# `learn` supersedes by id, which is precisely why the count would look
	# right while the hours were wrong.
	_cursor = float(d.get("cursor", -999.0))
	_witnessed = int(d.get("witnessed", 0))
	_lived_h = float(d.get("lived_h", 0.0))


# ===========================================================================
#  THE ACCEPTANCE GATE
# ===========================================================================
#
# THREE PHASES IN THREE PROCESSES, AND THAT IS THE WHOLE POINT.
# `coldstart.py --g8` saves and restores inside ONE running engine, which is
# the right test for "does load_state undo a perturbation" and cannot answer
# "does it survive closing the game": an in-process restore passes on a build
# whose save file never reaches the disk. So `--phase=learn` learns and QUITS,
# and `--phase=recall` is a second `godot` invocation that boots from nothing.
#
# `station/journal.py --gate` drives all of it and owns the controls.
func run_gate(host) -> void:
	var phase := String(_args().get("phase", "learn"))
	match phase:
		"learn":
			await _phase_learn(host)
		"recall":
			await _phase_recall(host)
		"compress":
			await _phase_compress(host)
		_:
			print("JOURNAL gate=FAIL unknown --phase=%s" % phase)
			get_tree().quit(2)


func _settle(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


## Learn three facts from three DIFFERENT real in-world sources, then quit.
func _phase_learn(host) -> void:
	await _settle(30)
	var day := _day()
	var hour := (float(_clock.hour()) if _clock != null else 13.0)
	var got: Array[String] = []

	# 1. A NAME, FROM AN ACTUAL CONVERSATION. The body is one `dialogue.gd`
	#    itself bound and offered -- `refresh()` is asked and its answer is
	#    what the fact is minted from, so a fact cannot be written about
	#    somebody the dialogue system does not have.
	var who = await _scan_partner()
	if who != null:
		# THE CONVERSATION IS ACTUALLY OPENED HERE. `_scan_partner` stops at the
		# prompt so that the recall phase can NAME the fact without minting it;
		# the learn phase is the one that talks, and `dialogue.gd::talk` prints
		# the `TALK open ...` line saying who was spoken to and about what.
		_dlg().talk()
		got.append(given_name(String(who.id), String(who.name),
			String(who.place), day, hour))
		note_talk(String(who.id), String(who.topic), "you were introduced",
			1.0, "you heard them out at %s" % String(who.place))
		print("JOURNAL talked to %s (%s) at %s about %s"
			% [String(who.name), String(who.id), String(who.place),
				String(who.topic)])
	else:
		print("JOURNAL no conversation was offered -- nobody to be introduced")

	# 2. A ROUTE TIME, derived by `transit.py` and carried in the manifest.
	got.append(learn_route(0, day, hour))
	# 3. A TELL, off `npc/faction.py`'s own mark table.
	if not marks.is_empty():
		var k: String = marks.keys()[0]
		got.append(learn_tell(k, _here(), day, hour))

	var kept := 0
	for f in got:
		if f != "":
			kept += 1
	print("JOURNAL learned=%d ids=%s" % [kept, ", ".join(
		PackedStringArray(got))])
	for e in entries():
		print("JOURNAL entry | " + e)
	print("JOURNAL " + journal_report())
	var snap: Dictionary = host.save_to("journal")
	print("JOURNAL saved sections=%s"
		% str((snap.get("_state", {}) as Dictionary).keys()))
	get_tree().quit(0)


## Boot from nothing, load the slot, and check the facts came back.
##
## THE EXPECTED IDS ARE RE-DERIVED, NOT READ OUT OF THE FILE. Reading them
## from the save would make this a test that the file is self-consistent, which
## every file is. Deriving them from the same deterministic inputs -- the same
## first talkable actor, the same route 0, the same first mark -- asks the
## question that matters: is THIS fact, the one the station can name, in there.
func _phase_recall(host) -> void:
	await _settle(30)
	var before := facts.size()
	if _args().has("no-restore"):
		print("JOURNAL: RESTORE SKIPPED (control)")
	else:
		host.load_from("journal")
	var want := await _expected_ids()
	var missing: Array[String] = []
	var unsourced: Array[String] = []
	for fid in want:
		if not facts.has(fid):
			missing.append(fid.substr(0, 8))
			continue
		# PLY-07's OWN CHECK: "journal entries whose text names the source
		# event". A fid that came back with an empty source is a fact that
		# survived as a key and lost the thing that makes it a memory.
		if String(facts[fid].get("source", "")).strip_edges() == "":
			unsourced.append(fid.substr(0, 8))
	# THE CONTROL INSIDE THE SUBJECT: "a fact NOT learned is absent". A journal
	# that returned true for everything would pass every check above.
	var never := fact_id("name_given", "res:nobody:who:was:never:met",
		"dialogue", "res:nobody:who:was:never:met")
	var invented := facts.has(never)
	var ok: bool = (missing.is_empty() and unsourced.is_empty()
		and not invented and want.size() >= 2)
	for e in entries():
		print("JOURNAL entry | " + e)
	print("JOURNAL " + journal_report())
	print("JOURNAL gate=%s wanted=%d had_before_load=%d missing=%s "
		% ["PASS" if ok else "FAIL", want.size(), before,
			("none" if missing.is_empty() else ", ".join(
				PackedStringArray(missing)))]
		+ "unsourced=%s a_fact_never_learned_is_present=%s"
		% [("none" if unsourced.is_empty() else ", ".join(
			PackedStringArray(unsourced))), str(invented)])
	get_tree().quit(0 if ok else 1)


## The ids the station can NAME for this scene, derived rather than read.
##
## THE PARTNER IS RE-SCANNED, NOT GUESSED, and the first version of this guessed
## and was wrong. It expected the first row in the actors file that can talk --
## Bo Rossi, `customs_north__npc_standing_0` -- and the conversation had been
## offered to David Nakamura, `..._standing_2`, because the customs halls hold
## 83 people over a few metres and `refresh()` offers whoever is nearest and in
## the cone. `dialogue.gd::_run_test` records the identical surprise in its own
## words: *"the scan was right and the harness was measuring the crowd."*
##
## So both phases ask the SAME question of the same deterministic scene -- stand
## here, who is offered -- and this one stops before `talk()`, so deriving the
## expected id cannot create the fact it is about to look for.
func _expected_ids() -> Array[String]:
	var out: Array[String] = []
	var p = await _scan_partner()
	if p != null:
		var who := String(p.id)
		out.append(fact_id("name_given", who, "dialogue", who))
	if not routes.is_empty():
		var r: Dictionary = routes[0]
		var k := "%s>%s" % [r["a"], r["b"]]
		out.append(fact_id("route_time", k, "transit", k))
	if not marks.is_empty():
		var m: String = marks.keys()[0]
		out.append(fact_id("tell_learned", m, "costume", m))
	return out


## COMPRESS TIME THROUGH THE RUNNING SIMULATION, and show the world moved.
##
## THREE THINGS ARE MEASURED AND ONLY ONE OF THEM CAN TELL A JUMP FROM A RUN.
## The clock advancing is necessary and proves nothing -- `Clock.set_hour`
## advances it in one statement. The crowd changing is necessary and proves
## nothing either, because `life.gd`'s Director is PURE in the hour and reads
## the same after a jump. What only a run produces is the WITNESS COUNT: the
## timed calls the player was standing there for, one fact each, minted as the
## cursor passed them.
##
## `--jump` is the control that makes that visible: identical clock delta,
## identical crowd afterwards, and nothing in the notebook.
func _phase_compress(host) -> void:
	await _settle(30)
	if _clock == null:
		print("COMPRESS gate=FAIL no clock in this build")
		get_tree().quit(2)
		return
	var h0: float = float(_clock.hours_abs())
	var crowd0: int = (int(_life.visible_count()) if _life != null else -1)
	var facts0: int = facts.size()
	var jump := _args().has("jump")
	if jump:
		# THE THING PLY-05 FORBIDS, run deliberately so the difference is a
		# measurement rather than an argument. `set_hour` is `life.gd`'s own
		# jump and its docstring says "a jump is indistinguishable from having
		# waited" -- which is true of the CLOCK and false of the world.
		_clock.set_hour(fposmod(float(_clock.hour()) + SLEEP_H, 24.0))
		print("COMPRESS: JUMPED %.2f h (control) -- nothing was lived through"
			% SLEEP_H)
	var frames := 0
	while float(_clock.hours_abs()) - h0 < SLEEP_H and frames < 4000:
		await get_tree().physics_frame
		frames += 1
	var advanced: float = float(_clock.hours_abs()) - h0
	var crowd1: int = (int(_life.visible_count()) if _life != null else -1)
	var minted: int = facts.size() - facts0
	# THE THREE CLAUSES, AND EACH ONE FAILS A DIFFERENT CONTROL:
	#   advanced   fails `--compress=1`, where the same wall clock buys ~0 h
	#   _witnessed fails `--jump`, where the hours arrive without being lived
	#   minted     is the consequence in the world the player can carry away
	var ok: bool = (advanced >= SLEEP_H * 0.9
		and _witnessed >= WITNESS_FLOOR and minted >= WITNESS_FLOOR)
	print("COMPRESS gate=%s advanced=%.3f h in %d frames (wanted %.2f), "
		% ["PASS" if ok else "FAIL", advanced, frames, SLEEP_H]
		+ "lived=%.3f jumped=%.3f witnessed=%d (floor %d) facts %d->%d "
		% [_lived_h, _jumped_h, _witnessed, WITNESS_FLOOR, facts0,
			facts.size()]
		+ "crowd %d->%d rate=%.4f h/s"
		% [crowd0, crowd1, float(_clock.rate)])
	for e in entries():
		print("COMPRESS heard | " + e)
	get_tree().quit(0 if ok else 1)


# ===========================================================================
#  Finding things, and asking rather than reaching in
# ===========================================================================
func _find_by_method(host, method: String):
	# The clock is `main.gd`'s own field and is not a node; ask the host for it
	# by the accessor it already has, then fall back to a tree walk for the
	# nodes.
	if host != null and host.get("_clock") != null \
			and host.get("_clock").has_method(method):
		return host.get("_clock")
	if host != null:
		for n in host.find_children("*", "Node", true, false):
			if n.has_method(method):
				return n
	return null


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s: String = a.lstrip("-")
		if s.contains("="):
			var kv := s.split("=", true, 1)
			out[kv[0]] = kv[1]
		else:
			out[s] = true
	return out


func _day() -> int:
	return (int(_clock.day()) if _clock != null and _clock.has_method("day")
		else 0)


func _here() -> String:
	return (String(deck_rooms[0]) if not deck_rooms.is_empty() else "this deck")


## The cast row this gate holds its conversation with, chosen by a rule both
## phases can apply without having spoken to anybody: the FIRST row in the
## deck's own actors file that carries a `who.id` and can talk.
func _first_talkable() -> String:
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) != TYPE_DICTIONARY:
			continue
		if not bool(who.get("talks", false)):
			continue
		var nid := String(who.get("id", ""))
		if nid != "":
			return nid
	return ""


var _actors_cache: Array = []


func _actor_rows() -> Array:
	if not _actors_cache.is_empty():
		return _actors_cache
	var root := _repo_root()
	var boot := root.path_join("station/generated/scene/boot.json")
	if not FileAccess.file_exists(boot):
		return []
	var bf := FileAccess.open(boot, FileAccess.READ)
	var bd = JSON.parse_string(bf.get_as_text())
	bf.close()
	if typeof(bd) != TYPE_DICTIONARY:
		return []
	var p := String(bd.get("actors", ""))
	if p == "" or not FileAccess.file_exists(p):
		return []
	var f := FileAccess.open(p, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(d) == TYPE_ARRAY:
		_actors_cache = d
	return _actors_cache


## Stand in front of a body the deck really has and ask `dialogue.gd` who is
## there. Returns its OWN Person, or null. DOES NOT OPEN THE CONVERSATION.
##
## THE FACT IS MINTED FROM WHAT THE DIALOGUE SYSTEM HANDS BACK, never from the
## actors file. The file says where to stand; `refresh()` decides whether there
## is anybody there to talk to, and if it says no then no name is learned --
## which is the correct failure and not a workaround.
##
## AND IT STOPS SHORT OF `talk()` so that `_expected_ids` can use it. The recall
## phase has to be able to say WHICH fact it is looking for without minting it,
## or the test proves only that the file it just wrote agrees with itself.
## `dialogue.gd`'s node, asked for each time until one answers.
func _dlg():
	if _dialogue != null and is_instance_valid(_dialogue):
		return _dialogue
	_dialogue = _find_by_method(_host, "lines_shown")
	return _dialogue


func _scan_partner():
	var dlg = _dlg()
	if dlg == null:
		return null
	var want := _first_talkable()
	var pos := Vector3.ZERO
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) == TYPE_DICTIONARY and String(who.get("id", "")) == want:
			pos = Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
				float(a.get("z", 0.0)))
			break
	if pos == Vector3.ZERO:
		return null
	var body = (_host._player() if _host != null
		and _host.has_method("_player") else null)
	if body == null:
		return null
	# UP IS TOWARDS THE AXIS. The same derivation `dialogue.gd::_up_at` makes,
	# and getting it wrong on a spun ring puts the eye in the ceiling.
	var radial := Vector3(pos.x, pos.y, 0.0)
	var up: Vector3 = (-radial.normalized() if radial.length() > 0.001
		else Vector3.UP)
	var toward := Vector3(0, 0, 1)
	if absf(toward.dot(up)) > 0.9:
		toward = Vector3(1, 0, 0)
	toward = (toward - up * toward.dot(up)).normalized()
	body.global_position = pos + toward * 1.2
	var cam := body.get_node_or_null("Camera3D") as Camera3D
	var head: Vector3 = pos + up * 1.55
	# AIMED BY `dialogue.gd`'s OWN `_aim`, not by a copy of it here. Session 4q
	# found `npc.gd` building `Basis(fwd.cross(up), up, fwd)` -- determinant
	# exactly -1 -- and drawing the entire corridor crowd mirrored for six
	# sessions, while `player.gd` and `dialogue.gd` had the sign right. A
	# second aim in this file would be a fourth site of that idiom to get
	# wrong, and the module that owns the cone should own the aim into it.
	if cam != null:
		dlg._aim(body, cam, up, head)
	dlg.watch(body)
	await get_tree().physics_frame
	return dlg.refresh()
