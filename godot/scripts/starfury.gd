extends Node3D
## THE FLYABLE STARFURY.
##
## WHAT THIS EXISTS TO END. Session 4d's audit of what actually works listed
## "no flyable Starfury (zero references in any .gd or .tscn, though a flight
## model and a mesh both exist)". Both did exist: `station/physics/starfury.py`
## is 228 lines of tested Newtonian 6-DOF, `station/starfury_geometry.py` is a
## 774-line airframe anchored to that model's own thruster mounts, and
## `station/physics/rotating_frame.py` knows exactly what leaving a spinning
## hull does to you. None of it was reachable from the engine. This file and
## `station/starfury_scene.py` are the whole of the bridge.
##
## IT IS A PORT, AND A PORT IS A LIABILITY UNTIL IT IS CHECKED. The flight
## maths below is a line-by-line translation of `station/physics/starfury.py`,
## which means there are now two copies of it, which means they can drift --
## and "a port that drifts from its tested source" is a defect this project has
## found in three other places. So `--selftest` replays nine scenarios recorded
## from the PYTHON model and asserts this one lands on the same numbers, plus
## the thruster layout itself, thruster by thruster. Two negative controls
## (`--drift=aero`, `--drift=nogyro`) prove the comparison can fail: they inject
## the two mistakes a port of this model actually makes -- letting velocity
## follow the nose, and dropping Euler's gyroscopic term -- and the self-test
## must go red for both.
##
## WHY NOT PUT THE MODEL IN PYTHON AND STREAM IT. Because a flyable ship is a
## thing you fly, at frame rate, in response to a key that was pressed 8 ms ago.
## The alternative to a checked port is a ship that plays back a recording.
##
## HEADLESS BY DESIGN, like `scripts/walk.gd` and for the same reason: there is
## no GPU and no human here. `--selftest` and `--mission` need no window at all,
## and `--out=PNG` flies the mission and photographs the result, so every claim
## this file makes is reproducible by running one command.
##
## MODES
##   --selftest [--drift=aero|nogyro]   replay the Python vectors; print the table
##   --dock-selftest [--drift=NAME]     replay the Python docking law's samples
##   --pilot-test                       fly it from a scripted key sequence
##   --mission  [--flight-out=PATH]     fly launch -> transit -> approach -> dock
##   --out=PNG  [--frame=NAME]          fly it and photograph it
##                                      (ride | release | lookback | dock)
##   (none)                             fly it yourself; see _read_pilot_input

# --- what the shot supplies -------------------------------------------------
@export var hull_glb: String = ""
@export var fury_glb: String = ""
@export var launch_json: String = ""
@export var vectors_json: String = ""

# --- the pilot's controls, and they are deliberately six axes ---------------
## A Starfury has no preferred direction of travel, so a control scheme with
## four axes is a control scheme for an aeroplane. W/S is main thrust, A/D and
## R/F are the lateral and vertical RCS, arrows and Q/E are attitude. There is
## no roll key because THE MODEL HAS NO ROLL AUTHORITY -- see the finding in
## `_autopilot`.
## Ceiling on the attitude keys, rad/s. 60 deg/s puts a 180 degree flip at
## three seconds, which is about what the show's fighters look like.
const PILOT_RATE := 1.047
const KEY_HELP := "W/S main  A/D lateral  R/F vertical  arrows pitch/yaw  " \
	+ "SPACE kill rotation  X kill velocity  TAB chase/cockpit"

var model: FlightModel
var _ship: Node3D
var _cam: Camera3D
var _readout: Label
var _world: Node3D
var _proto: Node                    ## exterior.tscn, borrowed and then freed
var _launch: Dictionary = {}
var _shot: Dictionary = {}
var _out_path: String = ""
var _origin: Vector3 = Vector3.ZERO
var _rebases: int = 0
var _chase: bool = true
var _elapsed: float = 0.0


# ===========================================================================
# THE FLIGHT MODEL -- a port of station/physics/starfury.py
# ===========================================================================

class FlightModel extends RefCounted:
	## Rigid-body state and integration, in the station's world frame.
	##
	## Attitude is a quaternion because the Starfury genuinely does spend time
	## pointing every direction, and it is integrated with the raw component
	## form the Python model uses rather than through Godot's Quaternion
	## operators -- a port that "tidies up" the maths is a port that cannot be
	## compared line for line against the thing it came from.
	class Thruster extends RefCounted:
		## One thruster: where it sits on the hull and which way it PUSHES THE
		## CRAFT (the opposite of where its plume goes). Body frame, relative to
		## the centre of mass.
		var tname: String
		var position: Vector3
		var direction: Vector3
		var max_thrust: float

		func _init(n: String, p: Vector3, d: Vector3, t: float) -> void:
			tname = n
			position = p
			direction = d
			max_thrust = t

		func force(throttle: float) -> Vector3:
			return direction * (max_thrust * clampf(throttle, 0.0, 1.0))

		func torque(throttle: float) -> Vector3:
			return position.cross(force(throttle))


	## The SA-23E Aurora's layout: four corner booms plus RCS quads.
	##
	## DUPLICATED FROM PYTHON ON PURPOSE, exactly as `starfury_geometry.py`
	## duplicates the same anchors: importing them would make the agreement test
	## vacuous, and the point is to fail loudly when one side is edited and the
	## other is not. `--selftest` compares this table against `vectors.json`'s
	## `layout` block thruster by thruster, so a changed boom length names itself.
	static func aurora_thrusters(main_thrust: float = 68000.0,
			rcs_thrust: float = 4200.0) -> Array:
		var t: Array = []
		var boom := 3.4          # m outboard on each diagonal
		var aft := -2.1          # m aft of the centre of mass
		for sx in [1.0, -1.0]:
			for sy in [1.0, -1.0]:
				var n := "main_%s%s" % ["u" if sy > 0.0 else "l",
					"r" if sx > 0.0 else "l"]
				t.append(Thruster.new(n, Vector3(sx * boom, sy * boom, aft),
					Vector3(0.0, 0.0, 1.0), main_thrust))
		for sx in [1.0, -1.0]:
			t.append(Thruster.new("rcs_lat_%s" % ("r" if sx > 0.0 else "l"),
				Vector3(sx * boom, 0.0, 0.0), Vector3(-sx, 0.0, 0.0), rcs_thrust))
		for sy in [1.0, -1.0]:
			t.append(Thruster.new("rcs_vert_%s" % ("u" if sy > 0.0 else "d"),
				Vector3(0.0, sy * boom, 0.0), Vector3(0.0, -sy, 0.0), rcs_thrust))
		t.append(Thruster.new("rcs_retro", Vector3(0.0, 0.0, 2.4),
			Vector3(0.0, 0.0, -1.0), rcs_thrust * 2.0))
		return t

	var mass: float = 14800.0
	var inertia: Vector3 = Vector3(52000.0, 52000.0, 31000.0)
	var position: Vector3 = Vector3.ZERO
	var velocity: Vector3 = Vector3.ZERO
	var orientation: Quaternion = Quaternion(0.0, 0.0, 0.0, 1.0)   # (x,y,z,w)
	var angular_velocity: Vector3 = Vector3.ZERO
	var thrusters: Array = []
	## Negative controls for --selftest. Never set in flight.
	var drift_aero: float = 0.0      ## fraction of velocity dragged to the nose
	var drift_nogyro: bool = false   ## drop Euler's gyroscopic term

	func _init() -> void:
		thrusters = aurora_thrusters()

	func body_to_world(v: Vector3) -> Vector3:
		var q := orientation
		var u := Vector3(q.x, q.y, q.z)
		var t := u.cross(v) * 2.0
		return v + t * q.w + u.cross(t)

	func world_to_body(v: Vector3) -> Vector3:
		var q := orientation
		var u := Vector3(-q.x, -q.y, -q.z)
		var t := u.cross(v) * 2.0
		return v + t * q.w + u.cross(t)

	func forward() -> Vector3:
		return body_to_world(Vector3(0.0, 0.0, 1.0))

	func speed() -> float:
		return velocity.length()

	func max_linear_accel() -> float:
		var s := 0.0
		for th in thrusters:
			if th.tname.begins_with("main_"):
				s += th.max_thrust
		return s / mass

	func normalise() -> void:
		var q := orientation
		var n := sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z)
		if n > 0.0:
			orientation = Quaternion(q.x / n, q.y / n, q.z / n, q.w / n)

	## Throttle each thruster to best approximate the commanded demand.
	##
	## Deliberately simple and honest, and copied as such: each thruster opens
	## in proportion to how well it serves the demand, and a demand the layout
	## cannot satisfy comes out PARTIALLY SATISFIED rather than silently exact.
	## This is the part of the model that is a judgement rather than arithmetic,
	## which is exactly why two of the nine self-test scenarios go through it.
	func allocate(translate: Vector3, rotate: Vector3) -> Dictionary:
		var out := {}
		var tn := translate.length()
		var rn := rotate.length()
		# `v * (1/n)` and not `v / n`. The Python model's `unit()` multiplies by
		# the reciprocal, and the two differ in the last bit of a double. That
		# is below any physical significance and ABOVE the tolerance the vector
		# comparison runs at, which is deliberate: the comparison is checking
		# that this is the same algorithm, not that it is approximately right.
		var tw := (translate * (1.0 / tn)) if tn > 0.0 else Vector3.ZERO
		var rw := (rotate * (1.0 / rn)) if rn > 0.0 else Vector3.ZERO
		for th in thrusters:
			var lin: float = th.direction.dot(tw) * tn
			var tq: Vector3 = th.torque(1.0)
			var rot := 0.0
			var tql := tq.length()
			if tql > 0.0:
				rot = (tq * (1.0 / tql)).dot(rw) * rn
			out[th.tname] = clampf(lin + rot, 0.0, 1.0)
		return out

	func net(throttles: Dictionary) -> Array:
		var f := Vector3.ZERO
		var t := Vector3.ZERO
		for th in thrusters:
			var k: float = throttles.get(th.tname, 0.0)
			if k <= 0.0:
				continue
			f += th.force(k)
			t += th.torque(k)
		return [f, t]

	## Advance by dt. Semi-implicit Euler: stable and momentum-preserving at
	## the step sizes a flight model runs at.
	func step(dt: float, throttles: Dictionary = {},
			external_accel: Vector3 = Vector3.ZERO) -> void:
		var n := net(throttles)
		var force_body: Vector3 = n[0]
		var torque_body: Vector3 = n[1]

		var accel := body_to_world(force_body) * (1.0 / mass) + external_accel
		velocity += accel * dt
		# NEGATIVE CONTROL ONLY. This is the aeroplane assumption -- velocity
		# follows the nose -- and it is the single mistake this model exists to
		# not make. It lives here so the self-test can prove it gets caught.
		#
		# IT DOES NOT FIRE ON EVERY SCENARIO, AND THAT IS ARITHMETIC RATHER
		# THAN A HOLE. Measured: 6 of 9 go red. The three that do not are
		# `flip_and_burn`, `allocate_forward` and `free_tumble`, and in all
		# three the velocity is COLLINEAR with the nose -- lerping a vector
		# toward its own line and renormalising to the same speed returns the
		# vector unchanged, whether it is parallel or antiparallel. A control
		# that fired on those would be measuring the lerp, not the coupling.
		if drift_aero > 0.0 and velocity.length() > 0.0:
			var sp := velocity.length()
			velocity = velocity.lerp(forward() * sp, drift_aero * dt).normalized() * sp
		position += velocity * dt

		var ix := inertia.x
		var iy := inertia.y
		var iz := inertia.z
		var wx := angular_velocity.x
		var wy := angular_velocity.y
		var wz := angular_velocity.z
		# Euler's equations: the gyroscopic term is what makes a tumbling
		# Starfury precess instead of spinning about a fixed body axis.
		var gyro := Vector3((iy - iz) * wy * wz, (iz - ix) * wz * wx,
			(ix - iy) * wx * wy)
		if drift_nogyro:
			gyro = Vector3.ZERO
		angular_velocity += Vector3((torque_body.x + gyro.x) / ix,
			(torque_body.y + gyro.y) / iy, (torque_body.z + gyro.z) / iz) * dt

		wx = angular_velocity.x
		wy = angular_velocity.y
		wz = angular_velocity.z
		var q := orientation
		orientation = Quaternion(
			q.x + 0.5 * dt * (q.w * wx + q.y * wz - q.z * wy),
			q.y + 0.5 * dt * (q.w * wy + q.z * wx - q.x * wz),
			q.z + 0.5 * dt * (q.w * wz + q.x * wy - q.y * wx),
			q.w + 0.5 * dt * (-q.x * wx - q.y * wy - q.z * wz))
		normalise()


