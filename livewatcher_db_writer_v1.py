
import os, json, time, sqlite3
ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
STATE = os.path.join(ROOT, "state", "live_tables.json")
def init():
    conn = sqlite3.connect(DB); cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS live_table_events (id INTEGER PRIMARY KEY AUTOINCREMENT, table_key TEXT, table_name TEXT, status TEXT, player_a TEXT, player_b TEXT, score_a INTEGER, score_b INTEGER, score TEXT, race_to INTEGER, race_text_es TEXT, winner TEXT, created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("CREATE TABLE IF NOT EXISTS latest_table_state (table_key TEXT PRIMARY KEY, table_name TEXT, status TEXT, player_a TEXT, player_b TEXT, score_a INTEGER, score_b INTEGER, score TEXT, race_to INTEGER, race_text_es TEXT, winner TEXT, updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.commit(); conn.close()
init()
last = {}
print("Watching live_tables.json for DB writes...")
while True:
    try:
        with open(STATE, "r", encoding="utf-8") as f: data = json.load(f)
        conn = sqlite3.connect(DB); cur = conn.cursor()
        for table_key, st in (data.get("tables") or {}).items():
            digest = json.dumps(st, sort_keys=True, ensure_ascii=False)
            if last.get(table_key) != digest:
                last[table_key] = digest
                cur.execute("INSERT INTO live_table_events (table_key, table_name, status, player_a, player_b, score_a, score_b, score, race_to, race_text_es, winner) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (table_key, st.get("table_name"), st.get("status"), st.get("player_a"), st.get("player_b"), st.get("score_a"), st.get("score_b"), st.get("score"), st.get("race_to"), st.get("race_text_es"), st.get("winner")))
                cur.execute("""INSERT INTO latest_table_state (table_key, table_name, status, player_a, player_b, score_a, score_b, score, race_to, race_text_es, winner)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(table_key) DO UPDATE SET
                               table_name=excluded.table_name,status=excluded.status,player_a=excluded.player_a,player_b=excluded.player_b,
                               score_a=excluded.score_a,score_b=excluded.score_b,score=excluded.score,race_to=excluded.race_to,
                               race_text_es=excluded.race_text_es,winner=excluded.winner,updated_ts_utc=CURRENT_TIMESTAMP""",
                            (table_key, st.get("table_name"), st.get("status"), st.get("player_a"), st.get("player_b"), st.get("score_a"), st.get("score_b"), st.get("score"), st.get("race_to"), st.get("race_text_es"), st.get("winner")))
                print("DB updated:", table_key, st.get("score"))
        conn.commit(); conn.close()
    except Exception as e:
        print("DB writer error:", e)
    time.sleep(2)
