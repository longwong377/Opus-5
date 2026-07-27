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
@export var shot_name: String = "engine_view"
## Applied to every surface of the imported station. The glTF carries geometry
## and normals only -- materials belong to the engine, not the export.
@export var hull_material: Material

func _ready() -> void:
	_apply_material($Station)
	_frame_camera()
	# Render one frame, capture, quit. Nothing here is interactive.
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	_capture()
	get_tree().quit()

func _apply_material(n: Node) -> void:
	if hull_material and n is MeshInstance3D:
		var mi := n as MeshInstance3D
		for i in mi.mesh.get_surface_count():
			mi.set_surface_override_material(i, hull_material)
	for c in n.get_children():
		_apply_material(c)


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

func _capture() -> void:
	var img := get_viewport().get_texture().get_image()
	var out := "res://../renders/%s.png" % shot_name
	var abs_out := ProjectSettings.globalize_path(out)
	DirAccess.make_dir_recursive_absolute(abs_out.get_base_dir())
	img.save_png(abs_out)
	print("captured %s  %dx%d" % [abs_out, img.get_width(), img.get_height()])
