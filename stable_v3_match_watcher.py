import os, sys, sqlite3, time, requests, re
from bs4 import BeautifulSoup
sys.path.append(r"C:\AI\BillarLanzarote\scripts")
from _stable_shared import load_json, save_json, ts_utc, norm
ROOT=r"C:\AI\BillarLanzarote"; CFG_PATH=os.path.join(ROOT,"config","stable_v3_config.json"); LOG_PATH=os.path.join(ROOT,"logs","stable_v3","stable_v3_match_watcher.log"); STATE_DIR=os.path.join(ROOT,"state"); RUNTIME_DIR=os.path.join(ROOT,"runtime"); DB_PATH=os.path.join(ROOT,"data","db","billar_lanzarote.db"); RAW_DIR=os.path.join(ROOT,"data","raw_cuescore","stable_v3"); HEADERS={"User-Agent":"Mozilla/5.0"}
for p in [os.path.dirname(LOG_PATH), STATE_DIR, RUNTIME_DIR, RAW_DIR]: os.makedirs(p, exist_ok=True)
def log(msg):
    line=f"[{ts_utc()}] {msg}"
    with open(LOG_PATH,"a",encoding="utf-8") as f: f.write(line+"\n")
    print(msg)
def fetch(url):
    r=requests.get(url, headers=HEADERS, timeout=20); r.raise_for_status(); return r.text
def save_raw(table_key, html):
    folder=os.path.join(RAW_DIR, table_key); os.makedirs(folder, exist_ok=True); p=os.path.join(folder, time.strftime("%Y%m%d_%H%M%S")+".html"); open(p,"w",encoding="utf-8").write(html); return p
def parse_scoreboard(html, fallback_name):
    soup=BeautifulSoup(html,"html.parser"); text=norm(soup.get_text(" ", strip=True)); players=[]; challenge_url=None
    for a in soup.find_all("a", href=True):
        href=a.get("href",""); t=norm(a.get_text(" ", strip=True))
        if "/challenge/" in href and "/edit/" not in href and not challenge_url: challenge_url = href if href.startswith("http") else f"https://cuescore.com{href}"
        if ("/player/" in href or "/challenge/" in href) and t and len(t)>2 and t not in players: players.append(t)
    players=players[:2]
    score_a=score_b=None; m=re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if m: score_a, score_b = int(m.group(1)), int(m.group(2))
    discipline=None
    for d in ["8-Ball","9-Ball","10-Ball","8 Ball","9 Ball","10 Ball"]:
        if d.lower() in text.lower(): discipline=d.replace(" ","-"); break
    return {"active": bool(players or m or challenge_url), "table_name": fallback_name, "player_a": players[0] if len(players)>0 else None, "player_b": players[1] if len(players)>1 else None, "score_a": score_a, "score_b": score_b, "challenge_url": challenge_url, "discipline": discipline, "last_seen_ts": ts_utc()}
def upsert_players(conn, state):
    cur=conn.cursor()
    for name in [state.get("player_a"), state.get("player_b")]:
        if name: cur.execute("INSERT OR IGNORE INTO players(name) VALUES (?)", (name,))
    conn.commit()
def save_snapshot(conn, table_key, state):
    cur=conn.cursor()
    cur.execute("INSERT INTO match_snapshots(table_key, player_a, player_b, score_a, score_b, challenge_url, source) VALUES (?,?,?,?,?,?,?)", (table_key, state.get("player_a"), state.get("player_b"), state.get("score_a"), state.get("score_b"), state.get("challenge_url"), "stable_v3_watcher"))
    conn.commit()
def save_final_match(conn, table_key, table_name, state):
    if not state.get("player_a") or not state.get("player_b"): return
    sa, sb = state.get("score_a"), state.get("score_b"); winner=None
    if sa is not None and sb is not None:
        if sa > sb: winner = state.get("player_a")
        elif sb > sa: winner = state.get("player_b")
    cur=conn.cursor()
    cur.execute("INSERT INTO matches(table_key, table_name, player_a, player_b, winner, score_a, score_b, challenge_url, source) VALUES (?,?,?,?,?,?,?,?,?)", (table_key, table_name, state.get("player_a"), state.get("player_b"), winner, sa, sb, state.get("challenge_url"), "stable_v3_watcher"))
    conn.commit()
def emit_event(table_key, event_type, state):
    save_json(os.path.join(RUNTIME_DIR, f"{table_key}_event.json"), {"event_type": event_type, "table_key": table_key, "ts": ts_utc(), "state": state})
def run():
    cfg=load_json(CFG_PATH, {}); poll=cfg.get("watcher", {}).get("poll_seconds", 10); last={}
    while True:
        conn=sqlite3.connect(DB_PATH)
        try:
            for table_key, meta in cfg.get("tables", {}).items():
                try:
                    html=fetch(f"https://cuescore.com/scoreboard/?codepersonal={meta.get('codepersonal')}")
                    state=parse_scoreboard(html, meta.get("name", table_key))
                    save_json(os.path.join(STATE_DIR, f"{table_key}_live.json"), state)
                    if cfg.get("watcher", {}).get("save_raw_html", True): save_raw(table_key, html)
                    upsert_players(conn, state); save_snapshot(conn, table_key, state)
                    prev=last.get(table_key); pa=prev.get("active") if isinstance(prev, dict) else False; na=state.get("active", False)
                    if not pa and na: emit_event(table_key, "match_started", state); log(f"{table_key}: match started")
                    elif pa and not na:
                        if prev: save_final_match(conn, table_key, meta.get("name", table_key), prev)
                        emit_event(table_key, "match_ended", state); log(f"{table_key}: match ended")
                    elif prev != state: emit_event(table_key, "state_changed", state); log(f"{table_key}: state changed")
                    last[table_key]=state
                except Exception as e:
                    log(f"{table_key}: watcher error: {e}")
            conn.close()
        except Exception:
            conn.close(); raise
        time.sleep(poll)
if __name__ == "__main__": run()
