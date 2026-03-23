
from __future__ import annotations
import json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

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

def append_log(path: Path, message: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{utc_now_iso()}] {message}\n")

def send_telegram(token: str, chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def active_table_name(current_match: dict | None):
    if not isinstance(current_match, dict):
        return None
    for key in ("table_id", "table", "table_name", "active_table"):
        v = current_match.get(key)
        if v:
            return str(v)
    return None

def bilingual(en: str, es: str):
    return f"{en}\n{es}"

def build_start_msg(table_name: str | None):
    extra_en = f"Active table: {table_name}" if table_name else "Active table: unknown"
    extra_es = f"Mesa activa: {table_name}" if table_name else "Mesa activa: desconocida"
    return bilingual("✅ System started", "✅ Sistema iniciado") + f"\n\n{extra_en}\n{extra_es}"

def build_stop_msg(table_name: str | None):
    extra_en = f"Active table: {table_name}" if table_name else "Active table: unknown"
    extra_es = f"Mesa activa: {table_name}" if table_name else "Mesa activa: desconocida"
    return bilingual("🛑 System stopped", "🛑 Sistema detenido") + f"\n\n{extra_en}\n{extra_es}"

def build_error_msg(code: str, message: str):
    es = {
        "MEDIAMTX_DOWN": "MediaMTX caído",
        "MISSING_FILES": "Faltan archivos críticos",
        "STALE_FILES": "Archivos críticos desactualizados",
        "RTSP_ROUTE_FAIL": "Fallo de ruta RTSP",
        "SYSTEM_ERROR": "Error del sistema",
    }.get(code, "Error del sistema")
    return bilingual(f"⚠️ {message}", f"⚠️ {es}")

def build_recovery_msg(message: str):
    return bilingual(f"✅ {message}", "✅ Sistema recuperado")
