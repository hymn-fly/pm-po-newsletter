from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from .config import get_settings


class MailieClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = str(settings.mailie_api_base_url).rstrip("/")
        self.api_key = settings.mailie_api_key
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def reserve_email_sending(self, supabase_client, email: str, progress_day: int) -> None:
        mapping_response = (
            supabase_client.table("progress_day_email_map")
            .select("automated_email_ext_id,automated_email_trigger_ext_id")
            .eq("progress_day", progress_day)
            .maybe_single()
            .execute()
        )

        mapping = mapping_response.data
        if not mapping:
            raise ValueError(f"Progress daily email map not found for progress day {progress_day}")

        automated_email_ext_id = mapping["automated_email_ext_id"]
        automated_email_trigger_ext_id = mapping["automated_email_trigger_ext_id"]

        payload = {
            "email": email,
            "automated_email_trigger_ext_id": automated_email_trigger_ext_id,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = self._client.post(
            f"/api/pmletter7/automated_emails/{automated_email_ext_id}/trigger.json",
            json=payload,
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(f"Failed to trigger email for progress day {progress_day}: {response.text}")

    def create_subscription(self, email: str, name: str = None, marketing_agreement: bool = True, marketing_agreed_at: str = None) -> dict:
        """
        구독자 신규등록 API를 호출합니다.
        
        Args:
            email: 구독자 이메일 (필수)
            name: 닉네임 (선택)
            marketing_agreement: 마케팅 동의 여부 (기본값: True)
            marketing_agreed_at: 마케팅 동의 시간 (ISO 형식, 기본값: 현재 시간)
        
        Returns:
            API 응답 데이터
        """
        
        
        payload = {
            "email": email,
            "marketing_agreement": marketing_agreement,
        }
        
        # 선택적 필드들 추가
        if name:
            payload["name"] = name
            
        payload["marketing_agreed_at"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = self._client.post("/api/pmletter7/subscriptions.json", json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise ValueError(f"Failed to create subscription: {response.text}")
        
        return response.json()
    
    

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MailieClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


def mark_email_sent(
    supabase_client,
    subscription_id: int,
    progress_day: int,
    sent_at: datetime,
    intro_completed: bool = False,
) -> None:
    update_payload = {
        "progress_day": progress_day,
        "last_sent_at": sent_at.isoformat(),
    }

    if intro_completed:
        update_payload["intro_completed_at"] = sent_at.isoformat()

    supabase_client.table("subscriptions").update(update_payload).eq("id", subscription_id).execute()
