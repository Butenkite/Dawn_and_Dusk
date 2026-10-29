#!/usr/bin/env python3
"""Generate history/countries/*.txt from tools/data/countries.csv.

Every tag the game knows needs a history file, even if the country does not
exist at the start (releasables use it when they appear). Writing ~360 of
these by hand is error-prone, so the CSV is the source of truth:

    tag, name, capital (state id), ruling (ideology group, blank = default)

Edit the CSV, run this script from the repo root, and commit both:

    python tools/countries/generate_country_history.py

Countries that get real content (story nations, supporting cast) should be
moved OUT of the CSV and into a hand-written history file. List those tags in
HAND_WRITTEN below so the script never overwrites them.
"""

import csv
import os
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MOD, DATA  # noqa: E402

CSV_PATH = str(DATA / "countries.csv")
OUT_DIR = str(MOD / "history" / "countries")

# Tags with hand-written history files. The generator skips these.
HAND_WRITTEN = set()

DEFAULT_RULING = "authoritarian_democrat"

GROUPS = [
    "communism", "socialist", "social_democrat", "democratic",
    "conservative", "authoritarian_democrat", "neutrality", "fascism",
]

# Placeholder popularity spread per ruling group (sums to 100).
# Real numbers come with each country's own pass.
POPULARITY = {
    "communism":         {"communism": 60, "socialist": 15, "authoritarian_democrat": 15, "neutrality": 5, "fascism": 5},
    "socialist":        {"socialist": 45, "communism": 10, "social_democrat": 20, "authoritarian_democrat": 15, "conservative": 10},
    "social_democrat":  {"social_democrat": 40, "democratic": 20, "conservative": 25, "socialist": 10, "fascism": 5},
    "democratic":          {"democratic": 40, "social_democrat": 20, "conservative": 30, "authoritarian_democrat": 5, "fascism": 5},
    "conservative":     {"conservative": 40, "democratic": 25, "social_democrat": 20, "authoritarian_democrat": 10, "fascism": 5},
    "authoritarian_democrat":    {"authoritarian_democrat": 50, "conservative": 15, "democratic": 10, "socialist": 10, "neutrality": 10, "fascism": 5},
    "neutrality":         {"neutrality": 55, "authoritarian_democrat": 20, "democratic": 10, "socialist": 10, "fascism": 5},
    "fascism": {"fascism": 55, "neutrality": 20, "authoritarian_democrat": 15, "conservative": 10},
}

# Government type shown on the politics screen (see
# common/scripted_localisation/dnd_government_type.txt). Countries not listed
# show "Not yet set" until their own pass.
GOVERNMENT = {
    "SAF": "parliamentary_republic",
    "EGY": "republic",
    "LIB": "republic",
    "LES": "constitutional_monarchy",
    "SWZ": "absolute_monarchy",
    "NMB": "republic",
    "BOT": "parliamentary_republic",
    "ZIM": "republic",
    "ZAM": "republic",
    "MLW": "republic",
    "MZB": "republic",
    "ANG": "republic",
    # central Africa
    "COG": "provisional_government",
    "RCD": "armed_movement",
    "MLC": "armed_movement",
    "RML": "armed_movement",
    "RCG": "provisional_government",
    "CAR": "republic",
    "CMR": "republic",
    "GAB": "republic",
    "EQG": "republic",
    "CHA": "republic",
    "RWA": "transitional_authority",
    "BRD": "military_government",
    "UGA": "republic",
    # west Africa
    "NGA": "federal_republic",
    "NGR": "republic",
    "DAH": "republic",
    "TOG": "republic",
    "GHA": "republic",
    "VOL": "republic",
    "IVO": "military_government",      # Guéï's junta since the coup of 24 December 1999
    "LIB": "republic",
    "SIE": "republic",
    "RUF": "armed_movement",
    "GNA": "republic",
    "GNB": "transitional_authority",    # between the 1998-99 civil war and Yalá's election
    "SEN": "republic",
    "GAM": "republic",
    "MLI": "republic",
    "MRT": "republic",
    "CBV": "republic",
    # east Africa
    "SUD": "republic",
    "SPL": "armed_movement",
    "ERI": "one_party_state",
    "ETH": "federal_republic",
    "DJI": "republic",
    "SOM": "provisional_government",    # no government since 1991; the Arta conference is months away
    "SML": "republic",                  # self-declared in 1991, recognised by no one
    "PNT": "transitional_authority",    # three-year transitional charter of 1998
    "SNA": "warlord_state",
    "SSA": "warlord_state",
    "HIR": "warlord_state",
    "RRA": "armed_movement",
    "JVA": "warlord_state",
    "SNF": "warlord_state",
    "KEN": "republic",
    "TZN": "republic",
    "MAD": "republic",
    "COM": "military_government",       # Azali's junta since the coup of 30 April 1999
    "ANJ": "provisional_government",    # seceded in August 1997
    "MUS": "parliamentary_republic",
    "SEY": "republic",
    # north Africa and the Middle East
    "MOR": "constitutional_monarchy",
    "SAH": "one_party_state",            # the Polisario's republic, in exile at Tindouf and in the Free Zone
    "ALG": "republic",
    "TUN": "republic",
    "LBA": "jamahiriya",
    "ISR": "parliamentary_republic",
    "PAL": "transitional_authority",     # the Oslo interim self-government
    "LEB": "parliamentary_republic",
    "SLA": "armed_movement",
    "SYR": "one_party_state",
    "JOR": "constitutional_monarchy",
    "IRQ": "one_party_state",
    "KDP": "provisional_government",
    "PUK": "provisional_government",
    "SAU": "absolute_monarchy",
    "YEM": "republic",
    "OMA": "absolute_monarchy",
    "UAE": "absolute_monarchy",
    "QAT": "absolute_monarchy",
    "BHR": "absolute_monarchy",
    "KUW": "constitutional_monarchy",
    "CYP": "republic",
    "NCY": "republic",
}

