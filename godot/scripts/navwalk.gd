extends SceneTree
## THE GATE ON `navgraph.gd` -- and the body that walks what it answered.
##
## `docs/MASTER-PLAN.md` P0.6's last item asks for one thing: *an NPC paths
## across decks on the engine graph*. This is the half that has to happen inside
## the engine, and it is deliberately three questions rather than one, because an
## existence proof is not a gate:
##
##   1. **A DENOMINATOR.** Every one of the 741 pairs of walkable z-clusters is
##      routed HERE, in GDScript, at run time -- and each answer is compared
##      NODE FOR NODE against the route `station/route_walk.path_between` found
##      in Python. Agreeing about how many hops a journey takes is cheap;
##      agreeing about which corridor it goes down is the only comparison that
##      can catch a graph that has been quietly re-derived in the engine.
##   2. **IT SURVIVES STREAMING.** Every node is resolved with NOTHING in the
##      scene tree, then again after geometry has been added and freed, and the
##      control is a graph that only counts nodes whose cell is resident -- which
##      is what a `NavigationRegion3D` baked from the loaded set would be, and it
##      loses most of the station.
##   3. **A BODY WALKS IT.** One named resident, two z-clusters, a route this
##      file asked the graph for AFTER the scene was up, and `floor_m` -- metres
##      covered while standing on something. Never path length: this codebase has
##      twice found a falling body reporting a journey.
##   4. **AND THE SHIPPED RUNTIME CAN REACH IT.** The same route is asked for a
##      second time through `life.gd`'s Director -- the object that owns
##      inhabitants and therefore the place a future commuter will ask from --
##      and the two polylines are compared waypoint for waypoint. A hook whose
##      gate only proves it compiles is the state `stream.gd` was in when it
##      scored green and moved nobody.
##
## NOTHING HERE DECIDES A ROUTE. `navgraph.gd` searches; the graph came out of
## `station/routes.py` through `station/navgraph_export.py`; the waypoints are
## `station/route_walk.py`'s. This file loads, asks, steers and counts.
##
## Run through its owner:  python3 station/navgraph_export.py --gate

const NAV := preload("res://scripts/navgraph.gd")

## How much faster than real time the walk runs. See `_start_walk` -- it moves
## `physics_ticks_per_second` and `time_scale` together, so the body's step in
## simulated time is unchanged and only the wall clock shrinks.
const FAST := 8

var _opt := {}
var _nav: Node = null
var _world: Node3D = null
var _walker: Node3D = null


