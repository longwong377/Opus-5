extends Node3D
## A body that has stopped standing up.
##
## THE OWNER ASKED FOR REAL RAGDOLLS AND THEN SAID WHAT THEY ARE FOR: *"if
## anyone dies, falls ill, or is shot, for example by a criminal or by law
## enforcement, and also maybe for fighting"*. Every one of those already
## happens here. `station/incident.py` runs **INC-SICK 380 times a day** -- its
## own text is "collapse -> the crowd opens -> the card is read -> a bed, an
## arm, or nothing" -- plus a dock accident every ~6 days, a fatality every
## ~500 of those, and INC-PICK / INC-CONTRA / INC-BRAWL feeding
## `consequence.py`'s arrest chain. So nothing here invents an event. This is
## the visible half of one the station has been having in text.
##
## WHY PROMOTION AND NOT "MAKE THE CROWD RAGDOLLS". `npc.gd` puts the whole
## station's crowd through MultiMesh -- "the station's entire crowd is 112 draw
## calls" -- and a MultiMesh instance is a transform into a shared mesh. **It
## cannot own a skeleton.** There is no version of this feature where the
## instanced crowd ragdolls. So the crowd stays instanced and exactly the
## bodies that need physics are HIDDEN from their bucket and rebuilt here as a
## skinned mesh with a `Skeleton3D`, a `PhysicalBoneSimulator3D` and sixteen
## `PhysicalBone3D`s, for as long as they need one.
##
## AND THE PROMOTED BODY IS THE GOOD ONE. It is not a compromise to fall back
## to: the body that ragdolls is by definition the one being looked at, so it
## is rebuilt at **lod 0 -- 7,212 triangles on a human** -- against the
## 484-triangle shared body the crowd draws. INV-403 already costed exactly
## this trade for room occupants.
##
## WHAT COMES FROM PYTHON AND WHAT IS DECIDED HERE. Everything about the body
## is `station/npc/ragdoll.py`'s: the skeleton (measured off the mesh by
## `animation._skeleton`), the skin weights, the segment masses (the mesh's own
## volume x a density solved from the gazetteer's 75 kg person), the shapes,
## the joint limits and the settle threshold. This file decides only WHEN and
## WHERE -- and applies the two things only the runtime knows: which way is
## down and how hard.
##
## GRAVITY IS NOT -Y AND IT IS NOT 9.81. This station spins. "Down" is radially
## OUTWARD from the axis and the magnitude runs 0.234 g on Yellow's innermost
## addressed deck to 1.693 g deep in Grey (`populace.place_gravity_at`). Every
## promotion is told its own `up` and its own `g`, and the fall is integrated
## against those -- see `_apply_gravity`. A ragdoll that fell at 9.81 m/s^2
## straight down would be visibly wrong on two thirds of this station.

const RAGDOLL_LAYER := 16          ## world is 1, interact proxies 2, people 4
const WORLD_LAYER := 1

## Where `station/npc/ragdoll.py --emit` wrote the bodies.
@export var data_dir: String = ""
## Hard cap on simultaneous promotions. **Derived, not preferred**: read out of
## the loaded species doc, which gets it from `schedule.NPC_BUDGET["lod"][0]` --
## the lod0 rung is `(0 m, 6 m, 8,000 triangles, 4 instances)`, and a promoted
## body is one lod0 instance. Overridable for the gate's controls only.
@export var max_concurrent: int = 0
## Whether promotion happens at all. `--no-ragdoll` is the negative control:
## the incident still fires, the person still stops being where they were, and
## nothing is visible. That is the build before this file existed.
@export var enabled: bool = true
## THE STATION'S OWN SPIN, omega^2 in rad^2/s^2, so a promotion that does not
## state its own gravity gets the RIGHT one instead of Earth's.
##
## `doll.g` used to default to 9.81 and `doll.up` to +Y, and every caller was
## expected to work both out. The gate did, because the gate is where they were
## written; `npc.gd::promote_walker` did not, and a body promoted out of the
## crowd would have fallen at 9.81 m/s^2 straight down on a station whose deck
## delivers 7.454 m/s^2 along a radius -- visibly wrong on two thirds of it.
##
## That is the shape this project keeps repeating: a fix applied to the instance
## the author was looking at rather than to the rule. So the derivation lives
## HERE, once, and every promotion that omits `g`/`up` gets it from its own
## world position. `main.gd::_spin_omega2` reads omega^2 off `cell_manifest`'s
## deck table -- g = omega^2 r on a rigid rotor, exact at every radius including
## the ones with no deck on them.
@export var omega2: float = 0.0

var _docs: Dictionary = {}          ## species -> the parsed json
var _live: Array = []               ## Doll
var _donor: Node = null             ## where materials are borrowed from
var _mat_cache: Dictionary = {}
var _player_rid: RID
var _promoted := 0
var _refused := 0
var _settled := 0
var _why_refused := ""
var _mat_fallbacks := 0


## One promoted body, and everything measured about it while it falls.
class Doll:
	var species: String
	var who: String = ""
	var cause: String = ""
	var scale: float = 1.0
	var root: Node3D
	var skel: Skeleton3D
	var sim: PhysicalBoneSimulator3D
	var mesh: MeshInstance3D
	var bones: Array = []             ## PhysicalBone3D, segment order
	var seg: Array = []               ## the json rows, same order
	var anchor_child: Array = []      ## joint point in the child's own frame
	var anchor_parent: Array = []     ## the same point in the parent's frame
	var parent_of: Array = []         ## index into `bones`, or -1
	var up: Vector3 = Vector3.UP
	var g: float = 9.81
	var settle_v: float = 0.06
	var quiet_frames: int = 0
	var trail: Array = []               ## bone positions, one row per tick
	var trail_at: int = 0
	var settle_frames_needed: int = 20
	var t: float = 0.0
	var settle_t: float = -1.0
	var timeout_s: float = 8.0
	var peak_speed: float = 0.0
	var worst_joint_m: float = 0.0
	var deepest_pen_m: float = 0.0      ## worst at ANY instant, impacts included
	var rest_pen_m: float = 0.0         ## what is left once it has stopped
	var knee_lo: float = 1e9            ## the knee hinge's range over the fall,
	var knee_hi: float = -1e9            ## in the SOLVER's own sign convention
	var v_cap: float = 1e9              ## see `_clamp` -- the physical ceiling
	var com0: Vector3 = Vector3.ZERO    ## the centre of mass at promotion
	var fall_m: float = 0.0             ## how far it has come DOWN since
	var clamped: int = 0                ## how often the solver had to be held
	var knee_limit: Vector2 = Vector2.ZERO   ## what the data DECLARED for it
	var restore: Callable = Callable()
	var dead: bool = true             ## a death stays down; illness gets up
	var done: bool = false


