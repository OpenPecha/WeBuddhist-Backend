from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pagination_output_metadata_type_0 import PaginationOutputMetadataType0
    from ..models.volume_model import VolumeModel


T = TypeVar("T", bound="PaginationOutput")


@_attrs_define
class PaginationOutput:
    """
    Attributes:
        id (str): Pagination annotation ID
        volume (VolumeModel):
        metadata (None | PaginationOutputMetadataType0 | Unset): Optional annotation metadata
    """

    id: str
    volume: VolumeModel
    metadata: None | PaginationOutputMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pagination_output_metadata_type_0 import PaginationOutputMetadataType0

        id = self.id

        volume = self.volume.to_dict()

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, PaginationOutputMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "volume": volume,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pagination_output_metadata_type_0 import PaginationOutputMetadataType0
        from ..models.volume_model import VolumeModel

        d = dict(src_dict)
        id = d.pop("id")

        volume = VolumeModel.from_dict(d.pop("volume"))

        def _parse_metadata(data: object) -> None | PaginationOutputMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = PaginationOutputMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PaginationOutputMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        pagination_output = cls(
            id=id,
            volume=volume,
            metadata=metadata,
        )

        pagination_output.additional_properties = d
        return pagination_output

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
