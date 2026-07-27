"""Tests for NPC schedules and the statistical population layer."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schedule import (RHYTHMS, ROLES, STATION_MIX, Activity, activity_at,
                      population_activity, role_for, shift_offset)

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    # --- determinism --------------------------------------------------------
    check("same NPC at same hour does the same thing",
          activity_at("n-1", "human", 14.0) == activity_at("n-1", "human", 14.0))
    check("role is stable for an NPC",
          role_for("n-1").key == role_for("n-1").key)

    # --- sleep wins ---------------------------------------------------------
    sleeping = sum(1 for i in range(400)
                   if activity_at(f"h-{i}", "human", 3.0) is Activity.SLEEP)
    check("most humans are asleep at 03:00", sleeping > 300, f"{sleeping}/400")
    awake = sum(1 for i in range(400)
                if activity_at(f"h-{i}", "human", 14.0) is Activity.SLEEP)
    check("almost no humans are asleep at 14:00", awake < 40, f"{awake}/400")

    # --- species differ visibly ---------------------------------------------
    # The point of per-species rhythms: a corridor at 03:00 should not be empty,
    # it should hold a specific and different crowd.
    at3 = {}
    for sp in ("human", "minbari", "centauri", "narn"):
        at3[sp] = sum(1 for i in range(400)
                      if activity_at(f"{sp}-{i}", sp, 3.0) is not Activity.SLEEP) / 400
    check("Minbari are far more awake at 03:00 than humans",
          at3["minbari"] > at3["human"] * 1.5,
          f"minbari {at3['minbari']:.0%} vs human {at3['human']:.0%}")
    check("Centauri are still up at 03:00",
          at3["centauri"] > 0.3, f"{at3['centauri']:.0%} awake")
    check("species do not all share one rhythm",
          max(at3.values()) - min(at3.values()) > 0.25,
          f"spread {max(at3.values()) - min(at3.values()):.0%}")

    # --- rotating shifts ----------------------------------------------------
    sec = [f"s-{i}" for i in range(300)]
    sec = [n for n in sec if role_for(n).workplace in ("patrol", "medlab")]
    if sec:
        offs = {shift_offset(n, role_for(n)) for n in sec}
        check("rotating roles are spread across shifts", len(offs) >= 2,
              f"offsets {sorted(offs)}")
        on_duty = [sum(1 for n in sec if activity_at(n, "human", h) is Activity.WORK)
                   for h in (2.0, 10.0, 18.0)]
        check("security is on duty around the clock", all(c > 0 for c in on_duty),
              f"02:00={on_duty[0]} 10:00={on_duty[1]} 18:00={on_duty[2]}")

    # --- no NPC is doing nothing all day ------------------------------------
    acts = {activity_at("n-7", "human", h / 2.0) for h in range(48)}
    check("an NPC's day has variety", len(acts) >= 3, str(sorted(a.value for a in acts)))

    # --- aggregate layer ----------------------------------------------------
    counts = population_activity(14.0, STATION_MIX, 2000)
    total = sum(counts.values())
    check("aggregate layer accounts for everyone", total > 1900, f"{total}")
    check("aggregate at 14:00 is mostly working or out",
          counts[Activity.SLEEP] < total * 0.25,
          f"{counts[Activity.SLEEP]}/{total} asleep")
    night = population_activity(3.0, STATION_MIX, 2000)
    check("aggregate at 03:00 is mostly asleep",
          night[Activity.SLEEP] > sum(night.values()) * 0.5,
          f"{night[Activity.SLEEP]}/{sum(night.values())} asleep")
    check("the station is never fully asleep",
          sum(v for k, v in night.items() if k is not Activity.SLEEP) > 200,
          f"{sum(v for k, v in night.items() if k is not Activity.SLEEP)} awake at 03:00")

    # --- data integrity -----------------------------------------------------
    check("species mix sums to about 1",
          abs(sum(STATION_MIX.values()) - 1.0) < 0.06,
          f"{sum(STATION_MIX.values()):.3f}")
    check("every mix species has a rhythm",
          all(s in RHYTHMS for s in STATION_MIX))
    check("inferred rhythms say so in their note",
          "INFERRED" in RHYTHMS["pakmara"].note)
    check("Downbelow lurkers have no work",
          any(r.key == "lurker" and r.work_hours == 0 for r in ROLES))

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
