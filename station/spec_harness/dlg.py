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

    # THE FLOOR. There is no per-NPC line store anywhere: every phrasing in the
    # module is a template SHARED by whoever is speaking, which is also why the
    # row's "no string may appear in two NPCs' sets" cannot hold as written.
    shared = set()
    for name in ("PHRASE", "ERA_PHRASE", "VISA_PHRASE", "DOWN_PHRASE", "GREET",
                 "FAREWELL", "FAREWELL_DUE", "PERSONAL"):
        shared |= _pool(getattr(dlg, name, ()))
    bad.append("the floor is %d lines (%d each x %d cast) and dialogue.py has "
               "%d NPC templates TOTAL, shared by every speaker -- so the "
               "no-two-identical rule is violated by construction, not by a "
               "shortfall" % (total, per, cast, len(shared)))
    return False, "DLG-01: " + "; ".join(bad)


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

    # THE FLOOR: what a cell can actually say.
    per_cell = len(_pool(dlg.PHRASE)) + len(_pool(dlg.GREET)) + \
        len(_pool(dlg.FAREWELL)) + len(_pool(dlg.FAREWELL_DUE))
    want_cell = _n(mt.group(1)) if mt else 30
    bad.append("a cell draws from %d shared templates (%d role registers x %d "
               "species voices modulate them, they do not multiply them); the "
               "floor is %d per cell"
               % (per_cell, len(dlg._ROLE_REGISTER), len(dlg._SPECIES_VOICE),
                  want_cell))
    return False, "DLG-02: " + "; ".join(bad)


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
    # THE FLOOR: `serve_response` returns one person saying one topic line; no
    # place-specific trade pool exists at all.
    bad.append("no per-counter trade vocabulary exists: serve_response() "
               "returns speak(), whose trade line comes from the shared "
               "PHRASE['trade'] pool of %d"
               % len(_pool(dlg.PHRASE.get("trade", ()))))
    return False, "DLG-03: " + "; ".join(bad)


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

    built = (len(br.ISN_BULLETINS) + len(br.MINIPAX_NOTICES)
             + len(br.SHIP_CALL) + len(br.BOARD_VOICE) + 1)
    bad.append("the floor is %d templates; broadcast.py ships %d (%d ISN, %d "
               "MiniPax, %d ship calls at one call type each against the "
               "spec's three, %d board voice, 1 sensor sweep) and there is no "
               "denunciation set"
               % (floor, built, len(br.ISN_BULLETINS), len(br.MINIPAX_NOTICES),
                  len(br.SHIP_CALL), len(br.BOARD_VOICE)))
    return False, "DLG-04: " + "; ".join(bad)


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

    # THE ROW'S PREMISE IS STALE, AND THAT IS THE FINDING. It opens "From zero
    # to a playable voice" and the section preamble says "zero player
    # utterances"; `dialogue.SAY` exists and holds player lines under exactly
    # the ask/press/let-go stances the row specifies.
    say = _pool(dlg.SAY)
    covered = len(dlg.SAY)
    missing = [k for k, _f in dlg.TOPICS if k not in dlg.SAY]
    bad.append("the annex says 'from zero'; dialogue.SAY ships %d player "
               "templates over %d of the %d topics (missing %s) against a "
               "floor of %d -- the openers/closers, the 96 role work-lines and "
               "the 15 SHOW-PAPERS/BUY-SELL/refusal lines are still zero"
               % (len(say), covered, len(dlg.TOPICS),
                  ", ".join(missing) or "none", floor))
    return False, "DLG-05: " + "; ".join(bad)


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
    if getattr(dlg, "BROKER_LINES", None) is None:
        bad.append("no Broker pool exists (≤%d, audience-gated)" % broker)

    # The half that IS built and passes: an office-designate species has no
    # personal name to render, enforced by a raise rather than by a convention.
    for sp in sched.SPECIES_WITHOUT_NAMES:
        card = dict((k, v) for k, v, _s in res.identicard(res.resident("3", sp)))
        if card["NAME"]:
            bad.append("%s renders a personal NAME %r" % (sp, card["NAME"]))
    if not bad:
        return True, ("DLG-06: scarce voices capped and no office-designate "
                      "species renders a personal name")
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