# ===========================================================================
# Entry
# ===========================================================================

func _ready() -> void:
	# Off until something asks for it. Godot enables _physics_process for any
	# node that defines it, and the headless modes below quit from inside
	# _ready -- a physics tick landing in the middle of that would step a model
	# that does not exist yet.
	set_physics_process(false)
	var args := _args()
	if args.has("scene-json"):
		_shot = _read_json(String(args["scene-json"]))
		hull_glb = String(_shot.get("hull_glb", hull_glb))
		fury_glb = String(_shot.get("fury_glb", fury_glb))
		launch_json = String(_shot.get("launch_json", launch_json))
		vectors_json = String(_shot.get("vectors_json", vectors_json))
	for pair in [["hull", "hull_glb"], ["fury", "fury_glb"],
			["launch-json", "launch_json"], ["vectors", "vectors_json"]]:
		if args.has(String(pair[0])):
			set(String(pair[1]), String(args[String(pair[0])]))
	_out_path = String(args.get("out", ""))

	if args.has("pilot-test"):
		get_tree().quit(0 if _pilot_test() else 1)
		return

	if args.has("selftest"):
		get_tree().quit(0 if _selftest(String(args.get("drift", ""))) else 1)
		return

	if launch_json != "":
		_launch = _read_json(launch_json)
		_dock = _launch.get("dock", {})

	if args.has("dock-selftest"):
		get_tree().quit(0 if _dock_selftest(String(args.get("drift", ""))) else 1)
		return

	if args.has("mission"):
		var flight := _fly_mission()
		var dst := String(args.get("flight-out",
			launch_json.get_base_dir() + "/flight.json"))
		var f := FileAccess.open(dst, FileAccess.WRITE)
		if f == null:
			push_error("starfury: cannot write %s" % dst)
			get_tree().quit(2)
			return
		f.store_string(JSON.stringify(flight, " "))
		f.close()
		print("starfury: wrote %s" % dst)
		get_tree().quit(0)
		return

	model = FlightModel.new()
	_build_world()
	_spawn_ship()

	if _out_path != "" and not args.has("free"):
		await _photograph(String(args.get("frame",
			_shot.get("frame", "lookback"))))
		return
	_start_interactive()
	# `--free=SECONDS` flies the REAL interactive path -- physics process, pilot
	# input, chase camera, debug readout -- for a fixed wall time and then, if
	# asked, photographs it. It exists because every other mode here bypasses
	# `_physics_process`, and a build whose only tested paths are the headless
	# ones is a build whose playable path is the untested one.
	if args.has("free"):
		var secs := float(args["free"])
		await get_tree().create_timer(secs).timeout
		print("starfury: %.1f s of free flight -- %.0f m travelled, %.1f m/s, "
			% [secs, model.position.distance_to(_launch_origin()), model.speed()]
			+ "%d origin rebase(s)" % _rebases)
		if _out_path != "":
			for i in 6:
				await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			DirAccess.make_dir_recursive_absolute(_out_path.get_base_dir())
			img.save_png(_out_path)
			print("captured %s  %dx%d" % [_out_path, img.get_width(),
				img.get_height()])
		get_tree().quit(0)


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--"):
			s = s.substr(2)
		var eq := s.find("=")
		if eq >= 0:
			out[s.substr(0, eq)] = s.substr(eq + 1)
		else:
			out[s] = "1"
	return out


## Godot's String % has no %e and no %g, and a formatting error there is a
## silently unprinted line in the middle of a verdict table.
func _sci(x: float) -> String:
	if x == 0.0:
		return "0"
	var e := int(floor(log(absf(x)) / log(10.0)))
	return "%.3fe%d" % [x / pow(10.0, e), e]


func _read_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("starfury: cannot open %s" % path)
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func _v3(a) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


# ===========================================================================
# THE SELF-TEST -- this port against the Python model that has the tests
# ===========================================================================

## Replay `vectors.json` and compare every checkpoint, component by component.
##
## THE TOLERANCE IS NOT A PHYSICS TOLERANCE. Both sides run the same
## semi-implicit Euler in double precision over the same step count, so
## agreement is a bit-level question: anything above ~1e-9 relative means a
## DIFFERENT ALGORITHM, not accumulated error. Setting a loose tolerance here
## would turn the one check on this port into a check that cannot fail, which
## is the defect CLAUDE.md names three times.
func _selftest(drift: String) -> bool:
	if vectors_json == "":
		push_error("starfury: --selftest needs --vectors=PATH")
		return false
	var vec := _read_json(vectors_json)
	if vec.is_empty():
		return false
	var tol: Dictionary = vec.get("tolerance", {})
	var abs_tol := float(tol.get("abs", 1e-6))
	var rel_tol := float(tol.get("rel", 1e-9))
	print("--- GDScript flight model against station/physics/starfury.py ---")
	if drift != "":
		print("NEGATIVE CONTROL ACTIVE: drift=%s. Every scenario it touches "
			% drift + "MUST fail; a control that does not fire proves nothing.")

	var ok := _check_layout(vec)
	var worst_name := ""
	var worst := 0.0
	var failed := 0
	for sc in vec.get("scenarios", []):
		var s: Dictionary = sc
		var m := FlightModel.new()
		if drift == "aero":
			m.drift_aero = 0.02
		elif drift == "nogyro":
			m.drift_nogyro = true
		var init: Dictionary = s.get("initial", {})
		if init.has("position"):
			m.position = _v3(init["position"])
		if init.has("velocity"):
			m.velocity = _v3(init["velocity"])
		if init.has("angular_velocity"):
			m.angular_velocity = _v3(init["angular_velocity"])
		if init.has("orientation"):
			var q = init["orientation"]
			m.orientation = Quaternion(float(q[1]), float(q[2]), float(q[3]),
				float(q[0]))
		var cmd: Dictionary = s["command"]
		var dt := float(s["dt"])
		var every := int(s["every"])
		var checks: Array = s["checkpoints"]
		var ci := 0
		var worst_here := 0.0
		for i in int(s["steps"]):
			var th: Dictionary = {}
			if cmd.has("throttles"):
				th = cmd["throttles"]
			else:
				th = m.allocate(_v3(cmd["demand"][0]), _v3(cmd["demand"][1]))
			m.step(dt, th)
			if (i + 1) % every == 0 and ci < checks.size():
				worst_here = maxf(worst_here, _compare(m, checks[ci]))
				ci += 1
		var pass_here := worst_here <= maxf(abs_tol, rel_tol)
		if not pass_here:
			failed += 1
		if worst_here > worst:
			worst = worst_here
			worst_name = String(s["name"])
		print("  %s  %-24s worst |delta| %s   %s"
			% ["PASS" if pass_here else "FAIL", String(s["name"]),
				_sci(worst_here), String(s["why"]).substr(0, 76)])
		ok = ok and pass_here

	print("  worst scenario: %s at %s (tolerance %s)"
		% [worst_name, _sci(worst), _sci(maxf(abs_tol, rel_tol))])
	if drift != "":
		# THE CONTROL'S VERDICT IS INVERTED. A drifted model that still matches
		# means the comparison is inert, and an inert comparison is worse than
		# no comparison because it is reported as a pass.
		if ok:
			print("CONTROL DID NOT FIRE -- the vector comparison cannot fail, "
				+ "so it says nothing about the port. This is a FAILURE.")
			return false
		print("CONTROL FIRED: %d of %d scenarios went red under drift=%s. "
			% [failed, vec.get("scenarios", []).size(), drift]
			+ "The comparison is real.")
		return true
	print("%d of %d scenarios match the Python model"
		% [vec.get("scenarios", []).size() - failed,
			vec.get("scenarios", []).size()])
	return ok


