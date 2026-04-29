import asyncio
import sys
import os

# Make sure Python can find the app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm import llm


async def main():
    print("Test 1: basic text...")
    response = await llm.generate(
        prompt="What is integration by parts? Answer in 2 sentences.",
        system="You are an A-level mathematics tutor."
    )
    print("RESPONSE:", response)
    print()

    print("Test 2: JSON output...")
    result = await llm.generate_json(
        prompt="""Classify this student message and return JSON with keys:
        intent (explain/quiz/hint), topic, subtopic.

        Student message: 'I dont understand the chain rule'"""
    )
    print("JSON RESULT:", result)


asyncio.run(main())

