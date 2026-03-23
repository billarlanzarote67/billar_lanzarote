import os, socket, sqlite3
ROOT=r"C:\AI\BillarLanzarote"; DB=r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db"
def port_open(host, port):
    s=socket.socket(); s.settimeout(1)
    try:
        s.connect((host, port)); s.close(); return True
    except Exception:
        return False
print("ROOT exists:", os.path.exists(ROOT))
print("DB exists:", os.path.exists(DB))
if os.path.exists(DB):
    conn=sqlite3.connect(DB); cur=conn.cursor()
    for tbl in ["players","matches","match_snapshots"]:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            print(tbl, "rows:", cur.fetchone()[0])
        except Exception as e:
            print(tbl, "error:", e)
    conn.close()
print("OBS websocket 4455 open:", port_open("127.0.0.1", 4455))
print("Control panel: http://127.0.0.1:8788")
print("Overlay API: http://127.0.0.1:8789/api/overlay?table=mesa1")
