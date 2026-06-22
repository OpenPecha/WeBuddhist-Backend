"""Advance alembic_version when schema is ahead of the recorded stamp.

Development databases were stamped with legacy revision ids while schema
migrations from other branches were applied directly. Before `alembic upgrade
head`, detect the highest fully-applied revision and stamp forward when needed.
"""
from __future__ import annotations

import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pecha_api.config import get  # noqa: E402

# revision_id -> schema markers that must exist for that migration to be considered applied
SCHEMA_MARKERS: dict[str, list[tuple]] = {
    "c5e7a9b1d3f2": [
        "any_of",
        [("column", "routine_sessions", "duration_ms")],
        [("enum", "sessiontype", "TIMER")],
    ],
    "e8f9a0b1c2d3": [("column", "series_metadata", "sub_title")],
    "402085623057": [("table", "recitation_collections")],
    "503196734168": [("enum", "sessiontype", "RECITATION_COLLECTION")],
    "a1b2c3d4e5f7": [("table", "verse_of_day")],
    "b2c3d4e5f6a8": [("column", "verse_of_day", "ref_id")],
    "ghxrmguaywg6": [("table", "timers")],
    "9913dcde55ca": [("table", "bookmarks")],
    "4c9060e232ad": [("column_nullable", "bookmarks", "name")],
    "f2a3b4c5d6e7": [("table", "user_daily_logs")],
    "2e73e46c9349": [("table", "timer_history")],
    "b1c2d3e4f5a6": [("table", "accumulators")],
    "c2d3e4f5a6b7": [("table", "accumulator_history")],
    "b7c8d9e0f1a2": [("table", "mantra")],
    "a3b4c5d6e7f9": [("table", "mantra_metadata")],
    "68055a51de95": [("table", "events")],
    "d5e6f7a8b9c0": [("column", "accumulators", "mantra_id")],
    "d1e2f3a4b5c6": [("table", "verse_metadata")],
    "f8a9b0c1d2e3": [("column", "events", "image_url")],
    "a3b4c5d6e7f8": [("table", "author_group_joins")],
    "b4c5d6e7f8a9": [("column", "author_groups", "group_type")],
    "c5d6e7f8a9b0": [("column", "series", "parent_series_id")],
    "c6d7e8f9a0b1": [("column", "author_group_metadata", "description_long")],
    "440953ec8a21": [("table", "content_transfer_requests")],
    "g0a1b2c3d4e5": [
        "any_of",
        [("column_type", "verse_metadata", "verse", "text")],
        [("column_type", "verse_metadata", "verse", "character varying")],
    ],
    "s3t4u5v6w7x8": [("table", "day_videos")],
    "u5v6w7x8y9z0": [("table", "tradition_list")],
}


def _normalize_parents(down_revision: str | Sequence[str] | None) -> tuple[str, ...]:
    if down_revision is None:
        return ()
    if isinstance(down_revision, str):
        return (down_revision,)
    return tuple(down_revision)


def _marker_passes(conn, marker: tuple) -> bool:
    kind = marker[0]
    if kind == "table":
        _, table = marker
        return conn.execute(
            text("SELECT to_regclass(:name) IS NOT NULL"),
            {"name": f"public.{table}"},
        ).scalar()
    if kind == "column":
        _, table, column = marker
        return conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                  AND column_name = :column
                """
            ),
            {"table": table, "column": column},
        ).scalar() is not None
    if kind == "column_nullable":
        _, table, column = marker
        return conn.execute(
            text(
                """
                SELECT is_nullable = 'YES'
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                  AND column_name = :column
                """
            ),
            {"table": table, "column": column},
        ).scalar() is True
    if kind == "enum":
        _, enum_name, value = marker
        return conn.execute(
            text(
                """
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = :enum_name AND e.enumlabel = :value
                """
            ),
            {"enum_name": enum_name, "value": value},
        ).scalar() is not None
    if kind == "column_type":
        _, table, column, data_type = marker
        return conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                  AND column_name = :column
                  AND data_type = :data_type
                """
            ),
            {"table": table, "column": column, "data_type": data_type},
        ).scalar() is not None
    return False


def _revision_markers_pass(conn, revision_id: str) -> bool:
    markers = SCHEMA_MARKERS.get(revision_id)
    if not markers:
        return True
    if markers[0] == "any_of":
        option_groups: Iterable[Sequence[tuple]] = markers[1:]
        return any(
            all(_marker_passes(conn, marker) for marker in option_group)
            for option_group in option_groups
        )
    return all(_marker_passes(conn, marker) for marker in markers)


def _compute_applied(script: ScriptDirectory, conn) -> dict[str, bool]:
    applied: dict[str, bool] = {}
    for revision in reversed(list(script.walk_revisions())):
        revision_id = revision.revision
        parents = _normalize_parents(revision.down_revision)
        parents_applied = all(applied[parent] for parent in parents) if parents else True
        applied[revision_id] = (
            _revision_markers_pass(conn, revision_id) and parents_applied
        )
    return applied


def _get_current_revisions(conn) -> list[str]:
    rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    return [row[0] for row in rows]


def _highest_applied_revision(
    script: ScriptDirectory, applied: dict[str, bool]
) -> str | None:
    for revision in script.walk_revisions():
        if applied.get(revision.revision):
            return revision.revision
    return None


def _is_ancestor(script: ScriptDirectory, ancestor: str, descendant: str) -> bool:
    if ancestor == descendant:
        return False
    for revision in script.walk_revisions(head=descendant):
        if revision.revision == ancestor:
            return True
    return False


def _should_stamp_forward(
    script: ScriptDirectory,
    current: str,
    target: str,
    applied: dict[str, bool],
) -> bool:
    if current == target:
        return False
    if applied.get(target) and not applied.get(current, False):
        return True
    return _is_ancestor(script, current, target)


def sync_stamp() -> None:
    database_url = get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set; skipping alembic stamp sync.")
        return

    config = Config(str(ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    engine = create_engine(database_url)

    with engine.connect() as conn:
        current_revisions = _get_current_revisions(conn)
        if not current_revisions:
            print("No alembic_version row found; leaving stamp unchanged.")
            return
        if len(current_revisions) > 1:
            print(
                "Multiple alembic_version rows found; leaving stamp unchanged: "
                f"{current_revisions}"
            )
            return

        current = current_revisions[0]
        applied = _compute_applied(script, conn)
        target = _highest_applied_revision(script, applied)
        if not target:
            print("Could not detect applied schema revision; leaving stamp unchanged.")
            return

        if not _should_stamp_forward(script, current, target, applied):
            print(
                f"Alembic stamp sync: current={current}, detected={target}; no change."
            )
            return

        conn.execute(
            text("UPDATE alembic_version SET version_num = :target"),
            {"target": target},
        )
        conn.commit()
        print(f"Alembic stamp synced forward: {current} -> {target}")


if __name__ == "__main__":
    sync_stamp()
