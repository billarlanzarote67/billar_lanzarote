import os, sqlite3, json
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
LOG = os.path.join(ROOT, "logs", "rebuild_player_data_from_all_sources_v1.log")
OUT = os.path.join(ROOT, "data", "player_source_audit_v1.json")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(cur, name):
    return bool(cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)).fetchone())

def get_tables(cur):
    return [r["name"] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

def get_columns(cur, table):
    try:
        return [r["name"] if "name" in r.keys() else r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    except Exception:
        return []

def ensure_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player_profiles (
        player_name TEXT PRIMARY KEY,
        matches_played INTEGER DEFAULT 0,
        matches_won INTEGER DEFAULT 0,
        matches_lost INTEGER DEFAULT 0,
        frames_won INTEGER DEFAULT 0,
        frames_lost INTEGER DEFAULT 0,
        win_pct REAL DEFAULT 0,
        updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS imported_player_cache (
        player_name TEXT PRIMARY KEY,
        source_table TEXT,
        source_column TEXT,
        source_status TEXT DEFAULT 'imported_only',
        updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP)""")

def discover_players(cur):
    names = {}
    candidate_tables = [
        "player_profiles","player_match_history","matches_final","players","tournament_players",
        "imported_players","cuescore_players","player_aliases","player_summary",
        "tournament_matches","imported_matches","matches","match_results",
        "raw_tournament_players","raw_tournament_matches"
    ]
    for table in get_tables(cur):
        if table not in candidate_tables and not any(x in table.lower() for x in ["player", "match", "tournament", "cuescore"]):
            continue
        cols = get_columns(cur, table)
        for col in ["player_name","name","full_name","display_name","player_a","player_b","opponent_name","alias"]:
            if col not in cols:
                continue
            try:
                for r in cur.execute(f"SELECT DISTINCT {col} AS n FROM {table} WHERE {col} IS NOT NULL AND TRIM({col}) != ''").fetchall():
                    name = str(r["n"]).strip()
                    if len(name) < 2:
                        continue
                    if name.lower() in {"breaking","runouts","runout","timeout","timeouts","end match","ball in hand","match statistics","challengematch","mesa 1","mesa 2"}:
                        continue
                    names.setdefault(name, {"sources":[]})
                    names[name]["sources"].append({"table": table, "column": col})
            except Exception:
                pass
    return names

def rebuild_profiles(cur):
    imported = {r["player_name"]: True for r in cur.execute("SELECT player_name FROM imported_player_cache").fetchall()} if table_exists(cur, "imported_player_cache") else {}
    stats = {}
    if table_exists(cur, "player_match_history"):
        cols = set(get_columns(cur, "player_match_history"))
        if {"player_name","did_win","frames_won","frames_lost"}.issubset(cols):
            for r in cur.execute("SELECT player_name,did_win,frames_won,frames_lost FROM player_match_history WHERE player_name IS NOT NULL AND TRIM(player_name) != ''").fetchall():
                name = str(r["player_name"]).strip()
                stats.setdefault(name, {"matches_played":0,"matches_won":0,"matches_lost":0,"frames_won":0,"frames_lost":0})
                stats[name]["matches_played"] += 1
                stats[name]["matches_won"] += 1 if int(r["did_win"] or 0) == 1 else 0
                stats[name]["matches_lost"] += 0 if int(r["did_win"] or 0) == 1 else 1
                stats[name]["frames_won"] += int(r["frames_won"] or 0)
                stats[name]["frames_lost"] += int(r["frames_lost"] or 0)
    cur.execute("DELETE FROM player_profiles")
    for name in sorted(set(imported.keys()) | set(stats.keys())):
        s = stats.get(name, {"matches_played":0,"matches_won":0,"matches_lost":0,"frames_won":0,"frames_lost":0})
        win_pct = round((s["matches_won"] * 100.0 / s["matches_played"]), 2) if s["matches_played"] > 0 else 0
        cur.execute("""INSERT INTO player_profiles
            (player_name,matches_played,matches_won,matches_lost,frames_won,frames_lost,win_pct,updated_ts_utc)
            VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
            (name, s["matches_played"], s["matches_won"], s["matches_lost"], s["frames_won"], s["frames_lost"], win_pct))

def main():
    if not os.path.exists(DB):
        print(f"DB not found: {DB}")
        return
    conn = connect()
    cur = conn.cursor()
    ensure_tables(cur)
    names = discover_players(cur)
    cur.execute("DELETE FROM imported_player_cache")
    for name, meta in names.items():
        src = meta["sources"][0] if meta["sources"] else {"table":"unknown","column":"unknown"}
        cur.execute("""INSERT INTO imported_player_cache
            (player_name,source_table,source_column,source_status,updated_ts_utc)
            VALUES (?,?,?,?,CURRENT_TIMESTAMP)""",
            (name, src["table"], src["column"], "imported_only"))
    conn.commit()
    rebuild_profiles(cur)
    conn.commit()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "db": DB,
            "tables": get_tables(cur),
            "discovered_player_count": len(names),
            "players": sorted(list(names.keys()))
        }, f, ensure_ascii=False, indent=2)
    log(f"Imported/cache players discovered: {len(names)}")
    log("Rebuilt player_profiles from imported + local sources")
    conn.close()

if __name__ == "__main__":
    main()
