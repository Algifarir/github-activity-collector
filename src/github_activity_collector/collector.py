from datetime import UTC, datetime


def _when(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC) if value else None


def _inside(value: str | None, start: datetime, end: datetime) -> bool:
    moment = _when(value)
    return bool(moment and start <= moment <= end)


def _activity(kind: str, repo: str, identifier: str, date: str, description: str, url: str, **extra) -> dict:
    return {"id": f"{kind}:{repo}:{identifier}", "type": kind, "repository": repo, "date": date, "description": description, "url": url, **extra}


def collect(client, repos: list[dict], username: str, author_emails: list[str], start: datetime, end: datetime) -> tuple[list[dict], list[str]]:
    """Collect metadata only; never asks GitHub for blobs, patches, or diffs."""
    events, warnings = [], []
    for repo_data in repos:
        repo = repo_data["full_name"]
        try:
            branches = {repo_data.get("default_branch", "main")}
            branches.update(branch["name"] for branch in client.pages(f"/repos/{repo}/branches"))
            for branch in branches:
                for commit in client.pages(f"/repos/{repo}/commits", {"sha": branch, "since": start.isoformat(), "until": end.isoformat(), "author": username}):
                    author = commit.get("author") or {}; details = commit["commit"]
                    if author.get("login") == username or details.get("author", {}).get("email") in author_emails:
                        events.append(_activity("commit", repo, commit["sha"], details["author"]["date"], details["message"].split("\n", 1)[0], commit["html_url"], sha=commit["sha"], author=username))
            pulls = list(client.pages(f"/repos/{repo}/pulls", {"state": "all", "sort": "updated", "direction": "desc"}))
            for pr in pulls:
                number, url = pr["number"], pr["html_url"]
                authored = pr["user"]["login"] == username
                if authored and _inside(pr.get("created_at"), start, end):
                    events.append(_activity("pull_request_created", repo, str(number), pr["created_at"], pr["title"], url, number=number, status="created"))
                if authored and pr.get("merged_at") and _inside(pr["merged_at"], start, end):
                    events.append(_activity("pull_request_merged", repo, f"{number}:merged", pr["merged_at"], pr["title"], url, number=number, status="merged"))
                if authored and pr.get("closed_at") and not pr.get("merged_at") and _inside(pr["closed_at"], start, end):
                    events.append(_activity("pull_request_closed", repo, f"{number}:closed", pr["closed_at"], pr["title"], url, number=number, status="closed"))
                for review in client.pages(f"/repos/{repo}/pulls/{number}/reviews"):
                    if review.get("user", {}).get("login") == username and _inside(review.get("submitted_at"), start, end):
                        events.append(_activity("review", repo, f"{number}:{review['id']}", review["submitted_at"], pr["title"], url, pull_request_number=number, review_state=review["state"]))
                for comment in client.pages(f"/repos/{repo}/issues/{number}/comments"):
                    if comment["user"]["login"] == username and _inside(comment.get("created_at"), start, end):
                        events.append(_activity("pull_request_comment", repo, f"{number}:{comment['id']}", comment["created_at"], pr["title"], url, number=number, status="commented"))
            for issue in client.pages(f"/repos/{repo}/issues", {"state": "all", "since": start.isoformat()}):
                if "pull_request" in issue: continue
                involved = issue.get("user", {}).get("login") == username or any(a["login"] == username for a in issue.get("assignees", []))
                if involved and _inside(issue.get("created_at"), start, end):
                    events.append(_activity("issue_created" if issue["user"]["login"] == username else "issue_assigned", repo, str(issue["number"]), issue["created_at"], issue["title"], issue["html_url"], number=issue["number"], state=issue["state"]))
                for comment in client.pages(f"/repos/{repo}/issues/{issue['number']}/comments"):
                    if comment["user"]["login"] == username and _inside(comment.get("created_at"), start, end):
                        events.append(_activity("issue_comment", repo, f"{issue['number']}:{comment['id']}", comment["created_at"], issue["title"], issue["html_url"], number=issue["number"], state=issue["state"]))
        except Exception as error:
            warnings.append(f"{repo}: {error}")
    return list({event["id"]: event for event in events}.values()), warnings
