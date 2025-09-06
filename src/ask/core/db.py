"""
SQLite schema and helpers for the A-S-K glyph dataset.

This module intentionally uses the Python standard library (sqlite3)
for zero-dependency setup. It provides:

- get_connection(db_path): returns a sqlite3.Connection with pragmas
- create_schema(conn): creates all tables and indexes if not exist

Tables are aligned with the normalized accessors in src/ask/merged_glyphs.py
so the ETL can be straightforward and idempotent.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "glyphs.db"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    # Pragmas for reliability and speed on local dev
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def _exec_many(conn: sqlite3.Connection, statements: Iterable[str]) -> None:
    cur = conn.cursor()
    for stmt in statements:
        cur.execute(stmt)
    conn.commit()


def create_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not already exist."""
    tables = [
        # Core lookup tables
        """
        CREATE TABLE IF NOT EXISTS vowels (
            vowel TEXT PRIMARY KEY
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS payloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vowel TEXT NOT NULL,
            type TEXT,
            tag TEXT,
            principle TEXT,
            confidence REAL,
            FOREIGN KEY (vowel) REFERENCES vowels(vowel)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS operators (
            glyph TEXT PRIMARY KEY,
            op TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS complete_operators (
            glyph TEXT PRIMARY KEY,
            principle TEXT,
            confidence REAL,
            FOREIGN KEY (glyph) REFERENCES operators(glyph) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS clusters (
            cluster TEXT PRIMARY KEY
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS cluster_ops (
            cluster TEXT NOT NULL,
            op TEXT NOT NULL,
            PRIMARY KEY (cluster, op),
            FOREIGN KEY (cluster) REFERENCES clusters(cluster) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS enhanced_clusters (
            cluster TEXT PRIMARY KEY,
            gloss TEXT,
            confidence REAL,
            FOREIGN KEY (cluster) REFERENCES clusters(cluster) ON DELETE CASCADE
        );
        """,
        # Fields and tags
        """
        CREATE TABLE IF NOT EXISTS glyph_fields (
            glyph TEXT PRIMARY KEY
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS glyph_field_tags (
            glyph TEXT NOT NULL,
            tag TEXT NOT NULL,
            confidence REAL,
            evidence_count INTEGER,
            PRIMARY KEY (glyph, tag),
            FOREIGN KEY (glyph) REFERENCES glyph_fields(glyph) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS glyph_field_tag_contexts (
            glyph TEXT NOT NULL,
            tag TEXT NOT NULL,
            context TEXT NOT NULL,
            PRIMARY KEY (glyph, tag, context),
            FOREIGN KEY (glyph, tag) REFERENCES glyph_field_tags(glyph, tag) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS glyph_position_prefs (
            glyph TEXT NOT NULL,
            position TEXT NOT NULL,
            name TEXT NOT NULL,
            score REAL,
            PRIMARY KEY (glyph, position, name),
            FOREIGN KEY (glyph) REFERENCES glyph_fields(glyph) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS glyph_cluster_behaviors (
            glyph TEXT NOT NULL,
            cluster TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (glyph, cluster),
            FOREIGN KEY (glyph) REFERENCES glyph_fields(glyph) ON DELETE CASCADE
        );
        """,
        # Other structures
        """
        CREATE TABLE IF NOT EXISTS tag_associations (
            tag TEXT PRIMARY KEY,
            value TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS named_payloads (
            name TEXT PRIMARY KEY,
            type TEXT,
            tag TEXT,
            principle TEXT,
            features TEXT,
            confidence REAL
        );
        """,
    ]

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_payloads_vowel ON payloads(vowel);",
        "CREATE INDEX IF NOT EXISTS idx_operators_op ON operators(op);",
        "CREATE INDEX IF NOT EXISTS idx_cluster_ops_op ON cluster_ops(op);",
        "CREATE INDEX IF NOT EXISTS idx_gft_tag ON glyph_field_tags(tag);",
        "CREATE INDEX IF NOT EXISTS idx_gpp_position ON glyph_position_prefs(position);",
    ]

    _exec_many(conn, tables + indexes)


__all__ = ["get_connection", "create_schema", "DEFAULT_DB_PATH"]
