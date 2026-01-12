import requests
import pytest
from unittest.mock import AsyncMock, patch


class DummyResponse:
    def __init__(
        self,
        payload,
        *,
        ok: bool = True,
        status_code: int = 200,
        text: str = "",
        raise_for_status_exc: Exception | None = None,
    ):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.text = text
        self._raise_for_status_exc = raise_for_status_exc

    def raise_for_status(self):
        if self._raise_for_status_exc:
            raise self._raise_for_status_exc

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_get_segments_annotation_calls_instances_endpoint():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse([{"ok": True}])
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_to_thread:
        result = await repo.get_segments_annotation(
            pecha_text_id="P1", openpecha_api_url="https://openpecha.example"
        )

    assert result == [{"ok": True}]
    assert mock_to_thread.await_count == 1
    call = mock_to_thread.await_args
    assert call.args[0] is repo.requests.get
    assert call.args[1] == "https://openpecha.example/v2/instances/P1"
    assert call.kwargs["params"] == {"annotation": "true", "content": "true"}


@pytest.mark.asyncio
async def test_get_segments_id_by_annotation_id_calls_annotations_endpoint():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse([{"id": "a1"}])
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_to_thread:
        result = await repo.get_segments_id_by_annotation_id(
            annotation_id="ann_1", openpecha_api_url="https://openpecha.example"
        )

    assert result == [{"id": "a1"}]
    call = mock_to_thread.await_args
    assert call.args[0] is repo.requests.get
    assert call.args[1] == "https://openpecha.example/v2/annotations/ann_1"

@pytest.mark.asyncio
async def test_get_segments_by_id_calls_annotations_endpoint():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse({"data": [{"id": "seg"}]})
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_to_thread:
        result = await repo.get_segments_by_id(
            annotation_id="ann_2",
            openpecha_api_url="https://openpecha.example",
        )

    assert result == {"data": [{"id": "seg"}]}
    call = mock_to_thread.await_args
    assert call.args[0] is repo.requests.get
    assert call.args[1] == "https://openpecha.example/v2/annotations/ann_2"


@pytest.mark.asyncio
async def test_get_segment_content_success_posts_segment_ids_payload():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse([{"segment_id": "s1", "content": "c1"}])
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_to_thread:
        result = await repo.get_segment_content(
            segment_id=["s1", "s2"],
            pecha_text_id="P1",
            openpecha_api_url="https://openpecha.example",
        )

    assert result == [{"segment_id": "s1", "content": "c1"}]
    call = mock_to_thread.await_args
    assert call.args[0] is repo.requests.post
    assert call.args[1] == "https://openpecha.example/v2/instances/P1/segment-content"
    assert call.kwargs["json"] == {"segment_ids": ["s1", "s2"]}


@pytest.mark.asyncio
async def test_get_segment_content_raises_on_http_error():
    from pecha_api.text_uploader.segments import segment_respository as repo

    http_error = requests.exceptions.HTTPError("boom")
    response = DummyResponse(
        {"detail": "bad"},
        ok=False,
        status_code=400,
        text="bad",
        raise_for_status_exc=http_error,
    )
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(requests.exceptions.HTTPError):
            await repo.get_segment_content(
                segment_id=["s1"],
                pecha_text_id="P1",
                openpecha_api_url="https://openpecha.example",
            )

@pytest.mark.asyncio
async def test_get_segment_content_raises_on_request_exception():
    from pecha_api.text_uploader.segments import segment_respository as repo

    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        side_effect=requests.exceptions.RequestException("boom"),
    ):
        with pytest.raises(requests.exceptions.RequestException):
            await repo.get_segment_content(
                segment_id=["s1"],
                pecha_text_id="P1",
                openpecha_api_url="https://openpecha.example",
            )


@pytest.mark.asyncio
async def test_get_segment_content_raises_on_unexpected_exception():
    from pecha_api.text_uploader.segments import segment_respository as repo

    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError):
            await repo.get_segment_content(
                segment_id=["s1"],
                pecha_text_id="P1",
                openpecha_api_url="https://openpecha.example",
            )


@pytest.mark.asyncio
async def test_post_segments_returns_json_when_ok():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse({"id": "seg_1"}, ok=True)
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ) as mock_to_thread:
        result = await repo.post_segments(
            segments_payload={"text_id": "t1", "segments": []},
            destination_url="https://dest.example",
            token="tok",
        )

    assert result == {"id": "seg_1"}
    call = mock_to_thread.await_args
    assert call.args[0] is repo.requests.post
    assert call.args[1] == "https://dest.example/segments"
    assert call.kwargs["headers"]["Authorization"] == "Bearer tok"


@pytest.mark.asyncio
async def test_post_segments_raises_for_non_ok_response():
    from pecha_api.text_uploader.segments import segment_respository as repo

    response = DummyResponse(
        {"detail": "bad"},
        ok=False,
        status_code=400,
        text="bad",
        raise_for_status_exc=requests.exceptions.HTTPError("boom"),
    )
    with patch(
        "pecha_api.text_uploader.segments.segment_respository.asyncio.to_thread",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(requests.exceptions.HTTPError):
            await repo.post_segments(
                segments_payload={"text_id": "t1", "segments": []},
                destination_url="https://dest.example",
                token="tok",
            )

