#!/usr/bin/env python3
"""SHELL B — THE HOMES OF 250,000 PEOPLE, GENERATED RATHER THAN ENUMERATED.

`docs/spec/PLACES.md` §2 commits the station to nine residential belts totalling
**≈5.12 M m² gross** and **222,580 dwellings** (209,580 block units + 13,000
refugee partitions), which is **89% of the station's housing**. Until this file
existed there was no builder for any of it: `ls station/ | grep -i resid`
returned nothing, and the 29 SHB spec rows passed because
`station/spec_harness/shb.py`'s own docstring says, in terms, *"Nothing in that
chain needs a built station ... there is no Shell B builder in the project at
all"*. The arithmetic re-added to 250,001 while nobody had a home.

Measured at adoption: **251 decks in the ring stacks, 71 of them carry a named
place**. The other 180 — 72% of the station — had no geometry of any kind.

WHY PROCEDURAL AT LOW DETAIL, AND NOT THE OTHER THING. The alternative was to
narrow the promise to the 129 named landmarks and call the rest structure. The
owner rejected it: CLAUDE.md's brief is that *"the simulation exists around you
rather than in text"*, and a station whose 250,000 residents have addresses but
no doors is a station that exists in text. Shell B is the connective tissue that
makes an address real. `docs/decisions-shell-b.md` carries the decision and what
would overturn it.

WHAT "LOW DETAIL" MEANS HERE, STATED AS A RULE RATHER THAN A FEELING. Shell A
(`rooms.build`) spends **25,740 triangles on one bay** of a docking bay and the
whole station's 128 places cost 19.6 M. Applying that vocabulary to 5.12 M m²
would be tens of millions of triangles for corridors nobody has a reason to
stand in. So Shell B emits **boxes and quads only**: no `articulate()`, no
`dressing.py`, no props, no baked bodies. The number to watch is **triangles per
square metre**, and `--deck` prints it. What Shell B buys is that a resident's
door is where their card says it is and opens onto a floor.

THE FOUR THINGS IT DOES NOT INVENT, because hard rule 4 says one authoritative
model:

  * unit dimensions are `quarters.unit_dims()`. The INV-032 ladder areas the
    annex quotes (34/18/46/22/16/9 m²) ARE `quarters.CLASSES`' areas, so a
    Shell B unit is the same room a Shell A quarters unit is, at less detail.
  * corridor width, wall thickness, door width and height are
    `interior_kit.PROVISIONAL`.
  * the deck a belt sits on, its radius and its cell plan are
    `interior.decks_in_ring` / `interior.ring_cells` — the same functions the
    Shell A deck builder uses.
  * the block counts, unit areas, per-deck programs and gross areas are PARSED
    OUT OF `docs/spec/PLACES.md`. Not restated here. `spec_harness/shb.py`
    already makes the point one level down: *"a constant copied into a harness
    cannot disagree with the row it checks"*. The same is true of a builder —
    a builder that restates the spec cannot be caught building the wrong thing.

THE COLLISION SHELL IS MEASURED, NEVER WRITTEN DOWN. CLAUDE.md's session-3v
rule: *"A player walks on a surface built for walking on ... The shell's profile
is measured off the kit by ray casting."* `block_profile()` casts rays at a
built block exactly as `collision.corridor_profile()` casts them at the corridor
kit, so if the block's floor slab or its door head moves, the shell moves with
it and cannot drift.

VARIETY IS A GATE, NOT AN ASPIRATION. CLAUDE.md's degeneracy rule — *"two places
whose geometry hashes the same ARE one place"* — is the reason five things vary
per deck and none of them is decoration:

  * the slot ORDER around the ring is a seeded permutation of the deck's own
    program, so no two decks present the same sequence of doors;
  * a block's units split unevenly between its two sides (the split is seeded
    within ±2 of half), so party walls do not line up between two blocks;
  * the spine's door phase is seeded within one unit frontage — `quarters.run`
    varies the same thing for the same reason;
  * every third block carries an end lobby, chosen by hash rather than by index;
  * the per-deck program itself moves with the deck (a wash room per BLOCK, a
    laundry hall every third deck), so the deck's own population changes it.

`--selftest --degeneracy` hashes twelve decks and asserts twelve distinct
geometries; `--selftest --legacy` disables all five and is shown collapsing.

WHAT THIS FILE DELIBERATELY DOES NOT DO. It is not wired into
`tools/export_station.py`. That file's `work_list()` enumerates decks from
`routes.clusters()` — every deck that CARRIES A LOCATION — which is exactly the
71, and adding the other 180 is a one-function change in a file this module does
not own. The instruction is in `docs/decisions-shell-b.md` §6 and in this
module's `integration_note()`, which prints it.

Run: python3 station/shell_b.py --selftest
     python3 station/shell_b.py --plan
     python3 station/shell_b.py --deck red/1/8
     python3 station/shell_b.py --deck red/1/8 --obj /tmp/shb.obj
"""
import argparse
import hashlib
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import collision as C                                            # noqa: E402
import interior as it                                            # noqa: E402
import interior_kit as kit                                       # noqa: E402
import quarters as Q                                             # noqa: E402
from spec_harness import shb as SPEC                              # noqa: E402

PLACES_MD = os.path.join(ROOT, "docs/spec/PLACES.md")

# --------------------------------------------------------------------------
# THE PROGRAM VOCABULARY
# --------------------------------------------------------------------------
#
# Every noun the nine belts use for a room, mapped to a canonical kind and a
# geometry family. WRITTEN OUT RATHER THAN FUZZY-MATCHED, for the reason
# `shb.py::_ROLE_OF` gives one level down: a fuzzy matcher pairs "cold store"
# with "storage" and leaves "stockroom" unmatched, which reads as agreement.
#
# The order matters — longest phrase first — because "shift wash-up rooms"
# contains "wash" and "irrigation pump houses" contains "pump".
PROGRAM_WORDS = (
    ("shift wash-up rooms", "wash"),
    ("staff wash rooms", "wash"),
    ("wash rooms", "wash"),
    ("wash room", "wash"),
    ("mess/galley points", "galley"),
    ("mess rooms", "mess"),
    ("mess", "mess"),
    ("irrigation pump houses", "pump"),
    ("pump rooms", "pump"),
    ("stockrooms", "stockroom"),
    ("cold stores", "cold_store"),
    ("cold store", "cold_store"),
    ("waste holds", "waste_hold"),
    ("storage rooms", "storage"),
    ("storage", "storage"),
    ("local plant rooms", "plant"),
    ("plant rooms", "plant"),
    ("plant", "plant"),
    ("maintenance shops", "maintenance"),
    ("maintenance shop", "maintenance"),
    ("maintenance", "maintenance"),
    ("laundry hall", "laundry"),
    ("sample lab", "lab"),
    ("tool cribs", "tool_crib"),
    ("first-aid points", "first_aid"),
    ("first-aid", "first_aid"),
    ("suit lockers", "suit_locker"),
    ("bothies", "bothy"),
    # `depot_tram` AND NOT `tram_depot`, WHICH IS NOT A STYLE CHOICE.
    # `materials._scan_generator_groups` reads group-name literals out of every
    # `station/*.py` by prefix -- `drum|endcap|truss|tram|core|ground|greeble|
    # light|garden|spoke` followed by an underscore -- and it cannot tell a
    # SPEC noun from a SURFACE name. Written the natural way round, this
    # module's program vocabulary put a phantom `tram_depot` group into the
    # material coverage list and the layer-3 gate reported it unbound: a
    # surface nothing draws, failing a gate about surfaces. Exactly the line
    # `NOT_GENERATORS` already draws for `rooms.py` ("a SPECIFICATION names
    # places and props, a GENERATOR names surfaces"), arriving from the other
    # side. No literal in this file may begin with one of those prefixes.
    ("tram depots", "depot_tram"),
    ("ag-store barn", "barn"),
    ("wash", "wash"),
)

# kind -> (family, plan aspect ratio, floor area a room of this kind may not go
# below, ceiling height in metres).
#
# THE MINIMUM IS A FLOOR, NOT A SIZE. A room's actual area is its share of the
# belt's own leftover gross (see `deck_slots`), apportioned in proportion to
# these minima — so the areas are DERIVED from the annex and these numbers only
# decide the split and stop a room becoming a cupboard when a belt is tight.
# Every one is authority 5 and every one is a plausible-shape argument rather
# than a source: a mess room seats a shift, a tool crib is a counter and racks,
# a tram depot stables two cars end to end.
PROGRAM = {
    "mess":        ("hall",      1.60,  60.0, 3.00),
    "galley":      ("hall",      1.60,  45.0, 3.00),
    "wash":        ("room",      2.20,  24.0, 2.80),
    "storage":     ("room",      1.40,  18.0, 3.00),
    "stockroom":   ("room",      1.40,  18.0, 3.00),
    "cold_store":  ("room",      1.30,  30.0, 3.00),
    "waste_hold":  ("plant",     1.30,  40.0, 3.20),
    "maintenance": ("shop",      1.50,  40.0, 3.20),
    "plant":       ("plant",     1.30,  30.0, 3.20),
    "pump":        ("plant",     1.20,  28.0, 3.20),
    "lab":         ("room",      1.50,  30.0, 2.80),
    "tool_crib":   ("room",      1.40,  16.0, 3.00),
    "first_aid":   ("room",      1.40,  18.0, 2.80),
    "suit_locker": ("room",      2.00,  18.0, 3.00),
    "laundry":     ("hall",      1.80,  80.0, 3.00),
    "bothy":       ("room",      1.40,  24.0, 2.80),
    "depot_tram":  ("depot",     2.50, 400.0, 5.00),
    "barn":        ("depot",     1.80, 200.0, 4.50),
    "partition":   ("partition", 1.50,   9.0, 2.60),
}

# The INV-032 ladder area -> the `quarters.CLASSES` key that IS that area. Built
# by lookup rather than typed, so a class whose area moves in `quarters.py`
# moves here and a ladder entry with no class raises instead of guessing.
UNIT_CLASS_BY_AREA = {c["area_m2"]: c["key"] for c in Q.CLASSES
                      if c["area_m2"] > 0}

WALL_T_M = Q.WALL_T_M               # 0.16 -- the quarters party wall
DOOR_W_M = kit.PROVISIONAL["door_width_m"]
DOOR_H_M = kit.PROVISIONAL["door_height_m"]
CORRIDOR_W_M = kit.class_params("residential")["corridor_width_m"]
RING_W_M = kit.PROVISIONAL["corridor_width_m"]
ARC_STEP_M = kit.PROVISIONAL["ring_frame_spacing_m"]   # 4.5 -- arc tessellation
SLOT_GAP_M = 0.6                    # structure between two slots on the ring
# The station's housing quantum, `arrival.py:573 UNITS_PER_BLOCK`, which the
# Shell B derivation paragraph makes normative ("blocks of 60 units"). Read
# from the annex through `belts()['SHB-01']['units_per_block']` everywhere a
# belt states it; this constant is only the fallback for the refugee halls,
# whose own row states a partition count and no block size.
UNITS_PER_HALL = 60

# The negative control, off by default. `--legacy` turns it on, which disables
# the five variety rules and the derived area budget; `--selftest --legacy` is
# expected to FAIL and is the evidence that this file's gates can.
_LEGACY = False

# --------------------------------------------------------------------------
# GROUP NAMES — and why every one of them carries somebody else's tail
# --------------------------------------------------------------------------
#
# `materials.resolve()` is a SUBSTRING match, longest fragment wins, and it is
# the identical rule `render_shot.gd::_material_for` runs. So a group named
# `shb_unit_qtr_wall` resolves through `qtr_wall`, which `materials.py` already
# binds, and Shell B inherits the station's material vocabulary WITHOUT an edit
# to `materials.py` and without a magenta fallback.
#
# That is not a trick, it is hard rule 4: a Shell B corridor wall is the same
# panel as a Shell A corridor wall, so it should be the same material by
# construction rather than by a second table somebody keeps in step.
#
# THE NAMES ARE LITERALS, deliberately. Session 4f: *"A NAME BUILT BY STRING
# INTERPOLATION IS INVISIBLE TO A REGEX OVER SOURCE"* — 45 groups sat on the
# fallback material because `corridor_dressing.py` named them
# `f"dress_{kind}"`. Every name Shell B can emit is spelled out below, and
# `_selftest` resolves all of them.
G = {
    "unit_deck":    "shb_unit_qtr_deck",
    "unit_soffit":  "shb_unit_soffit",
    "unit_wall":    "shb_unit_qtr_wall",
    "unit_party":   "shb_unit_party_qtr_wall",
    "unit_pier":    "shb_unit_pier_qtr_wall",
    "unit_head":    "shb_unit_head_door_frame",
    "unit_jamb":    "shb_unit_jamb_door_frame",
    "spine_deck":   "shb_spine_generic_deck",
    "spine_soffit": "shb_spine_soffit",
    "spine_wall":   "shb_spine_generic_wall",
    "spine_skirt":  "shb_spine_generic_skirt",
    "spine_light":  "shb_spine_light_soffit_blade",
    "ring_deck":    "shb_ring_generic_deck",
    "ring_soffit":  "shb_ring_soffit",
    "ring_wall":    "shb_ring_generic_wall",
    "ring_rib":     "shb_ring_generic_rib",
    "ring_light":   "shb_ring_light_soffit_blade",
    "room_deck":    "shb_room_generic_deck",
    "room_soffit":  "shb_room_soffit",
    "room_wall":    "shb_room_generic_wall",
    "room_head":    "shb_room_head_door_frame",
    # THE TAILS ARE CHOSEN BY ASKING `materials.resolve`, NOT BY LOOKING
    # PLAUSIBLE. The first draft used `fix_bench` and `fix_plant_skid`, both of
    # which read like every other fixture name in `rooms.py` and neither of
    # which `materials.py` binds -- the coverage claim in `_selftest` caught
    # them, which is the whole reason it is a claim and not a comment.
    "room_fit":     "shb_room_prop_bench",
    "plant_fit":    "shb_plant_prop_workbench",
}


# --------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------
def seed_of(*parts):
    """A stable 64-bit seed from a tuple of names and numbers.

    `rooms._u`'s idiom, restated rather than imported because importing
    `rooms.py` pulls in `dressing`, `populace` and `npc/body` — minutes of
    import for one hash, and a hard dependency on three modules other agents
    own. blake2b, digest_size 8, so the value is reproducible across processes
    and across Python versions; `hash()` is not.
    """
    h = hashlib.blake2b("|".join(str(p) for p in parts).encode(),
                        digest_size=8).digest()
    return int.from_bytes(h, "big")


def _u(*parts):
    """`seed_of` as a float in [0, 1)."""
    return seed_of(*parts) / float(1 << 64)


def _seed(*parts):
    """A per-slot seed, or ONE seed for the whole station under `--legacy`.

    This is the control that makes the degeneracy claim mean something. Every
    variety rule in this file hangs off a seed that carries the sector, the
    ring, the deck and the slot index; collapsing it to a constant is exactly
    what a generator that had never thought about repetition would do, and
    `--selftest --legacy` is that generator.
    """
    return seed_of("legacy") if _LEGACY else seed_of(*parts)


def _shuffle(items, *seed_parts):
    """A seeded permutation. Fisher-Yates from `seed_of`, not `random`.

    `random.Random(seed).shuffle` would also be deterministic, but only for one
    CPython; the algorithm is not specified and has changed. This one is three
    lines and cannot drift.
    """
    out = list(items)
    for i in range(len(out) - 1, 0, -1):
        j = seed_of(i, *seed_parts) % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


# --------------------------------------------------------------------------
# READING THE ANNEX
# --------------------------------------------------------------------------
_CACHE = {}

_DECK_RANGE = re.compile(r"decks?\s*(\d+)\s*[–-]\s*(\d+)")
_PER_DECK_MARK = re.compile(r"(?:^|[;.]\s*)[Pp]er\s+[a-zA-Z/']*\s*deck:|"
                            r"per deck:|/deck")
