extends Node
## Bind the station's materials and light its fittings IN THE BUILD A PLAYER
## STANDS IN.
##
## THE FINDING THIS CLOSES (docs/judge-3w.md, session 3w). `walk.tscn` is the
## only scene a player can be inside -- it is what `station/walkable.py`
## launches and what CI runs -- and it loaded a .glb, gave it collision and put
## a body on it. It applied NO MATERIALS and created NO LIGHTS. Every surface
## was the glTF fallback under a flat grey ambient, while `tools/export_scene.py`
## carried 429 material rules and sixteen measured light fittings that were only
## ever used to take screenshots. The playable build and the beautiful build
## were two different builds, and only one of them could be walked in.
##
## NOTHING HERE IS A SECOND TABLE, and that is the whole design. This project
## has been bitten three times by two descriptions of one thing drifting apart
## -- the material rules pasted into a scene nobody read back, the corridor's
## fourteen group names replaced by one, the door leaves re-derived from
## geometry that already knew. So both halves are BORROWED:
##
##   materials   `godot/scenes/interior.tscn`'s `material_rules`, which
##               `station/materials.py --export` writes and asserts. The scene
##               is INSTANTIATED but never entered into the tree -- so
##               render_shot.gd's `_ready` never fires -- and its own
##               `_material_for()` does the matching. Table and matcher are both
##               the shipping ones; this file supplies neither.
##
##   lighting    `tools/export_scene.py`'s `FIXTURE_LIGHTING`, `FIXTURE_MERGE_M`,
##               `INTERIOR_LIGHT_RANGE_M`, `INTERIOR_SHADOW_LIGHTS` and the
##               `--fixture-energy` default, PARSED OUT OF THE PYTHON SOURCE.
##               That is ugly and it is deliberately preferred to retyping
##               sixteen measured fittings into GDScript: a copy is correct on
##               the day it is written and silently wrong afterwards, and a
##               fitting's colour, range and cone are MEASUREMENTS. The parse
##               fails loudly and names what it could not find.
##
##               The clean version of this is four lines in export_scene.py --
##               `--dump-lighting` writing FIXTURE_LIGHTING to JSON beside the
##               deck mesh -- and it is written out in STATE.md for whoever owns
##               that file. Until then, the parse is the only way to have one
##               definition instead of two.
##
## WHAT IS NOT BORROWED, and is stated rather than hidden:
##
##   * WHERE the lamps go. `export_scene.fixture_lights` needs the generator's
##     (name, lo, hi) spans, and a .glb has lost them -- `export_gltf` merges
##     every span of one group name into a single mesh, so the deck's 832
##     downlights arrive as ONE mesh of 9,984 triangles. So the fittings are
##     recovered here by single-linkage clustering at `FIXTURE_MERGE_M`, which
##     is the same constant and the same intent. Checked against the Python:
##     850 lamps both ways, 832 downlights and 18 high bays, worst position
##     disagreement 0.32 mm. The check is in STATE.md and is reproducible.
##
##   * A SPOT ON A RING DECK AIMS RADIALLY OUTWARD, not at world -Y.
##     `fixture_lights` writes `aim = [0,-1,0]` because it only ever ran on one
##     room in that room's own frame. On an assembled ring the rooms are rotated
##     into the ring, so "down" for a bay flood at ring angle 90 deg is +Y, and
##     a world-down aim would fire it along a wall. Same rule as
##     `export_scene.radial_aim`, which the drum already uses for exactly this.

## Where the material table and the calibrated interior environment come from.
const INTERIOR_SCENE := "res://scenes/interior.tscn"
## Where the light fitting measurements come from, relative to the project dir.
const EXPORT_SCENE_PY := "../tools/export_scene.py"

## Points closer than this are the same vertex, for the purpose of counting how
## many distinct points a fitting has. NOT a weld tolerance and deliberately
## coarser than `export_scene.FIXTURE_WELD_M` (0.1 mm): glTF stores positions as
## float32 and this station's ring decks sit at z ~ 7,100 m, where a float32
## quantum is 0.49 mm. A 0.1 mm weld cannot dedupe data that is already
## quantised more coarsely than that. This only reduces the point count before
## clustering -- the lamp position is the cluster's bounding-box centre, taken
## from the retained vertices, so its error is the float32 quantum and not this.
const DEDUPE_M := 0.005

