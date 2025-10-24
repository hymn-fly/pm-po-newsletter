from datetime import datetime

from pydantic import BaseModel, EmailStr


class SubscriptionCreate(BaseModel):
    email: EmailStr


class Subscription(BaseModel):
    id: int
    email: EmailStr
    progress_day: int
    last_sent_at: datetime | None
    subscribed_at: datetime

    class Config:
        orm_mode = True


class SubscriptionResponse(BaseModel):
    success: bool
    data: Subscription | None = None
    message: str | None = None
