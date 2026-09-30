-- Feature requests. Nothing is public until it is approved.
CREATE TABLE requests (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT    NOT NULL,
  detail      TEXT    NOT NULL DEFAULT '',
  email       TEXT    NOT NULL DEFAULT '',
  status      TEXT    NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | planned | shipped
  votes       INTEGER NOT NULL DEFAULT 1,           -- the person asking counts as the first vote
  ip_hash     TEXT    NOT NULL,
  created_at  INTEGER NOT NULL
);
CREATE INDEX requests_public ON requests (status, votes DESC);
CREATE INDEX requests_by_ip  ON requests (ip_hash, created_at);

CREATE TABLE votes (
  request_id  INTEGER NOT NULL,
  voter       TEXT    NOT NULL,
  created_at  INTEGER NOT NULL,
  PRIMARY KEY (request_id, voter)
);
