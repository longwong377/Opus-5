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


## ---------------------------------------------------------------------------
##  AND A BODY ON THE DECK IS SOMETHING YOU WALK AROUND, NOT THROUGH
## ---------------------------------------------------------------------------
## `ragdoll.gd` excepts the player's RID from every physical bone, deliberately
## and for the reason at the top of this file: a `CharacterBody3D` touching
## ANYTHING has its floor snap refused, so sixteen bone colliders on the player's
## mask is the pre-4h floor-loss hazard multiplied by sixteen. `--ragdoll-solid`
## removes the exception and reproduces exactly that.
##
## So a settled ragdoll was a hologram: `STATE.md` §24.5, *"a settled ragdoll does
## not push the player aside the way a standing person does"*. The separation has
## to be done by hand here, and it is the SAME hand -- `push_off` already
## separates the player from a walker and from a baked person, across the floor
## plane only, capped at the player's own speed. This adds the third kind of body
## to the same loop rather than writing a second one.
##
## `--no-ragdoll-push` is the control: the corpse goes back to being a hologram.
var _ragdolls: Node = null
var _rag_bones: Array = []          ## PhysicalBone3D, rebuilt when the set moves
var _rag_stamp := -1
var _rag_push := true
var _push_rag_m := 0.0
var _push_rag_max := 0.0
var _rag_seen := 0                  ## segments considered on the last frame


func _ready() -> void:
	var a := _args()
	_solid_mode = String(a.get("npc-solid", "separate"))
	if a.has("no-npc-collision"):
		_solid_mode = "off"
	if a.has("no-ragdoll-push"):
		_rag_push = false
		print("npc: a body on the deck is a HOLOGRAM (control) -- the player "
			+ "walks through settled ragdolls, which is the build before "
			+ "session 4r")
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
	return ("push_m=%.2f push_max_mm=%.1f rag_push_m=%.3f rag_push_max_mm=%.1f "
		% [_push_m, _push_max * 1000.0, _push_rag_m, _push_rag_max * 1000.0]
		+ "rag_segments=%d%s" % [_rag_seen, ("" if _rag_push else " (OFF)")])


## Where the ragdoll director is, so a body on the deck can be walked around.
##
## TWO ROUTES, BOTH CHEAP, AND NEITHER IS A TREE SCAN. `promote_walker` is handed
## the director by whoever fires an incident, so the first collapse binds it for
## free; `walk.gd` also offers it the node `main.gd` builds. Whichever arrives
## first wins and the second is a no-op -- there is only ever one director.
func watch_ragdolls(director: Node) -> void:
	if director == null or _ragdolls == director:
		return
	if not director.has_method("promote"):
		push_error("npc: watch_ragdolls was handed a %s, which is not a ragdoll "
			% director.get_class() + "director")
		return
	_ragdolls = director
	_rag_stamp = -1


func ragdoll_director() -> Node:
	return _ragdolls


## Every physical bone of every promoted body, as [Transform3D, a, b, radius] in
## world space -- a capsule per segment.
##
## THE SHAPE IS AN APPROXIMATION AND HERE IS EXACTLY WHAT IS LOST. `ragdoll.py`
## solves each segment as a capsule or a BOX -- **7 of a human's 16 are boxes**:
## pelvis, spine, chest, both wrists, both ankles. This treats a box as a capsule
## down its own longest axis with the radius that CIRCUMSCRIBES the other two
## half-extents, so a chest is separated as the cylinder around it rather than as
## the box. The error is one-sided and OUTWARD: at the corners of a box segment
## the player is held `sqrt(h_i^2 + h_j^2) - max(h_i, h_j)` further away than the
## collision shape itself would hold them. Measured off the emitted
## `human_ragdoll.json` rather than estimated: **worst 33.2 mm at the spine**,
## 14.1 mm at the chest, 9.2 mm at the pelvis, 7.2 mm at a wrist. Nobody can walk
## into a body; a player standing beside one is up to 33 mm further off than the
## mesh, at one attitude of one segment.
##
## The alternative is a box-vs-capsule separation, which is a second collision
## routine in a file that has one, and `_overlap`'s whole design note is that the
## separation must be trivially horizontal or it costs the floor. INV-482.
func _ragdoll_segments() -> Array:
	if _ragdolls == null:
		return []
	if not is_instance_valid(_ragdolls):
		_ragdolls = null
		_rag_bones = []
		return []
	# A DOLL ROOT IS `queue_free`d ON DEMOTION, so the child count is the cheap
	# tell that the set has changed. Validity is checked anyway, because a free
	# lands at the end of a frame and this can run before it.
	var n := _ragdolls.get_child_count()
	if n != _rag_stamp:
		_rag_stamp = n
		_rag_bones = []
		for c in _ragdolls.get_children():
			_collect_bones(c, _rag_bones)
	var out: Array = []
	var live := false
	for pb in _rag_bones:
		if not is_instance_valid(pb):
			live = true
			continue
		var b := pb as PhysicalBone3D
		var cs: CollisionShape3D = null
		for c in b.get_children():
			if c is CollisionShape3D:
				cs = c
				break
		if cs == null or cs.shape == null:
			continue
		var xf: Transform3D = cs.global_transform
		var r := 0.0
		# THE AXIS IS PICKED, NEVER REBUILT INTO A BASIS. Swapping two columns of
		# a `Basis` to move the long axis into +Y mirrors it -- determinant -1 --
		# and this project has already paid six sessions for one of those.
		var axis := Vector3.ZERO
		if cs.shape is CapsuleShape3D:
			var cap := cs.shape as CapsuleShape3D
			r = cap.radius
			axis = xf.basis.y.normalized() * maxf(0.0,
				cap.height * 0.5 - cap.radius)
		elif cs.shape is BoxShape3D:
			var h: Vector3 = (cs.shape as BoxShape3D).size * 0.5
			# The longest local axis is the segment; the other two give the
			# circumscribing radius. See the docstring for what that costs.
			if h.y >= h.x and h.y >= h.z:
				r = sqrt(h.x * h.x + h.z * h.z)
				axis = xf.basis.y.normalized() * h.y
			elif h.x >= h.z:
				r = sqrt(h.y * h.y + h.z * h.z)
				axis = xf.basis.x.normalized() * h.x
			else:
				r = sqrt(h.x * h.x + h.y * h.y)
				axis = xf.basis.z.normalized() * h.z
		else:
			continue
		out.append([xf.origin + axis, xf.origin - axis, r])
	if live:
		_rag_stamp = -1
	return out


## The middle of the promoted bodies, for something that wants to walk at one.
## `Vector3.ZERO` when there are none -- no body is on the station's axis.
func ragdoll_centre() -> Vector3:
	var segs: Array = _ragdoll_segments()
	if segs.is_empty():
		return Vector3.ZERO
	var c := Vector3.ZERO
	for s in segs:
		c += ((s[0] as Vector3) + (s[1] as Vector3)) * 0.5
	return c / float(segs.size())


