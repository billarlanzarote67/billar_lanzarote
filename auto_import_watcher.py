
import json, os, time, sqlite3, uuid, subprocess
from pathlib import Path

CFG_PATH = r"C:\AI\BillarLanzarote\config\player_stats_dashboard_config.json"
IMPORTER_SCRIPT = r"C:\AI\BillarLanzarote\scripts\import_finished_match.py"
PYTHON_PATH = r"C:\Program Files\Python312\python.exe"

with open(CFG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

DB = CFG["db_path"]
QUEUE_FILE = CFG["auto_import_queue_file"]

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def ensure_queue():
    Path(os.path.dirname(QUEUE_FILE)).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump({"items": []}, f, indent=2)

def load_queue():
    ensure_queue()
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_queue(data):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_queue(source_url, source_type, table_id, status, result=None):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS importer_queue_log (
      queue_id TEXT PRIMARY KEY,
      queued_ts_utc TEXT NOT NULL,
      table_id TEXT,
      source_url TEXT NOT NULL,
      source_type TEXT NOT NULL,
      queue_status TEXT NOT NULL,
      result_json TEXT
    )
    """)
    cur.execute("""
    INSERT INTO importer_queue_log(queue_id, queued_ts_utc, table_id, source_url, source_type, queue_status, result_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), utc_now(), table_id, source_url, source_type, status, json.dumps(result or {}, ensure_ascii=False)))
    con.commit()
    con.close()

def read_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def discover_finished_match_urls():
    found = []
    for p in CFG.get("cuescore_state_paths", []):
        st = read_json(p)
        if not st:
            continue
        table_id = os.path.basename(p).split("_")[0]
        stack = [st]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for _, v in cur.items():
                    if isinstance(v, str) and "cuescore.com" in v and ("match" in v.lower() or "challenge" in v.lower()):
                        found.append({"table_id": table_id, "source_url": v, "source_type": "match"})
                    elif isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(cur, list):
                stack.extend(cur)
    seen = set()
    dedup = []
    for f in found:
        if f["source_url"] not in seen:
            seen.add(f["source_url"])
            dedup.append(f)
    return dedup

def run_import(url):
    cmd = [PYTHON_PATH, IMPORTER_SCRIPT, url]
    return subprocess.run(cmd, capture_output=True, text=True)

def main():
    ensure_queue()
    print("CueScore auto import watcher started")
    while True:
        q = load_queue()
        items = q.get("items", [])
        existing = {i["source_url"] for i in items}
        changed = False
        for d in discover_finished_match_urls():
            if d["source_url"] not in existing:
                items.append({"table_id": d["table_id"], "source_url": d["source_url"], "source_type": d["source_type"], "status": "queued"})
                log_queue(d["source_url"], d["source_type"], d["table_id"], "queued", {"reason": "discovered_from_cuescore_state"})
                changed = True
        for item in items:
            if item.get("status") == "queued":
                res = run_import(item["source_url"])
                item["status"] = "done" if res.returncode == 0 else "failed"
                item["last_stdout"] = res.stdout[-1000:]
                item["last_stderr"] = res.stderr[-1000:]
                log_queue(item["source_url"], item["source_type"], item.get("table_id"), item["status"], {"stdout": item["last_stdout"], "stderr": item["last_stderr"]})
                changed = True
        if changed:
            save_queue({"items": items})
        time.sleep(int(CFG.get("auto_import_poll_seconds", 20)))

if __name__ == "__main__":
    main()
