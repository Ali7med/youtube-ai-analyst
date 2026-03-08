CREATE TABLE IF NOT EXISTS searches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  order_by TEXT,
  results_count INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id TEXT UNIQUE NOT NULL,
  search_id INTEGER REFERENCES searches(id),
  title TEXT, summary TEXT, notes TEXT,
  thumbnail TEXT, rate REAL, label TEXT,
  link TEXT, views INTEGER, likes INTEGER,
  comments INTEGER, sentiment TEXT, content_type TEXT,
  topics TEXT, channel_id TEXT, published_at TEXT,
  duration TEXT, hook TEXT, cta TEXT,
  target_audience TEXT, content_gap TEXT,
  processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  video_id TEXT UNIQUE NOT NULL,
  text TEXT, source TEXT, language TEXT,
  segment_count INTEGER,
  cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, query TEXT, schedule TEXT,
  max_results INTEGER DEFAULT 10,
  auto_sheet BOOLEAN DEFAULT 1,
  notify_telegram BOOLEAN DEFAULT 0,
  last_run DATETIME, next_run DATETIME,
  status TEXT DEFAULT 'active',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel_id TEXT UNIQUE NOT NULL,
  name TEXT,
  subscribers INTEGER,
  total_views INTEGER,
  upload_count INTEGER,
  last_checked DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,
  target TEXT NOT NULL,
  name TEXT,
  last_checked DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