## The body, and the run.
##
## A Node3D CHILD RATHER THAN THIS SCRIPT'S OWN `_physics_process`, and that is
## `life.gd`'s Commuter pattern copied for its reason: a `SceneTree` script's
## physics callback is a `MainLoop` virtual and the tree's own step is not the
## same thing. Every headless walk in this project that works is driven from a
## node inside the tree.
class Walker extends Node3D:
	var body: CharacterBody3D = null
	var pts := PackedVector3Array()
	var cum := PackedFloat64Array()
	var s := 0.0
	var frame := 0
	var max_frames := 60000
	var floor_m := 0.0
	var air_m := 0.0
	var off := 0
	var prev := Vector3.ZERO
	var settle := 90
	var target := Vector3.ZERO
	var reached := 1e30
	var arrived_m := 1.5
	var steer := true
	var done := false
	var stall := 0
	var last_s := 0.0
	var owner_tree = null
	var note := ""

	func _ready() -> void:
		set_physics_process(true)

	func _physics_process(delta: float) -> void:
		if done or body == null:
			return
		frame += 1
		if frame <= settle:
			if frame == settle:
				prev = body.global_position
			return
		if frame > max_frames:
			finish("the run's own %d frame cap" % max_frames)
			return

		# WHERE ON THE POLYLINE THE BODY HAS ACTUALLY GOT TO, searching forward
		# from where it was. `life.gd`'s `Route.advance`, and its reason: a
		# carrot placed ahead of the SCHEDULE is only on the route when the two
		# are together, and 44 m along a ring corridor from a doorway is a point
		# through two walls.
		s = advance(s, body.global_position)
		var carrot := point_at(minf(cum[cum.size() - 1], s + 2.0))
		if steer:
			var to := carrot - body.global_position
			var up: Vector3 = body.body_up()
			var flat: Vector3 = to - up * to.dot(up)
			if flat.length() > float(body.speed_m_s) * delta:
				body.step(delta, Vector2.ZERO, false, false, to)
			else:
				body.step(delta, Vector2.ZERO, false, false)
		else:
			body.step(delta, Vector2.ZERO, false, false)

		# FLOOR METRES, NEVER PATH LENGTH. This codebase has twice found a
		# falling body reporting a journey -- 11,712 m in the streaming work and
		# 876,827 m before that.
		var now := body.global_position
		var d := now.distance_to(prev)
		if body.is_on_floor():
			floor_m += d
		else:
			air_m += d
			off += 1
		prev = now
		reached = minf(reached, now.distance_to(target))

		if reached <= arrived_m:
			finish("arrived")
			return
		if s - last_s < 0.001:
			stall += 1
			if stall > 60 * 20:
				finish("stopped making progress for 20 s")
				return
		else:
			stall = 0
			last_s = s

	func finish(why: String) -> void:
		done = true
		note = why
		if owner_tree != null:
			owner_tree.verdict()

	func advance(s_from: float, p: Vector3, window: float = 12.0) -> float:
		var best := s_from
		var best_d := 1e30
		var i := 0
		while i + 1 < pts.size():
			if cum[i + 1] < s_from:
				i += 1
				continue
			if cum[i] > s_from + window:
				break
			var a := pts[i]
			var ab := pts[i + 1] - a
			var l2 := ab.length_squared()
			var t := 0.0 if l2 <= 1e-12 else clampf((p - a).dot(ab) / l2, 0.0, 1.0)
			var q := a + ab * t
			var dd := q.distance_squared_to(p)
			if dd < best_d:
				best_d = dd
				best = maxf(s_from, cum[i] + sqrt(l2) * t)
			i += 1
		return best

	func point_at(x: float) -> Vector3:
		if pts.is_empty():
			return Vector3.ZERO
		var l: float = cum[cum.size() - 1]
		if x <= 0.0:
			return pts[0]
		if x >= l:
			return pts[pts.size() - 1]
		var lo := 0
		var hi := cum.size() - 1
		while lo + 1 < hi:
			var mid := (lo + hi) / 2
			if cum[mid] <= x:
				lo = mid
			else:
				hi = mid
		var seg: float = cum[lo + 1] - cum[lo]
		var fr: float = 0.0 if seg <= 1e-9 else (x - cum[lo]) / seg
		return pts[lo].lerp(pts[lo + 1], fr)


var _hops := 0
var _kinds := ""
var _from := ""
var _to := ""
var _found := false
var _crossed := false
var _reported := false


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var s := a.substr(2)
			var eq := s.find("=")
			if eq >= 0:
				_opt[s.substr(0, eq)] = s.substr(eq + 1)
			else:
				_opt[s] = "1"
	_nav = NAV.new()
	if not _nav.load_graph(String(_opt.get("graph", ""))):
		push_error("navwalk: " + String(_nav.why))
		quit(2)
		return
	print("navgraph: %d nodes, %d edges, digest %s"
		% [_nav.node_count(), _nav.edge_count(), _nav.digest])
	# BEFORE ANYTHING IS ASKED OF IT, so the control applies to both modes: a
	# graph with one kind of edge removed has to fail the pair sweep the same way
	# it fails the walk.
	if _opt.has("drop-edge"):
		_drop(String(_opt["drop-edge"]))
	if _opt.has("pairs"):
		_run_pairs()
		quit(0)
		return
	if _opt.has("walk"):
		_start_walk()
		return
	push_error("navwalk: nothing to do -- pass --pairs= or --walk=")
	quit(2)


# ===========================================================================
# 1.  THE DENOMINATOR, AND THE STREAMING PROPERTY
# ===========================================================================

