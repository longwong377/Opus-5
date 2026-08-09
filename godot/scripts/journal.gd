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
##
## ===========================================================================
## SESSION 4u -- A WINDOW, A COST LEDGER, AND THE CALLER THE SAVE NEVER HAD
## ===========================================================================
##
## THREE THINGS WERE MEASURED AT THE START OF 4u AND ALL THREE ARE THE SAME
## DEFECT WEARING THREE COSTUMES.
##
## 1. `grep -c "CanvasLayer\|_draw\|draw_string\|Control"` over this file was
##    **0**. Seventeen hundred lines, eight kinds of knowledge, thirteen standing
##    ledgers, a witness that can tell a lived night from a skipped one -- and
##    **no surface**. Everything above was true and none of it was ever on a
##    screen. That is the largest built-and-invisible machine in the repository.
##
## 2. `save.gd` was complete, tested, and **had no caller that WRITES on the
##    shipped path**. `main.gd::_front_door` reads slot `auto` to decide whether
##    CONTINUE is offered; `grep -rn "save_to"` found two call sites and both are
##    gates. So CONTINUE has been disabled since it was built, and not because
##    anything was broken.
##
## 3. The one thing in this project that reacts to the player -- a customs
##    verdict computed at runtime, refused, and answered by two officers who walk
##    to you -- left **no trace the player could come back to**. The record
##    reaches `station/generated/economy.json` through `interact.gd`, which is
##    real persistence and is invisible: no window shows it and no save carries
##    the rest of the world beside it.
##
## SO THIS FILE GAINS A COST LEDGER, A PAGE AND A CHECKPOINT, and the reason all
## three land HERE rather than in three files is not convenience. The journal is
## already the node whose entire subject is *what the player knows and what
## passing time cost them*; it already watches the world every frame through
## other nodes' public accessors and mints from what it sees. A consequence is
## the same shape as a rumour: something that happened, with an hour, a place and
## a source. `_watch_costs` reads `interact.gd`, `enforcement.gd`, `arrival.gd`
## and the body through methods and fields those files already expose -- nothing
## is reached into, nothing there is edited, and no rule is copied.
##
## WHAT THIS FILE DELIBERATELY DOES NOT DECIDE. Not what a verdict is
## (`arrival.gd::customs_verdict`), not what a conviction costs
## (`consequence.py` through `enforcement.gd`), not which ledger a person sits on
## (the manifest). It records, keeps, saves and DRAWS. A journal that computed a
## consequence would be a second copy of a rule, which is the defect this
## repository has paid for three times.
##
## THE CHECKPOINT IS A CALLER, AND ITS HOME IS ADMITTEDLY WRONG. Autosave
## belongs in `main.gd`, which owns the world and already owns `save_to`. It is
## driven from here because 4u's brief gave this agent three files and `main.gd`
## is not one of them, and because a checkpoint with a bad home beats a save
## system with no caller by exactly the margin this project keeps measuring.
## `_checkpoint()` calls `host.save_to(save.gd::AUTO_SLOT)` -- the same method
## the save gate uses and the same slot the front door reads. See
## `docs/MASTER-PLAN.md` for the one-line move.

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

## How near a body must be to one of the deck's cast before it is standing in
## that person's PLACE rather than in the corridor between two of them.
##
## DERIVED OFF THE BOOT DECK'S OWN ACTOR ROWS, not chosen. Its three named
## rooms hold 27-28 bodies each, spread 33 m along the axis and 4-10 m across
## the arc, so a body anywhere inside a room is within a few metres of
## somebody; the nearest body of the NEXT room is 44 m of arc away and the one
## after that 620 m. Any value between roughly 10 m and 40 m reads the same,
## which is what makes this a threshold rather than a tuning knob. INV-1160.
const PLACE_R_M := 12.0

## How much further than one frame of walking a body may move and still count
## as WALKING rather than having been PLACED, in metres.
##
## `player.gd::sprint_m_s` is 8.0 m/s and a physics frame is 1/60 s, so the
## fastest honest frame is 0.133 m. Four of those is the same stutter
## allowance `JUMP_TOL` gives the clock, applied to space -- and the teleport
## the control below performs is 44 m, which is 330x it. INV-1161.
const STEP_TOL_M := 0.55

## What fraction of `transit.py`'s own derived arc for a pair of places the
## player's feet must have actually covered before a route time may be written
## down. `PLACE_R_M` is eaten off each end of a leg, so a fully walked 44.3 m
## leg registers about 20 m of travel between the two place readings; a third
## is the honest floor and a teleport registers zero. INV-1162.
const LEG_FRACTION := 0.35

# --- what the station decided ---------------------------------------------
var kinds: Array = []
var mutable_kinds: Array = []
var stale_after_days: int = 7
var standing_blocks: Dictionary = {}
var routes: Array = []
var marks: Dictionary = {}
var calls: Array = []                  # broadcast.py's timed day
var deck_rooms: Array = []             # which of them are audible here
## "species/role" -> which CAST-05 ledger that person sits on. The station's
## decision, read rather than restated -- `station/journal.py::standing_for`.
var standing_for: Dictionary = {}
## dialogue.py's stance names -> what taking that line is worth on the ledger.
var stance_favour: Dictionary = {}

# --- what the player knows -------------------------------------------------
var facts: Dictionary = {}             # fid -> fact dictionary
var people: Dictionary = {}            # npc_id -> CAST-05 memory slot
var standing: Dictionary = {}          # ledger -> scalar

## --- WHAT IT COST YOU ------------------------------------------------------
##
## The consequence ledger: an ordered list of things that were DONE TO the
## player, each with the hour and place it happened and the sentence whichever
## system decided it produced. Ordered rather than keyed, because unlike a fact
## a consequence does not supersede -- two refusals at the same reader are two
## refusals, and collapsing them by id would make the second one free.
##
## EVERY ROW IS A QUOTE, NOT A JUDGEMENT. `what` is the other file's own words:
## `arrival.gd`'s verdict line, `enforcement.gd::booking`, the offence string
## `interact.gd::convict` was handed. This file adds the hour, the place and the
## order.
var costs: Array = []
## The baselines the watcher compares against. Re-taken on `load_state` for the
## reason `_resync` exists: a restored counter moving is not the world moving.
var _seen_reads := -1
var _seen_convictions := -1
var _seen_booking := ""
var _seen_tier := -99
var _cost_resync := true

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
## What the clock ran at before compression, so a rate can be put back.
var _boot_rate: float = -1.0

# --- THE SHIPPED OBSERVER --------------------------------------------------
#
# ROUND ONE'S DEFECT, NAMED BY ITS OWN REVIEWER AND CORRECT: `given_name`,
# `note_talk` and the route minter *"have no caller anywhere except
# `journal.gd::_phase_learn` -- the gate itself"*. That is this repository's
# ninth-instance defect arriving at the level of a MINTER rather than a
# loader: a player who walked up to somebody and talked recorded nothing,
# because the only thing that ever called the minter was the test, and the
# test called it directly so it could never notice.
#
# THE CURE IS NOT TO CALL THE MINTERS FROM `dialogue.gd`. It is to make the
# journal WATCH -- in `_process`, which every build runs, because
# `main.gd::_start_journal` is unconditional in `_ready`. That keeps the two
# files' ownership disjoint (`dialogue.gd` decides what a conversation IS,
# this file decides what is worth writing down) and it means the caller is
# the same one on every path into a conversation: the T key, `interact.gd`,
# or a harness. `dialogue.gd` is not edited at all.
#
# So a player presses T, `dialogue.gd::_unhandled_input` calls `talk()`,
# `_opened` goes up, and one frame later the journal has a name in it. The
# gate below PRESSES THE KEY through the viewport rather than calling
# `talk()`, so what it exercises is the path a player is on.
var _seen_opened: int = 0              # dialogue.gd::opened() last seen
var _seen_said: int = 0                # dialogue.gd::said() last seen
var _talking := ""                     # npc id of the open conversation
var _talk_place := ""
# --- the odometer: what the player's own feet did --------------------------
var _last_pos := Vector3.ZERO
var _have_pos := false
var _here_place := ""                  # place the body is standing in NOW
var _leg_from := ""                    # place it was last standing in
var _leg_m: float = 0.0                # metres walked since leaving it
var _leg_h0: float = -1.0              # station hour it left
var _leg_broken := 0                   # frames the body was PLACED, not walked
var _legs := 0                         # route facts the feet earned
var _placed := 0                       # discontinuities seen, all time
## Set by `load_state`: the next `_watch` re-reads the world's counters
## instead of reading their movement as something the player did.
var _resync := false


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
	_install_persistence()
	_install_page()
	return kinds.size() if not kinds.is_empty() else -1


# ===========================================================================
#  THE CHECKPOINT -- the caller `save.gd` never had
# ===========================================================================
const Save = preload("res://scripts/save.gd")

## Off by `--no-persist`, which is the negative control for the whole of 4u:
## everything else identical and the slot never written, so the second launch
## has nothing to come back to. It must FAIL.
var _persist := true
## Whether the shipped path has written this slot at least once this session.
var _checkpoints := 0
var _last_checkpoint := ""
## Real seconds between two automatic writes of the same slot. A checkpoint is a
## whole-world capture and a run that took one every frame would be measuring its
## own file writes; nothing in this build produces two consequences that close
## together except a gate.
const CHECKPOINT_GAP_S := 2.0
var _last_checkpoint_ms := -1


func _install_persistence() -> void:
	_persist = not _args().has("no-persist")
	if not _persist:
		print("journal: PERSISTENCE DISABLED (control) -- nothing that happens "
			+ "to you will be written to %s" % Save.slot_path(Save.AUTO_SLOT))
	if _args().has("forget"):
		# The control's other half. See `save.gd::erase`.
		var gone := Save.erase(Save.AUTO_SLOT)
		print("journal: FORGET (control) -- slot %s %s"
			% [Save.AUTO_SLOT, ("deleted" if gone else "was not there")])
	if _args().has("continue"):
		# DEFERRED, because `install()` runs inside `main.gd::_start` and the
		# streamer, the crowd and the interactables are still being built on the
		# frame it is called. Restoring into a half-built tree would put the
		# ledger back into a node that has not read it yet -- the same "bind
		# describes the tree at the instant it was called" trap `_dlg()` avoids.
		call_deferred("_continue_from_slot")


## THE READER SIDE, AND IT IS THE SAME CALL THE BUTTON MAKES.
##
## `main.gd::_on_menu_chosen` runs `load_from(MENU_SLOT)` when a player presses
## CONTINUE. This is that line with a flag in front of it, for a headless run
## that has no keyboard -- NOT a second restore path. If the two ever diverge the
## gate below says so, because it asserts `MENU_SLOT` and `save.gd::AUTO_SLOT`
## are the same string.
func _continue_from_slot() -> void:
	if _host == null or not _host.has_method("load_from"):
		print("journal: --continue asked for, and this host has no load_from")
		return
	var snap: Dictionary = Save.read(Save.AUTO_SLOT)
	if snap.is_empty():
		print("journal: --continue -- NOTHING IN SLOT %s. The world starts over."
			% Save.AUTO_SLOT)
		return
	print("journal: CONTINUING from %s -- %s"
		% [Save.slot_path(Save.AUTO_SLOT), Save.describe(snap)])
	_host.load_from(Save.AUTO_SLOT)


## Write the whole world to the auto slot because something happened to the
## player. Rate-limited, refused when the control is on, and LOUD either way.
func _checkpoint(why: String) -> bool:
	if not _persist:
		print("journal: checkpoint SKIPPED (control) -- %s would have been "
			% why + "written to %s" % Save.slot_path(Save.AUTO_SLOT))
		return false
	if _host == null or not _host.has_method("save_to"):
		print("journal: checkpoint SKIPPED -- this host has no save_to (%s)" % why)
		return false
	var now := Time.get_ticks_msec()
	if _last_checkpoint_ms >= 0 \
			and now - _last_checkpoint_ms < int(CHECKPOINT_GAP_S * 1000.0):
		return false
	_last_checkpoint_ms = now
	var snap: Dictionary = _host.save_to(Save.AUTO_SLOT)
	_checkpoints += 1
	_last_checkpoint = why
	print("journal: CHECKPOINT %d -- %s -- %s -> %s"
		% [_checkpoints, why, Save.headline(snap),
			Save.slot_path(Save.AUTO_SLOT)])
	return true


