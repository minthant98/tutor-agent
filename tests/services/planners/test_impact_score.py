"""Unit tests for impact_score — three regression cases from the task brief."""
from app.services.planners.impact_score import TopicStats, impact_score


def test_prereq_children_beats_raw_mastery():
    """Higher mastery is outweighed when a topic unlocks 5 downstream topics."""
    a = TopicStats(mastery=0.55, days_since_practice=5, prereq_children=5, exam_frequency=0.15)
    b = TopicStats(mastery=0.48, days_since_practice=5, prereq_children=1, exam_frequency=0.15)
    # a has higher mastery but unlocks 5 downstream topics → should rank higher
    assert impact_score(a) > impact_score(b)


def test_recency_amplifies():
    """A topic not practised for 30 days scores higher than one practised yesterday."""
    fresh = TopicStats(mastery=0.55, days_since_practice=1, prereq_children=1, exam_frequency=0.15)
    stale = TopicStats(mastery=0.55, days_since_practice=30, prereq_children=1, exam_frequency=0.15)
    assert impact_score(stale) > impact_score(fresh)


def test_exam_frequency_matters():
    """A topic that appears more in exams scores higher than an identical but rare topic."""
    common = TopicStats(mastery=0.55, days_since_practice=5, prereq_children=1, exam_frequency=0.30)
    rare   = TopicStats(mastery=0.55, days_since_practice=5, prereq_children=1, exam_frequency=0.01)
    assert impact_score(common) > impact_score(rare)
