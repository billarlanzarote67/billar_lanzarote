import sqlite3
from flask import Flask, render_template_string

DB = r"C:\AI\BillarLanzarote\data\billar_lanzarote.sqlite3"

app = Flask(__name__)

HTML = """
<html>
<head>
<title>Billar Lanzarote Stats</title>
<style>
body { font-family: Arial; background: #111; color: #eee; }
table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
th, td { border: 1px solid #444; padding: 8px; text-align: center; }
th { background: #222; }
h2 { color: #00ffcc; }
</style>
</head>
<body>

<h1>🎱 Billar Lanzarote Stats</h1>

<h2>Recent Matches</h2>
<table>
<tr>
<th>Table</th><th>Player A</th><th>Score</th><th>Player B</th><th>Winner</th><th>Time</th>
</tr>
{% for m in matches %}
<tr>
<td>{{m[2]}}</td>
<td>{{m[3]}}</td>
<td>{{m[6]}}-{{m[7]}}</td>
<td>{{m[4]}}</td>
<td>{{m[9]}}</td>
<td>{{m[14]}}</td>
</tr>
{% endfor %}
</table>

<h2>Player Profiles</h2>
<table>
<tr>
<th>Name</th><th>Played</th><th>Won</th><th>Lost</th><th>Frames W</th><th>Frames L</th><th>Win %</th>
</tr>
{% for p in players %}
<tr>
<td>{{p[0]}}</td>
<td>{{p[1]}}</td>
<td>{{p[2]}}</td>
<td>{{p[3]}}</td>
<td>{{p[4]}}</td>
<td>{{p[5]}}</td>
<td>{{p[6]}}</td>
</tr>
{% endfor %}
</table>

</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    matches = cur.execute("""
        SELECT * FROM matches_final
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    players = cur.execute("""
        SELECT * FROM player_profiles
        ORDER BY matches_won DESC
    """).fetchall()

    conn.close()

    return render_template_string(HTML, matches=matches, players=players)


if __name__ == "__main__":
    print("Starting stats browser...")
    print("Open: http://127.0.0.1:5098")
    app.run(port=5098)