func _ready() -> void:
	var a := _args()
	if a.has("no-ragdoll"):
		enabled = false
		print("ragdoll: DISABLED (negative control) -- an incident still fires "
			+ "and nothing is visible, which is the build before session 4p")
	if data_dir == "":
		data_dir = _root().path_join("station/generated/scene/npc")


# ===========================================================================
#  PROMOTION
# ===========================================================================
## Turn one instanced body into a physical one.
##
## `spec` carries what only the caller knows:
##   species      : String, the key in `body.SPECIES`
##   xform        : Transform3D, where the body is standing NOW -- the same
##                  transform `npc.gd::_walker_xform` writes into the MultiMesh
##   up           : Vector3, this deck's own up (radially INWARD on a ring)
##   g            : float, m/s^2, from `populace.place_gravity_at`
##   h_m          : float, this individual's measured stature -- the actor and
##                  walker records already carry it, from `populace.body_capsule`
##   velocity     : Vector3, what they were doing when it happened
##   impulse      : Vector3, applied at `impulse_bone` (a shot, a shove)
##   cause        : String, the incident class -- INC-SICK, INC-BRAWL, ...
##   dead         : bool, whether they get back up
##   restore      : Callable, called on demotion to put the instance back
##
## Returns the Doll, or null if it was refused -- and a refusal is reported
## rather than silent, because a cap that is being hit constantly is a budget
## that is wrong.
func promote(spec: Dictionary) -> Doll:
	if not enabled:
		_refused += 1
		_why_refused = "disabled"
		return null
	var species := String(spec.get("species", "human"))
	var d := _doc(species)
	if d.is_empty():
		_refused += 1
		_why_refused = "no body data for " + species
		push_warning("ragdoll: no %s_ragdoll.json in %s" % [species, data_dir])
		return null
	var cap: int = max_concurrent if max_concurrent > 0 else int(
		((d["ragdoll"] as Dictionary).get("concurrent_cap", {}) as Dictionary
		).get("cap", 4))
	if _live.size() >= cap:
		_refused += 1
		_why_refused = "cap %d reached" % cap
		return null

	# A MIRRORED TRANSFORM IS NOT A PLACE TO STAND, and this check exists
	# because it happened. The gate built its drop basis as
	# `Basis(along.cross(up), up, along)`, which for a ring corridor is
	# LEFT-handed -- x cross y came out as -z -- and a reflection handed to the
	# solver inverts every shape and every joint frame it contains. What it
	# looked like was not "the transform is wrong": it looked like a ragdoll
	# bug. One body fell through the deck at terminal velocity with its joints
	# perfectly rigid, and two exploded to 12 m of joint separation. Determinant
	# rather than "does it look orthonormal", because that is the property that
	# was violated and it is one line.
	var xf: Transform3D = spec.get("xform", Transform3D.IDENTITY)
	var det := xf.basis.determinant()
	if det < 0.001:
		_refused += 1
		_why_refused = "the promotion transform has determinant %.4f" % det
		push_error(("ragdoll: refusing to promote into a transform with "
			+ "determinant %.4f -- a mirrored or degenerate basis inverts "
			+ "every shape in the body") % det)
		return null

	var doll := Doll.new()
	doll.species = species
	doll.who = String(spec.get("who", ""))
	doll.cause = String(spec.get("cause", "?"))
	doll.dead = bool(spec.get("dead", true))
	# DERIVED FROM WHERE THE BODY IS, unless the caller states otherwise. Up is
	# INWARD on a spun ring -- the floor is the outer wall -- and the axis is
	# +Z, so the radial is (x, y, 0). A caller that knows better (the gate, and
	# its `--zero-g` control) still wins; a caller that says nothing no longer
	# gets Earth.
	var drop_at: Vector3 = xf.origin
	var radial := Vector3(drop_at.x, drop_at.y, 0.0)
	var r := radial.length()
	if spec.has("up"):
		doll.up = (spec["up"] as Vector3).normalized()
	elif r > 0.001:
		doll.up = -radial / r
	else:
		doll.up = Vector3.UP
	if spec.has("g"):
		doll.g = float(spec["g"])
	elif omega2 > 0.0 and r > 0.001:
		doll.g = omega2 * r
	else:
		# NOT 9.81. A build whose spin is unknown says so, because a body that
		# falls at exactly Earth gravity on a rotating station is a number
		# somebody will read as measured.
		doll.g = 0.0
		push_warning("ragdoll: no omega2 and no stated g at r=%.1f m -- the "
			% r + "body will not fall. Set `omega2` on the director.")
	doll.restore = spec.get("restore", Callable())

	var rag: Dictionary = d["ragdoll"]
	# THE INDIVIDUAL, NOT THE SPECIES MEAN. The shared skinned body is built
	# from `body.nominal(species)`; the person being promoted has their own
	# stature, and both ends of the ratio are MEASURED -- `h_m` off that
	# individual's mesh by `populace.body_capsule`, the reference off the
	# skinned mesh's own bounding height. Lengths scale, masses cube.
	var ref_h := float(rag.get("reference_height_m", 1.75))
	var h := float(spec.get("h_m", 0.0))
	doll.scale = (h / ref_h) if (h > 0.05 and ref_h > 0.05) else 1.0

	doll.root = Node3D.new()
	doll.root.name = "ragdoll_%s_%d" % [species, _promoted]
	add_child(doll.root)
	doll.root.global_transform = spec.get("xform", Transform3D.IDENTITY)

	_build_skeleton(doll, d)
	_build_mesh(doll, d)
	_build_bodies(doll, d)

	for sg in (rag["segments"] as Array):
		if String(sg["bone"]) == "knee_r":
			doll.knee_limit = Vector2(float(sg["joint"]["lower_deg"]),
				float(sg["joint"]["upper_deg"]))
	# THE PHYSICAL CEILING ON A BONE'S SPEED, and it is derived rather than
	# picked. Under `linear_damp` in REPLACE mode a falling body's terminal
	# speed is exactly g / damp -- 12.4 m/s at this deck's 0.76 g -- and
	# whatever was injected at promotion adds to it. Anything faster than twice
	# that did not come from gravity or from the incident: it came out of the
	# solver, which is what a ragdoll explosion IS.
	#
	# **The clamp is COUNTED and reported.** A stabiliser that fires constantly
	# is a defect being hidden, and the difference between "it never fires" and
	# "it fires every frame" is the difference between a safety net and a lie.
	var v_inj: float = (spec.get("velocity", Vector3.ZERO) as Vector3).length()
	var imp2: Vector3 = spec.get("impulse", Vector3.ZERO)
	doll.v_cap = 2.0 * (doll.g / maxf(0.05, float(
		(rag["damping"] as Dictionary)["linear"]))) + v_inj \
		+ imp2.length() / maxf(1.0, float(rag["mass_kg"]) * 0.1)

	# WITH NO GRAVITY THERE IS NO TERMINAL SPEED, so there is nothing to clamp
	# against. The `--zero-g` control drove `v_cap` to exactly 0 and the clamp
	# then pinned every bone to a standstill 640 times -- a stabiliser that had
	# become the thing being tested.
	if doll.g <= 0.0:
		doll.v_cap = 1e9

	doll.settle_v = float((rag["settle"] as Dictionary)["speed_m_s"])
	doll.settle_frames_needed = int((rag["settle"] as Dictionary)["frames"])
	doll.timeout_s = float((rag["settle"] as Dictionary)["timeout_s"])

	doll.sim.physical_bones_start_simulation()
	doll.com0 = _com(doll)
	# INHERIT WHAT THEY WERE DOING. A walker collapses at 1.4 m/s and a body
	# that starts from rest slides out from under its own momentum.
	var v0: Vector3 = spec.get("velocity", Vector3.ZERO)
	if v0.length_squared() > 1e-9:
		for pb in doll.bones:
			(pb as PhysicalBone3D).linear_velocity = v0
	var imp: Vector3 = spec.get("impulse", Vector3.ZERO)
	if imp.length_squared() > 1e-9:
		var at := int(spec.get("impulse_bone", 2))    # chest by default
		if not doll.bones.is_empty():
			var pb2: PhysicalBone3D = doll.bones[
				clampi(at, 0, doll.bones.size() - 1)]
			pb2.apply_central_impulse(imp)

	# A BODY ON THE DECK MUST NOT COST THE PLAYER THEIR FLOOR. `npc.gd` records
	# the whole diagnosis: a `CharacterBody3D` re-attaches to a floor it has
	# drifted off with a downcast that has `recovery_as_collision` set, so
	# **while the capsule is touching anything the snap is refused** -- and the
	# crowd's colliders had to come off the player's mask entirely. A ragdoll
	# is the same hazard with sixteen colliders instead of one, so the player
	# is an explicit exception on every bone. `--ragdoll-solid` removes it,
	# which is the control, and it must reproduce that failure.
	#
	# THERE WERE TWO LOCKS ON THAT DOOR AND THIS FLAG ONLY EVER OPENED ONE OF
	# THEM, which made it a control that could not fail. Measured in session 4q,
	# four runs of `--corpse-gate` on one build:
	#
	#   (subject)                            PASS  clearance_min -0.0000  offfloor 0/150
	#   --ragdoll-solid                      PASS  clearance_min -0.0000  offfloor 0/150
	#   --no-ragdoll-push                    FAIL  clearance_min -0.4200  offfloor 0/150
	#   --no-ragdoll-push --ragdoll-solid    FAIL  clearance_min -0.4822  offfloor 0/150
	#
	# `--ragdoll-solid` is IDENTICAL to the subject in every statistic the gate
	# reports. The second lock is the layer/mask pair: bones sit on
	# `RAGDOLL_LAYER` and `walk.gd::_spawn_player` never set the player's
	# `collision_mask`, so it was Godot's default 1 -- and Godot 4.4's
	# `move_and_collide` consults THE MOVER'S MASK ONLY. Probed in the engine
	# rather than remembered, with both controls firing (see
	# `scratchpad/layer_probe.gd`):
	#
	#   player L1 M1   obstacle L1  M1   ->  BLOCKED          (positive control)
	#   player L1 M1   obstacle L16 M0   ->  PASSED THROUGH   (negative control)
	#   player L1 M1   obstacle L16 M1   ->  PASSED THROUGH   (the shipped case)
	#   player L1 M17  obstacle L16 M1   ->  BLOCKED          (the fix)
	#
	# So the exception was removing a collision the mask had already removed.
	# `player_extra_mask()` below is the other half; `walk.gd` asks for it.
	#
	# WHY THE MASK AND NOT THE BONE'S LAYER. Putting bones on `WORLD_LAYER`
	# under the flag would also make them solid to the player -- and would make
	# them solid TO EACH OTHER, because their own mask is `WORLD_LAYER`. This
	# file measured that case at "peak 500 m/s and 13.1 m of joint separation";
	# the control would then reproduce a ragdoll explosion as well as the floor
	# hazard, and a control that changes two things measures neither.
	if _player_rid.is_valid() and not _args().has("ragdoll-solid"):
		doll.sim.physical_bones_add_collision_exception(_player_rid)

	if doll.bones.is_empty():
		# A BODY WITH NO SEGMENTS IS NOT A BODY, and the first engine run of
		# this file reported three of them SETTLING IN 0.33 s. Everything
		# downstream reads an empty array as "nothing is moving", so the
		# absence of a build is indistinguishable from a perfect one unless
		# something says so here.
		_refused += 1
		_why_refused = "the physical build produced no segments"
		push_error("ragdoll: %s built 0 segments -- refusing to promote"
			% species)
		doll.root.queue_free()
		return null
	_live.append(doll)
	_promoted += 1
	print(("ragdoll: PROMOTED %s%s -- %s, %d segments, %.1f kg, %s, "
		+ "g=%.2f m/s2 up=%.2f,%.2f,%.2f, scale=%.3f")
		% [species, ("" if doll.who == "" else " (" + doll.who + ")"),
		doll.cause, doll.bones.size(),
		float(rag["mass_kg"]) * pow(doll.scale, 3.0),
		("dead" if doll.dead else "down"), doll.g,
		doll.up.x, doll.up.y, doll.up.z, doll.scale])
	return doll


