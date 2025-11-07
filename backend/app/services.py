from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from supabase import Client

from app.email_service import MailieClient
from app.schemas import (
    AdvancedOptInRequest,
    Subscription,
    SubscriptionCreate,
)

SUBSCRIPTIONS_TABLE = "subscriptions"
INTRO_COURSE_DAYS = 5


class SubscriptionService:
    def __init__(self, supabase: Client) -> None:
        self.supabase = supabase

    def create_subscription(self, payload: SubscriptionCreate) -> Subscription:
        
        existing = (
            self.supabase.table(SUBSCRIPTIONS_TABLE)
            .select("id,email,progress_day,last_sent_at,subscribed_at")
            .eq("email", payload.email)
            .maybe_single()
            .execute()
        )

        if existing and existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 해당 이메일로 구독 중입니다.",
            )

        insert_response = (
            self.supabase.table(SUBSCRIPTIONS_TABLE)
            .insert(
                {
                    "email": payload.email,
                    "progress_day": 1,
                    "last_sent_at": None,
                    "subscribed_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                }
            )
            .execute()
        )

        if not insert_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="구독 정보를 저장하지 못했습니다.",
            )

        record = insert_response.data[0]
        
        # Mailie API에 신규 구독 등록
        try:
            with MailieClient() as mailie_client:
                mailie_client.create_subscription(email=payload.email)
        except Exception as e:
            # Mailie API 호출 실패 시 로그만 남기고 구독은 계속 진행
            print(f"Failed to register subscription with Mailie API: {e}")
        
        return Subscription(**record)

    def opt_in_advanced_content(self, payload: AdvancedOptInRequest) -> Subscription:
        
        existing = (
            self.supabase.table(SUBSCRIPTIONS_TABLE)
            .select("*")
            .eq("email", payload.email)
            .maybe_single()
            .execute()
        )

        if not existing or not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="구독 정보를 찾지 못했습니다.",
            )

        record = existing.data

        intro_completed_at = record.get("intro_completed_at")
        progress_day = record.get("progress_day", 0)

        if not intro_completed_at and progress_day <= INTRO_COURSE_DAYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="5일차 콘텐츠를 모두 완료한 후 신청할 수 있습니다.",
            )

        if record.get("advanced_opt_in"):
            return Subscription(**record)

        update_response = (
            self.supabase.table(SUBSCRIPTIONS_TABLE)
            .update(
                {
                    "advanced_opt_in": True,
                    "advanced_opted_in_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                }
            )
            .eq("id", record["id"])
            # .maybe_single()
            .execute()
        )
        print(update_response)

        if not update_response or not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="심화 콘텐츠 신청 상태를 업데이트하지 못했습니다.",
            )

        return Subscription(**update_response.data)
