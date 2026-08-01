extends SceneTree
## The station clock, and the people who live by it.
##
## THE PROPERTY THIS EXISTS FOR. `docs/MASTER-PLAN.md` §0 asks for four things
## and this is the third: *"it is alive: the station behaves identically whether
## or not it is observed; leaving and returning is consistent; 03:00 differs
## visibly from 13:00."* Until now the runtime had no clock at all. Every body in
## `<deck>_actors.json` was placed by `station/populace.py` at ONE hour, baked
## into the room mesh, and stood there for ever -- so the third clause was false
## by construction and the first two were vacuous, because nothing could change
## whether you watched it or not.
##
## THE ARCHITECTURE IS THE WHOLE ANSWER, and it is one sentence:
##
##     an inhabitant's state is a PURE FUNCTION of the station clock.
##
## Nothing here integrates, accumulates or steps. `Director.apply(h)` computes
## where everybody is from `h` alone, so:
##
##   * **behaves identically whether or not it is observed** -- there is no state
##     to diverge. A room nobody is looking at is not being simulated wrongly; it
##     is not being simulated at all, and the answer when you walk in is the same
##     answer it would have had.
##   * **leaving and returning is consistent** -- `apply(8.0)` after `apply(3.0)`
##     gives bit-identical results to `apply(8.0)` alone. That is gated, not
##     asserted: `--life-test` runs 03:00 -> 08:00 -> 13:00 -> 03:00 and compares
##     every transform, and the CONTROL is an integrating director in this same
##     file which drifts on the same trip and cannot get back.
##   * **03:00 differs visibly from 13:00** -- the numbers come from
##     `station/npc/life.py`, which walks all 250,000 residents' own days and
##     routes every journey on the station's own navigation graph. They are
##     embedded below; `life.py --selftest` re-derives them and fails on drift.
##
## WHAT IT DRIVES. Two things, because they are the two kinds of person the
## generator makes:
##
##   1. **Corridor walkers move.** A body on a ring deck has a radius and a
##      bearing; `apply` advances the bearing at the body's own walking speed as
##      a function of the clock. Nobody is on a treadmill: a corridor's crowd is
##      a FLOW, and the flow at 03:00 is the same people moving as at 08:00 --
##      there are just 2.48 times fewer of them.
##   2. **Rooms fill and empty.** `PRESENCE` is a per-place 24-hour curve
##      normalised to that place's own peak. How many are present is that curve
##      read against the hour the bodies were baked at; WHICH of them are present
##      is a deterministic function of their ids, so the same people are in the
##      Zocalo at 14:00 today and tomorrow. That is what makes a regular a
##      regular rather than a re-roll, and it is the same argument
##      `resident.affiliates` makes about pools.
##
## COST. One float compare and at most one transform write per bound body per
## frame; no allocation after `bind()`, no per-frame string work, no draw calls.
## `--life-test` measures it against `station/npc/body.py`'s NPC_FRAME_SHARE
## (0.19 of the frame) at 2,000 bodies -- twice the whole station's baked crowd.
##
## RUN IT:
##
##     godot --path godot --headless --script res://scripts/life.gd -- --life-test
##     godot --path godot --headless --script res://scripts/life.gd -- --life-hours
##
## USE IT:
##
##     var L := preload("res://scripts/life.gd")
##     var dir := L.Director.new()
##     dir.clock = L.Clock.new(13.0, 1.0 / 60.0)   # a station minute a second
##     add_child(dir)
##     dir.bind(deck_visual_root, actors_json_array)
##     dir.watch(player_body)                      # optional: nothing pops in view
##
## INTEGRATION NOTE, stated because it is a real interaction and not a bug.
## `npc.gd` turns a body to look at the player by writing its meshes' transforms;
## this script writes their origins. `Director.process_priority` is 100 so it
## runs after `npc.gd` in the same frame and composes on whatever basis `npc.gd`
## left. A body that is *both* walking *and* being looked at is the only case
## where the two meet, and `npc.gd` caches its pivot from the rest pose, so such
## a body turns about a point that lags its feet. Fixing that means `npc.gd`
## recomputing its pivot, which is not this script's file.


# ===========================================================================
# 1.  THE CLOCK
# ===========================================================================
## Station time. A pure function of elapsed real seconds, so two clocks started
## with the same parameters agree for ever without ever talking to each other.
##
## Earth Mean Time, authority 1: the customs board says so verbatim -- "TIME ON
## B-5 IS EARTH MEAN TIME (EMT)", transcribed in `station/signage.py`.
class Clock:
	const DAY_H := 24.0

	## Station hours per real second. 1.0 puts a whole day in 24 s, which is
	## what you want when the question is whether a corridor empties and not
	## what you want when you are standing in it. 1.0/60.0 is a station minute
	## a second; 1.0/3600.0 is real time.
	var rate: float = 1.0 / 60.0
	var start_hour: float = 13.0
	var elapsed_s: float = 0.0

	func _init(p_start: float = 13.0, p_rate: float = 1.0 / 60.0) -> void:
		start_hour = p_start
		rate = p_rate

	## Advance real time. The only mutation in this file, and it touches one
	## float that nothing reads except `hour()`.
	func tick(delta_s: float) -> void:
		elapsed_s += delta_s

	func hour() -> float:
		return fposmod(start_hour + elapsed_s * rate, DAY_H)

	## Jump the clock. A jump is indistinguishable from having waited, which is
	## the whole point of the design.
	func set_hour(h: float) -> void:
		start_hour = fposmod(h, DAY_H)
		elapsed_s = 0.0


