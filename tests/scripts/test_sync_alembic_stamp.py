from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts.sync_alembic_stamp import (
    _compute_applied,
    _revision_markers_pass,
    _should_stamp_forward,
    sync_stamp,
)


def test_revision_markers_pass_returns_false_without_explicit_markers():
    conn = MagicMock()
    revision = SimpleNamespace(revision="unknown_revision", down_revision="y9z0a1b2c3d4")

    assert _revision_markers_pass(conn, revision) is False


def test_revision_markers_pass_checks_series_partner_marker():
    conn = MagicMock()
    revision = SimpleNamespace(revision="866bdb766987", down_revision="y9z0a1b2c3d4")

    with patch(
        "scripts.sync_alembic_stamp._marker_passes",
        return_value=True,
    ) as mock_marker:
        assert _revision_markers_pass(conn, revision) is True

    mock_marker.assert_called_once_with(conn, ("table", "series_partner"))


def test_revision_markers_pass_allows_merge_revisions_without_markers():
    conn = MagicMock()
    revision = SimpleNamespace(
        revision="a967e8ec07c8",
        down_revision=("f0eab4237ef7", "z2a3b4c5d6e7"),
    )

    assert _revision_markers_pass(conn, revision) is True


def test_compute_applied_does_not_mark_unmarked_migration_as_applied():
    script = MagicMock()
    script.walk_revisions.return_value = [
        SimpleNamespace(revision="866bdb766987", down_revision="y9z0a1b2c3d4"),
        SimpleNamespace(revision="y9z0a1b2c3d4", down_revision=None),
    ]
    conn = MagicMock()

    with patch(
        "scripts.sync_alembic_stamp._revision_markers_pass",
        side_effect=lambda _conn, revision: revision.revision == "y9z0a1b2c3d4",
    ):
        applied = _compute_applied(script, conn)

    assert applied["y9z0a1b2c3d4"] is True
    assert applied["866bdb766987"] is False


def test_should_stamp_forward_when_current_stamp_is_ahead_of_verified_schema():
    applied = {"y9z0a1b2c3d4": True, "866bdb766987": False}

    assert _should_stamp_forward("866bdb766987", "y9z0a1b2c3d4", applied) is True
    assert _should_stamp_forward("y9z0a1b2c3d4", "866bdb766987", applied) is False


def test_sync_stamp_skipped_when_env_disabled():
    with patch("scripts.sync_alembic_stamp.get", return_value="false"):
        with patch("scripts.sync_alembic_stamp.create_engine") as mock_engine:
            sync_stamp()

    mock_engine.assert_not_called()
