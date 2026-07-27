extends Node3D
## Loads the generated station and renders it offscreen for inspection.
##
## There is no GPU and no human reviewer, so this scene exists to be rendered
## by Mesa lavapipe to a PNG that gets read back directly. It is the engine-side
## half of the verification loop described in CLAUDE.md.

@export var orbit_distance: float = 9500.0
@export var orbit_elevation_deg: float = 22.0
@export var orbit_azimuth_deg: float = 215.0
@export var target_z: float = 4023.0     ## station midpoint
## Direction the key light comes FROM, in the same spherical convention as the
## camera orbit. Aimed in code rather than as a hand-written basis in the scene:
## a DirectionalLight3D emits along its own -Z, and a 3x3 in a .tscn gives no
## hint which axis is which. Written out once, it stopped being guesswork.
@export var sun_azimuth_deg: float = 168.0
@export var sun_elevation_deg: float = 34.0
@export var shot_name: String = "engine_view"
## Mesh-name fragment -> Material. The glTF carries geometry and normals only,
## so every surface property lives here; the exporter groups triangles by
## feature and by greeble kind, which is what makes a name-keyed table
## sufficient. Matching is by substring because the importer decorates names
## (mesh resources come back as "BabylonStation_cargo_module"), and the longest
## match wins so "greeble_nav_light" beats "greeble_".
@export var material_rules: Dictionary = {}
## Used for any mesh no rule matches. The hull is most of the model, so the
## fallback is the common case rather than an error state.
@export var fallback_material: Material
## Frames rendered before capture. NoiseTexture2D generates on a worker thread;
## capturing too early gets the flat placeholder instead of the weathering.
@export var warmup_frames: int = 5

func _ready() -> void:
	_apply_materials($Station)
	_frame_camera()
	_aim_sun()
	for i in warmup_frames:
		await RenderingServer.frame_post_draw
	_capture()
	get_tree().quit()

func _material_for(mesh_name: String) -> Material:
	var best_len := -1
	var best: Material = fallback_material
	for key in material_rules:
		var frag := String(key)
		if mesh_name.contains(frag) and frag.length() > best_len:
			best_len = frag.length()
			best = material_rules[key]
	return best

func _apply_materials(root: Node) -> void:
	var applied := {}
	var meshes := _mesh_instances(root)
	for mi in meshes:
		# Node names can pick up import-time suffixes; the mesh resource keeps
		# the exporter's own group name, so prefer it and fall back to the node.
		var key := String(mi.mesh.resource_name) if mi.mesh.resource_name != "" else String(mi.name)
		var mat := _material_for(key)
		for i in mi.mesh.get_surface_count():
			mi.set_surface_override_material(i, mat)
		var label := mat.resource_name if mat else "<UNMATCHED, no fallback>"
		applied[label] = applied.get(label, 0) + 1
		print("materials: %-28s -> %s" % [key, label])
	print("materials: %d meshes over %d materials" % [meshes.size(), applied.size()])

func _mesh_instances(n: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		out.append(n)
	for c in n.get_children():
		_mesh_instances(c, out)
	return out


func _frame_camera() -> void:
	var cam := $Camera3D as Camera3D
	var az := deg_to_rad(orbit_azimuth_deg)
	var el := deg_to_rad(orbit_elevation_deg)
	var target := Vector3(0.0, 0.0, target_z)
	var offset := Vector3(
		cos(el) * cos(az),
		sin(el),
		cos(el) * sin(az)
	) * orbit_distance
	cam.global_position = target + offset
	# The station is 8 km along its own axis; using that axis as "up" would
	# stand it on end, so frame against world up and let the roll fall out.
	cam.look_at(target, Vector3.UP)
	# 8 km of station plus flight range; double precision keeps this stable.
	cam.near = 1.0
	cam.far = 200000.0

func _aim_sun() -> void:
	var sun := $Sun as DirectionalLight3D
	var az := deg_to_rad(sun_azimuth_deg)
	var el := deg_to_rad(sun_elevation_deg)
	var from := Vector3(cos(el) * cos(az), sin(el), cos(el) * sin(az)) * 20000.0
	sun.global_position = Vector3(0.0, 0.0, target_z) + from
	# look_at points -Z at the target, and -Z is the direction light travels,
	# so a surface facing back toward `from` is the one that gets lit.
	sun.look_at(Vector3(0.0, 0.0, target_z), Vector3.UP)

func _capture() -> void:
	var img := get_viewport().get_texture().get_image()
	var out := "res://../renders/%s.png" % shot_name
	var abs_out := ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(abs_out.get_base_dir())
	img.save_png(abs_out)
	print("captured %s  %dx%d" % [abs_out, img.get_width(), img.get_height()])