func checkpoints() -> int:
	return _checkpoints


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
	standing_for = d.get("standing_for", {})
	stance_favour = d.get("stance_favour", {})
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
	_boot_rate = float(_clock.rate)
	_clock.rate = _boot_rate * mult
	print("journal: TIME COMPRESSION x%.0f -- the clock now runs at %.4f "
		% [mult, float(_clock.rate)]
		+ "station hours a second, THROUGH the simulation")


# ===========================================================================
#  The witness -- what makes a compressed hour different from a skipped one
# ===========================================================================
func _process(delta: float) -> void:
	# THE OBSERVER RUNS FIRST AND RUNS WITHOUT A CLOCK. A build with no
	# Director still has a player who can walk up to somebody and talk, and a
	# journal that recorded nothing in that build would be exactly the "no
	# caller on the shipped path" defect with a different excuse.
	_watch(delta)
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
#  THE SHIPPED OBSERVER -- see the header block beside `_seen_opened`
# ===========================================================================
func _watch(delta: float) -> void:
	_watch_talk()
	_watch_feet(delta)
	_watch_costs()


# ===========================================================================
#  WHAT IT COST YOU -- the observer for consequences
# ===========================================================================
## Four counters other files already keep, watched the way `_watch_talk` watches
## `dialogue.gd::opened()`.
##
## NOT ONE OF THESE IS A RULE THIS FILE OWNS, and that is deliberate to the point
## of pedantry. `interact.gd` decides when a card has been read and when a
## conviction is written; `enforcement.gd` decides what a booking says; the body
## carries the rung `player.gd::rung_of` derived. This function's entire content
## is *notice, timestamp, place, keep*.
##
## AND IT RUNS IN EVERY BUILD, not only in a gate -- that is the whole lesson of
## the block above `_seen_opened`. A player refused at customs at 13:04 has a row
## in their notebook at 13:04 whether or not anybody is testing.
func _watch_costs() -> void:
	# ONE DECISION PER FRAME, SHARED. `_interact()` and `_enforcement()` both
	# consult it, so a frame that searches searches once for each and a frame
	# that does not costs two null checks. See `_look_now`.
	_looking = _look_now()
	var it = _interact()
	var body = _body()
	# A RESTORE IS NOT A CONSEQUENCE. Identical in shape to `_watch_talk`'s
	# `_resync`, and needed for the identical reason: `save.gd::restore` puts
	# `interact.gd`'s `customs_reads` and the record's conviction count back to
	# what they were, and to an observer watching a counter, a counter arriving is
	# a counter going up. Without this a reload would mint a duplicate of every
	# consequence in the file it just loaded.
	if _cost_resync:
		_cost_resync = false
		_seen_reads = (int(it.get("customs_reads")) if it != null else -1)
		_seen_convictions = (int(it.convictions()) if it != null
			and it.has_method("convictions") else -1)
		_seen_booking = _booking_now()
		_seen_tier = (int(body.tier) if body != null else -99)
		return

	# 1. THE CARD IN THE READER.
	if it != null:
		var reads := int(it.get("customs_reads"))
		if _seen_reads >= 0 and reads > _seen_reads:
			_seen_reads = reads
			_note_customs(it)
		elif _seen_reads < 0:
			_seen_reads = reads

	# 2. A CONVICTION ON THE CARD.
	if it != null and it.has_method("convictions"):
		var n := int(it.convictions())
		if _seen_convictions >= 0 and n > _seen_convictions:
			var was := _seen_convictions
			_seen_convictions = n
			_note_cost("conviction", _where_now(),
				"%d conviction(s) on the card" % n,
				"was %d before this" % was)
		elif _seen_convictions < 0:
			_seen_convictions = n

	# 3. WHAT THE OFFICERS BOOKED YOU FOR. `enforcement.gd::booking` is its own
	#    one-line readable record and it names the fine, the hold and the rung.
	var bk := _booking_now()
	if bk != "" and bk != _seen_booking:
		_seen_booking = bk
		_note_cost("booking", _where_now(), bk, _enforce_detail())

	# 4. THE RUNG ITSELF. Watched separately from the conviction because a
	#    revocation and a conviction are not the same event -- `convict()` writes
	#    one with `revoked=false` most of the time -- and because the rung is the
	#    number every checkpoint in the build actually compares against.
	if body != null:
		var t := int(body.tier)
		if _seen_tier > -99 and t < _seen_tier:
			_note_cost("demotion", _where_now(),
				"%s WITHDRAWN -- you now hold %s"
					% [_tier_name_of(_seen_tier).to_upper(),
						String(body.tier_name).to_upper()],
				"rung %d -> %d" % [_seen_tier, t])
		if t != _seen_tier:
			_seen_tier = t


## The customs row, with the verdict's own words when the card holder is here to
## supply them. `interact.gd::customs_status()` is the status; the STATION it
## failed at and the sentence are `arrival.gd::customs()`'s, read rather than
## restated, so the notebook cannot disagree with the plate on the reader.
func _note_customs(it) -> void:
	var status := String(it.customs_status()) if it.has_method("customs_status") \
		else ""
	var v: Dictionary = {}
	var card = _card_holder()
	if card != null and card.has_method("customs"):
		var c = card.call("customs")
		if typeof(c) == TYPE_DICTIONARY:
			v = c
	var place := String(v.get("place", ""))
	if place == "":
		place = _where_now()
	var what := ""
	if status == "":
		what = "a card was read and nothing decided anything"
	elif v.is_empty():
		what = "IDENTICARD %s" % status.to_upper()
	else:
		what = "IDENTICARD %s -- %s" % [status.to_upper(),
			String(v.get("verdict", ""))]
	var detail := ""
	if not v.is_empty():
		detail = "station %d, %s: %s" % [int(v.get("at_station", 0)),
			String(v.get("station", "")), String(v.get("why", ""))]
	_note_cost("customs", place, what, detail)
	# THE POINT OF THE WHOLE SESSION, IN ONE CALL. A verdict that is not written
	# to a slot is a verdict that dies with the process.
	_checkpoint("a customs verdict")


## Add a row, print it, and say so. Returns the row.
func _note_cost(kind: String, place: String, what: String,
		detail: String = "") -> Dictionary:
	# `--no-journal` STOPS THIS TOO, and it has to. The flag's contract is
	# "nothing will be learned", and a consequence is learned; a control that
	# silenced the rumours and kept the convictions would be a control that only
	# half removes its subject. It is also what keeps `--phase=continue` honest,
	# because that phase turns minting off so every row it reports came from a
	# file rather than from the frame it was reading in.
	if not _minting:
		return {}
	var row := {
		"kind": kind, "place": place, "what": what, "detail": detail,
		"day": _day(), "hour": (float(_clock.hour()) if _clock != null else -1.0),
		"credits": _credits_now(),
	}
	costs.append(row)
	print("journal: COST %s at %s, day %d %05.2f -- %s%s"
		% [kind, (place if place != "" else "-"), int(row["day"]),
			float(row["hour"]), what,
			(" (%s)" % detail if detail != "" else "")])
	return row


## The one sentence a save file carries about you. `save.gd::_headlines` asks
## every subject for one and this is the only node in the tree that has an
## answer, which is the correct shape: the notebook is where "what happened to
## me" lives.
##
## THE WORST ROW, NOT THE LAST. A player refused at customs and then fined has
## two rows and the refusal is the one that decides what their next day is like;
## reporting the most RECENT would let a trivial event bury a revocation.
func save_headline() -> String:
	if costs.is_empty():
		return ""
	var rank := {"demotion": 4, "booking": 3, "customs": 2, "conviction": 1}
	var best: Dictionary = {}
	var best_r := -1
	for row in costs:
		var r := int(rank.get(String(row.get("kind", "")), 0))
		if r >= best_r:
			best_r = r
			best = row
	var out := "%s (day %d, %05.2f" % [String(best.get("what", "")),
		int(best.get("day", 0)), float(best.get("hour", 0.0))]
	if String(best.get("place", "")) != "":
		out += " at %s" % String(best.get("place", ""))
	out += ")"
	if costs.size() > 1:
		out += " and %d more on the record" % (costs.size() - 1)
	return out


## What the notebook can say about the player's standing right now, in the terms
## a HUD can draw. Values only -- no formatting decisions, because `hud.gd` owns
## how its own face reads.
func consequence_state() -> Dictionary:
	var body = _body()
	var it = _interact()
	var last := {}
	for row in costs:
		if String(row.get("kind", "")) in ["customs", "booking", "demotion"]:
			last = row
	return {
		"rows": costs.size(),
		"customs": (String(it.customs_status()) if it != null
			and it.has_method("customs_status") else ""),
		"convictions": (int(it.convictions()) if it != null
			and it.has_method("convictions") else 0),
		"tier": (int(body.tier) if body != null else -1),
		"tier_name": (String(body.tier_name) if body != null else ""),
		"person": (String(body.person) if body != null else ""),
		"npc_id": (String(body.npc_id) if body != null else ""),
		"last": String(last.get("what", "")),
		"last_place": String(last.get("place", "")),
		"facts": facts.size(),
		"people": people.size(),
	}


func cost_count() -> int:
	return costs.size()


## The consequence ledger as lines, newest last. Used by the page and by the
## gate, so what a test asserts and what a player reads are one string.
func cost_lines() -> Array:
	var out: Array = []
	for row in costs:
		out.append("day %d %05.2f  %-10s %s%s" % [
			int(row.get("day", 0)), float(row.get("hour", 0.0)),
			String(row.get("kind", "")).to_upper(),
			String(row.get("what", "")),
			(" [%s]" % String(row.get("place", ""))
				if String(row.get("place", "")) != "" else "")])
	return out


# -- the nodes the watcher reads, all found by capability --------------------
#
# CACHED ON A HIT, AND BOUNDED ON A MISS. `_dlg()` above caches only a hit,
# because in a streamed build the node it wants arrives with a cell rather than
# with the scene -- and that is right. What it does not have to worry about, and
# these three do, is a build where the node NEVER arrives: `--mode=station` has
# no `arrival.gd` and never will, and `_watch_costs` runs every frame in every
# build. An unbounded `find_children("*", "Node", true, false)` per frame over a
# 907-cell streamed world is a cost with no upside and no error -- which is the
# shape of defect this project has twice mistaken for a content regression.
#
# So: retried every `_LOOK_EVERY` frames for `_LOOK_FRAMES`, then never again.
# Ten seconds at 60 fps is longer than any cell has taken to arrive here, and
# after it the answer for that build is settled.
const _LOOK_EVERY := 30
const _LOOK_FRAMES := 600
var _interact_n = null
var _card_n = null
var _enforce_n = null
var _look_frame := 0
var _looking := true


func _look_now() -> bool:
	_look_frame += 1
	return _look_frame <= _LOOK_FRAMES and _look_frame % _LOOK_EVERY == 0


## `customs_status` is `interact.gd`'s and nothing else in the tree answers it.
func _interact():
	if _interact_n != null and is_instance_valid(_interact_n):
		return _interact_n
	if _looking:
		_interact_n = _find_by_method(_host, "customs_status")
	return _interact_n


## `customs_verdict` is `arrival.gd`'s. A `--mode=station` build has none, and
## that is not a fault: nobody issued a card in that build, so there is no
## verdict for anybody to quote.
func _card_holder():
	if _card_n != null and is_instance_valid(_card_n):
		return _card_n
	# ALWAYS LOOKED FOR WHEN ASKED, because this one is only asked on the frame a
	# card goes through a reader -- which is rare, and which is exactly the frame
	# the answer must not be "I stopped looking".
	_card_n = _find_by_method(_host, "customs_verdict")
	return _card_n


