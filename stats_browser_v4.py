import os, sqlite3, html, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PORT = 5098

def fetch_all(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def render_page(title, body):
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; background:#111; color:#eee; margin:20px; }}
a {{ color:#8ecbff; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:14px; padding:16px; margin-bottom:18px; }}
table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
th, td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
.small {{ color:#aaa; font-size:12px; }}
.good {{ color:#7ee787; }}
.bad {{ color:#ff7b72; }}
.warn {{ color:#ffd166; font-weight:bold; }}
.mono {{ font-family: Consolas, monospace; }}
</style></head><body>{body}</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            matches = fetch_all("""
                SELECT id, table_display_name_es, game_type_es, player_a, score, player_b, winner, captured_ts_utc,
                       stats_status, avg_frametime_a, avg_frametime_b, runouts_a, runouts_b,
                       break_and_wins_a, break_and_wins_b, frames_stolen_a, frames_stolen_b,
                       timeouts_a, timeouts_b
                FROM matches_final ORDER BY id DESC LIMIT 100
            """)
            profiles = fetch_all("""
                SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost,
                       ROUND(win_pct, 2) AS win_pct, updated_ts_utc
                FROM player_profiles ORDER BY matches_played DESC, matches_won DESC, player_name ASC
            """)
            body = "<h1>Billar Lanzarote Stats</h1>"
            body += "<div class='small'>DB local: C:\\AI\\BillarLanzarote\\data\\billar_lanzarote.sqlite3</div>"
            body += "<div class='card'><h2>Partidas recientes</h2><table><tr><th>ID</th><th>Mesa</th><th>Juego</th><th>Jugador A</th><th>Marcador</th><th>Jugador B</th><th>Ganador</th><th>Estado stats</th><th>Stats extra</th><th>Guardado</th></tr>"
            for r in matches:
                stats_status = r["stats_status"] or "pending"
                stats_html = "<span class='warn'>Stats pending</span>" if stats_status != "captured" else (
                    f"Tiempo medio {html.escape(str(r['avg_frametime_a'] or ''))} / {html.escape(str(r['avg_frametime_b'] or ''))}<br>"
                    f"Runouts {r['runouts_a']}-{r['runouts_b']} | "
                    f"B&W {r['break_and_wins_a']}-{r['break_and_wins_b']} | "
                    f"Robadas {r['frames_stolen_a']}-{r['frames_stolen_b']} | "
                    f"Tiempos {r['timeouts_a']}-{r['timeouts_b']}"
                )
                body += (
                    f"<tr><td>{r['id']}</td><td>{html.escape(str(r['table_display_name_es'] or ''))}</td>"
                    f"<td>{html.escape(str(r['game_type_es'] or ''))}</td><td>{html.escape(str(r['player_a'] or ''))}</td>"
                    f"<td class='mono'>{html.escape(str(r['score'] or ''))}</td><td>{html.escape(str(r['player_b'] or ''))}</td>"
                    f"<td>{html.escape(str(r['winner'] or ''))}</td><td>{html.escape(str(stats_status))}</td>"
                    f"<td class='small'>{stats_html}</td><td class='small'>{html.escape(str(r['captured_ts_utc'] or ''))}</td></tr>"
                )
            body += "</table></div>"

            body += "<div class='card'><h2>Perfiles de jugadores</h2><table><tr><th>Jugador</th><th>Jugadas</th><th>Ganadas</th><th>Perdidas</th><th>Frames G</th><th>Frames P</th><th>Win %</th><th>Actualizado</th></tr>"
            for r in profiles:
                name = r["player_name"] or ""
                body += (
                    f"<tr><td><a href='/player?name={quote(name)}'>{html.escape(name)}</a></td>"
                    f"<td>{r['matches_played']}</td><td class='good'>{r['matches_won']}</td><td class='bad'>{r['matches_lost']}</td>"
                    f"<td>{r['frames_won']}</td><td>{r['frames_lost']}</td><td>{r['win_pct']}</td>"
                    f"<td class='small'>{html.escape(str(r['updated_ts_utc'] or ''))}</td></tr>"
                )
            body += "</table></div>"
            self._send(render_page("Billar Lanzarote Stats", body))
            return

        if parsed.path == "/player":
            name = parse_qs(parsed.query).get("name", [""])[0]
            prof = fetch_all("""
                SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost,
                       ROUND(win_pct, 2) AS win_pct, updated_ts_utc
                FROM player_profiles WHERE player_name = ? LIMIT 1
            """, (name,))
            rows = fetch_all("""
                SELECT id, opponent_name, table_key, game_type_es, did_win, frames_won, frames_lost,
                       winner, avg_frametime, runouts, break_and_wins, frames_stolen, timeouts, stats_status, created_ts_utc
                FROM player_match_history WHERE player_name = ? ORDER BY id DESC LIMIT 200
            """, (name,))
            body = f"<h1>{html.escape(name)}</h1><p><a href='/'>← Volver</a></p>"
            if prof:
                p = prof[0]
                body += (
                    "<div class='card'>"
                    f"<b>Jugadas:</b> {p['matches_played']} &nbsp; <b>Ganadas:</b> <span class='good'>{p['matches_won']}</span> &nbsp; "
                    f"<b>Perdidas:</b> <span class='bad'>{p['matches_lost']}</span> &nbsp; <b>Frames G:</b> {p['frames_won']} &nbsp; "
                    f"<b>Frames P:</b> {p['frames_lost']} &nbsp; <b>Win %:</b> {p['win_pct']} &nbsp; "
                    f"<div class='small'>Actualizado: {html.escape(str(p['updated_ts_utc'] or ''))}</div></div>"
                )
            body += "<div class='card'><h2>Historial</h2><table><tr><th>ID</th><th>Rival</th><th>Mesa</th><th>Juego</th><th>Resultado</th><th>Frames</th><th>Estado stats</th><th>Tiempo medio</th><th>Runouts</th><th>B&W</th><th>Robadas</th><th>Tiempos</th><th>Creado</th></tr>"
            for r in rows:
                result = "Ganó" if r["did_win"] == 1 else "Perdió"
                cls = "good" if r["did_win"] == 1 else "bad"
                stats_status = r["stats_status"] or "pending"
                body += (
                    f"<tr><td>{r['id']}</td><td>{html.escape(str(r['opponent_name'] or ''))}</td><td>{html.escape(str(r['table_key'] or ''))}</td>"
                    f"<td>{html.escape(str(r['game_type_es'] or ''))}</td><td class='{cls}'>{result}</td>"
                    f"<td class='mono'>{r['frames_won']}-{r['frames_lost']}</td><td>{html.escape(str(stats_status))}</td>"
                    f"<td>{html.escape(str(r['avg_frametime'] or ''))}</td><td>{html.escape(str(r['runouts'] or ''))}</td>"
                    f"<td>{html.escape(str(r['break_and_wins'] or ''))}</td><td>{html.escape(str(r['frames_stolen'] or ''))}</td>"
                    f"<td>{html.escape(str(r['timeouts'] or ''))}</td><td class='small'>{html.escape(str(r['created_ts_utc'] or ''))}</td></tr>"
                )
            body += "</table></div>"
            self._send(render_page(f"Player - {name}", body))
            return

        self._send(render_page("Not Found", "<div class='card'><h1>404</h1></div>"), 404)

if __name__ == "__main__":
    print(f"Stats browser running on http://127.0.0.1:{PORT}")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
