import http.server
import socketserver
import os
import webbrowser
from datetime import datetime

PORT = 5094
ROOT = r"C:\AI\BillarLanzarote"
WEB_DIR = os.path.join(ROOT, "web_overlay_preview")

LOG_DIR = os.path.join(ROOT, "logs", "overlay_preview")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "server.log")

def log(msg):
    line = f"[{datetime.now()}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Create simple UI if missing
os.makedirs(WEB_DIR, exist_ok=True)

index_file = os.path.join(WEB_DIR, "index.html")

if not os.path.exists(index_file):
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("""
<html>
<head>
<title>Overlay Preview</title>
<style>
body { background:#111; color:white; font-family:Arial; text-align:center; }
.card { margin:40px auto; padding:20px; width:60%; background:#222; border-radius:10px; }
</style>
</head>
<body>
<h1>Overlay Preview (LIVE)</h1>
<div class="card">Mesa 1 Overlay Placeholder</div>
<div class="card">Mesa 2 Overlay Placeholder</div>
</body>
</html>
""")

os.chdir(WEB_DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        log(format % args)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    log(f"Overlay Preview running on http://127.0.0.1:{PORT}")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    httpd.serve_forever()
