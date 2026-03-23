import json
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
