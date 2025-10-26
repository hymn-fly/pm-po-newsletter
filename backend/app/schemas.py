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
    advanced_opt_in: bool
    advanced_opted_in_at: datetime | None = None
    intro_completed_at: datetime | None = None

    class Config:
        orm_mode = True


class AdvancedOptInRequest(BaseModel):
    email: EmailStr


class SubscriptionResponse(BaseModel):
    success: bool
    data: Subscription | None = None
    message: str | None = None
