from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import MatchChallenge, Team, TeamMembership

User = get_user_model()


def mk(email, phone):
    return User.objects.create_user(email=email, phone=phone, password="x")


class TeamTests(APITestCase):
    def setUp(self):
        self.capA = mk("capa@x.com", "9811111111")
        self.capB = mk("capb@x.com", "9822222222")
        self.player = mk("player@x.com", "9833333333")

    def make_team(self, captain, name):
        self.client.force_authenticate(captain)
        return self.client.post(reverse("team-list"), {"name": name}).data

    def test_create_team_makes_captain_member(self):
        self.client.force_authenticate(self.capA)
        res = self.client.post(reverse("team-list"), {"name": "Thunder FC"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        team = Team.objects.get(slug=res.data["slug"])
        self.assertTrue(team.is_captain(self.capA))
        self.assertEqual(len(res.data["members"]), 1)

    def test_invite_and_accept(self):
        team = self.make_team(self.capA, "Thunder FC")
        slug = team["slug"]
        # captain invites
        self.client.force_authenticate(self.capA)
        res = self.client.post(reverse("team-invite", args=[slug]), {"user": str(self.player.pk)})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # invitee accepts
        self.client.force_authenticate(self.player)
        res = self.client.post(reverse("team-accept-invite", args=[slug]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["members"]), 2)

    def test_non_captain_cannot_invite(self):
        team = self.make_team(self.capA, "Thunder FC")
        self.client.force_authenticate(self.player)
        res = self.client.post(reverse("team-invite", args=[team["slug"]]),
                               {"user": str(self.capB.pk)})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_captain_cannot_leave(self):
        team = self.make_team(self.capA, "Thunder FC")
        self.client.force_authenticate(self.capA)
        res = self.client.post(reverse("team-leave", args=[team["slug"]]))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ChallengeTests(APITestCase):
    def setUp(self):
        self.capA = mk("capa@x.com", "9811111111")
        self.capB = mk("capb@x.com", "9822222222")
        self.teamA = Team.objects.create(name="Alpha", captain=self.capA)
        TeamMembership.objects.create(team=self.teamA, user=self.capA,
                                      role=TeamMembership.Role.CAPTAIN,
                                      status=TeamMembership.Status.ACTIVE)
        self.teamB = Team.objects.create(name="Bravo", captain=self.capB)
        TeamMembership.objects.create(team=self.teamB, user=self.capB,
                                      role=TeamMembership.Role.CAPTAIN,
                                      status=TeamMembership.Status.ACTIVE)
        self.start = (timezone.now() + timedelta(days=2)).isoformat()

    def propose(self):
        self.client.force_authenticate(self.capA)
        return self.client.post(reverse("challenge-list"), {
            "challenger_team": str(self.teamA.pk),
            "opponent_team": str(self.teamB.pk),
            "proposed_start": self.start,
        })

    def test_full_war_flow(self):
        res = self.propose()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        cid = res.data["id"]
        # opponent captain accepts
        self.client.force_authenticate(self.capB)
        res = self.client.post(reverse("challenge-accept", args=[cid]))
        self.assertEqual(res.data["status"], MatchChallenge.Status.ACCEPTED)
        # record result
        res = self.client.post(reverse("challenge-result", args=[cid]),
                               {"challenger_score": 3, "opponent_score": 2})
        self.assertEqual(res.data["status"], MatchChallenge.Status.PLAYED)
        self.assertEqual(res.data["challenger_score"], 3)

    def test_only_opponent_captain_accepts(self):
        cid = self.propose().data["id"]
        # challenger tries to accept own challenge
        self.client.force_authenticate(self.capA)
        res = self.client.post(reverse("challenge-accept", args=[cid]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_challenge_self(self):
        self.client.force_authenticate(self.capA)
        res = self.client.post(reverse("challenge-list"), {
            "challenger_team": str(self.teamA.pk),
            "opponent_team": str(self.teamA.pk),
            "proposed_start": self.start,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
