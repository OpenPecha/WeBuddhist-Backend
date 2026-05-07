from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.contribution_output_role import ContributionOutputRole
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.contribution_output_person_name_type_0 import ContributionOutputPersonNameType0


T = TypeVar("T", bound="ContributionOutput")


@_attrs_define
class ContributionOutput:
    """
    Attributes:
        role (ContributionOutputRole):
        person_id (None | str | Unset):
        person_bdrc_id (None | str | Unset):
        person_name (ContributionOutputPersonNameType0 | None | Unset): Localized person name (language code to name
            mapping)
        ai_id (None | str | Unset):
    """

    role: ContributionOutputRole
    person_id: None | str | Unset = UNSET
    person_bdrc_id: None | str | Unset = UNSET
    person_name: ContributionOutputPersonNameType0 | None | Unset = UNSET
    ai_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.contribution_output_person_name_type_0 import ContributionOutputPersonNameType0

        role = self.role.value

        person_id: None | str | Unset
        if isinstance(self.person_id, Unset):
            person_id = UNSET
        else:
            person_id = self.person_id

        person_bdrc_id: None | str | Unset
        if isinstance(self.person_bdrc_id, Unset):
            person_bdrc_id = UNSET
        else:
            person_bdrc_id = self.person_bdrc_id

        person_name: dict[str, Any] | None | Unset
        if isinstance(self.person_name, Unset):
            person_name = UNSET
        elif isinstance(self.person_name, ContributionOutputPersonNameType0):
            person_name = self.person_name.to_dict()
        else:
            person_name = self.person_name

        ai_id: None | str | Unset
        if isinstance(self.ai_id, Unset):
            ai_id = UNSET
        else:
            ai_id = self.ai_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "role": role,
            }
        )
        if person_id is not UNSET:
            field_dict["person_id"] = person_id
        if person_bdrc_id is not UNSET:
            field_dict["person_bdrc_id"] = person_bdrc_id
        if person_name is not UNSET:
            field_dict["person_name"] = person_name
        if ai_id is not UNSET:
            field_dict["ai_id"] = ai_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.contribution_output_person_name_type_0 import ContributionOutputPersonNameType0

        d = dict(src_dict)
        role = ContributionOutputRole(d.pop("role"))

        def _parse_person_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        person_id = _parse_person_id(d.pop("person_id", UNSET))

        def _parse_person_bdrc_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        person_bdrc_id = _parse_person_bdrc_id(d.pop("person_bdrc_id", UNSET))

        def _parse_person_name(data: object) -> ContributionOutputPersonNameType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                person_name_type_0 = ContributionOutputPersonNameType0.from_dict(data)

                return person_name_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ContributionOutputPersonNameType0 | None | Unset, data)

        person_name = _parse_person_name(d.pop("person_name", UNSET))

        def _parse_ai_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ai_id = _parse_ai_id(d.pop("ai_id", UNSET))

        contribution_output = cls(
            role=role,
            person_id=person_id,
            person_bdrc_id=person_bdrc_id,
            person_name=person_name,
            ai_id=ai_id,
        )

        contribution_output.additional_properties = d
        return contribution_output

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
