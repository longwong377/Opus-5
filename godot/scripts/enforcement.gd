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

## WHERE THE BRIG IS, AND THE ENGINE COMPUTED NONE OF IT. `enforcement.py::
## brig_address` resolves the register's (sector, ring, deck, angle, z) through
## `interior.place_floor_radius` and `deck.room_half_w_m` and hands over a point
## and a world box in metres. This file does not know that a deck's floor is a
## radius; if it did, that would be a second description of the fact, and the
## two would disagree the first time a ring stack moved.
var _brig: Dictionary = {}
var _cell := 0

## Does this build's `u()` agree with `consequence._u`? Set at `_load` from the
## baked `draw_check` vectors. FALSE MEANS NOTHING IS CHARGED: a hash that is
## subtly wrong produces a fine inside the band and a cell inside the block, so
## it cannot be caught by looking at the number. See `_fine_of`.
var _draw_ok := false


# ===========================================================================
#  THE DRAW -- `consequence._u`, IN THE ENGINE, BECAUSE THE PERSON IS HERE
# ===========================================================================
# WHY THIS EXISTS AT ALL, since this file's whole premise is that it computes
# nothing. Session 4t round 1 baked the fine and the cell as SCALARS, and both
# are `consequence._u` draws keyed on `npc_id`. `interact.gd::_my_purse` loads
# whichever `player:` purse the ledger on disk holds, which is not necessarily
# the purse the bake read -- so the shipped build charged one person's fine to
# another and booked them into a stranger's cell. Measured: 187.66 cr debited
# against a 206.63 cr booking record, in one run, printed on one screen.
#
# The fix cannot be "bake harder", because the person does not exist at bake
# time. So the split is: POLICY IS BAKED (the offence's fine band, the number of
# cells, which goods are restricted, the disposal ladder -- none of which depend
# on who is standing there) and THE DRAW IS TAKEN HERE, off the live `npc_id`,
# with the same hash. This file still holds no rule; it holds the project's
# PRNG, which is a different thing.
#
# `HashingContext` has MD5/SHA1/SHA256 and no blake2b, so it is written out. It
# is a single 128-byte block because every key this draws on is short, and
# `draw_check` proves the result against `consequence._u` at load, on four fixed
# strings, before a credit moves.
const _M32 := 0xFFFFFFFF
const _IV := [0x6a09e667, 0xf3bcc908, 0xbb67ae85, 0x84caa73b,
	0x3c6ef372, 0xfe94f82b, 0xa54ff53a, 0x5f1d36f1,
	0x510e527f, 0xade682d1, 0x9b05688c, 0x2b3e6c1f,
	0x1f83d9ab, 0xfb41bd6b, 0x5be0cd19, 0x137e2179]
