extends Node3D
## The inhabitants notice you.
##
## THE OTHER HALF OF W5. The station had 278 people standing in 87 rooms and not
## one of them knew a player existed: they were geometry baked into the merged
## room mesh, which is the same reason a pressure door was a picture of a door
## until `door.gd`. A room with people who never react is a diorama, and a
## diorama is what the owner meant by "it exists around you rather than in text"
## NOT being true yet.
##
## WHAT IT NEEDS FROM THE GENERATOR, and why a sidecar rather than the mesh.
## A body is baked into world-space geometry, so nothing here can recover which
## way somebody is facing by looking at them -- and a person who turns towards
## you has to be turned FROM somewhere. `station/populace.py` records the yaw it
## used, `station/deck.py` maps it into the ring's frame, and `walkable.py`
## writes it out beside the mesh as `<deck>_actors.json`. Asking the geometry to
## give back what the generator already knew is how the door leaves ended up
## 0.16 m out of their own frame.
##
## Turning is a TRANSFORM ABOUT THE BODY'S OWN AXIS, not a node rotation: the
## vertices are already at their world positions, so the node's transform has to
## be `translate(pivot) * rotate * translate(-pivot)` or the person swings round
## the station's axis instead of their own heels.

## How far away somebody notices you. Beyond this they carry on with what they
## were doing, which is the point -- a room where everyone stares from 30 m is
## as wrong as a room where nobody looks at all.
@export var notice_m: float = 6.0
## Radians per second a head and shoulders come round. A person turning to look
## is not a turret.
@export var turn_rate: float = 2.2

## The player capsule's radius, from `walk.gd::_spawn_player`. Passed nowhere:
## it is the same 0.35 m in both files and this is the second copy, which is a
## thing to fix when a third appears rather than by threading a setter through
## three call sites for one float.
const PLAYER_R_M := 0.35
## How much clear air a walker leaves before they stop. A shoulder's width of
## slack: enough that a person halts in front of you rather than in you, small
## enough that the corridor does not part like a crowd around royalty.
const YIELD_MARGIN_M := 0.15

var _people: Array = []
var _body: Node3D
## How many of the crowd stopped for the player on the last step. Reported, not
## just tracked -- it is the only thing that can say the yield is running, and a
## behaviour nothing measures is one that silently stops working.
var _yielding: int = 0


class Person:
	var group: String
	var parts: Array = []            # every mesh this body is made of
	var pivot := Vector3.ZERO
	var up := Vector3.UP
	var rest_yaw: float = 0.0        # the yaw the generator baked in
	var yaw: float = 0.0             # where they are looking now
	var noticed := false
	var body: StaticBody3D = null    # what a player bumps into
	var r_m: float = 0.0
	var h_m: float = 0.0


## Wire the cast list to the meshes it describes.
func collect(visual: Node, actors: Array) -> int:
	# A PERSON IS SEVERAL MESHES. `npc/body.py` tags what it builds -- skin
	# head, torso, arms, hands, feet, hair -- and `populace` now carries those
	# names through so each binds to its own material, which is what stopped all
	# 278 inhabitants rendering as one surface. The consequence here is that the
	# person's OWN group ends up with no faces of its own: the OBJ writer gives
	# each triangle to the last group covering it, and the parts are written
	# after the whole. Matching the exact name found nothing at all.
	var parts := {}
	for m in _meshes(visual):
		var n := String(m.name)
		for a2 in actors:
			var g2 := String(a2.get("group", ""))
			# EXACT, OR THE GROUP FOLLOWED BY AN UNDERSCORE. A bare prefix
			# test makes `..._standing_1` swallow `..._standing_10`'s parts,
			# which is invisible in a room of five and wrong in a room of
			# twelve.
			if g2 != "" and (n == g2 or n.begins_with(g2 + "_")):
				if not parts.has(g2):
					parts[g2] = []
				parts[g2].append(m)
				break
	for a in actors:
		var g := String(a.get("group", ""))
		if not parts.has(g) or parts[g].is_empty():
			continue
		var p := Person.new()
		p.group = g
		p.parts = parts[g]
		p.pivot = Vector3(float(a.get("x", 0.0)), float(a.get("y", 0.0)),
			float(a.get("z", 0.0)))
		# Up is INWARD on a spun ring: the floor is the outer wall, so a
		# person's head points at the axis. The axis is +Z, so the radial
		# component is the xy part of their position.
		var radial := Vector3(p.pivot.x, p.pivot.y, 0.0)
		p.up = (-radial.normalized() if radial.length() > 0.001
			else Vector3.UP)
		p.rest_yaw = float(a.get("yaw", 0.0))
		p.yaw = p.rest_yaw
		p.r_m = float(a.get("r_m", 0.0))
		p.h_m = float(a.get("h_m", 0.0))
		_people.append(p)
	if not _args().has("no-npc-collision"):
		for p in _people:
			_give_body(p)
	else:
		print("npc: inhabitant collision DISABLED (negative control)")
	return _people.size()


