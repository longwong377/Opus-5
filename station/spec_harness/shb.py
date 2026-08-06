"""SHB rows: Shell B, the nine residential belts -- their arithmetic, against
themselves, against the roster ledger, and against the code the ledger claims
to come from.

WHAT AN SHB ROW IS, AND WHY IT IS THE ONE FAMILY A HARNESS CAN ARGUE WITH. A
PLC row is an address and a program; an SHB row is a SUM. SHB-01 reads

    **62 blocks** x 60 units @18 m2 (EF/EA overflow beyond PLC-007's 270 and
    PLC-008's 1,260: 5,220 EF/EA heads - 1,530 = 3,690 units, 3,720 provided)
    across decks 2-9: ~8/deck ... **~=93,700 m2 gross.**

and every one of those numbers is derivable from another one. 62 x 60 must be
the 3,720 provided; 270 + 1,260 must be the 1,530 subtracted; 5,220 - 1,530
must be 3,690; 3,720 must cover 3,690; 3,720 x 18 x 1.4 must be 93,700; 62 over
the eight decks 2-9 must be the ~8/deck. **Nothing in that chain needs a built
station** -- which is exactly why it is worth checking, because a spec whose own
arithmetic has drifted is a spec that will be built wrong.

FOUR LAYERS, and they are in increasing order of what they can catch:

  1. THE ROW AGAINST ITSELF -- the chain above. Catches a figure edited in one
     place and not the others, which is the failure mode a 300-row spec has.
  2. THE ROW AGAINST ITS CITATIONS -- "PLC-007's 270" is checked against
     PLC-007's own program line ("90 bays -> 270 units at 34 m2") and against
     that row's own TILING total. Two documents' worth of agreement, free.
  3. THE ROW AGAINST THE LEDGER -- Sec 2's roster table, whose housed column the
     belts take their head counts from. The table is parsed and made to sum:
     role terms -> stated total, total + breather transfer -> housed, and the
     five housed figures -> 250,001.
  4. THE LEDGER AGAINST THE CODE -- and this is the layer that can find a
     defect rather than a typo. The table says it is "schedule.py ROLE_WEIGHTS";
     `_claim_roster` sums that live matrix by role and compares it term by term.
     A role weight edited in Python and not in the annex is a station whose
     housing does not fit its population, and nothing else in this project
     would notice.

WHAT IS DELIBERATELY NOT CHECKED, stated so a GREEN is never read as more than
it is. Every SHB row's CHECK is about a BUILT belt -- "every EF resident whose
card says Blue has a real, enterable, numbered unit", "the 07:40 commute tide
flows from these doors to PLC-116 lifts", "no two decks byte-identical". None of
that is settleable without geometry, and **there is no Shell B builder in the
project at all**: no module under `station/` assigns block program to a deck
cell, so the 3,720 units of SHB-01 exist as a number and nowhere else.
`SUFFICIENT = False` says so, and the note on a passing row names it.

THE PARSE HAS TO BE MEASURED, NOT LOOSENED. `plc.py`'s lesson one level down:
"I cannot read this" and "this disagrees" are opposite findings and only one is
about the station. So `--selftest` prints, per row, every clause the extractor
found, and a row whose housing clause does not parse FAILS rather than passing
vacuously -- the nine belts split 4 with housing and 5 without, and the five
without are recognised by their own words ("No housing", "No blocks", "No
formal housing"), never by an empty match.

THE THREE UNITS TRAPS, each of which cost a wrong first draft:

  * `x 60 units @18 m2` is 60 units per block at 18 m2 EACH, not 60 units of
    18 m2 total, and not a (60, 18) unit/area pair. SHB-06 writes the pair form
    instead -- `**6,250 @22 m2 ... + 7,910 @16 m2**` -- so both shapes exist and
    the extractor has to tell them apart by what precedes the number.
  * MINUS IS U+2212 AND THE DECK RANGE IS U+2013. `decks 2-9` uses an EN DASH
    and is not arithmetic; `5,220 - 1,530` uses a MINUS SIGN and is. A character
    class that conflates them turns every deck range into a failing subtraction.
  * gross is quoted to the nearest 100 m2, so the tolerance is 50 -- half the
    quoted precision, not a percentage. On SHB-04's 3,706,900 a 0.1% tolerance
    would be +/-3,707 and would accept a whole belt's worth of error.
"""
import os
import re

SUFFICIENT = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}

# --- the annex ------------------------------------------------------------
_HEAD = re.compile(r"^###\s+(SHB-\d+)\s*—\s*(.+?)\s*$")
_PLC_KEYLINE = re.compile(r"^#+\s*PLC-(\d+)\s*`([a-z0-9_]+)`")
_PLC_REF = re.compile(r"PLC-(\d+)")
_TILING = re.compile(r"TILING\s*\**\s*(\d+)\s*(?:→|->)\s*\**\s*([\d,]+)")
_PLC_UNITS = re.compile(r"([\d,]+)\s*bays\s*(?:→|->)\s*([\d,]+)\s*units\s*at\s*(\d+)\s*m²")

# --- the Shell B derivation preamble --------------------------------------
_LADDER = re.compile(r"quarters ladder \(([^)]*)\)")
_LADDER_TERM = re.compile(r"([a-z]+)\s+(\d+)")
_UPB = re.compile(r"UNITS_PER_BLOCK\s*=\s*(\d+)")
_GROSS_FACTOR = re.compile(r"gross = net ×([\d.]+)")
_MANIFEST = re.compile(r"\*\*(\d[\d,]*) decks,\s*([\d,]+) cells\*\*")

# --- the housing clauses --------------------------------------------------
# `**62 blocks** × 60 units @18 m²`   `+ **706 blocks** × 60 @9 m²`
_BLOCKS = re.compile(r"\*\*([\d,]+)\s*blocks\*\*\s*×\s*(\d+)"
                     r"(?:\s*units)?(?:\s*@(\d+)\s*m²)?")
# `6,250 @22 m² ... + 7,910 @16 m²` -- a unit COUNT and its area, which is only
# a pair when the number is not the per-block 60 the clause above already took.
_PAIR = re.compile(r"([\d,]{3,})\s*@(\d+)\s*m²")
# `5,220 EF/EA heads − 1,530 = 3,690 units`. U+2212 only: an en dash here is a
# range, not a subtraction.
#
# THE MINUEND IS THE NEAREST NUMBER TO THE LEFT OF THE SIGN, and the first
# version of this got it wrong in a way worth recording. A tolerant gap of
# `[^=\n−]{0,40}` let the leftmost-match rule reach back over TWO intervening
# figures and read SHB-01's "PLC-007's **270** and PLC-008's 1,260: 5,220 heads
# − 1,530" as "270 − 1,530", which then failed as arithmetic drift. That is the
# exact confusion `plc.py` warns about: a parse defect wearing a finding's
# clothes. The gap is now WORDS ONLY -- a token may not START with a digit --
# so the scan cannot step over a number to find its minuend.
_MINUS_EQ = re.compile(r"([\d,]+)(?:\s+[^\d\s=−][^\s=−]*)*\s+−\s*([\d,]+)"
                       r"[^=\n]{0,60}?=\s*([\d,]+)")
