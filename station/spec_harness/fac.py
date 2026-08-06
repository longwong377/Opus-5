"""FAC rows: the 28 faction blocks of `docs/spec/PEOPLE.md` §1 against the code.

WHAT A FAC ROW IS, AND THEREFORE WHAT CAN BE CHECKED. Every block is seven
labelled clauses -- **Numbers**, **Territory**, **Hours**, **Frictions**,
**Incidents**, **Standing**, **ACCEPT** -- and the first four are dense with
things the code ALSO states, in its own vocabulary, so a disagreement is a
finding rather than an opinion:

    "120 command-role heads"          `schedule.role_headcount()["command"]`
    "12,500" under ### FAC-13         `faction.head_count("FAC-13")`
    "`law_courts`, ... `minipax`"     `faction.BY_ID[fid]` territory, itself
                                      asserted against `directory.PLACES`
    "medium (PAIRS `narn/command`)"   `friction.PAIRS` -- row AND severity
    "ceremonial 6.0x = 2.70 m"        `friction.SEVERITY` x `BASE_SEPARATION_M`
    "semi-covert from (3,1)"          `costume.ERA_EVENTS["rangers_visible"]`
    "PSI_LICENSED_ABOARD=25"          `resident.PSI_LICENSED_ABOARD`
    "22,500 = 30 + 6,000 + 13,000 + 2,470 + 1,000"   the row's own arithmetic

None of that is restated here. Every expected value is a call into the module
that owns it, so this harness cannot drift from the station -- only from the
spec, which is the disagreement it exists to report.

HOW THE EXTRACTORS WERE BUILT, because rule 2 of the brief is the one that is
easy to violate quietly. The regexes below were written AFTER counting the
shapes in all 28 rows, not tuned until the numbers improved. Three examples of
what that turned up and what was done about it:

  * `-role heads` appears in THREE orders -- "120 command-role heads" (FAC-02),
    "cleric-role heads 7,300" (FAC-26) and "customs 900-role heads" (FAC-01).
    All three are matched; none is dropped.
  * a backticked snake_case token is USUALLY a place key (69 of the 74 distinct
    backticked tokens in the family) and sometimes a code symbol
    (`role_on_duty`), an era event (`rangers_visible`), a friction row
    (`narn/command`), a glob (`waste_*`) or an address (`grey/0`). Every one of
    those forms resolves through a named branch and an UNRESOLVED token is a
    FAILURE -- because "I cannot read this" must never be silent.
  * `**Numbers` is not always followed by `:**` -- FAC-12 writes
    `**Numbers (the PLC-021 ruling, auth 5 ...):**`. A regex demanding `:**`
    lost that row's whole paragraph.

SUFFICIENT = False, AND THE REASON IS THE ROW'S OWN LAST CLAUSE. Every FAC
block ends in an **ACCEPT** that is a scene: *"stand at the muster point
05:50-06:10: the caller works the board, names gangs against that day's actual
manifest ships, carded crews clear first, and >=1 casual is turned away toward
Downbelow"*. That is settled by a running station with a clock in it, and this
harness is a sub-second smoke check that imports data modules. It checks the
row's NUMBERS, TERRITORY, FRICTIONS and ERA GATE -- the half that is data --
and says so; it cannot see a caller work a board. A GREEN here would assert
the faction is arithmetically real, not that it is playable, so nothing here
may return a GREEN at all.
"""
import os
import re

SUFFICIENT = False

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Shapes, measured over the 28 rows before being written.
# ---------------------------------------------------------------------------
_HEAD = re.compile(r"^#+\s*(FAC-\d+)\s*[-—–]\s*(.+?)\s*$")
# `**Numbers:**` and `**Numbers (the PLC-021 ruling ...):**` -- FAC-12 is the
# second form and a pattern that demands the colon immediately loses it.
_NUMS = re.compile(r"\*\*Numbers[^*]*\*\*(.*?)(?=\*\*(?:Territory|Hours|Friction))",
                   re.S)
_TERR = re.compile(r"\*\*Territory:?\*\*(.*?)(?=\*\*(?:Hours|Friction|Incident))",
                   re.S)
