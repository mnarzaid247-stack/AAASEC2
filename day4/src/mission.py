import asyncio
import json
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

from deepagents import create_deep_agent
from shell_agent import SYSTEM_PROMPT, llm, make_backend


load_dotenv()


MCP_URL = os.getenv(
    "MCP_URL",
    "http://localhost:8002/mcp",
)

ADMIN_TOKEN = os.getenv(
    "MCP_ADMIN_TOKEN",
    "admin-secret-token",
)


# ============================================================
# PROTECTED MCP DATA TOOL
# ============================================================

def fetch_internal_report() -> str:
    """
    Retrieve the protected quarterly report
    from the authenticated MCP server.
    """

    async def fetch() -> str:

        async with Client(
            MCP_URL,
            auth=BearerAuth(token=ADMIN_TOKEN),
        ) as client:

            result = await client.call_tool(
                "get_internal_report",
                {},
            )

            return json.dumps(
                result.data
            )

    return asyncio.run(
        fetch()
    )


# ============================================================
# MISSION
# ============================================================

MISSION = (
    "First, call fetch_internal_report to retrieve the protected "
    "quarterly financial data. "

    "Then create a Python file named financial_analysis.py inside "
    "the work directory. "

    "The program must calculate total revenue, total costs, and "
    "profit for each month. It must also calculate the overall "
    "profit margin for the complete dataset and identify the month "
    "with the highest profit. "

    "Execute the Python program using the shell. "

    "Finally, report exactly the numerical results printed by the "
    "program and add one short business insight based on those results."
)


# ============================================================
# RUN MISSION
# ============================================================

if __name__ == "__main__":

    backend, cleanup = make_backend()

    try:

        agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                fetch_internal_report,
            ],
            backend=backend,
        )

        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": MISSION,
                    }
                ]
            }
        )

        final_message = result["messages"][-1]

        print(
            final_message.content
        )

    finally:
        cleanup()