## Put the body back: the instance reappears standing and the physics goes
## away. An illness or a knockdown ends here; a death does not.
func demote(doll: Doll) -> void:
	if doll == null or doll.done:
		return
	doll.done = true
	if doll.sim != null and doll.sim.is_simulating_physics():
		doll.sim.physical_bones_stop_simulation()
	if doll.restore.is_valid():
		doll.restore.call()
	_live.erase(doll)
	if is_instance_valid(doll.root):
		doll.root.queue_free()
	print("ragdoll: DEMOTED %s -- %s, back on their feet after %.2f s"
		% [doll.species, doll.cause, doll.t])


# ===========================================================================
#  BUILDING ONE
# ===========================================================================
func _build_skeleton(doll: Doll, d: Dictionary) -> void:
	var sk := Skeleton3D.new()
	sk.name = "Skeleton3D"
	# PHYSICS, NOT IDLE. Godot 4.4 runs `SkeletonModifier3D`s during the
	# skeleton's update pass and RESTORES the unmodified poses afterwards, so
	# the simulator's output is only ever visible to the skin -- which is why
	# `get_bone_global_pose()` read from outside still says "standing". The
	# callback mode decides whether that pass is in step with the solver.
	sk.modifier_callback_mode_process = \
		Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_PHYSICS
	doll.root.add_child(sk)
	doll.skel = sk
	var bones: Array = d["bones"]
	for b in bones:
		sk.add_bone(String(b["name"]))
	for i in range(bones.size()):
		var p := int(bones[i]["parent"])
		if p >= 0:
			sk.set_bone_parent(i, p)
	for i in range(bones.size()):
		var head := _v3(bones[i]["rest_head"]) * doll.scale
		var p := int(bones[i]["parent"])
		var local: Vector3 = head - (_v3(bones[p]["rest_head"]) * doll.scale
			if p >= 0 else Vector3.ZERO)
		# REST ROTATIONS ARE THE IDENTITY, and that is not an assumption --
		# `animation.godot_note()` states it: "a bone's rest transform is a
		# pure translation to its head". It is what makes the skinned mesh in
		# the rest pose exactly the built mesh, which `body.skin_selftest`
		# checks vertex for vertex.
		sk.set_bone_rest(i, Transform3D(Basis(), local))
	sk.reset_bone_poses()


