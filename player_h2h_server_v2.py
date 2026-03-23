import os, sqlite3, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PORT = 8097

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
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th, td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
.good {{ color:#7ee787; }}
.bad {{ color:#ff7b72; }}
a {{ color:#8ecbff; text-decoration:none; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:16px; margin-bottom:18px; }}
</style></head><body>{body}</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        selected = qs.get("player", [""])[0]

        players = fetch_all("""
            SELECT player_name FROM player_profiles
            ORDER BY matches_played DESC, player_name ASC
        """)

        body = "<div class='header'>Billar Lanzarote H2H</div>"
        body += "<div class='small'>Cara a cara usando la base de datos actual</div>"

        if not players:
            body += "<div class='card'>No hay jugadores todavía.</div>"
        else:
            body += "<div class='card'><b>Jugadores:</b><br>"
            body += " · ".join([f"<a href='/?player={quote(p['player_name'])}'>{html.escape(p['player_name'])}</a>" for p in players])
            body += "</div>"

        if selected:
            matches = fetch_all("""
                SELECT player_name, opponent_name, game_type_es, did_win, frames_won, frames_lost,
                       created_ts_utc
                FROM player_match_history
                WHERE player_name = ?
                ORDER BY created_ts_utc DESC
            """, (selected,))

            summary = fetch_all("""
                SELECT
                    opponent_name,
                    COUNT(*) AS played,
                    SUM(CASE WHEN did_win = 1 THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN did_win = 0 THEN 1 ELSE 0 END) AS losses,
                    SUM(frames_won) AS frames_won,
                    SUM(frames_lost) AS frames_lost
                FROM player_match_history
                WHERE player_name = ?
                GROUP BY opponent_name
                ORDER BY played DESC, wins DESC, opponent_name ASC
            """, (selected,))

            body += f"<div class='card'><h2>{html.escape(selected)}</h2></div>"

            if summary:
                body += "<div class='card'><h3>Resumen H2H</h3><table><tr><th>Rival</th><th>Jugadas</th><th>Ganadas</th><th>Perdidas</th><th>Frames G</th><th>Frames P</th></tr>"
                for r in summary:
                    body += (
                        f"<tr><td>{html.escape(str(r['opponent_name'] or ''))}</td>"
                        f"<td>{r['played']}</td><td class='good'>{r['wins']}</td><td class='bad'>{r['losses']}</td>"
                        f"<td>{r['frames_won']}</td><td>{r['frames_lost']}</td></tr>"
                    )
                body += "</table></div>"

            if matches:
                body += "<div class='card'><h3>Historial detallado</h3><table><tr><th>Rival</th><th>Juego</th><th>Resultado</th><th>Frames</th><th>Fecha</th></tr>"
                for m in matches:
                    result = "Ganó" if m["did_win"] == 1 else "Perdió"
                    cls = "good" if m["did_win"] == 1 else "bad"
                    body += (
                        f"<tr><td>{html.escape(str(m['opponent_name'] or ''))}</td>"
                        f"<td>{html.escape(str(m['game_type_es'] or ''))}</td>"
                        f"<td class='{cls}'>{result}</td>"
                        f"<td>{m['frames_won']}-{m['frames_lost']}</td>"
                        f"<td>{html.escape(str(m['created_ts_utc'] or ''))}</td></tr>"
                    )
                body += "</table></div>"
            elif selected:
                body += "<div class='card'>No hay historial para este jugador todavía.</div>"

        page = render("Billar Lanzarote H2H", body)
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"H2H running on http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
