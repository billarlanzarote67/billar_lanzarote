
import os, sqlite3, requests, re
ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
PHOTOS = os.path.join(ROOT, "data", "photos")
os.makedirs(PHOTOS, exist_ok=True)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name, COALESCE(photo_url,'') FROM players ORDER BY name")
rows = cur.fetchall()
conn.close()

print("Players:", len(rows))
for name, url in rows:
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', name)
    if not url:
        print("No photo URL for", name)
        continue
    ext = ".jpg"
    out = os.path.join(PHOTOS, safe + ext)
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        print("Saved", out)
    except Exception as e:
        print("Photo fetch failed:", name, e)
