import os, sqlite3, html
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PORT_GALLERY = 8099
PORT_H2H = 8097
PORT_PROFILE = 8101

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(conn, table_name):
    cur = conn.cursor()
    row = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,)
    ).fetchone()
    return bool(row)

def get_columns(conn, table_name):
    cur = conn.cursor()
    try:
        rows = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [r[1] for r in rows]
    except Exception:
        return []

def discover_all_player_names():
    conn = connect()
    cur = conn.cursor()
    names = set()

    if table_exists(conn, "player_profiles"):
        try:
            for row in cur.execute("SELECT player_name FROM player_profiles WHERE player_name IS NOT NULL AND TRIM(player_name) != ''"):
                names.add(row["player_name"].strip())
        except Exception:
            pass

    if table_exists(conn, "player_match_history"):
        cols = get_columns(conn, "player_match_history")
        if "player_name" in cols:
            try:
                for row in cur.execute("SELECT DISTINCT player_name FROM player_match_history WHERE player_name IS NOT NULL AND TRIM(player_name) != ''"):
                    names.add(row["player_name"].strip())
            except Exception:
                pass
        if "opponent_name" in cols:
            try:
                for row in cur.execute("SELECT DISTINCT opponent_name FROM player_match_history WHERE opponent_name IS NOT NULL AND TRIM(opponent_name) != ''"):
                    names.add(row["opponent_name"].strip())
            except Exception:
                pass

    if table_exists(conn, "matches_final"):
        cols = get_columns(conn, "matches_final")
        if "player_a" in cols:
            try:
                for row in cur.execute("SELECT DISTINCT player_a FROM matches_final WHERE player_a IS NOT NULL AND TRIM(player_a) != ''"):
                    names.add(row["player_a"].strip())
            except Exception:
                pass
        if "player_b" in cols:
            try:
                for row in cur.execute("SELECT DISTINCT player_b FROM matches_final WHERE player_b IS NOT NULL AND TRIM(player_b) != ''"):
                    names.add(row["player_b"].strip())
            except Exception:
                pass

    candidate_tables = [
        "players", "tournament_players", "imported_players", "cuescore_players",
        "player_aliases", "player_summary", "tournament_matches", "imported_matches",
        "matches", "match_results", "raw_tournament_players", "raw_tournament_matches",
    ]

    for table_name in candidate_tables:
        if not table_exists(conn, table_name):
            continue
        cols = get_columns(conn, table_name)
        for candidate_col in ["player_name", "name", "full_name", "display_name", "player_a", "player_b", "opponent_name", "alias"]:
            if candidate_col not in cols:
                continue
            try:
                query = f"SELECT DISTINCT {candidate_col} AS n FROM {table_name} WHERE {candidate_col} IS NOT NULL AND TRIM({candidate_col}) != ''"
                for row in cur.execute(query):
                    val = row["n"]
                    if val:
                        names.add(str(val).strip())
            except Exception:
                pass

    conn.close()
    cleaned = []
    junk = {"breaking","runouts","runout","timeout","timeouts","end match","ball in hand","match statistics","challengematch","mesa 1","mesa 2"}
    for name in sorted(names):
        low = name.lower().strip()
        if low in junk:
            continue
        if len(name.strip()) < 2:
            continue
        cleaned.append(name.strip())
    return cleaned

def build_player_rows():
    all_names = discover_all_player_names()
    conn = connect()
    cur = conn.cursor()
    profiles = {}
    if table_exists(conn, "player_profiles"):
        try:
            for row in cur.execute("""
                SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost, win_pct, updated_ts_utc
                FROM player_profiles
            """):
                profiles[row["player_name"]] = dict(row)
        except Exception:
            pass
    conn.close()

    rows_out = []
    for name in all_names:
        p = profiles.get(name)
        if p:
            rows_out.append({
                "player_name": name,
                "matches_played": p.get("matches_played") or 0,
                "matches_won": p.get("matches_won") or 0,
                "matches_lost": p.get("matches_lost") or 0,
                "frames_won": p.get("frames_won") or 0,
                "frames_lost": p.get("frames_lost") or 0,
                "win_pct": p.get("win_pct") or 0,
                "source_status": "profile+imported",
            })
        else:
            rows_out.append({
                "player_name": name,
                "matches_played": 0,
                "matches_won": 0,
                "matches_lost": 0,
                "frames_won": 0,
                "frames_lost": 0,
                "win_pct": 0,
                "source_status": "imported_only",
            })
    rows_out.sort(key=lambda r: (-r["matches_played"], -r["matches_won"], r["player_name"].lower()))
    return rows_out