func _build_mesh(doll: Doll, d: Dictionary) -> void:
	var am := ArrayMesh.new()
	var mats: Array = []
	for s in (d["surfaces"] as Array):
		var pos := PackedVector3Array()
		var nrm := PackedVector3Array()
		var bon := PackedInt32Array()
		var wgt := PackedFloat32Array()
		var idx := PackedInt32Array()
		var p: Array = s["positions"]
		var n: Array = s["normals"]
		for i in range(0, p.size(), 3):
			pos.append(Vector3(p[i], p[i + 1], p[i + 2]) * doll.scale)
			nrm.append(Vector3(n[i], n[i + 1], n[i + 2]))
		for b in (s["bones"] as Array):
			bon.append(int(b))
		for w in (s["weights"] as Array):
			wgt.append(float(w))
		for i in (s["indices"] as Array):
			idx.append(int(i))
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = pos
		arr[Mesh.ARRAY_NORMAL] = nrm
		arr[Mesh.ARRAY_BONES] = bon
		arr[Mesh.ARRAY_WEIGHTS] = wgt
		arr[Mesh.ARRAY_INDEX] = idx
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		am.surface_set_name(am.get_surface_count() - 1, String(s["group"]))
		mats.append(_material_for(String(s["group"])))
	var mi := MeshInstance3D.new()
	mi.name = "skin"
	mi.mesh = am
	doll.skel.add_child(mi)
	for i in range(mats.size()):
		if mats[i] != null:
			mi.set_surface_override_material(i, mats[i])
	# The skin is expressed in the skeleton's rest space, so the bind poses are
	# exactly the inverse rest globals -- which is what this builds.
	mi.skeleton = mi.get_path_to(doll.skel)
	mi.skin = doll.skel.create_skin_from_rest_transforms()
	doll.mesh = mi


