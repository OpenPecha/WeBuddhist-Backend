from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bibliographic_metadata_output_type import BibliographicMetadataOutputType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bibliographic_metadata_output_metadata_type_0 import BibliographicMetadataOutputMetadataType0
    from ..models.span_model import SpanModel


T = TypeVar("T", bound="BibliographicMetadataOutput")


@_attrs_define
class BibliographicMetadataOutput:
    """
    Attributes:
        id (str): Bibliographic metadata ID
        span (SpanModel):
        type_ (BibliographicMetadataOutputType): Type of bibliographic metadata
        metadata (BibliographicMetadataOutputMetadataType0 | None | Unset): Optional annotation metadata
    """

    id: str
    span: SpanModel
    type_: BibliographicMetadataOutputType
    metadata: BibliographicMetadataOutputMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.bibliographic_metadata_output_metadata_type_0 import BibliographicMetadataOutputMetadataType0

        id = self.id

        span = self.span.to_dict()

        type_ = self.type_.value

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, BibliographicMetadataOutputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "span": span,
                "type": type_,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bibliographic_metadata_output_metadata_type_0 import BibliographicMetadataOutputMetadataType0
        from ..models.span_model import SpanModel

        d = dict(src_dict)
        id = d.pop("id")

        span = SpanModel.from_dict(d.pop("span"))

        type_ = BibliographicMetadataOutputType(d.pop("type"))

        def _parse_metadata(data: object) -> BibliographicMetadataOutputMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = BibliographicMetadataOutputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BibliographicMetadataOutputMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        bibliographic_metadata_output = cls(
            id=id,
            span=span,
            type_=type_,
            metadata=metadata,
        )

        bibliographic_metadata_output.additional_properties = d
        return bibliographic_metadata_output

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
