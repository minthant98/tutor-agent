import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.admin import router as admin_router


from langsmith import Client



app = FastAPI(
    title="AI Tutor Agent",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "https://tutor-agent-production-d399.up.railway.app",
    "https://ascend-tutor-ai-agent.netlify.app",
    "https://minthant98.github.io",
    "https://tutor-agent-sigma.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(sessions_router, prefix=settings.api_v1_prefix)
app.include_router(admin_router, prefix=settings.api_v1_prefix)

@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/")
async def root():
    return {"message": "Tutor Agent API is running"}