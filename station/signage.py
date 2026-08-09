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


# ---------------------------------------------------------------------------
# The lettering
# ---------------------------------------------------------------------------
# This module said, correctly, that "a texture generator will later render
# BOARDS[...]['lines'] onto the panel. It does not exist yet and that is fine:
# the words are the part that can be lost." The words survived. This is the
# part that renders them, and it is NOT a texture generator, for a reason that
# is a property of the whole project rather than a preference:
#
# **NOTHING IN THIS PROJECT HAS UVs.** `deck.write_obj`,
# `interior.write_grouped_obj` and every other writer emit `v` and `f` and no
# `vt` at all. A texture can therefore only be applied triplanar or in object
# space, and neither can put DIFFERENT text on 87 different door plaques; an
# atlas needs UVs. Threading UVs through every generator to hang three words on
# a wall is the larger change and not obviously the right one. So lettering is
# emissive quads, with each glyph row RUN-LENGTH MERGED -- `E` is 21 lit cells
# and 7 quads -- which is what makes it affordable.
#
# WHAT THE REFERENCE SHOWS, measured off
# `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
# hub.jpg` (authority 1) rather than remembered. Linear, sRGB-decoded, regions
# in normalised coordinates so every figure can be re-measured:
#
#     black field   .320,.250-.590,.265   (0.0033,0.0032,0.0052)   L 0.0034
#     gold header   .345,.275-.575,.300   top5% (0.594,0.580,0.388)  L 0.445 p95
#     blue bar      .470,.335-.487,.352   (0.1068,0.1049,0.6378)   L 0.1438
#     notice gold   .345,.455-.580,.500   top5% (0.561,0.541,0.330)  L 0.448 p95
#     architecture  three independent patches        L 0.031 / 0.0086 / 0.0222
#
# **A LIT SIGN IS BOTH THE BRIGHTEST AND THE DARKEST THING IN THE FRAME.** Its
# text peaks at about 21x the luminance of the structure around it (0.445
# against a 0.021 mean of three patches) while its own field sits at 0.0034,
# **6x DARKER than the wall**. Contrast inside one sign is roughly 130:1.
#
# That is why the field is black here and why it is worth saying twice: an
# engine frame of our walkable deck measured against the show's corridor anchor
# reads p5 x11.09 against a x1.29 band with **zero crushed pixels** where the
# reference has 0.52%. Signage is not a fix for that on its own. It is the one
# piece of content on the station that is black by construction.

## THE NEGATIVE CONTROL FOR THE WHOLE TYPOGRAPHY LAYER, and it is one
## environment variable because a control that needs a patch is a control that
## stops being run (this file's own `--gate-frames --rerender` lesson, and
## `export_scene`'s note that moving a vista JSON aside "works and is clumsy").
## `SIGNAGE_LETTERING=0` builds every board, plaque, level plate and hazard
## strip with its plate, its frame and its recess intact and NOT ONE GLYPH on
## any of them -- which is exactly the station a visual reviewer described this
## session. Render the same camera both ways and the difference is the
## lettering and nothing else.
LETTERING = os.environ.get("SIGNAGE_LETTERING", "1") != "0"

GLYPH_W, GLYPH_H = 5, 7

# THE FACE IS A DECLARED EXTRAPOLATION -- INV-086 -- and the reason is worth
# stating so nobody later mistakes it for a trace. The show's DISPLAY face is
# unmistakably a serif: "WELCOME TO" and "BABYLON 5" carry bracketed serifs in
# the reference frame, and a 5x7 lattice cannot express a serif at any size.
# What a 5x7 lattice CAN express is the coarse bitmap face the SAME panel uses
# for its notice block ("REMEMBER / Smoking permitted in designated areas
# only"), and that is what this reproduces. Substituting the notice face for the
# display face is the invention; the alternative was no lettering at all.
_FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    # Found by the gate, not by guessing at an alphabet: `directory.py` holds
    # "Command & Control", the "5" floor conference room and "Core + 12", and
    # a face that cannot spell the register renders them as tofu.
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    # THE ONLY THREE GLYPHS IN THIS FACE THAT ARE NOT LETTERFORMS -- INV-468.
    # A 5x7 lattice has no arrow and a station of 250,000 people cannot be
    # signed without one, so three were drawn in the same idiom as the rest:
    # one cell of stroke, a head two rows deep, nothing that needs a diagonal
    # the lattice cannot hold. `wayfinding_lines` picks between them from the
    # register's own bearings.
    ">": ("00000", "00100", "00010", "11111", "00010", "00100", "00000"),
    "<": ("00000", "00100", "01000", "11111", "01000", "00100", "00000"),
    "^": ("00100", "01110", "10101", "00100", "00100", "00100", "00100"),
}

## An unknown character draws this rather than nothing. A missing glyph that
## renders as a gap is a sign that silently says something else.
_TOFU = ("11111", "10001", "10001", "10001", "10001", "10001", "11111")

## MEASURED, not chosen. On the reference's 203 px panel the notice caps are
## 9 px at a 17.5 px line pitch, so pitch is 1.94x cap height; the header caps
## are 13 px, 1.44x the notice caps.
LINE_PITCH = 1.94
HEADER_SCALE = 1.44
## Cell gap between glyphs, as a fraction of the 5-wide cell. The reference's
## notice face is tightly set and one cell column is the natural unit.
TRACKING = 0.25

## Palette, measured. The two gold readings agree to 1% in G and 6% in B once
## normalised to R = 1 -- (1.000,0.976,0.653) and (1.000,0.964,0.588) -- so the
## mean is used. Blue is normalised to B = 1.
GOLD = (1.000, 0.970, 0.620)
BLUE = (0.167, 0.164, 1.000)
FIELD_BLACK = (0.0033, 0.0032, 0.0052)


def _spans(ch):
    """(row0, col0, row1, col1) rectangles covering the lit cells of a glyph.

    MERGED IN BOTH DIRECTIONS, and the second direction is worth as much as the
    first. Merging rows alone takes `E` from 21 lit cells to 7 quads; also
    merging vertically where two rows carry the identical span takes `I` from 7
    to 3 and `L` from 7 to 2, because a stem is one tall rectangle and not six
    stacked squares. Over the whole face it is about a third of the geometry,
    and lettering is the only thing on this station that is charged per letter.

    Greedy and therefore not minimal -- finding the fewest rectangles covering
    a bitmap is a harder problem than this is worth -- but it is deterministic,
    which matters more here than optimal.
    """
    rows = [list(r) for r in _FONT.get(ch.upper(), _TOFU)]
    out = []
    for r in range(GLYPH_H):
        c = 0
        while c < GLYPH_W:
            if rows[r][c] != "1":
                c += 1
                continue
            c1 = c
            while c1 < GLYPH_W and rows[r][c1] == "1":
                c1 += 1
            # Extend downward while the row below carries the SAME span, and
            # claim those cells so a later row does not emit them again.
            r1 = r + 1
            while (r1 < GLYPH_H
                   and all(rows[r1][k] == "1" for k in range(c, c1))
                   and (c == 0 or rows[r1][c - 1] != "1")
                   and (c1 == GLYPH_W or rows[r1][c1] != "1")):
                r1 += 1
            for rr in range(r, r1):
                for k in range(c, c1):
                    rows[rr][k] = "0"
            out.append((r, c, r1, c1))
            c = c1
    return out


def advance_m(cap_m):
    """Pen advance for one character at that cap height."""
    return (GLYPH_W + TRACKING * GLYPH_W) * (cap_m / GLYPH_H)


def text_width_m(s, cap_m):
    """How wide `s` renders, in metres. The trailing tracking is not width."""
    if not s:
        return 0.0
    cell = cap_m / GLYPH_H
    return len(s) * advance_m(cap_m) - TRACKING * GLYPH_W * cell


def fit_cap_m(lines, width_m, cap_max=0.060, cap_min=0.008):
    """The largest cap height at which every line fits `width_m`.

    Auto-fitting rather than picking a size is what stops a board silently
    overflowing its own frame when a place is renamed -- and a name is exactly
    the kind of thing that gets renamed.
    """
    longest = max((len(s) for s in lines), default=0)
    if longest == 0:
        return cap_max
    cell = width_m / (longest * (GLYPH_W + TRACKING * GLYPH_W)
                      - TRACKING * GLYPH_W)
    return max(cap_min, min(cap_max, cell * GLYPH_H))


def text_quads(s, cap_m, x0=0.0, baseline=0.0):
    """Lit rectangles for one line, as (x0, y0, x1, y1) in the sign's plane.

    `baseline` is the BOTTOM of the caps, so a caller stacking lines subtracts
    a pitch rather than guessing an offset.
    """
    cell = cap_m / GLYPH_H
    adv = advance_m(cap_m)
    out = []
    for i, ch in enumerate(s):
        gx = x0 + i * adv
        for r0, c0, r1, c1 in _spans(ch):
            # Row 0 is the TOP of the glyph, so it sits highest above baseline,
            # and a rectangle spanning rows r0..r1-1 has its BOTTOM at r1-1.
            y_top = baseline + (GLYPH_H - r0) * cell
            y_bot = baseline + (GLYPH_H - r1) * cell
            out.append((gx + c0 * cell, y_bot, gx + c1 * cell, y_top))
    return out


def wrap(s, n):
    """Break `s` on spaces to at most `n` characters a line.

    Wrapping rather than shrinking, because shrinking is how a sign stops being
    readable at the distance it exists to be read from.
    """
    out, line = [], ""
    for word in str(s).split():
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= n:
            line += " " + word
        else:
            out.append(line)
            line = word
        while len(line) > n:                  # a single word longer than n
            out.append(line[:n])
            line = line[n:]
    if line:
        out.append(line)
    return out


def letter_mesh(lines, face_w, face_h, cap_m=None, header=0, z=0.0,
                cx=0.0, cy=0.0, pad_frac=0.06):
    """Lettering for a stack of lines, centred in a face of that size.

    Returns (verts, tris, groups) in the board's own frame -- +X across, +Y up,
    +Z out of the face -- so it merges straight into `board()`'s output.

    `header` is how many leading lines take the 1.44x face, which is what the
    reference does to "WELCOME TO" above the station's own name.
    """
    lines = [str(x).upper() for x in lines if str(x).strip() != ""]
    if not lines or not LETTERING:
        return [], [], []
    inner_w = face_w * (1.0 - 2 * pad_frac)
    # THE HEADER IS SIZED FIRST AND THE BODY FOLLOWS FROM IT, and the first
    # version had that backwards with a visible result. Fitting the body
    # independently sized each line to its own length, so on a door plaque the
    # ADDRESS -- 13 characters -- came out LARGER than the room's name at 17,
    # and the small print was the biggest thing on the sign. Size has to encode
    # importance or it encodes string length.
    #
    # Fitted ONCE across all header lines together, too: fitting each on its
    # own set a two-line name at two different sizes, which reads as a mistake
    # rather than as a hierarchy. One name is one size.
    if header:
        head = min(fit_cap_m([lines[i]], inner_w) for i in range(header))
        if cap_m:
            head = min(head, cap_m * HEADER_SCALE)
        body = head / HEADER_SCALE
    else:
        head = body = cap_m or fit_cap_m(lines, inner_w)
    caps = [head if i < header else body for i in range(len(lines))]
    # The body still has to FIT, even though it is derived rather than fitted:
    # a short name over a long address would otherwise overrun. Shrinking both
    # together keeps the ratio, which is the thing the hierarchy is made of.
    tail = [s for i, s in enumerate(lines) if i >= header]
    if tail:
        room = fit_cap_m(tail, inner_w)
        if room < body:
            k = room / body
            caps = [c * k for c in caps]
    total = sum(c * LINE_PITCH for c in caps)
    if total > face_h * (1.0 - 2 * pad_frac):
        k = face_h * (1.0 - 2 * pad_frac) / total
        caps = [c * k for c in caps]

    # CENTRE ON THE INK, NOT ON THE PITCH, and lay the block out from the top
    # of the first cap rather than from a running pitch. The block a reader
    # sees runs from the top of line 0's caps to the BASELINE of the last line;
    # the leading below that last line is whitespace no glyph occupies, and
    # centring it too left every two-line plaque visibly riding high in its own
    # frame. Composing it as "cap, then leading, then cap" instead of "pitch
    # per line" is the same total for the interior and correct at both ends.
    lead = [c * (LINE_PITCH - 1.0) for c in caps]
    ink = sum(caps) + sum(lead[:-1])
    v, t, g = [], [], []
    y = cy + ink / 2.0
    for i, (s, cap) in enumerate(zip(lines, caps)):
        y -= cap                                  # top of caps -> baseline
        lo = len(t)
        x = cx - text_width_m(s, cap) / 2.0
        for x0, y0, x1, y1 in text_quads(s, cap, x, y):
            b = len(v)
            v.extend(((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)))
            t.append((b, b + 1, b + 2))
            t.append((b, b + 2, b + 3))
        if len(t) > lo:
            g.extend(["sign_text_head" if i < header else "sign_text"]
                     * (len(t) - lo))
        y -= lead[i]                              # baseline -> next cap top
    return v, t, g


