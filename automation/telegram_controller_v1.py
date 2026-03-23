import os, time, requests, sys
sys.path.append(r"C:\AI\BillarLanzarote\automation")
from _shared import load_json, ts_utc
ROOT=r"C:\AI\BillarLanzarote"; CFG=os.path.join(ROOT,"config","live_system_config.json"); RUNTIME=os.path.join(ROOT,"runtime"); LOG=os.path.join(ROOT,"logs","live_system","telegram_controller.log")
os.makedirs(os.path.dirname(LOG),exist_ok=True)
def log(m): open(LOG,"a",encoding="utf-8").write(f"[{ts_utc()}] {m}\n"); print(m)
def send(token, chat, txt): requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id":chat,"text":txt}, timeout=15)
def run():
    seen={}
    while True:
        cfg=load_json(CFG,{}); tg=cfg.get("telegram",{}); token=tg.get("bot_token",""); chat=tg.get("chat_id","")
        if not tg.get("enabled") or not token or not chat: time.sleep(5); continue
        for fn in os.listdir(RUNTIME):
            if not fn.endswith("_event.json"): continue
            p=os.path.join(RUNTIME,fn); mt=os.path.getmtime(p)
            if seen.get(p)==mt: continue
            seen[p]=mt; ev=load_json(p,{}); et=ev.get("event_type"); st=ev.get("state",{}); table=ev.get("table_key","")
            try:
                if et=="match_started" and tg.get("match_start",True): send(token,chat,f"[{table}] Match started\n{st.get('player_a','?')} vs {st.get('player_b','?')}")
                elif et=="match_ended" and tg.get("match_end",True): send(token,chat,f"[{table}] Match ended\n{st.get('player_a','?')} vs {st.get('player_b','?')}")
                elif et=="stream_started" and tg.get("stream_start",True): send(token,chat,f"[{table}] Stream started")
                elif et=="stream_stopped" and tg.get("stream_end",True): send(token,chat,f"[{table}] Stream stopped")
            except Exception as e: log(f"telegram send error: {e}")
        time.sleep(3)
if __name__=="__main__": run()
