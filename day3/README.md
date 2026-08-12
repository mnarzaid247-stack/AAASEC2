# Day 3 — Deep Agent API and A2A Communication

## Overview

This project implements a Deep Agent and exposes it through a FastAPI HTTP API.

The agent supports basic tools, filesystem access, an OpenResponses-style endpoint, and A2A discovery and delegation.

## Project Structure

```text
day3/
├── README.md
├── .env.example
├── pyproject.toml
├── uv.lock
└── src/
    ├── agent.py
    ├── api.py
    └── a2a_client.py
```

## Components

### Agent

`src/agent.py` builds the Deep Agent.

The agent includes:

- `calculate` — evaluates simple arithmetic expressions.
- `current_time` — returns the current local date and time.
- Filesystem tools provided by `FilesystemBackend`.
- Fake mode for testing without API keys.

The agent follows this interface:

```python
agent = build_agent()

result = await agent.ainvoke({
    "messages": [
        {
            "role": "user",
            "content": "Hello"
        }
    ]
})
```

### HTTP API

`src/api.py` exposes the agent using FastAPI.

Available endpoints:

```text
GET  /healthz
POST /v1/responses
GET  /.well-known/agent-card.json
```

`/healthz` provides a simple health check.

`/v1/responses` accepts a request such as:

```json
{
  "input": "What time is it?"
}
```

and returns an OpenResponses-style response.

The Agent Card endpoint provides information that other agents can use to discover this agent.

### A2A Client

`src/a2a_client.py` demonstrates agent-to-agent discovery and delegation.

The client:

1. Retrieves the peer's Agent Card.
2. Reads the peer's endpoint from the card.
3. Sends a task to that endpoint.
4. Extracts the returned `output_text`.

The response endpoint is discovered from the Agent Card and is not hardcoded in the client.

## Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openrouter_api_key
STUDENT_NAME=Manar Zaid
PUBLIC_URL=http://localhost:8000
```

Do not commit the `.env` file or API keys to GitHub.

## Installation

Install the project dependencies:

```bash
uv sync
```

## Run the Agent

### Fake Mode

PowerShell:

```powershell
$env:USE_FAKE="1"
uv run python src/agent.py
```

### Real Agent

```powershell
Remove-Item Env:USE_FAKE
uv run python src/agent.py
```

## Run the API

For offline testing:

```powershell
$env:USE_FAKE="1"
uv run uvicorn src.api:app --reload
```

The API will run at:

```text
http://localhost:8000
```

## Test the API

Health check:

```powershell
curl.exe http://localhost:8000/healthz
```

Expected result:

```json
{"status":"ok"}
```

Test the agent endpoint:

```powershell
curl.exe -X POST http://localhost:8000/v1/responses `
  -H "Content-Type: application/json" `
  -d '{\"input\":\"hi\"}'
```

Test Agent Card discovery:

```powershell
curl.exe http://localhost:8000/.well-known/agent-card.json
```

## Test A2A Delegation

With the API running:

```powershell
uv run python src/a2a_client.py http://localhost:8000 "What time is it?"
```

The client discovers the agent through:

```text
/.well-known/agent-card.json
```

and delegates the task using the URL provided by the Agent Card.

## Author

Manar Zaid