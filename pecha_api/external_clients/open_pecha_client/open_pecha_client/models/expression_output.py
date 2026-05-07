from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.license_type import LicenseType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.contribution_output import ContributionOutput
    from ..models.expression_output_alt_titles_type_0_item import ExpressionOutputAltTitlesType0Item
    from ..models.expression_output_title import ExpressionOutputTitle


T = TypeVar("T", bound="ExpressionOutput")


@_attrs_define
class ExpressionOutput:
    """
    Attributes:
        id (str): Expression ID
        title (ExpressionOutputTitle):
        language (str):
        category_id (str):
        license_ (LicenseType): License type for content
        contributions (list[ContributionOutput]):
        commentaries (list[str]): IDs of commentaries on this text
        translations (list[str]): IDs of translations of this text
        editions (list[str]): IDs of editions (manifestations) of this text
        bdrc (None | str | Unset):
        wiki (None | str | Unset):
        date (None | str | Unset):
        alt_titles (list[ExpressionOutputAltTitlesType0Item] | None | Unset):
        commentary_of (None | str | Unset): ID of the text this is a commentary of
        translation_of (None | str | Unset): ID of the text this is a translation of
    """

    id: str
    title: ExpressionOutputTitle
    language: str
    category_id: str
    license_: LicenseType
    contributions: list[ContributionOutput]
    commentaries: list[str]
    translations: list[str]
    editions: list[str]
    bdrc: None | str | Unset = UNSET
    wiki: None | str | Unset = UNSET
    date: None | str | Unset = UNSET
    alt_titles: list[ExpressionOutputAltTitlesType0Item] | None | Unset = UNSET
    commentary_of: None | str | Unset = UNSET
    translation_of: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title.to_dict()

        language = self.language

        category_id = self.category_id

        license_ = self.license_.value

        contributions = []
        for contributions_item_data in self.contributions:
            contributions_item = contributions_item_data.to_dict()
            contributions.append(contributions_item)

        commentaries = self.commentaries

        translations = self.translations

        editions = self.editions

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "language": language,
                "category_id": category_id,
                "license": license_,
                "contributions": contributions,
                "commentaries": commentaries,
                "translations": translations,
                "editions": editions,
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.contribution_output import ContributionOutput
        from ..models.expression_output_alt_titles_type_0_item import ExpressionOutputAltTitlesType0Item
        from ..models.expression_output_title import ExpressionOutputTitle

        d = dict(src_dict)
        id = d.pop("id")

        title = ExpressionOutputTitle.from_dict(d.pop("title"))

        language = d.pop("language")

        category_id = d.pop("category_id")

        license_ = LicenseType(d.pop("license"))

        contributions = []
        _contributions = d.pop("contributions")
        for contributions_item_data in _contributions:
            contributions_item = ContributionOutput.from_dict(contributions_item_data)

            contributions.append(contributions_item)

        commentaries = cast(list[str], d.pop("commentaries"))

        translations = cast(list[str], d.pop("translations"))

        editions = cast(list[str], d.pop("editions"))

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

        def _parse_alt_titles(data: object) -> list[ExpressionOutputAltTitlesType0Item] | None | Unset:
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
                    alt_titles_type_0_item = ExpressionOutputAltTitlesType0Item.from_dict(alt_titles_type_0_item_data)

                    alt_titles_type_0.append(alt_titles_type_0_item)

                return alt_titles_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ExpressionOutputAltTitlesType0Item] | None | Unset, data)

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

        expression_output = cls(
            id=id,
            title=title,
            language=language,
            category_id=category_id,
            license_=license_,
            contributions=contributions,
            commentaries=commentaries,
            translations=translations,
            editions=editions,
            bdrc=bdrc,
            wiki=wiki,
            date=date,
            alt_titles=alt_titles,
            commentary_of=commentary_of,
            translation_of=translation_of,
        )

        expression_output.additional_properties = d
        return expression_output

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