## Largest absolute discrepancy across all thirteen numbers of a state.
##
## The quaternion is compared with its sign folded, because q and -q are the
## same attitude and a port that renormalises through a different branch is not
## wrong for choosing the other one.
func _compare(m: FlightModel, want: Dictionary) -> float:
	var d := 0.0
	for pair in [[m.position, want["position"]], [m.velocity, want["velocity"]],
			[m.angular_velocity, want["angular_velocity"]]]:
		var got: Vector3 = pair[0]
		var w = pair[1]
		for i in 3:
			d = maxf(d, absf(got[i] - float(w[i])))
	var q := m.orientation
	var wq = want["orientation"]
	var s := 1.0 if (q.w * float(wq[0]) + q.x * float(wq[1])
		+ q.y * float(wq[2]) + q.z * float(wq[3])) >= 0.0 else -1.0
	d = maxf(d, absf(s * q.w - float(wq[0])))
	d = maxf(d, absf(s * q.x - float(wq[1])))
	d = maxf(d, absf(s * q.y - float(wq[2])))
	d = maxf(d, absf(s * q.z - float(wq[3])))
	return d


## The thruster table, thruster by thruster.
##
## The vector replay covers this implicitly -- a wrong boom length changes the
## yaw scenario -- but implicitly is not good enough for a table that is
## DELIBERATELY duplicated in three files. When it breaks, the failure should
## say "main_ur is 0.4 m out", not "asymmetric_yaw drifted".
func _check_layout(vec: Dictionary) -> bool:
	var want: Dictionary = vec.get("layout", {})
	if want.is_empty():
		print("  ..    layout                   NOT CHECKED -- vectors.json "
			+ "carries no layout block")
		return true
	var mine := {}
	for th in FlightModel.aurora_thrusters():
		mine[th.tname] = th
	var bad := PackedStringArray()
	for key in want.keys():
		if not mine.has(key):
			bad.append("%s missing" % key)
			continue
		var t = mine[key]
		var w: Dictionary = want[key]
		if (t.position - _v3(w["position"])).length() > 1e-9:
			bad.append("%s position %s != %s" % [key, t.position, w["position"]])
		if (t.direction - _v3(w["direction"])).length() > 1e-9:
			bad.append("%s direction %s != %s" % [key, t.direction, w["direction"]])
		if absf(t.max_thrust - float(w["max_thrust"])) > 1e-6:
			bad.append("%s thrust %f != %f" % [key, t.max_thrust, w["max_thrust"]])
	for key in mine.keys():
		if not want.has(key):
			bad.append("%s is in the port and not in the model" % key)
	if bad.is_empty():
		print("  PASS  layout                   %d thrusters agree with "
			% mine.size() + "station/physics/starfury.py")
		return true
	print("  FAIL  layout                   %s" % ", ".join(bad))
	return false


# ===========================================================================
# THE MISSION -- launch from a cobra bay and fly clear
# ===========================================================================

const RIDE_S := 5.0          ## seconds riding the bay before release
const COAST_S := 6.0         ## seconds after release with no thrust at all
const MISSION_DT := 1.0 / 120.0
const MISSION_MAX_S := 240.0
const TRANSIT_VMAX := 520.0   ## m/s cruise cap on the run out
## Ceiling on the dock. The Python sweep's slowest of twelve start phases takes
## 160.6 s, of which up to 33.47 s is the loiter wait for the bay to come round,
## so 300 s is a little under twice the worst case and cannot be reached by a
## converging approach.
const DOCK_MAX_S := 300.0


## Fly the whole thing and return a record of it.
##
## THE LAUNCH IS NOT A NUMBER THIS FILE IS TOLD. `launch.json` carries the bay's
## radius, axial station, clocking and omega -- four measurements -- and the
## exit velocity is DERIVED here, twice, from those: once as omega x r and once
## by finite-differencing the trajectory of a craft riding the bay round. Both
## are then compared against `rotating_frame.velocity_to_inertial`'s analytic
## answer by `station/starfury_scene.py --check`. Three routes to one number,
## and a port that has the rotation backwards moves exactly one of them.
func _fly_mission() -> Dictionary:
	var bay: Dictionary = _launch.get("bay", {})
	var omega := float(_launch["omega_rad_s"])
	var r := float(bay["mouth_radius_m"])
	var z := float(bay["z_m"])
	var phase := float(bay["phase_rad"])
	var waypoint := _v3(_launch["waypoint_m"])
	var centre := _v3(_launch["station_centre_m"])

	var m := FlightModel.new()
	var dt := MISSION_DT
	var t := 0.0
	var samples := []

	# HOW LONG THE FIGHTER RIDES THE BAY BEFORE THE CLAMPS LET GO, and it is
	# derived rather than picked. The bay comes round once every 33.47 s, and
	# on most of that lap it is on the anti-sun side, where a fighter leaving
	# it is a black shape against a black hull -- the first launch frame taken
	# here was exactly that. So the ride lasts until the bay's own outward
	# radial swings into the sun, which is a number this scene already has:
	# the key's position. With no sun in the shot (the headless `--mission`
	# run) it falls back to RIDE_S, and the launch physics is identical either
	# way -- this only chooses WHEN in the lap it happens.
	var ride_s := RIDE_S
	if _shot.has("sun_from"):
		var sun := _v3(_shot["sun_from"]) - centre
		var want := atan2(sun.y, sun.x)
		ride_s = fposmod(want - phase, TAU) / omega

	# --- riding the bay ----------------------------------------------------
	# The craft is not flying yet: it is a point on a rotating hull, and its
	# position is a function of time and nothing else. Attitude is nose-out
	# along the tube, which is the one thing about a cobra bay that is not
	# arguable -- the tube points outward.
	var prev := Vector3.ZERO
	var nose_worst := 0.0
	while t < ride_s:
		var a := phase + omega * t
		prev = m.position
		m.position = Vector3(r * cos(a), r * sin(a), z)
		var out_dir := Vector3(cos(a), sin(a), 0.0)
		m.orientation = _look_quat(out_dir, Vector3(0.0, 0.0, 1.0))
		# THE ONE THING A QUATERNION BUILT FROM A BASIS CAN GET WRONG is which
		# way round it is, and a sign error there is invisible in every frame
		# except the one where the fighter leaves the bay backwards. Checked
		# every step rather than argued about: the nose must be the tube.
		nose_worst = maxf(nose_worst, (m.forward() - out_dir).length())
		t += dt
		if int(t / dt) % 12 == 0:
			samples.append(_sample(t, m, "ride"))

	if nose_worst > 1e-9:
		push_error("starfury: the airframe is not pointing down the tube -- "
			+ "nose off by %s. The launch attitude is wrong." % _sci(nose_worst))

	# --- release ------------------------------------------------------------
	var fd := (m.position - prev) / dt                 # from the ride itself
	var analytic := Vector3(-omega * m.position.y, omega * m.position.x, 0.0)
	m.velocity = analytic
	var release := {
		"t_s": t,
		"position_m": [m.position.x, m.position.y, m.position.z],
		"radius_m": Vector2(m.position.x, m.position.y).length(),
		"omega_rad_s": omega,
		"exit_velocity_m_s": [analytic.x, analytic.y, analytic.z],
		"exit_speed_m_s": analytic.length(),
		"exit_speed_finite_difference_m_s": fd.length(),
		"finite_difference_velocity_m_s": [fd.x, fd.y, fd.z],
		"derivation": ("omega x r computed in the engine, and the same number "
			+ "recovered by differencing the ride. Neither is read from "
			+ "launch.json; launch.json is what they are checked against."),
	}
	var r0 := Vector2(m.position.x, m.position.y).length()

	# --- coasting, unpowered ------------------------------------------------
	var t_coast_end := t + COAST_S
	while t < t_coast_end:
		m.step(dt)
		t += dt
		if int(t / dt) % 12 == 0:
			samples.append(_sample(t, m, "coast"))
	var r1 := Vector2(m.position.x, m.position.y).length()

	# --- transit ------------------------------------------------------------
	# VELOCITY MATCHING, not pursuit, and the difference is a mission that ends.
	# The first version aimed at the waypoint and braked when the closing rate
	# said to -- pure pursuit with a brachistochrone. It never converged: it
	# flew past, looped, and was still orbiting the waypoint at 240 s, 3.7 km
	# out and doing 490 m/s. The reason is that a closing-rate test cannot see
	# LATERAL velocity, and at 400 m/s with a four-second flip, lateral drift
	# is most of the miss.
	#
	# What works is to compute the velocity the craft SHOULD have -- along the
	# line of sight, capped three ways -- and burn to null the difference.
	# Aiming at `v_desired - v` kills the lateral component for free, because
	# it is part of the error rather than invisible to it.
	var peak := m.speed()
	var burn_s := 0.0
	var brake_s := 0.0
	var amax := m.max_linear_accel()
	while t < MISSION_MAX_S:
		var to_wp := waypoint - m.position
		var d := to_wp.length()
		# Three caps, each for a different reason. TRANSIT_VMAX is the cruise;
		# the square-root term is the brachistochrone, derated to 70% so there
		# is authority left for steering; the linear term is what stops the
		# terminal hunting, because near the target the limit has to fall
		# faster than the craft can turn.
		var vcap := minf(TRANSIT_VMAX, minf(
			sqrt(2.0 * 0.7 * amax * maxf(0.0, d - 100.0)), 0.10 * d + 15.0))
		var dv := to_wp.normalized() * vcap - m.velocity
		var aim := dv.normalized() if dv.length() > 1e-6 else m.forward()
		if m.velocity.dot(to_wp) < 0.0 or vcap < m.speed():
			brake_s += dt
		else:
			burn_s += dt
		m.step(dt, _autopilot(m, aim, 1.0 if dv.length() > 1.5 else 0.0))
		peak = maxf(peak, m.speed())
		t += dt
		if int(t / dt) % 12 == 0:
			samples.append(_sample(t, m, "transit"))
		if d < 400.0 and m.speed() < 60.0:
			break

	# --- station-keeping ----------------------------------------------------
	# IN VACUUM THERE IS NO BRAKE. Stopping is a manoeuvre: point retrograde,
	# burn until the velocity is gone, and it takes as long as it takes. This
	# is the same thing the X key does in free flight.
	var t_hold_end := t + 40.0
	while t < t_hold_end and m.speed() > 1.0:
		m.step(dt, _autopilot(m, -m.velocity.normalized(), 1.0))
		t += dt
		if int(t / dt) % 12 == 0:
			samples.append(_sample(t, m, "hold"))

	# --- turn and look back -------------------------------------------------
	# The last thing a pilot does before the shot: point the nose at the thing
	# they came out to look at.
	var t_look_end := t + 12.0
	while t < t_look_end:
		m.step(dt, _autopilot(m, (centre - m.position).normalized(), 0.0))
		t += dt
		if int(t / dt) % 12 == 0:
			samples.append(_sample(t, m, "look"))

	# THE LOOK-BACK BEAT IS CAPTURED BEFORE THE DOCK, and this is not tidiness.
	# `_photograph("lookback")` and `starfury_scene.compose_lookback` both used
	# `flight["final"]`, which up to this session WAS the look-back state. Adding
	# a dock phase after it silently redefined `final` to mean "parked in the
	# bay", and the money shot would have been taken from 3 m off the hull with
	# the nose 85 degrees off the station -- a frame nobody would have re-taken
	# and no gate would have failed on.
	var lookback := _sample(t, m, "lookback")
	var eye := _chase_eye(m)
	var nose_err := rad_to_deg((centre - m.position).normalized()
		.angle_to(m.forward()))
	var look_range := (m.position - centre).length()

	# --- the dock -----------------------------------------------------------
	# THE MISSION IS ONE CONTINUOUS RUN. Everything above got the fighter out;
	# this brings it home to the bay it left, and it is the same craft, the same
	# integrator and the same allocator throughout -- no teleport, no reset.
	var dock := _fly_dock(m, t, dt, samples)
	t = float(dock["t_end_s"])

	var summary := {
		"elapsed_s": t,
		"dt": dt,
		"range_m": look_range,
		"lookback_t_s": float(lookback["t_s"]),
		"docked": dock["docked"],
		"dock_elapsed_s": dock["elapsed_s"],
		"peak_speed_m_s": peak,
		"final_speed_m_s": m.speed(),
		"burn_s": burn_s,
		"brake_s": brake_s,
		"unpowered_radius_gain_m": r1 - r0,
		"unpowered_radius_m": [r0, r1],
		"nose_error_deg": nose_err,
		"dock_contact_speed_m_s": dock["contact_speed_m_s"],
		"max_linear_accel_m_s2": m.max_linear_accel(),
	}
	print("starfury: released at %.2f m/s from r %.1f m; coasted unpowered to "
		% [release["exit_speed_m_s"], r0]
		+ "r %.0f m in %.0f s; %.0f s under power (%.0f accelerating, %.0f "
			% [r1, COAST_S, burn_s + brake_s, burn_s, brake_s]
		+ "decelerating), peak %.0f m/s; looked back from %.0f m with the nose "
			% [peak, look_range]
		+ "%.2f deg off the station, then %s in %.0f s. %.0f s in all."
			% [nose_err, "DOCKED" if dock["docked"] else "did NOT dock",
				float(dock["elapsed_s"]), t])
	return {
		"release": release,
		"dock": dock,
		"lookback": lookback,
		"final": _sample(t, m, "final"),
		"camera": {"eye": [eye.x, eye.y, eye.z],
			"target": [centre.x, centre.y, centre.z], "fov": 46.0},
		"summary": summary,
		"samples": samples,
	}


