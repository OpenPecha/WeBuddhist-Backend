import io
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.texts.text_audio_models import TextAudioResponse
from pecha_api.texts.text_audio_service import (
    delete_text_audio,
    get_required_text,
    get_text_audio,
    to_text_audio_response,
    upload_text_audio,
    validate_text_audio_file,
)

SERVICE = "pecha_api.texts.text_audio_service"

VALID_TOKEN = "valid_token"
TEXT_ID = "text-123"
TEXT_TITLE = "Heart Sutra"
AUTHOR_EMAIL = "author@example.com"
BUCKET_NAME = "test-bucket"
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024
GENERATED_UUID = "11111111-1111-1111-1111-111111111111"
NEW_AUDIO_KEY = f"audio/texts/{GENERATED_UUID}.mp3"
EXISTING_AUDIO_KEY = "audio/texts/existing-key.mp3"


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


@pytest.fixture
def text_audio_model():
    """A stand-in for the Beanie document, which cannot be built without a live collection."""

    class StubTextAudio:
        text_id = "text_id"

        def __init__(self, **fields):
            for name, value in fields.items():
                setattr(self, name, value)
            self.insert = AsyncMock()
            self.save = AsyncMock()
            self.delete = AsyncMock()

    StubTextAudio.find_one = AsyncMock(return_value=None)
    return StubTextAudio