var spec: Dictionary = {}          ## FIXTURE_LIGHTING, parsed
var consts: Dictionary = {}        ## module-level scalars from export_scene.py
var problems: PackedStringArray = PackedStringArray()

var _owner: Node = null            ## the instantiated interior.tscn root
var _environment: Environment = null


## Load the material table, the environment and the fitting measurements.
## Returns false if anything is missing; `problems` says what.
func prepare() -> bool:
	problems = PackedStringArray()
	_harvest_interior()
	_read_lighting()
	return problems.is_empty()


## The calibrated interior Environment, or null. This is `interior.tscn`'s own
## `Env` sub-resource -- ACES at exposure 1.0, white point 4.0, ambient 1.30
## (AMBIENT_CALIBRATED_ENERGY, the residential corridor's measured fill), SSAO
## at a 0.6 m radius because the subject is a skirting board, and a low glow.
## Every one of those is a judgement someone made against a reference frame; a
## second set of numbers here would be a second look.
func environment() -> Environment:
	return _environment


func _harvest_interior() -> void:
	var ps := load(INTERIOR_SCENE) as PackedScene
	if ps == null:
		problems.append("cannot load " + INTERIOR_SCENE)
		return
	# NEVER add_child THIS. render_shot.gd's `_ready` requires --scene-json and
	# calls get_tree().quit(2) without one, so entering it into the tree would
	# kill the walk test with an error about a flag this scene does not use.
	_owner = ps.instantiate()
	if not _owner.get("material_rules"):
		problems.append(INTERIOR_SCENE + " has no material_rules")
	var we := _owner.get_node_or_null("WorldEnvironment") as WorldEnvironment
	if we == null or we.environment == null:
		problems.append(INTERIOR_SCENE + " has no WorldEnvironment")
	else:
		_environment = we.environment


func _python_source() -> String:
	var p := ProjectSettings.globalize_path("res://").path_join(
		EXPORT_SCENE_PY).simplify_path()
	if not FileAccess.file_exists(p):
		problems.append("no such file: " + p)
		return ""
	return FileAccess.get_file_as_string(p)


## `NAME = {` ... `\n}` at column zero. Anchored on the assignment rather than
## on the bare name, because the name also appears in prose in this file's
## comments a dozen times.
func _py_block(text: String, name: String) -> String:
	var head := "\n%s = {" % name
	var i := text.find(head)
	if i < 0:
		problems.append("no `%s = {` in export_scene.py" % name)
		return ""
	i += head.length() - 1
	var j := text.find("\n}", i)
	if j < 0:
		problems.append("`%s` is not closed" % name)
		return ""
	return text.substr(i, j - i + 2)


## Everything from an unquoted `#` to end of line. Checked against the source:
## no string inside the FIXTURE_LIGHTING block contains a `#`, so a plain cut is
## safe here and a quote-aware scanner would be pretending to more generality
## than the input has.
func _strip_comments(block: String) -> String:
	var out := ""
	for line in block.split("\n"):
		var h := String(line).find("#")
		out += (String(line) if h < 0 else String(line).substr(0, h)) + "\n"
	return out


func _re(pattern: String) -> RegEx:
	var r := RegEx.new()
	r.compile(pattern)
	return r


func _py_number(text: String, name: String, fallback: float) -> float:
	var m := _re("(?m)^" + name + "\\s*=\\s*([0-9.]+)").search(text)
	if m == null:
		problems.append("no `%s = <number>` in export_scene.py" % name)
		return fallback
	return m.get_string(1).to_float()


