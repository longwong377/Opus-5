"""The information layer: what the station is saying, and who can hear it.

CLAUDE.md's scope asks for *"an information layer the player can use — comms,
ISN, propaganda, signage, announcements"*. Four of those five did not exist.
`station/signage.py` builds the boards and their lettering — the station's
written voice, and it is good — but nothing generated a single **spoken** word,
a bulletin, or a notice.

DERIVED, NOT WRITTEN, and that is the whole design
---------------------------------------------------
An announcement here is not a line of dialogue someone typed. It is a **view of
a simulation that already exists**:

  * an arrival call names the ship `station/traffic.py` actually berthed, at the
    hour it actually berthed, in the tier it actually berthed in
  * a customs call fires when `traffic.hall_rate` says a hall is surging, which
    on a liner day is 8.5 people a minute against a 0.28 background
  * a watch call fires at the shift boundaries `npc/schedule.py` already rotates
    security through
  * a Ministry of Peace notice exists **only after `costume.ERA_EVENTS` says
    Nightwatch has surfaced** — S2E22, *The Fall of Night*. At the S3E05 datum
    it is on; render the same station at S2E01 and it is gone

So the information layer cannot drift from the station, because it has no
content of its own to drift with. A future session that changes the manifest
changes what the tannoy says, without touching this file.

THE BUILD NOTE THAT GOVERNS THE PROPAGANDA, and it is FACTIONS.md 11.5's own
-----------------------------------------------------------------------------
    "At the datum the propaganda layer is THREE SURFACES: ISN on public
     screens, Ministry of Peace notices, and Nightwatch recruitment. They
     should read as OFFICIAL AND REASONABLE -- clean typography in the same
     register as the customs boards -- because that is what makes them
     sinister. Do not make them look like villain posters."

Every line below is written to that instruction. The register is the customs
board's: `reference/01-station-exterior/welcome to babylon 5.webp` gives
*"FOLLOW ALL CUSTOMS PROCEDURES"* and *"TIME ON B-5 IS EARTH MEAN TIME (EMT)"*
at authority 1, and that flat civic voice is the one the Ministry borrows.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:                                    # pragma: no cover
    sys.path.insert(0, _HERE)

import directory as dr                                         # noqa: E402
import traffic as tf                                           # noqa: E402
from npc import costume as cos                                 # noqa: E402
from npc import schedule as sched                              # noqa: E402

GAZETTEER = os.path.join(os.path.dirname(_HERE), "docs", "gazetteer",
                         "FACTIONS.md")

# ===========================================================================
# 1.  Where a voice reaches
# ===========================================================================

# THE STATION TALKS IN PUBLIC AND NOT IN YOUR QUARTERS. A tannoy that reaches
# every room on the station is a tannoy nobody can get away from, and the
# owner's scope asks for isolation as well as crowding -- so the public address
# is scoped to the places a port announcement is FOR. Each is a register key.
PA_PLACES = ("arrival_concourse", "customs_north", "customs_south",
             "docking_bays", "bay_elevators", "zocalo", "transfer_systems",
             "cargo_bays")

# BabCom public terminals. FACTIONS.md 11.5, authority 4: "Public terminals in
# passenger lounges and the Zocalo; better quarters have BabCom and datanet
# terminals." So the Zocalo and the arrival concourse are STATED, and the
# command-grade quarters follow from the same sentence.
BABCOM_PLACES = ("zocalo", "arrival_concourse", "business_center",
                 "qtr_command", "ambassadorial_suites")

# ISN on public screens. The in-repo anchor is authority 1 and it is precise:
# the arrival concourse carries a WALL MONITOR SHOWING A TALKING HEAD -- a news
# screen, on screen, in the customs area
# (`reference/11-props-and-technology/babylon 5 welcome sign, instructions, and
# hub.jpg`). Everything else here is that surface repeated where a crowd stands.
ISN_PLACES = ("arrival_concourse", "customs_north", "customs_south",
              "zocalo", "mess_hall", "fresh_air")

# Ministry of Peace notices go where people queue and are processed --
# FACTIONS.md 13 proposes "public reporting terminals in the Zocalo and both
# customs halls" for the Nightwatch reporting terminal, and a notice belongs
# wherever the terminal does.
MINIPAX_PLACES = ("customs_north", "customs_south", "zocalo",
                  "arrival_concourse")

# ===========================================================================
# 2.  The voice
# ===========================================================================

# The customs board's own register, authority 1, from
# `reference/01-station-exterior/welcome to babylon 5.webp`. Kept verbatim
# because it is the tuning fork every invented line below is written against.
BOARD_VOICE = (
    "FOLLOW ALL CUSTOMS PROCEDURES",
    "TIME ON B-5 IS EARTH MEAN TIME (EMT)",
)

# How a ship type is called. The names are the manifest's; the phrasing is
# authority 5 and deliberately flat -- a port tannoy is a civil servant, not a
# narrator. "Delta Gamma 9" and "United Spaceways" are authority 4 (the type
# named in the pilot's docking sequence and its stated operator) and are the
# only proper nouns here that come from a source.
SHIP_CALL = {
    "freighter_bay": "Achilles-type freighter",
    "transport": "United Spaceways transport",
    "shuttle": "in-system shuttle",
    "freighter_standoff": "standoff-class freighter",
    "diplomatic": "diplomatic vessel",
    "liner": "Asimov-class liner",
    "ef_transport": "EarthForce personnel transport",
    "ef_warship": "EarthForce vessel",
    "alien_warship": "visiting patrol vessel",
    # SPEC-CHANGE #3: the fuel carrier. Named plainly rather than with an
    # invented class name (auth 5) -- the register's other alien and utility
    # hulls take descriptive calls for the same reason.
    "tanker": "fuel tanker",
}

# A liner's passengers clear customs over 90 minutes (traffic.hall_rate uses
# the same window), and the hall is told to expect them a quarter-hour out.
LINER_WARNING_H = 0.25

# The escalation ladder's rung 6 -- LAW-CRIME-DOWNBELOW.md 2.4: the external
# sensor arrays turned inward are "the station's one whole-volume search
# capability ... a superb scripted-event mechanic: a station-wide sweep the
# player can feel, ANNOUNCED OVER THE PUBLIC ADDRESS". Not on a schedule: it is
# an event, and this module can produce the line when something asks for it.
SENSOR_SWEEP = ("ATTENTION. Station sensors are being recalibrated for an "
                "internal scan. Remain in your quarters or place of business "
                "until the scan is complete.")


def _era_on(event: str, datum=None) -> bool:
    """Is `event` in force at the datum? `costume.era_active` is the authority.

    DELEGATED for the reason INV-240 records about the armband: a second era
    clock is a second description of one fact, and the one that reaches a frame
    wins. `costume.py` already refuses to dress an S2E01 officer in a Nightwatch
    band; the tannoy must agree with the sleeve.
    """
    return cos.era_active(event, datum or cos.ERA_DATUM)


# ===========================================================================
# 3.  What is being said
# ===========================================================================

def port_calls(day: int = 0) -> list:
    """Every arrival and departure call for one station day.

    Derived from `traffic.arrivals(day)` -- so the tannoy names the ship that
    berthed, in the tier it berthed in, at the hour it berthed. A liner also
    gets a warning call a quarter-hour ahead, because a hall about to take 8.5
    people a minute is told first.
    """
    out = []
    for i, a in enumerate(tf.arrivals(day)):
        what = SHIP_CALL.get(a["type"], a["type"])
        where = ("docking_bays" if a["berth"] == "bay"
                 else "transfer_systems" if a["berth"] == "standoff"
                 else None)
        if a["type"] == "liner":
            out.append({
                "hour": (a["hour"] - LINER_WARNING_H) % 24.0, "kind": "port",
                "places": ("customs_north", "customs_south",
                           "arrival_concourse"),
                "text": LINER_ADVISORY.format(what=what,
                                              souls=a["souls"]),
                "source": "traffic.arrivals + TRAFFIC-AND-CUSTOMS 5.2",
            })
        out.append({
            "hour": a["hour"], "kind": "port", "places": PA_PLACES,
            "text": ship_call(a["type"], "arrival"),
            "source": f"traffic.arrivals({day})[{i}] -> "
                      f"SHIP_CALLS[{a['type']!r}] arrival",
        })
        # THE BOARDING CALL IS THE ONE A PLAYER CAN ACT ON. It goes out a
        # quarter-hour before she breaks moorage, in the bay the hull is
        # actually in, and it is the third of DLG-04's three call types.
        out.append({
            "hour": (a["hour"] + a["stay_h"] - LINER_WARNING_H) % 24.0,
            "kind": "port",
            "places": ("docking_bays", "bay_elevators", "cargo_bays",
                       "transfer_systems"),
            "text": ship_call(a["type"], "boarding"),
            "source": f"traffic.arrivals({day})[{i}] + stay_h - "
                      f"{LINER_WARNING_H:.2f} h",
        })
        # And it leaves again. A port whose ships only arrive fills up.
        out.append({
            "hour": (a["hour"] + a["stay_h"]) % 24.0, "kind": "port",
            "places": ("docking_bays", "bay_elevators", "cargo_bays"),
            "text": ship_call(a["type"], "departure"),
            "source": f"traffic.arrivals({day})[{i}] + stay_h",
        })
    return out


def watch_calls() -> list:
    """Shift changes, from `schedule`'s own rotation rather than a new clock."""
    out = []
    for h, name in ((0.0, "A"), (8.0, "B"), (16.0, "C")):
        out.append({
            "hour": h, "kind": "watch", "places": PA_PLACES,
            "text": WATCH_CALL[name].format(
                n=sched.role_on_duty("security", h)),
            "source": "npc/schedule.role_on_duty + "
                      "LAW-CRIME-DOWNBELOW 2.2's three-shift table",
        })
    return out