# three orders, all three live in the family
_HEADS_NR = re.compile(r"([\d,]+)\s+([a-z']+)-role heads")
_HEADS_RN = re.compile(r"([a-z']+)-role heads\s+([\d,]+)")
_HEADS_RNR = re.compile(r"([a-z']+)\s+([\d,]+)-role heads")
_TOKEN = re.compile(r"`([^`]+)`")
_CONST = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\s*=\s*([\d]+(?:\.\d+)?(?:\s*/\s*[\d]+(?:\.\d+)?)?)")
# `security.py:105` and `resident.py:519–529` -- THE RANGE MATTERS. `ISN_PLACES`
# is cited as `broadcast.py:65–89` and lives at line 81, so a check that read
# only the first number would call a correct citation stale by 16 lines.
_CITE = re.compile(r"\b([a-z_]+\.py):(\d+)(?:\s*[–—-]\s*(\d+))?")
# a bare code symbol, NOT in backticks: `ISN_PLACES roster (broadcast.py:65–89)`
# and `broadcast.SENSOR_SWEEP`. The underscore is what makes this safe -- it
# excludes ISN, EA, PA, HIVE, LOOK, SYS-05, CAST-01, PLC-021 and every other
# capitalised thing in the family that is prose or an ID rather than a name.
_CAPS = re.compile(r"\b(?:([a-z_]+)\.)?([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)\b")
_RANGE = re.compile(r"(?<![:\d])([\d,]{2,})\s*[–—-]\s*([\d,]{2,})(?!\s*%)")
_EXACT = re.compile(r"(?<![\d.,:])([\d,]{2,})(?![\d,]*\s*%)")
_EPISODE = re.compile(r"\((\d),\s*(\d+)\)")
_SEP_M = re.compile(r"([\d.]+)\s*m separation")
_EVENTS_H = re.compile(r"([\d.]+)\s*events?/h")
_LADDER = re.compile(r"\b([a-z][a-z-]+)\s+([\d.]+)\s*[×x]\s*=\s*([\d.]+)\s*m")
_SUM = re.compile(r"([\d,]{2,})\s*=\s*([^(;—]*\+[^(;—]*)")
_APPROX = re.compile(r"^~([\d,]+)\b")
_MISSIONS = re.compile(r"\b(nine|NINE|ten|TEN|eleven|\d+)\s+staffed missions")
# the **Hours** clause of a species faction, against `schedule.RHYTHMS`
_SLEEP = re.compile(r"sleep\s+(\d{1,2}:\d{2})\s*[–—-]\s*(\d{1,2}:\d{2})")
_MEALS = re.compile(r"meals?\s+((?:\d{1,2}:\d{2}(?:\s*(?:,|and)\s*)?)+)")
_JITTER = re.compile(r"jitter\s+([\d.]+)")
_SECLUSION = re.compile(r"(\d+)\s*h seclusion")
_CLOCK = re.compile(r"(\d{1,2}):(\d{2})")
_WORDNUM = {"nine": 9, "ten": 10, "eleven": 11}
_SEVERITY_WORDS = ("highest", "high", "medium-high", "medium", "low",
                   "ceremonial", "episodic", "latent")

# what counts as evidence ABOUT THE STATION rather than about the row's own
# address. A row with none of these checked nothing and must not pass.
_SUBSTANTIVE = ("heads", "census", "territory", "friction", "ladder", "era",
                "const", "sum", "missions", "approx", "flag", "rhythm")


def _n(s):
    return int(str(s).replace(",", "").strip())


def _flat(text):
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# A module-level symbol index over station/, built once and cached.
#
# WHY STATIC AND NOT `getattr`. The spec cites symbols across a dozen modules
# and several of them (`arrival`, `broadcast`, `traffic`) are not otherwise
# needed here; importing a dozen modules to answer "is this name defined"
# would make a sub-second harness a second-and-a-half one and would import
# whatever those modules import. A scan of the source answers the same
# question and also gives the DEFINITION LINE, which is what makes the spec's
# own `security.py:105` citations checkable.
# ---------------------------------------------------------------------------
_SYMS = None
_STRINGS = None
# `EA_CITIZEN, RESIDENT, TRANSIT, SANCTUARY, NO_STATUS = (...)` is one line
# defining five names (arrival.py:387), and a pattern that only saw the first
# name before a `=` saw none of them, because the first name is followed by a
# comma. Tuple assignment is matched and every name on the left is registered.
_DEF = re.compile(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)|"
                  r"^([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)"
                  r"\s*(?::[^=]+)?=(?!=)")


def _index():
    """{symbol: [(module_path, line, rhs_text)]} plus the set of all string
    literals appearing anywhere in station/, which is how a data KEY
    (`breather_dispenser` is an entry in `directory.PLACES`' interacts tuple,
    not a definition) resolves."""
    global _SYMS, _STRINGS
    if _SYMS is not None:
        return _SYMS, _STRINGS
    syms, strings = {}, set()
    base = os.path.join(_ROOT, "station")
    files = [os.path.join(base, f) for f in sorted(os.listdir(base))
             if f.endswith(".py")]
    npc = os.path.join(base, "npc")
    files += [os.path.join(npc, f) for f in sorted(os.listdir(npc))
              if f.endswith(".py")]
    for path in files:
        try:
            src = open(path, encoding="utf-8").read()
        except OSError:                                      # pragma: no cover
            continue
        rel = os.path.basename(path)
        for i, ln in enumerate(src.splitlines(), 1):
            m = _DEF.match(ln)
            if m:
                rhs = ln.split("=", 1)[1] if "=" in ln and m.group(2) else ""
                for name in (m.group(1) or m.group(2)).split(","):
                    syms.setdefault(name.strip(), []).append((rel, i, rhs))
        strings.update(re.findall(r"['\"]([^'\"\\\n]{3,60})['\"]", src))
    _SYMS, _STRINGS = syms, strings
    return _SYMS, _STRINGS


