from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
from db import init_db, get_db
from schemas import TestCaseCreate, TestRunRequest, AgentConfig

app = FastAPI(title="AgentLens", version="1.0.0")
init_db()

# --- Test Case CRUD ---
@app.post("/api/test-cases")
def create_test_case(data: TestCaseCreate):
    with get_db() as db:
        cursor = db.execute('''
            INSERT INTO test_cases (name, description, input_prompt, expected_keywords, system_prompt)
            VALUES (?, ?, ?, ?, ?)
        ''', (data.name, data.description, data.input_prompt, data.expected_keywords, data.system_prompt))
        db.commit()
        return {"id": cursor.lastrowid}

@app.get("/api/test-cases")
def list_test_cases(skip: int = 0, limit: int = 50):
    with get_db() as db:
        rows = db.execute('SELECT * FROM test_cases ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, skip)).fetchall()
        return [dict(r) for r in rows]

@app.put("/api/test-cases/{id}")
def update_test_case(id: int, data: TestCaseCreate):
    with get_db() as db:
        cursor = db.execute('''
            UPDATE test_cases SET name=?, description=?, input_prompt=?, expected_keywords=?, system_prompt=?
            WHERE id=?
        ''', (data.name, data.description, data.input_prompt, data.expected_keywords, data.system_prompt, id))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Test case not found")
        return {"updated": True}

@app.delete("/api/test-cases/{id}")
def delete_test_case(id: int):
    with get_db() as db:
        db.execute('DELETE FROM test_runs WHERE test_case_id = ?', (id,))
        db.execute('DELETE FROM test_cases WHERE id = ?', (id,))
        db.commit()
        return {"deleted": True}

# --- Test Running ---
@app.post("/api/runs")
def create_run(data: TestRunRequest):
    from agent_runner import run_test_case
    import asyncio
    return asyncio.run(run_test_case(data.test_case_id, AgentConfig(
        model=data.model,
        api_key=data.api_key or os.getenv("OPENAI_API_KEY", ""),
        api_url=data.api_url,
        system_prompt=data.system_prompt or "You are a helpful AI assistant."
    )))

@app.get("/api/runs")
def list_runs(test_case_id: int = None, skip: int = 0, limit: int = 50):
    with get_db() as db:
        if test_case_id:
            rows = db.execute('''
                SELECT r.*, t.name as test_name
                FROM test_runs r
                JOIN test_cases t ON r.test_case_id = t.id
                WHERE r.test_case_id = ?
                ORDER BY r.created_at DESC
                LIMIT ? OFFSET ?
            ''', (test_case_id, limit, skip)).fetchall()
        else:
            rows = db.execute('''
                SELECT r.*, t.name as test_name
                FROM test_runs r
                JOIN test_cases t ON r.test_case_id = t.id
                ORDER BY r.created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, skip)).fetchall()
        return [dict(r) for r in rows]

@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    with get_db() as db:
        row = db.execute('''
            SELECT r.*, t.name, t.description, t.input_prompt, t.expected_keywords
            FROM test_runs r
            JOIN test_cases t ON r.test_case_id = t.id
            WHERE r.id = ?
        ''', (run_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Run not found")
        return dict(row)

@app.get("/api/stats")
def get_stats():
    with get_db() as db:
        total = db.execute('SELECT COUNT(*) as c FROM test_cases').fetchone()['c']
        runs = db.execute('SELECT COUNT(*) as c FROM test_runs').fetchone()['c']
        passed = db.execute("SELECT COUNT(*) as c FROM test_runs WHERE status='passed'").fetchone()['c']
        failed = db.execute("SELECT COUNT(*) as c FROM test_runs WHERE status='failed'").fetchone()['c']
        error = db.execute("SELECT COUNT(*) as c FROM test_runs WHERE status='error'").fetchone()['c']
        pass_rate = round(100 * passed / runs, 1) if runs > 0 else 0
        return {"total_cases": total, "total_runs": runs, "passed": passed, "failed": failed, "errors": error, "pass_rate": pass_rate}

# --- Frontend static files ---
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_dir, 'index.html'))
