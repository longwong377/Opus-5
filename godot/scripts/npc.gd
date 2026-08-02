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
##
## AND A PERSON CAN NOW GO AWAY UNDER YOU. With `scripts/stream.gd` an
## inhabitant's body arrives with their cell and is `queue_free`d with it, while
## the capsule a player bumps into is a child of THIS node and would outlive
## them -- an invisible person standing in an empty corridor. `collect()`
## therefore takes the cell's tag and `release()` gives back exactly what that
## cell brought, capsules included. The cast list itself is per DECK and is not
## split: an actor whose meshes are not in the cell simply binds to nothing,
## which is the same rule that already made `collect` skip an actor the glb never
## emitted.

## How far away somebody notices you. Beyond this they carry on with what they
## were doing, which is the point -- a room where everyone stares from 30 m is
## as wrong as a room where nobody looks at all.
@export var notice_m: float = 6.0
## Radians per second a head and shoulders come round. A person turning to look
## is not a turret.
@export var turn_rate: float = 2.2

var _people: Array = []
var _body: Node3D

# ---------------------------------------------------------------------------
#  YOU CANNOT WALK THROUGH A PERSON, AND A PERSON CANNOT TAKE YOUR FLOOR AWAY
# ---------------------------------------------------------------------------
# THE CROWD SHOVED THE PLAYER OFF THE FLOOR. `docs/streaming-doors-4g.md` 4c
# isolated it and did not fix it: with the corridor crowd on, the visit gate
# went from 0 of 16,200 frames off the floor to 605, the walk oscillated between
# three cells instead of crossing two, and the first visit was stopped 75 m
# short of the console. `--no-npc-collision` reproduced the crowd-less subject
# exactly, so it was never the wiring and never the LOD ladder.
#
# ITS DIAGNOSIS WAS WRONG, and the wrong diagnosis is the useful part. It read
# "a static body teleported into a CharacterBody3D ejects it rather than pushing
# it ... the body is thrown sideways out of a 2.6 m corridor", and proposed
# `AnimatableBody3D` with `sync_to_physics`. Three things were measured before
# any of this was written (`docs/runtime-4h.md` has the table):
#
#   * NOBODY IS THROWN ANYWHERE. Over 16,200 frames the body's greatest height
#     above its own last floor position is **1.3 mm**, in 442 separate episodes
#     the longest of which is 17 frames. It is not flight, it is flicker.
#   * `AnimatableBody3D` + `sync_to_physics`, swept every physics frame instead
#     of teleported at 10 Hz, moved the count from 2,523 to 2,507. Nothing.
#   * Padding the capsule's round end caps out of the player's reach -- the
#     classic "you got lifted by a hemisphere" -- moved it from 2,523 to 2,507
#     the other way. Also nothing.
#
# WHAT IT ACTUALLY IS, printed by `walk.gd` on the frame the floor is lost:
#
#     walk: OFF FLOOR f=711 lift=0.7mm v_up=-0.000 wall=true slides=3
#           [walker_human_23@n=-0.19,0.55,-0.81, ...]
#
# Every episode is a contact with a person, the contact normal is horizontal to
# within a degree, the body is not rising, and THE FLOOR IS NOT IN THE SLIDE
# LIST. `CharacterBody3D` re-attaches to a floor it has drifted off using
# `floor_snap_length`, and that snap casts down with `recovery_as_collision`
# set: while the capsule is in contact with anything, the cast comes back
# holding the thing it is touching, whose normal is 89 degrees off the floor,
# and the snap is refused. **So a body TOUCHING a person is a body with no
# floor**, whatever the person is made of. That is why every mechanism above
# changed nothing: they all still touch.
#
# THE MECHANISM THAT FITS A WALKER IS NOT A PHYSICS BODY AT ALL. People sit on
# their own collision layer with mask 0, so `move_and_slide` never resolves
# against one and the floor is never in question; and `push_off()` separates the
# player from anybody it overlaps by hand, ACROSS THE FLOOR PLANE ONLY, every
# frame. You still cannot walk through a person -- the separation is the full
# overlap, applied before they can get inside you -- and a person can no longer
# cost you the ground you are standing on, because nothing they do has a
# vertical component. It is the same shape of answer as `interact.gd`'s proxy
# boxes, which have been on their own layer with mask 0 since they were written.
#
# `--npc-solid=mask` puts them back on the world layer and turns the separation
# off, which is the build before this session and is one of `walkable.py
# --stream`'s six controls. It MUST fail.
const PEOPLE_LAYER := 4          ## world is 1, interact.gd's proxies are 2

