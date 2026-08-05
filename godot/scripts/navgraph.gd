extends Node
## THE STATION'S CIRCULATION GRAPH, IN THE ENGINE.
##
## WHAT THIS ENDS. `station/routes.py` is the authority on what connects to what
## -- 96 z-cluster nodes, 249 edges, one foot-connected component -- and
## `station/route_walk.py` lays the waypoints that cross each edge. Both are
## Python, both run offline, and **the engine could not ask either of them
## anything**. `docs/MASTER-PLAN.md` §A0 records the consequence in four words:
## *zero `Navigation*` in godot/*. Every route this project has ever walked was
## chosen in Python, written into a manifest, and played back -- so an inhabitant
## could follow a route and could not CHOOSE one, and a player asking "how do I
## get to the Zocalo" had nothing to ask.
##
## WHAT IT IS, AND WHAT IT DELIBERATELY IS NOT.
##
## It is a **baked node/edge graph read at runtime**, not a Godot
## `NavigationServer3D` navmesh. The trade is stated here rather than left to be
## rediscovered:
##
##   * The station is 11,248 m of geometry across 90 z-clusters and it STREAMS --
##     `stream.gd` keeps three cells resident and frees the rest. A
##     `NavigationRegion3D` can only path over geometry that exists, so a navmesh
##     built from the resident set answers "no route" for everywhere the player
##     is not, which is the whole station. A graph that is DATA is unaffected by
##     what is in the tree, and `--nav-stream` below proves that rather than
##     asserting it.
##   * "Up" in a ring corridor is radially inward, so it is a different vector at
##     every angle -- `npc/navigation.nav_from_ring_mesh` says so in as many
##     words. One navmesh region over a ring deck would classify the far side of
##     its own arc as a wall; doing it properly is one rotated region per cell
##     plus a `NavigationLink3D` at every seam, which is more machinery than this
##     and still cannot price a lift.
##   * A lift is a **wait**, not a distance. `npc/navigation.py` prices boarding
##     at half a headway plus half a dwell in both directions. That is a cost
##     model, and a navmesh has nowhere to put it.
##   * CLAUDE.md's own architecture: *"Heavy content generation happens offline
##     in Python -- schema -> meshes, collision, navmesh -- deterministic and
##     unit-testable without an engine at all. The runtime consumes committed
##     data."* This is that rule applied to routing.
##
## WHAT WOULD MAKE ME PICK THE OTHER ONE. Local avoidance between moving bodies,
## and pathing round furniture that MOVES. Neither is a station-scale question:
## `station/roomnav.py` already solves the static furniture case offline and this
## graph stops at a room's door on purpose. The day two hundred people have to
## flow round each other in one concourse, `NavigationServer3D` with
## `NavigationAgent3D` avoidance is the right tool for the last thirty metres --
## underneath this graph, not instead of it.
##
## NOTHING HERE DECIDES WHAT CONNECTS TO WHAT. Every node, every edge and every
## waypoint arrives in `station/generated/navgraph.json`, which
## `station/navgraph_export.py` writes by calling `routes.clusters()`,
## `routes.edges()` and `route_walk.endpoints()` -- the functions that own those
## answers. This file searches and concatenates. That is the whole of hard rule 4
## applied to circulation: there is one graph and the engine reads it.
##
## USE IT:
##
##     var nav := preload("res://scripts/navgraph.gd").new()
##     nav.load_graph("/abs/path/station/generated/navgraph.json")
##     var a := nav.node_of_place("qtr_civilian")
##     var b := nav.node_of_place("business_center")
##     var hops := nav.path(a, b)                      # PackedInt32Array of nodes
##     var pts := nav.route_points("qtr_civilian", "business_center")
##
## ITS OWN GATE:
##
##     python3 station/navgraph_export.py --gate

# ---------------------------------------------------------------------------
# The graph, as loaded
# ---------------------------------------------------------------------------

