from unittest.mock import patch

from fastapi.testclient import TestClient

from pecha_api.app import api

IMAGE_URL = "/api/v1/share/image?poem_id=3f2504e0-4f89-11d3-9a0c-0305e82c3301"
POEM_IMAGE = (b"x" * 5000, "image/jpeg")


def test_image_route_answers_head_requests():
    """Social crawlers send HEAD before fetching; a 405 means no preview image."""
    client = TestClient(api)

    with patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=POEM_IMAGE):
        response = client.head(IMAGE_URL)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        # The size must be known from the HEAD alone, so it cannot be chunked.
        assert response.headers["content-length"] == "5000"
        assert response.content == b""


def test_image_route_get_returns_the_body():
    client = TestClient(api)

    with patch("pecha_api.share.share_service._get_poem_image_bytes_", return_value=POEM_IMAGE):
        response = client.get(IMAGE_URL)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.headers["content-length"] == "5000"
        assert len(response.content) == 5000