const _SIGMA := [
	[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
	[14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
	[11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
	[7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
	[9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
	[2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
	[12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
	[13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
	[6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
	[10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0]]


## Rotate the 64-bit word held as (hi, lo) right by `n`, back into `v` at `i`.
static func _ror(v: Array, i: int, n: int) -> void:
	var hi: int = v[i]
	var lo: int = v[i + 1]
	if n >= 32:
		var t := hi
		hi = lo
		lo = t
		n -= 32
	if n > 0:
		var nh := ((hi >> n) | (lo << (32 - n))) & _M32
		var nl := ((lo >> n) | (hi << (32 - n))) & _M32
		hi = nh
		lo = nl
	v[i] = hi
	v[i + 1] = lo


## v[a] += v[b] (+ optional message word), in 32-bit halves so no addition ever
## touches the sign bit of a Godot int. That is the whole reason for the split
## representation: signed 64-bit overflow is not something to rely on.
static func _add(v: Array, a: int, b: int) -> void:
	var lo: int = v[a + 1] + v[b + 1]
	var hi: int = v[a] + v[b] + (lo >> 32)
	v[a] = hi & _M32
	v[a + 1] = lo & _M32


static func _addw(v: Array, a: int, whi: int, wlo: int) -> void:
	var lo: int = v[a + 1] + wlo
	var hi: int = v[a] + whi + (lo >> 32)
	v[a] = hi & _M32
	v[a + 1] = lo & _M32


static func _xor(v: Array, a: int, b: int) -> void:
	v[a] = v[a] ^ v[b]
	v[a + 1] = v[a + 1] ^ v[b + 1]


static func _g(v: Array, a: int, b: int, c: int, d: int,
		m: Array, x: int, y: int) -> void:
	_add(v, a, b)
	_addw(v, a, m[x * 2], m[x * 2 + 1])
	_xor(v, d, a)
	_ror(v, d, 32)
	_add(v, c, d)
	_xor(v, b, c)
	_ror(v, b, 24)
	_add(v, a, b)
	_addw(v, a, m[y * 2], m[y * 2 + 1])
	_xor(v, d, a)
	_ror(v, d, 16)
	_add(v, c, d)
	_xor(v, b, c)
	_ror(v, b, 63)


## blake2b, digest_size 8, no key, one block -- `consequence._u`'s hash exactly.
## Returns the uniform in [0,1) that `_u` returns: Python reads the 8-byte
## digest BIG-endian, and blake2b serialises h[0] little-endian, so the value is
## the byte-swap of the final h[0].
static func u(parts: Array) -> float:
	var strs := PackedStringArray()
	for p in parts:
		strs.append(str(p))
	var msg := "|".join(strs).to_utf8_buffer()
	if msg.size() > 128:
		push_error("enforcement.u: %d-byte key -- this is the one-block form"
			% msg.size())
		return -1.0
	var h := []
	h.resize(16)
	for i in range(16):
		h[i] = _IV[i]
	h[1] = h[1] ^ 0x01010008          # 0x01010000 | (keylen<<8) | digest_len
	var m := []
	m.resize(32)
	for i in range(16):
		var lo := 0
		var hi := 0
		for b in range(4):
			var j := i * 8 + b
			lo |= (int(msg[j]) if j < msg.size() else 0) << (b * 8)
		for b in range(4):
			var j := i * 8 + 4 + b
			hi |= (int(msg[j]) if j < msg.size() else 0) << (b * 8)
		m[i * 2] = hi & _M32
		m[i * 2 + 1] = lo & _M32
	var v := []
	v.resize(32)
	for i in range(16):
		v[i] = h[i]
		v[16 + i] = _IV[i]
	v[25] = v[25] ^ (msg.size() & _M32)          # t low word, low half
	v[28] = v[28] ^ _M32                         # final block: v[14] = ~v[14]
	v[29] = v[29] ^ _M32
	for r in range(12):
		var s: Array = _SIGMA[r % 10]
		# Word i lives at array index 2i (hi) and 2i+1 (lo), so the eight
		# standard column/diagonal mixes (0,4,8,12) .. (3,4,9,14) are doubled.
		_g(v, 0, 8, 16, 24, m, s[0], s[1])
		_g(v, 2, 10, 18, 26, m, s[2], s[3])
		_g(v, 4, 12, 20, 28, m, s[4], s[5])
		_g(v, 6, 14, 22, 30, m, s[6], s[7])
		_g(v, 0, 10, 20, 30, m, s[8], s[9])
		_g(v, 2, 12, 22, 24, m, s[10], s[11])
		_g(v, 4, 14, 16, 26, m, s[12], s[13])
		_g(v, 6, 8, 18, 28, m, s[14], s[15])
	var f_hi: int = h[0] ^ v[0] ^ v[16]
	var f_lo: int = h[1] ^ v[1] ^ v[17]
	# Byte-swap: Python reads the little-endian serialisation big-endian.
	var s_hi := _bswap(f_lo)
	var s_lo := _bswap(f_hi)
	return (float(s_hi) * 4294967296.0 + float(s_lo)) / 18446744073709551616.0


static func _bswap(x: int) -> int:
	return (((x >> 24) & 0xFF) | (((x >> 16) & 0xFF) << 8)
		| (((x >> 8) & 0xFF) << 16) | ((x & 0xFF) << 24)) & _M32

## What a search FINDS. `economy.GOODS`' own `contraband` class, baked. The
## engine holds no opinion about which goods are illegal.
var _restricted: Array = []
var _demoting := "contraband"

## Which offence THIS stop is. Set at `_open` from what is in the bag, and it
## selects which baked ladder the disposal comes out of -- `detention` (the card
## did not read: grade 1, a citation, `Record.ordinary()` does not count it and
## NOTHING IS TAKEN) or `search` (the bag held contraband: grade 3, and
## `consequence.REVOKE_ON_SERIOUS = 1` withdraws a conditional permission on
## the first one).
##
## THIS IS THE HALF THAT WAS MISSING AND IT IS ONE LINE OF ARITHMETIC. Before
## it, the whole engine path carried `id_check_fail` and nothing else, so the
## build could not demote anybody -- and `enforcement.py --selftest` check 4
## asserted "a refusal at a door never withdraws a permission, at ANY rung",
## which was TRUE and was also the reason. A rule with one of its two rows.
var _offence := ""

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

# -- the progression half: the rung, the cell, the record ------------------
var tier_before := -99
var tier_after := -99
var searched := 0                    ## stops where the bag was the offence
var brig_held := 0                   ## times the player was PUT IN the brig
var brig_in_box := 0                 ## and was inside its own register box
var brig_floor_m := -1.0             ## metres to the floor under them, or -1
var brig_at := Vector3.ZERO
var booking := ""                    ## the readable record, one line
var _return_to := Vector3.ZERO       ## where they were taken from


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
	_brig = d.get("brig_address", {})
	_restricted = d.get("restricted", [])
	_demoting = String(d.get("demoting_offence", "contraband"))
	_check_draw()
	print("enforcement: brig at %s %s ring %d deck %d, %d cells, %d restricted "
		% [String(_brig.get("place", "?")), String(_brig.get("sector", "?")),
			int(_brig.get("ring", -1)), int(_brig.get("deck", -1)),
			int(_brig.get("cells", 0)), _restricted.size()]
		+ "good(s); a search finds `%s`" % _demoting)
	print("enforcement: %d place(s) carry a consequence, for %s (rung %d %s), "
		% [_places.size(), String((d.get("player", {}) as Dictionary).get(
			"name", "?")), int((d.get("player", {}) as Dictionary).get(
			"tier", -99)), String((d.get("player", {}) as Dictionary).get(
			"tier_name", "?"))]
		+ "response %s" % _spread())
	var src: Array = d.get("restricted_from", [])
	var here := 0
	for r in src:
		if bool((r as Dictionary).get("in_boot", false)):
			here += 1
	print("enforcement: a restricted good is sold in %d place(s), %d of them in "
		% [src.size(), here]
		+ "this build's rooms -- %s"
		% ("a player can get one and be searched for it" if here > 0 else
			"so `--arrest-contraband` is the only route into a search. "
			+ "See enforcement.py::restricted_sources"))


## DOES THIS BUILD'S `u()` AGREE WITH `consequence._u`? Four fixed strings with
## known answers, checked before a credit can move. It is checked rather than
## trusted because a wrong hash is invisible in the output: every fine it draws
## is still inside the band and every cell is still inside the block, so the
## only way to see it is to compare against the thing it is supposed to be.
func _check_draw() -> void:
	var vs: Array = _data.get("draw_check", [])
	if vs.is_empty():
		_draw_ok = false
		print("enforcement: NO draw_check in the sidecar -- re-bake with "
			+ "`python3 station/enforcement.py --bake`. Nothing will be charged.")
		return
	var bad := 0
	var worst := 0.0
	for row in vs:
		var r := row as Dictionary
		var got := u(r.get("parts", []))
		var e := absf(got - float(r.get("u", -1.0)))
		worst = maxf(worst, e)
		if not (e < 1e-15):
			bad += 1
	_draw_ok = (bad == 0)
	print("enforcement: draw check %d/%d against consequence._u (worst |d| %.3e)"
		% [vs.size() - bad, vs.size(), worst]
		+ ("" if _draw_ok else " -- FAILED, so nothing will be charged"))


## THIS PERSON'S FINE FOR THIS OFFENCE, drawn here because the person is here.
## `consequence.fine_amount`: `round(lo + (hi-lo) * _u("fine", off, id, seed), 2)`.
## Returns -1.0 rather than 0.0 when it cannot be drawn, so a caller cannot
## mistake "no fine is due" for "I could not work out the fine".
func _fine_of(offence: String) -> float:
	if not _draw_ok or _player == null:
		return -1.0
	var row = (_data.get("offence", {}) as Dictionary).get(offence, null)
	if typeof(row) != TYPE_DICTIONARY:
		return -1.0
	var lo := float((row as Dictionary).get("fine_lo", 0.0))
	var hi := float((row as Dictionary).get("fine_hi", 0.0))
	if hi <= 0.0:
		return 0.0
	var nid := String(_player.get("npc_id"))
	if nid == "":
		return -1.0
	return snappedf(lo + (hi - lo) * u(["fine", offence, nid, _seed()]), 0.01)


## WHICH CELL THIS BOOKING GOES INTO. `enforcement.py::brig_cell` --
## `1 + int(_u("brig_cell", npc_id, day, seed) * BRIG_CELLS)`, keyed on the two
## things a booking is identified by. Derived here for the same reason the fine
## is: it is a draw on the person, and the person is not known at bake time.
func _cell_of() -> int:
	if not _draw_ok or _player == null:
		return 0
	var cells := int(_data.get("brig_cells", _brig.get("cells", 0)))
	var nid := String(_player.get("npc_id"))
	if cells <= 0 or nid == "":
		return 0
	return 1 + int(u(["brig_cell", nid, _day(), _seed()]) * float(cells))


func _seed() -> String:
	return String(_data.get("seed", "b5"))


## THE DAY THE BOOKING IS RECORDED ON, and it must be the LEDGER's day, not the
## sidecar's. `interact.gd::convict` writes `"day %d: ..."` into the record from
## `_led.day`, and `enforcement.py::bookings` reads that note back to recover
## the day it re-derives the cell from. If this read the bake day the two would
## name different cells for one booking, which is the defect this whole section
## exists to close, arriving by a different door.
func _day() -> int:
	if _interact != null:
		var led = _interact.get("_led")
		if typeof(led) == TYPE_DICTIONARY and (led as Dictionary).has("day"):
			return int((led as Dictionary)["day"])
	return int(_data.get("day", 1))


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
## TWO THINGS CAN OPEN A STOP, AND THEY ARE DIFFERENT RULES ON PURPOSE.
##
##   THE CARD. `hud.gd::_boundary` refuses you and this reacts to the sentence,
##   exactly as before. A second evaluation of "does this place admit me" here
##   would be the duplication that made two halves of one crowd disagree about
##   which way round a person is.
##
##   THE BAG. A place that READS A CARD is a place that searches, and what a
##   customs line finds in a bag is not a fact about the card -- an accepted
##   card and a bag full of Dust is the ordinary shape of THE-GAME section 4's
##   Broker shortcut, and it is the only stop on this deck that a tier-2 player
##   can meet, because `arrival_concourse` needs exactly rung 2 and therefore
##   ADMITS them. Without this trigger the demotion path is unreachable by the
##   only card that has anything to lose, which is the same defect as machinery
##   with no caller, one level up.
func _watch() -> void:
	var txt := String(_hud.get("check_text"))
	var here := String(_hud.get("_check_place"))
	if not txt.begins_with("IDENTICARD"):
		if state == DONE and here == "":
			state = IDLE               # stepped back into the corridor: re-armed
		return
	if here == "" or not _places.has(here):
		return
	if state == DONE and here == _place:
		return
	var found := _contraband()
	if not txt.begins_with("IDENTICARD REFUSED") and found == "":
		return
	if not bool((_places[here] as Dictionary).get("reads_card", false)) \
			and found != "":
		return                          # nobody searches you in a corridor
	_open(here, found)


## A DEFECT FOUND BY RUNNING IT, AND IT MADE THIS WHOLE GATE UNRUNNABLE ON A
## BUILD WITH GEOMETRY. Every place lookup in this file read `hud.gd::_boxes`
## -- and `hud.gd::bind` fills `_boxes` from the interact sidecar ONLY IF
## `_place_boxes` (the real mesh extents, via `places.gd::boxes`) came back
## empty. So on any build where the deck geometry loads, `_boxes` is `{}`,
## `_pick()` returns "", and the run prints
##
##     ARREST gate=FAIL -- nothing on this deck refuses a tier-0 card
##
## which is a sentence about the CARD and sent the reader to the wrong half of
## the system entirely. The gate could only ever pass on a build whose places
## had no meshes. That is the ninth-instance defect one level down: a caller
## that exists, runs, and reads the branch that is not taken.
##
## The two are different SHAPES -- `_place_boxes` is key -> AABB and `_boxes` is
## key -> [lo, hi] -- so this normalises rather than picking one, and prefers
## the geometry for the same reason `hud.gd` does: a room is bigger than its
## furniture, and the two disagreed by 31.6 m when that was tested.
func _box_of(key: String) -> Array:
	var pb = _hud.get("_place_boxes")
	if typeof(pb) == TYPE_DICTIONARY and (pb as Dictionary).has(key):
		var a: AABB = (pb as Dictionary)[key]
		return [a.position, a.position + a.size]
	var b = _hud.get("_boxes")
	if typeof(b) == TYPE_DICTIONARY and (b as Dictionary).has(key):
		return (b as Dictionary)[key]
	return []


func _has_box(key: String) -> bool:
	return not _box_of(key).is_empty()


## What is in the bag that the baked list calls contraband, or "".
func _contraband() -> String:
	if _player == null or _restricted.is_empty():
		return ""
	if _args().has("enforce-no-contraband"):
		return ""
	var bag = _player.get("carrying")
	if typeof(bag) != TYPE_ARRAY and typeof(bag) != TYPE_PACKED_STRING_ARRAY:
		return ""
	for item in bag:
		for bad in _restricted:
			if String(item) == String(bad):
				return String(item)
	return ""


func _open(key: String, found: String = "") -> void:
	_place = key
	_row = _places[key]
	_offence = (_demoting if found != ""
		else String((_row.get("detention", {}) as Dictionary).get("offence",
			"id_check_fail")))
	if found != "":
		searched += 1
		print("ARREST searched at %s -- `%s` in the bag: this is a %s docket, "
			% [key, found, _demoting]
			+ "not a citation (grade %d)"
			% int((_data.get("offence", {}) as Dictionary).get(
				_demoting, {}).get("grade", 0)))
	refused += 1
	var n := int(_stops.get(key, 0))
	_stops[key] = n + 1
	_wait_s = float(_row.get("respond_s", 0.0)) / rate
	_t = 0.0
	state = CALLED
	var who := _pair()
	print("ARREST %s at %s -- %s notified, %.0f s away (%s)"
		% [("stopped" if found != "" else "refused"), key, who,
			float(_row.get("respond_s", 0.0)),
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
	var b := _box_of(_place)
	var p: Vector3 = _player.global_position
	if b.is_empty():
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
	# A SEARCH THAT FINDS SOMETHING IS NOT A COIN TOSS. `DETAIN_ON_FAIL` prices
	# rung 3 -- "move on, no arrest, no record" -- for a card that did not read.
	# Nobody is waved through a customs line with Dust in their bag, and
	# `consequence.arrest` has no branch that would: grade 3 goes to the brig.
	if _offence == _demoting:
		will = true
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
	tier_before = int(_player.get("tier"))
	hour_before = (float(_clock.call("hour")) if _clock != null else -1.0)
	state = CUSTODY
	_say("DETAINED\n%s" % String(_legs[0]).to_upper())


## The custody chain as lines, straight off the baked table. Every duration in
## it was routed by `consequence.arrest` on the graph a resident commutes on;
## nothing here adds anything up except the hour index, which is the one leg
## that moves with the clock.
## WHICH BAKED LADDER THIS STOP COMES OUT OF. `detention` is the card; `search`
## is the bag. The hold is NOT duplicated between them -- only the disposal
## differs by offence, so `hold_s_h`/`total_s_h` are read from `detention` in
## both branches, which is `enforcement.py`'s own note on the key.
func _branch() -> Dictionary:
	if _offence == _demoting and _row.has("search"):
		return _row.get("search", {})
	return _row.get("detention", {})


## The leg at which the player is actually PUT IN THE BRIG, by index into the
## list `_chain()` returns. Named rather than counted at the call site, because
## a magic 1 in `_custody` would silently move if a line were inserted.
const BRIG_LEG := 1
const RELEASE_LEG := 6


func _chain() -> Array:
	var d: Dictionary = _branch()
	var hold_src: Dictionary = _row.get("detention", {})
	var legs: Dictionary = d.get("legs", {})
	var h := 13
	if _clock != null:
		h = int(floor(fposmod(float(_clock.call("hour")), 24.0)))
	var hold: Array = hold_src.get("hold_s_h", [])
	var hold_s := (float(hold[h]) if h < hold.size() else 0.0)
	var total: Array = hold_src.get("total_s_h", [])
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
		"BOOKED IN CELL %02d OF %d -- %s, %.0f min"
			% [_cell_of(), int(_brig.get("cells", 0)),
				String(d.get("offence", "")).to_upper().replace("_", " "),
				float(legs.get("booking_s", 0.0)) / 60.0],
		"HELD TO THE NEXT OMBUDS SITTING -- %.1f h" % (hold_s / 3600.0),
		"OMBUDS COURT -- %s" % String(c.get("reason", "")).left(64),
		"FINE %.2f CR -- %s" % [maxf(_fine_of(String(d.get("offence", ""))), 0.0),
			String(c.get("disposal", "")).to_upper()],
		"RELEASED -- %.1f h in custody, %s" % [total_s / 3600.0, card],
	]


# ---------------------------------------------------------------------------
#  THE BRIG, AS A PLACE THE PLAYER IS IN
# ---------------------------------------------------------------------------
## THE LIMIT THIS CLOSES IS IN THE FILE THAT SHIPPED IT. `_settle`'s own comment
## read: "Released into the corridor, because the brig is a real place in the
## register and it is 6 km and four decks from this one -- teleporting a body
## into a cell that has not streamed drops it through the world. The escort is
## reported in minutes and not walked, which is a real limit and is printed
## rather than hidden."
##
## Printing a limit is better than hiding one and it is still a caption. A hold
## you are TOLD about is the same thing as a refusal you can walk away from.
##
## SO THE BODY GOES, AND THE HONESTY IS MOVED FROM THE PROSE INTO A MEASUREMENT.
## The player is placed at the brig's own address -- `enforcement.py::
## brig_address`'s `stand`, which is `collision.stand_at`'s formula, so it is
## the point that module would have stood a body at -- and TWO separate things
## are then reported, because they are two separate claims and only one of them
## is always available:
##
##   `in_box`  the player's world position is inside the brig's own register
##             box. This is checkable with NO DECK BUILT, and it is the claim
##             "they are at the brig" in the only terms the register has.
##   `floor`   a ray finds collision under them. This is the claim "they are
##             STANDING in it", and it can only be true when red/2/1 has been
##             baked and streamed. When it is false the run says so, in those
##             words, and does not pretend.
##
## A gate that reported one number for both would be the tool-that-silently-
## degrades defect this project has already paid a session for.
func _to_brig() -> void:
	if _player == null or _brig.is_empty():
		return
	_return_to = _player.global_position
	var stand: Array = _brig.get("stand", [])
	if stand.size() < 3:
		return
	brig_at = Vector3(float(stand[0]), float(stand[1]), float(stand[2]))
	_player.global_position = brig_at
	_player.set("velocity", Vector3.ZERO)
	brig_held += 1
	var inside := _in_brig_box(brig_at)
	if inside:
		brig_in_box += 1
	brig_floor_m = _floor_under(brig_at)
	_cell = _cell_of()
	print("ARREST brig HELD at %s cell %02d of %d -- (%.1f, %.1f, %.1f), "
		% [String(_brig.get("place", "brig")), _cell,
			int(_brig.get("cells", 0)), brig_at.x, brig_at.y, brig_at.z]
		+ "%s %s ring %d deck %d %.0f deg z %.0f, in_box=%s, floor=%s"
		% [String(_brig.get("name", "")), String(_brig.get("sector", "?")),
			int(_brig.get("ring", -1)), int(_brig.get("deck", -1)),
			float(_brig.get("angle_deg", 0.0)), float(_brig.get("z_m", 0.0)),
			("yes" if inside else "NO"),
			("%.2f m" % brig_floor_m if brig_floor_m >= 0.0
				else "NONE -- red/2/1 is not built in this container, so the "
					+ "hold is an ADDRESS and not a floor")])


## Put back where they were taken from, then walked out of the room by the
## normal rung-3 exit. The brig is not a scene this build can leave on foot.
func _from_brig() -> void:
	if _player == null or _return_to == Vector3.ZERO:
		return
	_player.global_position = _return_to
	_player.set("velocity", Vector3.ZERO)
	_return_to = Vector3.ZERO


func _in_brig_box(p: Vector3) -> bool:
	var b = _brig.get("box")
	if typeof(b) != TYPE_ARRAY or (b as Array).size() < 2:
		return false
	var lo: Array = (b as Array)[0]
	var hi: Array = (b as Array)[1]
	for i in 3:
		if p[i] < float(lo[i]) - 0.01 or p[i] > float(hi[i]) + 0.01:
			return false
	return true


## Metres to the collision under a point, or -1.0 if there is none. Cast along
## the DECK'S OWN DOWN, which at r=157 m on a habitat ring is inward along the
## radius and is not -Y; a -Y cast at the brig would miss a floor that was
## there and report the limit for the wrong reason.
func _floor_under(p: Vector3) -> float:
	var down := Vector3(p.x, p.y, 0.0)
	if down.length() < 1.0:
		down = Vector3(0, -1, 0)
	down = -down.normalized()
	var space := get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(p - down * 2.0, p + down * 6.0)
	q.collision_mask = 1
	if _player != null:
		q.exclude = [_player.get_rid()]
	var hit := space.intersect_ray(q)
	if hit.is_empty():
		return -1.0
	return (p - down * 2.0).distance_to(hit["position"]) - 2.0


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
	var d: Dictionary = _branch()
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
	# HELD MEANS HELD. Between the escort leg and the release leg the body is
	# re-asserted at the cell every physics frame. Without it a player put at an
	# address with no floor under it falls for the length of the hold and is
	# somewhere else by the court leg -- which would make "you were in the brig"
	# true for one frame and false for the rest, which is the same as false.
	if _leg >= BRIG_LEG and _leg < RELEASE_LEG and _return_to != Vector3.ZERO:
		_player.global_position = brig_at
		_player.set("velocity", Vector3.ZERO)
	_t += delta * rate
	if _t < LEG_DWELL_S:
		return
	_t = 0.0
	_leg += 1
	if _leg == BRIG_LEG:
		_to_brig()
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
	var d: Dictionary = _branch()
	var legs: Dictionary = d.get("legs", {})
	var h := 13
	if _clock != null:
		h = int(floor(fposmod(float(_clock.call("hour")), 24.0)))
	var total: Array = (_row.get("detention", {}) as Dictionary).get(
		"total_s_h", [])
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

	# 2. THE MONEY, and it is THIS PERSON'S money -- see `_fine_of`. The sidecar
	#    carries the band; the point inside it is drawn here off the live
	#    `npc_id`, because `interact.gd::_my_purse` may well have loaded somebody
	#    the bake never saw. A negative comes back when the draw could not be
	#    made at all, and that is refused loudly rather than charged as zero.
	var offence := String(d.get("offence", ""))
	var fine := _fine_of(offence)
	if fine < 0.0:
		push_error("enforcement: no fine could be drawn for `%s` -- draw_ok=%s. "
			% [offence, _draw_ok] + "NOTHING CHARGED, NOTHING RECORDED.")
		print("ARREST fine UNPRICED for `%s` -- the sidecar carries no band or "
			% offence + "the draw check failed. Re-bake enforcement.json.")
		fine = 0.0
	if _interact != null and _interact.has_method("fine") and fine > 0.0:
		var paid: bool = _interact.call("fine", fine,
			String(_data.get("court", "law_courts")), offence)
		print("ARREST fine %.2f cr %s -- %.2f cr left"
			% [fine, ("paid" if paid else "OUTSTANDING"),
				float(_player.get("credits"))])
	credits_after = float(_player.get("credits"))

	# 3. THE RECORD AND THE RUNG. Written into the purse, so it survives.
	if _interact != null and _interact.has_method("convict"):
		_interact.call("convict", offence, fine,
			bool(c.get("revoked", false)), int(c.get("tier_after", -99)),
			String(c.get("tier_after_name", "")))
	last_line = String(c.get("disposal", ""))
	last_why = String(c.get("reason", ""))
	tier_after = int(_player.get("tier"))
	if tier_after < tier_before:
		print("ARREST DEMOTED %d (%s) -> %d (%s) -- %s"
			% [tier_before, String(c.get("tier_before_name", "")), tier_after,
				String(_player.get("tier_name")),
				String(c.get("reason", "")).left(64)])
	else:
		print("ARREST tier %d STANDS -- %s"
			% [tier_after, String(c.get("reason", "")).left(72)])

	# 3b. AND IT IS READABLE. The booking is not stored: `enforcement.py::
	#     bookings` recomputes it from the purse the line above just wrote, and
	#     this is that record's one-line form, printed where a gate can read it.
	_cell = _cell_of()
	booking = ("%s, %s, cell %02d of %d, %.2f cr, %s"
		% [String(_player.get("person")),
			offence, _cell,
			int(_brig.get("cells", 0)), fine,
			("%s WITHDRAWN" % String(c.get("tier_before_name", "")).to_upper()
				if bool(c.get("revoked", false)) else "card endorsed")])
	print("ARREST booking -- %s" % booking)

	# 4. AND YOU ARE NOT WHERE YOU WERE. Brought back from the cell to the room
	#    the arrest happened in, then walked out of it by the ordinary exit --
	#    the point the ray that placed the officer already proved clear.
	_from_brig()
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
	var b := _box_of(_place)
	var dir := _out_dir()
	var p: Vector3 = _player.global_position
	var want := APPROACH_MAX_M
	if not b.is_empty():
		var lo: Vector3 = b[0]
		var hi: Vector3 = b[1]
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
		+ "searched=%d brig=%d/%d tier=%d->%d " % [searched, brig_in_box,
			brig_held, tier_before, tier_after]
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
var _gate_tier0 := -99

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
		_player.set("tier_name", String((_data.get("tiers", {}) as Dictionary)
			.get(str(t), "forced_%d" % t)))
		print("ARREST control: the card now reads tier %d (%s)"
			% [t, String(_player.get("tier_name"))])
	# THE BAG, AND IT IS `player.gd::take` AND NOT A FIELD POKE. That is the
	# same call `interact.gd` makes when a player picks something up, so the
	# gate exercises the state a played session would actually be in -- and it
	# respects `bag_full()`, so a gate cannot smuggle a good past the carry cap
	# the game enforces.
	if _args().has("arrest-contraband") and not _restricted.is_empty():
		var good := String(_restricted[0])
		var got: bool = _player.call("take", good)
		print("ARREST bag: took `%s` -> %s (carrying %s)"
			% [good, ("yes" if got else "REFUSED -- bag full"),
				", ".join(_player.get("carrying"))])
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
	# THE RUNG THE RUN STARTED ON, held separately from `tier_before`, which is
	# per-arrest. A three-visit gate demotes on visit one and then arrests a
	# person with nothing left to take, so comparing the LAST arrest's before
	# and after would report "no demotion" on a run that demoted.
	_gate_tier0 = int(_player.get("tier"))
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
	var best := ""
	var carrying := _contraband() != ""
	for k in _places:
		var r: Dictionary = _places[k]
		# CARRYING CHANGES WHICH PLACES CAN STOP YOU, and that is the point of
		# the second trigger rather than a loosening of the first. With a clean
		# bag only a place that REFUSES the card can open a stop. With Dust in
		# it, any place that READS a card searches -- including the one that
		# just admitted you, which on this deck is the only place a rung-2 card
		# can meet at all.
		if carrying:
			if not bool(r.get("reads_card", false)):
				continue
		elif tier >= int(r.get("need", 0)):
			continue
		if not _has_box(String(k)):
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
	var b: Array = _box_of(_gate_k)
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
	# THE PROGRESSION HALF, and it is only asserted when the run was ASKED for
	# it. `--arrest-contraband` is what puts something in the bag; without it
	# the only offence available is grade 1 and `Record.ordinary()` correctly
	# takes nothing, so demanding a demotion on a clean-bag run would be a gate
	# that fails for the right behaviour.
	var want_demote := _args().has("arrest-contraband") \
		and not _args().has("enforce-no-contraband")
	var demoted := (tier_after >= 0 and _gate_tier0 > -99
		and tier_after < _gate_tier0)
	if want_demote:
		ok = ok and searched > 0 and demoted and booking != "" \
			and brig_in_box > 0
	print(("ARREST gate=%s refused=%d responded=%d arrived=%d moved_on=%d "
		+ "detained=%d searched=%d brig=%d/%d floor=%.2f tier=%d->%d "
		+ "walked=%.1fm cr=-%.2f clock=+%.1fh out=%.1fm rate=x%.0f "
		+ "place=%s") % [
		("PASS" if ok else "FAIL"), refused, responded, arrived, moved_on,
		detained, searched, brig_in_box, brig_held, brig_floor_m, _gate_tier0,
		tier_after, _gate_walked, dcr, dh, moved, rate, _gate_k])
	if booking != "":
		print("ARREST record -- %s" % booking)
	get_tree().quit(0 if ok else 1)
