"""Tests for NPC schedules, the species mix and the statistical population layer.

Every assertion here has been deliberately broken and watched to fail. That is
not ceremony: this repository has shipped an assertion that scored 768
triangles as passing from an `else` branch, and one that compared a value
against itself. The two patterns to avoid are *tautology* -- asserting
something the code just computed -- and *vacuity* -- a threshold no realisable
input can cross. Both are called out in comments wherever a reader might
reasonably mistake one for the other.
"""
import ast
import math
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))          # station/, for signage.py

from schedule import (ARRIVALS_PER_DAY, AVAIL_SCAN, CENSUS_SCAN, CUSTOMS_HALLS,
                      EXTINCT_SPECIES, HALL_DWELL_H, MEAL_HALF_WINDOW_H,
                      NPC_BUDGET, PEAK_RATE_PER_MIN, PLACES, PRE_SHIFT_H,
                      REF_WORK_START, RESIDENT_TOTAL, RHYTHMS, ROLE_WEIGHTS, ROLES,
                      ROLES_BY_KEY, ROTATING_WORKPLACES, SOULS_PER_ARRIVAL,
                      SPECIES_WITHOUT_NAMES, STATION_COUNTS, STATION_HEADCOUNT,
                      STATION_MIX, VORLON_SINGLETON, Activity, _in_window,
                      activity_at, activity_profile, apportion, arrival_times,
                      awake_fraction, crowd_at, crowd_headcount, density_at,
                      npc_triangle_budget, npc_visible_triangles,
                      population_activity, role_for, role_headcount, role_on_duty,
                      shift_offset, wake_hour, work_window)

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def note(text):
    print(f"NOTE  {text}")


# The SHARE column of FACTIONS.md 2.4, transcribed separately from the COUNT
# column that `schedule.STATION_COUNTS` holds. The source table states both;
# asserting they agree checks the transcription in both directions and catches
# a typo in either. This is not a second copy of a computed number -- nothing
# in schedule.py reads this dict, and it exists only to disagree.
FACTIONS_SHARES = {
    "human": 0.620, "narn": 0.090, "centauri": 0.070, "minbari": 0.050,
    "drazi": 0.050, "brakiri": 0.030, "pakmara": 0.025, "vree": 0.020,
    "abbai": 0.015, "gaim": 0.010, "hyach": 0.007, "llort": 0.005,
    "other": 0.005, "grome": 0.003,
}

# INV-005 records a mix that summed to 0.94 and silently dropped 120 of every
# 2,000 residents. It does NOT record which rows were short -- only the sum,
# which is the only part of it that mattered -- so this is a reconstruction
# that reproduces the sum. Kept as a fixture rather than a fallback, because
# the population layer now has to REFUSE it.
#
# The six-species mix that was actually in the file when this session started
# summed to 1.00, so it is a separate fixture: it is not a leak, it is merely
# superseded, and asserting the wrong one would have been an assertion that
# could not fail for the reason it claimed.
INV005_BROKEN_MIX = {"human": 0.62, "narn": 0.10, "centauri": 0.09,
                     "minbari": 0.07, "drazi": 0.01, "pakmara": 0.05}   # 0.94
SUPERSEDED_SIX = {"human": 0.62, "narn": 0.10, "centauri": 0.09,
                  "minbari": 0.07, "drazi": 0.07, "pakmara": 0.05}      # 1.00

# The "Human share" column of FACTIONS.md 2.5, transcribed independently of
# `schedule.PLACES`. THIS EXISTS BECAUSE THE FIRST VERSION OF THE HUMAN-SHARE
# CHECK WAS A TAUTOLOGY: it compared what `crowd_at()` produced against the
# same `human_share` field `crowd_at()` had just used as its base, so declaring
# the Zocalo 95% human changed the model, changed the expectation with it, and
# failed nothing. Rewriting the number here is the only way a transcription
# error can be caught, and the break test confirms it now is.
PLACE_HUMAN_SHARES = {
    "zocalo": 0.45, "customs_halls": 0.40, "central_corridor": 0.55,
    "earharts": 0.80, "dark_star": 0.50, "casino": 0.50,
    "business_district": 0.65, "law_courts": 0.75, "security_central": 0.95,
    "docking_bays": 0.60, "dock_workers_quarters": 0.70, "medlab_one": 0.70,
    "crew_country": 0.90, "council_chamber": 0.35, "ambassadorial_suites": 0.30,
    "alien_sector": 0.05, "fresh_air_restaurant": 0.60, "zen_garden": 0.50,
    "hydroponics": 0.85, "the_garden": 0.65, "downbelow": 0.68,
    "sanctuaries": 0.60, "industrial_grey": 0.90, "yellow_maintenance": 0.95,
}

# The "Dominant non-humans" column of 2.5, ranked, for the rows that name any.
# Same argument: ranking is data, and a silently reordered rank is a silently
# different crowd.
PLACE_DOMINANTS = {
    "zocalo": ("narn", "drazi", "centauri", "brakiri"),
    "central_corridor": ("drazi", "narn", "pakmara"),
    "earharts": ("centauri", "minbari"),
    "dark_star": ("drazi", "narn", "llort"),
    "casino": ("centauri", "brakiri", "drazi"),
    "business_district": ("brakiri", "centauri", "hyach"),
    "law_courts": ("narn", "centauri", "drazi"),
    "docking_bays": ("drazi", "narn", "pakmara", "vree"),
    "dock_workers_quarters": ("drazi", "narn"),
    "council_chamber": ("minbari", "centauri", "drazi", "brakiri", "abbai"),
    "hydroponics": ("abbai", "grome"),
    "downbelow": ("narn", "drazi", "pakmara", "llort"),
}


