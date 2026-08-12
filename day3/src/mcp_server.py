from pathlib import Path
import ast
import operator
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