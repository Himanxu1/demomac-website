-- Who downloaded the app: the email asked for before the DMG starts.
-- One row per address; a repeat download bumps `downloads` and `last_at`.
CREATE TABLE downloaders (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  email       TEXT    NOT NULL UNIQUE,
  source      TEXT    NOT NULL DEFAULT '',  -- the button's data-event, e.g. download-hero
  page        TEXT    NOT NULL DEFAULT '',  -- the page it was clicked on
  country     TEXT    NOT NULL DEFAULT '',
  ip_hash     TEXT    NOT NULL,
  downloads   INTEGER NOT NULL DEFAULT 1,
  created_at  INTEGER NOT NULL,
  last_at     INTEGER NOT NULL
);
CREATE INDEX downloaders_recent ON downloaders (created_at DESC);
CREATE INDEX downloaders_by_ip  ON downloaders (ip_hash, last_at);