def _literal(rhs):
    """The numeric value of a module-level RHS, or None.

    Arithmetic only, and deliberately: `NIGHTWATCH_SHARE = 175.0 / 500.0` is
    the shape the spec quotes as `175/500`, and comparing the string would
    make the check about formatting."""
    rhs = rhs.split("#", 1)[0].strip()
    if not rhs or not re.fullmatch(r"[\d.\s+\-*/()]+", rhs):
        return None
    try:
        return float(eval(rhs, {"__builtins__": {}}, {}))    # noqa: S307
    except (SyntaxError, ZeroDivisionError, TypeError, NameError):
        return None


# ---------------------------------------------------------------------------
_CITE_SLACK = 6


def _cite_distance(defs, cites):
    """How far the definition of a symbol is from where the spec says it is.

    `defs` is [(file, line, rhs)] and `cites` is [(file, start, end)]. Returns
    (distance, "file:start-end") for the closest same-file pairing, or None
    when the row cites no file the symbol lives in -- which is not a failure,
    only an absence of evidence."""
    best = None
    for f, a, b in cites:
        for df, dl, _rhs in defs:
            if df != f:
                continue
            d = 0 if a - _CITE_SLACK <= dl <= b + _CITE_SLACK else min(
                abs(dl - a), abs(dl - b))
            where = "%s:%d" % (f, a) if a == b else "%s:%d-%d" % (f, a, b)
            if best is None or d < best[0]:
                best = (d, where, dl)
    return best


def _severity_near(flat, idx, window=170):
    """The severity word the spec attaches to a friction reference.

    Word-boundary matched and LONGEST-FIRST, because `medium-high` contains
    `medium` and `high` and a substring test would call the Minbari row two
    different things."""
    seg = flat[max(0, idx - window): idx + window]
    best, bpos = None, None
    for w in sorted(_SEVERITY_WORDS, key=len, reverse=True):
        for m in re.finditer(r"(?<![\w-])%s(?![\w-])" % w, seg):
            d = abs(m.start() - min(idx, window))
            if bpos is None or d < bpos:
                best, bpos = w, d
    return best


def _symbol(name, module, defs, ctx, out):
    """One code symbol the row names, against where the row says it lives.

    Two claims, and the second is the one with teeth: the symbol is defined in
    station/ at all, and -- when the row cites the file and line -- it is
    STILL at that line. Every one of the family's eight symbol citations is
    exact today (`NIGHTWATCH_SHARE` at security.py:105 cited as :105), so this
    is a staleness detector with a live baseline rather than a hope."""
    if module and not any(d[0] == module + ".py" for d in defs):
        out("symbol", False, "%s.%s: %s is defined in %s, not there"
            % (module, name, name, ", ".join(sorted({d[0] for d in defs}))))
        return
    near = _cite_distance(defs, ctx["cites"])
    if near is None:
        out("symbol", True, "%s defined in %s" % (name, defs[0][0]))
        return
    d, where, at = near
    out("cite", d <= 0, "%s is at line %d, cited %s" % (name, at, where))


