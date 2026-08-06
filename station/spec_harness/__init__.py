"""One harness module per spec row family, dispatched by ID prefix.

WHY A PACKAGE AND NOT MORE FUNCTIONS IN `spec_check.py`. The registry has 300
rows in 13 families and each family asks a different question -- INC rows are
about `incident.py`'s classes, VRB rows about `interact.py`'s verbs, PLC rows
about a place's program. Putting all of them in one file guarantees the one
thing this project cannot afford: several people editing the same file, which
is how `git add -A`, half-written imports and stomped artefacts have all
happened here before.

THE CONTRACT, and it is deliberately small:

    check(row) -> (ok: bool, note: str)      required
    SUFFICIENT: bool                          required

`SUFFICIENT` is the honesty contract made explicit. A harness that verifies a
row's ADDRESS -- that the thing it names exists -- is real, can fail, and is
NOT enough to call the row done; `spec_check.py` reports those as a distinct
kind of RED. Only a harness that checks what the row actually CLAIMS may set
`SUFFICIENT = True`, and setting it is a statement that a GREEN here means the
content is there.

THE RULE EVERY MODULE HERE OBEYS. A harness must be able to FAIL on the current
content, and its author must have watched it do so. A check that passes because
it compares nothing is worse than no check: `check_place_register_agreement`
spent its whole life returning True because its only failure mode was an index
past the end of a list, and it lived inside the file whose header calls this
project "a museum of gates that were prose".
"""
import importlib
import os

FAMILIES = ("PLC", "INC", "SHB", "FAC", "SYS", "SHC", "VRB", "ROLE",
            "SUR", "PLY", "CAST", "DLG", "GDS")

_CACHE = {}


def module_for(prefix):
    """The harness module for a family, or None if nobody has written one yet.

    Absence is a normal state and is reported as such -- `spec_check.py` says
    "harness not implemented" and the row stays RED. What must never happen is
    an import error being swallowed into that same message, because then a
    broken harness and an unwritten one look identical. So only
    ModuleNotFoundError for THIS module is treated as absence; anything else
    propagates.
    """
    if prefix in _CACHE:
        return _CACHE[prefix]
    name = "%s.%s" % (__name__, prefix.lower())
    try:
        m = importlib.import_module(name)
    except ModuleNotFoundError as e:                             # noqa: PERF203
        if getattr(e, "name", "") != name:
            raise
        m = None
    _CACHE[prefix] = m
    return m


def spec_text(at, lines=40):
    """The rows's own text out of the annex it lives in.

    Every harness needs this and none of them should re-implement it: the `at`
    field is `path:line` and a row's claim runs from that heading to the next
    one. Read from the document rather than restated in code, so a harness
    cannot drift from the row it checks -- the same discipline
    `directory.gravity_of` follows for a deck's gravity.
    """
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    if ":" not in at:
        return ""
    path, ln = at.rsplit(":", 1)
    try:
        body = open(os.path.join(root, path), encoding="utf-8").read()
    except OSError:
        return ""
    src = body.splitlines()
    i = max(0, int(ln) - 1)
    out = []
    for j in range(i, min(len(src), i + lines)):
        if j > i and src[j].startswith("#"):
            break
        out.append(src[j])
    return "\n".join(out)
