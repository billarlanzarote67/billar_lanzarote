import os, sqlite3, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PORT = 8099

def fetch_all(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def render(title, body):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; background:#111; color:#eee; margin:20px; }}
.header {{ background: linear-gradient(90deg,#2b2b2b,#ff5a36); padding:16px; border-radius:16px; margin-bottom:20px; font-weight:bold; font-size:22px; }}
.small {{ color:#d6b08f; font-size:14px; margin-bottom:18px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(260px,1fr)); gap:16px; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:16px; }}
.name {{ font-size:22px; font-weight:bold; margin-bottom:8px; }}
.meta {{ color:#ddd; line-height:1.7; }}
a {{ color:#8ecbff; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.tag {{ display:inline-block; background:#2a2a2a; border-radius:999px; padding:4px 10px; margin-right:6px; margin-top:8px; font-size:12px; color:#ffd6c7; }}
</style></head><body>{body}</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        players = fetch_all("""
            SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost,
                   ROUND(win_pct, 2) AS win_pct, updated_ts_utc
            FROM player_profiles
            ORDER BY matches_played DESC, matches_won DESC, player_name ASC
        """)

        body = "<div class='header'>Billar Lanzarote Player Gallery</div>"
        body += "<div class='small'>Tema volcánico · vista bonita · texto jugadores en español</div>"
        if not players:
            body += "<div class='card'>No hay jugadores todavía en la base de datos.</div>"
        else:
            body += "<div class='grid'>"
            for p in players:
                name = p["player_name"] or ""
                card = (
                    "<div class='card'>"
                    f"<div class='name'><a href='http://127.0.0.1:8097/?player={quote(name)}'>{html.escape(name)}</a></div>"
                    f"<div class='meta'>Jugadas: {p['matches_played']}<br>"
                    f"Ganadas: {p['matches_won']}<br>"
                    f"Perdidas: {p['matches_lost']}<br>"
                    f"Frames G: {p['frames_won']}<br>"
                    f"Frames P: {p['frames_lost']}<br>"
                    f"Win %: {p['win_pct']}</div>"
                    "<div>"
                    f"<span class='tag'>Perfil</span>"
                    f"<span class='tag'>Jugador</span>"
                    "</div>"
                    "</div>"
                )
                body += card
            body += "</div>"

        page = render("Billar Lanzarote Player Gallery", body)
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"Player gallery running on http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
