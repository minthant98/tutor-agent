import asyncio
from app.workflows.state import initial_state
from app.agents.nodes import intent_agent, rules_engine


async def main():
    state = initial_state(
        student_id="test-student",
        subject="mathematics",
        exam_board="cambridge",
        exam_level="a_level",
        subscription_tier="pro",
    )

    # Test 1: intent agent
    print("Test 1: Intent classification...")
    state["current_input"] = "I don't understand integration by parts"
    result = await intent_agent(state)
    print("Intent:", result["intent"])
    print("Topic:", result["topic"])
    print("Retrieval query:", result["retrieval_query"])
    print()

    # Test 2: rules engine with clean state
    print("Test 2: Rules engine — clean state...")
    state["consecutive_wrong"] = 0
    state["hints_given"] = 0
    state["evaluation_result"] = None
    state["intent"] = "explain"
    result = rules_engine(state)
    print("Action:", result["rules_action"])
    print()

    # Test 3: rules engine with 3 wrong answers
    print("Test 3: Rules engine — 3 consecutive wrong...")
    state["consecutive_wrong"] = 3
    result = rules_engine(state)
    print("Action:", result["rules_action"])
    print()


asyncio.run(main())