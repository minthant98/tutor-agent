from pydantic import BaseModel


class PracticeTopic(BaseModel):
    topic_id: str
    topic_name: str
    mastery_pct: int  # 0–100
    has_attempts: bool
