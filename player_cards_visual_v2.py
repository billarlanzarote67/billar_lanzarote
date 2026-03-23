
import os, sqlite3, html, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
PHOTOS_DIRS = [
    os.path.join(ROOT, "data", "player_photos"),
    os.path.join(ROOT, "data", "photos"),
]
META_JSON = os.path.join(ROOT, "config", "player_metadata_v1.json")
PORT_GALLERY = 8099
PORT_H2H = 8097
PORT_PROFILE = 8101

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def table_exists(c, table):
    return bool(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,)).fetchone())

def load_meta():
    if os.path.exists(META_JSON):
        try:
            with open(META_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

META = load_meta()

def slugify(name):
    out = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out

def photo_path(name):
    stem = slugify(name)
    for folder in PHOTOS_DIRS:
        if not os.path.isdir(folder):
            continue
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            p = os.path.join(folder, stem + ext)
            if os.path.exists(p):
                return p
    return None

def photo_html(name):
    p = photo_path(name)
    if p:
        uri = p.replace("\\", "/")
        return f"<img class='photo' src='file:///{html.escape(uri)}'>"
    return "<div class='photo placeholder'>🎱</div>"

def flag_html(name):
    meta = META.get(name, {})
    emoji = meta.get("flag_emoji", "").strip()
    code = meta.get("flag_code", "").strip().upper()
    if emoji:
        return f"<span class='flag'>{html.escape(emoji)}</span>"
    if len(code) == 2 and code.isalpha():
        regional = "".join(chr(127397 + ord(ch)) for ch in code)
        return f"<span class='flag'>{regional}</span>"
    return ""

def players():
    c = db()
    rows = []
    if table_exists(c, "player_profiles"):
        rows = [dict(r) for r in c.execute("""
            SELECT player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost, win_pct
            FROM player_profiles
            ORDER BY matches_played DESC, matches_won DESC, player_name ASC
        """).fetchall()]
    c.close()
    return rows

def profile_rows(player):
    c = db()
    out = []
    if table_exists(c, "player_match_history"):
        out.extend([dict(r) for r in c.execute("""
            SELECT id, opponent_name, table_key, game_type_es, did_win, frames_won, frames_lost,
                   stats_status, avg_frametime, runouts, break_and_wins, frames_stolen, timeouts, created_ts_utc
            FROM player_match_history
            WHERE player_name = ?
            ORDER BY id DESC
        """, (player,)).fetchall()])
    if table_exists(c, "imported_match_cache"):
        start = 100000
        imported = c.execute("""
            SELECT id, source_table, player_a, player_b, winner, score, game_type_es, notes, imported_ts_utc
            FROM imported_match_cache
            WHERE player_a = ? OR player_b = ?
            ORDER BY id DESC
        """, (player, player)).fetchall()
        for i, r in enumerate(imported, start=1):
            a = r["player_a"]; b = r["player_b"]
            opp = b if a == player else a
            fw = fl = None
            score = r["score"] or ""
            if "-" in score:
                try:
                    sa, sb = [int(x.strip()) for x in score.split("-", 1)]
                    if a == player:
                        fw, fl = sa, sb
                    else:
                        fw, fl = sb, sa
                except Exception:
                    pass
            out.append({
                "id": start + i,
                "opponent_name": opp,
                "table_key": "importado",
                "game_type_es": r["game_type_es"] or "Sin juego",
                "did_win": 1 if (r["winner"] or "") == player else 0 if (r["winner"] or "") == opp else None,
                "frames_won": fw,
                "frames_lost": fl,
                "stats_status": "importado",
                "avg_frametime": None,
                "runouts": None,
                "break_and_wins": None,
                "frames_stolen": None,
                "timeouts": None,
                "created_ts_utc": r["imported_ts_utc"],
            })
    c.close()
    out.sort(key=lambda x: x["id"], reverse=True)
    return out

def h2h_rows(player):
    c = db()
    rows = {}
    if table_exists(c, "player_match_history"):
        for r in c.execute("""
            SELECT opponent_name, did_win, frames_won, frames_lost
            FROM player_match_history
            WHERE player_name = ?
        """, (player,)).fetchall():
            opp = r["opponent_name"] or "—"
            rows.setdefault(opp, {"played":0,"wins":0,"losses":0,"frames_won":0,"frames_lost":0})
            rows[opp]["played"] += 1
            rows[opp]["wins"] += 1 if int(r["did_win"] or 0) == 1 else 0
            rows[opp]["losses"] += 0 if int(r["did_win"] or 0) == 1 else 1
            rows[opp]["frames_won"] += int(r["frames_won"] or 0)
            rows[opp]["frames_lost"] += int(r["frames_lost"] or 0)
    if table_exists(c, "imported_match_cache"):
        for r in c.execute("""
            SELECT player_a, player_b, winner, score
            FROM imported_match_cache
            WHERE player_a = ? OR player_b = ?
        """, (player, player)).fetchall():
            opp = r["player_b"] if r["player_a"] == player else r["player_a"]
            rows.setdefault(opp, {"played":0,"wins":0,"losses":0,"frames_won":0,"frames_lost":0})
            rows[opp]["played"] += 1
            if (r["winner"] or "") == player:
                rows[opp]["wins"] += 1
            elif (r["winner"] or "") == opp:
                rows[opp]["losses"] += 1
            score = r["score"] or ""
            if "-" in score:
                try:
                    sa, sb = [int(x.strip()) for x in score.split("-", 1)]
                    if r["player_a"] == player:
                        rows[opp]["frames_won"] += sa; rows[opp]["frames_lost"] += sb
                    else:
                        rows[opp]["frames_won"] += sb; rows[opp]["frames_lost"] += sa
                except Exception:
                    pass
    c.close()
    out = [{"opponent_name": k, **v} for k, v in rows.items()]
    out.sort(key=lambda x: (-x["played"], -x["wins"], x["opponent_name"].lower()))
    return out

def render(title, body):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body {{ font-family: Arial, sans-serif; background:#111; color:#eee; margin:20px; }}
.header {{ background: linear-gradient(90deg,#2b2b2b,#ff5a36); padding:18px; border-radius:18px; margin-bottom:20px; font-weight:bold; font-size:24px; }}
.small {{ color:#d6b08f; font-size:14px; margin-bottom:18px; }}
.grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(360px,1fr)); gap:16px; }}
.card {{ background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:18px; box-shadow: 0 6px 20px rgba(0,0,0,.22); }}
.name {{ font-size:24px; font-weight:bold; margin-bottom:8px; line-height:1.2; }}
.meta {{ color:#ddd; line-height:1.8; }}
a {{ color:#8ecbff; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.tag {{ display:inline-block; background:#2a2a2a; border-radius:999px; padding:4px 10px; margin-right:6px; margin-top:8px; font-size:12px; color:#ffd6c7; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th, td {{ border:1px solid #333; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#222; }}
.good {{ color:#7ee787; }}
.bad {{ color:#ff7b72; }}
.warn {{ color:#ffd166; }}
.photo {{ width:112px; height:112px; border-radius:16px; object-fit:cover; border:1px solid #333; background:#222; display:flex; align-items:center; justify-content:center; font-size:40px; }}
.profile-wrap {{ display:grid; grid-template-columns: 126px 1fr; gap:18px; align-items:start; }}
.flag {{ font-size:24px; margin-left:8px; vertical-align:middle; }}
.stats-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(130px,1fr)); gap:10px; margin-top:14px; }}
.stat {{ background:#171717; border:1px solid #2c2c2c; padding:10px; border-radius:12px; }}
.stat-label {{ color:#aaa; font-size:12px; margin-bottom:4px; }}
.stat-value {{ font-size:20px; font-weight:bold; }}
</style></head><body>{body}</body></html>"""

def serve(handler, page):
    data = page.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

class Gallery(BaseHTTPRequestHandler):
    def do_GET(self):
        ps = players()
        body = "<div class='header'>Billar Lanzarote Player Gallery</div><div class='small'>Tarjetas visuales con foto, bandera y datos combinados local + importado</div>"
        if not ps:
            body += "<div class='card'>No hay jugadores todavía.</div>"
        else:
            body += "<div class='grid'>"
            for p in ps:
                n = p["player_name"]
                body += (
                    "<div class='card'><div class='profile-wrap'>"
                    f"{photo_html(n)}"
                    "<div>"
                    f"<div class='name'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(n)}'>{html.escape(n)}</a>{flag_html(n)}</div>"
                    "<div class='stats-grid'>"
                    f"<div class='stat'><div class='stat-label'>Jugadas</div><div class='stat-value'>{p['matches_played']}</div></div>"
                    f"<div class='stat'><div class='stat-label'>Ganadas</div><div class='stat-value'>{p['matches_won']}</div></div>"
                    f"<div class='stat'><div class='stat-label'>Perdidas</div><div class='stat-value'>{p['matches_lost']}</div></div>"
                    f"<div class='stat'><div class='stat-label'>Frames G</div><div class='stat-value'>{p['frames_won']}</div></div>"
                    f"<div class='stat'><div class='stat-label'>Frames P</div><div class='stat-value'>{p['frames_lost']}</div></div>"
                    f"<div class='stat'><div class='stat-label'>Win %</div><div class='stat-value'>{round(float(p['win_pct'] or 0),2)}</div></div>"
                    "</div>"
                    "<div><span class='tag'>Perfil</span><span class='tag'>Jugador</span></div>"
                    "</div></div></div>"
                )
            body += "</div>"
        serve(self, render("Billar Lanzarote Player Gallery", body))

class Profile(BaseHTTPRequestHandler):
    def do_GET(self):
        player = parse_qs(urlparse(self.path).query).get("player", [""])[0]
        pmap = {p["player_name"]: p for p in players()}
        body = "<div class='header'>Perfil de jugador</div><div class='small'><a href='http://127.0.0.1:8099'>← Volver a Gallery</a> · <a href='http://127.0.0.1:8097'>Abrir H2H</a></div>"
        if not player:
            body += "<div class='card'>No se ha seleccionado jugador.</div>"
            serve(self, render("Perfil de jugador", body)); return
        p = pmap.get(player, {"matches_played":0,"matches_won":0,"matches_lost":0,"frames_won":0,"frames_lost":0,"win_pct":0})
        body += (
            "<div class='card'><div class='profile-wrap'>"
            f"{photo_html(player)}"
            "<div>"
            f"<div class='name'>{html.escape(player)}{flag_html(player)}</div>"
            "<div class='stats-grid'>"
            f"<div class='stat'><div class='stat-label'>Jugadas</div><div class='stat-value'>{p['matches_played']}</div></div>"
            f"<div class='stat'><div class='stat-label'>Ganadas</div><div class='stat-value good'>{p['matches_won']}</div></div>"
            f"<div class='stat'><div class='stat-label'>Perdidas</div><div class='stat-value bad'>{p['matches_lost']}</div></div>"
            f"<div class='stat'><div class='stat-label'>Frames G</div><div class='stat-value'>{p['frames_won']}</div></div>"
            f"<div class='stat'><div class='stat-label'>Frames P</div><div class='stat-value'>{p['frames_lost']}</div></div>"
            f"<div class='stat'><div class='stat-label'>Win %</div><div class='stat-value'>{round(float(p['win_pct'] or 0),2)}</div></div>"
            "</div>"
            "<div><span class='tag'>Perfil local+importado</span></div>"
            "</div></div></div>"
        )
        rows = profile_rows(player)
        if rows:
            body += "<div class='card'><h2>Partidas en Mesa 1 y Mesa 2</h2><table><tr><th>ID</th><th>Rival</th><th>Mesa</th><th>Juego</th><th>Resultado</th><th>Frames</th><th>Estado</th><th>Tiempo medio</th><th>Runouts</th><th>B&W</th><th>Robadas</th><th>Tiempos</th><th>Creado</th></tr>"
            for r in rows:
                did = r["did_win"]
                if did is None:
                    result = "—"; cls = ""
                else:
                    result = "Ganó" if int(did or 0) == 1 else "Perdió"
                    cls = "good" if int(did or 0) == 1 else "bad"
                fw = r["frames_won"] if r["frames_won"] is not None else "?"
                fl = r["frames_lost"] if r["frames_lost"] is not None else "?"
                body += f"<tr><td>{r['id']}</td><td>{html.escape(str(r['opponent_name'] or ''))}</td><td>{html.escape(str(r['table_key'] or ''))}</td><td>{html.escape(str(r['game_type_es'] or 'Sin juego'))}</td><td class='{cls}'>{result}</td><td>{fw}-{fl}</td><td>{html.escape(str(r['stats_status'] or ''))}</td><td>{html.escape(str(r['avg_frametime'] or ''))}</td><td>{html.escape(str(r.get('runouts') or ''))}</td><td>{html.escape(str(r.get('break_and_wins') or ''))}</td><td>{html.escape(str(r.get('frames_stolen') or ''))}</td><td>{html.escape(str(r.get('timeouts') or ''))}</td><td>{html.escape(str(r['created_ts_utc'] or ''))}</td></tr>"
            body += "</table></div>"
        else:
            body += "<div class='card'>Sin partidas todavía para este jugador.</div>"
        serve(self, render(f"Perfil - {player}", body))

class H2H(BaseHTTPRequestHandler):
    def do_GET(self):
        player = parse_qs(urlparse(self.path).query).get("player", [""])[0]
        ps = players()
        body = "<div class='header'>Billar Lanzarote H2H</div><div class='small'>Cara a cara usando perfiles locales + DB antiguo importado</div>"
        body += "<div class='card'><b>Jugadores:</b><br>" + " · ".join([f"<a href='/?player={quote(p['player_name'])}'>{html.escape(p['player_name'])}</a>" for p in ps[:300]]) + "</div>"
        if player:
            rows = h2h_rows(player)
            body += f"<div class='card'><h2>{html.escape(player)}{flag_html(player)}</h2><div class='small'><a href='http://127.0.0.1:{PORT_PROFILE}/?player={quote(player)}'>Abrir perfil</a></div></div>"
            if rows:
                body += "<div class='card'><h3>Resumen H2H</h3><table><tr><th>Rival</th><th>Jugadas</th><th>Ganadas</th><th>Perdidas</th><th>Frames G</th><th>Frames P</th></tr>"
                for r in rows:
                    body += f"<tr><td>{html.escape(str(r['opponent_name']))}</td><td>{r['played']}</td><td class='good'>{r['wins']}</td><td class='bad'>{r['losses']}</td><td>{r['frames_won']}</td><td>{r['frames_lost']}</td></tr>"
                body += "</table></div>"
            else:
                body += "<div class='card'>No hay historial H2H todavía para este jugador.</div>"
        serve(self, render("Billar Lanzarote H2H", body))

def run(port, handler):
    print(f"Running on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), handler).serve_forever()

if __name__ == "__main__":
    import sys
    mode = (sys.argv[1] if len(sys.argv) > 1 else "gallery").lower()
    if mode == "gallery": run(PORT_GALLERY, Gallery)
    elif mode == "h2h": run(PORT_H2H, H2H)
    elif mode == "profile": run(PORT_PROFILE, Profile)
