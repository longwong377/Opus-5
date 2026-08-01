extends RefCounted

## WHERE AM I. One answer, asked of the geometry, used by everybody.
##
## THE DEFECT THIS CLOSES. `hud.gd` and `ambience.gd` both answered "which room
## is the player in" and they disagreed by **31.6 m**: the HUD said
## `CORRIDOR (near CUSTOMS NORTH 31.6 m)` while the audio said
## `place=customs_north`. You were told you were in the corridor while hearing
## the room.
##
## They disagreed because they were answering from different evidence:
##
##   ambience  every `<place>__<group>` mesh in the scene, merged -- the room's
##             own geometry;
##   hud       the bounding box of the room's INTERACTABLES out of the sidecar,
##             padded by 1.5 m, with its own comment admitting "a place's extent
##             here is the extent of the things IN it and a room is bigger than
##             its furniture".
##
## A room's extent is a property of the room, not of the furniture somebody put
## in it. `deck.build_deck` prefixes every one of a room's groups with
## `<key>__`, so the geometry already carries the answer and there was never a
## reason to infer it. That is hard rule 4 -- one schema, no second description
## -- applied to a question two scripts were each guessing at.
##
## DELIBERATELY CONTAINMENT AND NOT NEAREST, which is `ambience.place_at`'s rule
## and the correct one: on a ring deck every room opens off one corridor, so
## "not inside any room" means "in the corridor", not "near whichever room
## happens to be closest". The nearest-room answer is what put the word
## CORRIDOR next to a room name 31.6 m away.

## How far past its own wall face a room's box reaches. A doorway is where a
## room begins for anyone walking through it, and a box that stops at the wall
## makes the change happen one step late. From `ambience.gd`, which had it
## right; it is stated once here instead of twice there.
const DOORWAY_GROW_M := 1.5


static func meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for c in node.get_children():
		out.append_array(meshes(c))
	return out


## `{place_key: AABB}` in world space, from the scene's own mesh names.
static func boxes(visual: Node) -> Dictionary:
	var out := {}
	for m in meshes(visual):
		var n := String(m.name)
		var cut := n.find("__")
		if cut <= 0:
			continue
		var key := n.substr(0, cut)
		var box: AABB = m.global_transform * m.get_aabb()
		out[key] = (out[key] as AABB).merge(box) if out.has(key) else box
	for k in out.keys():
		out[k] = (out[k] as AABB).grow(DOORWAY_GROW_M)
	return out


## Which place contains this point, or "" for none.
##
## Smallest containing box wins: a bay inside a bay row is the room you are
## actually standing in.
static func at(boxes_: Dictionary, p: Vector3) -> String:
	var best := ""
	var best_v := INF
	for k in boxes_.keys():
		var box: AABB = boxes_[k]
		if not box.has_point(p):
			continue
		var v: float = box.size.x * box.size.y * box.size.z
		if v < best_v:
			best_v = v
			best = String(k)
	return best


## The nearest place and its distance, for a point inside none of them.
## Reported ALONGSIDE the containment answer, never instead of it.
static func nearest(boxes_: Dictionary, p: Vector3) -> Array:
	var name := ""
	var best := INF
	for k in boxes_.keys():
		var box: AABB = boxes_[k]
		var lo: Vector3 = box.position
		var hi: Vector3 = box.position + box.size
		var q := Vector3(clampf(p.x, lo.x, hi.x), clampf(p.y, lo.y, hi.y),
			clampf(p.z, lo.z, hi.z))
		var d := p.distance_to(q)
		if d < best:
			best = d
			name = String(k)
	return [name, best if best < INF else 0.0]
