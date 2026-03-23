import os, sqlite3

CANDIDATES = [
    r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db",
    r"C:\AI\BillarLanzarote\data\billar_lanzarote.sqlite3",
    r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite",
]

def score_db(path:str):
    if not os.path.exists(path):
        return (-1, 0, "missing")
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        if 'players' not in tables:
            con.close(); return (0, len(tables), 'no players table')
        cur.execute('SELECT COUNT(*) FROM players')
        players = cur.fetchone()[0]
        bonus = 0
        for t in ('player_profile_stats','player_cuescore_map','player_media','match_results','tournament_player_results'):
            if t in tables: bonus += 1
        con.close()
        return (1000 + players*10 + bonus, players, 'ok')
    except Exception as e:
        return (1, 0, f'error: {e}')

def find_best_db():
    scored = [(score_db(p), p) for p in CANDIDATES]
    scored.sort(key=lambda x: x[0][0], reverse=True)
    best_score, best_path = scored[0]
    return best_path, scored

if __name__ == '__main__':
    best, scored = find_best_db()
    print('BEST=', best)
    for s,p in scored:
        print(s, p)