func _collect_bones(node: Node, out: Array) -> void:
	if node is PhysicalBone3D:
		out.append(node)
	for c in node.get_children():
		_collect_bones(c, out)


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
		if w.hidden:
			continue          # somebody who is not in the room is not in the way
		push += _overlap(p, up, _walker_xform(w).origin, w.r_m, w.h_m)
	for pr in _people:
		push += _overlap(p, up, pr.pivot, pr.r_m, pr.h_m)
	# AND ANYBODY WHO IS ON THE FLOOR RATHER THAN ON THEIR FEET. A lying body is
	# not a standing capsule, so each segment is separated as its own capsule --
	# `_ragdoll_segments` states the approximation and its 48 mm cost. The push is
	# accumulated into the SAME vector and capped by the SAME cap below: a corpse
	# cannot shove the player faster than the player walks, and it cannot move
	# them vertically at all, which is the invariant this whole function exists
	# for.
	var segs: Array = _ragdoll_segments()
	_rag_seen = segs.size()
	var before: Vector3 = push
	# THE SEGMENTS ARE STILL COUNTED WITH THE CONTROL ON. A control that also
	# removes the measurement proves nothing: `--no-ragdoll-push` has to leave the
	# gate able to see the body it is walking through.
	if _rag_push:
		for s in segs:
			push += _seg_overlap(p, up, s[0], s[1], float(s[2]))
	var rag: float = (push - before).length()
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
		# THE ATTRIBUTION IS SCALED WITH IT. Reported uncapped, the corpse's share
		# came out LARGER than the total push it is part of -- 10.270 against
		# 10.01 m on the gate's own first run -- which is not a number anybody can
		# read.
		rag *= cap / l
		l = cap
	_body.global_position = p + push
	_push_m += l
	_push_max = maxf(_push_max, l)
	# COUNTED SEPARATELY so "the corpse moved me" and "the crowd moved me" are two
	# numbers rather than one. Attributed before the cap, since the cap is shared.
	if rag > 0.0:
		_push_rag_m += rag
		_push_rag_max = maxf(_push_rag_max, rag)
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


## The same question for a body that is LYING DOWN: how far, and which way, to
## move the player at `p` so they are not inside the capsule from `a` to `b` of
## radius `r`.
##
## THE PLAYER IS A VERTICAL CAPSULE AND THE SEGMENT IS AN ARBITRARY ONE, and this
## decomposes that into the two questions `_overlap` already asks -- do the two
## spans overlap ALONG up, and how close are their axes ACROSS it. That is exact
## when the segment is horizontal, which is what a settled body's segments mostly
## are, and it over-separates by at most `r * (1 - cos(tilt))` on a segment
## standing on end -- a forearm at 45 degrees is 29.3% of its own 43.3 mm radius
## (`elbow_r` in `human_ragdoll.json`), i.e. **12.7 mm**, and a thigh at 45
## degrees is 23.4 mm of its 79.9. Solving the true capsule-capsule distance would
## give a push with a component ALONG up, and a push along up is precisely what
## costs a `CharacterBody3D` its floor. The approximation is not a shortcut; it
## is the constraint.
func _seg_overlap(p: Vector3, up: Vector3, a: Vector3, b: Vector3,
		r: float) -> Vector3:
	if r <= 0.0:
		return Vector3.ZERO
	var da: Vector3 = a - p
	var db: Vector3 = b - p
	var va: float = da.dot(up)
	var vb: float = db.dot(up)
	# HEIGHT FIRST, exactly as above: a body on the deck below is not in the way.
	# The segment's own span is padded by its radius at both ends; the player's is
	# their capsule, feet at 0.
	if minf(va, vb) - r > _player_h or maxf(va, vb) + r < 0.0:
		return Vector3.ZERO
	var fa: Vector3 = da - up * va
	var fb: Vector3 = db - up * vb
	var e: Vector3 = fb - fa
	var ee: float = e.length_squared()
	# The closest point on the flattened segment to the player's own axis.
	var t: float = (0.0 if ee < 1e-12
		else clampf(-fa.dot(e) / ee, 0.0, 1.0))
	var c: Vector3 = fa + e * t
	var want: float = r + _player_r
	var l := c.length()
	if l >= want:
		return Vector3.ZERO
	if l < 1e-4:
		# Standing on the body's own axis: no direction is derivable from the
		# geometry, so use the station axis, which on a ring deck is across the
		# corridor. Same rule as `_overlap`.
		var away: Vector3 = Vector3(0, 0, 1) - up * up.z
		return away.normalized() * want
	return -c / l * (want - l)


## The player's clearance from the nearest promoted body, in metres, measured the
## way `_seg_overlap` measures it: negative means inside. Read by the corpse gate
## in `walk.gd` -- and it is the SAME function, so the gate cannot pass by
## measuring something the separation does not use.
func nearest_ragdoll_clearance() -> float:
	if _body == null:
		return INF
	var segs: Array = _ragdoll_segments()
	if segs.is_empty():
		return INF
	var p: Vector3 = _body.global_position
	var up: Vector3 = (_body.body_up() if _body.has_method("body_up")
		else Vector3.UP)
	var best := INF
	for s in segs:
		var da: Vector3 = (s[0] as Vector3) - p
		var db: Vector3 = (s[1] as Vector3) - p
		var va: float = da.dot(up)
		var vb: float = db.dot(up)
		if minf(va, vb) - float(s[2]) > _player_h or maxf(va, vb) + float(s[2]) < 0.0:
			continue
		var fa: Vector3 = da - up * va
		var fb: Vector3 = db - up * vb
		var e: Vector3 = fb - fa
		var ee: float = e.length_squared()
		var t: float = (0.0 if ee < 1e-12 else clampf(-fa.dot(e) / ee, 0.0, 1.0))
		best = minf(best, (fa + e * t).length() - (float(s[2]) + _player_r))
	return best



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
	# `up.cross(fwd)`, NOT `fwd.cross(up)` -- see `_walker_xform`. Invisible
	# here, because a capsule is symmetric about its own Y and a mirrored one
	# collides identically; fixed anyway, because the next person to copy this
	# block will copy it onto something that is not a capsule.
	var right := up.cross(fwd).normalized()
	fwd = right.cross(up).normalized()
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
## BOTH CROWDS, and that is the fix rather than a tidy-up. These two numbers are
## what `walkable.py --deck` asserts W5 on -- "somebody notices you walk in" --
## and they counted `_people` only. When `populace.ROOM_INSTANCED` moved room
## occupants into the MultiMesh buckets, `_people` went empty for those rooms
## and the gate correctly reported 0 noticed and 0 degrees turned. Reading one
## crowd and asserting about "the room" is the same defect as the turn itself,
## one level up: the question is about people, not about which container they
## happen to be drawn from.
func turned_deg() -> float:
	var most := 0.0
	for p in _people:
		most = maxf(most, absf(rad_to_deg(wrapf(p.yaw - p.rest_yaw,
			-PI, PI))))
	for w in _walkers:
		if not w.hidden:
			most = maxf(most, absf(rad_to_deg(w.notice_yaw)))
	return most


func noticed_count() -> int:
	var n := 0
	for p in _people:
		if p.noticed:
			n += 1
	for w in _walkers:
		if w.noticed and not w.hidden:
			n += 1
	return n


