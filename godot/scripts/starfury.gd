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
##   --mission  [--flight-out=PATH]     fly the cobra bay launch, write flight.json
##   --out=PNG  [--frame=NAME]          fly it and photograph it
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

	if args.has("selftest"):
		get_tree().quit(0 if _selftest(String(args.get("drift", ""))) else 1)
		return

	if launch_json != "":
		_launch = _read_json(launch_json)

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

	if _out_path != "":
		await _photograph(String(args.get("frame", "lookback")))
		return
	_start_interactive()


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

	# --- riding the bay ----------------------------------------------------
	# The craft is not flying yet: it is a point on a rotating hull, and its
	# position is a function of time and nothing else. Attitude is nose-out
	# along the tube, which is the one thing about a cobra bay that is not
	# arguable -- the tube points outward.
	var prev := Vector3.ZERO
	var nose_worst := 0.0
	while t < RIDE_S:
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

	var eye := _chase_eye(m)
	var nose_err := rad_to_deg((centre - m.position).normalized()
		.angle_to(m.forward()))
	var summary := {
		"elapsed_s": t,
		"dt": dt,
		"range_m": (m.position - centre).length(),
		"peak_speed_m_s": peak,
		"final_speed_m_s": m.speed(),
		"burn_s": burn_s,
		"brake_s": brake_s,
		"unpowered_radius_gain_m": r1 - r0,
		"unpowered_radius_m": [r0, r1],
		"nose_error_deg": nose_err,
		"max_linear_accel_m_s2": m.max_linear_accel(),
	}
	print("starfury: released at %.2f m/s from r %.1f m; coasted unpowered to "
		% [release["exit_speed_m_s"], r0]
		+ "r %.0f m in %.0f s; %.0f s under power (%.0f accelerating, %.0f "
			% [r1, COAST_S, burn_s + brake_s, burn_s, brake_s]
		+ "decelerating), peak %.0f m/s; ended %.0f m from the station centre "
			% [peak, summary["range_m"]]
		+ "at %.1f m/s with the nose %.2f deg off it, after %.0f s"
			% [summary["final_speed_m_s"], nose_err, t])
	return {
		"release": release,
		"final": _sample(t, m, "final"),
		"camera": {"eye": [eye.x, eye.y, eye.z],
			"target": [centre.x, centre.y, centre.z], "fov": 46.0},
		"summary": summary,
		"samples": samples,
	}


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
const CHASE := Vector3(16.0, 12.0, -55.0)


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
	var pick: Dictionary = flight["final"]
	if which == "release":
		pick = _pick_sample(flight, "coast")
	elif which == "ride":
		pick = _pick_sample(flight, "ride")
	model.position = _v3(pick["position"])
	model.velocity = _v3(pick["velocity"])
	var q = pick["orientation"]
	model.orientation = Quaternion(float(q[1]), float(q[2]), float(q[3]),
		float(q[0])).normalized()
	_chase = true
	_sync_transforms()
	if which != "lookback":
		# Close in for the launch beat. At 55 m astern with the nose pointing
		# radially out into empty space, the frame is a fighter and nothing
		# else; what makes it a launch is the hull it just left, so the camera
		# comes in tight on the ship and aims back along the radius at the
		# station's axis.
		_cam.fov = 60.0
		_cam.global_position = _place(model.position
			+ model.body_to_world(Vector3(11.0, 4.5, -26.0)))
		_cam.look_at(_place(Vector3(0.0, 0.0, model.position.z - 900.0)),
			Vector3(0.0, 0.0, 1.0))
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


func _pick_sample(flight: Dictionary, phase: String) -> Dictionary:
	var last: Dictionary = flight["final"]
	for s in flight["samples"]:
		if String(s["phase"]) == phase:
			last = s
	return last


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
	var trans := Vector3.ZERO
	var rot := Vector3.ZERO
	if Input.is_key_pressed(KEY_W):
		trans.z += 1.0
	if Input.is_key_pressed(KEY_S):
		trans.z -= 1.0
	if Input.is_key_pressed(KEY_D):
		trans.x += 1.0
	if Input.is_key_pressed(KEY_A):
		trans.x -= 1.0
	if Input.is_key_pressed(KEY_R):
		trans.y += 1.0
	if Input.is_key_pressed(KEY_F):
		trans.y -= 1.0
	if Input.is_key_pressed(KEY_UP):
		rot.x += 1.0
	if Input.is_key_pressed(KEY_DOWN):
		rot.x -= 1.0
	if Input.is_key_pressed(KEY_LEFT):
		rot.y += 1.0
	if Input.is_key_pressed(KEY_RIGHT):
		rot.y -= 1.0
	if Input.is_key_pressed(KEY_SPACE):
		rot -= model.angular_velocity * 3.0
	if Input.is_key_pressed(KEY_X) and model.speed() > 0.5:
		return _autopilot(model, -model.velocity.normalized(), 1.0)
	rot.z = 0.0
	if rot.length() > 1.0:
		rot = rot.normalized()
	return model.allocate(trans, rot)


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