def civic_calls() -> list:
    """The station's standing instructions -- the customs board, spoken.

    Authority 1 text, repeated. It is the one part of this module that is not
    invented at all, and it is here so the invented lines above and the notices
    below have something to sit beside in the same register.
    """
    return [{"hour": h, "kind": "civic", "places": MINIPAX_PLACES,
             "text": t, "source": "reference/01-station-exterior/"
                                  "welcome to babylon 5.webp, authority 1"}
            for h, t in zip((6.0, 14.0), BOARD_VOICE)]


# ISN bulletins, era-locked. Each is tied to an event in `costume.ERA_EVENTS`,
# so the bulletin list at a given datum is a FUNCTION of the datum rather than
# a list somebody maintained. The tone is FACTIONS.md 11.5's: ISN "initially
# genuine journalism; after Clark's consolidation it becomes a propaganda organ
# defending the government's xenophobic policies and attacking dissidents", so
# the later ones are drier and more official, not shriller.
# THE ROTATION IS THE CONTENT, NOT A DECORATION. A newsfeed screen in a
# concourse is on for the whole watch and a player stands under it for several
# minutes, so ONE string per story is the thing that reads as a placeholder --
# the same defect a repeated tertiary greeble is, in text. DLG-04 asks for
# 5 bulletins x 3 rotation variants, and the three are written as a REAL
# rotation rather than three paraphrases: the lead, the follow-up with the
# detail a bulletin adds an hour later, and the official reaction. Which one is
# on screen is `(hour + day)` -- see `isn_bulletins`. INV-690.
ISN_ROTATION = {
    "markab_extinct": (
        "ISN. Earth Alliance medical authorities confirm no surviving Markab "
        "population. Quarantine protocols aboard commercial stations remain "
        "in force.",
        "ISN. The Markab quarter aboard Babylon 5 remains sealed pending "
        "medical clearance. Xenobiology teams say the sealing is procedural "
        "and there is no continuing risk to other species.",
        "ISN. A memorial motion was laid before the Earth Alliance Senate "
        "today. A spokesman confirmed the Markab consular accounts will be "
        "held in trust against claimants.",
    ),
    "narn_surrender": (
        "ISN. The Narn Regime has accepted terms. The Earth Alliance restates "
        "its neutrality and urges nationals in former Narn space to register "
        "with the nearest consulate.",
        "ISN. Centauri administration of the Narn homeworld begins this week. "
        "Commercial shipping to the former Regime is suspended until further "
        "notice; carriers are advised to reroute through Ragesh Three.",
        "ISN. The Centauri Republic has thanked the Earth Alliance for what "
        "its ambassador called, quote, a properly neutral posture throughout "
        "the conflict.",
    ),
    "nightwatch_visible": (
        "ISN. The Ministry of Peace reports continued public support for the "
        "Nightwatch programme. A spokesman described participation as, quote, "
        "an ordinary civic duty.",
        "ISN. Nightwatch enrolment aboard Earth Alliance stations has passed "
        "one in three of security personnel. The Ministry stresses that "
        "enrolment is voluntary and carries a supplementary allowance.",
        "ISN. Asked about reports of pressure on officers who have not "
        "enrolled, a Ministry of Peace spokesman said the reports were, "
        "quote, without foundation, and declined further questions.",
    ),
    "rangers_visible": (
        "ISN. Earth Alliance security services are reviewing reports of an "
        "unregistered organisation operating along the rim. Citizens are "
        "asked to report unusual activity.",
        "ISN. The organisation is said to identify itself by a badge rather "
        "than a registry. Station authorities remind travellers that an "
        "unregistered courier carries no legal standing under Alliance law.",
        "ISN. A Ministry of Peace statement described the reports as a matter "
        "for internal security and confirmed no arrests have been made.",
    ),
    "martial_law": (
        "ISN. Emergency measures remain in effect. Normal commercial traffic "
        "is unaffected.",
        "ISN. Under the emergency measures, station commanders hold summary "
        "authority over movement and assembly. Travellers are advised to "
        "carry identification at all times.",
        "ISN. The President's office says the measures are temporary and will "
        "be reviewed. No date for review has been given.",
    ),
}

