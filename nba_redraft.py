"""NBA Redraft Simulator — you play as the Boston Celtics.

Snake draft, 30 teams, 5 rounds (150 picks). Rankings blend skill, age, and
health. Other teams are AI (best player available with small noise).

Run: python3 nba_redraft.py
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class Player:
    name: str
    pos: str
    age: int
    skill: int
    health: int
    score: float = field(init=False)

    def __post_init__(self) -> None:
        age_factor = max(0, 100 - max(0, self.age - 27) * 6)
        self.score = round(
            self.skill * 0.70 + age_factor * 0.15 + self.health * 0.15, 2
        )


# Curated NBA player pool — roughly current (2025-26 season).
# skill 1-100: current on-court impact.   health 1-100: durability.
# Tiered so ratings stay internally consistent.
PLAYERS_RAW: list[tuple[str, str, int, float, int]] = [
    ("Shai Gilgeous-Alexander", "PG", 27, 97.9, 92),
    ("Nikola Jokic", "C", 30, 99.0, 90),
    ("Luka Doncic", "PG", 26, 97.4, 78),
    ("Giannis Antetokounmpo", "PF", 30, 95.8, 82),
    ("Jayson Tatum", "SF", 27, 93.2, 85),
    ("Victor Wembanyama", "C", 21, 98.5, 78),
    ("Anthony Edwards", "SG", 24, 94.2, 90),
    ("Jalen Brunson", "PG", 29, 79.9, 85),
    ("Tyrese Haliburton", "PG", 25, 88.9, 70),
    ("Joel Embiid", "C", 31, 61.9, 55),
    ("Donovan Mitchell", "SG", 29, 94.8, 82),
    ("Kevin Durant", "SF", 37, 90.0, 78),
    ("Devin Booker", "SG", 29, 84.7, 85),
    ("Stephen Curry", "PG", 37, 70.4, 80),
    ("LeBron James", "SF", 40, 75.7, 82),
    ("Anthony Davis", "PF", 32, 76.7, 65),
    ("Tyrese Maxey", "PG", 25, 96.9, 85),
    ("Cade Cunningham", "PG", 24, 96.3, 82),
    ("Paolo Banchero", "PF", 23, 83.6, 80),
    ("Damian Lillard", "PG", 35, 64.5, 70),
    ("Jaylen Brown", "SG", 29, 87.9, 85),
    ("Karl-Anthony Towns", "C", 30, 90.5, 80),
    ("De'Aaron Fox", "PG", 28, 67.2, 82),
    ("Trae Young", "PG", 27, 72.0, 85),
    ("Jimmy Butler", "SF", 36, 15, 75),
    ("Kawhi Leonard", "SF", 34, 86.8, 55),
    ("Domantas Sabonis", "C", 29, 77.8, 88),
    ("Paul George", "SF", 35, 75.1, 65),
    ("Franz Wagner", "SF", 24, 63.5, 82),
    ("Alperen Sengun", "C", 23, 91.0, 85),
    ("Jaren Jackson Jr.", "PF", 26, 69.3, 78),
    ("Pascal Siakam", "PF", 31, 84.2, 85),
    ("Bam Adebayo", "C", 28, 68.2, 90),
    ("Ja Morant", "PG", 26, 73.0, 62),
    ("Zion Williamson", "PF", 25, 69.8, 50),
    ("Chet Holmgren", "C", 23, 87.3, 72),
    ("Evan Mobley", "PF", 24, 85.7, 85),
    ("Scottie Barnes", "SF", 24, 92.1, 85),
    ("Lauri Markkanen", "PF", 28, 76.2, 82),
    ("Jamal Murray", "PG", 28, 91.6, 72),
    ("Mikal Bridges", "SF", 29, 89.5, 95),
    ("OG Anunoby", "SF", 28, 52.3, 80),
    ("Rudy Gobert", "C", 33, 54.5, 88),
    ("Kristaps Porzingis", "C", 30, 31.7, 55),
    ("Zach LaVine", "SG", 30, 15, 70),
    ("Darius Garland", "PG", 25, 78.3, 80),
    ("Jalen Williams", "SF", 24, 78.9, 85),
    ("Desmond Bane", "SG", 27, 62.9, 82),
    ("LaMelo Ball", "PG", 24, 68.8, 55),
    ("Kyrie Irving", "PG", 33, 81.5, 65),
    ("AJ Dybantsa", "F", 19, 15, 86),
    ("Darryn Peterson", "G", 19, 15, 85),
    ("Cameron Boozer", "F", 19, 15, 88),
    ("Caleb Wilson", "F", 20, 15, 84),
    ("Dejounte Murray", "PG", 29, 74.6, 78),
    ("Julius Randle", "PF", 31, 51.3, 75),
    ("Mark Williams", "C", 24, 38.6, 65),
    ("Brandon Ingram", "SF", 28, 65.6, 68),
    ("Fred VanVleet", "PG", 31, 66.7, 78),
    ("Brandon Miller", "SF", 23, 72.5, 75),
    ("Josh Giddey", "SG", 23, 81.0, 85),
    ("Deni Avdija", "SF", 25, 85.2, 85),
    ("Tobias Harris", "PF", 33, 15, 88),
    ("Nikola Vucevic", "C", 35, 62.4, 85),
    ("Jrue Holiday", "PG", 35, 53.9, 82),
    ("Derrick White", "SG", 31, 53.4, 90),
    ("Draymond Green", "PF", 35, 15, 75),
    ("CJ McCollum", "SG", 34, 64.0, 78),
    ("Khris Middleton", "SF", 34, 15, 60),
    ("Michael Porter Jr.", "SF", 27, 74.1, 75),
    ("Aaron Gordon", "PF", 30, 46.0, 82),
    ("Jalen Duren", "C", 22, 86.3, 85),
    ("Jerami Grant", "SF", 31, 33.3, 80),
    ("Tyler Herro", "SG", 25, 67.7, 72),
    ("Coby White", "SG", 25, 26.4, 85),
    ("Miles Bridges", "PF", 27, 52.9, 82),
    ("Shaedon Sharpe", "SG", 22, 57.6, 75),
    ("Amen Thompson", "SF", 22, 92.6, 80),
    ("Ausar Thompson", "SF", 22, 44.4, 75),
    ("Immanuel Quickley", "PG", 26, 42.8, 78),
    ("Myles Turner", "C", 29, 40.1, 85),
    ("Jonas Valanciunas", "C", 33, 15, 85),
    ("Kyle Kuzma", "PF", 30, 22.7, 82),
    ("Bennedict Mathurin", "SG", 23, 29.5, 82),
    ("RJ Barrett", "SG", 25, 61.4, 78),
    ("Jalen Green", "SG", 23, 56.6, 82),
    ("Malik Monk", "PG", 27, 15, 80),
    ("Andrew Wiggins", "SF", 30, 55.5, 78),
    ("Klay Thompson", "SG", 35, 15, 75),
    ("Collin Sexton", "PG", 26, 22.1, 75),
    ("Christian Braun", "SG", 24, 20.0, 85),
    ("Austin Reaves", "SG", 27, 79.4, 82),
    ("Jabari Smith Jr.", "PF", 22, 44.9, 80),
    ("Jaden McDaniels", "SF", 25, 48.1, 85),
    ("Dyson Daniels", "SG", 22, 41.2, 82),
    ("Dereck Lively II", "C", 21, 15, 72),
    ("Walker Kessler", "C", 24, 47.6, 82),
    ("Naz Reid", "C", 26, 26.9, 85),
    ("Isaiah Hartenstein", "C", 27, 28.0, 82),
    ("Jalen Johnson", "SF", 23, 95.3, 70),
    ("Dillon Brooks", "SF", 29, 35.4, 82),
    ("Buddy Hield", "SG", 32, 15, 90),
    ("Payton Pritchard", "PG", 27, 58.2, 88),
    ("D'Angelo Russell", "PG", 29, 15, 80),
    ("Al Horford", "C", 39, 15, 82),
    ("Bobby Portis", "PF", 30, 15, 85),
    ("Gary Trent Jr.", "SG", 26, 15, 80),
    ("Jalen Suggs", "SG", 24, 46.5, 60),
    ("Devin Vassell", "SG", 25, 33.8, 75),
    ("Keldon Johnson", "SF", 26, 15, 82),
    ("Norman Powell", "SG", 32, 58.7, 80),
    ("Ivica Zubac", "C", 28, 51.8, 88),
    ("Nic Claxton", "C", 26, 31.1, 80),
    ("Donte DiVincenzo", "SG", 28, 27.4, 82),
    ("Cameron Johnson", "SF", 29, 15, 75),
    ("PJ Washington", "PF", 27, 15, 80),
    ("Jordan Poole", "SG", 26, 15, 82),
    ("Terry Rozier", "PG", 31, 15, 78),
    ("Stephon Castle", "SG", 21, 82.6, 82),
    ("Jaime Jaquez Jr.", "SF", 24, 35.9, 80),
    ("Trey Murphy III", "SF", 25, 83.1, 72),
    ("Grayson Allen", "SG", 30, 47.0, 82),
    ("Taurean Prince", "SF", 31, 15, 82),
    ("Luguentz Dort", "SG", 26, 15, 85),
    ("Brook Lopez", "C", 37, 15, 82),
    ("Clint Capela", "C", 31, 15, 82),
    ("Daniel Gafford", "C", 27, 21.6, 82),
    ("Derrick Jones Jr.", "SF", 28, 15, 82),
    ("Andrew Nembhard", "PG", 25, 50.8, 82),
    ("Aaron Nesmith", "SF", 26, 15, 80),
    ("Kentavious Caldwell-Pope", "SG", 32, 15, 82),
    ("Malcolm Brogdon", "PG", 32, 15, 65),
    ("Jalen Williams Jr.", "SF", 23, 15, 80),
    ("Tari Eason", "PF", 24, 15, 72),
    ("Jose Alvarado", "PG", 27, 15, 80),
    ("GG Jackson", "PF", 21, 15, 75),
    ("Keegan Murray", "PF", 25, 15, 82),
    ("Jakob Poeltl", "C", 30, 37.5, 85),
    ("Nickeil Alexander-Walker", "SG", 27, 71.4, 82),
    ("Royce O'Neale", "SF", 32, 15, 80),
    ("Guerschon Yabusele", "PF", 30, 15, 80),
    ("Isaiah Joe", "SG", 26, 15, 82),
    ("Toumani Camara", "SF", 25, 43.9, 82),
    ("Jaden Ivey", "SG", 23, 15, 70),
    ("Cason Wallace", "SG", 22, 24.2, 85),
    ("Bilal Coulibaly", "SF", 21, 25.8, 80),
    ("Bub Carrington", "SG", 20, 15, 82),
    ("Scoot Henderson", "PG", 21, 60.8, 78),
    ("Donovan Clingan", "C", 22, 59.8, 75),
    ("Reed Sheppard", "PG", 21, 56.1, 80),
    ("Alex Sarr", "C", 20, 70.9, 78),
    ("Zaccharie Risacher", "SF", 20, 15, 80),
    ("Matas Buzelis", "PF", 21, 73.6, 78),
    ("Kel'el Ware", "C", 21, 34.8, 78),
    ("Jaylen Wells", "SF", 22, 15, 82),
    ("Yves Missi", "C", 21, 15, 80),
    ("Ja'Kobe Walter", "SG", 21, 15, 80),
    ("Isaiah Collier", "PG", 21, 34.3, 80),
    ("Rob Dillingham", "PG", 20, 15, 72),
    ("Zach Edey", "C", 23, 60.3, 75),
    ("Tristan da Silva", "SF", 24, 15, 82),
    ("Bogdan Bogdanovic", "SG", 33, 15, 78),
    ("Kevin Huerter", "SG", 27, 15, 80),
    ("Bruce Brown", "SG", 29, 15, 78),
    ("Josh Hart", "SG", 30, 49.2, 85),
    ("Max Strus", "SG", 29, 15, 80),
    ("Caris LeVert", "SG", 31, 15, 78),
    ("Kelly Olynyk", "C", 34, 15, 78),
    ("De'Andre Hunter", "SF", 28, 15, 75),
    ("Jonathan Kuminga", "PF", 23, 15, 80),
    ("Moses Moody", "SG", 23, 15, 82),
    ("Santi Aldama", "PF", 25, 29.0, 80),
    ("Vince Williams Jr.", "SG", 25, 15, 80),
    ("Obi Toppin", "PF", 27, 15, 82),
    ("Jarrett Allen", "C", 27, 59.2, 85),
    ("Spencer Dinwiddie", "PG", 32, 15, 80),
    ("Precious Achiuwa", "PF", 26, 15, 78),
    ("Ayo Dosunmu", "SG", 25, 32.7, 82),
]

TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "LA Clippers", "LA Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans",
    "New York Knicks", "Oklahoma City Thunder", "Orlando Magic",
    "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers",
    "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
    "Utah Jazz", "Washington Wizards",
]

CELTICS = "Boston Celtics"
ROUNDS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_pool() -> list[Player]:
    pool = [Player(*row) for row in PLAYERS_RAW]
    pool.sort(key=lambda p: p.score, reverse=True)
    return pool


def build_snake_order(teams: list[str], rounds: int) -> list[str]:
    order: list[str] = []
    for r in range(rounds):
        order.extend(teams if r % 2 == 0 else list(reversed(teams)))
    return order


def hr(char: str = "-", n: int = 72) -> str:
    return char * n


def fmt_player_row(i: int, p: Player) -> str:
    return f" {i:>2}. {p.name:<26} {p.pos:<3} age {p.age:<2}  skill {p.skill:<3} health {p.health:<3}  score {p.score:5.2f}"


def show_top(available: list[Player], n: int = 15) -> None:
    print("\nTop available:")
    for i, p in enumerate(available[:n], start=1):
        print(fmt_player_row(i, p))


def show_roster(team: str, roster: list[Player]) -> None:
    if not roster:
        print(f"\n{team} roster: (empty)")
        return
    print(f"\n{team} roster ({len(roster)}):")
    for p in roster:
        print(f"   {p.pos:<3} {p.name:<26} age {p.age:<2} skill {p.skill}")


# ---------------------------------------------------------------------------
# Pick logic
# ---------------------------------------------------------------------------


def ai_pick(available: list[Player]) -> Player:
    """Best player available with small noise among the top 3.

    Top-3 instead of top-5 keeps stars from sliding too far while still
    allowing some realistic draft-day noise.
    """
    top = available[:3]
    # Square the weights so the top-scored player is clearly favored.
    weights = [p.score ** 2 for p in top]
    return random.choices(top, weights=weights, k=1)[0]


def user_pick(available: list[Player], roster: list[Player]) -> Player:
    """Prompt user for a pick. Accept 1-15 or substring match."""
    while True:
        show_top(available, 15)
        show_roster(CELTICS, roster)
        raw = input("\nYour pick (number 1-15 or player name): ").strip()
        if not raw:
            print(">> empty input, try again")
            continue

        # Numeric pick
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= min(15, len(available)):
                return available[idx - 1]
            print(f">> number must be 1-{min(15, len(available))}")
            continue

        # Name match (case-insensitive substring)
        q = raw.lower()
        matches = [p for p in available if q in p.name.lower()]
        if not matches:
            print(f">> no available player matching '{raw}'")
            continue
        if len(matches) == 1:
            return matches[0]
        print(f">> {len(matches)} matches — be more specific:")
        for m in matches[:10]:
            print(f"     {m.name} ({m.pos})")


# ---------------------------------------------------------------------------
# Main draft loop
# ---------------------------------------------------------------------------


def resolve_pick(available: list[Player], query: str) -> Player | None:
    q = query.strip().lower()
    if not q:
        return None
    matches = [p for p in available if q in p.name.lower()]
    if len(matches) == 1:
        return matches[0]
    # exact match fallback if multiple substring hits
    exact = [p for p in matches if p.name.lower() == q]
    if len(exact) == 1:
        return exact[0]
    return None


def run_draft(
    auto: bool = False,
    preset_picks: list[str] | None = None,
) -> None:
    """Run the full snake draft.

    auto=True runs without user input (for smoke testing).
    preset_picks: list of Celtics pick queries consumed in order; when exhausted
    the draft pauses at the next Celtics pick, prints state, and exits.
    """
    preset_picks = list(preset_picks or [])
    pool = build_pool()
    shuffled_teams = TEAMS.copy()
    random.shuffle(shuffled_teams)
    celtics_slot = shuffled_teams.index(CELTICS) + 1

    print(hr("="))
    print("  NBA REDRAFT SIMULATOR — you are the Boston Celtics")
    print(hr("="))
    print(f"\nDraft order randomized. Celtics have slot #{celtics_slot} of 30.")
    print(f"Snake draft, {ROUNDS} rounds, {ROUNDS * len(TEAMS)} picks total.\n")

    pick_order = build_snake_order(shuffled_teams, ROUNDS)
    rosters: dict[str, list[Player]] = {t: [] for t in TEAMS}

    for overall, team in enumerate(pick_order, start=1):
        rnd = (overall - 1) // len(TEAMS) + 1
        print(hr())
        print(f"Round {rnd}  |  Pick #{overall:>3}  |  {team} on the clock")

        if team == CELTICS and not auto:
            if preset_picks:
                query = preset_picks.pop(0)
                pick = resolve_pick(pool, query)
                if pick is None:
                    print(f"\n>> could not resolve preset pick '{query}' — aborting")
                    return
                print(f"  -> {team} select {pick.name} ({pick.pos}, age {pick.age}, "
                      f"skill {pick.skill}, score {pick.score}) *** YOUR PICK ***")
                pool.remove(pick)
                rosters[team].append(pick)
                continue
            # No preset — pause here and print state
            print("\n" + hr("="))
            print(f"  CELTICS ON THE CLOCK — Round {rnd}, Pick #{overall}")
            print(hr("="))
            show_top(pool, 15)
            show_roster(CELTICS, rosters[CELTICS])
            print("\n>> PAUSED. Tell Claude your pick (number or name).")
            return
        else:
            pick = ai_pick(pool)

        pool.remove(pick)
        rosters[team].append(pick)
        tag = " *** YOUR PICK ***" if team == CELTICS and not auto else ""
        print(
            f"  -> {team} select {pick.name} ({pick.pos}, age {pick.age}, "
            f"skill {pick.skill}, score {pick.score}){tag}"
        )

    # ---- Post-draft summary ----
    print("\n" + hr("="))
    print("  DRAFT COMPLETE")
    print(hr("="))
    show_roster(CELTICS, rosters[CELTICS])

    # Team totals
    totals = sorted(
        ((t, sum(p.score for p in r)) for t, r in rosters.items()),
        key=lambda x: x[1],
        reverse=True,
    )
    print("\nTop 5 drafts by total score:")
    for i, (t, s) in enumerate(totals[:5], start=1):
        marker = "  <-- you" if t == CELTICS else ""
        print(f"  {i}. {t:<26} {s:6.1f}{marker}")
    print("\nBottom 5 drafts by total score:")
    for i, (t, s) in enumerate(totals[-5:], start=len(totals) - 4):
        marker = "  <-- you" if t == CELTICS else ""
        print(f"  {i}. {t:<26} {s:6.1f}{marker}")

    celtics_rank = next(i for i, (t, _) in enumerate(totals, start=1) if t == CELTICS)
    print(f"\nCeltics finished ranked #{celtics_rank} of 30 by draft score.")


def parse_args(argv: list[str]) -> tuple[bool, int | None, list[str]]:
    auto = "--auto" in argv
    seed = None
    picks: list[str] = []
    for i, a in enumerate(argv):
        if a == "--seed" and i + 1 < len(argv):
            seed = int(argv[i + 1])
        if a == "--picks" and i + 1 < len(argv):
            picks = [p for p in argv[i + 1].split("|") if p.strip()]
    return auto, seed, picks


if __name__ == "__main__":
    auto, seed, picks = parse_args(sys.argv[1:])
    if seed is not None:
        random.seed(seed)
    if auto:
        run_draft(auto=True)
    else:
        try:
            run_draft(preset_picks=picks)
        except (KeyboardInterrupt, EOFError):
            print("\n\nDraft aborted.")
