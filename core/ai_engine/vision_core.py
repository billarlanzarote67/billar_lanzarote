
import cv2, json, os, sys, time, numpy as np
from pathlib import Path
ROOT = r"C:\AI\BillarLanzarote"
sys.path.append(os.path.join(ROOT, "core"))
from common import atomic_write_json, append_jsonl, utc_now, init_db

DB_PATH = os.path.join(ROOT, "database", "sqlite", "billar_lanzarote.sqlite")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def detect_ball_candidates(frame, cfg):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=18, param1=80, param2=16,
                               minRadius=cfg.get("ball_min_radius_px", 6),
                               maxRadius=cfg.get("ball_max_radius_px", 18))
    balls = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for idx, (x, y, r) in enumerate(circles):
            balls.append({"id": f"b{idx+1:02d}", "type": "object_ball", "x_px": int(x), "y_px": int(y), "r_px": int(r), "conf": 0.65})
    return balls

def estimate_motion(prev_gray, gray):
    if prev_gray is None: return 0, None
    diff = cv2.absdiff(prev_gray, gray)
    _, th = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
    motion = int(np.sum(th))
    return motion, th

def hardness_from_state(balls, motion):
    if len(balls) < 2:
        return {"score_0_100": 0, "label": "", "band": "", "confidence_0_1": 0.0}
    pts = np.array([(b["x_px"], b["y_px"]) for b in balls], dtype=np.float32)
    dsum = 0.0; pairs = 0
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            dsum += np.linalg.norm(pts[i]-pts[j]); pairs += 1
    avg_dist = dsum / pairs if pairs else 0.0
    cluster_factor = max(0.0, 1.0 - min(avg_dist / 220.0, 1.0))
    motion_factor = min(motion / 150000.0, 1.0)
    density_factor = min(len(balls) / 12.0, 1.0)
    score = int(max(0, min(100, round(25 + 40*cluster_factor + 20*motion_factor + 15*density_factor))))
    labels = [(10, "CHUPADO"), (22, "REGALADO"), (38, "FACILITO"), (58, "TIENE TRAMPA"), (78, "JODIDO"), (101, "MISIÓN IMPOSIBLE")]
    label = "FACILITO"
    for lim, lab in labels:
        if score <= lim:
            label = lab; break
    conf = round(min(0.9, 0.35 + (len(balls)/20.0) + (0.15 if score > 20 else 0.0)), 2)
    return {"score_0_100": score, "label": label, "band": label, "confidence_0_1": conf}

def run_table(table_cfg_path, show_debug=True):
    cfg = load_json(table_cfg_path)
    if not cfg.get("enabled", True):
        print(f'{cfg["table_id"]} disabled in config, exiting.'); return
    table_id = cfg["table_id"]; rtsp_url = cfg["rtsp_url"]
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"[{table_id}] Failed to open stream: {rtsp_url}"); return
    Path(cfg["events_dir"]).mkdir(parents=True, exist_ok=True)
    Path(cfg["clips_dir"]).mkdir(parents=True, exist_ok=True)
    Path(os.path.dirname(cfg["state_file"])).mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    prev_gray = None; shot_active = False; still_frames = 0; frame_seq = 0; last_hardness = None
    print(f"[{table_id}] Vision core started on {rtsp_url}")
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5); continue
        frame_seq += 1
        display = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion, motion_mask = estimate_motion(prev_gray, gray)
        balls = detect_ball_candidates(frame, cfg)
        for b in balls:
            cv2.circle(display, (b["x_px"], b["y_px"]), b["r_px"], (0,255,0), 2)
            cv2.putText(display, b["id"], (b["x_px"]+5, b["y_px"]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)
        start_thr = cfg.get("motion_start_threshold", 45000)
        stop_thr = cfg.get("motion_stop_threshold", 12000)
        still_needed = cfg.get("stillness_frames_needed", 12)
        if motion < stop_thr: still_frames += 1
        else: still_frames = 0
        if (not shot_active) and motion > start_thr:
            shot_active = True
            append_jsonl(os.path.join(cfg["events_dir"], time.strftime("%Y-%m-%d") + ".jsonl"),
                         {"ts_utc": utc_now(), "table_id": table_id, "source": "visioncore", "type": "shot_started", "payload": {"motion": motion}})
        if shot_active and still_frames >= still_needed:
            shot_active = False
            last_hardness = hardness_from_state(balls, motion)
            append_jsonl(os.path.join(cfg["events_dir"], time.strftime("%Y-%m-%d") + ".jsonl"),
                         {"ts_utc": utc_now(), "table_id": table_id, "source": "visioncore", "type": "shot_ended", "payload": {"motion": motion, "hardness": last_hardness}})
            atomic_write_json(cfg["hardness_file"], {
                "schema": "bl.shot_hardness.v1",
                "ts_utc": utc_now(),
                "table_id": table_id,
                "hardness": last_hardness,
                "public_overlay": {
                    "visible": last_hardness["confidence_0_1"] >= cfg.get("public_min_confidence", 0.72),
                    "text": f'Dificultad: {last_hardness["label"]}' if last_hardness["confidence_0_1"] >= cfg.get("public_min_confidence", 0.72) else ""
                }
            })
        atomic_write_json(cfg["state_file"], {
            "schema": "bl.table_state.v1",
            "ts_utc": utc_now(),
            "table_id": table_id,
            "frame_seq": frame_seq,
            "balls": balls,
            "quality": {"motion_score": motion, "ball_candidate_count": len(balls), "state_confidence": round(min(0.9, 0.2 + len(balls)/15.0), 2)}
        })
        atomic_write_json(cfg["ai_state_file"], {
            "schema": "bl.ai_state.v1",
            "ts_utc": utc_now(),
            "table_id": table_id,
            "status": "ok",
            "active_processing": True,
            "shot_active": shot_active,
            "vision_fps_target": cfg.get("fps_target", 10),
            "last_hardness": last_hardness,
        })
        cv2.putText(display, f"{table_id} motion:{motion}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        if last_hardness:
            cv2.putText(display, f'Dificultad: {last_hardness["label"]} ({last_hardness["confidence_0_1"]:.2f})', (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
        if show_debug:
            cv2.imshow(f"{table_id} original", display)
            if motion_mask is not None: cv2.imshow(f"{table_id} motion_mask", motion_mask)
            if (cv2.waitKey(1) & 0xFF) == 27: break
        prev_gray = gray
    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    config_arg = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "config", "mesa1_config.json")
    run_table(config_arg, show_debug=True)
