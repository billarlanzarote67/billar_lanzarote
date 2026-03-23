
import sqlite3, subprocess, os, json
from stats_automation_common import db, log_run, append_log

PY = r"C:\Program Files\Python312\python.exe"
SCRIPT = r"C:\AI\BillarLanzarote\scripts\import_player_profile.py"

def main():
    con = db(); cur = con.cursor()
    cur.execute("""SELECT DISTINCT cuescore_profile_url FROM player_cuescore_map
                   WHERE cuescore_profile_url IS NOT NULL AND TRIM(cuescore_profile_url) <> ''""")
    rows = [r[0] for r in cur.fetchall()]
    con.close()

    ok = 0; fail = 0
    for url in rows:
        res = subprocess.run([PY, SCRIPT, url], capture_output=True, text=True)
        if res.returncode == 0:
            ok += 1
        else:
            fail += 1
            append_log("profile_refresh.log", f"FAIL {url} :: {res.stderr[-500:]}")
    log_run("profile_refresh", None, "ok", {"ok": ok, "fail": fail, "count": len(rows)})
    print(json.dumps({"ok": ok, "fail": fail, "count": len(rows)}, indent=2))

if __name__ == "__main__":
    main()
