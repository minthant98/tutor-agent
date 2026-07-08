"""Free-tier rate limit for Exam Marker: 5 submissions per calendar month.
Pro tier unlimited."""
from fastapi import Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import GradedUpload, Student


async def check_marker_limit(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> Student:
    if student.subscription_tier == "pro":
        return student
    # Free tier — count submissions this calendar month
    res = await db.execute(
        select(func.count(GradedUpload.id)).where(
            GradedUpload.student_id == student.id,
            func.date_trunc('month', GradedUpload.created_at) ==
                func.date_trunc('month', func.now()),
        )
    )
    if (res.scalar() or 0) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Free monthly limit reached — upgrade to Pro for unlimited marking.",
        )
    return student
