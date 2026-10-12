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
from app.ai.conversation import (
    classify_deterministic_intent,
    run_comparison_node,
    run_follow_up_node,
    run_lyrics_request_node,
    run_recommend_similar_node,
    run_song_question_node,
    run_theory_node,
)
from app.ai.song_creation import run_song_creation_node


class AgentState(TypedDict, total=False):
    """
    Shared state that moves through the Nagham AI LangGraph.
    """

    # Original message from the user
    user_message: str

    # Prior turns of this conversation (session-scoped, never persisted
    # server-side -- see app/ai/conversation.py module docstring).
    history: list[dict[str, Any]]

    # Result produced by the intent-analysis node
    analysis: dict[str, Any]

    # Active SQLAlchemy database session
    db: Any

    # Maximum number of songs to retrieve
    limit: int

    # The authenticated user for this request, if any (app/core/security.py's
    # get_current_user_optional) -- None for anonymous requests. Only the
    # song_creation route requires this to be set.
    current_user: Any

    # Deterministic pre-classification result (set by classify_node)
    route: str
    maqam_matches: list[Any]
    resolved_song_id: int | None

    # Search strategy selected by the router:
    # structured | semantic | hybrid | theory_question | maqam_comparison |
    # song_question | follow_up | recommend_similar | lyrics_request
    search_type: str

    # Songs retrieved from the database
    results: list[Any]

    # Final grounded RAG response
    answer: str


def classify_node(state: AgentState) -> dict:
    """
    Deterministic routing pass, tried before the LLM intent extractor.
    See app/ai/conversation.py:classify_deterministic_intent for why this
    isn't left purely to the (small, local) LLM.
    """

    classified = classify_deterministic_intent(
        db=state["db"],
        message=state["user_message"],
        history=state.get("history"),
    )

    return {
        "route": classified.route,
        "maqam_matches": classified.maqam_matches,
        "resolved_song_id": classified.resolved_song_id,
        # Baseline analysis for the non-song-search routes (theory,
        # comparison, song_question, follow_up, recommend_similar), which
        # don't run the LLM intent extractor and so never overwrite this.
        # The song_search route's analyze_node always overwrites it with
        # the full extracted intent.
        "analysis": {"intent": classified.route},
    }


def route_after_classify(state: AgentState) -> str:
    return state["route"]


def analyze_node(state: AgentState) -> dict:
    start = time.perf_counter()

    user_message = state["user_message"]
    analysis = analyze_user_request(user_message, db=state["db"])

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
        analysis.get("exclude_filters"),
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
        exclude_filters=analysis.get("exclude_filters"),
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
    print("exclude_filters:", analysis.get("exclude_filters"))
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
        exclude_filters=analysis.get("exclude_filters"),
        limit=get_result_limit(state),
    )

    print(f"[TIMING] Hybrid Search: {time.perf_counter() - start:.2f}s")

    return {
        "search_type": "hybrid",
        "results": results,
    }


def generate_answer_node(state: AgentState) -> dict:
    start = time.perf_counter()

    answer = generate_rag_answer(
        user_message=state["user_message"],
        search_results=state["results"],
        contradictory=bool(state["analysis"].get("contradictory")),
    )

    print(f"[TIMING] RAG Answer: {time.perf_counter() - start:.2f}s")

    return {"answer": answer}


# --- Non-song-search intents: each is terminal (sets answer + results and
# goes straight to END), since they ground their answer internally rather
# than through the structured/semantic/hybrid + generate_answer pipeline. ---

def theory_node(state: AgentState) -> dict:
    return run_theory_node(
        db=state["db"],
        message=state["user_message"],
        maqam_matches=state.get("maqam_matches") or [],
    )


def comparison_node(state: AgentState) -> dict:
    return run_comparison_node(
        db=state["db"],
        message=state["user_message"],
        maqam_matches=state.get("maqam_matches") or [],
    )


def song_question_node(state: AgentState) -> dict:
    return run_song_question_node(
        db=state["db"],
        song_id=state["resolved_song_id"],
        message=state["user_message"],
    )


def follow_up_node(state: AgentState) -> dict:
    return run_follow_up_node(
        db=state["db"],
        message=state["user_message"],
        history=state.get("history") or [],
    )


def recommend_similar_node(state: AgentState) -> dict:
    return run_recommend_similar_node(
        db=state["db"],
        message=state["user_message"],
        history=state.get("history") or [],
        limit=get_result_limit(state),
    )


def lyrics_request_node(state: AgentState) -> dict:
    return run_lyrics_request_node(
        db=state["db"],
        song_id=state.get("resolved_song_id"),
        message=state["user_message"],
    )


def song_creation_node(state: AgentState) -> dict:
    return run_song_creation_node(
        db=state["db"],
        message=state["user_message"],
        history=state.get("history") or [],
        current_user=state.get("current_user"),
    )


def build_nagham_graph():
    """
    Build and compile the Nagham AI agent graph.
    """

    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("classify", classify_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("structured_search", structured_search_node)
    graph.add_node("semantic_search", semantic_search_node)
    graph.add_node("hybrid_search", hybrid_search_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("theory", theory_node)
    graph.add_node("comparison", comparison_node)
    graph.add_node("song_question", song_question_node)
    graph.add_node("follow_up", follow_up_node)
    graph.add_node("recommend_similar", recommend_similar_node)
    graph.add_node("lyrics_request", lyrics_request_node)
    graph.add_node("song_creation", song_creation_node)

    graph.add_edge(START, "classify")

    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "song_search": "analyze",
            "theory_question": "theory",
            "maqam_comparison": "comparison",
            "song_question": "song_question",
            "follow_up": "follow_up",
            "recommend_similar": "recommend_similar",
            "lyrics_request": "lyrics_request",
            "song_creation": "song_creation",
        },
    )

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

    # The conversational/theory intents ground their own answer and end
    # directly -- they don't go through the song-search ranking pipeline.
    graph.add_edge("theory", END)
    graph.add_edge("comparison", END)
    graph.add_edge("song_question", END)
    graph.add_edge("follow_up", END)
    graph.add_edge("recommend_similar", END)
    graph.add_edge("lyrics_request", END)
    graph.add_edge("song_creation", END)

    return graph.compile()


nagham_graph = build_nagham_graph()


def get_result_limit(state: AgentState) -> int:
    analysis = state.get("analysis", {})

    requested_limit = analysis.get("result_limit")

    if requested_limit is not None:
        return max(1, min(requested_limit, 10))

    return state.get("limit", 5)
