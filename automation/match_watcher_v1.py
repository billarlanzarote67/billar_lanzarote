import os, re, time, sqlite3, requests, sys
sys.path.append(r"C:\AI\BillarLanzarote\automation")
from bs4 import BeautifulSoup
from _shared import load_json, save_json, ts_utc, norm, short_hash
ROOT=r"C:\AI\BillarLanzarote"; CFG=os.path.join(ROOT,"config","live_system_config.json"); STATE=os.path.join(ROOT,"state"); RAW=os.path.join(ROOT,"data","raw_cuescore","live"); LOG=os.path.join(ROOT,"logs","live_system","match_watcher.log"); RUNTIME=os.path.join(ROOT,"runtime"); DB=os.path.join(ROOT,"database","sqlite","billar_lanzarote.sqlite")
for p in [STATE,RAW,os.path.dirname(LOG),RUNTIME]: os.makedirs(p, exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0"}
def log(m): open(LOG,"a",encoding="utf-8").write(f"[{ts_utc()}] {m}\n"); print(m)
def fetch(url): r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status(); return r.text
def save_raw(table, html):
    folder=os.path.join(RAW,table); os.makedirs(folder,exist_ok=True); p=os.path.join(folder,time.strftime("%Y%m%d_%H%M%S")+".html"); open(p,"w",encoding="utf-8").write(html); return p
def parse_html(html):
    soup=BeautifulSoup(html,"html.parser"); text=norm(soup.get_text(" ", strip=True)); players=[]
    for a in soup.find_all("a", href=True):
        href=a.get("href",""); t=norm(a.get_text(" ", strip=True))
        if ("/challenge/" in href or "/player/" in href) and t and t not in players and len(t)>2: players.append(t)
    players=players[:2]
    m=re.search(r"(\d+)\s*[-:]\s*(\d+)", text); sa=int(m.group(1)) if m else None; sb=int(m.group(2)) if m else None
    ch=None; cid=None
    for a in soup.find_all("a", href=True):
        href=a.get("href","")
        if "/challenge/" in href and "/edit/" not in href:
            ch=href if href.startswith("http") else "https://cuescore.com"+href
            m2=re.search(r"/(\d+)$", ch); cid=m2.group(1) if m2 else None; break
    disc=None
    for d in ["8-Ball","9-Ball","10-Ball","8 Ball","9 Ball","10 Ball"]:
        if d.lower() in text.lower(): disc=d.replace(" ","-"); break
    return {"active":bool(players or ch or m),"player_a":players[0] if len(players)>0 else None,"player_b":players[1] if len(players)>1 else None,"score_a":sa,"score_b":sb,"challenge_url":ch,"challenge_id":cid,"discipline":disc,"last_seen_ts":ts_utc()}
def schema():
    con=sqlite3.connect(DB); cur=con.cursor(); cur.executescript("CREATE TABLE IF NOT EXISTS live_matches (live_match_id TEXT PRIMARY KEY,table_key TEXT,table_name TEXT,challenge_id TEXT,challenge_url TEXT,player_a TEXT,player_b TEXT,discipline TEXT,status TEXT,started_ts TEXT,ended_ts TEXT,last_seen_ts TEXT,score_a INTEGER,score_b INTEGER,winner TEXT,raw_snapshot_path TEXT,updated_ts TEXT); CREATE TABLE IF NOT EXISTS live_match_snapshots (snapshot_id TEXT PRIMARY KEY,live_match_id TEXT,table_key TEXT,snapshot_ts TEXT,score_a INTEGER,score_b INTEGER,status TEXT,raw_snapshot_path TEXT);"); con.commit(); con.close()
def db_write(table_key, table_name, st, raw):
    schema(); con=sqlite3.connect(DB); cur=con.cursor(); seed=f"{table_key}|{st.get('challenge_id') or ''}|{st.get('player_a') or ''}|{st.get('player_b') or ''}"; mid=short_hash(seed)
    cur.execute("SELECT started_ts FROM live_matches WHERE live_match_id=?", (mid,)); row=cur.fetchone(); started=row[0] if row and row[0] else ts_utc()
    status="active" if st.get("active") else "idle"; winner=None
    if st.get("score_a") is not None and st.get("score_b") is not None:
        winner=st.get("player_a") if st["score_a"]>st["score_b"] else st.get("player_b") if st["score_b"]>st["score_a"] else None
    cur.execute("INSERT OR REPLACE INTO live_matches VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(mid,table_key,table_name,st.get("challenge_id"),st.get("challenge_url"),st.get("player_a"),st.get("player_b"),st.get("discipline"),status,started,None if st.get("active") else ts_utc(),st.get("last_seen_ts"),st.get("score_a"),st.get("score_b"),winner,raw,ts_utc()))
    sid=short_hash(f"{mid}|{st.get('score_a')}|{st.get('score_b')}|{st.get('last_seen_ts')}"); cur.execute("INSERT OR REPLACE INTO live_match_snapshots VALUES (?,?,?,?,?,?,?,?)",(sid,mid,table_key,ts_utc(),st.get("score_a"),st.get("score_b"),status,raw)); con.commit(); con.close()
def event(table, et, st): save_json(os.path.join(RUNTIME,f"{table}_event.json"),{"event_type":et,"table_key":table,"ts":ts_utc(),"state":st})
def run():
    cfg=load_json(CFG,{}); poll=cfg.get("watcher",{}).get("poll_seconds",5); prev={}
    while True:
        for tk,meta in cfg.get("tables",{}).items():
            html=None
            try:
                url=f"https://cuescore.com/scoreboard/?codepersonal={meta.get('code')}"; html=fetch(url); st=parse_html(html); save_json(os.path.join(STATE,f"{tk}_live.json"),st)
                if prev.get(tk)!=st:
                    raw=save_raw(tk, html); db_write(tk, meta.get("name",tk), st, raw); pa=prev.get(tk,{}).get("active",False); na=st.get("active",False)
                    if not pa and na: event(tk,"match_started",st); log(f"{tk}: match started")
                    elif pa and not na: event(tk,"match_ended",st); log(f"{tk}: match ended")
                    else: event(tk,"state_changed",st); log(f"{tk}: state changed")
                    prev[tk]=st
            except Exception as e:
                log(f"{tk}: watcher error: {e}")
                if html: save_raw(tk, html)
        time.sleep(poll)
if __name__=="__main__": run()
