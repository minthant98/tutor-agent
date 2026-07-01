# tests/test_learner_profile_service.py
import pytest
from app.services import learner_profile_service as svc

@pytest.mark.asyncio
async def test_upsert_creates_draft(db_session, student):
    s = await svc.upsert_subject_draft(db_session, student.id,
                                       subject="pure_mathematics",
                                       exam_board="edexcel",
                                       target_grade="A*")
    assert s.is_draft is True
    assert s.target_grade == "A*"

@pytest.mark.asyncio
async def test_upsert_idempotent(db_session, student):
    await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", exam_board="edexcel")
    s2 = await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", target_grade="B")
    assert s2.target_grade == "B"
    rows = await svc.list_subjects(db_session, student.id, include_drafts=True)
    assert len(rows) == 1

@pytest.mark.asyncio
async def test_finalize_flips_draft_and_sets_onboarded(db_session, student):
    await svc.upsert_subject_draft(db_session, student.id, subject="pure_mathematics", exam_board="edexcel", target_grade="A*")
    count = await svc.finalize_drafts(db_session, student.id)
    assert count == 1
    rows = await svc.list_subjects(db_session, student.id)
    assert all(not r.is_draft for r in rows)
    await db_session.refresh(student)
    assert student.onboarded_at is not None
    assert student.onboarding_complete is True

def test_is_supported_combo():
    assert svc.is_supported_combo("pure_mathematics", "edexcel", "a_level")
    assert svc.is_supported_combo("pure_mathematics", "cambridge", "a_level")
    assert not svc.is_supported_combo("physics", "edexcel", "a_level")
    assert not svc.is_supported_combo("pure_mathematics", "aqa", "a_level")
