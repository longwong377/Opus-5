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

TWO THINGS CHANGED IN SESSION 4t, BOTH FOUND ON THE PACKAGED BUILD RATHER THAN THE DEV TREE.

1. **447 of 3,683 shipped residents (12.1%) had an EMPTY identicard NAME field**, all of them
   in the eight buckets `schedule.SPECIES_WITHOUT_NAMES` lists. That was deliberate -- INV-004
   ruled that a grammar fitted to zero attested names is invention dressed as inference, so
   those cards rendered the prop's own empty-red state. **CLAUDE.md hard rule 1 outranks that
   reading**: "the answer to 'the show never establishes this' is NEVER to leave a hole. It is
   to extrapolate in style, reason it out on the page, mark it authority 5, and record what
   would overturn it." And the project had already made exactly that call one field over --
   `npc/body.py` builds a Gaim's entire silhouette from FACTIONS 9.2's four words "methane
   breathers in encounter suits" at authority 5, with the overturning evidence named. A station
   that extrapolates a species' BODY and refuses to extrapolate its NAME is inconsistent with
   itself. INV-1249 carries the seven grammars; INV-1251 carries the `other` bucket.

2. **43 shipped residents wore a show character's exact full name** -- 29 human across 9 names
   (three Michael Garibaldis, four Susan Ivanovas, six Marcus Coles) and, unreported by any
   gate here, **14 alien**: a Narn called G'Kar, two Minbari called Delenn, two Centauri called
   Londo Mollari. `docs/spec/PEOPLE.md` CAST-01 rule 4 already forbids this -- "a stand-in must
   NOT carry the surname of the show character whose office it holds ... canon surnames
   otherwise remain in the generic pool" -- and its ACCEPT clause asks for "a grep of the
   shipped cast registry finds no show-cast given+surname pair". `SHOW_CAST` below is that
   reserved vocabulary and `_pick_clear` is the one rule that enforces it, applied at every
   draw site rather than per species. INV-1250.

   **The reserved set is READ OUT OF THE GRAMMARS, not recalled.** Every grammar already
   records the on-screen names it was fitted to in its `attested` tuple, and those are exactly
   the names a background extra must not wear. So adding an attested name reserves it in the
   same edit -- the two facts cannot drift apart, and a check built from memory (which hard
   rule 1 forbids) is impossible by construction.

   **Enforcement is by CONSTRUCTION, not by sampling.** `all_names(species)` enumerates a
   grammar's entire cross product -- every pool here is small enough that the largest is 4,752
   -- so `tools/cast_gate.py` can prove a reserved name is *unreachable* rather than observe
   that 2,000 draws missed it. That distinction is why this shipped: the existing CAST-01
   harness DID sample 2,000 human draws, and it sampled `str(i)` ids while the shipped id space
   is `res:b5:<place>:<species>:<i>`. It found 28 and the build shipped 29 different ones.
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
    """A species' naming pattern, with the on-screen names it was fitted to.

    `order` says which element of a two-word name is the LINEAGE, because that
    is not universal and the identicard is where it shows. "given-family" is
    the human and Centauri order and the default; "family-given" is Hyach, and
    it is the one piece of alienness that reaches the one authority-1 document
    this project reproduces -- see INV-1249.

    `closed` marks a grammar that is a LIST OF ATTESTED NAMES rather than a
    generator. Only Vorlon is closed, and it is exempt from the show-cast
    reservation for a reason that is a rule and not a favour: the reserved set
    IS the attested set, so filtering a closed list against it would empty the
    list of the only two names that are evidence for anything. It is safe
    because no Vorlon is ever drawn -- `schedule.STATION_COUNTS` has no vorlon
    row, Kosh is authored (`VORLON_SINGLETON`), and `tools/cast_gate.py`
    asserts that absence rather than assuming it.
    """
    species: str
    attested: tuple            # names heard on screen -- the evidence
    note: str
    build: object = field(repr=False, default=None)
    order: str = "given-family"
    closed: bool = False
    enumerate_all: object = field(repr=False, default=None)

    def name(self, npc_id: str) -> str:
        return self.build(str(npc_id))


