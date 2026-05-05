from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.manifestation_type import ManifestationType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manifestation_input_alt_incipit_titles_type_0_item import ManifestationInputAltIncipitTitlesType0Item
    from ..models.manifestation_input_incipit_title_type_0 import ManifestationInputIncipitTitleType0


T = TypeVar("T", bound="ManifestationInput")


@_attrs_define
class ManifestationInput:
    """
    Attributes:
        type_ (ManifestationType): Type of manifestation/edition
        bdrc (None | str | Unset): BDRC identifier (required for diplomatic, forbidden for critical)
        wiki (None | str | Unset): Wikidata identifier
        source (None | str | Unset): Source of the manifestation
        colophon (None | str | Unset): Colophon text
        incipit_title (ManifestationInputIncipitTitleType0 | None | Unset): Localized incipit title
        alt_incipit_titles (list[ManifestationInputAltIncipitTitlesType0Item] | None | Unset): Alternative incipit
            titles
    """

    type_: ManifestationType
    bdrc: None | str | Unset = UNSET
    wiki: None | str | Unset = UNSET
    source: None | str | Unset = UNSET
    colophon: None | str | Unset = UNSET
    incipit_title: ManifestationInputIncipitTitleType0 | None | Unset = UNSET
    alt_incipit_titles: list[ManifestationInputAltIncipitTitlesType0Item] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.manifestation_input_incipit_title_type_0 import ManifestationInputIncipitTitleType0

        type_ = self.type_.value

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

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        else:
            source = self.source

        colophon: None | str | Unset
        if isinstance(self.colophon, Unset):
            colophon = UNSET
        else:
            colophon = self.colophon

        incipit_title: dict[str, Any] | None | Unset
        if isinstance(self.incipit_title, Unset):
            incipit_title = UNSET
        elif isinstance(self.incipit_title, ManifestationInputIncipitTitleType0):
            incipit_title = self.incipit_title.to_dict()
        else:
            incipit_title = self.incipit_title

        alt_incipit_titles: list[dict[str, Any]] | None | Unset
        if isinstance(self.alt_incipit_titles, Unset):
            alt_incipit_titles = UNSET
        elif isinstance(self.alt_incipit_titles, list):
            alt_incipit_titles = []
            for alt_incipit_titles_type_0_item_data in self.alt_incipit_titles:
                alt_incipit_titles_type_0_item = alt_incipit_titles_type_0_item_data.to_dict()
                alt_incipit_titles.append(alt_incipit_titles_type_0_item)

        else:
            alt_incipit_titles = self.alt_incipit_titles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if bdrc is not UNSET:
            field_dict["bdrc"] = bdrc
        if wiki is not UNSET:
            field_dict["wiki"] = wiki
        if source is not UNSET:
            field_dict["source"] = source
        if colophon is not UNSET:
            field_dict["colophon"] = colophon
        if incipit_title is not UNSET:
            field_dict["incipit_title"] = incipit_title
        if alt_incipit_titles is not UNSET:
            field_dict["alt_incipit_titles"] = alt_incipit_titles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manifestation_input_alt_incipit_titles_type_0_item import (
            ManifestationInputAltIncipitTitlesType0Item,
        )
        from ..models.manifestation_input_incipit_title_type_0 import ManifestationInputIncipitTitleType0

        d = dict(src_dict)
        type_ = ManifestationType(d.pop("type"))

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

        def _parse_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        def _parse_colophon(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        colophon = _parse_colophon(d.pop("colophon", UNSET))

        def _parse_incipit_title(data: object) -> ManifestationInputIncipitTitleType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                incipit_title_type_0 = ManifestationInputIncipitTitleType0.from_dict(data)

                return incipit_title_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ManifestationInputIncipitTitleType0 | None | Unset, data)

        incipit_title = _parse_incipit_title(d.pop("incipit_title", UNSET))

        def _parse_alt_incipit_titles(data: object) -> list[ManifestationInputAltIncipitTitlesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alt_incipit_titles_type_0 = []
                _alt_incipit_titles_type_0 = data
                for alt_incipit_titles_type_0_item_data in _alt_incipit_titles_type_0:
                    alt_incipit_titles_type_0_item = ManifestationInputAltIncipitTitlesType0Item.from_dict(
                        alt_incipit_titles_type_0_item_data
                    )

                    alt_incipit_titles_type_0.append(alt_incipit_titles_type_0_item)

                return alt_incipit_titles_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ManifestationInputAltIncipitTitlesType0Item] | None | Unset, data)

        alt_incipit_titles = _parse_alt_incipit_titles(d.pop("alt_incipit_titles", UNSET))

        manifestation_input = cls(
            type_=type_,
            bdrc=bdrc,
            wiki=wiki,
            source=source,
            colophon=colophon,
            incipit_title=incipit_title,
            alt_incipit_titles=alt_incipit_titles,
        )

        manifestation_input.additional_properties = d
        return manifestation_input

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
