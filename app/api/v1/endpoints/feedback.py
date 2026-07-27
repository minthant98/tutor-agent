"""
POST /api/v1/feedback

Auth-required endpoint.  Accepts subject + body and:
  1. Logs the feedback with structured fields.
  2. Optionally forwards to Resend if RESEND_API_KEY is set in the environment.

Resend integration is best-effort — a failure there does not propagate a 5xx
back to the student; the feedback is still logged regardless.
"""
import logging
import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.endpoints.auth import get_current_student
from app.db.models import Student

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])

_FEEDBACK_TO_EMAIL = os.environ.get("FEEDBACK_TO_EMAIL", "hello@stride.study")
_FEEDBACK_FROM_EMAIL = os.environ.get(
    "FEEDBACK_FROM_EMAIL", "noreply@stride.study"
)


class FeedbackIn(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


@router.post("", status_code=200)
async def submit_feedback(
    payload: FeedbackIn,
    student: Student = Depends(get_current_student),
) -> dict:
    logger.info(
        "feedback received",
        extra={
            "student_id": str(student.id),
            "student_email": student.email,
            "subject": payload.subject,
            "body_len": len(payload.body),
        },
    )
    logger.info("feedback: %s / %s", payload.subject, payload.body)

    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        try:
            import resend  # type: ignore[import]

            resend.api_key = resend_key
            resend.Emails.send(
                {
                    "from": _FEEDBACK_FROM_EMAIL,
                    "to": [_FEEDBACK_TO_EMAIL],
                    "reply_to": student.email,
                    "subject": f"[Stride Feedback] {payload.subject}",
                    "text": (
                        f"From: {student.name} <{student.email}>\n\n"
                        f"{payload.body}"
                    ),
                }
            )
            logger.info("feedback forwarded via Resend to %s", _FEEDBACK_TO_EMAIL)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Resend forward failed (feedback still logged): %s", exc
            )

    return {"status": "received"}