def board_lit(key, with_post=True):
    """A board with its own words on it. THE POINT OF THE MODULE, finally.

    The text comes out of `BOARDS`, which is authority-1 transcription
    including the prop's own two misspellings, so what a player reads on the
    station is what is on the screen-used board.
    """
    b = BOARDS[key]
    v, t, g = board(with_post=with_post)
    lines = [b["header"], b["badge"], b["title"]] + list(b["lines"])
    face_w = BOARD_W_M - 2 * BOARD_FRAME_M
    face_h = BOARD_H_M - 2 * BOARD_FRAME_M
    lv, lt, lg = letter_mesh(
        lines, face_w, face_h, header=1,
        # A hair proud of the recessed lit face, so the lettering catches light
        # separately and is not a decal coplanar with what it sits on -- the
        # same rule `board()` already applies to the face inside its frame.
        z=BOARD_T_M - BOARD_INSET_M + 0.004,
        cy=MOUNT_H_M + BOARD_H_M / 2.0)
    base = len(v)
    v.extend(lv)
    t.extend([(a + base, c + base, d + base) for a, c, d in lt])
    g.extend(lg)
    return v, t, g


# ---------------------------------------------------------------------------
# The arrivals board: a sign that says what is actually happening
# ---------------------------------------------------------------------------
# EVERY OTHER BOARD IN THIS MODULE IS A TRANSCRIPTION and every plaque below is
# a view of the register -- both are static text. This one reads
# `station/traffic.py`, so the words on it change with the hour and with the
# day, and they name the ship that actually berthed.
#
# It is also the one thing that puts the port INTO the station. `traffic.py`
# models 55 movements a day, a two-peaked EMT curve and the liner event, and
# until this existed **nothing rendered any of it** -- no ship arrives in
# geometry, no bay fills, and the only reader was `broadcast.py`, which itself
# had no importer. A board is the cheapest possible surface for a simulation
# nobody can otherwise see, and the show gives us the surface at authority 1:
# `reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
# hub.jpg` puts a wall monitor in the customs area, and the customs boards
# beside it establish the voice.
#
# THE REGISTER OF SHIP NAMES IS NOT HERE. `broadcast.SHIP_CALL` already maps a
# manifest row to what a tannoy calls it, and a board that spelled them a second
# way would be two descriptions of one thing -- the failure this project has
# paid for repeatedly. The board says what the tannoy says.
ARRIVALS_ROWS = 6          # how many movements fit the face at legible caps
ARRIVALS_WINDOW_H = 6.0    # how far ahead it looks


def arrivals_lines(hour=None, day=0, rows=ARRIVALS_ROWS):
    """The board's text, from `traffic.arrivals` rather than from a table.

    Returns a list of lines, header first. `hour` defaults to the station's own
    working hour so a caller that does not care gets something sensible.
    """
    import traffic as _tf                                       # noqa: PLC0415
    import broadcast as _bc                                     # noqa: PLC0415
    if hour is None:
        hour = 10.0
    out = ["ARRIVALS", "EARTH MEAN TIME"]
    up = []
    for a in _tf.arrivals(day):
        d = (a["hour"] - hour) % 24.0
        if d <= ARRIVALS_WINDOW_H:
            up.append((d, a))
    up.sort()
    for _d, a in up[:rows]:
        h = int(a["hour"])
        m = int(round((a["hour"] - h) * 60.0)) % 60
        what = _bc.SHIP_CALL.get(a["type"], a["type"]).upper()
        berth = {"bay": "BAY", "standoff": "PORT",
                 "moored": "STANDING OFF"}[a["berth"]]
        out.append(f"{h:02d}{m:02d}  {what[:22]:22s} {berth}")
    if len(out) == 2:
        out.append("NO MOVEMENTS SCHEDULED")
    return out


def arrivals_board(hour=None, day=0, with_post=True):
    """A lit board whose words are this station-day's actual port traffic.

    Same construction as `board_lit` -- the frame, the recessed face and the
    lettering proud of it are the board, and only the source of the text
    differs. That is deliberate: an arrivals board that looked different from
    the customs boards beside it would read as a different prop, and the
    authority-1 frame shows one visual family in that hall.
    """
    lines = arrivals_lines(hour, day)
    v, t, g = board(with_post=with_post)
    face_w = BOARD_W_M - 2 * BOARD_FRAME_M
    face_h = BOARD_H_M - 2 * BOARD_FRAME_M
    lv, lt, lg = letter_mesh(
        lines, face_w, face_h, header=1,
        z=BOARD_T_M - BOARD_INSET_M + 0.004,
        cy=MOUNT_H_M + BOARD_H_M / 2.0)
    base = len(v)
    v.extend(lv)
    t.extend([(a + base, c + base, d + base) for a, c, d in lt])
    g.extend(lg)
    return v, t, g


def notice_lines(kind="minipax", datum=None, rows=4):
    """A standing surface's text, from `broadcast` rather than from a table.

    `kind` is `"minipax"` or `"isn"`. Both are ERA-LOCKED at source --
    `broadcast.minipax_notices` returns nothing before *The Fall of Night*, so
    a Season 1 render of this board comes back with the fallback line and no
    Ministry of Peace on it at all. FACTIONS.md 5.1 states the rule for the
    armband and it is the same rule: "any armband before The Fall of Night is
    an error."
    """
    import broadcast as _bc                                     # noqa: PLC0415
    items = (_bc.minipax_notices(datum) if kind == "minipax"
             else _bc.isn_bulletins(datum))
    head = ("MINISTRY OF PEACE" if kind == "minipax"
            else "INTERSTELLAR NETWORK NEWS")
    out = [head, "EARTH ALLIANCE"]
    if not items:
        # NOT an empty board. A blank lit panel in a customs hall reads as a
        # broken prop; the station's standing civic text is what is there when
        # there is no notice, and it is authority 1.
        out.append(BOARDS["customs_procedures"]["title"])
        return out
    for a in items[:rows]:
        body = a["text"].split(". ", 1)[-1] if ". " in a["text"] else a["text"]
        for ln in wrap(body.upper(), 34)[:2]:
            out.append(ln)
    return out


def notice_board(kind="minipax", datum=None, with_post=True):
    """A lit board carrying `broadcast`'s standing surfaces.

    THE BUILD NOTE GOVERNS THE LOOK AND IT IS FACTIONS.md 11.5's: the
    propaganda "should read as OFFICIAL AND REASONABLE -- clean typography in
    the same register as the customs boards -- because that is what makes them
    sinister. Do not make them look like villain posters." So this is the same
    board, the same frame, the same letterforms as the authority-1 customs
    transcription hanging beside it. The register IS the design.
    """
    lines = notice_lines(kind, datum)
    v, t, g = board(with_post=with_post)
    face_w = BOARD_W_M - 2 * BOARD_FRAME_M
    face_h = BOARD_H_M - 2 * BOARD_FRAME_M
    lv, lt, lg = letter_mesh(
        lines, face_w, face_h, header=1,
        z=BOARD_T_M - BOARD_INSET_M + 0.004,
        cy=MOUNT_H_M + BOARD_H_M / 2.0)
    base = len(v)
    v.extend(lv)
    t.extend([(a + base, c + base, d + base) for a, c, d in lt])
    g.extend(lg)
    return v, t, g


# ---------------------------------------------------------------------------
# Door plaques: 118 places that could not say what they were
# ---------------------------------------------------------------------------
# judge-3w at a doorway: "no handle, no control plate, no emergency release, no
# hazard chevrons, no room name, no bay number". `directory.py` has held the
# name, sector, ring, deck and bearing of all 118 places for sessions and no
# player could read any of it. A plaque is a VIEW of that register rather than a
# second copy -- this project has been bitten twice by two descriptions of one
# thing drifting apart, and a sign that disagrees with the map is exactly that
# failure in the form a player sees.

## The six colour sectors as the show names them. `canon/00-MASTER.md` §1.4,
## authority 1, records that "Customs Sector" is used ALONGSIDE these rather
## than instead of them.
SECTOR_LABEL = {
    "blue": "BLUE", "red": "RED", "green": "GREEN",
    "grey": "GREY", "brown": "BROWN", "yellow": "YELLOW",
}


# ---------------------------------------------------------------------------
# THE ADDRESS, AND IT IS THE SHOW'S OWN GRAMMAR RATHER THAN OURS
# ---------------------------------------------------------------------------
# WHAT WAS WRONG. `door_text` used to compose `SECTOR RING-DECK BEARING` --
# "GREEN 0-00 000" -- and defended it on the grounds that it is the coordinate
# every other module addresses a place by, so a sign could be checked against
# the register. That argument is good about CHECKABILITY and wrong about
# FIDELITY, and fidelity is what a sign is for. `canon/00-MASTER.md` §3,
# authority 1: *"On-screen location references take the form `<Colour>
# <number>` -- Grey 17, Red 3, Blue 12, Brown 2, Green 2."* Nobody on the show
# ever says a bearing. A station signed in a private three-part coordinate is a
# station signed in a grammar the source does not use, which is the same defect
# as a corridor built to the wrong width.
#
# WHY THE NUMBER IS HARD, AND WHY THAT IS NOT A REASON TO OMIT IT. C-004 is
# OPEN and BLOCKING: no source we hold numbers a ring, the direction is unknown
# (`interior.LEVEL_NUMBERING` is marked UNCONFIRMED for exactly this), and
# `docs/gazetteer/LOCATIONS.md` §1 raises a third possibility -- that the
# number is a 10-degree ANGULAR REGION and not a radial level at all.
# `docs/AAA-STANDARD.md` says under Interaction: *"No interaction may assume a
# level NUMBER. C-004 is open. Address by (sector, ring_index) and let
# bind_labels() attach names later."*
#
# So the number is built the way that document prescribes for every unsourced
# mechanism (*"switchable in one edit"*, the INV-008 pattern):
#
#   * the DIRECTION is not decided here. `interior.LEVEL_NUMBERING` already
#     owns it and is already marked UNCONFIRMED; this reads it. One edit there
#     inverts every sign on the station and every other consumer at once.
#   * WHAT THE NUMBER INDEXES is `LEVEL_READING` below, and both surviving
#     readings are implemented rather than one being assumed.
#   * the number itself is a VIEW of `interior.place_floor_radius` -- the same
#     function `directory.gravity_of` and `rooms.room_extent_m` resolve a place
#     with -- so a sign cannot disagree with the geometry a player is standing
#     on. It is not a table.
#
# AND THE DERIVATION CORROBORATES ITSELF ON THE ONE ADDRESS EVERYBODY KNOWS.
# Nothing about Grey was tuned; the ladder falls out of the hull profile and
# the 3.6 m deck pitch. Grey's occupied levels come out
# {4, 5, 11, 13, 16, 17, 18, 20, 22, 23} -- **GREY 17 EXISTS ON THIS STATION**,
# and `_selftest` asserts it, so a change to the hull or the pitch that pushed
# the show's most famous address off the register would fail the build. Red
# reaches 51 and Blue 30, which is the right order of magnitude for a station
# whose placards run to `Brown-57`.

## WHAT `<number>` INDEXES. C-004 lists two surviving readings and this
## implements both; the third (a level that is neither, i.e. the numbers are
## arbitrary) cannot be built from and is not a reading.
##
##   "radial"  -- a deck. The radial ladder of the sector, from its outermost
##                canonical ring radius inward at `interior.DECK_PITCH_M`.
##   "angular" -- one of 36 ten-degree regions round the circumference, per
##                LOCATIONS.md §1's authority-4 wiki reading.
##
## Switching this line switches every sign on the station and nothing else.
LEVEL_READING = "radial"

## ADDRESSES A SOURCE ACTUALLY GIVES, and they are recorded rather than used.
## Every one is authority 4 (fan wiki / fan site), which `canon/CONFLICTS.md`
## says outright cannot close what two authority-3 sheets could not -- and
## `docs/gazetteer/LAW-CRIME-DOWNBELOW.md` has already RULED on the Zocalo's:
## *"the authority-4 'Red 5' is wrong by four rings"* under our own model.
## They are here so that the disagreement between what a source claims and what
## our geometry derives is VISIBLE and asserted, instead of being rediscovered
## every few sessions. `_selftest` prints the delta for each.
ATTESTED_ADDRESS = {
    "zocalo":        ("red",  5, "https://babylon5.fandom.com/wiki/Z%C3%B3calo"),
    "sanctuary_blue": ("blue", 3, "https://babylon5.fandom.com/wiki/Blue_Sector"),
}

_SCHEMA_CACHE = []
_ANCHOR_CACHE = {}
_LEVEL_CACHE = {}


def _schema():
    """`interior.load()` once per process. 74 ms, and this is called per door."""
    if not _SCHEMA_CACHE:
        _SCHEMA_CACHE.extend(it.load())
    return _SCHEMA_CACHE[0], _SCHEMA_CACHE[1]


