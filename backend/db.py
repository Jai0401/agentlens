import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'agentlens.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            input_prompt TEXT NOT NULL,
            expected_keywords TEXT,
            system_prompt TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_case_id INTEGER,
            status TEXT,
            output TEXT,
            tools_used TEXT,
            duration_ms INTEGER,
            error TEXT,
            model TEXT,
            api_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
        );
        ''')
        # Migration: add system_prompt column if missing (existing dbs)
        try:
            db.execute('ALTER TABLE test_cases ADD COLUMN system_prompt TEXT DEFAULT ""')
        except Exception:
            pass
        try:
            db.execute('ALTER TABLE test_runs ADD COLUMN model TEXT')
        except Exception:
            pass
        try:
            db.execute('ALTER TABLE test_runs ADD COLUMN api_url TEXT')
        except Exception:
            pass
        ''')
