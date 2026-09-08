import io
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from pymongo.errors import DuplicateKeyError
from starlette import status

from pecha_api.texts.text_audio_models import (
    TextAudioOtrContentResponse,
    TextAudioOtrResponse,
    TextAudioResponse,
    TextAudioSegmentsResponse,
    TextSegmentContent,
    UpdateTextAudioNameRequest,
)
from pecha_api.texts.audio_transcoder import TranscodedAudio
from pecha_api.texts.text_audio_service import (
    INVALID_OTR_DETAIL,
    delete_text_audio,
    delete_text_audio_otr,
    get_required_audio,
    get_required_text,
    get_text_audio_otr_content,
    get_text_audio_otrs,
    get_text_audios,
    get_text_segments_in_order,
    parse_otr_content,
    to_text_audio_response,
    update_text_audio_name,
    upload_text_audio,
    upload_text_audio_otr,
    validate_otr_file,
    validate_text_audio_file,
)
from pecha_api.texts.texts_response_models import (
    Section,
    TableOfContentType,
    TextSegment,
)

SERVICE = "pecha_api.texts.text_audio_service"

VALID_TOKEN = "valid_token"
TEXT_ID = "text-123"
TEXT_TITLE = "Heart Sutra"
AUTHOR_EMAIL = "author@example.com"
BUCKET_NAME = "test-bucket"
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024
MAX_OTR_FILE_SIZE = 5 * 1024 * 1024
GENERATED_UUID = "11111111-1111-1111-1111-111111111111"
NEW_AUDIO_KEY = f"audio/texts/{GENERATED_UUID}.mp3"
EXISTING_AUDIO_KEY = "audio/texts/existing-key.mp3"
AUDIO_ID = "64b000000000000000000001"
OTR_ID = "64b000000000000000000002"
OTR_CONTENT = {"text": "<p>transcript</p>", "media": "", "media-time": ""}
MP3_BYTES = b"converted mp3 bytes"


def _upload_file(
    filename: str = "chant.mp3",
    content_type: str = "audio/mpeg",
    size: int = 2 * 1024 * 1024,
    content: bytes = b"fake audio bytes",
) -> MagicMock:
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = content_type
    file.size = size
    file.file = io.BytesIO(content)
    return file


def _otr_file(
    filename: str = "228.otr",
    content: bytes = json.dumps(OTR_CONTENT).encode(),
    size: int = 1024,
) -> MagicMock:
    file = MagicMock(spec=UploadFile)
    file.filename = filename
    file.content_type = "application/json"
    file.size = size
    file.read = AsyncMock(return_value=content)
    return file


def _find_chain(items=None):
    chain = MagicMock()
    chain.sort.return_value = chain
    chain.to_list = AsyncMock(return_value=list(items or []))
    chain.delete = AsyncMock()
    return chain


@pytest.fixture
def text_audio_model():
    """A stand-in for the Beanie document, which cannot be built without a live collection."""

    class StubTextAudio:
        text_id = "text_id"
        instances = []

        def __init__(self, **fields):
            self.id = AUDIO_ID
            self.pending_cleanup_keys = []
            for name, value in fields.items():
                setattr(self, name, value)
            self.insert = AsyncMock()
            self.save = AsyncMock()
            self.delete = AsyncMock()
            StubTextAudio.instances.append(self)

    StubTextAudio.get = AsyncMock(return_value=None)
    StubTextAudio.find = MagicMock(return_value=_find_chain())
    return StubTextAudio


@pytest.fixture
def text_audio_otr_model():
    class StubTextAudioOtr:
        audio_id = "audio_id"
        instances = []

        def __init__(self, **fields):
            self.id = OTR_ID
            for name, value in fields.items():
                setattr(self, name, value)
            self.insert = AsyncMock()
            self.delete = AsyncMock()
            StubTextAudioOtr.instances.append(self)

    StubTextAudioOtr.get = AsyncMock(return_value=None)
    StubTextAudioOtr.find = MagicMock(return_value=_find_chain())
    return StubTextAudioOtr