_PER_BLOCK = re.compile(r"wash(?:\s+room)?\s+per\s+block")
_PER_N_DECKS = re.compile(r"(\d+)\s+laundry hall per\s+(\d+)\s+decks")
_SLASH_DECK = re.compile(r"([a-z][a-z\- ]*?)\s+(\d+)\s*/deck")
_GROSS = re.compile(r"≈\s*([\d,]+)\s*m²")
_SECTOR_RING = re.compile(
    r"(Blue|Red|Green|Grey|Yellow)\s+rings?\s+(\d)(?:\s*[–-]\s*(\d))?")


def _i(s):
    return int(str(s).replace(",", "").strip())


def _program_clause(flat):
    """The part of a row that lists rooms, and whether it is per deck.

    Returns `(text, per_deck)`. The rule is the row's own words and nothing
    else: a clause introduced by `per deck:` / `Per <x> deck:`, or one whose
    counts are written `N/deck`, is PER DECK; anything else is a BELT TOTAL to
    be spread over the belt's decks.

    THIS IS THE ONE PLACE THE READING COULD HAVE BEEN PICKED INSTEAD OF READ,
    and picking it would have been a factor of fourteen. SHB-05 says
    "12 pump rooms, 8 storage, 2 maintenance shops, sample lab" over Red ring 3,
    which stacks 14 decks. Read per-deck that is 322 rooms; read as a total it
    is 23. The row does not say "per deck", so it is 23 — and if a future
    editor adds those two words the builder follows without being touched.
    """
    per = bool(_PER_DECK_MARK.search(flat))
    m = re.search(r"[Pp]er\s+[a-zA-Z/']*\s*deck:\s*(.+?)(?:\*\*|$)", flat)
    if m:
        return m.group(1), True
    m = re.search(r"~\s*[\d,]+\s*(?:blocks)?/deck;\s*(.+?)(?:\*\*|$)", flat)
    if m:
        return m.group(1), True
    # A no-housing row states its program straight after the "No housing."
    m = re.search(r"No (?:housing|blocks|formal housing)[^.]*\.\s*(.+?)"
                  r"(?:\*\*|$)", flat)
    if m:
        return m.group(1), per
    return flat, per


def _trim_clause(clause):
    """Drop the sentence that INTRODUCES a program list, and the one after it.

    Two shapes, both taken from the annex's own punctuation rather than
    guessed, and both found by the residue check refusing to pass:

      * a lead-in ending in a colon — SHB-09's "At the 4 worked nodes
        (PLC-097/098/119–124 clusters):", SHB-05's "Water/waste rosette
        support:", SHB-07's "Field support:". The first draft read "4 worked"
        as four rooms of an unknown kind and failed the row, which is the
        residue check doing exactly its job: a lead-in is not a program.
      * a trailing prose clause introduced by "; the " — SHB-05's satellite
        camp fringe, SHB-08's casual muster. Both are places, not rooms.

    The colon is only cut when what follows still parses to a program, so a row
    whose only program sits BEFORE a colon cannot be silently emptied.
    """
    cut = re.search(r";\s*the\b", clause)
    if cut:
        clause = clause[:cut.start()]
    if ":" in clause:
        tail = clause.rsplit(":", 1)[1]
        counts, per_block, _pn, _res = _parse_program(tail)
        if counts or per_block:
            return tail
    return clause


def _parse_program(clause):
    """`(kind -> count, per_block kinds, per_n_decks, residue)` from prose.

    THE RESIDUE IS THE POINT. `shb.py`'s lesson one level down is that
    *"'I cannot read this' and 'this disagrees' are opposite findings and only
    one is about the station"* — so this returns what it could NOT consume, and
    `belts()` refuses any row whose residue still contains a `<number> <word>`
    pattern. A vocabulary that quietly drops "4 waste holds" builds a station
    with no waste holds and passes every arithmetic gate in the project.
    """
    txt = clause
    # Parentheticals are commentary -- "(air handler / water riser / breaker)",
    # "(1 per 4 blocks)", "(consignment cages matched to named stalls)". They
    # are dropped BEFORE matching so their nouns cannot be counted twice, and
    # they are dropped from the residue too so they cannot fail the check.
    txt = re.sub(r"\([^)]*\)", " ", txt)
    counts, per_block, per_n = {}, [], {}

    spans = []

    def take(m, kind, n):
        counts[kind] = counts.get(kind, 0) + n
        spans.append((m.start(), m.end()))

    for m in _PER_BLOCK.finditer(txt):
        per_block.append("wash")
        spans.append((m.start(), m.end()))
    for m in _PER_N_DECKS.finditer(txt):
        per_n["laundry"] = (int(m.group(1)), int(m.group(2)))
        spans.append((m.start(), m.end()))
    for m in _SLASH_DECK.finditer(txt):
        noun = m.group(1).strip().lower()
        kind = dict(PROGRAM_WORDS).get(noun)
        if kind is None:
            for word, k in PROGRAM_WORDS:
                if noun.endswith(word):
                    kind = k
                    break
        if kind:
            take(m, kind, int(m.group(2)))

    def consumed(a, b):
        return any(not (b <= s or a >= e) for s, e in spans)

    for word, kind in PROGRAM_WORDS:
        for m in re.finditer(r"(?:(\d+)\s+)?" + re.escape(word) + r"\b", txt):
            if consumed(m.start(), m.end()):
                continue
            take(m, kind, int(m.group(1)) if m.group(1) else 1)

    keep = []
    at = 0
    for s, e in sorted(spans):
        keep.append(txt[at:s])
        at = max(at, e)
    keep.append(txt[at:])
    residue = " ".join(keep)
    return counts, per_block, per_n, residue


def belts():
    """The nine belts, read out of `docs/spec/PLACES.md`, never restated.

    Each row: sector, rings, deck range, block clauses (count, per block, unit
    area), the unit-area split for a row that states one, the per-deck or
    whole-belt room program, and the row's own `≈ N m² gross`.

    A ROW THAT DOES NOT PARSE RAISES. It does not fall back to an empty program
    and it does not skip: a belt silently built with no mess rooms is a belt
    that passes every count in this project and houses nobody who eats.
    """
    if "belts" in _CACHE:
        return _CACHE["belts"]
    pre = SPEC._preamble()
    blocks = SPEC._blocks_md()
    out = {}
    for n in range(1, 10):
        key = "SHB-%02d" % n
        line, text = blocks[key]
        flat = re.sub(r"\s+", " ", text)
        head = flat.split("—", 1)[1] if "—" in flat else flat
        m = _SECTOR_RING.search(head)
        if m:
            sector = m.group(1).lower()
            r0 = int(m.group(2))
            rings = ([r0] if not m.group(3)
                     else list(range(r0, int(m.group(3)) + 1)))
        elif re.search(r"Yellow", head):
            sector, rings = "yellow", []
        else:
            raise ValueError("%s: heading names no sector/ring: %r"
                             % (key, head[:70]))

        clauses, pairs = SPEC._housing(text)
        mg = _GROSS.search(flat)
        if not mg:
            raise ValueError("%s states no gross m² figure" % key)
        md = _DECK_RANGE.search(flat)
        clause, per_deck = _program_clause(flat)
        clause = _trim_clause(clause)
        counts, per_block, per_n, residue = _parse_program(clause)
        if not counts and not per_block:
            raise ValueError("%s: no room program parsed from %r"
                             % (key, clause[:90]))
        stray = re.search(r"\b(\d+)\s+([a-z][a-z\-']{2,})", residue)
        if stray:
            raise ValueError(
                "%s: the program vocabulary cannot read %r in %r -- a parse "
                "failure, not a disagreement" % (key, stray.group(0),
                                                 residue.strip()[:90]))
        out[key] = {
            "id": key, "line": line, "sector": sector, "rings": rings,
            "deck_lo": int(md.group(1)) if md else None,
            "deck_hi": int(md.group(2)) if md else None,
            "clauses": clauses, "pairs": pairs,
            "units_per_block": pre["units_per_block"],
            "gross_factor": pre["gross_factor"],
            "gross_m2": _i(mg.group(1)),
            "program": counts, "per_block": per_block, "per_n_decks": per_n,
            "per_deck": per_deck,
            "units": sum(nb * per for nb, per, _a in clauses),
            "blocks": sum(nb for nb, _p, _a in clauses),
            "text": flat,
        }
    out["SHB-08.f"] = _refugee_row()
    _CACHE["belts"] = out
    return out


def _refugee_row():
    """SHB-08.f — 13,000 refugee partitions, the belt inside a lettered annexe.

    It is a belt in everything but numbering: 163,800 m² gross, its own
    dwelling count, and `docs/spec/PLACES.md` §4 TOTALS adds it to Grey's Shell
    B line separately from SHB-08's 36,000. Modelled here so the station's
    dwelling total can reach the annex's own 222,580 rather than stopping at
    209,580 and calling the difference rounding.

    Parsed from the annexe rather than typed, and `shb._sub_08f` already gates
    the same arithmetic from the other side.
    """
    txt, why = SPEC._annexe("SHB-008.f", "f")
    if txt is None:
        raise ValueError("SHB-08.f: %s" % why)
    m = re.search(r"the\s*([\d,]+)\s*\((\d+) m² partitions ×([\d.]+)"
                  r"[^=]*=\s*\*\*([\d,]+) m² gross\*\*", txt)
    if not m:
        raise ValueError("SHB-08.f: the partition arithmetic did not parse")
    n, area, factor, gross = (_i(m.group(1)), int(m.group(2)),
                              float(m.group(3)), _i(m.group(4)))
    return {
        "id": "SHB-08.f", "line": SPEC._blocks_md()["SHB-08"][0],
        "sector": "grey", "rings": [0], "deck_lo": None, "deck_hi": None,
        "clauses": [], "pairs": [], "units_per_block": 1,
        "gross_factor": factor, "gross_m2": gross,
        "program": {"partition": n}, "per_block": [], "per_n_decks": {},
        "per_deck": False, "units": 0, "blocks": 0,
        "partition_area_m2": area, "partitions": n,
        "text": txt,
    }


# --------------------------------------------------------------------------
# ONE DECK STACK PER RING -- the thing that decides every radius
# --------------------------------------------------------------------------
#
# TWO DECKS AT ONE RADIUS ARE ONE DECK, and this module shipped fifteen of
# them. `deck_slots` used to read `decks_in_ring(...)[min(deck, len - 1)]`, so
# once a belt's deck index ran past what the hull leaves at the belt's own z,
# every further deck resolved to the innermost radius the stack had:
#
#     blue ring 0   8 decks,  4 distinct radii -- decks 5,6,7,8,9 all at 179.5 m
#     grey ring 0  23 decks, 12 distinct radii -- decks 11..22 all at 390.8 m
#
# `tools/merge_cells.py::deck_headroom` derives streaming residency as a
# CONTAINMENT TEST ON RADIUS -- a deck floor is opaque, so the band a deck
# occupies is the gap to its inboard neighbour -- and it refused the export
# with "derived deck headroom below 2.0 m ... a band this thin is a fall
# through the world". That refusal is correct. `min(deck, len - 1)` is the
# defect, and a clamp is the exact shape of failure CLAUDE.md names: it emits
# the convenient reading instead of failing.
#
# The cure is not a better clamp. It is that A RING HAS ONE DECK STACK and
# every deck of that ring indexes it -- so distinct indices give distinct
# radii by construction, `DECK_PITCH_M` apart, and there is nothing left to
# clamp. A belt that asks for more decks than the stack holds is CAPPED, once,
# at belt level, where `_split_evenly` redistributes its blocks over the decks
# that remain and the annex's totals hold exactly.
#
# The stack depends on the belt's z depth (the hull tapers, so a deeper belt
# is asked about a narrower cylinder) and the depth depends on how many decks
# share the belt's blocks, so it is a fixed point. It is taken at SECTOR
# level, at ONE axial station, and that is not a convenience -- see
# `_settle_sector`, where taking it per ring was tried and put red ring 2 on
# red ring 3's radii.
_RING_STACK = {}          # (id(schema), sector, ring) -> the deck list in use
_SECTOR_Z = {}            # (id(schema), sector) -> (z probed, depth it came from)
_SETTLING = set()         # sectors whose fixed point is running right now
_CAPPED = {}              # (belt id, sector, ring) -> (wanted, kept, why)
_INDEXED = {}             # (sector, ring) -> why a rung could not be resolved
_SETTLE_PASSES = 5


def _probe_z(schema, profile, sector, depth_m):
    """The axial station a sector's whole shell is planned against.

    `depth_m <= 0` means "not measured yet" and gives the sector's own z0,
    which is where the first pass starts.
    """
    z0 = schema["sectors"]["extents_m"][sector]["z0"]
    if depth_m <= 0 or _LEGACY:
        return z0
    return it.narrowest_z(profile, z0 + depth_m / 2.0, depth_m)


def _sector_rings(sector):
    """Every ring index the sector's belts name, plus 0 for a node belt."""
    out = set()
    for b in belts().values():
        if b["sector"] == sector:
            out.update(b["rings"] or [0])
    return sorted(out)


def _stacks_at(schema, profile, sector, z):
    """`{ring: deck list}` for every ring this sector's belts use, at ONE z.

    One `z` for the whole sector is the load-bearing part. `interior.ring_radii`
    re-partitions the cross-section at every axial station, so "ring 2" is a
    different physical shell at two different z -- and two rings resolved at two
    different z can occupy the same radii while each is individually correct.
    Taken from one station they are nested by construction.
    """
    return {r: it.decks_in_ring(schema, profile, sector, r, z_m=z)
            for r in _sector_rings(sector)}


def ring_stack(schema, profile, sector, ring):
    """THE deck stack of one ring. Every radius in this module comes from here.

    Memoised per `(schema, sector, ring)`, so two decks of a ring can never
    answer from two different stacks -- which is the invariant that makes
    distinct deck indices give distinct radii.
    """
    k = (id(schema), sector, ring)
    if k not in _RING_STACK:
        z = _SECTOR_Z.get((id(schema), sector), (None, 0.0))[0]
        if z is None:
            z = _probe_z(schema, profile, sector, 0.0)
            _SECTOR_Z[(id(schema), sector)] = (z, 0.0)
        for r, st in _stacks_at(schema, profile, sector, z).items():
            _RING_STACK.setdefault((id(schema), sector, r), st)
        _RING_STACK.setdefault(k, it.decks_in_ring(schema, profile,
                                                   sector, ring, z_m=z))
        if sector not in _SETTLING:
            _settle_sector(schema, profile, sector)
    return _RING_STACK[k]


