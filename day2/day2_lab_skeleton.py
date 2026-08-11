import os
import operator
from datetime import datetime
from typing import Annotated, List, Literal
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

MAX_REVISIONS = 2      
MAX_TURNS = 12 
class TeamState(TypedDict):
    task: str
    execution_logs: Annotated[List[str], operator.add]
    research_notes: Annotated[List[str], operator.add]
    draft: str
    analysis: str
    revision_count: int
    next_agent: str
    critique: str
    turn_count: int

class RouterDecision(BaseModel):
    """The supervisor's choice of who acts next."""
    next_agent: Literal["researcher", "analyst", "writer", "critic", "FINISH"]
    reason: str = Field(description="One sentence explaining the choice")

PERSONAS = {
    "researcher": """
You are a research specialist.
Your job is to find relevant and reliable information and summarize the key facts from the sources.
Do not analyze the findings, write the final report, or critique the work.
""",

    "analyst": """
You are an analysis specialist.
Your job is to analyze the research notes, identify key findings, patterns, risks, and implications.
Do not search the web, write the final report, or critique the work.
""",
    "writer": """
You are a professional report writer.
Your job is to write a clear, concise, and well-structured report using the provided analysis.
If critique is provided, revise the previous draft according to that feedback.
Do not search the web, perform new analysis, or critique your own work.
""",

    "critic": """
You are a strict report reviewer.
Your job is to review the draft against the research notes and identify any important problems.
Reply with "APPROVED" if the draft is good enough, or "REVISE: <fixes>" if changes are needed.
Do not search the web, perform new research, or rewrite the report yourself.
"""
}

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
)
search_tool = TavilySearch(max_results=4)
supervisor_llm = llm.with_structured_output(RouterDecision)
def run_persona(role, user_content):
    response = llm.invoke([
        SystemMessage(content=PERSONAS[role]),
        HumanMessage(content=user_content),
    ])
    return response.content


def supervisor_node(state: TeamState):
    turn_count = state["turn_count"] + 1

    status = f"""
Task: {state["task"]}

Research notes available: {bool(state["research_notes"])}
Analysis available: {bool(state["analysis"])}
Draft available: {bool(state["draft"])}
Critique: {state["critique"] if state["critique"] else "None"}
Revision count: {state["revision_count"]}
Turn count: {turn_count}
"""

    decision = supervisor_llm.invoke([
        HumanMessage(
            content=f"""
You are supervising a multi-agent research team.

Choose who should act next:
- researcher
- analyst
- writer
- critic
- FINISH

Current team status:
{status}
"""
        )
    ])

    next_agent = decision.next_agent

    if turn_count > MAX_TURNS:
        next_agent = "FINISH"

    if (
        next_agent in ["writer", "critic"]
        and state["revision_count"] >= MAX_REVISIONS
        and state["draft"]
    ):
        next_agent = "FINISH"

    return {
        "next_agent": next_agent,
        "turn_count": turn_count,
        "execution_logs": [
            f"Supervisor chose {next_agent}: {decision.reason}"
        ],
    }

def researcher_node(state: TeamState):
    task = state["task"]

    search_results = search_tool.invoke({
        "query": task
    })["results"]

    sources_text = "\n\n".join(
        f"Title: {item.get('title', 'Untitled')}\n"
        f"Content: {item.get('content', '')}"
        for item in search_results
    )

    notes = run_persona(
        "researcher",
        f"""
Task:
{task}

Web search results:
{sources_text}

Summarize the most relevant facts and evidence for the team.
"""
    )

    return {
        "research_notes": [notes],
        "execution_logs": [
            f"Researcher collected {len(search_results)} sources"
        ],
    }


def analyst_node(state: TeamState):
    research_text = "\n\n".join(state["research_notes"])

    analysis = run_persona(
        "analyst",
        f"""
Task:
{state["task"]}

Research notes:
{research_text}

Analyze the research and identify the key findings,
patterns, risks, and implications.
"""
    )

    return {
        "analysis": analysis,
        "execution_logs": ["Analyst completed the analysis"],
    }


def writer_node(state: TeamState):
    """Write the draft — or REVISE it if a critique is present."""

    revising = (
        bool(state["critique"])
        and state["critique"].startswith("REVISE")
    )

    if revising:
        prompt = f"""
Task:
{state["task"]}

Analysis:
{state["analysis"]}

Previous draft:
{state["draft"]}

Critique:
{state["critique"]}

Revise the draft based on the critique.
Keep the report clear, concise, and well structured.
"""
    else:
        prompt = f"""
Task:
{state["task"]}

Analysis:
{state["analysis"]}

Write a clear, concise, and well-structured draft report.
"""

    draft = run_persona(
        "writer",
        prompt,
    )

    return {
        "draft": draft,
        "critique": "",
        "revision_count": (
            state["revision_count"] + 1
            if revising
            else state["revision_count"]
        ),
        "execution_logs": [
            "Writer revised the draft"
            if revising
            else "Writer created the first draft"
        ],
    }


def critic_node(state: TeamState):
    """Review the draft against the research notes."""

    research_text = "\n\n".join(state["research_notes"])

    critique = run_persona(
        "critic",
        f"""
Task:
{state["task"]}

Research notes:
{research_text}

Analysis:
{state["analysis"]}

Draft:
{state["draft"]}

Review the draft carefully against the research.
Reply with exactly one of these formats:

APPROVED

or

REVISE: <specific fixes needed>
"""
    )

    return {
        "critique": critique.strip(),
        "execution_logs": [
            f"Critic reviewed the draft: {critique.strip()}"
        ],
    }


def route_from_supervisor(state: TeamState) -> str:
    return state["next_agent"]

workflow = StateGraph(TeamState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("writer", writer_node)
workflow.add_node("critic", critic_node)
workflow.add_edge(START, "supervisor")

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

for worker in ["researcher", "analyst", "writer", "critic"]:
    workflow.add_edge(worker, "supervisor")
    
if __name__ == "__main__":
    initial_state = {
        "task": "Should our company adopt multi-agent AI systems in 2026?",
        "research_notes": [],
        "analysis": "",
        "draft": "",
        "critique": "",
        "revision_count": 0,
        "turn_count": 0,
        "next_agent": "",
        "execution_logs": [],
    }
    app = workflow.compile(
    checkpointer=InMemorySaver()
)
    print(app.get_graph().draw_mermaid())
    config = {
    "configurable": {
        "thread_id": "day2-run-1"
    }
}
    final_state = None

for chunk in app.stream(
    initial_state,
    config,
    stream_mode="values",
):
    final_state = chunk
    print(chunk)
    if final_state:
        print("\nFINAL DRAFT:\n")
        print(final_state["draft"])

        print("\nSTATS:\n")
        print(f"Turns: {final_state['turn_count']}")
        print(f"Revisions: {final_state['revision_count']}")
        print(f"Final critique: {final_state['critique']}")

        print("\nEXECUTION LOGS:\n")
        for log in final_state["execution_logs"]:
            print(log)

