# Advanced Agentic AI Systems Engineering Labs

This repository contains my solutions and implementations for the four-day **Advanced Agentic AI Systems Engineering** labs.

The labs progress from building a single LangGraph agent to multi-agent orchestration, deploying agents as services, and finally giving agents controlled shell access with authenticated MCP capabilities and LangSmith tracing.

## Repository Structure

```text
AAASEC2/
├── README.md
│
├── day1/
│   ├── README.md
│   └── day1_lab_solution.py
│
├── day2/
│   ├── README.md
│   └── day2_lab_solution.py
│
├── day3/
│   ├── README.md
│   ├── Dockerfile
│   ├── compose.yaml
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── artifacts/
│   ├── skills/
│   └── src/
│
└── day4/
    ├── README.md
    ├── pyproject.toml
    ├── work/
    └── src/
```

# Day 1 — Enterprise Research Agent

Day 1 focuses on building a single research agent using **LangGraph**.

The workflow is:

```text
START → collect → store_memory → analyze → evaluate
           ↑                                  │
           └──── quality < 7 ──────────────────┤
                                               ↓
                                      report → audit → END
```

The agent:

* Searches for information using Tavily.
* Stores collected information in vector memory.
* Analyzes research sources with an LLM.
* Uses structured output for quality evaluation.
* Retries research when quality is below the required threshold.
* Limits retries to prevent infinite loops.
* Generates a final enterprise research report.
* Maintains execution logs throughout the workflow.

### Main Concepts

* LangGraph state
* Nodes and edges
* Reducers
* Conditional routing
* Retry loops
* Structured output
* Vector memory
* Checkpointing

Solution:

```text
day1/day1_lab_solution.py
```

---

# Day 2 — Multi-Agent Research Team

Day 2 extends the single-agent architecture into a **multi-agent supervisor system**.

The system contains four specialized agents:

* Researcher
* Analyst
* Writer
* Critic

A Supervisor agent examines the shared state and decides which agent should work next.

```text
                   Supervisor
                  /    |    \
                 /     |     \
        Researcher  Analyst  Writer
             \         |       /
              \        |      /
                   Critic
                     |
                 Supervisor
                 /        \
             REVISE      FINISH
                |           |
              Writer       END
```

The system includes:

* Shared blackboard state.
* Structured supervisor routing.
* Specialized system prompts for each agent.
* Scoped tools.
* Writer–critic revision loops.
* Maximum revision and turn limits.
* Execution logging.

### Main Concepts

* Multi-agent orchestration
* Supervisor pattern
* Agent personas
* Shared state
* Structured routing decisions
* Hub-and-spoke graph architecture
* Revision loops and guardrails

Solution:

```text
day2/day2_lab_solution.py
```

---

# Day 3 — Shipping Agents as Software

Day 3 moves from agent logic to deploying and exposing agents as software services.

The project contains a Deep Agent with filesystem access, Agent Skills, an HTTP API, MCP capabilities, A2A discovery, and Docker support.

## Deep Agent

The agent includes custom tools such as:

* `calculate`
* `current_time`

It also receives filesystem capabilities through `FilesystemBackend`.

## Agent Skills

The project contains reusable skill instructions including:

```text
skills/research-brief/SKILL.md
skills/data-analysis-summary/SKILL.md
```

The research-brief skill produces:

* A headline
* Exactly three findings
* A recommendation
* A confidence statement

## HTTP API

FastAPI exposes:

```text
GET  /healthz
POST /v1/responses
GET  /.well-known/agent-card.json
```

The `/v1/responses` endpoint returns an OpenResponses-style response.

## A2A

The A2A client:

1. Discovers another agent through its Agent Card.
2. Reads its capabilities and skills.
3. Reads the response endpoint from the card.
4. Delegates a task to the discovered endpoint.
5. Extracts the returned output text.

## MCP

The FastMCP server exposes callable tools such as:

```text
calculate
word_stats
```

and exposes Agent Skills as MCP resources.

## Artifact Generation

The Deep Agent uses its filesystem tools to create a research artifact:

```text
artifacts/research_brief.md
```

This demonstrates that the agent can generate a structured result and persist it as a real project artifact.

## Docker

The project also contains:

```text
Dockerfile
compose.yaml
```

for containerizing the API and MCP services.

### Main Concepts

* Deep Agents
* FilesystemBackend
* Agent Skills
* FastAPI
* OpenResponses
* A2A discovery and delegation
* FastMCP
* Docker
* Docker Compose
* Artifact generation

---

# Day 4 — Shell Access, Authentication, and Tracing

Day 4 gives the agent more powerful capabilities while introducing stronger controls and observability.

The architecture combines:

```text
                    LangSmith
                       ▲
                       │ trace
                       │
User ─────► Deep Agent
              │
              ├────► Authenticated MCP
              │        protected data
              │
              └────► Shell Backend
                       write + execute
```

## Shell Agent

The Deep Agent uses `LocalShellBackend`, which adds the `execute` capability.

The agent can:

* Write Python files.
* Write tests.
* Execute commands.
* Read failures.
* Fix code.
* Re-run commands until successful.

The working files are kept under:

```text
day4/work/
```

## LangSmith

LangSmith tracing provides visibility into the full agent execution flow, including:

* Model calls
* Tool calls
* File creation
* Shell commands
* Errors
* Recovery steps
* Final output

## Authenticated MCP

The secure MCP server implements both authentication and authorization.

Two access levels are used:

```text
Student:
read:public

Admin:
read:public
read:internal
```

Public capability:

```text
get_server_time
```

Protected capabilities:

```text
get_internal_report
get_model_evaluation_results
```

Protected tools require the `read:internal` scope.

## Mission

The mission combines three components:

```text
Authenticated MCP → information
Shell Backend      → computation
LangSmith          → observability
```

The agent retrieves protected financial data, writes a Python analysis program, executes it, and reports the computed results.

## Custom Challenge

The custom challenge uses protected AI model evaluation data.

The agent:

1. Authenticates with the MCP server.
2. Retrieves protected evaluation results.
3. Writes an analysis program.
4. Executes the program using the shell.
5. Calculates model averages.
6. Determines the highest-performing model.
7. Calculates the difference between the highest and lowest scores.
8. Reports exactly what the program printed.
9. Produces a complete execution trace in LangSmith.

### Main Concepts

* LocalShellBackend
* Shell execution
* Authentication
* Authorization scopes
* Protected MCP tools
* LangSmith tracing
* End-to-end agent workflows
* Security boundaries

---

# Four-Day Progression

```text
Day 1
Build the machinery
↓
LangGraph single-agent workflows

Day 2
Compose the agents
↓
Supervisor-based multi-agent systems

Day 3
Ship agents as software
↓
HTTP + Skills + MCP + A2A + Docker

Day 4
Give agents power safely
↓
Shell + Authentication + Authorization + Tracing
```

## Technologies

* Python
* LangGraph
* LangChain
* Deep Agents
* OpenRouter
* Tavily
* Pydantic
* FastAPI
* FastMCP
* A2A
* Docker
* Docker Compose
* LangSmith
* uv

## Environment Setup

Each lab contains its own project configuration where required.

Install dependencies using:

```bash
uv sync
```

API keys and secrets should be stored in `.env` files.

Never commit real API keys or tokens to GitHub.

Use `.env.example` files to document the required environment variables safely.

## Author

Manar alzhrani
