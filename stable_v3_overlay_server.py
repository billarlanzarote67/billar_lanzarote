import os, sys
from flask import Flask, jsonify, request
sys.path.append(r"C:\AI\BillarLanzarote\scripts")
from _stable_shared import load_json
ROOT=r"C:\AI\BillarLanzarote"; CFG_PATH=os.path.join(ROOT,"config","stable_v3_config.json"); STATE_DIR=os.path.join(ROOT,"state"); LANG_PATH=os.path.join(ROOT,"config","lang_es.json")
app=Flask(__name__)
@app.route("/api/overlay")
def api_overlay():
    table=request.args.get("table","mesa1"); state=load_json(os.path.join(STATE_DIR, f"{table}_live.json"), {}); cfg=load_json(CFG_PATH, {}); meta=cfg.get("tables", {}).get(table, {}); lang=load_json(LANG_PATH, {})
    return jsonify({"table_key": table, "table_name": meta.get("name", table), "player_a": state.get("player_a"), "player_b": state.get("player_b"), "score_a": state.get("score_a"), "score_b": state.get("score_b"), "discipline": state.get("discipline"), "challenge_url": state.get("challenge_url"), "active": state.get("active", False), "labels": lang})
@app.route("/")
def home(): return "Billar Lanzarote Stable Pack v3 Overlay API OK"
if __name__=="__main__":
    cfg=load_json(CFG_PATH, {}); app.run(host="127.0.0.1", port=cfg.get("ui", {}).get("overlay_port", 8789), debug=False)
