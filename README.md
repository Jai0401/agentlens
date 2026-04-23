# AgentLens — AI Agent Testing & Observability

**AgentLens** is an open-source tool for systematically testing AI agent behavior. Create test cases, run them against any OpenAI-compatible API, and track pass/fail history with detailed output logs.

---

## Features

- ✅ **Test Case Management** — Create, edit, delete test cases with expected keywords
- ✅ **Multi-Provider Support** — Works with OpenAI, OpenRouter, Groq, DeepSeek, Anthropic, Gemini
- ✅ **Bulk Test Runs** — Run multiple test cases in sequence with real-time progress
- ✅ **Detailed Results** — Full output logs, duration tracking, error reporting
- ✅ **Agent Configurations** — Save and reuse API credentials for quick test runs
- ✅ **Statistics Dashboard** — Pass/fail rates, total runs, error tracking
- ✅ **Dark Theme UI** — Clean, professional interface
- 🚧 **In Progress** — Regression testing, historical diff, replay debugging

---

## Architecture

```
agentlens/
├── backend/
│   ├── main.py          # FastAPI app (CRUD + run endpoints)
│   ├── db.py            # SQLite setup
│   ├── schemas.py       # Pydantic models
│   ├── agent_runner.py  # Test execution engine
│   └── requirements.txt
├── frontend/
│   ├── index.html       # Main UI
│   ├── style.css        # Dark theme styles
│   └── app.js           # API client + UI logic
└── README.md
```

**Stack:**
- Backend: FastAPI (Python) + SQLite
- Frontend: Vanilla HTML/CSS/JS (no build step)
- API: OpenAI-compatible (any provider with chat/completions endpoint)

---

## Quick Start

### 1. Start the server

```bash
cd agentlens/backend
pip install -r requirements.txt
python3 -m uvicorn main:app --port 8002
```

Then open: **http://localhost:8002**

### 2. Configure API access

**Option A:** Enter API key directly in the UI (Run Tests tab)
**Option B:** Save a permanent Agent Config (Configs tab → New Config)

### 3. Create a test case

1. Go to **Test Cases** tab
2. Click **+ New Test Case**
3. Enter name, description, input prompt, expected keywords
4. Click **Create Test Case**

### 4. Run tests

1. Go to **Run Tests** tab
2. Select test cases via checkboxes
3. Enter API URL (default: OpenRouter)
4. Paste your API key
5. Pick a model
6. Click **▶ Run Selected Tests**

---

## API Reference

### Test Cases

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/test-cases` | List all test cases |
| POST | `/api/test-cases` | Create test case |
| GET | `/api/test-cases/{id}` | Get single test case |
| PUT | `/api/test-cases/{id}` | Update test case |
| DELETE | `/api/test-cases/{id}` | Delete test case + runs |

### Agent Configs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agent-configs` | List saved configs |
| POST | `/api/agent-configs` | Save new config |
| DELETE | `/api/agent-configs/{id}` | Delete config |

### Test Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/runs` | Run single test case |
| POST | `/api/runs/bulk` | Run multiple test cases |
| GET | `/api/runs` | List all runs (with filter) |
| GET | `/api/runs/{id}` | Get run details |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Dashboard stats |

---

## Supported Models

AgentLens works with any OpenAI-compatible API. Some popular options:

| Provider | API URL | Free Tier Models |
|----------|---------|-----------------|
| **OpenRouter** | `https://openrouter.ai/api/v1` | `tencent/hy3-preview:free`, `openrouter/auto` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| **DeepSeek** | `https://api.deepseek.com/v1` | `deepseek-chat-v3-0324` |
| **OpenAI** | `https://api.openai.com/v1` | (paid) |

---

## Schema

### Test Case
```json
{
  "name": "Basic Math Test",
  "description": "Validates arithmetic responses",
  "input_prompt": "What is 12 * 17?",
  "expected_keywords": "204",
  "system_prompt": "You are a helpful AI assistant."
}
```

### Run Request
```json
{
  "test_case_id": 1,
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-or-...",
  "model": "openai/gpt-4o-mini"
}
```

---

## Pain Points This Solves

| Pain Point | How AgentLens Helps |
|------------|---------------------|
| **"Vibe checking"** | Systematic pass/fail criteria instead of gut feel |
| **No regression testing** | Run all test cases after any change, see what broke |
| **Inconsistent agent behavior** | Track which models/prompts produce reliable results |
| **Black-box debugging** | Full output logs for every run, not just final answer |
| **Multiple providers** | Test same cases across OpenAI, DeepSeek, Groq side-by-side |

---

## Roadmap

- [ ] Regression testing — auto-run on model/prompt change
- [ ] Historical diff — compare outputs across runs
- [ ] Replay debugging — replay exact agent session from logs
- [ ] Multi-agent orchestration testing
- [ ] Semantic loop detection
- [ ] Export results as CSV/JSON

---

## License

MIT — use freely, contribute improvements.