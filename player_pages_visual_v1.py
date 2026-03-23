import os, sqlite3, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PHOTOS_DIR = os.path.join(ROOT, "data", "player_photos")
PORT_GALLERY = 8099
PORT_H2H = 8097
PORT_PROFILE = 8101

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(cur, table_name):
    return bool(cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table_name,)).fetchone())

def render_page(title, body):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; background:#111; color:#eee; margin:20px; }}
.header {{ background: linear-gradient(90deg,#2b2b2b,#ff5a36); padding:16px; border-radius:16px; margin-bottom:20px; font-weight:bold; font-size:22px; }}
.small {{ color:#d6b08f; font-size:14px; margin-bottom:18px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px,1fr)); gap:16px; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:16px; }}
.name {{ font-size:22px; font-weight:bold; margin-bottom:8px; }}
.meta {{ color:#ddd; line-height:1.7; }}
a {{ color:#8ecbff; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.tag {{ display:inline-block; background:#2a2a2a; border-radius:999px; padding:4px 10px; margin-right:6px; margin-top:8px; font-size:12px; color:#ffd6c7; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th, td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
.good {{ color:#7ee787; }}
.bad {{ color:#ff7b72; }}
.photo {{ width:96px; height:96px; border-radius:12px; object-fit:cover; border:1px solid #333; background:#222; }}
.profile-wrap {{ display:grid; grid-template-columns: 110px 1fr; gap:16px; align-items:start; }}
</style></head><body>{body}</body></html>"""

def serve(handler, text):
    data = text.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

def slugify(name):
    safe = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe

def photo_path_for(name):
    if not os.path.isdir(PHOTOS_DIR):
        return None
    stem = slugify(name)
    for ext in [".jpg",".jpeg",".png",".webp"]:
        p = os.path.join(PHOTOS_DIR, stem + ext)
        if os.path.exists(p):
            return p
    return None

def img_html(name):
    path = photo_path_for(name)
    if path:
        return f"<img class='photo' src='file:///{html.escape(path.replace(chr(92), '/'))}'>"
    return "<div class='photo'></div>"

def all_players():
    conn = connect()
    cur = conn.cursor()
    players = []
    if table_exists(cur, "player_profiles"):
        players = [dict(r) for r in cur.execute("""SELECT player_name,matches_played,matches_won,matches_lost,frames_won,frames_lost,win_pct FROM player_profiles ORDER BY matches_played DESC,matches_won DESC,player_name ASC""").fetchall()]
    conn.close()
    return players

def player_rows(player):
    conn = connect()
    cur = conn.cursor()
    rows = []
    if table_exists(cur, "player_match_history"):
        rows = cur.execute("""SELECT id,opponent_name,table_key,game_type_es,did_win,frames_won,frames_lost,stats_status,avg_frametime,created_ts_utc FROM player_match_history WHERE player_name=? ORDER BY id DESC""", (player,)).fetchall()
    conn.close()
    return rows

def h2h_rows(player):
    conn = connect()
    cur = conn.cursor()
    rows = []
    if table_exists(cur, "player_match_history"):
        rows = cur.execute("""SELECT opponent_name,COUNT(*) AS played,SUM(CASE WHEN did_win=1 THEN 1 ELSE 0 END) AS wins,SUM(CASE WHEN did_win=0 THEN 1 ELSE 0 END) AS losses,SUM(frames_won) AS frames_won,SUM(frames_lost) AS frames_lost FROM player_match_history WHERE player_name=? GROUP BY opponent_name ORDER BY played DESC,wins DESC,opponent_name ASC""", (player,)).fetchall()
    conn.close()
    return rows

class GalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        players = all_players()
        body = "<div class='header'>Billar Lanzarote Player Gallery</div><div class='small'>Jugadores importados + perfiles locales + fotos locales si existen</div>"
        if not players:
            body += "<div class='card'>No hay jugadores todavía.</div>"
        else:
            body += "<div class='grid'>"
            for p in players:
                name = p["player_name"]
                body += ("<div class='card'><div class='profile-wrap'>"
                    f"{img_html(name)}<div><div class='name'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(name)}'>{html.escape(name)}</a></div>"
                    f"<div class='meta'>Jugadas: {p['matches_played']}<br>Ganadas: {p['matches_won']}<br>Perdidas: {p['matches_lost']}<br>Frames G: {p['frames_won']}<br>Frames P: {p['frames_lost']}<br>Win %: {round(float(p['win_pct'] or 0), 2)}</div>"
                    "<div><span class='tag'>Perfil</span><span class='tag'>Jugador</span></div></div></div></div>")
            body += "</div>"
        serve(self, render_page("Billar Lanzarote Player Gallery", body))

class ProfileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        player = parse_qs(urlparse(self.path).query).get("player", [""])[0]
        players = {p["player_name"]: p for p in all_players()}
        body = "<div class='header'>Perfil de jugador</div><div class='small'><a href='http://127.0.0.1:8099'>← Volver a Gallery</a> · <a href='http://127.0.0.1:8097'>Abrir H2H</a></div>"
        if not player:
            body += "<div class='card'>No se ha seleccionado jugador.</div>"
            serve(self, render_page("Perfil de jugador", body))
            return
        p = players.get(player, {"matches_played":0,"matches_won":0,"matches_lost":0,"frames_won":0,"frames_lost":0,"win_pct":0})
        body += ("<div class='card'><div class='profile-wrap'>"
            f"{img_html(player)}<div><div class='name'>{html.escape(player)}</div>"
            f"<div class='meta'>Jugadas: {p['matches_played']} &nbsp; Ganadas: <span class='good'>{p['matches_won']}</span> &nbsp; Perdidas: <span class='bad'>{p['matches_lost']}</span> &nbsp; Frames G: {p['frames_won']} &nbsp; Frames P: {p['frames_lost']} &nbsp; Win %: {round(float(p['win_pct'] or 0), 2)}</div>"
            "<div><span class='tag'>Perfil local</span></div></div></div></div>")
        rows = player_rows(player)
        if rows:
            body += "<div class='card'><h2>Partidas en Mesa 1 y Mesa 2</h2><table><tr><th>ID</th><th>Rival</th><th>Mesa</th><th>Juego</th><th>Resultado</th><th>Frames</th><th>Estado stats</th><th>Tiempo medio</th><th>Creado</th></tr>"
            for r in rows:
                result = "Ganó" if int(r["did_win"] or 0) == 1 else "Perdió"
                cls = "good" if int(r["did_win"] or 0) == 1 else "bad"
                juego = r["game_type_es"] if r["game_type_es"] else "Sin juego"
                body += f"<tr><td>{r['id']}</td><td>{html.escape(str(r['opponent_name'] or ''))}</td><td>{html.escape(str(r['table_key'] or ''))}</td><td>{html.escape(str(juego))}</td><td class='{cls}'>{result}</td><td>{r['frames_won']}-{r['frames_lost']}</td><td>{html.escape(str(r['stats_status'] or ''))}</td><td>{html.escape(str(r['avg_frametime'] or ''))}</td><td>{html.escape(str(r['created_ts_utc'] or ''))}</td></tr>"
            body += "</table></div>"
        else:
            body += "<div class='card'>Sin partidas locales todavía para este jugador en Mesa 1 / Mesa 2.</div>"
        serve(self, render_page(f"Perfil - {player}", body))

class H2HHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        player = parse_qs(urlparse(self.path).query).get("player", [""])[0]
        players = all_players()
        body = "<div class='header'>Billar Lanzarote H2H</div><div class='small'>Cara a cara usando perfiles locales + jugadores importados</div>"
        body += "<div class='card'><b>Jugadores:</b><br>" + " · ".join([f"<a href='/?player={quote(p['player_name'])}'>{html.escape(p['player_name'])}</a>" for p in players[:200]]) + "</div>"
        if player:
            rows = h2h_rows(player)
            body += f"<div class='card'><h2>{html.escape(player)}</h2><div class='small'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(player)}'>Abrir perfil</a></div></div>"
            if rows:
                body += "<div class='card'><h3>Resumen H2H</h3><table><tr><th>Rival</th><th>Jugadas</th><th>Ganadas</th><th>Perdidas</th><th>Frames G</th><th>Frames P</th></tr>"
                for r in rows:
                    body += f"<tr><td>{html.escape(str(r['opponent_name'] or ''))}</td><td>{r['played']}</td><td class='good'>{r['wins']}</td><td class='bad'>{r['losses']}</td><td>{r['frames_won']}</td><td>{r['frames_lost']}</td></tr>"
                body += "</table></div>"
            else:
                body += "<div class='card'>No hay historial H2H local todavía para este jugador.</div>"
        serve(self, render_page("H2H", body))

def run(port, handler):
    print(f"Running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), handler).serve_forever()

if __name__ == "__main__":
    import sys
    mode = (sys.argv[1] if len(sys.argv) > 1 else "gallery").lower()
    if mode == "gallery": run(PORT_GALLERY, GalleryHandler)
    elif mode == "h2h": run(PORT_H2H, H2HHandler)
    elif mode == "profile": run(PORT_PROFILE, ProfileHandler)