## One dictionary per node, in the exporter's order. `kind` is
## `cluster` | `spine` | `column`, matching `routes.py`'s own node vocabulary.
var nodes: Array = []
## One dictionary per edge: {a, b, kind, length_m, built, why}. `kind` is
## `ring` | `axial` | `lift` | `spoke` | `trunk`, which is `routes.edges`' own.
var edges: Array = []
## Node index -> PackedInt32Array of edge indices, in the exporter's edge order.
## The order matters: it is what makes this search return the SAME path
## `route_walk.path_between` returns rather than merely a path of the same length.
var _adj: Array = []
var _by_id := {}
var _by_place := {}
var _pos := PackedVector3Array()
## Edges whose two ends are the same node -- `routes.py`'s `axial` self-loop,
## which is not a step between nodes but the corridor a node stands on.
var _self := {}

var loaded := false
var why := ""
var digest := ""
var built_from := ""

## Searches run since load. The gate reads it: a search count that did not move
## is a graph nobody asked anything, which is exactly the state this file ends.
var searches := 0
var search_us := 0.0


func load_graph(path: String) -> bool:
	loaded = false
	why = ""
	nodes = []
	edges = []
	_adj = []
	_by_id = {}
	_by_place = {}
	_self = {}
	_pos = PackedVector3Array()
	if path == "":
		why = "no navgraph path given"
		return false
	if not FileAccess.file_exists(path):
		why = "no graph at %s -- run `python3 station/navgraph_export.py --write`" % path
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		why = "could not open %s" % path
		return false
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		why = "%s is not a JSON object" % path
		return false
	var d: Dictionary = parsed
	if String(d.get("kind", "")) != "navgraph":
		why = "%s is not a navgraph (kind=%s)" % [path, String(d.get("kind", ""))]
		return false
	nodes = d.get("nodes", [])
	edges = d.get("edges", [])
	digest = String(d.get("digest", ""))
	built_from = String(d.get("built_from", ""))
	if nodes.is_empty() or edges.is_empty():
		why = "%s carries %d nodes and %d edges" % [path, nodes.size(), edges.size()]
		return false

	for i in range(nodes.size()):
		var n: Dictionary = nodes[i]
		_by_id[String(n.get("id", ""))] = i
		var p: Array = n.get("pos", [0.0, 0.0, 0.0])
		_pos.append(Vector3(float(p[0]), float(p[1]), float(p[2])))
		for k in (n.get("places", []) as Array):
			_by_place[String(k)] = i
	rebuild()
	loaded = true
	return true


## Build the adjacency from the edge list's `built` flags.
##
## SEPARATE FROM `load_graph` SO THE NEGATIVE CONTROL CAN REACH IT. "What
## happens with no lift edges" has to be asked the way `routes.py` would answer
## it if the generator did not exist -- by that module's own `built` flag,
## through this same index build. A control that reached round the adjacency and
## deleted entries would be testing a different graph from the one that ships.
func rebuild() -> void:
	_adj = []
	_adj.resize(nodes.size())
	_self = {}
	for i in range(nodes.size()):
		_adj[i] = PackedInt32Array()
	for e in range(edges.size()):
		var ed: Dictionary = edges[e]
		if not bool(ed.get("built", true)):
			continue
		var a := int(ed["a"])
		var b := int(ed["b"])
		if a == b:
			# `routes.py`'s `axial` edge is a self-loop: the spine IS the axial
			# corridor, so PASSING THROUGH the node is what traverses it. Kept
			# out of the adjacency for the same reason `path_between` keeps it
			# out -- it is not a step to a different place -- and re-inserted as
			# a leg by `route_legs` below.
			_self[a] = e
			continue
		# READ, APPEND, WRITE BACK -- AND THE FIRST VERSION DID NOT, which cost
		# an hour and is worth a line here because it fails SILENTLY. A
		# `PackedInt32Array` is a VALUE in GDScript, so `_adj[a].append(e)`
		# appends to a temporary copy and throws it away: the graph loaded, every
		# id resolved, `_self` filled correctly because a Dictionary IS a
		# reference -- and the adjacency was empty, so every one of 741 searches
		# returned "no route" with no error anywhere. The tell was `selfloops=71,
		# adjacency entries=0` in the same print.
		var la: PackedInt32Array = _adj[a]
		la.append(e)
		_adj[a] = la
		var lb: PackedInt32Array = _adj[b]
		lb.append(e)
		_adj[b] = lb


func node_count() -> int:
	return nodes.size()


func edge_count() -> int:
	return edges.size()


