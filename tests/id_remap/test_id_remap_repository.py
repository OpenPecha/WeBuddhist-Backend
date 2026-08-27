from unittest.mock import MagicMock

from pecha_api.id_remap.id_remap_repository import remap_segment_ids


def _mock_db(rowcount: int = 0, skipped_rows=None):
    db = MagicMock()

    def execute(statement):
        result = MagicMock()
        result.rowcount = rowcount
        result.all.return_value = skipped_rows or []
        return result

    db.execute.side_effect = execute
    return db


class TestRemapSegmentIdsAcceptsPlainStrings:
    def test_non_uuid_segment_id_updates_segment_ids_and_bookmarks_only(self):
        db = _mock_db(rowcount=1)

        updated, skipped = remap_segment_ids(
            db=db,
            old_segment_id="OP001234-not-a-uuid",
            new_segment_id="OP005678-also-not-a-uuid",
        )

        # segment_ids and bookmarks(VERSE) are plain string columns and
        # always run, regardless of UUID-ness.
        assert "sub_tasks.segment_ids" in updated
        assert "bookmarks(VERSE)" in updated

        # pecha_segment_id is never touched by the remap anymore.
        assert "sub_tasks.pecha_segment_id" not in updated

        # tag_segments.segment_id is a native UUID column and can't hold a
        # non-UUID value, so it's skipped rather than erroring.
        assert "tag_segments" not in updated

    def test_uuid_segment_id_also_touches_tag_segments(self):
        db = _mock_db(rowcount=1)

        updated, skipped = remap_segment_ids(
            db=db,
            old_segment_id="11111111-1111-1111-1111-111111111111",
            new_segment_id="22222222-2222-2222-2222-222222222222",
        )

        assert "sub_tasks.segment_ids" in updated
        assert "bookmarks(VERSE)" in updated
        assert "tag_segments" in updated
        assert "sub_tasks.pecha_segment_id" not in updated

    def test_non_uuid_segment_id_does_not_raise(self):
        db = _mock_db(rowcount=0)

        # Should not raise even for a segment id shaped nothing like a UUID.
        updated, skipped = remap_segment_ids(
            db=db,
            old_segment_id="some-arbitrary-external-id",
            new_segment_id="another-arbitrary-external-id",
        )

        assert isinstance(updated, dict)
        assert isinstance(skipped, list)
