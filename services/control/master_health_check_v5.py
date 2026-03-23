
from __future__ import annotations
import json, sys, time, subprocess
from pathlib import Path
from control_helpers_v5 import read_json, write_json, append_log, file_fresh, tcp_open, rtsp_probe, cleanup_old_logs, utc_now_iso

def load_cfg(cfg_path: Path):
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return cfg

def gather_health(cfg: dict):
    root = Path(cfg["root_path"])
    state = root / "state"
    logs = root / "logs" / "system"
    log_path = logs / "master_control_v5.log"
    services = {
        "mediamtx_8554": tcp_open("127.0.0.1", 8554, 2.0),
        "dashboard_8787": tcp_open("127.0.0.1", cfg.get("dashboard_port", 8787), 1.0),
        "obs_websocket_4455": tcp_open("127.0.0.1", 4455, 1.0),
    }
    critical = {}
    missing = []
    stale = []
    for rel in cfg.get("critical_files", []):
        p = root / rel
        exists = p.exists()
        fresh = file_fresh(p, 180) if exists else False
        critical[rel] = {"exists": exists, "fresh": fresh}
        if not exists:
            missing.append(rel)
        elif not fresh:
            stale.append(rel)

    sys_status = "ok"
    alerts = []
    if missing:
        sys_status = "error"
        alerts.append({"level":"error","code":"MISSING_FILES","message":"Missing critical files: " + ", ".join(missing),"time":utc_now_iso()})
    if stale and sys_status != "error":
        sys_status = "warning"
        alerts.append({"level":"warning","code":"STALE_FILES","message":"Stale critical files: " + ", ".join(stale),"time":utc_now_iso()})
    if not services["mediamtx_8554"]:
        sys_status = "error"
        alerts.append({"level":"error","code":"MEDIAMTX_DOWN","message":"MediaMTX not reachable on 127.0.0.1:8554","time":utc_now_iso()})

    # RTSP local route checks
    mesa_routes = {}
    for mesa in ("mesa1", "mesa2"):
        ok, reason = rtsp_probe(f"rtsp://127.0.0.1:8554/{mesa}")
        mesa_routes[mesa] = {"ok": ok, "reason": reason}
        if not ok:
            sys_status = "warning" if sys_status == "ok" else sys_status
            alerts.append({"level":"warning","code":"RTSP_ROUTE_FAIL","message":f"{mesa} route probe failed: {reason}","time":utc_now_iso()})

    removed = cleanup_old_logs(root / "logs", int(cfg.get("log_retention_days", 30)))
    if removed:
        append_log(log_path, "INFO", f"Log cleanup removed {removed} old files")

    payload = {
        "schema_version": "1.0.0",
        "system": {
            "name": "Billar Lanzarote",
            "version": "master_control_v5",
            "status": sys_status,
            "last_update": utc_now_iso()
        },
        "master_control": {
            "mediamtx_routes": mesa_routes,
            "services": services,
            "critical_files": critical
        },
        "alerts": alerts
    }
    return payload

def main():
    if len(sys.argv) < 2:
        print("Usage: python master_health_check_v5.py <config>")
        sys.exit(1)
    cfg_path = Path(sys.argv[1])
    cfg = load_cfg(cfg_path)
    root = Path(cfg["root_path"])
    out_path = root / "state" / "master_control_health_v5.json"
    log_path = root / "logs" / "system" / "master_control_v5.log"

    payload = gather_health(cfg)
    write_json(out_path, payload)
    append_log(log_path, "INFO", f"Health check wrote {out_path}")
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