def get_player_match_rows(player_name):
    conn = connect()
    cur = conn.cursor()
    rows = []
    if table_exists(conn, "player_match_history"):
        cols = get_columns(conn, "player_match_history")
        select_cols = [c for c in [
            "id","opponent_name","table_key","game_type_es","did_win","frames_won","frames_lost",
            "winner","avg_frametime","runouts","break_and_wins","frames_stolen","timeouts",
            "stats_status","created_ts_utc"
        ] if c in cols]
        if select_cols:
            try:
                sql = f"SELECT {', '.join(select_cols)} FROM player_match_history WHERE player_name = ? ORDER BY id DESC"
                rows = cur.execute(sql, (player_name,)).fetchall()
            except Exception:
                rows = []
    conn.close()
    return rows

def get_h2h_summary(player_name):
    conn = connect()
    cur = conn.cursor()
    summary = []
    if table_exists(conn, "player_match_history"):
        cols = get_columns(conn, "player_match_history")
        needed = {"opponent_name", "did_win", "frames_won", "frames_lost"}
        if needed.issubset(set(cols)):
            try:
                summary = cur.execute("""
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
                """, (player_name,)).fetchall()
            except Exception:
                summary = []
    conn.close()
    return summary

def render_page(title, body):
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
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th, td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
.good {{ color:#7ee787; }}
.bad {{ color:#ff7b72; }}
.warn {{ color:#ffd166; }}
.mono {{ font-family: Consolas, monospace; }}
</style></head><body>{body}</body></html>"""

def serve_html(handler, html_text):
    data = html_text.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

class GalleryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        players = build_player_rows()
        body = "<div class='header'>Billar Lanzarote Player Gallery</div>"
        body += "<div class='small'>Tema volcánico · vista bonita · texto jugadores en español · jugadores importados + perfiles locales</div>"
        if not players:
            body += "<div class='card'>No hay jugadores todavía en la base de datos.</div>"
        else:
            body += "<div class='grid'>"
            for p in players:
                name = p["player_name"]
                status_tag = "Importado" if p["source_status"] == "imported_only" else "Perfil"
                body += (
                    "<div class='card'>"
                    f"<div class='name'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(name)}'>{html.escape(name)}</a></div>"
                    f"<div class='meta'>Jugadas: {p['matches_played']}<br>"
                    f"Ganadas: {p['matches_won']}<br>"
                    f"Perdidas: {p['matches_lost']}<br>"
                    f"Frames G: {p['frames_won']}<br>"
                    f"Frames P: {p['frames_lost']}<br>"
                    f"Win %: {round(float(p['win_pct'] or 0), 2)}</div>"
                    f"<div><span class='tag'>{status_tag}</span><span class='tag'>Jugador</span></div>"
                    "</div>"
                )
            body += "</div>"
        serve_html(self, render_page("Billar Lanzarote Player Gallery", body))

class ProfileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        player = qs.get("player", [""])[0]
        all_players = build_player_rows()
        lookup = {p["player_name"]: p for p in all_players}

        body = "<div class='header'>Perfil de jugador</div>"
        body += "<div class='small'><a href='http://127.0.0.1:8099'>← Volver a Gallery</a> · <a href='http://127.0.0.1:8097'>Abrir H2H</a></div>"

        if not player:
            body += "<div class='card'>No se ha seleccionado jugador.</div>"
            serve_html(self, render_page("Perfil de jugador", body))
            return

        p = lookup.get(player, {
            "player_name": player,
            "matches_played": 0,
            "matches_won": 0,
            "matches_lost": 0,
            "frames_won": 0,
            "frames_lost": 0,
            "win_pct": 0,
            "source_status": "imported_only",
        })

        body += (
            "<div class='card'>"
            f"<div class='name'>{html.escape(player)}</div>"
            f"<div class='meta'>Jugadas: {p['matches_played']} &nbsp; "
            f"Ganadas: <span class='good'>{p['matches_won']}</span> &nbsp; "
            f"Perdidas: <span class='bad'>{p['matches_lost']}</span> &nbsp; "
            f"Frames G: {p['frames_won']} &nbsp; "
            f"Frames P: {p['frames_lost']} &nbsp; "
            f"Win %: {round(float(p['win_pct'] or 0), 2)}</div>"
            f"<div><span class='tag'>{'Importado' if p['source_status']=='imported_only' else 'Perfil local'}</span></div>"
            "</div>"
        )

        rows = get_player_match_rows(player)
        if rows:
            body += "<div class='card'><h2>Partidas en Mesa 1 y Mesa 2</h2><table><tr><th>ID</th><th>Rival</th><th>Mesa</th><th>Juego</th><th>Resultado</th><th>Frames</th><th>Estado stats</th><th>Tiempo medio</th><th>Creado</th></tr>"
            for r in rows:
                result = "Ganó" if ("did_win" in r.keys() and r["did_win"] == 1) else "Perdió"
                cls = "good" if ("did_win" in r.keys() and r["did_win"] == 1) else "bad"
                body += (
                    f"<tr><td>{html.escape(str(r['id'] if 'id' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['opponent_name'] if 'opponent_name' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['table_key'] if 'table_key' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['game_type_es'] if 'game_type_es' in r.keys() else ''))}</td>"
                    f"<td class='{cls}'>{result}</td>"
                    f"<td class='mono'>{html.escape(str(r['frames_won'] if 'frames_won' in r.keys() else ''))}-{html.escape(str(r['frames_lost'] if 'frames_lost' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['stats_status'] if 'stats_status' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['avg_frametime'] if 'avg_frametime' in r.keys() else ''))}</td>"
                    f"<td>{html.escape(str(r['created_ts_utc'] if 'created_ts_utc' in r.keys() else ''))}</td></tr>"
                )
            body += "</table></div>"
        else:
            body += "<div class='card'>Sin partidas locales todavía para este jugador en Mesa 1 / Mesa 2.</div>"

        serve_html(self, render_page(f"Perfil - {player}", body))

class H2HHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        player = qs.get("player", [""])[0]
        players = build_player_rows()

        body = "<div class='header'>Billar Lanzarote H2H</div>"
        body += "<div class='small'>Cara a cara usando perfiles locales + jugadores importados</div>"

        if not players:
            body += "<div class='card'>No hay jugadores todavía.</div>"
            serve_html(self, render_page("H2H", body))
            return

        body += "<div class='card'><b>Jugadores:</b><br>"
        body += " · ".join([f"<a href='/?player={quote(p['player_name'])}'>{html.escape(p['player_name'])}</a>" for p in players[:200]])
        body += "</div>"

        if player:
            summary = get_h2h_summary(player)
            body += f"<div class='card'><h2>{html.escape(player)}</h2><div class='small'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(player)}'>Abrir perfil</a></div></div>"
            if summary:
                body += "<div class='card'><h3>Resumen H2H</h3><table><tr><th>Rival</th><th>Jugadas</th><th>Ganadas</th><th>Perdidas</th><th>Frames G</th><th>Frames P</th></tr>"
                for r in summary:
                    body += (
                        f"<tr><td>{html.escape(str(r['opponent_name'] or ''))}</td>"
                        f"<td>{r['played']}</td><td class='good'>{r['wins']}</td><td class='bad'>{r['losses']}</td>"
                        f"<td>{r['frames_won']}</td><td>{r['frames_lost']}</td></tr>"
                    )
                body += "</table></div>"
            else:
                body += "<div class='card'>No hay historial H2H local todavía para este jugador.</div>"

        serve_html(self, render_page("H2H", body))

def run_server(port, handler):
    print(f"Running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), handler).serve_forever()

if __name__ == "__main__":
    import sys
    mode = (sys.argv[1] if len(sys.argv) > 1 else "gallery").lower()
    if mode == "gallery":
        run_server(PORT_GALLERY, GalleryHandler)
    elif mode == "h2h":
        run_server(PORT_H2H, H2HHandler)
    elif mode == "profile":
        run_server(PORT_PROFILE, ProfileHandler)
    else:
        print("Use: gallery | h2h | profile")
