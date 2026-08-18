import io
import os
import subprocess
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.texts.audio_transcoder import (
    CONVERSION_FAILED_DETAIL,
    CONVERSION_UNAVAILABLE_DETAIL,
    MP3_EXTENSION,
    MP3_MIME_TYPE,
    transcode_to_mp3,
)

MODULE = "pecha_api.texts.audio_transcoder"
CONFIG = {
    "FFMPEG_BINARY": "ffmpeg",
    "FFPROBE_BINARY": "ffprobe",
    "AUDIO_MP3_BITRATE": "128k",
}
MP3_BYTES = b"ID3 converted audio"


def _completed(stdout: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr=b"")


@pytest.fixture
def transcoder_env():
    """ffmpeg writes to the output path, so fake it by planting the bytes there."""
    def fake_run(command, **kwargs):
        if command[0] == "ffmpeg":
            with open(command[-1], "wb") as output:
                output.write(MP3_BYTES)
            return _completed()
        return _completed(stdout=b"10.580000\n")

    with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
         patch(f"{MODULE}.subprocess.run", side_effect=fake_run) as run:
        yield run


class TestTranscodeToMp3:
    def test_converted_bytes_and_duration_are_returned(self, transcoder_env):
        result = transcode_to_mp3(io.BytesIO(b"alac m4a bytes"), suffix=".m4a")

        assert result.content == MP3_BYTES
        assert result.duration_ms == 10580

    def test_ffmpeg_is_called_with_the_configured_bitrate(self, transcoder_env):
        transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        command = transcoder_env.call_args_list[0].args[0]
        assert command[0] == "ffmpeg"
        assert command[command.index("-b:a") + 1] == "128k"
        assert command[command.index("-codec:a") + 1] == "libmp3lame"
        assert command[-1].endswith(MP3_EXTENSION)
        assert command[command.index("-i") + 1].endswith(".m4a")

    def test_the_whole_source_is_converted_even_after_a_partial_read(self, transcoder_env):
        source = io.BytesIO(b"alac m4a bytes")
        source.read(4)

        transcode_to_mp3(source, suffix=".m4a")

        assert source.tell() == len(b"alac m4a bytes")

    def test_temporary_files_are_removed(self, transcoder_env):
        transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        command = transcoder_env.call_args_list[0].args[0]
        assert not os.path.exists(command[command.index("-i") + 1])
        assert not os.path.exists(command[-1])

    def test_an_undecodable_file_is_rejected(self):
        def failing_run(command, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1, cmd=command, stderr=b"Invalid data found"
            )

        with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
             patch(f"{MODULE}.subprocess.run", side_effect=failing_run):
            with pytest.raises(HTTPException) as exc:
                transcode_to_mp3(io.BytesIO(b"not audio"), suffix=".m4a")

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == CONVERSION_FAILED_DETAIL

    def test_an_empty_conversion_is_rejected(self):
        def empty_run(command, **kwargs):
            if command[0] == "ffmpeg":
                open(command[-1], "wb").close()
            return _completed()

        with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
             patch(f"{MODULE}.subprocess.run", side_effect=empty_run):
            with pytest.raises(HTTPException) as exc:
                transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.value.detail == CONVERSION_FAILED_DETAIL

    def test_a_missing_ffmpeg_reports_the_service_as_unavailable(self):
        with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
             patch(f"{MODULE}.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(HTTPException) as exc:
                transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.value.detail == CONVERSION_UNAVAILABLE_DETAIL

    def test_a_failed_duration_probe_does_not_fail_the_conversion(self):
        def run(command, **kwargs):
            if command[0] == "ffmpeg":
                with open(command[-1], "wb") as output:
                    output.write(MP3_BYTES)
                return _completed()
            raise subprocess.CalledProcessError(returncode=1, cmd=command, stderr=b"")

        with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
             patch(f"{MODULE}.subprocess.run", side_effect=run):
            result = transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        assert result.content == MP3_BYTES
        assert result.duration_ms is None

    def test_an_unparsable_duration_is_ignored(self):
        def run(command, **kwargs):
            if command[0] == "ffmpeg":
                with open(command[-1], "wb") as output:
                    output.write(MP3_BYTES)
                return _completed()
            return _completed(stdout=b"N/A\n")

        with patch(f"{MODULE}.get", side_effect=CONFIG.get), \
             patch(f"{MODULE}.subprocess.run", side_effect=run):
            result = transcode_to_mp3(io.BytesIO(b"bytes"), suffix=".m4a")

        assert result.duration_ms is None


def test_mp3_constants():
    assert MP3_EXTENSION == ".mp3"
    assert MP3_MIME_TYPE == "audio/mpeg"
