from unittest.mock import patch

from pecha_api.plans.transfers.transfer_invite_email import (
    _build_transfer_invitation_html,
    _transfer_expiry_label,
    send_content_transfer_invitation_email,
)


def test_transfer_expiry_label_plural_minutes():
    with patch("pecha_api.plans.transfers.transfer_invite_email.get_int", return_value=30):
        assert _transfer_expiry_label() == "30 minutes"


def test_transfer_expiry_label_singular_minute():
    with patch("pecha_api.plans.transfers.transfer_invite_email.get_int", return_value=1):
        assert _transfer_expiry_label() == "1 minute"


def test_build_transfer_invitation_html_contains_transfer_details():
    html = _build_transfer_invitation_html(
        requester_name="Alice",
        requester_email="alice@example.org",
        entity_label="plan",
        entity_title="Morning Practice",
        from_group_title="Source Group",
        to_group_title="Target Group",
        transfers_url="https://studio.webuddhist.com/transfers",
        logo_url="https://example.com/logo.png",
    )
    assert "Morning Practice" in html
    assert "Source Group" in html
    assert "Target Group" in html
    assert "alice@example.org" in html


def test_send_content_transfer_invitation_email_success():
    with patch("pecha_api.plans.transfers.transfer_invite_email.get", side_effect=lambda key: {
        "WEBUDDHIST_STUDIO_BASE_URL": "https://studio.webuddhist.com",
        "WEBUDDHIST_EMAIL_LOGO_URL": "https://example.com/logo.png",
    }[key]), patch(
        "pecha_api.plans.transfers.transfer_invite_email.get_int",
        return_value=30,
    ), patch(
        "pecha_api.plans.transfers.transfer_invite_email.send_email",
    ) as mock_send:
        send_content_transfer_invitation_email(
            target_email="owner@example.org",
            requester_name="Alice",
            requester_email="alice@example.org",
            entity_label="plan",
            entity_title="Morning Practice",
            from_group_title="Source Group",
            to_group_title="Target Group",
        )
    mock_send.assert_called_once()
    assert "Morning Practice" in mock_send.call_args.kwargs["message"]


def test_send_content_transfer_invitation_email_logs_failure():
    with patch("pecha_api.plans.transfers.transfer_invite_email.get", side_effect=lambda key: {
        "WEBUDDHIST_STUDIO_BASE_URL": "https://studio.webuddhist.com/",
        "WEBUDDHIST_EMAIL_LOGO_URL": "https://example.com/logo.png",
    }[key]), patch(
        "pecha_api.plans.transfers.transfer_invite_email.get_int",
        return_value=30,
    ), patch(
        "pecha_api.plans.transfers.transfer_invite_email.send_email",
        side_effect=RuntimeError("smtp down"),
    ), patch(
        "pecha_api.plans.transfers.transfer_invite_email.logging.exception",
    ) as mock_log:
        send_content_transfer_invitation_email(
            target_email="owner@example.org",
            requester_name="Alice",
            requester_email="alice@example.org",
            entity_label="series",
            entity_title="Evening Series",
            from_group_title="Source Group",
            to_group_title="Target Group",
        )
    mock_log.assert_called_once()
