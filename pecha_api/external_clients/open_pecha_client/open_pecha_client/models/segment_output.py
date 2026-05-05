from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.span_model import SpanModel


T = TypeVar("T", bound="SegmentOutput")


@_attrs_define
class SegmentOutput:
    """
    Attributes:
        id (str): Unique segment identifier
        manifestation_id (str): ID of the manifestation this segment belongs to
        text_id (str): ID of the expression (text) this segment belongs to
        lines (list[SpanModel]): Character spans that make up this segment
    """

    id: str
    manifestation_id: str
    text_id: str
    lines: list[SpanModel]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        manifestation_id = self.manifestation_id

        text_id = self.text_id

        lines = []
        for lines_item_data in self.lines:
            lines_item = lines_item_data.to_dict()
            lines.append(lines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "manifestation_id": manifestation_id,
                "text_id": text_id,
                "lines": lines,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.span_model import SpanModel

        d = dict(src_dict)
        id = d.pop("id")

        manifestation_id = d.pop("manifestation_id")

        text_id = d.pop("text_id")

        lines = []
        _lines = d.pop("lines")
        for lines_item_data in _lines:
            lines_item = SpanModel.from_dict(lines_item_data)

            lines.append(lines_item)

        segment_output = cls(
            id=id,
            manifestation_id=manifestation_id,
            text_id=text_id,
            lines=lines,
        )

        segment_output.additional_properties = d
        return segment_output

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
