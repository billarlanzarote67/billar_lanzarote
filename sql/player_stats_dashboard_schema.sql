
CREATE TABLE IF NOT EXISTS player_media (
  player_id TEXT PRIMARY KEY,
  cuescore_player_id TEXT,
  photo_url TEXT,
  local_photo_path TEXT,
  last_photo_sync_ts_utc TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS importer_queue_log (
  queue_id TEXT PRIMARY KEY,
  queued_ts_utc TEXT NOT NULL,
  table_id TEXT,
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL,
  queue_status TEXT NOT NULL,
  result_json TEXT
);
