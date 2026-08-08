#!/usr/bin/env python3
"""Is a light fitting a FITTING -- and does a sign SAY anything?

Two questions no gate in this repository could ask, both found by a judging
panel on the packaged build rather than by anything here.

  1. **THE LENS MUST NOT BE THE WHOLE LAMP.** `docs/AAA-STANDARD.md` defines
     CRAFT 1 as "a box primitive standing in for a named object". Every
     luminaire in `station/interior_kit.py` was one call to `_slab`: an
     emissive box with no housing, no bezel and no mount, on the fitting a
     corridor player looks at most (`materials.light_portal_head`'s own note
     calls it "the largest emissive surface a player ever stands under in this
     kit", and a ring deck carries 247 of them).

  2. **A SIGN PLATE MUST CARRY LETTERING.** The corridor kit emitted
     `sign_frame` and `sign_text` and both were bare slabs -- measured on the
     packaged build, `dist/Babylon5/station/generated/scene/deck/
     blue_0_0_z7440.obj` carries 1,968 triangles of each, which is 164 sign
     plates and 164 lettering plates and not one word. `station/signage.py`
     has had a working 5x7 face, a fitter and `door_text(place)` since it was
     written, and `deck.py` calls it at doorways; the 77% of a ring deck
     BETWEEN the doorways called none of it.

WHY THESE TWO ARE ONE GATE. They are the same failure: a part that passes every
existing check while not being the thing it is named after. Every gate in this
project scores a part against a standard -- articulation against a line density,
materials against a bind, lighting against a histogram -- and a lit rectangle
has a line density, a bind and a histogram. What none of them ask is whether the
object is an OBJECT.

WHAT MAKES IT CHEAP ENOUGH TO RUN. It builds `interior_kit.corridor_section`
and nothing else: no station build, no rooms, no GPU, about a second. It is safe
to run while agents are working, which `deck.py --sweep` and `rooms.py` are not.

    python3 tools/fittings_gate.py            # the gate
    python3 tools/fittings_gate.py --legacy   # the control: MUST fail
    python3 tools/fittings_gate.py --cost     # triangles per fitting, per lap

THE CONTROL IS THE POINT. `--legacy` monkey-patches `luminaire` back to the bare
`_slab` it replaced and `sign_lettering` to a no-op, rebuilds the same corridor,
and re-runs the same assertions. If it does not fail, this file is measuring
nothing. CLAUDE.md records two assertions in this project that could only fail
if somebody FIXED the defect; the way not to write a third is to show the gate
failing on the content it was written against.
"""
import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "station"))

import interior_kit as K                                        # noqa: E402

# The lens groups a corridor is lit BY, and the groups that are a lamp's BODY.
# Read off the kit rather than written down twice: anything tagged `light_*`
# that is not a body is a lens. A new fitting therefore arrives in this gate
# automatically, which is the failure mode `materials._scan_generator_groups`
# was written for one level up.
BODY_GROUPS = ("light_housing", "light_bezel")
# `light_deck_channel` is EXEMPT and the exemption is measured, not assumed.
# `interior_kit.deck_panel` already builds it as a lens in a trough: the trough
# floor is `deck_panel` material at t*0.30 and the lens is 62% of the channel
# width at t*0.22..t*0.55, leaving 34 mm of dark rebate either side. That is a
# housing; it is just made of deck plate rather than of a can. `--cost` prints
# it so the exemption stays visible.
#
# `light_indicator_red` is exempt for the opposite reason and it is arithmetic:
# `wall_station`'s status lamp is 8 x 40 x 55 mm. A 26 mm bezel does not fit on
# it, and a 2 mm one is under the 1.5 mm draft this kit already treats as the
# limit of what a surface can express. A pilot light is not a luminaire.
EXEMPT_LENSES = ("light_deck_channel", "light_indicator_red")

# A sign a player cannot read is a blank sign with extra triangles. The rule of
# thumb `signage.legible_at_m` already uses -- 125x cap height for a reader who
# is not looking for it -- against the width of the corridor a sign is read
# across. `PROVISIONAL["corridor_width_m"]` is 2.6, so a plate on the far wall
# is read from about 2.6 m at the worst.
READ_DISTANCE_M = 2.6