## `refuse_at` is `enforcement.gd`'s.
func _enforcement():
	if _enforce_n != null and is_instance_valid(_enforce_n):
		return _enforce_n
	if _looking:
		_enforce_n = _find_by_method(_host, "refuse_at")
	return _enforce_n


func _booking_now() -> String:
	var e = _enforcement()
	if e == null:
		return ""
	return String(e.get("booking"))


func _enforce_detail() -> String:
	var e = _enforcement()
	if e == null:
		return ""
	return "refused=%d arrived=%d moved_on=%d detained=%d searched=%d" % [
		int(e.get("refused")), int(e.get("arrived")), int(e.get("moved_on")),
		int(e.get("detained")), int(e.get("searched"))]


func _body():
	if _host != null and _host.has_method("_player"):
		var b = _host._player()
		if b != null and is_instance_valid(b):
			return b
	return null


func _credits_now() -> float:
	var b = _body()
	return (float(b.credits) if b != null else -1.0)


## The rung's own name, for a demotion row that has to say what was taken away.
## `arrival.gd::TIER_NAME` is the bake's table and this is the same six labels;
## it is used only to NAME a number the body already moved past, never to decide
## one, so it cannot become a second copy of the ladder.
func _tier_name_of(t: int) -> String:
	return {0: "no_status", 1: "sanctuary", 2: "transit", 3: "resident",
		4: "citizen", 5: "accredited"}.get(t, "rung %d" % t)


## WHERE THE BODY IS STANDING, not which deck booted. `_here()` above answers the
## second question and is right for a PA call, which is heard across a deck; a
## consequence happens to you in a room, and `_watch_feet` has already resolved
## which one every frame off the same place boxes the HUD uses.
func _where_now() -> String:
	if _here_place != "":
		return _here_place
	return ""


## A CONVERSATION THE PLAYER ACTUALLY OPENED, minted one frame after it opened.
##
## `dialogue.gd::opened()` is a counter it already keeps and already exposes;
## nothing is reached into and nothing there is edited. While a conversation is
## open `refresh()` is frozen to the person you are talking to -- that file's
## own rule, *"turning your head mid-sentence must not hand the conversation to
## the person behind you"* -- so this reads the partner rather than a scan.
func _watch_talk() -> void:
	var dlg = _dlg()
	if dlg == null:
		return
	# A RESTORE IS NOT A CONVERSATION, and this cost a whole gate run to find.
	# `save.gd` restores the `dialogue` section too, which puts `_opened` back
	# to what it was when the game was saved -- and to an observer watching a
	# counter, a counter going up is a counter going up. The recall phase
	# therefore minted a name for whoever was standing nearest at the moment
	# of the load (David Nakamura, not the Bo Rossi the walk had talked to),
	# and the acceptance then found "the name" present for the worst possible
	# reason: it had just been written, in the process that was supposed to be
	# only reading. Re-baselining on load is the fix, and `_resync` is set by
	# `load_state` rather than by the gate, so it protects a player's own load
	# and not just the test.
	if _resync:
		_resync = false
		_seen_opened = int(dlg.opened())
		_seen_said = int(dlg.said())
		return
	var n := int(dlg.opened())
	if n > _seen_opened:
		_seen_opened = n
		var p = dlg.refresh()
		if p != null:
			_note_opened(p)
	_watch_stance(dlg)


func _note_opened(p) -> void:
	var day := _day()
	var hour := (float(_clock.hour()) if _clock != null else 13.0)
	var who := String(p.id)
	_talking = who
	_talk_place = String(p.place)
	var fid := given_name(who, String(p.name), String(p.place), day, hour)
	# The introduction itself moves nothing. What a stance is worth is decided
	# below, when the player has actually said one -- a favour granted for
	# walking up would make the three stances decorative, which is the same
	# argument `dialogue.gd::talk` makes about its own menu.
	note_talk(who, String(p.topic), "you were introduced", 0.0, "")
	print("journal: %s gave you their name at %s (topic %s) -- %s"
		% [String(p.name), String(p.place), String(p.topic),
			("fact " + fid.substr(0, 8)) if fid != "" else "REFUSED"])


## WHAT THE PLAYER SAID, AND WHAT IT COST. `dialogue.gd::said()` counts player
## utterances and `picked()` names the stance; both are its own accessors.
##
## THE LEDGER IS NOT NAMED HERE. Which of CAST-05's thirteen blocks a Centauri
## dock inspector belongs on is `station/journal.py::standing_for`'s decision
## and arrives in the manifest, for the reason this file's header gives: a
## second copy of a decision is the defect this repository has paid for three
## times.
func _watch_stance(dlg) -> void:
	var n := int(dlg.said())
	if n <= _seen_said:
		return
	_seen_said = n
	if _talking == "":
		return
	var stance := String(dlg.picked())
	var w: float = float(stance_favour.get(stance, 0.0))
	if w == 0.0 and not stance_favour.has(stance):
		_refuse("%s is not one of dialogue.py's stances" % stance)
		return
	var block := _block_for(_talking)
	note_talk(_talking, _talk_place, "you were %s with them" % stance, w,
		"you took the %s line at %s" % [stance, _talk_place])
	var after := 0.0
	if block != "":
		after = move_standing(block, w, "you took the %s line with %s at %s"
			% [stance, _talking, _talk_place])
	print("journal: stance=%s favour%+.2f standing %s=%+.3f"
		% [stance, w, (block if block != "" else "-"), after])


## Which ledger the person you are talking to sits on. The rule is the
## manifest's; this is the JOIN, on the actor row's own `who` record.
func _block_for(npc_id: String) -> String:
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) != TYPE_DICTIONARY or String(who.get("id", "")) != npc_id:
			continue
		var sp := String(who.get("species", ""))
		var role := String(who.get("role", ""))
		if standing_for.has(sp + "/" + role):
			return String(standing_for[sp + "/" + role])
		if standing_for.has(sp + "/*"):
			return String(standing_for[sp + "/*"])
		if standing_for.has("*/" + role):
			return String(standing_for["*/" + role])
		return String(standing_for.get("*/*", ""))
	return ""


## THE ODOMETER. Metres the body covered UNDER ITS OWN POWER, and the place it
## is standing in, both read off the world every frame.
##
## THIS IS WHAT MAKES A ROUTE TIME A THING THE PLAYER LEARNED. Round one minted
## `routes[0]` out of the manifest the moment the gate asked, and its reviewer
## was right that the world was never consulted. A leg is now a fact about the
## player's feet: it may only be written down when the body has left one of the
## deck's places, covered at least `LEG_FRACTION` of the arc `transit.py`
## derives for that pair, and arrived in the other -- WITHOUT being placed.
## `--teleport` is the control and it is 44 m in one frame.
func _watch_feet(delta: float) -> void:
	var body = (_host._player() if _host != null
		and _host.has_method("_player") else null)
	if body == null or not is_instance_valid(body):
		return
	var pos: Vector3 = body.global_position
	if not _have_pos:
		_have_pos = true
		_last_pos = pos
		_here_place = _place_at(pos)
		_leg_from = _here_place
		_leg_h0 = (float(_clock.hours_abs()) if _clock != null else -1.0)
		return
	var step := pos.distance_to(_last_pos)
	_last_pos = pos
	# A STEP NO LEG COULD HAVE TAKEN IS A PLACEMENT, and you cannot claim to
	# have walked what you were carried over. The leg is not merely paused --
	# it is POISONED, so that a teleport followed by a short honest stroll
	# cannot buy the fact the teleport skipped.
	if step > maxf(STEP_TOL_M, 8.0 * maxf(delta, 0.0)):
		_leg_broken += 1
		_placed += 1
		_leg_m = 0.0
	else:
		_leg_m += step
	var was := _here_place
	_here_place = _place_at(pos)
	if _here_place == was:
		return
	# ARRIVING somewhere named closes the leg out of the place last stood in;
	# LEAVING one starts a new one. A body that wanders out of a room and back
	# in earns nothing, because `_leg_from` is the room it left.
	if _here_place != "" and _leg_from != "" and _leg_from != _here_place:
		_close_leg(_leg_from, _here_place)
	if was != "":
		_leg_from = was
	_leg_m = 0.0
	_leg_broken = 0
	_leg_h0 = (float(_clock.hours_abs()) if _clock != null else -1.0)


## Which of the deck's places a point is standing in, or "" for the corridor
## between them. Nearest body of the deck's own cast, inside `PLACE_R_M`.
func _place_at(pos: Vector3) -> String:
	var best := ""
	var best_d := PLACE_R_M * PLACE_R_M
	for a in _actor_rows():
		var d := pos.distance_squared_to(Vector3(
			float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0))))
		if d < best_d:
			best_d = d
			best = String(a.get("place", ""))
	return best


func _close_leg(a: String, b: String) -> void:
	if a == b or a == "" or b == "":
		return
	var h1: float = (float(_clock.hours_abs()) if _clock != null else -1.0)
	var mins: float = (maxf(h1 - _leg_h0, 0.0) * 60.0 if _leg_h0 >= 0.0
		else -1.0)
	var fid := walked_leg(a, b, _leg_m, mins, _day(),
		(float(_clock.hour()) if _clock != null else 13.0))
	if fid != "":
		_legs += 1
	print("journal: feet %s -> %s, %.1f m walked, %d placement(s) -- %s"
		% [a, b, _leg_m, _leg_broken,
			("fact " + fid.substr(0, 8)) if fid != "" else "no route fact"])


## How many route facts the feet earned, and how many placements were seen.
func legs_walked() -> int:
	return _legs


func placements() -> int:
	return _placed


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


## THE SAME ROUTE TIME, EARNED. `learn_route` above takes the station's word
## for a leg; this one takes the player's feet as the evidence that they are
## entitled to it, and REFUSES otherwise.
##
## THREE REFUSALS, AND EACH ONE ANSWERS A DIFFERENT WAY OF NOT HAVING WALKED:
##   * a pair `transit.py` never derived -- you cannot time a leg the station
##     has no arc for, and the subject would be a fact about nothing;
##   * a leg the body was PLACED across -- `_watch_feet` poisons `_leg_m` on
##     any step no leg could take, so a teleport arrives with 0.0 m;
##   * a leg the body only dipped into -- fewer than `LEG_FRACTION` of the
##     derived arc under its own feet.
##
## THE VALUE IS STILL `transit.py`'s NUMBER and that is deliberate. What the
## player learns is the station's real leg time, which is the thing a porter
## knows; what the walk buys is the RIGHT to know it. The source line carries
## both, so a reader can see the measurement beside the derivation.
func walked_leg(a: String, b: String, metres: float, minutes: float,
		day: int, hour: float) -> String:
	var r: Dictionary = {}
	for row in routes:
		if String(row.get("a", "")) == a and String(row.get("b", "")) == b:
			r = row
			break
		if String(row.get("a", "")) == b and String(row.get("b", "")) == a:
			r = row
			break
	if r.is_empty():
		_refuse("transit.py derives no arc for %s -> %s -- nothing to time"
			% [a, b])
		return ""
	var want: float = float(r["metres"]) * LEG_FRACTION
	if metres < want:
		_refuse("%s -> %s: %.1f m under your own feet, and %.1f m of "
			% [a, b, metres, float(r["metres"])]
			+ "transit.py's arc needs at least %.1f -- not walked" % want)
		return ""
	return learn("route_time", "%s>%s" % [a, b],
		"%.2f min" % float(r["minutes"]),
		"you walked %s -> %s yourself -- %.1f m of its %.1f m under your feet "
			% [a, b, metres, float(r["metres"])]
			+ "in %.2f station-minutes, day %d, %05.2f "
			% [minutes, day, hour]
			+ "(transit.py derives %.2f min: %s)"
			% [float(r["minutes"]), String(r.get("detail", ""))],
		"transit", "%s>%s" % [a, b], day, hour)


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


