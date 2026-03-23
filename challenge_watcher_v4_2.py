from playwright.sync_api import sync_playwright
import time
import json
import os
from datetime import datetime

# =========================
# CONFIG
# =========================
ROOT = r"C:\AI\BillarLanzarote"
OUT = os.path.join(ROOT, "data", "challenge_stats", "challenge_state.json")

# =========================
# SAVE FUNCTION
# =========================
def save(data):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# =========================
# MAIN
# =========================
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
            # =========================
            # SCORES
            # =========================
            score_a = int(page.locator(".score.scoreA.playerA").first.inner_text().strip())
            score_b = int(page.locator(".score.scoreB.playerB").first.inner_text().strip())

            # =========================
            # PLAYER NAMES
            # =========================
            player_a = page.locator(".contentPlayerA").first.inner_text().split("\n")[0].strip()
            player_b = page.locator(".contentPlayerB").first.inner_text().split("\n")[0].strip()

            # =========================
            # RACE TO (FIXED PROPERLY)
            # =========================
            race_to = None

            try:
                race_raw = page.locator(".raceTo").first.inner_text().strip()
                race_to = int(race_raw)
            except:
                pass

            race_es = f"Carrera a {race_to}" if race_to else "Carrera desconocida"

            # =========================
            # OUTPUT
            # =========================
            score = f"{score_a}-{score_b}"

            if score != last_score:
                print(f"🔥 {player_a} {score} {player_b} ({race_es})")
                last_score = score

                save({
                    "player_a": player_a,
                    "player_b": player_b,
                    "score_a": score_a,
                    "score_b": score_b,
                    "score": score,
                    "race_to": race_to,
                    "race_text_es": race_es,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            print("Error:", e)

        time.sleep(2)
