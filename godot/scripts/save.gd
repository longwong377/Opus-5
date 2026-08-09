extends RefCounted
##
## EVERYTHING THE PLAYER WOULD LOSE BY CLOSING THE GAME.
##
## There has never been one of these. `docs/MASTER-PLAN.md` §4r R7 records the
## consequence in one line -- *"a condition model with no save is a hunger bar
## that resets"* -- and it generalises: an economy with no save is a shop that
## refills, a journal with no save is a notebook nobody keeps, and a station
## clock with no save means every session starts at 13:00 whatever the last one
## ended at. Every player-facing system this project builds from here is worth
## less than it looks until this file exists.
##
## THE DESIGN RULE, AND IT IS THE ONE THIS REPOSITORY KEEPS RELEARNING. A save
## system that quietly saves four of nine subsystems looks identical, in every
## test, to one that saves all nine: the four round-trip, the gate goes green,
## and the five that were never asked are invisible. So this file's FIRST
## responsibility is not writing a file, it is `audit()` -- naming every live
## subsystem that has no `save_state`, on every capture, in the output. The gap
## is loud or it is not a gap anyone will find.
##
## THE CONTRACT is duck-typed rather than an interface, because GDScript has no
## interfaces and a base class would force every subsystem to inherit from one
## place for no other reason:
##
##     func save_state() -> Dictionary      # everything a reload must restore
##     func load_state(d: Dictionary) -> void
##
## A subsystem implements BOTH or NEITHER. One without the other is worse than
## neither, because it round-trips in a capture and silently drops on restore,
## which is a save file that reads as complete; `capture()` refuses that shape
## by name.
##
## WHAT IS DELIBERATELY NOT SAVED, so nobody looks for it later. The world is
## deterministic from committed data -- the station's geometry, the residents'
## names, homes, jobs and schedules, the incident tables, the material and
## lighting rigs -- and all of it is rebuilt identically at load from
## `station/generated/`. A save file that carried a copy of any of that would be
## a second, staler copy of a computed number, which is the defect `budget.py`'s
## cached collision total taught this project. Saving the SEED and the CLOCK is
## how the world comes back; saving the mesh would be how it comes back wrong.

const VERSION := 1

## Where a slot lives. `user://` rather than `res://` deliberately: `res://` is
## the shipped, read-only build, and the economy ledger's current write-back
## into `station/generated/` is a bug this file does not inherit.
const DIR := "user://saves"

## THE SLOT THE FRONT DOOR OFFERS, AND THE REASON IT IS NAMED HERE.
##
## `main.gd::MENU_SLOT` is the string CONTINUE reads and `main.gd::_front_door`
## passes it to `read()` below. Until session 4u **nothing anywhere called
## `write()` with it**: CONTINUE was permanently disabled, not because the save
## system was broken but because the save system had no caller on the shipped
## path. That is instance twelve of the defect CLAUDE.md counts eleven of, and it
## is the reason this constant exists rather than living only in `main.gd` -- a
## writer and a reader that agree by coincidence of two string literals is the
## same hazard one level down.
##
## `main.gd` is not edited to import this; the two literals are asserted equal by
## `journal.gd::--phase=persist`, which reads `main.gd`'s own `MENU_SLOT` through
## the host and refuses to run if they differ.
const AUTO_SLOT := "auto"


static func slot_path(slot: String) -> String:
	return "%s/%s.json" % [DIR, slot]


## Which live subsystems save, which are exempt and why, and which are neither.
##
## FOUR BUCKETS, AND THE THIRD IS THE ONE THAT MAKES THE NUMBER READABLE. Most
## of this station is deterministic from committed data, so most subsystems have
## nothing to save and never will -- the crowd, the ambience, the streamer, the
## resident bindings. A two-bucket audit calls all of those "missing" for ever,
## the headline reads "4 of 9" in perpetuity, and nobody can tell which of the
## five are decisions and which are bugs. A permanent red that nobody can act on
## is a red nobody reads.
##
## So a subsystem with nothing to save declares it:
##
##     func save_exempt() -> String:   # the REASON, non-empty
##
## and the reason is printed. Silence is still counted as `missing`. That is the
## same move `canon/INVENTIONS.md` makes for a number nobody sourced: the
## project's rule is not that everything must be sourced, it is that an
## unsourced thing must SAY it is unsourced.
##
## `partial` is a subsystem taught HALF the contract, which is always a bug: it
## round-trips in a capture and silently drops on restore, so the save file
## reads as complete.
static func audit(subjects: Dictionary) -> Dictionary:
	var can: Array[String] = []
	var missing: Array[String] = []
	var partial: Array[String] = []
	var exempt: Array[String] = []
	var names: Array = subjects.keys()
	names.sort()
	for name in names:
		var n = subjects[name]
		if n == null or not is_instance_valid(n):
			continue
		var has_save: bool = n.has_method("save_state")
		var has_load: bool = n.has_method("load_state")
		if has_save and has_load:
			can.append(String(name))
			continue
		if has_save or has_load:
			partial.append("%s (%s only)"
				% [name, "save_state" if has_save else "load_state"])
			continue
		# AN EXEMPTION WITH NO REASON IS NOT AN EXEMPTION. An empty string
		# falls through to `missing`, so `func save_exempt(): return ""`
		# cannot be used to make a subsystem disappear from the count.
		if n.has_method("save_exempt"):
			var why := String(n.save_exempt())
			if why.strip_edges() != "":
				exempt.append("%s (%s)" % [name, why])
				continue
		missing.append(String(name))
	return {"can": can, "missing": missing, "partial": partial,
			"exempt": exempt}


