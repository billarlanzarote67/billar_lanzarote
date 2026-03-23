
import time
import requests
from datetime import datetime

URL = input("Paste CueScore challenge URL: ").strip()

print("Starting watcher...")
last_score = None

while True:
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
        text = r.text

        # VERY BASIC score detection (temporary but real)
        import re
        match = re.search(r"(\d+)\s*-\s*(\d+)", text)

        if match:
            score = f"{match.group(1)}-{match.group(2)}"

            if score != last_score:
                print(f"[{datetime.now()}] Score change detected:", score)
                last_score = score

        else:
            print("Score not found...")

    except Exception as e:
        print("Error:", e)

    time.sleep(10)
