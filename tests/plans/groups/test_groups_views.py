from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.groups.groups_response_models import (
    AuthorGroupDetailDTO,
    AuthorGroupListResponse,
    AuthorGroupSummaryDTO,
    GroupInviteCreatedResponse,
    GroupMetadataDTO,
)
from pecha_api.plans.groups.groups_service import InviteEmailMismatchError


client = TestClient(api)


def _metadata() -> list[GroupMetadataDTO]:
    return [
        GroupMetadataDTO(
            id=uuid4(),
            title="Bodhichitta Authors",
            description="Meditation and Dharma writers",
            language="EN",
        )
    ]


def _group_detail() -> AuthorGroupDetailDTO:
    return AuthorGroupDetailDTO(
        id=uuid4(),
        slug="bodhichitta-authors",
        is_public=True,
        metadata=_metadata(),
        members=[],
        tags=[],
        social_links=[],
        series_ids=[],
        plan_ids=[],
        follower_count=0,
    )


def test_create_cms_group_success():
    group_detail = _group_detail()
    payload = {
        "slug": "bodhichitta-authors",
        "is_public": True,
        "metadata": [{"title": "Bodhichitta Authors", "description": "Dharma", "language": "EN"}],
    }
    with patch(
        "pecha_api.plans.groups.groups_views.create_author_group",
        return_value=group_detail,
    ) as mock_service:
        response = client.post(
            "/cms/groups",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    mock_service.assert_called_once()
    assert response.json()["slug"] == "bodhichitta-authors"


def test_get_public_groups_success():
    group_summary = AuthorGroupSummaryDTO(
        id=uuid4(),
        slug="bodhichitta-authors",
        is_public=True,
        metadata=_metadata(),
        tags=[],
        follower_count=4,
        member_count=2,
    )
    response_model = AuthorGroupListResponse(groups=[group_summary], skip=0, limit=20, total=1)
    with patch(
        "pecha_api.plans.groups.groups_views.list_public_groups",
        return_value=response_model,
    ) as mock_service:
        response = client.get("/groups")

    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(search=None, language=None, tag_id=None, skip=0, limit=20)
    assert response.json()["total"] == 1


def test_create_group_invite_success():
    group_id = uuid4()
    invite_response = GroupInviteCreatedResponse(
        invite_id=uuid4(),
        token="raw-token",
        target_email="author@example.org",
        role=AuthorGroupMemberRole.AUTHOR,
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        max_uses=1,
    )
    payload = {
        "target_email": "author@example.org",
        "role": "AUTHOR",
        "expires_at": "2026-05-31T12:00:00Z",
        "max_uses": 1,
    }
    with patch(
        "pecha_api.plans.groups.groups_views.create_group_member_invite",
        return_value=invite_response,
    ) as mock_service:
        response = client.post(
            f"/cms/groups/{group_id}/members/invites",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["token"] == "raw-token"
    mock_service.assert_called_once()


def test_accept_group_invite_email_mismatch_returns_code():
    payload = {"token": "wrong-user-token"}
    with patch(
        "pecha_api.plans.groups.groups_views.accept_group_invite",
        side_effect=InviteEmailMismatchError("This invite was sent to a different email address."),
    ):
        response = client.post(
            "/cms/groups/invites/accept",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "This invite was sent to a different email address.",
        "code": "INVITE_EMAIL_MISMATCH",
    }
