
import os
from flask import Flask, send_from_directory
ROOT = r"C:\AI\BillarLanzarote"
WEB = os.path.join(ROOT, "web_ui", "overlay_selector_v2")
app = Flask(__name__, static_folder=WEB, static_url_path="")
@app.route("/")
def home():
    return send_from_directory(WEB, "index.html")
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8795, debug=False)