# The five stories, one row each, in event order -- DERIVED from the rotation
# above so there is no second copy of a string. `ISN_BULLETINS` is the shape
# every existing caller reads and the shape DLG-04's arithmetic counts.
ISN_BULLETINS = tuple((ev, v[0]) for ev, v in ISN_ROTATION.items())

# Ministry of Peace notices. FACTIONS.md 5: a paramilitary division of MiniPax,
# set up under President Clark in 2259, whose stated purpose is "internal
# security and safety" and whose actual function is a propaganda instrument
# where "dissent is relabelled treason". The notices are written to the STATED
# purpose in the customs board's own voice, which is the build note's whole
# point -- an official, reasonable surface is what makes it sinister.
MINIPAX_ROTATION = (
    ("MINISTRY OF PEACE. Report suspicious activity at any station terminal. "
     "Your cooperation protects your neighbours.",
     "MINISTRY OF PEACE. A report costs you nothing and may cost a stranger "
     "very little. Terminals are available in every public concourse."),
    ("MINISTRY OF PEACE. Nightwatch is now recruiting. Enquire at any station "
     "house. A supplementary allowance is payable.",
     "MINISTRY OF PEACE. Nightwatch enrolment is open to all station "
     "residents in good standing. No previous service is required."),
    ("MINISTRY OF PEACE. Loyalty is the ordinary condition of a citizen. "
     "Reports may be filed anonymously.",
     "MINISTRY OF PEACE. Those with nothing to conceal have nothing to "
     "explain. Anonymity is guaranteed to every reporting citizen."),
)

MINIPAX_NOTICES = tuple(v[0] for v in MINIPAX_ROTATION)


