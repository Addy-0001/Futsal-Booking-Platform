"""
Thin notification hooks. In Phase 3 these are replaced by the notifications app
(SMS + email + in-app via Celery). For now they log, so the booking flow is wired
end-to-end and Phase 3 only swaps the implementation.
"""
import logging

logger = logging.getLogger("booksall.bookings")


def notify_booking_pending(booking):
    # → notify all owners/managers of booking.court.futsal that approval is needed.
    logger.info("Booking %s pending approval at futsal %s",
                booking.pk, booking.court.futsal_id)


def notify_booking_decided(booking):
    # → notify the player their booking was APPROVED / REJECTED.
    logger.info("Booking %s decided: %s (user %s)",
                booking.pk, booking.status, booking.user_id)
