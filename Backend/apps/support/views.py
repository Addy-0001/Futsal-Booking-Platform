from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.sanitize import sanitize_html

from .models import SupportTicket, TicketReply
from .serializers import (
    CreateReplySerializer,
    SupportTicketSerializer,
    TicketReplySerializer,
)


class SupportTicketViewSet(mixins.CreateModelMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    """Anyone can open a ticket. Authenticated users see & reply to their own
    threads; staff see everything."""

    serializer_class = SupportTicketSerializer
    filterset_fields = ["type", "status", "priority"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = SupportTicket.objects.select_related("reporter", "department").prefetch_related("replies")
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_staff:
            return qs
        return qs.filter(reporter=user)

    def perform_create(self, serializer):
        serializer.save(
            reporter=self.request.user if self.request.user.is_authenticated else None,
            message=sanitize_html(serializer.validated_data.get("message", "")),
        )

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        ticket = self.get_object()  # queryset already scopes to owner/staff
        is_owner = ticket.reporter_id == request.user.id
        if not (is_owner or request.user.is_staff):
            raise PermissionDenied("You can only reply to your own tickets.")

        ser = CreateReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        is_staff_reply = request.user.is_staff and not is_owner
        reply = TicketReply.objects.create(
            ticket=ticket, author=request.user,
            body=sanitize_html(ser.validated_data["body"]),
            is_staff_reply=is_staff_reply,
        )
        ticket.last_reply_at = timezone.now()
        if is_staff_reply:
            ticket.status = SupportTicket.Status.ANSWERED
        else:
            ticket.status = SupportTicket.Status.CUSTOMER_REPLY
        ticket.save(update_fields=["last_reply_at", "status", "updated_at"])
        return Response(TicketReplySerializer(reply, context={"request": request}).data, status=201)
