import os
from pathlib import Path


def setup_tracing():
    """Must be called before any langchain/langgraph imports."""
    # Load .env manually since pydantic-settings hasn't run yet
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key.strip(), value)

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
        print(f"LangSmith tracing disabled (tracing={tracing}, key={'set' if api_key else 'missing'})")