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

    # THE FLOOR, AND IT IS COUNTED ON RENDERED STRINGS RATHER THAN TEMPLATES.
    # `cast_lines(row)` returns the lines belonging to ONE person with that
    # person's own facts already in them; the runtime braces that survive
    # (`{ship}`, `{souls}`) are filled at speak() time, so this count still
    # UNDERSTATES what a player hears, which is the safe direction for a floor.
    roster = dlg.cast_roster()
    if len(roster) != cast:
        bad.append("dialogue.cast_roster() parses %d rows, spec says %d"
                   % (len(roster), cast))
    sets, short = {}, []
    for r in roster:
        ls = dlg.cast_lines(r)
        sets[r["who"]] = set(ls)
        if len(set(ls)) < per:
            short.append((r["who"], len(set(ls))))
    if short:
        bad.append("%d of %d cast are under %d distinct lines, e.g. %s"
                   % (len(short), len(roster), per, short[:3]))
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
    got = len(seen)
    if got < total:
        bad.append("%d distinct Tier-1 lines against a floor of %d"
                   % (got, total))
    if bad:
        return False, "DLG-01: " + "; ".join(bad)
    return True, ("DLG-01: %d distinct Tier-1 lines (%d each x %d cast parsed "
                  "from the annex), and no string appears in two NPCs' sets"
                  % (got, per, len(roster)))


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
    thin = [(c, len(set(v))) for c, v in pools.items()
            if len(set(v)) < want_cell]
    if thin:
        bad.append("%d of %d cells are under %d lines, e.g. %s"
                   % (len(thin), len(cells), want_cell, thin[:3]))
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
    return True, ("DLG-02: %d occupied cells x %d lines = %d distinct tier-2 "
                  "lines, no two cells sharing one, and %d draws before any "
                  "cell repeats" % (len(cells), want_cell, len(set(flat)),
                                    worst))


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
