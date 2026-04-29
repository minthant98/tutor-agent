import logging
from langgraph.graph import END, START, StateGraph
from app.agents.nodes import (
    adapt_agent,
    evaluator_agent,
    hint_agent,
    intent_agent,
    quiz_agent,
    retrieval_agent,
    rules_engine,
    tutor_agent,
)
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)


def route_by_intent(state: SessionState) -> str:
    intent = state.get("intent", "unknown")
    has_quiz = bool(state.get("quiz_question"))

    logger.info("Routing — intent: %s | has_quiz: %s", intent, has_quiz)

    # If there's an active quiz question, any non-quiz/non-off-topic
    # response is treated as an answer attempt
    if has_quiz and intent not in ("quiz", "off_topic", "greeting"):
        logger.info("Active quiz detected — routing to evaluator")
        return "evaluator_agent"

    routes = {
        "explain":      "tutor_agent",
        "quiz":         "quiz_agent",
        "hint":         "hint_agent",
        "check_answer": "evaluator_agent",
        "off_topic":    "rules_engine",
        "greeting":     "rules_engine",
        "unknown":      "tutor_agent",
    }
    destination = routes.get(intent, "tutor_agent")
    logger.info("Routing intent '%s' → %s", intent, destination)
    return destination

def build_graph():
    graph = StateGraph(SessionState)

    # Add all nodes
    graph.add_node("intent_agent",     intent_agent)
    graph.add_node("retrieval_agent",  retrieval_agent)
    graph.add_node("tutor_agent",      tutor_agent)
    graph.add_node("quiz_agent",       quiz_agent)
    graph.add_node("hint_agent",       hint_agent)
    graph.add_node("evaluator_agent",  evaluator_agent)
    graph.add_node("rules_engine",     rules_engine)
    graph.add_node("adapt_agent",      adapt_agent)

    # Entry point
    graph.add_edge(START, "intent_agent")

    # Intent → retrieval (always)
    graph.add_edge("intent_agent", "retrieval_agent")

    # Retrieval → route by intent
    graph.add_conditional_edges(
        "retrieval_agent",
        route_by_intent,
        {
            "tutor_agent":     "tutor_agent",
            "quiz_agent":      "quiz_agent",
            "hint_agent":      "hint_agent",
            "evaluator_agent": "evaluator_agent",
            "rules_engine":    "rules_engine",
        },
    )

    # All content agents → rules engine
    graph.add_edge("tutor_agent",     "rules_engine")
    graph.add_edge("quiz_agent",      "rules_engine")
    graph.add_edge("hint_agent",      "rules_engine")
    graph.add_edge("evaluator_agent", "rules_engine")

    # Rules engine → adapt
    graph.add_edge("rules_engine", "adapt_agent")

    # Adapt → end
    graph.add_edge("adapt_agent", END)

    return graph


tutor_graph = build_graph().compile()