from django.contrib import admin
from django.utils.html import format_html

from .models import Booking

_STATUS_COLORS = {
    "PENDING_APPROVAL": "#f5c842", "APPROVED": "#22c55e", "COMPLETED": "#4aa3ff",
    "REJECTED": "#ef4444", "CANCELLED": "#888888", "EXPIRED": "#888888",
}


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("court", "user", "start_at", "end_at", "status_badge",
                    "price_at_booking", "invoice_link")
    list_filter = ("status", "payment_method", "court__futsal")
    search_fields = ("user__email", "user__full_name", "court__futsal__name", "court__name")
    autocomplete_fields = ("court", "user", "approved_by")
    readonly_fields = ("id", "created_at", "updated_at", "approved_at")
    date_hierarchy = "start_at"
    actions = ("approve_bookings", "generate_invoice")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        c = _STATUS_COLORS.get(obj.status, "#888")
        return format_html(
            '<span style="background:{};color:{};padding:2px 9px;border-radius:999px;'
            'font-weight:700;font-size:11px;">{}</span>',
            c, "#fff" if obj.status in ("REJECTED",) else "#0a0a0a", obj.get_status_display(),
        )

    @admin.display(description="Invoice")
    def invoice_link(self, obj):
        inv = obj.invoices.first()
        if not inv:
            return "—"
        from django.urls import reverse
        url = reverse("admin:billing_invoice_change", args=[inv.pk])
        return format_html('<a href="{}">{}</a>', url, inv.number)

    @admin.action(description="Approve selected bookings")
    def approve_bookings(self, request, queryset):
        from .services import approve_booking
        n = 0
        for b in queryset.filter(status=Booking.Status.PENDING):
            try:
                approve_booking(booking=b, approver=request.user)
                n += 1
            except Exception as e:  # noqa: BLE001
                self.message_user(request, f"{b}: {e}", level="error")
        self.message_user(request, f"{n} booking(s) approved.")

    @admin.action(description="Generate invoice for selected bookings")
    def generate_invoice(self, request, queryset):
        from apps.billing.services import invoice_from_booking
        created = 0
        for b in queryset:
            if b.invoices.exists():
                continue
            invoice_from_booking(b, created_by=request.user)
            created += 1
        self.message_user(request, f"{created} invoice(s) generated.")
