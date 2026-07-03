from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.futsals.models import Futsal

from .models import EventLog
from .serializers import EventIngestSerializer


class EventIngestView(APIView):
    """POST /api/events/ — first-party event + page tracking. Accepts anonymous events."""

    permission_classes = [AllowAny]
    throttle_scope = "anon"

    def post(self, request):
        ser = EventIngestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        EventLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=ser.validated_data["name"],
            path=ser.validated_data.get("path", ""),
            session_id=ser.validated_data.get("session_id", ""),
            props=ser.validated_data.get("props", {}) or {},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


REVENUE_STATUSES = (Booking.Status.APPROVED, Booking.Status.COMPLETED)
DEMAND_STATUSES = (Booking.Status.PENDING, *REVENUE_STATUSES)


class ManagerStatsView(APIView):
    """
    GET /api/manage/stats/?days=30[&futsal=<uuid>]

    Aggregated dashboard numbers for the venues the caller manages. All series
    are computed in the database (a handful of GROUP BY queries) so neither
    side pushes booking rows around just to draw a chart.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            days = min(max(int(request.query_params.get("days", 30)), 7), 90)
        except ValueError:
            days = 30

        managed = Futsal.objects.filter(roles__user=request.user).distinct()
        futsal_id = request.query_params.get("futsal")
        if futsal_id:
            managed = managed.filter(pk=futsal_id)

        now = timezone.now()
        local_today = timezone.localdate()
        since = now - timedelta(days=days)

        qs = Booking.objects.filter(court__futsal__in=managed)
        period = qs.filter(created_at__gte=since)

        # ---- Headline totals (single aggregate query each) ----
        totals = qs.aggregate(
            pending=Count("id", filter=Q(status=Booking.Status.PENDING)),
            upcoming=Count("id", filter=Q(start_at__gte=now, status__in=Booking.ACTIVE_STATUSES)),
            revenue_confirmed=Sum("price_at_booking", filter=Q(status__in=REVENUE_STATUSES)),
        )
        period_totals = period.aggregate(
            bookings=Count("id"),
            revenue=Sum("price_at_booking", filter=Q(status__in=REVENUE_STATUSES)),
            cancelled=Count("id", filter=Q(status__in=(Booking.Status.CANCELLED, Booking.Status.REJECTED))),
        )

        # ---- Daily series (bookings created + revenue per local day, zero-filled) ----
        daily_rows = (
            period.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                bookings=Count("id"),
                revenue=Sum("price_at_booking", filter=Q(status__in=REVENUE_STATUSES)),
            )
        )
        by_day = {r["day"]: r for r in daily_rows}
        daily = []
        for i in range(days - 1, -1, -1):
            d = local_today - timedelta(days=i)
            row = by_day.get(d)
            daily.append({
                "date": d.isoformat(),
                "bookings": row["bookings"] if row else 0,
                "revenue": float(row["revenue"] or 0) if row else 0.0,
            })

        # ---- Status breakdown over the period ----
        by_status = {
            r["status"]: r["n"]
            for r in period.values("status").annotate(n=Count("id"))
        }

        # ---- Peak hours (local kickoff hour, demand = pending/approved/completed) ----
        peak_rows = (
            period.filter(status__in=DEMAND_STATUSES)
            .annotate(hour=ExtractHour("start_at"))
            .values("hour")
            .annotate(bookings=Count("id"))
        )
        by_hour = {r["hour"]: r["bookings"] for r in peak_rows}
        peak_hours = [{"hour": h, "bookings": by_hour.get(h, 0)} for h in range(24)]

        # ---- Top courts over the period ----
        by_court = list(
            period.values("court_id", "court__name", "court__futsal__name")
            .annotate(
                bookings=Count("id"),
                revenue=Sum("price_at_booking", filter=Q(status__in=REVENUE_STATUSES)),
            )
            .order_by("-bookings")[:8]
        )
        by_court = [
            {
                "court": str(r["court_id"]),
                "name": r["court__name"],
                "futsal_name": r["court__futsal__name"],
                "bookings": r["bookings"],
                "revenue": float(r["revenue"] or 0),
            }
            for r in by_court
        ]

        bookings_period = period_totals["bookings"] or 0
        return Response({
            "days": days,
            "totals": {
                "venues": managed.count(),
                "pending": totals["pending"] or 0,
                "upcoming": totals["upcoming"] or 0,
                "revenue_confirmed": float(totals["revenue_confirmed"] or 0),
            },
            "period": {
                "bookings": bookings_period,
                "revenue": float(period_totals["revenue"] or 0),
                "cancelled": period_totals["cancelled"] or 0,
                "weekly_avg_bookings": round(bookings_period / days * 7, 1),
                "daily_avg_bookings": round(bookings_period / days, 1),
            },
            "daily": daily,
            "by_status": by_status,
            "peak_hours": peak_hours,
            "by_court": by_court,
        })
