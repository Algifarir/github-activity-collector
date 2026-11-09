# GitHub Activity Collector

Metadata-only Python collector for GitHub commits, pull requests, reviews, and issues. It works with private repositories when the configured credential can read them; it never requests source files, diffs, or patches.

## Setup

1. Copy `config/repositories.example.yml` to `config/repositories.yml`. List only repositories and organisations approved for collection. Organisations are disabled until added to `organizations.include`.
2. Set either `GITHUB_TOKEN` to a fine-grained PAT with **read-only Metadata, Contents, Pull requests, Issues** access to only those repositories, or set all GitHub App variables in `.env.example`. A GitHub App needs the same read-only repository permissions and an installation limited to the approved repositories.
3. `python -m venv .venv`, activate it, then `pip install -r requirements.txt`.

Run `python -m github_activity_collector doctor`, then `python -m github_activity_collector collect --today`. Use `collect --incremental` for the saved-state timestamp plus its configurable overlap window. Reports go to `data/daily`; `report --weekly`, `report --monthly`, and `export --format copilot` create the other outputs.

## Security and operations

Credentials are environment-only and are not logged. Configure anonymization/title redaction for exports leaving the company boundary. The Actions workflow uses secrets, runs at 05:00 WIB (22:00 UTC), tests first, and uploads private artifacts for 14 days; it never commits report data.

GitHub Actions runners are ephemeral, so artifacts do **not** provide durable incremental state. For reliable history, run with a persistent storage volume or add a storage adapter (the `LocalStorage` seam) before relying on scheduled incremental collection. GitHub does not reliably expose an issue closer in every case; issue closure is therefore not claimed unless future API/event data proves it.
