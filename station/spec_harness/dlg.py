"""DLG rows: the dialogue volume floors, and what actually exists to meet them.

EVERY DLG ROW IS AN ARITHMETIC WITH ITS WORKING SHOWN -- *"11 topics x 3
salience variants = 33 · greetings 4 dayparts x 2 warmth bands = 8 ... 75
distinct lines each; x 50 cast = 3,750"*. That shape makes two different things
checkable, and this harness does both because they fail for opposite reasons:

  1. **The INPUTS.** Every multiplicand is a number in code -- 11 topics is
     `dialogue.TOPICS`, 50 cast is the CAST-02 table, 29 counters is
     `dialogue.serve_places()`, 10 ship classes is `traffic.MANIFEST`, 8
     ERA_EVENTS is `costume.ERA_EVENTS`, 79 species x role cells is a roll over
     `schedule.ROLE_WEIGHTS`. When one of those moves the floor moves with it
     and the spec's total goes stale. That is DRIFT and it is the valuable
     output.
  2. **The FLOOR.** How many distinct lines exist against the number demanded.

`SUFFICIENT = False`, and the annex says why in its own words: *"Per the
anti-rig rule these counts are FLOORS on top of the named-content checks --
hitting a number completes nothing; every DLG item also names content."* Each
row's ACCEPT-shape is a played session (*"one evening at Milo's counter
exhausts no pool"*, *"ten minutes at one counter never hears the same line
twice"*). Counting template pools is not that, so a pass here is a pass on the
arithmetic and the pool size, never on the row.

WHAT IS COUNTED, PRECISELY, so nobody has to guess what the number means. The
module's line pools are TEMPLATES with braces in them -- `"{min:.0f} minutes a
lap. Do you walk it alone?"` -- and one template rendered against two people's
facts is two lines a player hears. Counting templates therefore UNDERSTATES
what the player experiences and OVERSTATES nothing, which is the safe direction
for a floor. The baked sidecars in `station/generated/scene/deck/` hold the
rendered strings and are deliberately NOT read: they are a built artefact this
harness cannot rebuild in the smoke tier, and this project has already been
caught measuring a committed artefact that no longer described the code.
"""
import os
import re

SUFFICIENT = False

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HEAD = re.compile(r"^#+\s*DLG-(\d+)\s*[-—–]+\s*(.+?)\s*$")


def _n(s):
    return int(str(s).replace(",", "").replace("**", "").strip())


def _flat(text):
    """The row on one line.

    EVERY ARITHMETIC REGEX READS THIS, and the reason is a bug this file had
    for one run: the annex hard-wraps at 90 columns, so `**79** (human\n17,
    Drazi 6, ...` never matched a pattern written against the sentence, and two
    of DLG-02's three checks silently did nothing while the row still reported
    a failure for another reason. A check that cannot match is a check that
    cannot fail, and it hides inside a row that is red anyway.
    """
    return re.sub(r"\s+", " ", text)


def _pool(obj):
    """Distinct template strings in one of dialogue.py's line tables."""
    if isinstance(obj, dict):
        obj = [x for v in obj.values()
               for x in (v if isinstance(v, (list, tuple)) else [v])]
    return {x for x in obj if isinstance(x, str) and x}


def _cast_rows():
    """The CAST-02 roster length, read from the annex rather than assumed 50."""
    body = open(os.path.join(_ROOT, "docs/spec/PEOPLE.md"),
                encoding="utf-8").read()
    return len([l for l in body.splitlines() if re.match(r"^\|\s*\d+\s*\|", l)])


def _mask(dlg, row, line):
    """One Tier-1 line with everything that is THIS PERSON'S removed.

    What survives is the sentence frame -- the part somebody wrote. Every
    string the roster row carries and every string `_cast_facts` derives from
    it is replaced by a sentinel, longest first so that a substring can never
    eat the token that contains it, and whitespace tokens as well as whole
    values so that "Ruth" is masked out of a line that only used the forename.
    Runs of sentinels collapse, because "@ and @" against "@" is a difference
    in how many of the person's own names the sentence happened to use, not a
    difference in what was written.

    Tokens shorter than three characters are left alone deliberately: masking
    "a" or "of" would erase the sentence rather than the person, and this must
    stay a measurement of writing.
    """
    vals = [v for v in row.values() if isinstance(v, str)]
    try:
        vals += [v for v in dlg._cast_facts(row).values() if isinstance(v, str)]
    except Exception:                                        # pragma: no cover
        pass
    toks = set()
    for v in vals:
        v = v.strip()
        if len(v) > 2:
            toks.add(v)
        toks.update(t for t in v.split() if len(t) > 2)
    for t in sorted(toks, key=len, reverse=True):
        line = line.replace(t, "@")
    return re.sub(r"(?:@[\s,.'-]*)+", "@", line)


