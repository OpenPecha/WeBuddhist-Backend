from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole, AuthorGroupType
from pecha_api.plans.groups.groups_response_models import (
    AuthorGroupDetailDTO,
    AuthorGroupListResponse,
    AuthorGroupSummaryDTO,
    GroupInviteCreatedResponse,
    GroupMetadataDTO,
)
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
        group_type=AuthorGroupType.PAGE,
        is_public=True,
        metadata=_metadata(),
        members=[],
        tags=[],
        social_links=[],
        series=[],
        plans=[],
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
            "/cms/author/groups",
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
        group_type=AuthorGroupType.PAGE,
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
        response = client.get("/author/groups")

    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(
        search=None, language=None, tag_id=None, group_type=AuthorGroupType.COMMUNITY, skip=0, limit=20
    )
    assert response.json()["total"] == 1


def test_create_group_invite_success():
    from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus
    from pecha_api.plans.groups.groups_response_models import GroupInviteDTO

    group_id = uuid4()
    invite_id = uuid4()
    invite_dto = GroupInviteDTO(
        id=invite_id,
        group_id=group_id,
        group_name="Bodhichitta Authors",
        target_email="author@example.org",
        role=AuthorGroupMemberRole.AUTHOR,
        status=AuthorGroupInviteStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        created_at=datetime.now(timezone.utc),
        created_by="owner@example.org",
        inviter_name="Group Owner",
        inviter_email="owner@example.org",
    )
    invite_response = GroupInviteCreatedResponse(
        invite=invite_dto,
        notification_id=uuid4(),
    )
    payload = {"target_email": "author@example.org", "role": "AUTHOR"}
    with patch(
        "pecha_api.plans.groups.groups_views.create_group_member_invite",
        return_value=invite_response,
    ) as mock_service:
        response = client.post(
            f"/cms/author/groups/{group_id}/members/invites",
            json=payload,
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["invite"]["id"] == str(invite_id)
    mock_service.assert_called_once()


def test_get_my_pending_group_invites_delegates_to_service():
    from pecha_api.plans.groups.groups_response_models import GroupInviteListResponse

    with patch(
        "pecha_api.plans.groups.groups_views.list_my_pending_group_invites",
        return_value=GroupInviteListResponse(invites=[], total=0),
    ) as mock_service:
        response = client.get(
            "/cms/author/groups/invites/me",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(token="dummy")


def test_reject_group_invite_by_id_delegates_to_service():
    from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus
    from pecha_api.plans.groups.groups_response_models import GroupInviteDTO

    invite_id = uuid4()
    invite_dto = GroupInviteDTO(
        id=invite_id,
        group_id=uuid4(),
        group_name="Test Group",
        target_email="invitee@example.org",
        role=AuthorGroupMemberRole.AUTHOR,
        status=AuthorGroupInviteStatus.REJECTED,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        created_at=datetime.now(timezone.utc),
        created_by="owner@example.org",
        inviter_name="Group Owner",
        inviter_email="owner@example.org",
    )
    with patch(
        "pecha_api.plans.groups.groups_views.reject_group_invite_by_id",
        return_value=invite_dto,
    ) as mock_service:
        response = client.post(
            f"/cms/author/groups/invites/{invite_id}/reject",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(token="dummy", invite_id=invite_id)


def test_accept_group_invite_by_id_delegates_to_service():
    invite_id = uuid4()
    with patch(
        "pecha_api.plans.groups.groups_views.accept_group_invite_by_id",
        return_value=_group_detail(),
    ) as mock_service:
        response = client.post(
            f"/cms/author/groups/invites/{invite_id}/accept",
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once()


def test_put_cms_group_delegates_to_service():
    group_id = uuid4()
    detail = _group_detail()
    with patch(
        "pecha_api.plans.groups.groups_views.update_author_group",
        return_value=detail,
    ) as mock_service:
        response = client.put(
            f"/cms/author/groups/{group_id}",
            json={"slug": "updated-slug", "is_public": False},
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once()


def test_patch_cms_group_delegates_to_service():
    group_id = uuid4()
    detail = _group_detail()
    with patch(
        "pecha_api.plans.groups.groups_views.update_author_group",
        return_value=detail,
    ) as mock_service:
        response = client.patch(
            f"/cms/author/groups/{group_id}",
            json={"slug": "updated-slug"},
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once()


def test_get_cms_group_by_id():
    group_id = uuid4()
    with patch(
        "pecha_api.plans.groups.groups_views.get_cms_group_detail",
        return_value=_group_detail(),
    ) as mock_service:
        response = client.get(
            f"/cms/author/groups/{group_id}",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once()


def test_get_cms_groups_with_filters():
    summary = AuthorGroupSummaryDTO(
        id=uuid4(),
        slug="g",
        group_type=AuthorGroupType.PAGE,
        is_public=True,
        metadata=_metadata(),
        tags=[],
        follower_count=0,
        member_count=1,
    )
    listing = AuthorGroupListResponse(groups=[summary], skip=5, limit=10, total=1)
    tag_id = uuid4()
    with patch(
        "pecha_api.plans.groups.groups_views.list_cms_groups",
        return_value=listing,
    ) as mock_service:
        response = client.get(
            f"/cms/author/groups?search=foo&language=EN&skip=5&limit=10&tag_id={tag_id}",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(
        token="dummy",
        search="foo",
        language="EN",
        tag_id=tag_id,
        is_public=None,
        group_type=None,
        for_transfer=False,
        skip=5,
        limit=10,
    )


def test_put_cms_group_relations():
    group_id = uuid4()
    detail = _group_detail()
    tag_id = uuid4()
    plan_id = uuid4()
    series_id = uuid4()
    headers = {"Authorization": "Bearer dummy"}

    with patch("pecha_api.plans.groups.groups_views.replace_group_tags", return_value=detail) as mock_tags:
        assert client.put(f"/cms/author/groups/{group_id}/tags", json={"tag_ids": [str(tag_id)]}, headers=headers).status_code == 200
        mock_tags.assert_called_once()

    with patch(
        "pecha_api.plans.groups.groups_views.replace_group_social_links_by_id",
        return_value=detail,
    ) as mock_links:
        assert (
            client.put(
                f"/cms/author/groups/{group_id}/social-links",
                json={"social_links": [{"platform": "x", "url": "https://x.com/g"}]},
                headers=headers,
            ).status_code
            == 200
        )
        mock_links.assert_called_once()


def test_revoke_invite_and_member_endpoints():
    group_id = uuid4()
    invite_id = uuid4()
    author_id = uuid4()
    headers = {"Authorization": "Bearer dummy"}

    with patch("pecha_api.plans.groups.groups_views.revoke_group_invite") as mock_revoke:
        response = client.post(f"/cms/author/groups/{group_id}/members/invites/{invite_id}/revoke", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_revoke.assert_called_once()

    with patch("pecha_api.plans.groups.groups_views.update_group_member_role", return_value=_group_detail()) as mock_role:
        response = client.patch(
            f"/cms/author/groups/{group_id}/members/{author_id}/role",
            json={"role": "ADMIN"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK
        mock_role.assert_called_once()

    with patch("pecha_api.plans.groups.groups_views.delete_group_member") as mock_delete:
        response = client.delete(f"/cms/author/groups/{group_id}/members/{author_id}", headers=headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_delete.assert_called_once()


def test_get_public_group_by_id():
    group_id = uuid4()
    with patch(
        "pecha_api.plans.groups.groups_views.get_author_group_detail",
        return_value=_group_detail(),
    ) as mock_service:
        response = client.get(f"/author/groups/{group_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["slug"] == "bodhichitta-authors"
    mock_service.assert_called_once_with(group_id=group_id, require_public=True, language=None)


def test_get_public_group_by_id_with_language():
    group_id = uuid4()
    with patch(
        "pecha_api.plans.groups.groups_views.get_author_group_detail",
        return_value=_group_detail(),
    ) as mock_service:
        response = client.get(f"/author/groups/{group_id}?language=bo")
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(group_id=group_id, require_public=True, language="bo")


def test_follow_and_unfollow_group():
    group_id = uuid4()
    headers = {"Authorization": "Bearer dummy"}
    with patch("pecha_api.plans.groups.groups_views.follow_group") as mock_follow:
        assert client.post(f"/author/groups/{group_id}/follow", headers=headers).status_code == status.HTTP_204_NO_CONTENT
        mock_follow.assert_called_once()
    with patch("pecha_api.plans.groups.groups_views.unfollow_group") as mock_unfollow:
        assert client.delete(f"/author/groups/{group_id}/follow", headers=headers).status_code == status.HTTP_204_NO_CONTENT
        mock_unfollow.assert_called_once()


def test_get_my_followed_groups():
    listing = AuthorGroupListResponse(groups=[], skip=0, limit=20, total=0)
    with patch(
        "pecha_api.plans.groups.groups_views.list_followed_groups",
        return_value=listing,
    ) as mock_service:
        response = client.get(
            "/users/me/following/author/groups?skip=0&limit=20",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(token="dummy", skip=0, limit=20)


def test_get_my_followed_group_by_id():
    group_id = uuid4()
    group_summary = AuthorGroupSummaryDTO(
        id=group_id,
        slug="bodhichitta-authors",
        group_type=AuthorGroupType.PAGE,
        is_public=True,
        metadata=_metadata(),
        tags=[],
        follower_count=4,
        member_count=2,
    )
    with patch(
        "pecha_api.plans.groups.groups_views.get_followed_group",
        return_value=group_summary,
    ) as mock_service:
        response = client.get(
            f"/users/me/following/author/groups?group_id={group_id}&language=bo",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(group_id)
    mock_service.assert_called_once_with(token="dummy", group_id=group_id, language="bo")


def test_join_and_leave_group():
    group_id = uuid4()
    headers = {"Authorization": "Bearer dummy"}
    with patch("pecha_api.plans.groups.groups_views.join_group") as mock_join:
        assert client.post(f"/author/groups/{group_id}/join", headers=headers).status_code == status.HTTP_204_NO_CONTENT
        mock_join.assert_called_once()
    with patch("pecha_api.plans.groups.groups_views.leave_group") as mock_leave:
        assert client.delete(f"/author/groups/{group_id}/join", headers=headers).status_code == status.HTTP_204_NO_CONTENT
        mock_leave.assert_called_once()


def test_get_my_joined_groups():
    listing = AuthorGroupListResponse(groups=[], skip=0, limit=20, total=0)
    with patch(
        "pecha_api.plans.groups.groups_views.list_joined_groups",
        return_value=listing,
    ) as mock_service:
        response = client.get(
            "/users/me/joined/author/groups?skip=0&limit=20",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(token="dummy", skip=0, limit=20)


def test_get_my_joined_group_by_id():
    group_id = uuid4()
    group_summary = AuthorGroupSummaryDTO(
        id=group_id,
        slug="bodhichitta-authors",
        group_type=AuthorGroupType.PAGE,
        is_public=True,
        metadata=_metadata(),
        tags=[],
        follower_count=4,
        member_count=2,
    )
    with patch(
        "pecha_api.plans.groups.groups_views.get_joined_group",
        return_value=group_summary,
    ) as mock_service:
        response = client.get(
            f"/users/me/joined/author/groups?group_id={group_id}&language=bo",
            headers={"Authorization": "Bearer dummy"},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(group_id)
    mock_service.assert_called_once_with(token="dummy", group_id=group_id, language="bo")