# ---------------------------------------------------------------------------
# THE RESERVED VOCABULARY, AND THE ONE RULE THAT ENFORCES IT
# ---------------------------------------------------------------------------
# Names this module already states, in its own comments, are facts about the
# show. Cited rather than recalled, because hard rule 1 applies to a blocklist
# as much as to a dimension:
#
#   * the eleven human names in `HUMAN_GIVEN`/`HUMAN_SURNAME`'s own comment
#     ("Which sex Jeffrey Sinclair, Susan Ivanova, Michael Garibaldi, Stephen
#     Franklin, Zack Allan, Warren Keffer, Lianna Kemmer, Marcus Cole, David
#     Corwin, Neeoma Connally and Tessa Halloran are is a fact about the show");
#   * "ALEXANDER, LYTA" -- the authority-1 identicard transcribed in
#     `canon/00-MASTER.md` 1.4 and quoted at the top of `npc/resident.py`;
#   * the five names `docs/spec/PEOPLE.md` CAST-01 rules 1 and 5 name as
#     characters that must not appear: Deuce, Jinxo, N'Grath, Talia, Keffer.
#     Ombuds Wellington and Zimmerman are NOT here -- rule 5 keeps them as
#     named offices, so reserving them would forbid content the spec wants.
#
# Everything alien comes out of the grammars' own `attested` tuples below, so
# it is not repeated here.
SHOW_CAST_EXTRA = (
    "Jeffrey Sinclair", "Susan Ivanova", "Michael Garibaldi", "Stephen Franklin",
    "Zack Allan", "Warren Keffer", "Lianna Kemmer", "Marcus Cole",
    "David Corwin", "Neeoma Connally", "Tessa Halloran",
    "Lyta Alexander", "Talia Winters",
    "Deuce", "Jinxo", "N'Grath", "Talia", "Keffer",
)


def _pick_clear(seq, seed, salt, finish):
    """Pick from `seq`, having first dropped every choice that finishes RESERVED.

    THE RULE, AND IT LIVES IN ONE PLACE ON PURPOSE. CLAUDE.md: "a fix applied
    to an instance and not to the rule is a fix that will be needed again" --
    the previous attempt at this problem lived in the CAST-01 harness, checked
    humans only, and the shipped build carried fourteen alien collisions it had
    no way to see.

    FILTERING, NOT RETRYING. A redraw loop terminates only probabilistically
    and its bound is an argument; removing the reserved choices from the pool
    makes the name unreachable, which is a property. The cost is that every
    resident sharing the reserved name's first element shifts one slot along
    the pool -- deterministic, and the whole population is regenerated from the
    id anyway.
    """
    ok = tuple(x for x in seq if finish(x) not in RESERVED)
    if not ok:
        raise ValueError(
            f"every choice in a pool of {len(seq)} finishes as a reserved "
            f"name; the pool cannot be filtered to nothing")
    return _pick(ok, seed, salt)


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
    p = _pick(NARN_PREFIX, seed, "p")
    return p + "'" + _pick_clear(NARN_STEM, seed, "s", lambda s: p + "'" + s)


def _narn_all():
    return {f"{p}'{s}" for p in NARN_PREFIX for s in NARN_STEM}


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
    g = _pick(CENT_GIVEN, seed, "g")
    return g + " " + _pick_clear(CENT_HOUSE, seed, "h", lambda h: g + " " + h)


def _centauri_all():
    return {f"{g} {h}" for g in CENT_GIVEN for h in CENT_HOUSE}


# --- Minbari ---------------------------------------------------------------
# Single flowing names, liquid consonants and open vowels, frequently ending
# -enn, -ier, -oon, -ann: Delenn, Lennier, Neroon, Draal, Dukhat, Rathenn,
# Shakiri, Turval. Caste shows in role rather than in the name itself, so the
# grammar is one pattern and caste is carried separately on the NPC record.
MINB_ONSET = ("Del", "Lenn", "Ner", "Dra", "Duk", "Rath", "Shak", "Turv", "Kal", "Sin",
              "Val", "Mor", "Ther", "Bran", "Sech", "Nel", "Cor", "Ash")
MINB_CODA = ("enn", "ier", "oon", "al", "at", "iri", "an", "ath", "ir", "en", "aan", "ell")


def _minbari(seed):
    o = _pick(MINB_ONSET, seed, "o")
    return o + _pick_clear(MINB_CODA, seed, "c", lambda c: o + c)


def _minbari_all():
    return {o + c for o in MINB_ONSET for c in MINB_CODA}


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
    # THE SURNAME IS DRAWN FIRST AND THE GIVEN NAME IS FILTERED AGAINST IT,
    # which is the order CAST-01 rule 4 asks for: "canon surnames otherwise
    # remain in the generic pool" -- a background Sinclair is fine, a
    # background *Jeffrey* Sinclair is not. Filtering the surname instead
    # would have removed eleven real surnames from a multinational pool of 24.
    s = _pick(HUMAN_SURNAME, seed, "s")
    return _pick_clear(pool, seed, "g", lambda g: g + " " + s) + " " + s