def _minted_names():
    """Names the population actually casts, so Tier-1 reach can be asked.

    `resident.roster` is the same function every room build uses to decide who
    is standing in it, so a name it never returns is a name no player can be
    in front of. Three places, four hours and three species is a sample rather
    than the station -- the smoke tier may not build anything -- and a sample
    is enough to answer "does ANY of this reach a player", which is the
    question the ninth no-caller defect in CLAUDE.md is about.
    """
    try:
        from npc import resident as res                       # noqa: PLC0415
    except Exception:                                        # pragma: no cover
        return ()
    out = set()
    for pk in ("zocalo", "docking_bays", "medlab"):
        for h in (2, 9, 13, 20):
            for sp in ("human", "narn", "centauri"):
                try:
                    out.update(r.name for r in res.roster(pk, h, sp, 20)
                               if r.name)
                except Exception:                            # pragma: no cover
                    pass
    return tuple(sorted(out))


def _drift(claim, got, what):
    return None if claim == got else "spec says %s %s, code has %s" % (
        claim, what, got)


# ---------------------------------------------------------------------------
def _dlg01(text):
    import dialogue as dlg                                       # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"(\d+) topics × (\d+) salience variants = (\d+)", text)
    if not m:
        return False, "DLG-01: cannot read the per-NPC arithmetic"
    topics, variants, sub = (int(m.group(i)) for i in (1, 2, 3))
    d = _drift(topics, len(dlg.TOPICS), "topics")
    if d:
        bad.append(d)
    if topics * variants != sub:
        bad.append("%d x %d is not %d" % (topics, variants, sub))
    m2 = re.search(r"\*\*(\d+) distinct lines each; × (\d+) cast = ([\d,]+)\*\*",
                   text)
    if not m2:
        return False, "DLG-01: cannot read the per-NPC total"
    per, cast, total = _n(m2.group(1)), _n(m2.group(2)), _n(m2.group(3))
    if per * cast != total:
        bad.append("%d x %d is not %d" % (per, cast, total))
    d = _drift(cast, _cast_rows(), "Tier-1 rows")
    if d:
        bad.append(d)

    # THE FLOOR, AND IT IS COUNTED ON MASKED LINES RATHER THAN RENDERED ONES.
    #
    # THIS IS THE CHECK THE ROW HAD TO HAVE AND DID NOT, and the reason is
    # worth keeping because the old version PASSED on content that violated the
    # rule it was written to enforce. `cast_lines(row)` returns one person's
    # lines with that person's own facts already substituted in, and the old
    # count hashed those. Two people therefore compared UNEQUAL whenever they
    # had different names -- which is always -- so 50 renderings of one
    # sentence counted as 50 distinct lines, and the row's own rule ("no string
    # may appear in two NPCs' sets") could not fail by construction. A reviewer
    # passed it with "<name> says thing number 0."
    #
    # `_mask` removes every proper noun the roster row carries, and every value
    # `dialogue._cast_facts` derives from it, so what is hashed is the SENTENCE
    # FRAME -- what was actually written -- rather than what name substitution
    # made unequal. It is the strictly harder reading and it is the honest one:
    # if the frame is the same, Ruth Delgado and Ade Bankole are saying the same
    # sentence, and a player standing in front of both hears that.
    #
    # AND IT IS NOT A LOOSENING ANYWHERE: the rendered-string checks below are
    # kept as well. A masked collision is a finding; a rendered collision is
    # still a finding.
    roster = dlg.cast_roster()
    if len(roster) != cast:
        bad.append("dialogue.cast_roster() parses %d rows, spec says %d"
                   % (len(roster), cast))
    sets, msets, short, mshort = {}, {}, [], []
    for r in roster:
        ls = dlg.cast_lines(r)
        sets[r["who"]] = set(ls)
        msets[r["who"]] = {_mask(dlg, r, l) for l in ls}
        if len(set(ls)) < per:
            short.append((r["who"], len(set(ls))))
        if len(msets[r["who"]]) < per:
            mshort.append((r["who"], len(msets[r["who"]])))
    if short:
        bad.append("%d of %d cast are under %d distinct lines, e.g. %s"
                   % (len(short), len(roster), per, short[:3]))
    if mshort:
        bad.append("%d of %d cast are under %d distinct SENTENCE FRAMES once "
                   "their own proper nouns are masked out, e.g. %s"
                   % (len(mshort), len(roster), per, mshort[:3]))
    # THE RULE THE ROW IS ACTUALLY ABOUT: no string in two NPCs' sets.
    seen, shared = {}, []
    for who, ls in sets.items():
        for t in ls:
            if t in seen:
                shared.append((seen[t], who, t[:40]))
            else:
                seen[t] = who
    if shared:
        bad.append("%d strings appear in two NPCs' sets, e.g. %s"
                   % (len(shared), shared[:2]))
    mseen, mshared = {}, []
    for who, ls in msets.items():
        for t in ls:
            if t in mseen:
                mshared.append((mseen[t], who, t[:52]))
            else:
                mseen[t] = who
    if mshared:
        bad.append("%d masked frames are spoken word for word by two of the "
                   "fifty, e.g. %s" % (len(mshared), mshared[:2]))
    got, mgot = len(seen), len(mseen)
    if mgot < total:
        bad.append("%d distinct sentence frames against a floor of %d "
                   "(%d rendered strings, but they differ only by the "
                   "speaker's own proper nouns)" % (mgot, total, got))

    # AND THE FIFTY MUST BE PEOPLE THE SIMULATION CAN PRODUCE. A pool of lines
    # for names nobody is ever cast under is content no player can reach --
    # the ninth instance of this project's standing defect, at content scale.
    # `phrase()` reaches Tier-1 through `cast_by_name(sp.name)`, so the test is
    # that names the population actually mints resolve there.
    minted = _minted_names()
    hit = sum(1 for nm in minted if dlg.cast_by_name(nm) is not None)
    reached = len({r["who"] for r in roster if r["who"] in set(minted)})
    if not minted:
        bad.append("could not mint a single resident name to test Tier-1 "
                   "reachability against")
    elif not hit:
        bad.append("none of the %d names populace/names.py actually mints "
                   "resolves through dialogue.cast_by_name(), so no Tier-1 "
                   "line is reachable by any resident the station casts"
                   % len(minted))
    if bad and minted:
        # NOT A GATE, A NUMBER THE OWNER NEEDS BESIDE THE OTHERS. The hard
        # check above is the critic's ("some minted name reaches a row"); this
        # says how much of the cast the population actually casts, and it is
        # CAST-02's own defect rather than this row's, so it is reported here
        # and enforced there.
        bad.append("and %d of the %d Tier-1 cast are ever minted by "
                   "resident.roster over the sample -- the rest have lines "
                   "and no body (CAST-02's finding, reported here because "
                   "this is the row that writes for them)"
                   % (reached, len(roster)))
    if bad:
        return False, "DLG-01: " + "; ".join(bad)
    return True, ("DLG-01: %d distinct sentence frames over %d rendered "
                  "Tier-1 lines (%d each x %d cast parsed from the annex), no "
                  "frame shared by two of the fifty, and %d of %d minted "
                  "resident names reach a Tier-1 row"
                  % (mgot, got, per, len(roster), hit, len(minted)))


