from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.common.sanitize import sanitize_html

from .models import SupportTicket, TicketDepartment, TicketReply

# CKEditor 5 widget — degrade gracefully to a plain textarea if not installed yet.
try:
    from django_ckeditor_5.widgets import CKEditor5Widget

    _HAS_CKEDITOR = True
except Exception:  # noqa: BLE001
    CKEditor5Widget = None
    _HAS_CKEDITOR = False


def _ckeditor_field(**kwargs):
    if _HAS_CKEDITOR:
        return forms.CharField(widget=CKEditor5Widget(config_name="default"), **kwargs)
    return forms.CharField(widget=forms.Textarea(attrs={"rows": 8}), **kwargs)

# Quick-action submit button name -> ticket status to apply.
_QUICK_STATUS = {
    "_status_open": SupportTicket.Status.OPEN,
    "_status_in_progress": SupportTicket.Status.IN_PROGRESS,
    "_status_answered": SupportTicket.Status.ANSWERED,
    "_status_resolved": SupportTicket.Status.RESOLVED,
    "_status_closed": SupportTicket.Status.CLOSED,
}

_STATUS_COLORS = {
    "OPEN": "#c9ff47", "CUSTOMER_REPLY": "#f5c842", "IN_PROGRESS": "#4aa3ff",
    "ANSWERED": "#22c55e", "RESOLVED": "#22c55e", "CLOSED": "#888888",
}
_PRIORITY_COLORS = {"LOW": "#888888", "MEDIUM": "#4aa3ff", "HIGH": "#f5a623", "URGENT": "#ef4444"}


def _badge(text, color, fg="#0a0a0a"):
    return format_html(
        '<span style="background:{};color:{};padding:2px 9px;border-radius:999px;'
        'font-weight:700;font-size:11px;white-space:nowrap;">{}</span>',
        color, fg, text,
    )


@admin.register(TicketDepartment)
class TicketDepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "is_active", "ticket_count")
    list_filter = ("is_active",)
    search_fields = ("name", "email")

    @admin.display(description="Tickets")
    def ticket_count(self, obj):
        return obj.tickets.count()


class TicketReplyForm(forms.ModelForm):
    body = _ckeditor_field(label="Message")

    class Meta:
        model = TicketReply
        fields = ("body", "is_internal_note")


def _bubble(*, variant, author, when, body_html, tag=None):
    """Shared chat-bubble renderer for both the opening message and thread
    replies, so the ticket reads as one consistent conversation."""
    tag_html = format_html('<span class="bk-reply-tag">{}</span>', tag) if tag else ""
    return format_html(
        '<div class="bk-reply-bubble bk-reply-bubble--{}">'
        '<div class="bk-reply-bubble__meta">'
        '<span class="bk-reply-bubble__author">{}</span>'
        '<span class="bk-reply-bubble__time">{}</span>{}'
        "</div>"
        '<div class="bk-reply-bubble__body">{}</div>'
        "</div>",
        variant, author, when, tag_html, body_html,
    )


class TicketReplyInline(admin.StackedInline):
    model = TicketReply
    form = TicketReplyForm
    extra = 1
    classes = ("bk-reply-thread",)
    fields = ("rendered_body", "body", "is_internal_note", "is_staff_reply", "author", "created_at")
    readonly_fields = ("rendered_body", "author", "is_staff_reply", "created_at")

    @admin.display(description="")
    def rendered_body(self, obj):
        if not (obj and obj.pk):
            return ""
        if obj.author_id and obj.author:
            author = obj.author.get_full_name() or obj.author.get_username()
        else:
            author = "Staff" if obj.is_staff_reply else "Customer"
        when = timezone.localtime(obj.created_at).strftime("%d %b %Y, %H:%M")
        variant = "staff" if obj.is_staff_reply else "client"
        tag = "Internal note" if obj.is_internal_note else None
        # Stored body is already sanitized on save, so it's safe to mark safe here.
        return _bubble(variant=variant, author=author, when=when, body_html=mark_safe(obj.body), tag=tag)

    def has_change_permission(self, request, obj=None):
        return False  # replies are append-only


