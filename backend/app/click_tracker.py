from typing import Dict

from supabase import Client

PAGE_COUNTS_TABLE = "page_counts"


class ClickTracker:
    def __init__(self, supabase: Client) -> None:
        self._supabase = supabase

    def increment(self, href: str) -> int:
        existing = (
            self._supabase.table(PAGE_COUNTS_TABLE)
            .select("href,count")
            .eq("href", href)
            .limit(1)
            .execute()
        )
        if existing:
            if hasattr(existing, "error") and existing.error:
                message = getattr(existing.error, "message", str(existing.error))
                raise RuntimeError(f"Failed to fetch page count: {message}")

            record = (existing.data[0] if isinstance(existing.data, list) and existing.data else existing.data)
            if record:
                current_count = int(record.get("count") or 0) + 1
                update = (
                    self._supabase.table(PAGE_COUNTS_TABLE)
                    .update({"count": current_count})
                    .eq("href", href)
                    .execute()
                )
                if hasattr(update, "error") and update.error:
                    message = getattr(update.error, "message", str(update.error))
                    raise RuntimeError(f"Failed to update page count: {message}")

                updated_record = (
                    update.data[0]
                    if isinstance(update.data, list) and update.data
                    else (update.data or {})
                )
                updated_count = int(updated_record.get("count") or current_count)
                return updated_count

        insert = (
            self._supabase.table(PAGE_COUNTS_TABLE)
            .insert({"href": href, "count": 1})
            .execute()
        )
        if hasattr(insert, "error") and insert.error:
            message = getattr(insert.error, "message", str(insert.error))
            if "duplicate key value" in message.lower():
                # Another request inserted the same href concurrently; retry update path
                return self.increment(href)
            raise RuntimeError(f"Failed to insert page count: {message}")

        inserted = insert.data[0] if insert.data else {"href": href, "count": 1}
        return int(inserted.get("count") or 1)

    def get_counts(self) -> Dict[str, int]:
        result = (
            self._supabase.table(PAGE_COUNTS_TABLE)
            .select("href,count")
            .execute()
        )

        if result.error:
            message = getattr(result.error, "message", str(result.error))
            raise RuntimeError(f"Failed to retrieve page counts: {message}")

        records = result.data or []
        return {
            str(item.get("href")): int(item.get("count") or 0)
            for item in records
        }
