"""Contains all the data models used in inputs/outputs"""

from .aligned_segment import AlignedSegment
from .alignment_input import AlignmentInput
from .alignment_input_metadata_type_0 import AlignmentInputMetadataType0
from .alignment_input_target_segments_item import AlignmentInputTargetSegmentsItem
from .alignment_output import AlignmentOutput
from .alignment_output_metadata_type_0 import AlignmentOutputMetadataType0
from .annotation_request_input import AnnotationRequestInput
from .annotation_request_output import AnnotationRequestOutput
from .bibliographic_metadata_input import BibliographicMetadataInput
from .bibliographic_metadata_input_metadata_type_0 import BibliographicMetadataInputMetadataType0
from .bibliographic_metadata_input_type import BibliographicMetadataInputType
from .bibliographic_metadata_output import BibliographicMetadataOutput
from .bibliographic_metadata_output_metadata_type_0 import BibliographicMetadataOutputMetadataType0
from .bibliographic_metadata_output_type import BibliographicMetadataOutputType
from .category_input import CategoryInput
from .category_input_description_type_0 import CategoryInputDescriptionType0
from .category_input_title import CategoryInputTitle
from .category_output import CategoryOutput
from .category_output_description_type_0 import CategoryOutputDescriptionType0
from .category_output_title import CategoryOutputTitle
from .contribution_input import ContributionInput
from .contribution_input_role import ContributionInputRole
from .contribution_output import ContributionOutput
from .contribution_output_person_name_type_0 import ContributionOutputPersonNameType0
from .contribution_output_role import ContributionOutputRole
from .delete_v2_annotations_alignment_alignment_id_response_404 import (
    DeleteV2AnnotationsAlignmentAlignmentIdResponse404,
)
from .delete_v2_annotations_alignment_alignment_id_response_500 import (
    DeleteV2AnnotationsAlignmentAlignmentIdResponse500,
)
from .delete_v2_annotations_bibliographic_bibliographic_id_response_404 import (
    DeleteV2AnnotationsBibliographicBibliographicIdResponse404,
)
from .delete_v2_annotations_bibliographic_bibliographic_id_response_500 import (
    DeleteV2AnnotationsBibliographicBibliographicIdResponse500,
)
from .delete_v2_annotations_durchen_note_id_response_404 import DeleteV2AnnotationsDurchenNoteIdResponse404
from .delete_v2_annotations_durchen_note_id_response_500 import DeleteV2AnnotationsDurchenNoteIdResponse500
from .delete_v2_annotations_pagination_pagination_id_response_404 import (
    DeleteV2AnnotationsPaginationPaginationIdResponse404,
)
from .delete_v2_annotations_pagination_pagination_id_response_500 import (
    DeleteV2AnnotationsPaginationPaginationIdResponse500,
)
from .delete_v2_annotations_segmentation_segmentation_id_response_400 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse400,
)
from .delete_v2_annotations_segmentation_segmentation_id_response_404 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse404,
)
from .delete_v2_annotations_segmentation_segmentation_id_response_500 import (
    DeleteV2AnnotationsSegmentationSegmentationIdResponse500,
)
from .delete_v2_editions_edition_id_response_404 import DeleteV2EditionsEditionIdResponse404
from .delete_v2_editions_edition_id_response_500 import DeleteV2EditionsEditionIdResponse500
from .expression_input import ExpressionInput
from .expression_input_alt_titles_type_0_item import ExpressionInputAltTitlesType0Item
from .expression_input_title import ExpressionInputTitle
from .expression_output import ExpressionOutput
from .expression_output_alt_titles_type_0_item import ExpressionOutputAltTitlesType0Item
from .expression_output_title import ExpressionOutputTitle
from .expression_patch import ExpressionPatch
from .expression_patch_alt_titles_type_0_item import ExpressionPatchAltTitlesType0Item
from .expression_patch_title import ExpressionPatchTitle
from .get_v2_annotations_alignment_alignment_id_response_404 import GetV2AnnotationsAlignmentAlignmentIdResponse404
from .get_v2_annotations_alignment_alignment_id_response_500 import GetV2AnnotationsAlignmentAlignmentIdResponse500
from .get_v2_annotations_bibliographic_bibliographic_id_response_404 import (
    GetV2AnnotationsBibliographicBibliographicIdResponse404,
)
from .get_v2_annotations_bibliographic_bibliographic_id_response_500 import (
    GetV2AnnotationsBibliographicBibliographicIdResponse500,
)
from .get_v2_annotations_durchen_note_id_response_404 import GetV2AnnotationsDurchenNoteIdResponse404
from .get_v2_annotations_durchen_note_id_response_500 import GetV2AnnotationsDurchenNoteIdResponse500
from .get_v2_annotations_pagination_pagination_id_response_404 import GetV2AnnotationsPaginationPaginationIdResponse404
from .get_v2_annotations_pagination_pagination_id_response_500 import GetV2AnnotationsPaginationPaginationIdResponse500
from .get_v2_annotations_segmentation_segmentation_id_response_404 import (
    GetV2AnnotationsSegmentationSegmentationIdResponse404,
)
from .get_v2_annotations_segmentation_segmentation_id_response_500 import (
    GetV2AnnotationsSegmentationSegmentationIdResponse500,
)
from .get_v2_categories_response_400 import GetV2CategoriesResponse400
from .get_v2_categories_response_500 import GetV2CategoriesResponse500
from .get_v2_editions_edition_id_annotations_response_404 import GetV2EditionsEditionIdAnnotationsResponse404
from .get_v2_editions_edition_id_annotations_response_500 import GetV2EditionsEditionIdAnnotationsResponse500
from .get_v2_editions_edition_id_annotations_type_item import GetV2EditionsEditionIdAnnotationsTypeItem
from .get_v2_editions_edition_id_content_response_400 import GetV2EditionsEditionIdContentResponse400
from .get_v2_editions_edition_id_content_response_404 import GetV2EditionsEditionIdContentResponse404
from .get_v2_editions_edition_id_content_response_500 import GetV2EditionsEditionIdContentResponse500
from .get_v2_editions_edition_id_metadata_response_404 import GetV2EditionsEditionIdMetadataResponse404
from .get_v2_editions_edition_id_metadata_response_500 import GetV2EditionsEditionIdMetadataResponse500
from .get_v2_editions_edition_id_related_response_404 import GetV2EditionsEditionIdRelatedResponse404
from .get_v2_editions_edition_id_related_response_500 import GetV2EditionsEditionIdRelatedResponse500
from .get_v2_editions_edition_id_segments_related_response_400 import GetV2EditionsEditionIdSegmentsRelatedResponse400
from .get_v2_editions_edition_id_segments_related_response_404 import GetV2EditionsEditionIdSegmentsRelatedResponse404
from .get_v2_editions_edition_id_segments_related_response_422 import GetV2EditionsEditionIdSegmentsRelatedResponse422
from .get_v2_editions_edition_id_segments_related_response_422_details_item import (
    GetV2EditionsEditionIdSegmentsRelatedResponse422DetailsItem,
)
from .get_v2_editions_edition_id_segments_related_response_500 import GetV2EditionsEditionIdSegmentsRelatedResponse500
from .get_v2_languages_response_200_item import GetV2LanguagesResponse200Item
from .get_v2_languages_response_500 import GetV2LanguagesResponse500
from .get_v2_persons_person_id_response_404 import GetV2PersonsPersonIdResponse404
from .get_v2_persons_person_id_response_500 import GetV2PersonsPersonIdResponse500
from .get_v2_persons_response_500 import GetV2PersonsResponse500
from .get_v2_relations_expressions_expression_id_response_200 import GetV2RelationsExpressionsExpressionIdResponse200
from .get_v2_relations_expressions_expression_id_response_200_additional_property_item import (
    GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItem,
)
from .get_v2_relations_expressions_expression_id_response_200_additional_property_item_direction import (
    GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection,
)
from .get_v2_relations_expressions_expression_id_response_200_additional_property_item_type import (
    GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType,
)
from .get_v2_relations_expressions_expression_id_response_404 import GetV2RelationsExpressionsExpressionIdResponse404
from .get_v2_relations_expressions_expression_id_response_500 import GetV2RelationsExpressionsExpressionIdResponse500
from .get_v2_schema_openapi_response_500 import GetV2SchemaOpenapiResponse500
from .get_v2_segments_search_response_200 import GetV2SegmentsSearchResponse200
from .get_v2_segments_search_response_200_results_item import GetV2SegmentsSearchResponse200ResultsItem
from .get_v2_segments_search_response_200_results_item_entity import GetV2SegmentsSearchResponse200ResultsItemEntity
from .get_v2_segments_search_response_400 import GetV2SegmentsSearchResponse400
from .get_v2_segments_search_response_422 import GetV2SegmentsSearchResponse422
from .get_v2_segments_search_response_422_details_item import GetV2SegmentsSearchResponse422DetailsItem
from .get_v2_segments_search_response_500 import GetV2SegmentsSearchResponse500
from .get_v2_segments_search_search_type import GetV2SegmentsSearchSearchType
from .get_v2_segments_segment_id_content_response_404 import GetV2SegmentsSegmentIdContentResponse404
from .get_v2_segments_segment_id_content_response_500 import GetV2SegmentsSegmentIdContentResponse500
from .get_v2_segments_segment_id_related_response_404 import GetV2SegmentsSegmentIdRelatedResponse404
from .get_v2_segments_segment_id_related_response_500 import GetV2SegmentsSegmentIdRelatedResponse500
from .get_v2_texts_response_400 import GetV2TextsResponse400
from .get_v2_texts_response_500 import GetV2TextsResponse500
from .get_v2_texts_text_id_editions_edition_type import GetV2TextsTextIdEditionsEditionType
from .get_v2_texts_text_id_editions_response_400 import GetV2TextsTextIdEditionsResponse400
from .get_v2_texts_text_id_editions_response_404 import GetV2TextsTextIdEditionsResponse404
from .get_v2_texts_text_id_editions_response_500 import GetV2TextsTextIdEditionsResponse500
from .get_v2_texts_text_id_response_404 import GetV2TextsTextIdResponse404
from .get_v2_texts_text_id_response_500 import GetV2TextsTextIdResponse500
from .get_version_response_200 import GetVersionResponse200
from .get_version_response_500 import GetVersionResponse500
from .license_type import LicenseType
from .manifestation_input import ManifestationInput
from .manifestation_input_alt_incipit_titles_type_0_item import ManifestationInputAltIncipitTitlesType0Item
from .manifestation_input_incipit_title_type_0 import ManifestationInputIncipitTitleType0
from .manifestation_output import ManifestationOutput
from .manifestation_output_alt_incipit_titles_type_0_item import ManifestationOutputAltIncipitTitlesType0Item
from .manifestation_output_incipit_title_type_0 import ManifestationOutputIncipitTitleType0
from .manifestation_type import ManifestationType
from .note_input import NoteInput
from .note_input_metadata_type_0 import NoteInputMetadataType0
from .note_output import NoteOutput
from .note_output_metadata_type_0 import NoteOutputMetadataType0
from .page_model import PageModel
from .pagination_input import PaginationInput
from .pagination_input_metadata_type_0 import PaginationInputMetadataType0
from .pagination_output import PaginationOutput
from .pagination_output_metadata_type_0 import PaginationOutputMetadataType0
from .patch_v2_editions_edition_id_content_response_200 import PatchV2EditionsEditionIdContentResponse200
from .patch_v2_editions_edition_id_content_response_400 import PatchV2EditionsEditionIdContentResponse400
from .patch_v2_editions_edition_id_content_response_404 import PatchV2EditionsEditionIdContentResponse404
from .patch_v2_editions_edition_id_content_response_422 import PatchV2EditionsEditionIdContentResponse422
from .patch_v2_editions_edition_id_content_response_422_details_item import (
    PatchV2EditionsEditionIdContentResponse422DetailsItem,
)
from .patch_v2_editions_edition_id_content_response_500 import PatchV2EditionsEditionIdContentResponse500
from .patch_v2_persons_person_id_response_400 import PatchV2PersonsPersonIdResponse400
from .patch_v2_persons_person_id_response_404 import PatchV2PersonsPersonIdResponse404
from .patch_v2_persons_person_id_response_409 import PatchV2PersonsPersonIdResponse409
from .patch_v2_persons_person_id_response_422 import PatchV2PersonsPersonIdResponse422
from .patch_v2_persons_person_id_response_422_details_item import PatchV2PersonsPersonIdResponse422DetailsItem
from .patch_v2_persons_person_id_response_500 import PatchV2PersonsPersonIdResponse500
from .patch_v2_texts_text_id_response_400 import PatchV2TextsTextIdResponse400
from .patch_v2_texts_text_id_response_404 import PatchV2TextsTextIdResponse404
from .patch_v2_texts_text_id_response_422 import PatchV2TextsTextIdResponse422
from .patch_v2_texts_text_id_response_422_details_item import PatchV2TextsTextIdResponse422DetailsItem
from .patch_v2_texts_text_id_response_500 import PatchV2TextsTextIdResponse500
from .person_input import PersonInput
from .person_input_alt_names_type_0_item import PersonInputAltNamesType0Item
from .person_input_name import PersonInputName
from .person_output import PersonOutput
from .person_output_alt_names_type_0_item import PersonOutputAltNamesType0Item
from .person_output_name import PersonOutputName
from .person_patch import PersonPatch
from .person_patch_alt_names_type_0_item import PersonPatchAltNamesType0Item
from .person_patch_name import PersonPatchName
from .post_v2_applications_body import PostV2ApplicationsBody
from .post_v2_applications_response_201 import PostV2ApplicationsResponse201
from .post_v2_applications_response_400 import PostV2ApplicationsResponse400
from .post_v2_applications_response_422 import PostV2ApplicationsResponse422
from .post_v2_applications_response_422_details_item import PostV2ApplicationsResponse422DetailsItem
from .post_v2_applications_response_500 import PostV2ApplicationsResponse500
from .post_v2_categories_response_201 import PostV2CategoriesResponse201
from .post_v2_categories_response_400 import PostV2CategoriesResponse400
from .post_v2_categories_response_422 import PostV2CategoriesResponse422
from .post_v2_categories_response_422_details_item import PostV2CategoriesResponse422DetailsItem
from .post_v2_categories_response_500 import PostV2CategoriesResponse500
from .post_v2_editions_edition_id_annotations_response_201 import PostV2EditionsEditionIdAnnotationsResponse201
from .post_v2_editions_edition_id_annotations_response_400 import PostV2EditionsEditionIdAnnotationsResponse400
from .post_v2_editions_edition_id_annotations_response_404 import PostV2EditionsEditionIdAnnotationsResponse404
from .post_v2_editions_edition_id_annotations_response_422 import PostV2EditionsEditionIdAnnotationsResponse422
from .post_v2_editions_edition_id_annotations_response_422_details_item import (
    PostV2EditionsEditionIdAnnotationsResponse422DetailsItem,
)
from .post_v2_editions_edition_id_annotations_response_500 import PostV2EditionsEditionIdAnnotationsResponse500
from .post_v2_languages_body import PostV2LanguagesBody
from .post_v2_languages_response_201 import PostV2LanguagesResponse201
from .post_v2_languages_response_400 import PostV2LanguagesResponse400
from .post_v2_languages_response_422 import PostV2LanguagesResponse422
from .post_v2_languages_response_422_details_item import PostV2LanguagesResponse422DetailsItem
from .post_v2_languages_response_500 import PostV2LanguagesResponse500
from .post_v2_persons_response_201 import PostV2PersonsResponse201
from .post_v2_persons_response_400 import PostV2PersonsResponse400
from .post_v2_persons_response_422 import PostV2PersonsResponse422
from .post_v2_persons_response_422_details_item import PostV2PersonsResponse422DetailsItem
from .post_v2_persons_response_500 import PostV2PersonsResponse500
from .post_v2_texts_response_201 import PostV2TextsResponse201
from .post_v2_texts_response_400 import PostV2TextsResponse400
from .post_v2_texts_response_422 import PostV2TextsResponse422
from .post_v2_texts_response_422_details_item import PostV2TextsResponse422DetailsItem
from .post_v2_texts_response_500 import PostV2TextsResponse500
from .post_v2_texts_text_id_editions_body import PostV2TextsTextIdEditionsBody
from .post_v2_texts_text_id_editions_body_annotation_item_type_0 import PostV2TextsTextIdEditionsBodyAnnotationItemType0
from .post_v2_texts_text_id_editions_body_annotation_item_type_0_span import (
    PostV2TextsTextIdEditionsBodyAnnotationItemType0Span,
)
from .post_v2_texts_text_id_editions_body_annotation_item_type_1 import PostV2TextsTextIdEditionsBodyAnnotationItemType1
from .post_v2_texts_text_id_editions_body_annotation_item_type_1_span import (
    PostV2TextsTextIdEditionsBodyAnnotationItemType1Span,
)
from .post_v2_texts_text_id_editions_body_annotation_item_type_2 import PostV2TextsTextIdEditionsBodyAnnotationItemType2
from .post_v2_texts_text_id_editions_body_annotation_item_type_2_span import (
    PostV2TextsTextIdEditionsBodyAnnotationItemType2Span,
)
from .post_v2_texts_text_id_editions_body_annotation_item_type_2_type import (
    PostV2TextsTextIdEditionsBodyAnnotationItemType2Type,
)
from .post_v2_texts_text_id_editions_body_bibliography_annotation_item import (
    PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem,
)
from .post_v2_texts_text_id_editions_body_bibliography_annotation_item_span import (
    PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan,
)
from .post_v2_texts_text_id_editions_body_bibliography_annotation_item_type import (
    PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType,
)
from .post_v2_texts_text_id_editions_body_metadata import PostV2TextsTextIdEditionsBodyMetadata
from .post_v2_texts_text_id_editions_body_metadata_alt_incipit_titles_item import (
    PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem,
)
from .post_v2_texts_text_id_editions_body_metadata_incipit_title import (
    PostV2TextsTextIdEditionsBodyMetadataIncipitTitle,
)
from .post_v2_texts_text_id_editions_body_metadata_type import PostV2TextsTextIdEditionsBodyMetadataType
from .post_v2_texts_text_id_editions_response_201 import PostV2TextsTextIdEditionsResponse201
from .post_v2_texts_text_id_editions_response_400 import PostV2TextsTextIdEditionsResponse400
from .post_v2_texts_text_id_editions_response_422 import PostV2TextsTextIdEditionsResponse422
from .post_v2_texts_text_id_editions_response_422_details_item import PostV2TextsTextIdEditionsResponse422DetailsItem
from .post_v2_texts_text_id_editions_response_500 import PostV2TextsTextIdEditionsResponse500
from .segment_output import SegmentOutput
from .segmentation_input import SegmentationInput
from .segmentation_input_metadata_type_0 import SegmentationInputMetadataType0
from .segmentation_input_segments_item import SegmentationInputSegmentsItem
from .segmentation_output import SegmentationOutput
from .segmentation_output_metadata_type_0 import SegmentationOutputMetadataType0
from .span_model import SpanModel
from .text_operation import TextOperation
from .text_operation_type import TextOperationType
from .volume_model import VolumeModel
from .volume_model_metadata_type_0 import VolumeModelMetadataType0

