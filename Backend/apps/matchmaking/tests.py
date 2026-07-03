from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Match, MatchPlayer

User = get_user_model()


def mk(email, phone):
    return User.objects.create_user(email=email, phone=phone, password="x")


class MatchmakingTests(APITestCase):
    def setUp(self):
        self.host = mk("host@x.com", "9811111111")
        self.p2 = mk("p2@x.com", "9822222222")
        self.p3 = mk("p3@x.com", "9833333333")
        self.start = (timezone.now() + timedelta(days=1)).isoformat()

    def create_match(self, user, max_players=2):
        self.client.force_authenticate(user)
        return self.client.post(reverse("match-list"),
                                {"proposed_start": self.start, "format": "5s",
                                 "max_players": max_players})

    def test_host_auto_joins_on_create(self):
        res = self.create_match(self.host)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["joined_count"], 1)

    def test_join_fills_and_blocks_extra(self):
        match_id = self.create_match(self.host, max_players=2).data["id"]
        # p2 joins -> match becomes FULL (host + p2 = 2)
        self.client.force_authenticate(self.p2)
        res = self.client.post(reverse("match-join", args=[match_id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Match.Status.FULL)
        # p3 cannot join a full match
        self.client.force_authenticate(self.p3)
        res = self.client.post(reverse("match-join", args=[match_id]))
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_leave_reopens_full_match(self):
        match_id = self.create_match(self.host, max_players=2).data["id"]
        self.client.force_authenticate(self.p2)
        self.client.post(reverse("match-join", args=[match_id]))
        res = self.client.post(reverse("match-leave", args=[match_id]))
        self.assertEqual(res.data["status"], Match.Status.OPEN)

    def test_host_cannot_leave(self):
        match_id = self.create_match(self.host).data["id"]
        self.client.force_authenticate(self.host)
        res = self.client.post(reverse("match-leave", args=[match_id]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_host_cancels(self):
        match_id = self.create_match(self.host).data["id"]
        self.client.force_authenticate(self.p2)
        res = self.client.post(reverse("match-cancel", args=[match_id]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_list_shows_open_matches(self):
        self.create_match(self.host)
        self.client.force_authenticate(user=None)
        res = self.client.get(reverse("match-list"))
        self.assertEqual(res.data["count"], 1)
