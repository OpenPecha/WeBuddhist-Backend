from typing import List, Optional, TypeVar, Union

T = TypeVar("T")


def format_metadata_response(
    metadata_list: List[T],
    language: Optional[str],
) -> Union[T, List[T], None]:
    if language:
        return metadata_list[0] if metadata_list else None
    return metadata_list
