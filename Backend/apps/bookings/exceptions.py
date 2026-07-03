from rest_framework.exceptions import APIException


class SlotUnavailable(APIException):
    status_code = 409
    default_detail = "That time slot is no longer available."
    default_code = "slot_unavailable"


class SlotInPast(APIException):
    status_code = 400
    default_detail = "You cannot book a slot in the past."
    default_code = "slot_in_past"


class OutsideOperatingHours(APIException):
    status_code = 400
    default_detail = "The court is not available at that time."
    default_code = "outside_operating_hours"


class InvalidBookingTransition(APIException):
    status_code = 400
    default_detail = "This action is not allowed for the booking's current status."
    default_code = "invalid_transition"
