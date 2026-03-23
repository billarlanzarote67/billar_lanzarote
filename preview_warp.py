import argparse
import json
import os

import cv2
import numpy as np

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Image path")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--rtsp", help="RTSP stream URL")
    parser.add_argument("--calibration", default="output/table_calibration.json")
    args = parser.parse_args()

    print(f"[INFO] Loading calibration: {args.calibration}", flush=True)
    if not os.path.exists(args.calibration):
        raise RuntimeError(f"Calibration file not found: {args.calibration}")

    with open(args.calibration, "r", encoding="utf-8") as f:
        calib = json.load(f)

    M = np.array(calib["homography_matrix"], dtype=np.float32)
    warp_w = int(calib["warp_width"])
    warp_h = int(calib["warp_height"])
    print(f"[INFO] Warp size: {warp_w}x{warp_h}", flush=True)

    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise RuntimeError(f"Could not read image: {args.image}")
        warped = cv2.warpPerspective(frame, M, (warp_w, warp_h))
        cv2.imshow("Original", frame)
        cv2.imshow("Warped", warped)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    cap = cv2.VideoCapture(args.rtsp if args.rtsp else args.camera)
    if not cap.isOpened():
        raise RuntimeError("Could not open video source")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[WARN] Could not read frame.", flush=True)
            break
        warped = cv2.warpPerspective(frame, M, (warp_w, warp_h))
        cv2.imshow("Original", frame)
        cv2.imshow("Warped", warped)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            print("[INFO] Quit requested.", flush=True)
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