func _build_bodies(doll: Doll, d: Dictionary) -> void:
	var sim := PhysicalBoneSimulator3D.new()
	sim.name = "sim"
	doll.skel.add_child(sim)
	doll.sim = sim
	var segs: Array = (d["ragdoll"] as Dictionary)["segments"]
	var by_name := {}
	for i in range(segs.size()):
		by_name[String(segs[i]["bone"])] = i
	var s3 := doll.scale
	for si in range(segs.size()):
		var seg: Dictionary = segs[si]
		var pb := PhysicalBone3D.new()
		pb.name = "pb_" + String(seg["bone"])
		pb.bone_name = String(seg["bone"])
		# MASS CUBES WITH THE SCALE, because it is a volume. Length scales,
		# area squares, mass cubes -- getting this wrong makes a tall person
		# light and a short one leaden, which reads as the wrong material
		# rather than the wrong size.
		pb.mass = maxf(0.02, float(seg["mass_kg"]) * pow(s3, 3.0))
		pb.friction = float((d["ragdoll"]["damping"] as Dictionary)["friction"])
		pb.bounce = float((d["ragdoll"]["damping"] as Dictionary)["bounce"])
		pb.linear_damp_mode = PhysicalBone3D.DAMP_MODE_REPLACE
		pb.angular_damp_mode = PhysicalBone3D.DAMP_MODE_REPLACE
		pb.linear_damp = float((d["ragdoll"]["damping"] as Dictionary)["linear"])
		pb.angular_damp = float((d["ragdoll"]["damping"] as Dictionary)["angular"])
		# GRAVITY IS APPLIED BY HAND, so `gravity_scale` is zero. See
		# `_apply_gravity`: the project's own gravity points -Y at 9.8 and this
		# station's points at its axis at anything from 0.23 to 1.69 g.
		pb.gravity_scale = 0.0
		pb.collision_layer = RAGDOLL_LAYER
		# WORLD ONLY, AND NOT THE OTHER BONES. A ragdoll's segments overlap at
		# rest BY CONSTRUCTION here: the shapes are solved from the mesh's own
		# volume, so a chest box and a thigh capsule share the volume the skin
		# blends between them, and a solver handed two boxes already inside
		# each other answers with a separation impulse. Measured, with
		# self-collision on: **peak 500 m/s and 13.1 m of joint separation**
		# within eight seconds -- the classic ragdoll explosion, and the shapes
		# were the cause rather than the joints.
		#
		# What holds the limbs apart instead is the joint limits, which is what
		# they are for. WHAT IS LOST is real and worth stating: an arm can pass
		# through the far thigh in an extreme pose. The alternative is a
		# curated per-pair exception list, which is a table of the kind this
		# project keeps paying for.
		pb.collision_mask = WORLD_LAYER
		pb.can_sleep = true

		# The body's own frame: +Y along the segment, +X the figure's own
		# mediolateral axis. `station/npc/ragdoll.py::joint_basis_note` explains
		# why that one choice serves both joint types.
		var ex := _v3(seg["frame_x"])
		var ay := _v3(seg["axis"])
		var ez := ex.cross(ay)
		var centre := _v3(seg["centre_m"]) * s3
		var world_centre: Vector3 = ex * centre.x + ay * centre.y + ez * centre.z
		pb.body_offset = Transform3D(Basis(ex, ay, ez), world_centre)

		var cs := CollisionShape3D.new()
		if String(seg["shape"]) == "box":
			var bx := BoxShape3D.new()
			var hm: Array = seg["half_m"]
			bx.size = Vector3(hm[0], hm[1], hm[2]) * 2.0 * s3
			cs.shape = bx
		else:
			var cap := CapsuleShape3D.new()
			cap.radius = float(seg["radius_m"]) * s3
			cap.height = maxf(float(seg["height_m"]) * s3, 2.0 * cap.radius)
			cs.shape = cap
		pb.add_child(cs)
		sim.add_child(pb)
		# The joint sits at the segment's own bone head, which in the body's
		# frame is minus the centre offset. Godot clamps it there itself
		# (`_fix_joint_offset`); computing it as well means the two agree
		# rather than one of them being a surprise.
		var jbasis := Basis(Vector3(0, 1, 0), Vector3(0, 0, 1), Vector3(1, 0, 0))
		var jd: Dictionary = seg["joint"]
		# THE OFFSET GOES ON BEFORE THE TYPE, AND THE ORDER IS THE WHOLE
		# CONSTRAINT. `PhysicalBone3D::set_joint_type` is what calls
		# `_reload_joint()`, and `_reload_joint` is the only place the joint's
		# frames are built -- `joint_transf = get_global_transform() *
		# joint_offset`. `set_joint_offset` does NOT reload it (it only fixes
		# the origin and resets the body to rest). So setting the type first
		# builds every joint from an IDENTITY offset, which puts the hinge axis
		# on the body's local Z instead of its local X: measured, a knee that
		# went to **-180 degrees** under a limit of -2..145, because the axis
		# the limit was about was not the axis the knee bends on.
		if String(jd["type"]) != "none":
			pb.joint_offset = Transform3D(jbasis, -centre)
		match String(jd["type"]):
			"hinge":
				pb.joint_type = PhysicalBone3D.JOINT_TYPE_HINGE
				pb.set("joint_constraints/angular_limit_enabled", true)
				pb.set("joint_constraints/angular_limit_lower",
					float(jd["lower_deg"]))
				pb.set("joint_constraints/angular_limit_upper",
					float(jd["upper_deg"]))
			"cone":
				pb.joint_type = PhysicalBone3D.JOINT_TYPE_CONE
				pb.set("joint_constraints/swing_span", float(jd["swing_deg"]))
				pb.set("joint_constraints/twist_span", float(jd["twist_deg"]))
			_:
				pb.joint_type = PhysicalBone3D.JOINT_TYPE_NONE
		# NOT `reset_to_rest_position()`: it exists on `PhysicalBone3D` in C++
		# and is NOT bound to script in 4.4 (`_bind_methods` does not list it),
		# so calling it aborts the build with "Nonexistent function" and every
		# promoted body comes out with zero segments -- which the first engine
		# run of this file did, and reported as a clean 0.33 s settle. The
		# engine does the reset itself: `set_body_offset` -> `_update_joint_
		# offset` -> `reset_to_rest_position`, and `bone_name` -> `update_bone_
		# id` -> the same. Setting `joint_offset` after `body_offset` is what
		# puts the body on its bone.
		doll.bones.append(pb)
		doll.seg.append(seg)
		doll.anchor_child.append(-centre)
		var par = seg["parent"]
		doll.parent_of.append(int(by_name[String(par)]) if par != null else -1)
	# The joint point expressed in the PARENT's frame, recorded once at rest so
	# `worst_joint_m` measures separation rather than re-deriving the rig.
	for i in range(doll.bones.size()):
		var p: int = doll.parent_of[i]
		if p < 0:
			doll.anchor_parent.append(Vector3.ZERO)
			continue
		var w: Vector3 = (doll.bones[i] as PhysicalBone3D).global_transform \
			* doll.anchor_child[i]
		doll.anchor_parent.append(
			(doll.bones[p] as PhysicalBone3D).global_transform.affine_inverse() * w)


# ===========================================================================
#  FALLING, AND MEASURING THE FALL
# ===========================================================================
func _physics_process(delta: float) -> void:
	for i in range(_live.size() - 1, -1, -1):
		var doll: Doll = _live[i]
		if not is_instance_valid(doll.root):
			_live.remove_at(i)
			continue
		doll.t += delta
		_apply_gravity(doll, delta)
		_clamp(doll)
		_measure(doll)
		if doll.settle_t < 0.0 and doll.quiet_frames >= doll.settle_frames_needed:
			doll.settle_t = doll.t
			_settled += 1
			print(("ragdoll: SETTLED %s (%s) in %.2f s -- peak %.2f m/s, "
				+ "worst joint gap %.1f mm, deck penetration %.1f mm at rest "
				+ "(%.1f mm worst at impact), fell %.2f m, knees %.0f..%.0f deg")
				% [doll.species, doll.cause, doll.settle_t, doll.peak_speed,
				doll.worst_joint_m * 1000.0, doll.rest_pen_m * 1000.0,
				doll.deepest_pen_m * 1000.0, doll.fall_m,
				doll.knee_lo, doll.knee_hi])
			if not doll.dead:
				demote(doll)
		elif doll.settle_t < 0.0 and doll.t > doll.timeout_s:
			doll.settle_t = -2.0
			print(("ragdoll: TIMEOUT %s (%s) after %.1f s -- still moving at "
				+ "%.3f m/s; put down where it is")
				% [doll.species, doll.cause, doll.t, _fastest(doll)])