def _dlg02(text):
    import dialogue as dlg                                       # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"computed this session from ROLE_WEIGHTS: \*\*(\d+)\*\*", text)
    if not m:
        return False, "DLG-02: cannot read the occupied-cell count"
    claim = int(m.group(1))
    cells = {sp: sum(1 for _r, n in w.items() if n)
             for sp, w in sched.ROLE_WEIGHTS.items()}
    got = sum(cells.values())
    d = _drift(claim, got, "occupied (species x role) cells")
    if d:
        bad.append(d)
    # THE BREAKDOWN IS QUOTED TOO and it is the half that would rot silently:
    # the total can stay 79 while the shape behind it changes.
    mb = re.search(r"human (\d+), Drazi (\d+), five-cell species ×(\d+), "
                   r"four-cell ×(\d+), vorlon (\d+)", text)
    if not mb:
        return False, "DLG-02: cannot read the per-species cell breakdown"
    if mb:
        want = dict(human=int(mb.group(1)), drazi=int(mb.group(2)),
                    vorlon=int(mb.group(5)))
        for sp, n in want.items():
            if cells.get(sp) != n:
                bad.append("%s has %s cells, spec says %d"
                           % (sp, cells.get(sp), n))
        five = sum(1 for v in cells.values() if v == 5)
        four = sum(1 for v in cells.values() if v == 4)
        if five != int(mb.group(3)):
            bad.append("%d species have five cells, spec says %s"
                       % (five, mb.group(3)))
        if four != int(mb.group(4)):
            bad.append("%d species have four cells, spec says %s"
                       % (four, mb.group(4)))
    mt = re.search(r"11 topics × 2 variants \+ 8 greet/farewell = \*\*(\d+) → "
                   r"([\d,]+) lines\*\*", text)
    if not mt:
        return False, "DLG-02: cannot read the per-cell arithmetic"
    if _n(mt.group(1)) * got != _n(mt.group(2)):
        bad.append("%s x %d cells is not %s" % (mt.group(1), got, mt.group(2)))

    # THE FLOOR: what a cell can actually say, measured over ALL of them.
    want_cell = _n(mt.group(1))
    cells = dlg.occupied_cells()
    if len(cells) != got:
        bad.append("dialogue.occupied_cells() gives %d, ROLE_WEIGHTS gives %d"
                   % (len(cells), got))
    pools = {c: dlg.cell_lines(*c) for c in cells}
    # AND IT IS COUNTED WITH THE SPECIES REGISTER FRAME STRIPPED BACK OFF.
    #
    # THE FIRST BUILD OF THIS MATRIX PASSED 30 WITHOUT WRITING 30. Each cell
    # held 11 role clauses put through the species' 2 `SPECIES_FRAME` affixes
    # and the pair was counted as two lines, so nineteen real utterances --
    # 11 topics + 4 greetings + 4 farewells -- reported as thirty. The affix is
    # the same two strings on all eleven topics; it is register modulation,
    # which the annex asks for under its own heading, and a modulation applied
    # to one sentence is not two sentences.
    #
    # `dialogue.cell_utterances` inverts the frame exactly (every frame is
    # prefix + "{say}" + suffix, so the strip is a prefix/suffix match), which
    # means adding a THIRD frame buys a cell nothing here. That is the property
    # that makes this a floor rather than a knob, and it is why the check is
    # the inverse rather than a division by `len(SPECIES_FRAME[species])`:
    # division would still reward padding the frame table as long as the pool
    # grew with it.
    utt = {c: set(dlg.cell_utterances(*c)) for c in cells}
    thin = [(c, len(v)) for c, v in utt.items() if len(v) < want_cell]
    if thin:
        bad.append("%d of %d cells are under %d DISTINCT UTTERANCES once the "
                   "species register frame is stripped off (rendered pools are "
                   "%s), e.g. %s"
                   % (len(thin), len(cells), want_cell,
                      "/".join(str(x) for x in sorted(
                          {len(set(v)) for v in pools.values()})), thin[:3]))
    # AND THE CELLS MUST BE DIFFERENT CELLS. A matrix of 79 identical pools
    # passes every count above; identity is the only check that can see it.
    flat = [t for v in pools.values() for t in v]
    if len(set(flat)) != len(flat):
        bad.append("%d of %d tier-2 lines are shared between cells"
                   % (len(flat) - len(set(flat)), len(flat)))
    # The annex's normative anti-repeat floor, walked rather than assumed.
    mr = re.search(r"lines-before-first-repeat ≥(\d+)", text)
    floor_rep = int(mr.group(1)) if mr else 20
    worst = min((dlg.lines_before_repeat(sp, r, "harness") for sp, r in cells),
                default=0)
    if worst < floor_rep:
        bad.append("a cell repeats itself after %d draws, floor is %d"
                   % (worst, floor_rep))
    if bad:
        return False, "DLG-02: " + "; ".join(bad)
    return True, ("DLG-02: %d occupied cells x %d distinct utterances "
                  "(measured with the species register frame stripped off, so "
                  "the affix buys nothing) = %d rendered tier-2 lines, no two "
                  "cells sharing one, and %d draws before any cell repeats"
                  % (len(cells), want_cell, len(set(flat)), worst))


