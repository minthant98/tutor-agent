import pytest
import time
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_next_question_returns_candidate(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    fake_candidate = {
        "question_id": "q1", "question_text": "Integrate x^2",
        "mark_scheme": "MS", "max_marks": 3,
        "paper_ref": "Edexcel P1 2024", "topic": "integration_basics",
        "used_generated_mark_scheme": False,
    }
    with patch("app.api.v1.endpoints.marker.pick_question",
              new=AsyncMock(return_value=fake_candidate)):
        r = await authed_client.get("/api/v1/marker/next-question")
    assert r.status_code == 200
    body = r.json()
    assert body["question_text"] == "Integrate x^2"
    assert body["max_marks"] == 3


@pytest.mark.asyncio
async def test_post_submissions_typed_returns_submission_id(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "q1", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x^2",
    })
    assert r.status_code == 201
    assert "submission_id" in r.json()
    assert r.json().get("upload_url") is None  # typed doesn't need upload


@pytest.mark.asyncio
async def test_post_submissions_photo_returns_upload_url(
    authed_client, student_with_subject, syllabus_edexcel_seeded
):
    with patch("app.api.v1.endpoints.marker.generate_signed_upload_url",
              new=AsyncMock(return_value="https://supabase/upload?token=x")):
        r = await authed_client.post("/api/v1/marker/submissions", json={
            "question_id": "q1", "question_text": "Q", "mark_scheme": "MS",
            "max_marks": 6, "input_type": "photo", "photo_extension": "jpg",
        })
    assert r.status_code == 201
    body = r.json()
    assert body["upload_url"].startswith("https://supabase")
    assert body["upload_path"].endswith(".jpg")


@pytest.mark.asyncio
async def test_post_submissions_free_tier_rate_limit(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    # Seed 5 existing this month
    for i in range(5):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "qN", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x",
    })
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_post_submissions_pro_tier_unlimited(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload, Student
    from sqlalchemy import update
    await db_session.execute(
        update(Student).where(Student.id == student_with_subject.id)
        .values(subscription_tier="pro")
    )
    for i in range(5):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.post("/api/v1/marker/submissions", json={
        "question_id": "qN", "question_text": "Q", "mark_scheme": "MS",
        "max_marks": 6, "input_type": "typed", "answer_text": "x",
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_get_submission_returns_status(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    upload = GradedUpload(
        student_id=student_with_subject.id, subject="pure_mathematics",
        exam_board="edexcel", question_id="q1",
        question_text="Q", mark_scheme="MS", max_marks=6,
        input_type="typed", answer_text="x", status="pending",
    )
    db_session.add(upload); await db_session.flush()

    r = await authed_client.get(f"/api/v1/marker/submissions/{upload.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_get_submission_isolates_other_students(
    authed_client, student_with_subject, db_session
):
    """Requesting another student's submission returns 404."""
    from app.db.models import GradedUpload, Student
    from uuid import uuid4
    other = Student(email="other@e.com", name="Other", hashed_password="x",
                    exam_board="edexcel", exam_level="a_level",
                    subjects=[], subscription_tier="free")
    db_session.add(other); await db_session.flush()

    upload = GradedUpload(
        student_id=other.id, subject="pure_mathematics", exam_board="edexcel",
        question_id="q1", question_text="Q", mark_scheme="MS", max_marks=6,
        input_type="typed", answer_text="x", status="graded",
    )
    db_session.add(upload); await db_session.flush()

    r = await authed_client.get(f"/api/v1/marker/submissions/{upload.id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_submissions_pagination(
    authed_client, student_with_subject, db_session
):
    from app.db.models import GradedUpload
    for i in range(12):
        db_session.add(GradedUpload(
            student_id=student_with_subject.id, subject="pure_mathematics",
            exam_board="edexcel", question_id=f"q{i}",
            question_text="Q", mark_scheme="MS", max_marks=6,
            input_type="typed", answer_text="A", status="graded",
        ))
    await db_session.flush()

    r = await authed_client.get("/api/v1/marker/submissions?limit=10&offset=0")
    assert len(r.json()) == 10

    r2 = await authed_client.get("/api/v1/marker/submissions?limit=10&offset=10")
    assert len(r2.json()) == 2
