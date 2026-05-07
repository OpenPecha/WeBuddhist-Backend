from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_1_span import (
        PostV2TextsTextIdEditionsBodyAnnotationItemType1Span,
    )


T = TypeVar("T", bound="PostV2TextsTextIdEditionsBodyAnnotationItemType1")


@_attrs_define
class PostV2TextsTextIdEditionsBodyAnnotationItemType1:
    """Pagination annotation (for DIPLOMATIC manifestations)

    Attributes:
        span (PostV2TextsTextIdEditionsBodyAnnotationItemType1Span):
        reference (str): Page/folio reference for the span
    """

    span: PostV2TextsTextIdEditionsBodyAnnotationItemType1Span
    reference: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        span = self.span.to_dict()

        reference = self.reference

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span": span,
                "reference": reference,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_1_span import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType1Span,
        )

        d = dict(src_dict)
        span = PostV2TextsTextIdEditionsBodyAnnotationItemType1Span.from_dict(d.pop("span"))

        reference = d.pop("reference")

        post_v2_texts_text_id_editions_body_annotation_item_type_1 = cls(
            span=span,
            reference=reference,
        )

        post_v2_texts_text_id_editions_body_annotation_item_type_1.additional_properties = d
        return post_v2_texts_text_id_editions_body_annotation_item_type_1

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
