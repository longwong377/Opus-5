#!/usr/bin/env python3
"""The AAA bar, enforced.

Reads a JSON scorecard -- one entry per subsystem, each holding an ordered list
of review rounds -- and answers the only question that matters to a review loop:
may this subsystem stop.

The rubric it enforces is `docs/AAA-STANDARD.md`. Four dimensions scored 0-5:
CRAFT, FIDELITY, PERFORMANCE, ROBUSTNESS. The bar is all four >= 4 with two
consecutive rounds producing no finding above `minor`.

Two things here are not arithmetic and are the reason the file exists.

**Regression.** A critic sees one snapshot. A rubric sees the sequence, so it can
say "this was a 5 last round and it is a 4 now" -- which no reviewer looking at
the current build can know. A drop exits non-zero whether or not the subsystem is
still above the bar, because "still passing" is not the same as "not worse".

**Termination.** A sufficiently harsh critic always finds something, so an
unbounded review loop is the most expensive failure mode this project has. The
gate refuses a `major` finding on a dimension the same round scored at the bar,
requires a descriptor reference on every finding that is not an explicit
preference, and forces a subsystem past `max_rounds` to be CAPPED with a written
reason rather than reviewed again.

Usage:
    python3 tools/aaa_gate.py                       # self-test, "N/N passed"
    python3 tools/aaa_gate.py <scorecard.json>      # evaluate
    python3 tools/aaa_gate.py <scorecard.json> --strict
    python3 tools/aaa_gate.py --template
"""
import json
import os
import re
import sys

DIMENSIONS = ("craft", "fidelity", "performance", "robustness")
DIM_LETTER = {"craft": "C", "fidelity": "F", "performance": "P",
              "robustness": "R"}
LETTER_DIM = {v: k for k, v in DIM_LETTER.items()}
DIM_HEAD = {"craft": "CRAFT", "fidelity": "FIDELITY",
            "performance": "PERF", "robustness": "ROBUST"}

# Ordered worst first. `blocking` and `major` reset the clean-round counter;
# `minor`, `note` and `resolved` never do. That asymmetry is the whole stopping
# rule -- if a minor finding could reopen a subsystem there would be no bottom
# to the loop.
#
# `resolved` IS NOT A FINDING. It is a round's record that a PREVIOUS round's
# finding has been answered, and it is in the schema because the alternative is
# what three exterior_approach rounds actually did: file the closure as a
# `note`, where it reads as an open preference and is indistinguishable from
# work still outstanding. A closure cites the descriptor it closes, and that
# descriptor is deliberately exempt from the score coupling below -- a resolved
# C4 on a round that now scores craft 4 is the correct shape, not a
# contradiction.
SEVERITIES = ("blocking", "major", "minor", "note", "resolved")
RESETTING = ("blocking", "major")

DEFAULT_BAR = {"min_score": 4, "clean_rounds_required": 2, "max_rounds": 4}
STATUSES = ("active", "capped", "shipped")

TOP_KEYS = {"version", "bar", "subsystems", "notes"}
SUB_KEYS = {"status", "cap_reason", "rounds", "owner", "notes"}
# `what_is_good` is a list, and it is in the schema rather than tolerated,
# because a review that enumerates only defects gives a builder no way to tell
# what it must not break while fixing them. Two 4e rounds carried it already.
ROUND_KEYS = {"round", "reviewer", "date", "scores", "evidence", "findings",
              "broke_assertions", "regression_waiver", "notes", "what_is_good"}
FINDING_KEYS = {"severity", "dimension", "descriptor", "text", "where"}

DESCRIPTOR_RE = re.compile(r"^[CFPR][0-5]$")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CARD = os.path.join(ROOT, "docs", "aaa-scorecard.json")


# --------------------------------------------------------------------------
# structural validation
#
# Everything below rejects a scorecard that is *shaped* wrong, before any score
# is believed. A malformed scorecard that half-parses is worse than none: it
# prints a dashboard, and a dashboard reads as a result.
# --------------------------------------------------------------------------

def _is_int(v):
    # bool is a subclass of int, and JSON `true` parses to True. A score of
    # `true` would otherwise be read as 1 and pass every range check.
    return isinstance(v, int) and not isinstance(v, bool)


def _nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def _unknown_keys(obj, known):
    """The keys of `obj` this schema does not recognise.

    An underscore prefix marks documentation -- `_merge_note`, `_frames`, the
    provenance a merging agent has to keep somewhere.  Those are allowed, and
    the reason the allowance is safe is that nobody misspells a key by adding a
    leading underscore.  Except in one case, which is the whole point of the
    exception being narrow: `_findings` next to a missing `findings` would make
    a round's findings silently vanish, and the round would then read as clean.
    So `_x` is documentation only when `x` is NOT itself a key of this schema.
    """
    bad = []
    for k in sorted(set(obj) - set(known)):
        if k.startswith("_") and k.lstrip("_") not in known:
            continue
        bad.append(k)
    return bad


def validate(card):
    """Return a sorted list of structural errors. Empty means well-formed."""
    err = []

    if not isinstance(card, dict):
        return ["scorecard is not an object"]

    for k in sorted(set(card) - TOP_KEYS):
        err.append(f"unknown top-level key {k!r}")

    bar = dict(DEFAULT_BAR)
    given = card.get("bar", {})
    if not isinstance(given, dict):
        err.append("bar is not an object")
        given = {}
    for k in sorted(set(given) - set(DEFAULT_BAR)):
        err.append(f"unknown bar key {k!r}")
    for k in DEFAULT_BAR:
        if k in given:
            if not _is_int(given[k]):
                err.append(f"bar.{k} is not an integer")
            else:
                bar[k] = given[k]
    if not 0 <= bar["min_score"] <= 5:
        err.append(f"bar.min_score {bar['min_score']} outside 0-5")
    if bar["clean_rounds_required"] < 1:
        err.append("bar.clean_rounds_required must be at least 1")
    if bar["max_rounds"] < 1:
        err.append("bar.max_rounds must be at least 1")

    subs = card.get("subsystems")
    if not isinstance(subs, dict) or not subs:
        err.append("subsystems missing or empty")
        return sorted(err)

    for name in sorted(subs):
        err.extend(_validate_subsystem(name, subs[name], bar))
    return sorted(err)


