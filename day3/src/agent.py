import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"


# ============================================================
# TOOLS
# ============================================================

@tool
def calculate(expression: str) -> str:
    """Evaluate a simple arithmetic expression."""

    allowed_chars = set("0123456789+-*/(). %")

    if not set(expression) <= allowed_chars:
        return "Invalid expression."

    try:
        result = eval(
            expression,
            {"__builtins__": {}},
            {},
        )
        return str(result)

    except Exception as error:
        return f"Calculation error: {error}"


@tool
def current_time() -> str:
    """Return the current local date and time."""

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ============================================================
# FAKE AGENT
# ============================================================

class FakeAgent:
    async def ainvoke(self, state):

        messages = state.get("messages", [])

        if messages:
            last_message = messages[-1]

            if isinstance(last_message, dict):
                content = last_message.get(
                    "content",
                    "",
                )
            else:
                content = getattr(
                    last_message,
                    "content",
                    "",
                )
        else:
            content = ""

        reply = (
            "Fake agent reply: "
            f"I received your request: {content}"
        )

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": reply,
                }
            ]
        }


# ============================================================
# BUILD AGENT
# ============================================================

def build_agent():

    if USE_FAKE:
        return FakeAgent()

    from langchain_openai import ChatOpenAI
    from deepagents import create_deep_agent
    from deepagents.backends.filesystem import FilesystemBackend

    day3_root = Path(__file__).resolve().parent.parent

    model = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
    )

    backend = FilesystemBackend(
        root_dir=day3_root,
        virtual_mode=True,
    )

    system_prompt = (
        "You are a helpful AI assistant. "
        "Use the available tools when they are relevant. "
        "You can calculate arithmetic expressions and provide the current time. "
        "You also have filesystem access inside the Day 3 project directory. "
        "Use available skills when appropriate."
    )

    agent = create_deep_agent(
        model=model,
        tools=[
            calculate,
            current_time,
        ],
        system_prompt=system_prompt,
        backend=backend,
        skills=[
            "/skills/",
        ],
    )

    return agent


# ============================================================
# SMOKE TEST
# ============================================================

async def main():

    agent = build_agent()

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Hello. Tell me what tools "
                        "you can use."
                    ),
                }
            ]
        }
    )

    messages = result.get(
        "messages",
        [],
    )

    if not messages:
        print("No reply received.")
        return

    last_message = messages[-1]

    if isinstance(last_message, dict):
        print(
            last_message.get(
                "content",
                last_message,
            )
        )
    else:
        print(
            getattr(
                last_message,
                "content",
                last_message,
            )
        )


if __name__ == "__main__":

    import asyncio

    asyncio.run(
        main()
    )