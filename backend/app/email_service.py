from datetime import datetime

import httpx

from .config import get_settings


class MailieClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = str(settings.mailie_api_base_url).rstrip("/")
        self.api_key = settings.mailie_api_key
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def send_course_email(self, email: str, day: int) -> None:
        payload = {
            "recipient": email,
            "course_day": day,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = self._client.post("/v1/campaigns/pm-letter", json=payload, headers=headers)
        response.raise_for_status()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MailieClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


def mark_email_sent(supabase_client, subscription_id: int, progress_day: int, sent_at: datetime) -> None:
    supabase_client.table("subscriptions").update(
        {
            "progress_day": progress_day,
            "last_sent_at": sent_at.isoformat(),
        }
    ).eq("id", subscription_id).execute()