def _validate_subsystem(name, sub, bar):
    err = []
    tag = f"{name}"
    if not isinstance(sub, dict):
        return [f"{tag}: not an object"]
    for k in _unknown_keys(sub, SUB_KEYS):
        err.append(f"{tag}: unknown key {k!r}")

    status = sub.get("status", "active")
    if status not in STATUSES:
        err.append(f"{tag}: status {status!r} not one of {list(STATUSES)}")
    # A cap is a decision owed to the owner, so it has to carry the reason the
    # owner is being asked to decide about. A cap with no reason is just a
    # subsystem that stopped being reviewed.
    if status == "capped" and not _nonempty_str(sub.get("cap_reason")):
        err.append(f"{tag}: capped with no cap_reason")
    if status != "capped" and sub.get("cap_reason") is not None:
        err.append(f"{tag}: cap_reason set but status is {status!r}")

    rounds = sub.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        err.append(f"{tag}: rounds missing or empty")
        return err

    last_n = None
    for i, rnd in enumerate(rounds):
        err.extend(_validate_round(tag, i, rnd, bar))
        if isinstance(rnd, dict) and _is_int(rnd.get("round")):
            n = rnd["round"]
            # Strictly increasing, so re-submitting last round's scorecard is
            # an error rather than progress towards the clean-round count.
            if last_n is not None and n <= last_n:
                err.append(f"{tag}: round {n} does not follow round {last_n}")
            last_n = n

    # A waiver only means something against a regression. A standing waiver
    # would silently authorise the next drop.
    for i, rnd in enumerate(rounds):
        if not isinstance(rnd, dict):
            continue
        w = rnd.get("regression_waiver")
        if w is None:
            continue
        if not _nonempty_str(w):
            err.append(f"{tag}: round {rnd.get('round')}: empty regression_waiver")
        elif not _regressions(rounds, i):
            err.append(f"{tag}: round {rnd.get('round')}: "
                       f"regression_waiver with no regression")
    return err


def _validate_round(tag, index, rnd, bar):
    err = []
    if not isinstance(rnd, dict):
        return [f"{tag}: round #{index} is not an object"]
    rtag = f"{tag}: round {rnd.get('round', '?')}"
    for k in _unknown_keys(rnd, ROUND_KEYS):
        err.append(f"{rtag}: unknown key {k!r}")
    if not _is_int(rnd.get("round")):
        err.append(f"{rtag}: round number is not an integer")

    scores = rnd.get("scores")
    if not isinstance(scores, dict):
        return err + [f"{rtag}: scores missing"]
    missing = sorted(set(DIMENSIONS) - set(scores))
    extra = sorted(set(scores) - set(DIMENSIONS))
    for d in missing:
        err.append(f"{rtag}: missing dimension {d!r}")
    for d in extra:
        err.append(f"{rtag}: unknown dimension {d!r}")

    evidence = rnd.get("evidence", {})
    if not isinstance(evidence, dict):
        err.append(f"{rtag}: evidence is not an object")
        evidence = {}
    # Evidence is keyed by the dimension it supports, so that "scored 4 with no
    # evidence" can be asked per dimension. A review also produces things that
    # back several dimensions at once -- the render path, the frame list, the
    # measured distribution -- and those take the documentation prefix, which
    # deliberately does NOT count as evidence for any dimension: a measurement
    # filed under `_measured` leaves craft with nothing under its own name, and
    # the gate should say so.
    for d in _unknown_keys(evidence, DIMENSIONS):
        err.append(f"{rtag}: evidence for unknown dimension {d!r}")

    for d in DIMENSIONS:
        if d not in scores:
            continue
        s = scores[d]
        if not _is_int(s):
            err.append(f"{rtag}: {d} score {s!r} is not an integer")
            continue
        # Membership rather than `0 <= s <= 5`, so that if the integer guard
        # above is ever removed this reports the bad score instead of raising
        # on the first comparison against a string. A tool that reads a
        # hand-edited JSON file should not traceback at the user.
        if s not in (0, 1, 2, 3, 4, 5):
            err.append(f"{rtag}: {d} score {s} outside 0-5")
            continue
        # At or above the bar the score is a claim about the artefact, and a
        # claim needs something to point at: a render path, a measured number,
        # an assertion name or a citation.
        if s >= bar["min_score"] and not _nonempty_str(evidence.get(d)):
            err.append(f"{rtag}: {d} scored {s} with no evidence")

    # ROBUSTNESS 5's descriptor *is* the claim that every assertion was
    # deliberately broken and observed to fail. It is the one score that cannot
    # be awarded from reading the code.
    if scores.get("robustness") == 5 and rnd.get("broke_assertions") is not True:
        err.append(f"{rtag}: robustness 5 requires broke_assertions: true")
    if "broke_assertions" in rnd and not isinstance(rnd["broke_assertions"], bool):
        err.append(f"{rtag}: broke_assertions is not a boolean")

    findings = rnd.get("findings", [])
    if not isinstance(findings, list):
        err.append(f"{rtag}: findings is not a list")
        findings = []
    for j, f in enumerate(findings):
        err.extend(_validate_finding(rtag, j, f, scores, bar))

    err.extend(_validate_coupling(rtag, scores, findings, bar))
    return err


