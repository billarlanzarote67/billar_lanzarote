
import sqlite3, math, json
from stats_automation_common import db, utc_now, log_run

BASE = 1200.0
K = 24.0

def get_rating(cur, player_id):
    cur.execute("SELECT elo_rating FROM elo_ratings WHERE player_id = ?", (player_id,))
    row = cur.fetchone()
    return float(row[0]) if row else BASE

def set_rating(cur, player_id, rating, seeded_from="match_history"):
    cur.execute("""INSERT OR REPLACE INTO elo_ratings(player_id, elo_rating, seeded_from, last_updated_ts_utc)
                   VALUES (?, ?, ?, ?)""", (player_id, rating, seeded_from, utc_now()))

def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))

def main():
    con = db(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS elo_ratings(
        player_id TEXT PRIMARY KEY,
        elo_rating REAL NOT NULL,
        seeded_from TEXT,
        last_updated_ts_utc TEXT NOT NULL
    )""")
    cur.execute("""SELECT player1_id, player2_id, winner_player_id FROM match_results
                   WHERE player1_id IS NOT NULL AND player2_id IS NOT NULL
                   ORDER BY COALESCE(played_ts_utc, '') ASC""")
    matches = cur.fetchall()
    processed = 0
    for a, b, w in matches:
        ra = get_rating(cur, a)
        rb = get_rating(cur, b)
        ea = expected(ra, rb)
        eb = expected(rb, ra)
        sa = 1.0 if w == a else 0.0 if w == b else 0.5
        sb = 1.0 if w == b else 0.0 if w == a else 0.5
        ra2 = ra + K * (sa - ea)
        rb2 = rb + K * (sb - eb)
        set_rating(cur, a, round(ra2, 2))
        set_rating(cur, b, round(rb2, 2))
        processed += 1
    con.commit(); con.close()
    log_run("elo_seed", None, "ok", {"processed_matches": processed})
    print(json.dumps({"processed_matches": processed}, indent=2))

if __name__ == "__main__":
    main()