def _check_token(tok, ctx, out):
    """Resolve one backticked token, by a named branch per form.

    Everything the family actually contains has a branch; anything else is an
    UNRESOLVED failure rather than a silent skip."""
    import directory as DIR                                   # noqa: PLC0415
    from npc import costume as cos                            # noqa: PLC0415
    from npc import faction as FAC                            # noqa: PLC0415
    from npc import friction as FR                            # noqa: PLC0415
    keys, syms, strings = ctx["keys"], ctx["syms"], ctx["strings"]

    # a friction row: `narn/command`, `human/*`
    m = re.fullmatch(r"([a-z']+)/([a-z*']+)", tok)
    if m and m.group(2) != "0":
        a, b = m.group(1), m.group(2)
        row = None
        for p in FR.PAIRS:
            if (p[0], p[1]) in ((a, b), (b, a)):
                row = p
                break
        if row is None:
            # `grey/0`-shaped addresses never reach here; a two-word slash
            # token that is not a PAIRS row is a claim about a table that
            # does not have it.
            if a in {q["sector"] for q in DIR.PLACES}:
                out("address", True, "`%s` is a sector/ring address" % tok)
            else:
                out("friction", False,
                    "spec cites friction row `%s` and friction.PAIRS has no "
                    "such row" % tok)
            return
        want = _severity_near(ctx["flat"], ctx["flat"].find("`%s`" % tok))
        if want is None:
            out("friction", True, "`%s` is a PAIRS row (%s)" % (tok, row[2]))
        elif want != row[2]:
            out("friction", False,
                "`%s`: spec says %s, friction.PAIRS says %s"
                % (tok, want, row[2]))
        else:
            out("friction", True, "`%s` %s" % (tok, row[2]))
        return

    # a sector/ring address: `grey/0`
    if re.fullmatch(r"[a-z]+/\d+", tok):
        sec, ring = tok.split("/")
        ok = any(q["sector"] == sec and q["ring"] == int(ring)
                 for q in DIR.PLACES)
        out("address", ok, "`%s` %s" % (tok, "is a live sector/ring"
                                        if ok else "names no place"))
        return

    # a glob over place keys: `waste_*`
    if tok.endswith("_*"):
        pre = tok[:-1]
        hits = sorted(k for k in keys if k.startswith(pre))
        out("territory", bool(hits),
            "`%s` -> %s" % (tok, ", ".join(hits) or "NOTHING in the register"))
        ctx["glob"].append((tok, hits))
        return

    # a call: `Role("command")`
    m = re.fullmatch(r"([A-Za-z_]+)\(\"([a-z_]+)\"\)", tok)
    if m:
        name, arg = m.group(1), m.group(2)
        ok = name in syms and arg in ctx["roles"]
        out("symbol", ok, "`%s`: %s%s" % (
            tok, "defined" if name in syms else "%s is not defined" % name,
            "" if arg in ctx["roles"] else "; %r is not a role" % arg))
        return

    # a place key
    if tok in keys:
        return                    # counted by the territory check, not here
    if tok in FAC.PENDING:
        out("pending", True,
            "`%s` is faction.PENDING -- the people layer has it, the geometry "
            "register does not" % tok)
        return

    # an era event
    if tok in cos.ERA_EVENTS:
        ep = cos.ERA_EVENTS[tok][0]
        said = _EPISODE.findall(ctx["flat"])
        want = (str(ep[0]), str(ep[1]))
        out("era", want in said or not said,
            "`%s` = %s%s" % (tok, ep, "" if want in said else
                             " but the row quotes %s" % said))
        return

    # a module-level symbol, checked AT ITS CITED LINE where the row gives one
    bare = tok.strip("*_ ")
    if bare in syms:
        _symbol(bare, None, syms[bare], ctx, out)
        return
    if tok in strings or bare in strings:
        out("symbol", True, "`%s` is a data key in station/" % tok)
        return
    out("symbol", False,
        "`%s` resolves to nothing: not a place key, not a friction row, not "
        "an era event, not a symbol or string in station/" % tok)


