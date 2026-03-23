from playwright.sync_api import sync_playwright
import os
import json
import time
import sqlite3
import re
import unicodedata
from datetime import datetime
import requests

ROOT = r"C:\AI\BillarLanzarote"
CFG_PATH = os.path.join(ROOT, "config", "live_tables_watcher_final_capture_config_v1_3.json")
STATE_DIR = os.path.join(ROOT, "state")
DATA_DIR = os.path.join(ROOT, "data")
COMPLETED_DIR = os.path.join(DATA_DIR, "completed_matches")
DB_PATH = os.path.join(DATA_DIR, "billar_lanzarote.sqlite3")
LOG_PATH = os.path.join(ROOT, "logs", "live_tables_watcher_final_capture_v1_3.log")
FINAL_STATE_PATH = os.path.join(STATE_DIR, "final_capture_state_v1_3.json")
RAW_NAME_DEBUG_DIR = os.path.join(ROOT, "logs", "name_parse_debug")

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COMPLETED_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(RAW_NAME_DEBUG_DIR, exist_ok=True)

STAT_LABELS = [
    "Frames won",
    "Average frametime",
    "Win %",
    "Runouts",
    "Break and wins",
    "Frames stolen",
    "Timeouts",
]

JUNK_NAME_PHRASES = {
    "breaking", "runouts", "runout", "rack", "undo", "timeout", "timeouts",
    "end match", "pause", "resume", "ball in hand", "innings", "average",
    "high run", "total average", "total", "break no-score", "no-score"
}

JUNK_EXACT = {
    "mesa 1", "mesa 2", "table 1", "table 2", "bola 10", "10-ball", "9-ball",
    "8-ball", "challengematch", "match statistics", "statistics"
}


