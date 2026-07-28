"""Station signage: the boards, and what is written on them.

The project had **no signage of any kind**. `reference/16-signage-typography-ui/`
holds three files and all three are logos. Signage is everywhere in a real
interior, it is most of how a place tells you what it is, and the owner asked
specifically for an information layer the player can use.

This module is deliberately two things at once, and the split matters:

  - **Geometry** for a backlit board -- panel, frame, mounting post. Small,
    instanced, reused everywhere.
  - **The TEXT, verbatim**, as canon data. What a sign says is a *fact about the
    station*, not a decoration, and it belongs under version control next to
    every other sourced fact rather than baked into a texture nobody can grep.

A texture generator will later render `BOARDS[...]["lines"]` onto the panel. It
does not exist yet and that is fine: the words are the part that can be lost.

THE SOURCE

`reference/01-station-exterior/welcome to babylon 5.webp` -- authority 1, and the
only frame in the whole reference set that shows readable station signage. Two
backlit blue boards on dark structural posts, white text, in the customs hall.
Both are transcribed below **exactly as they appear**, including the prop's own
spelling. `ARANGEMENT` has one R and `ATMOCHEMICAL` is not a word; both are on
the screen-used board and both are reproduced. A future session that "corrects"
them would be correcting the show.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import interior as it                                        # noqa: E402

# ---------------------------------------------------------------------------
# What the signs say
# ---------------------------------------------------------------------------
# `sic` marks a spelling that is wrong in English and right on the prop.
BOARDS = {
    "customs_atmosphere": {
        "where": "Customs hall, Blue Sector, adjacent to the main docking bays",
        "auth": 1,
        "src": "reference/01-station-exterior/welcome to babylon 5.webp",
        "header": "Welcome to Babylon 5",
        "badge": "CUSTOMS SECTOR",
        "title": "ATMOSPHERE CAUTION",
        "lines": [
            "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE ON B-5.",
            "OTHERS MAY BE CREATED BY PRIOR ARANGEMENT.",          # sic
            "UNCOMMON ATMOSPHERIC MAKEUPS MAY BE SYNTHESIZED",
            "FOR ENCOUNTER SUITS.",
            "FOR SPECIFIC ATMOCHEMICAL BREAKDOWNS SEE MONITOR BELOW.",  # sic
        ],
        "sic": ["ARANGEMENT", "ATMOCHEMICAL"],
        "truncated": "The board continues 'REMEMBER...' below the frame line.",
    },
    "customs_procedures": {
        "where": "Customs hall, Blue Sector, beside the atmosphere board",
        "auth": 1,
        "src": "reference/01-station-exterior/welcome to babylon 5.webp",
        "header": "Welcome to Babylon 5",
        "badge": "CUSTOMS SECTOR",
        "title": "FOLLOW ALL CUSTOMS PROCEDURES.",
        "lines": [
            "SEE MONITORS FOR DETAILS",
            "TIME ON B-5 IS EARTH MEAN TIME (EMT)",
            "MONETARY EXCHANGE RATES THROUGH BUSINESS CENTER",
        ],
        "sic": [],
        "truncated": "Partly occluded by the first board; read from the "
                     "right-hand panel in the same frame.",
    },
}

# Three facts these boards establish that are not signage at all, and that
# nothing else in the project holds:
#
#   1. SIX atmospheres are available simultaneously, and others can be made to
#      order. That is a life-support requirement with a number in it, and it is
#      the mechanic behind the alien sector and Kosh's encounter suit.
#   2. The station runs on EARTH MEAN TIME. Every NPC schedule in
#      station/npc/schedule.py is implicitly on some clock; this names it.
#   3. There is a BUSINESS CENTER, and it handles currency exchange. A location,
#      sourced, that the gazetteer can place.
ESTABLISHED = {
    "atmospheres_available": 6,
    "atmospheres_to_order": True,
    "station_time": "Earth Mean Time (EMT)",
    "currency_exchange_at": "Business Center",
}

# ---------------------------------------------------------------------------
# The board itself
# ---------------------------------------------------------------------------
# Proportioned off the frame: the panel is markedly TALLER than wide, roughly
# 3:4, with a wide flat frame and the lit face set back inside it. Absolute size
# is INV-023 -- there is nothing of known size in the frame, which is cropped to
# the boards themselves.
BOARD_W_M = 1.10
BOARD_H_M = 1.48
BOARD_FRAME_M = 0.075
BOARD_INSET_M = 0.035      # how far the lit face sits behind the frame
BOARD_T_M = 0.11
POST_W_M = 0.34            # the dark structural post the boards hang on
# The post must not touch the board's back plane. It sat at exactly z = 0, which
# is where the lit face's own back face is, so the two were coplanar and
# z-fought -- visible in the first render as a wedge of post punched through the
# lit panel. Same defect family as the Zocalo's doubled bay seams.
POST_GAP_M = 0.012
MOUNT_H_M = 1.35           # underside of the board above the deck


class _M:
    def __init__(self):
        self.v, self.t, self.g = [], [], []

    def box(self, x0, x1, y0, y1, z0, z1, group):
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        i = len(self.v)
        self.v.extend(c)
        for a, b, d, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                           (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            self.t.append((i + a, i + d, i + b))
            self.t.append((i + a, i + e, i + d))
        self.g.extend([group] * 12)

    def as_tuple(self):
        return self.v, self.t, self.g


def board(with_post=True):
    """One backlit board. +X across, +Y up, +Z out of the face; deck at y = 0.

    The lit face is a SEPARATE box set back inside the frame rather than a
    coplanar decal on it. That is what makes a backlit sign read as backlit at a
    glancing angle: the frame casts a shadow onto the face, and a decal cannot.
    """
    m = _M()
    hw, y0, y1 = BOARD_W_M / 2.0, MOUNT_H_M, MOUNT_H_M + BOARD_H_M
    f = BOARD_FRAME_M

    if with_post:
        m.box(-POST_W_M / 2, POST_W_M / 2, 0.0, y1 + 0.22,
              -BOARD_T_M, -POST_GAP_M, "sign_post")

    # Frame, as four rails rather than one slab, so the face can sit inside it.
    m.box(-hw, hw, y1 - f, y1, 0.0, BOARD_T_M, "sign_frame")
    m.box(-hw, hw, y0, y0 + f, 0.0, BOARD_T_M, "sign_frame")
    m.box(-hw, -hw + f, y0, y1, 0.0, BOARD_T_M, "sign_frame")
    m.box(hw - f, hw, y0, y1, 0.0, BOARD_T_M, "sign_frame")

    # The lit face, recessed.
    m.box(-hw + f, hw - f, y0 + f, y1 - f,
          0.0, BOARD_T_M - BOARD_INSET_M, "sign_face")
    return m.as_tuple()


def board_pair(gap_m=0.55):
    """The two customs boards as the frame shows them: side by side on posts."""
    m = _M()
    for i, dx in enumerate((-(BOARD_W_M + gap_m) / 2.0,
                            (BOARD_W_M + gap_m) / 2.0)):
        v, t, g = board()
        base = len(m.v)
        m.v.extend([(x + dx, y, z) for x, y, z in v])
        m.t.extend([(a + base, b + base, c + base) for a, b, c in t])
        m.g.extend(g)
    return m.as_tuple()


def legible_at_m(cap_height_m=None):
    """How far away this board's body text can still be read.

    The rule of thumb sign designers use is that a capital stays legible to
    about 250x its height for a reader who is looking for it, and half that for
    one who is not. The body text on this board is about 26 lines' worth of the
    lit face, so a capital is roughly face_height / 26.

    It is worth computing rather than assuming, because it decides how many
    boards a concourse needs: at 1.48 m the answer is that one board serves a
    radius of about 12 m, not the whole hall.
    """
    if cap_height_m is None:
        cap_height_m = (BOARD_H_M - 2 * BOARD_FRAME_M) / 26.0
    return cap_height_m * 250.0, cap_height_m * 125.0


def write_obj(path):
    v, t, g = board_pair()
    it.write_grouped_obj(path, v, t, g)
    return path, len(v), len(t)


# ---------------------------------------------------------------------------
def _selftest():
    ok = fail = 0

    def check(name, cond, detail=""):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"FAIL  {name}" + (f"  -- {detail}" if detail else ""))

    # --- the words ---------------------------------------------------------
    # These are the only authority-1 signage transcriptions the project holds.
    # Asserting them looks odd until you notice that a well-meaning edit is
    # exactly how a transcription rots: the two sic spellings are the things
    # most likely to be "fixed" by someone who has not seen the frame.
    a = BOARDS["customs_atmosphere"]
    check("the atmosphere board keeps the prop's own spelling",
          any("ARANGEMENT" in ln for ln in a["lines"])
          and any("ATMOCHEMICAL" in ln for ln in a["lines"]),
          "ARANGEMENT and ATMOCHEMICAL are on the screen-used board")
    check("both sic spellings are declared",
          set(a["sic"]) == {"ARANGEMENT", "ATMOCHEMICAL"})
    check("every board cites an authority-1 frame",
          all(b["auth"] == 1 and b["src"].startswith("reference/")
              for b in BOARDS.values()))
    check("the six-atmosphere figure agrees with the board text",
          str(ESTABLISHED["atmospheres_available"]) == "6"
          and "SIX DIFFERENT ATMOSPHERES" in a["lines"][0])
    check("station time is named", "Earth Mean Time" in
          ESTABLISHED["station_time"])

    # --- the board ---------------------------------------------------------
    v, t, g = board()
    check("the board is taller than it is wide, as the frame shows",
          BOARD_H_M > BOARD_W_M, f"{BOARD_H_M} x {BOARD_W_M}")
    check("the lit face is recessed behind its frame, not coplanar",
          0.0 < BOARD_INSET_M < BOARD_T_M,
          f"inset {BOARD_INSET_M} into a {BOARD_T_M} board")

    face = [v[i] for k, tri in enumerate(t) if g[k] == "sign_face" for i in tri]
    frame = [v[i] for k, tri in enumerate(t) if g[k] == "sign_frame" for i in tri]
    check("the lit face sits inside the frame on every side",
          min(q[0] for q in face) > min(q[0] for q in frame) and
          max(q[0] for q in face) < max(q[0] for q in frame) and
          min(q[1] for q in face) > min(q[1] for q in frame) and
          max(q[1] for q in face) < max(q[1] for q in frame))
    check("the face does not protrude through the frame",
          max(q[2] for q in face) < max(q[2] for q in frame) + 1e-9)

    # A sign nobody can reach or read is set dressing. Both bounds matter.
    check("the board is readable from standing eye height",
          MOUNT_H_M < 1.7 < MOUNT_H_M + BOARD_H_M,
          f"board spans {MOUNT_H_M}..{MOUNT_H_M + BOARD_H_M} m")
    check("the board clears a walking crowd",
          MOUNT_H_M > 1.2, f"{MOUNT_H_M} m to the underside")

    post = [v[i] for k, tri in enumerate(t) if g[k] == "sign_post" for i in tri]
    check("the post does not share a plane with the board",
          max(q[2] for q in post) < 0.0 - 1e-9,
          f"post front at z={max(q[2] for q in post):.4f}, board back at 0.0")

    far, glance = legible_at_m()
    check("legibility range is computed, not assumed",
          5.0 < glance < 40.0 and far > glance,
          f"{glance:.1f} m at a glance, {far:.1f} m if looked for")

    # --- the pair ----------------------------------------------------------
    pv, pt, pg = board_pair()
    check("the pair is two boards", len(pt) == len(t) * 2)
    xs = [q[0] for q in pv]
    check("the two boards do not overlap",
          max(xs) - min(xs) > BOARD_W_M * 2,
          f"{max(xs) - min(xs):.2f} m across a pair of {BOARD_W_M} m boards")

    print(f"{ok}/{ok + fail} passed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(_selftest())
