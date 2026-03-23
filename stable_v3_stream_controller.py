import os, sys, time
from obswebsocket import obsws, requests as obsreq
sys.path.append(r"C:\AI\BillarLanzarote\scripts")
from _stable_shared import load_json, save_json, ts_utc
ROOT=r"C:\AI\BillarLanzarote"; CFG_PATH=os.path.join(ROOT,"config","stable_v3_config.json"); STATE_DIR=os.path.join(ROOT,"state"); RUNTIME_DIR=os.path.join(ROOT,"runtime"); LOG_PATH=os.path.join(ROOT,"logs","stable_v3","stable_v3_stream_controller.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True); os.makedirs(RUNTIME_DIR, exist_ok=True)
def log(msg):
    line=f"[{ts_utc()}] {msg}"
    with open(LOG_PATH,"a",encoding="utf-8") as f: f.write(line+"\n")
    print(msg)
def event(table_key, event_type, state=None):
    save_json(os.path.join(RUNTIME_DIR, f"{table_key}_stream_event.json"), {"event_type": event_type, "table_key": table_key, "ts": ts_utc(), "state": state or {}})
def connect_obs(cfg):
    oc=cfg.get("obs", {}); ws=obsws(oc.get("host","127.0.0.1"), oc.get("port",4455), oc.get("password","")); ws.connect(); return ws
def run():
    live={}; stop_at={}
    while True:
        cfg=load_json(CFG_PATH, {})
        if not cfg.get("obs", {}).get("enabled", True): time.sleep(5); continue
        try: ws=connect_obs(cfg)
        except Exception as e: log(f"OBS connect failed: {e}"); time.sleep(5); continue
        try:
            while True:
                for table_key, meta in cfg.get("tables", {}).items():
                    st=load_json(os.path.join(STATE_DIR, f"{table_key}_live.json"), {"active": False}); is_live=live.get(table_key, False)
                    if st.get("active") and not is_live and cfg["obs"].get("auto_start", True):
                        try: ws.call(obsreq.SetCurrentProgramScene(sceneName=meta.get("scene_name", meta.get("name", table_key))))
                        except Exception: pass
                        try: ws.call(obsreq.StartStream())
                        except Exception: pass
                        live[table_key]=True; stop_at[table_key]=None; event(table_key, "stream_started", st); log(f"{table_key}: stream started")
                    elif not st.get("active") and is_live and cfg["obs"].get("auto_stop", True):
                        if not stop_at.get(table_key): stop_at[table_key]=time.time()+cfg["obs"].get("auto_stop_delay_seconds",90)
                        elif time.time() >= stop_at[table_key]:
                            try: ws.call(obsreq.StopStream())
                            except Exception: pass
                            live[table_key]=False; stop_at[table_key]=None; event(table_key, "stream_stopped", st); log(f"{table_key}: stream stopped")
                    elif st.get("active") and is_live:
                        stop_at[table_key]=None
                save_json(os.path.join(RUNTIME_DIR,"stable_v3_stream_status.json"), {"ts": ts_utc(), "tables": {k: {"is_streaming": bool(v), "pending_stop": stop_at.get(k)} for k,v in live.items()}})
                time.sleep(3)
        except Exception as e:
            log(f"Stream loop error: {e}"); time.sleep(5)
if __name__=="__main__": run()