# `141,640 civilian units beyond PLC-019: 143,560 − 1,920`
_BEYOND = re.compile(r"([\d,]+)\s+[a-z]+ units beyond PLC-(\d+):\s*"
                     r"([\d,]+)\s*−\s*([\d,]+)")
# `beyond PLC-007's 270 and PLC-008's 1,260: ... − 1,530`
_TWO_PLC = re.compile(r"PLC-(\d+)'s ([\d,]+) and\s+PLC-(\d+)'s ([\d,]+)")
_GROSS = re.compile(r"≈\s*([\d,]+)\s*m²")
_PER_DECK = re.compile(r"~\s*([\d,]+)\s*(?:blocks)?\s*/deck")
_M2_PER_DECK = re.compile(r"~\s*([\d,]+)\s*m²/deck")
_DECK_RANGE = re.compile(r"decks\s*(\d+)\s*[–-]\s*(\d+)")
_DECK_COUNT = re.compile(r"\*\*(\d+) residential decks")
_NO_HOUSING = re.compile(r"No (?:housing|blocks|formal housing)", re.I)

# --- the roster ledger ----------------------------------------------------
_LEDGER_ROW = re.compile(r"^\|\s*(Blue|Red \(civilian\)|Red \(transient\)|"
                         r"Green|Grey|Yellow)\s*\|(.+)\|(.+)\|(.+)\|\s*$")
_TERM = re.compile(r"([A-Za-z][A-Za-z /']*?)\s+([\d,]+)(?=\s*(?:·|=|$))")
_NUM = re.compile(r"[\d,]+")

# The ledger's own words for a `schedule.ROLE_WEIGHTS` role. Written out rather
# than fuzzy-matched: two of them SPLIT one role across two sectors (EF
# engineering + civilian engineers is `engineer`; EF medical + civilian medical
# is `medical`), so the comparison is per-ROLE over the whole table and not per
# ledger cell. A fuzzy matcher would have silently paired "civilian medical"
# with `medical` and left "EF medical" unmatched, which reads as agreement.
_ROLE_OF = {
    "command": "command", "security": "security", "customs": "customs",
    "traffic": "traffic", "dockworkers": "dockworker",
    "EF engineering": "engineer", "civilian engineers": "engineer",
    "EF medical": "medical", "civilian medical": "medical",
    "merchant": "merchant", "service": "service", "financier": "financier",
    "industrial": "industrial", "waste": "waste",
    "visitors/transients": "visitor", "diplomats": "diplomat",
    "clerics": "cleric", "hydroponics": "hydroponics", "Kosh": "envoy",
    "lurkers": "lurker", "refugees": "refugee",
}

_TIERS = re.compile(r"\bT([1-9])\b")
_LETTER = re.compile(r"(?:^|\s)([a-z])\.\s+\*\*")


# ---------------------------------------------------------------------------
# reading the annex
# ---------------------------------------------------------------------------
def _i(s):
    return int(str(s).replace(",", "").strip())


def _places_md():
    if "md" not in _CACHE:
        _CACHE["md"] = open(os.path.join(ROOT, "docs/spec/PLACES.md"),
                            encoding="utf-8").read()
    return _CACHE["md"]


def _blocks_md():
    """SHB id -> (line number, block text), heading to the next heading."""
    if "shb" not in _CACHE:
        out, cur = {}, None
        for n, ln in enumerate(_places_md().splitlines(), 1):
            m = _HEAD.match(ln)
            if m:
                cur = m.group(1)
                out[cur] = [n, [ln]]
            elif ln.startswith("#"):
                cur = None
            elif cur:
                out[cur][1].append(ln)
        _CACHE["shb"] = {k: (v[0], "\n".join(v[1])) for k, v in out.items()}
    return _CACHE["shb"]


def _preamble():
    """The Shell B derivation paragraph's four normative constants.

    Read from the document, never restated here, for `plc.py`'s reason: a
    constant copied into a harness cannot disagree with the row it checks, so
    copying it would delete the only interesting failure.
    """
    if "pre" in _CACHE:
        return _CACHE["pre"]
    body = _places_md()
    i = body.find("# 2. SHELL B")
    j = body.find("### SHB-01")
    txt = re.sub(r"\s+", " ", body[i:j] if i >= 0 < j else "")
    lad = {}
    ml = _LADDER.search(txt)
    if ml:
        lad = {k: int(v) for k, v in _LADDER_TERM.findall(ml.group(1))}
    mu, mg, mm = (_UPB.search(txt), _GROSS_FACTOR.search(txt),
                  _MANIFEST.search(txt))
    _CACHE["pre"] = {
        "ladder": lad,
        "units_per_block": int(mu.group(1)) if mu else None,
        "gross_factor": float(mg.group(1)) if mg else None,
        "decks": _i(mm.group(1)) if mm else None,
        "cells": _i(mm.group(2)) if mm else None,
        "text": txt,
    }
    return _CACHE["pre"]


def _ledger():
    """The roster table: sector -> {terms, stated total, transfer, housed}.

    SCOPED TO THE SHELL B PREAMBLE, and it has to be. PLACES.md carries a
    SECOND five-row table keyed on the same sector names -- Sec 4 TOTALS, whose
    `| Blue |` row is places/tiling/gross/capacity -- and an unscoped scan read
    it last and reported Blue as housing 12,930 with a +265,800 breather
    transfer. Both tables are real and they mean different things; a parser that
    cannot tell them apart manufactures drift out of thin air.
    """
    if "led" in _CACHE:
        return _CACHE["led"]
    body = _places_md()
    i, j = body.find("# 2. SHELL B"), body.find("### SHB-01")
    rows = {}
    for ln in body[i:j].splitlines():
        m = _LEDGER_ROW.match(ln.strip())
        if not m:
            continue
        who, roles, transfer, housed = m.groups()
        flat = re.sub(r"\([^)]*\)", " ", roles)          # drop parentheticals
        flat = flat.replace("—", " ").strip()
        total = None
        if "=" in flat:
            tail = flat.rsplit("=", 1)[1]
            mt = _NUM.search(tail)
            total = _i(mt.group(0)) if mt else None
            flat = flat.rsplit("=", 1)[0]
        terms = [(k.strip(), _i(v)) for k, v in _TERM.findall(flat + " ")]
        mh = _NUM.search(housed)
        mt = _NUM.search(transfer)
        sign = -1 if "−" in transfer else 1
        rows[who] = {
            "terms": terms,
            "total": total,
            "transfer": (sign * _i(mt.group(0))) if mt else 0,
            "housed": _i(mh.group(0)) if mh else 0,
            "raw": roles,
        }
    _CACHE["led"] = rows
    return rows


def _plc_keys():
    if "plc" not in _CACHE:
        out = {}
        for ln in _places_md().splitlines():
            m = _PLC_KEYLINE.match(ln.strip())
            if m:
                out[int(m.group(1))] = m.group(2)
        _CACHE["plc"] = out
    return _CACHE["plc"]


