"""Billing service layer — keep invoice totals and statuses consistent."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import Invoice, InvoiceItem, Payment

TWO = Decimal("0.01")


def recalc_invoice(invoice: Invoice, *, save=True) -> Invoice:
    """Recompute subtotal/tax/total/amount_paid and derive the status."""
    subtotal = invoice.items.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    paid = invoice.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
    tax = (subtotal * (invoice.tax_rate or Decimal("0"))) / Decimal("100")

    invoice.subtotal = subtotal.quantize(TWO)
    invoice.tax_amount = tax.quantize(TWO)
    invoice.total = (subtotal + tax).quantize(TWO)
    invoice.amount_paid = paid.quantize(TWO)

    # Don't override manually-set terminal/draft states.
    if invoice.status not in (Invoice.Status.CANCELLED, Invoice.Status.REFUNDED, Invoice.Status.DRAFT):
        if invoice.total > 0 and invoice.amount_paid >= invoice.total:
            invoice.status = Invoice.Status.PAID
            invoice.paid_at = invoice.paid_at or timezone.now()
        elif invoice.amount_paid > 0:
            invoice.status = Invoice.Status.PARTIAL
        elif invoice.due_date and invoice.due_date < timezone.localdate():
            invoice.status = Invoice.Status.OVERDUE
        else:
            invoice.status = Invoice.Status.UNPAID

    if save:
        invoice.save(update_fields=[
            "subtotal", "tax_amount", "total", "amount_paid", "status", "paid_at", "updated_at",
        ])
    return invoice


def add_payment(*, invoice: Invoice, amount, method=Payment.Method.CASH,
                reference="", recorded_by=None, note="") -> Payment:
    payment = Payment.objects.create(
        invoice=invoice, amount=Decimal(amount), method=method,
        reference=reference, recorded_by=recorded_by, note=note,
    )
    recalc_invoice(invoice)
    return payment


def mark_paid(*, invoice: Invoice, recorded_by=None, method=Payment.Method.CASH) -> Invoice:
    """Record a payment for the outstanding balance and mark the invoice paid."""
    if invoice.status == Invoice.Status.DRAFT:
        invoice.status = Invoice.Status.UNPAID
        invoice.save(update_fields=["status", "updated_at"])
    recalc_invoice(invoice, save=True)
    balance = invoice.balance
    if balance > 0:
        add_payment(invoice=invoice, amount=balance, method=method,
                    recorded_by=recorded_by, note="Marked paid from admin")
    return invoice


def invoice_from_booking(booking, *, due_in_days=7, issue=True, created_by=None) -> Invoice:
    """Generate an invoice for a court booking."""
    inv = Invoice.objects.create(
        customer=booking.user,
        booking=booking,
        status=Invoice.Status.UNPAID if issue else Invoice.Status.DRAFT,
        due_date=timezone.localdate() + timedelta(days=due_in_days),
        notes=f"Auto-generated for booking {booking.pk}.",
    )
    court = booking.court
    when = timezone.localtime(booking.start_at).strftime("%Y-%m-%d %H:%M")
    InvoiceItem.objects.create(
        invoice=inv,
        description=f"Court booking — {court.name} @ {when}",
        quantity=Decimal("1.00"),
        unit_price=Decimal(booking.price_at_booking),
    )
    recalc_invoice(inv)
    return inv
