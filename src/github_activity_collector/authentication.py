import os
from datetime import UTC, datetime, timedelta


class AuthenticationError(RuntimeError):
    pass


def token() -> str:
    """Return a PAT, or exchange GitHub App credentials for an installation token."""
    if value := os.getenv("GITHUB_TOKEN"):
        return value
    app_id, installation, key = (os.getenv(name) for name in ("GITHUB_APP_ID", "GITHUB_APP_INSTALLATION_ID", "GITHUB_APP_PRIVATE_KEY"))
    if not all((app_id, installation, key)):
        raise AuthenticationError("Set GITHUB_TOKEN or all GitHub App environment variables.")
    try:
        import jwt
        from .github_client import GitHubClient
        now = datetime.now(UTC)
        signed = jwt.encode({"iat": now - timedelta(seconds=60), "exp": now + timedelta(minutes=9), "iss": app_id}, key.replace("\\n", "\n"), algorithm="RS256")
        response = GitHubClient(signed, auth_scheme="Bearer").request("POST", f"/app/installations/{installation}/access_tokens")
        return response["token"]
    except Exception as error:
        raise AuthenticationError("Could not obtain a GitHub App installation token.") from error