# ---------------------------------------------------------------------------
def check(row):                                                   # noqa: C901
    import directory as DIR                                   # noqa: PLC0415
    from npc import costume as cos                            # noqa: PLC0415
    from npc import faction as FAC                            # noqa: PLC0415
    from npc import friction as FR                            # noqa: PLC0415
    from npc import schedule as SCH                           # noqa: PLC0415
    from spec_harness import spec_text                        # noqa: PLC0415

    rid = row.get("id", "")
    m = re.fullmatch(r"FAC-0*(\d+)", rid)
    if not m:
        return False, "not a FAC id: %r" % rid
    fid = "FAC-%02d" % int(m.group(1))

    text = spec_text(row.get("at", ""), lines=60)
    if not text:
        return False, "cannot read the row's own text from %r" % row.get("at")
    head = _HEAD.match(text.splitlines()[0].strip())
    if not head:
        return False, "heading is not `### FAC-nn -- name`: %r" % (
            text.splitlines()[0][:60])
    if head.group(1) != fid:
        return False, "registry row %s points at the block for %s" % (
            rid, head.group(1))
    if fid not in FAC.BY_ID:
        return False, "%s: npc/faction.py has no register entry" % fid

    flat = _flat(text)
    entry = FAC.BY_ID[fid]
    name, terr = entry[1], entry[3]
    bad, notes, kinds = [], [], set()

    def out(kind, ok, detail):
        kinds.add(kind)
        (notes if ok else bad).append("%s: %s" % (kind, detail))

    # -- 1. the block and the register are talking about the same faction ---
    #
    # WORD BY WORD AND NOT CHARACTER BY CHARACTER. The register's name is the
    # head of the spec's title -- "Security" against "Security (the force
    # proper)" -- so a prefix test is right and a character-level one is not:
    # `"thedrazii".startswith("thedrazi")` is True, and a control that renamed
    # the Drazi to the Drazii sailed through until this was word-based.
    title = head.group(2)
    words = lambda s: re.findall(r"[a-z0-9']+", s.lower())     # noqa: E731
    tw, nw = words(title), words(name)
    if tw[:len(nw)] != nw:
        bad.append("name: spec calls it %r, the register calls it %r"
                   % (title, name))

    ctx = {"keys": {q["key"] for q in DIR.PLACES}, "flat": flat, "glob": [],
           "roles": SCH.role_headcount(),
           "cites": [(c[0], int(c[1]), int(c[2] or c[1]))
                     for c in _CITE.findall(flat)]}
    ctx["syms"], ctx["strings"] = _index()

    # -- 2. every cited file:line is a line that exists ---------------------
    for f, ln, _end in ctx["cites"]:
        path = None
        for cand in (os.path.join(_ROOT, "station", f),
                     os.path.join(_ROOT, "station", "npc", f)):
            if os.path.exists(cand):
                path = cand
                break
        if path is None:
            out("cite", False, "%s:%d cites a file station/ does not have"
                % (f, ln))
            continue
        nlines = sum(1 for _ in open(path, encoding="utf-8"))
        if ln > nlines:
            out("cite", False, "%s:%d is past the end of a %d-line file"
                % (f, ln, nlines))

    # -- 3. head counts ----------------------------------------------------
    mn = _NUMS.search(text)
    para = _flat(mn.group(1)) if mn else ""
    if not para and mn is None:
        bad.append("parse: no **Numbers** clause under the heading")
    claims = ([(r, n) for n, r in _HEADS_NR.findall(para)]
              + [(r, n) for r, n in _HEADS_RN.findall(para)]
              + [(r, n) for r, n in _HEADS_RNR.findall(para)])
    for role, num in claims:
        got = ctx["roles"].get(role)
        if got is None:
            out("heads", False, "spec cites a %r role and ROLE_WEIGHTS has "
                                "none" % role)
        elif got != _n(num):
            out("heads", False, "%s heads: spec %s, role_headcount %d"
                % (role, num, got))
        else:
            out("heads", True, "%s %d" % (role, got))

    # -- 4. the census, for a faction the spec counts as one species -------
    hc = FAC.head_count(fid)
    species = [v for k, v in entry[2] if k == "species"]
    if len(species) == 1 and para:
        stripped = re.sub(r"\*+", "", para).strip()
        if re.match(r"zero\b", stripped, re.I):
            said = 0
        else:
            mnum = re.match(r"[^\d]*?([\d,]+)", stripped)
            said = _n(mnum.group(1)) if mnum else None
        if said is None:
            out("census", False, "no leading head-count in %r" % stripped[:40])
        elif hc != said:
            out("census", False, "%s: spec %s, faction.head_count %s"
                % (species[0], said, hc))
        else:
            out("census", True, "%s %s" % (species[0], hc))

    # -- 5. the row's own arithmetic ---------------------------------------
    for total, rhs in _SUM.findall(para):
        parts = [_n(x) for x in re.findall(r"[\d,]{2,}", rhs)]
        if len(parts) < 2:
            continue
        if sum(parts) != _n(total):
            out("sum", False, "%s = %s sums to %d"
                % (total, " + ".join("%d" % p for p in parts), sum(parts)))
        else:
            out("sum", True, "%s = %d parts" % (total, len(parts)))
    for seg in para.split(";"):
        if seg.count("·") >= 2 and ":" in seg:
            lhs, rhs = seg.split(":", 1)
            items = [p for p in rhs.split("·")]
            nums = [re.findall(r"[\d,]+", p) for p in items]
            if all(len(x) == 1 for x in nums):
                tot = re.search(r"~?([\d,]{2,})", lhs)
                if tot:
                    # THE FIRST NUMBER ON THE LEFT AND ONLY IT. FAC-24 reads
                    # "~20,000 unregistered (bracketed 13,000-50,000)", and a
                    # check that accepted any number on that side would pass
                    # a census summing to 50,000 as readily as one summing to
                    # the total the row actually states.
                    s = sum(_n(x[0]) for x in nums)
                    out("sum", _n(tot.group(1)) == s,
                        "census: %d items sum to %s against the row's %s"
                        % (len(nums), "{:,}".format(s), tot.group(1)))
    mapx = _APPROX.match(re.sub(r"\*+", "", para).strip())
    if mapx and hc:
        want = _n(mapx.group(1))
        out("approx", abs(hc - want) <= 0.10 * want,
            "spec ~%s against head_count %s" % (mapx.group(1),
                                                "{:,}".format(hc)))

    # -- 4b. the rhythm, for a faction that IS a species --------------------
    #
    # THE **HOURS** CLAUSE IS NOT DECORATION. Thirteen of the 28 blocks state a
    # sleep block, a meal list or a jitter, and every one of those is a field
    # of `schedule.RHYTHMS[species]` -- "sleep 04:30-11:00" is
    # `sleep_start=4.5, sleep_hours=6.5`, "meals 12:00, 17:00, 23:00" is the
    # `meals` tuple, "hive jitter 0.35" is `jitter`. A faction whose people
    # sleep at hours the schedule does not keep is a faction the player will
    # never meet where the row says they are.
    if len(species) == 1 and species[0] in SCH.RHYTHMS:
        r = SCH.RHYTHMS[species[0]]
        clk = lambda s: int(s.split(":")[0]) + int(s.split(":")[1]) / 60.0  # noqa: E731
        ms = _SLEEP.search(flat)
        if ms:
            a, b = clk(ms.group(1)), clk(ms.group(2))
            out("rhythm", abs(r.sleep_start - a) < 1e-6
                and abs((r.sleep_start + r.sleep_hours) % 24.0 - b) < 1e-6,
                "%s sleep: spec %s-%s, RHYTHMS %04.1f for %.1f h -> %04.1f"
                % (species[0], ms.group(1), ms.group(2), r.sleep_start,
                   r.sleep_hours, (r.sleep_start + r.sleep_hours) % 24.0))
        mj = _JITTER.search(flat)
        if mj:
            out("rhythm", abs(r.jitter - float(mj.group(1))) < 1e-9,
                "%s jitter: spec %s, RHYTHMS %s"
                % (species[0], mj.group(1), r.jitter))
        mmeal = _MEALS.search(flat)
        if mmeal:
            said = tuple(sorted(clk("%s:%s" % g)
                                for g in _CLOCK.findall(mmeal.group(1))))
            out("rhythm", said == tuple(sorted(r.meals)),
                "%s meals: spec %s, RHYTHMS %s"
                % (species[0], list(said), list(r.meals)))
        elif re.search(r"no meals", flat):
            out("rhythm", r.meals == (),
                "%s: the row says no meals and RHYTHMS has %s"
                % (species[0], list(r.meals)))
        msec = _SECLUSION.search(flat)
        if msec:
            out("rhythm", abs(r.sleep_hours - float(msec.group(1))) < 1e-9,
                "%s seclusion: spec %s h, RHYTHMS %s h"
                % (species[0], msec.group(1), r.sleep_hours))

    # -- 5b. a flag's population is the number the row states ---------------
    #
    # FOUR OF THE 28 FACTIONS ARE NOT A SPECIES OR A ROLE. The Nightwatch is
    # an armband, Psi Corps a badge, the Guild a card, the Rangers a brooch --
    # `faction._FLAGS` -- and each of those populations is owned by a
    # different module (`costume`, `resident`, `faction.GUILD_CARDED`). The
    # row states the same population in words, so the two can be compared:
    # exactly, or inside a range the row itself gives.
    exacts = [_n(x) for x in _EXACT.findall(para)]
    ranges = [(_n(a), _n(b)) for a, b in _RANGE.findall(para)]
    for kind, val in entry[2]:
        if kind != "flag":
            continue
        pop = FAC._flag_population(val, cos.ERA_DATUM)
        if pop in exacts:
            out("flag", True, "%s population %s is the row's own number"
                % (val, "{:,}".format(pop)))
        elif any(lo <= pop <= hi for lo, hi in ranges):
            out("flag", True, "%s population %s inside the row's band"
                % (val, "{:,}".format(pop)))
        else:
            out("flag", False,
                "%s population is %s and the row states %s -- neither the "
                "same number nor inside any band it gives"
                % (val, "{:,}".format(pop),
                   " / ".join("%s-%s" % r for r in ranges) or "no band"))

    # -- 6. staffed missions (FAC-12's "one ruling, three consumers") ------
    mm = _MISSIONS.search(flat)
    if mm:
        want = _WORDNUM.get(mm.group(1).lower()) or int(mm.group(1))
        out("missions", len(species) == want,
            "spec says %d staffed missions; faction.py's %s carries %d species"
            % (want, fid, len(species)))

    # -- 7. friction ladder figures ----------------------------------------
    for msep in _SEP_M.finditer(flat):
        sev = _severity_near(flat, msep.start())
        if sev is None:
            continue
        want = FR.BASE_SEPARATION_M * FR.SEVERITY[sev][0]
        out("ladder", abs(want - float(msep.group(1))) < 0.005,
            "%s separation: spec %s m, friction %.2f m"
            % (sev, msep.group(1), want))
    for mev in _EVENTS_H.finditer(flat):
        sev = _severity_near(flat, mev.start())
        if sev is None:
            continue
        out("ladder", abs(FR.SEVERITY[sev][1] - float(mev.group(1))) < 1e-9,
            "%s contact: spec %s/h, friction %s/h"
            % (sev, mev.group(1), FR.SEVERITY[sev][1]))
    for sev, mult, metres in _LADDER.findall(flat):
        if sev not in FR.SEVERITY:
            continue
        ok = (abs(FR.SEVERITY[sev][0] - float(mult)) < 1e-9
              and abs(FR.BASE_SEPARATION_M * float(mult)
                      - float(metres)) < 0.005)
        out("ladder", ok, "%s %sx = %s m against %sx = %.2f m"
            % (sev, mult, metres, FR.SEVERITY[sev][0],
               FR.BASE_SEPARATION_M * FR.SEVERITY[sev][0]))

    # -- 8. the era gate ----------------------------------------------------
    era = entry[5]
    if era:
        key = era.lstrip("!")
        if key not in cos.ERA_EVENTS:
            out("era", False, "the register gates %s on %r and costume."
                              "ERA_EVENTS has no such event" % (fid, key))
        else:
            ep = cos.ERA_EVENTS[key][0]
            said = _EPISODE.findall(flat)
            out("era", (str(ep[0]), str(ep[1])) in said,
                "%s gates on %s = %s and the row quotes %s"
                % (fid, key, ep, said or "no episode at all"))

    # -- 9. constants the row quotes with a value --------------------------
    for cname, cval in _CONST.findall(flat):
        defs = ctx["syms"].get(cname)
        if not defs:
            out("const", False, "%s=%s: station/ defines no such constant"
                % (cname, cval))
            continue
        want = _literal(cval)
        vals = [(d[0], _literal(d[2])) for d in defs if _literal(d[2]) is not None]
        if want is None or not vals:
            out("const", True, "%s defined in %s" % (cname, defs[0][0]))
        elif any(abs(v - want) < 1e-9 for _f, v in vals):
            out("const", True, "%s = %s" % (cname, cval))
        else:
            out("const", False, "%s: spec %s = %g, code %s"
                % (cname, cval, want,
                   ", ".join("%s %g" % (f, v) for f, v in vals)))

    # -- 10. territory ------------------------------------------------------
    mt = _TERR.search(text)
    spec_terr = []
    if mt:
        spec_terr = [t for t in _TOKEN.findall(_flat(mt.group(1)))
                     if re.fullmatch(r"[a-z][a-z0-9_]*", t)]
    for k in spec_terr:
        if k not in ctx["keys"]:
            if k in FAC.PENDING:
                out("pending", True, "`%s` is pending an address" % k)
            else:
                out("territory", False,
                    "spec gives `%s` as %s territory and directory.PLACES has "
                    "no such place" % (k, fid))
        elif k not in terr:
            out("territory", False,
                "spec gives `%s` as %s territory and faction.py's %s carries "
                "%s" % (k, fid, fid, ", ".join(terr) or "nothing"))
        else:
            out("territory", True, "`%s`" % k)

    # -- 11. every remaining backticked token resolves ----------------------
    for tok in dict.fromkeys(_TOKEN.findall(flat)):
        _check_token(tok, ctx, out)

    # -- 12. and every code symbol named OUTSIDE backticks -----------------
    for mod, sym in dict.fromkeys(_CAPS.findall(flat)):
        defs = ctx["syms"].get(sym)
        if not defs:
            out("symbol", False,
                "the row names %s%s and station/ defines no such symbol"
                % (mod + "." if mod else "", sym))
        else:
            _symbol(sym, mod or None, defs, ctx, out)
    for tok, hits in ctx["glob"]:
        if hits and not any(h in terr for h in hits):
            out("territory", False,
                "spec gives `%s` as territory and faction.py's %s carries "
                "none of %s" % (tok, fid, ", ".join(hits)))

    # -- verdict ------------------------------------------------------------
    if not kinds & set(_SUBSTANTIVE):
        return False, ("%s `%s`: nothing substantive parsed out of the row -- "
                       "no head-count, territory, friction, era or constant "
                       "claim. That is a parse failure, not a pass" % (fid, name))
    if bad:
        return False, "%s %s: %s" % (fid, name, "; ".join(bad[:4]))
    return True, "%s %s: %d claims agree (%s)" % (
        fid, name, len(notes), ", ".join(sorted(kinds)))