## Fly the approach and dock. The launch run backwards.
##
## FIVE STAGES AND EACH ONE ENDS ON A MEASUREMENT, not on a timer:
##   return    fly to the loiter point -- a FIXED INERTIAL point on the hold
##             circle, on the craft's own azimuth. Ends inside the capture box.
##   loiter    wait, costing nothing, until the bay is exactly one spin-up arc
##             behind. Arming on `gap > lead` first, because committing merely
##             because the gap is small lets the bay sweep past a craft at rest
##             and the law then chases it the long way round and cuts the chord
##             into the hull -- measured, on 1 of 12 start phases.
##   run_in    spin up onto the circle and capture the hold point.
##   terminal  ramp the standoff down at the plan's closing rate.
##   settle    hold at the contact standoff until the contact test passes.
func _fly_dock(m: FlightModel, t0: float, dt: float, samples: Array) -> Dictionary:
	if _dock.is_empty():
		return {"docked": false, "reason": "launch.json carries no dock block",
			"t_end_s": t0}
	var t := t0
	var stage := "return"
	var standoff: float = _dk("standoff_m")
	var loiter := _loiter_point(m.position)
	var lead: float = _dk("commit_lead_rad")
	var armed := false
	var t_stage := t0
	var times := {"return": 0.0, "loiter": 0.0, "run_in": 0.0,
		"terminal": 0.0, "settle": 0.0}
	var prev_aim := Vector3.ZERO
	var have_prev := false
	var peak := 0.0
	var dock_peak := 0.0
	var hull_clear := 1.0e30
	var docked := false
	var reason := ""
	var steps := 0
	while t - t0 < DOCK_MAX_S:
		var target := _stage_target(stage, t, standoff, loiter)
		var out := _dock_command(t, m.position, m.velocity, standoff, target)
		var cmd: Vector3 = out[0]
		var d: float = out[1]
		var dv: float = out[2]
		if stage == "return":
			if d <= _dk("capture_range_m") and dv <= _dk("capture_speed_m_s"):
				stage = "loiter"
				times["return"] = t - t_stage
				t_stage = t
		if stage == "loiter":
			var gap: float = fposmod(atan2(m.position.y, m.position.x)
				- (float(_dock["bay_phase"]) + float(_dock["omega"]) * t), TAU)
			if gap > lead:
				armed = true
			if armed and gap <= lead:
				stage = "run_in"
				times["loiter"] = t - t_stage
				t_stage = t
		elif stage == "run_in":
			if d <= _dk("capture_range_m") and dv <= _dk("capture_speed_m_s"):
				stage = "terminal"
				times["run_in"] = t - t_stage
				t_stage = t
		elif stage == "terminal":
			standoff = maxf(_dk("contact_standoff_m"),
				standoff - _dk("closing_rate_m_s") * dt)
			if standoff <= _dk("contact_standoff_m"):
				stage = "settle"
				times["terminal"] = t - t_stage
				t_stage = t
		elif stage == "settle":
			var rep := _contact_report(t, m.position, m.velocity)
			if bool(rep["safe"]) and d <= _dk("capture_range_m"):
				times["settle"] = t - t_stage
				docked = true
				break
		var clear: float = Vector2(m.position.x, m.position.y).length() \
			- _hull_radius_at(m.position.z)
		hull_clear = minf(hull_clear, clear)
		if clear < 0.0:
			reason = "flew into the hull at r %.1f m, z %.1f m" \
				% [Vector2(m.position.x, m.position.y).length(), m.position.z]
			break
		var mag := cmd.length()
		peak = maxf(peak, mag)
		if stage == "terminal" or stage == "settle":
			dock_peak = maxf(dock_peak, mag)
		# The feedforward is the demand's OWN measured rotation rate, not the
		# station's omega. Both are right at the bay and only one is right at
		# 10 km: during the return the demand points wherever the velocity error
		# is and rotates at nothing like omega. It converges to 0.1877 rad/s by
		# the time the craft is on the circle, which is omega to three figures.
		var aim := _unit(cmd)
		var ff := Vector3.ZERO if not have_prev \
			else prev_aim.cross(aim) * (1.0 / dt)
		prev_aim = aim
		have_prev = true
		var ap := _dock_autopilot(m, aim,
			ff, minf(1.0, mag / _dk("max_accel_m_s2")))
		m.step(dt, ap[0])
		t += dt
		steps += 1
		if steps % 12 == 0:
			samples.append(_sample(t, m, "dock_" + stage))
	if not docked and reason == "":
		reason = "ran out of time in stage %s" % stage
	var rep := _contact_report(t, m.position, m.velocity)
	var bay_pos: Vector3 = _dock_target(t, 0.0, 0.0)[0]
	var phase_err := rad_to_deg(atan2(m.position.y, m.position.x)
		- (float(_dock["bay_phase"]) + float(_dock["omega"]) * t))
	while phase_err > 180.0:
		phase_err -= 360.0
	while phase_err < -180.0:
		phase_err += 360.0
	var radial: float = m.velocity.dot(
		Vector3(bay_pos.x, bay_pos.y, 0.0).normalized())
	var r_c := Vector2(m.position.x, m.position.y).length()
	var out_d := {
		"docked": docked, "reason": reason, "t_end_s": t,
		"elapsed_s": t - t0, "steps": steps,
		"stage_s": times, "loiter_point_m": [loiter.x, loiter.y, loiter.z],
		"commit_lead_deg": rad_to_deg(lead),
		"closing_rate_m_s": rep["closing_rate"],
		"lateral_slip_m_s": rep["lateral_slip"],
		"naive_lateral_m_s": rep["naive_lateral"],
		"naive_safe": rep["naive_safe"],
		"misalignment_deg": rep["misalignment_deg"],
		"lateral_offset_m": rep["lateral_offset"],
		"phase_error_deg": phase_err,
		"miss_m": (m.position - bay_pos).length(),
		"contact_radius_m": r_c,
		"contact_speed_m_s": m.speed(),
		"radial_velocity_m_s": radial,
		# The tangential speed the craft would have AT THE BAY'S OWN RADIUS if
		# it kept co-rotating -- which is the number the launch releases at.
		"tangential_at_bay_radius_m_s":
			sqrt(maxf(0.0, m.speed() * m.speed() - radial * radial))
			* float(_dock["bay_radius"]) / maxf(1.0, r_c),
		"peak_accel_m_s2": peak,
		"peak_accel_fraction": peak / _dk("max_accel_m_s2"),
		"dock_peak_accel_m_s2": dock_peak,
		"dock_peak_accel_fraction": dock_peak / _dk("max_accel_m_s2"),
		"hull_clearance_m": hull_clear,
		"contact_safe": docked and bool(rep["safe"]),
	}
	print("starfury: dock %s -- %s in %.1f s (return %.1f, loiter %.1f, run-in "
		% ["ACHIEVED" if docked else "FAILED (%s)" % reason,
			"contact" if docked else "no contact", t - t0, times["return"],
			times["loiter"]]
		+ "%.1f, close %.1f, settle %.2f); closing %.3f m/s, slip %.4f m/s, "
			% [times["run_in"], times["terminal"], times["settle"],
				rep["closing_rate"], rep["lateral_slip"]]
		+ "lateral %.2f m, phase error %+.3f deg, peak %.1f%% of thrust, hull "
			% [rep["lateral_offset"], phase_err,
				100.0 * dock_peak / _dk("max_accel_m_s2")]
		+ "clearance %.1f m" % hull_clear)
	return out_d