def _dlg03(text):
    import dialogue as dlg                                       # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"(\d+) counters across (\d+) places", text)
    if not m:
        return False, "DLG-03: cannot read the counter arithmetic"
    c_claim, p_claim = int(m.group(1)), int(m.group(2))
    places = dlg.serve_places()
    counters = sum(len(dlg.serve_tokens(k)) for k in places)
    if c_claim != counters:
        bad.append("spec says %d counters, dialogue.serve_tokens totals %d"
                   % (c_claim, counters))
    if p_claim != len(places):
        bad.append("spec says %d places, dialogue.serve_places() returns %d"
                   % (p_claim, len(places)))
    mt = re.search(r"≥(\d+) place-specific trade lines beyond their matrix "
                   r"cell[^=]*= \*\*(\d+)\*\*", text)
    if not mt:
        return False, "DLG-03: cannot read the per-counter line arithmetic"
    if mt:
        each, tot = int(mt.group(1)), int(mt.group(2))
        if each * c_claim != tot:
            bad.append("%d x %d is not %d" % (each, c_claim, tot))
        if bad:
            bad.append("on the live counter count the floor is %d, not %d"
                       % (each * counters, tot))
    # THE FLOOR: six place-specific trade lines per counter, naming wares.
    tl = dlg.trade_lines()
    thin = [(k, len(set(v))) for k, v in tl.items() if len(set(v)) < each]
    if thin:
        bad.append("%d counters are under %d place-specific trade lines, "
                   "e.g. %s" % (len(thin), each, thin[:3]))
    flat = [x for v in tl.values() for x in v]
    if len(set(flat)) != len(flat):
        bad.append("%d of %d trade lines are shared between counters"
                   % (len(flat) - len(set(flat)), len(flat)))
    # THE ROW'S OWN SPECIFICITY RULE, WHICH IS NOT A COUNT.
    vague = [k for k, v in tl.items()
             if any(re.search(r"\bgoods\b|\bwares\b|\bitems\b", x)
                    for x in v)]
    if vague:
        bad.append("%d counters trade in unnamed goods: %s"
                   % (len(vague), vague[:3]))
    if bad:
        return False, "DLG-03: " + "; ".join(bad)
    return True, ("DLG-03: %d counters across %d places, %d distinct "
                  "place-specific trade lines, every one naming its wares"
                  % (counters, len(places), len(set(flat))))


