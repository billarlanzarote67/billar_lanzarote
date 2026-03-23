
import os, json, re, sqlite3, requests, time
from bs4 import BeautifulSoup

ROOT = r"C:\AI\BillarLanzarote"
OUTDIR = os.path.join(ROOT, "data", "challenge_stats")
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
os.makedirs(OUTDIR, exist_ok=True)

def init_table():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challenge_match_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        winner TEXT,
        frames_won_a INTEGER,
        frames_won_b INTEGER,
        average_frame_time_a TEXT,
        average_frame_time_b TEXT,
        win_pct_a REAL,
        win_pct_b REAL,
        runouts_a INTEGER,
        runouts_b INTEGER,
        break_wins_a INTEGER,
        break_wins_b INTEGER,
        frames_stolen_a INTEGER,
        frames_stolen_b INTEGER,
        timeouts_a INTEGER,
        timeouts_b INTEGER,
        raw_json_path TEXT,
        created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def fetch(url):
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    return r.text

def maybe_num(text):
    try:
        return int(text)
    except Exception:
        try:
            return float(text.replace("%","").strip())
        except Exception:
            return None

def parse_from_text(text):
    # best-effort parser for public challenge pages / screenshots text dumps
    stats = {
        "frames_won_a": None, "frames_won_b": None,
        "average_frame_time_a": None, "average_frame_time_b": None,
        "win_pct_a": None, "win_pct_b": None,
        "runouts_a": None, "runouts_b": None,
        "break_wins_a": None, "break_wins_b": None,
        "frames_stolen_a": None, "frames_stolen_b": None,
        "timeouts_a": None, "timeouts_b": None,
    }
    m = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    score_a = int(m.group(1)) if m else None
    score_b = int(m.group(2)) if m else None
    return stats, score_a, score_b

def find_players_and_score(soup):
    text = soup.get_text(" ", strip=True)
    players = []
    for a in soup.find_all("a", href=True):
        href = a.get("href","")
        t = a.get_text(" ", strip=True)
        if "/player/" in href and t and t not in players:
            players.append(t)
    stats, score_a, score_b = parse_from_text(text)
    return players[:2], score_a, score_b, stats, text[:2000]

init_table()
url = input("Paste CueScore challenge URL: ").strip()
html = fetch(url)
soup = BeautifulSoup(html, "html.parser")
players, score_a, score_b, stats, snippet = find_players_and_score(soup)
player_a = players[0] if len(players) > 0 else None
player_b = players[1] if len(players) > 1 else None
winner = None
if score_a is not None and score_b is not None:
    winner = player_a if score_a > score_b else player_b

payload = {
    "url": url,
    "player_a": player_a, "player_b": player_b,
    "score_a": score_a, "score_b": score_b,
    "winner": winner,
    **stats,
    "raw_text_snippet": snippet
}
out = os.path.join(OUTDIR, "last_challenge_stats_v2.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
INSERT INTO challenge_match_stats (
 url, player_a, player_b, score_a, score_b, winner,
 frames_won_a, frames_won_b, average_frame_time_a, average_frame_time_b,
 win_pct_a, win_pct_b, runouts_a, runouts_b, break_wins_a, break_wins_b,
 frames_stolen_a, frames_stolen_b, timeouts_a, timeouts_b, raw_json_path
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (
    url, player_a, player_b, score_a, score_b, winner,
    stats["frames_won_a"], stats["frames_won_b"], stats["average_frame_time_a"], stats["average_frame_time_b"],
    stats["win_pct_a"], stats["win_pct_b"], stats["runouts_a"], stats["runouts_b"], stats["break_wins_a"], stats["break_wins_b"],
    stats["frames_stolen_a"], stats["frames_stolen_b"], stats["timeouts_a"], stats["timeouts_b"], out
))
conn.commit()
conn.close()
print("Saved JSON:", out)
print("Saved SQLite row in challenge_match_stats")
