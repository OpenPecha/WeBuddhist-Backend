from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostV2CategoriesResponse422DetailsItem")


@_attrs_define
class PostV2CategoriesResponse422DetailsItem:
    """
    Attributes:
        loc (list[str] | Unset):
        msg (str | Unset):
        type_ (str | Unset):
    """

    loc: list[str] | Unset = UNSET
    msg: str | Unset = UNSET
    type_: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        loc: list[str] | Unset = UNSET
        if not isinstance(self.loc, Unset):
            loc = self.loc

        msg = self.msg

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if loc is not UNSET:
            field_dict["loc"] = loc
        if msg is not UNSET:
            field_dict["msg"] = msg
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        loc = cast(list[str], d.pop("loc", UNSET))

        msg = d.pop("msg", UNSET)

        type_ = d.pop("type", UNSET)

        post_v2_categories_response_422_details_item = cls(
            loc=loc,
            msg=msg,
            type_=type_,
        )

        post_v2_categories_response_422_details_item.additional_properties = d
        return post_v2_categories_response_422_details_item

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