var _solid_mode := "separate"    ## "separate" | "mask" (control) | "off"
var _walker_bodies := 0
var _said_collider := false
## The player's own capsule radius, read off the body it is told to watch --
## never written down here, because a second copy of `walk.gd::_spawn_player`'s
## 0.35 m is a second copy of how wide a person is.
var _player_r := 0.35
var _player_h := 1.8
## How far the separation has moved the player in total, and the largest single
## frame of it. The claim "a person is something you bump into" is these two
## numbers; with `--no-npc-collision` they are zero and you walk through people.
var _push_m := 0.0
var _push_max := 0.0


func _ready() -> void:
	var a := _args()
	_solid_mode = String(a.get("npc-solid", "separate"))
	if a.has("no-npc-collision"):
		_solid_mode = "off"
	if a.has("crowd-hz"):
		crowd_hz = float(a["crowd-hz"])


## WHICH MECHANISM ACTUALLY RAN, in the verdict, on every run. Anything that can
## substitute a lesser mode for the one asked for has to say which one it used --
## CLAUDE.md's rule, learned from a renderer that silently fell back to OpenGL 3
## and exited 0 with a PNG.
func walker_collider_report() -> String:
	return "%s/%s" % [_solid_mode,
		("every_frame" if crowd_hz <= 0.0 else "%.0fhz" % crowd_hz)]


func push_report() -> String:
	return "push_m=%.2f push_max_mm=%.1f" % [_push_m, _push_max * 1000.0]


## SEPARATE THE PLAYER FROM ANYBODY IT IS INSIDE, ACROSS THE FLOOR ONLY.
##
## Called by `walk.gd` immediately after `player.step()`, so the next frame's
## `move_and_slide` starts from a body that is not overlapping a person. The
## push is the exact overlap of the two circles in the floor plane -- no more,
## so it cannot fling anybody, and no less, so a person cannot be walked into.
##
## THE UP COMPONENT IS PROJECTED OUT AND THAT IS THE WHOLE POINT. On a spun ring
## "up" is radial and different at every angle, so this is the body's own up and
## not a world axis. A separation with any vertical component would put the body
## a millimetre off the deck, and a millimetre off the deck is what this exists
## to stop.
func push_off(delta: float) -> float:
	if _body == null or _solid_mode != "separate":
		return 0.0
	var p: Vector3 = _body.global_position
	var up: Vector3 = (_body.body_up() if _body.has_method("body_up")
		else Vector3.UP)
	var push := Vector3.ZERO
	for w in _walkers:
		push += _overlap(p, up, _walker_xform(w).origin, w.r_m, w.h_m)
	for pr in _people:
		push += _overlap(p, up, pr.pivot, pr.r_m, pr.h_m)
	var l := push.length()
	if l <= 0.0:
		return 0.0
	# NOBODY MOVES YOU FASTER THAN YOU CAN WALK. Uncapped, this was measured
	# putting the body 162 mm sideways in a single frame -- which is what
	# resolving a whole overlap at once looks like when a streamed cell arrives
	# with somebody already standing where the player is. A deep overlap is now
	# paid off over as many frames as it takes, at the player's OWN speed, read
	# off the body rather than written down here.
	var cap: float = maxf(0.01, float(_body.get("speed_m_s")) * delta)
	if l > cap:
		push *= cap / l
		l = cap
	_body.global_position = p + push
	_push_m += l
	_push_max = maxf(_push_max, l)
	return l


## How far, and which way, to move a body at `p` so it is not inside somebody
## standing at `foot` with radius `r` and height `h`. Zero unless the two
## actually overlap, both across the floor and up it.
func _overlap(p: Vector3, up: Vector3, foot: Vector3, r: float,
		h: float) -> Vector3:
	if r <= 0.0 or h <= 0.0:
		return Vector3.ZERO
	var d: Vector3 = p - foot
	# HEIGHT FIRST: somebody on the deck below is not in your way. A body's
	# origin is at its feet, so the two overlap when their spans do.
	var vert: float = d.dot(up)
	if vert > h or vert < -_player_h:
		return Vector3.ZERO
	var flat: Vector3 = d - up * vert
	var want: float = r + _player_r
	var l := flat.length()
	if l >= want:
		return Vector3.ZERO
	if l < 1e-4:
		# Dead centre: any direction will do and none is derivable, so use the
		# station axis, which on a ring deck is across the corridor.
		flat = Vector3(0, 0, 1) - up * up.z
		l = maxf(flat.length(), 1e-4)
	return flat / l * (want - l)



