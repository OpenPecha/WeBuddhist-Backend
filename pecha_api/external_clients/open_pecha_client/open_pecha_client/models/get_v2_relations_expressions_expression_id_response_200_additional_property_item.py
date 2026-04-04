from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_v2_relations_expressions_expression_id_response_200_additional_property_item_direction import (
    GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection,
)
from ..models.get_v2_relations_expressions_expression_id_response_200_additional_property_item_type import (
    GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType,
)

T = TypeVar("T", bound="GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItem")


@_attrs_define
class GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItem:
    """
    Attributes:
        type_ (GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType): Relationship type
        direction (GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection): Direction relative
            to the expression
        other_id (str): Related expression ID
    """

    type_: GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType
    direction: GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection
    other_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        direction = self.direction.value

        other_id = self.other_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "direction": direction,
                "otherId": other_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType(d.pop("type"))

        direction = GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection(d.pop("direction"))

        other_id = d.pop("otherId")

        get_v2_relations_expressions_expression_id_response_200_additional_property_item = cls(
            type_=type_,
            direction=direction,
            other_id=other_id,
        )

        get_v2_relations_expressions_expression_id_response_200_additional_property_item.additional_properties = d
        return get_v2_relations_expressions_expression_id_response_200_additional_property_item

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