# ===========================================================================
#  THE PAGE -- the surface this file did not have
# ===========================================================================
#
# MEASURED BEFORE IT EXISTED: `grep -c "CanvasLayer\|_draw\|draw_string\|Control"`
# over this file was 0, across 1,731 lines. Everything the journal knows was
# reachable only from a log. A player could not see a single fact they had
# learned, a single person they had met, a single ledger they stood on, or one
# thing that had been done to them.
#
# WHY IT IS DRAWN AND NOT ASSEMBLED FROM CONTROLS -- the same argument
# `hud.gd::Face` makes and it is not repeated for style: the whole interface is
# hairlines and small tracked capitals, a StyleBox cannot express those without a
# texture, and a texture is a binary this project has a standing rule against.
# Drawing it also keeps the entire look in one reviewable function.
#
# THE PALETTE IS `hud.gd`'s, TO THE THREE DECIMALS, and it is duplicated rather
# than imported for a reason worth stating: `hud.gd` is a CanvasLayer script and
# preloading it here would instantiate a second HUD's worth of constants into a
# node that is not one. Three colours copied is a smaller liability than a class
# dependency between two overlays -- and if they ever disagree, the page and the
# face are on screen at the same time, so the disagreement is visible rather than
# theoretical.
const P_CYAN := Color(0.494, 0.812, 0.882)
const P_AMBER := Color(1.0, 0.702, 0.290)
const P_INK := Color(0.016, 0.031, 0.047)

## The key. `dialogue.gd` owns T and the digits, `interact.gd` owns E,
## `player.gd` owns ESC. J is free, checked against all three.
const PAGE_KEY := KEY_J

var _page: CanvasLayer = null
var _page_face = null
var _page_open := false
var _page_scroll := 0
## HOW MANY DRAW CALLS THE LAST FRAME OF THE PAGE ACTUALLY ISSUED. A headless
## build has no raster to read, so "the page drew" cannot be proved from a
## picture -- and "the node exists" is not the claim. This is incremented inside
## `_draw` by every primitive, so a gate can fail on a page that is present,
## visible, and drawing nothing.
var _page_ops := 0


func _install_page() -> void:
	# THE SAME EXCLUSIONS `hud.gd` TAKES, and for its reason: `walkable.py` parses
	# one line out of a headless walk and a Control tree over a null driver can
	# only subtract from it. `--no-journal-page` is this file's own control.
	var a := _args()
	if a.has("walk-test") or a.has("no-hud") or a.has("no-journal-page"):
		print("journal: NO PAGE in this build (%s)"
			% ("--walk-test" if a.has("walk-test")
				else "--no-hud" if a.has("no-hud") else "--no-journal-page"))
		return
	_page = CanvasLayer.new()
	_page.name = "JournalPage"
	# ABOVE THE HUD AND ABOVE THE CONVERSATION. Both of those are CanvasLayers at
	# the default layer 0; a full-page log drawn underneath them would have the
	# reticle and the prompt printed through it.
	_page.layer = 20
	_page_face = Page.new()
	_page_face.j = self
	_page_face.name = "Face"
	_page_face.set_anchors_preset(Control.PRESET_FULL_RECT)
	_page_face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_page.add_child(_page_face)
	add_child(_page)
	_page.visible = false
	if a.has("journal-open"):
		open_page()
	if a.has("journal-shot"):
		call_deferred("_page_shot", String(a["journal-shot"]))
	print("journal: page ready -- press J (%d ledger(s), %d kind(s) to show)"
		% [standing_blocks.size(), kinds.size()])


## A PICTURE OF THE PAGE, because `_page_ops` proves the draw ran and says
## nothing about whether anybody would want to read it. `docs/AAA-STANDARD.md`
## scores craft off a frame and this is how a full-screen overlay gets one.
##
## IT NAMES THE DRIVER IT ACTUALLY GOT, on every run, per CLAUDE.md's
## render-fallback rule: a container with no Vulkan ICD silently substitutes
## OpenGL 3 Compatibility, exits 0 with a PNG, and ten frames were judged through
## it in session 4e. A page of flat 2D drawing would survive that substitution --
## which is exactly why the line has to say so rather than be assumed harmless.
func _page_shot(path: String) -> void:
	# ROWS BEFORE PIXELS. An empty notebook photographs as an empty notebook, so
	# a shot run seeds nothing and instead SAYS what was in it -- if the answer is
	# "nothing", the frame is honest and the reader knows why.
	# `--shot-closed` LEAVES IT SHUT, and that is the A/B for the whole overlay:
	# the same frame with and without the page is what says this file draws
	# anything at all, and it is also the only way to photograph `hud.gd`'s
	# record band without a full-screen wash over it.
	if _args().has("shot-closed"):
		print("journal: SHOT WITH THE PAGE CLOSED (control) -- what is on the "
			+ "frame is hud.gd's band and nothing of this file's")
	else:
		open_page()
	for _i in 8:
		await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var err := img.save_png(path)
	print("JOURNALSHOT %s %dx%d ops=%d facts=%d costs=%d driver=%s adapter=%s "
		% [path, img.get_width(), img.get_height(), _page_ops, facts.size(),
			costs.size(), RenderingServer.get_video_adapter_api_version(),
			RenderingServer.get_video_adapter_name()]
		+ "err=%d" % err)
	# THE CLOSED SHOT MUST NOT BE ASKED TO HAVE DRAWN. `ops > 0` is the assertion
	# that the page renders when it is open; requiring it of the control would
	# make the control fail on the very thing it withholds, which is a control
	# that proves nothing.
	var want_ops: bool = not _args().has("shot-closed")
	get_tree().quit(0 if err == OK and (_page_ops > 0 or not want_ops) else 1)


func _unhandled_input(e: InputEvent) -> void:
	if _page == null:
		return
	if not (e is InputEventKey and e.pressed and not e.echo):
		return
	if e.keycode == PAGE_KEY:
		toggle_page()
		get_viewport().set_input_as_handled()
		return
	if not _page_open:
		return
	match e.keycode:
		KEY_ESCAPE:
			close_page()
			get_viewport().set_input_as_handled()
		KEY_DOWN, KEY_PAGEDOWN:
			_page_scroll += (1 if e.keycode == KEY_DOWN else 10)
			_redraw_page()
			get_viewport().set_input_as_handled()
		KEY_UP, KEY_PAGEUP:
			_page_scroll = maxi(0, _page_scroll
				- (1 if e.keycode == KEY_UP else 10))
			_redraw_page()
			get_viewport().set_input_as_handled()


func open_page() -> void:
	if _page == null:
		return
	_page_open = true
	_page.visible = true
	_redraw_page()
	print("journal: PAGE OPEN -- %d fact(s), %d person(s), %d consequence(s)"
		% [facts.size(), people.size(), costs.size()])


func close_page() -> void:
	if _page == null:
		return
	_page_open = false
	_page.visible = false
	print("journal: page closed")


func toggle_page() -> void:
	if _page_open:
		close_page()
	else:
		open_page()


func page_is_open() -> bool:
	return _page_open


func page_ops() -> int:
	return _page_ops


func _redraw_page() -> void:
	if _page_face != null:
		_page_face.queue_redraw()


## WHAT THE PAGE SAYS, AS DATA. The gate asserts on THIS and `_draw` renders it,
## so a test cannot pass against strings a player never sees -- which is the
## defect one level up from "a gate that reads a committed artefact".
##
## Four columns of one question each, and they are the four the brief named:
## what you know, who you know, what was done to you, and where you stand.
func page_columns() -> Array:
	var know: Array = []
	var ents := entries()
	# Newest first: a notebook is read from the end.
	for i in range(ents.size() - 1, -1, -1):
		know.append(String(ents[i]))
	if know.is_empty():
		know.append("-- nothing learned yet. Facts are minted by things that "
			+ "happen to you: a name given, a call overheard, a leg walked.")

	var met: Array = []
	var pk: Array = people.keys()
	pk.sort()
	for k in pk:
		var s: Dictionary = people[k]
		var nm := String(s.get("name", ""))
		met.append("%s  %s  %d talk(s)  favour %+.2f%s" % [
			(nm if nm != "" else "a face you would know again"),
			String(k),
			int(s.get("talks", 0)), float(s.get("favour", 0.0)),
			("  -- " + String(s.get("last_outcome", ""))
				if String(s.get("last_outcome", "")) != "" else "")])
	if met.is_empty():
		met.append("-- nobody. Press T beside somebody to be introduced.")

	var cost := cost_lines()
	if cost.is_empty():
		cost.append("-- nothing has been done to you. Yet.")

	var stand: Array = []
	var sk: Array = standing.keys()
	sk.sort()
	for k in sk:
		var v := float(standing[k])
		if absf(v) < 0.0005:
			continue
		stand.append("%-22s %+7.3f" % [String(k), v])
	if stand.is_empty():
		stand.append("-- level with all %d ledgers." % standing.size())

	return [
		{"head": "WHAT YOU KNOW", "rows": know, "scroll": true},
		{"head": "WHO YOU KNOW", "rows": met, "scroll": false},
		{"head": "WHAT IT COST YOU", "rows": cost, "scroll": false},
		{"head": "WHERE YOU STAND", "rows": stand, "scroll": false},
	]


## The two lines across the top: who you are and when it is.
func page_header() -> Array:
	var st := consequence_state()
	var who := String(st.get("person", ""))
	if who == "":
		who = "NOBODY THIS BUILD NAMED"
	var card := String(st.get("tier_name", ""))
	var line1 := "%s   %s" % [who.to_upper(),
		(card.to_upper() if card != "" else "NO CARD")]
	if String(st.get("customs", "")) != "":
		line1 += "   CUSTOMS: %s" % String(st.get("customs", "")).to_upper()
	if int(st.get("convictions", 0)) > 0:
		line1 += "   %d CONVICTION(S)" % int(st.get("convictions", 0))
	var line2 := "DAY %d   %05.2f   %.2f H LIVED" % [_day(),
		(float(_clock.hour()) if _clock != null else -1.0), _lived_h]
	if _jumps > 0:
		line2 += "   %d JUMP(S) SKIPPING %.2f H" % [_jumps, _jumped_h]
	line2 += "   %s" % (_where_now().to_upper() if _where_now() != ""
		else "IN THE CORRIDOR")
	return [line1, line2]


func page_footer() -> String:
	var bits := PackedStringArray()
	bits.append("%d FACT(S)" % facts.size())
	bits.append("%d MET" % people.size())
	bits.append("%d ON THE RECORD" % costs.size())
	bits.append("%d CHECKPOINT(S)" % _checkpoints)
	if not _persist:
		bits.append("PERSISTENCE OFF (CONTROL)")
	if not _refusals.is_empty():
		bits.append("%d REFUSED" % _refusals.size())
	return "   ".join(bits)


## The full page as flat text, for a log and for a gate.
func page_text() -> Array:
	var out: Array = []
	for h in page_header():
		out.append(String(h))
	for c in page_columns():
		out.append("== %s ==" % String(c["head"]))
		for r in c["rows"]:
			out.append("   " + String(r))
	out.append(page_footer())
	return out


