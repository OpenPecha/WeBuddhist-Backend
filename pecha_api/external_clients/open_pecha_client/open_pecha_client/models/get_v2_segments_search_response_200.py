from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.get_v2_segments_search_response_200_results_item import GetV2SegmentsSearchResponse200ResultsItem


T = TypeVar("T", bound="GetV2SegmentsSearchResponse200")


@_attrs_define
class GetV2SegmentsSearchResponse200:
    """
    Attributes:
        query (str): The search query that was used
        search_type (str): The search type that was used
        results (list[GetV2SegmentsSearchResponse200ResultsItem]): List of search results with segmentation IDs
        count (int): Number of results returned
    """

    query: str
    search_type: str
    results: list[GetV2SegmentsSearchResponse200ResultsItem]
    count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        query = self.query

        search_type = self.search_type

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "query": query,
                "search_type": search_type,
                "results": results,
                "count": count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_v2_segments_search_response_200_results_item import GetV2SegmentsSearchResponse200ResultsItem

        d = dict(src_dict)
        query = d.pop("query")

        search_type = d.pop("search_type")

        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = GetV2SegmentsSearchResponse200ResultsItem.from_dict(results_item_data)

            results.append(results_item)

        count = d.pop("count")

        get_v2_segments_search_response_200 = cls(
            query=query,
            search_type=search_type,
            results=results,
            count=count,
        )

        get_v2_segments_search_response_200.additional_properties = d
        return get_v2_segments_search_response_200

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