def _validate_finding(rtag, index, f, scores, bar):
    err = []
    if not isinstance(f, dict):
        return [f"{rtag}: finding #{index} is not an object"]
    ftag = f"{rtag}: finding #{index}"
    for k in _unknown_keys(f, FINDING_KEYS):
        err.append(f"{ftag}: unknown key {k!r}")

    sev = f.get("severity")
    if sev not in SEVERITIES:
        err.append(f"{ftag}: severity {sev!r} not one of {list(SEVERITIES)}")
        return err
    if not _nonempty_str(f.get("text")):
        err.append(f"{ftag}: no text")

    # A `note` is a preference by definition, so it is the one severity that
    # needs no descriptor -- and the one that can never block anything.
    if sev == "note":
        return err

    dim = f.get("dimension")
    if dim not in DIMENSIONS:
        err.append(f"{ftag}: dimension {dim!r} not one of {list(DIMENSIONS)}")
        return err

    desc = f.get("descriptor")
    if not isinstance(desc, str) or not DESCRIPTOR_RE.match(desc):
        err.append(f"{ftag}: descriptor {desc!r} is not [CFPR][0-5] -- a "
                   f"finding must name the descriptor it points at")
        return err
    if LETTER_DIM[desc[0]] != dim:
        err.append(f"{ftag}: descriptor {desc} is a "
                   f"{LETTER_DIM[desc[0]]} descriptor on a {dim} finding")
        return err

    # A closure names what it closed and is not scored against this round.
    if sev == "resolved":
        return err

    digit = int(desc[1])
    s = scores.get(dim)
    if sev in RESETTING:
        # Severity inflation: a major has to cite a below-bar descriptor, or it
        # is a minor wearing a bigger word.
        if digit >= bar["min_score"]:
            err.append(f"{ftag}: {sev} cites {desc}, which is at or above the "
                       f"bar of {bar['min_score']}")
        if _is_int(s) and s > digit:
            err.append(f"{ftag}: cites {desc} but {dim} is scored {s}")
    else:  # minor
        # Severity deflation: a minor that cites a below-bar descriptor is
        # describing something that moves the score, which is a major.
        if digit < bar["min_score"]:
            err.append(f"{ftag}: minor cites {desc}, below the bar of "
                       f"{bar['min_score']} -- that is a major")
    return err


def _validate_coupling(rtag, scores, findings, bar):
    """Scores and findings must agree with each other.

    A dimension below the bar with nothing explaining it is an unexplained
    score; a dimension at the bar carrying a major finding is a reviewer who
    wanted to say `major` without saying which descriptor fails.
    """
    err = []
    heavy = {}
    for f in findings:
        if isinstance(f, dict) and f.get("severity") in RESETTING:
            heavy.setdefault(f.get("dimension"), 0)
            heavy[f["dimension"]] += 1
    for d in DIMENSIONS:
        s = scores.get(d)
        if not _is_int(s) or not 0 <= s <= 5:
            continue
        if s < bar["min_score"] and not heavy.get(d):
            err.append(f"{rtag}: {d} scored {s}, below the bar, with no major "
                       f"or blocking finding explaining it")
        if s >= bar["min_score"] and heavy.get(d):
            err.append(f"{rtag}: {d} scored {s}, at or above the bar, with a "
                       f"major or blocking finding against it")
    return err


# --------------------------------------------------------------------------
# evaluation
# --------------------------------------------------------------------------

def _regressions(rounds, i):
    """Dimensions lower in rounds[i] than in rounds[i-1]."""
    if i == 0:
        return []
    prev, cur = rounds[i - 1], rounds[i]
    if not (isinstance(prev, dict) and isinstance(cur, dict)):
        return []
    a, b = prev.get("scores", {}), cur.get("scores", {})
    out = []
    for d in DIMENSIONS:
        if _is_int(a.get(d)) and _is_int(b.get(d)) and b[d] < a[d]:
            out.append((d, a[d], b[d]))
    return out


def _round_is_clean(rounds, i):
    """No finding above `minor`, and no regression into this round.

    A round carrying a waived regression is explicitly not clean. The waiver
    stops the build going red; it does not make the round evidence of quality.
    """
    rnd = rounds[i]
    for f in rnd.get("findings", []):
        if isinstance(f, dict) and f.get("severity") in RESETTING:
            return False
    return not _regressions(rounds, i)


def evaluate(card):
    """Return a report dict. Deterministic: no dict-order dependence anywhere."""
    bar = dict(DEFAULT_BAR)
    given = card.get("bar", {}) if isinstance(card, dict) else {}
    if isinstance(given, dict):
        for k in DEFAULT_BAR:
            if _is_int(given.get(k)):
                bar[k] = given[k]

    report = {"bar": bar, "errors": validate(card), "subsystems": {}}
    subs = card.get("subsystems", {}) if isinstance(card, dict) else {}
    if not isinstance(subs, dict):
        return report

    for name in sorted(subs):
        sub = subs[name]
        if not isinstance(sub, dict) or not isinstance(sub.get("rounds"), list) \
                or not sub["rounds"]:
            continue
        rounds = [r for r in sub["rounds"] if isinstance(r, dict)]
        if not rounds:
            continue
        cur = rounds[-1]
        scores = {d: cur.get("scores", {}).get(d) for d in DIMENSIONS}
        prev = rounds[-2] if len(rounds) > 1 else None
        deltas = {}
        for d in DIMENSIONS:
            if prev and _is_int(scores[d]) and _is_int(prev.get("scores", {}).get(d)):
                deltas[d] = scores[d] - prev["scores"][d]
            else:
                deltas[d] = None

        streak = 0
        for i in range(len(rounds) - 1, -1, -1):
            if _round_is_clean(rounds, i):
                streak += 1
            else:
                break

        at_bar = all(_is_int(scores[d]) and scores[d] >= bar["min_score"]
                     for d in DIMENSIONS)
        shippable = at_bar and streak >= bar["clean_rounds_required"]
        regs = _regressions(rounds, len(rounds) - 1)
        waiver = cur.get("regression_waiver")
        status = sub.get("status", "active")
        capped = status == "capped"
        # Over the cap and not done: the loop has to stop and somebody has to
        # decide. That is a failure of the gate, not another review round.
        over_cap = (not capped and not shippable
                    and status != "shipped"
                    and len(rounds) > bar["max_rounds"])

        if regs and not waiver:
            verdict = "REGRESSED"
        elif capped:
            verdict = "CAPPED"
        elif status == "shipped":
            verdict = "SHIPPED"
        elif over_cap:
            verdict = "OVER-CAP"
        elif shippable:
            verdict = "SHIP"
        else:
            verdict = "ACTIVE"

        opens = sorted(
            (f for f in cur.get("findings", []) if isinstance(f, dict)),
            key=lambda f: (SEVERITIES.index(f.get("severity"))
                           if f.get("severity") in SEVERITIES else 99,
                           str(f.get("dimension")), str(f.get("text"))))

        report["subsystems"][name] = {
            "round": cur.get("round"),
            "rounds_used": len(rounds),
            "scores": scores,
            "deltas": deltas,
            "clean_streak": streak,
            "at_bar": at_bar,
            "shippable": shippable,
            "regressions": regs,
            "waiver": waiver,
            "status": status,
            "capped": capped,
            "cap_reason": sub.get("cap_reason"),
            "over_cap": over_cap,
            "verdict": verdict,
            "findings": opens,
            "shortfall": sorted(d for d in DIMENSIONS
                                if not (_is_int(scores[d])
                                        and scores[d] >= bar["min_score"])),
        }
    return report


