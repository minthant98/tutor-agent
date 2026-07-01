# app/schemas/onboarding.py
from datetime import date
from typing import Literal
from pydantic import BaseModel


WizardStep = Literal[
    "subjects", "exam-board", "exam-date", "target-grade", "preferences", "roadmap", "done"
]


class WizardStateOut(BaseModel):
    next_step: WizardStep
    progress_pct: int


class SubjectsIn(BaseModel):
    subjects: list[str]


class ExamBoardIn(BaseModel):
    exam_board: str


class ExamDateIn(BaseModel):
    exam_date: date | None = None


class TargetGradeIn(BaseModel):
    target_grade: str


class PreferencesIn(BaseModel):
    worked_examples: bool = False
    visual: bool = False
    step_by_step: bool = False
    practice: bool = False
