import os
import sqlite3
import time
from datetime import datetime

ROOT = r"C:\AI\BillarLanzarote"
SOURCE_DB = os.path.join(ROOT, "database", "sqlite", "billar_lanzarote.sqlite")
TARGET_DB = os.path.join(ROOT, "data", "billar_lanzarote.sqlite3")
LOG_PATH = os.path.join(ROOT, "logs", "merge_legacy_db_into_canonical_v1.log")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(message: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_conn(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def ensure_target_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS imported_player_cache (
            player_name TEXT PRIMARY KEY,
            source_table TEXT,
            source_column TEXT,
            source_status TEXT DEFAULT 'merged_import',
            cuescore_player_id TEXT,
            cuescore_profile_url TEXT,
            photo_url TEXT,
            updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for stmt in [
        "ALTER TABLE imported_player_cache ADD COLUMN cuescore_player_id TEXT",
        "ALTER TABLE imported_player_cache ADD COLUMN cuescore_profile_url TEXT",
        "ALTER TABLE imported_player_cache ADD COLUMN photo_url TEXT",
    ]:
        try:
            cur.execute(stmt)
        except sqlite3.OperationalError:
            pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS imported_match_cache (
            source_match_id TEXT PRIMARY KEY,
            source_table TEXT,
            player_a TEXT,
            player_b TEXT,
            winner TEXT,
            score TEXT,
            game_type_es TEXT,
            notes TEXT,
            imported_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_profiles (
            player_name TEXT PRIMARY KEY,
            matches_played INTEGER DEFAULT 0,
            matches_won INTEGER DEFAULT 0,
            matches_lost INTEGER DEFAULT 0,
            frames_won INTEGER DEFAULT 0,
            frames_lost INTEGER DEFAULT 0,
            win_pct REAL DEFAULT 0,
            updated_ts_utc DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def merge_value(existing, incoming):
    values = [v for v in (existing, incoming) if v not in (None, "", "None")]
    if not values:
        return 0
    try:
        return max(float(v) for v in values)
    except Exception:
        return values[-1]


def load_source_players(conn: sqlite3.Connection):
    if not table_exists(conn, "players"):
        return []
    sql = """
        SELECT
            p.display_name,
            p.player_id,
            s.matches_played,
            s.wins,
            s.losses,
            s.win_rate,
            s.frames_won,
            s.frames_lost,
            m.cuescore_player_id,
            m.cuescore_profile_url,
            media.photo_url
        FROM players p
        LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
        LEFT JOIN player_cuescore_map m ON m.player_id = p.player_id
        LEFT JOIN player_media media ON media.player_id = p.player_id
        WHERE p.display_name IS NOT NULL AND TRIM(p.display_name) != ''
        ORDER BY p.display_name ASC
    """
    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    merged = {}
    for row in rows:
        name = str(row.get("display_name") or "").strip()
        if not name:
            continue
        bucket = merged.setdefault(
            name,
            {
                "display_name": name,
                "matches_played": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0,
                "frames_won": 0,
                "frames_lost": 0,
                "cuescore_player_id": None,
                "cuescore_profile_url": None,
                "photo_url": None,
            },
        )
        for key in ("matches_played", "wins", "losses", "win_rate", "frames_won", "frames_lost"):
            bucket[key] = merge_value(bucket.get(key), row.get(key))
        for key in ("cuescore_player_id", "cuescore_profile_url", "photo_url"):
            bucket[key] = bucket.get(key) or row.get(key)
    return list(merged.values())


def merge_players(target: sqlite3.Connection, players) -> int:
    cur = target.cursor()
    merged_count = 0
    for row in players:
        name = row["display_name"]
        cur.execute(
            """
            INSERT INTO imported_player_cache(
                player_name, source_table, source_column, source_status,
                cuescore_player_id, cuescore_profile_url, photo_url, updated_ts_utc
            ) VALUES (?, 'players', 'display_name', 'merged_import', ?, ?, ?, ?)
            ON CONFLICT(player_name) DO UPDATE SET
                source_status=excluded.source_status,
                cuescore_player_id=COALESCE(excluded.cuescore_player_id, imported_player_cache.cuescore_player_id),
                cuescore_profile_url=COALESCE(excluded.cuescore_profile_url, imported_player_cache.cuescore_profile_url),
                photo_url=COALESCE(excluded.photo_url, imported_player_cache.photo_url),
                updated_ts_utc=excluded.updated_ts_utc
            """,
            (
                name,
                row.get("cuescore_player_id"),
                row.get("cuescore_profile_url"),
                row.get("photo_url"),
                utc_now(),
            ),
        )

        existing = cur.execute(
            """
            SELECT matches_played, matches_won, matches_lost, frames_won, frames_lost, win_pct
            FROM player_profiles WHERE player_name=?
            """,
            (name,),
        ).fetchone()
        matches_played = merge_value(existing["matches_played"] if existing else None, row.get("matches_played"))
        matches_won = merge_value(existing["matches_won"] if existing else None, row.get("wins"))
        matches_lost = merge_value(existing["matches_lost"] if existing else None, row.get("losses"))
        frames_won = merge_value(existing["frames_won"] if existing else None, row.get("frames_won"))
        frames_lost = merge_value(existing["frames_lost"] if existing else None, row.get("frames_lost"))
        win_pct = merge_value(existing["win_pct"] if existing else None, row.get("win_rate"))

        cur.execute(
            """
            INSERT INTO player_profiles(
                player_name, matches_played, matches_won, matches_lost,
                frames_won, frames_lost, win_pct, updated_ts_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(player_name) DO UPDATE SET
                matches_played=excluded.matches_played,
                matches_won=excluded.matches_won,
                matches_lost=excluded.matches_lost,
                frames_won=excluded.frames_won,
                frames_lost=excluded.frames_lost,
                win_pct=excluded.win_pct,
                updated_ts_utc=CURRENT_TIMESTAMP
            """,
            (
                name,
                int(matches_played or 0),
                int(matches_won or 0),
                int(matches_lost or 0),
                int(frames_won or 0),
                int(frames_lost or 0),
                float(win_pct or 0),
            ),
        )
        merged_count += 1
    target.commit()
    return merged_count


def merge_matches(source: sqlite3.Connection, target: sqlite3.Connection) -> int:
    if not table_exists(source, "match_results"):
        return 0
    rows = source.execute(
        """
        SELECT
            COALESCE(cuescore_match_id, match_id) AS source_match_id,
            player1_name,
            player2_name,
            winner_name,
            score1,
            score2,
            source_type,
            played_ts_utc
        FROM match_results
        """
    ).fetchall()
    cur = target.cursor()
    count = 0
    for row in rows:
        source_match_id = str(row["source_match_id"] or "").strip()
        if not source_match_id:
            continue
        score_a = row["score1"] if row["score1"] is not None else ""
        score_b = row["score2"] if row["score2"] is not None else ""
        score = f"{score_a}-{score_b}" if score_a != "" or score_b != "" else None
        cur.execute(
            """
            INSERT INTO imported_match_cache(
                source_match_id, source_table, player_a, player_b, winner,
                score, game_type_es, notes, imported_ts_utc
            ) VALUES (?, 'match_results', ?, ?, ?, ?, NULL, ?, ?)
            ON CONFLICT(source_match_id) DO UPDATE SET
                player_a=excluded.player_a,
                player_b=excluded.player_b,
                winner=excluded.winner,
                score=excluded.score,
                notes=excluded.notes,
                imported_ts_utc=excluded.imported_ts_utc
            """,
            (
                source_match_id,
                row["player1_name"],
                row["player2_name"],
                row["winner_name"],
                score,
                row["source_type"] or "imported_from_legacy",
                row["played_ts_utc"] or utc_now(),
            ),
        )
        count += 1
    target.commit()
    return count


def main() -> None:
    if not os.path.exists(SOURCE_DB):
        raise FileNotFoundError(f"Source DB not found: {SOURCE_DB}")
    os.makedirs(os.path.dirname(TARGET_DB), exist_ok=True)
    source = get_conn(SOURCE_DB)
    target = get_conn(TARGET_DB)
    ensure_target_schema(target)

    players = load_source_players(source)
    merged_players = merge_players(target, players)
    merged_matches = merge_matches(source, target)

    log(f"Source DB: {SOURCE_DB}")
    log(f"Target DB: {TARGET_DB}")
    log(f"Merged players: {merged_players}")
    log(f"Merged imported matches: {merged_matches}")

    source.close()
    target.close()


if __name__ == "__main__":
    main()
