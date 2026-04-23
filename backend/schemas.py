from pydantic import BaseModel
from typing import Optional

class TestCaseCreate(BaseModel):
    name: str
    description: str = ""
    input_prompt: str
    expected_keywords: str = ""  # comma-separated

class TestCaseResponse(TestCaseCreate):
    id: int

class TestRunRequest(BaseModel):
    test_case_id: int
    model: str = "openai/gpt-4o-mini"
    api_key: Optional[str] = None

class AgentConfig(BaseModel):
    model: str
    api_key: str
    system_prompt: str = "You are a helpful AI assistant."
