"""GDS-001: the goods vocabulary, against `station/economy.py`'s `GOODS`.

ONE ROW, AND IT IS THE MOST DIRECTLY CHECKABLE ROW IN THE REGISTRY, because it
is the only one whose subject already exists in Python as a table. PLACES.md
Sec 0.3 declares a vocabulary -- a seed set of named wares, four fields per
entry, a supply enumeration, and a floor -- and `economy.GOODS` is that table.
Everything here is a comparison between the two, which is what makes it able to
fail on live content rather than on a typo.

THE ROW'S OWN CLAUSES, each mapped to a claim:

  "Each entry: name . origin species/world . price band on the SYS-04 ladder .
   supply source {drum | hydroponics | import | route}"
      -> `_claim_fields`: every Good carries all four, its klass resolves in
         `CLASS_BAND`, and its supply is one of the FOUR the row enumerates.
  "Seed set (attested names first ...)"
      -> `_claim_seed`: every name the sentence lists resolves to a Good.
  "Floor: >=60 named goods at completion, every one placed behind at least one
   named counter and one supply source."
      -> `_claim_floor`: `len(GOODS)` against 60, and every Good reachable from
         some place in the register.
  "spoo sits on a Narn row at 1-2 cr"        -> `_claim_spoo`
  "the G'Quan Eth row carries its customs class"  -> `_claim_gqe`
  "no stall anywhere sells unnamed 'goods'"  -> `_claim_named`

WHAT IS NOT CHECKED, AND WHY IT CANNOT BE HERE. Two clauses need something this
tier does not have:

  * "every Shell A stock/menu reference resolves to a row of it" is a claim
    about the OTHER direction -- that no PLC row names a ware the vocabulary
    lacks. Deciding it needs a lexicon of what counts as a ware in English
    prose; scanning PLACES.md for the 34 names we already have would only ever
    confirm itself, which is the shape of check this project calls a museum
    piece. Stated as unsettled rather than faked.
  * "the Fresh Air menu names tonight's dish from a PLC-110 field or PLC-026
    rack consignment" needs a MENU, and there is no menu function anywhere in
    `economy.py` or `hospitality.py`. The settleable half -- that Fresh Air's
    stock contains at least one drum- or hydroponics-supplied line -- is
    checked and reported as the half it is.

THE SEED MATCHER IS THE PART THAT HAD TO BE MEASURED. The seed set is prose:
`**spoo** (Narn farmed delicacy; G'Dral's row)` and
`Drazi duct-sealant + hardware grades (Brakk's stall)` and
`drum staples (grain, greens, orchard fruit - ...)` are three different shapes
in one sentence, and `GOODS` writes two of them differently again ("hydroponic
specialty rack" singular, "Drazi hardware grade B", "Vree instrument optics"
where the spec says "instrument-grade optics"). A matcher that demanded exact
strings reported 13 of 22 seed items missing, which is a parse rate, not a
finding. Measuring the shapes gave three rules -- split on `+`, fall back to the
parenthetical's comma terms, and match on content words covering two thirds of
the shorter name -- and the residue is ONE item. `--selftest` prints the
residue, so a future widening of this matcher is visible rather than silent.
"""
import os
import re

SUFFICIENT = False

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CACHE = {}

_SUPPLY_SET = re.compile(r"supply source \{([^}]*)\}")
_FLOOR = re.compile(r"≥\s*(\d+)\s*named goods")
_SPOO = re.compile(r"spoo sits on a (\w+) row at\s*(\d+)[–-](\d+)\s*cr")
_SEED_HEAD = "Seed set"
_PAREN = re.compile(r"\(([^)]*)\)")
_STOP = {"the", "a", "an", "of", "and", "grade", "b"}


def _row_text(row):
    from spec_harness import spec_text                            # noqa: PLC0415
    return spec_text(row.get("at", ""), lines=40)