## THE FALL IS AGAINST THIS DECK'S OWN GRAVITY. Applied as an impulse per tick
## rather than through `gravity_scale`, because Godot's project gravity is one
## vector for the whole world and this station does not have one: "down" is
## radially outward from the spin axis and its magnitude is a function of
## radius. `--zero-g` withholds it, which is the control -- a body that still
## settles with no gravity was never falling.
func _apply_gravity(doll: Doll, delta: float) -> void:
	if doll.g <= 0.0:
		return
	var a: Vector3 = -doll.up * doll.g * delta
	for pb in doll.bones:
		var b := pb as PhysicalBone3D
		if b.is_simulating_physics():
			b.apply_central_impulse(a * b.mass)


## Hold the solver to what gravity and the incident can actually produce. See
## `v_cap`. Without it, a knee arriving at its 145-degree limit at speed pumps
## energy into the chain and the whole body reaches **471 m/s and 15.6 m of
## joint separation** -- measured, in the shipped scene, on the run that first
## got the hinge axes right.
func _clamp(doll: Doll) -> void:
	for i in range(doll.bones.size()):
		var pb := doll.bones[i] as PhysicalBone3D
		var v: Vector3 = pb.linear_velocity
		if v.length() > doll.v_cap:
			pb.linear_velocity = v.normalized() * doll.v_cap
			doll.clamped += 1
		# Angular, as the tip speed the same cap implies over this segment's
		# own length -- so a hand is allowed to spin faster than a thigh, which
		# is what having a length means.
		var l: float = maxf(0.05, float(doll.seg[i]["length_m"]) * doll.scale)
		var w: Vector3 = pb.angular_velocity
		var wcap: float = doll.v_cap / l
		if w.length() > wcap:
			pb.angular_velocity = w.normalized() * wcap
			doll.clamped += 1


func _measure(doll: Doll) -> void:
	var fastest := 0.0
	for pb in doll.bones:
		var v: float = (pb as PhysicalBone3D).linear_velocity.length()
		fastest = maxf(fastest, v)
	doll.peak_speed = maxf(doll.peak_speed, fastest)
	# DID IT FALL? The instrument the `--zero-g` control needs, and the reason
	# it needs its own: "settled" only asks whether the body has stopped, and a
	# body in no gravity has never started. What separates a collapse from a
	# statue is that the CENTRE OF MASS COMES DOWN -- about 0.8 m for a
	# standing human, from mid-chest to the deck -- so that is what is measured
	# and reported, along the body's own up rather than along -Y.
	doll.fall_m = maxf(doll.fall_m, (doll.com0 - _com(doll)).dot(doll.up))
	# SETTLED IS A DISPLACEMENT TEST, NOT A VELOCITY TEST, and the difference
	# decides whether a body ever settles at all. A resting body's feet buzz
	# against the deck: measured, a corpse whose fastest bone averaged 0.018
	# m/s -- a third of the threshold -- never once produced twenty CONSECUTIVE
	# ticks under it, so an instantaneous check reported "settle=NEVER" on a
	# body that had visibly stopped. What the derived threshold actually means
	# is "the picture has stopped moving", so the honest form of it is how far
	# anything got over the window, which contact jitter cancels out of.
	var n: int = doll.settle_frames_needed
	if doll.trail.is_empty():
		doll.trail.resize(n)
	var row := PackedVector3Array()
	for pb in doll.bones:
		row.append((pb as PhysicalBone3D).global_position)
	var old = doll.trail[doll.trail_at]
	doll.trail[doll.trail_at] = row
	doll.trail_at = (doll.trail_at + 1) % n
	var moved := -1.0
	if old != null and (old as PackedVector3Array).size() == row.size():
		moved = 0.0
		for i in range(row.size()):
			moved = maxf(moved, row[i].distance_to((old as PackedVector3Array)[i]))
	var window_m: float = doll.settle_v * float(n) / 60.0
	doll.quiet_frames = n if (moved >= 0.0 and moved < window_m) else 0

	# JOINT SEPARATION. A constraint solver does not weld: it pulls. The gap
	# between where the child says its joint is and where the parent says it is
	# is the honest measure of "did it explode", and it is the number that goes
	# to hundreds of millimetres when a mass ratio or a shape is wrong.
	for i in range(doll.bones.size()):
		var p: int = doll.parent_of[i]
		if p < 0:
			continue
		var a: Vector3 = (doll.bones[i] as PhysicalBone3D).global_transform \
			* doll.anchor_child[i]
		var b: Vector3 = (doll.bones[p] as PhysicalBone3D).global_transform \
			* doll.anchor_parent[i]
		doll.worst_joint_m = maxf(doll.worst_joint_m, a.distance_to(b))

	# THE KNEE'S WHOLE RANGE, every frame rather than at the end. A limb that
	# inverts during a tumble and comes back is still a limb that inverted, and
	# the `--no-joint-limits` control is exactly that transient. Recorded as a
	# range and compared against the DECLARED limit, so the instrument does not
	# have to know which way round the solver counts.
	for nm in ["knee_r", "knee_l"]:
		var k := hinge_deg(doll, nm)
		doll.knee_lo = minf(doll.knee_lo, k)
		doll.knee_hi = maxf(doll.knee_hi, k)

	# INTERPENETRATION, against the deck the body is actually lying on rather
	# than against a plane. Cast along the body's own down from each segment's
	# centre, and ask how far the segment's lowest point is BELOW what it hits.
	# Only the ragdoll's own layer is excluded, so what it finds is the floor.
	var space := get_world_3d().direct_space_state
	var pen := 0.0
	for i in range(doll.bones.size()):
		var pb := doll.bones[i] as PhysicalBone3D
		var c: Vector3 = pb.global_position
		var q := PhysicsRayQueryParameters3D.create(
			c + doll.up * 0.05, c - doll.up * 2.0)
		q.collision_mask = WORLD_LAYER
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			continue
		var low: float = _lowest_along(pb, doll.seg[i], doll.up, doll.scale)
		var floor_h: float = (hit["position"] as Vector3).dot(doll.up)
		doll.deepest_pen_m = maxf(doll.deepest_pen_m, floor_h - low)
		pen = maxf(pen, floor_h - low)
	# THE PENETRATION THAT MATTERS IS THE ONE THAT IS LEFT. A solver lets a
	# fast contact sink for a frame or two and pushes it back out; the number a
	# player can see is the one the body comes to rest at, so both are kept and
	# both are reported.
	if doll.quiet_frames > 0:
		doll.rest_pen_m = pen