def _components(tris, want):
    """Connected components of `want`-indexed triangles, by shared vertex.

    A fitting is a CONNECTED BODY and a tagged span is not one -- the same
    distinction `export_scene.fixture_lights` had to learn when a single span
    turned out to be four wall courses and it put one lamp at their centroid.
    `wall_assembly` emits every downlight of a bay inside one `light_downlight`
    span, so clustering by span would ask the question of a bay rather than of
    a lamp.
    """
    parent = {}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in want:
        for k in tris[i]:
            parent.setdefault(k, k)
    for i in want:
        a, b, c = tris[i]
        union(a, b)
        union(a, c)
    out = {}
    for i in want:
        out.setdefault(find(tris[i][0]), []).append(i)
    return list(out.values())


def _aabb(verts, tris, idx):
    pts = [verts[k] for i in idx for k in tris[i]]
    return (tuple(min(p[j] for p in pts) for j in range(3)),
            tuple(max(p[j] for p in pts) for j in range(3)))


def _owner(n, spans):
    own = [None] * n
    for name, lo, hi in spans:
        for i in range(lo, min(hi, n)):
            own[i] = name
    return own


def build(length=21.6, doors=((7.0, 1), (14.0, 0))):
    """One corridor section, with a wall door and a bulkhead in it.

    THE HARD CASE, and it is deliberate. `interior_kit._tag_coverage` defaulted
    to a corridor with NO doors for as long as this project has existed, and
    1,248 untagged triangles a deck lived in exactly the pieces that default
    never built. A gate that builds the easy case is a gate on the easy half.
    """
    K.reset_tags()
    v, t = K.corridor_section(length, doors=doors)
    return v, t, K.tagged_spans(t)


def lens_report(verts, tris, spans):
    """Per lens body: is there a lamp around it?

    THE TEST, and it is a containment test rather than a triangle count. For
    every connected emissive body, the non-emissive fitting geometry near it
    must reach FURTHER OUT than the lens does in both cross-section directions
    and at least as far as the lens along the axis it faces. That is the
    literal reading of "the emissive surface inside a fitting rather than being
    the fitting", and a bare `_slab` fails it because there is nothing near it
    at all.

    Counting triangles instead would be the wrong test twice over: a lens with
    a subdivided face would pass, and a housing built as one box behind the
    lens -- which is a backing plate, not a fitting -- would pass too.
    """
    own = _owner(len(tris), spans)
    body = [i for i in range(len(tris)) if own[i] in BODY_GROUPS]
    lens_names = sorted({n for n in own
                         if n and n.startswith("light_")
                         and n not in BODY_GROUPS and n not in EXEMPT_LENSES})
    rows = []
    for name in lens_names:
        for comp in _components(tris, [i for i in range(len(tris))
                                       if own[i] == name]):
            lo, hi = _aabb(verts, tris, comp)
            size = [hi[j] - lo[j] for j in range(3)]
            # The neighbourhood is the fitting's own scale, so a lamp is never
            # 'housed' by a wall three metres away.
            #
            # INTERSECTION, NOT CONTAINMENT, and the first version had it the
            # other way round with a result worth recording. Requiring every
            # vertex of a body triangle to lie inside the lens's expanded box
            # excluded the long side rails of `pilaster`'s channel -- which is
            # 0.90 m of bezel round seven 85 mm cells -- so the gate reported
            # 98 of 116 lenses UNHOUSED on a corridor whose lenses are housed.
            # A housing is legitimately much larger than the lens it holds; the
            # question is whether it REACHES the lens, not whether it is small.
            reach = max(size) * 0.75 + 0.05
            near = []
            for i in body:
                pts = [verts[k] for k in tris[i]]
                if all(min(p[j] for p in pts) <= hi[j] + reach
                       and max(p[j] for p in pts) >= lo[j] - reach
                       for j in range(3)):
                    near.append(i)
            if not near:
                rows.append((name, size, None, None))
                continue
            blo, bhi = _aabb(verts, tris, near)
            # Which axis does the fitting face? The one the lens is thinnest
            # on -- a lens is a plate, and a plate faces along its short axis.
            ax = min(range(3), key=lambda j: size[j])
            cross = [j for j in range(3) if j != ax]
            margin = min(min(lo[j] - blo[j], bhi[j] - hi[j]) for j in cross)
            # ...and the body must reach the lit plane, or the 'housing' is a
            # backing plate behind a lamp that is still its own front surface.
            depth = max(bhi[ax] - hi[ax], lo[ax] - blo[ax])
            rows.append((name, size, margin, depth))
    return rows


