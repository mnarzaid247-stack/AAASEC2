from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers.skills import SkillsDirectoryProvider


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP("Manar Zaid Tools")


# ============================================================
# TOOLS
# ============================================================

@mcp.tool
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


@mcp.tool
def word_stats(text: str) -> dict:
    """Return basic statistics about a text."""

    words = text.split()

    return {
        "characters": len(text),
        "words": len(words),
        "lines": len(text.splitlines()) or 1,
    }


# ============================================================
# SKILLS PROVIDER
# ============================================================

day3_root = Path(__file__).resolve().parent.parent

skills_path = day3_root / "skills"

mcp.add_provider(
    SkillsDirectoryProvider(
        roots=skills_path
    )
)


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001,
    )