def _plc_block(n):
    src = _places_md().splitlines()
    want = "PLC-%03d" % n
    for i, ln in enumerate(src):
        if ln.startswith("###") and want in ln:
            out = [ln]
            for j in range(i + 1, len(src)):
                if src[j].startswith("#"):
                    break
                out.append(src[j])
            return "\n".join(out)
    return ""


# ---------------------------------------------------------------------------
# the housing model a row states
# ---------------------------------------------------------------------------
def _housing(text):
    """(clauses, problems). A clause is (blocks, per_block, area_m2 or None)."""
    flat = re.sub(r"\s+", " ", text)
    clauses = [(_i(a), _i(b), _i(c) if c else None)
               for a, b, c in _BLOCKS.findall(flat)]
    pairs = [(_i(a), _i(b)) for a, b in _PAIR.findall(flat)]
    return clauses, pairs


def _claim_blocks(rid, text):
    """The block/unit/area chain, and the citations it hangs off."""
    pre = _preamble()
    flat = re.sub(r"\s+", " ", text)
    clauses, pairs = _housing(text)
    bad, said = [], []

    if not clauses:
        if _NO_HOUSING.search(flat):
            return True, "declares no housing in its own words"
        return False, ("no `**N blocks** × M` clause parsed and the row does "
                       "not say it has no housing -- the extractor cannot read "
                       "this row, which is not the same as disagreeing with it")

    upb = pre["units_per_block"]
    units_total = 0
    net_m2 = 0
    for nb, per, area in clauses:
        if upb is not None and per != upb:
            bad.append("a block is %d units here and the derivation says %d"
                       % (per, upb))
        units_total += nb * per
        if area is not None:
            net_m2 += nb * per * area
            if area not in pre["ladder"].values():
                bad.append("%d m² is not on the INV-032 ladder %s"
                           % (area, sorted(set(pre["ladder"].values()))))
    said.append("%s = %s units"
                % (" + ".join("%d×%d" % (n, p) for n, p, _a in clauses),
                   "{:,}".format(units_total)))

    # SHB-06 states its areas as a SPLIT of the block total rather than on the
    # clause. The split must exhaust the units the blocks provide.
    if any(a is None for _n, _p, a in clauses) and pairs:
        split = sum(n for n, _a in pairs)
        if split != units_total:
            bad.append("the @m² split is %s units and %d blocks × %d provide "
                       "%s" % ("{:,}".format(split), clauses[0][0],
                               clauses[0][1], "{:,}".format(units_total)))
        for n, a in pairs:
            net_m2 += n * a
            if a not in pre["ladder"].values():
                bad.append("%d m² is not on the INV-032 ladder" % a)
        said.append("split %s" % " + ".join("%s@%d" % ("{:,}".format(n), a)
                                            for n, a in pairs))

    # units provided must cover the heads the row computes for itself.
    need = []
    for a, b, c in _MINUS_EQ.findall(flat):
        a, b, c = _i(a), _i(b), _i(c)
        if a - b != c:
            bad.append("the row's own subtraction %s − %s = %s is %s"
                       % ("{:,}".format(a), "{:,}".format(b),
                          "{:,}".format(c), "{:,}".format(a - b)))
        else:
            said.append("%s − %s = %s" % ("{:,}".format(a), "{:,}".format(b),
                                          "{:,}".format(c)))
            need.append(c)
    for c, plc, a, b in _BEYOND.findall(flat):
        c, a, b = _i(c), _i(a), _i(b)
        if a - b != c:
            bad.append("beyond PLC-%s: %s − %s is %s, the row says %s"
                       % (plc, "{:,}".format(a), "{:,}".format(b),
                          "{:,}".format(a - b), "{:,}".format(c)))
        else:
            said.append("PLC-%s: %s − %s = %s" % (plc, "{:,}".format(a),
                                                  "{:,}".format(b),
                                                  "{:,}".format(c)))
            need.append(c)
    if need and units_total < sum(need):
        bad.append("provides %s units for %s heads -- the belt under-houses "
                   "its own demand" % ("{:,}".format(units_total),
                                       "{:,}".format(sum(need))))

    # the cited PLC capacities, against those rows' own program lines.
    ok, note = _claim_citations(flat)
    (said if ok else bad).append(note)

    if bad:
        return False, "; ".join(bad)
    return True, "; ".join(said)


def _claim_citations(flat):
    """`PLC-007's 270` against PLC-007's own `90 bays → 270 units at 34 m²`.

    Two documents' worth of agreement for the price of one regex, and the one
    place an SHB row can be wrong about somebody else rather than about itself.
    """
    cites = []
    for p1, n1, p2, n2 in _TWO_PLC.findall(flat):
        cites += [(int(p1), _i(n1)), (int(p2), _i(n2))]
        # the two capacities must be what the row then subtracts
        pass
    for c, plc, a, b in _BEYOND.findall(flat):
        cites.append((int(plc), _i(b)))
    if not cites:
        return True, "cites no PLC capacity"
    bad, said = [], []
    for n, want in cites:
        blk = _plc_block(n)
        if not blk:
            bad.append("PLC-%03d has no row in PLACES.md" % n)
            continue
        mu = _PLC_UNITS.search(re.sub(r"\s+", " ", blk))
        if not mu:
            bad.append("PLC-%03d's row states no `N bays → M units` line to "
                       "check %s against" % (n, "{:,}".format(want)))
            continue
        bays, units, area = _i(mu.group(1)), _i(mu.group(2)), _i(mu.group(3))
        if units != want:
            bad.append("PLC-%03d's capacity is %s units and this row cites %s"
                       % (n, "{:,}".format(units), "{:,}".format(want)))
            continue
        mt = _TILING.search(blk)
        if mt and _i(mt.group(2)) != bays:
            bad.append("PLC-%03d says %s bays and its TILING total is %s"
                       % (n, "{:,}".format(bays), mt.group(2)))
            continue
        said.append("PLC-%03d %s units @%d m²" % (n, "{:,}".format(units), area))
    # the two-capacity sum: `PLC-007's 270 and PLC-008's 1,260: ... − 1,530`
    for p1, n1, p2, n2 in _TWO_PLC.findall(flat):
        tail = flat.split(n2, 1)[1]
        mm = re.search(r"−\s*([\d,]+)", tail)
        if mm:
            got, want = _i(n1) + _i(n2), _i(mm.group(1))
            if got != want:
                bad.append("PLC-%s's %s + PLC-%s's %s = %s and the row "
                           "subtracts %s" % (p1, n1, p2, n2,
                                             "{:,}".format(got),
                                             "{:,}".format(want)))
            else:
                said.append("%s + %s = %s subtracted" % (n1, n2,
                                                         "{:,}".format(got)))
    if bad:
        return False, "; ".join(bad)
    return True, "cites " + ", ".join(said)


