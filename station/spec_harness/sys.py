"""SYS rows: the sixteen station systems, against the modules they name.

WHAT A SYS ROW IS, AND WHY MOST OF IT CANNOT BE SETTLED HERE. Every row is five
declared fields -- State, Tick, Couples to, Player surface, Check -- plus a
`harness:` line, and SYSTEMS.md's own format law (line 3-9 of the annex) makes
that shape normative: *"A field an item genuinely lacks is written `none`, never
omitted."* The CHECK field is almost always a simulation: *"boot day 1, run to
day 8 headless"*, *"across one headless day"*, *"a scripted theft in the Zocalo
is detected in seconds"*. None of that runs in the smoke tier and most of it
does not run at all yet, so `SUFFICIENT = False` -- a GREEN here would assert a
day-run this file never performed.

WHAT IT DOES CHECK IS THE HALF OF EACH ROW THAT IS ALREADY A FACT. A SYS row is
unusual among the families in how much of it is arithmetic the station can be
asked about today: it names modules, cites them by `file:line`, restates their
constants, and quotes derived numbers. Four generic checks and one per-row
table:

  format      the five fields and the harness line are present. This is the
              annex's own law and it is checked first because a row missing a
              field is a row whose claim is unreadable, not a row that
              disagrees.
  citations   every `<module>.py:<a>-<b>` resolves to a real file with that
              many lines, AND every symbol the row names that is defined in
              that file is defined INSIDE the cited range. That last clause is
              what makes the citation a claim rather than a decoration, and it
              is what found SYS-04's drift.
  references  every `PLC-`/`SYS-`/`FAC-`/`INC-`/`GDS-`/`PLY-`/`ROLE-`/`SHB-`/
              `SHC-`/`CAST-`/`DLG-`/`VRB-`/`SUR-` id resolves against
              `docs/spec/completion.yaml`; every `C-nnn` against
              `canon/CONFLICTS.md`; every `INV-nnn` against
              `canon/INVENTIONS.md`; every `SPEC-CHANGE #n` against
              `docs/THE-STATION.md`. A row that couples to a renumbered thing
              is a row that has quietly stopped meaning what it says.
  constants   a `NAME=value` the row states is resolved in the modules the row
              names (then in a declared search order) and compared.
  tools       every `<file> --flag` the row names -- the harness line above
              all -- resolves to a file that contains that literal flag. A
              harness line naming a command that cannot run is this project's
              oldest defect at spec scale.
  CLAIMS      the per-row table below, and it is where the real content is:
              traffic's ten-class manifest restated 1:1, the customs pipeline's
              ten stations counted inside the cited line range, the economy's
              five quoted prices against `economy.LADDER`, the plant's five
              headline flows re-derived from `plant_systems`' own per-head
              constants, transit's four timetables and the two journey times,
              and SYS-15's venue list against `civic_calendar.RULES` in both
              directions.

WHAT IT FOUND, AND ALL FOUR ARE LIVE FAILURES RATHER THAN A DEMONSTRATION:

  SYS-04   `CREDIT_MIN/MAX exist, player.py:140-174` -- they are at **192 and
           193**. Session 4q inserted INV-410's inventory-slot derivation above
           them; lines 140-174 are now that comment. The citation still
           resolves and still points at a real file, which is exactly why only
           a containment check can see it.
  SYS-06   *"the route's five stations"*, twice in one row -- and
           `security.BLACK_MARKET_ROUTE` carries **six**. The row's own
           parenthesis lists five (bribed docker, cargo lift, unfinished-deck
           cache, fixer, Zocalo under-counter) and the code's sixth is
           `black_market`, the margin stall between the fixer and retail. The
           check that follows -- *"traces back through the route's five
           stations when followed"* -- would trace six.
  SYS-10   **no Tick field.** The annex's format law says a field an item
           genuinely lacks is written `none` and never omitted; SYS-10 writes
           State, Builds, Couples to, Player surface and Check, and no Tick.
           It is the only one of the twenty-five SYS+SUR rows that does --
           `grep -c "Tick:"` returns 25 over 25 rows, and SYS-14 has two.
           It matters rather than being tidiness: the row's own State declares
           exposure timers, a drunk condition that "decays by morning" and a
           therapy queue, all of which are things that tick.
  SYS-14   *"the **22-class union below IS PLACES §0.2's vocabulary**"* against
           its own CHECK field eight lines later: *"the 30-row union above
           matches PLACES §0.2 in both directions"*. The table is **30** rows
           and `incident.CLASSES` is **30**. The row contradicts itself; the
           code agrees with the second number.

WHAT IS NOT CHECKED HERE AND WHY, stated so nobody reads a pass as more than it
is. `SYS-05`'s *"escalation ladder 7 rungs"* names no code object --
`consequence.RUNGS` is the six-rung CARD ladder and is a different thing.
`SYS-09`'s *"70 shafts"* appears nowhere but this row. `SYS-12`'s `K=3` memory
slots are an auth-5 invention with no implementation. `SYS-07`'s *"three
rosettes"* and *">98% closure"* are prose in `plant_systems`' docstring rather
than data. Each is named in the row's note rather than passed over in silence.

EVERY CHECK ABOVE HAS BEEN RUN BOTH WAYS. The five that pass on the live
station were each made to fail by moving one number in the station -- one
manifest rate by 0.1/day, one POSTS pair, 5 L of hygiene water, one journey
time, one calendar rule -- and the four that fail were each made to pass by
correcting the ROW, which is also the proof that the expected values are read
out of the annex rather than restated in this file. A check that cannot do both
is not a check.

COST: **0.568 s for all sixteen rows in one process**, 0.036 s a row amortised,
and it is the same shape `inc.py` records -- the first row that reaches a module
pays for the import and the rest are microseconds. Cold, one row at a time
through `spec_check.py --id`: 317 ms for SYS-009 (it loads the schema and builds
four timetables), 221 ms for SYS-002, 127 ms for SYS-015.
"""
import os
import re

SUFFICIENT = False

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# The annex's own format law (docs/spec/SYSTEMS.md:3-9), read as a shape.
# ---------------------------------------------------------------------------
# `**State:**`, `**CHECK:**`, `**Check (named, end-to-end):**` and `**harness:**`
# are all real headings in the live annex and the parenthetical is why an
# earlier version of this regex reported SYS-15 as missing its Check. Measured
# the shapes over all 25 SYS+SUR rows before widening it: five labels appear on
# every row, one row bolds its harness line and twenty-four do not.
_FIELD = re.compile(r"^\*\*(?P<lab>[A-Za-z][A-Za-z ,'\-]*?)"
                    r"(?P<paren>\s*\([^)]*\))?:\*\*", re.M)
_HARNESS = re.compile(r"^\**harness\**\s*:", re.M | re.I)
_REQUIRED = ("state", "tick", "couples to", "player surface", "check")

# `traffic.py:132-142`, `npc/costume.py:147-168`, `resident.py:846-893`
_CIT = re.compile(r"\b((?:[a-z_][a-z_0-9]*/)*[a-z_][a-z_0-9]*\.py)"
                  r":(\d+)(?:-(\d+))?")
# `LAW-CRIME:748`, `LIFE-SUPPORT:65-114`, `TRAFFIC-AND-CUSTOMS 6.3`
_GAZ = re.compile(r"\b([A-Z][A-Z\-]{3,}):(\d+)(?:-(\d+))?")
_ID = re.compile(r"\b(PLC|INC|SYS|FAC|GDS|PLY|SUR|ROLE|SHB|SHC|CAST|DLG|VRB)"
                 r"-([A-Za-z0-9]+(?:/\d+)*)")
