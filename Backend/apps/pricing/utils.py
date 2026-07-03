"""Weekday bitmask helpers. Bit i (0=Mon … 6=Sun) set => rule applies that day."""

ALL_DAYS = 0b1111111  # 127
WEEKDAYS = 0b0011111   # Mon–Fri
WEEKENDS = 0b1100000   # Sat, Sun  (bit5=Sat, bit6=Sun)


def day_bit(weekday: int) -> int:
    return 1 << weekday


def mask_from_days(days) -> int:
    mask = 0
    for d in days:
        mask |= day_bit(d)
    return mask


def mask_contains(mask: int, weekday: int) -> bool:
    return bool(mask & day_bit(weekday))


def days_from_mask(mask: int):
    return [d for d in range(7) if mask_contains(mask, d)]