def _claim_gross(rid, text):
    """gross = net × the derivation's own factor, to the quoted precision."""
    pre = _preamble()
    flat = re.sub(r"\s+", " ", text)
    clauses, pairs = _housing(text)
    if not clauses:
        mg = _GROSS.search(flat)
        if not mg:
            return False, "states no ≈ m² figure at all"
        return True, ("%s m² stated, no housing arithmetic to derive it from "
                      "(auth 5 assertion)" % mg.group(1))
    if pre["gross_factor"] is None:
        return False, "the Shell B derivation states no net→gross factor"
    net = 0
    for nb, per, area in clauses:
        if area is not None:
            net += nb * per * area
    for n, a in pairs:
        if any(x is None for _b, _p, x in clauses):
            net += n * a
    if not net:
        return False, "no unit area parsed, so gross cannot be derived"
    want = net * pre["gross_factor"]
    mg = _GROSS.search(flat)
    if not mg:
        return False, "states no ≈ m² gross figure to compare %s to" % round(want)
    said = _i(mg.group(1))
    slack = 50.0                       # half the 100 m² the annex quotes to
    incl = "incl. annexes" in flat
    if incl:
        ok = want <= said <= want * 1.02
        why = ("stated %s m² is not between the derived %s and +2%% for the "
               "annexes it says it includes"
               % ("{:,}".format(said), "{:,.0f}".format(want)))
    else:
        ok = abs(said - want) <= slack
        why = ("net %s m² × %.1f = %s and the row states %s -- off by %s, and "
               "the figure is quoted to the nearest 100"
               % ("{:,}".format(net), pre["gross_factor"],
                  "{:,.0f}".format(want), "{:,}".format(said),
                  "{:,.0f}".format(abs(said - want))))
    if not ok:
        return False, why
    return True, ("net %s × %.1f = %s ≈ the stated %s m²%s"
                  % ("{:,}".format(net), pre["gross_factor"],
                     "{:,.0f}".format(want), "{:,}".format(said),
                     " (incl. annexes)" if incl else ""))


def _claim_decks(rid, text):
    """The belt's deck range against the ring the model actually stacks.

    `interior.decks_in_ring` is 0.08 s for the whole station and is the same
    function the deck builder uses, so "decks 2-9" is checkable against the
    thing that would have to build them. `interior.cell_manifest` -- which the
    derivation paragraph cites for its 251/3,414 -- is 17 s and is NOT called;
    the 251 recomputes from `decks_in_ring` instead, and the 3,414 cells stay
    unchecked in this tier and are named as such.
    """
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import interior as IT                                        # noqa: PLC0415
    flat = re.sub(r"\s+", " ", text)
    head = flat.split("—", 1)[1] if "—" in flat else flat
    m = re.search(r"(Blue|Red|Green|Grey|Yellow)\s+rings?\s+(\d)(?:\s*[–-]\s*(\d))?",
                  head)
    if not m:
        m2 = re.search(r"###\s*SHB-\d+\s*—\s*(Yellow)", flat)
        if not m2:
            return False, "the heading names no sector/ring: %r" % head[:60]
        # SHB-09 is the one belt that names no ring: it is "at the 4 worked
        # nodes", which are PLC rows, not a deck stack. The anchor claim checks
        # those; there is no deck range to check here and saying so beats
        # inventing one.
        sector, rings = "yellow", []
    else:
        sector = m.group(1).lower()
        r0 = int(m.group(2))
        rings = list(range(r0, int(m.group(3)) + 1)) if m.group(3) else [r0]

    schema, prof = IT.load()
    have = {r: len(IT.decks_in_ring(schema, prof, sector, r)) for r in rings}
    if not rings:
        return True, ("%s: the row names worked nodes rather than a ring, so "
                      "it states no deck range" % sector)
    bad, said = [], ["%s ring%s %s -> %s decks"
                     % (sector, "s" if len(rings) > 1 else "",
                        ",".join(str(r) for r in rings),
                        "+".join(str(have[r]) for r in rings))]

    mr = _DECK_RANGE.search(flat)
    if mr and rings:
        lo, hi = int(mr.group(1)), int(mr.group(2))
        n = have[rings[0]]
        if hi >= n:
            bad.append("the row houses on decks %d–%d and %s ring %d stacks "
                       "%d decks (0..%d)" % (lo, hi, sector, rings[0], n, n - 1))
        else:
            said.append("decks %d–%d fit inside the %d stacked" % (lo, hi, n))
    mc = _DECK_COUNT.search(flat)
    if mc:
        want, got = int(mc.group(1)), sum(have.values())
        if want != got:
            bad.append("the row counts %d residential decks and %s rings %s "
                       "stack %d" % (want, sector,
                                     ",".join(str(r) for r in rings), got))
        else:
            said.append("%d residential decks = the rings' own stack" % got)

    # blocks per deck, and m² per deck, against the row's own ~ figures.
    clauses, _pairs = _housing(text)
    ndecks = None
    if mc:
        ndecks = int(mc.group(1))
    elif mr:
        ndecks = int(mr.group(2)) - int(mr.group(1)) + 1
    if ndecks and clauses:
        nb = sum(c[0] for c in clauses)
        mp = _PER_DECK.search(flat)
        if mp:
            want, got = _i(mp.group(1)), nb / ndecks
            if abs(want - got) > 0.5:
                bad.append("%d blocks over %d decks is %.2f/deck and the row "
                           "says ~%d" % (nb, ndecks, got, want))
            else:
                said.append("%d blocks / %d decks = %.2f ≈ ~%d"
                            % (nb, ndecks, got, want))
        mm = _M2_PER_DECK.search(flat)
        mg = _GROSS.search(flat)
        if mm and mg:
            want, got = _i(mm.group(1)), _i(mg.group(1)) / ndecks
            if abs(want - got) > 50:
                bad.append("%s m² over %d decks is %s/deck and the row says ~%s"
                           % (mg.group(1), ndecks, "{:,.0f}".format(got),
                              mm.group(1)))
            else:
                said.append("%s m²/deck ≈ ~%s" % ("{:,.0f}".format(got),
                                                  mm.group(1)))
    return (False, "; ".join(bad)) if bad else (True, "; ".join(said))


def _claim_manifest():
    """The derivation's 251 decks, recomputed from the ring stacks."""
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import interior as IT                                        # noqa: PLC0415
    pre = _preamble()
    if pre["decks"] is None:
        return False, "the derivation paragraph states no deck count"
    schema, prof = IT.load()
    got = sum(len(IT.decks_in_ring(schema, prof, s, r))
              for s in ("blue", "red", "green", "grey", "yellow")
              for r in range(4))
    if got != pre["decks"]:
        return False, ("the derivation says %d decks and the ring stacks sum "
                       "to %d" % (pre["decks"], got))
    return True, "%d decks = the ring stacks' own sum" % got


