from __future__ import annotations
import atexit, json, socket, subprocess, sys, time
from datetime import datetime
from pathlib import Path
try:
    import websocket
except Exception:
    websocket = None

from watchdog_telegram_sender_v1 import send_telegram_from_config, append_log

def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def log(cfg, line):
    append_log(cfg["watchdog_log"], line)
    print(f"{now_iso()} {line}")

def process_running(name):
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return name.lower() in (out.stdout or "").lower()

def file_fresh(path, stale):
    p = Path(path)
    return p.exists() and (time.time() - p.stat().st_mtime <= stale)

def tcp_open(host, port, timeout):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def rtsp_ok(rtsp_url, timeout):
    try:
        stripped = rtsp_url.replace("rtsp://", "", 1)
        host_port, path = stripped.split("/", 1)
        host, port = host_port.split(":")
        port = int(port)
        req = (
            f"OPTIONS rtsp://{host}:{port}/{path} RTSP/1.0\r\n"
            "CSeq: 1\r\n"
            "User-Agent: BillarWatchdog/1.0\r\n\r\n"
        ).encode("utf-8")
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(req)
            resp = s.recv(1024).decode("utf-8", errors="ignore")
            return "RTSP/" in resp and ("200" in resp or "401" in resp or "454" in resp)
    except Exception:
        return False

def ws_ok(host, port, timeout):
    if not tcp_open(host, port, timeout):
        return False
    if websocket is None:
        return True
    try:
        ws = websocket.create_connection(f"ws://{host}:{port}", timeout=timeout)
        ws.close()
        return True
    except Exception:
        return True

def run_bat(path):
    return subprocess.run(["cmd", "/c", path], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=180)

def touch_flag(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(now_iso(), encoding="utf-8")

def should_alert(state, key, cooldown):
    last = float(state.get(key, 0))
    return (time.time() - last) >= cooldown

def mark_alert(state, key):
    state[key] = time.time()

def send_alert(cfg, state, key, text):
    if not should_alert(state, key, cfg["cooldown_seconds"]):
        return
    ok, resp = send_telegram_from_config(cfg["telegram_config"], text)
    log(cfg, f"[ALERT] {text} | ok={ok} | resp={resp}")
    mark_alert(state, key)

def send_recovery(cfg, state, key, text):
    rec_key = f"recovered::{key}"
    if state.get(rec_key):
        return
    ok, resp = send_telegram_from_config(cfg["telegram_config"], text)
    log(cfg, f"[RECOVERY] {text} | ok={ok} | resp={resp}")
    state[rec_key] = True

def clear_recovery(state, key):
    state.pop(f"recovered::{key}", None)

def startup_alert(cfg, state):
    if state.get("startup_alert_sent"):
        return
    ok, resp = send_telegram_from_config(cfg["telegram_config"], "Billar Lanzarote watchdog started.")
    log(cfg, f"[STARTUP] ok={ok} | resp={resp}")
    state["startup_alert_sent"] = True

def shutdown_alert(cfg):
    ok, resp = send_telegram_from_config(cfg["telegram_config"], "Billar Lanzarote watchdog stopped.")
    log(cfg, f"[SHUTDOWN] ok={ok} | resp={resp}")

def snapshot(cfg):
    hf = cfg["health_files"]
    return {
        "timestamp": now_iso(),
        "obs_process_ok": process_running("obs64.exe"),
        "obs_websocket_ok": ws_ok(cfg["obs_websocket_host"], int(cfg["obs_websocket_port"]), int(cfg["websocket_timeout_seconds"])),
        "mediamtx_process_ok": process_running("mediamtx.exe"),
        "rtsp_mesa1_ok": rtsp_ok(cfg["rtsp_routes"]["mesa1"], int(cfg["rtsp_timeout_seconds"])),
        "rtsp_mesa2_ok": rtsp_ok(cfg["rtsp_routes"]["mesa2"], int(cfg["rtsp_timeout_seconds"])),
        "ai_state_fresh": file_fresh(hf["ai_state"], int(cfg["json_stale_seconds"])),
        "system_health_fresh": file_fresh(hf["system_health"], int(cfg["json_stale_seconds"])),
        "master_control_fresh": file_fresh(hf["master_control"], int(cfg["json_stale_seconds"])),
        "current_match_fresh": file_fresh(hf["current_match"], int(cfg["json_stale_seconds"]))
    }

def evaluate(cfg, state, snap, started_at):
    if (time.time() - started_at) < int(cfg["startup_grace_seconds"]):
        return
    if not snap["obs_process_ok"] or not snap["obs_websocket_ok"]:
        send_alert(cfg, state, "obs", "OBS is down or websocket is unreachable.")
    else:
        clear_recovery(state, "obs")
        send_recovery(cfg, state, "obs", "OBS recovered.")
    if not snap["mediamtx_process_ok"]:
        send_alert(cfg, state, "mediamtx", "MediaMTX process is not running.")
    else:
        clear_recovery(state, "mediamtx")
        send_recovery(cfg, state, "mediamtx", "MediaMTX recovered.")
    if not snap["rtsp_mesa1_ok"]:
        send_alert(cfg, state, "rtsp1", "RTSP route mesa1 is unavailable.")
    else:
        clear_recovery(state, "rtsp1")
        send_recovery(cfg, state, "rtsp1", "RTSP route mesa1 recovered.")
    if not snap["rtsp_mesa2_ok"]:
        send_alert(cfg, state, "rtsp2", "RTSP route mesa2 is unavailable.")
    else:
        clear_recovery(state, "rtsp2")
        send_recovery(cfg, state, "rtsp2", "RTSP route mesa2 recovered.")
    if not snap["ai_state_fresh"]:
        send_alert(cfg, state, "ai", "AI state JSON is stale.")
    else:
        clear_recovery(state, "ai")
        send_recovery(cfg, state, "ai", "AI state freshness recovered.")

def main():
    cfg = load_json(r"C:\AI\BillarLanzarote\config\watchdog_config_v1.json")
    if not cfg:
        print("Missing watchdog config")
        sys.exit(1)
    Path(cfg["watchdog_log"]).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["status_output"]).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["watchdog_state"]).parent.mkdir(parents=True, exist_ok=True)
    state = load_json(cfg["watchdog_state"])
    started_at = time.time()
    atexit.register(shutdown_alert, cfg)
    log(cfg, "[BOOT] Watchdog starting")
    startup_alert(cfg, state)
    save_json(cfg["watchdog_state"], state)
    while True:
        try:
            snap = snapshot(cfg)
            save_json(cfg["status_output"], snap)
            state = load_json(cfg["watchdog_state"])
            evaluate(cfg, state, snap, started_at)
            save_json(cfg["watchdog_state"], state)
            time.sleep(int(cfg["poll_interval_seconds"]))
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(cfg, f"[ERROR] {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