def _human_all():
    return {f"{g} {s}" for g in HUMAN_GIVEN for s in HUMAN_SURNAME}


# --- Drazi -----------------------------------------------------------------
# Short, hard, plosive-heavy. Attested Drazi are usually addressed by title
# rather than name on screen, so this grammar is thinner evidence than the
# others and is logged as such.
DRAZI = ("Vok", "Zhad", "Grum", "Tak", "Bra", "Nok", "Dral", "Kro", "Zar", "Thul")
DRAZI_TAIL = ("", "ak", "un", "or", "ith", "az")


def _drazi(seed):
    a = _pick(DRAZI, seed, "a")
    return a + _pick_clear(DRAZI_TAIL, seed, "b", lambda b: a + b)


def _drazi_all():
    return {a + b for a in DRAZI for b in DRAZI_TAIL}


# --- pak'ma'ra -------------------------------------------------------------
# The species name itself carries two apostrophes and lowercase styling, which
# is the strongest available signal for the naming pattern: three short
# elements, apostrophe-separated, not capitalised.
PAK = ("pak", "ma", "ra", "tho", "gul", "sen", "vak", "lu", "mor", "esh", "ka", "rin")


def _pakmara(seed):
    a = _pick(PAK, seed, "1")
    b = _pick(PAK, seed, "2")
    # AND THE THIRD ELEMENT IS FILTERED, which catches a defect nobody had
    # named: `PAK` holds "pak", "ma" and "ra", so the grammar could produce
    # `pak'ma'ra` -- an individual whose personal name is the word for their
    # entire species. It is reserved automatically because the species word is
    # this grammar's own `attested` entry, which is the whole argument for
    # building the reserved set out of the evidence rather than by hand.
    c = _pick_clear(PAK, seed, "3", lambda c: a + "'" + b + "'" + c)
    return f"{a}'{b}'{c}"


def _pakmara_all():
    return {f"{a}'{b}'{c}" for a in PAK for b in PAK for c in PAK}


# --- Vorlon ----------------------------------------------------------------
# Only two Vorlon names are attested, both single words ending in a hard
# consonant: Kosh, Ulkesh. Two data points is almost no evidence, so this
# grammar is deliberately narrow and flagged.
VORLON = ("Kosh", "Ulkesh", "Ithik", "Sherann", "Vakhet", "Zohar")


def _vorlon(seed):
    return _pick(VORLON, seed, "v")


def _vorlon_all():
    return set(VORLON)


# ===========================================================================
# THE SEVEN THAT HAD NO GRAMMAR -- INV-1249
# ===========================================================================
# Every one of these species already has an EXTRAPOLATED BODY in `npc/body.py`
# at authority 5, sourced from one line of `docs/gazetteer/FACTIONS.md` 9.2 and
# carrying its own "what would overturn it". So the precedent for extrapolating
# them is this repository's, not mine; what was inconsistent was extrapolating
# the silhouette and refusing the name.
#
# THE METHOD IS THE ONE THIS FILE ALREADY USED FOR PAK'MA'RA, and it is the
# only method available when the reference set attests no personal name: the
# SPECIES WORD ITSELF is a real, on-screen word in that species' own phonology,
# so it is evidence about the phonotactics even though it is evidence about
# nothing else. Each grammar below is fitted to its own species word and then
# shaped by the ONE line of character FACTIONS 9.2 gives it. Both inputs are
# named in each block. Authority 5 throughout; overturned by any attested
# personal name, which goes in the `attested` tuple and re-runs the tests --
# INV-004's stated workflow, unchanged.
#
# SIZING IS DERIVED, NOT PICKED. Each cross product is set so the station's
# own headcount for that species (`schedule.STATION_COUNTS`) does not exhaust
# it: the existing human grammar offers 528 names to 155,000 people and Narn
# 240 to 22,500, so the bar these are held to is the bar the file already sets,
# and the smallest new grammar (Grome, 168 for 750) sits at the same order.