## How far the segment's collision shape reaches along -up, in world units.
func _lowest_along(pb: PhysicalBone3D, seg: Dictionary, up: Vector3,
		s: float) -> float:
	var t := pb.global_transform
	var centre := t.origin.dot(up)
	if String(seg["shape"]) == "box":
		var hm: Array = seg["half_m"]
		var h := Vector3(hm[0], hm[1], hm[2]) * s
		var reach: float = absf(t.basis.x.dot(up)) * h.x \
			+ absf(t.basis.y.dot(up)) * h.y + absf(t.basis.z.dot(up)) * h.z
		return centre - reach
	var r: float = float(seg["radius_m"]) * s
	var half: float = maxf(float(seg["height_m"]) * s * 0.5, r)
	return centre - (absf(t.basis.y.dot(up)) * (half - r) + r)


## The mass-weighted centre of the physical body, in world space.
func _com(doll: Doll) -> Vector3:
	var acc := Vector3.ZERO
	var m := 0.0
	for pb in doll.bones:
		var b := pb as PhysicalBone3D
		acc += b.global_position * b.mass
		m += b.mass
	return acc / maxf(m, 1e-6)


func _fastest(doll: Doll) -> float:
	var f := 0.0
	for pb in doll.bones:
		f = maxf(f, (pb as PhysicalBone3D).linear_velocity.length())
	return f


# ===========================================================================
#  WIRING
# ===========================================================================
## Materials are BORROWED from the cell the body is standing in, never
## invented. `station/materials.py` binds by substring on the group fragment
## and the streamed `.glb` already carries the resolved material for every
## `npc_skin`, `npc_cloth__*`, `npc_hair` and `npc_leather__*` surface on the
## deck -- so a promoted body wears exactly what the baked body it replaces was
## wearing. **A fallback is counted and reported** rather than silently used:
## a body in flat grey is the tell that the donor was not wired.
func set_material_donor(node: Node) -> void:
	_donor = node
	_mat_cache.clear()


func _material_for(group: String):
	if _mat_cache.has(group):
		return _mat_cache[group]
	var found: Material = null
	if _donor != null:
		found = _scan_materials(_donor, group)
	if found == null:
		_mat_fallbacks += 1
	_mat_cache[group] = found
	return found


func _scan_materials(n: Node, group: String) -> Material:
	if n is MeshInstance3D:
		var mi := n as MeshInstance3D
		if String(mi.name).find(group) >= 0 and mi.mesh != null:
			for i in range(mi.mesh.get_surface_count()):
				var m: Material = mi.get_active_material(i)
				if m != null:
					return m
	# AND THE CROWD, WHICH IS NOT A MeshInstance3D. Scanning only those found
	# nothing at all in a corridor cell and every promoted body came out on the
	# fallback: since INV-403 the room occupants are instanced too, so the only
	# thing in the tree wearing `npc_skin` is a **MultiMeshInstance3D** that
	# `npc.gd` made. Its material lives on the shared mesh's surface rather
	# than on the instance.
	if n is MultiMeshInstance3D:
		var mm := n as MultiMeshInstance3D
		if String(mm.name).find(group) >= 0 and mm.multimesh != null \
				and mm.multimesh.mesh != null:
			if mm.material_override != null:
				return mm.material_override
			for i in range(mm.multimesh.mesh.get_surface_count()):
				var m2: Material = mm.multimesh.mesh.surface_get_material(i)
				if m2 != null:
					return m2
	for c in n.get_children():
		var got := _scan_materials(c, group)
		if got != null:
			return got
	return null


## The player's body, so every promoted body can except it. See `promote`.
func watch(body: Node3D) -> void:
	if body is CollisionObject3D:
		_player_rid = (body as CollisionObject3D).get_rid()


func live_count() -> int:
	return _live.size()


func report() -> String:
	return "promoted=%d settled=%d live=%d refused=%d%s material_fallbacks=%d" \
		% [_promoted, _settled, _live.size(), _refused,
		("" if _why_refused == "" else " (" + _why_refused + ")"),
		_mat_fallbacks]


# ===========================================================================
#  THE GATE
# ===========================================================================
## Promote a body, drop it, and print what it did. Runs in the shipped scene,
## on the streamed build, at the player's own spawn -- so it cannot pass on a
## rig that only exists in a test harness. **This project has ten instances of
## built-but-unreachable and the tenth was found the day before this was
## written**, so a scan that finds a reference is not evidence and this is what
## is offered instead.
##
## `spec` is the same dictionary `promote` takes. Returns immediately; the
## result arrives through `_physics_process` and `gate_verdict()`.
var _gate_dolls: Array = []
var _gate_labels: Array = []


func gate_drop(label: String, spec: Dictionary) -> void:
	var doll := promote(spec)
	_gate_dolls.append(doll)
	_gate_labels.append(label)
	if doll == null:
		print("ragdoll: gate %-14s REFUSED -- %s" % [label, _why_refused])


func gate_done() -> bool:
	for d in _gate_dolls:
		if d != null and not d.done and d.settle_t == -1.0:
			return false
	return true


