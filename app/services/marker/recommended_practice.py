"""Derive a recommended practice item from a graded submission's missed criteria.

MVP heuristic: find first not-awarded criterion → keyword-match its description to a
sub-skill → build a blurb and topic_id.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.models import GradedUpload

# ---------------------------------------------------------------------------
# Keyword → sub_skill mapping (order matters: first match wins)
# ---------------------------------------------------------------------------

_KEYWORD_TO_SKILL: list[tuple[str, str]] = [
    ("chain rule", "chain_rule"),
    ("product rule", "product_rule"),
    ("quotient rule", "quotient_rule"),
    ("substitut", "substitution"),          # substitution / substituting
    ("integrat", "integration"),            # integration / integrating
    ("differentiat", "differentiation"),    # differentiation / differentiating
    ("limit", "limits"),
]

# Human-readable labels for blurb construction
_SKILL_LABELS: dict[str, str] = {
    "chain_rule": "chain rule",
    "product_rule": "product rule",
    "quotient_rule": "quotient rule",
    "substitution": "substitution",
    "integration": "integration",
    "differentiation": "differentiation",
    "limits": "limits",
}

# Human-readable topic labels (for when sub_skill == topic_id fallback)
_TOPIC_LABELS: dict[str, str] = {
    "integration_basics": "Integration Basics",
    "pure_mathematics": "Pure Mathematics",
}


def _derive_sub_skill(description: str) -> str | None:
    """Return the first matching sub-skill slug for the given criterion description."""
    lowered = description.lower()
    for keyword, skill in _KEYWORD_TO_SKILL:
        if keyword in lowered:
            return skill
    return None


async def compute(db: "AsyncSession", submission: "GradedUpload") -> dict | None:
    """Derive {topic_id, sub_skill, blurb} from missed criteria.

    Returns None if all criteria were awarded (or if feedback_json is missing/empty).
    """
    feedback = submission.feedback_json
    if not feedback or not isinstance(feedback, dict):
        return None

    criteria = feedback.get("criteria", [])
    if not criteria:
        return None

    # Find first not-awarded criterion
    missed: dict | None = None
    for criterion in criteria:
        if not criterion.get("awarded", True):
            missed = criterion
            break

    if missed is None:
        return None  # all criteria awarded

    # Derive topic_id from the upload
    from app.services.marker.orchestrator import _infer_topic_from_upload
    topic_id = _infer_topic_from_upload(submission)

    # Derive sub_skill from the missed criterion description
    description = missed.get("description", "")
    sub_skill = _derive_sub_skill(description) or topic_id

    # Build blurb
    if sub_skill != topic_id:
        skill_label = _SKILL_LABELS.get(sub_skill, sub_skill.replace("_", " "))
        blurb = f"Practice {skill_label} with one targeted question."
    else:
        topic_label = _TOPIC_LABELS.get(topic_id, topic_id.replace("_", " ").title())
        blurb = f"Practice {topic_label} with one targeted question."

    return {
        "topic_id": topic_id,
        "sub_skill": sub_skill,
        "blurb": blurb,
    }