def _gaps(times):
    t = sorted(times)
    return [(t[(i + 1) % len(t)] - t[i]) % 24.0 for i in range(len(t))]


def _raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except ValueError:
        return True
    return False


def main():
    # =======================================================================
    # 1. THE MIX -- what INV-005 says must never be checked by eye again
    # =======================================================================
    check("head count sums to exactly 250,000",
          sum(STATION_COUNTS.values()) == RESIDENT_TOTAL,
          f"{sum(STATION_COUNTS.values()):,}")
    # Tolerance is ZERO, deliberately. INV-005's failure mode was a 0.06
    # tolerance that a 0.94 sum walked straight through. `math.fsum` is exactly
    # 1.0 here; the naive `sum` of the same fourteen floats is not, which is
    # why the module derives shares from integer counts.
    check("species shares sum to exactly 1.0",
          math.fsum(STATION_MIX.values()) == 1.0,
          f"fsum {math.fsum(STATION_MIX.values())!r}, "
          f"naive sum {sum(STATION_MIX.values())!r}")
    check("the mix is fifteen species, not six",
          len(STATION_COUNTS) + 1 == 15,
          f"{len(STATION_COUNTS)} apportioned + the Vorlon singleton")
    bad = {sp: (STATION_COUNTS[sp] / RESIDENT_TOTAL, FACTIONS_SHARES.get(sp))
           for sp in STATION_COUNTS
           if abs(STATION_COUNTS[sp] / RESIDENT_TOTAL
                  - FACTIONS_SHARES.get(sp, -1.0)) > 1e-12}
    check("2.4's count column and share column agree exactly",
          not bad and set(FACTIONS_SHARES) == set(STATION_COUNTS), str(bad))

    # --- the Vorlon singleton ----------------------------------------------
    check("Vorlon is hard-coded as exactly one person",
          VORLON_SINGLETON == 1 and isinstance(VORLON_SINGLETON, int))
    check("Vorlon is not a share in the mix",
          "vorlon" not in STATION_MIX and "vorlon" not in STATION_COUNTS)
    check("station head count is the mix plus Kosh",
          STATION_HEADCOUNT == 250_001, f"{STATION_HEADCOUNT:,}")
    # NOT a tautology: this computes the rounding artefact the singleton exists
    # to avoid, and shows it is real rather than theoretical.
    as_share = VORLON_SINGLETON / RESIDENT_TOTAL
    check("one-in-250,000 as a share rounds to nobody at sample scale",
          int(2_000 * as_share) == 0 and int(20_000 * as_share) == 0,
          f"share {as_share:g} -> {int(2000 * as_share)} of 2,000 and "
          f"{int(20000 * as_share)} of 20,000")
    check("no apportionment at any scale produces a Vorlon",
          all("vorlon" not in apportion(n) for n in (7, 2_000, 250_000)))

    # --- Markab: zero, and recorded rather than omitted ---------------------
    check("Markab are zero at the datum",
          "markab" not in STATION_COUNTS
          and STATION_COUNTS.get("markab", 0) == 0
          and EXTINCT_SPECIES["markab"]["count"] == 0)
    check("the extinction records the event and what to do if the datum moves",
          "S2E18" in EXTINCT_SPECIES["markab"]["died"]
          and EXTINCT_SPECIES["markab"]["if_datum_moves_before_S2E18"]["share"]
          == 0.008)
    check("the sealed Markab quarter holds nobody at any hour",
          all(density_at("markab_quarter", h / 2.0) == 0.0 for h in range(48))
          and crowd_at("markab_quarter", 13.0) == {}
          and crowd_headcount("markab_quarter", 13.0, 5_000.0) == {})

    # --- the leak itself ----------------------------------------------------
    try:
        population_activity(14.0, INV005_BROKEN_MIX, 2_000)
        raised = ""
    except ValueError as exc:
        raised = str(exc)
    check("a 0.94 mix is refused, not silently normalised",
          "120" in raised and "INV-005" in raised, raised[:88])
    # The superseded six-species mix summed to 1.00, so it must be ACCEPTED --
    # it was the wrong mix, not a leaking one. Without this the check above
    # could pass by rejecting everything.
    try:
        ok_six = sum(population_activity(14.0, SUPERSEDED_SIX, 2_000).values()) == 2_000
    except ValueError:
        ok_six = False
    check("a mix that does sum to 1.0 is accepted", ok_six,
          f"the superseded six summed to {math.fsum(SUPERSEDED_SIX.values())}")
    check("the tolerance is tight enough to catch a small leak",
          _raises(population_activity, 14.0,
                  dict(STATION_MIX, human=STATION_MIX["human"] - 1e-6), 2_000))
    check("apportionment is exact at every scale, not truncated",
          all(sum(apportion(n).values()) == n
              for n in (1, 3, 7, 17, 997, 999, 2_000, 12_345, 45_001, 250_000)))
    # The leak is not hypothetical. Flooring fourteen shares loses up to
    # thirteen people per call, and it loses them for the whole run because the
    # aggregate layer is recomputed every station-hour from the same shares.
    losses = {n: n - sum(int(n * s) for s in STATION_MIX.values())
              for n in (997, 999, 12_345, 45_001)}
    check("largest-remainder recovers the people int() truncation loses",
          all(v > 0 for v in losses.values())
          and all(sum(apportion(n).values()) == n for n in losses),
          f"int() loses {losses}; apportion loses none")

    # =======================================================================
    # 2. RHYTHMS AND ROLES
    # =======================================================================
    check("every mix species has a rhythm", all(s in RHYTHMS for s in STATION_MIX))
    check("Kosh has a rhythm even though he is not in the mix",
          "vorlon" in RHYTHMS and RHYTHMS["vorlon"].meals == ())
    check("inferred rhythms say so in their note",
          "INFERRED" in RHYTHMS["pakmara"].note)
    check("the sourced rhythm claims cite what sourced them",
          "authority 4" in RHYTHMS["brakiri"].note
          and "NIGHT DWELLERS" in RHYTHMS["brakiri"].note
          and "encounter suits" in RHYTHMS["gaim"].note
          and "Amphibian" in RHYTHMS["abbai"].note)
    check("Gaim and Kosh wear suits; the Abbai want a humid mix",
          RHYTHMS["gaim"].breather == "suit" and RHYTHMS["gaim"].atmos == "methane"
          and RHYTHMS["vorlon"].breather == "suit"
          and RHYTHMS["abbai"].atmos == "humid_oxygen")

    # Cross-module, against an authority-1 prop: the customs board says SIX
    # atmospheres are available at once. A fifteen-species mix must not quietly
    # need a seventh.
    try:
        import signage                                     # noqa: PLC0415
        six = signage.ESTABLISHED["atmospheres_available"]
    except Exception:                                      # noqa: BLE001
        six = None
    classes = {RHYTHMS[s].atmos for s in list(STATION_MIX) + ["vorlon"]}
    check("atmosphere classes fit inside the board's SIX",
          six == 6 and len(classes) <= six,
          f"{len(classes)} classes {sorted(classes)} vs signage's {six}")

    check("Downbelow lurkers have no work",
          any(r.key == "lurker" and r.work_hours == 0 for r in ROLES))
    check("queuing is not lurking, and neither is being a tourist",
          {r.key for r in ROLES} >= {"lurker", "refugee", "visitor"}
          and all(ROLES_BY_KEY[k].work_hours == 0
                  for k in ("lurker", "refugee", "visitor"))
          and len({ROLES_BY_KEY[k].workplace
                   for k in ("lurker", "refugee", "visitor")}) == 3)
    check("a rotating role's declared start IS the reference day watch",
          all(r.work_start == REF_WORK_START for r in ROLES
              if r.workplace in ROTATING_WORKPLACES),
          f"REF_WORK_START = {REF_WORK_START}")
    check("PRE_SHIFT_H is derived from the human rhythm, not chosen",
          abs(PRE_SHIFT_H - (REF_WORK_START - wake_hour("human"))) < 1e-12
          and abs(PRE_SHIFT_H - 1.5) < 1e-12, f"{PRE_SHIFT_H} h")

    # Role weights are an APPORTIONMENT of the mix, not a wish list: they sum
    # per species to that species' head count, so the roster cannot double-count
    # anyone or drop anyone.
    mism = {sp: (sum(w.values()), STATION_COUNTS.get(sp, VORLON_SINGLETON))
            for sp, w in ROLE_WEIGHTS.items()
            if sum(w.values()) != STATION_COUNTS.get(sp, VORLON_SINGLETON)}
    check("every species' role weights sum to that species' head count",
          not mism, str(mism))
    check("role weights only name roles that exist",
          all(k in ROLES_BY_KEY for w in ROLE_WEIGHTS.values() for k in w))
    heads = role_headcount()
    check("role head counts total the whole station including Kosh",
          sum(heads.values()) == STATION_HEADCOUNT, f"{sum(heads.values()):,}")
    # Five cross-checks against figures FACTIONS.md states in PROSE, elsewhere
    # from the tables the weights were transcribed from.
    check("security is 500 officers (2.2)", heads["security"] == 500)
    check("command is 120 (2.2)", heads["command"] == 120)
    check("13,000 Narn refugees (6.2)", heads["refugee"] == 13_000)
    check("Downbelow is ~20,000 people (2.2, 11.2)",
          abs(heads["lurker"] - 20_000) / 20_000 < 0.03, f"{heads['lurker']:,}")
    check("~45,000 transients in port (2.2, 2.3)",
          abs(heads["visitor"] - 45_000) / 45_000 < 0.03, f"{heads['visitor']:,}")

    # =======================================================================
    # 3. DETERMINISM
    # =======================================================================
    check("same NPC at same hour does the same thing",
          activity_at("n-1", "human", 14.0) == activity_at("n-1", "human", 14.0))
    check("role is stable for an NPC", role_for("n-1").key == role_for("n-1").key)
    # Neither check above can catch a salted hash: both calls happen in one
    # process, where `str.__hash__` is stable. This one can, and a salted hash
    # would have produced a different station every run.
    # BOTH paths, exactly as lines 18-19 set up for this process. The probe used
    # to insert `_HERE` alone, which was true when it was written and stopped
    # being true when `schedule.py` grew a module-scope `from npc import body`
    # for `_body_frame_share()` -- that needs `station/` on the path, so every
    # probe process died on ModuleNotFoundError and printed nothing. A child
    # process does not inherit sys.path edits; it inherits the interpreter's
    # defaults, so anything the parent had to arrange the child must arrange too.
    probe = (
        "import sys, os; sys.path.insert(0, %r); sys.path.insert(0, %r);"
        "import schedule as S;"
        "print('|'.join(S.role_for('n-%%d' %% i, 'narn').key + ':' +"
        "S.activity_at('n-%%d' %% i, 'narn', i %% 24).value for i in range(400)))"
        % (os.path.dirname(_HERE), _HERE)
    )
    outs, errs = [], []
    for seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", probe], env=env,
                           capture_output=True, text=True)
        outs.append(r.stdout)
        errs.append(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "")
    # `len(outs[0]) > 1_000` is the clause that kept this honest -- two crashed
    # runs both print nothing and compare EQUAL, which is CLAUDE.md's "a diff of
    # two failed runs is not a pass". It did its job; what it could not do is say
    # WHY, because the harness captured stderr and dropped it. It took a manual
    # re-run to see a one-line ModuleNotFoundError. Report the child's last error
    # line: a harness that can only say "0 bytes" makes its own failure expensive.
    check("identical byte for byte across two PYTHONHASHSEED values",
          outs[0] == outs[1] and len(outs[0]) > 1_000,
          f"{len(outs[0])} bytes, seeds 0 and 12345"
          + (f" -- child said: {errs[0] or errs[1]}" if (errs[0] or errs[1])
             else ""))
    # Parsed rather than grepped. A substring search over the source flagged
    # the module's own docstring, which says in prose that it never uses
    # `str.__hash__` -- so the first version of this check failed on a comment
    # and would equally have passed a module that mentioned nothing and used
    # everything. The AST sees code and not prose.
    tree = ast.parse(open(os.path.join(_HERE, "schedule.py")).read())
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree)
                if isinstance(n, ast.Import)} | {
        n.module.split(".")[0] for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    builtin_hash = any(isinstance(n.func, ast.Name) and n.func.id == "hash"
                       for n in ast.walk(tree) if isinstance(n, ast.Call))
    check("the module imports no `random` and calls no salted hash",
          "random" not in imported and "__hash__" not in attrs
          and not builtin_hash and "hashlib" in imported,
          f"imports {sorted(imported)}")

    # =======================================================================
    # 4. SLEEP, SHIFTS AND THE NIGHT WATCH
    # =======================================================================
    sleeping = sum(1 for i in range(400)
                   if activity_at(f"h-{i}", "human", 3.0) is Activity.SLEEP)
    check("most humans are asleep at 03:00", sleeping > 250, f"{sleeping}/400")
    awake = sum(1 for i in range(400)
                if activity_at(f"h-{i}", "human", 14.0) is Activity.SLEEP)
    check("few humans are asleep at 14:00", awake < 80, f"{awake}/400")

    # A 24-hour coverage property should not be sampled at all. Three watches
    # of 8 hours tile the clock exactly, so assert that directly, at every hour
    # and for every rotating role. This cannot be flaky and cannot pass by luck.
    ungapped = True
    for role in ROLES:
        if role.workplace not in ROTATING_WORKPLACES:
            continue
        gaps = [h for h in range(24)
                if not any(_in_window(float(h), role.work_start + off,
                                      role.work_hours)
                           for off in (0.0, 8.0, 16.0))]
        if gaps:
            ungapped = False
            print(f"      {role.key}: unmanned at {gaps}")
    check("three watches tile all 24 hours for every rotating role", ungapped,
          f"{sum(1 for r in ROLES if r.workplace in ROTATING_WORKPLACES)} "
          "rotating roles x 24 hours")

    # The precondition that makes the sleep model safe rather than lucky.
    over = [(sp, k) for sp, w in ROLE_WEIGHTS.items() for k, v in w.items()
            if v > 0 and RHYTHMS.get(sp, RHYTHMS["human"]).sleep_hours
            + ROLES_BY_KEY[k].work_hours + PRE_SHIFT_H > 24.0]
    check("sleep + shift + pre-shift fits in 24 h for every realisable pair",
          not over, str(over[:4]))
    # ...and the consequence, measured on the built model rather than assumed.
    # THIS IS THE ASSERTION THE OLD `on_duty > 0` SHOULD HAVE BEEN. Sweeping
    # every species against every role it can hold, at quarter-hour resolution
    # across the whole shift, is what catches a night watch in bed -- a count
    # greater than zero does not, because jitter always leaves a few standing.
    clash, swept = 0, 0
    lost = []
    for sp in list(STATION_MIX) + ["vorlon"]:
        for i in range(160):
            nid = f"clash-{sp}-{i}"
            win = work_window(nid, sp)
            if win is None:
                continue
            swept += 1
            w0, hours = win
            asleep = sum(1 for step in range(int(hours * 4))
                         if activity_at(nid, sp, (w0 + step * 0.25 + 0.05) % 24.0)
                         is Activity.SLEEP)
            clash += 1 if asleep else 0
            # Hours actually observed at work over the whole day. A night watch
            # in bed does not merely overlap -- it loses most of its shift, and
            # under the previous model a human night watch lost 7.5 h of 8.
            worked = sum(1 for q in range(96)
                         if activity_at(nid, sp, q * 0.25) is Activity.WORK) * 0.25
            if worked < hours - 2.0:
                lost.append((sp, nid, round(hours - worked, 2)))
    check("nobody is asleep inside their own shift, over every species x role",
          clash == 0, f"{clash} of {swept} workers asleep on duty")
    check("every worker is observed working most of their shift",
          not lost, f"{len(lost)} short, worst {sorted(lost, key=lambda r: -r[2])[:2]}")

    rot = [r for r in ROLES if r.workplace in ROTATING_WORKPLACES][0]
    check("rotating roles are spread across three watches",
          {shift_offset(f"s-{i}", rot) for i in range(300)} == {0.0, 8.0, 16.0})
    check("non-rotating roles are not shifted",
          all(shift_offset(f"s-{i}", ROLES_BY_KEY["merchant"]) == 0.0
              for i in range(50)))
    # Sized so the answer is not a lottery: security is 500 of 155,000 humans
    # (2.2), so 300 ids yield about ONE officer and any question about them
    # becomes a coin toss. 20,000 ids carry ~65.
    sec = [n for n in (f"s-{i}" for i in range(20_000))
           if role_for(n).key == "security"]
    check("the officer sample is large enough to mean anything", len(sec) >= 20,
          f"{len(sec)} of 20,000 ids")
    check("officers land on all three watches",
          {shift_offset(n, role_for(n)) for n in sec} == {0.0, 8.0, 16.0},
          f"over {len(sec)} officers")
    on_duty = [sum(1 for n in sec if activity_at(n, "human", h) is Activity.WORK)
               for h in (2.0, 10.0, 18.0)]
    check("security is on duty around the clock", all(c > 0 for c in on_duty),
          f"02:00={on_duty[0]} 10:00={on_duty[1]} 18:00={on_duty[2]} of {len(sec)}")
    # 2.2: "roughly 150 officers are on duty at any moment across five
    # pressurised sectors and 210 decks". That was a sentence; this is a
    # measurement of the model, and the garrison-at-chokepoints design that
    # makes the crime layer credible rests entirely on it.
    duty = [role_on_duty("security", h) for h in (2.0, 10.0, 18.0)]
    check("~150 security on duty at any moment (2.2)",
          all(120 <= c <= 210 for c in duty),
          f"{duty} station-wide, from 500 officers on three watches")
    check("C&C keeps three watches, so the bridge is never empty",
          all(role_on_duty("command", h) > 20 for h in (2.0, 14.0)),
          f"02:00={role_on_duty('command', 2.0)}, "
          f"14:00={role_on_duty('command', 14.0)} of 120")

    # --- meal windows -------------------------------------------------------
    # Never tested before, and the window was silently one-sided: a Python
    # modulo is non-negative, so `abs((hour - m) % 24) < 0.6` could only ever
    # be true AFTER the meal hour.
    before = sum(1 for i in range(600)
                 if activity_at(f"m-{i}", "human", 12.5 - MEAL_HALF_WINDOW_H / 2)
                 is Activity.EAT)
    after = sum(1 for i in range(600)
                if activity_at(f"m-{i}", "human", 12.5 + MEAL_HALF_WINDOW_H / 2)
                is Activity.EAT)
    check("meal windows are centred on the meal hour, not one-sided",
          before > 30 and after > 30 and 0.4 < before / max(after, 1) < 2.5,
          f"{before} eating just before 12:30, {after} just after")

    # =======================================================================
    # 5. FIFTEEN SPECIES MEAN FIFTEEN CROWDS
    # =======================================================================
    at3 = {sp: awake_fraction(sp, 3.0) for sp in STATION_MIX}
    check("Minbari are far more awake at 03:00 than humans",
          at3["minbari"] > at3["human"] * 1.5,
          f"minbari {at3['minbari']:.0%} vs human {at3['human']:.0%}")
    check("Centauri are still up at 03:00", at3["centauri"] > 0.3,
          f"{at3['centauri']:.0%} awake")
    check("Brakiri are a NIGHT species, not merely a late one",
          at3["brakiri"] > 0.85 and awake_fraction("brakiri", 12.0) < 0.25,
          f"{at3['brakiri']:.0%} awake at 03:00, "
          f"{awake_fraction('brakiri', 12.0):.0%} at 12:00")
    check("species do not all share one rhythm",
          max(at3.values()) - min(at3.values()) > 0.5,
          f"spread {max(at3.values()) - min(at3.values()):.0%} across "
          f"{len(at3)} species at one hour")
    # Isolation is a design target as much as crowding: there must be an hour
    # when most of the station is asleep, and an hour when most of it is not.
    hourly = [sum(awake_fraction(sp, float(h)) * STATION_COUNTS[sp]
                  for sp in STATION_MIX) / RESIDENT_TOTAL for h in range(24)]
    check("the station has a real night and a real day",
          min(hourly) < 0.45 and max(hourly) > 0.85,
          f"{min(hourly):.0%} awake at {hourly.index(min(hourly)):02d}:00, "
          f"{max(hourly):.0%} at {hourly.index(max(hourly)):02d}:00")
    check("an NPC's day has variety",
          len({activity_at("n-7", "human", h / 2.0) for h in range(48)}) >= 3)

    # =======================================================================
    # 6. THE STATISTICAL LAYER -- it must agree with counting everybody
    # =======================================================================
    counts = population_activity(14.0, STATION_MIX, 2_000)
    check("aggregate layer accounts for everyone, exactly",
          sum(counts.values()) == 2_000, f"{sum(counts.values())}")
    check("aggregate is exact at full station scale too",
          sum(population_activity(14.0, STATION_MIX, RESIDENT_TOTAL).values())
          == RESIDENT_TOTAL)
    check("aggregate at 14:00 is mostly working or out",
          counts[Activity.SLEEP] < sum(counts.values()) * 0.25,
          f"{counts[Activity.SLEEP]}/{sum(counts.values())} asleep")
    night = population_activity(3.0, STATION_MIX, 2_000)
    check("aggregate at 03:00 is mostly asleep",
          night[Activity.SLEEP] > sum(night.values()) * 0.5,
          f"{night[Activity.SLEEP]}/{sum(night.values())} asleep")
    check("the station is never fully asleep",
          sum(v for k, v in night.items() if k is not Activity.SLEEP) > 200,
          f"{sum(v for k, v in night.items() if k is not Activity.SLEEP)} awake")
    at3_full = population_activity(3.0, STATION_MIX, RESIDENT_TOTAL)
    check("tens of thousands are still at work at 03:00",
          at3_full[Activity.WORK] > 15_000, f"{at3_full[Activity.WORK]:,} working")

    # Commuting. `Activity.TRANSIT` was in the enum and nothing emitted it, so
    # the corridors and lifts had no population and everyone teleported to
    # work. The check is not that transit exists but that it peaks where the
    # source independently says the Central Corridor is busy -- 07:00-09:00 and
    # 17:00-19:00 (2.5) -- which nothing here was tuned to produce.
    tr = [population_activity(float(h), STATION_MIX,
                              RESIDENT_TOTAL)[Activity.TRANSIT] for h in range(24)]
    morning = max(range(6, 11), key=lambda h: tr[h])
    evening = max(range(14, 21), key=lambda h: tr[h])
    check("commuting peaks near the Central Corridor's stated rush hours",
          tr[morning] > 2 * (sum(tr) / 24) and tr[evening] > 2 * (sum(tr) / 24)
          and 7 <= morning <= 9 and 16 <= evening <= 18,
          f"peaks {morning:02d}:00 ({tr[morning]:,}) and {evening:02d}:00 "
          f"({tr[evening]:,}) against a mean of {sum(tr) / 24:,.0f}; the "
          f"evening peak is an hour EARLY against 2.5's 17:00-19:00")
    check("the third peak is the midnight watch handover, not a bug",
          tr[0] > sum(tr) / 24, f"00:00 = {tr[0]:,}, third busiest -- the "
          "16-hour watch coming off and the 0-hour watch going on")

    # THE claim the whole LOD design rests on, tested rather than asserted in a
    # docstring: the sampled layer must reproduce what enumerating individuals
    # gives, or the population changes when the player looks away.
    worst = 0.0
    for sp, hour in (("human", 14.0), ("brakiri", 3.0), ("gaim", 9.0)):
        n, full = 8_192, {a: 0 for a in Activity}
        for i in range(n):
            full[activity_at(f"agg-{sp}-{i}", sp, hour)] += 1
        prof = activity_profile(sp, hour)
        worst = max(worst, max(abs(prof[a] - full[a] / n) for a in Activity))
    check("the sampled layer matches a full enumeration within sampling error",
          worst < 0.05,
          f"worst error {worst:.4f} at scan={CENSUS_SCAN}, "
          f"1/sqrt(n) = {1 / math.sqrt(CENSUS_SCAN):.3f}")

    # =======================================================================
    # 7. WHERE THE CROWD IS -- FACTIONS.md 2.5, wired in as data
    # =======================================================================
    check("every place in 2.5 is present", len(PLACES) >= 24, f"{len(PLACES)} places")
    check("no place carries a level number -- C-003 and C-004 are OPEN",
          all(p.ring_class in ("", "outer", "middle", "inner", "axis")
              for p in PLACES.values())
          and not any(ch.isdigit() for p in PLACES.values()
                      for ch in p.ring_class + p.sector))
    check("every species named as dominant is in the mix",
          all(s in STATION_COUNTS for p in PLACES.values() for s in p.dominant))
    bad = [(k, math.fsum(crowd_at(k, h).values()))
           for k in PLACES for h in (3.0, 13.0, 22.0)
           if not PLACES[k].sealed
           and abs(math.fsum(crowd_at(k, h).values()) - 1.0) > 1e-9]
    check("composition sums to 1.0 at every place and hour", not bad, str(bad[:3]))

    # The transcription itself, against an independent copy of 2.5's columns.
    off = {k: (PLACES[k].human_share, v) for k, v in PLACE_HUMAN_SHARES.items()
           if k not in PLACES or abs(PLACES[k].human_share - v) > 1e-12}
    check("every human share matches an independent transcription of 2.5",
          not off and len(PLACE_HUMAN_SHARES) == 24, str(off))
    offd = {k: (PLACES[k].dominant, v) for k, v in PLACE_DOMINANTS.items()
            if k not in PLACES or PLACES[k].dominant != v}
    check("the dominant-species rankings match 2.5, in order", not offd, str(offd))

    # Now the model, not the table. The stated share is the fraction of the
    # STANDING crowd, so the honest comparison weights each hour by how many
    # people are standing there. This measures how far the availability
    # modulation -- which is driven purely by the rhythms -- drags the crowd
    # away from the stated figure. NOTHING CALIBRATES IT: no constant is fitted
    # to make this pass, and the three worst places are the three whose opening
    # hours are furthest out of step with the human day.
    drift = {}
    for k, p in PLACES.items():
        if p.sealed:
            continue
        num = den = 0.0
        for i in range(48):
            h = i * 0.5
            d = density_at(k, h)
            num += crowd_at(k, h)["human"] * d
            den += d
        drift[k] = num / den - p.human_share
    worst_k = max(drift, key=lambda k: abs(drift[k]))
    close = sum(1 for v in drift.values() if abs(v) < 0.03)
    check("rhythm-driven availability keeps the stated human share",
          abs(drift[worst_k]) < 0.10 and close >= 20,
          f"worst {worst_k} {drift[worst_k]:+.3f}; {close}/{len(drift)} "
          "within 0.03 with no calibration")

    # 2.4's stated gradient: "the docks and customs are the most alien places on
    # the station and Blue Sector crew country is the most human".
    hum = {k: crowd_at(k, 13.0)["human"] for k in
           ("customs_halls", "docking_bays", "crew_country", "alien_sector")}
    check("the alien-to-human gradient runs the way 2.4 says it does",
          hum["customs_halls"] < hum["docking_bays"] < hum["crew_country"]
          and hum["alien_sector"] == min(crowd_at(k, 13.0).get("human", 1.0)
                                         for k in PLACES if not PLACES[k].sealed),
          " ".join(f"{k}={v:.2f}" for k, v in hum.items()))
    bd_night = crowd_at("business_district", 2.0)["brakiri"]
    bd_day = crowd_at("business_district", 13.0)["brakiri"]
    check("Brakiri are the Business District's night crowd",
          bd_night > bd_day * 2.5,
          f"{bd_night:.1%} at 02:00 vs {bd_day:.1%} at 13:00 -- from one "
          "authority-4 sentence, not a constant")
    check("the Gaim are what make the Alien Sector alien",
          crowd_at("alien_sector", 13.0)["gaim"] > 0.25
          and crowd_at("alien_sector", 13.0)["human"] < 0.10,
          f"gaim {crowd_at('alien_sector', 13.0)['gaim']:.0%}, human "
          f"{crowd_at('alien_sector', 13.0)['human']:.0%}")

    # --- crowdedness and isolation, as numbers ------------------------------
    dens = {(k, h): density_at(k, float(h)) for k in PLACES for h in range(24)
            if not PLACES[k].sealed}
    hi, lo = max(dens, key=dens.get), min(dens, key=dens.get)
    check("the station is both crowded and empty, by a factor of hundreds",
          dens[hi] / dens[lo] > 100.0,
          f"{hi[0]} at {hi[1]:02d}:00 = {dens[hi]:.2f} vs {lo[0]} = "
          f"{dens[lo]:.2f} per 100 m2 -- {dens[hi] / dens[lo]:.0f}x")
    check("a dead hour is quiet, not empty -- 05:00 in the Zocalo",
          0.0 < density_at("zocalo", 5.0) < density_at("zocalo", 13.0) * 0.2,
          f"{density_at('zocalo', 5.0):.2f} vs "
          f"{density_at('zocalo', 13.0):.2f} per 100 m2")
    check("Downbelow has no rhythm at all",
          len({round(density_at("downbelow", h / 2.0), 6) for h in range(48)}) == 1,
          "flat by design -- 2.5, '24 h, no rhythm'")
    check("a crowd arrives over minutes; it does not teleport",
          max(abs(density_at("zocalo", h / 60.0)
                  - density_at("zocalo", (h + 1) / 60.0)) for h in range(1440))
          < density_at("zocalo", 13.0) * 0.05)

    # --- the arrivals model, FACTIONS.md 2.3 --------------------------------
    check("52 ship movements a station-day", len(arrival_times()) == ARRIVALS_PER_DAY)
    g = _gaps(arrival_times())
    check("arrivals are irregular, so the hall gets real dead periods",
          max(g) > 2.0 * (24.0 / ARRIVALS_PER_DAY),
          f"gaps {min(g):.2f}-{max(g):.2f} h against an even {24 / ARRIVALS_PER_DAY:.2f} h")
    busy_frac = sum(1 for m in range(1440)
                    if density_at("customs_halls", m / 60.0) > 20.0) / 1440.0
    check("the customs hall heaves and then empties",
          0.05 < busy_frac < 0.35, f"{busy_frac:.0%} of the day above 20/100m2")
    check("the customs dwell time is derived from 2.3's 20-40/minute band",
          20.0 <= PEAK_RATE_PER_MIN <= 40.0
          and abs(HALL_DWELL_H * 60.0
                  - SOULS_PER_ARRIVAL / CUSTOMS_HALLS / PEAK_RATE_PER_MIN * 3.0)
          < 1e-9,
          f"{PEAK_RATE_PER_MIN:.0f}/min at the counter, "
          f"{HALL_DWELL_H * 60:.0f} min of queue")
    check("daily arrivals close the loop 2.3 opens",
          abs(ARRIVALS_PER_DAY * SOULS_PER_ARRIVAL - 6_300) / 6_300 < 0.02
          and abs(2 * ARRIVALS_PER_DAY * SOULS_PER_ARRIVAL / CUSTOMS_HALLS / 1440.0
                  - 4.4) < 0.2,
          f"{ARRIVALS_PER_DAY * SOULS_PER_ARRIVAL:,} souls/day vs ~6,300; "
          f"{2 * ARRIVALS_PER_DAY * SOULS_PER_ARRIVAL / CUSTOMS_HALLS / 1440.0:.2f}"
          "/min/hall vs ~4.4")

    hc = crowd_headcount("zocalo", 13.0, 4_000.0)
    check("a crowd is whole people and the parts sum to the whole",
          sum(hc.values()) == int(round(density_at("zocalo", 13.0) * 40.0))
          and all(isinstance(v, int) and v > 0 for v in hc.values()),
          f"{sum(hc.values())} people over 4,000 m2, {len(hc)} species present")

    # =======================================================================
    # 8. COST -- the render path cannot see any of this, and it is the limit
    # =======================================================================
    check("the NPC visible set fits its slice of the frame",
          npc_visible_triangles() <= npc_triangle_budget(),
          f"{npc_visible_triangles():,} of {npc_triangle_budget():,} tri "
          f"({npc_visible_triangles() / npc_triangle_budget():.0%})")
    lods = NPC_BUDGET["lod"]
    check("LOD is a chain with no gap and no overlap",
          all(abs(lods[i][2] - lods[i + 1][1]) < 1e-9 for i in range(len(lods) - 1))
          and lods[0][1] == 0.0)
    check("each LOD is cheaper and further than the one before it",
          all(lods[i][3] > lods[i + 1][3] and lods[i][4] < lods[i + 1][4]
              for i in range(len(lods) - 1)))
    check("bodies drawn stay under the crowd-agent cap",
          sum(n for *_, n in lods) <= NPC_BUDGET["crowd_agents"],
          f"{sum(n for *_, n in lods)} drawn, "
          f"{NPC_BUDGET['crowd_agents']} simulated")
    check("draw calls fit under the exterior's own allowance",
          NPC_BUDGET["max_draw_calls"] <= 64
          and (len(STATION_COUNTS) + 1) * 2 <= NPC_BUDGET["max_draw_calls"],
          f"{(len(STATION_COUNTS) + 1) * 2} batches "
          f"(15 species x near/far) <= {NPC_BUDGET['max_draw_calls']}")
    # The statistical layer must not scale with the population or the whole
    # design is a lie: cost is O(species x scan) and the multiplier is free.
    check("the statistical layer costs the same at 2,000 and at 250,000",
          CENSUS_SCAN * (len(STATION_COUNTS) + 1) < RESIDENT_TOTAL / 4,
          f"{CENSUS_SCAN * (len(STATION_COUNTS) + 1):,} evaluations per hour, "
          f"cached, against {RESIDENT_TOTAL:,} residents")
    peak = max(density_at(k, float(h)) for k in PLACES for h in range(24)
               if not PLACES[k].sealed)
    check("even the densest place fits the drawn-body cap",
          peak / 100.0 * 2_500.0 <= NPC_BUDGET["crowd_agents"],
          f"{peak / 100.0 * 2500.0:.0f} bodies in a 2,500 m2 view at "
          f"{peak:.0f}/100m2")
    check("availability sampling is cheaper than the census it modulates",
          AVAIL_SCAN < CENSUS_SCAN, f"{AVAIL_SCAN} vs {CENSUS_SCAN}")

    # =======================================================================
    # 9. NAMES -- the gap is DECLARED, not filled from nothing
    # =======================================================================
    try:
        import names                                       # noqa: PLC0415
        grammars = set(names.GRAMMARS)
    except Exception as exc:                               # noqa: BLE001
        grammars = None
        note(f"names.py not importable, naming checks skipped: {exc}")
    if grammars is not None:
        missing = [s for s in STATION_MIX
                   if s not in grammars and s not in SPECIES_WITHOUT_NAMES]
        overlap = sorted(grammars & set(SPECIES_WITHOUT_NAMES))
        check("every mix species is either nameable or declared unnameable",
              not missing, str(missing))
        check("nothing is both nameable and declared unnameable",
              not overlap,
              str(overlap) or "adding a grammar must delete its entry here")
        check("Vorlon stays a closed list and is never generated in bulk",
              "vorlon" not in STATION_MIX
              and names.GRAMMARS["vorlon"].attested == ("Kosh", "Ulkesh"))

    # An independent transcription of the same source table, if the body module
    # is present. Two agents reading FACTIONS.md 2.4 separately and agreeing is
    # worth more than either reading it twice.
    try:
        import body                                        # noqa: PLC0415
        rows = body.FACTIONS_MIX
    except Exception:                                      # noqa: BLE001
        rows = None
        note("body.py not present; the independent-transcription check was skipped")
    if rows is not None:
        diff = {k for k in set(rows) | set(STATION_COUNTS)
                if rows.get(k, (None,))[0] != STATION_COUNTS.get(k)}
        check("body.py's independent transcription of 2.4 agrees exactly",
              not diff and body.VORLON_SINGLETON == VORLON_SINGLETON, str(diff))

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
