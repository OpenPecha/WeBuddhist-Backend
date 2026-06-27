import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def extract_youtube_video_id(url: str) -> Optional[str]:
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower()
    if host not in _YOUTUBE_HOSTS:
        return None
    if host in ("youtu.be", "www.youtu.be"):
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif parsed.path.startswith(("/embed/", "/shorts/", "/v/")):
        candidate = parsed.path.split("/")[2]
    else:
        candidate = parse_qs(parsed.query).get("v", [None])[0]
    if candidate and re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate
    return None
