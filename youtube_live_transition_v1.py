from __future__ import annotations
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("SKIPPED: usage youtube_live_transition_v1.py <config> <target>")
        sys.exit(0)

    cfg_path = Path(sys.argv[1])
    target = sys.argv[2].strip().lower()

    if not cfg_path.exists():
        print("SKIPPED: youtube config missing")
        sys.exit(0)

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    if not cfg.get("enabled", False):
        print("SKIPPED: youtube hook disabled")
        sys.exit(0)

    cred = Path(cfg.get("credentials_json_path", ""))
    token = Path(cfg.get("token_json_path", ""))
    if not cred.exists() or not token.exists():
        print("SKIPPED: youtube credentials/token missing")
        sys.exit(0)

    # Safe stub: credential files exist, but this pack does not force OAuth flow.
    # User can drop in a richer implementation later without changing the bot wiring.
    print(f"SKIPPED: youtube transition hook ready but not armed for target={target}")
    sys.exit(0)

if __name__ == "__main__":
    main()
