from __future__ import annotations
import json
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def append_log(path: str | Path, line: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{now_iso()} {line}\n")

def send_telegram(token: str, chat_id: str | int, text: str) -> tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": str(chat_id), "text": text}).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=data, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return True, body
    except Exception as e:
        return False, str(e)

def send_telegram_from_config(telegram_config_path: str | Path, text: str) -> tuple[bool, str]:
    cfg = load_json(telegram_config_path)
    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()
    if not token:
        return False, "bot_token missing"
    if not chat_id:
        return False, "chat_id missing"
    return send_telegram(token, chat_id, text)
