
import os, re, json, sqlite3, requests, time
from bs4 import BeautifulSoup

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
OUTDIR = os.path.join(ROOT, "data", "challenge_stats")
RAWDIR = os.path.join(OUTDIR, "raw")
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(RAWDIR, exist_ok=True)

def init():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS challenge_match_stats_v3 (
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
        raw_text_snippet TEXT,
        raw_html_path TEXT,
        raw_json_path TEXT,
        created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit(); conn.close()

def fetch(url):
    r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    return r.text

def get_text(soup):
    return soup.get_text(" ", strip=True)

def extract_players(soup):
    players = []
    for a in soup.find_all("a", href=True):
        href = a.get("href","")
        t = a.get_text(" ", strip=True)
        if "/player/" in href and t and t not in players:
            players.append(t)
    return players[:2]

def extract_score(text):
    m = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))

def extract_pair(text, label):
    pat = re.compile(rf"(\d+)\s+{re.escape(label)}\s+(\d+)", re.I)
    m = pat.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def extract_pct_pair(text, label):
    pat = re.compile(rf"(\d+(?:\.\d+)?)%\s+{re.escape(label)}\s+(\d+(?:\.\d+)?)%", re.I)
    m = pat.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

def extract_time_pair(text, label):
    pat = re.compile(rf"([0-9mh s:]+)\s+{re.escape(label)}\s+([0-9mh s:]+)", re.I)
    m = pat.search(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, None

init()
url = input("Paste CueScore challenge URL: ").strip()
html = fetch(url)
stamp = time.strftime("%Y%m%d_%H%M%S")
raw_html_path = os.path.join(RAWDIR, f"challenge_{stamp}.html")
with open(raw_html_path, "w", encoding="utf-8") as f:
    f.write(html)

soup = BeautifulSoup(html, "html.parser")
text = get_text(soup)
player_a, player_b = (extract_players(soup) + [None, None])[:2]
score_a, score_b = extract_score(text)
winner = player_a if score_a is not None and score_b is not None and score_a > score_b else player_b if score_a is not None and score_b is not None and score_b > score_a else None

frames_won_a, frames_won_b = extract_pair(text, "Frames won")
avg_a, avg_b = extract_time_pair(text, "Average frametime")
win_pct_a, win_pct_b = extract_pct_pair(text, "Win %")
runouts_a, runouts_b = extract_pair(text, "Runouts")
break_wins_a, break_wins_b = extract_pair(text, "Break and wins")
frames_stolen_a, frames_stolen_b = extract_pair(text, "Frames stolen")
timeouts_a, timeouts_b = extract_pair(text, "Timeouts")

payload = {
    "url": url,
    "player_a": player_a, "player_b": player_b,
    "score_a": score_a, "score_b": score_b, "winner": winner,
    "frames_won_a": frames_won_a, "frames_won_b": frames_won_b,
    "average_frame_time_a": avg_a, "average_frame_time_b": avg_b,
    "win_pct_a": win_pct_a, "win_pct_b": win_pct_b,
    "runouts_a": runouts_a, "runouts_b": runouts_b,
    "break_wins_a": break_wins_a, "break_wins_b": break_wins_b,
    "frames_stolen_a": frames_stolen_a, "frames_stolen_b": frames_stolen_b,
    "timeouts_a": timeouts_a, "timeouts_b": timeouts_b,
    "raw_text_snippet": text[:3000],
    "raw_html_path": raw_html_path
}
raw_json_path = os.path.join(OUTDIR, f"challenge_{stamp}.json")
payload["raw_json_path"] = raw_json_path
with open(raw_json_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
INSERT INTO challenge_match_stats_v3 (
url, player_a, player_b, score_a, score_b, winner,
frames_won_a, frames_won_b, average_frame_time_a, average_frame_time_b,
win_pct_a, win_pct_b, runouts_a, runouts_b, break_wins_a, break_wins_b,
frames_stolen_a, frames_stolen_b, timeouts_a, timeouts_b,
raw_text_snippet, raw_html_path, raw_json_path
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (
 url, player_a, player_b, score_a, score_b, winner,
 frames_won_a, frames_won_b, avg_a, avg_b,
 win_pct_a, win_pct_b, runouts_a, runouts_b, break_wins_a, break_wins_b,
 frames_stolen_a, frames_stolen_b, timeouts_a, timeouts_b,
 text[:3000], raw_html_path, raw_json_path
))
conn.commit(); conn.close()

print("Saved JSON:", raw_json_path)
print("Saved SQLite row in challenge_match_stats_v3")
