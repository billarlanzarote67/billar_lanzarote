import argparse
import json
import math
import os
import time
from pathlib import Path

import cv2
import numpy as np

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_runtime(path):
    return load_json(path)

def get_source(args, runtime):
    if args.rtsp_from_config:
        url = runtime["input"]["rtsp_url_high"]
        return cv2.VideoCapture(url), f"rtsp:{url}"
    if args.rtsp:
        return cv2.VideoCapture(args.rtsp), f"rtsp:{args.rtsp}"
    return cv2.VideoCapture(args.camera), f"camera:{args.camera}"

def detect_circles(warped, cfg):
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    blur_k = int(cfg.get("blur_kernel", 7))
    if blur_k % 2 == 0:
        blur_k += 1
    gray = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=float(cfg.get("hough_dp", 1.2)),
        minDist=float(cfg.get("hough_min_dist", 28)),
        param1=float(cfg.get("hough_param1", 100)),
        param2=float(cfg.get("hough_param2", 18)),
        minRadius=int(cfg.get("min_radius", 8)),
        maxRadius=int(cfg.get("max_radius", 22)),
    )

    out = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            out.append({"x": int(x), "y": int(y), "r": int(r)})
    return out

def draw_circles(frame, circles):
    for i, c in enumerate(circles, start=1):
        x, y, r = c["x"], c["y"], c["r"]
        cv2.circle(frame, (x, y), r, (0, 255, 255), 2)
        cv2.circle(frame, (x, y), 2, (0, 0, 255), 3)
        cv2.putText(frame, str(i), (x - 6, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

def circles_signature(circles):
    pts = sorted([(c["x"], c["y"]) for c in circles])
    return pts

def movement_amount(a, b):
    if not a or not b:
        return 9999
    # cheap signature difference
    n = min(len(a), len(b))
    if n == 0:
        return 9999
    total = 0
    for i in range(n):
        total += abs(a[i][0] - b[i][0]) + abs(a[i][1] - b[i][1])
    return total / n

def save_layout(layout_dir, circles):
    Path(layout_dir).mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = Path(layout_dir) / f"layout_{ts}.json"
    data = {
        "timestamp": ts,
        "balls": [
            {"id": i + 1, "x": c["x"], "y": c["y"], "r": c["r"]}
            for i, c in enumerate(circles)
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return str(path)

def write_overlay(path, circles, stable, saved_path=None):
    Path(os.path.dirname(path) or ".").mkdir(parents=True, exist_ok=True)
    data = {
        "ball_count": len(circles),
        "stable_table": stable,
        "latest_saved_layout": saved_path,
        "balls": [
            {"id": i + 1, "x": c["x"], "y": c["y"], "r": c["r"]}
            for i, c in enumerate(circles)
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--rtsp")
    parser.add_argument("--rtsp-from-config", action="store_true")
    parser.add_argument("--calibration", default="output/table_calibration.json")
    parser.add_argument("--runtime", default="config/runtime_config.json")
    args = parser.parse_args()

    runtime = get_runtime(args.runtime)
    calib = load_json(args.calibration)
    M = np.array(calib["homography_matrix"], dtype=np.float32)
    warp_w = int(calib["warp_width"])
    warp_h = int(calib["warp_height"])

    cap, source_name = get_source(args, runtime)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open source: {source_name}")
    print(f"[INFO] Opened source: {source_name}")

    detect_cfg = runtime["detection"]
    stable_cfg = runtime["stability"]
    out_cfg = runtime["output"]

    prev_sig = None
    stable_since = None
    last_saved_sig = None

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[WARN] Could not read frame.")
            break

        warped = cv2.warpPerspective(frame, M, (warp_w, warp_h))
        circles = detect_circles(warped, detect_cfg)
        draw_circles(warped, circles)

        sig = circles_signature(circles)
        move = movement_amount(sig, prev_sig) if prev_sig is not None else 9999
        moving = move > stable_cfg.get("movement_px_threshold", 6)

        if moving:
            stable_since = None
        else:
            if stable_since is None:
                stable_since = time.time()

        stable = False
        saved_path = None
        if stable_since is not None:
            stable = (time.time() - stable_since) >= stable_cfg.get("stable_seconds_required", 1.5)

        if stable and sig and sig != last_saved_sig and out_cfg.get("save_layouts_when_stable", True):
            saved_path = save_layout(out_cfg["layout_dir"], circles)
            last_saved_sig = list(sig)
            print(f"[OK] Saved stable layout: {saved_path}")

        write_overlay(out_cfg["overlay_json"], circles, stable, saved_path)

        debug = warped.copy()
        status = f"balls={len(circles)} move={move:.1f} stable={stable}"
        cv2.putText(debug, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 220, 50), 2)

        cv2.imshow("Warped Ball Detection", debug)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            break

        prev_sig = sig

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
