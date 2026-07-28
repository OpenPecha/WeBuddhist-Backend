from starlette import status


def get_client():
    from pecha_api.app import api
    from fastapi.testclient import TestClient
    return TestClient(api)


class TestChatViewer:

    def test_view_chat_page_renders(self):
        client = get_client()

        response = client.get("/view/chat")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "Chat Test Viewer" in response.text
        assert "/chat/live" in response.text