## THE PAGE ITSELF.
class Page extends Control:
	var j                                  # the journal that owns this page
	var _font: Font = ThemeDB.fallback_font

	func _draw() -> void:
		if j == null or _font == null:
			return
		j._page_ops = 0
		var sz := size
		var s: float = maxf(sz.y / 720.0, 0.35)
		# THE WHOLE FRAME GOES DARK, and that is the one place this overlay is
		# allowed to be heavier than the HUD: a log is a thing you stop to read.
		# Not opaque -- 0.90 -- because the station carrying on behind the page is
		# the scope document's own sentence about existing around you.
		#
		# AND THE FIRST FRAME OF IT WAS MEASURED RATHER THAN ASSUMED, which is why
		# the panels below get plates of their own. At 0.88 over the whole screen,
		# 12% of every layer underneath came through -- and two of those layers are
		# TEXT: `arrival.gd`'s card caption (layer 9) landed across the words
		# PERSONAL LOG, and `hud.gd`'s own record band (layer 8) read through the
		# bottom right corner. A wash that is uniform cannot distinguish the
		# corridor behind the page, which should show, from another interface's
		# lettering, which must not. The cure is local: dark where this page has
		# words, thin where it does not.
		_rect(Rect2(Vector2.ZERO, sz), Color(P_INK, 0.90))

		var m := 46.0 * s
		var top := 40.0 * s

		# -- the head ---------------------------------------------------------
		var head: Array = j.page_header()
		_rect(Rect2(0.0, 0.0, sz.x, top + 62.0 * s), Color(P_INK, 0.86))
		_caps(Vector2(m, top), "PERSONAL LOG", int(roundf(24.0 * s)),
			Color(P_CYAN, 0.98), 4.0 * s)
		_bracket(Vector2(m - 14.0 * s, top - 22.0 * s), 18.0 * s, 26.0 * s,
			Color(P_CYAN, 0.75), s)
		_line(Vector2(m, top + 12.0 * s), Vector2(sz.x - m, top + 12.0 * s),
			Color(P_CYAN, 0.40), s)
		_caps(Vector2(m, top + 34.0 * s), String(head[0]),
			int(roundf(13.0 * s)), Color(P_AMBER, 0.92), 2.0 * s)
		_caps(Vector2(m, top + 52.0 * s), String(head[1]),
			int(roundf(11.0 * s)), Color(P_CYAN, 0.62), 1.6 * s)

		# -- four panels ------------------------------------------------------
		# Two columns; the left one is the fact list and takes the scroll, the
		# right one stacks the three short ledgers. The split is 54/46 because the
		# fact lines carry their own source sentence and are the long ones.
		var body_y := top + 78.0 * s
		var body_h := sz.y - body_y - 46.0 * s
		var gap := 26.0 * s
		var lw: float = (sz.x - m * 2.0 - gap) * 0.54
		var rw: float = (sz.x - m * 2.0 - gap) - lw
		var cols: Array = j.page_columns()

		_panel(Rect2(m, body_y, lw, body_h), String(cols[0]["head"]),
			cols[0]["rows"], s, int(j._page_scroll), true)

		var rh: float = (body_h - gap * 2.0) / 3.0
		var ry := body_y
		for i in [1, 2, 3]:
			_panel(Rect2(m + lw + gap, ry, rw, rh), String(cols[i]["head"]),
				cols[i]["rows"], s, 0, false)
			ry += rh + gap

		# -- the foot ---------------------------------------------------------
		var fy := sz.y - 26.0 * s
		_rect(Rect2(0.0, fy - 20.0 * s, sz.x, sz.y - fy + 20.0 * s),
			Color(P_INK, 0.86))
		_line(Vector2(m, fy - 14.0 * s), Vector2(sz.x - m, fy - 14.0 * s),
			Color(P_CYAN, 0.30), s)
		_caps(Vector2(m, fy), String(j.page_footer()), int(roundf(10.0 * s)),
			Color(P_CYAN, 0.55), 1.4 * s)
		var hint := "J CLOSE    UP DOWN SCROLL"
		var hw := _caps_w(hint, int(roundf(10.0 * s)), 1.4 * s)
		_caps(Vector2(sz.x - m - hw, fy), hint, int(roundf(10.0 * s)),
			Color(P_AMBER, 0.55), 1.4 * s)

	# -- one titled panel of lines -----------------------------------------
	func _panel(r: Rect2, head: String, rows: Array, s: float, scroll: int,
			scrollable: bool) -> void:
		var px := int(roundf(10.0 * s))
		var lh: float = px * 1.62
		var room := int(floorf((r.size.y - 24.0 * s) / lh))
		if room < 1:
			room = 1
		var first := 0
		if scrollable:
			first = clampi(scroll, 0, maxi(0, rows.size() - room))
		# LAID OUT BEFORE ANYTHING IS DRAWN, so the plate can be the size of the
		# WORDS rather than the size of the panel. A plate the size of the panel
		# would black out most of the frame -- and the point of a 0.90 wash is
		# that the station is still there behind the page.
		#
		# WRAPPED BY MEASUREMENT, NOT BY A CHARACTER COUNT. A fact line carries
		# its whole source sentence and the panel is a measured width, so cutting
		# at "80 characters" would clip on one frame size and leave a gap on
		# another.
		var lines: Array = []
		var shown := 0
		for i in range(first, rows.size()):
			if shown >= room:
				break
			var raw := String(rows[i])
			var parts := _wrap(raw, r.size.x - 16.0 * s, px, 1.2 * s)
			for k in parts.size():
				if shown >= room:
					break
				lines.append({"s": String(parts[k]), "lead": k == 0,
					"cost": raw.begins_with("day ")})
				shown += 1
		var used: float = 26.0 * s + lh * float(lines.size()) + 6.0 * s
		_rect(Rect2(r.position - Vector2(8.0 * s, 16.0 * s),
			Vector2(r.size.x + 16.0 * s, used + 16.0 * s)),
			Color(P_INK, 0.80))

		_line(r.position, Vector2(r.end.x, r.position.y), Color(P_CYAN, 0.55), s)
		_bracket(r.position, 14.0 * s, 12.0 * s, Color(P_CYAN, 0.75), s)
		var hpx := int(roundf(12.0 * s))
		_caps(r.position + Vector2(2.0 * s, -6.0 * s), head, hpx,
			Color(P_AMBER, 0.90), 2.4 * s)
		var y: float = r.position.y + 22.0 * s
		for row in lines:
			var col: Color = (P_AMBER if bool(row["cost"]) else P_CYAN)
			var dim: float = (0.88 if bool(row["lead"]) else 0.55)
			_caps(Vector2(r.position.x + 8.0 * s, y), String(row["s"]), px,
				Color(col, dim), 1.2 * s)
			y += lh
		if scrollable and rows.size() > room:
			var more := "%d MORE  (%d-%d OF %d)" % [
				maxi(0, rows.size() - first - shown), first + 1,
				first + shown, rows.size()]
			_caps(Vector2(r.position.x + 8.0 * s, y + 6.0 * s), more,
				int(roundf(9.0 * s)), Color(P_AMBER, 0.60), 1.2 * s)

	# -- primitives ---------------------------------------------------------
	func _rect(r: Rect2, c: Color) -> void:
		draw_rect(r, c, true)
		j._page_ops += 1

	func _line(a: Vector2, b: Vector2, c: Color, s: float) -> void:
		draw_line(a, b, c, maxf(1.0, roundf(s)), false)
		j._page_ops += 1

	func _bracket(at: Vector2, dx: float, dy: float, c: Color,
			s: float) -> void:
		_line(at, at + Vector2(dx, 0), c, s)
		_line(at, at + Vector2(0, dy), c, s)

	## Small capitals with the letters pushed apart -- `hud.gd::_tracked`'s rule,
	## and the reason is the same: untracked default-font capitals read as a debug
	## overlay, which is what a page like this must not look like.
	func _caps(pos: Vector2, text: String, px: int, c: Color,
			track: float) -> float:
		var t := text.to_upper()
		var x := pos.x
		for i in t.length():
			var ch := t[i]
			draw_char(_font, Vector2(x, pos.y), ch, px, c)
			x += _font.get_char_size(ch.unicode_at(0), px).x + track
			j._page_ops += 1
		return x - pos.x

	func _caps_w(text: String, px: int, track: float) -> float:
		var t := text.to_upper()
		var w := 0.0
		for i in t.length():
			w += _font.get_char_size(t[i].unicode_at(0), px).x + track
		return maxf(w - track, 0.0)

	func _wrap(text: String, width: float, px: int, track: float) -> Array:
		var out: Array = []
		var line := ""
		for word in text.split(" ", false):
			var t := (word if line == "" else line + " " + word)
			if _caps_w(t, px, track) > width and line != "":
				out.append(line)
				line = word
			else:
				line = t
		if line != "":
			out.append(line)
		if out.is_empty():
			out.append("")
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
			"lived_h": _lived_h, "costs": costs}


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
	# WHAT WAS DONE TO YOU COMES BACK WITH WHAT YOU KNOW. A missing key leaves the
	# ledger EMPTY rather than untouched, which is the honest reading of a save
	# written before this existed: that session recorded no consequences, so a
	# world restored from it has none. Carrying the live rows across a load would
	# make a reload the one way to keep a consequence a save did not contain.
	var cs = d.get("costs", [])
	costs = (cs.duplicate(true) if typeof(cs) == TYPE_ARRAY else [])
	# ...AND SO ARE THE OBSERVER'S BASELINES, for the same reason one level
	# out: every other section of the save is being restored in the same
	# frame, and a restored counter moving is not the world moving. See
	# `_watch_talk`.
	_resync = true
	_cost_resync = true
	_have_pos = false


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
		"persist":
			await _phase_persist(host)
		"continue":
			await _phase_continue(host)
		_:
			print("JOURNAL gate=FAIL unknown --phase=%s" % phase)
			get_tree().quit(2)


func _settle(n: int) -> void:
	for _i in n:
		await get_tree().physics_frame