# --- Brakiri ---------------------------------------------------------------
# Species word: "Brakiri" -- cluster onset Br-, light -iri tail, no hard stop
# at the end. FACTIONS 9.2: "Traders and financiers; night dwellers", clustering
# in the Business District, Zocalo and Casino.
# TWO ELEMENTS JOINED BY A HYPHEN, and the hyphen is the reasoned part. A
# financier is identified on a contract by person AND house, which argues for
# two elements; making them two WORDS would have given Brakiri the same visible
# shape as human, Centauri and Hyach names, and this file's whole premise is
# that "a Narn name and a Centauri name are never mistakable for each other".
# The hyphen is the transliteration EA records already use for a bound
# two-element alien name -- the same decision the record makes when it keeps
# pak'ma'ra's apostrophes.
BRAK_PERSONAL = ("Torbek", "Krasil", "Brakan", "Dranek", "Zhabir", "Tessik",
                 "Mordak", "Vrasim", "Halbek", "Ostrek", "Nakiri", "Ferakh",
                 "Dobrin", "Semikh", "Turbal", "Kravic", "Belsir", "Ondrek",
                 "Tarnik", "Vesbar")
BRAK_HOUSE = ("Ashem", "Vashal", "Drenim", "Kolbar", "Tirakh", "Semvar",
              "Brannik", "Oskeri", "Zhemal", "Lubrin", "Karsim", "Hedrak",
              "Norvim", "Casbek", "Elrash", "Timbari")


def _brakiri(seed):
    p = _pick(BRAK_PERSONAL, seed, "p")
    return p + "-" + _pick_clear(BRAK_HOUSE, seed, "h", lambda h: p + "-" + h)


def _brakiri_all():
    return {p + "-" + h for p in BRAK_PERSONAL for h in BRAK_HOUSE}


# --- Vree ------------------------------------------------------------------
# Species word: "Vree" -- consonant cluster, then a DOUBLED VOWEL, and that
# doubled vowel is the only distinctive thing the word carries, so it is the
# signature. FACTIONS 9.2: "Traders; saucer craft". `body.py` builds them at
# 1.50 m with a large flat-faced cranium and calls its own entry "EXTRAPOLATED
# and WEAK"; a small high-headed species is given a thin, fricative phonology
# to match, which is the same inference in sound that the body made in shape.
# "Dr" IS DELIBERATELY ABSENT. It was here, and `cast_gate.py --D` reported
# `CLASH ('minbari', 'vree', ['Draan', 'Draath'])`: Minbari build "Dra" + "aan"
# and Vree built "Dr" + "aa" + "n", and the two grammars landed on the same
# string. The founding claim of this file is that two species' names are never
# mistakable, so an onset that makes them identical is the thing that gives.
VREE_ONSET = ("Vr", "Shr", "Zh", "Kr", "Thr", "Sr", "Fl", "Chr", "Vl", "Skr",
              "Pr", "Tr", "Gl", "Sv", "Zv", "Str", "Sn", "Kl")
VREE_NUCLEUS = ("ee", "aa", "ii", "oo", "uu")
VREE_CODA = ("n", "l", "sh", "th", "k")


def _vree(seed):
    o = _pick(VREE_ONSET, seed, "o")
    n = _pick(VREE_NUCLEUS, seed, "n")
    return o + n + _pick_clear(VREE_CODA, seed, "c", lambda c: o + n + c)


def _vree_all():
    return {o + n + c for o in VREE_ONSET for n in VREE_NUCLEUS for c in VREE_CODA}


# --- Abbai -----------------------------------------------------------------
# Species word: "Abbai" -- VOWEL-INITIAL, geminate consonant, vowel-final. It
# is the only vowel-initial species word in the whole reference set, which
# makes it the one grammar here a reader can identify from its first letter.
# FACTIONS 9.2: "League founders; mediators; amphibian". A mediator's name
# ending open rather than on a hard stop is the same inference `body.py` made
# when it gave the Abbai one soft swept fin and nothing else.
ABB_VOWEL = ("A", "E", "I", "O", "U")
ABB_STEM = ("bba", "mma", "ssa", "lla", "nna", "ddi", "rri", "kko", "ppa",
            "tti", "ffe", "zza")
ABB_TAIL = ("i", "ra", "li", "shu", "mi", "na")


def _abbai(seed):
    v = _pick(ABB_VOWEL, seed, "v")
    s = _pick(ABB_STEM, seed, "s")
    return v + s + _pick_clear(ABB_TAIL, seed, "t", lambda t: v + s + t)


def _abbai_all():
    return {v + s + t for v in ABB_VOWEL for s in ABB_STEM for t in ABB_TAIL}