# ---------------------------------------------------------------------------
# the ledger, and the code it says it comes from
# ---------------------------------------------------------------------------
def _claim_roster():
    """Sec 2's roster table against `npc/schedule.ROLE_WEIGHTS`, both ways.

    THIS IS THE ONE CLAIM HERE THAT CAN FIND A DEFECT RATHER THAN A TYPO. The
    table's own header says it IS `schedule.py ROLE_WEIGHTS`; the belts size
    themselves off its housed column. If a species' role weight moves in Python
    and the annex does not, the station's housing stops fitting its population
    and no other gate in this project computes that comparison.
    """
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import npc.schedule as SC                                    # noqa: PLC0415
    led = _ledger()
    if len(led) < 5:
        return False, "the roster table did not parse (%d rows)" % len(led)
    bad, said = [], []

    # 1. each row's terms sum to its stated total; total + transfer = housed.
    housed_sum = 0
    for who, r in led.items():
        s = sum(v for _k, v in r["terms"])
        want = r["total"] if r["total"] is not None else r["housed"] - r["transfer"]
        if r["terms"] and s != want:
            bad.append("%s's role terms sum to %s and the row states %s"
                       % (who, "{:,}".format(s), "{:,}".format(want)))
        if r["terms"] and want + r["transfer"] != r["housed"]:
            bad.append("%s: %s %+d ≠ the housed %s"
                       % (who, "{:,}".format(want), r["transfer"],
                          "{:,}".format(r["housed"])))
        housed_sum += r["housed"]

    # 2. the column sum the table states about itself.
    m = re.search(r"Column sum:.*?=\s*([\d,]+)\s*exactly", _places_md())
    if not m:
        bad.append("the table states no column sum")
    elif _i(m.group(1)) != housed_sum:
        bad.append("the housed column sums to %s and the table claims %s"
                   % ("{:,}".format(housed_sum), m.group(1)))
    else:
        said.append("housed column = %s" % "{:,}".format(housed_sum))

    # 3. and against the live matrix, role by role.
    live = {}
    for _sp, roles in SC.ROLE_WEIGHTS.items():
        for role, n in roles.items():
            live[role] = live.get(role, 0) + n
    spec = {}
    unmapped = []
    for who, r in led.items():
        for k, v in r["terms"]:
            role = _ROLE_OF.get(k)
            if role is None:
                unmapped.append("%s/%s" % (who, k))
                continue
            spec[role] = spec.get(role, 0) + v
    if unmapped:
        bad.append("ledger terms this harness cannot map to a ROLE_WEIGHTS "
                   "role: %s -- a parse failure, not a disagreement"
                   % ", ".join(unmapped))
    for role in sorted(set(live) | set(spec)):
        a, b = spec.get(role), live.get(role)
        if a is None:
            bad.append("ROLE_WEIGHTS has %s=%s and the ledger names no such row"
                       % (role, "{:,}".format(b)))
        elif b is None:
            bad.append("the ledger houses %s %s and ROLE_WEIGHTS has no such "
                       "role" % ("{:,}".format(a), role))
        elif a != b:
            bad.append("%s: ledger %s, ROLE_WEIGHTS %s"
                       % (role, "{:,}".format(a), "{:,}".format(b)))
    if sum(live.values()) != housed_sum:
        bad.append("ROLE_WEIGHTS totals %s and the housed column %s"
                   % ("{:,}".format(sum(live.values())),
                      "{:,}".format(housed_sum)))
    else:
        said.append("%d roles agree with ROLE_WEIGHTS, %s heads"
                    % (len(live), "{:,}".format(housed_sum)))
    if bad:
        return False, "; ".join(bad[:4])
    return True, "; ".join(said)


# Each belt's own tie to the ledger: (what it cites, how it is derived).
# Written per row because each belt takes a DIFFERENT slice -- SHB-04 takes two
# housed cells verbatim, SHB-01 takes a total less a parenthetical, SHB-06 takes
# a transfer plus the breathers already in Green.
def _tie_01(flat, led):
    blue = led["Blue"]
    mg = re.search(r"([\d,]+)\s*guild", blue["raw"])
    if not mg:
        return False, "Blue's ledger cell names no guild figure"
    guild = _i(mg.group(1))
    m = re.search(r"([\d,]+)\s*EF/EA heads", flat)
    if not m:
        return False, "the row states no EF/EA head figure"
    ef = _i(m.group(1))
    if ef + guild != blue["total"]:
        return False, ("EF/EA %s + guild %s = %s and Blue's role rows total %s"
                       % ("{:,}".format(ef), "{:,}".format(guild),
                          "{:,}".format(ef + guild),
                          "{:,}".format(blue["total"])))
    return True, ("EF/EA %s + guild %s = Blue's %s"
                  % ("{:,}".format(ef), "{:,}".format(guild),
                     "{:,}".format(blue["total"])))


def _tie_02(flat, led):
    blue = led["Blue"]
    mg = re.search(r"([\d,]+)\s*guild", blue["raw"])
    m = re.search(r"Blue:\s*([\d,]+)\s*−\s*([\d,]+)", flat)
    if not (mg and m):
        return False, "the guild/Gaim figures did not parse"
    if _i(m.group(1)) != _i(mg.group(1)):
        return False, ("the row houses %s guild and Blue's ledger cell says %s"
                       % (m.group(1), mg.group(1)))
    if _i(m.group(2)) != abs(blue["transfer"]):
        return False, ("the row moves %s Gaim out and Blue's breather transfer "
                       "is %d" % (m.group(2), blue["transfer"]))
    return True, ("guild %s less the ledger's own %d-head breather transfer"
                  % (mg.group(1), abs(blue["transfer"])))


def _tie_04(flat, led):
    said = []
    for who, key in (("Red (civilian)", "civilian"),
                     ("Red (transient)", "transient")):
        h = led[who]["housed"]
        if "{:,}".format(h) not in flat:
            return False, ("%s's housed %s does not appear in the row"
                           % (who, "{:,}".format(h)))
        said.append("%s %s" % (key, "{:,}".format(h)))
    return True, "takes the ledger's housed cells verbatim: " + ", ".join(said)


def _tie_06(flat, led):
    g = led["Green"]
    m = re.search(r"([\d,]+)\s*units for\s*([\d,]+)\s*housed beyond the PLC "
                  r"rows'\s*([\d,]+)", flat)
    if not m:
        return False, "the row's units/housed/PLC-beyond triple did not parse"
    units, hh, plc = _i(m.group(1)), _i(m.group(2)), _i(m.group(3))
    if hh + plc != g["housed"]:
        return False, ("%s housed here + %s in the PLC rows = %s and Green's "
                       "housed cell is %s" % ("{:,}".format(hh),
                                              "{:,}".format(plc),
                                              "{:,}".format(hh + plc),
                                              "{:,}".format(g["housed"])))
    mb = re.search(r"([\d,]+)\s*@22 m²", flat)
    if not mb:
        return False, "the row states no breather-zone unit count"
    br = _i(mb.group(1))
    # every breather in the station, from the live matrix: the preamble names
    # Gaim and Abbai as the two breather species.
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import npc.schedule as SC                                    # noqa: PLC0415
    live = sum(sum(SC.ROLE_WEIGHTS[s].values()) for s in ("gaim", "abbai")
               if s in SC.ROLE_WEIGHTS)
    if br != live:
        return False, ("the zone extensions hold %s breathers and ROLE_WEIGHTS "
                       "has %s Gaim+Abbai heads" % ("{:,}".format(br),
                                                    "{:,}".format(live)))
    if units < hh:
        return False, "%d units for %d housed" % (units, hh)
    return True, ("%s + %s = Green's housed %s; %s breathers = every Gaim and "
                  "Abbai head in ROLE_WEIGHTS"
                  % ("{:,}".format(hh), "{:,}".format(plc),
                     "{:,}".format(g["housed"]), "{:,}".format(br)))


