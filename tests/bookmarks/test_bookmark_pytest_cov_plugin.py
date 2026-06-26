from pathlib import Path

from pecha_api.bookmarks import pytest_cov_plugin
from pecha_api.bookmarks.pytest_cov_plugin import (
    _expand_to_bookmarks_suite,
    _has_coverage,
    _is_bookmark_only_run,
    _is_bookmark_test_path,
    _is_full_bookmarks_suite,
    _looks_like_test_path,
)


def test_is_bookmark_test_path_detects_bookmark_tests():
    assert _is_bookmark_test_path("tests/bookmarks/test_bookmark_services.py") is True
    assert _is_bookmark_test_path(r"tests\bookmarks\test_bookmark_utils.py") is True
    assert _is_bookmark_test_path("test_bookmark_services.py") is True
    assert _is_bookmark_test_path("tests/plans/test_plan_service.py") is False


def test_is_bookmark_only_run_detects_bookmark_test_paths():
    assert _is_bookmark_only_run(["tests/bookmarks/", "--cov=pecha_api"]) is True
    assert _is_bookmark_only_run([r"tests\bookmarks", "--cov=pecha_api"]) is True
    assert _is_bookmark_only_run(["test_bookmark_services.py", "--cov=pecha_api"]) is True
    assert _is_bookmark_only_run(
        ["tests/bookmarks/test_bookmark_services.py::test_create_bookmark_service_success", "--cov=pecha_api"]
    ) is True
    assert _is_bookmark_only_run(["tests/plans/", "--cov=pecha_api"]) is False
    assert _is_bookmark_only_run(["tests/bookmarks/", "tests/plans/"]) is False


def test_is_full_bookmarks_suite_detects_directory_run():
    rootpath = Path("d:/work/WeBuddhist-Backend")
    bookmarks_dir = str(rootpath / "tests" / "bookmarks")

    assert _is_full_bookmarks_suite(["tests/bookmarks/", "--cov=pecha_api"], rootpath) is True
    assert _is_full_bookmarks_suite([bookmarks_dir, "--cov=pecha_api"], rootpath) is True
    assert _is_full_bookmarks_suite(
        ["tests/bookmarks/test_bookmark_services.py", "--cov=pecha_api"],
        rootpath,
    ) is False


def test_expand_to_bookmarks_suite_replaces_single_file_with_directory():
    rootpath = Path("d:/work/WeBuddhist-Backend")
    bookmarks_dir = str(rootpath / "tests" / "bookmarks")
    args = [
        "tests/bookmarks/test_bookmark_services.py",
        "--cov=pecha_api/bookmarks",
        "-q",
    ]

    _expand_to_bookmarks_suite(args, rootpath)

    assert args == ["--cov=pecha_api/bookmarks", "-q", bookmarks_dir]


def test_looks_like_test_path():
    assert _looks_like_test_path("tests/plans/") is True
    assert _looks_like_test_path("test_bookmark_services.py") is True
    assert _looks_like_test_path("--cov=pecha_api") is False


def test_has_coverage_detects_cov_flags_and_namespace():
    namespace = type("Namespace", (), {"cov_source": ["pecha_api"]})()

    assert _has_coverage(["tests/bookmarks/", "--cov=pecha_api"], namespace) is True
    assert _has_coverage(["tests/bookmarks/"], namespace) is True
    assert _has_coverage(["tests/bookmarks/"], type("Namespace", (), {})()) is False


def test_expand_to_bookmarks_suite_is_noop_for_full_directory_run():
    rootpath = Path("d:/work/WeBuddhist-Backend")
    args = ["tests/bookmarks/", "--cov=pecha_api", "-q"]

    _expand_to_bookmarks_suite(args, rootpath)

    assert args == ["tests/bookmarks/", "--cov=pecha_api", "-q"]


def test_pytest_load_initial_conftests_narrows_cov_and_expands_suite():
    rootpath = Path("d:/work/WeBuddhist-Backend")
    bookmarks_dir = str(rootpath / "tests" / "bookmarks")
    args = ["tests/bookmarks/test_bookmark_services.py", "--cov=pecha_api"]
    namespace = type("Namespace", (), {"cov_source": ["pecha_api"]})()
    early_config = type("EarlyConfig", (), {"known_args_namespace": namespace, "rootpath": rootpath})()
    parser = object()

    list(pytest_cov_plugin.pytest_load_initial_conftests(early_config, parser, args))

    assert args == ["--cov=pecha_api", bookmarks_dir]
    assert namespace.cov_source == ["pecha_api/bookmarks"]
