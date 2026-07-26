-- TitleChain — persistence only. SQLite never computes; derive() does.
-- Executed at startup, idempotent.

CREATE TABLE IF NOT EXISTS cases (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  advocate_id      TEXT    NOT NULL DEFAULT 'meena',
  property_key     TEXT,                -- "Puliyampatti · S.No 95/2 +4"
  status           TEXT    NOT NULL,    -- QUEUED | READING | TYPING | DERIVING | READY | FAILED | REFUSED
  status_detail    TEXT,                -- honest, user-facing: "Reading page 3 of 12"
  pages_total      INTEGER DEFAULT 0,
  pages_done       INTEGER DEFAULT 0,
  rulebook_version TEXT    NOT NULL DEFAULT 'v1.0',
  -- JSON list of the checks that actually ran and failed, e.g.
  -- ["a registration-entry table", "a declared entry count"]. NULL means we did
  -- not run them: the refusal screen must never claim a check it did not make.
  refusal_checks   TEXT,
  created_at       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS ec_documents (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id              INTEGER NOT NULL REFERENCES cases(id),
  filename             TEXT,
  file_path            TEXT,
  raster_dir           TEXT,            -- where page rasters/cached DI output live
  sro                  TEXT,
  village              TEXT,
  survey_nos           TEXT,            -- comma-joined, verbatim
  search_start         TEXT,
  search_end           TEXT,
  issue_date           TEXT,
  declared_entry_count INTEGER,
  page_count           INTEGER
);

CREATE TABLE IF NOT EXISTS entries (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  ec_id              INTEGER NOT NULL REFERENCES ec_documents(id),
  sr_no              INTEGER,
  doc_no             TEXT,
  doc_year           INTEGER,
  date_execution     TEXT,
  date_presentation  TEXT,
  date_registration  TEXT,
  nature             TEXT,
  volume_page        TEXT,
  consideration_value TEXT,
  market_value       TEXT,
  remarks            TEXT,
  pr_numbers         TEXT,              -- "4451/2005,4453/2005,..."
  survey_nos         TEXT,
  page_num           INTEGER,
  block_id           TEXT,
  block_confidence   REAL,
  bbox               TEXT               -- "x1,y1,x2,y2" straight from stage-① JSON
);

CREATE TABLE IF NOT EXISTS parties (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id    INTEGER NOT NULL REFERENCES entries(id),
  role        TEXT,                     -- executant | claimant
  name_native TEXT,
  name_roman  TEXT,
  role_marker TEXT,
  cluster_id  TEXT
);

CREATE TABLE IF NOT EXISTS corrections (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id   INTEGER NOT NULL REFERENCES entries(id),
  field      TEXT    NOT NULL,
  old_value  TEXT,
  new_value  TEXT,
  actor      TEXT    NOT NULL DEFAULT 'meena',
  created_at TEXT    NOT NULL
);

-- Append-only. An "undo" is a NEW correction that reverts, never a delete:
-- in a record supporting a legal opinion, a destructive edit is a defect.

CREATE TABLE IF NOT EXISTS unread_chunks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  ec_id      INTEGER NOT NULL REFERENCES ec_documents(id),
  page_from  INTEGER,
  page_to    INTEGER,
  reason     TEXT
);
