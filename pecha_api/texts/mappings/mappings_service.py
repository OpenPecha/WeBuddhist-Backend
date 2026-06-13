from typing import List, Dict, Tuple, Any
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.texts_models import Text
from pecha_api.texts.segments.segments_models import Segment, Mapping
from pecha_api.texts.segments.segments_repository import (
    check_all_segment_exists,
)
from pecha_api.texts.texts_repository import check_all_text_exists
from .mappings_repository import (
    bulk_update_segment_mappings,
    get_mapping_segments_by_ids,
)
from .mappings_response_models import (
    TextMappingRequest,
    MappingsModel,
    TextMapping,
    MappingSegmentDTO,
    MappingSegmentResponse,
)
from ..segments.segments_response_models import MappingResponse
from ...users.users_service import verify_admin_access


# Mappings Service
# ===============

async def update_segment_mapping(
    text_mapping_request: TextMappingRequest,
    token: str,
) -> MappingSegmentResponse:
    is_admin: bool = verify_admin_access(token=token)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorConstants.ADMIN_ERROR_MESSAGE,
        )

    text_id_dict, segment_id_dict = await _get_text_and_segment_ids(
        text_mapping_request=text_mapping_request
    )
    _apply_resolved_ids(text_mapping_request=text_mapping_request, text_id_dict=text_id_dict, segment_id_dict=segment_id_dict)
    await _validate_mapping_request(text_mapping_request=text_mapping_request)

    segment_dict: Dict[str, List[Mapping]] = _get_segments_from_text_mapping(
        text_mappings=text_mapping_request.text_mappings
    )
    segment_ids: List[str] = list(segment_dict.keys())
    existing_segments = await get_mapping_segments_by_ids(segment_ids=segment_ids)
    if not existing_segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid segments found to update",
        )

    segment_mappings_to_save = _build_segment_mappings_to_save(
        existing_segments=existing_segments,
        update_segment_dict=segment_dict,
    )
    if not segment_mappings_to_save:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE,
        )

    await bulk_update_segment_mappings(segment_mappings=segment_mappings_to_save)
    return _build_mapping_response(
        existing_segments=existing_segments,
        segment_mappings=segment_mappings_to_save,
    )


async def delete_segment_mapping(text_mapping_request: TextMappingRequest, token: str) -> MappingSegmentResponse:
    is_admin: bool = verify_admin_access(token=token)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorConstants.ADMIN_ERROR_MESSAGE,
        )

    segment_dict: Dict[str, List[Mapping]] = _get_segments_from_text_mapping(
        text_mappings=text_mapping_request.text_mappings
    )
    segment_ids: List[str] = list(segment_dict.keys())
    existing_segments = await get_mapping_segments_by_ids(segment_ids=segment_ids)
    if not existing_segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid segments found to update",
        )

    segment_mappings_to_save = _build_segment_mappings_to_delete(
        existing_segments=existing_segments,
        delete_segment_dict=segment_dict,
    )
    if not segment_mappings_to_save:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE,
        )

    await bulk_update_segment_mappings(segment_mappings=segment_mappings_to_save)
    return _build_mapping_response(
        existing_segments=existing_segments,
        segment_mappings=segment_mappings_to_save,
    )


async def _get_text_and_segment_ids(
    text_mapping_request: TextMappingRequest,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    segment_identifiers: List[str] = []
    text_identifiers: List[str] = []
    for text_mapping in text_mapping_request.text_mappings:
        text_identifiers.append(text_mapping.text_id)
        segment_identifiers.append(text_mapping.segment_id)
        for mapping in text_mapping.mappings:
            text_identifiers.append(mapping.parent_text_id)
            segment_identifiers.extend(mapping.segments)

    text_id_dict = await Text.resolve_text_identifier_lookup(text_identifiers=text_identifiers)
    segment_id_dict = await Segment.resolve_segment_identifier_lookup(
        segment_identifiers=segment_identifiers
    )
    return text_id_dict, segment_id_dict


def _apply_resolved_ids(
    *,
    text_mapping_request: TextMappingRequest,
    text_id_dict: Dict[str, str],
    segment_id_dict: Dict[str, str],
) -> None:
    for text_mapping in text_mapping_request.text_mappings:
        text_mapping.text_id = _resolve_identifier(
            identifier=text_mapping.text_id,
            lookup=text_id_dict,
            entity_name="Text",
        )
        text_mapping.segment_id = _resolve_identifier(
            identifier=text_mapping.segment_id,
            lookup=segment_id_dict,
            entity_name="Segment",
        )
        for mapping in text_mapping.mappings:
            mapping.parent_text_id = _resolve_identifier(
                identifier=mapping.parent_text_id,
                lookup=text_id_dict,
                entity_name="Text",
            )
            mapping.segments = [
                _resolve_identifier(
                    identifier=segment,
                    lookup=segment_id_dict,
                    entity_name="Segment",
                )
                for segment in mapping.segments
            ]


def _resolve_identifier(identifier: str, lookup: Dict[str, str], entity_name: str) -> str:
    resolved_id = lookup.get(identifier)
    if resolved_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found",
        )
    return resolved_id


