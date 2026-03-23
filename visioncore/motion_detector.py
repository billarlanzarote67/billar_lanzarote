
import cv2, sys, json, os, time
cfg = json.load(open(r"C:\AI\BillarLanzarote\config\visioncore_config.json", "r", encoding="utf-8"))
table = sys.argv[1] if len(sys.argv) > 1 else "mesa1"
src = cfg[table]["source"]
state_path = cfg[table]["state_path"]
cap = cv2.VideoCapture(src)
prev = None
print("Motion detector:", table)
while True:
    ok, frame = cap.read()
    if not ok:
        time.sleep(1); continue
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if prev is None:
        prev = gray
        continue
    diff = cv2.absdiff(prev, gray)
    score = float(diff.mean())
    state = {"table": table, "motion_score": round(score,2), "motion_active": score > cfg.get("motion_threshold",18), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(state)
    prev = gray
    time.sleep(1)
