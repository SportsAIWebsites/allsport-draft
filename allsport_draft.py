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
    # Updated 2026-08-23. NFL (starts Sep 9), NHL (Sep 29), NBA (Oct 20),
    # CBB (Nov 1), and CFB (FBS Week 0 starts Aug 29) haven't started
    # their 2026-27 seasons yet, so only confirmed multi-week/season-opening
    # absences are tagged (as OUT/IR) — no Q/D until each league's games
    # are live. MLB's season is in progress, so IL tags reflect current
    # active placements.
    "Micah Parsons": "IR",       # NFL — ACL tear (Dec 2025 surgery), now with GB (traded); targeting Week 6 (mid-Oct) at best
    "Tyreek Hill": "OUT",        # NFL — unsigned FA recovering from knee reconstruction
    "Jayden Higgins": "IR",      # NFL — torn ACL, out for the season
    "Connor Bedard": "OUT",      # NHL — shoulder surgery July 2026, targeting early/mid-Nov return
    "Aaron Judge": "IL",         # MLB — rib stress fracture, on IL since May 31
    "Juan Soto": "IL",           # MLB — Grade 2 calf strain, on IL since July 24
    "Corbin Burnes": "IL",       # MLB — Tommy John recovery hit a new lat/teres strain setback, now targeting Sept
    "Edwin Diaz": "IL",          # MLB — neck inflammation, placed Aug 18, seeing spine specialist
    "Max Fried": "IL",           # MLB — recurrence of left elbow bone bruise, placed Aug 18 (retro to Aug 14)
    "Spencer Strider": "IL",     # MLB — on 60-day IL, throwing progression restarted, 2026 return not assured
    "Jimmy Butler": "IR",        # NBA — torn ACL, will open 2026-27 season injured
    "JT Toppin": "OUT",          # CBB — ACL tear Feb 2026, expected out to ~Dec 2026
    "Donnie Freeman": "OUT",     # CBB — ruptured Achilles (offseason workout), out for 2026-27 season
    "Ahmad Hardy": "OUT",        # CFB — recovering from a gunshot wound, still no firm return date, missing Sep 3 opener
    "Dylan Stewart": "OUT",      # CFB — lingering back injury, coach calls Sep 5 opener "unrealistic"
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
        self.score = round(self.skill * 0.95 + self.health * 0.05, 2)
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
    ("Patrick Mahomes", "QB", 30, 65.1, 85),
    ("Garrett Nussmeier", "QB", 25, 15, 80),
    ("Chris Oladokun", "QB", 25, 15, 80),
    ("Emari Demercado", "RB", 25, 15, 80),
    ("Emmett Johnson", "RB", 25, 31.2, 80),
    ("Jaydn Ott", "RB", 25, 15, 80),
    ("Brashard Smith", "RB", 25, 15, 80),
    ("EJ Smith", "RB", 25, 15, 80),
    ("Kenneth Walker III", "RB", 25, 91.8, 78),
    ("Cyrus Allen", "WR", 25, 30.0, 80),
    ("Andrew Armstrong", "WR", 25, 15, 80),
    ("Jason Brownlee", "WR", 25, 15, 80),
    ("Jeff Caldwell", "WR", 25, 15, 80),
    ("Jacob De Jesus", "WR", 25, 15, 80),
    ("Omari Evans", "WR", 25, 15, 80),
    ("Jimmy Holiday", "WR", 25, 15, 80),
    ("Xavier Loyd", "WR", 25, 15, 80),
    ("Nikko Remigio", "WR", 25, 15, 80),
    ("Rashee Rice", "WR", 25, 90.2, 78),
    ("Jalen Royals", "WR", 25, 15, 80),
    ("Tyquan Thornton", "WR", 25, 15, 80),
    ("Jeff Weimer", "WR", 25, 15, 80),
    ("Xavier Worthy", "WR", 22, 57.9, 80),
    ("Jake Briningstool", "TE", 25, 15, 80),
    ("Noah Gray", "TE", 25, 15, 80),
    ("Travis Kelce", "TE", 36, 51.5, 75),
    ("Mason Pline", "TE", 25, 15, 80),
    ("Tre Watson", "TE", 25, 15, 80),
    ("Jared Wiley", "TE", 25, 15, 80),
    ("Harrison Butker", "K", 25, 15, 80),
    ("Matt Araiza", "P", 25, 15, 80),
    ("James Winchester", "LS", 25, 15, 80),
    ("Josh Allen", "QB", 29, 87.0, 88),
    ("Kyle Allen", "QB", 25, 15, 80),
    ("Shane Buechele", "QB", 25, 15, 80),
    ("James Cook III", "RB", 25, 15, 80),
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
    ("Khalil Shakir", "WR", 25, 48.7, 85),
    ("Tyrell Shavers", "WR", 25, 15, 80),
    ("Trent Sherfield", "WR", 25, 15, 80),
    ("Quentin Skinner", "WR", 25, 15, 80),
    ("Max Tomczak", "WR", 25, 15, 80),
    ("Jackson Hawes", "TE", 25, 15, 80),
    ("Dalton Kincaid", "TE", 25, 51.9, 78),
    ("Dawson Knox", "TE", 25, 15, 80),
    ("Keleki Latu", "TE", 25, 15, 80),
    ("Shane Zylstra", "TE", 25, 15, 80),
    ("Tyler Bass", "K", 25, 15, 80),
    ("Mitch Wishnowsky", "P", 25, 15, 80),
    ("Reid Ferguson", "LS", 25, 15, 80),
    ("Andy Dalton", "QB", 25, 15, 80),
    ("Jalen Hurts", "QB", 27, 67.9, 85),
    ("Tanner McKee", "QB", 25, 15, 80),
    ("Saquon Barkley", "RB", 28, 94.6, 82),
    ("Tank Bigsby", "RB", 25, 27.6, 80),
    ("Will Shipley", "RB", 25, 15, 80),
    ("Hollywood Brown", "WR", 25, 15, 80),
    ("DeVonta Smith", "WR", 25, 83.4, 80),
    ("Elijah Moore", "WR", 25, 15, 80),
    ("Johnny Wilson", "WR", 25, 15, 80),
    ("Grant Calcaterra", "TE", 25, 15, 80),
    ("Dallas Goedert", "TE", 25, 46.7, 80),
    ("Eli Stowers", "TE", 25, 15, 80),
    ("Jake Elliott", "K", 25, 15, 80),
    ("Braden Mann", "P", 25, 15, 80),
    ("Joshua Dobbs", "QB", 25, 15, 80),
    ("Jared Goff", "QB", 31, 50.7, 88),
    ("Jahmyr Gibbs", "RB", 23, 99.0, 85),
    ("Isiah Pacheco", "RB", 25, 36.8, 80),
    ("Amon-Ra St. Brown", "WR", 26, 96.6, 90),
    ("Jameson Williams", "WR", 24, 77.1, 75),
    ("Tyler Conklin", "TE", 25, 15, 80),
    ("Sam LaPorta", "TE", 24, 64.3, 85),
    ("Jake Bates", "K", 25, 15, 80),
    ("Lamar Jackson", "QB", 28, 81.0, 85),
    ("Derrick Henry", "RB", 31, 92.2, 78),
    ("Justice Hill", "RB", 25, 15, 80),
    ("Zay Flowers", "WR", 25, 84.2, 82),
    ("Rashod Bateman", "WR", 25, 21.2, 80),
    ("Mark Andrews", "TE", 25, 49.5, 80),
    ("Tyler Loop", "K", 25, 15, 80),
    ("Jordan Love", "QB", 27, 57.1, 82),
    ("Josh Jacobs", "RB", 27, 87.4, 80),
    ("Christian Watson", "WR", 25, 75.1, 80),
    ("Jayden Reed", "WR", 25, 63.1, 80),
    ("Matthew Golden", "WR", 25, 52.3, 80),
    ("Tucker Kraft", "TE", 24, 67.5, 85),
    ("Trey Smack", "K", 25, 15, 80),
    ("Brock Purdy", "QB", 25, 56.7, 80),
    ("Christian McCaffrey", "RB", 29, 97.0, 62),
    ("Brandon Aiyuk", "WR", 25, 15, 80),
    ("Deebo Samuel Sr.", "WR", 25, 15, 80),
    ("George Kittle", "TE", 32, 48.3, 80),
    ("Eddy Pineiro", "K", 25, 15, 80),
    ("Dak Prescott", "QB", 32, 66.7, 75),
    ("Javonte Williams", "RB", 25, 86.2, 75),
    ("CeeDee Lamb", "WR", 26, 95.4, 88),
    ("George Pickens", "WR", 25, 89.8, 80),
    ("Jake Ferguson", "TE", 25, 53.5, 80),
    ("Brandon Aubrey", "K", 25, 15, 80),
    ("Quinn Ewers", "QB", 25, 15, 80),
    ("De'Von Achane", "RB", 24, 94.2, 78),
    ("Jaylen Wright", "RB", 25, 15, 80),
    ("Tyreek Hill", "WR", 31, 15, 82),
    ("Jaylen Waddle", "WR", 27, 82.2, 82),
    ("Malik Washington", "WR", 25, 31.6, 80),
    ("Jonnu Smith", "TE", 25, 15, 80),
    ("Riley Patterson", "K", 25, 15, 80),
    ("Geno Smith", "QB", 35, 15, 82),
    ("Breece Hall", "RB", 24, 84.6, 75),
    ("Garrett Wilson", "WR", 25, 80.6, 85),
    ("Adonai Mitchell", "WR", 25, 33.6, 80),
    ("Mason Taylor", "TE", 25, 15, 80),
    ("Jason Sanders", "K", 25, 15, 80),
    ("Aaron Rodgers", "QB", 25, 15, 80),
    ("Kaleb Johnson", "RB", 25, 15, 80),
    ("Jaylen Warren", "RB", 25, 73.5, 80),
    ("DK Metcalf", "WR", 28, 69.9, 82),
    ("Roman Wilson", "WR", 25, 15, 80),
    ("Pat Freiermuth", "TE", 25, 15, 80),
    ("Chris Boswell", "K", 25, 15, 80),
    ("Joe Burrow", "QB", 29, 73.9, 78),
    ("Chase Brown", "RB", 25, 91.4, 82),
    ("Ja'Marr Chase", "WR", 25, 98.2, 90),
    ("Tee Higgins", "WR", 27, 85.0, 78),
    ("Mike Gesicki", "TE", 25, 15, 80),
    ("Evan McPherson", "K", 25, 15, 80),
    ("C.J. Stroud", "QB", 24, 35.2, 88),
    ("Nico Collins", "WR", 26, 93.0, 82),
    ("Jayden Higgins", "WR", 25, 15, 80),
    ("Tank Dell", "WR", 25, 35.6, 80),
    ("Dalton Schultz", "TE", 25, 24.0, 80),
    ("Ka'imi Fairbairn", "K", 25, 15, 80),
    ("Bo Nix", "QB", 25, 49.1, 85),
    ("J.K. Dobbins", "RB", 25, 68.7, 80),
    ("RJ Harvey", "RB", 25, 68.3, 80),
    ("Courtland Sutton", "WR", 30, 62.7, 82),
    ("Marvin Mims Jr.", "WR", 25, 15, 80),
    ("Evan Engram", "TE", 31, 15, 75),
    ("Wil Lutz", "K", 25, 15, 80),
    ("Justin Herbert", "QB", 25, 65.9, 80),
    ("Omarion Hampton", "RB", 25, 89.4, 80),
    ("Ladd McConkey", "WR", 23, 83.8, 82),
    ("Quentin Johnston", "WR", 25, 55.1, 80),
    ("David Njoku", "TE", 25, 15, 80),
    ("Cameron Dicker", "K", 25, 15, 80),
    ("Sam Darnold", "QB", 29, 42.7, 80),
    ("Zach Charbonnet", "RB", 25, 41.1, 80),
    ("Jaxon Smith-Njigba", "WR", 25, 97.4, 80),
    ("Cooper Kupp", "WR", 25, 28.0, 80),
    ("Rashid Shaheed", "WR", 25, 43.1, 80),
    ("AJ Barner", "TE", 25, 15, 80),
    ("Jason Myers", "K", 25, 15, 80),
    ("Justin Jefferson", "WR", 26, 95.8, 88),
    ("Bijan Robinson", "RB", 23, 98.6, 88),
    ("Puka Nacua", "WR", 24, 97.8, 78),
    ("A.J. Brown", "WR", 28, 91.0, 82),
    ("Drake London", "WR", 24, 93.8, 85),
    ("Malik Nabers", "WR", 22, 90.6, 82),
    ("Marvin Harrison Jr.", "WR", 23, 71.5, 85),
    ("Brock Bowers", "TE", 23, 92.6, 85),
    ("Trey McBride", "TE", 26, 89.0, 85),
    ("Jonathan Taylor", "RB", 26, 96.2, 78),
    ("Trevor Lawrence", "QB", 26, 52.7, 82),
    ("Matthew Stafford", "QB", 37, 54.3, 75),
    ("Baker Mayfield", "QB", 30, 47.1, 85),
    ("Jayden Daniels", "QB", 25, 75.9, 78),
    ("Kyler Murray", "QB", 28, 49.9, 75),
    ("Rome Odunze", "WR", 23, 74.7, 85),
    ("Terry McLaurin", "WR", 30, 77.5, 85),
    ("Chris Olave", "WR", 25, 88.6, 75),
    ("James Cook", "RB", 25, 95.0, 82),
    ("Alvin Kamara", "RB", 30, 30.8, 78),
    ("Rhamondre Stevenson", "RB", 27, 69.5, 78),
    ("Caleb Williams", "QB", 24, 63.9, 82),
    ("Drake Maye", "QB", 24, 73.1, 85),
    ("J.J. McCarthy", "QB", 23, 15, 78),
    ("Isaiah Pacheco", "RB", 26, 15, 75),
    ("Jerry Jeudy", "WR", 26, 32.0, 82),
    ("Jauan Jennings", "WR", 28, 43.5, 80),
    ("Josh Downs", "WR", 24, 63.5, 82),
    ("Wan'Dale Robinson", "WR", 24, 59.5, 80),
    ("Ricky Pearsall", "WR", 24, 15, 78),
    ("Brian Thomas Jr.", "WR", 23, 72.3, 82),
    ("Tony Pollard", "RB", 28, 71.1, 80),
    ("Aaron Jones", "RB", 30, 60.7, 72),
    ("Najee Harris", "RB", 27, 15, 82),
    ("David Montgomery", "RB", 28, 81.8, 75),
    ("Zack Moss", "RB", 27, 15, 75),
    ("Rachaad White", "RB", 26, 61.1, 80),
    ("Zamir White", "RB", 25, 15, 82),
    ("Tyjae Spears", "RB", 24, 44.7, 78),
    ("Cade Otton", "TE", 26, 15, 82),
    ("Colston Loveland", "TE", 21, 85.4, 82),
    ("Isaiah Likely", "TE", 25, 39.9, 80),
    ("Fernando Mendoza", "QB", 22, 15, 85),
    ("Jeremiyah Love", "RB", 21, 86.6, 85),
    ("Ashton Jeanty", "RB", 24, 93.4, 82),
    ("Travis Etienne Jr.", "RB", 24, 88.2, 82),
    ("Kyren Williams", "RB", 24, 87.8, 82),
    ("Tetairoa Mcmillan", "WR", 24, 85.8, 82),
    ("Bucky Irving", "RB", 24, 83.0, 82),
    ("Cam Skattebo", "RB", 24, 82.6, 82),
    ("D'Andre Swift", "RB", 24, 81.4, 82),
    ("Quinshon Judkins", "RB", 24, 80.2, 82),
    ("Emeka Egbuka", "WR", 24, 79.8, 82),
    ("Mike Evans", "WR", 24, 79.4, 82),
    ("Bhayshul Tuten", "RB", 24, 79.1, 82),
    ("TreVeyon Henderson", "RB", 24, 78.7, 82),
    ("Davante Adams", "WR", 24, 78.3, 82),
    ("Jadarian Price", "RB", 24, 77.9, 82),
    ("Tyler Warren", "TE", 24, 76.7, 82),
    ("Luther Burden III", "WR", 24, 76.3, 82),
    ("Carnell Tate", "WR", 24, 75.5, 82),
    ("D.J. Moore", "WR", 24, 74.3, 82),
    ("Blake Corum", "RB", 24, 72.7, 82),
    ("Parker Washington", "WR", 24, 71.9, 82),
    ("Harold Fannin", "TE", 24, 70.7, 82),
    ("Rico Dowdle", "RB", 24, 70.3, 82),
    ("Jordan Addison", "WR", 24, 69.1, 82),
    ("Makai Lemon", "WR", 24, 67.1, 82),
    ("Michael Wilson", "WR", 24, 66.3, 82),
    ("Jonathon Brooks", "RB", 24, 65.5, 82),
    ("Kyle Monangai", "RB", 24, 64.7, 82),
    ("Chris Godwin", "WR", 24, 62.3, 82),
    ("Chuba Hubbard", "RB", 24, 61.9, 82),
    ("Kyle Pitts", "TE", 24, 61.5, 82),
    ("Jaxson Dart", "QB", 24, 60.3, 82),
    ("Jakobi Meyers", "WR", 24, 59.9, 82),
    ("Chris Rodriguez", "RB", 24, 59.1, 82),
    ("Kenneth Gainwell", "RB", 24, 58.7, 82),
    ("Romeo Doubs", "WR", 24, 58.3, 82),
    ("Stefon Diggs", "WR", 24, 57.5, 82),
    ("KC Concepcion", "WR", 24, 56.3, 82),
    ("Jordan Mason", "RB", 24, 55.9, 82),
    ("Jacory Croskey-Merritt", "RB", 24, 55.5, 82),
    ("Alec Pierce", "WR", 24, 54.7, 82),
    ("Keaton Mitchell", "RB", 24, 53.9, 82),
    ("Woody Marks", "RB", 24, 53.1, 82),
    ("Travis Hunter", "WR", 24, 51.1, 82),
    ("Michael Pittman Jr.", "WR", 24, 50.3, 82),
    ("Tyler Allgeier", "RB", 24, 47.9, 82),
    ("Omar Cooper Jr.", "WR", 24, 47.5, 82),
    ("Deebo Samuel", "WR", 24, 46.3, 82),
    ("Jalen Coker", "WR", 24, 45.9, 82),
    ("Dylan Sampson", "RB", 24, 45.5, 82),
    ("De'Zhaun Stribling", "WR", 24, 45.1, 82),
    ("Jordyn Tyson", "WR", 24, 44.3, 82),
    ("Oronde Gadsden II", "TE", 24, 43.9, 82),
    ("Tyler Shough", "QB", 24, 42.3, 82),
    ("Juwan Johnson", "TE", 24, 41.9, 82),
    ("Jonah Coleman", "RB", 24, 41.5, 82),
    ("Brian Robinson Jr.", "RB", 24, 40.7, 82),
    ("Keenan Allen", "WR", 24, 40.3, 82),
    ("Tre Tucker", "WR", 24, 39.6, 82),
    ("Denzel Boston", "WR", 24, 39.2, 82),
    ("Germie Bernard", "WR", 24, 38.8, 82),
    ("MarShawn Lloyd", "RB", 24, 38.4, 82),
    ("Braelon Allen", "RB", 24, 38.0, 82),
    ("Jalen McMillan", "WR", 24, 37.6, 82),
    ("Calvin Ridley", "WR", 24, 37.2, 82),
    ("Hunter Henry", "TE", 24, 36.4, 82),
    ("Ja'Kobi Lane", "WR", 24, 36.0, 82),
    ("Tre Harris", "WR", 24, 34.8, 82),
    ("Jalen Nailor", "WR", 24, 34.4, 82),
    ("Brenton Strange", "TE", 24, 34.0, 82),
    ("Pat Bryant", "WR", 24, 33.2, 82),
    ("Ted Hurst", "WR", 24, 32.8, 82),
    ("Daniel Jones", "QB", 24, 32.4, 82),
    ("T.J. Hockenson", "TE", 24, 30.4, 82),
    ("Kayshon Boutte", "WR", 24, 29.6, 82),
    ("Sean Tucker", "RB", 24, 29.2, 82),
    ("Malik Willis", "QB", 24, 28.8, 82),
    ("Zachariah Branch", "WR", 24, 28.4, 82),
    ("Dontayvion Wicks", "WR", 24, 27.2, 82),
    ("Nick Singleton", "RB", 24, 26.8, 82),
    ("Jaydon Blue", "RB", 24, 26.4, 82),
    ("Chig Okonkwo", "TE", 24, 26.0, 82),
    ("Kenyon Sadiq", "TE", 24, 25.6, 82),
    ("Bryce Lance", "WR", 24, 25.2, 82),
    ("Kaelon Black", "RB", 24, 24.8, 82),
    ("Tyrone Tracy Jr.", "RB", 24, 24.4, 82),
    ("DeVaughn Vele", "WR", 24, 23.6, 82),
    ("Kaytron Allen", "RB", 24, 23.2, 82),
    ("George Holani", "RB", 24, 22.8, 82),
    ("A.J. Barner", "TE", 24, 22.4, 82),
    ("Isaac TeSlaa", "WR", 24, 22.0, 82),
    ("Mike Washington", "RB", 24, 21.6, 82),
    ("Christian Kirk", "WR", 24, 20.8, 82),
    ("Jaylin Noel", "WR", 24, 20.4, 82),
    ("Darren Waller", "TE", 24, 20.0, 82),
]



