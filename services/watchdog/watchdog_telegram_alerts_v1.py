
from __future__ import annotations
import json, sys, time
from pathlib import Path
from telegram_helpers import (
    read_json, write_json, append_log, send_telegram, active_table_name,
    build_start_msg, build_stop_msg, build_error_msg, build_recovery_msg
)

def load_cfg(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def summarize_alerts(alerts):
    out = []
    for a in alerts or []:
        out.append((a.get("code") or "SYSTEM_ERROR", a.get("message") or "Unknown system issue"))
    return out

def send_safe(cfg, text, log_path: Path):
    token = cfg.get("bot_token")
    if not token or token == "8677774799:AAHfU74_aBUbvWqPUuz4ErhCJg4NCl6Vdk0":
        append_log(log_path, "ERROR token missing, alert not sent")
        return False
    try:
        send_telegram(token, int(cfg["chat_id"]), text)
        append_log(log_path, f"SENT {text.splitlines()[0]}")
        return True
    except Exception as e:
        append_log(log_path, f"ERROR send failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python watchdog_telegram_alerts_v1.py <config_path>")
        sys.exit(1)
    cfg_path = Path(sys.argv[1])
    cfg = load_cfg(cfg_path)
    log_path = Path(cfg["alert_log_path"])
    state_cache_path = Path(cfg["state_cache_path"])
    stop_flag = Path(cfg["restart_stream_flag_path"]).parent.parent / "telegram" / "STOP_WATCHDOG_TELEGRAM_ALERTS_v1.flag"

    cache = read_json(state_cache_path) or {"last_status": None, "last_alert_codes": [], "startup_sent": False, "shutdown_sent": False}

    current_match = read_json(Path(cfg["active_table_source_path"]))
    table_name = active_table_name(current_match)
    if cfg.get("startup_alert") and not cache.get("startup_sent"):
        send_safe(cfg, build_start_msg(table_name), log_path)
        cache["startup_sent"] = True
        cache["shutdown_sent"] = False
        write_json(state_cache_path, cache)

    append_log(log_path, "watchdog telegram loop started")

    while True:
        if stop_flag.exists():
            if cfg.get("shutdown_alert") and not cache.get("shutdown_sent"):
                current_match = read_json(Path(cfg["active_table_source_path"]))
                table_name = active_table_name(current_match)
                send_safe(cfg, build_stop_msg(table_name), log_path)
                cache["shutdown_sent"] = True
                write_json(state_cache_path, cache)
            stop_flag.unlink(missing_ok=True)
            append_log(log_path, "stop flag detected")
            break

        current = read_json(Path(cfg["health_input_path"])) or read_json(Path(cfg["system_health_input_path"])) or {}
        status = (((current.get("system") or {}).get("status")) or "unknown")
        alert_pairs = summarize_alerts(current.get("alerts") or [])
        alert_codes = [x[0] for x in alert_pairs]

        if status in {"error", "warning"} and alert_codes != cache.get("last_alert_codes", []):
            msgs = []
            for code, msg in alert_pairs:
                msgs.append(build_error_msg(code, msg))
                if cfg.get("auto_restart"):
                    if code in {"MEDIAMTX_DOWN", "RTSP_ROUTE_FAIL"}:
                        p = Path(cfg["restart_stream_flag_path"]); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("restart_stream", encoding="utf-8")
                    elif code in {"STALE_FILES", "SYSTEM_ERROR"}:
                        p = Path(cfg["restart_ai_flag_path"]); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("restart_ai", encoding="utf-8")
            send_safe(cfg, "\n\n--------------------------------\n\n".join(msgs), log_path)

        if status == "ok" and cache.get("last_status") in {"error", "warning"}:
            send_safe(cfg, build_recovery_msg("System recovered"), log_path)

        cache["last_status"] = status
        cache["last_alert_codes"] = alert_codes
        write_json(state_cache_path, cache)
        time.sleep(int(cfg.get("poll_interval_seconds", 15)))

if __name__ == "__main__":
    main()