func gate_verdict() -> String:
	var out: Array = []
	for i in range(_gate_dolls.size()):
		var d: Doll = _gate_dolls[i]
		if d == null:
			out.append("%s: refused" % _gate_labels[i])
			continue
		out.append(("%s: settle=%s peak=%.2fm/s joint=%.1fmm pen_peak=%.1fmm "
			+ "pen_rest=%.1fmm fell=%.2fm knee=%.0f..%.0fdeg (limit %.0f..%.0f) "
			+ "clamped=%d")
			% [_gate_labels[i],
			("%.2fs" % d.settle_t) if d.settle_t > 0.0 else "NEVER",
			d.peak_speed, d.worst_joint_m * 1000.0, d.deepest_pen_m * 1000.0,
			d.rest_pen_m * 1000.0, d.fall_m, d.knee_lo, d.knee_hi,
			d.knee_limit.x, d.knee_limit.y, d.clamped])
	return "\n".join(out)


## The signed flexion of a hinge, in degrees, measured off the bodies rather
## than off the constraint. Positive is flexion (the shin swinging back);
## NEGATIVE IS HYPEREXTENSION and it is what "the limbs invert" looks like as a
## number. With the limits on it cannot pass -2 deg; the `--no-joint-limits`
## control removes them and this is the instrument that notices.
func hinge_deg(doll: Doll, bone: String) -> float:
	for i in range(doll.seg.size()):
		if String(doll.seg[i]["bone"]) != bone:
			continue
		var p: int = doll.parent_of[i]
		if p < 0:
			return 0.0
		var child := (doll.bones[i] as PhysicalBone3D).global_transform.basis
		var par := (doll.bones[p] as PhysicalBone3D).global_transform.basis
		var axis: Vector3 = par.x                       # the hinge axis
		var a: Vector3 = par.y - axis * par.y.dot(axis)
		var b: Vector3 = child.y - axis * child.y.dot(axis)
		if a.length() < 1e-6 or b.length() < 1e-6:
			return 0.0
		a = a.normalized()
		b = b.normalized()
		# `b.cross(a)`, NOT `a.cross(b)`, and the order was settled by the
		# engine rather than by reasoning. Measured the other way round, a body
		# folding its knees to a perfectly ordinary 86 degrees reported
		# **-86** and one against its 145-degree limit reported **-148** --
		# which reads as "the limbs are inverting" when what is happening is
		# that GodotPhysics counts a hinge the opposite way from the naive
		# right-hand rule about the same axis. Flipped here so the number is in
		# the same sign convention as the limit it is checked against.
		var s: float = axis.dot(b.cross(a))
		return rad_to_deg(atan2(s, a.dot(b)))
	return 0.0


## The two controls that live inside this file. The third -- promotion turned
## off entirely -- is `--no-ragdoll`, at the top.
func apply_controls() -> String:
	var a := _args()
	var said: Array = []
	if a.has("no-joint-limits"):
		said.append("joint limits REMOVED")
	if a.has("zero-g"):
		said.append("gravity ZERO")
	if a.has("ragdoll-solid"):
		said.append("player NOT excepted (the pre-4h floor-loss hazard)")
	return "-" if said.is_empty() else ", ".join(said)


## The bits a player's `collision_mask` must carry to FEEL a settled body.
##
## STATIC, AND READ BY `walk.gd` AT SPAWN, because the player is built before
## any body falls over and its mask has to be right from its first frame. Zero
## on the shipped build -- a corpse is separated by `npc.gd::push_off`, never by
## the solver, for the floor-loss reason above. `--ragdoll-solid` returns
## `RAGDOLL_LAYER`, which is the OTHER half of that control; see the block at
## `physical_bones_add_collision_exception` for the four measured runs that
## showed the flag doing nothing without it.
##
## ONE COPY OF THE LAYER NUMBER. `walk.gd` could have written 16 and it would
## have been right today; this project's own history is a list of second copies
## of a mapping with one of them updated.
static func player_extra_mask() -> int:
	for a in OS.get_cmdline_user_args():
		if String(a) == "--ragdoll-solid":
			return RAGDOLL_LAYER
	return 0


func controls_open_joints() -> bool:
	return _args().has("no-joint-limits")


func controls_zero_g() -> bool:
	return _args().has("zero-g")


# ===========================================================================
func _doc(species: String) -> Dictionary:
	if _docs.has(species):
		return _docs[species]
	var p := data_dir.path_join(species + "_ragdoll.json")
	if not FileAccess.file_exists(p):
		_docs[species] = {}
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	var d = JSON.parse_string(f.get_as_text())
	var doc: Dictionary = d if typeof(d) == TYPE_DICTIONARY else {}
	# THE CONTROL THAT HAS TO FIRE. Opening every joint to 180 degrees is what
	# "no joint limits" means for a cone and a hinge alike, and it is done to
	# the DATA rather than to the builder so that nothing about the build path
	# differs between the control and the subject.
	if not doc.is_empty() and controls_open_joints():
		for seg in ((doc["ragdoll"] as Dictionary)["segments"] as Array):
			var j: Dictionary = seg["joint"]
			if String(j["type"]) == "hinge":
				j["lower_deg"] = -180.0
				j["upper_deg"] = 180.0
			elif String(j["type"]) == "cone":
				j["swing_deg"] = 180.0
				j["twist_deg"] = 180.0
	_docs[species] = doc
	return doc


func _v3(a) -> Vector3:
	if typeof(a) == TYPE_ARRAY and (a as Array).size() == 3:
		return Vector3(float(a[0]), float(a[1]), float(a[2]))
	return Vector3.ZERO


func _root() -> String:
	return ProjectSettings.globalize_path("res://").path_join("..").simplify_path()


func _args() -> Dictionary:
	var out := {}
	for a in OS.get_cmdline_user_args():
		var s := String(a)
		if s.begins_with("--"):
			var b := s.substr(2)
			var eq := b.find("=")
			if eq >= 0:
				out[b.substr(0, eq)] = b.substr(eq + 1)
			else:
				out[b] = "1"
	return out


## BODIES ON THE FLOOR ARE NOT SAVED.
## An incident is regenerated from `station/incident.py`'s tables and the clock,
## so the station keeps producing them at the same rate after a reload. A body
## that was already lying there when the game was saved is gone. That is a
## visible discontinuity and it is recorded rather than hidden: keeping one
## needs the collapse to be an entity with an id, which is the same piece of
## work the crowd and the dialogue both name.
func save_exempt() -> String:
	return "incidents regenerate from the clock; a body already down is LOST"
