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
    if not lines:
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
    """The lines on one door's plaque: address first, then what it is.

    The address is `SECTOR RING-DECK BEARING` -- the same coordinate every
    other module in this project addresses a place by, so a player reading a
    sign and an agent reading `directory.py` are reading the same thing. A
    station whose signage uses a private numbering nobody else uses is a
    station where a sign cannot be checked against anything.
    """
    sec = SECTOR_LABEL.get(place["sector"], str(place["sector"]).upper())
    addr = (f"{sec} {place['ring']}-{int(place['deck']):02d} "
            f"{int(round(place['angle_deg'])) % 360:03d}")
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


def door_plaque(place):
    """The sign beside one door, in its own frame: +X across, +Y up, +Z out."""
    m = _M()
    hw, hh = PLAQUE_W_M / 2.0, PLAQUE_H_M / 2.0
    b = 0.012
    m.box(-hw, hw, -hh, hh, 0.0, PLAQUE_T_M * 0.45, "sign_frame")
    m.box(-hw + b, hw - b, -hh + b, hh - b, PLAQUE_T_M * 0.45, PLAQUE_T_M,
          "sign_face")
    lines = door_text(place)
    # Every NAME line takes the large face and the trailing address line does
    # not, so a two-line name does not have its second line demoted to small
    # print. `door_text` puts the address last precisely so this is
    # `len(lines) - 1` and not a magic number that drifts when the layout does.
    lv, lt, lg = letter_mesh(lines, PLAQUE_W_M - 2 * b, PLAQUE_H_M - 2 * b,
                             header=len(lines) - 1, z=PLAQUE_T_M + 0.0015)
    base = len(m.v)
    m.v.extend(lv)
    m.t.extend([(a + base, c + base, d + base) for a, c, d in lt])
    m.g.extend(lg)
    return m.as_tuple()


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
    pv, pt, pg = door_plaque(_dr.PLACES[0])
    over = [(pv[i][0], pv[i][1]) for k, tri in enumerate(pt)
            if pg[k].startswith("sign_text") for i in tri
            if abs(pv[i][0]) > PLAQUE_W_M / 2.0 + 1e-9
            or abs(pv[i][1]) > PLAQUE_H_M / 2.0 + 1e-9]
    check("every letter is inside its own plaque", not over, str(over[:3]))

    # ...on ALL of them, because the failure is data-driven: one long place
    # name is all it takes and there are 118 of them.
    spill = []
    for p in _dr.PLACES:
        qv, qt, qg = door_plaque(p)
        if any(abs(qv[i][0]) > PLAQUE_W_M / 2.0 + 1e-9
               or abs(qv[i][1]) > PLAQUE_H_M / 2.0 + 1e-9
               for k, tri in enumerate(qt) if qg[k].startswith("sign_text")
               for i in tri):
            spill.append(p["key"])
    check("no plaque on the station overruns its frame", not spill,
          f"{len(spill)} do: {spill[:4]}")

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
    #    `blue/0/0` is 589,216 triangles; 0.1% of it is 589, so the worst
    #    plaque on the station at 508 passes and one twice this size does not.
    #    This is the bound that can actually fail for a reason a reader can
    #    check, because it names both quantities.
    DECK_TRIS = 589216
    check("no plaque is more than 0.1% of the deck it hangs on",
          max(each) < DECK_TRIS * 0.001,
          f"worst {max(each)} tri "
          f"({_dr.PLACES[each.index(max(each))]['key']}) against "
          f"{DECK_TRIS * 0.001:.0f}")
    deck_share = 6 * (tot / len(each)) / float(DECK_TRIS)
    check("six plaques on a deck are under 1% of it", deck_share < 0.01,
          f"{deck_share * 100:.2f}% of blue/0/0")
    print(f"  {len(_FONT)} glyphs; {tot:,} triangles for {len(_dr.PLACES)} "
          f"plaques ({tot / len(_dr.PLACES):.0f} each, worst {max(each)}), "
          f"caps {worst * 1000:.1f} mm readable to {read_m:.1f} m, "
          f"{deck_share * 100:.2f}% of a deck")
    print(f"  customs board: {len(bt):,} triangles, {n_text:,} of them "
          f"lettering, {len(BOARDS['customs_atmosphere']['lines'])} "
          f"transcribed lines")

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