# ===========================================================================
# 3b.  THE REST OF DLG-04 -- three call types, the watch, the scene set and
#      the rumour matrix
# ===========================================================================
#
# WHY THIS EXISTS AS CONTENT AND NOT AS ONE PARAMETERISED SENTENCE. The module
# used to announce every hull with one arrival string and one departure string
# and substitute the class name into both -- so a fuel tanker standing off at
# forty kilometres and an Asimov liner discharging eight hundred people through
# the customs hall were the same announcement with a different noun in it. A
# player who stands in the concourse for one station-day hears fifty-one port
# calls (`traffic.arrivals` at the datum), and two phrasings across fifty-one
# calls is the audible equivalent of the tiling seam the eye can index.
#
# So the three call types are the three things a port actually says about a
# hull, and each class says them in its own terms:
#
#   arrival   -- she is here, and where. A bay hull names its tier; a standoff
#                hull names the lighterage that has to go out to her.
#   departure -- she is going, and what that closes.
#   boarding  -- the call that only matters to somebody who has to BE on her:
#                passengers, crew, a work gang, a customs party.
#
# 10 classes x 3 = 30, which is DLG-04's PA figure. The class list is
# `traffic.MANIFEST`'s and the selftest asserts the two agree, so a class added
# to the manifest cannot leave a hole here. Authority 5 throughout; the
# register is the customs board's (authority 1) as everywhere else in this
# file. INV-691.
SHIP_CALLS = {
    "freighter_bay": (
        "ACHILLES-TYPE FREIGHTER NOW ARRIVING, docking bays. Bay crews to "
        "grapple stations.",
        "ACHILLES-TYPE FREIGHTER DEPARTING. Grapples clear, bay doors "
        "closing.",
        "Cargo detail for the Achilles-type freighter, report to the bay "
        "gallery. Manifests to the quartermaster before you go up.",
    ),
    "transport": (
        "UNITED SPACEWAYS TRANSPORT NOW ARRIVING, docking bays. Passengers "
        "to customs on disembarkation.",
        "UNITED SPACEWAYS TRANSPORT DEPARTING. Bay doors closing.",
        "Final call, United Spaceways transport. Ticketed passengers to the "
        "bay elevators with identicards in hand.",
    ),
    "shuttle": (
        "IN-SYSTEM SHUTTLE NOW ARRIVING, docking bays.",
        "IN-SYSTEM SHUTTLE DEPARTING. Bay doors closing.",
        "Shuttle boarding at the bay elevators. Hand baggage only; no cargo "
        "will be carried.",
    ),
    "freighter_standoff": (
        "STANDOFF-CLASS FREIGHTER ARRIVED AND STANDING OFF. Lighterage to be "
        "arranged through the cargo desk.",
        "STANDOFF-CLASS FREIGHTER DEPARTING. All lighters to be recovered "
        "before she breaks moorage.",
        "Lighter crews for the standoff freighter, muster at transfer "
        "systems. Suits and tethers checked at the lock.",
    ),
    "tanker": (
        "FUEL TANKER ARRIVED AND STANDING OFF. No transfer until the "
        "guard boat reports on station.",
        "FUEL TANKER DEPARTING. Transfer lines purged and stowed.",
        "Transfer party for the fuel tanker, report to transfer systems. "
        "No open work in the transfer corridor while she is connected.",
    ),
    "diplomatic": (
        "DIPLOMATIC VESSEL ARRIVED AND STANDING OFF. Reception party to the "
        "diplomatic wing.",
        "DIPLOMATIC VESSEL DEPARTING. The wing is closed to visitors until "
        "she is clear.",
        "The diplomatic party will embark from the transfer lock. The "
        "concourse route is closed for the next quarter-hour.",
    ),
    "liner": (
        "ASIMOV-CLASS LINER NOW ARRIVING, docking bays. Arriving passengers "
        "to customs.",
        "ASIMOV-CLASS LINER DEPARTING. Bay doors closing.",
        "Final call, Asimov-class liner. Passengers with cleared papers to "
        "the bay elevators. Uncleared passengers remain in the hall.",
    ),
    "ef_transport": (
        "EARTHFORCE PERSONNEL TRANSPORT NOW ARRIVING, docking bays. Station "
        "personnel to receive.",
        "EARTHFORCE PERSONNEL TRANSPORT DEPARTING. Bay doors closing.",
        "Drafted personnel for the EarthForce transport, muster at the bay "
        "gallery with orders and kit.",
    ),
    "ef_warship": (
        "EARTHFORCE VESSEL MOORED. Station traffic to keep the moorage "
        "approach clear.",
        "EARTHFORCE VESSEL UNMOORING. Approach lanes closed until she is "
        "under way.",
        "Liberty party for the EarthForce vessel returns at the change of "
        "the watch. Shore leave passes to be shown at the lock.",
    ),
    "alien_warship": (
        "VISITING PATROL VESSEL MOORED. Her crew are guests of the station "
        "and hold no authority aboard.",
        "VISITING PATROL VESSEL UNMOORING. Approach lanes closed.",
        "The visiting patrol vessel recalls her crew at the change of the "
        "watch. Station security will escort to the moorage lock.",
    ),
}

CALL_TYPES = ("arrival", "departure", "boarding")

# The watch call, one per watch, and each one says what that watch INHERITS --
# LAW-CRIME-DOWNBELOW 2.2's three-shift table read as three different jobs
# rather than as one string with a letter substituted into it. A is the watch
# that holds the station while it sleeps; B is the one that meets the traffic;
# C is the one that takes the Zocalo at closing.
WATCH_CALL = {
    "A": ("A WATCH. All personnel report to duty stations. {n} security on "
          "watch. Downbelow boundary patrols to be walked hourly until "
          "oh-eight-hundred."),
    "B": ("B WATCH. All personnel report to duty stations. {n} security on "
          "watch. Customs positions to be manned for the day's arrivals."),
    "C": ("C WATCH. All personnel report to duty stations. {n} security on "
          "watch. Zocalo and licensed premises to be cleared at closing."),
}

# The liner customs advisory, named because DLG-04 counts it as one template
# and it was previously an f-string inside `port_calls` where nothing could
# count it.
LINER_ADVISORY = ("CUSTOMS ADVISORY. {what} arriving in fifteen minutes with "
                  "{souls} passengers. All processing positions to be manned.")

# ---------------------------------------------------------------------------
# THE DENUNCIATION SCENE. FACTIONS.md 5's Nightwatch is a propaganda instrument
# in which "dissent is relabelled treason", and DLG-04 asks for the scene set
# as CONTENT rather than as a mood: eight lines that play out one questioning
# in a public corridor, which is the form the show gives it -- it happens where
# people are, and the crowd's job is to not be involved.
#
# The eight are ordered as the scene plays: the approach, the demand, the
# denouncer, the accusation, the defence, the crowd, the disposal, the aftermath.
# `speaker` says who says it, so the runtime can put the line in the right
# mouth instead of on the tannoy. Authority 5. INV-692.
DENUNCIATION = (
    ("nightwatch", "A word. Station business. You needn't stop what you are "
                   "doing -- just answer where you are."),
    ("nightwatch", "Identicard. And your business at this hour, in your own "
                   "words, if you would."),
    ("informant", "That's him. That's the one I filed on. He said it twice "
                  "and the second time there were four of us stood there."),
    ("nightwatch", "It is reported that you spoke against the Ministry in a "
                   "public place. Do you say the report is false?"),
    ("accused", "I said the docks were being run badly. That is not the same "
                "sentence and you know it is not."),
    ("bystander", "Nobody here saw anything. We were none of us stood close "
                  "enough to hear a word of it."),
    ("nightwatch", "You will present yourself at the station house at the "
                   "change of the watch. Do not make me come and find you."),
    ("bystander", "Get on. Look at your boots and get on. It is not your "
                  "turn today."),
)