## A PERSON IS SOMETHING YOU BUMP INTO, and until this existed a player walked
## through all 147 of them.
##
## NOT IN THE STATIC COLLISION, and that is deliberate rather than an oversight
## anybody should correct: `station/rooms.py::is_solid` excludes every `npc_`
## group because static collision is generated ONCE, so baking inhabitants into
## it makes permanent statues -- a person you bump into and who never moves is
## worse than one you walk through. The capsule therefore lives here, on a node
## that follows the person, and `station/populace.py::body_capsule` measures it
## off that individual's own mesh: 0.269 m for a human, 0.414 for a Vorlon in
## an encounter suit. A single number could not say that.
##
## Upright along the body's OWN up, which on a spun ring points at the axis and
## not at world +Y. Getting that wrong lays every capsule on its side, which a
## walk test reads as "the corridor is clear" -- the failure that looks like
## success.
func _give_body(p: Person) -> void:
	if p.r_m <= 0.0 or p.h_m <= 0.0:
		return
	var sb := StaticBody3D.new()
	sb.name = "body_" + p.group
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	# Godot's capsule height INCLUDES its two hemispherical ends, so a body
	# 1.80 m tall with a 0.27 m radius is a 1.80 m capsule and not a 2.34 m
	# one. Clamped so a wide short figure cannot ask for a negative cylinder.
	cap.radius = p.r_m
	cap.height = maxf(p.h_m, 2.0 * p.r_m + 0.01)
	cs.shape = cap
	sb.add_child(cs)
	add_child(sb)
	# A Godot capsule stands along its own +Y. Build a basis whose +Y is the
	# body's up -- inward on the ring -- and put its centre half a height along
	# that from the feet.
	var up := p.up
	var fwd := Vector3(0, 0, 1)
	if absf(fwd.dot(up)) > 0.99:
		fwd = Vector3(1, 0, 0)
	var right := fwd.cross(up).normalized()
	fwd = up.cross(right).normalized()
	sb.global_transform = Transform3D(Basis(right, up, fwd),
		p.pivot + up * (cap.height * 0.5))
	p.body = sb


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s2 := a.trim_prefix("--")
		var eq := s2.find("=")
		if eq < 0:
			out[s2] = true
		else:
			out[s2.substr(0, eq)] = s2.substr(eq + 1)
	return out


func watch(body: Node3D) -> void:
	_body = body


func _meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		out.append_array(_meshes(c))
	return out


## The yaw that would face `target` from `p`, in the same convention
## `populace._place_body` used: it rotates the body about ITS OWN up by `yaw`,
## and at yaw 0 the body's forward is the room's +z, which the ring maps to the
## station axis.
func _yaw_towards(p: Person, target: Vector3) -> float:
	var to := target - p.pivot
	to = to - p.up * to.dot(p.up)
	if to.length() < 0.01:
		return p.rest_yaw
	# Basis at rest: the room's +z axis carried onto the ring. The ring rotates
	# a room by its angle, which `deck.py` has already folded into `rest_yaw`,
	# so the reference direction here is the station axis itself.
	var fwd0 := Vector3(0, 0, 1)
	fwd0 = (fwd0 - p.up * fwd0.dot(p.up)).normalized()
	var right0 := fwd0.cross(p.up).normalized()
	return atan2(to.dot(right0), to.dot(fwd0))


