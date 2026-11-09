from fnmatch import fnmatch


def allowed(name: str, private: bool, config: dict) -> bool:
    collection = config.get("collection", {})
    if private and not collection.get("include_private", True) or not private and not collection.get("include_public", True):
        return False
    include = config.get("repositories", {}).get("include", [])
    orgs = config.get("organizations", {}).get("include", [])
    owner = name.split("/", 1)[0]
    return (any(fnmatch(name, pattern) for pattern in include) or owner in orgs) and not any(fnmatch(name, pattern) for pattern in config.get("repositories", {}).get("exclude", []))


def discover(client, config: dict) -> list[dict]:
    repos = {repo["full_name"]: repo for repo in client.pages("/user/repos", {"affiliation": "owner,collaborator,organization_member", "sort": "updated"})}
    for org in config.get("organizations", {}).get("include", []):
        repos.update({repo["full_name"]: repo for repo in client.pages(f"/orgs/{org}/repos", {"type": "all", "sort": "updated"})})
    return [repo for repo in repos.values() if allowed(repo["full_name"], repo.get("private", False), config)]