func _read_lighting() -> void:
	var text := _python_source()
	if text == "":
		return
	consts = {
		"merge_m": _py_number(text, "FIXTURE_MERGE_M", 0.9),
		"range_m": _py_number(text, "INTERIOR_LIGHT_RANGE_M", 7.0),
		"shadow_n": _py_number(text, "INTERIOR_SHADOW_LIGHTS", 2.0),
		"samples_per_range": _py_number(text, "EXTENDED_SAMPLES_PER_RANGE", 4.0),
		"sample_cap": _py_number(text, "EXTENDED_SAMPLE_CAP", 24.0),
	}
	# The energy every `energy_rel` is relative to. It is an argparse default
	# rather than a module constant, so it is read where it lives; at the
	# corridor anchor `room_exposure` is 1.0 by definition, so this is the whole
	# multiplier for a deck that is 77% corridor kit.
	var m := _re("--fixture-energy\"\\s*,\\s*type=float\\s*,\\s*default=([0-9.]+)"
		).search(text)
	if m == null:
		problems.append("no `--fixture-energy ... default=` in export_scene.py")
		consts["fixture_energy"] = 3.0
	else:
		consts["fixture_energy"] = m.get_string(1).to_float()

	var block := _strip_comments(_py_block(text, "FIXTURE_LIGHTING"))
	if block == "":
		return
	var colour := _re("\"colour\"\\s*:\\s*\\(\\s*([0-9.]+)\\s*,\\s*([0-9.]+)"
		+ "\\s*,\\s*([0-9.]+)\\s*\\)")
	var kind := _re("\"kind\"\\s*:\\s*\"([a-z]+)\"")
	var erel := _re("\"energy_rel\"\\s*:\\s*([0-9.]+)")
	var rng := _re("\"range_m\"\\s*:\\s*([0-9.]+)")
	var shadow := _re("\"shadow\"\\s*:\\s*(True|False)")
	var angle := _re("\"angle_deg\"\\s*:\\s*([0-9.]+)")
	spec = {}
	for e in _re("\"([A-Za-z0-9_]+)\"\\s*:\\s*\\{([^{}]*)\\}").search_all(block):
		var name := e.get_string(1)
		var body := e.get_string(2)
		var c := colour.search(body)
		var k := kind.search(body)
		var g := erel.search(body)
		var r := rng.search(body)
		var s := shadow.search(body)
		if c == null or k == null or g == null or r == null or s == null:
			problems.append("FIXTURE_LIGHTING[%s] did not parse" % name)
			continue
		var d := {
			"kind": k.get_string(1),
			"colour": Color(c.get_string(1).to_float(),
				c.get_string(2).to_float(), c.get_string(3).to_float()),
			"energy_rel": g.get_string(1).to_float(),
			"range_m": r.get_string(1).to_float(),
			"shadow": s.get_string(1) == "True",
		}
		var a := angle.search(body)
		d["angle_deg"] = (a.get_string(1).to_float() if a != null else 45.0)
		spec[name] = d
	if spec.is_empty():
		problems.append("FIXTURE_LIGHTING parsed to nothing")


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

## Give every mesh under `root` the material the interior scene binds to its
## group name. Returns {meshes, bound, unmatched, ruled_but_null}.
##
## The matching is `render_shot.gd`'s own `_material_for` -- longest substring
## wins -- called on the instantiated interior scene. Restating eight lines of
## matcher here would be a second implementation of the thing whose duplication
## this project has already paid for twice.
##
## `bound` COUNTS MATERIALS APPLIED, NOT RULES MATCHED, and the difference is
## not pedantry: it was measured. `godot/.godot/` is gitignored, so a fresh
## clone or a `git worktree` has no import cache, every `[ext_resource]` in
## interior.tscn resolves to NULL, and the rules dictionary still has all 429
## keys pointing at nothing. The first version of this counter reported
## "271/286 on a material rule" over a frame in which not one material existed.
## A summary line that cannot distinguish "bound" from "matched a rule whose
## value is null" is the same defect as an assertion that cannot fail.
func bind(root: Node) -> Dictionary:
	if _owner == null:
		return {"meshes": 0, "bound": 0, "unmatched": PackedStringArray(),
			"ruled_but_null": PackedStringArray()}
	var rules: Dictionary = _owner.get("material_rules")
	var missed := {}
	var empty := {}
	var meshes := 0
	var bound := 0
	for mi in _mesh_instances(root):
		meshes += 1
		var key := String(mi.name)
		var mat: Material = _owner._material_for(key)
		var hit := false
		for frag in rules:
			if key.contains(String(frag)):
				hit = true
				break
		if mat != null:
			bound += 1
			for i in mi.mesh.get_surface_count():
				mi.set_surface_override_material(i, mat)
		elif hit:
			empty[key] = true
		if not hit:
			missed[key] = true
	return {"meshes": meshes, "bound": bound,
		"unmatched": PackedStringArray(missed.keys()),
		"ruled_but_null": PackedStringArray(empty.keys())}