## How far off the nearest person is from actually facing `target`, in degrees.
##
## "DID THEY TURN" IS NOT THE QUESTION. A body rotated by a wrong yaw convention
## turns just as far as one rotated by the right one, and reports the same
## number -- which is how the deck assembler nearly shipped every inhabitant
## facing however far round the ring their room happened to sit. This asks
## whether they ended up LOOKING AT YOU.
## BOTH CROWDS, for the same reason `noticed_count` reads both. Reading
## `_people` alone returned the -1 "nobody in range" sentinel on a deck where
## twenty instanced occupants had just turned to look at the player, and the
## walk gate treats -1 as a failure -- correctly, since it cannot tell "nobody
## was near" from "nothing measured them". So the fix that made them turn had
## to reach this function too, or W5 would have gone from NOBODY NOTICED to
## THE YAW CONVENTION IS WRONG and looked like a regression.
##
## A WALKER'S ERROR IS MEASURED OFF THE TRANSFORM THEY ARE ACTUALLY DRAWN WITH,
## not off `notice_yaw` alone. That is the whole point of the check: a turn
## applied with the wrong sign, or about the wrong axis, produces exactly the
## same `notice_yaw` and a body facing the other way. Asking the finished basis
## where its +Z points is the only form that can catch it.
func facing_error_deg(target: Vector3) -> float:
	var best := 1e30
	var err := -1.0
	for p in _people:
		var d := target.distance_to(p.pivot)
		if d < best and d <= notice_m:
			best = d
			err = absf(rad_to_deg(wrapf(_yaw_towards(p, target) - p.yaw,
				-PI, PI)))
	for w in _walkers:
		if w.hidden:
			continue
		var xf := _walker_xform(w)
		var d2 := target.distance_to(xf.origin)
		if d2 < best and d2 <= notice_m:
			best = d2
			var up := xf.basis.y.normalized()
			var to := target - xf.origin
			to = to - up * to.dot(up)
			if to.length() < 0.01:
				continue
			var f := xf.basis.z.normalized()
			f = (f - up * f.dot(up)).normalized()
			err = absf(rad_to_deg(f.signed_angle_to(to.normalized(), up)))
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
	# -- AN INSTANCED PERSON CAN TURN TO LOOK AT YOU ------------------------
	# `notice_yaw` is a rotation about this walker's OWN up, applied in
	# `_walker_xform` on top of whichever heading they already have. It is a
	# separate field rather than a mutation of `angle`/`fwd_free` because those
	# are where they are GOING and this is where they are LOOKING: a commuter
	# who glances at you must still arrive at their post.
	#
	# Until 4r there was no such field and no such turn. `populace.ROOM_INSTANCED`
	# (4p) moved room occupants out of baked meshes into these buckets, and the
	# code that turns somebody -- `_people` / `Person` -- finds its subjects by
	# matching actor group names against MeshInstance3D NAMES. An instanced
	# occupant has no per-person mesh, so it had no Person, so nobody looked up:
	# `walkable.py --deck blue/0/0` reported "reached docking_bays and NOBODY
	# noticed -- 0.0 deg turned". Two crowd systems, and only one of them could
	# see you.
	var notice_yaw: float = 0.0
	var noticed: bool = false
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
	# -- AN OCCUPANT IS A WALKER WHO LIVES SOMEWHERE ------------------------
	# The third kind, and it is the one this class existed to make possible.
	# A loop walker never arrives; a commuter is steered by a physics body;
	# an OCCUPANT is a pure function of the station clock -- `day` is the
	# timetable `populace.occupant_day` derived from that resident's own
	# species rhythm, role and shift, and everything below is where they are
	# when they are doing each thing. Nothing here integrates, so walking out
	# of a room and coming back gives the answer the room would have had:
	# `life.gd`'s architecture, applied to the half of the crowd that could
	# not have it while it was welded into the deck.
	var occupant: bool = false
	var hidden: bool = false          # away: drawn nowhere, collides nothing
	var day: Array = []               # [[hour, state], ...] transitions
	var anchor: Vector3 = Vector3.ZERO
	var up_a: Vector3 = Vector3.UP    # their own up, cached from the anchor
	var tang: Vector3 = Vector3.ZERO  # room x, carried onto the ring
	var axis: Vector3 = Vector3(0, 0, 1)
	var seat_off: Vector3 = Vector3.ZERO
	var has_seat: bool = false
	var bunk_off: Vector3 = Vector3.ZERO
	var has_bunk: bool = false
	var exit_off: Vector3 = Vector3.ZERO
	var talks: bool = false
	var yaw0: float = 0.0
	var state: String = ""
	var changes: int = 0              # how many times they have changed state
	var who_name: String = ""
	var place: String = ""
	var moved_m: float = 0.0          # ground they have covered, in metres


## How many phases one walk cycle is cut into. The generator's own
## `populace.CROWD_PHASES`, and the bucket key's index is a phase only below
## this -- at and above it the index is a POSE, which is what lets a room
## occupant sit, sleep or talk without the bucket sort learning a second shape.
const WALK_PHASES := 8

## The pose slots, in `populace.POSE_SLOTS` order. Named here because a state
## machine has to be able to ask for "the sleeping body" by something other than
## the number 10; the NUMBERS are not written down -- `_slots` below is measured
## off the library that was actually loaded, so a library with more poses in it
## than this build knows about still allocates correctly.
const SLOT_IDLE := 8
const SLOT_SIT := 9
const SLOT_SLEEP := 10
const SLOT_TALK := 11

var _walkers: Array[Walker] = []
var _mm: Dictionary = {}          # "crowd_human_4_3" -> MultiMeshInstance3D
var _mm_rows: Dictionary = {}     # the same key -> Array[Walker] this frame
## Highest slot index the loaded library actually carries, plus one. MEASURED
## off the library rather than declared: a build whose `crowd_lod*.glb` predates
## the poses has 8, and allocating 12 buckets for it would size four MultiMeshes
## per species per rung that can never be filled.
var _slots := WALK_PHASES


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
	dress_crowd()
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
	dress_crowd()
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
	# HOW MANY SLOTS THIS LIBRARY HAS, read off its own mesh names. A walk phase
	# and a pose share one index axis (see `WALK_PHASES`), so the count is the
	# largest index present plus one -- 8 for a library baked before the poses
	# existed, 12 for one baked after. Declaring it instead would allocate
	# buckets for meshes that are not there.
	for k0 in meshes.keys():
		var bits := String(k0).split("_")
		if bits.size() >= 4:
			_slots = maxi(_slots, int(bits[bits.size() - 1]) + 1)
	var counts := {}
	for sp2 in per_species:
		for lod in lods:
			for ph in range(_slots):
				# A POSE BUCKET IS NOT AN EIGHTH OF ANYTHING. Walkers spread over
				# eight phases so a phase bucket holds about an eighth; an
				# occupant sits in ONE pose for hours, and at 03:00 every sleeper
				# in a residential block is in the same bucket. So a pose bucket
				# is sized to the whole species and a phase bucket keeps the
				# three-eighths slack `_place_crowd` clamps against.
				counts["crowd_%s_%d_%d" % [sp2, lod, ph]] = (
					maxi(4, int(per_species[sp2])) if ph >= WALK_PHASES
					else maxi(4, int(ceil(float(per_species[sp2]) / 8.0 * 3.0))))
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


# ---------------------------------------------------------------------------
# The crowd's clothes
# ---------------------------------------------------------------------------

## What `dress_crowd` last found. Read by tools/crowd_material_gate.py and
## printed on every run that has a crowd in it.
var crowd_mm_total := 0        ## buckets offered to the binder
var crowd_mm_bound := 0        ## buckets that came back wearing the wardrobe
var crowd_unmatched := PackedStringArray()   ## group names no rule matched
var crowd_dress_why := "not run"
var _dressed := {}             ## bucket node -> true, so a re-index is cheap