def _settle_sector(schema, profile, sector):
    """Run the depth/stack fixed point for one sector, at one axial station.

    THE OLD LOOP WAS DEAD CODE AND THIS IS WHAT REPLACES IT. `deck_slots`
    carried a documented three-pass recursion on `_pass` -- and 70 lines above
    it `for _pass in range(6):` rebinds the same name, so by the time the
    recursion guard was read `_pass` was always 5 and `if _pass < 3` never
    fired. Every radius in the module came from pass 0, probed at the sector's
    z0. The shadowing was invisible because the answer looked sane: z0 is the
    narrow end of most sectors here, so the dead loop's result was usually the
    conservative one anyway.

    TWO THINGS BOUND THE DEEPENING, AND BOTH WERE FOUND BY A NUMBER MOVING.

    *One station per sector.* Settling each ring against its own belt's depth
    was tried first. It gave every ring distinct radii and put **red ring 2 on
    red ring 3's exact radii** (101.86, 98.26, 94.66 …), because SHB-04 runs
    300 m deep and the hull at that station carries a ring 2 no bigger than the
    ring 3 at red's near end. Each ring was individually right and the pair was
    a solid interpenetrating a solid. `ring_radii` partitions the whole
    cross-section, so ring indices are only comparable within one station.

    *A deepening that deletes a ring is refused.* At red's deep station ring 3
    does not stack at all, so adopting it would silently delete SHB-05's twelve
    decks. The rule is `spec_registry`'s: refuse the ambiguity rather than emit
    the convenient reading of it -- keep the last station at which every ring
    the sector's belts name still exists, and record which one that was.
    """
    key = (id(schema), sector)
    _SETTLING.add(sector)
    try:
        for _ in range(_SETTLE_PASSES):
            _BELT_INDEX.pop(key, None)
            deepest = 0.0
            for b in sorted(belts().values(), key=lambda x: x["id"]):
                if b["sector"] != sector:
                    continue
                for sec, ring, dk in belt_decks(schema, profile, b):
                    p = deck_slots(schema, profile, sec, ring, dk)
                    if p is not None:
                        deepest = max(deepest, p["depth_m"])
            if deepest <= _SECTOR_Z[key][1] + 0.01:
                break                      # the depth stopped growing
            z = _probe_z(schema, profile, sector, deepest)
            nxt = _stacks_at(schema, profile, sector, z)
            if any(not v for v in nxt.values()):
                break                      # a ring would vanish -- refuse it
            same = all(len(v) == len(_RING_STACK.get((id(schema), sector, r),
                                                     []))
                       and abs(v[0]["floor_r_m"]
                               - _RING_STACK[(id(schema), sector, r)][0]
                               ["floor_r_m"]) < 0.005
                       for r, v in nxt.items())
            _SECTOR_Z[key] = (z, deepest)
            for r, v in nxt.items():
                _RING_STACK[(id(schema), sector, r)] = v
            if same:
                break
    finally:
        _SETTLING.discard(sector)
        _BELT_INDEX.pop(key, None)


def stack_entry(schema, profile, sector, ring, deck):
    """The deck stack row a Shell B deck NUMBER names. Never a clamp.

    A Shell B deck number is a register LABEL where the register claims that
    rung and the canonical RUNG where it does not (`belt_decks` / `_address`),
    and the two sets are disjoint by construction, so this is a lookup and not
    a subscript. It used to read `stack[min(deck, len - 1)]`, which is the
    clamp that put fifteen decks of this module's own plan at a radius another
    deck already had.

    ONE PLACE IT CANNOT BE A RUNG, AND IT IS NAMED RATHER THAN CLAMPED
    SILENTLY. `ring_radii` re-partitions the whole cross-section at every axial
    station, so a ring INDEX does not always name the same ring at two z. On
    yellow it does not: the sector's belt settles at z 0.0, where `ring_1` has
    closed up entirely and index 0 therefore names `ring_2`. SHB-09's node deck
    is addressed by the register -- ring index 0 of yellow, meaning `ring_1` --
    and no rung of `ring_2` is that deck. There is no mapping between the two
    ladders because they are different rings; the module keeps its pre-4w
    positional resolution there so the row still accounts for its 12,000 m²,
    and records it in `indexed()` so it is never silent. `--plan` prints it.

    Everywhere else -- 83 of the plan's 84 decks -- the rung resolves exactly
    and a miss raises, because a miss there is a bug in `belt_decks`' cap.
    """
    stack = ring_stack(schema, profile, sector, ring)
    if _LEGACY:
        # THE CONTROL IS THE CLAMP ITSELF. `--selftest --legacy` withholds the
        # cap and restores `min(deck, len - 1)`, which is what this module
        # shipped, so claim 12 is shown failing on the behaviour it was written
        # against rather than only passing on the behaviour that replaced it.
        return stack[min(deck, len(stack) - 1)]
    claimed = it.claimed_rungs(schema, profile, sector, ring)
    want = {lab: j for j, lab in claimed.items()}.get(deck, deck)
    for d in stack:
        if d["rung"] == want:
            return d
    canon = it.ring_radii(schema, profile, sector)
    z = _SECTOR_Z.get((id(schema), sector), (None, 0.0))[0]
    here = it.ring_radii(schema, profile, sector, z_m=z)
    a = canon[ring]["id"] if ring < len(canon) else "(none)"
    b = here[ring]["id"] if ring < len(here) else "(none)"
    if a != b and stack:
        _INDEXED[(sector, ring)] = (
            "ring index %d is %s at the sector's widest and %s at z %.1f m, so "
            "a register rung of %s has no counterpart in %s -- deck %d resolved "
            "POSITIONALLY to rung %d, r %.2f m"
            % (ring, a, b, z or 0.0, a, b, deck,
               stack[min(deck, len(stack) - 1)]["rung"],
               stack[min(deck, len(stack) - 1)]["floor_r_m"]))
        return stack[min(deck, len(stack) - 1)]
    raise ValueError(
        "shell_b: %s ring %d has no rung %d -- the hull leaves rungs %s over "
        "%.0f m of z, and belt_decks hands out rungs, not positions"
        % (sector, ring, deck, [d["rung"] for d in stack] or "none",
           _SECTOR_Z.get((id(schema), sector), (0, 0.0))[1]))


def indexed():
    """(sector, ring) -> why a Shell B deck there is a position and not a rung.

    Empty is the healthy state. A row here is an address this module cannot
    make unambiguous on its own; see `stack_entry`.
    """
    return dict(_INDEXED)


def reset_stacks():
    """Drop every cached stack. `--selftest` calls it when `_LEGACY` flips.

    The legacy control changes what a stack IS (see `belt_decks`), so a cache
    filled under one setting and read under the other would make the A/B a
    comparison of a thing with itself -- CLAUDE.md's vacuous-A/B defect.
    """
    _RING_STACK.clear()
    _SECTOR_Z.clear()
    _CAPPED.clear()
    _INDEXED.clear()
    _BELT_INDEX.clear()


def _min_headroom():
    """`tools/merge_cells.MIN_HEADROOM_M`, READ from the tool that refuses.

    Falls back to a stated 2.0 only if the tool cannot be loaded at all, and
    says so in the claim's own note rather than pretending it read it.
    """
    global _MIN_HEADROOM
    if _MIN_HEADROOM is None:
        import importlib.util                                    # noqa: PLC0415
        p = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "tools", "merge_cells.py")
        try:
            sp = importlib.util.spec_from_file_location("_mc_headroom", p)
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
            _MIN_HEADROOM = float(m.MIN_HEADROOM_M)
        except Exception:                                        # noqa: BLE001
            _MIN_HEADROOM = 2.0
    return _MIN_HEADROOM


_MIN_HEADROOM = None


def caps():
    """What the hull took off the belts, so a cap can never be silent.

    `--plan` prints it and `_selftest` claim 12 reads it. A belt capped to
    zero decks raises in `belt_decks` instead of appearing here: that is the
    "state it with numbers rather than clamping" case and there is nothing to
    redistribute over.
    """
    return dict(_CAPPED)


def _note_cap(belt, sector, ring, wanted, kept, why):
    if wanted != kept:
        _CAPPED[(belt["id"], sector, ring)] = (wanted, kept, why)
    else:
        _CAPPED.pop((belt["id"], sector, ring), None)


# --------------------------------------------------------------------------
# WHICH DECKS A BELT OWNS
# --------------------------------------------------------------------------
def belt_decks(schema, profile, belt):
    """`[(sector, ring, rung)]` for one belt, from the live ring stacks.

    A SHELL B DECK NUMBER IS A CANONICAL RUNG. `interior.decks_in_ring` returns
    two numbers per deck: `deck_index`, its POSITION in the list the hull leaves
    at this z, and `rung`, its number on the ring's one canonical ladder. This
    module used to hand out positions, and a position means nothing outside the
    z it was taken at -- grey ring 0 stacks 23 rungs and the hull leaves 11 over
    SHB-08's own z, so Shell B's "deck 10" was **rung 22**, while
    `cell_manifest.json`'s deck_table -- built z-blind, so its `deck_index` IS
    the rung -- reads deck 10 as rung 10, 43.2 m outboard. Rungs are the same
    number in both places by construction, so the ambiguity ends here rather
    than being translated somewhere downstream.

    Three rules, in order, and each is the row's own words rather than a
    default:

      1. the row states `decks N–M` — take the rungs of that range the hull
         leaves, and RAISE if the ring does not stack that far at its widest.
         `shb.py::_claim_decks` already checks the same thing from the spec
         side; a builder that clamped instead would build a belt into decks
         that do not exist and report success.
      2. the row names worked nodes (SHB-09) — resolve the PLC ids it cites to
         register rows and take the decks they land on. No ring range is stated
         because the belt is not a stack, and inventing one would be the
         `_claim_decks` failure this file's own harness declines to make.
      3. otherwise — every rung of the ring the hull leaves over the belt's
         own z.

    AND A RUNG THE REGISTER HAS ALREADY CLAIMED IS ADDRESSED BY THE REGISTER'S
    OWN LABEL FOR IT. That one line is the whole fix and it is worth stating
    why it is not the other obvious one.

    Grey ring 0 stacks 23 rungs, the register puts 19 places on them, and this
    rule used to read `range(n_hull)` -- POSITIONS in the hull-narrowed stack,
    so `deck 1` was rung 13 while Shell A called that same deck `grey_0_55`.
    Two names, one radius, and `tools/merge_cells.py::deck_headroom` refused
    the export over the resulting 0.000 m bands. It was right.

    THE FIRST FIX TRIED WAS `interior.free_rungs` ALONE -- give Shell B only
    the rungs no register place claims -- AND IT IS MEASURABLY WRONG. It takes
    SHB-04 from 32 decks of red rings 1-2 to the 18 the register leaves free,
    and the annex's own arithmetic assumes 32: 3,706,900 m² over 32 decks is
    the ~115,800 m²/deck `block_plan` is checked against. At 18 the belt needs
    **399.7 m of axial depth against red's 369 m** and pushes red ring 1 deck 8
    1.6 m outside the pressure hull -- claims 5 and 6 of `_selftest`, both
    failing, both real. The belts and the register genuinely SHARE decks: a
    landmark occupies part of a ring and housing occupies the rest, which is
    what `tools/export_station.py::work_list`'s `decks.setdefault` has always
    said ("38 of them at an address Shell A already owns").

    So sharing is kept and the NAMING is fixed. A claimed rung is addressed by
    `interior.claimed_rungs()[rung]` -- the register's own deck number for it --
    so the two shells produce ONE key for one deck and merge, instead of two
    keys 0.000 m apart. A free rung is addressed by the rung itself.

    ONE RESIDUE, DROPPED LOUDLY RATHER THAN LEFT AMBIGUOUS. The two addressing
    systems share the `sector_ring_deck` namespace, so a free rung whose NUMBER
    is also a register label elsewhere on the ring cannot be named: grey ring 0
    leaves rungs 19-22 free and carries places labelled 20 and 22 (at rungs 5
    and 6). Those two Shell B decks are refused, with the reason recorded in
    `caps()` and printed by `--plan`, because keeping them means a key that
    names two radii -- the exact defect this rule exists to end. Disambiguating
    the namespace itself belongs to `tools/export_station.py` and the manifest,
    which this module does not own.

    AND THEN CAPPED AT WHAT THE HULL LEAVES, WHICH IS A DIFFERENT QUESTION
    FROM RULE 1. Rule 1 asks the ring at the sector's widest cylinder and is
    about the SPEC: a row naming a deck the ring never stacks is a spec error
    and still raises. The cap asks `ring_stack` -- the same ring over the
    belt's own z span -- and is about the HULL: blue ring 0 stacks ten decks
    at its widest and six where SHB-01 actually is, so `decks 2–9` is eight
    decks of spec against four decks of ship.

    A belt keeps the OUTERMOST decks it asked for, because the hull takes the
    outer ones (narrowing moves `r_outer` inward and leaves `r_inner` alone),
    and its blocks redistribute over what is left: `_split_evenly` sums to the
    belt total by construction, and `deck_slots` shares the belt's gross by
    units-on-this-deck rather than by deck index, so BOTH the dwelling count
    and the gross survive the cap unchanged. What changes is density per deck.

    Nothing here is silent -- every cap is recorded in `caps()`, printed by
    `--plan`, and asserted against in `_selftest`.
    """
    sec, rings = belt["sector"], belt["rings"]
    if not rings:
        return _node_decks(belt)
    if belt["deck_lo"] is not None:
        n = len(it.decks_in_ring(schema, profile, sec, rings[0]))
        if belt["deck_hi"] >= n:
            raise ValueError(
                "%s houses on decks %d-%d and %s ring %d stacks %d (0..%d)"
                % (belt["id"], belt["deck_lo"], belt["deck_hi"], sec,
                   rings[0], n, n - 1))
        if _LEGACY:
            hi = min(belt["deck_hi"], n - 1)
            return [(sec, rings[0], d) for d in range(belt["deck_lo"], hi + 1)]
        # THE ROW'S `decks N–M` ARE RUNGS, NOT POSITIONS. On every ring a row
        # states a range for (blue 0-1, green 0) the register's own deck labels
        # are already valid indices, so `deck_index_for` returns them unchanged
        # and label == rung. Intersecting the range with the rungs the hull
        # leaves is therefore the row's own words and the ship's own shape,
        # with nothing in between: `min(deck_hi, n_hull - 1)` counted DECKS
        # against a range of NAMES and handed out `decks 2..4` of blue ring 0
        # while building rungs 7, 8 and 9.
        stack = ring_stack(schema, profile, sec, rings[0])
        keep, _drop = _address(schema, profile, sec, rings[0],
                              [d["rung"] for d in stack
                               if belt["deck_lo"] <= d["rung"]
                               <= belt["deck_hi"]])
        if not keep:
            # NOT CLAMPABLE AND NOT BUILDABLE. Every deck the belt names is
            # outside what the hull leaves, so there is nothing to redistribute
            # over. Say it with numbers.
            raise ValueError(
                "%s houses on decks %d-%d of %s ring %d and the hull leaves "
                "rungs %s over the belt's own %.0f m of z -- no deck of this "
                "belt can be built"
                % (belt["id"], belt["deck_lo"], belt["deck_hi"], sec, rings[0],
                   [d["rung"] for d in stack] or "none",
                   _SECTOR_Z.get((id(schema), sec), (0, 0.0))[1]))
        _note_cap(belt, sec, rings[0], belt["deck_hi"] - belt["deck_lo"] + 1,
                  len(keep),
                  "ring stacks %d at its widest, rungs %d-%d over the belt's "
                  "z span" % (n, stack[0]["rung"], stack[-1]["rung"]))
        return [(sec, rings[0], j) for j in keep]
    out = []
    for r in rings:
        wide = len(it.decks_in_ring(schema, profile, sec, r))
        if _LEGACY:
            out += [(sec, r, d) for d in range(wide)]
            _note_cap(belt, sec, r, wide, wide, "legacy: every deck of the "
                                                "ring at its widest")
            continue
        stack = ring_stack(schema, profile, sec, r)
        keep, drop = _address(schema, profile, sec, r,
                             [d["rung"] for d in stack])
        _note_cap(belt, sec, r, wide, len(keep),
                  "ring stacks %d at its widest, %d over the belt's z span"
                  % (wide, len(stack))
                  + ("" if not drop else
                     "; rung(s) %s refused -- the number is a register label "
                     "elsewhere on this ring and one key cannot name two radii"
                     % (drop,)))
        out += [(sec, r, j) for j in keep]
    return out


def _address(schema, profile, sector, ring, rungs):
    """`([address], [refused rung])` for a list of rungs of one ring.

    THE ONE PLACE THE TWO NAMING SYSTEMS MEET. Shell A addresses a deck by the
    register's own number for it; Shell B addresses one by its rung on the
    canonical ladder; both go into the same `sector_ring_deck` key. So a rung
    the register claims takes the register's name -- which is what makes the
    two shells MERGE on a shared deck instead of producing two keys at one
    radius -- and a free rung takes its own number.

    A free rung whose number is a register label of some OTHER rung on the same
    ring is refused rather than emitted, because there is no third name
    available and either choice would be a key that means two things. It is
    returned so the caller can record it; nothing here is silent.
    """
    claimed = it.claimed_rungs(schema, profile, sector, ring)   # rung -> label
    labels = set(claimed.values())
    keep, drop = [], []
    for j in rungs:
        if j in claimed:
            keep.append(claimed[j])
        elif j in labels:
            drop.append(j)
        else:
            keep.append(j)
    return keep, drop


