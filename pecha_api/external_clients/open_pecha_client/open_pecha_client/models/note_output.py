from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.note_output_metadata_type_0 import NoteOutputMetadataType0
    from ..models.span_model import SpanModel


T = TypeVar("T", bound="NoteOutput")


@_attrs_define
class NoteOutput:
    """
    Attributes:
        id (str): Note ID
        span (SpanModel):
        text (str): The note content
        metadata (None | NoteOutputMetadataType0 | Unset): Optional annotation metadata
    """

    id: str
    span: SpanModel
    text: str
    metadata: None | NoteOutputMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.note_output_metadata_type_0 import NoteOutputMetadataType0

        id = self.id

        span = self.span.to_dict()

        text = self.text

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, NoteOutputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "span": span,
                "text": text,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.note_output_metadata_type_0 import NoteOutputMetadataType0
        from ..models.span_model import SpanModel

        d = dict(src_dict)
        id = d.pop("id")

        span = SpanModel.from_dict(d.pop("span"))

        text = d.pop("text")

        def _parse_metadata(data: object) -> None | NoteOutputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = NoteOutputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | NoteOutputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        note_output = cls(
            id=id,
            span=span,
            text=text,
            metadata=metadata,
        )

        note_output.additional_properties = d
        return note_output

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
