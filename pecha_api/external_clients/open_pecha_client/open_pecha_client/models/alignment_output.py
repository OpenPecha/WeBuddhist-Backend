from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.aligned_segment import AlignedSegment
    from ..models.alignment_output_metadata_type_0 import AlignmentOutputMetadataType0
    from ..models.segment_output import SegmentOutput


T = TypeVar("T", bound="AlignmentOutput")


@_attrs_define
class AlignmentOutput:
    """
    Attributes:
        id (str): Alignment annotation ID
        target_id (str): ID of the target manifestation
        target_segments (list[SegmentOutput]): Segments from the target manifestation
        aligned_segments (list[AlignedSegment]): Aligned segments with their alignment indices
        metadata (AlignmentOutputMetadataType0 | None | Unset): Optional annotation metadata
    """

    id: str
    target_id: str
    target_segments: list[SegmentOutput]
    aligned_segments: list[AlignedSegment]
    metadata: AlignmentOutputMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.alignment_output_metadata_type_0 import AlignmentOutputMetadataType0

        id = self.id

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
        elif isinstance(self.metadata, AlignmentOutputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
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
        from ..models.alignment_output_metadata_type_0 import AlignmentOutputMetadataType0
        from ..models.segment_output import SegmentOutput

        d = dict(src_dict)
        id = d.pop("id")

        target_id = d.pop("target_id")

        target_segments = []
        _target_segments = d.pop("target_segments")
        for target_segments_item_data in _target_segments:
            target_segments_item = SegmentOutput.from_dict(target_segments_item_data)

            target_segments.append(target_segments_item)

        aligned_segments = []
        _aligned_segments = d.pop("aligned_segments")
        for aligned_segments_item_data in _aligned_segments:
            aligned_segments_item = AlignedSegment.from_dict(aligned_segments_item_data)

            aligned_segments.append(aligned_segments_item)

        def _parse_metadata(data: object) -> AlignmentOutputMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = AlignmentOutputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AlignmentOutputMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        alignment_output = cls(
            id=id,
            target_id=target_id,
            target_segments=target_segments,
            aligned_segments=aligned_segments,
            metadata=metadata,
        )

        alignment_output.additional_properties = d
        return alignment_output

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
