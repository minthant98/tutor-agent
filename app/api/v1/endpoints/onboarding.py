"""
app/api/v1/endpoints/onboarding.py
------------------------------------
Onboarding wizard endpoints.

State machine tracks step completion via `_step_*` markers in
`student.preferences` rather than inferring from LearnerSubject field
values (which have server-side defaults that would cause false positives).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.db.database import get_db
from app.db.models import Student, LearnerSubject
from app.services import learner_profile_service as lps
from app.schemas.onboarding import (
    WizardStateOut,
    SubjectsIn,
    ExamBoardIn,
    ExamDateIn,
    TargetGradeIn,
    PreferencesIn,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# Derive supported subjects from SUPPORTED_COMBOS
SUPPORTED_SUBJECTS = {combo[0] for combo in lps.SUPPORTED_COMBOS}

_STEPS = ["subjects", "exam-board", "exam-date", "target-grade", "preferences", "roadmap", "done"]


def _has_real_prefs(prefs: dict) -> bool:
    """Return True if at least one of the 4 real preference keys is present."""
    real_keys = {"worked_examples", "visual", "step_by_step", "practice"}
    return any(k in prefs for k in real_keys)


def _wizard_state(student: Student, drafts: list[LearnerSubject]) -> WizardStateOut:
    """
    Determine the current wizard step using _step_* preference markers.

    We do NOT infer completion from draft field values because LearnerSubject
    defaults (exam_board="edexcel", target_grade="A") would make those checks
    always true from the moment a draft row is created.

    Short-circuit: if `onboarded_at` is already set, the student is fully onboarded.
    """
    prefs = student.preferences or {}

    # Short-circuit: already fully onboarded
    if student.onboarded_at:
        return WizardStateOut(next_step="done", progress_pct=100)  # type: ignore[arg-type]

    if not any(d.subject for d in drafts):
        next_step = "subjects"
    elif not prefs.get("_step_board_done"):
        next_step = "exam-board"
    elif not prefs.get("_step_date_done"):
        next_step = "exam-date"
    elif not prefs.get("_step_grade_done"):
        next_step = "target-grade"
    elif not _has_real_prefs(prefs):
        next_step = "preferences"
    else:
        next_step = "roadmap"

    idx = _STEPS.index(next_step)
    progress_pct = int(idx / (len(_STEPS) - 1) * 100)
    return WizardStateOut(next_step=next_step, progress_pct=progress_pct)  # type: ignore[arg-type]


async def _get_state(db: AsyncSession, student: Student) -> WizardStateOut:
    """Load drafts and compute wizard state."""
    # get_or_create_draft returns ALL subjects (both draft and finalized).
    # We only look at draft rows for wizard progress.
    all_subjects = await lps.get_or_create_draft(db, student.id)
    drafts = [s for s in all_subjects if s.is_draft]
    return _wizard_state(student, drafts)


# ── GET /onboarding/state ─────────────────────────────────────────────────────

@router.get("/state", response_model=WizardStateOut)
async def get_wizard_state(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    return await _get_state(db, student)


# ── POST /onboarding/subjects ─────────────────────────────────────────────────

@router.post("/subjects", response_model=WizardStateOut)
async def post_subjects(
    body: SubjectsIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    # Validate all subjects before creating any drafts
    for subject in body.subjects:
        if subject not in SUPPORTED_SUBJECTS:
            raise HTTPException(400, f"Subject '{subject}' is not yet supported")

    for subject in body.subjects:
        await lps.upsert_subject_draft(db, student.id, subject)
    # Refresh student from DB to get latest preferences
    student = await db.get(Student, student.id)
    return await _get_state(db, student)


# ── POST /onboarding/exam-board ───────────────────────────────────────────────

@router.post("/exam-board", response_model=WizardStateOut)
async def post_exam_board(
    body: ExamBoardIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    all_subjects = await lps.get_or_create_draft(db, student.id)

    # Validate board compatibility for all draft subjects BEFORE mutating
    for s in all_subjects:
        if s.is_draft:
            if not lps.is_supported_combo(s.subject, body.exam_board, s.exam_level or "a_level"):
                raise HTTPException(400, f"Board '{body.exam_board}' is not supported for subject '{s.subject}'")

    # All validations passed; now update the board
    for s in all_subjects:
        if s.is_draft:
            s.exam_board = body.exam_board
    # Mark step complete via preference marker
    prefs = dict(student.preferences or {})
    prefs["_step_board_done"] = True
    student.preferences = prefs
    await db.flush()
    student = await db.get(Student, student.id)
    return await _get_state(db, student)


# ── POST /onboarding/exam-date ────────────────────────────────────────────────

@router.post("/exam-date", response_model=WizardStateOut)
async def post_exam_date(
    body: ExamDateIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    all_subjects = await lps.get_or_create_draft(db, student.id)
    for s in all_subjects:
        if s.is_draft:
            if body.exam_date is not None:
                s.exam_date = body.exam_date
    prefs = dict(student.preferences or {})
    prefs["_step_date_done"] = True
    student.preferences = prefs
    await db.flush()
    student = await db.get(Student, student.id)
    return await _get_state(db, student)


# ── POST /onboarding/target-grade ─────────────────────────────────────────────

@router.post("/target-grade", response_model=WizardStateOut)
async def post_target_grade(
    body: TargetGradeIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    all_subjects = await lps.get_or_create_draft(db, student.id)
    for s in all_subjects:
        if s.is_draft:
            s.target_grade = body.target_grade
    prefs = dict(student.preferences or {})
    prefs["_step_grade_done"] = True
    student.preferences = prefs
    await db.flush()
    student = await db.get(Student, student.id)
    return await _get_state(db, student)


# ── POST /onboarding/preferences ──────────────────────────────────────────────

@router.post("/preferences", response_model=WizardStateOut)
async def post_preferences(
    body: PreferencesIn,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    # Preserve _step_* markers before calling lps.update_preferences,
    # which only knows about the 4 real preference keys.
    old_prefs = dict(student.preferences or {})
    step_markers = {k: v for k, v in old_prefs.items() if k.startswith("_step_")}

    await lps.update_preferences(db, student.id, body.model_dump())

    # Refresh and re-merge the markers
    student = await db.get(Student, student.id)
    merged = dict(student.preferences or {})
    merged.update(step_markers)
    student.preferences = merged
    await db.flush()
    student = await db.get(Student, student.id)
    return await _get_state(db, student)


# ── POST /onboarding/complete ─────────────────────────────────────────────────

@router.post("/complete", response_model=WizardStateOut)
async def post_complete(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> WizardStateOut:
    await lps.finalize_drafts(db, student.id)
    student = await db.get(Student, student.id)
    return await _get_state(db, student)
