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
            onboarding_complete=bool(student.onboarding_complete),
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

    # Onboarding completes the first time the user saves their profile
    student.onboarding_complete = True

    await db.flush()
    await db.commit()
    logger.info("Profile updated for student %s", student.id)
    return StudentResponse.from_student(student)

# ── Password reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a password reset token and email it. Always returns 202 even if
    the email doesn't exist — prevents enumeration attacks.
    """
    import hashlib
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.core.email import send_email, password_reset_email
    from app.db.models import PasswordResetToken

    result = await db.execute(select(Student).where(Student.email == body.email.lower()))
    student = result.scalar_one_or_none()

    if student:
        # 64-char URL-safe random token; hash before storing
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        token_row = PasswordResetToken(
            student_id=student.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(token_row)
        await db.commit()

        reset_link = f"{settings.frontend_url}/reset-password/{raw_token}"
        subject, html = password_reset_email(student.name, reset_link)
        send_email(student.email, subject, html)
        logger.info("Password reset email sent to %s", student.email)
    else:
        logger.info("Forgot password requested for unknown email: %s", body.email)

    return {"message": "If an account exists with this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a reset token and set a new password."""
    import hashlib
    from datetime import datetime, timezone
    from app.db.models import PasswordResetToken

    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()

    if not token_row:
        raise HTTPException(400, detail="Invalid or expired reset link.")
    if token_row.used_at is not None:
        raise HTTPException(400, detail="This reset link has already been used.")
    if token_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, detail="This reset link has expired. Request a new one.")

    student_result = await db.execute(
        select(Student).where(Student.id == token_row.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(400, detail="Account not found.")

    student.hashed_password = hash_password(body.new_password)
    token_row.used_at = datetime.now(timezone.utc)

    await db.commit()
    logger.info("Password reset completed for student %s", student.id)

    return {"message": "Password updated. You can now sign in with your new password."}
