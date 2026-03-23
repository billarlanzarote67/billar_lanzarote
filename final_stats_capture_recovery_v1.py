
import os, json, sqlite3, glob
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
MATCH_DIR = os.path.join(ROOT, "data", "completed_matches")
LOG = os.path.join(ROOT, "logs", "final_stats_capture_recovery_v1.log")

os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def table_exists(c, table_name):
    return bool(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table_name,)).fetchone())

def parse_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def normalize_game(v):
    if not v:
        return None
    s = str(v).strip().lower()
    mapping = {
        "8-ball": "Bola 8",
        "bola 8": "Bola 8",
        "9-ball": "Bola 9",
        "bola 9": "Bola 9",
        "10-ball": "Bola 10",
        "bola 10": "Bola 10",
    }
    return mapping.get(s, str(v).strip())

def run():
    if not os.path.exists(DB):
        print(f"DB not found: {DB}")
        return
    c = conn()
    cur = c.cursor()
    if not table_exists(c, "player_match_history"):
        log("player_match_history missing. Nothing to update.")
        c.close()
        return
    files = sorted(glob.glob(os.path.join(MATCH_DIR, "*.json")))
    updated = 0
    for fp in files:
        data = parse_json(fp)
        if not isinstance(data, dict):
            continue
        a = (data.get("player_a") or "").strip()
        b = (data.get("player_b") or "").strip()
        if not a or not b:
            continue
        avg_a = data.get("avg_frametime_a")
        avg_b = data.get("avg_frametime_b")
        run_a = data.get("runouts_a")
        run_b = data.get("runouts_b")
        baw_a = data.get("break_and_wins_a")
        baw_b = data.get("break_and_wins_b")
        stl_a = data.get("frames_stolen_a")
        stl_b = data.get("frames_stolen_b")
        to_a = data.get("timeouts_a")
        to_b = data.get("timeouts_b")
        game = normalize_game(data.get("game_type_es") or data.get("game_type"))
        score = data.get("score")
        for player, opp, avg, run, baw, stl, tmo in [
            (a, b, avg_a, run_a, baw_a, stl_a, to_a),
            (b, a, avg_b, run_b, baw_b, stl_b, to_b),
        ]:
            row = cur.execute("""
                SELECT id FROM player_match_history
                WHERE player_name = ? AND opponent_name = ?
                ORDER BY id DESC LIMIT 1
            """, (player, opp)).fetchone()
            if not row:
                continue
            cur.execute("""
                UPDATE player_match_history
                SET avg_frametime = COALESCE(?, avg_frametime),
                    runouts = COALESCE(?, runouts),
                    break_and_wins = COALESCE(?, break_and_wins),
                    frames_stolen = COALESCE(?, frames_stolen),
                    timeouts = COALESCE(?, timeouts),
                    game_type_es = COALESCE(?, game_type_es),
                    stats_status = CASE
                        WHEN ? IS NOT NULL OR ? IS NOT NULL OR ? IS NOT NULL OR ? IS NOT NULL OR ? IS NOT NULL
                        THEN 'captured'
                        ELSE stats_status
                    END
                WHERE id = ?
            """, (avg, run, baw, stl, tmo, game, avg, run, baw, stl, tmo, row["id"]))
            updated += 1
    c.commit()
    c.close()
    log(f"Recovered/final stats rows updated: {updated}")

if __name__ == "__main__":
    run()
