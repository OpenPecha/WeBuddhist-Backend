"""Re-encode uploaded audio to MP3.

Recorders write whatever codec they like into the containers we accept -
Apple Voice Memos, for instance, puts ALAC inside an .m4a, which only Safari
can decode, so the file plays nowhere else. Every upload is converted to MP3
before it reaches S3 so the stored object is playable in any browser.
"""

import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import BinaryIO, Optional

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get

MP3_EXTENSION = ".mp3"
MP3_MIME_TYPE = "audio/mpeg"

CONVERSION_FAILED_DETAIL = (
    "Could not convert this audio file. Use MP3, M4A, WAV, AAC, or OGG."
)
CONVERSION_UNAVAILABLE_DETAIL = "Audio conversion is unavailable."


@dataclass
class TranscodedAudio:
    content: bytes
    duration_ms: Optional[int]


def _run(command: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, capture_output=True, check=True)
    except FileNotFoundError:
        logging.error("%s is not installed on this host.", command[0])
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=CONVERSION_UNAVAILABLE_DETAIL,
        )


def _probe_duration_ms(path: str) -> Optional[int]:
    try:
        result = _run([
            get("FFPROBE_BINARY"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ])
        return round(float(result.stdout.decode().strip()) * 1000)
    except (subprocess.CalledProcessError, ValueError):
        # Duration is a nice-to-have; a converted file without it is fine.
        return None


def transcode_to_mp3(source: BinaryIO, suffix: str = "") -> TranscodedAudio:
    """Convert an uploaded audio stream to MP3, reporting its duration."""
    source_path = output_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as source_file:
            source.seek(0)
            source_file.write(source.read())
            source_path = source_file.name
        with tempfile.NamedTemporaryFile(suffix=MP3_EXTENSION, delete=False) as output_file:
            output_path = output_file.name

        try:
            _run([
                get("FFMPEG_BINARY"),
                "-hide_banner",
                "-loglevel", "error",
                "-nostdin",
                "-y",
                "-i", source_path,
                "-vn",
                "-map_metadata", "-1",
                "-codec:a", "libmp3lame",
                "-b:a", get("AUDIO_MP3_BITRATE"),
                output_path,
            ])
        except subprocess.CalledProcessError as error:
            logging.error("ffmpeg failed to convert audio: %s", error.stderr)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CONVERSION_FAILED_DETAIL,
            )

        with open(output_path, "rb") as converted:
            content = converted.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CONVERSION_FAILED_DETAIL,
            )
        return TranscodedAudio(
            content=content,
            duration_ms=_probe_duration_ms(output_path),
        )
    finally:
        for path in (source_path, output_path):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    logging.warning("Could not remove the temporary file %s.", path)