# --- Gaim ------------------------------------------------------------------
# THIS ONE IS NOT A PERSONAL NAME, AND THAT IS THE POINT. FACTIONS 9.2 calls
# the Gaim "hive-caste insectoids" at authority 4, and `npc/resident.py`
# ALREADY ACTED ON THAT ONCE: `HIVE_SPECIES` refuses the SEX field for them,
# because "an Earth Alliance customs form with a two-value sex field does not
# fit a hive". The identical argument reaches the NAME field, and it reaches a
# different answer than "leave it blank" -- a customs officer with a hive
# individual in front of them writes down the identifier that individual
# answers to, which for a hive is BROOD and POSITION WITHIN IT.
#
# So a Gaim designation is `<brood>-<n>`, a single token, and the card renders
# it whole: `ZHAMAIM-47`. It is visibly a designation rather than a name, which
# is the honest rendering of what the station knows.
#
# THE ORDINAL RANGE IS DERIVED. FACTIONS 9.2 puts 2,500 Gaim aboard. 48 brood
# words x ordinals 1..99 is 4,752 designations, so the station's Gaim can each
# carry a distinct one with room over; 1..24 would have given 1,152 and forced
# collisions the record could not tell apart.
GAIM_ONSET = ("Zha", "Kre", "Mok", "Vash", "Thra", "Ssu", "Nge", "Gai")
GAIM_CODA = ("maim", "kesh", "roth", "shal", "vekh", "nurr")
GAIM_ORDINALS = 99


def _gaim(seed):
    o = _pick(GAIM_ONSET, seed, "o")
    c = _pick(GAIM_CODA, seed, "c")
    # THE ORDINAL GOES THROUGH THE RULE TOO, and it is not decoration. This
    # generator originally picked the ordinal with a bare `_pick` on the
    # grounds that no show character is called `Zhamaim-47`, which is true and
    # is not the point: `cast_gate.py`'s C1 instruments `_pick_clear` and calls
    # every grammar, and it reported "12 of 13 reached _pick_clear; MISSING
    # ['gaim']". A rule with an exception nobody wrote down is a rule that will
    # be missing again when the reserved set grows.
    n = _pick_clear(tuple(range(1, GAIM_ORDINALS + 1)), seed, "n",
                    lambda k: f"{o}{c}-{k}")
    return f"{o}{c}-{n}"


def _gaim_all():
    return {f"{o}{c}-{n}" for o in GAIM_ONSET for c in GAIM_CODA
            for n in range(1, GAIM_ORDINALS + 1)}


# --- Hyach -----------------------------------------------------------------
# Species word: "Hyach" -- a palatal glide onset (Hy-) and a fricative coda
# (-ch), and both recur through the vocabulary below. It is also the ONE of
# these seven with any frame behind it: `reference/00-INDEX.md` records an
# authority-1 Council delegation name-plate reading "HYAC..." with the rest
# occluded. That plate is a DELEGATION name, not a person's, so it constrains
# the phonology and nothing else -- which is exactly what it is used for.
#
# FACTIONS 9.2: "Long-lived, formal". Formality is what makes the name two
# elements rather than one. Long-lived is what puts the LINEAGE FIRST: a
# species that outlives its own institutions identifies by the thing that
# persists, so a Hyach written in full is `<lineage> <personal>` -- the
# inverse of the human order. `Grammar.order` carries that, `resident.py`
# reads it, and the identicard consequently renders `HYAVANN, TESH` with
# HYAVANN the lineage where a human card has the family name. It is the only
# place in this project where the card's two halves swap meaning, and it costs
# one field to say so instead of silently mislabelling 1,750 people.
HYACH_LINEAGE = ("Hyavann", "Nyoreth", "Kyavesh", "Tyaloch", "Shyareth",
                 "Hyunneth", "Myavach", "Lyoseth", "Gyareth", "Nyulech",
                 "Chyavan", "Ryoneth", "Hyalach", "Kyunesh", "Tyaresh",
                 "Syovach")
HYACH_PERSONAL = ("Tesh", "Valach", "Norech", "Suvann", "Ileth", "Marech",
                  "Ossan", "Yaleth", "Turach", "Nevesh", "Alech", "Rivann",
                  "Sonach", "Emeth", "Kavesh", "Uleth", "Dorach", "Sevann")


def _hyach(seed):
    ln = _pick(HYACH_LINEAGE, seed, "l")
    return ln + " " + _pick_clear(HYACH_PERSONAL, seed, "p",
                                  lambda p: ln + " " + p)


def _hyach_all():
    return {ln + " " + p for ln in HYACH_LINEAGE for p in HYACH_PERSONAL}


