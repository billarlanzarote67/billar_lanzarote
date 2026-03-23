
import os, re, sys, json, sqlite3, uuid, requests
from bs4 import BeautifulSoup
from common_import import load_config, init_schema, utc_now, ensure_dir, save_text, extract_numeric_id_from_url, insert_raw_import, slug, find_or_create_player, log_event_if_possible

SCHEMA_PATH = r"C:\AI\BillarLanzarote\sql\cuescore_importer_schema.sql"

def try_playwright_screenshot(url, screenshot_path):
    try:
        from playwright.sync_api import sync_playwright
        ensure_dir(os.path.dirname(screenshot_path))
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 2400})
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.screenshot(path=screenshot_path, full_page=True)
            html = page.content()
            browser.close()
            return html, True
    except Exception:
        return None, False

def parse_finished_match(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidate_names = []
    for ln in lines:
        if 2 <= len(ln) <= 60 and not re.search(r'https?://|©|Cookie policy|Terms of service', ln, re.I):
            digit_ratio = sum(ch.isdigit() for ch in ln) / max(1, len(ln))
            if digit_ratio < 0.1 and ln not in candidate_names:
                candidate_names.append(ln)
        if len(candidate_names) >= 12:
            break
    player1 = candidate_names[0] if len(candidate_names) > 0 else None
    player2 = candidate_names[1] if len(candidate_names) > 1 else None
    score1 = score2 = None
    nums = [int(x) for x in re.findall(r'\b\d+\b', text)]
    for i in range(len(nums)-1):
        if 0 <= nums[i] <= 25 and 0 <= nums[i+1] <= 25:
            score1, score2 = nums[i], nums[i+1]
            break
    winner_name = None
    if player1 and player2 and score1 is not None and score2 is not None:
        if score1 > score2: winner_name = player1
        elif score2 > score1: winner_name = player2
    return {"player1_name": player1, "player2_name": player2, "score1": score1, "score2": score2, "winner_name": winner_name}

def upsert_match_result(db_path, cuescore_match_id, parsed, raw_html_path, screenshot_path, source_url):
    p1_id = find_or_create_player(db_path, parsed["player1_name"]) if parsed["player1_name"] else None
    p2_id = find_or_create_player(db_path, parsed["player2_name"]) if parsed["player2_name"] else None
    winner_id = p1_id if parsed["winner_name"] == parsed["player1_name"] else p2_id if parsed["winner_name"] == parsed["player2_name"] else None
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO match_results(
      match_id, cuescore_match_id, player1_id, player2_id, player1_name, player2_name,
      score1, score2, winner_player_id, winner_name, played_ts_utc, source_type, raw_html_path, screenshot_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), cuescore_match_id, p1_id, p2_id, parsed["player1_name"], parsed["player2_name"], parsed["score1"], parsed["score2"], winner_id, parsed["winner_name"], utc_now(), "scrape", raw_html_path, screenshot_path))
    con.commit(); con.close()
    log_event_if_possible(db_path, "cuescore_match_imported", {"source_url": source_url, **parsed})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_finished_match.py <cuescore_match_or_page_url>")
        sys.exit(1)
    url = sys.argv[1]
    cfg = load_config()
    db_path = cfg["db_path"]
    init_schema(db_path, SCHEMA_PATH)
    match_id = extract_numeric_id_from_url(url)
    stamp = utc_now().replace(":", "-")
    html_path = os.path.join(cfg["match_import_root"], f"{slug(match_id or 'match')}_{stamp}.html")
    screenshot_path = os.path.join(cfg["screenshots_root"], "matches", f"{slug(match_id or 'match')}_{stamp}.png")
    html = None
    screenshot_ok = False
    if cfg.get("save_screenshot_when_possible", True):
        html, screenshot_ok = try_playwright_screenshot(url, screenshot_path)
    if html is None:
        r = requests.get(url, timeout=cfg.get("requests_timeout_seconds", 20))
        r.raise_for_status()
        html = r.text
    if cfg.get("save_html_every_time", True):
        save_text(html_path, html)
    parsed = parse_finished_match(html)
    upsert_match_result(db_path, match_id, parsed, html_path, screenshot_path if screenshot_ok else None, url)
    insert_raw_import(db_path, "match", url, cuescore_match_id=match_id, raw_html_path=html_path, screenshot_path=screenshot_path if screenshot_ok else None, raw_json=parsed, parse_status="parsed")
    print(json.dumps(parsed, indent=2, ensure_ascii=False))