def _dlg04(text):
    import broadcast as br                                       # noqa: PLC0415
    import traffic                                               # noqa: PLC0415
    from npc import costume                                      # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"ISN (\d+) bulletins × (\d+) rotation variants = (\d+)", text)
    if m:
        if len(br.ISN_BULLETINS) != int(m.group(1)):
            bad.append("spec says %s ISN bulletins, broadcast has %d"
                       % (m.group(1), len(br.ISN_BULLETINS)))
        if int(m.group(1)) * int(m.group(2)) != int(m.group(3)):
            bad.append("ISN arithmetic does not hold")
    m = re.search(r"MiniPax (\d+) × (\d+) = (\d+)", text)
    if m and len(br.MINIPAX_NOTICES) != int(m.group(1)):
        bad.append("spec says %s MiniPax notices, broadcast has %d"
                   % (m.group(1), len(br.MINIPAX_NOTICES)))
    m = re.search(r"\*\*(\d+) ship classes\*\*", text)
    if m:
        if len(traffic.MANIFEST) != int(m.group(1)):
            bad.append("spec says %s ship classes, traffic.MANIFEST has %d"
                       % (m.group(1), len(traffic.MANIFEST)))
        if len(br.SHIP_CALL) != len(traffic.MANIFEST):
            bad.append("broadcast.SHIP_CALL covers %d of the manifest's %d "
                       "classes" % (len(br.SHIP_CALL), len(traffic.MANIFEST)))
    m = re.search(r"(\d+) ERA_EVENTS × (\d+) speaker classes = (\d+)", text)
    if not m:
        return False, "DLG-04: cannot read the era-rumour arithmetic"
    if len(costume.ERA_EVENTS) != int(m.group(1)):
        bad.append("spec says %s ERA_EVENTS, costume has %d"
                   % (m.group(1), len(costume.ERA_EVENTS)))
    m = re.search(r"\*\*(\d+)\*\*, all era-locked", text)
    if not m:
        return False, "DLG-04: cannot read the ambient/era floor"
    floor = int(m.group(1))

    # THE FLOOR, read off broadcast.py's own census so the count and the
    # content cannot drift apart.
    cens = br.templates()
    flat = [t for v in cens.values() for t in v]
    if len(set(flat)) != len(flat):
        bad.append("%d broadcast templates are duplicated"
                   % (len(flat) - len(set(flat))))
    if len(set(flat)) < floor:
        bad.append("broadcast.py ships %d distinct templates against a floor "
                   "of %d (%s)"
                   % (len(set(flat)), floor,
                      ", ".join("%s %d" % (k, len(v))
                                for k, v in cens.items())))
    if not cens.get("denunciation"):
        bad.append("there is no denunciation set")
    if len(cens.get("pa_ship", ())) != len(traffic.MANIFEST) * 3:
        bad.append("PA covers %d of the %d ship-class x call-type templates"
                   % (len(cens.get("pa_ship", ())), len(traffic.MANIFEST) * 3))
    want_rumour = len(costume.ERA_EVENTS) * len(br.RUMOUR_SPEAKERS)
    if len(cens.get("rumour", ())) != want_rumour:
        bad.append("the era-rumour matrix has %d rows, %d events x %d speaker "
                   "classes is %d" % (len(cens.get("rumour", ())),
                                      len(costume.ERA_EVENTS),
                                      len(br.RUMOUR_SPEAKERS), want_rumour))
    if bad:
        return False, "DLG-04: " + "; ".join(bad)
    return True, ("DLG-04: %d distinct broadcast templates, all era-locked "
                  "through costume.ERA_EVENTS (%s)"
                  % (len(set(flat)),
                     ", ".join("%s %d" % (k, len(v)) for k, v in cens.items())))


