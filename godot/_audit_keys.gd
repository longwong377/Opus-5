extends SceneTree
## TEMPORARY AUDIT DRIVER -- walk to the first room that has anything in it,
## then try to look at it and use it, all through the real input path.

var _player: Node = null
var _interact: Node = null
var _dialogue: Node = null
var _hud: Node = null
var _phase := 0
var _f := 0
var _sweeps := 0


func _initialize() -> void:
	root.add_child(load("res://scenes/main.tscn").instantiate())


func _key(code: int, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	e.echo = false
	Input.parse_input_event(e)


func _mouse(dx: float) -> void:
	var mm := InputEventMouseMotion.new()
	mm.relative = Vector2(dx, 0)
	Input.parse_input_event(mm)


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


func _physics_process(_d: float) -> bool:
	_f += 1
	if _phase == 0:
		if _f < 90:
			return false
		_player = _find("player.gd")
		if _player == null:
			return _f > 9000
		_interact = _find("interact.gd")
		_dialogue = _find("dialogue.gd")
		_hud = _find("hud.gd")
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		print("AUDIT: mouse_mode after forcing CAPTURED = %d" % Input.mouse_mode)
		_key(KEY_UP, true)
		_phase = 1
		_f = 0
		return false

	if _phase == 1:
		# 108 s of holding forward gets into obs_dome_2
		if _f >= 6500:
			_key(KEY_UP, false)
			print("AUDIT: arrived place=%s items=%d"
				% [String(_hud.get("place_name")),
					(_interact.count() if _interact.has_method("count") else -1)])
			_phase = 2
			_f = 0
		return false

	# sweep the view a full turn, pressing E and T at every 15 degrees
	if _phase == 2:
		if _f % 30 == 0:
			_mouse(119.0)                     # ~15 deg at 0.0022 rad/px
			if _interact != null and _interact.has_method("refresh"):
				_interact.refresh()
			var g := ""
			if _interact.has_method("prompt_group"):
				g = String(_interact.prompt_group())
			var dnear := ""
			if _dialogue != null and _dialogue.has_method("report"):
				dnear = String(_dialogue.report())
			if g != "" or dnear != "prompt=-":
				print("AUDIT sweep %d yaw=%.2f prompt='%s' dialogue='%s'"
					% [_sweeps, float(_player.get("_yaw")), g, dnear])
				_key(KEY_E, true); _key(KEY_E, false)
				_key(KEY_T, true); _key(KEY_T, false)
			_sweeps += 1
		if _sweeps >= 26:
			print("AUDIT: swept %d headings; yaw=%.2f" % [_sweeps,
				float(_player.get("_yaw"))])
			_phase = 3
			_f = 0
		return false

	# step forward a little and sweep again, twice
	if _phase == 3:
		if _f == 1:
			_key(KEY_DOWN, true)              # back off 3 s
		if _f == 180:
			_key(KEY_DOWN, false)
			_sweeps = 0
			_phase = 2
			_f = 0
			print("AUDIT: backed off, sweeping again")
		return false

	print("AUDIT: DONE")
	return true