class Person:
	var group: String
	var tag: String = ""             # which streamed cell brought them, "" = all
	var parts: Array = []            # every mesh this body is made of
	var pivot := Vector3.ZERO
	var up := Vector3.UP
	var rest_yaw: float = 0.0        # the yaw the generator baked in
	var yaw: float = 0.0             # where they are looking now
	var noticed := false
	var body: StaticBody3D = null    # what a player bumps into
	var r_m: float = 0.0
	var h_m: float = 0.0


## Counters the streaming gate reads.
var wired_cells := 0
var released_cells := 0
var double_wires := 0
var stale_parts := 0


## Wire the cast list to the meshes it describes.
##
## `tag` names the streamed cell these meshes came from, or "" for a monolithic
## load. Only actors whose meshes are IN this scene are bound, so the whole deck
## cast list can be handed to every cell.
func collect(visual: Node, actors: Array, tag: String = "") -> int:
	# A PERSON IS SEVERAL MESHES. `npc/body.py` tags what it builds -- skin
	# head, torso, arms, hands, feet, hair -- and `populace` now carries those
	# names through so each binds to its own material, which is what stopped all
	# 278 inhabitants rendering as one surface. The consequence here is that the
	# person's OWN group ends up with no faces of its own: the OBJ writer gives
	# each triangle to the last group covering it, and the parts are written
	# after the whole. Matching the exact name found nothing at all.
	if tag != "":
		for p0 in _people:
			if p0.tag == tag:
				double_wires += 1
				push_error("npc: cell %s was wired twice without a release" % tag)
				return _people.size()
		wired_cells += 1
	var before := _people.size()
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
		p.tag = tag
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
	if _solid_mode != "off":
		for i in range(before, _people.size()):
			_give_body(_people[i])
	elif before == 0:
		print("npc: inhabitant collision DISABLED (negative control) -- a "
			+ "person you walk through is a hologram")
	return _people.size() - before


## Give back every person one streamed cell brought, and the capsules with them.
## Called BEFORE the cell is freed: their meshes are about to stop existing and
## a `Person` holding them would be read on the next frame.
func release(tag: String) -> int:
	var keep := []
	var gone := 0
	for p in _people:
		if p.tag == tag and tag != "":
			if p.body != null and is_instance_valid(p.body):
				p.body.queue_free()
			gone += 1
		else:
			keep.append(p)
	_people = keep
	if gone > 0:
		released_cells += 1
	gone += release_crowd(tag)
	return gone


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
	_layer(sb)
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


## Which layer a body a player bumps into sits on, and it is not the world's.
##
## `collision_mask = 0` always: a person is something that gets bumped INTO, and
## has never needed to collide with anything itself. `--npc-solid=mask` puts
## them back on layer 1, which is the build before session 4h and the control
## that has to fail.
func _layer(sb: CollisionObject3D) -> void:
	sb.collision_layer = (1 if _solid_mode == "mask" else PEOPLE_LAYER)
	sb.collision_mask = 0


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