# ===========================================================================
# THE NEGATIVE CONTROLS, AND THEY LIVE HERE RATHER THAN IN A SCRATCH FILE
# ===========================================================================
#
# The rule this repository breaks most often is "a check that cannot fail for
# the thing it is named after", and the reason it survives is that the proof a
# check CAN fail is usually a paragraph in a handover rather than something a
# later context can run. So it is code: each row below corrupts ONE claim in a
# COPY of PEOPLE.md, re-runs that row, and demands the harness fail FOR THAT
# REASON -- the family key must appear in the message, so a control that fires
# for an unrelated defect does not count as firing.
#
#     python3 station/spec_harness/fac.py --selftest
#
# (label, FAC number, the text to corrupt, what to corrupt it to)
_CONTROLS = (
    ("census", 13, "12,500 — dominant in", "12,400 — dominant in"),
    ("census", 23, "**Numbers:** 1 — hard", "**Numbers:** 2 — hard"),
    ("heads", 2, "120 command-role heads", "121 command-role heads"),
    ("rhythm", 20, "sleep 08:00–14:00", "sleep 08:00–15:00"),
    ("rhythm", 20, "meals 15:00, 01:30", "meals 15:00, 01:45"),
    ("friction", 11, "medium (PAIRS `minbari/minbari`)",
     "high (PAIRS `minbari/minbari`)"),
    ("friction", 11, "`minbari/minbari`", "`minbari/warrior`"),
    ("ladder", 23, "ceremonial 6.0× = 2.70 m", "ceremonial 6.0× = 2.90 m"),
    ("ladder", 9, "0.02 events/h", "0.05 events/h"),
    ("era", 28, "semi-covert from (3,1)", "semi-covert from (3,4)"),
    ("const", 5, "PSI_LICENSED_ABOARD=25", "PSI_LICENSED_ABOARD=30"),
    ("symbol", 27, "ISN_PLACES", "ISN_SCREEN_PLACES"),
    # ON A ROW THAT OTHERWISE PASSES, so the control cannot be satisfied by
    # the row's own live failure. FAC-05 is green; FAC-04 is not.
    ("cite", 5, "resident.py:519–529", "resident.py:619–629"),
    ("cite", 5, "resident.py:519–529", "resident.py:9519–9529"),
    ("sum", 10, "17,500 = 150 mission", "17,400 = 150 mission"),
    ("sum", 24, "sick 500;", "sick 900;"),
    ("flag", 28, "20–60 aboard", "70–90 aboard"),
    ("missions", 12, "**NINE staffed missions", "**TEN staffed missions"),
    ("approx", 24, "~20,000 unregistered", "~40,000 unregistered"),
    ("territory", 7, "`medlab_red`", "`medlab_scarlet`"),
    ("name", 13, "### FAC-13 — The Drazi", "### FAC-13 — The Drazii"),
)


