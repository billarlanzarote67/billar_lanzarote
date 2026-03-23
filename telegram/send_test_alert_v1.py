
from __future__ import annotations
import json, sys
from pathlib import Path
from telegram_helpers import send_telegram, append_log, bilingual

def main():
    if len(sys.argv) < 2:
        print("Usage: python send_test_alert_v1.py <config_path>")
        sys.exit(1)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    token = cfg.get("bot_token")
    if not token or token == "PASTE_CURRENT_OR_NEW_TOKEN_HERE":
        print("ERROR: bot_token missing")
        sys.exit(2)
    text = bilingual("🧪 Test alert from Billar Lanzarote", "🧪 Alerta de prueba de Billar Lanzarote")
    print(send_telegram(token, int(cfg["chat_id"]), text))
    append_log(Path(cfg["alert_log_path"]), "SENT test alert")

if __name__ == "__main__":
    main()
