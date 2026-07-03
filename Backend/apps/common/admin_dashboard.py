"""
Turns the Django admin home page into a stats dashboard.

We wrap ``admin.site.index`` to inject a ``booksall_stats`` context, which
``templates/admin/index.html`` renders as a grid of metric cards, a support
response-time chart, and a to-do list, above the usual app list. We also
register a small JSON endpoint (``admin:dashboard_stats_json``) so that page
can poll for fresh numbers every couple of minutes without a full reload.
Everything is computed defensively so a missing model or a migration gap
never takes the admin home down.
"""
from urllib.parse import urlencode

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, reverse


def _n(qs_count):
    try:
        return qs_count()
    except Exception:
        return "—"


def _url(viewname):
    try:
        return reverse(viewname)
    except Exception:
        return ""


def _filtered_url(viewname, **params):
    base = _url(viewname)
    if not base or not params:
        return base
    return f"{base}?{urlencode(params)}"


def _money(value):
    try:
        return f"NPR {int(value):,}"
    except Exception:
        return "NPR 0"


def _fmt_duration(seconds):
    """38m / 2.4h / 1.3d — compact, human-scale duration for tooltips."""
    seconds = max(int(seconds), 0)
    if seconds < 3600:
        return f"{max(seconds // 60, 1)}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _response_time_buckets():
    """Bucket support tickets by time-to-first-staff-reply, for the pie chart.

    Tickets with no staff reply yet are surfaced as their own "Awaiting first
    response" slice (using how long they've been waiting so far) rather than
    being silently excluded — that's usually the number an admin cares about
    most.
    """
    from django.db.models import Min
    from django.utils import timezone

    from apps.support.models import SupportTicket, TicketReply

    now = timezone.now()
    order = ["Under 1 hour", "1–4 hours", "4–24 hours", "1–3 days", "Over 3 days"]
    colors = {
        "Under 1 hour": "#c9ff47",
        "1–4 hours": "#8fe000",
        "4–24 hours": "#4aa3ff",
        "1–3 days": "#f5a623",
        "Over 3 days": "#ef4444",
    }
    counts = dict.fromkeys(order, 0)
    seconds_sum = dict.fromkeys(order, 0.0)

    first_reply_at = dict(
        TicketReply.objects.filter(is_staff_reply=True, is_internal_note=False)
        .values("ticket_id")
        .annotate(first_at=Min("created_at"))
        .values_list("ticket_id", "first_at")
    )

    awaiting, awaiting_wait_sum = 0, 0.0
    for ticket_id, created_at in SupportTicket.objects.values_list("id", "created_at"):
        first_at = first_reply_at.get(ticket_id)
        if not first_at:
            awaiting += 1
            awaiting_wait_sum += (now - created_at).total_seconds()
            continue
        secs = (first_at - created_at).total_seconds()
        if secs < 3600:
            key = order[0]
        elif secs < 4 * 3600:
            key = order[1]
        elif secs < 24 * 3600:
            key = order[2]
        elif secs < 72 * 3600:
            key = order[3]
        else:
            key = order[4]
        counts[key] += 1
        seconds_sum[key] += secs

    slices = [
        {
            "label": key,
            "count": counts[key],
            "avg": _fmt_duration(seconds_sum[key] / counts[key]) + " avg",
            "color": colors[key],
        }
        for key in order
        if counts[key]
    ]
    if awaiting:
        slices.append({
            "label": "Awaiting first response",
            "count": awaiting,
            "avg": _fmt_duration(awaiting_wait_sum / awaiting) + " waiting so far",
            "color": "#5a5a5a",
        })
    return slices


def _booking_activity(days=7):
    """Daily booking volume for the last N days, for the activity bar chart.
    Split by status so the bars themselves communicate the pending/approved/
    completed mix, not just the total."""
    from django.utils import timezone

    from apps.bookings.models import Booking

    today = timezone.localdate()
    start = today - timezone.timedelta(days=days - 1)
    rows = Booking.objects.filter(created_at__date__gte=start).values_list("created_at", "status")

    buckets = {start + timezone.timedelta(days=i): {"PENDING_APPROVAL": 0, "APPROVED": 0, "OTHER": 0} for i in range(days)}
    for created_at, status in rows:
        day = timezone.localtime(created_at).date()
        bucket = buckets.get(day)
        if bucket is None:
            continue
        if status in ("PENDING_APPROVAL", "APPROVED"):
            bucket[status] += 1
        else:
            bucket["OTHER"] += 1

    ordered_days = sorted(buckets)
    return {
        "labels": [d.strftime("%a") for d in ordered_days],
        "pending": [buckets[d]["PENDING_APPROVAL"] for d in ordered_days],
        "approved": [buckets[d]["APPROVED"] for d in ordered_days],
        "other": [buckets[d]["OTHER"] for d in ordered_days],
    }