## WALK A LEG, TALK TO SOMEBODY, TAKE A LINE -- then quit.
##
## NOT ONE FACT IS MINTED IN THIS FUNCTION, and that is round two's whole
## change. Round one called `given_name`, `learn_route` and `learn_tell`
## directly, so the acceptance exercised a path no player is on and its
## reviewer said so in one sentence: *"the gate cannot see this because it
## calls the minters directly."* Everything below drives the WORLD -- the
## player's own `step()`, the T key through the viewport, the stance key --
## and every fact that appears is minted by `_watch()` off what the world
## did. If the observer is unwired, this phase learns NOTHING and the gate
## fails, which is the property round one did not have.
func _phase_learn(host) -> void:
	await _settle(30)
	var pair := _leg_pair()
	var body = (host._player() if host != null and host.has_method("_player")
		else null)
	if body == null or pair.size() != 2:
		print("JOURNAL gate=FAIL no player body (%s) or no derivable leg (%s)"
			% [str(body != null), str(pair)])
		get_tree().quit(2)
		return
	# ONE DRIVER. `player.gd::drive_externally` exists for exactly this and its
	# own docstring says why: with no window there is no input, so leaving
	# `_physics_process` on would step the body a second time every frame with
	# a zero wish and rebuild its basis from a yaw nothing set.
	if body.has_method("drive_externally"):
		body.drive_externally()
	var to_pos := _partner_pos()
	if to_pos == Vector3.ZERO:
		to_pos = _place_pos(pair[1])
	# START WHERE THE STATION ITSELF STARTS A PLAYER, and that is a MEASURED
	# finding rather than a preference. Two earlier versions of this stood the
	# body inside `pair[0]` -- at the room's centroid, then at the actor row
	# nearest the destination -- and both WEDGED, covering 6.3 m in 3,000
	# frames, which is exactly the "a capsule dropped on that wedges on an
	# internal edge" symptom `station/collision.py` was written for.
	# `station/boot.py` derives its spawn off the collision shell's own floor
	# and asserts the two agree, so it is the one point on this deck known to
	# be standable. From there the walk runs down the ring corridor and passes
	# THROUGH `pair[0]` on its way to `pair[1]` -- which is how a player
	# reaches either of them anyway.
	var from_pos := _spawn_pos()
	if from_pos == Vector3.ZERO:
		from_pos = _nearest_body_in(pair[0], to_pos)
	# THE START IS A PLACEMENT AND THE JOURNEY IS NOT. No leg is open yet, and
	# `_watch_feet` starts counting the moment the body leaves a named place.
	body.global_position = from_pos
	await _settle(6)
	var walked := 0.0
	var frames := 0
	if _args().has("teleport"):
		# THE CONTROL PLY-05 AND PLY-07 BOTH NEED: the same two endpoints and
		# the same clock, with the ground never crossed. `_watch_feet` sees a
		# step no leg could take, poisons the leg, and the route fact is
		# refused -- so a fast-travel that pretended to be a walk cannot buy
		# the porter's knowledge.
		print("JOURNAL: TELEPORTED (control) -- the ground was never covered")
		body.global_position = to_pos
		await _settle(10)
	else:
		var d: float = body.get_physics_process_delta_time()
		var last: Vector3 = body.global_position
		# ALONG THE RING, NOT THROUGH IT. Both places sit on the same 211.5 m
		# radius at different ring angles, so the straight line between them
		# cuts a chord THROUGH the deck's inboard wall. Steering along the
		# tangent is the direction a corridor actually runs -- and it is
		# derived from the two positions rather than written down, so it holds
		# for any pair on any ring.
		var stuck := 0
		var side := 1.0
		var z0: float = from_pos.z
		# THE WALK ENDS WHEN THE LEG IS EARNED, and reaching the person is a
		# separate step below. TWO RUNS WERE SPENT ESTABLISHING WHY, and the
		# answer is worth keeping: the ring CORRIDOR is walkable end to end --
		# 221.2 m at 4.15 m/s with nothing in the way and zero placements --
		# and the INTERIOR of a customs hall is not, because
		# `station/collision.py` sweeps a smooth shell for the corridor while a
		# room's own fittings stay solid. Told to walk the last stretch to Bo
		# Rossi the body reached `customs_north` and then spent 1,200 frames
		# going nowhere, 25.7 m short, exactly as it had when an earlier
		# version started it inside the room.
		#
		# So: the LEG is walked, and the last 25 m is a placement -- the same
		# placement `_phase_recall` makes to ask who is offered, and it happens
		# AFTER the leg has closed, so it cannot buy the route fact. The
		# `--teleport` control replaces the WALK and still fails.
		while frames < 6000 and _here_place != pair[1]:
			var pos: Vector3 = body.global_position
			var dir: Vector3 = to_pos - pos
			if dir.length() < 1.4:
				break
			var out := Vector3(pos.x, pos.y, 0.0).normalized()
			var tan := Vector3(-out.y, out.x, 0.0)
			if tan.dot(dir) < 0.0:
				tan = -tan
			# The ring is walked round; the axial error is trimmed, gently,
			# because a corridor is 33 m long and only a few metres wide.
			var steer := (tan + Vector3(0, 0, clampf(dir.z, -1.0, 1.0)
				* 0.15)).normalized()
			# A BODY THAT HAS STOPPED IS AGAINST SOMETHING, and a ring corridor
			# has two sides -- both along the station's AXIS, because the
			# corridor's length is the ring. Fifteen frames of no progress is a
			# quarter of a second at a walk, which no open floor produces. The
			# sidestep is BLENDED and BOUNDED: an earlier version steered
			# straight along +Z, walked the body off the 33 m end of the deck
			# and let it fall, which read as 55 km "walked" in 2,000 frames.
			if stuck > 15:
				var z_off: float = pos.z - z0
				var s: float = side
				if absf(z_off) > 6.0:
					s = -signf(z_off)
				steer = (steer * 0.6 + Vector3(0, 0, s) * 0.8).normalized()
				if stuck > 120:
					side = -side
					stuck = 16
			body.step(d, Vector2(0, 1), false, false, steer)
			await get_tree().physics_frame
			var moved: float = body.global_position.distance_to(last)
			walked += moved
			stuck = (0 if moved > 0.02 else stuck + 1)
			last = body.global_position
			frames += 1
			if frames % 600 == 0:
				print("JOURNAL: ...%d frames, %.1f m, %.1f m to go, in %s"
					% [frames, walked, dir.length(),
						(_here_place if _here_place != "" else "the corridor")])
		print("JOURNAL: WALKED %s -> %s, %.1f m under its own feet in %d "
			% [pair[0], pair[1], walked, frames]
			+ "frames, standing in %s" % (_here_place if _here_place != ""
				else "the corridor"))
	# THE CONVERSATION, THROUGH THE KEY A PLAYER PRESSES. `dialogue.gd` binds
	# KEY_T in `_unhandled_input` and calls `talk()`; pushing the event into
	# the viewport runs that binding rather than going round it, so what this
	# proves is that the shipped keypress reaches the notebook.
	var who = await _scan_partner()
	if _args().has("mute"):
		# THE CONTROL FOR THE OTHER HALF: everything else identical, and the
		# key never pressed. No conversation, therefore no name, therefore no
		# pass -- which is what makes the name clause in `_phase_recall` a
		# requirement rather than a decoration.
		print("JOURNAL: MUTE (control) -- the T key was never pressed")
	elif who == null:
		print("JOURNAL no conversation was offered -- nobody to be introduced")
	else:
		_press(KEY_T)
		await _settle(4)
		# ...and then keep pressing until the menu is armed, because the
		# stance is where a conversation costs something. `talk()` refuses to
		# walk past an unanswered question, which is the state we want.
		for _i in 24:
			if int(_dlg().said()) > 0 or _dlg().picked() != "":
				break
			_press(KEY_1)
			await _settle(1)
			_press(KEY_T)
			await _settle(1)
		await _settle(4)

	var got: Array[String] = []
	for k in facts:
		got.append(String(k))
	print("JOURNAL learned=%d ids=%s legs=%d placements=%d"
		% [got.size(), ", ".join(PackedStringArray(got)), _legs, _placed])
	print("JOURNAL standing %s" % _standing_line())
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
	# THE READING PROCESS MAY NOT WRITE. With minting live, this phase minted
	# its own `name_given` on the frame the save came back -- see `_watch_talk`
	# -- and then found "the name" present because it had just written it. A
	# gate that can satisfy itself is the defect this repository names most
	# often, so the minter is switched OFF for the whole phase and every fact
	# reported below is therefore a fact that arrived in a FILE.
	_minting = false
	print("JOURNAL: MINTING OFF for the recall phase -- everything below "
		+ "came out of the slot")
	var before := facts.size()
	if _args().has("no-restore"):
		print("JOURNAL: RESTORE SKIPPED (control)")
	else:
		host.load_from("journal")
	var want := _expected_ids()
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
	# --- THE THREE CLAUSES ROUND ONE DID NOT HAVE -------------------------
	#
	# Its reviewer's finding was exact: `want.size() >= 2` let the whole
	# conversation half of the acceptance DISAPPEAR whenever `_scan_partner`
	# returned null, so *"learn and recall agree BY CONSTRUCTION when the
	# dialogue system is entirely absent"* -- which is the state that
	# container was in. A gate whose subject can vanish is a gate that passes
	# on a station with nobody on it.
	#
	# 1. THE NAME IS NAMED. Not "at least two facts": THIS fact, about the
	#    person the deck actually offered, or FAIL.
	# 2. `people` AND `standing` ARE CHECKED. `save_state` returns three
	#    dictionaries and round one read only the first, so a restore could
	#    hand back `{"people": {}, "standing": {}}` and still print PASS with
	#    the loss visible on the adjacent line.
	# 3. THE LEDGER IS NON-ZERO. An all-zero ledger is what a fresh journal
	#    has, so a `standing` that came back at its boot value is
	#    indistinguishable from one that never loaded.
	var named := _recall_a_name()
	var ledger := _standing_line()
	var moved := 0
	for k in standing:
		if absf(float(standing[k])) > 1e-9:
			moved += 1
	var ok: bool = (missing.is_empty() and unsourced.is_empty()
		and not invented and want.size() >= 1 and named
		and people.size() >= 1 and standing.size() >= 1 and moved >= 1)
	for e in entries():
		print("JOURNAL entry | " + e)
	print("JOURNAL " + journal_report())
	print("JOURNAL gate=%s wanted=%d had_before_load=%d missing=%s "
		% ["PASS" if ok else "FAIL", want.size(), before,
			("none" if missing.is_empty() else ", ".join(
				PackedStringArray(missing)))]
		+ "unsourced=%s a_fact_never_learned_is_present=%s "
		% [("none" if unsourced.is_empty() else ", ".join(
			PackedStringArray(unsourced))), str(invented)]
		+ "name_back=%s(%s) people=%d ledgers_moved=%d"
		% [str(named), (_named_back if _named_back != "" else "nobody"),
			people.size(), moved])
	print("JOURNAL standing %s" % ledger)
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
## Who the restored journal says gave the player their name, or "".
var _named_back := ""


## IS THERE A NAME IN HERE, GIVEN BY SOMEBODY WHO IS REALLY ON THIS DECK?
##
## THIS REPLACED A DERIVED FACT ID, AND THE REASON IS A MEASUREMENT. The first
## version re-scanned for the partner in this phase and looked for that exact
## id -- and the two phases DISAGREED about who it was: the learn phase, which
## reaches `customs_north` at 13.90 after a 221 m walk, is offered Bo Rossi;
## the recall phase, which boots at 13.01 and stands in the same spot, is
## offered David Nakamura. `dialogue.gd::scan` takes whoever is nearest and in
## the cone, and the crowd is not the same crowd an hour later. Round one's own
## header records the identical surprise about the identical function.
##
## So the question is asked the way it can be answered: a `name_given` fact,
## about somebody in THIS deck's cast, whose CAST-05 memory slot also came back
## saying the name was given. With minting switched off for the phase and
## `had_before_load` printed beside it, all three of those had to arrive in a
## file.
func _recall_a_name() -> bool:
	_named_back = ""
	var cast := {}
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) == TYPE_DICTIONARY:
			cast[String(who.get("id", ""))] = String(who.get("name", ""))
	for fid in facts:
		var f: Dictionary = facts[fid]
		if String(f.get("kind", "")) != "name_given":
			continue
		var subj := String(f.get("subject", ""))
		if not cast.has(subj) or not name_given(subj):
			continue
		_named_back = "%s / %s" % [String(f.get("value", "")), subj]
		return true
	return false


func _expected_ids() -> Array[String]:
	var out: Array[String] = []
	# THE LEG IS THE ONE THE FEET WALKED, derived the same way in both phases
	# -- from the deck's own cast and `transit.py`'s own arcs, with nothing
	# read out of the save. This one IS a named id, because unlike the
	# conversation it does not depend on which of 83 people the crowd put
	# nearest at the hour the phase happens to boot at.
	var pair := _leg_pair()
	if pair.size() == 2:
		var k := "%s>%s" % [pair[0], pair[1]]
		out.append(fact_id("route_time", k, "transit", k))
	else:
		print("JOURNAL: NO LEG IS DERIVABLE ON THIS DECK")
	return out