def failures(report, strict=False):
    """Reasons the gate should exit non-zero, sorted."""
    out = list(report["errors"])
    for name in sorted(report["subsystems"]):
        s = report["subsystems"][name]
        if s["regressions"] and not s["waiver"]:
            for d, a, b in s["regressions"]:
                out.append(f"{name}: {d} regressed {a} -> {b} "
                           f"(no regression_waiver)")
        if s["over_cap"]:
            out.append(f"{name}: {s['rounds_used']} rounds used of "
                       f"{report['bar']['max_rounds']} and not at the bar -- "
                       f"cap it with a reason or raise max_rounds deliberately")
        if strict and not (s["shippable"] or s["capped"]
                           or s["status"] == "shipped"):
            out.append(f"{name}: below the bar "
                       f"({', '.join(s['shortfall']) or 'clean rounds'}) "
                       f"and --strict is set")
    return sorted(out)


# --------------------------------------------------------------------------
# dashboard
# --------------------------------------------------------------------------

def _cell(score, delta):
    if not _is_int(score):
        return "  ?   ?   "
    bar = "#" * score + "." * (5 - score)
    mark = "   "
    if delta is not None and delta > 0:
        mark = f" +{delta}"
    elif delta is not None and delta < 0:
        mark = f" {delta}"
    return f"{bar} {score}{mark}"


def format_report(report, path="", strict=False):
    bar = report["bar"]
    L = []
    L.append(f"AAA gate -- {path}" if path else "AAA gate")
    L.append(f"bar: every dimension >= {bar['min_score']}, "
             f"{bar['clean_rounds_required']} consecutive rounds with no "
             f"finding above 'minor', at most {bar['max_rounds']} rounds")
    L.append("")

    if report["errors"]:
        L.append(f"SCORECARD IS MALFORMED -- {len(report['errors'])} problem(s)")
        for e in report["errors"]:
            L.append(f"  ! {e}")
        L.append("")

    names = sorted(report["subsystems"])
    if names:
        width = max(20, min(28, max(len(n) for n in names)))
        head = (f"{'subsystem':<{width}} rnd  "
                + "  ".join(f"{DIM_HEAD[d]:<10}" for d in DIMENSIONS)
                + "  cln  verdict")
        L.append(head)
        L.append("-" * len(head))
        for n in names:
            s = report["subsystems"][n]
            cells = "  ".join(_cell(s["scores"][d], s["deltas"][d])
                              for d in DIMENSIONS)
            L.append(f"{n[:width]:<{width}} {str(s['round']):>3}  {cells}"
                     f"  {s['clean_streak']:>3}  {s['verdict']}")
        L.append("")

    for n in names:
        s = report["subsystems"][n]
        lines = []
        for d, a, b in s["regressions"]:
            tail = f"  WAIVED: {s['waiver']}" if s["waiver"] else ""
            lines.append(f"  REGRESSION  {d} {a} -> {b}{tail}")
        for f in s["findings"]:
            if f.get("severity") == "note":
                lines.append(f"  note        {f.get('text')}")
            else:
                where = f"  [{f['where']}]" if f.get("where") else ""
                lines.append(f"  {f.get('severity','?'):<11} "
                             f"{f.get('descriptor','--')} {f.get('text')}{where}")
        if s["capped"]:
            lines.append(f"  CAPPED      {s['cap_reason']}")
        if s["over_cap"]:
            lines.append(f"  OVER CAP    {s['rounds_used']} rounds used; "
                         f"cap it with a reason or decide to raise the cap")
        if lines:
            L.append(f"{n}:")
            L.extend(lines)
            L.append("")

    ship = [n for n in names if report["subsystems"][n]["verdict"] in
            ("SHIP", "SHIPPED")]
    capped = [n for n in names if report["subsystems"][n]["capped"]]
    active = [n for n in names if n not in ship and n not in capped]

    L.append(f"{len(ship)} at the bar, {len(capped)} capped (decision owed), "
             f"{len(active)} still active")
    if active:
        L.append("continue: " + ", ".join(
            f"{n} ({', '.join(report['subsystems'][n]['shortfall']) or 'needs a clean round'})"
            for n in active))
    if capped:
        L.append("decisions owed to the owner:")
        for n in capped:
            L.append(f"  {n}: {report['subsystems'][n]['cap_reason']}")

    fails = failures(report, strict)
    L.append("")
    if fails:
        L.append(f"GATE FAILED -- {len(fails)} reason(s)")
        for f in fails:
            L.append(f"  x {f}")
    else:
        # Deliberately not "GATE PASSED: everything is AAA". Without --strict
        # this gate only asserts that nothing went backwards and the scorecard
        # is honest about its own shape. Seven subsystems can be at CRAFT 1 and
        # still pass it, and that must not read as approval.
        L.append("GATE PASSED -- no regression, no structural problem"
                 + ("" if active else "; nothing is owed another round"))
    L.append("")
    L.append("This gate scores the scorecard. It says nothing about framerate, "
             "motion, audio\nor how the thing feels to play -- see "
             "'What this rubric cannot judge' in\ndocs/AAA-STANDARD.md.")
    return L