def _node_decks(belt):
    """SHB-09's four worked nodes, resolved through the register."""
    import directory as DIR                                      # noqa: PLC0415
    keys = SPEC._plc_keys()
    seen = []
    for n in sorted({int(x) for x in re.findall(r"PLC-(\d+)", belt["text"])}):
        k = keys.get(n)
        if not k:
            continue
        try:
            p = DIR.by_key(k)
        except KeyError:
            continue
        if p["sector"] != belt["sector"]:
            continue
        t = (p["sector"], int(p["ring"]), _deck_index(p))
        if t not in seen:
            seen.append(t)
    if not seen:
        raise ValueError("%s: none of its PLC nodes resolve to a %s deck"
                         % (belt["id"], belt["sector"]))
    return sorted(seen)


def _deck_index(place):
    """A register row's deck NUMBER made into a stack index.

    Fifteen register rows carry a deck number no generated stack can index
    (Grey 40, 55, 80; Yellow 30) — `interior.ring_cells`' own comment records
    the crash. `deck.deck_index` ranks them; this module needs one number and
    does not own that file, so it clamps the same way `ring_cells` does and
    says so rather than raising in the middle of a belt.
    """
    try:
        return max(0, int(place["deck"]))
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------
# UNITS AND BLOCKS
# --------------------------------------------------------------------------
def unit_class_for_area(area_m2):
    """The `quarters.CLASSES` key whose area IS this ladder entry.

    RAISES for an area not on the ladder. `shb.py` asserts the same thing from
    the spec side ("%d m² is not on the INV-032 ladder"); a builder that
    invented a class for an unknown area would put the station's housing and
    its quarters generator on two different ladders.
    """
    k = UNIT_CLASS_BY_AREA.get(float(area_m2))
    if k is None:
        raise ValueError("%g m² is on no quarters class (ladder is %s)"
                         % (area_m2, sorted(UNIT_CLASS_BY_AREA)))
    return k


def block_plan(area_m2, n_units, seed, annex=()):
    """One residential block's dimensions, derived from `quarters.unit_dims`.

    A block is a double-loaded spine: units either side of a corridor, opening
    onto it, tiled along the station axis. So

        width  = 2 * unit depth + corridor + three walls   (across the ring)
        length = units on the busier side * unit frontage  (along the axis)

    THE SPLIT IS NOT HALF AND HALF, and that is a variety decision with a
    reason. Two adjacent blocks whose units both split 30/30 have party walls
    at identical axial stations for their whole length, which is `deck.py
    --degeneracy`'s question asked one scale down. The split is seeded within
    ±2 of half, so the two sides of one block are already offset from each
    other and no two blocks agree.

    Checked against the annex without being told: SHB-04's civilian block comes
    out 13.2 m x 94.9 m = 1,252 m², and 96 of those plus their support rooms is
    the row's own ~115,800 m²/deck. Nothing here was fitted to that number.
    """
    cls = unit_class_for_area(area_m2)
    w, d = Q.unit_dims(Q.class_by_key(cls))
    half = n_units // 2
    skew = 0 if _LEGACY else int(seed_of("skew", seed) % 5) - 2     # -2..+2
    left = max(1, min(n_units - 1, half + skew))
    right = n_units - left
    # THE BLOCK IS AS LONG AS AN EVEN SPLIT WOULD MAKE IT, AND THE SKEW DOES
    # NOT LENGTHEN IT. The first version took `max(left, right)`, so a +2 skew
    # bought two extra unit frontages of block for no extra units -- a
    # systematic **+3.3% on every block in the station**, which showed up as
    # SHB-04 building 123,485 m² against the annex's 115,841. The busier side
    # keeps its own pitch and the quieter side's units are simply a little
    # larger, which is what a real block does with an odd remainder; `block()`
    # already lays each side at `length / count`.
    n_side = (n_units + 1) // 2
    length = n_side * w
    width = 2 * d + CORRIDOR_W_M + 3 * WALL_T_M
    # THE COMMUNAL WASH ROOM IS PART OF THE BLOCK, and putting it on the ring
    # instead was worth 0.7% of the whole station. The derivation paragraph's
    # sanitation rule is "each block gets a communal wash room", and SHB-01 and
    # SHB-04 write it as `wash room per block` -- not as a count per deck like
    # every other room they list. Laid as its own ring slot it cost SHB-04 96
    # extra doors on the ring per deck and 374 m of arc to reach them; laid at
    # the quiet end of the block's own spine it costs nothing but its floor,
    # and it is where a resident actually meets it.
    ann = [(k, a) for k, a in annex]
    annex_m2 = sum(a for _k, a in ann)
    annex_l = annex_m2 / width if width > 0 else 0.0
    return {"class": cls, "unit_w_m": w, "unit_d_m": d,
            "left": left, "right": right, "n_side": n_side,
            "width_m": width, "length_m": length + annex_l,
            "unit_run_m": length, "annex": ann, "annex_l_m": annex_l,
            "net_m2": n_units * area_m2,
            "footprint_m2": width * (length + annex_l),
            "phase_m": (w / 2.0 if _LEGACY else _u("phase", seed) * w),
            "lobby": False if _LEGACY else seed_of("lobby", seed) % 3 == 0}


