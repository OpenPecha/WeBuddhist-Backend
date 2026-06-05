import logging

from pecha_api.config import get, get_int
from pecha_api.notification.email_provider import send_email
from pecha_api.plans.groups.group_invite_email import (
    BRAND_PRIMARY,
    SHELL_LIGHT,
    TEXT_MUTED,
)


def _transfer_expiry_label() -> str:
    minutes = get_int("GROUP_INVITE_EXPIRY_MINUTES")
    minutes = max(1, min(minutes, 24 * 60))
    if minutes == 1:
        return "1 minute"
    return f"{minutes} minutes"


def _build_transfer_invitation_html(
    *,
    requester_name: str,
    requester_email: str,
    entity_label: str,
    entity_title: str,
    from_group_title: str,
    to_group_title: str,
    transfers_url: str,
    logo_url: str,
) -> str:
    expiry_label = _transfer_expiry_label()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Content transfer invitation</title>
</head>
<body style="margin:0;padding:0;background-color:{SHELL_LIGHT};font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:{SHELL_LIGHT};padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          <tr>
            <td style="background-color:#181818;padding:28px 32px;text-align:center;">
              <img src="{logo_url}" alt="WeBuddhist" width="56" height="56" style="display:block;margin:0 auto 12px;border-radius:8px;" />
              <p style="margin:0;font-size:18px;font-weight:600;color:#ffffff;letter-spacing:0.02em;">WeBuddhist Studio</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <h1 style="margin:0 0 16px;font-size:22px;font-weight:700;color:#1a1a1a;">Content transfer request</h1>
              <p style="margin:0 0 20px;font-size:16px;line-height:1.6;color:#333333;">
                <strong>{requester_name}</strong>
                (<a href="mailto:{requester_email}" style="color:{BRAND_PRIMARY};text-decoration:none;">{requester_email}</a>)
                requested to transfer {entity_label} <strong>{entity_title}</strong>
                from <strong>{from_group_title}</strong> to <strong>{to_group_title}</strong>.
              </p>
              <table role="presentation" cellspacing="0" cellpadding="0" align="center" style="margin:0 auto 24px;">
                <tr>
                  <td style="border-radius:8px;background-color:{BRAND_PRIMARY};">
                    <a href="{transfers_url}" target="_blank" rel="noopener noreferrer"
                       style="display:inline-block;padding:14px 32px;font-size:16px;font-weight:600;color:#ffffff;text-decoration:none;">
                      Review transfer
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 8px;font-size:14px;line-height:1.5;color:{TEXT_MUTED};">
                If the button does not work, copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 24px;font-size:14px;word-break:break-all;">
                <a href="{transfers_url}" style="color:{BRAND_PRIMARY};">{transfers_url}</a>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;background-color:#fafafa;border-top:1px solid #eeeeee;">
              <p style="margin:0;font-size:12px;line-height:1.5;color:{TEXT_MUTED};text-align:center;">
                This request expires in {expiry_label}. If you did not expect this email, you can safely ignore it.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_content_transfer_invitation_email(
    *,
    target_email: str,
    requester_name: str,
    requester_email: str,
    entity_label: str,
    entity_title: str,
    from_group_title: str,
    to_group_title: str,
) -> None:
    base_url = get("WEBUDDHIST_STUDIO_BASE_URL").rstrip("/")
    transfers_url = f"{base_url}/transfers"
    logo_url = get("WEBUDDHIST_EMAIL_LOGO_URL")
    subject = f"Content transfer request: {entity_title}"
    html = _build_transfer_invitation_html(
        requester_name=requester_name,
        requester_email=requester_email,
        entity_label=entity_label,
        entity_title=entity_title,
        from_group_title=from_group_title,
        to_group_title=to_group_title,
        transfers_url=transfers_url,
        logo_url=logo_url,
    )
    try:
        send_email(to_email=target_email, subject=subject, message=html)
    except Exception:
        logging.exception("Failed to send content transfer invitation email to %s", target_email)
