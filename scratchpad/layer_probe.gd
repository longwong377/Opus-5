extends SceneTree
# Does Godot's 3D collision test consider BOTH directions of layer/mask?
# `ragdoll.gd` puts bones on layer 16 with mask 1 (WORLD_LAYER); `walk.gd`
# leaves the player on Godot's defaults, layer 1 / mask 1. Under a
# unidirectional rule (the mover's mask alone) the player never sees a bone;
# under a bidirectional rule (either side names the other) it does. Settled in
# the engine rather than from memory.
#
# EVERY READING HERE HAS A CONTROL BESIDE IT. The first version of this probe
# reported "passed through" for both the subject and the control, because the
# nodes were built in _init before the tree had a physics space -- the sweep
# was answering with an error, not a miss. That is why the control is printed.

var _root: Node3D
var _p: CharacterBody3D
var _bone: StaticBody3D
var _done := false

func _initialize() -> void:
	_root = Node3D.new()
	get_root().add_child(_root)

	var floorb := StaticBody3D.new()
	var fs := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(40, 1, 40)
	fs.shape = box
	floorb.add_child(fs)
	floorb.position = Vector3(0, -0.5, 0)
	_root.add_child(floorb)

	_bone = StaticBody3D.new()
	_bone.name = "bone"
	var bs := CollisionShape3D.new()
	var bb := BoxShape3D.new()
	bb.size = Vector3(1.0, 1.0, 1.0)
	bs.shape = bb
	_bone.add_child(bs)
	_bone.position = Vector3(2.0, 0.5, 0)
	_bone.collision_layer = 16          # RAGDOLL_LAYER
	_bone.collision_mask = 1            # WORLD_LAYER
	_root.add_child(_bone)

	_p = CharacterBody3D.new()
	var ps := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.height = 1.8
	cap.radius = 0.35
	ps.shape = cap
	ps.position = Vector3(0, 0.9, 0)
	_p.add_child(ps)
	_root.add_child(_p)


func _sweep(label: String, p_layer: int, p_mask: int,
		b_layer: int, b_mask: int) -> void:
	_p.collision_layer = p_layer
	_p.collision_mask = p_mask
	_bone.collision_layer = b_layer
	_bone.collision_mask = b_mask
	_p.global_position = Vector3(0, 0, 0)
	var hit := _p.move_and_collide(Vector3(4.0, 0, 0))
	print("%-58s player L%-2d M%-2d  obstacle L%-2d M%-2d  ->  %s"
		% [label, p_layer, p_mask, b_layer, b_mask,
		("BLOCKED at x=%.3f" % _p.global_position.x) if hit != null
		else "PASSED THROUGH (moved to x=%.3f)" % _p.global_position.x])


func _physics_process(_d: float) -> bool:
	if _done:
		return true
	_done = true
	print("\nGodot %s -- 3D collision layer/mask semantics\n"
		% Engine.get_version_info()["string"])
	_sweep("POSITIVE CONTROL: both on layer 1, both masking 1", 1, 1, 1, 1)
	_sweep("NEGATIVE CONTROL: neither side names the other", 1, 1, 16, 0)
	_sweep("THE SHIPPED CASE: walk.gd default vs ragdoll.gd bone", 1, 1, 16, 1)
	_sweep("THE FIX: player masks RAGDOLL_LAYER too", 1, 1 | 16, 16, 1)
	_sweep("THE OTHER FIX: bone put on WORLD_LAYER", 1, 1, 1, 1)
	return true
