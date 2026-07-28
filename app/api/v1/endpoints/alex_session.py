"""Alex session chat endpoint.

POST /api/v1/alex/session/{session_id}/message
  - Auth: Bearer token (standard Authorization header via fetch streaming)
  - Body: { "text": "<student message>" }
  - Response: text/event-stream
      data: {"delta": "..."}    — one per token
      data: {"done": true}      — final event
      data: {"error": "..."}    — on failure
"""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student, TutorSession
from app.services.alex.session_chat import stream_alex_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alex", tags=["alex"])


class AlexMessageRequest(BaseModel):
    text: str


@router.post("/session/{session_id}/message")
async def alex_session_message(
    session_id: uuid.UUID,
    body: AlexMessageRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Stream Alex's response for a student's question within a session."""
    # Ownership guard
    result = await db.execute(
        select(TutorSession).where(TutorSession.id == session_id)
    )
    db_session = result.scalar_one_or_none()

    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if db_session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not your session.")

    async def generate():
        try:
            async for token in stream_alex_reply(
                db=db,
                student_id=str(student.id),
                session_id=str(session_id),
                user_message=body.text,
            ):
                yield f"data: {json.dumps({'delta': token})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as exc:
            logger.error("Alex stream error: %s", exc, exc_info=True)
            yield f"data: {json.dumps({'error': 'Something went wrong — try again.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
