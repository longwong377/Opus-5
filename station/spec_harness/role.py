"""ROLE rows: the twelve careers, checked at their SEATING rather than at play.

WHAT A ROLE ROW IS. Each of the twelve names a job a player can hold and is
built out of six labelled parts -- **Seated by** (the evidence the role is
already data-complete), **Get it**, **The shift/day/run/trade/sortie**,
**Mastery**, **Incidents exposed**, **ACCEPT**. The Seated-by line is the only
part a headless harness can decide, and it is the part that rots: it cites the
roster headcount the role is drawn from and the exact `file.py:line-line` where
the machinery lives, and both of those are numbers in code that move.

SO THIS IS AN ADDRESS HARNESS AND `SUFFICIENT = False`. Every ROLE row's ACCEPT
is a played shift -- *"work one full liner surge end-to-end"*, *"one full
C-watch"*, *"live seven days below with no status"*. There is no career system,
no shift clock and no player job anywhere in the project, so a GREEN here would
assert something that has not been built. What this harness settles is narrower
and still worth having: the role's workforce still exists at the size the spec
quotes, and every line number the spec points at still points at the thing.

WHAT IT DELIBERATELY DOES NOT CHECK, AND THE MEASUREMENT BEHIND THAT. Two
tempting checks were built, measured against the live annex, and dropped
because they report a PARSE failure rather than a station fact -- which is the
one thing rule 2 says a harness must not do:

  * **The closed verb set.** The annex's preamble (PEOPLE.md around line 771)
    is normative: *"Every loop below is written in the closed player verb set
    ... LOOK, USE, TAKE/PLACE, SIT, BUY/SELL, TALK, WORK, SHOW-PAPERS,
    FIGHT/RESTRAIN, PILOT, RIDE, SLEEP, EAT/DRINK"*. Extracting the shift's
    verbs by ALL-CAPS token gives **41 distinct non-verb tokens across the 12
    rows** (`ACCEPT`, `FAC-`, `SYS-`, `POSTS`, `PPG`, `SANCTUARY`, `NOTHING`,
    `VACANT` ...); restricting to verb POSITION -- a capital token followed by
    a lowercase word, `(` or `[T` -- still leaves 16 false hits and would
    report 10 of 12 rows as malformed. There IS one true escape in there and
    it was found by reading, not by regex: **ROLE-07's shift says `READ`
    gauges, and READ is not one of the thirteen verbs.** That is filed as
    drift, not as a check.
  * **The `[T-tier]` fixtures.** `USE cargo_crane [T3]` looks like a machine
    vocabulary and is one 17 times out of 33; the other 16 are the last word
    of a noun phrase (`handoff [T3]`, `report [T3]`, `till [T3]`, `gauges
    [T1->T2]`). 48% noise is a bad parse, not 16 missing props.

Backticked names ARE checked, because that grammar is unambiguous: 14 of them
across the twelve rows and all 14 resolve today, so the check is inert-but-real
rather than untested -- break one and it says so.
"""
import os
import re

SUFFICIENT = False

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Where a `foo.py` or `foo.gd` named in the spec is allowed to live. Ordered,
# and the scratchpad worktrees are NOT on it: `find . -name starfury.gd` returns
# three paths, two of them an agent's private checkout, and a harness that
# resolved a citation against one of those would be checking a copy.
_SRC_DIRS = ("station", "station/npc", "godot/scripts", "tools")

_HEAD = re.compile(r"^#+\s*ROLE-(\d+)\s*[-—–]+\s*(.+?)\s*$")
# `arrival.py:440-545`, `dialogue.py:1314`, `starfury.gd:12-20`. The dash is an
# en-dash in this annex and a hyphen in others; take either.
_CIT = re.compile(r"\b([a-z_][a-z_0-9]*\.(?:py|gd))\s*:\s*(\d+)"
                  r"(?:\s*[-–—]\s*(\d+))?")
_FILE = re.compile(r"\b([a-z_][a-z_0-9]*\.(?:py|gd))\b")
# `LAW-CRIME:211-232`, `FACTIONS:366`, `LIFE-SUPPORT:121`
_DOCCIT = re.compile(r"\b([A-Z][A-Z-]{3,})\s*(?:§[\d.]+\s*)?:\s*(\d+)"
                     r"(?:\s*[-–—]\s*(\d+))?")
