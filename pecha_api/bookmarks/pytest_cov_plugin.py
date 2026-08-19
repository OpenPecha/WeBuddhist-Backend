from __future__ import annotations

from pathlib import Path

import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    if _is_bookmark_only_run(args):
        namespace = early_config.known_args_namespace
        if _has_coverage(args, namespace):
            _expand_to_bookmarks_suite(args, early_config.rootpath)
            cov_source = getattr(namespace, "cov_source", None)
            if cov_source == ["pecha_api"]:
                namespace.cov_source = ["pecha_api/bookmarks"]
    yield


def _has_coverage(args: list[str], namespace) -> bool:
    if any(str(arg).startswith("--cov") for arg in args):
        return True
    return getattr(namespace, "cov_source", None) is not None


def _is_bookmark_test_path(path: str) -> bool:
    normalized = str(path).replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1]
    if "tests/" in normalized and "bookmarks" in normalized:
        return True
    return basename.startswith("test_bookmark_") and basename.endswith(".py")


def _is_bookmark_only_run(args: list[str]) -> bool:
    test_paths = [
        _test_path_from_arg(str(arg))
        for arg in args
        if not str(arg).startswith("-") and _looks_like_test_path(str(arg))
    ]
    return bool(test_paths) and all(_is_bookmark_test_path(path) for path in test_paths)


def _looks_like_test_path(path: str) -> bool:
    normalized = str(path).replace("\\", "/")
    return "tests/" in normalized or normalized.endswith(".py")


def _test_path_from_arg(arg: str) -> str:
    return arg.split("::", 1)[0]


def _is_full_bookmarks_suite(args: list[str], rootpath: Path) -> bool:
    bookmarks_dir = _bookmarks_test_dir(rootpath)
    for arg in args:
        if str(arg).startswith("-"):
            continue
        candidate = (_test_path_from_arg(str(arg))).replace("\\", "/").rstrip("/")
        if candidate in {str(bookmarks_dir), str(bookmarks_dir).replace("\\", "/")}:
            return True
        if candidate in {"tests/bookmarks", "tests/bookmarks/"}:
            return True
    return False


def _expand_to_bookmarks_suite(args: list[str], rootpath: Path) -> None:
    if _is_full_bookmarks_suite(args, rootpath):
        return

    bookmarks_dir = str(_bookmarks_test_dir(rootpath))
    new_args: list[str] = []
    for arg in args:
        test_path = _test_path_from_arg(str(arg))
        if not str(arg).startswith("-") and _is_bookmark_test_path(test_path):
            continue
        new_args.append(arg)

    new_args.append(bookmarks_dir)
    args[:] = new_args


def _bookmarks_test_dir(rootpath: Path) -> Path:
    return rootpath / "tests" / "bookmarks"
