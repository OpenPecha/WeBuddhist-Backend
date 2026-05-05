from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.page_model import PageModel
    from ..models.volume_model_metadata_type_0 import VolumeModelMetadataType0


T = TypeVar("T", bound="VolumeModel")


@_attrs_define
class VolumeModel:
    """
    Attributes:
        pages (list[PageModel]): Pages in this volume
        index (int | None | Unset): Volume index (optional)
        metadata (None | Unset | VolumeModelMetadataType0): Optional volume metadata
    """

    pages: list[PageModel]
    index: int | None | Unset = UNSET
    metadata: None | Unset | VolumeModelMetadataType0 = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.volume_model_metadata_type_0 import VolumeModelMetadataType0

        pages = []
        for pages_item_data in self.pages:
            pages_item = pages_item_data.to_dict()
            pages.append(pages_item)

        index: int | None | Unset
        if isinstance(self.index, Unset):
            index = UNSET
        else:
            index = self.index

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, VolumeModelMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pages": pages,
            }
        )
        if index is not UNSET:
            field_dict["index"] = index
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.page_model import PageModel
        from ..models.volume_model_metadata_type_0 import VolumeModelMetadataType0

        d = dict(src_dict)
        pages = []
        _pages = d.pop("pages")
        for pages_item_data in _pages:
            pages_item = PageModel.from_dict(pages_item_data)

            pages.append(pages_item)

        def _parse_index(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        index = _parse_index(d.pop("index", UNSET))

        def _parse_metadata(data: object) -> None | Unset | VolumeModelMetadataType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = VolumeModelMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | VolumeModelMetadataType0, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        volume_model = cls(
            pages=pages,
            index=index,
            metadata=metadata,
        )

        volume_model.additional_properties = d
        return volume_model

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
