from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import MatchChallenge, Team, TeamMembership
from .serializers import (
    ChallengeSerializer,
    InviteSerializer,
    ResultSerializer,
    TeamSerializer,
)


class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"
    search_fields = ["name"]

    def get_queryset(self):
        return Team.objects.select_related("captain").prefetch_related("memberships__user")

    def perform_create(self, serializer):
        team = serializer.save(captain=self.request.user)
        TeamMembership.objects.create(
            team=team, user=self.request.user,
            role=TeamMembership.Role.CAPTAIN, status=TeamMembership.Status.ACTIVE,
        )

    def _require_captain(self, team):
        if not team.is_captain(self.request.user) and not self.request.user.is_staff:
            raise PermissionDenied("Only the team captain can do this.")

    def perform_update(self, serializer):
        self._require_captain(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._require_captain(instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    def invite(self, request, slug=None):
        team = self.get_object()
        self._require_captain(team)
        ser = InviteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = ser.validated_data.get("email")
        invitee = (User.objects.filter(email=email.lower()).first() if email
                   else User.objects.filter(pk=ser.validated_data.get("user")).first())
        if not invitee:
            raise ValidationError("No user found with that email.")

        membership, created = TeamMembership.objects.get_or_create(
            team=team, user=invitee,
            defaults={"status": TeamMembership.Status.INVITED},
        )
        if not created and membership.status == TeamMembership.Status.LEFT:
            membership.status = TeamMembership.Status.INVITED
            membership.save(update_fields=["status", "updated_at"])
        return Response(TeamSerializer(team).data, status=201)

    @action(detail=True, methods=["post"], url_path="accept-invite")
    def accept_invite(self, request, slug=None):
        team = self.get_object()
        m = team.memberships.filter(user=request.user, status=TeamMembership.Status.INVITED).first()
        if not m:
            raise ValidationError("You have no pending invite for this team.")
        m.status = TeamMembership.Status.ACTIVE
        m.save(update_fields=["status", "updated_at"])
        return Response(TeamSerializer(team).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, slug=None):
        team = self.get_object()
        if team.is_captain(request.user):
            raise ValidationError("The captain can't leave; transfer captaincy or delete the team.")
        m = team.memberships.filter(user=request.user, status=TeamMembership.Status.ACTIVE).first()
        if not m:
            raise ValidationError("You're not an active member of this team.")
        m.status = TeamMembership.Status.LEFT
        m.save(update_fields=["status", "updated_at"])
        return Response(TeamSerializer(team).data)


class ChallengeViewSet(viewsets.ModelViewSet):
    serializer_class = ChallengeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "challenger_team", "opponent_team"]

    def get_queryset(self):
        user = self.request.user
        qs = MatchChallenge.objects.select_related("challenger_team", "opponent_team")
        if user.is_staff:
            return qs
        # Challenges involving any team the user captains or actively plays for.
        return qs.filter(
            Q(challenger_team__captain=user) | Q(opponent_team__captain=user)
            | Q(challenger_team__memberships__user=user,
                challenger_team__memberships__status=TeamMembership.Status.ACTIVE)
            | Q(opponent_team__memberships__user=user,
                opponent_team__memberships__status=TeamMembership.Status.ACTIVE)
        ).distinct()

    def perform_create(self, serializer):
        challenger = serializer.validated_data["challenger_team"]
        opponent = serializer.validated_data["opponent_team"]
        if not challenger.is_captain(self.request.user):
            raise PermissionDenied("Only the challenger team's captain can propose a challenge.")
        if challenger == opponent:
            raise ValidationError("A team cannot challenge itself.")
        serializer.save(created_by=self.request.user, status=MatchChallenge.Status.PROPOSED)

    def _respond(self, request, new_status):
        challenge = self.get_object()
        if not challenge.opponent_team.is_captain(request.user):
            raise PermissionDenied("Only the opponent captain can respond.")
        if challenge.status != MatchChallenge.Status.PROPOSED:
            raise ValidationError("This challenge has already been responded to.")
        challenge.status = new_status
        challenge.responded_by = request.user
        challenge.save(update_fields=["status", "responded_by", "updated_at"])
        return challenge

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return Response(ChallengeSerializer(
            self._respond(request, MatchChallenge.Status.ACCEPTED)).data)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        return Response(ChallengeSerializer(
            self._respond(request, MatchChallenge.Status.DECLINED)).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        challenge = self.get_object()
        if not challenge.challenger_team.is_captain(request.user):
            raise PermissionDenied("Only the challenger captain can cancel.")
        if challenge.status in (MatchChallenge.Status.PLAYED, MatchChallenge.Status.CANCELLED):
            raise ValidationError("This challenge can no longer be cancelled.")
        challenge.status = MatchChallenge.Status.CANCELLED
        challenge.save(update_fields=["status", "updated_at"])
        return Response(ChallengeSerializer(challenge).data)

    @action(detail=True, methods=["post"])
    def result(self, request, pk=None):
        challenge = self.get_object()
        captains = (challenge.challenger_team.is_captain(request.user)
                    or challenge.opponent_team.is_captain(request.user))
        if not captains:
            raise PermissionDenied("Only a participating captain can record the result.")
        if challenge.status not in (MatchChallenge.Status.ACCEPTED, MatchChallenge.Status.SCHEDULED):
            raise ValidationError("Only accepted/scheduled challenges can have a result.")
        ser = ResultSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        challenge.challenger_score = ser.validated_data["challenger_score"]
        challenge.opponent_score = ser.validated_data["opponent_score"]
        challenge.status = MatchChallenge.Status.PLAYED
        challenge.save(update_fields=["challenger_score", "opponent_score", "status", "updated_at"])
        return Response(ChallengeSerializer(challenge).data)
