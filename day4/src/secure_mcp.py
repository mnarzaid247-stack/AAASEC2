import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth import require_scopes
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier


load_dotenv()


# ============================================================
# AUTH CONFIGURATION
# ============================================================

STUDENT_TOKEN = os.getenv(
    "MCP_STUDENT_TOKEN",
    "student-secret-token",
)

ADMIN_TOKEN = os.getenv(
    "MCP_ADMIN_TOKEN",
    "admin-secret-token",
)


token_verifier = StaticTokenVerifier(
    tokens={
        STUDENT_TOKEN: {
            "client_id": "student",
            "scopes": [
                "read:public",
            ],
        },

        ADMIN_TOKEN: {
            "client_id": "admin",
            "scopes": [
                "read:public",
                "read:internal",
            ],
        },
    }
)


# ============================================================
# MCP SERVER
# ============================================================

mcp = FastMCP(
    "Manar Secure MCP Tools",
    auth=token_verifier,
)


# ============================================================
# PUBLIC TOOL
# ============================================================

@mcp.tool
def get_server_time() -> str:
    """
    Return the current UTC server time.
    Available to any authenticated client.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# PROTECTED FINANCIAL TOOL
# ============================================================

@mcp.tool(
    auth=require_scopes(
        "read:internal"
    )
)
def get_internal_report() -> dict:
    """
    Return protected quarterly financial data.
    Requires read:internal scope.
    """

    return {
        "quarter": "Q3-2026",
        "months": [
            {
                "month": "July",
                "revenue_sar": 412000,
                "costs_sar": 298000,
            },
            {
                "month": "August",
                "revenue_sar": 385000,
                "costs_sar": 310000,
            },
            {
                "month": "September",
                "revenue_sar": 505000,
                "costs_sar": 342000,
            },
        ],
        "classification": "internal",
    }


# ============================================================
# CHALLENGE — CUSTOM PROTECTED TOOL
# ============================================================

@mcp.tool(
    auth=require_scopes(
        "read:internal"
    )
)
def get_model_evaluation_results() -> dict:
    """
    Return internal AI model evaluation results.
    Requires read:internal scope.
    """

    return {
        "evaluation": "Internal AI Model Benchmark",
        "models": [
            {
                "name": "Model Alpha",
                "accuracy": 91,
                "reasoning": 88,
                "safety": 94,
            },
            {
                "name": "Model Beta",
                "accuracy": 87,
                "reasoning": 93,
                "safety": 90,
            },
            {
                "name": "Model Gamma",
                "accuracy": 94,
                "reasoning": 91,
                "safety": 86,
            },
        ],
        "scale": "0-100",
        "classification": "internal",
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8002,
    )