TEMPLATE = {
    "version": 1,
    "bar": dict(DEFAULT_BAR),
    "subsystems": {
        "example_subsystem": {
            "status": "active",
            "rounds": [
                {
                    "round": 1,
                    "reviewer": "who reviewed it",
                    "date": "YYYY-MM-DD",
                    "scores": {"craft": 3, "fidelity": 4,
                               "performance": 4, "robustness": 2},
                    "evidence": {
                        "fidelity": "measured against <file> at <calibration>",
                        "performance": "budget.py worst case N/M tri (P%)",
                    },
                    "broke_assertions": False,
                    "what_is_good": [
                        "what already works and must not be broken fixing the "
                        "findings below",
                    ],
                    "findings": [
                        {"severity": "major", "dimension": "craft",
                         "descriptor": "C3",
                         "where": "station/<module>.py:<function>",
                         "text": "what specifically is wrong"},
                        {"severity": "major", "dimension": "robustness",
                         "descriptor": "R2",
                         "text": "assertions are per-instance, not per-class"},
                        {"severity": "minor", "dimension": "craft",
                         "descriptor": "C4",
                         "text": "true, specific, moves nothing below the bar"},
                        {"severity": "note",
                         "text": "a preference; never blocks"},
                    ],
                }
            ],
        }
    },
}


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------

def _mk_round(n, scores, findings=(), evidence=None, min_score=4, **kw):
    """Build a round that is structurally valid by construction.

    Auto-fills the evidence a score at the bar requires and the explaining
    finding a score below the bar requires, so that a test aimed at one rule is
    not tripped by another. Tests of those two rules pass explicit values.
    """
    scores = dict(scores)
    ev = dict(evidence) if evidence else {}
    fs = list(findings)
    explained = {f.get("dimension") for f in fs
                 if f.get("severity") in RESETTING}
    for d in DIMENSIONS:
        s = scores.get(d)
        if _is_int(s) and s >= min_score and d not in ev:
            ev[d] = f"auto: {d} evidence"
        if _is_int(s) and s < min_score and d not in explained:
            fs.append({"severity": "major", "dimension": d,
                       "descriptor": f"{DIM_LETTER[d]}{s}",
                       "text": f"auto: {d} below the bar"})
    r = {"round": n, "scores": scores, "evidence": ev, "findings": fs}
    if scores.get("robustness") == 5:
        r.setdefault("broke_assertions", True)
    r.update(kw)
    return r


def _card(rounds, name="sub", bar=None, **sub):
    c = {"version": 1, "bar": dict(bar or DEFAULT_BAR),
         "subsystems": {name: dict(rounds=list(rounds), **sub)}}
    return c