## Drop the instantiated interior scene. Call once binding is done; the
## Materials and the Environment are Resources and stay alive on their own
## references, so freeing the node does not take the look with it.
func release() -> void:
	if _owner != null:
		_owner.free()
		_owner = null


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------

## Put a real source at every measured fitting under `root`.
##
## MEMBERSHIP OF FIXTURE_LIGHTING IS THE GATE, not the `light_` prefix --
## export_scene.fixture_lights says so and gives the reason: a fitting has to be
## MEASURED to become a source. Of the deck's fifteen `light_*` groups only two
## families are in the table. `light_pilaster_strip`, `light_portal_head` and
## `light_deck_channel` are emissive-only, and that is a measurement (two
## independent tests in `grey level 1.webp`), not an omission. Treating the trim
## as lighting floods the fill and destroys the contrast that IS the corridor.
##
## THE NAME IS THE TAIL AFTER `__`. `deck.py` prefixes a room's groups with its
## place key -- `f"{q['key']}__{n}"`, and splits on the same separator itself --
## so the deck's fittings arrive as `docking_bays__light_highbay`. An exact-name
## table sees none of them. This is a real defect in the shot path too: run
## `fixture_lights` on an assembled deck and every room fitting is invisible to
## it; only the corridor kit's unprefixed `light_downlight` matches.
func light(root: Node, holder: Node3D, energy: float, eye: Vector3) -> Dictionary:
	var merge: float = consts.get("merge_m", 0.9)
	var default_range: float = consts.get("range_m", 7.0)
	var made: Array[Light3D] = []
	var casters: Array[Light3D] = []
	var lit := {}
	var emissive_only := PackedStringArray()
	var extended := PackedStringArray()

	for mi in _mesh_instances(root):
		var name := String(mi.name)
		var fitting := name.get_slice("__", name.get_slice_count("__") - 1)
		if not spec.has(fitting):
			if name.contains("light_"):
				emissive_only.append(name)
			continue
		var s: Dictionary = spec[fitting]
		var reach: float = s["range_m"] if s["range_m"] > 0.0 else default_range
		var boxes := _fittings(mi, merge)
		lit[fitting] = int(lit.get(fitting, 0)) + boxes.size()
		for box in boxes:
			var aabb: AABB = box
			var parts := _samples(aabb, reach)
			if parts.size() > 1 and not extended.has(fitting):
				extended.append(fitting)
			for p in parts:
				var l := _lamp(s, reach, energy / float(parts.size()), p)
				holder.add_child(l)
				l.global_position = p
				if l is SpotLight3D:
					# Straight down IS the measurement for all five spots in
					# the table; on a ring, down is radially outward.
					var down := Vector3(p.x, p.y, 0.0)
					down = (down.normalized() if down.length() > 0.001
						else Vector3.DOWN)
					l.look_at(p + down, Vector3(0.0, 0.0, 1.0))
				made.append(l)
				if s["shadow"]:
					casters.append(l)

	# Shadows are rationed exactly as fixture_lights rations them: an omni
	# shadow is a cube map, so each one re-renders the scene six times, on a
	# CPU. Nearest to the eye wins.
	var n_shadow := int(consts.get("shadow_n", 2.0))
	casters.sort_custom(func(a, b): return (a.global_position.distance_squared_to(eye)
		< b.global_position.distance_squared_to(eye)))
	for i in mini(n_shadow, casters.size()):
		casters[i].shadow_enabled = true
		casters[i].shadow_bias = 0.08
	return {"lights": made.size(), "by_fitting": lit,
		"shadows": mini(n_shadow, casters.size()),
		"emissive_only": emissive_only, "extended": extended}


func _lamp(s: Dictionary, reach: float, energy: float, _pos: Vector3) -> Light3D:
	var l: Light3D
	if String(s["kind"]) == "spot":
		var sp := SpotLight3D.new()
		sp.spot_range = reach
		sp.spot_attenuation = 1.0
		sp.spot_angle = float(s["angle_deg"])
		sp.spot_angle_attenuation = 0.6
		l = sp
	else:
		var o := OmniLight3D.new()
		o.omni_range = reach
		o.omni_attenuation = 1.0
		l = o
	l.light_color = s["colour"]
	l.light_energy = energy * float(s["energy_rel"])
	return l


