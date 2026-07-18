"""Composite impact score for weak-area topic ranking.

Ranks topics by how much benefit a student gets from practising them now,
combining:
  - weakness        (1 - mastery)
  - recency weight  (longer since last practice → higher need to revisit)
  - prereq children (topics that unlock if this one is mastered)
  - exam frequency  (syllabus weighting for this topic)

Note: SyllabusTopic currently carries no `weight` column and no
prereq-children relationship.  Callers that cannot supply these values
should use the safe defaults:
    exam_frequency=0.1  (mild weight — non-zero so all topics score > 0)
    prereq_children=0   (no downstream unlocks assumed)
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class TopicStats:
    mastery: float           # 0..1
    days_since_practice: int # 0 if practised today; larger = more forgotten
    prereq_children: int     # topics unlocked when this one is mastered
    exam_frequency: float    # 0..1 syllabus weight / exam frequency


def recency_weight(days: int) -> float:
    """More recently practised = closer to 1.0; long-forgotten = up to 3.0."""
    return min(1.0 + math.log1p(days) / 3.0, 3.0)


def prerequisite_multiplier(children: int) -> float:
    """More downstream topics unlocked = higher multiplier."""
    return 1.0 + math.log1p(children) * 0.4


def impact_score(t: TopicStats) -> float:
    """Return a composite priority score — higher means practise sooner."""
    weakness = 1.0 - t.mastery
    return (
        weakness
        * recency_weight(t.days_since_practice)
        * prerequisite_multiplier(t.prereq_children)
        * (t.exam_frequency + 0.05)
    )


__all__ = ["TopicStats", "recency_weight", "prerequisite_multiplier", "impact_score"]
