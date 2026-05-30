import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Student

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)


class ProfileUpdateRequest(BaseModel):
    subjects: list[str] | None = None
    exam_board: str | None = None
    exam_level: str | None = None
    exam_date: str | None = None  # ISO format: "2026-06-15"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class StudentResponse(BaseModel):
    id: str
    email: str
    name: str
    exam_board: str
    exam_level: str
    subjects: list[str]
    subscription_tier: str
    subscription_status: str
    exam_date: str | None
    onboarding_complete: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_student(cls, student) -> "StudentResponse":
        return cls(
            id=str(student.id),
            email=student.email,
            name=student.name,
            exam_board=student.exam_board,
            exam_level=student.exam_level,
            subjects=student.subjects or [],
            subscription_tier=student.subscription_tier,
            subscription_status=student.subscription_status,
            exam_date=student.exam_date.isoformat() if student.exam_date else None,
            onboarding_complete=student.exam_date is not None,
        )


# ── Dependency: get current student from JWT ──────────────────────────────────

async def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Student:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    from app.core.auth import decode_access_token
    payload = decode_access_token(token)
    student_id = payload.get("sub")

    if not student_id:
        raise credentials_exception

    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise credentials_exception

    return student


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).where(Student.email == body.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    student = Student(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        exam_board="edexcel",
        exam_level="a_level",
        subjects=[],
        subscription_tier="free",
        subscription_status="active",
    )
    db.add(student)
    await db.flush()

    logger.info("New student registered: %s", body.email)
    return StudentResponse.from_student(student)


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Student).where(Student.email == form.username)
    )
    student = result.scalar_one_or_none()

    if not student or not verify_password(form.password, student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(student.id)})

    logger.info("Student logged in: %s", form.username)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=StudentResponse)
async def me(student: Student = Depends(get_current_student)):
    return StudentResponse.from_student(student)


# ── PATCH /auth/profile ───────────────────────────────────────────────────────

@router.patch("/profile", response_model=StudentResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Save onboarding data: subjects, exam board, exam date."""
    from datetime import date

    if body.subjects is not None:
        student.subjects = body.subjects
    if body.exam_board is not None:
        student.exam_board = body.exam_board
    if body.exam_level is not None:
        student.exam_level = body.exam_level
    if body.exam_date is not None:
        try:
            student.exam_date = date.fromisoformat(body.exam_date)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(400, detail="exam_date must be ISO format: YYYY-MM-DD")

    await db.flush()
    await db.commit()
    logger.info("Profile updated for student %s", student.id)
    return StudentResponse.from_student(student)