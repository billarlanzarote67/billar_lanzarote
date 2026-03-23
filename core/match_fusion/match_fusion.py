
import json, os, time
ROOT = r"C:\AI\BillarLanzarote"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

for mesa in ("mesa1","mesa2"):
    fused = {
        "schema": "bl.fused_state.v1",
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "table_id": mesa,
        "cuescore": load_json(os.path.join(ROOT, "state", "cuescore_state.json")),
        "ai": load_json(os.path.join(ROOT, "state", f"{mesa}_ai_state.json")),
        "hardness": load_json(os.path.join(ROOT, "state", f"{mesa}_shot_hardness.json"))
    }
    with open(os.path.join(ROOT, "state", f"{mesa}_fused_state.json"), "w", encoding="utf-8") as f:
        json.dump(fused, f, indent=2, ensure_ascii=False)
    print(f"wrote fused state for {mesa}")