def _build_segment_mappings_to_delete(
    *,
    existing_segments: List[dict],
    delete_segment_dict: Dict[str, List[Mapping]],
) -> Dict[str, List[Mapping]]:
    segment_mappings: Dict[str, List[Mapping]] = {}

    for segment in existing_segments:
        segment_id = segment["id"]
        if segment_id not in delete_segment_dict:
            continue

        mappings_to_delete = delete_segment_dict[segment_id]
        existing_mappings = _get_existing_mappings(segment)
        remaining_mappings = [
            mapping
            for mapping in existing_mappings.values()
            if (mapping.text_id, tuple(sorted(mapping.segments))) not in {
                (delete_map.text_id, tuple(sorted(delete_map.segments)))
                for delete_map in mappings_to_delete
            }
        ]
        segment_mappings[segment_id] = remaining_mappings

    return segment_mappings


async def _validate_mapping_request(text_mapping_request: TextMappingRequest) -> bool:
    text_ids: set[str] = set()
    segment_ids: set[str] = set()

    for text_mapping in text_mapping_request.text_mappings:
        text_ids.add(text_mapping.text_id)
        segment_ids.add(text_mapping.segment_id)
        parent_text_ids = [mapping.parent_text_id for mapping in text_mapping.mappings]
        if text_mapping.text_id in parent_text_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorConstants.SAME_TEXT_MAPPING_ERROR_MESSAGE,
            )
        text_ids.update(parent_text_ids)
        segment_ids.update(
            segment for mapping in text_mapping.mappings for segment in mapping.segments
        )

    text_uuid_ids = _to_uuid_list(values=text_ids, entity_name="Text")
    segment_uuid_ids = _to_uuid_list(values=segment_ids, entity_name="Segment")

    if not await check_all_text_exists(text_ids=text_uuid_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE,
        )
    if not await check_all_segment_exists(segment_ids=segment_uuid_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE,
        )
    return True


def _to_uuid_list(values: set[str], entity_name: str) -> List[UUID]:
    uuid_values: List[UUID] = []
    for value in values:
        try:
            uuid_values.append(UUID(value))
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {entity_name} ID format: {error}",
            ) from error
    return uuid_values


def _merge_segment_mappings(existing_mapping: Mapping, new_mapping: Mapping) -> Mapping:
    unique_segments = set(existing_mapping.segments + new_mapping.segments)
    existing_mapping.segments = list(unique_segments)
    return existing_mapping


def _get_existing_mappings(segment: Any) -> Dict[str, Mapping]:
    raw_mappings = segment.mapping if hasattr(segment, "mapping") else segment.get("mapping", [])
    mappings = [
        mapping if isinstance(mapping, Mapping) else Mapping(**mapping)
        for mapping in (raw_mappings or [])
    ]
    return {mapping.text_id: mapping for mapping in mappings}


def _process_new_mappings(
    new_mappings: List[Mapping],
    existing_mappings: Dict[str, Mapping],
) -> List[Mapping]:
    merged: List[Mapping] = []
    processed_text_ids: set[str] = set()

    for new_mapping in new_mappings:
        processed_text_ids.add(new_mapping.text_id)
        if new_mapping.text_id in existing_mappings:
            merged.append(
                _merge_segment_mappings(
                    existing_mappings[new_mapping.text_id],
                    new_mapping,
                )
            )
        else:
            merged.append(new_mapping)

    merged.extend(
        mapping
        for text_id, mapping in existing_mappings.items()
        if text_id not in processed_text_ids
    )
    return merged


def _build_segment_mappings_to_save(
    *,
    existing_segments: List[dict],
    update_segment_dict: Dict[str, List[Mapping]],
) -> Dict[str, List[Mapping]]:
    segment_mappings: Dict[str, List[Mapping]] = {}

    for segment in existing_segments:
        segment_id = segment["id"]
        if segment_id not in update_segment_dict:
            continue

        existing_mappings = _get_existing_mappings(segment)
        new_mappings = update_segment_dict[segment_id]
        segment_mappings[segment_id] = _process_new_mappings(new_mappings, existing_mappings)

    return segment_mappings


def _get_segments_from_text_mapping(text_mappings: List[TextMapping]) -> Dict[str, List[Mapping]]:
    segment_dict: Dict[str, List[Mapping]] = {}
    for text_mapping in text_mappings:
        mappings = [
            Mapping(text_id=mapping.parent_text_id, segments=mapping.segments)
            for mapping in text_mapping.mappings
        ]
        segment_dict[str(text_mapping.segment_id)] = mappings
    return segment_dict


def _build_mapping_response(
    *,
    existing_segments: List[dict],
    segment_mappings: Dict[str, List[Mapping]],
) -> MappingSegmentResponse:
    segment_lookup = {segment["id"]: segment for segment in existing_segments}
    segment_dtos = [
        MappingSegmentDTO(
            id=segment_id,
            pecha_segment_id=segment_lookup[segment_id].get("pecha_segment_id"),
            text_id=segment_lookup[segment_id]["text_id"],
            type=segment_lookup[segment_id]["type"],
            mapping=[MappingResponse(**mapping.model_dump()) for mapping in mappings],
        )
        for segment_id, mappings in segment_mappings.items()
        if segment_id in segment_lookup
    ]
    return MappingSegmentResponse(segments=segment_dtos)


def _construct_update_segments(segments: List[Any], update_segment_dict: Dict[str, List[Mapping]]) -> List[Any]:
    updated_segments = []

    for segment in segments:
        segment_id = str(segment.id) if hasattr(segment, "id") else segment["id"]
        if segment_id in update_segment_dict:
            existing_mappings = _get_existing_mappings(segment)
            new_mappings = update_segment_dict[segment_id]
            merged_mappings = _process_new_mappings(new_mappings, existing_mappings)
            if hasattr(segment, "mapping"):
                segment.mapping = merged_mappings
            else:
                segment["mapping"] = merged_mappings
            updated_segments.append(segment)

    return updated_segments
