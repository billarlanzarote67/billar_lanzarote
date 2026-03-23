
import os, json, sqlite3, glob, re
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
MATCH_DIR = os.path.join(ROOT, "data", "completed_matches")
LOG = os.path.join(ROOT, "logs", "deep_final_stats_parser_v1.log")
AUDIT = os.path.join(ROOT, "data", "deep_final_stats_audit_v1.json")

os.makedirs(os.path.dirname(LOG), exist_ok=True)
os.makedirs(os.path.dirname(AUDIT), exist_ok=True)

STAT_KEYS = {
    "avg_frametime_a": ["avg_frametime_a", "average_frametime_a", "average_frame_time_a"],
    "avg_frametime_b": ["avg_frametime_b", "average_frametime_b", "average_frame_time_b"],
    "runouts_a": ["runouts_a"],
    "runouts_b": ["runouts_b"],
    "break_and_wins_a": ["break_and_wins_a", "baw_a", "break_wins_a"],
    "break_and_wins_b": ["break_and_wins_b", "baw_b", "break_wins_b"],
    "frames_stolen_a": ["frames_stolen_a", "robadas_a"],
    "frames_stolen_b": ["frames_stolen_b", "robadas_b"],
    "timeouts_a": ["timeouts_a", "tiempos_a"],
    "timeouts_b": ["timeouts_b", "tiempos_b"],
    "game_type": ["game_type_es", "game_type", "game"],
}

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def pick(d, aliases):
    for k in aliases:
        if k in d and d[k] not in (None, "", "None"):
            return d[k]
    return None

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
        "8-ball": "Bola 8", "bola 8": "Bola 8",
        "9-ball": "Bola 9", "bola 9": "Bola 9",
        "10-ball": "Bola 10", "bola 10": "Bola 10",
    }
    return mapping.get(s, str(v).strip())

def update_latest_row(cur, player, opp, payload):
    row = cur.execute("""
        SELECT id FROM player_match_history
        WHERE player_name = ? AND opponent_name = ?
        ORDER BY id DESC LIMIT 1
    """, (player, opp)).fetchone()
    if not row:
        return False
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
    """, (
        payload.get("avg_frametime"),
        payload.get("runouts"),
        payload.get("break_and_wins"),
        payload.get("frames_stolen"),
        payload.get("timeouts"),
        payload.get("game_type_es"),
        payload.get("avg_frametime"),
        payload.get("runouts"),
        payload.get("break_and_wins"),
        payload.get("frames_stolen"),
        payload.get("timeouts"),
        row["id"]
    ))
    return True

def run():
    if not os.path.exists(DB):
        print(f"DB not found: {DB}")
        return
    c = conn()
    cur = c.cursor()
    files = sorted(glob.glob(os.path.join(MATCH_DIR, "*.json")))
    updated = 0
    audit = []
    for fp in files:
        data = parse_json(fp)
        if not isinstance(data, dict):
            continue
        a = str(data.get("player_a") or "").strip()
        b = str(data.get("player_b") or "").strip()
        if not a or not b:
            continue
        game = normalize_game(pick(data, STAT_KEYS["game_type"]))
        pa = {
            "avg_frametime": pick(data, STAT_KEYS["avg_frametime_a"]),
            "runouts": pick(data, STAT_KEYS["runouts_a"]),
            "break_and_wins": pick(data, STAT_KEYS["break_and_wins_a"]),
            "frames_stolen": pick(data, STAT_KEYS["frames_stolen_a"]),
            "timeouts": pick(data, STAT_KEYS["timeouts_a"]),
            "game_type_es": game,
        }
        pb = {
            "avg_frametime": pick(data, STAT_KEYS["avg_frametime_b"]),
            "runouts": pick(data, STAT_KEYS["runouts_b"]),
            "break_and_wins": pick(data, STAT_KEYS["break_and_wins_b"]),
            "frames_stolen": pick(data, STAT_KEYS["frames_stolen_b"]),
            "timeouts": pick(data, STAT_KEYS["timeouts_b"]),
            "game_type_es": game,
        }
        ua = update_latest_row(cur, a, b, pa)
        ub = update_latest_row(cur, b, a, pb)
        if ua: updated += 1
        if ub: updated += 1
        audit.append({
            "file": os.path.basename(fp),
            "player_a": a,
            "player_b": b,
            "game_type_es": game,
            "updated_a": ua,
            "updated_b": ub,
            "payload_a": pa,
            "payload_b": pb
        })
    c.commit()
    c.close()
    with open(AUDIT, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "updated_rows": updated, "files": audit}, f, ensure_ascii=False, indent=2)
    log(f"Deep final stats parser updated rows: {updated}")

if __name__ == "__main__":
    run()
