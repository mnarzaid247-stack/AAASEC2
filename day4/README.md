# Day 4 — Shell Execution, Authenticated MCP, and LangSmith Tracing

## Overview

Day 4 extends the agent from previous labs by giving it controlled shell access, authenticated MCP capabilities, and execution tracing through LangSmith.

The main objective is to combine:

* A Deep Agent
* Shell execution
* Authenticated MCP tools
* Authorization scopes
* LangSmith tracing
* File creation and Python execution
* A complete end-to-end mission

## Project Structure

```text
day4/
├── README.md
├── .env.example
├── pyproject.toml
│
├── work/
│
└── src/
    ├── shell_agent.py
    ├── secure_mcp.py
    ├── check_auth.py
    ├── mission.py
    └── challenge.py
```

## 1. Shell Agent

`src/shell_agent.py` creates a Deep Agent with shell access using `LocalShellBackend`.

The agent can use filesystem tools and the `execute` tool to:

* Create Python files
* Create tests
* Run shell commands
* Run Python programs
* Inspect errors
* Fix failures
* Re-run commands until successful

The local backend uses:

```text
day4/work/
```

as the working directory.

The shell environment only receives the `PATH` variable instead of inheriting the full environment.

## Calculator Task

The shell agent is asked to:

1. Create `calculator.py`.
2. Implement add, subtract, multiply, and divide.
3. Create pytest tests.
4. Include a division-by-zero test.
5. Execute the tests.
6. Fix failures if needed.
7. Report the final pytest output.

Run:

```bash
uv run python src/shell_agent.py
```

## 2. LangSmith Tracing

LangSmith tracing records the complete agent execution flow.

Environment variables:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=aaasec2-day4
```

No additional tracing code is required.

The trace can show:

* User input
* Model calls
* File writes
* Shell execution
* Tool results
* Error recovery
* Final response

This provides visibility into the full agent workflow.

## 3. Authenticated MCP Server

`src/secure_mcp.py` exposes authenticated MCP tools on port `8002`.

The server uses two identities.

### Student

The student token has:

```text
read:public
```

### Admin

The admin token has:

```text
read:public
read:internal
```

## MCP Tools

### Public Tool

```text
get_server_time
```

Any valid authenticated user can call this tool.

### Protected Financial Tool

```text
get_internal_report
```

Requires:

```text
read:internal
```

### Custom Protected Tool

```text
get_model_evaluation_results
```

This tool contains internal AI model benchmark data and also requires:

```text
read:internal
```

Run the MCP server:

```bash
uv run python src/secure_mcp.py
```

The MCP endpoint is:

```text
http://localhost:8002/mcp
```

## 4. Authentication and Authorization Test

`src/check_auth.py` is the provided authentication test script.

Run the secure MCP server first, then:

```bash
uv run python src/check_auth.py
```

Expected behavior:

```text
No token + public tool          -> rejected
Wrong token + public tool       -> rejected
Student token + public tool     -> allowed
Student token + protected tool  -> rejected
Admin token + protected tool    -> allowed
```

The protected tool may appear as `Unknown tool` for unauthorized clients because FastMCP hides tools that the current scopes cannot access.

## 5. Mission

`src/mission.py` combines the main Day 4 components.

The workflow is:

```text
User
  ↓
Deep Agent
  ├── Authenticated MCP → protected financial data
  ├── Filesystem        → writes analysis program
  ├── Execute           → runs Python analysis
  └── LangSmith         → records the complete trace
```

The agent retrieves protected quarterly data and creates a Python program that calculates:

* Revenue
* Costs
* Profit per month
* Overall profit margin
* Highest-profit month

The agent then executes the program and reports the exact computed results.

Run the MCP server first:

```bash
uv run python src/secure_mcp.py
```

Then run:

```bash
uv run python src/mission.py
```

## 6. Challenge

`src/challenge.py` implements a custom end-to-end task.

The custom protected MCP capability is:

```text
get_model_evaluation_results
```

The dataset contains AI model evaluation scores for:

* Accuracy
* Reasoning
* Safety

The challenge agent must:

1. Authenticate with the MCP server.
2. Fetch the protected model evaluation data.
3. Write `analyze_models.py`.
4. Calculate the average score for every model.
5. Identify the highest-performing model.
6. Calculate the difference between highest and lowest averages.
7. Execute the Python program using the shell.
8. Report exactly what the program printed.
9. Add one short insight.

Run:

```bash
uv run python src/challenge.py
```

## 7. Environment Variables

Create a `.env` file using `.env.example`.

Example:

```env
OPENAI_API_KEY=your_openrouter_api_key

MCP_STUDENT_TOKEN=student-secret-token
MCP_ADMIN_TOKEN=admin-secret-token
MCP_URL=http://localhost:8002/mcp

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=aaasec2-day4

SANDBOX_PROVIDER=local
```

Do not commit the real `.env` file or API keys.

## 8. Security

`LocalShellBackend` is not an isolated sandbox.

The filesystem tools are scoped to the project work directory, and the shell environment is restricted, but commands still run as the current operating-system user.

A real sandbox provider such as Daytona or LangSmith Sandbox provides stronger infrastructure-level isolation.

## Run Order

Terminal 1:

```bash
uv run python src/secure_mcp.py
```

Terminal 2:

```bash
uv run python src/check_auth.py
```

Then:

```bash
uv run python src/mission.py
```

Finally:

```bash
uv run python src/challenge.py
```

## Author

Manar alzhrani
