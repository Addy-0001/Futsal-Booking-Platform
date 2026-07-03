"""Availability helpers for a court: operating hours + one-off closures."""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.utils import timezone


def _venue_local(court, when: datetime) -> datetime:
    tz = ZoneInfo(court.futsal.timezone)
    if timezone.is_naive(when):
        return when.replace(tzinfo=tz)
    return when.astimezone(tz)


def availability_error(court, start: datetime, end: datetime):
    """
    Return a human-readable reason the [start, end) slot is NOT bookable on this court,
    or None if it is fine. Checks: same local day, no closure, inside operating hours.
    """
    local_start = _venue_local(court, start)
    local_end = _venue_local(court, end)

    if local_start.date() != local_end.date():
        return "Bookings cannot span across days."

    date = local_start.date()
    weekday = local_start.weekday()

    if court.closures.filter(date=date).exists():
        return "The court is closed on this date."

    hours = court.operating_hours.filter(weekday=weekday).first()
    if hours is None:
        return "The court is not open on this day."

    if not (hours.open_time <= local_start.time() and local_end.time() <= hours.close_time):
        return f"Outside operating hours ({hours.open_time:%H:%M}–{hours.close_time:%H:%M})."

    return None
