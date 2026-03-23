
import argparse, json, os, re, sqlite3, sys, time, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

DB = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
RAW_DIR = r"C:\AI\BillarLanzarote\data\raw_cuescore\tournaments"
LOG_DIR = r"C:\AI\BillarLanzarote\logs\import"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def ensure_dirs():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def db_conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db_conn()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        created_ts_utc TEXT NOT NULL,
        notes TEXT
    );
    CREATE TABLE IF NOT EXISTS player_cuescore_map (
        player_id TEXT PRIMARY KEY,
        cuescore_player_id TEXT,
        cuescore_profile_url TEXT,
        cuescore_display_name TEXT,
        last_verified_ts_utc TEXT
    );
    CREATE TABLE IF NOT EXISTS player_profile_stats (
        player_id TEXT PRIMARY KEY,
        matches_played REAL,
        wins REAL,
        losses REAL,
        win_rate REAL,
        innings_average REAL,
        runouts REAL,
        lag_wins REAL,
        frame_win_average REAL,
        points REAL,
        last_import_ts_utc TEXT,
        raw_json TEXT
    );
    CREATE TABLE IF NOT EXISTS tournament_player_results (
        row_id TEXT PRIMARY KEY,
        tournament_url TEXT NOT NULL,
        tournament_id TEXT,
        player_id TEXT,
        cuescore_player_id TEXT,
        display_name TEXT,
        matches_played REAL,
        wins REAL,
        losses REAL,
        frames_total REAL,
        frames_won REAL,
        frames_lost REAL,
        win_rate REAL,
        source_json TEXT,
        imported_ts_utc TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS player_media (
        player_id TEXT PRIMARY KEY,
        cuescore_player_id TEXT,
        photo_url TEXT,
        local_photo_path TEXT,
        local_fallback_photo_path TEXT,
        photo_source TEXT,
        last_photo_sync_ts_utc TEXT,
        notes TEXT
    );
    """)
    for col in [("player_profile_stats","frames_won"),("player_profile_stats","frames_lost"),("player_profile_stats","frames_total")]:
        try:
            cur.execute(f"ALTER TABLE {col[0]} ADD COLUMN {col[1]} REAL")
        except sqlite3.OperationalError:
            pass
    con.commit()
    con.close()

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def save_raw(url, html):
    path = os.path.join(RAW_DIR, re.sub(r"[^A-Za-z0-9]+","_",url)[:80] + "_" + time.strftime("%Y%m%d_%H%M%S") + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def norm(text):
    return re.sub(r"\s+", " ", (text or "")).strip()

def parse_number(text):
    if not text:
        return None
    m = re.search(r"[-+]?\d+(?:[.,]\d+)?", text.replace("%",""))
    return float(m.group(0).replace(",", ".")) if m else None

def player_id_for(display_name):
    return "plr_" + re.sub(r"[^a-z0-9]+","_",display_name.lower()).strip("_")

def extract_rows(soup, base_url):
    rows = []
    for tr in soup.find_all("tr"):
        row_text = norm(tr.get_text(" ", strip=True))
        a = tr.find("a", href=re.compile(r"/player/", re.I))
        if not a:
            continue
        href = a.get("href","").strip()
        full = href if href.startswith("http") else urljoin(base_url, href)
        full = full.replace("https://cuescore.com//cuescore.com", "https://cuescore.com").split("?")[0].split("#")[0]
        m = re.search(r"/player/([^/]+)/(\d+)$", full, re.I)
        if not m:
            continue
        display = norm(a.get_text(" ", strip=True)) or m.group(1).replace("+"," ")
        nums = re.findall(r"(\d+\s*\(\s*\d+\s*/\s*\d+\s*\)|\d+%?)", row_text)
        matches_total = wins = losses = frames_total = frames_won = frames_lost = win_rate = None
        if len(nums) >= 1:
            mm = re.search(r"(\d+)\s*\(\s*(\d+)\s*/\s*(\d+)\s*\)", nums[0])
            if mm:
                matches_total, wins, losses = map(float, mm.groups())
        if len(nums) >= 2:
            mf = re.search(r"(\d+)\s*\(\s*(\d+)\s*/\s*(\d+)\s*\)", nums[1])
            if mf:
                frames_total, frames_won, frames_lost = map(float, mf.groups())
        if len(nums) >= 3 and "%" in nums[2]:
            win_rate = parse_number(nums[2])

        rows.append({
            "display_name": display,
            "cuescore_player_id": m.group(2),
            "profile_url": full,
            "matches_played": matches_total,
            "wins": wins,
            "losses": losses,
            "frames_total": frames_total,
            "frames_won": frames_won,
            "frames_lost": frames_lost,
            "win_rate": win_rate,
        })
    dedup = {}
    for r in rows:
        dedup[r["cuescore_player_id"]] = r
    return list(dedup.values())

def import_tournament(url):
    ensure_dirs()
    init_db()
    html = fetch(url)
    raw = save_raw(url, html)
    soup = BeautifulSoup(html, "html.parser")
    rows = extract_rows(soup, url)
    con = db_conn()
    cur = con.cursor()
    imported = 0
    tid = re.search(r"/(\d+)$", url)
    tid = tid.group(1) if tid else None

    for r in rows:
        pid = player_id_for(r["display_name"])
        cur.execute("INSERT OR IGNORE INTO players(player_id, display_name, created_ts_utc, notes) VALUES (?, ?, ?, ?)",
                    (pid, r["display_name"], utc_now(), "Created/updated by tournament stats importer"))
        cur.execute("""
            INSERT OR REPLACE INTO player_cuescore_map(player_id, cuescore_player_id, cuescore_profile_url, cuescore_display_name, last_verified_ts_utc)
            VALUES (?, ?, ?, ?, ?)
        """, (pid, r["cuescore_player_id"], r["profile_url"], r["display_name"], utc_now()))
        cur.execute("""
            INSERT OR REPLACE INTO player_profile_stats(player_id, matches_played, wins, losses, win_rate, innings_average, runouts, lag_wins, frame_win_average, points, last_import_ts_utc, raw_json, frames_won, frames_lost, frames_total)
            VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT innings_average FROM player_profile_stats WHERE player_id=?), NULL),
                    COALESCE((SELECT runouts FROM player_profile_stats WHERE player_id=?), NULL),
                    COALESCE((SELECT lag_wins FROM player_profile_stats WHERE player_id=?), NULL),
                    COALESCE((SELECT frame_win_average FROM player_profile_stats WHERE player_id=?), NULL),
                    COALESCE((SELECT points FROM player_profile_stats WHERE player_id=?), NULL),
                    ?, ?, ?, ?, ?)
        """, (pid, r["matches_played"], r["wins"], r["losses"], r["win_rate"],
              pid, pid, pid, pid, pid, utc_now(), json.dumps(r, ensure_ascii=False), r["frames_won"], r["frames_lost"], r["frames_total"]))
        cur.execute("""
            INSERT OR REPLACE INTO tournament_player_results(row_id, tournament_url, tournament_id, player_id, cuescore_player_id, display_name, matches_played, wins, losses, frames_total, frames_won, frames_lost, win_rate, source_json, imported_ts_utc)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"{tid}_{r['cuescore_player_id']}", url, tid, pid, r["cuescore_player_id"], r["display_name"], r["matches_played"], r["wins"], r["losses"], r["frames_total"], r["frames_won"], r["frames_lost"], r["win_rate"], json.dumps(r, ensure_ascii=False), utc_now()))
        imported += 1
    con.commit()
    con.close()
    return {"imported": imported, "raw_html": raw, "rows": len(rows), "url": url}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--mode", default="update")
    args = ap.parse_args()
    print(json.dumps(import_tournament(args.url), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"status":"fail","error":str(e)}, indent=2, ensure_ascii=False))
        sys.exit(1)
