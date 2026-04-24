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
            expected_keywords TEXT DEFAULT '',
            system_prompt TEXT DEFAULT '',
            eval_mode TEXT DEFAULT 'keyword',
            judge_model TEXT DEFAULT 'openai/gpt-4o-mini',
            judge_threshold REAL DEFAULT 7.0,
            judge_prompt TEXT DEFAULT '',
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
            judge_score REAL,
            judge_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
        );
        ''')
        
        # Migrations for existing databases
        for col, dtype, default in [
            ('system_prompt', 'TEXT', '""'),
            ('eval_mode', 'TEXT', '"keyword"'),
            ('judge_model', 'TEXT', '"openai/gpt-4o-mini"'),
            ('judge_threshold', 'REAL', '7.0'),
            ('judge_prompt', 'TEXT', '""'),
        ]:
            try:
                db.execute(f'ALTER TABLE test_cases ADD COLUMN {col} {dtype} DEFAULT {default}')
            except Exception:
                pass
        
        for col, dtype, default in [
            ('model', 'TEXT', 'NULL'),
            ('api_url', 'TEXT', 'NULL'),
            ('judge_score', 'REAL', 'NULL'),
            ('judge_reason', 'TEXT', 'NULL'),
        ]:
            try:
                db.execute(f'ALTER TABLE test_runs ADD COLUMN {col} {dtype} DEFAULT {default}')
            except Exception:
                pass