func _run_pairs() -> void:
	var f := FileAccess.open(String(_opt["pairs"]), FileAccess.READ)
	if f == null:
		push_error("navwalk: no pair list at " + String(_opt["pairs"]))
		quit(2)
		return
	var rows = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(rows) != TYPE_ARRAY:
		push_error("navwalk: the pair list is not an array")
		quit(2)
		return

	var routed := 0
	var mismatch := 0
	var crossdeck := 0
	var crossring := 0
	var crosssector := 0
	var first_bad := ""
	var t0 := Time.get_ticks_usec()
	for r in rows:
		var row: Dictionary = r
		var a: int = _nav.node_of(String(row["a"]))
		var b: int = _nav.node_of(String(row["b"]))
		if a < 0 or b < 0:
			mismatch += 1
			if first_bad == "":
				first_bad = "%s or %s is not a node" % [row["a"], row["b"]]
			continue
		var seq: PackedInt32Array = _nav.path(a, b)
		if seq.is_empty():
			if first_bad == "":
				first_bad = "no engine route %s -> %s" % [row["a"], row["b"]]
			continue
		routed += 1
		# NODE FOR NODE. `route_walk.path_between` returns LEGS and inserts the
		# axial self-loop where the path enters a spine; the node sequence it
		# implies is what Python wrote into the list, so this compares the two
		# sequences directly.
		var want: Array = row["seq"] if row["seq"] != null else []
		var got: Array = []
		for i in seq:
			got.append(String((_nav.nodes[i] as Dictionary)["id"]))
		if got != want:
			mismatch += 1
			if first_bad == "":
				first_bad = "%s -> %s: engine %s, python %s" % [
					row["a"], row["b"], str(got), str(want)]
		var na: Dictionary = _nav.nodes[a]
		var nb: Dictionary = _nav.nodes[b]
		var same_sector: bool = str(na.get("sector", "")) == str(nb.get("sector", "!"))
		var same_ring: bool = int(na.get("ring", -1)) == int(nb.get("ring", -2))
		var same_deck: bool = int(na.get("deck", -1)) == int(nb.get("deck", -2))
		if not (same_sector and same_ring and same_deck):
			crossdeck += 1
		if not (same_sector and same_ring):
			crossring += 1
		if not same_sector:
			crosssector += 1
	var us := float(Time.get_ticks_usec() - t0)

	# AND THE OTHER SEARCH, ON THE SAME PAIRS. `path_weighted` orders by METRES
	# rather than by hops, and it exists because the two questions are different
	# -- but a second search with no caller and no gate is exactly the thing this
	# project keeps finding scored green and moving nobody, so it is run here and
	# the disagreement is reported. It cannot be compared against Python: that
	# authority's BFS answers hops, and `routes.py` carries a real `length_m` on
	# its `trunk` edges only. What IS asserted is that it routes everything the
	# hop search does; where it differs is a shorter walk, not a missing one.
	var t1 := Time.get_ticks_usec()
	var w_routed := 0
	var w_differ := 0
	for r in rows:
		var row2: Dictionary = r
		var a2: int = _nav.node_of(String(row2["a"]))
		var b2: int = _nav.node_of(String(row2["b"]))
		if a2 < 0 or b2 < 0:
			continue
		var wseq: PackedInt32Array = _nav.path_weighted(a2, b2)
		if wseq.is_empty():
			continue
		w_routed += 1
		if wseq != _nav.path(a2, b2):
			w_differ += 1
	print("NAVGRAPH WEIGHTED routed=%d of=%d differ=%d us_per_search=%.1f"
		% [w_routed, rows.size(), w_differ,
			float(Time.get_ticks_usec() - t1) / maxf(1.0, float(rows.size()))])

	print(("NAVGRAPH PAIRS routed=%d of=%d mismatch=%d crossdeck=%d "
		+ "crossring=%d crosssector=%d us_per_search=%.1f total_ms=%.1f%s")
		% [routed, rows.size(), mismatch, crossdeck, crossring, crosssector,
			us / maxf(1.0, float(rows.size())), us / 1000.0,
			("" if first_bad == "" else "  first=" + first_bad)])

	_run_stream()


