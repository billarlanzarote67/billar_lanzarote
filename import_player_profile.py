import json
import os
import re
import sqlite3
import sys
import time
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DB_PATH = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
RAW_DIR = r"C:\AI\BillarLanzarote\data\raw_cuescore\profiles"
LOG_DIR = r"C:\AI\BillarLanzarote\logs\import"
TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_dirs() -> None:
    Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)
    Path(RAW_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def log_line(filename: str, message: str) -> None:
    ensure_dirs()
    path = os.path.join(LOG_DIR, filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{utc_now()}] {message}\n")


def save_raw_html(cuescore_player_id: str, html: str) -> str:
    ensure_dirs()
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    safe_id = cuescore_player_id or "unknown"
    path = os.path.join(RAW_DIR, f"profile_{safe_id}_{stamp}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def connect_db() -> sqlite3.Connection:
    ensure_dirs()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        created_ts_utc TEXT NOT NULL,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_cuescore_map (
        player_id TEXT PRIMARY KEY,
        cuescore_player_id TEXT,
        cuescore_profile_url TEXT,
        cuescore_display_name TEXT,
        last_verified_ts_utc TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_profile_stats (
        player_id TEXT PRIMARY KEY,
        matches_played REAL,
        wins REAL,
        losses REAL,
        win_rate REAL,
        innings_average REAL,
        runouts REAL,
        lag_wins REAL,
        frame_win_average REAL,
        points REAL,
        last_import_ts_utc TEXT,
        raw_json TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_media (
        player_id TEXT PRIMARY KEY,
        cuescore_player_id TEXT,
        photo_url TEXT,
        local_photo_path TEXT,
        local_fallback_photo_path TEXT,
        photo_source TEXT,
        last_photo_sync_ts_utc TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS importer_run_log (
        run_id TEXT PRIMARY KEY,
        ts_utc TEXT NOT NULL,
        source_type TEXT NOT NULL,
        source_url TEXT,
        status TEXT NOT NULL,
        details_json TEXT
    )
    """)

    con.commit()
    con.close()


def log_run(source_url: str, status: str, details: dict) -> None:
    con = connect_db()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO importer_run_log (
        run_id, ts_utc, source_type, source_url, status, details_json
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        utc_now(),
        "player_profile",
        source_url,
        status,
        json.dumps(details, ensure_ascii=False),
    ))
    con.commit()
    con.close()


def get_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def extract_player_id_from_url(url: str) -> str | None:
    m = re.search(r"/player/[^/]+/(\d+)", url)
    return m.group(1) if m else None


def extract_name_from_url(url: str) -> str:
    m = re.search(r"/player/([^/]+)/\d+", url)
    if not m:
        return "Unknown Player"
    return m.group(1).replace("+", " ").strip()


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_title(soup: BeautifulSoup) -> str:
    title = soup.title.string if soup.title and soup.title.string else ""
    return normalize_whitespace(title)


def is_error_page(title: str, text: str) -> bool:
    bad_patterns = [
        "404",
        "page not found",
        "not found",
        "error",
    ]
    blob = f"{title} {text[:500]}".lower()
    return any(pat in blob for pat in bad_patterns)


def first_non_empty(*values: str | None) -> str | None:
    for v in values:
        if v is not None:
            v = normalize_whitespace(v)
            if v:
                return v
    return None


def try_meta_content(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop})
    if tag and tag.get("content"):
        return normalize_whitespace(tag["content"])
    return None


def get_best_display_name(url: str, soup: BeautifulSoup, page_text: str) -> str:
    url_name = extract_name_from_url(url)

    og_title = try_meta_content(soup, "og:title")
    if og_title:
        # Strip common site suffixes if present
        og_title = re.sub(r"\s*[-|–]\s*CueScore.*$", "", og_title, flags=re.I).strip()

    h1 = soup.find("h1")
    h1_text = normalize_whitespace(h1.get_text(" ", strip=True)) if h1 else None

    # Best guess in order
    name = first_non_empty(h1_text, og_title, url_name)

    if not name:
        return "Unknown Player"

    # Protect against bad titles
    bad_names = {
        "page not found",
        "cuescore - 404 not found",
        "404 not found",
        "page not found - cuescore.com",
    }
    if name.lower() in bad_names:
        return "Unknown Player"

    return name


def search_number(page_text: str, label_patterns: list[str]) -> float | None:
    """
    Robust stat extractor.
    Looks for patterns like:
    Matches 12
    Matches: 12
    Won 7
    Win % 58
    """
    text = page_text

    for label in label_patterns:
        # Label followed by optional punctuation then a number
        pattern = rf"{label}\s*[:\-]?\s*([0-9]+(?:[.,][0-9]+)?)"
        m = re.search(pattern, text, flags=re.I)
        if m:
            raw = m.group(1).replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                return None

    return None


def extract_photo_url(soup: BeautifulSoup) -> str | None:
    og_image = try_meta_content(soup, "og:image")
    if og_image and "cuescore" in og_image.lower():
        return og_image

    for img in soup.find_all("img", src=True):
        src = img.get("src", "").strip()
        alt = (img.get("alt") or "").lower()
        if not src:
            continue
        if any(x in alt for x in ["player", "profile", "avatar"]):
            if src.startswith("http"):
                return src
            return "https://cuescore.com" + src

    return None


def get_or_create_player(display_name: str) -> str:
    con = connect_db()
    cur = con.cursor()

    cur.execute(
        "SELECT player_id FROM players WHERE lower(display_name) = lower(?)",
        (display_name,)
    )
    row = cur.fetchone()
    if row:
        con.close()
        return row["player_id"]

    player_id = str(uuid.uuid4())
    cur.execute("""
    INSERT INTO players (player_id, display_name, created_ts_utc, notes)
    VALUES (?, ?, ?, ?)
    """, (
        player_id,
        display_name,
        utc_now(),
        "Auto-created by import_player_profile.py"
    ))
    con.commit()
    con.close()
    return player_id


def upsert_profile(
    player_id: str,
    cuescore_player_id: str | None,
    profile_url: str,
    display_name: str,
    stats: dict,
    photo_url: str | None,
) -> None:
    con = connect_db()
    cur = con.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO player_cuescore_map (
        player_id, cuescore_player_id, cuescore_profile_url,
        cuescore_display_name, last_verified_ts_utc
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        player_id,
        cuescore_player_id,
        profile_url,
        display_name,
        utc_now(),
    ))

    cur.execute("""
    INSERT OR REPLACE INTO player_profile_stats (
        player_id, matches_played, wins, losses, win_rate,
        innings_average, runouts, lag_wins, frame_win_average,
        points, last_import_ts_utc, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        player_id,
        stats.get("matches_played"),
        stats.get("wins"),
        stats.get("losses"),
        stats.get("win_rate"),
        stats.get("innings_average"),
        stats.get("runouts"),
        stats.get("lag_wins"),
        stats.get("frame_win_average"),
        stats.get("points"),
        utc_now(),
        json.dumps(stats, ensure_ascii=False),
    ))

    if photo_url:
        cur.execute("""
        INSERT OR REPLACE INTO player_media (
            player_id, cuescore_player_id, photo_url, local_photo_path,
            local_fallback_photo_path, photo_source, last_photo_sync_ts_utc, notes
        ) VALUES (?, ?, ?, COALESCE(
            (SELECT local_photo_path FROM player_media WHERE player_id = ?), NULL
        ), COALESCE(
            (SELECT local_fallback_photo_path FROM player_media WHERE player_id = ?), NULL
        ), ?, ?, ?)
        """, (
            player_id,
            cuescore_player_id,
            photo_url,
            player_id,
            player_id,
            "cuescore_remote",
            utc_now(),
            "Photo URL captured from CueScore profile page",
        ))

    con.commit()
    con.close()


def parse_profile_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    page_text = normalize_whitespace(soup.get_text(" ", strip=True))
    title = parse_title(soup)

    if is_error_page(title, page_text):
        raise ValueError(f"Error page detected: {title or 'Unknown title'}")

    display_name = get_best_display_name(url, soup, page_text)
    cuescore_player_id = extract_player_id_from_url(url)
    photo_url = extract_photo_url(soup)

    stats = {
        "matches_played": search_number(page_text, [r"matches", r"played"]),
        "wins": search_number(page_text, [r"wins?", r"won"]),
        "losses": search_number(page_text, [r"losses?", r"lost"]),
        "win_rate": search_number(page_text, [r"win\s*%", r"win percentage"]),
        "innings_average": search_number(page_text, [r"innings average", r"avg innings"]),
        "runouts": search_number(page_text, [r"runouts?", r"run outs?"]),
        "lag_wins": search_number(page_text, [r"lag wins?", r"lags won"]),
        "frame_win_average": search_number(page_text, [r"frame win average", r"avg frame"]),
        "points": search_number(page_text, [r"points?"]),
    }

    return {
        "display_name": display_name,
        "cuescore_player_id": cuescore_player_id,
        "photo_url": photo_url,
        "stats": stats,
        "title": title,
    }


def main() -> int:
    ensure_dirs()
    init_db()

    if len(sys.argv) < 2:
        print("Usage: import_player_profile.py <CueScore player profile URL>")
        return 1

    url = sys.argv[1].strip()

    if "/player/" not in url:
        print("ERROR: URL must be a CueScore player profile URL.")
        return 1

    try:
        html = get_html(url)
        result = parse_profile_page(html, url)
        raw_path = save_raw_html(result["cuescore_player_id"] or "unknown", html)

        player_id = get_or_create_player(result["display_name"])
        upsert_profile(
            player_id=player_id,
            cuescore_player_id=result["cuescore_player_id"],
            profile_url=url,
            display_name=result["display_name"],
            stats=result["stats"],
            photo_url=result["photo_url"],
        )

        payload = {
            "status": "ok",
            "player_id": player_id,
            "display_name": result["display_name"],
            "cuescore_player_id": result["cuescore_player_id"],
            "photo_url": result["photo_url"],
            "stats": result["stats"],
            "raw_html": raw_path,
        }

        log_run(url, "ok", payload)
        log_line("player_profile_import.log", f"OK {result['display_name']} :: {url}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    except Exception as e:
        err = {
            "status": "fail",
            "url": url,
            "error": str(e),
        }
        log_run(url, "fail", err)
        log_line("player_profile_import.log", f"FAIL {url} :: {e}")
        print(json.dumps(err, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
