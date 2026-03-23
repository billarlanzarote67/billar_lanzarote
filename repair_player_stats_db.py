
import json, re, sqlite3, time
DB = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
def norm(s): return re.sub(r"\s+"," ",(s or "").strip()).lower()
def safe_max(*vals):
    vals = [v for v in vals if v not in (None, "", "None")]
    if not vals: return None
    try: return max(float(v) for v in vals)
    except: return vals[0]
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; cur = con.cursor()
for col in ("frames_won","frames_lost","frames_total"):
    try: cur.execute(f"ALTER TABLE player_profile_stats ADD COLUMN {col} REAL")
    except sqlite3.OperationalError: pass
cur.execute("SELECT player_id, display_name FROM players ORDER BY display_name")
rows = [dict(r) for r in cur.fetchall()]
groups = {}
for r in rows: groups.setdefault(norm(r["display_name"]), []).append(r)
merged = 0; deleted = 0
for _, grp in groups.items():
    if len(grp) < 2: continue
    keeper = grp[0]["player_id"]
    stats = {"matches_played":None,"wins":None,"losses":None,"win_rate":None,"frames_won":None,"frames_lost":None,"frames_total":None,"points":None}
    cue = {"cuescore_player_id":None,"cuescore_profile_url":None,"cuescore_display_name":grp[0]["display_name"]}
    media = {"photo_url":None,"local_photo_path":None,"local_fallback_photo_path":None}
    for g in grp:
        pid = g["player_id"]
        cur.execute("SELECT * FROM player_profile_stats WHERE player_id=?", (pid,))
        s = cur.fetchone()
        if s:
            d = dict(s)
            for k in stats: stats[k] = safe_max(stats[k], d.get(k))
        cur.execute("SELECT * FROM player_cuescore_map WHERE player_id=?", (pid,))
        m = cur.fetchone()
        if m:
            d = dict(m)
            cue["cuescore_player_id"] = cue["cuescore_player_id"] or d.get("cuescore_player_id")
            cue["cuescore_profile_url"] = cue["cuescore_profile_url"] or d.get("cuescore_profile_url")
            cue["cuescore_display_name"] = cue["cuescore_display_name"] or d.get("cuescore_display_name")
        cur.execute("SELECT * FROM player_media WHERE player_id=?", (pid,))
        md = cur.fetchone()
        if md:
            d = dict(md)
            media["photo_url"] = media["photo_url"] or d.get("photo_url")
            media["local_photo_path"] = media["local_photo_path"] or d.get("local_photo_path")
            media["local_fallback_photo_path"] = media["local_fallback_photo_path"] or d.get("local_fallback_photo_path")
    cur.execute("""INSERT OR REPLACE INTO player_profile_stats
    (player_id,matches_played,wins,losses,win_rate,innings_average,runouts,lag_wins,frame_win_average,points,last_import_ts_utc,raw_json,frames_won,frames_lost,frames_total)
    VALUES (?,?,?,?,?,COALESCE((SELECT innings_average FROM player_profile_stats WHERE player_id=?),NULL),
    COALESCE((SELECT runouts FROM player_profile_stats WHERE player_id=?),NULL),
    COALESCE((SELECT lag_wins FROM player_profile_stats WHERE player_id=?),NULL),
    COALESCE((SELECT frame_win_average FROM player_profile_stats WHERE player_id=?),NULL),
    ?,?,?,?, ?,?)""",
    (keeper,stats["matches_played"],stats["wins"],stats["losses"],stats["win_rate"],keeper,keeper,keeper,keeper,stats["points"],time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),json.dumps({"merged":[g["player_id"] for g in grp]}),stats["frames_won"],stats["frames_lost"],stats["frames_total"]))
    cur.execute("INSERT OR REPLACE INTO player_cuescore_map(player_id,cuescore_player_id,cuescore_profile_url,cuescore_display_name,last_verified_ts_utc) VALUES (?,?,?,?,?)",
                (keeper,cue["cuescore_player_id"],cue["cuescore_profile_url"],cue["cuescore_display_name"],time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    cur.execute("INSERT OR REPLACE INTO player_media(player_id,cuescore_player_id,photo_url,local_photo_path,local_fallback_photo_path,photo_source,last_photo_sync_ts_utc,notes) VALUES (?,?,?,?,?,'merged',?,'Merged duplicates')",
                (keeper,cue["cuescore_player_id"],media["photo_url"],media["local_photo_path"],media["local_fallback_photo_path"],time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    for g in grp[1:]:
        pid = g["player_id"]
        cur.execute("DELETE FROM player_profile_stats WHERE player_id=?", (pid,))
        cur.execute("DELETE FROM player_cuescore_map WHERE player_id=?", (pid,))
        cur.execute("DELETE FROM player_media WHERE player_id=?", (pid,))
        cur.execute("DELETE FROM players WHERE player_id=?", (pid,))
        deleted += 1
    merged += 1
con.commit(); con.close()
print(json.dumps({"status":"ok","merged_groups":merged,"deleted_duplicate_rows":deleted}, indent=2))