## The snapshot. Never raises on a subsystem that refuses -- a save that dies
## because one shop counter threw is worse than a save with one section absent
## and said so -- but every refusal is recorded in `_failed` inside the snapshot
## itself, so a save file always carries its own honesty.
static func capture(subjects: Dictionary, meta: Dictionary = {}) -> Dictionary:
	var au := audit(subjects)
	var state := {}
	var failed: Array[String] = []
	for name in au["can"]:
		var d = subjects[name].save_state()
		if typeof(d) != TYPE_DICTIONARY:
			failed.append("%s: save_state returned %s, not a Dictionary"
				% [name, type_string(typeof(d))])
			continue
		state[name] = d
	var snap := {
		"_version": VERSION,
		"_state": state,
		"_missing": au["missing"],
		"_partial": au["partial"],
		"_exempt": au["exempt"],
		"_failed": failed,
		"_headline": _headlines(subjects),
	}
	for k in meta:
		snap["_" + String(k)] = meta[k]
	return snap


## WHAT HAPPENED TO YOU, IN THE SNAPSHOT, IN ENGLISH.
##
## THE THIRD METHOD OF THE CONTRACT, AND IT IS OPTIONAL FOR A REASON THE OTHER
## TWO ARE NOT. `save_state`/`load_state` are about a world coming back; this is
## about a PLAYER being told what it is coming back to. Most subsystems have
## nothing to say -- the crowd, the streamer, the ambience -- and a subsystem
## that stays silent is not a gap:
##
##     func save_headline() -> String     # "" when nothing happened to you
##
## SO A SAVE FILE CARRIES ITS OWN SENTENCE, and `describe()` puts it in front of
## the section list. That is not decoration: `main.gd::_front_door` calls
## `describe()` for the CONTINUE blurb, so the front door stops reading
## "save v1: 6 of 6 savable subsystems" and starts reading "REFUSED at customs
## north -- transit withdrawn, 1 conviction". A consequence a player cannot read
## on the way back in is a consequence they have to take the log's word for.
##
## IT IS COLLECTED AT CAPTURE, NOT DERIVED AT READ. Deriving it from `_state`
## would put a second copy of every subsystem's own shape in this file -- the
## defect this repository has paid for three times -- and would go stale the day
## one of them changes a key. Asking the live node is the same duck-typed move
## `audit()` already makes.
static func _headlines(subjects: Dictionary) -> String:
	var names: Array = subjects.keys()
	names.sort()
	var out := PackedStringArray()
	for name in names:
		var n = subjects[name]
		if n == null or not is_instance_valid(n):
			continue
		if not n.has_method("save_headline"):
			continue
		var s := String(n.save_headline()).strip_edges()
		if s != "":
			out.append(s)
	return "; ".join(out)


## The sentence a snapshot carries, or "" when nothing in it had one to give.
static func headline(snap: Dictionary) -> String:
	return String(snap.get("_headline", "")).strip_edges()


## Put a snapshot back. Returns what was applied, what the file carried that
## nothing here wanted, and what is live and had nothing in the file.
##
## THE THIRD LIST IS THE ONE THAT MATTERS. A save written before a subsystem
## learned to save will load without error and leave that subsystem at its boot
## default, which reads exactly like a subsystem that restored correctly to its
## boot value. `absent` names it.
static func restore(subjects: Dictionary, snap: Dictionary) -> Dictionary:
	var state = snap.get("_state", {})
	if typeof(state) != TYPE_DICTIONARY:
		return {"applied": [], "unknown": [], "absent": [],
				"error": "no _state"}
	var applied: Array[String] = []
	var unknown: Array[String] = []
	var absent: Array[String] = []
	var au := audit(subjects)
	for name in state.keys():
		if not subjects.has(name) or subjects[name] == null:
			unknown.append(String(name))
			continue
		if not subjects[name].has_method("load_state"):
			unknown.append(String(name) + " (no load_state)")
			continue
		subjects[name].load_state(state[name])
		applied.append(String(name))
	for name in au["can"]:
		if not state.has(name):
			absent.append(String(name))
	applied.sort()
	unknown.sort()
	absent.sort()
	return {"applied": applied, "unknown": unknown, "absent": absent,
			"error": ""}


