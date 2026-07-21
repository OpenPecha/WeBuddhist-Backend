from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_response_models import (
    Section,
    TableOfContent,
    TableOfContentType,
    TextSegment,
)
from pecha_api.texts.texts_toc_utils import get_segment_page


def _build_toc(segment_count: int) -> TableOfContent:
    return TableOfContent(
        id="toc_1",
        type=TableOfContentType.TEXT,
        text_id="text_1",
        sections=[
            Section(
                id="section_1",
                title="Section 1",
                section_number=1,
                segments=[
                    TextSegment(segment_id=f"seg_{i}", segment_number=i)
                    for i in range(1, segment_count + 1)
                ],
            )
        ],
    )


def test_get_segment_page_next_includes_has_more_flags():
    toc = _build_toc(50)

    total, position, page, has_more_up, has_more_down = get_segment_page(
        table_of_content=toc,
        segment_id="seg_1",
        direction=PaginationDirection.NEXT,
        size=20,
    )

    assert total == 50
    assert position == 1
    assert list(page.values()) == list(range(1, 21))
    assert has_more_up is False
    assert has_more_down is True


def test_get_segment_page_previous_includes_has_more_flags():
    toc = _build_toc(50)

    total, position, page, has_more_up, has_more_down = get_segment_page(
        table_of_content=toc,
        segment_id="seg_40",
        direction=PaginationDirection.PREVIOUS,
        size=20,
    )

    assert total == 50
    assert position == 40
    assert list(page.values()) == list(range(21, 41))
    assert has_more_up is True
    assert has_more_down is True


def test_get_segment_page_with_start_and_end():
    toc = _build_toc(100)

    total, position, page, has_more_up, has_more_down = get_segment_page(
        table_of_content=toc,
        segment_id="seg_1",
        direction=PaginationDirection.NEXT,
        size=20,
        start=50,
        end=60,
    )

    assert total == 100
    assert position == 60
    assert list(page.values()) == list(range(50, 61))
    assert has_more_up is True
    assert has_more_down is True


def test_get_segment_page_with_start_only_uses_size():
    toc = _build_toc(100)

    total, position, page, has_more_up, has_more_down = get_segment_page(
        table_of_content=toc,
        segment_id="seg_1",
        direction=PaginationDirection.NEXT,
        size=10,
        start=50,
    )

    assert total == 100
    assert position == 59
    assert list(page.values()) == list(range(50, 60))
    assert has_more_up is True
    assert has_more_down is True


def test_get_segment_page_clamps_end_to_total():
    toc = _build_toc(55)

    total, position, page, has_more_up, has_more_down = get_segment_page(
        table_of_content=toc,
        segment_id="seg_1",
        direction=PaginationDirection.NEXT,
        size=20,
        start=50,
        end=80,
    )

    assert total == 55
    assert position == 55
    assert list(page.values()) == list(range(50, 56))
    assert has_more_up is True
    assert has_more_down is False
