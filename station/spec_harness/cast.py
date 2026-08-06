"""CAST rows: the named-cast ladder, from the show-character policy to Tier 3.

SIX ROWS AND NO TWO OF THEM ASK THE SAME QUESTION, which is why this module
dispatches per row instead of running one grammar over all of them the way
`plc.py` does. CAST-01 is a policy ruling, CAST-02 a pinned 50-row roster,
CAST-03 the Tier-2 population, CAST-04 the statistical 250,000, CAST-05 a
memory system that does not exist, CAST-06 the children question.

`SUFFICIENT = True`, AND THAT IS A DELIBERATE, ARGUABLE CALL. CAST-04's ACCEPT
is the only row anywhere near this harness whose acceptance is *entirely*
headless -- *"render the identicard of npc_id 0, 124,999 and 249,999: all 9
fields; a Gaim draw shows SEX=HIVE and DES-ATMOS methane; a Brakiri draw shows
the empty red NAME field; the same three cards byte-match across two sessions
on two machines; and STATION_HEADCOUNT still sums 250,001 with Kosh outside the
statistical draw"*. Every clause of that is a function call. Declaring the
module not-sufficient would make it permanently unGREENable for a reason that
is not true of it.

The cost of that call is the honesty risk, and it is met head-on: **every one
of the six checks below is written so that a True return means the row's own
ACCEPT was met**, not that its address resolved. Five of the six therefore fail
today, each with the measured number that is missing, and none of them has a
branch that passes on absence. What a GREEN here would assert, per row:

  CAST-01  no show-cast given+surname pair is drawable, Kosh is the only
           instantiated canon character, and the offscreen offices are
           reachable as content.
  CAST-02  the fifty pinned residents exist, at their anchors, with links.
  CAST-03  the regulars pool is stable across two visits a week apart.
  CAST-04  the three cards render nine fields, deterministically.
  CAST-05  per-NPC memory and faction standing exist as state.
  CAST-06  no minor exists outside the three roles that source one, and every
           minor resolves a guardian.

THE ONE THING THIS CONTRACT CANNOT SAY, and it is filed in
`scratchpad/PATCHES-4r-spec-role-cast-dlg.md`: `SUFFICIENT` is per MODULE and a family
is not homogeneous. CAST-04 is settleable and CAST-05 is not, and one boolean
has to cover both.
"""
import os
import re

SUFFICIENT = True

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SRC_DIRS = ("station", "station/npc")

_HEAD = re.compile(r"^#+\s*CAST-(\d+)\s*[-—–]+\s*(.+?)\s*$")
_ROW = re.compile(r"^\|\s*(\d+)\s*\|")
# `hum`, `drz`, `cen F 47`, `other (insectoid) —`. The species code is the
# first token of the second column.
_SPCODE = re.compile(r"^([a-z']+)")
# The annex abbreviates species by prefix everywhere except one: `drz` drops
# its vowels. Prefix-match first, alias only where prefix cannot work, so the
# table is decoded rather than transcribed.
_SP_ALIAS = {"drz": "drazi"}


def _read(path):
    try:
        return open(os.path.join(_ROOT, path), encoding="utf-8",
                    errors="replace").read()
    except OSError:
        return ""


_SRC_CACHE = {}


def _sources():
    """Every shipped Python source, by path. Not the scratchpad worktrees.

    Cached, because five of the six checks below want it and re-reading ~60
    files per row is the difference between a smoke harness and a slow one.
    """
    if not _SRC_CACHE:
        for d in _SRC_DIRS:
            full = os.path.join(_ROOT, d)
            for f in sorted(os.listdir(full)):
                if f.endswith(".py"):
                    _SRC_CACHE[d + "/" + f] = _read(d + "/" + f)
    return _SRC_CACHE


def _table(text):
    """The CAST-02 roster as [(n, cells)], in document order."""
    rows = []
    for ln in text.splitlines():
        m = _ROW.match(ln.strip())
        if m:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows.append((int(m.group(1)), cells))
    return rows


def _species_of(code, known):
    code = code.strip().lower()
    if code in _SP_ALIAS:
        return _SP_ALIAS[code]
    if code in known:
        return code
    hits = [s for s in known if s.startswith(code)]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------------------
