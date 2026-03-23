
import os, json
from flask import Flask, request, jsonify, send_from_directory

ROOT = r"C:\AI\BillarLanzarote_DEMO"
STATE = os.path.join(ROOT, "state")
CFG = os.path.join(ROOT, "config", "demo_config.json")
WEB = os.path.join(ROOT, "overlay", "web")

app = Flask(__name__, static_folder=WEB, static_url_path="")

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

@app.route("/overlay")
def overlay():
    return send_from_directory(WEB, "overlay.html")

@app.route("/api/overlay")
def api_overlay():
    table = request.args.get("table", "mesa1")
    st = load_json(os.path.join(STATE, f"{table}_live.json"), {})
    cfg = load_json(CFG, {})
    table_name = cfg.get("tables", {}).get(table, {}).get("name", table)
    return jsonify({
        "table_name": table_name,
        "player_a": st.get("player_a"),
        "player_b": st.get("player_b"),
        "score_a": st.get("score_a"),
        "score_b": st.get("score_b"),
        "discipline": st.get("discipline"),
        "warning": st.get("warning"),
        "mode": st.get("mode", "normal"),
        "active": st.get("active", False)
    })

if __name__ == "__main__":
    cfg = load_json(CFG, {})
    port = cfg.get("ui", {}).get("overlay_port", 8799)
    app.run(host="127.0.0.1", port=port, debug=False)
