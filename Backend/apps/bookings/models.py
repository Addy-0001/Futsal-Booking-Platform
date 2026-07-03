from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.futsals.models import Court


class Booking(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING_APPROVAL", "Pending approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"
        COMPLETED = "COMPLETED", "Completed"

    # Statuses that hold inventory — only these participate in the overlap constraint.
    ACTIVE_STATUSES = (Status.PENDING, Status.APPROVED)

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash / pay at futsal"

    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name="bookings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )

    # Slot stored as two UTC instants ([start, end), end exclusive). Portable across
    # SQLite (dev) and Postgres; non-overlap is enforced by a Postgres exclusion
    # constraint over tstzrange(start_at, end_at) — see migration 0002.
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    price_at_booking = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH
    )

    note = models.CharField(max_length=300, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_bookings",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["court", "start_at"]),
            models.Index(fields=["user", "-start_at"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(start_at__lt=models.F("end_at")),
                name="booking_start_before_end",
            ),
        ]

    def __str__(self):
        return f"{self.court} {self.start_at:%Y-%m-%d %H:%M} [{self.status}]"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES
