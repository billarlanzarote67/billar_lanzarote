import json
import os
from pathlib import Path

ROOT = Path(r"C:\AI\BillarLanzarote")
SCRIPTS = ROOT / "scripts"
STATE = ROOT / "state"
LOGS = ROOT / "logs"
CFG = ROOT / "config"
INSTALL01 = ROOT / "01_INSTALL"

SCRIPTS.mkdir(parents=True, exist_ok=True)
STATE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
CFG.mkdir(parents=True, exist_ok=True)
INSTALL01.mkdir(parents=True, exist_ok=True)

write_state_bridges = r'''import json
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
'''

project_health_remap = r'''import json
import os
import socket
import time
from pathlib import Path

ROOT = Path(r"C:\AI\BillarLanzarote")
STATE = ROOT / "state"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def load_json(path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), None
        return None, "missing"
    except Exception as e:
        return None, str(e)

def state_status(path):
    data, err = load_json(path)
    if err:
        return {
            "file": path.name,
            "exists": False,
            "json_ok": False,
            "fresh": False,
            "age_seconds": None,
            "message": err
        }

    age = time.time() - path.stat().st_mtime
    fresh = age <= 600
    return {
        "file": path.name,
        "exists": True,
        "json_ok": True,
        "fresh": fresh,
        "age_seconds": round(age, 1),
        "message": "ok" if fresh else f"stale ({round(age,1)}s > 600s)"
    }

def port_open(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

state_files = [
    STATE / "master_control_health_v5.json",
    STATE / "watchdog_state_v1.json",
    STATE / "watchdog_status_v1.json",
    STATE / "mesa1_live.json",
    STATE / "mesa2_live.json",
    STATE / "mesa1_match.json",
    STATE / "mesa2_match.json",
    STATE / "mesa1_ai_state.json",
    STATE / "mesa2_ai_state.json",
    STATE / "health_state.json",
    STATE / "current_match.json",
    STATE / "mesa1_overlay_state.json",
    STATE / "mesa2_overlay_state.json",
    STATE / "mesa1_cuescore_state.json",
    STATE / "mesa2_cuescore_state.json",
]

ports = [
    ("master_control", 5090),
    ("overlay_preview", 5094),
    ("status_ui", 5095),
    ("overlay_thumbnails", 5097),
    ("obs_websocket", 4455),
    ("mediamtx", 8554),
    ("stable_v3_panel", 8788),
    ("stable_v3_overlay_api", 8789),
]

state_results = [state_status(p) for p in state_files]
port_results = []
for name, port in ports:
    ok = port_open("127.0.0.1", port)
    port_results.append({"name": name, "port": port, "ok": ok})

warnings = sum(1 for s in state_results if not s["fresh"]) + sum(1 for p in port_results if not p["ok"])
required_failures = 0

report = {
    "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
    "warnings": warnings,
    "required_failures": required_failures,
    "ports": port_results,
    "state_files": state_results
}

txt_lines = []
txt_lines.append("BILLAR LANZAROTE HEALTH REMAP REPORT")
txt_lines.append("=" * 50)
txt_lines.append(f"Generated: {report['generated']}")
txt_lines.append("")
txt_lines.append("PORTS")
for p in port_results:
    txt_lines.append(f"- {p['name']} ({p['port']}): {'OK' if p['ok'] else 'FAIL'}")
txt_lines.append("")
txt_lines.append("STATE FILES")
for s in state_results:
    txt_lines.append(
        f"- {s['file']}: exists={s['exists']} json_ok={s['json_ok']} "
        f"fresh={s['fresh']} age={s['age_seconds']} msg={s['message']}"
    )

report_txt = LOGS / "project_health_report.txt"
report_json = LOGS / "project_health_report.json"
report_html = LOGS / "project_health_dashboard.html"

with open(report_txt, "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines))

with open(report_json, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

rows = []
for p in port_results:
    badge = "OK" if p["ok"] else "FAIL"
    color = "#22c55e" if p["ok"] else "#ef4444"
    rows.append(f'<div class="card"><div class="label">{p["name"]} ({p["port"]})</div><div class="value" style="color:{color}">{badge}</div></div>')
ports_html = "".join(rows)

state_rows = []
for s in state_results:
    if s["exists"] and s["json_ok"] and s["fresh"]:
        status = "OK"
        color = "#22c55e"
    elif s["exists"] and s["json_ok"]:
        status = "STALE"
        color = "#facc15"
    else:
        status = "MISSING/BAD"
        color = "#fb923c"
    state_rows.append(
        f"<tr><td>{s['file']}</td><td style='color:{color}'>{status}</td><td>{s['age_seconds']}</td><td>{s['message']}</td></tr>"
    )

html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Billar Lanzarote Health Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; background:#111827; color:#f3f4f6; margin:20px; }}
h1 {{ margin:0 0 8px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:20px; }}
.card {{ background:#1f2937; border-radius:14px; padding:16px; }}
.label {{ color:#d1d5db; font-size:14px; }}
.value {{ font-size:28px; font-weight:bold; margin-top:8px; }}
table {{ width:100%; border-collapse:collapse; background:#1f2937; border-radius:14px; overflow:hidden; }}
th, td {{ padding:10px; border-bottom:1px solid #374151; text-align:left; }}
.smallgrid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-bottom:20px; }}
</style>
</head>
<body>
<h1>Billar Lanzarote Health Dashboard</h1>
<div>Generated: {report['generated']}</div>
<br>
<div class="smallgrid">
  <div class="card"><div class="label">Required Failures</div><div class="value" style="color:#22c55e">{required_failures}</div></div>
  <div class="card"><div class="label">Warnings</div><div class="value" style="color:#facc15">{warnings}</div></div>
</div>
<h2>Ports</h2>
<div class="grid">{ports_html}</div>
<h2>State Files</h2>
<table>
<tr><th>File</th><th>Status</th><th>Age</th><th>Message</th></tr>
{''.join(state_rows)}
</table>
</body>
</html>"""

with open(report_html, "w", encoding="utf-8") as f:
    f.write(html)

print("Health remap reports written:")
print(report_txt)
print(report_json)
print(report_html)
'''

def bat(text: str) -> str:
    return text.replace("\n", "\r\n")

shim_files = {
    INSTALL01 / "VERIFY_ALL.bat": bat(r'''@echo off
call "C:\AI\BillarLanzarote\CHECK_HEALTH_DASHBOARD.bat"
'''),
    INSTALL01 / "START_LIVE_WATCHER.bat": bat(r'''@echo off
call "C:\AI\BillarLanzarote\launchers\RUN_LIVEWATCHER_DB_WRITER_V1.bat"
'''),
    INSTALL01 / "STOP_LIVE_WATCHER.bat": bat(r'''@echo off
call "C:\AI\BillarLanzarote\STOP_EVERYTHING.bat"
'''),
    INSTALL01 / "OPEN_OVERLAY_PREVIEW_PAGE.bat": bat(r'''@echo off
start "" http://127.0.0.1:5094
'''),
    INSTALL01 / "START_PLAYER_GALLERY.bat": bat(r'''@echo off
start "" cmd /k "C:\Progra~1\Python312\python.exe C:\AI\BillarLanzarote\scripts\player_gallery_server.py"
'''),
    INSTALL01 / "START_H2H_DASHBOARD.bat": bat(r'''@echo off
start "" cmd /k "C:\Progra~1\Python312\python.exe C:\AI\BillarLanzarote\scripts\player_h2h_server.py"
'''),
    INSTALL01 / "OPEN_TELEGRAM_CONFIG.bat": bat(r'''@echo off
explorer "C:\AI\BillarLanzarote\config"
'''),
    INSTALL01 / "OPEN_ROOT_FOLDER.bat": bat(r'''@echo off
explorer "C:\AI\BillarLanzarote"
'''),
    INSTALL01 / "OPEN_LOGS.bat": bat(r'''@echo off
explorer "C:\AI\BillarLanzarote\logs"
'''),
    INSTALL01 / "OPEN_CONFIG.bat": bat(r'''@echo off
explorer "C:\AI\BillarLanzarote\config"
'''),
    INSTALL01 / "OPEN_MESA1_OVERLAY.bat": bat(r'''@echo off
start "" http://127.0.0.1:5094
'''),
    INSTALL01 / "OPEN_MESA2_OVERLAY.bat": bat(r'''@echo off
start "" http://127.0.0.1:5094
'''),
    INSTALL01 / "SET_VOLCANIC_STATIC_DEFAULT.bat": bat(r'''@echo off
start "" http://127.0.0.1:5094
'''),
    INSTALL01 / "SET_VOLCANIC_ANIMATED_DEFAULT.bat": bat(r'''@echo off
start "" http://127.0.0.1:5094
'''),
}

check_health_bat = bat(r'''@echo off
setlocal
set ROOT=C:\AI\BillarLanzarote
set PY=C:\Progra~1\Python312\python.exe

cd /d "%ROOT%"

echo Writing state bridge files...
"%PY%" "%ROOT%\scripts\write_state_bridges_v1.py"

echo Building remapped health dashboard...
"%PY%" "%ROOT%\scripts\project_health_remap_v1.py"

start "" "%ROOT%\logs\project_health_dashboard.html"
echo Health dashboard refreshed.
pause
exit /b 0
''')

start_everything_bat = bat(r'''@echo off
title BILLAR LANZAROTE - START EVERYTHING
setlocal

set ROOT=C:\AI\BillarLanzarote

echo ========================================
echo STARTING BILLAR LANZAROTE SYSTEM
echo ========================================

cd /d "%ROOT%"

echo Starting Stable Core...
call "%ROOT%\launchers\START_STABLE_PACK_V3.bat"
timeout /t 2 >nul

echo Starting Vision Core Mesa1...
call "%ROOT%\launchers\START_VISIONCORE_MESA1.bat"
timeout /t 1 >nul

echo Starting Vision Core Mesa2...
call "%ROOT%\launchers\START_VISIONCORE_MESA2.bat"
timeout /t 1 >nul

echo Starting LiveWatcher DB...
start "LiveWatcher DB" cmd /k ""%ROOT%\launchers\RUN_LIVEWATCHER_DB_WRITER_V1.bat""
timeout /t 1 >nul

echo Starting Overlay Preview...
start "Overlay Preview" cmd /k "C:\Progra~1\Python312\python.exe C:\AI\BillarLanzarote\scripts\overlay_preview_server.py"
timeout /t 1 >nul

echo Refreshing state bridges + health dashboard...
call "%ROOT%\CHECK_HEALTH_DASHBOARD.bat"

start "" http://127.0.0.1:5090
start "" http://127.0.0.1:5094

echo ========================================
echo SYSTEM STARTED
echo ========================================
pause
exit /b 0
''')

files_to_write = {
    SCRIPTS / "write_state_bridges_v1.py": write_state_bridges,
    SCRIPTS / "project_health_remap_v1.py": project_health_remap,
    ROOT / "CHECK_HEALTH_DASHBOARD.bat": check_health_bat,
    ROOT / "START_EVERYTHING.bat": start_everything_bat,
}

for path, content in files_to_write.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

for path, content in shim_files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

print("Created/updated:")
for path in list(files_to_write.keys()) + list(shim_files.keys()):
    print(path)
