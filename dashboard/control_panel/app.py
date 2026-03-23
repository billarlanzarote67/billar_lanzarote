import os, sys
from flask import Flask, request, redirect
sys.path.append(r"C:\AI\BillarLanzarote\automation")
from _shared import load_json, save_json, ts_utc
ROOT=r"C:\AI\BillarLanzarote"; CFG=os.path.join(ROOT,"config","live_system_config.json"); STATE=os.path.join(ROOT,"state"); RUNTIME=os.path.join(ROOT,"runtime")
app=Flask(__name__)
def manual(table, action): save_json(os.path.join(RUNTIME,f"{table}_manual.json"),{"table_key":table,"action":action,"ts":ts_utc()})
@app.route("/")
def index():
    cfg=load_json(CFG,{}); live=load_json(os.path.join(RUNTIME,"live_stream_status.json"),{"tables":{}}); tg=cfg.get("telegram",{}); cards=""
    for tk,meta in cfg.get("tables",{}).items():
        st=load_json(os.path.join(STATE,f"{tk}_live.json"),{}); ls=live.get("tables",{}).get(tk,{})
        cards += f"<div class='card'><div class='name'>{meta.get('name',tk)}</div><div class='row'><strong>Status:</strong> {'LIVE MATCH' if st.get('active') else 'IDLE'}</div><div class='row'><strong>Players:</strong> {(st.get('player_a') or '—')} vs {(st.get('player_b') or '—')}</div><div class='row'><strong>Score:</strong> {(st.get('score_a') if st.get('score_a') is not None else '—')} - {(st.get('score_b') if st.get('score_b') is not None else '—')}</div><div class='row'><strong>Discipline:</strong> {st.get('discipline') or '—'}</div><div class='row'><strong>Challenge URL:</strong> {st.get('challenge_url') or '—'}</div><div class='row'><strong>Streaming:</strong> {ls.get('is_streaming', False)}</div><div style='margin-top:12px'><a class='btn' href='/action?table={tk}&do=force_start'>Force Start</a><a class='btn danger' href='/action?table={tk}&do=force_stop'>Force Stop</a></div></div>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Control Panel</title><style>body{{font-family:Arial,sans-serif;background:#0b0b0b;color:#fff;padding:20px}}.banner{{background:linear-gradient(90deg,#1a1a1a,#ff3c00);padding:16px 20px;border-radius:16px;font-size:28px;font-weight:800;margin-bottom:20px}}.muted{{color:#ffb08f;margin-bottom:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px}}.card{{background:#141414;border:1px solid #ff7a00;border-radius:16px;padding:18px}}.name{{font-size:24px;font-weight:700;margin-bottom:10px}}.row{{margin:8px 0;word-break:break-word}}.btn{{display:inline-block;background:#ff5a00;color:#fff;text-decoration:none;padding:10px 14px;border-radius:10px;margin-right:8px}}.btn.danger{{background:#7a1c00}}</style></head><body><div class='banner'>SYSTEM OK</div><div class='muted'>Volcanic Edition • Telegram enabled: {tg.get('enabled', False)}</div><div style='margin-bottom:20px'><a class='btn' href='/toggle_telegram'>Toggle Telegram</a></div><div class='grid'>{cards}</div></body></html>"
@app.route("/action")
def action():
    table=request.args.get("table",""); todo=request.args.get("do","")
    if table and todo: manual(table,todo)
    return redirect("/")
@app.route("/toggle_telegram")
def toggle():
    cfg=load_json(CFG,{}); tg=cfg.setdefault("telegram",{}); tg["enabled"]=not tg.get("enabled",True); save_json(CFG,cfg); return redirect("/")
if __name__=="__main__":
    port=load_json(CFG,{}).get("ui",{}).get("control_panel_port",8788); app.run(host="127.0.0.1", port=port, debug=False)
