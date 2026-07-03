"""
Outbound auth emails. Kept sync-simple here; in prod these are dispatched via
Celery (see notifications app) so a slow SMTP server never blocks the request.
"""
from django.conf import settings
from django.core.mail import send_mail

from .tokens import email_verification_token, encode_uid, password_reset_token


def _link(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


def send_verification_email(user):
    uid = encode_uid(user)
    token = email_verification_token.make_token(user)
    link = _link(f"/verify-email?uid={uid}&token={token}")
    send_mail(
        subject="Verify your Booksall account",
        message=f"Welcome to Booksall!\n\nVerify your email: {link}\n\n"
                f"This link expires in 30 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    uid = encode_uid(user)
    token = password_reset_token.make_token(user)
    link = _link(f"/reset-password?uid={uid}&token={token}")
    send_mail(
        subject="Reset your Booksall password",
        message=f"Reset your password: {link}\n\n"
                f"This link expires in 30 minutes. If you didn't request this, ignore it.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
