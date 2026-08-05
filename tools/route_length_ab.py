#!/usr/bin/env python3
"""Would real edge lengths change any route? Measure before building.

`routes.py` writes `length_m: 0.0` on five of its six edge kinds and nothing
reads the field. `route_walk.path_between` is plain BFS -- fewest hops. The
question task #9 leaves open is whether metre-weighted search would pick
DIFFERENT routes, and it is cheap to answer on a 179-node graph.

This computes a real length for each edge kind from the station's own geometry,
runs Dijkstra against the existing BFS over every pair, and reports how often
they disagree and by how many metres.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
ROOT = "/home/user/Opus-5"
sys.path.insert(0, os.path.join(ROOT, "station"))

import interior as it                                            # noqa: E402
import routes as R                                               # noqa: E402
import route_walk as RW                                          # noqa: E402


def _deck_r(schema, profile, sec, ring, deck, z):
    """A deck's floor radius, with a MARKED fallback where the stack is empty.

    `decks_in_ring` returns nothing at a z where the hull taper has closed the
    ring out -- a real fact about the station, not an error. Falling back
    silently would be the defect this whole exercise is about, so the caller is
    told which branch answered.
    """
    decks = it.decks_in_ring(schema, profile, sec, ring, z_m=z)
    if decks:
        return decks[min(deck, len(decks) - 1)]["floor_r_m"], "stack"
    rings = it.ring_radii(schema, profile, sec, z_m=z)
    if not rings:
        raise ValueError("no rings at z=%.0f" % z)
    rr = rings[min(ring, len(rings) - 1)]
    return rr["r_outer"], "FALLBACK: no deck stack at z=%.0f" % z


def real_length(e, nodes, schema, profile):
    """A length in metres for one edge, from the geometry the station has.

    ring   -- the arc from the cluster's own angle to the transit angle, at the
              deck's floor radius. That IS the walk.
    lift   -- the radial rise between the deck and the column's landing.
    spoke  -- the radial distance between two ring radii.
    trunk  -- already computed by routes.py as the axial gap.
    axial  -- a SELF-LOOP on a spine node. One edge cannot carry a per-pair z
              distance, so it is reported separately rather than guessed at.
    """
    k = e["kind"]
    if k == "trunk":
        return float(e["length_m"]), "routes.py already computes this"
    if k == "axial":
        return None, "self-loop: no single length exists"
    if k == "ring":
        a = e["a"]                       # (sector, ring, deck, z)
        import deck as D
        try:
            n = nodes[a]
            _h, lo, span = D.deck_arc(n["sector"], n["ring"], n["deck"], n["z"])
            hi = lo + span
            ang = R.transit_angle(a[0], nodes)
        except Exception as exc:
            return None, "arc unavailable: %s" % exc
        try:
            r, how = _deck_r(schema, profile, a[0], a[1], a[2], a[3])
        except Exception as exc:
            return None, "radius unavailable: %s" % exc
        mid = (lo + hi) / 2.0
        d = abs(((ang - mid) + 180.0) % 360.0 - 180.0)
        return math.radians(d) * r, "arc %.1f deg at r=%.1f (%s)" % (d, r, how)
    if k in ("lift", "spoke"):
        a, b = e["a"], e["b"]
        # NODE KEY SHAPES, which is what the first two attempts got wrong:
        #   cluster ("blue", 0, 0, 6880.0)          sector, ring, deck, z
        #   spine   ("spine", "blue", 0, 0)         sector, ring, deck
        #   column  ("column", "blue", 0, 6880.0)   sector, ring, z
        def _parts(node):
            if node[0] == "spine":
                return node[1], node[2], node[3], None
            if node[0] == "column":
                return node[1], node[2], 0, node[3]
            return node[0], node[1], node[2], node[3]

        def _fr(node, z_hint):
            sec, ring, deck, z = _parts(node)
            return _deck_r(schema, profile, sec, ring, deck,
                           z if z is not None else z_hint)[0]
        try:
            za, zb = _parts(a)[3], _parts(b)[3]
            hint = za if za is not None else zb
            if k == "lift":
                sec, ring, _d, _z = _parts(a)
                decks = it.decks_in_ring(schema, profile, sec, ring, z_m=hint)
                rs = [dd["floor_r_m"] for dd in decks]
                return abs(max(rs) - min(rs)), "rise over %d decks" % len(rs)
            return abs(_fr(a, hint) - _fr(b, hint)), "spoke between rings"
        except Exception as exc:
            return None, "radii unavailable: %s" % exc
    return None, "unknown kind"


def dijkstra(adj, w, a, b):
    import heapq
    dist = {a: 0.0}
    prev = {a: None}
    q = [(0.0, a)]
    seen = set()
    while q:
        d, cur = heapq.heappop(q)
        if cur in seen:
            continue
        seen.add(cur)
        if cur == b:
            break
        for nxt in adj.get(cur, ()):
            nd = d + w.get((cur, nxt), 0.0)
            if nxt not in dist or nd < dist[nxt] - 1e-9:
                dist[nxt] = nd
                prev[nxt] = cur
                heapq.heappush(q, (nd, nxt))
    if b not in dist:
        return None, None
    seq, cur = [], b
    while cur is not None:
        seq.append(cur)
        cur = prev[cur]
    seq.reverse()
    return seq, dist[b]


def bfs(adj, a, b):
    prev = {a: None}
    q = [a]
    while q:
        cur = q.pop(0)
        if cur == b:
            break
        for nxt in adj.get(cur, ()):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    if b not in prev:
        return None
    seq, cur = [], b
    while cur is not None:
        seq.append(cur)
        cur = prev[cur]
    seq.reverse()
    return seq


def main():
    schema, profile = R.station()      # the RESOLVED pair -- see routes.station's
                                       # own table: asking any other way gives a
                                       # different graph (71 components vs 1)
    nodes = R.clusters()
    es = R.edges(nodes, schema, profile=profile)
    print("graph: %d nodes, %d edges" % (len(nodes), len(es)))

    # Real lengths, and how many we could compute
    lens, why, unknown = {}, {}, {}
    for i, e in enumerate(es):
        if not e["built"]:
            continue
        L, note = real_length(e, nodes, schema, profile)
        key = (e["a"], e["b"])
        if L is None:
            unknown.setdefault(e["kind"], []).append(note)
        else:
            lens[key] = L
            lens[(e["b"], e["a"])] = L
        why.setdefault(e["kind"], note)

    by_kind = {}
    for e in es:
        if not e["built"]:
            continue
        k = e["kind"]
        L = lens.get((e["a"], e["b"]))
        by_kind.setdefault(k, []).append(L)
    print("\nreal length by edge kind:")
    for k in sorted(by_kind):
        vals = [v for v in by_kind[k] if v is not None]
        n = len(by_kind[k])
        if vals:
            print("  %-6s %3d edges  min %8.1f  median %8.1f  max %8.1f m"
                  % (k, n, min(vals), sorted(vals)[len(vals) // 2], max(vals)))
        else:
            print("  %-6s %3d edges  NO LENGTH -- %s" % (k, n, why.get(k, "")))

    built = [e for e in es if e["built"] and e["a"] != e["b"]]
    priced = sum(1 for e in built if (e["a"], e["b"]) in lens)
    print("\npriced %d of %d traversable edges" % (priced, len(built)))
    if priced < len(built):
        print("REFUSING TO COMPARE. Dijkstra with missing weights degenerates to")
        print("BFS, and would report '0 different' for the same reason the")
        print("original A/B did -- two identical algorithms. Fix the %d unpriced"
              % (len(built) - priced))
        print("edges first.")
        for k, notes in sorted(unknown.items()):
            print("  %-6s %3d unpriced -- %s" % (k, len(notes), notes[0]))
        return 1

    adj = {}
    for e in es:
        if not e["built"] or e["a"] == e["b"]:
            continue
        adj.setdefault(e["a"], []).append(e["b"])
        adj.setdefault(e["b"], []).append(e["a"])

    keys = sorted(nodes)
    pairs = [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]]
    same, differ, hops_worse, m_saved = 0, 0, 0, []
    unreach = 0
    for a, b in pairs:
        pb = bfs(adj, a, b)
        pd, dcost = dijkstra(adj, adj and lens, a, b)
        if pb is None or pd is None:
            unreach += 1
            continue
        if pb == pd:
            same += 1
            continue
        differ += 1
        bcost = sum(lens.get((pb[i], pb[i + 1]), 0.0) for i in range(len(pb) - 1))
        if bcost > dcost + 1e-6:
            hops_worse += 1
            m_saved.append(bcost - dcost)
    print("\nBFS (fewest hops) against Dijkstra (fewest metres), over %d pairs:"
          % len(pairs))
    print("  identical route      %d" % same)
    print("  different route      %d" % differ)
    print("  BFS strictly longer  %d" % hops_worse)
    if m_saved:
        m_saved.sort()
        print("  metres BFS wastes:   median %.1f  max %.1f  total %.1f"
              % (m_saved[len(m_saved) // 2], m_saved[-1], sum(m_saved)))
    print("  unreachable pairs    %d" % unreach)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