def _todos():
    """Flat list of things an admin should probably act on today."""
    items = []

    try:
        from apps.support.models import SupportTicket

        S = SupportTicket.Status
        new_t = SupportTicket.objects.filter(status=S.OPEN).count()
        replied_t = SupportTicket.objects.filter(status=S.CUSTOMER_REPLY).count()
        if new_t:
            items.append({
                "label": "New tickets awaiting a first reply", "count": new_t,
                "severity": "urgent", "icon": "support",
                "url": _filtered_url("admin:support_supportticket_changelist", status__exact=S.OPEN),
            })
        if replied_t:
            items.append({
                "label": "Tickets with a new customer reply", "count": replied_t,
                "severity": "warn", "icon": "support",
                "url": _filtered_url("admin:support_supportticket_changelist", status__exact=S.CUSTOMER_REPLY),
            })
    except Exception:
        pass

    try:
        from apps.bookings.models import Booking

        pending_b = Booking.objects.filter(status=Booking.Status.PENDING).count()
        if pending_b:
            items.append({
                "label": "Bookings awaiting approval", "count": pending_b,
                "severity": "warn", "icon": "sales",
                "url": _filtered_url("admin:bookings_booking_changelist", status__exact=Booking.Status.PENDING),
            })
    except Exception:
        pass

    try:
        from apps.billing.models import Invoice

        overdue_i = Invoice.objects.filter(status=Invoice.Status.OVERDUE).count()
        unpaid_i = Invoice.objects.filter(
            status__in=[Invoice.Status.UNPAID, Invoice.Status.PARTIAL]
        ).count()
        if overdue_i:
            items.append({
                "label": "Overdue invoices", "count": overdue_i,
                "severity": "urgent", "icon": "sales",
                "url": _filtered_url("admin:billing_invoice_changelist", status__exact=Invoice.Status.OVERDUE),
            })
        if unpaid_i:
            items.append({
                "label": "Unpaid invoices", "count": unpaid_i,
                "severity": "normal", "icon": "sales",
                "url": _filtered_url("admin:billing_invoice_changelist", status__in="UNPAID,PARTIAL"),
            })
    except Exception:
        pass

    try:
        from apps.futsals.models import Futsal

        pending_v = Futsal.objects.filter(status=Futsal.Status.PENDING).count()
        if pending_v:
            items.append({
                "label": "Futsal venues awaiting review", "count": pending_v,
                "severity": "warn", "icon": "system",
                "url": _filtered_url("admin:futsals_futsal_changelist", status__exact=Futsal.Status.PENDING),
            })
    except Exception:
        pass

    return items


