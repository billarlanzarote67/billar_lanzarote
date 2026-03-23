import json, os, time, hashlib, re

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def ts_utc(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def norm(text): return re.sub(r"\s+", " ", (text or "").strip())