func _physics_process(delta: float) -> void:
	if _body == null:
		return
	var here := _body.global_position
	for p in _people:
		var d := here.distance_to(p.pivot)
		# NOBODY IS NEAR AND NOBODY IS TURNING: SKIP THEM ENTIRELY.
		#
		# An optimisation, and worth having on its own terms -- `notice_m` is
		# 6 m, so on a deck of a hundred-odd people the number turning at any
		# instant is a handful and the rest were having a transform computed
		# and written to every part of them for nothing.
		#
		# IT IS NOT WHAT FIXED THE WALK GATE, and that is written down because
		# the wrong answer was believed twice. The gate had gone from 10.2 s to
		# over 200 s for 120 frames, and the cause was neither this loop, nor
		# the collision capsules, nor the instanced crowd -- all three were
		# blamed in turn. It was a PARSE ERROR in this file: `for w in
		# _walkers` over an untyped Array makes `w` a Variant, so `var d :=
		# w.omega * delta` could not infer, the whole script failed to load,
		# and every call from `walk.gd` threw. 23,933 stack traces to stdout.
		# With the script parsing, people on costs the same 10.2 s as people
		# off. See `_walkers: Array[Walker]`.
		#
		# The early-out is on TWO conditions and both are needed: far away AND
		# already at rest. Testing distance alone would freeze somebody who
		# walked out of range mid-turn, leaving them staring at where the
		# player used to be -- which is a worse artefact than the cost.
		if d > notice_m and absf(wrapf(p.yaw - p.rest_yaw, -PI, PI)) < 1e-4:
			continue
		var want: float = (_yaw_towards(p, here) if d <= notice_m
			else p.rest_yaw)
		# Shortest way round, so nobody spins 350 degrees to look 10 to their
		# left.
		var diff: float = wrapf(want - p.yaw, -PI, PI)
		var step: float = turn_rate * delta
		p.yaw += clampf(diff, -step, step)
		p.noticed = p.noticed or d <= notice_m
		var b := Basis(p.up, p.yaw - p.rest_yaw)
		var xf := Transform3D(b, p.pivot - b * p.pivot)
		for m in p.parts:
			m.global_transform = xf
		# THE CAPSULE IS NOT TOUCHED HERE, and that is correct rather than an
		# omission: it is a body of revolution about the person's own up axis,
		# so turning to look at you moves nothing a player could feel. It will
		# need updating the day these people WALK, and `p.body` is held for
		# exactly that.


## For the headless test: how far the nearest person has turned from the pose
## they were generated in, in degrees, and how many noticed at all.
func turned_deg() -> float:
	var most := 0.0
	for p in _people:
		most = maxf(most, absf(rad_to_deg(wrapf(p.yaw - p.rest_yaw,
			-PI, PI))))
	return most


func noticed_count() -> int:
	var n := 0
	for p in _people:
		if p.noticed:
			n += 1
	return n


## How far off the nearest person is from actually facing `target`, in degrees.
##
## "DID THEY TURN" IS NOT THE QUESTION. A body rotated by a wrong yaw convention
## turns just as far as one rotated by the right one, and reports the same
## number -- which is how the deck assembler nearly shipped every inhabitant
## facing however far round the ring their room happened to sit. This asks
## whether they ended up LOOKING AT YOU.
func facing_error_deg(target: Vector3) -> float:
	var best := 1e30
	var err := -1.0
	for p in _people:
		var d := target.distance_to(p.pivot)
		if d < best and d <= notice_m:
			best = d
			err = absf(rad_to_deg(wrapf(_yaw_towards(p, target) - p.yaw,
				-PI, PI)))
	return err


# ===========================================================================
#  THE CROWD -- shared bodies, instanced, and they WALK
# ===========================================================================
# WHY THIS IS NOT `collect()` WITH MORE PEOPLE IN IT. Everything above binds a
# person to the meshes they were BAKED as, which is right for a room occupant:
# they are an individual, `body.individual` built them, and their identicard
# describes that mesh. It is wrong for a corridor, for three measured reasons
# recorded in `station/populace.py`: a rigid per-part transform is 145 mm out
# at the knee, splitting each part at its dominant bone needs 19 pieces, and
# TWELVE pieces was already 1,262 primitives on one deck.
#
# So a walker is a PLACEMENT against `populace.station_crowd_library` -- 112
# shared bodies, 14 species by 8 walk phases, 54,816 triangles for the whole
# station against 466,092 baked. Every walker of one species at one phase goes
# into one MultiMesh, so the station's entire crowd is **112 draw calls**
# rather than 963, and moving somebody is writing one transform into a buffer.
#
# The phase is chosen by TIME rather than by distance travelled, and the two
# agree because `populace` gives each walker `cycle_s` from the same
# `walk_clip` its `omega` came from. A crowd whose feet slide is a crowd
# animated at one speed and moved at another.
class Walker:
	var species: String
	var lod: int
	var phase: int
	var angle: float          # radians round the ring
	var radius: float
	var z: float
	var omega: float          # radians a second, signed by direction
	var cycle_s: float
	var t: float = 0.0
	var body: StaticBody3D = null
	var r_m: float = 0.0
	var h_m: float = 0.0


