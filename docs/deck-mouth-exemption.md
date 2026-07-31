# The change `station/deck.py` needs before a docking bay can be composed

Written in session 4a by the agent that closed the composed shells. `deck.py` was
not that agent's to edit, so the change is stated here in full rather than made.

## What is blocked

`station/bespoke.py`'s `NOT_COMPOSED` still holds back `docking_bay`. The reason it
was held back is gone — the shell went from **151 open boundary edges to 31** — but
the 31 that remain will still fail `deck._selftest`'s watertightness assertion, and
they are **correct content**: they are the bay's mouth, which opens on vacuum and is
how a Starfury gets in.

Composing the bay today therefore trades one true statement ("the deck is watertight")
for another ("a player can walk into a docking bay"), and neither should be given up.

## What the exemption must NOT be

A tolerance. `assert open_edges < 40` would pass a bay with a hole in its roof, and
would silently absorb the next module that regresses. The whole point of the 3,693
→ 31 work is that a declared hole is still a hole; an exemption that cannot tell an
opening from a hole re-opens exactly the door that was just shut.

## What it should be

The same test `station/aperture.py` already applies to the hull, and the same one
`docking_bay._selftest` now applies to itself: **an opening is a single closed loop
whose every vertex has degree exactly 2.** Anything else is a hole.

Concretely, in `deck.py`, beside the existing watertightness check:

```python
# APERTURES A ROOM DECLARES, which are content rather than defects. A docking
# bay's mouth opens on vacuum; a bay with no mouth is a garage. The exemption
# is not a tolerance -- `assert open < 40` would pass a hole in the roof --
# it is `aperture.py`'s rule: an OPENING is one closed loop with every vertex
# of degree exactly 2, and every edge of it must lie in the plane the room
# nominated. Anything else is still a failure.
def _declared_apertures(place, verts, tris):
    """(unexplained_open_edges, [described apertures]) for one composed room."""
    mod = place.get("module")
    want = _bespoke.SHELL_APERTURES.get(mod)
    op, _nm = _it_kit.boundary_edges(verts, tris)
    if not want:
        return op, []
    described = []
    for plane_fn, label in want:
        loop = [e for e in op if plane_fn(e[0]) and plane_fn(e[1])]
        if not loop:
            continue
        deg = {}
        for a, b in loop:
            deg[a] = deg.get(a, 0) + 1
            deg[b] = deg.get(b, 0) + 1
        if not all(d == 2 for d in deg.values()):
            continue                     # not a loop -- leave it unexplained
        adj = {}
        for a, b in loop:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        start = loop[0][0]
        seen, cur, prev = {start}, adj[start][0], start
        while cur != start:
            seen.add(cur)
            nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
            prev, cur = cur, nxt
        if len(seen) != len(deg):
            continue                     # two coplanar openings, not one
        described.append((label, len(loop)))
        op = [e for e in op if e not in set(loop)]
    return op, described
```

and the assertion becomes

```python
    unexplained, apertures = _declared_apertures(place, verts, tris)
    check("the deck is watertight once its declared apertures are set aside",
          not unexplained,
          f"{len(unexplained)} open edges that are not a declared aperture, "
          f"first at {unexplained[:1]}; declared: {apertures}")
```

`plane_fn` has to be evaluated **in the composed frame**, after the room has been
placed on the ring, so it cannot be a bare `z == 0` test written in `bespoke.py`.
The cheapest correct form is a predicate built at composition time from the room's
own transform — the same transform `room_shell` already applies.

## The registry it reads

`bespoke.py` should grow, next to `SHELL_OPEN_EDGES`:

```python
# Openings a module declares, as (local-frame plane test, label). NOT holes:
# each is asserted to be one closed degree-2 loop by the module's own selftest
# and again by `deck.py` at composition. Adding an entry here is a claim that
# something is meant to be open, and the loop test is what stops that claim
# being a way to hide a hole.
SHELL_APERTURES = {
    "docking_bay": [(lambda p: abs(p[2]) < 1e-6, "the bay mouth, on vacuum")],
}
```

That entry is deliberately not added yet: a registry with no consumer is the
`station/npc/` failure mode this project has already paid for twice. Add it in the
same change that teaches `deck.py` to read it.

## A SECOND THING FOR WHOEVER OWNS `deck.py`: green/0/0 has never been walkable

Found while verifying this session's closure work, and **it is not caused by it** —
the A/B is below and both halves were run.

```
python3 station/walkable.py --deck green/0/0 --deck-only
  FAIL  deck green/0/0  dropped 0.57 m from a spawn 50 mm above the shell
        -- the floor is not where it says
```

That is the verdict at HEAD **and** at `b9aa9a4`, this session's parent, with
`station/` checked out wholesale at each — same failure, same 0.57 m, to the
centimetre. `red/0/0` and `blue/0/0` both PASS at HEAD.

What is known about it:

* `deck.build_deck` spawns at `C.stand_at(cmeta, here[0]["angle_deg"])`, and
  `here[0]` on green/0/0 is `council_chamber` at angle 0.0 — so the body is put
  at the **corridor's** floor radius on the **chamber's** bearing.
* The chamber's own alignment is not the cause: `bespoke.floor_y` returns 0.000
  for it, `dressable_extent` 22.0 × 22.0 m, and `room_shell` places its floor
  band at y = 0 exactly. All three are unchanged by this session's rebuild.
* `room_shell_for` sizes a composed room's collision from `rooms.room_extent_m`
  and `rooms.bay_span_m`, **not** from the module's mesh, so no change to
  `council_chamber.py` can move that shell at all.

So the discrepancy is between the corridor shell's `floor_r_m` and whatever the
body actually lands on at that bearing. `blue/0/0` and `red/0/0` do not show it,
which suggests something specific to this cluster's geometry rather than to the
shell in general. It needs someone who owns `collision.py` and `deck.py`.

**It is worth treating as a real defect and not a gate quirk**: 0.57 m is
three times `MAX_DECK_DROP_M` and a player spawning on that deck falls half a
metre before they can move.

## What to check afterwards

1. `python3 station/docking_bay.py` — 35/35, including the mouth-loop assertions.
2. `python3 station/deck.py --selftest` on `blue/0/0`, which is where the bays are.
3. `python3 station/walkable.py --deck blue/0/0 --deck-only` — a body must still
   walk. The bay's ledges now climb toward the hull (INV-170), so the clear deck
   between them is 21.6 m wide where it used to be the full 42 m; the walk gate
   reports metres traversed and will say whether that matters.
4. `python3 station/bespoke.py` — the closure debt line must still read 31.
