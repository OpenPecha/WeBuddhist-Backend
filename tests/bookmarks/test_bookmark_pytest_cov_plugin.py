from pecha_api.bookmarks.pytest_cov_plugin import _is_bookmark_only_run


def test_is_bookmark_only_run_detects_bookmark_test_paths():
    assert _is_bookmark_only_run(["tests/bookmarks/", "--cov=pecha_api"]) is True
    assert _is_bookmark_only_run([r"tests\bookmarks", "--cov=pecha_api"]) is True
    assert _is_bookmark_only_run(["tests/plans/", "--cov=pecha_api"]) is False
    assert _is_bookmark_only_run(["tests/bookmarks/", "tests/plans/"]) is False
    assert _is_bookmark_only_run(["--cov=pecha_api"]) is False
    assert _is_bookmark_only_run(["tests/bookmarks/test_bookmark_utils.py"]) is True