# --------------------------------------------------------------------------
# GEOMETRY PRIMITIVES -- boxes and quads, and nothing else
# --------------------------------------------------------------------------
def _box(v, t, g, name, lo, hi):
    """A closed box. `rooms._box`, restated for the import reason in `seed_of`."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    n = len(v)
    v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    t0 = len(t)
    for a, b, c, d in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                       (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)):
        t += [(n + a, n + b, n + c), (n + a, n + c, n + d)]
    g.append((name, t0, len(t)))
    return v, t, g


def _slab(v, t, g, name, x0, x1, y, z0, z1, up=True, step_m=ARC_STEP_M):
    """A horizontal plate, SUBDIVIDED ACROSS x.

    x becomes an arc under `deck._place_local` (`a = a0 + x/r`), so one quad
    spanning 70 m of x at r = 200 m is a chord that sags 1.5 m below the floor
    it stands in for. Subdividing at the kit's own ring-frame spacing (4.5 m)
    puts the worst sag at 6 mm, which is under `collision.MAX_SAG_M`.
    """
    n = max(1, int(math.ceil(abs(x1 - x0) / step_m)))
    t0 = len(t)
    for i in range(n):
        a = x0 + (x1 - x0) * i / n
        b = x0 + (x1 - x0) * (i + 1) / n
        k = len(v)
        v += [(a, y, z0), (b, y, z0), (b, y, z1), (a, y, z1)]
        if up:
            t += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
        else:
            t += [(k, k + 2, k + 1), (k, k + 3, k + 2)]
    g.append((name, t0, len(t)))
    return v, t, g


def _panel(v, t, g, name, x, y0, y1, z0, z1, face=1.0):
    """A vertical plate in the y-z plane at constant x, facing +x or -x."""
    k = len(v)
    t0 = len(t)
    v += [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]
    if face > 0:
        t += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
    else:
        t += [(k, k + 2, k + 1), (k, k + 3, k + 2)]
    g.append((name, t0, len(t)))
    return v, t, g


def _end(v, t, g, name, z, x0, x1, y0, y1, face=1.0, step_m=ARC_STEP_M):
    """A vertical plate in the x-y plane at constant z, subdivided across x."""
    n = max(1, int(math.ceil(abs(x1 - x0) / step_m)))
    t0 = len(t)
    for i in range(n):
        a = x0 + (x1 - x0) * i / n
        b = x0 + (x1 - x0) * (i + 1) / n
        k = len(v)
        v += [(a, y0, z), (b, y0, z), (b, y1, z), (a, y1, z)]
        if face > 0:
            t += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
        else:
            t += [(k, k + 2, k + 1), (k, k + 3, k + 2)]
    g.append((name, t0, len(t)))
    return v, t, g


# --------------------------------------------------------------------------
# A BLOCK
# --------------------------------------------------------------------------
def block(area_m2, n_units, seed, lod=1, plan=None):
    """One residential block: 60 doors on a spine, at Shell B detail.

    Local frame is `rooms.build`'s and `deck._place_local`'s: **x across the
    ring, y up from the deck, z along the station axis, and the way IN is +z**
    — the end the ring corridor arrives at. Nothing here is curved; the bend
    happens in `_place_local`, which is why every long run in x is subdivided.

    `lod` is the one dial and it is honest about what it buys:

      lod 1  unit interiors are built — party walls, back walls, floor and
             soffit inside every unit. The unit is enterable, which is what
             SHB-01's own CHECK asks for ("a real, enterable, numbered unit").
      lod 0  the corridor FACE only — pier, door head, jamb, and a sealed back
             wall. Half the triangles; a door you can see and not enter.

    Both are measured by `--deck --lod`, because a LOD claim with one number is
    a LOD claim nobody can price.
    """
    p = plan or block_plan(area_m2, n_units, seed)
    w, d = p["unit_w_m"], p["unit_d_m"]
    hw = p["width_m"] / 2.0
    ln = p["length_m"]
    run = p.get("unit_run_m", ln)              # where the units stop
    ch = Q.UNIT_H_M
    cw2 = CORRIDOR_W_M / 2.0
    v, t, g = [], [], []
    prof = C.corridor_profile()
    spine_h = min(prof["ceil_y"], ch)

    # --- the spine: deck, soffit, skirt, light -----------------------------
    _slab(v, t, g, G["spine_deck"], -cw2, cw2, 0.0, -ln, 0.0)
    _slab(v, t, g, G["spine_soffit"], -cw2, cw2, spine_h, -ln, 0.0, up=False)
    # THE SKIRT IS A BOX, NOT A PLATE, AND THAT IS A MEASUREMENT DECISION.
    # As a zero-thickness horizontal plate at y = 0.08 it was invisible to
    # `block_profile`'s sideways rays -- which then reported a half width of
    # exactly `CORRIDOR_W_M / 2`, the constant it was supposed to be measuring
    # INSTEAD of. A measured number that can only ever equal the written-down
    # one is the "default nobody chose" trap this project already has a note
    # about; as a 60 mm solid it is a real intrusion and the ray cast has
    # something to find.
    for s in (-1, 1):
        _box(v, t, g, G["spine_skirt"],
             (min(s * cw2, s * (cw2 - 0.06)), 0.0, -ln),
             (max(s * cw2, s * (cw2 - 0.06)), 0.14, 0.0))
    _slab(v, t, g, G["spine_light"], -0.16, 0.16, spine_h - 0.05, -ln, 0.0,
          up=False)

    # --- the block's outer walls and the two ends ---------------------------
    for s in (-1, 1):
        _panel(v, t, g, G["unit_wall"], s * hw, 0.0, ch, -ln, 0.0, face=-s)
    _end(v, t, g, G["unit_wall"], -ln, -hw, hw, 0.0, ch, face=1.0)

    # The +z end is the way in: wall either side of a corridor-width aperture.
    _end(v, t, g, G["unit_wall"], 0.0, -hw, -cw2, 0.0, ch, face=-1.0)
    _end(v, t, g, G["unit_wall"], 0.0, cw2, hw, 0.0, ch, face=-1.0)
    _end(v, t, g, G["unit_wall"], 0.0, -cw2, cw2, spine_h, ch, face=-1.0)

    # --- the units ----------------------------------------------------------
    # Doors are cut in the spine walls at each unit's centre, phase-shifted by
    # the block's seed so two blocks side by side do not present the same
    # rhythm. The phase is bounded by one frontage so a door never leaves its
    # own unit.
    doors = []
    for side, count in ((-1, p["left"]), (1, p["right"])):
        x_in = side * cw2                       # the spine face
        x_out = side * (cw2 + d)                # the unit's back wall
        pitch = run / count
        for i in range(count):
            zc = -run + (i + 0.5) * pitch
            zc += (p["phase_m"] - w / 2.0) * 0.25
            zc = min(max(zc, -run + DOOR_W_M), -DOOR_W_M / 2.0)
            z0, z1 = zc - DOOR_W_M / 2.0, zc + DOOR_W_M / 2.0
            doors.append((side, zc))
            # Spine wall: the pier before the door, and the head above it.
            zp = -run + i * pitch
            _panel(v, t, g, G["unit_pier"], x_in, 0.0, ch, zp, z0, face=-side)
            _panel(v, t, g, G["unit_head"], x_in, DOOR_H_M, ch, z0, z1,
                   face=-side)
            if i == count - 1:
                _panel(v, t, g, G["unit_pier"], x_in, 0.0, ch, z1,
                       -run + (i + 1) * pitch, face=-side)
            # The reveal a player looks straight into. Two jambs and a soffit;
            # session 3x's finding is that the doorway is where a player looks
            # closest, and it is the one place Shell B spends triangles.
            for zz in (z0, z1):
                _end(v, t, g, G["unit_jamb"], zz, x_in, x_in + side * WALL_T_M,
                     0.0, DOOR_H_M, face=1.0 if zz == z0 else -1.0,
                     step_m=WALL_T_M)
            _slab(v, t, g, G["unit_jamb"], x_in, x_in + side * WALL_T_M,
                  DOOR_H_M, z0, z1, up=False, step_m=WALL_T_M)
            if lod >= 1:
                # The unit itself: floor, soffit, party wall, and the far face
                # of the spine wall so the room is closed.
                _slab(v, t, g, G["unit_deck"], x_in, x_out, 0.0, zp,
                      -run + (i + 1) * pitch)
                _slab(v, t, g, G["unit_soffit"], x_in, x_out, ch, zp,
                      -run + (i + 1) * pitch, up=False)
                _panel(v, t, g, G["unit_pier"], x_in + side * WALL_T_M,
                       0.0, ch, zp, z0, face=side)
                _panel(v, t, g, G["unit_head"], x_in + side * WALL_T_M,
                       DOOR_H_M, ch, z0, z1, face=side)
                if i == count - 1:
                    _panel(v, t, g, G["unit_pier"], x_in + side * WALL_T_M,
                           0.0, ch, z1, -run + (i + 1) * pitch, face=side)
                if i:
                    _end(v, t, g, G["unit_party"], zp, x_in, x_out, 0.0, ch,
                         face=1.0)
                    _end(v, t, g, G["unit_party"], zp + WALL_T_M, x_in, x_out,
                         0.0, ch, face=-1.0)
        if lod < 1:
            # Sealed: one plate standing in for every unit on this side.
            _slab(v, t, g, G["unit_deck"], x_in, x_out, 0.0, -run, 0.0)
            _slab(v, t, g, G["unit_soffit"], x_in, x_out, ch, -run, 0.0,
                  up=False)

    # --- the block's own annexe rooms, at the quiet end of the spine --------
    #
    # The communal wash room, and anything else the belt states "per block".
    # Built off the far end because that is the end away from the ring
    # corridor: a resident walks past every door in the block to reach it,
    # which is the class texture the derivation paragraph names when it says
    # the absence of private showers "is walkable class texture".
    at = -run
    for kind, a_m2 in p.get("annex", ()):
        seg = a_m2 / max(p["width_m"], 1e-9)
        z1, z0 = at, at - seg
        _slab(v, t, g, G["room_deck"], -hw, hw, 0.0, z0, z1)
        _slab(v, t, g, G["room_soffit"], -hw, hw, PROGRAM[kind][3], z0, z1,
              up=False)
        _end(v, t, g, G["room_wall"], z1, -hw, -DOOR_W_M / 2.0, 0.0, ch,
             face=-1.0)
        _end(v, t, g, G["room_wall"], z1, DOOR_W_M / 2.0, hw, 0.0, ch,
             face=-1.0)
        _end(v, t, g, G["room_head"], z1, -DOOR_W_M / 2.0, DOOR_W_M / 2.0,
             DOOR_H_M, ch, face=-1.0, step_m=DOOR_W_M)
        n = max(1, int((hw * 2 - 1.0) // 1.6))
        for i in range(n):
            xc = -hw + 0.5 + i * 1.6
            _box(v, t, g, G["room_fit"], (xc, 0.0, z0 + 0.4),
                 (xc + 1.1, 0.9, z0 + 1.0))
        at = z0

    # --- the end lobby, on the blocks whose hash says so --------------------
    if p["lobby"]:
        _box(v, t, g, G["room_fit"],
             (-cw2 + 0.2, 0.0, -ln + 0.3), (-cw2 + 0.7, 0.45, -ln + 2.1))
        _box(v, t, g, G["room_fit"],
             (cw2 - 0.7, 0.0, -ln + 0.3), (cw2 - 0.2, 0.45, -ln + 2.1))

    p.update(triangles=len(t), doors=doors, ceiling_m=ch, spine_h_m=spine_h,
             lod=lod)
    return v, t, g, p


# --------------------------------------------------------------------------
# A SUPPORT ROOM
# --------------------------------------------------------------------------
def room_dims(kind, area_m2):
    """(width across the ring, length along the axis) for a program room."""
    fam, aspect, floor_m2, _h = PROGRAM[kind]
    a = max(area_m2, floor_m2)
    length = math.sqrt(a * aspect)
    return a / length, length


def support_room(kind, area_m2, seed):
    """A mess room, wash room, store, shop, plant room or partition.

    Same frame as `block()`: the way in is +z. Low detail is four walls, a
    deck, a soffit, a doorway and the one fitting the room is named for — a
    bench in a shop, a skid in a plant room, a run of tables in a mess. That
    last item is not decoration: `rooms.py`'s own lesson is that a room built
    from its interactables alone is *"controls without machinery"*, and a wash
    room with nothing in it is a cupboard with a sign on it.
    """
    fam, _asp, _floor, ch = PROGRAM[kind]
    w, ln = room_dims(kind, area_m2)
    hw = w / 2.0
    v, t, g = [], [], []
    _slab(v, t, g, G["room_deck"], -hw, hw, 0.0, -ln, 0.0)
    _slab(v, t, g, G["room_soffit"], -hw, hw, ch, -ln, 0.0, up=False)
    for s in (-1, 1):
        _panel(v, t, g, G["room_wall"], s * hw, 0.0, ch, -ln, 0.0, face=-s)
    _end(v, t, g, G["room_wall"], -ln, -hw, hw, 0.0, ch, face=1.0)
    # The +z end carries the door.
    dx = min(DOOR_W_M / 2.0, hw - 0.3)
    off = (_u("door", kind, seed) - 0.5) * max(0.0, (hw - dx) * 1.2)
    off = max(-(hw - dx), min(hw - dx, off))
    _end(v, t, g, G["room_wall"], 0.0, -hw, off - dx, 0.0, ch, face=-1.0)
    _end(v, t, g, G["room_wall"], 0.0, off + dx, hw, 0.0, ch, face=-1.0)
    _end(v, t, g, G["room_head"], 0.0, off - dx, off + dx, DOOR_H_M, ch,
         face=-1.0, step_m=DOOR_W_M)

    # The fitting. Count and size derive from the room, not from a table of
    # furniture: a bigger mess seats more people in the same 1.5 m module.
    if fam in ("hall",):
        rows = max(1, int((ln - 2.4) // 3.0))
        for i in range(rows):
            zc = -ln + 1.4 + i * 3.0
            _box(v, t, g, G["room_fit"], (-hw + 0.8, 0.0, zc),
                 (hw - 0.8, 0.75, zc + 1.0))
    elif fam in ("plant", "shop"):
        n = max(1, int((ln - 1.6) // 2.6))
        for i in range(n):
            zc = -ln + 0.9 + i * 2.6
            _box(v, t, g, G["plant_fit"] if fam == "plant" else G["room_fit"],
                 (-hw + 0.5, 0.0, zc), (-hw + 1.7, 1.9 if fam == "plant" else
                                        0.95, zc + 1.6))
    elif fam in ("room",):
        n = max(1, int((ln - 1.0) // 2.0))
        for i in range(n):
            zc = -ln + 0.6 + i * 2.0
            for s in (-1, 1):
                _box(v, t, g, G["room_fit"],
                     (s * (hw - 0.6), 0.0, zc), (s * hw - s * 0.05, 1.8,
                                                 zc + 1.2))
    elif fam == "depot":
        _box(v, t, g, G["plant_fit"], (-hw + 1.0, 0.0, -ln + 1.0),
             (-hw + 2.2, 1.2, -1.0))
    # a partition has nothing in it, and the emptiness is the content
    return v, t, g, {"kind": kind, "family": fam, "width_m": w,
                     "length_m": ln, "area_m2": w * ln, "ceiling_m": ch,
                     "triangles": len(t)}


# --------------------------------------------------------------------------
# THE DECK PLAN -- what stands where, around the ring
# --------------------------------------------------------------------------
def deck_slots(schema, profile, sector, ring, deck):
    """Every block and room on one deck, in ring order, with its arc.

    THE AREA BUDGET IS DERIVED, NOT PICKED, and this is where build-to-spec
    actually happens:

        gross (the row's own ≈ figure, per deck)
      − the blocks' footprints (their own geometry, `block_plan`)
      − the ring corridor's footprint (its own geometry)
      = what the program rooms may occupy, split between them in proportion to
        `PROGRAM`'s minima.

    So the generated area lands on the annex's stated gross BY CONSTRUCTION, and
    the only way it can miss is if the blocks and the corridor already exceed
    it — which is a real finding, is reported as `over_m2`, and fails
    `--selftest`.

    THE ORDER IS A SEEDED PERMUTATION and that is the degeneracy gate's
    business, not taste. Laid in program order every deck in a belt would
    present the same sequence of doors to a player walking the ring, which is
    128 identical rooms wearing 128 names — the exact blind spot session 4h
    found. `--legacy` lays them in program order and `--selftest --degeneracy`
    shows it collapsing.
    """
    owners = deck_belts(schema, profile, sector, ring, deck)
    if not owners:
        return None
    # THE RADIUS IS WHAT THE HULL LEAVES OVER THE BELT'S OWN z SPAN, not what
    # the sector's widest cylinder allows, and getting that wrong put **14 of
    # 101 decks outside the pressure hull, the worst by 37.2 m**. It is the
    # same defect `interior.decks_in_ring` records for `qtr_command`, `war_room`
    # and two others -- "the RING was there and the DECK inside it was not" --
    # arriving on a belt instead of a place, and CLAUDE.md carries "places
    # outside the pressure hull: 0 of 129 (was 34)" as a number somebody paid
    # for.
    #
    # IT IS ONE STACK PER RING AND IT IS ASKED FOR EXACTLY ONCE. This used to
    # read `decks_list[min(deck, len(decks_list) - 1)]`, which is the clamp
    # that put fifteen decks of this station at a radius another deck already
    # had -- see `ring_stack`. There is no clamp here now: `belt_decks` has
    # already capped the belt to what the stack holds, so an index past its end
    # is a bug in the cap and raises rather than resolving to a neighbour.
    d = stack_entry(schema, profile, sector, ring, deck)
    r = d["floor_r_m"]
    circ = 2 * math.pi * r
    ids = "+".join(o["belt"]["id"] for o in owners)

    # --- blocks and program, belt by belt -----------------------------------
    #
    # A DECK CAN HAVE TWO OWNERS AND THEY MUST NOT BE MERGED FIRST. Grey ring 0
    # carries SHB-08 (per-deck program, 36,000 m²) and SHB-08.f (a whole-belt
    # count of 13,000 partitions, 163,800 m²). The first version merged the two
    # rows into one synthetic belt and divided the partitions by the deck count
    # inside the merge -- `13,000 // 23 * 23` -- which built **12,995**
    # partitions for 13,000 refugees and lost five families to integer
    # division. Each belt is now split by `_split_evenly`, which is exact by
    # construction, and the deck is the union of what its owners ask for.
    blocks, prog, gross_deck = [], {}, 0.0
    for o in owners:
        belt, n_decks, idx = o["belt"], o["decks"], o["index"]
        seed = ("shb", belt["id"], sector, ring, deck)
        # `wash room per block` is an ANNEXE OF THE BLOCK, not a ring slot --
        # see `block_plan`. It takes its stated minimum area rather than a
        # share of the belt's leftover gross, because it is sized to the block
        # it serves and the block count is fixed by the annex.
        ann = tuple((k, PROGRAM[k][2]) for k in belt["per_block"])
        mine = []
        for ci, (nb, per, area) in enumerate(belt["clauses"]):
            area = area if area is not None else _pair_area(belt, ci)
            share = _split_evenly(nb, n_decks)[idx]
            for k in range(share):
                s = _seed(*seed, "block", ci, k)
                mine.append({"kind": "block", "area_m2": area, "units": per,
                             "seed": s,
                             "plan": block_plan(area, per, s, annex=ann)})
        # SHB-06 states its unit areas as a SPLIT of the block total rather
        # than on the clause; the blocks are re-typed here so the breather zone
        # extensions are 22 m² units and the rest are 16 m².
        if belt["pairs"] and any(a is None for _n, _p, a in belt["clauses"]):
            mine = _retype_from_pairs(belt, mine, n_decks, idx, seed)
        blocks += mine
        mine_prog = {}
        for kind, n in belt["program"].items():
            mine_prog[kind] = (n if belt["per_deck"]
                               else _split_evenly(n, n_decks)[idx])
        for kind, (n, every) in belt["per_n_decks"].items():
            if idx % every == 0:
                mine_prog[kind] = mine_prog.get(kind, 0) + n
        for kind, n in mine_prog.items():
            prog[kind] = prog.get(kind, 0) + n
        # THIS DECK'S SHARE OF THE BELT'S GROSS FOLLOWS ITS CONTENT, NOT ITS
        # INDEX, and a flat `gross / n_decks` was worth 4.4%. SHB-01 puts 62
        # blocks on 8 decks — 7.75 each, so six decks carry 8 and two carry 7 —
        # and a flat share charged every deck for 7.75 blocks while building
        # eight. The overshoot looked like a geometry problem (it was reported
        # as "the blocks are too big") and was an accounting one: the deck with
        # more housing on it is owed more of the belt's gross.
        share = 1.0 / float(n_decks)
        if _LEGACY:
            pass                       # the flat share the first version used
        elif belt["units"]:
            share = sum(x["units"] for x in mine) / float(belt["units"])
        elif belt["program"] and not belt["per_deck"]:
            tot_prog = sum(belt["program"].values())
            if tot_prog:
                share = sum(mine_prog.get(k, 0)
                            for k in belt["program"]) / float(tot_prog)
        gross_deck += belt["gross_m2"] * share
    prog = {k: v for k, v in prog.items() if v > 0}
    if not blocks and not prog:
        # A deck the belt's own division left nothing for. SHB-05 spreads 23
        # rooms over Red ring 3's 14 decks, so two decks get none — and a deck
        # with no program is not a Shell B deck. Saying so beats building an
        # empty ring corridor and charging the belt for it.
        return None
    seed = ("shb", ids, sector, ring, deck)

    # --- refugee partitions are HALLS, not 13,000 doors off a ring ----------
    #
    # SHB-08.f's own words are "partitioned converted-cargo volume ... communal
    # standpipes", and reading it the other way was measurably wrong rather
    # than merely inelegant. Laid as 13,000 individually-doored 9 m² rooms the
    # belt needs 1,384 m of arc for the partitions and another 353 m for the
    # gaps between them, so the ring corridor alone came to 4,680 m² against a
    # whole-deck budget of 8,687 — the annex's ×1.4 allows **0.28 m² of
    # circulation per partition**, which is not enough corridor to reach one.
    #
    # A hall of 60 partitions off one spine is the same geometry as SHB-04's
    # transient block (`quarters` class `transient`, 9 m², the same ladder
    # entry) and costs one door on the ring instead of sixty. 60 is
    # `arrival.py:573 UNITS_PER_BLOCK`, which the derivation paragraph already
    # makes the station's housing quantum — not a number chosen here.
    n_part = prog.pop("partition", 0)
    if n_part:
        per = belts()["SHB-08.f"]["units_per_block"] or 1
        per = UNITS_PER_HALL
        area = float(belts()["SHB-08.f"]["partition_area_m2"])
        left = n_part
        k = 0
        while left > 0:
            take = min(per, left)
            s = _seed(*seed, "partition", k)
            blocks.append({"kind": "block", "partition": True,
                           "area_m2": area, "units": take, "seed": s,
                           "plan": block_plan(area, take, s)})
            left -= take
            k += 1
    block_m2 = sum(x["plan"]["footprint_m2"] for x in blocks)

    weight = sum(PROGRAM[k][2] * n for k, n in prog.items())
    # THE RING CORRIDOR IS CHARGED FOR THE ARC IT ACTUALLY SERVES, and the
    # first version charged for the whole circle. That is not a rounding
    # difference: Grey ring 0 is 2,735 m around, so a closed ring corridor is
    # 7,110 m² against the deck's whole 8,687 m² budget -- **82% of a
    # residential belt spent on corridor nobody's door opens off**, and it put
    # the station 9.9% over the annex's stated gross with the overshoot
    # concentrated entirely in the belts that have no housing.
    #
    # An arc with no slot on it is not Shell B at all: `docs/spec/PLACES.md` §3
    # SHC-11 already owns unbuilt ring fabric -- "capped / sheeted / welded-shut
    # openings, stencilled UNCOMMISSIONED". So the corridor is sized in two
    # passes: lay the slots first to learn the arc they occupy, then charge for
    # that arc. Charging for it needs the rooms' widths, and their AREAS are
    # what is left after charging for it -- so the two are solved together, by
    # six fixed-point passes rather than by a formula. Six because the map is a
    # square root and converges to under a square metre in three; the extra
    # three cost nothing and the residual is printed rather than assumed.
    #
    # SUM OF BAND ARCS == TOTAL ARC LAID, exactly, whether the slots wrap into
    # one band or nine: a full band is the whole circumference and the last one
    # is the remainder. So the estimate below is not an approximation of the
    # banding, only of the room widths it is iterating toward.
    n_slots = len(blocks) + sum(prog.values())
    block_arc = sum(x["plan"]["width_m"] for x in blocks)
    budget = gross_deck - block_m2
    for _pass in range(6):
        arc = block_arc + n_slots * SLOT_GAP_M
        for kind, n in prog.items():
            a = max(PROGRAM[kind][2],
                    (budget * PROGRAM[kind][2] / weight) if weight > 0 else 0.0)
            arc += n * math.sqrt(a / PROGRAM[kind][1])
        ring_m2 = arc * RING_W_M
        budget = gross_deck - block_m2 - ring_m2
    # THE LEGACY CONTROL WITHHOLDS THE DERIVATION AND NOTHING ELSE. Every room
    # takes its stated minimum instead of its share of the belt's own leftover
    # gross, which is what a builder that had never read the annex's ≈ figure
    # would produce. It is the A/B that shows the area claim is doing work.
    if _LEGACY:
        budget = 0.0
    rooms = []
    for kind, n in sorted(prog.items()):
        for k in range(n):
            share = (budget * PROGRAM[kind][2] / weight) if weight > 0 else 0.0
            a = max(PROGRAM[kind][2], share)
            rooms.append({"kind": kind, "area_m2": a,
                          "seed": _seed(*seed, "room", kind, k)})
    room_m2 = 0.0
    for x in rooms:
        w, ln = room_dims(x["kind"], x["area_m2"])
        x["width_m"], x["length_m"] = w, ln
        room_m2 += w * ln

    slots = blocks + rooms
    if not _LEGACY:
        slots = [slots[i] for i in _shuffle(range(len(slots)), *seed, "order")]

    # --- lay them round the ring, wrapping into axial bands -----------------
    ex = schema["sectors"]["extents_m"][sector]
    z_span = ex["z1"] - ex["z0"]
    # TWO PASSES, AND THE FIRST VERSION HAD ONE. A slot is built with its way
    # in at local +z and its body running back to -z, so a band's ring corridor
    # sits at the HIGH end of the block it serves. Placing the first band's
    # corridor at the sector's own `z0` therefore ran every block on the deck
    # 94 m out through the bulkhead -- red/1/5 came back spanning z 6,331 to
    # 6,527 with the sector running 6,425 to 6,794. The depth of a band is not
    # known until its slots are laid, so the arcs are laid first and the z of
    # each band's corridor is assigned after, at `z0 + sum of the depths so
    # far`. `fits_z` is the assertion that the whole stack still lands inside
    # the sector, and `_selftest` runs it over all 101 decks.
    band_at, arc_at = 0, 0.0
    band_depth, band_arc = {}, {}
    for s in slots:
        w = (s["plan"]["width_m"] if s["kind"] == "block" else s["width_m"])
        ln = (s["plan"]["length_m"] if s["kind"] == "block" else s["length_m"])
        if arc_at + w + SLOT_GAP_M > circ:
            band_at, arc_at = band_at + 1, 0.0
        s["band"] = band_at
        s["arc_m"] = arc_at + w / 2.0
        s["angle_deg"] = math.degrees((arc_at + w / 2.0) / r)
        s["width_used_m"] = w
        s["length_used_m"] = ln
        band_depth[band_at] = max(band_depth.get(band_at, 0.0), ln)
        arc_at += w + SLOT_GAP_M
        band_arc[band_at] = min(circ, arc_at)
    bands = band_at + 1
    band_z, at = {}, ex["z0"] + RING_W_M
    for b in range(bands):
        at += band_depth.get(b, 0.0)
        band_z[b] = at
        at += RING_W_M
    for s in slots:
        s["z_m"] = band_z[s["band"]]
    depth = at - ex["z0"]

    # The hull is re-asked with this depth by `_settle_sector`, at RING level,
    # over the deepest belt the ring carries. It used to be re-asked HERE, per
    # deck -- which is what let two decks of one ring answer from two different
    # stacks -- and it never ran at all, because `for _pass in range(6):` above
    # rebinds the recursion guard's own name. See `_settle_sector`.
    ring_arc_m = sum(band_arc.values())
    ring_m2 = (circ * bands if _LEGACY else ring_arc_m) * RING_W_M

    built = block_m2 + room_m2 + ring_m2
    return {
        "belt": ids, "sector": sector, "ring": ring, "deck": deck,
        # THE ADDRESS AND THE LADDER NUMBER, BOTH, because they are not
        # always the same integer and every consumer needs to know which
        # it is holding. `deck` is the streaming key; `rung` is the one
        # number `cell_manifest.json`'s z-blind `deck_index` also is.
        "rung": d["rung"],
        "radius_m": r, "circumference_m": circ, "use": d["use"],
        "gravity_g": d["floor_g"],
        "z0": ex["z0"], "z_span_m": z_span, "bands": bands, "depth_m": depth,
        "band_arc_m": band_arc, "ring_arc_m": ring_arc_m,
        "ring_closed": all(v >= circ - 1e-6 for v in band_arc.values()),
        "gross_target_m2": gross_deck, "block_m2": block_m2,
        "room_m2": room_m2, "ring_m2": ring_m2,
        "built_m2": built, "over_m2": max(0.0, built - gross_deck),
        "budget_m2": budget,
        "blocks": len([s for s in slots if s["kind"] == "block"]),
        "units": sum(s["units"] for s in slots
                     if s["kind"] == "block" and not s.get("partition")),
        "partitions": sum(s["units"] for s in slots if s.get("partition")),
        "program": prog, "slots": slots,
        "fits_z": depth <= z_span,
    }


def _pair_area(belt, ci):
    """The unit area for a clause that states none -- SHB-06's `@22`/`@16` split."""
    if belt["pairs"]:
        return float(belt["pairs"][0][1])
    raise ValueError("%s clause %d states no unit area and no @m² split"
                     % (belt["id"], ci))


def _retype_from_pairs(belt, blocks, n_decks, idx, seed):
    """Give this deck its share of each `@m²` band in SHB-06's split.

    The row provides 236 blocks x 60 and then splits the 14,160 units
    `6,250 @22 m²` + `7,910 @16 m²`. Blocks are whole, so the 22 m² band takes
    `ceil(6,250/60)` = 105 blocks and the rest are 16 m². Spread over the
    belt's decks by the same even split every other count uses, so a deck's mix
    is a property of the deck rather than of the order blocks were made in.
    """
    per = belt["units_per_block"]
    want = []
    for n_units, area in belt["pairs"]:
        want.append((int(math.ceil(n_units / float(per))), float(area)))
    total = sum(n for n, _a in want)
    if total < len(blocks):
        want[-1] = (want[-1][0] + (len(blocks) - total), want[-1][1])
    shares = []
    for n, area in want:
        shares.append((_split_evenly(n, n_decks)[idx], area))
    out, at = [], 0
    for n, area in shares:
        for _k in range(n):
            if at >= len(blocks):
                break
            b = blocks[at]
            b["area_m2"] = area
            b["plan"] = block_plan(area, b["units"], b["seed"])
            out.append(b)
            at += 1
    out += blocks[at:]
    return out


def _split_evenly(total, n):
    """`total` split over `n` decks so the parts sum to `total` exactly.

    The remainder goes to the LOW decks, deterministically. A `round()` per
    deck loses or gains blocks -- 2,361 over 32 decks is 73.78, and rounding
    every deck to 74 provides 2,368, which is seven blocks the annex never
    authorised and 420 units of housing nobody counted.
    """
    if n <= 0:
        return []
    if _LEGACY:
        return [int(round(total / float(n)))] * int(n)
    base, rem = divmod(int(total), int(n))
    return [base + (1 if i < rem else 0) for i in range(n)]


_BELT_INDEX = {}


def deck_belts(schema, profile, sector, ring, deck):
    """Every belt that owns this deck: `[{belt, decks, index}]`, or `[]`.

    A LIST, NOT ONE ROW. Grey ring 0 is owned twice — SHB-08's industrial
    support and SHB-08.f's 13,000 refugee partitions — and the two rows have
    different shapes (one is per deck, one is a belt total). Returning a single
    merged belt cost five partitions to integer division; see `deck_slots`.
    """
    key = (id(schema), sector)
    if key not in _BELT_INDEX:
        idx = {}
        for b in sorted(belts().values(), key=lambda x: x["id"]):
            if b["sector"] != sector:
                continue
            ds = belt_decks(schema, profile, b)
            for i, t in enumerate(ds):
                idx.setdefault(t, []).append({"belt": b, "decks": len(ds),
                                              "index": i})
        _BELT_INDEX[key] = idx
    return _BELT_INDEX[key].get((sector, ring, deck), [])


# --------------------------------------------------------------------------
# BUILDING A DECK
# --------------------------------------------------------------------------
def build_deck(schema, profile, sector, ring, deck, lod=1, cells=None,
               place=True, rings=True):
    """Every slot on one deck, plus the ring corridor that reaches them.

    `cells` restricts the build to a set of streaming-cell indices from
    `interior.ring_cells`, which is how this is meant to be consumed: a deck of
    SHB-04 is 96 blocks and nobody renders 96 blocks at once. `--deck` with no
    `--cell` builds the whole deck so the per-deck numbers can be measured
    once; the engine asks for one cell.

    `place=False` leaves every slot in its own local frame, which is what the
    degeneracy hash wants: two decks placed at different angles differ
    trivially, and the question is whether their CONTENT differs.
    """
    plan = deck_slots(schema, profile, sector, ring, deck)
    if plan is None:
        return [], [], [], {"built": False, "why": "no belt owns this deck"}
    import deck as DK                                            # noqa: PLC0415
    r = plan["radius_m"]
    # THE CELL PLAN IS ASKED FOR BY RUNG, NOT BY ADDRESS. `ring_cells`
    # subscripts the ring's z-blind stack, where index == rung, and it
    # RAISES for a register deck NUMBER -- `grey_0_50` is a name. The
    # address is one or the other (`_address`), so the rung is taken from
    # the stack row rather than from the key.
    cellplan = it.ring_cells(schema, profile, sector, ring,
                             plan["rung"])
    want = None if cells is None else set(cells)

    V, T, Gs = [], [], []
    n_slot = 0
    for s in plan["slots"]:
        ci = int(s["angle_deg"] // cellplan["cell_deg"]) % cellplan["cells"]
        s["cell"] = ci
        if want is not None and ci not in want:
            continue
        if s["kind"] == "block":
            v, t, g, meta = block(s["area_m2"], s["units"], s["seed"],
                                  lod=lod, plan=s["plan"])
        else:
            v, t, g, meta = support_room(s["kind"], s["area_m2"], s["seed"])
        s["triangles"] = meta["triangles"]
        if place:
            v = DK._place_local(v, r, s["angle_deg"], s["z_m"])
        _append(V, T, Gs, v, t, g, "z%d_%s%d" % (int(s["z_m"]), s["kind"][:4],
                                                 n_slot))
        n_slot += 1

    # --- the ring corridor, over the arc its own band actually occupies -----
    #
    # NOT THE WHOLE CIRCLE. `deck_slots` records `band_arc[band]` -- how far
    # round the ring that band's slots reach -- and the corridor stops there.
    # Beyond it the deck is SHC-11 fabric ("UNCOMMISSIONED — B5 CONSTRUCTION
    # CONTRACT 5 — NO SERVICES"), which is a stencil somebody else owns and not
    # 2.7 km of empty corridor charged to a residential belt.
    for band in range(plan["bands"]) if rings else ():
        arcs = [s for s in plan["slots"] if s["band"] == band]
        if not arcs:
            continue
        z = arcs[0]["z_m"]
        reach = plan["band_arc_m"].get(band, 0.0)
        cell_m = 2 * math.pi * r * (cellplan["cell_deg"] / 360.0)
        for ci in range(cellplan["cells"]):
            if want is not None and ci not in want:
                continue
            a_m = ci * cell_m
            if a_m >= reach - 1e-6:
                break
            deg = math.degrees(min(cell_m, reach - a_m) / r)
            a0 = ci * cellplan["cell_deg"]
            v, t, g = ring_run(r, a0, deg, place=place)
            if place:
                v = DK._place_local(v, r, a0, z - RING_W_M / 2.0)
            _append(V, T, Gs, v, t, g, "z%d_ring%d_%d" % (int(z), band, ci))

    meta = dict(plan)
    meta.update(built=True, triangles=len(T), groups=len(Gs), lod=lod,
                slots_built=n_slot, cells=cellplan["cells"],
                cell_deg=cellplan["cell_deg"],
                tri_per_m2=len(T) / max(plan["built_m2"], 1e-9))
    meta.pop("slots", None)
    meta["slot_table"] = plan["slots"]
    return V, T, Gs, meta


def ring_run(r, start_deg, degrees, place=True):
    """One cell's worth of Shell B ring corridor, in the local frame.

    NOT `interior.ring_arc`, and the reason is the whole argument for this
    file. That function emits the authored corridor kit at **285 triangles a
    metre**; a single Red ring-1 deck is 1,268 m around, so its ring corridor
    alone would be 361,000 triangles and the 180 unbuilt decks would be
    65 million. This is the same cross-section — width and ceiling taken from
    `interior_kit.PROVISIONAL` and `collision.corridor_profile` so a body
    crossing from a Shell A corridor into a Shell B one feels no step — with a
    rib every 4.5 m and nothing else.
    """
    prof = C.corridor_profile()
    h = prof["ceil_y"]
    hw = RING_W_M / 2.0
    ln = 2 * math.pi * r * (degrees / 360.0)
    v, t, g = [], [], []
    _slab(v, t, g, G["ring_deck"], 0.0, ln, 0.0, -hw, hw)
    _slab(v, t, g, G["ring_soffit"], 0.0, ln, h, -hw, hw, up=False)
    # The two side walls run ALONG the arc, so they are neither `_panel` (one
    # quad at constant x, which here would be a 4.5 cm sliver) nor `_end`. They
    # are emitted directly, subdivided on the same 4.5 m step as the floor, for
    # the sag reason in `_slab`'s docstring.
    n = max(1, int(math.ceil(ln / ARC_STEP_M)))
    for s in (-1, 1):
        t0 = len(t)
        for i in range(n):
            a, b = ln * i / n, ln * (i + 1) / n
            k = len(v)
            v += [(a, 0.0, s * hw), (b, 0.0, s * hw),
                  (b, h, s * hw), (a, h, s * hw)]
            if s < 0:
                t += [(k, k + 1, k + 2), (k, k + 2, k + 3)]
            else:
                t += [(k, k + 2, k + 1), (k, k + 3, k + 2)]
        g.append((G["ring_wall"], t0, len(t)))
    nrib = max(1, int(ln / ARC_STEP_M))
    for i in range(nrib):
        a = ln * (i + 0.5) / nrib
        for s in (-1, 1):
            _box(v, t, g, G["ring_rib"],
                 (a - 0.11, 0.0, s * hw - (0.16 if s > 0 else 0.0)),
                 (a + 0.11, h, s * hw + (0.0 if s > 0 else 0.16)))
    _slab(v, t, g, G["ring_light"], 0.0, ln, h - 0.05, -0.14, 0.14, up=False)
    return v, t, g


def _append(V, T, Gs, v, t, g, prefix):
    """Merge one piece into the deck, prefixing its groups.

    THE PREFIX IS `export_station._sidecars`' CONVENTION, not a new one:
    `z<int>__<name>` so two slots' identically-named spans do not merge into
    one material group, and so the tail — which is what `materials.resolve`
    and `interact.resolve` match on — survives untouched.
    """
    # ONE GROUP PER (SLOT, MATERIAL), NOT ONE PER PLATE. This module emits
    # every surface as its own span, so a straight copy gave red/1/5 **66,733
    # groups** -- and a group is a SURFACE to Godot's glTF importer, which is
    # 66,733 draw calls for one deck. The triangles are reordered so each name
    # is contiguous and one span covers it: the same deck comes to 2,208.
    #
    # The `z<int>__` prefix stays and stays per slot, for `export_station`'s
    # reason: merging two slots' identically-named spans would make one
    # instance whose AABB spans the whole ring, which is exactly the failure
    # CLAUDE.md records for the corridor occluder ("Godot culls per instance
    # AABB and the corridor's OBJ groups span the whole 345 deg ring").
    base = len(V)
    V.extend(v)
    order = {}
    for name, lo, hi in g:
        order.setdefault(name, []).append((lo, hi))
    for name in sorted(order):
        t0 = len(T)
        for lo, hi in order[name]:
            T.extend((a + base, b + base, c + base) for a, b, c in t[lo:hi])
        if len(T) > t0:
            Gs.append(("%s__%s" % (prefix, name), t0, len(T)))


# --------------------------------------------------------------------------
# COLLISION -- measured, never written down
# --------------------------------------------------------------------------
_BPROF = {}


def block_profile(area_m2=16.0, n_units=60, seed=0, force=False):
    """A Shell B block's walkable cross-section, MEASURED off its own geometry.

    `collision.corridor_profile`'s method, applied to this module's kit rather
    than to the authored one, and for CLAUDE.md's stated reason: the shell's
    profile is measured *"so it cannot drift from what it stands in for"*. If
    the spine's skirt grows, the light blade drops, or the door head moves, the
    number moves with it and no constant here has to be edited.

    Returns `floor_y` (the highest thing underfoot -- the skirt is 80 mm proud
    and a body walks past it, not on it), `half_w` (the NARROWEST clearance
    over a body's height, which is what a door jamb decides) and `ceil_y`.
    """
    key = (round(area_m2, 3), n_units, seed)
    if key in _BPROF and not force:
        return _BPROF[key]
    v, t, _g, p = block(area_m2, n_units, seed, lod=1)
    ln = p["length_m"]
    tops = []
    for i in range(12):
        x = -CORRIDOR_W_M / 2.0 * 0.8 + CORRIDOR_W_M * 0.8 * i / 11.0
        for j in range(24):
            z = -ln + ln * (j + 0.5) / 24.0
            h = C.cast((x, 2.4, z), (0.0, -1.0, 0.0), v, t)
            if h is not None and 2.4 - h < 0.6:
                tops.append(2.4 - h)
    floor_y = max(tops) if tops else 0.0
    body_top = floor_y + 1.8
    widths = []
    for i in range(10):
        y = floor_y + 0.05 + (body_top - floor_y - 0.05) * i / 9.0
        for j in range(40):
            z = -ln + 0.3 + (ln - 0.6) * j / 39.0
            a = C.cast((0.0, y, z), (1.0, 0.0, 0.0), v, t)
            b = C.cast((0.0, y, z), (-1.0, 0.0, 0.0), v, t)
            if a is not None and b is not None:
                widths.append(min(a, b))
    half_w = min(widths) if widths else CORRIDOR_W_M / 2.0
    heads = []
    for j in range(16):
        z = -ln + ln * (j + 0.5) / 16.0
        h = C.cast((0.0, floor_y + 0.1, z), (0.0, 1.0, 0.0), v, t)
        if h is not None:
            heads.append(floor_y + 0.1 + h)
    ceil_y = min(heads) if heads else Q.UNIT_H_M
    out = {"floor_y": floor_y, "half_w": half_w, "ceil_y": ceil_y,
           "samples": len(widths), "measured_on": (area_m2, n_units, seed)}
    _BPROF[key] = out
    return out


def deck_collision(schema, profile, sector, ring, deck, cells=None):
    """A smooth walkable shell for one Shell B deck.

    COLLISION IS NOT RENDER GEOMETRY (session 3v). A body dropped on the render
    mesh wedges on the 80 mm skirt and the 160 mm party wall returns; this
    emits a smooth box per spine, per room and per ring arc, at the radius
    `block_profile()` measured, with an aperture where every door is.

    Reuses `collision.room_shell` for the rooms and the block spines, so the
    aperture rule, the header-only door span and the winding — which Godot's
    `ConcavePolygonShape3D` will not forgive — come from the module that
    already got them right.
    """
    plan = deck_slots(schema, profile, sector, ring, deck)
    if plan is None:
        return [], [], {"built": False}
    prof = block_profile()
    r = plan["radius_m"]
    meta = {"floor_r_m": r - prof["floor_y"], "door_w_m": DOOR_W_M,
            "door_h_m": DOOR_H_M}
    # THE CELL PLAN IS ASKED FOR BY RUNG, NOT BY ADDRESS. `ring_cells`
    # subscripts the ring's z-blind stack, where index == rung, and it
    # RAISES for a register deck NUMBER -- `grey_0_50` is a name. The
    # address is one or the other (`_address`), so the rung is taken from
    # the stack row rather than from the key.
    cellplan = it.ring_cells(schema, profile, sector, ring,
                             plan["rung"])
    want = None if cells is None else set(cells)
    V, T, groups = [], [], []
    for s in plan["slots"]:
        ci = int(s["angle_deg"] // cellplan["cell_deg"]) % cellplan["cells"]
        if want is not None and ci not in want:
            continue
        if s["kind"] == "block":
            hw = prof["half_w"]
            ln = s["plan"]["length_m"]
            ceil = prof["ceil_y"] - prof["floor_y"]
        else:
            hw = s["width_m"] / 2.0 - 0.05
            ln = s["length_m"]
            ceil = PROGRAM[s["kind"]][3] - prof["floor_y"]
        z_mid = s["z_m"] - ln / 2.0
        v, t = C.room_shell(meta, s["angle_deg"], hw, ln / 2.0, ceil, z_mid,
                            door_angle_deg=s["angle_deg"])
        t0 = len(T)
        base = len(V)
        V.extend(v)
        T.extend((a + base, b + base, c + base) for a, b, c in t)
        groups.append(("shb_%s_%d" % (s["kind"], len(groups)), t0, len(T)))
    for band in range(plan["bands"]):
        arcs = [s for s in plan["slots"] if s["band"] == band]
        if not arcs:
            continue
        z = arcs[0]["z_m"] - RING_W_M / 2.0
        reach = plan["band_arc_m"].get(band, 0.0)
        cell_m = 2 * math.pi * r * (cellplan["cell_deg"] / 360.0)
        for ci in range(cellplan["cells"]):
            if want is not None and ci not in want:
                continue
            a_m = ci * cell_m
            if a_m >= reach - 1e-6:
                break
            arc_m = min(cell_m, reach - a_m)
            a0 = math.degrees((a_m + arc_m / 2.0) / r)
            v, t = C.room_shell(meta, a0, arc_m / 2.0, RING_W_M / 2.0,
                                prof["ceil_y"] - prof["floor_y"], z)
            t0 = len(T)
            base = len(V)
            V.extend(v)
            T.extend((a + base, b + base, c + base) for a, b, c in t)
            groups.append(("shb_ring_%d_%d" % (band, ci), t0, len(T)))
    return V, T, {"built": True, "groups": groups, "triangles": len(T),
                  "profile": prof,
                  "shell_frac": None}


# --------------------------------------------------------------------------
# THE WHOLE-STATION PLAN
# --------------------------------------------------------------------------
def station_plan(schema, profile):
    """Every Shell B deck in the station, described but not built.

    `interior.cell_manifest`'s architecture and its reason (ADR 0003): the
    repository stores the rule, not the result. 5.12 M m² of residential fabric
    is not a set of committed meshes, it is a function of the schema.
    """
    rows = []
    for b in sorted(belts().values(), key=lambda x: x["id"]):
        for sec, ring, dk in belt_decks(schema, profile, b):
            p = deck_slots(schema, profile, sec, ring, dk)
            if p is None:
                continue
            rows.append(p)
    # Grey ring 0 is owned once (SHB-08 + SHB-08.f merged), so a deck can
    # appear twice in the loop above; keep one row per address.
    seen, out = set(), []
    for p in rows:
        k = (p["sector"], p["ring"], p["deck"])
        if k in seen:
            continue
        seen.add(k)
        out.append({k2: v for k2, v in p.items() if k2 != "slots"})
    return out


def station_totals(schema, profile):
    """The plan added up, against the annex's own §4 TOTALS line."""
    rows = station_plan(schema, profile)
    tot = {
        "decks": len(rows),
        "blocks": sum(r["blocks"] for r in rows),
        "units": sum(r["units"] for r in rows),
        "partitions": sum(r["partitions"] for r in rows),
        "built_m2": sum(r["built_m2"] for r in rows),
        "target_m2": sum(r["gross_target_m2"] for r in rows),
        "over_m2": sum(r["over_m2"] for r in rows),
        "not_fitting_z": [(r["sector"], r["ring"], r["deck"])
                          for r in rows if not r["fits_z"]],
    }
    tot["spec_units"] = sum(b["units"] for b in belts().values())
    tot["spec_partitions"] = belts()["SHB-08.f"]["partitions"]
    tot["spec_gross_m2"] = sum(b["gross_m2"] for b in belts().values())
    return tot, rows


def integration_note():
    """The exact change that puts Shell B on the shipped path. Not applied here.

    This module does not own `tools/export_station.py` and does not edit it. The
    note is printed by `--integration` so the instruction lives with the code
    rather than only in a report.
    """
    return """\
tools/export_station.py :: work_list()  (the function at line 70)

  It enumerates decks from `routes.clusters()` -- "every deck that CARRIES A
  LOCATION" -- which is 71 of the station's 251. Shell B plans 86 decks, 38 of
  them at an address Shell A already owns (`decks.setdefault` leaves those to
  Shell A), so the change adds 48 decks and the station builds 119.

  IT WAS 101 PLANNED / 63 ADDED BEFORE SESSION 4v. Fifteen of those decks were
  a clamp: `deck_slots` resolved any deck index past the hull-narrowed stack to
  the innermost radius the stack had, so blue ring 0 built 8 decks at 4 radii
  and grey ring 0 built 23 at 12. `tools/merge_cells.py` refused the export
  over it and was right to. See `ring_stack`.

  AFTER the `decks[k[:3]].append(k[3])` loop and BEFORE `rings = ...`, add:

      import shell_b as SHB
      schema, profile = it.load()
      for row in SHB.station_plan(schema, profile):
          key = (row["sector"], row["ring"], row["deck"])
          if key == (DRUM_SECTOR, DRUM_RING, DRUM_DECK):
              continue
          decks.setdefault(key, [])          # a Shell B deck has no cluster z

  and in `main()`'s per-deck loop, where `D.build_deck_clusters(...)` is called
  (line 273), take the Shell B branch when the deck has no clusters:

      if not decks[k]:
          V, T, Gs, st = SHB.build_deck(schema, profile, sec, ring, dk)
          cv, ct, cmeta = SHB.deck_collision(schema, profile, sec, ring, dk)
      else:
          V, T, G, st = D.build_deck_clusters(...)          # unchanged

  `st` carries `blocks`, `units` and `built_m2`, which the manifest row can
  record beside `rooms`. `SHB.deck_collision` returns `(V, T, meta)` with
  `meta["groups"]` in the same span form `_write` already expects.

  NOTHING ELSE CHANGES. Group names resolve through `materials.resolve` by
  substring (`shb_unit_qtr_wall` -> `qtr_wall`), so no edit to materials.py is
  needed; `_sidecars`' `_tail()` already strips the `z<int>__` prefix this
  module emits.
"""


# --------------------------------------------------------------------------
# OUTPUT
# --------------------------------------------------------------------------
def write_obj(path, V, T, Gs):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# station/shell_b.py\n")
        for x, y, z in V:
            f.write("v %.6f %.6f %.6f\n" % (x, y, z))
        at = 0
        for name, lo, hi in Gs:
            if lo > at:
                for a, b, c in T[at:lo]:
                    f.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))
            f.write("g %s\n" % name)
            for a, b, c in T[lo:hi]:
                f.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))
            at = hi
        for a, b, c in T[at:]:
            f.write("f %d %d %d\n" % (a + 1, b + 1, c + 1))
    return path


