import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

POINTS = []

def mouse_callback(event, x, y, flags, param):
    global POINTS
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(POINTS) < 4:
            POINTS.append((x, y))
            print(f"[DEBUG] Point {len(POINTS)} added: {(x, y)}", flush=True)

def draw_points(frame):
    labels = ["TL", "TR", "BR", "BL"]
    for i, p in enumerate(POINTS):
        cv2.circle(frame, p, 8, (0, 255, 255), -1)
        cv2.putText(frame, labels[i], (p[0] + 10, p[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

def get_source(args):
    if args.image:
        img = cv2.imread(args.image)
        if img is None:
            raise RuntimeError(f"Could not read image: {args.image}")
        return "image", img
    if args.rtsp:
        cap = cv2.VideoCapture(args.rtsp)
        if not cap.isOpened():
            raise RuntimeError("Could not open RTSP stream")
        return "video", cap
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {args.camera}")
    return "video", cap

def compute_warp(points, width, height):
    src = np.array(points, dtype=np.float32)
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    return M

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Path to still image")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--rtsp", help="RTSP stream URL")
    parser.add_argument("--config", default="config/table_config.json")
    parser.add_argument("--output", default="output/table_calibration.json")
    args = parser.parse_args()

    print("[INFO] Starting calibration...", flush=True)
    print(f"[INFO] Args: {args}", flush=True)

    config = {}
    if os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"[INFO] Loaded config: {args.config}", flush=True)
    else:
        print(f"[WARN] Config not found: {args.config}", flush=True)

    warp_w = config.get("output_warp_size", {}).get("width", 1400)
    warp_h = config.get("output_warp_size", {}).get("height", 700)
    print(f"[INFO] Warp size: {warp_w}x{warp_h}", flush=True)

    source_type, src = get_source(args)
    print(f"[INFO] Source type: {source_type}", flush=True)

    cv2.namedWindow("Calibration")
    cv2.setMouseCallback("Calibration", mouse_callback)

    frozen_frame = None

    while True:
        if source_type == "image":
            frame = src.copy()
        else:
            ok, frame = src.read()
            if not ok:
                raise RuntimeError("Could not read from video source")
            if frozen_frame is not None:
                frame = frozen_frame.copy()

        display = frame.copy()
        draw_points(display)

        help_text = "Click TL, TR, BR, BL | f=freeze | r=reset | s=save | q=quit"
        cv2.putText(display, help_text, (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 220, 50), 2)

        if len(POINTS) == 4:
            M = compute_warp(POINTS, warp_w, warp_h)
            warped = cv2.warpPerspective(frame, M, (warp_w, warp_h))
            small = cv2.resize(warped, (700, 350))
            cv2.imshow("Warp Preview", small)

        cv2.imshow("Calibration", display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("q"):
            print("[INFO] Quit requested.", flush=True)
            break
        elif key == ord("r"):
            POINTS.clear()
            print("[INFO] Points reset.", flush=True)
        elif key == ord("f") and source_type == "video":
            frozen_frame = None if frozen_frame is not None else frame.copy()
            print("[INFO] Freeze toggled.", flush=True)
        elif key == ord("s"):
            if len(POINTS) != 4:
                print("[WARN] Need exactly 4 points before saving.", flush=True)
                continue

            M = compute_warp(POINTS, warp_w, warp_h)
            out = {
                "source_points": POINTS,
                "warp_width": warp_w,
                "warp_height": warp_h,
                "homography_matrix": np.asarray(M).tolist(),
                "config_used": config,
                "point_order": ["top_left", "top_right", "bottom_right", "bottom_left"]
            }
            Path(os.path.dirname(args.output) or ".").mkdir(parents=True, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            print(f"[OK] Saved calibration to {args.output}", flush=True)

    if source_type == "video":
        src.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        raise
