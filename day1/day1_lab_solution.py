import os
import operator
from datetime import datetime
from typing import Annotated, List, Dict
from typing_extensions import TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage
from langchain_core.vectorstores import InMemoryVectorStore

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()

USE_FAKE = os.getenv("USE_FAKE", "0") == "1"


# ============================================================
# STEP 1 — STATE
# ============================================================

class AgentState(TypedDict):
    topic: str
    search_query: str
    collected_data: List[Dict]
    analyzed_data: List[Dict]
    quality_score: int
    iteration_count: int
    final_report: str
    execution_logs: Annotated[List[str], operator.add]


# ============================================================
# STEP 3 — STRUCTURED OUTPUT
# ============================================================

class QualityScore(BaseModel):
    """Evaluation of research quality."""

    score: int = Field(ge=1, le=10)
    reasoning: str = Field(
        description="One-sentence justification"
    )


# ============================================================
# STEP 2 — MODEL + SEARCH + EMBEDDINGS
# ============================================================

if USE_FAKE:

    from langchain_core.embeddings import DeterministicFakeEmbedding

    class FakeLLM:
        def invoke(self, messages):

            class Response:
                content = (
                    "Key findings: multi-agent orchestration, "
                    "state-graph workflows, and guardrails dominate "
                    "enterprise agentic AI adoption in 2026."
                )

            return Response()

    class FakeEvaluator:

        def __init__(self):
            self.calls = 0

        def invoke(self, messages):

            self.calls += 1

            if self.calls == 1:
                return QualityScore(
                    score=5,
                    reasoning="Only one shallow pass over the sources."
                )

            return QualityScore(
                score=8,
                reasoning="Second pass added breadth and depth."
            )

    class FakeSearch:

        def invoke(self, payload):

            query = payload["query"]

            return {
                "results": [
                    {
                        "title": f"Fake source A for: {query}",
                        "url": "https://example.com/a",
                        "content": (
                            f"Deterministic content about {query} "
                            f"— trends, tooling, adoption."
                        ),
                    },
                    {
                        "title": f"Fake source B for: {query}",
                        "url": "https://example.com/b",
                        "content": (
                            f"Deterministic content about {query} "
                            f"— risks, governance, ROI."
                        ),
                    },
                ]
            }

    llm = FakeLLM()
    evaluator = FakeEvaluator()
    search_tool = FakeSearch()

    embeddings = DeterministicFakeEmbedding(
        size=256
    )

else:

    from langchain_openai import ChatOpenAI
    from langchain_tavily import TavilySearch

    llm = ChatOpenAI(
        model="nvidia/nemotron-3-super-120b-a12b:free",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
    )

    evaluator = llm.with_structured_output(
        QualityScore
    )

    search_tool = TavilySearch(
        max_results=5
    )

    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name=(
                "sentence-transformers/"
                "all-MiniLM-L6-v2"
            )
        )

    except ImportError:

        from langchain_core.embeddings import DeterministicFakeEmbedding

        embeddings = DeterministicFakeEmbedding(
            size=256
        )


vector_store = InMemoryVectorStore(
    embeddings
)


# ============================================================
# STEP 4 — NODES
# ============================================================

def collect_node(state: AgentState):

    iteration = state["iteration_count"] + 1

    angles = {
        1: f"{state['topic']} overview 2026",
        2: (
            f"{state['topic']} "
            f"case studies implementation challenges"
        ),
        3: (
            f"{state['topic']} "
            f"ROI metrics production deployments"
        ),
    }

    query = angles.get(
        iteration,
        f"{state['topic']} latest developments"
    )

    results = search_tool.invoke(
        {"query": query}
    )["results"]

    sources = [
        {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", ""),
        }
        for result in results
    ]

    return {
        "search_query": query,
        "collected_data": sources,
        "iteration_count": iteration,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"collect (iter {iteration}): "
                f"'{query}' → {len(sources)} sources"
            )
        ],
    }


def store_memory_node(state: AgentState):

    texts = [
        source["content"]
        for source in state["collected_data"]
        if source["content"]
    ]

    if texts:
        vector_store.add_texts(texts)

    return {
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"store_memory: "
                f"{len(texts)} chunks embedded"
            )
        ]
    }


