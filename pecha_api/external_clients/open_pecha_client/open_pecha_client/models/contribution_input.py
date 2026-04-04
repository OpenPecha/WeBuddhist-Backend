from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.contribution_input_role import ContributionInputRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="ContributionInput")


@_attrs_define
class ContributionInput:
    """Human or AI contribution. Must provide either person_id OR person_bdrc_id for human contributions, or ai_id for AI
    contributions.

        Attributes:
            role (ContributionInputRole):
            person_id (str | Unset): Person ID (for human contributions)
            person_bdrc_id (str | Unset): Person BDRC ID (for human contributions)
            ai_id (str | Unset): AI model identifier (for AI contributions)
    """

    role: ContributionInputRole
    person_id: str | Unset = UNSET
    person_bdrc_id: str | Unset = UNSET
    ai_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role = self.role.value

        person_id = self.person_id

        person_bdrc_id = self.person_bdrc_id

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
        if ai_id is not UNSET:
            field_dict["ai_id"] = ai_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        role = ContributionInputRole(d.pop("role"))

        person_id = d.pop("person_id", UNSET)

        person_bdrc_id = d.pop("person_bdrc_id", UNSET)

        ai_id = d.pop("ai_id", UNSET)

        contribution_input = cls(
            role=role,
            person_id=person_id,
            person_bdrc_id=person_bdrc_id,
            ai_id=ai_id,
        )

        contribution_input.additional_properties = d
        return contribution_input

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
