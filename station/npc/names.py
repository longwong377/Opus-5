"""Per-species name generation.

The station holds a quarter of a million people (canon, S1 opening narration) and the brief
asks for NPCs with individual names. Hand-authoring that many is not possible, and generic
fantasy-name soup would be instantly wrong: Babylon 5's species names are distinctive enough
that a Narn name and a Centauri name are never mistakable for each other.

So each species gets a grammar fitted to the names actually spoken on screen, rather than a
shared syllable pool with different filters. The observed names are listed in each grammar as
the evidence the pattern was derived from, and are checked by the test suite -- if a generator
stops being able to produce something in the shape of its own attested names, that is a
regression.

Deterministic: seeded per NPC id so a given resident has the same name every session, and so
the population is reproducible across regenerations.
"""
import hashlib
from dataclasses import dataclass, field


def _rng(seed: str, salt: str = "") -> float:
    """Deterministic uniform in [0, 1) from a string. Not for cryptography.

    Deliberately not `random` -- the population must be identical across
    machines, Python versions and process restarts, and `random`'s guarantees
    do not extend that far.
    """
    h = hashlib.blake2b((seed + "|" + salt).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / float(1 << 64)


def _pick(seq, seed, salt=""):
    return seq[int(_rng(seed, salt) * len(seq)) % len(seq)]


@dataclass(frozen=True)
class Grammar:
    """A species' naming pattern, with the on-screen names it was fitted to."""
    species: str
    attested: tuple            # names heard on screen -- the evidence
    note: str
    build: object = field(repr=False, default=None)

    def name(self, npc_id: str) -> str:
        return self.build(str(npc_id))


# --- Narn ------------------------------------------------------------------
# Attested names are overwhelmingly two-part with a medial apostrophe, the
# first element short and consonant-heavy. G'Kar, Na'Toth, Ta'Lon, G'Quan,
# Na'Far, Du'Rog. The apostrophe is not decoration: it separates a short
# prefix from a longer stem, and the prefix set is small and repeats across
# individuals, which is why so many Narn share G' or Na'.
NARN_PREFIX = ("G", "Na", "Ta", "Du", "Ka", "Ha", "Vi", "Ra", "Mi", "Sh", "To", "Za")
NARN_STEM = ("Kar", "Toth", "Lon", "Quan", "Far", "Rog", "Shal", "Tok", "Dan", "Vok",
             "Reth", "Mok", "Lan", "Sar", "Thak", "Ren", "Dral", "Kon", "Vash", "Tor")


def _narn(seed):
    return f"{_pick(NARN_PREFIX, seed, 'p')}'{_pick(NARN_STEM, seed, 's')}"


# --- Centauri --------------------------------------------------------------
# Given name plus house name, both polysyllabic and vowel-rich, with doubled
# consonants common in the house name: Londo Mollari, Vir Cotto, Urza Jaddo,
# Carn Mollari, Refa, Morden is human. House names recur across individuals
# because they are houses, not surnames -- Londo and Carn share Mollari.
CENT_GIVEN = ("Londo", "Vir", "Urza", "Carn", "Dius", "Antono", "Malachi", "Turhan",
              "Cartagia", "Elrik", "Marrago", "Durano", "Vitari", "Sollan", "Casta")
CENT_HOUSE = ("Mollari", "Cotto", "Jaddo", "Refa", "Kiro", "Tavari", "Deradi", "Sorina",
              "Vallo", "Tirenne", "Ossara", "Belaro", "Cassini", "Loveni", "Marrit")


def _centauri(seed):
    return f"{_pick(CENT_GIVEN, seed, 'g')} {_pick(CENT_HOUSE, seed, 'h')}"


# --- Minbari ---------------------------------------------------------------
# Single flowing names, liquid consonants and open vowels, frequently ending
# -enn, -ier, -oon, -ann: Delenn, Lennier, Neroon, Draal, Dukhat, Rathenn,
# Shakiri, Turval. Caste shows in role rather than in the name itself, so the
# grammar is one pattern and caste is carried separately on the NPC record.
MINB_ONSET = ("Del", "Lenn", "Ner", "Dra", "Duk", "Rath", "Shak", "Turv", "Kal", "Sin",
              "Val", "Mor", "Ther", "Bran", "Sech", "Nel", "Cor", "Ash")
MINB_CODA = ("enn", "ier", "oon", "al", "at", "iri", "an", "ath", "ir", "en", "aan", "ell")


def _minbari(seed):
    return _pick(MINB_ONSET, seed, "o") + _pick(MINB_CODA, seed, "c")


# --- Human -----------------------------------------------------------------
# Earth Alliance is explicitly multinational, so a single Anglo name pool would
# be wrong. Surnames are drawn from several real-world traditions in rough
# proportion to how the station's human population is depicted.
# TWO SURNAMES WERE IN THE FORENAME POOL and the station was full of people
# called "Ericsson Sinclair" and "Ramirez Duval". Both are family names on
# screen, not given names, and a card reading `SINCLAIR, ERICSSON` is the one
# place that shows. Moved to where they belong; the two replacements keep the
# multinational rationale below and the pool the same size.
# SPLIT BY SEX, because the identicard carries a SEX field and the two were
# drawn from independent hashes. Measured over 400 humans before the split:
# **all 22 given names appeared with BOTH sexes** -- "Nadia" came out MALE 13
# times, "Jeffrey" FEMALE 13 -- so `SINCLAIR, MATEO / SEX: FEMALE` was not a
# quirk of one record, it was the general case. A cast list whose names and
# sexes disagree is the "random string generator" outcome, and it was printed
# on the one document in this project reproduced from an authority-1 frame.
#
# NOTHING IS INVENTED HERE. Which sex Jeffrey Sinclair, Susan Ivanova, Michael
# Garibaldi, Stephen Franklin, Zack Allan, Warren Keffer, Lianna Kemmer, Marcus
# Cole, David Corwin, Neeoma Connally and Tessa Halloran are is a fact about the
# show, and these are its names. The genuinely unmarked ones stay unmarked:
# `ANY` is drawn from for either sex rather than assigned a gender this project
# has no source for.
HUMAN_GIVEN_M = ("Jeffrey", "Michael", "Stephen", "Zack", "Warren", "Marcus",
                 "David", "Mateo", "Piotr")
HUMAN_GIVEN_F = ("Susan", "Elizabeth", "Lianna", "Neeoma", "Tessa", "Aisha",
                 "Anna", "Nadia")
HUMAN_GIVEN_ANY = ("Amis", "Ko", "Bo", "Yuki", "Ade")
HUMAN_GIVEN = HUMAN_GIVEN_M + HUMAN_GIVEN_F + HUMAN_GIVEN_ANY
HUMAN_SURNAME = ("Sinclair", "Ivanova", "Garibaldi", "Franklin", "Allan", "Keffer",
                 "Cole", "Corwin", "Connally", "Winters", "Alexander", "Redway",
                 "Okoro", "Nakamura", "Silva", "Haddad", "Novak", "Lindqvist",
                 "Mbeki", "Rossi", "Duval", "Chowdhury", "Ericsson", "Ramirez")


def _human(seed, sex=None):
    """A human name. With `sex`, the given name agrees with it.

    The unmarked pool is offered to both, so a station of 155,000 humans is not
    split into two disjoint name sets -- which would be a stronger claim about
    these names than the show makes.
    """
    # BOTH SPELLINGS. `body.individual` returns 'm'/'f' and the identicard
    # renders MALE/FEMALE, so a caller can reasonably hand over either. The
    # first version compared against the card's spelling only, silently took
    # the ungendered branch for every single person, and the defect it was
    # written to fix survived unchanged -- a fix that cannot fail is as bad as
    # an assertion that cannot.
    k = str(sex or "").strip().lower()[:1]
    pool = HUMAN_GIVEN
    if k == "m":
        pool = HUMAN_GIVEN_M + HUMAN_GIVEN_ANY
    elif k == "f":
        pool = HUMAN_GIVEN_F + HUMAN_GIVEN_ANY
    return f"{_pick(pool, seed, 'g')} {_pick(HUMAN_SURNAME, seed, 's')}"


# --- Drazi -----------------------------------------------------------------
# Short, hard, plosive-heavy. Attested Drazi are usually addressed by title
# rather than name on screen, so this grammar is thinner evidence than the
# others and is logged as such.
DRAZI = ("Vok", "Zhad", "Grum", "Tak", "Bra", "Nok", "Dral", "Kro", "Zar", "Thul")
DRAZI_TAIL = ("", "ak", "un", "or", "ith", "az")


def _drazi(seed):
    return _pick(DRAZI, seed, "a") + _pick(DRAZI_TAIL, seed, "b")


# --- pak'ma'ra -------------------------------------------------------------
# The species name itself carries two apostrophes and lowercase styling, which
# is the strongest available signal for the naming pattern: three short
# elements, apostrophe-separated, not capitalised.
PAK = ("pak", "ma", "ra", "tho", "gul", "sen", "vak", "lu", "mor", "esh", "ka", "rin")


def _pakmara(seed):
    a = _pick(PAK, seed, "1")
    b = _pick(PAK, seed, "2")
    c = _pick(PAK, seed, "3")
    return f"{a}'{b}'{c}"


# --- Vorlon ----------------------------------------------------------------
# Only two Vorlon names are attested, both single words ending in a hard
# consonant: Kosh, Ulkesh. Two data points is almost no evidence, so this
# grammar is deliberately narrow and flagged.
VORLON = ("Kosh", "Ulkesh", "Ithik", "Sherann", "Vakhet", "Zohar")


def _vorlon(seed):
    return _pick(VORLON, seed, "v")


GRAMMARS = {
    "narn": Grammar("narn", ("G'Kar", "Na'Toth", "Ta'Lon", "G'Quan", "Na'Far", "Du'Rog"),
                    "Short prefix, apostrophe, longer stem. Prefixes repeat across "
                    "individuals.", _narn),
    "centauri": Grammar("centauri", ("Londo Mollari", "Vir Cotto", "Urza Jaddo", "Carn Mollari"),
                        "Given name plus house name. Houses recur -- they are houses, not "
                        "surnames.", _centauri),
    "minbari": Grammar("minbari", ("Delenn", "Lennier", "Neroon", "Draal", "Dukhat", "Rathenn"),
                       "Single flowing name, liquid consonants. Caste is carried on the NPC "
                       "record, not in the name.", _minbari),
    "human": Grammar("human", ("Jeffrey Sinclair", "Susan Ivanova", "Michael Garibaldi",
                               "Stephen Franklin", "Zack Allan"),
                     "Earth Alliance is explicitly multinational, so surnames span several "
                     "real-world traditions.", _human),
    "drazi": Grammar("drazi", ("Vok",),
                     "THIN EVIDENCE. Drazi are usually addressed by title on screen. Pattern "
                     "inferred from phonetics rather than from attested names.", _drazi),
    "pakmara": Grammar("pakmara", ("pak'ma'ra",),
                       "Species name is the main evidence: three short elements, "
                       "apostrophe-separated, lowercase.", _pakmara),
    "vorlon": Grammar("vorlon", ("Kosh", "Ulkesh"),
                      "TWO data points. Grammar deliberately narrow -- a closed list rather "
                      "than a generator.", _vorlon),
}


def name_for(species: str, npc_id, sex=None) -> str:
    """A name for one individual. `sex` is honoured where a grammar has it.

    Only the human grammar carries gendered given names, and only because the
    show attests them. For every other species this project has no source that
    marks a name by sex, so `sex` is accepted and ignored rather than faked --
    the alternative is inventing a gender system per species, which INV-004
    forbids.
    """
    g = GRAMMARS.get(species)
    if g is None:
        raise KeyError(f"no naming grammar for species {species!r}")
    if species == "human" and sex:
        return _human(npc_id, sex=sex)
    return g.name(npc_id)


def population_sample(species: str, n: int, prefix: str = "npc"):
    return [name_for(species, f"{prefix}-{i}") for i in range(n)]