def geometry_hash(V, T):
    """An identity hash of a mesh, quantised to a millimetre.

    `deck.py --degeneracy`'s question and its argument: *"Two places whose
    geometry hashes the same ARE one place"* -- identity, not similarity, so
    there is no threshold to tune and nothing to argue with.
    """
    h = hashlib.blake2b(digest_size=16)
    for x, y, z in V:
        h.update(b"%d|%d|%d;" % (round(x * 1000), round(y * 1000),
                                 round(z * 1000)))
    for a, b, c in T:
        h.update(b"%d,%d,%d;" % (a, b, c))
    return h.hexdigest()


# --------------------------------------------------------------------------
# THE GATE
# --------------------------------------------------------------------------
def _selftest(out=print, legacy=False, quick=False):
    """Nine claims, each able to fail, and each shown failing by a control.

    `--legacy` is the control set, and it is not a mode: it turns off the five
    variety rules and the derived area budget and is expected to FAIL. A gate
    that cannot fail on the content in front of it is measuring the wrong
    thing (CLAUDE.md, layer 2's lesson).
    """
    global _LEGACY
    _LEGACY = legacy
    _BPROF.clear()                 # the profile is measured off the geometry
    reset_stacks()                 # `_LEGACY` changes what a deck stack IS
    schema, profile = it.load()
    fails = []

    def claim(name, ok, note):
        out("  %-34s %-4s %s" % (name, "PASS" if ok else "FAIL", note))
        if not ok:
            fails.append(name)

    out("SHELL B -- the residential fabric, %s"
        % ("LEGACY CONTROLS ON" if legacy else "as shipped"))
    out("")

    # 1. the annex parses, completely.
    try:
        B = belts()
        rows = ", ".join("%s %s r%s %d blk" % (b["id"], b["sector"],
                                               b["rings"], b["blocks"])
                         for b in sorted(B.values(), key=lambda x: x["id"]))
        claim("the annex parses", len(B) == 10, "%d rows: %s" % (len(B),
                                                                 rows[:130]))
    except Exception as e:                                       # noqa: BLE001
        claim("the annex parses", False, "%s: %s" % (type(e).__name__, e))
        out("")
        out("%d of 12 claims fail" % len(fails))
        return len(fails)

    # 2. every belt's program parsed, and nothing was silently dropped.
    bad = [b["id"] for b in B.values() if not b["program"] and not b["per_block"]]
    kinds = sorted({k for b in B.values() for k in b["program"]})
    claim("every belt has a program", not bad,
          "%d kinds across 10 rows: %s" % (len(kinds), ", ".join(kinds)))

    # 3. the units the builder plans equal the units the annex states.
    tot, prows = station_totals(schema, profile)
    claim("units built == units specified",
          tot["units"] == tot["spec_units"],
          "%s planned, %s in the annex (%s partitions vs %s)"
          % ("{:,}".format(tot["units"]), "{:,}".format(tot["spec_units"]),
             "{:,}".format(tot["partitions"]),
             "{:,}".format(tot["spec_partitions"])))

    # 4. the generated area lands on the annex's own gross.
    err = abs(tot["built_m2"] - tot["target_m2"]) / max(tot["target_m2"], 1)
    claim("area == the annex's gross", err <= 0.02,
          "%s m² built against %s m² stated -- %.2f%% (over on %d decks by "
          "%s m²)" % ("{:,.0f}".format(tot["built_m2"]),
                      "{:,.0f}".format(tot["target_m2"]), err * 100,
                      sum(1 for r in prows if r["over_m2"] > 1),
                      "{:,.0f}".format(tot["over_m2"])))

    # 5. every belt fits inside its sector's own axial extent.
    claim("every deck fits its sector in z", not tot["not_fitting_z"],
          "%d decks, worst depth %.0f m" % (tot["decks"],
                                            max(r["depth_m"] for r in prows)))

    # 6. no deck puts a resident outside the pressure hull.
    #
    # CLAUDE.md's live table carries "places outside the pressure hull: 0 of
    # 129 (was 34)" as a hard-won number, and a belt that hangs 3,747,126 m² of
    # housing off a ring stack sized at the sector's WIDEST cylinder is exactly
    # how it goes back to 34. `interior.decks_in_ring`'s own note names the four
    # places it happened to. Checked against `hull_radius_at` at each band's own
    # z rather than at the deck's centre, because a belt 300 m deep in z spans
    # a taper.
    out_of_hull = []
    for p in prows:
        for z in (p["z0"], p["z0"] + p["depth_m"]):
            lim = it.hull_radius_at(profile, z) - it.HULL_SKIN_M
            if p["radius_m"] > lim:
                out_of_hull.append((p["sector"], p["ring"], p["deck"],
                                    round(p["radius_m"] - lim, 1)))
                break
    claim("no deck outside the pressure hull", not out_of_hull,
          "%d decks checked at both ends of their z span%s"
          % (len(prows), "" if not out_of_hull else
             "; %d outside, worst by %.1f m: %s"
             % (len(out_of_hull), max(x[3] for x in out_of_hull),
                out_of_hull[:3])))

    # 7. every group name resolves to a material.
    import materials as M                                        # noqa: PLC0415
    unbound = [n for n in sorted(set(G.values()))
               if M.resolve(n, "interior") is None]
    claim("every group carries a material", not unbound,
          "%d names, %d unbound%s" % (len(set(G.values())), len(unbound),
                                      (": " + ", ".join(unbound)) if unbound
                                      else ""))

    # 7. the collision profile is measured, and is inside the render mesh.
    prof = block_profile()
    ok = (0.0 <= prof["floor_y"] < 0.20 and 0.9 <= prof["half_w"]
          <= CORRIDOR_W_M / 2.0 + 1e-6 and 2.0 < prof["ceil_y"] <= Q.UNIT_H_M)
    claim("collision profile measured", ok,
          "floor %.3f m, half width %.3f m (kit %.3f), head %.3f m, %d samples"
          % (prof["floor_y"], prof["half_w"], CORRIDOR_W_M / 2.0,
             prof["ceil_y"], prof["samples"]))

    # 8. no two decks are the same deck.
    # THE SAMPLE IS TAKEN FROM THE PLAN, NOT WRITTEN DOWN, and that is a
    # correctness requirement rather than tidiness. It used to name
    # `red/1/0..5` and `blue/0/2..4` as literals; a Shell B deck number is now
    # a canonical rung, red ring 1's free rungs start at 8, and every one of
    # those literals resolves to no belt at all -- twelve empty meshes, twelve
    # identical hashes, and a degeneracy claim that fails for the one reason it
    # is not about. Derived, it can only ever name decks that exist, and the
    # spread is asserted below so it cannot quietly shrink to one ring.
    sample = []
    for k in sorted({(p["sector"], p["ring"]) for p in prows}):
        sample += [(p["sector"], p["ring"], p["deck"]) for p in prows
                   if (p["sector"], p["ring"]) == k][:3]
    sample = sample[:12]
    n_rings = len({(s, r) for s, r, _d in sample})
    thin_sample = "" if (len(sample) >= 10 and n_rings >= 3) else \
        "; SAMPLE TOO THIN to be a degeneracy test: %d decks over %d rings" \
        % (len(sample), n_rings)
    hashes = {}
    for sec, ring, dk in sample:
        # `rings=False` AND `place=False`, and both exclusions are the point.
        # Placed, two decks differ because they sit at different angles;
        # WITH the ring corridor they differ because the deck radius differs,
        # so the hash is dominated by a number that has nothing to do with
        # whether the two decks are the same PLACE. Stripped to the slots in
        # their own frames, the only thing left that can differ is the content
        # -- which is the question `deck.py --degeneracy` asks.
        V, T, _g, _m = build_deck(schema, profile, sec, ring, dk,
                                  lod=0 if quick else 1, place=False,
                                  rings=False)
        hashes.setdefault(geometry_hash(V, T), []).append((sec, ring, dk))
    dupes = {h: v for h, v in hashes.items() if len(v) > 1}
    claim("no two decks hash the same", not dupes and not thin_sample,
          "%d decks over %d rings, %d distinct content geometries%s%s"
          % (len(sample), n_rings, len(hashes),
             ("; COLLIDING: " + str(list(dupes.values())[:3])) if dupes
             else "", thin_sample))

    # 9. you cannot see the background from inside a block.
    #
    # CLAUDE.md: "A hole in geometry shows the background through it, and the
    # background is black. Two surfaces shipped open for four sessions because
    # of this." A plate kit is exactly where that happens -- every surface here
    # is an open quad and nothing is a closed solid, so `boundary_edges` counts
    # thousands and says nothing useful. What a player can actually catch is a
    # LINE OF SIGHT OUT, so that is what is measured: rays from stations down
    # the spine and from inside four units, on a lattice of headings, and every
    # one must hit something. The way in at +z is excluded by construction --
    # it is a door, not a hole.
    ok, note = _containment()
    claim("no line of sight out of a block", ok, note)

    # 10. two blocks of the same size on the same deck are not one block.
    #
    # THE FIRST VERSION OF THIS CLAIM COULD NOT FAIL, and it is worth saying so
    # rather than quietly replacing it: it hashed the two HALVES of one block,
    # which always differ because one end carries the way in and the other the
    # wash-room annexe. It passed with every variety rule switched off. The
    # question the degeneracy rule actually asks is whether two things that
    # should be different ARE, so it compares two blocks of identical class and
    # unit count on one deck -- which can only differ through their seeds.
    # THE DECK IS THE PLAN'S BUSIEST, NOT A LITERAL, for the reason claim 8's
    # sample is derived: `red/1/5` is no longer a Shell B address at all now
    # that a deck number is a rung, and a hard-coded one that has stopped
    # existing turns a claim into a crash.
    busiest = max(prows, key=lambda p: p["blocks"])
    pl = deck_slots(schema, profile, busiest["sector"], busiest["ring"],
                    busiest["deck"])
    where = "%s/%d/%d" % (busiest["sector"], busiest["ring"], busiest["deck"])
    same = {}
    for s in pl["slots"]:
        if s["kind"] != "block":
            continue
        same.setdefault((s["area_m2"], s["units"]), []).append(s)
    pair = max(same.values(), key=len)[:2]
    hs = [geometry_hash(*block(x["area_m2"], x["units"], x["seed"],
                               plan=x["plan"])[:2]) for x in pair]
    claim("two like blocks are not one block", hs[0] != hs[1],
          "%d blocks of %g m² x %d on %s, two of them hash %s / %s"
          % (len(max(same.values(), key=len)), pair[0]["area_m2"],
             pair[0]["units"], where, hs[0][:8], hs[1][:8]))

    # 12. no two decks of a ring stand at one radius.
    #
    # THE CLAIM THIS MODULE SHIPPED WITHOUT, AND IT COST A WINDOWS BUILD.
    # `tools/merge_cells.py::deck_headroom` derives streaming residency as a
    # containment test on RADIUS -- a deck floor is opaque, so a deck occupies
    # the band from its own floor radius inward to its neighbour's -- and it
    # refused a 48-minute export with "derived deck headroom below 2.0 m ...
    # a band this thin is a fall through the world". It was right. Fifteen
    # decks of this module's own plan sat at a radius another deck already had,
    # because `deck_slots` read `stack[min(deck, len(stack) - 1)]`.
    #
    # THE BAR IS READ, NOT RESTATED. `MIN_HEADROOM_M` is imported from the tool
    # that refuses, so this gate cannot pass a build that tool would reject --
    # the rule `spec_harness/shb.py` states one level down, "a constant copied
    # into a harness cannot disagree with the row it checks".
    ring_r, gaps = {}, []
    for p in prows:
        ring_r.setdefault((p["sector"], p["ring"]), {})[p["deck"]] = \
            round(float(p["radius_m"]), 3)
    dup = []
    for k, v in sorted(ring_r.items()):
        rs = sorted(v.values(), reverse=True)
        if len(set(rs)) != len(rs):
            seen = {}
            for dk, r in sorted(v.items()):
                seen.setdefault(r, []).append(dk)
            dup.append((k, len(rs), len(set(rs)),
                        sorted(x for x in seen.values() if len(x) > 1)[:1]))
        gaps += [(round(a - b, 3), k) for a, b in zip(rs, rs[1:])]
    thin = sorted(g for g in gaps if g[0] < _min_headroom())
    claim("no two decks of a ring share a radius", not dup and not thin,
          "%d rings, %d decks, tightest gap %.3f m against %.3f m demanded by "
          "merge_cells%s%s"
          % (len(ring_r), len(prows), min(gaps)[0] if gaps else float("nan"),
             _min_headroom(),
             "" if not dup else "; NOT DISTINCT: %s" % (dup[:2],),
             "" if not thin else "; %d gap(s) under the bar: %s"
             % (len(thin), thin[:3])))

    out("")
    out("%d of 12 claims fail" % len(fails))
    _LEGACY = False
    return len(fails)


