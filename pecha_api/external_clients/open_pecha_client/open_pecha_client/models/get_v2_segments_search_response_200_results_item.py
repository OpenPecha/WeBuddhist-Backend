from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.get_v2_segments_search_response_200_results_item_entity import (
        GetV2SegmentsSearchResponse200ResultsItemEntity,
    )


T = TypeVar("T", bound="GetV2SegmentsSearchResponse200ResultsItem")


@_attrs_define
class GetV2SegmentsSearchResponse200ResultsItem:
    """
    Attributes:
        id (str): Search segmentation segment ID
        distance (float): Search distance/score
        entity (GetV2SegmentsSearchResponse200ResultsItemEntity): Additional entity data from search. Contains 'text'
            field when return_text=true
        segmentation_ids (list[str]): List of overlapping segmentation annotation segment IDs
    """

    id: str
    distance: float
    entity: GetV2SegmentsSearchResponse200ResultsItemEntity
    segmentation_ids: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        distance = self.distance

        entity = self.entity.to_dict()

        segmentation_ids = self.segmentation_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "distance": distance,
                "entity": entity,
                "segmentation_ids": segmentation_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_v2_segments_search_response_200_results_item_entity import (
            GetV2SegmentsSearchResponse200ResultsItemEntity,
        )

        d = dict(src_dict)
        id = d.pop("id")

        distance = d.pop("distance")

        entity = GetV2SegmentsSearchResponse200ResultsItemEntity.from_dict(d.pop("entity"))

        segmentation_ids = cast(list[str], d.pop("segmentation_ids"))

        get_v2_segments_search_response_200_results_item = cls(
            id=id,
            distance=distance,
            entity=entity,
            segmentation_ids=segmentation_ids,
        )

        get_v2_segments_search_response_200_results_item.additional_properties = d
        return get_v2_segments_search_response_200_results_item

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
