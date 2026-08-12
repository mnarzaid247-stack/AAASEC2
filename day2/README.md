# Day 2 Lab — Multi-Agent Research Team with LangGraph

## Overview

This lab implements a **multi-agent research team** using LangGraph.

Instead of using a single agent, the system contains multiple specialized agents coordinated by a **supervisor**.

The supervisor decides which agent should work next based on the current team state.

## Agents

The system contains four worker agents:

* **Researcher** — searches for information and collects factual research notes.
* **Analyst** — analyzes the research notes and identifies patterns, risks, and implications.
* **Writer** — creates the executive brief and revises it when feedback is provided.
* **Critic** — reviews the draft and either approves it or requests specific revisions.

A **Supervisor** coordinates the workflow and decides which worker should act next.

## Workflow

```text
                 ┌──────────── Supervisor ────────────┐
                 │                                    │
                 ↓                                    │
             Researcher                               │
                 │                                    │
                 └──────────────→ Supervisor           │
                                      │
                                      ↓
                                   Analyst
                                      │
                                      └────→ Supervisor
                                                   │
                                                   ↓
                                                Writer
                                                   │
                                                   └──→ Supervisor
                                                            │
                                                            ↓
                                                         Critic
                                                            │
                                      ┌─────────────────────┘
                                      ↓
                                  Supervisor
                                 /          \
                           REVISE            FINISH
                              ↓                ↓
                           Writer             END
```

Every worker returns to the supervisor after completing its task.

## Shared State

The agents communicate through a shared LangGraph state called `TeamState`.

It stores:

* the original task
* research notes
* analysis
* current draft
* critic feedback
* revision count
* supervisor turn count
* next selected agent
* execution logs

The `research_notes` and `execution_logs` fields use reducers so new values are appended instead of replacing previous values.

## Supervisor Routing

The supervisor uses structured output to choose one of the following actions:

```text
researcher
analyst
writer
critic
FINISH
```

The normal workflow is:

```text
researcher → analyst → writer → critic
```

If the critic responds with `REVISE`, the supervisor sends the task back to the writer.

If the critic approves the draft, the supervisor selects `FINISH`.

## Guardrails

The workflow includes limits to prevent infinite loops:

```text
MAX_REVISIONS = 2
MAX_TURNS = 12
```

The system stops when the draft is approved, the revision limit is reached, or the maximum number of supervisor turns is exceeded.

## Technologies Used

* Python
* LangGraph
* LangChain
* OpenRouter
* Tavily Search
* Pydantic
* Structured Output
* LangGraph InMemorySaver

## Environment Variables

Create a `.env` file and add:

```env
OPENAI_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Do not commit the `.env` file or API keys to GitHub.

## Installation

Install the dependencies using:

```bash
uv sync
```

## Running the Lab

Run the solution:

```bash
uv run python day2_lab_solution.py
```

## Offline Test

The lab supports a fake mode that does not require API keys.

### Linux / macOS / WSL

```bash
USE_FAKE=1 uv run python day2_lab_solution.py
```

### PowerShell

```powershell
$env:USE_FAKE="1"
uv run python day2_lab_solution.py
```

In fake mode, the critic rejects the first draft and requests a revision. The writer revises the draft, and the critic then approves it.

This demonstrates the revision loop:

```text
Writer → Critic → Writer → Critic → FINISH
```

## Solution File

The completed implementation is available in:

```text
day2_lab_solution.py
```

## Author

Manar alzhrani
