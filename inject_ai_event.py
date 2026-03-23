
import os, json, sys, time
ROOT = r"C:\AI\BillarLanzarote"
RUNTIME = os.path.join(ROOT, "runtime")
os.makedirs(RUNTIME, exist_ok=True)

event_type = sys.argv[1] if len(sys.argv) > 1 else "cue_foul"
table = sys.argv[2] if len(sys.argv) > 2 else "mesa1"
payload = {
    "event_type": event_type,
    "table_key": table,
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "state": {"demo": True, "event_label": event_type}
}
path = os.path.join(RUNTIME, f"{table}_event.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print("Injected:", path)
