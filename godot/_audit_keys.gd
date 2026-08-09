extends SceneTree
## TEMPORARY AUDIT DRIVER -- walk test through the REAL key path.
## Delete after use.

var _main: Node = null
var _player: Node = null
var _interact: Node = null
var _hud: Node = null
var _phase := 0
var _f := 0
var _p0 := Vector3.ZERO
var _path := 0.0
var _prev := Vector3.ZERO


func _initialize() -> void:
	root.add_child(load("res://scenes/main.tscn").instantiate())
	print("AUDIT: main.tscn instanced")


func _key(code: int, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	e.echo = false
	Input.parse_input_event(e)


func _find(cls: String, n: Node = null) -> Node:
	if n == null:
		n = root
	if n.get_script() != null and String(n.get_script().resource_path).ends_with(cls):
		return n
	for c in n.get_children():
		var r := _find(cls, c)
		if r != null:
			return r
	return null


func _report(tag: String) -> void:
	var d: float = _player.global_position.distance_to(_p0)
	var items := -1
	var press := -1
	if _interact != null:
		if _interact.has_method("count"):
			items = _interact.count()
	var place := "?"
	var near := ""
	if _hud != null:
		place = String(_hud.get("place_name"))
		near = "%s %.0fm" % [String(_hud.get("near_name")),
			float(_hud.get("near_m"))]
	print("AUDIT %s t=%.0fs straight=%.1f m path=%.1f m place=%s near=%s floor=%s items=%d"
		% [tag, _f / 60.0, d, _path, place, near,
			str(_player.is_on_floor()), items])


func _physics_process(_d: float) -> bool:
	_f += 1
	if _phase == 0:
		if _f < 90:
			return false
		_player = _find("player.gd")
		if _player == null:
			if _f > 9000:
				print("AUDIT: NO PLAYER"); return true
			return false
		_interact = _find("interact.gd")
		_hud = _find("hud.gd")
		_p0 = _player.global_position
		_prev = _p0
		print("AUDIT: start p=%.2f,%.2f,%.2f" % [_p0.x, _p0.y, _p0.z])
		_key(KEY_UP, true)
		_phase = 1
		_f = 0
		return false

	if _phase == 1:
		var now: Vector3 = _player.global_position
		_path += now.distance_to(_prev)
		_prev = now
		if _f % 600 == 0:
			_report("WALK")
		if _f >= 5400:                       # 90 s of holding the up arrow
			_key(KEY_UP, false)
			_report("WALK-END")
			_phase = 2
			_f = 0
		return false

	# turn 90 degrees left with the mouse and walk again
	if _phase == 2:
		if _f == 1:
			var mm := InputEventMouseMotion.new()
			# look_sensitivity is 0.0022 rad/px by default -> ~714 px for 90 deg
			mm.relative = Vector2(-714, 0)
			Input.parse_input_event(mm)
			print("AUDIT: yaw now %s (mouse_mode=%d)"
				% [str(_player.get("_yaw")), Input.mouse_mode])
			_p0 = _player.global_position
			_prev = _p0
			_path = 0.0
			_key(KEY_UP, true)
		if _f % 600 == 0:
			var now2: Vector3 = _player.global_position
			_path += now2.distance_to(_prev)
			_prev = now2
			_report("TURNED")
		else:
			var n3: Vector3 = _player.global_position
			_path += n3.distance_to(_prev)
			_prev = n3
		if _f >= 3600:
			_key(KEY_UP, false)
			_report("TURNED-END")
			_phase = 3
			_f = 0
		return false

	print("AUDIT: DONE")
	return true
