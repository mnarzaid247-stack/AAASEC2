import os
import time
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import build_agent

# ============================================================
# ENVIRONMENT
# ============================================================

STUDENT_NAME = os.getenv(
    "STUDENT_NAME",
    "Manar Zaid",
)

PUBLIC_URL = os.getenv(
    "PUBLIC_URL",
    "http://localhost:8000",
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Day 3 Agent API",
    version="1.0.0",
)


# Build the agent only once when the application starts.
agent = build_agent()


# ============================================================
# REQUEST MODEL
# ============================================================

class ResponseRequest(BaseModel):
    input: str
    model: str | None = None


# ============================================================
# HELPER
# ============================================================

def extract_agent_reply(result) -> str:
    """
    Extract the final assistant text from the agent result.
    """

    messages = result.get(
        "messages",
        [],
    )

    if not messages:
        return ""

    last_message = messages[-1]

    if isinstance(last_message, dict):
        return str(
            last_message.get(
                "content",
                "",
            )
        )

    return str(
        getattr(
            last_message,
            "content",
            "",
        )
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/healthz")
async def health_check():

    return {
        "status": "ok"
    }


# ============================================================
# OPENRESPONSES ENDPOINT
# ============================================================

@app.post("/v1/responses")
async def create_response(
    request: ResponseRequest,
):

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": request.input,
                }
            ]
        }
    )

    reply = extract_agent_reply(
        result
    )

    model_name = (
        request.model
        or "day3-agent"
    )

    return {
        "id": f"resp_{uuid.uuid4().hex}",
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model_name,
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": reply,
                    }
                ],
            }
        ],
    }


# ============================================================
# A2A AGENT CARD
# ============================================================

@app.get("/.well-known/agent-card.json")
async def agent_card():

    return {
        "protocolVersion": "1.0",
        "name": f"{STUDENT_NAME} Day 3 Agent",
        "description": (
            "A Deep Agent exposed through "
            "an OpenResponses-compatible API."
        ),
        "url": (
            f"{PUBLIC_URL.rstrip('/')}"
            f"/v1/responses"
        ),
        "version": "0.1.0",
        "capabilities": {
            "streaming": False,
        },
        "defaultInputModes": [
            "text/plain",
        ],
        "defaultOutputModes": [
            "text/plain",
        ],
        "skills": [
            {
                "id": "calculate",
                "name": "Calculate",
                "description": (
                    "Evaluate simple arithmetic expressions."
                ),
                "tags": [
                    "math",
                    "calculation",
                ],
            },
            {
                "id": "current-time",
                "name": "Current Time",
                "description": (
                    "Return the current local date and time."
                ),
                "tags": [
                    "time",
                    "utility",
                ],
            },
        ],
    }