def load_cfg():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


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
    if not token or not chat_id or "PUT_" in token:
        log("Telegram skipped: token/chat_id not fully configured.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as e:
        log(f"Telegram error: {e}")


def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=20, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=20000;")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS live_table_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_key TEXT,
        table_name TEXT,
        status TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        score TEXT,
        race_to INTEGER,
        race_text_es TEXT,
        winner TEXT,
        loser TEXT,
        source_url TEXT,
        raw_player_a TEXT,
        raw_player_b TEXT,
        created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS latest_table_state (
        table_key TEXT PRIMARY KEY,
        table_name TEXT,
        status TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        score TEXT,
        race_to INTEGER,
        race_text_es TEXT,
        winner TEXT,
        loser TEXT,
        source_url TEXT,
        raw_player_a TEXT,
        raw_player_b TEXT,
        updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches_final (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_signature TEXT UNIQUE,
        table_key TEXT,
        table_name TEXT,
        player_a TEXT,
        player_b TEXT,
        score_a INTEGER,
        score_b INTEGER,
        score TEXT,
        race_to INTEGER,
        winner TEXT,
        loser TEXT,
        source_url TEXT,
        raw_player_a TEXT,
        raw_player_b TEXT,
        avg_frametime_a TEXT,
        avg_frametime_b TEXT,
        win_pct_a REAL,
        win_pct_b REAL,
        runouts_a INTEGER,
        runouts_b INTEGER,
        break_and_wins_a INTEGER,
        break_and_wins_b INTEGER,
        frames_stolen_a INTEGER,
        frames_stolen_b INTEGER,
        timeouts_a INTEGER,
        timeouts_b INTEGER,
        raw_stats_text TEXT,
        raw_json_path TEXT,
        captured_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_profiles (
        player_name TEXT PRIMARY KEY,
        matches_played INTEGER DEFAULT 0,
        matches_won INTEGER DEFAULT 0,
        matches_lost INTEGER DEFAULT 0,
        frames_won INTEGER DEFAULT 0,
        frames_lost INTEGER DEFAULT 0,
        win_pct REAL DEFAULT 0,
        updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_match_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_signature TEXT,
        player_name TEXT,
        opponent_name TEXT,
        table_key TEXT,
        did_win INTEGER,
        frames_won INTEGER,
        frames_lost INTEGER,
        winner TEXT,
        avg_frametime TEXT,
        runouts INTEGER,
        break_and_wins INTEGER,
        frames_stolen INTEGER,
        timeouts INTEGER,
        created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    return conn


def safe_text(page, selector):
    try:
        return page.locator(selector).first.inner_text().strip()
    except Exception:
        return ""


def get_body_text(page):
    try:
        return page.locator("body").first.inner_text()
    except Exception:
        return ""


def parse_int(value):
    try:
        return int(str(value).strip())
    except Exception:
        return None


def parse_float_percent(value):
    if value is None:
        return None
    txt = str(value).replace("%", "").strip()
    txt = txt.replace(",", ".")
    try:
        return float(txt)
    except Exception:
        return None


def strip_flags_and_symbols(text):
    if not text:
        return text
    cleaned = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("S"):
            continue
        cleaned.append(ch)
    return "".join(cleaned)


def extract_player_name(block_text):
    if not block_text:
        return None
    block_text = strip_flags_and_symbols(block_text)
    lines = []
    for line in block_text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        low = line.lower()
        if low in JUNK_EXACT:
            continue
        if low.startswith("race to") or low.startswith("mesa ") or low.startswith("table "):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if re.fullmatch(r"[\W_]+", line):
            continue
        if any(phrase in low for phrase in JUNK_NAME_PHRASES):
            continue
        if len(line) < 2:
            continue
        lines.append(line)
    if not lines:
        return None
    lines = lines[:2]
    name = re.sub(r"\s+", " ", " ".join(lines)).strip(" -|")
    low_name = name.lower()
    if low_name in JUNK_EXACT:
        return None
    if any(phrase == low_name for phrase in JUNK_NAME_PHRASES):
        return None
    return name or None


def write_name_debug(st):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(RAW_NAME_DEBUG_DIR, f"{st['table_key']}_{ts}.json")
    save_json(path, {
        "table_key": st.get("table_key"),
        "table_name": st.get("table_name"),
        "raw_player_a": st.get("raw_player_a"),
        "raw_player_b": st.get("raw_player_b"),
        "parsed_player_a": st.get("player_a"),
        "parsed_player_b": st.get("player_b"),
        "source_url": st.get("source_url"),
        "timestamp": datetime.now().isoformat(),
    })


def looks_like_idle_junk(player_a, player_b, score_a, score_b):
    vals = [player_a or "", player_b or ""]
    if score_a is not None or score_b is not None:
        return False
    if not any(vals):
        return True
    joined = " ".join(vals).lower().strip()
    bad_bits = ["break", "breaking", "runout", "runouts", "no-score", "ball in hand", "innings", "average"]
    return any(bit in joined for bit in bad_bits)


def parse_final_stats_from_body(body_text):
    result = {
        "avg_frametime_a": None,
        "avg_frametime_b": None,
        "win_pct_a": None,
        "win_pct_b": None,
        "runouts_a": None,
        "runouts_b": None,
        "break_and_wins_a": None,
        "break_and_wins_b": None,
        "frames_stolen_a": None,
        "frames_stolen_b": None,
        "timeouts_a": None,
        "timeouts_b": None,
        "raw_stats_text": None,
    }

    if not body_text:
        return result

    text = strip_flags_and_symbols(body_text)
    if "Match statistics" not in text and "Frames won" not in text:
        return result

    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    start_idx = None
    for i, ln in enumerate(lines):
        if ln.lower() == "match statistics":
            start_idx = i
            break
    if start_idx is None:
        for i, ln in enumerate(lines):
            if ln.lower() == "frames won":
                start_idx = max(0, i - 3)
                break
    if start_idx is None:
        return result

    stats_lines = lines[start_idx:start_idx + 30]
    result["raw_stats_text"] = "\n".join(stats_lines)

    # Expected alternating pattern around labels:
    # left_value / label / right_value
    def find_triplet(label):
        for i, ln in enumerate(stats_lines):
            if ln.lower() == label.lower():
                left = stats_lines[i - 1] if i - 1 >= 0 else None
                right = stats_lines[i + 1] if i + 1 < len(stats_lines) else None
                return left, right
        return None, None

    left, right = find_triplet("Average frametime")
    result["avg_frametime_a"] = left
    result["avg_frametime_b"] = right

    left, right = find_triplet("Win %")
    result["win_pct_a"] = parse_float_percent(left)
    result["win_pct_b"] = parse_float_percent(right)

    left, right = find_triplet("Runouts")
    result["runouts_a"] = parse_int(left)
    result["runouts_b"] = parse_int(right)

    left, right = find_triplet("Break and wins")
    result["break_and_wins_a"] = parse_int(left)
    result["break_and_wins_b"] = parse_int(right)

    left, right = find_triplet("Frames stolen")
    result["frames_stolen_a"] = parse_int(left)
    result["frames_stolen_b"] = parse_int(right)

    left, right = find_triplet("Timeouts")
    result["timeouts_a"] = parse_int(left)
    result["timeouts_b"] = parse_int(right)

    return result


def parse_table(page, table_key, meta):
    raw_player_a = safe_text(page, ".contentPlayerA")
    raw_player_b = safe_text(page, ".contentPlayerB")
    player_a = extract_player_name(raw_player_a)
    player_b = extract_player_name(raw_player_b)

    score_a = parse_int(safe_text(page, ".score.scoreA.playerA") or safe_text(page, ".scoreA"))
    score_b = parse_int(safe_text(page, ".score.scoreB.playerB") or safe_text(page, ".scoreB"))
    race_to = parse_int(safe_text(page, ".raceTo"))

    source_url = meta.get("primary_url", "")
    status = "idle"
    winner = None
    loser = None

    if looks_like_idle_junk(player_a, player_b, score_a, score_b):
        player_a = None
        player_b = None
        score_a = None
        score_b = None
        race_to = None

    if player_a or player_b or score_a is not None or score_b is not None:
        status = "live"

    if race_to is not None and score_a is not None and score_b is not None:
        if score_a >= race_to:
            winner = player_a
            loser = player_b
        elif score_b >= race_to:
            winner = player_b
            loser = player_a

    state = {
        "table_key": table_key,
        "table_name": meta.get("name", table_key),
        "status": status,
        "player_a": player_a,
        "player_b": player_b,
        "raw_player_a": raw_player_a,
        "raw_player_b": raw_player_b,
        "score_a": score_a,
        "score_b": score_b,
        "score": f"{score_a}-{score_b}" if score_a is not None and score_b is not None else None,
        "race_to": race_to,
        "race_text_es": f"Carrera a {race_to}" if race_to else "Carrera desconocida",
        "winner": winner,
        "loser": loser,
        "source_url": source_url,
        "last_update": datetime.now().isoformat(),
    }
    return state


def maybe_reload_or_fallback(page, meta):
    fallback = (meta.get("fallback_url") or "").strip()
    if fallback:
        try:
            page.goto(fallback, wait_until="domcontentloaded")
            time.sleep(3)
            return True, fallback
        except Exception:
            return False, None
    return False, None


def write_live_state(conn, st):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO live_table_events (
            table_key, table_name, status, player_a, player_b, score_a, score_b,
            score, race_to, race_text_es, winner, loser, source_url, raw_player_a, raw_player_b
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        st.get("table_key"), st.get("table_name"), st.get("status"),
        st.get("player_a"), st.get("player_b"), st.get("score_a"), st.get("score_b"),
        st.get("score"), st.get("race_to"), st.get("race_text_es"),
        st.get("winner"), st.get("loser"), st.get("source_url"),
        st.get("raw_player_a"), st.get("raw_player_b"),
    ))
    cur.execute("""
        INSERT INTO latest_table_state (
            table_key, table_name, status, player_a, player_b, score_a, score_b,
            score, race_to, race_text_es, winner, loser, source_url, raw_player_a, raw_player_b
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(table_key) DO UPDATE SET
            table_name=excluded.table_name,
            status=excluded.status,
            player_a=excluded.player_a,
            player_b=excluded.player_b,
            score_a=excluded.score_a,
            score_b=excluded.score_b,
            score=excluded.score,
            race_to=excluded.race_to,
            race_text_es=excluded.race_text_es,
            winner=excluded.winner,
            loser=excluded.loser,
            source_url=excluded.source_url,
            raw_player_a=excluded.raw_player_a,
            raw_player_b=excluded.raw_player_b,
            updated_ts_utc=CURRENT_TIMESTAMP
    """, (
        st.get("table_key"), st.get("table_name"), st.get("status"),
        st.get("player_a"), st.get("player_b"), st.get("score_a"), st.get("score_b"),
        st.get("score"), st.get("race_to"), st.get("race_text_es"),
        st.get("winner"), st.get("loser"), st.get("source_url"),
        st.get("raw_player_a"), st.get("raw_player_b"),
    ))
    conn.commit()


def make_signature(st):
    return "|".join([
        st.get("table_key") or "",
        (st.get("player_a") or "").lower(),
        (st.get("player_b") or "").lower(),
        str(st.get("score_a")),
        str(st.get("score_b")),
        str(st.get("race_to")),
        (st.get("winner") or "").lower(),
    ])


def final_already_saved(conn, signature):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM matches_final WHERE match_signature=? LIMIT 1", (signature,))
    return cur.fetchone() is not None


def upsert_player_profile(conn, player_name, won, frames_won, frames_lost):
    if not player_name:
        return
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO player_profiles (
            player_name, matches_played, matches_won, matches_lost, frames_won, frames_lost, win_pct, updated_ts_utc
        ) VALUES (?, 1, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        ON CONFLICT(player_name) DO UPDATE SET
            matches_played = matches_played + 1,
            matches_won = matches_won + excluded.matches_won,
            matches_lost = matches_lost + excluded.matches_lost,
            frames_won = frames_won + excluded.frames_won,
            frames_lost = frames_lost + excluded.frames_lost,
            updated_ts_utc = CURRENT_TIMESTAMP
    """, (
        player_name, 1 if won else 0, 0 if won else 1, frames_won or 0, frames_lost or 0
    ))
    cur.execute("""
        UPDATE player_profiles
        SET win_pct = CASE
            WHEN matches_played > 0 THEN ROUND(matches_won * 100.0 / matches_played, 2)
            ELSE 0
        END,
        updated_ts_utc = CURRENT_TIMESTAMP
        WHERE player_name = ?
    """, (player_name,))
    conn.commit()


def save_final_match(conn, st, stats):
    signature = make_signature(st)
    if final_already_saved(conn, signature):
        return False, signature, None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_a = re.sub(r"[^A-Za-z0-9._ -]+", "", (st.get("player_a") or "unknown")).replace(" ", "_")
    safe_b = re.sub(r"[^A-Za-z0-9._ -]+", "", (st.get("player_b") or "unknown")).replace(" ", "_")
    json_path = os.path.join(COMPLETED_DIR, f"{st['table_key']}_{ts}_{safe_a}_vs_{safe_b}.json")

    payload = dict(st)
    payload.update(stats)
    payload["match_signature"] = signature
    payload["captured_ts"] = datetime.now().isoformat()
    save_json(json_path, payload)

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matches_final (
            match_signature, table_key, table_name, player_a, player_b,
            score_a, score_b, score, race_to, winner, loser, source_url,
            raw_player_a, raw_player_b, avg_frametime_a, avg_frametime_b,
            win_pct_a, win_pct_b, runouts_a, runouts_b, break_and_wins_a, break_and_wins_b,
            frames_stolen_a, frames_stolen_b, timeouts_a, timeouts_b, raw_stats_text, raw_json_path
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        signature, st.get("table_key"), st.get("table_name"), st.get("player_a"), st.get("player_b"),
        st.get("score_a"), st.get("score_b"), st.get("score"), st.get("race_to"), st.get("winner"), st.get("loser"),
        st.get("source_url"), st.get("raw_player_a"), st.get("raw_player_b"),
        stats.get("avg_frametime_a"), stats.get("avg_frametime_b"),
        stats.get("win_pct_a"), stats.get("win_pct_b"),
        stats.get("runouts_a"), stats.get("runouts_b"),
        stats.get("break_and_wins_a"), stats.get("break_and_wins_b"),
        stats.get("frames_stolen_a"), stats.get("frames_stolen_b"),
        stats.get("timeouts_a"), stats.get("timeouts_b"),
        stats.get("raw_stats_text"), json_path
    ))

    cur.executemany("""
        INSERT INTO player_match_history (
            match_signature, player_name, opponent_name, table_key, did_win, frames_won, frames_lost, winner,
            avg_frametime, runouts, break_and_wins, frames_stolen, timeouts
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (
            signature, st.get("player_a"), st.get("player_b"), st.get("table_key"),
            1 if (st.get("winner") or "").lower() == (st.get("player_a") or "").lower() else 0,
            st.get("score_a") or 0, st.get("score_b") or 0, st.get("winner"),
            stats.get("avg_frametime_a"), stats.get("runouts_a"), stats.get("break_and_wins_a"),
            stats.get("frames_stolen_a"), stats.get("timeouts_a")
        ),
        (
            signature, st.get("player_b"), st.get("player_a"), st.get("table_key"),
            1 if (st.get("winner") or "").lower() == (st.get("player_b") or "").lower() else 0,
            st.get("score_b") or 0, st.get("score_a") or 0, st.get("winner"),
            stats.get("avg_frametime_b"), stats.get("runouts_b"), stats.get("break_and_wins_b"),
            stats.get("frames_stolen_b"), stats.get("timeouts_b")
        ),
    ])
    conn.commit()

    upsert_player_profile(conn, st.get("player_a"),
                          (st.get("winner") or "").lower() == (st.get("player_a") or "").lower(),
                          st.get("score_a") or 0, st.get("score_b") or 0)
    upsert_player_profile(conn, st.get("player_b"),
                          (st.get("winner") or "").lower() == (st.get("player_b") or "").lower(),
                          st.get("score_b") or 0, st.get("score_a") or 0)

    return True, signature, json_path


def main():
    cfg = load_cfg()
    poll = max(1, int(cfg.get("poll_seconds", 2)))
    wait_sec = max(1, int(cfg.get("page_wait_seconds", 4)))
    stable_needed = max(1, int(cfg.get("stable_final_polls", 2)))
    last_digest = {}
    stable_final = load_json(FINAL_STATE_PATH, {"stable": {}})
    conn = init_db()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=bool(cfg.get("headless", False)))
        pages = {}

        for table_key, meta in cfg["tables"].items():
            page = browser.new_page()
            page.goto(meta["primary_url"], wait_until="domcontentloaded")
            time.sleep(wait_sec)
            pages[table_key] = page
            log(f"{table_key}: opened {meta['primary_url']}")

        while True:
            try:
                merged = {"last_update": datetime.now().isoformat(), "tables": {}}
                for table_key, meta in cfg["tables"].items():
                    page = pages[table_key]
                    try:
                        state = parse_table(page, table_key, meta)
                        if state["status"] == "idle" and meta.get("fallback_url"):
                            ok, fallback_used = maybe_reload_or_fallback(page, meta)
                            if ok:
                                state = parse_table(page, table_key, meta)
                                if fallback_used:
                                    state["source_url"] = fallback_used

                        merged["tables"][table_key] = state
                        save_json(os.path.join(STATE_DIR, f"{table_key}_match.json"), state)
                        write_name_debug(state)

                        digest = json.dumps(state, sort_keys=True, ensure_ascii=False)
                        if last_digest.get(table_key) != digest:
                            write_live_state(conn, state)
                            last_digest[table_key] = digest
                            log(f"{table_key}: state changed -> {state.get('player_a') or '—'} {state.get('score') or 'no-score'} {state.get('player_b') or '—'}")

                        signature = make_signature(state)
                        current = stable_final["stable"].setdefault(table_key, {"signature": None, "count": 0})

                        if state.get("winner") and state.get("race_to") is not None:
                            if current["signature"] == signature:
                                current["count"] += 1
                            else:
                                current["signature"] = signature
                                current["count"] = 1

                            body_text = get_body_text(page)
                            stats = parse_final_stats_from_body(body_text)

                            log(f"{table_key}: final candidate {current['count']}/{stable_needed} -> {signature}")

                            if current["count"] >= stable_needed:
                                saved, _, json_path = save_final_match(conn, state, stats)
                                if saved:
                                    msg = (
                                        f"🏆 Final {state.get('table_name')}\n"
                                        f"{state.get('player_a') or '—'} {state.get('score') or ''} {state.get('player_b') or '—'}\n"
                                        f"Ganador: {state.get('winner') or '—'}"
                                    )
                                    send_telegram(cfg, msg)
                                    log(f"{table_key}: FINAL SAVED -> {json_path}")
                                current["count"] = 0
                        else:
                            current["signature"] = None
                            current["count"] = 0

                    except Exception as e:
                        log(f"{table_key}: error {e}")

                save_json(os.path.join(STATE_DIR, "live_tables.json"), merged)
                save_json(FINAL_STATE_PATH, stable_final)
                time.sleep(poll)
            except Exception as e:
                log(f"main loop error: {e}")
                time.sleep(poll)


if __name__ == "__main__":
    main()
