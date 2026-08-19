"""All-Sport Fantasy Redraft — six sports, one combined draft board.

Snake draft, 8 teams (You, Bruner, + 6 bots), 12 rounds (96 picks). No
position requirements — pure best-player-available across NFL, MLB, NHL,
NBA, college basketball (CBB), and college football (CFB).

Each sport scores its own players with a sport-appropriate formula, then
those raw scores are z-score normalized *within* that sport's pool and
mapped onto a shared 0-100 "draft_value" scale. That's what makes an
elite NHL goalie and an elite NFL receiver comparable on one board — raw
skill numbers don't mean the same thing across sports, but "this player
is 1.5 standard deviations above their sport's own average" does.

Run: python3 allsport_draft.py
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field

from nba_redraft import PLAYERS_RAW as NBA_PLAYERS_RAW


# ---------------------------------------------------------------------------
# Player model
# ---------------------------------------------------------------------------


COLLEGE_SPORTS = {"CBB", "CFB"}

# Injury/availability overlay, keyed by player name. Values are one of
# "Q", "D", "IR", "IL", "OUT". Maintained by a nightly status-check job;
# players who have left their league entirely are removed from the
# relevant *_RAW list instead of tagged here.
PLAYER_STATUS: dict[str, str] = {
    # Updated 2026-08-17. NFL/NHL/NBA/CBB haven't started their 2026-27
    # seasons yet, so only confirmed multi-week/season-opening absences are
    # tagged (as OUT/IR) — no Q/D until each league's games are live. MLB's
    # season is in progress, so IL tags reflect current active placements.
    "Micah Parsons": "IR",       # NFL — ACL tear (Dec 2025 surgery), out to ~Week 6
    "Tyreek Hill": "OUT",        # NFL — unsigned FA recovering from knee reconstruction
    "Connor Bedard": "OUT",      # NHL — shoulder surgery July 2026, out to ~Nov 2026
    "Aaron Judge": "IL",         # MLB — rib stress fracture, on IL since June
    "Juan Soto": "IL",           # MLB — Grade 2 calf strain, on IL since July 24
    "Corbin Burnes": "IL",       # MLB — recovering from Tommy John surgery, missed 2026 so far
    "Vladimir Guerrero Jr.": "IL",  # MLB — concussion IL, placed Aug 14/15
    "JT Toppin": "OUT",          # CBB — ACL tear Feb 2026, expected out to ~Dec 2026
}


@dataclass
class Player:
    name: str
    sport: str
    pos: str
    age: int | None
    class_year: int | None
    skill: int
    health: int
    score: float = field(init=False)
    draft_value: float = field(default=0.0)
    status: str | None = field(default=None)
    pos_rank: int = field(default=0)

    def __post_init__(self) -> None:
        # This is a redraft for one season, not a dynasty league — age and
        # class year are display info only. A veteran having a great year
        # ranks the same as a rookie having the same great year; only
        # current talent and durability-for-this-season matter.
        self.score = round(self.skill * 0.85 + self.health * 0.15, 2)
        self.status = PLAYER_STATUS.get(self.name)

    @property
    def age_display(self) -> str:
        if self.age is not None:
            return str(self.age)
        return {1: "Fr", 2: "So", 3: "Jr", 4: "Sr"}.get(self.class_year or 1, "?")


SPORTS: list[str] = ["NFL", "MLB", "NHL", "NBA", "CBB", "CFB"]


# ---------------------------------------------------------------------------
# NFL — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

NFL_RAW: list[tuple[str, str, int, int, int]] = [
    ("Justin Fields", "QB", 25, 15, 80),
    ("Patrick Mahomes", "QB", 30, 65.3, 85),
    ("Garrett Nussmeier", "QB", 25, 15, 80),
    ("Chris Oladokun", "QB", 25, 15, 80),
    ("Emari Demercado", "RB", 25, 15, 80),
    ("Emmett Johnson", "RB", 25, 31.5, 80),
    ("Jaydn Ott", "RB", 25, 15, 80),
    ("Brashard Smith", "RB", 25, 15, 80),
    ("EJ Smith", "RB", 25, 15, 80),
    ("Kenneth Walker III", "RB", 25, 91.9, 78),
    ("Cyrus Allen", "WR", 25, 30.3, 80),
    ("Andrew Armstrong", "WR", 25, 15, 80),
    ("Jason Brownlee", "WR", 25, 15, 80),
    ("Jeff Caldwell", "WR", 25, 15, 80),
    ("Jacob De Jesus", "WR", 25, 15, 80),
    ("Omari Evans", "WR", 25, 15, 80),
    ("Jimmy Holiday", "WR", 25, 15, 80),
    ("Xavier Loyd", "WR", 25, 15, 80),
    ("Nikko Remigio", "WR", 25, 15, 80),
    ("Rashee Rice", "WR", 25, 90.3, 78),
    ("Jalen Royals", "WR", 25, 15, 80),
    ("Tyquan Thornton", "WR", 25, 15, 80),
    ("Jeff Weimer", "WR", 25, 15, 80),
    ("Xavier Worthy", "WR", 22, 58.1, 80),
    ("Jake Briningstool", "TE", 25, 15, 80),
    ("Noah Gray", "TE", 25, 15, 80),
    ("Travis Kelce", "TE", 36, 51.8, 75),
    ("Mason Pline", "TE", 25, 15, 80),
    ("Tre Watson", "TE", 25, 15, 80),
    ("Jared Wiley", "TE", 25, 15, 80),
    ("Vincent Anthony Jr.", "DE", 25, 15, 80),
    ("Felix Anudike-Uzomah", "DE", 25, 15, 80),
    ("Anthony Dunn Jr.", "DE", 25, 15, 80),
    ("Ashton Gillotte", "DE", 25, 15, 80),
    ("Ethan Hurkett", "DE", 25, 15, 80),
    ("George Karlaftis", "DE", 25, 15, 80),
    ("Emmanuel Ogbah", "DE", 25, 15, 80),
    ("Tyreke Smith", "DE", 25, 15, 80),
    ("R Mason Thomas", "DE", 25, 15, 80),
    ("Cole Brevard", "DT", 25, 15, 80),
    ("Marcus Harris", "DT", 25, 15, 80),
    ("Chris Jones", "DT", 31, 15, 82),
    ("Amari McNeill", "DT", 25, 15, 80),
    ("Omarr Norman-Lott", "DT", 25, 15, 80),
    ("Damon Payne", "DT", 25, 15, 80),
    ("Khyiris Tonga", "DT", 25, 15, 80),
    ("Peter Woods", "DT", 25, 15, 80),
    ("Kam Arnold", "LB", 25, 15, 80),
    ("Jeffrey Bassa", "LB", 25, 15, 80),
    ("Wesley Bissainthe", "LB", 25, 15, 80),
    ("Nick Bolton", "LB", 25, 15, 80),
    ("Cole Christiansen", "LB", 25, 15, 80),
    ("Jack Cochrane", "LB", 25, 15, 80),
    ("Cooper McDonald", "LB", 25, 15, 80),
    ("Drue Tranquill", "LB", 25, 15, 80),
    ("Jadon Canady", "CB", 25, 15, 80),
    ("Mansoor Delane", "CB", 25, 15, 80),
    ("Kaiir Elam", "CB", 25, 15, 80),
    ("Kristian Fulton", "CB", 25, 15, 80),
    ("Kevin Knowles", "CB", 25, 15, 80),
    ("Kader Kohou", "CB", 25, 15, 80),
    ("D'Arco Perkins-McAllister", "CB", 25, 15, 80),
    ("Chris Roland-Wallace", "CB", 25, 15, 80),
    ("Melvin Smith Jr.", "CB", 25, 15, 80),
    ("L'Jarius Sneed", "CB", 25, 15, 80),
    ("Zelmar Vedder", "CB", 25, 15, 80),
    ("Nohl Williams", "CB", 25, 15, 80),
    ("Chamarri Conner", "S", 25, 15, 80),
    ("Alohi Gilman", "S", 25, 15, 80),
    ("Jaden Hicks", "S", 25, 15, 80),
    ("Tanner McCalister", "S", 25, 15, 80),
    ("Xavier Nwankpa", "S", 25, 15, 80),
    ("DeShon Singleton", "S", 25, 15, 80),
    ("Harrison Butker", "K", 25, 15, 80),
    ("Matt Araiza", "P", 25, 15, 80),
    ("James Winchester", "LS", 25, 15, 80),
    ("Josh Allen", "QB", 29, 87.1, 88),
    ("Kyle Allen", "QB", 25, 15, 80),
    ("Shane Buechele", "QB", 25, 15, 80),
    ("James Cook III", "RB", 25, 95.0, 80),
    ("Ray Davis", "RB", 25, 15, 80),
    ("Frank Gore Jr.", "RB", 25, 15, 80),
    ("Ty Johnson", "RB", 25, 15, 80),
    ("Ian Wheeler", "RB", 25, 15, 80),
    ("Skyler Bell", "WR", 25, 15, 80),
    ("Keon Coleman", "WR", 23, 15, 82),
    ("Mac Dalena", "WR", 25, 15, 80),
    ("Stephen Gosnell", "WR", 25, 15, 80),
    ("Mecole Hardman Jr.", "WR", 25, 15, 80),
    ("Ja'Mori Maclin", "WR", 25, 15, 80),
    ("DJ Moore", "WR", 25, 15, 80),
    ("Joshua Palmer", "WR", 25, 15, 80),
    ("Dante Pettis", "WR", 25, 15, 80),
    ("Khalil Shakir", "WR", 25, 49.0, 85),
    ("Tyrell Shavers", "WR", 25, 15, 80),
    ("Trent Sherfield", "WR", 25, 15, 80),
    ("Quentin Skinner", "WR", 25, 15, 80),
    ("Max Tomczak", "WR", 25, 15, 80),
    ("Jackson Hawes", "TE", 25, 15, 80),
    ("Dalton Kincaid", "TE", 25, 52.2, 78),
    ("Dawson Knox", "TE", 25, 15, 80),
    ("Keleki Latu", "TE", 25, 15, 80),
    ("Shane Zylstra", "TE", 25, 15, 80),
    ("Mike Danna", "DE", 25, 15, 80),
    ("Cade Denhoff", "DE", 25, 15, 80),
    ("Michael Hoecht", "DE", 25, 15, 80),
    ("Landon Jackson", "DE", 25, 15, 80),
    ("Andre Jones Jr.", "DE", 25, 15, 80),
    ("Tommy Akingbesote", "DT", 25, 15, 80),
    ("DeWayne Carter", "DT", 25, 15, 80),
    ("Zane Durant", "DT", 25, 15, 80),
    ("Zion Logue", "DT", 25, 15, 80),
    ("Phidarian Mathis", "DT", 25, 15, 80),
    ("Ed Oliver", "DT", 25, 15, 80),
    ("T.J. Sanders", "DT", 25, 15, 80),
    ("Deone Walker", "DT", 25, 15, 80),
    ("Joe Andreessen", "LB", 25, 15, 80),
    ("Terrel Bernard", "LB", 25, 15, 80),
    ("Bradley Chubb", "LB", 25, 15, 80),
    ("Jimmy Ciarlo", "LB", 25, 15, 80),
    ("Kaleb Elarms-Orr", "LB", 25, 15, 80),
    ("Theron Gaines", "LB", 25, 15, 80),
    ("Keonta Jenkins", "LB", 25, 15, 80),
    ("TJ Parker", "LB", 25, 15, 80),
    ("Greg Rousseau", "LB", 25, 15, 80),
    ("Javon Solomon", "LB", 25, 15, 80),
    ("Dorian Williams", "LB", 25, 15, 80),
    ("Dee Alford", "CB", 25, 15, 80),
    ("Christian Benford", "CB", 25, 15, 80),
    ("Te'Cory Couch", "CB", 25, 15, 80),
    ("Jordan Dunbar", "CB", 25, 15, 80),
    ("Maxwell Hairston", "CB", 25, 15, 80),
    ("Jordan Hancock", "CB", 25, 15, 80),
    ("Davison Igbinosun", "CB", 25, 15, 80),
    ("Anthony Kendall", "CB", 25, 15, 80),
    ("D.J. Miller", "CB", 25, 15, 80),
    ("Toriano Pride Jr.", "CB", 25, 15, 80),
    ("Kani Walker", "CB", 25, 15, 80),
    ("Cole Bishop", "S", 25, 15, 80),
    ("Sam Franklin Jr.", "S", 25, 15, 80),
    ("C.J. Gardner-Johnson", "S", 25, 15, 80),
    ("Damar Hamlin", "S", 25, 15, 80),
    ("Jalon Kilgore", "S", 25, 15, 80),
    ("Wande Owens", "S", 25, 15, 80),
    ("Geno Stone", "S", 25, 15, 80),
    ("Tyler Bass", "K", 25, 15, 80),
    ("Mitch Wishnowsky", "P", 25, 15, 80),
    ("Reid Ferguson", "LS", 25, 15, 80),
    ("Andy Dalton", "QB", 25, 15, 80),
    ("Jalen Hurts", "QB", 27, 68.0, 85),
    ("Tanner McKee", "QB", 25, 15, 80),
    ("Saquon Barkley", "RB", 28, 94.6, 82),
    ("Tank Bigsby", "RB", 25, 27.5, 80),
    ("Will Shipley", "RB", 25, 15, 80),
    ("Hollywood Brown", "WR", 25, 15, 80),
    ("DeVonta Smith", "WR", 25, 83.5, 80),
    ("Elijah Moore", "WR", 25, 15, 80),
    ("Johnny Wilson", "WR", 25, 15, 80),
    ("Grant Calcaterra", "TE", 25, 15, 80),
    ("Dallas Goedert", "TE", 25, 46.6, 80),
    ("Eli Stowers", "TE", 25, 15, 80),
    ("AJ Epenesa", "DE", 25, 15, 80),
    ("Jalen Carter", "DT", 24, 15, 82),
    ("Jordan Davis", "DT", 25, 15, 80),
    ("Zack Baun", "LB", 28, 15, 85),
    ("Jihaad Campbell", "LB", 25, 15, 80),
    ("Nolan Smith Jr.", "LB", 25, 15, 80),
    ("Jeremiah Trotter Jr.", "LB", 25, 15, 80),
    ("Cooper DeJean", "CB", 25, 15, 80),
    ("Quinyon Mitchell", "CB", 25, 15, 80),
    ("Riq Woolen", "CB", 25, 15, 80),
    ("Andrew Mukuba", "S", 25, 15, 80),
    ("Jake Elliott", "K", 25, 15, 80),
    ("Braden Mann", "P", 25, 15, 80),
    ("Joshua Dobbs", "QB", 25, 15, 80),
    ("Jared Goff", "QB", 31, 51.0, 88),
    ("Jahmyr Gibbs", "RB", 23, 99.0, 85),
    ("Isiah Pacheco", "RB", 25, 36.7, 80),
    ("Amon-Ra St. Brown", "WR", 26, 96.6, 90),
    ("Jameson Williams", "WR", 24, 77.2, 75),
    ("Tyler Conklin", "TE", 25, 15, 80),
    ("Sam LaPorta", "TE", 24, 64.5, 85),
    ("Aidan Hutchinson", "DE", 25, 15, 65),
    ("Alim McNeill", "DT", 25, 15, 80),
    ("Tyleik Williams", "DT", 25, 15, 80),
    ("Jack Campbell", "LB", 25, 15, 80),
    ("Alex Anzalone", "LB", 25, 15, 80),
    ("D.J. Reed", "CB", 25, 15, 80),
    ("Brian Branch", "S", 25, 15, 80),
    ("Kerby Joseph", "S", 25, 15, 80),
    ("Jake Bates", "K", 25, 15, 80),
    ("Lamar Jackson", "QB", 28, 81.1, 85),
    ("Derrick Henry", "RB", 31, 92.3, 78),
    ("Justice Hill", "RB", 25, 15, 80),
    ("Zay Flowers", "WR", 25, 84.3, 82),
    ("Rashod Bateman", "WR", 25, 20.8, 80),
    ("Mark Andrews", "TE", 25, 49.8, 80),
    ("Calais Campbell", "DE", 25, 15, 80),
    ("Nnamdi Madubuike", "DT", 25, 15, 80),
    ("Roquan Smith", "LB", 28, 15, 85),
    ("Trey Hendrickson", "DE", 30, 15, 78),
    ("Marlon Humphrey", "CB", 29, 15, 75),
    ("Nate Wiggins", "CB", 25, 15, 80),
    ("Kyle Hamilton", "S", 25, 15, 85),
    ("Malaki Starks", "S", 25, 15, 80),
    ("Tyler Loop", "K", 25, 15, 80),
    ("Jordan Love", "QB", 27, 57.3, 82),
    ("Josh Jacobs", "RB", 27, 87.5, 80),
    ("Christian Watson", "WR", 25, 75.2, 80),
    ("Jayden Reed", "WR", 25, 63.3, 80),
    ("Matthew Golden", "WR", 25, 52.6, 80),
    ("Tucker Kraft", "TE", 24, 67.6, 85),
    ("Micah Parsons", "LB", 26, 15, 85),
    ("Javon Hargrave", "DT", 25, 15, 80),
    ("Devonte Wyatt", "DT", 25, 15, 80),
    ("Zaire Franklin", "LB", 25, 15, 80),
    ("Edgerrin Cooper", "LB", 25, 15, 80),
    ("Xavier McKinney", "S", 26, 15, 82),
    ("Trey Smack", "K", 25, 15, 80),
    ("Brock Purdy", "QB", 25, 56.9, 80),
    ("Christian McCaffrey", "RB", 29, 97.0, 62),
    ("Brandon Aiyuk", "WR", 25, 15, 80),
    ("Deebo Samuel Sr.", "WR", 25, 46.2, 80),
    ("George Kittle", "TE", 32, 48.6, 80),
    ("Nick Bosa", "DE", 28, 15, 78),
    ("Fred Warner", "LB", 29, 15, 88),
    ("Dre Greenlaw", "LB", 25, 15, 80),
    ("Deommodore Lenoir", "CB", 25, 15, 80),
    ("Renardo Green", "CB", 25, 15, 80),
    ("Eddy Pineiro", "K", 25, 15, 80),
    ("Dak Prescott", "QB", 32, 66.8, 75),
    ("Javonte Williams", "RB", 25, 86.3, 75),
    ("CeeDee Lamb", "WR", 26, 95.4, 88),
    ("George Pickens", "WR", 25, 89.9, 80),
    ("Jake Ferguson", "TE", 25, 53.7, 80),
    ("Kenny Clark", "DT", 25, 15, 80),
    ("Quinnen Williams", "DT", 28, 15, 85),
    ("Von Miller", "LB", 25, 15, 80),
    ("DaRon Bland", "CB", 25, 15, 80),
    ("Caleb Downs", "S", 21, 15, 88),
    ("Brandon Aubrey", "K", 25, 15, 80),
    ("Quinn Ewers", "QB", 25, 15, 80),
    ("De'Von Achane", "RB", 24, 94.2, 78),
    ("Jaylen Wright", "RB", 25, 15, 80),
    ("Tyreek Hill", "WR", 31, 15, 82),
    ("Jaylen Waddle", "WR", 27, 82.3, 82),
    ("Malik Washington", "WR", 25, 31.9, 80),
    ("Jonnu Smith", "TE", 25, 15, 80),
    ("Zach Sieler", "DT", 25, 15, 80),
    ("Jordyn Brooks", "LB", 27, 15, 82),
    ("Chop Robinson", "LB", 25, 15, 80),
    ("Jason Marshall Jr.", "CB", 25, 15, 80),
    ("Minkah Fitzpatrick", "S", 25, 15, 80),
    ("Riley Patterson", "K", 25, 15, 80),
    ("Geno Smith", "QB", 35, 15, 82),
    ("Breece Hall", "RB", 24, 84.7, 75),
    ("Garrett Wilson", "WR", 25, 80.7, 85),
    ("Adonai Mitchell", "WR", 25, 33.9, 80),
    ("Mason Taylor", "TE", 25, 15, 80),
    ("Will McDonald IV", "DE", 25, 15, 80),
    ("Jamien Sherwood", "LB", 25, 15, 80),
    ("Sauce Gardner", "CB", 25, 15, 88),
    ("D'Angelo Ponds", "CB", 25, 15, 80),
    ("Jason Sanders", "K", 25, 15, 80),
    ("Aaron Rodgers", "QB", 25, 15, 80),
    ("Kaleb Johnson", "RB", 25, 15, 80),
    ("Jaylen Warren", "RB", 25, 73.6, 80),
    ("DK Metcalf", "WR", 28, 70.0, 82),
    ("Roman Wilson", "WR", 25, 15, 80),
    ("Pat Freiermuth", "TE", 25, 15, 80),
    ("Cameron Heyward", "DT", 36, 15, 78),
    ("Derrick Harmon", "DT", 25, 15, 80),
    ("T.J. Watt", "LB", 31, 15, 80),
    ("Patrick Queen", "LB", 25, 15, 80),
    ("Alex Highsmith", "LB", 25, 15, 80),
    ("Jalen Ramsey", "CB", 25, 15, 80),
    ("Joey Porter Jr.", "CB", 25, 15, 80),
    ("DeShon Elliott", "S", 25, 15, 80),
    ("Chris Boswell", "K", 25, 15, 80),
    ("Joe Burrow", "QB", 29, 74.0, 78),
    ("Chase Brown", "RB", 25, 91.5, 82),
    ("Ja'Marr Chase", "WR", 25, 98.2, 90),
    ("Tee Higgins", "WR", 27, 85.1, 78),
    ("Mike Gesicki", "TE", 25, 15, 80),
    ("Shemar Stewart", "DE", 25, 15, 80),
    ("B.J. Hill", "DT", 25, 15, 80),
    ("Dexter Lawrence II", "DT", 25, 15, 80),
    ("Dax Hill", "CB", 25, 15, 80),
    ("DJ Turner II", "CB", 25, 15, 80),
    ("Jordan Battle", "S", 25, 15, 80),
    ("Evan McPherson", "K", 25, 15, 80),
    ("C.J. Stroud", "QB", 24, 35.5, 88),
    ("Nico Collins", "WR", 26, 93.0, 82),
    ("Jayden Higgins", "WR", 25, 47.4, 80),
    ("Tank Dell", "WR", 25, 29.9, 80),
    ("Dalton Schultz", "TE", 25, 23.6, 80),
    ("Will Anderson Jr.", "LB", 24, 15, 85),
    ("Danielle Hunter", "DE", 31, 15, 82),
    ("Derek Stingley Jr.", "CB", 25, 15, 80),
    ("Kamari Lassiter", "CB", 25, 15, 80),
    ("Reed Blankenship", "S", 25, 15, 80),
    ("Ka'imi Fairbairn", "K", 25, 15, 80),
    ("Bo Nix", "QB", 25, 49.4, 85),
    ("J.K. Dobbins", "RB", 25, 68.8, 80),
    ("RJ Harvey", "RB", 25, 68.4, 80),
    ("Courtland Sutton", "WR", 30, 62.9, 82),
    ("Marvin Mims Jr.", "WR", 25, 15, 80),
    ("Evan Engram", "TE", 31, 15, 75),
    ("Zach Allen", "DE", 25, 15, 80),
    ("D.J. Jones", "DT", 25, 15, 80),
    ("Nik Bonitto", "LB", 25, 15, 80),
    ("Jonathon Cooper", "LB", 25, 15, 80),
    ("Pat Surtain II", "CB", 25, 15, 80),
    ("Talanoa Hufanga", "S", 25, 15, 80),
    ("Wil Lutz", "K", 25, 15, 80),
    ("Justin Herbert", "QB", 25, 66.1, 80),
    ("Omarion Hampton", "RB", 25, 89.5, 80),
    ("Ladd McConkey", "WR", 23, 83.9, 82),
    ("Quentin Johnston", "WR", 25, 55.3, 80),
    ("David Njoku", "TE", 25, 15, 80),
    ("Khalil Mack", "LB", 34, 15, 72),
    ("Tuli Tuipulotu", "LB", 25, 15, 80),
    ("Daiyan Henley", "LB", 25, 15, 80),
    ("Derwin James Jr.", "S", 25, 15, 80),
    ("Cameron Dicker", "K", 25, 15, 80),
    ("Sam Darnold", "QB", 29, 42.6, 80),
    ("Zach Charbonnet", "RB", 25, 41.0, 80),
    ("Jaxon Smith-Njigba", "WR", 25, 97.4, 80),
    ("Cooper Kupp", "WR", 25, 27.9, 80),
    ("Rashid Shaheed", "WR", 25, 43.0, 80),
    ("AJ Barner", "TE", 25, 15, 80),
    ("Leonard Williams", "DT", 25, 15, 80),
    ("Byron Murphy II", "DT", 25, 15, 80),
    ("Ernest Jones IV", "LB", 25, 15, 80),
    ("Devon Witherspoon", "CB", 25, 15, 80),
    ("Nick Emmanwori", "S", 25, 15, 80),
    ("Jason Myers", "K", 25, 15, 80),
    ("Justin Jefferson", "WR", 26, 95.8, 88),
    ("Bijan Robinson", "RB", 23, 98.6, 88),
    ("Myles Garrett", "DE", 30, 15, 88),
    ("Puka Nacua", "WR", 24, 97.8, 78),
    ("A.J. Brown", "WR", 28, 91.1, 82),
    ("Drake London", "WR", 24, 93.8, 85),
    ("Malik Nabers", "WR", 22, 90.7, 82),
    ("Marvin Harrison Jr.", "WR", 23, 71.6, 85),
    ("Brock Bowers", "TE", 23, 92.6, 85),
    ("Trey McBride", "TE", 26, 89.1, 85),
    ("Jonathan Taylor", "RB", 26, 96.2, 78),
    ("Trevor Lawrence", "QB", 26, 52.9, 82),
    ("Matthew Stafford", "QB", 37, 54.5, 75),
    ("Baker Mayfield", "QB", 30, 47.0, 85),
    ("Jayden Daniels", "QB", 25, 76.0, 78),
    ("Kyler Murray", "QB", 28, 50.2, 75),
    ("Maxx Crosby", "DE", 28, 15, 88),
    ("Patrick Surtain II", "CB", 25, 15, 88),
    ("Derwin James", "S", 29, 15, 72),
    ("Antoine Winfield Jr.", "S", 27, 15, 82),
    ("Denzel Ward", "CB", 29, 15, 75),
    ("Brian Burns", "DE", 27, 15, 82),
    ("Rome Odunze", "WR", 23, 74.8, 85),
    ("Terry McLaurin", "WR", 30, 77.6, 85),
    ("Chris Olave", "WR", 25, 88.7, 75),
    ("James Cook", "RB", 25, 15, 82),
    ("Alvin Kamara", "RB", 30, 31.1, 78),
    ("Rhamondre Stevenson", "RB", 27, 69.6, 78),
    ("Caleb Williams", "QB", 24, 64.1, 82),
    ("Drake Maye", "QB", 24, 73.2, 85),
    ("J.J. McCarthy", "QB", 23, 15, 78),
    ("Isaiah Pacheco", "RB", 26, 15, 75),
    ("Xavien Howard", "CB", 32, 15, 70),
    ("Trevon Diggs", "CB", 27, 15, 68),
    ("Za'Darius Smith", "LB", 33, 15, 70),
    ("Jerry Jeudy", "WR", 26, 32.3, 82),
    ("Jauan Jennings", "WR", 28, 43.4, 80),
    ("Josh Downs", "WR", 24, 63.7, 82),
    ("Wan'Dale Robinson", "WR", 24, 59.7, 80),
    ("Ricky Pearsall", "WR", 24, 15, 78),
    ("Brian Thomas Jr.", "WR", 23, 72.4, 82),
    ("Tony Pollard", "RB", 28, 71.2, 80),
    ("Aaron Jones", "RB", 30, 60.9, 72),
    ("Najee Harris", "RB", 27, 15, 82),
    ("David Montgomery", "RB", 28, 81.9, 75),
    ("Zack Moss", "RB", 27, 15, 75),
    ("Rachaad White", "RB", 26, 61.3, 80),
    ("Zamir White", "RB", 25, 15, 82),
    ("Tyjae Spears", "RB", 24, 44.6, 78),
    ("Cade Otton", "TE", 26, 15, 82),
    ("Colston Loveland", "TE", 21, 85.5, 82),
    ("Isaiah Likely", "TE", 25, 39.8, 80),
    ("Dexter Lawrence", "DT", 27, 15, 82),
    ("Vita Vea", "DT", 30, 15, 80),
    ("Josh Sweat", "DE", 28, 15, 80),
    ("Bobby Wagner", "LB", 35, 15, 82),
    ("Foyesade Oluokun", "LB", 29, 15, 88),
    ("Devin White", "LB", 27, 15, 78),
    ("Jaire Alexander", "CB", 28, 15, 65),
    ("Jaylon Johnson", "CB", 26, 15, 82),
    ("Charvarius Ward", "CB", 29, 15, 82),
    ("Christian Gonzalez", "CB", 23, 15, 78),
    ("Terrion Arnold", "CB", 22, 15, 82),
    ("Budda Baker", "S", 29, 15, 82),
    ("Jessie Bates III", "S", 28, 15, 85),
    ("Jordan Poyer", "S", 34, 15, 80),
    ("Camryn Bynum", "S", 26, 15, 85),
    ("Fernando Mendoza", "QB", 22, 15, 85),
    ("David Bailey", "LB", 21, 15, 85),
    ("Jeremiyah Love", "RB", 21, 86.7, 85),
    ("Arvell Reese", "LB", 21, 15, 85),
    ("Sonny Styles", "LB", 21, 15, 85),
]



# ---------------------------------------------------------------------------
# MLB — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

MLB_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Catchers (restored -- accidentally caught by an NFL-Center-position
    # removal regex that also matched MLB's "C" position code) ----
    ("William Contreras", "C", 27, 82, 85),
    ("Adley Rutschman", "C", 27, 85, 78),
    ("Cal Raleigh", "C", 29, 87, 85),
    ("Salvador Perez", "C", 35, 76, 78),
    ("J.T. Realmuto", "C", 34, 76, 72),
    ("Logan O'Hoppe", "C", 25, 72, 78),
    ("Shohei Ohtani", "DH", 31, 99.0, 82),
    ("Aaron Judge", "OF", 33, 71.8, 82),
    ("Juan Soto", "OF", 27, 92.9, 88),
    ("Bobby Witt Jr.", "SS", 25, 98.5, 90),
    ("Jose Ramirez", "3B", 33, 98.2, 88),
    ("Mookie Betts", "SS", 33, 69.1, 82),
    ("Ronald Acuna Jr.", "OF", 28, 95.3, 68),
    ("Gunnar Henderson", "SS", 24, 74.7, 88),
    ("Vladimir Guerrero Jr.", "1B", 27, 73.9, 88),
    ("Freddie Freeman", "1B", 36, 86.1, 82),
    ("Yordan Alvarez", "DH", 28, 98.7, 70),
    ("Kyle Tucker", "OF", 28, 62.5, 85),
    ("Paul Skenes", "SP", 23, 92.7, 85),
    ("Tarik Skubal", "SP", 28, 96.6, 88),
    ("Zack Wheeler", "SP", 35, 93.5, 82),
    ("Gerrit Cole", "SP", 35, 74.4, 65),
    ("Corbin Burnes", "SP", 31, 15, 85),
    ("Spencer Strider", "SP", 27, 15, 60),
    ("Mason Miller", "RP", 27, 87.6, 75),
    ("Corbin Carroll", "OF", 25, 96.4, 82),
    ("Julio Rodriguez", "OF", 25, 94.5, 85),
    ("Elly De La Cruz", "SS", 23, 97.7, 85),
    ("Matt Olson", "1B", 32, 93.2, 88),
    ("Francisco Lindor", "SS", 32, 71.3, 88),
    ("Trea Turner", "SS", 33, 90.5, 85),
    ("Manny Machado", "3B", 33, 76.5, 82),
    ("Rafael Devers", "3B", 29, 74.2, 80),
    ("Austin Riley", "3B", 28, 48.0, 80),
    ("Jackson Chourio", "OF", 22, 90.8, 85),
    ("James Wood", "OF", 23, 90.0, 85),
    ("Jackson Merrill", "OF", 22, 75.5, 85),
    ("Riley Greene", "OF", 25, 77.1, 82),
    ("Bryce Harper", "1B", 33, 85.8, 72),
    ("Pete Alonso", "1B", 31, 83.9, 85),
    ("Ketel Marte", "2B", 32, 83.4, 78),
    ("Marcus Semien", "2B", 35, 15, 88),
    ("Jazz Chisholm Jr.", "2B", 28, 84.5, 75),
    ("Ozzie Albies", "2B", 28, 73.6, 78),
    ("Jose Altuve", "2B", 35, 23.2, 82),
    ("CJ Abrams", "SS", 25, 97.2, 85),
    ("Bo Bichette", "SS", 27, 64.7, 75),
    ("Xander Bogaerts", "SS", 33, 49.1, 78),
    ("Anthony Volpe", "SS", 24, 15, 85),
    ("Wyatt Langford", "OF", 23, 60.7, 80),
    ("Steven Kwan", "OF", 27, 41.1, 88),
    ("Ian Happ", "OF", 31, 56.2, 85),
    ("Christian Yelich", "OF", 33, 39.3, 72),
    ("George Springer", "OF", 36, 61.0, 75),
    ("Teoscar Hernandez", "OF", 33, 63.1, 82),
    ("Anthony Santander", "OF", 31, 15, 82),
    ("Michael Harris II", "OF", 24, 85.5, 78),
    ("Nolan Arenado", "3B", 34, 51.2, 82),
    ("Alex Bregman", "3B", 31, 64.9, 78),
    ("Yoshinobu Yamamoto", "SP", 27, 95.0, 82),
    ("Hunter Greene", "SP", 26, 15, 75),
    ("Dylan Cease", "SP", 30, 92.1, 85),
    ("Max Fried", "SP", 32, 86.8, 85),
    ("Framber Valdez", "SP", 32, 45.4, 85),
    ("Logan Gilbert", "SP", 28, 86.3, 85),
    ("Chris Sale", "SP", 37, 95.8, 65),
    ("Ranger Suarez", "SP", 30, 59.1, 80),
    ("Sonny Gray", "SP", 36, 83.7, 78),
    ("Kevin Gausman", "SP", 35, 70.5, 85),
    ("Blake Snell", "SP", 33, 53.0, 72),
    ("Freddy Peralta", "SP", 29, 51.7, 82),
    ("Josh Hader", "RP", 31, 67.6, 85),
    ("Edwin Diaz", "RP", 31, 57.3, 78),
    ("Felix Bautista", "RP", 30, 15, 65),
    ("Devin Williams", "RP", 30, 54.3, 78),
    ("Ryan Helsley", "RP", 31, 15, 80),
    ("Raisel Iglesias", "RP", 35, 69.9, 82),
    ("Camilo Doval", "RP", 28, 15, 78),
    ("Byron Buxton", "OF", 32, 67.8, 55),
    ("Luis Robert Jr.", "OF", 28, 15, 65),
    ("Randy Arozarena", "OF", 30, 91.6, 78),
    ("Jarren Duran", "OF", 29, 33.5, 82),
    ("Brenton Doyle", "OF", 27, 15, 82),
    ("Lawrence Butler", "OF", 25, 15, 80),
    ("Colton Cowser", "OF", 25, 15, 80),
    ("Jasson Dominguez", "OF", 22, 15, 78),
    ("Ceddanne Rafaela", "OF", 25, 82.6, 85),
    ("Jung Hoo Lee", "OF", 27, 49.3, 78),
    ("Spencer Torkelson", "1B", 26, 15, 82),
    ("Christian Walker", "1B", 34, 75.2, 82),
    ("Josh Naylor", "1B", 28, 70.2, 82),
    ("Triston Casas", "1B", 26, 15, 72),
    ("Nathaniel Lowe", "1B", 30, 15, 82),
    ("Gleyber Torres", "2B", 28, 52.5, 80),
    ("Brice Turang", "2B", 25, 89.0, 85),
    ("Andres Gimenez", "2B", 27, 15, 82),
    ("Luis Arraez", "2B", 28, 83.1, 88),
    ("Willy Adames", "SS", 29, 55.4, 85),
    ("Ha-Seong Kim", "SS", 30, 15, 78),
    ("Dansby Swanson", "SS", 31, 48.5, 78),
    ("Oneil Cruz", "SS", 26, 89.5, 70),
    ("Jordan Westburg", "3B", 26, 15, 78),
    ("Junior Caminero", "3B", 22, 97.9, 82),
    ("Max Muncy", "3B", 35, 63.6, 72),
    ("Ryan McMahon", "3B", 30, 15, 82),
    ("Shane Bieber", "SP", 30, 15, 65),
    ("Jack Flaherty", "SP", 29, 15, 75),
    ("Aaron Nola", "SP", 32, 15, 82),
    ("Zac Gallen", "SP", 30, 15, 82),
    ("Cristopher Sanchez", "SP", 28, 96.1, 85),
    ("Joe Ryan", "SP", 29, 87.4, 85),
    ("Garrett Crochet", "SP", 26, 65.4, 80),
    ("MacKenzie Gore", "SP", 26, 37.4, 82),
    ("Bryce Miller", "SP", 26, 45.1, 82),
    ("Michael King", "SP", 30, 73.4, 78),
    ("Jhoan Duran", "RP", 27, 85.3, 82),
    ("Andres Munoz", "RP", 25, 80.8, 80),
    ("Robert Suarez", "RP", 34, 15, 82),
    ("Kenley Jansen", "RP", 38, 53.3, 78),
]


# ---------------------------------------------------------------------------
# NHL — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

NHL_RAW: list[tuple[str, str, int, int, int]] = [
    ("Connor McDavid", "C", 29, 99.0, 85),
    ("Nathan MacKinnon", "C", 30, 98.7, 85),
    ("Auston Matthews", "C", 28, 93.9, 78),
    ("Leon Draisaitl", "C", 30, 97.7, 88),
    ("Jack Hughes", "C", 24, 93.6, 78),
    ("Connor Bedard", "C", 20, 78.7, 82),
    ("Sidney Crosby", "C", 38, 85.0, 82),
    ("Jack Eichel", "C", 29, 92.3, 78),
    ("Aleksander Barkov", "C", 30, 87.3, 75),
    ("Elias Pettersson", "C", 27, 55.9, 78),
    ("Tim Stutzle", "C", 23, 15, 85),
    ("Wyatt Johnston", "C", 22, 94.2, 88),
    ("Matty Beniers", "C", 22, 15, 82),
    ("Macklin Celebrini", "C", 19, 98.0, 82),
    ("John Tavares", "C", 35, 73.3, 82),
    ("Sebastian Aho", "C", 28, 68.9, 85),
    ("Nico Hischier", "C", 26, 68.5, 82),
    ("Steven Stamkos", "C", 35, 67.6, 75),
    ("Brayden Point", "C", 29, 80.0, 78),
    ("Dylan Larkin", "C", 28, 77.7, 82),
    ("Nazem Kadri", "C", 34, 63.8, 82),
    ("Tage Thompson", "C", 28, 89.5, 78),
    ("Trevor Zegras", "C", 24, 59.7, 72),
    ("Kirby Dach", "C", 24, 15, 68),
    ("Bo Horvat", "C", 30, 72.7, 82),
    ("Barrett Hayton", "C", 25, 15, 82),
    ("Sam Bennett", "C", 29, 67.3, 78),
    ("Mark Scheifele", "C", 32, 89.2, 80),
    ("Adam Fantilli", "C", 21, 80.6, 82),
    ("Nick Suzuki", "C", 26, 94.6, 88),
    ("Igor Shesterkin", "G", 29, 86.0, 85),
    ("Connor Hellebuyck", "G", 32, 90.8, 88),
    ("Juuse Saros", "G", 30, 39.4, 78),
    ("Jake Oettinger", "G", 27, 86.3, 85),
    ("Thatcher Demko", "G", 29, 15, 65),
    ("Stuart Skinner", "G", 26, 15, 82),
    ("Ilya Sorokin", "G", 30, 90.4, 80),
    ("Logan Thompson", "G", 28, 91.1, 78),
    ("Andrei Vasilevskiy", "G", 31, 95.2, 78),
    ("Darcy Kuemper", "G", 35, 27.0, 70),
    ("Jacob Markstrom", "G", 35, 74.3, 78),
    ("Linus Ullmark", "G", 32, 51.4, 75),
    ("Joey Daccord", "G", 28, 15, 82),
    ("Filip Gustavsson", "G", 27, 15, 82),
    ("Sergei Bobrovsky", "G", 37, 61.9, 78),
    ("Karel Vejmelka", "G", 29, 62.2, 80),
    ("Spencer Knight", "G", 24, 44.7, 75),
    ("Cale Makar", "D", 27, 96.8, 82),
    ("Nikita Kucherov", "RW", 32, 98.4, 85),
    ("David Pastrnak", "RW", 29, 97.4, 88),
    ("Kirill Kaprizov", "LW", 28, 97.1, 82),
    ("Quinn Hughes", "D", 26, 95.5, 85),
    ("Mikko Rantanen", "RW", 29, 92.0, 85),
    ("Artemi Panarin", "LW", 33, 84.7, 85),
    ("Matthew Tkachuk", "LW", 27, 91.7, 72),
    ("Brady Tkachuk", "LW", 26, 93.0, 82),
    ("William Nylander", "RW", 29, 85.4, 88),
    ("Mitch Marner", "RW", 28, 83.8, 85),
    ("Adam Fox", "D", 27, 74.9, 85),
    ("Roman Josi", "D", 35, 69.2, 82),
    ("Victor Hedman", "D", 34, 62.8, 78),
    ("Zach Werenski", "D", 28, 95.8, 82),
    ("Rasmus Dahlin", "D", 25, 86.9, 85),
    ("Miro Heiskanen", "D", 26, 71.1, 80),
    ("Clayton Keller", "RW", 27, 85.7, 82),
    ("Jason Robertson", "LW", 26, 96.5, 85),
    ("Sam Reinhart", "RW", 29, 87.6, 88),
    ("Seth Jarvis", "RW", 23, 15, 85),
    ("Jesper Bratt", "LW", 27, 77.1, 88),
    ("Filip Forsberg", "LW", 31, 78.1, 82),
    ("Charlie McAvoy", "D", 27, 57.1, 65),
    ("Moritz Seider", "D", 24, 75.2, 88),
    ("Evan Bouchard", "D", 26, 92.7, 85),
    ("Noah Dobson", "D", 25, 52.4, 85),
    ("Devon Toews", "D", 31, 15, 82),
    ("Josh Morrissey", "D", 30, 52.7, 85),
    ("Shea Theodore", "D", 30, 51.7, 78),
    ("Aaron Ekblad", "D", 29, 15, 75),
    ("Alex Ovechkin", "LW", 40, 67.0, 82),
    ("Nikolaj Ehlers", "LW", 29, 65.4, 78),
    ("Kyle Connor", "LW", 28, 89.8, 85),
    ("Drew Doughty", "D", 35, 15, 75),
    ("Patrick Kane", "RW", 36, 44.4, 68),
    ("Brad Marchand", "LW", 37, 58.1, 78),
    ("Alex DeBrincat", "LW", 27, 84.1, 80),
    ("Cutter Gauthier", "LW", 21, 90.1, 82),
    ("Owen Power", "D", 22, 15, 85),
    ("Luke Hughes", "D", 21, 38.1, 82),
    ("Jared McCann", "LW", 29, 15, 82),
    ("Anders Lee", "LW", 35, 31.1, 82),
    ("Filip Zadina", "LW", 25, 15, 75),
    ("Andrei Svechnikov", "LW", 25, 65.7, 75),
    ("Jake Guentzel", "LW", 31, 88.2, 78),
    ("Matthew Boldy", "LW", 24, 15, 85),
    ("Brandon Hagel", "LW", 27, 87.9, 88),
    ("Jordan Kyrou", "RW", 27, 60.3, 82),
    ("Tyler Bertuzzi", "LW", 30, 29.2, 78),
    ("Vasily Podkolzin", "RW", 24, 15, 78),
    ("Cole Caufield", "RW", 24, 93.3, 82),
    ("Zach Hyman", "RW", 33, 71.7, 78),
    ("Juraj Slafkovsky", "LW", 21, 83.1, 82),
    ("Lane Hutson", "D", 21, 91.4, 82),
    ("Jake Sanderson", "D", 23, 79.3, 85),
    ("K'Andre Miller", "D", 25, 22.5, 85),
    ("Ivan Provorov", "D", 28, 15, 85),
    ("Jaccob Slavin", "D", 31, 15, 88),
    ("Brandon Montour", "D", 30, 47.6, 82),
    ("Jared Spurgeon", "D", 35, 15, 75),
    ("Alex Pietrangelo", "D", 35, 15, 65),
    ("MacKenzie Weegar", "D", 31, 47.9, 88),
    ("Vince Dunn", "D", 28, 45.7, 85),
    ("Rasmus Andersson", "D", 28, 38.7, 85),
    ("Erik Karlsson", "D", 35, 69.5, 65),
]


# ---------------------------------------------------------------------------
# CBB — college (name, pos, class_year 1-4, skill, health)
# ---------------------------------------------------------------------------

CBB_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Centers (restored -- accidentally caught by an NFL-Center-position
    # removal regex that also matched CBB's "C" position code) ----
    ("Flory Bidunga", "C", 2, 84, 85),
    ("Alex Condon", "C", 3, 83, 85),
    ("Aaron Bradshaw", "C", 2, 74, 78),
    ("Assane Diop", "C", 2, 66, 78),
    ("Malachi Moreno", "C", 1, 68, 80),
    ("Johann Grunloh", "C", 2, 72, 80),
    # ---- Elite (89-96) ----
    ("JT Toppin", "PF", 3, 90, 85),
    # ---- Quality (74-88) ----
    ("Tahaad Pettiford", "PG", 2, 86, 82),
    ("Boogie Fland", "PG", 2, 85, 78),
    ("PJ Haggerty", "SG", 3, 82, 80),
    ("Jasper Johnson", "SG", 1, 80, 80),
    ("Tyler Betsey", "SF", 2, 80, 80),
    ("Donovan Dent", "PG", 3, 80, 82),
    ("Cayden Boozer", "PG", 1, 78, 82),
    ("Ian Jackson", "SG", 2, 76, 80),
    ("Karter Knox", "SG", 1, 76, 80),
    ("Miles Byrd", "SG", 4, 72, 82),
    ("Solo Ball", "SG", 3, 74, 82),
    ("Trey Green", "PG", 1, 75, 80),
    # ---- Depth / role players (55-78) ----
    ("Chance Westry", "SG", 2, 66, 78),
    ("Braylon Mullins", "SG", 1, 68, 82),
    ("Jerry Easter II", "SG", 1, 68, 80),
    # ---- 2026-27 incoming class / transfer portal backfill ----
    ("Tyran Stokes", "SF", 1, 95, 85),
    ("Jordan Smith", "PG", 1, 88, 84),
    ("Caleb Holt", "SG", 1, 85, 82),
    ("Jason Crowe", "PG", 1, 84, 82),
    ("Cameron Williams", "PF", 1, 82, 82),
    ("Milan Momcilovic", "PF", 3, 80, 82),
    ("John Blackwell", "SG", 3, 79, 82),
    ("Donnie Freeman", "PF", 3, 79, 82),
    ("Jack Burton", "SF", 4, 78, 78),
    ("Quentin Coleman", "SG", 1, 78, 80),
    ("Jaxon Richardson", "SF", 1, 77, 80),
    ("Juke Harris", "SG", 2, 77, 80),
    ("Toni Bryant", "PF", 1, 76, 80),
    ("Tylen Riley", "PG", 4, 76, 82),
    ("Taylen Kinney", "SG", 1, 75, 80),
    ("Dra Gibbs-Lawhorn", "SG", 4, 75, 80),
    ("Cameron Holmes", "PF", 1, 74, 78),
    ("Jamier Jones", "SG", 2, 74, 80),
    # ---- 2026-27 additional backfill (returning stars / transfers) ----
    ("Thomas Haugh", "PF", 4, 88, 85),
    ("Jeremy Fears Jr.", "PG", 3, 84, 85),
    ("Markus Burton", "PG", 4, 83, 82),
    ("Urban Klavzar", "SG", 2, 78, 82),
    ("Isaiah Brown", "SF", 2, 77, 82),
    ("Tyler Tanner", "PG", 3, 75, 82),
    ("Chance Mallory", "PG", 2, 75, 80),
    ("Sam Lewis", "SG", 3, 73, 80),
    ("Thijs de Ridder", "SF", 3, 73, 82),
    ("CJ Ingram", "SF", 2, 68, 82),
    ("Alex Lloyd", "PG", 1, 65, 80),
]


# ---------------------------------------------------------------------------
# CFB — college (name, pos, class_year 1-4, skill, health)
# ---------------------------------------------------------------------------

CFB_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Elite (88-97) ----
    ("Jeremiah Smith", "WR", 3, 97, 88),
    ("Arch Manning", "QB", 2, 90, 82),
    ("Ryan Williams", "WR", 2, 92, 82),
    ("LaNorris Sellers", "QB", 2, 87, 85),
    ("Dylan Stewart", "DE", 3, 90, 82),
    # ---- Quality (74-87) ----
    ("Julian Sayin", "QB", 2, 82, 82),
    ("DJ Lagway", "QB", 2, 85, 75),
    ("Dante Moore", "QB", 2, 78, 82),
    ("Dylan Raiola", "QB", 2, 84, 82),
    ("Sam Leavitt", "QB", 3, 82, 85),
    ("Avery Johnson", "QB", 4, 78, 85),
    ("Rocco Becht", "QB", 4, 79, 84),
    ("CJ Baxter", "RB", 3, 78, 78),
    ("Makhi Hughes", "RB", 3, 78, 82),
    ("Nyck Harbor", "WR", 4, 80, 82),
    ("Duce Robinson", "WR", 3, 80, 84),
    ("Evan Stewart", "WR", 4, 78, 75),
    ("Nic Anderson", "WR", 4, 76, 75),
    ("Anto Saka", "DE", 3, 82, 85),
    ("Colin Simmons", "DE", 2, 82, 78),
    ("Whit Weeks", "LB", 4, 82, 88),
    ("Xavier Lucas", "CB", 3, 80, 85),
    ("A.J. Harris", "CB", 4, 78, 82),
    ("Cameron Calhoun", "CB", 3, 78, 85),
    ("Peyton Bowen", "S", 3, 78, 85),
    ("Luke Kromenhoek", "QB", 2, 74, 82),
    ("Cutter Boley", "QB", 2, 73, 80),
    # ---- Depth / role players (55-78) ----
    ("Marcel Reed", "QB", 2, 76, 82),
    ("Noah Fifita", "QB", 4, 76, 82),
    ("Demond Williams Jr.", "QB", 2, 74, 85),
    ("Bryce Underwood", "QB", 1, 78, 82),
    ("Air Noland", "QB", 1, 70, 80),
    ("Husan Longstreet", "QB", 1, 68, 82),
    ("Justice Haynes", "RB", 2, 76, 82),
    ("Darius Taylor", "RB", 3, 76, 82),
    ("Quintrevion Wisner", "RB", 3, 74, 82),
    ("Roderick Robinson II", "RB", 3, 74, 82),
    ("Nate Frazier", "RB", 2, 72, 82),
    ("Jerrick Gibson", "RB", 1, 70, 82),
    ("Rueben Owens II", "RB", 2, 72, 80),
    ("Eric Singleton Jr.", "WR", 3, 74, 82),
    ("Winston Watkins Jr.", "WR", 3, 74, 80),
    ("Vernell Brown III", "WR", 2, 70, 82),
    ("Dakorien Moore", "WR", 1, 76, 82),
    ("Chris Henry Jr.", "WR", 2, 74, 78),
    ("Cam Coleman", "WR", 2, 78, 85),
    ("Ryan Wingo", "WR", 2, 74, 80),
    ("Rico Flores Jr.", "WR", 2, 70, 82),
    ("Jaime Ffrench", "WR", 4, 66, 80),
    ("Walker Lyons", "TE", 3, 68, 82),
    ("Vic Burley", "DT", 2, 72, 82),
    # ---- 2026 preseason top players backfill ----
    ("C.J. Carr", "QB", 3, 86, 85),
    ("Darian Mensah", "QB", 3, 85, 82),
    ("Leonard Moore", "CB", 3, 84, 85),
    ("Ahmad Hardy", "RB", 3, 83, 85),
    ("John Mateer", "QB", 4, 82, 78),
    ("Trinidad Chambliss", "QB", 4, 81, 82),
    ("Jalen Bolden", "S", 3, 80, 82),
    ("Josh Hoover", "QB", 4, 80, 82),
    ("Gunner Stockton", "QB", 3, 80, 82),
    ("Kewan Lacy", "RB", 3, 78, 82),
    ("Jayden Maiava", "QB", 4, 78, 80),
    ("Faizon Brandon", "QB", 1, 78, 82),
    ("Mark Fletcher", "RB", 2, 76, 80),
    ("Savion Hiter", "RB", 1, 76, 82),
    ("Keelon Russell", "QB", 2, 76, 82),
    ("Luke Wafle", "DE", 1, 74, 80),
    ("EJ Crowell", "RB", 1, 74, 82),
]



# ---------------------------------------------------------------------------
# Pool building + cross-sport normalization
# ---------------------------------------------------------------------------


def _build_pro(sport: str, raw: list[tuple[str, str, int, int, int]]) -> list[Player]:
    return [Player(name, sport, pos, age, None, skill, health) for name, pos, age, skill, health in raw]


def _build_college(sport: str, raw: list[tuple[str, str, int, int, int]]) -> list[Player]:
    return [
        Player(name, sport, pos, None, class_year, skill, health)
        for name, pos, class_year, skill, health in raw
    ]


def _build_nba() -> list[Player]:
    # Reuse the existing NBA prototype's data instead of re-typing it. Trim
    # to keep pool depth roughly in line with the other five sports.
    trimmed = NBA_PLAYERS_RAW[:120]
    return [Player(name, "NBA", pos, age, None, skill, health) for name, pos, age, skill, health in trimmed]


def normalize_pool(players: list[Player]) -> None:
    """Percentile-rank each player within their own sport's pool, then map
    that standing onto a shared 1-99 `draft_value` scale.

    This is the step that makes cross-sport comparison meaningful: judge a
    player against their own sport's peers first (percentile rank), then
    convert that standing into a number that means the same thing across
    sports. Percentile rank (rather than z-score) keeps one sport's outlier
    ratings from dominating the shared board — a sport can only ever
    contribute its true proportional share of the combined top tier,
    regardless of how spread out or clustered its raw skill numbers happen
    to be. Ties get averaged ranks so equal scores land on equal percentiles.
    """
    n = len(players)
    if n == 0:
        return
    if n == 1:
        players[0].draft_value = 99.0
        return
    ordered = sorted(players, key=lambda p: p.score)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ordered[j + 1].score == ordered[i].score:
            j += 1
        percentile = ((i + j) / 2) / (n - 1)
        draft_value = round(1.0 + percentile * 98.0, 1)
        for k in range(i, j + 1):
            ordered[k].draft_value = draft_value
        i = j + 1


def build_pool() -> list[Player]:
    sport_pools = {
        "NFL": _build_pro("NFL", NFL_RAW),
        "MLB": _build_pro("MLB", MLB_RAW),
        "NHL": _build_pro("NHL", NHL_RAW),
        "NBA": _build_nba(),
        "CBB": _build_college("CBB", CBB_RAW),
        "CFB": _build_college("CFB", CFB_RAW),
    }
    pool: list[Player] = []
    for sport in SPORTS:
        players = sport_pools[sport]
        normalize_pool(players)
        _assign_pos_ranks(players)
        pool.extend(players)
    pool.sort(key=lambda p: p.draft_value, reverse=True)
    return pool


def _assign_pos_ranks(players: list[Player]) -> None:
    """Position rank (e.g. "RB4") within this sport's own pool, highest
    score first. This is the number shown to the user in place of the old
    synthetic Skill number -- for NFL it's backed by real expert-consensus
    fantasy rankings (see NFL_RAW), not anything computed or guessed."""
    by_pos: dict[str, list[Player]] = {}
    for p in players:
        by_pos.setdefault(p.pos, []).append(p)
    for pos_group in by_pos.values():
        pos_group.sort(key=lambda p: p.score, reverse=True)
        for i, p in enumerate(pos_group, start=1):
            p.pos_rank = i


# ---------------------------------------------------------------------------
# Draft mechanics
# ---------------------------------------------------------------------------

TEAM_NAMES: list[str] = [
    "You",
    "Bruner",
    "Bot Ace",
    "Bot Ranger",
    "Bot Comet",
    "Bot Titan",
    "Bot Nova",
    "Bot Vortex",
]
HUMAN_TEAMS = {"You", "Bruner"}
ROUNDS = 30
ROSTER_SIZE = ROUNDS  # 30 flat roster spots per team; "starters" (10 of 30)
                       # is a future lineup-setting feature, not modeled here.


def build_snake_order(teams: list[str], rounds: int) -> list[str]:
    order: list[str] = []
    for r in range(rounds):
        order.extend(teams if r % 2 == 0 else list(reversed(teams)))
    return order


def ai_pick(available: list[Player]) -> Player:
    """Best player available with small noise among the top 3, weighted by
    draft_value squared so the top-ranked player is clearly favored while
    still allowing some draft-day noise."""
    top = available[:3]
    weights = [max(p.draft_value, 1.0) ** 2 for p in top]
    return random.choices(top, weights=weights, k=1)[0]


def resolve_pick(available: list[Player], query: str) -> Player | None:
    q = query.strip().lower()
    if not q:
        return None
    matches = [p for p in available if q in p.name.lower()]
    if len(matches) == 1:
        return matches[0]
    exact = [p for p in matches if p.name.lower() == q]
    if len(exact) == 1:
        return exact[0]
    return None


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------


def _cli_smoke_test() -> None:
    pool = build_pool()
    print(f"Total pool: {len(pool)} players")
    for sport in SPORTS:
        n = sum(1 for p in pool if p.sport == sport)
        print(f"  {sport}: {n}")
    print("\nTop 20 combined draft board:")
    for i, p in enumerate(pool[:20], start=1):
        print(f" {i:>2}. {p.name:<24} {p.sport:<4} {p.pos:<4} draft_value {p.draft_value:5.1f}")

    teams = TEAM_NAMES.copy()
    random.shuffle(teams)
    order = build_snake_order(teams, ROUNDS)
    print(f"\nSnake order (first 8 picks): {order[:8]}")
    print(f"Total picks: {len(order)}")


if __name__ == "__main__":
    _cli_smoke_test()
