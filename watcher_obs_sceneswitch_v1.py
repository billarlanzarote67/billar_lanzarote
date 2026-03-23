
import os, json, time
from obswebsocket import obsws, requests as obsreq
ROOT = r"C:\AI\BillarLanzarote"
CFG = os.path.join(ROOT, "config", "watcher_obs_sceneswitch_v1.json")
STATE = os.path.join(ROOT, "state", "live_tables.json")
cfg = json.load(open(CFG, "r", encoding="utf-8"))
last_scene = None
def choose_scene(data):
    tables = data.get("tables") or {}
    m1 = tables.get("mesa1", {}); m2 = tables.get("mesa2", {})
    if m1.get("status") == "live" and m2.get("status") != "live": return cfg.get("mesa1_scene", "Mesa 1")
    if m2.get("status") == "live" and m1.get("status") != "live": return cfg.get("mesa2_scene", "Mesa 2")
    if m1.get("status") == "live" and m2.get("status") == "live":
        return cfg.get("mesa1_scene", "Mesa 1") if cfg.get("preferred_when_both_live", "mesa1") == "mesa1" else cfg.get("mesa2_scene", "Mesa 2")
    return None
while True:
    try:
        data = json.load(open(STATE, "r", encoding="utf-8")); target = choose_scene(data)
        if target and target != last_scene:
            if cfg.get("dry_run", True): print("DRY RUN switch ->", target)
            else:
                ws = obsws(cfg["obs_host"], cfg["obs_port"], cfg["obs_password"]); ws.connect()
                ws.call(obsreq.SetCurrentProgramScene(sceneName=target)); ws.disconnect()
                print("Switched ->", target)
            last_scene = target
    except Exception as e:
        print("OBS scene switch error:", e)
    time.sleep(2)