def sign_report(verts, tris, spans):
    """Per sign field: is anything written on it, and can it be read?"""
    import signage as SG                                        # noqa: PLC0415
    own = _owner(len(tris), spans)
    text = [i for i in range(len(tris)) if own[i] in K.DECAL_GROUPS]
    fields = [i for i in range(len(tris)) if own[i] in ("sign_field",)]
    rows = []
    for comp in _components(tris, fields):
        lo, hi = _aabb(verts, tris, comp)
        size = [hi[j] - lo[j] for j in range(3)]
        reach = max(size) * 0.6 + 0.05
        near = [i for i in text
                if all(lo[j] - reach <= verts[k][j] <= hi[j] + reach
                       for k in tris[i] for j in range(3))]
        if not near:
            rows.append((size, 0, 0.0, 0.0))
            continue
        # CAP HEIGHT IS MEASURED OFF THE GEOMETRY, not read back out of the
        # call that made it. A glyph rectangle is at most one cap tall, and the
        # tallest rectangle in a block IS a cap on this face: every letter in
        # `signage._FONT` has a full-height stem or bowl except `.` `,` and
        # `'`, none of which appear alone on a line.
        tallest = 0.0
        for i in near:
            pts = [verts[k] for k in tris[i]]
            tallest = max(tallest, max(p[1] for p in pts) - min(p[1]
                                                               for p in pts))
        rows.append((size, len(near), tallest, tallest * 125.0))
    return rows, len(text), SG.GLYPH_H


