
import os, time, json
ROOT = r"C:\AI\BillarLanzarote"
RUNTIME = os.path.join(ROOT, "runtime")
LOG = os.path.join(ROOT, "logs", "ai_framework", "ai_events.jsonl")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
os.makedirs(RUNTIME, exist_ok=True)

print("Watching runtime for *_event.json files...")
seen = {}
while True:
    for name in os.listdir(RUNTIME):
        if name.endswith("_event.json"):
            path = os.path.join(RUNTIME, name)
            mtime = os.path.getmtime(path)
            if seen.get(path) != mtime:
                seen[path] = mtime
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    with open(LOG, "a", encoding="utf-8") as out:
                        out.write(json.dumps(data, ensure_ascii=False) + "\n")
                    print("Logged:", name, data.get("event_type"))
                except Exception as e:
                    print("Error:", e)
    time.sleep(2)
