from datetime import UTC, datetime
from github_activity_collector.collector import collect


class Client:
    def pages(self, path, params=None):
        if path.endswith("/branches"): return iter([{"name": "main"}, {"name": "release"}])
        if path.endswith("/commits"):
            return iter([{"sha": "same", "author": {"login": "me"}, "commit": {"author": {"date": "2026-11-09T01:00:00Z", "email": "me@test"}, "message": "done"}, "html_url": "https://x"}])
        return iter([])


def test_commit_seen_on_two_branches_is_deduplicated():
    events, warnings = collect(Client(), [{"full_name": "me/repo", "default_branch": "main"}], "me", [], datetime(2026, 11, 9, tzinfo=UTC), datetime(2026, 11, 10, tzinfo=UTC))
    assert not warnings
    assert [event["id"] for event in events] == ["commit:me/repo:same"]