## Put the measured wardrobe on the crowd. INSTANCE TEN OF THIS PROJECT'S
## SIGNATURE DEFECT, CLOSED HERE.
##
## `_index_library` has always named every bucket after its material key, and
## the ten-line comment above it says the name exists FOR THE BINDER. Nothing
## called the binder. The two shipped callers of `dress_scene.bind` each pass a
## root that cannot contain the crowd -- `walk.gd` passes the level scene and
## `stream.gd` passes one cell's visual root -- while the buckets hang off THIS
## node. So 2,148 bodies across the three shipped libraries reached the frame on
## the glTF importer's default material, and that default is not "no material":
## it is a StandardMaterial3D with `albedo_color = (1,1,1,1)` and no textures.
## An untextured white mannequin, literally, at 2.6 m from the camera.
##
## WHY THE OBVIOUS CHECK GOES GREEN, because it did when this was written.
## Asking "does the bucket have a material" reports 504 of 504 on an UNFIXED
## build, since Godot manufactures that white default per surface. The only
## question worth asking is whether the material is THE ONE `material_rules`
## binds to the bucket's own name, which is what `dress_scene.bind` answers and
## what `crowd_unmatched` reports.
##
## IT OWNS ITS OWN DRESSER RATHER THAN BORROWING ONE. `walk.gd` releases its
## dresser immediately after the monolithic bind, so a borrowed reference would
## be alive on the streamed path and dead on the other -- and a dead dresser's
## `bind` returns zeros, which reads exactly like success. A second instantiate
## of `interior.tscn` costs one scene: every Material under it is already in
## Godot's resource cache by the time a crowd exists, because the deck was
## dressed from the same table.
##
## BEST EFFORT, LOUDLY, and `--no-dress` still means what it says. This must
## never fail a walk test -- what colour somebody's coat is has no bearing on
## whether a player can stand up -- so every failure prints its reason and
## leaves the crowd drawable.
func dress_crowd() -> Dictionary:
	var todo: Array[MultiMeshInstance3D] = []
	for k in _mm.keys():
		for mmi in _mm[k]:
			if not _dressed.has(mmi):
				todo.append(mmi)
	if todo.is_empty():
		return {"total": crowd_mm_total, "bound": crowd_mm_bound}
	crowd_mm_total += todo.size()

	# THE SAME FLAG walk.gd READS, and read the same way. With `--no-dress` the
	# build is grey geometry under a flat ambient and that control has to keep
	# covering the people; a crowd that dressed itself anyway would make the
	# control a lie about half the frame.
	for a in OS.get_cmdline_user_args():
		if String(a) == "--no-dress":
			crowd_dress_why = "disabled by --no-dress (control)"
			for mmi in todo:
				_dressed[mmi] = true
			print("npc: crowd dressing DISABLED (control) -- %d bucket(s) stay "
				% todo.size() + "on the glTF default, which is flat white")
			return {"total": crowd_mm_total, "bound": crowd_mm_bound}

	var scr := load("res://scripts/dress_scene.gd")
	if scr == null:
		crowd_dress_why = "dress_scene.gd did not load"
		push_error("npc: crowd NOT dressed -- " + crowd_dress_why)
		print("npc: crowd NOT dressed -- %s" % crowd_dress_why)
		return {"total": crowd_mm_total, "bound": crowd_mm_bound}
	var dress := Node.new()
	dress.name = "CrowdDress"
	dress.set_script(scr)
	add_child(dress)
	if not dress.call("prepare"):
		crowd_dress_why = ", ".join(dress.get("problems"))
		push_error("npc: crowd NOT dressed -- " + crowd_dress_why)
		print("npc: crowd NOT dressed -- %s" % crowd_dress_why)
		dress.queue_free()
		return {"total": crowd_mm_total, "bound": crowd_mm_bound}

	# A HOLDER WITH EXACTLY THE BUCKETS IN IT. `bind` walks a subtree, and this
	# node's other children are walker colliders and the dresser itself; handing
	# it `self` would work today and quietly start binding a walker's collision
	# capsule the day one carries a mesh. Reparented back immediately.
	var holder := Node3D.new()
	holder.name = "CrowdDressHolder"
	add_child(holder)
	for mmi in todo:
		remove_child(mmi)
		holder.add_child(mmi)
	var m: Dictionary = dress.call("bind", holder)
	for mmi in todo:
		holder.remove_child(mmi)
		add_child(mmi)
		_dressed[mmi] = true
	holder.queue_free()
	dress.call("release")
	dress.queue_free()

	crowd_mm_bound += int(m.get("multimesh_bound", 0))
	var un: PackedStringArray = m.get("unmatched", PackedStringArray())
	for u in un:
		if not crowd_unmatched.has(u):
			crowd_unmatched.append(u)
	var nul: PackedStringArray = m.get("ruled_but_null", PackedStringArray())
	crowd_dress_why = "ok"
	if not nul.is_empty():
		crowd_dress_why = "%d rule(s) resolved to NULL" % nul.size()
		push_error("npc: %d crowd group(s) matched a material rule that "
			% nul.size() + "resolved to NULL -- the material library did not "
			+ "load; the crowd is the glTF default, which is flat white")
	print("npc: crowd %d/%d bucket(s) MATERIALLED%s%s"
		% [crowd_mm_bound, crowd_mm_total,
			("" if un.is_empty() else ", %d on the glTF default: %s"
				% [un.size(), ", ".join(un.slice(0, 6))]),
			("" if nul.is_empty() else ", %d rule(s) NULL: %s"
				% [nul.size(), ", ".join(nul.slice(0, 6))])])
	return {"total": crowd_mm_total, "bound": crowd_mm_bound}


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
## WHY THE LAST `promote_walker` CAME BACK EMPTY. An empty return has four
## different causes and they need four different fixes -- no crowd in the build,
## a cell that has not streamed, a radius too tight, or the director refusing --
## so the caller is told which. `_collapse` prints it.
var promote_why := ""