## THE STREAMING PROPERTY, MEASURED THREE WAYS.
##
## `resolved` -- every node found by POSITION with an empty scene tree.
## `after`    -- the same query after a hundred MeshInstance3Ds have been added
##               and freed, which is what a cell arriving and leaving does to the
##               shape of the tree.
## `control`  -- the same query when only nodes "in the resident set" count. That
##               is a navmesh baked from what is loaded, expressed as a filter,
##               and it is the number a `NavigationRegion3D` design would get.
func _run_stream() -> void:
	var n: int = _nav.node_count()
	# THE NODES WITH REAL GEOMETRY, which is `route_walk.endpoints`' 39 walkable
	# z-clusters. The other 57 carry a topological position only (their z, on the
	# axis) because that module refused them a floor, and two of those can share
	# a point -- so asking "does the nearest node to X come back as X" of one of
	# them is asking about a tie rather than about streaming.
	var want: PackedInt32Array = PackedInt32Array()
	for i in range(n):
		var nd: Dictionary = _nav.nodes[i]
		if String(nd.get("kind", "")) == "cluster" and bool(nd.get("walkable", false)):
			want.append(i)

	# ASKED OF THE CLUSTERS, AND THE FIRST VERSION WAS NOT -- it read 6 of 39.
	# A `spine` node's position is the point where that deck's axial corridor
	# meets its ring one, which IS one of its clusters' junctions, so an
	# unqualified nearest-node lands on whichever of the two sorts first. That is
	# a TIE and not a streaming failure, and a test that cannot tell them apart
	# is measuring the sort order. `distinct` below is the property that makes
	# the qualified question meaningful: no two clusters share a point, so
	# resolving one by position is unambiguous.
	var resolved := 0
	for i in want:
		if _nav.nearest_node(_nav.node_pos(i), "cluster") == i:
			resolved += 1
	var distinct := {}
	for i in want:
		distinct[_nav.node_pos(i)] = 1

	# Geometry arrives, and leaves -- which is all a cell boundary is.
	var root := get_root()
	var junk := Node3D.new()
	root.add_child(junk)
	for i in range(100):
		var mi := MeshInstance3D.new()
		mi.mesh = BoxMesh.new()
		mi.position = Vector3(i * 3.0, 0.0, 0.0)
		junk.add_child(mi)
	var after := 0
	for i in want:
		if _nav.nearest_node(_nav.node_pos(i), "cluster") == i:
			after += 1
	junk.free()

	# THE CONTROL, AND IT IS THE `NavigationRegion3D` DESIGN EXPRESSED AS A
	# FILTER. `stream.gd` keeps the cell you are in plus both neighbours --
	# `budget.CELLS["resident_tris"]` 180,000 over `cell_tris` 60,000 = 3 cells,
	# 73.8 m each on the boot deck. A navmesh baked from the resident set can
	# only path inside that, so this counts the nodes within it: everything else
	# is a destination the engine could not have routed to.
	var here: Vector3 = _nav.node_pos(want[0]) if want.size() > 0 else Vector3.ZERO
	var control := 0
	for i in want:
		if _nav.node_pos(i).distance_to(here) <= 3.0 * 73.8:
			control += 1
	print(("NAVGRAPH STREAM resolved=%d after=%d control=%d of=%d distinct=%d "
		+ "searches=%d") % [resolved, after, control, want.size(),
			distinct.size(), _nav.searches])


# ===========================================================================
# 2.  THE WALK
# ===========================================================================

