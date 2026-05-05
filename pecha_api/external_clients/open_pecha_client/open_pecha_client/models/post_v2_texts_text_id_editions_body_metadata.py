from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.post_v2_texts_text_id_editions_body_metadata_type import PostV2TextsTextIdEditionsBodyMetadataType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_v2_texts_text_id_editions_body_metadata_alt_incipit_titles_item import (
        PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem,
    )
    from ..models.post_v2_texts_text_id_editions_body_metadata_incipit_title import (
        PostV2TextsTextIdEditionsBodyMetadataIncipitTitle,
    )


T = TypeVar("T", bound="PostV2TextsTextIdEditionsBodyMetadata")


@_attrs_define
class PostV2TextsTextIdEditionsBodyMetadata:
    """
    Attributes:
        type_ (PostV2TextsTextIdEditionsBodyMetadataType): Type of manifestation
        source (None | str | Unset): Source identifier for the manifestation
        bdrc (str | Unset): BDRC identifier (required for diplomatic type)
        wiki (str | Unset): Wiki identifier
        colophon (str | Unset): Colophon text
        incipit_title (PostV2TextsTextIdEditionsBodyMetadataIncipitTitle | Unset): Localized incipit title
        alt_incipit_titles (list[PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem] | Unset): Alternative
            localized incipit titles
    """

    type_: PostV2TextsTextIdEditionsBodyMetadataType
    source: None | str | Unset = UNSET
    bdrc: str | Unset = UNSET
    wiki: str | Unset = UNSET
    colophon: str | Unset = UNSET
    incipit_title: PostV2TextsTextIdEditionsBodyMetadataIncipitTitle | Unset = UNSET
    alt_incipit_titles: list[PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        bdrc = self.bdrc

        wiki = self.wiki

        colophon = self.colophon

        incipit_title: dict[str, Any] | Unset = UNSET
        if not isinstance(self.incipit_title, Unset):
            incipit_title = self.incipit_title.to_dict()

        alt_incipit_titles: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.alt_incipit_titles, Unset):
            alt_incipit_titles = []
            for alt_incipit_titles_item_data in self.alt_incipit_titles:
                alt_incipit_titles_item = alt_incipit_titles_item_data.to_dict()
                alt_incipit_titles.append(alt_incipit_titles_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if source is not UNSET:
            field_dict["source"] = source
        if bdrc is not UNSET:
            field_dict["bdrc"] = bdrc
        if wiki is not UNSET:
            field_dict["wiki"] = wiki
        if colophon is not UNSET:
            field_dict["colophon"] = colophon
        if incipit_title is not UNSET:
            field_dict["incipit_title"] = incipit_title
        if alt_incipit_titles is not UNSET:
            field_dict["alt_incipit_titles"] = alt_incipit_titles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_v2_texts_text_id_editions_body_metadata_alt_incipit_titles_item import (
            PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem,
        )
        from ..models.post_v2_texts_text_id_editions_body_metadata_incipit_title import (
            PostV2TextsTextIdEditionsBodyMetadataIncipitTitle,
        )

        d = dict(src_dict)
        type_ = PostV2TextsTextIdEditionsBodyMetadataType(d.pop("type"))

        def _parse_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        bdrc = d.pop("bdrc", UNSET)

        wiki = d.pop("wiki", UNSET)

        colophon = d.pop("colophon", UNSET)

        _incipit_title = d.pop("incipit_title", UNSET)
        incipit_title: PostV2TextsTextIdEditionsBodyMetadataIncipitTitle | Unset
        if isinstance(_incipit_title, Unset):
            incipit_title = UNSET
        else:
            incipit_title = PostV2TextsTextIdEditionsBodyMetadataIncipitTitle.from_dict(_incipit_title)

        _alt_incipit_titles = d.pop("alt_incipit_titles", UNSET)
        alt_incipit_titles: list[PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem] | Unset = UNSET
        if _alt_incipit_titles is not UNSET:
            alt_incipit_titles = []
            for alt_incipit_titles_item_data in _alt_incipit_titles:
                alt_incipit_titles_item = PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem.from_dict(
                    alt_incipit_titles_item_data
                )

                alt_incipit_titles.append(alt_incipit_titles_item)

        post_v2_texts_text_id_editions_body_metadata = cls(
            type_=type_,
            source=source,
            bdrc=bdrc,
            wiki=wiki,
            colophon=colophon,
            incipit_title=incipit_title,
            alt_incipit_titles=alt_incipit_titles,
        )

        post_v2_texts_text_id_editions_body_metadata.additional_properties = d
        return post_v2_texts_text_id_editions_body_metadata

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
