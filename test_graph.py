import asyncio
from app.workflows.state import initial_state
from app.workflows.graph import tutor_graph


async def main():
    state = initial_state(
        student_id="test-student",
        subject="mathematics",
        exam_board="cambridge",
        exam_level="a_level",
        subscription_tier="pro",
    )

    print("=" * 60)
    print("Turn 1: Student asks for an explanation")
    print("=" * 60)

    state["current_input"] = "Can you explain integration by parts?"

    result = await tutor_graph.ainvoke(state)

    print("Intent:   ", result["intent"])
    print("Topic:    ", result["topic"])
    print("Chunks:   ", len(result["retrieved_chunks"]))
    print("Action:   ", result["rules_action"])
    print()
    print("RESPONSE:")
    print(result["final_response"])
    print()

    print("=" * 60)
    print("Turn 2: Off-topic message")
    print("=" * 60)

    state["current_input"] = "Who won the Premier League last night?"

    result = await tutor_graph.ainvoke(state)

    print("Intent:   ", result["intent"])
    print("Action:   ", result["rules_action"])
    print()
    print("RESPONSE:")
    print(result["final_response"])


asyncio.run(main())