
import os, socket
ROOT = r"C:\AI\BillarLanzarote_DEMO"
print("Demo root exists:", os.path.exists(ROOT))
print("Config exists:", os.path.exists(os.path.join(ROOT, "config", "demo_config.json")))
def open_port(host, port):
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False
print("OBS websocket 4455 open:", open_port("127.0.0.1", 4455))
print("Demo dashboard: http://127.0.0.1:8798")
print("Demo overlay API mesa1: http://127.0.0.1:8799/api/overlay?table=mesa1")