# Rebel movements and juntas: no elections whatever their ideology.
NO_ELECTIONS = {"RCD", "MLC", "RML", "BRD", "RUF", "IVO",
                "SPL", "ERI", "SOM", "SML", "PNT", "SNA", "SSA", "HIR", "RRA", "JVA", "SNF", "COM", "ANJ",
                "SAH", "SLA", "KDP", "PUK", "PAL"}

# Extra history lines for countries at war on 1 January 2000: the basic
# small-arms technology and an order of battle from history/units (written
# by tools/countries/generate_armies.py).
AT_WAR = {
    "COG": "COG_2000", "RCD": "RCD_2000", "MLC": "MLC_2000", "RML": "RML_2000",
    "SIE": "SIE_2000", "RUF": "RUF_2000",
    "SUD": "SUD_2000", "SPL": "SPL_2000", "ETH": "ETH_2000", "ERI": "ERI_2000",
}
# Country flags set at the start: Sierra Leone and the RUF hold the line of
# the Lomé ceasefire (July 1999), for content to break later.
START_FLAGS = {"SIE": ["dnd_lome_ceasefire"], "RUF": ["dnd_lome_ceasefire"],
               # the Comoros split since Anjouan's secession (August 1997), for
               # the reunification to play out later
               "COM": ["dnd_anjouan_secession"], "ANJ": ["dnd_anjouan_secession"],
               # Somalia without a state: every faction, and the Somalia the
               # Arta conference will try to rebuild
               **{t: ["dnd_somali_collapse"] for t in ("SOM", "SML", "PNT", "SNA", "SSA", "HIR", "RRA", "JVA", "SNF")},
               # standing arrangements of 2000, for content to keep or break:
               # the Western Sahara ceasefire (1991), Israel's security zone in
               # south Lebanon, the Oslo interim period, UN sanctions and the
               # no-fly zones over Iraq, the KDP-PUK Washington Agreement (1998),
               # the division of Cyprus (1974) and Algeria's Civil Concord (1999)
               "MOR": ["dnd_western_sahara_ceasefire"], "SAH": ["dnd_western_sahara_ceasefire"],
               "LEB": ["dnd_security_zone"], "SLA": ["dnd_security_zone"],
               "ISR": ["dnd_security_zone", "dnd_oslo_interim"], "PAL": ["dnd_oslo_interim"],
               "IRQ": ["dnd_un_sanctions", "dnd_no_fly_zones"],
               "KDP": ["dnd_washington_agreement"], "PUK": ["dnd_washington_agreement"],
               "CYP": ["dnd_cyprus_division"], "NCY": ["dnd_cyprus_division"],
               "ALG": ["dnd_civil_concord"]}