## A fitting longer than its own throw cannot be a point, so it is sampled --
## `export_scene.EXTENDED_SAMPLES_PER_RANGE`, and the energy is shared so
## sampling never changes how much light is in the room. Nothing on a ring deck
## reaches this (the widest body is a 1.371 m high bay against a 12.5 m range),
## which is why it prints when it fires: it means a fitting has changed shape.
func _samples(aabb: AABB, reach: float) -> Array[Vector3]:
	var out: Array[Vector3] = []
	if aabb.size.length() <= reach:
		out.append(aabb.get_center())
		return out
	var axis := 0
	if aabb.size.y > aabb.size[axis]:
		axis = 1
	if aabb.size.z > aabb.size[axis]:
		axis = 2
	var pitch: float = reach / float(consts.get("samples_per_range", 4.0))
	var n := clampi(int(ceil(aabb.size[axis] / maxf(pitch, 0.01))), 1,
		int(consts.get("sample_cap", 24.0)))
	for i in n:
		var p := aabb.get_center()
		p[axis] = aabb.position[axis] + aabb.size[axis] * (float(i) + 0.5) / float(n)
		out.append(p)
	return out


## One mesh -> one bounding box per FITTING, by single-linkage clustering at
## `FIXTURE_MERGE_M`.
##
## WHY CLUSTERING AND NOT THE GENERATOR'S SPANS: `export_gltf.load_obj_groups`
## keys on the group NAME, so all 832 corridor downlights arrive as one mesh of
## 9,984 triangles with no record of where one lamp ends and the next begins.
## 0.9 m is the constant export_scene already chose for exactly this question,
## and for the stated reason -- it spans a pilaster strip's seven bars at 0.12 m
## pitch without reaching the next pilaster a portal bay away.
func _fittings(mi: MeshInstance3D, merge: float) -> Array:
	var xf := mi.global_transform
	var pts := PackedVector3Array()
	var seen := {}
	for si in mi.mesh.get_surface_count():
		var arr := mi.mesh.surface_get_arrays(si)
		if arr.size() <= Mesh.ARRAY_VERTEX:
			continue
		var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for v in vs:
			var w: Vector3 = xf * v
			var k := Vector3i(roundi(w.x / DEDUPE_M), roundi(w.y / DEDUPE_M),
				roundi(w.z / DEDUPE_M))
			if seen.has(k):
				continue
			seen[k] = true
			pts.append(w)
	if pts.is_empty():
		return []

	# Spatial hash at the merge radius, so only the 27 neighbouring cells are
	# ever compared. Without it this is 30k x 30k on the corridor's downlights.
	var grid := {}
	for i in pts.size():
		var k := Vector3i(floori(pts[i].x / merge), floori(pts[i].y / merge),
			floori(pts[i].z / merge))
		if not grid.has(k):
			grid[k] = []
		grid[k].append(i)

	var parent := PackedInt32Array()
	parent.resize(pts.size())
	for i in pts.size():
		parent[i] = i
	var r2 := merge * merge
	for k in grid:
		var a: Array = grid[k]
		for dx in [-1, 0, 1]:
			for dy in [-1, 0, 1]:
				for dz in [-1, 0, 1]:
					var nk: Vector3i = Vector3i(k.x + dx, k.y + dy, k.z + dz)
					if not grid.has(nk):
						continue
					var b: Array = grid[nk]
					for i in a:
						for j in b:
							if i >= j:
								continue
							if pts[i].distance_squared_to(pts[j]) <= r2:
								_union(parent, i, j)

	var boxes := {}
	for i in pts.size():
		var r := _find(parent, i)
		if boxes.has(r):
			boxes[r] = (boxes[r] as AABB).expand(pts[i])
		else:
			boxes[r] = AABB(pts[i], Vector3.ZERO)
	return boxes.values()


func _find(parent: PackedInt32Array, a: int) -> int:
	while parent[a] != a:
		parent[a] = parent[parent[a]]
		a = parent[a]
	return a


func _union(parent: PackedInt32Array, a: int, b: int) -> void:
	var ra := _find(parent, a)
	var rb := _find(parent, b)
	if ra != rb:
		parent[rb] = ra


func _mesh_instances(n: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	if n is MeshInstance3D and (n as MeshInstance3D).mesh != null:
		out.append(n)
	for c in n.get_children():
		_mesh_instances(c, out)
	return out
