import os
import sqlite3
import html
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
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
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
.mono {{ font-family: Consolas, monospace; }}
</style>
</head>
<body>{body}</body>
</html>"""

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
            profiles = fetch_all("""
                SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost,
                       ROUND(win_pct, 2) AS win_pct, updated_ts_utc
                FROM player_profiles
                ORDER BY matches_played DESC, matches_won DESC, player_name ASC
            """)

            matches = fetch_all("""
                SELECT id, table_name, player_a, score, player_b, winner, captured_ts_utc,
                       avg_frametime_a, avg_frametime_b, runouts_a, runouts_b,
                       break_and_wins_a, break_and_wins_b, frames_stolen_a, frames_stolen_b,
                       timeouts_a, timeouts_b
                FROM matches_final
                ORDER BY id DESC
                LIMIT 100
            """)

            body = "<h1>Billar Lanzarote Stats</h1>"
            body += "<div class='small'>Local DB: C:\\AI\\BillarLanzarote\\data\\billar_lanzarote.sqlite3</div>"

            body += "<div class='card'><h2>Recent Matches</h2><table><tr><th>ID</th><th>Table</th><th>Player A</th><th>Score</th><th>Player B</th><th>Winner</th><th>Extra Stats</th><th>Captured</th></tr>"
            for r in matches:
                extras = (
                    f"A avg {html.escape(str(r['avg_frametime_a'] or ''))} / "
                    f"B avg {html.escape(str(r['avg_frametime_b'] or ''))}<br>"
                    f"Runouts {r['runouts_a']}-{r['runouts_b']} | "
                    f"B&W {r['break_and_wins_a']}-{r['break_and_wins_b']} | "
                    f"Stolen {r['frames_stolen_a']}-{r['frames_stolen_b']} | "
                    f"TO {r['timeouts_a']}-{r['timeouts_b']}"
                )
                body += (
                    f"<tr>"
                    f"<td>{r['id']}</td>"
                    f"<td>{html.escape(str(r['table_name'] or ''))}</td>"
                    f"<td>{html.escape(str(r['player_a'] or ''))}</td>"
                    f"<td class='mono'>{html.escape(str(r['score'] or ''))}</td>"
                    f"<td>{html.escape(str(r['player_b'] or ''))}</td>"
                    f"<td>{html.escape(str(r['winner'] or ''))}</td>"
                    f"<td class='small'>{extras}</td>"
                    f"<td class='small'>{html.escape(str(r['captured_ts_utc'] or ''))}</td>"
                    f"</tr>"
                )
            body += "</table></div>"

            body += "<div class='card'><h2>Player Profiles</h2><table><tr><th>Player</th><th>Played</th><th>Won</th><th>Lost</th><th>Frames Won</th><th>Frames Lost</th><th>Win %</th><th>Updated</th></tr>"
            for r in profiles:
                name = r["player_name"] or ""
                body += (
                    f"<tr>"
                    f"<td><a href='/player?name={quote(name)}'>{html.escape(name)}</a></td>"
                    f"<td>{r['matches_played']}</td>"
                    f"<td class='good'>{r['matches_won']}</td>"
                    f"<td class='bad'>{r['matches_lost']}</td>"
                    f"<td>{r['frames_won']}</td>"
                    f"<td>{r['frames_lost']}</td>"
                    f"<td>{r['win_pct']}</td>"
                    f"<td class='small'>{html.escape(str(r['updated_ts_utc'] or ''))}</td>"
                    f"</tr>"
                )
            body += "</table></div>"
            self._send(render_page("Billar Lanzarote Stats", body))
            return

        if parsed.path == "/player":
            name = parse_qs(parsed.query).get("name", [""])[0]
            prof = fetch_all("""
                SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost,
                       ROUND(win_pct, 2) AS win_pct, updated_ts_utc
                FROM player_profiles
                WHERE player_name = ?
                LIMIT 1
            """, (name,))

            rows = fetch_all("""
                SELECT id, opponent_name, table_key, did_win, frames_won, frames_lost, winner,
                       avg_frametime, runouts, break_and_wins, frames_stolen, timeouts, created_ts_utc
                FROM player_match_history
                WHERE player_name = ?
                ORDER BY id DESC
                LIMIT 200
            """, (name,))

            body = f"<h1>{html.escape(name)}</h1><p><a href='/'>← Back</a></p>"
            if prof:
                p = prof[0]
                body += (
                    "<div class='card'>"
                    f"<b>Played:</b> {p['matches_played']} &nbsp; "
                    f"<b>Won:</b> <span class='good'>{p['matches_won']}</span> &nbsp; "
                    f"<b>Lost:</b> <span class='bad'>{p['matches_lost']}</span> &nbsp; "
                    f"<b>Frames Won:</b> {p['frames_won']} &nbsp; "
                    f"<b>Frames Lost:</b> {p['frames_lost']} &nbsp; "
                    f"<b>Win %:</b> {p['win_pct']} &nbsp; "
                    f"<div class='small'>Updated: {html.escape(str(p['updated_ts_utc'] or ''))}</div>"
                    "</div>"
                )

            body += "<div class='card'><h2>Match History</h2><table><tr><th>ID</th><th>Opponent</th><th>Table</th><th>Result</th><th>Frames</th><th>Avg Frame</th><th>Runouts</th><th>B&W</th><th>Stolen</th><th>Timeouts</th><th>Created</th></tr>"
            for r in rows:
                result = "Win" if r["did_win"] == 1 else "Loss"
                cls = "good" if r["did_win"] == 1 else "bad"
                body += (
                    f"<tr>"
                    f"<td>{r['id']}</td>"
                    f"<td>{html.escape(str(r['opponent_name'] or ''))}</td>"
                    f"<td>{html.escape(str(r['table_key'] or ''))}</td>"
                    f"<td class='{cls}'>{result}</td>"
                    f"<td class='mono'>{r['frames_won']}-{r['frames_lost']}</td>"
                    f"<td>{html.escape(str(r['avg_frametime'] or ''))}</td>"
                    f"<td>{html.escape(str(r['runouts'] or ''))}</td>"
                    f"<td>{html.escape(str(r['break_and_wins'] or ''))}</td>"
                    f"<td>{html.escape(str(r['frames_stolen'] or ''))}</td>"
                    f"<td>{html.escape(str(r['timeouts'] or ''))}</td>"
                    f"<td class='small'>{html.escape(str(r['created_ts_utc'] or ''))}</td>"
                    f"</tr>"
                )
            body += "</table></div>"
            self._send(render_page(f"Player - {name}", body))
            return

        self._send(render_page("Not Found", "<div class='card'><h1>404</h1></div>"), 404)

if __name__ == "__main__":
    print(f"Stats browser running on http://127.0.0.1:{PORT}")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()
