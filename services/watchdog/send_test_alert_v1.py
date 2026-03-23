from __future__ import annotations

import json
import sys
from pathlib import Path

from telegram_helpers import send_telegram, append_log, bilingual


def main():
    if len(sys.argv) < 2:
        print("Usage: python send_test_alert_v1.py <config_path>")
        sys.exit(1)

    config_path = Path(sys.argv[1])

    if not config_path.exists():
        print(f"ERROR: config file not found: {config_path}")
        sys.exit(2)

    cfg = json.loads(config_path.read_text(encoding="utf-8"))

    token = str(cfg.get("bot_token", "")).strip()
    chat_id = str(cfg.get("chat_id", "")).strip()

    if not token:
        print("ERROR: bot_token missing")
        sys.exit(3)

    if not chat_id:
        print("ERROR: chat_id missing")
        sys.exit(4)

    text = bilingual(
        "✅ Test alert from Billar Lanzarote",
        "📌 Alerta de prueba de Billar Lanzarote"
    )

    try:
        result = send_telegram(token, int(chat_id), text)
        print(result)

        log_path = Path(cfg.get("alert_log_path", r"C:\AI\BillarLanzarote\logs\telegram\telegram_alerts.log"))
        append_log(log_path, "[SENT] Test alert")
        print("SUCCESS: Telegram test alert sent")
    except Exception as e:
        print(f"ERROR: Telegram send failed: {e}")
        sys.exit(5)


if __name__ == "__main__":
    main()
