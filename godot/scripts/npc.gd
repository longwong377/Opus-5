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

var _people: Array = []
var _body: Node3D


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
