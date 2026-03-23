import sqlite3, os
DB_PATH = r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, photo_url TEXT, created_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, table_key TEXT, table_name TEXT, player_a TEXT, player_b TEXT, winner TEXT, score_a INTEGER, score_b INTEGER, challenge_url TEXT, source TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS match_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, table_key TEXT, player_a TEXT, player_b TEXT, score_a INTEGER, score_b INTEGER, challenge_url TEXT, source TEXT, snapshot_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)")
conn.commit(); conn.close(); print("DB created at:", DB_PATH)
