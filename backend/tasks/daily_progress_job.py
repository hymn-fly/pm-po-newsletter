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
        .lt("progress_day", COURSE_TOTAL_DAYS)
        .order("id")
        .execute()
    )

    subscriptions = response.data or []

    if not subscriptions:
        logger.info("No pending subscriptions to process.")
        return

    with MailieClient() as mailie:
        for subscription in subscriptions:
            next_day = subscription["progress_day"] + 1
            email = subscription["email"]

            try:
                mailie.send_course_email(email=email, day=next_day)
                mark_email_sent(
                    supabase_client=supabase,
                    subscription_id=subscription["id"],
                    progress_day=next_day,
                    sent_at=now,
                )
                logger.info("Sent day %s content to %s", next_day, email)
            except Exception as exc:  # noqa: BLE001 - we want to log and continue
                logger.exception("Failed to send email for %s day %s: %s", email, next_day, exc)


if __name__ == "__main__":
    run()