__all__ = (
    "AlignedSegment",
    "AlignmentInput",
    "AlignmentInputMetadataType0",
    "AlignmentInputTargetSegmentsItem",
    "AlignmentOutput",
    "AlignmentOutputMetadataType0",
    "AnnotationRequestInput",
    "AnnotationRequestOutput",
    "BibliographicMetadataInput",
    "BibliographicMetadataInputMetadataType0",
    "BibliographicMetadataInputType",
    "BibliographicMetadataOutput",
    "BibliographicMetadataOutputMetadataType0",
    "BibliographicMetadataOutputType",
    "CategoryInput",
    "CategoryInputDescriptionType0",
    "CategoryInputTitle",
    "CategoryOutput",
    "CategoryOutputDescriptionType0",
    "CategoryOutputTitle",
    "ContributionInput",
    "ContributionInputRole",
    "ContributionOutput",
    "ContributionOutputPersonNameType0",
    "ContributionOutputRole",
    "DeleteV2AnnotationsAlignmentAlignmentIdResponse404",
    "DeleteV2AnnotationsAlignmentAlignmentIdResponse500",
    "DeleteV2AnnotationsBibliographicBibliographicIdResponse404",
    "DeleteV2AnnotationsBibliographicBibliographicIdResponse500",
    "DeleteV2AnnotationsDurchenNoteIdResponse404",
    "DeleteV2AnnotationsDurchenNoteIdResponse500",
    "DeleteV2AnnotationsPaginationPaginationIdResponse404",
    "DeleteV2AnnotationsPaginationPaginationIdResponse500",
    "DeleteV2AnnotationsSegmentationSegmentationIdResponse400",
    "DeleteV2AnnotationsSegmentationSegmentationIdResponse404",
    "DeleteV2AnnotationsSegmentationSegmentationIdResponse500",
    "DeleteV2EditionsEditionIdResponse404",
    "DeleteV2EditionsEditionIdResponse500",
    "ExpressionInput",
    "ExpressionInputAltTitlesType0Item",
    "ExpressionInputTitle",
    "ExpressionOutput",
    "ExpressionOutputAltTitlesType0Item",
    "ExpressionOutputTitle",
    "ExpressionPatch",
    "ExpressionPatchAltTitlesType0Item",
    "ExpressionPatchTitle",
    "GetV2AnnotationsAlignmentAlignmentIdResponse404",
    "GetV2AnnotationsAlignmentAlignmentIdResponse500",
    "GetV2AnnotationsBibliographicBibliographicIdResponse404",
    "GetV2AnnotationsBibliographicBibliographicIdResponse500",
    "GetV2AnnotationsDurchenNoteIdResponse404",
    "GetV2AnnotationsDurchenNoteIdResponse500",
    "GetV2AnnotationsPaginationPaginationIdResponse404",
    "GetV2AnnotationsPaginationPaginationIdResponse500",
    "GetV2AnnotationsSegmentationSegmentationIdResponse404",
    "GetV2AnnotationsSegmentationSegmentationIdResponse500",
    "GetV2CategoriesResponse400",
    "GetV2CategoriesResponse500",
    "GetV2EditionsEditionIdAnnotationsResponse404",
    "GetV2EditionsEditionIdAnnotationsResponse500",
    "GetV2EditionsEditionIdAnnotationsTypeItem",
    "GetV2EditionsEditionIdContentResponse400",
    "GetV2EditionsEditionIdContentResponse404",
    "GetV2EditionsEditionIdContentResponse500",
    "GetV2EditionsEditionIdMetadataResponse404",
    "GetV2EditionsEditionIdMetadataResponse500",
    "GetV2EditionsEditionIdRelatedResponse404",
    "GetV2EditionsEditionIdRelatedResponse500",
    "GetV2EditionsEditionIdSegmentsRelatedResponse400",
    "GetV2EditionsEditionIdSegmentsRelatedResponse404",
    "GetV2EditionsEditionIdSegmentsRelatedResponse422",
    "GetV2EditionsEditionIdSegmentsRelatedResponse422DetailsItem",
    "GetV2EditionsEditionIdSegmentsRelatedResponse500",
    "GetV2LanguagesResponse200Item",
    "GetV2LanguagesResponse500",
    "GetV2PersonsPersonIdResponse404",
    "GetV2PersonsPersonIdResponse500",
    "GetV2PersonsResponse500",
    "GetV2RelationsExpressionsExpressionIdResponse200",
    "GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItem",
    "GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemDirection",
    "GetV2RelationsExpressionsExpressionIdResponse200AdditionalPropertyItemType",
    "GetV2RelationsExpressionsExpressionIdResponse404",
    "GetV2RelationsExpressionsExpressionIdResponse500",
    "GetV2SchemaOpenapiResponse500",
    "GetV2SegmentsSearchResponse200",
    "GetV2SegmentsSearchResponse200ResultsItem",
    "GetV2SegmentsSearchResponse200ResultsItemEntity",
    "GetV2SegmentsSearchResponse400",
    "GetV2SegmentsSearchResponse422",
    "GetV2SegmentsSearchResponse422DetailsItem",
    "GetV2SegmentsSearchResponse500",
    "GetV2SegmentsSearchSearchType",
    "GetV2SegmentsSegmentIdContentResponse404",
    "GetV2SegmentsSegmentIdContentResponse500",
    "GetV2SegmentsSegmentIdRelatedResponse404",
    "GetV2SegmentsSegmentIdRelatedResponse500",
    "GetV2TextsResponse400",
    "GetV2TextsResponse500",
    "GetV2TextsTextIdEditionsEditionType",
    "GetV2TextsTextIdEditionsResponse400",
    "GetV2TextsTextIdEditionsResponse404",
    "GetV2TextsTextIdEditionsResponse500",
    "GetV2TextsTextIdResponse404",
    "GetV2TextsTextIdResponse500",
    "GetVersionResponse200",
    "GetVersionResponse500",
    "LicenseType",
    "ManifestationInput",
    "ManifestationInputAltIncipitTitlesType0Item",
    "ManifestationInputIncipitTitleType0",
    "ManifestationOutput",
    "ManifestationOutputAltIncipitTitlesType0Item",
    "ManifestationOutputIncipitTitleType0",
    "ManifestationType",
    "NoteInput",
    "NoteInputMetadataType0",
    "NoteOutput",
    "NoteOutputMetadataType0",
    "PageModel",
    "PaginationInput",
    "PaginationInputMetadataType0",
    "PaginationOutput",
    "PaginationOutputMetadataType0",
    "PatchV2EditionsEditionIdContentResponse200",
    "PatchV2EditionsEditionIdContentResponse400",
    "PatchV2EditionsEditionIdContentResponse404",
    "PatchV2EditionsEditionIdContentResponse422",
    "PatchV2EditionsEditionIdContentResponse422DetailsItem",
    "PatchV2EditionsEditionIdContentResponse500",
    "PatchV2PersonsPersonIdResponse400",
    "PatchV2PersonsPersonIdResponse404",
    "PatchV2PersonsPersonIdResponse409",
    "PatchV2PersonsPersonIdResponse422",
    "PatchV2PersonsPersonIdResponse422DetailsItem",
    "PatchV2PersonsPersonIdResponse500",
    "PatchV2TextsTextIdResponse400",
    "PatchV2TextsTextIdResponse404",
    "PatchV2TextsTextIdResponse422",
    "PatchV2TextsTextIdResponse422DetailsItem",
    "PatchV2TextsTextIdResponse500",
    "PersonInput",
    "PersonInputAltNamesType0Item",
    "PersonInputName",
    "PersonOutput",
    "PersonOutputAltNamesType0Item",
    "PersonOutputName",
    "PersonPatch",
    "PersonPatchAltNamesType0Item",
    "PersonPatchName",
    "PostV2ApplicationsBody",
    "PostV2ApplicationsResponse201",
    "PostV2ApplicationsResponse400",
    "PostV2ApplicationsResponse422",
    "PostV2ApplicationsResponse422DetailsItem",
    "PostV2ApplicationsResponse500",
    "PostV2CategoriesResponse201",
    "PostV2CategoriesResponse400",
    "PostV2CategoriesResponse422",
    "PostV2CategoriesResponse422DetailsItem",
    "PostV2CategoriesResponse500",
    "PostV2EditionsEditionIdAnnotationsResponse201",
    "PostV2EditionsEditionIdAnnotationsResponse400",
    "PostV2EditionsEditionIdAnnotationsResponse404",
    "PostV2EditionsEditionIdAnnotationsResponse422",
    "PostV2EditionsEditionIdAnnotationsResponse422DetailsItem",
    "PostV2EditionsEditionIdAnnotationsResponse500",
    "PostV2LanguagesBody",
    "PostV2LanguagesResponse201",
    "PostV2LanguagesResponse400",
    "PostV2LanguagesResponse422",
    "PostV2LanguagesResponse422DetailsItem",
    "PostV2LanguagesResponse500",
    "PostV2PersonsResponse201",
    "PostV2PersonsResponse400",
    "PostV2PersonsResponse422",
    "PostV2PersonsResponse422DetailsItem",
    "PostV2PersonsResponse500",
    "PostV2TextsResponse201",
    "PostV2TextsResponse400",
    "PostV2TextsResponse422",
    "PostV2TextsResponse422DetailsItem",
    "PostV2TextsResponse500",
    "PostV2TextsTextIdEditionsBody",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType0",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType0Span",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType1",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType1Span",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType2",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType2Span",
    "PostV2TextsTextIdEditionsBodyAnnotationItemType2Type",
    "PostV2TextsTextIdEditionsBodyBibliographyAnnotationItem",
    "PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemSpan",
    "PostV2TextsTextIdEditionsBodyBibliographyAnnotationItemType",
    "PostV2TextsTextIdEditionsBodyMetadata",
    "PostV2TextsTextIdEditionsBodyMetadataAltIncipitTitlesItem",
    "PostV2TextsTextIdEditionsBodyMetadataIncipitTitle",
    "PostV2TextsTextIdEditionsBodyMetadataType",
    "PostV2TextsTextIdEditionsResponse201",
    "PostV2TextsTextIdEditionsResponse400",
    "PostV2TextsTextIdEditionsResponse422",
    "PostV2TextsTextIdEditionsResponse422DetailsItem",
    "PostV2TextsTextIdEditionsResponse500",
    "SegmentationInput",
    "SegmentationInputMetadataType0",
    "SegmentationInputSegmentsItem",
    "SegmentationOutput",
    "SegmentationOutputMetadataType0",
    "SegmentOutput",
    "SpanModel",
    "TextOperation",
    "TextOperationType",
    "VolumeModel",
    "VolumeModelMetadataType0",
)
