
import time, json, os
from datetime import datetime
from playwright.sync_api import sync_playwright

ROOT = r"C:\AI\BillarLanzarote"
OUT_JSON = os.path.join(ROOT, "data", "challenge_stats", "challenge_state.json")
LOG_FILE = os.path.join(ROOT, "logs", "challenge_watcher_v4_1.log")

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

URL = input("Paste CueScore challenge URL: ").strip()

last_score = None

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def extract_score(text):
    import re
    m = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL)

    log("Page loaded, waiting for content...")
    time.sleep(5)

    while True:
        try:
            content = page.inner_text("body")

            a, b = extract_score(content)

            if a is not None:
                score = f"{a}-{b}"
                confidence = 0.8 if a is not None else 0.2

                if score != last_score:
                    log(f"Score update detected: {score} (confidence {confidence})")
                    last_score = score

                    data = {
                        "score_a": a,
                        "score_b": b,
                        "score": score,
                        "confidence": confidence,
                        "timestamp": datetime.now().isoformat()
                    }

                    with open(OUT_JSON, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)

            else:
                log("Score not detected")

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(10)
