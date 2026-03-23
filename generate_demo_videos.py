
import os
import cv2
import numpy as np

ROOT = r"C:\AI\BillarLanzarote_DEMO"
VIDEOS = os.path.join(ROOT, "videos")
os.makedirs(VIDEOS, exist_ok=True)

def make_video(path, seed):
    width, height = 1280, 720
    fps = 25
    seconds = 30
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))
    rng = np.random.default_rng(seed)

    ball_positions = []
    colors = [
        (255,255,255), (0,255,255), (255,0,0), (0,0,255), (0,255,0),
        (255,0,255), (255,255,0), (200,200,200), (50,150,255)
    ]
    for i in range(9):
        x = int(rng.integers(240, width-240))
        y = int(rng.integers(180, height-180))
        vx = int(rng.integers(-4, 5))
        vy = int(rng.integers(-4, 5))
        ball_positions.append([x, y, vx, vy, colors[i % len(colors)]])

    for frame in range(fps * seconds):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (28, 90, 35)
        cv2.rectangle(img, (80, 60), (width-80, height-60), (20,60,20), thickness=35)
        cv2.rectangle(img, (120, 100), (width-120, height-100), (40,120,50), thickness=-1)
        pockets = [(120,100),(width//2,100),(width-120,100),(120,height-100),(width//2,height-100),(width-120,height-100)]
        for p in pockets:
            cv2.circle(img, p, 22, (10,10,10), -1)

        for b in ball_positions:
            b[0] += b[2]
            b[1] += b[3]
            if b[0] < 150 or b[0] > width-150:
                b[2] *= -1
            if b[1] < 130 or b[1] > height-130:
                b[3] *= -1
            cv2.circle(img, (b[0], b[1]), 14, b[4], -1)
            cv2.circle(img, (b[0], b[1]), 14, (20,20,20), 2)

        cv2.putText(img, "BILLAR LANZAROTE DEMO", (140, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(img, os.path.basename(path), (980, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,200,180), 2, cv2.LINE_AA)

        out.write(img)
    out.release()

make_video(os.path.join(VIDEOS, "mesa1_demo.mp4"), 1)
make_video(os.path.join(VIDEOS, "mesa2_demo.mp4"), 2)
print("Demo videos created.")