def _existing_audio(
    model,
    audio_key: str = EXISTING_AUDIO_KEY,
    pending_cleanup_keys=None,
    text_id: str = TEXT_ID,
    name: Optional[str] = None,
):
    return model(
        text_id=text_id,
        text_title=TEXT_TITLE,
        audio_key=audio_key,
        file_name="old.mp3",
        name=name,
        mime_type="audio/mpeg",
        file_size_bytes=1024,
        duration_ms=60000,
        created_by=AUTHOR_EMAIL,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        pending_cleanup_keys=pending_cleanup_keys or [],
    )


def _existing_otr(
    model,
    name: str = "228",
    audio_id: str = AUDIO_ID,
    parsed_text: str = "transcript",
    spans: Optional[list] = None,
):
    return model(
        audio_id=audio_id,
        text_id=TEXT_ID,
        name=name,
        file_name=f"{name}.otr",
        content=dict(OTR_CONTENT),
        parsed_text=parsed_text,
        spans=spans if spans is not None else [],
        created_by=AUTHOR_EMAIL,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def audio_env(text_audio_model, text_audio_otr_model):
    config = {"AWS_BUCKET_NAME": BUCKET_NAME}
    int_config = {
        "MAX_AUDIO_FILE_SIZE": MAX_AUDIO_FILE_SIZE,
        "MAX_OTR_FILE_SIZE": MAX_OTR_FILE_SIZE,
    }

    with patch(f"{SERVICE}.validate_cms_author_details") as validate_author, \
         patch(f"{SERVICE}.get", side_effect=config.get), \
         patch(f"{SERVICE}.get_int", side_effect=int_config.get), \
         patch(f"{SERVICE}.upload_bytes") as upload, \
         patch(
             f"{SERVICE}.transcode_to_mp3",
             return_value=TranscodedAudio(content=MP3_BYTES, duration_ms=10580),
         ) as transcode, \
         patch(f"{SERVICE}.delete_file") as delete, \
         patch(f"{SERVICE}.generate_presigned_access_url") as presigned_url, \
         patch(f"{SERVICE}.get_text_by_id_from_openpecha", new_callable=AsyncMock) as get_text, \
         patch(f"{SERVICE}.TextAudio", text_audio_model), \
         patch(f"{SERVICE}.TextAudioOtr", text_audio_otr_model), \
         patch(f"{SERVICE}.uuid.uuid4", return_value=GENERATED_UUID):
        validate_author.return_value = MagicMock(email=AUTHOR_EMAIL)
        get_text.return_value = MagicMock(title=TEXT_TITLE)
        upload.side_effect = lambda **kwargs: kwargs["s3_key"]
        presigned_url.side_effect = lambda bucket_name, s3_key: f"https://cdn.test/{s3_key}"

        yield SimpleNamespace(
            validate_author=validate_author,
            upload=upload,
            transcode=transcode,
            delete=delete,
            presigned_url=presigned_url,
            get_text=get_text,
            model=text_audio_model,
            otr_model=text_audio_otr_model,
        )


class TestValidateTextAudioFile:
    @pytest.mark.parametrize("extension", [".mp3", ".m4a", ".wav", ".aac", ".ogg"])
    def test_supported_extensions_are_returned(self, audio_env, extension):
        assert validate_text_audio_file(_upload_file(filename=f"chant{extension}")) == extension

    def test_extension_check_is_case_insensitive(self, audio_env):
        assert validate_text_audio_file(_upload_file(filename="CHANT.MP3")) == ".mp3"

    def test_unsupported_extension_is_rejected(self, audio_env):
        file = _upload_file(filename="notes.pdf")

        with pytest.raises(HTTPException) as exc:
            validate_text_audio_file(file)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported audio file" in exc.value.detail

    def test_missing_filename_is_rejected(self, audio_env):
        file = _upload_file(filename=None)

        with pytest.raises(HTTPException) as exc:
            validate_text_audio_file(file)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_oversized_file_is_rejected(self, audio_env):
        file = _upload_file(size=MAX_AUDIO_FILE_SIZE + 1)

        with pytest.raises(HTTPException) as exc:
            validate_text_audio_file(file)

        assert exc.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_file_exactly_at_the_size_limit_is_accepted(self, audio_env):
        assert validate_text_audio_file(_upload_file(size=MAX_AUDIO_FILE_SIZE)) == ".mp3"

    def test_unknown_size_is_accepted(self, audio_env):
        assert validate_text_audio_file(_upload_file(size=None)) == ".mp3"


class TestValidateOtrFile:
    @pytest.mark.parametrize("filename", ["228.otr", "228.json", "228.OTR"])
    def test_supported_extensions_are_accepted(self, audio_env, filename):
        assert validate_otr_file(_otr_file(filename=filename)) is None

    def test_unsupported_extension_is_rejected(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            validate_otr_file(_otr_file(filename="notes.txt"))

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == INVALID_OTR_DETAIL

    def test_oversized_file_is_rejected(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            validate_otr_file(_otr_file(size=MAX_OTR_FILE_SIZE + 1))

        assert exc.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class TestParseOtrContent:
    def test_json_object_is_returned(self):
        assert parse_otr_content(json.dumps(OTR_CONTENT).encode()) == OTR_CONTENT

    @pytest.mark.parametrize(
        "raw",
        [b"not json at all", b'"just a string"', b"[1, 2, 3]", b"null", b"\xff\xfe"],
    )
    def test_invalid_content_is_rejected(self, raw):
        with pytest.raises(HTTPException) as exc:
            parse_otr_content(raw)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == INVALID_OTR_DETAIL


class TestToTextAudioResponse:
    def test_document_is_mapped_with_a_presigned_url(self, audio_env):
        audio = _existing_audio(audio_env.model, name="Morning session")

        response = to_text_audio_response(audio)

        assert isinstance(response, TextAudioResponse)
        assert response.id == AUDIO_ID
        assert response.text_id == TEXT_ID
        assert response.text_title == TEXT_TITLE
        assert response.audio_key == EXISTING_AUDIO_KEY
        assert response.audio_url == f"https://cdn.test/{EXISTING_AUDIO_KEY}"
        assert response.name == "Morning session"
        assert response.file_name == "old.mp3"
        assert response.mime_type == "audio/mpeg"
        assert response.file_size_bytes == 1024
        assert response.duration_ms == 60000
        audio_env.presigned_url.assert_called_once_with(
            bucket_name=BUCKET_NAME,
            s3_key=EXISTING_AUDIO_KEY,
        )

    def test_missing_name_falls_back_to_file_name(self, audio_env):
        """Documents written before the name field existed have name=None;
        the response must still surface a usable display name."""
        audio = _existing_audio(audio_env.model, name=None)

        response = to_text_audio_response(audio)

        assert response.name == "old.mp3"


class TestGetRequiredText:
    @pytest.mark.asyncio
    async def test_existing_text_is_returned(self, audio_env):
        text = await get_required_text(text_id=TEXT_ID)

        assert text.title == TEXT_TITLE
        audio_env.get_text.assert_awaited_once_with(text_id=TEXT_ID)

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )

        with pytest.raises(HTTPException) as exc:
            await get_required_text(text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetRequiredAudio:
    @pytest.mark.asyncio
    async def test_matching_audio_is_returned(self, audio_env):
        existing = _existing_audio(audio_env.model)
        audio_env.model.get.return_value = existing

        assert await get_required_audio(text_id=TEXT_ID, audio_id=AUDIO_ID) is existing

    @pytest.mark.asyncio
    async def test_audio_of_another_text_raises_not_found(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(
            audio_env.model, text_id="other-text"
        )

        with pytest.raises(HTTPException) as exc:
            await get_required_audio(text_id=TEXT_ID, audio_id=AUDIO_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_unknown_audio_raises_not_found(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await get_required_audio(text_id=TEXT_ID, audio_id=AUDIO_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_malformed_audio_id_raises_not_found_without_a_lookup(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await get_required_audio(text_id=TEXT_ID, audio_id="not-an-object-id")

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.model.get.assert_not_awaited()


class TestGetTextAudios:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_audio_is_stored(self, audio_env):
        assert await get_text_audios(token=VALID_TOKEN, text_id=TEXT_ID) == []
        audio_env.validate_author.assert_called_once_with(token=VALID_TOKEN)

    @pytest.mark.asyncio
    async def test_returns_stored_audios(self, audio_env):
        audio_env.model.find.return_value = _find_chain(
            [_existing_audio(audio_env.model)]
        )

        responses = await get_text_audios(token=VALID_TOKEN, text_id=TEXT_ID)

        assert len(responses) == 1
        assert responses[0].id == AUDIO_ID
        assert responses[0].audio_key == EXISTING_AUDIO_KEY
        assert responses[0].audio_url == f"https://cdn.test/{EXISTING_AUDIO_KEY}"

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )

        with pytest.raises(HTTPException) as exc:
            await get_text_audios(token=VALID_TOKEN, text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_author_validation_failure_is_propagated(self, audio_env):
        audio_env.validate_author.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Author is not active",
        )

        with pytest.raises(HTTPException) as exc:
            await get_text_audios(token="invalid_token", text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def _table_of_content(sections, toc_type=TableOfContentType.TEXT):
    return SimpleNamespace(type=toc_type, sections=sections)


class TestGetTextSegmentsInOrder:
    @pytest.mark.asyncio
    async def test_returns_segments_sorted_into_reading_order(self, audio_env):
        sections = [
            Section(
                id="sec-2",
                title="Two",
                section_number=2,
                segments=[TextSegment(segment_id="seg-3", segment_number=1)],
            ),
            Section(
                id="sec-1",
                title="One",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg-2", segment_number=2),
                    TextSegment(segment_id="seg-1", segment_number=1),
                ],
            ),
        ]
        with patch(f"{SERVICE}.TableOfContent") as mock_toc, patch(
            f"{SERVICE}.Segment"
        ) as mock_segment:
            mock_toc.get_table_of_contents_by_text_id = AsyncMock(
                return_value=[_table_of_content(sections)]
            )
            mock_segment.get_segment_contents_by_ids = AsyncMock(
                return_value={
                    "seg-1": (TEXT_ID, "first"),
                    "seg-2": (TEXT_ID, "second"),
                    "seg-3": (TEXT_ID, "third"),
                }
            )

            response = await get_text_segments_in_order(
                token=VALID_TOKEN, text_id=TEXT_ID
            )

        assert response == TextAudioSegmentsResponse(
            text_id=TEXT_ID,
            segments=[
                TextSegmentContent(segment_id="seg-1", content="first"),
                TextSegmentContent(segment_id="seg-2", content="second"),
                TextSegmentContent(segment_id="seg-3", content="third"),
            ],
        )

    @pytest.mark.asyncio
    async def test_sheet_tables_of_content_are_skipped(self, audio_env):
        text_section = [
            Section(
                id="sec-1",
                title="One",
                section_number=1,
                segments=[TextSegment(segment_id="seg-1", segment_number=1)],
            )
        ]
        sheet_section = [
            Section(
                id="sec-9",
                title="Sheet",
                section_number=1,
                segments=[TextSegment(segment_id="seg-9", segment_number=1)],
            )
        ]
        with patch(f"{SERVICE}.TableOfContent") as mock_toc, patch(
            f"{SERVICE}.Segment"
        ) as mock_segment:
            mock_toc.get_table_of_contents_by_text_id = AsyncMock(
                return_value=[
                    _table_of_content(sheet_section, toc_type=TableOfContentType.SHEET),
                    _table_of_content(text_section, toc_type=TableOfContentType.TEXT),
                ]
            )
            mock_segment.get_segment_contents_by_ids = AsyncMock(
                return_value={"seg-1": (TEXT_ID, "only the text content")}
            )

            response = await get_text_segments_in_order(
                token=VALID_TOKEN, text_id=TEXT_ID
            )

        mock_segment.get_segment_contents_by_ids.assert_awaited_once_with(
            segment_ids=["seg-1"]
        )
        assert response.segments == [
            TextSegmentContent(segment_id="seg-1", content="only the text content")
        ]

    @pytest.mark.asyncio
    async def test_refs_missing_content_are_dropped(self, audio_env):
        sections = [
            Section(
                id="sec-1",
                title="One",
                section_number=1,
                segments=[
                    TextSegment(segment_id="seg-1", segment_number=1),
                    TextSegment(segment_id="seg-missing", segment_number=2),
                ],
            )
        ]
        with patch(f"{SERVICE}.TableOfContent") as mock_toc, patch(
            f"{SERVICE}.Segment"
        ) as mock_segment:
            mock_toc.get_table_of_contents_by_text_id = AsyncMock(
                return_value=[_table_of_content(sections)]
            )
            mock_segment.get_segment_contents_by_ids = AsyncMock(
                return_value={"seg-1": (TEXT_ID, "first")}
            )

            response = await get_text_segments_in_order(
                token=VALID_TOKEN, text_id=TEXT_ID
            )

        assert response.segments == [
            TextSegmentContent(segment_id="seg-1", content="first")
        ]

    @pytest.mark.asyncio
    async def test_no_table_of_content_yields_no_segments(self, audio_env):
        with patch(f"{SERVICE}.TableOfContent") as mock_toc, patch(
            f"{SERVICE}.Segment"
        ) as mock_segment:
            mock_toc.get_table_of_contents_by_text_id = AsyncMock(return_value=[])
            mock_segment.get_segment_contents_by_ids = AsyncMock(return_value={})

            response = await get_text_segments_in_order(
                token=VALID_TOKEN, text_id=TEXT_ID
            )

        assert response == TextAudioSegmentsResponse(text_id=TEXT_ID, segments=[])
        mock_segment.get_segment_contents_by_ids.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )

        with pytest.raises(HTTPException) as exc:
            await get_text_segments_in_order(token=VALID_TOKEN, text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


class TestUploadTextAudio:
    @pytest.mark.asyncio
    async def test_upload_stores_the_converted_mp3(self, audio_env):
        file = _upload_file()

        response = await upload_text_audio(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            file=file,
            duration_ms=90000,
        )

        audio_env.transcode.assert_called_once_with(file.file, suffix=".mp3")
        upload_kwargs = audio_env.upload.call_args.kwargs
        assert upload_kwargs["bucket_name"] == BUCKET_NAME
        assert upload_kwargs["s3_key"] == NEW_AUDIO_KEY
        assert upload_kwargs["content_type"] == "audio/mpeg"
        assert upload_kwargs["file"].getvalue() == MP3_BYTES
        audio_env.delete.assert_not_called()
        assert response.id == AUDIO_ID
        assert response.audio_key == NEW_AUDIO_KEY
        assert response.text_title == TEXT_TITLE
        assert response.name == "chant.mp3"
        assert response.file_name == "chant.mp3"
        assert response.mime_type == "audio/mpeg"
        assert response.file_size_bytes == len(MP3_BYTES)
        # The probed duration wins over the one the browser guessed.
        assert response.duration_ms == 10580
        created = audio_env.model.instances[-1]
        created.insert.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_other_formats_are_stored_as_mp3(self, audio_env):
        file = _upload_file(filename="chant.m4a", content_type="audio/x-m4a")

        response = await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        audio_env.transcode.assert_called_once_with(file.file, suffix=".m4a")
        assert audio_env.upload.call_args.kwargs["s3_key"] == NEW_AUDIO_KEY
        assert response.audio_key.endswith(".mp3")
        assert response.file_name == "chant.mp3"
        assert response.name == "chant.mp3"
        assert response.mime_type == "audio/mpeg"

    @pytest.mark.asyncio
    async def test_client_duration_is_kept_when_the_file_cannot_be_probed(self, audio_env):
        audio_env.transcode.return_value = TranscodedAudio(content=MP3_BYTES, duration_ms=None)

        response = await upload_text_audio(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            file=_upload_file(),
            duration_ms=90000,
        )

        assert response.duration_ms == 90000

    @pytest.mark.asyncio
    async def test_nothing_is_uploaded_when_the_conversion_fails(self, audio_env):
        audio_env.transcode.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not convert this audio file.",
        )

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=_upload_file())

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        audio_env.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_uploaded_object_is_removed_when_persistence_fails(self, audio_env):
        original_init = audio_env.model.__init__

        def failing_init(self, **fields):
            original_init(self, **fields)
            self.insert = AsyncMock(side_effect=RuntimeError("mongo is down"))

        file = _upload_file()

        with patch.object(audio_env.model, "__init__", failing_init):
            with pytest.raises(RuntimeError):
                await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        audio_env.delete.assert_called_once_with(NEW_AUDIO_KEY)

    @pytest.mark.asyncio
    async def test_nothing_is_uploaded_when_the_text_is_missing(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )
        file = _upload_file()

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.upload.assert_not_called()

    @pytest.mark.asyncio
    async def test_nothing_is_uploaded_when_the_file_is_invalid(self, audio_env):
        file = _upload_file(filename="notes.pdf")

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        audio_env.upload.assert_not_called()
        audio_env.transcode.assert_not_called()


class TestUpdateTextAudioName:
    @pytest.mark.asyncio
    async def test_name_is_updated_and_saved(self, audio_env):
        existing = _existing_audio(audio_env.model, name="old name")
        audio_env.model.get.return_value = existing

        response = await update_text_audio_name(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            request=UpdateTextAudioNameRequest(name="new name"),
        )

        assert response.name == "new name"
        assert existing.name == "new name"
        existing.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_surrounding_whitespace_is_trimmed(self, audio_env):
        existing = _existing_audio(audio_env.model, name="old name")
        audio_env.model.get.return_value = existing

        response = await update_text_audio_name(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            request=UpdateTextAudioNameRequest(name="  morning session  "),
        )

        assert response.name == "morning session"

    def test_blank_name_is_rejected_by_the_request_model(self):
        with pytest.raises(ValueError, match="Audio name is required"):
            UpdateTextAudioNameRequest(name="   ")

    @pytest.mark.asyncio
    async def test_unknown_audio_raises_not_found(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await update_text_audio_name(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                request=UpdateTextAudioNameRequest(name="new name"),
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )

        with pytest.raises(HTTPException) as exc:
            await update_text_audio_name(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                request=UpdateTextAudioNameRequest(name="new name"),
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_author_validation_failure_is_propagated(self, audio_env):
        audio_env.validate_author.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Author is not active",
        )

        with pytest.raises(HTTPException) as exc:
            await update_text_audio_name(
                token="invalid_token",
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                request=UpdateTextAudioNameRequest(name="new name"),
            )

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteTextAudio:
    @pytest.mark.asyncio
    async def test_stored_audio_is_removed_with_its_otrs(self, audio_env):
        existing = _existing_audio(audio_env.model)
        audio_env.model.get.return_value = existing
        otr_chain = _find_chain()
        audio_env.otr_model.find.return_value = otr_chain

        assert await delete_text_audio(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
        ) is None

        otr_chain.delete.assert_awaited_once()
        existing.delete.assert_awaited_once()
        audio_env.delete.assert_called_once_with(EXISTING_AUDIO_KEY)

    @pytest.mark.asyncio
    async def test_unknown_audio_raises_not_found(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await delete_text_audio(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Text not found."
        )

        with pytest.raises(HTTPException) as exc:
            await delete_text_audio(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_metadata_is_deleted_even_if_s3_cleanup_fails(self, audio_env):
        """Mongo deletion is the source of truth. If it succeeds, the audio no
        longer exists for the app, so a later S3 failure must only orphan
        storage - it must never leave metadata pointing at a missing file."""
        existing = _existing_audio(audio_env.model)
        audio_env.model.get.return_value = existing
        audio_env.delete.side_effect = HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 error"
        )

        assert await delete_text_audio(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
        ) is None

        existing.delete.assert_awaited_once()
        audio_env.delete.assert_called_once_with(EXISTING_AUDIO_KEY)

    @pytest.mark.asyncio
    async def test_audio_survives_when_otr_cleanup_fails(self, audio_env):
        """A failed OTR bulk delete must propagate rather than being
        swallowed - the operation must never report success while
        permanently orphaning transcript records. Nothing should be deleted:
        the audio document is untouched so the caller can safely retry."""
        existing = _existing_audio(audio_env.model)
        audio_env.model.get.return_value = existing
        otr_chain = _find_chain()
        otr_chain.delete.side_effect = RuntimeError("mongo is down")
        audio_env.otr_model.find.return_value = otr_chain

        with pytest.raises(RuntimeError):
            await delete_text_audio(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
            )

        existing.delete.assert_not_called()
        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_audio_deletion_failure_after_otr_cleanup_is_not_swallowed(self, audio_env):
        """If the audio delete itself fails after its OTRs are already gone,
        that must still surface as an error - never a false success - so the
        caller knows to retry rather than believing the delete completed."""
        existing = _existing_audio(audio_env.model)
        audio_env.model.get.return_value = existing
        existing.delete.side_effect = RuntimeError("mongo is down")
        otr_chain = _find_chain()
        audio_env.otr_model.find.return_value = otr_chain

        with pytest.raises(RuntimeError):
            await delete_text_audio(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
            )

        otr_chain.delete.assert_awaited_once()
        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_also_retries_cleanup_of_previously_pending_keys(self, audio_env):
        stale_key = "audio/texts/stale-key.mp3"
        existing = _existing_audio(audio_env.model, pending_cleanup_keys=[stale_key])
        audio_env.model.get.return_value = existing

        assert await delete_text_audio(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
        ) is None

        existing.delete.assert_awaited_once()
        audio_env.delete.assert_any_call(EXISTING_AUDIO_KEY)
        audio_env.delete.assert_any_call(stale_key)
        assert audio_env.delete.call_count == 2


class TestUploadTextAudioOtr:
    @pytest.mark.asyncio
    async def test_valid_otr_is_stored_as_json(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        response = await upload_text_audio_otr(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            file=_otr_file(),
        )

        assert isinstance(response, TextAudioOtrResponse)
        assert response.id == OTR_ID
        assert response.audio_id == AUDIO_ID
        assert response.name == "228"
        assert response.file_name == "228.otr"
        created = audio_env.otr_model.instances[-1]
        created.insert.assert_awaited_once()
        assert created.content == OTR_CONTENT
        assert created.parsed_text == "transcript"
        assert created.spans == []
        assert created.created_by == AUTHOR_EMAIL

    @pytest.mark.asyncio
    async def test_explicit_name_overrides_the_file_name(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        response = await upload_text_audio_otr(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            file=_otr_file(),
            name="  morning session  ",
        )

        assert response.name == "morning session"

    @pytest.mark.asyncio
    async def test_invalid_json_is_rejected(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio_otr(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                file=_otr_file(content=b"not json at all"),
            )

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == INVALID_OTR_DETAIL
        assert audio_env.otr_model.instances == []

    @pytest.mark.asyncio
    async def test_non_object_json_is_rejected(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio_otr(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                file=_otr_file(content=b"[1, 2, 3]"),
            )

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert audio_env.otr_model.instances == []

    @pytest.mark.asyncio
    async def test_unsupported_extension_is_rejected(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio_otr(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                file=_otr_file(filename="notes.txt"),
            )

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == INVALID_OTR_DETAIL

    @pytest.mark.asyncio
    async def test_blank_name_is_rejected(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await upload_text_audio_otr(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                file=_otr_file(),
                name="   ",
            )

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert audio_env.otr_model.instances == []

    @pytest.mark.asyncio
    async def test_duplicate_name_raises_conflict(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)
        original_init = audio_env.otr_model.__init__

        def failing_init(self, **fields):
            original_init(self, **fields)
            self.insert = AsyncMock(side_effect=DuplicateKeyError("duplicate"))

        with patch.object(audio_env.otr_model, "__init__", failing_init):
            with pytest.raises(HTTPException) as exc:
                await upload_text_audio_otr(
                    token=VALID_TOKEN,
                    text_id=TEXT_ID,
                    audio_id=AUDIO_ID,
                    file=_otr_file(),
                )

        assert exc.value.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_unknown_audio_raises_not_found(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await upload_text_audio_otr(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                file=_otr_file(),
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert audio_env.otr_model.instances == []


class TestGetTextAudioOtrs:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_otr_is_stored(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        assert await get_text_audio_otrs(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
        ) == []

    @pytest.mark.asyncio
    async def test_returns_stored_otrs(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)
        audio_env.otr_model.find.return_value = _find_chain(
            [_existing_otr(audio_env.otr_model)]
        )

        responses = await get_text_audio_otrs(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
        )

        assert len(responses) == 1
        assert responses[0].id == OTR_ID
        assert responses[0].name == "228"
        assert responses[0].audio_id == AUDIO_ID

    @pytest.mark.asyncio
    async def test_unknown_audio_raises_not_found(self, audio_env):
        with pytest.raises(HTTPException) as exc:
            await get_text_audio_otrs(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetTextAudioOtrContent:
    @pytest.mark.asyncio
    async def test_otr_content_is_returned_as_json(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)
        audio_env.otr_model.get.return_value = _existing_otr(audio_env.otr_model)

        content = await get_text_audio_otr_content(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID, otr_id=OTR_ID
        )

        assert content == TextAudioOtrContentResponse(text="transcript", spans=[])

    @pytest.mark.asyncio
    async def test_otr_of_another_audio_raises_not_found(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)
        audio_env.otr_model.get.return_value = _existing_otr(
            audio_env.otr_model, audio_id="64b000000000000000000009"
        )

        with pytest.raises(HTTPException) as exc:
            await get_text_audio_otr_content(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID, otr_id=OTR_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_unknown_otr_raises_not_found(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await get_text_audio_otr_content(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID, otr_id=OTR_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_malformed_otr_id_raises_not_found_without_a_lookup(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await get_text_audio_otr_content(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                audio_id=AUDIO_ID,
                otr_id="not-an-object-id",
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.otr_model.get.assert_not_awaited()


class TestDeleteTextAudioOtr:
    @pytest.mark.asyncio
    async def test_stored_otr_is_removed(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)
        existing = _existing_otr(audio_env.otr_model)
        audio_env.otr_model.get.return_value = existing

        assert await delete_text_audio_otr(
            token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID, otr_id=OTR_ID
        ) is None

        existing.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_otr_raises_not_found(self, audio_env):
        audio_env.model.get.return_value = _existing_audio(audio_env.model)

        with pytest.raises(HTTPException) as exc:
            await delete_text_audio_otr(
                token=VALID_TOKEN, text_id=TEXT_ID, audio_id=AUDIO_ID, otr_id=OTR_ID
            )

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