var _walkers: Array[Walker] = []
var _mm: Dictionary = {}          # "crowd_human_4_3" -> MultiMeshInstance3D
var _mm_rows: Dictionary = {}     # the same key -> Array[Walker] this frame


## The LOD ladder, as `max_m:lod` pairs nearest-first. Parsed from the string
## `station/populace.crowd_ladder()` produced, so the runtime and the generator
## cannot disagree about which mesh belongs at which distance.
var _ladder: Array = []


func set_crowd_ladder(spec: String) -> void:
	_ladder.clear()
	for part in spec.split(","):
		var kv := String(part).split(":")
		if kv.size() == 2:
			_ladder.append([float(kv[0]), int(kv[1])])
	_ladder.sort_custom(func(a, b): return a[0] < b[0])


## Which chain LOD a walker at `d` metres should be drawn at.
##
## A BAKED WALKER HAD ONE LOD BECAUSE A STATIC MESH HAS NO OTHER OPTION -- the
## generator picks for the mean distance down the corridor's 66 m sight line
## and everybody pays it, so the person two metres in front of you is a
## 484-triangle body where `schedule.NPC_BUDGET` allows 2,000. An INSTANCED
## walker is a transform, so the only thing standing between us and the right
## answer was a second library.
func _lod_at(d: float) -> int:
	if _ladder.is_empty():
		return 4
	for rung in _ladder:
		if d <= float(rung[0]):
			return int(rung[1])
	return int(_ladder[_ladder.size() - 1][1])


## Build the crowd from several LOD libraries and one placement list.
func build_crowd_multi(libraries: Array, rows: Array) -> int:
	var n := 0
	for lib in libraries:
		n = build_crowd(lib, rows if n == 0 else [])
	return _walkers.size()


