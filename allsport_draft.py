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


# (peak_age, decline_per_year) — pro sports only. Rough career-arc shape per
# sport: NFL bodies decline fastest, MLB hitters/pitchers age gentlest.
AGE_CURVES: dict[str, tuple[int, int]] = {
    "NFL": (27, 8),
    "MLB": (29, 5),
    "NHL": (27, 6),
    "NBA": (27, 6),
}

# College sports have no real "aging" story — class_year (1=Fr .. 4=Sr) gets
# a mild bump for proven upperclassmen instead of a decline curve.
CLASS_YEAR_FACTOR: dict[int, int] = {1: 74, 2: 82, 3: 90, 4: 95}

COLLEGE_SPORTS = {"CBB", "CFB"}


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

    def __post_init__(self) -> None:
        if self.sport in COLLEGE_SPORTS:
            factor = CLASS_YEAR_FACTOR.get(self.class_year or 1, 74)
        else:
            peak, decay = AGE_CURVES.get(self.sport, (27, 6))
            factor = max(0, 100 - max(0, (self.age or peak) - peak) * decay)
        self.score = round(self.skill * 0.70 + factor * 0.15 + self.health * 0.15, 2)

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
    # ---- Superstars (90-99) ----
    ("Patrick Mahomes", "QB", 30, 98, 85),
    ("Josh Allen", "QB", 29, 97, 88),
    ("Lamar Jackson", "QB", 28, 96, 85),
    ("Joe Burrow", "QB", 29, 95, 78),
    ("Justin Jefferson", "WR", 26, 96, 88),
    ("Ja'Marr Chase", "WR", 25, 96, 90),
    ("CeeDee Lamb", "WR", 26, 94, 88),
    ("Tyreek Hill", "WR", 31, 92, 82),
    ("Christian McCaffrey", "RB", 29, 93, 62),
    ("Saquon Barkley", "RB", 28, 94, 82),
    ("Bijan Robinson", "RB", 23, 92, 88),
    ("Myles Garrett", "DE", 30, 96, 88),
    ("Micah Parsons", "LB", 26, 95, 85),
    ("T.J. Watt", "LB", 31, 94, 80),
    ("Travis Kelce", "TE", 36, 90, 75),
    ("Jalen Hurts", "QB", 27, 91, 85),
    ("C.J. Stroud", "QB", 24, 91, 88),
    ("Nick Bosa", "DE", 28, 93, 78),
    ("Sauce Gardner", "CB", 25, 92, 88),
    ("Amon-Ra St. Brown", "WR", 26, 92, 90),
    # ---- All-Pro tier (80-89) ----
    ("Puka Nacua", "WR", 24, 89, 78),
    ("A.J. Brown", "WR", 28, 90, 82),
    ("Garrett Wilson", "WR", 25, 88, 85),
    ("Drake London", "WR", 24, 87, 85),
    ("Nico Collins", "WR", 26, 87, 82),
    ("Malik Nabers", "WR", 22, 88, 82),
    ("Marvin Harrison Jr.", "WR", 23, 86, 85),
    ("Brock Bowers", "TE", 23, 90, 85),
    ("George Kittle", "TE", 32, 87, 80),
    ("Trey McBride", "TE", 26, 87, 85),
    ("Derrick Henry", "RB", 31, 89, 78),
    ("Jahmyr Gibbs", "RB", 23, 88, 85),
    ("Josh Jacobs", "RB", 27, 85, 80),
    ("Kenneth Walker III", "RB", 25, 82, 78),
    ("De'Von Achane", "RB", 24, 85, 78),
    ("Jonathan Taylor", "RB", 26, 86, 78),
    ("Trevor Lawrence", "QB", 26, 82, 82),
    ("Jordan Love", "QB", 27, 83, 82),
    ("Dak Prescott", "QB", 32, 83, 75),
    ("Jared Goff", "QB", 31, 84, 88),
    ("Matthew Stafford", "QB", 37, 83, 75),
    ("Baker Mayfield", "QB", 30, 82, 85),
    ("Bo Nix", "QB", 25, 81, 85),
    ("Jayden Daniels", "QB", 25, 88, 78),
    ("Kyler Murray", "QB", 28, 80, 75),
    ("Aidan Hutchinson", "DE", 25, 90, 65),
    ("Maxx Crosby", "DE", 28, 92, 88),
    ("Will Anderson Jr.", "LB", 24, 87, 85),
    ("Fred Warner", "LB", 29, 91, 88),
    ("Roquan Smith", "LB", 28, 88, 85),
    ("Patrick Surtain II", "CB", 25, 93, 88),
    ("Derwin James", "S", 29, 88, 72),
    ("Antoine Winfield Jr.", "S", 27, 87, 82),
    ("Kyle Hamilton", "S", 25, 88, 85),
    ("Quinnen Williams", "DT", 28, 88, 85),
    ("Chris Jones", "DT", 31, 89, 82),
    ("Denzel Ward", "CB", 29, 82, 75),
    ("Zack Baun", "LB", 28, 84, 85),
    ("Brian Burns", "DE", 27, 85, 82),
    # ---- Quality starters (65-79) ----
    ("Rome Odunze", "WR", 23, 78, 85),
    ("Tee Higgins", "WR", 27, 82, 78),
    ("DK Metcalf", "WR", 28, 83, 82),
    ("Terry McLaurin", "WR", 30, 82, 85),
    ("Zay Flowers", "WR", 25, 80, 82),
    ("Chris Olave", "WR", 25, 79, 75),
    ("Jaylen Waddle", "WR", 27, 80, 82),
    ("Courtland Sutton", "WR", 30, 78, 82),
    ("James Cook", "RB", 25, 80, 82),
    ("Chase Brown", "RB", 25, 78, 82),
    ("Alvin Kamara", "RB", 30, 80, 78),
    ("Breece Hall", "RB", 24, 79, 75),
    ("Rhamondre Stevenson", "RB", 27, 74, 78),
    ("Sam LaPorta", "TE", 24, 82, 85),
    ("Evan Engram", "TE", 31, 76, 75),
    ("Geno Smith", "QB", 35, 76, 82),
    ("Sam Darnold", "QB", 29, 76, 80),
    ("Caleb Williams", "QB", 24, 80, 82),
    ("Drake Maye", "QB", 24, 82, 85),
    ("J.J. McCarthy", "QB", 23, 76, 78),
    ("Isaiah Pacheco", "RB", 26, 76, 75),
    ("Xavien Howard", "CB", 32, 74, 70),
    ("Trevon Diggs", "CB", 27, 78, 68),
    ("Za'Darius Smith", "LB", 33, 74, 70),
    # ---- Depth / role players (55-78) ----
    ("Rashee Rice", "WR", 25, 78, 78),
    ("Jameson Williams", "WR", 24, 78, 75),
    ("Jerry Jeudy", "WR", 26, 74, 82),
    ("Jauan Jennings", "WR", 28, 72, 80),
    ("Khalil Shakir", "WR", 25, 74, 85),
    ("Josh Downs", "WR", 24, 72, 82),
    ("Wan'Dale Robinson", "WR", 24, 70, 80),
    ("Ricky Pearsall", "WR", 24, 72, 78),
    ("Xavier Worthy", "WR", 22, 76, 80),
    ("Ladd McConkey", "WR", 23, 78, 82),
    ("Brian Thomas Jr.", "WR", 23, 80, 82),
    ("Keon Coleman", "WR", 23, 72, 82),
    ("Javonte Williams", "RB", 25, 72, 75),
    ("Tony Pollard", "RB", 28, 74, 80),
    ("Aaron Jones", "RB", 30, 74, 72),
    ("Najee Harris", "RB", 27, 74, 82),
    ("David Montgomery", "RB", 28, 74, 75),
    ("Zack Moss", "RB", 27, 68, 75),
    ("Rachaad White", "RB", 26, 70, 80),
    ("Zamir White", "RB", 25, 70, 82),
    ("Tyjae Spears", "RB", 24, 70, 78),
    ("Cade Otton", "TE", 26, 70, 82),
    ("Dalton Kincaid", "TE", 25, 76, 78),
    ("Colston Loveland", "TE", 21, 74, 82),
    ("Tucker Kraft", "TE", 24, 74, 85),
    ("Isaiah Likely", "TE", 25, 72, 80),
    ("Cameron Heyward", "DT", 36, 78, 78),
    ("Dexter Lawrence", "DT", 27, 84, 82),
    ("Jalen Carter", "DT", 24, 84, 82),
    ("Vita Vea", "DT", 30, 80, 80),
    ("Josh Sweat", "DE", 28, 78, 80),
    ("Danielle Hunter", "DE", 31, 80, 82),
    ("Trey Hendrickson", "DE", 30, 84, 78),
    ("Khalil Mack", "LB", 34, 78, 72),
    ("Bobby Wagner", "LB", 35, 74, 82),
    ("Foyesade Oluokun", "LB", 29, 74, 88),
    ("Devin White", "LB", 27, 70, 78),
    ("Jordyn Brooks", "LB", 27, 74, 82),
    ("Jaire Alexander", "CB", 28, 78, 65),
    ("Jaylon Johnson", "CB", 26, 80, 82),
    ("Marlon Humphrey", "CB", 29, 78, 75),
    ("Charvarius Ward", "CB", 29, 74, 82),
    ("Christian Gonzalez", "CB", 23, 82, 78),
    ("Terrion Arnold", "CB", 22, 74, 82),
    ("Budda Baker", "S", 29, 78, 82),
    ("Jessie Bates III", "S", 28, 76, 85),
    ("Jordan Poyer", "S", 34, 68, 80),
    ("Xavier McKinney", "S", 26, 76, 82),
    ("Camryn Bynum", "S", 26, 72, 85),
    ("Trent Williams", "OT", 37, 86, 70),
    ("Penei Sewell", "OT", 24, 86, 85),
    ("Laremy Tunsil", "OT", 31, 80, 80),
    ("Lane Johnson", "OT", 35, 80, 68),
    ("Tristan Wirfs", "OT", 26, 84, 78),
    ("Zack Martin", "OG", 34, 82, 78),
    ("Joel Bitonio", "OG", 34, 78, 82),
    ("Quenton Nelson", "OG", 29, 80, 80),
    ("Creed Humphrey", "C", 26, 82, 85),
    ("Frank Ragnow", "C", 29, 76, 72),
    # ---- 2026 NFL Draft rookies (78-88) ----
    ("Fernando Mendoza", "QB", 22, 84, 85),
    ("David Bailey", "LB", 21, 82, 85),
    ("Jeremiyah Love", "RB", 21, 85, 85),
    ("Arvell Reese", "LB", 21, 80, 85),
    ("Sonny Styles", "LB", 21, 80, 85),
    ("Spencer Fano", "OT", 20, 82, 88),
    ("Francis Mauigoa", "OG", 21, 81, 85),
    ("Caleb Downs", "S", 21, 86, 88),
]


