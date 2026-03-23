import os
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = r"C:\AI\BillarLanzarote"
PHOTOS_DIR = os.path.join(ROOT, "data", "player_photos")
PORT = 8102
os.makedirs(PHOTOS_DIR, exist_ok=True)

HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Player Photo Setup</title>
<style>
body { font-family: Arial,sans-serif; background:#111; color:#eee; margin:20px; }
.card { background:#1b1b1b; border:1px solid #2d2d2d; border-radius:18px; padding:16px; max-width:900px; }
code { background:#222; padding:2px 6px; border-radius:6px; }
a { color:#8ecbff; }
</style></head><body><div class="card">
<h1>Player Photo Setup</h1>
<p>Put player photos into:</p>
<p><code>C:\\AI\\BillarLanzarote\\data\\player_photos</code></p>
<p>Use filenames like:</p>
<ul>
<li><code>Carlos_Enrique_Moreno_Angulo.jpg</code></li>
<li><code>Ais_Eyez_Bailey.jpg</code></li>
</ul>
<p>Supported: jpg, jpeg, png, webp</p>
<p>After adding photos, refresh:</p>
<ul>
<li><a href="http://127.0.0.1:8099">Gallery</a></li>
<li><a href="http://127.0.0.1:8101/?player=Ais%20Eyez%20Bailey">Profile page example</a></li>
</ul>
</div></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    print(f"Photo setup help on http://127.0.0.1:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
