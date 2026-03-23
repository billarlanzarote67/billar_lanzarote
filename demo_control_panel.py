
import os, json
from flask import Flask, redirect, request

ROOT = r"C:\AI\BillarLanzarote_DEMO"
STATE = os.path.join(ROOT, "state")
CFG = os.path.join(ROOT, "config", "demo_config.json")
RUNTIME = os.path.join(ROOT, "runtime")

app = Flask(__name__)

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    cfg = load_json(CFG, {})
    cards = ""
    for table_key, meta in cfg.get("tables", {}).items():
        st = load_json(os.path.join(STATE, f"{table_key}_live.json"), {})
        cards += f"""
        <div class='card'>
          <div class='name'>{meta.get('name', table_key)}</div>
          <div class='row'><strong>Status:</strong> {'LIVE MATCH' if st.get('active') else 'IDLE'}</div>
          <div class='row'><strong>Players:</strong> {(st.get('player_a') or '—')} vs {(st.get('player_b') or '—')}</div>
          <div class='row'><strong>Score:</strong> {(st.get('score_a') if st.get('score_a') is not None else '—')} - {(st.get('score_b') if st.get('score_b') is not None else '—')}</div>
          <div class='row'><strong>Discipline:</strong> {st.get('discipline') or '—'}</div>
          <div class='row'><strong>Warning:</strong> {st.get('warning') or '—'}</div>
          <div style='margin-top:12px'>
            <a class='btn' href='/inject?table={table_key}&do=foul'>Inject Foul</a>
            <a class='btn' href='/inject?table={table_key}&do=cluster'>Inject Cluster</a>
            <a class='btn danger' href='/inject?table={table_key}&do=end'>Force End</a>
          </div>
        </div>
        """
    return f"""
    <!doctype html>
    <html><head><meta charset='utf-8'><title>BL Demo Control Panel</title>
    <style>
    body{{font-family:Arial,sans-serif;background:#0b0b0b;color:#fff;padding:20px}}
    .banner{{background:linear-gradient(90deg,#1a1a1a,#ff3c00);padding:16px 20px;border-radius:16px;font-size:28px;font-weight:800;margin-bottom:20px}}
    .muted{{color:#ffb08f;margin-bottom:18px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px}}
    .card{{background:#141414;border:1px solid #ff7a00;border-radius:16px;padding:18px}}
    .name{{font-size:24px;font-weight:700;margin-bottom:10px}}
    .row{{margin:8px 0;word-break:break-word}}
    .btn{{display:inline-block;background:#ff5a00;color:#fff;text-decoration:none;padding:10px 14px;border-radius:10px;margin-right:8px}}
    .btn.danger{{background:#7a1c00}}
    </style></head>
    <body>
      <div class='banner'>DEMO SYSTEM OK</div>
      <div class='muted'>Independent demo environment • safe to turn off before club</div>
      <div class='grid'>{cards}</div>
    </body></html>
    """

@app.route("/inject")
def inject():
    table = request.args.get("table", "mesa1")
    todo = request.args.get("do", "")
    path = os.path.join(STATE, f"{table}_live.json")
    st = load_json(path, {}) or {}
    if todo == "foul":
        st["warning"] = "Cue ball pocketed • foul warning"
    elif todo == "cluster":
        st["warning"] = "Ball cluster detected"
    elif todo == "end":
        st["active"] = False
        st["warning"] = "Match ended"
    save_json(path, st)
    return redirect("/")

if __name__ == "__main__":
    cfg = load_json(CFG, {})
    port = cfg.get("ui", {}).get("dashboard_port", 8798)
    app.run(host="127.0.0.1", port=port, debug=False)