## Hand the nearest person to `at` over to the ragdoll director and take them
## out of the crowd. Returns who fell, or "" if nobody was close enough.
##
## THIS IS WHAT MAKES A COLLAPSE A PERSON RATHER THAN A PROP. `ragdoll.gd` can
## drop a body anywhere; dropping one where nobody was standing is a corpse
## appearing out of the air. So the body comes OUT OF THE CROWD: a walker who
## was there a moment ago stops being drawn, and the ragdoll takes their place,
## their species, their stature and their heading.
##
## The three states that have to move together, and each one bit me:
##   * `hidden` -- out of every MultiMesh bucket, or the crowd keeps drawing a
##     standing copy of somebody lying on the floor.
##   * `collision_layer = 0` -- out of `push_off`'s way, or the player is
##     shouldered aside by a person who is no longer there.
##   * `restore` -- both of the above put back on demotion, because
##     `INC-SICK`'s subject GETS UP, and a walker who came back invisible would
##     be a hole in the crowd that never closes.
##
## `_place_crowd()` at the end is not optional: the buckets are rebuilt from
## `hidden`, so without it the change is in the data and not on the screen.
## `want_species` IS NOT COSMETIC. The incident names a person -- David Allan,
## human -- and the body comes out of the crowd, so without this the nearest
## walker is taken whatever they are and a human's collapse is played by a
## Drazi. Matching first and falling back to the nearest ANYBODY is the honest
## order, and `promote_why` records which of the two happened so a run can say
## whether its casualties were the right species.
func promote_walker(director: Node, spec: Dictionary, at: Vector3,
		radius_m: float = 12.0, want_species: String = "") -> String:
	promote_why = ""
	if director == null:
		promote_why = "no ragdoll director"
		return ""
	# WHOEVER FIRES A COLLAPSE HAS ALREADY FOUND THE DIRECTOR, so `push_off` gets
	# it for nothing and never has to search a tree of several thousand nodes for
	# it. See `watch_ragdolls`.
	watch_ragdolls(director)
	if _walkers.is_empty():
		promote_why = "this build has no crowd at all"
		return ""
	var best: Walker = null
	var best_d := radius_m * radius_m
	var any: Walker = null
	var any_d := radius_m * radius_m
	# THE NEAREST ANYBODY, whether or not they are in range. Without it the
	# failure reads "nobody within 12 m" and says nothing about whether the
	# crowd is 13 m away or on the other side of the station -- which is the
	# difference between a radius to widen and a cell that has not streamed.
	var nearest := INF
	var shown := 0
	for w in _walkers:
		if w.hidden:
			continue
		shown += 1
		var d: float = _walker_xform(w).origin.distance_squared_to(at)
		nearest = minf(nearest, d)
		if d < any_d:
			any_d = d
			any = w
		if want_species != "" and w.species != want_species:
			continue
		if d < best_d:
			best_d = d
			best = w
	var matched := best != null
	if best == null:
		best = any
	if best == null:
		promote_why = ("nobody within %.0f m -- %d of %d walkers drawn, "
			% [radius_m, shown, _walkers.size()]
			+ ("none at all" if shown == 0
				else "nearest %.1f m" % sqrt(nearest)))
		return ""
	var xf := _walker_xform(best)
	var was := best.hidden
	best.hidden = true
	if best.body != null:
		best.body.collision_layer = 0
	var w2 := best
	spec["species"] = w2.species
	spec["h_m"] = w2.h_m
	spec["xform"] = xf
	# THE MOMENTUM THEY ALREADY HAD. Somebody who collapses mid-stride does not
	# stop first. `omega * radius` is the tangential speed the ring walker was
	# carrying and `basis.z` is the way they were facing -- both read off the
	# same transform the body is dropped into, so they cannot disagree.
	spec["velocity"] = xf.basis.z * absf(w2.omega) * w2.radius
	spec["restore"] = func():
		w2.hidden = was
		if w2.body != null:
			w2.body.collision_layer = PEOPLE_LAYER
		_place_crowd()
	var doll = director.call("promote", spec)
	if doll == null:
		promote_why = ("the director refused (%s) -- %s, det=%.3f"
			% [String(director.get("_why_refused")), w2.species,
				xf.basis.determinant()])
		# REFUSED -- put them straight back. A cap reached or a species with no
		# body data is not a reason for somebody to vanish.
		best.hidden = was
		if best.body != null:
			best.body.collision_layer = PEOPLE_LAYER
		return ""
	_place_crowd()
	promote_why = ("the nearest %s, %.1f m away"
		% [w2.species, sqrt(best_d if matched else any_d)]
		if matched else
		"NO %s in reach -- the nearest anybody, a %s %.1f m away"
		% [want_species, w2.species, sqrt(any_d)])
	# WHO ACTUALLY FELL, which is not always who the incident named. A corridor
	# walker is anonymous by construction -- `who_name` is empty on the ring
	# crowd and set only on a room occupant bound to a resident -- so this
	# returns the person when there is one and the species when there is not,
	# and never borrows the incident's name for a body that is not theirs.
	return (w2.who_name if w2.who_name != "" else "a " + w2.species)


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
		f2 = _turned(f2.normalized(), up2, w.notice_yaw)
		var r2 := up2.cross(f2).normalized()
		return Transform3D(Basis(r2, up2, f2), w.pos)
	var ca := cos(w.angle)
	var sa := sin(w.angle)
	var up := Vector3(-ca, -sa, 0.0)
	var fwd := Vector3(-sa, ca, 0.0) * signf(w.omega if w.omega != 0.0 else 1.0)
	# `up.cross(fwd)`, AND IT WAS `fwd.cross(up)` UNTIL SESSION 4q, WHICH IS A
	# MIRROR. `Basis(x, y, z)` takes the three COLUMNS and is right-handed only
	# when x cross y = z. With `right = fwd x up` that product is MINUS fwd, so
	# the determinant is exactly -1: every walker in the corridor was drawn as
	# their own reflection. Nothing caught it in six sessions because a
	# roughly symmetric body reads the same either way at corridor distance,
	# and no gate here asks a transform whether it is a rotation.
	#
	# `ragdoll.gd::promote` is what found it, on the first real promotion, by
	# refusing a determinant of -1.0000 -- a check written for a bug the GATE
	# had hit and which turned out to be sitting in the shipped crowd. The
	# baked half of the crowd never had it: `populace._place_body` places a
	# body with a plain yaw, which is always right-handed. So the two halves of
	# one crowd disagreed about which way round a person is.
	#
	# `player.gd` and `dialogue.gd` use the same `fwd.cross(up)` and are BOTH
	# CORRECT, which is why this is a one-line sign and not a sweep: they pass
	# `Basis(right, up, -fwd)`, and the two negations cancel to +1. Only this
	# file's figures face +Z -- `body.py`'s do, `ragdoll.gd` agrees -- so only
	# this file needed the other sign.
	fwd = _turned(fwd, up, w.notice_yaw)
	var right := up.cross(fwd).normalized()
	return Transform3D(Basis(right, up, fwd),
		Vector3(w.radius * ca, w.radius * sa, w.z))


## `fwd` rotated about `up` by `yaw`, staying in the plane perpendicular to up.
##
## A ROTATION ABOUT THE BODY'S OWN UP CANNOT CHANGE THE HANDEDNESS, which is
## the property that matters here: `_walker_xform` builds `Basis(up.cross(fwd),
## up, fwd)` and that is right-handed only while the three stay orthonormal. So
## the turn is applied to `fwd` BEFORE `right` is derived from it, never to the
## finished basis -- rotating a basis that has already been assembled is how a
## determinant drifts. Session 4q's mirrored crowd is the reason that sentence
## is here rather than assumed.
static func _turned(fwd: Vector3, up: Vector3, yaw: float) -> Vector3:
	if absf(yaw) < 1e-6:
		return fwd
	return fwd.rotated(up.normalized(), yaw).normalized()


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
		# AWAY IS A REAL STATE AND IT COSTS NOTHING. An occupant whose timetable
		# has them somewhere else is in no bucket at all -- not a hidden mesh, not
		# a zero-scale transform, not there. That is the difference between a
		# room that empties and a room whose people are invisible.
		if w.hidden:
			continue
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