def _flat(text):
    """The row on one line.

    The annex hard-wraps at 88 columns, so `spoo sits on a Narn row\\nat 1-2 cr`
    is one claim split across two lines and a regex written against the
    sentence finds nothing. That reads as "the row makes no price claim", which
    is a reader failure wearing a finding's clothes -- the exact confusion this
    package's rule 2 is about.
    """
    return re.sub(r"\s+", " ", text)


def _norm_words(s):
    """Content words of a ware name, singularised crudely and stop-listed.

    `grade` and `b` are stop words because `GOODS` writes "Drazi hardware
    grade B" for what the annex calls "hardware grades" and "Vree instrument
    optics" for "Vree instrument-grade optics" -- the grade token is noise in
    both directions, and removing it from BOTH sides is symmetric rather than
    a thumb on the scale.
    """
    s = s.lower().replace("’", "'")
    s = re.sub(r"[^a-z0-9']+", " ", s)
    out = []
    for w in s.split():
        if w.endswith("s") and len(w) > 3:
            w = w[:-1]
        if w and w not in _STOP:
            out.append(w)
    return set(out)


def _match(seed, names):
    """The Good whose name this seed phrase denotes, or None.

    Content-word overlap covering two thirds of the SHORTER name, with at
    least one word shared. Directional rules ("seed is a prefix of the name")
    were tried first and miss "hardware grades" against "Drazi hardware
    grade B" in one direction and "Vree instrument-grade optics" against "Vree
    instrument optics" in the other.
    """
    sw = _norm_words(seed)
    if not sw:
        return None
    best, score = None, 0.0
    for n in names:
        nw = _norm_words(n)
        if not nw:
            continue
        shared = len(sw & nw)
        if not shared:
            continue
        cov = shared / float(min(len(sw), len(nw)))
        if cov >= 2 / 3.0 and cov > score:
            best, score = n, cov
    return best


def _seed_items(text):
    """The seed sentence, split into the wares it names.

    Returns [(phrase, [alternative phrases])]. The alternatives are the
    parenthetical's comma terms, which is how "drum staples (grain, greens,
    orchard fruit)" names three wares in one item.
    """
    i = text.find(_SEED_HEAD)
    if i < 0:
        return []
    j = text.find("**Floor", i)
    body = text[i:j if j > 0 else len(text)]
    body = body.split(":", 1)[1] if ":" in body else body
    body = re.sub(r"\s+", " ", body).replace("**", "")
    out = []
    for chunk in body.split("·"):
        chunk = chunk.strip().rstrip(".")
        if not chunk:
            continue
        alts = []
        mp = _PAREN.search(chunk)
        if mp:
            inner = mp.group(1).split("—")[0]
            alts = [t.strip() for t in inner.split(",") if t.strip()]
            chunk = chunk[:mp.start()].strip()
        for part in chunk.split(" + "):
            part = part.strip()
            if part:
                out.append((part, alts))
    return out


# ---------------------------------------------------------------------------
def _claim_fields(text, EC):
    """Four fields per entry, and the supply enumeration the row declares."""
    m = _SUPPLY_SET.search(_flat(text))
    if not m:
        return False, "the row declares no supply-source enumeration"
    declared = {w.strip() for w in m.group(1).split("|") if w.strip()}
    bad = []
    used = {}
    for g in EC.GOODS:
        for f in ("name", "origin", "supply", "klass"):
            if not getattr(g, f, None):
                bad.append("%r has no %s" % (g.name, f))
        if g.klass not in EC.CLASS_BAND:
            bad.append("%r's class %r is on no SYS-04 band" % (g.name, g.klass))
        used.setdefault(g.supply, []).append(g.name)
    extra = sorted(set(used) - declared)
    if extra:
        bad.append("the row enumerates supply sources {%s} and economy.py uses "
                   "%s as well (%d line(s), e.g. %s)"
                   % (" | ".join(sorted(declared)), ", ".join(extra),
                      sum(len(used[e]) for e in extra), used[extra[0]][0]))
    if bad:
        return False, "; ".join(bad[:3])
    return True, ("%d entries, 4 fields each, supplies {%s}"
                  % (len(EC.GOODS), " | ".join(sorted(used))))


