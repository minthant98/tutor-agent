from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.sessions import router as sessions_router

app = FastAPI(
    title="AI Tutor Agent",
    version="0.1.0",
    docs_url="/docs",
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
    }


@app.get("/")
async def root():
    return {"message": "Tutor Agent API is running"}