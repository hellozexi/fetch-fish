"""SQLite cache for WeRead books."""
import sqlite3
from pathlib import Path
from typing import Optional
import config

DB_FILE = config.CACHE_DIR / "weread.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            cover_url TEXT,
            updated_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS chapters (
            id TEXT PRIMARY KEY,
            book_id TEXT,
            idx INTEGER,
            title TEXT,
            start_offset INTEGER
        );
        CREATE TABLE IF NOT EXISTS content (
            chapter_id TEXT,
            offset INTEGER,
            text TEXT,
            PRIMARY KEY (chapter_id, offset)
        );
    """)
    db.commit()
    return db