import argparse
import json
from pathlib import Path

import cv2
import numpy as np

def latest_layout(layout_dir):
    files = sorted(Path(layout_dir).glob("layout_*.json"))
    return files[-1] if files else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", default="config/runtime_config.json")
    parser.add_argument("--output", default="output/projector_layout.png")
    args = parser.parse_args()

    with open(args.runtime, "r", encoding="utf-8") as f:
        runtime = json.load(f)

    overlay_json = Path(runtime["output"]["overlay_json"])
    layout_dir = Path(runtime["output"]["layout_dir"])
    latest = latest_layout(layout_dir)
    if latest is None:
        raise RuntimeError("No saved layout found yet.")

    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)

    canvas = np.zeros((700, 1400, 3), dtype=np.uint8)
    canvas[:] = (155, 155, 155)

    # simple rail border
    cv2.rectangle(canvas, (20, 20), (1380, 680), (35, 35, 35), 20)

    for ball in data["balls"]:
        x, y, r = int(ball["x"]), int(ball["y"]), int(ball["r"])
        cv2.circle(canvas, (x, y), max(10, r), (230, 230, 230), -1)
        cv2.circle(canvas, (x, y), max(10, r), (0, 0, 0), 2)
        cv2.putText(canvas, str(ball["id"]), (x - 8, y + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), canvas)
    print(f"[OK] Projector layout image written to {out}")
    print(f"[INFO] Based on latest saved layout: {latest}")

if __name__ == "__main__":
    main()
