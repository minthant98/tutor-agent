# tests/test_readiness_service.py
import pytest
from datetime import date, timedelta
from app.services import readiness_service as svc
from app.core.grade_prediction import predict_grade
from app.db.models import MasteryState, SyllabusTopic, ReadinessSnapshot

@pytest.mark.asyncio
async def test_compute_readiness_zero_when_no_mastery(db_session, student, syllabus_edexcel_seeded):
    pct = await svc.compute_readiness_pct(db_session, student.id, "pure_mathematics", "2026.1")
    assert pct == 0.0

@pytest.mark.asyncio
async def test_compute_readiness_counts_only_competent_topics(db_session, student, syllabus_edexcel_seeded):
    db_session.add_all([
        MasteryState(student_id=student.id, subject="pure_mathematics", topic="integration_basics", mastery_score=0.8),
        MasteryState(student_id=student.id, subject="pure_mathematics", topic="differentiation_basics", mastery_score=0.6),  # below 0.7
    ])
    await db_session.flush()
    pct = await svc.compute_readiness_pct(db_session, student.id, "pure_mathematics", "2026.1")
    # 1 competent topic of 22 = 4.5%
    assert pct == pytest.approx(100.0 / 22, abs=0.5)

@pytest.mark.asyncio
async def test_snapshot_idempotent_per_day(db_session, student):
    snap1 = await svc.write_snapshot_if_first_today(db_session, student.id, "pure_mathematics")
    snap2 = await svc.write_snapshot_if_first_today(db_session, student.id, "pure_mathematics")
    assert snap1 is not None
    assert snap2 is None  # already written today

def test_grade_prediction_buckets():
    assert predict_grade(95) == "A*"
    assert predict_grade(80) == "A"
    assert predict_grade(70) == "B"
    assert predict_grade(50) == "C"
    assert predict_grade(35) == "D"
    assert predict_grade(20) == "E"
    assert predict_grade(0) == "E"
