from collections import Counter
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

JAKARTA = ZoneInfo("Asia/Jakarta")


def period_for(day, mode: str):
    local = datetime.combine(day, datetime.min.time(), JAKARTA)
    if mode == "weekly":
        start = local - timedelta(days=(local.weekday() - 3) % 7); end = start + timedelta(days=7) - timedelta(microseconds=1)
    elif mode == "monthly":
        start = local.replace(day=1); next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1); end = next_month - timedelta(microseconds=1)
    else: start = local; end = local + timedelta(days=1) - timedelta(microseconds=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def report(events: list[dict], start: datetime, end: datetime, config: dict, warnings: list[str], report_type="daily") -> dict:
    included = [item for item in events if start <= datetime.fromisoformat(item["date"].replace("Z", "+00:00")) <= end]
    counts = Counter(item["type"] for item in included)
    clean = [{**item, "repository": "private-repository" if config.get("collection", {}).get("anonymize_repositories") else item["repository"], "description": "Private activity" if config.get("collection", {}).get("redact_titles") else item["description"]} for item in included]
    return {"schema_version": "1.0", "report_type": report_type, "developer": {"name": config.get("developer_name", ""), "github_username": config["github"]["username"]}, "period": {"start": start.astimezone(JAKARTA).date().isoformat(), "end": end.astimezone(JAKARTA).date().isoformat(), "timezone": "Asia/Jakarta"}, "statistics": {"commits": counts["commit"], "pull_requests_created": counts["pull_request_created"], "pull_requests_merged": counts["pull_request_merged"], "reviews": counts["review"], "issues": sum(v for k, v in counts.items() if k.startswith("issue_"))}, "activities": clean, "repositories": sorted({x["repository"] for x in clean}), "collection_metadata": {"generated_at": datetime.now(UTC).isoformat(), "collection_status": "partial" if warnings else "complete", "warnings": warnings}}


def copilot_context(payload: dict) -> dict:
    return {"report_type": payload["report_type"], "period": payload["period"], "developer": payload["developer"]["name"], "github_username": payload["developer"]["github_username"], "statistics": payload["statistics"], "contributions": payload["activities"], "source_references": [x["url"] for x in payload["activities"]], "collection_metadata": payload["collection_metadata"]}
