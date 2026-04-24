import time
import json
import re
from openai import OpenAI
from db import get_db

async def run_test_case(test_case_id: int, api_url: str, api_key: str, model: str, system_prompt: str):
    # Get test case
    with get_db() as db:
        row = db.execute('SELECT * FROM test_cases WHERE id = ?', (test_case_id,)).fetchone()
        if not row:
            raise ValueError(f"Test case {test_case_id} not found")
        test_case = dict(row)

    start_time = time.time()
    output = None
    error = None
    status = "passed"
    judge_score = None
    judge_reason = None

    try:
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt or test_case['system_prompt'] or "You are a helpful AI assistant."},
            {"role": "user", "content": test_case['input_prompt']}
        ]

        # Call LLM API
        client = OpenAI(api_key=api_key, base_url=api_url)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.3
        )

        output = response.choices[0].message.content
        duration_ms = int((time.time() - start_time) * 1000)

        # Evaluate based on eval_mode
        eval_mode = test_case.get('eval_mode', 'keyword')
        
        if eval_mode == 'judge':
            # LLM-as-Judge evaluation
            judge_score, judge_reason = await _evaluate_with_judge(
                prompt=test_case['input_prompt'],
                response=output,
                judge_model=test_case.get('judge_model', 'openai/gpt-4o-mini'),
                judge_threshold=test_case.get('judge_threshold', 7.0),
                judge_prompt=test_case.get('judge_prompt'),
                client=client
            )
            
            threshold = judge_threshold
            status = "passed" if judge_score >= threshold else "failed"
            status = status
        else:
            # Keyword-based evaluation (original)
            keywords = [k.strip().lower() for k in test_case['expected_keywords'].split(',') if k.strip()]
            if keywords:
                output_lower = output.lower()
                missing = [kw for kw in keywords if kw not in output_lower]
                if missing:
                    status = "failed"
                    error = f"Missing keywords: {', '.join(missing)}"

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        status = "error"
        error = str(e)
        output = None

    # Save run
    with get_db() as db:
        cursor = db.execute('''
            INSERT INTO test_runs (test_case_id, status, output, duration_ms, error, model, api_url, judge_score, judge_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (test_case_id, status, output[:20000] if output else None, duration_ms, error, model, api_url, judge_score, judge_reason))
        db.commit()
        run_id = cursor.lastrowid

    return {
        "id": run_id,
        "test_case_id": test_case_id,
        "status": status,
        "output": output,
        "duration_ms": duration_ms,
        "error": error,
        "model": model,
        "judge_score": judge_score,
        "judge_reason": judge_reason
    }


async def _evaluate_with_judge(prompt: str, response: str, judge_model: str, judge_threshold: float, judge_prompt: str, client) -> tuple:
    """
    Use an LLM as a judge to evaluate the agent's response.
    Returns (score: float, reason: str)
    """
    system_prompt = judge_prompt or """You are an impartial AI judge. Evaluate the response to the given prompt.

Score the response on THREE dimensions (each 0-10):
1. accuracy - Is the information factually correct?
2. relevance - Does it directly address the user's question?
3. helpfulness - Is it clear, complete, and useful?

Return ONLY valid JSON with this structure:
{"accuracy": 8, "relevance": 9, "helpfulness": 7, "overall": 8, "reason": "brief explanation"}

Overall score is a weighted average: accuracy(40%) + relevance(30%) + helpfulness(30%).
JSON OUTPUT ONLY — no markdown, no explanation outside the JSON."""

    judge_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Prompt: {prompt}\n\nResponse to evaluate: {response}"}
    ]

    try:
        judge_response = client.chat.completions.create(
            model=judge_model,
            messages=judge_messages,
            max_tokens=512,
            temperature=0.2
        )

        judge_text = judge_response.choices[0].message.content.strip()
        
        # Parse JSON from judge response
        # Handle cases where model wraps in ```json block
        json_match = re.search(r'\{[^{}]*"overall"[^{}]*\}', judge_text, re.DOTALL)
        if json_match:
            judge_data = json.loads(json_match.group())
            score = float(judge_data.get('overall', 0))
            reason = judge_data.get('reason', '')
            return score, reason
        else:
            # Try parsing entire response as JSON
            try:
                judge_data = json.loads(judge_text)
                score = float(judge_data.get('overall', 0))
                reason = judge_data.get('reason', '')
                return score, reason
            except Exception:
                return 0.0, f"Could not parse judge output: {judge_text[:100]}"
    except Exception as e:
        return 0.0, f"Judge error: {str(e)}"