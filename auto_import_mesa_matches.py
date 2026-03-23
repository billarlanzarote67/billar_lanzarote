
import os, json, time, subprocess
from stats_automation_common import load_cfg, ensure_dir, append_log, safe_hash, log_run

PY = r"C:\Program Files\Python312\python.exe"
IMPORT_SCRIPT = r"C:\AI\BillarLanzarote\scripts\import_finished_match.py"

def read_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def discover_urls(obj):
    found = []
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for v in cur.values():
                if isinstance(v, str) and "cuescore.com" in v and ("match" in v.lower() or "challenge" in v.lower() or "scoreboard" in v.lower()):
                    found.append(v)
                elif isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return list(dict.fromkeys(found))

def load_done(queue_file):
    if not os.path.exists(queue_file):
        return {"done": [], "history": []}
    try:
        return json.load(open(queue_file, "r", encoding="utf-8"))
    except Exception:
        return {"done": [], "history": []}

def save_done(queue_file, data):
    ensure_dir(os.path.dirname(queue_file))
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    cfg = load_cfg()
    qf = cfg["queue_file"]
    state = load_done(qf)
    done = set(state.get("done", []))
    poll = int(cfg.get("poll_seconds", 60))
    append_log("auto_import.log", "Auto import watcher started")
    while True:
        changed = False
        for path in cfg.get("mesa_state_files", []):
            st = read_json(path)
            if not st:
                continue
            for url in discover_urls(st):
                key = safe_hash(url)
                if key in done:
                    continue
                res = subprocess.run([PY, IMPORT_SCRIPT, url], capture_output=True, text=True)
                if res.returncode == 0:
                    done.add(key)
                    state.setdefault("history", []).append({"url": url, "status": "ok"})
                    append_log("auto_import.log", f"OK {url}")
                    log_run("auto_match_import", url, "ok", {"stdout": res.stdout[-500:]})
                    changed = True
                else:
                    state.setdefault("history", []).append({"url": url, "status": "fail", "stderr": res.stderr[-500:]})
                    append_log("auto_import.log", f"FAIL {url} :: {res.stderr[-500:]}")
                    log_run("auto_match_import", url, "fail", {"stderr": res.stderr[-500:]})
                    changed = True
        if changed:
            state["done"] = sorted(done)
            save_done(qf, state)
        time.sleep(poll)

if __name__ == "__main__":
    main()
