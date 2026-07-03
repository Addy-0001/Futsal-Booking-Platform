"""
Price resolution — the single server-authoritative source of a slot's price.
Never trust a price sent by the client; always resolve here.
"""
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.utils import timezone

from .utils import mask_contains


def to_venue_local(court, when: datetime) -> datetime:
    """Convert an aware datetime to the futsal's local timezone.
    Naive datetimes are interpreted as already venue-local."""
    tz = ZoneInfo(court.futsal.timezone)
    if timezone.is_naive(when):
        return when.replace(tzinfo=tz)
    return when.astimezone(tz)


def resolve_price(court, when: datetime) -> Decimal:
    """
    Return the NPR price for a slot starting at `when` on `court`.
    Picks the highest-priority active rule matching weekday + time + validity window,
    else the court's default_price.
    """
    local = to_venue_local(court, when)
    weekday, t, date = local.weekday(), local.time(), local.date()

    candidates = court.price_rules.filter(
        is_active=True, start_time__lte=t, end_time__gt=t,
    ).order_by("-priority", "start_time")

    for rule in candidates:
        if rule.valid_from and date < rule.valid_from:
            continue
        if rule.valid_to and date > rule.valid_to:
            continue
        if not mask_contains(rule.days_mask, weekday):
            continue
        return rule.price

    return court.default_price
