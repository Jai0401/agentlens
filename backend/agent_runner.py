import time
import os
from db import get_db
from schemas import AgentConfig

async def run_test_case(test_case_id: int, config: AgentConfig):
    # Get test case
    with get_db() as db:
        row = db.execute('SELECT * FROM test_cases WHERE id = ?', (test_case_id,)).fetchone()
        if not row:
            raise ValueError(f"Test case {test_case_id} not found")
        test_case = dict(row)

    # Run agent
    start = time.time()
    try:
        # Build messages
        # Use test case's system_prompt if provided, else config's
        system_prompt = test_case.get('system_prompt') or config.system_prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_case['input_prompt']}
        ]

        # Call OpenAI-compatible API
        from openai import OpenAI
        base_url = config.api_url if hasattr(config, 'api_url') else "https://openrouter.ai/api/v1"
        client = OpenAI(api_key=config.api_key, base_url=base_url)

        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=2048,
            temperature=0.3
        )

        output = response.choices[0].message.content
        duration_ms = int((time.time() - start) * 1000)

        # Check expected keywords
        keywords = [k.strip().lower() for k in test_case['expected_keywords'].split(',') if k.strip()]
        passed = all(kw in output.lower() for kw in keywords) if keywords else True

        status = "passed" if passed else "failed"
        error = None

        # Save run
        with get_db() as db:
            cursor = db.execute('''
                INSERT INTO test_runs (test_case_id, status, output, duration_ms, error)
                VALUES (?, ?, ?, ?, ?)
            ''', (test_case_id, status, output[:10000], duration_ms, error))
            db.commit()
            run_id = cursor.lastrowid

        return {"run_id": run_id, "status": status, "output": output, "duration_ms": duration_ms}

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        with get_db() as db:
            cursor = db.execute('''
                INSERT INTO test_runs (test_case_id, status, error, duration_ms)
                VALUES (?, ?, ?, ?)
            ''', (test_case_id, "error", str(e), duration_ms))
            db.commit()
            run_id = cursor.lastrowid
        return {"run_id": run_id, "status": "error", "error": str(e)}
