"""SQLite storage for Ravi OS. One file, created on first run."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("RAVI_OS_DB", Path(__file__).resolve().parent.parent / "data" / "ravi_os.db"))

MODULES = {
    "ideas": "Ideas Inbox",
    "projects": "Project Tracker",
    "research": "Research Vault",
    "prompts": "Prompt Library",
    "stocks": "Stock Watchlist",
    "sanskrit": "Sanskrit / Hindu Thought",
    "animals": "Animal Welfare",
    "learning": "Learning Roadmap",
}
STATUSES = ["inbox", "active", "someday", "done", "archived"]
TAG_KINDS = ["domain", "urgency", "monetization", "spiritual", "public_good", "difficulty", "custom"]

DEFAULT_PROFILE = (
    "Data scientist with Python, PySpark, SQL and ML experience. "
    "Loves deep research, AI websites, Sanskrit/Hindu thought, stock analysis, "
    "animal welfare, and practical monetizable tools. Building for long-term "
    "personal growth and making the world better."
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  module TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'inbox',
  source TEXT NOT NULL DEFAULT 'manual',
  meta TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_items_module ON items(module);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);

CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  value TEXT NOT NULL,
  UNIQUE(item_id, kind, value)
);

CREATE TABLE IF NOT EXISTS scores (
  item_id INTEGER PRIMARY KEY REFERENCES items(id) ON DELETE CASCADE,
  long_term_value INTEGER,
  ease INTEGER,
  monetization INTEGER,
  personal_fit INTEGER,
  defensibility INTEGER,
  impact INTEGER,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  done INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  done_at TEXT
);

CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL UNIQUE,
  wins TEXT NOT NULL DEFAULT '',
  blockers TEXT NOT NULL DEFAULT '',
  gratitude TEXT NOT NULL DEFAULT '',
  tomorrow TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con


def get_setting(con: sqlite3.Connection, key: str, default):
    row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return json.loads(row["value"]) if row else default


def set_setting(con: sqlite3.Connection, key: str, value) -> None:
    con.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, json.dumps(value)),
    )
    con.commit()