_CONFLICT = re.compile(r"\bC-(\d{3})\b")
_INV = re.compile(r"\bINV-(\d+)(?:\.\.(\d+))?")
_SPECCHANGE = re.compile(r"SPEC-CHANGE\s*#(\d+)")
_CONST = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\s*=\s*"
                    r"(\(\s*\d+\s*,\s*\d+\s*\)|"
                    r"[0-9]+(?:\.[0-9]+)?(?:\s*/\s*[0-9]+(?:\.[0-9]+)?)?)")
_UPPER = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\b")
_MODPY = re.compile(r"\b([a-z_][a-z_0-9]*)\.py\b")
_DEF = re.compile(r"^(?:def\s+|class\s+)?([A-Za-z_][A-Za-z_0-9]*)\s*[=(:]", re.M)

# WHERE A BARE CONSTANT NAME IS LOOKED UP. Order is declared rather than
# alphabetical: a row names its own module first, and this list is only the
# fallback for names the row states without a module (`NIGHTWATCH_SHARE=175/500`
# is Nightwatch's, not the era clock's). Every entry is import-cheap -- measured
# 0.46 s for the whole list in one process, and it is imported one at a time
# until the name is found, so no row pays for all of it.
_SEARCH = ("traffic", "arrival", "player", "economy", "broadcast", "transit",
           "consequence", "plant_systems", "directory", "signage",
           "alien_sector", "incident", "npc.security", "npc.costume",
           "npc.schedule", "npc.resident")

_REG_IDS = None
_DEFS = {}


def _text(row, lines=140):
    from spec_harness import spec_text                          # noqa: PLC0415
    return spec_text(row.get("at", ""), lines=lines)


def _registry_ids():
    """Every id the registry carries, read from it rather than restated.

    A list of families written into this file would be a second copy of
    `docs/spec/completion.yaml` and would drift from it -- the same reason
    `spec_text` reads a row from the annex instead of quoting it.
    """
    global _REG_IDS
    if _REG_IDS is None:
        ids = set()
        path = os.path.join(_ROOT, "docs", "spec", "completion.yaml")
        try:
            for ln in open(path, encoding="utf-8"):
                if re.match(r"^\s+- id: ", ln):
                    ids.add(ln.split("id:", 1)[1].strip())
        except OSError:                                      # pragma: no cover
            pass
        _REG_IDS = ids
    return _REG_IDS


def _norm_id(fam, num):
    if not num.isdigit():
        return "%s-%s" % (fam, num.upper())
    return "%s-%03d" % (fam, int(num))


def _ids_in(text):
    out = []
    for m in _ID.finditer(text):
        for part in m.group(2).split("/"):
            out.append(_norm_id(m.group(1), part))
    return out


_DIRS = ("station", "station/npc", "station/physics", "tools",
         "godot/scripts", "docs")


def _find_py(rel):
    """The file a `<path>.py:<line>` citation names.

    The annex writes some paths from the repo root (`npc/costume.py`) and some
    bare (`resident.py`, which is `station/npc/resident.py`; `starfury.gd`,
    which is `godot/scripts/`), so a resolver that only tried the literal path
    reported the bare ones as MISSING -- a parse failure dressed up as a
    finding, which is the thing this package exists to avoid. Tries the literal
    path under the repo root and under `station/`, then the basename in each
    directory the annex actually names things out of.
    """
    for c in (os.path.join(_ROOT, rel), os.path.join(_ROOT, "station", rel)):
        if os.path.exists(c):
            return c
    base = os.path.basename(rel)
    for d in _DIRS:
        c = os.path.join(_ROOT, d, base)
        if os.path.exists(c):
            return c
    return None


# `tools/measure_frame.py --gate-frames --rerender`, `npc/body.py
# --silhouette`, `tools/render_godot.sh + panel scoring`
_TOOL = re.compile(r"\b((?:[\w.\-]+/)*[\w.\-]+\.(?:py|sh|gd))"
                   r"((?:\s+--[\w\-]+)*)")


def check_tools(t, bad, note):
    """Every file the row names exists, and every flag it names is real.

    THE HARNESS LINE IS A CLAIM ABOUT A COMMAND, and this project's most
    expensive recurring defect is a gate that does not run. A row whose
    `harness:` field names `tools/x.py --flag` is asserting that command
    works; resolving the file and grepping its source for the literal flag
    costs one file read and catches the case where the flag moved to another
    tool -- which is what SUR-05 turned out to be.
    """
    seen = 0
    for m in _TOOL.finditer(t):
        rel, flags = m.group(1), m.group(2)
        path = _find_py(rel)
        if path is None:
            bad.append("names %s and no such file exists" % rel)
            continue
        seen += 1
        if not flags:
            continue
        src = open(path, encoding="utf-8", errors="replace").read()
        for f in flags.split():
            if f not in src:
                bad.append("names `%s %s` and %s contains no such flag"
                           % (rel, f, os.path.relpath(path, _ROOT)))
    for rel in re.findall(r"\b((?:[\w.\-]+/)+[\w.\-]+\.json)\b", t):
        if not os.path.exists(os.path.join(_ROOT, rel)):
            bad.append("names %s and no such file exists" % rel)
        else:
            seen += 1
    note.append("%d named file(s) resolve" % seen)


def _defs(path):
    """Module-level names in a file and the line each is defined on.

    A source scan and not an import, because the question is "where does this
    live in the file the citation points at", which an import cannot answer,
    and because several of the cited files are expensive to import.
    """
    if path not in _DEFS:
        out = {}
        try:
            for i, ln in enumerate(open(path, encoding="utf-8"), 1):
                if ln[:1] in (" ", "\t", "#", "\n"):
                    continue
                m = _DEF.match(ln)
                if m and m.group(1) not in out:
                    out[m.group(1)] = i
        except OSError:                                      # pragma: no cover
            pass
        _DEFS[path] = out
    return _DEFS[path]


def _names_stated(text):
    """UPPER_CASE names the row states, including the `A/B` contraction.

    `CREDIT_MIN/MAX` is one claim about two constants and a plain scan reads it
    as `CREDIT_MIN` and `MAX`; the second is expanded against the first's own
    prefix, which is the only form of it the annex uses.
    """
    out = []
    for m in _UPPER.finditer(text):
        name = m.group(1)
        out.append(name)
        tail = text[m.end():m.end() + 40]
        t = re.match(r"/([A-Z][A-Z0-9_]*)", tail)
        if t and "_" in name:
            out.append(name.rsplit("_", 1)[0] + "_" + t.group(1))
    return out


def _resolve_const(name, prefer):
    """(module_name, value) for a constant, or (None, None).

    `prefer` is the modules the row itself names, tried first; `_SEARCH` is the
    fallback. Imported one at a time so a row that states no constant imports
    nothing.
    """
    import importlib                                            # noqa: PLC0415
    for mod in list(prefer) + [m for m in _SEARCH if m not in prefer]:
        try:
            m = importlib.import_module(mod)
        except Exception:                                        # noqa: BLE001
            continue
        if hasattr(m, name):
            return mod, getattr(m, name)
    return None, None


def _val(lit):
    lit = lit.strip()
    if lit.startswith("("):
        return tuple(int(x) for x in re.findall(r"\d+", lit))
    if "/" in lit:
        a, b = lit.split("/")
        return float(a) / float(b)
    return float(lit)


