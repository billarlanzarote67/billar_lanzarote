import os, time, sys
sys.path.append(r"C:\AI\BillarLanzarote\automation")
from _shared import load_json, save_json, ts_utc
from obswebsocket import obsws, requests as obsreq
ROOT=r"C:\AI\BillarLanzarote"; CFG=os.path.join(ROOT,"config","live_system_config.json"); STATE=os.path.join(ROOT,"state"); RUNTIME=os.path.join(ROOT,"runtime"); LOG=os.path.join(ROOT,"logs","live_system","stream_controller.log")
os.makedirs(os.path.dirname(LOG),exist_ok=True); os.makedirs(RUNTIME,exist_ok=True)
def log(m): open(LOG,"a",encoding="utf-8").write(f"[{ts_utc()}] {m}\n"); print(m)
def ev(t,e,s=None): save_json(os.path.join(RUNTIME,f"{t}_event.json"),{"event_type":e,"table_key":t,"ts":ts_utc(),"state":s or {}})
def conn(cfg): ws=obsws(cfg["stream"].get("obs_host","127.0.0.1"),cfg["stream"].get("obs_port",4455),cfg["stream"].get("obs_password","")); ws.connect(); return ws
def run():
    live={}; stop={}
    while True:
        cfg=load_json(CFG,{})
        try: ws=conn(cfg)
        except Exception as e: log(f"obs connect failed: {e}"); time.sleep(5); continue
        try:
            while True:
                for tk,meta in cfg.get("tables",{}).items():
                    st=load_json(os.path.join(STATE,f"{tk}_live.json"),{"active":False}); isl=live.get(tk,False)
                    if st.get("active") and not isl and cfg["stream"].get("auto_start",True):
                        sc=cfg["stream"]["scene_map"].get(tk,meta.get("name",tk))
                        try: ws.call(obsreq.SetCurrentProgramScene(sceneName=sc))
                        except Exception: pass
                        try: ws.call(obsreq.StartStream())
                        except Exception: pass
                        live[tk]=True; stop[tk]=None; ev(tk,"stream_started",st); log(f"{tk}: stream started")
                    elif not st.get("active") and isl and cfg["stream"].get("auto_stop",True):
                        if not stop.get(tk): stop[tk]=time.time()+cfg["stream"].get("auto_stop_delay_seconds",90)
                        elif time.time()>=stop[tk]:
                            try: ws.call(obsreq.StopStream())
                            except Exception: pass
                            live[tk]=False; stop[tk]=None; ev(tk,"stream_stopped",st); log(f"{tk}: stream stopped")
                    elif st.get("active") and isl: stop[tk]=None
                save_json(os.path.join(RUNTIME,"live_stream_status.json"),{"ts":ts_utc(),"tables":{k:{"is_streaming":bool(v),"pending_stop":stop.get(k)} for k,v in live.items()}})
                time.sleep(3)
        except Exception as e: log(f"stream loop failure: {e}"); time.sleep(5)
if __name__=="__main__": run()
