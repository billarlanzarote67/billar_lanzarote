
import re, json, sys
from _import_common import fetch, upsert_player, insert_match
from bs4 import BeautifulSoup

url = input("Paste CueScore tournament URL: ").strip()
html = fetch(url)
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(" ", strip=True)

# Simple pass: collect player links and challenge links
players = set()
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    label = a.get_text(" ", strip=True)
    if "/player/" in href and label:
        players.add(label)

for p in sorted(players):
    upsert_player(p)

print("Players imported:", len(players))
print("Tournament parsed (basic mode).")