# ---------------------------------------------------------------------------
# MLB — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

MLB_RAW: list[tuple[str, str, int, int, int]] = [
    ("William Contreras", "C", 27, 56.6, 85),
    ("Adley Rutschman", "C", 27, 15, 78),
    ("Cal Raleigh", "C", 29, 83.1, 85),
    ("Salvador Perez", "C", 35, 15, 78),
    ("J.T. Realmuto", "C", 34, 15, 72),
    ("Logan O'Hoppe", "C", 25, 15, 78),
    ("Shohei Ohtani", "DH", 31, 99.0, 82),
    ("Aaron Judge", "OF", 33, 98.5, 82),
    ("Juan Soto", "OF", 27, 96.9, 88),
    ("Bobby Witt Jr.", "SS", 25, 97.9, 90),
    ("Jose Ramirez", "3B", 33, 95.3, 88),
    ("Mookie Betts", "SS", 33, 63.5, 82),
    ("Ronald Acuna Jr.", "OF", 28, 97.4, 68),
    ("Gunnar Henderson", "SS", 24, 91.6, 88),
    ("Vladimir Guerrero Jr.", "1B", 27, 94.8, 88),
    ("Freddie Freeman", "1B", 36, 81.0, 82),
    ("Yordan Alvarez", "DH", 28, 90.5, 70),
    ("Kyle Tucker", "OF", 28, 92.6, 85),
    ("Paul Skenes", "SP", 23, 93.7, 85),
    ("Tarik Skubal", "SP", 28, 95.8, 88),
    ("Zack Wheeler", "SP", 35, 51.3, 82),
    ("Gerrit Cole", "SP", 35, 20.0, 65),
    ("Corbin Burnes", "SP", 31, 15, 85),
    ("Spencer Strider", "SP", 27, 15, 60),
    ("Mason Miller", "RP", 27, 64.5, 75),
    ("Corbin Carroll", "OF", 25, 94.2, 82),
    ("Julio Rodriguez", "OF", 25, 93.2, 85),
    ("Elly De La Cruz", "SS", 23, 96.3, 85),
    ("Matt Olson", "1B", 32, 72.0, 88),
    ("Francisco Lindor", "SS", 32, 88.4, 88),
    ("Trea Turner", "SS", 33, 85.2, 85),
    ("Manny Machado", "3B", 33, 77.8, 82),
    ("Rafael Devers", "3B", 29, 68.8, 80),
    ("Austin Riley", "3B", 28, 79.4, 80),
    ("Jackson Chourio", "OF", 22, 89.5, 85),
    ("James Wood", "OF", 23, 87.9, 85),
    ("Jackson Merrill", "OF", 22, 81.5, 85),
    ("Riley Greene", "OF", 25, 66.1, 82),
    ("Bryce Harper", "1B", 33, 75.1, 72),
    ("Pete Alonso", "1B", 31, 83.6, 85),
    ("Ketel Marte", "2B", 32, 84.7, 78),
    ("Marcus Semien", "2B", 35, 15, 88),
    ("Jazz Chisholm Jr.", "2B", 28, 82.0, 75),
    ("Ozzie Albies", "2B", 28, 15, 78),
    ("Jose Altuve", "2B", 35, 59.8, 82),
    ("CJ Abrams", "SS", 25, 73.0, 85),
    ("Bo Bichette", "SS", 27, 74.1, 75),
    ("Xander Bogaerts", "SS", 33, 15, 78),
    ("Anthony Volpe", "SS", 24, 15, 85),
    ("Wyatt Langford", "OF", 23, 85.7, 80),
    ("Steven Kwan", "OF", 27, 23.7, 88),
    ("Ian Happ", "OF", 31, 49.7, 85),
    ("Christian Yelich", "OF", 33, 52.9, 72),
    ("George Springer", "OF", 36, 59.2, 75),
    ("Teoscar Hernandez", "OF", 33, 61.4, 82),
    ("Anthony Santander", "OF", 31, 15, 82),
    ("Michael Harris II", "OF", 24, 78.3, 78),
    ("Nolan Arenado", "3B", 34, 15, 82),
    ("Alex Bregman", "3B", 31, 44.4, 78),
    ("Yoshinobu Yamamoto", "SP", 27, 80.4, 82),
    ("Hunter Greene", "SP", 26, 72.5, 75),
    ("Dylan Cease", "SP", 30, 53.4, 85),
    ("Max Fried", "SP", 32, 77.3, 85),
    ("Framber Valdez", "SP", 32, 62.9, 85),
    ("Logan Gilbert", "SP", 28, 87.3, 85),
    ("Chris Sale", "SP", 37, 69.8, 65),
    ("Ranger Suarez", "SP", 30, 15, 80),
    ("Sonny Gray", "SP", 36, 25.8, 78),
    ("Kevin Gausman", "SP", 35, 29.5, 85),
    ("Blake Snell", "SP", 33, 73.6, 72),
    ("Freddy Peralta", "SP", 29, 42.8, 82),
    ("Josh Hader", "RP", 31, 62.4, 85),
    ("Edwin Diaz", "RP", 31, 60.8, 78),
    ("Felix Bautista", "RP", 30, 15, 65),
    ("Devin Williams", "RP", 30, 49.2, 78),
    ("Ryan Helsley", "RP", 31, 31.1, 80),
    ("Raisel Iglesias", "RP", 35, 24.2, 82),
    ("Camilo Doval", "RP", 28, 15, 78),
    ("Byron Buxton", "OF", 32, 52.3, 55),
    ("Luis Robert Jr.", "OF", 28, 56.1, 65),
    ("Randy Arozarena", "OF", 30, 34.8, 78),
    ("Jarren Duran", "OF", 29, 79.9, 82),
    ("Brenton Doyle", "OF", 27, 38.6, 82),
    ("Lawrence Butler", "OF", 25, 15, 80),
    ("Colton Cowser", "OF", 25, 15, 80),
    ("Jasson Dominguez", "OF", 22, 15, 78),
    ("Ceddanne Rafaela", "OF", 25, 26.9, 85),
    ("Jung Hoo Lee", "OF", 27, 37.5, 78),
    ("Spencer Torkelson", "1B", 26, 15, 82),
    ("Christian Walker", "1B", 34, 15, 82),
    ("Josh Naylor", "1B", 28, 60.3, 82),
    ("Triston Casas", "1B", 26, 15, 72),
    ("Nathaniel Lowe", "1B", 30, 15, 82),
    ("Gleyber Torres", "2B", 28, 15, 80),
    ("Brice Turang", "2B", 25, 74.6, 85),
    ("Andres Gimenez", "2B", 27, 15, 82),
    ("Luis Arraez", "2B", 28, 15, 88),
    ("Willy Adames", "SS", 29, 40.1, 85),
    ("Ha-Seong Kim", "SS", 30, 15, 78),
    ("Dansby Swanson", "SS", 31, 15, 78),
    ("Oneil Cruz", "SS", 26, 67.7, 70),
    ("Jordan Westburg", "3B", 26, 47.6, 78),
    ("Junior Caminero", "3B", 22, 86.8, 82),
    ("Max Muncy", "3B", 35, 20.5, 72),
    ("Ryan McMahon", "3B", 30, 15, 82),
    ("Shane Bieber", "SP", 30, 15, 65),
    ("Jack Flaherty", "SP", 29, 15, 75),
    ("Aaron Nola", "SP", 32, 15, 82),
    ("Zac Gallen", "SP", 30, 15, 82),
    ("Cristopher Sanchez", "SP", 28, 86.3, 85),
    ("Joe Ryan", "SP", 29, 65.1, 85),
    ("Garrett Crochet", "SP", 26, 88.9, 80),
    ("MacKenzie Gore", "SP", 26, 15, 82),
    ("Bryce Miller", "SP", 26, 15, 82),
    ("Michael King", "SP", 30, 15, 78),
    ("Jhoan Duran", "RP", 27, 54.5, 82),
    ("Andres Munoz", "RP", 25, 51.8, 80),
    ("Robert Suarez", "RP", 34, 15, 82),
    ("Kenley Jansen", "RP", 38, 15, 78),
    ("Fernando Tatis Jr.", "OF", 27, 92.1, 82),
    ("Nick Kurtz", "1B", 27, 91.0, 82),
    ("Zach Neto", "SS", 27, 90.0, 82),
    ("Kyle Schwarber", "DH", 27, 84.2, 82),
    ("Pete Crow-Armstrong", "OF", 27, 82.6, 82),
    ("Bryan Woo", "SP", 27, 78.9, 82),
    ("George Kirby", "SP", 27, 76.7, 82),
    ("Brent Rooker", "OF", 27, 76.2, 82),
    ("Jacob deGrom", "SP", 27, 75.7, 82),
    ("Roman Anthony", "OF", 27, 71.4, 82),
    ("Corey Seager", "SS", 27, 70.9, 82),
    ("Seiya Suzuki", "OF", 27, 70.4, 82),
    ("Jeremy Pena", "SS", 27, 69.3, 82),
    ("Hunter Brown", "SP", 27, 68.2, 82),
    ("Cole Ragans", "SP", 27, 67.2, 82),
    ("Geraldo Perdomo", "SS", 27, 66.7, 82),
    ("Cody Bellinger", "OF", 27, 65.6, 82),
    ("Logan Webb", "SP", 27, 64.0, 82),
    ("Tyler Soderstrom", "1B", 27, 61.9, 82),
    ("Dylan Crews", "OF", 27, 58.7, 82),
    ("Aroldis Chapman", "RP", 27, 58.2, 82),
    ("Trevor Story", "SS", 27, 57.6, 82),
    ("Jacob Wilson", "SS", 27, 57.1, 82),
    ("Cade Smith", "RP", 27, 55.5, 82),
    ("Spencer Schwellenbach", "SP", 27, 55.0, 82),
    ("Nico Hoerner", "2B", 27, 53.9, 82),
    ("Maikel Garcia", "3B", 27, 50.8, 82),
    ("Mike Trout", "OF", 27, 50.2, 82),
    ("Michael Busch", "1B", 27, 48.6, 82),
    ("Jacob Misiorowski", "SP", 27, 48.1, 82),
    ("Ben Rice", "C", 27, 47.0, 82),
    ("Kyle Bradish", "SP", 27, 46.5, 82),
    ("Willson Contreras", "1B", 27, 46.0, 82),
    ("Drew Rasmussen", "SP", 27, 45.4, 82),
    ("Vinnie Pasquantino", "1B", 27, 44.9, 82),
    ("Alec Bohm", "3B", 27, 43.9, 82),
    ("Jonathan Aranda", "1B", 27, 43.3, 82),
    ("David Bednar", "RP", 27, 42.3, 82),
    ("Isaac Paredes", "3B", 27, 41.7, 82),
    ("Eury Perez", "SP", 27, 41.2, 82),
    ("Bryan Reynolds", "OF", 27, 40.7, 82),
    ("Jesus Luzardo", "SP", 27, 39.6, 82),
    ("Jo Adell", "OF", 27, 39.1, 82),
    ("Jac Caglianone", "OF", 27, 38.0, 82),
    ("Joe Musgrove", "SP", 27, 37.0, 82),
    ("Jeff Hoffman", "RP", 27, 36.4, 82),
    ("Nolan McLean", "SP", 27, 35.9, 82),
    ("Alec Burleson", "OF", 27, 35.4, 82),
    ("Gavin Williams", "SP", 27, 34.3, 82),
    ("Griffin Jax", "RP", 27, 33.8, 82),
    ("Agustin Ramirez", "C", 27, 33.3, 82),
    ("Ezequiel Tovar", "SS", 27, 32.7, 82),
    ("Tanner Bibee", "SP", 27, 32.2, 82),
    ("Xavier Edwards", "SS", 27, 31.7, 82),
    ("Andy Pages", "OF", 27, 30.6, 82),
    ("Nick Pivetta", "SP", 27, 30.1, 82),
    ("Yandy Diaz", "1B", 27, 29.0, 82),
    ("Shea Langeliers", "C", 27, 28.5, 82),
    ("Luke Keaschall", "2B", 27, 28.0, 82),
    ("Brandon Lowe", "2B", 27, 27.4, 82),
    ("Matt Chapman", "3B", 27, 26.4, 82),
    ("Marcell Ozuna", "DH", 27, 25.3, 82),
    ("Josh Lowe", "OF", 27, 24.8, 82),
    ("Jackson Holliday", "2B", 27, 23.2, 82),
    ("Trevor Megill", "RP", 27, 22.7, 82),
    ("Kyle Stowers", "OF", 27, 22.1, 82),
    ("Brandon Nimmo", "OF", 27, 21.6, 82),
    ("Tyler Glasnow", "SP", 27, 21.1, 82),
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
    ("Alex Condon", "C", 3, 87, 85),
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
    ("Cayden Boozer", "PG", 1, 90, 82),
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
    ("Caleb Holt", "SG", 1, 88, 82),
    ("Jason Crowe", "PG", 1, 84, 82),
    ("Cameron Williams", "PF", 1, 82, 82),
    ("Milan Momcilovic", "PF", 3, 80, 82),
    ("John Blackwell", "SG", 3, 79, 82),
    ("Donnie Freeman", "PF", 3, 79, 82),
    ("Jack Burton", "SF", 4, 78, 78),
    ("Quentin Coleman", "SG", 1, 78, 80),
    ("Jaxon Richardson", "SF", 1, 77, 80),
    ("Juke Harris", "SG", 2, 82, 80),
    ("Toni Bryant", "PF", 1, 76, 80),
    ("Tylen Riley", "PG", 4, 76, 82),
    ("Taylen Kinney", "SG", 1, 75, 80),
    ("Dra Gibbs-Lawhorn", "SG", 4, 75, 80),
    ("Cameron Holmes", "PF", 1, 74, 78),
    ("Jamier Jones", "SG", 2, 74, 80),
    # ---- 2026-27 additional backfill (returning stars / transfers) ----
    ("Thomas Haugh", "PF", 4, 97, 85),
    ("Jeremy Fears Jr.", "PG", 3, 93, 85),
    ("Markus Burton", "PG", 4, 83, 82),
    ("Urban Klavzar", "SG", 2, 78, 82),
    ("Isaiah Brown", "SF", 2, 77, 82),
    ("Tyler Tanner", "PG", 3, 86, 82),
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
    ("Jeremiah Smith", "WR", 3, 99.0, 88),
    ("Arch Manning", "QB", 2, 88.5, 82),
    ("Ryan Williams", "WR", 2, 15, 82),
    ("LaNorris Sellers", "QB", 2, 15, 85),
    ("Julian Sayin", "QB", 2, 75.3, 82),
    ("DJ Lagway", "QB", 2, 15, 75),
    ("Dante Moore", "QB", 2, 97.7, 82),
    ("Dylan Raiola", "QB", 2, 15, 82),
    ("Sam Leavitt", "QB", 3, 34.5, 85),
    ("Avery Johnson", "QB", 4, 15, 85),
    ("Rocco Becht", "QB", 4, 15, 84),
    ("CJ Baxter", "RB", 3, 15, 78),
    ("Makhi Hughes", "RB", 3, 15, 82),
    ("Nyck Harbor", "WR", 4, 15, 82),
    ("Duce Robinson", "WR", 3, 62.1, 84),
    ("Evan Stewart", "WR", 4, 15, 75),
    ("Nic Anderson", "WR", 4, 15, 75),
    ("Luke Kromenhoek", "QB", 2, 15, 82),
    ("Cutter Boley", "QB", 2, 15, 80),
    ("Marcel Reed", "QB", 2, 15, 82),
    ("Noah Fifita", "QB", 4, 15, 82),
    ("Demond Williams Jr.", "QB", 2, 15, 85),
    ("Bryce Underwood", "QB", 1, 15, 82),
    ("Air Noland", "QB", 1, 15, 80),
    ("Husan Longstreet", "QB", 1, 15, 82),
    ("Justice Haynes", "RB", 2, 15, 82),
    ("Darius Taylor", "RB", 3, 15, 82),
    ("Quintrevion Wisner", "RB", 3, 15, 82),
    ("Roderick Robinson II", "RB", 3, 15, 82),
    ("Nate Frazier", "RB", 2, 15, 82),
    ("Jerrick Gibson", "RB", 1, 15, 82),
    ("Rueben Owens II", "RB", 2, 15, 80),
    ("Eric Singleton Jr.", "WR", 3, 15, 82),
    ("Winston Watkins Jr.", "WR", 3, 15, 80),
    ("Vernell Brown III", "WR", 2, 15, 82),
    ("Dakorien Moore", "WR", 1, 15, 82),
    ("Chris Henry Jr.", "WR", 2, 15, 78),
    ("Cam Coleman", "WR", 2, 84.5, 85),
    ("Ryan Wingo", "WR", 2, 15, 80),
    ("Rico Flores Jr.", "WR", 2, 15, 82),
    ("Jaime Ffrench", "WR", 4, 15, 80),
    ("Walker Lyons", "TE", 3, 15, 82),
    ("C.J. Carr", "QB", 3, 76.6, 85),
    ("Darian Mensah", "QB", 3, 83.2, 82),
    ("Ahmad Hardy", "RB", 3, 67.4, 85),
    ("John Mateer", "QB", 4, 15, 78),
    ("Trinidad Chambliss", "QB", 4, 96.4, 82),
    ("Josh Hoover", "QB", 4, 15, 82),
    ("Gunner Stockton", "QB", 3, 15, 82),
    ("Kewan Lacy", "RB", 3, 89.8, 82),
    ("Jayden Maiava", "QB", 4, 85.8, 80),
    ("Faizon Brandon", "QB", 1, 15, 82),
    ("Mark Fletcher", "RB", 2, 74.0, 80),
    ("Savion Hiter", "RB", 1, 15, 82),
    ("Keelon Russell", "QB", 2, 15, 82),
    ("EJ Crowell", "RB", 1, 15, 82),
    ("Malachi Toney", "WR", 2, 95.0, 82),
    ("Drew Mestemaker", "QB", 1, 87.2, 82),
    ("Kevin Jennings", "QB", 3, 66.1, 82),
    ("KJ Duff", "WR", 3, 47.6, 82),
    ("Mario Craver", "WR", 3, 41.1, 82),
    ("Caleb Hawkins", "RB", 2, 39.8, 82),
    ("Jadan Baugh", "RB", 2, 38.4, 82),
    ("LJ Martin", "RB", 3, 26.6, 82),
    ("Trey'Dez Green", "TE", 2, 25.3, 82),
    ("Jamari Johnson", "TE", 3, 24.0, 82),
    ("DeSean Bishop", "RB", 3, 21.3, 82),
    ("Braylon Staley", "WR", 2, 20.0, 82),
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
        if sport in COLLEGE_VALUE_DISCOUNT:
            _discount_draft_value(players, COLLEGE_VALUE_DISCOUNT[sport])
        pool.extend(players)
    pool.sort(key=lambda p: p.draft_value, reverse=True)
    return pool


# College players carry far more projection uncertainty than pro players in a
# one-season redraft context (no track record against pro competition, huge
# year-to-year variance), so their percentile-ranked draft_value is scaled
# down after normalization — keeps their internal ordering intact while
# ensuring even a college pool's best player can't outrank the pro sports'
# genuine stars on the combined board.
COLLEGE_VALUE_DISCOUNT = {"CBB": 55.0, "CFB": 55.0}


def _discount_draft_value(players: list[Player], cap: float) -> None:
    for p in players:
        p.draft_value = round(1.0 + (p.draft_value - 1.0) / 98.0 * (cap - 1.0), 1)


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
