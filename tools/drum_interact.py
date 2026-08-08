#!/usr/bin/env python3
"""DOES THE HABITAT DRUM ACTUALLY CONTAIN WHAT THE REGISTER SAYS A PLAYER MEETS?

`station/interact.py --audit` already asks that question for every place on the
station and answers **31 of 31** for the drum's twelve locations. Built through
this file's own assembly instead, the honest answer when it was written was
**9 of 31**. Both numbers are correct and they are about different objects.

THE TENTH INSTANCE OF THIS PROJECT'S SIGNATURE DEFECT, IN GATE FORM. CLAUDE.md
records nine cases of finished machinery with no caller on the shipped path, and
one sentence from session 4h that explains this one exactly: *"A thing is built
more than once in this project, and a gate on one build path says nothing about
the other."* `interact.resolve_place` builds through `deck.room_geometry`, which
for an open drum place falls back to `rooms.build` -- a corridor-fed enclosed bay
with `prop_bench`, `prop_path` and `prop_pool_edge` in it. That bay is real, it
resolves everything it declares, and **the drum does not ship it**.
`tools/export_drum.py` says so in its own header: only `bespoke.NEAR_END` modules
are composed as rooms, because *"dropping a sealed grey bay onto the Garden's
lawn is worse than leaving the lawn"*. So `--audit` scored a room nobody can
stand in, and the deck that ships had twenty-two declared interactables with no
object behind them.

That is why this gate exists in `tools/` beside the exporter rather than as a
flag on `interact.py`: **a gate belongs to the thing that builds the artefact.**

WHAT IT ASSEMBLES, AND WHY IT IMPORTS RATHER THAN RESTATES. Every part, the
place-attribution rule, the tram substitution and the uniform dressing come from
`export_drum` itself -- `place_boxes`, `_finder`, `attribute`, `PART_PLACE`,
`uniform_dressing`, `drum_rooms`, `_merge`. A second copy of that list is this
repository's oldest defect in a new costume, and it is the copy that would drift
first: a part added to the exporter and not here would be a group the gate cannot
see, which is precisely the blindness being fixed.

The resolution itself is `interact.resolve`, the function `interact.sidecar`
calls to write `green_1_0_interact.json`. Not a reimplementation of it: if this
file decided for itself what resolves, it could pass while the shipped sidecar
was empty.

Run: python3 tools/drum_interact.py              # the shipped ground, ~2.5 min
     python3 tools/drum_interact.py --fast-ground # the eye-LOD ground, ~30 s
     python3 tools/drum_interact.py --control     # prove the gate can fail
     python3 tools/drum_interact.py --vs-audit    # both build paths, side by side
"""
import argparse
import collections
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import directory as dr                                            # noqa: E402
import drum_ground as dg                                          # noqa: E402
import drum_walk as DW                                            # noqa: E402
import export_drum as ED                                          # noqa: E402
import interact as IX                                             # noqa: E402


def assemble(fast_ground=False, no_rooms=False):
    """The drum's render mesh, exactly as `export_drum.main` composes it.

    `fast_ground` keeps `export_scene.drum_parts`' eye-LOD ground (46,172 tri)
    instead of rebuilding all 280 patches at the shipped stride (573,440 tri).
    It is an APPROXIMATION AND IT IS CHECKED: `--ground-control` runs both and
    asserts they resolve identically, because the ground is the one part whose
    group names (`ground_road`, `ground_avenue`, `ground_shore`, ...) could in
    principle alias a declared token and nobody should take that on trust.

    `no_rooms` drops the two composed interiors -- the control that shows this
    gate can fail, since Earhart's and Fresh Air are the only drum places that
    resolve everything they declare.
    """
    import export_scene as ES                                     # noqa: PLC0415
    import tram as _tram                                          # noqa: PLC0415

    schema, profile, sector = DW.drum()
    boxes = ED.place_boxes(dg.FLOOR_R)
    at = ED._finder(boxes)
    eye = (0.0, -(dg.FLOOR_R - 2.0), (dg.Z0 + dg.Z1) / 2.0)
    parts = [(n, v, t, list(g))
             for n, v, t, g in ES.drum_parts(schema, profile, sector, eye)]
    by = {n: i for i, (n, _v, _t, _g) in enumerate(parts)}

    # The two substitutions `export_drum.main` makes, for its own stated
    # reasons: a static deck has no eye, and a shell has no seats.
    tv, tt, tm = _tram.drum_trams(schema, profile, sector, per_guideway=2,
                                  interior=True, glazed=True)
    parts[by["trams"]] = ("trams", tv, tt, tm["groups"])
    dv, dt, dgn, _meta = ED.uniform_dressing()
    parts[by["dressing"]] = ("dressing", dv, dt, dgn)
    if not fast_ground:
        gv, gt, gg = ED.full_ground(DW.collision_stride()[0])
        parts[by["ground"]] = ("ground", gv, gt, gg)

    rooms_built = []
    if not no_rooms:
        rparts, _actors, rooms_built = ED.drum_rooms(schema, profile, boxes)
        parts.extend((f"room_{k}", v, t, g) for k, v, t, g in rparts)

    named = []
    for n, v, t, g in parts:
        if n.startswith("room_"):
            named.append((n, v, t, g))
            continue
        fixed = ED.PART_PLACE.get(n)
        if fixed:
            named.append((n, v, t, [f"{fixed}{IX.PLACE_SEP}{x}" for x in g]))
            continue
        g2, _h = ED.attribute(v, t, g, at)
        named.append((n, v, t, g2))
    V, T, per = ED._merge(named)
    return boxes, V, T, DW._spans(per), per, rooms_built