## Build the crowd from the library scene and the placement list.
func build_crowd(library: Node, rows: Array) -> int:
	var meshes := {}
	for m in _meshes(library):
		# The library's mesh names are `crowd_<species>_<lod>_<phase>_npc_skin`
		# and friends; the body key is everything before the material suffix.
		var n := String(m.name)
		var cut := n.find("_npc_")
		if cut > 0:
			var key := n.substr(0, cut)
			if not meshes.has(key):
				meshes[key] = []
			# THE SOURCE NODE'S NAME TRAVELS WITH THE MESH, because material
			# binding is by name: `materials.resolve` matches the longest
			# fragment IN the group name, so a MultiMesh called
			# `crowd_human_4_3_0` resolves to nothing while
			# `crowd_human_4_3_npc_skin` resolves to skin. Naming a node after
			# its index instead of after what it is renders the whole crowd on
			# the magenta fallback.
			meshes[key].append([m.mesh, n])
	for r in rows:
		var w := Walker.new()
		w.species = String(r.get("species", "human"))
		w.lod = int(r.get("lod", 4))
		w.phase = int(r.get("phase", 0))
		var x := float(r.get("x", 0.0))
		var y := float(r.get("y", 0.0))
		w.z = float(r.get("z", 0.0))
		w.radius = sqrt(x * x + y * y)
		w.angle = atan2(y, x)
		w.omega = float(r.get("omega", 0.0))
		w.cycle_s = maxf(0.1, float(r.get("cycle_s", 1.0)))
		w.r_m = float(r.get("r_m", 0.0))
		w.h_m = float(r.get("h_m", 0.0))
		# Start each walker at their own point in the cycle, so 134 people are
		# not marching. The generator already picked it; this reproduces it.
		w.t = w.cycle_s * float(w.phase) / 8.0
		_walkers.append(w)
	# One MultiMesh per (species, lod, phase). Sized to the worst case -- every
	# walker of that species at that phase at once -- because a MultiMesh's
	# instance_count cannot grow without reallocating.
	# SIZED TO WHAT CAN ACTUALLY BE IN THE BUCKET, not to the species. A
	# MultiMesh uploads `instance_count` transforms whenever it is touched, not
	# `visible_instance_count`, so sizing every one of a species' eight phase
	# buckets to the whole species uploads eight times the crowd every frame --
	# 7,304 transforms a frame on a deck with 134 walkers, which is what made
	# the first version of this take minutes where the walk gate takes 38 s.
	# Walkers spread over eight phases, so a bucket holds about an eighth;
	# three times that plus a floor of four is slack no realistic clustering
	# exceeds, and `_place_crowd` clamps to the count anyway.
	var per_species := {}
	for w in _walkers:
		per_species[w.species] = int(per_species.get(w.species, 0)) + 1
	# EVERY RUNG, not just the one the bake chose. A walker's LOD now changes
	# with their distance to the player, so a bucket has to exist for each
	# level the ladder can put them at -- keyed the same way, so `_place_crowd`
	# needs no change at all. Sizing is per rung and worst-case: in the limit
	# every walker of a species is at one distance band and one phase.
	var lods := []
	for rung in _ladder:
		if not lods.has(int(rung[1])):
			lods.append(int(rung[1]))
	if lods.is_empty():
		lods = [4]
	var counts := {}
	for w in _walkers:
		for lod in lods:
			for ph in range(8):
				var k := "crowd_%s_%d_%d" % [w.species, lod, ph]
				counts[k] = maxi(4, int(ceil(
					float(per_species[w.species]) / 8.0 * 3.0)))
	for k in counts.keys():
		if not meshes.has(k):
			continue
		for surf in meshes[k]:
			var mmi := MultiMeshInstance3D.new()
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = surf[0]
			mm.instance_count = int(counts[k])
			mm.visible_instance_count = 0
			mmi.multimesh = mm
			mmi.name = String(surf[1])
			add_child(mmi)
			if not _mm.has(k):
				_mm[k] = []
			_mm[k].append(mmi)
	if not _args().has("no-npc-collision"):
		for w in _walkers:
			_give_walker_body(w)
	_place_crowd()
	return _walkers.size()


func _give_walker_body(w: Walker) -> void:
	if w.r_m <= 0.0 or w.h_m <= 0.0:
		return
	var sb := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = w.r_m
	cap.height = maxf(w.h_m, 2.0 * w.r_m + 0.01)
	cs.shape = cap
	sb.add_child(cs)
	add_child(sb)
	w.body = sb


## Where a walker is, and which way is up for them. Up is INWARD on a spun
## ring, so it is a different direction at every angle -- which is why the
## generator writes a basis per instance and why this recomputes one rather
## than carrying a yaw.
func _walker_xform(w: Walker) -> Transform3D:
	var ca := cos(w.angle)
	var sa := sin(w.angle)
	var up := Vector3(-ca, -sa, 0.0)
	var fwd := Vector3(-sa, ca, 0.0) * signf(w.omega if w.omega != 0.0 else 1.0)
	var right := fwd.cross(up).normalized()
	return Transform3D(Basis(right, up, fwd),
		Vector3(w.radius * ca, w.radius * sa, w.z))


## Refill every MultiMesh from the walkers' current phase. A walker moves
## between MultiMeshes as their phase advances, which is a bucket sort of a
## few hundred items and costs nothing.
func _place_crowd() -> void:
	for k in _mm.keys():
		_mm_rows[k] = []
	for w in _walkers:
		var k := "crowd_%s_%d_%d" % [w.species, w.lod, w.phase]
		if _mm_rows.has(k):
			_mm_rows[k].append(w)
	for k in _mm.keys():
		var rows: Array = _mm_rows[k]
		for mmi in _mm[k]:
			var mm: MultiMesh = mmi.multimesh
			mm.visible_instance_count = mini(rows.size(), mm.instance_count)
			for i in range(mm.visible_instance_count):
				mm.set_instance_transform(i, _walker_xform(rows[i]))


## How far round the ring the crowd has travelled, in metres, summed. The
## headless walk test reads it: a crowd that does not move is a crowd of
## statues wearing a walk pose, which is worse than statues.
var _crowd_travel_m: float = 0.0