# ---------------------------------------------------------------------------
# MLB — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

MLB_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Elite (90-99) ----
    ("Shohei Ohtani", "DH", 31, 99, 82),
    ("Aaron Judge", "OF", 33, 97, 82),
    ("Juan Soto", "OF", 27, 95, 88),
    ("Bobby Witt Jr.", "SS", 25, 94, 90),
    ("Jose Ramirez", "3B", 33, 92, 88),
    ("Mookie Betts", "SS", 33, 91, 82),
    ("Ronald Acuna Jr.", "OF", 28, 92, 68),
    ("Gunnar Henderson", "SS", 24, 91, 88),
    ("Vladimir Guerrero Jr.", "1B", 27, 90, 88),
    ("Freddie Freeman", "1B", 36, 90, 82),
    ("Yordan Alvarez", "DH", 28, 90, 70),
    ("Kyle Tucker", "OF", 28, 90, 85),
    ("Paul Skenes", "SP", 23, 96, 85),
    ("Tarik Skubal", "SP", 28, 95, 88),
    ("Zack Wheeler", "SP", 35, 92, 82),
    ("Gerrit Cole", "SP", 35, 91, 65),
    ("Corbin Burnes", "SP", 31, 90, 85),
    ("Spencer Strider", "SP", 27, 90, 60),
    ("Emmanuel Clase", "RP", 27, 92, 88),
    ("Mason Miller", "RP", 27, 90, 75),
    # ---- Quality (75-89) ----
    ("Corbin Carroll", "OF", 25, 88, 82),
    ("Julio Rodriguez", "OF", 25, 88, 85),
    ("Elly De La Cruz", "SS", 23, 89, 85),
    ("Matt Olson", "1B", 32, 85, 88),
    ("Francisco Lindor", "SS", 32, 88, 88),
    ("Trea Turner", "SS", 33, 85, 85),
    ("Manny Machado", "3B", 33, 83, 82),
    ("Rafael Devers", "3B", 29, 84, 80),
    ("Austin Riley", "3B", 28, 82, 80),
    ("Jackson Chourio", "OF", 22, 83, 85),
    ("James Wood", "OF", 23, 83, 85),
    ("Jackson Merrill", "OF", 22, 82, 85),
    ("Riley Greene", "OF", 25, 81, 82),
    ("Bryce Harper", "1B", 33, 87, 72),
    ("Pete Alonso", "1B", 31, 82, 85),
    ("William Contreras", "C", 27, 82, 85),
    ("Adley Rutschman", "C", 27, 85, 78),
    ("Cal Raleigh", "C", 29, 87, 85),
    ("Ketel Marte", "2B", 32, 84, 78),
    ("Marcus Semien", "2B", 35, 78, 88),
    ("Jazz Chisholm Jr.", "2B", 28, 78, 75),
    ("Ozzie Albies", "2B", 28, 78, 78),
    ("Jose Altuve", "2B", 35, 82, 82),
    ("CJ Abrams", "SS", 25, 80, 85),
    ("Bo Bichette", "SS", 27, 78, 75),
    ("Xander Bogaerts", "SS", 33, 78, 78),
    ("Anthony Volpe", "SS", 24, 76, 85),
    ("Wyatt Langford", "OF", 23, 78, 80),
    ("Steven Kwan", "OF", 27, 79, 88),
    ("Ian Happ", "OF", 31, 77, 85),
    ("Christian Yelich", "OF", 33, 76, 72),
    ("George Springer", "OF", 36, 74, 75),
    ("Teoscar Hernandez", "OF", 33, 79, 82),
    ("Anthony Santander", "OF", 31, 76, 82),
    ("Michael Harris II", "OF", 24, 76, 78),
    ("Nolan Arenado", "3B", 34, 76, 82),
    ("Alex Bregman", "3B", 31, 80, 78),
    ("Yoshinobu Yamamoto", "SP", 27, 88, 82),
    ("Hunter Greene", "SP", 26, 86, 75),
    ("Dylan Cease", "SP", 30, 84, 85),
    ("Max Fried", "SP", 32, 86, 85),
    ("Framber Valdez", "SP", 32, 87, 85),
    ("Logan Gilbert", "SP", 28, 85, 85),
    ("Chris Sale", "SP", 37, 88, 65),
    ("Ranger Suarez", "SP", 30, 80, 80),
    ("Sonny Gray", "SP", 36, 79, 78),
    ("Kevin Gausman", "SP", 35, 79, 85),
    ("Blake Snell", "SP", 33, 83, 72),
    ("Freddy Peralta", "SP", 29, 79, 82),
    ("Josh Hader", "RP", 31, 89, 85),
    ("Edwin Diaz", "RP", 31, 88, 78),
    ("Felix Bautista", "RP", 30, 85, 65),
    ("Devin Williams", "RP", 30, 82, 78),
    ("Ryan Helsley", "RP", 31, 82, 80),
    ("Raisel Iglesias", "RP", 35, 78, 82),
    ("Camilo Doval", "RP", 28, 78, 78),
    # ---- Depth / role players (55-78) ----
    ("Byron Buxton", "OF", 32, 76, 55),
    ("Luis Robert Jr.", "OF", 28, 74, 65),
    ("Randy Arozarena", "OF", 30, 72, 78),
    ("Jarren Duran", "OF", 29, 76, 82),
    ("Brenton Doyle", "OF", 27, 72, 82),
    ("Lawrence Butler", "OF", 25, 72, 80),
    ("Colton Cowser", "OF", 25, 70, 80),
    ("Jasson Dominguez", "OF", 22, 72, 78),
    ("Ceddanne Rafaela", "OF", 25, 70, 85),
    ("Jung Hoo Lee", "OF", 27, 72, 78),
    ("Spencer Torkelson", "1B", 26, 70, 82),
    ("Christian Walker", "1B", 34, 70, 82),
    ("Josh Naylor", "1B", 28, 74, 82),
    ("Triston Casas", "1B", 26, 72, 72),
    ("Nathaniel Lowe", "1B", 30, 68, 82),
    ("Gleyber Torres", "2B", 28, 74, 80),
    ("Brice Turang", "2B", 25, 68, 85),
    ("Andres Gimenez", "2B", 27, 72, 82),
    ("Luis Arraez", "2B", 28, 76, 88),
    ("Willy Adames", "SS", 29, 78, 85),
    ("Ha-Seong Kim", "SS", 30, 74, 78),
    ("Dansby Swanson", "SS", 31, 76, 78),
    ("Oneil Cruz", "SS", 26, 78, 70),
    ("Jordan Westburg", "3B", 26, 74, 78),
    ("Junior Caminero", "3B", 22, 76, 82),
    ("Max Muncy", "3B", 35, 72, 72),
    ("Ryan McMahon", "3B", 30, 70, 82),
    ("Salvador Perez", "C", 35, 76, 78),
    ("J.T. Realmuto", "C", 34, 76, 72),
    ("Logan O'Hoppe", "C", 25, 72, 78),
    ("Shane Bieber", "SP", 30, 78, 65),
    ("Jack Flaherty", "SP", 29, 76, 75),
    ("Aaron Nola", "SP", 32, 76, 82),
    ("Zac Gallen", "SP", 30, 78, 82),
    ("Cristopher Sanchez", "SP", 28, 76, 85),
    ("Joe Ryan", "SP", 29, 76, 85),
    ("Garrett Crochet", "SP", 26, 82, 80),
    ("MacKenzie Gore", "SP", 26, 76, 82),
    ("Bryce Miller", "SP", 26, 74, 82),
    ("Michael King", "SP", 30, 74, 78),
    ("Jhoan Duran", "RP", 27, 84, 82),
    ("Andres Munoz", "RP", 25, 82, 80),
    ("Robert Suarez", "RP", 34, 78, 82),
    ("Kenley Jansen", "RP", 38, 72, 78),
]