def resolve_drum(boxes, spans, per):
    """Per place: what it declares, what its own mesh provides, and how.

    `IX.resolve` and nothing else -- the same call, with the same span list,
    that `interact.sidecar` makes when `export_drum` writes the deck's
    `_interact.json`. `sidecar` groups names by the `PLACE_SEP` prefix
    `attribute` puts on them; so does this.
    """
    byplace = collections.defaultdict(list)
    for nm in set(per):
        if IX.PLACE_SEP in nm:
            byplace[nm.partition(IX.PLACE_SEP)[0]].append(nm)
    decl = {p["key"]: tuple(p.get("interacts") or ()) for p in dr.PLACES}
    rows = []
    for b in sorted(boxes, key=lambda r: r["key"]):
        k = b["key"]
        want = decl.get(k, ())
        names = sorted(byplace.get(k, []))
        got = IX.resolve(want, names, spans)
        exact = IX.emitted_tokens(names)
        rows.append({
            "key": k,
            "declared": want,
            "groups": len(names),
            "resolved": tuple(t for t in want if t in got),
            # HOW, not just whether -- the distinction `resolve_place` keeps and
            # the reason the twenty-two split into two different jobs.
            "alias": {t: got[t] for t in want if t in got and t not in exact},
            "unresolved": tuple(t for t in want if t not in got),
            "near": {t: IX.near_miss(t, names)[:3] for t in want
                     if t not in got and IX.near_miss(t, names)},
            "verbs": {t: IX.verb_of(t) for t in want},
        })
    return rows


def report(rows, title):
    d = sum(len(r["declared"]) for r in rows)
    g = sum(len(r["resolved"]) for r in rows)
    print(f"\n{title}\n")
    for r in rows:
        miss = r["unresolved"]
        print(f"  {r['key']:16s} {len(r['resolved'])}/{len(r['declared'])}"
              f"  groups {r['groups']:>4d}"
              + (f"   MISSING {', '.join(miss)}" if miss else ""))
        for t, n in sorted(r["alias"].items()):
            print(f"       {t} <- {n.partition(IX.PLACE_SEP)[2]}  "
                  f"(the generator's own word)")
        for t, near in sorted(r["near"].items()):
            print(f"       near {t}: {', '.join(x.partition(IX.PLACE_SEP)[2] for x in near)}")
    # BY VERB, because a `tread` row and an `open` row are not worth the same.
    # `godot/scripts/interact.gd::_aim` opens `if not it.pressable: continue`,
    # so an unresolved `tread` token costs the audit and costs the player
    # nothing, while an unresolved `open` is a door that is not there.
    press = collections.Counter()
    for r in rows:
        for t in r["unresolved"]:
            press["pressable" if IX.verb_of(t) in IX.PRESSABLE
                  else "tread"] += 1
    print(f"\n  {g}/{d} declared interactables resolve on the drum's OWN mesh")
    if d > g:
        print(f"  of the {d - g} that do not: {press['pressable']} are "
              f"PRESSABLE (a player would reach for them and find nothing) "
              f"and {press['tread']} are `tread` (no prompt either way)")
    return g, d