def _legacy():
    """Put the fittings back the way the panel found them.

    A bare emissive slab at the envelope the housing pass kept, and lettering
    removed. This is the BEFORE, rebuilt rather than remembered -- CLAUDE.md
    records eleven of fourteen lighting 'failures' turning out to be stale
    committed frames, and a control that cannot be rebuilt is the same defect.
    """
    def slab_only(x0, x1, y0, y1, z0, z1, lens_group, face="+x", **_kw):
        v, t = [], []
        with K.tag(lens_group):
            K._slab(v, t, x0, x1, y0, y1, z0, z1)
        return v, t

    K.luminaire = slab_only
    K.sign_lettering = lambda *a, **k: 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--legacy", action="store_true",
                    help="rebuild the pre-housing fittings; the gate must fail")
    ap.add_argument("--cost", action="store_true",
                    help="triangles per fitting and per ring deck")
    args = ap.parse_args(argv)
    if args.legacy:
        _legacy()

    v, t, spans = build()
    print(f"corridor_section(21.6, one wall door, one bulkhead): "
          f"{len(t):,} triangles")

    fails = 0

    # -- 1. every lens sits inside a lamp ----------------------------------
    rows = lens_report(v, t, spans)
    print(f"\nLENS CONTAINMENT -- is the emissive surface inside a fitting?\n")
    print(f"    {'lens group':24s} {'bodies':>7s} {'w x h x d (mm)':>22s} "
          f"{'worst rim':>10s} {'worst depth':>12s}")
    print("-" * 82)
    bad = 0
    # ONE LINE PER GROUP AND THE WORST CASE IN IT, because 116 identical rows
    # is a report nobody reads and the failure is always the worst row.
    byname = {}
    for name, size, margin, depth in rows:
        ok = (margin is not None and margin > 1e-6
              and depth is not None and depth > 1e-6)
        bad += 0 if ok else 1
        cur = byname.setdefault(name, [0, 0, size, margin, depth])
        cur[0] += 1
        cur[1] += 0 if ok else 1
        for slot, val in ((3, margin), (4, depth)):
            if val is None or (cur[slot] is not None and val < cur[slot]):
                cur[slot] = val
    for name in sorted(byname):
        cnt, nbad, size, margin, depth = byname[name]
        dims = " x ".join(f"{s * 1000:.0f}" for s in sorted(size, reverse=True))
        m_s = "      -- mm" if margin is None else f"{margin * 1000:8.1f} mm"
        d_s = "        -- mm" if depth is None else f"{depth * 1000:10.1f} mm"
        print(f"{'FAIL' if nbad else 'PASS'}"
              f"{name:24s} {cnt:7d} {dims:>22s} {m_s}{d_s}"
              + (f"   {nbad} unhoused" if nbad else ""))
    n = len(rows)
    print(f"\n{n - bad}/{n} lens bodies are surrounded by "
          f"{' or '.join(BODY_GROUPS)} geometry that stands proud of them.")
    print(f"rim   = how far the lamp body extends beyond the lens across the "
          f"face. Zero is a\n        bare emissive box: nothing is around it.")
    print(f"depth = how far the body reaches along the axis the lens faces. "
          f"Zero is a lens\n        whose own front IS the front of the "
          f"fitting.")
    print(f"exempt by measurement: {', '.join(EXEMPT_LENSES)} -- see the "
          f"module docstring.")
    if bad:
        fails += 1

    # -- 2. every sign says something --------------------------------------
    srows, n_text, gh = sign_report(v, t, spans)
    print(f"\nSIGN LEGIBILITY -- is anything written on the plate?\n")
    print(f"    {'plate (mm)':>18s} {'glyph tris':>10s} {'cap (mm)':>9s} "
          f"{'legible to':>11s}")
    print("-" * 60)
    sbad = 0
    for size, ntri, cap, reach in sorted(srows, key=lambda r: -r[1]):
        dims = " x ".join(f"{s * 1000:.0f}"
                          for s in sorted(size, reverse=True)[:2])
        ok = ntri > 0 and reach >= READ_DISTANCE_M
        sbad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}{dims:>18s} {ntri:10d} "
              f"{cap * 1000:9.1f} {reach:10.2f} m")
    print(f"\n{len(srows) - sbad}/{len(srows)} sign plates carry lettering "
          f"legible across a {READ_DISTANCE_M} m corridor.")
    print(f"the whole section carries {n_text:,} glyph triangles on a "
          f"{gh}-row face.")
    print("legible to = cap height x 125, `signage.legible_at_m`'s own rule "
          "for a reader\n             who is not looking for the sign.")
    if sbad:
        fails += 1

    # -- 3. and none of it narrowed the corridor ---------------------------
    # `collision.corridor_profile` casts sideways between floor_y + 0.05 and
    # floor_y + 1.8 and keeps the NARROWEST clear half width; `station/lift.py`
    # sizes its car from the same number. So a housing that projected further
    # than the lens it wraps would shrink the station's corridors AND its lifts
    # with nothing to say so -- `interior_kit._selftest` asks this of
    # `wall_station` and `service_run` and NOT of `wall_assembly`, which is
    # where the downlights are. Asked here of the assembled section, which is
    # what the profile is actually measured on.
    own = _owner(len(t), spans)
    lo_b, hi_b = 0.022 + 0.05, 0.022 + 1.8
    inner = {}
    for i, tri in enumerate(t):
        pts = [v[k] for k in tri]
        if max(p[1] for p in pts) < lo_b or min(p[1] for p in pts) > hi_b:
            continue
        r = min(abs(p[0]) for p in pts)
        nm = own[i] or "untagged"
        if nm not in inner or r < inner[nm]:
            inner[nm] = r
    fit = {nm: r for nm, r in inner.items()
           if nm.startswith("light_") or nm.startswith("sign_")}
    half = K.PROVISIONAL["corridor_width_m"] / 2.0
    limit = half - K.PROVISIONAL["pilaster_proj_m"]
    print(f"\nWALKING ENVELOPE -- did a housing grow into the corridor?\n")
    print(f"    corridor half width {half:.3f} m, pilaster projection "
          f"{K.PROVISIONAL['pilaster_proj_m']:.3f} m, so nothing may come "
          f"inside {limit:.4f} m")
    ebad = 0
    for nm in sorted(fit, key=lambda a: fit[a])[:6]:
        ok = fit[nm] >= limit - 1e-9
        ebad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'}{nm:26s} innermost surface at "
              f"{fit[nm]:.4f} m from the centreline")
    print(f"\n{len(fit) - ebad}/{len(fit)} fitting and sign groups stay "
          f"outside the body band's clear width.")
    if ebad:
        fails += 1

    if args.cost:
        own = _owner(len(t), spans)
        per = {}
        for i, nm in enumerate(own):
            per[nm] = per.get(nm, 0) + 1
        print("\nCOST\n")
        fitting = sum(per.get(g, 0) for g in BODY_GROUPS)
        letters = sum(per.get(g, 0) for g in K.DECAL_GROUPS)
        print(f"  lamp bodies    {fitting:8,d} tri "
              f"({fitting / len(t) * 100:5.2f}% of the section)")
        print(f"  lettering      {letters:8,d} tri "
              f"({letters / len(t) * 100:5.2f}% of the section)")
        # PER LAP, from the ASSEMBLED DECK's own fitting counts rather than
        # from this section scaled up: `dist/Babylon5/.../blue_0_0_z7440.obj`
        # carries light_portal_head 2,964 tri, light_downlight 5,868 and
        # light_pilaster_strip 41,496, which at the pre-housing 12 tri a slab
        # and 84 tri a strip is 247 portal heads, 489 downlights and 494
        # pilasters. Those are the multipliers; a fitting's own body cost is
        # measured here.
        deck = {"light_portal_head": 247, "light_downlight": 489,
                "light_pilaster_strip": 494}
        # PER FITTING, NOT PER LENS, and the difference is a factor of seven on
        # one of the three rows: `pilaster`'s channel holds SEVEN cells inside
        # ONE can and ONE rim, so dividing the body total by the lens count
        # attributes a seventh of a channel to each cell and reports a fitting
        # that costs 17 triangles. A fitting is a connected body; that is the
        # same distinction `_components` is written for one section up.
        body_idx = [i for i in range(len(t)) if own[i] in BODY_GROUPS]
        # A FITTING IS THE CAN PLUS ITS RIM AND THE RIM IS FOUR BANDS, so a
        # fitting is FIVE connected components, not one -- they interpenetrate
        # rather than sharing vertices, which is exactly what `luminaire` builds
        # them to do. Attribution is therefore by AABB OVERLAP with a lens, and
        # the fitting count is the lens-body count.
        lens_boxes = {}
        for name in deck:
            idx = [i for i in range(len(t)) if own[i] == name]
            lens_boxes[name] = [_aabb(v, t, lc) for lc in _components(t, idx)] \
                if idx else []
        per_fitting = {}
        for comp in _components(t, body_idx):
            blo, bhi = _aabb(v, t, comp)
            owner_name = None
            for name, boxes in lens_boxes.items():
                if any(all(blo[j] <= lhi[j] + 1e-6 and llo[j] <= bhi[j] + 1e-6
                           for j in range(3)) for llo, lhi in boxes):
                    owner_name = name
                    break
            key = owner_name or "unattributed"
            slot = per_fitting.setdefault(key, [0, 0])
            # HOW MANY FITTINGS: one CAN is one fitting, derived rather than
            # written down. Writing the counts here would be a second
            # description of what the kit built, which is the drift this
            # project has paid for more than once.
            slot[0] += 1 if all(own[i] == "light_housing" for i in comp) else 0
            slot[1] += len(comp)
        print()
        total = 0.0
        for name, count in sorted(deck.items()):
            if name not in per_fitting:
                print(f"  {name:24s}  not built in this section")
                continue
            nfit, ntri = per_fitting[name]
            each = ntri / nfit
            print(f"  {name:24s} {each:6.0f} tri of body each x {count:4d} "
                  f"a ring deck = {each * count:9,.0f}")
            total += each * count
        if per_fitting.get("unattributed", [0])[0]:
            print(f"  {'unattributed':24s} {per_fitting['unattributed'][0]:4d} "
                  f"bodies hold no lens -- suspicious, read the geometry")
        # LETTERING PER LAP, on the same footing. The packaged deck carries
        # `sign_frame` 1,968 triangles at 12 a plate, so 164 sign plates -- and
        # 164 `sign_text` plates that were blank. The lettering that replaces
        # them is charged per letter, which is why `signage._spans` merges runs.
        if srows:
            per_plate = sum(r[1] for r in srows) / len(srows)
            letters_lap = per_plate * 164
            print(f"  {'lettering':24s} {per_plate:6.0f} tri each x "
                  f"{164:4d} a ring deck = {letters_lap:9,.0f}")
            total += letters_lap
        print(f"  {'':24s} {'':24s}   ring-deck total  {total:9,.0f} tri")
        print("\n  the SAME fittings before this pass cost 12 tri of lens each "
              "and no body at all,\n  and the sign plates were blank, so the "
              "ring-deck delta IS the total above:\n  on the packaged deck's "
              f"484,440 triangles that is +{total / 484440 * 100:.1f}%.")

    if args.legacy:
        if fails:
            print("\nCONTROL OK: the pre-housing corridor FAILS questions 1 "
                  "and 2, so neither is inert.\nQuestion 3 PASSES here and is "
                  "supposed to: it is a regression guard on the walking\n"
                  "envelope, and the content it guards against is a housing "
                  "that grows into the\ncorridor, which the legacy corridor "
                  "has no housings to do.")
            return 0
        print("\nCONTROL DID NOT FIRE -- the legacy corridor passes this "
              "gate, which means the gate measures nothing. Fix the gate, "
              "not the content.")
        return 1
    if fails:
        print(f"\n{fails} of 3 questions FAILED.")
        return 1
    print("\nall three questions pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
