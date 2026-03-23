
import re
from bs4 import BeautifulSoup
from _import_common import fetch, upsert_player, insert_match

url = input("Paste CueScore challenge URL: ").strip()
html = fetch(url)
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(" ", strip=True)

players = []
for a in soup.find_all("a", href=True):
    href = a.get("href","")
    t = a.get_text(" ", strip=True)
    if "/player/" in href and t and t not in players:
        players.append(t)

m = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
score_a = int(m.group(1)) if m else None
score_b = int(m.group(2)) if m else None
player_a = players[0] if len(players) > 0 else None
player_b = players[1] if len(players) > 1 else None
winner = None
if score_a is not None and score_b is not None:
    winner = player_a if score_a > score_b else player_b

for p in [player_a, player_b]:
    if p: upsert_player(p)

if player_a and player_b:
    insert_match("Challenge", player_a, player_b, winner, score_a, score_b, url, "challenge_import")
    print("Challenge match imported.")
else:
    print("Could not confidently parse both players.")
