from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.note_input_metadata_type_0 import NoteInputMetadataType0
    from ..models.span_model import SpanModel


T = TypeVar("T", bound="NoteInput")


@_attrs_define
class NoteInput:
    """
    Attributes:
        span (SpanModel):
        text (str):
        metadata (None | NoteInputMetadataType0 | Unset):
    """

    span: SpanModel
    text: str
    metadata: None | NoteInputMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.note_input_metadata_type_0 import NoteInputMetadataType0

        span = self.span.to_dict()

        text = self.text

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, NoteInputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span": span,
                "text": text,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.note_input_metadata_type_0 import NoteInputMetadataType0
        from ..models.span_model import SpanModel

        d = dict(src_dict)
        span = SpanModel.from_dict(d.pop("span"))

        text = d.pop("text")

        def _parse_metadata(data: object) -> None | NoteInputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = NoteInputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | NoteInputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        note_input = cls(
            span=span,
            text=text,
            metadata=metadata,
        )

        note_input.additional_properties = d
        return note_input

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
