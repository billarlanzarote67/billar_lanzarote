
import os, sqlite3, requests
from bs4 import BeautifulSoup

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
HEADERS = {"User-Agent":"Mozilla/5.0"}

def conn():
    return sqlite3.connect(DB)

def upsert_player(name, photo_url=""):
    if not name: return
    c = conn()
    cur = c.cursor()
    cur.execute("INSERT OR IGNORE INTO players(name, photo_url) VALUES (?,?)", (name, photo_url))
    if photo_url:
        cur.execute("UPDATE players SET photo_url=? WHERE name=?", (photo_url, name))
    c.commit(); c.close()

def insert_match(table_name, player_a, player_b, winner, score_a, score_b, challenge_url, source):
    c = conn()
    cur = c.cursor()
    cur.execute("""
        INSERT INTO matches(table_key, table_name, player_a, player_b, winner, score_a, score_b, challenge_url, source)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, ("manual_import", table_name, player_a, player_b, winner, score_a, score_b, challenge_url, source))
    c.commit(); c.close()

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text
