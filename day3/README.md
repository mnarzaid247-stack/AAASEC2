# Day 3 — Deep Agents, Skills, MCP, Docker, and A2A

## Overview

This project implements a Deep Agent and exposes it as a production-style service.

The project demonstrates:

- Deep Agent creation
- Custom tools
- Agent Skills
- FastAPI HTTP API
- OpenResponses-style responses
- A2A Agent Card discovery
- Agent-to-Agent delegation
- FastMCP tools and skill resources
- Docker containerization
- Docker Compose multi-service orchestration

## Project Structure

```text
day3/
├── README.md
├── .env.example
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── uv.lock
│
├── skills/
│   ├── research-brief/
│   │   └── SKILL.md
│   └── data-analysis-summary/
│       └── SKILL.md
│
└── src/
    ├── agent.py
    ├── api.py
    ├── a2a_client.py
    └── mcp_server.py
```

## 1. Deep Agent

`src/agent.py` builds the main Deep Agent.

The agent provides:

- `calculate` — evaluates simple arithmetic expressions.
- `current_time` — returns the current local date and time.
- Filesystem tools through `FilesystemBackend`.
- Agent Skills from the `/skills/` directory.
- Fake mode for offline testing.

The main contract is:

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

## 2. Agent Skills

The project includes two skills.

### Research Brief

`skills/research-brief/SKILL.md`

Produces a concise research brief containing:

- A headline
- Exactly three findings
- A recommendation
- A confidence statement

### Data Analysis Summary

`skills/data-analysis-summary/SKILL.md`

Provides instructions for turning statistical or analytical findings into a concise summary for a non-technical audience.

## 3. HTTP API

`src/api.py` exposes the agent using FastAPI.

Available endpoints:

```text
GET  /healthz
POST /v1/responses
GET  /.well-known/agent-card.json
```

### Health Check

```text
GET /healthz
```

returns:

```json
{
  "status": "ok"
}
```

### OpenResponses Endpoint

```text
POST /v1/responses
```

accepts:

```json
{
  "input": "What time is it?"
}
```

and returns an OpenResponses-style response containing the assistant output.

## 4. A2A Agent Card

The agent exposes an A2A Agent Card at:

```text
/.well-known/agent-card.json
```

The card describes the agent, its capabilities, skills, and response endpoint.

Other agents can use this endpoint to discover the agent before delegating work.

## 5. A2A Delegation

`src/a2a_client.py` implements discovery and delegation.

The client:

1. Retrieves the peer Agent Card.
2. Reads the available skills.
3. Reads the response endpoint from `card["url"]`.
4. Sends a task to the discovered endpoint.
5. Extracts `output_text` from the OpenResponses reply.

The response endpoint is not hardcoded in the client.

Example:

```bash
uv run python src/a2a_client.py http://localhost:8000 "What time is it?"
```

## 6. MCP Server

`src/mcp_server.py` exposes tools and skills through FastMCP.

The MCP server provides two callable tools:

- `calculate`
- `word_stats`

It also exposes the project skills as MCP resources using `SkillsDirectoryProvider`.

The server runs on port `8001`.

Run it with:

```bash
uv run python src/mcp_server.py
```

The MCP endpoint is:

```text
http://localhost:8001/mcp
```

## 7. Environment Variables

Copy `.env.example` to `.env` and provide the required values.

Example:

```env
OPENAI_API_KEY=your_openrouter_api_key
STUDENT_NAME=Manar Zaid
PUBLIC_URL=http://localhost:8000
```

For offline testing:

```env
USE_FAKE=1
```

Never commit the real `.env` file or API keys.

## 8. Installation

Install dependencies using:

```bash
uv sync
```

## 9. Run the Agent

### Fake Mode — PowerShell

```powershell
$env:USE_FAKE="1"
uv run python src/agent.py
```

### Real Mode

```powershell
Remove-Item Env:USE_FAKE
uv run python src/agent.py
```

## 10. Run the API

```powershell
$env:USE_FAKE="1"
uv run uvicorn src.api:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Test the health endpoint:

```powershell
curl.exe http://localhost:8000/healthz
```

Test the response endpoint:

```powershell
curl.exe -X POST http://localhost:8000/v1/responses `
  -H "Content-Type: application/json" `
  -d '{\"input\":\"hi\"}'
```

Test the Agent Card:

```powershell
curl.exe http://localhost:8000/.well-known/agent-card.json
```

## 11. Docker

Build the agent image:

```bash
docker build -t aaasec2-agent .
```

Run the API container:

```bash
docker run --rm -p 8000:8000 --env-file .env aaasec2-agent
```

## 12. Docker Compose

The project contains two services:

```text
agent-api → port 8000
mcp       → port 8001
```

Inside the Compose network, the API can address the MCP service using:

```text
http://mcp:8001/mcp
```

Start the services with:

```bash
docker compose up --build
```

Stop them with:

```bash
docker compose down
```

## Author

Manar alzhrani