# --- Llort -----------------------------------------------------------------
# Species word: "Llort" -- a DOUBLED-CONSONANT onset and a hard cluster coda,
# and the doubled onset is unmistakable on a page, which is the signature.
# FACTIONS 9.2: "Reputation as scavengers and thieves", clustering in
# Downbelow, the docks and the markets. `body.py` built them short, long-armed
# and stooped for the same line. A single blunt token is what a name is when
# it is the one somebody is called in a market rather than the one on a
# registry -- and it is deliberately the shortest grammar here.
LLORT_ONSET = ("Ll", "Rr", "Nn", "Mm", "Zz", "Kk", "Tt", "Dd", "Gg", "Vv",
               "Ss", "Bb")
LLORT_CODA = ("ort", "urk", "ask", "ist", "ekt", "unt", "arg", "osk", "irt",
              "ugh", "akt", "esk", "olt", "ump", "irk", "ost", "ans", "ubb")


def _llort(seed):
    o = _pick(LLORT_ONSET, seed, "o")
    return o + _pick_clear(LLORT_CODA, seed, "c", lambda c: o + c)


def _llort_all():
    return {o + c for o in LLORT_ONSET for c in LLORT_CODA}


# --- Grome -----------------------------------------------------------------
# THE THINNEST OF THE SEVEN AND IT SAYS SO. FACTIONS 9.2's character column for
# the Grome is LITERALLY EMPTY -- the only species row in the table that has
# nothing in it. All that is left is the placement ("Hydroponics, labour") and
# the species word: "Grome", a heavy cluster onset over a round back vowel.
# So the grammar is the species word's own shape and nothing more: cluster
# onset, round coda, one word, no ornament. `body.py` reached the same place
# from the same absence and built the largest humanoid on the station.
GROME_ONSET = ("Gr", "Br", "Dr", "Thr", "Kr", "Skr", "Vr", "Ghr", "Tr", "Chr",
               "Pr", "Shr", "Zr", "Str")
GROME_CODA = ("om", "ome", "un", "on", "olo", "ovek", "orn", "umal", "oth",
              "ogun", "omek", "ulo")


def _grome(seed):
    o = _pick(GROME_ONSET, seed, "o")
    return o + _pick_clear(GROME_CODA, seed, "c", lambda c: o + c)


def _grome_all():
    return {o + c for o in GROME_ONSET for c in GROME_CODA}


# --- other -----------------------------------------------------------------
# NOT A SPECIES AND IT MUST NOT GET A GRAMMAR. `body.py` is explicit: "The
# tail: rare League species, unidentified traders, one-off visitors ... It is a
# distribution, not a species", and FACTIONS 2.4 asks for a rotating model set
# "so the tail never looks like the same six aliens".
#
# So the naming answer is the same answer body.py gave the meshes: A
# DISTRIBUTION OVER THE GRAMMARS. Each individual picks one alien grammar by
# hash and is named by it. That fills the field, makes no claim about any
# species, and gives the tail the variety 2.4 asks for -- 2,540 reachable names
# across ten shapes instead of one blank.
#
# FOUR GRAMMARS ARE EXCLUDED AND EACH FOR ITS OWN REASON:
#   human   -- the row is "RARE SPECIES and one-off visitors"; a human in it
#              would be a human, and humans have their own 155,000-strong row.
#   vorlon  -- a closed list of two attested names plus four inventions, and
#              the only Vorlon aboard is authored. Drawing "Kosh" for a
#              background extra is the exact defect this session is closing.
#   gaim    -- its designation asserts a brood and a hive-caste structure.
#   hyach   -- its order asserts a lineage-first naming culture.
# The last two are excluded because they encode a specific INSTITUTION, and an
# unidentified traveller cannot be assumed into one. The remaining ten encode
# only phonology, which is the most an unidentified species can borrow.
OTHER_GRAMMARS = ("narn", "centauri", "minbari", "drazi", "pakmara",
                  "brakiri", "vree", "abbai", "llort", "grome")


def _other(seed):
    return GRAMMARS[_pick(OTHER_GRAMMARS, seed, "sp")].build(seed)


def _other_all():
    out = set()
    for sp in OTHER_GRAMMARS:
        out |= GRAMMARS[sp].enumerate_all()
    return out


