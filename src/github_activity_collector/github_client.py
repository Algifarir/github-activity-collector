import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG = logging.getLogger(__name__)


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    base_url = "https://api.github.com"

    def __init__(self, access_token: str, auth_scheme: str = "token"):
        self.access_token, self.auth_scheme = access_token, auth_scheme

    def request(self, method: str, path: str, params: dict | None = None) -> dict | list:
        url = self.base_url + path + (("?" + urlencode(params)) if params else "")
        request = Request(url, method=method, headers={"Accept": "application/vnd.github+json", "Authorization": f"{self.auth_scheme} {self.access_token}", "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code in (401, 403):
                raise GitHubError("GitHub authentication, authorization, or rate-limit failure. Check token permissions and retry later.") from error
            raise GitHubError(f"GitHub API request failed ({error.code}) for {path}.") from error
        except URLError as error:
            raise GitHubError("GitHub API is unreachable.") from error

    def pages(self, path: str, params: dict | None = None):
        params = {**(params or {}), "per_page": 100}
        for page in range(1, 101):
            payload = self.request("GET", path, {**params, "page": page})
            if not payload:
                return
            yield from payload
            if len(payload) < 100:
                return
        raise GitHubError(f"Pagination limit reached for {path}.")
