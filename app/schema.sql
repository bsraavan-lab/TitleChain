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

-- A case holds N certificates. That is not a future feature: ec5 in the sample
-- corpus is two certificates for one property inside one PDF, and the whole
-- missing-document workflow is "add another one of these".
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
  page_count           INTEGER,
  uploaded_at          TEXT,
  -- which DocumentRequest this certificate was fetched to fill. Set when the
  -- advocate drops a file on a request card, so the app can report whether it
  -- actually filled the hole it was ordered for.
  fulfils_request_key  TEXT,
  page_from            INTEGER,         -- bundle split: this certificate's pages
  page_to              INTEGER          -- within the uploaded file
);

-- Append-only, exactly like corrections. The current state of a review is the
-- latest row for that finding_key; the history is shown in the report. An
-- advocate who marks something reviewed and then unmarks it has that sequence in
-- the record — in a file supporting a legal opinion, a destructive edit is a
-- defect.
CREATE TABLE IF NOT EXISTS reviews (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id      INTEGER NOT NULL REFERENCES cases(id),
  finding_key  TEXT    NOT NULL,        -- subject-scoped; survives re-derivation
  state        TEXT    NOT NULL,        -- reviewed | accepted | awaiting_document | open
  note         TEXT,
  actor        TEXT    NOT NULL DEFAULT 'meena',
  created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS reviews_case ON reviews(case_id, finding_key);

-- A log of what the rulebook SAID, and when. This does not violate "derived
-- state is disposable": findings are still rebuilt from scratch on every
-- derivation. What is recorded here is the event — at time T the rulebook
-- reported this set of keys — and it is the only way "which findings did this
-- upload resolve?" can be answered by a diff rather than by a guess.
CREATE TABLE IF NOT EXISTS derivations (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id          INTEGER NOT NULL REFERENCES cases(id),
  at               TEXT    NOT NULL,
  rulebook_version TEXT    NOT NULL,
  trigger          TEXT,                -- upload | merge | correction
  ec_id            INTEGER,             -- the certificate that triggered it, if any
  open_keys        TEXT    NOT NULL,    -- JSON array of open finding keys
  all_keys         TEXT    NOT NULL     -- JSON array of every key reported
);

-- The cost ledger. One row per real HTTP request, recorded fact.
CREATE TABLE IF NOT EXISTS api_calls (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id     INTEGER,
  ec_id       INTEGER,
  stage       TEXT,                     -- digitise | header | entries | transliterate | speak
  model       TEXT,
  ladder_rung TEXT,                     -- "105b/low+s1" — retries stay visible
  pages       INTEGER DEFAULT 0,
  tokens_in   INTEGER DEFAULT 0,
  tokens_out  INTEGER DEFAULT 0,
  chars       INTEGER DEFAULT 0,
  cached      INTEGER DEFAULT 0,
  ms          INTEGER DEFAULT 0,
  created_at  TEXT
);
CREATE INDEX IF NOT EXISTS api_calls_case ON api_calls(case_id);

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