def _rows():
    """The FAC rows as `spec_check.py` hands them over: id and `at`."""
    reg = open(os.path.join(_ROOT, "docs/spec/completion.yaml"),
               encoding="utf-8").read()
    return [{"id": m.group(1), "at": m.group(2)} for m in
            re.finditer(r"- id: (FAC-\d+)\n\s+at: (\S+)", reg)]


def _selftest(out=print):                                    # pragma: no cover
    import tempfile
    rows = _rows()
    out("THE 28 FACTIONS -- docs/spec/PEOPLE.md 1 against the code")
    npass = 0
    for row in rows:
        ok, note = check(row)
        npass += ok
        out("  %s %s" % ("PASS" if ok else "FAIL", note))
    out("  -- %d of %d rows agree with the code" % (npass, len(rows)))

    src = os.path.join(_ROOT, "docs/spec/PEOPLE.md")
    base = open(src, encoding="utf-8").read()
    at_of = {r["id"]: r["at"] for r in rows}
    tmp = os.path.join(tempfile.mkdtemp(prefix="fac-controls-"), "PEOPLE.md")
    out("\nNEGATIVE CONTROLS -- one corrupted claim each, in a copy")
    dead = []
    for label, n, old, new in _CONTROLS:
        rid = "FAC-%03d" % n
        if base.count(old) != 1:
            dead.append("%s: the control's own anchor %r appears %d times"
                        % (label, old, base.count(old)))
            continue
        open(tmp, "w", encoding="utf-8").write(base.replace(old, new))
        ok, note = check({"id": rid, "at": "%s:%s"
                          % (tmp, at_of[rid].split(":")[1])})
        fired = (not ok) and label in note
        out("  %-9s %s %s  %s" % (label, rid,
                                  "FIRES" if fired else "DOES NOT FIRE",
                                  note[:120]))
        if not fired:
            dead.append("%s on %s did not fail for its own reason" % (label, rid))
    if dead:
        out("")
        for d in dead:
            out("  DEAD CONTROL %s" % d)
    out("\n%d of %d controls fire" % (len(_CONTROLS) - len(dead), len(_CONTROLS)))
    return not dead


if __name__ == "__main__":                                   # pragma: no cover
    import sys
    # run directly, the way a person checks a harness. Imported by
    # `spec_check.py` the path is already set; here it is not, and `station/`
    # is what both `directory` and the `spec_harness` package hang off.
    sys.path.insert(0, os.path.join(_ROOT, "station"))
    raise SystemExit(0 if _selftest() else 1)

