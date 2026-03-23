import json
import os
from pathlib import Path

ROOT = Path(r"C:\AI\BillarLanzarote")
STATE = ROOT / "state"
STATE.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

mesa1_live = load_json(STATE / "mesa1_live.json", {"table": "mesa1", "active": False})
mesa2_live = load_json(STATE / "mesa2_live.json", {"table": "mesa2", "active": False})
mesa1_match = load_json(STATE / "mesa1_match.json", {"table": "mesa1"})
mesa2_match = load_json(STATE / "mesa2_match.json", {"table": "mesa2"})
mesa1_ai = load_json(STATE / "mesa1_ai_state.json", {})
mesa2_ai = load_json(STATE / "mesa2_ai_state.json", {})
health_v5 = load_json(STATE / "master_control_health_v5.json", {})
watchdog_state = load_json(STATE / "watchdog_state_v1.json", {})
watchdog_status = load_json(STATE / "watchdog_status_v1.json", {})

if not mesa1_ai:
    mesa1_ai = {
        "table": "mesa1",
        "source": "bridge",
        "motion_active": bool(mesa1_live.get("active", False)),
        "live": mesa1_live
    }

if not mesa2_ai:
    mesa2_ai = {
        "table": "mesa2",
        "source": "bridge",
        "motion_active": bool(mesa2_live.get("active", False)),
        "live": mesa2_live
    }

health_state = {
    "source": "master_control_health_v5.json",
    "health": health_v5,
    "watchdog_state": watchdog_state,
    "watchdog_status": watchdog_status
}

current_match = {
    "mesa1": mesa1_match,
    "mesa2": mesa2_match
}

obs_scene_switcher_state = {
    "source": "bridge",
    "enabled": True,
    "obs_ok": True
}

mesa1_overlay_state = {
    "table": "mesa1",
    "source": "mesa1_live.json",
    "live": mesa1_live,
    "match": mesa1_match
}

mesa2_overlay_state = {
    "table": "mesa2",
    "source": "mesa2_live.json",
    "live": mesa2_live,
    "match": mesa2_match
}

mesa1_cuescore_state = {
    "table": "mesa1",
    "source": "mesa1_match.json",
    "match": mesa1_match
}

mesa2_cuescore_state = {
    "table": "mesa2",
    "source": "mesa2_match.json",
    "match": mesa2_match
}

save_json(STATE / "mesa1_ai_state.json", mesa1_ai)
save_json(STATE / "mesa2_ai_state.json", mesa2_ai)
save_json(STATE / "health_state.json", health_state)
save_json(STATE / "current_match.json", current_match)
save_json(STATE / "obs_scene_switcher_state.json", obs_scene_switcher_state)
save_json(STATE / "mesa1_overlay_state.json", mesa1_overlay_state)
save_json(STATE / "mesa2_overlay_state.json", mesa2_overlay_state)
save_json(STATE / "mesa1_cuescore_state.json", mesa1_cuescore_state)
save_json(STATE / "mesa2_cuescore_state.json", mesa2_cuescore_state)

print("Bridge files written to:", STATE)
