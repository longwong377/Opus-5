extends Node3D
## Render one shot offscreen and write a PNG.
##
## There is no GPU and no human reviewer, so this is the whole aesthetic
## feedback loop: Mesa lavapipe rasterises on the CPU under Xvfb, the frame is
## saved, and the PNG is read back directly. See CLAUDE.md, "Verification".
##
## Everything that varies between shots -- geometry, camera, lights -- arrives
## in a scene.json written by tools/export_scene.py. Everything that is a LOOK
## -- environment, tonemapping, the key light -- lives in the .tscn that has
## this script attached, because a look has to be judged as a whole and a look
## split across a Python file and a scene file cannot be.
##
## Geometry is loaded at RUNTIME through GLTFDocument rather than imported as a
## project resource. That keeps 30 MB of regenerated binary out of the Godot
## project, removes the several-minute `--import` pass from every render, and
## means a shot can point at any .glb on disk without the project knowing about
## it in advance.

## Mesh-name fragment -> Material. Longest match wins, so "greeble_nav_light"
## beats "greeble_". Substring rather than prefix because glTF node names pick
## up decoration on some paths. Set per-scene in the .tscn.
@export var material_rules: Dictionary = {}
## Applied to any mesh no rule matches. On the exterior that is the hull, which
## is most of the model; inside the drum it should never be used at all, and
## `tools/export_scene.py` asserts that it is not.
@export var fallback_material: Material
## Frames drawn before the capture. NoiseTexture2D generates on a worker
## thread, so capturing immediately gets flat placeholder albedo instead of the
## weathering -- a difference that reads as "the material is wrong".
@export var warmup_frames: int = 6
## Scale on every light loaded from scene.json. The lights themselves are
## derived geometry (see export_scene.light_runs); this is the exposure knob
## for them, and it lives with the environment because that is what it is
## judged against.
@export var light_gain: float = 1.0
## Shadow settings for the omnis that are allowed to cast. Kept low because an
## omni shadow is a cube map and this renderer is a CPU.
@export var omni_shadow_bias: float = 0.08

var _shot: Dictionary = {}
var _out_path: String = ""


func _ready() -> void:
	var args := _parse_args()
	if not args.has("scene-json"):
		push_error("render_shot: --scene-json is required")
		get_tree().quit(2)
		return

	var f := FileAccess.open(args["scene-json"], FileAccess.READ)
	if f == null:
		push_error("render_shot: cannot open %s" % args["scene-json"])
		get_tree().quit(2)
		return
	var parsed = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("render_shot: %s is not a JSON object" % args["scene-json"])
		get_tree().quit(2)
		return
	_shot = parsed
	_out_path = args.get("out", _shot.get("out_png", ""))
	if _out_path == "":
		push_error("render_shot: no output path")
		get_tree().quit(2)
		return

	if args.has("warmup"):
		warmup_frames = int(args["warmup"])
	if args.has("light-gain"):
		light_gain = float(args["light-gain"])
		# Scale the SCENE's own lights too, not only the light runs the shot
		# JSON carries. The exterior shot has "lights": 0 -- its key, fill and
		# rim are DirectionalLight3D nodes in exterior.tscn -- so --light-gain
		# was a documented flag that did exactly nothing there, and two renders
		# an order of magnitude apart in gain came back byte-identical. That
		# matters beyond tidiness: with no way to turn the rig down there is no
		# way to see whether an emissive material emits, and the rig is built so
		# that a rim kicker always lights the camera-facing edge.
		_scale_scene_lights(self, light_gain)
	if args.has("no-ssao"):
		var env := ($WorldEnvironment as WorldEnvironment).environment
		env.ssao_enabled = false
		env.ssil_enabled = false

	var t0 := Time.get_ticks_msec()
	_load_geometry()
	print("render_shot: geometry %d ms" % [Time.get_ticks_msec() - t0])
	_place_camera()
	_aim_sun()
	_spawn_lights()

	for i in warmup_frames:
		await RenderingServer.frame_post_draw
	_capture()
	get_tree().quit()


## `godot ... -- --scene-json=/path --out=/path` . Everything after the bare
## `--` is ours; Godot's own flags are parsed before it.
func _parse_args() -> Dictionary:
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


func _load_geometry() -> void:
	var holder := Node3D.new()
	holder.name = "Geometry"
	add_child(holder)
	var total := 0
	for path in _shot.get("glb", []):
		var doc := GLTFDocument.new()
		var state := GLTFState.new()
		var err := doc.append_from_file(String(path), state)
		if err != OK:
			push_error("render_shot: glTF load failed (%d) for %s" % [err, path])
			continue
		var scene := doc.generate_scene(state)
		holder.add_child(scene)
		total += _apply_materials(scene)
	print("render_shot: %d mesh instances over %d files"
		% [total, _shot.get("glb", []).size()])


func _material_for(mesh_name: String) -> Material:
	var best_len := -1
	var best: Material = fallback_material
	for key in material_rules:
		var frag := String(key)
		if mesh_name.contains(frag) and frag.length() > best_len:
			best_len = frag.length()
			best = material_rules[key]
	return best


