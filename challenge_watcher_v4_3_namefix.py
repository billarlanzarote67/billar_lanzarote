from playwright.sync_api import sync_playwright
import time
import json
import os
import re
import unicodedata
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
OUT = os.path.join(ROOT, "data", "challenge_stats", "challenge_state.json")
DEBUG = os.path.join(ROOT, "logs", "challenge_name_debug")
os.makedirs(DEBUG, exist_ok=True)

def save(data):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def strip_flags_and_symbols(text):
    if not text:
        return text
    cleaned = []
    for ch in text:
        if unicodedata.category(ch).startswith("S"):
            continue
        cleaned.append(ch)
    return "".join(cleaned)

def extract_player_name(block_text):
    if not block_text:
        return None
    block_text = strip_flags_and_symbols(block_text)
    bad = {
        "breaking", "runouts", "runout", "rack", "undo", "timeout", "end match",
        "pause", "resume", "ball in hand", "innings", "average", "high run",
        "total average", "total", "break no-score", "no-score"
    }
    lines = []
    for line in block_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        low = line.lower()
        if any(word in low for word in bad):
            continue
        if low.startswith("race to") or low.startswith("table ") or low.startswith("mesa "):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    if not lines:
        return None
    return " ".join(lines[:2]).strip()

url = input("Paste CueScore URL: ").strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    print("Page loaded...")
    time.sleep(5)
    last_score = None

    while True:
        try:
            score_a = int(page.locator(".score.scoreA.playerA").first.inner_text().strip())
            score_b = int(page.locator(".score.scoreB.playerB").first.inner_text().strip())

            raw_a = page.locator(".contentPlayerA").first.inner_text().strip()
            raw_b = page.locator(".contentPlayerB").first.inner_text().strip()
            player_a = extract_player_name(raw_a)
            player_b = extract_player_name(raw_b)

            race_to = None
            try:
                race_to = int(page.locator(".raceTo").first.inner_text().strip())
            except:
                pass

            score = f"{score_a}-{score_b}"
            if score != last_score:
                print(f"🔥 {player_a} {score} {player_b}")
                last_score = score

                save({
                    "player_a": player_a,
                    "player_b": player_b,
                    "raw_player_a": raw_a,
                    "raw_player_b": raw_b,
                    "score_a": score_a,
                    "score_b": score_b,
                    "score": score,
                    "race_to": race_to,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            print("Error:", e)

        time.sleep(2)
