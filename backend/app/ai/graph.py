from langgraph.graph import StateGraph, START, END
import time
from typing import Any, TypedDict
from app.ai.agent import (
    analyze_user_request,
    generate_rag_answer,
)
from app.ai.tools import structured_search_songs
from app.ai.semantic_search import (
    semantic_search_songs,
    hybrid_search_songs,
)


class AgentState(TypedDict, total=False):
    """
    Shared state that moves through the Nagham AI LangGraph.
    """

    # Original message from the user
    user_message: str

    # Result produced by the intent-analysis node
    analysis: dict[str, Any]
    
    # Active SQLAlchemy database session
    db: Any

    # Maximum number of songs to retrieve
    limit: int

    # Search strategy selected by the router:
    # structured | semantic | hybrid
    search_type: str

    # Songs retrieved from the database
    results: list[Any]

    # Final grounded RAG response
    answer: str
    
    

# def analyze_node(state: AgentState) -> dict:
#     """
#     Analyze the user's natural-language request
#     and store the extracted intent in the graph state.
#     """

#     user_message = state["user_message"]

#     analysis = analyze_user_request(user_message)

#     return {
#         "analysis": analysis
#     }


def analyze_node(state: AgentState) -> dict:
    start = time.perf_counter()

    user_message = state["user_message"]
    analysis = analyze_user_request(user_message)

    print(f"[TIMING] Analyze: {time.perf_counter() - start:.2f}s")

    return {"analysis": analysis}
    



def route_search(state: AgentState) -> str:
    """
    Decide which search strategy should be used
    based on the analyzed user request.
    """

    analysis = state["analysis"]

    semantic_query = analysis.get("semantic_query")

    has_semantic = bool(
        semantic_query and semantic_query.strip()
    )

    has_structured = any([
        analysis.get("maqam"),
        analysis.get("artist"),
        analysis.get("artists"),
        analysis.get("composers"),
        analysis.get("difficulty"),
        analysis.get("year"),
        analysis.get("filter_groups"),
    ])

    if has_semantic and has_structured:
        return "hybrid"

    if has_structured:
        return "structured"

    return "semantic"




def structured_search_node(state: AgentState) -> dict:
    """
    Search using structured database constraints only.
    """

    analysis = state["analysis"]

    songs = structured_search_songs(
        db=state["db"],
        maqam=analysis.get("maqam"),
        artist=analysis.get("artist"),
        difficulty=analysis.get("difficulty"),
        year=analysis.get("year"),
        filter_groups=analysis.get("filter_groups"),
        limit=get_result_limit(state),
    )

    # Normalize results to the same structure used
    # by semantic and hybrid search.
    results = [
        {
            "song": song,
            "similarity": None,
        }
        for song in songs
    ]

    return {
        "search_type": "structured",
        "results": results,
    }


def semantic_search_node(state: AgentState) -> dict:
    """
    Search songs by semantic meaning only.
    """

    analysis = state["analysis"]

    semantic_query = (
        analysis.get("semantic_query")
        or state["user_message"]
    )

    results = semantic_search_songs(
        db=state["db"],
        query=semantic_query,
        moods=analysis.get("moods"),
        topics=analysis.get("topics"),
        limit=get_result_limit(state),
    )

    return {
        "search_type": "semantic",
        "results": results,
    }



def hybrid_search_node(state: AgentState) -> dict:
    start = time.perf_counter()

    analysis = state["analysis"]
    
    print("\n[HYBRID ANALYSIS]")
    print("semantic_query:", analysis.get("semantic_query"))
    print("moods:", analysis.get("moods"))
    print("topics:", analysis.get("topics"))
    print("artist:", analysis.get("artist"))
    print("filter_groups:", analysis.get("filter_groups"))
    print("maqam:", analysis.get("maqam"))
    print("result_limit:", analysis.get("result_limit"))

    results = hybrid_search_songs(
        db=state["db"],
        semantic_query=analysis["semantic_query"],
        maqam=analysis.get("maqam"),
        artist=analysis.get("artist"),
        difficulty=analysis.get("difficulty"),
        year=analysis.get("year"),
        moods=analysis.get("moods"),
        topics=analysis.get("topics"),
        filter_groups=analysis.get("filter_groups"),
        limit=get_result_limit(state),
    )

    print(f"[TIMING] Hybrid Search: {time.perf_counter() - start:.2f}s")

    return {
        "search_type": "hybrid",
        "results": results,
    }
    



# def generate_answer_node(state: AgentState) -> dict:
#     """
#     Generate the final grounded answer from retrieved songs.
#     """

#     answer = generate_rag_answer(
#         user_message=state["user_message"],
#         search_results=state["results"],
#     )

#     return {
#         "answer": answer
#     }

def generate_answer_node(state: AgentState) -> dict:
    start = time.perf_counter()

    answer = generate_rag_answer(
        user_message=state["user_message"],
        search_results=state["results"],
    )

    print(f"[TIMING] RAG Answer: {time.perf_counter() - start:.2f}s")

    return {"answer": answer}
    
    
    


def build_nagham_graph():
    """
    Build and compile the Nagham AI agent graph.
    """

    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("analyze", analyze_node)
    graph.add_node("structured_search", structured_search_node)
    graph.add_node("semantic_search", semantic_search_node)
    graph.add_node("hybrid_search", hybrid_search_node)
    graph.add_node("generate_answer", generate_answer_node)

    # Start with intent analysis
    graph.add_edge(START, "analyze")

    # Route to the appropriate search strategy
    graph.add_conditional_edges(
        "analyze",
        route_search,
        {
            "structured": "structured_search",
            "semantic": "semantic_search",
            "hybrid": "hybrid_search",
        },
    )

    # All search strategies continue to RAG answer generation
    graph.add_edge("structured_search", "generate_answer")
    graph.add_edge("semantic_search", "generate_answer")
    graph.add_edge("hybrid_search", "generate_answer")

    # Finish after generating the answer
    graph.add_edge("generate_answer", END)

    return graph.compile()


nagham_graph = build_nagham_graph()



def get_result_limit(state: AgentState) -> int:
    analysis = state.get("analysis", {})

    requested_limit = analysis.get("result_limit")

    if requested_limit is not None:
        return max(1, min(requested_limit, 10))

    return state.get("limit", 5)