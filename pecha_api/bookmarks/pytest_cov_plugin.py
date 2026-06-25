import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):  # pragma: no cover
    if _is_bookmark_only_run(args):
        namespace = early_config.known_args_namespace
        cov_source = getattr(namespace, "cov_source", None)
        if cov_source == ["pecha_api"]:
            namespace.cov_source = ["pecha_api/bookmarks"]
    yield


def _is_bookmark_only_run(args: list[str]) -> bool:
    test_paths = [
        str(arg).replace("\\", "/")
        for arg in args
        if not str(arg).startswith("-")
    ]
    test_paths = [path for path in test_paths if "tests/" in path or path.endswith(".py")]
    return bool(test_paths) and all("bookmarks" in path for path in test_paths)