def _tie_08(flat, led):
    m = re.search(r"the\s*([\d,]+)\s*\(9 m² partitions", flat)
    if not m:
        return False, "the refugee overspill figure did not parse"
    ref = _i(m.group(1))
    grey = dict(led["Grey"]["terms"]).get("refugees")
    if grey != ref:
        return False, ("the overspill houses %s and Grey's ledger row has %s "
                       "refugees" % ("{:,}".format(ref),
                                     "{:,}".format(grey or 0)))
    return True, "%s = Grey's own refugee row" % "{:,}".format(ref)


_TIES = {"SHB-001": _tie_01, "SHB-002": _tie_02, "SHB-004": _tie_04,
         "SHB-006": _tie_06, "SHB-008": _tie_08}


# ---------------------------------------------------------------------------
# Sec 4 TOTALS -- the same belts, added up a second time, by a different table
# ---------------------------------------------------------------------------
# `| Blue | 36 | 36 → **7,692** | 265,800 (SHB-01/02) | 12,930 (270 + 1,260 +
#   3,720 + 7,680) vs **12,870** ✓ |`
#
# A SECOND STATEMENT OF A NUMBER IS THE CHEAPEST GATE THERE IS, and this annex
# states every belt's gross and every sector's capacity twice. The rows are
# independent prose written at different times, so they can disagree -- and one
# of them does.
_TOTALS_ROW = re.compile(r"^\|\s*(Blue|Red|Green|Grey|Yellow)\s*\|\s*(\d+)\s*\|"
                         r"([^|]*)\|([^|]*)\|([^|]*)\|\s*$")
_SECTOR_OF = {1: "Blue", 2: "Blue", 3: "Red", 4: "Red", 5: "Red",
              6: "Green", 7: "Green", 8: "Grey", 9: "Yellow"}
_LEDGER_OF = {"Blue": ("Blue",), "Red": ("Red (civilian)", "Red (transient)"),
              "Green": ("Green",), "Grey": ("Grey",), "Yellow": ("Yellow",)}


def _totals():
    if "tot" in _CACHE:
        return _CACHE["tot"]
    body = _places_md()
    i = body.find("# 4. TOTALS")
    rows = {}
    for ln in body[i:].splitlines() if i >= 0 else ():
        m = _TOTALS_ROW.match(ln.strip())
        if m:
            rows[m.group(1)] = {"places": int(m.group(2)),
                                "tiling": m.group(3), "gross": m.group(4),
                                "capacity": m.group(5)}
    _CACHE["tot"] = rows
    return rows


def _claim_totals(n, text):
    """This belt against Sec 4's per-sector reconciliation of the same belts."""
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    sector = _SECTOR_OF[n]
    tot = _totals().get(sector)
    if not tot:
        return False, "Sec 4 TOTALS has no %s row" % sector
    bad, said = [], []

    # 1. the places count, against the live register.
    live = sum(1 for p in DIR.PLACES if p["sector"] == sector.lower())
    if live != tot["places"]:
        bad.append("TOTALS says %s holds %d places and directory.PLACES has %d"
                   % (sector, tot["places"], live))
    else:
        said.append("%d places = the register" % live)

    # 2. the Shell B gross, against the belts' own ≈ figures.
    nums = [_i(x) for x in _NUM.findall(tot["gross"])
            if len(x.replace(",", "")) > 2]
    # `(SHB-01/02)` and `(SHB-03/04/05)` are LISTS. A plain `SHB-(\d+)` reads
    # the first id and drops the rest, which turned a 300 m² disagreement into
    # a 172,100 m² one -- a parse defect that looks far more like a finding
    # than the finding it was hiding.
    ids = []
    for tok in re.findall(r"SHB-([\d/]+)", tot["gross"]):
        ids += [int(x) for x in tok.split("/") if x.isdigit()]
    if not nums:
        bad.append("the %s gross cell states no figure" % sector)
    else:
        total = nums[0]
        comps = nums[1:]
        if "+" in tot["gross"] and len(comps) > 1:
            if sum(comps) != total:
                bad.append("%s's gross components %s sum to %s, cell says %s"
                           % (sector, comps, "{:,}".format(sum(comps)),
                              "{:,}".format(total)))
            else:
                said.append("gross %s = its own %d components"
                            % ("{:,}".format(total), len(comps)))
        elif ids:
            parts = []
            for b in ids:
                blk = _blocks_md().get("SHB-%02d" % b)
                mg = _GROSS.search(re.sub(r"\s+", " ", blk[1])) if blk else None
                if not mg:
                    bad.append("SHB-%02d states no ≈ m² for the %s total"
                               % (b, sector))
                else:
                    parts.append((b, _i(mg.group(1))))
            s = sum(v for _b, v in parts)
            if parts and abs(s - total) > 50 * len(parts):
                bad.append("TOTALS says %s m² of Shell B in %s and its own "
                           "belts state %s (%s) -- a %s m² disagreement "
                           "between two tables in one annex"
                           % ("{:,}".format(total), sector, "{:,}".format(s),
                              " + ".join("SHB-%02d %s" % (b, "{:,}".format(v))
                                         for b, v in parts),
                              "{:,}".format(abs(s - total))))
            elif parts:
                said.append("gross %s ≈ %s from %d belts"
                            % ("{:,}".format(total), "{:,}".format(s),
                               len(parts)))

    # 3. the capacity cell: components sum, and cover the ledger's housed.
    cap = tot["capacity"]
    cn = [_i(x) for x in _NUM.findall(cap) if len(x.replace(",", "")) > 2]
    mv = re.search(r"vs\s*\*\*([\d,]+)\*\*", cap)
    if cn and mv:
        capacity, housed = cn[0], _i(mv.group(1))
        comps = [x for x in cn[1:] if x != housed]
        if "+" in cap and len(comps) > 1 and sum(comps) != capacity:
            bad.append("%s's capacity components sum to %s, cell says %s"
                       % (sector, "{:,}".format(sum(comps)),
                          "{:,}".format(capacity)))
        want = sum(_ledger()[k]["housed"] for k in _LEDGER_OF[sector])
        if housed != want:
            bad.append("TOTALS houses %s in %s and the roster ledger houses %s"
                       % ("{:,}".format(housed), sector, "{:,}".format(want)))
        elif capacity < housed:
            bad.append("%s provides %s for %s housed"
                       % (sector, "{:,}".format(capacity),
                          "{:,}".format(housed)))
        else:
            said.append("capacity %s ≥ housed %s = the ledger"
                        % ("{:,}".format(capacity), "{:,}".format(housed)))
        # this belt's own units must appear among the capacity components
        clauses, _p = _housing(text)
        if clauses and comps:
            mine = sum(nb * per for nb, per, _a in clauses)
            each = [nb * per for nb, per, _a in clauses]
            if mine not in comps and not all(e in comps for e in each):
                bad.append("SHB-%02d provides %s units and %s's capacity "
                           "components are %s" % (n, "{:,}".format(mine),
                                                  sector, comps))
            else:
                said.append("its %s units are in the capacity sum"
                            % "{:,}".format(mine))
    if bad:
        return False, "; ".join(bad)
    return True, "; ".join(said)