## `contact_is_safe` referenced to the ROTATING STRUCTURE rather than to the
## bay's own reference point -- see `docking.contact_report`. Both verdicts are
## reported because the difference is the finding: a craft standing off by its
## own half-length is co-rotating 0.563 m/s faster than the bay, and the old
## function's lateral limit is 0.500, so a perfectly flown dock fails it by
## construction.
func _contact_report(t: float, pos: Vector3, vel: Vector3) -> Dictionary:
	var w: float = float(_dock["omega"])
	var ang := float(_dock["bay_phase"]) + w * t
	var n := Vector3(cos(ang), sin(ang), 0.0)
	var bp: Vector3 = _dock_target(t, 0.0, 0.0)[0]
	var slip := vel - Vector3(-w * pos.y, w * pos.x, 0.0)
	var naive := vel - Vector3(-w * bp.y, w * bp.x, 0.0)
	var los := _unit(pos - bp)
	var mis := rad_to_deg(acos(clampf(los.dot(n), -1.0, 1.0)))
	var lat := (slip - n * slip.dot(n)).length()
	var offs: Vector3 = pos - bp
	return {
		"safe": -slip.dot(n) <= 2.0 and lat <= 0.5 and mis <= 8.0,
		"closing_rate": -slip.dot(n), "lateral_slip": lat,
		"misalignment_deg": mis,
		"lateral_offset": (offs - n * offs.dot(n)).length(),
		"naive_lateral": (naive - n * naive.dot(n)).length(),
		"naive_safe": -naive.dot(n) <= 2.0
			and (naive - n * naive.dot(n)).length() <= 0.5 and mis <= 8.0,
	}


## The port against station/physics/docking.py, at fixed states, open loop.
##
## `--dock-selftest --drift=NAME` injects the three mistakes a port of this law
## actually makes and the comparison must go red for all three:
##   nocoriolis   drop the 2*closing*omega term out of the target acceleration
##   nophase      drop the target's velocity feedforward
##   noattff      drop the attitude loop's rotation-rate feedforward
func _dock_selftest(drift: String) -> bool:
	if vectors_json == "" or _dock.is_empty():
		push_error("starfury: --dock-selftest needs --vectors and a dock block")
		return false
	var vec := _read_json(vectors_json)
	var gs: Array = vec.get("guidance_samples", [])
	var att: Array = vec.get("attitude_samples", [])
	if gs.is_empty() or att.is_empty():
		push_error("starfury: vectors.json carries no guidance/attitude "
			+ "samples -- run station/starfury_scene.py --build")
		return false
	_drift = drift
	print("--- the docking law against station/physics/docking.py ---")
	if drift != "":
		print("NEGATIVE CONTROL ACTIVE: drift=%s. The comparison MUST go red."
			% drift)
	var worst_g := 0.0
	var bad_g := 0
	for s in gs:
		var sd: Dictionary = s
		var target := _stage_target(String(sd["stage"]), float(sd["t"]),
			float(sd["standoff_m"]), _v3(sd["loiter"]))
		var got := _dock_command(float(sd["t"]), _v3(sd["position"]),
			_v3(sd["velocity"]), float(sd["standoff_m"]), target,
			bool(sd["phase_match"]))
		var want := _v3(sd["accel"])
		var e := (got[0] as Vector3 - want).length()
		e = maxf(e, absf(float(got[1]) - float(sd["range_m"])))
		e = maxf(e, absf(float(got[2]) - float(sd["velocity_error_m_s"])))
		worst_g = maxf(worst_g, e)
		if e > 1e-9:
			bad_g += 1
	print("  %s  guidance                 %d of %d samples match, worst "
		% ["PASS" if bad_g == 0 else "FAIL", gs.size() - bad_g, gs.size()]
		+ "|delta| %s" % _sci(worst_g))

	var worst_a := 0.0
	var bad_a := 0
	for s in att:
		var sd: Dictionary = s
		var m := FlightModel.new()
		var q = sd["orientation"]
		m.orientation = Quaternion(float(q[1]), float(q[2]), float(q[3]),
			float(q[0]))
		m.angular_velocity = _v3(sd["angular_velocity"])
		var r := _dock_autopilot(m, _v3(sd["aim"]), _v3(sd["omega_ff"]),
			float(sd["throttle"]))
		var want: Dictionary = sd["throttles"]
		var e := absf(float(r[1]) - float(sd["pointing_error_deg"]))
		for key in want.keys():
			e = maxf(e, absf(float((r[0] as Dictionary).get(key, -1.0))
				- float(want[key])))
		worst_a = maxf(worst_a, e)
		if e > 1e-9:
			bad_a += 1
	print("  %s  attitude                 %d of %d samples match, worst "
		% ["PASS" if bad_a == 0 else "FAIL", att.size() - bad_a, att.size()]
		+ "|delta| %s" % _sci(worst_a))
	_drift = ""
	var ok := bad_g == 0 and bad_a == 0
	if drift != "":
		# INVERTED. A drifted port that still matches means the comparison is
		# inert, and an inert comparison is worse than none because it is
		# reported as a pass.
		if ok:
			print("CONTROL DID NOT FIRE -- drift=%s changed nothing the "
				% drift + "comparison can see. This is a FAILURE.")
			return false
		print("CONTROL FIRED: %d guidance and %d attitude samples went red "
			% [bad_g, bad_a] + "under drift=%s." % drift)
		return true
	print("%d guidance and %d attitude samples match the Python law"
		% [gs.size(), att.size()])
	return ok


## Set only by `--dock-selftest --drift=`. Never in flight.
var _drift: String = ""


func _sample(t: float, m: FlightModel, phase: String) -> Dictionary:
	return {
		"t_s": t, "phase": phase,
		"position": [m.position.x, m.position.y, m.position.z],
		"velocity": [m.velocity.x, m.velocity.y, m.velocity.z],
		"orientation": [m.orientation.w, m.orientation.x, m.orientation.y,
			m.orientation.z],
		"angular_velocity": [m.angular_velocity.x, m.angular_velocity.y,
			m.angular_velocity.z],
		"speed": m.speed(),
	}


## Point the nose at `aim` and, once it is roughly there, open the mains.
##
## A FINDING, and it belongs here rather than in a note: `aurora_thrusters()`
## produces torque from THE FOUR MAINS ONLY. Every RCS thruster in the layout
## fires straight through the centre of mass -- `rcs_lat_r` sits at
## (3.4, 0, 0) and pushes along -X, so its moment arm is parallel to its thrust
## and its torque is identically zero -- and the mains, being on the aft
## centreline of each boom, produce torque about X and Y and NONE about Z.
## Two consequences the pilot feels: there is no roll authority at all, and
## every rotation is also a shove, because turning means running two of the
## four mains. The autopilot is written to that layout rather than around it,
## and the roll axis is simply never commanded.
func _autopilot(m: FlightModel, aim: Vector3, throttle: float) -> Dictionary:
	var f := m.forward()
	var axis := f.cross(aim)
	var ang := atan2(axis.length(), f.dot(aim))
	var err := Vector3.ZERO
	if axis.length() > 1e-12:
		err = m.world_to_body(axis.normalized()) * ang
	# Proportional-derivative, with the derivative in body frame where the
	# angular velocity already is. Gains are set so a 180 degree flip settles
	# in about four seconds, which is what the braking margin above is priced
	# against.
	var rot := err * 0.9 - m.angular_velocity * 2.2
	rot.z = 0.0                              # no roll authority; see above
	if rot.length() > 1.0:
		rot = rot.normalized()
	var thr := throttle if ang < deg_to_rad(12.0) else 0.0
	return m.allocate(Vector3(0.0, 0.0, thr), rot)


