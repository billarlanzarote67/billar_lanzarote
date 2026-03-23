
import json, os, re, sqlite3, time, uuid, hashlib
from pathlib import Path

CFG_PATH = r"C:\AI\BillarLanzarote\config\stats_automation_v7.json"

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def load_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_log_root():
    cfg = load_cfg()
    ensure_dir(cfg["log_root"])

def append_log(name, message):
    ensure_log_root()
    cfg = load_cfg()
    path = os.path.join(cfg["log_root"], name)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{utc_now()}] {message}\n")

def db():
    cfg = load_cfg()
    ensure_dir(os.path.dirname(cfg["db_path"]))
    return sqlite3.connect(cfg["db_path"])

def init_sql(schema_paths):
    con = db()
    cur = con.cursor()
    for p in schema_paths:
        if os.path.exists(p):
            cur.executescript(open(p, "r", encoding="utf-8").read())
    con.commit()
    con.close()

def safe_hash(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def log_run(source_type, source_url, status, details=None):
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS importer_run_log(
      run_id TEXT PRIMARY KEY, ts_utc TEXT NOT NULL, source_type TEXT NOT NULL, source_url TEXT, status TEXT NOT NULL, details_json TEXT
    )""")
    cur.execute("""INSERT INTO importer_run_log(run_id, ts_utc, source_type, source_url, status, details_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), utc_now(), source_type, source_url, status, json.dumps(details or {}, ensure_ascii=False)))
    con.commit()
    con.close()

def player_exists_by_name(name):
    con = db(); cur = con.cursor()
    try:
        cur.execute("SELECT player_id FROM players WHERE display_name = ?", (name,))
        row = cur.fetchone()
    except sqlite3.Error:
        row = None
    con.close()
    return row[0] if row else None

def find_or_create_player(name):
    pid = player_exists_by_name(name)
    if pid:
        return pid
    con = db(); cur = con.cursor()
    pid = str(uuid.uuid4())
    try:
        cur.execute("INSERT INTO players(player_id, display_name, created_ts_utc, notes) VALUES (?, ?, ?, ?)",
                    (pid, name, utc_now(), "Auto-created by stats automation v7"))
        con.commit()
    except sqlite3.Error:
        pass
    con.close()
    return pid
