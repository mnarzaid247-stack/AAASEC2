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
# PROTECTED MCP TOOL
# ============================================================

# This tool will be implemented in secure_mcp.py.
MY_TOOL_NAME = "get_model_evaluation_results"


# ============================================================
# MCP DATA FETCHER
# ============================================================

def fetch_my_data() -> str:
    """
    Fetch protected AI model evaluation data
    from the authenticated MCP server.
    """

    async def call_mcp() -> str:

        async with Client(
            MCP_URL,
            auth=BearerAuth(
                token=ADMIN_TOKEN
            ),
        ) as client:

            result = await client.call_tool(
                MY_TOOL_NAME,
                {},
            )

            return json.dumps(
                result.data
            )

    return asyncio.run(
        call_mcp()
    )


# ============================================================
# AGENT MISSION
# ============================================================

MISSION = (
    "1. Call fetch_my_data to retrieve the protected AI model "
    "evaluation results. "

    "2. Write a Python program named analyze_models.py that reads "
    "the returned evaluation data and calculates the average score "
    "for each model across all evaluation metrics. "

    "3. Determine which model has the highest average score and "
    "calculate the difference between the highest and lowest "
    "average scores. "

    "4. Save the Python program inside the work directory and "
    "execute it using the shell. "

    "5. Report exactly what the Python program printed, then add "
    "one short insight about the model performance."
)


# ============================================================
# BUILD AND RUN CHALLENGE AGENT
# ============================================================

if __name__ == "__main__":

    backend, cleanup = make_backend()

    try:

        agent = create_deep_agent(
            model=llm,
            system_prompt=SYSTEM_PROMPT,
            tools=[
                fetch_my_data,
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

        final_message = result[
            "messages"
        ][-1]

        print(
            final_message.content
        )

    finally:
        cleanup()