def _claim_anchors(text):
    """Every PLC the belt names resolves to a place the register carries."""
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import directory as DIR                                      # noqa: PLC0415
    keys = _plc_keys()
    bad, seen = [], []
    for n in sorted({int(x) for x in _PLC_REF.findall(text)}):
        k = keys.get(n)
        if not k:
            bad.append("PLC-%03d names no place in PLACES.md" % n)
            continue
        try:
            DIR.by_key(k)
        except KeyError:
            bad.append("PLC-%03d `%s` is in no register row" % (n, k))
            continue
        seen.append(k)
    if bad:
        return False, "; ".join(bad)
    if not seen:
        return True, "names no PLC anchor"
    return True, ("%d PLC anchor(s) resolve: %s" % (len(seen),
                                                    ", ".join(seen[:5])))


# ---------------------------------------------------------------------------
# lettered annexes
# ---------------------------------------------------------------------------
def _annexe(rid, letter):
    """One lettered annexe's own text out of its parent's block.

    THE LAST LETTER'S END IS THE TRAP. `e.` in SHB-02 has no `f.` after it, so
    a naive slice to end-of-block swallows the row's CHECK paragraph -- and the
    CHECK cites PLCs the annexe never mentions, which then get reported as that
    annexe's resolved anchors. An annexe ends at the next lettered marker OR at
    the next top-level `- ` bullet, whichever comes first.
    """
    parent = "SHB-%02d" % int(rid.split("-")[1].split(".")[0])
    blk = _blocks_md().get(parent)
    if not blk:
        return None, "no SHB block headed %s" % parent
    flat = re.sub(r"[ \t]+", " ", blk[1])
    marks = [(m.group(1), m.start()) for m in _LETTER.finditer(flat)]
    have = [L for L, _s in marks]
    if letter not in have:
        return None, ("the parent declares letters %s and the registry asks "
                      "for `%s.`" % (sorted(set(have)) or "(none)", letter))
    i = have.index(letter)
    start = marks[i][1]
    end = marks[i + 1][1] if i + 1 < len(marks) else len(flat)
    nxt = flat.find("\n- ", start)
    if nxt != -1:
        end = min(end, nxt)
    return re.sub(r"\s+", " ", flat[start:end]).strip(), ""


# Row-specific numbers a lettered annexe states that the code has an opinion
# about. Each returns (ok, note) and each can fail: the values are read live.
def _sub_02c(txt):
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import economy as EC                                         # noqa: PLC0415
    m = re.search(r"pays\s*(\d+)[–-](\d+)\s*cr day labour", txt)
    if not m:
        return False, "the day-labour band did not parse"
    lo, hi = float(m.group(1)), float(m.group(2))
    if (lo, hi) != (EC.CASUAL_LO, EC.CASUAL_HI):
        return False, ("the annexe pays %g–%g cr and economy.py's casual band "
                       "is %g–%g" % (lo, hi, EC.CASUAL_LO, EC.CASUAL_HI))
    return True, "%g–%g cr = economy.CASUAL_LO/HI" % (lo, hi)


def _sub_02b(txt):
    m = re.search(r"(\d+)\s*cells feeding PLC-(\d+)", txt)
    if not m:
        return False, "the cell count did not parse"
    n, plc = int(m.group(1)), int(m.group(2))
    blk = _plc_block(plc)
    mb = re.search(r"\*\*(\d+) cells", re.sub(r"\s+", " ", blk))
    if not mb:
        return False, "PLC-%03d states no cell count to feed" % plc
    if n > int(mb.group(1)):
        return False, ("the annexe feeds %d cells into PLC-%03d's %s"
                       % (n, plc, mb.group(1)))
    return True, "%d cells feeding PLC-%03d's %s" % (n, plc, mb.group(1))


def _sub_08b(txt):
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import economy as EC                                         # noqa: PLC0415
    m = re.search(r"\((\d+) cr/night bunk hall,\s*([\d,]+) bunks", txt)
    if not m:
        return False, "the dosshouse rate/bunk count did not parse"
    rate, bunks = float(m.group(1)), _i(m.group(2))
    lo, hi = EC.ladder("bunk_dosshouse")
    if not (lo <= rate <= hi):
        return False, ("the annexe charges %g cr/night and economy.py's "
                       "bunk_dosshouse ladder is %g–%g cr" % (rate, lo, hi))
    return True, "%g cr/night = economy's bunk_dosshouse %g–%g, %d bunks" % (
        rate, lo, hi, bunks)


def _sub_08d(txt):
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import npc.faction as FA                                     # noqa: PLC0415
    m = re.search(r"(\d+)[–-](\d+)\s*Rangers aboard", txt)
    if not m:
        return False, "the Ranger head range did not parse"
    lo, hi = int(m.group(1)), int(m.group(2))
    got = FA.head_count("FAC-28")
    if not (lo <= got <= hi):
        return False, ("the annexe says %d–%d Rangers aboard and faction.py "
                       "counts %d" % (lo, hi, got))
    return True, "%d–%d Rangers, faction.py counts %d" % (lo, hi, got)


def _sub_08f(txt):
    """The refugee partition arithmetic, the one sub-row that is a sum."""
    pre = _preamble()
    m = re.search(r"the\s*([\d,]+)\s*\((\d+) m² partitions ×([\d.]+)[^=]*=\s*"
                  r"\*\*([\d,]+) m² gross\*\*", txt)
    if not m:
        return False, "the partition arithmetic did not parse"
    n, a, f, gross = _i(m.group(1)), int(m.group(2)), float(m.group(3)), _i(m.group(4))
    if f != pre["gross_factor"]:
        return False, ("this annexe uses ×%.2f and the Shell B derivation says "
                       "×%.2f is applied everywhere" % (f, pre["gross_factor"]))
    want = n * a * f
    if abs(want - gross) > 50:
        return False, ("%s × %d m² × %.1f = %s and the annexe states %s"
                       % ("{:,}".format(n), a, f, "{:,.0f}".format(want),
                          "{:,}".format(gross)))
    if a not in pre["ladder"].values():
        return False, "%d m² is not on the INV-032 ladder" % a
    return True, ("%s × %d × %.1f = %s m² gross" % ("{:,}".format(n), a, f,
                                                    "{:,}".format(gross)))


_SUB_NUMBERS = {
    "SHB-002.b": _sub_02b, "SHB-002.c": _sub_02c,
    "SHB-008.b": _sub_08b, "SHB-008.d": _sub_08d, "SHB-008.f": _sub_08f,
}


