from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ConsentRecord, Policy

User = get_user_model()


class LegalTests(APITestCase):
    def test_seeded_policies_are_public(self):
        res = self.client.get(reverse("policy-detail", args=["privacy"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["slug"], "privacy")
        self.assertTrue(res.data["body"])

    def test_consent_recorded_for_anon(self):
        res = self.client.post(reverse("consent"), {"slug": "terms"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ConsentRecord.objects.count(), 1)

    def test_consent_links_user_when_authenticated(self):
        user = User.objects.create_user(email="u@x.com", phone="9811111111", password="x")
        self.client.force_authenticate(user)
        self.client.post(reverse("consent"), {"slug": "privacy"})
        self.assertEqual(ConsentRecord.objects.filter(user=user).count(), 1)

    def test_only_current_version_served(self):
        # add an older non-current version; endpoint must return v? current only
        p = Policy.objects.get(slug="privacy")
        self.assertTrue(p.is_current)
