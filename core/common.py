
import json, os, tempfile, time, sqlite3, uuid
from pathlib import Path

def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def atomic_write_json(path, data):
    ensure_parent(path)
    fd, tmp = tempfile.mkstemp(prefix="tmp_", suffix=".json", dir=str(Path(path).parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except: pass

def append_jsonl(path, obj):
    ensure_parent(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def init_db(db_path):
    ensure_parent(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS events (
      event_id TEXT PRIMARY KEY,
      ts_utc TEXT NOT NULL,
      table_id TEXT NOT NULL,
      match_id TEXT,
      source TEXT NOT NULL,
      type TEXT NOT NULL,
      payload_json TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS shots (
      shot_id TEXT PRIMARY KEY,
      table_id TEXT NOT NULL,
      match_id TEXT,
      ts_start_utc TEXT NOT NULL,
      ts_end_utc TEXT,
      hardness_score REAL,
      hardness_band TEXT,
      hardness_confidence REAL,
      outcome TEXT,
      replay_clip_path TEXT
    );
    ''')
    con.commit()
    con.close()