def dashboard_stats():
    from django.contrib.auth import get_user_model

    cards = []
    bookings = {}

    # Futsals & courts
    try:
        from apps.futsals.models import Court, Futsal

        total_f = Futsal.objects.count()
        active_f = Futsal.objects.filter(status=Futsal.Status.ACTIVE).count()
        cards.append({
            "label": "Futsals", "value": total_f, "icon": "venue",
            "sub": f"{active_f} active", "accent": True,
            "url": _url("admin:futsals_futsal_changelist"),
        })
        cards.append({
            "label": "Courts", "value": _n(Court.objects.count), "icon": "court",
            "sub": f"{_n(lambda: Court.objects.filter(is_active=True).count())} active",
            "url": _url("admin:futsals_court_changelist"),
        })
    except Exception:
        pass

    # Bookings + revenue
    try:
        from django.db.models import Sum

        from apps.bookings.models import Booking

        S = Booking.Status
        total_b = Booking.objects.count()
        pending = Booking.objects.filter(status=S.PENDING).count()
        approved = Booking.objects.filter(status=S.APPROVED).count()
        completed = Booking.objects.filter(status=S.COMPLETED).count()
        revenue = (
            Booking.objects.filter(status__in=[S.APPROVED, S.COMPLETED])
            .aggregate(t=Sum("price_at_booking"))["t"] or 0
        )
        bookings = {
            "total": total_b, "pending": pending,
            "approved": approved, "completed": completed,
        }
        cards.append({
            "label": "Bookings", "value": total_b, "icon": "calendar",
            "sub": f"{pending} awaiting approval", "accent": True,
            "url": _url("admin:bookings_booking_changelist"),
        })
        cards.append({
            "label": "Confirmed revenue", "value": _money(revenue), "icon": "cash",
            "sub": f"{approved + completed} paid slots", "big": True,
            "url": _url("admin:bookings_booking_changelist"),
        })
    except Exception:
        pass

    # Players
    try:
        User = get_user_model()
        cards.append({
            "label": "Players", "value": User.objects.count(), "icon": "players",
            "sub": f"{User.objects.filter(is_staff=True).count()} staff",
            "url": _url("admin:accounts_user_changelist"),
        })
    except Exception:
        pass

    # Teams
    try:
        from apps.teams.models import Team

        cards.append({
            "label": "Teams", "value": Team.objects.count(), "icon": "team",
            "sub": "registered",
            "url": _url("admin:teams_team_changelist"),
        })
    except Exception:
        pass

    # Matches
    try:
        from apps.matchmaking.models import Match

        total_m = Match.objects.count()
        sub = "total"
        try:
            open_m = Match.objects.filter(status="OPEN").count()
            sub = f"{open_m} open"
        except Exception:
            pass
        cards.append({
            "label": "Matches", "value": total_m, "icon": "match", "sub": sub,
            "url": _url("admin:matchmaking_match_changelist"),
        })
    except Exception:
        pass

    # Support tickets + responses
    try:
        from django.utils import timezone

        from apps.support.models import SupportTicket, TicketReply

        total_t = SupportTicket.objects.count()
        open_t = SupportTicket.objects.filter(status__in=SupportTicket.OPEN_STATUSES).count()
        cards.append({
            "label": "Support tickets", "value": open_t, "icon": "ticket",
            "sub": f"{total_t} all time", "accent": open_t > 0,
            "url": _url("admin:support_supportticket_changelist"),
        })
        today = timezone.localdate()
        replies_today = TicketReply.objects.filter(
            is_staff_reply=True, created_at__date=today,
        ).count()
        cards.append({
            "label": "Responses today", "value": replies_today, "icon": "chat",
            "sub": "staff replies sent",
            "url": _url("admin:support_ticketreply_changelist"),
        })
    except Exception:
        pass

    # Billing — outstanding & overdue
    try:
        from django.db.models import F, Sum

        from apps.billing.models import Invoice

        outstanding = (
            Invoice.objects.filter(status__in=Invoice.OPEN_STATUSES)
            .aggregate(t=Sum(F("total") - F("amount_paid")))["t"] or 0
        )
        overdue = Invoice.objects.filter(status=Invoice.Status.OVERDUE).count()
        cards.append({
            "label": "Outstanding", "value": _money(outstanding), "icon": "cash",
            "sub": f"{overdue} overdue", "big": True,
            "url": _url("admin:billing_invoice_changelist"),
        })
        cards.append({
            "label": "Invoices", "value": Invoice.objects.count(), "icon": "invoice",
            "sub": f"{Invoice.objects.filter(status=Invoice.Status.PAID).count()} paid",
            "url": _url("admin:billing_invoice_changelist"),
        })
    except Exception:
        pass

    try:
        response_buckets = _response_time_buckets()
    except Exception:
        response_buckets = []

    try:
        booking_activity = _booking_activity()
    except Exception:
        booking_activity = {"labels": [], "pending": [], "approved": [], "other": []}

    try:
        todos = _todos()
    except Exception:
        todos = []

    return {
        "cards": cards,
        "bookings": bookings,
        "response_buckets": response_buckets,
        "booking_activity": booking_activity,
        "todos": todos,
    }


_EMPTY_STATS = {
    "cards": [], "bookings": {}, "response_buckets": [], "todos": [],
    "booking_activity": {"labels": [], "pending": [], "approved": [], "other": []},
}


def dashboard_stats_json(request):
    """JSON version of the same stats, for the homepage's 2-minute poll."""
    try:
        return JsonResponse(dashboard_stats())
    except Exception:
        return JsonResponse(_EMPTY_STATS)


def install():
    """Wrap admin.site.index/get_urls to add the dashboard context + JSON
    polling endpoint. Idempotent."""
    if getattr(admin.site, "_booksall_dashboard_installed", False):
        return
    original_index = admin.site.index

    def index(request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context["booksall_stats"] = dashboard_stats()
        except Exception:
            extra_context["booksall_stats"] = _EMPTY_STATS
        return original_index(request, extra_context)

    admin.site.index = index

    original_get_urls = admin.site.get_urls

    def get_urls():
        # Prepended so it's matched before the catch-all model urls below it.
        custom = [
            path(
                "dashboard-stats.json",
                admin.site.admin_view(dashboard_stats_json),
                name="dashboard_stats_json",
            ),
        ]
        return custom + original_get_urls()

    admin.site.get_urls = get_urls
    admin.site._booksall_dashboard_installed = True
