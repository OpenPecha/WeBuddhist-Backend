from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.license_type import LicenseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.contribution_input import ContributionInput
    from ..models.expression_input_alt_titles_type_0_item import ExpressionInputAltTitlesType0Item
    from ..models.expression_input_title import ExpressionInputTitle


T = TypeVar("T", bound="ExpressionInput")


@_attrs_define
class ExpressionInput:
    """
    Attributes:
        title (ExpressionInputTitle): Localized title (language code to text mapping)
        language (str): Primary language code
        category_id (str): Category ID this text belongs to
        contributions (list[ContributionInput]):
        bdrc (None | str | Unset): BDRC identifier
        wiki (None | str | Unset): Wikidata identifier
        date (None | str | Unset): Date of composition
        alt_titles (list[ExpressionInputAltTitlesType0Item] | None | Unset): Alternative localized titles
        commentary_of (None | str | Unset): ID of the text this is a commentary of
        translation_of (None | str | Unset): ID of the text this is a translation of
        license_ (LicenseType | Unset): License type for content
    """

    title: ExpressionInputTitle
    language: str
    category_id: str
    contributions: list[ContributionInput]
    bdrc: None | str | Unset = UNSET
    wiki: None | str | Unset = UNSET
    date: None | str | Unset = UNSET
    alt_titles: list[ExpressionInputAltTitlesType0Item] | None | Unset = UNSET
    commentary_of: None | str | Unset = UNSET
    translation_of: None | str | Unset = UNSET
    license_: LicenseType | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title.to_dict()

        language = self.language

        category_id = self.category_id

        contributions = []
        for contributions_item_data in self.contributions:
            contributions_item = contributions_item_data.to_dict()
            contributions.append(contributions_item)

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

        commentary_of: None | str | Unset
        if isinstance(self.commentary_of, Unset):
            commentary_of = UNSET
        else:
            commentary_of = self.commentary_of

        translation_of: None | str | Unset
        if isinstance(self.translation_of, Unset):
            translation_of = UNSET
        else:
            translation_of = self.translation_of

        license_: str | Unset = UNSET
        if not isinstance(self.license_, Unset):
            license_ = self.license_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "language": language,
                "category_id": category_id,
                "contributions": contributions,
            }
        )
        if bdrc is not UNSET:
            field_dict["bdrc"] = bdrc
        if wiki is not UNSET:
            field_dict["wiki"] = wiki
        if date is not UNSET:
            field_dict["date"] = date
        if alt_titles is not UNSET:
            field_dict["alt_titles"] = alt_titles
        if commentary_of is not UNSET:
            field_dict["commentary_of"] = commentary_of
        if translation_of is not UNSET:
            field_dict["translation_of"] = translation_of
        if license_ is not UNSET:
            field_dict["license"] = license_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.contribution_input import ContributionInput
        from ..models.expression_input_alt_titles_type_0_item import ExpressionInputAltTitlesType0Item
        from ..models.expression_input_title import ExpressionInputTitle

        d = dict(src_dict)
        title = ExpressionInputTitle.from_dict(d.pop("title"))

        language = d.pop("language")

        category_id = d.pop("category_id")

        contributions = []
        _contributions = d.pop("contributions")
        for contributions_item_data in _contributions:
            contributions_item = ContributionInput.from_dict(contributions_item_data)

            contributions.append(contributions_item)

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

        def _parse_alt_titles(data: object) -> list[ExpressionInputAltTitlesType0Item] | None | Unset:
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
                    alt_titles_type_0_item = ExpressionInputAltTitlesType0Item.from_dict(alt_titles_type_0_item_data)

                    alt_titles_type_0.append(alt_titles_type_0_item)

                return alt_titles_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ExpressionInputAltTitlesType0Item] | None | Unset, data)

        alt_titles = _parse_alt_titles(d.pop("alt_titles", UNSET))

        def _parse_commentary_of(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        commentary_of = _parse_commentary_of(d.pop("commentary_of", UNSET))

        def _parse_translation_of(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        translation_of = _parse_translation_of(d.pop("translation_of", UNSET))

        _license_ = d.pop("license", UNSET)
        license_: LicenseType | Unset
        if isinstance(_license_, Unset):
            license_ = UNSET
        else:
            license_ = LicenseType(_license_)

        expression_input = cls(
            title=title,
            language=language,
            category_id=category_id,
            contributions=contributions,
            bdrc=bdrc,
            wiki=wiki,
            date=date,
            alt_titles=alt_titles,
            commentary_of=commentary_of,
            translation_of=translation_of,
            license_=license_,
        )

        expression_input.additional_properties = d
        return expression_input

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
