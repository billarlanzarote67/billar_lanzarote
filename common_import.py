
import json, os, re, sqlite3, time, uuid
from pathlib import Path

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def load_config():
    with open(r"C:\AI\BillarLanzarote\config\cuescore_importer_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def init_schema(db_path, schema_path):
    ensure_dir(os.path.dirname(db_path))
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    con.commit()
    con.close()

def slug(text):
    text = re.sub(r'[^A-Za-z0-9._-]+', '_', text.strip())
    return text[:120] if text else "item"

def extract_numeric_id_from_url(url):
    m = re.search(r'/(\d+)(?:\?.*)?$', url)
    return m.group(1) if m else None

def save_text(path, content):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def find_or_create_player(db_path, display_name):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT player_id FROM players WHERE display_name = ?", (display_name,))
    row = cur.fetchone()
    if row:
        con.close()
        return row[0]
    pid = str(uuid.uuid4())
    cur.execute("INSERT INTO players(player_id, display_name, created_ts_utc, notes) VALUES (?, ?, ?, ?)",
                (pid, display_name, utc_now(), "Auto-created from CueScore import"))
    con.commit()
    con.close()
    return pid

def insert_raw_import(db_path, source_type, source_url, cuescore_match_id=None, cuescore_player_id=None, raw_html_path=None, screenshot_path=None, raw_json=None, parse_status="imported"):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
    INSERT INTO cuescore_import_raw(
      import_id, imported_ts_utc, source_type, source_url, cuescore_match_id, cuescore_player_id,
      raw_html_path, screenshot_path, raw_json, parse_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()), utc_now(), source_type, source_url, cuescore_match_id, cuescore_player_id,
        raw_html_path, screenshot_path, json.dumps(raw_json, ensure_ascii=False) if raw_json else None, parse_status
    ))
    con.commit()
    con.close()

def log_event_if_possible(db_path, event_type, payload, table_id="system"):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("""
        INSERT INTO events(event_id, ts_utc, table_id, match_id, source, type, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), utc_now(), table_id, None, "cuescore_importer", event_type, json.dumps(payload, ensure_ascii=False)))
        con.commit()
        con.close()
    except Exception:
        pass