def _containment(area_m2=16.0, n_units=60, lattice=16, holed=False):
    """Rays from inside a block: how many escape, and where from.

    `holed` is the negative control and it deletes ONE plate -- the block's
    `-x` outer wall -- which is the single surface a player standing in a unit
    looks straight at. If the measurement cannot tell that apart from an intact
    block it is measuring nothing.
    """
    v, t, g, p = block(area_m2, n_units, seed_of("containment"), lod=1)
    if holed:
        keep = [(n, lo, hi) for n, lo, hi in g if n != G["unit_wall"]]
        drop = [(lo, hi) for n, lo, hi in g if n == G["unit_wall"]][:1]
        if drop:
            lo, hi = drop[0]
            t = t[:lo] + t[hi:]
    idx = C.grid_index(v, t, cell_m=6.0)
    run, hw = p.get("unit_run_m", p["length_m"]), p["width_m"] / 2.0
    d = p["unit_d_m"]
    stations = [(0.0, 1.2, -run * f) for f in (0.15, 0.45, 0.75)]
    stations += [(s * (CORRIDOR_W_M / 2.0 + d / 2.0), 1.2, -run * f)
                 for s in (-1, 1) for f in (0.3, 0.6)]
    out, tried = [], 0
    for o in stations:
        for i in range(lattice):
            for j in range(lattice // 2):
                th = 2 * math.pi * i / lattice
                ph = math.pi * (j + 0.5) / (lattice // 2)
                dirv = (math.sin(ph) * math.cos(th), math.cos(ph),
                        math.sin(ph) * math.sin(th))
                # The way in is a door, not a hole: a ray leaving through the
                # +z aperture is the aperture working.
                if dirv[2] > 0.55:
                    continue
                tried += 1
                if C.cast_short(o, dirv, v, t, idx, 400.0) is None:
                    out.append((o, dirv))
    frac = len(out) / max(tried, 1)
    return (not out,
            "%d rays from %d stations, %d escape (%.2f%%)%s"
            % (tried, len(stations), len(out), 100 * frac,
               "" if not out else "; first at %s heading %s"
               % (tuple(round(x, 1) for x in out[0][0]),
                  tuple(round(x, 2) for x in out[0][1]))))


def _slice_z(v, t, z0, z1):
    """The sub-mesh whose triangles are entirely inside a z band."""
    keep = [tri for tri in t
            if all(z0 - 1e-6 <= v[i][2] <= z1 + 1e-6 for i in tri)]
    idx, vv, tt = {}, [], []
    for tri in keep:
        n = []
        for i in tri:
            if i not in idx:
                idx[i] = len(vv)
                vv.append(v[i])
            n.append(idx[i])
        tt.append(tuple(n))
    return vv, tt


# --------------------------------------------------------------------------
def _cli(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--legacy", action="store_true",
                    help="turn OFF the five variety rules and the derived "
                         "area budget. The negative control; it must fail")
    ap.add_argument("--quick", action="store_true",
                    help="run the degeneracy hash at lod 0")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--deck", default="", metavar="SECTOR/RING/DECK")
    ap.add_argument("--cell", type=int, default=None)
    ap.add_argument("--lod", type=int, default=1)
    ap.add_argument("--obj", default="")
    ap.add_argument("--integration", action="store_true")
    a = ap.parse_args(argv)

    if a.integration:
        print(integration_note())
        return 0
    if a.selftest:
        return 1 if _selftest(legacy=a.legacy, quick=a.quick) else 0

    schema, profile = it.load()
    if a.plan:
        tot, rows = station_totals(schema, profile)
        print("\nSHELL B -- THE PLAN\n")
        print("  %-9s %-6s %-4s %-4s %7s %7s %9s %9s %5s"
              % ("belt", "sector", "ring", "deck", "blocks", "units",
                 "built m2", "spec m2", "bands"))
        for r in rows:
            print("  %-9s %-6s %-4d %-4d %7d %7d %9.0f %9.0f %5d"
                  % (r["belt"][:9], r["sector"], r["ring"], r["deck"],
                     r["blocks"], r["units"], r["built_m2"],
                     r["gross_target_m2"], r["bands"]))
        print("")
        print("  %d decks, %s blocks, %s units + %s partitions"
              % (tot["decks"], "{:,}".format(tot["blocks"]),
                 "{:,}".format(tot["units"]),
                 "{:,}".format(tot["partitions"])))
        print("  %s m2 generated against the annex's %s m2 (%.2f%%)"
              % ("{:,.0f}".format(tot["built_m2"]),
                 "{:,.0f}".format(tot["target_m2"]),
                 100.0 * tot["built_m2"] / max(tot["target_m2"], 1)))
        # A CAP IS NEVER SILENT. The belts as written want more decks than the
        # hull leaves over their own z; the blocks redistribute over the decks
        # that remain, so the dwellings and the gross are unchanged and the
        # DENSITY per deck is what moves. Printed with the axial station the
        # sector's stacks were taken at, because that is the number that
        # decides it.
        c = caps()
        print("")
        if not c:
            print("  no belt capped -- every belt's decks all exist at its z")
        for (bid, sec, ring), (want, kept, why) in sorted(c.items()):
            print("  CAPPED  %-9s %s ring %d: %d decks asked, %d built  (%s)"
                  % (bid, sec, ring, want, kept, why))
        for (_i, sec), (z, dep) in sorted(_SECTOR_Z.items(),
                                          key=lambda t: t[0][1]):
            print("  %-6s stacks taken at z %.1f m (belt depth %.0f m)"
                  % (sec, z, dep))
        # AN ADDRESS THIS MODULE CANNOT MAKE UNAMBIGUOUS IS PRINTED, NOT
        # SWALLOWED. See `stack_entry`.
        ix = indexed()
        print("")
        if not ix:
            print("  every Shell B deck number is a canonical rung")
        for (sec, ring), why in sorted(ix.items()):
            print("  POSITIONAL  %s ring %d: %s" % (sec, ring, why))
        return 0

    if a.deck:
        sec, ring, dk = a.deck.split("/")
        ring, dk = int(ring), int(dk)
        cells = None if a.cell is None else [a.cell]
        V, T, Gs, m = build_deck(schema, profile, sec, ring, dk, lod=a.lod,
                                 cells=cells)
        if not m.get("built"):
            print("  %s: %s" % (a.deck, m.get("why")))
            return 1
        cv, ct, cm = deck_collision(schema, profile, sec, ring, dk, cells=cells)
        print("\nSHELL B DECK %s -- belt %s\n" % (a.deck, m["belt"]))
        print("  radius %.2f m, %.0f m around, %d streaming cells, "
              "gravity %.2f g" % (m["radius_m"], m["circumference_m"],
                                  m["cells"], m["gravity_g"]))
        print("  %d blocks x %d units, %d rooms, %d bands, %.0f m deep in z "
              "(sector has %.0f)"
              % (m["blocks"], m["units"] // max(m["blocks"], 1),
                 len(m["slot_table"]) - m["blocks"], m["bands"], m["depth_m"],
                 m["z_span_m"]))
        print("  program: %s" % ", ".join("%s x%d" % (k, v)
                                          for k, v in sorted(m["program"].items())))
        print("")
        print("  area      %10.0f m2 built  (blocks %.0f + rooms %.0f + "
              "corridor %.0f)" % (m["built_m2"], m["block_m2"], m["room_m2"],
                                  m["ring_m2"]))
        print("            %10.0f m2 the annex states for this deck"
              % m["gross_target_m2"])
        print("  capacity  %10d dwellings" % m["units"])
        print("  triangles %10s render (lod %d), %s collision (%.1f%%)"
              % ("{:,}".format(m["triangles"]), a.lod,
                 "{:,}".format(cm["triangles"]),
                 100.0 * cm["triangles"] / max(m["triangles"], 1)))
        # THE AREA IS THE DECK'S AND THE TRIANGLES ARE THE CELL'S when `--cell`
        # is given, so a tri/m² printed across the two is a number about
        # nothing. Said out loud rather than divided anyway: a tool that
        # reports a ratio between two different populations is manufacturing
        # evidence, which is the same fault as one that silently degrades.
        if cells is not None:
            print("  triangles are CELL %d's; the areas above are the whole "
                  "deck's, so no tri/m2 is quoted -- they are different "
                  "populations" % a.cell)
        else:
            print("  per m2    %10.2f render tri/m2, %.3f collision tri/m2"
                  % (m["tri_per_m2"], cm["triangles"] / max(m["built_m2"], 1)))
            print("  per cell  %10s render tri (mean over %d cells)"
                  % ("{:,.0f}".format(m["triangles"] / max(m["cells"], 1)),
                     m["cells"]))
        if a.obj:
            write_obj(a.obj, V, T, Gs)
            print("  wrote %s (%d groups)" % (a.obj, len(Gs)))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
