extends SceneTree
## Loads every material in res://materials/ and asserts it parsed.
##
## Run headless:
##   godot --headless --path godot --script res://scripts/verify_materials.gd
##
## Worth having because a .tres is hand-authored text and only the exterior set
## is bound to a mesh in station_view.tscn. The interior materials --
## panelling, warning accent, deck channels, signage -- have no geometry to bind
## to yet, so nothing else would ever open them.
##
## Loading is not enough on its own. A dangling SubResource id does fail the
## load, but a misspelt property key does **not**: Godot drops keys it does not
## recognise and hands back a material that is silently at its defaults. That is
## the worst failure shape here, because it renders as a plausible surface
## rather than as an error, so every key is checked against the real property
## list rather than trusted because the file parsed.

const DIR := "res://materials"

func _initialize() -> void:
	var names := DirAccess.get_files_at(DIR)
	var failed := 0
	var checked := 0
	for f in names:
		if not f.ends_with(".tres"):
			continue
		checked += 1
		var path := "%s/%s" % [DIR, f]
		var res := ResourceLoader.load(path)
		if res == null or not res is BaseMaterial3D:
			push_error("FAIL  %s did not load as a material" % path)
			failed += 1
			continue
		var m := res as BaseMaterial3D
		var bad := false
		# An emissive that is not enabled is the failure mode that renders as a
		# dark object rather than as an error, so it is asserted rather than
		# eyeballed.
		var wants_emission := f.begins_with("emissive_") or f.begins_with("marker_light_")
		if wants_emission and not m.emission_enabled:
			push_error("FAIL  %s is named as a light source but emission is off" % path)
			bad = true
		var known := {}
		for p in m.get_property_list():
			known[p.name] = true
		for key in _resource_keys(path):
			if not known.has(key):
				push_error("FAIL  %s sets '%s', which %s has no such property -- Godot ignored it and left the default" % [path, key, m.get_class()])
				bad = true
		if bad:
			failed += 1
			continue
		print("ok    %-26s %s" % [f, m.resource_name])
	print("%d/%d materials loaded" % [checked - failed, checked])
	quit(1 if failed > 0 else 0)

func _resource_keys(path: String) -> PackedStringArray:
	## Property keys assigned in the file's [resource] block.
	##
	## Only that block: the [sub_resource] blocks are other classes with other
	## property lists, and a bad id in one of those does fail the load, so they
	## are already covered.
	var out := PackedStringArray()
	var text := FileAccess.get_file_as_string(path)
	var in_resource := false
	for raw in text.split("\n"):
		var line := raw.strip_edges()
		if line.begins_with("["):
			in_resource = line.begins_with("[resource]")
			continue
		if not in_resource or line.is_empty() or line.begins_with(";"):
			continue
		var eq := line.find(" = ")
		if eq > 0:
			out.append(line.substr(0, eq))
	return out
