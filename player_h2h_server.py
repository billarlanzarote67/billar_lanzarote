import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory

DB_PRIMARY = r"C:\AI\BillarLanzarote\data\billar_lanzarote.sqlite3"
DB_FALLBACK = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
APP_DIR = os.path.dirname(__file__)


def resolve_db() -> str:
    if os.path.exists(DB_PRIMARY):
        return DB_PRIMARY
    return DB_FALLBACK

DB = resolve_db()
app = Flask(__name__, static_folder=APP_DIR, static_url_path="")


def q(sql: str, params=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def one(sql: str, params=()):
    rows = q(sql, params)
    return rows[0] if rows else None


def clean_value(v):
    if v in (None, "", "None"):
        return None
    return v


@app.route("/")
def index():
    return send_from_directory(APP_DIR, "player_h2h_index.html")


@app.route("/api/players")
def api_players():
    rows = q(
        """
        SELECT p.player_id,
               p.display_name,
               s.matches_played,
               s.wins,
               s.losses,
               s.win_rate,
               s.frames_won,
               s.frames_lost,
               s.frames_total
        FROM players p
        LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
        ORDER BY COALESCE(s.wins, 0) DESC, p.display_name ASC
        """
    )
    return jsonify(rows)


@app.route("/api/headtohead")
def api_h2h():
    a = request.args.get("a", "").strip()
    b = request.args.get("b", "").strip()

    if not a or not b:
        return jsonify({"status": "error", "message": "Both players are required."}), 400
    if a == b:
        return jsonify({"status": "error", "message": "Choose two different players."}), 400

    pa = one(
        """
        SELECT p.player_id,p.display_name,s.matches_played,s.wins,s.losses,s.win_rate,s.frames_won,s.frames_lost,s.frames_total
        FROM players p
        LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
        WHERE p.player_id = ?
        """,
        (a,),
    )
    pb = one(
        """
        SELECT p.player_id,p.display_name,s.matches_played,s.wins,s.losses,s.win_rate,s.frames_won,s.frames_lost,s.frames_total
        FROM players p
        LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
        WHERE p.player_id = ?
        """,
        (b,),
    )

    if not pa or not pb:
        return jsonify({"status": "error", "message": "One or both players were not found."}), 404

    result = {
        "status": "ok",
        "player_a": {
            "display_name": pa["display_name"],
            "matches_played": clean_value(pa.get("matches_played")),
            "wins": clean_value(pa.get("wins")),
            "losses": clean_value(pa.get("losses")),
            "win_rate": clean_value(pa.get("win_rate")),
            "frames_won": clean_value(pa.get("frames_won")),
            "frames_lost": clean_value(pa.get("frames_lost")),
            "frames_total": clean_value(pa.get("frames_total")),
        },
        "player_b": {
            "display_name": pb["display_name"],
            "matches_played": clean_value(pb.get("matches_played")),
            "wins": clean_value(pb.get("wins")),
            "losses": clean_value(pb.get("losses")),
            "win_rate": clean_value(pb.get("win_rate")),
            "frames_won": clean_value(pb.get("frames_won")),
            "frames_lost": clean_value(pb.get("frames_lost")),
            "frames_total": clean_value(pb.get("frames_total")),
        },
        "note": "This H2H view compares stored player summary stats. Match-by-match H2H can be added later.",
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8097, debug=False)
