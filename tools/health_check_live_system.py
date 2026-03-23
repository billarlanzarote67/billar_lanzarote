import os, socket
ROOT=r"C:\AI\BillarLanzarote"
print("Root exists:", os.path.exists(ROOT))
def po(h,p):
 s=socket.socket(); s.settimeout(1)
 try:
  s.connect((h,p)); s.close(); return True
 except: return False
print("OBS websocket 4455 open:", po("127.0.0.1",4455))
print("Control Panel: http://127.0.0.1:8788")
print("Overlay API: http://127.0.0.1:8789/api/overlay?table=mesa1")
