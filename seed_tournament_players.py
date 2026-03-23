
import json, os, re, sqlite3, sys, uuid, requests, time
from bs4 import BeautifulSoup

DB = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
CFG = r"C:\AI\BillarLanzarote\config\stats_system_upgrade_v2.json"
SQL = r"C:\AI\BillarLanzarote\sql\stats_system_upgrade_v2.sql"

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def init_schema():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    if os.path.exists(SQL):
        cur.executescript(open(SQL, "r", encoding="utf-8").read())
    con.commit(); con.close()

def load_cfg():
    with open(CFG, "r", encoding="utf-8") as f:
        return json.load(f)

def ensure_player(display_name):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    try:
        cur.execute("SELECT player_id FROM players WHERE display_name = ?", (display_name,))
        row = cur.fetchone()
        if row:
            con.close()
            return row[0]
    except sqlite3.Error:
        pass
    pid = str(uuid.uuid4())
    try:
        cur.execute("INSERT INTO players(player_id, display_name, created_ts_utc, notes) VALUES (?, ?, ?, ?)",
                    (pid, display_name, utc_now(), "Auto-created from tournament seeder"))
        con.commit()
    except sqlite3.Error:
        pass
    con.close()
    return pid

def seed_tournament():
    cfg = load_cfg()
    url = cfg["seed_tournament_url"]
    tid = cfg["seed_tournament_id"]
    html = requests.get(url, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    # This is a conservative starter: scrape rows from text heuristically and store raw text snapshot
    raw_rows = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if len(ln) < 2:
            continue
        # Keep rows with percentages or frame/match language visible on tournament rankings page
        if "%" in ln or "Frames" in ln or "Matches" in ln:
            raw_rows.append({"line_no": i, "text": ln})

    # Save raw snapshot row into import_health
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""INSERT OR REPLACE INTO import_health(item_key, item_type, status, last_checked_ts_utc, details_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"tournament_seed_{tid}", "tournament_seed", "seeded_raw", utc_now(), json.dumps({"url": url, "raw_row_count": len(raw_rows)}, ensure_ascii=False)))
    con.commit(); con.close()

    # Minimal seed from known visible players on page by anchor text fallback
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        name = a.get_text(" ", strip=True)
        if "/player/" in href and name:
            pid_local = ensure_player(name)
            m = re.search(r"/player/(\d+)", href)
            cuescore_pid = m.group(1) if m else None
            con = sqlite3.connect(DB)
            cur = con.cursor()
            try:
                cur.execute("""INSERT OR REPLACE INTO player_cuescore_map(player_id, cuescore_player_id, cuescore_profile_url, cuescore_display_name, last_verified_ts_utc)
                               VALUES (?, ?, ?, ?, ?)""",
                            (pid_local, cuescore_pid or "", href if href.startswith("http") else "https://cuescore.com" + href, name, utc_now()))
                cur.execute("""INSERT INTO tournament_participant_stats(
                               row_id, tournament_id, tournament_name, cuescore_player_id, display_name, nationality,
                               matches_played, matches_won, matches_lost, frames_won, frames_lost, win_percentage,
                               imported_ts_utc, raw_json)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (str(uuid.uuid4()), tid, "Inaguración Billar Lanzarote", cuescore_pid, name, None,
                             None, None, None, None, None, None, utc_now(), json.dumps({"source_href": href}, ensure_ascii=False)))
                con.commit()
            except sqlite3.Error:
                pass
            con.close()

    print("Tournament seeding complete")

if __name__ == "__main__":
    init_schema()
    seed_tournament()
