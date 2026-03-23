
import sqlite3, uuid, time
from difflib import SequenceMatcher
from stats_automation_common import db

def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

con = db(); cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS alias_suggestions(
  suggestion_id TEXT PRIMARY KEY, player_name_a TEXT NOT NULL, player_name_b TEXT NOT NULL,
  reason TEXT, confidence REAL, status TEXT NOT NULL, created_ts_utc TEXT NOT NULL
)""")
cur.execute("SELECT display_name FROM players ORDER BY display_name")
names = [r[0] for r in cur.fetchall() if r[0]]
added = 0
for i in range(len(names)):
    for j in range(i+1, len(names)):
        a, b = names[i], names[j]
        score = SequenceMatcher(None, a.lower(), b.lower()).ratio()
        if score >= 0.86 and a != b:
            try:
                cur.execute("""INSERT INTO alias_suggestions(suggestion_id, player_name_a, player_name_b, reason, confidence, status, created_ts_utc)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (str(uuid.uuid4()), a, b, "name_similarity", score, "suggested", utc_now()))
                added += 1
            except sqlite3.Error:
                pass
con.commit(); con.close()
print({"added": added})