# ---------------------------------------------------------------------------
# NHL — pro (name, pos, age, skill, health)
# ---------------------------------------------------------------------------

NHL_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Elite (87-99) ----
    ("Connor McDavid", "C", 29, 99, 85),
    ("Nathan MacKinnon", "C", 30, 97, 85),
    ("Cale Makar", "D", 27, 96, 82),
    ("Auston Matthews", "C", 28, 95, 78),
    ("Nikita Kucherov", "RW", 32, 95, 85),
    ("Leon Draisaitl", "C", 30, 94, 88),
    ("David Pastrnak", "RW", 29, 92, 88),
    ("Kirill Kaprizov", "LW", 28, 93, 82),
    ("Quinn Hughes", "D", 26, 93, 85),
    ("Igor Shesterkin", "G", 29, 93, 85),
    ("Connor Hellebuyck", "G", 32, 93, 88),
    ("Mikko Rantanen", "RW", 29, 91, 85),
    ("Jack Hughes", "C", 24, 90, 78),
    ("Connor Bedard", "C", 20, 87, 82),
    ("Sidney Crosby", "C", 38, 87, 82),
    # ---- Quality (74-89) ----
    ("Artemi Panarin", "LW", 33, 89, 85),
    ("Jack Eichel", "C", 29, 89, 78),
    ("Matthew Tkachuk", "LW", 27, 89, 72),
    ("Brady Tkachuk", "LW", 26, 87, 82),
    ("William Nylander", "RW", 29, 86, 88),
    ("Mitch Marner", "RW", 28, 87, 85),
    ("Aleksander Barkov", "C", 30, 85, 75),
    ("Adam Fox", "D", 27, 88, 85),
    ("Roman Josi", "D", 35, 85, 82),
    ("Victor Hedman", "D", 34, 84, 78),
    ("Zach Werenski", "D", 28, 85, 82),
    ("Rasmus Dahlin", "D", 25, 86, 85),
    ("Miro Heiskanen", "D", 26, 86, 80),
    ("Elias Pettersson", "C", 27, 84, 78),
    ("Tim Stutzle", "C", 23, 85, 85),
    ("Clayton Keller", "RW", 27, 82, 82),
    ("Jason Robertson", "LW", 26, 83, 85),
    ("Wyatt Johnston", "C", 22, 82, 88),
    ("Matty Beniers", "C", 22, 79, 82),
    ("Macklin Celebrini", "C", 19, 80, 82),
    ("John Tavares", "C", 35, 78, 82),
    ("Sam Reinhart", "RW", 29, 83, 88),
    ("Sebastian Aho", "C", 28, 83, 85),
    ("Seth Jarvis", "RW", 23, 79, 85),
    ("Jesper Bratt", "LW", 27, 80, 88),
    ("Nico Hischier", "C", 26, 82, 82),
    ("Filip Forsberg", "LW", 31, 80, 82),
    ("Juuse Saros", "G", 30, 84, 78),
    ("Jake Oettinger", "G", 27, 84, 85),
    ("Thatcher Demko", "G", 29, 80, 65),
    ("Stuart Skinner", "G", 26, 76, 82),
    ("Ilya Sorokin", "G", 30, 82, 80),
    ("Logan Thompson", "G", 28, 76, 78),
    ("Andrei Vasilevskiy", "G", 31, 84, 78),
    ("Charlie McAvoy", "D", 27, 83, 65),
    ("Moritz Seider", "D", 24, 82, 88),
    ("Evan Bouchard", "D", 26, 83, 85),
    ("Noah Dobson", "D", 25, 79, 85),
    ("Devon Toews", "D", 31, 81, 82),
    ("Josh Morrissey", "D", 30, 80, 85),
    ("Shea Theodore", "D", 30, 78, 78),
    ("Aaron Ekblad", "D", 29, 76, 75),
    ("Alex Ovechkin", "LW", 40, 82, 82),
    ("Steven Stamkos", "C", 35, 76, 75),
    ("Brayden Point", "C", 29, 85, 78),
    ("Nikolaj Ehlers", "LW", 29, 78, 78),
    ("Kyle Connor", "LW", 28, 82, 85),
    ("Anze Kopitar", "C", 38, 74, 82),
    ("Drew Doughty", "D", 35, 70, 75),
    ("Dylan Larkin", "C", 28, 78, 82),
    ("Patrick Kane", "RW", 36, 72, 68),
    ("Brad Marchand", "LW", 37, 78, 78),
    ("Nazem Kadri", "C", 34, 74, 82),
    ("Tage Thompson", "C", 28, 78, 78),
    ("Alex DeBrincat", "LW", 27, 78, 80),
    ("Trevor Zegras", "C", 24, 74, 72),
    ("Cutter Gauthier", "LW", 21, 76, 82),
    ("Owen Power", "D", 22, 76, 85),
    ("Luke Hughes", "D", 21, 76, 82),
    # ---- Depth / role players (55-78) ----
    ("Jared McCann", "LW", 29, 74, 82),
    ("Anders Lee", "LW", 35, 68, 82),
    ("Filip Zadina", "LW", 25, 62, 75),
    ("Andrei Svechnikov", "LW", 25, 80, 75),
    ("Jake Guentzel", "LW", 31, 82, 78),
    ("Matthew Boldy", "LW", 24, 80, 85),
    ("Brandon Hagel", "LW", 27, 78, 88),
    ("Jordan Kyrou", "RW", 27, 80, 82),
    ("Tyler Bertuzzi", "LW", 30, 70, 78),
    ("Vasily Podkolzin", "RW", 24, 66, 78),
    ("Cole Caufield", "RW", 24, 84, 82),
    ("Kirby Dach", "C", 24, 74, 68),
    ("Bo Horvat", "C", 30, 76, 82),
    ("Barrett Hayton", "C", 25, 68, 82),
    ("Sam Bennett", "C", 29, 78, 78),
    ("Mark Scheifele", "C", 32, 82, 80),
    ("Adam Fantilli", "C", 21, 78, 82),
    ("Zach Hyman", "RW", 33, 80, 78),
    ("Nick Suzuki", "C", 26, 82, 88),
    ("Juraj Slafkovsky", "LW", 21, 76, 82),
    ("Lane Hutson", "D", 21, 82, 82),
    ("Jake Sanderson", "D", 23, 80, 85),
    ("K'Andre Miller", "D", 25, 74, 85),
    ("Ivan Provorov", "D", 28, 74, 85),
    ("Jaccob Slavin", "D", 31, 80, 88),
    ("Brandon Montour", "D", 30, 74, 82),
    ("Jared Spurgeon", "D", 35, 72, 75),
    ("Alex Pietrangelo", "D", 35, 70, 65),
    ("MacKenzie Weegar", "D", 31, 74, 88),
    ("Vince Dunn", "D", 28, 74, 85),
    ("Rasmus Andersson", "D", 28, 76, 85),
    ("Erik Karlsson", "D", 35, 74, 65),
    ("Darcy Kuemper", "G", 35, 68, 70),
    ("Jacob Markstrom", "G", 35, 76, 78),
    ("Linus Ullmark", "G", 32, 78, 75),
    ("Joey Daccord", "G", 28, 76, 82),
    ("Filip Gustavsson", "G", 27, 76, 82),
    ("Sergei Bobrovsky", "G", 37, 76, 78),
    ("Karel Vejmelka", "G", 29, 68, 80),
    ("Spencer Knight", "G", 24, 72, 75),
]