GRAMMARS = {
    "narn": Grammar("narn", ("G'Kar", "Na'Toth", "Ta'Lon", "G'Quan", "Na'Far", "Du'Rog"),
                    "Short prefix, apostrophe, longer stem. Prefixes repeat across "
                    "individuals.", _narn, enumerate_all=_narn_all),
    "centauri": Grammar("centauri", ("Londo Mollari", "Vir Cotto", "Urza Jaddo", "Carn Mollari"),
                        "Given name plus house name. Houses recur -- they are houses, not "
                        "surnames.", _centauri, enumerate_all=_centauri_all),
    "minbari": Grammar("minbari", ("Delenn", "Lennier", "Neroon", "Draal", "Dukhat", "Rathenn"),
                       "Single flowing name, liquid consonants. Caste is carried on the NPC "
                       "record, not in the name.", _minbari, enumerate_all=_minbari_all),
    "human": Grammar("human", ("Jeffrey Sinclair", "Susan Ivanova", "Michael Garibaldi",
                               "Stephen Franklin", "Zack Allan"),
                     "Earth Alliance is explicitly multinational, so surnames span several "
                     "real-world traditions.", _human, enumerate_all=_human_all),
    "drazi": Grammar("drazi", ("Vok",),
                     "THIN EVIDENCE. Drazi are usually addressed by title on screen. Pattern "
                     "inferred from phonetics rather than from attested names.", _drazi,
                     enumerate_all=_drazi_all),
    "pakmara": Grammar("pakmara", ("pak'ma'ra",),
                       "Species name is the main evidence: three short elements, "
                       "apostrophe-separated, lowercase.", _pakmara,
                       enumerate_all=_pakmara_all),
    "vorlon": Grammar("vorlon", ("Kosh", "Ulkesh"),
                      "TWO data points. Grammar deliberately narrow -- a closed list rather "
                      "than a generator.", _vorlon, closed=True, enumerate_all=_vorlon_all),

    # --- INV-1249: the seven that shipped 447 blank identicards -------------
    "brakiri": Grammar("brakiri", ("Brakiri",),
                       "NO ATTESTED PERSONAL NAME; the main evidence is the species word: "
                       "cluster onset, light -iri tail. Two elements hyphenated, because "
                       "FACTIONS 9.2 makes them financiers and a financier is a person AND "
                       "a house on a contract.", _brakiri, enumerate_all=_brakiri_all),
    "vree": Grammar("vree", ("Vree",),
                    "NO ATTESTED PERSONAL NAME; the main evidence is the species word, whose "
                    "one distinctive feature is a DOUBLED VOWEL -- so that is the signature. "
                    "Short and thin to match body.py's 1.50 m large-craniumed build.",
                    _vree, enumerate_all=_vree_all),
    "abbai": Grammar("abbai", ("Abbai",),
                     "NO ATTESTED PERSONAL NAME; the main evidence is the species word: the "
                     "only VOWEL-INITIAL species word in the reference set, with a geminate "
                     "consonant and an open ending. Mediators' names do not end on a stop.",
                     _abbai, enumerate_all=_abbai_all),
    "gaim": Grammar("gaim", ("Gaim",),
                    "NOT A PERSONAL NAME; the main evidence is the species word plus FACTIONS "
                    "9.2's 'hive-caste', which resident.py ALREADY acted on once by refusing "
                    "the SEX field. A brood designation and an ordinal, rendered whole.",
                    _gaim, enumerate_all=_gaim_all),
    "hyach": Grammar("hyach", ("Hyach",),
                     "NO ATTESTED PERSONAL NAME, but the ONLY one of the seven with a frame "
                     "behind it -- an authority-1 Council name-plate reading 'HYAC...'. That "
                     "is a DELEGATION name, so the main evidence is still phonology alone. "
                     "Lineage first, from FACTIONS 9.2's 'long-lived, formal'.",
                     _hyach, order="family-given", enumerate_all=_hyach_all),
    "llort": Grammar("llort", ("Llort",),
                     "NO ATTESTED PERSONAL NAME; the main evidence is the species word: a "
                     "DOUBLED-CONSONANT onset over a hard cluster coda. One blunt token, "
                     "which is what a name is when it is a market name rather than a "
                     "registry one.", _llort, enumerate_all=_llort_all),
    "grome": Grammar("grome", ("Grome",),
                     "THE THINNEST GRAMMAR HERE and it says so: FACTIONS 9.2's character "
                     "column for the Grome is literally empty, so the main evidence is the "
                     "word alone -- heavy cluster onset, round back vowel, no ornament.",
                     _grome, enumerate_all=_grome_all),
    "other": Grammar("other", ("Vree", "Abbai", "Llort"),
                     "NOT A SPECIES -- body.py calls it 'a distribution, not a species'. A "
                     "DISTRIBUTION OVER TEN GRAMMARS, one drawn per individual, which is the "
                     "naming form of FACTIONS 2.4's rotating model set. Its attested tuple "
                     "is a sample of the species words it borrows from.",
                     _other, enumerate_all=_other_all),
}