# ---------------------------------------------------------------------------
# THE ERA RUMOUR MATRIX -- 8 ERA_EVENTS x 4 speaker classes = 32.
#
# WHY FOUR CLASSES AND NOT FIFTEEN SPECIES. What changes when the news is the
# same and the mouth is different is not the SPECIES, it is what the speaker
# stands to lose by it, and the station sorts that four ways: the office that
# has to administer it, the trade that has to price it, the people below who
# find out last and pay first, and the non-human resident for whom an Earth
# Alliance emergency is somebody else's emergency happening to them. Species
# register is applied on top by `dialogue._SPECIES_VOICE`; doing it twice would
# be two descriptions of one fact.
#
# Every row is era-locked through `costume.ERA_EVENTS` -- the SAME clock as the
# armband and the ISN screen (INV-240), so a rumour cannot circulate before its
# event. Authority 5. INV-693.
RUMOUR_SPEAKERS = ("official", "trader", "downbelow", "alien")

ERA_RUMOUR = {
    ("markab_extinct", "official"):
        "The quarter is sealed and it stays sealed. That is a medical order "
        "and I do not have the authority to lift it.",
    ("markab_extinct", "trader"):
        "Three of my standing orders were Markab. Nobody has told me who I "
        "invoice now, and nobody is going to.",
    ("markab_extinct", "downbelow"):
        "There are empty quarters up there with the air still running and "
        "they would rather seal them than let us in.",
    ("markab_extinct", "alien"):
        "An entire people, aboard this station, and it took eleven days. Do "
        "not ask me to find a lesson in it.",
    ("psi_resident_ends", "official"):
        "The resident telepath's posting is closed. Requests go to Earthdome "
        "now, and Earthdome is not quick.",
    ("psi_resident_ends", "trader"):
        "No commercial scan aboard for the moment. Every contract on this "
        "level is being signed on somebody's word.",
    ("psi_resident_ends", "downbelow"):
        "The reader's gone. That is the first good news down here in a year "
        "and nobody up there thinks so.",
    ("psi_resident_ends", "alien"):
        "The Corps kept one of theirs here and now it does not. I am told to "
        "read nothing into that. I read something into it.",
    ("narn_surrender", "official"):
        "The Regime's registry is void. Every Narn-flagged hull in the "
        "berth-map is a stateless hull and I have no procedure for it.",
    ("narn_surrender", "trader"):
        "The Narn lines are gone. Everything that came up that route now "
        "comes through Centauri hands and it comes at Centauri prices.",
    ("narn_surrender", "downbelow"):
        "There will be another thousand of them down here by the month's end "
        "and there was no room for the last thousand.",
    ("narn_surrender", "alien"):
        "They have terms. Terms are what you are given when you have nothing "
        "left to give in return.",
    ("nightwatch_visible", "official"):
        "One in three of my officers now wears it. I sign the same duty roster "
        "and I no longer know who is reading it.",
    ("nightwatch_visible", "trader"):
        "I keep my opinions behind the counter with the takings. Both are "
        "safer there.",
    ("nightwatch_visible", "downbelow"):
        "They pay for a report. Down here that is a week's food for a name, "
        "and there are names for sale.",
    ("nightwatch_visible", "alien"):
        "It is a human arrangement, in a human corridor, and it will be at my "
        "door within the year.",
    ("rangers_visible", "official"):
        "Unregistered couriers, moving without a filed route. I am asked to "
        "report them and not asked what they are.",
    ("rangers_visible", "trader"):
        "Somebody is running cargo without a manifest and being paid well for "
        "it. That is either very good work or a very short career.",
    ("rangers_visible", "downbelow"):
        "One of them bought a berth off me and paid in cash and asked me "
        "nothing. That is not how anybody down here behaves.",
    ("rangers_visible", "alien"):
        "The badge is Minbari work. Whatever it is, it is older than the "
        "Alliance that is looking for it.",
    ("monastics_resident", "official"):
        "The order has permanent quarters now. It is a residency grant and it "
        "went through in a week, which is not usual.",
    ("monastics_resident", "trader"):
        "They buy plainly, they pay on the day, and they never once haggle. I "
        "would take a corridor of them.",
    ("monastics_resident", "downbelow"):
        "The brothers come down with soup and they do not ask for a name to "
        "put against it. That is the whole of it.",
    ("monastics_resident", "alien"):
        "Humans who study rather than trade. It is the first thing your "
        "species has done here that I understand.",
    ("martial_law", "official"):
        "Summary authority over movement and assembly. I have read the order "
        "four times looking for the part that limits it.",
    ("martial_law", "trader"):
        "Curfew closes me two hours early and the same rent falls due. Write "
        "to whom, exactly?",
    ("martial_law", "downbelow"):
        "Emergency measures. Down here that means a sweep, and a sweep means "
        "they take the ones who cannot run.",
    ("martial_law", "alien"):
        "Your government has suspended itself and calls it order. Mine would "
        "at least have the decency to call it what it is.",
    ("secession", "official"):
        "We are independent as of this morning. I am still wearing the "
        "uniform of the service that is now going to come and take it back.",
    ("secession", "trader"):
        "No Alliance clearing, no Alliance credit line. Every account on this "
        "level settles in cash until somebody says otherwise.",
    ("secession", "downbelow"):
        "They have broken away and there is still no post below the eighth "
        "deck. Nothing changed down here at all.",
    ("secession", "alien"):
        "You have made yourselves a small power with a large enemy. The "
        "League will be very interested and very careful.",
}


def era_rumours(datum=None) -> list:
    """The rumour lines circulating at `datum`, one per (event, speaker class).

    Era-locked through the SAME clock as the armband and the ISN screen.
    """
    return [{"hour": None, "kind": "rumour", "places": ISN_PLACES,
             "text": t, "event": ev, "speaker": who,
             "source": f"costume.ERA_EVENTS[{ev!r}] + FACTIONS.md 11.5 "
                       f"({who} register)"}
            for (ev, who), t in ERA_RUMOUR.items() if _era_on(ev, datum)]


