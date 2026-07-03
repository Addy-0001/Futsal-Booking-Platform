from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


def _next_ref(model, field, prefix, start=1000):
    """Human-friendly sequential reference, e.g. TKT-1001. Safe on SQLite & Postgres."""
    last = (
        model.objects.exclude(**{field: ""})
        .order_by("-created_at")
        .values_list(field, flat=True)
        .first()
    )
    n = start
    if last and "-" in last:
        try:
            n = int(last.split("-")[-1])
        except ValueError:
            n = start
    return f"{prefix}-{n + 1}"


class TicketDepartment(BaseModel):
    """Routing queue for tickets (e.g. Billing, Technical, Bookings)."""

    name = models.CharField(max_length=80, unique=True)
    email = models.EmailField(blank=True)
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupportTicket(BaseModel):
    """A support conversation. Opening message lives here; the thread is TicketReply."""

    class Type(models.TextChoices):
        SUPPORT = "SUPPORT", "Support request"
        BILLING = "BILLING", "Billing"
        BUG = "BUG", "Bug report"
        FEEDBACK = "FEEDBACK", "Feedback"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ANSWERED = "ANSWERED", "Answered"
        CUSTOMER_REPLY = "CUSTOMER_REPLY", "Customer reply"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    # Open statuses still needing attention (used by dashboards / SLAs).
    OPEN_STATUSES = (Status.OPEN, Status.CUSTOMER_REPLY, Status.IN_PROGRESS)

    number = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tickets",
    )
    email = models.EmailField(blank=True)  # for anonymous reporters
    department = models.ForeignKey(
        TicketDepartment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_tickets", limit_choices_to={"is_staff": True},
    )
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.SUPPORT)
    priority = models.CharField(max_length=8, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)

    subject = models.CharField(max_length=150)
    message = models.TextField()
    url = models.CharField(max_length=400, blank=True)  # page the report came from

    last_reply_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_reply_at"]
        indexes = [
            models.Index(fields=["type", "status"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_ref(SupportTicket, "number", "TKT")
        if self.status == self.Status.CLOSED and self.closed_at is None:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number or '#'} · {self.subject}"

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    @property
    def requester_display(self):
        if self.reporter:
            return self.reporter.get_full_name()
        return self.email or "Anonymous"


class TicketReply(BaseModel):
    """A message in a ticket thread. Internal notes are hidden from the customer."""

    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ticket_replies",
    )
    body = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    is_internal_note = models.BooleanField(
        default=False, help_text="Only visible to staff — never shown to the customer."
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        who = "Staff" if self.is_staff_reply else "Customer"
        return f"{who} reply on {self.ticket.number}"
