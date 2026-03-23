
CREATE TABLE IF NOT EXISTS players (
  player_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  created_ts_utc TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS player_cuescore_map (
  player_id TEXT NOT NULL,
  cuescore_player_id TEXT NOT NULL,
  cuescore_profile_url TEXT,
  cuescore_display_name TEXT,
  last_verified_ts_utc TEXT,
  PRIMARY KEY (player_id, cuescore_player_id)
);

CREATE TABLE IF NOT EXISTS cuescore_import_raw (
  import_id TEXT PRIMARY KEY,
  imported_ts_utc TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_url TEXT NOT NULL,
  cuescore_match_id TEXT,
  cuescore_player_id TEXT,
  raw_html_path TEXT,
  screenshot_path TEXT,
  raw_json TEXT,
  parse_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS match_results (
  match_id TEXT PRIMARY KEY,
  cuescore_match_id TEXT,
  player1_id TEXT,
  player2_id TEXT,
  player1_name TEXT,
  player2_name TEXT,
  score1 INTEGER,
  score2 INTEGER,
  winner_player_id TEXT,
  winner_name TEXT,
  played_ts_utc TEXT,
  source_type TEXT,
  raw_html_path TEXT,
  screenshot_path TEXT
);

CREATE TABLE IF NOT EXISTS player_profile_stats (
  player_id TEXT PRIMARY KEY,
  cuescore_player_id TEXT,
  matches_played INTEGER,
  wins INTEGER,
  losses INTEGER,
  win_rate REAL,
  innings_average REAL,
  runouts INTEGER,
  lag_wins INTEGER,
  frame_win_average REAL,
  points INTEGER,
  last_match_ts_utc TEXT,
  last_import_ts_utc TEXT,
  stats_json TEXT
);
