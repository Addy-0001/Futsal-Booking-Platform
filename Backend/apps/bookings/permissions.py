from rest_framework import permissions


def is_futsal_staff(user, booking):
    return user.is_staff or booking.court.futsal.is_staff_member(user)


def is_booking_party(user, booking):
    """The player who made it, or staff of the venue."""
    return booking.user_id == user.id or is_futsal_staff(user, booking)


class IsBookingParty(permissions.BasePermission):
    """Read/act only if you own the booking or manage the venue."""

    def has_object_permission(self, request, view, obj):
        return is_booking_party(request.user, obj)
