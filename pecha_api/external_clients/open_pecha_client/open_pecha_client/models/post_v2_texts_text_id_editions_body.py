from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_0 import (
        PostV2TextsTextIdEditionsBodyAnnotationItemType0,
    )
    from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_1 import (
        PostV2TextsTextIdEditionsBodyAnnotationItemType1,
    )
    from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_2 import (
        PostV2TextsTextIdEditionsBodyAnnotationItemType2,
    )
    from ..models.post_v2_texts_text_id_editions_body_bibliography_annotation_item import (
        PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem,
    )
    from ..models.post_v2_texts_text_id_editions_body_metadata import PostV2TextsTextIdEditionsBodyMetadata


T = TypeVar("T", bound="PostV2TextsTextIdEditionsBody")


@_attrs_define
class PostV2TextsTextIdEditionsBody:
    """
    Attributes:
        metadata (PostV2TextsTextIdEditionsBodyMetadata):
        content (str): The text content
        annotation (list[PostV2TextsTextIdEditionsBodyAnnotationItemType0 |
            PostV2TextsTextIdEditionsBodyAnnotationItemType1 | PostV2TextsTextIdEditionsBodyAnnotationItemType2] | Unset):
            Segmentation or pagination or bibliography annotation segments
        bibliography_annotation (list[PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem] | Unset): Bibliography
            annotation segments with bibliography type
    """

    metadata: PostV2TextsTextIdEditionsBodyMetadata
    content: str
    annotation: (
        list[
            PostV2TextsTextIdEditionsBodyAnnotationItemType0
            | PostV2TextsTextIdEditionsBodyAnnotationItemType1
            | PostV2TextsTextIdEditionsBodyAnnotationItemType2
        ]
        | Unset
    ) = UNSET
    bibliography_annotation: list[PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_0 import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType0,
        )
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_1 import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType1,
        )

        metadata = self.metadata.to_dict()

        content = self.content

        annotation: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.annotation, Unset):
            annotation = []
            for annotation_item_data in self.annotation:
                annotation_item: dict[str, Any]
                if isinstance(annotation_item_data, PostV2TextsTextIdEditionsBodyAnnotationItemType0):
                    annotation_item = annotation_item_data.to_dict()
                elif isinstance(annotation_item_data, PostV2TextsTextIdEditionsBodyAnnotationItemType1):
                    annotation_item = annotation_item_data.to_dict()
                else:
                    annotation_item = annotation_item_data.to_dict()

                annotation.append(annotation_item)

        bibliography_annotation: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.bibliography_annotation, Unset):
            bibliography_annotation = []
            for bibliography_annotation_item_data in self.bibliography_annotation:
                bibliography_annotation_item = bibliography_annotation_item_data.to_dict()
                bibliography_annotation.append(bibliography_annotation_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "metadata": metadata,
                "content": content,
            }
        )
        if annotation is not UNSET:
            field_dict["annotation"] = annotation
        if bibliography_annotation is not UNSET:
            field_dict["bibliography_annotation"] = bibliography_annotation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_0 import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType0,
        )
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_1 import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType1,
        )
        from ..models.post_v2_texts_text_id_editions_body_annotation_item_type_2 import (
            PostV2TextsTextIdEditionsBodyAnnotationItemType2,
        )
        from ..models.post_v2_texts_text_id_editions_body_bibliography_annotation_item import (
            PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem,
        )
        from ..models.post_v2_texts_text_id_editions_body_metadata import PostV2TextsTextIdEditionsBodyMetadata

        d = dict(src_dict)
        metadata = PostV2TextsTextIdEditionsBodyMetadata.from_dict(d.pop("metadata"))

        content = d.pop("content")

        _annotation = d.pop("annotation", UNSET)
        annotation: (
            list[
                PostV2TextsTextIdEditionsBodyAnnotationItemType0
                | PostV2TextsTextIdEditionsBodyAnnotationItemType1
                | PostV2TextsTextIdEditionsBodyAnnotationItemType2
            ]
            | Unset
        ) = UNSET
        if _annotation is not UNSET:
            annotation = []
            for annotation_item_data in _annotation:

                def _parse_annotation_item(
                    data: object,
                ) -> (
                    PostV2TextsTextIdEditionsBodyAnnotationItemType0
                    | PostV2TextsTextIdEditionsBodyAnnotationItemType1
                    | PostV2TextsTextIdEditionsBodyAnnotationItemType2
                ):
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        annotation_item_type_0 = PostV2TextsTextIdEditionsBodyAnnotationItemType0.from_dict(data)

                        return annotation_item_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        annotation_item_type_1 = PostV2TextsTextIdEditionsBodyAnnotationItemType1.from_dict(data)

                        return annotation_item_type_1
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    annotation_item_type_2 = PostV2TextsTextIdEditionsBodyAnnotationItemType2.from_dict(data)

                    return annotation_item_type_2

                annotation_item = _parse_annotation_item(annotation_item_data)

                annotation.append(annotation_item)

        _bibliography_annotation = d.pop("bibliography_annotation", UNSET)
        bibliography_annotation: list[PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem] | Unset = UNSET
        if _bibliography_annotation is not UNSET:
            bibliography_annotation = []
            for bibliography_annotation_item_data in _bibliography_annotation:
                bibliography_annotation_item = PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem.from_dict(
                    bibliography_annotation_item_data
                )

                bibliography_annotation.append(bibliography_annotation_item)

        post_v2_texts_text_id_editions_body = cls(
            metadata=metadata,
            content=content,
            annotation=annotation,
            bibliography_annotation=bibliography_annotation,
        )

        post_v2_texts_text_id_editions_body.additional_properties = d
        return post_v2_texts_text_id_editions_body

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
