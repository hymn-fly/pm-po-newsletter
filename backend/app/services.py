from datetime import datetime, timezone
from zoneinfo import ZoneInfo


from fastapi import HTTPException, status
from supabase import Client

from app.email_service import MailieClient
from app.schemas import Subscription, SubscriptionCreate

SUBSCRIPTIONS_TABLE = "subscriptions"


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