def _cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fast-ground", action="store_true",
                    help="eye-LOD ground instead of the shipped 280 patches")
    ap.add_argument("--control", action="store_true",
                    help="drop the composed rooms -- the gate must go redder")
    ap.add_argument("--ground-control", action="store_true",
                    help="assert the ground contributes no interactable")
    ap.add_argument("--vs-audit", action="store_true",
                    help="also run interact.resolve_place on the same twelve "
                         "places, so the two build paths can be compared")
    a = ap.parse_args(argv)

    t0 = time.time()
    boxes, V, T, spans, per, built = assemble(fast_ground=a.fast_ground)
    print(f"THE DRUM'S OWN MESH: {len(T):,} tri, {len(spans):,} spans, "
          f"{len(set(per)):,} names, {len(boxes)} register places "
          f"({time.time() - t0:.0f} s"
          + (", eye-LOD ground" if a.fast_ground else
             f", ground at the shipped stride {DW.collision_stride()[0]}")
          + ")")
    print(f"  composed rooms: "
          + (", ".join(f"{k} ({m}, {h})" for k, m, h in built) or "none"))
    rows = resolve_drum(boxes, spans, per)
    got, want = report(rows, "WHAT THE REGISTER DECLARES, AGAINST WHAT THE "
                             "DRUM BUILDS")

    if a.ground_control:
        # THE ONE PART TAKEN ON TRUST OTHERWISE. Both grounds, same resolution
        # or the `--fast-ground` shortcut is not a shortcut.
        b2, _V2, _T2, s2, p2, _u = assemble(fast_ground=not a.fast_ground)
        r2 = resolve_drum(b2, s2, p2)
        same = all(x["resolved"] == y["resolved"]
                   for x, y in zip(rows, r2))
        print(f"\n  GROUND CONTROL: the other ground resolves "
              f"{sum(len(r['resolved']) for r in r2)}/{want} -- "
              + ("IDENTICAL, so the ground provides no interactable"
                 if same else "DIFFERENT, the ground is load-bearing"))
        if not same:
            return 1

    if a.control:
        _b, _V, _T, s3, p3, _u = assemble(fast_ground=a.fast_ground,
                                          no_rooms=True)
        r3 = resolve_drum(_b, s3, p3)
        g3 = sum(len(r["resolved"]) for r in r3)
        print(f"\n  CONTROL: with the two composed rooms dropped the drum "
              f"resolves {g3}/{want}, not {got}. The gate moves with the "
              f"content, so it is measuring the mesh and not the register.")
        if g3 >= got:
            print("  FAIL  the control did not move -- this gate cannot fail")
            return 1

    if a.vs_audit:
        # THE COMPARISON THIS FILE EXISTS FOR. Same twelve places, the other
        # build path, `interact.py --audit`'s own function.
        import interior as it                                     # noqa: PLC0415
        schema, profile = it.load()
        keys = {b["key"] for b in boxes}
        ag = ad = 0
        print("\n  THE OTHER BUILD PATH -- interact.resolve_place, through "
              "deck.room_geometry:")
        for q in dr.PLACES:
            if q["key"] not in keys:
                continue
            try:
                r = IX.resolve_place(schema, profile, q)
            except Exception as e:                                # noqa: BLE001
                print(f"    {q['key']:16s} ERROR {type(e).__name__}")
                continue
            ag += len(r["resolved"])
            ad += len(r["declared"])
            mine = next(x for x in rows if x["key"] == q["key"])
            flag = "" if len(r["resolved"]) == len(mine["resolved"]) \
                else "   <-- THE TWO PATHS DISAGREE"
            print(f"    {q['key']:16s} audit {len(r['resolved'])}/"
                  f"{len(r['declared'])}   drum "
                  f"{len(mine['resolved'])}/{len(mine['declared'])}{flag}")
        print(f"    audit says {ag}/{ad}; the shipped drum has {got}/{want}")

    if got < want:
        print(f"\nFAIL  {want - got} of the drum's {want} declared "
              f"interactables resolve to nothing the shipped deck emits. "
              f"`interact.py --audit` does not see this: it builds these "
              f"places through deck.room_geometry, which the drum's exporter "
              f"deliberately does not use for an open place.")
        return 1
    print(f"\nPASS  every one of the drum's {want} declared interactables "
          f"resolves to a group the shipped deck actually emits.")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
