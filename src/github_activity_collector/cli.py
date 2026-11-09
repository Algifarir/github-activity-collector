import argparse
import json
import logging
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml
from .authentication import token
from .collector import collect
from .github_client import GitHubClient
from .reporting import JAKARTA, copilot_context, period_for, report
from .repositories import discover
from .storage import LocalStorage


def config():
    path = Path("config/repositories.yml")
    if not path.exists(): raise SystemExit("Copy config/repositories.example.yml to config/repositories.yml and configure explicit allowlists.")
    return yaml.safe_load(path.read_text()) or {}


def bounds(args, storage=None, cfg=None):
    if args.incremental:
        state = storage.load_state() if storage else {}
        if last := state.get("last_successful_collection"):
            overlap = (cfg or {}).get("collection", {}).get("overlap_hours", 24)
            return datetime.fromisoformat(last).astimezone(UTC) - timedelta(hours=overlap), datetime.now(UTC)
        days = (cfg or {}).get("collection", {}).get("initial_backfill_days", 90)
        return datetime.now(UTC) - timedelta(days=days), datetime.now(UTC)
    if args.today: day = date.today(); return period_for(day, "daily")
    start = date.fromisoformat(args.from_date or args.date); end = date.fromisoformat(args.to or args.from_date or args.date)
    if end < start: raise SystemExit("--to must not be earlier than --from.")
    tz = ZoneInfo("Asia/Jakarta"); return datetime.combine(start, time.min, tz).astimezone(ZoneInfo("UTC")), datetime.combine(end, time.max, tz).astimezone(ZoneInfo("UTC"))


def diagnostic(client, cfg, storage, show_repositories=False):
    identity = client.request("GET", "/user")
    identity_headers = client.last_headers
    repos = discover(client, cfg)
    reports = sorted((storage.root / "daily").glob("github_activity_*.json"))
    latest = json.loads(reports[-1].read_text()) if reports else {}
    result = {"authenticated_as": identity.get("login"), "configured_github_username": cfg["github"]["username"], "configured_author_emails": cfg["github"].get("author_emails", []), "configured_repository_patterns": cfg.get("repositories", {}).get("include", []), "configured_organizations": cfg.get("organizations", {}).get("include", []), "accessible_authorized_repository_count": len(repos), "token_scopes": identity_headers.get("x-oauth-scopes", "not reported by GitHub"), "rate_limit_remaining": identity_headers.get("x-ratelimit-remaining", "not reported by GitHub"), "last_collection_statistics": latest.get("statistics")}
    if show_repositories: result["accessible_repositories"] = [repo["full_name"] for repo in repos]
    return result


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    collect_p = sub.add_parser("collect"); group = collect_p.add_mutually_exclusive_group(required=True); group.add_argument("--today", action="store_true"); group.add_argument("--date"); group.add_argument("--from", dest="from_date"); group.add_argument("--incremental", action="store_true"); collect_p.add_argument("--to")
    report_p = sub.add_parser("report"); group = report_p.add_mutually_exclusive_group(required=True); group.add_argument("--weekly", action="store_true"); group.add_argument("--monthly", action="store_true")
    sub.add_parser("export").add_argument("--format", choices=["copilot"], required=True); sub.add_parser("doctor"); diagnose_p = sub.add_parser("diagnose"); diagnose_p.add_argument("--show-repositories", action="store_true")
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg, storage = config(), LocalStorage()
    if args.command == "doctor":
        repos = discover(GitHubClient(token()), cfg); print(f"Authentication works; {len(repos)} explicitly permitted repositories accessible."); return
    if args.command == "diagnose":
        print(json.dumps(diagnostic(GitHubClient(token()), cfg, storage, args.show_repositories), indent=2)); return
    if args.command == "collect":
        start, end = bounds(args, storage, cfg); client = GitHubClient(token()); events, warnings = collect(client, discover(client, cfg), cfg["github"]["username"], cfg["github"].get("author_emails", []), start, end)
        payload = report(events, start, end, cfg, warnings); stamp = start.astimezone(JAKARTA).date().isoformat(); storage.save_json("daily", f"github_activity_{stamp}.json", payload); storage.save_csv("daily", f"github_activity_{stamp}.csv", payload["activities"])
        if not warnings: storage.save_state({"last_successful_collection": datetime.now(ZoneInfo("UTC")).isoformat()})
        print(json.dumps({"collection_status": payload["collection_metadata"]["collection_status"], "activities": len(events), "commits": payload["statistics"]["commits"], "pull_requests_created": payload["statistics"]["pull_requests_created"], "reviews": payload["statistics"]["reviews"], "issues": payload["statistics"]["issues"], "repository_count": len(payload["repositories"]), "warning_count": len(warnings)}, indent=2)); return
    daily = sorted((storage.root / "daily").glob("github_activity_*.json"))
    if not daily: raise SystemExit("No daily reports found; collect first.")
    reports = [json.loads(path.read_text()) for path in daily]
    payload = reports[-1]
    if args.command == "export": storage.save_json("daily", "activity_report_context.json", copilot_context(payload)); return
    mode = "weekly" if args.weekly else "monthly"; start, end = period_for(date.today(), mode)
    events = [event for item in reports for event in item["activities"]]
    warnings = [warning for item in reports for warning in item["collection_metadata"]["warnings"]]
    output = report(events, start, end, cfg, warnings, mode); label = f"{start.astimezone(JAKARTA).date()}_to_{end.astimezone(JAKARTA).date()}" if mode == "weekly" else str(start.astimezone(JAKARTA).date())[:7]; storage.save_json(mode, f"{mode}_{label}.json", output); storage.save_csv(mode, f"{mode}_{label}.csv", output["activities"])

if __name__ == "__main__": main()
