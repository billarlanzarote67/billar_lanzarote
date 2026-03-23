
from __future__ import annotations
import json, os, socket, subprocess, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)

def append_log(path: Path, level: str, msg: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] [{level}] {msg}\n")

def file_fresh(path: Path, seconds: int):
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age <= seconds

def tcp_open(host: str, port: int, timeout: float = 2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def rtsp_probe(rtsp_url: str, vlc_exe: str | None = None):
    # Lightweight TCP probe against RTSP host:port. Does not authenticate full stream.
    # Good enough for fast health checks.
    try:
        if "rtsp://" not in rtsp_url:
            return False, "invalid_rtsp_url"
        rest = rtsp_url.split("://", 1)[1]
        if "@" in rest:
            rest = rest.split("@", 1)[1]
        host_port = rest.split("/", 1)[0]
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            host, port = host_port, 554
        ok = tcp_open(host, port, timeout=2.0)
        return ok, f"tcp_{'ok' if ok else 'fail'}_{host}_{port}"
    except Exception as e:
        return False, f"probe_error:{e}"

def cleanup_old_logs(log_root: Path, days: int):
    cutoff = time.time() - days * 86400
    removed = 0
    if not log_root.exists():
        return removed
    for p in log_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".log", ".txt", ".jsonl"}:
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except Exception:
                pass
    return removed

def run_cmd(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=False)
