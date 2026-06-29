"""Migration regression tests for ux_overhaul_v1.

Loads a representative snapshot of pre-migration data, runs the migration,
and verifies no data loss or schema regression.
"""
import os
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text


FIXTURE = Path(__file__).parent / "fixtures" / "pre_migration_v2.sql"


def _sync_to_async_url(sync_url: str) -> str:
    """Convert postgresql:// to postgresql+asyncpg:// for alembic env.py."""
    for prefix in ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://"):
        if sync_url.startswith(prefix):
            return "postgresql+asyncpg://" + sync_url[len(prefix):]
    return sync_url


def _ensure_psycopg_url(url: str) -> str:
    """Ensure the sync URL uses psycopg (v3) driver for SQLAlchemy create_engine."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _alembic_env(sync_url: str) -> dict:
    """Build subprocess env that overrides DATABASE_URL so alembic targets the test DB."""
    return {**os.environ, "DATABASE_URL": _sync_to_async_url(sync_url), "SYNC_DATABASE_URL": sync_url}


def _upgrade(sync_url: str) -> None:
    subprocess.check_call(["alembic", "upgrade", "head"], env=_alembic_env(sync_url))


@pytest.fixture
def legacy_db():
    """Provision an empty DB at the previous Alembic revision, load fixture data, yield URL."""
    url = os.environ["TEST_SYNC_DATABASE_URL"]
    env = _alembic_env(url)
    engine = create_engine(_ensure_psycopg_url(url))
    # Always ensure we start at the latest head before going down one step.
    # This guarantees idempotency across test runs even if a prior test failed mid-upgrade.
    subprocess.check_call(["alembic", "upgrade", "head"], env=env)
    # Now downgrade by exactly one revision (removes ux_overhaul_v1 tables/columns)
    subprocess.check_call(["alembic", "downgrade", "-1"], env=env)
    # Wipe any leftover test rows from a prior run (child tables first, then parent).
    _test_ids = "('11111111-1111-1111-1111-111111111111','22222222-2222-2222-2222-222222222222')"
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM mastery_state WHERE student_id IN {_test_ids}"))
        conn.execute(text(f"DELETE FROM sessions WHERE student_id IN {_test_ids}"))
        conn.execute(text(f"DELETE FROM study_plans WHERE student_id IN {_test_ids}"))
        conn.execute(text(f"DELETE FROM students WHERE id IN {_test_ids}"))
    with engine.begin() as conn:
        for stmt in FIXTURE.read_text().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    yield url
    # Restore DB to head so next fixture call starts clean
    subprocess.check_call(["alembic", "upgrade", "head"], env=env)


def test_migration_backfills_learner_subjects(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT subject, exam_board, exam_date FROM learner_subjects "
            "WHERE student_id = '11111111-1111-1111-1111-111111111111'"
        )).fetchall()
    assert len(rows) == 1
    assert rows[0].subject == "pure_mathematics"
    assert rows[0].exam_board == "edexcel"
    assert str(rows[0].exam_date) == "2026-11-15"


def test_migration_skips_mid_onboarding_users(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        count = conn.execute(text(
            "SELECT count(*) FROM learner_subjects "
            "WHERE student_id = '22222222-2222-2222-2222-222222222222'"
        )).scalar()
    assert count == 0  # Bob's empty subjects array → no backfill row


def test_migration_marks_existing_sessions_as_v1(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT session_version, session_type, current_segment_idx "
            "FROM sessions WHERE id = '33333333-3333-3333-3333-333333333333'"
        )).fetchone()
    assert row.session_version == 1
    assert row.session_type == "practice"
    assert row.current_segment_idx == 0


def test_migration_preserves_mastery_rows(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT topic, mastery_score FROM mastery_state "
            "WHERE student_id = '11111111-1111-1111-1111-111111111111' "
            "ORDER BY topic"
        )).fetchall()
    assert len(rows) == 2
    assert rows[0].topic == "differentiation_basics"
    assert rows[0].mastery_score == pytest.approx(0.82)
    assert rows[1].topic == "integration_basics"
    assert rows[1].mastery_score == pytest.approx(0.65)


def test_migration_seeds_syllabus_topics(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        edx = conn.execute(text(
            "SELECT count(*) FROM syllabus_topics "
            "WHERE exam_board='edexcel' AND version='2026.1'"
        )).scalar()
        cam = conn.execute(text(
            "SELECT count(*) FROM syllabus_topics "
            "WHERE exam_board='cambridge' AND version='2026.1'"
        )).scalar()
    assert edx == 22
    assert cam == 17


def test_migration_preferences_default_empty_dict(legacy_db):
    _upgrade(legacy_db)
    engine = create_engine(_ensure_psycopg_url(legacy_db))
    with engine.connect() as conn:
        prefs = conn.execute(text(
            "SELECT preferences FROM students "
            "WHERE id = '11111111-1111-1111-1111-111111111111'"
        )).scalar()
    assert prefs == {}