# ===========================================================================
# THE DOCK -- a port of station/physics/docking.py
# ===========================================================================
## Docking is the launch run backwards, and the hard part is that the bay is
## rotating. The launch already rides the bay and lets go at the right phase;
## the dock has to MATCH that phase from outside -- arrive on the bay's own
## circle, at its angular rate, at the right angle, with a closing velocity the
## airframe can null.
##
## THE WHOLE LAW IS `station/physics/docking.py` AND THIS IS A PORT OF IT, which
## makes it a liability until it is checked. `--dock-selftest` replays 48
## guidance samples and 16 attitude samples recorded from the Python module and
## compares component by component at 1e-9. Open loop, deliberately: the mission
## below flies the same law in a feedback loop, and a feedback loop HIDES a
## mis-ported gain by correcting for it -- the trajectory comes out nearly right
## and the law is wrong.
##
## Every constant comes out of `launch.json`'s `dock` block. Not one of them is
## written here, because a constant duplicated across a language boundary is a
## constant that drifts.

var _dock: Dictionary = {}


func _dk(key: String, fallback: float = 0.0) -> float:
	return float(_dock.get(key, fallback))


## Python's `unit()` multiplies by the reciprocal; Godot's `normalized()`
## divides. They differ in the last bit of a double, which is below any physical
## significance and ABOVE the 1e-9 the sample comparison runs at -- and that is
## deliberate, because the comparison is asking whether this is the same
## algorithm, not whether it is approximately right. `allocate` already carries
## the same note.
func _unit(v: Vector3) -> Vector3:
	var n := v.length()
	return Vector3.ZERO if n == 0.0 else v * (1.0 / n)


func _clip(v: Vector3, cap: float) -> Vector3:
	var n := v.length()
	return v if n <= cap else v * (cap / n)


## Position, velocity and acceleration of a point held `standoff` off the bay
## while closing on it at `closing` m/s. Differentiated, not guessed:
## with p = R(t) n(t), R' = -closing and n' = omega * tangent,
##     v = -closing n + omega R t
##     a = -omega^2 R n - 2 closing omega t
## The second acceleration term is the Coriolis term of a radial closure and it
## is the one a careless port drops.
func _dock_target(t: float, standoff: float, closing: float) -> Array:
	var ang := float(_dock["bay_phase"]) + float(_dock["omega"]) * t
	var n := Vector3(cos(ang), sin(ang), 0.0)
	var tg := Vector3(-sin(ang), cos(ang), 0.0)
	var w: float = float(_dock["omega"])
	var r: float = float(_dock["bay_radius"]) + standoff
	# NEGATIVE CONTROL ONLY: the Coriolis term of a radial closure, 0.56 m/s^2
	# at the plan's closing rate. Dropping it is the single most plausible port
	# mistake in this function, and it is a term nobody would notice missing
	# from a trajectory plot.
	var cor := 0.0 if _drift == "nocoriolis" else -2.0 * closing * w
	return [Vector3(r * n.x, r * n.y, float(_dock["bay_z"])),
		tg * (w * r) + n * (-closing),
		n * (-w * w * r) + tg * cor]


## Where the craft waits for the bay, on ITS OWN azimuth.
##
## A point on the hold circle is doing 68.5 m/s and costs 12.9 m/s^2 to stay on;
## a point FIXED IN INERTIAL SPACE on the same circle costs nothing, and the bay
## arrives at it within one 33.47 s rotation whatever the craft does. The launch
## is a craft at rest in the ROTATING frame being thrown clear; the dock is a
## craft at rest in the INERTIAL frame being caught.
##
## The azimuth is the craft's own and that is a hull-clearance result rather
## than a preference: measured along the straight line from the look-back point,
## aiming at the hold point at the BAY's phase clears the hull by -11.6 m -- it
## goes through the station -- and the same radius on the craft's own azimuth
## clears by +96.5 m.
func _loiter_point(pos: Vector3) -> Vector3:
	var th := atan2(pos.y, pos.x)
	var r: float = _dk("hold_radius_m")
	return Vector3(r * cos(th), r * sin(th), float(_dock["bay_z"]))


func _stage_target(stage: String, t: float, standoff: float,
		loiter: Vector3) -> Array:
	if stage == "return" or stage == "loiter":
		return [loiter, Vector3.ZERO, Vector3.ZERO]
	return _dock_target(t, standoff,
		_dk("closing_rate_m_s") if stage == "terminal" else 0.0)


## The guidance law: one gain, two feedforwards.
##
##     a = a_target(t) + vel_gain * (v_desired - v)
##     v_desired = unit(target - pos) * vcap + v_target(t)
##
## VELOCITY MATCHING, NOT PURSUIT, for the reason the transit leg above records:
## a closing-rate test cannot see LATERAL velocity. AND THE TARGET'S OWN
## ACCELERATION IS FED FORWARD, which is what makes the equilibrium the circle
## rather than a straight line -- without it, sitting exactly on the hold point
## with exactly the hold point's velocity gives zero command and the craft flies
## straight while the hold point curves away.
##
## `phase_match=false` is the negative control: it drops the target's velocity
## and acceleration, which is docking with a rotating station as though it were
## not rotating, and the craft misses by 298 m.
func _dock_command(t: float, pos: Vector3, vel: Vector3, standoff: float,
		target: Array, phase_match: bool = true) -> Array:
	var p: Vector3 = target[0]
	var v: Vector3 = target[1] if phase_match else Vector3.ZERO
	var a: Vector3 = target[2] if phase_match else Vector3.ZERO
	# NEGATIVE CONTROL ONLY. `nophase` drops the target's VELOCITY feedforward
	# and keeps its acceleration -- a subtler mistake than `phase_match=false`,
	# and one a port makes by forgetting a single `+ v`.
	if _drift == "nophase":
		v = Vector3.ZERO
	var dp := p - pos
	var d := dp.length()
	# NO STANDOFF SUBTRACTED FROM THE BRACHISTOCHRONE. The transit leg above
	# uses `sqrt(2 * 0.7 * amax * (d - 100))` because it means to stop short of
	# its waypoint. Written that way here it read zero for every d under the
	# capture range, which took the WHOLE cap to zero -- it is a min -- and
	# removed the position feedback: the craft then settled 14.26 m from the bay
	# and held it, because a law with no position term has a perfect equilibrium
	# at any offset whose velocity matches.
	var amax: float = _dk("max_accel_m_s2")
	var vcap: float = minf(_dk("cruise_vmax_m_s"), minf(
		sqrt(2.0 * _dk("brachistochrone_derate") * amax * d),
		_dk("terminal_taper") * d))
	var v_des := _unit(dp) * vcap + v
	return [_clip(a + (v_des - vel) * _dk("vel_gain"), amax), d,
		(v - vel).length()]


## Point the nose at `aim`, tracking a demand that is itself rotating.
##
## THE FEEDFORWARD IS THE DIFFERENCE BETWEEN DOCKING AND NOT. A docking craft's
## thrust vector rotates with the station, 10.75 deg/s, once every 33.47 s. A
## pure PD tracking that settles where `kp * error = kd * rate`, i.e. at a
## standing error of kd/kp * omega = 26 degrees -- past the thrust gate, so the
## mains never light and the craft never docks. Measured before the feedforward:
## the pointing error pinned at exactly 25.0 deg, the gate value, for the whole
## approach. After it: 0.0-0.5 deg.
##
## `rot.z` is zeroed because the layout has no roll authority; see `_autopilot`.
func _dock_autopilot(m: FlightModel, aim: Vector3, omega_ff: Vector3,
		throttle: float) -> Array:
	var f := m.forward()
	var axis := f.cross(aim)
	var ang := atan2(axis.length(), f.dot(aim))
	var err := Vector3.ZERO
	if axis.length() > 1e-12:
		err = m.world_to_body(_unit(axis)) * ang
	# NEGATIVE CONTROL ONLY: the one number that makes docking work.
	var w_ff := m.world_to_body(
		Vector3.ZERO if _drift == "noattff" else omega_ff)
	var rot := err * _dk("att_kp") - (m.angular_velocity - w_ff) * _dk("att_kd")
	rot.z = 0.0
	if rot.length() > 1.0:
		rot = _unit(rot)
	var thr := throttle if ang < deg_to_rad(_dk("thrust_gate_deg")) else 0.0
	return [m.allocate(Vector3(0.0, 0.0, thr), rot), rad_to_deg(ang)]


## The station's own radius at z, from the profile `launch.json` carries.
##
## SAMPLED FROM `components.radius_at`, the function the hull mesh is built
## from, at 20.17 m -- so a craft that measures its clearance here and the hull
## a player looks at cannot disagree about where the station is. Nothing in this
## model collides, so without this a law that flies THROUGH the station reports
## a clean miss distance and reads as merely inaccurate.
func _hull_radius_at(z: float) -> float:
	var hp: Dictionary = _launch.get("hull_profile", {})
	if hp.is_empty():
		return 0.0
	var radii: Array = hp["radii"]
	var u := (z - float(hp["z0"])) / float(hp["step"])
	if u <= 0.0 or u >= float(radii.size() - 1):
		return 0.0                       # off either end: no station to hit
	var i := int(floor(u))
	var f := u - float(i)
	return lerpf(float(radii[i]), float(radii[i + 1]), f)


func _look_quat(fwd: Vector3, up: Vector3) -> Quaternion:
	var z := fwd.normalized()
	var x := up.cross(z)
	if x.length() < 1e-9:
		x = Vector3(0.0, 0.0, 1.0).cross(z)
	x = x.normalized()
	var y := z.cross(x)
	return Basis(x, y, z).get_rotation_quaternion()


## Where the camera sits when it is not in the cockpit.
##
## Offset in the SHIP'S frame, not the world's, so the framing is the same
## whatever attitude the flight ends in. Astern and above is a chase view; the
## lateral offset is what stops the fighter from sitting exactly on top of the
## thing it was flown out to photograph.
const CHASE := Vector3(9.0, 7.0, -46.0)


func _chase_eye(m: FlightModel) -> Vector3:
	return m.position + m.body_to_world(CHASE)


# ===========================================================================
# The world
# ===========================================================================

