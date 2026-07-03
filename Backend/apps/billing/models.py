from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel

TWO = Decimal("0.01")


def _next_number(model, field, prefix, start=1000):
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


class Invoice(BaseModel):
    """A billable document — like a WHMCS invoice. Totals derive from line items
    and payments via apps.billing.services.recalc_invoice()."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partially paid"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    OPEN_STATUSES = (Status.UNPAID, Status.PARTIAL, Status.OVERDUE)

    number = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices"
    )
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    currency = models.CharField(max_length=8, default="NPR")

    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)

    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"),
                                   help_text="Percent, e.g. 13 for 13% VAT.")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["customer", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = _next_number(Invoice, "number", "INV")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number} · {self.customer.get_full_name()}"

    @property
    def balance(self):
        return (self.total - self.amount_paid).quantize(TWO)

    @property
    def is_overdue(self):
        return (
            self.status in self.OPEN_STATUSES
            and self.due_date is not None
            and self.due_date < timezone.localdate()
        )


class InvoiceItem(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        self.amount = (Decimal(self.quantity) * Decimal(self.unit_price)).quantize(TWO)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} × {self.quantity}"


class Payment(BaseModel):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK = "BANK", "Bank transfer"
        CARD = "CARD", "Card"
        ONLINE = "ONLINE", "Online / wallet"
        OTHER = "OTHER", "Other"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=8, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_payments",
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.amount} {self.get_method_display()} → {self.invoice.number}"
