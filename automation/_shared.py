import json, os, time, re, hashlib
def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return default
def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
def ts_utc(): return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def norm(t): return re.sub(r"\s+", " ", (t or "").strip())
def short_hash(t): return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]