# ===========================================================================
#  THE TWO-LAUNCH GATE: does what happened to you survive closing the game
# ===========================================================================
#
# TWO PROCESSES, FOR THE REASON `--phase=learn`/`recall` ALREADY GIVES ONE
# SCREEN UP: a save and a restore inside one running engine passes on a build
# whose file never reaches the disk. `--phase=persist` puts a card in a reader
# and QUITS; `--phase=continue` is a second `godot` that boots from nothing and
# asks what came back.
#
# WHAT IS REAL IN THIS GATE AND WHAT IS SUBSTITUTED, said plainly because a gate
# that quietly stands in for the thing it tests is worse than none.
#
#   REAL: the key. `_press(KEY_E)` goes through the viewport into
#         `interact.gd::_unhandled_input`, which calls `use()`, which dispatches
#         `_verb_operate`, which asks `arrival.gd::customs_verdict`, which
#         computes the verdict from the nine fields on the card the body is
#         carrying, which routes a refusal into `enforcement.gd::refuse_at` and
#         writes the record into the economy ledger. Not one step of that chain
#         is bypassed and not one of those files is touched by this session.
#
#   SUBSTITUTED: the WALK. The body is PLACED at the reader. That is not a
#         convenience -- measured this session on the shipped build,
#         `arrival.gd --arrival-test --arrival-from=present --arrival-budget=4000`
#         walked **888.6 m and never got within 174.1 m of the reader**, and its
#         own verdict line says so: `reader_used=false outcome=NOT-COMPUTED`.
#         The customs hall's interior is not navigable by the bug-algorithm
#         steer, which `arrival.gd`'s own comments already predicted and which a
#         navmesh is the answer to. THAT IS AN OPEN DEFECT AND IT IS NOT THIS
#         GATE'S TO CLOSE; what this gate must not do is let the walk's failure
#         hide the persistence question behind it.
#
# THE PLACEMENT IS DECLARED TO THE JOURNAL'S OWN WATCHER rather than hidden from
# it: `_watch_feet` will see a step no leg could take and poison the open leg,
# which is correct -- a route fact must not be buyable by teleport, and this run
# does not claim one.
func _phase_persist(host) -> void:
	await _settle(30)
	# THE TWO SLOT NAMES MUST BE ONE STRING. `main.gd::MENU_SLOT` is what
	# CONTINUE reads and `save.gd::AUTO_SLOT` is what the checkpoint writes; if
	# they ever drift, every launch below would pass while the front door stayed
	# dead. Read off the host rather than assumed.
	var ms = host.get("MENU_SLOT")
	if ms == null:
		# A constant this engine build does not expose through `get()` is not a
		# failure of the thing being tested, and reporting it as one would be a
		# gate failing on its own instrument. Said out loud instead.
		print("PERSIST: main.gd::MENU_SLOT is not readable through get() on this "
			+ "build -- the slot agreement is UNCHECKED (save.gd::AUTO_SLOT=%s)"
			% Save.AUTO_SLOT)
	elif String(ms) != Save.AUTO_SLOT:
		print("PERSIST gate=FAIL main.gd::MENU_SLOT=%s but save.gd::AUTO_SLOT=%s"
			% [String(ms), Save.AUTO_SLOT])
		get_tree().quit(2)
		return
	# START FROM NOTHING. Without this the gate could pass on a file an earlier
	# run left behind -- and the `--no-persist` control could pass hardest of all.
	Save.erase(Save.AUTO_SLOT)
	print("PERSIST: slot %s cleared -- this launch starts with no memory"
		% Save.slot_path(Save.AUTO_SLOT))

	# THE LOOKUP BUDGET IS LIFTED FOR THIS ONE CALL. `_look_now()` throttles the
	# watcher's search so a build with no `enforcement.gd` does not walk a
	# 907-cell tree every frame for ever; a gate asking once must not inherit the
	# throttle and report "no interact node" because it asked on the wrong frame.
	_looking = true
	var it = _interact()
	var body = _body()
	if it == null or body == null:
		print("PERSIST gate=FAIL interact=%s player=%s"
			% [str(it != null), str(body != null)])
		get_tree().quit(2)
		return
	var group := String(_args().get("reader", "customs_north__prop_identicard_reader"))
	var row := _sidecar_row(group)
	if row.is_empty():
		print("PERSIST gate=FAIL no sidecar row for %s" % group)
		get_tree().quit(2)
		return
	if body.has_method("drive_externally"):
		body.drive_externally()
	# BOTH SIDES, AND THE PROMPT DECIDES WHICH ONE WAS RIGHT. `interact.gd`'s own
	# `prompt_group()` is the answer -- the same value the E key acts on -- so
	# this cannot settle on a side that looks right and would not have prompted.
	var placed := false
	var side := 0.0
	for s in [1.0, -1.0]:
		if not _stand_at_panel(body, row, s):
			continue
		await _settle(8)
		it.refresh()
		print("PERSIST: side %+.0f -- %.2f m, %s"
			% [s, it.range_to(group), it.probe(group)])
		if String(it.prompt_group()) == group:
			placed = true
			side = s
			break
	print("PERSIST: standing at %s from side %+.0f -- prompt=%s"
		% [group, side, (it.prompt_group() if it.prompt_group() != "" else "-")])
	# THE KEY, THROUGH THE VIEWPORT. `interact.gd` binds E in `_unhandled_input`
	# and calls `use()`; pushing the event runs THAT binding rather than going
	# round it, which is the half round one of the journal gate was told it had
	# skipped.
	it.refresh()
	var before := costs.size()
	if _args().has("no-press"):
		print("PERSIST: KEY NEVER PRESSED (control) -- nothing should happen")
	else:
		_press(KEY_E)
	await _settle(30)
	# THE CONSEQUENCE IS ALLOWED TO ARRIVE. A refusal calls two officers who then
	# have to cross the floor; quitting on the press would kill the process
	# between the cause and the effect -- `arrival.gd::_advance` had to learn the
	# same thing and its comment is the one this follows.
	var hold := int(_args().get("persist-hold", "240"))
	for _i in hold:
		await get_tree().physics_frame

	var st := consequence_state()
	print("PERSIST: %s" % JSON.stringify(st))
	for ln in page_text():
		print("PERSIST page | " + ln)
	var snap: Dictionary = Save.read(Save.AUTO_SLOT)
	var on_disk := not snap.is_empty()
	var head := Save.headline(snap)
	var sections: Array = (snap.get("_state", {}) as Dictionary).keys() \
		if on_disk else []
	sections.sort()
	var rows := costs.size()
	var ok: bool = (placed and rows > before and _checkpoints > 0 and on_disk
		and head != "" and sections.has("journal") and sections.has("interact"))
	print(("PERSIST gate=%s placed=%s verdict=%s costs=%d(+%d) checkpoints=%d "
		+ "slot_written=%s headline=%s sections=%s") % [
		("PASS" if ok else "FAIL"), str(placed).to_lower(),
		(String(st.get("customs", "")) if String(st.get("customs", "")) != ""
			else "-"),
		rows, rows - before, _checkpoints, str(on_disk).to_lower(),
		("\"%s\"" % head if head != "" else "-"),
		("/".join(PackedStringArray(sections)) if not sections.is_empty()
			else "-")])
	get_tree().quit(0 if ok else 1)


## LAUNCH TWO. Boot from nothing, press CONTINUE, and ask what the station
## remembers about you.
##
## THE READING PROCESS MAY NOT WRITE, and `_phase_recall` above paid a whole run
## to learn it: with the minter live, a phase that is supposed to only read can
## mint the very thing it then finds. Minting is off for the whole of this phase,
## so every row reported below arrived in a FILE.
func _phase_continue(host) -> void:
	await _settle(30)
	_minting = false
	print("CONTINUE: MINTING OFF -- everything below came out of the slot")
	var before := costs.size()
	var snap_on_disk: Dictionary = Save.read(Save.AUTO_SLOT)
	print("CONTINUE: slot %s -- %s" % [Save.slot_path(Save.AUTO_SLOT),
		("EMPTY, there is nothing to come back to" if snap_on_disk.is_empty()
			else Save.describe(snap_on_disk))])
	if _args().has("no-restore"):
		print("CONTINUE: RESTORE SKIPPED (control)")
	else:
		host.load_from(Save.AUTO_SLOT)
	await _settle(10)

	var st := consequence_state()
	for ln in page_text():
		print("CONTINUE page | " + ln)
	# WHAT THE LEDGER SAYS, BESIDE WHAT THE SAVE SAYS. There are two persistence
	# channels in this build and they are not the same: `interact.gd` writes the
	# record into `station/generated/economy.json` on the frame it happens, and
	# the save slot carries the rest of the world. Reporting only one would leave
	# the other free to disagree.
	var ledger_status := String(st.get("customs", ""))
	var head := Save.headline(snap_on_disk)
	var ok: bool = (costs.size() > before and costs.size() > 0 and head != ""
		and ledger_status != "")
	print(("CONTINUE gate=%s costs_before=%d costs_after=%d headline=%s "
		+ "ledger_customs=%s tier=%d(%s) person=%s facts=%d") % [
		("PASS" if ok else "FAIL"), before, costs.size(),
		("\"%s\"" % head if head != "" else "-"),
		(ledger_status if ledger_status != "" else "-"),
		int(st.get("tier", -1)), String(st.get("tier_name", "-")),
		String(st.get("person", "-")).replace(" ", "_"), facts.size()])
	for ln in cost_lines():
		print("CONTINUE cost | " + ln)
	get_tree().quit(0 if ok else 1)


## One row out of the interactables sidecar the deck was built with. The same
## document `interact.gd` binds its `Item`s from, so the position this gate
## walks to cannot disagree with the box the prompt is measured against.
func _sidecar_row(group: String) -> Dictionary:
	var root := _repo_root()
	var boot := root.path_join("station/generated/scene/boot.json")
	if not FileAccess.file_exists(boot):
		return {}
	var bf := FileAccess.open(boot, FileAccess.READ)
	var bd = JSON.parse_string(bf.get_as_text())
	bf.close()
	if typeof(bd) != TYPE_DICTIONARY:
		return {}
	var p := String(bd.get("interact", ""))
	if p == "" or not FileAccess.file_exists(p):
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(rows) != TYPE_ARRAY:
		return {}
	for r in rows:
		if typeof(r) == TYPE_DICTIONARY and String(r.get("group", "")) == group:
			return r
	return {}


## Stand a body in front of a wall panel and look at it.
##
## THE THREE DIRECTIONS ARE DERIVED FROM THE STATION, not written down. UP is
## towards the axis (`-r_hat`), which is the same derivation `_scan_partner` and
## `dialogue.gd::_up_at` make and the one that puts the eye in the ceiling when
## it is wrong. DOWN to the floor is how far outboard the deck is under the
## panel, taken from the body's own radius rather than from a constant. BACK is
## whichever direction, in the plane the body walks on, points into the room the
## panel belongs to -- read off the sidecar row's own `place` box.
func _stand_at_panel(body, row: Dictionary, side: float) -> bool:
	var c = row.get("centre", [])
	if typeof(c) != TYPE_ARRAY or (c as Array).size() != 3:
		return false
	var centre := Vector3(float(c[0]), float(c[1]), float(c[2]))
	var radial := Vector3(centre.x, centre.y, 0.0)
	if radial.length() < 1.0:
		return false
	var out: Vector3 = radial.normalized()      # "down" on a spun ring
	var up: Vector3 = -out
	# THE FLOOR UNDER THE PANEL, at the radius the body was already standing at.
	# `boot.json`'s spawn is the one point on this deck known to be standable and
	# the body is on it when this runs, so its own radius is the deck's floor.
	var here: Vector3 = body.global_position
	var floor_r: float = Vector3(here.x, here.y, 0.0).length()
	var foot: Vector3 = out * floor_r + Vector3(0, 0, centre.z)
	# WHICH SIDE OF THE PANEL. It is 0.065 m thin along Z, so there are exactly
	# two, and the caller tries both rather than deriving one -- see the loop in
	# `_phase_persist`. THE FIRST VERSION OF THIS DERIVED IT from the place's own
	# centroid and got it backwards, and the symptom was the one `player.gd::
	# drive_externally`'s header already documents to the degree:
	# `off_axis=160deg/35`, a body standing 1.39 m from a reader it was facing
	# directly away from. Two tries and a printed answer beats a derivation that
	# can be silently wrong.
	var back := Vector3(0, 0, signf(side))
	var stand: Vector3 = foot + back * 1.80 + up * 0.10
	body.global_position = stand

	# THE POSE, THROUGH THE BODY'S OWN ONE CONSTRUCTION SITE.
	# `player.gd::stand_basis` is the project's single right-handed basis
	# expression -- its own header names `npc.gd::_walker_xform` as what happens
	# when a second copy gets the sign wrong and mirrors a crowd for six
	# sessions. Nothing here builds a Basis.
	var fwd: Vector3 = centre - stand
	fwd = fwd - up * fwd.dot(up)
	if fwd.length() < 1e-3:
		return false
	fwd = fwd.normalized()
	if body.has_method("stand_basis"):
		body.global_transform = Transform3D(body.stand_basis(fwd), stand)
	# AND THE EYE IS PITCHED AT THE PANEL, which the basis alone cannot do: a
	# body's basis is flat on the deck and this reader sits 1.2 m off the floor,
	# so a horizontal eye at 1.70 m looks OVER it. `interact.gd::scan` measures
	# its 35-degree cone about the CAMERA axis, so the pitch is not cosmetic --
	# it is the difference between a prompt and no prompt.
	var cam := body.get_node_or_null("Camera3D") as Camera3D
	if cam != null:
		var eye: Vector3 = stand + up * 1.70
		var to: Vector3 = centre - eye
		var p: float = atan2(to.dot(up), to.dot(fwd))
		cam.transform = Transform3D(Basis(Vector3.RIGHT, p),
			Vector3(0, 1.70, 0))
	return true


