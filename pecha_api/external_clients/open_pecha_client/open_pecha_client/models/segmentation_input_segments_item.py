from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.span_model import SpanModel


T = TypeVar("T", bound="SegmentationInputSegmentsItem")


@_attrs_define
class SegmentationInputSegmentsItem:
    """
    Attributes:
        lines (list[SpanModel]):
    """

    lines: list[SpanModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        lines = []
        for lines_item_data in self.lines:
            lines_item = lines_item_data.to_dict()
            lines.append(lines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "lines": lines,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.span_model import SpanModel

        d = dict(src_dict)
        lines = []
        _lines = d.pop("lines")
        for lines_item_data in _lines:
            lines_item = SpanModel.from_dict(lines_item_data)

            lines.append(lines_item)

        segmentation_input_segments_item = cls(
            lines=lines,
        )

        segmentation_input_segments_item.additional_properties = d
        return segmentation_input_segments_item

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