def _dlg05(text):
    import dialogue as dlg                                       # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"(\d+) topics × (\d+) choice stances \(([^)]*)\) = (\d+)", text)
    if not m:
        return False, "DLG-05: cannot read the player-line arithmetic"
    topics, stances, sub = int(m.group(1)), int(m.group(2)), int(m.group(4))
    if topics * stances != sub:
        bad.append("%d x %d is not %d" % (topics, stances, sub))
    if len(dlg.TOPICS) != topics:
        bad.append("spec says %d topics, dialogue.TOPICS has %d"
                   % (topics, len(dlg.TOPICS)))
    if len(dlg.STANCES) != stances:
        bad.append("spec says %d stances, dialogue.STANCES has %d"
                   % (stances, len(dlg.STANCES)))
    m2 = re.search(r"\*\*(\d+) distinct player lines\*\*", text)
    if not m2:
        return False, "DLG-05: cannot read the player-line floor"
    floor = int(m2.group(1))

    # THE FLOOR, over the four families the row's arithmetic names.
    pl = dlg.player_lines()
    flat = [t for v in pl.values() for t in v]
    if len(set(flat)) != len(flat):
        bad.append("%d player lines are duplicated"
                   % (len(flat) - len(set(flat))))
    missing = [k for k, _f in dlg.TOPICS if k not in dlg.SAY]
    if missing:
        bad.append("dialogue.SAY has no row for %s" % ", ".join(missing))
    if len(set(flat)) < floor:
        bad.append("dialogue ships %d distinct player lines against a floor "
                   "of %d (%s)" % (len(set(flat)), floor,
                                   ", ".join("%s %d" % (k, len(v))
                                             for k, v in pl.items())))
    # The 96 are two lists multiplied, and the lists are the project's own.
    mw = re.search(r"role work-lines (\d+) roles × (\d+) shift verbs = (\d+)",
                   text)
    if mw:
        nr, nv, nt = (int(mw.group(i)) for i in (1, 2, 3))
        if len(dlg.PLAYER_ROLES) != nr:
            bad.append("spec says %d player roles, dialogue has %d"
                       % (nr, len(dlg.PLAYER_ROLES)))
        if len(dlg.SHIFT_VERBS) != nv:
            bad.append("spec says %d shift verbs, dialogue has %d"
                       % (nv, len(dlg.SHIFT_VERBS)))
        holes = [(r, v) for r in dlg.PLAYER_ROLES for v in dlg.SHIFT_VERBS
                 if (r, v) not in dlg.WORK_LINE]
        if holes:
            bad.append("%d of %d work-grid cells are empty, e.g. %s"
                       % (len(holes), nt, holes[:3]))
    if bad:
        return False, "DLG-05: " + "; ".join(bad)
    return True, ("DLG-05: %d distinct player lines over %d topics x %d "
                  "stances, %d roles x %d verbs, and the openers, papers and "
                  "refusals" % (len(set(flat)), len(dlg.TOPICS),
                                len(dlg.STANCES), len(dlg.PLAYER_ROLES),
                                len(dlg.SHIFT_VERBS)))


