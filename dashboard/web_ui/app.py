import os, sqlite3, subprocess, html
from flask import Flask, request, redirect, send_from_directory
from werkzeug.utils import secure_filename
from db_locator import find_best_db

DB, SCORED = find_best_db()
UPLOAD_DIR = r"C:\AI\BillarLanzarote\data\players\photos\local_uploads"
PYTHON_EXE = r"C:\Program Files\Python312\python.exe"
IMPORT_SCRIPT = r"C:\AI\BillarLanzarote\scripts\import_tournament_results_any_v2.py"
app = Flask(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def rows(sql, params=()):
    con = db(); cur = con.cursor(); cur.execute(sql, params)
    out = [dict(r) for r in cur.fetchall()]
    con.close(); return out

def fmt_int(v):
    if v in (None, '', 'None'): return ''
    try: return str(int(float(v)))
    except Exception: return str(v)

def has_table(name):
    con = db(); cur = con.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    ok = cur.fetchone() is not None
    con.close(); return ok

@app.route('/uploads/<path:name>')
def uploads(name):
    return send_from_directory(UPLOAD_DIR, name)

@app.route('/upload_photo/<player_id>', methods=['POST'])
def upload_photo(player_id):
    file = request.files.get('photo')
    if not file or not file.filename:
        return redirect('/')
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1] or '.jpg'
    save_name = f'{player_id}{ext}'
    path = os.path.join(UPLOAD_DIR, save_name)
    file.save(path)
    con = db(); cur = con.cursor()
    if has_table('player_media'):
        cur.execute("""
        INSERT OR REPLACE INTO player_media(
            player_id,cuescore_player_id,photo_url,local_photo_path,local_fallback_photo_path,
            photo_source,last_photo_sync_ts_utc,notes
        ) VALUES (
            ?,
            COALESCE((SELECT cuescore_player_id FROM player_media WHERE player_id=?),NULL),
            COALESCE((SELECT photo_url FROM player_media WHERE player_id=?),NULL),
            ?,?,
            'local_upload',datetime('now'),'Local uploaded photo'
        )
        """, (player_id, player_id, player_id, path, path))
        con.commit()
    con.close()
    return redirect('/')

@app.route('/', methods=['GET'])
def index():
    tournament_url = request.args.get('tournament_url', '')
    players = rows("""
    SELECT p.player_id,p.display_name,
           s.matches_played,s.wins,s.losses,s.win_rate,s.frames_won,s.frames_lost,s.frames_total,
           m.cuescore_profile_url,m.cuescore_player_id,
           media.photo_url,media.local_photo_path,media.local_fallback_photo_path
    FROM players p
    LEFT JOIN player_profile_stats s ON s.player_id=p.player_id
    LEFT JOIN player_cuescore_map m ON m.player_id=p.player_id
    LEFT JOIN player_media media ON media.player_id=p.player_id
    ORDER BY COALESCE(s.wins,0) DESC, COALESCE(s.win_rate,0) DESC, p.display_name ASC
    """)
    cards = ''
    for p in players:
        photo = p.get('local_photo_path') or p.get('local_fallback_photo_path') or p.get('photo_url') or ''
        if photo and str(photo).lower().startswith('c:'):
            photo_src = '/uploads/' + html.escape(os.path.basename(photo)) if os.path.exists(photo) else html.escape(str(photo))
        else:
            photo_src = html.escape(str(photo)) if photo else ''
        photo_html = f"<img src='{photo_src}' style='width:88px;height:88px;object-fit:cover;border-radius:50%;background:#333'>" if photo_src else "<div style='width:88px;height:88px;border-radius:50%;background:#333;display:flex;align-items:center;justify-content:center;color:#999'>No Photo</div>"
        winpct = '' if p.get('win_rate') in (None,'','None') else f"{round(float(p['win_rate']))}%"
        cuescore_btn = f"<a href='{html.escape(str(p.get('cuescore_profile_url')))}' target='_blank' style='display:inline-block;padding:8px 12px;background:#2d8cff;color:#fff;border-radius:8px;text-decoration:none'>CueScore</a>" if p.get('cuescore_profile_url') else ''
        pid = html.escape(str(p['player_id']))
        name = html.escape(str(p['display_name']))
        cid = fmt_int(p.get('cuescore_player_id'))
        cards += f"<div class='card'><div style='display:flex;gap:14px;align-items:center'>{photo_html}<div style='flex:1'><div class='name'>{name}</div><div class='muted'>CueScore ID: {cid}</div>{cuescore_btn}</div></div><div class='stats'><div>Matches: {fmt_int(p.get('matches_played'))}</div><div>Wins/Losses: {fmt_int(p.get('wins'))} / {fmt_int(p.get('losses'))}</div><div>Frames W/L: {fmt_int(p.get('frames_won'))} / {fmt_int(p.get('frames_lost'))}</div><div>Win %: {winpct}</div></div><form action='/upload_photo/{pid}' method='post' enctype='multipart/form-data' style='margin-top:12px'><input type='file' name='photo' accept='image/*'><button type='submit'>Upload Local Photo</button></form></div>"
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Billar Lanzarote Player Gallery</title><style>body{{font-family:Arial,sans-serif;background:#111;color:#eee;padding:20px}}h1{{margin-bottom:8px}}.muted{{color:#bbb}}.toolbar{{background:#1c1c1c;border-radius:16px;padding:16px;margin-bottom:18px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}.card{{background:#1c1c1c;border-radius:16px;padding:16px;box-shadow:0 4px 12px rgba(0,0,0,.25)}}.name{{font-size:24px;font-weight:bold;margin-bottom:6px}}.stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}}input,button{{padding:8px;border-radius:8px;border:none}}button{{background:#2d8cff;color:white;cursor:pointer}}.note{{background:#1c1c1c;padding:10px;border-radius:10px;margin:0 0 14px 0;color:#ccc}}</style></head><body><h1>Billar Lanzarote Player Gallery</h1><div class='muted'>Players in database: {len(players)} | DB: {html.escape(DB)}</div><div class='note'>DB candidates: {html.escape(str(SCORED))}</div><div class='toolbar'><form action='/run_import' method='post'><div style='display:flex;gap:8px;align-items:center;flex-wrap:wrap'><label>Tournament URL</label><input type='text' name='tournament_url' style='min-width:420px' value='{html.escape(tournament_url)}' placeholder='Paste CueScore tournament URL'><button type='submit'>Import / Update Tournament</button></div></form></div><div class='grid'>{cards or '<div class=card>No players found.</div>'}</div></body></html>"

@app.route('/run_import', methods=['POST'])
def run_import():
    url = request.form.get('tournament_url','').strip()
    if not url:
        return redirect('/')
    subprocess.Popen([PYTHON_EXE, IMPORT_SCRIPT, '--url', url, '--mode', 'update'])
    return redirect(f'/?tournament_url={url}')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8099, debug=False)
