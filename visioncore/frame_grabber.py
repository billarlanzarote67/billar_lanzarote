
import cv2, sys, json, os, time
cfg = json.load(open(r"C:\AI\BillarLanzarote\config\visioncore_config.json", "r", encoding="utf-8"))
table = sys.argv[1] if len(sys.argv) > 1 else "mesa1"
src = cfg[table]["source"]
cap = cv2.VideoCapture(src)
print("Opening:", src)
while True:
    ok, frame = cap.read()
    if not ok:
        print("Frame read failed"); time.sleep(1); continue
    print(f"{table}: frame {frame.shape[1]}x{frame.shape[0]}")
    time.sleep(0.5)