def _num(text, pattern, what, bad):
    """A number read out of the ROW, or a MALFORMED failure.

    Every claim below takes its expected value from the annex rather than from
    a literal in this file, so the harness cannot drift from the row it checks.
    When the pattern misses, that is recorded as MALFORMED and not as a
    disagreement -- they are opposite findings and only one is about the
    station.
    """
    m = re.search(pattern, text)
    if not m:
        bad.append("MALFORMED: cannot read %s out of the row" % what)
        return None
    g = [x for x in m.groups() if x is not None]
    try:
        return float(g[0].replace(",", "")) if len(g) == 1 else \
            tuple(float(x.replace(",", "")) for x in g)
    except ValueError:                                       # pragma: no cover
        bad.append("MALFORMED: %s is not a number in the row" % what)
        return None


def _close(a, b, tol):
    return a is not None and abs(float(a) - float(b)) <= tol


_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
          "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
          "twelve": 12}


def _count(text, pattern, what, bad):
    """A count the row writes either as a numeral or as an English word.

    The annex does both -- `55.0 arrivals/day`, `**ten classes**`, `six
    standing atmospheres` -- and a parser that only read numerals reported
    three rows as MALFORMED, which is a fact about the parser and not about the
    station.
    """
    m = re.search(pattern, text)
    if not m:
        bad.append("MALFORMED: cannot read %s out of the row" % what)
        return None
    tok = m.group(1)
    if tok.isdigit():
        return int(tok)
    if tok.lower() in _WORDS:
        return _WORDS[tok.lower()]
    bad.append("MALFORMED: %s reads %r, which is not a count" % (what, tok))
    return None


def _flat(t):
    """The row on one line.

    The annex hard-wraps at about ninety columns, so `55.0\\narrivals/day` and
    `(90% of crime\\nin Downbelow` are two of its ordinary shapes and every
    phrase pattern below would miss them. Line structure is only needed by
    SYS-14's table, which gets the unflattened text.
    """
    return re.sub(r"\s+", " ", t)


# ===========================================================================
# The per-row claims. Each takes the row's text and appends to `bad`/`note`.
# ===========================================================================

def _c_sys01(t, bad, note, raw=""):
    from npc import costume as cos                              # noqa: PLC0415
    import broadcast as bc                                      # noqa: PLC0415
    n = _num(t, r"each of the (\d+)\s*`costume\.ERA_EVENTS`", "the era-event "
             "count", bad)
    if n is not None and len(cos.ERA_EVENTS) != int(n):
        bad.append("era events: row says %d, costume.ERA_EVENTS has %d"
                   % (n, len(cos.ERA_EVENTS)))
    b = _num(t, r"ISN bulletins \((\d+) era-keyed", "the bulletin count", bad)
    if b is not None and len(bc.ISN_BULLETINS) != int(b):
        bad.append("ISN bulletins: row says %d era-keyed, "
                   "broadcast.ISN_BULLETINS has %d" % (b, len(bc.ISN_BULLETINS)))
    note.append("%d era events, %d ISN bulletins" % (len(cos.ERA_EVENTS),
                                                     len(bc.ISN_BULLETINS)))


def _c_sys02(t, bad, note, raw=""):
    """The manifest, restated 1:1 -- which is what the row says it is."""
    import traffic as tr                                        # noqa: PLC0415
    code = {m[0]: m[1] for m in tr.MANIFEST}
    stated = {}
    for m in re.finditer(r"\b([a-z][a-z_]+)\s+(\d+(?:\.\d+)?)\b", t):
        if m.group(1) in code or m.group(1) in ("tanker",):
            stated[m.group(1)] = float(m.group(2))
    want_n = _count(t, r"\*\*(\w+) classes\*\*", "the class count", bad)
    if want_n is not None and len(tr.MANIFEST) != want_n:
        bad.append("manifest: row says %d classes, traffic.MANIFEST has %d"
                   % (want_n, len(tr.MANIFEST)))
    if len(stated) < 10:
        bad.append("MALFORMED: read %d of the row's per-class rates (%s)"
                   % (len(stated), sorted(stated)))
    for k, v in sorted(stated.items()):
        if k not in code:
            bad.append("class %s: the row restates it, traffic.MANIFEST has "
                       "no such class" % k)
        elif abs(code[k] - v) > 1e-9:
            bad.append("class %s: row %.4g/day, traffic.MANIFEST %.4g/day"
                       % (k, v, code[k]))
    tot = _num(t, r"(\d+\.\d+) arrivals/day exactly", "the daily total", bad)
    got = sum(m[1] for m in tr.MANIFEST)
    if tot is not None and abs(got - tot) > 1e-9:
        bad.append("arrivals/day: row says %.4g exactly, traffic.MANIFEST "
                   "sums to %.4g" % (tot, got))
    bays = _num(t, r"\((\d+) bays × A/B levels", "the bay count", bad)
    if bays is not None and tr.bay_count() != int(bays):
        bad.append("bays: row says %d, traffic.bay_count() is %d"
                   % (bays, tr.bay_count()))
    # `DAY_BANDS (peak-to-trough 3.12:1)` is the RAMPED curve's ratio, which is
    # what `traffic.report` prints; the bare band ratio is 3.125 and the stated
    # design figure `PEAK_TO_TROUGH` is 3.0. Compared against the same number
    # the module prints, at the precision the row quotes it to.
    p2t = _num(t, r"peak-to-trough ([\d.]+):1", "the peak-to-trough ratio", bad)
    pk = max(tr.day_curve(i / 60.0) for i in range(24 * 60))
    trough = min(tr.day_curve(i / 60.0) for i in range(24 * 60))
    if p2t is not None and not _close(p2t, pk / trough, 0.005):
        bad.append("peak-to-trough: row says %.3f:1, the ramped DAY_BANDS "
                   "curve gives %.4f:1 (traffic.PEAK_TO_TROUGH states %.2f)"
                   % (p2t, pk / trough, tr.PEAK_TO_TROUGH))
    phases = _num(t, r"(\d+)-phase docking state machine", "the phase count",
                  bad)
    chain = re.search(r"state machine per ship \(([^)]*)\)", t)
    if phases is not None and chain:
        beats = [b for b in re.split(r"→|->", chain.group(1)) if b.strip()]
        if len(beats) != int(phases):
            bad.append("docking: row says %d phases and its own chain lists "
                       "%d (%r)" % (phases, len(beats),
                                    [b.strip() for b in beats]))
    note.append("%d manifest classes summing %.1f/day, %d bays, "
                "peak-to-trough %.3f:1" % (len(tr.MANIFEST), got,
                                           tr.bay_count(), pk / trough))


