"""Durable local outbox; deliberately no external delivery or broker calls."""
import hashlib
import json
from pathlib import Path
import sqlite3


class AlertStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS alerts (
                event_id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'LOCAL_PENDING'
            )""")

    def put(self, key, created_at, kind, payload):
        event_id = hashlib.sha256(key.encode()).hexdigest()
        with sqlite3.connect(self.path) as db:
            cur = db.execute("INSERT OR IGNORE INTO alerts(event_id,created_at,kind,payload) VALUES(?,?,?,?)",
                             (event_id, created_at, kind, json.dumps(payload, sort_keys=True)))
            return cur.rowcount == 1

    def rows(self):
        with sqlite3.connect(self.path) as db:
            return [dict(zip(["event_id", "created_at", "kind", "payload", "status"], r))
                    for r in db.execute("SELECT * FROM alerts ORDER BY created_at,event_id")]