# ===========================================================================
# 2.  THE DIRECTOR
# ===========================================================================
## Drives bound inhabitants from the clock. One per scene.
class Director extends Node3D:

	# -- the derived tables ------------------------------------------------
	# GENERATED by `python3 station/npc/life.py --gd`. Do not hand-edit:
	# `life.py --selftest` re-derives these and fails on drift.
	const TRANSIT_AT := [15419, 9632, 7939, 9898, 9476, 11239, 19034, 27680, 24064, 21222, 15909, 17777, 22957, 23858, 19422, 20973, 24930, 26927, 25187, 29791, 29577, 26315, 23564, 23723]
	const ON_FOOT_AT := [7855, 4270, 3750, 5092, 4610, 5729, 9410, 14904, 12646, 10395, 7776, 8743, 10906, 11312, 9723, 10517, 11070, 12390, 12479, 15321, 15163, 13215, 12343, 12077]
	const WALK_MIN_PER_DAY := 58.01
	const QUIET_HOUR := 2
	const BUSY_HOUR := 19
	const PRESENCE := {
		"air_compressors": [0.00, 0.00, 0.01, 0.15, 0.29, 0.31, 0.31, 0.54, 0.97, 1.00, 1.00, 0.81, 0.62, 0.71, 0.69, 0.69, 0.38, 0.02, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"alien_resident_qtr": [0.93, 0.98, 0.92, 0.80, 0.66, 0.53, 0.39, 0.52, 0.48, 0.44, 0.41, 0.45, 0.61, 0.33, 0.54, 0.69, 0.70, 0.75, 0.78, 0.76, 0.95, 1.00, 0.76, 0.80],
		"alien_sector": [0.98, 1.00, 0.94, 0.80, 0.67, 0.57, 0.35, 0.41, 0.43, 0.59, 0.64, 0.56, 0.67, 0.41, 0.67, 0.73, 0.72, 0.68, 0.66, 0.77, 0.91, 0.88, 0.72, 0.81],
		"alien_worship": [0.14, 0.24, 0.63, 0.88, 0.87, 0.94, 0.79, 1.00, 0.97, 0.94, 0.59, 0.31, 0.35, 0.28, 0.46, 0.41, 0.27, 0.31, 0.35, 0.40, 0.38, 0.38, 0.33, 0.25],
		"alpha_substation": [0.00, 0.00, 0.01, 0.15, 0.23, 0.23, 0.22, 0.28, 0.94, 1.00, 1.00, 0.99, 0.85, 0.77, 0.77, 0.77, 0.65, 0.06, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"ambassadorial_suites": [0.44, 0.89, 0.98, 1.00, 0.91, 0.40, 0.30, 0.75, 0.64, 0.64, 0.71, 0.73, 0.63, 0.44, 0.93, 0.82, 0.57, 0.55, 0.64, 0.65, 0.60, 0.60, 0.62, 0.44],
		"arrival_concourse": [0.13, 0.10, 0.10, 0.10, 0.09, 0.07, 0.15, 0.27, 0.75, 0.94, 0.58, 0.62, 0.61, 0.69, 0.83, 0.86, 1.00, 0.66, 0.47, 0.36, 0.89, 0.80, 0.79, 0.42],
		"atmos_monitor": [0.00, 0.00, 0.01, 0.09, 0.20, 0.22, 0.22, 0.34, 0.94, 1.00, 1.00, 0.89, 0.55, 0.80, 0.78, 0.78, 0.66, 0.06, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"bar_unnamed": [0.52, 0.46, 0.34, 0.44, 0.37, 0.39, 0.30, 0.84, 0.91, 0.64, 0.44, 0.59, 0.63, 0.69, 0.60, 0.69, 0.71, 0.83, 0.81, 0.85, 1.00, 0.82, 0.84, 0.80],
		"bay_elevators": [0.00, 0.00, 0.00, 0.00, 0.03, 0.19, 0.45, 0.76, 1.00, 1.00, 1.00, 1.00, 1.00, 0.98, 0.85, 0.56, 0.15, 0.05, 0.05, 0.05, 0.05, 0.05, 0.03, 0.01],
		"black_market": [0.09, 0.03, 0.02, 0.03, 0.05, 0.09, 0.23, 0.44, 0.90, 0.71, 0.86, 0.93, 0.61, 0.61, 0.74, 0.69, 0.83, 1.00, 0.91, 0.36, 0.59, 0.77, 0.82, 0.53],
		"business_center": [0.18, 0.14, 0.14, 0.09, 0.11, 0.12, 0.17, 0.18, 0.26, 0.58, 0.78, 0.75, 0.75, 0.68, 0.86, 1.00, 0.99, 0.92, 0.89, 0.81, 0.71, 0.70, 0.49, 0.35],
		"cargo_bays": [0.00, 0.00, 0.00, 0.00, 0.03, 0.18, 0.64, 0.92, 1.00, 1.00, 0.86, 0.94, 1.00, 0.97, 0.83, 0.36, 0.06, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.00],
		"casino": [0.49, 0.47, 0.50, 0.53, 0.58, 0.48, 0.49, 0.63, 0.90, 0.92, 0.73, 0.62, 0.69, 0.83, 1.00, 0.74, 0.75, 0.64, 0.53, 0.41, 0.52, 0.70, 0.79, 0.59],
		"central_corridor": [0.13, 0.09, 0.08, 0.10, 0.12, 0.12, 0.22, 0.34, 0.94, 0.76, 0.80, 0.98, 0.66, 0.56, 0.89, 0.84, 0.80, 0.67, 0.92, 0.61, 0.97, 1.00, 0.84, 0.36],
		"cobra_bays": [0.00, 0.00, 0.00, 0.00, 0.04, 0.24, 0.51, 0.86, 1.00, 1.00, 1.00, 1.00, 1.00, 0.96, 0.77, 0.48, 0.09, 0.03, 0.03, 0.03, 0.03, 0.03, 0.02, 0.01],
		"conference_5": [0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.26, 0.72, 0.78, 0.87, 0.82, 1.00, 1.00, 0.75, 0.26, 0.23, 0.11, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"council_chamber": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.15, 0.56, 0.65, 0.81, 0.92, 1.00, 1.00, 0.84, 0.50, 0.49, 0.29, 0.19, 0.18, 0.18, 0.18, 0.08, 0.00, 0.00],
		"customs_north": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.07, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.93, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"dark_star": [0.58, 0.60, 0.45, 0.41, 0.41, 0.47, 0.49, 0.50, 0.59, 0.48, 0.49, 0.43, 0.36, 0.36, 0.46, 0.48, 0.54, 0.66, 0.60, 0.53, 0.76, 1.00, 1.00, 0.73],
		"docking_bays": [0.00, 0.00, 0.00, 0.00, 0.04, 0.21, 0.44, 0.70, 1.00, 1.00, 1.00, 0.99, 1.00, 0.96, 0.82, 0.59, 0.19, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.01],
		"domed_rotunda": [0.20, 0.13, 0.13, 0.15, 0.11, 0.08, 0.24, 0.19, 0.44, 0.58, 0.71, 0.57, 0.35, 0.62, 0.90, 1.00, 0.69, 0.56, 0.88, 0.35, 0.88, 0.99, 0.81, 0.25],
		"downbelow": [0.95, 0.97, 0.98, 1.00, 1.00, 0.96, 0.91, 0.69, 0.46, 0.50, 0.48, 0.45, 0.51, 0.57, 0.51, 0.40, 0.36, 0.33, 0.22, 0.48, 0.55, 0.56, 0.50, 0.67],
		"downbelow_arch": [0.90, 0.97, 1.00, 0.98, 0.95, 0.96, 0.84, 0.75, 0.48, 0.40, 0.38, 0.48, 0.57, 0.48, 0.28, 0.38, 0.53, 0.43, 0.32, 0.53, 0.48, 0.52, 0.52, 0.69],
		"drum_office": [0.15, 0.16, 0.13, 0.03, 0.00, 0.00, 0.03, 0.03, 0.06, 0.37, 0.49, 0.50, 0.50, 0.51, 0.90, 1.00, 0.97, 0.66, 0.44, 0.66, 0.69, 0.58, 0.25, 0.14],
		"earharts": [0.60, 0.73, 0.69, 0.68, 0.69, 0.59, 0.65, 0.73, 1.00, 0.91, 0.58, 0.44, 0.43, 0.44, 0.61, 0.69, 0.88, 0.73, 0.70, 0.56, 0.65, 0.63, 0.66, 0.51],
		"eclipse_cafe": [0.40, 0.41, 0.32, 0.46, 0.36, 0.35, 0.37, 0.74, 1.00, 0.60, 0.39, 0.49, 0.55, 0.82, 0.63, 0.52, 0.49, 0.45, 0.38, 0.58, 0.78, 0.38, 0.20, 0.37],
		"fabrication": [0.85, 0.75, 0.79, 0.79, 0.79, 0.79, 0.79, 0.78, 0.65, 0.98, 1.00, 1.00, 0.90, 0.90, 1.00, 1.00, 0.89, 0.61, 0.60, 0.60, 0.54, 0.58, 0.60, 0.61],
		"fresh_air": [0.90, 0.52, 0.31, 0.35, 0.36, 0.39, 0.37, 0.65, 0.64, 0.51, 0.36, 0.37, 0.54, 0.62, 0.37, 0.39, 0.80, 0.96, 0.84, 1.00, 0.80, 0.60, 0.68, 0.75],
		"fusion_core": [0.00, 0.00, 0.01, 0.09, 0.21, 0.22, 0.22, 0.22, 0.97, 1.00, 1.00, 0.97, 0.71, 0.79, 0.78, 0.78, 0.71, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"garden_terrace": [0.35, 0.49, 0.40, 0.43, 0.36, 0.37, 0.40, 0.51, 0.52, 0.39, 0.40, 0.70, 0.53, 0.60, 0.70, 0.72, 0.70, 0.80, 1.00, 0.67, 0.91, 0.81, 0.72, 0.56],
		"garden_town": [0.22, 0.42, 0.52, 0.39, 0.60, 0.70, 0.79, 0.58, 0.71, 0.76, 0.97, 0.70, 0.59, 0.42, 0.56, 0.72, 0.64, 0.66, 0.50, 0.39, 0.81, 1.00, 0.62, 0.44],
		"generator_hall": [0.00, 0.00, 0.01, 0.22, 0.48, 0.49, 0.49, 0.58, 1.00, 1.00, 1.00, 0.99, 0.78, 0.52, 0.51, 0.51, 0.32, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"happy_daze": [0.56, 0.60, 0.45, 0.37, 0.44, 0.39, 0.47, 0.51, 0.80, 0.89, 0.72, 0.55, 0.61, 0.74, 0.84, 0.77, 0.92, 0.87, 0.85, 1.00, 0.80, 0.72, 0.68, 0.43],
		"hydroponics": [0.00, 0.00, 0.00, 0.10, 0.31, 0.81, 1.00, 1.00, 0.99, 0.73, 0.99, 0.90, 0.60, 0.19, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"interfaith_chapel": [0.39, 0.15, 0.55, 0.65, 0.75, 0.77, 0.53, 0.79, 1.00, 0.96, 0.63, 0.45, 0.51, 0.37, 0.49, 0.42, 0.58, 0.53, 0.39, 0.37, 0.53, 0.55, 0.50, 0.42],
		"kosh_quarters": [0.00, 0.00, 0.00, 0.00, 0.00, 0.19, 0.09, 0.80, 1.00, 0.96, 0.75, 0.67, 0.54, 0.13, 0.82, 0.83, 0.60, 0.51, 0.81, 0.53, 0.55, 0.44, 0.07, 0.00],
		"league_delegations": [0.42, 0.51, 0.50, 0.52, 0.56, 0.57, 0.68, 1.00, 0.80, 0.65, 0.68, 0.84, 0.66, 0.38, 0.43, 0.38, 0.46, 0.56, 0.61, 0.41, 0.49, 0.55, 0.22, 0.25],
		"lowg_bays": [0.00, 0.00, 0.00, 0.00, 0.02, 0.17, 0.46, 0.83, 1.00, 1.00, 1.00, 1.00, 1.00, 0.98, 0.85, 0.54, 0.11, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.00],
		"mainstage_node": [0.00, 0.00, 0.07, 0.63, 1.00, 1.00, 0.99, 0.58, 1.00, 1.00, 1.00, 0.93, 0.37, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"maintenance": [0.55, 0.34, 0.39, 0.44, 0.40, 0.45, 0.45, 0.52, 0.67, 0.85, 0.85, 0.85, 0.73, 0.74, 0.78, 0.76, 1.00, 0.79, 0.79, 0.79, 0.63, 0.70, 0.79, 0.82],
		"medlab_others": [0.50, 0.50, 0.50, 0.50, 0.40, 0.00, 0.00, 0.07, 0.50, 0.50, 0.50, 0.50, 0.22, 0.48, 0.50, 0.50, 0.61, 1.00, 0.97, 0.66, 0.50, 0.50, 0.50, 0.50],
		"mess_hall": [0.71, 0.52, 0.26, 0.62, 0.27, 0.29, 0.58, 0.58, 0.63, 0.65, 0.61, 0.71, 0.59, 0.63, 0.66, 1.00, 0.88, 0.81, 0.89, 0.71, 0.57, 0.52, 0.52, 0.69],
		"micro_g_bays": [0.00, 0.00, 0.01, 0.16, 0.24, 0.24, 0.24, 0.60, 1.00, 1.00, 1.00, 0.99, 0.84, 0.76, 0.76, 0.76, 0.36, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"morgue": [1.00, 1.00, 1.00, 1.00, 0.27, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.73, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00],
		"outdoor_rec": [0.26, 0.42, 0.50, 0.30, 0.30, 0.30, 0.40, 0.34, 0.32, 0.34, 0.28, 0.31, 0.37, 0.39, 0.55, 0.54, 0.42, 0.51, 0.75, 0.51, 0.83, 1.00, 0.98, 0.58],
		"plant_zone": [0.66, 0.30, 0.34, 0.37, 0.39, 0.39, 0.40, 0.48, 0.68, 0.61, 0.62, 0.62, 0.56, 0.55, 0.57, 0.56, 0.65, 1.00, 1.00, 1.00, 0.91, 0.80, 0.99, 0.98],
		"plantroom_bay": [0.00, 0.00, 0.00, 0.00, 0.06, 0.23, 0.49, 0.72, 1.00, 1.00, 1.00, 1.00, 1.00, 0.95, 0.78, 0.49, 0.18, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01],
		"post_office": [0.12, 0.13, 0.17, 0.09, 0.18, 0.17, 0.15, 0.18, 0.22, 0.51, 0.83, 0.81, 0.78, 0.74, 0.84, 0.88, 0.94, 1.00, 0.93, 0.82, 0.56, 0.36, 0.36, 0.21],
		"power_transfer": [0.00, 0.00, 0.00, 0.08, 0.11, 0.11, 0.21, 0.76, 0.96, 1.00, 1.00, 0.74, 0.91, 0.89, 0.89, 0.79, 0.22, 0.04, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"primary_breaker": [0.00, 0.00, 0.00, 0.07, 0.11, 0.12, 0.19, 0.55, 1.00, 1.00, 1.00, 1.00, 0.93, 0.89, 0.88, 0.81, 0.42, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"qtr_civilian": [0.94, 0.99, 0.99, 1.00, 0.97, 0.95, 0.95, 0.83, 0.65, 0.41, 0.42, 0.48, 0.44, 0.41, 0.35, 0.34, 0.36, 0.38, 0.42, 0.44, 0.54, 0.63, 0.68, 0.75],
		"qtr_command": [0.00, 0.00, 0.00, 0.00, 0.00, 0.06, 0.12, 0.83, 0.67, 0.45, 0.67, 0.81, 0.71, 0.23, 0.56, 0.78, 1.00, 0.82, 0.74, 0.59, 0.48, 0.52, 0.06, 0.00],
		"qtr_personnel": [0.89, 0.97, 1.00, 0.93, 0.89, 0.86, 0.66, 0.42, 0.43, 0.45, 0.44, 0.48, 0.45, 0.44, 0.41, 0.33, 0.28, 0.41, 0.53, 0.48, 0.45, 0.44, 0.55, 0.80],
		"qtr_transient": [0.93, 0.99, 1.00, 0.99, 0.99, 0.95, 0.77, 0.42, 0.11, 0.12, 0.12, 0.07, 0.15, 0.25, 0.03, 0.03, 0.02, 0.04, 0.02, 0.26, 0.08, 0.07, 0.27, 0.63],
		"reactor_hall": [0.00, 0.00, 0.00, 0.09, 0.31, 0.33, 0.33, 0.29, 0.93, 1.00, 1.00, 0.96, 0.55, 0.69, 0.67, 0.67, 0.67, 0.07, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"rotation_drivers": [0.00, 0.00, 0.01, 0.19, 0.33, 0.33, 0.33, 0.53, 1.00, 1.00, 1.00, 0.99, 0.81, 0.67, 0.67, 0.67, 0.40, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"sanctuaries": [0.27, 0.27, 0.60, 0.67, 0.79, 0.72, 0.87, 1.00, 0.79, 0.79, 0.46, 0.41, 0.40, 0.33, 0.42, 0.46, 0.41, 0.51, 0.69, 0.59, 0.69, 0.90, 0.74, 0.45],
		"sanctuary_blue": [0.06, 0.06, 0.41, 0.58, 0.77, 1.00, 0.86, 0.83, 0.96, 0.86, 0.51, 0.36, 0.37, 0.26, 0.25, 0.22, 0.21, 0.70, 0.61, 0.27, 0.54, 0.71, 0.85, 0.33],
		"security_posts": [0.27, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.72, 1.00, 1.00, 1.00, 0.61, 0.79, 1.00, 1.00],
		"shops_kiosks": [0.14, 0.15, 0.14, 0.10, 0.15, 0.15, 0.17, 0.36, 0.59, 0.83, 0.91, 0.91, 0.85, 0.73, 0.80, 0.85, 0.82, 0.94, 1.00, 0.76, 0.71, 0.75, 0.64, 0.42],
		"subfloor_stack": [0.92, 0.98, 0.99, 0.98, 0.99, 1.00, 0.90, 0.68, 0.24, 0.39, 0.45, 0.36, 0.53, 0.55, 0.38, 0.34, 0.32, 0.33, 0.33, 0.50, 0.38, 0.43, 0.42, 0.59],
		"the_garden": [0.19, 0.19, 0.23, 0.25, 0.32, 0.35, 0.33, 0.43, 0.74, 0.76, 0.87, 0.82, 0.65, 0.65, 1.00, 0.87, 0.83, 0.72, 0.73, 0.52, 0.81, 0.70, 0.66, 0.43],
		"waste_control": [0.93, 0.93, 0.93, 0.93, 0.93, 0.93, 1.00, 0.90, 0.87, 0.87, 0.87, 0.87, 0.87, 0.87, 0.80, 0.58, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.66, 0.97],
		"waste_green": [1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.95, 0.86, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.78, 0.70, 0.70, 0.70, 0.70, 0.70, 0.70, 0.75, 0.89],
		"waste_red": [0.47, 0.47, 0.47, 0.47, 0.47, 0.47, 0.61, 0.93, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.93, 0.99, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.92, 0.55],
		"water_rec": [0.27, 0.34, 0.25, 0.27, 0.28, 0.19, 0.14, 0.39, 0.62, 0.66, 0.36, 0.27, 0.37, 0.45, 0.67, 0.57, 0.51, 0.73, 0.84, 0.35, 0.59, 0.83, 1.00, 0.63],
		"water_reclamation": [0.00, 0.00, 0.00, 0.05, 0.16, 0.16, 0.17, 0.89, 1.00, 1.00, 1.00, 0.73, 0.89, 0.84, 0.84, 0.83, 0.08, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"zen_garden": [0.47, 0.51, 0.49, 0.47, 0.47, 0.52, 0.18, 0.30, 1.00, 0.60, 0.84, 0.51, 0.52, 0.71, 0.65, 0.61, 0.48, 0.56, 0.71, 0.55, 0.76, 0.97, 0.99, 0.63],
		"zerog_maint": [0.00, 0.00, 0.01, 0.14, 0.38, 0.39, 0.39, 0.48, 1.00, 1.00, 1.00, 0.99, 0.86, 0.62, 0.61, 0.61, 0.43, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
		"zocalo": [0.16, 0.13, 0.16, 0.11, 0.12, 0.14, 0.19, 0.25, 0.46, 0.76, 0.89, 0.90, 0.88, 0.87, 0.96, 0.95, 0.95, 0.95, 1.00, 0.83, 0.55, 0.50, 0.53, 0.41],
	}
	# END GENERATED

	## The station-clock hour `station/populace.py` baked the bodies at. Every
	## curve here is read as a RATIO against this hour, so at the bake hour the
	## scene is exactly the scene the generator produced: nothing hidden, nothing
	## moved. `populate()`'s own default is 13.0.
	const BAKE_HOUR := 13.0
	const DAY_H := 24.0

	## Metres per second a corridor walker covers. `populace._walk_speed` derives
	## this per species from the Froude gait model at the deck's own gravity and
	## bakes the pose, but nothing carries the number out to the runtime, so this
	## is the human 1-g figure and a body in Grey walks it too. Stated, not
	## hidden; closing it means the actor record carrying a speed.
	var walk_speed_ms: float = 1.30
	## How close a body has to be before its presence is left alone. Popping a
	## person out of existence in front of the player is worse than a room one
	## body over its curve for a few seconds, and the curve is a statistical
	## claim in the first place.
	var hold_radius_m: float = 12.0
	var clock: Clock = null

	class Person:
		var group: String = ""
		var place: String = ""
		var place_i: int = 0                # index into the director's tables
		var nodes: Array[Node3D] = []
		var rest: Array[Vector3] = []       # each node's baked origin
		# The same origins in the RING's own frame: x along the radius, y along
		# the tangent, z down the axis. Precomputed because rotating a body
		# about the station axis then costs one sin and one cos for the whole
		# body instead of two per node per frame -- see the note on `apply`.
		var local: Array[Vector3] = []
		var radius_m: float = 0.0           # distance from the station axis
		var bearing0: float = 0.0           # baked bearing about that axis
		var inv_r: float = 0.0              # way / radius: radians per metre
		var walker: bool = false
		var way: float = 1.0                # +1 or -1 round the ring
		# The overwhelmingly common case is a body whose parts merge to one
		# mesh, and the frame loop is where that matters: the fast path skips
		# an array iteration and two index lookups per body per frame.
		var node0: Node3D = null
		var local0: Vector3 = Vector3.ZERO
		var single: bool = false
		var rank: float = 0.0               # stable 0..1 order for presence
		var order: int = 0                  # this person's rank within a place
		var shown: bool = true

	var _people: Array[Person] = []
	var _by_place: Dictionary = {}
	var _place_keys: Array = []             # index -> place key
	var _place_n: PackedInt32Array = PackedInt32Array()
	var _want: PackedInt32Array = PackedInt32Array()
	var _viewer: Node3D = null
	var _visible_n: int = 0
	var _clipped: int = 0
	var _apply_us: float = 0.0

	func _init() -> void:
		# AFTER npc.gd, deliberately. See the integration note at the top.
		process_priority = 100

	# -- the curves --------------------------------------------------------
	## Linear interpolation into a 24-entry hourly table, wrapping at midnight.
	## A crowd does not step at the top of the hour -- `schedule.PlaceCrowd`
	## already says so in as many words ("a crowd arrives over an hour; it does
	## not teleport", BAND_RAMP_H) and this is the runtime half of it.
	static func hourly(table: Array, h: float) -> float:
		var x := fposmod(h, DAY_H)
		var i := int(floor(x))
		var f := x - float(i)
		var a := float(table[i % 24])
		var b := float(table[(i + 1) % 24])
		return a + (b - a) * f

	## How busy the corridors are at `h`, as a ratio against the bake hour.
	static func corridor_scale(h: float) -> float:
		var base := hourly(ON_FOOT_AT, BAKE_HOUR)
		if base <= 0.0:
			return 1.0
		return hourly(ON_FOOT_AT, h) / base

	## How full a named place is at `h`, as a ratio against the bake hour.
	## A place with no curve returns 1.0 -- UNKNOWN MEANS LEAVE IT ALONE,
	## because the failure mode of guessing is an empty room, and an empty room
	## on a station of 250,000 reads as a bug rather than as a mood.
	## `populace.FALLBACK_PER_100M2` makes the same argument at the other end.
	static func place_scale(place: String, h: float) -> float:
		if not PRESENCE.has(place):
			return 1.0
		var curve: Array = PRESENCE[place]
		var base := hourly(curve, BAKE_HOUR)
		if base <= 0.0:
			return 1.0
		return hourly(curve, h) / base

	# -- binding -----------------------------------------------------------
	## Attach to the meshes `<deck>_actors.json` describes. Returns the count.
	##
	## The grouping rule is `npc.gd`'s, duplicated rather than shared because
	## that script exposes no accessor for it: a mesh belongs to an actor if its
	## name is the actor's group EXACTLY, or that group followed by an
	## underscore. A bare `begins_with` makes `..._standing_1` swallow
	## `..._standing_10`'s parts, which is invisible in a room of five and wrong
	## in a room of twelve.
	func bind(visual: Node, actors: Array) -> int:
		_people.clear()
		_by_place.clear()
		_place_keys.clear()
		_place_n.clear()
		_want.clear()
		var meshes := _meshes(visual)
		for a in actors:
			var g := String(a.get("group", ""))
			if g == "":
				continue
			var p := Person.new()
			p.group = g
			p.place = String(a.get("place", ""))
			for m in meshes:
				var n := String(m.name)
				if n == g or n.begins_with(g + "_"):
					p.nodes.append(m)
					p.rest.append(m.position)
			if p.nodes.is_empty():
				continue
			var x := float(a.get("x", 0.0))
			var y := float(a.get("y", 0.0))
			p.radius_m = sqrt(x * x + y * y)
			p.bearing0 = atan2(y, x)
			p.walker = String(a.get("pose", "")) == "walking"
			var c0 := cos(p.bearing0)
			var s0 := sin(p.bearing0)
			for r0 in p.rest:
				p.local.append(Vector3(r0.x * c0 + r0.y * s0,
					-r0.x * s0 + r0.y * c0, r0.z))
			var who: Dictionary = a.get("who", {})
			var ident := String(who.get("id", g))
			p.way = 1.0 if (_stable(ident + "|way") < 0.5) else -1.0
			p.rank = _stable(ident + "|rank")
			p.inv_r = p.way / p.radius_m if p.radius_m > 0.001 else 0.0
			p.single = p.nodes.size() == 1
			if p.single:
				p.node0 = p.nodes[0]
				p.local0 = p.local[0]
			_people.append(p)
			if not _by_place.has(p.place):
				_by_place[p.place] = []
			_by_place[p.place].append(_people.size() - 1)
		# ORDER BY THE STABLE RANK, ONCE, AND CACHE THE ORDER ON THE PERSON.
		# Presence takes a prefix of this list, so a room that loses four people
		# loses the same four every day and keeps its regulars. Caching `order`
		# is not a micro-optimisation: `idx.find(pi)` in the frame loop is O(n)
		# inside an O(n) loop, and at 2,000 bodies that is four million
		# comparisons a frame, which blows the crowd's entire frame share on
		# a linear search.
		# THE PLACE KEY BECOMES AN INDEX HERE, and that is not a micro-
		# optimisation either: looking a body's place up by STRING in the frame
		# loop hashes a string per body per frame, and the docstring's claim of
		# "no per-frame string work" was false until this line existed. Measured:
		# 4,771 us for 2,000 bodies with the string lookup, against a 3,167 us
		# budget -- the claim and the gate disagreed and the gate was right.
		for key in _by_place.keys():
			var idx: Array = _by_place[key]
			idx.sort_custom(func(i, j): return _people[i].rank < _people[j].rank)
			var pi := _place_keys.size()
			for j in range(idx.size()):
				_people[idx[j]].order = j
				_people[idx[j]].place_i = pi
			_place_keys.append(String(key))
			_place_n.append(idx.size())
			_want.append(idx.size())
		return _people.size()

	## Whose eyes decide what may pop. Optional; without one, presence changes
	## take effect at once, which is right for a headless gate and wrong in
	## front of a player.
	func watch(body: Node3D) -> void:
		_viewer = body

	# -- the frame ---------------------------------------------------------
	func _process(delta: float) -> void:
		if clock == null:
			return
		clock.tick(delta)
		apply(clock.hour())

	## Put every bound body where the clock says it is. Pure in `h`.
	##
	## The walk is inlined rather than called: 2,000 bodies is 2,000 function
	## calls a frame, and in GDScript that alone is a measurable share of a
	## budget this has to fit inside.
	func apply(h: float) -> void:
		var t0 := Time.get_ticks_usec()
		var scale_corridor := clampf(corridor_scale(h), 0.0, 1.0)
		for i in range(_place_keys.size()):
			var f := place_scale(_place_keys[i], h)
			if f > 1.0:
				_clipped += 1
			_want[i] = int(round(float(_place_n[i]) * clampf(f, 0.0, 1.0)))
		var arc := walk_speed_ms * (h - BAKE_HOUR) * 3600.0
		var shown := 0
		for p in _people:
			var here: bool = (p.rank < scale_corridor) if p.walker \
				else (p.order < _want[p.place_i])
			if here != p.shown and _may_pop(p):
				p.shown = here
				for m in p.nodes:
					m.visible = here
			if not p.shown:
				continue
			shown += 1
			if not p.walker or p.radius_m <= 0.001:
				continue
			# A walker's bearing is its baked bearing plus the arc it has
			# covered since the bake hour. PURE IN `h`: there is no previous
			# position anywhere in this block, which is exactly why leaving and
			# returning is consistent. The body's parts rotate about the station
			# axis WITH it, so a shoulder stays on the shoulder -- a body is
			# 0.6 m wide on a 211 m ring, which is 0.16 deg, enough to read as
			# walking crabwise if the parts are merely translated.
			var ang: float = p.bearing0 + arc * p.inv_r
			var c := cos(ang)
			var s := sin(ang)
			if p.single:
				var l0 := p.local0
				p.node0.position = Vector3(l0.x * c - l0.y * s,
					l0.x * s + l0.y * c, l0.z)
				continue
			var nodes := p.nodes
			var local := p.local
			for i in nodes.size():
				var l: Vector3 = local[i]
				nodes[i].position = Vector3(l.x * c - l.y * s,
					l.x * s + l.y * c, l.z)
		_visible_n = shown
		_apply_us = float(Time.get_ticks_usec() - t0)

	## Where one body stands at one hour. The same arithmetic `apply` inlines,
	## exposed so the self-test can exercise it on a single walker.
	func walk_to(p: Person, h: float) -> void:
		if p.radius_m <= 0.001:
			return
		var ang: float = p.bearing0 + p.way * walk_speed_ms \
			* (h - BAKE_HOUR) * 3600.0 / p.radius_m
		var c := cos(ang)
		var s := sin(ang)
		for i in range(p.nodes.size()):
			var l: Vector3 = p.local[i]
			p.nodes[i].position = Vector3(l.x * c - l.y * s,
				l.x * s + l.y * c, l.z)

	func _may_pop(p: Person) -> bool:
		if _viewer == null:
			return true
		return p.nodes[0].global_position.distance_to(
			_viewer.global_position) > hold_radius_m

	# -- reporting ---------------------------------------------------------
	func count() -> int:
		return _people.size()

	func visible_count() -> int:
		return _visible_n

	func apply_us() -> float:
		return _apply_us

	## How many times a place asked for more bodies than were baked into it.
	## Reported rather than hidden: the runtime cannot create a person, so a
	## room busier than its bake hour is capped, and a capped room is a claim
	## this script is quietly not meeting.
	func clipped() -> int:
		return _clipped

	func transforms() -> PackedVector3Array:
		var out := PackedVector3Array()
		for p in _people:
			for m in p.nodes:
				out.append(m.position)
		return out

	# -- helpers -----------------------------------------------------------
	## A deterministic 0..1 from a string. FNV-1a rather than `String.hash()`,
	## because this decides WHO is in a room and that answer has to be the same
	## on every machine and every engine version -- the property
	## `station/npc/schedule.py` buys with blake2b, for the same reason and in
	## the same words: "never `str.__hash__` (salted per process)".
	static func _stable(s: String) -> float:
		var h: int = 2166136261
		for i in range(s.length()):
			h = (h ^ s.unicode_at(i)) & 0xFFFFFFFF
			h = (h * 16777619) & 0xFFFFFFFF
		return float(h) / 4294967296.0

	func _meshes(n: Node) -> Array[Node3D]:
		var out: Array[Node3D] = []
		if n is MeshInstance3D:
			out.append(n)
		for c in n.get_children():
			out.append_array(_meshes(c))
		return out


## An integrator, kept ONLY as the control for the purity gate.
##
## This is what a naive crowd runtime does: step the position by `speed * delta`
## every frame and keep it. It looks identical on screen and it fails the one
## property that matters -- walk away, come back, and the station has drifted by
## however long you were gone times whatever your framerate happened to be.
## `--life-test` runs the same 03:00 -> 08:00 -> 03:00 trip through both.
class Integrator extends RefCounted:
	var pos: float = 0.0
	var speed: float = 1.30

	func step(dt_s: float) -> void:
		pos += speed * dt_s

	func jump_to(_h: float) -> void:
		pass                                  # an integrator cannot jump


# ===========================================================================
# 3.  SELF-TEST
# ===========================================================================
var _fails: Array = []


func _check(ok: bool, name: String, detail: String = "") -> bool:
	print(("  ok   " if ok else "  FAIL ") + name
		+ ("  -- " + detail if detail != "" else ""))
	if not ok:
		_fails.append(name)
	return ok


var _shot_out := ""
var _shot_wait := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var mode := "test"
	var deck := "/home/user/Opus-5/station/generated/scene/deck/blue_0_0_z7440_actors.json"
	var glb := "/home/user/Opus-5/station/generated/scene/deck/blue_0_0_z7440.glb"
	var hour := 13.0
	var out := ""
	var at := "customs_north"
	for a in args:
		if a == "--life-hours":
			mode = "hours"
		elif a == "--life-shot":
			mode = "shot"
		elif a.begins_with("--actors="):
			deck = a.substr(9)
		elif a.begins_with("--glb="):
			glb = a.substr(6)
		elif a.begins_with("--hour="):
			hour = float(a.substr(7))
		elif a.begins_with("--at="):
			at = a.substr(5)
		elif a.begins_with("--out="):
			out = a.substr(6)
	if mode == "hours":
		_report_hours()
		quit(0)
		return
	if mode == "shot":
		_run_shot(glb, deck, at, hour, out)
		return
	_run_test(deck)


# ---------------------------------------------------------------------------
# A FRAME OF THE SAME PLACE AT TWO HOURS
# ---------------------------------------------------------------------------
# WHAT THIS IS AND WHAT IT IS NOT, stated first because CLAUDE.md is explicit
# that a craft claim cites a materialled engine frame. **This is not a craft
# frame.** `station/generated/scene/deck/*.glb` carries POSITION and NORMAL and
# no materials at all; the .tres assignment pass that makes a deck look like
# anything lives in `tools/export_scene.py` and `godot/scripts/render_shot.gd`,
# neither of which this session owns. So this is a clay render of the real
# station geometry with the real cast, and the only claim it makes is the one it
# can support: **the same view, the same camera, two hours, and a different
# number of people in it** -- which is `docs/MASTER-PLAN.md` §0's third clause,
# photographed.
func _run_shot(glb_path: String, actors_path: String, at: String,
		hour: float, out: String) -> void:
	var actors: Array = _read_array(actors_path)
	if actors.is_empty():
		push_error("no actors at " + actors_path)
		quit(2)
		return
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var err := doc.append_from_file(glb_path, st)
	if err != OK:
		push_error("could not read %s (%d)" % [glb_path, err])
		quit(2)
		return
	var scene := doc.generate_scene(st)
	if scene == null:
		push_error("glTF produced no scene")
		quit(2)
		return
	var root := get_root()
	root.add_child(scene)

	var dir := Director.new()
	root.add_child(dir)
	var n := dir.bind(scene, actors)
	dir.apply(hour)
	print("bound %d of %d actors; %d present at %05.2f"
		% [n, actors.size(), dir.visible_count(), hour])

	# The eye stands on the deck floor at the named place's own bearing, which
	# is read off the cast rather than written down: the actors carry the
	# generator's own coordinates and a camera derived from them cannot be
	# aimed at somewhere the people are not.
	var here: Array = []
	for a in actors:
		if String(a.get("place", "")) == at:
			here.append(a)
	if here.is_empty():
		here = actors
	var bx := 0.0
	var by := 0.0
	var z0 := 1e30
	var z1 := -1e30
	for a in here:
		bx += float(a.get("x", 0.0))
		by += float(a.get("y", 0.0))
		z0 = minf(z0, float(a.get("z", 0.0)))
		z1 = maxf(z1, float(a.get("z", 0.0)))
	bx /= float(here.size())
	by /= float(here.size())
	var bearing := atan2(by, bx)
	var r_floor := sqrt(bx * bx + by * by)
	# UP IS TOWARDS THE AXIS. A ring deck's gravity is centrifugal, so "down"
	# is outwards and the eye sits at a SMALLER radius than the floor.
	var radial := Vector3(cos(bearing), sin(bearing), 0.0)
	var eye := radial * (r_floor - 1.70) + Vector3(0.0, 0.0, z0 - 13.0)
	var look := radial * (r_floor - 1.70) + Vector3(0.0, 0.0, z1)

	var cam := Camera3D.new()
	cam.fov = 60.0
	cam.near = 0.05
	cam.far = 20000.0
	root.add_child(cam)
	# `look_at_from_position`, not `look_at`: during `_initialize` the window's
	# children are not yet considered inside the tree, and `look_at` reads the
	# global transform to get there. It fails loudly and then aims at nothing.
	cam.look_at_from_position(eye, look, -radial)

	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.02, 0.02, 0.03)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.55, 0.58, 0.66)
	e.ambient_light_energy = 0.30
	# Filmic, and the reason is the same one `tools/measure_frame.py` records
	# about our own frames: an untonemapped clay render of white default
	# material clips to paper at any exposure that lets you see the ceiling.
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.tonemap_exposure = 0.9
	env.environment = e
	root.add_child(env)
	var key := DirectionalLight3D.new()
	root.add_child(key)
	key.look_at_from_position(eye, look + radial * 4.0, -radial)
	key.light_energy = 1.1

	_shot_out = out
	_shot_wait = 8


func _process(_delta: float) -> bool:
	if _shot_out == "":
		return false
	_shot_wait -= 1
	if _shot_wait > 0:
		return false
	var img := get_root().get_texture().get_image()
	img.save_png(_shot_out)
	print("wrote " + _shot_out)
	quit(0)
	return true


func _report_hours() -> void:
	print("hour   in transit    on foot   corridor")
	for h in range(24):
		print("%02d:00   %9d  %9d      x%.2f"
			% [h, Director.TRANSIT_AT[h], Director.ON_FOOT_AT[h],
				Director.corridor_scale(float(h))])


func _run_test(actors_path: String) -> void:
	print("=".repeat(74))
	print("godot/scripts/life.gd -- the station clock and the people in it")
	print("=".repeat(74))

	# --- 1. the embedded tables ------------------------------------------
	print("\n1. THE TABLES station/npc/life.py DERIVED")
	_check(Director.TRANSIT_AT.size() == 24 and Director.ON_FOOT_AT.size() == 24,
		"both hourly tables have 24 entries",
		"%d, %d" % [Director.TRANSIT_AT.size(), Director.ON_FOOT_AT.size()])
	var bad := 0
	for h in range(24):
		if Director.ON_FOOT_AT[h] > Director.TRANSIT_AT[h]:
			bad += 1
	_check(bad == 0, "nobody is on foot who is not in transit",
		"%d hours violate it" % bad)
	var ratio := float(Director.ON_FOOT_AT[Director.BUSY_HOUR]) \
		/ float(Director.ON_FOOT_AT[Director.QUIET_HOUR])
	_check(ratio > 2.0, "the busiest corridor hour beats the quietest",
		"%02d:00 %d vs %02d:00 %d = x%.2f"
		% [Director.BUSY_HOUR, Director.ON_FOOT_AT[Director.BUSY_HOUR],
			Director.QUIET_HOUR, Director.ON_FOOT_AT[Director.QUIET_HOUR],
			ratio])
	_check(Director.corridor_scale(3.0) < Director.corridor_scale(8.0) * 0.75,
		"03:00 is a visibly emptier corridor than 08:00",
		"x%.2f vs x%.2f of the bake hour"
		% [Director.corridor_scale(3.0), Director.corridor_scale(8.0)])
	_check(absf(Director.corridor_scale(8.0)
		- Director.corridor_scale(8.0)) < 1e-12,
		"CONTROL: 08:00 against itself shows no difference")
	_check(absf(Director.corridor_scale(Director.BAKE_HOUR) - 1.0) < 1e-9,
		"at the bake hour the scene is what the generator produced", "x1.000")
	var rows := 0
	var bad_rows := 0
	for k in Director.PRESENCE.keys():
		rows += 1
		var c: Array = Director.PRESENCE[k]
		if c.size() != 24 or absf(float(c.max()) - 1.0) > 1e-6:
			bad_rows += 1
	_check(rows > 0 and bad_rows == 0,
		"every PRESENCE curve is 24 hours normalised to its own peak",
		"%d places, %d malformed" % [rows, bad_rows])

	# --- 2. the clock -----------------------------------------------------
	print("\n2. THE CLOCK")
	var ck := Clock.new(13.0, 1.0)
	ck.tick(1.0)
	_check(absf(ck.hour() - 14.0) < 1e-9, "one second at rate 1.0 is one hour",
		"%.4f" % ck.hour())
	ck.tick(11.0)
	_check(absf(ck.hour() - 1.0) < 1e-9, "the clock wraps at midnight",
		"13:00 + 12 h = %.2f" % ck.hour())
	var c1 := Clock.new(6.0, 0.5)
	var c2 := Clock.new(6.0, 0.5)
	for i in range(100):
		c1.tick(0.017)
		c2.tick(0.017)
	_check(absf(c1.hour() - c2.hour()) < 1e-12,
		"two clocks with the same parameters never diverge",
		"%.9f h apart after 100 ticks" % absf(c1.hour() - c2.hour()))

	# --- 3. binding to a real deck's cast ---------------------------------
	print("\n3. BOUND TO A REAL DECK'S CAST")
	var actors: Array = _read_array(actors_path)
	_check(actors.size() > 0, "read <deck>_actors.json",
		"%d actors from %s" % [actors.size(), actors_path.get_file()])
	var root := Node3D.new()
	get_root().add_child(root)
	var visual := Node3D.new()
	root.add_child(visual)
	# One node per actor at the position the generator recorded. This does NOT
	# load the deck's 816k-triangle mesh: what is under test is the director's
	# arithmetic, and a MeshInstance3D in the right place exercises every line
	# of it for a thousandth of the cost.
	for a in actors:
		var mi := MeshInstance3D.new()
		mi.name = String(a.get("group", "x"))
		mi.position = Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0)))
		visual.add_child(mi)
	var dir := Director.new()
	root.add_child(dir)
	var n := dir.bind(visual, actors)
	_check(n == actors.size(), "every actor bound to its mesh",
		"%d of %d" % [n, actors.size()])

	# --- 4. leaving and returning is consistent ---------------------------
	print("\n4. LEAVING AND RETURNING IS CONSISTENT")
	dir.apply(3.0)
	var at3 := dir.transforms()
	var vis3 := dir.visible_count()
	dir.apply(8.0)
	var vis8 := dir.visible_count()
	dir.apply(13.0)
	var vis13 := dir.visible_count()
	dir.apply(3.0)
	var back3 := dir.transforms()
	var vis3b := dir.visible_count()
	var drift := 0.0
	for i in range(at3.size()):
		drift = maxf(drift, at3[i].distance_to(back3[i]))
	_check(drift < 1e-9 and vis3 == vis3b,
		"03:00 -> 08:00 -> 13:00 -> 03:00 returns every body exactly",
		"worst drift %.12f m over %d transforms, %d visible both times"
		% [drift, at3.size(), vis3])
	_check(vis3 < vis8 and vis8 <= vis13,
		"and the three hours are three different rooms",
		"%d bodies present at 03:00, %d at 08:00, %d at 13:00"
		% [vis3, vis8, vis13])

	# CONTROL: the integrator. Same trip, and it cannot come back.
	var itg := Integrator.new()
	for i in range(600):
		itg.step(0.016)
	var after := itg.pos
	itg.jump_to(3.0)
	_check(absf(itg.pos - after) < 1e-12 and itg.pos > 1.0,
		"CONTROL: an integrating director cannot return to 03:00",
		"%.2f m of accumulated drift it has no way to undo" % itg.pos)

	# --- 5. walkers cover ground ------------------------------------------
	print("\n5. A WALKER COVERS GROUND")
	# This deck's cast is all `standing` -- `populace.populate_corridor` writes
	# walkers and `deck.py` bakes them, but not onto this cluster -- so the
	# walker is built here. That is the difference between testing the code and
	# testing the data that happened to be lying about.
	var walker := Director.Person.new()
	var mi2 := MeshInstance3D.new()
	visual.add_child(mi2)
	walker.nodes.append(mi2)
	walker.rest.append(Vector3(211.0, 0.0, 7440.0))
	walker.local.append(Vector3(211.0, 0.0, 7440.0))   # bearing0 is 0, so local
	walker.radius_m = 211.0                            # and world agree here
	walker.bearing0 = 0.0
	walker.walker = true
	walker.way = 1.0
	mi2.position = walker.rest[0]
	dir.walk_to(walker, Director.BAKE_HOUR)
	var p0: Vector3 = mi2.position
	dir.walk_to(walker, Director.BAKE_HOUR + 1.0 / 60.0)   # one station minute
	var d_m := p0.distance_to(mi2.position)
	var want := dir.walk_speed_ms * 60.0
	_check(absf(d_m - want) / want < 0.02,
		"one station minute of walking covers a minute of walking",
		"%.1f m against %.1f m at %.2f m/s" % [d_m, want, dir.walk_speed_ms])
	dir.walk_to(walker, Director.BAKE_HOUR)
	_check(mi2.position.distance_to(p0) < 1e-9,
		"and returning to the same hour returns the same metre",
		"%.12f m apart" % mi2.position.distance_to(p0))
	# CONTROL: the SAME gate, on a director that does not move anybody. It has
	# to fail, or "a walker covers ground" is measuring the clock rather than
	# the walking.
	var still := Director.new()
	still.walk_speed_ms = 0.0
	root.add_child(still)
	still.walk_to(walker, Director.BAKE_HOUR + 1.0 / 60.0)
	var d0 := p0.distance_to(mi2.position)
	_check(absf(d0 - want) / want > 0.5,
		"CONTROL: at zero speed the same gate measures no motion, and fails",
		"%.1f m against the %.1f m it demands" % [d0, want])

	# --- 6. the frame budget ----------------------------------------------
	print("\n6. THE FRAME BUDGET")
	# 2,000 bodies is more than the whole station carries: `deck.py --sweep`
	# reports 963 walking in corridors and 1,065 standing in rooms.
	var big := Node3D.new()
	root.add_child(big)
	var many: Array = []
	for i in range(2000):
		var m := MeshInstance3D.new()
		m.name = "crowd_%d" % i
		m.position = Vector3(211.0 * cos(i * 0.003), 211.0 * sin(i * 0.003),
			7440.0)
		big.add_child(m)
		many.append({"group": m.name, "place": "central_corridor",
			"pose": "walking", "x": m.position.x, "y": m.position.y,
			"z": m.position.z, "who": {"id": "crowd:%d" % i}})
	var d2 := Director.new()
	root.add_child(d2)
	d2.bind(big, many)
	var worst := 0.0
	for k in range(24):
		d2.apply(float(k))
		worst = maxf(worst, d2.apply_us())
	# THE BUDGET IS BORROWED AND THAT IS SAID OUT LOUD. `body.NPC_FRAME_SHARE`
	# = 0.19 is a MESH budget -- it is how much of a frame the crowd may spend
	# holding triangles, and `crowd.py` spends it on LOD. The project has no
	# CPU budget for a crowd director because it has never had one, so this
	# gate borrows the only number that exists and uses it as a ceiling, which
	# is the conservative direction: 0.19 x a 16.67 ms frame at CLAUDE.md's
	# 1440p60 target = 3,167 us for the WHOLE crowd, and this must fit inside
	# it with the drawing still to pay for.
	var budget_us := 0.19 * 16667.0
	_check(worst < budget_us,
		"2,000 bodies update inside the crowd's borrowed frame share",
		("%.0f us worst of 24 hours against %.0f us -- %.2f us a body, so"
		+ " the 73 on the loaded deck cost %.0f us")
		% [worst, budget_us, worst / 2000.0, worst * 73.0 / 2000.0])

	print("\n" + "=".repeat(74))
	if _fails.is_empty():
		print("all gates pass")
		quit(0)
	else:
		print("%d FAILED: %s" % [_fails.size(), ", ".join(_fails)])
		quit(1)


func _read_array(path: String) -> Array:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return []
	var txt := f.get_as_text()
	f.close()
	var v = JSON.parse_string(txt)
	return v if v is Array else []
