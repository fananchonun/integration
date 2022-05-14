"""Sample datasets for testing."""
# pylint: disable=invalid-name,missing-docstring

repository_data = {
    "id": 999999999,
    "full_name": "test/test",
    "fork": False,
    "description": "Sample description for repository.",
    "pushed_at": "1970-01-01T00:00:00Z",
    "stargazers_count": 999,
    "archived": False,
    "topics": ["topic1", "topic2"],
    "default_branch": "master",
    "last_commit": "12345678",
}

response_rate_limit_header = {
    "X-RateLimit-Limit": "999",
    "X-RateLimit-Remaining": "999",
    "X-RateLimit-Reset": "999",
    "Content-Type": "application/json",
}

response_rate_limit_header_with_limit = {
    "X-RateLimit-Limit": "",
    "X-RateLimit-Remaining": "0",
    "X-RateLimit-Reset": "999",
    "Content-Type": "application/json",
}

tree_files_base = {
    "tree": [
        {"path": "info.md", "type": "blob"},
        {"path": "readme.md", "type": "blob"},
        {"path": "hacs.json", "type": "blob"},
    ]
}


def tree_files_base_integration():
    integrationtree = tree_files_base
    integrationtree["tree"].append(
        {"path": "custom_components/test/manifest.json", "type": "blob"}
    )
    integrationtree["tree"].append(
        {"path": "custom_components/test/__init__.py", "type": "blob"}
    )
    integrationtree["tree"].append(
        {"path": "custom_components/test/sensor.py", "type": "blob"}
    )
    integrationtree["tree"].append(
        {"path": "custom_components/test/.translations/en.json", "type": "blob"}
    )
    return integrationtree
