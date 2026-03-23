import os, sys, sqlite3
from flask import Flask
sys.path.append(r"C:\AI\BillarLanzarote\scripts")
from _stable_shared import load_json
ROOT=r"C:\AI\BillarLanzarote"; CFG_PATH=os.path.join(ROOT,"config","stable_v3_config.json"); STATE_DIR=os.path.join(ROOT,"state"); DB_PATH=os.path.join(ROOT,"data","db","billar_lanzarote.db"); LANG_PATH=os.path.join(ROOT,"config","lang_es.json")
app=Flask(__name__)
def get_recent_matches():
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor(); cur.execute("SELECT table_name, player_a, player_b, score_a, score_b, timestamp FROM matches ORDER BY id DESC LIMIT 10"); rows=cur.fetchall(); conn.close(); return rows
@app.route("/")
def index():
    cfg=load_json(CFG_PATH, {}); lang=load_json(LANG_PATH, {}); cards=""
    for table_key, meta in cfg.get("tables", {}).items():
        st=load_json(os.path.join(STATE_DIR, f"{table_key}_live.json"), {}); status=lang.get("status_live","PARTIDA EN CURSO") if st.get("active") else lang.get("status_idle","EN ESPERA")
        cards += f"<div class='card'><div class='name'>{meta.get('name', table_key)}</div><div class='row'><strong>Estado:</strong> {status}</div><div class='row'><strong>{lang.get('players','Jugadores')}:</strong> {(st.get('player_a') or '—')} vs {(st.get('player_b') or '—')}</div><div class='row'><strong>{lang.get('score','Marcador')}:</strong> {(st.get('score_a') if st.get('score_a') is not None else '—')} - {(st.get('score_b') if st.get('score_b') is not None else '—')}</div><div class='row'><strong>{lang.get('discipline','Modalidad')}:</strong> {st.get('discipline') or '—'}</div><div class='row'><strong>URL:</strong> {st.get('challenge_url') or '—'}</div></div>"
    rows=""
    for row in get_recent_matches(): rows += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}-{row[4]}</td><td>{row[5]}</td></tr>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Billar Lanzarote Stable Pack v3</title><style>body{{font-family:Arial,sans-serif;background:#0b0b0b;color:#fff;padding:20px}}.banner{{background:linear-gradient(90deg,#1a1a1a,#ff3c00);padding:16px 20px;border-radius:16px;font-size:28px;font-weight:800;box-shadow:0 8px 24px rgba(0,0,0,.35);margin-bottom:20px}}.muted{{color:#ffb08f;margin-bottom:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px}}.card{{background:#141414;border:1px solid #ff7a00;border-radius:16px;padding:18px;box-shadow:0 6px 20px rgba(0,0,0,.25)}}.name{{font-size:24px;font-weight:700;margin-bottom:10px}}.row{{margin:8px 0;word-break:break-word}}table{{width:100%;border-collapse:collapse;background:#141414;border:1px solid #ff7a00;border-radius:16px;overflow:hidden}}th,td{{padding:10px;border-bottom:1px solid #2a2a2a;text-align:left}}th{{background:#1a1a1a}}</style></head><body><div class='banner'>{lang.get('system_ok','SISTEMA OK')}</div><div class='muted'>Stable Pack v3 • Billar Lanzarote • tema volcánico</div><div class='grid'>{cards}</div><h2 style='margin-top:28px'>{lang.get('recent_matches','Partidas recientes')}</h2><table><thead><tr><th>Mesa</th><th>Jugador A</th><th>Jugador B</th><th>{lang.get('score','Marcador')}</th><th>Fecha</th></tr></thead><tbody>{rows}</tbody></table></body></html>"
if __name__=="__main__":
    cfg=load_json(CFG_PATH, {}); app.run(host="127.0.0.1", port=cfg.get("ui", {}).get("control_panel_port", 8788), debug=False)