# CAST-01 -- the show-character policy
# ---------------------------------------------------------------------------
def _cast01(text):
    from npc import names as nm                                  # noqa: PLC0415
    from npc import resident as res                              # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415
    import directory as dr                                       # noqa: PLC0415
    import traffic                                               # noqa: PLC0415

    bad, good = [], []

    # ---- ACCEPT clause 1: no show-cast given+surname PAIR is drawable ------
    # THE BANNED PAIRS ARE NOT MINE. `npc/names.py` names them itself, in the
    # comment that explains why the pools hold them: "Which sex Jeffrey
    # Sinclair, Susan Ivanova, Michael Garibaldi, Stephen Franklin, Zack Allan,
    # Warren Keffer, Lianna Kemmer, Marcus Cole, David Corwin, Neeoma Connally
    # and Tessa Halloran are is a fact about the show, and these are its
    # names." So the list is READ OUT OF THE REPO rather than recalled, which
    # is hard rule 1 applied to a harness: a check built from memory is an
    # unmarked invention with a boolean on the end.
    src = _read("station/npc/names.py")
    given, surname = set(nm.HUMAN_GIVEN), set(nm.HUMAN_SURNAME)
    pairs = {(a, b) for a, b in re.findall(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", src)
             if a in given and b in surname}
    # ...and then CONSTRUCTED, not reasoned about. A pair being possible is an
    # argument; a pair coming out of the shipped draw is evidence.
    drawn = []
    for i in range(2000):
        sur, fore = res._split_name("human", str(i))
        if (fore, sur) in pairs:
            drawn.append((i, fore, sur))
    if drawn:
        bad.append("%d show-cast given+surname pairs are constructible from "
                   "names.py's own pools and %d of the first 2,000 human ids "
                   "draw one (npc_id %s is %s %s)"
                   % (len(pairs), len(drawn), drawn[0][0], drawn[0][1],
                      drawn[0][2]))
    else:
        good.append("no canon pair in 2,000 draws")

    # ---- rule 2: exactly one instantiated canon character, and it is Kosh ---
    if sched.VORLON_SINGLETON != 1:
        bad.append("VORLON_SINGLETON is %r, not 1" % sched.VORLON_SINGLETON)
    if "vorlon" in sched.STATION_COUNTS:
        bad.append("vorlon is inside STATION_COUNTS, so Kosh is sampled rather "
                   "than authored")
    if sched.STATION_HEADCOUNT != sum(sched.STATION_COUNTS.values()) + 1:
        bad.append("STATION_HEADCOUNT %d is not the statistical draw + Kosh"
                   % sched.STATION_HEADCOUNT)
    keys = {p["key"] for p in dr.PLACES}
    if "kosh_quarters" not in keys:
        bad.append("no `kosh_quarters` in the register")
    if not bad:
        good.append("Kosh authored, %d sampled" % sum(sched.STATION_COUNTS.values()))

    # ---- rule 5: era-gating ------------------------------------------------
    # Checked where it is EXACT rather than by grep: "no Markab" is a zero in
    # the census, "no White Star warship" is a ship class the manifest does not
    # carry. A case-insensitive grep for "white star" hits `arrival.py:351`,
    # where it is the attested name of a civilian LINER, and `costume.py:846`,
    # where it is seven stars on a flag -- two false findings for one true one.
    if "markab" in sched.STATION_COUNTS:
        bad.append("STATION_COUNTS carries markab -- extinct at the datum")
    for cls in traffic.MANIFEST:
        if "white_star" in cls[0] or "isa" == cls[0]:
            bad.append("manifest carries %r" % cls[0])
    if "markab_extinct" not in _era_events():
        bad.append("costume.ERA_EVENTS has no markab_extinct gate")

    # ---- ACCEPT clause 3: the offscreen offices are REACHABLE as content ----
    # The row names three specific artefacts. They are the whole difference
    # between "present-but-offscreen" and "absent", so they are the check.
    srcs = _sources()
    blob = "\n".join(srcs.values())
    if not re.search(r"not receiving", blob, re.I):
        bad.append('no "the Ambassador is not receiving" line exists anywhere')
    if not re.search(r"name.?plate", "\n".join(
            v for k, v in srcs.items() if "cnc" in k or "command" in k), re.I):
        bad.append("no name-plate content at `cnc`")
    if not re.search(r"commanding officer|station commander|the CO\b",
                     _read("station/broadcast.py")):
        bad.append("no PA order in the CO's name in broadcast.py")

    if bad:
        return False, "CAST-01: " + "; ".join(bad)
    return True, "CAST-01: policy holds -- " + "; ".join(good)


def _era_events():
    from npc import costume                                      # noqa: PLC0415
    return set(costume.ERA_EVENTS)


# ---------------------------------------------------------------------------
# CAST-02 -- the fifty pinned residents
# ---------------------------------------------------------------------------
def _cast02(text):
    from npc import resident as res                              # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415
    import directory as dr                                       # noqa: PLC0415

    bad, good = [], []
    rows = _table(text)
    if [n for n, _ in rows] != list(range(1, 51)):
        return False, ("CAST-02: the roster table is %d rows numbered %s, not "
                       "1..50" % (len(rows), rows[0][0] if rows else "-"))
    good.append("50 rows")

    keys = {p["key"] for p in dr.PLACES}
    known = set(sched.STATION_COUNTS) | {"vorlon"}
    homes, species = 0, 0
    for n, cells in rows:
        if len(cells) < 7:
            bad.append("row %d has %d columns" % (n, len(cells)))
            continue
        sp = _species_of((_SPCODE.match(cells[2]) or [""])[0], known)
        if sp is None:
            bad.append("row %d's species code %r decodes to nothing"
                       % (n, cells[2][:8]))
        else:
            species += 1
        for h in re.findall(r"`([a-z0-9_]+)`", cells[4]):
            if h not in keys:
                bad.append("row %d lives at `%s`, which the register has no "
                           "place for" % (n, h))
            else:
                homes += 1
        for link in re.findall(r"\b(\d+)\b", cells[6].split("—")[0]):
            if not 1 <= int(link) <= 50:
                bad.append("row %d links to %s, off the 1..50 roster"
                           % (n, link))
    good.append("%d home addresses resolve, %d species decode" % (homes, species))

    # THE OFFICE-DESIGNATES, named by the annex itself two paragraphs below the
    # table: "rows 5, 25, 35, 36, 46, 47, 50: the empty red NAME field; row 47:
    # SEX=HIVE". Content, and checkable now.
    named = re.search(r"rows?\s+((?:\d+,\s*)+\*?\*?\d+\*?\*?)\s*:\s*the empty red",
                      text)
    desig = [int(x) for x in re.findall(r"\d+", named.group(1))] if named else []
    if len(desig) < 5:
        bad.append("cannot read the office-designate row list from the annex")
    by_n = dict(rows)
    for n in desig:
        cells = by_n.get(n)
        if not cells:
            continue
        sp = _species_of((_SPCODE.match(cells[2]) or [""])[0], known)
        if sp not in sched.SPECIES_WITHOUT_NAMES:
            bad.append("row %d is an office-designate but %s HAS a name "
                       "grammar" % (n, sp))
            continue
        card = dict((k, v) for k, v, _s in res.identicard(res.resident("7", sp)))
        if card["NAME"]:
            bad.append("row %d (%s) renders NAME %r, not the empty red field"
                       % (n, sp, card["NAME"]))
    if desig and not bad:
        good.append("%d office-designates render an empty NAME" % len(desig))
    if 47 in by_n:
        sp = _species_of((_SPCODE.match(by_n[47][2]) or [""])[0], known)
        card = dict((k, v) for k, v, _s in res.identicard(res.resident("7", sp)))
        if card["SEX"] != "HIVE":
            bad.append("row 47 renders SEX=%r, not HIVE" % card["SEX"])

    # ---- and now the row's own CHECK: are these fifty people IN the game? ---
    # The umbrella's three probes are Delgado at the muster board at 05:40,
    # Delgado greeting a player she has met, and Duarte's 340 cr debt going
    # quiet when it is paid. None of them can even be attempted while the
    # roster is a table in a document, so the first question is whether the
    # names exist in code at all.
    # ---- and now the row's own CHECK: are these fifty people IN the game? ---
    # PRESENCE IS COUNTED TWICE, and the second count is the one that matters.
    # A surname appearing SOMEWHERE in `station/` proves very little: `Halloran`
    # is in `names.py`'s comment about which canon names are real, and `Brakk`
    # is inside a string in `economy.py`'s goods table ("Brakk's stall; a
    # sealant is a solvent"). Neither is a resident with a home, a schedule and
    # two links. A real Tier-1 roster is ONE table carrying all fifty, so the
    # discriminating number is the most any single module knows about.
    srcs = _sources()
    names = []
    for n, cells in rows:
        name = re.sub(r"\*\*|`", "", cells[1]).strip()
        if name.lower().startswith("the "):
            continue                     # office-designates have no name to find
        names.append((n, name.replace("'", "").split()[-1]))
    # ONE ALTERNATION, ONE PASS PER FILE. Forty-two names searched separately
    # across sixty modules is 2,520 scans and took 9.8 s -- ten times the
    # smoke tier's whole budget for a row.
    rx = re.compile(r"\b(%s)\b" % "|".join(re.escape(l) for _n, l in names))
    seen, best_file, best = set(), "-", 0
    for path, body in srcs.items():
        hit = set(rx.findall(body))
        seen |= hit
        if len(hit) > best:
            best_file, best = path, len(hit)
    anywhere = sorted(seen)
    if best < len(names):
        bad.append("%d of the %d named rows appear anywhere in station/ and no "
                   "single module carries more than %d of them (%s), so there "
                   "is no Tier-1 roster to probe: probes 1-3 (Delgado at the "
                   "05:40 muster, her memory of the player, Duarte's 340 cr "
                   "debt going quiet) cannot run"
                   % (len(anywhere), len(names), best, best_file))

    if bad:
        return False, "CAST-02: " + "; ".join(bad[:6])
    return True, "CAST-02: " + "; ".join(good)


# ---------------------------------------------------------------------------
# CAST-03 -- Tier 2, named-with-schedule
# ---------------------------------------------------------------------------
def _cast03(text):
    from npc import resident as res                              # noqa: PLC0415

    bad, good = [], []
    # LOCAL_BIAS is quoted in the row and is the mechanism the whole ACCEPT
    # rests on: "somebody who drinks in Earhart's drinks in Earhart's".
    m = re.search(r"LOCAL_BIAS=([\d.]+)", text)
    if m and abs(float(m.group(1)) - res.LOCAL_BIAS) > 1e-9:
        bad.append("spec says LOCAL_BIAS=%s, resident.py has %.2f"
                   % (m.group(1), res.LOCAL_BIAS))

    # THE ACCEPT IS HEADLESS AND IS RUN HERE, as far as it goes: "enter
    # bar_unnamed at 21:00 on two visits a week apart ... >=12 patrons of whom
    # >=8 recur from the regulars pool with the same faces, names and seats".
    a = res.roster("bar_unnamed", 21.0, "human", 14)
    b = res.roster("bar_unnamed", 21.0 + 7 * 24, "human", 14)
    recur = len({r.npc_id for r in a} & {r.npc_id for r in b})
    if len(a) < 12:
        bad.append("bar_unnamed casts %d patrons at 21:00, the ACCEPT wants "
                   ">=12" % len(a))
    if recur < 8:
        bad.append("only %d of them recur a week later, the ACCEPT wants >=8"
                   % recur)
    else:
        good.append("%d of %d patrons recur a week later" % (recur, len(a)))

    # ...and the half that cannot run: the ACCEPT's second sentence names Milo
    # and Vresh, who are CAST-02 rows, and CAST-02 reports 0 of 50 in code.
    ok, note = _cast02_presence()
    if not ok:
        bad.append(note)
    if bad:
        return False, "CAST-03: " + "; ".join(bad)
    return True, "CAST-03: " + "; ".join(good)


def _cast02_presence():
    """Whether the Tier-1 names exist in code -- CAST-03's ACCEPT needs two."""
    blob = "\n".join(_sources().values())
    want = ("Okada", "Vresh")
    miss = [w for w in want if not re.search(r"\b%s\b" % w, blob)]
    if miss:
        return False, ("the ACCEPT names Milo and Vresh behind the counter and "
                       "%s appear(s) nowhere in station/" % ", ".join(miss))
    return True, ""


# ---------------------------------------------------------------------------
# CAST-04 -- Tier 3, the statistical 250,000
# ---------------------------------------------------------------------------
def _cast04(text):
    from npc import resident as res                              # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415

    bad, good = [], []
    ids = [int(x.replace(",", "")) for x in
           re.findall(r"npc_id ([\d,]+), ([\d,]+) and ([\d,]+)", text)[0]] \
        if re.search(r"npc_id [\d,]+, [\d,]+ and [\d,]+", text) else []
    if not ids:
        return False, "CAST-04: cannot read the three npc_ids out of the ACCEPT"
    for i in ids:
        card = res.identicard(res.resident(str(i)))
        if tuple(k for k, _v, _s in card) != tuple(res.CARD):
            bad.append("npc_id %d's card is not the prop's nine fields in "
                       "order" % i)
        # byte-match on a second construction. `resident` is `lru_cache`d, so
        # the cache is dropped first -- otherwise this compares an object with
        # itself, which is the vacuous A/B this project has already paid for.
        res.resident.cache_clear()
        if res.identicard(res.resident(str(i))) != card:
            bad.append("npc_id %d does not reproduce" % i)
    good.append("%d cards, 9 fields, reproducible" % len(ids))

    gaim = res.resident("7", "gaim")
    gcard = dict((k, v) for k, v, _s in res.identicard(gaim))
    if gcard["SEX"] != "HIVE":
        bad.append("a Gaim draw renders SEX=%r" % gcard["SEX"])
    # THE ACCEPT ASKS FOR SOMETHING THE CODE DECLINES TO PRINT, and this is a
    # spec/code disagreement rather than a bug in either: the row wants
    # "DES-ATMOS methane" on the card, and `resident.ATMOS_NUMBER` numbers ONLY
    # the standard oxygen mix -- "nothing numbers them, and a wrong number
    # printed on a wall is worse than a blank" -- so a Gaim card renders
    # DES/ATMOS EMPTY and carries methane in `atmos_class`, MEDICAL and PHYS
    # CHR instead. Reported with both readings; not resolved here.
    if "methane" in text and "methane" not in gcard["DES/ATMOS"].lower():
        bad.append("the ACCEPT wants DES-ATMOS methane on a Gaim card; "
                   "ATMOS_NUMBER['methane'] is %r by design, so the field "
                   "renders %r and atmos_class=%r carries the fact"
                   % (res.ATMOS_NUMBER.get("methane"), gcard["DES/ATMOS"],
                      gaim.atmos_class))
    if res.identicard(res.resident("7", "brakiri"))[0][2] != res.EMPTY:
        bad.append("a Brakiri draw does not render the empty red NAME field")

    if sched.STATION_HEADCOUNT != 250001:
        bad.append("STATION_HEADCOUNT is %d, not 250,001"
                   % sched.STATION_HEADCOUNT)
    if sum(sched.STATION_COUNTS.values()) != 250000:
        bad.append("the statistical draw sums %d, not 250,000"
                   % sum(sched.STATION_COUNTS.values()))
    # the age bands the row quotes verbatim
    for sp, lo, hi in re.findall(r"(human|Minbari|Hyach) (\d+)[-–—](\d+)", text):
        band = res.AGE_BAND.get(sp.lower())
        if band and (band[0] != int(lo) or band[1] != int(hi)):
            bad.append("%s band is %s in code, %s-%s in the spec"
                       % (sp, band, lo, hi))
    if bad:
        return False, "CAST-04: " + "; ".join(bad)
    return True, ("CAST-04: " + "; ".join(good) + "; STATION_HEADCOUNT 250,001 "
                  "with Kosh outside the draw. NOT checked: 'on two machines' "
                  "-- this runs in one process")


# ---------------------------------------------------------------------------
# CAST-05 -- memory, standing and the relationship graph
# ---------------------------------------------------------------------------
def _cast05(text):
    from npc import resident as res                              # noqa: PLC0415
    import dialogue as dlg                                       # noqa: PLC0415

    # The row lists four pieces of save-persisted state. Each is probed for as
    # an API, not grepped for as a word, so a comment cannot satisfy it.
    missing = []
    lis = getattr(dlg, "Listener", None)
    fields = set(getattr(lis, "__dataclass_fields__", {}) or {})
    if not fields & {"met", "known", "name_given"}:
        missing.append("met/known two-stage flags (dialogue.Listener carries "
                       "%s)" % (", ".join(sorted(fields)) or "nothing"))
    if not any(hasattr(res.Resident, f) for f in ("memory", "last_topic",
                                                  "ledger")):
        missing.append("per-NPC memory slots")
    blob = "\n".join(_sources().values())
    if not re.search(r"\bdef (save|persist)_", blob):
        missing.append("any save/restore of world state")
    # `\b` MATTERS HERE: without it this matched `fines_outstanding: float`
    # in `consequence.py` three times and reported faction standing as PRESENT.
    if not re.search(r"\bstanding\s*[:=]\s*(float|-?[\d.]+)", blob):
        missing.append("faction standing scalars")
    if missing:
        return False, ("CAST-05: %s -- the row's own premise (\"no "
                       "relationship graph, no memory of the player, no "
                       "persistent world-state exists\") still holds"
                       % "; ".join(missing))
    return True, "CAST-05: memory, standing and the link graph are live state"


# ---------------------------------------------------------------------------
# CAST-06 -- households and the children question
# ---------------------------------------------------------------------------
def _cast06(text):
    from npc import resident as res                              # noqa: PLC0415
    from npc import schedule as sched                            # noqa: PLC0415

    bad = []
    m = re.search(r"ages (\d+)[-–—](\d+)", text)
    lo, hi = (int(m.group(1)), int(m.group(2))) if m else (4, 17)
    roles = tuple(re.findall(r"\b(visitor|refugee|lurker)\b", text))
    want = {"visitor", "refugee", "lurker"}
    if want - set(roles):
        bad.append("the row no longer names the three sourcing roles")

    # THE CENSUS, sampled rather than exhaustive and SAYING SO. 250,000
    # `resident()` builds is 58 s and this tier is defined as sub-second; the
    # draw is a pure hash of npc_id, so a 6,000-id sample over three species is
    # a real sample of the same function and finds a systematic escape.
    N, minors, escapes = 2000, 0, []
    for sp in ("human", "narn", "drazi"):
        for i in range(N):
            role = sched.role_for(str(i), sp).key
            age = res._age(str(i), sp, role)
            if age < 18:
                minors += 1
                if role not in want:
                    escapes.append((sp, i, role, age))
                if not (lo <= age <= hi):
                    bad.append("npc_id %s (%s) is %d, outside the %d-%d band"
                               % (i, sp, age, lo, hi))
    if escapes:
        bad.append("%d minors hold a role that does not source one, first "
                   "%s" % (len(escapes), escapes[0]))
    if not minors:
        bad.append("no minor appeared in %d draws -- the 8%% is not firing"
                   % (3 * N))

    # the household link the row's ACCEPT turns on
    if not any(hasattr(res.Resident, f) for f in ("guardian", "household",
                                                  "family")):
        bad.append("no guardian/household link exists on Resident, so \"every "
                   "minor resolves a guardian link\" cannot be true of the "
                   "%d minors in the sample" % minors)
    if bad:
        return False, "CAST-06: " + "; ".join(bad[:4])
    return True, ("CAST-06: %d minors in %d draws, every one in a sourcing "
                  "role with a guardian" % (minors, 3 * N))


_ROWS = {1: _cast01, 2: _cast02, 3: _cast03, 4: _cast04, 5: _cast05,
         6: _cast06}


def check(row):
    from spec_harness import spec_text                           # noqa: PLC0415
    text = spec_text(row.get("at", ""), lines=130)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    mh = _HEAD.match(text.splitlines()[0].strip())
    if not mh:
        return False, "heading is not a CAST row: %r" % text.splitlines()[0][:60]
    n = int(row["id"].split("-")[1])
    if int(mh.group(1)) != n:
        return False, "%s's heading says CAST-%s" % (row["id"], mh.group(1))
    fn = _ROWS.get(n)
    if fn is None:
        return False, "no check is written for %s" % row["id"]
    return fn(text)