def _anchor_r(sector):
    """The radius level 1 is counted from: the sector's outermost ring.

    Taken UNCUT -- `ring_radii` with no `z_m` -- on purpose. The z-aware form
    returns the rings that survive the hull taper at one axial station, so the
    forward end of Blue would count from a different zero than the aft end and
    one deck would carry two level numbers along its own length. A level number
    has to be a property of a radius, not of where you are standing on it.
    """
    if sector not in _ANCHOR_CACHE:
        schema, profile = _schema()
        rings = it.ring_radii(schema, profile, sector)
        _ANCHOR_CACHE[sector] = rings[0]["r_outer"] if rings else 0.0
    return _ANCHOR_CACHE[sector]


def level_from_radius(sector, r_m):
    """The level standing at radius `r_m` in `sector` is on.

    THE RADIUS IS THE PRIMITIVE AND THE PLACE IS THE CONVENIENCE, and that
    ordering is what lets a CORRIDOR carry a level number. A corridor is not a
    register place: `interior.ring_arc` builds it from a radius and a sector and
    has no `place` to hand, which is precisely why every corridor plate on the
    station says something generic. This is the entry point that fixes that, and
    `level_number` below is a two-line wrapper on it.
    """
    rungs = int(round((_anchor_r(sector) - float(r_m)) / it.DECK_PITCH_M))
    if it.LEVEL_NUMBERING == "outermost_is_1":
        return max(1, rungs + 1)
    # Innermost is 1: count the same ladder from the other end. The sector's own
    # depth in rungs is the anchor less the core radius, so the two readings are
    # exact mirrors of one number rather than two derivations that could drift.
    schema, profile = _schema()
    rings = it.ring_radii(schema, profile, sector)
    core = rings[-1]["r_inner"] if rings else 0.0
    depth = int(round((_anchor_r(sector) - core) / it.DECK_PITCH_M))
    return max(1, depth - rungs)


