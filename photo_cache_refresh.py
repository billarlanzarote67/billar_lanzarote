
import os, re, requests, sqlite3
from bs4 import BeautifulSoup
from stats_automation_common import load_cfg, db, ensure_dir, utc_now, append_log, log_run

def main():
    cfg = load_cfg()
    root = cfg["photo_cache_root"]
    ensure_dir(root)
    con = db(); cur = con.cursor()
    try:
        cur.execute("""SELECT m.player_id, m.cuescore_player_id, m.cuescore_profile_url, m.cuescore_display_name
                       FROM player_cuescore_map m
                       ORDER BY m.cuescore_display_name""")
        rows = cur.fetchall()
    except Exception:
        rows = []
    updated = 0
    for player_id, cuescore_pid, url, display_name in rows:
        if not url:
            continue
        try:
            html = requests.get(url, timeout=20).text
            soup = BeautifulSoup(html, "html.parser")
            img_url = None
            for img in soup.find_all("img", src=True):
                src = img.get("src", "")
                alt = (img.get("alt") or "").lower()
                if "player" in alt or "profile" in alt or "avatar" in src.lower():
                    img_url = src if src.startswith("http") else "https://cuescore.com" + src
                    break
            if img_url:
                ext = ".jpg"
                m = re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", img_url, re.I)
                if m:
                    ext = "." + m.group(1).lower()
                local = os.path.join(root, f"{cuescore_pid or player_id}{ext}")
                r = requests.get(img_url, timeout=20)
                if r.status_code == 200 and len(r.content) > 0:
                    with open(local, "wb") as f:
                        f.write(r.content)
                    try:
                        cur.execute("""CREATE TABLE IF NOT EXISTS player_media(
                            player_id TEXT PRIMARY KEY,
                            cuescore_player_id TEXT,
                            photo_url TEXT,
                            local_photo_path TEXT,
                            local_fallback_photo_path TEXT,
                            photo_source TEXT,
                            last_photo_sync_ts_utc TEXT,
                            notes TEXT
                        )""")
                        cur.execute("""INSERT OR REPLACE INTO player_media(
                            player_id, cuescore_player_id, photo_url, local_photo_path, local_fallback_photo_path, photo_source, last_photo_sync_ts_utc, notes
                        ) VALUES (?, ?, ?, ?, COALESCE((SELECT local_fallback_photo_path FROM player_media WHERE player_id = ?), NULL), ?, ?, ?)""",
                            (player_id, cuescore_pid, img_url, local, player_id, "cuescore", utc_now(), display_name))
                        con.commit()
                    except Exception as e:
                        append_log("photo_refresh.log", f"DB fail {url} :: {e}")
                    updated += 1
        except Exception as e:
            append_log("photo_refresh.log", f"FAIL {url} :: {e}")
    con.close()
    log_run("photo_refresh", None, "ok", {"updated": updated})
    print({"updated": updated})

if __name__ == "__main__":
    main()
