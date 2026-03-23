
import os, re, sqlite3, shutil
from flask import Flask, send_from_directory, jsonify, request

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
WEB = os.path.join(ROOT, "web_ui", "photo_upload")
PHOTOS = os.path.join(ROOT, "data", "photos")
os.makedirs(PHOTOS, exist_ok=True)

app = Flask(__name__, static_folder=WEB, static_url_path="")

def q(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    return send_from_directory(WEB, "index.html")

@app.route("/api/players")
def api_players():
    return jsonify({"players":[r["name"] for r in q("SELECT name FROM players ORDER BY name")]})

@app.route("/api/set_photo", methods=["POST"])
def set_photo():
    name = request.form.get("name","").strip()
    source_path = request.form.get("source_path","").strip()
    if not name or not source_path or not os.path.exists(source_path):
        return jsonify({"ok":False,"error":"Invalid name or source path"}), 400
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', name)
    ext = os.path.splitext(source_path)[1] or ".jpg"
    dest = os.path.join(PHOTOS, safe + ext)
    shutil.copy2(source_path, dest)
    rel = f"/photos/{safe + ext}"
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("UPDATE players SET photo_url=? WHERE name=?", (rel, name))
    conn.commit(); conn.close()
    return jsonify({"ok":True,"photo_url":rel})

@app.route("/photos/<path:name>")
def photos(name):
    return send_from_directory(PHOTOS, name)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8793, debug=False)