func node_of(id: String) -> int:
	return int(_by_id.get(id, -1))


## The node a named place stands on. A PLACE IS NOT A NODE IN THIS GRAPH and
## that is `routes.py`'s finding restated: two places in one z-cluster are
## already joined by the ring corridor that serves them, so making the cluster
## the node is what stops the graph flattering itself. A place is a label on one.
func node_of_place(key: String) -> int:
	return int(_by_place.get(key, -1))


func places_on(i: int) -> Array:
	if i < 0 or i >= nodes.size():
		return []
	return (nodes[i] as Dictionary).get("places", [])


func node_pos(i: int) -> Vector3:
	return _pos[i] if i >= 0 and i < _pos.size() else Vector3.ZERO


## The nearest node to a point in station space, optionally of one kind.
##
## NO RAYCAST, NO SCENE LOOKUP, NO RESIDENCY TEST -- and that is the streaming
## property, stated as an implementation. This reads `_pos`, which came out of
## the JSON, so the answer is the same whether three cells are resident or
## nine hundred. A version of this that asked the tree "which cell is this?"
## would return -1 for every point the player is not standing in, which is the
## whole station; `--nav-stream` runs exactly that as its control.
func nearest_node(p: Vector3, kind: String = "") -> int:
	var best := -1
	var best_d := INF
	for i in range(_pos.size()):
		if kind != "" and String((nodes[i] as Dictionary).get("kind", "")) != kind:
			continue
		var d := _pos[i].distance_squared_to(p)
		if d < best_d:
			best_d = d
			best = i
	return best


# ---------------------------------------------------------------------------
# THE SEARCH
# ---------------------------------------------------------------------------

## Shortest path in HOPS, as node indices, or an empty array if there is none.
##
## BREADTH FIRST, IN THE EXPORTER'S EDGE ORDER, BECAUSE THE ANSWER HAS TO BE THE
## AUTHORITY'S ANSWER. `route_walk.path_between` is a BFS over `routes.edges()`
## in the order that function returns them; this is the same search over the same
## list, so the two do not merely agree on how long a route is, they return the
## same route. `navgraph_export.py --gate` asserts that node for node over all
## 741 routable pairs -- an agreement of shape, not of summary statistic, and the
## only check that can catch a graph which has been quietly re-derived here.
func path(a: int, b: int) -> PackedInt32Array:
	var out := PackedInt32Array()
	if not loaded or a < 0 or b < 0 or a >= nodes.size() or b >= nodes.size():
		return out
	var t0 := Time.get_ticks_usec()
	searches += 1
	var prev := PackedInt32Array()
	prev.resize(nodes.size())
	prev.fill(-2)                      # -2 unseen, -1 the start
	prev[a] = -1
	var q := PackedInt32Array([a])
	var head := 0
	while head < q.size():
		var cur := q[head]
		head += 1
		if cur == b:
			break
		for e in (_adj[cur] as PackedInt32Array):
			var ed: Dictionary = edges[e]
			var nxt := int(ed["b"]) if int(ed["a"]) == cur else int(ed["a"])
			if prev[nxt] == -2:
				prev[nxt] = cur
				q.append(nxt)
	search_us += float(Time.get_ticks_usec() - t0)
	if prev[b] == -2:
		return out
	var seq := PackedInt32Array()
	var c := b
	while c != -1:
		seq.append(c)
		c = prev[c]
	seq.reverse()
	return seq