# Wars already running on 1 January 2000. Declared in history (as vanilla
# does for Italy and Ethiopia in 1936), so the game opens mid-war with no
# declaration popups.
AT_WAR_WITH = {
    "COG": ["RCD", "MLC", "RML"],   # Kinshasa against all three rebel movements
    "RCD": ["RML"],                 # Rwanda's and Uganda's clients, as at Kisangani
    "SUD": ["SPL"],                 # the Second Sudanese Civil War, since 1983
    "ERI": ["ETH"],                 # the border war, since Eritrea took Badme in May 1998
}
WAR_STABILITY = {"COG": 0.35, "RCD": 0.3, "MLC": 0.4, "RML": 0.25, "SIE": 0.35, "RUF": 0.3,
                 "SUD": 0.4, "SPL": 0.45, "ETH": 0.5, "ERI": 0.55}
WAR_SUPPORT = {"COG": 0.5, "RCD": 0.5, "MLC": 0.45, "RML": 0.4, "SIE": 0.3, "RUF": 0.45,
               "SUD": 0.4, "SPL": 0.6, "ETH": 0.6, "ERI": 0.75}

# Capitals of countries whose map region has been rebuilt come from the
# map builder (tools/data/map/built.json), since their state ids change.
BUILT = str(DATA / "map" / "built.json")

# Groups whose governments hold (some kind of) elections.
ELECTORAL = {"social_democrat", "democratic", "conservative", "authoritarian_democrat"}

TEMPLATE = """\
# {name}
# GENERATED by tools/countries/generate_country_history.py from tools/data/countries.csv.
# Do not edit by hand: change the CSV and re-run the script, or add the tag to
# HAND_WRITTEN in the script and write this file yourself.

capital = {capital}

set_research_slots = 3
set_stability = {stability}
set_war_support = {war_support}
set_convoys = 10
{government}{war}
set_politics = {{
	ruling_party = {ruling}
	last_election = "1999.1.1"
	election_frequency = 48
	elections_allowed = {elections}
}}

set_popularities = {{
{popularities}
}}
"""


def built_capitals():
    caps = {}
    if os.path.exists(BUILT):
        import json
        with open(BUILT, encoding="utf-8") as f:
            for region in json.load(f).values():
                caps.update(region.get("capitals", {}))
    return caps


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    caps = built_capitals()
    written = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row["tag"].strip()
            if tag in HAND_WRITTEN:
                continue
            ruling = (row["ruling"] or DEFAULT_RULING).strip()
            if ruling not in POPULARITY:
                sys.exit(f"{tag}: unknown ruling group '{ruling}'")
            pops = POPULARITY[ruling]
            assert sum(pops.values()) == 100, ruling
            pop_lines = "\n".join(f"\t{g} = {pops[g]}" for g in GROUPS if g in pops)
            text = TEMPLATE.format(
                name=row["name"],
                capital=caps.get(tag, row["capital"]),
                ruling=ruling,
                elections="yes" if ruling in ELECTORAL and tag not in NO_ELECTIONS else "no",
                stability=WAR_STABILITY.get(tag, 0.5),
                war_support=WAR_SUPPORT.get(tag, 0.2),
                war=(f"\noob = \"{AT_WAR[tag]}\"\n\nset_technology = {{\n\tinfantry_weapons = 1\n}}\n"
                     if tag in AT_WAR else "") + "".join(
                    f"\ndeclare_war_on = {{\n\ttarget = {t}\n\ttype = annex_everything\n}}\n"
                    for t in AT_WAR_WITH.get(tag, [])),
                popularities=pop_lines,
                government=(f"set_country_flag = dnd_govt_{GOVERNMENT[tag]}\n"
                            if tag in GOVERNMENT else "") + "".join(
                    f"set_country_flag = {f}\n" for f in START_FLAGS.get(tag, [])),
            )
            path = os.path.join(OUT_DIR, f"{tag} - {row['name']}.txt")
            # utf-8 with BOM, matching what the game writes and expects
            with open(path, "w", encoding="utf-8-sig", newline="\n") as out:
                out.write(text)
            written += 1
    print(f"wrote {written} country history files to {OUT_DIR}")


if __name__ == "__main__":
    main()