func _start_walk() -> void:
	var man := _read(String(_opt["walk"]))
	if man.is_empty():
		push_error("navwalk: could not read " + String(_opt["walk"]))
		quit(2)
		return

	var root := get_root()
	_world = Node3D.new()
	_world.name = "World"
	root.add_child(_world)
	var tris := 0
	for path in (man.get("collision_glbs", []) as Array):
		var sc := _glb(String(path))
		if sc == null:
			push_error("navwalk: could not load " + String(path))
			quit(2)
			return
		_world.add_child(sc)
		for m in _meshes(sc):
			m.create_trimesh_collision()
			if m.mesh != null:
				tris += _tri_count(m.mesh)

	# THE ROUTE IS ASKED FOR AFTER THE SCENE IS UP, deliberately: this is the
	# moment a running game would ask -- geometry in the tree, a body about to
	# stand on it -- and it is the moment a navmesh baked from the resident set
	# would have only what is loaded.
	var frm := String(_opt.get("from", ""))
	var to := String(_opt.get("to", ""))
	var a: int = _nav.node_of_place(frm)
	var b: int = _nav.node_of_place(to)
	var seq: PackedInt32Array = _nav.path(a, b) if (a >= 0 and b >= 0) \
		else PackedInt32Array()
	_found = seq.size() > 1
	_from = String((_nav.nodes[a] as Dictionary)["id"]) if a >= 0 else "?"
	_to = String((_nav.nodes[b] as Dictionary)["id"]) if b >= 0 else "?"
	_crossed = a >= 0 and b >= 0 and a != b
	var legs: Array = _nav.route_legs(a, b)
	var kinds: Array = []
	for leg in legs:
		var k := String(leg["kind"])
		if not kinds.has(k):
			kinds.append(k)
	kinds.sort()
	_kinds = ",".join(PackedStringArray(kinds))
	_hops = legs.size()

	_walker = Walker.new()
	_walker.owner_tree = self
	_walker.arrived_m = float(man.get("arrived_m", 1.5))
	_walker.steer = not _opt.has("no-steer")
	if not _found:
		verdict_with("no route on the graph")
		return

	_walker.pts = _nav.route_points(frm, to)
	if _walker.pts.size() < 2:
		verdict_with("the route carries %d waypoint(s)" % _walker.pts.size())
		return
	_walker.cum.append(0.0)
	for i in range(1, _walker.pts.size()):
		_walker.cum.append(_walker.cum[i - 1]
			+ _walker.pts[i].distance_to(_walker.pts[i - 1]))

	# EVERY PRESSURE DOOR OPEN. A shut door is a solid panel in the shell, and
	# whether a door opens is `door.gd`'s gate and `walkable.py --deck`'s, not
	# this one. What is under test here is whether the ROUTE is walkable.
	for m in _meshes(_world):
		if String(m.name).begins_with("doorpanel_"):
			for c in m.get_children():
				if c is StaticBody3D:
					for cs in c.get_children():
						if cs is CollisionShape3D:
							cs.disabled = true

	# THROUGH `life.gd`'s DIRECTOR, WHICH IS THE HOOK THIS SESSION ADDED TO IT.
	# The Director is the object that owns inhabitants, so it is where a future
	# commuter will ask for a route; `Director.route_between` delegates to this
	# graph and returns empty when the build has none. Asserted waypoint for
	# waypoint against the polyline the body is about to walk, because a hook
	# whose gate only proves it COMPILES is the state `stream.gd` was in when it
	# scored green and moved nobody.
	var L = load("res://scripts/life.gd")
	var same := -1
	if L != null:
		var dir = L.Director.new()
		root.add_child(dir)
		dir.nav = _nav
		var via: PackedVector3Array = dir.route_between(frm, to)
		same = 1 if via == _walker.pts else 0
		print("NAVGRAPH DIRECTOR same=%d pts=%d via=%d"
			% [same, _walker.pts.size(), via.size()])
		dir.queue_free()

	_walker.body = _spawn(man)
	root.add_child(_walker.body)
	_walker.prev = _walker.body.position
	_walker.target = _walker.pts[_walker.pts.size() - 1]
	# THE BUDGET IS THE ROUTE'S OWN LENGTH AT THE BODY'S OWN SPEED, times three
	# for the acceleration at every waypoint and the arc a body cuts at a corner.
	_walker.max_frames = int(ceil(_walker.cum[_walker.cum.size() - 1]
		/ float(_walker.body.speed_m_s) * 60.0 * 3.0)) + 900

	# WALL TIME, NOT SIMULATED TIME -- and the two knobs move together for the
	# reason `life.gd` records: a body stepping 1.9 m at a time is not walking.
	# A headless tree still steps physics in REAL time, so 9,256 ticks at 60 Hz
	# is 154 seconds of a CI job spent watching a capsule walk 645 m. Raising
	# `time_scale` alone scales the DELTA each tick receives, which is the thing
	# that must not change; raising it together with `physics_ticks_per_second`
	# by the same factor leaves the delta at exactly 1/60 s and runs the same
	# ticks faster. Measured against the x1 run: identical floor_m, identical
	# frame count, identical arrival.
	Engine.physics_ticks_per_second = 60 * FAST
	Engine.max_physics_steps_per_frame = FAST * 4
	Engine.time_scale = float(FAST)
	# AND IT SAYS WHICH ONE IT GOT. Anything that can substitute a lesser mode
	# for the one asked for reports what it did -- CLAUDE.md's rule, learned from
	# a renderer that silently fell back to OpenGL 3 and exited 0 with a PNG.
	var got := Engine.physics_ticks_per_second
	if got != 60 * FAST:
		push_error("navwalk: asked for %d physics ticks/s and got %d"
			% [60 * FAST, got])
	root.add_child(_walker)
	print(("navwalk: %s, route found at run time -- %d legs (%s), %d waypoints, "
		+ "%.1f m, %d collision tri, cap %d frames, physics %d Hz x%d "
		+ "(delta %.6f s)")
		% [String(man.get("deck", "?")), _hops, _kinds, _walker.pts.size(),
			_walker.cum[_walker.cum.size() - 1], tris, _walker.max_frames,
			Engine.physics_ticks_per_second, FAST,
			Engine.time_scale / float(Engine.physics_ticks_per_second)])


