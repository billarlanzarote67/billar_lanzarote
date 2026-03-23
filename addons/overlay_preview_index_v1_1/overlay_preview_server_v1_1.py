
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import html

ROOT = Path(r"C:\AI\BillarLanzarote")
VOLCANIC = ROOT / "addons" / "obs_overlays_v1_1" / "overlays" / "volcanic"
NEUTRAL = ROOT / "addons" / "obs_overlays_v1_1" / "overlays" / "neutral"

def group_files(folder: Path):
    groups = {"long": [], "thin": [], "square": [], "compact": [], "other": []}
    if folder.exists():
        for p in sorted(folder.glob("*.html")):
            name = p.name.lower()
            placed = False
            for size in ("long","thin","square","compact"):
                if f"_{size}.html" in name or f"_{size}_" in name:
                    groups[size].append(p.name)
                    placed = True
                    break
            if not placed:
                groups["other"].append(p.name)
    return groups

def section(title, groups):
    out = [f"<h2>{html.escape(title)}</h2>"]
    for gname, files in groups.items():
        if not files:
            continue
        out.append(f"<h3>{html.escape(gname)}</h3><ul>")
        for f in files:
            out.append(f"<li><code>{html.escape(f)}</code></li>")
        out.append("</ul>")
    return "".join(out)

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Overlay Preview Index</title>
<style>body{font-family:Arial;background:#111;color:#eee;padding:20px}code{background:#222;padding:2px 6px;border-radius:6px}h1{color:#ff3b30}h2{margin-top:28px}</style>
</head><body><h1>Overlay Preview Index v1.1</h1>%s%s</body></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        volc = group_files(VOLCANIC)
        neut = group_files(NEUTRAL)
        body = (PAGE % (section("Volcanic", volc), section("Neutral", neut))).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print("Overlay Preview Index v1.1 -> http://127.0.0.1:8793")
    HTTPServer(("127.0.0.1", 8793), Handler).serve_forever()