# ---------------------------------------------------------------------------
# CBB — college (name, pos, class_year 1-4, skill, health)
# ---------------------------------------------------------------------------

CBB_RAW: list[tuple[str, str, int, int, int]] = [
    # ---- Elite (89-96) ----
    ("JT Toppin", "PF", 3, 90, 85),
    # ---- Quality (74-88) ----
    ("Tahaad Pettiford", "PG", 2, 86, 82),
    ("Boogie Fland", "PG", 2, 85, 78),
    ("Flory Bidunga", "C", 2, 84, 85),
    ("Alex Condon", "C", 3, 83, 85),
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
    ("Aaron Bradshaw", "C", 2, 74, 78),
    ("Cliff Omoruyi", "C", 4, 72, 82),
    ("Hunter Sallis", "SG", 4, 74, 82),
    ("Assane Diop", "C", 2, 66, 78),
    ("Trentyn Flowers", "SF", 2, 70, 80),
    ("Chance Westry", "SG", 2, 66, 78),
    ("Jaxson Kohler", "C", 2, 62, 78),
    ("Malachi Moreno", "C", 1, 68, 80),
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
    ("Johann Grunloh", "C", 2, 72, 80),
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
    ("Damien Martinez", "RB", 3, 72, 78),
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
    ("Miles Kitselman", "TE", 3, 66, 82),
    ("Vic Burley", "DT", 2, 72, 82),
    ("Zxavian Harris", "DT", 2, 68, 80),
    # ---- 2026 preseason top players backfill ----
    ("C.J. Carr", "QB", 3, 86, 85),
    ("Darian Mensah", "QB", 3, 85, 82),
    ("Leonard Moore", "CB", 3, 84, 85),
    ("Ahmad Hardy", "RB", 3, 83, 85),
    ("John Mateer", "QB", 4, 82, 78),
    ("Carter Smith", "OT", 3, 82, 85),
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
        pool.extend(players)
    pool.sort(key=lambda p: p.draft_value, reverse=True)
    return pool


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