def _c_sys03(t, bad, note, raw=""):
    """The ten stations, counted INSIDE the range the row cites for them."""
    import arrival as ar                                        # noqa: PLC0415
    import player as pl                                         # noqa: PLC0415
    n = _num(t, r"(\d+)-station pipeline", "the pipeline length", bad)
    m = re.search(r"\(arrival\.py:(\d+)-(\d+)\)", t)
    if n is not None and m:
        a, b = int(m.group(1)), int(m.group(2))
        src = open(os.path.join(_ROOT, "station", "arrival.py"),
                   encoding="utf-8").read().splitlines()
        nums = {int(x) for ln in src[a - 1:b]
                for x in re.findall(r"\brow\((\d+),", ln)}
        if len(nums) != int(n):
            bad.append("customs pipeline: row says %d stations, arrival.py:"
                       "%d-%d resolves %d distinct station numbers %s"
                       % (n, a, b, len(nums), sorted(nums)))
    for k in re.findall(r"`(secondary_inspection|customs_holding)`", t):
        if k not in ar.UNBUILT:
            bad.append("the row says `%s` is `built=False` in arrival.UNBUILT "
                       "and it is not in that table (%s)"
                       % (k, sorted(ar.UNBUILT)))
    ps = _num(t, r"P=(0\.\d+)/(0\.\d+)", "the contraband rates", bad)
    if ps is not None:
        for want, got, name in ((ps[0], ar.CONTRABAND_P, "CONTRABAND_P"),
                                (ps[1], ar.CONTRABAND_P_NO_STATUS,
                                 "CONTRABAND_P_NO_STATUS")):
            if abs(want - got) > 1e-9:
                bad.append("%s: row says %.4g, arrival.py has %.4g"
                           % (name, want, got))
    leak = _num(t, r"(\d+)%/day leak", "the leak rate", bad)
    if leak is not None and abs(pl.LEAK_RATE - leak / 100.0) > 1e-9:
        bad.append("leak: row says %g%%/day, player.LEAK_RATE is %g"
                   % (leak, pl.LEAK_RATE))
    floor = _num(t, r"(\d+) cr passage-home FLOOR", "the passage floor", bad)
    if floor is not None and abs(pl.PASSAGE_HOME_CR - floor) > 1e-9:
        bad.append("passage home: row says %g cr floor, player."
                   "PASSAGE_HOME_CR is %g" % (floor, pl.PASSAGE_HOME_CR))
    note.append("pipeline and both unbuilt rooms resolve; P=%g/%g, leak %g, "
                "passage %g cr" % (ar.CONTRABAND_P, ar.CONTRABAND_P_NO_STATUS,
                                   pl.LEAK_RATE, pl.PASSAGE_HOME_CR))


def _c_sys04(t, bad, note, raw=""):
    """The four prices the row quotes, against `economy.LADDER`."""
    import economy as ec                                        # noqa: PLC0415
    lad = {r[0]: (r[1], r[2], r[3], r[4]) for r in ec.LADDER}
    want = (("command quarters (\\d+) cr/wk", "quarters_command", "week"),
            ("cart meal (\\d+)-(\\d+) cr", "meal_cart", "each"),
            ("dock day-labour (\\d+)-(\\d+) cr", "labour_casual", "day"),
            ("dosshouse bunk (\\d+) cr/night", "bunk_dosshouse", "night"),
            ("passage home (\\d+)–(\\d+) cr", "passage_home", "each"))
    seen = 0
    for pat, key, unit in want:
        m = re.search(pat, t)
        if not m:
            bad.append("MALFORMED: the row does not quote %s in the form this "
                       "harness reads (%r)" % (key, pat))
            continue
        seen += 1
        if key not in lad:
            bad.append("economy.LADDER has no `%s` row" % key)
            continue
        lo, hi, u, _auth = lad[key]
        g = [float(x) for x in m.groups() if x is not None]
        wlo, whi = (g[0], g[0]) if len(g) == 1 else (g[0], g[1])
        if abs(lo - wlo) > 1e-9 or abs(hi - whi) > 1e-9 or u != unit:
            bad.append("%s: row %g-%g/%s, economy.LADDER %g-%g/%s"
                       % (key, wlo, whi, unit, lo, hi, u))
    # "the ONE auth-1 price" -- and the ladder marks its authorities, so the
    # claim that exactly one of them is sourced is itself checkable.
    a1 = [r[0] for r in ec.LADDER if r[4] == 1]
    if re.search(r"the ONE auth-1 price", t) and len(a1) != 1:
        bad.append("the row calls command quarters THE one auth-1 price and "
                   "economy.LADDER carries %d auth-1 rows %s" % (len(a1), a1))
    note.append("%d of 5 quoted prices matched economy.LADDER; auth-1 rows %s"
                % (seen, a1))


def _c_sys05(t, bad, note, raw=""):
    from npc import security as se                              # noqa: PLC0415
    import consequence as cq                                    # noqa: PLC0415
    n = _num(t, r"(\d+) officers / ~(\d+) on duty / (\d+) watches",
             "the force ladder", bad)
    if n is not None:
        if se.force_total() != int(n[0]):
            bad.append("force: row says %d officers, security.force_total() "
                       "is %d" % (n[0], se.force_total()))
        if se.GAZETTEER_CLAIMS["on_duty"] != int(n[1]):
            bad.append("on duty: row says ~%d, security.GAZETTEER_CLAIMS "
                       "carries %d" % (n[1], se.GAZETTEER_CLAIMS["on_duty"]))
    posted = _num(t, r"(\d+)\s*posted at the POSTS table", "the posted count",
                  bad)
    got = sum(p[1] for p in se.POSTS) * se.PATROL_UNIT
    if posted is not None and got != int(posted):
        bad.append("posted: row says %d, POSTS x PATROL_UNIT is %d"
                   % (posted, got))
    cells = _num(t, r"\((\d+)-(\d+) cells", "the brig cell band", bad)
    if cells is not None and (cq.BRIG_CELLS_LO, cq.BRIG_CELLS_HI) != \
            (int(cells[0]), int(cells[1])):
        bad.append("brig: row says %d-%d cells, consequence.py has %d-%d"
                   % (cells[0], cells[1], cq.BRIG_CELLS_LO, cq.BRIG_CELLS_HI))
    omb = _num(t, r"\((\d+) named ombudsmen", "the ombudsman count", bad)
    if omb is not None and cq.OMBUDSMEN != int(omb):
        bad.append("ombudsmen: row says %d, consequence.OMBUDSMEN is %d"
                   % (omb, cq.OMBUDSMEN))
    share = _num(t, r"\((\d+)% of crime in Downbelow", "the crime share", bad)
    if share is not None and abs(cq.DOWNBELOW_CRIME_SHARE - share / 100.0) > 1e-9:
        bad.append("Downbelow crime share: row says %g%%, consequence."
                   "DOWNBELOW_CRIME_SHARE is %g" % (share,
                                                    cq.DOWNBELOW_CRIME_SHARE))
    note.append("force %d, %d posted, brig %d-%d, %d ombudsmen, crime share "
                "%g; the 7-rung escalation ladder names no code object and is "
                "NOT checked" % (se.force_total(), got, cq.BRIG_CELLS_LO,
                                 cq.BRIG_CELLS_HI, cq.OMBUDSMEN,
                                 cq.DOWNBELOW_CRIME_SHARE))


