
from __future__ import annotations
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from control_helpers_v5 import read_json

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="3">
<title>Billar Lanzarote Dashboard v5</title>
<style>
body{font-family:Arial,sans-serif;background:#111;color:#eee;margin:20px}
.banner{padding:16px;border-radius:10px;font-size:28px;font-weight:bold;margin-bottom:20px}
.ok{background:#14532d}.warning{background:#854d0e}.error{background:#7f1d1d}
.card{background:#1f2937;padding:14px;border-radius:10px;margin-bottom:14px}
.small{font-size:12px;color:#bbb}.mono{font-family:Consolas,monospace}
button{padding:10px 14px;border:none;border-radius:8px;background:#2563eb;color:white;cursor:pointer}
a{color:#93c5fd}
</style>
</head>
<body>
{body}
</body>
</html>
"""

def render(root: Path):
    mch = read_json(root / "state" / "master_control_health_v5.json") or {}
    h = read_json(root / "state" / "health_state.json") or {}
    m1 = read_json(root / "state" / "mesa1_cuescore_state.json") or {}
    m2 = read_json(root / "state" / "mesa2_cuescore_state.json") or {}
    a1 = read_json(root / "state" / "mesa1_ai_state.json") or {}
    a2 = read_json(root / "state" / "mesa2_ai_state.json") or {}

    status = (((mch.get("system") or {}).get("status")) or "warning")
    banner_cls = "ok" if status=="ok" else ("warning" if status=="warning" else "error")
    alerts = mch.get("alerts") or []
    alerts_html = "".join([f"<li>{x.get('code')}: {x.get('message')}</li>" for x in alerts]) or "<li>No alerts</li>"

    def mesa_block(name, cues, ai):
        players = cues.get("players") or {}
        pa = ((players.get("player_a") or {}).get("display_name")) or "-"
        pb = ((players.get("player_b") or {}).get("display_name")) or "-"
        score_a = ((players.get("player_a") or {}).get("score"))
        score_b = ((players.get("player_b") or {}).get("score"))
        active = ((ai.get("active_player") or {}).get("label")) or "unknown"
        shot_state = ((ai.get("table_state") or {}).get("shot_state")) or "unknown"
        return f"""
        <div class='card'>
            <h2>{name.upper()}</h2>
            <div>Players: <span class='mono'>{pa}</span> vs <span class='mono'>{pb}</span></div>
            <div>Score: <span class='mono'>{score_a}</span> - <span class='mono'>{score_b}</span></div>
            <div>Active Player: <span class='mono'>{active}</span></div>
            <div>Shot State: <span class='mono'>{shot_state}</span></div>
        </div>
        """

    body = f"""
    <div class='banner {banner_cls}'>SYSTEM {status.upper()}</div>
    <div class='card'>
        <h2>Alerts</h2>
        <ul>{alerts_html}</ul>
        <div><a href='/restart_obs'>Restart OBS</a></div>
    </div>
    {mesa_block('mesa1', m1, a1)}
    {mesa_block('mesa2', m2, a2)}
    <div class='card small'>Auto-refresh every 3 seconds</div>
    """
    return HTML.format(body=body)

class Handler(BaseHTTPRequestHandler):
    ROOT = None

    def do_GET(self):
        if self.path == "/restart_obs":
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            # signal file for external handler
            sig = self.ROOT / "services" / "control" / "RESTART_OBS_v5.flag"
            sig.parent.mkdir(parents=True, exist_ok=True)
            sig.write_text("restart_obs", encoding="utf-8")
            return
        html = render(self.ROOT).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

def main():
    if len(sys.argv) < 3:
        print("Usage: python dashboard_server_v5.py <root> <port>")
        sys.exit(1)
    root = Path(sys.argv[1])
    port = int(sys.argv[2])
    Handler.ROOT = root
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"Dashboard running at http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