## The same search weighted by metres instead of hops.
##
## KEPT SEPARATE AND NOT MADE THE DEFAULT, deliberately. `routes.py` carries a
## real `length_m` on its `trunk` edges and 0.0 on the rest, because that module
## answers "does this connect" and not "how far"; the metres this walks are the
## ones `navgraph_export.py` measured off `route_walk`'s own waypoints, which
## exist for 39 of the 96 clusters. So a weighted search is a BETTER route where
## the geometry is built and a DIFFERENT one where it is not, and a gate that
## compared it against the Python authority would be comparing two questions.
## When every cluster carries waypoints this becomes the default and the gate
## moves with it.
func path_weighted(a: int, b: int) -> PackedInt32Array:
	var out := PackedInt32Array()
	if not loaded or a < 0 or b < 0 or a >= nodes.size() or b >= nodes.size():
		return out
	var t0 := Time.get_ticks_usec()
	searches += 1
	var n := nodes.size()
	var dist := PackedFloat64Array()
	dist.resize(n)
	dist.fill(INF)
	var prev := PackedInt32Array()
	prev.resize(n)
	prev.fill(-2)
	var done := PackedByteArray()
	done.resize(n)
	done.fill(0)
	dist[a] = 0.0
	prev[a] = -1
	# LINEAR SCAN RATHER THAN A HEAP, AND THE SIZE IS WHY. This graph is ~230
	# nodes, so the scan is ~53,000 float compares -- tens of microseconds, once
	# per replan, against 2,500 agents replanning eight times a station-day
	# (`npc/navigation.PLAN_BUDGET`). A heap is the right answer at ten thousand
	# nodes and is not needed at two hundred; saying so beats writing one that
	# is never exercised.
	while true:
		var u := -1
		var bd := INF
		for i in range(n):
			if done[i] == 0 and dist[i] < bd:
				bd = dist[i]
				u = i
		if u < 0 or u == b:
			break
		done[u] = 1
		for e in (_adj[u] as PackedInt32Array):
			var ed: Dictionary = edges[e]
			var v := int(ed["b"]) if int(ed["a"]) == u else int(ed["a"])
			var w := maxf(0.0, float(ed.get("length_m", 0.0)))
			if dist[u] + w < dist[v]:
				dist[v] = dist[u] + w
				prev[v] = u
	search_us += float(Time.get_ticks_usec() - t0)
	if prev[b] == -2:
		return out
	var seq := PackedInt32Array()
	var c := b
	while c != -1:
		seq.append(c)
		c = prev[c]
	seq.reverse()
	return seq


## The path as LEGS, which is what a body walks: every edge crossed, plus the
## `axial` self-loop of any node passed through.
##
## THE SELF-LOOP INSERTION IS `route_walk.path_between`'s RULE, not a new one:
## *"the `axial` edge is a self-loop on a spine node -- the spine IS the axial
## corridor -- so passing through a spine node is what traverses it, and that
## leg is inserted where the path enters one."*
func route_legs(a: int, b: int) -> Array:
	var seq := path(a, b)
	var out: Array = []
	if seq.size() < 2:
		return out
	for i in range(seq.size() - 1):
		var u := seq[i]
		var v := seq[i + 1]
		var found := -1
		for e in (_adj[u] as PackedInt32Array):
			var ed: Dictionary = edges[e]
			if int(ed["a"]) == v or int(ed["b"]) == v:
				found = e
				break
		if found < 0:
			return []
		out.append({"edge": found, "kind": String((edges[found] as Dictionary)["kind"]),
			"a": u, "b": v})
		if _self.has(v):
			var se := int(_self[v])
			out.append({"edge": se, "kind": String((edges[se] as Dictionary)["kind"]),
				"a": v, "b": v})
	return out


# ---------------------------------------------------------------------------
# THE WAYPOINTS
# ---------------------------------------------------------------------------

