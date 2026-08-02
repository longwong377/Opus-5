extends CharacterBody3D
## The player. A body that stands on the station and walks around it.
##
## THIS IS THE FILE THIS PROJECT SPENT ITS FIRST THREE PHASES NOT WRITING. As of
## session 3u the string `CollisionShape` appeared nowhere in the repository:
## 118 locations had geometry, materials and measured lighting, and not one of
## them had a floor in the physics sense. Every gate measured a part in
## isolation, so nothing ever failed for the absence of a player.
##
## GRAVITY POINTS OUTWARD, NOT DOWN, and that is not a detail on this station.
## The habitat drum spins; "down" for someone standing inside it is AWAY from the
## spin axis, so the gravity vector is the radial direction at the player's own
## position and it changes as they walk around the barrel. In the cylindrical
## sections it is -Y like anywhere else. `gravity_mode` selects, because a body
## walking in Blue Sector and a body walking on the drum floor are the same body
## under different fields.

## Which field this body is in. "drum" derives it from position; "deck" is -Y.
@export_enum("deck", "drum") var gravity_mode: String = "deck"
## Metres per second squared. 9.81 on a deck; the drum's own spin gravity is a
## property of the drum and is read from the schema by whoever spawns the body.
@export var gravity_m_s2: float = 9.81
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


func _ready() -> void:
	_cam = get_node_or_null("Camera3D")
	if _cam == null:
		_cam = Camera3D.new()
		_cam.name = "Camera3D"
		add_child(_cam)
	_cam.position = Vector3(0.0, eye_height_m, 0.0)
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


## The direction gravity pulls this body, as a unit vector.
##
## On a spinning drum the floor is the INSIDE of a barrel, so "down" is the
## outward radial direction from the spin axis -- the axis being +Z in this
## project's world frame. Getting this backwards is the same sign error that
## `interior.drum_interior` guards with `_inward_fraction`: a body with the sign
## wrong falls to the axis and hangs there, which looks like a physics bug and
## is a coordinate one.
func gravity_dir() -> Vector3:
	if gravity_mode == "drum":
		var radial := Vector3(global_position.x, global_position.y, 0.0)
		if radial.length() < 0.001:
			return Vector3(0, -1, 0)
		return radial.normalized()
	return Vector3(0, -1, 0)


## The body's own up, which is the opposite of the way it falls.
func body_up() -> Vector3:
	return -gravity_dir()


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


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= event.relative.x * look_sensitivity
		_pitch = clamp(_pitch - event.relative.y * look_sensitivity,
			-1.4, 1.4)
	elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


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
	var g := gravity_dir() * gravity_m_s2

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
	var fwd := Vector3(0, 0, 1) if gravity_mode == "drum" else Vector3.FORWARD
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
	global_transform.basis = Basis(right, up, -fwd).orthonormalized()

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