# ===========================================================================
#  ROOM OCCUPANTS -- and they were the wrong KIND of object
# ===========================================================================
# THE OWNER'S WORDS, and they name the defect exactly: "these need to be real
# people and we've come this far and we have fucking humanoid dioramas in
# rooms?"
#
# Everything in `collect()` above binds a person to the meshes they were BAKED
# as, and the whole runtime behaviour of such a person was `_physics_process`
# turning their yaw to face the player within 6 m. They never stood, never
# walked, never left, never slept -- `life.gd` says so in as many words, "a
# baked actor can only be shown or hidden", and it is not a limitation of that
# file: **a static mesh has no other option**, which is this file's own header
# sentence about LOD applied to behaviour.
#
# THE TRADE WAS MADE FOR THE CORRIDOR AND NOT FOR THE ROOMS, and it was
# backwards. `populace.py` records the reasoning -- an instanced walker wears
# their species' NOMINAL body rather than their own, "which room occupants do
# not pay". At two metres a player judges BEHAVIOUR, not bone structure. A
# unique face that never stands up reads worse than a shared face that gets up
# and leaves. Distance wants silhouette; proximity wants behaviour.
#
# WHAT AN OCCUPANT COSTS, measured rather than argued: nothing in the deck .glb
# (their body is in `crowd_lod*.glb`, shared) against 5.04 primitives and ~3,760
# triangles each baked; `populace.py --rooms` reports 249,728 triangles and 886
# primitives given back over eight rooms. What it BUYS is the timetable below.
#
# AND IT IS PURE IN THE HOUR. `set_hour(h)` computes state and position from `h`
# alone -- no previous position anywhere -- so a player who leaves a deck and
# comes back finds the room the clock says it should be, not the room plus
# however long they were gone times whatever the framerate was. That is
# `life.gd`'s Director property, and this is the same property for the people
# that Director could only ever show and hide.

## Every occupant's state at the hour last applied, for the verdict.
var _occ_states := {}
var _occ_moved := 0
var _occ_hour: float = -1.0
var _occ_said := false
## How many state changes get a line of their own before the log stops being
## readable. A whole station-day at 2 hours a second is hundreds; the first
## few are the evidence and the counter carries the rest.
const OCC_LOG_MAX := 24
var _occ_log := 0
## Ground the occupants have covered between them, in metres. THE SAME CLAIM
## `crowd_travel_m` makes for the corridor, asked of the people who could not
## make it at all: a room whose occupants change pose but never change place is
## still a diorama with more poses in it.
var _occ_travel_m: float = 0.0
var _occ_hour0: float = 0.0



## Admit room occupants from the cast list. Returns how many became instances.
##
## AN ACTOR ROW IS ENOUGH, and that is what makes this reachable without editing
## the generator's deck writer: `station/deck.py` forwards `species` and `lod`
## verbatim off an actor record and copies `who` whole, so the mesh key, the
## pose slot, the anchors and the timetable ride inside `who` and arrive intact.
##
## A ROW WITH BAKED MESHES IN THE SCENE IS **PROMOTED**, NOT DUPLICATED. Decks
## built before `populace.ROOM_INSTANCED` still carry their occupants' triangles;
## those meshes are hidden here and the instance drives instead, so a station
## that has not been rebuilt gets the behaviour today and gets the triangles back
## when it is. Without that this would be nine bodies drawn twice.
func add_occupants(rows: Array, tag: String = "", visual: Node = null) -> int:
	var before := _walkers.size()
	var promoted := 0
	var baked := {}
	if visual != null:
		for m in _meshes(visual):
			baked[String(m.name)] = m
	for r0 in rows:
		var r: Dictionary = r0
		var who: Dictionary = r.get("who", {})
		if not who.has("day"):
			continue                     # not an instanced occupant row
		var sp := String(r.get("species", who.get("species", "")))
		if sp == "":
			continue
		var w := Walker.new()
		w.tag = tag
		w.occupant = true
		w.species = sp
		w.lod = int(r.get("lod", 4))
		w.phase = int(who.get("slot", SLOT_IDLE))
		w.cycle_s = 1.0
		w.r_m = float(r.get("r_m", 0.0))
		w.h_m = float(r.get("h_m", 0.0))
		w.free = true
		w.anchor = Vector3(float(r.get("x", 0.0)), float(r.get("y", 0.0)),
			float(r.get("z", 0.0)))
		w.pos = w.anchor
		w.yaw0 = float(r.get("yaw", 0.0))
		w.day = who.get("day", [])
		w.talks = bool(who.get("talks", false))
		w.who_name = String(who.get("name", ""))
		w.place = String(r.get("place", ""))
		# THE ROOM'S OWN AXES, RECOVERED FROM WHERE THEY ARE STANDING. Every
		# offset in the row is room-local -- x across, z along -- because that is
		# the frame `deck.py::_place_local` maps: room x wraps onto the ring's
		# arc and room z stays the station axis. So "along" is world +Z and
		# "across" is the tangent at this body's own angle, which is a different
		# direction for every person on the ring and is why the offsets are
		# offsets rather than points.
		var radial := Vector3(w.anchor.x, w.anchor.y, 0.0)
		w.up_a = (-radial.normalized() if radial.length() > 0.001
			else Vector3.UP)
		w.axis = Vector3(0, 0, 1)
		w.tang = w.axis.cross(w.up_a).normalized()
		var seat = who.get("seat")
		if seat is Array and (seat as Array).size() == 2:
			w.has_seat = true
			# ALONG THEIR OWN UP, WHICH IS INWARD ON A SPUN RING. The shared sit
			# pose is built on the species' fitted seat and the room's seats are
			# 87-153 mm off it; `seat_dy` is that difference, computed where
			# `animation.seat_height` lives, and adding it here puts the hips
			# back on the pan. Zero unless the real seat is HIGHER -- see the
			# note in `populace._give_lives` for why it is one-sided.
			w.seat_off = (w.tang * float(seat[0]) + w.axis * float(seat[1])
				+ w.up_a * float(who.get("seat_dy", 0.0)))
		var bunk = who.get("bunk")
		if bunk is Array and (bunk as Array).size() == 2:
			w.has_bunk = true
			w.bunk_off = w.tang * float(bunk[0]) + w.axis * float(bunk[1])
		var ex = who.get("exit")
		if ex is Array and (ex as Array).size() == 2:
			w.exit_off = w.tang * float(ex[0]) + w.axis * float(ex[1])
		# Their heading at rest, in the same convention `_yaw_towards` uses:
		# yaw 0 faces the station axis.
		w.fwd_free = (w.axis * cos(w.yaw0) + w.tang * sin(w.yaw0)).normalized()
		_walkers.append(w)
		var g := String(r.get("group", ""))
		if g != "":
			for n in baked.keys():
				if n == g or String(n).begins_with(g + "_"):
					(baked[n] as Node3D).visible = false
					promoted += 1
	if _solid_mode != "off":
		for i in range(before, _walkers.size()):
			_give_walker_body(_walkers[i])
	var added := _walkers.size() - before
	if added > 0:
		if promoted > 0:
			print("npc: %d occupant(s) instanced, %d baked mesh(es) hidden "
				% [added, promoted]
				+ "-- a deck built before populace.ROOM_INSTANCED still ships "
				+ "their triangles; the instance drives them")
		# NO HOUR IS INVENTED HERE. `walk.gd` wires the first cell before
		# `main.gd` has built the Director, so a written-down 13.00 was used and
		# then corrected to 03.00 on the next frame -- four state changes that
		# never happened, in the one number in the verdict a diorama cannot
		# produce. Without a clock they keep the pose slot the generator baked
		# and `advance_crowd` states them the moment there is an hour to state
		# them at.
		var h0 := _occ_hour
		if h0 < 0.0:
			var ck0 := _find_clock()
			h0 = (float(ck0.call("hour")) if ck0 != null else -1.0)
		if h0 >= 0.0:
			set_hour(h0)
		else:
			_place_crowd()
	return added