func _apply_materials(root: Node) -> int:
	var n := 0
	var unmatched := {}
	for mi in _mesh_instances(root):
		# The glTF node keeps the exporter's group name; the mesh resource name
		# picks up a scene prefix. Prefer the node.
		var key := String(mi.name)
		var mat := _material_for(key)
		# Ask whether a RULE matched, not whether the result happens to equal
		# the fallback. The first version compared materials, and since the
		# drum scene's fallback is deliberately one of the real materials, it
		# reported two correctly-bound end cap courses as unbound on every
		# run -- a false alarm that would have trained the next reader to
		# ignore the warning that exists to catch the real thing.
		if not _has_rule(key):
			unmatched[key] = true
		for i in mi.mesh.get_surface_count():
			mi.set_surface_override_material(i, mat)
		n += 1
	if unmatched.size() > 0:
		# Not an error on the exterior, where the fallback IS the hull material.
		# Printed always, because a mesh silently landing on the fallback is the
		# failure a render cannot show: grey on grey.
		print("render_shot: fallback material used by %d group(s): %s"
			% [unmatched.size(), ", ".join(PackedStringArray(unmatched.keys()))])
	return n


func _has_rule(mesh_name: String) -> bool:
	for key in material_rules:
		if mesh_name.contains(String(key)):
			return true
	return false


func _mesh_instances(n: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		out.append(n)
	for c in n.get_children():
		_mesh_instances(c, out)
	return out


func _v3(a) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _place_camera() -> void:
	var cam := $Camera3D as Camera3D
	var c: Dictionary = _shot["camera"]
	cam.fov = float(c.get("fov", 46.0))
	cam.near = float(c.get("near", 1.0))
	cam.far = float(c.get("far", 200000.0))
	cam.global_position = _v3(c["eye"])
	# Inside the drum "up" is radially inward, because that is where gravity
	# is not. It comes from the shot rather than being assumed, and getting it
	# wrong puts the ground on the ceiling in a frame symmetric enough to hide
	# the mistake.
	cam.look_at(_v3(c["target"]), _v3(c.get("up", [0.0, 1.0, 0.0])))
	print("render_shot: camera at %s looking at %s"
		% [cam.global_position, _v3(c["target"])])


## Aim the whole three-point rig from the shot.
##
## Every one of these was once a hand-written 3x3 basis in the scene file, and
## the rim's basis pointed from the camera's own side at the framings actually
## used -- so it acted as a second frontal fill and the hull had no terminator
## at any sun angle. Directions that are relative to the key and to the camera
## have to be computed where the key and the camera are known.
func _aim_sun() -> void:
	var at := _v3(_shot.get("sun_at", [0, 0, 0]))
	for pair in [["Sun", "sun_from"], ["Rim", "rim_from"], ["Fill", "fill_from"]]:
		var node := get_node_or_null(String(pair[0])) as DirectionalLight3D
		if node == null:
			continue
		if _shot.get(pair[1], null) == null:
			node.visible = false
			continue
		node.global_position = _v3(_shot[pair[1]])
		# A DirectionalLight3D emits along its own -Z, and look_at points -Z at
		# the target, so a surface facing back toward the light's position is
		# the one that gets lit.
		node.look_at(at, Vector3.UP)

	# Directional shadow range has to follow the shot, and this was a real
	# defect rather than a refinement. Godot scales a directional light's
	# depth bias by the size of the world the shadow map covers, so a fixed
	# 12 km range applied to a 1.4 km close-up biased every shadow clean off
	# its caster: at a 10 degree sun a row of 40 m cargo modules on the dorsal
	# rail threw NO shadow at all, which reads as "this renderer has no
	# shadows" rather than as a tuning error.
	var sun := get_node_or_null("Sun") as DirectionalLight3D
	if sun != null and _shot.has("camera"):
		var c: Dictionary = _shot["camera"]
		var d := _v3(c["eye"]).distance_to(_v3(c["target"]))
		sun.directional_shadow_max_distance = clampf(d * 2.2, 400.0, 20000.0)


func _spawn_lights() -> void:
	var lights: Array = _shot.get("lights", [])
	if lights.is_empty():
		return
	var holder := Node3D.new()
	holder.name = "LightRuns"
	add_child(holder)
	var shadowed := 0
	for l in lights:
		var o := OmniLight3D.new()
		# Parent first, position second. global_position on a node that is not
		# yet in the tree is a no-op that logs "!is_inside_tree()" and silently
		# leaves the light at the origin -- which, inside a drum, is on the
		# spin axis inside the core tube, i.e. lighting nothing.
		holder.add_child(o)
		o.global_position = _v3(l["pos"])
		var c = l.get("colour", [1, 1, 1])
		o.light_color = Color(float(c[0]), float(c[1]), float(c[2]))
		o.light_energy = float(l.get("energy", 1.0)) * light_gain
		o.omni_range = float(l.get("range", 500.0))
		o.omni_attenuation = float(l.get("attenuation", 1.0))
		if bool(l.get("shadow", false)):
			o.shadow_enabled = true
			o.shadow_bias = omni_shadow_bias
			shadowed += 1
	print("render_shot: %d light-run sources, %d casting shadows"
		% [lights.size(), shadowed])


func _scale_scene_lights(node: Node, gain: float) -> void:
	if node is Light3D:
		(node as Light3D).light_energy *= gain
	for child in node.get_children():
		_scale_scene_lights(child, gain)


func _capture() -> void:
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(_out_path.get_base_dir())
	var err := img.save_png(_out_path)
	if err != OK:
		push_error("render_shot: save_png failed (%d) for %s" % [err, _out_path])
		return
	print("captured %s  %dx%d" % [_out_path, img.get_width(), img.get_height()])
