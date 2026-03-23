
import json, os, time
ROOT = r"C:\AI\BillarLanzarote"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def estimate_prob(label, conf):
    base = {"CHUPADO":0.92,"REGALADO":0.82,"FACILITO":0.68,"TIENE TRAMPA":0.52,"JODIDO":0.31,"MISIÓN IMPOSIBLE":0.14}.get(label, 0.5)
    return round(max(0.01, min(0.99, base * max(0.5, conf))), 2)

for mesa in ("mesa1","mesa2"):
    h = load_json(os.path.join(ROOT, "state", f"{mesa}_shot_hardness.json"))
    if not h: continue
    label = h["hardness"]["label"]; conf = h["hardness"]["confidence_0_1"]
    p_make = estimate_prob(label, conf)
    with open(os.path.join(ROOT, "state", f"{mesa}_probability_state.json"), "w", encoding="utf-8") as f:
        json.dump({"schema":"bl.probability.v1","table_id":mesa,"ts_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"label":label,"confidence_0_1":conf,"p_make":p_make}, f, indent=2, ensure_ascii=False)
    print(f"{mesa}: p_make={p_make}")