def _dlg06(text):
    import dialogue as dlg                                       # noqa: PLC0415
    from npc import resident as res                              # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415

    text, bad = _flat(text), []
    m = re.search(r"Kosh: \*\*≤(\d+) lines", text)
    mb = re.search(r"The Broker: audience-gated, ≤(\d+)", text)
    if not m or not mb:
        return False, "DLG-06: cannot read the two scarce-voice ceilings"
    kosh, broker = int(m.group(1)), int(mb.group(1))

    # The ceiling half: is there a Kosh pool at all, and is it capped?
    pool = getattr(dlg, "KOSH_LINES", None)
    if pool is None:
        bad.append("no Kosh line pool exists, so the ≤%d ceiling and "
                   "\"never twice in one session\" are unenforced -- vorlon "
                   "has a voice row and draws the same shared templates as "
                   "everybody else" % kosh)
    elif len(_pool(pool)) > kosh:
        bad.append("Kosh pool is %d, over the ≤%d ceiling"
                   % (len(_pool(pool)), kosh))
    elif pool is not None:
        # A CEILING IS NOT A COUNT, IT IS A BEHAVIOUR. "Never twice in one
        # session" is checked by walking a session past the end of the pool
        # and asserting the answer becomes silence rather than a repeat.
        k = dlg._Speaker("kosh", "vorlon", "envoy", "council_chamber", "", "",
                         "", "", "", "", False, "")
        said = [dlg.scarce_line(k, dlg.World(session="spec", turn=t))[0]
                for t in range(kosh + 2)]
        spoke = [x for x in said if x]
        if len(set(spoke)) != len(spoke):
            bad.append("a Kosh session repeats itself inside %d lines" % kosh)
        if any(said[kosh:]):
            bad.append("the Kosh pool does not fall silent when exhausted")
    bl = getattr(dlg, "BROKER_LINES", None)
    if bl is None:
        bad.append("no Broker pool exists (≤%d, audience-gated)" % broker)
    else:
        if len({t for _g, t in bl}) > broker:
            bad.append("Broker pool is %d, over the ≤%d ceiling"
                       % (len({t for _g, t in bl}), broker))
        alone, room = set(dlg.broker_lines(True)), set(dlg.broker_lines(False))
        if not alone or not room or (alone & room):
            bad.append("the Broker is not audience-gated: %d alone, %d with a "
                       "room, %d shared" % (len(alone), len(room),
                                            len(alone & room)))

    # The half that IS built and passes: an office-designate species has no
    # personal name to render, enforced by a raise rather than by a convention.
    for sp in sched.SPECIES_WITHOUT_NAMES:
        card = dict((k, v) for k, v, _s in res.identicard(res.resident("3", sp)))
        if card["NAME"]:
            bad.append("%s renders a personal NAME %r" % (sp, card["NAME"]))
    if not bad:
        return True, ("DLG-06: Kosh %d lines (≤%d, distinct, then silence), "
                      "Broker %d (≤%d, %d alone / %d with a room), and no "
                      "office-designate species renders a personal name"
                      % (len(_pool(pool)), kosh, len({t for _g, t in bl}),
                         broker, len(dlg.broker_lines(True)),
                         len(dlg.broker_lines(False))))
    return False, ("DLG-06: " + "; ".join(bad) + " [the no-name half holds: "
                   "%d species without a name grammar all render an empty NAME]"
                   % len(sched.SPECIES_WITHOUT_NAMES))


_ROWS = {1: _dlg01, 2: _dlg02, 3: _dlg03, 4: _dlg04, 5: _dlg05, 6: _dlg06}


def check(row):
    from spec_harness import spec_text                           # noqa: PLC0415
    text = spec_text(row.get("at", ""), lines=40)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    mh = _HEAD.match(text.splitlines()[0].strip())
    if not mh:
        return False, "heading is not a DLG row: %r" % text.splitlines()[0][:60]
    n = int(row["id"].split("-")[1])
    if int(mh.group(1)) != n:
        return False, "%s's heading says DLG-%s" % (row["id"], mh.group(1))
    return _ROWS[n](text)
