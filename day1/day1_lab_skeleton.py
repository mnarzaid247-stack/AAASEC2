import os
import operator
from datetime import datetime
from typing import Annotated, List, Dict
from typing_extensions import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
load_dotenv()

class AgentState(TypedDict):
    topic: str
    search_query: str
    collected_data: List[Dict]
    analyzed_data: List[Dict]
    quality_score: int
    iteration_count: int
    final_report: str
    execution_logs: Annotated[List[str], operator.add]


llm = ChatOpenAI(
    model = "nvidia/nemotron-3-super-120b-a12b:free", 
    temperature  = 0, 
    base_url="https://openrouter.ai/api/v1",
    )

search_tool = TavilySearch(max_results=5)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store = InMemoryVectorStore(
    embedding=embeddings
)

class QualityScore(BaseModel):
    """Evaluation of research quality."""
    score: int = Field(ge=1, le=10)
    reasoning: str = Field(description="One-sentence justification")

evaluator = llm.with_structured_output(QualityScore)

def collect_node(state: AgentState):
    """Search the web. On retries, CHANGE the query!"""
    iteration = state["iteration_count"] + 1 
    if iteration == 1:
        query = state["topic"]
    elif iteration == 2:
        query = f"{state['topic']} detailed research"
    else:
        query = f"{state['topic']} latest developments"  
    results = search_tool.invoke({"query": query})["results"]
    return {
        "search_query": query,
        "collected_data": results,
        "iteration_count": iteration,
        "execution_logs": [f"Search iteration {iteration}: {query}"]
    }

def store_memory_node(state: AgentState):
    """Save source contents into the vector store."""
    contents = [result["content"] for result in state["collected_data"]]
    vector_store.add_texts(contents)
    return {
    "execution_logs": [f"Stored {len(contents)} sources in memory"]
    }


def analyze_node(state: AgentState):
    """LLM-analyze each source. Bonus: retrieve related past
    research with vector_store.similarity_search(content, k=2)
    and include it in the prompt — that's what makes this RAG."""
    analyses = []
    for source in state["collected_data"]:
        content = source["content"]
        response = llm.invoke([HumanMessage(content=f"Analyze this research source:\n{content}")])
        analyses.append({
            "analysis": response.content
        })
    return {
    "analyzed_data": analyses,
    "execution_logs": [f"Analyzed {len(analyses)} sources "]
    }


def evaluate_node(state: AgentState):
    """Score the research with the STRUCTURED evaluator (Step 3)."""
    analyses_text = "\n\n".join(
        item["analysis"] for item in state["analyzed_data"]
    )

    result = evaluator.invoke(
        [
            HumanMessage(
                content=(
                    "Evaluate the quality of this research from 1 to 10. "
                    "Consider relevance, depth, clarity, and usefulness.\n\n"
                    f"{analyses_text}"
                )
            )
        ]
    )

    return {
        "quality_score": result.score,
        "execution_logs": [
            f"Quality score: {result.score} - {result.reasoning}"
        ]
    }
    

def report_node(state: AgentState):
    analyses = "\n\n".join(
        f"Source: {item.get('title', 'Untitled')}\nAnalysis: {item.get('analysis', item)}"
        for item in state["analyzed_data"]
    )
    response = llm.invoke(
        "Write a concise enterprise research report on "
        f"{state['topic']} using the following source analyses. Include key findings, "
        f"business implications, and recommended next steps.\n\n{analyses}"
    )
    return {
        "final_report": response.content,
        "execution_logs": ["Generated enterprise report"],
    }


def audit_node(state: AgentState):
    """Log completion stats."""
    return {
        "execution_logs": [
            f"Audit completed at {datetime.now().isoformat()} | "
            f"Iterations: {state['iteration_count']} | "
            f"Quality score: {state['quality_score']}"
        ]
    }


# ============================================================
# STEP 5 — THE CONDITIONAL EDGE (the heart of this lab)
# ============================================================
# Write a router function: takes state, RETURNS THE NAME of the
# next node as a string.
#
# CRITICAL — loops must terminate. Two rules:
#   a) every retry must change something (your query, Step 4.2),
#   b) hard-cap the retries with iteration_count.
# Without both, same search → same score → infinite loop → LangGraph
# kills the run at recursion limit 25 with GraphRecursionError.
#
# WHERE TO LOOK (read BOTH):
#   - "Conditional branching":
#     https://docs.langchain.com/oss/python/langgraph/use-graph-api#conditional-branching
#   - "Create and control loops":
#     https://docs.langchain.com/oss/python/langgraph/use-graph-api#create-and-control-loops
#
# EXPERIMENT: comment out the iteration cap, force low scores, run,
# and read the GraphRecursionError message. Now you understand why
# the docs insist on termination conditions.

def quality_router(state: AgentState) -> str:
    if state["quality_score"] >= 7:
        return "report"

    if state["iteration_count"] >= 3:
        return "report"

    return "collect"


workflow = StateGraph(AgentState)

workflow.add_node("collect", collect_node)
workflow.add_node("store_memory", store_memory_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("report", report_node)
workflow.add_node("audit", audit_node)

workflow.add_edge(START, "collect")
workflow.add_edge("collect", "store_memory")
workflow.add_edge("store_memory", "analyze")
workflow.add_edge("analyze", "evaluate")

workflow.add_conditional_edges(
    "evaluate",
    quality_router,
    {
        "collect": "collect",
        "report": "report",
    },
)

workflow.add_edge("report", "audit")
workflow.add_edge("audit", END)


if __name__ == "__main__":
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
app = workflow.compile(checkpointer=InMemorySaver())

print(app.get_graph().draw_mermaid())

config = {
    "configurable": {
        "thread_id": "run-1"
    }
}

final_state = None

for chunk in app.stream(
    initial_state,
    config,
    stream_mode="values"
):
    final_state = chunk
    print(chunk)

if final_state:
    print("\nFINAL REPORT:\n")
    print(final_state["final_report"])

    print("\nEXECUTION LOGS:\n")
    for log in final_state["execution_logs"]:
        print(log)
