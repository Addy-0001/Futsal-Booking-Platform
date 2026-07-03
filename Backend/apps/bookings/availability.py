"""
Public court availability — generates the bookable slot grid the frontend renders.
Returns per-slot price (server-authoritative) and free/taken/past status, with
occupied slots anonymized (no booker identity leaked).
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.futsals.models import Court, Futsal
from apps.pricing.services import resolve_price

from .models import Booking

MAX_SLOT_MINUTES = 240
MIN_SLOT_MINUTES = 30


class AvailabilityQuerySerializer(serializers.Serializer):
    court = serializers.UUIDField()
    date = serializers.DateField()
    slot_minutes = serializers.IntegerField(
        required=False, default=60, min_value=MIN_SLOT_MINUTES, max_value=MAX_SLOT_MINUTES
    )


class AvailabilityView(APIView):
    """GET /api/availability/?court=<uuid>&date=YYYY-MM-DD[&slot_minutes=60]"""

    permission_classes = [AllowAny]

    def get(self, request):
        q = AvailabilityQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        court = get_object_or_404(
            Court.objects.select_related("futsal"),
            pk=q.validated_data["court"], is_active=True,
            futsal__status=Futsal.Status.ACTIVE,
        )
        date = q.validated_data["date"]
        step = timedelta(minutes=q.validated_data["slot_minutes"])
        tz = ZoneInfo(court.futsal.timezone)
        weekday = date.weekday()

        closed = court.closures.filter(date=date).exists()
        hours = court.operating_hours.filter(weekday=weekday).first()
        if closed or hours is None:
            return Response({
                "court": str(court.pk), "date": date, "is_open": False,
                "open_time": None, "close_time": None, "slots": [],
            })

        # Active bookings overlapping this calendar day (single query).
        day_start = datetime.combine(date, time.min, tzinfo=tz)
        day_end = day_start + timedelta(days=1)
        occupied = list(
            Booking.objects.filter(
                court=court, status__in=Booking.ACTIVE_STATUSES,
                start_at__lt=day_end, end_at__gt=day_start,
            ).values_list("start_at", "end_at")
        )

        now = timezone.now()
        cursor = datetime.combine(date, hours.open_time, tzinfo=tz)
        limit = datetime.combine(date, hours.close_time, tzinfo=tz)
        slots = []
        while cursor + step <= limit:
            start, end = cursor, cursor + step
            taken = any(os < end and oe > start for os, oe in occupied)
            past = start <= now
            slots.append({
                "start_at": start,
                "end_at": end,
                "price": resolve_price(court, start),
                "status": "taken" if taken else ("past" if past else "free"),
                "available": not taken and not past,
            })
            cursor += step

        return Response({
            "court": str(court.pk),
            "date": date,
            "is_open": True,
            "open_time": hours.open_time,
            "close_time": hours.close_time,
            "currency": "NPR",
            "slots": slots,
        })
