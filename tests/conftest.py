"""Shared pytest fixtures for the tutor_agent test suite.

Rules:
- Fixtures are additive — never rename or remove an existing fixture.
- All DB-backed fixtures use the async SQLAlchemy session against TEST_ASYNC_DATABASE_URL.
- Each test gets a fresh session; the session is rolled back after the test.
"""
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.models import Student

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------

_ASYNC_DB_URL = os.environ.get(
    "TEST_ASYNC_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://tutor:tutor@localhost:5434/stride_test",
    ),
)

# ---------------------------------------------------------------------------
# Session fixture — fresh engine per test to avoid "attached to a different
# loop" errors with asyncpg (each test gets its own asyncio event loop via
# asyncio_default_fixture_loop_scope=function in pytest.ini).
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session():
    """Fresh async SQLAlchemy session per test — rolled back at teardown."""
    engine = create_async_engine(
        _ASYNC_DB_URL,
        echo=False,
        connect_args={"statement_cache_size": 0},
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def student(db_session):
    """A minimal Student row for use in service tests."""
    s = Student(
        email="test_student@example.com",
        name="Test Student",
        hashed_password="hashed$dummy",
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        onboarding_complete=False,
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def syllabus_edexcel_seeded(db_session):
    """Ensure SyllabusTopic rows for Edexcel Pure Maths 2026.1 exist (22 topics).

    Uses INSERT ... ON CONFLICT DO NOTHING so this fixture is safe to run
    against a DB that already has the rows seeded by the Alembic migration.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from app.db.models import SyllabusTopic
    from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS, SYLLABUS_VERSION
    import uuid

    rows = [
        {
            "id": uuid.uuid4(),
            "exam_board": "edexcel",
            "subject": "pure_mathematics",
            "version": SYLLABUS_VERSION,
            **t,
        }
        for t in EDEXCEL_9MA0_TOPICS
    ]
    stmt = pg_insert(SyllabusTopic).values(rows).on_conflict_do_nothing(
        constraint="uq_syllabus_board_subject_version_topic"
    )
    await db_session.execute(stmt)
    await db_session.flush()


@pytest.fixture
def state_factory(student):
    from app.workflows.state import initial_state
    def _make(**overrides):
        s = initial_state(student_id=str(student.id), subject="pure_mathematics")
        s.update(overrides)
        return s
    return _make


@pytest.fixture
def redis_client():
    """Synchronous Redis client (matching get_redis() which is sync)."""
    from app.core.redis_client import get_redis
    return get_redis()
