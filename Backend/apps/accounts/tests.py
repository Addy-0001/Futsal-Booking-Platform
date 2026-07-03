from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .tokens import email_verification_token, encode_uid, password_reset_token

User = get_user_model()


class AuthFlowTests(APITestCase):
    def _register(self, **over):
        payload = {
            "email": "player@example.com",
            "phone": "9812345678",
            "full_name": "Test Player",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        payload.update(over)
        return self.client.post(reverse("accounts:register"), payload)

    def test_register_sends_verification_and_creates_user(self):
        res = self._register()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="player@example.com")
        self.assertFalse(user.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_mismatch_rejected(self):
        res = self._register(password_confirm="different")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_tokens_and_user(self):
        self._register()
        res = self.client.post(reverse("accounts:login"),
                               {"email": "player@example.com", "password": "StrongPass123!"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["email"], "player@example.com")

    def test_email_verification(self):
        self._register()
        user = User.objects.get(email="player@example.com")
        res = self.client.post(reverse("accounts:verify-email"),
                               {"uid": encode_uid(user),
                                "token": email_verification_token.make_token(user)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_password_reset_flow(self):
        self._register()
        user = User.objects.get(email="player@example.com")
        # request (does not reveal existence)
        res = self.client.post(reverse("accounts:password-reset"),
                               {"email": "player@example.com"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # confirm
        res = self.client.post(reverse("accounts:password-reset-confirm"),
                               {"uid": encode_uid(user),
                                "token": password_reset_token.make_token(user),
                                "new_password": "BrandNewPass456!"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("BrandNewPass456!"))

    def test_reset_token_is_single_use(self):
        self._register()
        user = User.objects.get(email="player@example.com")
        token = password_reset_token.make_token(user)
        uid = encode_uid(user)
        first = self.client.post(reverse("accounts:password-reset-confirm"),
                                 {"uid": uid, "token": token, "new_password": "BrandNewPass456!"})
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        # reusing the same token after the password changed must fail
        second = self.client.post(reverse("accounts:password-reset-confirm"),
                                  {"uid": uid, "token": token, "new_password": "AnotherPass789!"})
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get(reverse("accounts:me")).status_code,
                         status.HTTP_401_UNAUTHORIZED)
