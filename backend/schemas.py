from pydantic import BaseModel
from typing import Optional

class TestCaseCreate(BaseModel):
    name: str
    description: str = ""
    input_prompt: str
    expected_keywords: str = ""  # comma-separated (fallback if no judge)
    system_prompt: str = ""
    # LLM judge settings
    eval_mode: str = "keyword"  # "keyword" | "judge"
    judge_model: str = "openai/gpt-4o-mini"
    judge_threshold: float = 7.0  # score 0-10, pass if >= threshold
    judge_prompt: str = ""  # custom judge prompt (optional)

class TestCaseResponse(TestCaseCreate):
    id: int

class TestRunRequest(BaseModel):
    test_case_id: int
    model: str = "openai/gpt-4o-mini"
    api_key: Optional[str] = None
    api_url: str = "https://openrouter.ai/api/v1"
    system_prompt: Optional[str] = None

class AgentConfig(BaseModel):
    model: str
    api_key: str
    api_url: str = "https://openrouter.ai/api/v1"
    system_prompt: str = "You are a helpful AI assistant."

class JudgePrompt:
    DEFAULT_JUDGE_PROMPT = """You are an impartial AI judge. Evaluate the response to the given prompt.

Score the response on THREE dimensions (each 0-10):
1. **accuracy** - Is the information factually correct?
2. **relevance** - Does it directly address the user's question?
3. **helpfulness** - Is it clear, complete, and useful?

Return ONLY valid JSON with this structure:
{{"accuracy": 8, "relevance": 9, "helpfulness": 7, "overall": 8, "reason": "brief explanation"}}

Overall score is a weighted average: accuracy(40%) + relevance(30%) + helpfulness(30%).

JSON OUTPUT ONLY — no markdown, no explanation outside the JSON."""