import os, json, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
STATE_DIR = os.path.join(ROOT, "state")
DATA_DIR = os.path.join(ROOT, "data")
LOG_DIR = os.path.join(ROOT, "logs")
PORT = 5090

STATE_FILES = [
    "live_tables.json",
    "mesa1_match.json",
    "mesa2_match.json",
    "health_state.json",
    "mesa1_overlay_state.json",
    "mesa2_overlay_state.json",
    "obs_scene_switcher_state.json",
]

def read_json(name):
    path = os.path.join(STATE_DIR, name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def render(title, body):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial,sans-serif; background:#111; color:#eee; margin:20px; }}
h1,h2,h3 {{ margin:0 0 12px 0; }}
.header {{ background:linear-gradient(90deg,#1e1e1e,#ff5a36); padding:18px; border-radius:18px; margin-bottom:18px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(260px,1fr)); gap:16px; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:16px; }}
.btnrow {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0 20px 0; }}
a.btn {{ display:inline-block; background:#2a2a2a; color:#fff; padding:10px 14px; border-radius:12px; text-decoration:none; border:1px solid #444; }}
a.btn:hover {{ background:#333; }}
.good {{ color:#7ee787; font-weight:bold; }}
.bad {{ color:#ff7b72; font-weight:bold; }}
.warn {{ color:#ffd166; font-weight:bold; }}
.small {{ color:#aaa; font-size:12px; }}
.mono {{ font-family:Consolas,monospace; }}
table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
th,td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
</style></head><body>{body}</body></html>"""

def status_chip(ok, warn=False):
    if ok is True:
        return "<span class='good'>OK</span>"
    if warn:
        return "<span class='warn'>WARN</span>"
    return "<span class='bad'>OFF</span>"

def table_card(table_key, display_name):
    st = read_json(f"{table_key}_match.json") or {}
    status = st.get("status") == "live"
    player_a = st.get("player_a") or "—"
    player_b = st.get("player_b") or "—"
    score = st.get("score") or "—"
    game = st.get("game_type_es") or "Sin juego"
    race = st.get("race_text_es") or "Carrera desconocida"
    updated = st.get("last_update") or "—"
    return f"""
    <div class='card'>
      <h3>{html.escape(display_name)}</h3>
      <div>Estado: {status_chip(status, warn=not status)}</div>
      <div>Juego: <b>{html.escape(game)}</b></div>
      <div>Partida: {html.escape(player_a)} <span class='mono'>{html.escape(score)}</span> {html.escape(player_b)}</div>
      <div>{html.escape(race)}</div>
      <div class='small'>Actualizado: {html.escape(updated)}</div>
    </div>
    """

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            live_tables = read_json("live_tables.json") or {}
            body = "<div class='header'><h1>Billar Lanzarote Control</h1><div class='small'>Recuperación UI v2 · UTF-8 limpio · capa de control local</div></div>"

            body += "<div class='btnrow'>"
            body += "<a class='btn' href='http://127.0.0.1:5098'>Abrir Stats</a>"
            body += "<a class='btn' href='http://127.0.0.1:8099'>Abrir Gallery</a>"
            body += "<a class='btn' href='http://127.0.0.1:8097'>Abrir H2H</a>"
            body += "<a class='btn' href='https://cuescore.com/scoreboard/?code=c5f492c7'>Mesa 1 CueScore</a>"
            body += "<a class='btn' href='https://cuescore.com/scoreboard/?code=0b581e05'>Mesa 2 CueScore</a>"
            body += "<a class='btn' href='/files'>Ver archivos</a>"
            body += "</div>"

            body += "<div class='grid'>"
            body += table_card("mesa1", "Mesa 1")
            body += table_card("mesa2", "Mesa 2")
            db_ok = os.path.exists(os.path.join(DATA_DIR, "billar_lanzarote.sqlite3"))
            body += f"<div class='card'><h3>Base de datos</h3><div>Estado: {status_chip(db_ok)}</div><div class='small mono'>{html.escape(os.path.join(DATA_DIR, 'billar_lanzarote.sqlite3'))}</div></div>"
            stats_ok = True
            body += f"<div class='card'><h3>Servicios UI</h3><div>Stats: {status_chip(stats_ok)}</div><div>Gallery: <span class='warn'>externo</span></div><div>H2H: <span class='warn'>externo</span></div></div>"
            body += "</div>"

            body += "<div class='card'><h2>Estado rápido</h2>"
            body += f"<div>Última actualización global: <span class='mono'>{html.escape(str(live_tables.get('last_update') or '—'))}</span></div>"
            body += "</div>"

            page = render("Billar Lanzarote Control", body)
            data = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/files":
            body = "<div class='header'><h1>Archivos clave</h1><div class='small'><a href='/'>← Volver</a></div></div>"
            body += "<div class='card'><h2>State files</h2><table><tr><th>Archivo</th><th>Existe</th></tr>"
            for name in STATE_FILES:
                ok = os.path.exists(os.path.join(STATE_DIR, name))
                body += f"<tr><td class='mono'>{html.escape(name)}</td><td>{status_chip(ok)}</td></tr>"
            body += "</table></div>"

            completed = os.path.join(DATA_DIR, "completed_matches")
            try:
                files = sorted(os.listdir(completed), reverse=True)[:20]
            except Exception:
                files = []
            body += "<div class='card'><h2>Completed matches</h2>"
            if files:
                body += "<table><tr><th>Archivo</th></tr>"
                for f in files:
                    body += f"<tr><td class='mono'>{html.escape(f)}</td></tr>"
                body += "</table>"
            else:
                body += "<div>No hay archivos todavía.</div>"
            body += "</div>"

            page = render("Billar Lanzarote Files", body)
            data = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        data = render("404", "<div class='card'><h1>404</h1></div>").encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"Master Control recovery v2 on http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
