"""
Booking service layer — the only correct way to create/mutate bookings.

Concurrency model (design doc §5):
- The hard guarantee is a Postgres exclusion constraint: two overlapping ACTIVE
  bookings on the same court are physically impossible (migration 0002).
- This layer adds a transaction + per-court row lock + an application overlap check
  for a friendly error and to cover the SQLite dev fallback. If the DB constraint
  fires anyway (true race), the IntegrityError is caught and surfaced as SlotUnavailable.
"""
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.futsals.models import Court
from apps.futsals.services import availability_error
from apps.pricing.services import resolve_price

from .exceptions import (
    InvalidBookingTransition,
    OutsideOperatingHours,
    SlotInPast,
    SlotUnavailable,
)
from .models import Booking
from .notifications import notify_booking_decided, notify_booking_pending


def _validate_slot(court: Court, start: datetime, end: datetime):
    if start >= end:
        raise OutsideOperatingHours("Start must be before end.")
    if start <= timezone.now():
        raise SlotInPast()
    reason = availability_error(court, start, end)
    if reason:
        raise OutsideOperatingHours(reason)


def _overlaps(court, start, end, exclude_pk=None) -> bool:
    qs = Booking.objects.filter(
        court=court, status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=end, end_at__gt=start,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def create_booking(*, user, court: Court, start: datetime, end: datetime, note: str = "") -> Booking:
    _validate_slot(court, start, end)
    with transaction.atomic():
        # Serialize concurrent writers on the same court (no-op on SQLite, real on Postgres).
        Court.objects.select_for_update().get(pk=court.pk)
        if _overlaps(court, start, end):
            raise SlotUnavailable()
        price = resolve_price(court, start)
        try:
            booking = Booking.objects.create(
                court=court, user=user, start_at=start, end_at=end,
                price_at_booking=price, status=Booking.Status.PENDING, note=note,
            )
        except IntegrityError:
            # Exclusion constraint won the race — deterministic loser.
            raise SlotUnavailable()
    notify_booking_pending(booking)
    return booking


def reschedule_booking(*, booking: Booking, start: datetime, end: datetime) -> Booking:
    _validate_slot(booking.court, start, end)
    with transaction.atomic():
        b = Booking.objects.select_for_update().get(pk=booking.pk)
        if b.status not in Booking.ACTIVE_STATUSES:
            raise InvalidBookingTransition("Only pending or approved bookings can be rescheduled.")
        if _overlaps(b.court, start, end, exclude_pk=b.pk):
            raise SlotUnavailable()
        b.start_at, b.end_at = start, end
        b.price_at_booking = resolve_price(b.court, start)
        b.status = Booking.Status.PENDING  # re-approval required after a time change
        b.approved_by = None
        b.approved_at = None
        try:
            b.save(update_fields=["start_at", "end_at", "price_at_booking",
                                  "status", "approved_by", "approved_at", "updated_at"])
        except IntegrityError:
            raise SlotUnavailable()
    notify_booking_pending(b)
    return b


def cancel_booking(*, booking: Booking, reason: str = "") -> Booking:
    if booking.status not in Booking.ACTIVE_STATUSES:
        raise InvalidBookingTransition("This booking can no longer be cancelled.")
    booking.status = Booking.Status.CANCELLED
    booking.cancellation_reason = reason
    booking.save(update_fields=["status", "cancellation_reason", "updated_at"])
    return booking


def complete_booking(*, booking: Booking) -> Booking:
    """Venue staff mark a played (approved) booking as completed."""
    if booking.status != Booking.Status.APPROVED:
        raise InvalidBookingTransition("Only approved bookings can be marked completed.")
    booking.status = Booking.Status.COMPLETED
    booking.save(update_fields=["status", "updated_at"])
    return booking


def approve_booking(*, booking: Booking, approver) -> Booking:
    if booking.status != Booking.Status.PENDING:
        raise InvalidBookingTransition("Only pending bookings can be approved.")
    booking.status = Booking.Status.APPROVED
    booking.approved_by = approver
    booking.approved_at = timezone.now()
    booking.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    notify_booking_decided(booking)
    return booking


def reject_booking(*, booking: Booking, approver, reason: str = "") -> Booking:
    if booking.status != Booking.Status.PENDING:
        raise InvalidBookingTransition("Only pending bookings can be rejected.")
    booking.status = Booking.Status.REJECTED
    booking.approved_by = approver
    booking.approved_at = timezone.now()
    booking.cancellation_reason = reason
    booking.save(update_fields=["status", "approved_by", "approved_at",
                                "cancellation_reason", "updated_at"])
    notify_booking_decided(booking)
    return booking