## MEASURED OFF THE BODY, NOT WRITTEN DOWN. The separation needs the player's
## own girth and stature, and `walk.gd::_spawn_player` already decided both. A
## second copy here is a second answer to "how wide is a person", which is the
## failure mode hard rule 4 exists for.
func watch(body: Node3D) -> void:
	_body = body
	for c in body.get_children():
		if c is CollisionShape3D and (c as CollisionShape3D).shape is CapsuleShape3D:
			var cap: CapsuleShape3D = (c as CollisionShape3D).shape
			_player_r = cap.radius
			_player_h = cap.height
			break


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
			# A STREAMED CELL CAN TAKE A PERSON AWAY UNDER YOU. `release()` runs
			# before the cell is freed so this should never fire; it is COUNTED
			# rather than silently skipped, because a person whose meshes have
			# gone and whose record has not is exactly the state that otherwise
			# shows up as a null crash three subsystems away.
			if not is_instance_valid(m):
				stale_parts += 1
				continue
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
	var body: PhysicsBody3D = null
	var r_m: float = 0.0
	var h_m: float = 0.0
	var tag: String = ""      # which streamed cell they belong to
	# -- A COMMUTER IS A WALKER WHO IS NOT ON A LOOP -----------------------
	# Everything above describes somebody going round the ring for ever:
	# `angle` advances at `omega` and never arrives. That is the right model
	# for ambient corridor traffic and it is the wrong one for a resident with
	# a shift to get to, so `free` swaps the ring parameters for a world
	# position and a heading that somebody else decides. It is the SAME body,
	# the SAME MultiMesh bucket and the SAME phase ladder -- see
	# `drive_commuter`, and `station/agenda.py` for who does the deciding.
	var free: bool = false
	var pos: Vector3 = Vector3.ZERO
	var fwd_free: Vector3 = Vector3(0, 0, 1)
	var speed_ms: float = 1.4


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
##
## EVERY LIBRARY IS SIZED FROM THE WHOLE LIST, not just the first. The bucket key
## carries the rung -- `crowd_<species>_<lod>_<phase>` -- so the three libraries
## fill disjoint buckets and each has to see the placement list to know how big
## its own buckets must be.
func build_crowd_multi(libraries: Array, rows: Array) -> int:
	prepare_crowd(libraries, rows)
	add_crowd(rows, "")
	return _walkers.size()


## THE CROWD IS NOT CELL GEOMETRY, and that is why it is allocated once.
##
## A walker is a PLACEMENT against 112 shared bodies -- their meshes live in
## `crowd_lod*.glb`, not in any cell -- so a streamed build cannot get them by
## instancing a cell. What it CAN do is choose who is present: the MultiMeshes
## are sized here from the whole deck's placement list, because
## `MultiMesh.instance_count` cannot grow without reallocating, and `add_crowd`
## then admits the walkers of each cell as it arrives. `_place_crowd` already
## writes only as many transforms as there are walkers, so an unadmitted cell's
## crowd costs nothing.
func prepare_crowd(libraries: Array, all_rows: Array) -> int:
	var n := 0
	for lib in libraries:
		n += _index_library(lib, all_rows)
	return n


## Admit one cell's walkers. `rows` is that cell's slice of the placement list.
func add_crowd(rows: Array, tag: String) -> int:
	var before := _walkers.size()
	for r in rows:
		_walkers.append(_walker_from(r, tag))
	if _solid_mode != "off":
		for i in range(before, _walkers.size()):
			_give_walker_body(_walkers[i])
		# SAY WHICH MECHANISM RAN, once, on every run that has a crowd in it.
		if not _said_collider and _walker_bodies > 0:
			_said_collider = true
			print("npc: walker colliders are %s" % walker_collider_report())
	_place_crowd()
	return _walkers.size() - before


## Take them back with their cell.
func release_crowd(tag: String) -> int:
	if tag == "":
		return 0
	var keep: Array[Walker] = []
	var gone := 0
	for w in _walkers:
		if w.tag == tag:
			if w.body != null and is_instance_valid(w.body):
				w.body.queue_free()
			gone += 1
		else:
			keep.append(w)
	_walkers = keep
	if gone > 0:
		_place_crowd()
	return gone


func _walker_from(r: Dictionary, tag: String) -> Walker:
	var w := Walker.new()
	w.tag = tag
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
	return w


## Build the crowd from the library scene and the placement list.
func build_crowd(library: Node, rows: Array) -> int:
	_index_library(library, rows)
	add_crowd(rows, "")
	return _walkers.size()


## Index one LOD library and allocate its MultiMeshes for a placement list.
##
## Split out of `build_crowd` so a STREAMED build can size the buckets from the
## whole deck before any walker exists -- see `prepare_crowd`. It appends no
## walkers, so calling it twice for the same library would double the buckets;
## `_mm` is keyed by bucket and guarded for that.
func _index_library(library: Node, rows: Array) -> int:
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
	for r in rows:
		var sp := String((r as Dictionary).get("species", "human"))
		per_species[sp] = int(per_species.get(sp, 0)) + 1
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
	for sp2 in per_species:
		for lod in lods:
			for ph in range(8):
				counts["crowd_%s_%d_%d" % [sp2, lod, ph]] = maxi(4, int(ceil(
					float(per_species[sp2]) / 8.0 * 3.0)))
	var made := 0
	for k in counts.keys():
		if not meshes.has(k) or _mm.has(k):
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
			made += 1
	return made


