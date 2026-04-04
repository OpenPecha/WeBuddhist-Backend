from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.category_output_description_type_0 import CategoryOutputDescriptionType0
    from ..models.category_output_title import CategoryOutputTitle


T = TypeVar("T", bound="CategoryOutput")


@_attrs_define
class CategoryOutput:
    """
    Attributes:
        id (str): Category ID
        title (CategoryOutputTitle): Localized category titles
        children (list[str]): List of child category IDs
        description (CategoryOutputDescriptionType0 | None | Unset): Localized category descriptions (language code to
            text mapping, optional)
        parent_id (None | str | Unset): Parent category ID (null for root categories)
    """

    id: str
    title: CategoryOutputTitle
    children: list[str]
    description: CategoryOutputDescriptionType0 | None | Unset = UNSET
    parent_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.category_output_description_type_0 import CategoryOutputDescriptionType0

        id = self.id

        title = self.title.to_dict()

        children = self.children

        description: dict[str, Any] | None | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        elif isinstance(self.description, CategoryOutputDescriptionType0):
            description = self.description.to_dict()
        else:
            description = self.description

        parent_id: None | str | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = self.parent_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "children": children,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if parent_id is not UNSET:
            field_dict["parent_id"] = parent_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.category_output_description_type_0 import CategoryOutputDescriptionType0
        from ..models.category_output_title import CategoryOutputTitle

        d = dict(src_dict)
        id = d.pop("id")

        title = CategoryOutputTitle.from_dict(d.pop("title"))

        children = cast(list[str], d.pop("children"))

        def _parse_description(data: object) -> CategoryOutputDescriptionType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                description_type_0 = CategoryOutputDescriptionType0.from_dict(data)

                return description_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CategoryOutputDescriptionType0 | None | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_parent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_id = _parse_parent_id(d.pop("parent_id", UNSET))

        category_output = cls(
            id=id,
            title=title,
            children=children,
            description=description,
            parent_id=parent_id,
        )

        category_output.additional_properties = d
        return category_output

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
