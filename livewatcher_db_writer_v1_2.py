import os
import json
import time
import sqlite3
import traceback
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
STATE = os.path.join(ROOT, "state", "live_tables.json")
LOG = os.path.join(ROOT, "logs", "livewatcher_db_writer_v1_2.log")

os.makedirs(os.path.dirname(DB), exist_ok=True)
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def connect_db():
    conn = sqlite3.connect(DB, timeout=20, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=20000;")
    return conn

def init(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_table_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_key TEXT,
        table_name TEXT,
        status TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        score TEXT,
        race_to INTEGER,
        race_text_es TEXT,
        winner TEXT,
        loser TEXT,
        source_url TEXT,
        raw_player_a TEXT,
        raw_player_b TEXT,
        created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS latest_table_state (
        table_key TEXT PRIMARY KEY,
        table_name TEXT,
        status TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        score TEXT,
        race_to INTEGER,
        race_text_es TEXT,
        winner TEXT,
        loser TEXT,
        source_url TEXT,
        raw_player_a TEXT,
        raw_player_b TEXT,
        updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def main():
    conn = connect_db()
    init(conn)
    last = {}
    log("Watching live_tables.json for DB writes...")
    while True:
        try:
            with open(STATE, "r", encoding="utf-8") as f:
                data = json.load(f)

            cur = conn.cursor()
            changed = 0
            for table_key, st in (data.get("tables") or {}).items():
                digest = json.dumps(st, sort_keys=True, ensure_ascii=False)
                if last.get(table_key) == digest:
                    continue
                last[table_key] = digest
                changed += 1

                cur.execute("""
                    INSERT INTO live_table_events (
                        table_key, table_name, status, player_a, player_b, score_a, score_b,
                        score, race_to, race_text_es, winner, loser, source_url, raw_player_a, raw_player_b
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    table_key, st.get("table_name"), st.get("status"), st.get("player_a"), st.get("player_b"),
                    st.get("score_a"), st.get("score_b"), st.get("score"), st.get("race_to"),
                    st.get("race_text_es"), st.get("winner"), st.get("loser"), st.get("source_url"),
                    st.get("raw_player_a"), st.get("raw_player_b")
                ))

                cur.execute("""
                    INSERT INTO latest_table_state (
                        table_key, table_name, status, player_a, player_b, score_a, score_b,
                        score, race_to, race_text_es, winner, loser, source_url, raw_player_a, raw_player_b
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(table_key) DO UPDATE SET
                        table_name=excluded.table_name,
                        status=excluded.status,
                        player_a=excluded.player_a,
                        player_b=excluded.player_b,
                        score_a=excluded.score_a,
                        score_b=excluded.score_b,
                        score=excluded.score,
                        race_to=excluded.race_to,
                        race_text_es=excluded.race_text_es,
                        winner=excluded.winner,
                        loser=excluded.loser,
                        source_url=excluded.source_url,
                        raw_player_a=excluded.raw_player_a,
                        raw_player_b=excluded.raw_player_b,
                        updated_ts_utc=CURRENT_TIMESTAMP
                """, (
                    table_key, st.get("table_name"), st.get("status"), st.get("player_a"), st.get("player_b"),
                    st.get("score_a"), st.get("score_b"), st.get("score"), st.get("race_to"),
                    st.get("race_text_es"), st.get("winner"), st.get("loser"), st.get("source_url"),
                    st.get("raw_player_a"), st.get("raw_player_b")
                ))
                log(f"DB updated: {table_key} {st.get('score')} {st.get('player_a')} vs {st.get('player_b')}")

            if changed:
                conn.commit()

        except sqlite3.OperationalError as e:
            log(f"SQLite operational error: {e}")
            time.sleep(2)
            try:
                conn.close()
            except Exception:
                pass
            conn = connect_db()
            init(conn)

        except FileNotFoundError:
            log(f"State file not found yet: {STATE}")

        except json.JSONDecodeError:
            log("State file is being written right now, retrying...")

        except Exception as e:
            log(f"DB writer fatal-ish error: {e}")
            log(traceback.format_exc())

        time.sleep(2)

if __name__ == "__main__":
    main()
