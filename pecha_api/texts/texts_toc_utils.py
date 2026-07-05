from typing import Dict, Iterator, List, Optional, Tuple

from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_response_models import Section, TableOfContent

FIRST_SEGMENT_PREVIEW_COUNT = 3


def section_contains_segment(sections: List[Section], segment_id: str) -> bool:
    for section in sections:
        for segment in section.segments:
            if segment.segment_id == segment_id:
                return True
        if section.sections and section_contains_segment(section.sections, segment_id):
            return True
    return False


def find_first_segment_in_sections(sections: List[Section]) -> Optional[str]:
    refs = get_first_n_segment_refs_from_sections(sections, count=1)
    return refs[0] if refs else None


def iter_segment_refs_in_sections(sections: List[Section]):
    for section in sections:
        for segment in section.segments:
            segment_ref = segment.segment_id or segment.pecha_segment_id
            if segment_ref:
                yield segment_ref
        if section.sections:
            yield from iter_segment_refs_in_sections(section.sections)


def get_first_n_segment_refs_from_sections(
    sections: List[Section],
    *,
    count: int = FIRST_SEGMENT_PREVIEW_COUNT,
) -> List[str]:
    refs: List[str] = []
    for segment_ref in iter_segment_refs_in_sections(sections):
        refs.append(segment_ref)
        if len(refs) >= count:
            break
    return refs


def get_first_n_segment_refs_from_table_of_contents(
    table_of_contents: List[TableOfContent],
    count: int = FIRST_SEGMENT_PREVIEW_COUNT,
) -> List[str]:
    refs: List[str] = []
    for table_of_content in table_of_contents:
        for segment_ref in iter_segment_refs_in_sections(table_of_content.sections):
            refs.append(segment_ref)
            if len(refs) >= count:
                return refs
    return refs


def combine_segment_preview_contents(contents: List[str]) -> str:
    return "\n".join(
        content.strip()
        for content in contents
        if content and content.strip()
    )


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
