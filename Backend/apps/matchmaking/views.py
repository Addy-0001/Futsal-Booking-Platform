from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Match, MatchPlayer
from .serializers import CreateMatchSerializer, MatchSerializer
from .services import cancel_match, join_match, leave_match


class MatchViewSet(viewsets.ModelViewSet):
    """Open pickup matches. Anyone can browse; authenticated users host/join."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_fields = ["status", "city", "format", "court"]
    ordering_fields = ["proposed_start", "created_at"]

    def get_queryset(self):
        qs = Match.objects.select_related("host", "court").prefetch_related("players__user")
        # Public browsing shows joinable matches; the rest visible to involved users.
        if self.action == "list" and not self.request.query_params.get("status"):
            return qs.filter(status__in=[Match.Status.OPEN, Match.Status.FULL])
        return qs

    def get_serializer_class(self):
        return CreateMatchSerializer if self.action == "create" else MatchSerializer

    def perform_create(self, serializer):
        match = serializer.save(host=self.request.user)
        # Host is automatically the first player.
        MatchPlayer.objects.create(match=match, user=self.request.user)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        return Response(MatchSerializer(ser.instance).data, status=201)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        join_match(match=self.get_object(), user=request.user)
        return Response(MatchSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        leave_match(match=self.get_object(), user=request.user)
        return Response(MatchSerializer(self.get_object()).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        match = self.get_object()
        if match.host_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied("Only the host can cancel this match.")
        return Response(MatchSerializer(cancel_match(match=match)).data)
