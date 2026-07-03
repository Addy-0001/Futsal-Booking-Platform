from datetime import time, timedelta
from decimal import Decimal
from unittest import skipUnless
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.futsals.models import Court, Futsal, FutsalRole, OperatingHours

from .exceptions import SlotInPast, SlotUnavailable
from .models import Booking
from .services import cancel_booking, create_booking

User = get_user_model()
KTM = ZoneInfo("Asia/Kathmandu")


def future_slot(days=2, hour=18, dur=1):
    base = (timezone.now().astimezone(KTM) + timedelta(days=days)).replace(
        hour=hour, minute=0, second=0, microsecond=0)
    return base, base + timedelta(hours=dur)


class BookingTestBase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@x.com", phone="9811111111", password="x")
        self.player = User.objects.create_user(email="player@x.com", phone="9822222222", password="x")
        self.other = User.objects.create_user(email="other@x.com", phone="9833333333", password="x")
        self.futsal = Futsal.objects.create(name="F", created_by=self.owner,
                                             status=Futsal.Status.ACTIVE, timezone="Asia/Kathmandu")
        FutsalRole.objects.create(user=self.owner, futsal=self.futsal, role=FutsalRole.Role.OWNER)
        self.court = Court.objects.create(futsal=self.futsal, name="C", default_price=Decimal("1000"))
        for wd in range(7):
            OperatingHours.objects.create(court=self.court, weekday=wd,
                                          open_time=time(6, 0), close_time=time(23, 0))

    def book(self, user=None, **over):
        start, end = future_slot()
        data = {"court": str(self.court.pk), "start_at": over.get("start", start).isoformat(),
                "end_at": over.get("end", end).isoformat()}
        self.client.force_authenticate(user or self.player)
        return self.client.post(reverse("booking-list"), data)


class BookingCreateTests(BookingTestBase):
    def test_create_is_pending_with_price_snapshot(self):
        res = self.book()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], Booking.Status.PENDING)
        self.assertEqual(Decimal(res.data["price_at_booking"]), Decimal("1000"))

    def test_cannot_book_in_past(self):
        start = (timezone.now().astimezone(KTM) - timedelta(days=1)).replace(hour=18, minute=0,
                                                                             second=0, microsecond=0)
        res = self.book(start=start, end=start + timedelta(hours=1))
        self.assertEqual(res.status_code, SlotInPast.status_code)

    def test_outside_operating_hours_rejected(self):
        start, end = future_slot(hour=3)  # 03:00, before 06:00 open
        res = self.book(start=start, end=end)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_booking_same_slot_conflicts(self):
        self.assertEqual(self.book().status_code, status.HTTP_201_CREATED)
        # second player, identical slot
        res = self.book(user=self.other)
        self.assertEqual(res.status_code, SlotUnavailable.status_code)  # 409

    def test_cancel_frees_slot_for_rebooking(self):
        first = self.book()
        booking = Booking.objects.get(pk=first.data["id"])
        cancel_booking(booking=booking, reason="changed my mind")
        # slot is free again
        res = self.book(user=self.other)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class BookingLifecycleTests(BookingTestBase):
    def _make(self):
        return Booking.objects.get(pk=self.book().data["id"])

    def test_staff_can_approve(self):
        b = self._make()
        self.client.force_authenticate(self.owner)
        res = self.client.post(reverse("booking-approve", args=[b.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Booking.Status.APPROVED)

    def test_player_cannot_approve_own_booking(self):
        b = self._make()
        self.client.force_authenticate(self.player)
        res = self.client.post(reverse("booking-approve", args=[b.pk]))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_reschedule_moves_slot_and_resets_to_pending(self):
        b = self._make()
        self.client.force_authenticate(self.owner)
        self.client.post(reverse("booking-approve", args=[b.pk]))
        # player reschedules to a different hour
        ns, ne = future_slot(hour=20)
        self.client.force_authenticate(self.player)
        res = self.client.post(reverse("booking-reschedule", args=[b.pk]),
                               {"start_at": ns.isoformat(), "end_at": ne.isoformat()})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["status"], Booking.Status.PENDING)

    def test_user_only_sees_own_bookings(self):
        self._make()  # player's booking
        self.client.force_authenticate(self.other)
        res = self.client.get(reverse("booking-list"))
        self.assertEqual(res.data["count"], 0)

    def test_owner_sees_venue_bookings(self):
        self._make()
        self.client.force_authenticate(self.owner)
        res = self.client.get(reverse("booking-list"))
        self.assertEqual(res.data["count"], 1)


class AvailabilityTests(BookingTestBase):
    def test_grid_marks_taken_slot(self):
        first = self.book()  # books the 18:00 slot (default future_slot)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=first.data["id"])
        date = booking.start_at.astimezone(KTM).date()

        res = self.client.get(reverse("availability"),
                              {"court": str(self.court.pk), "date": date.isoformat()})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["is_open"])
        taken = [s for s in res.data["slots"] if s["status"] == "taken"]
        free = [s for s in res.data["slots"] if s["status"] == "free"]
        self.assertEqual(len(taken), 1)            # exactly the booked hour
        self.assertTrue(len(free) > 0)             # other hours still open
        self.assertEqual(Decimal(taken[0]["price"]), Decimal("1000"))

    def test_closed_day_returns_no_slots(self):
        from apps.futsals.models import ClosureException
        date = (timezone.now().astimezone(KTM) + timedelta(days=2)).date()
        ClosureException.objects.create(court=self.court, date=date, reason="Holiday")
        res = self.client.get(reverse("availability"),
                              {"court": str(self.court.pk), "date": date.isoformat()})
        self.assertFalse(res.data["is_open"])
        self.assertEqual(res.data["slots"], [])


class ConcurrencyTests(BookingTestBase):
    @skipUnless(connection.vendor == "postgresql",
                "Exclusion constraint race only enforced on PostgreSQL")
    def test_parallel_inserts_only_one_wins(self):
        import threading

        start, end = future_slot()
        results = []

        def attempt(user):
            try:
                create_booking(user=user, court=self.court, start=start, end=end)
                results.append("ok")
            except SlotUnavailable:
                results.append("conflict")

        t1 = threading.Thread(target=attempt, args=(self.player,))
        t2 = threading.Thread(target=attempt, args=(self.other,))
        t1.start(); t2.start(); t1.join(); t2.join()

        self.assertEqual(sorted(results), ["conflict", "ok"])
        self.assertEqual(Booking.objects.filter(status=Booking.Status.PENDING).count(), 1)
