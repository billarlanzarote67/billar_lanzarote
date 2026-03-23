import json
import os
import sqlite3
import time
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
STATE = os.path.join(ROOT, "state", "live_tables.json")
LOG = os.path.join(ROOT, "logs", "livewatcher_db_writer_v2.log")

os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA busy_timeout=5000;")
    return con

def init_db() -> None:
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS live_table_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_key TEXT,
            table_name TEXT,
            status TEXT,
            game_type_es TEXT,
            player_a TEXT,
            player_b TEXT,
            score_a INTEGER,
            score_b INTEGER,
            score TEXT,
            race_to INTEGER,
            race_text_es TEXT,
            winner TEXT,
            source_url TEXT,
            created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS latest_table_state (
            table_key TEXT PRIMARY KEY,
            table_name TEXT,
            status TEXT,
            game_type_es TEXT,
            player_a TEXT,
            player_b TEXT,
            score_a INTEGER,
            score_b INTEGER,
            score TEXT,
            race_to INTEGER,
            race_text_es TEXT,
            winner TEXT,
            source_url TEXT,
            updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    con.close()

def load_state():
    if not os.path.exists(STATE):
        return None
    with open(STATE, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    init_db()
    last_digest = {}

    log(f"Watching: {STATE}")
    log(f"DB: {DB}")

    while True:
        try:
            data = load_state()
            if not data:
                time.sleep(2)
                continue

            con = get_conn()
            cur = con.cursor()

            tables = data.get("tables") or {}
            for table_key, st in tables.items():
                digest = json.dumps(st, sort_keys=True, ensure_ascii=False)

                if last_digest.get(table_key) == digest:
                    continue

                last_digest[table_key] = digest

                cur.execute("""
                    INSERT INTO live_table_events (
                        table_key, table_name, status, game_type_es,
                        player_a, player_b, score_a, score_b, score,
                        race_to, race_text_es, winner, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    table_key,
                    st.get("table_name"),
                    st.get("status"),
                    st.get("game_type_es"),
                    st.get("player_a"),
                    st.get("player_b"),
                    st.get("score_a"),
                    st.get("score_b"),
                    st.get("score"),
                    st.get("race_to"),
                    st.get("race_text_es"),
                    st.get("winner"),
                    st.get("source_url"),
                ))

                cur.execute("""
                    INSERT INTO latest_table_state (
                        table_key, table_name, status, game_type_es,
                        player_a, player_b, score_a, score_b, score,
                        race_to, race_text_es, winner, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(table_key) DO UPDATE SET
                        table_name=excluded.table_name,
                        status=excluded.status,
                        game_type_es=excluded.game_type_es,
                        player_a=excluded.player_a,
                        player_b=excluded.player_b,
                        score_a=excluded.score_a,
                        score_b=excluded.score_b,
                        score=excluded.score,
                        race_to=excluded.race_to,
                        race_text_es=excluded.race_text_es,
                        winner=excluded.winner,
                        source_url=excluded.source_url,
                        updated_ts_utc=CURRENT_TIMESTAMP
                """, (
                    table_key,
                    st.get("table_name"),
                    st.get("status"),
                    st.get("game_type_es"),
                    st.get("player_a"),
                    st.get("player_b"),
                    st.get("score_a"),
                    st.get("score_b"),
                    st.get("score"),
                    st.get("race_to"),
                    st.get("race_text_es"),
                    st.get("winner"),
                    st.get("source_url"),
                ))

                log(f"DB updated -> {table_key} | {st.get('status')} | {st.get('score')} | {st.get('player_a')} vs {st.get('player_b')}")

            con.commit()
            con.close()

        except Exception as e:
            log(f"ERROR: {e}")

        time.sleep(2)

if __name__ == "__main__":
    main()
