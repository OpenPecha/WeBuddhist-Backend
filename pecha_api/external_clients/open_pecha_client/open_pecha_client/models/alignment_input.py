from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aligned_segment import AlignedSegment
    from ..models.alignment_input_metadata_type_0 import AlignmentInputMetadataType0
    from ..models.alignment_input_target_segments_item import AlignmentInputTargetSegmentsItem


T = TypeVar("T", bound="AlignmentInput")


@_attrs_define
class AlignmentInput:
    """
    Attributes:
        target_id (str): ID of the target manifestation
        target_segments (list[AlignmentInputTargetSegmentsItem]):
        aligned_segments (list[AlignedSegment]):
        metadata (AlignmentInputMetadataType0 | None | Unset):
    """

    target_id: str
    target_segments: list[AlignmentInputTargetSegmentsItem]
    aligned_segments: list[AlignedSegment]
    metadata: AlignmentInputMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alignment_input_metadata_type_0 import AlignmentInputMetadataType0

        target_id = self.target_id

        target_segments = []
        for target_segments_item_data in self.target_segments:
            target_segments_item = target_segments_item_data.to_dict()
            target_segments.append(target_segments_item)

        aligned_segments = []
        for aligned_segments_item_data in self.aligned_segments:
            aligned_segments_item = aligned_segments_item_data.to_dict()
            aligned_segments.append(aligned_segments_item)

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, AlignmentInputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "target_id": target_id,
                "target_segments": target_segments,
                "aligned_segments": aligned_segments,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.aligned_segment import AlignedSegment
        from ..models.alignment_input_metadata_type_0 import AlignmentInputMetadataType0
        from ..models.alignment_input_target_segments_item import AlignmentInputTargetSegmentsItem

        d = dict(src_dict)
        target_id = d.pop("target_id")

        target_segments = []
        _target_segments = d.pop("target_segments")
        for target_segments_item_data in _target_segments:
            target_segments_item = AlignmentInputTargetSegmentsItem.from_dict(target_segments_item_data)

            target_segments.append(target_segments_item)

        aligned_segments = []
        _aligned_segments = d.pop("aligned_segments")
        for aligned_segments_item_data in _aligned_segments:
            aligned_segments_item = AlignedSegment.from_dict(aligned_segments_item_data)

            aligned_segments.append(aligned_segments_item)

        def _parse_metadata(data: object) -> AlignmentInputMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = AlignmentInputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AlignmentInputMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        alignment_input = cls(
            target_id=target_id,
            target_segments=target_segments,
            aligned_segments=aligned_segments,
            metadata=metadata,
        )

        alignment_input.additional_properties = d
        return alignment_input

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
