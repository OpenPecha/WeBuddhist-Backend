from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v2_texts_text_id_editions_body_bibliography_annotation_item_type import (
    PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType,
)

if TYPE_CHECKING:
    from ..models.post_v2_texts_text_id_editions_body_bibliography_annotation_item_span import (
        PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan,
    )


T = TypeVar("T", bound="PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem")


@_attrs_define
class PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem:
    """
    Attributes:
        span (PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan):
        type_ (PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType): Type of bibliography annotation
    """

    span: PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan
    type_: PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        span = self.span.to_dict()

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span": span,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v2_texts_text_id_editions_body_bibliography_annotation_item_span import (
            PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan,
        )

        d = dict(src_dict)
        span = PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan.from_dict(d.pop("span"))

        type_ = PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType(d.pop("type"))

        post_v2_texts_text_id_editions_body_bibliography_annotation_item = cls(
            span=span,
            type_=type_,
        )

        post_v2_texts_text_id_editions_body_bibliography_annotation_item.additional_properties = d
        return post_v2_texts_text_id_editions_body_bibliography_annotation_item

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
