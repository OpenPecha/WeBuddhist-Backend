from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alignment_output import AlignmentOutput
    from ..models.bibliographic_metadata_output import BibliographicMetadataOutput
    from ..models.note_output import NoteOutput
    from ..models.pagination_output import PaginationOutput
    from ..models.segmentation_output import SegmentationOutput


T = TypeVar("T", bound="AnnotationRequestOutput")


@_attrs_define
class AnnotationRequestOutput:
    """Response containing annotations for an edition

    Attributes:
        segmentations (list[SegmentationOutput] | None | Unset):
        alignments (list[AlignmentOutput] | None | Unset):
        pagination (PaginationOutput | Unset):
        bibliographic_metadata (list[BibliographicMetadataOutput] | None | Unset):
        durchen_notes (list[NoteOutput] | None | Unset):
    """

    segmentations: list[SegmentationOutput] | None | Unset = UNSET
    alignments: list[AlignmentOutput] | None | Unset = UNSET
    pagination: PaginationOutput | Unset = UNSET
    bibliographic_metadata: list[BibliographicMetadataOutput] | None | Unset = UNSET
    durchen_notes: list[NoteOutput] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        segmentations: list[dict[str, Any]] | None | Unset
        if isinstance(self.segmentations, Unset):
            segmentations = UNSET
        elif isinstance(self.segmentations, list):
            segmentations = []
            for segmentations_type_0_item_data in self.segmentations:
                segmentations_type_0_item = segmentations_type_0_item_data.to_dict()
                segmentations.append(segmentations_type_0_item)

        else:
            segmentations = self.segmentations

        alignments: list[dict[str, Any]] | None | Unset
        if isinstance(self.alignments, Unset):
            alignments = UNSET
        elif isinstance(self.alignments, list):
            alignments = []
            for alignments_type_0_item_data in self.alignments:
                alignments_type_0_item = alignments_type_0_item_data.to_dict()
                alignments.append(alignments_type_0_item)

        else:
            alignments = self.alignments

        pagination: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pagination, Unset):
            pagination = self.pagination.to_dict()

        bibliographic_metadata: list[dict[str, Any]] | None | Unset
        if isinstance(self.bibliographic_metadata, Unset):
            bibliographic_metadata = UNSET
        elif isinstance(self.bibliographic_metadata, list):
            bibliographic_metadata = []
            for bibliographic_metadata_type_0_item_data in self.bibliographic_metadata:
                bibliographic_metadata_type_0_item = bibliographic_metadata_type_0_item_data.to_dict()
                bibliographic_metadata.append(bibliographic_metadata_type_0_item)

        else:
            bibliographic_metadata = self.bibliographic_metadata

        durchen_notes: list[dict[str, Any]] | None | Unset
        if isinstance(self.durchen_notes, Unset):
            durchen_notes = UNSET
        elif isinstance(self.durchen_notes, list):
            durchen_notes = []
            for durchen_notes_type_0_item_data in self.durchen_notes:
                durchen_notes_type_0_item = durchen_notes_type_0_item_data.to_dict()
                durchen_notes.append(durchen_notes_type_0_item)

        else:
            durchen_notes = self.durchen_notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if segmentations is not UNSET:
            field_dict["segmentations"] = segmentations
        if alignments is not UNSET:
            field_dict["alignments"] = alignments
        if pagination is not UNSET:
            field_dict["pagination"] = pagination
        if bibliographic_metadata is not UNSET:
            field_dict["bibliographic_metadata"] = bibliographic_metadata
        if durchen_notes is not UNSET:
            field_dict["durchen_notes"] = durchen_notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alignment_output import AlignmentOutput
        from ..models.bibliographic_metadata_output import BibliographicMetadataOutput
        from ..models.note_output import NoteOutput
        from ..models.pagination_output import PaginationOutput
        from ..models.segmentation_output import SegmentationOutput

        d = dict(src_dict)

        def _parse_segmentations(data: object) -> list[SegmentationOutput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                segmentations_type_0 = []
                _segmentations_type_0 = data
                for segmentations_type_0_item_data in _segmentations_type_0:
                    segmentations_type_0_item = SegmentationOutput.from_dict(segmentations_type_0_item_data)

                    segmentations_type_0.append(segmentations_type_0_item)

                return segmentations_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[SegmentationOutput] | None | Unset, data)

        segmentations = _parse_segmentations(d.pop("segmentations", UNSET))

        def _parse_alignments(data: object) -> list[AlignmentOutput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                alignments_type_0 = []
                _alignments_type_0 = data
                for alignments_type_0_item_data in _alignments_type_0:
                    alignments_type_0_item = AlignmentOutput.from_dict(alignments_type_0_item_data)

                    alignments_type_0.append(alignments_type_0_item)

                return alignments_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[AlignmentOutput] | None | Unset, data)

        alignments = _parse_alignments(d.pop("alignments", UNSET))

        _pagination = d.pop("pagination", UNSET)
        pagination: PaginationOutput | Unset
        if isinstance(_pagination, Unset):
            pagination = UNSET
        else:
            pagination = PaginationOutput.from_dict(_pagination)

        def _parse_bibliographic_metadata(data: object) -> list[BibliographicMetadataOutput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bibliographic_metadata_type_0 = []
                _bibliographic_metadata_type_0 = data
                for bibliographic_metadata_type_0_item_data in _bibliographic_metadata_type_0:
                    bibliographic_metadata_type_0_item = BibliographicMetadataOutput.from_dict(
                        bibliographic_metadata_type_0_item_data
                    )

                    bibliographic_metadata_type_0.append(bibliographic_metadata_type_0_item)

                return bibliographic_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[BibliographicMetadataOutput] | None | Unset, data)

        bibliographic_metadata = _parse_bibliographic_metadata(d.pop("bibliographic_metadata", UNSET))

        def _parse_durchen_notes(data: object) -> list[NoteOutput] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                durchen_notes_type_0 = []
                _durchen_notes_type_0 = data
                for durchen_notes_type_0_item_data in _durchen_notes_type_0:
                    durchen_notes_type_0_item = NoteOutput.from_dict(durchen_notes_type_0_item_data)

                    durchen_notes_type_0.append(durchen_notes_type_0_item)

                return durchen_notes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[NoteOutput] | None | Unset, data)

        durchen_notes = _parse_durchen_notes(d.pop("durchen_notes", UNSET))

        annotation_request_output = cls(
            segmentations=segmentations,
            alignments=alignments,
            pagination=pagination,
            bibliographic_metadata=bibliographic_metadata,
            durchen_notes=durchen_notes,
        )

        annotation_request_output.additional_properties = d
        return annotation_request_output

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