## The centre of a named place, off the interact sidecar's own rows. Not a second
## register: it is the union of the boxes `hud.gd::_places` unions for the same
## purpose, computed from the same file.
func _place_centre(place: String) -> Vector3:
	if place == "":
		return Vector3.ZERO
	var root := _repo_root()
	var boot := root.path_join("station/generated/scene/boot.json")
	if not FileAccess.file_exists(boot):
		return Vector3.ZERO
	var bf := FileAccess.open(boot, FileAccess.READ)
	var bd = JSON.parse_string(bf.get_as_text())
	bf.close()
	var p := String((bd as Dictionary).get("interact", ""))
	if p == "" or not FileAccess.file_exists(p):
		return Vector3.ZERO
	var f := FileAccess.open(p, FileAccess.READ)
	var rows = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(rows) != TYPE_ARRAY:
		return Vector3.ZERO
	var sum := Vector3.ZERO
	var n := 0
	for r in rows:
		if typeof(r) != TYPE_DICTIONARY or String(r.get("place", "")) != place:
			continue
		var c = r.get("centre", [])
		if typeof(c) != TYPE_ARRAY or (c as Array).size() != 3:
			continue
		sum += Vector3(float(c[0]), float(c[1]), float(c[2]))
		n += 1
	return (sum / float(n) if n > 0 else Vector3.ZERO)


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
	# THE ACCOUNTING IS ZEROED AT THE START OF THE MEASURED WINDOW, and the
	# first version of this was not -- which made the `--jump` control fail for
	# the wrong reason and is exactly the shape of defect this project calls a
	# vacuous A/B. The thirty settle frames advance the clock by 0.01 h, that
	# crossed four of the deck's 62 timed calls, and the control reported
	# `witnessed=4` against a floor of 4: the clause meant to catch a jump had
	# already been satisfied before the jump happened, and only the fact count
	# saved the verdict. All three counters now describe the same interval as
	# `advanced`.
	_witnessed = 0
	_lived_h = 0.0
	_jumped_h = 0.0
	_jumps = 0
	var h0: float = float(_clock.hours_abs())
	var crowd0: int = (int(_life.visible_count()) if _life != null else -1)
	var moved0: float = (float(_clock.hour()) if _clock != null else 0.0)
	var facts0: int = facts.size()
	# HOW MANY FRAMES A CONTINUOUS RUN OF THIS WINDOW COSTS, derived from the
	# clock's own rate and the engine's own physics tick rather than counted
	# after the fact -- because the control below has to be given the SAME
	# number of frames, and a control that ran fewer is a control a reader can
	# fairly dismiss.
	var per_frame: float = maxf(float(_clock.rate)
		/ float(Engine.physics_ticks_per_second), 1e-9)
	var need := int(ceil(SLEEP_H / per_frame))
	var jump := _args().has("jump")
	if jump:
		# THE THING PLY-05 FORBIDS, run deliberately so the difference is a
		# measurement rather than an argument. `set_hour` is `life.gd`'s own
		# jump and its docstring says "a jump is indistinguishable from having
		# waited" -- which is true of the CLOCK and false of the world.
		#
		# AND THE COMPRESSION IS PUT BACK AFTERWARDS, which is the part that
		# makes this control answer the obvious objection. Without it the jump
		# satisfies the loop on frame ZERO, and a reader is entitled to say the
		# control witnessed nothing because it was never given a frame to
		# witness in. With the rate back at its boot value the control runs the
		# SAME %d frames the subject runs, over the SAME 7.25 station hours of
		# arrival -- and still hears nothing, because the hours arrived instead
		# of passing.
		_clock.set_hour(fposmod(float(_clock.hour()) + SLEEP_H, 24.0))
		if _boot_rate > 0.0:
			_clock.rate = _boot_rate
		print("COMPRESS: JUMPED %.2f h (control), rate back to %.4f h/s -- the "
			% [SLEEP_H, float(_clock.rate)]
			+ "same %d frames follow and nothing in them was lived through"
			% need)
	var frames := 0
	while (float(_clock.hours_abs()) - h0 < SLEEP_H or frames < need) \
			and frames < 4000:
		await get_tree().physics_frame
		frames += 1
	var advanced: float = float(_clock.hours_abs()) - h0
	var crowd1: int = (int(_life.visible_count()) if _life != null else -1)
	var minted: int = facts.size() - facts0
	# THE FOUR CLAUSES, AND EACH ONE FAILS A DIFFERENT CONTROL:
	#   advanced   fails `--compress=1`, where the same wall clock buys ~0 h
	#   _witnessed fails `--jump`, where the hours arrive without being lived
	#   minted     is the consequence in the world the player can carry away
	#   world      fails an EMPTY SCENE -- added in round two because its
	#              reviewer was right that `witnessed`/`minted` are one
	#              counter and neither reads the simulation. `_life` is
	#              `life.gd`'s Director, `deck_rooms` is what
	#              `broadcast.audible_at` says this deck can hear, and a run
	#              through a station with neither is a run through nothing.
	#              plus `dialogue.gd::count()`, which is how many people are
	#              actually standing on this deck. A run through a station
	#              with none of those is a run through nothing.
	#
	# AND `crowd1` IS REPORTED RATHER THAN GATED, which is a measurement and
	# not a concession. The first version of this clause required
	# `crowd1 > 0` and FAILED THE SUBJECT: `life.gd::visible_count()` reads
	# **0** in this phase on a deck that demonstrably has 83 speaking people
	# on it, because the Director's visible set is its own streamed crowd
	# rather than the baked cast. Gating on a counter that reads zero on a
	# CORRECT build is how a gate gets quietly relaxed two sessions later.
	# The honest fix is to gate on the population this phase can actually
	# see, and to leave the other number printed where somebody can ask.
	var cast := (int(_dlg().count()) if _dlg() != null else 0)
	var world := (_life != null and not deck_rooms.is_empty() and cast > 0)
	var ok: bool = (advanced >= SLEEP_H * 0.9
		and _witnessed >= WITNESS_FLOOR and minted >= WITNESS_FLOOR and world)
	print("COMPRESS gate=%s advanced=%.3f h in %d frames (wanted %.2f), "
		% ["PASS" if ok else "FAIL", advanced, frames, SLEEP_H]
		+ "lived=%.3f jumped=%.3f witnessed=%d (floor %d) facts %d->%d "
		% [_lived_h, _jumped_h, _witnessed, WITNESS_FLOOR, facts0,
			facts.size()]
		+ "crowd %d->%d says_differently=%d/%d rate=%.4f h/s "
		% [crowd0, crowd1, _hour_moves(moved0, float(_clock.hour())),
			(int(_dlg().count()) if _dlg() != null else 0),
			float(_clock.rate)]
		+ "world=%s (life=%s rooms=%d cast=%d)"
		% [str(world), str(_life != null), deck_rooms.size(), cast])
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


## THE KEY A PLAYER PRESSES, pushed through the viewport so it reaches
## `dialogue.gd::_unhandled_input` exactly as a keyboard would. Calling `talk()`
## would test the function; this tests the BINDING, which is the half round one
## skipped and the half a player is on.
func _press(code: Key) -> void:
	var ev := InputEventKey.new()
	ev.keycode = code
	ev.physical_keycode = code
	ev.pressed = true
	get_viewport().push_input(ev)
	var up := InputEventKey.new()
	up.keycode = code
	up.physical_keycode = code
	up.pressed = false
	get_viewport().push_input(up)


## The leg the feet are asked to walk, DERIVED and identical in both phases:
## the place the deck's first talkable body stands in, and the other end of the
## SHORTEST arc `transit.py` derived that touches it.
##
## Shortest because it has to be walkable in a test: this deck's three rooms
## are 44 m, 620 m and 665 m apart, and a gate that asked for the 665 m leg
## would be a gate nobody ever ran twice.
func _leg_pair() -> Array:
	var b := ""
	var want := _first_talkable()
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) == TYPE_DICTIONARY and String(who.get("id", "")) == want:
			b = String(a.get("place", ""))
			break
	if b == "" or routes.is_empty():
		return []
	var best := ""
	var best_m := INF
	for r in routes:
		var ra := String(r.get("a", ""))
		var rb := String(r.get("b", ""))
		var other := ("" if (ra != b and rb != b) else (rb if ra == b else ra))
		if other == "" or other == b:
			continue
		if float(r.get("metres", INF)) < best_m:
			best_m = float(r.get("metres", INF))
			best = other
	return ([best, b] if best != "" else [])


## Where a place IS, taken as the centroid of the bodies standing in it. The
## actors file is the only thing on this deck that says where a named room is
## in world space; the boot manifest carries the room NAMES and no coordinates.
func _place_pos(place: String) -> Vector3:
	var sum := Vector3.ZERO
	var n := 0
	for a in _actor_rows():
		if String(a.get("place", "")) != place:
			continue
		sum += Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0)))
		n += 1
	return (sum / float(n) if n > 0 else Vector3.ZERO)


## THE ONE POINT ON THIS DECK KNOWN TO BE STANDABLE. `station/boot.py` derives
## it off the collision shell's own floor and prints the two derivations
## agreeing to 4 mm; anything else here would be a second guess at a thing
## already measured.
func _spawn_pos() -> Vector3:
	var root := _repo_root()
	var boot := root.path_join("station/generated/scene/boot.json")
	if not FileAccess.file_exists(boot):
		return Vector3.ZERO
	var f := FileAccess.open(boot, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(d) != TYPE_DICTIONARY:
		return Vector3.ZERO
	var s = d.get("spawn", [])
	if typeof(s) != TYPE_ARRAY or s.size() < 3:
		return Vector3.ZERO
	return Vector3(float(s[0]), float(s[1]), float(s[2]))


## Where the deck's first talkable body stands. The destination of the walk,
## so the leg ends where the conversation can start.
func _partner_pos() -> Vector3:
	var want := _first_talkable()
	for a in _actor_rows():
		var who = a.get("who", {})
		if typeof(who) == TYPE_DICTIONARY and String(who.get("id", "")) == want:
			return Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
				float(a.get("z", 0.0)))
	return Vector3.ZERO


## The body of `place` standing closest to `toward` -- floor by construction,
## and on the side of the room the walk is leaving by.
func _nearest_body_in(place: String, toward: Vector3) -> Vector3:
	var best := Vector3.ZERO
	var best_d := INF
	for a in _actor_rows():
		if String(a.get("place", "")) != place:
			continue
		var p := Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0)))
		var d := p.distance_squared_to(toward)
		if d < best_d:
			best_d = d
			best = p
	return best


## Every ledger that has moved, printed so the two PROCESSES can be compared
## against each other by `station/journal.py` rather than each against itself.
func _standing_line() -> String:
	var parts: Array[String] = []
	var keys: Array = standing.keys()
	keys.sort()
	for k in keys:
		if absf(float(standing[k])) > 1e-9:
			parts.append("%s:%+.4f" % [String(k), float(standing[k])])
	return ("none" if parts.is_empty() else " ".join(
		PackedStringArray(parts)))


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
## How many of the deck's cast say something DIFFERENT at `b` than at `a`.
##
## REPORTED, NOT GATED, and the distinction is the point. `dialogue.gd`'s takes
## are selected by the hour, so this moves after a jump exactly as it moves
## after seven hours of running -- it is evidence that the hour ARRIVED
## somewhere different, and it is evidence about nothing else. The clause that
## can tell a jump from a run is the witness count, and only that one.
func _hour_moves(a: float, b: float) -> int:
	var dlg = _dlg()
	return (int(dlg.hour_moves(a, b)) if dlg != null else -1)


## `dialogue.gd`'s node, asked for each time until one answers.
func _dlg():
	if _dialogue != null and is_instance_valid(_dialogue):
		return _dialogue
	_dialogue = _find_by_method(_host, "lines_shown")
	return _dialogue


## `move = false` AIMS WITHOUT PLACING, which is what the learn phase needs
## once it has WALKED there: standing the body at the partner would be the
## teleport its own control exists to reject, and the leg would be poisoned by
## the act of finding somebody to talk to.
func _scan_partner(move: bool = true):
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
	if move:
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