def denunciation_scene(datum=None) -> list:
    """The Nightwatch questioning, as an ordered scene. Empty before the era.

    FACTIONS.md 5.1: *"Any armband before The Fall of Night is an error."* The
    scene is the armband speaking, so it is locked to the same event.
    """
    if not _era_on("nightwatch_visible", datum):
        return []
    return [{"hour": None, "kind": "denunciation", "places": MINIPAX_PLACES,
             "text": t, "speaker": who, "beat": i,
             "event": "nightwatch_visible",
             "source": "FACTIONS.md 5 -- dissent relabelled treason"}
            for i, (who, t) in enumerate(DENUNCIATION)]


def ship_call(kind: str, call: str = "arrival") -> str:
    """One PA line for one hull class and one of the three call types."""
    row = SHIP_CALLS.get(kind)
    if row is None:                                          # pragma: no cover
        return SHIP_CALL.get(kind, kind).upper()
    return row[CALL_TYPES.index(call)]


def templates() -> dict:
    """DLG-04's census, computed rather than asserted.

    Every distinct broadcast string this module can put in front of a player,
    grouped the way `docs/spec/PEOPLE.md` DLG-04's arithmetic groups them. The
    harness reads THIS, so the count and the content cannot drift apart -- a
    row added to a table below is counted the moment it exists and a row
    deleted stops being counted the same moment.
    """
    return {
        "isn": {t for v in ISN_ROTATION.values() for t in v},
        "minipax": {t for v in MINIPAX_ROTATION for t in v},
        "pa_ship": {t for v in SHIP_CALLS.values() for t in v},
        "watch": set(WATCH_CALL.values()),
        "board": set(BOARD_VOICE),
        "sweep": {SENSOR_SWEEP},
        "advisory": {LINER_ADVISORY},
        "denunciation": {t for _who, t in DENUNCIATION},
        "rumour": set(ERA_RUMOUR.values()),
    }


def isn_bulletins(datum=None, rotation: int = 0) -> list:
    """The bulletins in force at `datum`, in event order.

    THE ERA LOCK IS THE POINT. At the S3E05 datum four of the five are on; at
    S2E01 none are, because none of their events has happened. A future session
    that moves `costume.ERA_DATUM` moves what the screens say, and nothing here
    has to know.
    """
    return [{"hour": None, "kind": "isn", "places": ISN_PLACES,
             "text": ISN_ROTATION[ev][rotation % len(ISN_ROTATION[ev])],
             "event": ev, "rotation": rotation % len(ISN_ROTATION[ev]),
             "source": f"costume.ERA_EVENTS[{ev!r}] + FACTIONS.md 11.5, "
                       f"rotation slot {rotation % len(ISN_ROTATION[ev])}"}
            for ev, _txt in ISN_BULLETINS if _era_on(ev, datum)]


def minipax_notices(datum=None, rotation: int = 0) -> list:
    """Ministry of Peace notices -- ONLY after Nightwatch surfaces aboard.

    FACTIONS.md 5.1 is explicit: *"Any armband before The Fall of Night is an
    error."* The same is true of the notices; a Ministry of Peace poster in a
    Season 1 customs hall is the same mistake as the armband.
    """
    if not _era_on("nightwatch_visible", datum):
        return []
    return [{"hour": None, "kind": "minipax", "places": MINIPAX_PLACES,
             "text": v[rotation % len(v)], "event": "nightwatch_visible",
             "rotation": rotation % len(v),
             "source": "FACTIONS.md 5 and 11.5's build note, rotation slot "
                       f"{rotation % len(v)}"}
            for v in MINIPAX_ROTATION]


# ===========================================================================
# 4.  What a player hears
# ===========================================================================

def day(day_n: int = 0, datum=None) -> list:
    """Everything the station says on one day, in time order.

    Timed items first by hour; the standing surfaces (ISN, notices) carry
    `hour=None` because a screen is always on and a poster is always up.
    """
    timed = port_calls(day_n) + watch_calls() + civic_calls()
    timed.sort(key=lambda a: a["hour"])
    # THE ROTATION SLOT IS THE DAY. A screen that shows the same three
    # sentences forever is one sentence with extra steps, so which of a story's
    # three phrasings is up is a function of the day the player is standing in.
    return (timed + isn_bulletins(datum, day_n) + minipax_notices(datum, day_n)
            + era_rumours(datum) + denunciation_scene(datum))


def audible_at(place_key: str, hour: float, day_n: int = 0, window_h=0.25,
               datum=None) -> list:
    """What a player standing in `place_key` at `hour` can hear or read.

    `window_h` is how long a call is still "now". Standing surfaces are always
    returned, because a screen a player can walk up to is part of what the room
    says whether or not anything was announced this minute.
    """
    out = []
    for a in day(day_n, datum):
        if place_key not in a["places"]:
            continue
        if a["hour"] is None:
            out.append(a)
            continue
        d = min(abs(a["hour"] - hour), abs(a["hour"] - hour + 24.0),
                abs(a["hour"] - hour - 24.0))
        if d <= window_h:
            out.append(a)
    return out


def has_terminal(place_key: str) -> bool:
    """Is there a BabCom terminal here a player could use?"""
    return place_key in BABCOM_PLACES


# ===========================================================================
# 5.  Report
# ===========================================================================