# THE RESERVED SET, BUILT FROM THE GRAMMARS' OWN EVIDENCE. Every `attested`
# entry is by definition a name spoken on screen (or, for the seven above, the
# species' own word), and neither is something a background extra may wear.
# Constructing it this way is what makes it self-maintaining: an attested name
# added to a grammar is reserved in the same edit, so the blocklist can never
# fall behind the evidence. Compare the alternative -- a hand-written list,
# which is an unmarked invention with a boolean on the end.
RESERVED = frozenset(
    tuple(SHOW_CAST_EXTRA)
    + tuple(n for g in GRAMMARS.values() for n in g.attested)
)
# Kept as the public name for the same set: `SHOW_CAST` is what the check
# reads, `RESERVED` is what `_pick_clear` filters against, and they are one
# object so they cannot disagree.
SHOW_CAST = RESERVED


def name_for(species: str, npc_id, sex=None) -> str:
    """A name for one individual. `sex` is honoured where a grammar has it.

    Only the human grammar carries gendered given names, and only because the
    show attests them. For every other species this project has no source that
    marks a name by sex, so `sex` is accepted and ignored rather than faked --
    the alternative is inventing a gender system per species, which INV-004
    forbids.

    RAISES for an unknown species, and that raise now has teeth. Until INV-1249
    it fired for eight of the fifteen species aboard and `resident._split_name`
    swallowed it into an empty NAME field -- so a genuine typo in a species
    string was indistinguishable from a species the show never named, and both
    shipped as a blank card. Every species in `schedule.STATION_COUNTS` and in
    `body.SPECIES` now has a grammar (`tools/cast_gate.py` asserts it), so the
    only thing this can still catch is the typo.
    """
    g = GRAMMARS.get(species)
    if g is None:
        raise KeyError(f"no naming grammar for species {species!r}")
    if species == "human" and sex:
        return _human(npc_id, sex=sex)
    return g.name(npc_id)


def split_name(species: str, full: str):
    """`(family, given)` for a full name, honouring the species' own order.

    Lives here rather than in `resident.py` because the ORDER is a property of
    the grammar, and a caller that has to know which species inverts is a
    caller that will get it wrong. Hyach is the one that inverts -- see the
    Hyach block above. A one-element name is all family and no given, which is
    how the card renders a Narn or a Gaim.
    """
    if " " not in full:
        return full, ""
    a, b = full.split(" ", 1)
    g = GRAMMARS.get(species)
    if g is not None and g.order == "family-given":
        return a, b
    return b, a


def all_names(species: str) -> set:
    """Every name this grammar's VOCABULARY can spell, filter or no filter.

    This is the raw cross product and it deliberately still contains the show
    cast: `all_names("minbari")` holds Delenn, `all_names("human")` holds
    Michael Garibaldi. That is the hazard the reservation exists to remove, and
    a gate that could not see it could not show its own work.

    Small enough to enumerate -- the largest is Gaim's 4,752 -- which is what
    lets a check reason about EVERY name a grammar could spell, where the
    previous one drew 2,000 humans, found 28 collisions, and could say nothing
    about the draws it had not made.
    """
    g = GRAMMARS.get(species)
    if g is None:
        raise KeyError(f"no naming grammar for species {species!r}")
    if g.enumerate_all is None:
        raise KeyError(f"grammar {species!r} cannot enumerate itself")
    return g.enumerate_all()


def reachable_names(species: str) -> set:
    """Every name a DRAW can actually return.

    Equal to `all_names(species) - RESERVED`, and that equality is a
    consequence of `_pick_clear` rather than a restatement of it: the filter
    keys on the FINISHED name, so removing the reserved finished names from the
    product is exactly what the draw does. The equality holds only while every
    generator routes its final element through `_pick_clear`, which is not
    something source can be trusted about -- `tools/cast_gate.py` instruments
    the function and CALLS every grammar to prove each one reaches it.

    A closed grammar is exempt and returns its list unchanged; see `Grammar`.
    """
    g = GRAMMARS.get(species)
    if g is None:
        raise KeyError(f"no naming grammar for species {species!r}")
    if g.closed:
        return set(g.enumerate_all())
    return set(g.enumerate_all()) - RESERVED


def population_sample(species: str, n: int, prefix: str = "npc"):
    return [name_for(species, f"{prefix}-{i}") for i in range(n)]
