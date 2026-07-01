# app/core/grade_prediction.py
def predict_grade(readiness_pct: float) -> str:
    """Heuristic readiness % → grade bucket. NOT a real model."""
    if readiness_pct >= 90: return "A*"
    if readiness_pct >= 75: return "A"
    if readiness_pct >= 60: return "B"
    if readiness_pct >= 45: return "C"
    if readiness_pct >= 30: return "D"
    return "E"