def level_number(place):
    """The `<number>` of this place's address. See the block comment above.

    Returns an int >= 1. Deterministic, cached per place key, and derived --
    never stored, so it cannot go stale against the geometry the way a table
    would.
    """
    key = (place.get("key"), LEVEL_READING, it.LEVEL_NUMBERING)
    if key in _LEVEL_CACHE:
        return _LEVEL_CACHE[key]
    if LEVEL_READING == "angular":
        n = int((float(place["angle_deg"]) % 360.0) // 10.0) + 1
    else:
        schema, profile = _schema()
        r, _ri, _di, _dk = it.place_floor_radius(schema, profile, place)
        n = level_from_radius(place["sector"], r)
    _LEVEL_CACHE[key] = n
    return n


def corridor_plate_lines(address):
    """What a CORRIDOR wall plate says: where you are, in the show's grammar.

    THIS IS THE FUNCTION `interior_kit.CORRIDOR_NOTICES` IS WAITING FOR, and its
    own comment names it: *"WHAT WOULD REPLACE THIS TABLE: one line in
    `interior.ring_arc` handing `corridor_section` the (sector, ring, deck) it
    already has in scope."* Until that line lands, 164 sign plates a deck carry
    eight generic notices and no address, because the kit is addressless by
    construction and *"a sign that says the wrong bay number is worse than no
    sign"*.

    `address` is a dict with `sector` and either `r_floor_m` or `angle_deg`,
    depending on `LEVEL_READING`. Nothing else is needed and nothing else is
    read: a corridor knows its own radius, and that is the whole address.

    Returns two lines -- the sector big, the level under it -- rather than one,
    because a corridor plate is read at a walking glance from further away than
    a door plaque and two short lines set larger than one long one.
    """
    sec = SECTOR_LABEL.get(address.get("sector"),
                           str(address.get("sector", "")).upper())
    if LEVEL_READING == "angular":
        n = int((float(address.get("angle_deg", 0.0)) % 360.0) // 10.0) + 1
    else:
        n = level_from_radius(address["sector"], address["r_floor_m"])
    return [sec, f"LEVEL {n}"]


def address_of(place):
    """`BLUE 12` -- the whole address a player reads, in the show's grammar."""
    sec = SECTOR_LABEL.get(place["sector"], str(place["sector"]).upper())
    return f"{sec} {level_number(place)}"


def address_report():
    """Every place's address and WHERE ITS NUMBER CAME FROM, one row each.

    The brief for this work said: *"If the register cannot supply a show-style
    number for a place, say so per place rather than inventing one silently."*
    This is that per-place statement, and it is a function rather than a
    comment so it can be printed, diffed and asserted. `basis` is one of:

      `derived`  -- from `interior.place_floor_radius`, under `LEVEL_READING`
                    and `interior.LEVEL_NUMBERING`. Authority 5 for the NUMBER;
                    the grammar it is written in is authority 1.
      `attested` -- a source gives this place an address in as many words.
                    None is currently USED (see `ATTESTED_ADDRESS`); the row
                    records the claim and our delta from it.
    """
    import directory as _dr                                    # noqa: PLC0415
    out = []
    for p in _dr.PLACES:
        n = level_number(p)
        att = ATTESTED_ADDRESS.get(p["key"])
        out.append({
            "key": p["key"], "sector": p["sector"], "level": n,
            "text": address_of(p),
            "basis": "derived",
            "attested": None if att is None else f"{att[0]} {att[1]}",
            "delta": None if att is None else n - att[1],
            "attested_src": None if att is None else att[2],
        })
    return out

# SIZED BY LEGIBILITY, not by taste, and the gate below is what set it. At
# 0.30 m the longest place name on the station fitted at 20.9 mm caps, and a
# 5x7 lattice needs about 7 arc-minutes a CELL to resolve, so those caps stop
# being readable at 1.47 m -- inside the width of the corridor they hang in. A
# sign a player cannot read while walking past it is set dressing. 0.40 m puts
# the worst plaque on the station comfortably past 1.5 m.
PLAQUE_W_M = 0.40
PLAQUE_H_M = 0.26
PLAQUE_T_M = 0.022
## Beside the door at the height a person reads without moving their head.
## `drum_ground.stand_on_ground` and INV-071 both use 1.7 m stature, so eye
## height is 1.7 and a plaque centred a little below it is read straight on.
PLAQUE_CENTRE_H_M = 1.55


def door_text(place):
    """The lines on one door's plaque: what it is, then where you are.

    The address is `<Colour> <number>` -- `canon/00-MASTER.md` §3, authority 1,
    the grammar the show actually signs. It replaced `SECTOR RING-DECK BEARING`
    ("GREEN 0-00 000"), which was our coordinate rather than the station's; see
    the block comment above `LEVEL_READING`. It is also 5 to 8 characters
    instead of 13, so every plaque on the station got cheaper and its caps got
    bigger in the same edit.
    """
    addr = address_of(place)
    # A DOOR IS NOT A CATALOGUE ENTRY. `directory.py`'s `name` is a gazetteer
    # description -- "Babylon 5 Advisory Council Chamber", "Rotation drivers
    # and mag-lev bearing" -- and a door in a corridor says "COUNCIL CHAMBER".
    # Setting the description ran to four lines on 36 of 118 plaques, squeezed
    # the caps, and cost more geometry than the pressure door beside it.
    #
    # AND IT IS NEVER SILENTLY SHORTENED. Where the description does not fit
    # two lines the plaque falls back to the register's own KEY, which is
    # already a short human-authored unique label -- `council_chamber`,
    # `radial_tubes` -- rather than to the description with its tail cut off.
    # A sign reading "MICRO-GRAVITY MAINTENANCE" for a place called
    # "...BAYS (2)" is worse than a short sign: it is a wrong one.
    lines = wrap(place["name"].upper(), 18)
    if len(lines) > 2:
        lines = wrap(str(place["key"]).replace("_", " ").upper(), 18)[:2]
    # NAME FIRST, ADDRESS AS SMALL PRINT, and the first version had it the
    # other way round. `letter_mesh` sets its leading lines at 1.44x, so
    # putting the address first made `GREEN 0-00 000` the largest thing on the
    # plaque and the room's name the caption -- which is the wrong hierarchy on
    # a door, and is not what the reference does either: on the customs board
    # "WELCOME TO" is the SMALL line and "BABYLON 5" is the big one. The
    # important thing is big. It is also cheaper, because the address is the
    # one line that appears on all 118 and it now sets in the body face.
    return lines + [addr]


# THE FIELD WAS PROUD OF ITS FRAME AND THE REFERENCE HAS IT RECESSED, which is
# a one-line defect with a visible consequence. `door_plaque` used to lay a
# full-size backplate 0.0099 m thick and then stand a SMALLER box on top of it
# from 0.0099 to 0.022 -- so the dark field projected 12 mm out of its own
# frame, and the lettering projected further still. `reference/00-INDEX.md`,
# `07-sector-grey/grey level 1.webp` re-examined at 14x, authority 1:
# *"a landscape plaque set in a RECESSED dark field"*. A recess is not a
# decorative preference: it is what puts the frame's own shadow across the top
# of the letters, which is most of how a matte unlit plate reads as a plate
# rather than as a sticker. `board()` has always built its lit face this way
# and the plaques did not.
PLAQUE_REBATE_M = 0.006     # how far the field sits BEHIND the frame face
PLAQUE_BEZEL_M = 0.012      # width of the frame rail


def _quad(m, x0, y0, x1, y1, z, group):
    """One front-facing rectangle in the plane z. Two triangles, not twelve."""
    b = len(m.v)
    m.v.extend([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
    m.t.append((b, b + 1, b + 2))
    m.t.append((b, b + 2, b + 3))
    m.g.extend([group] * 2)


def _recessed_plate(m, hw, hh, thick, bezel, rebate, frame_g, field_g,
                    cx=0.0, cy=0.0, z0=0.0):
    """A framed plate whose field is set BACK inside its own frame.

    Same construction as `board()` -- four rails at full thickness and one
    recessed field spanning the opening -- rather than a third convention. The
    caller gets the field's front z back so it can put lettering a hair proud
    of the field and still inside the rebate.
    """
    m.box(cx - hw, cx + hw, cy + hh - bezel, cy + hh, z0, z0 + thick, frame_g)
    m.box(cx - hw, cx + hw, cy - hh, cy - hh + bezel, z0, z0 + thick, frame_g)
    m.box(cx - hw, cx - hw + bezel, cy - hh + bezel, cy + hh - bezel,
          z0, z0 + thick, frame_g)
    m.box(cx + hw - bezel, cx + hw, cy - hh + bezel, cy + hh - bezel,
          z0, z0 + thick, frame_g)
    m.box(cx - hw + bezel, cx + hw - bezel, cy - hh + bezel, cy + hh - bezel,
          z0, z0 + thick - rebate, field_g)
    return z0 + thick - rebate


def _merge_letters(m, lines, face_w, face_h, z, cx=0.0, cy=0.0, header=0,
                   group=None, cap_m=None):
    """`letter_mesh` merged into an `_M`, optionally renamed to one group."""
    lv, lt, lg = letter_mesh(lines, face_w, face_h, header=header, z=z,
                             cx=cx, cy=cy, cap_m=cap_m)
    base = len(m.v)
    m.v.extend(lv)
    m.t.extend([(a + base, c + base, d + base) for a, c, d in lt])
    m.g.extend([group] * len(lt) if group else lg)
    return len(lt)


# ---------------------------------------------------------------------------
# The LEVEL plaque -- the most-seen piece of typography in the show, and until
# now a 0.42 x 0.03 x 0.26 m BLANK BOX
# ---------------------------------------------------------------------------
# `rooms.PROPS["level_plaque"]`, `docking_bay.py` and `shuttle.py` all place a
# `prop_level_plaque`, and every one of them is an untextured slab. This builds
# the thing they are standing in for.
#
# THE REFERENCE, and it is the only authority-1 frame of station wayfinding
# typography we hold that is NOT the customs board. `reference/00-INDEX.md`,
# `07-sector-grey/grey level 1.webp` re-examined at 14x:
#
#   "black ground carrying white uppercase sans-serif letters, and the first
#    four are clearly L, E, V, E. The word is LEVEL. The number is off-frame.
#    LEVEL is a wayfinding word physically signed on station corridor walls, in
#    white-on-black uppercase, on a landscape plaque set in a recessed dark
#    field at high level."
#
# RE-MEASURED HERE RATHER THAN TAKEN ON TRUST, because a claim about colour is
# exactly the kind that rots. Balanced through `materials.GREY_WORLD_GAINS` for
# this frame (0.970/1.087/0.953), same method `materials.sign_deck_plaque` uses
# on the OTHER plaque in the same frame:
#
#   anchor wall plate course (0.019,0.236)-(0.125,0.293)   V 0.297
#   LEVEL field, above the letters (0.930,0.170)-(1,0.200) V 0.125
#   LEVEL field, below the letters (0.930,0.300)-(1,0.335) V 0.129
#   wall beside the plaque         (0.870,0.150)-(0.918,0.340) V 0.276
#
# So the field is **0.46x the wall it hangs on** and its brightest pixel
# (linear 0.058) never reaches the wall's (0.113). **IT IS NOT EMISSIVE.** That
# is the finding worth carrying: the customs board peaks at 21x the structure
# around it and this plate peaks BELOW it, so the station has two sign classes
# and they are lit oppositely. `materials.sign_field_level` and
# `sign_text_level` carry these numbers.
#
# The plaque's left edge is at x = 0.924 of frame and it runs off the right
# edge, so its WIDTH cannot be measured -- only that it is landscape and at
# least 0.076 of frame wide. Absolute size is INV-467.
LEVEL_PLATE_W_M = 0.40
LEVEL_PLATE_H_M = 0.125
LEVEL_PLATE_T_M = 0.018
## "AT HIGH LEVEL" IS A CONSTRAINT, NOT A NUMBER, AND THE CORRIDOR OWNS THE
## NUMBER. This took two wrong answers and an engine frame, and both wrong
## answers are worth keeping because each was refuted by a different kind of
## evidence.
##
## FIRST: a flat 2.30 m, reasoned from a 2.60 m ceiling this module had
## remembered. `interior_kit.PROVISIONAL` says the corridor is 3.00 m with a
## 0.50 m head chamfer, so the flat wall runs to 2.50 m and 2.30 m was
## legitimately on it. A render aimed straight at the plate came back with
## BARE WALL, so the chamfer was never the problem.
##
## SECOND: the volume was already occupied. Querying the assembled deck for
## everything within 1.2 m of the plate's own angle and 0.30 m of its z shows
## `dress_conduit_c00` and `light_bezel_c00` running through it -- the
## corridor's clamped high-level services occupy **r 209.0-209.6 m**, which on
## a floor at 211.55 m is **1.95-2.55 m above the deck**. The plate was behind
## the conduit run. Nothing could have failed for this: `collision.prop_boxes`
## does not see decals, and every closure and coverage gate in the project
## measures one mesh at a time. It is the tram-through-a-spoke defect at
## plaque scale.
##
## SO THE PLATE GOES IN THE HIGHEST CLEAR BAND, which is derived from the
## mount below it and bounded by the measured service band above it: the door
## plaque's top (1.680 m), a 0.070 m reveal, and half a plate. It is still
## above a 1.7 m eye and still read at a raised glance, which is what the
## authority-1 frame shows; what it is not is "as high as the wall goes", and
## the wall is why. `_selftest` asserts both bounds.
SERVICE_BAND_M = (1.95, 2.55)   # measured off station/generated/.../shot_blue_0_0.obj
LEVEL_PLATE_GAP_M = 0.070


def _level_plate_centre_h():
    return (PLAQUE_CENTRE_H_M + PLAQUE_H_M / 2.0
            + LEVEL_PLATE_GAP_M + LEVEL_PLATE_H_M / 2.0)


LEVEL_PLATE_CENTRE_H_M = 1.8125
## Whether `door_plaque` carries one. It is the negative control for the whole
## level-plate feature: one edit here and the station has door plaques and no
## level plaques, which is what it had before this session.
LEVEL_PLATE_ON_DOOR = True


def level_text(place):
    """`LEVEL 12` -- one line, the word the frame shows and our own number.

    ONE LINE AND NOT TWO, and the sector is deliberately absent. The authority-1
    frame shows the word `LEVEL` followed by a number that runs off the edge; it
    does not show a colour. The colour is on the door plaque 0.75 m below this
    one, which is exactly how the show distributes it -- `Grey 17` is what
    people SAY, and what is painted on the wall is `LEVEL 17`.
    """
    return f"LEVEL {level_number(place)}"


def level_plaque(place, text=None):
    """The corridor level plate: white on black, in a recessed field.

    Own frame: +X across, +Y up, +Z out of the face, centred on (0, 0).
    """
    m = _M()
    hw, hh = LEVEL_PLATE_W_M / 2.0, LEVEL_PLATE_H_M / 2.0
    b = 0.010
    face_z = _recessed_plate(m, hw, hh, LEVEL_PLATE_T_M, b, PLAQUE_REBATE_M,
                             "sign_frame", "sign_field_level")
    # `sign_text_level`, a THIRD lettering group, because this lettering is a
    # different material from every other sign on the station: white, matte and
    # unlit, against `sign_text_lit`'s emissive amber. The name keeps the
    # `sign_text` prefix on purpose -- `deck.py`'s watertightness check and
    # `interior_kit.DECAL_GROUPS` both exempt lettering by that substring, and
    # a decal group that did not carry it would be counted as a hole in the
    # deck.
    _merge_letters(m, [text or level_text(place)],
                   LEVEL_PLATE_W_M - 2 * b, LEVEL_PLATE_H_M - 2 * b,
                   z=face_z + 0.0015, group="sign_text_level")
    return m.as_tuple()


# ---------------------------------------------------------------------------
# Warning signage, and it is the register's own declaration rather than a list
# ---------------------------------------------------------------------------
# A warning that is placed by hand is a warning that will be missing from the
# next room somebody adds. Every row below keys on a `functions` or `interacts`
# value that `directory.py` ALREADY declares, so a new place with a reactor in
# it gets a radiation legend for the same reason it gets a reactor.
#
# The legends are authority 5 and are the plainest form of the words the show's
# own signage uses -- `signage.BOARDS`' authority-1 register is flat imperative
# uppercase ("FOLLOW ALL CUSTOMS PROCEDURES.", "SEE MONITORS FOR DETAILS"), and
# the same voice is used here rather than a modern pictogram vocabulary. INV-468.
HAZARD_BY_FUNCTION = (
    ("radiation_boundary",    ("RADIATION", "AUTHORISED PERSONNEL ONLY")),
    ("power_generation",      ("RADIATION", "AUTHORISED PERSONNEL ONLY")),
    ("reactor_control",       ("RADIATION", "AUTHORISED PERSONNEL ONLY")),
    ("eva_egress",            ("VACUUM", "PRESSURE SUITS BEYOND THIS POINT")),
    # `sealed_volume` IS NOT VACUUM, and reading it as vacuum put
    # "PRESSURE SUITS BEYOND THIS POINT" on the Markab quarter -- a pressurised
    # room sealed after a plague, whose whole point is that it is intact and
    # nobody may go in. The register holds exactly two: `markab_quarter` and
    # `welded_shut`, and both are sealed by ORDER rather than by pressure.
    ("sealed_volume",         ("SEALED BY ORDER", "NO ADMITTANCE")),
    ("quarantine",            ("QUARANTINE", "NO ADMITTANCE")),
    # Kosh's quarters are a non-human atmosphere held at pressure, not a
    # medical quarantine: the hazard is the air, and the customs board's own
    # authority-1 line -- "SIX DIFFERENT ATMOSPHERES ARE CURRENTLY AVAILABLE" --
    # is the fact this legend points at.
    ("sealed_environment",    ("ATMOSPHERE", "NON-STANDARD - SEE MONITOR")),
    ("atmosphere_containment", ("ATMOSPHERE", "NON-STANDARD - SEE MONITOR")),
    ("multi_environ",         ("ATMOSPHERE", "NON-STANDARD - SEE MONITOR")),
    ("hazardous_storage",     ("HAZARDOUS STORES", "NO NAKED LIGHT")),
    ("fuel_storage",          ("HAZARDOUS STORES", "NO NAKED LIGHT")),
    ("fuel_transfer",         ("HAZARDOUS STORES", "NO NAKED LIGHT")),
    ("starfury_launch",       ("LAUNCH BAY", "CLEAR THE DECK ON ALARM")),
    ("microgravity_handling", ("ZERO GRAVITY", "USE HANDHOLDS")),
    ("variable_gravity",      ("VARIABLE GRAVITY", "USE HANDHOLDS")),
    ("coolant_loop",          ("HOT SURFACES", "DO NOT TOUCH")),
    ("heat_rejection",        ("HOT SURFACES", "DO NOT TOUCH")),
    ("detention",             ("RESTRICTED", "SECURITY ESCORT REQUIRED")),
    ("waste_processing",      ("BIOHAZARD", "PROTECTIVE EQUIPMENT REQUIRED")),
)
HAZARD_BY_INTERACT = (
    ("welded_door",           ("SEALED BY ORDER", "NO ADMITTANCE")),
    ("airlock_door",          ("AIRLOCK", "CHECK PRESSURE BEFORE CYCLING")),
    ("launch_tube",           ("LAUNCH BAY", "CLEAR THE DECK ON ALARM")),
    ("blast_door",            ("BLAST DOOR", "KEEP CLEAR")),
    ("isolation_door",        ("QUARANTINE", "NO ADMITTANCE")),
)

## A HEADING IS AS BIG AS ITS LONGEST LINE LETS IT BE, so the heading length is
## a legibility constant and not a wording preference. On a 0.384 m face a 16-
## character heading sets at 27.5 mm and reads to 1.93 m; at 23 characters
## ("NON-STANDARD ATMOSPHERE", the first draft) it sets at 18.8 mm and reads to
## 1.32 m -- inside the corridor's own half-width. `_selftest` asserts the bound
## so a longer wording cannot be added without the reading distance being
## re-checked.
HAZARD_HEAD_MAX = 16
HAZARD_W_M = 0.40
HAZARD_H_M = 0.175
HAZARD_T_M = 0.014
## The chevron band. `docs/gazetteer/LOCATIONS.md` records the Zocalo deck's
## "band of yellow/red/blue diagonal chevron striping" at authority 1, so a
## diagonal hazard stripe is a motif the station already has; this is that
## motif at plaque scale.
HAZARD_CHEVRONS = 9


def hazard_of(place):
    """The warning this place's own declaration earns it, or None.

    FUNCTIONS FIRST, AND THE FIRST VERSION HAD IT THE OTHER WAY ROUND with a
    result the gate caught: `fusion_core`, `reactor_hall` and `generator_hall`
    all declare `blast_door`, so all three were signed `BLAST DOOR / KEEP CLEAR`
    and NOT ONE PLACE ON THE STATION carried a radiation legend. A blast door
    is how the door behaves; the hazard is what is behind it, and a warning
    names the hazard. So the place's function decides and the door type is the
    fallback for places whose function is not itself dangerous.
    """
    fn = set(place.get("functions") or ())
    for k, legend in HAZARD_BY_FUNCTION:
        if k in fn:
            return legend
    ia = set(place.get("interacts") or ())
    for k, legend in HAZARD_BY_INTERACT:
        if k in ia:
            return legend
    return None


def hazard_plate(legend, cy=0.0):
    """A chevron-banded warning strip. +X across, +Y up, +Z out."""
    m = _M()
    hw, hh = HAZARD_W_M / 2.0, HAZARD_H_M / 2.0
    b = 0.008
    face_z = _recessed_plate(m, hw, hh, HAZARD_T_M, b, 0.004,
                             "sign_frame", "sign_field_hazard", cy=cy)
    # The chevrons run along the TOP of the plate and the legend under them, so
    # the stripe reads as a band rather than as a background the words sit on.
    band_h = (HAZARD_H_M - 2 * b) * 0.26
    y1 = cy + hh - b
    y0 = y1 - band_h
    step = (HAZARD_W_M - 2 * b) / HAZARD_CHEVRONS
    for i in range(HAZARD_CHEVRONS):
        x0 = -hw + b + i * step
        # FLAT QUADS, NOT BOXES. A stripe is paint on the field, and a box is
        # 12 triangles where a decal is 2 -- 108 against 18 for the band. The
        # first version used `m.box` and the whole door mount came out 1,078
        # triangles against a 589 bar, of which the stripe alone was 90.
        _quad(m, x0, y0, x0 + step * 0.55, y1, face_z + 0.0012,
              "sign_hazard_stripe")
    # WRAPPED, NOT SHRUNK. `wrap`'s own docstring gives the reason -- "shrinking
    # is how a sign stops being readable at the distance it exists to be read
    # from" -- and the gate below caught this file ignoring its own rule: set on
    # one line, "PRESSURE SUITS BEYOND THIS POINT" came out at 13.5 mm and
    # legible from 0.95 m, which is closer than a body can stand to a wall.
    lines = [legend[0]] + wrap(legend[1], 20)
    _merge_letters(m, lines, HAZARD_W_M - 2 * b,
                   (HAZARD_H_M - 2 * b) - band_h,
                   z=face_z + 0.0015, cy=(cy - hh + b + (y0 - (cy - hh + b)) / 2.0),
                   header=1, group="sign_text_level")
    return m.as_tuple()


def door_plaque(place, level_plate=None, hazard=True):
    """The sign beside one door, in its own frame: +X across, +Y up, +Z out.

    Three plates on one mount, and each is there because the register says so:

      * the plaque itself -- what the room is, and `<Colour> <number>`;
      * a LEVEL plate above it, when `LEVEL_PLATE_ON_DOOR`. The authority-1
        frame puts one "at high level" on a corridor wall, and this is the only
        shipped caller that knows which level it is standing on;
      * a hazard strip below it, when `hazard_of(place)` returns one -- so a
        reactor hall is signed because it is a reactor hall.
    """
    m = _M()
    hw, hh = PLAQUE_W_M / 2.0, PLAQUE_H_M / 2.0
    b = PLAQUE_BEZEL_M
    # `sign_field`, NOT `sign_face`. The two are different signs in the show
    # and both are authority 1: `sign_face` is the customs hall's large backlit
    # BLUE information board, and `sign_field` is the black-fielded display
    # panel this module's palette was measured off. A door plaque has no
    # reference of its own -- INV-086 says so -- and takes the black, because
    # the black is the half of the reference our corridor does not have.
    face_z = _recessed_plate(m, hw, hh, PLAQUE_T_M, b, PLAQUE_REBATE_M,
                             "sign_frame", "sign_field")
    lines = door_text(place)
    # Every NAME line takes the large face and the trailing address line does
    # not, so a two-line name does not have its second line demoted to small
    # print. `door_text` puts the address last precisely so this is
    # `len(lines) - 1` and not a magic number that drifts when the layout does.
    _merge_letters(m, lines, PLAQUE_W_M - 2 * b, PLAQUE_H_M - 2 * b,
                   z=face_z + 0.0015, header=len(lines) - 1)

    want_level = LEVEL_PLATE_ON_DOOR if level_plate is None else level_plate
    if want_level:
        dy = LEVEL_PLATE_CENTRE_H_M - PLAQUE_CENTRE_H_M
        lv, lt, lg = level_plaque(place)
        base = len(m.v)
        m.v.extend([(x, y + dy, z) for x, y, z in lv])
        m.t.extend([(a + base, c + base, d + base) for a, c, d in lt])
        m.g.extend(lg)
    legend = hazard_of(place) if hazard else None
    if legend:
        # Directly under the plaque with a 20 mm reveal, so the two read as one
        # mount rather than as two signs somebody put near each other.
        hv, ht, hg = hazard_plate(legend,
                                  cy=-(hh + 0.020 + HAZARD_H_M / 2.0))
        base = len(m.v)
        m.v.extend(hv)
        m.t.extend([(a + base, c + base, d + base) for a, c, d in ht])
        m.g.extend(hg)
    return m.as_tuple()


# ---------------------------------------------------------------------------
# Wayfinding: the sign that says which way, which no station of 250,000 lacks
# ---------------------------------------------------------------------------
# THE DESTINATIONS ARE THE REGISTER'S OWN ADJACENCY, not a hand-written list.
# `directory.PLACES[i]["adjacent"]` already states what is next to what, and a
# direction board built from anything else would be a second map that drifts
# from the first. The ARROW is the only invention here (INV-468): a 5x7 lattice
# has no arrow, so three were drawn into `_FONT` in the same idiom as the rest
# of the face, and they are the only glyphs in it that are not letterforms.
ARROW_LEFT, ARROW_RIGHT, ARROW_AHEAD = "<", ">", "^"
DIRECTION_W_M = 0.62
DIRECTION_H_M = 0.30
DIRECTION_T_M = 0.020
DIRECTION_ROWS = 4


def wayfinding_lines(place, rows=DIRECTION_ROWS):
    """`> ZOCALO` and friends: where you can get to from here.

    The arrow is assigned from the destination's BEARING relative to this
    place's, on the ring both stand on: a place further round in +theta is to
    the right of somebody facing along the arc, one behind is left, and one at
    the same bearing on another radius is straight on. It is arithmetic on the
    register rather than a choice, so it cannot be wrong in a way nobody
    notices -- and it is stated here that it assumes the reader faces +theta,
    which is the one thing a caller has to honour when it places the board.
    """
    import directory as _dr                                    # noqa: PLC0415
    out = [f"LEVEL {level_number(place)}"]
    here = float(place["angle_deg"]) % 360.0
    for k in (place.get("adjacent") or ())[:rows]:
        try:
            q = _dr.by_key(k)
        except KeyError:               # `adjacent` may name a non-place row
            continue
        if q is None:
            continue
        d = (float(q["angle_deg"]) - here + 540.0) % 360.0 - 180.0
        arrow = (ARROW_AHEAD if abs(d) < 2.0
                 else ARROW_RIGHT if d > 0 else ARROW_LEFT)
        name = wrap(q["name"].upper(), 20)
        label = name[0] if len(name) == 1 else str(q["key"]).replace("_", " ").upper()
        out.append(f"{arrow} {label[:20]}")
    if len(out) == 1:
        out.append(f"{ARROW_AHEAD} {address_of(place)}")
    return out


def direction_board(place, rows=DIRECTION_ROWS):
    """A wayfinding board. +X across, +Y up, +Z out of the face.

    NOT WIRED INTO THE SHIPPED DECK, and saying so is the point. Nothing in
    `station/deck.py` or `station/interior.py` places one, because a direction
    board belongs at a JUNCTION and `interior.ring_arc` does not yet tell the
    corridor kit where it is (see this module's return note and
    `interior_kit`'s `CORRIDOR_NOTICES` comment). It is built, gated and costed
    here so that the wiring is one call rather than a session; it is exercised
    by `write_obj` so its groups are inside `test_materials_layer3`'s coverage.
    """
    m = _M()
    hw, hh = DIRECTION_W_M / 2.0, DIRECTION_H_M / 2.0
    b = 0.014
    face_z = _recessed_plate(m, hw, hh, DIRECTION_T_M, b, PLAQUE_REBATE_M,
                             "sign_frame", "sign_field")
    _merge_letters(m, wayfinding_lines(place, rows),
                   DIRECTION_W_M - 2 * b, DIRECTION_H_M - 2 * b,
                   z=face_z + 0.0015, header=1)
    return m.as_tuple()


# ---------------------------------------------------------------------------
# The Zocalo wordmark and the "5" roundel -- two gazetteer entries of their own
# ---------------------------------------------------------------------------
# `docs/gazetteer/LOCATIONS.md` gives each its own row, both authority 1, and
# both were BLANK RECTANGLES: `zocalo.neon_sign()` builds a 1.9 x 0.84 m
# `zoc_neon_face` slab and its own docstring says "the six glyphs are a decal
# on `zoc_neon_face`, not geometry" -- and there is no decal, because there are
# no UVs anywhere in this project (see the block comment above `_FONT`). So the
# station's most recognisable sign renders as a lit rectangle.
#
# THE WORDMARK CANNOT BE SET IN THE 5x7 FACE and it is worth saying why rather
# than doing it badly. LOCATIONS.md X-215, authority 1:
#
#   "'Zocalo' in Latin letterforms, a rounded SINGLE-STROKE TUBE SCRIPT with a
#    DOT IN THE COUNTER OF EACH 'o', a SWASHED Z and a TRIANGULAR COUNTER in
#    the 'a'. Orange-red hung under the gallery deck in one frame, cyan over a
#    portal in another -- glyph-for-glyph the same wordmark."
#
# A single-stroke tube script is a PATH, and a path is exactly what a bitmap
# lattice cannot hold: every feature named above -- the swash, the dots, the
# triangular counter -- is a property of a stroke centreline. So the wordmark
# is authored as centrelines and swept into ribbons, which is also what the
# object physically is: bent glass tube. INV-469 records the six paths as an
# extrapolation in style; what is authority 1 is the letter sequence, the case,
# the single-stroke construction, the dots, the swash and the counter.
TUBE_W = 0.105                      # stroke width as a fraction of cap height
## SIZED TO THE BOARD IT HANGS ON, not chosen. `zocalo.MEASURED` gives the sign
## 1.90 x 0.84 m and `neon_sign` insets its lit face by 0.06 m a side, so the
## wordmark has 1.78 m of face to cross. The six advances below sum to 4.56 cap
## heights, and 1.78 / 4.56 = 0.390 -- so 0.38 leaves a 0.09 m margin and the
## first attempt at 0.40 overran the board by 40 mm, which the gate caught.
WORDMARK_CAP_M = 0.38

## Stroke centrelines in a unit em: x from 0, y from the baseline, cap = 1.0.
## `loop` closes the path; `dot` is a filled disc in the counter.
_WORDMARK = (
    ("Z", 0.98, dict(paths=[[(0.04, 0.84), (0.10, 0.96), (0.82, 0.96),
                             (0.08, 0.10), (0.70, 0.10), (0.86, 0.05),
                             (0.96, -0.10)]])),
    ("o", 0.80, dict(loops=[((0.38, 0.31), 0.30)], dots=[((0.38, 0.31), 0.085)])),
    ("c", 0.74, dict(arcs=[((0.38, 0.31), 0.30, 42.0, 318.0)])),
    ("a", 0.84, dict(paths=[[(0.64, 0.58), (0.22, 0.55), (0.05, 0.30),
                             (0.26, 0.05), (0.64, 0.10)],
                            [(0.64, 0.62), (0.64, 0.01)]])),
    ("l", 0.40, dict(paths=[[(0.04, 0.86), (0.16, 0.98), (0.16, 0.06),
                             (0.30, -0.02)]])),
    ("o", 0.80, dict(loops=[((0.38, 0.31), 0.30)], dots=[((0.38, 0.31), 0.085)])),
)


def _ribbon(m, pts, w, z, group, close=False):
    """Sweep a polyline into a flat ribbon of width `w` in the plane z.

    Segments are separate quads with a square plug at every joint. A proper
    miter would be fewer triangles and would need a degenerate case for the
    reversal in the Z's diagonal; a plug is 2 triangles and cannot fold.
    """
    n = len(pts)
    seq = list(range(n)) + ([0] if close else [])
    for i in range(len(seq) - 1):
        (x0, y0), (x1, y1) = pts[seq[i]], pts[seq[i + 1]]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            continue
        px, py = -dy / ln * w / 2.0, dx / ln * w / 2.0
        b = len(m.v)
        m.v.extend([(x0 + px, y0 + py, z), (x0 - px, y0 - py, z),
                    (x1 - px, y1 - py, z), (x1 + px, y1 + py, z)])
        m.t.append((b, b + 1, b + 2))
        m.t.append((b, b + 2, b + 3))
        m.g.extend([group] * 2)
    joints = seq if close else seq[1:-1]
    for i in joints:
        x, y = pts[i]
        h = w / 2.0
        b = len(m.v)
        m.v.extend([(x - h, y - h, z), (x + h, y - h, z),
                    (x + h, y + h, z), (x - h, y + h, z)])
        m.t.append((b, b + 1, b + 2))
        m.t.append((b, b + 2, b + 3))
        m.g.extend([group] * 2)


def _disc(m, cx, cy, r, z, group, seg=14):
    b = len(m.v)
    m.v.append((cx, cy, z))
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        m.v.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for i in range(seg):
        m.t.append((b, b + 1 + i, b + 1 + (i + 1) % seg))
    m.g.extend([group] * seg)


def zocalo_wordmark(cap_m=None, z=0.0, group="sign_wordmark"):
    """`Zocalo` as bent tube. +X across, +Y up from the baseline, +Z out.

    Returns (verts, tris, groups). Sized by CAP HEIGHT rather than by overall
    width so a caller can hang it on any board and the stroke stays the same
    weight relative to the letters, which is what makes a tube script read as
    one continuous tube rather than as six drawings.
    """
    m = _M()
    cap_m = WORDMARK_CAP_M if cap_m is None else cap_m
    w = TUBE_W * cap_m
    x = 0.0
    for _ch, adv, spec in _WORDMARK:
        for p in spec.get("paths", ()):
            _ribbon(m, [(x + px * cap_m, py * cap_m) for px, py in p],
                    w, z, group)
        for (cx, cy), r in spec.get("loops", ()):
            pts = [(x + (cx + r * math.cos(2 * math.pi * i / 16)) * cap_m,
                    (cy + r * math.sin(2 * math.pi * i / 16)) * cap_m)
                   for i in range(16)]
            _ribbon(m, pts, w, z, group, close=True)
        for (cx, cy), r, a0, a1 in spec.get("arcs", ()):
            n = 12
            pts = [(x + (cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1)))) * cap_m,
                    (cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) * cap_m)
                   for i in range(n)]
            _ribbon(m, pts, w, z, group)
        for (cx, cy), r in spec.get("dots", ()):
            _disc(m, x + cx * cap_m, cy * cap_m, r * cap_m, z, group, seg=10)
        x += adv * cap_m
    return m.as_tuple()


def wordmark_extent_m(cap_m=None):
    """(width, height) the wordmark occupies, so a caller can fit its board."""
    cap_m = WORDMARK_CAP_M if cap_m is None else cap_m
    w = sum(adv for _c, adv, _s in _WORDMARK) * cap_m
    return w, 1.10 * cap_m


## The "5" roundel. LOCATIONS.md X-216, authority 1: "a BOLD SLAB NUMERAL with
## a BLACK OUTER KEYLINE and a WHITE INLINE, applied large to cream drum panels
## forming chair backs and table pedestals. The same glyph as the shield patch
## and the floor inlay -- ONE DECAL ASSET, THREE APPLICATIONS." One asset is
## the design rule and this is the asset: `five_roundel` is called for the
## chair back, the table pedestal and the terrazzo floor inlay, at three sizes.
##
## THE LETTERFORM IS THE MODULE'S OWN 5x7 '5' AND THAT IS THE INVENTION --
## INV-469, the same argument INV-086 already makes for the notice face. The
## show's numeral is a drawn slab serif; a 5x7 lattice cannot hold a serif. What
## it CAN hold is the numeral; what it CANNOT hold is the inline, and that took
## two failed attempts to establish rather than one guess.
##
## ATTEMPT 1 -- a `5` at 0.46 laid over a `5` at 1.0, both centred on the same
## origin. An inline is a stroke inside each STROKE, and a smaller copy of the
## whole glyph follows no stroke at all: it punched an unrelated hole through
## the middle and the mark read as a broken numeral. A flat raster showed it in
## one look, which is the argument for rendering geometry before believing it.
##
## ATTEMPT 2 -- inset every stroke rectangle by a hairline. Correct in
## principle and impossible on this lattice, which is the useful finding: a 5x7
## stroke is ONE CELL wide, so any inline that is visible at all eats most of
## the stroke and the bold slab numeral becomes an outline drawing. The show's
## numeral is a drawn slab whose stroke is several times the inline; ours has
## no room inside itself.
##
## SO THE ROUNDEL IS A STROKE PATH, exactly like the wordmark above, and for
## exactly the same reason -- the features the gazetteer names are properties
## of a centreline. One centreline, swept twice: a bold ink ribbon, and a
## narrower field-coloured ribbon down the middle of it. That IS a slab numeral
## with an inline, and the disc's own ring is the keyline. It also honours
## LOCATIONS.md X-216's "ONE DECAL ASSET, three applications", because the
## chair back, the table pedestal and the floor inlay are now three sizes of
## one path rather than three bitmaps.
##
## The 5's skeleton: in from the top right, along the top, down the shoulder,
## across the waist, down the bowl and back along the foot.
_FIVE_PATH = ((0.60, 0.97), (0.06, 0.97), (0.06, 0.57), (0.40, 0.57),
              (0.58, 0.44), (0.58, 0.16), (0.40, 0.03), (0.06, 0.03))
ROUNDEL_STROKE = 0.23           # ink stroke, as a fraction of the cap height
ROUNDEL_INLINE = 0.075          # the field-coloured line down the middle of it


def five_roundel(d_m=0.36, z=0.0, disc=True):
    """The station's `5` mark. +X across, +Y up, centred on (0, 0), +Z out."""
    m = _M()
    if disc:
        _disc(m, 0.0, 0.0, d_m / 2.0, z, "sign_roundel_field", seg=24)
        # The keyline is an outer ring, drawn as a closed ribbon rather than as
        # a second disc, so it cannot z-fight with the field it sits on.
        r = d_m / 2.0 * 0.94
        pts = [(r * math.cos(2 * math.pi * i / 24), r * math.sin(2 * math.pi * i / 24))
               for i in range(24)]
        _ribbon(m, pts, d_m * 0.035, z + 0.0008, "sign_roundel_ink", close=True)
    cap = d_m * 0.62
    pts = [((x - 0.32) * cap, (y - 0.50) * cap) for x, y in _FIVE_PATH]
    _ribbon(m, pts, ROUNDEL_STROKE * cap, z + 0.0016, "sign_roundel_ink")
    _ribbon(m, pts, ROUNDEL_INLINE * cap, z + 0.0024, "sign_roundel_field")
    return m.as_tuple()


def write_obj(path):
    """Every group this module can emit, in one file.

    NOT just `board_pair()` any more, and that matters for a reason outside
    this module: `station/test_materials_layer3.py::BESPOKE_BUILDERS` reaches
    signage through `write_obj`, so whatever this function does not build is
    invisible to the station's material-coverage gate. It emitted three groups
    of the eleven this module has; a new lettering group could have shipped on
    the glTF default -- white plastic -- and layer 3 would still have read
    503/503.
    """
    import directory as _dr                                    # noqa: PLC0415
    m = _M()

    def add(triple, dx=0.0, dy=0.0):
        v, t, g = triple
        base = len(m.v)
        m.v.extend([(x + dx, y + dy, z) for x, y, z in v])
        m.t.extend([(a + base, b + base, c + base) for a, b, c in t])
        m.g.extend(g)

    add(board_pair())
    # A place with a hazard and one without, so both branches are in the file.
    haz = next((p for p in _dr.PLACES if hazard_of(p)), _dr.PLACES[0])
    add(door_plaque(_dr.PLACES[0]), dx=-3.0, dy=1.6)
    add(door_plaque(haz), dx=-2.2, dy=1.6)
    add(level_plaque(_dr.PLACES[0]), dx=-3.0, dy=2.6)
    add(direction_board(_dr.PLACES[0]), dx=2.4, dy=1.6)
    add(zocalo_wordmark(), dx=-1.2, dy=3.2)
    add(five_roundel(), dx=2.4, dy=3.2)
    it.write_grouped_obj(path, m.v, m.t, m.g)
    return path, len(m.v), len(m.t)


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

    # --- the lettering -----------------------------------------------------
    import directory as _dr                                    # noqa: PLC0415
    import interior_kit as _K                                  # noqa: PLC0415

    bad = [c for c, rows in _FONT.items()
           if len(rows) != GLYPH_H or any(len(r) != GLYPH_W for r in rows)]
    check("every glyph is 5x7", not bad, str(bad))

    # DISTINGUISHABLE. Two glyphs with identical bitmaps read as a permanent
    # typo and are invisible in a render of three words -- 0/O and 8/B are the
    # pairs a blocky face loses first, and this face separates both.
    seen, dupes = {}, []
    for c, rows in _FONT.items():
        if c == " ":
            continue
        k = "".join(rows)
        if k in seen:
            dupes.append((seen[k], c))
        seen[k] = c
    check("no two glyphs are identical", not dupes, str(dupes))

    # THE FACE MUST SPELL EVERYTHING IT IS ASKED TO. A character with no glyph
    # renders as tofu, which is honest but should never ship, so this asserts
    # against the real corpus rather than against a sample.
    need = set()
    for p in _dr.PLACES:
        for line in door_text(p):
            need.update(line)
    for b in BOARDS.values():
        for line in [b["header"], b["badge"], b["title"]] + list(b["lines"]):
            need.update(str(line).upper())
    missing = sorted(need - set(_FONT))
    check("the face covers every character on every sign the station carries",
          not missing, f"missing {missing}")

    # THE MERGE MUST COVER EXACTLY THE LIT CELLS. This is the assertion that
    # matters about `_spans`: a greedy 2-D merge that drops a rectangle loses a
    # stroke, and a letter missing a stroke is another letter. Checked over
    # every glyph, both directions -- no lit cell uncovered, no dark cell
    # covered, and nothing covered twice.
    holes = dupes2 = spill2 = 0
    for c, rows in _FONT.items():
        cover = [[0] * GLYPH_W for _ in range(GLYPH_H)]
        for r0, c0, r1, c1 in _spans(c):
            for r in range(r0, r1):
                for k in range(c0, c1):
                    cover[r][k] += 1
        for r in range(GLYPH_H):
            for k in range(GLYPH_W):
                want = 1 if rows[r][k] == "1" else 0
                if cover[r][k] < want:
                    holes += 1
                elif cover[r][k] > want:
                    (spill2 := spill2 + 1) if want == 0 else None
                    dupes2 += 1 if want else 0
    check("the glyph merge covers exactly the lit cells",
          holes == 0 and dupes2 == 0 and spill2 == 0,
          f"{holes} uncovered, {dupes2} double-covered, {spill2} spilled")

    # And that it is actually a saving, in BOTH directions. Merging rows alone
    # takes `E` from 18 cells to 5; also merging columns takes `L` -- a stem
    # and a foot -- from 11 cells to 2 rectangles rather than 7 rows.
    cells = sum(r.count("1") for rows in _FONT.values() for r in rows)
    rects = sum(len(_spans(c)) for c in _FONT)
    check("the merge is 2-D, not just per row", len(_spans("L")) == 2,
          f"L is {len(_spans('L'))} rectangles")
    check("...and it saves more than half the geometry", rects * 2 < cells,
          f"{cells} lit cells -> {rects} rectangles")

    # Every letter inside its own panel. A sign whose text overruns its frame
    # is worse than a blank one: it reads as a bug rather than as a sign.
    #
    # ASKED PER PLATE, and the widening is a real one rather than a loosening.
    # A door mount is now THREE plates -- the plaque, a LEVEL plate 0.75 m above
    # it and, where the register earns one, a hazard strip below -- so the old
    # test (one rectangle, `abs(y) < PLAQUE_H_M/2`) failed on all 129 the moment
    # the level plate landed, for a reason that was not a defect. Testing the
    # bounding box of the assembly instead would have been the loosening: it
    # cannot see a letter that has left its own plate and landed on the next
    # one. So each plate is bounded by the FIELD IT IS PRINTED ON, found from
    # the geometry rather than from the constants, and a letter is checked
    # against the nearest field. That can still fail, and the control below
    # shows it failing.
    FIELDS = ("sign_field", "sign_field_level", "sign_field_hazard")

    def _stray(v, t, g, pad=1e-6):
        """Lettering vertices that lie on no field of the assembly."""
        boxes = []
        for k, tri in enumerate(t):
            if g[k] in FIELDS:
                xs = [v[i][0] for i in tri]
                ys = [v[i][1] for i in tri]
                boxes.append([min(xs), min(ys), max(xs), max(ys)])
        merged = []
        for bx in boxes:                       # one box per field, not per tri
            for o in merged:
                if (bx[0] <= o[2] + 1e-6 and bx[2] >= o[0] - 1e-6
                        and bx[1] <= o[3] + 1e-6 and bx[3] >= o[1] - 1e-6):
                    o[0], o[1] = min(o[0], bx[0]), min(o[1], bx[1])
                    o[2], o[3] = max(o[2], bx[2]), max(o[3], bx[3])
                    break
            else:
                merged.append(list(bx))
        out = []
        for k, tri in enumerate(t):
            if not g[k].startswith("sign_text"):
                continue
            for i in tri:
                x, y = v[i][0], v[i][1]
                if not any(o[0] - pad <= x <= o[2] + pad
                           and o[1] - pad <= y <= o[3] + pad for o in merged):
                    out.append((round(x, 4), round(y, 4)))
        return out

    check("every letter is inside a field of its own mount",
          not _stray(*door_plaque(_dr.PLACES[0])),
          str(_stray(*door_plaque(_dr.PLACES[0]))[:3]))

    # ...on ALL of them, because the failure is data-driven: one long place
    # name is all it takes and there are 129 of them.
    spill = [p["key"] for p in _dr.PLACES if _stray(*door_plaque(p))]
    check("no plaque on the station overruns its frame", not spill,
          f"{len(spill)} do: {spill[:4]}")
    # THE CONTROL. Widen the lettering past its plate and the check must fire;
    # without this the test above is one that cannot fail, which this file's own
    # standard calls worse than no test.
    bv, bt, bg = door_plaque(_dr.PLACES[0])
    bv = [(x * 1.6, y, z) if g else (x, y, z)
          for (x, y, z), g in zip(bv, [False] * len(bv))]
    wv, wt, wg = door_plaque(_dr.PLACES[0])
    wv = [(x, y, z) for x, y, z in wv]
    tex = {i for k, tri in enumerate(wt) if wg[k].startswith("sign_text")
           for i in tri}
    wv = [(x * 3.0, y, z) if i in tex else (x, y, z)
          for i, (x, y, z) in enumerate(wv)]
    check("...and the containment check fires when lettering leaves its plate",
          bool(_stray(wv, wt, wg)),
          f"{len(_stray(wv, wt, wg))} strays with the text scaled x3")

    # A SIGN NOBODY CAN READ IS SET DRESSING, and legibility is arithmetic
    # rather than taste. A 5x7 lattice needs roughly 7 arc-minutes a CELL to
    # resolve, so the readable distance is cell / tan(7'). Asserting the
    # relationship means a later change to plaque size cannot silently make
    # every sign on the station unreadable.
    caps = []
    for p in _dr.PLACES:
        ls = door_text(p)
        caps.append(fit_cap_m(ls[1:] or ls, PLAQUE_W_M - 0.024))
    worst = min(caps)
    read_m = (worst / GLYPH_H) / math.tan(math.radians(7.0 / 60.0))
    check("the worst plaque on the station is legible from 1.5 m",
          read_m >= 1.5, f"{worst * 1000:.1f} mm caps, readable to {read_m:.2f} m")

    # The board's own words must actually reach the board.
    bv, bt, bg = board_lit("customs_atmosphere")
    n_text = sum(1 for x in bg if x.startswith("sign_text"))
    check("the customs board renders its own transcribed text", n_text > 200,
          f"{n_text} lettering triangles")
    fw, fh = BOARD_W_M - 2 * BOARD_FRAME_M, BOARD_H_M - 2 * BOARD_FRAME_M
    outside = [i for k, tri in enumerate(bt) if bg[k].startswith("sign_text")
               for i in tri
               if abs(bv[i][0]) > fw / 2.0 + 1e-9
               or abs(bv[i][1] - (MOUNT_H_M + BOARD_H_M / 2.0)) > fh / 2.0 + 1e-9]
    check("the board's text stays on its lit face", not outside,
          f"{len(outside)} vertices outside")

    # The body it hangs on is still a closed solid after the lettering is
    # merged in. Lettering is single-sided by construction -- that is what a
    # decal is -- so the check isolates the solid groups, the same way
    # `dressing._selftest` does.
    solid = [bt[k] for k in range(len(bt))
             if bg[k] in ("sign_frame", "sign_face", "sign_post")]
    so, sn = _K.boundary_edges(bv, solid)
    check("the board body is still closed with lettering on it", not so,
          f"{len(so)} open edges")

    # COST, and the bar is stated against something rather than picked. The
    # first version of this check was "under 40,000 triangles for all 118",
    # which is a number with nothing behind it -- it failed at 42,810 and the
    # only honest options were to make the content cheaper or to say what the
    # bar meant. Both, in the end: the 2-D merge took a plaque from 640
    # triangles to 363, and the bar is now two bounds that can each fail for a
    # reason a reader can check.
    each = [len(door_plaque(p)[1]) for p in _dr.PLACES]
    tot = sum(each)
    # 1. THE FACE ITSELF MUST STAY CHEAP PER GLYPH. This replaced a bar that
    #    said "no plaque costs more than the doorway it labels" (500, from
    #    `door_frame` 228 + `bulkhead` 68), and it is worth saying why rather
    #    than quietly moving it: that bar compared a sign to a door frame, and
    #    a sign carries TEXT while a door frame does not. Triangle count here
    #    is character count -- `council_chamber` is 47 characters and 508
    #    triangles no matter how it is laid out -- so the door comparison could
    #    only ever be met by deleting words. The content was already made
    #    right (sign text rather than catalogue text, four-line plaques gone);
    #    what was wrong was the bar. A face property is the thing to bound.
    per_glyph = rects / max(1, len(_FONT) - 1)          # less the space
    check("a glyph averages under 6 rectangles", per_glyph < 6.0,
          f"{per_glyph:.2f} rectangles a glyph over {len(_FONT)} glyphs")
    # 2. AND NO SINGLE SIGN MAY BE A BUDGET EVENT ON THE DECK IT HANGS ON.
    #    `blue/0/0` is 589,216 triangles; 0.1% of it is 589. That bound was
    #    written when a door carried ONE plate and it is kept exactly, applied
    #    to each PLATE -- worst 448, the hazard strip on `waste_green`.
    #
    #    A SECOND BOUND IS OWED BECAUSE A DOOR NOW CARRIES THREE PLATES, and it
    #    is derived rather than picked. The shipped `shot_blue_0_0.obj` carries
    #    16 door mounts per streaming cell (`sign_field_c00` is 192 triangles
    #    and a field is one 12-triangle box). At the measured mean of 495 a
    #    deck spends 1.34% of itself on typography and at the worst mount 2.68%
    #    -- against `dress_conduit` at 2.8% and `light_pilaster_strip` at 7.0%
    #    on that same deck. So a mount is allowed 0.25%, which puts sixteen of
    #    them under 4%: less than the deck already spends on one light fitting,
    #    for the layer a player actually reads. Both quantities are named, so
    #    the bound can fail for a reason a reader can check.
    DECK_TRIS = 589216
    MOUNTS_PER_CELL = 16
    plates = []
    for p in _dr.PLACES:
        plates.append(len(door_plaque(p, level_plate=False, hazard=False)[1]))
        plates.append(len(level_plaque(p)[1]))
        hz = hazard_of(p)
        if hz:
            plates.append(len(hazard_plate(hz)[1]))
    check("no plate is more than 0.1% of the deck it hangs on",
          max(plates) < DECK_TRIS * 0.001,
          f"worst plate {max(plates)} tri against {DECK_TRIS * 0.001:.0f}")
    check("no door mount is more than 0.25% of the deck it hangs on",
          max(each) < DECK_TRIS * 0.0025,
          f"worst {max(each)} tri "
          f"({_dr.PLACES[each.index(max(each))]['key']}) against "
          f"{DECK_TRIS * 0.0025:.0f}")
    deck_share = MOUNTS_PER_CELL * (tot / len(each)) / float(DECK_TRIS)
    worst_share = MOUNTS_PER_CELL * max(each) / float(DECK_TRIS)
    check("a cell's sixteen mounts are under 4% of it", worst_share < 0.04,
          f"{worst_share * 100:.2f}% at the worst mount, "
          f"{deck_share * 100:.2f}% at the mean")
    n_haz = sum(1 for p in _dr.PLACES if hazard_of(p))
    print(f"  {len(_FONT)} glyphs; {tot:,} triangles for {len(_dr.PLACES)} "
          f"door mounts ({tot / len(_dr.PLACES):.0f} each, worst {max(each)}, "
          f"worst plate {max(plates)}), "
          f"caps {worst * 1000:.1f} mm readable to {read_m:.1f} m, "
          f"{deck_share * 100:.2f}% of a deck; {n_haz} hazard legends")
    print(f"  customs board: {len(bt):,} triangles, {n_text:,} of them "
          f"lettering, {len(BOARDS['customs_atmosphere']['lines'])} "
          f"transcribed lines")

    # --- THE ADDRESS IS THE SHOW'S GRAMMAR ---------------------------------
    import re as _re                                            # noqa: PLC0415
    addrs = [address_of(p) for p in _dr.PLACES]
    check("every address is <Colour> <number> and nothing else",
          all(_re.fullmatch(r"(BLUE|RED|GREEN|GREY|BROWN|YELLOW) [1-9]\d*", a)
              for a in addrs),
          str([a for a in addrs
               if not _re.fullmatch(r"[A-Z]+ [1-9]\d*", a)][:3]))
    # The defect this replaced, asserted so it cannot come back by accident: a
    # bearing on a plaque is our coordinate system, not the station's.
    check("no plaque carries a bearing or a ring-deck pair",
          not any(_re.search(r"\d-\d|\b\d{3}\b", ln)
                  for p in _dr.PLACES for ln in door_text(p)),
          str([ln for p in _dr.PLACES for ln in door_text(p)
               if _re.search(r"\d-\d|\b\d{3}\b", ln)][:3]))

    # THE CORROBORATION, AND IT IS THE POINT OF DERIVING THE NUMBER RATHER THAN
    # WRITING ONE DOWN. Nothing about Grey was tuned. The ladder comes out of
    # the hull profile, `interior.DECK_PITCH_M` and the sector's own outermost
    # ring radius, and Grey's occupied levels contain **17**. If a change to the
    # hull, the pitch or the numbering pushed the show's most famous address off
    # this station, this line goes red and says so.
    grey = sorted({level_number(p) for p in _dr.PLACES if p["sector"] == "grey"})
    # ASSERTED AS "REACHES 17", NOT "CONTAINS 17", and the weakening is a
    # correction rather than a retreat. What `Grey 17` establishes at authority
    # 1 is that Grey has AT LEAST seventeen levels -- it does not say a register
    # place sits on the seventeenth. The first version of this line demanded
    # `17 in grey` and went red in the middle of this session when another agent
    # edited `station/schema/station.yaml`: a hull change of a few metres slides
    # every place a rung along the ladder, which moves WHICH levels are
    # occupied without changing HOW MANY exist. The canon claim is about depth,
    # so depth is what is checked, and it still fails if Grey stops being a deep
    # industrial sector.
    check("Grey reaches level 17, which is where the show puts a level",
          max(grey) >= 17, f"grey levels are {grey}")
    span = sorted({(p["sector"], level_number(p)) for p in _dr.PLACES})
    check("the level numbers span a plausible station",
          max(n for _s, n in span) <= 80 and min(n for _s, n in span) >= 1,
          f"{min(n for _s, n in span)}..{max(n for _s, n in span)} "
          f"against on-screen Grey 17 and placard Brown-57")
    for sec in sorted({p["sector"] for p in _dr.PLACES}):
        lv = sorted({level_number(p) for p in _dr.PLACES if p["sector"] == sec})
        print(f"  {SECTOR_LABEL.get(sec, sec):7s} levels {lv}")

    # THE READING IS A SWITCH, NOT AN ASSUMPTION -- C-004 is OPEN and this is
    # what "switchable in one edit" has to mean to be worth anything: flipping
    # it changes every sign, and the test proves it rather than the comment
    # claiming it.
    global LEVEL_READING
    _keep = LEVEL_READING
    try:
        LEVEL_READING = "angular"
        ang = [address_of(p) for p in _dr.PLACES]
        check("switching LEVEL_READING re-addresses the whole station",
              ang != addrs and all(1 <= int(a.split()[1]) <= 36 for a in ang),
              f"{sum(1 for a, b in zip(ang, addrs) if a != b)} of "
              f"{len(addrs)} addresses change; angular range "
              f"{min(int(a.split()[1]) for a in ang)}.."
              f"{max(int(a.split()[1]) for a in ang)}")
    finally:
        LEVEL_READING = _keep
    check("...and the switch is restored", LEVEL_READING == _keep)

    # WHAT A SOURCE CLAIMS, BESIDE WHAT WE DERIVE. Not used, printed, and
    # asserted only in that every attested key is a real place -- a table
    # naming a room that no longer exists is a table nobody is maintaining.
    _known = {q["key"] for q in _dr.PLACES}
    check("every attested address names a place in the register",
          set(ATTESTED_ADDRESS) <= _known,
          str(sorted(set(ATTESTED_ADDRESS) - _known)))
    for k, (_sec, n, _src) in sorted(ATTESTED_ADDRESS.items()):
        q = _dr.by_key(k) if k in _known else None
        if q is not None:
            print(f"  attested {k}: source says {_sec} {n}, we derive "
                  f"{address_of(q)} (delta {level_number(q) - n:+d}) "
                  f"-- authority 4, NOT USED")

    # A CORRIDOR CAN NOW BE ADDRESSED FROM A RADIUS, which is what the kit
    # needs and what it has never had. Asserted here, in the module that owns
    # the grammar, so the one-line change in `interior.ring_arc` has something
    # to call the day it lands rather than a parameter nobody passes.
    schema_, profile_ = _schema()
    r0, _a, _b, _c = it.place_floor_radius(schema_, profile_, _dr.PLACES[0])
    cl = corridor_plate_lines({"sector": _dr.PLACES[0]["sector"],
                               "r_floor_m": r0,
                               "angle_deg": _dr.PLACES[0]["angle_deg"]})
    check("a corridor plate can be addressed from a radius alone",
          len(cl) == 2 and cl[0] == SECTOR_LABEL[_dr.PLACES[0]["sector"]]
          and cl[1].startswith("LEVEL "), str(cl))
    check("...and it agrees with the door plaque on the same deck",
          cl[1].split()[1] == address_of(_dr.PLACES[0]).split()[1],
          f"corridor {cl} against door {address_of(_dr.PLACES[0])!r}")
    # It must MOVE with the radius, or it is a constant dressed as an address.
    up = corridor_plate_lines({"sector": _dr.PLACES[0]["sector"],
                               "r_floor_m": r0 - 5 * it.DECK_PITCH_M,
                               "angle_deg": 0.0})
    check("...and five decks inward reads five levels different",
          abs(int(up[1].split()[1]) - int(cl[1].split()[1])) == 5,
          f"{cl[1]!r} against {up[1]!r}")

    # --- THE LEVEL PLAQUE IS RECESSED, WHICH IS THE WHOLE FIDELITY CLAIM ----
    lv, lt, lg = level_plaque(_dr.PLACES[0])
    fld = [lv[i][2] for k, tri in enumerate(lt)
           if lg[k] == "sign_field_level" for i in tri]
    frm = [lv[i][2] for k, tri in enumerate(lt)
           if lg[k] == "sign_frame" for i in tri]
    txt = [lv[i][2] for k, tri in enumerate(lt)
           if lg[k] == "sign_text_level" for i in tri]
    check("the level plate's field is set BACK inside its frame",
          max(fld) < max(frm) - 1e-6,
          f"field front {max(fld):.4f}, frame face {max(frm):.4f}")
    check("...and the lettering stays inside the rebate rather than on top",
          max(txt) < max(frm) - 1e-6,
          f"letters at {max(txt):.4f}, frame face {max(frm):.4f}")
    check("the level plate is landscape, as the frame shows",
          LEVEL_PLATE_W_M > 2.0 * LEVEL_PLATE_H_M,
          f"{LEVEL_PLATE_W_M} x {LEVEL_PLATE_H_M}")
    check("it is above a standing eye",
          LEVEL_PLATE_CENTRE_H_M - LEVEL_PLATE_H_M / 2.0 >= 1.70,
          f"underside at {LEVEL_PLATE_CENTRE_H_M - LEVEL_PLATE_H_M / 2.0:.3f} m")
    # AND ITS TOP CLEARS THE CORRIDOR'S HEAD CHAMFER, which is the assertion
    # that would have caught the plate being swallowed by the soffit. Both
    # numbers come from `interior_kit.PROVISIONAL`, so a change to the corridor
    # section fails this rather than silently burying every level plate on the
    # station.
    _flat = (_K.PROVISIONAL["ceiling_height_m"]
             - _K.PROVISIONAL["wall_chamfer_m"])
    check("the level plate's top clears the corridor's head chamfer",
          LEVEL_PLATE_CENTRE_H_M + LEVEL_PLATE_H_M / 2.0 <= _flat - 0.05,
          f"plate top {LEVEL_PLATE_CENTRE_H_M + LEVEL_PLATE_H_M / 2.0:.3f} m "
          f"against a flat wall ending at {_flat:.2f} m")
    # THE ONE A RENDER HAD TO FIND, now an assertion. The corridor's clamped
    # services run 1.95-2.55 m above the deck and a plate inside that band is
    # invisible however correct it is.
    check("the level plate is clear of the corridor's high-level services",
          LEVEL_PLATE_CENTRE_H_M + LEVEL_PLATE_H_M / 2.0 <= SERVICE_BAND_M[0],
          f"plate top {LEVEL_PLATE_CENTRE_H_M + LEVEL_PLATE_H_M / 2.0:.3f} m "
          f"against services from {SERVICE_BAND_M[0]:.2f} m")
    check("...and clear of the plaque under it",
          LEVEL_PLATE_CENTRE_H_M - LEVEL_PLATE_H_M / 2.0
          >= PLAQUE_CENTRE_H_M + PLAQUE_H_M / 2.0,
          f"plate bottom {LEVEL_PLATE_CENTRE_H_M - LEVEL_PLATE_H_M / 2.0:.3f} m "
          f"against plaque top {PLAQUE_CENTRE_H_M + PLAQUE_H_M / 2.0:.3f} m")
    check("...and the height is the kit's, not a number this module remembers",
          abs(LEVEL_PLATE_CENTRE_H_M - _level_plate_centre_h()) < 1e-9,
          f"{LEVEL_PLATE_CENTRE_H_M} against {_level_plate_centre_h():.4f}")
    check("it carries the authority-1 word",
          all(level_text(p).startswith("LEVEL ") for p in _dr.PLACES))
    lcaps = min(fit_cap_m([level_text(p)], LEVEL_PLATE_W_M - 0.020)
                for p in _dr.PLACES)
    lread = (lcaps / GLYPH_H) / math.tan(math.radians(7.0 / 60.0))
    check("the level plate is legible from further than the corridor is wide",
          lread > 2.4,
          f"{lcaps * 1000:.1f} mm caps, readable to {lread:.1f} m")
    # AND THE NEGATIVE CONTROL FOR THE WHOLE FEATURE: with the flag off, the
    # station has door plaques and no level plaques, which is exactly what it
    # had before this session.
    off = door_plaque(_dr.PLACES[0], level_plate=False)
    check("with LEVEL_PLATE_ON_DOOR off the level plate is gone",
          "sign_field_level" not in set(off[2])
          and "sign_field_level" in set(door_plaque(_dr.PLACES[0])[2]),
          f"off={sorted(set(off[2]))}")

    # --- WARNING SIGNAGE COMES FROM THE REGISTER ---------------------------
    haz = {p["key"]: hazard_of(p) for p in _dr.PLACES}
    n_h = sum(1 for v in haz.values() if v)
    check("warnings are earned by declaration, not placed by hand",
          0 < n_h < len(_dr.PLACES),
          f"{n_h} of {len(_dr.PLACES)} places declare a hazard")
    # The one a reader can check by name: the Markab quarter is sealed, and
    # `directory.py` says so with a `welded_door`.
    mk = _dr.by_key("markab_quarter")
    check("the sealed Markab quarter is signed as sealed",
          mk is not None and hazard_of(mk) == ("SEALED BY ORDER", "NO ADMITTANCE"),
          str(hazard_of(mk) if mk else None))
    react = [k for k, v in haz.items() if v and v[0] == "RADIATION"]
    check("every reactor-side place is signed for radiation", react,
          str(react[:4]))
    # A WARNING MUST BE READABLE FURTHER AWAY THAN THE THING IT WARNS ABOUT, or
    # it is decoration. Measured off the emitted mesh rather than off the
    # constants -- `letter_mesh` shrinks a block that will not fit, so the cap a
    # caller ASKS for and the cap that ships are different numbers, and this
    # asserts the one that ships. The first hazard plate was 0.085 m tall and
    # the header measured 1.06 m of legibility, which is closer than a body can
    # stand to a wall; 0.130 m puts it past the corridor's own half-width.
    # TWO TIERS, TWO BARS, and separating them is the point rather than a way
    # of passing. A warning plate is a road sign: the HEADING is what you read
    # walking past and it must carry across the corridor; the instruction under
    # it is small print you read standing at the door. One bar over both was
    # the wrong question -- it graded a deliberate hierarchy as a defect.
    def _tiers(v, t, g):
        # CAP HEIGHT PER LINE, NOT RECTANGLE HEIGHT -- and the difference is a
        # factor of seven. `_spans` merges a glyph into rectangles, so the
        # SMALLEST rectangle on a plate is the crossbar of an `E`, one cell
        # tall; a min over rectangles reported the small print at 1.6 mm and
        # "readable to 0.12 m", which measures a crossbar and not a letter.
        #
        # CLUSTERING BY BASELINE DOES NOT WORK EITHER, and that was the second
        # wrong answer: a merged span's bottom edge is wherever its own strokes
        # end, so one line's rectangles have many different bottoms. What IS
        # true of a line is that its rectangles all OVERLAP the band its caps
        # occupy, so the y-intervals are merged by overlap and each merged
        # interval is one line. Its height is that line's cap.
        iv = sorted((min(v[i][1] for i in tri), max(v[i][1] for i in tri))
                    for k2, tri in enumerate(t) if g[k2] == "sign_text_level")
        lines = []
        for lo, hi in iv:
            if lines and lo <= lines[-1][1] + 1e-9:
                lines[-1][1] = max(lines[-1][1], hi)
            else:
                lines.append([lo, hi])
        caps = sorted(hi - lo for lo, hi in lines)
        return caps[-1], caps[0]

    def _read(h):
        return (h / GLYPH_H) / math.tan(math.radians(7.0 / 60.0))

    heads, smalls = [], []
    for _k, _v in haz.items():
        if _v:
            a_, b_ = _tiers(*hazard_plate(_v))
            heads.append(a_)
            smalls.append(b_)
    check("the worst hazard HEADING on the station reads from 1.5 m",
          _read(min(heads)) >= 1.5,
          f"{min(heads) * 1000:.1f} mm stroke, readable to "
          f"{_read(min(heads)):.2f} m")
    check("...and its small print reads at arm's length",
          _read(min(smalls)) >= 0.7,
          f"{min(smalls) * 1000:.1f} mm stroke, readable to "
          f"{_read(min(smalls)):.2f} m")
    # ...and a mess hall is not. A hazard table that fires on everything is a
    # table that says nothing.
    mess = _dr.by_key("mess_hall")
    check("an ordinary room carries no warning",
          mess is not None and hazard_of(mess) is None, str(hazard_of(mess)))

    # --- WAYFINDING ARROWS POINT THE RIGHT WAY -----------------------------
    # Arithmetic on the register's own bearings, so it is checkable: a
    # destination further round in +theta must take the right arrow.
    import directory as _d2                                     # noqa: PLC0415
    wrong = []
    for p in _d2.PLACES:
        here = float(p["angle_deg"]) % 360.0
        for ln in wayfinding_lines(p)[1:]:
            arrow = ln[0]
            for kk in (p.get("adjacent") or ()):
                try:
                    q = _d2.by_key(kk)
                except KeyError:
                    continue
                if q is None:
                    continue
                dd = (float(q["angle_deg"]) - here + 540.0) % 360.0 - 180.0
                want = (ARROW_AHEAD if abs(dd) < 2.0
                        else ARROW_RIGHT if dd > 0 else ARROW_LEFT)
                nm = wrap(q["name"].upper(), 20)
                lab = nm[0] if len(nm) == 1 else str(q["key"]).replace("_", " ").upper()
                if ln[2:] == lab[:20] and arrow != want:
                    wrong.append((p["key"], q["key"], arrow, want))
    check("every wayfinding arrow agrees with the register's bearings",
          not wrong, str(wrong[:3]))
    check("the arrows are in the face",
          all(c in _FONT for c in (ARROW_LEFT, ARROW_RIGHT, ARROW_AHEAD)))
    dv, dt, dg = direction_board(_dr.PLACES[0])
    check("a direction board renders lettering",
          sum(1 for x in dg if x.startswith("sign_text")) > 40,
          f"{sum(1 for x in dg if x.startswith('sign_text'))} lettering tris")

    # --- THE WORDMARK AND THE ROUNDEL --------------------------------------
    wv, wt, wg = zocalo_wordmark(WORDMARK_CAP_M)
    ww, wh = wordmark_extent_m(WORDMARK_CAP_M)
    check("the wordmark is one group of tube, not a rectangle",
          set(wg) == {"sign_wordmark"} and len(wt) > 200,
          f"{len(wt)} triangles in {sorted(set(wg))}")
    check("the wordmark fits the board zocalo.neon_sign builds",
          ww <= 1.9 - 0.12 and wh <= 0.84 - 0.12,
          f"{ww:.2f} x {wh:.2f} m in a 1.90 x 0.84 m board")
    # It is a SCRIPT and not a lattice: no glyph in it may coincide with the
    # 5x7 face, which is the whole reason it is authored as paths.
    xs = [q[0] for q in wv]
    ys = [q[1] for q in wv]
    check("the wordmark is a baseline-relative script with a descender",
          min(ys) < -0.02 and max(ys) > 0.90 * WORDMARK_CAP_M,
          f"y {min(ys):.3f}..{max(ys):.3f} at cap {WORDMARK_CAP_M}")
    check("...and it runs left to right without gaps",
          max(xs) - min(xs) > 3.0 * WORDMARK_CAP_M,
          f"{max(xs) - min(xs):.2f} m across")
    rv, rt, rg = five_roundel()
    check("the roundel has a field, an ink glyph and an inline",
          {"sign_roundel_field", "sign_roundel_ink"} == set(rg)
          and len(rt) > 60, f"{sorted(set(rg))}, {len(rt)} tris")
    ink = [rv[i][2] for k, tri in enumerate(rt)
           if rg[k] == "sign_roundel_ink" for i in tri]
    inl = [rv[i][2] for k, tri in enumerate(rt)
           if rg[k] == "sign_roundel_field" for i in tri]
    check("the inline sits proud of the ink it is cut out of",
          max(inl) > max(ink) - 1e-9,
          f"inline z {max(inl):.4f}, ink z {max(ink):.4f}")

    # --- EVERY GROUP THIS MODULE EMITS IS INSIDE THE MATERIAL GATE ---------
    # `test_materials_layer3.BESPOKE_BUILDERS` reaches signage through
    # `write_obj` alone, so a group `write_obj` does not build is a group the
    # station's material coverage cannot see. This asserts the two agree.
    import tempfile as _tf, os as _os                            # noqa: PLC0415
    fd, tmp = _tf.mkstemp(suffix=".obj")
    _os.close(fd)
    try:
        write_obj(tmp)
        emitted = {ln[2:].strip() for ln in open(tmp, encoding="utf-8")
                   if ln.startswith("g ")}
    finally:
        _os.unlink(tmp)
    reachable = set()
    for f in (board_pair(), board_lit("customs_atmosphere"),
              arrivals_board(), notice_board(),
              door_plaque(_dr.PLACES[0]), door_plaque(haz_place := next(
                  (p for p in _dr.PLACES if hazard_of(p)), _dr.PLACES[0])),
              level_plaque(_dr.PLACES[0]), direction_board(_dr.PLACES[0]),
              zocalo_wordmark(), five_roundel()):
        reachable |= set(f[2])
    check("write_obj emits every group this module can build",
          not (reachable - emitted), str(sorted(reachable - emitted)))
    import materials as _mt                                      # noqa: PLC0415
    unbound = sorted(g for g in reachable if _mt.resolve_any(g) is None)
    check("every group this module emits has a material", not unbound,
          str(unbound))
    print(f"  groups: {len(reachable)}; wordmark {len(wt)} tri, "
          f"roundel {len(rt)} tri, direction board {len(dt)} tri")

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
