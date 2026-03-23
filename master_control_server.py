import http.server
import socketserver
import json
import os

PORT = 5090
ROOT = "C:\\AI\\BillarLanzarote"
STATE = os.path.join(ROOT, "state")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = f"""
            <html>
            <head>
            <title>Billar Lanzarote Master Control</title>
            <style>
                body {{ background:#111; color:#eee; font-family:Arial; }}
                .btn {{ padding:15px; margin:10px; background:#333; display:inline-block; cursor:pointer; }}
            </style>
            </head>
            <body>
            <h1>🔥 Billar Lanzarote Control</h1>

            <div class="btn" onclick="fetch('/start')">▶ START SYSTEM</div>
            <div class="btn" onclick="fetch('/stop')">⛔ STOP SYSTEM</div>

            <h3>State Files</h3>
            <pre>{self.get_state()}</pre>

            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif self.path == "/start":
            os.system(f"{ROOT}\\START_EVERYTHING.bat")
            self.respond("STARTED")

        elif self.path == "/stop":
            os.system(f"{ROOT}\\STOP_ALL_CANONICAL_v1.bat")
            self.respond("STOPPED")

    def respond(self, msg):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(msg.encode())

    def get_state(self):
        try:
            files = os.listdir(STATE)
            return "\n".join(files)
        except:
            return "No state folder"

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Master Control running on http://127.0.0.1:{PORT}")
    httpd.serve_forever()
