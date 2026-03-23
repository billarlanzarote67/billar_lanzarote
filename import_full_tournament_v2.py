
import re
from bs4 import BeautifulSoup
import requests, sqlite3

DB = r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db"
HEADERS = {"User-Agent":"Mozilla/5.0"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

url = input("Paste CueScore tournament URL: ").strip()
html = fetch(url)
soup = BeautifulSoup(html, "html.parser")
conn = sqlite3.connect(DB)
cur = conn.cursor()
players = set()
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    t = a.get_text(" ", strip=True)
    if "/player/" in href and t:
        players.add(t)
for p in sorted(players):
    cur.execute("INSERT OR IGNORE INTO players(name) VALUES (?)", (p,))
conn.commit(); conn.close()
print("Tournament v2 import players:", len(players))
print("Next step: run REBUILD_PLAYER_SUMMARY.bat")
