from github_activity_collector.repositories import allowed


def test_allowlist_and_exclude_take_precedence():
    config = {"repositories": {"include": ["me/*"], "exclude": ["me/nope"]}, "collection": {"include_private": True, "include_public": True}}
    assert allowed("me/yes", False, config)
    assert not allowed("me/nope", False, config)
    assert not allowed("other/yes", False, config)
