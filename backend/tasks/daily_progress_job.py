"""Railway cron entrypoint to advance the 5-day course and trigger Mailie emails."""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.email_service import MailieClient, mark_email_sent
from app.supabase_client import get_supabase_client

COURSE_TOTAL_DAYS = 5


def run() -> None:
    supabase = get_supabase_client()
    now = datetime.now(timezone.utc)

    response = (
        supabase.table("subscriptions")
        .select("id,email,progress_day")
        .order("id")
        .execute()
    )

    subscriptions = response.data or []

    if not subscriptions:
        logger.info("No pending subscriptions to process.")
        return

    with MailieClient() as mailie:
        for subscription in subscriptions:
            current_day = subscription["progress_day"]
            email = subscription["email"]

            try:
                mailie.reserve_email_sending(
                    supabase_client=supabase, email=email, progress_day=current_day)
                mark_email_sent(
                    supabase_client=supabase,
                    subscription_id=subscription["id"],
                    progress_day=current_day + 1,
                    sent_at=now,
                )
                logger.info(f"Sent day {current_day} content to {email}")
            except Exception as exc:  # noqa: BLE001 - we want to log and continue
                logger.exception(f"Failed to send email for {email} day {current_day}: {exc}")


if __name__ == "__main__":
    run()
