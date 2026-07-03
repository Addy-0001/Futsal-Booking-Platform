from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SupportTicket

User = get_user_model()


class SupportTests(APITestCase):
    def test_anyone_can_file_a_ticket(self):
        res = self.client.post(reverse("supportticket-list"), {
            "type": "BUG", "email": "a@x.com", "subject": "Broken button",
            "message": "The book button fails.", "url": "/futsals/abc",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SupportTicket.objects.get().status, SupportTicket.Status.OPEN)

    def test_listing_requires_staff(self):
        SupportTicket.objects.create(type="SUPPORT", subject="s", message="m")
        # anonymous
        self.assertIn(self.client.get(reverse("supportticket-list")).status_code,
                      (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        # normal user
        user = User.objects.create_user(email="u@x.com", phone="9811111111", password="x")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get(reverse("supportticket-list")).status_code,
                         status.HTTP_403_FORBIDDEN)
        # staff
        admin = User.objects.create_superuser(email="admin@x.com", phone="9899999999", password="x")
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(reverse("supportticket-list")).status_code,
                         status.HTTP_200_OK)