## What one timetable says at an hour. PURE, and deliberately the same
## arithmetic as `populace._state_at`, so the gate and the runtime cannot
## disagree about what somebody is doing.
static func state_at(day: Array, hour: float) -> String:
	if day.is_empty():
		return "idle"
	var h := fposmod(hour, 24.0)
	var st := String((day[day.size() - 1] as Array)[1])
	for e in day:
		if float((e as Array)[0]) <= h:
			st = String((e as Array)[1])
		else:
			break
	return st


## The window `hour` falls in: [start, end] in hours, wrapping at midnight.
static func window_at(day: Array, hour: float) -> Vector2:
	if day.size() < 2:
		return Vector2(0.0, 24.0)
	var h := fposmod(hour, 24.0)
	for i in range(day.size()):
		var a := float((day[i] as Array)[0])
		var b := float((day[(i + 1) % day.size()] as Array)[0])
		var span: float = fposmod(b - a, 24.0)
		if span <= 0.0:
			span = 24.0
		if fposmod(h - a, 24.0) < span:
			return Vector2(a, span)
	return Vector2(0.0, 24.0)


## PUT EVERY OCCUPANT WHERE THE CLOCK SAYS THEY ARE. Pure in `h`.
##
## The mapping from a state to a body is the only place a decision is made here,
## and each one is forced by what the room has rather than chosen:
##
##   away      not drawn, no collider in play. Most of a day, for most people.
##   sleep     the sleeping pose, on the bed the generator found them. Nobody
##             without a bunk is ever in this state -- `populace._give_lives`
##             rewrites it to `away`, because you go home to sleep.
##   eat/work  seated if they have a seat, standing at their post if not.
##   idle      talking if somebody was placed inside `friction`'s own widest
##             separation of them, standing otherwise.
##   transit   walking the room's reserved circulation lane, between their post
##             and the way out, at the fraction of the window that has elapsed.
func set_hour(h: float) -> int:
	_occ_hour = h
	var moved := 0
	_occ_states.clear()
	for w in _walkers:
		if not w.occupant:
			continue
		var st := state_at(w.day, h)
		_occ_states[st] = int(_occ_states.get(st, 0)) + 1
		if st != w.state:
			# THE LINE THAT PROVES IT, and it names the person. A count of
			# occupants is a count a diorama also produces; a named resident
			# whose state changes at an hour their own species rhythm and their
			# own shift decided is not.
			if w.state != "" and _occ_log < OCC_LOG_MAX:
				_occ_log += 1
				print("npc: %05.2f EMT  %s (%s) in %s: %s -> %s"
					% [fposmod(h, 24.0),
						(w.who_name if w.who_name != "" else "<unnamed>"),
						w.species, w.place, w.state, st])
			# THE FIRST ASSIGNMENT IS NOT A CHANGE. Counting it made a build that
			# admitted 394 people and then froze report `changes=394`, which is
			# the exact number a diorama would print.
			if w.state != "":
				w.changes += 1
				moved += 1
			w.state = st
		w.hidden = st == "away"
		if w.hidden:
			# The capsule goes with them. A person who is not in the room is not
			# something you can bump into, and leaving the collider behind is the
			# "invisible person standing in an empty corridor" this file's own
			# header records for streamed cells.
			if w.body != null and is_instance_valid(w.body):
				(w.body as Node3D).visible = false
				(w.body as CollisionObject3D).collision_layer = 0
			continue
		var at: Vector3 = w.anchor
		var face: Vector3 = w.fwd_free
		match st:
			"sleep":
				w.phase = SLOT_SLEEP
				at = w.anchor + w.bunk_off
			"eat", "work":
				if w.has_seat:
					w.phase = SLOT_SIT
					at = w.anchor + w.seat_off
				else:
					w.phase = SLOT_IDLE
			"transit":
				# THE ONLY STATE THAT MOVES, and it moves as a function of the
				# hour and nothing else. `window_at` gives the start and length
				# of this leg of their day; the body is that fraction of the way
				# along the lane. Out on the second half, back on the first --
				# `schedule.activity_at` emits TRANSIT both before a shift and
				# after it, so which way somebody is going is decided by what
				# they are about to be doing rather than by a coin.
				w.phase = int(floor(fposmod(h * 3600.0 / maxf(w.cycle_s, 0.1),
					float(WALK_PHASES)))) % WALK_PHASES
				var win := window_at(w.day, h)
				var f: float = clampf(fposmod(h - win.x, 24.0)
					/ maxf(win.y, 1e-4), 0.0, 1.0)
				var leaving := state_at(w.day, h + win.y + 0.01) == "away"
				var t: float = (f if leaving else 1.0 - f)
				at = w.anchor + w.exit_off * t
				if w.exit_off.length() > 0.01:
					face = w.exit_off.normalized() * (1.0 if leaving else -1.0)
			_:
				w.phase = SLOT_TALK if w.talks else SLOT_IDLE
		var step := w.pos.distance_to(at)
		if step < 50.0:
			# A jump bigger than a room is somebody arriving from `away`, not
			# somebody walking; counting it would let a station that teleports
			# everybody report the largest travel figure of all.
			w.moved_m += step
			_occ_travel_m += step
		w.pos = at
		w.fwd_free = face
		if w.body != null and is_instance_valid(w.body):
			(w.body as Node3D).visible = true
			_layer(w.body as CollisionObject3D)
			w.body.global_transform = _walker_body_xform(w)
	_occ_moved += moved
	if moved > 0:
		_place_crowd()
	return moved


## The station clock, followed rather than owned.
##
## `walk.gd` builds this node and has no clock; `main.gd` builds the Clock and
## hands it to `life.gd`'s Director. Both are load-bearing files this change does
## not own, and `scripts/dialogue.gd` already solved it the same way: the
## Director is a node in the tree with an `hour()` accessor, so one guarded
## search BY CAPABILITY finds it and a build without one keeps the hour it
## booted with -- which is the old behaviour exactly.
var _clock_node: Node = null
var _clock_looked := false
var _clock_tries := 0


## A NEGATIVE ANSWER IS NOT LATCHED, and latching one cost the whole feature on
## the shipped path: `walk.gd` wires the first cell inside `main.gd::_ready`,
## BEFORE `_start_clock` has built the Director, so the first search legitimately
## finds nothing -- and a one-shot `_looked = true` then meant the occupants
## never found the clock that appeared four lines later. `dialogue.gd` gets away
## with the one-shot because it is built after the Director; this node is not.
## Capped so a build with no Director does not walk the tree every frame.
const CLOCK_TRIES := 240


func _find_clock() -> Node:
	if _clock_node != null or _clock_looked:
		return _clock_node
	_clock_tries += 1
	if _clock_tries >= CLOCK_TRIES:
		_clock_looked = true
	var scene := get_tree().current_scene if get_tree() != null else null
	for root in [scene, get_parent()]:
		if root == null:
			continue
		var n := _search_clock(root, 0)
		if n != null:
			_clock_node = n
			print("npc: occupants following the station clock at %s"
				% _clock_node.get_path())
			return _clock_node
	if _clock_looked:
		print("npc: no station clock in the tree after %d frames -- occupants "
			% CLOCK_TRIES + "hold the pose the generator baked them in")
	return null


