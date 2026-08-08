#!/usr/bin/env python3
"""Does every resident aboard have a name, and is it theirs to wear?

WHY THIS EXISTS RATHER THAN A WIDER CAST-01. `station/spec_harness/cast.py`
already asks part of question 3, and it shipped a build with 43 violations in
it, because of one line:

    for i in range(2000):
        sur, fore = res._split_name("human", str(i))

Two defects in one loop, and they are the two this project keeps producing.
**It samples the wrong id space** -- the shipped ids are
`res:b5:<place>:<species>:<i>` (see `resident.pool_id`), not `"0".."1999"`, so
its 28 findings and the build's 29 were disjoint populations that happened to
have similar counts. And **it samples humans only**, so fourteen alien
collisions -- a Narn called G'Kar, two Minbari called Delenn, two Centauri
called Londo Mollari -- were invisible to every gate in the repository.

WHAT THIS ASKS, and each one can fail on content this repo has shipped:

  A  NO EMPTY NAME. Every species in `schedule.STATION_COUNTS`, in
     `body.SPECIES` and in the packaged census has a grammar, and a resident
     drawn for it comes back with a non-empty identicard NAME. `--legacy`
     restores the pre-INV-1249 behaviour and reports what the build shipped.

  B  NO UNMARKED GRAMMAR. Every grammar's species is named in an
     `canon/INVENTIONS.md` entry. Hard rule 1 forbids unmarked invention, and
     seven grammars' worth of names is a large thing to leave unlogged. Read
     out of the file, so deleting the entry fails the gate.

  C  NO RESERVED NAME, PROVED THREE WAYS rather than sampled once:
       C1  the rule is ON THE PATH -- `_pick_clear` is instrumented and every
           non-closed grammar's `build` is CALLED. A static scan can say a
           caller exists; only running it says the caller runs.
       C2  given C1, the reachable set is the vocabulary minus the reserved
           names, so the gate reports how many show-cast names each grammar
           could spell and no longer can. That number is the gate's own
           negative control: if it were zero the check would be vacuous.
       C3  and the shipped id space is drawn from anyway, per species, because
           a proof about a grammar is not a proof about a spawner.

  D  THE GRAMMARS STAY DISTINGUISHABLE. This file's founding claim is that "a
     Narn name and a Centauri name are never mistakable for each other", and
     fifteen grammars is where that starts to be work. Pairwise-disjoint over
     the full vocabularies, not over a sample. `other` is exempt and says so --
     it is a distribution OVER the other grammars, so overlap is its
     definition.

Seconds, no build, no GPU, no `station/generated/` read. Safe to run while
agents work -- which matters, because the gates that would have caught this are
the ones nobody runs mid-session.

    python3 tools/cast_gate.py              # the gate
    python3 tools/cast_gate.py --legacy     # the same questions, rule removed
    python3 tools/cast_gate.py --packaged D # measure a packaged build instead
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "station"), os.path.join(ROOT, "station", "npc")):
    if p not in sys.path:
        sys.path.insert(0, p)

# BARE IMPORTS, AND THE REASON IS A TRAP THIS GATE FELL INTO ON ITS FIRST RUN.
# `station/npc` is on `sys.path` AND `station/npc/__init__.py` exists, so
# `import names` and `from npc import names` load the SAME FILE into TWO
# module objects with two `GRAMMARS` dicts and two `RESERVED` sets. This file
# was written with `from npc import ...`; `resident.py` uses bare `import
# names`; and `--legacy`, which deletes grammars to prove the gate can fail,
# deleted them from a copy nothing runs. It reported "0 of 840 blank" for a
# build with no grammars in it -- a green number that meant nothing, produced
# by the check written to stop exactly that.
#
# The import style is half the fix. `_same_module_as_the_build_uses()` is the
# other half, because a future edit can reintroduce it silently.
import names as nm                                               # noqa: E402
import resident as res                                           # noqa: E402
import schedule as sched                                         # noqa: E402
import body as npc_body                                          # noqa: E402

DRAWS = 400          # ids sampled per species from the shipped id space
PLACES = ("zocalo", "docking_bays", "black_market", "standard_corridor",
          "mess_hall", "security_central")

_results = []


def check(name, ok, detail=""):
    _results.append((name, bool(ok)))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    return ok


# ---------------------------------------------------------------------------
# the id space the build actually uses
# ---------------------------------------------------------------------------
def shipped_ids(species, n=DRAWS):
    """Ids in the form the spawner mints them.

    NOT `str(i)`. `resident.pool_id` is the one function that builds these and
    it is called rather than imitated, so this cannot drift from the spawner
    the way the CAST-01 loop did.
    """
    out = []
    i = 0
    while len(out) < n:
        out.append(res.pool_id(PLACES[i % len(PLACES)], species, i, "b5"))
        i += 1
    return out


def census_species():
    """Every species string a shipped resident can carry.

    Union of three sources rather than one, because they disagree: the census
    (`STATION_COUNTS`) has no vorlon row (Kosh is authored), `body.SPECIES`
    has vorlon and `other`, and `RHYTHMS` is keyed differently again. A species
    missing from any of them is exactly how one would ship unnamed.
    """
    return (set(sched.STATION_COUNTS) | set(npc_body.SPECIES)
            | set(sched.RHYTHMS)) - {"vorlon"}


# ---------------------------------------------------------------------------
# A -- nobody ships without a name
# ---------------------------------------------------------------------------
def gate_a(legacy):
    print("\n== A  every resident aboard has a name ==")
    # THE PRECONDITION FIRST. Everything below reads `nm`; `resident` names
    # people out of `res.npc_names`. If those are two module objects -- and
    # they were, until this line -- then every measurement here is of a copy
    # nothing runs, and `--legacy` cannot fail because it edits the wrong dict.
    check("the gate and the spawner share one names module",
          res.npc_names is nm,
          f"{nm.__name__} vs {res.npc_names.__name__}"
          + ("" if res.npc_names is nm else
             " -- MEASURING A COPY; every number below is meaningless"))
    missing_grammar = sorted(s for s in census_species() if s not in nm.GRAMMARS)
    check("every species aboard has a naming grammar",
          not missing_grammar,
          f"{len(census_species())} species aboard, "
          + (f"NO GRAMMAR for {missing_grammar}" if missing_grammar
             else "all 14 covered"))

    blank = collections.Counter()
    total = 0
    for sp in sorted(census_species()):
        for nid in shipped_ids(sp, 60):
            total += 1
            try:
                r = res.resident(nid, sp)
                nmv = dict((k, v) for k, v, _s in res.identicard(r))["NAME"]
            except KeyError:
                nmv = ""
            if not nmv:
                blank[sp] += 1
    # THE PERCENTAGE HERE IS NOT THE SHIPPED PERCENTAGE and must not be quoted
    # as one: this draws 60 ids per species UNIFORMLY, so `--legacy` reports
    # 57.1% where the packaged build carried 12.1%. The difference is entirely
    # population weighting -- 2,438 of the build's 3,683 residents are human.
    # `--packaged` gives the weighted figure; this one gives the per-species
    # answer, which is what the assertion is about.
    pct = 100.0 * sum(blank.values()) / max(total, 1)
    check("no identicard ships with an empty NAME field",
          not blank,
          f"{sum(blank.values())} of {total} blank ({pct:.1f}% of a UNIFORM "
          f"per-species draw, not of the station)"
          + (f" -- {dict(blank)}" if blank else ""))
    return total


# ---------------------------------------------------------------------------
# B -- no grammar is unmarked invention
# ---------------------------------------------------------------------------
def gate_b():
    print("\n== B  every grammar is a LOGGED extrapolation ==")
    text = open(os.path.join(ROOT, "canon", "INVENTIONS.md"),
                encoding="utf-8").read()
    # Entries that are ABOUT naming. Matched on the heading, then the species
    # is looked for in that entry's own body -- a species name appearing
    # somewhere in a 5,000-entry file proves nothing.
    blocks = re.split(r"^## (INV-\d+)", text, flags=re.M)
    naming = {}
    for i in range(1, len(blocks), 2):
        inv, body = blocks[i], blocks[i + 1]
        head = body.split("\n", 1)[0].lower()
        if "name" in head or "naming" in head:
            # APOSTROPHES STRIPPED, because the code key and the readable form
            # differ for exactly one species and FACTIONS.md 9.2 says so in as
            # many words: "`schedule.py`'s key is `pakmara` and the show's own
            # usage is generally lowercase `pak'ma'ra`". Searching for the key
            # alone reported INV-004 as not covering pak'ma'ra, which it plainly
            # does -- a spelling difference the repo has already ruled on is not
            # a missing entry.
            naming[inv] = body.lower().replace("'", "").replace("’", "")
    unlogged = []
    for sp in sorted(nm.GRAMMARS):
        if not any(sp in b for b in naming.values()):
            unlogged.append(sp)
    check("every naming grammar is named inside a naming INVENTIONS entry",
          not unlogged,
          f"{len(naming)} naming entries ({', '.join(sorted(naming))})"
          + (f"; UNLOGGED: {unlogged}" if unlogged else ""))


# ---------------------------------------------------------------------------
# C -- the reserved cast
# ---------------------------------------------------------------------------
def gate_c(legacy):
    print("\n== C  no background extra wears a show character's name ==")

    # C1 -- the rule is on the path, PROVED BY CALLING IT.
    seen = set()
    real = nm._pick_clear

    def spy(seq, seed, salt, finish):
        seen.add(_current[0])
        return real(seq, seed, salt, finish)

    _current = [None]
    nm._pick_clear = spy
    try:
        for sp, g in nm.GRAMMARS.items():
            if g.closed or sp == "other":
                continue
            _current[0] = sp
            g.build("probe-id-1")
    finally:
        nm._pick_clear = real
    want = {s for s, g in nm.GRAMMARS.items() if not g.closed and s != "other"}
    check("every open grammar RUNS the reservation rule when it builds a name",
          seen == want,
          f"{len(seen)} of {len(want)} reached _pick_clear"
          + (f"; MISSING {sorted(want - seen)}" if want - seen else ""))

    # C2 -- what the vocabularies could spell, and what the rule removes.
    # `other` is a union of the rest, and a closed grammar keeps its attested
    # names on purpose -- neither belongs in a count of what the rule REMOVED.
    spellable = {s: nm.all_names(s) & nm.RESERVED for s in nm.GRAMMARS
                 if s != "other" and not nm.GRAMMARS[s].closed}
    hazard = sum(len(v) for v in spellable.values())
    check("the check is not vacuous: the vocabularies CAN spell the cast",
          hazard > 0,
          f"{hazard} reserved names are constructible across "
          f"{sum(1 for v in spellable.values() if v)} grammars and the rule "
          "makes every one unreachable -- "
          + "; ".join(f"{k}:{len(v)}" for k, v in sorted(spellable.items()) if v))

    # C3 -- and the shipped id space, drawn for real.
    worn = []
    for sp in sorted(census_species()):
        for nid in shipped_ids(sp):
            try:
                n = res.resident(nid, sp).name
            except KeyError:
                continue
            if n in nm.RESERVED:
                worn.append((sp, nid, n))
    drawn = len(census_species()) * DRAWS
    check("no resident drawn from the SHIPPED id space wears a reserved name",
          not worn,
          f"{len(worn)} of {drawn} draws"
          + (f" -- e.g. {worn[0][2]!r} as a {worn[0][0]} ({worn[0][1]})"
             if worn else ""))

    # And the exemption is safe rather than assumed.
    closed = [s for s, g in nm.GRAMMARS.items() if g.closed]
    check("the one grammar exempt from the rule is never sampled aboard",
          all(s not in sched.STATION_COUNTS for s in closed),
          f"closed: {closed}; STATION_COUNTS has "
          f"{[s for s in closed if s in sched.STATION_COUNTS] or 'none of them'}")


# ---------------------------------------------------------------------------
# D -- fifteen grammars stay fifteen grammars
# ---------------------------------------------------------------------------
def gate_d():
    print("\n== D  the grammars stay distinguishable ==")
    sp = [s for s in sorted(nm.GRAMMARS) if s != "other"]
    vocab = {s: nm.reachable_names(s) for s in sp}
    clashes = []
    for i, a in enumerate(sp):
        for b in sp[i + 1:]:
            both = vocab[a] & vocab[b]
            if both:
                clashes.append((a, b, sorted(both)[:3]))
    check("no two species can produce the same name",
          not clashes,
          f"{len(sp)} grammars, "
          f"{sum(len(v) for v in vocab.values())} reachable names"
          + (f"; CLASH {clashes[:3]}" if clashes else ""))

    # Variety, against the population each grammar has to name. Not a fixed
    # threshold: the bar is the one this file already meets for Narn, whose
    # reachable names cover 22,500 people. Anything coarser reads as repetition
    # where Narn does not.
    #
    # THE ASSERTION IS SCOPED TO THE SEVEN THIS SESSION ADDED, AND THE REST IS
    # REPORTED RATHER THAN ASSERTED -- which is a decision, not a dodge. Run
    # unscoped, this check fails on `human` (519 names for 155,000 people, 1 per
    # 299) and `drazi` (59 for 12,500, 1 per 212), both of which predate
    # INV-1249 by many sessions. Asserting on them would make a gate about
    # unnamed species fail for a reason it did not cause, which is how a gate
    # gets switched off; leaving the number unprinted would be worse. So it is
    # printed every run, with its own heading, as a standing finding.
    added = ("brakiri", "vree", "abbai", "gaim", "hyach", "llort", "grome")
    narn_ratio = sched.STATION_COUNTS["narn"] / len(vocab["narn"])
    ratios = {s: sched.STATION_COUNTS[s] / len(vocab[s])
              for s in sp if sched.STATION_COUNTS.get(s)}
    thin_new = [(s, sched.STATION_COUNTS[s], len(vocab[s]), round(ratios[s]))
                for s in added if s in ratios and ratios[s] > narn_ratio]
    present = [s for s in added if s in ratios]
    # A CHECK WITH AN EMPTY SUBJECT IS NOT A PASS. In `--legacy` the seven do
    # not exist, and an earlier version of this line printed PASS over an empty
    # list -- the vacuous green this file's own docstring is about.
    check("every grammar INV-1249 adds is finer-grained than the Narn one",
          len(present) == len(added) and not thin_new,
          f"Narn is 1 name per {narn_ratio:.0f} people; "
          + (", ".join(f"{s} 1/{ratios[s]:.0f}" for s in present)
             if present else "NONE OF THE SEVEN EXIST")
          + (f"; COARSER: {thin_new}" if thin_new else "")
          + (f"; MISSING {sorted(set(added) - set(present))}"
             if len(present) != len(added) else ""))
    pre = [(s, sched.STATION_COUNTS[s], len(vocab[s]), round(ratios[s]))
           for s in ratios if s not in added and ratios[s] > narn_ratio]
    if pre:
        print("  NOTE  pre-existing grammars coarser than Narn, NOT asserted on "
              "and NOT fixed here: "
              + "; ".join(f"{s} {p:,} people / {v} names = 1 per {r}"
                          for s, p, v, r in sorted(pre)))


# ---------------------------------------------------------------------------
# the legacy control -- the build as it shipped
# ---------------------------------------------------------------------------
def make_legacy():
    """Restore the pre-INV-1249 behaviour so the gate can be SHOWN failing.

    Two edits, matching the two defects: the seven grammars go away (so their
    species blank, as `schedule.SPECIES_WITHOUT_NAMES` says they did) and the
    reservation rule becomes a no-op (so a draw can land on the cast again).
    Nothing else changes, which is what makes the before/after a measurement of
    this change rather than of two builds.
    """
    for s in list(nm.GRAMMARS):
        if s in sched.SPECIES_WITHOUT_NAMES:
            del nm.GRAMMARS[s]
    nm._pick_clear = lambda seq, seed, salt, finish: nm._pick(seq, seed, salt)
    res.resident.cache_clear()


def packaged(root):
    """Measure a packaged build's own actors instead of regenerating.

    Deliberately NOT the default. CLAUDE.md: a gate that reads a committed
    artefact must be able to rebuild it, and this one cannot -- `dist/` is a
    5.5 GB export. So it is an OPTIONAL second opinion on a build that already
    exists, and the gate proper runs against the source of truth.
    """
    import glob
    import json
    ids, blank, worn = {}, collections.Counter(), collections.Counter()
    files = sorted(glob.glob(os.path.join(root, "**", "*_actors.json"),
                             recursive=True))
    for f in files:
        for a in json.load(open(f)):
            w = a.get("who") or {}
            if w.get("id") in ids:
                continue
            ids[w.get("id")] = w
    for w in ids.values():
        n = (w.get("name") or "").strip()
        if not n:
            blank[w.get("species", "?")] += 1
        elif n in nm.RESERVED:
            worn[n] += 1
    print(f"\n== packaged build: {len(files)} actor files, {len(ids)} residents ==")
    print(f"   empty NAME : {sum(blank.values())} "
          f"({100.0 * sum(blank.values()) / max(len(ids), 1):.1f}%)  {dict(blank)}")
    print(f"   reserved   : {sum(worn.values())} across {len(worn)} names  "
          f"{dict(worn.most_common(8))}")
    return sum(blank.values()), sum(worn.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy", action="store_true",
                    help="run the same questions with INV-1249/1249 removed")
    ap.add_argument("--packaged", metavar="DIR",
                    help="also measure a packaged build's actors.json")
    a = ap.parse_args()

    if a.legacy:
        make_legacy()
        print("*** LEGACY MODE: the seven grammars and the reservation rule are "
              "removed. Every FAIL below is what the build shipped. ***")

    gate_a(a.legacy)
    gate_b()
    gate_c(a.legacy)
    gate_d()
    if a.packaged:
        packaged(a.packaged)

    bad = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(bad)}/{len(_results)} passed")
    if bad:
        print("FAILED: " + "; ".join(bad))
    if a.legacy:
        print("\n(legacy run: a FAIL here is the point -- it is the state this "
              "change moved the build out of)")
        return 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
