from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.segmentation_input_metadata_type_0 import SegmentationInputMetadataType0
    from ..models.segmentation_input_segments_item import SegmentationInputSegmentsItem


T = TypeVar("T", bound="SegmentationInput")


@_attrs_define
class SegmentationInput:
    """
    Attributes:
        segments (list[SegmentationInputSegmentsItem]):
        metadata (None | SegmentationInputMetadataType0 | Unset):
    """

    segments: list[SegmentationInputSegmentsItem]
    metadata: None | SegmentationInputMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.segmentation_input_metadata_type_0 import SegmentationInputMetadataType0

        segments = []
        for segments_item_data in self.segments:
            segments_item = segments_item_data.to_dict()
            segments.append(segments_item)

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, SegmentationInputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "segments": segments,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.segmentation_input_metadata_type_0 import SegmentationInputMetadataType0
        from ..models.segmentation_input_segments_item import SegmentationInputSegmentsItem

        d = dict(src_dict)
        segments = []
        _segments = d.pop("segments")
        for segments_item_data in _segments:
            segments_item = SegmentationInputSegmentsItem.from_dict(segments_item_data)

            segments.append(segments_item)

        def _parse_metadata(data: object) -> None | SegmentationInputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = SegmentationInputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SegmentationInputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        segmentation_input = cls(
            segments=segments,
            metadata=metadata,
        )

        segmentation_input.additional_properties = d
        return segmentation_input

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
