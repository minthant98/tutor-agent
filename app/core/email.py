"""
Resend-backed transactional email.

All sends are non-blocking and silently no-op if RESEND_API_KEY is unset,
so the auth flow never breaks because of email infrastructure.
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.resend_api_key:
        return None
    try:
        import resend
        resend.api_key = settings.resend_api_key
        _client = resend
        logger.info("Resend email client initialised")
    except Exception as e:
        logger.warning("Resend init failed: %s", e)
        _client = None
    return _client


def send_email(to: str, subject: str, html: str) -> bool:
    """Send a transactional email. Returns True on success, False if disabled or failed."""
    client = _get_client()
    if not client:
        logger.warning("Email not sent (Resend disabled): %s to %s", subject, to)
        return False
    try:
        params: dict[str, Any] = {
            "from": settings.resend_from_email,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        client.Emails.send(params)
        logger.info("Email sent: %s to %s", subject, to)
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e, exc_info=True)
        return False


def password_reset_email(name: str, reset_link: str) -> tuple[str, str]:
    """Returns (subject, html) for the password reset email."""
    subject = "Reset your Stride password"
    html = f"""
<!DOCTYPE html>
<html>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 40px 20px; color: #0F172A;">
    <div style="margin-bottom: 32px;">
      <span style="font-size: 24px; font-weight: bold; color: #0F172A;">Stride</span>
    </div>

    <h1 style="font-size: 24px; margin: 0 0 16px; color: #0F172A;">Reset your password</h1>

    <p style="color: #475569; line-height: 1.6; margin: 0 0 24px;">
      Hi {name},<br><br>
      We received a request to reset your Stride password. Click the button below to choose a new password. This link expires in <strong>1 hour</strong>.
    </p>

    <a href="{reset_link}"
       style="display: inline-block; background: #0F172A; color: white; text-decoration: none; padding: 14px 28px; border-radius: 12px; font-weight: 600; font-size: 14px;">
      Reset password →
    </a>

    <p style="color: #94A3B8; font-size: 13px; line-height: 1.6; margin: 32px 0 0;">
      If you didn't request this, you can safely ignore this email — your password won't change.
    </p>

    <p style="color: #94A3B8; font-size: 12px; margin: 24px 0 0;">
      Or copy and paste this link into your browser:<br>
      <span style="word-break: break-all;">{reset_link}</span>
    </p>

    <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 32px 0;">
    <p style="color: #94A3B8; font-size: 12px; margin: 0;">
      Stride — Your AI Learning Companion
    </p>
  </body>
</html>
"""
    return subject, html
