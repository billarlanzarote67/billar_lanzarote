import argparse
import json
import os
import re
import sqlite3
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DB = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
RAW_DIR = r"C:\AI\BillarLanzarote\data\raw_cuescore\tournaments"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())

def pid_for(name):
    return "plr_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def photo_url(profile_url):
    try:
        h = fetch(profile_url)
        soup = BeautifulSoup(h, "html.parser")
        tag = soup.find("meta", attrs={"property": "og:image"})
        return tag.get("content") if tag and tag.get("content") else None
    except Exception:
        return None

def save_raw(url, html):
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(
        RAW_DIR,
        re.sub(r"[^A-Za-z0-9]+", "_", url)[:80] + "_" + time.strftime("%Y%m%d_%H%M%S") + ".html",
    )
    open(path, "w", encoding="utf-8").write(html)
    return path

def parse_rows(soup, base_url):
    out = []
    for tr in soup.find_all("tr"):
        a = tr.find("a", href=re.compile(r"/player/", re.I))
        if not a:
            continue
        name = norm(a.get_text(" ", strip=True))
        href = a.get("href", "").strip()
        full = href if href.startswith("http") else urljoin(base_url, href)
        full = full.replace("https://cuescore.com//cuescore.com", "https://cuescore.com").split("?")[0].split("#")[0]
        m = re.search(r"/player/([^/]+)/(\d+)$", full, re.I)
        if not m:
            continue
        cells = " | ".join(norm(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"]))
        pairs = re.findall(r"(\d+)\s*\(\s*(\d+)\s*/\s*(\d+)\s*\)", cells)
        pct = re.search(r"(\d+)\s*%", cells)
        mp = w = l = ft = fw = fl = wp = None
        if len(pairs) >= 1:
            mp, w, l = map(float, pairs[0])
        if len(pairs) >= 2:
            ft, fw, fl = map(float, pairs[1])
        if pct:
            wp = float(pct.group(1))
        out.append(
            {
                "display_name": name,
                "cuescore_player_id": m.group(2),
                "profile_url": full,
                "matches_played": mp,
                "wins": w,
                "losses": l,
                "frames_total": ft,
                "frames_won": fw,
                "frames_lost": fl,
                "win_rate": wp,
            }
        )
    dedup = {}
    for r in out:
        dedup[r["cuescore_player_id"]] = r
    return list(dedup.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--mode", default="update")
    args = ap.parse_args()

    html = fetch(args.url)
    raw = save_raw(args.url, html)
    soup = BeautifulSoup(html, "html.parser")
    rows = parse_rows(soup, args.url)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    tidm = re.search(r"/(\d+)$", args.url)
    tid = tidm.group(1) if tidm else None
    imported = 0

    for r in rows:
        pid = pid_for(r["display_name"])
        cur.execute(
            "INSERT OR IGNORE INTO players(player_id,display_name,created_ts_utc,notes) VALUES (?,?,?,?)",
            (pid, r["display_name"], utc_now(), "Created/updated by tournament importer"),
        )
        cur.execute(
            "INSERT OR REPLACE INTO player_cuescore_map(player_id,cuescore_player_id,cuescore_profile_url,cuescore_display_name,last_verified_ts_utc) VALUES (?,?,?,?,?)",
            (pid, r["cuescore_player_id"], r["profile_url"], r["display_name"], utc_now()),
        )
        cur.execute(
            """INSERT OR REPLACE INTO player_profile_stats(
                   player_id,matches_played,wins,losses,win_rate,innings_average,runouts,lag_wins,
                   frame_win_average,points,last_import_ts_utc,raw_json,frames_won,frames_lost,frames_total
               )
               VALUES (
                   ?,?,?,?,?,COALESCE((SELECT innings_average FROM player_profile_stats WHERE player_id=?),NULL),
                   COALESCE((SELECT runouts FROM player_profile_stats WHERE player_id=?),NULL),
                   COALESCE((SELECT lag_wins FROM player_profile_stats WHERE player_id=?),NULL),
                   COALESCE((SELECT frame_win_average FROM player_profile_stats WHERE player_id=?),NULL),
                   COALESCE((SELECT points FROM player_profile_stats WHERE player_id=?),NULL),
                   ?,?,?,?,?
               )""",
            (
                pid,
                r["matches_played"],
                r["wins"],
                r["losses"],
                r["win_rate"],
                pid,
                pid,
                pid,
                pid,
                pid,
                utc_now(),
                json.dumps(r, ensure_ascii=False),
                r["frames_won"],
                r["frames_lost"],
                r["frames_total"],
            ),
        )
        cur.execute(
            "INSERT OR REPLACE INTO tournament_player_results(row_id,tournament_url,tournament_id,player_id,cuescore_player_id,display_name,matches_played,wins,losses,frames_total,frames_won,frames_lost,win_rate,source_json,imported_ts_utc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"{tid}_{r['cuescore_player_id']}",
                args.url,
                tid,
                pid,
                r["cuescore_player_id"],
                r["display_name"],
                r["matches_played"],
                r["wins"],
                r["losses"],
                r["frames_total"],
                r["frames_won"],
                r["frames_lost"],
                r["win_rate"],
                json.dumps(r, ensure_ascii=False),
                utc_now(),
            ),
        )
        pu = photo_url(r["profile_url"])
        if pu:
            cur.execute(
                "INSERT OR REPLACE INTO player_media(player_id,cuescore_player_id,photo_url,local_photo_path,local_fallback_photo_path,photo_source,last_photo_sync_ts_utc,notes) VALUES (?,?,?,COALESCE((SELECT local_photo_path FROM player_media WHERE player_id=?),NULL),COALESCE((SELECT local_fallback_photo_path FROM player_media WHERE player_id=?),NULL),'cuescore_remote',?,?)",
                (pid, r["cuescore_player_id"], pu, pid, pid, utc_now(), r["profile_url"]),
            )
        imported += 1

    con.commit()
    con.close()
    print(json.dumps({"status": "ok", "imported": imported, "rows": len(rows), "raw_html": raw, "url": args.url}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"status": "fail", "error": str(e)}, indent=2))
        sys.exit(1)
