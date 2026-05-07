import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import MasteryState, TutorSession
from app.workflows.graph import tutor_graph
from app.workflows.state import SessionState

logger = logging.getLogger(__name__)


async def process_message(
    db: AsyncSession,
    db_session: TutorSession,
    state: SessionState,
    student_message: str,
) -> tuple[str, SessionState]:

    state["current_input"] = student_message
    state["current_input_type"] = "text"
    state["conversation_history"].append({
        "role": "student",
        "content": student_message,
        "metadata": {"turn": state.get("turn_count", 0)},
    })

    # ── SHORT CIRCUIT: if active quiz, evaluate directly ──────────
    if state.get("quiz_question"):
        from app.agents.nodes import evaluator_agent, rules_engine, adapt_agent, intent_agent

        intent_result = await intent_agent(state)
        detected_intent = intent_result.get("intent", "unknown")

        if detected_intent not in ("explain", "quiz", "off_topic", "greeting"):
            state["student_answer"] = student_message
            state.update(intent_result)

            eval_result = await evaluator_agent(state)
            state.update(eval_result)
            logger.info("After eval — score: %s, consecutive_wrong: %s, consecutive_correct: %s",
                state.get('evaluation_result', {}).get('score_pct'),
                state.get('consecutive_wrong'),
                state.get('consecutive_correct')
)

            rules_result = rules_engine(state)
            state.update(rules_result)

            adapt_result = await adapt_agent(state)
            state.update(adapt_result)

            response = state.get("final_response") or "Could you rephrase that?"

            state["conversation_history"].append({
                "role": "tutor",
                "content": response,
                "metadata": {
                    "intent": "check_answer",
                    "topic": state.get("topic"),
                    "rules_action": state.get("rules_action"),
                },
            })

            state["quiz_question"] = None
            state["student_answer"] = None
            state["turn_count"] = state.get("turn_count", 0) + 1

            db_session.messages = state.get("conversation_history", [])
            db_session.topic = state.get("topic")
            await db.flush()

            if state.get("evaluation_result"):
                await _update_mastery(db, state)

            return response, state

        # Student wants something else — clear quiz and fall through
        state["quiz_question"] = None

    # ── NORMAL FLOW: run the full graph ───────────────────────────
    import copy
    state_copy = copy.deepcopy(state)

    try:
        result: SessionState = await tutor_graph.ainvoke(state_copy)
    except Exception as e:
        logger.error("Graph error: %s", e, exc_info=True)
        return "Sorry, I ran into an error. Please try again.", state

    response = result.get("final_response") or "Could you rephrase that?"

    result["conversation_history"].append({
        "role": "tutor",
        "content": response,
        "metadata": {
            "intent": result.get("intent"),
            "topic": result.get("topic"),
            "rules_action": result.get("rules_action"),
        },
    })

    keys_to_preserve = [
        "weak_topics", "mastery_scores", "hints_given",
        "consecutive_wrong", "consecutive_correct",
        "mode", "exam_board", "exam_level", "subscription_tier",
    ]
    for key in keys_to_preserve:
        if not result.get(key) and state.get(key):
            result[key] = state[key]

    if result.get("quiz_question"):
        pass
    elif state.get("quiz_question"):
        result["quiz_question"] = state["quiz_question"]

    db_session.messages = result.get("conversation_history", [])
    db_session.topic = result.get("topic")
    await db.flush()

    if result.get("evaluation_result"):
        await _update_mastery(db, result)

    return response, result


async def _update_mastery(db: AsyncSession, state: SessionState) -> None:
    eval_result = state.get("evaluation_result")
    topic = state.get("topic")
    if not eval_result or not topic:
        return

    score = float(eval_result.get("score_pct") or 0.0)
    student_id = state["student_id"]

    stmt = select(MasteryState).where(
        MasteryState.student_id == student_id,
        MasteryState.subject == state["subject"],
        MasteryState.topic == topic,
    )
    result = await db.execute(stmt)
    mastery = result.scalar_one_or_none()

    if mastery is None:
        mastery = MasteryState(
            student_id=student_id,
            subject=state["subject"],
            topic=topic,
            mastery_score=0.0,
            total_attempts=0,
            correct_streak=0,
            is_weak=False,
        )
        db.add(mastery)

    current_score = float(mastery.mastery_score or 0.0)
    current_attempts = int(mastery.total_attempts or 0)
    current_streak = int(mastery.correct_streak or 0)

    alpha = 0.3
    mastery.mastery_score = alpha * score + (1 - alpha) * current_score
    mastery.total_attempts = current_attempts + 1
    mastery.last_reviewed_at = datetime.now(timezone.utc)
    mastery.correct_streak = current_streak + 1 if score >= 0.6 else 0
    mastery.is_weak = mastery.mastery_score < 0.5

    await db.flush()
    logger.info("Mastery updated: topic=%s score=%.2f", topic, mastery.mastery_score)