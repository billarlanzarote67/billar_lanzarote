
from playwright.sync_api import sync_playwright
import os, json, time
from datetime import datetime
import requests

ROOT = r"C:\AI\BillarLanzarote"
CFG_PATH = os.path.join(ROOT, "config", "live_tables_watcher_config_v1.json")
STATE_DIR = os.path.join(ROOT, "state")
LOG_PATH = os.path.join(ROOT, "logs", "live_tables_watcher_v1.log")

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def load_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def send_telegram(cfg, message):
    tg = cfg.get("telegram", {})
    if not tg.get("enabled"):
        return
    token = tg.get("bot_token", "").strip()
    chat_id = tg.get("chat_id", "").strip()
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as e:
        log(f"Telegram error: {e}")

def parse_table(page, table_key, meta):
    # Try primary page first, then fallback if needed
    status = "idle"
    player_a = None
    player_b = None
    score_a = None
    score_b = None
    race_to = None
    winner = None
    source_used = meta.get("primary_url", "")

    def safe_text(locator):
        try:
            return locator.first.inner_text().strip()
        except Exception:
            return ""

    # Generic selectors that work on scoreboard pages that mirror the challenge structure
    player_a = safe_text(page.locator(".contentPlayerA")).split("\n")[0].strip() if safe_text(page.locator(".contentPlayerA")) else ""
    player_b = safe_text(page.locator(".contentPlayerB")).split("\n")[0].strip() if safe_text(page.locator(".contentPlayerB")) else ""
    score_a_txt = safe_text(page.locator(".score.scoreA.playerA")) or safe_text(page.locator(".scoreA"))
    score_b_txt = safe_text(page.locator(".score.scoreB.playerB")) or safe_text(page.locator(".scoreB"))
    race_txt = safe_text(page.locator(".raceTo"))

    try:
        score_a = int(score_a_txt)
        score_b = int(score_b_txt)
    except Exception:
        score_a = None
        score_b = None

    try:
        race_to = int(race_txt)
    except Exception:
        race_to = None

    if player_a or player_b or score_a is not None or score_b is not None:
        status = "live"

    if race_to is not None and score_a is not None and score_b is not None:
        if score_a >= race_to:
            winner = player_a
        elif score_b >= race_to:
            winner = player_b

    return {
        "table_key": table_key,
        "table_name": meta.get("name", table_key),
        "status": status,
        "player_a": player_a or None,
        "player_b": player_b or None,
        "score_a": score_a,
        "score_b": score_b,
        "score": f"{score_a}-{score_b}" if score_a is not None and score_b is not None else None,
        "race_to": race_to,
        "race_text_es": f"Carrera a {race_to}" if race_to else "Carrera desconocida",
        "winner": winner,
        "source_url": source_used,
        "last_update": datetime.now().isoformat()
    }

def maybe_reload_or_fallback(page, meta):
    # if page load is weird, try fallback URL if configured
    fallback = (meta.get("fallback_url") or "").strip()
    if fallback:
        try:
            page.goto(fallback, wait_until="domcontentloaded")
            time.sleep(3)
            return True
        except Exception:
            return False
    return False

def main():
    cfg = load_cfg()
    poll = max(1, int(cfg.get("poll_seconds", 2)))
    last_scores = {"mesa1": None, "mesa2": None}
    last_status = {"mesa1": None, "mesa2": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        pages = {}

        for table_key, meta in cfg["tables"].items():
            page = browser.new_page()
            page.goto(meta["primary_url"], wait_until="domcontentloaded")
            time.sleep(4)
            pages[table_key] = page
            log(f"{table_key}: opened {meta['primary_url']}")

        while True:
            merged = {"last_update": datetime.now().isoformat(), "tables": {}}

            for table_key, meta in cfg["tables"].items():
                page = pages[table_key]
                try:
                    state = parse_table(page, table_key, meta)

                    # fallback if nothing found
                    if state["status"] == "idle" and meta.get("fallback_url"):
                        log(f"{table_key}: primary looked idle, trying fallback")
                        if maybe_reload_or_fallback(page, meta):
                            state = parse_table(page, table_key, meta)

                    merged["tables"][table_key] = state
                    save_json(os.path.join(STATE_DIR, f"{table_key}_match.json"), state)

                    prev_score = last_scores.get(table_key)
                    prev_status = last_status.get(table_key)

                    if state["status"] != prev_status:
                        if state["status"] == "live":
                            send_telegram(cfg, f"🎱 {state['table_name']} en juego\n{state.get('player_a') or '—'} vs {state.get('player_b') or '—'}\n{state.get('race_text_es') or ''}")
                        elif state["status"] == "idle" and prev_status == "live":
                            send_telegram(cfg, f"⏹ {state['table_name']} sin partida")
                        last_status[table_key] = state["status"]

                    if state.get("score") and state.get("score") != prev_score:
                        send_every = cfg.get("telegram", {}).get("send_every_score_change", True)
                        send_final_only = cfg.get("telegram", {}).get("send_final_only", False)
                        if send_every and not send_final_only:
                            send_telegram(cfg, f"📣 {state['table_name']}\n{state.get('player_a') or '—'} {state.get('score') or ''} {state.get('player_b') or '—'}\n{state.get('race_text_es') or ''}")
                        if state.get("winner"):
                            send_telegram(cfg, f"🏆 Final {state['table_name']}\n{state.get('winner')} gana\n{state.get('player_a') or '—'} {state.get('score') or ''} {state.get('player_b') or '—'}")
                        last_scores[table_key] = state.get("score")

                except Exception as e:
                    log(f"{table_key}: error {e}")

            save_json(os.path.join(STATE_DIR, "live_tables.json"), merged)
            time.sleep(poll)

if __name__ == "__main__":
    main()
