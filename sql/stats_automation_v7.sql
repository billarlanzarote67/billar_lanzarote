
CREATE TABLE IF NOT EXISTS player_media (
  player_id TEXT PRIMARY KEY,
  cuescore_player_id TEXT,
  photo_url TEXT,
  local_photo_path TEXT,
  local_fallback_photo_path TEXT,
  photo_source TEXT,
  last_photo_sync_ts_utc TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS player_aliases (
  alias_id TEXT PRIMARY KEY,
  player_id TEXT NOT NULL,
  alias_name TEXT NOT NULL,
  source_type TEXT,
  created_ts_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alias_suggestions (
  suggestion_id TEXT PRIMARY KEY,
  player_name_a TEXT NOT NULL,
  player_name_b TEXT NOT NULL,
  reason TEXT,
  confidence REAL,
  status TEXT NOT NULL,
  created_ts_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS elo_ratings (
  player_id TEXT PRIMARY KEY,
  elo_rating REAL NOT NULL,
  seeded_from TEXT,
  last_updated_ts_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS importer_run_log (
  run_id TEXT PRIMARY KEY,
  ts_utc TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_url TEXT,
  status TEXT NOT NULL,
  details_json TEXT
);

CREATE TABLE IF NOT EXISTS tournament_participant_stats (
  row_id TEXT PRIMARY KEY,
  tournament_id TEXT NOT NULL,
  tournament_name TEXT,
  cuescore_player_id TEXT,
  display_name TEXT,
  nationality TEXT,
  matches_played INTEGER,
  matches_won INTEGER,
  matches_lost INTEGER,
  frames_won INTEGER,
  frames_lost INTEGER,
  win_percentage REAL,
  imported_ts_utc TEXT NOT NULL,
  raw_json TEXT
);
