from html.parser import HTMLParser
from typing import List, Optional, Tuple

from .text_audio_models import OtrSpanEntry, OtrSpanRange


class _OtrTranscriptParser(HTMLParser):
    """Extracts plain transcript text and audio-sync spans from an OTR
    upload's HTML "text" field.

    Editors mark sync points with
    `<span class="timestamp" data-timestamp="SECONDS">label</span>`; the
    label (e.g. "1:09:00") is just a display string and is dropped. Each
    marker opens a span that runs until the next marker (or the end of the
    document), recording the audio timestamp at which that stretch of text
    starts.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: List[str] = []
        self._spans: List[OtrSpanEntry] = []
        self._pending_timestamp: Optional[float] = None
        self._pending_start = 0
        self._in_timestamp_label = False

    @property
    def text(self) -> str:
        return "".join(self._chunks)

    @property
    def spans(self) -> List[OtrSpanEntry]:
        return self._spans

    def _position(self) -> int:
        return len(self.text)

    def _close_pending_span(self) -> None:
        if self._pending_timestamp is None:
            return
        end = self._position()
        if end > self._pending_start:
            self._spans.append(
                OtrSpanEntry(
                    span=OtrSpanRange(start=self._pending_start, end=end),
                    timestamp=self._pending_timestamp,
                )
            )
        self._pending_timestamp = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "span":
            attr_map = dict(attrs)
            if attr_map.get("class") == "timestamp":
                timestamp = self._parse_timestamp(attr_map.get("data-timestamp"))
                if timestamp is not None:
                    self._close_pending_span()
                    self._pending_timestamp = timestamp
                    self._pending_start = self._position()
                self._in_timestamp_label = True
            return
        if tag == "br":
            self._chunks.append("\n")
        elif tag == "p" and self._chunks:
            self._chunks.append("\n\n")

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self._in_timestamp_label = False

    def handle_data(self, data: str) -> None:
        if self._in_timestamp_label:
            return
        self._chunks.append(data)

    def close(self) -> None:
        super().close()
        self._close_pending_span()

    @staticmethod
    def _parse_timestamp(raw: Optional[str]) -> Optional[float]:
        if raw is None:
            return None
        try:
            return float(raw)
        except ValueError:
            return None


def parse_otr_transcript(raw_text: object) -> Tuple[str, List[OtrSpanEntry]]:
    """Parse an OTR upload's HTML "text" field into plain transcript text
    plus the audio-sync spans anchored to its timestamp markers."""
    if not isinstance(raw_text, str) or not raw_text.strip():
        return "", []
    parser = _OtrTranscriptParser()
    parser.feed(raw_text)
    parser.close()
    return parser.text, parser.spans
