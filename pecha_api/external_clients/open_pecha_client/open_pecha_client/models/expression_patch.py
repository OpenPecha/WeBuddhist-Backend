from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.license_type import LicenseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.expression_patch_alt_titles_type_0_item import ExpressionPatchAltTitlesType0Item
    from ..models.expression_patch_title import ExpressionPatchTitle


T = TypeVar("T", bound="ExpressionPatch")


@_attrs_define
class ExpressionPatch:
    """Partial update for a text. At least one field must be provided.

    Attributes:
        bdrc (None | str | Unset): BDRC identifier
        wiki (None | str | Unset): Wikidata identifier
        date (None | str | Unset): Date of composition
        title (ExpressionPatchTitle | Unset): Localized title (language code to text mapping)
        alt_titles (list[ExpressionPatchAltTitlesType0Item] | None | Unset): Alternative localized titles
        language (None | str | Unset): Language code (BCP47 format)
        category_id (None | str | Unset): Category ID
        license_ (LicenseType | Unset): License type for content
    """

    bdrc: None | str | Unset = UNSET
    wiki: None | str | Unset = UNSET
    date: None | str | Unset = UNSET
    title: ExpressionPatchTitle | Unset = UNSET
    alt_titles: list[ExpressionPatchAltTitlesType0Item] | None | Unset = UNSET
    language: None | str | Unset = UNSET
    category_id: None | str | Unset = UNSET
    license_: LicenseType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        date: None | str | Unset
        if isinstance(self.date, Unset):
            date = UNSET
        else:
            date = self.date

        title: dict[str, Any] | Unset = UNSET
        if not isinstance(self.title, Unset):
            title = self.title.to_dict()

        alt_titles: list[dict[str, Any]] | None | Unset
        if isinstance(self.alt_titles, Unset):
            alt_titles = UNSET
        elif isinstance(self.alt_titles, list):
            alt_titles = []
            for alt_titles_type_0_item_data in self.alt_titles:
                alt_titles_type_0_item = alt_titles_type_0_item_data.to_dict()
                alt_titles.append(alt_titles_type_0_item)

        else:
            alt_titles = self.alt_titles

        language: None | str | Unset
        if isinstance(self.language, Unset):
            language = UNSET
        else:
            language = self.language

        category_id: None | str | Unset
        if isinstance(self.category_id, Unset):
            category_id = UNSET
        else:
            category_id = self.category_id

        license_: str | Unset = UNSET
        if not isinstance(self.license_, Unset):
            license_ = self.license_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if bdrc is not UNSET:
            field_dict["bdrc"] = bdrc
        if wiki is not UNSET:
            field_dict["wiki"] = wiki
        if date is not UNSET:
            field_dict["date"] = date
        if title is not UNSET:
            field_dict["title"] = title
        if alt_titles is not UNSET:
            field_dict["alt_titles"] = alt_titles
        if language is not UNSET:
            field_dict["language"] = language
        if category_id is not UNSET:
            field_dict["category_id"] = category_id
        if license_ is not UNSET:
            field_dict["license"] = license_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.expression_patch_alt_titles_type_0_item import ExpressionPatchAltTitlesType0Item
        from ..models.expression_patch_title import ExpressionPatchTitle

        d = dict(src_dict)

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

        def _parse_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        date = _parse_date(d.pop("date", UNSET))

        _title = d.pop("title", UNSET)
        title: ExpressionPatchTitle | Unset
        if isinstance(_title, Unset):
            title = UNSET
        else:
            title = ExpressionPatchTitle.from_dict(_title)

        def _parse_alt_titles(data: object) -> list[ExpressionPatchAltTitlesType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alt_titles_type_0 = []
                _alt_titles_type_0 = data
                for alt_titles_type_0_item_data in _alt_titles_type_0:
                    alt_titles_type_0_item = ExpressionPatchAltTitlesType0Item.from_dict(alt_titles_type_0_item_data)

                    alt_titles_type_0.append(alt_titles_type_0_item)

                return alt_titles_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ExpressionPatchAltTitlesType0Item] | None | Unset, data)

        alt_titles = _parse_alt_titles(d.pop("alt_titles", UNSET))

        def _parse_language(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        language = _parse_language(d.pop("language", UNSET))

        def _parse_category_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        category_id = _parse_category_id(d.pop("category_id", UNSET))

        _license_ = d.pop("license", UNSET)
        license_: LicenseType | Unset
        if isinstance(_license_, Unset):
            license_ = UNSET
        else:
            license_ = LicenseType(_license_)

        expression_patch = cls(
            bdrc=bdrc,
            wiki=wiki,
            date=date,
            title=title,
            alt_titles=alt_titles,
            language=language,
            category_id=category_id,
            license_=license_,
        )

        expression_patch.additional_properties = d
        return expression_patch

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