## The floor polyline from one named place to another, in station space.
##
## NOT ONE POINT OF IT IS COMPUTED HERE. Each z-cluster carries its own two legs
## in the artefact -- the ring arc from a place's door to the deck's spine, and
## the axial run from that junction to the transit column's lobby -- and each was
## laid by `route_walk._arc_points` and `route_walk._line_points`, at
## `route_walk.RING_STEP_DEG`'s sagitta and `route_walk.door_tol_m`'s doorway
## discipline. This walks the route the search returned and concatenates them,
## forwards on the way out and reversed on the way in.
##
## IT STOPS AT THE ROOM'S DOOR, ON PURPOSE. Crossing a room past its furniture is
## `station/roomnav.py`'s question and it is answered against that room's own
## emitted mesh; a straight line from a doorway to a register's centre is the
## defect that stopped the L3 commute 5.59 m from its post and was written up
## twice as a lift fault. This graph is circulation. `commute_points` below keeps
## the room legs it is given and replaces only what this graph owns.
##
## A RIDE HAS NO POLYLINE. Nobody walks a lift shaft, and a 21.6 m radial jump
## laid as a polyline is a route through the floor -- `life.gd`'s Commuter drives
## the car from `transit.gd` and the points stop and restart either side of it.
## `route_points` therefore returns the WALKABLE runs, in order, as an Array of
## PackedVector3Array -- one per uninterrupted walk.
func route_runs(from_place: String, to_place: String) -> Array:
	var a := node_of_place(from_place)
	var b := node_of_place(to_place)
	var runs: Array = []
	if a < 0 or b < 0 or a == b:
		return runs
	var seq: PackedInt32Array = path(a, b)
	if seq.size() < 2:
		return runs

	var cur := PackedVector3Array()
	for i in range(seq.size()):
		var idx := seq[i]
		var nd: Dictionary = nodes[idx]
		var kind := String(nd.get("kind", ""))
		if kind == "cluster":
			# THE RING ARC ONLY -- from the place's own door round to the deck's
			# transit angle. Everything past the junction belongs to the spine,
			# because which way you step onto it depends on where you are going:
			# see `navgraph_export.graph`'s note on the aim point.
			var first := i == 0
			var place := from_place if first else to_place
			if first:
				_add(cur, _leg_points(idx, place, "ring"))
			else:
				_add(cur, _reversed(_leg_points(idx, place, "ring")))
		elif kind == "spine":
			# THE SPINE IS A CORRIDOR AND NOT A POINT, which is exactly why
			# `routes.py` models it as a self-loop. What crosses it depends on
			# what is either side, and every one of these runs was laid by
			# `route_walk._line_points` in the exporter -- none of them is
			# interpolated here.
			var prev: int = seq[i - 1] if i > 0 else -1
			var nxt: int = seq[i + 1] if i + 1 < seq.size() else -1
			var pk := "" if prev < 0 else String((nodes[prev] as Dictionary).get("kind", ""))
			var nk := "" if nxt < 0 else String((nodes[nxt] as Dictionary).get("kind", ""))
			if pk == "cluster" and nk == "cluster":
				var tbl: Dictionary = nd.get("runs", {})
				var key := "%s|%s" % [String((nodes[prev] as Dictionary)["id"]),
					String((nodes[nxt] as Dictionary)["id"])]
				_add(cur, _v3s(tbl.get(key, [])))
			elif pk == "cluster" and nk == "column":
				_add(cur, _v3s((nodes[prev] as Dictionary).get("lobby_run", [])))
			elif pk == "column" and nk == "cluster":
				_add(cur, _reversed(_v3s(
					(nodes[nxt] as Dictionary).get("lobby_run", []))))
		else:
			# column: a RIDE. Nobody walks a lift shaft, and a 21.6 m radial jump
			# laid as a polyline is a route through the floor. Close the run.
			if cur.size() > 1:
				runs.append(cur)
			cur = PackedVector3Array()
	if cur.size() > 1:
		runs.append(cur)
	return runs


func route_points(from_place: String, to_place: String) -> PackedVector3Array:
	var out := PackedVector3Array()
	for r in route_runs(from_place, to_place):
		for p in (r as PackedVector3Array):
			out.append(p)
	return out


func _leg_points(i: int, place: String, which: String) -> PackedVector3Array:
	var nd: Dictionary = nodes[i]
	var legs: Dictionary = nd.get("legs", {})
	if not legs.has(place):
		return PackedVector3Array()
	return _v3s((legs[place] as Dictionary).get(which, []))


func _v3s(raw: Array) -> PackedVector3Array:
	var out := PackedVector3Array()
	for p in raw:
		out.append(Vector3(float(p[0]), float(p[1]), float(p[2])))
	return out


func _reversed(v: PackedVector3Array) -> PackedVector3Array:
	var out := v.duplicate()
	out.reverse()
	return out


## Append, dropping a point that repeats the one before it. Every leg starts
## where the last one ended -- the junction is the last point of the ring arc and
## the first of the axial run -- so without this a route carries a zero-length
## segment at every seam and `advance` divides by it.
func _add(cur: PackedVector3Array, add: PackedVector3Array) -> void:
	for p in add:
		if cur.is_empty() or cur[cur.size() - 1].distance_squared_to(p) > 1e-8:
			cur.append(p)
