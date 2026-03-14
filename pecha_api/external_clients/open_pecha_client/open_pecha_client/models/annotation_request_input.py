from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alignment_input import AlignmentInput
    from ..models.bibliographic_metadata_input import BibliographicMetadataInput
    from ..models.note_input import NoteInput
    from ..models.pagination_input import PaginationInput
    from ..models.segmentation_input import SegmentationInput


T = TypeVar("T", bound="AnnotationRequestInput")


@_attrs_define
class AnnotationRequestInput:
    """Request body for adding annotations. Exactly one annotation type must be provided.

    Attributes:
        segmentation (SegmentationInput | Unset):
        alignment (AlignmentInput | Unset):
        pagination (PaginationInput | Unset):
        bibliographic_metadata (list[BibliographicMetadataInput] | Unset):
        durchen_notes (list[NoteInput] | Unset):
    """

    segmentation: SegmentationInput | Unset = UNSET
    alignment: AlignmentInput | Unset = UNSET
    pagination: PaginationInput | Unset = UNSET
    bibliographic_metadata: list[BibliographicMetadataInput] | Unset = UNSET
    durchen_notes: list[NoteInput] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        segmentation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.segmentation, Unset):
            segmentation = self.segmentation.to_dict()

        alignment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.alignment, Unset):
            alignment = self.alignment.to_dict()

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        bibliographic_metadata: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.bibliographic_metadata, Unset):
            bibliographic_metadata = []
            for bibliographic_metadata_item_data in self.bibliographic_metadata:
                bibliographic_metadata_item = bibliographic_metadata_item_data.to_dict()
                bibliographic_metadata.append(bibliographic_metadata_item)

        durchen_notes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.durchen_notes, Unset):
            durchen_notes = []
            for durchen_notes_item_data in self.durchen_notes:
                durchen_notes_item = durchen_notes_item_data.to_dict()
                durchen_notes.append(durchen_notes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if segmentation is not UNSET:
            field_dict["segmentation"] = segmentation
        if alignment is not UNSET:
            field_dict["alignment"] = alignment
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if bibliographic_metadata is not UNSET:
            field_dict["bibliographic_metadata"] = bibliographic_metadata
        if durchen_notes is not UNSET:
            field_dict["durchen_notes"] = durchen_notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alignment_input import AlignmentInput
        from ..models.bibliographic_metadata_input import BibliographicMetadataInput
        from ..models.note_input import NoteInput
        from ..models.pagination_input import PaginationInput
        from ..models.segmentation_input import SegmentationInput

        d = dict(src_dict)
        _segmentation = d.pop("segmentation", UNSET)
        segmentation: SegmentationInput | Unset
        if isinstance(_segmentation, Unset):
            segmentation = UNSET
        else:
            segmentation = SegmentationInput.from_dict(_segmentation)

        _alignment = d.pop("alignment", UNSET)
        alignment: AlignmentInput | Unset
        if isinstance(_alignment, Unset):
            alignment = UNSET
        else:
            alignment = AlignmentInput.from_dict(_alignment)

        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationInput | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationInput.from_dict(_pagination)

        _bibliographic_metadata = d.pop("bibliographic_metadata", UNSET)
        bibliographic_metadata: list[BibliographicMetadataInput] | Unset = UNSET
        if _bibliographic_metadata is not UNSET:
            bibliographic_metadata = []
            for bibliographic_metadata_item_data in _bibliographic_metadata:
                bibliographic_metadata_item = BibliographicMetadataInput.from_dict(bibliographic_metadata_item_data)

                bibliographic_metadata.append(bibliographic_metadata_item)

        _durchen_notes = d.pop("durchen_notes", UNSET)
        durchen_notes: list[NoteInput] | Unset = UNSET
        if _durchen_notes is not UNSET:
            durchen_notes = []
            for durchen_notes_item_data in _durchen_notes:
                durchen_notes_item = NoteInput.from_dict(durchen_notes_item_data)

                durchen_notes.append(durchen_notes_item)

        annotation_request_input = cls(
            segmentation=segmentation,
            alignment=alignment,
            pagination=pagination,
            bibliographic_metadata=bibliographic_metadata,
            durchen_notes=durchen_notes,
        )

        annotation_request_input.additional_properties = d
        return annotation_request_input

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
