from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.text_operation_type import TextOperationType
from ..types import UNSET, Unset

T = TypeVar("T", bound="TextOperation")


@_attrs_define
class TextOperation:
    """
    Attributes:
        type_ (TextOperationType): The type of text operation
        position (int | Unset): Position for INSERT operation (required for insert)
        start (int | Unset): Start position for DELETE/REPLACE operations (required for delete/replace)
        end (int | Unset): End position for DELETE/REPLACE operations (required for delete/replace)
        text (str | Unset): Text for INSERT/REPLACE operations (required for insert/replace)
    """

    type_: TextOperationType
    position: int | Unset = UNSET
    start: int | Unset = UNSET
    end: int | Unset = UNSET
    text: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        position = self.position

        start = self.start

        end = self.end

        text = self.text

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if position is not UNSET:
            field_dict["position"] = position
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if text is not UNSET:
            field_dict["text"] = text

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = TextOperationType(d.pop("type"))

        position = d.pop("position", UNSET)

        start = d.pop("start", UNSET)

        end = d.pop("end", UNSET)

        text = d.pop("text", UNSET)

        text_operation = cls(
            type_=type_,
            position=position,
            start=start,
            end=end,
            text=text,
        )

        text_operation.additional_properties = d
        return text_operation

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
