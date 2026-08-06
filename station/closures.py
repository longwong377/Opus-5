#!/usr/bin/env python3
"""What is stencilled on the plates that close the station's unbuilt volume.

WHY THIS IS A MODULE AND NOT A TABLE IN `signage.py`. `signage.BOARDS` holds the
station's LIT DIRECTORY BOARDS -- the customs atmosphere notice, the welcome
board -- authority-1 objects read off show frames, with a header, a badge and a
frame rail. A closure stencil is a different object: paint on a welded plate at
the edge of a volume nobody may enter, no frame, no light of its own, and its
content is a REFUSAL rather than a direction. Putting the two in one table would
have made `signage.BOARDS` mean "any text on a wall", which is how a vocabulary
stops being one.

WHERE THESE COME FROM. `docs/spec/PLACES.md` §SHC enumerates thirteen closures
-- the volume the station HAS and does not build -- and quotes the stencil on
each in the annex text itself. `station/spec_harness/shc.py` checks that every
quoted stencil exists as a string literal in the repository, and on its first run
found **none of them**. These are them, transcribed verbatim, em dashes and all.

**ELEVEN, NOT THIRTEEN, AND NOT TWELVE EITHER** -- and getting that count right
took the file's own self-test. Thirteen SHC rows; SHC-13 carries no stencil
deliberately (below); and SHC-02 quotes none because its row says *"12 stencils
cross-reffed to PLC-092"*, i.e. its texts are the `welded_shut` door's own twelve
and belong to that place rather than to this table. Inventing twelve strings here
would have been authoring content the spec assigns elsewhere -- which is the
quiet way a table stops being a transcription and starts being an opinion.

THE THIRTEENTH IS DELIBERATELY BLANK AND THAT IS THE POINT OF IT. SHC-13 is
Grey 17 -- the hidden inhabited level -- and its own row says the opening is
*"an unremarkable capped opening identical to SHC-11's, deliberately
UNSTENCILLED"*. A table that filled all thirteen in would have been a table
somebody completed rather than transcribed, so `None` is stored with the reason
beside it and `_selftest` asserts it stays `None`. That assertion is the control
on this whole file: it fails the day somebody "finishes" the set.

WHAT THIS DOES *NOT* DO, SAID PLAINLY BECAUSE THE OPPOSITE IS THIS PROJECT'S
SIGNATURE DEFECT. The texts exist here and `plate()` builds the geometry for one,
using `signage.text_quads` -- the same machinery the docking bay's numerals go
through, not a second text renderer. **Nothing yet paints them onto the actual
closure surfaces across the station.** So `shc.py`'s "is this a string literal in
station/" check will now pass for all twelve, and that check is therefore weaker
than it looks: a literal in a table is not a stencil a player can read. That is a
finding about the harness and it is recorded here rather than left for somebody
to discover after the ledger goes quiet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import signage                                                   # noqa: E402


# THE STENCIL, THE PLACE IT SEALS, AND WHAT KIND OF CLOSURE CARRIES IT.
#
# `at` is the register key the closure adjoins where the annex names one, so a
# builder can find its surface without a second lookup table. `kind` is the
# closure vocabulary the annex uses -- these are not interchangeable: a manway
# cover is dogged and openable by authority, a weld bead is not openable at all,
# and a player who learns that difference has learned something true about the
# station.
CLOSURES = {
    "SHC-01": {
        "at": "markab_quarter",
        "kind": "welded_plate",
        "extra": "wreath bracket",
        # ONE LINE, DELIBERATELY, AND OVER THE LINE LENGTH THIS FILE OTHERWISE
        # KEEPS. Wrapping this with implicit concatenation is legitimate
        # Python and it BROKE THE CHECK: `spec_harness/shc.py` greps the
        # repository for the stencil as a literal, and three of eleven were
        # split across source lines and stayed red while the other eight went
        # green. The string IS the content here -- a stencil is one piece of
        # paint -- so it is stored as one, and the harness's own weakness
        # (source-text grep, not an import) is recorded in the module
        # docstring rather than worked around silently.
        "text": "SECTION CLOSED BY ORDER — MEDICAL AUTHORITY B5 — 2259. NO ENTRY. LET THEM REST.",  # noqa: E501
        "why": "the only monument to an extinct species; the datum is a "
               "consequence of the Markab plague, not decoration",
    },
    "SHC-02": {
        "at": "welded_shut",
        "kind": "weld_bead_cap",
        "extra": "12 cap plates",
        # NO QUOTED TEXT IN THE ANNEX, and it is not an omission: the row says
        # "12 stencils cross-reffed to PLC-092", i.e. the twelve are the
        # welded_shut door's own texts and PLC-092 declares `welded_door x12 --
        # 12 distinct texts`. They belong to that place, not to this table, and
        # inventing twelve here would be authoring content the spec assigns
        # elsewhere.
        "text": None,
        "why": "cross-referenced to PLC-092's own twelve door texts; not this "
               "table's to author",
    },
    "SHC-03": {
        "at": "water_reclamation",
        "kind": "manway_dogged",
        "text": "POTABLE RESERVE — 30 DAY — ENTRY BY WATER AUTHORITY PERMIT W-7 ONLY",  # noqa: E501
        "why": "the reserve IS the volume; 397,500 m3 of it",
    },
    "SHC-04": {
        "at": "hazard_tanks",
        "kind": "blast_manway",
        "text": "ISOTOPE SLUSH — CRYOGENIC — SUIT AND ESCORT MANDATORY",
        "why": "Yellow tankage interiors: slush, inert gas x4, hazard, fuel "
               "bund inner cells",
    },
    "SHC-05": {
        "at": "plant_zone",
        "kind": "frame_and_sheet",
        "text": "GREY VOID G-nn — NO AIR ASSURANCE BEYOND THIS FRAME",
        "why": "~139 M m3 less the catwalk web -- the bulk void between the "
               "walkable skeleton",
    },
    "SHC-06": {
        "at": "fusion_core",
        "kind": "shield_door",
        "text": "RADIATION AREA — REACTOR CONTAINMENT — DOSIMETRY + ESCORT",
        "why": "most of the 800 m drum; the reactor is mostly not a room",
    },
    "SHC-07": {
        "at": "aft_hull_block",
        "kind": "ring_bulkhead",
        "text": "STRUCTURAL VOLUME — AFT BLOCK — NO DECKING BEYOND FRAME 3107–4207",  # noqa: E501
        "why": "0.2785 km3 of undecked flanks",
    },
    "SHC-08": {
        "at": "bearing_neck",
        "kind": "ring_bulkhead",
        "text": "MAIN BEARING — ROTATING/STATIC INTERFACE — AUTHORISED RIGGERS ONLY",  # noqa: E501
        "why": "where Green's stack ends at 310.7 m",
    },
    "SHC-09": {
        "at": "eva_lock_blue",
        "kind": "crawlway_hatch",
        "extra": "every 40 m",
        "text": "HULL INTERSPACE — VACUUM RATED — LOG OUT / LOG IN",
        "why": "enterable ONLY at declared EVA/maintenance points",
    },
    "SHC-10": {
        "at": "nav_beacon",
        "kind": "pressure_cap",
        "text": "UNPRESSURISED BEYOND THIS POINT — DEFLECTOR MAST",
        "why": "the forward spike above z 8,010 is instrument mast, never "
               "habitable",
    },
    "SHC-11": {
        "at": "downbelow",
        "kind": "capped_opening",
        "text": "UNCOMMISSIONED — B5 CONSTRUCTION CONTRACT 5 — NO SERVICES",
        "why": "600 of Downbelow's 745 outer-ring cells are empty; the "
               "closure vocabulary itself is authority 1",
    },
    "SHC-12": {
        "at": "red_section",
        "kind": "deck_edge_bulkhead",
        "text": "RED RESERVE TANKAGE R-nn",
        "why": "what Red's housing does not fill is tankage",
    },
    "SHC-13": {
        "at": "grey_seventeen",
        "kind": "capped_opening",
        # DELIBERATELY UNSTENCILLED. Grey 17 is the hidden inhabited level and
        # the annex is explicit: "an unremarkable capped opening identical to
        # SHC-11's, deliberately UNSTENCILLED". A stencil would announce it.
        # `_selftest` asserts this stays None -- it is the control on the whole
        # table, and it fails the day somebody tidies the set by filling it in.
        "text": None,
        "why": "the hidden level announces nothing; a stencil here would be "
               "the one that gives it away",
    },
}

# How big the paint is. Derived rather than chosen: `signage.legible_at_m()`
# answers what cap height a given reading distance needs, and a closure plate is
# read from the corridor it seals -- one corridor width away, not across a hall.
STENCIL_CAP_M = 0.075
PLATE_MARGIN_M = 0.11


def stencils():
    """(id, text) for every closure that carries one. Eleven of thirteen."""
    return [(k, v["text"]) for k, v in sorted(CLOSURES.items()) if v["text"]]


def unstencilled():
    """The closures that deliberately carry no text, with the reason."""
    return [(k, v["why"]) for k, v in sorted(CLOSURES.items())
            if not v["text"]]


def plate(shc_id, width_m=2.20, cap_m=STENCIL_CAP_M):
    """The stencil's lit quads for one closure, in the plate's own frame.

    Uses `signage.text_quads`, which is the same call the docking bay's numerals
    go through. A second text renderer here would be a second opinion about what
    a letter looks like, and this project has paid for that class of duplication
    more than once.

    Returns a dict with the fitted cap, the broken lines, the lit rectangles
    and the plate's own size -- or None for a closure with no stencil. The
    absence is a real answer, not an error, and SHC-13 depends on it.
    """
    row = CLOSURES[shc_id]
    if not row["text"]:
        return None
    inner = width_m - 2 * PLATE_MARGIN_M
    lines = _wrap(row["text"], inner, cap_m)
    # THE CAP IS FITTED, NOT ASSERTED. `signage.fit_cap_m` returns the largest
    # cap at which every line fits, which is why the two longest stencils
    # (SHC-03 at 2.67 m and SHC-05 at 2.26 m of paint at the nominal 0.075 m)
    # are not a content problem: they are read smaller. My first selftest
    # measured them at the NOMINAL cap and reported both as overflowing a plate
    # they never overflow -- an assertion about a number the builder does not
    # use. It now measures what `plate()` actually lays out.
    fit = signage.fit_cap_m(lines, inner, cap_max=cap_m)
    rects, pitch = [], signage.LINE_PITCH * fit
    for i, ln in enumerate(lines):
        rects += signage.text_quads(ln, fit, x0=PLATE_MARGIN_M,
                                    baseline=-(i + 1) * pitch)
    return {"id": shc_id, "cap_m": fit, "lines": lines, "rects": rects,
            "width_m": width_m,
            "height_m": len(lines) * pitch + 2 * PLATE_MARGIN_M}


def _wrap(text, width_m, cap_m):
    """Break a stencil onto lines that fit the plate, at its own em dashes.

    THE EM DASH IS THE AUTHOR'S OWN BREAK. Every one of these strings is built
    as clauses separated by ` — `, which is how the annex wrote them and how a
    real stencil is laid out: SECTION CLOSED BY ORDER / MEDICAL AUTHORITY B5 /
    2259. Breaking on spaces instead would produce a paragraph, which is not
    what paint on a plate looks like.
    """
    parts = [p.strip() for p in text.split("—")]
    out, cur = [], ""
    for p in parts:
        trial = (cur + " " + p).strip() if cur else p
        if cur and signage.text_width_m(trial, cap_m) > width_m:
            out.append(cur)
            cur = p
        else:
            cur = trial
    if cur:
        out.append(cur)
    return out


def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("FAIL  %s%s" % (name, "  -- " + detail if detail else ""))

    import re                                                    # noqa: PLC0415
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    annex = open(os.path.join(root, "docs/spec/PLACES.md"),
                 encoding="utf-8").read()

    check("thirteen closures, one per SHC row", len(CLOSURES) == 13,
          str(len(CLOSURES)))
    # ELEVEN CARRY PAINT. Pinned as a number because the docstring said
    # "twelve" twice before this test was run, and a count in prose that
    # nothing asserts is a count that drifts.
    check("eleven of them carry a stencil", len(stencils()) == 11,
          str(len(stencils())))

    # EVERY TEXT IS THE ANNEX'S OWN, CHARACTER FOR CHARACTER. Not "close
    # enough": these are stencils quoted in a normative document, and a
    # transcription that drifts is a second version of the text -- which is the
    # exact defect `signage.BOARDS` records with its `sic` field for
    # "ARANGEMENT". Comparing against the document rather than against a copy is
    # what stops this table becoming the authority by accident.
    for sid, text in stencils():
        check("%s is quoted verbatim in PLACES.md" % sid, '"%s"' % text in annex,
              text[:56])

    # THE CONTROL, AND IT IS THE POINT OF THE FILE. SHC-13's opening is
    # deliberately unstencilled -- a stencil there would give away the hidden
    # level. If somebody "completes" the table this fails.
    check("SHC-13 carries NO stencil, deliberately",
          CLOSURES["SHC-13"]["text"] is None)
    check("SHC-02 defers its twelve texts to PLC-092",
          CLOSURES["SHC-02"]["text"] is None)
    check("exactly two closures are unstencilled", len(unstencilled()) == 2,
          str([k for k, _ in unstencilled()]))

    # A stencil has to fit its plate and be readable from the corridor it seals.
    # BREAKS ON ITS OWN EM DASHES -- ASKED ONLY OF THE STENCILS THAT HAVE ONE.
    # My first version asserted every stencil breaks onto two or more lines and
    # SHC-12 failed it: "RED RESERVE TANKAGE R-nn" carries no em dash and is
    # legitimately one line of paint. Asserting a shape the content does not
    # have is how a gate gets loosened until it means nothing; the honest form
    # is to ask the question only where it applies, and to ASSERT THE ONE-LINE
    # CASE TOO so the distinction stays real.
    for sid, text in stencils():
        lines = _wrap(text, 2.20 - 2 * PLATE_MARGIN_M, STENCIL_CAP_M)
        if "—" in text:
            check("%s breaks at its own em dashes" % sid, len(lines) >= 2,
                  "%d line(s): %r" % (len(lines), lines[:2]))
        else:
            check("%s is one line and has no em dash to break at" % sid,
                  len(lines) == 1, "%d line(s)" % len(lines))
        # Measured at the FITTED cap, which is what the builder lays out.
        b = plate(sid)
        widest = max(signage.text_width_m(x, b["cap_m"]) for x in b["lines"])
        check("%s fits a 2.20 m plate as laid out" % sid, widest <= 2.20,
              "%.2f m at cap %.3f" % (widest, b["cap_m"]))
        check("%s stays legible: cap >= 8 mm" % sid, b["cap_m"] >= 0.008,
              "%.4f m" % b["cap_m"])

    # The geometry actually builds, and the two blanks actually return None.
    for sid in CLOSURES:
        got = plate(sid)
        if CLOSURES[sid]["text"]:
            check("%s builds quads" % sid,
                  got is not None and len(got["rects"]) > 0,
                  "rects=%s" % (len(got["rects"]) if got else None))
        else:
            check("%s builds nothing" % sid, got is None)

    print("\n%d/%d passed" % (ok, ok + fail))
    print("%d stencils, %d deliberately blank (%s)"
          % (len(stencils()), len(unstencilled()),
             ", ".join(k for k, _ in unstencilled())))
    print("NOT WIRED: nothing paints these onto the station's closure surfaces "
          "yet, so `spec_harness/shc.py`'s string-literal check now passes on a "
          "table rather than on a stencil a player can read. That is a "
          "weakness in the harness and it is stated here rather than left to "
          "be discovered after the ledger goes quiet.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
