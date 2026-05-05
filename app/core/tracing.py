import os

def setup_tracing():
    """Must be called before any langchain/langgraph imports."""
    tracing = os.getenv("LANGSMITH_TRACING", "false")
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    project = os.getenv("LANGSMITH_PROJECT", "ascend-tutor")
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    os.environ["LANGSMITH_TRACING"] = tracing
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = project
    os.environ["LANGSMITH_ENDPOINT"] = endpoint

    if tracing == "true" and api_key:
        print(f"LangSmith tracing enabled → project: {project}")
    else:
        print("LangSmith tracing disabled")