## The capsule a player bumps into as somebody walks past them.
##
## ON `PEOPLE_LAYER` WITH MASK 0, so `move_and_slide` never resolves against it
## and `push_off` does the separating -- see the header. It is still a real
## collider rather than a number in an array, because it is what any future
## query about "is somebody standing there" will ask, and because
## `--npc-solid=mask` has to be able to put exactly it back on the world layer.
##
## AND IT IS PUT WHERE THEY ARE BEFORE IT ENTERS THE TREE. It was not: the
## capsule sat at the world origin, 7 km away, until the next `advance_crowd`
## moved it -- so for the first tenth of a second after a cell arrived, its
## walkers were somewhere else entirely.
func _give_walker_body(w: Walker) -> void:
	if w.r_m <= 0.0 or w.h_m <= 0.0:
		return
	var sb := StaticBody3D.new()
	_walker_bodies += 1
	sb.name = "walker_%s_%d" % [w.species, _walker_bodies]
	_layer(sb)
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = w.r_m
	cap.height = maxf(w.h_m, 2.0 * w.r_m + 0.01)
	cs.shape = cap
	sb.add_child(cs)
	w.body = sb
	sb.transform = _walker_body_xform(w)
	add_child(sb)


## Where a walker is, and which way is up for them. Up is INWARD on a spun
## ring, so it is a different direction at every angle -- which is why the
## generator writes a basis per instance and why this recomputes one rather
## than carrying a yaw.
func _walker_xform(w: Walker) -> Transform3D:
	# A COMMUTER'S FEET ARE WHEREVER THEY GOT TO. Up is still INWARD -- that is a
	# property of standing inside a spun barrel and not of being on a loop -- so
	# it is recomputed from their own position exactly as below; only the
	# position and the heading come from outside.
	if w.free:
		var radial := Vector3(w.pos.x, w.pos.y, 0.0)
		var up2 := (-radial.normalized() if radial.length() > 0.001
			else Vector3.UP)
		var f2 := w.fwd_free - up2 * w.fwd_free.dot(up2)
		if f2.length() < 1e-4:
			f2 = Vector3(0, 0, 1) - up2 * up2.z
		f2 = f2.normalized()
		var r2 := f2.cross(up2).normalized()
		return Transform3D(Basis(r2, up2, f2), w.pos)
	var ca := cos(w.angle)
	var sa := sin(w.angle)
	var up := Vector3(-ca, -sa, 0.0)
	var fwd := Vector3(-sa, ca, 0.0) * signf(w.omega if w.omega != 0.0 else 1.0)
	var right := fwd.cross(up).normalized()
	return Transform3D(Basis(right, up, fwd),
		Vector3(w.radius * ca, w.radius * sa, w.z))


# ---------------------------------------------------------------------------
#  A COMMUTER -- a walker who is going somewhere, and gets there
# ---------------------------------------------------------------------------
# WHY THIS IS A WALKER AND NOT A `Person`. `collect()` binds somebody to the
# meshes they were BAKED as, which is right for a room occupant and impossible
# for a commuter: a baked body is welded into the deck's merged mesh, so the only
# thing a runtime can do with one is show it or hide it, and a resident who winks
# out of their quarters and winks in at their post is not going to work. It also
# costs the deck .glb primitives -- measured across the shipped station, 5.04 per
# baked actor against `budget.BUDGETS["deck_primitives"] = 600`, which two decks
# are already over. An instanced walker costs ZERO: their body is in
# `crowd_lod*.glb` and every walker of one (species, lod, phase) shares one
# MultiMesh.
#
# WHAT IS NOT DECIDED HERE. Where they are. `station/agenda.py` lays the route on
# the corridor `deck.deck_plan` built, `life.gd` puts a CharacterBody3D on the
# collision shell and walks it, and this is handed the result -- so the drawn
# body and the physics body cannot disagree about where somebody is, which is the
# same rule `_walker_body_xform` already applies to the capsule.

## Admit one commuter. Returns their `Walker`, to be handed to `drive_commuter`.
##
## `prepare_crowd` must have been called with a placement list containing this
## row, because a MultiMesh's `instance_count` cannot grow without reallocating.
func add_commuter(row: Dictionary) -> Walker:
	var w := _walker_from(row, "")
	w.free = true
	w.pos = Vector3(float(row.get("x", 0.0)), float(row.get("y", 0.0)),
		float(row.get("z", 0.0)))
	w.speed_ms = maxf(0.01, float(row.get("speed_ms", 1.4)))
	_walkers.append(w)
	if _solid_mode != "off":
		_give_walker_body(w)
	_place_crowd()
	return w