## Borrow the look from `scenes/exterior.tscn` rather than restating it.
##
## THE LOOK IS ONE JUDGEMENT AND IT LIVES IN ONE FILE. exterior.tscn carries the
## calibrated exposure (0.43, measured against the show at this framing), the
## ambient, the tonemapper, the three-point rig and 36 material rules written by
## `station/materials.py --export`. Copying any of it here would create a second
## copy that drifts silently -- the failure this project has written down twice.
## So the scene is INSTANTIATED AND NOT ADDED TO THE TREE (so its own _ready
## never runs and never quits us), its environment and lights are reparented
## into this scene, its `_apply_materials` is called on our geometry, and the
## husk is freed.
func _build_world() -> void:
	_world = Node3D.new()
	_world.name = "World"
	add_child(_world)
	_proto = load("res://scenes/exterior.tscn").instantiate()
	for n in ["WorldEnvironment", "Sun", "Fill", "Rim"]:
		var node := _proto.get_node_or_null(NodePath(n))
		if node == null:
			push_warning("starfury: exterior.tscn has no %s" % n)
			continue
		# Unset the owner first. A node reparented out of an instanced scene
		# keeps pointing at that scene's root, and Godot warns on every one of
		# them -- four lines of noise in a log this project greps for real
		# errors.
		node.owner = null
		_proto.remove_child(node)
		add_child(node)
	_aim_rig()

	var loaded := 0
	if hull_glb != "" and FileAccess.file_exists(hull_glb):
		var hull := _load_glb(hull_glb)
		if hull != null:
			_world.add_child(hull)
			loaded += _proto._apply_materials(hull)
	else:
		push_warning("starfury: no hull at %s -- the station will not be in "
			% hull_glb + "the frame. Run tools/export_scene.py --shot exterior.")
	print("starfury: %d station mesh instances" % loaded)


## The three-point rig, aimed from the shot exactly as `render_shot.gd` aims it.
##
## The positions come from `station/starfury_scene.py`, which computes them with
## `tools/export_scene.py`'s own formulas, so the key sits where the exterior
## shot's key sits. What is NOT copied is the energies and colours: those are
## properties of the light nodes, and the light nodes are the exterior scene's
## own, reparented.
func _aim_rig() -> void:
	var at := _v3(_shot.get("sun_at", [0.0, 0.0, 4023.0]))
	for pair in [["Sun", "sun_from"], ["Rim", "rim_from"], ["Fill", "fill_from"]]:
		var node := get_node_or_null(NodePath(String(pair[0]))) as DirectionalLight3D
		if node == null:
			continue
		if not _shot.has(String(pair[1])):
			node.visible = false
			continue
		node.global_position = _v3(_shot[String(pair[1])])
		node.look_at(at, Vector3.UP)
	var sun := get_node_or_null(^"Sun") as DirectionalLight3D
	if sun != null:
		sun.directional_shadow_max_distance = 20000.0


func _load_glb(path: String) -> Node:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	if doc.append_from_file(path, state) != OK:
		push_error("starfury: glTF load failed for %s" % path)
		return null
	return doc.generate_scene(state)


func _spawn_ship() -> void:
	_ship = Node3D.new()
	_ship.name = "Starfury"
	_world.add_child(_ship)
	if fury_glb != "" and FileAccess.file_exists(fury_glb):
		var mesh := _load_glb(fury_glb)
		if mesh != null:
			_ship.add_child(mesh)
			if _proto != null:
				_proto._apply_materials(mesh)
	else:
		push_error("starfury: no airframe at %s -- run "
			% fury_glb + "station/starfury_scene.py --build")
	_cam = Camera3D.new()
	_cam.fov = 46.0
	_cam.near = 0.5
	_cam.far = 200000.0
	_cam.current = true
	add_child(_cam)
	# The husk has given up everything it had. Freed rather than left in
	# memory because a node that is never in the tree and never freed is a
	# leak Godot reports at exit, and this project's render log filter hides
	# exactly those lines.
	if _proto != null:
		_proto.free()
		_proto = null


## Rebase the scene near the viewer before anything is narrowed to float32.
##
## The engine is built precision=double (ADR 0001), so the SIMULATION is fine at
## 11 km. The GPU is not: rendering narrows to float32 whatever the CPU used,
## and `station/physics/floating_origin.py` measures the spacing between
## representable float32 values at 3.91 mm at 50 km and about 0.5 mm at 8 km --
## visible shimmer on a stationary hull. Rebasing costs one transform on two
## roots and removes it.
func _rebase_if_needed(viewer: Vector3) -> void:
	if (viewer - _origin).length() <= 500.0:
		return
	_origin = viewer
	_rebases += 1


func _place(world_pos: Vector3) -> Vector3:
	return world_pos - _origin


## Spacing between representable float32 values at distance x, in metres.
## `station/physics/floating_origin.py` computes the same thing by bit-twiddling
## a struct; here it is the exponent, which is the same number and needs no
## byte packing. Reported by the readout so the rebase is visible as a NUMBER
## rather than as an assurance.
func _f32_spacing(x: float) -> float:
	x = absf(x)
	if x < 1e-30:
		return 0.0
	return pow(2.0, floor(log(x) / log(2.0)) - 23.0)


func _eye_world() -> Vector3:
	if _chase:
		return _chase_eye(model)
	# The cockpit. `starfury_geometry.cockpit_volume()` puts the tub forward
	# and high in the fuselage; the pilot STANDS in it, braced against a near
	# vertical couch (reference/12-starfury/, catalogued session 3j), so the
	# eye is high rather than reclined.
	return model.position + model.body_to_world(Vector3(0.0, 1.05, 1.35))


func _sync_transforms() -> void:
	var eye := _eye_world()
	_rebase_if_needed(eye)
	_world.position = -_origin
	if _ship != null:
		_ship.transform = Transform3D(Basis(model.orientation), model.position)
	if _cam == null:
		return
	_cam.global_position = _place(eye)
	var look: Vector3
	if _chase:
		# AHEAD OF THE SHIP, not at it. Aiming at the hull puts the fighter
		# dead centre and whatever it is flying towards behind it; aiming where
		# it is pointing puts the subject in the middle of the frame and the
		# fighter in the near corner, which is the shot.
		look = _place(model.position + model.forward() * 300.0)
	else:
		look = _place(model.position + model.body_to_world(
			Vector3(0.0, 0.0, 400.0)))
	# Up is the SHIP'S up, not the world's. There is no world up in vacuum, and
	# using Vector3.UP puts the horizon back into a game that does not have one.
	_cam.look_at(look, model.body_to_world(Vector3(0.0, 1.0, 0.0)))


# ===========================================================================
# The photograph
# ===========================================================================

## Fly the mission, freeze it at the named beat, and photograph it.
##
## THE FRAME IS TAKEN FROM WHERE THE FLIGHT ENDED UP, not from a camera anyone
## chose. That is the whole reason this mode exists rather than a static
## `--eye`: a shot composed by hand says nothing about whether the ship can get
## there, and this project has a scar for exactly that shape of evidence.
func _photograph(which: String) -> void:
	var flight := _fly_mission()
	var pick: Dictionary = flight.get("lookback", flight["final"])
	if which == "dock":
		pick = flight["final"]
	elif which == "release":
		# The FIRST coast sample, a twelfth of a second after the clamps let
		# go: the fighter is still in the bay's mouth and the hull it is
		# leaving is the frame. The last one is six seconds and 150 m later,
		# by which time the station is a wall behind it and the launch is over.
		pick = _pick_sample(flight, "coast", true)
	elif which == "ride":
		pick = _pick_sample(flight, "ride", true)
	model.position = _v3(pick["position"])
	model.velocity = _v3(pick["velocity"])
	var q = pick["orientation"]
	model.orientation = Quaternion(float(q[1]), float(q[2]), float(q[3]),
		float(q[0])).normalized()
	_chase = true
	_sync_transforms()
	if which != "lookback" and which != "dock":
		# THE LAUNCH BEAT NEEDS A DIFFERENT CAMERA, and the reason is where the
		# fighter is pointing. A cobra bay tube points radially OUT, so at
		# release the nose is aimed at empty space and the station is directly
		# behind the craft: a chase camera astern of it is inside the hull. The
		# camera therefore stands OUTBOARD of the fighter, up the radius, and
		# looks back down it -- which puts the fighter in the near field and
		# the 8 km hull it just left filling everything under it.
		#
		# `up` is the outward radial, so "down" in this frame is toward the
		# spin axis. That is the only up there is here and it is the one the
		# pilot has.
		var outward := Vector3(model.position.x, model.position.y,
			0.0).normalized()
		# AIM STRAIGHT DOWN THE RADIUS, at the hull directly under the bay.
		# The first three attempts aimed along the axis as well, and the
		# fighter came out clipped by the bottom of the frame every time. The
		# reason is worth the line: with `up` set to the outward radial, a
		# camera offset along +Z and an aim point offset along -Z put the
		# fighter FURTHER inboard than the aim axis, which is screen-down.
		# Aiming perpendicular to the axis removes that term entirely and the
		# fighter sits about ten degrees above centre.
		var inboard := Vector3(0.0, 0.0, model.position.z)
		_cam.fov = 60.0
		_cam.global_position = _place(model.position + outward * 52.0
			+ Vector3(0.0, 0.0, 10.0))
		_cam.look_at(_place(model.position.lerp(inboard, 0.6)), outward)
	print("starfury: camera at %s, ship at %s (%s)"
		% [_cam.global_position + _origin, model.position, which])
	for i in 10:
		await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(_out_path.get_base_dir())
	if img.save_png(_out_path) != OK:
		push_error("starfury: save_png failed for %s" % _out_path)
		get_tree().quit(2)
		return
	print("captured %s  %dx%d" % [_out_path, img.get_width(), img.get_height()])
	get_tree().quit(0)


func _pick_sample(flight: Dictionary, phase: String,
		first: bool = false) -> Dictionary:
	var hit: Dictionary = flight["final"]
	var found := false
	for s in flight["samples"]:
		if String(s["phase"]) != phase:
			continue
		if first and found:
			continue
		hit = s
		found = true
	return hit