AT_BAR = {"craft": 4, "fidelity": 4, "performance": 4, "robustness": 4}


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    def errs(card):
        return validate(card)

    def has(card, needle):
        return any(needle in e for e in validate(card))

    # --- structure: a well-formed card produces no errors -------------------
    good = _card([_mk_round(1, AT_BAR), _mk_round(2, AT_BAR)])
    check("a well-formed scorecard validates clean", errs(good) == [],
          str(errs(good)))

    # --- structure: score domain -------------------------------------------
    # The class is "a score that is not an integer 0-5 must never reach the
    # dashboard". `true` is the interesting member: JSON true parses to a bool,
    # bool is a subclass of int, and it would otherwise be scored as 1.
    #
    # The two guards are asserted against their OWN message. Matching either
    # message would let one guard cover for the other, and mutation showed that
    # is exactly what happened when both tests matched on "craft score".
    for bad, label in ((6, "6"), (-1, "-1")):
        c = _card([_mk_round(1, dict(AT_BAR, craft=bad))])
        check(f"score {label} is rejected as out of range",
              has(c, f"craft score {bad} outside 0-5"), str(errs(c)))
    for bad, label in ((True, "true"), ("4", '"4"'), (3.5, "3.5"),
                       (None, "null")):
        c = _card([_mk_round(1, dict(AT_BAR, craft=bad))])
        check(f"score {label} is rejected as not an integer",
              has(c, "is not an integer"), str(errs(c)))

    c = _card([{"round": 1, "scores": {"craft": 4, "fidelity": 4,
                                       "performance": 4}}])
    check("a missing dimension is rejected", has(c, "missing dimension"))
    c = _card([_mk_round(1, dict(AT_BAR, sound=4))])
    check("an unknown dimension is rejected", has(c, "unknown dimension"))

    # --- severity: `resolved` -----------------------------------------------
    # A closure record. It must be sayable on a round that now scores at the
    # bar -- that is the whole situation it exists for -- and it must NOT be a
    # way to file an open defect where nothing counts it.
    RES = {"severity": "resolved", "dimension": "craft", "descriptor": "C2",
           "text": "round 1's C2 is answered: <what changed and how measured>"}
    c = _card([_mk_round(1, AT_BAR, findings=[RES])])
    check("a resolved closure is accepted at the bar", not errs(c), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, findings=[RES])])
    check("a resolved closure does not reset the clean-round counter",
          not has(c, "at or above the bar, with a major"), str(errs(c)))
    # Built by hand: _mk_round auto-fills the explaining major, which is
    # exactly the thing under test here.
    c = _card([{"round": 1, "scores": dict(AT_BAR, craft=2),
                "evidence": {d: "e" for d in DIMENSIONS if d != "craft"},
                "findings": [RES]}])
    check("a resolved closure does not explain a below-bar score",
          has(c, "craft scored 2, below the bar, with no major"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, findings=[dict(RES, descriptor="R2")])])
    check("a resolved closure still has to name a real descriptor for its dim",
          has(c, "is a robustness descriptor on a craft finding"),
          str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, findings=[dict(RES, descriptor="-")])])
    check("a resolved closure with no descriptor is rejected",
          has(c, "is not [CFPR][0-5]"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, findings=[dict(RES, text="")])])
    check("a resolved closure with no text is rejected", has(c, "no text"),
          str(errs(c)))
    c = _card([_mk_round(1, AT_BAR)])
    c["subsystems"]["sub"]["rounds"][0]["evidence"]["frames"] = ["a.png"]
    check("evidence under a non-dimension key is rejected",
          has(c, "evidence for unknown dimension"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR)])
    c["subsystems"]["sub"]["rounds"][0]["evidence"]["_frames"] = ["a.png"]
    check("shared evidence under the documentation prefix is allowed",
          not has(c, "evidence for unknown dimension"), str(errs(c)))
    # ...and it is not a way to give a dimension evidence it does not have.
    c = _card([_mk_round(1, AT_BAR)])
    ev = c["subsystems"]["sub"]["rounds"][0]["evidence"]
    del ev["craft"]
    ev["_craft_notes"] = "measured over there"
    check("prefixed evidence does not satisfy a dimension's own evidence",
          has(c, "craft scored"), str(errs(c)))

    # --- structure: evidence and the robustness-5 claim ---------------------
    c = _card([{"round": 1, "scores": dict(AT_BAR), "evidence": {},
                "findings": []}])
    check("a score at the bar with no evidence is rejected",
          has(c, "with no evidence"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, robustness=5))])
    del c["subsystems"]["sub"]["rounds"][0]["broke_assertions"]
    check("robustness 5 without broke_assertions is rejected",
          has(c, "broke_assertions"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, robustness=5))])
    check("robustness 5 with broke_assertions validates", errs(c) == [],
          str(errs(c)))

    # --- structure: findings must point at a descriptor ---------------------
    def finding(**kw):
        f = {"severity": "major", "dimension": "craft", "descriptor": "C2",
             "text": "t"}
        f.update(kw)
        return f

    c = _card([_mk_round(1, dict(AT_BAR, craft=2), [finding(severity="grave")])])
    check("an unknown severity is rejected", has(c, "severity"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=2),
                         [finding(descriptor="R2")])])
    check("a descriptor whose letter contradicts its dimension is rejected",
          has(c, "descriptor R2 is a"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=2),
                         [{"severity": "major", "dimension": "craft",
                           "text": "t"}])])
    check("a major with no descriptor is rejected", has(c, "descriptor"),
          str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=2),
                         [finding(descriptor="C9")])])
    check("a descriptor outside 0-5 is rejected", has(c, "descriptor"),
          str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, [{"severity": "note", "text": "taste"}])])
    check("a note needs no descriptor", errs(c) == [], str(errs(c)))

    # Severity must agree with the descriptor in BOTH directions. This is the
    # anti-inflation rule that keeps a harsh critic from calling a preference a
    # major, and the anti-deflation rule that keeps a real defect from being
    # filed as a minor so a subsystem can ship.
    #
    # The card below scores craft BELOW the bar deliberately, so that the
    # score/finding coupling rule stays silent and the only thing that can
    # reject it is the inflation rule itself. Written the obvious way -- craft
    # at the bar -- the coupling rule fires too and the assertion passes with
    # the inflation rule deleted, which is what mutating the source revealed.
    c = _card([_mk_round(1, dict(AT_BAR, craft=2),
                         [finding(descriptor="C4")])])
    check("a major citing an at-bar descriptor is rejected",
          has(c, "cites C4, which is at or above"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=3),
                         [finding(descriptor="C1")])])
    check("a finding citing a lower descriptor than the score is rejected",
          has(c, "cites C1 but craft is scored 3"), str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=2),
                         [finding(), {"severity": "minor",
                                      "dimension": "fidelity",
                                      "descriptor": "F2", "text": "t"}])])
    check("a minor citing a below-bar descriptor is rejected",
          has(c, "that is a major"), str(errs(c)))

    # --- structure: scores and findings must agree --------------------------
    c = _card([{"round": 1, "scores": dict(AT_BAR, craft=2),
                "evidence": {d: "e" for d in DIMENSIONS}, "findings": []}])
    check("a below-bar score with nothing explaining it is rejected",
          has(c, "with no major"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR, [finding(dimension="fidelity",
                                             descriptor="F2")])])
    check("a major against a dimension scored at the bar is rejected",
          has(c, "at or above the bar, with a major"), str(errs(c)))

    # --- structure: rounds are a sequence -----------------------------------
    c = _card([_mk_round(1, AT_BAR), _mk_round(1, AT_BAR)])
    check("a repeated round number is rejected", has(c, "does not follow"),
          str(errs(c)))
    c = _card([_mk_round(2, AT_BAR), _mk_round(1, AT_BAR)])
    check("a decreasing round number is rejected", has(c, "does not follow"))
    c = _card([])
    check("a subsystem with no rounds is rejected", has(c, "rounds missing"))
    c = _card([_mk_round(1, AT_BAR)])
    c["subsystems"]["sub"]["rounds"][0]["finding"] = []
    check("a misspelled round key is rejected", has(c, "unknown key"),
          str(errs(c)))

    # An underscore prefix marks provenance a merging agent has to keep -- and
    # the allowance is narrow on purpose, because the one thing it must never
    # let through is a key that shadows a real one. `_findings` beside no
    # `findings` is a round whose findings have silently vanished, which reads
    # as a clean round.
    c = _card([_mk_round(1, AT_BAR)])
    c["subsystems"]["sub"]["_merge_note"] = "merged from an agent's file"
    c["subsystems"]["sub"]["rounds"][0]["_frames"] = {"normal": "a.png"}
    check("an underscored documentation key is allowed",
          not has(c, "unknown key"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR)])
    del c["subsystems"]["sub"]["rounds"][0]["findings"]
    c["subsystems"]["sub"]["rounds"][0]["_findings"] = []
    check("an underscored key that shadows a real one is rejected",
          has(c, "unknown key '_findings'"), str(errs(c)))
    c = _card([_mk_round(1, AT_BAR)])
    c["subsystems"]["sub"]["rounds"][0]["__scores"] = {}
    check("underscores do not stack their way past the shadow rule",
          has(c, "unknown key '__scores'"), str(errs(c)))

    # --- structure: caps and waivers ----------------------------------------
    c = _card([_mk_round(1, dict(AT_BAR, craft=2))], status="capped")
    check("a cap with no reason is rejected", has(c, "no cap_reason"),
          str(errs(c)))
    c = _card([_mk_round(1, dict(AT_BAR, craft=2))], status="capped",
              cap_reason="craft 2: components are box primitives")
    check("a cap with a reason validates", errs(c) == [], str(errs(c)))
    c = _card([_mk_round(1, AT_BAR),
               _mk_round(2, AT_BAR, regression_waiver="none happened")])
    check("a waiver with no regression is rejected",
          has(c, "no regression"), str(errs(c)))

    # --- the bar ------------------------------------------------------------
    # THE rule: one clean round is not enough. Both cards below are at the bar
    # in every dimension; only the two-round one may stop.
    one = evaluate(_card([_mk_round(1, AT_BAR)]))["subsystems"]["sub"]
    two = evaluate(good)["subsystems"]["sub"]
    check("one clean round at the bar does not ship", not one["shippable"],
          str(one))
    check("two clean rounds at the bar ship", two["shippable"], str(two))
    check("one clean round still reports at_bar", one["at_bar"])

    # A minor finding must not reopen a subsystem -- otherwise the loop has no
    # bottom, which is the failure this whole rubric exists to prevent.
    minors = [{"severity": "minor", "dimension": "craft", "descriptor": "C4",
               "text": "a true, specific, non-blocking observation"}]
    m = evaluate(_card([_mk_round(1, AT_BAR, minors),
                        _mk_round(2, AT_BAR, minors)]))["subsystems"]["sub"]
    check("minor findings do not reset the clean-round count",
          m["shippable"] and m["clean_streak"] == 2, str(m))

    # Asserted on _round_is_clean directly. Written the obvious way -- round 1
    # at the bar, round 2 with a major -- the drop from 4 to 3 is ALSO a
    # regression, so the assertion passes with the major rule deleted. Round 0
    # has no predecessor, so nothing but the finding can make it unclean.
    check("a round carrying a major finding is not clean",
          not _round_is_clean([_mk_round(1, dict(AT_BAR, craft=3))], 0))
    check("a round with no finding above minor is clean",
          _round_is_clean([_mk_round(1, AT_BAR, minors)], 0))
    streak = evaluate(_card([
        _mk_round(1, dict(AT_BAR, craft=3)),
        _mk_round(2, dict(AT_BAR, craft=3)),   # no regression: 3 -> 3
        _mk_round(3, AT_BAR),
    ]))["subsystems"]["sub"]
    check("majors reset the count, so a fix leaves a streak of one",
          streak["clean_streak"] == 1 and not streak["shippable"],
          str(streak))

    # A below-bar score must not ship even when the scorecard is malformed and
    # carries nothing explaining it. On a VALID card the coupling rule makes
    # this unreachable -- a below-bar score always carries a major, so the
    # round is never clean -- which is why the obvious version of this test is
    # vacuous. evaluate() runs on malformed cards too, so the guard is real.
    sloppy_round = {"scores": dict(AT_BAR, robustness=1),
                    "evidence": {d: "e" for d in DIMENSIONS}, "findings": []}
    below = evaluate(_card([dict(sloppy_round, round=1),
                            dict(sloppy_round, round=2)]))["subsystems"]["sub"]
    check("a below-bar score does not ship even with nothing explaining it",
          not below["shippable"] and below["clean_streak"] == 2, str(below))
    check("the shortfall names the failing dimension",
          below["shortfall"] == ["robustness"], str(below["shortfall"]))

    # --- regression ---------------------------------------------------------
    # The class: a drop is a failure REGARDLESS of the absolute level. A critic
    # looking at one snapshot cannot see this and a rubric can.
    r = _card([_mk_round(1, dict(AT_BAR, craft=5)), _mk_round(2, AT_BAR)])
    rep = evaluate(r)
    check("a drop from 5 to 4 is a regression even though 4 is at the bar",
          rep["subsystems"]["sub"]["regressions"] == [("craft", 5, 4)],
          str(rep["subsystems"]["sub"]["regressions"]))
    check("a regression fails the gate", failures(rep) != [], str(failures(rep)))
    check("a regression is the verdict",
          rep["subsystems"]["sub"]["verdict"] == "REGRESSED")

    r2 = _card([_mk_round(1, AT_BAR), _mk_round(2, dict(AT_BAR, fidelity=5))])
    check("an improvement is not a regression", failures(evaluate(r2)) == [],
          str(failures(evaluate(r2))))
    check("the delta is reported",
          evaluate(r2)["subsystems"]["sub"]["deltas"]["fidelity"] == 1)

    r3 = _card([_mk_round(1, dict(AT_BAR, craft=5)),
                _mk_round(2, AT_BAR,
                          regression_waiver="rescored against the new "
                                            "descriptor set")])
    rep3 = evaluate(r3)
    check("a waived regression does not fail the gate",
          failures(rep3) == [], str(failures(rep3)))
    check("a waived regression is still not a clean round",
          not rep3["subsystems"]["sub"]["shippable"]
          and rep3["subsystems"]["sub"]["clean_streak"] == 0,
          str(rep3["subsystems"]["sub"]))

    # --- the hard stop ------------------------------------------------------
    over = _card([_mk_round(n, dict(AT_BAR, craft=2)) for n in range(1, 6)],
                 bar=dict(DEFAULT_BAR, max_rounds=4))
    repo = evaluate(over)
    check("exceeding max_rounds without reaching the bar fails the gate",
          any("rounds used" in f for f in failures(repo)), str(failures(repo)))
    check("exceeding max_rounds is the verdict",
          repo["subsystems"]["sub"]["verdict"] == "OVER-CAP")

    capped = _card([_mk_round(n, dict(AT_BAR, craft=2)) for n in range(1, 6)],
                   bar=dict(DEFAULT_BAR, max_rounds=4), status="capped",
                   cap_reason="craft 2: cobra bays are box primitives; "
                              "raising it needs reference we do not hold")
    repc = evaluate(capped)
    check("a capped subsystem stops the loop instead of failing it",
          failures(repc) == [] and repc["subsystems"]["sub"]["verdict"]
          == "CAPPED", str(failures(repc)))
    check("a capped subsystem is listed as a decision owed",
          any("decisions owed" in ln for ln in format_report(repc)))

    # --- strict mode --------------------------------------------------------
    b = _card([_mk_round(1, dict(AT_BAR, robustness=1))])
    check("a below-bar subsystem passes without --strict",
          failures(evaluate(b)) == [], str(failures(evaluate(b))))
    check("a below-bar subsystem fails with --strict",
          failures(evaluate(b), strict=True) != [])
    check("a shipped subsystem passes --strict",
          failures(evaluate(good), strict=True) == [],
          str(failures(evaluate(good), strict=True)))

    # --- determinism --------------------------------------------------------
    # The class: dict insertion order must never reach the output. Python dicts
    # preserve insertion order, so an unsorted iteration would make the report
    # depend on the order a reviewer happened to type the subsystems in.
    #
    # evaluate() and format_report() are asserted SEPARATELY. The end-to-end
    # comparison alone is vacuous: it survives either one of them dropping its
    # sort, because whichever still sorts covers for the other. Mutating the
    # source is how that was found.
    names3 = ("zocalo", "drum_ground", "cobra_bays")
    a_card = {"version": 1, "bar": dict(DEFAULT_BAR), "subsystems": {}}
    b_card = {"version": 1, "bar": dict(DEFAULT_BAR), "subsystems": {}}
    for n in names3:
        a_card["subsystems"][n] = {"rounds": [_mk_round(1, AT_BAR),
                                              _mk_round(2, AT_BAR)]}
    # reversed(), not sorted(reverse=True) -- names3 happens to already BE its
    # own reverse-sorted order, so the second card was being built in the same
    # insertion order as the first and the comparison compared nothing.
    for n in reversed(names3):
        b_card["subsystems"][n] = {"rounds": [_mk_round(1, AT_BAR),
                                              _mk_round(2, AT_BAR)]}
    rep_a, rep_b = evaluate(a_card), evaluate(b_card)
    check("evaluate() emits subsystems in sorted order",
          list(rep_a["subsystems"]) == sorted(names3)
          and list(rep_b["subsystems"]) == sorted(names3),
          f"{list(rep_a['subsystems'])} / {list(rep_b['subsystems'])}")

    # Hand-build a report whose subsystems are in reverse order, so this
    # assertion reaches format_report() even when evaluate() is sorting.
    shuffled = {"bar": rep_a["bar"], "errors": [], "subsystems": {
        n: rep_a["subsystems"][n]
        for n in sorted(rep_a["subsystems"], reverse=True)}}
    check("format_report() emits subsystems in sorted order",
          format_report(shuffled) == format_report(rep_a))
    check("the report does not depend on key insertion order",
          format_report(rep_a) == format_report(rep_b))
    check("all three subsystems reach the report",
          len(rep_a["subsystems"]) == 3)

    # --- overall verdict ----------------------------------------------------
    mixed = {"version": 1, "bar": dict(DEFAULT_BAR), "subsystems": {
        "done": {"rounds": [_mk_round(1, AT_BAR), _mk_round(2, AT_BAR)]},
        "open": {"rounds": [_mk_round(1, dict(AT_BAR, craft=2))]},
    }}
    lines = format_report(evaluate(mixed))
    check("the dashboard names what still needs work",
          any(ln.startswith("continue: ") and "open" in ln for ln in lines),
          str([ln for ln in lines if ln.startswith("continue")]))
    check("the dashboard does not list a shipped subsystem as continuing",
          not any(ln.startswith("continue: ") and "done" in ln
                  for ln in lines))
    allgood = format_report(evaluate(good))
    check("a fully clean board says nothing is owed another round",
          any("nothing is owed" in ln for ln in allgood))

    # --- the shipped template is itself valid -------------------------------
    check("the --template skeleton is a valid scorecard",
          validate(TEMPLATE) == [], str(validate(TEMPLATE)))

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


def main(argv):
    args = [a for a in argv[1:]]
    if "--template" in args:
        print(json.dumps(TEMPLATE, indent=2, sort_keys=True))
        return 0
    strict = "--strict" in args
    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        return _selftest()
    path = paths[0]
    if not os.path.exists(path):
        print(f"no scorecard at {path}\n"
              f"start one with:  python3 tools/aaa_gate.py --template")
        return 1
    try:
        card = json.load(open(path))
    except json.JSONDecodeError as exc:
        print(f"{path} is not valid JSON: {exc}")
        return 1
    report = evaluate(card)
    print("\n".join(format_report(report, path, strict)))
    return 1 if failures(report, strict) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
