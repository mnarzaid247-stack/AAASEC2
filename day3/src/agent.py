import os
from datetime import datetime
from pathlib import Path
import ast
import operator

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"


# ============================================================
# TOOLS
# ============================================================

@tool
def calculate(expression: str) -> str:
    """Evaluate a simple arithmetic expression safely."""

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operator.")

            return operation(
                evaluate(node.left),
                evaluate(node.right),
            )

        if isinstance(node, ast.UnaryOp):
            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operator.")

            return operation(
                evaluate(node.operand)
            )

        raise ValueError("Invalid expression.")

    try:
        tree = ast.parse(
            expression,
            mode="eval",
        )

        return str(
            evaluate(tree)
        )

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
                        "Create a research brief about the benefits and risks "
                        "of multi-agent AI systems. "
                        "Use the research-brief skill. "
                        "Include exactly three findings, a recommendation, "
                        "and a confidence section. "
                        "Save the final report to "
                        "/artifacts/research_brief.md using your filesystem tools."
                    ),
                }
            ]
        }
    )

    messages = result.get("messages", [])

    if not messages:
        print("No reply received.")
        return

    last_message = messages[-1]

    if isinstance(last_message, dict):
        reply = last_message.get("content", "")
    else:
        reply = getattr(last_message, "content", "")

    print(reply)

    day3_root = Path(__file__).resolve().parent.parent
    artifact_path = day3_root / "artifacts" / "research_brief.md"

    print()

    if artifact_path.exists():
        print(f"Artifact created: {artifact_path}")
    else:
        print("Artifact was not created.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())