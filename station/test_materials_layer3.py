"""Layer 3's coverage and plausibility gate: every interior surface, checked.

WHY THIS EXISTS RATHER THAN A REVIEWER
---------------------------------------
The first plan for layer 3 was seven proposing agents each shadowed by an
adversarial reviewer, per CLAUDE.md's loop. Two things were wrong with it.

The machine runs **two agents at a time** (`min(16, cores - 2)` on four cores),
so fourteen agents is a queue seven deep, not a fan-out — about an hour and
three quarters of wall clock for work that has to survive a session limit.

More importantly, **most of what the reviewer was being asked to check is
computable**, and a reviewer is the wrong instrument for a computable question.
"Does every one of the 113 groups resolve", "does any bind fragment swallow a
group it should not", "is this albedo inside the measured neutral band", "is
metallic a physical value" — a program answers those exactly, cannot be argued
out of a finding, and keeps answering them on every push. An LLM asked the same
question answers it once, approximately, and then the answer rots.

So the reviewer's checklist is split. Everything mechanical is here. What is
left for a reviewer is the one genuinely aesthetic question — *does this read as
Babylon 5, season 2-3* — which no assertion can settle.

WHAT IT CHECKS
--------------
  1. COVERAGE. Every group emitted by `rooms.py` for all 68 procedural
     locations resolves to a material in the interior scene. This is the layer's
     definition of done and it is a number, not an opinion.
  2. FRAGMENT AMBIGUITY. Substring matching with longest-wins is quietly
     dangerous: `_wall` and `prop_monitor_wall` both match one group, and which
     wins is decided by name length rather than by anyone's intent. Any group
     two materials both claim is a defect.
  3. THE MEASURED PALETTE. `materials.py` PROVENANCE records that interior
     structural surfaces are neutral and that saturation above 0.20 belongs to
     the accent registers. Asserted per material rather than trusted.
  4. PHYSICAL PLAUSIBILITY. Ranges, and the one rule that survived contact
     with the reviewed library: roughness below 0.15 is glass, still water or
     polished metal and nothing else. A bimodal-metallic rule was drafted and
     DROPPED -- see the note by ROUGHNESS_MIRROR. It failed nineteen reviewed
     materials, which meant it was wrong about the corpus.
  5. DECK AGAINST WALL. Per archetype, the deck must be darker AND smoother
     than the wall it meets — the measured relationship, and the one that makes
     a floor read as a floor.
  6. SOURCED MEANS SOURCED. A `source` string that names a file must name a
     file that exists; one that names a reference frame must name a frame that
     exists and is not quarantined. CLAUDE.md's cardinal sin is a number that
     looks sourced and is not, and a proposer under pressure writes plausible
     source strings.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                          # noqa: E402
import rooms as R                                              # noqa: E402
import materials as M                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Saturation ceiling for a structural surface. From materials.py PROVENANCE:
# "these are the only saturations above 0.20 that survive the cast correction",
# said of the four ACCENT registers. Anything structural above it is either a
# measurement nobody made or the sector-colour mistake.
STRUCTURAL_SAT_MAX = 0.20

# NO BIMODALITY RULE, and the reason is worth writing down. The first draft
# asserted metallic is 0 or ~1 with a dead zone between, which is how the real
# world works and how most PBR guides put it. Run against the existing library
# it failed NINETEEN reviewed materials, including `hull_exterior` at 0.34 --
# a measured value from `exterior more.jpg`. The library's metallic values are
# continuous from 0.0 to 0.8, so this project authors metallic as a BLEND for
# painted and worn metal, deliberately and throughout.
#
# A gate that fails the reviewed corpus is wrong about the corpus, not the
# other way round. Imposing an outside convention on a documented decision
# would have meant nineteen "defects" that are nothing of the kind, and the
# next reader learning to ignore this file.

# Below this, a surface is glass, still water, or polished metal. Nothing else.
ROUGHNESS_MIRROR = 0.15
MIRROR_OK = ("glaz", "glass", "window", "screen", "viewport", "monitor",
             "display", "polish", "water", "mirror")

# Emissive fittings are exempt from the neutral-albedo rule: a lamp is allowed
# to be a colour. The rule is about SURFACES.
QUARANTINE = ("21-QUARANTINE", "22-QUARANTINE")


def _sat(rgb):
    hi, lo = max(rgb), min(rgb)
    return 0.0 if hi <= 0 else (hi - lo) / hi


def _val(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def station_groups(schema, profile):
    """Every group name `rooms.py` emits, across all 68 procedural locations."""
    out = set()
    for place in R.unbuilt(schema, profile):
        _v, _t, g = R.build(schema, profile, place)
        out.update(n for n, _lo, _hi in g)
    return out


# Bespoke modules whose geometry this gate knows how to build. The value is a
# callable taking (schema, profile) and returning group names.
#
# WHY BY RUNNING THEM. `materials.KNOWN_GROUPS` is fed by a regex over the
# generators' source, restricted to the prefixes
# `drum|endcap|truss|tram|core|ground|greeble|light`. Every group in this
# project that does NOT start with one of those is invisible to it -- which is
# all 124 of rooms.py's, and all 42 of command_control's, council_chamber's,
# docking_bay's and signage's. Its gate, "every known generator group resolves
# to a material", therefore passed over a list that did not contain them.
#
# A gate whose input list is short is not a gate. Widening the regex is the
# obvious fix and the wrong one: it is what made the scan match directory.py
# place keys and rooms.py prop names, six false failures in one run. Asking the
# generator what it emits cannot drift, because it IS the emission.
#
# This table grows as entry points are established. A module absent from it is
# reported as UNCHECKED rather than silently passing -- an unknown is not a
# pass, and the count below says how many are still unknown.
def _via_write_obj(mod_name):
    def build(_schema, _profile):
        import importlib, tempfile, os as _os, io as _io, contextlib
        mod = importlib.import_module(mod_name)
        fd, path = tempfile.mkstemp(suffix=".obj")
        _os.close(fd)
        try:
            with contextlib.redirect_stdout(_io.StringIO()):
                mod.write_obj(path)
            with open(path) as f:
                return {ln[2:].strip() for ln in f if ln.startswith("g ")}
        finally:
            _os.unlink(path)
    return build


BESPOKE_BUILDERS = {
    "command_control": _via_write_obj("command_control"),
    "council_chamber": _via_write_obj("council_chamber"),
    "docking_bay": _via_write_obj("docking_bay"),
    "signage": _via_write_obj("signage"),
}

# Every module that owns at least one addressed place, so the gate can say how
# much of layer 3 it is NOT yet able to see.
BESPOKE_ALL = ("zocalo", "customs", "command_control", "council_chamber",
               "garden", "alien_sector", "plant", "hospitality", "quarters",
               "docking_bay", "signage", "interior_kit", "core_tube", "tram",
               "components")


def bespoke_groups(schema, profile):
    """{module: {group names}} for every bespoke module we can build."""
    out = {}
    for name, build in sorted(BESPOKE_BUILDERS.items()):
        try:
            out[name] = build(schema, profile)
        except Exception as exc:                               # noqa: BLE001
            out[name] = {f"__error__ {type(exc).__name__}: {exc}"}
    return out


def unresolved(groups, scene="interior"):
    return sorted(g for g in groups if M.resolve_any(g, scene) is None)


def ambiguous(groups, scene="interior"):
    """Groups that two different materials both claim.

    The first version of this asked whether a fragment "swallows" a group and
    tested `frag in g and len(frag) > len(g)` -- which no pair of strings can
    satisfy, since a substring is never longer than its container. It was a
    check that could not fire, which is the defect this project has shipped
    three times and now probes for explicitly.

    The real, computable defect is AMBIGUITY: two materials' fragments both
    match one group, so which one wins is decided by fragment length rather
    than by anybody's intent. `_wall` and `prop_monitor_wall` are exactly that
    shape -- the monitor happens to win because its name is longer, and would
    silently stop winning if someone renamed it.
    """
    out = []
    for g in sorted(groups):
        owners = {m.name for m in M.MATERIALS
                  if scene in m.scenes
                  for frag in m.binds if frag in g}
        if len(owners) > 1:
            out.append((g, sorted(owners)))
    return out


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    schema, profile = it.load()
    groups = station_groups(schema, profile)
    check("rooms.py still emits groups to cover", len(groups) > 100,
          f"{len(groups)}")

    # --- 1. COVERAGE: the layer's definition of done ----------------------
    miss = unresolved(groups)
    check("every interior group resolves to a material",
          not miss, f"{len(miss)} of {len(groups)} unresolved: {miss[:8]}")
    print(f"  coverage  {len(groups) - len(miss)}/{len(groups)} groups "
          f"({100 * (len(groups) - len(miss)) / max(len(groups), 1):.0f}%)")

    # --- 1b. THE BESPOKE MODULES ------------------------------------------
    # The 50 places with their own generator. Reported separately from the
    # procedural 68 because they are a different tier of the plan and because
    # their coverage is much worse -- collapsing the two into one percentage
    # would hide that behind rooms.py's 100%.
    bg = bespoke_groups(schema, profile)
    errs = {k: sorted(v)[0] for k, v in bg.items()
            if any(x.startswith("__error__") for x in v)}
    check("every bespoke module this gate knows how to build, builds",
          not errs, str(errs))
    b_all = {g for v in bg.values() for g in v if not g.startswith("__error__")}
    b_miss = unresolved(b_all)
    print(f"  bespoke   {len(b_all) - len(b_miss)}/{len(b_all)} groups over "
          f"{len(BESPOKE_BUILDERS)} of {len(BESPOKE_ALL)} modules "
          f"({len(BESPOKE_ALL) - len(BESPOKE_BUILDERS)} still unenumerated)")
    # NOT a hard failure yet: the remaining modules' entry points are still
    # being established, and failing the build for work that is openly
    # in progress teaches the next reader to ignore this file. It becomes a
    # hard check when BESPOKE_BUILDERS covers BESPOKE_ALL.
    if b_miss:
        print(f"            {len(b_miss)} unresolved, e.g. {b_miss[:6]}")
    check("the bespoke enumeration is honest about what it cannot see",
          set(BESPOKE_BUILDERS) <= set(BESPOKE_ALL),
          str(sorted(set(BESPOKE_BUILDERS) - set(BESPOKE_ALL))))

    # --- 2. FRAGMENT SAFETY ----------------------------------------------
    # The failure this catches has already happened once in this project, in
    # the partition of these very groups: "_wall" caught prop_monitor_wall.
    amb = ambiguous(groups)
    check("no group is claimed by two different materials",
          not amb, f"{len(amb)}: {amb[:4]}")
    # And the gate must be able to fire, or it is decoration.
    check("the ambiguity test can fire", _ambiguity_probe())

    # --- 3. THE MEASURED PALETTE -----------------------------------------
    # SATURATION MUST BE MEASURED, NOT INVENTED -- which is CLAUDE.md's first
    # hard rule applied to colour, and it is a better rule than the two drafts
    # before it.
    #
    # Draft one flagged every saturated material and swept in radiators, cargo
    # modules, hazard chevrons and land cover, all of which are meant to be
    # saturated. Draft two exempted them by NAME, which is fragile: it let
    # "hazard_chevron" through and would have flagged "edge_chevron_nosing",
    # the same surface under a different name, and "container_skin", whose
    # value is the cargo-module measurement already in this library.
    #
    # The principled line is provenance. A structural surface may be as
    # saturated as a frame says it is; what it may not be is saturated because
    # somebody liked it. So: over the ceiling is fine IF the source cites a
    # real file -- and the source-existence check below is what makes that
    # citation mean something.
    loud = []
    for m in M.MATERIALS:
        if "interior" not in m.scenes or m.emission is not None:
            continue
        if _sat(m.albedo) <= STRUCTURAL_SAT_MAX:
            continue
        cites = re.search(r"\.(?:webp|jpg|jpeg|png)\b", m.source)
        if not cites:
            loud.append((m.name, round(_sat(m.albedo), 3)))
    check("a saturated structural surface cites the frame it was measured from",
          not loud, f"{len(loud)} saturated with no frame cited: {loud[:6]}")

    # --- 4. PHYSICAL PLAUSIBILITY ----------------------------------------
    out_of_range = [(m.name, m.metallic, m.roughness, m.specular)
                    for m in M.MATERIALS
                    if not (0.0 <= m.metallic <= 1.0
                            and 0.0 <= m.roughness <= 1.0
                            and 0.0 <= m.specular <= 1.0)]
    check("metallic, roughness and specular are all in [0, 1]",
          not out_of_range, str(out_of_range[:4]))
    mirror = [(m.name, m.roughness) for m in M.MATERIALS
              if m.roughness < ROUGHNESS_MIRROR
              and not any(w in m.name for w in MIRROR_OK)]
    check("only glass and polished metal are mirror-smooth",
          not mirror, f"{len(mirror)}: {mirror[:6]}")

    # --- 5. DECK AGAINST WALL, PER ARCHETYPE ------------------------------
    # The measured relationship, and the one that makes a floor read as a
    # floor: darker than the wall, and smoother, because its brightness is
    # specular rather than albedo.
    checked = 0
    for arch, _keys in R.ARCHETYPES:
        d = M.resolve_any(f"{arch}_deck", "interior")
        w = M.resolve_any(f"{arch}_wall", "interior")
        if d is None or w is None or d is w:
            continue
        checked += 1
        check(f"{arch}: the deck is darker than the wall it meets",
              _val(d.albedo) < _val(w.albedo) + 1e-9,
              f"deck {_val(d.albedo):.3f} vs wall {_val(w.albedo):.3f}")
        check(f"{arch}: the deck is smoother than the wall",
              d.roughness <= w.roughness + 1e-9,
              f"deck {d.roughness} vs wall {w.roughness}")
    print(f"  deck/wall pairs distinguished: {checked}")

    # --- 6. SOURCED MEANS SOURCED ----------------------------------------
    # CLAUDE.md's cardinal sin. A source string naming a path must name a path
    # that exists; naming a quarantined frame is worse than naming nothing.
    # CHECKED BY INVERSION, and two earlier attempts say why. Extracting a
    # filename from prose with a regex fails both ways here: allowing spaces
    # makes it eat the preceding words ("...and directory.py" became the
    # filename "and directory.py"), and forbidding them splits the real
    # filenames, which contain spaces -- "exterior more.jpg" became "more.jpg",
    # and 24 correct sources were reported as fabrications.
    #
    # So instead of parsing the source, ask whether any REAL file in the repo
    # is named inside it. That handles spaces without a grammar, and it is the
    # question actually being asked.
    real = _repo_files()
    bad_src, quarantined = [], []
    for m in M.MATERIALS:
        looks_cited = re.search(r"\.(?:webp|jpg|jpeg|png|md|py)\b", m.source)
        if not looks_cited:
            continue
        named = [f for f in real if f in m.source]
        if not named:
            bad_src.append((m.name, m.source[:60]))
        for f in named:
            if any(q in p for q in QUARANTINE for p in real[f]):
                quarantined.append((m.name, f))
    check("a source that cites a file cites one that exists",
          not bad_src, f"{len(bad_src)}: {bad_src[:4]}")
    check("no material sources a quarantined frame",
          not quarantined, str(quarantined[:4]))

    # Non-empty, and not a restatement of the material's own name. A length
    # threshold was the first draft and it failed `core_band`, whose source is
    # "34b" -- terse, and a real authority-1 frame ID. Short is not the same as
    # absent.
    empty = [m.name for m in M.MATERIALS
             if not m.source.strip()
             or m.source.strip().lower() == m.name.lower()]
    check("every material names a source", not empty, str(empty[:6]))

    print(f"\n{ok}/{ok + fail} passed")
    return 1 if fail else 0


_FILES = {}


def _repo_files():
    """{basename: [relative paths]} for every file in the repo.

    Basenames rather than paths, because a source cites a frame by its name --
    "exterior more.jpg" -- not by where the sorter happened to file it.
    """
    if not _FILES:
        for dirpath, dirnames, filenames in os.walk(ROOT):
            dirnames[:] = [d for d in dirnames
                           if d not in (".git", "__pycache__", ".godot",
                                        "node_modules")]
            for fn in filenames:
                _FILES.setdefault(fn, []).append(
                    os.path.relpath(os.path.join(dirpath, fn), ROOT))
    return _FILES


def _ambiguity_probe():
    """The ambiguity test must be able to fire.

    Builds the exact shape it exists to catch -- `_wall` and
    `prop_monitor_wall` both matching one group -- and asserts the detector
    sees it, then asserts it stays quiet on a clean pair. Three assertions in
    this project have been vacuous, one of them named "FNV-1a is stable across
    processes" and comparing a value to itself.
    """
    a = M.Material("probe_a", "a", albedo=(0.5, 0.5, 0.5), roughness=0.5,
                   binds=("_wall",), scenes=("interior",), source="probe")
    b = M.Material("probe_b", "b", albedo=(0.5, 0.5, 0.5), roughness=0.5,
                   binds=("prop_monitor_wall",), scenes=("interior",),
                   source="probe")
    saved = M.MATERIALS
    try:
        M.MATERIALS = (a, b)
        fires = bool(ambiguous({"prop_monitor_wall"}))
        M.MATERIALS = (a,)
        quiet = not ambiguous({"office_wall"})
        return fires and quiet
    finally:
        M.MATERIALS = saved


if __name__ == "__main__":
    sys.exit(_selftest())
