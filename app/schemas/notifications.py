# app/schemas/notifications.py
from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    type: str
    payload: dict
    read_at: datetime | None
    created_at: datetime


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class MarkReadIn(BaseModel):
    ids: list[str]