def _c_sys06(t, bad, note, raw=""):
    from npc import schedule as sc                              # noqa: PLC0415
    from npc import security as se                              # noqa: PLC0415
    import directory as dr                                      # noqa: PLC0415
    n = _count(t, r"the route's (\w+) stations", "the route length", bad)
    if n is not None and len(se.BLACK_MARKET_ROUTE) != n:
        bad.append("black market route: the row says %d stations (twice -- "
                   "the State field and the CHECK), security."
                   "BLACK_MARKET_ROUTE has %d: %s"
                   % (n, len(se.BLACK_MARKET_ROUTE),
                      [r[0] for r in se.BLACK_MARKET_ROUTE]))
    # EITHER VOCABULARY, AND SECURITY.PY SAYS WHY. Its own selftest accepts a
    # route node that is a `schedule.PLACES` crowd REGION rather than a
    # `directory.PLACES` room -- "a bribed docker is a person in a district,
    # not a room you walk into" -- and `dock_workers_quarters` is one of the
    # eight names that exist only in the second vocabulary. A harness that
    # only knew the register would report that documented decision as a
    # defect, which is a finding about the harness.
    keys = {p["key"] for p in dr.PLACES}
    for k in re.findall(r"`([a-z][a-z_0-9]*)`\s+place exists", t):
        if k not in keys:
            bad.append("the row says `%s` exists and directory.PLACES has no "
                       "such key" % k)
    unknown = [r[0] for r in se.BLACK_MARKET_ROUTE
               if r[0] not in keys and r[0] not in sc.PLACES]
    if unknown:
        bad.append("route stations in neither directory.PLACES nor "
                   "schedule.PLACES: %s" % unknown)
    regions = [r[0] for r in se.BLACK_MARKET_ROUTE if r[0] not in keys]
    note.append("route %d stations, %d register rooms + %d crowd region(s) %s"
                % (len(se.BLACK_MARKET_ROUTE),
                   len(se.BLACK_MARKET_ROUTE) - len(regions), len(regions),
                   regions))


def _c_sys07(t, bad, note, raw=""):
    """The five headline flows, re-derived from the plant's own constants."""
    import plant_systems as ps                                  # noqa: PLC0415
    import alien_sector as al                                   # noqa: PLC0415
    head = ps.HEADCOUNT
    gw = _num(t, r"power \(≈([\d.]+) GW", "the power demand", bad)
    if gw is not None and not _close(gw, ps.POWER_TOTAL_MW / 1000.0, 0.05):
        bad.append("power: row says ~%g GW, plant_systems.POWER_TOTAL_MW is "
                   "%g MW" % (gw, ps.POWER_TOTAL_MW))
    w = _num(t, r"water \(([\d,]+) m³/day", "the water demand", bad)
    got_w = (ps.WATER_DRINK_L_HEAD_DAY + ps.WATER_HYGIENE_L_HEAD_DAY) \
        * head / 1000.0
    if w is not None and not _close(w, got_w, 1.0):
        bad.append("water: row says %g m3/day, (%g+%g) L/head x %d is %.1f"
                   % (w, ps.WATER_DRINK_L_HEAD_DAY,
                      ps.WATER_HYGIENE_L_HEAD_DAY, head, got_w))
    res = _num(t, r"(\d+)-day reserve", "the reserve", bad)
    if res is not None and abs(ps.WATER_RESERVE_DAYS - res) > 1e-9:
        bad.append("reserve: row says %g days, WATER_RESERVE_DAYS is %g"
                   % (res, ps.WATER_RESERVE_DAYS))
    o2 = _num(t, r"O₂ (\d+) t/d", "the oxygen flow", bad)
    got_o2 = ps.O2_KG_PER_HEAD_DAY * head / 1000.0
    if o2 is not None and not _close(o2, got_o2, 0.5):
        bad.append("oxygen: row says %g t/d, %g kg/head x %d is %.1f"
                   % (o2, ps.O2_KG_PER_HEAD_DAY, head, got_o2))
    wa = _num(t, r"waste \(([\d.]+) t/d", "the waste flow", bad)
    got_wa = ps.WASTE_SOLID_KG_HEAD_DAY * head / 1000.0
    if wa is not None and not _close(wa, got_wa, 0.1):
        bad.append("waste: row says %g t/d, %g kg/head x %d is %.1f"
                   % (wa, ps.WASTE_SOLID_KG_HEAD_DAY, head, got_wa))
    at = _num(t, r"(\w+) atmospheres held", "the atmosphere count", bad) \
        if re.search(r"\d+ atmospheres held", t) else None
    if at is None:
        m = re.search(r"(\w+) atmospheres held", t)
        at = {"six": 6, "five": 5, "seven": 7}.get(m.group(1)) if m else None
    if at is not None and al.atmospheres_available() != int(at):
        bad.append("atmospheres: row says %d held, alien_sector."
                   "atmospheres_available() is %d"
                   % (at, al.atmospheres_available()))
    note.append("power %.3f GW, water %.0f m3/d, O2 %.0f t/d, waste %.1f t/d, "
                "%d atmospheres; the three rosettes and the >98%% closure are "
                "prose in plant_systems and are NOT checked"
                % (ps.POWER_TOTAL_MW / 1000.0, got_w, got_o2, got_wa,
                   al.atmospheres_available()))


def _c_sys08(t, bad, note, raw=""):
    import broadcast as bc                                      # noqa: PLC0415
    want = re.search(r"PA\s*\n?schedule \(([^)]*)\)", t)
    kinds = {"port calls": "port_calls", "watch calls": "watch_calls",
             "civic calls": "civic_calls"}
    if not want:
        bad.append("MALFORMED: cannot read the PA schedule list out of the row")
    else:
        for phrase, fn in sorted(kinds.items()):
            if phrase in want.group(1) and not callable(getattr(bc, fn, None)):
                bad.append("the row says broadcast.py implements %s and it has "
                           "no `%s`" % (phrase, fn))
    n = _num(t, r"ISN bulletin queue \((\d+) era-keyed", "the bulletin count",
             bad)
    if n is not None and len(bc.ISN_BULLETINS) != int(n):
        bad.append("ISN bulletins: row says %d, broadcast.ISN_BULLETINS has %d"
                   % (n, len(bc.ISN_BULLETINS)))
    note.append("port/watch/civic calls all implemented, %d ISN bulletins"
                % len(bc.ISN_BULLETINS))