## BY CAPABILITY, AND `hour()` ALONE IS NOT ENOUGH OF ONE. `dialogue.gd` exposes
## an `hour()` too -- it FOLLOWS the clock and reports what it last heard, which
## is -1.0 until something tells it -- and a depth-first search found it before
## the Director on the shipped scene: `npc: occupants following the station clock
## at /root/Main/Walk/Dialogue`, and every occupant then held the hour they were
## admitted at for ever. The Director is the node that also `apply`s an hour;
## a node that only reports one is a follower like this one.
func _search_clock(node: Node, depth: int) -> Node:
	if depth > 4:
		return null
	if node.has_method("hour") and node.has_method("apply") and node != self:
		return node
	for c in node.get_children():
		var got := _search_clock(c, depth + 1)
		if got != null:
			return got
	return null


## How many occupants, in what states, and how many state changes have happened.
## THE ONLY THING THAT CAN TELL A LIVING ROOM FROM A DIORAMA: the count is the
## same either way and the CHANGES are not.
func occupant_report() -> String:
	var n := 0
	var shown := 0
	for w in _walkers:
		if w.occupant:
			n += 1
			if not w.hidden:
				shown += 1
	var parts := []
	var keys := _occ_states.keys()
	keys.sort()
	for k in keys:
		parts.append("%s:%d" % [k, _occ_states[k]])
	return ("occupants=%d present=%d changes=%d travel_m=%.1f draws=%d/%d "
		+ "h=%.2f [%s]") % [
		n, shown, _occ_moved, _occ_travel_m, crowd_draw_calls(),
		crowd_buckets(), _occ_hour, ", ".join(parts)]


func occupant_travel_m() -> float:
	return _occ_travel_m


## HOW MANY DRAW CALLS THE PEOPLE ACTUALLY COST, counted rather than reasoned
## about. A MultiMesh with `visible_instance_count == 0` submits nothing, so the
## number is the buckets that have somebody in them -- which is a function of how
## many (species, lod, slot) combinations are present and NOT of how many people
## there are. That is the whole argument for instancing and it is the only form
## of it a run can falsify: `schedule.NPC_BUDGET["max_draw_calls"]` is 32, and a
## baked crowd pays one draw call per material span per person.
func crowd_draw_calls() -> int:
	var n := 0
	for k in _mm.keys():
		for mmi in _mm[k]:
			if (mmi as MultiMeshInstance3D).multimesh.visible_instance_count > 0:
				n += 1
	return n


## Every MultiMesh allocated, drawing or not. The resident cost.
func crowd_buckets() -> int:
	var n := 0
	for k in _mm.keys():
		n += (_mm[k] as Array).size()
	return n


func occupant_count() -> int:
	var n := 0
	for w in _walkers:
		if w.occupant:
			n += 1
	return n


func occupant_changes() -> int:
	return _occ_moved


## Turn the instanced crowd toward the player, and let them turn back.
##
## THIS IS THE OTHER HALF OF `_physics_process`'s `_people` LOOP, for the people
## that loop cannot see. Same `notice_m`, same `turn_rate`, same shortest-way-round
## rule -- deliberately, because two crowds turning at two speeds is exactly the
## "two descriptions of one thing" this project keeps paying for.
##
## `w.pos` is only maintained for commuters, so a loop walker's position comes
## from `_walker_xform(w).origin` -- which is the same call `advance_crowd`
## already makes to choose their LOD, so this adds no new notion of where
## anybody is.
##
## AN OCCUPANT WHO IS `away` IS NOT THERE. They are in no bucket, draw nothing
## and collide with nothing, so turning them would be turning a person who is
## somewhere else -- and would count toward `noticed`, which is the number the
## walk gate asserts on.
func _notice_walkers(eye: Vector3, delta: float) -> void:
	var step: float = turn_rate * delta
	for w in _walkers:
		if w.hidden:
			continue
		var at := (w.pos if w.free or w.occupant else _walker_xform(w).origin)
		var d := eye.distance_to(at)
		# Same two-condition early-out the `_people` loop uses: far away AND
		# already back at rest. Distance alone would freeze somebody mid-turn
		# staring at where the player used to be.
		if d > notice_m and absf(w.notice_yaw) < 1e-4:
			continue
		var want := 0.0
		if d <= notice_m:
			w.noticed = true
			# The angle from where they FACE to where the player IS, measured
			# in the plane they stand in. `_walker_xform` with the turn zeroed
			# gives their rest facing; comparing against the live one would
			# make this frame's answer depend on last frame's turn.
			var was := w.notice_yaw
			w.notice_yaw = 0.0
			var rest := _walker_xform(w)
			w.notice_yaw = was
			var up := rest.basis.y.normalized()
			var to := eye - rest.origin
			to = to - up * to.dot(up)
			if to.length() > 0.01:
				var f := rest.basis.z.normalized()
				var r := up.cross(f).normalized()
				want = atan2(to.dot(r), to.dot(f))
		var diff: float = wrapf(want - w.notice_yaw, -PI, PI)
		w.notice_yaw = wrapf(w.notice_yaw + clampf(diff, -step, step), -PI, PI)


func advance_crowd(delta: float) -> void:
	# THE OCCUPANTS FIRST, AND THEY ARE NOT ADVANCED -- they are EVALUATED. A
	# clock that runs at 60x is exactly why: nothing here steps, so a station
	# minute a second and real time give the same room at the same hour.
	var ck := _find_clock()
	if ck != null:
		var h: float = float(ck.call("hour"))
		if h >= 0.0 and absf(h - _occ_hour) > 1e-4:
			var ch := set_hour(h)
			if ch > 0 and not _occ_said:
				_occ_said = true
				print("npc: %s" % occupant_report())
			if absf(h - _occ_hour0) >= 1.0 and occupant_count() > 0:
				_occ_hour0 = h
				print("npc: %s" % occupant_report())
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
	if _body != null:
		_notice_walkers(eye, delta)
	for w in _walkers:
		if w.occupant:
			# AN OCCUPANT'S PHASE IS A POSE, NOT A FRAME OF A WALK CYCLE, and
			# falling through this loop overwrote it every frame: `w.phase =
			# int(w.t / cycle_s * 8) % 8` drove SLOT_SLEEP back down into the
			# walk phases, so a sleeping Narn was redrawn as frame 3 of a stride
			# 60 times a second. Their RUNG still moves with the player, because
			# that is a property of where the camera is and not of what they are
			# doing.
			if _body != null and not w.hidden:
				w.lod = _lod_at(eye.distance_to(w.pos))
			continue
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


## THE CROWD IS NOT SAVED, AND THAT IS A DECISION WITH A COST.
## A walker's position along its corridor is a phase derived from the resident's
## id and the clock, so restoring the clock puts the crowd back where it was --
## the corridor looks right. What does NOT come back is anything a player did to
## an individual: a body they knocked over, a walker they were following. Those
## need a stable id for a crowd body across a reload, which is the same missing
## piece `dialogue.gd::load_state` names for resuming a conversation.
func save_exempt() -> String:
	return "walker phase is derived from the clock; per-body player effects are NOT kept"