static func write(slot: String, snap: Dictionary) -> String:
	DirAccess.make_dir_recursive_absolute(DIR)
	var path := slot_path(slot)
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return "cannot write %s (%d)" % [path, FileAccess.get_open_error()]
	f.store_string(JSON.stringify(snap, " ", true))
	f.close()
	return ""


## CAPTURE AND WRITE, IN ONE CALL, BECAUSE THE TWO-CALL VERSION IS WHAT WENT
## UNCALLED. `main.gd::save_to` already pairs them and is the right caller for a
## save the PLAYER asks for; this exists for the saves nobody asks for -- the one
## the world takes the moment something happens to you. Returns the snapshot with
## `_write_error` set, so a caller that ignores the return value still leaves the
## failure inside the artefact rather than only in a console nobody sees.
static func checkpoint(subjects: Dictionary, slot: String,
		meta: Dictionary = {}) -> Dictionary:
	var snap := capture(subjects, meta)
	var why := write(slot, snap)
	snap["_write_error"] = why
	if why != "":
		push_error("save: " + why)
	return snap


## Delete a slot. THE NEGATIVE CONTROL NEEDS THIS AND NOTHING ELSE DOES.
##
## "Show the world forgetting" is only a control if the second launch starts with
## nothing to find. Withholding the WRITE while a file from an earlier run is
## still on disk produces a run that loads the old save and reports continuity --
## a control that passes for the reason it was written to catch, which is the
## vacuous A/B this project has recorded twice.
static func erase(slot: String) -> bool:
	var path := slot_path(slot)
	if not FileAccess.file_exists(path):
		return false
	return DirAccess.remove_absolute(ProjectSettings.globalize_path(path)) == OK


## Read a slot. Returns {} when there is none -- a first run is not an error.
static func read(slot: String) -> Dictionary:
	var path := slot_path(slot)
	if not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var d = JSON.parse_string(f.get_as_text())
	if typeof(d) != TYPE_DICTIONARY:
		return {}
	# A VERSION FROM THE FUTURE IS REFUSED, NOT COERCED. Loading a newer
	# snapshot into an older build restores the sections it recognises and drops
	# the rest, which is a corrupted world that looks like a working one.
	if int(d.get("_version", 0)) > VERSION:
		push_error("save: %s is version %d, this build reads %d"
			% [path, int(d.get("_version", 0)), VERSION])
		return {}
	return d


## One line naming what a snapshot holds and what it does not.
static func describe(snap: Dictionary) -> String:
	var state = snap.get("_state", {})
	var kept: Array = state.keys() if typeof(state) == TYPE_DICTIONARY else []
	kept.sort()
	# THE DENOMINATOR EXCLUDES THE EXEMPT ONES, and the exempt count is printed
	# beside it rather than folded in. "4 of 4, 5 exempt" and "4 of 9" describe
	# the same build and only the first says whether anything is outstanding.
	# THE SENTENCE FIRST AND THE BOOKKEEPING AFTER. This string is the CONTINUE
	# button's blurb (`main.gd::_front_door` -> `_menu.save_why`), and a player
	# standing at the front door wants to know what happened to them, not how many
	# subsystems implement a duck-typed interface.
	var head := headline(snap)
	var out := ("%s. " % head if head != "" else "")
	out += "save v%d: %d of %d savable subsystems -- %s" % [
		int(snap.get("_version", 0)), kept.size(),
		kept.size() + _len(snap.get("_missing", [])),
		", ".join(PackedStringArray(kept)) if kept.size() > 0 else "nothing",
	]
	var ex = snap.get("_exempt", [])
	if _len(ex) > 0:
		out += "; %d exempt: %s" % [_len(ex), ", ".join(PackedStringArray(ex))]
	var miss = snap.get("_missing", [])
	if _len(miss) > 0:
		out += "; NO save_state AND NO REASON: " + ", ".join(PackedStringArray(miss))
	var part = snap.get("_partial", [])
	if _len(part) > 0:
		out += "; HALF the contract: " + ", ".join(PackedStringArray(part))
	var fail = snap.get("_failed", [])
	if _len(fail) > 0:
		out += "; REFUSED: " + ", ".join(PackedStringArray(fail))
	return out


static func _len(a) -> int:
	return a.size() if typeof(a) == TYPE_ARRAY else 0
