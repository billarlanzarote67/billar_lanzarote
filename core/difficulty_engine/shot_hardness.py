
import json, os, time
ROOT = r"C:\AI\BillarLanzarote"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def map_score(score):
    if score <= 10: return "CHUPADO"
    if score <= 22: return "REGALADO"
    if score <= 38: return "FACILITO"
    if score <= 58: return "TIENE TRAMPA"
    if score <= 78: return "JODIDO"
    return "MISIÓN IMPOSIBLE"

for mesa in ("mesa1","mesa2"):
    p = os.path.join(ROOT, "state", f"{mesa}_table_state.json")
    d = load_json(p)
    if not d: continue
    count = len(d.get("balls", []))
    motion = d.get("quality", {}).get("motion_score", 0)
    score = min(100, 15 + count * 4 + int(motion / 12000))
    conf = min(0.85, 0.25 + count / 20.0)
    label = map_score(score)
    out = os.path.join(ROOT, "state", f"{mesa}_shot_hardness.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "schema": "bl.shot_hardness.v1",
            "table_id": mesa,
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hardness": {"score_0_100": score, "label": label, "confidence_0_1": conf},
            "public_overlay": {"visible": conf >= 0.72, "text": f"Dificultad: {label}" if conf >= 0.72 else ""}
        }, f, indent=2, ensure_ascii=False)
    print(f"{mesa}: Dificultad: {label} ({conf:.2f})")
