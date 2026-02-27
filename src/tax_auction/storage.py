from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import DiscoveredArtifact, ListingRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  captured_at TEXT NOT NULL,
  source_url TEXT NOT NULL,
  html_path TEXT NOT NULL,
  html_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  link_text TEXT NOT NULL,
  file_type TEXT NOT NULL,
  local_path TEXT,
  FOREIGN KEY(snapshot_id) REFERENCES snapshot(id)
);

CREATE TABLE IF NOT EXISTS listing (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL,
  apn TEXT NOT NULL,
  situs_address TEXT,
  minimum_bid REAL,
  source_artifact_url TEXT NOT NULL,
  FOREIGN KEY(snapshot_id) REFERENCES snapshot(id)
);

CREATE TABLE IF NOT EXISTS listing_change_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_id INTEGER NOT NULL,
  apn TEXT NOT NULL,
  change_type TEXT NOT NULL,
  FOREIGN KEY(snapshot_id) REFERENCES snapshot(id)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert_snapshot(
    conn: sqlite3.Connection,
    captured_at: str,
    source_url: str,
    html_path: str,
    html_sha256: str,
) -> int:
    cur = conn.execute(
        "INSERT INTO snapshot(captured_at, source_url, html_path, html_sha256) VALUES (?, ?, ?, ?)",
        (captured_at, source_url, html_path, html_sha256),
    )
    conn.commit()
    return int(cur.lastrowid)


def insert_artifacts(
    conn: sqlite3.Connection,
    snapshot_id: int,
    artifacts: Iterable[DiscoveredArtifact],
    local_path_by_url: dict[str, str],
) -> None:
    conn.executemany(
        "INSERT INTO artifact(snapshot_id, url, link_text, file_type, local_path) VALUES (?, ?, ?, ?, ?)",
        [
            (
                snapshot_id,
                a.url,
                a.link_text,
                a.file_type,
                local_path_by_url.get(a.url),
            )
            for a in artifacts
        ],
    )
    conn.commit()


def insert_listings(conn: sqlite3.Connection, snapshot_id: int, listings: Iterable[ListingRecord]) -> None:
    conn.executemany(
        "INSERT INTO listing(snapshot_id, apn, situs_address, minimum_bid, source_artifact_url) VALUES (?, ?, ?, ?, ?)",
        [
            (
                snapshot_id,
                l.apn,
                l.situs_address,
                l.minimum_bid,
                l.source_artifact_url,
            )
            for l in listings
        ],
    )
    conn.commit()


def get_previous_snapshot_id(conn: sqlite3.Connection, current_snapshot_id: int) -> int | None:
    row = conn.execute(
        "SELECT id FROM snapshot WHERE id < ? ORDER BY id DESC LIMIT 1", (current_snapshot_id,)
    ).fetchone()
    return int(row[0]) if row else None


def get_snapshot_apns(conn: sqlite3.Connection, snapshot_id: int) -> set[str]:
    rows = conn.execute("SELECT DISTINCT apn FROM listing WHERE snapshot_id = ?", (snapshot_id,)).fetchall()
    return {r[0] for r in rows}


def insert_change_events(conn: sqlite3.Connection, snapshot_id: int, change_events: list[tuple[str, str]]) -> None:
    conn.executemany(
        "INSERT INTO listing_change_event(snapshot_id, apn, change_type) VALUES (?, ?, ?)",
        [(snapshot_id, apn, change_type) for apn, change_type in change_events],
    )
    conn.commit()
