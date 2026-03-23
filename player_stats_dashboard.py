import json
import os
import sqlite3
from flask import Flask, jsonify, render_template_string

CFG_PATH = r"C:\AI\BillarLanzarote\config\player_stats_dashboard_config.json"

with open(CFG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

DB = CFG["db_path"]
PORT = int(CFG.get("dashboard_port", 8098))

app = Flask(__name__)

PAGE_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Billar Lanzarote Stats</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #111;
      color: #eee;
      padding: 20px;
      margin: 0;
    }
    h1 {
      margin: 0 0 6px 0;
      font-size: 30px;
      font-weight: 800;
    }
    .muted {
      color: #bbb;
      font-size: 13px;
    }
    .panel {
      background: #1c1c1c;
      border-radius: 14px;
      padding: 16px;
      margin-top: 18px;
      box-shadow: 0 0 0 1px rgba(255,255,255,0.05) inset;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 14px;
    }
    th, td {
      border: 1px solid #333;
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #222;
    }
    a {
      color: #8fd3ff;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
    .ok { color: #8df58d; font-weight: 700; }
    .warn { color: #ffd166; font-weight: 700; }
  </style>
</head>
<body>
  <h1>Billar Lanzarote Stats</h1>
  <div class="muted">DB local: {{ db_path }}</div>

  <div class="panel">
    <h2>Partidas recientes</h2>
    <table id="matchesTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Mesa</th>
          <th>Juego</th>
          <th>Jugador A</th>
          <th>Marcador</th>
          <th>Jugador B</th>
          <th>Ganador</th>
          <th>Estado stats</th>
          <th>Stats extra</th>
          <th>Guardado</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="panel">
    <h2>Perfiles de jugadores</h2>
    <table id="playersTable">
      <thead>
        <tr>
          <th>Jugador</th>
          <th>Jugadas</th>
          <th>Ganadas</th>
          <th>Perdidas</th>
          <th>Frames G</th>
          <th>Frames P</th>
          <th>Win %</th>
          <th>Actualizado</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <script>
    function v(x) {
      if (x === null || x === undefined || x === "" || x === "None") return "—";
      return x;
    }

    function pct(x) {
      if (x === null || x === undefined || x === "" || x === "None") return "—";
      const n = Number(x);
      if (Number.isNaN(n)) return x;
      return n.toFixed(1);
    }

    async function boot() {
      const matchesRes = await fetch("/api/recent_matches");
      const matches = await matchesRes.json();

      const playersRes = await fetch("/api/players");
      const players = await playersRes.json();

      const mtb = document.querySelector("#matchesTable tbody");
      const ptb = document.querySelector("#playersTable tbody");

      mtb.innerHTML = "";
      ptb.innerHTML = "";

      for (const m of matches) {
        const tr = document.createElement("tr");
        const statsState = m.stats_state || "pending";
        const statsClass = statsState === "ready" ? "ok" : "warn";
        tr.innerHTML = `
          <td>${v(m.id)}</td>
          <td>${v(m.table_key)}</td>
          <td>${v(m.game_type_es)}</td>
          <td>${v(m.player_a)}</td>
          <td>${v(m.score)}</td>
          <td>${v(m.player_b)}</td>
          <td>${v(m.winner)}</td>
          <td class="${statsClass}">${v(statsState)}</td>
          <td>${v(m.stats_summary)}</td>
          <td>${v(m.created_ts_utc)}</td>
        `;
        mtb.appendChild(tr);
      }

      for (const p of players) {
        const tr = document.createElement("tr");
        const href = `/api/player/${encodeURIComponent(p.player_id)}`;
        tr.innerHTML = `
          <td><a href="${href}" target="_blank">${v(p.display_name)}</a></td>
          <td>${v(p.matches_played)}</td>
          <td>${v(p.wins)}</td>
          <td>${v(p.losses)}</td>
          <td>${v(p.frames_won)}</td>
          <td>${v(p.frames_lost)}</td>
          <td>${pct(p.win_rate)}</td>
          <td>${v(p.last_import_ts_utc)}</td>
        `;
        ptb.appendChild(tr);
      }
    }

    boot();
  </script>
</body>
</html>
"""

def get_conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def q(sql, params=()):
    con = get_conn()
    cur = con.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

def table_exists(name: str) -> bool:
    rows = q("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return len(rows) > 0

@app.route("/")
def index():
    return render_template_string(PAGE_HTML, db_path=DB)

@app.route("/api/players")
def api_players():
    if not table_exists("players"):
        return jsonify([])

    rows = q("""
        SELECT
            p.player_id,
            p.display_name,
            s.matches_played,
            s.wins,
            s.losses,
            s.win_rate,
            s.frames_won,
            s.frames_lost,
            s.frames_total,
            s.last_import_ts_utc
        FROM players p
        LEFT JOIN player_profile_stats s
            ON s.player_id = p.player_id
        ORDER BY COALESCE(s.matches_played, 0) DESC, p.display_name ASC
    """)
    return jsonify(rows)

@app.route("/api/player/<player_id>")
def api_player(player_id):
    player = q("""
        SELECT
            p.player_id,
            p.display_name,
            s.matches_played,
            s.wins,
            s.losses,
            s.win_rate,
            s.frames_won,
            s.frames_lost,
            s.frames_total,
            s.last_import_ts_utc,
            m.cuescore_player_id,
            m.cuescore_profile_url,
            media.photo_url,
            media.local_photo_path
        FROM players p
        LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
        LEFT JOIN player_cuescore_map m ON m.player_id = p.player_id
        LEFT JOIN player_media media ON media.player_id = p.player_id
        WHERE p.player_id = ?
    """, (player_id,))
    return jsonify(player[0] if player else {})

@app.route("/api/recent_matches")
def api_recent_matches():
    if not table_exists("completed_matches"):
        return jsonify([])

    rows = q("""
        SELECT
            id,
            table_key,
            game_type_es,
            player_a,
            player_b,
            score,
            winner,
            stats_state,
            stats_summary,
            created_ts_utc
        FROM completed_matches
        ORDER BY id DESC
        LIMIT 50
    """)
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