def _c_sys09(t, bad, note, raw=""):
    """Four timetables, the shuttle's own axis, and the two journey times."""
    import interior as it                                       # noqa: PLC0415
    import transit as tt                                        # noqa: PLC0415
    schema, profile = it.load()
    lines = {L["key"]: L for L in tt.all_lines(schema, profile)}
    n = _num(t, r"core shuttle (\d+) stops / drum tram (\d+) / ground tram "
                r"(\d+) / spoke lifts (\d+) lines", "the four timetables", bad)
    if n is not None:
        for want, key, field in ((n[0], "core_shuttle", "stops"),
                                 (n[1], "guideway_tram", "stops"),
                                 (n[2], "ground_tram", "stops"),
                                 (n[3], "spoke_lift", "lines")):
            got = lines[key][field]
            if got != int(want):
                bad.append("%s: row says %d %s, transit gives %d"
                           % (key, want, field, got))
    z = _num(t, r"runs z ([\d,]+)–([\d,]+) \(([\d,]+) m, stops @([\d.]+) m\)",
             "the shuttle axis", bad)
    if z is not None:
        cs = lines["core_shuttle"]
        span = cs["z1"] - cs["z0"]
        pitch = span / (cs["stops"] - 1)
        for want, got, name in ((z[0], cs["z0"], "z0"), (z[1], cs["z1"], "z1"),
                                (z[2], span, "span"), (z[3], pitch, "spacing")):
            if not _close(want, got, 0.51):
                bad.append("core shuttle %s: row %g, transit %g"
                           % (name, want, got))
    # The honest-signage claim, which is the one a player can catch us on.
    j = _num(t, r"walks faster than the shuttle \((\d+)m(\d+)s vs (\d+)m(\d+)s",
             "the two journey times", bad)
    if j is not None:
        js, _reps = tt.journeys(schema, profile)
        by = {x["name"]: x["seconds"] for x in js}
        foot = by.get("Blue docking bays -> the Zocalo, on foot")
        ride = by.get("Blue docking bays -> the Zocalo, by core shuttle")
        if foot is None or ride is None:
            bad.append("transit.journeys names no docking-bays -> Zocalo pair "
                       "(%s)" % sorted(by))
        else:
            for want, got, name in ((j[0] * 60 + j[1], foot, "on foot"),
                                    (j[2] * 60 + j[3], ride, "by shuttle")):
                if not _close(want, got, 0.51):
                    bad.append("bays->Zocalo %s: row %dm%02ds, transit %dm%02ds"
                               % (name, want // 60, want % 60,
                                  int(got) // 60, int(got) % 60))
            if foot >= ride:
                bad.append("the row's whole point is that walking is faster "
                           "and transit gives foot %.0f s vs shuttle %.0f s"
                           % (foot, ride))
    note.append("4 timetables, shuttle z%.0f-%.0f @%.1f m, bays->Zocalo "
                "%.0f s on foot vs %.0f s riding; the 70 shafts appear in no "
                "module and are NOT checked"
                % (lines["core_shuttle"]["z0"], lines["core_shuttle"]["z1"],
                   (lines["core_shuttle"]["z1"] - lines["core_shuttle"]["z0"])
                   / (lines["core_shuttle"]["stops"] - 1),
                   *[x["seconds"] for x in tt.journeys(schema, profile)[0]
                     if x["name"].startswith("Blue docking bays")]))


def _c_sys10(t, bad, note, raw=""):
    from npc import schedule as sc                              # noqa: PLC0415
    import alien_sector as al                                   # noqa: PLC0415
    n = _num(t, r"\(([\d,]+) medical role-holders exist in the data\)",
             "the medical headcount", bad)
    got = sc.ROLE_WEIGHTS["human"].get("medical")
    if n is not None and got != int(n):
        bad.append("medical staff: row says %d in the data, schedule."
                   "ROLE_WEIGHTS['human']['medical'] is %s" % (n, got))
    at = re.search(r"\(?(six|five|seven) atmospheres are real barriers", t)
    if at:
        want = {"five": 5, "six": 6, "seven": 7}[at.group(1)]
        if al.atmospheres_available() != want:
            bad.append("atmospheres: row says %d are real barriers, "
                       "alien_sector.atmospheres_available() is %d"
                       % (want, al.atmospheres_available()))
    note.append("%s medical role-holders, %d atmospheres; the condition model "
                "is auth-5 and unimplemented, so nothing here checks it"
                % (got, al.atmospheres_available()))


def _c_sys11(t, bad, note, raw=""):
    import alien_sector as al                                   # noqa: PLC0415
    import directory as dr                                      # noqa: PLC0415
    m = re.search(r"(six|five|seven) standing atmospheres", t)
    if not m:
        bad.append("MALFORMED: cannot read the atmosphere count out of the row")
    else:
        want = {"five": 5, "six": 6, "seven": 7}[m.group(1)]
        if al.atmospheres_available() != want:
            bad.append("atmospheres: row says %d standing, alien_sector."
                       "atmospheres_available() is %d"
                       % (want, al.atmospheres_available()))
    # `atmosphere_containment`/`sealed_environment` are the register's own
    # function names and the CHECK field is stated over them, so a rename that
    # emptied the set would make the check vacuous.
    fns = set()
    for p in dr.PLACES:
        fns.update(p.get("functions") or ())
    for f in re.findall(r"`(atmosphere_containment|sealed_environment)`", t):
        if f not in fns:
            bad.append("the CHECK is stated over every `%s` place and no "
                       "register row carries that function" % f)
    n = sum(1 for p in dr.PLACES
            if {"atmosphere_containment", "sealed_environment"}
            & set(p.get("functions") or ()))
    note.append("%d atmospheres, %d places carry a containment function"
                % (al.atmospheres_available(), n))


def _c_sys14(t, bad, note, raw=""):
    """The class table, and the row disagrees with itself about its size."""
    import incident as inc                                      # noqa: PLC0415
    # The table is the one part of a SYS row that needs its line structure, so
    # this claim reads `raw` where the others read the flattened text.
    rows = [ln for ln in raw.splitlines() if re.match(r"^\|\s*INC-", ln)]
    stated = [int(x) for x in re.findall(r"the (\d+)-(?:class|row) union", t)]
    if not stated:
        bad.append("MALFORMED: the row states no union size")
    for s in sorted(set(stated)):
        if s != len(rows):
            bad.append("union size: the row says %d and its own table is %d "
                       "rows (it states %s in different places)"
                       % (s, len(rows), sorted(set(stated))))
    if len(rows) != len(inc.CLASSES):
        bad.append("the table is %d rows and incident.CLASSES has %d classes"
                   % (len(rows), len(inc.CLASSES)))
    ids = {re.match(r"^\|\s*(INC-[A-Z]+)", ln).group(1) for ln in rows}
    missing = sorted(ids - set(inc.BY_ID))
    extra = sorted(set(inc.BY_ID) - ids)
    if missing or extra:
        bad.append("table vs incident.BY_ID: table-only %s, code-only %s"
                   % (missing, extra))
    note.append("%d table rows, %d incident classes, ids agree"
                % (len(rows), len(inc.CLASSES)))


def _c_sys15(t, bad, note, raw=""):
    """Every venue the calendar names is booked by a rule, both ways.

    `civic_calendar.py` reads SYS-15's own text for its venue list, so the
    strong question is not whether the ids resolve -- the reference check above
    already asks that -- but whether the module that implements the row covers
    every venue the row names AND names no venue the row does not. A rule for a
    place the spec never asked for is the same defect as a spec venue nothing
    books, and only a two-way comparison catches both.
    """
    import civic_calendar as cc                                 # noqa: PLC0415
    ids = set(cc.spec_plc_ids())
    mine = {i for i in _ids_in(t) if i.startswith("PLC-")}
    if ids != mine:
        bad.append("MALFORMED: this harness reads %d PLC ids out of the row "
                   "and civic_calendar.spec_plc_ids() reads %d (%s)"
                   % (len(mine), len(ids),
                      sorted(mine ^ ids)))
    idx = cc.plc_index()
    unresolved = sorted(i for i in ids if i not in idx)
    if unresolved:
        bad.append("names %s, which resolve to no register place" % unresolved)
    covered = set()
    for r in cc.RULES:
        covered |= set(r.plc)
    if ids - covered:
        bad.append("venues the row names that no civic_calendar rule books: %s"
                   % sorted(ids - covered))
    if covered - ids:
        bad.append("civic_calendar books %s, which SYS-15 does not name"
                   % sorted(covered - ids))
    note.append("%d named venues, %d rules, coverage exact in both directions"
                % (len(ids), len(cc.RULES)))


CLAIMS = {
    "SYS-001": _c_sys01, "SYS-002": _c_sys02, "SYS-003": _c_sys03,
    "SYS-004": _c_sys04, "SYS-005": _c_sys05, "SYS-006": _c_sys06,
    "SYS-007": _c_sys07, "SYS-008": _c_sys08, "SYS-009": _c_sys09,
    "SYS-010": _c_sys10, "SYS-011": _c_sys11, "SYS-014": _c_sys14,
    "SYS-015": _c_sys15,
}

# Rows with no per-row claim, and the reason each one has none. Printed in the
# note so a pass is never read as "this row was checked and is fine".
NO_CLAIM = {
    "SYS-012": "the K=3 memory bound and the per-topic pool floors are auth-5 "
               "targets with no implementation to compare against",
    "SYS-013": "persistence has no save format yet; every claim is a "
               "save/reload delta",
    "SYS-016": "knowledge facts have no module; the whole row is tool-to-build",
}


# ===========================================================================


def check(row):
    from spec_harness import spec_text                          # noqa: PLC0415
    rid = row.get("id", "")
    t = _text(row)
    if not t:
        return False, "cannot read the row's own text from %r" % row.get("at")
    head = t.splitlines()[0].strip()
    if not re.match(r"^#+\s*%s\b" % rid.split("-")[0] + r"-\d+", head):
        return False, "%s: the heading at %s is %r, which is not a %s row" % (
            rid, row.get("at"), head[:60], rid.split("-")[0])
    bad, note = [], []

    # -- the annex's own format law ----------------------------------------
    labels = {m.group("lab").strip().lower() for m in _FIELD.finditer(t)}
    miss = [f for f in _REQUIRED if f not in labels]
    if miss:
        bad.append("format law: no %s field (has %s)"
                   % (", ".join(miss), sorted(labels)))
    if not _HARNESS.search(t):
        bad.append("format law: no harness line")

    # -- citations, and containment is what makes them a claim -------------
    mods_named = set(_MODPY.findall(t))
    for m in _CIT.finditer(t):
        rel, a = m.group(1), int(m.group(2))
        b = int(m.group(3) or m.group(2))
        path = _find_py(rel)
        if path is None:
            bad.append("cites %s and no such file exists" % m.group(0))
            continue
        n = len(open(path, encoding="utf-8").read().splitlines())
        if b > n:
            bad.append("cites %s and %s is %d lines"
                       % (m.group(0), os.path.relpath(path, _ROOT), n))
            continue
        # THE SYMBOL HAS TO BE NEAR THE CITATION, and the window is measured
        # rather than chosen. A row names several modules and several
        # constants; scoping containment to every name in the row made
        # SYS-02's `traffic.py:132-142` answer for `DAY_BANDS`, which it
        # never claimed to (they are 400 characters apart, under different
        # clauses). Every citation the annex writes sits within about twenty
        # characters of the name it is a citation FOR -- `CREDIT_MIN/MAX
        # exist, player.py:140-174` -- so the window is generous at 140 and
        # still excludes the next clause.
        near = _flat(t[max(0, m.start() - 140):m.end() + 140])
        defs = _defs(path)
        for name in set(_names_stated(near)):
            if name in defs and not (a <= defs[name] <= b):
                bad.append("cites %s for %s and %s defines it at line %d"
                           % (m.group(0), name,
                              os.path.relpath(path, _ROOT), defs[name]))
    for m in _GAZ.finditer(t):
        stem = m.group(1)
        hit = [f for f in os.listdir(os.path.join(_ROOT, "docs", "gazetteer"))
               if f.startswith(stem)]
        if not hit:
            bad.append("cites %s and docs/gazetteer has no such document"
                       % m.group(0))
            continue
        n = len(open(os.path.join(_ROOT, "docs", "gazetteer", hit[0]),
                     encoding="utf-8").read().splitlines())
        if int(m.group(3) or m.group(2)) > n:
            bad.append("cites %s and %s is %d lines" % (m.group(0), hit[0], n))

    # -- every id the row couples to ---------------------------------------
    reg = _registry_ids()
    dangling = sorted({i for i in _ids_in(t) if i != rid and i not in reg
                       and not i.startswith("INC-")})
    if dangling:
        bad.append("couples to %s, which the registry has no row for"
                   % dangling)
    conflicts = open(os.path.join(_ROOT, "canon", "CONFLICTS.md"),
                     encoding="utf-8").read()
    for c in sorted(set(_CONFLICT.findall(t))):
        if "C-%s" % c not in conflicts:
            bad.append("names C-%s and canon/CONFLICTS.md has no such entry" % c)
    inv = None
    for m in _INV.finditer(t):
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        if inv is None:
            inv = open(os.path.join(_ROOT, "canon", "INVENTIONS.md"),
                       encoding="utf-8").read()
        for k in range(lo, hi + 1):
            if "INV-%03d" % k not in inv:
                bad.append("names INV-%03d and canon/INVENTIONS.md has no "
                           "such entry" % k)
    ts = None
    for sc in sorted(set(_SPECCHANGE.findall(t))):
        if ts is None:
            ts = open(os.path.join(_ROOT, "docs", "THE-STATION.md"),
                      encoding="utf-8").read()
        if "SPEC-CHANGE #%s" % sc not in ts:
            bad.append("names SPEC-CHANGE #%s and docs/THE-STATION.md does "
                       "not carry it" % sc)

    # -- constants the row states with a value -----------------------------
    for m in _CONST.finditer(t):
        name, lit = m.group(1), m.group(2)
        want = _val(lit)
        mod, got = _resolve_const(name, sorted(mods_named))
        if mod is None:
            bad.append("states %s=%s and no module this row names, nor any in "
                       "the search list, defines it" % (name, lit))
            continue
        try:
            same = (tuple(got) == want if isinstance(want, tuple)
                    else abs(float(got) - want) <= 1e-9)
        except (TypeError, ValueError):                      # pragma: no cover
            same = False
        if not same:
            bad.append("%s: row says %s, %s has %r" % (name, lit, mod, got))

    # -- the files and flags the row names, harness line included ----------
    check_tools(t, bad, note)

    # -- the per-row claim, which is where the content is ------------------
    fn = CLAIMS.get(rid)
    if fn is not None:
        fn(_flat(t), bad, note, t)
    elif rid in NO_CLAIM:
        note.append("NO CONTENT CLAIM: %s" % NO_CLAIM[rid])
    else:
        note.append("NO CONTENT CLAIM for this row")

    if bad:
        return False, "%s: %s" % (rid, "; ".join(bad))
    return True, "%s: %s" % (rid, "; ".join(note) if note else "address only")


# ===========================================================================
# The controls, and they are IN the module because a control kept in a
# scratch file is a control nobody runs again. `fac.py` established the
# spec-side half of this pattern; the code-side half is added here because
# half of what a SYS row claims is a number in a module, and corrupting the
# annex cannot test whether the harness is really asking the station.
# ===========================================================================

_SPEC = "docs/spec/SYSTEMS.md"

# (label, row, find, replace, expected outcome after the edit)
# A row that PASSES today is broken and must FAIL; a row that FAILS today is
# corrected and must PASS. Both directions, because a check that only ever
# fails is as useless as one that only ever passes.
_SPEC_CONTROLS = (
    ("citation", "SYS-004", "player.py:140-174", "player.py:186-196", True),
    ("route", "SYS-006", "the route's five stations",
     "the route's six stations", True),
    ("format", "SYS-010", "**Couples to:** SYS-11 locks",
     "**Tick:** none\n**Couples to:** SYS-11 locks", True),
    ("manifest", "SYS-002", "shuttle 12 ·", "shuttle 13 ·", False),
    ("total", "SYS-002", "55.0\narrivals/day", "56.0\narrivals/day", False),
    ("bays", "SYS-002", "(24 bays × A/B", "(25 bays × A/B", False),
    ("phases", "SYS-002", "8-phase docking", "9-phase docking", False),
    ("pipeline", "SYS-003", "10-station pipeline", "11-station pipeline",
     False),
    ("price", "SYS-004", "cart meal 1-2 cr", "cart meal 1-3 cr", False),
    ("force", "SYS-005", "500 officers", "600 officers", False),
    ("cells", "SYS-005", "(24-40 cells", "(24-44 cells", False),
    ("water", "SYS-007", "water (13,250 m³/day", "water (14,250 m³/day",
     False),
    ("stops", "SYS-009", "core shuttle 13 stops", "core shuttle 14 stops",
     False),
    ("axis", "SYS-009", "z 3,397–8,047", "z 3,397–8,048", False),
    ("journey", "SYS-009", "(6m38s vs 10m32s)", "(6m39s vs 10m32s)", False),
    # THE ANNEX WRAPS MID-CLAIM and an anchor has to survive that: "(2,800\n
    # medical role-holders" is one sentence over two lines, so the anchor is
    # the part of it that is on one line. The selftest reports an anchor that
    # matches zero or several times as a DEAD CONTROL rather than passing it,
    # which is how this one was found.
    ("medical", "SYS-010", "medlab staffing (2,800",
     "medlab staffing (2,900", False),
    # This one moves for a second-order reason and it is worth stating:
    # `civic_calendar.spec_plc_ids()` reads the REAL annex, not the copy, so
    # renaming a venue in the copy makes the two readers disagree and the
    # harness says so. The coverage arm of the same check is exercised by the
    # code-side control below, which removes PLC-067's only booker.
    ("venue", "SYS-015", "PLC-067", "PLC-077", False),
    ("reference", "SYS-016", "ROLE-10's four buyers", "ROLE-99's four buyers",
     False),
    ("invention", "SYS-013", "PLY-03's class", "PLY-93's class", False),
)


def _code_controls():
    """One number moved in the station, per check that passes on it.

    Returns (label, row, patch, unpatch) tuples. These are the ones that
    matter most: they ask whether the harness is reading the station at all,
    which no amount of corrupting the annex can answer.
    """
    import civic_calendar as cc                                 # noqa: PLC0415
    import plant_systems as ps                                  # noqa: PLC0415
    import traffic as tr                                        # noqa: PLC0415
    import transit as tt                                        # noqa: PLC0415
    from npc import security as se                              # noqa: PLC0415

    man, posts = tr.MANIFEST, se.POSTS
    hyg, rules, jour = ps.WATER_HYGIENE_L_HEAD_DAY, cc.RULES, tt.journeys

    def _slow(schema, profile):
        js, reps = jour(schema, profile)
        for x in js:
            if x["name"].startswith("Blue docking bays -> the Zocalo, on"):
                x["seconds"] = 999.0
        return js, reps

    return (
        ("traffic.MANIFEST shuttle 12.0 -> 12.1/day", "SYS-002",
         lambda: setattr(tr, "MANIFEST", tuple(
             ("shuttle", 12.1) + m[2:] if m[0] == "shuttle" else m
             for m in man)),
         lambda: setattr(tr, "MANIFEST", man)),
        ("security.POSTS: the Zocalo loses a pair", "SYS-005",
         lambda: setattr(se, "POSTS", tuple(
             (p[0], p[1] - 1) + p[2:] if p[0] == "zocalo" else p
             for p in posts)),
         lambda: setattr(se, "POSTS", posts)),
        ("plant_systems: hygiene water 50 -> 45 L/head/day", "SYS-007",
         lambda: setattr(ps, "WATER_HYGIENE_L_HEAD_DAY", 45.0),
         lambda: setattr(ps, "WATER_HYGIENE_L_HEAD_DAY", hyg)),
        ("transit: the walk to the Zocalo takes 16m39s", "SYS-009",
         lambda: setattr(tt, "journeys", _slow),
         lambda: setattr(tt, "journeys", jour)),
        # R-LESSON IS THE CONTROL AND R-WEDDING IS NOT, which had to be
        # measured: dropping R-WEDDING changes nothing because PLC-053 is
        # still booked by R-FESTIVAL, R-MINIPAX and R-RECEPTION, and the
        # check is RIGHT to say so. A control has to remove the last booker
        # of a venue to be a control at all.
        ("civic_calendar: PLC-067's only booker removed", "SYS-015",
         lambda: setattr(cc, "RULES",
                         tuple(r for r in rules if r.rid != "R-LESSON")),
         lambda: setattr(cc, "RULES", rules)),
    )


def _rows(fam="SYS"):
    reg = open(os.path.join(_ROOT, "docs/spec/completion.yaml"),
               encoding="utf-8").read()
    return [{"id": m.group(1), "at": m.group(2)} for m in
            re.finditer(r"- id: (%s-\d+)\n\s+at: (\S+)" % fam, reg)]


def _selftest(out=print):                                    # pragma: no cover
    import tempfile
    rows = _rows("SYS")
    out("THE SIXTEEN SYSTEMS -- docs/spec/SYSTEMS.md against the code")
    npass = 0
    for row in rows:
        ok, note = check(row)
        npass += ok
        out("  %s %s" % ("PASS" if ok else "FAIL", note[:200]))
    out("  -- %d of %d rows agree with the code" % (npass, len(rows)))

    base = open(os.path.join(_ROOT, _SPEC), encoding="utf-8").read()
    at_of = {r["id"]: r["at"] for r in rows}
    tmp = os.path.join(tempfile.mkdtemp(prefix="sys-controls-"), "SYSTEMS.md")
    dead = []
    out("\nSPEC-SIDE CONTROLS -- one claim changed each, in a copy")
    for label, rid, old, new, want_fail in _SPEC_CONTROLS:
        if base.count(old) != 1:
            dead.append("%s: its anchor %r appears %d times in the annex"
                        % (label, old, base.count(old)))
            continue
        open(tmp, "w", encoding="utf-8").write(base.replace(old, new))
        ok, note = check({"id": rid, "at": "%s:%s"
                          % (tmp, at_of[rid].split(":")[1])})
        fired = (not ok) if want_fail is False else ok
        out("  %-10s %s %-14s %s" % (label, rid,
                                     "MOVES" if fired else "DOES NOT MOVE",
                                     note[:110]))
        if not fired:
            dead.append("%s on %s did not move the answer" % (label, rid))

    out("\nCODE-SIDE CONTROLS -- one number moved in the station")
    for label, rid, patch, unpatch in _code_controls():
        row = {"id": rid, "at": at_of[rid]}
        before = check(row)[0]
        patch()
        try:
            after = check(row)
        finally:
            unpatch()
        out("  %s %-46s %s" % (rid, label[:46],
                               "FIRES" if before and not after[0]
                               else "DEAD"))
        if not (before and not after[0]):
            dead.append("%s: %s did not turn a PASS into a FAIL"
                        % (rid, label))
        else:
            out("      %s" % after[1][:150])
    for d in dead:
        out("  DEAD CONTROL %s" % d)
    n = len(_SPEC_CONTROLS) + len(_code_controls())
    out("\n%d of %d controls move the answer" % (n - len(dead), n))
    return not dead


if __name__ == "__main__":                                   # pragma: no cover
    import sys as _s
    # Run directly, the way a person checks a harness. Imported through
    # `spec_check.py` the path is already set; here it is not, and `station/`
    # is what both `directory` and the `spec_harness` package hang off.
    _s.path.insert(0, os.path.join(_ROOT, "station"))
    _s.exit(0 if _selftest() else 1)