def _claim_seed(text, EC):
    """Every ware the seed sentence names resolves to a row of the table."""
    items = _seed_items(text)
    if len(items) < 10:
        return False, ("the seed sentence parsed to %d items -- that is a "
                       "reader failure, not a disagreement" % len(items))
    names = [g.name for g in EC.GOODS]
    missing = []
    for phrase, alts in items:
        if _match(phrase, names):
            continue
        if any(_match(a, names) for a in alts):
            continue
        missing.append(phrase)
    if missing:
        return False, ("%d of %d seed wares are in no economy.GOODS row: %s"
                       % (len(missing), len(items),
                          ", ".join(repr(x) for x in missing)))
    return True, "all %d seed wares resolve" % len(items)


def _claim_floor(text, EC):
    """The >=60 floor, and every ware behind a counter and a supply."""
    m = _FLOOR.search(_flat(text))
    if not m:
        return False, "the row states no goods floor"
    want = int(m.group(1))
    bad = []
    if len(EC.GOODS) < want:
        bad.append("the floor is ≥%d named goods at completion and "
                   "economy.GOODS holds %d -- %d short"
                   % (want, len(EC.GOODS), want - len(EC.GOODS)))
    # "placed behind at least one named counter": a counter in the register
    # whose derived stock actually lists it, not merely a declared function.
    stocked = set()
    for k in EC.counters():
        stocked |= set(EC.goods_list(k))
    # TWO DIFFERENT FAILURES WEAR ONE NUMBER HERE, and separating them is the
    # whole value of the claim. A ware with `sold_by = ()` is UNSELLABLE BY
    # DESIGN -- economy.py says so in its own note ("pumped, never craned -- no
    # counter sells it") -- so that group is a straight disagreement with the
    # row's "every one placed behind at least one named counter". A ware that
    # DOES declare a selling function and still reaches no counter is a
    # different thing: `goods_list` caps a counter at MAX_LINES and ranks by
    # species weight, so the line exists and is never drawn. One is a spec
    # conflict, the other is a coverage hole.
    unplaced = [g for g in EC.GOODS if g.name not in stocked]
    nofn = [g.name for g in unplaced if not g.sold_by]
    undrawn = [g.name for g in unplaced if g.sold_by]
    if nofn:
        bad.append("%d ware(s) declare no selling function at all, so no "
                   "counter can carry them: %s" % (len(nofn), ", ".join(nofn)))
    if undrawn:
        bad.append("%d ware(s) declare a selling function and are still on no "
                   "counter's derived list (goods_list caps at MAX_LINES and "
                   "ranks by species weight): %s"
                   % (len(undrawn), ", ".join(undrawn)))
    if bad:
        return False, "; ".join(bad)
    return True, ("%d ≥ %d named goods, every one stocked somewhere"
                  % (len(EC.GOODS), want))


def _claim_spoo(text, EC):
    """`spoo sits on a Narn row at 1-2 cr`, priced by the model that sells it."""
    m = _SPOO.search(_flat(text))
    if not m:
        return False, "the row makes no spoo price claim"
    origin, lo, hi = m.group(1).lower(), float(m.group(2)), float(m.group(3))
    g = EC.GOODS_BY_NAME.get("spoo")
    if g is None:
        return False, "economy.GOODS has no `spoo`"
    if g.origin.lower() != origin:
        return False, ("the row puts spoo on a %s row and its origin is %r"
                       % (origin.title(), g.origin))
    quoted = [(k, EC.price("spoo", k)) for k in EC.counters()
              if "spoo" in EC.goods_list(k)]
    if not quoted:
        return False, "no counter in the register carries spoo at all"
    out = [(k, p) for k, p in quoted if not (lo <= p <= hi)]
    if out:
        return False, ("the row prices spoo at %g–%g cr and %d of %d counters "
                       "quote outside it: %s (economy's venue multipliers move "
                       "it: %s)"
                       % (lo, hi, len(out), len(quoted),
                          ", ".join("%s %.2f" % x for x in out[:4]),
                          ", ".join("%s ×%.4g" % (s, v) for s, v
                                    in sorted(EC.VENUE_MULT.items()))))
    return True, ("spoo %s, %d counters all inside %g–%g cr"
                  % (g.origin, len(quoted), lo, hi))


