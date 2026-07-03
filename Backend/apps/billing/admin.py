from django.contrib import admin
from django.utils.html import format_html

from .models import Invoice, InvoiceItem, Payment
from .services import mark_paid, recalc_invoice

_STATUS_COLORS = {
    "DRAFT": "#888888", "UNPAID": "#f5c842", "PARTIAL": "#4aa3ff",
    "PAID": "#22c55e", "OVERDUE": "#ef4444", "CANCELLED": "#888888", "REFUNDED": "#a855f7",
}


def _badge(text, color, fg="#0a0a0a"):
    return format_html(
        '<span style="background:{};color:{};padding:2px 9px;border-radius:999px;'
        'font-weight:700;font-size:11px;white-space:nowrap;">{}</span>',
        color, fg, text,
    )


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ("description", "quantity", "unit_price", "amount")
    readonly_fields = ("amount",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("amount", "method", "reference", "paid_at", "recorded_by")
    readonly_fields = ("recorded_by",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline, PaymentInline]
    list_display = ("number", "customer", "status_badge", "total_display",
                    "paid_display", "balance_display", "issue_date", "due_date")
    list_filter = ("status", "issue_date", "due_date")
    search_fields = ("number", "customer__email", "customer__full_name", "notes")
    autocomplete_fields = ("customer", "booking")
    date_hierarchy = "issue_date"
    readonly_fields = ("number", "subtotal", "tax_amount", "total", "amount_paid",
                       "paid_at", "created_at", "updated_at")
    actions = ("action_mark_paid", "action_issue", "action_cancel", "action_recalc")
    fieldsets = (
        (None, {"fields": ("number", "customer", "booking", "status")}),
        ("Dates", {"fields": (("issue_date", "due_date"), "paid_at")}),
        ("Amounts", {"fields": ("tax_rate", ("subtotal", "tax_amount"), ("total", "amount_paid"))}),
        ("Notes", {"fields": ("notes",)}),
        ("Meta", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        c = _STATUS_COLORS.get(obj.status, "#888")
        return _badge(obj.get_status_display(), c, "#fff" if obj.status in ("OVERDUE", "REFUNDED") else "#0a0a0a")

    @admin.display(description="Total", ordering="total")
    def total_display(self, obj):
        return f"{obj.currency} {obj.total:,.2f}"

    @admin.display(description="Paid")
    def paid_display(self, obj):
        return f"{obj.currency} {obj.amount_paid:,.2f}"

    @admin.display(description="Balance")
    def balance_display(self, obj):
        b = obj.balance
        color = "#22c55e" if b <= 0 else "#f5a623"
        text = f"{obj.currency} {b:,.2f}"
        return format_html('<b style="color:{}">{}</b>', color, text)

    def save_related(self, request, form, formsets, change):
        # Stamp who recorded new payments, then recompute totals from the saved inlines.
        super().save_related(request, form, formsets, change)
        for p in form.instance.payments.filter(recorded_by__isnull=True):
            p.recorded_by = request.user
            p.save(update_fields=["recorded_by"])
        recalc_invoice(form.instance)

    @admin.action(description="Mark as PAID (record balance)")
    def action_mark_paid(self, request, queryset):
        for inv in queryset:
            mark_paid(invoice=inv, recorded_by=request.user)
        self.message_user(request, f"{queryset.count()} invoice(s) marked paid.")

    @admin.action(description="Issue (Draft → Unpaid)")
    def action_issue(self, request, queryset):
        n = 0
        for inv in queryset.filter(status=Invoice.Status.DRAFT):
            inv.status = Invoice.Status.UNPAID
            inv.save(update_fields=["status", "updated_at"])
            recalc_invoice(inv)
            n += 1
        self.message_user(request, f"{n} invoice(s) issued.")

    @admin.action(description="Cancel invoices")
    def action_cancel(self, request, queryset):
        n = queryset.update(status=Invoice.Status.CANCELLED)
        self.message_user(request, f"{n} invoice(s) cancelled.")

    @admin.action(description="Recalculate totals")
    def action_recalc(self, request, queryset):
        for inv in queryset:
            recalc_invoice(inv)
        self.message_user(request, "Totals recalculated.")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("invoice", "amount", "method", "reference", "paid_at", "recorded_by")
    list_filter = ("method", "paid_at")
    search_fields = ("invoice__number", "reference")
    autocomplete_fields = ("invoice", "recorded_by")