def _check_sub(rid):
    letter = rid.split(".")[-1]
    txt, why = _annexe(rid, letter)
    if txt is None:
        return False, why
    results = []
    if not re.match(r"[a-z]\.\s+\*\*[^*]+\*\*", txt):
        results.append(("title", False, "names no bolded annexe title"))
    else:
        results.append(("title", True,
                        re.match(r"[a-z]\.\s+\*\*([^*]+)\*\*", txt).group(1)))
    results.append(("anchors",) + _claim_anchors(txt))
    tiers = sorted({int(t) for t in _TIERS.findall(txt)})
    if tiers and (min(tiers) < 1 or max(tiers) > 4):
        results.append(("tiers", False,
                        "tags a tier outside T1–T4: %s" % tiers))
    elif tiers:
        results.append(("tiers", True, "T-tiers " + ",".join(str(t) for t in tiers)))
    fn = _SUB_NUMBERS.get(rid)
    if fn is not None:
        results.append(("number",) + fn(txt))
    bad = [(n, t) for n, ok, t in results if not ok]
    good = [(n, t) for n, ok, t in results if ok]
    if bad:
        return False, "; ".join("%s: %s" % (n, t) for n, t in bad)
    return True, "; ".join("%s: %s" % (n, t) for n, t in good)


# ---------------------------------------------------------------------------
def check(row):
    rid = row.get("id", "")
    if "." in rid:
        return _check_sub(rid)
    n = int(rid.split("-")[1])
    key = "SHB-%02d" % n
    blk = _blocks_md().get(key)
    if not blk:
        return False, "PLACES.md has no `### %s` block" % key
    line, text = blk
    at = row.get("at", "")
    if at and at.rsplit(":", 1)[-1].isdigit() and int(at.rsplit(":", 1)[1]) != line:
        return False, ("the registry points at %s and `### %s` is at line %d"
                       % (at, key, line))
    flat = re.sub(r"\s+", " ", text)

    results = [("blocks",) + _claim_blocks(key, text),
               ("gross",) + _claim_gross(key, text),
               ("decks",) + _claim_decks(key, text),
               ("anchors",) + _claim_anchors(text),
               ("totals",) + _claim_totals(n, text),
               ("manifest",) + _claim_manifest(),
               ("roster",) + _claim_roster()]
    tie = _TIES.get("SHB-%03d" % n)
    if tie is not None:
        results.append(("ledger tie",) + tie(flat, _ledger()))
    bad = [(a, t) for a, ok, t in results if not ok]
    good = [(a, t) for a, ok, t in results if ok]
    if bad:
        return False, "; ".join("%s: %s" % (a, t) for a, t in bad)
    return True, ("%s arithmetic consistent [%s] -- but NO Shell B builder "
                  "exists, so the row's own CHECK (enterable numbered units, "
                  "the commute tide, no dead ends) is unsettleable here"
                  % (key, "; ".join("%s: %s" % (a, t) for a, t in good)))


# ---------------------------------------------------------------------------
def _selftest(out=print):
    """Every row, then the negative controls that prove each claim discriminates."""
    import sys                                                   # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pre = _preamble()
    out("derivation: %d units/block, ×%.1f gross, ladder %s, %s decks / %s cells"
        % (pre["units_per_block"], pre["gross_factor"],
           sorted(set(pre["ladder"].values())), pre["decks"], pre["cells"]))
    led = _ledger()
    for who, r in led.items():
        out("  ledger %-16s %2d terms, total %-9s transfer %+6d housed %s"
            % (who, len(r["terms"]),
               "{:,}".format(r["total"]) if r["total"] else "-",
               r["transfer"], "{:,}".format(r["housed"])))
    out("")

    ids = []
    for n in range(1, 10):
        ids.append("SHB-%03d" % n)
        blk = _blocks_md().get("SHB-%02d" % n)
        for L in sorted({m.group(1) for m in _LETTER.finditer(blk[1])}):
            ids.append("SHB-%03d.%s" % (n, L))
    fails = 0
    for rid in ids:
        at = "docs/spec/PLACES.md:%d" % _blocks_md()[
            "SHB-%02d" % int(rid.split("-")[1].split(".")[0])][0]
        ok, note = check({"id": rid, "at": at})
        fails += 0 if ok else 1
        out("%-12s %-4s %s" % (rid, "PASS" if ok else "FAIL", note[:200]))
    out("")
    out("%d of %d SHB rows fail" % (fails, len(ids)))

    out("")
    out("-- negative controls: each breaks ONE input and must be caught --")
    md = _places_md()

    def bend(old, new, rid, label):
        if old not in md:                                  # pragma: no cover
            out("%-34s -> CONTROL BROKEN: %r is not in PLACES.md"
                % (label, old[:40]))
            return
        _CACHE["md"] = md.replace(old, new, 1)
        for k in ("shb", "pre", "led", "plc", "tot"):
            _CACHE.pop(k, None)
        ok, note = check({"id": rid, "at": ""})
        out("%-34s -> %-4s %s" % (label, "PASS" if ok else "FAIL", note[:260]))
        _CACHE["md"] = md
        for k in ("shb", "pre", "led", "plc", "tot"):
            _CACHE.pop(k, None)

    bend("**62 blocks**", "**61 blocks**", "SHB-001", "SHB-01 one block fewer")
    bend("≈93,700 m² gross", "≈95,000 m² gross", "SHB-001", "SHB-01 gross bent")
    bend("across decks 2–9", "across decks 2–19", "SHB-001", "SHB-01 decks past the stack")
    bend("PLC-007's 270", "PLC-007's 280", "SHB-001", "SHB-01 miscites PLC-007")
    bend("· security 500 ·", "· security 550 ·", "SHB-001", "ledger security +50")
    bend("**32 residential decks", "**34 residential decks", "SHB-004",
         "SHB-04 deck count bent")
    bend("**2,361 blocks**", "**2,300 blocks**", "SHB-004", "SHB-04 under-houses")
    bend("**6,250 @22 m²", "**6,000 @22 m²", "SHB-006", "SHB-06 breather split bent")
    bend("pays 8–15 cr day labour", "pays 9–15 cr day labour", "SHB-002.c",
         "SHB-02.c day rate vs economy.py")
    bend("mechanic; 20–60", "mechanic; 70–90", "SHB-008.d",
         "SHB-08.d Ranger count vs faction.py")
    bend("×1.4 circulation/wash = **163,800 m² gross**",
         "×1.4 circulation/wash = **173,800 m² gross**", "SHB-008.f",
         "SHB-08.f partition arithmetic")

    # and a code-side control: move a role weight, not the annex.
    import npc.schedule as SC                                    # noqa: PLC0415
    keep = SC.ROLE_WEIGHTS["human"]["security"]
    SC.ROLE_WEIGHTS["human"]["security"] = keep + 50
    _CACHE.pop("led", None)
    ok, note = check({"id": "SHB-001", "at": ""})
    out("%-34s -> %-4s %s" % ("ROLE_WEIGHTS security +50 in CODE",
                              "PASS" if ok else "FAIL", note[:260]))
    SC.ROLE_WEIGHTS["human"]["security"] = keep
    _CACHE.pop("led", None)

    # a letter the parent does not declare
    ok, note = check({"id": "SHB-001.z", "at": ""})
    out("%-34s -> %-4s %s" % ("SHB-01.z (undeclared letter)",
                              "PASS" if ok else "FAIL", note[:150]))
    return fails


if __name__ == "__main__":                                       # pragma: no cover
    import sys
    sys.path.insert(0, os.path.join(ROOT, "station"))
    _selftest()