def _claim_gqe(text, EC):
    """G'Quan Eth carries a customs class, and the class means something."""
    g = EC.GOODS_BY_NAME.get("G'Quan Eth")
    if g is None:
        return False, "economy.GOODS has no `G'Quan Eth`"
    bad = []
    if g.cargo != "bonded":
        bad.append("the annex calls it controlled/customs class and its cargo "
                   "class is %r" % g.cargo)
    # the row names INC-GQE as its incident class; it must be a real one.
    if "INC-GQE" in _flat(text):
        import sys                                                # noqa: PLC0415
        sys.path.insert(0, os.path.join(ROOT, "station"))
        import incident as IN                                     # noqa: PLC0415
        ids = {c[0] if isinstance(c, (tuple, list)) else getattr(c, "cid", "")
               for c in getattr(IN, "CLASSES", ())}
        if "INC-GQE" not in ids:
            bad.append("the row cites INC-GQE and incident.py has no such "
                       "class (%d classes)" % len(ids))
    if bad:
        return False, "; ".join(bad)
    return True, "G'Quan Eth is %s cargo, INC-GQE exists" % g.cargo


def _claim_named(EC):
    """No counter sells a token: every counter's stock is named, both kinds."""
    bad, empty = [], []
    for k in EC.counters():
        gl = EC.goods_list(k)
        for n in gl:
            if n not in EC.GOODS_BY_NAME:
                bad.append("%s stocks %r, which is in no GOODS row" % (k, n))
        if not gl:
            svc = EC.services_at(k) if hasattr(EC, "services_at") else ()
            if not svc:
                bad.append("%s is a counter and sells neither a named good nor "
                           "a named service" % k)
            else:
                empty.append(k)
    if bad:
        return False, "; ".join(bad[:3])
    return True, ("%d counters, every line named; %d sell services only (%s)"
                  % (len(EC.counters()), len(empty), ", ".join(empty[:3])))


def _claim_menu(EC):
    """The Fresh Air clause, and the half of it this tier can settle."""
    key = "fresh_air"
    try:
        gl = EC.goods_list(key)
    except KeyError:
        return False, "the register has no `fresh_air`"
    from_drum = [n for n in gl
                 if EC.GOODS_BY_NAME[n].supply in ("drum", "hydroponics")]
    if not from_drum:
        return False, ("Fresh Air's %d stock lines include nothing supplied by "
                       "the drum or hydroponics, so no dish of its could name "
                       "a PLC-110 field or PLC-026 rack" % len(gl))
    return True, ("Fresh Air stocks %d drum/hydroponics line(s) (%s) -- but "
                  "there is NO menu function in economy.py or hospitality.py, "
                  "so \"names tonight's dish\" is unsettleable"
                  % (len(from_drum), ", ".join(from_drum[:3])))


# ---------------------------------------------------------------------------
def check(row):
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    import economy as EC                                          # noqa: PLC0415
    text = _row_text(row)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    if "GDS-01" not in text.splitlines()[0]:
        return False, ("the registry points at %r, whose heading is %r"
                       % (row.get("at"), text.splitlines()[0][:60]))
    results = [("fields",) + _claim_fields(text, EC),
               ("seed",) + _claim_seed(text, EC),
               ("floor",) + _claim_floor(text, EC),
               ("spoo",) + _claim_spoo(text, EC),
               ("G'Quan Eth",) + _claim_gqe(text, EC),
               ("named",) + _claim_named(EC),
               ("menu",) + _claim_menu(EC)]
    bad = [(n, t) for n, ok, t in results if not ok]
    good = [(n, t) for n, ok, t in results if ok]
    if bad:
        return False, "; ".join("%s: %s" % (n, t) for n, t in bad)
    return True, "; ".join("%s: %s" % (n, t) for n, t in good)


