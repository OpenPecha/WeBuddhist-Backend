from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.person_patch_alt_names_type_0_item import PersonPatchAltNamesType0Item
    from ..models.person_patch_name import PersonPatchName


T = TypeVar("T", bound="PersonPatch")


@_attrs_define
class PersonPatch:
    """Partial update for a person. At least one field must be provided.

    Attributes:
        bdrc (None | str | Unset): BDRC identifier
        wiki (None | str | Unset): Wikidata identifier
        name (PersonPatchName | Unset): Localized name (language code -> name)
        alt_names (list[PersonPatchAltNamesType0Item] | None | Unset): Alternative localized names
    """

    bdrc: None | str | Unset = UNSET
    wiki: None | str | Unset = UNSET
    name: PersonPatchName | Unset = UNSET
    alt_names: list[PersonPatchAltNamesType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bdrc: None | str | Unset
        if isinstance(self.bdrc, Unset):
            bdrc = UNSET
        else:
            bdrc = self.bdrc

        wiki: None | str | Unset
        if isinstance(self.wiki, Unset):
            wiki = UNSET
        else:
            wiki = self.wiki

        name: dict[str, Any] | Unset = UNSET
        if not isinstance(self.name, Unset):
            name = self.name.to_dict()

        alt_names: list[dict[str, Any]] | None | Unset
        if isinstance(self.alt_names, Unset):
            alt_names = UNSET
        elif isinstance(self.alt_names, list):
            alt_names = []
            for alt_names_type_0_item_data in self.alt_names:
                alt_names_type_0_item = alt_names_type_0_item_data.to_dict()
                alt_names.append(alt_names_type_0_item)

        else:
            alt_names = self.alt_names

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bdrc is not UNSET:
            field_dict["bdrc"] = bdrc
        if wiki is not UNSET:
            field_dict["wiki"] = wiki
        if name is not UNSET:
            field_dict["name"] = name
        if alt_names is not UNSET:
            field_dict["alt_names"] = alt_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.person_patch_alt_names_type_0_item import PersonPatchAltNamesType0Item
        from ..models.person_patch_name import PersonPatchName

        d = dict(src_dict)

        def _parse_bdrc(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        bdrc = _parse_bdrc(d.pop("bdrc", UNSET))

        def _parse_wiki(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        wiki = _parse_wiki(d.pop("wiki", UNSET))

        _name = d.pop("name", UNSET)
        name: PersonPatchName | Unset
        if isinstance(_name, Unset):
            name = UNSET
        else:
            name = PersonPatchName.from_dict(_name)

        def _parse_alt_names(data: object) -> list[PersonPatchAltNamesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alt_names_type_0 = []
                _alt_names_type_0 = data
                for alt_names_type_0_item_data in _alt_names_type_0:
                    alt_names_type_0_item = PersonPatchAltNamesType0Item.from_dict(alt_names_type_0_item_data)

                    alt_names_type_0.append(alt_names_type_0_item)

                return alt_names_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PersonPatchAltNamesType0Item] | None | Unset, data)

        alt_names = _parse_alt_names(d.pop("alt_names", UNSET))

        person_patch = cls(
            bdrc=bdrc,
            wiki=wiki,
            name=name,
            alt_names=alt_names,
        )

        person_patch.additional_properties = d
        return person_patch

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