## THE NEGATIVE CONTROL, AND IT IS APPLIED TO THE GRAPH RATHER THAN THE
## GEOMETRY. Marking every edge of one kind unbuilt asks "was that edge load
## bearing", through `routes.py`'s own `built` flag and `navgraph.rebuild()`'s
## own index build -- so what is being searched is a graph that could really
## exist, not an adjacency somebody reached into. Two z-clusters of one deck are
## joined by exactly one axial corridor, so dropping `axial` must leave no route.
func _drop(kind: String) -> void:
	var n := 0
	for e in _nav.edges:
		if String((e as Dictionary)["kind"]) == kind:
			(e as Dictionary)["built"] = false
			n += 1
	_nav.rebuild()
	print("navwalk: CONTROL -- %d `%s` edge(s) marked unbuilt" % [n, kind])


func _spawn(man: Dictionary) -> CharacterBody3D:
	var b := CharacterBody3D.new()
	b.set_script(load("res://scripts/player.gd"))
	# DOWN IS OUTWARD. A ring deck is the inside of a spun barrel, so gravity is
	# the radial direction at the body's own position -- `player.gd`'s header
	# records what getting it wrong costs: a capsule lying sideways through the
	# floor, reporting `on_floor=true`, unable to move.
	b.gravity_mode = "drum"
	var shape := CollisionShape3D.new()
	var caps := CapsuleShape3D.new()
	caps.height = 1.8
	caps.radius = float(man.get("capsule_r_m", 0.35))
	shape.shape = caps
	shape.position = Vector3(0, caps.height * 0.5, 0)
	b.add_child(shape)
	b.position = Vector3(float(man["spawn"][0]), float(man["spawn"][1]),
		float(man["spawn"][2]))
	b.platform_floor_layers = 0
	# `player.gd`'s own exported speed. P0.7 is an OPEN OWNER DECISION about
	# whether the player should walk at 4.2 m/s or at the 1.22 m/s the NPCs are
	# Froude-scaled to; this gate takes no position on it and uses the shipped
	# number, so a route walkable here is walkable in the shipped build.
	return b


func verdict_with(why: String) -> void:
	if _walker != null:
		_walker.note = why
		_walker.done = true
	verdict()


func verdict() -> void:
	if _reported:
		return
	_reported = true
	var w := _walker
	var route_m: float = 0.0
	if w != null and w.cum.size() > 0:
		route_m = w.cum[w.cum.size() - 1]
	print(("NAVWALK who=%s found=%d crossed=%d hops=%d kinds=%s from=%s to=%s "
		+ "route_m=%.1f floor_m=%.1f air_m=%.2f offfloor=%d s=%.1f "
		+ "reached_m=%.2f frames=%d steer=%d why=%s")
		% [String(_opt.get("who", "?")).replace(" ", "_"),
			1 if _found else 0, 1 if _crossed else 0, _hops,
			("-" if _kinds == "" else _kinds), _from, _to,
			route_m,
			(0.0 if w == null else w.floor_m),
			(0.0 if w == null else w.air_m),
			(0 if w == null else w.off),
			(0.0 if w == null else w.s),
			(0.0 if w == null or w.reached > 1e29 else w.reached),
			(0 if w == null else w.frame),
			(1 if w == null or w.steer else 0),
			(("-" if w == null else w.note).replace(" ", "_"))])
	quit(0)


## A WALL-CLOCK CAP, because a headless test that never ends costs a session
## rather than failing. `Walker` has a frame cap of its own derived from the
## route; this fires if the tree itself never gets there.
var _ticks := 0


func _process(_delta: float) -> bool:
	_ticks += 1
	if _ticks > 120000:
		verdict_with("the tree's own tick cap")
		return true
	return false


# ===========================================================================
# Plumbing
# ===========================================================================

func _read(path: String) -> Dictionary:
	if path == "" or not FileAccess.file_exists(path):
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var d = JSON.parse_string(f.get_as_text())
	f.close()
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _glb(path: String) -> Node:
	if not FileAccess.file_exists(path):
		return null
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	if doc.append_from_file(path, st) != OK:
		return null
	return doc.generate_scene(st)


func _meshes(n: Node, out: Array = []) -> Array:
	if n is MeshInstance3D:
		out.append(n)
	for c in n.get_children():
		_meshes(c, out)
	return out


func _tri_count(m: Mesh) -> int:
	var t := 0
	for s in range(m.get_surface_count()):
		var arr := m.surface_get_arrays(s)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		if idx != null and idx.size() > 0:
			t += idx.size() / 3
		else:
			t += (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	return t
