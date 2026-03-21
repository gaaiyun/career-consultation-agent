from __future__ import annotations

import sqlite3

from src.config.settings import Settings


def get_connection(settings: Settings) -> sqlite3.Connection:
    settings.ensure_directories()
    connection = sqlite3.connect(settings.sqlite_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(settings: Settings) -> None:
    with get_connection(settings) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
              case_id TEXT PRIMARY KEY,
              client_alias TEXT NOT NULL,
              source_text TEXT NOT NULL,
              current_stage TEXT NOT NULL,
              tags_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_versions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              case_id TEXT NOT NULL,
              stage_name TEXT NOT NULL,
              version_no INTEGER NOT NULL,
              input_payload TEXT NOT NULL,
              output_payload TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prompt_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              case_id TEXT NOT NULL,
              stage_name TEXT NOT NULL,
              prompt_name TEXT NOT NULL,
              model TEXT NOT NULL,
              temperature REAL NOT NULL,
              input_summary TEXT NOT NULL,
              raw_response TEXT NOT NULL,
              success INTEGER NOT NULL,
              latency_ms INTEGER NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exports (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              case_id TEXT NOT NULL,
              export_type TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
