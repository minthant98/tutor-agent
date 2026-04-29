import asyncio
from app.workflows.state import initial_state
from app.agents.nodes import (
    intent_agent,
    retrieval_agent,
    tutor_agent,
    quiz_agent,
    evaluator_agent,
    hint_agent,
    rules_engine,
    adapt_agent,
)


def print_result(test_name: str, result: dict):
    print(f"{'='*50}")
    print(f"TEST: {test_name}")
    print(f"{'='*50}")
    for key, value in result.items():
        if value is not None and value != [] and value != {}:
            if isinstance(value, str) and len(value) > 150:
                print(f"  {key}: {value[:150]}...")
            else:
                print(f"  {key}: {value}")
    print()


def make_state(**kwargs):
    state = initial_state(
        student_id="test-student-123",
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
        subscription_tier="pro",
    )
    state.update(kwargs)
    return state


async def test_intent_agent():
    print("\n" + "="*50)
    print("AGENT 1: INTENT AGENT")
    print("="*50)

    cases = [
        "Can you explain differentiation from first principles?",
        "Give me a practice question on integration",
        "I'm stuck, can I have a hint?",
        "Is my answer correct? I got dy/dx = 2x + 3",
        "Who won the World Cup?",
        "Hello, I need help with maths",
    ]

    for message in cases:
        state = make_state(current_input=message)
        result = await intent_agent(state)
        print(f"  Input:  '{message}'")
        print(f"  Intent: {result['intent']} | Topic: {result['topic']}")
        print()


async def test_retrieval_agent():
    print("\n" + "="*50)
    print("AGENT 2: RETRIEVAL AGENT")
    print("="*50)

    # With a valid query
    state = make_state(
        intent="explain",
        retrieval_query="differentiation from first principles",
    )
    result = await retrieval_agent(state)
    print(f"  Query: 'differentiation from first principles'")
    print(f"  Chunks retrieved: {len(result['retrieved_chunks'])}")
    if result['retrieved_chunks']:
        top = result['retrieved_chunks'][0]
        print(f"  Top chunk score: {top['score']}")
        print(f"  Top chunk preview: {top['text'][:100]}...")
    print()

    # Off-topic — should return empty
    state = make_state(intent="off_topic", retrieval_query=None)
    result = await retrieval_agent(state)
    print(f"  Off-topic query → chunks: {len(result['retrieved_chunks'])} (should be 0)")
    print()