def _existing_audio(model, audio_key: str = EXISTING_AUDIO_KEY):
    return model(
        text_id=TEXT_ID,
        text_title=TEXT_TITLE,
        audio_key=audio_key,
        file_name="old.mp3",
        mime_type="audio/mpeg",
        file_size_bytes=1024,
        duration_ms=60000,
        created_by=AUTHOR_EMAIL,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def audio_env(text_audio_model):
    config = {"AWS_BUCKET_NAME": BUCKET_NAME}
    int_config = {"MAX_AUDIO_FILE_SIZE": MAX_AUDIO_FILE_SIZE}

    with patch(f"{SERVICE}.validate_cms_author_details") as validate_author, \
         patch(f"{SERVICE}.get", side_effect=config.get), \
         patch(f"{SERVICE}.get_int", side_effect=int_config.get), \
         patch(f"{SERVICE}.upload_file") as upload, \
         patch(f"{SERVICE}.delete_file") as delete, \
         patch(f"{SERVICE}.generate_presigned_access_url") as presigned_url, \
         patch(f"{SERVICE}.Text.get_text", new_callable=AsyncMock) as get_text, \
         patch(f"{SERVICE}.TextAudio", text_audio_model), \
         patch(f"{SERVICE}.uuid.uuid4", return_value=GENERATED_UUID):
        validate_author.return_value = MagicMock(email=AUTHOR_EMAIL)
        get_text.return_value = MagicMock(title=TEXT_TITLE)
        upload.side_effect = lambda **kwargs: kwargs["s3_key"]
        presigned_url.side_effect = lambda bucket_name, s3_key: f"https://cdn.test/{s3_key}"

        yield SimpleNamespace(
            validate_author=validate_author,
            upload=upload,
            delete=delete,
            presigned_url=presigned_url,
            get_text=get_text,
            model=text_audio_model,
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


class TestToTextAudioResponse:
    def test_document_is_mapped_with_a_presigned_url(self, audio_env):
        audio = _existing_audio(audio_env.model)

        response = to_text_audio_response(audio)

        assert isinstance(response, TextAudioResponse)
        assert response.text_id == TEXT_ID
        assert response.text_title == TEXT_TITLE
        assert response.audio_key == EXISTING_AUDIO_KEY
        assert response.audio_url == f"https://cdn.test/{EXISTING_AUDIO_KEY}"
        assert response.file_name == "old.mp3"
        assert response.mime_type == "audio/mpeg"
        assert response.file_size_bytes == 1024
        assert response.duration_ms == 60000
        audio_env.presigned_url.assert_called_once_with(
            bucket_name=BUCKET_NAME,
            s3_key=EXISTING_AUDIO_KEY,
        )


class TestGetRequiredText:
    @pytest.mark.asyncio
    async def test_existing_text_is_returned(self, audio_env):
        text = await get_required_text(text_id=TEXT_ID)

        assert text.title == TEXT_TITLE
        audio_env.get_text.assert_awaited_once_with(text_id=TEXT_ID)

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_required_text(text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetTextAudio:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_audio_is_stored(self, audio_env):
        assert await get_text_audio(token=VALID_TOKEN, text_id=TEXT_ID) is None
        audio_env.validate_author.assert_called_once_with(token=VALID_TOKEN)

    @pytest.mark.asyncio
    async def test_returns_stored_audio(self, audio_env):
        audio_env.model.find_one.return_value = _existing_audio(audio_env.model)

        response = await get_text_audio(token=VALID_TOKEN, text_id=TEXT_ID)

        assert response.audio_key == EXISTING_AUDIO_KEY
        assert response.audio_url == f"https://cdn.test/{EXISTING_AUDIO_KEY}"

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.return_value = None

        with pytest.raises(HTTPException) as exc:
            await get_text_audio(token=VALID_TOKEN, text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_author_validation_failure_is_propagated(self, audio_env):
        audio_env.validate_author.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Author is not active",
        )

        with pytest.raises(HTTPException) as exc:
            await get_text_audio(token="invalid_token", text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_403_FORBIDDEN


class TestUploadTextAudio:
    @pytest.mark.asyncio
    async def test_first_upload_creates_a_document(self, audio_env):
        file = _upload_file()

        response = await upload_text_audio(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            file=file,
            duration_ms=90000,
        )

        audio_env.upload.assert_called_once_with(
            bucket_name=BUCKET_NAME,
            s3_key=NEW_AUDIO_KEY,
            file=file,
        )
        audio_env.delete.assert_not_called()
        assert response.audio_key == NEW_AUDIO_KEY
        assert response.text_title == TEXT_TITLE
        assert response.file_name == "chant.mp3"
        assert response.mime_type == "audio/mpeg"
        assert response.file_size_bytes == file.size
        assert response.duration_ms == 90000

    @pytest.mark.asyncio
    async def test_upload_replaces_existing_audio_and_removes_the_old_object(self, audio_env):
        existing = _existing_audio(audio_env.model)
        audio_env.model.find_one.return_value = existing

        response = await upload_text_audio(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            file=_upload_file(filename="new-chant.wav", content_type="audio/wav"),
        )

        existing.save.assert_awaited_once()
        audio_env.delete.assert_called_once_with(EXISTING_AUDIO_KEY)
        assert response.audio_key == f"audio/texts/{GENERATED_UUID}.wav"
        assert response.file_name == "new-chant.wav"
        assert response.mime_type == "audio/wav"
        assert response.duration_ms is None

    @pytest.mark.asyncio
    async def test_mime_type_is_guessed_when_the_client_omits_it(self, audio_env):
        with patch(f"{SERVICE}.mimetypes.guess_type", return_value=("audio/ogg", None)):
            response = await upload_text_audio(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                file=_upload_file(filename="chant.ogg", content_type=None),
            )

        assert response.mime_type == "audio/ogg"

    @pytest.mark.asyncio
    async def test_mime_type_falls_back_to_mpeg_when_it_cannot_be_guessed(self, audio_env):
        with patch(f"{SERVICE}.mimetypes.guess_type", return_value=(None, None)):
            response = await upload_text_audio(
                token=VALID_TOKEN,
                text_id=TEXT_ID,
                file=_upload_file(content_type=None),
            )

        assert response.mime_type == "audio/mpeg"

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
    async def test_replacement_succeeds_even_if_the_old_object_cannot_be_deleted(self, audio_env):
        audio_env.model.find_one.return_value = _existing_audio(audio_env.model)
        audio_env.delete.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 delete failed",
        )

        response = await upload_text_audio(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            file=_upload_file(),
        )

        assert response.audio_key == NEW_AUDIO_KEY
        audio_env.delete.assert_called_once_with(EXISTING_AUDIO_KEY)

    @pytest.mark.asyncio
    async def test_nothing_is_uploaded_when_the_text_is_missing(self, audio_env):
        audio_env.get_text.return_value = None
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

    @pytest.mark.asyncio
    async def test_concurrent_upload_handles_duplicate_key_error(self, audio_env):
        """When concurrent uploads race, DuplicateKeyError is caught and metadata updated."""
        from pymongo.errors import DuplicateKeyError

        file = _upload_file()
        # Patch the __init__ to make insert fail with DuplicateKeyError on first create
        original_init = audio_env.model.__init__

        def init_with_insert_fail(self, **fields):
            original_init(self, **fields)
            self.insert = AsyncMock(side_effect=DuplicateKeyError("Duplicate key error"))

        concurrent_audio = _existing_audio(audio_env.model)
        audio_env.model.find_one.return_value = concurrent_audio

        with patch.object(audio_env.model, "__init__", init_with_insert_fail):
            response = await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        # The concurrent document should have been updated
        concurrent_audio.save.assert_awaited_once()
        assert response.audio_key == NEW_AUDIO_KEY

    @pytest.mark.asyncio
    async def test_concurrent_upload_cleans_up_on_duplicate_key_error(self, audio_env):
        """When DuplicateKeyError occurs and no document found, S3 object is cleaned up."""
        from pymongo.errors import DuplicateKeyError

        file = _upload_file()
        # Patch the __init__ to make insert fail with DuplicateKeyError
        original_init = audio_env.model.__init__

        def init_with_insert_fail(self, **fields):
            original_init(self, **fields)
            self.insert = AsyncMock(side_effect=DuplicateKeyError("Duplicate key error"))

        # When find_one returns None, it means the race condition couldn't be resolved
        audio_env.model.find_one.return_value = None

        with patch.object(audio_env.model, "__init__", init_with_insert_fail):
            with pytest.raises(HTTPException) as exc:
                await upload_text_audio(token=VALID_TOKEN, text_id=TEXT_ID, file=file)

        assert exc.value.status_code == status.HTTP_409_CONFLICT
        # S3 object should be cleaned up on failure
        audio_env.delete.assert_called_once_with(NEW_AUDIO_KEY)


class TestDeleteTextAudio:
    @pytest.mark.asyncio
    async def test_stored_audio_is_removed_from_s3_and_mongo(self, audio_env):
        existing = _existing_audio(audio_env.model)
        audio_env.model.find_one.return_value = existing

        assert await delete_text_audio(token=VALID_TOKEN, text_id=TEXT_ID) is None

        audio_env.delete.assert_called_once_with(EXISTING_AUDIO_KEY)
        existing.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_is_a_no_op_when_there_is_no_audio(self, audio_env):
        assert await delete_text_audio(token=VALID_TOKEN, text_id=TEXT_ID) is None

        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_text_raises_not_found(self, audio_env):
        audio_env.get_text.return_value = None

        with pytest.raises(HTTPException) as exc:
            await delete_text_audio(token=VALID_TOKEN, text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        audio_env.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_deletion_failure_retains_metadata(self, audio_env):
        """When S3 deletion fails, metadata should remain in DB for retry."""
        existing = _existing_audio(audio_env.model)
        audio_env.model.find_one.return_value = existing
        audio_env.delete.side_effect = HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 error")

        with pytest.raises(HTTPException) as exc:
            await delete_text_audio(token=VALID_TOKEN, text_id=TEXT_ID)

        assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        # Metadata should NOT be deleted when S3 deletion fails
        existing.delete.assert_not_awaited()