def report(out=print):
    d = day(0)
    timed = [a for a in d if a["hour"] is not None]
    standing = [a for a in d if a["hour"] is None]
    out(f"THE STATION SAYS {len(timed)} TIMED THINGS A DAY and carries "
        f"{len(standing)} standing surfaces, at datum {cos.ERA_DATUM}")
    kinds = {}
    for a in d:
        kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
    out("  " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    out("")
    out("A DAY AT THE ARRIVAL CONCOURSE")
    for h in (2.0, 8.0, 10.5, 14.0, 18.0, 22.0):
        heard = audible_at("arrival_concourse", h, 0)
        live = [a for a in heard if a["hour"] is not None]
        out(f"  {h:05.2f}  {len(live)} call(s), "
            f"{len(heard) - len(live)} standing surface(s)")
        for a in live[:2]:
            out(f"          [{a['kind']}] {a['text'][:78]}")
    out("")
    out("THE ERA LOCK -- the same station, three datums")
    for dm, label in (((2, 1), "S2E01"), ((2, 22), "S2E22"),
                      ((3, 5), "S3E05, the datum")):
        b = isn_bulletins(dm)
        m = minipax_notices(dm)
        out(f"  {label:16s} {len(b)} ISN bulletin(s), "
            f"{len(m)} Ministry of Peace notice(s)")
    out("")
    out("A LINER DAY, at the north hall")
    ld = next((n for n in range(8) if tf.liner_today(n)), 0)
    la = next((a for a in tf.arrivals(ld) if a["type"] == "liner"), None)
    if la:
        for dh in (-0.3, -0.25, 0.0, 0.4):
            h = (la["hour"] + dh) % 24.0
            heard = [a for a in audible_at("customs_north", h, ld)
                     if a["hour"] is not None]
            r = tf.hall_rate(h, ld)
            out(f"  {h:05.2f}  {r['total_per_min']:5.2f}/min "
                f"(x{r['multiple']:.1f})  "
                + (heard[0]["text"][:64] if heard else "--"))
    out("")
    out(f"BabCom terminals at: {', '.join(BABCOM_PLACES)}")


# ===========================================================================
# 6.  Gate
# ===========================================================================

_FAILED = []


def check(ok, name, detail=""):
    if not ok:
        _FAILED.append(f"{name}: {detail}")
    return ok


def _has(key):
    try:
        dr.by_key(key)
        return True
    except Exception:
        return False


def _selftest(out=print):                                       # noqa: C901
    global ISN_BULLETINS, PA_PLACES
    del _FAILED[:]
    n = 0

    # -- EVERY SHIP CLASS HAS A SPOKEN NAME ------------------------------
    # `port_calls` falls back to the raw manifest key, so a class added to
    # traffic.MANIFEST without an entry here has the PA announcing a dict key
    # ("now docking, tanker") and nothing fails. That is this project's own
    # recurring shape -- a table extended in one place and not the other -- so
    # the coupling is asserted rather than remembered. Found when SPEC-CHANGE #3
    # added the tanker.
    import traffic as _t                                          # noqa: PLC0415
    n += 1
    missing = [k for k, *_ in _t.MANIFEST if k not in SHIP_CALL]
    check(not missing, "every traffic.MANIFEST class has a spoken SHIP_CALL name",
          f"{missing}")
    n += 1
    orphan = [k for k in SHIP_CALL if k not in {r[0] for r in _t.MANIFEST}]
    check(not orphan, "...and no SHIP_CALL names a class the manifest dropped",
          f"{orphan}")

    # -- DLG-04: THREE CALL TYPES PER CLASS, AND NO TWO CLASSES SHARE ONE ----
    # The defect this catches is the one the module HAD: one arrival string
    # with the class name substituted into it, which is 51 announcements a day
    # in two phrasings. Identity, not similarity -- `deck.py --degeneracy`'s
    # question asked of text. Two hulls whose calls hash the same ARE one hull.
    n += 1
    gaps = [k for k, *_ in _t.MANIFEST
            if len(SHIP_CALLS.get(k, ())) != len(CALL_TYPES)]
    check(not gaps, f"every manifest class has all {len(CALL_TYPES)} call types",
          f"{gaps}")
    n += 1
    calls = [t for v in SHIP_CALLS.values() for t in v]
    check(len(set(calls)) == len(calls),
          "no two hull classes share a PA line",
          f"{len(calls) - len(set(calls))} duplicated")

    # -- DLG-04: the census is the content, and it is 98 --------------------
    n += 1
    cens = templates()
    flat = [t for v in cens.values() for t in v]
    check(len(set(flat)) == len(flat),
          "every broadcast template in the census is distinct",
          f"{len(flat) - len(set(flat))} duplicated")
    n += 1
    check(len(ERA_RUMOUR) == len(cos.ERA_EVENTS) * len(RUMOUR_SPEAKERS),
          f"the rumour matrix is {len(cos.ERA_EVENTS)} events x "
          f"{len(RUMOUR_SPEAKERS)} speaker classes",
          f"{len(ERA_RUMOUR)} rows")
    n += 1
    holes = [(e, w) for e in cos.ERA_EVENTS for w in RUMOUR_SPEAKERS
             if (e, w) not in ERA_RUMOUR]
    check(not holes, "...with no hole in it", f"{holes[:4]}")

    # -- every place a voice reaches is a real place ---------------------
    for name, group in (("PA_PLACES", PA_PLACES),
                        ("BABCOM_PLACES", BABCOM_PLACES),
                        ("ISN_PLACES", ISN_PLACES),
                        ("MINIPAX_PLACES", MINIPAX_PLACES)):
        n += 1
        bad = [k for k in group if not _has(k)]
        check(not bad, f"every {name} entry is a register place", f"{bad}")
    n += 1
    check(set(PA_PLACES) & set(BABCOM_PLACES),
          "the port and the comms network overlap somewhere a player stands")

    # -- the calls are DERIVED, and this is what proves it ---------------
    n += 1
    a0 = tf.arrivals(0)
    calls = port_calls(0)
    check(len(calls) >= 2 * len(a0),
          "every arrival gets an arrival call and a departure call",
          f"{len(calls)} calls for {len(a0)} arrivals")
    n += 1
    # THE ASSERTION THAT MATTERS: change the port and the tannoy changes.
    # Nothing here is a fixed list, so this must hold by construction.
    c1 = [a["text"] for a in port_calls(1)]
    check(c1 != [a["text"] for a in calls],
          "a different day says different things -- the calls come from the "
          "manifest, not from a script")
    n += 1
    liner_day = next((d for d in range(8) if tf.liner_today(d)), None)
    check(liner_day is not None, "a liner turns up within a week")
    if liner_day is not None:
        n += 1
        lc = [a for a in port_calls(liner_day)
              if "CUSTOMS ADVISORY" in a["text"]]
        check(len(lc) == 1,
              "a liner day gets exactly one customs advisory, ahead of it",
              f"{len(lc)}")
        n += 1
        la = next(a for a in tf.arrivals(liner_day) if a["type"] == "liner")
        check(str(la["souls"]) in lc[0]["text"],
              "and it names the number of passengers that actually berthed",
              f"{la['souls']} in {lc[0]['text'][:60]!r}")
        n += 1
        nold = next((d for d in range(8) if not tf.liner_today(d)), None)
        if nold is not None:
            check(not [a for a in port_calls(nold)
                       if "CUSTOMS ADVISORY" in a["text"]],
                  "and a day with no liner gets no advisory -- the control "
                  "for the one above")
        else:
            check(False, "no linerless day in a week to control against")

    # -- the watch ------------------------------------------------------
    n += 1
    w = watch_calls()
    check(len(w) == 3 and {x["hour"] for x in w} == {0.0, 8.0, 16.0},
          "three watches, on the three-shift boundaries", f"{w}")
    n += 1
    check(all(str(sched.role_on_duty("security", x["hour"])) in x["text"]
              for x in w),
          "and each names the number actually on duty at that hour")

    # -- THE ERA LOCK, which is the sharpest thing in this module --------
    n += 1
    at_datum = isn_bulletins()
    check(len(at_datum) >= 3,
          "several ISN bulletins are in force at the S3E05 datum",
          f"{len(at_datum)}")
    n += 1
    early = isn_bulletins((2, 1))
    check(not early,
          "and NONE at S2E01, because none of their events has happened",
          f"{len(early)}")
    n += 1
    check(not minipax_notices((2, 1)) and not minipax_notices((2, 21)),
          "no Ministry of Peace notice before The Fall of Night -- the same "
          "rule FACTIONS.md 5.1 states for the armband")
    n += 1
    check(minipax_notices((2, 22)) and minipax_notices((3, 5)),
          "and they are up from S2E22 onward")
    n += 1
    check(all(_era_on(b["event"]) for b in at_datum),
          "every bulletin in force cites an event that is in force")

    # -- audibility -----------------------------------------------------
    n += 1
    heard = audible_at("arrival_concourse", 10.0, 0)
    check(heard, "something is audible at the concourse at the morning peak",
          f"{len(heard)}")
    n += 1
    quarters = audible_at("qtr_civilian", 10.0, 0)
    check(not quarters,
          "and NOTHING is audible in ordinary civilian quarters -- a tannoy "
          "you cannot get away from is a tannoy the owner's isolation brief "
          "does not want", f"{len(quarters)}")
    n += 1
    always = audible_at("zocalo", 3.0, 0)
    check(any(a["hour"] is None for a in always),
          "a standing surface is there at three in the morning, because a "
          "screen is always on")
    n += 1
    check(has_terminal("zocalo") and not has_terminal("downbelow"),
          "the Zocalo has a BabCom terminal and Downbelow does not")

    # -- the voice ------------------------------------------------------
    n += 1
    txt = open(GAZETTEER).read() if os.path.exists(GAZETTEER) else ""
    check("Do not make them look like villain posters" in txt,
          "the build note this module is written to is still in FACTIONS.md")
    n += 1
    shouty = [a for a in minipax_notices()
              if "!" in a["text"] or "TRAITOR" in a["text"].upper()]
    check(not shouty,
          "the notices are official and reasonable, which is the build note's "
          "whole point -- no exclamation marks, no villain vocabulary",
          f"{shouty}")
    n += 1
    check(all(t.upper() == t or t.startswith("MINISTRY")
              for t in BOARD_VOICE),
          "the authority-1 board text is carried verbatim")

    # ------------------------------------------------------------------
    # NEGATIVE CONTROLS
    # ------------------------------------------------------------------
    out("negative controls:")

    keep = ISN_BULLETINS
    try:
        # An entry citing an event that does not exist must be caught, not
        # silently dropped -- an unknown key is a typo that reads as content.
        ISN_BULLETINS = keep + (("no_such_event", "ISN. Nothing happened."),)
        raised = False
        try:
            isn_bulletins()
        except KeyError:
            raised = True
        verdict = ("raises KeyError, FIRES" if raised
                   else "silently dropped, DOES NOT FIRE")
        out(f"  a bulletin citing an unknown era event -> {verdict}")
        n += 1
        check(raised, "an unknown era event is an error, not a no-op")
    finally:
        ISN_BULLETINS = keep

    keepp = PA_PLACES
    try:
        PA_PLACES = ("not_a_place",)
        bad = [k for k in PA_PLACES if not _has(k)]
        out(f"  a PA place that is not in the register -> {bad} -- "
            f"place gate {'FIRES' if bad else 'DOES NOT FIRE'}")
        n += 1
        check(bad, "the register gate fires on an invented place")
    finally:
        PA_PLACES = keepp

    d0 = cos.ERA_DATUM
    out(f"  the era lock at three datums: S2E01 {len(isn_bulletins((2, 1)))} "
        f"bulletins / {len(minipax_notices((2, 1)))} notices; "
        f"S2E22 {len(isn_bulletins((2, 22)))} / "
        f"{len(minipax_notices((2, 22)))}; "
        f"datum {d0} {len(isn_bulletins())} / {len(minipax_notices())}")

    if _FAILED:
        out("")
        for f in _FAILED:
            out(f"  FAIL {f}")
    out(f"\n{n - len(_FAILED)}/{n} passed")
    return not _FAILED


if __name__ == "__main__":                                   # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.report:
        ok = _selftest()
        if a.report:
            print()
            report()
        raise SystemExit(0 if ok else 1)
    report()
