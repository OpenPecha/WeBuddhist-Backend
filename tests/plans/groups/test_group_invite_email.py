from unittest.mock import patch

from pecha_api.plans.groups.group_invite_email import (
    _build_invitation_html,
    _invite_expiry_label,
    send_group_invitation_email,
)


def test_invite_expiry_label_plural_minutes():
    with patch("pecha_api.plans.groups.group_invite_email.get_int", return_value=30):
        assert _invite_expiry_label() == "30 minutes"


def test_invite_expiry_label_singular_minute():
    with patch("pecha_api.plans.groups.group_invite_email.get_int", return_value=1):
        assert _invite_expiry_label() == "1 minute"


def test_build_invitation_html_contains_group_and_role():
    html = _build_invitation_html(
        inviter_name="Alice",
        inviter_email="alice@example.org",
        group_title="Dharma Group",
        invite_role="AUTHOR",
        invitations_url="https://studio.webuddhist.com/groups",
        login_url="https://studio.webuddhist.com/login",
        logo_url="https://example.com/logo.png",
    )
    assert "Dharma Group" in html
    assert "Author" in html
    assert "alice@example.org" in html


def test_build_invitation_html_contains_login_link():
    html = _build_invitation_html(
        inviter_name="Alice",
        inviter_email="alice@example.org",
        group_title="Dharma Group",
        invite_role="AUTHOR",
        invitations_url="https://studio.webuddhist.com/groups",
        login_url="https://studio.webuddhist.com/login",
        logo_url="https://example.com/logo.png",
    )
    assert 'href="https://studio.webuddhist.com/login"' in html
    assert "Log in to WeBuddhist Studio" in html


def test_send_group_invitation_email_success():
    with patch("pecha_api.plans.groups.group_invite_email.get", side_effect=lambda key: {
        "WEBUDDHIST_STUDIO_BASE_URL": "https://studio.webuddhist.com",
        "WEBUDDHIST_EMAIL_LOGO_URL": "https://example.com/logo.png",
    }[key]), patch(
        "pecha_api.plans.groups.group_invite_email.get_int",
        return_value=30,
    ), patch(
        "pecha_api.plans.groups.group_invite_email.send_email",
    ) as mock_send:
        send_group_invitation_email(
            target_email="invitee@example.org",
            inviter_name="Alice",
            inviter_email="alice@example.org",
            group_title="Dharma Group",
            invite_role="AUTHOR",
        )
    mock_send.assert_called_once()
    message = mock_send.call_args.kwargs["message"]
    assert "Dharma Group" in message
    assert 'href="https://studio.webuddhist.com/login"' in message


def test_send_group_invitation_email_logs_failure():
    with patch("pecha_api.plans.groups.group_invite_email.get", side_effect=lambda key: {
        "WEBUDDHIST_STUDIO_BASE_URL": "https://studio.webuddhist.com/",
        "WEBUDDHIST_EMAIL_LOGO_URL": "https://example.com/logo.png",
    }[key]), patch(
        "pecha_api.plans.groups.group_invite_email.get_int",
        return_value=30,
    ), patch(
        "pecha_api.plans.groups.group_invite_email.send_email",
        side_effect=RuntimeError("smtp down"),
    ), patch(
        "pecha_api.plans.groups.group_invite_email.logging.exception",
    ) as mock_log:
        send_group_invitation_email(
            target_email="invitee@example.org",
            inviter_name="Alice",
            inviter_email="alice@example.org",
            group_title="Dharma Group",
            invite_role="VIEWER",
        )
    mock_log.assert_called_once()
