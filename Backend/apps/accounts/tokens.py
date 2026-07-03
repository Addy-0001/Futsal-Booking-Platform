"""
Token helpers for email verification and password reset.

Both use Django's PasswordResetTokenGenerator machinery:
- single-use by construction (the hash folds in mutable user state, so once the
  action succeeds the same token no longer validates)
- expiry enforced by settings.PASSWORD_RESET_TIMEOUT (1800s = 30 min)
"""
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator,
)
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Token invalidates once the email is verified (state folded into the hash)."""

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_email_verified}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()
# Password reset reuses Django's default generator (folds in password hash + last_login).
password_reset_token = default_token_generator


def encode_uid(user):
    return urlsafe_base64_encode(force_bytes(str(user.pk)))


def decode_uid(uidb64):
    return force_str(urlsafe_base64_decode(uidb64))
