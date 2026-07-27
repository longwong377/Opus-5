"""Tests for per-species name generation.

The point is that species stay distinguishable and that generation is
deterministic. A name generator that drifts toward a common phonetic mush is
the failure mode worth guarding against.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from names import GRAMMARS, name_for, population_sample

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))


def main():
    # --- determinism --------------------------------------------------------
    check("same id gives the same name every time",
          all(name_for(s, "npc-42") == name_for(s, "npc-42") for s in GRAMMARS))
    check("different ids give different names",
          name_for("narn", "npc-1") != name_for("narn", "npc-2"))

    # --- species stay distinguishable ---------------------------------------
    narn = population_sample("narn", 200)
    cent = population_sample("centauri", 200)
    minb = population_sample("minbari", 200)
    pak = population_sample("pakmara", 200)
    human = population_sample("human", 200)

    check("Narn names all carry a medial apostrophe",
          all(re.fullmatch(r"[A-Z][a-z]?'[A-Z][a-z]+", n) for n in narn),
          narn[0])
    check("Centauri names are two words",
          all(len(n.split()) == 2 for n in cent), cent[0])
    check("Minbari names are a single word with no apostrophe",
          all(" " not in n and "'" not in n for n in minb), minb[0])
    check("pak'ma'ra names are lowercase with two apostrophes",
          all(n.islower() and n.count("'") == 2 for n in pak), pak[0])
    check("human names are two words with no apostrophe",
          all(len(n.split()) == 2 and "'" not in n for n in human), human[0])

    # No name generated for one species may be generable by another.
    overlap = set(narn) & set(cent) | set(narn) & set(minb) | set(cent) & set(minb)
    check("no name is shared between species", not overlap, str(list(overlap)[:3]))

    # --- variety ------------------------------------------------------------
    for sp in ("narn", "centauri", "minbari", "human"):
        pool = population_sample(sp, 500)
        uniq = len(set(pool))
        check(f"{sp} produces variety over 500 draws", uniq > 150,
              f"{uniq} distinct")

    # Vorlon is deliberately a closed list, so it must NOT show variety.
    v = set(population_sample("vorlon", 200))
    check("Vorlon is a closed list, not a generator", len(v) <= 8,
          f"{len(v)} distinct -- two names are attested, so a generator would be invention")

    # --- attested names stay reachable in shape -----------------------------
    # Not that the generator produces the exact attested names, but that the
    # attested names would pass the generator's own shape test. If a grammar
    # drifts so far that G'Kar no longer looks Narn, it has stopped modelling
    # the thing it was fitted to.
    check("G'Kar matches the Narn shape",
          bool(re.fullmatch(r"[A-Z][a-z]?'[A-Z][a-z]+", "G'Kar")))
    check("Na'Toth matches the Narn shape",
          bool(re.fullmatch(r"[A-Z][a-z]?'[A-Z][a-z]+", "Na'Toth")))
    check("Londo Mollari matches the Centauri shape",
          len("Londo Mollari".split()) == 2)
    check("Delenn matches the Minbari shape",
          " " not in "Delenn" and "'" not in "Delenn")
    check("pak'ma'ra matches its own shape",
          "pak'ma'ra".islower() and "pak'ma'ra".count("'") == 2)

    # --- evidence is recorded -----------------------------------------------
    check("every grammar records the names it was fitted to",
          all(len(g.attested) >= 1 for g in GRAMMARS.values()))
    thin = [s for s, g in GRAMMARS.items() if len(g.attested) <= 2]
    check("thin-evidence grammars are flagged in their note",
          all("THIN" in GRAMMARS[s].note or "TWO" in GRAMMARS[s].note
              or "main evidence" in GRAMMARS[s].note for s in thin),
          f"thin: {thin}")

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
