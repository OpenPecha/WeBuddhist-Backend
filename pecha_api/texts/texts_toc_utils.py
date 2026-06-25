from typing import Dict, Iterator, List, Optional, Tuple

from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_response_models import Section, TableOfContent


def section_contains_segment(sections: List[Section], segment_id: str) -> bool:
    for section in sections:
        for segment in section.segments:
            if segment.segment_id == segment_id:
                return True
        if section.sections and section_contains_segment(section.sections, segment_id):
            return True
    return False


def find_first_segment_in_sections(sections: List[Section]) -> Optional[str]:
    for section in sections:
        if section.segments:
            return section.segments[0].segment_id
        if section.sections:
            segment_id = find_first_segment_in_sections(section.sections)
            if segment_id:
                return segment_id
    return None


def get_first_segment_ids_by_text_ids(
    table_of_contents_by_text_id: Dict[str, List[TableOfContent]],
) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for text_id, table_of_contents in table_of_contents_by_text_id.items():
        for table_of_content in table_of_contents:
            segment_id = find_first_segment_in_sections(table_of_content.sections)
            if segment_id:
                result[text_id] = segment_id
                break
    return result


def iter_segment_positions(table_of_content: TableOfContent) -> Iterator[Tuple[str, int]]:
    position = 1

    def walk_section(section: Section) -> Iterator[Tuple[str, int]]:
        nonlocal position
        for segment in section.segments:
            yield segment.segment_id, position
            position += 1
        if section.sections:
            for subsection in section.sections:
                yield from walk_section(subsection)

    for section in table_of_content.sections:
        yield from walk_section(section)


def get_segment_page(
    table_of_content: TableOfContent,
    segment_id: str,
    direction: PaginationDirection,
    size: int,
) -> Tuple[int, int, Dict[str, int]]:
    """
    Resolve pagination without materializing every segment id in memory.
    Returns (total_segments, current_segment_position, page_segment_id_to_position).
    """
    total_segments = 0
    anchor_position = 0

    for seg_id, position in iter_segment_positions(table_of_content):
        total_segments = position
        if seg_id == segment_id:
            anchor_position = position

    if anchor_position == 0:
        anchor_position = 1

    anchor_index = anchor_position - 1
    if direction == PaginationDirection.NEXT:
        page_start = anchor_index
        page_end = min(anchor_index + size, total_segments)
    else:
        page_start = max(0, anchor_index - size + 1)
        page_end = anchor_index + 1

    page_start_pos = page_start + 1
    page_end_pos = page_end

    page_segments: Dict[str, int] = {}
    for seg_id, position in iter_segment_positions(table_of_content):
        if page_start_pos <= position <= page_end_pos:
            page_segments[seg_id] = position
        if position > page_end_pos:
            break

    return total_segments, anchor_position, page_segments