class SupportTicketForm(forms.ModelForm):
    message = _ckeditor_field(label="Message")

    class Meta:
        model = SupportTicket
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # NOTE: this model's PK is a UUIDField with default=uuid.uuid4, so a
        # brand-new, unsaved instance already has a non-empty `.pk` — checking
        # `self.instance.pk` can't tell "new" from "existing" here. Use
        # `_state.adding` instead (False once the row has actually been saved).
        if self.instance and not self.instance._state.adding:
            # `message` is read-only once a ticket exists — get_fieldsets()
            # swaps it out for the rendered `message_display` bubble instead,
            # so it's never shown on the edit form. But it's declared
            # directly on this form class, and Django ModelForms always keep
            # explicitly declared fields regardless of admin fieldsets/
            # exclude — so without this, it silently stayed a REQUIRED field
            # with no input on the page, and every save (including posting a
            # reply, which shares this same <form>) failed validation with
            # nothing visibly wrong. Dropping it here removes it from
            # validation entirely, matching what's actually on screen.
            self.fields.pop("message", None)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    change_form_template = "admin/support/supportticket/change_form.html"
    form = SupportTicketForm
    inlines = [TicketReplyInline]
    list_display = (
        "number", "subject", "type", "priority_badge", "status_badge",
        "requester_display", "department", "assigned_to", "last_reply_at",
    )
    list_filter = ("status", "priority", "type", "department", "assigned_to")
    search_fields = ("number", "subject", "message", "email", "reporter__email", "reporter__full_name")
    autocomplete_fields = ("reporter", "assigned_to", "department")
    date_hierarchy = "created_at"
    actions = ("assign_to_me", "mark_in_progress", "mark_resolved", "close_tickets")

    @admin.display(description="Message")
    def message_display(self, obj):
        # Read-only, sanitized-HTML-safe rendering of the client's opening
        # message — styled as the first bubble in the thread instead of
        # Django's default readonly display (which would show the raw HTML
        # tags escaped as text).
        when = timezone.localtime(obj.created_at).strftime("%d %b %Y, %H:%M")
        return _bubble(
            variant="client", author=obj.requester_display, when=when,
            body_html=mark_safe(obj.message),
        )

    def get_fieldsets(self, request, obj=None):
        # The opening message is only ever edited while filing a brand-new
        # ticket (obj is None) — once it exists, show the safe rendered
        # bubble instead of Django's default readonly text (which would
        # escape the stored HTML into a wall of tags).
        message_field = "message" if obj is None else "message_display"
        return (
            (None, {"fields": ("subject", message_field), "classes": ("bk-ticket-main-fs",)}),
            ("Ticket details", {"fields": ("number", "type", "url"), "classes": ("bk-ticket-side-fs",)}),
            ("Routing", {
                "fields": (("department", "assigned_to"), ("priority", "status")),
                "classes": ("bk-ticket-side-fs",),
            }),
            ("Requester", {"fields": ("reporter", "email"), "classes": ("bk-ticket-side-fs",)}),
            ("Timeline", {
                "fields": (("last_reply_at", "closed_at"), ("created_at", "updated_at")),
                "classes": ("bk-ticket-side-fs",),
            }),
        )

    def get_readonly_fields(self, request, obj=None):
        base = ("number", "last_reply_at", "closed_at", "created_at", "updated_at")
        if obj is not None:
            base += ("message_display",)
        return base

    def response_change(self, request, obj):
        """Handle the WHMCS-style quick-action buttons. The form has already been
        saved (all field edits + any reply) by the time we get here; we just apply
        the requested status/assignment and stay on the ticket page."""
        for key, status in _QUICK_STATUS.items():
            if key in request.POST:
                obj.status = status
                fields = ["status", "updated_at"]
                if status == SupportTicket.Status.CLOSED and obj.closed_at is None:
                    obj.closed_at = timezone.now()
                    fields.append("closed_at")
                obj.save(update_fields=fields)
                self.message_user(request, f"Ticket {obj.number} → {obj.get_status_display()}.")
                return HttpResponseRedirect(request.get_full_path())
        if "_assign_me" in request.POST:
            obj.assigned_to = request.user
            obj.save(update_fields=["assigned_to", "updated_at"])
            self.message_user(request, f"Ticket {obj.number} assigned to you.")
            return HttpResponseRedirect(request.get_full_path())
        return super().response_change(request, obj)

    @admin.display(description="Priority", ordering="priority")
    def priority_badge(self, obj):
        return _badge(obj.get_priority_display(), _PRIORITY_COLORS.get(obj.priority, "#888"),
                      "#fff" if obj.priority in ("HIGH", "URGENT") else "#0a0a0a")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        c = _STATUS_COLORS.get(obj.status, "#888")
        return _badge(obj.get_status_display(), c, "#0a0a0a" if c != "#888888" else "#fff")

    def save_model(self, request, obj, form, change):
        obj.message = sanitize_html(obj.message)
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """When staff post a reply from the ticket page, stamp author + bump the ticket."""
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, TicketReply):
                obj.body = sanitize_html(obj.body)
                if obj.author_id is None:
                    obj.author = request.user
                    obj.is_staff_reply = not obj.is_internal_note
            obj.save()
            if isinstance(obj, TicketReply) and not obj.is_internal_note:
                t = obj.ticket
                t.last_reply_at = timezone.now()
                if t.status in (t.Status.OPEN, t.Status.CUSTOMER_REPLY, t.Status.IN_PROGRESS):
                    t.status = t.Status.ANSWERED
                t.save(update_fields=["last_reply_at", "status", "updated_at"])
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()

    @admin.action(description="Assign selected tickets to me")
    def assign_to_me(self, request, queryset):
        n = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{n} ticket(s) assigned to you.")

    @admin.action(description="Mark In progress")
    def mark_in_progress(self, request, queryset):
        n = queryset.update(status=SupportTicket.Status.IN_PROGRESS)
        self.message_user(request, f"{n} ticket(s) marked in progress.")

    @admin.action(description="Mark Resolved")
    def mark_resolved(self, request, queryset):
        n = queryset.update(status=SupportTicket.Status.RESOLVED)
        self.message_user(request, f"{n} ticket(s) marked resolved.")

    @admin.action(description="Close tickets")
    def close_tickets(self, request, queryset):
        n = queryset.update(status=SupportTicket.Status.CLOSED, closed_at=timezone.now())
        self.message_user(request, f"{n} ticket(s) closed.")


@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "is_staff_reply", "is_internal_note", "created_at")
    list_filter = ("is_staff_reply", "is_internal_note")
    search_fields = ("ticket__number", "body")
    autocomplete_fields = ("ticket", "author")

    def has_change_permission(self, request, obj=None):
        # This standalone listing (separate from the append-only ticket
        # inline) used to let anyone with change perms freely rewrite any
        # reply's body — including a client's. A client's own words are now
        # never editable here; staff can still open/correct their own replies.
        if obj is not None and not obj.is_staff_reply:
            return False
        return super().has_change_permission(request, obj)
