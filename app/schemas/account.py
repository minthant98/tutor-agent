# app/schemas/account.py
from datetime import date
from pydantic import BaseModel


class ProfileOut(BaseModel):
    name: str
    email: str


class SubjectOut(BaseModel):
    id: str
    subject: str
    exam_board: str
    exam_level: str
    exam_date: date | None
    target_grade: str
    current_grade: str | None
    readiness_pct: float


class PreferencesOut(BaseModel):
    worked_examples: bool = False
    visual: bool = False
    step_by_step: bool = False
    practice: bool = False


class BillingOut(BaseModel):
    tier: str
    status: str


class AccountOut(BaseModel):
    profile: ProfileOut
    subjects: list[SubjectOut]
    preferences: PreferencesOut
    billing: BillingOut


class SubjectPatch(BaseModel):
    exam_date: date | None = None
    target_grade: str | None = None
    current_grade: str | None = None
    exam_board: str | None = None


class ProfilePatch(BaseModel):
    name: str | None = None
