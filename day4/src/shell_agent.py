import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from deepagents import create_deep_agent


load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

SANDBOX_PROVIDER = os.getenv(
    "SANDBOX_PROVIDER",
    "local",
)

WORK_DIR = (
    Path(__file__).resolve().parent.parent
    / "work"
)


# ============================================================
# MODEL
# ============================================================

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = (
    "You are a Python coding agent with access to a shell. "
    "Use filesystem tools to create and modify files. "
    "Use execute to run commands and tests. "
    "When a command fails, inspect the output, fix the issue, "
    "and run the command again until the task succeeds. "
    "Keep all project files inside the assigned work directory."
)


# ============================================================
# BACKEND FACTORY
# ============================================================

def make_backend():
    """
    Build the requested execution backend and return:
        (backend, cleanup_function)
    """

    if SANDBOX_PROVIDER == "local":

        from deepagents.backends import LocalShellBackend

        WORK_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        backend = LocalShellBackend(
            root_dir=str(WORK_DIR),
            virtual_mode=True,
            env={
                "PATH": os.environ.get(
                    "PATH",
                    "/usr/bin:/bin",
                )
            },
        )

        def cleanup():
            pass

        return backend, cleanup


    if SANDBOX_PROVIDER == "daytona":

        from daytona import Daytona
        from langchain_daytona import DaytonaSandbox

        daytona = Daytona()

        sandbox = daytona.create()

        backend = DaytonaSandbox(
            sandbox=sandbox
        )

        return backend, sandbox.stop


    if SANDBOX_PROVIDER == "langsmith":

        from deepagents.backends import LangSmithSandbox
        from langsmith.sandbox import SandboxClient

        client = SandboxClient()

        sandbox = client.create_sandbox()

        backend = LangSmithSandbox(
            sandbox=sandbox
        )

        def cleanup():
            client.delete_sandbox(
                sandbox.name
            )

        return backend, cleanup


    raise ValueError(
        f"Unsupported SANDBOX_PROVIDER: "
        f"{SANDBOX_PROVIDER}"
    )


# ============================================================
# CODING TASK
# ============================================================

TASK = (
    "Create a small Python calculator project inside the work directory. "
    "First create calculator.py with add, subtract, multiply, and divide "
    "functions. The divide function must raise ZeroDivisionError when the "
    "second argument is zero. "

    "Then create test_calculator.py with pytest tests for every operation, "
    "including a test that verifies division by zero raises the correct error. "

    "Use the execute tool to run the tests with 'python -m pytest'. "
    "If pytest is unavailable, install it first. "

    "If any test fails, inspect the error, fix the code or tests, and rerun "
    "pytest until all tests pass. "

    "At the end, report the exact final pytest result."
)


# ============================================================
# RUN AGENT
# ============================================================

if __name__ == "__main__":

    backend, cleanup = make_backend()

    try:

        agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            backend=backend,
        )

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": TASK,
                    }
                ]
            }
        )

        final_message = result[
            "messages"
        ][-1]

        print(
            final_message.content
        )

    finally:

        cleanup()