_BACKTICK = re.compile(r"`([a-z][a-z0-9_]*)`")
_INV = re.compile(r"\bINV-(\d+)\b")
_IDENT = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+|[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b")
_SHIFT_H = re.compile(r"(\d+)-h\s+shifts?")
_LABEL = re.compile(r"\*\*([A-Za-z][^:*]{0,32}):\*\*")

_REQUIRED_LABELS = ("Seated by", "Get it", "Mastery", "Incidents exposed",
                    "ACCEPT")


def _read(path):
    try:
        return open(os.path.join(_ROOT, path), encoding="utf-8",
                    errors="replace").read()
    except OSError:
        return None


def _src(fname):
    """The one canonical path for a source file the spec names, or None."""
    for d in _SRC_DIRS:
        p = os.path.join(d, fname)
        if os.path.exists(os.path.join(_ROOT, p)):
            return p
    return None


def _doc(name):
    """`LAW-CRIME` -> `docs/gazetteer/LAW-CRIME-DOWNBELOW.md`.

    The annex cites gazetteer files by their leading word, not their filename,
    so the match is a prefix. Ambiguity is reported rather than guessed at.
    """
    d = os.path.join(_ROOT, "docs/gazetteer")
    hits = [f for f in sorted(os.listdir(d))
            if f.startswith(name) and f.endswith(".md")]
    return "docs/gazetteer/" + hits[0] if len(hits) == 1 else None


def _clause(text, end):
    """The clause a citation sits in: back to the previous `;` or newline pair.

    WHY NOT A FIXED WINDOW. The first version took 140 characters and reported
    `VISA_EXPIRED_P` missing from `schedule.py` -- a false finding, because the
    row attributes that constant to the identicard renderer in the PREVIOUS
    clause and the citation belongs to `wave_pulse` in this one. Semicolons are
    what this annex separates its evidence with; use them.
    """
    start = max(text.rfind(";", 0, end), text.rfind(". ", 0, end),
                text.rfind("**", 0, end))
    return text[start + 1:end]


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def check(row):                                                  # noqa: C901
    import directory as dr                                       # noqa: PLC0415
    import interact as it                                        # noqa: PLC0415
    import rooms                                                 # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415
    from spec_harness import spec_text                           # noqa: PLC0415

    text = spec_text(row.get("at", ""), lines=60)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    lines = text.splitlines()
    mh = _HEAD.match(lines[0].strip())
    if not mh:
        return False, "heading is not a ROLE row: %r" % lines[0][:60]
    want_n = int(row["id"].split("-")[1])
    if int(mh.group(1)) != want_n:
        return False, "%s's heading says ROLE-%s" % (row["id"], mh.group(1))
    title = mh.group(2)

    bad, ok_notes = [], []

    # ---- the row's own six-part shape (the WORK-fidelity clause's frame) ----
    labels = {_norm(x) for x in _LABEL.findall(text)}
    missing = [x for x in _REQUIRED_LABELS if x not in labels]
    # "The shift" is spelled five ways across the twelve (shift / day / run /
    # trade / sortie), so it is matched by its opening word rather than listed.
    if not any(x.startswith("The ") for x in labels):
        missing.append("The <shift>")
    if missing:
        bad.append("row has no %s section" % ", ".join(missing))

    seated = text.split("**Seated by:**", 1)[-1].split("**Get it:**")[0]
    # STRIP THE CITATIONS BEFORE LOOKING FOR A HEADCOUNT, and this is not
    # tidiness: `traffic.py:132-142` matched the roster pattern as "traffic
    # 132" and reported ROLE-03 as claiming a 132-strong traffic branch
    # against the register's 400. A line number is not a population.
    seated_prose = _CIT.sub(" ", seated)

    # ---- the workforce it is drawn from, against schedule.ROLE_WEIGHTS ------
    # ROLE_WEIGHTS is an apportionment of STATION_COUNTS per species; the roll
    # over species is the station's headcount for that job, which is the number
    # every Seated-by line quotes.
    totals = {}
    for w in sched.ROLE_WEIGHTS.values():
        for k, n in w.items():
            totals[k] = totals.get(k, 0) + int(n)
    claimed = []
    for key in sorted(totals):
        m = re.search(r"\b%s\b[^\d\n]{0,4}([\d][\d,]{2,})" % re.escape(key),
                      seated_prose)
        if not m:
            continue
        n = int(m.group(1).replace(",", ""))
        claimed.append(key)
        if n != totals[key]:
            bad.append("roster: spec says %s %s, ROLE_WEIGHTS totals %d"
                       % (key, m.group(1), totals[key]))
        else:
            ok_notes.append("%s %d" % (key, n))
        mh2 = _SHIFT_H.search(seated_prose)
        if mh2 and abs(float(mh2.group(1)) - sched.ROLES_BY_KEY[key].work_hours) > 0.01:
            bad.append("shift length: spec says %s-h, schedule.ROLES says %.0f-h"
                       % (mh2.group(1), sched.ROLES_BY_KEY[key].work_hours))
    if not claimed:
        # Three rows are seated on something other than a roster row -- the
        # porter on a share of the informal economy, the broker on an informer
        # census, the pilot on FACTIONS' flight-ops complement. That is not a
        # defect; it IS a fact worth printing, because `flight ops 350` is a
        # workforce `ROLE_WEIGHTS` does not carry.
        ok_notes.append("no ROLE_WEIGHTS roster claim")

    # ---- every file it names exists, at the one path it is allowed to -------
    for f in sorted(set(_FILE.findall(text))):
        if _src(f) is None:
            bad.append("names %s, which is in none of %s"
                       % (f, ", ".join(_SRC_DIRS)))

    # ---- every line citation still points at what the clause claims ---------
    for m in _CIT.finditer(text):
        f, a = m.group(1), int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        p = _src(f)
        if p is None:
            continue                                  # already reported above
        src = (_read(p) or "").splitlines()
        if b > len(src) or a < 1:
            bad.append("%s:%d-%d is past the end of a %d-line file"
                       % (f, a, b, len(src)))
            continue
        # slack: a range is a claim about a span and gets none; a bare line
        # number is a pointer at a definition and gets five lines either way.
        slack = 0 if m.group(3) else 5
        for ident in set(_IDENT.findall(_clause(text, m.start()))):
            if ident.endswith(".py") or ident.endswith(".gd"):
                continue
            hits = [i + 1 for i, ln in enumerate(src)
                    if re.search(r"\b%s\b" % re.escape(ident), ln)]
            if not hits:
                bad.append("clause names `%s` at %s:%d-%d and %s has no "
                           "occurrence of it" % (ident, f, a, b, f))
            elif not any(a - slack <= h <= b + slack for h in hits):
                bad.append("`%s` is cited at %s:%d-%d and lives at line %s"
                           % (ident, f, a, b,
                              ", ".join(str(h) for h in hits[:4])))

    # ---- gazetteer citations resolve to a file and a line that exists -------
    for m in _DOCCIT.finditer(text):
        name, a = m.group(1), int(m.group(2))
        b = int(m.group(3)) if m.group(3) else a
        p = _doc(name)
        if p is None:
            continue          # not a gazetteer name -- an ID like `SPEC-CHANGE`
        n = len((_read(p) or "").splitlines())
        if b > n:
            bad.append("%s:%d-%d is past the end of %s (%d lines)"
                       % (name, a, b, os.path.basename(p), n))

    # ---- backticked names resolve to a place, a prop, or a symbol ----------
    keys = {p["key"] for p in dr.PLACES}
    vocab = set()
    for src_obj in (rooms, it):
        for n in dir(src_obj):
            v = getattr(src_obj, n)
            if isinstance(v, dict):
                vocab |= {k for k in v if isinstance(k, str)}
                for x in v.values():
                    if isinstance(x, (list, tuple)):
                        vocab |= {y for y in x if isinstance(y, str)}
            elif isinstance(v, (tuple, list, set, frozenset)):
                vocab |= {y for y in v if isinstance(y, str)}
    for p in dr.PLACES:
        vocab |= set(p.get("interacts") or ())
    for name in sorted(set(_BACKTICK.findall(text))):
        if name in keys or name in vocab:
            continue
        found = any(re.search(r"\b%s\b" % re.escape(name), _read(os.path.join(d, f)) or "")
                    for d in _SRC_DIRS
                    for f in sorted(os.listdir(os.path.join(_ROOT, d)))
                    if f.endswith((".py", ".gd")))
        if not found:
            bad.append("`%s` names no place, prop or symbol anywhere" % name)

    # ---- declared inventions exist ----------------------------------------
    inv = _read("canon/INVENTIONS.md") or ""
    for n in sorted(set(_INV.findall(text))):
        if not re.search(r"\bINV-%s\b" % n, inv):
            bad.append("cites INV-%s, which canon/INVENTIONS.md has no entry for" % n)

    head = "%s (%s)" % (row["id"], title[:34])
    if bad:
        return False, "%s: %s" % (head, "; ".join(bad))
    return True, ("%s: seated -- %s; every citation resolves. NOT settled: the "
                  "row's ACCEPT is a played shift and no career system exists"
                  % (head, ", ".join(ok_notes) or "no roster claim"))
