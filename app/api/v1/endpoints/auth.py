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
    exam_board: str = "edexcel"
    exam_level: str = "a_level"
    subjects: list[str] = ["pure_mathematics"]


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
        exam_board=body.exam_board,
        exam_level=body.exam_level,
        subjects=body.subjects,
        subscription_tier="free",
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