def analyze_node(state: AgentState):

    analyzed = []

    for source in state["collected_data"]:

        related = vector_store.similarity_search(
            source["content"],
            k=2,
        )

        related_context = "\n".join(
            document.page_content[:200]
            for document in related
        )

        prompt = (
            f"Topic: {state['topic']}\n\n"
            f"Source: {source['title']}\n"
            f"{source['content']}\n\n"
            f"Related prior research:\n"
            f"{related_context}\n\n"
            f"Extract the 2-3 most important insights "
            f"as concise bullet points."
        )

        response = llm.invoke(
            [
                HumanMessage(
                    content=prompt
                )
            ]
        )

        analyzed.append(
            {
                "title": source["title"],
                "url": source["url"],
                "insights": response.content,
            }
        )

    return {
        "analyzed_data": analyzed,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"analyze: "
                f"{len(analyzed)} sources analyzed"
            )
        ],
    }


def evaluate_node(state: AgentState):

    summary = "\n".join(
        item["insights"]
        for item in state["analyzed_data"]
    )

    result = evaluator.invoke(
        [
            HumanMessage(
                content=(
                    f"Rate this research on "
                    f"'{state['topic']}' from 1-10 "
                    f"for depth, breadth, and usefulness "
                    f"to an enterprise reader.\n\n"
                    f"{summary}"
                )
            )
        ]
    )

    return {
        "quality_score": result.score,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"evaluate: score={result.score} "
                f"({result.reasoning})"
            )
        ],
    }


def report_node(state: AgentState):

    insights = "\n\n".join(
        (
            f"### {item['title']}\n"
            f"Source: {item['url']}\n"
            f"{item['insights']}"
        )
        for item in state["analyzed_data"]
    )

    response = llm.invoke(
        [
            HumanMessage(
                content=(
                    f"Write a concise enterprise "
                    f"research report on "
                    f"'{state['topic']}' "
                    f"with an executive summary, "
                    f"key findings, and recommendations, "
                    f"based on:\n\n"
                    f"{insights}"
                )
            )
        ]
    )

    return {
        "final_report": response.content,
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"report: generated"
            )
        ],
    }


def audit_node(state: AgentState):

    return {
        "execution_logs": [
            (
                f"[{datetime.now():%H:%M:%S}] "
                f"audit: done | "
                f"iterations={state['iteration_count']} | "
                f"final_score={state['quality_score']} | "
                f"sources={len(state['collected_data'])}"
            )
        ]
    }


# ============================================================
# STEP 5 — ROUTER
# ============================================================

def quality_router(state: AgentState) -> str:

    if state["quality_score"] >= 7:
        return "report"

    if state["iteration_count"] >= 3:
        return "report"

    return "collect"


# ============================================================
# STEP 6 — BUILD GRAPH
# ============================================================

workflow = StateGraph(
    AgentState
)

workflow.add_node(
    "collect",
    collect_node
)

workflow.add_node(
    "store_memory",
    store_memory_node
)

workflow.add_node(
    "analyze",
    analyze_node
)

workflow.add_node(
    "evaluate",
    evaluate_node
)

workflow.add_node(
    "report",
    report_node
)

workflow.add_node(
    "audit",
    audit_node
)


workflow.add_edge(
    START,
    "collect"
)

workflow.add_edge(
    "collect",
    "store_memory"
)

workflow.add_edge(
    "store_memory",
    "analyze"
)

workflow.add_edge(
    "analyze",
    "evaluate"
)

workflow.add_conditional_edges(
    "evaluate",
    quality_router,
    {
        "collect": "collect",
        "report": "report",
    },
)

workflow.add_edge(
    "report",
    "audit"
)

workflow.add_edge(
    "audit",
    END
)


# ============================================================
# STEP 7 — COMPILE + RUN
# ============================================================

app = workflow.compile(
    checkpointer=InMemorySaver()
)


if __name__ == "__main__":

    print("=" * 60)
    print("GRAPH")
    print("=" * 60)

    print(
        app.get_graph().draw_mermaid()
    )

    initial_state = {
        "topic": "Enterprise Agentic AI Systems",
        "search_query": "",
        "collected_data": [],
        "analyzed_data": [],
        "quality_score": 0,
        "iteration_count": 0,
        "final_report": "",
        "execution_logs": [],
    }

    config = {
        "configurable": {
            "thread_id": "run-1"
        }
    }

    print()
    print("=" * 60)
    print(
        f"RUN (USE_FAKE={USE_FAKE})"
    )
    print("=" * 60)

    final_state = None

    for chunk in app.stream(
        initial_state,
        config,
        stream_mode="values",
    ):

        final_state = chunk

        if chunk["execution_logs"]:
            print(
                chunk["execution_logs"][-1]
            )

    print()
    print("=" * 60)
    print("FINAL REPORT")
    print("=" * 60)

    print(
        final_state["final_report"]
    )

    print()
    print("=" * 60)
    print("FULL EXECUTION LOG")
    print("=" * 60)

    for line in final_state["execution_logs"]:
        print(line)