import os
import operator
from datetime import datetime
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"

MAX_REVISIONS = 2
MAX_TURNS = 12


# ============================================================
# STATE
# ============================================================

class TeamState(TypedDict):
    task: str
    research_notes: Annotated[List[str], operator.add]
    analysis: str
    draft: str
    critique: str
    revision_count: int
    turn_count: int
    next_agent: str
    execution_logs: Annotated[List[str], operator.add]


# ============================================================
# SUPERVISOR DECISION SCHEMA
# ============================================================

class RouterDecision(BaseModel):
    next_agent: Literal[
        "researcher",
        "analyst",
        "writer",
        "critic",
        "FINISH",
    ]

    reason: str = Field(
        description="Reason for choosing the next agent"
    )


# ============================================================
# PERSONAS
# ============================================================

PERSONAS = {
    "researcher": (
        "You are a research agent. "
        "Collect factual information and summarize it as short bullet points. "
        "Include sources when available. "
        "Do not perform analysis."
    ),

    "analyst": (
        "You are an analysis agent. "
        "Read the research notes and identify patterns, risks, benefits, "
        "and important implications. "
        "Do not search for new information."
    ),

    "writer": (
        "You are a professional business writer. "
        "Use the available research and analysis to write a concise "
        "executive brief with key findings and a recommendation. "
        "If feedback is provided, revise the previous draft accordingly."
    ),

    "critic": (
        "You are a strict reviewer. "
        "Compare the draft with the research notes. "
        "If the draft is accurate and complete, respond with APPROVED. "
        "Otherwise respond with REVISE: followed by specific fixes."
    ),
}


# ============================================================
# MODEL SETUP
# ============================================================

if USE_FAKE:

    class FakeWorker:
        def __init__(self):
            self.critic_count = 0

        def run(self, role: str, prompt: str) -> str:

            if role == "researcher":
                return (
                    "- Multi-agent systems can divide complex work "
                    "between specialized agents.\n"
                    "- Supervisor patterns provide centralized routing "
                    "and coordination.\n"
                    "- Critic/revision loops can improve final output quality."
                )

            if role == "analyst":
                return (
                    "The main benefit of multi-agent systems is specialization. "
                    "However, additional coordination increases complexity and cost. "
                    "Supervisor-based orchestration can reduce uncontrolled behavior "
                    "by making routing decisions explicit."
                )

            if role == "writer":
                return (
                    "Executive Brief\n\n"
                    "Multi-agent AI systems can improve complex workflows by "
                    "assigning specialized responsibilities to different agents. "
                    "A supervisor can coordinate these agents while a critic can "
                    "review outputs before completion.\n\n"
                    "Recommendation: begin with a controlled pilot on one workflow "
                    "before wider adoption."
                )

            if role == "critic":
                self.critic_count += 1

                if self.critic_count == 1:
                    return (
                        "REVISE: make the recommendation more specific "
                        "and mention the coordination risk."
                    )

                return "APPROVED"

            return ""

    fake_worker = FakeWorker()

    def run_persona(role: str, prompt: str) -> str:
        return fake_worker.run(role, prompt)

    def supervisor_decide(state: TeamState) -> RouterDecision:

        if not state["research_notes"]:
            return RouterDecision(
                next_agent="researcher",
                reason="Research has not been collected yet.",
            )

        if not state["analysis"]:
            return RouterDecision(
                next_agent="analyst",
                reason="Research exists but still needs analysis.",
            )

        if not state["draft"]:
            return RouterDecision(
                next_agent="writer",
                reason="Analysis is ready and a draft is needed.",
            )

        if not state["critique"]:
            return RouterDecision(
                next_agent="critic",
                reason="The current draft needs review.",
            )

        if (
            state["critique"].startswith("REVISE")
            and state["revision_count"] < MAX_REVISIONS
        ):
            return RouterDecision(
                next_agent="writer",
                reason="The critic requested changes.",
            )

        return RouterDecision(
            next_agent="FINISH",
            reason="The draft is complete or the revision limit was reached.",
        )

else:

    from langchain_openai import ChatOpenAI
    from langchain_tavily import TavilySearch

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
    )

    search_tool = TavilySearch(max_results=4)

    supervisor_llm = llm.with_structured_output(
        RouterDecision
    )

    def run_persona(role: str, prompt: str) -> str:

        response = llm.invoke(
            [
                SystemMessage(
                    content=PERSONAS[role]
                ),
                HumanMessage(
                    content=prompt
                ),
            ]
        )

        return response.content

    def supervisor_decide(state: TeamState) -> RouterDecision:

        progress = (
            f"Task: {state['task']}\n"
            f"Research available: {bool(state['research_notes'])}\n"
            f"Analysis available: {bool(state['analysis'])}\n"
            f"Draft available: {bool(state['draft'])}\n"
            f"Critique: {state['critique'] or 'none'}\n"
            f"Revisions: {state['revision_count']} / {MAX_REVISIONS}\n"
        )

        return supervisor_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You supervise a team with four agents: "
                        "researcher, analyst, writer, and critic. "
                        "Choose exactly one next agent. "
                        "Use the normal order researcher -> analyst -> writer -> critic. "
                        "If critique requests revision, send work back to writer. "
                        "If the draft is approved or revision limit is reached, choose FINISH."
                    )
                ),
                HumanMessage(
                    content=progress
                ),
            ]
        )


# ============================================================
# SUPERVISOR NODE
# ============================================================