# ---------------------------------------------------------------------------
def _selftest(out=print):
    import sys                                                    # noqa: PLC0415
    sys.path.insert(0, os.path.join(ROOT, "station"))
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import economy as EC                                          # noqa: PLC0415
    row = {"id": "GDS-001", "at": "docs/spec/PLACES.md:164"}
    text = _row_text(row)

    # THE PARSE, PRINTED. `plc.py`'s rule: a poor parse rate is not a finding.
    items = _seed_items(text)
    names = [g.name for g in EC.GOODS]
    hit = [(p, _match(p, names) or next((_match(a, names) for a in alts
                                         if _match(a, names)), None))
           for p, alts in items]
    out("seed sentence -> %d items, %d resolved" %
        (len(items), sum(1 for _p, g in hit if g)))
    for p, g in hit:
        out("   %-34s -> %s" % (p[:34], g or "** NO GOODS ROW **"))
    out("")

    ok, note = check(row)
    out("GDS-001 %s" % ("PASS" if ok else "FAIL"))
    for part in note.split("; "):
        out("   " + part)

    out("")
    out("-- negative controls --")
    keep_goods = EC.GOODS

    # 1. remove a seed ware from the table: the seed claim must name it.
    EC.GOODS = tuple(g for g in keep_goods if g.name != "spoo")
    EC.GOODS_BY_NAME = {g.name: g for g in EC.GOODS}
    out("spoo deleted from GOODS   -> %s" % (_claim_seed(text, EC)[1])[:120])
    EC.GOODS = keep_goods
    EC.GOODS_BY_NAME = {g.name: g for g in EC.GOODS}

    # 2. the floor is a real comparison, not a constant: raise the table above
    #    it by duplicating rows and watch the floor claim flip.
    import dataclasses                                            # noqa: PLC0415
    pad = tuple(dataclasses.replace(keep_goods[0], name="pad-%d" % i)
                for i in range(60 - len(keep_goods)))
    EC.GOODS = keep_goods + pad
    EC.GOODS_BY_NAME = {g.name: g for g in EC.GOODS}
    # The floor is TWO sub-claims (a count and a placement) and this control
    # isolates the count: padding cannot place anything, so the placement half
    # must still fail while the "N short" half disappears entirely.
    _ok2, n2 = _claim_floor(text, EC)
    out("padded to %d goods        -> count clause %s  (%s)"
        % (len(EC.GOODS), "GONE" if "short" not in n2 else "STILL THERE",
           n2[:96]))
    EC.GOODS = keep_goods
    EC.GOODS_BY_NAME = {g.name: g for g in EC.GOODS}

    # 3. the spoo claim reads a live price, so moving the venue multiplier
    #    must move the verdict.
    keep_v = dict(EC.VENUE_MULT)
    EC.VENUE_MULT.update({k: 1.0 for k in EC.VENUE_MULT})
    ok3, n3 = _claim_spoo(text, EC)
    out("venue multipliers flattened -> %s %s" % ("PASS" if ok3 else "FAIL",
                                                  n3[:130]))
    EC.VENUE_MULT.clear()
    EC.VENUE_MULT.update(keep_v)

    # 4. and the supply enumeration: declare the extra one and it stops being
    #    extra, which proves the claim reads the ROW and not a constant here.
    t2 = text.replace("{drum | hydroponics | import | route}",
                      "{drum | hydroponics | import | route | station}")
    out("row widened to allow `station` -> %s %s"
        % ("PASS" if _claim_fields(t2, EC)[0] else "FAIL",
           _claim_fields(t2, EC)[1][:110]))
    return 0 if ok else 1


if __name__ == "__main__":                                        # pragma: no cover
    import sys
    sys.path.insert(0, os.path.join(ROOT, "station"))
    _selftest()