func crowd_travel_m() -> float:
	return _crowd_travel_m


func crowd_count() -> int:
	return _walkers.size()


## How many of the crowd stopped for the player on the last step.
func yielding_count() -> int:
	return _yielding


## How many walkers ended up on each rung, and the nearest one's distance.
## THE ONLY THING THAT CAN SHOW THE LADDER IS USED: the crowd covers the same
## distance whatever LOD it is drawn at, so `crowd_travel_m` cannot tell a
## working ladder from a dead one. This can.
func crowd_lod_report() -> String:
	var by := {}
	var nearest := 1e9
	var eye := (_body.global_position if _body != null else Vector3.ZERO)
	for w in _walkers:
		by[w.lod] = int(by.get(w.lod, 0)) + 1
		if _body != null:
			nearest = minf(nearest,
				eye.distance_to(_walker_xform(w).origin))
	var keys := by.keys()
	keys.sort()
	var parts := []
	for k in keys:
		parts.append("%d:%d" % [k, by[k]])
	return "%s nearest=%.1f" % ["/".join(parts), nearest]


## How often the crowd's transforms are rewritten, in hertz. NOT every physics
## frame, and the reason is measured: each rewrite re-uploads every MultiMesh's
## whole instance buffer, so at 60 Hz a deck's crowd cost more than the rest of
## the walk gate put together. At 10 Hz a walker moves 0.145 m between updates
## -- under the 0.22 m tile they are stepping on, and a tenth of the 1.45 m
## stride the pose is showing -- so nothing a player can see is dropped.
@export var crowd_hz: float = 10.0

var _crowd_dt: float = 0.0


func advance_crowd(delta: float) -> void:
	if _walkers.is_empty():
		return
	_crowd_dt += delta
	var step := 1.0 / maxf(1.0, crowd_hz)
	if _crowd_dt < step:
		return
	delta = _crowd_dt
	_crowd_dt = 0.0
	var eye := (_body.global_position if _body != null else Vector3.ZERO)
	_yielding = 0
	for w in _walkers:
		var d: float = w.omega * delta
		# -- THEY STOP RATHER THAN WALK THROUGH YOU ------------------------
		# A walker's path is a fixed circular orbit and their capsule is a
		# StaticBody3D teleported onto it every step, so anything standing on
		# that orbit is BULLDOZED. Measured over a 204 s launch with nobody
		# touching the keyboard: the player was carried along at a walking pace
		# in 0.6 m shoves, pushed through the trimesh floor, and ended 66 km
		# outside the station in free fall.
		#
		# THE WALK GATE COULD NOT SEE IT. It runs 30 s and DRIVES the body, so
		# every frame it measures is one where being moved is correct, and it
		# never stands still. `on_floor=true` was reported throughout, because
		# it was true -- right up to the frame it was not.
		#
		# Stopping rather than steering around is the smaller change and the
		# more honest one: a person whose way you are standing in stops. Their
		# stride freezes with them (`w.t` does not advance), so the pose is a
		# person halted mid-step and not a person moonwalking on the spot.
		if w.body != null and _body != null and d != 0.0:
			var ahead := w.angle + d
			var p := Vector3(w.radius * cos(ahead), w.radius * sin(ahead), w.z)
			var clear := w.r_m + PLAYER_R_M + YIELD_MARGIN_M
			if p.distance_squared_to(eye) < clear * clear:
				_yielding += 1
				continue
		w.angle += d
		_crowd_travel_m += absf(d) * w.radius
		w.t += delta
		# THE RUNG THEY BELONG ON. Recomputed here rather than at build time
		# because it is a function of where the player is, and `_place_crowd`
		# buckets on `w.lod` already -- so choosing it is the whole change.
		if _body != null:
			w.lod = _lod_at(eye.distance_to(_walker_xform(w).origin))
		# Eight phases over one stride cycle. `cycle_s` and `omega` come from
		# the SAME `walk_clip`, so the feet land where the body has moved to.
		w.phase = int(floor(w.t / w.cycle_s * 8.0)) % 8
		if w.body != null:
			var xf := _walker_xform(w)
			w.body.global_transform = Transform3D(xf.basis,
				xf.origin + xf.basis.y * (maxf(w.h_m, 2.0 * w.r_m + 0.01) * 0.5))
	_place_crowd()
