"""Celery maintenance jobs (scheduled via Celery Beat — see settings)."""
from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from .models import Booking

# How long a PENDING booking may sit before it's auto-expired, freeing the slot.
PENDING_TTL = timedelta(hours=2)


@shared_task
def expire_stale_pending():
    """Expire pending bookings that are too old or whose start time has passed."""
    now = timezone.now()
    return Booking.objects.filter(status=Booking.Status.PENDING).filter(
        Q(created_at__lt=now - PENDING_TTL) | Q(start_at__lte=now)
    ).update(status=Booking.Status.EXPIRED)


@shared_task
def complete_past_bookings():
    """Mark approved bookings whose end time has passed as completed."""
    now = timezone.now()
    return Booking.objects.filter(
        status=Booking.Status.APPROVED, end_at__lte=now
    ).update(status=Booking.Status.COMPLETED)
