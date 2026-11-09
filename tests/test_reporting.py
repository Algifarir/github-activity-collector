from datetime import UTC, date, datetime
from github_activity_collector.reporting import JAKARTA, period_for, report


def test_week_starts_thursday_in_jakarta():
    start, end = period_for(date(2026, 11, 9), "weekly")
    assert start.astimezone(JAKARTA).date() == date(2026, 11, 5)
    assert end.astimezone(JAKARTA).date() == date(2026, 11, 11)


def test_month_uses_full_jakarta_month():
    start, end = period_for(date(2026, 11, 1), "monthly")
    assert (start.astimezone(JAKARTA).date(), end.astimezone(JAKARTA).date()) == (date(2026, 11, 1), date(2026, 11, 30))


def test_report_counts_only_actual_deduplicated_events():
    event = {"id": "commit:o/r:1", "type": "commit", "repository": "o/r", "date": "2026-11-09T01:00:00Z", "description": "x", "url": "https://example.test"}
    result = report([event], datetime(2026, 11, 8, tzinfo=UTC), datetime(2026, 11, 10, tzinfo=UTC), {"github": {"username": "me"}}, [], "daily")
    assert result["statistics"]["commits"] == 1
