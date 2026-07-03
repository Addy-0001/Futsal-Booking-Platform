from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .permissions import IsBookingParty, is_booking_party, is_futsal_staff
from .serializers import (
    BookingActionSerializer,
    BookingSerializer,
    CreateBookingSerializer,
    RescheduleSerializer,
)
from .services import (
    approve_booking,
    cancel_booking,
    complete_booking,
    create_booking,
    reject_booking,
    reschedule_booking,
)


class BookingViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    Players create/cancel/reschedule their own bookings; venue staff see and
    approve/reject bookings for futsals they manage. History is strictly per-user.
    """

    permission_classes = [IsAuthenticated, IsBookingParty]
    serializer_class = BookingSerializer
    filterset_fields = {
        "status": ["exact"],
        "court": ["exact"],
        "court__futsal": ["exact"],
        "start_at": ["gte", "lt"],
    }
    ordering_fields = ["start_at", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.select_related("court", "court__futsal", "user")
        if user.is_staff:
            return qs
        # Own bookings OR bookings at any futsal the user is staff of.
        return qs.filter(Q(user=user) | Q(court__futsal__roles__user=user)).distinct()

    def create(self, request, *args, **kwargs):
        ser = CreateBookingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = create_booking(
            user=request.user,
            court=ser.validated_data["court"],
            start=ser.validated_data["start_at"],
            end=ser.validated_data["end_at"],
            note=ser.validated_data.get("note", ""),
        )
        return Response(BookingSerializer(booking).data, status=201)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()  # enforces IsBookingParty
        ser = BookingActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = cancel_booking(booking=booking, reason=ser.validated_data.get("reason", ""))
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        booking = self.get_object()
        if booking.user_id != request.user.id and not is_futsal_staff(request.user, booking):
            raise PermissionDenied("Only the player or venue staff can reschedule this booking.")
        ser = RescheduleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = reschedule_booking(
            booking=booking,
            start=ser.validated_data["start_at"],
            end=ser.validated_data["end_at"],
        )
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        booking = self._staff_only(request)
        booking = approve_booking(booking=booking, approver=request.user)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self._staff_only(request)
        booking = complete_booking(booking=booking)
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        booking = self._staff_only(request)
        ser = BookingActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        booking = reject_booking(booking=booking, approver=request.user,
                                 reason=ser.validated_data.get("reason", ""))
        return Response(BookingSerializer(booking).data)

    def _staff_only(self, request):
        booking = self.get_object()
        if not is_futsal_staff(request.user, booking):
            raise PermissionDenied("Only venue staff can approve or reject bookings.")
        return booking
