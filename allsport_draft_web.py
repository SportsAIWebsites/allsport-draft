"""All-Sport Redraft — Flask dashboard for two humans + six bots.

Two human seats ("You" and "Buddy") share one draft over local wifi via
?team=you / ?team=buddy. Bots think for 15 real seconds (a background
thread ticks the draft forward) before auto-picking; humans pick via POST.

Run:
    venv/bin/python allsport_draft_web.py
Then open http://<host-ip>:5060/?team=you and http://<host-ip>:5060/?team=buddy
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request

from allsport_draft import (
    HUMAN_TEAMS,
    ROUNDS,
    TEAM_NAMES,
    Player,
    ai_pick,
    build_pool,
    build_snake_order,
    resolve_pick,
)

try:
    import psycopg2
except ImportError:
    psycopg2 = None

app = Flask(__name__, template_folder="templates")

BOT_THINK_SECONDS = 15
DATABASE_URL = os.environ.get("DATABASE_URL")


# ---------------------------------------------------------------------------
# Optional Postgres persistence — draft state survives a host restart/redeploy.
# Falls back to pure in-memory (no-op save/load) when DATABASE_URL isn't set,
# so local `python allsport_draft_web.py` runs need no database at all.
# ---------------------------------------------------------------------------


def _db_conn():
    if not DATABASE_URL or psycopg2 is None:
        return None
    return psycopg2.connect(DATABASE_URL)


def _ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS allsport_draft_state (
                id INT PRIMARY KEY DEFAULT 1,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )
    conn.commit()


def _load_persisted() -> dict | None:
    conn = _db_conn()
    if conn is None:
        return None
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT payload FROM allsport_draft_state WHERE id = 1")
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _save_persisted(payload: dict) -> None:
    conn = _db_conn()
    if conn is None:
        return
    try:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO allsport_draft_state (id, payload, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                [json.dumps(payload)],
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# In-memory draft state
# ---------------------------------------------------------------------------


class Draft:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.all_players: list[Player] = build_pool()
        payload = _load_persisted()
        if payload:
            self._restore(payload)
        else:
            self.reset()

    def reset(self) -> None:
        with self._lock:
            self.all_players = build_pool()
            self.pool: list[Player] = list(self.all_players)
            order_teams = TEAM_NAMES.copy()
            random.shuffle(order_teams)
            self.draft_order: list[str] = build_snake_order(order_teams, ROUNDS)
            self.slots: dict[str, int] = {t: i + 1 for i, t in enumerate(order_teams)}
            self.rosters: dict[str, list[Player]] = {t: [] for t in TEAM_NAMES}
            self.picks: list[dict] = []
            self.cursor: int = 0
            self.clock_deadline: float | None = None  # epoch seconds bot auto-picks at
            self._set_clock_for_current()
            self._persist()

    def _restore(self, payload: dict) -> None:
        by_name = {p.name: p for p in self.all_players}
        teams_n = len(TEAM_NAMES)
        self.draft_order = payload["draft_order"]
        self.slots = {t: i + 1 for i, t in enumerate(self.draft_order[:teams_n])}
        self.picks = payload["picks"]
        self.cursor = payload["cursor"]
        self.clock_deadline = payload["clock_deadline"]
        drafted_names = {pk["player"]["name"] for pk in self.picks}
        self.pool = [p for p in self.all_players if p.name not in drafted_names]
        self.rosters = {t: [] for t in TEAM_NAMES}
        for pk in self.picks:
            self.rosters[pk["team"]].append(by_name[pk["player"]["name"]])

    def _persist(self) -> None:
        _save_persisted(
            {
                "draft_order": self.draft_order,
                "picks": self.picks,
                "cursor": self.cursor,
                "clock_deadline": self.clock_deadline,
            }
        )

    # -- internal helpers --------------------------------------------------

    def _set_clock_for_current(self) -> None:
        if self.is_complete():
            self.clock_deadline = None
            return
        team = self.draft_order[self.cursor]
        if team in HUMAN_TEAMS:
            self.clock_deadline = None
        else:
            self.clock_deadline = time.time() + BOT_THINK_SECONDS

    def _commit(self, team: str, player: Player) -> None:
        self.pool.remove(player)
        self.rosters[team].append(player)
        rnd = self.cursor // len(TEAM_NAMES) + 1
        self.picks.append({
            "overall": self.cursor + 1,
            "round": rnd,
            "team": team,
            "player": _player_dict(player),
        })
        self.cursor += 1
        self._set_clock_for_current()
        self._persist()

    def tick(self) -> None:
        """Called periodically (poll + background thread). If a bot is on
        the clock and its think-timer has elapsed, auto-pick for it."""
        with self._lock:
            if self.is_complete():
                return
            team = self.draft_order[self.cursor]
            if team in HUMAN_TEAMS:
                return
            if self.clock_deadline is None or time.time() < self.clock_deadline:
                return
            pick = ai_pick(self.pool)
            self._commit(team, pick)

    # -- public API ----------------------------------------------------

    def make_pick(self, team: str, query: str) -> tuple[bool, str]:
        with self._lock:
            if self.is_complete():
                return False, "Draft already complete."
            if team not in HUMAN_TEAMS:
                return False, "Only human seats may submit a pick."
            if self.draft_order[self.cursor] != team:
                return False, f"Not {team}'s pick."
            player = resolve_pick(self.pool, query)
            if player is None:
                return False, f"No unique available player matches '{query}'."
            self._commit(team, player)
            return True, f"{team} selected {player.name}."

    def is_complete(self) -> bool:
        return self.cursor >= len(self.draft_order)

    def on_clock(self) -> str | None:
        if self.is_complete():
            return None
        return self.draft_order[self.cursor]

    def snapshot(self, viewer: str | None = None) -> dict:
        with self._lock:
            drafted_names = {p.name for t in TEAM_NAMES for p in self.rosters[t]}
            rankings = [
                {**_player_dict(p), "drafted": p.name in drafted_names}
                for p in self.all_players
            ]
            pick_by_name = {pk["player"]["name"]: pk for pk in self.picks}
            for r in rankings:
                pk = pick_by_name.get(r["name"])
                if pk:
                    r["pick_overall"] = pk["overall"]
                    r["pick_team"] = pk["team"]

            board_rounds: list[list[dict]] = [[] for _ in range(ROUNDS)]
            for pk in self.picks:
                board_rounds[pk["round"] - 1].append(pk)

            current_team = self.on_clock()
            current_round = self.cursor // len(TEAM_NAMES) + 1 if not self.is_complete() else None
            current_overall = self.cursor + 1 if not self.is_complete() else None
            seconds_left = None
            if self.clock_deadline is not None:
                seconds_left = max(0, round(self.clock_deadline - time.time()))

            top_available = [_player_dict(p) for p in self.pool[:30]]

            rosters_out = {t: [_player_dict(p) for p in self.rosters[t]] for t in TEAM_NAMES}
            team_totals = sorted(
                [
                    {
                        "team": t,
                        "total": round(sum(p.draft_value for p in self.rosters[t]), 1),
                        "count": len(self.rosters[t]),
                    }
                    for t in TEAM_NAMES
                ],
                key=lambda x: x["total"],
                reverse=True,
            )

            return {
                "viewer": viewer,
                "rounds": ROUNDS,
                "roster_size": ROUNDS,
                "teams": TEAM_NAMES,
                "human_teams": sorted(HUMAN_TEAMS),
                "slots": self.slots,
                "draft_order": self.draft_order,
                "board_rounds": board_rounds,
                "current_team": current_team,
                "current_round": current_round,
                "current_overall": current_overall,
                "total_picks": len(self.draft_order),
                "is_viewer_turn": viewer is not None and current_team == viewer,
                "bot_on_clock": current_team is not None and current_team not in HUMAN_TEAMS,
                "seconds_left": seconds_left,
                "rankings": rankings,
                "top_available": top_available,
                "rosters": rosters_out,
                "viewer_roster": rosters_out.get(viewer, []) if viewer else [],
                "team_totals": team_totals,
                "complete": self.is_complete(),
            }


def _player_dict(p: Player) -> dict:
    d = asdict(p)
    d["score"] = float(p.score)
    d["draft_value"] = float(p.draft_value)
    d["age_display"] = p.age_display
    return d


draft = Draft()


# ---------------------------------------------------------------------------
# Background bot-clock thread
# ---------------------------------------------------------------------------


def _bot_loop() -> None:
    while True:
        try:
            draft.tick()
        except Exception:
            pass
        time.sleep(1)


_bot_thread = threading.Thread(target=_bot_loop, daemon=True)
_bot_thread.start()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _resolve_viewer() -> str | None:
    raw = request.args.get("team", "")
    if not raw and request.view_args:
        raw = request.view_args.get("team") or ""
    team = raw.strip().lower()
    if team == "you":
        return "You"
    if team == "buddy":
        return "Buddy"
    return None


@app.route("/")
@app.route("/<team>")
def index(team: str | None = None):
    return render_template("allsport_draft.html")


@app.route("/api/state")
def api_state():
    draft.tick()
    viewer = _resolve_viewer()
    return jsonify(draft.snapshot(viewer))


@app.route("/api/pick", methods=["POST"])
def api_pick():
    data = request.get_json(silent=True) or {}
    viewer = _resolve_viewer()
    query = str(data.get("player", "")).strip()
    if viewer is None:
        return jsonify({"ok": False, "message": "Unknown seat. Use ?team=you or ?team=buddy."}), 400
    ok, msg = draft.make_pick(viewer, query)
    status = 200 if ok else 400
    return jsonify({"ok": ok, "message": msg, "state": draft.snapshot(viewer)}), status


@app.route("/api/reset", methods=["POST"])
def api_reset():
    draft.reset()
    viewer = _resolve_viewer()
    return jsonify({"ok": True, "state": draft.snapshot(viewer)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5060))
    print(f"All-Sport Redraft dashboard -> http://0.0.0.0:{port}/?team=you  and  /?team=buddy")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
