from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.post_v2_persons_response_422_details_item import PostV2PersonsResponse422DetailsItem


T = TypeVar("T", bound="PostV2PersonsResponse422")


@_attrs_define
class PostV2PersonsResponse422:
    """
    Attributes:
        error (str):
        details (list[PostV2PersonsResponse422DetailsItem]):
    """

    error: str
    details: list[PostV2PersonsResponse422DetailsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        error = self.error

        details = []
        for details_item_data in self.details:
            details_item = details_item_data.to_dict()
            details.append(details_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "error": error,
                "details": details,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v2_persons_response_422_details_item import PostV2PersonsResponse422DetailsItem

        d = dict(src_dict)
        error = d.pop("error")

        details = []
        _details = d.pop("details")
        for details_item_data in _details:
            details_item = PostV2PersonsResponse422DetailsItem.from_dict(details_item_data)

            details.append(details_item)

        post_v2_persons_response_422 = cls(
            error=error,
            details=details,
        )

        post_v2_persons_response_422.additional_properties = d
        return post_v2_persons_response_422

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