async def test_tutor_agent():
    print("\n" + "="*50)
    print("AGENT 3: TUTOR AGENT")
    print("="*50)

    from app.rag.retriever import retrieve
    chunks = await retrieve(
        query="differentiation from first principles",
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    state = make_state(
        current_input="Explain differentiation from first principles",
        intent="explain",
        topic="differentiation",
        retrieved_chunks=chunks,
    )
    result = await tutor_agent(state)
    print(f"  Response length: {len(result['final_response'])} chars")
    print(f"  Preview: {result['final_response'][:200]}...")
    print()


async def test_quiz_agent():
    print("\n" + "="*50)
    print("AGENT 4: QUIZ AGENT")
    print("="*50)

    from app.rag.retriever import retrieve
    chunks = await retrieve(
        query="integration by parts",
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    state = make_state(
        intent="quiz",
        topic="integration",
        retrieved_chunks=chunks,
    )
    result = await quiz_agent(state)
    q = result["quiz_question"]
    print(f"  Question: {q.get('question', '')[:150]}...")
    print(f"  Marks: {q.get('marks_available')}")
    print(f"  Difficulty: {q.get('difficulty')}")
    print(f"  Has mark scheme: {bool(q.get('mark_scheme'))}")
    print()
    return result["quiz_question"]


async def test_evaluator_agent(quiz_question: dict):
    print("\n" + "="*50)
    print("AGENT 5: EVALUATOR AGENT")
    print("="*50)

    # Test with a good answer
    state = make_state(
        quiz_question=quiz_question,
        current_input="I used integration by parts with u=x and dv=e^x dx, giving xe^x - e^x + C",
    )
    result = await evaluator_agent(state)
    eval_r = result["evaluation_result"]
    print(f"  Answer: 'I used integration by parts...'")
    print(f"  Score: {eval_r.get('score_pct')} | Marks: {eval_r.get('marks_awarded')}")
    print(f"  Feedback: {eval_r.get('feedback', '')[:100]}...")
    print(f"  Consecutive wrong: {result['consecutive_wrong']}")
    print(f"  Consecutive correct: {result['consecutive_correct']}")
    print()

    # Test with a wrong answer
    state2 = make_state(
        quiz_question=quiz_question,
        current_input="The answer is just e^x + C",
    )
    result2 = await evaluator_agent(state2)
    eval_r2 = result2["evaluation_result"]
    print(f"  Answer: 'The answer is just e^x + C'")
    print(f"  Score: {eval_r2.get('score_pct')} | Marks: {eval_r2.get('marks_awarded')}")
    print(f"  Consecutive wrong: {result2['consecutive_wrong']}")
    print()


async def test_hint_agent(quiz_question: dict):
    print("\n" + "="*50)
    print("AGENT 6: HINT AGENT")
    print("="*50)

    from app.rag.retriever import retrieve
    chunks = await retrieve(
        query="integration by parts",
        subject="pure_mathematics",
        exam_board="edexcel",
        exam_level="a_level",
    )

    # First hint
    state = make_state(
        quiz_question=quiz_question,
        hints_given=0,
        retrieved_chunks=chunks,
    )
    result = await hint_agent(state)
    print(f"  Hint 1: {result['final_response'][:150]}...")
    print(f"  Hints given after: {result['hints_given']}")
    print()

    # At limit — should trigger worked example
    state2 = make_state(
        quiz_question=quiz_question,
        hints_given=4,
        retrieved_chunks=chunks,
    )
    result2 = await hint_agent(state2)
    print(f"  At hint limit (4) → rules_action: {result2.get('rules_action')}")
    print()


async def test_rules_engine():
    print("\n" + "="*50)
    print("AGENT 7: RULES ENGINE")
    print("="*50)

    cases = [
        ("Clean state",           dict(intent="explain", consecutive_wrong=0, hints_given=0, evaluation_result=None, subscription_tier="pro", mode="explain")),
        ("3 wrong answers",       dict(intent="check_answer", consecutive_wrong=3, hints_given=0, evaluation_result=None)),
        ("Score below 40%",       dict(intent="check_answer", consecutive_wrong=1, hints_given=0, evaluation_result={"score_pct": 0.3})),
        ("5 hints used",          dict(intent="hint", consecutive_wrong=0, hints_given=5, evaluation_result=None)),
        ("Off-topic",             dict(intent="off_topic", consecutive_wrong=0, hints_given=0, evaluation_result=None)),
        ("Free tier quiz",        dict(intent="quiz", consecutive_wrong=0, hints_given=0, evaluation_result=None, subscription_tier="free", mode="quiz")),
    ]

    for name, kwargs in cases:
        state = make_state(**kwargs)
        result = rules_engine(state)
        print(f"  {name:30} → {result['rules_action']}")
    print()


async def test_adapt_agent():
    print("\n" + "="*50)
    print("AGENT 8: ADAPT AGENT")
    print("="*50)

    cases = [
        ("redirect_off_topic",    dict(rules_action="redirect_off_topic")),
        ("re_explain",            dict(rules_action="re_explain", explanation="The chain rule states...")),
        ("show_worked_example",   dict(rules_action="show_worked_example", quiz_question={"mark_scheme": "Step 1: ..."})),
        ("continue — weak topic", dict(rules_action="continue", evaluation_result={"score_pct": 0.3}, topic="integration", weak_topics=[])),
    ]

    for name, kwargs in cases:
        state = make_state(**kwargs)
        result = await adapt_agent(state)
        response = result.get("final_response", "")
        weak = result.get("weak_topics", [])
        print(f"  {name:30} → response: {str(response)[:80]}...")
        if weak:
            print(f"  {'':30}   weak_topics: {weak}")
    print()


async def main():
    print("\n🧪 TESTING ALL TUTOR AGENT NODES")
    print("This tests each agent in isolation with real ChromaDB content\n")

    await test_intent_agent()
    await test_retrieval_agent()
    await test_tutor_agent()
    quiz_question = await test_quiz_agent()
    await test_evaluator_agent(quiz_question)
    await test_hint_agent(quiz_question)
    await test_rules_engine()
    await test_adapt_agent()

    print("="*50)
    print("ALL AGENTS TESTED")
    print("="*50)


asyncio.run(main())