## Put a commuter where their body actually got to, and advance their gait by
## the ground they actually covered.
##
## THE PHASE COMES FROM DISTANCE, NOT FROM TIME, and that is the difference
## between this and `advance_crowd`. A loop walker's `omega` and `cycle_s` come
## from the same `walk_clip`, so time and distance agree by construction. A
## commuter is steered by a character controller that scrapes walls, waits at
## doors and is capped at its own speed -- so the only quantity that keeps the
## feet on the ground is how far they moved.
func drive_commuter(w: Walker, at: Vector3, heading: Vector3,
		moved_m: float) -> void:
	if w == null:
		return
	w.pos = at
	if heading.length_squared() > 1e-8:
		w.fwd_free = heading.normalized()
	_crowd_travel_m += moved_m
	w.t += moved_m / w.speed_ms
	w.phase = int(floor(w.t / w.cycle_s * 8.0)) % 8
	if w.body != null:
		w.body.global_transform = _walker_body_xform(w)
	_place_crowd()


## Where a walker's CAPSULE stands. Their own transform raised half a height
## along their own up, because a Godot capsule is centred on its origin and a
## walker's origin is their feet.
##
## ONE FORMULA, TWO CALLERS. It was written out twice -- once where the body is
## made and once where it moves -- and the two were not the same: the first
## never ran at all, so every capsule spent its first frames at the world
## origin.
func _walker_body_xform(w: Walker) -> Transform3D:
	var xf := _walker_xform(w)
	return Transform3D(xf.basis,
		xf.origin + xf.basis.y * (maxf(w.h_m, 2.0 * w.r_m + 0.01) * 0.5))


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


## How often the crowd advances, in hertz. **0 -- the default -- is every
## physics frame**, and that is a change from the 10 Hz this shipped with.
##
## THE OLD NUMBER WAS MEASURED AGAINST THE WRONG QUESTION, and this is the
## lesson rather than the setting. 10 Hz was justified by a bound on POSITION
## ERROR: "a walker moves 0.145 m between updates -- under the 0.22 m tile they
## are stepping on". True, and it says nothing about the two things the rate
## actually costs. A body redrawn ten times a second is a body animated at
## **10 fps**; and its collider crosses the whole 0.145 m in ONE step, into
## whoever is standing there.
##
## AND THE COST IT WAS TRADED AGAINST IS NOT THERE ANY MORE. The claim was that
## at 60 Hz "a deck's crowd cost more than the rest of the walk gate put
## together", and it was measured before the MultiMesh buckets were sized to what
## can be in them rather than to the whole species -- eight times the crowd
## uploaded every frame. Re-measured on the visit gate, same 16,200 frames, same
## deck: **67 s with no crowd at all and 68 s with the crowd drawing at 10 Hz**,
## so 2,700 updates of 134 walkers cost about a second. The whole of the 86 s the
## crowd used to add was its COLLIDERS, and those are off the player's mask now.
##
## `--crowd-hz=10` restores the old cadence exactly -- state, collider and draw
## together -- so it is the control for this half of the fix.
@export var crowd_hz: float = 0.0

var _crowd_dt: float = 0.0


func advance_crowd(delta: float) -> void:
	if _walkers.is_empty():
		return
	# THROTTLED ONLY IF ASKED. When it is, the accumulated delta is replayed in
	# one step, so the crowd covers the same ground either way and
	# `crowd_travel_m` cannot tell the two apart -- which is what makes it a
	# control on the SHOVE rather than on how far anybody walked.
	if crowd_hz > 0.0:
		_crowd_dt += delta
		if _crowd_dt < 1.0 / crowd_hz:
			return
		delta = _crowd_dt
		_crowd_dt = 0.0
	var eye := (_body.global_position if _body != null else Vector3.ZERO)
	for w in _walkers:
		var d: float = w.omega * delta
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
		# THE CAPSULE GOES WHERE THE BODY GOES. The drawn body and the thing a
		# player bumps into come from ONE call, so they cannot disagree about
		# where somebody is -- and `push_off` reads the same function again
		# rather than the capsule's transform, so a third answer is impossible.
		if w.body != null:
			w.body.global_transform = _walker_body_xform(w)
	_place_crowd()