# ===========================================================================
# Flying it yourself
# ===========================================================================

func _start_interactive() -> void:
	var bay: Dictionary = _launch.get("bay", {})
	if not bay.is_empty():
		var omega := float(_launch["omega_rad_s"])
		var r := float(bay["mouth_radius_m"])
		var ph := float(bay["phase_rad"])
		model.position = Vector3(r * cos(ph), r * sin(ph), float(bay["z_m"]))
		model.velocity = Vector3(-omega * model.position.y,
			omega * model.position.x, 0.0)
		model.orientation = _look_quat(Vector3(cos(ph), sin(ph), 0.0),
			Vector3(0.0, 0.0, 1.0))
	_spawn_world = model.position
	var layer := CanvasLayer.new()
	add_child(layer)
	_readout = Label.new()
	_readout.position = Vector2(16, 12)
	_readout.add_theme_font_size_override("font_size", 15)
	layer.add_child(_readout)
	_sync_transforms()
	set_physics_process(true)
	print("starfury: free flight. %s" % KEY_HELP)


## Six axes, and no autopilot on any of them.
##
## THE INERTIA IS THE POINT. Nothing here damps velocity, nothing turns the nose
## into the direction of travel, and releasing every key leaves the craft doing
## exactly what it was doing. X is a KILL-VELOCITY key rather than a brake
## because in vacuum there is no such thing as a brake: it points the nose
## retrograde and burns, which is what a pilot does and takes as long as it
## takes.
func _read_pilot_input() -> Dictionary:
	var keys := {}
	for k in [KEY_W, KEY_S, KEY_A, KEY_D, KEY_R, KEY_F, KEY_UP, KEY_DOWN,
			KEY_LEFT, KEY_RIGHT, KEY_SPACE, KEY_X]:
		if Input.is_key_pressed(k):
			keys[k] = true
	return _command_from_keys(keys)


## THE MAPPING ITSELF, SPLIT OUT SO IT CAN BE TESTED. `Input.is_key_pressed`
## cannot be driven headlessly, and a control scheme nobody can test is one
## that silently stops working -- exactly the scar `scripts/walk.gd`'s header
## records. `--pilot-test` drives this with a scripted key sequence.
func _command_from_keys(keys: Dictionary) -> Dictionary:
	var trans := Vector3.ZERO
	var rot := Vector3.ZERO
	if keys.has(KEY_W):
		trans.z += 1.0
	if keys.has(KEY_S):
		trans.z -= 1.0
	if keys.has(KEY_D):
		trans.x += 1.0
	if keys.has(KEY_A):
		trans.x -= 1.0
	if keys.has(KEY_R):
		trans.y += 1.0
	if keys.has(KEY_F):
		trans.y -= 1.0
	# THE ATTITUDE KEYS COMMAND A RATE, NOT A TORQUE, and that is a
	# playability decision with a measured reason. Wired straight to torque,
	# two seconds on the yaw key spun the craft to 720 deg/s -- correct for a
	# layout whose four mains have 3.4 m of leverage each, and unflyable. A
	# rate command with a 60 deg/s ceiling is what every space sim does and it
	# changes NOTHING about the physics: the demand still goes through
	# `allocate`, the thrusters still saturate, and the craft still has to
	# fight its own inertia to get there.
	#
	# WITH NO ATTITUDE KEY HELD THE DEMAND IS ZERO, not "damp to zero". Taking
	# your hands off leaves the craft rotating at whatever rate it had, because
	# nothing in vacuum stops it. SPACE is the key that stops it, and it is a
	# manoeuvre like any other.
	var rate := Vector3.ZERO
	var attitude_held := false
	for pair in [[KEY_UP, Vector3(1.0, 0.0, 0.0)], [KEY_DOWN, Vector3(-1.0, 0.0, 0.0)],
			[KEY_LEFT, Vector3(0.0, 1.0, 0.0)], [KEY_RIGHT, Vector3(0.0, -1.0, 0.0)]]:
		if keys.has(pair[0]):
			rate += (pair[1] as Vector3) * PILOT_RATE
			attitude_held = true
	if attitude_held:
		rot = (rate - model.angular_velocity) * 1.2
	elif keys.has(KEY_SPACE):
		rot = -model.angular_velocity * 3.0
	if keys.has(KEY_X) and model.speed() > 0.5:
		return _autopilot(model, -model.velocity.normalized(), 1.0)
	rot.z = 0.0
	if rot.length() > 1.0:
		rot = rot.normalized()
	return model.allocate(trans, rot)


## Fly the ship from a scripted key sequence and report what a pilot got.
##
## THE ASSERTION IS DISTANCE COVERED AND DECOUPLING, not "did it move".
## `station/walkable.py` learned that four one-second nudges prove a body is
## not wedged and prove nothing about whether you can go anywhere; the same
## applies here, with a second question a walk test does not have -- whether
## turning the nose moved the velocity, which is the whole premise of the
## craft. Both are printed as numbers and both have a stated floor.
func _pilot_test() -> bool:
	model = FlightModel.new()
	var dt := 1.0 / 60.0
	var script := [
		[3.0, {KEY_W: true}, "mains ahead"],
		[2.0, {KEY_LEFT: true}, "yaw left, no thrust"],
		[2.0, {}, "hands off"],
		[2.0, {KEY_D: true}, "lateral RCS, starboard"],
		[2.0, {KEY_R: true}, "vertical RCS, up"],
		[2.0, {KEY_SPACE: true}, "kill rotation"],
		[16.0, {KEY_X: true}, "kill velocity"],
	]
	var travelled := 0.0
	var ok := true
	var v_before_turn := Vector3.ZERO
	var turn_drift := 0.0
	var swept := 0.0
	for leg in script:
		var secs: float = leg[0]
		var keys: Dictionary = leg[1]
		var v0 := model.velocity
		var p0 := model.position
		var f0 := model.forward()
		var prev := model.forward()
		var steps := int(secs / dt)
		for i in steps:
			model.step(dt, _command_from_keys(keys))
			var d := prev.dot(model.forward())
			swept += rad_to_deg(acos(clampf(d, -1.0, 1.0)))
			prev = model.forward()
		travelled += (model.position - p0).length()
		if String(leg[2]).begins_with("yaw"):
			v_before_turn = v0
			turn_drift = (model.velocity - v0).length()
		print("  %-24s  speed %7.2f m/s  spin %6.2f deg/s  nose %6.1f deg "
			% [String(leg[2]), model.speed(),
				rad_to_deg(model.angular_velocity.length()),
				rad_to_deg(acos(clampf(f0.dot(model.forward()), -1.0, 1.0)))]
			+ "off velocity %6.1f"
			% [rad_to_deg(model.velocity.normalized().angle_to(model.forward()))
				if model.speed() > 0.01 else 0.0])
	print("  nose swept %.0f deg in total; travelled %.0f m" % [swept, travelled])
	# 1. A pilot can go somewhere. Three seconds of mains at 18.4 m/s^2 is
	#    83 m before anything else happens; the whole run must beat 300 m or
	#    the controls are not connected to the craft.
	if travelled < 300.0:
		print("  FAIL  travelled only %.0f m -- the controls move nothing"
			% travelled)
		ok = false
	# 2. Turning does not steer. The yaw leg commands attitude and no
	#    translation, so the velocity may change ONLY by the thrust the four
	#    mains unavoidably produce while torquing (see _autopilot) -- which is
	#    along the nose, not toward it. An aeroplane-shaped controller would
	#    move it by tens of m/s.
	if turn_drift > 25.0:
		print("  FAIL  yawing moved the velocity by %.1f m/s" % turn_drift)
		ok = false
	# 3. And it can stop, which in vacuum is a manoeuvre rather than a brake.
	if model.speed() > 2.0:
		print("  FAIL  kill-velocity left %.2f m/s" % model.speed())
		ok = false
	print("  yaw leg moved the velocity %.2f m/s (from %.2f m/s), final speed "
		% [turn_drift, v_before_turn.length()] + "%.3f m/s" % model.speed())
	print("PILOT TEST: " + ("PASS" if ok else "FAIL"))
	return ok


## Where the craft started, for the free-flight distance report.
var _spawn_world: Vector3 = Vector3.ZERO


func _launch_origin() -> Vector3:
	return _spawn_world


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and (event as InputEventKey).pressed \
			and not (event as InputEventKey).echo \
			and (event as InputEventKey).keycode == KEY_TAB:
		_chase = not _chase


func _physics_process(delta: float) -> void:
	if model == null or _readout == null:
		return
	_elapsed += delta
	model.step(delta, _read_pilot_input())
	_sync_transforms()
	var centre := _v3(_shot.get("sun_at", [0.0, 0.0, 4023.0]))
	var to_c := centre - model.position
	var drift := rad_to_deg(model.velocity.normalized().angle_to(model.forward())) \
		if model.speed() > 0.01 else 0.0
	_readout.text = ("t %6.1f s\nposition  %9.1f %9.1f %9.1f m\n"
		% [_elapsed, model.position.x, model.position.y, model.position.z]
		+ "velocity  %9.1f %9.1f %9.1f m/s\nspeed     %9.1f m/s\n"
		% [model.velocity.x, model.velocity.y, model.velocity.z, model.speed()]
		+ "nose off velocity %5.1f deg   spin %5.2f deg/s\n"
		% [drift, rad_to_deg(model.angular_velocity.length())]
		+ "range to station centre %8.0f m\n"
		% [to_c.length()]
		+ "floating origin %.0f,%.0f,%.0f  rebases %d  float32 spacing here "
		% [_origin.x, _origin.y, _origin.z, _rebases]
		+ "%.2f mm, after rebase %.4f mm\n"
		% [_f32_spacing(model.position.length()) * 1000.0,
			_f32_spacing(maxf(1.0, (model.position - _origin).length())) * 1000.0]
		+ KEY_HELP)