def supervisor_node(state: TeamState):

    new_turn = state["turn_count"] + 1

    if new_turn > MAX_TURNS:
        decision = RouterDecision(
            next_agent="FINISH",
            reason="Maximum number of supervisor turns reached.",
        )

    else:
        decision = supervisor_decide(state)

        if (
            decision.next_agent in {"writer", "critic"}
            and state["revision_count"] >= MAX_REVISIONS
            and state["draft"]
        ):
            decision = RouterDecision(
                next_agent="FINISH",
                reason="Maximum number of revisions reached.",
            )

    return {
        "next_agent": decision.next_agent,
        "turn_count": new_turn,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"Supervisor -> {decision.next_agent}: "
                f"{decision.reason}"
            )
        ],
    }


# ============================================================
# RESEARCHER
# ============================================================

def researcher_node(state: TeamState):

    if USE_FAKE:

        notes = run_persona(
            "researcher",
            state["task"],
        )

    else:

        results = search_tool.invoke(
            {
                "query": state["task"]
            }
        )["results"]

        search_text = "\n".join(
            (
                f"Title: {item.get('title', '')}\n"
                f"Content: {item.get('content', '')}\n"
                f"URL: {item.get('url', '')}"
            )
            for item in results
        )

        notes = run_persona(
            "researcher",
            (
                f"Research this task:\n"
                f"{state['task']}\n\n"
                f"Search results:\n"
                f"{search_text}"
            ),
        )

    return {
        "research_notes": [notes],
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] Researcher completed research"
        ],
    }


# ============================================================
# ANALYST
# ============================================================

def analyst_node(state: TeamState):

    all_notes = "\n\n".join(
        state["research_notes"]
    )

    analysis = run_persona(
        "analyst",
        (
            f"Task:\n"
            f"{state['task']}\n\n"
            f"Research notes:\n"
            f"{all_notes}"
        ),
    )

    return {
        "analysis": analysis,
        "execution_logs": [
            f"[{datetime.now():%H:%M:%S}] Analyst completed analysis"
        ],
    }


# ============================================================
# WRITER
# ============================================================

def writer_node(state: TeamState):

    needs_revision = (
        bool(state["critique"])
        and state["critique"].startswith("REVISE")
    )

    prompt = (
        f"Task:\n"
        f"{state['task']}\n\n"
        f"Research:\n"
        f"{'\n\n'.join(state['research_notes'])}\n\n"
        f"Analysis:\n"
        f"{state['analysis']}"
    )

    if needs_revision:
        prompt += (
            f"\n\nPrevious draft:\n"
            f"{state['draft']}\n\n"
            f"Reviewer feedback:\n"
            f"{state['critique']}"
        )

    new_draft = run_persona(
        "writer",
        prompt,
    )

    new_revision_count = state["revision_count"]

    if needs_revision:
        new_revision_count += 1

    return {
        "draft": new_draft,
        "critique": "",
        "revision_count": new_revision_count,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                + (
                    f"Writer completed revision {new_revision_count}"
                    if needs_revision
                    else "Writer created first draft"
                )
            )
        ],
    }


# ============================================================
# CRITIC
# ============================================================

def critic_node(state: TeamState):

    feedback = run_persona(
        "critic",
        (
            f"Task:\n"
            f"{state['task']}\n\n"
            f"Research notes:\n"
            f"{'\n\n'.join(state['research_notes'])}\n\n"
            f"Draft:\n"
            f"{state['draft']}"
        ),
    )

    return {
        "critique": feedback,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"Critic result: {feedback}"
            )
        ],
    }


# ============================================================
# ROUTING
# ============================================================

def route_from_supervisor(state: TeamState) -> str:
    return state["next_agent"]


# ============================================================
# GRAPH
# ============================================================

workflow = StateGraph(
    TeamState
)

workflow.add_node(
    "supervisor",
    supervisor_node,
)

workflow.add_node(
    "researcher",
    researcher_node,
)

workflow.add_node(
    "analyst",
    analyst_node,
)

workflow.add_node(
    "writer",
    writer_node,
)

workflow.add_node(
    "critic",
    critic_node,
)

workflow.add_edge(
    START,
    "supervisor",
)

workflow.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "researcher": "researcher",
        "analyst": "analyst",
        "writer": "writer",
        "critic": "critic",
        "FINISH": END,
    },
)

for worker in [
    "researcher",
    "analyst",
    "writer",
    "critic",
]:
    workflow.add_edge(
        worker,
        "supervisor",
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app = workflow.compile(
        checkpointer=InMemorySaver()
    )

    print("=" * 60)
    print("MULTI-AGENT GRAPH")
    print("=" * 60)

    print(
        app.get_graph().draw_mermaid()
    )

    initial_state = {
        "task": (
            "Should our company adopt "
            "multi-agent AI systems in 2026?"
        ),
        "research_notes": [],
        "analysis": "",
        "draft": "",
        "critique": "",
        "revision_count": 0,
        "turn_count": 0,
        "next_agent": "",
        "execution_logs": [],
    }

    config = {
        "configurable": {
            "thread_id": "day2-team-run"
        }
    }

    final_state = None

    print()
    print("=" * 60)
    print(f"RUNNING — USE_FAKE={USE_FAKE}")
    print("=" * 60)

    for state_update in app.stream(
        initial_state,
        config,
        stream_mode="values",
    ):

        final_state = state_update

        if state_update["execution_logs"]:
            print(
                state_update["execution_logs"][-1]
            )

    print()
    print("=" * 60)
    print("FINAL DRAFT")
    print("=" * 60)

    print(
        final_state["draft"]
    )

    print()
    print("=" * 60)
    print("FINAL STATS")
    print("=" * 60)

    print(
        f"Turns: {final_state['turn_count']}"
    )

    print(
        f"Revisions: {final_state['revision_count']}"
    )

    print(
        f"Final critique: {final_state['critique']}"
    )