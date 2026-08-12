# Day 1 Lab — Enterprise Research Agent with LangGraph

## Overview

This lab implements an **Enterprise Research Agent** using LangGraph.

The agent collects research from the web, stores the collected information in memory, analyzes the sources using an LLM, evaluates the quality of the research, and retries the research process when the quality score is too low.

## Workflow

```text
START → collect → store_memory → analyze → evaluate
           ↑                                  │
           └── quality < 7 (max 3 tries) ─────┤
                                              └── quality >= 7
                                                       ↓
                                              report → audit → END
```

## How It Works

The workflow consists of six main nodes:

* **collect** — Searches for information using Tavily. The search query changes on every retry to improve the research results.
* **store_memory** — Stores the collected source content in an in-memory vector store.
* **analyze** — Uses the LLM to analyze the collected sources and retrieve related information from vector memory.
* **evaluate** — Evaluates the quality of the research using structured output with a Pydantic schema.
* **report** — Generates the final enterprise research report.
* **audit** — Records the final execution statistics and research results.

## Quality Control

The agent uses conditional routing after the evaluation step.

If the quality score is **7 or higher**, the workflow continues to the report.

If the score is below 7, the agent performs another research iteration using a different search query.

The workflow allows a maximum of **3 research iterations** to prevent an infinite loop.

## Technologies Used

* Python
* LangGraph
* LangChain
* OpenRouter
* Tavily Search
* Pydantic
* InMemoryVectorStore
* HuggingFace Embeddings
* LangGraph InMemorySaver

## Environment Variables

Create a `.env` file and add:

```env
OPENAI_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Do not commit the `.env` file or API keys to GitHub.

## Installation

Install the project dependencies using:

```bash
uv sync
```

## Running the Lab

Run the solution:

```bash
uv run python day1_lab_solution.py
```

The program will display the LangGraph Mermaid diagram, execute the research workflow, generate the final report, and print the execution logs.

## Offline Test

The lab can also be tested without API keys using fake deterministic components:

### Linux / macOS / WSL

```bash
USE_FAKE=1 uv run python day1_lab_solution.py
```

### PowerShell

```powershell
$env:USE_FAKE="1"
uv run python day1_lab_solution.py
```

## Solution File

The completed implementation is available in:

```text
day1_lab_solution.py
```

## Author

Manar alzhrani
